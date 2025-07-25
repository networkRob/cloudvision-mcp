import grpc
from .models import SwitchInfo
from arista.inventory.v1 import models

EOS_PLATFORMS = ["DCS-", "CCS-", "AWE-"]
EOS_VIRTUAL = ["cEOS", "vEOS"]

def createConnection(datadict):
    # datadict = get_env_vars()
    # create the header object for the token
    callCreds = grpc.access_token_call_credentials(datadict['cvtoken'])

    with open(datadict["cert"], "rb") as f:
        cert = f.read()
    channelCreds = grpc.ssl_channel_credentials(root_certificates=cert)

    connCreds = grpc.composite_channel_credentials(channelCreds, callCreds)
    return(connCreds)

def serialize_repeated_int32(repeated_int32):
     # Convert RepeatedInt32 to a list of integers
     int_list = [int(value) for value in repeated_int32]

     return int_list
 
def convert_response_to_switch(device) -> SwitchInfo:
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
    else:
        switch = SwitchInfo()
    return(switch)
