from arista.connectivitymonitor.v1 import models
from arista.connectivitymonitor.v1 import services
from google.protobuf import wrappers_pb2 as wrappers
from .utils import RPC_TIMEOUT, convert_response_to_probe_stat
from .models import ProbeStats
import grpc
import logging
import os
import json
import sys



def grpc_all_probe_status(channel):
    """
    Gets all Connectivity Monitor Probe Stats  in CVP
    """
    all_probes = []
    stub = services.ProbeStatsServiceStub(channel)
    get_all_req = services.ProbeStatsStreamRequest()
    for probe in stub.GetAll(get_all_req, timeout=RPC_TIMEOUT):
        try:
            _probe = convert_response_to_probe_stat(probe)
            all_probes.append(_probe)
        except Exception as e:
            logging.error(f"Error with probe: {e}")
    return(all_probes)


def grpc_one_probe_status(channel, serial_number="", host="", vrf="", sourceIntf=""):
    """
    Gets one Connectivity Monitor Probe Stats in CVP
    """
    all_probes = []
    stub = services.ProbeStatsServiceStub(channel)
    get_all_req = services.ProbeStatsStreamRequest()
    if serial_number:
        get_all_req.partial_eq_filter.append(
            models.ProbeStats(
                key = models.ProbeStatsKey(
                    device_id = wrappers.StringValue(value=serial_number)
                )
            )
        )
    if host:
        get_all_req.partial_eq_filter.append(
            models.ProbeStats(
                key = models.ProbeStatsKey(
                    host= wrappers.StringValue(value=host)
                )
            )
        )
    if vrf:
        get_all_req.partial_eq_filter.append(
            models.ProbeStats(
                key = models.ProbeStatsKey(
                    vrf= wrappers.StringValue(value=vrf)
                )
            )
        )
    if sourceIntf:
        get_all_req.partial_eq_filter.append(
            models.ProbeStats(
                key = models.ProbeStatsKey(
                    source_intf= wrappers.StringValue(value=sourceIntf)
                )
            )
        )
    try:
        for _probe in  stub.GetAll(get_all_req, timeout=RPC_TIMEOUT):
            logging.debug(f"One PRE PROBE: {_probe}")
            probe = convert_response_to_probe_stat(_probe)
            logging.debug(f"One PROBE: {probe}")
            all_probes.append(probe)
        return(all_probes)
    except Exception as e:
        logging.error(f"Error with probe: {e}")
        return(ProbeStats())
