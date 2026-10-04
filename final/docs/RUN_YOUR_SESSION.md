# Run the same test on your own session

Work inside `final/` in the GitHub repository, or the extracted final ZIP root. Python 3.10+, no installation step. Windows commands use `py`; replace it with `python3` elsewhere.

## 1. Make a message file

Use JSON Lines: one JSON object per line. Example:

```json
{"id":"m1","time":"2026-01-01T10:00:00Z","speaker":"Agent A","text":"I found an alert.","session_id":"room-1"}
```

Required: unique `id`, timestamp with timezone, speaker, text. A compatible AI Village row may instead use `created_at`, `agent_speaker_id`/`user_speaker_id`, `content`, `room_id`. `{ "row": {...}, "row_sha256": "..." }` export envelopes are accepted and their row checksums are verified. Multiple rooms require `--session ROOM_ID`. This adapter supports text chats; arbitrary screenshots or computer-use payloads need a separate adapter.

Null content is rejected instead of silently removed. Export a declared text session first. Missing timezone is rejected unless you explicitly use `--assume-utc`. This changes the timezone assumption, not the message text or event claims.

## 2. Copy the question template

Copy `examples/earthquake_question.json` to a new file and edit it:

- Give the case a unique ID.
- Set `kind` to `real_observational` and `gold_hypothesis` to `null` for real, unaudited data.
- Ask about one fixed target: e.g. which process produced file A0 at commit X. Do not let the question silently change to a replacement file.
- Define four distinct explanations, including “other process” if appropriate. Avoid vague or overlapping categories.
- Set six increasing `checkpoint_cutoffs`, counting messages **after room selection and chronological sorting**. The last cutoff must equal the selected message count. Choose stages for ambiguity, new evidence and follow-up; do not simply split by equal time.

With more than 900 citation spans, the current runner rejects the case before paid execution. Choose and document a smaller investigation window. It is not a system for sending millions of turns in one request.

## 3. Prepare and plan

```powershell
py prepare_session.py --input local_data/my_session.jsonl --spec local_data/my_question.json --out cases/my_case.json
py session.py run --case cases/my_case.json --model gpt-4.1-mini --out runs/my_case
```

Add `--session ROOM_ID` when selecting one room from a multi-room input. Preparation preserves text and uses posting times, with ID as the tie-breaker. The runner creates a 24-call plan and sends zero calls without `--execute`.

## 4. Execute locally

```powershell
$secureKey = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
py session.py run --case cases/my_case.json --model gpt-4.1-mini --out runs/my_case --execute
```

Keep commands on one line. Do not append a backslash in PowerShell. The key stays in your local process environment; do not commit it. Source messages are sent to the selected OpenAI model only when you execute.

Six checkpoints × four conditions × repeats = calls. A second repeat requires `--repeats 2 --max-calls 48` and a new output folder. Repeats on one episode measure sampling variation, not independent evidence across episodes.

## 5. Read and review

```powershell
Start-Process runs/my_case/review.html
```

The page shows the four final answers in shuffled order, their fixed question, probability distribution and evidence. “On target” means it addresses the named original object/event; “supported” means the sources justify its inference. These are different judgments. Select options, add notes, click **Download target_review.json**, then import the actual downloaded file:

```powershell
py session.py analyze --out runs/my_case --review "$HOME\Downloads\target_review.json"
```

The generic review covers final answers. `answers.json` contains every checkpoint. The separate historical label-case reviewer supports all 24 answers with its case-specific rubric:

```powershell
py review_label_case.py --out C:\path\to\label_run --review "$HOME\Downloads\label_review.json"
```

Use it only for the original label transfer run. It does not accept new `session.py` plans. Browser downloads do not automatically write into your dataset; the import command saves them there.

## Recheck the completed experiment

Extract your authorized `label_share_bundle.zip` to a folder and use the supplied review JSON:

```powershell
py verify_label_run.py --run C:\path\to\label_run --review C:\path\to\label_review.json --out results/revalidated_label.json
```

This reconstructs expected requests and verifies raw answers, citations and review IDs without API calls. It exports public numeric results. To rebuild the 98-message case from an authorized full episode audit:

```powershell
py prepare_label_case_v2.py --source C:\path\to\full_episode_audit.json --out cases/label_case_v2.json
```

A new run of that rebuilt case uses `session.py`, with a new versioned plan and the schema evidence cap. It will not be bit-for-bit the old experimental request series and should not overwrite the historical run.

## Errors and safe resume

- **Output belongs to another configuration:** choose a new output folder. The code is protecting an existing experiment.
- **Valid earlier calls replay when resuming:** they are read from disk, not billed again. Remaining missing calls are sent only with `--execute`.
- **Saved response is invalid:** the response remains saved and later calls stop. A repeated command will not fix it. Do not delete it to hide the failure. Inspect it and document any replacement run. The new runner addresses the earlier more-than-six-evidence-items schema mismatch, but other validation failures can still occur.
- **Network timeout:** the remote request may have run even if its answer was not received. No automatic retry occurs; a manual rerun can incur another charge.
- **Run lock exists:** confirm the earlier process is no longer running before removing the stale lock.

`RECOVERY.md` and `recover_label_run.py` retain the separate historical transfer recovery workflow. They are not a recovery tool for `session-1.0.0` folders.

## Recompute the external artifact check

This is separate from observer inference and makes no model calls. With Git installed, get the public artifact repository and audit a fixed commit:

```powershell
git clone https://github.com/ai-village-agents/research-2026-05.git local_data/research-2026-05
py audit_label_swap_v2.py --repo local_data/research-2026-05 --rev 2442b493c0b6eb2fcd3045c77bf5b463b29b31c5 --out results/artifact_audit.json
```

It matches packets and scores, checks exact label pairs and score ranges, and reports equality by source judge. Extra correlation diagnostics are descriptive: a change score shares its baseline mathematically, so a negative baseline/change correlation alone is not causal evidence. The full execution procedure remains unaudited.
