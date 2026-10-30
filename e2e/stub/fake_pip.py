#!/usr/bin/env python3
"""Stand-in for `pip install --target DIR ... yt-dlp[default]` in tests. Never touches the
network: it writes just the package metadata yt-dlp-z reads the version from.

Installs yt-dlp 2099.1.1, or 2099.1.2.dev0 with --pre (the nightly channel).
With --dry-run --report - it prints the JSON report of what it would install instead.
Fails like pip without network when FAKE_PIP_FAIL is set.
"""

import json

import os
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[1:]
    if os.environ.get("FAKE_PIP_FAIL"):
        print("ERROR: No matching distribution found for yt-dlp[default]")
        sys.exit(1)
    version = "2099.1.2.dev0" if "--pre" in args else "2099.1.1"
    if "--dry-run" in args:
        install = [{"metadata": {"name": "yt-dlp", "version": version}}]
        print(json.dumps({"version": "1", "install": install}))
        return
    print("Collecting yt-dlp[default]")
    target = Path(args[args.index("--target") + 1])
    dist_info = target / f"yt_dlp-{version}.dist-info"
    dist_info.mkdir(parents=True)
    metadata = f"Metadata-Version: 2.1\nName: yt-dlp\nVersion: {version}\n"
    (dist_info / "METADATA").write_text(metadata)
    print(f"Successfully installed yt-dlp-{version}")


if __name__ == "__main__":
    main()
