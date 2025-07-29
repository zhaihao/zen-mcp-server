#!/usr/bin/env python3
"""
OpenAI Dashboard compatible MCP server
"""
from fastmcp import FastMCP
from src.looking_glass import lg_mcp
from src.utils import slog

# 创建MCP服务器
mcp = FastMCP(
    name="Zenlayer MCP Server",
    instructions='Network latency query service for Zenlayer backbone network using IATA city codes',
)

# 挂载工具
mcp.mount(lg_mcp)

if __name__ == "__main__":
    slog.info("Starting OpenAI-compatible MCP server...")
    mcp.run(transport='http', host='0.0.0.0', port=3000)