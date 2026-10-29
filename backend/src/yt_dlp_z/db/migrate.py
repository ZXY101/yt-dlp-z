from pathlib import Path

from alembic import command
from alembic.config import Config

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def alembic_config(database_path: Path) -> Config:
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    # Migrations use the sync sqlite driver so they can run in a worker thread
    # at startup without nesting event loops.
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")
    return config


def upgrade_to_head(database_path: Path) -> None:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    command.upgrade(alembic_config(database_path), "head")
