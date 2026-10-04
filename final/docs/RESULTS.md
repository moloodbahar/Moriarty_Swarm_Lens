# What the experiment found

## Final demonstration: label-swap score provenance

Question: how was the GPT-5.5 native label-swap batch at commit `adce92c` produced?

Input: 98 messages; six cumulative prefixes containing 14, 16, 31, 47, 79 and 98 messages; four observer conditions; one repeat. Observer: GPT-4.1-mini, reported snapshot `gpt-4.1-mini-2025-04-14`. GPT-5.5 is the agent named in the source case, not the observer model.

| Setup | Separate rescoring | Reuse per response | Shared-context consistency | Other |
|---|---:|---:|---:|---:|
| Fresh | .05 | .05 | .80 | .10 |
| History | .86 | .04 | .06 | .04 |
| Ledger | .10 | .05 | .80 | .05 |
| Recap | .05 | .75 | .10 | .10 |

These are descriptive model reports. There is no audited process gold label and the options partly overlap: scoring items separately need not mean separate contexts.

The history condition's probability of separate rescoring rose from .75 to .86. Fresh moved from .85 to .05. Ledger assigned .80 to shared-context consistency at all six checkpoints, with an unchanged full distribution. Recap moved from separate rescoring (.75) to reuse (.75 at the final checkpoint). Stability is not automatically correctness, and change is not automatically improvement.

## Submitted review

| Setup | Alternatives acknowledged | Process overclaim marked yes | Explanation matches probabilities |
|---|---:|---:|---:|
| Fresh | 5/6 | 6/6 | 6/6 |
| History | 2/6 | 6/6 | 6/6 |
| Ledger | 6/6 | 5/6 | 6/6 |
| Recap | 5/6 | 6/6 | 6/6 |
| Total | 18/24 | 23/24 | 24/24 |

One supplied review pass, no independent second rater, no demonstrated blind adjudication. These labels are retained exactly as submitted. The sole “no overclaim” label, ledger c4, has a note explaining probability/rationale consistency rather than why the process inference is supported. Many other notes are brief. The 5/6 versus 6/6 difference does not establish a ledger benefit.

## Mechanical verification

- All 24 saved response records pass parsing, probability, source-span and request-hash validation.
- All 144 formal evidence entries resolve to exact text in the permitted prefix.
- Reconstructed requests contain the correct prefix and allowed history; source citations do not reference future records.
- The supplied review matches the plan hash and contains 24 distinct valid job IDs.
- Reported usage: 775,775 input tokens and 9,243 output tokens across accepted responses. No dollar estimate is inferred. A resume manifest's attempt count describes its latest invocation, not the whole experiment.
- The bundle does not provide a full history of failed or discarded attempts. We report the accepted records that were supplied, not an uninterrupted 24-call success rate.

These are consistency checks on saved records. They do not establish semantic accuracy, independent certification of API execution, or truthful source-agent claims.

Plan SHA-256: `d686b7ef59aef61b1f67bb2a2e6526b416b8a6baebf50411ff453924add2d7d5`.

## Separate artifact audit

Public repository: https://github.com/ai-village-agents/research-2026-05

Target commit: `adce92cae1e00083a062e1fed1e92f2631569ad6`.
Later repository snapshot: `2442b493c0b6eb2fcd3045c77bf5b463b29b31c5`.

Matching the same underlying responses across label conditions gave:

| Source judge | Identical five-score tuples / 40 pairs | Changed score cells / 200 |
|---|---:|---:|
| GPT-5.5 | 40/40 | 0/200 |
| Claude | 5/40 | 83/200 |
| Gemini | 0/40 | 106/200 |
| Kimi | 4/40 | 109/200 |

Equality is a real artifact finding, not proof of the execution procedure. Metadata describing native scoring is a report. Other judges are not matched causal controls for how GPT produced its files. The earlier GPT artifact had 9/40 identical pairs; it is a different file version and must not be substituted for the target.

Some chat summaries shortened the caveat about interpretation. The canonical report retained it. We should not claim that the entire swarm erased the caveat.

The external audit was conducted separately and was not part of the observer's visible prefixes. These findings combine the experiment with investigator-led artifact analysis; they were not all automatically discovered by the observer pipeline.

## What remains unknown

Which generation procedure actually produced the target scores. Identical outputs are compatible with several procedures. The next useful evidence is the exact input arrangement, model-call or computer-use records, and execution/code history bound to the target file hashes. More peer assertions or a successful statistics rerun cannot settle that question.

No real accuracy improvement, causal mechanism for observer disagreement, or superiority of the ledger has been established.
