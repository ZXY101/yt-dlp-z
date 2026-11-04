"""Writes placed comments as Advanced SubStation Alpha text."""

from yt_dlp_z.schemas.live_chat import OverlayStyle
from yt_dlp_z.services.live_chat.layout import SCREEN_HEIGHT, SCREEN_WIDTH, Placement

HEADER = """[Script Info]
Title: Live chat
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, \
Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, \
Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chat,{font},{size},&H{alpha}FFFFFF,&H00FFFFFF,&H{alpha}000000,&H00000000,\
-1,0,0,0,100,100,0,0,1,{outline},0,7,0,0,0,1

"""
EVENTS_HEADER = """[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
OUTLINE_DIVISOR = 16


def ass_time(seconds: float) -> str:
    centis = round(seconds * 100)
    hours, centis = divmod(centis, 360000)
    minutes, centis = divmod(centis, 6000)
    whole, centis = divmod(centis, 100)
    return f"{hours}:{minutes:02}:{whole:02}.{centis:02}"


def header(style: OverlayStyle, font: str) -> str:
    return HEADER.format(
        width=SCREEN_WIDTH,
        height=SCREEN_HEIGHT,
        font=font,
        size=style.font_size,
        alpha=f"{round((1 - style.opacity) * 255):02X}",
        outline=max(1, round(style.font_size / OUTLINE_DIVISOR)),
    )


def _position_tag(placement: Placement) -> str:
    y = placement.y
    if placement.fixed:
        return rf"\an8\pos({SCREEN_WIDTH // 2},{y})"
    return rf"\move({SCREEN_WIDTH},{y},{-round(placement.width)},{y})"


def dialogue(placement: Placement, font_size: int) -> str:
    look = placement.look
    tags = [_position_tag(placement)]
    if look.colour:
        tags.append(rf"\c&H{look.colour}&")
    if placement.size != font_size:
        tags.append(rf"\fs{placement.size}")
    timing = f"{ass_time(placement.start)},{ass_time(placement.end)}"
    return f"Dialogue: 0,{timing},Chat,,0,0,0,,{{{''.join(tags)}}}{placement.comment.text}\n"
