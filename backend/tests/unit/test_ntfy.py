import pytest

from tests.ntfy_server import fake_ntfy
from yt_dlp_z.services.notify.ntfy import MESSAGE_LIMIT, Message, NotifyError, send_ntfy
from yt_dlp_z.services.notify.store import NtfyConfig


async def test_sends_json_with_the_token() -> None:
    with fake_ntfy() as ntfy:
        config = NtfyConfig(server=ntfy.url + "/", topic="dl", token="tk_abc")  # noqa: S106
        await send_ntfy(config, Message("録画開始", "x" * 2000, ["red_circle"], click="https://a"))
    message = ntfy.received[0]
    assert message["topic"] == "dl"
    assert message["title"] == "録画開始"
    assert len(message["message"]) == MESSAGE_LIMIT
    assert message["tags"] == ["red_circle"]
    assert message["click"] == "https://a"
    assert ntfy.auth == ["Bearer tk_abc"]


async def test_no_token_sends_no_auth_header() -> None:
    with fake_ntfy() as ntfy:
        await send_ntfy(NtfyConfig(server=ntfy.url, topic="dl"), Message("t", "m"))
    assert ntfy.auth == [None]
    assert "click" not in ntfy.received[0]


@pytest.mark.parametrize(
    ("status", "error"),
    [(403, "refused the access token"), (500, "answered with error 500")],
)
async def test_server_errors(status: int, error: str) -> None:
    with fake_ntfy() as ntfy:
        ntfy.status = status
        with pytest.raises(NotifyError, match=error):
            await send_ntfy(NtfyConfig(server=ntfy.url, topic="dl"), Message("t", "m"))


async def test_unreachable_server() -> None:
    with fake_ntfy() as ntfy:
        url = ntfy.url
    with pytest.raises(NotifyError, match="Couldn't reach the ntfy server"):
        await send_ntfy(NtfyConfig(server=url, topic="dl"), Message("t", "m"))
