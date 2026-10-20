---
name: anomaly-harvest-directive
description: "Greg 2026-09-23 -- scrape EVERY CT we hold for transitional anatomy (VerSeFusion over VerSe, TS v2 via SPINEPS, COBRA, all others), maximize CTSP's L6/sacralisations, and use the scoping review to find more CT; two labellers, count needs both junctions in FOV"
metadata:
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-23T22:28:04.478Z
---

Greg, 2026-09-23: "SCRAPE THE BOTTOM OF THE BARREL FOR ANOMALIES." Every CT dataset we hold should yield transitional
cases: VerSe (~40+ transitional; use **VerSeFusion**, better quality), TotalSegmentator v2/v3 through SPINEPS, COBRA
(692), CTSP1K (18 L6 + 12 sacralised + Castellvi I-II + lumbar rib -- **maximize every one**), and any other CT on disk.
Then run the programmatic scoping review (`spinesurg-ct-nnunet/spine_data_review/`, `bash run_all.sh --run-date ...`
via WSL) to find more public CT.

**Why:** transitional anatomy is the clinical payload, and real transitional people are the binding constraint
(LEVELCHECK power table: >=35 per stratum at zero errors; two strata had zero typed people).

**How to apply:** his worry "any CT on the internet could be segmented" is answered by a stated criterion, not a
crawl: a call needs a COUNT, a count needs both junction references in FOV, so rank collections by expected
transitional people = n x P(junction countable) x prevalence, deduped against aggregators, with a stopping rule
stated in advance. Two independent labellers (SPINEPS ctd names + TotalSegmentator geometric rib/lumbar count);
discordance -> rendered review queue for Greg. Never name by SPINEPS id ([[spineps-ids-can-be-scrambled]]). COBRA /
C-ArmLSpine transitional people are TEST only, never rendered for training. Workflow anomaly-harvest
wf_babed05b-84a -> `SchwingNet/results/transitional_registry/` (one row per person). Related:
[[lstv-tltv-detection-goal]], [[no-unexplained-subsets-fix-not-disclose]], [[lstv-data-landscape]].
