import tempfile
from grid_sim import Grid, t, GB
with tempfile.TemporaryDirectory() as d:
    g = Grid(d)
    meta = (g.subvol / ".meta").stat().st_size
    q = g.X + meta + 1000 * GB
    g.attr(g.group, "ceph.quota.max_bytes", q)
    H, S = 16_900_000_000_000, 150_000_000_000
    # reading 1: 2,000 GB moved home->shared, gone from home, not yet in shared; the parent's figure dips too
    first = (f"{g.home} ceph.dir.rbytes {H - 2000*GB}\n{g.data} ceph.dir.rbytes {16_000_000_000_000 - 2000*GB}\n"
             f"{g.shared} ceph.dir.rbytes {S}\n{g.subvol} ceph.dir.rbytes {g.X - 2000*GB}\n{g.group} ceph.dir.rbytes {g.X - 2000*GB}\n")
    # reading 2: shared shows the first move, home shows a second 1,000 GB move gone; parents dip by 1,000
    second = (f"{g.home} ceph.dir.rbytes {H - 3000*GB}\n{g.data} ceph.dir.rbytes {16_000_000_000_000 - 3000*GB}\n"
              f"{g.shared} ceph.dir.rbytes {S + 2000*GB}\n{g.subvol} ceph.dir.rbytes {g.X - 1000*GB}\n{g.group} ceph.dir.rbytes {g.X - 1000*GB}\n")
    with g.xattrs.open("a") as h: h.write(first)
    later = g.base / "later"; later.write_text(second)
    moving = f'sleep() {{ cat "{later}" >> "$FAKE_XATTRS"; }}; '
    print("true room under the group", q - g.X - meta)
    print("first reading alone", g.rule('volume_free_bytes "$VOLUME"')[:2])
    print("settled", g.rule(moving + 'settled_room "$VOLUME"')[:2])
# the 200-character cut on the longest acq id with a zip-reading sizer
for id_, how in (("zenodo_ts_task_pleural_effusion", "1234 files listed by zenodo with 12 zips read"),
                 ("hf_abdomenatlas2_0_mini", "12345 files listed by the hub with 1234 zips read")):
    for where in ("under the quota", "under a quota above the volume"):
        line = (f"{id_}: refused for space; it needs 1234 gb of its 1234 gb by {how} and only 4887 gb is free "
                f"{where} after 1489 gb owed to 3 running fetches at 2026-10-24T01:18:00Z\n")
        print(repr(t.shown(line).splitlines()[0][-60:]))
