"""Entry point for running MCP server."""

import uvicorn

from data_cataloger.mcp.server import create_sse_app

if __name__ == "__main__":
    app = create_sse_app()
    uvicorn.run(app, host="0.0.0.0", port=8001)
