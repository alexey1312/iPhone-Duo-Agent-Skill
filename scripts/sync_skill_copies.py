#!/usr/bin/env python3
"""Copy canonical references and scripts into each skill that uses them.

Each skill must work when installed alone, so shared files live in two places:
the canonical copy at the repository root and a copy inside every skill that
needs it. Edit the root copy, then run this script. `--check` fails when a copy
has drifted, which is what CI runs.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ALL_SKILLS = [
    "iphone-duo-readiness",
    "iphone-duo-adaptivity-audit",
    "iphone-duo-bars",
    "iphone-duo-layout",
    "iphone-duo-displays",
]
POSE_SKILLS = ["iphone-duo-readiness", "iphone-duo-bars", "iphone-duo-layout", "iphone-duo-displays"]

COPIES: dict[str, list[str]] = {
    "references/sources.md": ALL_SKILLS,
    "references/api-availability.md": ALL_SKILLS,
    "references/recommendation-format.md": ALL_SKILLS,
    "references/pose-test-matrix.md": POSE_SKILLS,
    "references/device-geometry.md": POSE_SKILLS,
    "scripts/duo_scan.py": ALL_SKILLS,
    "scripts/sdk_api_check.py": ALL_SKILLS,
}


def planned() -> list[tuple[Path, Path]]:
    pairs = []
    for relative, skills in COPIES.items():
        for skill in skills:
            pairs.append((ROOT / relative, ROOT / "skills" / skill / relative))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    args = parser.parse_args(argv)

    drifted = []
    for source, destination in planned():
        if destination.exists() and filecmp.cmp(source, destination, shallow=False):
            continue
        drifted.append(destination.relative_to(ROOT))
        if not args.check:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    if args.check:
        for path in drifted:
            print(f"out of sync: {path}")
        if drifted:
            print("run: python3 scripts/sync_skill_copies.py")
            return 1
        print("all skill copies in sync")
        return 0
    print(f"updated {len(drifted)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
