#!/usr/bin/env python3
"""Build Target_HDDS.xml (KLF LH2 target, version 3.0 = "KLF target v2.0")
from the JBrock Inventor model TGT-401-5000-0000 (STEP, 2026-11-17) plus the
v2.0 changes agreed with Chris Keith / Richard Jones (LEDGER.md 2026-11-18):
  * cell wall Al 7075, 0.5 mm, domed ends, LH2 volume as in the CAD
    (wall grows outward from the CAD inner surface; the entrance dome keeps
    the CAD outer surface and grows inward, to stay inside the cell base bore)
  * G10 = 1.85 g/cm3; spider rings with holes get the CAD mass via an
    effective density
Coordinates: Target frame (placed at LASS z = 50.2):
    z_local[cm] = z_CAD[mm]/10 + 14.870   (CAD -> LASS: +65.070 cm; was 16.515 from the
    reference GlueX start counter in the STEP file, see LEDGER.md)
Inputs: pcons_local.json (CAD r-z sections, made by profile.py) and
        struts.json (axes of struts and rods), both in /scratch/klf-geometry/lh2tgt.
"""
import json
import math
import sys

sys.path.insert(0, '/home/claude/klf-geometry/lh2tgt-hdds')
from profile import pcon_volume   # noqa: E402

SCR = '/scratch/klf-geometry/lh2tgt/'
CAD = json.load(open(SCR + 'pcons_local.json'))
STR = json.load(open(SCR + 'struts.json'))
ZOFF = 14.870                       # cm, CAD mm/10 -> Target frame
# 2026-11-19: whole target shifted by -1.645 cm (was 16.515) so that the
# downstream flange of the 6-way cross ends exactly at the LASS boundary
# (LASS z = -72.0), as in the GlueX master HDDS (SixWayCross at LASS -105.96);
# the two CAD/HDDS anchors (start counter, cross) differ by 1.0-1.6 cm.
PCON_ZOFF = 16.515                  # offset baked into pcons_local.json
CAD = {k: [(z - PCON_ZOFF + ZOFF, a, b) for z, a, b in v] for k, v in CAD.items()}


def zl(zcad_mm):
    return zcad_mm / 10 + ZOFF


def simplify(planes, tol=0.005):
    """drop planes whose rmin and rmax are within tol (cm) of the straight
    line through their neighbours (never drops the two planes of a step)."""
    P = [list(p) for p in planes]
    while True:
        best, bi = None, None
        for k in range(1, len(P) - 1):
            p0, p1, p2 = P[k - 1], P[k], P[k + 1]
            if p1[0] - p0[0] < 1e-9 or p2[0] - p1[0] < 1e-9:
                continue
            t = (p1[0] - p0[0]) / (p2[0] - p0[0])
            e = max(abs(p0[j] + t * (p2[j] - p0[j]) - p1[j]) for j in (1, 2))
            if e < tol and (best is None or e < best):
                best, bi = e, k
        if bi is None:
            return [tuple(p) for p in P]
        P.pop(bi)


def sphere_r(R, zc, z):
    d = R * R - (z - zc) ** 2
    return math.sqrt(d) if d > 0 else 0.0


# ---------------------------------------------------------------- the cell
R_IN, WALL = 2.8311, 0.05            # CAD inner radius; Al 7075 0.5 mm
R_OUT = R_IN + WALL
Z_DOMEC = zl(138.705)                # centre of the downstream hemisphere
NDOME = 18                           # 5 deg steps: sagitta 0.03 mm


def hemisphere(R, zc, rcyl, z0):
    pl = [(z0, 0.0, rcyl), (zc, 0.0, rcyl)]
    for k in range(1, NDOME):
        th = math.radians(90.0 * k / NDOME)
        pl.append((zc + R * math.sin(th), 0.0, R * math.cos(th)))
    pl.append((zc + R, 0.0, 0.0))
    return pl


R_CLEAR = 3.0          # beam path clear radius (6 cm beam); only the cell
                       # (LH2, wall, domes) and the exit window lie inside it

# The cell is a closed Al 7075 can of the CAD (Chris Keith) radius:
# cylinder + convex-upstream entrance dome + downstream hemisphere.  The
# entrance dome keeps the CAD inner (LH2-side) sphere and inner apex, so the
# LH2 length is the CAD one; it now spans the full cell radius (the CAD
# neck inside the cell base, r 2.41/2.67, is gone).
Z_APEX_I = zl(-258.22) + 0.05        # CAD Kapton outer apex + 0.5 mm wall
RI = 6.0159                          # CAD entrance dome, inner sphere radius
ZC_E = Z_APEX_I + RI                 # its centre, on the axis
RO = RI + WALL
Z_APEX_O = ZC_E - RO
# Joint option B (Richard, 2026-11-19): at its upstream end the cell wall
# flares at 45 deg from the cell radius out to a short lip of inner radius
# R_CLEAR (0.5 mm wall), which is seated in the cell base bore R_LIP_O; the
# entrance dome closes the lip.  So the joint lies outside the beam and the
# beam edge (r 2.881..3.0) crosses only the 0.5 mm flare wall at 45 deg.
R_LIP_I = R_CLEAR
R_LIP_O = R_CLEAR + WALL
L_LIP = 0.635                         # lip length beyond the dome rim (CAD joint)
Z_RIM_I = ZC_E - math.sqrt(RI ** 2 - R_LIP_I ** 2)  # inner dome meets the lip
Z_RIM_O = ZC_E - math.sqrt(RO ** 2 - R_LIP_O ** 2)
Z_FL_B = Z_RIM_I + L_LIP              # inner flare starts (upstream end, r 3.0)
Z_FL_A = Z_FL_B + (R_LIP_I - R_IN)    # inner flare ends at the cell radius
OFF = WALL * math.sqrt(2)             # radial offset of a 45 deg 0.5 mm wall
# outer cone: r = R_IN + OFF + (Z_FL_A - z); meets R_OUT and R_LIP_O at
Z_FLO_A = Z_FL_A + (R_IN + OFF - R_OUT)
Z_FLO_B = Z_FL_A - (R_LIP_O - R_IN - OFF)


def cap(R, zc, z_apex, z_rim, rcyl, n=16):
    """convex-upstream spherical cap from the apex to the rim radius rcyl"""
    th_max = math.asin(rcyl / R)
    pl = [(z_apex, 0.0, 0.0)]
    for k in range(1, n):
        th = th_max * k / n
        pl.append((zc - R * math.cos(th), 0.0, R * math.sin(th)))
    pl.append((z_rim, 0.0, rcyl))
    return pl


CELL = (cap(RO, ZC_E, Z_APEX_O, Z_RIM_O, R_LIP_O)
        + [(Z_FLO_B, 0.0, R_LIP_O), (Z_FLO_A, 0.0, R_OUT)]
        + hemisphere(R_OUT, Z_DOMEC, R_OUT, Z_FLO_A)[1:])   # mother, Al 7075
LH2 = (cap(RI, ZC_E, Z_APEX_I, Z_RIM_I, R_LIP_I)
       + [(Z_FL_B, 0.0, R_LIP_I), (Z_FL_A, 0.0, R_IN)]
       + hemisphere(R_IN, Z_DOMEC, R_IN, Z_FL_A)[1:])       # daughter

# cell base (Al 6061): CAD outer profile, bore = the outer radius of the cell
# lip (3.05 cm), so the lip is seated in it over Z_RIM_O .. Z_FLO_B; the
# CAD cone is cut where its outer radius reaches 3.2 cm.
Z_CONE1 = zl(-242.334)
Z_BASE1 = Z_CONE1 + (4.3413 - 3.2)   # 45 deg cone in the CAD
BODY = [(zl(-271.072), R_LIP_O, 4.3413), (Z_CONE1, R_LIP_O, 4.3413),
        (Z_BASE1, R_LIP_O, 3.2)]

# ------------------------------------------------------- vacuum vessel walls
# Rohacell vessel: CAD profile up to where its inner (toroidal) surface comes
# down to R_CLEAR; from there a bore of R_CLEAR to the exit window, which
# stays at the CAD z (13 mm downstream of the cell apex).  The outer sphere
# (R 4.7244) is followed until it comes down to R_END, then a cylinder of
# R_END carries the end face (2.4 mm wide, as in the CAD).
Z_XW0, Z_XW1, R_BORE = zl(180.28), zl(180.407), R_CLEAR
R_END = R_CLEAR + 0.24
ZC_R, R_R = zl(138.8203), 4.7244
roh_out = lambda z: sphere_r(R_R, ZC_R, z) if z > ZC_R else R_R
Z_SPH1 = ZC_R + math.sqrt(R_R ** 2 - R_END ** 2)   # outer sphere reaches R_END
roh_cad = [tuple(p) for p in CAD['TGT-401-0002-0043']]


def roh_inner(z):
    """CAD inner radius of the Rohacell vessel at z (between planes)"""
    for (za, ra, _), (zb, rb, _) in zip(roh_cad[:-1], roh_cad[1:]):
        if za <= z <= zb and zb > za:
            return ra + (rb - ra) * (z - za) / (zb - za)
    raise ValueError(z)


Z_BORE0 = next(p[0] for p in roh_cad if p[0] > 30 and p[1] <= R_CLEAR)
Z_BORE0 = max(p[0] for p in roh_cad if p[0] < Z_BORE0)
lo, hi = Z_BORE0, next(p[0] for p in roh_cad if p[0] > 30 and p[1] <= R_CLEAR)
for _ in range(60):                   # where the CAD inner surface = R_CLEAR
    mid = (lo + hi) / 2
    lo, hi = (mid, hi) if roh_inner(mid) > R_CLEAR else (lo, mid)
Z_BORE0 = (lo + hi) / 2
ROH = [p for p in roh_cad if p[0] < Z_BORE0 - 1e-6]
zz = sorted(set([Z_BORE0, Z_SPH1, Z_XW0, Z_XW1] +
                [p[0] for p in roh_cad if Z_BORE0 < p[0] < Z_SPH1]))
for z in zz:
    ROH.append((z, R_BORE, roh_out(z) if z <= Z_SPH1 else R_END))

WALLS = [  # name, CAD part, material, comment
    ('TGF1', 'TGT-401-0002-0036-0', 'StainlessSteel', 'cross-side flange 0036'),
    ('TGF2', 'TGT-401-0002-0037-0', 'StainlessSteel', 'beam pipe flange 0037'),
    ('TGB1', 'TGT-401-0002-0038-0', 'Aluminum', 'target arm beam pipe 0038'),
    ('TGF3', 'TGT-401-0002-0039', 'Aluminum', 'beam pipe end flange 0039'),
    ('TGF4', 'TGT-401-0002-x oring sealing surface josh', 'Aluminum',
     'o-ring sealing ring'),
    ('TGB2', 'TGT-401-0002-0040', 'Aluminum', 'chamber tube 0040'),
    ('TGF5', 'TGT-401-0002-0041', 'Aluminum', 'chamber flange 0041'),
    ('TGB3', 'TGT-401-0002-0042', 'Aluminum', 'chamber cone 0042'),
]
WALLP = {n: simplify([tuple(p) for p in CAD[c]]) for n, c, m, t in WALLS}
WALLP['TGRV'] = simplify(ROH)
WALLS.append(('TGRV', None, 'MediumDensityROHACELL',
              'Rohacell 71 vacuum vessel 0043'))

RINGS = [  # name, CAD part, material
    ('TGG1', 'TGT-401-0005-0005', 'G10'),
    ('TGG2', 'TGT-401-0005-0006', 'G10'),
    ('TGG3', 'TGT-401-0002-0021', 'G10ring21'),
    ('TGG4', 'TGT-401-0002-0029', 'G10spider'),
    ('TGG5', 'TGT-401-0002-0028', 'G10spider'),
]
RINGP = {n: [tuple(p) for p in CAD[c]] for n, c, m in RINGS}
# ring 0021: bore 2.8575 cm is inside the beam; open it to 3.3338 cm, the
# bore of the other two spider rings
RINGP['TGG3'] = [(z, 3.3338, ro) for z, ri, ro in RINGP['TGG3']]
# TGG1 meets the cell base (Body outer 4.3413) over its last 1.78 mm
z0, ri, ro = RINGP['TGG1'][0]
z1 = RINGP['TGG1'][1][0]
RINGP['TGG1'] = [(z0, ri, ro), (BODY[0][0], ri, ro), (BODY[0][0], 4.3413, ro),
                 (z1, 4.3413, ro)]

# snap nearly equal z planes of different CAD parts (CAD round-off of
# ~1 um left 1 um slivers between touching parts) to one common value
def snap_z(partsdicts, tol=3e-4):
    zs = sorted(set(p[0] for d in partsdicts for pl in d.values() for p in pl))
    rep, cur = {}, None
    for z in zs:
        if cur is None or z - cur > tol:
            cur = z
        rep[z] = cur
    for d in partsdicts:
        for n in d:
            d[n] = [(rep[z], ri, ro) for z, ri, ro in d[n]]


snap_z([WALLP, RINGP])


# envelope: union of the outer radii of walls and the window
def rmax_at(planes, z, side):
    """outer radius of a pcon at z from below (side=-1) or above (+1)"""
    best = None
    for (za, _, ra), (zb, _, rb) in zip(planes[:-1], planes[1:]):
        if zb - za < 1e-12:
            continue
        if za - 1e-12 <= z <= zb + 1e-12:
            if (side < 0 and z > za + 1e-12) or (side > 0 and z < zb - 1e-12):
                r = ra + (rb - ra) * (z - za) / (zb - za)
                best = r if best is None else max(best, r)
    return best


def envelope(parts):
    zs = sorted(set(round(p[0], 7) for pl in parts for p in pl))
    out = []
    for z in zs:
        for side in (-1, 1):
            r = [rmax_at(pl, z, side) for pl in parts]
            r = [x for x in r if x is not None]
            if r:
                out.append((z, 0.0, max(r)))
    clean = [out[0]]
    for p in out[1:]:
        if abs(p[0] - clean[-1][0]) < 1e-12 and abs(p[2] - clean[-1][2]) < 1e-9:
            continue
        clean.append(p)
    return clean


TARG = envelope(list(WALLP.values()))
# vacuum through the 5.6 mm joint between the cross flange (ends at LASS
# -72.0) and flange 0036, inside the 0036 bore, so the beam vacuum and the
# cryogenic lines are continuous from the cross into the target arm
Z_LASS0 = -72.0 - 50.2
R_JOINT = 10.8077
TARG = [(Z_LASS0, 0.0, R_JOINT), (TARG[0][0], 0.0, R_JOINT)] + TARG

# ------------------------------------------------------------ rods, struts
RING_Z = {n: (pl[0][0], pl[-1][0]) for n, pl in RINGP.items()}
RODS = []          # (name, x, y, z0, z1, r, material, inside-ring or None)
for t, s in STR.items():
    if s['name'] != 'TGT-401-0005-0010':
        continue
    x, y = s['c'][0] / 10, s['c'][1] / 10
    za, zb = zl(s['c'][2] + s['smin']), zl(s['c'][2] + s['smax'])
    cuts = [za, zb]
    for n, (r0, r1) in RING_Z.items():
        if r0 < zb and r1 > za:
            cuts += [r0, r1]
    cuts = sorted(cuts)
    for a, b in zip(cuts[:-1], cuts[1:]):
        ring = [n for n, (r0, r1) in RING_Z.items()
                if r0 - 1e-9 <= a and b <= r1 + 1e-9]
        RODS.append((x, y, a, b, ring[0] if ring else None))

STRUTS = []        # (x, y, z, length, ax, ay) -- tubs along the strut axis
R_STRUT = 0.2385   # solid 3/16" rods: CAD volume / length
for t, s in STR.items():
    if s['name']:
        continue
    c = [v / 10 for v in s['c']]
    a = s['ax']
    zc_ = zl(s['c'][2])
    if zc_ > -60:   # first hexapod: ring 0021 (TGG3) to ring 0005-0006 (TGG2)
        lo, hi = RING_Z['TGG3'][1], RING_Z['TGG2'][0]
    else:           # second hexapod: ring 0028 (TGG5) to ring 0029 (TGG4)
        lo, hi = RING_Z['TGG5'][1], RING_Z['TGG4'][0]
    d = R_STRUT * math.sqrt(1 - a[2] ** 2) / a[2] + 0.002
    lo, hi = lo + d, hi - d
    zm = (lo + hi) / 2
    sm = (zm - zc_) / a[2]
    x, y = c[0] + a[0] * sm, c[1] + a[1] * sm
    L = (hi - lo) / a[2]
    axr = -math.degrees(math.asin(a[1]))
    ayr = math.degrees(math.atan2(a[0], a[2]))
    STRUTS.append((x, y, zm, L, axr, ayr))


# daughters of the rings and of the cell base from build_cryostat.py
# (cryogenic lines and hardware passing through them)
import os
EXTRA = json.load(open('target_daughters.json')) if os.path.exists('target_daughters.json') else {}

TUBS = {}
for x, y, a, b, ring in RODS:
    TUBS.setdefault(('rod', round(b - a, 5)), 'TGR%d' % (len(TUBS) + 1))
for x, y, z, L, ax, ay in STRUTS:
    k = ('strut', round(L, 3))
    if k not in TUBS:
        TUBS[k] = 'TGS%d' % (sum(1 for q in TUBS if q[0] == 'strut') + 1)

# ------------------------------------------------------------------ writing
def fmt(v):
    s = '%.5f' % v
    return s.rstrip('0').rstrip('.') if '.' in s else s


def pcon_xml(name, mat, planes, comment):
    L = ['  <pcon name="%s" material="%s" comment="%s">' % (name, mat, comment)]
    for z, ri, ro in planes:
        L.append('    <polyplane Rio_Z="%s %s %s"/>' % (fmt(ri), fmt(ro), fmt(z)))
    L.append('  </pcon>')
    return L


def main(out):
    X = []
    X.append('''<?xml version="1.0" encoding="UTF-8"?>
<!--DOCTYPE HDDS>

  Hall D Geometry Data Base: KLF liquid hydrogen target
  *****************************************************

     version 3.0: KLF target v2.0, generated by build_target.py from the
                  JBrock Inventor model TGT-401-5000-0000 (2026-11-17) with
                  the v2.0 changes (Al 7075 0.5 mm cell with domed ends,
                  LH2 volume from the CAD). Do not edit by hand. [claude/rtj]

<HDDS specification="v1.0" xmlns="http://www.gluex.org/hdds">
-->

<section name        = "Target"
         version     = "3.0"
         date        = "2026-11-18"
         author      = "R.T. Jones"
         top_volume  = "TARG"
         specification = "v1.0">

<!-- Target frame: z = z_CAD[mm]/10 + 14.870 cm; placed at LASS z = 50.2.
     TARG is the vacuum inside the vessel: its outline is the union of the
     outer surfaces of the beam pipe, chamber flanges and Rohacell vessel. -->

  <composition name="Target">
    <posXYZ volume="targetVessel" X_Y_Z="0.0 0.0 0.0"/>
    <posXYZ volume="targetCryostatLASS" X_Y_Z="0.0 0.0 -50.2"/>
  </composition>

  <composition name="targetVessel" envelope="TARG">
    <posXYZ volume="targetCryostatTARG" X_Y_Z="0.0 0.0 -50.2"/>''')
    for n, c, m, t in WALLS:
        X.append('    <posXYZ volume="%s" X_Y_Z="0.0 0.0 0.0"/>' % n)
    X.append('    <posXYZ volume="TGXW" X_Y_Z="0.0 0.0 %s"/>'
             % fmt((Z_XW0 + Z_XW1) / 2))
    X.append('    <posXYZ volume="%s" X_Y_Z="0.0 0.0 0.0"/>' % ('cellBase' if EXTRA.get('TGBD') else 'TGBD'))
    X.append('    <posXYZ volume="targetCell" X_Y_Z="0.0 0.0 0.0"/>')
    for n, c, m in RINGS:
        has = any(r[4] == n for r in RODS) or bool(EXTRA.get(n))
        X.append('    <posXYZ volume="%s" X_Y_Z="0.0 0.0 0.0"/>'
                 % (('ring' + n) if has else n))
    for x, y, a, b, ring in RODS:
        if ring is None:
            X.append('    <posXYZ volume="%s" X_Y_Z="%s %s %s"/>'
                     % (TUBS[('rod', round(b - a, 5))], fmt(x), fmt(y),
                        fmt((a + b) / 2)))
    for x, y, z, L, ax, ay in STRUTS:
        X.append('    <posXYZ volume="%s" X_Y_Z="%s %s %s" rot="%s %s 0.0"/>'
                 % (TUBS[('strut', round(L, 3))], fmt(x), fmt(y), fmt(z),
                    fmt(ax), fmt(ay)))
    X.append('  </composition>\n')
    X.append('  <composition name="targetCell" envelope="TGCL">')
    X.append('    <posXYZ volume="LIH2" X_Y_Z="0.0 0.0 0.0"/>')
    X.append('  </composition>\n')
    if EXTRA.get('TGBD'):
        X.append('  <composition name="cellBase" envelope="TGBD">')
        X += EXTRA['TGBD']
        X.append('  </composition>\n')
    for n, c, m in RINGS:
        if any(r[4] == n for r in RODS) or EXTRA.get(n):
            X.append('  <composition name="ring%s" envelope="%s">' % (n, n))
            X += EXTRA.get(n, [])
            for x, y, a, b, ring in RODS:
                if ring == n:
                    X.append('    <posXYZ volume="%s" X_Y_Z="%s %s %s"/>'
                             % (TUBS[('rod', round(b - a, 5))], fmt(x),
                                fmt(y), fmt((a + b) / 2)))
            X.append('  </composition>\n')
    X += pcon_xml('TARG', 'Vacuum', TARG, 'target vacuum vessel interior')
    for n, c, m, t in WALLS:
        X += pcon_xml(n, m, WALLP[n], t)
    X.append('  <tubs name="TGXW" Rio_Z="0.0 %s %s" material="Kapton" '
             'comment="vessel exit window, 5 mil"/>'
             % (fmt(R_BORE - 1e-4), fmt(Z_XW1 - Z_XW0)))
    X += pcon_xml('TGBD', 'Aluminum', BODY, 'cell base (Al 6061), bore 3.05 cm = cell lip')
    X += pcon_xml('TGCL', 'Al7075', CELL, 'target cell, 0.5 mm Al 7075, domed ends, 45 deg flare to a lip at r 3.0')
    X += pcon_xml('LIH2', 'LiqHydrogen', LH2, 'target contents')
    for n, c, m in RINGS:
        X += pcon_xml(n, m, RINGP[n], 'G10 ring ' + c[8:])
    for (kind, L), n in sorted(TUBS.items(), key=lambda kv: kv[1]):
        if kind == 'rod':
            X.append('  <tubs name="%s" Rio_Z="0.0 0.3175 %s" '
                     'material="StainlessSteel" comment="support rod '
                     '0005-0010 segment"/>' % (n, fmt(L)))
        else:
            X.append('  <tubs name="%s" Rio_Z="0.0 %s %s" material="CFRP" '
                     'comment="hexapod strut, 3/16 inch rod"/>'
                     % (n, fmt(R_STRUT), fmt(L)))
    X.append('\n</section>\n\n<!-- </HDDS> -->')
    open(out, 'w').write('\n'.join(X) + '\n')


if __name__ == '__main__':
    main(sys.argv[1])
    v = lambda p: pcon_volume(p)
    print("LH2 volume %.1f cm3, LASS z %.3f .. %.3f" % (v(LH2), LH2[0][0] + 50.2, LH2[-1][0] + 50.2))
    print("cell wall incl. domes %.2f cm3" % (v(CELL) - v(LH2)))
    print("Rohacell bore %.4f from LASS z %.3f; exit window r %.4f at LASS %.3f"
          % (R_BORE, Z_BORE0 + 50.2, R_BORE - 1e-4, Z_XW0 + 50.2))
    print("TARG planes %d, rods %d segments, struts %d"
          % (len(TARG), len(RODS), len(STRUTS)))
    for n in WALLP:
        print("  %s %d planes" % (n, len(WALLP[n])))
