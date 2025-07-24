import grpc

def createConnection(datadict):
    # datadict = get_env_vars()
    # create the header object for the token
    callCreds = grpc.access_token_call_credentials(datadict['cvtoken'])

    with open(datadict["cert"], "rb") as f:
        cert = f.read()
    channelCreds = grpc.ssl_channel_credentials(root_certificates=cert)

    connCreds = grpc.composite_channel_credentials(channelCreds, callCreds)
    return(connCreds)

