# MORIARTY Swarm Lens

Repository: https://github.com/moloodbahar/Moriarty_Swarm_Lens

Demo: https://moriarty-swarm-lens.melody21.chatgpt.site

Code for the final release: https://github.com/moloodbahar/Moriarty_Swarm_Lens/tree/master/final

We built a test bench for AI investigators reading multi-agent conversations. It keeps one question fixed, reveals the transcript chronologically, and compares four setups of the same model: fresh reading, previous-answer history, history plus alternative checks, and repeated source evidence without previous answers.

The final demonstration uses 98 AI Village messages, six checkpoints and 24 saved GPT-4.1-mini answers. All 144 formal evidence entries match their permitted source messages. However, a submitted review marks 23 of the 24 answers as making an unsupported process inference. The setups end with different preferred explanations for the same score batch. A separate public-file audit confirms identical paired scores, but does not identify how they were generated.

Our contribution is a reproducible way to inspect belief revision, target confusion and the gap between a valid citation and a justified inference. The demo exposes the actual probability trajectories and review counts. The repository includes a plain-language guide and a text-session adapter for running the same protocol elsewhere.

This is an exploratory result, not a benchmark win. The final case is one episode, the review has one pass, and the hypotheses partly overlap. We have not demonstrated that the evidence ledger improves accuracy or that the swarm itself converged on a hidden shared belief.
