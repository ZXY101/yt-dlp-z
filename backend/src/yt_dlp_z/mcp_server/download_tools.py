from typing import Annotated, Any

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from yt_dlp_z.mcp_server.api_client import ApiClient
from yt_dlp_z.mcp_server.download_plan import (
    default_preset,
    find_preset,
    is_video_in_playlist,
    job_from_preset,
    recording_request,
    with_playlist_choice,
)
from yt_dlp_z.schemas.live_chat import OverlayStyle

READ_ONLY = ToolAnnotations(readOnlyHint=True)
# Enough to judge a download by; the full job is mostly options the agent didn't ask about.
SUMMARY_FIELDS = (
    "id",
    "title",
    "url",
    "status",
    "kind",
    "progress",
    "speed",
    "eta",
    "scheduled_at",
    "part",
    "filepath",
    "error",
    "chat_status",
    "subscription_id",
)
DownloadId = Annotated[int, Field(description="The id from list_downloads.")]


def _summary(job: dict[str, Any]) -> dict[str, Any]:
    return {field: job.get(field) for field in SUMMARY_FIELDS}


async def _named_preset(api: ApiClient, ctx: Context, name: str | None) -> tuple[Any, Any]:
    presets = await api.call(ctx, "GET", "/api/presets")
    if name is None:
        return presets, None
    preset = find_preset(presets, name)
    if preset is None:
        known = ", ".join(item["name"] for item in presets) or "none"
        raise ToolError(f'No preset named "{name}". Presets: {known}.')
    return presets, preset


async def _start(
    api: ApiClient,
    ctx: Context,
    url: str,
    preset: str | None,
    whole_playlist: bool,
    output_dir: str | None,
) -> dict[str, Any]:
    presets, chosen = await _named_preset(api, ctx, preset)
    cookie_id = chosen["cookie_id"] if chosen else None
    alone = is_video_in_playlist(url) and not whole_playlist
    probe = {"url": url, "cookie_id": cookie_id, "no_playlist": alone}
    info = await api.call(ctx, "POST", "/api/media/probe", probe)
    if info["kind"] in {"playlist", "channel"} and not whole_playlist:
        count = info["entry_count"] or "an unknown number of"
        raise ToolError(
            f'"{info["title"]}" is a {info["kind"]} with {count} videos. '
            "Set whole_playlist to download them all."
        )
    preset_used = chosen or default_preset(presets, info["kind"])
    job = with_playlist_choice(job_from_preset(preset_used), url, whole_playlist)
    job.update(url=url, title=info["title"])
    if info["kind"] in {"live", "upcoming"}:
        job["recording"] = recording_request(preset_used, presets, info)
    if output_dir:
        job["output_dir"] = output_dir
    created = await api.call(ctx, "POST", "/api/jobs", job)
    return {**_summary(created), "preset": preset_used["name"] if preset_used else None}


def register_download_tools(server: MCPServer, api: ApiClient) -> None:
    @server.tool(annotations=READ_ONLY, structured_output=False)
    async def check_link(url: str, ctx: Context) -> dict[str, Any]:
        """What a link points at (video, playlist, channel, live, upcoming) without downloading."""
        return await api.call(ctx, "POST", "/api/media/probe", {"url": url})  # type: ignore[no-any-return]

    @server.tool(structured_output=False)
    async def start_download(
        url: str,
        ctx: Context,
        preset: Annotated[
            str | None, Field(description="Preset name. Empty: the default for this kind of link.")
        ] = None,
        whole_playlist: Annotated[
            bool,
            Field(description="Required to download every video of a playlist or channel link."),
        ] = False,
        output_dir: Annotated[
            str | None,
            Field(description="Empty: the preset's folder. Relative: inside the download folder."),
        ] = None,
    ) -> dict[str, Any]:
        """Download a link, or record it when it is a live or upcoming stream.

        Checks the link first. Refuses a playlist or channel unless whole_playlist is set."""
        return await _start(api, ctx, url, preset, whole_playlist, output_dir)

    @server.tool(annotations=READ_ONLY, structured_output=False)
    async def list_downloads(
        ctx: Context,
        limit: Annotated[int, Field(ge=1, le=200)] = 20,
        status: Annotated[
            str | None,
            Field(description="Only this status, e.g. running, queued, failed, completed."),
        ] = None,
    ) -> list[dict[str, Any]]:
        """Downloads and recordings, newest first."""
        jobs = await api.call(ctx, "GET", "/api/jobs", params={"limit": 200 if status else limit})
        matching = [job for job in jobs if status is None or job["status"] == status]
        return [_summary(job) for job in matching[:limit]]

    @server.tool(annotations=READ_ONLY, structured_output=False)
    async def get_download(
        job_id: DownloadId,
        ctx: Context,
        log_lines: Annotated[int, Field(ge=0, le=500, description="Last lines of its log.")] = 0,
    ) -> dict[str, Any]:
        """One download with all its settings, and optionally the end of its log."""
        job: dict[str, Any] = await api.call(ctx, "GET", f"/api/jobs/{job_id}")
        if log_lines:
            log = await api.call(ctx, "GET", f"/api/jobs/{job_id}/log")
            job["log"] = "\n".join(log.splitlines()[-log_lines:])
        return job

    @server.tool(structured_output=False)
    async def cancel_download(job_id: DownloadId, ctx: Context) -> dict[str, Any]:
        """Stop a queued or running download or recording."""
        return _summary(await api.call(ctx, "POST", f"/api/jobs/{job_id}/cancel"))

    @server.tool(structured_output=False)
    async def retry_download(job_id: DownloadId, ctx: Context) -> dict[str, Any]:
        """Run a failed or cancelled download again."""
        return _summary(await api.call(ctx, "POST", f"/api/jobs/{job_id}/retry"))

    @server.tool(structured_output=False)
    async def rebuild_chat_overlay(
        job_id: DownloadId,
        ctx: Context,
        style: Annotated[
            OverlayStyle | None,
            Field(description="How the overlay looks. Empty: the look it already has."),
        ] = None,
    ) -> dict[str, Any]:
        """Build a download's live chat overlay (.ass) again from its saved chat, replacing
        the old one. Needs a download that saved its live chat."""
        body = style.model_dump() if style else None
        path = f"/api/jobs/{job_id}/live-chat/overlay"
        return _summary(await api.call(ctx, "POST", path, body=body))

    @server.tool(annotations=ToolAnnotations(destructiveHint=True), structured_output=False)
    async def remove_download(
        job_id: DownloadId,
        ctx: Context,
        delete_files: Annotated[
            bool,
            Field(description="Also delete its saved files for good. Off: history entry only."),
        ] = False,
    ) -> str:
        """Remove a finished download from the history, optionally deleting its files."""
        params = {"delete_files": delete_files}
        await api.call(ctx, "DELETE", f"/api/jobs/{job_id}", params=params)
        return "Removed, with its files." if delete_files else "Removed. Its files were kept."
