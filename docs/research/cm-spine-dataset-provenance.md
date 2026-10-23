# Where the CM Spine images went

Source: the thread "Dataset census and roadmap", 2026-10-23: the owner's ask to find a public copy
of the CM Spine set and to audit the trail it left, with two uploads, the paper's PDF (Zeng et al.,
Electronics 2024, 13, 2137) and src.zip, the src/ directory of the paper's repository as Software
Heritage archived it, and the links the owner gave: the Wayback capture of 2024-05-30, the Software
Heritage snapshot d76722e92435ccbd0a52ba0ceafd914a7b040c65 at revision
d42f5acba252e0de1e33190b3d6c61f2ef9d523e, the Google Drive file 1r9wX1802gkU4-EQHMMlyAlEiWXGWLhhJ,
GH Archive and the paper's page. The record is spine-datasets' datasets/cm_spine_drive_file.json and
the letter letters/cm_spine_drive_file.md (spine-datasets #220). What was read is in section 7, and
what the session could not read, in section 8.

## 1. The question

Find a mirror of the 208 images, and audit the trail the set left on the way. The audit covers the
dataset and its repository: where the set was published, what survives, who holds it and how to
ask. It reads the author's public record no further than the repository and the addresses the paper
prints, which is what a request needs.

## 2. What the paper says

- Zeng, Wang, Dai, Wang, Xiong, Xiao, Cai, Zhang, Sun, Cheng and Song, "Exploring Neighbor Spatial
  Relationships for Enhanced Lumbar Vertebrae Detection in X-ray Images", Electronics 2024, 13(11),
  2137, received 1 April 2024, published 30 May 2024, CC BY 4.0 for the paper. The corresponding
  authors are Erkang Cheng (ekcheng@iim.ac.cn) and Bo Song (songbo@iim.ac.cn), Institute of
  Intelligent Machines, Hefei Institutes of Physical Science, Chinese Academy of Sciences; the first
  author is Yu Zeng (yzeng@iim.ac.cn), School of Biomedical Engineering, Anhui Medical University
  and the same institute. The paper prints every author's address.
- The set (section 4.1): "We use a mobile dual-mode G-arm X-ray machine (Geelin500-A) to collect 208
  1024 x 1024 lumbar spine X-ray anterior view images during surgical procedures", focal spot
  0.6 mm, target angle 10 degrees, "from patients suffering from lumbar disc herniation or vertebral
  compression fractures", 148 for training and 60 for testing, L1 to L5 annotated, 537 vertebrae in
  all, with Table 2 counting the level combinations. No hospital, no dates, no ethics approval.
- The Data Availability Statement, in full: "Our code and data are available at
  https://github.com/zengyuyuyu/Neighbor (accessed on 19 March 2024)."
- The back matter holds Author Contributions, Funding (NSFC 61973294, the Anhui Provincial Key R&D
  Program 2023s07020017 and 2022i01020020, GXXT-2021-030, and the Anhui Provincial Key Laboratory of
  Bionic Sensing and Advanced Robot Technology), the Data Availability Statement and Conflicts of
  Interest. There is no Institutional Review Board statement and no Informed Consent statement.

## 3. The repository's trail, in order

- 4 to 18 March 2024: the dates of the project's own files in the archived src/ (coco_cp.py,
  ctdet.py, decode.py, losses.py, main.py and the rest); the files taken from CenterNet are dated
  6 December 2022. The archive is CenterNet's tree with the paper's changes: 90 Python files, the
  loaders for COCO, KITTI and Pascal, the DCNv2 operator and a compiled nms extension. The loader
  that reads the set, src/lib/datasets/dataset/coco_cp.py, expects data/coco/train2022 and val2022
  with annotations/spine_train.json and spine_val.json in COCO form, so the Drive file most likely
  held the images and two COCO files. No image, label, README, licence or citation file is in the
  archive, and the repository's root held src/ and README.md only.
- 19 March 2024: the paper's access date for the repository.
- 30 May 2024: the Wayback capture the owner linked, the day the paper came out. The README it
  holds, as the owner's summary and the page's last rendering give it: the paper's title, the two
  sets, CM Spine with the Drive link and BUU Spine with its page, and "follow CenterNet's
  installation and training instructions"; no licence and no address.
- 9 December 2025: Software Heritage's visit, the owner's link; the repository was public that day.
- 1 September 2026: the data platform's gdown of the Drive file left an empty directory
  (spine-datasets' record), which gdown does for a deleted file and for one it may not read alike.
- 23 October 2026: raw.githubusercontent.com answers 404 for README.md on main and on master and for
  src/main.py, while a control file on the same host answers; the profile page says the account
  "doesn't have any public repositories yet"; the Drive API answers "Requested entity was not found"
  to the owner's Google account, which Google answers for a deleted file and for one the account
  may not open alike. A fetch of the repository page still returned a rendering, 18 commits, 0
  forks, 0 stars, 1 watcher, main the only branch, no release, root src/ and README.md, which is a
  cache, since the files behind it are gone. So the repository was deleted or made private between
  9 December 2025 and 23 October 2026, and its 0 forks mean no copy stands under another name on
  GitHub.

## 4. Where a copy was looked for, and what was found

| Where | How | Found |
|---|---|---|
| The web | the set's name, the paper's title, the device, the author's handle, in English and Chinese | the paper and the repository, nothing else |
| The Drive id | the web; grep.app, over the part of public GitHub code it indexes, for the id and for spine_train.json | the repository's own page; 0 code hits |
| Zenodo | the records the search returned | LUMOS (18173664, osteoporosis X-ray and CT) and spineFE (15313259, CT); neither |
| Roboflow Universe | the search class:lumbar, 31 entries on its first page | the nearest, researchRun (206 images, one class "lumbar", February 2022, CC BY 4.0), predates the paper; L1-L5 Lumbar Crop (706 images) is a crop set; none is the set |
| Kaggle | the search's one vertebra X-ray set | scoliosis, spondylolisthesis and normal, a classification set; not the set |
| Dataset lists | the READMEs of openmedlab/Awesome-Medical-Dataset, adalca/medical-datasets, sfikas/medical-imaging-datasets, beamandrew/medical-data, linhandev/dataset and aaekay/radiology-datasets | none lists it; the spine X-ray rows are VinDr-SpineXR and the Mendeley vertebrae set |
| Surveys | arXiv 2510.03318 (lumbar spine, 2025), both halves | its dataset tables name no X-ray set of this kind |
| Papers citing it | OpenAlex, 3 works | Xie et al., CMIG 2025, a methodological survey (not read); Ben Fredj et al., YOLO11-MSCA, Electronics 2026, uses BUU-LSPINE alone and cites the paper in its reference list only; Xiao, Xiong and Wang, ITOEC 2025, the group's own, whose page could not be read |
| Forks | the repository's last rendering, a cache | 0; a fork made after that rendering would not show, and a fork of a deleted repository lives on under its own name |

So no public copy was found anywhere the session could read, and the set, as far as the public
record shows, was only ever the one Drive file.

## 5. What this means for the data availability statement

The statement promises code and data at the repository. The data were never in the repository;
the README linked a Drive file. Both are unreachable now, so the statement resolves to nothing.
MDPI's research and publication ethics page says "Raw data must be made publicly available, unless
there is a compelling reason otherwise (e.g., patient confidentiality)", asks authors who remove
data from a repository or change its access to "notify the Editorial Office as soon as possible",
and tells a reader with a concern to "first contact the corresponding author to attempt to resolve
the issue directly", then the form or publication.ethics@mdpi.com. The Electronics office is
electronics@mdpi.com (managing editor) and dme-electronics@mdpi.com. Whether the authors told the
office is not public. Patient confidentiality is the exception MDPI names, and the paper has no
ethics statement, so the authors may have withdrawn the set for that reason; the letter asks for the
terms and the approval, not only the files.

## 6. The route

1. Open the Drive link signed in to the owner's Google account. "You need access" offers Request
   access, one press that mails the file's owner, who is most likely the first author; "the file you
   have requested does not exist" means it is gone. The API cannot tell the two apart.
2. Send the letter in spine-datasets' letters/cm_spine_drive_file.md to Cheng and Song, Zeng in
   copy; it is also an Outlook draft in the owner's mailbox. It asks for the 208 images and labels,
   the terms, the ethics approval and the de-identification.
3. After two weeks without an answer: the Electronics editorial office, citing the Data Availability
   Statement, as MDPI's ethics page lays out.
4. The company beside the group: Chimed Intelligent Machinery Co. Ltd is a co-author affiliation on
   the group's ITOEC 2025 paper. Whether it makes the Geelin G-arm, and so holds the raw images, is
   not established; the maker's page on the Anhui association site (www.ahyyxh.cn, "Geelin500")
   could not be read from the session.
5. Software Heritage can give the whole revision, not only src/: on the snapshot page, Download >
   bare repository or tar.gz for the root directory. git log on it gives the 18 commits' dates and
   whether the README ever carried another link (a Baidu share, say); the session cannot reach the
   archive.
6. The hubs the session could not search: Google Dataset Search, OpenDataLab, Hugging Face datasets
   and Academic Torrents, each by "lumbar spine X-ray"; a hit with 208 images or the classes L1 to
   L5 would be worth opening.

## 7. Read

- The paper's PDF (the owner's upload) and its page at https://www.mdpi.com/2079-9292/13/11/2137
  (the Data Availability Statement, the funding, the back matter).
- src.zip (the owner's upload): its file list, dates, every URL, address and dataset path in it.
- The Google Drive API, as the owner's account, for the file's metadata.
- raw.githubusercontent.com for README.md on main and master and src/main.py, and a control file;
  the profile page and the repository page through the fetch tool.
- OpenAlex: the work W4399155220, its cited_by_count and the three citing works.
- https://www.mdpi.com/2079-9292/15/7/1341 (YOLO11-MSCA), https://www.mdpi.com/ethics and the
  Electronics editorial office page.
- grep.app's API for the Drive id and for spine_train.json; Zenodo records 18173664 and 15313259;
  Roboflow Universe's search and the researchRun page; the Kaggle page; the six dataset lists'
  READMEs; arXiv 2510.03318's HTML; the web searches of section 4.

## 8. Not readable from the session

web.archive.org and archive.org (blocked), archive.softwareheritage.org (a browser check, Anubis),
api.openalex.org and api.semanticscholar.org by curl (OpenAlex answers the fetch tool, Semantic
Scholar refuses it), api.crossref.org, gitee.com, huggingface.co, opendatalab.com (JavaScript),
academictorrents.com (a browser check), ieeexplore.ieee.org, www.ahyyxh.cn, GitHub's HTML pages
by curl and its commits and tree pages by the fetch tool (robots), and GH Archive by BigQuery (no
credentials). The GitHub API was not used, since the session's GitHub access is scoped to its own
repositories.
