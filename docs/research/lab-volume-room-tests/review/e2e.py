import os, sys, tempfile
from pathlib import Path
from grid_sim import Grid, t, GB

def job_env(g, **extra):
    env = dict(GETFATTR=str(g.tools / "getfattr"), SQUEUE=str(g.tools / "squeue"), SIZER=str(g.tools / "sizer"),
               FAKE_XATTRS=str(g.xattrs), FAKE_QUEUE=str(g.queue), MOUNTINFO=str(g.mountinfo), VOLUME=str(g.link),
               DATA_ROOT=str(g.data), USER="go2432", SIZE_RULE_STAND_INS="yes", SIZE_RULE_SETTLE="0",
               STAT=str(g.tools / "stat"))
    env.update(extra)
    return env

class V:  # what run_fetch_job needs of a volume
    def __init__(self, g): self.g = g
    def env(self, **extra): return job_env(self.g, **extra)

def fetch(g, need, source="hf_example", **extra):
    extra.setdefault("FAKE_SIZE", f"{need} {need} 3 files listed by the hub")
    code, out = t.run_fetch_job(g.base, V(g), "hf-token", t.HF_ARGS, source=source, FAKE_FILES="2", **extra)
    return code, [l for l in t.shown(out).splitlines() if source in l]

with tempfile.TemporaryDirectory() as d:
    g = Grid(d)
    room = 21990232555520 - g.X
    print("A volume binds, room", room)
    print(fetch(g, room)); print(fetch(g, room + 1))
    # B: the group's quota made the least: 1000 GB above what the group holds by its sum
    meta = (g.subvol / ".meta").stat().st_size
    q = g.X + meta + 1000 * GB
    g.attr(g.group, "ceph.quota.max_bytes", q)
    print("B group binds")
    print(fetch(g, 1000 * GB)); print(fetch(g, 1000 * GB + 1))
