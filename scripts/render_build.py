#!/usr/bin/env python3
"""Prepare and install PiPiName on Render.

Render's Git checkout behavior for Git LFS objects is not documented as a
guarantee. This script verifies the bundled SQLite database and downloads the
real LFS object from GitHub when the checkout contains only an LFS pointer.
"""

from __future__ import annotations

import os
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "src" / "pipiname" / "data" / "pipiname.sqlite3"
SQLITE_HEADER = b"SQLite format 3\x00"
GITHUB_REPOSITORY = "zhangdabao131-dev/PiPiName"


def is_sqlite_database(path: Path) -> bool:
    if not path.is_file():
        return False
    with path.open("rb") as file:
        return file.read(len(SQLITE_HEADER)) == SQLITE_HEADER


def run_git_lfs_pull() -> None:
    try:
        subprocess.run(
            ["git", "lfs", "pull", "--include", DATABASE.relative_to(ROOT).as_posix()],
            cwd=ROOT,
            check=False,
        )
    except OSError:
        # Some native build images might not include Git LFS.
        pass


def download_database() -> None:
    commit = os.environ.get("RENDER_GIT_COMMIT", "master")
    relative_path = DATABASE.relative_to(ROOT).as_posix()
    url = f"https://media.githubusercontent.com/media/{GITHUB_REPOSITORY}/{commit}/{relative_path}"
    temporary = DATABASE.with_suffix(".sqlite3.download")
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading SQLite index from GitHub ({commit}) ...", flush=True)
    try:
        urllib.request.urlretrieve(url, temporary)
        if not is_sqlite_database(temporary):
            raise RuntimeError("downloaded file is not a valid SQLite database")
        temporary.replace(DATABASE)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_database() -> None:
    if is_sqlite_database(DATABASE):
        print("SQLite index is present.", flush=True)
        return
    print("SQLite index is missing or is only a Git LFS pointer.", flush=True)
    run_git_lfs_pull()
    if not is_sqlite_database(DATABASE):
        download_database()
    size_mb = DATABASE.stat().st_size / 1024 / 1024
    print(f"SQLite index ready ({size_mb:.2f} MB).", flush=True)


def main() -> int:
    ensure_database()
    subprocess.check_call([sys.executable, "-m", "pip", "install", "."], cwd=ROOT)
    subprocess.check_call(
        [
            sys.executable,
            "-c",
            "from pipiname.index import NameIndex; assert NameIndex().health()['ok']",
        ],
        cwd=ROOT,
    )
    print("Render build validation passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())