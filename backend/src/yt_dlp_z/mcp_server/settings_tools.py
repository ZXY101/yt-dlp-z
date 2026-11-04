from typing import Annotated, Any, Literal

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from yt_dlp_z.mcp_server.api_client import ApiClient

Section = Literal["general", "notifications", "proxies", "ytdlp", "po_tokens"]
# Each section: where it is read, and where changes are saved.
SECTIONS: dict[str, tuple[str, str]] = {
    "general": ("/api/settings", "/api/settings"),
    "notifications": ("/api/notifications", "/api/notifications"),
    "proxies": ("/api/proxies/settings", "/api/proxies/settings"),
    "ytdlp": ("/api/ytdlp", "/api/ytdlp/preferences"),
    "po_tokens": ("/api/ytdlp/pot", "/api/ytdlp/pot"),
}


def register_settings_tools(server: MCPServer, api: ApiClient) -> None:
    @server.tool(annotations=ToolAnnotations(readOnlyHint=True), structured_output=False)
    async def get_settings(section: Section, ctx: Context) -> dict[str, Any]:
        """Read one section of the settings. Secrets are never included."""
        read_path, _ = SECTIONS[section]
        return await api.call(ctx, "GET", read_path)  # type: ignore[no-any-return]

    @server.tool(structured_output=False)
    async def update_settings(
        section: Section,
        changes: Annotated[
            dict[str, Any],
            Field(description="Only the fields to change, named as get_settings shows them."),
        ],
        ctx: Context,
    ) -> dict[str, Any]:
        """Change settings in one section; everything else in it stays as it is."""
        read_path, write_path = SECTIONS[section]
        current = await api.call(ctx, "GET", read_path)
        unknown = sorted(set(changes) - set(current))
        if unknown:
            raise ToolError(f"Unknown {section} settings: {', '.join(unknown)}.")
        await api.call(ctx, "PUT", write_path, {**current, **changes})
        return await api.call(ctx, "GET", read_path)  # type: ignore[no-any-return]

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True), structured_output=False)
    async def get_system_status(ctx: Context) -> dict[str, Any]:
        """The yt-dlp version and whether ffmpeg and Deno are available, for debugging."""
        return await api.call(ctx, "GET", "/api/system")  # type: ignore[no-any-return]

    @server.tool(structured_output=False)
    async def update_ytdlp(ctx: Context) -> str:
        """Install the newest yt-dlp on the chosen channel. Runs in the background."""
        await api.call(ctx, "POST", "/api/ytdlp/update")
        return 'Update started. get_settings("ytdlp") shows how it went.'
