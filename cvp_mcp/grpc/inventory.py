from arista.inventory.v1 import models
from arista.inventory.v1 import services
from google.protobuf import wrappers_pb2 as wrappers
from .utils import createConnection, convert_response_to_switch
from .models import SwitchInfo
import grpc
import logging
import os
import json



RPC_TIMEOUT = 30  # in second
EOS_PLATFORMS = ["DCS-", "CCS-", "AWE-"]
EOS_VIRTUAL = ["cEOS", "vEOS"]

def grpc_all_inventory(datadict):
    """
    Prints the hostname of all devices known to the system.
    Optionally filters based on the only_active and only_inactive arguments.
    When filtering, only_active takes priority to only_inactive if both are set.
    """
    logging.info("CVP Get all Tool")
    connCreds = createConnection(datadict)
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
                    switch = convert_response_to_switch(device)
                    all_devices.append(switch)
            except Exception as e:
                logging.error(f"Error with device: {e}")
        return(all_devices)
        # return(json.dumps(all_devices))

def grpc_one_inventory_serial(datadict, device_id):
    """
    Function to get details of one device from CloudVision
    """
    logging.info("Get one device from CVP by serial number")
    connCreds = createConnection(datadict)
    device = ""
    with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
        stub = services.DeviceServiceStub(channel)
        try:
            req = services.DeviceRequest(
                key={"device_id": wrappers.StringValue(value=device_id)}
            )
        except Exception as e:
            logging.error(e)
        device = stub.GetOne(req)
        converted_device = convert_response_to_switch(device)
        logging.debug(json.dumps(converted_device ))
        return(converted_device )

