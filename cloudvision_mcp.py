#!/usr/bin/python3

from mcp.server.fastmcp import FastMCP
from typing import TypedDict, Optional
from cvp_mcp.grpc.inventory import grpc_all_inventory, grpc_one_inventory_serial
from cvp_mcp.grpc.bugs import grpc_all_bug_exposure
from cvp_mcp.grpc.monitor import grpc_all_probe_status, grpc_one_probe_status
from cvp_mcp.grpc.lifecycle import grpc_all_device_lifecycle
from cvp_mcp.grpc.endpoint import grpc_one_endpoint_location
from cvp_mcp.grpc.models import SwitchInfo, BugExposure, DeviceLifecycleSummary
from cvp_mcp.grpc.connector import conn_get_info_bugs
from cvp_mcp.grpc.utils import createConnection
import argparse
import grpc
import json
import sys
import logging
import os

CVP_TRANSPORT = "grpc"

logging.basicConfig(
    level=logging.INFO,                # Minimum log level
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
)

logging.info('Starting the FastMCP server...')

# Initialize FastMCP server
mcp = FastMCP(
    name = "CVP MCP Server",
    host = "0.0.0.0",
    stateless_http = True
)


#async function to return creds
def get_env_vars():
    cvp = os.environ.get("CVP")
    cvtoken = os.environ.get("CVPTOKEN")
    certfile = os.environ.get("CERT")
    datadict = {}
    datadict['cvtoken'] = cvtoken
    datadict["cvp"] = cvp
    datadict["cert"] = certfile
    return datadict

# ===================================================
# Inventory Based Tools
# ===================================================

@mcp.tool()
def get_cvp_one_device(device_id) -> str:
    """
    Prints out information about a single device in CVP
    For one switch it gets the serial number, system mac address,
    hostname, EOS version, streaming status, device type, harware revision,
    FQDN, domain name, and model
    """
    datadict = get_env_vars()
    logging.debug(f"CVP Get One Device Tool - {device_id}")
    try:
        match CVP_TRANSPORT:
            case "grpc":
                connCreds = createConnection(datadict)
                with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
                    device = grpc_one_inventory_serial(channel, device_id)
            case "http":
                device = ""
    except Exception as e:
        logging.error(e)
    logging.debug(json.dumps(device, indent=2))
    return(json.dumps(device, indent=2))
    
@mcp.tool()
def get_cvp_all_inventory() -> dict:
    """
    Grabs all switches and devices from CloudVision (CVP)
    For all devices it gets the serial number, system mac address,
    hostname, EOS version, streaming status, device type, harware revision,
    FQDN, domain name, and model
    """
    datadict = get_env_vars()
    all_devices = {}
    logging.info("CVP Get all Tool")
    match CVP_TRANSPORT:
        case "grpc":
            connCreds = createConnection(datadict)
            with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
                all_active, all_inactive = grpc_all_inventory(channel)
                all_devices["streaming_active"] = all_active
                all_devices["streaming_inactive"] = all_inactive
        case "http":
            logging.info("CVP HTTP Request for all devices")
            all_devices = ""
    logging.debug(json.dumps(all_devices))    
    # return(json.dumps(all_devices, indent=2))
    return(all_devices)

# ===================================================
# Bug Based Tools
# ===================================================

@mcp.tool()
def get_cvp_all_bugs() -> dict:
    """
    Prints out all bug exposures
    For each bug, it gets: device serial number, list of bug IDs,
    list of CVE IDs, bug count, cve count and the highest exposure to bugs and CVEs.
    This will also get switches based on the found serial numbers in the bug report,
    It will get  the serial number, system mac address,
    hostname, EOS version, streaming status, device type, harware revision,
    FQDN, domain name, and model
    """
    all_data = {}
    all_devices = []
    all_bug_ids = []
    # all_bug_info = {}
    datadict = get_env_vars()
    logging.info("CVP Get all Bugs Tool")
    match CVP_TRANSPORT:
        case "grpc":
            connCreds = createConnection(datadict)
            with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
                all_bugs = grpc_all_bug_exposure(channel)
                if all_bugs:
                    for bug in all_bugs:
                        for id in bug["bug_ids"]:
                            if id not in all_bug_ids:
                                all_bug_ids.append(id)
                        device = grpc_one_inventory_serial(channel, bug["serial_number"])
                        if device:
                            all_devices.append(device)
        case "http":
            logging.info("HTTP Transport to get all bugs")
            all_bugs = ""
    logging.debug(json.dumps(all_bugs))    
    # Grab information about each bug
    all_bug_info = conn_get_info_bugs(datadict, all_bug_ids)
    all_data["bug_info"] = all_bug_info
    all_data['bugs'] = all_bugs
    all_data['devices'] = all_devices
    try:
        logging.debug(f"Bug Data: {type(all_data['bug_info'])} {all_data['bug_info']}")
        logging.debug(f"All data: {json.dumps(all_data)}")
    except Exception as y:
        logging.error(y)
    # return(json.dumps(all_data, indent=2))
    return(all_data)


# ===================================================
# Commectivty Monitor Based Tools
# ===================================================

@mcp.tool()
def get_cvp_all_connectivity_probes() -> dict:
    """
    Gets all connectivity monitor probes from CVP
    Displays latency, jitter, http response time and packet loss
    """
    datadict = get_env_vars()
    all_devices = {}
    all_data = {}
    logging.info("CVP Get all Probes")
    match CVP_TRANSPORT:
        case "grpc":
            connCreds = createConnection(datadict)
            with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
                all_probes= grpc_all_probe_status(channel)
                # Gather information about the source switches for analytics
                for probe in all_probes:
                    serial_number = probe['serial_number']
                    if serial_number not in all_devices.keys():
                        all_devices[serial_number] = grpc_one_inventory_serial(channel, serial_number)
        case "http":
            logging.info("CVP HTTP Request for all devices")
            all_devices = ""
    all_data['devices'] = all_devices
    all_data['probes'] = all_probes
    logging.debug(json.dumps(all_data))    
    # return(json.dumps(all_data, indent=2))
    return(all_data)

@mcp.tool()
def get_cvp_one_connectivity_probe(
    serial_number: Optional[str] = None,
    endpoint: Optional[str] = None,
    vrf: Optional[str] = None,
    source_interface: Optional[str] = None) -> str:
    """
    Prints out information about a single device in CVP
    Displays latency, jitter, http response time and packet loss
    """
    datadict = get_env_vars()
    logging.debug(f"CVP Get One Probe State")
    all_data = {}
    all_devices = {}
    try:
        match CVP_TRANSPORT:
            case "grpc":
                connCreds = createConnection(datadict)
                with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
                    probes = grpc_one_probe_status(channel, serial_number, endpoint, vrf, source_interface)
                    for _probe in probes:
                        logging.debug(f"MON S/n: {_probe['serial_number']}")
                        serial_number = _probe['serial_number']
                        if serial_number  not in all_devices.keys():
                            all_devices[serial_number]= grpc_one_inventory_serial(channel, serial_number)
                    all_data['probes'] = probes
                    all_data['devices'] = all_devices
            case "http":
                device = ""
    except Exception as e:
        logging.error(e)
    logging.debug(json.dumps(all_data, indent=2))
    return(json.dumps(all_data, indent=2))


# ===================================================
# Device Lifecycle Based Tools
# ===================================================

@mcp.tool()
def get_cvp_all_device_lifecycle()-> dict:
    """
    Gets all device lifecycle from CVP
    Displays information about switch software end of life,
    and hardware end of support, end of rma, end of sale and end of life.
    """
    datadict = get_env_vars()
    all_devices = {}
    all_data = {}
    logging.info("CVP Get all Device Lifecycle")
    match CVP_TRANSPORT:
        case "grpc":
            connCreds = createConnection(datadict)
            with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
                all_lifecycle = grpc_all_device_lifecycle(channel)
                # Gather information about the source switches for analytics
                for _lifecycle in all_lifecycle:
                    serial_number = _lifecycle['serial_number']
                    if serial_number not in all_devices.keys():
                        all_devices[serial_number] = grpc_one_inventory_serial(channel, serial_number)
        case "http":
            logging.info("CVP HTTP Request for all devices")
            all_devices = ""
    all_data['devices'] = all_devices
    all_data['lifecycle'] = all_lifecycle
    logging.debug(json.dumps(all_data))    
    # return(json.dumps(all_data, indent=2))
    return(all_data)

# ===================================================
# Endpoint Location  Based Tools
# ===================================================

@mcp.tool()
def get_cvp_endpoint_location(search_term: str)-> dict:
    """
    Gets all endpoint locations from CVP for a user device, or connected endpoint
     based on a query of MAC, IP or hostname
    Displays information about endpoint device location, ip address
    mac address. This will also convert the switch serial number hostname and get information
    of the switch.
    """
    datadict = get_env_vars()
    all_devices = {}
    all_data = {}
    logging.info("CVP Get Endpoint Location")
    match CVP_TRANSPORT:
        case "grpc":
            connCreds = createConnection(datadict)
            with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
                all_endpoints = grpc_one_endpoint_location(channel, search_term)
                # Gather information about the source switches for analytics
                for _endpoint in all_endpoints:
                    _endpoint = _endpoint[0]
                    logging.debug(f"END FOR: {_endpoint} - {_endpoint.keys()}")
                    for _device in _endpoint["location_list"]:
                        serial_number = _device['device_id']['value']
                        if serial_number not in all_devices.keys():
                            all_devices[serial_number] = grpc_one_inventory_serial(channel, serial_number)
        case "http":
            logging.info("CVP HTTP Request for all devices")
            all_devices = ""
    all_data['devices'] = all_devices
    all_data['endpoints'] = all_endpoints
    logging.debug(json.dumps(all_data))    
    # return(json.dumps(all_data, indent=2))
    return(all_data)

def main(args):
    """Entry point for the direct execution server."""
    global CVP_TRANSPORT

    if args.debug:
        logging.info("Setting server logging to DEBUG")
        logging.getLogger().setLevel(logging.DEBUG)
    mcp_transport = args.transport
    mcp_port = args.port
    mcp_cvp = args.cvp
    CVP_TRANSPORT = mcp_cvp

    logging.info(f"Starting MCP server via {mcp_transport}")
    logging.info(f"Server connection to CVP via {mcp_cvp}")
    # Adding check as HTTP connection to CVP is currently not supported
    if mcp_cvp == "http":
        logging.warning("HTTP connections to CVP are currently not supported")
        sys.exit(1)
    if mcp_transport == "http":
        mcp.settings.port = mcp_port
        logging.info(f"Streamable HTTP Server listening on port {mcp_port}")
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--transport", type=str, help="MCP Transport method", default="http", choices=["http", "stdio"], required=False)
    parser.add_argument("-p", "--port", type=int, help="Port to run the Streamable HTTP Server", default=8000, required=False)
    parser.add_argument("-c", "--cvp", type=str, help="CVP Connection protocol", choices=["grpc", "http"], default="grpc", required=False)
    parser.add_argument("-d", "--debug", help="Enable debug logging", action="store_true")
    args = parser.parse_args()
    main(args)
