# Spine imaging datasets on Chinese dataset hosts

Source: the thread "Dataset census and roadmap", 2026-10-23: the owner's ask of 16:31 UTC to run
the search made that morning for the CM Spine set (cm-spine-dataset-provenance.md, section 4) for
the other datasets the registry can only ask for by letter, form or account, since a set that was
published on a Chinese host, or under a Chinese name, is missed by a search in English alone. The
search ran on the owner's own computer through a Remote Control session, read-only, because the
cloud session's proxy refuses the Chinese hosts; its raw answers and its summary are in the Desktop
folder opendatalab-search-2 there, outside any repository. The registry's side of the same ask, the
answers to the letters, is spine-datasets #222.

## 1. The question

Sixty of the registry's 165 records reach their source by a letter, a form, an account, an
agreement or the owner's hand, and 51 of them are not on the grid: intraoperative and
interventional sets held by one hospital or one group (Huashan, PUMCH, Chongqing, Taipei Veterans,
Johns Hopkins' LevelCheck, Bournemouth's quantitative fluoroscopy, Pittsburgh's swallow studies,
Daradia's vertebroplasty, Mayfield, Inselspital, Maastricht, Vanderbilt, Jefferson, Warangal,
Seattle Science), the chest, PET and whole-body sets behind a credentialed account, and the cohort
films (MrOS, SOF). Several were made in China or
Taiwan and published, if at all, with a Chinese name. The question is whether any of them, or a
copy of any of them, sits on a dataset host the registry's English-language sweeps never read:
OpenDataLab (Shanghai AI Lab), ModelScope, Baidu AI Studio, Alibaba Tianchi, Heywhale, Hyper.ai
and Science Data Bank, with Hugging Face read again with the same words for comparison.

## 2. How it was searched

The rules of the run: log in nowhere, accept no terms, download no dataset file; search APIs and
metadata only; a pause of about a second between requests; PowerShell, since the computer's
python3 is the Store stub. Four parts:

1. OpenDataLab's keyword search, POST https://opendatalab.com/api/datasets/list with the JSON
   body {"backend":false,"keywords":"<word>","pageSize":100,"pageNo":1,"state":["online"]}
   sent as UTF-8 bytes, the call its Python SDK makes; the hit count is data.selected (data.total
   is the whole catalogue, 5,452), the records data.list, further pages read only while
   data.selected exceeded what was read and at most five a keyword. 109 English keywords: the
   holders and their cities (Huashan, Fudan, PUMCH, Peking Union, Xiehe, Chongqing, TVGH, Taipei
   Veterans, Johns Hopkins, Bournemouth, Pittsburgh, Mayfield, Inselspital, Maastricht,
   Vanderbilt, Jefferson, Warangal, NIMS, Seattle Science, Daradia, Breen, Faubel, Konica), the
   sets' own names (SX-Stitch, IRI-VFI, SpineXR, LevelCheck, Harms, BORDaR, DMX, PainSource,
   MrOS, Radiopaedia, AbdomenAtlas, CheXpert, MIMIC-CXR, PadChest, BRAX, VinDr, ReXGradient,
   BIMCV, Open-i, Indiana chest, NLST, LIDC, Merlin, INSPECT, MAGIC-CT, CAMS-Knee, Veriserum,
   Guide3D, FracAtlas, COBRA, CADICA, ARCADE, XCAD, NHANES, VertXNet, ENHANCE.PET, Procedure
   Guide, ScienceDB, Science Data Bank), and the subjects (stitching, stitch, whole spine, full
   spine, pediatric interventional, ankylosing spondylitis, whole-body PET, FDG, quantitative
   fluoroscopy, swallow, videofluoroscopy, VFSS, dysphagia, vertebroplasty, kyphoplasty,
   myelography, flexion-extension, cervical, dynamic digital radiography, motion X-ray,
   arthroplasty, THA, hip, DRG stimulation, 2D-3D registration, coupling, osteoporotic fractures,
   Genant, lateral spine, osteoporosis, coronary angiography, DDH, hip dysplasia, canine,
   veterinary, scoliosis, cephalometric, interventional radiology, DSA, angiography, PET/CT,
   knee, chest X-ray, CXR, intraoperative, surgical navigation, radiograph). 55 Chinese keywords,
   given here in pinyin with their meaning since the repository holds ASCII: Huashan Yiyuan
   (Huashan Hospital), Fudan, Xiehe Yiyuan (Union Hospital), Beijing Xiehe (Peking Union), pinjie
   (stitching), quan jizhu (whole spine), Chongqing, ertong (children), xiao'er (paediatric),
   jieru (interventional), Taibei Rongzong (Taipei Veterans General Hospital), Rongmin Zong
   Yiyuan (Veterans General Hospital), Taiwan, qiangzhixing jizhuyan (ankylosing spondylitis),
   Kexue Shuju Yinhang (Science Data Bank), tunyan (swallowing), tunyan zaoying (videofluoroscopic
   swallow study), zaoying (contrast imaging), xueguan zaoying (angiography), guanzhuang dongmai
   (coronary artery), guanmai (coronary), shuzi jianying (digital subtraction), xi guanjie (knee
   joint), kuan guanjie (hip joint), kuan guanjie fayu buliang (developmental dysplasia of the
   hip), jisui zaoying (myelography), jingzhui (cervical spine), xiongzhui (thoracic spine),
   dizhui (sacral spine), dongtai (dynamic), qushen (flexion-extension), xiongpian (chest film),
   xiongbu X xian (chest X-ray), zhuiti chengxing (vertebroplasty), houtu chengxing
   (kyphoplasty), guanjie zhihuan (arthroplasty), touying celiang (cephalometry), guzhi shusong
   (osteoporosis), zhengcewei (AP and lateral views), quanshen (whole body), zhengdianzi
   (positron), quan (canine), gou (dog), shouyi (veterinary), fei (lung), leigu (rib), yaozhui
   shoushu (lumbar spine surgery), shoushu daohang (surgical navigation), peizhun (registration),
   erwei sanwei peizhun (2D-3D registration), pingpian (plain film), shuzihua X xian (digital
   radiography), DR yingxiang (DR images), yixue yingxiang (medical imaging), shujuji (dataset).
   The API splits a Chinese keyword into its characters, so a broad word matches thousands of
   unrelated records; what matters is that a record carrying the word is never missed.
2. OpenDataLab's single-dataset lookup, GET
   https://opendatalab.com/api/datasets/<name>?backend=false, for 51 exact names (SpineXR,
   VinDr-SpineXR, TVGH-SpineXR, CheXpert, MIMIC-CXR, PadChest, BRAX, VinDr-CXR, VinDr-PCXR,
   ReXGradient-160K, BIMCV-COVID19, Open-i, NLST, LIDC-IDRI, CT-RATE, AbdomenAtlas, FracAtlas,
   CAMS-Knee, MAGIC-CT, Veriserum, Guide3D, CADICA, ARCADE, XCAD, NHANES,
   VFSS2022, IRI-VFI, SX-Stitch, LevelCheck, DeepFluoro, TotalSegmentator, SpineWeb, Spine-Web,
   xVertSeg, CSI2014, AASCE2019, AASCE, BUU-LSPINE, BUU_LSPINE, Sunnybrook, UWSpine, ISBI2015,
   CEPHA29, Aariz, MURA, GRAZPEDWRI-DX, ENHANCE-PET, AutoPET, OAI, MedPix, ROCO); an answer whose
   data.id is 0 means no dataset of that name.
3. Hugging Face, GET https://huggingface.co/api/datasets?search=<word>&limit=500, for 75 words:
   the anatomy and the modality (spine, spinal, vertebra, vertebrae, scoliosis, lumbar, cervical,
   thoracic, fluoroscopy, fluoroscopic, fluoro, c-arm, carm, radiograph, radiography, x-ray, xray,
   swallow, vfss, dysphagia, angiography, coronary, dsa, myelography, knee, hip, ddh, pet-ct,
   chest, cxr, nhanes, osteoporosis, fracture, cephalometric, canine, veterinary, intraoperative,
   surgical, stitching) and the holders' and sets' names (huashan, pumch, tvgh, chongqing,
   levelcheck, mros, radiopaedia, deepfluoro, spinexr, vindr, mimic-cxr, chexpert, padchest, brax,
   rexgradient, bimcv, open-i, nlst, lidc, merlin, inspect, magic-ct, cams-knee, veriserum,
   guide3d, fracatlas, cobra, cadica, arcade, xcad, abdomenatlas, ct-rate, totalsegmentator,
   verse, ctspine1k, mrspineseg). The search matches dataset ids, so a set whose id carries none
   of these words is found only through its description.
4. The other Chinese hosts, best effort within twenty minutes: ModelScope (modelscope.cn), Baidu
   AI Studio (aistudio.baidu.com), Alibaba Tianchi (tianchi.aliyun.com/dataset), Heywhale
   (heywhale.com), Hyper.ai (hyper.ai/datasets) and Science Data Bank (scidb.cn), each searched
   through whatever page or endpoint it answers without a login, for the core words jizhu and
   jichui (spine), zhugu (vertebra), yaozhui (lumbar spine), jingzhui (cervical spine), jizhu
   cewan (scoliosis), toushi (fluoroscopy), C bi (C-arm), shuzhong (intraoperative), X guang and X
   xian (X-ray), and spine, vertebra, scoliosis, fluoroscopy, C-arm, X-ray and radiograph.

## 3. What OpenDataLab holds

All 316 keyword requests answered (the 164 keywords with their further pages). They returned 2,475
distinct datasets, of which 217 carry one of the relevance terms the report was told to look for
(spine, vertebra, scoliosis, fluoroscopy, C-arm, radiograph, X-ray, DXA, swallow, angiography,
myelography, knee, hip, PET, cephalometry, canine, chest, NHANES, osteoporosis, fracture,
orthopaedics, kyphoplasty, vertebroplasty, stitching, intraoperative, navigation, registration,
paediatric and interventional, in English and in Chinese) and 50 are spine, X-ray or radiograph
sets. The search matches word by word, so a large count is no exact hit: "Science Data Bank"
matched 1,461 records on its three words. The spine sets the catalogue holds are the ones the
CM Spine search found that morning, MRI and CT: CTSpine1K, VerSe, xVertSeg, CSI 2014 (vertebra
localisation and segmentation), MRSpineSeg, IVDM3Seg and Lumbar Spine MRI, and the one
fluoroscopy set is DeepFluoroLabeling-IPCAI2020, the hip and pelvis set the registry holds as
deepfluoro. No spine radiograph set is there, and none of the request-route sets (LevelCheck,
SX-Stitch, IRI-VFI, the TVGH and Huashan sets, VFSS2022, MrOS, BORDaR, Daradia) appears under its
English or its Chinese name.

## 4. The exact names

Of the 51 names, seven exist on OpenDataLab, each with its id: CheXpert 5382, MIMIC-CXR 3985,
BRAX 4576, NLST 5181, LIDC-IDRI 2277, xVertSeg 5760 and MURA 5426. The other 44 answer id 0, no
such dataset: LevelCheck, SX-Stitch, IRI-VFI, VFSS2022 and every spelling of SpineXR among them.
The seven are public sets the registry already records from their holders (CheXpert, MIMIC-CXR,
BRAX, NLST and LIDC-IDRI; MURA and xVertSeg are not spine radiographs); whether OpenDataLab mirrors
their files or only points at the holder was not read, and the registry takes each from its holder
under the holder's terms in any case, since a catalogue's copy of a credentialed set grants
nothing.

## 5. Hugging Face

The 75 words returned 2,870 distinct dataset ids; 1,113 match a relevance term and 144 name the
spine, fluoroscopy or radiographs. None is one of the request-route sets. Five are worth a line,
each read again from the session through the Hub's API on 2026-10-23:

- MartialTerran/Cervical_Spine_X-ray_Atlas_CSXA_V3.0 (made 2025-09-30): a copy of CSXA, the
  Cervical Spine X-ray Atlas of Ran et al. (Science Data Bank, doi 10.57760/sciencedb.15391), as
  two zips of the 4,963 PNGs and the 4,963 JSON annotations, put there because the release's
  GitHub site answers 404 and Science Data Bank gives no direct download. The registry holds CSXA
  from Science Data Bank already (datasets/csxa.json, on the grid), so nothing follows.
- Borel237/vindr-spinexr-npz (made 2026-07-20): a README and no files. VinDr-SpineXR is held under
  PhysioNet's credentialed licence, and a repack elsewhere would be no route to it anyway.
- LStriving/Videofluoroscopic_Swallowing (made 2025-06-23): a README and no files; it adds nothing
  to the swallow sets the registry records (DysphagiaBank, Pittsburgh, VFSS2022).
- benjamindkilleen/fluoroseg: FluoroSeg, about three million simulated X-ray images rendered from
  CT with organ and tool masks and text pairs, the data behind FluoroSAM (Killeen et al., MICCAI
  2025, arXiv 2403.08059), CC BY-NC-SA 4.0 behind a click-through gate, about a thousand zips named
  by CT and scene. A simulated set, not an imaging dataset, so it is no record of the registry;
  whether the owner wants it is the owner's call.
- Silversorrow/SpineBench: 40,263 spine images with question and answer pairs, known from the
  CM Spine search.

## 6. The other Chinese hosts

Nothing from intraoperative C-arm or fluoroscopy of the spine is on any of them; their spine sets
are MRI and CT. Host by host:

- ModelScope answered its search: two small lumbosacral CT segmentation samples and a cephalogram
  set; no spine X-ray.
- Baidu AI Studio answered: lumbar MRI and CT sets (CTSpine1K's lumbar crops), hand bone-age
  X-rays, chest X-ray and security X-ray sets; no fluoroscopy.
- Alibaba Tianchi refused the script's requests (403, a missing csrf token) but answered through
  its public page in the browser, at most ten results a search: dataset 79463, the spine-disease
  challenge (jizhu jibing shujuji, "spine disease dataset", lumbar MRI), and copies of MURA and
  chest X-ray sets.
- Heywhale searches titles only: a scoliosis spine CT set (jizhu jisuanji duanceng saomiao, jizhu
  cewan, "spine computed tomography, scoliosis"), a disc herniation set, lumbar disc coordinates
  and knee X-rays.
- Hyper.ai, first page of cards only: VerSe, a multi-region fracture X-ray set, MURA and chest
  X-ray sets.
- Science Data Bank's search is loose, so the run read the top 100 results a word and then 17
  targeted phrases. It gave four records on the spine or X-ray, each read again from the session
  through DataCite's record of its DOI and the page's own meta tags (the page is a JavaScript
  shell): CSXA (above, held); "10-case CT and X-ray DICOM dataset for 2D-3D registration" (doi
  10.57760/sciencedb.32821, Zixuan Qin, Northeast University, issued 2025-12-05, CC BY 4.0, 5.37 GB
  in one file, ten anonymised cases each with one CT volume and several fluoroscopy frames in
  DICOM; its subjects are head, 2D-3D registration and style transfer, so it is a head set and not
  the spine); "Vertebrae" (zhugu; doi 10.57760/sciencedb.27226, Jiangzhou, Xiamen University,
  issued 2025-09-02, CC BY-NC 4.0, 828 GB in 249 files, no description, subjects biology, liyu
  (carp), yu (fish) and zhugu (vertebra): fish vertebrae, not a spine imaging set); and MTDDH
  (doi 10.57760/sciencedb.24372, Qi, Jiao, Li and others, Children's Hospital of Zhejiang
  University School of Medicine, issued 2025-04-29, CC BY 4.0, 4.05 GB in three files), 1,250
  paediatric pelvic X-rays annotated with four regions for image quality and eight key points for
  developmental dysplasia of the hip and 906 more with the eight key points. MTDDH is the one new
  set for the registry, beside the Mendeley DDH hip sets it already lists, for the same reason:
  the lumbosacral junction is in the field of a pelvic film. A foot X-ray angle set (HVAngleEst,
  sciencedb.19819) is not.

Two more leads came out of the run. The Johns Hopkins hip-surgery cadaver deposit (doi
10.7281/t1/c304hz, Grupp, Unberath, Armand and Taylor, 2,659 fluoroscopy frames and 19 CTs from six
cadavers) is DeepFluoro's vendor DICOM deposit, which the registry holds (datasets/deepfluoro.json).
An OSF project, "AI for automatic vertebrae motion tracking in fluoroscopic images" (doi
10.17605/osf.io/z2jby), reads like the Bournemouth quantitative fluoroscopy group's work; OSF's
pages are a JavaScript shell and its API is closed to the session (robots and the proxy), so what
the project holds is for the owner to open; if it holds image data the Bournemouth records change.

## 7. What it means for the registry

None of the sets the registry asks for by letter, form or account is on any host searched, under
its English or its Chinese name, so the letters, the forms and the introductions stay the way to
them; spine-datasets #222 records the answers that had come by 2026-10-23. The search adds one
record, MTDDH (spine-datasets, with this note), and changes no other. Nothing was fetched and no
fetch is asked for: MTDDH waits, like the registry's other Science Data Bank set, on the owner
reading whether the site asks for a login and on a fetch route for Science Data Bank
(answered later that day: no login; section 9).

## 8. What was not searched or was cut short

- CSXA was not in Science Data Bank's top 100 for "spine" and was found only through the Hugging
  Face copy, so a record of the same kind can still be buried there; the 17 targeted phrases were
  the run's answer to that, within the time it had.
- Hyper.ai gave the first page of cards only, Heywhale searches no descriptions, Tianchi gives ten
  results a search, and the other-hosts part ran past its twenty minutes on the Science Data Bank
  phrases.
- Whether OpenDataLab mirrors the files of the seven sets it lists was not read.
- OSF (z2jby) could not be read from the session; the owner's paste answered it (section 9).
- The raw answers and the run's own summary are on the owner's computer, in the Desktop folder
  opendatalab-search-2 (odl, odl_get and hf with every answer, odl_relevant.csv, hf_relevant.csv,
  hf_all_ids.txt, other_relevant.csv, other_counts.csv, other/tianchi_results.json, the scripts
  and SUMMARY.md), outside any repository; the cloud session cannot open that folder while a
  Remote Control session runs, and had no need to after the run reported.

## 9. What the owner's pages answered, later on 2026-10-23

The owner opened the two pages the session could not and pasted them into the thread, and a second
Remote Control session read the file lists on the owner's computer, where the answers are in the
Desktop folder dataset-links.

- OSF z2jby is the Bournemouth group's deposit for the MRC grant MR/X005372/1, "AI for automatic
  vertebral motion tracking of fluoroscopic images" (UKRI Gateway to Research, pasted by the owner:
  Bournemouth University, Faculty of Science and Technology, principal investigator Marcin Budka,
  65,073 pounds, August 2022 to February 2023, closed), which worked on the quantitative fluoroscopy
  database Professor Breen's team had collected over years of earlier research, whose participants
  consented to future research use, with an independent sample from the Royal Hampshire County
  Hospital as a check. The project is public, made 2023-02-15 by Rantilini Samaratunga with
  Alexander Breen, Alan Breen and Marcin Budka, DOI 10.17605/OSF.IO/Z2JBY, no licence stated
  (node_license null), no description beyond the grant line, and three files in OSF Storage. Its
  code is the GitHub repository dsibournemouth/project-maid (GPL-3.0, six commits, two inference
  notebooks and two Python files), whose README says the image dataset (1.4 GB) and the pre-trained
  models are downloaded from the OSF project, and whose two sample GIFs (WB_FLEX-NS048, clean and
  obstructed) are lateral lumbar fluoroscopy frames of 224 by 224 pixels with five tracked vertebral
  boxes, weight-bearing flexion; the paper is Samaratunga, Budka, Breen and Breen, "Automatic
  detection of the lumbar spine using transfer learning for Quantitative Fluoroscopy", Procedia
  Computer Science 2025, vol. 270, pp. 2291-2300 (doi 10.1016/j.procs.2025.09.350; a TechRxiv
  preprint of 2024-03-04), on sagittal lumbar fluoroscopy sequences; the grant page also lists
  "Automated Lumbar Spine Tracking in Quantitative Fluoroscopy" as in preparation. The files, read
  through OSF's API (api.osf.io/v2/nodes/z2jby/files/osfstorage/) on the owner's computer:
  preproc_224_wb_flex.zip, 1,492,963,815 bytes, uploaded 2023-02-20, sha256
  b43de4c185dd751ed2e3e04d75e8eef10aa6c3e09bf4393accffbecd6805bb26, download
  https://osf.io/download/xjt4f/; rn50-224-wb-flex-50ep-bs500.pth, 383,648,577 bytes, 2023-02-21;
  and shape-rn50-224-wb-flex-38ep-bs500.pth, 459,107,325 bytes, 2023-03-13; no folders. So the image
  set is the weight-bearing flexion frames preprocessed to 224 pixels, a subset of the 2021
  database, and the two .pth files are the paper's ResNet-50 weights. Each osf.io/download link
  answers with no login (a 302 to files.de-1.osf.io, whose HEAD gives 200 with the same size, then a
  60-second presigned object-storage address, so a manifest keeps the osf.io/download form). The
  lumbar record says so (spine-datasets #224). Dr Branney is checking with his research department,
  and the owner chose not to chase him with a question about the deposit's terms; they are asked
  when he answers. Since OSF states no licence, the registry's promoter cannot take the deposit
  until Bournemouth's grant is recorded (spine-datasets manifests/README.md).
- MTDDH downloads from Science Data Bank with no login: the owner downloaded it on 2026-10-23 with
  no account. The paper is Qi, Jiao, Li and others, "A dataset for quality evaluation of pelvic
  X-ray and diagnosis of developmental dysplasia of the hip", Scientific Data 2025 (doi
  10.1038/s41597-025-05146-x, PMC12106846): one film per child, ages 5 to 40 months, file names
  randomised; the first part 1,250 children (781 girls, 469 boys, mean age 14.6 months), JPG in
  Training, Validation and Test folders with JSON annotations for the first two, and a segmentation
  part of the same shape without a test split, the four quality regions being both obturator
  foramina and both ilia; the second part 906 children (558 girls, 384 boys, mean age 14.3 months),
  PNG with COCO-format annotations; three paediatric orthopaedic surgeons annotated; the hospital's
  ethics committee approval 2023-IRB-0287-P-01 waived consent and approved the public release; the
  corresponding authors are Guoqiang Zhao and Gang Yu (Zhejiang University). The same authors posted
  MTDDH.rar (1,871,869,324 bytes, CC BY 4.0, 2024-12-11, doi 10.6084/m9.figshare.27999131.v1, served
  from ndownloader.figshare.com; figshare's API gave no md5) five months before the Science Data
  Bank version the paper cites (V1, 2025-04-29, 4,053,482,052 bytes in three files), so the figshare
  copy is an older and smaller fallback, and a Kaggle re-upload (amirmmahdavikia/mtddh-pelvic-x-ray)
  is a third party's and not a source. Science Data Bank's page is a Nuxt shell whose API base is
  www.scidb.cn/api: the dataset details endpoint (sdb-dataset-service/dataset/details) answers
  "PERMISSION NO ACCESS" without a login, but the public ones carry everything: gin-sdb-
  croissant/public/getCroissant gives the record as Croissant JSON-LD (conditionsOfAccess PUBLIC, CC
  BY 4.0, version 1.0.0, 2025-04-29, 4,053,482,052 bytes), POST gin-sdb-
  filetree/public/file/childrenFileListByPath with the dataSetId, version V1 and path /V1 gives the
  file list, and sdb-filetree-service/getAllUrl gives one download address a line. The three files,
  each a plain download from download.scidb.cn with no login (HEAD 200 with the same Content-Length,
  a Range request 206, no redirect): JPG_DICOM.rar, 1,165,024,411 bytes, md5
  2029b761e5077e61280f4a5fb9308a32, fileId 6598e44aa54eb418af5add89c199fd9f; MTDDH.zip,
  1,872,032,279 bytes, md5 1508164e97c35b7063a163726bf4ef05, fileId
  c4ecee1aec98deb8327888bce3e07901; and code.zip, 1,016,425,362 bytes, md5
  a91952a0f1b6fc0989e8a1d53cd0432e, fileId b4c4789e608dc5f66e654b47f072d5f1, each at
  https://download.scidb.cn/download?fileId=ID&path=/V1/NAME&fileName=NAME; no sha256 is published.
  The figshare rar carries supplied_md5 697c3c29b6a1faf69a2032e22486400e and is not the same archive
  as MTDDH.zip. The manifest and the record's fetching status wait on the owner's word, since the
  promoter fetches a merged manifest, and on the promoter learning download.scidb.cn as a host
  Science Data Bank serves files from, a one-line change to tools/promote.py that reaches the grid
  only through the owner's gate word.

## 10. Read

OpenDataLab's search and lookup APIs and Hugging Face's dataset API from the owner's computer;
from the session, Hugging Face's /api/datasets/<id> for the five ids above, DataCite's records of
the three Science Data Bank DOIs, scidb.cn's page meta tags for the same three, and the
registry's records csxa, deepfluoro, ipcai2025_xray_ct, vfss2022, dysphagiabank,
mendeley_ddh_hips, vindr_spinexr and scidb_enhance_pet_1_6k.
