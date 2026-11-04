"""The chat JSON to .ass converter (services/live_chat)."""

import json
from collections.abc import Mapping
from pathlib import Path

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

from yt_dlp_z.schemas.live_chat import OverlayStyle
from yt_dlp_z.services.live_chat.ass import ass_time, dialogue
from yt_dlp_z.services.live_chat.comments import MAX_CHARS, Comment, clean_text, read_comments
from yt_dlp_z.services.live_chat.fonts import FONT_ENV, ass_encode, find_font
from yt_dlp_z.services.live_chat.layout import SCREEN_WIDTH, Layout, Placement, text_width
from yt_dlp_z.services.live_chat.look import BIG_SCALE, PALETTE, ROLE_COLOURS, look_of
from yt_dlp_z.services.live_chat.overlay import OverlayResult, build_overlay, overlay_path
from yt_dlp_z.services.live_chat.split import SavedPart, split_capture


def replay(offset_ms: int, item: Mapping[str, object]) -> str:
    actions = [{"addChatItemAction": {"item": item}}]
    action = {"actions": actions, "videoOffsetTimeMsec": str(offset_ms)}
    return json.dumps({"replayChatItemAction": action})


def text_item(text: str, **fields: object) -> dict[str, object]:
    renderer = {"message": {"runs": [{"text": text}]}, **fields}
    return {"liveChatTextMessageRenderer": renderer}


def chat_file(tmp_path: Path, lines: list[str]) -> Path:
    path = tmp_path / "Title [id].live_chat.json"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def comments_at(*seconds: float) -> list[Comment]:
    return [Comment(second, f"comment {index}") for index, second in enumerate(seconds)]


def test_chat_cannot_inject_ass_commands() -> None:
    cleaned = clean_text(r"{\pos(0,0)}hi")
    assert not set("{}\\") & set(cleaned)
    assert cleaned.endswith("hi")


def test_clean_text_keeps_symbols_and_drops_what_libass_cannot_draw() -> None:
    assert clean_text("★ ♪ 草😀\u200b") == "★ ♪ 草"


def test_clean_text_shortens_long_comments() -> None:
    cleaned = clean_text("x" * 200)
    assert len(cleaned) == MAX_CHARS
    assert cleaned.endswith("…")


def test_reads_replay_and_live_offsets(tmp_path: Path) -> None:
    live_action = {"actions": [{"addChatItemAction": {"item": text_item("live")}}]}
    live = json.dumps({"replayChatItemAction": live_action, "videoOffsetTimeMsec": 2500})
    path = chat_file(tmp_path, [replay(1500, text_item("replayed")), live])
    found = list(read_comments(path, show_paid=True))
    assert [(comment.seconds, comment.text) for comment in found] == [
        (1.5, "replayed"),
        (2.5, "live"),
    ]


def test_skips_broken_lines_and_keeps_the_rest(tmp_path: Path) -> None:
    bad_offset = {"replayChatItemAction": {"videoOffsetTimeMsec": "soon", "actions": []}}
    lines = ["not json", "[1, 2]", json.dumps(bad_offset), replay(1000, text_item("kept"))]
    found = list(read_comments(chat_file(tmp_path, lines), show_paid=True))
    assert [comment.text for comment in found] == ["kept"]


def test_super_chats_and_stickers_take_their_colour(tmp_path: Path) -> None:
    paid = {
        "liveChatPaidMessageRenderer": {
            "purchaseAmountText": {"simpleText": "¥500"},
            "message": {"runs": [{"text": "thanks"}]},
            "bodyBackgroundColor": 0xFF102030,
        }
    }
    sticker = {
        "liveChatPaidStickerRenderer": {
            "purchaseAmountText": {"simpleText": "$5.00"},
            "backgroundColor": 0xFF405060,
        }
    }
    path = chat_file(tmp_path, [replay(1000, paid), replay(2000, sticker)])
    found = list(read_comments(path, show_paid=True))
    assert [(comment.text, comment.colour) for comment in found] == [
        ("¥500 thanks", "302010"),
        ("$5.00", "605040"),
    ]
    assert list(read_comments(path, show_paid=False)) == []


@pytest.mark.parametrize(
    ("badge", "role"),
    [
        ({"customThumbnail": {}}, "member"),
        ({"icon": {"iconType": "OWNER"}}, "owner"),
        ({"icon": {"iconType": "MODERATOR"}}, "moderator"),
        ({"icon": {"iconType": "VERIFIED"}}, ""),
    ],
)
def test_reads_the_viewers_role(tmp_path: Path, badge: dict[str, object], role: str) -> None:
    badges = [{"liveChatAuthorBadgeRenderer": badge}]
    path = chat_file(tmp_path, [replay(0, text_item("hi", authorBadges=badges))])
    assert next(read_comments(path, show_paid=True)).role == role


def test_look_is_the_same_on_every_build() -> None:
    style = OverlayStyle(colour_mode="random", big_share=0.3, small_share=0.3, fixed_share=0.3)
    comment = Comment(3.0, "same", author="UCa")
    assert look_of(comment, style) == look_of(comment, style)


def test_colour_modes() -> None:
    comment = Comment(1.0, "hi", author="UCa", role="owner")
    assert look_of(comment, OverlayStyle()).colour is None
    assert look_of(comment, OverlayStyle(colour_mode="role")).colour == ROLE_COLOURS["owner"]
    assert look_of(comment, OverlayStyle(colour_mode="random")).colour in PALETTE
    one_viewer = [
        look_of(Comment(float(n), f"text {n}", author="UCa"), OverlayStyle(colour_mode="author"))
        for n in range(5)
    ]
    assert len({look.colour for look in one_viewer}) == 1


@pytest.mark.parametrize(
    ("role", "staff_colour", "role_colour"),
    [
        ("owner", ROLE_COLOURS["owner"], ROLE_COLOURS["owner"]),
        ("moderator", ROLE_COLOURS["moderator"], ROLE_COLOURS["moderator"]),
        ("member", None, ROLE_COLOURS["member"]),
        ("", None, None),
    ],
)
def test_staff_colours_leave_members_white(
    role: str, staff_colour: str | None, role_colour: str | None
) -> None:
    comment = Comment(1.0, "hi", role=role)
    assert look_of(comment, OverlayStyle(colour_mode="staff")).colour == staff_colour
    assert look_of(comment, OverlayStyle(colour_mode="role")).colour == role_colour


def test_paid_comments_keep_their_colour_and_keep_scrolling() -> None:
    look = look_of(Comment(1.0, "¥500", colour="102030"), OverlayStyle(fixed_share=1.0))
    assert look.colour == "102030"
    assert look.position == "scroll"


def test_shares_change_size_and_position() -> None:
    comment = Comment(1.0, "hi")
    assert look_of(comment, OverlayStyle(big_share=1.0)).scale == BIG_SCALE
    assert look_of(comment, OverlayStyle(small_share=1.0)).scale < 1
    assert look_of(comment, OverlayStyle(fixed_share=1.0)).position in {"top", "bottom"}


def overlaps(first: Placement, second: Placement) -> bool:
    """Whether two scrolling comments in one lane touch at any moment both are on screen."""

    def left_edge(placed: Placement, now: float) -> float:
        travelled = (now - placed.start) / (placed.end - placed.start)
        return SCREEN_WIDTH - travelled * (SCREEN_WIDTH + placed.width)

    both_from, both_to = max(first.start, second.start), min(first.end, second.end)
    moments = [both_from + (both_to - both_from) * step / 20 for step in range(21)]
    ahead, behind = sorted((first, second), key=lambda placed: placed.start)
    return any(left_edge(ahead, now) + ahead.width > left_edge(behind, now) for now in moments)


def test_comments_in_one_lane_never_touch() -> None:
    layout = Layout(OverlayStyle(max_on_screen=200))
    placed = [
        layout.place(Comment(index * 0.3, "長いコメント" * (1 + index % 4))) for index in range(100)
    ]
    shown = [item for item in placed if item]
    for first in shown:
        for second in shown:
            same_lane = first.y == second.y and first is not second
            if same_lane and first.start < second.start < first.end:
                assert not overlaps(first, second)


def test_the_limit_skips_comments_but_never_paid_ones() -> None:
    layout = Layout(OverlayStyle(max_on_screen=2))
    results = [layout.place(comment) for comment in comments_at(0, 0.5, 1)]
    assert [bool(result) for result in results] == [True, True, False]
    assert layout.place(Comment(1.1, "¥500", colour="102030"))
    assert layout.stats.placed == 3


def test_comments_arriving_together_enter_one_after_another() -> None:
    layout = Layout(OverlayStyle(max_on_screen=200))
    placed = [layout.place(comment) for comment in comments_at(*[5.0] * 20)]
    starts = [item.start for item in placed if item]
    assert len(set(starts)) == len(starts)
    assert len(starts) < 20


def test_paid_comments_still_show_when_every_lane_is_full() -> None:
    layout = Layout(OverlayStyle(max_on_screen=200, screen_area=0.1))
    for comment in comments_at(*[1.0] * 3):
        layout.place(comment)
    assert layout.place(Comment(1.0, "¥500 " + "very long " * 5, colour="102030"))


def test_fixed_comments_hold_still_at_the_top_and_bottom() -> None:
    layout = Layout(OverlayStyle(fixed_share=1.0))
    placed = [layout.place(Comment(float(n), f"held {n}")) for n in range(12)]
    shown = [item for item in placed if item]
    assert all(item.fixed for item in shown)
    assert any(r"\an8\pos" in dialogue(item, 48) for item in shown)
    assert len({item.y for item in shown}) > 1


def test_big_comments_are_written_with_their_size() -> None:
    placed = Layout(OverlayStyle(big_share=1.0)).place(Comment(1.0, "big"))
    assert placed is not None
    assert r"\fs72" in dialogue(placed, 48)


def test_wide_characters_count_as_wider() -> None:
    assert text_width("あ", 48) > text_width("a", 48)


def test_ass_time() -> None:
    assert ass_time(3661.25) == "1:01:01.25"
    assert ass_time(0) == "0:00:00.00"


def test_ass_font_encoding() -> None:
    # The spec's scheme: 3 bytes to 4 characters, each 6 bits offset by 33.
    assert ass_encode(b"\x00\x00\x00") == "!!!!"
    assert ass_encode(b"\xff") == "`Q"
    assert ass_encode(b"\xff\xff") == "``]"
    long_lines = ass_encode(bytes(300)).split("\n")
    assert max(len(line) for line in long_lines) == 80


def small_font(path: Path) -> Path:
    builder = FontBuilder(1000, isTTF=True)
    glyphs = [".notdef", "space", "a"]
    builder.setupGlyphOrder(glyphs)
    builder.setupCharacterMap({32: "space", 97: "a"})
    empty = TTGlyphPen(None).glyph()
    builder.setupGlyf(dict.fromkeys(glyphs, empty))
    builder.setupHorizontalMetrics(dict.fromkeys(glyphs, (500, 0)))
    builder.setupHorizontalHeader(ascent=800, descent=-200)
    builder.setupNameTable({"familyName": "Test Chat Font", "styleName": "Bold"})
    builder.setupOS2()
    builder.setupPost()
    builder.save(path)
    return path


def overlay_of(tmp_path: Path, style: OverlayStyle | None = None) -> str:
    path = chat_file(tmp_path, [replay(1000, text_item("aaa")), replay(9000, text_item("a a"))])
    build_overlay(path, style or OverlayStyle())
    return overlay_path(path).read_text(encoding="utf-8-sig")


def test_overlay_is_named_like_the_video(tmp_path: Path) -> None:
    chat = tmp_path / "A.B [id].live_chat.json"
    assert overlay_path(chat) == tmp_path / "A.B [id].ass"


def test_overlay_embeds_the_font(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FONT_ENV, str(small_font(tmp_path / "font.ttf")))
    text = overlay_of(tmp_path)
    assert "Style: Chat,Test Chat Font,48," in text
    assert text.index("[Fonts]\nfontname: chat-font.otf\n") < text.index("[Events]")
    assert "aaa" in text


def test_overlay_reports_how_many_comments_it_shows(tmp_path: Path) -> None:
    lines = [replay(1000, text_item("one")), replay(2000, text_item("two"))]
    assert build_overlay(chat_file(tmp_path, lines), OverlayStyle(max_on_screen=1)) == (
        OverlayResult(comments=2, shown=1)
    )


def test_overlay_without_a_font_still_works(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(FONT_ENV, str(tmp_path / "missing.otf"))
    assert find_font() is None
    text = overlay_of(tmp_path)
    assert "[Fonts]" not in text
    assert "Dialogue: 0,0:00:01.00," in text


def test_a_broken_font_file_does_not_lose_the_overlay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broken = tmp_path / "broken.otf"
    broken.write_bytes(b"not a font")
    monkeypatch.setenv(FONT_ENV, str(broken))
    assert "[Fonts]" not in overlay_of(tmp_path)


def test_offset_moves_comments_and_drops_those_before_the_video(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(FONT_ENV, str(tmp_path / "missing.otf"))
    text = overlay_of(tmp_path, OverlayStyle(offset_seconds=-5))
    assert text.count("Dialogue:") == 1
    assert "0:00:04." in text


def test_rebuilding_gives_the_same_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(FONT_ENV, str(tmp_path / "missing.otf"))
    style = OverlayStyle(colour_mode="random", big_share=0.2, fixed_share=0.2)
    assert overlay_of(tmp_path, style) == overlay_of(tmp_path, style)


def live_line(moment: float, text: str, item_id: str | None = None) -> str:
    renderer = {
        "id": item_id or text,
        "timestampUsec": str(int(moment * 1_000_000)),
        "message": {"runs": [{"text": text}]},
    }
    actions = [{"addChatItemAction": {"item": {"liveChatTextMessageRenderer": renderer}}}]
    return json.dumps(
        {"replayChatItemAction": {"actions": actions}, "videoOffsetTimeMsec": "123", "isLive": True}
    )


def capture_files_on_disk(folder: Path, *runs: list[str]) -> None:
    folder.mkdir(exist_ok=True)
    for number, lines in enumerate(runs, start=1):
        name = f"chat-{number}.live_chat.json.part"
        (folder / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


def shown(chat_path: Path) -> list[tuple[float, str]]:
    return [(item.seconds, item.text) for item in read_comments(chat_path, show_paid=True)]


def test_each_part_gets_the_comments_of_its_own_time(tmp_path: Path) -> None:
    capture_files_on_disk(
        tmp_path / "capture",
        [live_line(1005, "first part"), live_line(1100, "second part"), live_line(1103, "later")],
    )
    parts = [
        SavedPart(tmp_path / "Stream (part 1).mp4", 1000),
        SavedPart(tmp_path / "Stream (part 2).mp4", 1098),
    ]
    assert len(split_capture(tmp_path / "capture", parts)) == 2
    assert shown(tmp_path / "Stream (part 1).live_chat.json") == [(5.0, "first part")]
    assert shown(tmp_path / "Stream (part 2).live_chat.json") == [
        (2.0, "second part"),
        (5.0, "later"),
    ]


def test_waiting_room_chat_is_kept_but_not_shown(tmp_path: Path) -> None:
    capture_files_on_disk(
        tmp_path / "capture", [live_line(990, "early"), live_line(1001, "on time")]
    )
    path = split_capture(tmp_path / "capture", [SavedPart(tmp_path / "S.mp4", 1000)])[0]
    assert "early" in path.read_text(encoding="utf-8")
    style = OverlayStyle()
    build_overlay(path, style)
    overlay = overlay_path(path).read_text(encoding="utf-8-sig")
    assert "on time" in overlay
    assert "early" not in overlay


def test_a_capture_that_restarted_has_each_comment_once(tmp_path: Path) -> None:
    capture_files_on_disk(
        tmp_path / "capture",
        [live_line(1001, "one"), live_line(1002, "two")],
        [live_line(1002, "two"), live_line(1003, "three")],
    )
    path = split_capture(tmp_path / "capture", [SavedPart(tmp_path / "S.mp4", 1000)])[0]
    assert [text for _, text in shown(path)] == ["one", "two", "three"]


def test_files_yt_dlp_keeps_while_running_are_not_read(tmp_path: Path) -> None:
    capture_files_on_disk(tmp_path / "capture", [live_line(1001, "kept")])
    leftovers = {
        "chat-1.live_chat.json.part-Frag4": live_line(1002, "fragment"),
        "chat-1.live_chat.json.ytdl": live_line(1003, "state"),
    }
    for name, line in leftovers.items():
        (tmp_path / "capture" / name).write_text(line + "\n", encoding="utf-8")
    path = split_capture(tmp_path / "capture", [SavedPart(tmp_path / "S.mp4", 1000)])[0]
    assert [text for _, text in shown(path)] == ["kept"]


def test_a_half_written_last_line_is_skipped(tmp_path: Path) -> None:
    capture_files_on_disk(
        tmp_path / "capture", [live_line(1001, "whole"), live_line(1002, "cut")[:40]]
    )
    path = split_capture(tmp_path / "capture", [SavedPart(tmp_path / "S.mp4", 1000)])[0]
    assert [text for _, text in shown(path)] == ["whole"]


def test_nothing_to_split_writes_nothing(tmp_path: Path) -> None:
    capture_files_on_disk(tmp_path / "capture", [live_line(1001, "one")])
    assert split_capture(tmp_path / "capture", []) == []
    (tmp_path / "empty").mkdir()
    assert split_capture(tmp_path / "empty", [SavedPart(tmp_path / "S.mp4", 1000)]) == []
    assert not (tmp_path / "S.live_chat.json").exists()
