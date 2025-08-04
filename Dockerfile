FROM docker.io/python:3.13

RUN pip3 install uv

RUN mkdir /workspace

WORKDIR /workspace

COPY . .

RUN uv sync

ENTRYPOINT [ "uv", "run", "cloudvision_mcp.py" ]
