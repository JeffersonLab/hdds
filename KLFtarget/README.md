# KLF LH2 target v2.0 — HDDS model (target, cryostat, cart)

Generated files (do not edit by hand; change the scripts and regenerate):

| file | made by | contents |
|---|---|---|
| `Target_HDDS.xml` (section Target, v3.0) | `build_target.py` | LH2 cell and target arm inside LASS |
| `TargetCryostat_HDDS.xml` (section TargetCryostat, v1.0) | `build_cryostat.py` | 6-way cross, internals, tower, entrance port, cryogenic lines, GlueX cart |
| `PairSpect_HDDS.xml` | `PairSpect_HDDS_xml.py` (copy of the repo generator) | pair spectrometer with its shielding moved upstream |
| `Material_HDDS.xml` | `make_materials.py` | repo materials + `materials_klf.xml` + `materials_scaled.xml` |
| `main_HDDS.xml` | by hand (copy of the repo file) | entity paths, KFM at hall z -1187.55, targetCryostat in experimentalHall |

Build order:

```
PY=/scratch/klf-geometry/lh2tgt/venv/bin/python
python3 PairSpect_HDDS_xml.py > PairSpect_HDDS.xml
$PY build_target.py Target_HDDS.xml
$PY build_cryostat.py TargetCryostat_HDDS.xml cryostat_report.json
$PY build_target.py Target_HDDS.xml        # again: picks up target_daughters.json
python3 make_materials.py
```

The CAD solids are fitted once by `/scratch/klf-geometry/lh2tgt/analyze_solids.py`
(about 25 s per solid; output `prims_*.json`), from the STEP assembly tree
recovered by `steptree.py` (`solids_named.json`).

## Sources

- **CAD.** J. Brock (TJNAF/SURATech), Inventor STEP AP214 `TGT-401-5000-0000 KLF Concept JBrock`,
  dated 2026-11-17, in `../liqH2-target/`.
- **How the CAD was read.** OpenCASCADE, through gmsh 4.15.2 in a scratch venv:
  - `/scratch/klf-geometry/lh2tgt/imp.py` gives the volume and bounding box of each solid.
  - `sect4.py` cuts each axisymmetric part with a plane through the axis, at φ = 0° and 90°.
  - `profile.py` turns the cut outlines into pcon planes.
  - `struts.py` gives the strut axes from the inertia tensor.
- **v2.0 decisions** (C. Keith, R. Jones; see `../LEDGER.md`, 2026-11-18 and 2026-11-19):
  - The cell is Al 7075 with a 0.5 mm wall and domed ends.
  - The cell dimensions are Chris's (the CAD): LH2 radius 2.8311 cm and the CAD LH2 length.
  - **Beam path clearance R_clear = 3.0 cm (6 cm beam):** nothing inside r < 3.0 cm except the cell (LH2, wall, domes) and the exit window.
  - G-10 has density 1.85 g/cm³.
  - "Generic" parts are aluminium unless there is a reason to think otherwise.
  - The Rohacell vessel is kept.

## Coordinates

- **CAD to LASS:** z_LASS = z_CAD/10 + 65.070 (target frame: + 14.870, placed at LASS z = 50.2).
- **Anchor:** the cross centre lands at LASS z = -105.96, where GlueX master has `SixWayCross`, and its downstream flange ends exactly at the LASS boundary (z = -72.0).
- **Earlier anchor:** the reference start counter (+66.715) put everything 1.645 cm further downstream; the two anchors agree to 1.0-1.6 cm, and the cross one keeps the hall/LASS split clean.

## Contents (48 volumes)

| HDDS | part | material |
|---|---|---|
| TARG | vacuum inside the vessel: the union of the outer wall surfaces, LASS z −69.80 … 84.76 | Vacuum |
| TGF1, TGF2 | flanges 0036, 0037 | StainlessSteel |
| TGB1 | 8" target-arm beam pipe 0038 | Aluminum |
| TGF3, TGF4, TGB2, TGF5, TGB3 | flange 0039, o-ring ring, chamber tube 0040, flange 0041, cone 0042 | Aluminum |
| TGRV | vacuum vessel 0043, 12.3 mm wall; downstream of LASS z 82.38 the bore is 3.0 cm (CAD 2.0) and the end is a cylinder r 3.24 to the window | MediumDensityROHACELL (0.075) |
| TGXW | exit window, 5 mil, r 3.0 cm, at the CAD z (LASS 84.74, 13 mm beyond the cell apex) | Kapton |
| TGBD | cell base (Al 6061): CAD outer profile, bore 3.05 cm; the cell lip is seated in it over 6.85 mm | Aluminum |
| TGCL / LIH2 | cell: cylinder r 2.8311 / 2.8811 cm (Chris's radius). At the upstream end the 0.5 mm wall flares at 45° out to a lip of r 3.00 / 3.05, closed by a convex-upstream entrance dome (the CAD inner sphere, R 6.016 cm). Hemispherical downstream dome. / LH2 inside it | Al7075 / LiqHydrogen |
| TGG1–TGG5 | G-10 rings 0005-0005, 0005-0006, 0021, 0029, 0028; the 0021 bore is opened from 2.86 to 3.33 cm, as in the other two spider rings | G10; G10ring21 and G10spider are scaled to the CAD mass, because the rings are drawn without their holes |
| TGR1–TGR4 | three SS support rods 0005-0010, Ø 6.35 mm; the segments inside rings are daughters of the ring | StainlessSteel |
| TGS1–TGS5 | two hexapods of six struts each, Ø 4.77 mm | CFRP (1.43, the CAD value) |

- **LH2:** 1039 cm³ (73.6 g), LASS z 40.94 … 83.42.
- **Cell:** wall, flare, lip and domes, 110 g.
- **Aluminium along rays parallel to the axis:**
  - r ≤ 2.5 cm: 0.10–0.16 cm (the two domes);
  - r 2.83–2.88: about 38.5 cm (the cell wall itself);
  - r 2.88–3.0: 0.13 cm (the flare and the dome edge).
- **Mass agreement:** within 3% of the CAD for every part not changed for the clearance; see `masses_stage1_2026-11-18.txt` (stage 1, before the shift).
- **New materials:** Al7075, G10, G10ring21, G10spider and CFRP, added at the end of the copy in `Material_HDDS.xml`.

## Not in stage 1

- **Upstream of LASS z −69.8:** the 6-way cross, the copper heat shields (including plate 0032 with its ~1" hole), the 6" openings and the expanded flange.
  - Several of these parts lost their names in the STEP import and are mixed with the reference GlueX target assembly, so they still have to be identified.
- **Cryogenic plumbing inside the beam pipe:**
  - copper bars 0017, 241 cm³;
  - SS tubes 0015 and 0016, flex hoses 0012 and 0018, about 15 VCR fittings, 0023, 0013/0014, 0024/0025 and the Omnetics connector;
  - two unnamed clamps at CAD z ≈ −570.
- **Small hardware:**
  - the support-rod bushings, springs and cups (3 × 8 cm³);
  - the 5000-0004 rods, which run into the cross;
  - polyimide blocks 0031 and SS 0005-0007;
  - screws.
- **Rohacell:** the CAD fillets are kept, simplified to 0.05 mm.

## Checks (2026-11-19)

- **Beam path:** `../tools/beam_clear.py main_HDDS.xml Target 3.0 -70 90 --allow LIH2,TGXW` finds nothing inside r < 3.0 cm over LASS z −70 … 90, apart from the cell and the window. The verify, overlap and flair checks were repeated on the flared-joint version.
  - The same check on the current repo target finds the FR-4 ring TGR1 and the Rohacell end CYLW.

- **FLUKA translation:**
  `hdds2fluka.py main_HDDS.xml --root Target --container-shape envelope -o tgt` gives 47 regions.
- **Independent check:**
  `verify.py ... --per-volume 20000 --uniform 1000000` passes on 1.96 M points.
- **Overlaps:**
  `../tools/subtree_check.py main_HDDS.xml Target --n 400000` (46 volumes) finds no overlaps inside the target and none with the start counter.
  - The only overlap is TARG with CDCB, the CDC cable cone, at LASS z 7.82–7.84 and r 9.4–9.9 cm.
  - The current repo target already has it: TARM vs CDCB.
- **flair:** `klf_target_v2.flair` and `klf_target_v2.inp` show 0 errors in four views.

## Open design points

- **Cell to base joint (option B, 2026-11-19):** a 45° flare and lip, seated in the base outside the beam. Whether 0.5 mm Al 7075 can be made this way is still to be confirmed. The fill and return ports should enter through the base and the lip at r > 3.0 cm (not modelled).
- **Second hexapod:** it is "Generic" (part 0030) in the CAD. It is drawn as CFRP like the first hexapod (0027), since aluminium struts would short the thermal isolation.
- **Upstream of LASS z −69.8 (stage 2):** the copper plate 0032 has a hole of about 1", and the 6" openings are still to be made.

## Cryostat, port and cart (2026-11-19)

Layout (option b, Richard): the GlueX target cart is kept, so the KFM and
the pair-spectrometer shielding move upstream:

| item | LASS z (cm) |
|---|---|
| lead donut, lead wall, poly wall | -779.6 ... -689.6 (moved 169.9 cm upstream) |
| KFM | -688.6 ... -336.1 (hall z -1187.55, moved 237.6 cm) |
| DET5 | -335.75 (between the KFM exit and the cart; was -72.4) |
| KL beam pipe HPO4 (iron, bore 2.75) | -335.55 ... -166.645 |
| 6 inch port: 8 inch CF flange + nipple, bore 7.62 | -166.645 ... -142.6 |
| entrance blank 921 (bore opened from 1.7 to 7.62 cm) | -142.6 ... -140.9 |
| 6-way cross (centre -105.96) | -139.9 ... -72.0 |
| GlueX cart and stand | -335.35 ... -72 |

Modelling:

- **Cross:** GlueX-style (junction cube with a vacuum box and vacuum openings, six flanged arms, bore 19.84 cm), KLF CAD dimensions; 72.3 kg SS against 68.0 kg in the CAD.
- **Vacuum:** junction, arm bores, flange-joint gaps, the 0035 nipple and the port are vacuum volumes; the beam path is vacuum from the port to the exit window.
- **Hand-built:** copper heat shield 0005 (plates and can, 6 inch openings in both beam walls, 1152.9 cm3 kept), plate 0032 (6 inch opening breaks through its lower edge: 259 of 480 cm2 left), pulse-tube bellows mount 0002, valve bracket 0003, flange clamps (rings, mass kept), CF spacer rings at the joints.
- **Everything else:** fitted primitives (pcon about the part's own axis, or box), CAD mass kept by density-scaled materials `Material_xNNN`; parts inside the G-10 rings or the cell base are their daughters.
- **Changes forced by the 3 cm beam clearance:** fill-line VCR fittings, a flex hose and copper clamp 0008 moved 0.1-0.6 cm outward (`cryostat_report.json`, "moved"); the return-line loop 0023 (2 cm3 SS) dropped, it goes around the beam axis.
- **Dropped (KLF, about 0.5 kg in all):**
  - near the cell base, parts that hit a hexapod strut once moved out of the beam: copper clamp 0010 (tags 287, 288, 19 cm3), VCR fittings 20, 22, 23;
  - the last 4 cm of copper jacket 0017:2 (strut contact, also in the CAD);
  - small hardware on the support rods (bronze bushings, aluminium cups, brass springs; about 0.2 kg), polyimide blocks 0031, block 0005-0007;
  - four springs and two cups at the heat-shield wall.
- **Reference parts dropped or folded:** the GlueX 1.5 inch beam stub and its supports (replaced by the 6 inch port), flange bolts, and cart pieces in the way of the port or the beam pipe (5.4 kg dropped, 15.3 kg folded into neighbouring cart parts). Every item is in `cryostat_report.json`.
- **Cross -x arm:** the CAD has no blank on it (open port); its bore vacuum ends at the arm flange.

Masses (model / CAD): KLF cryostat and lines 273 / 269 kg; cart 158 kg (CAD 1085 kg with the three large blocks solid).


**Cart enclosures:** the three large "Generic" cart blocks (CAD 1041, 1042, 1043; 159, 146, 51 L above the beam at LASS z -314 ... -155) are thin-walled aluminium boxes with 3 mm walls (Richard, 2026-11-19; the wall thickness is my assumption), 39 kg in all instead of 961 kg solid. Their tops stop at y 76.99, below the cart's top frame rails.

Checks (2026-11-19)

- **Beam path:** `../tools/beam_clear.py main_HDDS.xml Target 3.0 -70 90 --allow LIH2,TGXW` finds nothing inside r < 3.0 cm over LASS z −70 … 90, apart from the cell and the window. The verify, overlap and flair checks were repeated on the flared-joint version.
  - The same check on the current repo target finds the FR-4 ring TGR1 and the Rohacell end CYLW.

- **FLUKA translation:**
  `hdds2fluka.py main_HDDS.xml --root Target --container-shape envelope -o tgt` gives 47 regions.
- **Independent check:**
  `verify.py ... --per-volume 20000 --uniform 1000000` passes on 1.96 M points.
- **Overlaps:**
  `../tools/subtree_check.py main_HDDS.xml Target --n 400000` (46 volumes) finds no overlaps inside the target and none with the start counter.
  - The only overlap is TARG with CDCB, the CDC cable cone, at LASS z 7.82–7.84 and r 9.4–9.9 cm.
  - The current repo target already has it: TARM vs CDCB.
- **flair:** `klf_target_v2.flair` and `klf_target_v2.inp` show 0 errors in four views.

## Open design points

- **Cell to base joint (option B, 2026-11-19):** a 45° flare and lip, seated in the base outside the beam. Whether 0.5 mm Al 7075 can be made this way is still to be confirmed. The fill and return ports should enter through the base and the lip at r > 3.0 cm (not modelled).
- **Second hexapod:** it is "Generic" (part 0030) in the CAD. It is drawn as CFRP like the first hexapod (0027), since aluminium struts would short the thermal isolation.
- **Upstream of LASS z −69.8 (stage 2):** the copper plate 0032 has a hole of about 1", and the 6" openings are still to be made.

## Cryostat, port and cart (2026-11-19)

Layout (option b, Richard): the GlueX target cart is kept, so the KFM and
the pair-spectrometer shielding move upstream:

| item | LASS z (cm) |
|---|---|
| lead donut, lead wall, poly wall | -779.6 ... -689.6 (moved 169.9 cm upstream) |
| KFM | -688.6 ... -336.1 (hall z -1187.55, moved 237.6 cm) |
| DET5 | -335.75 (between the KFM exit and the cart; was -72.4) |
| KL beam pipe HPO4 (iron, bore 2.75) | -335.55 ... -166.645 |
| 6 inch port: 8 inch CF flange + nipple, bore 7.62 | -166.645 ... -142.6 |
| entrance blank 921 (bore opened from 1.7 to 7.62 cm) | -142.6 ... -140.9 |
| 6-way cross (centre -105.96) | -139.9 ... -72.0 |
| GlueX cart and stand | -335.35 ... -72 |

Modelling:

- **Cross:** GlueX-style (junction cube with a vacuum box and vacuum openings, six flanged arms, bore 19.84 cm), KLF CAD dimensions; 72.3 kg SS against 68.0 kg in the CAD.
- **Vacuum:** junction, arm bores, flange-joint gaps, the 0035 nipple and the port are vacuum volumes; the beam path is vacuum from the port to the exit window.
- **Hand-built:** copper heat shield 0005 (plates and can, 6 inch openings in both beam walls, 1152.9 cm3 kept), plate 0032 (6 inch opening breaks through its lower edge: 259 of 480 cm2 left), pulse-tube bellows mount 0002, valve bracket 0003, flange clamps (rings, mass kept), CF spacer rings at the joints.
- **Everything else:** fitted primitives (pcon about the part's own axis, or box), CAD mass kept by density-scaled materials `Material_xNNN`; parts inside the G-10 rings or the cell base are their daughters.
- **Changes forced by the 3 cm beam clearance:** fill-line VCR fittings, a flex hose and copper clamp 0008 moved 0.1-0.6 cm outward (`cryostat_report.json`, "moved"); the return-line loop 0023 (2 cm3 SS) dropped, it goes around the beam axis.
- **Dropped (KLF, about 0.5 kg in all):**
  - near the cell base, parts that hit a hexapod strut once moved out of the beam: copper clamp 0010 (tags 287, 288, 19 cm3), VCR fittings 20, 22, 23;
  - the last 4 cm of copper jacket 0017:2 (strut contact, also in the CAD);
  - small hardware on the support rods (bronze bushings, aluminium cups, brass springs; about 0.2 kg), polyimide blocks 0031, block 0005-0007;
  - four springs and two cups at the heat-shield wall.
- **Reference parts dropped or folded:** the GlueX 1.5 inch beam stub and its supports (replaced by the 6 inch port), flange bolts, and cart pieces in the way of the port or the beam pipe (5.4 kg dropped, 15.3 kg folded into neighbouring cart parts). Every item is in `cryostat_report.json`.
- **Cross -x arm:** the CAD has no blank on it (open port); its bore vacuum ends at the arm flange.

Masses (model / CAD): KLF cryostat and lines 273 / 269 kg; cart 158 kg (CAD 1085 kg with the three large blocks solid).


**Open: the three large "Generic" cart blocks** (CAD 1041, 1042, 1043: 159, 146,
51 L above the beam at LASS z -314 ... -155) are solid aluminium by the
rule, 961 kg of the cart's 1078 kg. They are most likely enclosures or
equipment, not solid blocks.

Checks (2026-11-19, final build, `/scratch/klf-geometry/lh2tgt/fullcheck.sh`):

| check | Target (LASS) | targetCryostat (hall) |
|---|---|---|
| FLUKA translation | 125 regions | 325 regions |
| verify.py (FLUKA vs HDDS) | PASS | PASS |
| subtree_check.py (overlaps, daughters outside mothers, neighbours) | none | none |
| beam_clear.py, r < 3.0 cm | clear, LASS -72 ... 90 | clear, LASS -170 ... -72 |
| flair 2D kernel | 0 errors in 24 views | 0 errors in 32 views |

- **Neighbours:** the moved KFM has no overlaps. In the pair spectrometer, DET5 and DET7 stick out of the hall volume, as they also do in the repo.
- **CDCB:** the old target/CDCB contact at LASS z 7.8 is gone with the 1.645 cm shift.
