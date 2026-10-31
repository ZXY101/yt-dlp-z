"""Recognises yt-dlp errors that mean "try another proxy"."""

# YouTube's bot check and rate limits, and proxies that can't be reached. Lowercase.
BLOCK_HINTS = (
    # "Sign in to confirm you're not a bot" (YouTube varies the apostrophe).
    "not a bot",
    "http error 429",
    "too many requests",
    "rate-limited",
    "unable to connect to proxy",
    "proxyerror",
    "tunnel connection failed",
    "socks",
)


def is_proxy_block(error: str | None) -> bool:
    if not error:
        return False
    text = error.lower()
    return any(hint in text for hint in BLOCK_HINTS)
