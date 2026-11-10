from pathlib import Path
from typing import Any

from yt_dlp_z.db.models.job import Job, JobKind, JobStatus
from yt_dlp_z.services.jobs.duplicates import find_same_job

URL = "https://www.youtube.com/watch?v=abc"
OUT = "/downloads"


def job(**fields: Any) -> Job:
    values: dict[str, Any] = {
        "url": URL,
        "status": JobStatus.COMPLETED,
        "kind": JobKind.DOWNLOAD,
        "options": {},
        "extra_args": "",
        "output_dir": OUT,
        "folders": None,
        "file_name": None,
        "media_files": False,
        "cookie_id": None,
        "filepath": None,
    }
    return Job(**(values | fields))


def planned(**fields: Any) -> dict[str, Any]:
    return {"url": "https://youtu.be/abc", "options": {}, "recording": None} | fields


def test_a_running_or_finished_job_with_the_same_settings_is_found() -> None:
    running = job(status=JobStatus.RUNNING)
    assert find_same_job([running], planned(), OUT) is running


def test_failed_and_cancelled_jobs_are_retried() -> None:
    jobs = [job(status=JobStatus.FAILED), job(status=JobStatus.CANCELLED)]
    assert find_same_job(jobs, planned(), OUT) is None


def test_other_settings_or_folders_are_new_downloads() -> None:
    assert find_same_job([job()], planned(options={"--extract-audio": True}), OUT) is None
    assert find_same_job([job()], planned(), "/elsewhere") is None
    assert find_same_job([job()], planned(recording={"from_start": True}), OUT) is None


def test_a_finished_download_whose_file_is_gone_is_downloaded_again(tmp_path: Path) -> None:
    gone = job(filepath=str(tmp_path / "gone.mp4"))
    assert find_same_job([gone], planned(), OUT) is None
    kept = tmp_path / "kept.mp4"
    kept.write_text("video")
    there = job(filepath=str(kept))
    assert find_same_job([there], planned(), OUT) is there
