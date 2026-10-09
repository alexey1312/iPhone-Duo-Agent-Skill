# Contributing

Thanks for helping keep these skills accurate.

## Good contributions

- **SDK updates.** When a new Xcode ships, run `python3 scripts/sdk_api_check.py`, update
  the measured snapshot in `references/api-availability.md`, and fix any sample whose
  spelling changed. Say which Xcode build you checked.
- **Scanner rules.** Add a `Rule` to `scripts/duo_scan.py` with a session citation, a
  positive and a negative test in `tests/test_duo_scan.py`, and a row in
  `READINESS-CHECKS.md`.
- **False positives** found on real projects, with a minimal reproduction.
- **Evals** for behavior the skills get wrong: add a case to
  `skills/<skill>/evals/evals.json` (with a small fixture project under
  `skills/<skill>/evals/files/`) or a query to `skills/<skill>/evals/trigger-evals.json`.

## Rules

- Guidance must trace to an Apple session, documentation page or the SDK. Label
  anything else as inference.
- Edit shared references and scripts at the repository root, then run
  `python3 scripts/sync_skill_copies.py`.
- No third-party Python dependencies.

## Evaluating a change

The skills are developed with Anthropic's
[skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator):
run each eval with and without the skill, grade the expectations, aggregate a benchmark,
and review outputs in its viewer. Trigger accuracy is tuned with its `run_loop` against
`trigger-evals.json`. Keep workspaces outside the repository (`*-workspace/` is ignored).

The same cases also run through `claude plugin eval`.
`scripts/build_plugin_evals.py` stages a copy of the plugin without any `evals/`
directory — the expectations are the answer key — and writes one `case.yaml` per case
next to it, outside the repository:

```bash
python3 scripts/build_plugin_evals.py "$TMPDIR/duo-plugin-eval"
claude plugin eval "$TMPDIR/duo-plugin-eval" --trust-plugin --scaffold \
  --allow-tools Bash Edit Write --model claude-opus-5-5 --judge-model claude-sonnet-5-5 \
  --no-publish --max-cost-usd 60 --json "$TMPDIR/duo-eval.json"
```

`--no-publish` keeps the HTML report local; without it the report is published.
The runner's `costUsd` leaves out the judge — a four-case pilot cost $3.25 for the
agents and $1.55 for the judge — so set `--max-cost-usd` to about two thirds of the
real budget. Before trusting a full run, read a few failing transcripts: the pilot's
first grader version misjudged about one failure in four.

## Checks

```bash
python3 scripts/sync_skill_copies.py --check
python3 -m unittest discover -s tests -v
```

## Releasing

1. Bump the version in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
   `.cursor-plugin/plugin.json` and `agents/openai.yaml` (the tests check they agree)
   and merge it to `main`.
2. Tag that commit and push the tag:

   ```bash
   git tag v1.1.0 && git push origin v1.1.0
   ```

   If you can merge but cannot push tags, run the `Release` workflow from `main`
   instead (Actions › Release › Run workflow). It tags `v<plugin version>` at
   `main`'s head. It refuses to run from another branch, and it refuses a version
   whose tag already exists.

The `Release` workflow (`.github/workflows/release.yml`) refuses a tag that does not
match the plugin version, re-runs the checks, builds one `.skill` archive per skill
with `scripts/package_skills.py`, and publishes a GitHub release with the archives and
generated notes.
