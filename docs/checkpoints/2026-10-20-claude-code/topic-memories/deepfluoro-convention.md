---
name: deepfluoro-convention
description: "DeepFluoro (IPCAI 2020) file layout and projection convention, settled by 0.00 px reprojection on 2026-09-21 -- (z,y,x) volume, ext@inv(T), rot-180 not applied to landmarks, transmission-like image"
metadata: 
  node_type: memory
  type: reference
  originSessionId: f1bdbd78-151f-470b-b703-dd9af9b3fecc
  modified: 2026-09-21T04:21:49.658Z
---

DeepFluoro full-res is `~/deepfluoro/unpacked_full/ipcai_2020_full_res_data.h5` on the grid (2.5 GB
zip fetched with `tools/dl_deepfluoro.py`, see [[cloudflare-tls-fingerprint]]). Six specimens keyed
`17-1882, 17-1905, 18-0725, 18-1109, 18-2799, 18-2800`, 366 projections total, plus `proj-params`.

**What each specimen holds:** `vol/pixels` HU float32 **indexed (z,y,x)**, 1 mm isotropic, identity
dir-mat, `origin` (x0,y0,z0) mm; `vol-seg/image/pixels` same grid, 7 classes
`1 left-hemipelvis, 2 right-hemipelvis, 3 vertebrae (ONE merged class, 90-112 mm ~ 2-3 lumbar
levels), 4 upper-sacrum, 5 left-femur, 6 right-femur, 7 lower-sacrum`; `vol-landmarks` 14 pelvic
points in world mm (FH, GSN, IOF, MOF, SPS, IPS, ASIS, l/r -- **no spinal landmark**). Each
`projections/NNN` has `image/pixels` 1536x1536 float32 at **0.194 mm/px**, `gt-seg/pixels` 2-D uint8,
`gt-landmarks` 14x(2,1) in (col,row) px, `gt-poses/cam-to-pelvis-vol` 4x4 mm (+ left/right femur and
`*-good-fov` flags), and `rot-180-for-up` (set on 39/111 of spec 1).

**The convention, settled by reprojection error rather than a README** (`tools/deepfluoro_convention.py`):
```
p_cam = ext @ inv(cam-to-pelvis-vol) @ p_vol        # ext is proj-params/extrinsic, REQUIRED
uv    = K @ p_cam / z                                # K = proj-params/intrinsic, focal -5257.7 px (keep the sign), pp 767.5
                                                     # (col,row); rot-180-for-up NOT applied to landmark coords
```
Median **0.00 px, p90 0.00 px** over 111 projections x 14 landmarks. The (z,y,x) index order was
decided by the segmentation label found at each landmark's index (6/6 correct vs 1/6 the other way, two
specimens) -- a range check on one landmark had said (x,y,z) by coincidence. Focal x 0.194 = **1020 mm
SID** (CIOS Fusion, flat panel, so no II distortion). The stored image is **transmission-like**
(bright = more photons), decided by correlating under both signs.

`tools/deepfluoro_render.py` ray-casts a polyenergetic DRR (repo's water/bone basis, no detector
physics) at any projection; frame 000 gives NCC +0.437 raw / **+0.491** attenuation-space (floor at p2,
not min -- min+1 let the collimated border swamp it to -0.03), landmarks coincident, checkerboard edges
continuous. `slurm/deepfluoro_pairs.sh` renders all 366 (DRR, real, seg) triples to
`~/model_night/deepfluoro/pairs/` -- the fitting set for a learned image-formation model and the first
real-fluoro pixel-for-pixel validation target the renderer has had.

The 8x package (`ipcai_2020_ds_8x.h5`) is a different layout: per-specimen `projs/segs/lands`
(N,180,180), no CT, no poses. See [[drr-to-fluoro-levers]], [[fluorocap-is-reproductions-not-fluoroscopy]].
