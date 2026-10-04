# MORIARTY quotation fix — v0.1.1

Your saved OpenAI responses completed successfully. The evidence_ledger c1 response
failed all four exact-quote checks because it shortened quotations with ellipses and
changed punctuation. The persistent_history c1 response passed quote checks.

The updated interface supplies deterministic source spans to every arm. The model
selects span IDs from an enum; Python inserts the exact source text and saves offsets.
Unknown/future IDs still fail. The raw response, raw parsed selections, resolved
citations and canonical parsed output are retained. Existing invalid outputs are not
rewritten, repaired, or promoted to valid results. Semantic support still needs review.

## Install
Extract this ZIP INTO your existing Moriarty_Swarm_Lens folder, replacing moriarty.py.
The archive includes data/ai_village_case_v2.json and tests/test_span_citations.py.
Keep your existing other data, fixtures, tests and runs. This is a patch, not the initial
full installation. Copy the old moriarty.py to a backup if you want its exact source.

From the PowerShell terminal in that folder, with OPENAI_API_KEY already configured:

```powershell
py -m unittest discover -s tests -v
py moriarty.py run --case data/ai_village_case_v2.json --model gpt-4.1-mini --checkpoints 0 --out runs/v2_span_ids --execute
Start-Process runs/v2_span_ids/dashboard.html
```

This is 18 paid calls: 6 checkpoints x 3 arms x 1 repeat. Omit --execute to inspect the
plan without calls, then rerun the identical command with --execute. Do not append a
backslash to PowerShell command lines. Each command above is a complete line.

Your uploaded case_snapshot was v1. The explicit --case argument selects v2, whose
21-message sequence places separate checkpoints before/after the scoring claim,
challenge, admission, peer responses and replacement claim. Source statements remain
unaudited; no real hidden-goal accuracy is calculated.

The error 'Output belongs to another configuration' protects existing output when a
model/case/configuration differs from its plan. Use the new folder above, preserving
runs/pilot and runs/pilot2. Do not mix responses from different protocol versions.

## Verification and research status
17 offline checks passed (13 original + 4 span-citation checks). The two uploaded real
responses were revalidated; the four invalid quotations remain invalid. Zero new API
calls were made in the build workspace, so the updated live path still needs your run.

All three arms receive the same source texts and span catalog; the catalog adds input
tokens. Persistent histories retain canonical resolved quotations. The new API output
schema asks for evidence entries with span_id, hypothesis_id and relation. Saved
parsed outputs continue to expose source_id, quote, hypothesis_id and relation for
compatibility with the dashboard and evaluator. A quote existing in the source does
not establish that it supports the assigned hypothesis.

The valid uploaded response assigns 0.60 to native Gemini judgment partly using
Claude's own judging report. This appears to transfer evidence between different
agents. It warrants semantic review, but is not yet evidence of interpretive capture:
only one checkpoint was supplied and underlying score provenance lacks audited truth.
