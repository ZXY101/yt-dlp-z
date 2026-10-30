import sys

import pytest

from yt_dlp_z.schemas.options import OptionSchema
from yt_dlp_z.services.ytdlp import schema as schema_module
from yt_dlp_z.services.ytdlp.errors import SchemaUnavailableError
from yt_dlp_z.services.ytdlp.schema import OptionSchemaProvider, read_option_schema


async def test_reads_the_installed_yt_dlp() -> None:
    schema = await read_option_schema(allow_unsafe=False)
    options = {option.flag: option for group in schema.groups for option in group.options}
    assert schema.ytdlp_version
    assert options["--format"].kind == "string"
    assert options["--extract-audio"].kind == "flag"
    assert options["--format-sort"].repeatable is True
    assert options["--exec"].blocked_reason is not None
    assert options["--format"].blocked_reason is None
    assert "-f" in options["--format"].short


async def test_allow_unsafe_unblocks_unsafe_options() -> None:
    schema = await read_option_schema(allow_unsafe=True)
    options = {option.flag: option for group in schema.groups for option in group.options}
    assert options["--exec"].blocked_reason is None
    assert options["--paths"].blocked_reason is not None


@pytest.mark.parametrize(
    ("script", "message"),
    [
        ("import sys; sys.exit('boom')", "Couldn't read yt-dlp's options: boom"),
        ("print('not json')", "unexpected format"),
        ("print('{\"groups\": 1}')", "unexpected format"),
    ],
)
async def test_failures_raise_schema_unavailable(
    monkeypatch: pytest.MonkeyPatch, script: str, message: str
) -> None:
    monkeypatch.setattr(schema_module, "DUMP_COMMAND", [sys.executable, "-c", script])
    with pytest.raises(SchemaUnavailableError, match=message):
        await read_option_schema(allow_unsafe=False)


async def test_timeout_raises_schema_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        schema_module, "DUMP_COMMAND", [sys.executable, "-c", "import time; time.sleep(5)"]
    )
    monkeypatch.setattr(schema_module, "TIMEOUT_SECONDS", 0.2)
    with pytest.raises(SchemaUnavailableError, match="timed out"):
        await read_option_schema(allow_unsafe=False)


async def test_provider_caches_until_invalidated(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[bool] = []
    real_read = schema_module.read_option_schema

    async def counting_read(*, allow_unsafe: bool) -> OptionSchema:
        calls.append(allow_unsafe)
        return await real_read(allow_unsafe=allow_unsafe)

    monkeypatch.setattr(schema_module, "read_option_schema", counting_read)
    provider = OptionSchemaProvider(allow_unsafe=False)
    _, index = await provider.get()
    await provider.get()
    assert len(calls) == 1
    assert index["-f"].flag == "--format"
    provider.invalidate()
    await provider.get()
    assert len(calls) == 2
