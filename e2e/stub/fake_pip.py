#!/usr/bin/env python3
"""Stand-in for `pip install --target DIR ... yt-dlp[default]` in tests. Never touches the
network: it writes just the package metadata yt-dlp-z reads the version from.

Installs yt-dlp 2099.1.1, or 2099.1.2.dev0 with --pre (the nightly channel).
Fails like pip without network when FAKE_PIP_FAIL is set.
"""

import os
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[1:]
    print("Collecting yt-dlp[default]")
    if os.environ.get("FAKE_PIP_FAIL"):
        print("ERROR: No matching distribution found for yt-dlp[default]")
        sys.exit(1)
    target = Path(args[args.index("--target") + 1])
    version = "2099.1.2.dev0" if "--pre" in args else "2099.1.1"
    dist_info = target / f"yt_dlp-{version}.dist-info"
    dist_info.mkdir(parents=True)
    metadata = f"Metadata-Version: 2.1\nName: yt-dlp\nVersion: {version}\n"
    (dist_info / "METADATA").write_text(metadata)
    print(f"Successfully installed yt-dlp-{version}")


if __name__ == "__main__":
    main()
