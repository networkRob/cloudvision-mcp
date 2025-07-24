from typing import TypedDict

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
