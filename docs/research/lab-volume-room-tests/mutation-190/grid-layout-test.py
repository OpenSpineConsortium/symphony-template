    def test_the_grids_layout_reads_each_folder_by_the_sum_where_its_figure_is_no_count(self):
        # The grid's layout (the status word of 2026-10-24 01:18 UTC): the volume inside its
        # subvolume's folder, beside one file, inside its group's folder, which holds nothing else and
        # carries the one quota above the volume, on a mount whose root lies higher. Here each folder's
        # own figure reads as no count, so what each holds is the sum of its own entries, the one that
        # holds the folder below counted at what that holds, from the volume's use up (#190).
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        top = Path(tmp.name)
        group = top / "group"
        sub = group / "sub"
        sub.mkdir(parents=True)
        volume = Volume(sub, quota=21991 * GB, used=13146 * GB)
        stat = dict(STAT=str(volume.tools / "stat"))
        volume.mount(top)
        volume.attribute(volume.tools, "ceph.dir.rbytes", 1 * GB)
        for folder, entries in ((sub, len(list(sub.iterdir()))), (group, 1), (top, 1)):
            volume.attribute(folder, "ceph.dir.rbytes", "1" * 48)
            volume.attribute(folder, "stat.size", entries)
        volume.attribute(group, "ceph.quota.max_bytes", 13500 * GB)
        env = dict(os.environ, DATA=str(volume.data), **volume.env(**stat))

        def rule(call):
            done = subprocess.run(["bash", "-c", f'. "{ROOT}/grid/size-rule.sh"; {call}'], env=env,
                                  capture_output=True, text=True, timeout=60)
            return done.returncode, done.stdout.strip()

        files = sum(entry.stat().st_size for entry in sub.iterdir() if entry.is_file())
        held = 13146 * GB + 1 * GB + files
        self.assertEqual(rule(f'path_quotas "$VOLUME" {13146 * GB}'), (0, f"2 {13500 * GB} {held} entries"))
        self.assertEqual(rule('volume_free_bytes "$VOLUME"'), (0, f"{13500 * GB - held} quota-2"))
        # a second entry in the group's folder, another subvolume, counts by its own figure
        other = group / "other"
        other.mkdir()
        volume.attribute(other, "ceph.dir.rbytes", 300 * GB)
        volume.attribute(group, "stat.size", 2)
        self.assertEqual(rule('volume_free_bytes "$VOLUME"'), (0, f"{13500 * GB - held - 300 * GB} quota-2"))
        # and one whose figure is no count leaves the room under the group's quota unknown
        volume.attribute(other, "ceph.dir.rbytes", "1" * 48)
        self.assertEqual(rule(f'path_quotas "$VOLUME" {13146 * GB}'), (2, "unread 2"))
        self.assertEqual(rule('volume_free_bytes "$VOLUME"'), (1, ""))
