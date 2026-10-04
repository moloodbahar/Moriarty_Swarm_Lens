# MORIARTY Swarm Lens

**Can an AI investigator follow a changing agent conversation without confusing reports, proof, and later replacements?**

MORIARTY Swarm Lens lets us check. It shows the same conversation to one AI model in four different ways, pauses at six points, and compares its answers. Every evidence quote points back to a message it was allowed to see.

**[Open the interactive demo](https://moriarty-swarm-lens.melody21.chatgpt.site) · [Results](final/docs/RESULTS.md) · [Run your own session](final/docs/RUN_YOUR_SESSION.md)**

The demo replays two completed case questions from one research episode. It does not send API requests or ask for a key.

## What is an AI swarm?

Here, it means a group of AI agents working and communicating together: sharing information, handing off tasks, making files and changing plans. A swarm does not necessarily have one shared mind or one agreed goal.

Reading thousands of their messages is difficult. Worse, several agents repeating a claim can make it look independently confirmed when they are all repeating the same source. Our tool helps an investigator check how an AI reader interprets that record.

## An everyday example

Imagine an emergency team sharing an earthquake alert. Later, someone discovers that the **original alert** came from an old drill. Then a **new, real earthquake** happens.

If we ask “Where did the original alert come from?”, the later earthquake does not change the answer. A reader must keep the two alerts separate.

Our experiment asks whether an AI reader does that, whether remembering its earlier answers helps or hurts, and whether checking alternative explanations helps. This earthquake example is fictional; our measured results come from AI Village research conversations.

## What did we actually discover?

### Earlier case: synthetic scores and a reported cleanup

Gemini acknowledged producing heuristic and randomized research scores. It then reported deleting and replacing them. Between those reports, peers described synthetic rows as still awaiting replacement and discussed provisional analyses containing Gemini rows.

**We could see the claims, but had not independently established that the cleanup was completed.** Different messages may refer to different local copies, stages or artifacts. We did not prove that synthetic rows remained, that removal succeeded, or that anyone was deceptive.

The original observer question was about **how the original batch was made**. After replacement updates, the fresh reader changed from **85% synthetic at c5 to 85% native at c6**, using the later replacement to explain the original batch. History and ledger retained **90% synthetic**. Some of their wording also accepts replacement reports as facts; preserving the original answer does not verify the replacement.

The demo now shows this original **three-setup, 18-answer pilot** alongside the later **four-setup, 24-answer label case**. Source recap was added later; no recap result is invented for the original pilot. Both cases belong to the same May research episode.

At every checkpoint you can read the **actual selected messages**, switch between new messages and the whole visible prefix, search speakers/text, and open each observer’s rationale. Click a quotation to highlight it in its source message.

### Later case: equal scores, different process explanations

In our final case, agents discussed scores that stayed exactly the same after labels were swapped. We asked **how those scores were produced**, not merely whether they were equal.

The same observer model, given the same available source messages, finished with different preferred explanations:

| Observer setup | Preferred explanation at the end | Reported probability |
|---|---|---:|
| Fresh reader | Both label conditions scored together, with pairwise consistency | 80% |
| Reader with answer history | Separate scoring of each displayed item | 86% |
| Reader with history + alternative checks | Both label conditions scored together, with pairwise consistency | 80% |
| Reader with repeated source reminders | Score each unique response once, then reuse it | 75% |

These are **model-reported probabilities, not measured chances of being correct**.

We checked all **24 saved answers** and **144 evidence entries**. Their quotes match the visible messages. In the submitted review, **23 of 24 answers were marked as claiming more about the scoring process than the evidence established**. That is one review pass on one episode, not an independently measured 96% error rate across swarms.

A separate audit of public score files confirmed **40 of 40 paired responses had identical five-part scores**. That establishes equality. It does **not** establish whether scores were independently produced, reused, or made consistent in a shared context.

**The useful result: correct quotations and confident explanations are not enough to establish how a swarm did something.** The tool makes that gap visible and reviewable. We have not shown that the evidence-ledger condition improves accuracy.

## Why four observers?

They are **four setups of the same model**, not four different models and not the original agents in the swarm. All four see every selected source message up to the current checkpoint.

| Setup / code name | What extra information it gets | What it tests |
|---|---|---|
| Fresh reader / `fresh_prefix` | No earlier answers | What does the current evidence suggest on its own? |
| Answer history / `persistent_history` | Its own previous structured answers | Does remembering an interpretation preserve the target, or make it stick to an early mistake? |
| Alternative checks / `evidence_ledger` | Previous answers plus instructions to compare alternatives, look for contradictions and name missing evidence | Does a more careful checking instruction improve revision? |
| Source reminders / `evidence_recap` | One exact source message from each earlier checkpoint boundary; no earlier answers | Is a difference associated with remembering interpretations, or simply seeing old evidence again? |

“Evidence ledger” is the historical condition name. In this implementation it is a **prompt instruction plus answer history**, not a separate verified evidence database. The setups have different input lengths; this is not a token-matched experiment. The recap is a useful control, not a complete removal of all confounds.

## From dataset to result

1. **Get an authorized chat export.** We used [AI Village on Hugging Face](https://huggingface.co/datasets/aidigestorg/ai-village).
2. **Choose one session and a fixed question.** Name the exact artifact, action or claim being investigated. Write four possible explanations.
3. **Keep the messages in posting order.** Preserve speaker, message ID and original text. A message about yesterday is still posted today; do not silently rewrite its time.
4. **Choose six stopping points.** At each point, the observer can see only messages already posted. Later messages and any evaluation label are excluded.
5. **Run the four setups.** Six checkpoints × four setups = 24 calls for one repeat.
6. **Check the saved answers.** Validate probabilities, allowed evidence spans and request hashes. Save invalid responses and stop; never quietly repair an answer.
7. **Review what the evidence actually supports.** Check target identity, alternative explanations and unsupported process claims. Exact-quote validation alone cannot do this.
8. **Audit external artifacts separately.** Compare files and commits where available. Keep this information out of the original observer inputs.
9. **Report trajectories, disagreements and limitations.** Do not turn confidence or repeated messages into factual accuracy.

[Dataset fields and exact case selection](final/docs/DATA_AND_METHOD.md) · [What we built over the project](final/docs/PROJECT_HISTORY.md)

## Run it

Python 3.10 or newer; no packages to install. On Windows use `py`. On macOS/Linux use `python3`.

If you downloaded the whole GitHub repository, enter its `final` folder first. If you downloaded the final ZIP, open a terminal in the extracted folder containing this README.

```powershell
# Only for a checkout of the full GitHub repository:
cd final

# Offline tests: no API key and no model calls.
py -m unittest discover -s tests -v

# Prepare the clearly fictional earthquake example.
py prepare_session.py --input examples/earthquake_session.jsonl --spec examples/earthquake_question.json --out cases/earthquake.json

# Plan 24 calls without sending any.
py session.py run --case cases/earthquake.json --model gpt-4.1-mini --out runs/earthquake
```

To send those requests, enter an OpenAI key **locally**, then add `--execute`. An HF token is not an OpenAI key and is not needed for a prepared case.

```powershell
$secureKey = Read-Host "OpenAI API key" -AsSecureString
$env:OPENAI_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
py session.py run --case cases/earthquake.json --model gpt-4.1-mini --out runs/earthquake --execute
Start-Process runs/earthquake/review.html
```

This is a paid API run. The completed pilot used `gpt-4.1-mini-2025-04-14`; the command uses its requested model alias. Your account must support the selected model and structured outputs. The example has **no stored model predictions**; its text is not real experimental evidence.

Outputs include `plan.json`, saved requests/responses, `answers.json` for every checkpoint, `summary.json`, `RESULTS.md`, and `review.html`. In that HTML page, review the four final answers, select judgments, add notes, and download `target_review.json`. Import it with:

```powershell
py session.py analyze --out runs/earthquake --review "$HOME\Downloads\target_review.json"
```

This updates the local reviewed dataset and results without new model calls. It does not alter source messages. [Full instructions, input format and troubleshooting](final/docs/RUN_YOUR_SESSION.md).

For the already completed label case, `verify_label_run.py` rechecks the original run and the submitted 24-answer review. It requires your authorized raw bundle; the public demo includes the selected conversations and saved answers; original request/response verification still requires the authorized raw run bundle.

## What is our contribution?

A small, reproducible **test bench for AI swarm investigators**:

- Keep one historical question fixed while a conversation evolves.
- Compare remembering prior answers with repeating prior source evidence.
- Trace each citation to an exact, already-visible message.
- Separate source correctness, inference quality and external artifact checks.
- Show the observer's proposed next observation, so an investigator can ask for the missing execution record instead of guessing.

We are not claiming to have invented memory experiments or evidence citations. We are not reproducing a complete published MORIARTY benchmark. Our contribution is this inspectable combination, adapted to real multi-agent traces, and the documented failure cases it exposed.

## What has not been solved?

We have not recovered hidden agent beliefs or proven why the swarm acted. We have not measured collective convergence inside the swarm. We have not demonstrated a statistically reliable accuracy gain from any observer setup. The final score-generation process still needs sufficiently complete execution/model-call records.

To measure a real gain, freeze the protocol, use independently selected episodes, obtain evidence-based labels from two reviewers, and compare paired error rates by **episode**. Repeated checkpoints are not independent examples. [Evaluation plan](final/docs/EVALUATION.md).

## Where to look

| File | Purpose |
|---|---|
| `demo/index.html` | Two-case replay with actual conversations, observer answers and clickable source quotes |
| `results/label_results_public.json` | Validated public numeric results and citation source IDs |
| `docs/RESULTS.md` | Findings, review counts and limits |
| `docs/DATA_AND_METHOD.md` | Data names, row counts, columns, provenance and workflow |
| `docs/PROJECT_HISTORY.md` | Earlier extractor, original-score and outreach work |
| `docs/EVALUATION.md` | What would count as a real improvement |
| `docs/DEMO_SCRIPT.md` | A short presentation walkthrough |
| `SUBMISSION.md` | Text ready to paste into the submission |
| `prepare_session.py`, `session.py` | Prepare and run a new compatible text session |
| `verify_label_run.py` | Revalidate the completed historical label run |
| `moriarty.py`, `followup.py`, `transfer.py` | Frozen historical machinery; retained for provenance |

Start new experiments with `session.py`. It enforces the six-evidence-entry limit in the API schema from the first request. It does not change or relabel the historical experiment. Reusing a folder with a different configuration is rejected.
