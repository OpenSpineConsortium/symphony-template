---
name: panjabi-1991-page-892
description: "RESOLVED 2026-09-13: complete Panjabi 1991 obtained by ILL (CTSpinoPelvic1K-1/PANJABI_1991_FULL_fixed.pdf, p. 892 = page 7, image-only); Table 3 values now in level_references.csv"
metadata: 
  node_type: memory
  type: reference
  originSessionId: e44eca96-f48c-494d-ba1f-7dae68bdf06d
  modified: 2026-09-10T13:24:20.046Z
---

Panjabi MM, Takata K, Goel V, Federico D, Oxland T, Duranceau J, Krag M.
"Thoracic human vertebrae: quantitative three-dimensional anatomy."
*Spine* 1991;16(8):888-901. **doi:10.1097/00007632-199108000-00006**, PMID 1948374.
Print ISSN 0362-2436 (OCLC 2589719, LCCN 76646361); online ISSN 1528-1159
(OCLC 43273987, and a second online record 761256696).

**RESOLVED 2026-09-13:** a complete copy arrived by interlibrary loan (Internet Archive lender) as `CTSpinoPelvic1K-1/PANJABI_1991_FULL_fixed.pdf`; p. 892 is PDF page 7, a scan with no text layer (read by eye). Table 3 EPWu T11 34.9+/-0.97, T12 39.0+/-0.58; VBHp T11 21.3+/-0.71, T12 22.7+/-1.04 are in `morphometrics/make_reference_table.py` (THORACIC) and the level-atlas figure was regenerated. History below.

**Every scan on hand skipped p. 892** -- `MANUAL_REFS/panjabi1991.pdf` and
`paper/mpda/DUPLICATE_THORACIC.pdf` are byte-identical (861,004 bytes, MD5
d8c4b0ed411d0aa3); page 4 = 891, page 5 = 893. The likely cause is a defect in
**LWW's own scan**, which is what every library's Ovid subscription serves -- so
requesting "the PDF" from any library reproduces the gap. **Paper or microfiche
only.**

What p. 892 gates: Table 3 (thoracic vertebral body + **endplate** dimensions).
Table 4 (canal SCW/SCD, p. 893) and Table 5 (pedicle PDW, p. 894) are already
transcribed into `morphometrics/level_references.csv`.

Verified holdings (each library's own catalog, not WorldCat -- its holdings APIs
are closed):
- **EMU, Ypsilanti (~30 mi)** -- **microfiche**, 2nd Level West, run v.15(1990)-v.22(1997).
  Best option: a fiche image is independent of the LWW scan. Call first.
- **U-M Ann Arbor (~36 mi)** -- Offsite Shelving, holdings `1-16,18-32 : 1976-2007`.
  Barcode **39015023202016** = v.16 1991 Jun-Oct. Non-affiliates request 3 business
  days ahead (http://umich.qualtrics.com/jfe/form/SV_7aFL2k4gFKSBJHf), collect at
  Hatcher (not Taubman). No-account overhead scanner in Hatcher North; bring USB.
  U-M also licenses **Journals@Ovid Complete, 1976 vol. 1-**.
- **MSU (~78 mi)** -- RD768 .S67, Remote Storage, `v.16 no.5,7-8 1991`.
- **NLM** -- W1 SP47, but DOCLINE is library-to-library only; Loansome Doc retired 2019.

Ruled out: **Detroit Public Library** (confirmed not held), U-Detroit Mercy, Macomb CC,
**WSU** (see [[wsu-library-access-cutoff]]). Sladen (HFH) and Corewell Royal Oak
catalogs list *no serials at all*, so their silence proves nothing -- Corewell Royal Oak
(248-898-1750) has a documented print collection + photocopier and is the only
plausible same-day metro-Detroit hit. MeLCat exposes only `v.16 Suppl.10`.
