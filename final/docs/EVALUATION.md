# What would count as a real improvement?

Current question: does preserving previous interpretations help an AI investigator maintain the correct target and revise appropriately, or does it make early mistakes persist? Does checking alternatives help beyond ordinary history? Does repeating source evidence explain part of the difference?

Current evidence: a working, auditable experiment and exploratory failure cases. We cannot report a statistically established accuracy gain.

## Next confirmatory test

1. Freeze question-writing rules, prompts, checkpoint rules, model/version, failure handling and primary outcome before seeing model outputs on new episodes.
2. Select independent episodes with both corrections to an original claim and later replacements that must remain separate. Include successful revision cases, not just suspected failures. Record selection criteria and exclusions.
3. Improve the hypothesis definitions so alternatives are distinguishable. Use neutral IDs and balance option order across repeated runs to test label/order effects.
4. Have two reviewers independently assess inference support and target identity against the same visible evidence. Report agreement and adjudicate disagreements. Audit external artifacts/execution logs before assigning factual process labels.
5. Compare the four setups on matched episodes. A practical primary outcome is the proportion of reviewed answers with an unsupported process claim after a prespecified update. Target substitution can be a separate secondary outcome. Report abstentions, missing answers, failures and review coverage.
6. Average repeats/checkpoints within each episode as prespecified, then compute paired differences and a bootstrap confidence interval resampling **episodes**. Do not treat 24 dependent answers from one episode as 24 independent cases. Choose the number of episodes with a power/precision plan, not a made-up significance target.
7. If factual labels really exist, report Brier score and accuracy separately. Low entropy, low disagreement or stable probabilities are not substitutes for correctness.

A real gain would look like: across independent audited episodes, the intervention reduces unsupported inferences or target substitution, with uncertainty bounds that support a useful reduction and acceptable cost/failure rates. That is a proposed criterion, not a result we have already obtained.

Useful engineering improvements: explicit artifact IDs and versions; a structured evidence table distinguishing claim, observation and inference; links between original claims and copied claims; execution-log retrieval tied to file hashes; better abstention when alternatives are observationally indistinguishable; token-matched controls. Each needs its own evaluation.
