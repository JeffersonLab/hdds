#!/usr/bin/env python3
"""Build TargetCryostat_HDDS.xml: the 16" 6-way cryostat cross with its
internals, the cryocooler tower, the 6" entrance port, the cryogenic lines
and support hardware inside the target vacuum, and the GlueX target cart
(STEP reference assembly "HALL_D_TARGET_ASSEMBLY 20140401").

Frame: everything is computed in the LASS frame (cm):
    x = x_CAD/10, y = y_CAD/10, z = z_CAD/10 + ZLASS     (ZLASS = 65.070)
and placed through three compositions without envelope:
    targetCryostat      in experimentalHall at (150, -350, -500)  -> HALL air
    targetCryostatLASS  in Target (at LASS 50.2) at z = -50.2       -> LASS air
    targetCryostatTARG  in targetVessel (TARG) at z = -50.2         -> target vacuum
The cross itself follows the GlueX master model (BeamLine_HDDS.xml,
SixWayCross): a steel junction cube with a vacuum box inside and vacuum
holes in its faces, plus six flanged arm tubes; the dimensions are the KLF
CAD ones (they are the same hardware).  All other parts are the primitives
fitted by analyze_solids.py (pcon about the part's own axis, or box), with
the CAD mass kept through a per-part density factor.
"""
import json
import math
import re
import sys

import numpy as np

sys.path.insert(0, '/home/claude/klf-geometry/lh2tgt-hdds')
SCR = '/scratch/klf-geometry/lh2tgt/'
ZLASS = 65.070
ZC = -105.96                      # cross centre (LASS z)
RB, RT, RF = 19.84248, 20.32, 22.504      # bore, tube, flange radius
L0, LF0, LF1 = 20.32, 32.258, 33.96       # arm start, flange start, arm end
WALL = 0.4775                     # junction cube wall
HALF_OUT, HALF_IN = 20.32, 19.84248
LASS_Z0 = -72.0
R_CLEAR = 3.0
PORT_R, PORT_T = 7.62, 0.21       # 6" clear bore, tube wall
PORT_F_R, PORT_F_T = 10.135, 2.24 # 8" CF flange
PORT_Z0 = -165.0 - 1.645          # upstream face of the port flange (LASS)
Z921D = -140.894                  # downstream face of the entrance blank 921 (LASS)
R_SPACER = 19.647                 # bore of the CF spacer rings at the flange joints
GAPS = {'+x': 35.088, '-x': 35.088, '-y': 35.0}   # arm end .. blank (from the cross centre), 20 um clear
NOTES = []
DROPPED = []   # (group, name, grams, why)
NAMEMAP = {}


# ------------------------------------------------------------ geometry utils
def rot_angles(R):
    """HDDS rot="ax ay az" (deg) for x_mother = Rz Ry Rx x_local"""
    ay = -math.asin(max(-1, min(1, R[2, 0])))
    ax = math.atan2(R[2, 1], R[2, 2])
    az = math.atan2(R[1, 0], R[0, 0])
    return [math.degrees(v) for v in (ax, ay, az)]


def rmat(ax, ay, az):
    ax, ay, az = [math.radians(v) for v in (ax, ay, az)]
    Rx = np.array([[1, 0, 0], [0, math.cos(ax), -math.sin(ax)], [0, math.sin(ax), math.cos(ax)]])
    Ry = np.array([[math.cos(ay), 0, math.sin(ay)], [0, 1, 0], [-math.sin(ay), 0, math.cos(ay)]])
    Rz = np.array([[math.cos(az), -math.sin(az), 0], [math.sin(az), math.cos(az), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


AXES = {'+z': np.eye(3), '-z': rmat(0, 180, 0), '+x': rmat(0, 90, 0),
        '-x': rmat(0, 270, 0), '-y': rmat(90, 0, 0), '+y': rmat(270, 0, 0)}


def cad_to_lass(p):
    p = np.asarray(p, float) / 10.0
    return p + np.array([0, 0, ZLASS])


def pcon_r(planes, s):
    """(rmin, rmax) arrays of a pcon at local s (nan outside)"""
    s = np.asarray(s, float)
    rmin = np.full(s.shape, np.nan)
    rmax = np.full(s.shape, np.nan)
    for (z1, a1, b1), (z2, a2, b2) in zip(planes[:-1], planes[1:]):
        if z2 - z1 <= 0:
            continue
        m = (s >= z1) & (s <= z2) & np.isnan(rmax)
        t = (s[m] - z1) / (z2 - z1)
        rmin[m] = a1 + t * (a2 - a1)
        rmax[m] = b1 + t * (b2 - b1)
    return rmin, rmax


class Solid:
    """an HDDS primitive placed in the LASS frame"""
    def __init__(self, name, kind, o, R, par, mat, f=1.0, comment=''):
        self.name, self.kind, self.o, self.R = name, kind, np.asarray(o, float), np.asarray(R, float)
        self.par, self.mat, self.f, self.comment = par, mat, f, comment

    def local(self, P):
        return (np.asarray(P) - self.o) @ self.R

    def inside(self, P, eps=0.0):
        Q = self.local(P)
        if self.kind == 'box':
            h = np.asarray(self.par) / 2 - eps
            ok = np.all(np.abs(Q) <= h, axis=1)
            if hasattr(self, 'hole'):
                ax, hc, hr = self.hole
                o2 = [j for j in range(3) if j != ax]
                PP = np.asarray(P)
                ok &= np.hypot(PP[:, o2[0]] - hc[0], PP[:, o2[1]] - hc[1]) > hr
            return ok
        if self.kind == 'pcon':
            rmin, rmax = pcon_r(self.par, Q[:, 2])
            r = np.hypot(Q[:, 0], Q[:, 1])
            ok = ~np.isnan(rmax)
            ok[ok] &= (r[ok] >= rmin[ok] + eps) & (r[ok] <= rmax[ok] - eps)
            return ok
        raise ValueError(self.kind)

    def sample(self, n=4000, rng=np.random.default_rng(1)):
        if self.kind == 'box':
            Q = (rng.uniform(-0.5, 0.5, (n, 3)) * np.asarray(self.par))
        else:
            zs = [p[0] for p in self.par]
            rm = max(p[2] for p in self.par)
            Q = np.c_[rng.uniform(-rm, rm, (n * 4, 2)), rng.uniform(min(zs), max(zs), n * 4)]
            rmin, rmax = pcon_r(self.par, Q[:, 2])
            r = np.hypot(Q[:, 0], Q[:, 1])
            Q = Q[(~np.isnan(rmax)) & (r >= rmin) & (r <= rmax)][:n]
        return Q @ self.R.T + self.o

    def volume(self):
        if self.kind == 'box':
            return float(np.prod(self.par))
        from profile import pcon_volume
        return pcon_volume(self.par)

    def cut(self, axis, lo, hi):
        """piece of this solid with lo <= p[axis] <= hi (global axis 0,1,2);
        only for solids whose local z or a box axis is parallel to it"""
        g = np.zeros(3); g[axis] = 1.0
        if self.kind == 'pcon':
            dz = self.R[:, 2] @ g
            if abs(dz) < 0.98:
                return None
            # local s of the global planes; for a slightly tilted solid the
            # cut faces are pulled in by r*tan(tilt) so no corner crosses
            rm = max(p[2] for p in self.par)
            marg = rm * math.sqrt(max(0.0, 1 - dz * dz)) / abs(dz) + (1e-4 if abs(abs(dz) - 1) > 1e-9 else 0.0)
            s_lo, s_hi = sorted([(lo - self.o[axis]) / dz, (hi - self.o[axis]) / dz])
            s_lo, s_hi = s_lo + marg, s_hi - marg
            pl = self.par
            zs = sorted(set([p[0] for p in pl] + [s_lo, s_hi]))
            zs = [z for z in zs if s_lo - 1e-9 <= z <= s_hi + 1e-9 and pl[0][0] - 1e-9 <= z <= pl[-1][0] + 1e-9]
            if len(zs) < 2:
                return None
            new = []
            for z in zs:
                same = [p for p in pl if abs(p[0] - z) < 1e-9]
                if same and s_lo + 1e-9 < z < s_hi - 1e-9:
                    new += [tuple(p) for p in same]
                else:
                    a, b = pcon_r(pl, np.array([z + (1e-7 if z <= s_lo + 1e-9 else -1e-7)]))
                    if not np.isnan(b[0]):
                        new.append((z, float(a[0]), float(b[0])))
            new = [p for p in new if p[2] > p[1] - 1e-12]
            if len(new) < 2 or new[-1][0] - new[0][0] < 1e-6:
                return None
            return Solid(self.name, 'pcon', self.o, self.R, new, self.mat, self.f, self.comment)
        if self.kind == 'box':
            k = int(np.argmax(np.abs(self.R.T @ g)))
            ck = abs(self.R[:, k] @ g)
            if ck < 0.98:
                return None
            others = [j for j in range(3) if j != k]
            marg = sum(self.par[j] / 2 * abs(self.R[:, j] @ g) for j in others) + (1e-4 if ck < 1 - 1e-9 else 0.0)
            c = self.o[axis]
            h = self.par[k] / 2 * ck
            a, b = max(c - h, lo + marg), min(c + h, hi - marg)
            if b - a < 1e-6:
                return None
            o = self.o + self.R[:, k] * (((a + b) / 2 - c) / (self.R[:, k] @ g))
            par = list(self.par); par[k] = (b - a) / ck
            return Solid(self.name, 'box', o, self.R, par, self.mat, self.f, self.comment)


# ---------------------------------------------------------------- mothers
class Mother:
    def __init__(self, name, test, comp, o=(0, 0, 0), R=np.eye(3), prio=0):
        self.name, self.test, self.comp, self.o, self.R, self.prio = name, test, comp, np.asarray(o, float), R, prio
        self.items = []


def in_box(c, h):
    c, h = np.asarray(c, float), np.asarray(h, float)
    return lambda P: np.all(np.abs(np.asarray(P) - c) <= h, axis=1)


def in_cyl(o, d, r, s0, s1):
    o, d = np.asarray(o, float), np.asarray(d, float)
    def f(P):
        Q = np.asarray(P) - o
        s = Q @ d
        rr = np.linalg.norm(Q - np.outer(s, d), axis=1)
        return (rr <= r) & (s >= s0) & (s <= s1)
    return f


def build_mothers(targ_planes):
    M = []
    cc = np.array([0, 0, ZC])
    M.append(Mother('XJV', in_box(cc, [HALF_IN] * 3), 'crossJunctionVac', cc, prio=3))
    for key, Ra in AXES.items():
        d = Ra[:, 2]
        # hole disk in the cube wall, then the arm bore
        M.append(Mother('XJH' + key, in_cyl(cc, d, RB, HALF_IN, HALF_OUT), 'crossHole' + key[0].replace('+', 'P').replace('-', 'M') + key[1],
                        cc + d * (HALF_IN + HALF_OUT) / 2, Ra, prio=3))
        M.append(Mother('XAV' + key, in_cyl(cc, d, RB, L0, LF1), 'crossArm' + key[0].replace('+', 'P').replace('-', 'M') + key[1],
                        cc + d * (L0 + LF1) / 2, Ra, prio=3))
    # flange-joint gaps (vacuum discs): +y to the 0035 nipple, -z to the port blank
    M.append(Mother('XGPY', in_cyl(cc, [0, 1, 0], RB, LF1, 34.52), 'crossGapPY',
                    cc + np.array([0, (LF1 + 34.52) / 2, 0]), AXES['+y'], prio=3))
    M.append(Mother('XGMZ', in_cyl(cc, [0, 0, -1], R_SPACER, LF1, -(Z921D - ZC)), 'crossGapMZ',
                    cc + np.array([0, 0, -(LF1 + (-(Z921D - ZC))) / 2]), AXES['-z'], prio=3))
    # target vacuum (TARG, LASS z >= -72)
    def in_targ(P):
        P = np.asarray(P)
        rmin, rmax = pcon_r(targ_planes, P[:, 2] - 50.2)
        r = np.hypot(P[:, 0], P[:, 1])
        ok = ~np.isnan(rmax)
        ok[ok] &= r[ok] <= rmax[ok]
        return ok
    import build_target as BT
    def in_rings(P):
        P = np.asarray(P)
        m = np.zeros(len(P), bool)
        for nm, planes in list(BT.RINGP.items()) + [('TGBD', BT.BODY)]:
            a, b = pcon_r(planes, P[:, 2] - 50.2)
            r = np.hypot(P[:, 0], P[:, 1])
            ok = ~np.isnan(b)
            ok[ok] &= (r[ok] >= a[ok]) & (r[ok] <= b[ok])
            m |= ok
        return m
    M.append(Mother('TARG', lambda P: in_targ(P) & ~in_rings(P), 'targetCryostatTARG', prio=2))
    for nm, planes in list(BT.RINGP.items()) + [('TGBD', BT.BODY)]:
        def t(P, planes=planes):
            P = np.asarray(P)
            a, b = pcon_r(planes, P[:, 2] - 50.2)
            r = np.hypot(P[:, 0], P[:, 1])
            ok = ~np.isnan(b)
            ok[ok] &= (r[ok] >= a[ok]) & (r[ok] <= b[ok])
            return ok
        M.append(Mother(nm, t, 'inTarget:' + nm, [0, 0, 50.2], np.eye(3), prio=4))
    def in_cross(P):
        P = np.asarray(P)
        Q = P - cc
        m = np.all(np.abs(Q) <= HALF_OUT, axis=1)
        for key, Ra in AXES.items():
            m |= in_cyl(cc, Ra[:, 2], RF, L0, LF1)(P)
        m |= in_cyl(cc, [0, 1, 0], RB, LF1, 34.52)(P)
        m |= in_cyl(cc, [0, 0, -1], R_SPACER, LF1, -(Z921D - ZC))(P)
        for extra in EXTRA_MOTHER_TESTS:
            m |= extra(P)
        return m
    M.append(Mother('LASS', lambda P: (np.asarray(P)[:, 2] >= LASS_Z0) & (np.hypot(np.asarray(P)[:, 0], np.asarray(P)[:, 1]) <= 188) & ~in_targ(P), 'targetCryostatLASS', prio=1))
    M.append(Mother('HALL', lambda P: (np.asarray(P)[:, 2] < LASS_Z0) & ~in_cross(P), 'targetCryostat', prio=0))
    return M


EXTRA_MOTHER_TESTS = []


# ---------------------------------------------------------------- materials
BASE = {  # HDDS material, density g/cm3 (for scaled copies)
    'Aluminum': 2.70, 'Al7075': 2.81, 'StainlessSteel': 8.02, 'Copper': 8.96,
    'Iron': 7.87, 'BrassCAD': 8.47, 'Bronze': 8.874, 'G10': 1.85, 'CFRP': 1.43,
    'Kapton': 1.42, 'Polyethylene': 0.95}
CAD2HDDS = {
    'Aluminum 6061': 'Aluminum', 'Stainless Steel': 'StainlessSteel',
    'Stainless Steel, Austenitic': 'StainlessSteel', 'Copper': 'Copper',
    'Steel, Mild': 'Iron', 'Brass, Soft Yellow': 'BrassCAD', 'Bronze, Soft Tin': 'Bronze',
    'Garlite 10 JDB': 'G10', 'CFRP': 'CFRP', 'Polyimide': 'Kapton', 'Kapton': 'Kapton'}
# parts without a CAD material, or "Generic" (rule: aluminium unless there is
# a reason to think otherwise; the reasons are given here)
BYNAME = [
    (r'^TGT-401-0002-0034', 'Aluminum', 'flange clamp and ring (CAD: xClamp and ring, Al 6061)'),
    (r'^Compress Spring', 'StainlessSteel', 'spring'),
    (r'^TGT-401-0005-0011', 'Aluminum', 'spring cup (CAD: Al Spring Cup)'),
    (r'^Hexagon Socket Set Screw', 'Iron', 'set screw, mild steel'),
    (r'^SS_\d_VCR', 'StainlessSteel', 'VCR fitting (stainless by design)'),
    (r'^cross, 16 inch', 'StainlessSteel', 'CF cross'),
    (r'^Omnetics', 'Polyethylene', 'plastic micro-connector'),
    (r'^TGT-401-0002-0030', 'CFRP', 'hexapod strut (stage 1 choice)'),
]


def load_cad_materials():
    m = {}
    for line in open(SCR + 'materials.txt'):
        p = re.split(r'\s{2,}', line.strip())
        if len(p) >= 3:
            m[p[0].replace('_', '-')] = p[1]
    return m


CADMAT = load_cad_materials()


def material_of(tag, path, bbox_lass):
    prod = re.sub(r':\d+$', '', path[-1]) if path else ''
    top = path[1] if path and len(path) > 1 else ''
    for rx, mat, why in BYNAME:
        if re.match(rx, prod):
            return mat, why
    if top.startswith('HALL_D_TARGET'):
        lo, hi = bbox_lass
        # blank flanges and plates on the cross ports are stainless (CF seals)
        if (np.all(lo >= [-37.5, -37.5, -143.0]) and np.all(hi <= [37.5, 73.0, -72.0])):
            return 'StainlessSteel', 'cross port blank (reference assembly, CF flange)'
        return 'Aluminum', 'cart (reference assembly, "Generic": aluminium by rule)'
    cm = CADMAT.get(prod.replace('_', '-'))
    if cm in CAD2HDDS:
        return CAD2HDDS[cm], 'CAD material ' + cm
    if cm in ('Generic', None):
        return 'Aluminum', 'CAD "%s": aluminium by rule' % cm
    return 'Aluminum', 'unmapped CAD material %s' % cm


def scaled(mat, f):
    if 0.97 < f < 1.03:
        return mat
    k = int(round(f * 50)) * 2          # 2% steps
    k = max(k, 2)
    return '%s_x%03d' % (mat, k)


def material_xml(names):
    L = ['  <!-- density-scaled copies (parts drawn without their holes and',
         '       slots keep the CAD mass); name_xNNN = NNN % of the density -->']
    for n in sorted(names):
        m = re.match(r'(.+)_x(\d{3})$', n)
        if not m:
            continue
        base, k = m.group(1), int(m.group(2))
        L.append('  <composite name="%s">' % n)
        L.append('    <addmaterial material="%s"> <fractionmass fraction="1.0"/> </addmaterial>' % base)
        L.append('    <real name="density" value="%.4g" unit="g/cm^3"/>' % (BASE[base] * k / 100))
        L.append('  </composite>')
    return L


# --------------------------------------------------------- fixed (by hand)
def cross_solids():
    """GlueX-style cross: junction cube + 6 arms (tube + CF flange)"""
    cc = np.array([0, 0, ZC])
    S = [Solid('XJB', 'box', cc, np.eye(3), [2 * HALF_OUT] * 3, 'StainlessSteel', comment='cross junction (GlueX-style cube)'),
         Solid('XJV', 'box', cc, np.eye(3), [2 * HALF_IN] * 3, 'Vacuum', comment='cross junction vacuum')]
    arm = [(L0, 0.0, RT), (LF0, 0.0, RT), (LF0, 0.0, RF), (LF1, 0.0, RF)]
    for key, Ra in AXES.items():
        S.append(Solid('XAR', 'pcon', cc, Ra, arm, 'StainlessSteel', comment='cross arm ' + key))
    return S


def port_solids():
    """6 inch entrance port: nipple + 8 inch CF flange, vacuum inside"""
    z0, z1 = PORT_Z0, -142.597          # flange face .. upstream face of blank 921
    pl = [(z0, PORT_R, PORT_F_R), (z0 + PORT_F_T, PORT_R, PORT_F_R),
          (z0 + PORT_F_T, PORT_R, PORT_R + PORT_T), (z1, PORT_R, PORT_R + PORT_T)]
    return [Solid('XPNP', 'pcon', [0, 0, 0], np.eye(3), pl, 'StainlessSteel', comment='6 inch entrance port, 8 inch CF flange'),
            Solid('XPVC', 'pcon', [0, 0, 0], np.eye(3), [(z0, 0, PORT_R), (Z921D, 0, PORT_R)], 'Vacuum',
                  comment='vacuum in the entrance port and the 6 inch hole of the blank')]


def spacer_solids():
    """CF spacer rings (CAD 176.4 cm3 SS each, reference assembly parts
    912, 925, 946, 936) in the flange joint gaps, and vacuum inside them"""
    cc = np.array([0, 0, ZC])
    out = []
    joints = {'-z': -(Z921D - ZC)}
    joints.update(GAPS)
    for key, g in joints.items():
        Ra = AXES[key]
        ring = Solid('XK' + AXCODE[key], 'pcon', cc, Ra, [(LF1, R_SPACER, 21.841), (g, R_SPACER, 21.841)], 'StainlessSteel', 1.0,
                     'CF spacer ring at the %s flange joint (reference part, mass kept)' % key)
        ring.f = 176.4 / ring.volume()
        out.append(ring)
        if key != '-z':
            out.append(Solid('XW' + AXCODE[key], 'pcon', cc, Ra, [(LF1, 0, R_SPACER), (g, 0, R_SPACER)], 'Vacuum', 1.0,
                             'vacuum in the %s flange joint' % key))
    return out


def gap_solids():
    cc = np.array([0, 0, ZC])
    return [Solid('XGPY', 'pcon', cc, AXES['+y'], [(LF1, 0, RB), (34.52, 0, RB)], 'Vacuum', comment='flange joint gap, cross to 0035'),
            Solid('XGMZ', 'pcon', cc, AXES['-z'], [(LF1, 0, R_SPACER), (-(Z921D - ZC), 0, R_SPACER)], 'Vacuum', comment='flange joint gap, cross to entrance blank')]


CLAMP_JOINT = {  # instance: (arm axis, r_in)
    '5': ('-z', 22.52), '3': ('+z', 22.52), '4': ('-x', 24.42), '6': ('+x', 24.42),
    '1': ('+y', 24.42), '2': ('+y', 24.42)}


def clamp_solids(S_named, V):
    out = []
    cc = np.array([0, 0, ZC])
    groups = {}
    for t, e in S_named.items():
        if t.startswith('_'):
            continue
        m = re.match(r'TGT-401-0002-0034:(\d)', e['path'][-1])
        if m:
            groups.setdefault(m.group(1), []).append(t)
    for k, tags in sorted(groups.items()):
        key, rin = CLAMP_JOINT[k]
        Ra = AXES[key]
        d = Ra[:, 2]
        vol, s_all, r_all = 0.0, [], []
        for t in tags:
            b = np.array(V[int(t)]['bb'])
            lo, hi = cad_to_lass(b[:3]), cad_to_lass(b[3:])
            corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
            Q = corners - cc
            s = Q @ d
            s_all += [s.min(), s.max()]
            perp = Q - np.outer(s, d)
            # axis-aligned blocks: the radial extent is the bbox extent along the radial axis
            r_all.append(np.abs(perp).max())
            vol += V[int(t)]['vol'] / 1000
        s0, s1 = min(s_all), max(s_all)
        rout = max(r_all)
        vr = math.pi * (rout ** 2 - rin ** 2) * (s1 - s0)
        f = vol / vr
        out.append(Solid('XCL' + k, 'pcon', cc, Ra, [(s0, rin, rout), (s1, rin, rout)], 'Aluminum', f,
                         comment='flange clamp 0034:%s (8 blocks + 2 rings) as a ring, mass kept' % k))
    return out


# ------------------------------------------------------- fitted CAD parts
SKIP_PRODUCTS = (r'^cross, 16 inch', r'^Body1_MODEL_SOLIDS', r'^TGT-401-0002-0034')


def prim_solids(prims, S_named, V):
    out = []
    for t, p in prims.items():
        e = S_named.get(t, {})
        path = e.get('path', ['', '', V[int(t)]['name'].split('/')[-1]])
        prod = path[-1]
        if any(re.match(rx, prod) for rx in SKIP_PRODUCTS):
            continue
        b = np.array(V[int(t)]['bb'])
        lo, hi = cad_to_lass(b[:3]), cad_to_lass(b[3:])
        top = path[1] if len(path) > 1 else ''
        # GlueX 1.5 inch beam stub, its bellows/flanges/supports: replaced by the 6 inch port
        if top.startswith('HALL_D_TARGET') and hi[2] > -172 and lo[2] < -140.9 and \
                max(abs(lo[0]), abs(hi[0]), abs(lo[1]), abs(hi[1])) < 11.0 and t != '921':
            NOTES.append('dropped GlueX beam-stub part %s (z %.1f..%.1f)' % (t, lo[2], hi[2]))
            continue
        mat, why = material_of(t, path, (lo, hi))
        name = 'C%04d' % int(t)
        comm = '%s [%s]' % (re.sub(r'[<>&"]', '', prod)[:40], why)
        R = np.array(p['R'])
        if p['type'] == 'box':
            s = Solid(name, 'box', cad_to_lass(p['c']), R, [d / 10 for d in p['dims']], mat, p['f'], comm)
            s.tag = t
            out.append(s)
        else:
            o = cad_to_lass(p['o'])
            groups = p['planes'] if isinstance(p['planes'][0][0], list) else [p['planes']]
            for k, pl in enumerate(groups):
                planes = [(z / 10, a / 10, bb / 10) for z, a, bb in pl]
                s = Solid(name + ('' if len(groups) == 1 else chr(97 + k)), 'pcon', o, R, planes, mat, p['f'], comm)
                s.tag = t
                out.append(s)
    return out


def open_port_bore(solids):
    """blank 921: bore opened to the 6 inch port radius"""
    for s in solids:
        if getattr(s, 'tag', '') in ('934', '956') and s.kind == 'pcon':
            d = s.R[:, 2]
            k = int(np.argmax(np.abs(d)))
            o = np.array([0.0, 0.0, ZC]); o[k] = s.o[k]
            s.o = o                                  # centred on the cross arm axis
        if getattr(s, 'tag', '') == '921' and s.kind == 'pcon':
            s.o = np.array([0.0, 0.0, s.o[2]])      # CAD axis is 0.8 mm off the beam axis
            s.par = [(z, max(a, PORT_R), b) for z, a, b in s.par]
            s.comment += '; 1.5 inch port opened to a 6 inch bore'
            NOTES.append('blank 921: bore opened to r %.2f' % PORT_R)


SHRINK_NOT_MOVE = ('287', '288')


def move_out_of_beam(solids):
    """parts of the fill/return lines inside r < R_CLEAR (CAD routing into the
    old cell base) are moved radially outward until r >= R_CLEAR + 0.05"""
    for s in solids:
        if s.mat == 'Vacuum':
            continue
        P = s.sample(20000)
        r = np.hypot(P[:, 0], P[:, 1])
        if r.min() >= R_CLEAR or P[:, 2].min() > 39.0 or P[:, 2].max() < PORT_Z0:
            continue
        if getattr(s, 'tag', '') in SHRINK_NOT_MOVE and s.kind == 'box':
            # cut the box face nearest the beam back to r = R_CLEAR + 0.05
            c = s.o[:2]
            u = c / np.linalg.norm(c)
            k = int(np.argmax([abs(s.R[:2, j] @ u) for j in range(3)]))
            sg = 1.0 if s.R[:2, k] @ u > 0 else -1.0
            lo, hi = 0.0, s.par[k]
            for _ in range(40):
                mid = (lo + hi) / 2
                o = s.o + s.R[:, k] * sg * mid / 2
                par = list(s.par); par[k] = s.par[k] - mid
                t = Solid(s.name, 'box', o, s.R, par, s.mat, s.f)
                Q = t.sample(6000)
                if np.hypot(Q[:, 0], Q[:, 1]).min() >= R_CLEAR + 0.05:
                    hi = mid
                else:
                    lo = mid
            v0 = s.volume()
            s.o = s.o + s.R[:, k] * sg * hi / 2
            s.par = list(s.par); s.par[k] -= hi
            s.f = min(1.0, s.f * v0 / s.volume())
            s.comment += '; beam side cut back by %.2f cm' % hi
            NOTES.append('%s cut back by %.2f cm on the beam side (r >= 3)' % (s.name, hi))
            continue
        c = P[:, :2].mean(0)
        u = c / (np.linalg.norm(c) or 1)
        # smallest outward shift that clears the beam
        lo, hi = 0.0, 3.0
        for _ in range(40):
            m = (lo + hi) / 2
            Q = P[:, :2] + u * m
            if np.hypot(Q[:, 0], Q[:, 1]).min() >= R_CLEAR + 0.1:
                hi = m
            else:
                lo = m
        if hi >= 3.0 - 1e-6 or np.linalg.norm(c) < 1.0:
            s.mat = 'DROP'
            NOTES.append('%s (%s) dropped: it crosses the beam (min r %.2f), cannot be moved out' % (s.name, s.comment[:30], r.min()))
            continue
        s.o = s.o + np.array([u[0] * hi, u[1] * hi, 0])
        s.comment += '; moved %.2f cm outward (beam clearance r>=3)' % hi
        NOTES.append('%s (%s) moved %.2f cm outward, min r was %.2f' % (s.name, s.comment[:30], hi, r.min()))


# ------------------------------------------------- mother assignment, cuts
SPLIT_PLANES = None


def split_planes():
    cc_z = ZC
    planes = {0: [], 1: [], 2: [LASS_Z0]}
    for ax in range(3):
        c = 0.0 if ax < 2 else cc_z
        for sgn in (-1, 1):
            planes[ax] += [c + sgn * HALF_IN, c + sgn * HALF_OUT, c + sgn * LF1]
    planes[1] += [34.52, 62.74]
    import build_target as BT
    for nm, pl in list(BT.RINGP.items()) + [('TGBD', BT.BODY)]:
        planes[2] += [pl[0][0] + 50.2, pl[-1][0] + 50.2]
    planes[2] += [Z921D]
    return {k: sorted(set(v)) for k, v in planes.items()}


def assign(solids, mothers, report):
    """place every solid in the innermost mother containing all its sample
    points; solids spanning several mothers are cut along planes of the
    mother boundaries when their axis allows it"""
    placed = []
    planes = split_planes()
    queue = list(solids)
    while queue:
        s = queue.pop(0)
        P = s.sample(3000)
        if len(P) == 0:
            report.append('no sample points: %s' % s.name)
            continue
        ins = [(m, m.test(P)) for m in mothers]
        full = [m for m, k in ins if k.all()]
        if full:
            m = max(full, key=lambda m: m.prio)
            m.items.append(s)
            placed.append((s, m))
            continue
        # try cuts along the global axes
        done = False
        for ax in (2, 1, 0):
            lo, hi = P[:, ax].min(), P[:, ax].max()
            cuts = [c for c in planes[ax] if lo + 1e-6 < c < hi - 1e-6]
            if not cuts:
                continue
            edges = [lo - 1] + cuts + [hi + 1]
            pieces = [s.cut(ax, a, b) for a, b in zip(edges[:-1], edges[1:])]
            if all(p is not None for p in pieces):
                for k, p in enumerate(pieces):
                    p.name = s.name + ('.%d' % k if len(pieces) > 1 else '')
                queue = pieces + queue
                done = True
                break
        if not done:
            frac = {m.name: float(k.mean()) for m, k in ins if k.any()}
            if s.comment.startswith('HALL_D_TARGET'):
                DROPPED.append(('cart', s.name, s.volume() * s.f * BASE.get(s.mat, 2.7), 'cannot be placed (bolt/gasket in a flange?) %s' % frac))
            else:
                report.append('cannot place %s (%s): in %s' % (s.name, s.comment[:40], frac))
    return placed


# ------------------------------------------------------ sibling overlaps
def aabb(s):
    P = s.sample(1500)
    return P.min(0), P.max(0)


def find_overlaps(items, n=12000):
    """pairs of siblings that share volume (sampled), with overlap fraction"""
    bb = [aabb(s) for s in items]
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (a0, a1), (b0, b1) = bb[i], bb[j]
            if np.any(a1 < b0) or np.any(b1 < a0):
                continue
            si, sj = items[i], items[j]
            small, big = (si, sj) if si.volume() <= sj.volume() else (sj, si)
            P = small.sample(n)
            if len(P) == 0:
                continue
            fr = big.inside(P).mean()
            if fr > 0:
                out.append((small, big, fr))
    return out


# ------------------------------------------------------------------ naming
class Namer:
    def __init__(self, first):
        self.first, self.n = first, 0

    def __call__(self):
        self.n += 1
        k, s = self.n, ''
        for _ in range(3):
            s = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[k % 36] + s
            k //= 36
        return self.first + s


def fmt(v):
    s = '%.5f' % v
    s = s.rstrip('0').rstrip('.') if '.' in s else s
    return '0' if s in ('-0', '') else s


def xattr(t):
    return t.replace('&', 'and').replace('"', "'").replace('<', '(').replace('>', ')')


def shape_xml(name, s, mat):
    s.comment = xattr(s.comment)
    if s.kind == 'box':
        return ['  <box name="%s" X_Y_Z="%s" material="%s" comment="%s"/>'
                % (name, ' '.join(fmt(v) for v in s.par), mat, s.comment)]
    L = ['  <pcon name="%s" material="%s" comment="%s">' % (name, mat, s.comment)]
    for z, a, b in s.par:
        L.append('    <polyplane Rio_Z="%s %s %s"/>' % (fmt(a), fmt(b), fmt(z)))
    L.append('  </pcon>')
    return L


def place_xml(vol, s, m):
    Rl = m.R.T @ s.R
    t = m.R.T @ (s.o - m.o)
    a = rot_angles(Rl)
    rot = '' if max(abs(x) for x in a) < 1e-7 else ' rot="%s"' % ' '.join(fmt(x) for x in a)
    return '    <posXYZ volume="%s" X_Y_Z="%s"%s/>' % (vol, ' '.join(fmt(x) for x in t), rot)


# -------------------------------------------------------------------- main
def main(out_xml, out_report):
    import build_target as BT
    S_named = json.load(open(SCR + 'solids_named.json'))
    V = {e['tag']: e for e in json.load(open(SCR + 'vols.json'))}
    prims = {}
    for k in range(6):
        prims.update(json.load(open(SCR + 'prims_%d.json' % k)))
    # refits as boxes of polycone fits that came out smaller than the solid;
    # 0004 (181) keeps its polycone (the box is 1 %% full) with f = 1.13
    for k in (6, 7):
        for t, p in json.load(open(SCR + 'prims_%d.json' % k)).items():
            if t not in ('181',):
                prims[t] = p
    for t, p in prims.items():
        if p['vmodel'] < p['vcad']:
            p['f'] = p['vcad'] / p['vmodel']
            if p['f'] > 1.03:
                NOTES.append('part %s: fitted volume %.1f < CAD %.1f cm3, density x%.2f' % (t, p['vmodel'] / 1e3, p['vcad'] / 1e3, p['f']))
    # vacuum inside the 0035 nipple (bore r 20.002 from the CAD) and the gap
    # up to the 0001 top plate
    cc = np.array([0, 0, ZC])
    y0, y1, rn = 34.52, 62.74, 20.002
    t = in_cyl(cc, [0, 1, 0], rn, y0, y1)
    EXTRA_MOTHER_TESTS[:] = [t]
    xn = Mother('XNVP', t, 'crossNippleVac', cc + np.array([0, (y0 + y1) / 2, 0]), AXES['+y'], prio=3)
    xn.shape_xml = ['  <tubs name="XNVP" Rio_Z="0 %s %s" material="Vacuum" comment="vacuum in the 0035 nipple and the gap to the top plate"/>' % (fmt(rn), fmt(y1 - y0))]
    mothers = build_mothers(BT.TARG) + [xn]
    M = {m.name: m for m in mothers}
    fitted = prim_solids(prims, S_named, V)
    open_port_bore(fitted)
    fitted = apply_overrides(fitted, prims)
    move_out_of_beam(fitted)
    fitted = [x for x in fitted if x.mat != 'DROP']
    statics = port_solids() + clamp_solids(S_named, V) + spacer_solids()
    report = []
    placed = assign(fitted + statics, mothers, report)

    # sibling overlaps per mother (the cross walls, junction and gaps are
    # hand-placed volumes outside this list: test fitted parts against them)
    fixed = cross_solids() + gap_solids()
    over = []
    for m in mothers:
        items = list(m.items)
        if m.name == 'HALL':
            items += [s for s in fixed if s.name in ('XJB', 'XAR') or s.name.startswith('XG')]
            # KL beam pipe from the KFM exit to the port (PairSpect_HDDS.xml, HPO4)
            items.append(Solid('XBPI', 'pcon', [0, 0, 0], np.eye(3), [(-335.55, 0, 8.0), (PORT_Z0, 0, 8.0)], 'Iron', comment='KL beam pipe HPO4 (check only)'))
            # DET5 scoring plane and the KFM exit (check only)
            items.append(Solid('XDT5', 'box', [0, 0, -335.75], np.eye(3), [1700, 1198, 0.2], 'Air', comment='DET5 (check only)'))
        over += [(m.name, a, b, fr) for a, b, fr in find_overlaps(items)]
    # small nested parts (springs in cups, VCR nuts on glands, clamp blocks):
    # the smaller one is merged into the larger one (mass kept up to f = 1)
    absorbed = set()
    for mname, a, b, fr in sorted(over, key=lambda q: q[1].volume()):
        if id(a) in absorbed or id(b) in absorbed:
            continue
        if a.volume() < 20.0 and a.mat != 'Vacuum' and b.mat != 'Vacuum' and not b.name.startswith('X'):
            ma, mb = a.volume() * a.f * BASE.get(a.mat, 2.7), b.volume() * b.f * BASE.get(b.mat, 2.7)
            fnew = b.f * (ma + mb) / mb
            lost = max(0.0, fnew - 1.0) * b.volume() * BASE.get(b.mat, 2.7)
            b.f = min(1.0, fnew)
            for m in mothers:
                if a in m.items:
                    m.items.remove(a)
            absorbed.add(id(a))
            NOTES.append('%s (%.1f g) merged into %s%s' % (a.name, ma, b.name, '' if lost < 0.01 else ' (%.1f g not kept)' % lost))
    over = [q for q in over if id(q[1]) not in absorbed and id(q[2]) not in absorbed]
    keep = []
    for mname, a, b, fr in over:
        if b.name in ('XBPI', 'XDT5') or a.name in ('XBPI', 'XDT5'):
            part = a if b.name in ('XBPI', 'XDT5') else b
            if part.comment.startswith('HALL_D_TARGET'):
                for m in mothers:
                    if part in m.items:
                        m.items.remove(part)
                NOTES.append('cart part %s (%.1f cm3) dropped: it is in the way of %s' % (part.name, part.volume(), b.comment if b.name.startswith('XB') or b.name.startswith('XD') else a.comment))
                continue
        keep.append((mname, a, b, fr))
    over = keep
    # reference assembly (cart) parts: they give way to KLF parts; among
    # themselves the smaller one is folded into the larger one when it fits
    def is_ref(x):
        return x.comment.startswith('HALL_D_TARGET') and '[cart' in x.comment
    def remove(x):
        for m in mothers:
            if x in m.items:
                m.items.remove(x)
    gone = set()
    keep = []
    for mname, a, b, fr in sorted(over, key=lambda q: q[1].volume()):
        if id(a) in gone or id(b) in gone:
            continue
        if is_ref(a) and is_ref(b):
            ma = a.volume() * a.f
            cap = b.volume() * (1.0 - b.f)
            b.f = min(1.0, b.f + ma / b.volume())
            remove(a); gone.add(id(a))
            DROPPED.append(('cart', a.name, ma * BASE.get(a.mat, 2.7), 'folded into %s' % b.name if cap >= ma else 'folded into %s, %.0f g not kept' % (b.name, (ma - cap) * BASE.get(a.mat, 2.7))))
        elif is_ref(a) or is_ref(b):
            r = a if is_ref(a) else b
            remove(r); gone.add(id(r))
            DROPPED.append(('cart', r.name, r.volume() * r.f * BASE.get(r.mat, 2.7), 'in the way of KLF part %s' % (b.name if r is a else a.name)))
        else:
            keep.append((mname, a, b, fr))
    over = keep
    for mname, a, b, fr in over:
        report.append('overlap in %s: %s (%s, %.1f cm3) with %s (%s): %.2f%% of the first'
                      % (mname, a.name, a.comment[:35], a.volume(), b.name, b.comment[:35], 100 * fr))
    # mass bookkeeping (kg): model = volume x f x density of every placed
    # solid; CAD = CAD volume x the density of the material assigned here
    mass = {'cart': [0.0, 0.0], 'KLF cryostat and lines': [0.0, 0.0]}
    for m in mothers:
        for x in m.items:
            if x.mat in ('Vacuum', 'Air', 'DROP'):
                continue
            g = 'cart' if (x.comment.startswith('HALL_D_TARGET') and '[cart' in x.comment) else 'KLF cryostat and lines'
            mass[g][0] += x.volume() * x.f * BASE.get(x.mat, 2.7) / 1000
    for t, p in prims.items():
        e = S_named.get(t, {})
        path = e.get('path', ['', '', ''])
        top = path[1] if len(path) > 1 else ''
        b = np.array(V[int(t)]['bb'])
        mat, why = material_of(t, path, (cad_to_lass(b[:3]), cad_to_lass(b[3:])))
        g = 'cart' if (top.startswith('HALL_D_TARGET') and why.startswith('cart')) else 'KLF cryostat and lines'
        if re.match(r'^cross, 16 inch', path[-1]) or re.match(r'^Body1', path[-1]):
            mat = 'StainlessSteel'
        mass[g][1] += p['vcad'] / 1000 * BASE.get(mat, 2.7) / 1000
    json.dump(dict(notes=NOTES, report=report, dropped=DROPPED, mass_kg=mass), open(out_report, 'w'), indent=1)
    return placed, mothers, over, fixed


# -------------------------------------------------------------- XML output
AXCODE = {'+z': 'PZ', '-z': 'MZ', '+x': 'PX', '-x': 'MX', '+y': 'PY', '-y': 'MY'}


def write_xml(out, mothers, extra_mothers_xml=None):
    M = {m.name: m for m in mothers}
    newname = Namer('Q')
    used_mats = set()
    shapes, comps = [], {}
    comps_extra = []

    def items_xml(m):
        L = []
        for s in m.items:
            if not hasattr(s, 'hname'):
                s.hname = s.name if (len(s.name) == 4 and s.name[0] == 'X') else newname()
                mat = scaled(s.mat, s.f) if s.mat != 'Vacuum' else 'Vacuum'
                used_mats.add(mat)
                shapes.extend(shape_xml(s.hname, s, mat))
                if hasattr(s, 'hole'):
                    ax, hc, hr = s.hole
                    hn = newname()
                    o2 = [j for j in range(3) if j != ax]
                    pt = s.o.copy(); pt[o2[0]], pt[o2[1]] = hc[0], hc[1]
                    loc = s.R.T @ (pt - s.o)
                    rot = {2: '', 1: ' rot="90 0 0"', 0: ' rot="0 90 0"'}[ax]
                    shapes.append('  <tubs name="%s" Rio_Z="0 %s %s" material="Vacuum" comment="hole"/>' % (hn, fmt(hr), fmt(s.par[ax])))
                    comps_extra.append('  <composition name="hole%s" envelope="%s">' % (s.hname, s.hname))
                    comps_extra.append('    <posXYZ volume="%s" X_Y_Z="%s"%s/>' % (hn, ' '.join(fmt(v) for v in loc), rot))
                    comps_extra.append('  </composition>')
            NAMEMAP[s.hname] = dict(name=s.name, tag=getattr(s, 'tag', ''), comment=s.comment, mother=m.name)
            L.append(place_xml(('hole' + s.hname) if hasattr(s, 'hole') else s.hname, s, m))
        return L

    cc = np.array([0, 0, ZC])
    X = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<!--DOCTYPE HDDS>',
         '',
         '  Hall D Geometry Data Base: KLF LH2 target cryostat, entrance port and cart',
         '  *************************************************************************',
         '',
         '     version 1.0: generated by build_cryostat.py from the JBrock Inventor',
         '                  model TGT-401-5000-0000 (2026-11-17), with the GlueX target',
         '                  cart (reference assembly in the same STEP file) and the',
         '                  KLF v2.0 changes (6 inch entrance port). Do not edit. [claude/rtj]',
         '',
         '<HDDS specification="v1.0" xmlns="http://www.gluex.org/hdds">',
         '-->',
         '',
         '<section name        = "TargetCryostat"',
         '         version     = "1.0"',
         '         date        = "2026-11-19"',
         '         author      = "R.T. Jones"',
         '         top_volume  = "XJBX"',
         '         specification = "v1.0">',
         '',
         '<!-- All coordinates are in the LASS frame (z = z_CAD/10 + %.3f cm):' % ZLASS,
         '     targetCryostat is placed in experimentalHall at (150,-350,-500),',
         '     targetCryostatLASS in Target and targetCryostatTARG in targetVessel at z=-50.2.',
         '     The cross follows the GlueX master SixWayCross model (junction cube,',
         '     six flanged arms); everything else is fitted to the CAD solids, with',
         '     the CAD mass kept by density-scaled materials (Material_xNNN). -->',
         '']
    # top-level hall composition
    L = ['  <composition name="targetCryostat">',
         '    <posXYZ volume="crossJunction" X_Y_Z="0 0 %s"/>' % fmt(ZC)]
    for key, Ra in AXES.items():
        a = rot_angles(Ra)
        L.append('    <posXYZ volume="crossArm%s" X_Y_Z="0 0 %s" rot="%s"/>' % (AXCODE[key], fmt(ZC), ' '.join(fmt(v) for v in a)))
    for g in ('XGPY', 'XGMZ'):
        m = M[g]
        a = rot_angles(m.R)
        L.append('    <posXYZ volume="%s" X_Y_Z="%s" rot="%s"/>' % (m.comp, ' '.join(fmt(v) for v in m.o), ' '.join(fmt(v) for v in a)))
    for m in mothers:
        if m.name.startswith('XN'):
            a = rot_angles(m.R)
            L.append('    <posXYZ volume="%s" X_Y_Z="%s" rot="%s"/>' % (m.comp, ' '.join(fmt(v) for v in m.o), ' '.join(fmt(v) for v in a)))
    L += items_xml(M['HALL'])
    L.append('  </composition>')
    X += L + ['']
    # junction
    X.append('  <composition name="crossJunction" envelope="XJBX">')
    X.append('    <posXYZ volume="crossJunctionVac" X_Y_Z="0 0 0"/>')
    for key, Ra in AXES.items():
        d = Ra[:, 2] * (HALF_IN + HALF_OUT) / 2
        X.append('    <posXYZ volume="crossHole%s" X_Y_Z="%s" rot="%s"/>' % (AXCODE[key], ' '.join(fmt(v) for v in d), ' '.join(fmt(v) for v in rot_angles(Ra))))
    X.append('  </composition>')
    X.append('  <composition name="crossJunctionVac" envelope="XJVX">')
    X += items_xml(M['XJV'])
    X.append('  </composition>')
    for key, Ra in AXES.items():
        c = AXCODE[key]
        X.append('  <composition name="crossHole%s" envelope="XH%s">' % (c, c))
        X += items_xml(M['XJH' + key])
        X.append('  </composition>')
        X.append('  <composition name="crossArm%s" envelope="XA%s">' % (c, c))
        X.append('    <posXYZ volume="crossArm%sVac" X_Y_Z="0 0 %s"/>' % (c, fmt((L0 + LF1) / 2)))
        X.append('  </composition>')
        X.append('  <composition name="crossArm%sVac" envelope="XV%s">' % (c, c))
        X += items_xml(M['XAV' + key])
        X.append('  </composition>')
    for g, length in (('XGPY', 34.52 - LF1), ('XGMZ', -(Z921D - ZC) - LF1)):
        X.append('  <composition name="%s" envelope="%s">' % (M[g].comp, g))
        X += items_xml(M[g])
        X.append('  </composition>')
        shapes.append('  <tubs name="%s" Rio_Z="0 %s %s" material="Vacuum" comment="vacuum in the flange joint gap"/>' % (g, fmt(RB if g == 'XGPY' else R_SPACER), fmt(length)))
    for m in mothers:
        if m.name.startswith('XN'):
            X.append('  <composition name="%s" envelope="%s">' % (m.comp, m.name))
            X += items_xml(m)
            X.append('  </composition>')
            shapes.extend(m.shape_xml)
    intarget = {}
    for m in mothers:
        if m.comp.startswith('inTarget:'):
            intarget[m.name] = items_xml(m)
    json.dump(intarget, open('target_daughters.json', 'w'), indent=0)
    for nm in ('LASS', 'TARG'):
        X.append('  <composition name="%s">' % M[nm].comp)
        X += items_xml(M[nm])
        X.append('  </composition>')
    X += comps_extra
    X.append('')
    # cross shapes
    shapes += ['  <box name="XJBX" X_Y_Z="%s %s %s" material="StainlessSteel" comment="cross junction (GlueX-style cube)"/>' % ((fmt(2 * HALF_OUT),) * 3),
               '  <box name="XJVX" X_Y_Z="%s %s %s" material="Vacuum" comment="cross junction vacuum"/>' % ((fmt(2 * HALF_IN),) * 3)]
    for key in AXES:
        c = AXCODE[key]
        shapes.append('  <tubs name="XH%s" Rio_Z="0 %s %s" material="Vacuum" comment="opening of the junction cube to arm %s"/>' % (c, fmt(RB), fmt(HALF_OUT - HALF_IN), key))
        shapes += ['  <pcon name="XA%s" material="StainlessSteel" comment="cross arm %s, tube and CF flange">' % (c, key),
                   '    <polyplane Rio_Z="0 %s %s"/>' % (fmt(RT), fmt(L0)),
                   '    <polyplane Rio_Z="0 %s %s"/>' % (fmt(RT), fmt(LF0)),
                   '    <polyplane Rio_Z="0 %s %s"/>' % (fmt(RF), fmt(LF0)),
                   '    <polyplane Rio_Z="0 %s %s"/>' % (fmt(RF), fmt(LF1)),
                   '  </pcon>',
                   '  <tubs name="XV%s" Rio_Z="0 %s %s" material="Vacuum" comment="cross arm %s bore"/>' % (c, fmt(RB), fmt(LF1 - L0), key)]
    X += shapes
    X += ['', '</section>', '', '<!-- </HDDS> -->']
    open(out, 'w').write('\n'.join(X) + '\n')
    return used_mats




# ----------------------------------------------------- hand-made overrides
# parts whose fitted envelope is poor (sparse) or that need the 6 inch
# openings; masses from the CAD (cm3 in comments)
FOLD = {'182': '215',     # 0006:1 copper straps (21.9) -> condenser copper 0046
        '213': '203', '214': '203',  # copper lid plates (2 x 52.7) -> 0006 copper ring above them
        '223': '219', '228': '219', # bent SS tubes 0048, 0049 (2.0, 5.1) -> 0045 tube
        '217': '216',             # 0047 clamshell halves (10.3 each) share one envelope
        '1498': '1488',           # two touching cart pieces
        '1077': '1078',           # two touching cart pieces
        '83': '84'}


def hbox(name, c, dims, mat, f, comment, hole_r=None, hole_c=None, hole_ax=2):
    s = Solid(name, 'box', c, np.eye(3), dims, mat, f, comment)
    if hole_r:
        s.hole = (hole_ax, np.asarray(hole_c, float), hole_r)   # hole along a global axis
    return s


def beam_hole_plate(name, x0, x1, y0, y1, z0, z1, rh, comment):
    """rectangular plate (normal along z) with a beam hole of radius rh about
    the beam axis, as a bar above the hole and two legs beside it (a hole that
    reaches the bottom edge simply opens it, as drilling would)"""
    out = []
    if y1 > rh:
        out.append(hbox(name + 'T', [(x0 + x1) / 2, (max(y0, rh) + y1) / 2, (z0 + z1) / 2],
                        [x1 - x0, y1 - max(y0, rh), z1 - z0], 'Copper', 1.0, comment + ' (above the hole)'))
    yl0, yl1 = y0, min(y1, rh)
    if yl1 > yl0:
        if x1 > rh:
            out.append(hbox(name + 'R', [(rh + x1) / 2, (yl0 + yl1) / 2, (z0 + z1) / 2], [x1 - rh, yl1 - yl0, z1 - z0],
                            'Copper', 1.0, comment + ' (beside the hole)'))
        if x0 < -rh:
            out.append(hbox(name + 'L', [(x0 - rh) / 2, (yl0 + yl1) / 2, (z0 + z1) / 2], [-rh - x0, yl1 - yl0, z1 - z0],
                            'Copper', 1.0, comment + ' (beside the hole)'))
    return out


RH = 7.68     # 6 inch clear hole (r >= 7.62) in the heat shield walls and 0032


def shield_box():
    """copper heat shield 0005 (CAD solids 85 + 86, 1152.9 cm3) by hand:
    lower box (plates 0.159 cm) around the beam with a top plate holding the
    vertical can (r 10.477-10.795, flange r 15.24 at the top); its upstream
    and downstream walls get the 6 inch beam opening; the density is scaled to
    the CAD mass"""
    cc = np.array([0, 0, ZC])
    x0, x1, y0, y1, z0, z1 = -12.065, 12.065, -7.843, 16.287, -118.02, -93.25
    t = 0.159
    zm, ym = (z0 + z1) / 2, (y0 + y1) / 2
    S = [hbox('XSB1', [0, y0 + t / 2, zm], [x1 - x0, t, z1 - z0], 'Copper', 1.0, 'heat shield 0005 bottom'),
         Solid('XSB6', 'pcon', cc, AXES['+y'], [(y1 - t, 10.477, x1 - t - 0.001), (y1, 10.477, x1 - t - 0.001)],
               'Copper', 1.0, 'heat shield 0005 top plate around the can (annulus, mass kept)'),
         hbox('XSB2', [x0 + t / 2, (y0 + t + y1) / 2, zm], [t, y1 - y0 - t, z1 - z0], 'Copper', 1.0, 'heat shield 0005 side'),
         hbox('XSB3', [x1 - t / 2, (y0 + t + y1) / 2, zm], [t, y1 - y0 - t, z1 - z0], 'Copper', 1.0, 'heat shield 0005 side')]
    S += beam_hole_plate('XSB4', x0 + t, x1 - t, y0 + t, y1 - t, z0, z0 + t, RH, 'heat shield 0005 upstream wall, 6 inch opening')
    S += beam_hole_plate('XSB5', x0 + t, x1 - t, y0 + t, y1 - t, z1 - t, z1, RH, 'heat shield 0005 downstream wall, 6 inch opening')
    S.append(Solid('XSCN', 'pcon', cc, AXES['+y'], [(y1, 10.477, 10.795), (36.791, 10.477, 10.795),
                                                    (36.791, 10.477, 15.24), (37.743, 10.477, 15.24)],
                   'Copper', 1.0, 'heat shield 0005 can and top flange'))
    vt = sum(x.volume() for x in S)
    f = (871.17 + 281.72) / vt
    for x in S:
        x.f = f
    NOTES.append('heat shield 0005: geometric %.1f cm3 for the CAD 1152.9 cm3 (density x%.2f)' % (vt, f))
    return S


def plate_0032(p):
    """copper plate 0032 (CAD 70.4 cm3, x +-11, y -6.7..15.2) with its 1 inch
    hole opened to 6 inch: the opening breaks through its lower edge"""
    c = cad_to_lass(p['c'])
    d = [v / 10 for v in p['dims']]
    R = np.array(p['R'])
    dims = [0, 0, 0]
    for j in range(3):
        dims[int(np.argmax(np.abs(R[:, j])))] = d[j]
    lo, hi = c - np.array(dims) / 2, c + np.array(dims) / 2
    S = beam_hole_plate('XSP1', lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], RH, 'heat shield plate 0032, 6 inch opening')
    area0 = dims[0] * dims[1]
    for x in S:
        x.f = p['f']            # same areal density as the CAD plate
    NOTES.append('plate 0032: %.1f of %.1f cm2 left after the 6 inch opening' % (sum(x.par[0] * x.par[1] for x in S), area0))
    return S


def bellows_0002():
    """pulse-tube mount 0002 (CAD 688.9 cm3 SS): two flanges and a bellows,
    as a pcon about the vertical axis of the cross (mass kept)"""
    cc = np.array([0, 0, ZC])
    pl = [(64.46, 3.0, 11.52), (65.40, 3.0, 11.52), (65.40, 7.8, 8.6), (71.50, 7.8, 8.6),
          (71.50, 3.0, 11.52), (72.55, 3.0, 11.52)]
    s = Solid('XBEL', 'pcon', cc, AXES['+y'], pl, 'StainlessSteel', 1.0, 'pulse tube mount 0002 (flanges + bellows)')
    s.f = min(1.0, 688.9 / s.volume())
    return s


def apply_overrides(fitted, prims):
    by_tag = {}
    for s in fitted:
        by_tag.setdefault(getattr(s, 'tag', ''), []).append(s)
    out = []
    S_named = json.load(open(SCR + 'solids_named.json'))
    hw = [t for t, e in S_named.items() if not t.startswith('_') and any('TGT-401-5000-0003' in q for q in e['path'])
          and not e['path'][-1].startswith('TGT-401-0005-0010')]
    NOTES.append('dropped: hardware on the three stage-1 support rods 5000-0003 (%d parts: bronze bushings, Al cups, brass springs, about 160 g), '
                 'polyimide blocks 0031 (3 x 1.07 cm3), VCR fitting tag 23 (3.7 cm3 SS, would hit a hexapod strut)' % len(hw))
    drop = set(hw) | set(['15', '16', '23', '20', '22', '287', '288'])
    NOTES.append('dropped near the cell base, where moving them out of the beam puts them against the hexapod struts: '
                 'copper clamp 0010 (tags 287, 288: 19.1 cm3), VCR fittings tags 20, 22 (5.4 cm3 SS)')
    drop |= set(['85', '86', '87', '178', '911', '912', '925', '946', '936', '240', '253', '266', '279', '244', '257', '5', '2', '4', '17']) | set(FOLD)
    NOTES.append('dropped at the G-10 ring edges: 0005-0007 block (1.07 cm3 SS), spring (0.83 cm3), polyimide block 0031:3 (1.07 cm3)')
    NOTES.append('springs 240, 253, 266, 279 (4 x 0.83 cm3 steel) and spring cups 244, 257 (2 x 0.66 cm3 Al) on the support rods at the shield wall dropped')
    for s in fitted:
        if getattr(s, 'tag', '') not in drop:
            out.append(s)
    # folds: add the mass to the target part (f up to 1)
    for src, dst in FOLD.items():
        if src not in prims or dst not in by_tag:
            continue
        m_src = prims[src]['vcad'] / 1000
        tgt = by_tag[dst]
        vt = sum(x.volume() * x.f for x in tgt)
        cap = sum(x.volume() for x in tgt)
        scale = min((vt + m_src) / vt, cap / vt)
        for x in tgt:
            x.f = min(1.0, x.f * scale)
        lost = vt + m_src - vt * scale
        NOTES.append('part %s (%.1f cm3) folded into %s%s' % (src, m_src, dst, '' if lost < 0.05 else ' (%.1f cm3 not kept)' % lost))
    # cryocooler frame plates 0000 (175, 176): axis-aligned boxes (their
    # principal-axis boxes touched each other)
    Vt = {str(e['tag']): e for e in json.load(open(SCR + 'vols.json'))}
    for t in ('175', '176'):
        b = np.array(Vt[t]['bb'])
        lo, hi = cad_to_lass(b[:3]), cad_to_lass(b[3:])
        out = [x for x in out if getattr(x, 'tag', '') != t]
        bx = Solid('C%04d' % int(t), 'box', (lo + hi) / 2, np.eye(3), list(hi - lo), 'StainlessSteel',
                   Vt[t]['vol'] / 1000 / float(np.prod(hi - lo)), 'TGT-401-0002-0000 frame [CAD material Stainless Steel]')
        bx.tag = t
        out.append(bx)
    # clamp blocks on the copper jackets (0010, 0011, 0008) touch each other
    # at their faces: 0.5 mm smaller boxes, mass kept
    for x in out:
        if getattr(x, 'tag', '') in ('77', '78', '81', '82', '84') and x.kind == 'box':
            v0 = x.volume()
            x.par = [max(d - 0.05, 0.01) for d in x.par]
            x.f = x.f * v0 / x.volume()
    # copper jacket 0017:2 (tag 80) ends against a hexapod strut (also in the
    # CAD, about 1 mm): shortened to end at LASS z = 6.8 (about 43 g)
    keep = []
    for x in out:
        if getattr(x, 'tag', '') == '80' and x.kind == 'pcon':
            y = x.cut(2, -1e9, 6.8)
            y.tag = '80'
            keep.append(y)
        else:
            keep.append(x)
    out = keep
    NOTES.append('copper jacket 0017:2 shortened to end at LASS z 6.8 (strut contact)')
    # the three large 'Generic' cart blocks (1041, 1042, 1043; 159, 146, 51 L)
    # are enclosures, not solid metal (Richard 2026-11-19): thin-walled
    # aluminium boxes, 3 mm walls, on the CAD outline
    Vb = {str(e['tag']): e for e in json.load(open(SCR + 'vols.json'))}
    T = 0.3
    for t in ('1041', '1042', '1043'):
        if not any(getattr(x, 'tag', '') == t for x in out):
            continue
        out = [x for x in out if getattr(x, 'tag', '') != t]
        b = np.array(Vb[t]['bb'])
        lo, hi = cad_to_lass(b[:3]) + 0.002, cad_to_lass(b[3:]) - 0.002
        hi[1] = min(hi[1], 76.99)          # top frame rails of the cart start at y 77.0
        c, d = (lo + hi) / 2, hi - lo
        comm = 'HALL_D_TARGET_ASSEMBLY 20140401:1 [cart enclosure %s, 3 mm Al shell]' % t
        plates = [  # (centre, dims): top/bottom full, x walls between them, z walls inside
            ([c[0], hi[1] - T / 2, c[2]], [d[0], T, d[2]]), ([c[0], lo[1] + T / 2, c[2]], [d[0], T, d[2]]),
            ([lo[0] + T / 2, c[1], c[2]], [T, d[1] - 2 * T, d[2]]), ([hi[0] - T / 2, c[1], c[2]], [T, d[1] - 2 * T, d[2]]),
            ([c[0], c[1], lo[2] + T / 2], [d[0] - 2 * T, d[1] - 2 * T, T]), ([c[0], c[1], hi[2] - T / 2], [d[0] - 2 * T, d[1] - 2 * T, T])]
        for k, (pc, pd) in enumerate(plates):
            x = Solid('C%s%d' % (t, k), 'box', pc, np.eye(3), pd, 'Aluminum', 1.0, comm)
            x.tag = t + '_%d' % k
            out.append(x)
        NOTES.append('cart block %s: 3 mm Al shell, %.1f kg (was %.0f kg solid)' % (t, sum(np.prod(pd) for _, pd in plates) * 2.7 / 1000, Vb[t]['vol'] / 1000 * 2.7 / 1000))
    # pulse tube valve bracket 0003 (CAD 395.9 cm3 Al) wraps the two valve
    # bodies 0000 (174, 177, bottom at y 95.4): a plate under them, mass kept
    out = [x for x in out if getattr(x, 'tag', '') != '180']
    br = Solid('XVBR', 'box', [0, (88.6 + 95.35) / 2, (-189.21 - 172.99) / 2], np.eye(3), [66.0, 95.35 - 88.6, 189.21 - 172.99],
               'Aluminum', 1.0, 'pulse tube valve bracket 0003 under the valve bodies (mass kept)')
    br.f = 395.9 / br.volume()
    out.append(br)
    for x in out:
        if getattr(x, 'tag', '') == '1049' and x.kind == 'box':
            v0 = x.volume(); x.par = [d - 0.02 for d in x.par]; x.f *= v0 / x.volume()
    # cart frame members touch face to face (box faces equal to < 1 um):
    # every cart box 20 um smaller per face, mass kept
    for x in out:
        if x.kind == 'box' and x.comment.startswith('HALL_D_TARGET') and '[cart' in x.comment:
            v0 = x.volume()
            x.par = [max(d - 0.004, 0.001) for d in x.par]
            x.f = x.f * v0 / x.volume()
    out += shield_box()
    if '87' in prims:
        out += plate_0032(prims['87'])
    out.append(bellows_0002())
    return out


if __name__ == '__main__':
    placed, mothers, over, fixed = main(sys.argv[1], sys.argv[2])
    print(len(placed), 'placed;', len(over), 'overlapping pairs')
    for m in mothers:
        print('  %-6s %4d items' % (m.name, len(m.items)))
    mats = write_xml(sys.argv[1], mothers)
    json.dump(NAMEMAP, open('namemap.json', 'w'), indent=0)
    open('materials_scaled.xml', 'w').write('\n'.join(material_xml(mats)) + '\n')
    print('materials used:', len(mats))
