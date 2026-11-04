from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.types import Receive, Scope, Send

from yt_dlp_z.api.deps import has_api_token
from yt_dlp_z.api.state import AppState
from yt_dlp_z.mcp_server.api_client import ApiClient
from yt_dlp_z.mcp_server.download_tools import register_download_tools
from yt_dlp_z.mcp_server.library_tools import register_library_tools
from yt_dlp_z.mcp_server.settings_tools import register_settings_tools

INSTRUCTIONS = """Controls a yt-dlp-z server: downloads, live recordings, presets, channel
subscriptions and settings. Before bulk changes or deleting files, confirm with the user."""


def _build_server(app: FastAPI) -> MCPServer:
    server = MCPServer("yt-dlp-z", instructions=INSTRUCTIONS)
    api = ApiClient(app)
    register_download_tools(server, api)
    register_library_tools(server, api)
    register_settings_tools(server, api)
    return server


class _McpEndpoint:
    """A raw ASGI app: Starlette would wrap a plain function as a request handler."""

    def __init__(self, app: FastAPI, server: MCPServer) -> None:
        self._app = app
        self._server = server

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        state: AppState = self._app.state.app_state
        async with state.session_factory() as db:
            allowed = await has_api_token(Request(scope), state, db)
        if allowed:
            await self._server.session_manager.handle_request(scope, receive, send)
            return
        response = JSONResponse(
            {"detail": "An API token is required"},
            status_code=401,
            headers={"WWW-Authenticate": "Bearer"},
        )
        await response(scope, receive, send)


def mount_mcp(app: FastAPI) -> MCPServer:
    """Serves MCP at /mcp. Its session manager must run inside the app's lifespan."""
    server = _build_server(app)
    # Stateless: every call is self-contained and carries its own token. The SDK's Host
    # check is off because servers are reached by any name or IP; a browser on another
    # site can't send the bearer token this endpoint requires.
    server.streamable_http_app(
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )
    endpoint = _McpEndpoint(app, server)
    app.router.add_route("/mcp", endpoint, include_in_schema=False)  # type: ignore[arg-type]
    return server
