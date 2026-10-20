---
name: rsnai-paper-endpoint
description: "THE CULMINATION (Greg, 2026-09-22): ONE concise RSNA AI manuscript (paper/rsnai/main_v2.tex) -- navigation from C-arm shots alone; six-row full-page Figure 1; checklist docs/RSNAI_PLAN.md ticked only against evidence; bibliography RESOLVED 2026-09-22 (49 entries verified, claims reworded in all three manuscripts); pick up every session and re-verify"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T15:39:03.210Z
---

**Endpoint (Greg, 2026-09-22):** ONE very concise *Radiology: Artificial Intelligence* manuscript that introduces many
results quickly for a reader fluent in neurosurgery, AI and computer science. Story: navigation (tracker registered
to a 3-D scan) vs hand counting across C-arm shots (cite the counting procedure; cite the quaternary fiducial study's
cost) -> navigation made of OR C-arm shots alone. Results: level naming on plain films -> film detectors fail on
fluoroscopy -> table of every fluoroscopic dataset -> naive DRR mapped into each detector's domain by physical terms ->
per-device parameter distributions, sampled -> device manifold in 3-D -> pooled detector over all devices,
leave-one-device-out, scaling -> device fine-tuning -> best universal detector (sacrum, vertebra, C2, hips, BCF point)
-> benchmark vs published networks retrained on our data -> future (phantom, cadaver, human).

**Figure 1 (Greg's spec): one full page, six landscape full-width rows** -- (a) processing chain; (b) the prone-patient
sweep cartoon ("head left, posterior up"); (c) confirmation (instrument from posterior -> matched onto the chain ->
ordinal; no tracker, no preoperative CT); (d) every C-arm dataset and every plain-film corpus in one PCA space,
labelled by DICOM header (scanner) or dataset, showing film vs fluoro separability -- be thorough, find every corpus
on the grid; (e) corpus construction + network + what separates the work from prior art; (f) same style as (c) in
the fluoroscopic domain on a synthetic VerSe full spine with an LSTV/TLTV (verse547/602/631 = C1-L5 + T13).
Tools: fig_story_rows.py, corpus_manifold.py + fig_row4_manifold.py, fig_row5_corpus_arch.py, fig_story_compose.py.

**Where things live:** checklist `spinesurg-ct-nnunet/docs/RSNAI_PLAN.md` (A-E, dated status log at the bottom --
read the last entry first); manuscript `paper/rsnai/main_v2.tex` (builds clean with `latexmk` in WSL; every number a
letters-only macro from `claims.tex` <- `tools/claims_fill.py` <- `docs/RSNAI_CLAIMS.json`, checked by
`tools/claims_check.py`); data manifest `docs/RSNAI_DATA_MANIFEST.json`; Table 1 `tools/rsnai_table1.py`. The older
drafts `paper/rsnai/main.tex` (chain paper) and `paper/qi_universal_protocol/main.tex` are sources to lift from.
ALWAYS read before writing under `paper/` (main.tex was overwritten once and restored from git).

**Citations -- verified facts and traps:** counting workflow = manbachi2018 (count up from sacrum / down from C1 on
C-arm fluoroscopy) + strong2021 (navigation for level validation; needles cephalad from the sacrum; stitched shots) +
hsiang2011 (wrong-level persists; navigation not in every hospital). NO source gives "three or four bodies" or a
9-inch field for counting -- never write it. siminski2023 = Mayo Clinic Rochester (179 placements, 176 thoracic,
51.9 min, 183 mGy); the paper never says "quaternary", so the text names the centre. Macki 2014 figures are the cost
of IMPLANTING a fiducial ($1,237.55 / $1,267.03, 2013 CPT). Furuya's 81 % is of lumbar events only. The Universal
Protocol cites `jcnpsg2025` (Joint Commission 2025 goals PDF), not jc2024. upadhyaya2012 has NO cost or time numbers.
Bibliography resolved 2026-09-22: `tools/bib_apply_resolved.py` applied workflow wf_387e3e52-e7b; record of every
entry, verdict and claim check in `docs/BIB_RESOLVE_2026-09-22.json`; remaining audit flags are Crossref quirks. Long
notes live in `annote` (unsrtnat prints `note`). The superseded `paper/rsnai/main.tex` was not corrected.

**Why:** Greg wants formal rigour and to resume without losing the thread; the recurring failure in this project is
a plausible wrong value (now seen in the bibliography too). "Exponential" / "refutes the literature" stay conditional
on C7/C8 and C6 passing their pre-stated tests; C6 fails so far.

**How to apply:** each session: read the plan's last status entry, re-verify against the grid, run claims_check and
bib_audit, then work the next unticked box. Related: [[k-devices-one-network]], [[resume-2026-09-22]],
[[carmlspine-level-experiment]], [[commercialization-stance]] (never name the product in the paper),
[[bash-heredoc-backslashes]], [[no-jobs-on-login-node]].
