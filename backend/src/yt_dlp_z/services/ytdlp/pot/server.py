"""Asks a bgutil PO token server for its version (its GET /ping).

The server: https://github.com/Brainicism/bgutil-ytdlp-pot-provider
"""

import asyncio
import json
import re
import urllib.error
import urllib.request

TIMEOUT_SECONDS = 10
# The version becomes part of a pip requirement, so only plain release numbers pass.
VERSION_PATTERN = re.compile(r"^\d+(\.\d+){0,3}$")
NOT_A_PROVIDER = "That address doesn't answer like a bgutil PO token provider."


class PotError(Exception):
    """The provider can't be used. The text is shown to the user."""


def _get_ping(url: str) -> object:
    # Straight to the server, never through HTTP_PROXY, like the yt-dlp plugin does.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(f"{url.rstrip('/')}/ping", timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise PotError(f"The provider answered with error {error.code}.") from error
    except (urllib.error.URLError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise PotError(f"Couldn't reach the provider: {reason}") from error
    except ValueError as error:
        raise PotError(NOT_A_PROVIDER) from error


def _version(url: str) -> str:
    data = _get_ping(url)
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str) or not VERSION_PATTERN.match(version):
        raise PotError(NOT_A_PROVIDER)
    return version


async def server_version(url: str) -> str:
    return await asyncio.to_thread(_version, url)
