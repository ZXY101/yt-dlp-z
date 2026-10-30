class ArgumentError(ValueError):
    """User-supplied yt-dlp options that can't be used. The message is shown to the user."""


class SchemaUnavailableError(RuntimeError):
    """yt-dlp's option schema couldn't be read (yt-dlp missing or broken)."""
