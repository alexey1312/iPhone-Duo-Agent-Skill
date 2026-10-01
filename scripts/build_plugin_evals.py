#!/usr/bin/env python3
"""Stage the plugin with its skill-creator evals as a `claude plugin eval` suite.

`skills/*/evals/evals.json` stays the single source of the cases. This script
writes a copy of the plugin *without* any `evals/` directory — the expectations
are the answer key, and an agent that can read its skill's directory must not
find them there — and puts the generated suite next to it:

    <out>/.claude-plugin/        copied
    <out>/skills/<skill>/        copied, minus evals/
    <out>/evals/<skill>--<case>/
        case.yaml                prompt, tools, graders (JSON, which is YAML)
        scaffold.sh              copies the fixture into the run's workspace
        fixture/<Project>/       from skills/<skill>/evals/files/

Plan-only cases get read-only tools plus Bash and are graded on the final
message; cases that ask for an edit also get Edit and Write and are graded on
the whole trace, plus regex checks on the files they should leave behind.
Every case carries a low-weight check that the trace never touches an answer
key. Run it outside the repository so nothing above the stage leads back to
the expectations:

    python3 scripts/build_plugin_evals.py "$TMPDIR/duo-plugin-eval"
    claude plugin eval "$TMPDIR/duo-plugin-eval" --scaffold --allow-tools Bash Edit Write \\
        --judge-model claude-sonnet-5-5 --no-publish --max-cost-usd 5
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.1"
EDIT_MARKERS = ("Fix it", "fix it", "Clean up", "apply what's safe", "Just do it", "Go ahead")
READ_TOOLS = ["Read", "Glob", "Grep", "Skill", "Bash"]
EDIT_TOOLS = READ_TOOLS + ["Edit", "Write"]
# Plan-only cases cannot modify anything (no Edit or Write), so this expectation
# would be a constant pass that only dilutes the score.
STRUCTURAL = "No file in the project copy was modified."
ANSWER_KEY = r"graders/|case\.yaml|evals\.json"

# End-state checks for the cases that ask for an edit: (file in the workspace, pattern, match).
FILE_CHECKS: dict[str, list[tuple[str, str, str]]] = {
    "hinge-status-switch": [
        ("HingeBadge/HingeBadge/HingeBadge.swift", r"default\s*:", "contains"),
        ("HingeBadge/HingeBadge/HingeBadge.swift", r"@unknown", "not_contains"),
    ],
    "mac-host-tests-hinge": [
        ("FoldKit/Sources/FoldKit/FoldMeter.swift", r"#if\s+(os\(iOS\)|!os\(macOS\))", "contains"),
        ("FoldKit/Sources/FoldKit/FoldMeter.swift", r"#available\(iOS 27\.1", "contains"),
    ],
    "apply-with-installed-sdk": [
        ("PodcastPlayer/PodcastPlayer/PlayerScreen.swift", r"ArrangementView", "contains"),
        ("PodcastPlayer/PodcastPlayer/PlayerScreen.swift", r"axisBehavior\(\.horizontalOnly\)", "contains"),
        ("PodcastPlayer/PodcastPlayer/PlayerScreen.swift", r"[#@]available\(iOS 27\.1", "contains"),
    ],
}

SCAFFOLD = """#!/bin/bash
# Runs in the eval's empty workspace; copies this case's fixture into it.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -R "$here/fixture/." .
"""


def load_cases(root: Path = ROOT) -> list[dict]:
    cases = []
    for path in sorted(root.glob("skills/*/evals/evals.json")):
        skill = path.parts[-3]
        for item in json.loads(path.read_text(encoding="utf-8"))["evals"]:
            cases.append({**item, "skill": skill})
    return cases


def is_edit(case: dict) -> bool:
    return any(marker in case["prompt"] for marker in EDIT_MARKERS)


def case_id(case: dict) -> str:
    return f"{case['skill'].removeprefix('iphone-duo-')}--{case['name']}"


def case_definition(case: dict) -> dict:
    edit = is_edit(case)
    graders = []
    for index, expectation in enumerate(case["expectations"], start=1):
        if not edit and expectation == STRUCTURAL:
            continue
        graders.append({
            "type": "llm",
            "name": f"e{index:02d}",
            "criteria": f"Pass only if this holds for the agent's work: {expectation}",
            "focus": "trace" if edit else "last_message",
        })
    for number, (file, pattern, match) in enumerate(FILE_CHECKS.get(case["name"], []), start=1):
        graders.append({"type": "regex", "name": f"file{number:02d}", "target": {"source": "file", "path": file},
                        "pattern": pattern, "match": match})
    graders.append({"type": "regex", "name": "no-answer-key", "target": "trace", "pattern": ANSWER_KEY,
                    "match": "not_contains", "weight": 0.01})
    definition = {
        "schema_version": SCHEMA_VERSION,
        "name": case_id(case),
        "description": case["expected_output"],
        "tags": [case["skill"].removeprefix("iphone-duo-"), "edit" if edit else "plan"],
        "execution": {
            "prompt": case["prompt"].replace("evals/files/", "./"),
            "max_turns": 40 if edit else 30,
            "timeout_seconds": 900,
            "allowed_tools": EDIT_TOOLS if edit else READ_TOOLS,
        },
        "graders": graders,
    }
    if case["files"]:
        definition["context"] = {"scaffold_script": "scaffold.sh"}
    return definition


def stage_plugin(out: Path, root: Path = ROOT) -> None:
    shutil.copytree(root / ".claude-plugin", out / ".claude-plugin")
    shutil.copytree(root / "skills", out / "skills", ignore=shutil.ignore_patterns("evals", "__pycache__"))
    shutil.copy2(root / "LICENSE", out / "LICENSE")


def build(out: Path, root: Path = ROOT) -> list[str]:
    if out.exists():
        shutil.rmtree(out)
    stage_plugin(out, root)
    written = []
    for case in load_cases(root):
        directory = out / "evals" / case_id(case)
        directory.mkdir(parents=True)
        (directory / "case.yaml").write_text(json.dumps(case_definition(case), indent=2) + "\n", encoding="utf-8")
        if case["files"]:
            (directory / "scaffold.sh").write_text(SCAFFOLD, encoding="utf-8")
            for relative in case["files"]:
                source = root / "skills" / case["skill"] / relative
                shutil.copytree(source, directory / "fixture" / source.name)
        written.append(case_id(case))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out", type=Path, help="stage directory, outside the repository")
    args = parser.parse_args(argv)
    out = args.out.resolve()
    if out == ROOT or ROOT in out.parents:
        print("build_plugin_evals: stage outside the repository, or the answer key is reachable from it",
              file=sys.stderr)
        return 2
    cases = build(out)
    print(f"staged {len(cases)} cases in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
