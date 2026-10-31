from datetime import timedelta

import pytest
from pydantic import TypeAdapter, ValidationError

from yt_dlp_z.db.models.job import Job, utcnow
from yt_dlp_z.db.models.proxy import Proxy
from yt_dlp_z.schemas.proxies import ProxyUrl
from yt_dlp_z.services.proxies.blocks import is_proxy_block
from yt_dlp_z.services.proxies.check_script import exit_ip, short_error
from yt_dlp_z.services.proxies.pool import ProxyPool
from yt_dlp_z.services.proxies.store import hide_password, is_available, masked_url


def test_proxy_urls() -> None:
    adapter = TypeAdapter(ProxyUrl)
    assert adapter.validate_python(" socks5h://vpn:1080 ") == "socks5h://vpn:1080"
    assert adapter.validate_python("http://u:p@vpn:8888/") == "http://u:p@vpn:8888/"
    for url in ["vpn:1080", "socks5://vpn:notaport", "http://vpn:8888?x=1"]:
        with pytest.raises(ValidationError):
            adapter.validate_python(url)


def test_masked_url_and_hide_password() -> None:
    assert masked_url("http://vpn:8888") == "http://vpn:8888"
    assert masked_url("socks5://me:secret@vpn:1080") == "socks5://me:****@vpn:1080"
    assert masked_url("socks5://:secret@vpn:1080") == "socks5://:****@vpn:1080"
    url = "socks5://me:secret@vpn:1080"
    assert hide_password(f"failed: {url}", url) == "failed: socks5://me:****@vpn:1080"
    assert hide_password("bad password secret", url) == "bad password ****"
    assert hide_password(None, url) is None
    assert hide_password("no password", "http://vpn:8888") == "no password"


@pytest.mark.parametrize(
    ("error", "blocked"),
    [
        ("ERROR: [youtube] x: Sign in to confirm you\u2019re not a bot", True),
        ("ERROR: Unable to download webpage: HTTP Error 429: Too Many Requests", True),
        ("ERROR: Unable to connect to proxy", True),
        ("ERROR: [youtube] x: Video unavailable", False),
        (None, False),
    ],
)
def test_proxy_blocks(error: str | None, blocked: bool) -> None:
    assert is_proxy_block(error) is blocked


def test_exit_ip() -> None:
    assert exit_ip("fl=1\nip=203.0.113.7\nloc=ZA\n") == "203.0.113.7 (ZA)"
    assert exit_ip("ip=203.0.113.7") == "203.0.113.7"
    assert exit_ip("nothing here") is None


def test_short_error() -> None:
    long = OSError(
        "SocksHTTPSConnection(host='www.cloudflare.com', port=443): "
        "Failed to establish a new connection: [Errno 111] Connection refused"
    )
    assert (
        short_error(long) == "Failed to establish a new connection: [Errno 111] Connection refused"
    )
    assert short_error(TimeoutError()) == "TimeoutError"


def test_availability() -> None:
    now = utcnow()
    assert is_available(Proxy(enabled=True), now)
    assert not is_available(Proxy(enabled=False), now)
    # SQLite gives back naive datetimes.
    later = (now + timedelta(minutes=5)).replace(tzinfo=None)
    assert not is_available(Proxy(enabled=True, cooldown_until=later), now)
    assert is_available(Proxy(enabled=True, cooldown_until=now - timedelta(seconds=1)), now)


def pool_of(count: int) -> list[Proxy]:
    return [Proxy(id=number, name=f"P{number}") for number in range(1, count + 1)]


def test_sticky_keeps_a_channel_on_one_proxy() -> None:
    pool, proxies = ProxyPool(), pool_of(3)
    channel = Job(proxy_mode="sticky", subscription_id=7)
    picks = {pool.choose(proxies, channel).id for _ in range(5)}
    assert picks == {proxies[7 % 3].id}
    # One-off downloads have no channel: they rotate.
    one_off = Job(proxy_mode="sticky", subscription_id=None)
    assert [pool.choose(proxies, one_off).id for _ in range(4)] == [1, 2, 3, 1]


def test_random_picks_from_the_free_proxies() -> None:
    proxies = pool_of(3)
    picks = {ProxyPool().choose(proxies, Job(proxy_mode="random")).id for _ in range(50)}
    assert picks <= {1, 2, 3}
    assert len(picks) > 1
