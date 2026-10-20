---
name: pooled-vs-lodo-device-designs
description: "Design P pools every C-arm into one model tested on a cross-device holdout (Greg's ask, 2026-09-22); LODO answers a different question and both are reported"
metadata: 
  node_type: memory
  type: project
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-22T21:49:35.903Z
---

Greg, 2026-09-22: "train like one model on all the C-arms ... a one-size-fits-all model, and then test that on a
holdout test set across every single detector -- no leave-one-device-out."

Built as `tools/devcorpus_build.py lists --design P` (`slurm/devcorpus_pooled.sh`). Every geometry x every card,
plus every device's real training frames, into one detector; scored on every device's real TEST split.

**The two designs answer different questions and neither substitutes for the other.** Pooled: every device in the
fleet is represented in training -- the deployable case for a vendor who can collect frames from each unit it ships
to. LODO: the model meets a machine that did not exist when it was trained -- the harder question, and the one a
regulatory submission is asked. Report both; never quote the pooled number without the LODO number beside it.

**The list builder refuses rather than warns.** Two conditions that a pooled design is exactly where they break:
one CT subject must be on ONE side of the split in every geometry and under every card (the styled corpora each
drew their own validation subjects, so two disagreeing means a subject trains under one geometry and validates
under another), and real frames must split BY SPECIMEN. Checked by hand first: deepfluoro, carmlspine,
cobra_elekta and geneva_hip are all specimen-keyed with zero overlap.

First build: 5 styled corpora over 3 devices, 18,906 training entries (12,730 styled + 6,176 real), 1,998
validation, 17 held CT subjects, 56 test specimens (cios 1, surgio 28, elekta 27). geneva_hip is test-only and not
in training, so it also scores as a completely unseen device for free.

Related: [[device-sampling-audit]], [[k-devices-one-network]], [[ct-benchmark-covers-all-collections]].
