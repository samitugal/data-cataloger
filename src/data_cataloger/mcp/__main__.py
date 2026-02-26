"""Entry point for running MCP server."""

import asyncio

from mcp.server.stdio import stdio_server

from data_cataloger.mcp.server import create_mcp_server


async def main() -> None:
    """Run MCP server with stdio transport."""
    server = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
