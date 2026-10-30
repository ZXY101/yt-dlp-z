from typing import Literal

from pydantic import BaseModel


class OptionSpec(BaseModel):
    flag: str
    aliases: list[str]
    short: list[str]
    kind: Literal["flag", "string", "number", "choice"]
    repeatable: bool
    metavar: str | None
    choices: list[str] | None
    help: str
    # Set when yt-dlp-z refuses this option, with the reason to show the user.
    blocked_reason: str | None = None


class OptionGroup(BaseModel):
    title: str
    options: list[OptionSpec]


class OptionSchema(BaseModel):
    ytdlp_version: str
    groups: list[OptionGroup]
