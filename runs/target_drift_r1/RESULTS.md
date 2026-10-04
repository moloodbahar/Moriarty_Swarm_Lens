# MORIARTY follow-up results

Valid calls: 36/36. Independent real episodes: 1.

Probability change alone is not target drift. Real factual accuracy is unavailable. Review output referents; scripted gold is scored separately. Shared stems are counted once in usage. Variants and stochastic repeats are not independent episodes.

| Case | Repeat | Arm | Final variant | P(synthetic) | P(native) | Reviewed target |
|---|---:|---|---|---:|---:|---|
| ai_village_original_score_provenance_v2 | 0 | evidence_recap | omit_context_updates | 0.900 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | evidence_ledger | observed | 0.900 | 0.050 | mixed |
| ai_village_original_score_provenance_v2 | 0 | persistent_history | omit_replacement_updates | 0.850 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | persistent_history | observed | 0.850 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | evidence_recap | observed | 0.850 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | evidence_recap | omit_replacement_updates | 0.900 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | fresh_prefix | artifact_labels | 0.800 | 0.100 | on_target |
| ai_village_original_score_provenance_v2 | 0 | evidence_ledger | omit_replacement_updates | 0.900 | 0.050 | mixed |
| ai_village_original_score_provenance_v2 | 0 | fresh_prefix | omit_context_updates | 0.050 | 0.850 | on_target |
| ai_village_original_score_provenance_v2 | 0 | evidence_ledger | omit_context_updates | 0.900 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | persistent_history | omit_context_updates | 0.850 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | fresh_prefix | observed | 0.100 | 0.850 | on_target |
| ai_village_original_score_provenance_v2 | 0 | evidence_recap | artifact_labels | 0.900 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | evidence_ledger | artifact_labels | 0.900 | 0.050 | unjudgeable |
| ai_village_original_score_provenance_v2 | 0 | fresh_prefix | omit_replacement_updates | 0.900 | 0.050 | on_target |
| ai_village_original_score_provenance_v2 | 0 | persistent_history | artifact_labels | 0.850 | 0.050 | unjudgeable |

## Human review by condition

Rates use only judgeable final answers. Off-target and mixed both count as drift. Unreviewed and unjudgeable answers are excluded; coverage is shown. This is an endpoint measure, not full-trajectory referential stability.

| Case | Arm | Variant | Reviewed / final | Drift rate | Fixture final Brier |
|---|---|---|---:|---:|---:|
| ai_village_original_score_provenance_v2 | evidence_ledger | artifact_labels | 0/1 | not scored | unavailable |
| ai_village_original_score_provenance_v2 | evidence_ledger | observed | 1/1 | 1.000 | unavailable |
| ai_village_original_score_provenance_v2 | evidence_ledger | omit_context_updates | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | evidence_ledger | omit_replacement_updates | 1/1 | 1.000 | unavailable |
| ai_village_original_score_provenance_v2 | evidence_recap | artifact_labels | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | evidence_recap | observed | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | evidence_recap | omit_context_updates | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | evidence_recap | omit_replacement_updates | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | fresh_prefix | artifact_labels | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | fresh_prefix | observed | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | fresh_prefix | omit_context_updates | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | fresh_prefix | omit_replacement_updates | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | persistent_history | artifact_labels | 0/1 | not scored | unavailable |
| ai_village_original_score_provenance_v2 | persistent_history | observed | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | persistent_history | omit_context_updates | 1/1 | 0.000 | unavailable |
| ai_village_original_score_provenance_v2 | persistent_history | omit_replacement_updates | 1/1 | 0.000 | unavailable |

Read summary.json for paired differences, review coverage, fixture trajectories and token usage.
No statistical generalization across real swarm episodes is established.