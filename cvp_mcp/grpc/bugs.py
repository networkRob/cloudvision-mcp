from arista.bugexposure.v1 import models
from arista.bugexposure.v1 import services
from .utils import createConnection
from .models import BugExposure
import grpc
import logging
import os
import json



RPC_TIMEOUT = 30  # in second
EOS_PLATFORMS = ["DCS-", "CCS-", "AWE-"]
EOS_VIRTUAL = ["cEOS", "vEOS"]

def get_all_bug_exposure(datadict):
    """
    Gets all bugs in CVP
    """
    connCreds = createConnection(datadict)
    all_bugs= []
    with grpc.secure_channel(datadict["cvp"], connCreds) as channel:
        # create the Python stub for the inventory API
        # this is essentially the client, but Python gRPC refers to them as "stubs"
        # because they call into the gRPC C API
        stub = services.BugExposureServiceStub(channel)

        get_all_req = services.BugExposureStreamRequest()

        print(json.dumps(stub.GetAll(get_all_req, timeout=RPC_TIMEOUT)))

        for bug in stub.GetAll(get_all_req, timeout=RPC_TIMEOUT):
            logging.info(json.dumps(bug, indent=2))
            try:
                # Check to make sure the device is valid
                if bug.value.key.device_id != "127.0.0.1":
                    match bug.value.highest_bug_exposure:
                        case models.HIGHEST_EXPOSURE_HIGH:
                            highest_bug = "High"
                        case models.HIGHEST_EXPOSURE_LOW:
                            highest_bug = "Low"
                        case models.HIGHEST_EXPOSURE_NONE:
                            highest_bug = "None"
                        case _:
                            highest_bug = "Unspecified"
                    match bug.value.highest_cve_exposure:
                        case models.HIGHEST_EXPOSURE_HIGH:
                            highest_cve = "High"
                        case models.HIGHEST_EXPOSURE_LOW:
                            highest_cve = "Low"
                        case models.HIGHEST_EXPOSURE_NONE:
                            highest_cve = "None"
                        case _:
                            highest_cve = "Unspecified"
                    bug_exposure = BugExposure(
                        serial_number = bug.value.key.device_id.value,
                        bug_ids = bug.value.bug_ids,
                        cve_ids = bug.value.cve_ids,
                        bug_count = bug.value.bug_count,
                        cve_count = bug.value.cve_count,
                        highest_cve_exposure = highest_cve,
                        highest_bug_exposre = highest_bug
                    )
                    all_bugs.append(bug_exposure)
            except Exception as e:
                logging.info(f"Error with device: {e}")
        return(all_bugs)
        # return(json.dumps(all_devices))
