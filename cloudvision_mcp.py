#!/usr/bin/python3

from arista.inventory.v1 import models
from arista.inventory.v1 import services
from mcp.server.fastmcp import FastMCP
from typing import TypedDict
from cvp_mcp.grpc.inventory import get_all_inventory
from cvp_mcp.grpc.models import SwitchInfo
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


#async function to return creds
def get_env_vars():
    cvp = os.environ.get("CVP")
    cvtoken = os.environ.get("CVPTOKEN")
    datadict = {}
    datadict['cvtoken'] = cvtoken
    datadict["cvp"] = cvp
    datadict["cert"] = "./cert.pem"
    return datadict


@mcp.tool()
def get_all() -> str:
    """
    Prints the hostname of all devices known to the system.
    Optionally filters based on the only_active and only_inactive arguments.
    When filtering, only_active takes priority to only_inactive if both are set.
    """
    datadict = get_env_vars()
    logging.info("CVP Get all Tool")
    all_devices = get_all_inventory(datadict)
    logging.info(json.dumps(all_devices))    
    return(json.dumps(all_devices, indent=2))
    # return(all_devices)

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
