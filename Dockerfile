FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY palette_remap/ ./palette_remap/

RUN pip install --no-cache-dir ".[mcp]"

# Mount your images/palette files here at runtime:
#   --mount type=bind,src=/host/path,dst=/images
VOLUME ["/images"]

ENTRYPOINT ["palette-remap-mcp"]
