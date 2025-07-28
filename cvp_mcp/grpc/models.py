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

class BugExposure(TypedDict):
    serial_number: str
    bug_ids: list[int]
    cve_ids: list[int]
    bug_count: int
    cve_count: int
    highest_cve_exposure: str
    highest_but_exposure: str

class ProbeStats(TypedDict):
    serial_number: str
    host: str
    vrf: str
    source_intf: str
    latency_millis: float
    jitter_millis: float
    http_response_time_millis: float
    packet_loss_percent: int
    error: str
    
