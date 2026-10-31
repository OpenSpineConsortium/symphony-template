# Sorting a spine imaging corpus into gold and silver evidence tiers: the method and the count

The thread "Sort the corpus into gold and silver tiers", 2026-10-27, on the owner's ask of 03:06 UTC that day: before the claims of the vertebral-naming work are tested, sort every de-identified dataset held, and every one approved or requested, into gold and silver tiers, so that the power of each planned experiment can be computed and the experiments limited to gold data wherever they can be. This note holds the public half: the tiers, how a case is placed, how the power is read and what the one grid job costs. The table itself, source by source with its counts, and the research note are confidential and stay in SchwingNet (docs/research/corpus-tiers/README.md and data/corpus-tiers/sources.json), which never leave that repository.

## The tiers, as the owner set them

A case is gold when one study of the person shows the whole spine, so that a level named in it can be checked by counting from the second cervical vertebra; it is silver when it shows less. Within each:

- 1: a CT and a real X-ray (AP, lateral or both) of the same person, with a person's annotation of the vertebrae on at least one of the two.
- 2: the same pair, with no person's annotation on either.
- 3: a CT or an X-ray alone, with a person's annotation.
- 4: a CT or an X-ray alone, with none.

The owner wrote tiers 3 and 4 as "CT paired or full spine XRay"; the sort reads them as one modality alone, which is the only reading that keeps the four tiers distinct, and says so wherever it prints them.

## How a case is placed

- The unit is the person. A person with several studies counts once, at the best tier any of them reaches, in the order gold 1 to 4, then silver 1 to 4: gold first, since only a whole spine verifies a count.
- Whole spine means the count from C2 holds: C2 is in the field, no more than one body lies above it, no gap between two bodies is wide enough to hide a missed one, and the sacrum is in the field. For a CT with vertebra masks this is read from the mask itself, with the centroid file's C2 and nothing else of the labeller's names; for a film it is read from the field of view the release or the reader records.
- A pair is gold only when both images show the whole spine. A whole-spine CT with real C-arm frames of part of the spine is gold 3 or 4 by the CT and silver 1 or 2 as a pair, and both are reported.
- An X-ray is a real radiograph or real fluoroscopy. A digitally reconstructed radiograph, edited or not, is not an X-ray for these tiers, so a source made only of synthetic images stands outside them.
- A person's annotation is a mask, a point, a corner or a level name that a person drew, checked or refined. A machine's masks and level names, from any segmenter or labeller, are recorded beside the tier and never raise it; a radiology report that only mentions a level is recorded as report-only and does not raise it either.
- A source not held, approved or requested, is given the tier it would bring and holds no one until it is on the grid.

## The conversions the owner named, and what each needs first

- Machine masks on an unannotated case (tier 4 towards tier 3): the masks give every vertebra a provisional name, which is what the count from C2 is read from, but they are a machine's, so the case stays at tier 4 for the owner's definition and is counted again in a column of its own until a person has checked it.
- An edited DRR from an annotated whole-spine CT (tier 3 towards tier 1): it can stand beside a real X-ray only once the edited DRRs are shown, by a pre-registered two-sample test, not to be told apart from real radiographs at the resolution the claims are read at; until then the pair is synthetic and is reported apart, never pooled with real pairs, and its labels are the CT's, so it cannot test naming on real X-ray.
- A person's review, or the level-naming tool with a person confirming it (tier 3 towards tier 1, tier 4 towards tier 3): each reviewed case moves one step when the reviewer is recorded; the tool's own answer is a machine's until then.

## How the power is read

Each claim is a proportion over persons, so its precision is the Wilson interval at the expected rate over the gold persons the claim can use; a claim that no error occurs is bounded by the exact one-sided binomial bound, about three over the number of persons (the rule of three). The sort prints, for every tier, the persons held and the half-width each gives at 90 percent accuracy, and the research note sets each planned experiment beside the tier it needs.

## The count

One CPU job, through the existing job word `schwingnet-census-<id>` that grid-accounts.yml already accepts, with the id `tiers`: SchwingNet's grid/gate.sh word `census tiers` queues grid/census.sbatch, which reads every existing vertebra mask the project's transitional census lists, writes nothing but its per-case file on the lab volume and a report of counts, and segments, trains and fetches nothing. It waits for the owner's word and count, asked once as a decision card in the thread. Nothing changes in this repository's grid route.
