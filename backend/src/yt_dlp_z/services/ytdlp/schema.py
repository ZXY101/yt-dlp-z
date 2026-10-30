import asyncio
import json
import sys

from pydantic import ValidationError

from yt_dlp_z.schemas.options import OptionSchema, OptionSpec
from yt_dlp_z.services.ytdlp.communicate import communicate
from yt_dlp_z.services.ytdlp.errors import SchemaUnavailableError
from yt_dlp_z.services.ytdlp.policy import blocked_reason

DUMP_COMMAND = [sys.executable, "-m", "yt_dlp_z.services.ytdlp.schema_dump"]
TIMEOUT_SECONDS = 30

OptionIndex = dict[str, OptionSpec]


async def read_option_schema(*, allow_unsafe: bool) -> OptionSchema:
    process = await asyncio.create_subprocess_exec(
        *DUMP_COMMAND, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        async with asyncio.timeout(TIMEOUT_SECONDS):
            stdout, stderr = await communicate(process)
    except TimeoutError as error:
        raise SchemaUnavailableError("Reading yt-dlp's options timed out.") from error
    if process.returncode != 0:
        detail = stderr.decode(errors="replace").strip().splitlines()[-1:] or ["no output"]
        raise SchemaUnavailableError(f"Couldn't read yt-dlp's options: {detail[0]}")
    try:
        schema = OptionSchema.model_validate(json.loads(stdout))
    except (json.JSONDecodeError, ValidationError) as error:
        raise SchemaUnavailableError("yt-dlp's options were in an unexpected format.") from error
    for group in schema.groups:
        for option in group.options:
            option.blocked_reason = blocked_reason(option.flag, allow_unsafe=allow_unsafe)
    return schema


def build_index(schema: OptionSchema) -> OptionIndex:
    """Maps every long flag, alias and short flag to its option."""
    index: OptionIndex = {}
    for group in schema.groups:
        for option in group.options:
            for name in [option.flag, *option.aliases, *option.short]:
                index[name] = option
    return index


class OptionSchemaProvider:
    """Reads the schema once and caches it until yt-dlp changes."""

    def __init__(self, *, allow_unsafe: bool) -> None:
        self._allow_unsafe = allow_unsafe
        self._schema: OptionSchema | None = None
        self._index: OptionIndex = {}
        self._lock = asyncio.Lock()

    async def get(self) -> tuple[OptionSchema, OptionIndex]:
        async with self._lock:
            if self._schema is None:
                self._schema = await read_option_schema(allow_unsafe=self._allow_unsafe)
                self._index = build_index(self._schema)
            return self._schema, self._index

    def invalidate(self) -> None:
        self._schema = None
