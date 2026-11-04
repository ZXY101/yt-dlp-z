"""Embeds a font in the overlay, so Japanese text shows on every player.

Jellyfin's web and mobile players render subtitles without any system fonts, and show boxes
for Japanese. A .ass file can carry its own font, so only the characters a chat actually
uses are subset out of a CJK font and written into it, about 200 KB for a busy stream.
"""

import io
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTCollection, TTFont

logger = logging.getLogger(__name__)

FONT_ENV = "YTDLPZ_CHAT_FONT"
FAMILY = "Noto Sans CJK JP"
FONT_FILE_NAME = "chat-font.otf"
# The Docker image has the first; the others are where Linux systems put the same font.
FONT_LOCATIONS = (
    "/app/fonts/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Bold.ttc",
)
LINE_CHARS = 80
ASCII_PRINTABLE = {chr(code) for code in range(32, 127)}
FAMILY_NAME_ID = 1
BITS_PER_CHAR = 6
FIRST_CHAR = 33


@dataclass(frozen=True)
class ChatFont:
    path: Path
    family: str


def _family(font: TTFont) -> str:
    return str(font["name"].getDebugName(FAMILY_NAME_ID))


def _open_font(path: Path) -> TTFont:
    """One font from the file. In a collection, the Japanese one when it has one."""
    if path.suffix.lower() != ".ttc":
        return TTFont(path)
    fonts = TTCollection(path).fonts
    return next((font for font in fonts if _family(font) == FAMILY), fonts[0])


def find_font() -> ChatFont | None:
    """None: the overlay still works, using whatever fonts the player has."""
    configured = os.environ.get(FONT_ENV)
    for location in [configured] if configured else FONT_LOCATIONS:
        path = Path(location)
        if not path.is_file():
            continue
        try:
            return ChatFont(path, _family(_open_font(path)))
        except Exception:
            # Whatever fontTools trips over in a bad file, the overlay is still useful.
            logger.warning("Couldn't read the font %s", path, exc_info=True)
    return None


def ass_encode(data: bytes) -> str:
    """The ASS [Fonts] encoding: each 3 bytes become 4 characters, offset by 33."""
    encoded = []
    for start in range(0, len(data), 3):
        chunk = data[start : start + 3]
        bits = int.from_bytes(chunk.ljust(3, b"\0"), "big")
        sextets = [(bits >> shift) & 63 for shift in (18, 12, BITS_PER_CHAR, 0)]
        encoded.append("".join(chr(sextet + FIRST_CHAR) for sextet in sextets[: len(chunk) + 1]))
    text = "".join(encoded)
    return "\n".join(text[i : i + LINE_CHARS] for i in range(0, len(text), LINE_CHARS))


def _subset(font: TTFont, characters: set[str]) -> bytes:
    options = Options()
    options.layout_features = []  # Chat is plain text; shaping tables only add size.
    options.hinting = False
    options.name_IDs = ["*"]  # libass finds the font by its family name.
    subsetter = Subsetter(options)
    subsetter.populate(unicodes=[ord(char) for char in characters | ASCII_PRINTABLE])
    subsetter.subset(font)
    output = io.BytesIO()
    font.save(output)
    return output.getvalue()


def fonts_section(font: ChatFont, characters: set[str]) -> str:
    data = _subset(_open_font(font.path), characters)
    return f"[Fonts]\nfontname: {FONT_FILE_NAME}\n{ass_encode(data)}\n\n"
