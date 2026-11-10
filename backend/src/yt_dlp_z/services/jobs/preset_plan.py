from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

from yt_dlp_z.schemas.recording import DEFAULT_RECORDING, RecordingSettings
from yt_dlp_z.services.live.plan import plan_recording

SECONDS_PER_HOUR = 3600
# Which kind of preset suits what the link check found.
PRESET_KIND_FOR = {
    "video": "video",
    "playlist": "playlist",
    "channel": "playlist",
    "live": "live",
    "upcoming": "live",
}
# What a job copies from its preset.
PRESET_JOB_FIELDS = (
    "options",
    "extra_args",
    "output_dir",
    "cookie_id",
    "folders",
    "file_name",
    "video_folder",
    "media_files",
    "live_chat",
    "proxy_mode",
)


def find_preset(presets: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    return next((preset for preset in presets if preset["name"].lower() == name.lower()), None)


def default_preset(presets: list[dict[str, Any]], media_kind: str) -> dict[str, Any] | None:
    """The default for this kind of link, else the default for any link."""
    wanted = PRESET_KIND_FOR[media_kind]
    defaults = {preset["kind"]: preset for preset in presets if preset["is_default"]}
    return defaults.get(wanted) or defaults.get("any")


def is_video_in_playlist(url: str) -> bool:
    query = parse_qs(urlparse(url).query)
    return "v" in query and "list" in query


def job_from_preset(preset: dict[str, Any] | None) -> dict[str, Any]:
    if preset is None:
        return {}
    return {field: preset[field] for field in PRESET_JOB_FIELDS}


def with_playlist_choice(job: dict[str, Any], url: str, whole_playlist: bool) -> dict[str, Any]:
    """A video opened from a playlist would otherwise follow yt-dlp's default."""
    if not is_video_in_playlist(url):
        return job
    flag = "--yes-playlist" if whole_playlist else "--no-playlist"
    return {**job, "options": {**job.get("options", {}), flag: True}}


def _hours(seconds: int | None) -> int | None:
    return seconds // SECONDS_PER_HOUR if seconds else None


def _recording_settings(
    preset: dict[str, Any] | None, presets: list[dict[str, Any]]
) -> RecordingSettings:
    """The preset's own settings, else the default live-stream preset's."""
    for candidate in (preset, default_preset(presets, "live")):
        if candidate and candidate["recording"]:
            return RecordingSettings.model_validate(candidate["recording"])
    return DEFAULT_RECORDING


def recording_request(
    preset: dict[str, Any] | None, presets: list[dict[str, Any]], info: dict[str, Any]
) -> dict[str, Any]:
    """Applies the recording settings to this stream, as the download form does."""
    settings = _recording_settings(preset, presets)
    live_since = info["live_since"] if info["kind"] == "live" else None
    since = datetime.fromisoformat(live_since) if live_since else None
    plan = plan_recording(settings, since, datetime.now(UTC))
    return {
        "from_start": plan.record_from_start,
        "starts_at": info["starts_at"] if info["kind"] == "upcoming" else None,
        "part_hours": _hours(plan.part_seconds),
        "max_hours": _hours(plan.max_seconds),
        "vod_after_hours": _hours(plan.vod_after_seconds),
        "vod_replace": plan.vod_replace,
    }
