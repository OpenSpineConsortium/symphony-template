---
name: engine-swap-architecture
description: Demo/engine contract so the geometric measurement+compensation can later be swapped for an end-to-end trained neural net
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

The user wants to eventually **replace the geometric measurement + compensation/synthesis engine with an end-to-end trained neural net** -- without rewriting the viewer.

**Key enabler (already true):** the PACS demo viewer (`openspineconsortium.github.io/pacs/pacs.js`) is **decoupled** -- it consumes a precomputed **`metrics.json` contract** (`summary` PI/SS/PT/LL, `geometry` world-mm construction, `postop` {summary, geometry, plan}) + the `ct`/`seg` `.nii.gz`. It does NOT care whether those came from ostk geometry or a network.

**How to apply / build toward this:**
- Treat `metrics.json` (+ volumes) as the stable **interface**. Any backend that emits the same schema drops in.
- In `ostk`, put the pipeline behind a thin predictor interface, e.g. `predict(ct, label) -> {summary, geometry}` and `synthesize(ct, label, plan) -> {postop_ct, postop_seg, summary, geometry}`, with the current geometric code as the default backend and a future `nn` backend implementing the same signature.
- The NN targets are well-defined supervised labels: the geometric pipeline's measurements (PI/SS/PT/LL, endplate landmarks, femoral-head centres) are the **training labels** -- i.e. the current toolkit can **bootstrap/auto-label** the dataset for the NN.
- Keep the analytic carry-forward ([[postop-spine-synthesis]]) as the supervision/validation signal for a learned post-op generator too.
