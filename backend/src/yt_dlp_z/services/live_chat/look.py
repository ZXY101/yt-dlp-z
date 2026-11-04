"""How each comment looks: colour, size and whether it scrolls or holds still."""

import zlib
from dataclasses import dataclass

from yt_dlp_z.schemas.live_chat import OverlayStyle
from yt_dlp_z.services.live_chat.comments import Comment

BIG_SCALE = 1.5
SMALL_SCALE = 0.7
# Colours as ASS writes them: blue, green, red.
PALETTE = ["FFFFFF", "6060FF", "A080FF", "00C0FF", "00FFFF", "00FF00", "FFFF00", "FFA040", "FF60C0"]
ROLE_COLOURS = {"owner": "00FFFF", "moderator": "FFA040", "member": "00FF00"}


@dataclass(frozen=True)
class Look:
    colour: str | None
    scale: float
    position: str  # scroll, top or bottom


def _colour(comment: Comment, style: OverlayStyle, roll: int) -> str | None:
    if comment.colour is not None or style.colour_mode == "white":
        return comment.colour
    if style.colour_mode == "random":
        return PALETTE[roll % len(PALETTE)]
    if style.colour_mode == "author":
        return PALETTE[zlib.crc32(comment.author.encode()) % len(PALETTE)]
    if style.colour_mode == "staff" and comment.role == "member":
        return None
    return ROLE_COLOURS.get(comment.role)


def _scale(style: OverlayStyle, roll: int) -> float:
    size_roll = (roll >> 8) % 1000 / 1000
    if size_roll < style.big_share:
        return BIG_SCALE
    if size_roll < style.big_share + style.small_share:
        return SMALL_SCALE
    return 1.0


def _position(comment: Comment, style: OverlayStyle, roll: int) -> str:
    # Paid comments always scroll, so they get the same attention as on the stream.
    if comment.colour is None and (roll >> 18) % 1000 / 1000 < style.fixed_share:
        return "top" if (roll >> 28) & 1 else "bottom"
    return "scroll"


def look_of(comment: Comment, style: OverlayStyle) -> Look:
    # A hash, not random numbers, so rebuilding the overlay gives the same result.
    roll = zlib.crc32(f"{comment.seconds}{comment.text}{comment.author}".encode())
    return Look(_colour(comment, style, roll), _scale(style, roll), _position(comment, style, roll))
