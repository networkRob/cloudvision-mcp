from arista.inventory.v1 import models
from arista.inventory.v1 import services
from .utils import createConnection
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
        return(all_devices)
        # return(json.dumps(all_devices))
