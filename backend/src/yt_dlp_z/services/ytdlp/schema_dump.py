"""Prints yt-dlp's option schema as JSON.

Runs as its own process: it is the only module that imports yt_dlp, so the server
never loads yt-dlp itself and always describes the currently installed version."""

import json
import optparse
import sys
from typing import Any

REPEATABLE_CALLBACKS = {
    "_list_from_options_callback",
    "_dict_from_options_callback",
    "_set_from_options_callback",
}
SKIPPED_ACTIONS = {"help", "version"}


def option_kind(option: optparse.Option) -> str:
    if not option.takes_value():
        return "flag"
    if option.choices:
        return "choice"
    if option.type in {"int", "float"}:
        return "number"
    return "string"


def is_repeatable(option: optparse.Option) -> bool:
    if option.action == "append":
        return True
    return getattr(option.callback, "__name__", "") in REPEATABLE_CALLBACKS


def describe(option: optparse.Option, formatter: optparse.HelpFormatter) -> dict[str, Any] | None:
    if option.help == optparse.SUPPRESS_HELP or option.action in SKIPPED_ACTIONS:
        return None
    return {
        "flag": option._long_opts[0],
        "aliases": option._long_opts[1:],
        "short": option._short_opts,
        "kind": option_kind(option),
        "repeatable": is_repeatable(option),
        "metavar": option.metavar,
        "choices": list(option.choices) if option.choices else None,
        "help": formatter.expand_default(option),
    }


def main() -> None:
    import yt_dlp  # noqa: PLC0415  (kept out of module scope; see docstring)
    from yt_dlp.options import create_parser  # noqa: PLC0415

    parser = create_parser()
    parser.formatter.set_parser(parser)
    groups = []
    for group in parser.option_groups:
        options = [describe(option, parser.formatter) for option in group.option_list]
        visible = [option for option in options if option is not None]
        if visible:
            groups.append({"title": group.title, "options": visible})
    json.dump({"ytdlp_version": yt_dlp.version.__version__, "groups": groups}, sys.stdout)


if __name__ == "__main__":
    main()
