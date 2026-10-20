---
name: lstv-reread-queue
description: "Where to log cases whose source LSTV label looks wrong, for radiologist re-reading"
metadata: 
  node_type: memory
  type: project
  originSessionId: 436e5c70-681e-4f38-aab2-30dfa25af7b5
---

When an adjudication turns up a case whose **source LSTV/Castellvi label disagrees with the
anatomy** (e.g. the manifest says `normal` but the CT shows 5 anterior sacral foramina = 6-segment
sacrum = sacralization, and/or a rib sits on the vertebra labelled L1), **append it to
`docs/lstv_reread_queue.csv`** in the CTSpinoPelvic1K repo (do NOT start a new file) -- Greg's
radiologists pull that queue to re-read. Columns: date_flagged, case_id, volume_id, token, config,
source_lstv_label, discrepancy, flagged_by, status.

First entry (2026-07-04): case `121__spine_only` / volume `0172` -- source `normal`, but 5 sacral
foramina + 12th rib on "L1" -> flagged as likely sacralization, `pending_reread`.

Normal sacrum = 5 segments = **4 anterior sacral foramina**; 5 foramina = sacralization (6-segment),
3 = lumbarization. Don't infer LSTV from the pseudolabelled/student ribs (untrusted) -- the
manifest's `lstv_label`/`castellvi_type` are the source radiologist read; `prov_spine=manual` means
the vertebra labels are hand GT. See [[thoracic-gt-fov-limited]], [[splits-origin-and-v3-resplit]].
