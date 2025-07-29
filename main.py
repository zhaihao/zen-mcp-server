from fastmcp import FastMCP


from src.looking_glass import lg_mcp
from src.utils import slog



mcp = FastMCP(
    name="Zenlayer MCP Server",
    instructions='',
)

# 直接导入服务器
mcp.mount(lg_mcp)
slog.info("setup mcp server...")

http_app = mcp.http_app()

if __name__ == '__main__':
    mcp.run(transport='streamable-http', host='0.0.0.0', port=3000)
