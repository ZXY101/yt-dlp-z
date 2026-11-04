from typing import Annotated, Literal

from pydantic import BaseModel, Field

# "save": keep the chat's JSON. "overlay": also build a subtitle overlay from it.
LiveChatMode = Literal["off", "save", "overlay"]
# "author": each viewer keeps one colour. "staff": the owner and moderators stand out. "role":
# members too.
ColourMode = Literal["white", "random", "author", "staff", "role"]
Share = Annotated[float, Field(ge=0, le=1)]
# Where a job's live chat ended up. "stopped": the user cancelled while it was being fetched.
ChatStatus = Literal["capturing", "fetching", "saved", "overlay", "none", "failed", "stopped"]


class OverlayStyle(BaseModel):
    """How the scrolling chat overlay looks. Defaults were chosen on a real, busy stream."""

    scroll_seconds: float = Field(default=7.0, ge=2, le=30)
    font_size: int = Field(default=48, ge=16, le=120)
    opacity: float = Field(default=0.85, ge=0.1, le=1)
    # Share of the screen height comments may use, from the top.
    screen_area: float = Field(default=0.75, ge=0.1, le=1)
    # Most comments on screen at once; more than this are skipped, except Super Chats.
    max_on_screen: int = Field(default=30, ge=1, le=200)
    # Added to every comment's time; negative shows chat earlier.
    offset_seconds: float = Field(default=0.0, ge=-600, le=600)
    show_paid: bool = True
    colour_mode: ColourMode = "white"
    big_share: Share = 0.0
    small_share: Share = 0.0
    # Share of comments held still at the top or bottom instead of scrolling.
    fixed_share: Share = 0.0


class LiveChatSettings(OverlayStyle):
    """Part of a preset or download. Every job keeps the values it started with."""

    mode: LiveChatMode = "off"
