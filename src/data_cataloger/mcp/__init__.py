"""MCP Server module for Data Cataloger.

Provides Model Context Protocol server for AI assistants to access
enriched database metadata through standardized tools.
"""

from data_cataloger.mcp.server import create_mcp_server

__all__ = ["create_mcp_server"]
