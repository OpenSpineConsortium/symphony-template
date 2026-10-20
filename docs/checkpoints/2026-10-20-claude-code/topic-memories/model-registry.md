---
name: model-registry
description: "Where trained weights live on the grid (content-addressed store, ledger, MLflow SQLite, HF mirror), how trainers/chains register them, and the MLflow install that works"
metadata: 
  node_type: memory
  type: project
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-15T10:19:37.831Z
---

Since 2026-09-15 every weight file the grid pipeline produces goes into `~/model_registry/<sha16>/<file>`
(read-only), ledgered in `~/model_registry/registry.jsonl`, aliased under `~/model_registry/aliases/<name>`,
logged to MLflow (SQLite `~/mlflow/mlflow.db`, artifacts `~/mlflow/artifacts/<stage>/`) and mirrored to the
private HF repo `gregoryschwingmdphd/level-id-weights` under `registry/<name>/<sha>.<ext>`. Code:
`tools/model_registry.py` (register / resolve / link / restore / sync / list / backfill); doc
`docs/MODEL_REGISTRY.md`. Trainers call `try_register` after `torch.save` with `push=False` (compute nodes
have no route out); `slurm/registry_sync_loop.sh` and the chains run `sync` on the login node to mirror and
to log to MLflow. Chains use `model_registry.py link`, never `ln -sf`, for fixed-name model paths.

**Why:** an `ln -sf model.pt model.pt` in a chain destroyed a 2.5-hour model on 2026-09-15; the user asked
that models be backed up implicitly by the pipeline.

**How to apply:** new trainers register on save; new chains link + sync; the MLflow env is `spineps` only
(mlflow-skinny 3.16 + `pip install --no-deps sqlalchemy alembic Mako MarkupSafe`; full mlflow and greenlet
do not build there; one MLflow version per SQLite file). MLflow `log_artifact` of an NFS file fails on
xattr copy, so runs carry a `registration.json` pointer written from `/dev/shm`. See
[[level-model-bank-coverage]], [[overnight-2026-09-15-chains]].
