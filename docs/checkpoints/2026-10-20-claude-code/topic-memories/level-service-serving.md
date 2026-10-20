---
name: level-service-serving
description: "STANDING RULE (2026-09-14) - the OSC website must never serve model weights; inference runs behind the level service (service/ in spinesurg-ct-nnunet), weights in the private HF repo gregoryschwingmdphd/level-id-weights; hosting not yet chosen"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-14T11:20:03.819Z
---

User directive 2026-09-14: "keep the most robust latest model on the OSC website after optimizing it for
low latency consumer performance, continually just make sure the weights aren't downloadable."

- Until 2026-09-14 the site shipped the detector as ONNX (`pacs/models/*.onnx`, 121 MB) + vendored
  onnxruntime; anything a browser loads is downloadable, so those files were removed from the site
  (commit 5559d87 on OpenSpineConsortium/openspineconsortium.github.io). History REWRITTEN with git-filter-repo on
  2026-09-14 (user's OK) and force-pushed (new head ea0086c); zero onnx/ort paths remain in any ref.
  GitHub still served the old blob by commit SHA right after the push (cached, unreachable objects);
  a GitHub Support request to purge is the remaining step.
- The page (`pacs/xr.js` + `pacs/remote.js`) now calls a level service: `GET /health`, `POST /infer`
  (multipart image, conf, imgsz) -> boxes, corners, level names (`level_run` from the contiguous-run
  decode, `level` from the BiGRU labeller, `top3`). Endpoint = `?service=URL`, then localStorage
  `levelIdService`, then `SERVICE_DEFAULT` (https://level-id.openspineconsortium.org, NOT yet live).
- Service code: `spinesurg-ct-nnunet/service/` (FastAPI, `model_defs.py` self-contained; Dockerfile CPU
  torch 2.6). Weights: PRIVATE `gregoryschwingmdphd/level-id-weights` (detector.pt = detect_v5z ep25,
  level_model.pt = M19 all2 aug2 rung1, recurrent_head.pt, registry.json with sha256). Release script
  `tools/deploy_service.py` refuses a public weights repo. Org repo `OpenSpineConsortium/level-id-weights`
  also exists (private, empty).
- `service/modal_app.py`: one-command Modal deploy (L4, scale-to-zero, secret hf-read).
- Hosting: Hugging Face Docker Spaces return 402 for BOTH the org and the personal account (free tier no
  longer allows Docker/Gradio Spaces). Options for the user: HF PRO/Team, Modal (scale-to-zero, GPU),
  Fly.io, EC2/Lambda with the AWS keys the user holds, or a workstation behind a Cloudflare tunnel.
- Measured on the grid login node (8 old CPUs): 1.6-2.3 s per 2048-px film end to end, ~0.9 s fixed
  overhead; V100: detector 23 ms + 2.3 ms/crop. A CPU host is not faster than the old in-browser WebGPU
  path; a GPU host is.

**How to apply:** never add model files to the website repo or any public repo; ship models only by
updating the private weights repo via `tools/deploy_service.py`; when hosting is chosen set
`SERVICE_DEFAULT` in `pacs/remote.js`. Related: [[fluorocap-repo-private]], [[commercialization-stance]],
[[pacs-website-latency-root-cause]].
