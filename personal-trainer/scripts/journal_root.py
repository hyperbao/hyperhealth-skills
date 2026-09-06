#!/usr/bin/env python3
"""Resolve where the coaching journal lives for the current user.

The journal's home is the CoachBridge iCloud Drive folder, so it syncs to the athlete's
devices and is visible in Finder / the Files app. That folder is an iCloud *container*:
on macOS it materialises under ``~/Library/Mobile Documents/`` with a name derived from
the app's container identifier (``iCloud~<reverse-dns>~CoachBridge``). Nothing here
hard-codes that identifier or the home directory — the container is discovered for
whoever is running the skill.

Resolution order (first match wins):

1. ``--root PATH`` / ``--local`` / ``$COACHBRIDGE_JOURNAL_ROOT`` — explicit override
   (dev sandboxes such as ``coach-test/``).
2. iCloud Drive is available AND the CoachBridge container is present → the journal is
   ``<container>/Documents/journal`` (``source: icloud``).
3. iCloud Drive is available but the container has not appeared yet → **no root**
   (``source: icloud-pending``, exit 3). Do NOT fall back: the athlete needs to open the
   CoachBridge iPhone app (it creates the folder) and let iCloud sync it down.
4. iCloud Drive is NOT available on this machine → ``./journal`` in the working
   directory (``source: local``).

Stdlib only (Python >= 3.8). Exit codes: 0 resolved, 2 bad input, 3 iCloud pending.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path

APP_FOLDER_SUFFIX = "~CoachBridge"          # container folders end with the app name
ICLOUD_CONTAINER_PREFIX = "iCloud~"          # ...and start with this on disk
ICLOUD_DRIVE_ROOT = "com~apple~CloudDocs"    # present iff iCloud Drive is enabled
PROFILE_FILE = "client-profile.md"           # written at intake; marks a real journal
ENV_OVERRIDE = "COACHBRIDGE_JOURNAL_ROOT"


def mobile_documents(home: Path) -> Path:
    return home / "Library" / "Mobile Documents"


def icloud_drive_available(home: Path) -> bool:
    """iCloud Drive is on for this user when its root folder exists in Mobile Documents."""
    if platform.system() != "Darwin":
        return False
    return (mobile_documents(home) / ICLOUD_DRIVE_ROOT).is_dir()


def find_containers(home: Path) -> list[Path]:
    """Every CoachBridge iCloud container synced to this Mac, regardless of the
    reverse-DNS prefix in its name (team / bundle changes don't break discovery)."""
    md = mobile_documents(home)
    if not md.is_dir():
        return []
    pattern = f"{ICLOUD_CONTAINER_PREFIX}*{APP_FOLDER_SUFFIX}"
    return sorted(p for p in md.glob(pattern) if p.is_dir())


def pick_container(containers: list[Path]) -> Path:
    """Prefer a container that already holds a journal; else the most recently touched."""
    with_journal = [c for c in containers if (c / "Documents" / "journal" / PROFILE_FILE).is_file()]
    pool = with_journal or containers
    return max(pool, key=lambda c: c.stat().st_mtime)


def journal_exists(root: Path) -> bool:
    return (root / PROFILE_FILE).is_file()


def resolve(cwd: Path, home: Path, override: str | None) -> dict:
    result: dict = {
        "source": None,
        "root": None,
        "exists": False,
        "icloud_available": icloud_drive_available(home),
        "container": None,
        "local_journal_present": journal_exists(cwd / "journal"),
        "notes": [],
    }

    if override:
        root = Path(override).expanduser()
        if not root.is_absolute():
            root = (cwd / root).resolve()
        result.update(source="override", root=str(root), exists=journal_exists(root))
        return result

    containers = find_containers(home)
    if result["icloud_available"] and containers:
        container = pick_container(containers)
        root = container / "Documents" / "journal"
        result.update(source="icloud", root=str(root), exists=journal_exists(root),
                      container=str(container))
        if len(containers) > 1:
            result["notes"].append(
                f"{len(containers)} CoachBridge containers found; using {container.name}. "
                "Others: " + ", ".join(c.name for c in containers if c != container))
        return result

    if result["icloud_available"]:
        result.update(source="icloud-pending")
        result["notes"].append(
            "iCloud Drive is on but the CoachBridge folder hasn't synced to this Mac yet. "
            "Open the CoachBridge app on the iPhone (it creates the folder once 'Sync with "
            "iCloud' was chosen in its setup), check that CoachBridge is enabled under iCloud "
            "Drive on both devices, then re-run. If the athlete chose to keep data on-device "
            "(get_status → journal.mode 'local'), run this with --local instead.")
        return result

    if containers:
        # Folder left behind after iCloud Drive was switched off — not live, don't use it.
        result["notes"].append(
            "A CoachBridge container exists but iCloud Drive is off; ignoring it.")
    root = cwd / "journal"
    result.update(source="local", root=str(root), exists=journal_exists(root))
    result["notes"].append("iCloud Drive is not available here; using the working directory.")
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", metavar="PATH", help="explicit journal root (overrides discovery)")
    ap.add_argument("--local", action="store_true", help="shorthand for --root ./journal (sandbox runs)")
    ap.add_argument("--cwd", metavar="DIR", default=os.getcwd(), help="working directory for the local fallback")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    if args.root and args.local:
        ap.error("--root and --local are mutually exclusive")
    override = args.root or ("./journal" if args.local else None) or os.environ.get(ENV_OVERRIDE) or None

    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.is_dir():
        ap.error(f"--cwd is not a directory: {cwd}")
    home = Path.home()

    result = resolve(cwd, home, override)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"source:            {result['source']}")
        print(f"root:              {result['root'] or '(none — see notes)'}")
        print(f"journal exists:    {'yes' if result['exists'] else 'no (run intake)'}")
        print(f"iCloud available:  {'yes' if result['icloud_available'] else 'no'}")
        if result["container"]:
            print(f"container:         {result['container']}")
        if result["local_journal_present"] and result["source"] != "override":
            print(f"note:              a local ./journal also exists in {cwd} — "
                  "use --local only if the athlete wants that sandbox copy")
        for note in result["notes"]:
            print(f"note:              {note}")

    return 3 if result["source"] == "icloud-pending" else 0


if __name__ == "__main__":
    sys.exit(main())
