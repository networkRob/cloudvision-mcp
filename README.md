# MCP Server for CloudVision

This MCP server can be used to query and interact with Arista CloudVision.

## Usage

To run, you can the server via `uv`. Make sure you load your environment variables for `CVP` and `CVPTOKEN` prior to running.

```
  uv run cloudvision_mcp.py
```

### Alternate Method

To run in a container, build the image first.
```
  podman build -t cloudvision_mcp:latest
```

Populate an env-file, sample below.

`cvp-mcp.env`
```
  CVP=<cvp_server_address>
  CVPTOKEN=<service_account_api_token>
```

Run
```
  podman run -d --name cvp-mcp --env-file cvp-mcp.env cloudvision-mcp:latest
```

The server will be running by default with Streamable HTTP on port 8000

## Server Options

The server can be configured with the following flags
| Flag | Description |
| --- | --- |
| -t | MCP Transport {"http", "stdio"} |
| -p | MCP Port for Streamable HTTP (default=8000) |
| -c | CVP Connection protocol {"grcp", "http"} (default=grpc) |

### **Note**

For gRPC connections, a trusted cert mut be running on CloudVision. Otherwise, you will need to have a copy of the self-signed cert in the project directory before building the container image. The cert file should be named `cert.pem`

## Client Configurations

The example client configs can work with Claude Desktop or a local Ollama LLM via (https://github.com/jonigl/mcp-client-for-ollama) project.

### STDIO MCP Server Configuration
```
  {
    "mcpServers": {
      "CVP MCP Server": {
        "command": "uv",
        "args": [
          "run",
          "--directory",
          "<path_to_project_directory>",
          "./cloudvision_mcp.py"
        ]
      }
    }
  }
```

### Streamable HTTP Server Configuration
```
  {
    "mcpServers": {
      "CVP MCP Server": {
        "type": "streamable-http",
        "url": "<mcp_server_address>:<port>/mcp"
      }
    }
  }
  
```
