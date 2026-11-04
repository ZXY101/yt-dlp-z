"""Builds a video's .ass overlay from its saved chat JSON."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from yt_dlp_z.schemas.live_chat import OverlayStyle
from yt_dlp_z.services.live_chat.ass import EVENTS_HEADER, dialogue, header
from yt_dlp_z.services.live_chat.comments import Comment, read_comments
from yt_dlp_z.services.live_chat.fonts import FAMILY, find_font, fonts_section
from yt_dlp_z.services.live_chat.layout import Layout

logger = logging.getLogger(__name__)

CHAT_SUFFIX = ".live_chat.json"


@dataclass(frozen=True)
class OverlayResult:
    comments: int
    shown: int


def overlay_path(chat_path: Path) -> Path:
    """Beside the video with the video's name, where players look for subtitles."""
    return chat_path.with_name(chat_path.name.removesuffix(CHAT_SUFFIX) + ".ass")


def _timed_comments(chat_path: Path, style: OverlayStyle) -> list[Comment]:
    comments = []
    for comment in read_comments(chat_path, style.show_paid):
        seconds = comment.seconds + style.offset_seconds
        if seconds >= 0:  # Below zero: waiting-room chat, before the video starts.
            comments.append(
                Comment(seconds, comment.text, comment.colour, comment.author, comment.role)
            )
    comments.sort(key=lambda comment: comment.seconds)
    return comments


def _fonts_or_nothing(characters: set[str]) -> tuple[str, str]:
    """The font's family and its [Fonts] section. A font problem shouldn't lose the overlay:
    players with the font installed, or a fallback set, still show it."""
    font = find_font()
    if font is None:
        logger.warning("No CJK font found, so the chat overlay has none embedded")
        return FAMILY, ""
    try:
        return font.family, fonts_section(font, characters)
    except Exception:
        logger.warning("Couldn't embed the font %s", font.path, exc_info=True)
        return font.family, ""


def build_overlay(chat_path: Path, style: OverlayStyle) -> OverlayResult:
    """Replaces the overlay in one step, so a player never reads half a file. Slow for a long
    stream (seconds), so call it off the event loop."""
    layout = Layout(style)
    placements = [
        placed for comment in _timed_comments(chat_path, style) if (placed := layout.place(comment))
    ]
    characters = {char for placed in placements for char in placed.comment.text}
    family, fonts = _fonts_or_nothing(characters)
    target = overlay_path(chat_path)
    temporary = target.with_name(target.name + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="\n") as ass_file:
        ass_file.write(header(style, family))
        ass_file.write(fonts)
        ass_file.write(EVENTS_HEADER)
        ass_file.writelines(dialogue(placed, style.font_size) for placed in placements)
    os.replace(temporary, target)
    return OverlayResult(comments=layout.stats.read, shown=layout.stats.placed)
