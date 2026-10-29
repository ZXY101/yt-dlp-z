import argparse
import asyncio
import getpass
import json
import os
import sys

import uvicorn

from yt_dlp_z.core.config import get_settings
from yt_dlp_z.db.engine import create_engine, create_session_factory
from yt_dlp_z.db.migrate import upgrade_to_head
from yt_dlp_z.main import create_app
from yt_dlp_z.schemas.auth import MIN_PASSWORD_LENGTH
from yt_dlp_z.services.auth_service import change_password


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yt-dlp-z")
    parser.add_argument("--host", help="bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, help="port (default 8080)")
    parser.add_argument("--config-dir", help="where the database and secrets live")
    parser.add_argument("--reload", action="store_true", help="auto-reload (development)")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("reset-password", help="set a new admin password")
    commands.add_parser("openapi", help="print the OpenAPI schema as JSON")
    return parser


def apply_overrides(args: argparse.Namespace) -> None:
    """CLI flags override env vars by writing to them before settings load."""
    overrides = {
        "YTDLPZ_HOST": args.host,
        "YTDLPZ_PORT": args.port,
        "YTDLPZ_CONFIG_DIR": args.config_dir,
    }
    for name, value in overrides.items():
        if value is not None:
            os.environ[name] = str(value)


async def reset_password(new_password: str) -> None:
    settings = get_settings()
    upgrade_to_head(settings.database_path)
    engine = create_engine(settings.database_path)
    async with create_session_factory(engine)() as session:
        await change_password(session, new_password)
    await engine.dispose()


def prompt_password() -> str:
    password = getpass.getpass("New admin password: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if getpass.getpass("Repeat password: ") != password:
        sys.exit("Passwords do not match.")
    return password


def main() -> None:
    args = build_parser().parse_args()
    apply_overrides(args)
    if args.command == "openapi":
        print(json.dumps(create_app().openapi(), indent=2))
        return
    if args.command == "reset-password":
        asyncio.run(reset_password(prompt_password()))
        print("Password changed. All existing sessions were logged out.")
        return
    settings = get_settings()
    uvicorn.run(
        "yt_dlp_z.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=args.reload,
        proxy_headers=True,
    )
