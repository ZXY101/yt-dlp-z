"""Turns user-chosen options and free-form extra arguments into a safe yt-dlp argv."""

import shlex
from collections.abc import Mapping

from yt_dlp_z.schemas.options import OptionSpec
from yt_dlp_z.services.ytdlp.errors import ArgumentError
from yt_dlp_z.services.ytdlp.policy import blocked_reason, check_output_template
from yt_dlp_z.services.ytdlp.schema import OptionIndex

OptionValue = bool | int | float | str | list[str]


def build_user_args(
    index: OptionIndex,
    options: Mapping[str, OptionValue],
    extra_args: str,
    *,
    allow_unsafe: bool,
) -> list[str]:
    args: list[str] = []
    for flag, value in options.items():
        spec = _lookup(index, flag, allow_unsafe=allow_unsafe)
        args += _option_args(spec, value)
    return args + _extra_args(index, extra_args, allow_unsafe=allow_unsafe)


def _lookup(index: OptionIndex, name: str, *, allow_unsafe: bool) -> OptionSpec:
    spec = index.get(name)
    if spec is None:
        raise ArgumentError(f"Unknown yt-dlp option: {name}")
    reason = blocked_reason(spec.flag, allow_unsafe=allow_unsafe)
    if reason:
        raise ArgumentError(f"{spec.flag} isn't allowed. {reason}")
    return spec


def _option_args(spec: OptionSpec, value: OptionValue) -> list[str]:
    if spec.kind == "flag":
        if isinstance(value, bool):
            return [spec.flag] if value else []
        raise ArgumentError(f"{spec.flag} is an on/off option.")
    if isinstance(value, list) and not spec.repeatable:
        raise ArgumentError(f"{spec.flag} takes a single value.")
    values = value if isinstance(value, list) else [value]
    args: list[str] = []
    for item in values:
        args += [spec.flag, _checked_value(spec, item)]
    return args


def _checked_value(spec: OptionSpec, value: object) -> str:
    if isinstance(value, bool) or not isinstance(value, str | int | float):
        raise ArgumentError(f"{spec.flag} needs a value.")
    text = str(value)
    if spec.kind == "number":
        try:
            float(text)
        except ValueError:
            raise ArgumentError(f"{spec.flag} needs a number.") from None
    if spec.choices and text not in spec.choices:
        raise ArgumentError(f"{spec.flag} must be one of: {', '.join(spec.choices)}.")
    if spec.flag == "--output":
        check_output_template(text)
    return text


def _split_token(token: str) -> tuple[str, str | None]:
    if token.startswith("--"):
        name, separator, value = token.partition("=")
        return name, value if separator else None
    return token[:2], token[2:] or None


def _extra_args(index: OptionIndex, text: str, *, allow_unsafe: bool) -> list[str]:
    try:
        tokens = shlex.split(text)
    except ValueError as error:
        raise ArgumentError(f"Extra arguments: {error}.") from None
    args: list[str] = []
    position = 0
    while position < len(tokens):
        option_args, position = _consume_option(tokens, position, index, allow_unsafe)
        args += option_args
    return args


def _consume_option(
    tokens: list[str], position: int, index: OptionIndex, allow_unsafe: bool
) -> tuple[list[str], int]:
    token = tokens[position]
    if not token.startswith("-") or token in {"-", "--"}:
        raise ArgumentError(f"Unexpected {token!r} in extra arguments. Put URLs in the URL field.")
    name, inline_value = _split_token(token)
    spec = _lookup(index, name, allow_unsafe=allow_unsafe)
    if spec.kind == "flag":
        if inline_value is not None:
            raise ArgumentError(f"Write short options separately: {token!r}.")
        return [spec.flag], position + 1
    if inline_value is not None:
        return [spec.flag, _checked_value(spec, inline_value)], position + 1
    if position + 1 >= len(tokens):
        raise ArgumentError(f"{spec.flag} needs a value.")
    return [spec.flag, _checked_value(spec, tokens[position + 1])], position + 2
