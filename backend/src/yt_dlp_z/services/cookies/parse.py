"""Checks that uploaded text is a Netscape cookies.txt file and summarises it.

The summary (count and domains) is all the app ever shows about a cookies file.
"""

from dataclasses import dataclass

FIELD_COUNT = 7
HTTP_ONLY_PREFIX = "#HttpOnly_"


class CookieFormatError(ValueError):
    pass


@dataclass(frozen=True)
class CookieSummary:
    cookie_count: int
    domains: list[str]


def _cookie_fields(line: str) -> list[str] | None:
    """The fields of a cookie line, or None for blank and comment lines."""
    if line.startswith(HTTP_ONLY_PREFIX):
        line = line.removeprefix(HTTP_ONLY_PREFIX)
    elif not line.strip() or line.startswith("#"):
        return None
    return line.split("\t")


def summarise_cookies(text: str) -> CookieSummary:
    domains: set[str] = set()
    count = 0
    for number, line in enumerate(text.splitlines(), start=1):
        fields = _cookie_fields(line)
        if fields is None:
            continue
        if len(fields) != FIELD_COUNT or not fields[0]:
            # Never echo the line itself: it may hold a session token.
            raise CookieFormatError(
                f"Line {number} isn't in Netscape cookies.txt format "
                "(7 tab-separated fields). Export the file with a cookies.txt extension."
            )
        domains.add(fields[0].lstrip("."))
        count += 1
    if count == 0:
        raise CookieFormatError("The file has no cookies in it.")
    return CookieSummary(cookie_count=count, domains=sorted(domains))
