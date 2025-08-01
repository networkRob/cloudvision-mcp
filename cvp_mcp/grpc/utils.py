import grpc
from .models import SwitchInfo, ProbeStats,DeviceLifecycleSummary, DeviceHardwareEoL, DeviceSoftwareEoL, EndpointLocation, EndpointLocationList
from arista.inventory.v1 import models
from arista.endpointlocation.v1 import models as endpoint_models
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

    if datadict["cert"]:
        with open(datadict["cert"], "rb") as f:
            cert = f.read()
        channelCreds = grpc.ssl_channel_credentials(root_certificates=cert)
    else:
        channelCreds = grpc.ssl_channel_credentials()
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

def convert_response_to_endpoint_location(endpoint) -> EndpointLocation:
    all_endpoints = []
    all_locations = []
    if endpoint.location_list.values:
        location = serialize_arista_protobuf(endpoint.location_list.values[0])
        all_locations.append(location)
        # for _location in endpoint.location_list.values:
        #     location = serialize_arista_protobuf(_location)
        #     # _device_enum = _location.device_status.value
        #     # location = EndpointLocationList(
        #     #     serial_number = _location.device_id.value,
        #     #     device_status = _location.device_status.enum_type.values_by_number[_device_enum].name
        #     # )
        #     all_locations.append(location)
    if endpoint.identifier_list:
        for _endpoint in endpoint.identifier_list.values:
            match _endpoint.type:
                case endpoint_models.IDENTIFIER_TYPE_MAC_ADDR:
                    mac_address = convert_protobuf_value(_endpoint.value)
                    logging.debug(f"MAC TYPE: {type(mac_address)}")
                case endpoint_models.IDENTIFIER_TYPE_IPV4_ADDR:
                    ip_address = convert_protobuf_value(_endpoint.value)
                case endpoint_models.IDENTIFIER_TYPE_HOSTNAME:
                    hostname = convert_protobuf_value(_endpoint.value)
    all_endpoints.append(EndpointLocation(
       hostname = hostname,
       mac_address = mac_address,
       ip_address = ip_address,
       location_list = all_locations        
    ))
    return(all_endpoints)

def serialize_arista_protobuf(pb_obj, max_depth=10, current_depth=0):
    """Recursively serialize Arista protobuf objects to dict with enum names"""
    if current_depth >= max_depth:
        return str(pb_obj)
    
    result = {}
    
    try:
        for field, value in pb_obj.ListFields():
            field_name = field.name
            
            try:
                # Handle different field types
                if hasattr(value, 'ListFields'):  # Nested protobuf message
                    result[field_name] = serialize_arista_protobuf(value, max_depth, current_depth + 1)
                    
                elif hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):  # Repeated field
                    result[field_name] = []
                    for item in value:
                        if hasattr(item, 'ListFields'):  # Repeated protobuf messages
                            result[field_name].append(serialize_arista_protobuf(item, max_depth, current_depth + 1))
                        else:
                            result[field_name].append(convert_protobuf_value(item, field))
                            
                else:  # Simple field
                    result[field_name] = convert_protobuf_value(value, field)
                    
            except Exception as e:
                result[field_name] = f"<serialization_error: {str(e)}>"
                
    except Exception as e:
        return {"serialization_error": str(e), "object_type": str(type(pb_obj))}
    
    return result

def convert_protobuf_value(value, field_descriptor=None):
    """Convert protobuf values to JSON-serializable types, preserving enum names"""
    
    # Check if this is an enum field
    if field_descriptor and hasattr(field_descriptor, 'enum_type') and field_descriptor.enum_type:
        try:
            # Get the enum name from the descriptor
            enum_name = field_descriptor.enum_type.values_by_number[value].name
            return enum_name
        except (KeyError, AttributeError):
            # Fallback to int if enum name lookup fails
            return value
    
    # Handle other types
    if isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    elif hasattr(value, 'seconds') and hasattr(value, 'nanos'):  # Timestamp
        return {"seconds": value.seconds, "nanos": value.nanos}
    else:
        return str(value)
