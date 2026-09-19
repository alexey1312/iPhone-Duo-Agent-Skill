# Benchmark — 2026-09-13

Run with Anthropic's [skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator)
workflow on Claude Opus 5, Xcode 27.0 beta 6 (iOS 27.0 SDK), one run per configuration.

> **These numbers are a record of that day, not a current measurement.**
> They were scored against the eval assertions as they stood on 2026-09-13.
> Six of those assertions have since been rewritten: they hard-coded
> "the installed 27.0 SDK", which on a 27.1 machine scores a correct agent *wrong*.
> The toolchain moved too — Xcode 27.1 ships the iOS 27.1 SDK and the iPhone Duo
> simulator, so the "blocked on 27.1" answers the baseline was penalised for missing
> are no longer the right answers.
> Treat the 100 % against 56 % as historical. Re-run before citing it:
>
> ```bash
> claude plugin eval . --trust-plugin
> ```
>
> Write a new dated directory next to this one rather than editing this one —
> it is evidence of a run, and editing it destroys that.

## Task evals (with skill vs. without skill)

Each eval gives an agent a small fixture project from `skills/<skill>/evals/files/` and a
realistic prompt. The baseline agent had no skill but could search the web and found
Apple's iPhone Duo tech talks on its own, so the gap measures workflow, not access to
information. Separate grader agents scored each run (they could see which configuration they graded) against the expectations in
`skills/<skill>/evals/evals.json`.

| Eval | Skill | With skill | Without skill |
| --- | --- | --- | --- |
| full-readiness-plan | iphone-duo-readiness | 11/11 | 6/11 |
| missing-27-1-sdk | iphone-duo-readiness | 6/6 | 3/6 |
| documented-orientation-exception | iphone-duo-adaptivity-audit | 7/7 | 4/7 |
| toolbar-audit | iphone-duo-bars | 8/8 | 6/8 |
| centered-column-and-fold | iphone-duo-layout | 8/8 | 2/8 |
| camera-teleprompter | iphone-duo-displays | 8/8 | 6/8 |
| **Pass rate** | | **100%** | **56%** |

Cost: +97 s and ~27k tokens per task on average. Iteration 1 (before the fixes below)
scored 98% vs 70% on looser assertions — see `iteration-1-benchmark.md`.

What iteration 1 taught the skills: sequence work that compiles today ahead of a
toolchain upgrade; never ship guessed iOS 27.1 calls behind compile-time guards;
preserve existing behavior and typecheck edits; keep documented exceptions minimal;
check camera-session prerequisites before a capture accessory; never paginate scrolling
text around the fold; the scanner now joins Swift member chains across lines and catches
symmetric insets through a local variable. The iteration-2 baseline reuses iteration-1
no-skill outputs, regraded against the stricter assertions.

## Trigger accuracy (`skills/<skill>/evals/trigger-evals.json`)

20 realistic queries per skill (about half near-misses), 3 runs each, 60/40 train/test
split, via skill-creator's `run_loop`.

| Skill | Train | Test | Result |
| --- | --- | --- | --- |
| iphone-duo-readiness | 12/12 | 8/8 | original description kept |
| iphone-duo-adaptivity-audit | 13/13 | 5/7 → 20/20 on the full set | exclusion for brightness / locked game orientation added |
| iphone-duo-bars | 13/13 | 7/7 | original description kept |
| iphone-duo-layout | 12/13 → 13/13 | 5/7 → 7/7 | optimized description adopted |
| iphone-duo-displays | 12/13 | 8/8 | one layout near-miss; exclusion added, not re-measured |

Note: skill-creator's `run_eval.py` runs parallel workers in one project directory, so
each `claude -p` sees every worker's temporary command file and trigger detection fails
(3/3 correct with one worker, 1/3 with three). These numbers come from a patched copy
that gives each query its own temporary project directory.
