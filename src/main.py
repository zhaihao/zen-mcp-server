from fastmcp import FastMCP
import uvicorn
from fastmcp.server.auth import BearerAuthProvider

from fastmcp.server.auth.providers.bearer import RSAKeyPair

from src.looking_glass import lg_mcp
from src.utils import slog

issuer = 'https://console.zenlayer.com'
audience = 'zenlayer-mcp-test-server'
key_pair = RSAKeyPair.generate()

auth = BearerAuthProvider(
    public_key=key_pair.public_key,
    issuer=issuer,
    audience=audience
)

mcp = FastMCP(
    name="Zenlayer MCP Server",
    instructions='',
    # auth=auth
)

# 直接导入服务器
mcp.mount(lg_mcp)
slog.info("setup mcp server...")

http_app = mcp.http_app()

if __name__ == '__main__':
    #
    # token = key_pair.create_token(
    #     subject='console-mcp-dev',
    #     issuer=issuer,
    #     audience=audience,
    #     scopes=["read", "write"]
    # )
    # slog.info(f'token:\n{token}')
    uvicorn.run("main:http_app", reload=False,host='0.0.0.0', port=3000)
