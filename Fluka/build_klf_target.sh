#!/bin/bash
# Build the FLUKA bundles of the KLF LH2 target (cell and target arm in LASS,
# cryostat + entrance port + cart in the hall) and of the KLF flux monitor
# (moved upstream of the target cart) from the HDDS source, check each with
# verify.py, and pack them for the host geometry.
#
# usage, from the top of the hdds checkout:   Fluka/build_klf_target.sh [OUTDIR]
#
# All three use --container-shape envelope: the host subtracts STEM_envelope.inp
# (the flux monitor sits between the pair-spectrometer shielding, the beam
# pipe and the target cart with < 1 cm gaps, too tight for a box container).
# Name spaces (no clashes with the start counter bundle: body prefix s,
# ROT-DEFI 11-20):  flux monitor  no prefix, ROT-DEFI 1-2
#                   target        body prefix t, ROT-DEFI from 21
#                   cryostat      body prefix c, ROT-DEFI from 31
set -euo pipefail
OUT=${1:-klf_target_fluka}
[ -f main_HDDS.xml ] && [ -f Fluka/hdds2fluka.py ] || { echo "run from the top of the hdds checkout"; exit 1; }
mkdir -p "$OUT"

echo "== translating"
python3 Fluka/hdds2fluka.py main_HDDS.xml --root Target --container-shape envelope \
        --body-prefix t --rot-index-start 21 -o "$OUT/klftarget"
python3 Fluka/hdds2fluka.py main_HDDS.xml --root targetCryostat --container-shape envelope \
        --body-prefix c --rot-index-start 31 -o "$OUT/klfcryostat"
python3 Fluka/hdds2fluka.py main_HDDS.xml --root KLFFluxMonitor --container-shape envelope -o "$OUT/kfm"

echo "== verifying (FLUKA regions against the HDDS volumes)"
for r in "Target klftarget 2000" "targetCryostat klfcryostat 2000" "KLFFluxMonitor kfm 100"; do
    set -- $r
    python3 Fluka/verify.py main_HDDS.xml "$OUT/$2" --root "$1" \
            --per-volume $3 --uniform 200000 | tail -n 1 | sed "s/^/$2: /"
done

echo "== packing"
tar czf "$OUT.tgz" -C "$OUT" .
ls -l "$OUT.tgz"; md5sum "$OUT.tgz"
