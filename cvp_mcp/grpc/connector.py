from cloudvision.Connector.grpc_client import GRPCClient, create_query
import logging
import json

def find_frozen_dicts(obj, path="root"):
    if hasattr(obj, '__class__') and 'frozendict' in str(type(obj)).lower():
        logging.debug(f"Found FrozenDict at {path}: {type(obj)}")
    elif isinstance(obj, dict):
        for key, value in obj.items():
            find_frozen_dicts(value, f"{path}.{key}")
    elif isinstance(obj, (list, tuple)):
        for i, item in enumerate(obj):
            find_frozen_dicts(item, f"{path}[{i}]")

def serialize_cloudvision_data(data):
    """Serialize CloudVision data structures to JSON, handling FrozenDict objects"""
    def convert_frozen_dicts(obj):
        if hasattr(obj, '__class__') and 'FrozenDict' in str(type(obj)):
            return dict(obj)
        elif isinstance(obj, dict):
            return {k: convert_frozen_dicts(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_frozen_dicts(item) for item in obj]
        return obj
    
    converted = convert_frozen_dicts(data)
    return(converted)

def get(client, dataset, pathElts):
    ''' Returns a query on a path element'''
    result = {}
    query = [
        create_query([(pathElts, [])], dataset)
    ]

    for batch in client.get(query):
        for notif in batch["notifications"]:
            bug_info = serialize_cloudvision_data(notif['updates'])
            result.update(bug_info)
            # result.update(notif["updates"])
            # find_frozen_dicts(notif['updates'])
    return result

def getBugInfo(client, bugId, mem=dict()):
    if bugId in mem:
        return mem[bugId]
    pathElts = [
        "BugAlerts",
        "bugs",
        bugId
    ]
    dataset = "analytics"
    bugInfo = get(client, dataset, pathElts)
    mem[bugId] = bugInfo

    return bugInfo

def conn_get_info_bugs(datadict, bug_ids):
    """
    Returns an array of information about each bug id
    """
    all_bugs = {}
    dataset = "analytics"
    cv_addr = f"{datadict['cvp']}:443"
    with GRPCClient(grpcAddr=cv_addr, tokenValue=datadict["cvtoken"]) as client:
        for bugId in bug_ids:
            pathElts = [
                "BugAlerts",
                "bugs",
                bugId
            ]
            try:
                bugInfo = get(client, dataset, pathElts)
                all_bugs[bugId] = dict(bugInfo)
            except Exception as e:
                logging.error(f"Get Bug: {e}")
    # logging.debug(type(all_bugs))
    # logging.debug(f"All Bugs: {json.dumps(all_bugs)}")
    return(all_bugs)
