#!/usr/bin/python3

from arista.inventory.v1 import models
from arista.inventory.v1 import services
from mcp.server.fastmcp import FastMCP
from typing import TypedDict
import argparse
import grpc
import json
import sys
import logging
import os

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

RPC_TIMEOUT = 30  # in second
EOS_PLATFORMS = ["DCS-", "CCS-", "AWE-"]
EOS_VIRTUAL = ["cEOS", "vEOS"]

class SwitchInfo(TypedDict):
    hostname: str
    model: str
    serial_number: str
    system_mac: str
    version: str
    streaming_status: str
    device_type: str
    hardware_revision: str
    fqdn: str
    domain_name: str

#async function to return creds
def get_env_vars():
    cvp = os.environ.get("CVP")
    cvtoken = os.environ.get("CVPTOKEN")
    datadict = {}
    datadict['cvtoken'] = cvtoken
    datadict["cvp"] = cvp
    datadict["cert"] = "./cert.pem"
    return datadict

def createConnection():
    datadict = get_env_vars()
    # create the header object for the token
    callCreds = grpc.access_token_call_credentials(datadict['cvtoken'])

    with open(datadict["cert"], "rb") as f:
        cert = f.read()
    channelCreds = grpc.ssl_channel_credentials(root_certificates=cert)

    connCreds = grpc.composite_channel_credentials(channelCreds, callCreds)
    return(connCreds)

@mcp.tool()
def get_all() -> str:
    """
    Prints the hostname of all devices known to the system.
    Optionally filters based on the only_active and only_inactive arguments.
    When filtering, only_active takes priority to only_inactive if both are set.
    """
    logging.info("CVP Get all Tool")
    datadict = get_env_vars()
    connCreds = createConnection()
    all_devices = []
    with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
        # create the Python stub for the inventory API
        # this is essentially the client, but Python gRPC refers to them as "stubs"
        # because they call into the gRPC C API
        stub = services.DeviceServiceStub(channel)

        get_all_req = services.DeviceStreamRequest()
        # Add filters to only get Active and Inactive streaming devices
        get_all_req.partial_eq_filter.append(models.Device(
            streaming_status=models.STREAMING_STATUS_INACTIVE,
        ))
        get_all_req.partial_eq_filter.append(models.Device(
            streaming_status=models.STREAMING_STATUS_ACTIVE,
        ))

        for device in stub.GetAll(get_all_req, timeout=RPC_TIMEOUT):
            try:
                # Check to make sure the device has a valid System MAC
                if device.value.system_mac_address.value:
                    match device.value.streaming_status:
                        case models.STREAMING_STATUS_INACTIVE:
                            streaming_status = "Inactive"
                        case models.STREAMING_STATUS_ACTIVE:
                            streaming_status = "Active"
                        case _:
                            streaming_status = "Unknown"
                    if any(x in device.value.model_name.value for x in EOS_PLATFORMS):
                        device_type = "EOS"
                    elif any(x in device.value.model_name.value for x in EOS_VIRTUAL):
                        device_type = "Virtual EOS"
                    elif "C-" in device.value.model_name.value:
                        device_type = "Access Point"
                    else:
                        device_type = "Third Party"
                    switch = SwitchInfo(
                        hostname = device.value.hostname.value,
                        model = device.value.model_name.value,
                        serial_number = device.value.key.device_id.value,
                        system_mac = device.value.system_mac_address.value,
                        version = device.value.software_version.value,
                        streaming_status = streaming_status,
                        device_type = device_type,
                        hardware_revision = device.value.hardware_revision.value,
                        fqdn = device.value.fqdn.value,
                        domain_name = device.value.domain_name.value
                    )
                    all_devices.append(switch)
            except Exception as e:
                logging.info(f"Error with device: {e}")
        return(json.dumps(all_devices))

def main(args):
    """Entry point for the direct execution server."""
    mcp_transport = args.transport
    mcp_port = args.port
    mcp_cvp = args.cvp

    logging.info(f"Starting MCP server via {mcp_transport}")
    logging.info(f"Server connection to CVP via {mcp_cvp}")
    if mcp_transport == "http":
        mcp.settings.port = mcp_port
        logging.info(f"Streamable HTTP Server listening on port {mcp_port}")
        mcp.run(transport="streamable-http")
    else:
        mcp_run(transport="stdio")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--transport", type=str, help="MCP Transport method", default="http", choices=["http", "stdio"], required=False)
    parser.add_argument("-p", "--port", type=int, help="Port to run the Streamable HTTP Server", default=8000, required=False)
    parser.add_argument("-c", "--cvp", type=str, help="CVP Connection protocol", choices=["grpc", "http"], default="grpc", required=False)
    args = parser.parse_args()
    main(args)
