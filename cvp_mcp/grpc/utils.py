import grpc
from .models import SwitchInfo, ProbeStats,DeviceLifecycleSummary, DeviceHardwareEoL, DeviceSoftwareEoL
from arista.inventory.v1 import models
import logging

RPC_TIMEOUT = 30
EOS_PLATFORMS = ["DCS-", "CCS-", "AWE-"]
EOS_VIRTUAL = ["cEOS", "vEOS"]

def datetime_to_readable_format(dt, format_type="full"):
    """
    Convert datetime object to various readable formats.
    
    Args:
        dt: datetime object
        format_type: Type of format to return
        
    Returns:
        str: Formatted date string
    """
    if dt is None:
        return None
    
    formats = {
        "full": "%B %d, %Y",           # April 25, 2028
        "short": "%b %d, %Y",          # Apr 25, 2028
        "with_day": "%A, %B %d, %Y",   # Friday, April 25, 2028
        "numeric": "%m/%d/%Y",         # 04/25/2028
        "iso_date": "%Y-%m-%d",        # 2028-04-25
        "friendly": "%B %d, %Y at %I:%M %p",  # April 25, 2028 at 12:00 AM
    }
    
    return dt.strftime(formats.get(format_type, formats["full"]))


    
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

def convert_response_to_probe_stat(probe) -> ProbeStats:
    _probe = ProbeStats(
        serial_number = probe.value.key.device_id.value,
        host = probe.value.key.host.value,
        vrf = probe.value.key.vrf.value,
        source_intf = probe.value.key.source_intf.value,
        latency_millis = probe.value.latency_millis.value,
        jitter_millis = probe.value.jitter_millis.value,
        http_response_time_millis = probe.value.http_response_time_millis.value,
        packet_loss_percent = probe.value.packet_loss_percent.value,
        error = probe.value.error.value
    )
    return _probe

def convert_response_to_device_lifecycle(device) -> DeviceLifecycleSummary:
    try:
        _sw = DeviceSoftwareEoL(
            version = device.value.software_eol.version.value,
            end_of_support = datetime_to_readable_format(device.value.software_eol.end_of_support.ToDatetime(), "with_day")
        )
    except:
        _sw = DeviceSoftwareEoL(
            version = "",
            end_of_support = ""
        )
    logging.debug(f"SW: {_sw}")
    try:
        _hw = DeviceHardwareEoL(
            end_of_life = datetime_to_readable_format(device.value.hardware_lifecycle_summary.end_of_life.ToDatetime(), "with_day"),
            end_of_sale = datetime_to_readable_format(device.value.hardware_lifecycle_summary.end_of_sale.ToDatetime(), "with_day"),
            end_of_tac_support = datetime_to_readable_format(device.value.hardware_lifecycle_summary.end_of_tag_support.ToDatetime(), "with_day"),
            end_of_hardware_rma_request = datetime_to_readable_format(device.value.hardware_lifecycle_summary.end_of_hardware_rma_request.ToDatetime(), "with_day")
        )
    except:
        _hw = DeviceHardwareEoL(
            end_of_life = "",
            end_of_sale = "",
            end_of_tac_support = "",
            end_of_hardware_rma_request = ""
        )
    _device = DeviceLifecycleSummary(
        serial_number = device.value.key.device_id.value,
        software_eol = _sw,
        hardware_lifecycle_summary = _hw
    )
    return(_device)
