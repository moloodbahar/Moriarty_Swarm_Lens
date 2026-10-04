# MORIARTY Swarm Lens — hackathon development experiment v0.1

**Question:** Does retaining an early interpretation of another agent's behavior
make an observer less responsive to later diagnostic evidence? Does explicitly
checking alternatives and contradictions improve revision?

This package contains executable research infrastructure and actual source data
preparation. **It does not contain completed model experiment results.** No API key
was available in the build workspace. Offline unit tests use mock responses; those
responses are never shipped as experimental predictions.

Python 3.10 or later. Python 3.13 on Windows is supported. No `pip install` needed.
Unzip this package into a NEW folder. It does not replace `semantic.py` or the earlier
extractor. Commands below are PowerShell commands run inside this package folder.

## 1. Check the inputs and code — no API calls

```powershell
py -m unittest discover -s tests -v
py moriarty.py inspect
```

Bundled development case: the actual AI Village research-score provenance discussion.
458 room messages are retained in `data/full_episode_audit.json`. The declared prompt
subset includes all May 13 17:20–21:01 room messages plus the May 11 explicit mock-data
disclosure: **123 records**, five chronological checkpoints. No keyword filtering occurs
inside that window. The source-room choice, bounds, candidate hypotheses and checkpoints
were selected after inspection; this is not an unseen or prospective experiment.

To rebuild from your own authorized local export:

```powershell
py prepare_case.py --messages "C:\path\chat_messages.jsonl" --agents "C:\path\agents.jsonl" --out data
```

Both plain rows and `{source, row_sha256, row}` wrapped rows are supported, as are `.gz`
files. Raw content is preserved; source statements are not automatically verified facts.

## 2. Plan the smallest real-data pilot — still no API calls

Choose an exact OpenAI model ID available in your account. This code calls the Responses
API with strict structured outputs; the selected model must support that format.
The model ID is an explicit parameter: no unverified model availability is assumed.

```powershell
$env:MORIARTY_MODEL = "YOUR_EXACT_MODEL_ID"
py moriarty.py run --model $env:MORIARTY_MODEL --checkpoints 2 --out runs/pilot
```

This writes a **six-call plan**: three conditions × the first two checkpoints × one
repeat. `plan.json` contains model-visible evidence and selected job metadata, not model
answers. The first two prefixes contain 3 and 6 messages. The later prefixes contain
21, 113 and 123 messages. Their different sizes affect input cost.

## 3. Run those six calls

Set `OPENAI_API_KEY` locally. An HF token is unnecessary for the bundled case and cannot
authenticate model inference. Do not paste either token into chat, source files, or git.
This prompt masks the value while typing (it is still held in the process environment).

```powershell
$secureKey = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
py moriarty.py run --model $env:MORIARTY_MODEL --checkpoints 2 --out runs/pilot --execute
Start-Process runs/pilot/dashboard.html
```

`--execute` sends paid requests. Without it, nothing is sent. A strict call count is
declared in the plan; no automatic retries occur. Inspect usage in `metrics.json`.
The code has no price table and does not claim dollar estimates.

On a network failure, the outcome of that request may be uncertain. Earlier completed
outputs survive; rerunning the identical command resumes at the missing job. An invalid
response is preserved and stops its trajectory. Use a new output folder after changing
model, case, repeats, seed, checkpoint count or output cap. Do not delete failed responses
to selectively rerun outcomes: record failures and any replacement run explicitly.

## 4. Run the full five-stage development experiment

Once the small pilot produces valid JSON:

```powershell
py moriarty.py run --model $env:MORIARTY_MODEL --checkpoints 0 --out runs/full --execute
Start-Process runs/full/dashboard.html
```

`--checkpoints 0` selects all five checkpoints: **15 calls** for one repeat. For three
repeats, add `--repeats 3` and use a new folder (45 calls). Repeats on this one episode
are stochastic variability measurements, not 45 independent swarm cases.

## 5. Review the answers

In `dashboard.html`, inspect each probability distribution, rationale, exact quotes,
and its expandable visible-source panel. Select evidence support and confidence labels.
Click **Download review.json**. Then use the ACTUAL downloaded path, for example:

```powershell
py moriarty.py review --out runs/full --file "$HOME\Downloads\review.json"
```

This creates `reviewed_dataset.json` and `review_summary.json`. It never edits source
messages. Unreviewed entries remain unreviewed. Your review evaluates evidence support;
it does not turn inferred private intent into ground truth. The page requires no server.

To regenerate metrics/dashboard from saved responses without more calls:

```powershell
py moriarty.py evaluate --out runs/full
```

## What is compared?

| Condition | Visible evidence | Memory | Additional instruction |
|---|---|---|---|
| fresh_prefix | Complete selected prefix | None | Ordinary interpretation |
| persistent_history | Same prefix | Own earlier structured judgments | Ordinary interpretation |
| evidence_ledger | Same prefix | Own earlier structured judgments | Check all alternatives, contradictions and independent support |

All conditions use the same model, schema and output cap. Candidate order is randomly
permuted per repeat and shared across its conditions. Arm call order is randomized at
each checkpoint; checkpoints remain chronological to preserve memory dependencies.

Persistent history is operationalized as earlier structured judgments, **not** hidden
reasoning or complete provider conversation state. Earlier raw prefixes are not duplicated;
the current complete prefix contains that evidence. History and the intervention add input
tokens. Thus this is an evidence-matched comparison, not an equal-total-token-budget test.
This departure from full conversational persistence must be reported.

## Which outcomes are valid?

**Real case:** four hypotheses concern the generation process of the ORIGINAL score
batch. Later replacement methods are different artifacts. A self-report strongly changes
the evidential balance but does not independently prove what the script executed. The
file/commit hash is not yet audited. Consequently the real case has **no gold label**.
The program reports probabilities, entropy, successive Jensen–Shannon divergence and
dominant-hypothesis changes. It does not report real hidden-goal accuracy, wrong-capture
rates or recovery time. Confidence and JS alone do not establish correct revision.

**Controlled fixtures:** `data/fixtures/*.json` contains four scripted six-step examples,
one for each assigned goal. They allow plumbing/metric checks with known labels. To run
a model smoke experiment on one fixture:

```powershell
py moriarty.py run --case data/fixtures/valid_measurement.json --model $env:MORIARTY_MODEL --checkpoints 0 --out runs/fixture --execute
```

Fixture accuracy and capture metrics are labeled as fixture results. They do not establish
real-swarm performance, robust goal inference, or reproduction of the full original
MORIARTY author-generation and validation protocol. They have no LeakageJudge, reachability
gates, or independent narrative validation. Do not pool them with real-case results.

The `.8` concentration threshold is an exploratory choice, configurable with `--threshold`.
Probabilities are explicit model reports; **not** token log-probabilities or calibrated
posteriors. For labeled fixtures, q is true-goal probability, W is maximum wrong-goal
probability, H is normalized entropy, Brier is the unnormalized multiclass sum-squared
error (range 0–2), and recovery lag counts checkpoints from the declared diagnostic stage
until q reaches the threshold. Ties at the top are not counted as wrong dominance.

## What would establish a real gain?

Freeze this development protocol before using independent unseen episodes. Audit artifacts
and define fixed propositions or externally assigned goals; do not label intent by intuition.
Use independent human adjudication for semantic support and diagnostic evidence. Compare
complete matched trajectories, reporting failures and abstentions. For multiple independent
episodes, calculate paired per-episode differences and bootstrap confidence intervals by
episode; average stochastic repeats within each episode first. Avoid message-level or
repeat-level pseudoreplication. Predeclare primary outcome and threshold, and include cases
where peers revise successfully as well as cases suspected of persistence.

Until then, a dashboard showing revision is a feasibility demonstration, not a statistical
claim that the evidence ledger improves oversight.

## Files and provenance

- `moriarty.py`: planner, API runner, validation, trajectory metrics, HTML review and import.
- `prepare_case.py`: reproduces source selection from your export.
- `make_fixtures.py`: rebuilds transparent controlled fixtures.
- `tests/test_moriarty.py`: integrity, prefix blindness, quote validation, history, failures and metrics.
- `results/data_profile.json`: actual source-preparation counts, zero model calls.
- `results/offline_checks.json`: completed verification; not model results.
- `results/real_plan/plan.json`: generated full real-case plan; not executed.

AI Village source: https://huggingface.co/datasets/aidigestorg/ai-village

Pinned wrapped export revision: `838b4150303ca8228e8edb432d8b8ccae353d258`.
The raw subset preserves per-row source metadata and checksums where provided. All prefix
records are hashed; an edited case with stale checksum is rejected. Future records and
gold labels are excluded from API inputs by a whitelist. Case IDs in local output folders
are not sent as hidden-goal clues. Exact quote validation checks existence, not entailment.

**Data rights:** this is a private research bundle for the authorized dataset user.
Do not publish bundled AI Village messages without checking permission and dataset terms.
The code can be added to your hackathon repository independently of the data.

Optional future SwarmTraces adapter: https://swarmtraces.org/ and https://swarmtraces.org/viewer/
Its current structured timestamp field is empty. Reconstructed parent links must not be
treated as chronological transmission or separate independent episodes. The present code
does not claim to implement that adapter.

API reference checked during implementation:
https://developers.openai.com/api/reference/cli/resources/responses/methods/create
