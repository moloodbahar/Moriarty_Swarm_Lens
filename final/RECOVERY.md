# Recover the stopped label_v2 pilot

This add-on fixes the evidence-array schema mismatch for the remaining calls and preserves the validated prefix. It adds files; it does not replace moriarty.py, followup.py, transfer.py, or review_label_case.py, whose hashes are part of the original protocol.

## Why it stopped

The prompt and local validator require at most six evidence entries. The original request schema did not enforce this maximum. An otherwise well-formed API response can therefore exceed six entries and fail local validation. The existing runner saves that failure and deliberately refuses to put it into history. Repeating --execute encounters that same saved response.

The reported checkpoint and job ID match our frozen plan: fresh_prefix c4, job 774cd3aebd9bb43cf0b01e4b. We have not received your raw failure file; the prepare command below reads it, verifies its request hash, and prints the actual validation error. It does not assume the pasted diagnosis is correct.

## Install and prepare (no API calls)

Extract this patch into your current Moriarty_Swarm_Lens project, alongside transfer.py. Keep your original runs/label_v2 folder.

From PowerShell in that project:

```powershell
py -m unittest discover -s tests -p test_recovery.py -v
py recover_label_run.py prepare --from-run runs/label_v2 --out runs/label_v2_recovered
```

Expected: 14 valid responses reused, one invalid response archived, 10 requests remain, zero API calls. It creates a new sibling folder and leaves the original run untouched. If preparation already succeeded, skip it and use resume. Do not delete either run to repeat preparation.

## Continue the remaining calls

Optional dry run:

```powershell
py recover_label_run.py resume --out runs/label_v2_recovered
```

With OPENAI_API_KEY still set locally in your terminal:

```powershell
py recover_label_run.py resume --out runs/label_v2_recovered --execute
```

The first 14 entries say `reused`; they do not call the API. The remaining 10 requests enforce `text.format.schema.properties.evidence.maxItems = 6`. Questions, evidence, hypothesis order, model, token cap, and prior accepted judgments are unchanged. Newly generated answers must still pass citation, probability, completion and refusal checks. Scores and evidence are never silently trimmed or normalized.

If your key is no longer set, enter it locally before execution:

```powershell
$secureKey = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
```

No backslashes at line endings. No Hugging Face token is needed. API execution incurs your normal API usage costs. Do not run two processes in the same output folder.

## Review and share

Successful completion automatically produces label_results.json, label_review.html, and label_share_bundle.zip. Open the review page:

```powershell
Start-Process .\runs\label_v2_recovered\label_review.html
```

Download label_review.json from that page, copy it to the project folder, and import it using the recovery-aware analyzer:

```powershell
py recover_label_run.py analyze --out runs/label_v2_recovered --review label_review.json
```

Use recover_label_run.py for this recovered folder. The older transfer.py and review_label_case.py analyzers do not understand its changed request hashes. Share **runs/label_v2_recovered/label_share_bundle.zip**. It includes the original plan, recovery policy, unchanged reused responses, archived original failure, and every new attempt.

## If a new call fails

The program prints the specific error and preserves the request plus raw response under attempts/JOB_ID/0001.json. The failure never enters observer history. Refusals, incomplete responses, bad citations, bad probabilities, network failures, or other errors can still occur; a length constraint does not fix all possible failures.

There are no automatic retries. After inspecting and resolving a new failure, explicitly authorize one further attempt at that checkpoint:

```powershell
py recover_label_run.py resume --out runs/label_v2_recovered --execute --retry-failed
```

A timeout can have an uncertain billing outcome. The attempt log records it, and the next invocation requires this explicit retry flag. A completed run makes zero new calls when resumed. A valid saved response is revalidated before reuse; tampering does not trigger a paid replacement automatically.

## Research interpretation

This is an exploratory recovered run: 14 original-schema answers plus up to 10 accepted answers generated with schema-level enforcement of the existing six-evidence instruction. The schema change may affect generation and the original invalid output was selected out by a validation rule. These facts are recorded in recovery_plan.json and label_results.json. Do not present this as a fresh 24-call experiment under one unchanged schema, or omit failure rates. A later confirmatory experiment should apply the same fixed schema to all arms from its first call.

The official Structured Outputs documentation lists maxItems as a supported array constraint for supported non-fine-tuned models: https://developers.openai.com/api/docs/guides/structured-outputs . This recovery is intended for your gpt-4.1-mini run.

## Validation performed

Six offline recovery tests pass. They reproduce a 14-valid/one-invalid prefix, confirm exactly 10 additional mocked calls, verify original files remain unchanged, enforce explicit retries, reject tampered saved records, preserve archived failures, and confirm the only changed request field is maxItems=6. No live API call was made while building this patch.
