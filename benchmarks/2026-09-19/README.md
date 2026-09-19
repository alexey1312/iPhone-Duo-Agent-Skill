# Benchmark — 2026-09-19

One case, run with `claude plugin eval` on plugin version **1.2.1**, Claude Code
2.1.278, against **Xcode 27.1 (27A9269)** and the iOS 27.1 SDK.
Three runs per arm, three judge votes per run.
346 s, $2.01.

```bash
claude plugin eval . --trust-plugin
```

| Case | With skill | Without skill | Δ |
| --- | --- | --- | --- |
| `sdk-availability-honesty` | **1.00** (3/3) | 0.33 (1/3) | **+0.67** |

## This is not a replacement for `2026-09-13/`

That benchmark ran **six** task evals plus trigger accuracy through skill-creator.
This is **one** case through a different runner.
It is narrower in coverage and better in statistics — three runs and nine judge
votes per arm against that one's single run — so the two answer different questions
and the numbers do not belong in the same table.

## What the Δ actually measures

**Read the baseline's failures before citing +0.67.**
Both losing runs were *honest refusals*, not wrong answers:

> "I don't know, and I'd be making it up if I told you either way. Both
> `ArrangementView` and `AVCaptureDevice.DeviceType.builtInOuterUltraWideCamera`
> are symbols I don't have. My knowledge cutoff is May 2026 and today is September
> 19, 2026 … The names are plausible enough that I could confidently invent
> signatures for them, which is exactly why I'm not going to."

That is good behaviour. The grader scores *did you give the right availability
answer*, and a principled "I cannot know this" scores zero against that rubric.

So this Δ measures **the skill supplying knowledge the model does not have and
could not reach in the sandbox** — the case's `allowed_tools` are `Read, Glob,
Grep, Skill`, with no `Bash`, so the baseline could not run `sdk_api_check.py` or
grep the SDK even in principle. It does **not** show the baseline hallucinating,
and it is not comparable to `2026-09-13/`, where the baseline had web search and
the gap measured workflow rather than knowledge.

The one baseline run that passed got there anyway, so a third of the time the
answer is reachable without the skill.

## Cost

| | Turns | Duration | Cost per run |
| --- | --- | --- | --- |
| With skill | 9–11 | 45–59 s | ~$0.47 |
| Without | 4–5 | 55–71 s | ~$0.20 |

The skill roughly doubles turns and cost on this case.

## Worth doing next

Add `Bash` to the case's `allowed_tools` and re-run. That tests the harder and more
useful question — whether the skill still helps an agent that **can** check the SDK
itself — and would make this comparable to the 2026-09-13 baseline, which had a way
to find things out. As it stands the baseline was asked a question it had no route
to answer.

Raw runner output: `aggregate-result.json`.
