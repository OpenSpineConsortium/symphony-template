---
name: spineps-ids-can-be-scrambled
description: "SPINEPS masks harvested before commit 147428d (2026-09-21 18:20) carry RAW instance ids 1..N, not VerSe names; name from the ctd / guard tools/spineps_ids.py; VERIDAH's own names are unreliable vs readers; v8/v9 banks saw most G3 test people"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-24T01:10:27.387Z
---

**Cause (audit 2026-09-23, `SchwingNet/results/spineps_ids/{CENSUS,CONSUMERS,IMPACT,TS12_VERIFY,VERIFY}.md`):**
`benchmark/run_spineps_cases.py` kept the last file with "seg-vert" in its name, SPINEPS's `output_raw` instance
mask (ids 1..N, no names). Every store harvested before commit 147428d is raw: `~/bench/spineps/native` 800/800,
`~/bench_ts/spineps/native` ~1,469/1,518, tsv3 symlinks into it, `cobra2026/seg/spineps` 146/146. Stores harvested
after the fix are VerSe-coded. Body masks (`tools/body_masks.py`) copied the ids verbatim: ~2,714 raw bodies.
Guard: `tools/spineps_ids.py` (raises on raw ids, out-of-order names, T12 skips), wired into 13 readers;
3,490 masks relabelled into new trees.

**The 12 TotalSegmentator "L6":** chosen by "id 25 present" = "at least 25 instances". Independent rib count:
4 transitional (s1089 L6; s0616 T13; s1088 and s1123 a rib-less 25th vertebra, L6-pattern by rib count) and 8
normal (s1178 was VERIDAH skipping T12 on a scoliotic spine).

**VERIDAH is not truth.** On CTSP its ctd calls L6 on 24 cases where readers say 10, T13 on 52 where readers say
0; it skipped T12 wrongly in all 53 CTSP cases where it skipped. 46 post-fix CTSP masks pass the guard but are a
level off against readers. SPINEPS-derived truth needs a human (LEVELCHECK_MODEL.md section 4).

**Leak found by the split:** the v8/v9 level banks trained on 49/54 val+test L6, 4/4 T13, 14/14 sacralised G3
people. No checkpoint descended from v8/v9 may be scored on the G3 test; Figure 6 trains from ImageNet instead.

**How to apply:** never name a level by a SPINEPS id; call the guard; cross-check against reader labels where
they exist; check checkpoint lineage against the split before any evaluation. Related:
[[label-scheme-v4-vs-ostk]], [[versefusion-t13-flag-wrong]], [[six-figure-paper-plan]].
