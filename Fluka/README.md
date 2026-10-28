# hdds2fluka

Translate an HDDS geometry (GlueX / KLF) into FLUKA combinatorial geometry,
material definitions and region–material assignments. Python 3 + numpy.

## Usage

```
# one sub-assembly, in HDDS global (Hall D) coordinates, inside an
# air-filled RPP container that the host geometry subtracts
python3 hdds2fluka.py main_HDDS_KLF2025_KFM.xml --root KLFFluxMonitor -o kfm

# the complete geometry, world volume down to the last straw
python3 hdds2fluka.py main_HDDS_KLF2025_KFM.xml -o klf_full

# independent check of a translation (see "Verification")
python3 verify.py main_HDDS_KLF2025_KFM.xml kfm --root KLFFluxMonitor
```

Options:

| option | meaning |
|---|---|
| `--root VOL` | translate only VOL (any composition or solid); positions stay global |
| `--top VOL` | top composition of the tree (default `everything`) |
| `--container NAME` | region name of the `--root` container; the body is the same name in lower case (default `HDDSBOX` / `hddsbox`) |
| `--margin CM` | container margin around the `--root` contents (default 1 cm) |
| `--material-map HDDS=FLUKA` | use a material already defined in the host input instead of writing a definition (repeatable), e.g. `--material-map Air=AIR` |
| `--no-field` | do not set the magnetic-field flag in ASSIGNMA |
| `--box` | write rotated boxes as BOX bodies instead of RPPs under ROT-DEFI transformations |
| `--body-prefix X` | extra characters in generated body names, to avoid clashes with a host geometry |

## Output files (stem `S`)

| file | contents |
|---|---|
| `S.inp` | self-contained FLUKA input (geometry, materials, ASSIGNMA, blackhole outside); open it in flair to view or debug the geometry |
| `S_rotdefi.inp` | ROT-DEFI cards for the rotated boxes (must precede GEOBEGIN) |
| `S_bodies.inp` | body definitions only (free format, names; rotated boxes inside `$start_transform` blocks) |
| `S_regions.inp` | region definitions only |
| `S_materials.inp` | MATERIAL / COMPOUND cards |
| `S_assignma.inp` | ASSIGNMA cards |
| `S_regions.csv` | region → material, field flag, HDDS volume, shape, sensitive flag, HDDS placement path |

### Embedding a `--root` translation in an existing FLUKA geometry

1. Paste `S_bodies.inp` into the host's body list and `S_regions.inp` into its
   region list; put the `S_rotdefi.inp` cards before GEOBEGIN.
2. In the host region that currently fills that space (usually hall air),
   subtract the container body: `... -hddsbox`.
3. Add the cards from `S_materials.inp` (skip any the host already defines, or
   rerun with `--material-map`) and `S_assignma.inp`.

## How HDDS maps to FLUKA

* Every HDDS placement becomes a FLUKA region; a mother's region is its own
  solid minus its daughters. Large mother regions are cut by planes into
  several regions (same material, same HDDS volume in the CSV) so that no
  region involves more than ~300 bodies, which keeps FLUKA tracking fast.
* Shapes: `box` → RPP, or for a rotated box an RPP inside
  `$start_transform` with a ROT-DEFI rotation (FLUKA discourages BOX bodies;
  `--box` restores them); `tubs`/`cons`/`pcon` → RCC/TRC
  per segment with planes between segments; `pgon` → planes (apothem radii);
  `trd` → a box cut by its four side planes; `eltu` → REC; phi profiles →
  half-space planes through the axis.
* Placement conventions follow `hddsCommon.cpp`: shift then rotate,
  `rot="ax ay az"` applied as Rz·Ry·Rx, `mposPhi` implied rotation (default
  on), full lengths in `X_Y_Z`, `Rio_Z`, `Xmp_Ymp_Z`.
* ROT-DEFI convention: each z-axis card is Ry(−θ)·Rz(−φ) acting on the body
  coordinates, cards with the same name applied in order — the convention
  of the FLUKA manual as implemented by pyg4ometry, which reads the
  generated transformations back with the same rotations as HDDS.
* HDDS 1.1 geometry layers are honoured: a volume placed on a higher layer
  (and everything inside it) gives way to overlapping siblings on lower
  layers, e.g. the CDC end plates around the straws.
* MATERIAL cards leave WHAT(2) (atomic weight) blank, as required since
  FLUKA 4.4.0.
* Materials: composites become COMPOUND cards (atom counts when given, mass
  fractions otherwise) with the HDDS density; elements use the standard
  FLUKA names (`CARBON`, `TUNGSTEN`, …); HDDS `Vacuum` → FLUKA `VACUUM`.
  A composite without a density gets the HDDS mixture rule
  ρ = 1/Σ(wᵢ/ρᵢ), as in `hddsCommon.cpp`.
* Magnetic field: regions inside an HDDS `<apply region=...>` with a field get
  the ASSIGNMA field flag; the field map itself is up to the FLUKA user.
* Not supported yet (the script stops with a message): boolean solids,
  `sphere`, `stackX/Y/Z`.

## Verification

`verify.py` is written independently of the region construction:

1. it reads the generated `S.inp` back with its own parser and evaluates which
   FLUKA region(s) contain each sample point;
2. it classifies the same points by walking the HDDS placement tree with exact
   point-in-shape tests and the layer priority rule;
3. it requires every point to lie in exactly one FLUKA region, and that region
   to belong to the HDDS volume containing the point.

Points are sampled in and around every volume plus uniformly through the
whole assembly; `--max-volumes N` samples around a random subset for very
large geometries.
