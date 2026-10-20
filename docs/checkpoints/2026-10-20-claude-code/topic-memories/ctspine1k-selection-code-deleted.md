---
name: ctspine1k-selection-code-deleted
description: "CTSpine1K's claimed supine/prone selection code does not select -- it overwrites by os.walk order -- and was deleted from the repo; recover it at commit 7f44959"
metadata: 
  node_type: memory
  type: reference
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-12T15:41:28.033Z
---

CTSpine1K's README claims "We randomly select one of the two positions (we open the code
for selecting them, dicom2nii.py)". Both halves are false.

DELETED: commit bcd8f47, 11 Jun 2021, "Delete dicom2nii.py". The repo now holds only
Path.csv, two READMEs, Task056_VerSe2019.py and data_split.txt -- no preprocessing,
training, download or selection code. The file survives at the parent commit:
https://raw.githubusercontent.com/MIRACLE-Center/CTSpine1K/7f44959/dicom2nii.py

AND IT NEVER SELECTED ANYTHING. 41 lines. It loops `for path_, _, file_ in
os.walk(directory1)`, and for every series with more than 10 slices writes to
`os.path.join(path2, volumeID + ".nii.gz")` -- the SAME filename each time. So a patient's
retained volume is whichever series os.walk reached LAST, overwriting the rest, with
`series_id[0]` inside readdcm taking the first GDCM series in that directory. No seed, no
random call, no supine/prone logic.

WHY IT MATTERS FOR THE PAPER. main.tex says neither source released the mapping from an
annotation to the series it was drawn on. The stronger, documented claim is that for
CTSpine1K the mapping NEVER EXISTED: which acquisition survived was an unrecorded side
effect of directory traversal order and filename collision on a machine in 2020. So the
crosswalk in [[s1-carve-changed-spinopelvic]]'s pipeline is not recovering lost metadata --
it is the only way the correspondence can be established.

Also checked: CTSpine1K's table labels its Decathlon subset "MSD T10" but its text says
task03_liver, 201 cases (which matches Task03 Liver exactly). CTPelvic1K's MSD_T10 is 155
cases. They are DIFFERENT tasks, so "COLONOG is the only collection common to both" holds --
but the two tables read as though they share MSD_T10. And CTSpine1K's per-source counts
(825+201+40+31 = 1,097) do not sum to its stated 1,005.
