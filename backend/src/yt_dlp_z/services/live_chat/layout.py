"""Places comments into horizontal lanes so they never overlap."""

import unicodedata
from collections import deque
from dataclasses import dataclass, field

from yt_dlp_z.schemas.live_chat import OverlayStyle
from yt_dlp_z.services.live_chat.comments import Comment
from yt_dlp_z.services.live_chat.look import Look, look_of

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
LANE_SPACING = 1.15
# Width of a non-wide character, as a share of the font size. Slightly generous: an estimate
# that is too small makes a comment vanish before its tail has left the screen.
NARROW_CHAR_WIDTH = 0.62
FIXED_SECONDS = 4.0
# How late a comment may start when every lane is busy.
DELAY_TOLERANCE = 1.5
# Comments arriving together enter one after another, not as a vertical wall.
STAGGER_SECONDS = 0.2
BIG_LANES = 2


@dataclass
class _Occupant:
    start: float
    speed: float
    width: float
    fixed_until: float | None = None


Lanes = list[_Occupant | None]


@dataclass(frozen=True)
class Placement:
    """Where and when a comment shows, ready to be written as a subtitle event."""

    comment: Comment
    look: Look
    start: float
    end: float
    size: int
    y: int
    width: float
    fixed: bool


@dataclass
class Stats:
    read: int = 0
    placed: int = 0
    active: deque[float] = field(default_factory=deque)


def text_width(text: str, font_size: int) -> float:
    wide = sum(unicodedata.east_asian_width(char) in {"W", "F"} for char in text)
    return (wide + (len(text) - wide) * NARROW_CHAR_WIDTH) * font_size


def _earliest_start(previous: _Occupant | None, speed: float, fixed: bool) -> float:
    """When a new comment can enter this lane without touching the one ahead."""
    if previous is None:
        return 0.0
    previous_gone = previous.start + (SCREEN_WIDTH + previous.width) / previous.speed
    if fixed:
        return previous.fixed_until or previous_gone
    if previous.fixed_until:
        time_to_reach = (SCREEN_WIDTH - previous.width) / 2 / speed
        return previous.fixed_until - time_to_reach
    tail_on_screen = previous.start + previous.width / previous.speed
    # A longer comment moves faster, so its head must not reach the screen edge first.
    return max(tail_on_screen, previous_gone - SCREEN_WIDTH / speed)


class Layout:
    def __init__(self, style: OverlayStyle) -> None:
        self.style = style
        self.stats = Stats()
        self.lane_height = round(style.font_size * LANE_SPACING)
        count = int(SCREEN_HEIGHT * style.screen_area / self.lane_height)
        self.lanes: Lanes = [None] * max(count, 1)
        spare = int(SCREEN_HEIGHT * (1 - style.screen_area) / self.lane_height)
        self.bottom_lanes: Lanes = [None] * spare
        self.last_start = 0.0

    def _is_full(self, now: float) -> bool:
        active = self.stats.active
        while active and active[0] <= now:
            active.popleft()
        return len(active) >= self.style.max_on_screen

    def _best_lane(
        self, lanes: Lanes, arrival: float, speed: float, wanted: tuple[int, bool]
    ) -> tuple[int, float]:
        # Top lane first when several are free, so quiet chat stays near the top.
        span, fixed = wanted
        starts = []
        for index in range(max(len(lanes) - span + 1, 1)):
            group = lanes[index : index + span]
            earliest = max(_earliest_start(lane, speed, fixed) for lane in group)
            starts.append(max(arrival, earliest))
        best = min(starts)
        return starts.index(best), best

    def _start_time(self, arrival: float, free_at: float, paid: bool) -> float | None:
        """When to show it, or None when it would be too late. Paid comments always show,
        even if they overlap."""
        latest = arrival + DELAY_TOLERANCE
        start = max(free_at, self.last_start + STAGGER_SECONDS)
        if start <= latest:
            return start
        if paid:
            return latest if free_at <= latest else arrival
        return None

    def _lane_y(self, lanes: Lanes, lane: int, span: int, size: int) -> int:
        if lanes is self.bottom_lanes:
            return SCREEN_HEIGHT - (lane + span) * self.lane_height
        return lane * self.lane_height + round(size * 0.2)

    def place(self, comment: Comment) -> Placement | None:
        """Returns where it goes, or None when it was skipped because the screen is full."""
        self.stats.read += 1
        paid = comment.colour is not None
        if not paid and self._is_full(comment.seconds):
            return None
        look = look_of(comment, self.style)
        size = round(self.style.font_size * look.scale)
        width = text_width(comment.text, size) + size
        fixed = look.position != "scroll" and width < SCREEN_WIDTH
        speed = (SCREEN_WIDTH + width) / self.style.scroll_seconds
        at_bottom = fixed and look.position == "bottom" and bool(self.bottom_lanes)
        lanes = self.bottom_lanes if at_bottom else self.lanes
        span = BIG_LANES if look.scale > 1 else 1
        lane, free_at = self._best_lane(lanes, comment.seconds, speed, (span, fixed))
        start = self._start_time(comment.seconds, free_at, paid)
        if start is None:
            return None
        end = start + (FIXED_SECONDS if fixed else self.style.scroll_seconds)
        occupant = _Occupant(start, speed, width, end if fixed else None)
        lanes[lane : lane + span] = [occupant] * len(lanes[lane : lane + span])
        self.last_start = start
        self.stats.active.append(end)
        self.stats.placed += 1
        y = self._lane_y(lanes, lane, span, size)
        return Placement(comment, look, start, end, size, y, width, fixed)
