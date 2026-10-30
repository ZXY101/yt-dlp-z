from pydantic import BaseModel, Field

MAX_CONCURRENT_DOWNLOADS = 10


class AppSettings(BaseModel):
    download_dir: str = Field(min_length=1, max_length=4096)
    max_concurrent_downloads: int = Field(ge=1, le=MAX_CONCURRENT_DOWNLOADS)
