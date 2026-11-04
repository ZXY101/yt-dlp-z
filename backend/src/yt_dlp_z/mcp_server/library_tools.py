from typing import Annotated, Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from yt_dlp_z.mcp_server.api_client import ApiClient
from yt_dlp_z.mcp_server.download_plan import find_preset

READ_ONLY = ToolAnnotations(readOnlyHint=True)
Changes = Annotated[
    dict[str, Any],
    Field(description="Only the fields to change; read the current ones from the list tool."),
]


async def _preset_id(api: ApiClient, ctx: Context, name: str | None) -> int | None:
    if name is None:
        return None
    preset = find_preset(await api.call(ctx, "GET", "/api/presets"), name)
    if preset is None:
        raise ToolError(f'No preset named "{name}".')
    return int(preset["id"])


def register_library_tools(server: MCPServer, api: ApiClient) -> None:
    _register_preset_tools(server, api)
    _register_subscription_tools(server, api)


def _register_preset_tools(server: MCPServer, api: ApiClient) -> None:
    @server.tool(annotations=READ_ONLY, structured_output=False)
    async def list_presets(ctx: Context) -> list[dict[str, Any]]:
        """Saved download settings, with the yt-dlp options each one sets."""
        return await api.call(ctx, "GET", "/api/presets")  # type: ignore[no-any-return]

    @server.tool(structured_output=False)
    async def save_preset(name: str, changes: Changes, ctx: Context) -> dict[str, Any]:
        """Change a preset, or create it if the name is new.

        Fields: options (yt-dlp long flags, e.g. {"--format": "bv*+ba"}), extra_args, output_dir,
        cookie_id, folders, file_name, media_files, live_chat, proxy_mode, kind, is_default,
        recording."""
        existing = find_preset(await api.call(ctx, "GET", "/api/presets"), name)
        if existing is None:
            body = {"name": name, **changes}
            return await api.call(ctx, "POST", "/api/presets", body)  # type: ignore[no-any-return]
        path = f"/api/presets/{existing['id']}"
        return await api.call(ctx, "PUT", path, {**existing, **changes})  # type: ignore[no-any-return]

    @server.tool(annotations=READ_ONLY, structured_output=False)
    async def list_cookies(ctx: Context) -> list[dict[str, Any]]:
        """Uploaded cookies files: names, ids and domains, never their contents."""
        return await api.call(ctx, "GET", "/api/cookies")  # type: ignore[no-any-return]


def _register_subscription_tools(server: MCPServer, api: ApiClient) -> None:
    @server.tool(annotations=READ_ONLY, structured_output=False)
    async def list_subscriptions(ctx: Context) -> list[dict[str, Any]]:
        """Watched channels and playlists, with their settings and last check."""
        return await api.call(ctx, "GET", "/api/subscriptions")  # type: ignore[no-any-return]

    @server.tool(structured_output=False)
    async def add_subscription(
        channel: Annotated[str, Field(description="Channel URL, @handle, or playlist URL.")],
        ctx: Context,
        preset: Annotated[str | None, Field(description="Preset name for its videos.")] = None,
        stream_preset: Annotated[str | None, Field(description="Preset for its streams.")] = None,
        backfill: Annotated[
            int, Field(ge=0, description="How many of the newest uploads to download now.")
        ] = 0,
        poll_minutes: Annotated[int | None, Field(description="Minutes between checks.")] = None,
        filters: Annotated[
            dict[str, Any] | None,
            Field(
                description=(
                    'Which uploads to take. Default: {"content_types": ["video"]}. Types: video, '
                    "short, stream (live streams and premieres). Also title_include, "
                    "title_exclude, min_duration, max_duration, published_after, "
                    "include_members_only."
                )
            ),
        ] = None,
    ) -> dict[str, Any]:
        """Start watching a channel or playlist; matching uploads download automatically."""
        body: dict[str, Any] = {
            "channel": channel,
            "backfill": backfill,
            "preset_id": await _preset_id(api, ctx, preset),
            "stream_preset_id": await _preset_id(api, ctx, stream_preset),
        }
        if poll_minutes is not None:
            body["poll_minutes"] = poll_minutes
        if filters is not None:
            body["filters"] = filters
        return await api.call(ctx, "POST", "/api/subscriptions", body)  # type: ignore[no-any-return]

    @server.tool(structured_output=False)
    async def update_subscription(
        subscription_id: int, changes: Changes, ctx: Context
    ) -> dict[str, Any]:
        """Change a subscription.

        Fields: preset_id, stream_preset_id, cookie_id, output_dir, filters, poll_minutes,
        enabled (false pauses it), keep_days (delete downloads after N days; null keeps them)."""
        path = f"/api/subscriptions/{subscription_id}"
        current = await api.call(ctx, "GET", path)
        return await api.call(ctx, "PUT", path, {**current, **changes})  # type: ignore[no-any-return]

    @server.tool(annotations=READ_ONLY, structured_output=False)
    async def list_subscription_videos(subscription_id: int, ctx: Context) -> list[dict[str, Any]]:
        """The 50 newest uploads a subscription has seen, what happened to each, and why.

        Use it to find out why a video wasn't downloaded."""
        path = f"/api/subscriptions/{subscription_id}/videos"
        return await api.call(ctx, "GET", path)  # type: ignore[no-any-return]

    @server.tool(structured_output=False)
    async def check_subscription(subscription_id: int, ctx: Context) -> str:
        """Look for new uploads on this subscription now rather than at its next check."""
        await api.call(ctx, "POST", f"/api/subscriptions/{subscription_id}/check")
        return "Check started. New uploads will appear in list_downloads."
