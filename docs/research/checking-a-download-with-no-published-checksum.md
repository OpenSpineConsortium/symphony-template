# Checking a download whose publisher gives no checksum, and gated tests that need an optional dependency

Source: the thread "SchwingNet bank recipes and leak checks", 2026-10-21, issue #44 of OpenSpineConsortium/SchwingNet (pull request #48, merged that day). This note keeps what is general in that work; nothing here is about what the data is for.

## A download with no checksum

NIH publishes ChestX-ray14 as twelve archives behind Box links with no checksum of any kind, so a fetch had been left to a person, who copied the files by hand and checked nothing. Academic Torrents carries the same twelve files as one torrent, and a torrent's info dictionary is a published checksum in all but name: every file's length and a SHA-1 for every fixed-size piece of the files laid end to end, pinned by the infohash, the SHA-1 of the info dictionary itself.

So the fetch downloads the archives over HTTP as before and then checks them against the torrent, without any torrent client:

- the .torrent file is fetched once and kept, and its info dictionary's SHA-1 must equal the infohash written in the recipe, so a changed or substituted torrent is refused, and a cached copy that no longer matches is fetched again;
- the info dictionary is read with a bencode parser of about thirty lines of standard-library Python;
- each downloaded file is matched to a torrent entry by name, its length must agree, every name the recipe lists must be matched, and every piece that lies wholly inside files present on disk is hashed and compared;
- a run in which no piece could be checked fails, so a torrent that names other files cannot pass by checking nothing.

Only after that are the archives unpacked, regular files only, each written to a temporary name and renamed, and nothing outside the target folder.

The method applies wherever a publisher gives no checksum but a torrent of the same release exists. Where the torrent's host is unreachable from the machine doing the fetch, the .torrent can be placed beside the state by hand, since its own hash is what is trusted, not where it came from. The URLs were taken from three independent copies of the publisher's download script that agreed; the copy the repository held had one of them wrong, which only the cross-check showed.

## A gate that refuses skipped tests

beethoven-qa's gate, as SchwingNet runs it, fails a test run under its own test folder with any test skipped, and `pytest.importorskip` counts as a skip. A test that needs a dependency only one environment carries (here pydicom, locked into the training environment and not the default one) therefore cannot sit in the gated folder. It went under the template's tests/, as a unittest with `skipIf` on the import, where `bash scripts/check.sh` runs it and a skip is allowed, and it is run in full with that environment's Python. The gate also refuses `# type: ignore` and `# fmt: skip` in tests.

A related observation: CrossHair, the gate's symbolic lane, once reported a counterexample against an unchanged function on a commit that touched no source, and passed on the next commit. A symbolic finding on code a pull request does not touch is checked on the base branch before it is treated as the pull request's.
