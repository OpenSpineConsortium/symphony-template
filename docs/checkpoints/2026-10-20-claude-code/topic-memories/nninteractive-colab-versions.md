---
name: nninteractive-colab-versions
description: Working version pins for the ITK-SNAP DLS (nnInteractive) AI-segmentation server on Google Colab
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1af48852-259d-4e9a-8d35-41c5258bbce6
---

The ITK-SNAP Deep Learning Server (nnInteractive) on Colab breaks if you `pip install itksnap-dls nnInteractive` unpinned -- pip pulls nnInteractive 2.x + nnunetv2 2.7.0, which crash with `use_pinned_memory` and `build_network_architecture() takes 4 to 5 positional arguments but 6 were given`. itksnap-dls 0.1.2 (current) only works with the OLD nnInteractive 1.x.

**Known-good combo (confirmed working June 2026, T4 GPU, Python 3.12):**
```
!pip install "itksnap-dls>=0.0.7" "nnInteractive==1.1.0"
!pip install --no-deps "nnunetv2==2.6.2"
!pip install "numpy<2.1"
```
Must be three SEPARATE lines -- one combined resolve re-pulls the broken versions. `--no-deps` on nnunetv2 is the key (forces the downgrade past nnInteractive's `>=2.7.0` pin). Then **Runtime -> Restart session**, then run the server cell (`!NGROK_AUTHTOKEN=... python -m itksnap_dls --ngrok`). Verify: `nnUNetTrainer.build_network_architecture` signature must contain `arch_init_kwargs_req_import`. Fallback if not: `nnunetv2==2.5.1`.

The red pip "dependency conflict" warnings are expected (we override the resolver on purpose). ITK-SNAP 3D view never auto-renders -- click **Update** in the 3D pane; nnInteractive fills the ACTIVE label, so set it before scribbling. See [[review-space-repos]].

**START_SESSION 500 / EMPTY-BODY JSONDecodeError (root-caused 2026-06-30):** with this pin set, starting an AI session fails -- ITK-SNAP shows *"Error creating session on DLS server: Internal Server Error"* and the Colab log shows `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` from `huggingface_hub`/`httpx`, right after `Configuring Huggingface HTTP client`. **REAL cause: itksnap_dls's `segment.py` line ~36 does `hf.set_client_factory(lambda: httpx.Client(verify=...))` with NO `follow_redirects`** -- HF's `/api/models/...` redirects, httpx (unlike requests) doesn't follow by default -> empty body -> JSON crash. The bare-model-id thing (`nnInteractiveWrapper.ID == "nnInteractive"`) was a RED HERRING / at most secondary; patching only the id does NOT fix it (Greg confirmed: id patched, still 500). The model is **public** at `nnInteractive/nnInteractive` (= `MIC-DKFZ/nnInteractive`) -- no HF token needed. **Fix (confirmed working -- model downloaded, session init 9s): patch the installed `segment.py` on disk for follow_redirects (+ id for good measure), then run the NORMAL server line** (do NOT `runpy` in a cell -- in-process breaks ngrok on Colab: `'_asyncio.Task' object has no attribute 'url'`). After install+restart:
```python
import itksnap_dls, pathlib, re
p = pathlib.Path(itksnap_dls.__file__).parent / "segment.py"
s = p.read_text()
s = re.sub(r"httpx\.Client\((?!follow_redirects)", "httpx.Client(follow_redirects=True, ", s)  # THE fix
s = re.sub(r"(['\"])nnInteractive\1", r"\1nnInteractive/nnInteractive\1", s)                    # id (minor)
p.write_text(s)
print("ok:", "follow_redirects=True" in p.read_text() and "nnInteractive/nnInteractive" in p.read_text())  # True
```
then `!NGROK_AUTHTOKEN="..." python -m itksnap_dls --ngrok`. (segment.py is the pip package, not the dataset repo -- a fresh runtime re-installs it un-patched, so re-run this cell every session BEFORE the server cell.) Also: `ERR_NGROK_334 "endpoint already online"` = your own stale server holding the free one-endpoint tunnel -> Runtime -> Disconnect and delete runtime (+ close other tabs), or `!pkill -9 -f itksnap_dls; pkill -9 -f ngrok`.
Fallback for students: the rib-review task only needs CONNECTING two pieces of a rib, which is a one-stroke brush edit in ITK-SNAP -- the AI tool is optional. Documented in REVIEWERS_AI_EDITING.md.
