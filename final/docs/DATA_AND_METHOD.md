# Data and method, from input to output

## Inputs actually used

Dataset: **aidigestorg/ai-village** — https://huggingface.co/datasets/aidigestorg/ai-village

Pinned export revision: `838b4150303ca8228e8edb432d8b8ccae353d258`.

The counts below are our local exported snapshot, not a claim about the current live dataset size.

| Table | Local rows | Subject | Fields used |
|---|---:|---|---|
| chat_messages | 183,485 | Messages between agents and users | id, agent_speaker_id, user_speaker_id, speaker_type, content, room_id, created_at |
| agents | 46 | Agent identities and metadata | id, name; model_string is available metadata |
| chat_rooms | 16 | Conversation rooms | id, name |

Full observed chat-message columns: `id`, `agent_speaker_id`, `user_speaker_id`, `speaker_type`, `content`, `room_id`, `created_at`, `updated_at`, `has_been_approved`.

Full observed agent columns: `id`, `name`, `emoji`, `status_message`, `model_string`, `is_pending`, `is_updating_memory`, `input_tokens_used`, `output_tokens_used`, `last_seen_event_index`, `money`, `paused_until`, `paused_until_task_id`, `current_computer_use_session_id`, `village_id`, `created_at`, `updated_at`, `goal`, `is_participating`, `current_human_use_session_request_id`, `is_paused_for_google_sign_in`, `current_room_id`.

Full observed room columns: `id`, `name`, `village_id`, `created_at`, `updated_at`, `last_nudger_run_at`, `last_nudger_run_chat_message_id`, `deleted_at`, `whitelisted_agent_names`, `blacklisted_agent_names`.

Export envelopes have `source`, `row_sha256` and `row`. We preserve available provenance. Most identity/accounting metadata is not given to the observers. An agent's goal field is not an independently measured belief state.

Why this dataset: it contains multi-agent conversations with identifiable speakers, timestamps, handoffs and public artifacts that can sometimes be checked. We do not analyze all 183,485 messages with the model. We do not claim to have analyzed the advertised millions of computer-use turns.

Other source considered: [SwarmTraces](https://swarmtraces.org/). No completed SwarmTraces experiment is part of these reported results. The German forum and Transluce logs are also not evaluated here. Listing a dataset is not evidence of transfer performance.

## Case selection

| Case | Messages shown at final checkpoint | Distinct episode | Use |
|---|---:|---|---|
| Original-score provenance v2 | 21 | May research episode | Original pilot and target-drift follow-up |
| Outreach destination | 80 | July 8 outreach episode | Different-topic transfer check |
| GPT label-swap provenance v2 | 98 | Same May episode as the original-score case | Final demo and supplied review |

The May room audit preserves 458 messages. The final demo uses two contiguous windows in room `d45ec7c6-6adb-49cb-8c40-dc5d18c37d84`: May 13, 2026, 20:41–21:01 and May 14, 17:00–20:51, in the export's timestamp convention. There is no keyword filtering inside those windows. Six prefix ends: 14, 16, 31, 47, 79, 98. Cases and checkpoints were selected after source inspection. They are development cases, not a pristine held-out benchmark.

Record checksum: `80d621c55f34514be573bb002fefd0819e60136ed55f825d494bfc089aa0caca`.

## Variables

**Inputs:** posted message time, speaker, original text, source ID, fixed target/question, four candidate explanations, checkpoint boundary, observer condition, model, repeat and seed.

**Outputs per checkpoint:** four probabilities summing to one; short rationale; up to six exact evidence spans; unresolved questions; proposed next observation.

**Derived descriptive measures:** leading explanation, confidence movement, normalized entropy, Jensen–Shannon change between consecutive distributions. Large movement means the answer changed, not that it improved.

**Review variables:** whether the answer stays on the fixed target; whether cited sources support the inference; for the label case, alternatives acknowledged, process overclaim and rationale/probability consistency.

**Missing gold variable:** independently audited generation process. It is deliberately absent rather than guessed.

## Safeguards and limits

Visible inputs are built with a whitelist. Evaluation labels, future records and external audit metadata are excluded. Hypothesis order is shuffled per repeat but matched across conditions. Each condition has its own previous answers. The recap repeats source messages, not prior interpretations. No web browsing or transcript instructions are executed by the observer runner.

Exact quotations are resolved by the code from selected span IDs. Invalid probabilities, unavailable/future spans and too many evidence items stop the run. The public release's new runner enforces a maximum of six evidence items in the API schema as well. It does not rewrite historical requests.

Posting order is an evidence-availability order, not a full timeline of real-world actions. A first-line recap, future plan or claimed completion remains a statement until separately checked. Human-written targets and hypotheses can themselves introduce framing errors. The label-case hypotheses are not perfectly mutually exclusive.

The updated public replay includes the selected 21-message and 98-message case conversations, saved observer answers, exact quotes and numeric trajectories. It does not include the full 183,485-message export or computer-use logs. Request-level verification from scratch still requires the original saved run files. The public earthquake fixture is an illustration and plumbing example, not evidence of real-swarm performance.

## Original APIs supplied for discovery

- https://datasets-server.huggingface.co/splits?dataset=aidigestorg%2Fai-village
- https://datasets-server.huggingface.co/rows?dataset=aidigestorg%2Fai-village&config=agent_goals&split=train&offset=0&length=100
- https://huggingface.co/api/datasets/aidigestorg/ai-village/parquet/agent_goals/train

The `agent_goals` endpoint was part of initial access/discovery; its rows are not the 98-message experimental input. Access and table availability depend on the authorized account. Do not use an HF token as an OpenAI inference key.
