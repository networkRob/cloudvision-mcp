from arista.lifecycle.v1 import models
from arista.lifecycle.v1 import services
from google.protobuf import wrappers_pb2 as wrappers
from .utils import RPC_TIMEOUT, convert_response_to_device_lifecycle
from .models import DeviceLifecycleSummary
import grpc
import logging
import os
import json
import sys



def grpc_all_device_lifecycle(channel):
    """
    Gets all Device Lifecycle Stats  in CVP
    """
    all_devices = []
    stub = services.DeviceLifecycleSummaryServiceStub(channel)
    get_all_req = services.DeviceLifecycleSummaryStreamRequest()
    for device in stub.GetAll(get_all_req, timeout=RPC_TIMEOUT):
        try:
            _device = convert_response_to_device_lifecycle(device)
            all_devices.append(_device)
        except Exception as e:
            logging.error(f"Error with device Lifecycle: {e}")
    return(all_devices)


