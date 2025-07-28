from arista.connectivitymonitor.v1 import models
from arista.connectivitymonitor.v1 import services
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
