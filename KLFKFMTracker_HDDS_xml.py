#!/usr/bin/env python3
#
# Generates KLFKFMTracker_HDDS.xml (KLF flux monitor straw tracker).
#
# Based on S. Fegan's KLFKFMTracker_HDDS.xml v1.0 (4 modules x 4 rows of Mylar
# straws, pitch 0.8 cm, rows staggered by 0.4 cm, modules rotated 0/45/90/135 deg).
# Version 2.0 (claude/rtj 2026-11-21, LEDGER.md):
#  - each straw layer is a complete disk of radius 50 cm centred on the beam:
#    every straw is the chord of the disk at its offset (the whole tube inside it);
#  - straw positions are symmetric about the beam (v1.0 ran from x = -50 to +47.2);
#  - a beam hole for the 7 cm OD KFM beam pipe: a regular octagon with apothem
#    3.55 cm (flat sides along x and y); a straw whose tube would enter it is split
#    into two pieces ending where the octagon clears the full straw width;
#  - module mother volumes are rings (inner radius 3.52 cm) so the pipe passes
#    through them.
#
# dimensions are in cm

import math

R_disk = 50.0                  # straw-layer disk radius
a_hole = 3.55                  # octagon apothem (pipe OD/2 = 3.5, + 0.5 mm)
r_straw = 0.4                  # straw half-width used for clearances (tube is 0.3999)
straw_rio = (0.3973, 0.3999)   # Mylar wall, as v1.0 after 8a1a92f
pitch = 0.8
rows = [(-1.5, 0.4), (-0.5, 0.0), (0.5, 0.4), (1.5, 0.0)]   # (z, x of the straw nearest x=0, >= 0)
env_rio_z = (3.52, 50.5, 5.0)
module_rot = [0, 45, 90, 135]
module_dz = 10.0


def octagon_halfheight(x):
    """|y| of the octagon boundary at |x| (inside the octagon for |y| below it)."""
    x = abs(x)
    t = a_hole * math.tan(math.pi / 8)
    if x <= t:
        return a_hole
    return a_hole * math.sqrt(2) - x if x < a_hole else None


def floor4(v):
    return math.floor(v * 1e4 + 1e-9) / 1e4


def ceil4(v):
    return math.ceil(v * 1e4 - 1e-9) / 1e4


def straw_pieces(x0):
    """list of (y_centre, length) for the straw at x = x0"""
    ymax = floor4(math.sqrt(R_disk**2 - (abs(x0) + r_straw)**2))
    xmin = max(abs(x0) - r_straw, 0.0)
    if xmin >= a_hole:
        return [(0.0, round(2 * ymax, 4))]
    h = ceil4(octagon_halfheight(xmin))
    L = round(ymax - h, 4)
    yc = round((ymax + h) / 2, 5)
    return [(yc, L), (-yc, L)]


placements = []    # (x, y, z, length)
for z, xfirst in rows:
    n = int(math.floor((R_disk - r_straw - xfirst) / pitch + 1e-9)) + 1
    xs = sorted({round(s * (xfirst + k * pitch), 4) for k in range(n) for s in (1, -1)})
    for x0 in xs:
        if abs(x0) + r_straw >= R_disk:
            continue
        for yc, L in straw_pieces(x0):
            placements.append((x0, yc, z, L))

# one tubs volume per distinct length; 4-character names KS00, KS01, ...
digits = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
lengths = sorted({p[3] for p in placements}, reverse=True)
vname = {L: 'KS' + digits[i // 36] + digits[i % 36] for i, L in enumerate(lengths)}

out = []
w = out.append
w('''<?xml version="1.0" encoding="UTF-8"?>
<!--DOCTYPE HDDS>

  Hall D Geometry Data Base: Kaon Flux Monitor straw tracker
  **********************************************************

     version 1.0: Initial version (S. Fegan)
     version 2.0: complete 50 cm disks centred on the beam with an octagonal
                  hole (apothem 3.55 cm) for the 7 cm OD beam pipe; generated
                  by KLFKFMTracker_HDDS_xml.py (claude/rtj 2026-11-21)

<HDDS specification="v1.0" xmlns="http://www.gluex.org/hdds">
-->

<section name        = "KLFKFMTracker"
         version     = "2.0"
         date        = "2026-11-21"
         author      = "S.Fegan, R.T. Jones"
         top_volume  = "KFMN"
         specification = "v1.0">


<!-- Origin of the flux monitor tracker is the centre of its first module, on the beam axis.
     %d straw pieces per module (%d straws split around the beam hole), %d distinct lengths.
-->

  <composition name="KLFKFMTracker">''' % (
    len(placements), sum(1 for p in placements if p[1] > 0), len(lengths)))
for i, rot in enumerate(module_rot):
    rs = '' if rot == 0 else ' rot="0 0 %d"' % rot
    w('    <posXYZ volume="TrackerModule%d" X_Y_Z="0.00    0.0   %.1f"%s/>' % (i + 1, i * module_dz, rs))
w('  </composition>\n')
for i in range(len(module_rot)):
    w('  <composition name="TrackerModule%d" envelope="KFT%d">' % (i + 1, i + 1))
    w('    <posXYZ volume="TrackerStrawLayer" X_Y_Z="0 0 0" />')
    w('  </composition>')
w('')
w('<!-- one straw layer: 4 rows; x = straw offset, y = piece centre along the straw -->')
w('  <composition name="TrackerStrawLayer">')
for x0, yc, z, L in placements:
    w('    <posXYZ volume="%s" X_Y_Z="%g %g %g" rot="90 0 0" />' % (vname[L], x0, yc, z))
w('  </composition>\n')
for L in lengths:
    w('  <tubs name="%s" Rio_Z="%g %g %g" material="Mylar" />' % (vname[L], straw_rio[0], straw_rio[1], L))
w('')
for i in range(len(module_rot)):
    w('  <tubs name="KFT%d" Rio_Z="%g %g %g" material="Air" comment="Mother volume for flux monitor tracker straws (ring: the beam pipe passes through)" />'
      % (i + 1, env_rio_z[0], env_rio_z[1], env_rio_z[2]))
w('''
</section>

<!-- </HDDS> -->''')

print('\n'.join(out))
