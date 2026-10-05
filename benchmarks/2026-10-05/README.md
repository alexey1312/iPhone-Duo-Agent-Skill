# Benchmark — 2026-10-05

Six new cases for the guidance taken from Apple's forum answers
(`references/sources.md` › Developer Forums Q&A),
run with `claude plugin eval` on plugin version **1.4.0**,
Claude Code 2.1.289, model `claude-opus-5-5`, judge `claude-sonnet-5-5`.
The machine had Xcode 27.0 selected with `xcode-select`
and Xcode 27.1 (27A9269) installed next to it.

```bash
python3 scripts/build_plugin_evals.py "$TMPDIR/duo-plugin-eval"   # then keep only the six cases
claude plugin eval "$TMPDIR/duo-plugin-eval" --trust-plugin --scaffold \
  --allow-tools Bash Edit Write --model claude-opus-5-5 --judge-model claude-sonnet-5-5 \
  --runs 2 -j 4 --no-publish --max-cost-usd 25 --threshold 0
```

Three runs, because the first one showed two things to fix.
Per-run grader verdicts and costs are in `summary.json`.

| Case | Run 1 with / without | Run 2 with / without | Run 3 with / without |
| --- | --- | --- | --- |
| `adaptivity-audit--fold-state-scene-delegate` | 1.00 / 0.17 | **1.00 / 0.00** | — |
| `bars--custom-back-chevron` | 1.00 / 0.50 | **1.00 / 0.50** | — |
| `bars--custom-tab-bar` | 0.75 / 0.13 | 0.50 / 0.00 | **0.92 / 0.00** (3 runs per arm) |
| `layout--compositional-fold` | 0.63 / 0.25 | **1.00 / 0.25** | — |
| `layout--sheet-fold-placement` | 0.83 / 0.17 | **0.83 / 0.34** | — |
| `layout--webview-fold` | 0.90 / 0.10 | **1.00 / 0.20** | — |
| Mean Δ | +0.63 | +0.67 | +0.91 (one case) |

Bold is the run that counts for each case: the last one after its last change.
Two runs per arm (three in run 3) is a small sample;
read a single failed criterion as a hint, not a rate.

## What changed between runs

The failures of run 1 were read before anything was changed, as `CONTRIBUTING.md` asks.

1. **The selected Xcode hid the SDK.** One `compositional-fold` run checked the selected
   Xcode 27.0, found no `reservedRegions`, and planned the fix as *blocked*.
   Two other runs found Xcode 27.1 next to it by themselves.
   `sdk_api_check.py` now lists newer SDKs installed in other `/Applications/Xcode*.app`
   bundles and prints the `DEVELOPER_DIR` command to re-run with.
   It still changes nothing.
2. **One criterion asked for two claims.** `compositional-fold` e01 wanted both
   "no automatic fold avoidance" and "no insets"; answers that explained the insets
   correctly failed it. The criterion now has one core claim and keeps the rest as
   examples in parentheses, the way `JUDGE_PREAMBLE` reads them.
3. **Agents dropped the migration.** In run 2 both `custom-tab-bar` answers accepted
   "we can't move to `UITabBarController` this quarter" and planned only the custom
   route. `iphone-duo-bars` now keeps the migration as a plan item, with what the
   custom bar keeps missing. Run 3 has it in all three answers; the judge passed two
   (*Still failing*, below).

## What the Δ measures

Unlike `2026-09-19/`, these cases allow `Bash`, so the baseline could read the files,
grep the SDK and run anything it liked.
The gap is knowledge the baseline does not have: the forum answers are dated after the
model's training, and several are behaviours measured on the simulator
(`scripts/probes/forum_probe.swift`), not API names.
The baseline's reasoning was often sound; what it lacked was the API and the facts.
In run 2:

- `fold-state-scene-delegate`: both baseline answers rejected the stored fold state,
  as the skill does, but moved the layout onto `UIHingeInteraction` updates instead of
  the reserved regions. Both said they could not find the hinge API in the selected
  27.0 SDK and did not look for another Xcode.
- `webview-fold`: both said correctly that `env(safe-area-inset-*)` cannot describe
  the crease and that WebKit does not fill `env(viewport-segment-*)`. Neither found a
  native fold API in the selected 27.0 SDK; one moved the button to a corner instead.
- `custom-back-chevron`: both got the back indicator image right (0.50), but not why a
  custom-view item stays horizontal or what `axisBehavior` does.

So part of this Δ is the selected Xcode: the baseline has no checker that points at
Xcode 27.1, and it does not know that the hinge and region APIs exist.

## Still failing

- `sheet-fold-placement` run 2, one answer: it said the placement applies in every
  pose but left out that a folded sheet goes to the leading side by default.
  The skill states it; the answer omitted it.
- `custom-tab-bar` run 3, one answer: the judge failed e01 three times, but the answer
  states that no API moves a custom bar and plans the move to `UITabBarController` as a
  long-term item (DUO-04). Read it as a grader miss; the pilot in `CONTRIBUTING.md`
  saw about one in four.

## Cost

| Run | Agents | Judge | Duration |
| --- | --- | --- | --- |
| 1 | $8.11 | $2.11 | 405 s |
| 2 | $8.23 | $2.25 | 405 s |
| 3 | $2.54 | $0.94 | 168 s |

The runner's `costUsd` leaves out the judge (`CONTRIBUTING.md`); the judge column is the
sum of the per-run `judgeCostUsd`.
