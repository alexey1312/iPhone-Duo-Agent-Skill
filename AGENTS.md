# Agent guidance

This repository contains Agent Skills that advise on and change iOS app code.

- **Phase 1 stays read-only.** `duo_scan.py` and `sdk_api_check.py` must never write to
  the scanned project or the SDK. Keep it that way; `test_scan_does_not_modify_files`
  guards the scanner.
- **Every recommendation cites a session and timestamp.** New scanner rules need a
  `source` matching `Tech Talk 1114xx … m:ss` or `WWDC26 278 … m:ss`; the metadata test
  enforces it.
- **The SDK outranks the talks.** Do not add code samples using an API without either
  typechecking them against an SDK that declares it or marking them as reproduced from
  a session page and requiring a 27.1 SDK.
- **Shared files have one source.** Edit `references/*.md` and `scripts/*.py` at the
  root, then run `python3 scripts/sync_skill_copies.py`. Never edit the copies under
  `skills/*/references` or `skills/*/scripts` that the sync script owns.
- **Keep SKILL.md descriptions under 1024 characters** and the `name` equal to the
  directory name.
- **Scanner changes need tests** for both a positive and a negative case.
- **Behavior changes need evals.** Each skill keeps skill-creator evals in
  `skills/<skill>/evals/` (`evals.json` with fixture projects under `files/`, and
  `trigger-evals.json`). Re-run them with and without the skill before claiming an
  improvement; `scripts/package_skills.py` leaves `evals/` out of release archives.
- Keep the plugin version identical in `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json` and
  `agents/openai.yaml`. A GitHub release is cut by pushing a matching `vX.Y.Z` tag;
  the `Release` workflow builds the `.skill` archives (`CONTRIBUTING.md` › Releasing).
- Run before completing a change:

  ```bash
  python3 scripts/sync_skill_copies.py --check
  python3 -m unittest discover -s tests -v
  ```
