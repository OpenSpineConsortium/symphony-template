# Looking inside a fetched set before its recipe

Source: the thread "Dataset finalization", 2026-10-23, in the project symphony_3. Read from SchwingNet's grid/gate.sh, grid/fetch-xray.json and grid/run-platform-fetch.sh at main 129a5a9, and from the gate's status answers of that day for jobs 40746797 to 40746809.

The owner asked for two Kaggle sets on the grid so they could be explored: the scoliosis YOLOv5 export (spine-datasets #23) and the fracture multi-region set (#24). He wants to check #23 against AASCE and map #24 back to the uploads it merges. Three things were learned on the way.

## The fetch word takes the X-ray chain first

SchwingNet's `fetch <id>` looks the id up in grid/fetch-xray.json before it looks at run-platform-fetch.sh's list. An id in fetch-xray.json gets the whole X-ray chain: fetch, bank and ingest, then a catalog build. Both Kaggle sets were already in that file, so the two downloads he approved queued six jobs. The kaggle-dataset lines added to the platform script in SchwingNet #165 are never reached for those ids.

Before sending `fetch` for an id, check which list holds it. Count the chain's jobs, not just one, when asking the owner for his number.

## Cancel takes the whole word

`cancel <job>` cancels the job named and every live job recorded under the same word, for example `fetch:<id>`. It does not cancel only the job named. Cancelling one step of a chain therefore cancels the fetch with it.

## A Roboflow export defeats a hash check

The plan for #23 was to compare the sha256 of every image with the AASCE copies on the grid. A Roboflow export re-encodes every image, usually resizes it (640 x 640 is the default) and may add mirrored or brightened copies. No byte hash of such a file can match the original film, even when the person is the same.

The check that can work is a content comparison. A percentile 8-bit reduction squashed to a square absorbs resizing and stretching. A perceptual hash finds candidates, with each image's mirror tried too, and NCC64 at 0.97 confirms them, which is the leak checks' rule. File names help once Roboflow's `_jpg.rf.<hash>` suffix is cut. Crops and rotations beyond a few degrees escape both checks, so "no match" there is a floor, not a proof of new people.

SchwingNet #168 builds this as the gate word `explore <id>`, passed by hpcworker #38 and by grid-accounts.yml's job schwingnet-explore-<id>. The first send queues one read-only job; the next send prints the report.
