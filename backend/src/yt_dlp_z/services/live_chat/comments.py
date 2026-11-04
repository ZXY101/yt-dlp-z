"""Reads the comments out of yt-dlp's .live_chat.json, one JSON object per line."""

import json
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_CHARS = 60
FIRST_EMOJI = 0x1F000
VARIATION_SELECTOR = "\ufe0f"
DEFAULT_PAID_ARGB = 0xFFFFD54F
ROLES = {"owner", "moderator"}
# Chat is untrusted: braces and backslashes would be ASS commands.
SAFE_CHARS = str.maketrans({"{": "\uff5b", "}": "\uff5d", "\\": "\uff3c", "\n": " ", "\r": " "})


@dataclass(frozen=True)
class Comment:
    seconds: float
    text: str
    # ASS blue-green-red hex. Set on Super Chats and Super Stickers only.
    colour: str | None = None
    author: str = ""
    role: str = ""


def _can_render(char: str) -> bool:
    """libass draws no colour emoji, so they'd show as boxes. Symbols like ★ and ♪ are fine."""
    is_emoji = ord(char) >= FIRST_EMOJI or char == VARIATION_SELECTOR
    return not is_emoji and unicodedata.category(char) not in {"Cc", "Cf"}


def clean_text(text: str) -> str:
    kept = (char for char in text.translate(SAFE_CHARS) if _can_render(char))
    cleaned = " ".join("".join(kept).split())
    return cleaned[: MAX_CHARS - 1] + "…" if len(cleaned) > MAX_CHARS else cleaned


def _message_text(renderer: dict[str, Any]) -> str:
    # Emoji runs have no "text": custom ones are images, which ASS can't show.
    runs = renderer.get("message", {}).get("runs", [])
    return clean_text("".join(run.get("text", "") for run in runs))


def _paid_colour(argb: object) -> str:
    value = argb if isinstance(argb, int) else DEFAULT_PAID_ARGB
    red, green, blue = (value >> 16) & 255, (value >> 8) & 255, value & 255
    return f"{blue:02X}{green:02X}{red:02X}"


def _role(renderer: dict[str, Any]) -> str:
    for badge in renderer.get("authorBadges", []):
        badge_renderer = badge.get("liveChatAuthorBadgeRenderer", {})
        if "customThumbnail" in badge_renderer:
            return "member"
        icon = badge_renderer.get("icon", {}).get("iconType", "").lower()
        if icon in ROLES:
            return str(icon)
    return ""


def _paid_comment(renderer: dict[str, Any], seconds: float, colour_key: str) -> Comment | None:
    amount = renderer.get("purchaseAmountText", {}).get("simpleText", "")
    text = clean_text(f"{amount} {_message_text(renderer)}")
    return Comment(seconds, text, _paid_colour(renderer.get(colour_key))) if text else None


def _comment_from_item(item: dict[str, Any], seconds: float, show_paid: bool) -> Comment | None:
    renderer = item.get("liveChatTextMessageRenderer")
    if renderer:
        text = _message_text(renderer)
        author = renderer.get("authorExternalChannelId", "")
        return Comment(seconds, text, None, author, _role(renderer)) if text else None
    if not show_paid:
        return None
    paid = item.get("liveChatPaidMessageRenderer")
    if paid:
        return _paid_comment(paid, seconds, "bodyBackgroundColor")
    sticker = item.get("liveChatPaidStickerRenderer")
    if sticker:
        return _paid_comment(sticker, seconds, "backgroundColor")
    return None


def _entry_comments(entry: dict[str, Any], show_paid: bool) -> Iterator[Comment]:
    replay = entry["replayChatItemAction"]
    # A replay keeps the offset inside the action; a live capture beside it.
    offset = replay.get("videoOffsetTimeMsec", entry.get("videoOffsetTimeMsec", 0))
    seconds = int(offset) / 1000
    for action in replay.get("actions", []):
        item = action.get("addChatItemAction", {}).get("item", {})
        comment = _comment_from_item(item, seconds, show_paid)
        if comment:
            yield comment


def read_comments(path: Path, show_paid: bool) -> Iterator[Comment]:
    """Comments in file order. A line that isn't what's expected is skipped: a capture that
    was cut off, or a change on YouTube's side, shouldn't lose the rest of the chat."""
    with path.open(encoding="utf-8") as chat_file:
        for line in chat_file:
            try:
                yield from _entry_comments(json.loads(line), show_paid)
            except (ValueError, TypeError, KeyError, AttributeError):
                continue
