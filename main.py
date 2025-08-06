# -*- coding: utf-8 -*-
import logging
from fastmcp import FastMCP
from src.looking_glass import lg_mcp
from src.utils import slog

# 启用详细日志
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("fastmcp").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.DEBUG)

mcp = FastMCP(
    name="Zenlayer MCP Server",
    instructions='Network latency query service for Zenlayer backbone network',
    stateless_http=False,
)

# 直接导入服务器
mcp.mount(lg_mcp)
slog.info("setup mcp server...")

if __name__ == '__main__':
    slog.info("Starting MCP server with detailed logging...")
    mcp.run(transport='http', host='0.0.0.0', port=3100, log_level="debug")
