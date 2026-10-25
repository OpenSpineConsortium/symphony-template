"""A simulation of the real grid's layout (facts of 2026-10-23/24) with the test's stand-ins."""
import os, subprocess, sys, tempfile
from pathlib import Path
RV = Path("/tmp/claude-0/-home-claude/ecdd0a20-c17e-5671-b6da-4109dc513c50/scratchpad/rv")
sys.path.insert(0, str(RV / "tests"))
import test_xray_chain as t

GB = 10**9

class Grid:
    def __init__(self, base):
        self.base = Path(base)
        self.tools = self.base / "tools"; self.tools.mkdir()
        for name, text in t.STAND_INS.items():
            (self.tools / name).write_text(text); (self.tools / name).chmod(0o755)
        # getfattr follows links, as the real one does: resolve the folder before the stand-in looks it up
        (self.tools / "getfattr-real").write_text(t.STAND_INS["getfattr"]); (self.tools / "getfattr-real").chmod(0o755)
        (self.tools / "getfattr").write_text('#!/bin/bash\nargs=(); for a in "$@"; do if [ -e "$a" ] && [ "${a#/}" != "$a" ]; then args+=("$(readlink -f -- "$a")"); else args+=("$a"); fi; done\nexec "' + str(self.tools / 'getfattr-real') + '" "${args[@]}"\n')
        self.xattrs = self.base / "xattrs"; self.xattrs.write_text("")
        self.queue = self.base / "queue"; self.queue.write_text("")
        self.rs = self.base / ".rs"
        self.volumes = self.rs / "volumes"
        self.group = self.volumes / "rs_grp_oschome"
        self.subvol = self.group / "rs_vol_oschome"
        self.uuid = self.subvol / "8f1c2d3e-uuid"
        self.home = self.uuid / "go2432"; self.data = self.home / "data"; self.shared = self.uuid / "shared"; self.other = self.uuid / "other"
        for f in (self.data, self.shared, self.other): f.mkdir(parents=True)
        (self.subvol / ".meta").write_text("[GLOBAL]\nversion = 2\ntype = subvolume\npath = /volumes/rs_grp_oschome/rs_vol_oschome/8f1c2d3e-uuid\nstate = complete\n")
        for i in range(5): (self.volumes / f"grp{i}").mkdir()
        (self.base / "rs").mkdir()
        self.link = self.base / "rs" / "rs_grp_oschome"; self.link.symlink_to(self.uuid)
        self.mountinfo = self.base / "mountinfo"
        self.mountinfo.write_text("22 1 253:0 / / rw,relatime shared:1 - xfs /dev/vda1 rw\n"
                                  f"98 22 0:52 / {self.rs} rw,noatime shared:40 - ceph 10.0.0.1:6789:/ rw,name=lab\n")
        self.used_entries = {self.home: 16_900_000_000_000, self.shared: 150_000_000_000, self.other: 52_970_629_057}
        self.X = sum(self.used_entries.values())
        a = self.attr
        a(self.uuid, "ceph.quota.max_bytes", 21990232555520)
        a(self.uuid, "ceph.dir.rbytes", "1" * 48)
        a(self.uuid, "stat.size", 3)
        a(self.link, "ceph.quota.max_bytes", 21990232555520)
        a(self.link, "ceph.dir.rbytes", "1" * 48)
        a(self.link, "stat.size", 3)
        for f, v in self.used_entries.items(): a(f, "ceph.dir.rbytes", v)
        a(self.data, "ceph.dir.rbytes", 16_000_000_000_000)
        a(self.data, "stat.size", 126)
        a(f"{self.data}/*", "ceph.dir.rbytes", 0)
        a(self.subvol, "ceph.dir.rbytes", self.X)
        a(self.subvol, "stat.size", 2)
        a(self.group, "ceph.quota.max_bytes", 43980465111040)
        a(self.group, "ceph.dir.rbytes", self.X)
        a(self.group, "stat.size", 1)
        a(self.volumes, "ceph.dir.rbytes", 1820301260775581)
        a(self.volumes, "stat.size", 251)
        a(self.rs, "ceph.dir.rbytes", 1820301260775581)
        a(self.rs, "stat.size", 1)

    def attr(self, folder, name, value):
        with self.xattrs.open("a") as h: h.write(f"{folder} {name} {value}\n")

    def env(self, **extra):
        env = dict(os.environ, GETFATTR=str(self.tools / "getfattr"), SQUEUE=str(self.tools / "squeue"),
                   SIZER=str(self.tools / "sizer"), FAKE_XATTRS=str(self.xattrs), FAKE_QUEUE=str(self.queue),
                   MOUNTINFO=str(self.mountinfo), VOLUME=str(self.link), DATA_ROOT=str(self.data), DATA=str(self.data),
                   USER="go2432", SIZE_RULE_STAND_INS="yes", SIZE_RULE_SETTLE="0", STAT=str(self.tools / "stat"),
                   REPO=str(RV))
        env.update(extra)
        return env

    def rule(self, call, script=None, **extra):
        script = script or (RV / "grid" / "size-rule.sh")
        done = subprocess.run(["bash", "-c", f'set -uo pipefail; . "{script}"; {call}'], env=self.env(**extra),
                              capture_output=True, text=True, timeout=120)
        return done.returncode, done.stdout.rstrip("\n"), done.stderr.strip()

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        g = Grid(d)
        print("X =", g.X, " meta size", (g.subvol / ".meta").stat().st_size)
        for call in ('quota_below "$VOLUME"; echo rc=$?', 'quotas_above "$VOLUME"', 'volume_used "$VOLUME"',
                     f'path_quotas "$VOLUME" {g.X}', 'volume_free_bytes "$VOLUME"', 'settled_room "$VOLUME"'):
            print(call, "->", g.rule(call))
        code, out, err = g.rule('quota_readout "$VOLUME" "Lab"')
        print(code); print(out.replace(str(g.base), "<BASE>")); print("stderr:", err)
