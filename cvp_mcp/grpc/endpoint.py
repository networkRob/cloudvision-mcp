from arista.endpointlocation.v1 import models
from arista.endpointlocation.v1 import services
from google.protobuf import wrappers_pb2 as wrappers
from .utils import RPC_TIMEOUT, convert_response_to_probe_stat, convert_response_to_endpoint_location, serialize_arista_protobuf
from .models import ProbeStats
import grpc
import logging
import os
import json
import sys



def grpc_one_endpoint_location(channel, query):
    """
    Performs a serach to get an endpoint based on search term
    """
    all_endpoints= []
    stub = services.EndpointLocationServiceStub(channel)
    get_all_req = services.EndpointLocationRequest(
        key=models.EndpointLocationKey(
            search_term=wrappers.StringValue(value=query)
        )
    )
    try:
        endpoints = stub.GetOne(get_all_req, timeout=RPC_TIMEOUT)
        for endpoint in endpoints.value.device_map.values:
            logging.debug(f"One PRE PROBE: {endpoint}")
            # probe = serialize_arista_protobuf(endpoint)
            _endpoint = convert_response_to_endpoint_location(endpoints.value.device_map.values[endpoint])
            logging.debug(f"One PROBE: {_endpoint}")
            all_endpoints.append(_endpoint)
        return(all_endpoints)
    except Exception as e:
        logging.error(f"Error with Endpoint Location: {e}")
        return(ProbeStats())
