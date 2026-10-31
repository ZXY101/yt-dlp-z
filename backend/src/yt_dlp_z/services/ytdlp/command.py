from pathlib import Path

# yt-dlp prints these prefixes (via the templates below) so the runner can pick
# structured data out of its normal output. The E2E stub prints the same ones.
PROGRESS_MARKER = "[ytdlpz:progress]"
INFO_MARKER = "[ytdlpz:info]"
FILE_MARKER = "[ytdlpz:file]"
# Only printed for media-server output (services/media_server).
NFO_MARKER = "[ytdlpz:nfo]"

INFO_FIELDS = "id,title,uploader,duration,webpage_url"


def build_command(
    ytdlp_command: list[str], user_args: list[str], url: str, download_dir: Path
) -> list[str]:
    return [
        *ytdlp_command,
        # User/system yt-dlp config files must not change what the app runs.
        "--ignore-config",
        "--newline",
        "--color",
        "never",
        "--progress",
        "--progress-template",
        f"download:{PROGRESS_MARKER}%(progress)j",
        "--print",
        f"before_dl:{INFO_MARKER}%(.{{{INFO_FIELDS}}})j",
        "--print",
        f"after_move:{FILE_MARKER}%(filepath)j",
        # --print implies --quiet; keep yt-dlp's normal messages for the job log.
        "--no-quiet",
        *user_args,
        "--paths",
        f"home:{download_dir}",
        "--",
        url,
    ]
