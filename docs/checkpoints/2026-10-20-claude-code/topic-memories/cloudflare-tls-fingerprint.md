---
name: cloudflare-tls-fingerprint
description: "Archives that 403 curl/wget/urllib from every IP are blocking the TLS fingerprint, not the address -- curl_cffi impersonate=\"chrome\" is served normally"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T00:18:28.581Z
---

The JHU Data Archive (`archive.data.jhu.edu`, where DeepFluoro lives) answers **HTTP 403** to curl,
wget and urllib -- from the WSU grid login node, from a residential workstation, over http and https,
and **with a complete browser header set** including UA, Accept, sec-ch-ua and Sec-Fetch-*. The body is
a Cloudflare "Attention Required!" interstitial.

It is neither the IP nor the headers. It is the **TLS/HTTP2 fingerprint** (JA3). A client presenting
Chrome's fingerprint is served normally, no browser and no interactive challenge needed:

```python
from curl_cffi import requests
r = requests.get(url, impersonate="chrome", stream=True, allow_redirects=True)
```

Worked first try, HTTP 200. `tools/dl_deepfluoro.py` in `spinesurg-ct-nnunet` does this; install with
`$HOME/mambaforge/envs/fluorogen/bin/python -m pip install curl_cffi` (the grid's system `python3` is
too old -- it reports `ImportError: No module named curl_cffi` in py2 style).

Worth trying before asking the user to download something by hand, and before concluding a dataset is
unreachable from the grid. Note the grid login node **does** have outbound internet -- an HTTP status
code coming back at all proves that, as against a DNS failure.
