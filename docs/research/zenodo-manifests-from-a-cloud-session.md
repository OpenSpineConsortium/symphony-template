# Zenodo manifests from a cloud session

Source: the thread "Open CT dataset downloads" in the project symphony_2, 2026-10-22. The work is
spine-datasets #140, #161, #162 and #163 (issues #55 to #58).

## What was done

Four CT sets in spine-datasets' queue are on Zenodo under CC BY 4.0, with no non-commercial or
no-derivatives term, so the promoter may fetch them on the owner's merge alone. Each got a manifest
listing every file of its Zenodo record with its exact byte count and md5, and its record moved to
fetching:

| Task | Set | Zenodo record | Files | Bytes |
| --- | --- | --- | --- | --- |
| #55 | LumVBCanSeg | 8181250 | 1 | 10,075,438,693 |
| #56 | MedPelvis3D | 21757686 | 100 | 31,351,310,903 |
| #57 | International TMTV Benchmark | 13255214 | 5 | 6,846,084,599 |
| #58 | UniToChest | 5797912 | 2 | 84,067,545,368 |

MedPelvis3D's record now holds about twice what the registry noted (15.1 GB): per-case zips, the
combined NIfTI parts, meshes, point clouds and samples. The manifest takes the whole record, so the
shared copy matches the publisher's and nobody has to guess which half is canonical.

VSDFullBody (#59) is also on Zenodo but its record's text says CC BY-NC-SA, so the review refuses
its manifest until the owner records a grant; it was left alone.

## How the file lists were read

tools/dataset_review.py's `manifest --zenodo N` reads Zenodo's API, which a cloud session cannot
reach: the container's proxy refuses zenodo.org outright, and the web fetch tool is refused at
zenodo.org/api/ by the site's robots.txt. The record's export page,
`https://zenodo.org/records/N/export/json`, is allowed and carries the same file list with exact
sizes and md5s. The fetch tool hands the page to a small model that answers a prompt, so a long
list is a transcription: MedPelvis3D's 100 lines were read twice in separate fetches and the two
copies compared identical before use. Zenodo rate-limits the fetch tool hard after two or three
pages in a row; one page every few minutes went through.

A slip would cost a retry, not a wrong copy: the promoter installs a file only when its size and md5
match the manifest, and removes a whole but wrong file so the next pass starts it again.

## The link to use

Each file's link is `https://zenodo.org/api/records/N/files/<key>/content`, the key
percent-encoded (TMTV has a file name with spaces). The export's own `links.self` drops `/content`
and answers with the file's JSON description, not its bytes, so it must not be copied as is.
The review's tests use the same `/content` form.
