# Release 1.0.0 checks

Six offline regression tests passed, including a complete mocked 24-call run and resume, changed-plan/request rejection, no future/gold leakage, recap without prior judgments, input validation, and preservation/stopping on invalid output. Mock answers are not experimental results and are not bundled as predictions.

The real label bundle was revalidated separately: 24 saved outputs, 144 exact visible evidence entries and 24 submitted review entries. No new paid calls were made. The public demo has 24 normalized probability distributions; its JavaScript passes syntax validation. Browser visual QA was unavailable in this environment.

New experiments use session-1.0.0, which enforces the six-entry evidence cap in the API schema. Historical files and request hashes remain unchanged. Version 1.0 provided aggregate results and a fictional example; version 1.1 adds the selected conversations. Request-level revalidation still requires the original saved run files.

## Source-visible replay update

The demo now includes both selected conversations, full saved observer rationales and exact evidence entries. New-message/all-visible filters, text/speaker search and quote-to-message highlighting are connected to checkpoint selection. The original pilot correctly shows three observer setups, with no invented recap trajectory.

The original run was revalidated: 18 answers and 108 quotes, in addition to the previously validated label run’s 24 answers and 144 quotes. Node checks verify all 12 case/checkpoint prefixes, new-message partitioning, filtering and all 252 source links. JavaScript syntax and HTML container nesting pass. Browser visual QA remains unavailable. No paid model calls were made.
