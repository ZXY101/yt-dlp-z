import pytest

from yt_dlp_z.services.cookies.parse import CookieFormatError, summarise_cookies

FAKE_COOKIES = "\n".join(
    [
        "# Netscape HTTP Cookie File",
        "",
        ".youtube.com\tTRUE\t/\tTRUE\t0\tPREF\tfake-value",
        "#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t0\tSID\tfake-session",
        "example.com\tFALSE\t/\tFALSE\t0\ttheme\tdark",
    ]
)


def test_counts_cookies_and_lists_domains() -> None:
    summary = summarise_cookies(FAKE_COOKIES)
    assert summary.cookie_count == 3
    assert summary.domains == ["example.com", "youtube.com"]


def test_rejects_malformed_lines_without_echoing_them() -> None:
    with pytest.raises(CookieFormatError) as error:
        summarise_cookies("# header\nSID=fake-secret-token; path=/")
    assert "Line 2" in str(error.value)
    assert "fake-secret-token" not in str(error.value)


def test_rejects_files_without_cookies() -> None:
    with pytest.raises(CookieFormatError, match="no cookies"):
        summarise_cookies("# Netscape HTTP Cookie File\n\n")
