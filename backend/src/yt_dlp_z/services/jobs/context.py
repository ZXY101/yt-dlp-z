from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from yt_dlp_z.core.config import Settings
from yt_dlp_z.db.models.job import Job
from yt_dlp_z.schemas.jobs import JobEvent, JobOut
from yt_dlp_z.services.events import EventHub
from yt_dlp_z.services.proxies.pool import ProxyPool
from yt_dlp_z.services.ytdlp.schema import OptionSchemaProvider


@dataclass(frozen=True)
class JobContext:
    session_factory: async_sessionmaker[AsyncSession]
    hub: EventHub
    settings: Settings
    schemas: OptionSchemaProvider
    proxies: ProxyPool


def publish_job(hub: EventHub, job: Job) -> None:
    hub.publish(JobEvent(job=JobOut.model_validate(job)).model_dump(mode="json"))


def job_log_path(settings: Settings, job_id: int) -> Path:
    return settings.config_dir / "logs" / f"job-{job_id}.log"
