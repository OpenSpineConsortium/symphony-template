---
name: pacs-website-latency-root-cause
description: "PACS X-ray demo went 40,018 ms -> 1,360 ms; root cause was the http redirect on the custom domain, then COEP vs CDN, then input size -- measure with pacs/measure_live.py"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-13T02:51:52.592Z
---

Fixed 2026-09-12 in openspineconsortium.github.io (commits 4955e46, 1446389, e1d2fde, 45ae8f1).

The chain: `openspineconsortium.github.io/pacs/` 301s to **http://**openspineconsortium.com
(Enforce HTTPS is off on the custom domain). On http `navigator.gpu` is undefined and service
workers cannot register, so WebGPU never starts and `coi-serviceworker` never grants threads ->
single-threaded WASM, 40 s. Forcing https from the page fixed both, then COEP refused the
jsdelivr CDN (a Worker can't be built from a cross-origin script) -> onnxruntime-web vendored
under `pacs/ort/`; the import must be `./ort/` (a bare `ort/` is rejected as a module
specifier). Then 1024->640 export cut anchors 21,504->8,400: 3,257 -> 1,360 ms on Intel Gen-9.

**Why:** fp16 buys size not speed on CPU; three browsers agreed on 40 s; the page itself
prints `NNN ms - GPU|CPU` at xr.js:679 -- that line settles backend questions.

**How to apply:** test with `python pacs/measure_live.py --film X --headed --channel chrome`
(enters via the github.io host on purpose). Verify any fp16 export locally with
`src/check_fp16_films.py` (CHECK_IMG=640) -- the grid node's glibc can't run onnxruntime.
Related: [[xray-corner-detector-status]], [[pacs-demo-and-ostk-params]].
