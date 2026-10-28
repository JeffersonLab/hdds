#!/usr/bin/env python3
"""
hdds2fluka.py - translate an HDDS geometry (GlueX / KLF) into FLUKA
combinatorial geometry, materials and region-material assignments.

Usage examples (from the top of an hdds checkout, klf_beamline branch)
  # just the KLF flux monitor, in Hall D (HDDS global) coordinates,
  # wrapped in an air-filled container body that the host geometry subtracts
  python3 Fluka/hdds2fluka.py main_HDDS.xml --root KLFFluxMonitor -o kfm

  # the complete geometry, from the top volume down to the last straw
  python3 Fluka/hdds2fluka.py main_HDDS.xml -o klf_full

The HDDS conventions reproduced here were taken from hddsCommon.cpp and
hdds-root.cpp in the HDDS repository:
  - a <composition> with an envelope places its contents in the envelope
    frame; without an envelope its contents are placed directly into the
    nearest enclosing envelope (it is only a grouping of placements)
  - placement = shift by the position (in the mother frame), then rotate
    the local axes by rot="ax ay az": x_mother = t + Rz(az) Ry(ay) Rx(ax) x
  - box X_Y_Z, tubs Rio_Z, eltu Rxy_Z and trd Xmp_Ymp_Z give FULL lengths
  - tubs/pcon/pgon profile="phi0 dphi"; pgon radii are apothems (distance
    from the axis to the flat faces), sides spread evenly over the profile
  - trd Xmp_Ymp_Z="x- x+ y- y+ z" with inclination="a_xz a_yz": the centre
    of the +z face is displaced by (z/2 tan a_xz, z/2 tan a_yz)
  - attribute defaults come from the HDDS schema (e.g. impliedRot="true")

Only Python 3 and numpy are needed.
"""

import argparse
import math
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import numpy as np

EPS = 1e-7          # geometric tolerance (cm) for coincidence tests
NUMFMT = "%.10g"    # precision of numbers written to the geometry


class HDDSError(Exception):
    pass


# ---------------------------------------------------------------------------
# Reading the HDDS document
# ---------------------------------------------------------------------------

def _strip_ns(tag):
    return tag.split('}', 1)[1] if '}' in tag else tag


def load_hdds(mainfile):
    """Read an HDDS main file, expand its SYSTEM entities, apply schema
    defaults and return the root element plus an id -> element table."""
    topdir = os.path.dirname(os.path.abspath(mainfile))
    text = open(mainfile, encoding='utf-8').read()
    m = re.search(r'<!DOCTYPE\s+\w+\s*\[(.*?)\]\s*>', text, re.S)
    if not m:
        raise HDDSError("no DOCTYPE entity block found in %s" % mainfile)
    entities = dict(re.findall(r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"([^"]+)"\s*>',
                               m.group(1)))
    text = text[:m.start()] + text[m.end():]

    def include(match):
        name = match.group(1)
        if name not in entities:
            return match.group(0)
        path = os.path.join(topdir, entities[name])
        if not os.path.exists(path):
            raise HDDSError("%s includes %s, which does not exist"
                            % (mainfile, entities[name]))
        sub = open(path, encoding='utf-8').read()
        return re.sub(r'<\?xml[^>]*\?>', '', sub, count=1)

    text = re.sub(r'&(\w+);', include, text)
    root = ET.fromstring(text)
    for el in root.iter():
        el.tag = _strip_ns(el.tag)
        for k in list(el.attrib):
            if '}' in k:
                del el.attrib[k]

    xsd = None
    loc = re.search(r'schemaLocation="\S+\s+(\S+)"', text)
    if loc and os.path.exists(os.path.join(topdir, loc.group(1))):
        xsd = os.path.join(topdir, loc.group(1))
    if xsd:
        defaults = schema_defaults(xsd)
        for el in root.iter():
            for k, v in defaults.get(el.tag, {}).items():
                el.attrib.setdefault(k, v)

    table = {}
    for el in root.iter():
        name = el.get('name')
        if name and el.tag not in ('real', 'int', 'string', 'real_array',
                                   'int_array', 'string_data',
                                   'reference_data', 'reference_vector',
                                   'reference', 'section'):
            table[name] = el
    return root, table


def schema_defaults(xsd):
    """Attribute defaults for every top-level element of the HDDS schema."""
    sroot = ET.parse(xsd).getroot()
    xs = '{http://www.w3.org/2001/XMLSchema}'
    out = {}
    for el in sroot.findall(xs + 'element'):
        d = {}
        for att in el.iter(xs + 'attribute'):
            if att.get('name') and att.get('default') is not None:
                d[att.get('name')] = att.get('default')
        out[el.get('name')] = d
    return out


# ---------------------------------------------------------------------------
# Units
# ---------------------------------------------------------------------------

LENGTH = {'cm': 1.0, 'mm': 0.1, 'm': 100.0, 'km': 1e5, 'um': 1e-4,
          'nm': 1e-7, 'in': 2.54, 'ft': 30.48, 'mil': 2.54e-3}
ANGLE = {'deg': math.pi / 180, 'rad': 1.0, 'mrad': 1e-3, 'urad': 1e-6}


def ulen(el):
    u = el.get('unit_length', 'cm')
    if u not in LENGTH:
        raise HDDSError("unknown unit_length=\"%s\" on <%s %s>"
                        % (u, el.tag, el.get('name') or el.get('volume')))
    return LENGTH[u]


def uang(el):
    u = el.get('unit_angle', 'deg')
    if u not in ANGLE:
        raise HDDSError("unknown unit_angle=\"%s\" on <%s %s>"
                        % (u, el.tag, el.get('name') or el.get('volume')))
    return ANGLE[u]


def floats(s, n=None):
    v = [float(x) for x in s.split()]
    if n is not None and len(v) != n:
        raise HDDSError("expected %d numbers in '%s'" % (n, s))
    return v


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------

def rot_xyz(ax, ay, az):
    """HDDS Refsys::rotate: R_new = R_old . Rz(az) . Ry(ay) . Rx(ax)"""
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


class Frame:
    """x_global = t + R x_local"""
    __slots__ = ('R', 't')

    def __init__(self, R=None, t=None):
        self.R = np.eye(3) if R is None else R
        self.t = np.zeros(3) if t is None else t

    def place(self, origin, angles):
        """child frame: shift by origin (in this frame), then rotate"""
        t = self.t + self.R @ np.asarray(origin, float)
        R = self.R @ rot_xyz(*angles) if any(angles) else self.R
        return Frame(R, t)

    def compose(self, other):
        return Frame(self.R @ other.R, self.t + self.R @ other.t)

    def inverse(self):
        return Frame(self.R.T, -self.R.T @ self.t)

    def point(self, p):
        return self.t + self.R @ np.asarray(p, float)

    def vector(self, v):
        return self.R @ np.asarray(v, float)


# ---------------------------------------------------------------------------
# Flattening the placement tree
# ---------------------------------------------------------------------------

SHAPES = ('box', 'tubs', 'pcon', 'pgon', 'trd', 'eltu', 'cons', 'sphere')


class PV:
    """One physical placement of a solid (a FLUKA region-to-be)."""
    __slots__ = ('id', 'el', 'name', 'frame', 'mother', 'daughters',
                 'path', 'inroot', 'field', 'region', 'shape', 'layer')

    def __init__(self, el, frame, mother, path, inroot, field):
        self.el = el
        self.name = el.get('name')
        self.frame = frame
        self.mother = mother
        self.daughters = []
        self.path = path
        self.inroot = inroot
        self.field = field
        self.region = None
        self.shape = None
        self.layer = 0


class Flattener:
    def __init__(self, table, root_name=None):
        self.table = table
        self.root_name = root_name
        self.pvs = []
        self.root_frames = []

    def get(self, name):
        if name not in self.table:
            raise HDDSError("volume '%s' is not defined" % name)
        return self.table[name]

    def run(self, top):
        el = self.get(top)
        if el.tag == 'composition' and not el.get('envelope'):
            raise HDDSError("top volume '%s' must have an envelope" % top)
        self.place(el, Frame(), None, top, self.root_name in (None, top),
                   False, 0)
        return self.pvs

    def new_pv(self, el, frame, mother, path, inroot, field, layer):
        pv = PV(el, frame, mother, path, inroot, field)
        pv.layer = layer
        pv.id = len(self.pvs)
        self.pvs.append(pv)
        if mother is not None:
            mother.daughters.append(pv)
        return pv

    def place(self, el, frame, mother, path, inroot, field, layer):
        name = el.get('name')
        if name == self.root_name:
            inroot = True
            self.root_frames.append(frame)
        if el.tag in SHAPES:
            self.new_pv(el, frame, mother, path, inroot, field, layer)
            return
        if el.tag in ('union', 'intersection', 'subtraction'):
            raise HDDSError("boolean solid '%s' is not supported yet" % name)
        if el.tag in ('stackX', 'stackY', 'stackZ'):
            raise HDDSError("'%s' (%s) is not supported yet" % (name, el.tag))
        if el.tag != 'composition':
            raise HDDSError("cannot place '%s' of type <%s>" % (name, el.tag))

        cont = mother
        cframe = frame
        env = el.get('envelope')
        envel = self.get(env) if env else None
        for c in list(el) + (list(envel) if envel is not None else []):
            if c.tag == 'apply':
                reg = self.get(c.get('region'))
                field = any(x.tag != 'noBfield' for x in reg)
        if envel is not None:
            cont = self.new_pv(envel, frame, mother, path, inroot, field,
                               layer)
        seen = {}
        for c in el:
            if c.tag in ('apply',) or not c.get('volume'):
                continue
            targ = self.get(c.get('volume'))
            L, A = ulen(c), uang(c)
            ang = [a * A for a in floats(c.get('rot', '0 0 0'), 3)]
            # k-th placement command of this volume in this composition
            k = seen[c.get('volume')] = seen.get(c.get('volume'), 0) + 1
            for i, (org, angles) in enumerate(self.positions(c, L, A, ang)):
                sub = "%s/%s" % (path, c.get('volume'))
                if k > 1:
                    sub += "#%d" % k
                if c.tag != 'posXYZ' and c.tag != 'posRPhiZ':
                    sub += "[%d]" % i
                self.place(targ, cframe.place(org, angles), cont, sub,
                           inroot, field,
                           layer + int(c.get('geometry_layer', '0')))

    @staticmethod
    def positions(c, L, A, ang):
        tag = c.tag
        S = float(c.get('S', '0')) * L
        if tag == 'posXYZ':
            return [([v * L for v in floats(c.get('X_Y_Z'), 3)], ang)]
        if tag == 'posRPhiZ':
            r, phi, z = floats(c.get('R_Phi_Z'), 3)
            r, phi, z = r * L, phi * A, z * L
            a = list(ang)
            if c.get('impliedRot') == 'true' and phi != 0:
                a[2] += phi
            return [([r * math.cos(phi) - S * math.sin(phi),
                      r * math.sin(phi) + S * math.cos(phi), z], a)]
        n = int(c.get('ncopy'))
        out = []
        if tag == 'mposPhi':
            phi0 = float(c.get('Phi0', '0')) * A
            dphi = (float(c.get('dPhi')) * A if c.get('dPhi')
                    else 2 * math.pi / n)
            r, z = [v * L for v in floats(c.get('R_Z'), 2)]
            implied = c.get('impliedRot') == 'true'
            for i in range(n):
                phi = phi0 + i * dphi
                a = list(ang)
                if implied:
                    a[2] += phi
                out.append(([r * math.cos(phi) - S * math.sin(phi),
                             r * math.sin(phi) + S * math.cos(phi), z], a))
        elif tag == 'mposR':
            r0, dr = float(c.get('R0')) * L, float(c.get('dR')) * L
            z, phi = floats(c.get('Z_Phi'), 2)
            z, phi = z * L, phi * A
            for i in range(n):
                r = r0 + i * dr
                out.append(([r * math.cos(phi) - S * math.sin(phi),
                             r * math.sin(phi) + S * math.cos(phi), z], ang))
        elif tag == 'mposX':
            x0, dx = float(c.get('X0')) * L, float(c.get('dX')) * L
            y, z = [v * L for v in floats(c.get('Y_Z'), 2)]
            for i in range(n):
                out.append(([x0 + i * dx, y + S, z], ang))
        elif tag == 'mposY':
            y0, dy = float(c.get('Y0')) * L, float(c.get('dY')) * L
            z, x = [v * L for v in floats(c.get('Z_X'), 2)]
            for i in range(n):          # (S is ignored here, as in HDDS)
                out.append(([x, y0 + i * dy, z], ang))
        elif tag == 'mposZ':
            z0, dz = float(c.get('Z0')) * L, float(c.get('dZ')) * L
            if c.get('X_Y') is not None:
                x, y = [v * L for v in floats(c.get('X_Y'), 2)]
            else:
                r, phi = floats(c.get('R_Phi'), 2)
                x, y = r * L * math.cos(phi * A), r * L * math.sin(phi * A)
            phi = math.atan2(y, x)
            x, y = x - S * math.sin(phi), y + S * math.cos(phi)
            for i in range(n):
                out.append(([x, y, z0 + i * dz], ang))
        else:
            raise HDDSError("placement <%s> is not supported" % tag)
        return out


# ---------------------------------------------------------------------------
# Bounding proxies used to decide which solids can touch which
# ---------------------------------------------------------------------------

class OBB:
    """oriented bounding box: centre c, axes = columns of R, half sizes h"""
    __slots__ = ('c', 'R', 'h', 'lo', 'hi', 'cols', 'ct', 'ht')

    def __init__(self, c, R, h):
        self.c, self.R, self.h = np.asarray(c, float), R, np.asarray(h, float)
        ext = np.abs(R) @ self.h
        self.lo, self.hi = self.c - ext, self.c + ext
        self.cols = tuple(tuple(float(x) for x in R[:, k]) for k in range(3))
        self.ct = tuple(float(x) for x in self.c)
        self.ht = tuple(float(x) for x in self.h)


class Capsule:
    """segment p0-p1 swept by a sphere of radius r"""
    __slots__ = ('p0', 'p1', 'r', 'lo', 'hi')

    def __init__(self, p0, p1, r):
        self.p0 = tuple(float(x) for x in p0)
        self.p1 = tuple(float(x) for x in p1)
        self.r = float(r)
        a0, a1 = np.asarray(self.p0), np.asarray(self.p1)
        self.lo = np.minimum(a0, a1) - r
        self.hi = np.maximum(a0, a1) + r


class Ring:
    """solid of revolution bound: axis a through o, axial range s0..s1,
    radial range rmin..rmax"""
    __slots__ = ('a', 'o', 's0', 's1', 'rmin', 'rmax', 'lo', 'hi')

    def __init__(self, a, o, s0, s1, rmin, rmax):
        self.a, self.o = np.asarray(a, float), np.asarray(o, float)
        self.s0, self.s1, self.rmin, self.rmax = s0, s1, max(rmin, 0.0), rmax
        p0, p1 = self.o + self.a * s0, self.o + self.a * s1
        ext = rmax * np.sqrt(np.maximum(0.0, 1 - self.a ** 2))
        self.lo = np.minimum(p0, p1) - ext
        self.hi = np.maximum(p0, p1) + ext


class Cyl:
    """finite cylinder: axis segment p0-p1, radius r (exact solid bound)"""
    __slots__ = ('p0', 'p1', 'r', 'a', 'h', 'c', 'lo', 'hi')

    def __init__(self, p0, p1, r):
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0
        L = float(np.linalg.norm(d))
        self.a = tuple(float(x) for x in d / L) if L > 0 else (0.0, 0.0, 1.0)
        self.h = L / 2
        self.c = tuple(float(x) for x in (p0 + p1) / 2)
        self.p0, self.p1, self.r = tuple(p0), tuple(p1), float(r)
        ext = np.abs(d) / 2 + r * np.sqrt(np.maximum(0.0, 1 - (d / L) ** 2)) \
            if L > 0 else np.full(3, r)
        self.lo = (p0 + p1) / 2 - ext
        self.hi = (p0 + p1) / 2 + ext


def _cyl_half(cy, n):
    """half-width of the projection of cylinder cy onto unit vector n"""
    an = abs(cy.a[0] * n[0] + cy.a[1] * n[1] + cy.a[2] * n[2])
    return cy.h * an + cy.r * math.sqrt(max(0.0, 1 - an * an))


def _closest_dir(A, B):
    """unit vector between the closest points of the two axis segments"""
    p1, q1, p2, q2 = A.p0, A.p1, B.p0, B.p1
    d1 = [q1[i] - p1[i] for i in range(3)]
    d2 = [q2[i] - p2[i] for i in range(3)]
    r = [p1[i] - p2[i] for i in range(3)]
    a = sum(x * x for x in d1)
    e = sum(x * x for x in d2)
    f = sum(d2[i] * r[i] for i in range(3))
    c = sum(d1[i] * r[i] for i in range(3))
    bb = sum(d1[i] * d2[i] for i in range(3))
    den = a * e - bb * bb
    s = min(max((bb * f - c * e) / den, 0.0), 1.0) if den > 1e-14 else 0.0
    t = (bb * s + f) / e if e > 1e-14 else 0.0
    if t < 0:
        t, s = 0.0, min(max(-c / a, 0.0), 1.0) if a > 1e-14 else 0.0
    elif t > 1:
        t, s = 1.0, min(max((bb - c) / a, 0.0), 1.0) if a > 1e-14 else 0.0
    v = [r[i] + d1[i] * s - d2[i] * t for i in range(3)]
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v] if n > 1e-12 else None


def _cyl_disjoint(A, B, tol):
    """separating-axis test between two finite cylinders (sufficient)"""
    T = [B.c[i] - A.c[i] for i in range(3)]
    axes = [A.a, B.a]
    x = (A.a[1] * B.a[2] - A.a[2] * B.a[1], A.a[2] * B.a[0] - A.a[0] * B.a[2],
         A.a[0] * B.a[1] - A.a[1] * B.a[0])
    nx = math.sqrt(sum(v * v for v in x))
    if nx > 1e-9:
        axes.append([v / nx for v in x])
    d = _closest_dir(A, B)
    if d is not None:
        axes.append(d)
    for n in axes:
        if abs(T[0] * n[0] + T[1] * n[1] + T[2] * n[2]) > \
                _cyl_half(A, n) + _cyl_half(B, n) - tol:
            return True
    return False


def _cyl_obb_disjoint(A, B, tol):
    """separating-axis test between a finite cylinder and an oriented box"""
    T = [B.ct[i] - A.c[i] for i in range(3)]
    axes = list(B.cols) + [A.a]
    for col in B.cols:
        x = (A.a[1] * col[2] - A.a[2] * col[1], A.a[2] * col[0] - A.a[0] * col[2],
             A.a[0] * col[1] - A.a[1] * col[0])
        nx = math.sqrt(sum(v * v for v in x))
        if nx > 1e-9:
            axes.append([v / nx for v in x])
    for n in axes:
        hb = sum(B.ht[k] * abs(B.cols[k][0] * n[0] + B.cols[k][1] * n[1] +
                               B.cols[k][2] * n[2]) for k in range(3))
        if abs(T[0] * n[0] + T[1] * n[1] + T[2] * n[2]) > \
                _cyl_half(A, n) + hb - tol:
            return True
    return False


class Poly:
    """bound for parts of a pgon: points whose polygonal radius (distance
    to the plane of the side facing them) lies in amin..amax, sides every
    `pitch` radians starting with a side normal at `phase`"""
    __slots__ = ('a', 'o', 's0', 's1', 'R', 'pitch', 'phase', 'amin', 'amax',
                 'ring', 'lo', 'hi')

    def __init__(self, frame, s0, s1, pitch, phase, amin, amax):
        self.R, self.o = frame.R, frame.t
        self.a = frame.R[:, 2]
        self.s0, self.s1, self.pitch, self.phase = s0, s1, pitch, phase
        self.amin, self.amax = max(amin, 0.0), amax
        self.ring = Ring(self.a, self.o, s0, s1, self.amin,
                         amax / math.cos(pitch / 2))
        self.lo, self.hi = self.ring.lo, self.ring.hi


def _poly_disjoint(A, B, tol):
    """coaxial polygons with the same side directions: compare the axial
    and polygonal-radius ranges"""
    if abs(A.pitch - B.pitch) > 1e-9:
        return False
    Q = A.R.T @ B.R
    if abs(Q[2, 2] - 1) > 1e-9:
        return False
    d = A.R.T @ (B.o - A.o)
    if abs(d[0]) > 1e-7 or abs(d[1]) > 1e-7:
        return False
    delta = math.atan2(Q[1, 0], Q[0, 0])
    x = (B.phase + delta - A.phase) / A.pitch
    if abs(x - round(x)) > 1e-7:
        return False
    s0, s1 = B.s0 + d[2], B.s1 + d[2]
    if min(A.s1, s1) - max(A.s0, s0) <= tol:
        return True
    return A.amax <= B.amin + tol or B.amax <= A.amin + tol


def _ring_rel(A, B):
    """B seen from A: B's axial range projected on A's axis, the overlap
    with A's axial range, and bounds on the distance from A's axis of
    B's points inside that overlap (lo_r, hi_r); None if not parallel"""
    c = A.a @ B.a
    if abs(c) < 1 - 1e-4:
        return None
    sin = math.sqrt(max(0.0, 1 - c * c))
    d0 = (B.o - A.o) @ A.a
    q = sorted((d0 + c * B.s0, d0 + c * B.s1))
    q = (q[0] - B.rmax * sin, q[1] + B.rmax * sin)
    ov = (max(A.s0, q[0]), min(A.s1, q[1]))
    if ov[1] <= ov[0]:
        return q, ov, 0.0, 0.0

    def perp(sv):
        x = B.o + B.a * ((sv - d0) / c) - A.o
        return x - A.a * (x @ A.a)
    P0, P1 = perp(ov[0]), perp(ov[1])
    V = P1 - P0
    t = 0.0 if V @ V < 1e-30 else min(max(-(P0 @ V) / (V @ V), 0.0), 1.0)
    dmin = np.linalg.norm(P0 + V * t)
    dmax = max(np.linalg.norm(P0), np.linalg.norm(P1))
    hi_r = dmax + B.rmax + 1e-9
    lo_r = max(0.0, dmin - B.rmax, B.rmin * abs(c) - dmax) - 1e-9
    return q, ov, lo_r, hi_r


def _ring_disjoint(A, B, tol):
    rel = _ring_rel(A, B)
    if rel is None:
        return False
    q, ov, lo_r, hi_r = rel
    if ov[1] - ov[0] <= tol:
        return True
    return hi_r <= A.rmin + tol or lo_r >= A.rmax - tol


def contained(small, big, tol=EPS):
    """True if proxy small lies inside the exact solid big"""
    if isinstance(small, Poly):
        small = small.ring
    if isinstance(small, Ring) and isinstance(big, Ring):
        rel = _ring_rel(big, small)
        if rel is None:
            return False
        q, ov, lo_r, hi_r = rel
        return (q[0] >= big.s0 - tol and q[1] <= big.s1 + tol and
                hi_r <= big.rmax + tol and
                (big.rmin <= tol or lo_r >= big.rmin - tol))
    if isinstance(small, OBB) and isinstance(big, OBB):
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    x = small.c + small.R @ (small.h * (sx, sy, sz))
                    if np.any(np.abs(big.R.T @ (x - big.c)) > big.h + tol):
                        return False
        return True
    return False


def _obb_disjoint(a, b, tol):
    """separating-axis test for two oriented boxes (plain floats)"""
    A = a.cols
    B = b.cols
    ah, bh = a.ht, b.ht
    T = (b.ct[0] - a.ct[0], b.ct[1] - a.ct[1], b.ct[2] - a.ct[2])
    R = [[A[i][0] * B[j][0] + A[i][1] * B[j][1] + A[i][2] * B[j][2]
          for j in range(3)] for i in range(3)]
    Ra = [[abs(R[i][j]) + 1e-12 for j in range(3)] for i in range(3)]
    t = [T[0] * A[i][0] + T[1] * A[i][1] + T[2] * A[i][2] for i in range(3)]
    for i in range(3):
        if abs(t[i]) > ah[i] + bh[0] * Ra[i][0] + bh[1] * Ra[i][1] + \
                bh[2] * Ra[i][2] - tol:
            return True
    for j in range(3):
        tb = t[0] * R[0][j] + t[1] * R[1][j] + t[2] * R[2][j]
        if abs(tb) > ah[0] * Ra[0][j] + ah[1] * Ra[1][j] + ah[2] * Ra[2][j] \
                + bh[j] - tol:
            return True
    for i in range(3):
        i1, i2 = (i + 1) % 3, (i + 2) % 3
        for j in range(3):
            j1, j2 = (j + 1) % 3, (j + 2) % 3
            ra = ah[i1] * Ra[i2][j] + ah[i2] * Ra[i1][j]
            rb = bh[j1] * Ra[i][j2] + bh[j2] * Ra[i][j1]
            if abs(t[i2] * R[i1][j] - t[i1] * R[i2][j]) > ra + rb - tol:
                n2 = 1 - R[i][j] * R[i][j]
                if n2 > 1e-12:     # skip near-parallel edge pairs
                    return True
    return False


def _seg_dist(p1, q1, p2, q2):
    """distance between segments p1-q1 and p2-q2 (plain floats)"""
    d1 = (q1[0] - p1[0], q1[1] - p1[1], q1[2] - p1[2])
    d2 = (q2[0] - p2[0], q2[1] - p2[1], q2[2] - p2[2])
    r = (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])
    a = d1[0] * d1[0] + d1[1] * d1[1] + d1[2] * d1[2]
    e = d2[0] * d2[0] + d2[1] * d2[1] + d2[2] * d2[2]
    f = d2[0] * r[0] + d2[1] * r[1] + d2[2] * r[2]
    if a < 1e-14 and e < 1e-14:
        s = t = 0.0
    elif a < 1e-14:
        s, t = 0.0, min(max(f / e, 0.0), 1.0)
    else:
        c = d1[0] * r[0] + d1[1] * r[1] + d1[2] * r[2]
        if e < 1e-14:
            t, s = 0.0, min(max(-c / a, 0.0), 1.0)
        else:
            bb = d1[0] * d2[0] + d1[1] * d2[1] + d1[2] * d2[2]
            den = a * e - bb * bb
            s = min(max((bb * f - c * e) / den, 0.0), 1.0) if den > 1e-14 \
                else 0.0
            t = (bb * s + f) / e
            if t < 0:
                t, s = 0.0, min(max(-c / a, 0.0), 1.0)
            elif t > 1:
                t, s = 1.0, min(max((bb - c) / a, 0.0), 1.0)
    x = r[0] + d1[0] * s - d2[0] * t
    y = r[1] + d1[1] * s - d2[1] * t
    z = r[2] + d1[2] * s - d2[2] * t
    return math.sqrt(x * x + y * y + z * z)


def _agg(pl):
    """intersection of the axis-aligned bounds of a proxy list (cached)"""
    key = id(pl)
    c = _AGG.get(key)
    if c is not None and c[0] is pl:
        return c[1]
    lo = [max(p.lo[i] for p in pl) for i in range(3)]
    hi = [min(p.hi[i] for p in pl) for i in range(3)]
    _AGG[key] = (pl, (lo, hi))
    if len(_AGG) > 400000:
        _AGG.clear()
    return lo, hi


_AGG = {}


def disjoint(pa, pb, tol=EPS):
    """True if two proxy lists provably do not share interior volume"""
    (la, ha), (lb, hb) = _agg(pa), _agg(pb)
    for i in range(3):
        if la[i] >= hb[i] - tol or lb[i] >= ha[i] - tol:
            return True
    for a in pa:
        for b in pb:
            if isinstance(a, Ring) and isinstance(b, Ring):
                if _ring_disjoint(a, b, tol):
                    return True
            elif isinstance(a, Capsule) and isinstance(b, Capsule):
                if _seg_dist(a.p0, a.p1, b.p0, b.p1) >= a.r + b.r - tol:
                    return True
            elif isinstance(a, Poly) and isinstance(b, Poly):
                if _poly_disjoint(a, b, tol):
                    return True
            elif isinstance(a, Cyl):
                if isinstance(b, Cyl):
                    if _cyl_disjoint(a, b, tol):
                        return True
                elif isinstance(b, OBB) and _cyl_obb_disjoint(a, b, tol):
                    return True
            elif isinstance(b, Cyl) and isinstance(a, OBB):
                if _cyl_obb_disjoint(b, a, tol):
                    return True
    for a in pa:
        if isinstance(a, OBB):
            for b in pb:
                if isinstance(b, OBB) and _obb_disjoint(a, b, tol):
                    return True
    return False


def aabb(proxies):
    lo = np.max([p.lo for p in proxies], axis=0)
    hi = np.min([p.hi for p in proxies], axis=0)
    return lo, hi


# ---------------------------------------------------------------------------
# FLUKA bodies
# ---------------------------------------------------------------------------

B36 = "0123456789abcdefghijklmnopqrstuvwxyz"


def base36(n, width):
    s = ""
    while n:
        n, r = divmod(n, 36)
        s = B36[r] + s
    return s.rjust(width, '0')


class BodyTable:
    PREFIX = {'RPP': 'r', 'BOX': 'x', 'RCC': 'c', 'TRC': 't', 'PLA': 'p',
              'REC': 'e'}

    def __init__(self, prefix='', transforms=True):
        self.prefix = prefix
        self.bodies = []          # (name, type, params, rotation name)
        self.keys = {}
        self.ntiny = 0
        self.transforms = transforms
        self.rotations = {}       # key -> (name, R, cards)

    def add(self, btype, params, rot=None):
        params = [0.0 if abs(v) < 1e-12 else float(v) for v in params]
        key = (btype, rot) + tuple(round(v, 7) for v in params)
        name = self.keys.get(key)
        if name is None:
            name = (self.PREFIX[btype] + self.prefix
                    + base36(len(self.bodies), 8 - 1 - len(self.prefix)))
            self.keys[key] = name
            self.bodies.append((name, btype, params, rot))
        return name

    def rotation(self, R):
        """name of a ROT-DEFI transformation whose matrix is R (body
        local -> global); two z-axis cards: Rz(-phi2) . Ry(-theta1) .
        Rz(-phi1)"""
        key = tuple(np.round(R, 10).ravel())
        if key in self.rotations:
            return self.rotations[key][0]
        name = 'rt' + base36(len(self.rotations) + 1, 5)
        self.rotations[key] = (name, R, rotdefi_angles(R))
        return name

    def add_named(self, name, btype, params):
        if any(b[0] == name for b in self.bodies):
            raise HDDSError("body name %s already used" % name)
        self.bodies.append((name, btype, [float(v) for v in params], None))
        return name

    def plane(self, normal, point):
        """half-space n.(x-p) < 0, canonical so coincident planes share
        one body; returns a signed literal"""
        n = np.asarray(normal, float)
        n = n / np.linalg.norm(n)
        d = n @ np.asarray(point, float)
        # canonical orientation: first significant component positive
        k = int(np.argmax(np.abs(n) > 1e-9))
        sign = '+'
        if n[k] < 0:
            n, d, sign = -n, -d, '-'
        name = self.add('PLA', list(n) + list(n * d))
        return sign + name


def _ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def rotdefi_matrix(cards):
    """matrix of a chain of z-axis ROT-DEFI cards [(theta, phi) deg], in
    the convention of the FLUKA manual as implemented by pyg4ometry: one
    card is Ry(-theta) Rz(-phi); later cards act after earlier ones"""
    M = np.eye(3)
    for th, ph in cards:
        M = _ry(-math.radians(th)) @ _rz(-math.radians(ph)) @ M
    return M


def rotdefi_angles(R):
    """two z-axis ROT-DEFI cards reproducing the proper rotation R"""
    b = math.acos(max(-1.0, min(1.0, R[2, 2])))
    if math.sin(b) > 1e-9:
        a = math.atan2(R[1, 2], R[0, 2])
        c = math.atan2(R[2, 1], -R[2, 0])
    else:
        a, c = math.atan2(R[1, 0], R[0, 0]) if R[2, 2] > 0 else \
            math.atan2(-R[1, 0], -R[0, 0]), 0.0
    # R = Rz(a) Ry(b) Rz(c) = Rz(a+pi) Ry(-b) Rz(c-pi)
    def wrap(x):
        x = math.degrees(x)
        while x > 180:
            x -= 360
        while x < -180:
            x += 360
        return x
    # one card Ry(-theta) Rz(-phi) suffices when R[1,2] = R[2,1]... = 0
    th = math.atan2(-R[0, 2], R[2, 2])
    if th < 0:
        th += 2 * math.pi
    if th <= math.pi + 1e-12:
        ph = math.atan2(-R[1, 0], R[1, 1])
        one = [(math.degrees(th), wrap(ph))]
        if np.allclose(rotdefi_matrix(one), R, atol=1e-9):
            return one
    cards = [(math.degrees(b), wrap(-(c - math.pi))), (0.0, wrap(-(a + math.pi)))]
    if not np.allclose(rotdefi_matrix(cards), R, atol=1e-9):
        raise HDDSError("could not express a rotation as ROT-DEFI cards")
    return cards


def lit_neg(lit):
    return ('-' if lit[0] == '+' else '+') + lit[1:]


# ---------------------------------------------------------------------------
# Solids: hull body, exact solid zones, slack zones (hull minus solid)
# ---------------------------------------------------------------------------

class Zone:
    """intersection of signed bodies; prox are bounding proxies (supersets),
    excl are exact solids known to be excluded by negative literals"""
    __slots__ = ('lits', 'prox', 'excl', 'wp')

    def __init__(self, lits, prox, excl=(), wp=None):
        self.lits = list(lits)
        self.prox = list(prox)
        self.excl = list(excl)
        self.wp = wp          # extra proxy valid only inside the own wedge

    def wedged(self, w):
        """this zone cut by its own solid's wedge literals w"""
        return Zone(self.lits + w, self.prox + ([self.wp] if self.wp else []),
                    self.excl)

    def cut(self, other):
        return Zone(self.lits + other.lits, self.prox + other.prox,
                    self.excl + other.excl)

    def empty(self):
        return any(contained(p, x) for p in self.prox for x in self.excl)


class Solid:
    """FLUKA view of one placed HDDS shape.
       hull      : literal of a single body containing the whole solid
       hprox     : proxies of the hull
       full      : zones of the solid ignoring any phi profile
       slack     : zones of (hull - full)
       wedge     : None, or (phi0, dphi) of the profile (local frame) with
                   frame/axis info for phi families"""
    __slots__ = ('hull', 'hprox', 'full', 'slack', 'phi', 'frame', 'key',
                 'hexcl', 'cyl', 'wedge_in_slack')

    def __init__(self):
        self.phi = None
        self.key = None
        self.hexcl = None
        self.cyl = None
        self.wedge_in_slack = False


def tiny(bt, r):
    if r < 1e-6:
        bt.ntiny += 1
        return 1e-6
    return r


def phi_zones(bt, frame, a, d):
    """zones (literal lists) for the azimuthal interval [a, a+d] (radians)
    about the local z axis of frame; [] means 'everything'"""
    if d >= 2 * math.pi - 1e-12:
        return [[]]
    o = frame.t

    def P(ang):    # half-space phi in (ang, ang+pi) == n.x > 0, n=(-s,c,0)
        n = frame.vector((-math.sin(ang), math.cos(ang), 0.0))
        return bt.plane(-n, o)       # inside of PLA is -n.x... < 0
    b = a + d
    if d <= math.pi + 1e-12:
        return [[P(a), lit_neg(P(b))]]
    return [[P(a)], [lit_neg(P(b))]]


def cyl_prox(frame, za, zb, rmin, rmax):
    """proxies of the part of a coaxial ring za<z<zb, rmin<r<rmax"""
    return [OBB(frame.point((0, 0, 0.5 * (za + zb))), frame.R,
                (rmax, rmax, 0.5 * (zb - za))),
            Capsule(frame.point((0, 0, za)), frame.point((0, 0, zb)), rmax),
            Ring(frame.R[:, 2], frame.t, za, zb, rmin, rmax),
            Cyl(frame.point((0, 0, za)), frame.point((0, 0, zb)), rmax)]


def solid_revolution(bt, frame, planes):
    """planes: [(z, rmin, rmax), ...] in increasing z (pcon/tubs/cons)"""
    s = Solid()
    zs = [p[0] for p in planes]
    if any(zs[i + 1] < zs[i] - EPS for i in range(len(zs) - 1)):
        raise HDDSError("polyplane z values must not decrease")
    z0, z1 = zs[0], zs[-1]
    Rmax = max(p[2] for p in planes)
    axis = frame.vector((0, 0, 1))
    base = frame.point((0, 0, z0))
    s.hull = '+' + bt.add('RCC', list(base) + list(axis * (z1 - z0)) + [Rmax])
    s.hprox = cyl_prox(frame, z0, z1, 0.0, Rmax)
    s.hexcl = s.hprox[2]
    s.full, s.slack = [], []
    slabs = [(planes[i], planes[i + 1]) for i in range(len(planes) - 1)
             if planes[i + 1][0] - planes[i][0] > EPS]

    def zplane(z):   # half-space below z
        return bt.plane(axis, frame.point((0, 0, z)))

    for j, ((za, ria, roa), (zb, rib, rob)) in enumerate(slabs):
        if max(roa, rob) <= EPS:
            out = None
        elif (abs(roa - Rmax) < EPS and abs(rob - Rmax) < EPS
              and len(slabs) == 1):
            out = s.hull
        else:
            out = '+' + cone(bt, frame, za, zb, roa, rob)
        inn = None
        if max(ria, rib) > EPS:
            inn = '+' + cone(bt, frame, za, zb, ria, rib)
        bounds = []
        if j > 0:
            bounds.append(lit_neg(zplane(za)))
        if j < len(slabs) - 1:
            bounds.append(zplane(zb))
        if out is not None:
            s.full.append(Zone([out] + ([lit_neg(inn)] if inn else []),
                               cyl_prox(frame, za, zb, min(ria, rib),
                                        max(roa, rob))))
        full_radius = abs(roa - Rmax) < EPS and abs(rob - Rmax) < EPS
        if out != s.hull and not full_radius:   # hull outside this cone
            s.slack.append(Zone([s.hull] + bounds +
                                ([lit_neg(out)] if out else []),
                                cyl_prox(frame, za, zb, min(roa, rob), Rmax)))
        if inn:
            s.slack.append(Zone([inn], cyl_prox(frame, za, zb, 0.0,
                                                max(ria, rib))))
    return s


def cone(bt, frame, za, zb, ra, rb):
    if abs(ra - rb) < 1e-9:
        return bt.add('RCC', list(frame.point((0, 0, za))) +
                      list(frame.vector((0, 0, zb - za))) + [ra])
    if ra > rb:
        return bt.add('TRC', list(frame.point((0, 0, za))) +
                      list(frame.vector((0, 0, zb - za))) + [ra, tiny(bt, rb)])
    return bt.add('TRC', list(frame.point((0, 0, zb))) +
                  list(frame.vector((0, 0, za - zb))) + [rb, tiny(bt, ra)])


def solid_polygon(bt, frame, planes, nseg, phi0, dphi):
    """pgon: apothem radii, nseg flat sides spread over [phi0, phi0+dphi]"""
    s = Solid()
    zs = [p[0] for p in planes]
    if any(zs[i + 1] < zs[i] - EPS for i in range(len(zs) - 1)):
        raise HDDSError("polyplane z values must not decrease")
    z0, z1 = zs[0], zs[-1]
    half = dphi / nseg / 2
    sec = 1 / math.cos(half)
    Rhull = max(p[2] for p in planes) * sec
    axis = frame.vector((0, 0, 1))
    base = frame.point((0, 0, z0))
    s.hull = '+' + bt.add('RCC', list(base) + list(axis * (z1 - z0)) + [Rhull])
    s.hprox = cyl_prox(frame, z0, z1, 0.0, Rhull)
    s.hexcl = s.hprox[2]
    s.full, s.slack = [], []
    slabs = [(planes[i], planes[i + 1]) for i in range(len(planes) - 1)
             if planes[i + 1][0] - planes[i][0] > EPS]
    angles = [phi0 + (2 * k + 1) * half for k in range(nseg)]

    def side(ang, za, zb, ra, rb):
        u = np.array([math.cos(ang), math.sin(ang), 0.0])
        slope = (rb - ra) / (zb - za)
        n = np.array([u[0], u[1], -slope])
        p = np.array([ra * u[0], ra * u[1], za])
        return bt.plane(frame.vector(n), frame.point(p))

    pitch, phase = 2 * half, phi0 + half
    closed = dphi >= 2 * math.pi - 1e-9

    def poly(za, zb, amin, amax):
        return Poly(frame, za, zb, pitch, phase, amin, amax)

    for j, ((za, ria, roa), (zb, rib, rob)) in enumerate(slabs):
        bounds = []
        if j > 0:
            bounds.append(lit_neg(bt.plane(axis, frame.point((0, 0, za)))))
        if j < len(slabs) - 1:
            bounds.append(bt.plane(axis, frame.point((0, 0, zb))))
        outs = [side(a, za, zb, roa, rob) for a in angles]
        base_lits = [s.hull] + bounds
        fpoly = poly(za, zb, min(ria, rib), max(roa, rob))
        fprox = cyl_prox(frame, za, zb, min(ria, rib), max(roa, rob) * sec) \
            + ([fpoly] if closed else [])
        fwp = None if closed else fpoly
        if max(ria, rib) > EPS:
            ins = [side(a, za, zb, ria, rib) for a in angles]
            for k in range(nseg):
                s.full.append(Zone(base_lits + outs + [lit_neg(ins[k])], fprox,
                                   wp=fwp))
            hpoly = poly(za, zb, 0.0, max(ria, rib))
            s.slack.append(Zone(base_lits + ins,
                                cyl_prox(frame, za, zb, 0.0,
                                         max(ria, rib) * sec) +
                                ([hpoly] if closed else []),
                                wp=None if closed else hpoly))
        else:
            s.full.append(Zone(base_lits + outs, fprox, wp=fwp))
        oprox = cyl_prox(frame, za, zb, min(roa, rob), Rhull) + \
            [poly(za, zb, min(roa, rob), Rhull)]
        for o in outs:
            s.slack.append(Zone(base_lits + [lit_neg(o)], oprox))
    return s


def solid_box(bt, frame, hx, hy, hz, center=(0, 0, 0)):
    s = Solid()
    R = frame.R
    c = frame.point(center)
    s.hprox = [OBB(c, R, (hx, hy, hz))]
    if np.all(np.abs(np.abs(R) - np.round(np.abs(R))) < 1e-12) and \
            np.allclose(np.abs(R).sum(axis=0), 1):
        ext = np.abs(R) @ np.array([hx, hy, hz])
        lo, hi = c - ext, c + ext
        s.hull = '+' + bt.add('RPP', [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]])
    elif bt.transforms:              # RPP in the rotated frame
        rot = bt.rotation(R)
        cl = R.T @ c
        s.hull = '+' + bt.add('RPP', [cl[0] - hx, cl[0] + hx, cl[1] - hy,
                                      cl[1] + hy, cl[2] - hz, cl[2] + hz],
                              rot)
    else:
        v = frame.point(np.asarray(center) - (hx, hy, hz))
        s.hull = '+' + bt.add('BOX', list(v) + list(R[:, 0] * 2 * hx) +
                              list(R[:, 1] * 2 * hy) + list(R[:, 2] * 2 * hz))
    s.hexcl = s.hprox[0]
    s.full = [Zone([s.hull], s.hprox)]
    s.slack = []
    return s


def solid_trd(bt, frame, xm, xp, ym, yp, zl, axz, ayz):
    dz = zl / 2
    tx, ty = math.tan(axz), math.tan(ayz)
    # face edges: (x at -dz, x at +dz) for +x and -x faces, same for y
    xpl, xpu = xm / 2 - dz * tx, xp / 2 + dz * tx
    xml, xmu = -xm / 2 - dz * tx, -xp / 2 + dz * tx
    ypl, ypu = ym / 2 - dz * ty, yp / 2 + dz * ty
    yml, ymu = -ym / 2 - dz * ty, -yp / 2 + dz * ty
    xlo, xhi = min(xml, xmu), max(xpl, xpu)
    ylo, yhi = min(yml, ymu), max(ypl, ypu)
    c = ((xlo + xhi) / 2, (ylo + yhi) / 2, 0.0)
    s = solid_box(bt, frame, (xhi - xlo) / 2, (yhi - ylo) / 2, dz, c)
    faces = []
    # (outward normal, point, sliver box lo/hi in local coords)
    for (a, b, sgn, ax) in ((xpl, xpu, 1, 0), (xml, xmu, -1, 0),
                            (ypl, ypu, 1, 1), (yml, ymu, -1, 1)):
        if abs(a - b) < 1e-9 and abs(a - (xhi if ax == 0 and sgn > 0 else
                                          xlo if ax == 0 else
                                          yhi if sgn > 0 else ylo)) < 1e-9:
            continue          # face coincides with the hull face
        n = np.zeros(3)
        n[ax] = sgn * 2 * dz
        n[2] = -sgn * (b - a)
        p = np.zeros(3)
        p[ax] = a
        p[2] = -dz
        lit = bt.plane(frame.vector(n), frame.point(p))
        lo = [xlo, ylo, -dz]
        hi = [xhi, yhi, dz]
        if sgn > 0:
            lo[ax] = min(a, b)
        else:
            hi[ax] = max(a, b)
        sc = (np.array(lo) + np.array(hi)) / 2
        sh = (np.array(hi) - np.array(lo)) / 2
        faces.append((lit, OBB(frame.point(sc), frame.R, sh)))
    s.full = [Zone([s.hull] + [f[0] for f in faces], s.hprox)]
    s.slack = [Zone([s.hull, lit_neg(f[0])], [f[1]]) for f in faces]
    return s


def solid_eltu(bt, frame, rx, ry, zl):
    s = Solid()
    s.hull = '+' + bt.add('REC', list(frame.point((0, 0, -zl / 2))) +
                          list(frame.vector((0, 0, zl))) +
                          list(frame.vector((rx, 0, 0))) +
                          list(frame.vector((0, ry, 0))))
    s.hprox = [OBB(frame.t, frame.R, (rx, ry, zl / 2))]
    s.full = [Zone([s.hull], s.hprox)]
    s.slack = []
    return s


def make_solid(bt, pv):
    el, f = pv.el, pv.frame
    L, A = ulen(el), uang(el)
    tag = el.tag
    phi = None
    if tag == 'box':
        x, y, z = [v * L for v in floats(el.get('X_Y_Z'), 3)]
        s = solid_box(bt, f, x / 2, y / 2, z / 2)
    elif tag == 'tubs':
        ri, ro, z = [v * L for v in floats(el.get('Rio_Z'), 3)]
        s = solid_revolution(bt, f, [(-z / 2, ri, ro), (z / 2, ri, ro)])
        phi = el.get('profile')
    elif tag == 'cons':
        rim, rom, rip, rop, z = [v * L for v in
                                 floats(el.get('Rio1_Rio2_Z'), 5)]
        s = solid_revolution(bt, f, [(-z / 2, rim, rom), (z / 2, rip, rop)])
        phi = el.get('profile')
    elif tag == 'pcon':
        planes = []
        for pp in el.findall('polyplane'):
            ri, ro, z = [v * ulen(pp) for v in floats(pp.get('Rio_Z'), 3)]
            planes.append((z, ri, ro))
        s = solid_revolution(bt, f, planes)
        phi = el.get('profile')
    elif tag == 'pgon':
        planes = []
        for pp in el.findall('polyplane'):
            ri, ro, z = [v * ulen(pp) for v in floats(pp.get('Rio_Z'), 3)]
            planes.append((z, ri, ro))
        p0, dp = [v * A for v in floats(el.get('profile'), 2)]
        s = solid_polygon(bt, f, planes, int(el.get('segments')), p0, dp)
        phi = el.get('profile')
    elif tag == 'trd':
        xm, xp, ym, yp, z = [v * L for v in floats(el.get('Xmp_Ymp_Z'), 5)]
        axz, ayz = [v * A for v in floats(el.get('inclination', '0 0'), 2)]
        s = solid_trd(bt, f, xm, xp, ym, yp, z, axz, ayz)
    elif tag == 'eltu':
        rx, ry, z = [v * L for v in floats(el.get('Rxy_Z'), 3)]
        s = solid_eltu(bt, f, rx, ry, z)
    else:
        raise HDDSError("shape <%s> (%s) is not supported yet"
                        % (tag, pv.name))
    s.frame = f
    if phi is not None:
        p0, dp = [v * A for v in floats(phi, 2)]
        if dp < 2 * math.pi - 1e-9:
            s.phi = (p0, dp)
    s.key = s.hull          # phi sectors sharing this cylinder group
    return s


def sector_obb(frame, a, d, rmin, R, s0, s1):
    """oriented box around the sector a..a+d (d <= pi) of a ring"""
    if d > math.pi + 1e-9:
        return None
    h = d / 2
    pts = [(r * math.cos(t), r * math.sin(t)) for t in (-h, h)
           for r in (R, rmin)] + [(R, 0.0)]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    bf = Frame(frame.R @ rot_xyz(0, 0, a + h), frame.t)
    c = ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, (s0 + s1) / 2)
    return OBB(bf.point(c), bf.R, ((max(xs) - min(xs)) / 2,
                                   (max(ys) - min(ys)) / 2, (s1 - s0) / 2))


def sector_hull(bt, s):
    """replace the full-cylinder hull of a phi segment by the box around
    the sector; the cylinder form is kept in s.cyl for phi families"""
    cyl = Solid()
    cyl.hull, cyl.hprox, cyl.hexcl, cyl.full, cyl.slack = (
        s.hull, s.hprox, s.hexcl, s.full, s.slack)
    cyl.frame, cyl.phi, cyl.key = s.frame, s.phi, s.key
    s.cyl = cyl
    ring = s.hprox[2]
    R = ring.rmax
    rmin = min([z.prox[2].rmin for z in s.full if len(z.prox) > 2] or [0.0])
    p0, dp = s.phi
    mid = p0 + dp / 2              # box aligned with the sector bisector
    h = dp / 2
    angs = [-h, h] + ([0.0] if h > 0 else [])
    pts = [(r * math.cos(a), r * math.sin(a)) for a in angs
           for r in ((R, rmin) if a != 0.0 else (R,))]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    zc = 0.5 * (ring.s0 + ring.s1)
    hz = 0.5 * (ring.s1 - ring.s0)
    bframe = Frame(s.frame.R @ rot_xyz(0, 0, mid), s.frame.t)
    box = solid_box(bt, bframe, (max(xs) - min(xs)) / 2,
                    (max(ys) - min(ys)) / 2, hz,
                    ((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, zc))
    bo = box.hprox[0]
    w = phi_zones(bt, s.frame, p0, dp)[0]       # [+P(a), -P(b)]
    slack = [Zone([box.hull, lit_neg(cyl.hull)], [bo])]
    slack += [Zone([box.hull] + z.lits, z.prox + [bo]) for z in cyl.slack]
    for z in cyl.full:
        for l in w:
            slack.append(Zone([box.hull] + z.lits + [lit_neg(l)],
                              z.prox + [bo]))
    s.hull, s.hprox, s.hexcl = box.hull, [bo, ring], box.hexcl
    s.slack = slack
    s.wedge_in_slack = True


# ---------------------------------------------------------------------------
# Regions: mother minus daughters
# ---------------------------------------------------------------------------

class Unit:
    """what a mother must cut out: one daughter, or a family of phi
    sectors sharing the same hull"""
    __slots__ = ('index', 'hull', 'hprox', 'slack', 'lo', 'hi', 'hexcl')


MAX_PIECES = 4000      # zones per decomposition before splitting
MAX_BODIES = 300       # bodies per region before splitting
MAX_DEPTH = 24


class RegionBuilder:
    def __init__(self, bt):
        self.bt = bt
        self.warnings = []
        self.nsplit = 0
        self.max_bodies = MAX_BODIES

    def solid_zones(self, s):
        """exact zones of a placed solid (full zones cut by its wedge)"""
        if s.phi is None:
            return [Zone(z.lits, z.prox) for z in s.full]
        wz = phi_zones(self.bt, s.frame, s.phi[0], s.phi[1])
        return [z.wedged(w) for z in s.full for w in wz]

    def units(self, daughters):
        """group daughters into cut units"""
        fam = {}
        out = []
        for d in daughters:
            s = d.shape
            if s.phi is not None:
                fam.setdefault(s.key, []).append(d)
            else:
                out.append(self.single_unit(s))
        for members in fam.values():
            cover = sum(m.shape.phi[1] for m in members)
            if len(members) > 2 or (len(members) == 2 and cover > math.pi):
                out.extend(self.family_units(members))
            else:
                out.extend(self.single_unit(m.shape) for m in members)
        for i, u in enumerate(out):
            u.index = i
            u.lo, u.hi = aabb(u.hprox)
        return out

    def single_unit(self, s):
        if (s.phi is not None and s.cyl is None and
                s.phi[1] <= math.pi + 1e-9):
            sector_hull(self.bt, s)       # tight box around the sector
        u = Unit()
        u.hull, u.hprox, u.hexcl = s.hull, s.hprox, s.hexcl
        u.slack = list(s.slack)
        if s.phi is not None and not s.wedge_in_slack:
            p0, dp = s.phi
            for w in phi_zones(self.bt, s.frame, p0 + dp, 2 * math.pi - dp):
                u.slack.append(Zone([s.hull] + w, s.hprox))
            wz = phi_zones(self.bt, s.frame, p0, dp)
            u.slack = [z.wedged(w) for z in s.slack
                       for w in wz] + u.slack[len(s.slack):]
        return u

    def family_units(self, members):
        """phi sectors of one shape about a common axis: one unit whose
        slack is each member's slack inside its own wedge plus the gaps"""
        ref = members[0].shape.frame
        ivals = []
        for d in members:
            s = d.shape.cyl or d.shape
            Q = ref.R.T @ s.frame.R
            if (abs(Q[2, 2] - 1) > 1e-9 or
                    np.linalg.norm(ref.R.T @ (s.frame.t - ref.t)) > 1e-6):
                return [self.single_unit(m.shape) for m in members]
            delta = math.atan2(Q[1, 0], Q[0, 0])
            a = (s.phi[0] + delta) % (2 * math.pi)
            ivals.append((a, s.phi[1], d))
        ivals.sort(key=lambda v: v[0])
        for k in range(len(ivals)):
            a, dp, _ = ivals[k]
            nxt = ivals[(k + 1) % len(ivals)][0] + (2 * math.pi if
                                                     k == len(ivals) - 1 else 0)
            if a + dp > nxt + 1e-9 and len(ivals) > 1:
                self.warnings.append("overlapping phi sectors of %s"
                                     % members[0].name)
                return [self.single_unit(m.shape) for m in members]
        u = Unit()
        s0 = members[0].shape.cyl or members[0].shape
        u.hull, u.hprox, u.hexcl = s0.hull, s0.hprox, s0.hexcl
        ring = s0.hprox[2]
        cyls = [d.shape.cyl or d.shape for _, _, d in ivals]
        uniform = all([z.lits for z in c.full] == [z.lits for z in s0.full]
                      and [z.lits for z in c.slack] ==
                      [z.lits for z in s0.slack] for c in cyls)
        gaps = []
        for k in range(len(ivals)):
            a, dp, _ = ivals[k]
            b = ivals[(k + 1) % len(ivals)][0]
            gap = (b - (a + dp)) % (2 * math.pi)
            if gap > 2 * math.pi - 1e-9:      # rounding: touching sectors
                gap = 0.0
            if len(ivals) == 1:
                gap = 2 * math.pi - dp
            if gap > 1e-9:
                gaps.append((a + dp, gap))
        u.slack = []
        if uniform:
            u.slack.extend(Zone(z.lits, z.prox) for z in s0.slack)
            for a, g in gaps:
                ob = sector_obb(ref, a, g, 0.0, ring.rmax, ring.s0, ring.s1)
                for w in phi_zones(self.bt, ref, a, g):
                    for z in s0.full:
                        u.slack.append(Zone(z.lits + w, z.prox +
                                            ([ob] if ob else [])))
        else:
            for a, dp, d in ivals:
                c = d.shape.cyl or d.shape
                for w in phi_zones(self.bt, c.frame, c.phi[0], c.phi[1]):
                    for z in c.slack:
                        u.slack.append(z.wedged(w))
            for a, g in gaps:
                ob = sector_obb(ref, a, g, 0.0, ring.rmax, ring.s0, ring.s1)
                for w in phi_zones(self.bt, ref, a, g):
                    u.slack.append(Zone([u.hull] + w,
                                        u.hprox + ([ob] if ob else [])))
        return [u]

    def region_parts(self, own, daughters, obb):
        """(union of own zones) minus all daughters, as a list of parts;
        each part is a list of zones that becomes its own FLUKA region.
        Large or explosive regions are split by planes across obb."""
        if not daughters:
            return [own]
        return self.split(own, self.units(daughters), obb, 0)

    def region_zones(self, own, daughters, obb=None):
        parts = self.region_parts(own, daughters, obb)
        return [z for p in parts for z in p]

    def split(self, own, units, obb, depth):
        los = np.array([u.lo for u in units]) if units else None
        lo, hi = obb.lo, obb.hi
        if units:
            m = np.all(los < hi - EPS, axis=1) & \
                np.all(np.array([u.hi for u in units]) > lo + EPS, axis=1)
            units = [units[i] for i in np.nonzero(m)[0]
                     if not disjoint([obb], units[i].hprox)]
        for i, u in enumerate(units):
            u.index = i
        zones = None
        if not units:
            zones = own
        elif len(units) <= self.max_bodies or depth >= MAX_DEPTH:
            try:
                zones = self.direct(own, units)
            except Explode:
                pass
        if zones is not None and (self.nbodies(zones) <= self.max_bodies
                                  or depth >= MAX_DEPTH):
            return [zones]
        cut = self.choose_cut(units, obb) if depth < MAX_DEPTH else None
        if cut is None:
            if zones is None:
                raise HDDSError("region decomposition exploded and the "
                                "region cannot be split further")
            return [zones]
        k, v = cut
        a = obb.R[:, k]
        c0 = obb.c @ a
        below = self.bt.plane(a, a * v)
        parts = []
        for lit, (s0, s1) in ((below, (c0 - obb.h[k], v)),
                              (lit_neg(below), (v, c0 + obb.h[k]))):
            h = obb.h.copy()
            h[k] = (s1 - s0) / 2
            cell = OBB(obb.c + a * ((s0 + s1) / 2 - c0), obb.R, h)
            cown = [Zone(e.lits + [lit],
                         [p for p in e.prox if p is not obb] + [cell], e.excl)
                    for e in own if not disjoint(e.prox, [cell])]
            if cown:
                parts.extend(self.split(cown, list(units), cell, depth + 1))
        self.nsplit += 1
        return parts

    @staticmethod
    def nbodies(zones):
        return len({l[1:] for z in zones for l in z.lits})

    @staticmethod
    def choose_cut(units, obb):
        """axis of obb along which the daughters are most spread out, cut at
        the median of their centres"""
        best = None
        for k in range(3):
            a = obb.R[:, k]
            c0 = obb.c @ a
            lo, hi = c0 - obb.h[k], c0 + obb.h[k]
            cs = sorted({round(u.hprox[0].c @ a, 6) for u in units})
            cs = [c for c in cs if lo + 1e-4 < c < hi - 1e-4]
            if len(cs) < 2:
                continue
            spread = (cs[-1] - cs[0]) / (hi - lo)
            n = len(cs)
            v = 0.5 * (cs[(n - 1) // 2] + cs[n // 2]) if n % 2 == 0 else \
                0.5 * (cs[n // 2 - 1] + cs[n // 2])
            score = (n, spread)
            if best is None or score > best[0]:
                best = (score, (k, v))
        return best[1] if best else None

    def direct(self, own, units):
        los = np.array([u.lo for u in units])
        his = np.array([u.hi for u in units])

        def candidates(prox, skip=-1):
            lo, hi = aabb(prox)
            m = np.all(los < hi - EPS, axis=1) & np.all(his > lo + EPS, axis=1)
            return [units[i] for i in np.nonzero(m)[0]
                    if i != skip and not disjoint(prox, units[i].hprox)]

        result = []
        for e in own:
            cut = [lit_neg(u.hull) for u in candidates(e.prox)]
            result.append(Zone(e.lits + cut, e.prox))
        for u in units:
            for s in u.slack:
                for e in own:
                    if disjoint(s.prox, e.prox):
                        continue
                    result.extend(self.refine(s.cut(e), u, candidates))
                    if len(result) > MAX_PIECES:
                        raise Explode()
        return result

    def refine(self, piece, u, candidates):
        if piece.empty():
            return []
        pieces = [piece]
        for v in candidates(piece.prox, u.index):
            nxt = []
            for p in pieces:
                if disjoint(p.prox, v.hprox) or any(
                        contained(h, x) for h in v.hprox for x in p.excl):
                    nxt.append(p)
                    continue
                ex = [v.hexcl] if v.hexcl is not None else []
                if v.index < u.index:   # its slack was handled with v
                    q = Zone(p.lits + [lit_neg(v.hull)], p.prox, p.excl + ex)
                    if not q.empty():
                        nxt.append(q)
                    continue
                q = Zone(p.lits + [lit_neg(v.hull)], p.prox, p.excl + ex)
                if not q.empty():
                    nxt.append(q)
                for t in v.slack:
                    if not disjoint(p.prox, t.prox):
                        q = p.cut(t)
                        if not q.empty():
                            nxt.append(q)
            pieces = nxt
            if len(pieces) > MAX_PIECES:
                raise Explode()
        return pieces


class Explode(Exception):
    pass


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

FLUKA_ELEMENT = {
    1: 'HYDROGEN', 2: 'HELIUM', 3: 'LITHIUM', 4: 'BERYLLIU', 5: 'BORON',
    6: 'CARBON', 7: 'NITROGEN', 8: 'OXYGEN', 9: 'FLUORINE', 10: 'NEON',
    11: 'SODIUM', 12: 'MAGNESIU', 13: 'ALUMINUM', 14: 'SILICON',
    15: 'PHOSPHO', 16: 'SULFUR', 17: 'CHLORINE', 18: 'ARGON',
    19: 'POTASSIU', 20: 'CALCIUM', 22: 'TITANIUM', 24: 'CHROMIUM',
    25: 'MANGANES', 26: 'IRON', 27: 'COBALT', 28: 'NICKEL', 29: 'COPPER',
    30: 'ZINC', 31: 'GALLIUM', 32: 'GERMANIU', 33: 'ARSENIC', 35: 'BROMINE',
    36: 'KRYPTON', 38: 'STRONTIU', 40: 'ZIRCONIU', 42: 'MOLYBDEN',
    47: 'SILVER', 48: 'CADMIUM', 49: 'INDIUM', 50: 'TIN', 51: 'ANTIMONY',
    53: 'IODINE', 54: 'XENON', 55: 'CESIUM', 56: 'BARIUM', 57: 'LANTHANU',
    58: 'CERIUM', 64: 'GADOLINI', 73: 'TANTALUM', 74: 'TUNGSTEN',
    78: 'PLATINUM', 79: 'GOLD', 80: 'MERCURY', 82: 'LEAD', 83: 'BISMUTH',
    90: 'THORIUM', 92: 'URANIUM'}

# materials predefined in FLUKA (no MATERIAL card needed)
FLUKA_PREDEFINED = {'BLCKHOLE', 'VACUUM', 'HYDROGEN', 'HELIUM', 'BERYLLIU',
                    'CARBON', 'NITROGEN', 'OXYGEN', 'MAGNESIU', 'ALUMINUM',
                    'IRON', 'COPPER', 'SILVER', 'SILICON', 'GOLD', 'MERCURY',
                    'LEAD', 'TANTALUM', 'SODIUM', 'ARGON', 'CALCIUM', 'TIN',
                    'TUNGSTEN', 'TITANIUM', 'NICKEL'}


DERIVED_DENSITY = {}


def density_of(el, table=None):
    for r in el.findall('real'):
        if r.get('name') == 'density':
            unit = r.get('unit', 'g/cm^3')
            if unit not in ('g/cm^3', 'g/cm3'):
                raise HDDSError("density unit %s of %s" % (unit, el.get('name')))
            return float(r.get('value'))
    parts = el.findall('addmaterial')
    if table is None or not parts:
        raise HDDSError("material %s has no density" % el.get('name'))
    # as hddsCommon.cpp Substance: volume-additive mixture of the parts,
    # weights = natoms * A, or the mass fractions
    num = den = 0.0
    for p in parts:
        sub = table[p.get('material')]
        if p.find('natoms') is not None:
            w = float(p.find('natoms').get('n')) * float(sub.get('a'))
        else:
            w = float(p.find('fractionmass').get('fraction'))
        num += w
        den += w / density_of(sub, table)
    rho = num / den
    DERIVED_DENSITY[el.get('name')] = rho
    return rho


class Materials:
    """HDDS elements/composites -> FLUKA MATERIAL/COMPOUND cards"""

    def __init__(self, table, mapping=None, vacuum=('Vacuum',)):
        self.table = table
        self.map = dict(mapping or {})      # HDDS name -> FLUKA name (given)
        for v in vacuum:
            self.map.setdefault(v, 'VACUUM')
        self.names = {}                     # HDDS name -> FLUKA name
        self.cards = []
        self.used = set(self.map.values())

    def fname(self, hname):
        if hname in self.map:
            return self.map[hname]
        if hname in self.names:
            return self.names[hname]
        el = self.table[hname]
        if el.tag == 'element':
            name = FLUKA_ELEMENT.get(int(el.get('z')))
            if name is None:
                name = re.sub('[^A-Z0-9]', '', hname.upper())[:8]
            self.names[hname] = name
            if name not in self.used:
                self.used.add(name)
                if name not in FLUKA_PREDEFINED:
                    # WHAT(2) (atomic weight) is left blank: deprecated
                    # since FLUKA 4.4.0, FLUKA uses the natural element
                    self.cards.append(('MATERIAL', [float(el.get('z')), 0.0,
                                       density_of(el, self.table)],
                                       name, hname))
            return name
        base = re.sub('[^A-Z0-9]', '', hname.upper())[:8] or 'MAT'
        if not base[0].isalpha():
            base = ('M' + base)[:8]
        name, k = base, 0
        while name in self.used or name in FLUKA_PREDEFINED:
            k += 1
            suf = str(k)
            name = base[:8 - len(suf)] + suf
        self.used.add(name)
        self.names[hname] = name
        comp = self.composition(hname)
        self.cards.append(('MATERIAL', [0.0, 0.0, density_of(el, self.table)], name, hname))
        self.cards.append(('COMPOUND', comp, name, hname))
        return name

    def composition(self, hname):
        """list of (amount, element FLUKA name); amount>0 atoms, <0 mass"""
        el = self.table[hname]
        parts = el.findall('addmaterial')
        if all(p.find('natoms') is not None and
               self.table[p.get('material')].tag == 'element' for p in parts):
            return [(float(p.find('natoms').get('n')),
                     self.fname(p.get('material'))) for p in parts]
        mass = {}
        for elname, w in self.elemental(hname).items():
            mass[self.fname(elname)] = mass.get(self.fname(elname), 0) + w
        return [(-w, n) for n, w in mass.items()]

    def elemental(self, hname, scale=1.0):
        """elemental mass fractions of a material"""
        el = self.table[hname]
        if el.tag == 'element':
            return {hname: scale}
        parts = el.findall('addmaterial')
        ws = []
        for p in parts:
            sub = self.table[p.get('material')]
            if p.find('fractionmass') is not None:
                ws.append(float(p.find('fractionmass').get('fraction')))
            elif p.find('natoms') is not None:
                if sub.tag != 'element':
                    raise HDDSError("natoms of a composite in %s" % hname)
                ws.append(float(p.find('natoms').get('n')) * float(sub.get('a')))
            else:
                raise HDDSError("no amount for %s in %s"
                                % (p.get('material'), hname))
        tot = sum(ws)
        out = {}
        for p, w in zip(parts, ws):
            for k, v in self.elemental(p.get('material'),
                                       scale * w / tot).items():
                out[k] = out.get(k, 0) + v
        return out


# ---------------------------------------------------------------------------
# Writing FLUKA input
# ---------------------------------------------------------------------------

def f10(x):
    if isinstance(x, str):
        return x.rjust(10)
    if x == int(x) and abs(x) < 1e9:
        s = "%d." % x
    else:
        for p in range(9, 0, -1):
            s = "%.*g" % (p, x)
            if len(s) <= 10:
                break
        if '.' not in s and 'e' not in s:
            s += '.'
    return s.rjust(10)


def card(name, whats, sdum=''):
    whats = list(whats) + [''] * (6 - len(whats))
    return name.ljust(10) + ''.join(
        (' ' * 10 if w == '' or w is None else f10(w)) for w in whats) + sdum


def wrap(head, tokens, width=100):
    lines, cur = [], head
    for t in tokens:
        if len(cur) + 1 + len(t) > width:
            lines.append(cur)
            cur = ' ' * 10 + t
        else:
            cur += ' ' + t
    lines.append(cur)
    return lines


def body_lines(name, btype, params):
    return wrap("%s %s" % (btype, name), [NUMFMT % p for p in params], 90)


def region_lines(name, zones):
    toks = []
    for i, z in enumerate(zones):
        if i:
            toks.append('|')
        toks.extend(z.lits)
    return wrap("%-8s 5" % name, toks)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class Translation:
    def __init__(self, mainfile, top='everything', root=None, margin=1.0,
                 container='HDDSBOX', matmap=None, field=True,
                 body_prefix='', transforms=True):
        self.root_el, self.table = load_hdds(mainfile)
        self.fl = Flattener(self.table, root)
        self.pvs = self.fl.run(top)
        if root and not self.fl.root_frames:
            raise HDDSError("volume '%s' is not placed under '%s'"
                            % (root, top))
        self.root = root
        self.bt = BodyTable(body_prefix, transforms)
        self.rb = RegionBuilder(self.bt)
        self.mats = Materials(self.table, matmap)
        self.field = field
        self.regions = []      # (name, zones, material, field, pv-or-None, note)
        self.build(margin, container)

    def build(self, margin, container):
        sel = [p for p in self.pvs if p.inroot]
        for p in sel:
            p.shape = make_solid(self.bt, p)
        counters = {}
        used = set()

        def rname(base):
            base = re.sub('[^A-Za-z0-9]', '', base)[:4] or 'R'
            if not base[0].isalpha():
                base = ('R' + base)[:4]
            k = counters.get(base, 0) + 1
            counters[base] = k
            name = base + (str(k).rjust(4, '0') if k < 10000 else
                           base36(k, 4))
            while name in used:
                k += 1
                counters[base] = k
                name = base + base36(k, 4)
            used.add(name)
            return name

        if self.root:
            tops = [p for p in sel if p.mother is None or not p.mother.inroot]
            lo = np.min([aabb(p.shape.hprox)[0] for p in tops], axis=0)
            hi = np.max([aabb(p.shape.hprox)[1] for p in tops], axis=0)
            lo, hi = lo - margin, hi + margin
            cb = self.bt.add_named(container[:8].lower(), 'RPP',
                                   [lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]])
            self.container = (cb, lo, hi)
            mothers = {id(p.mother) for p in tops}
            m = tops[0].mother
            if len(mothers) > 1:
                self.rb.warnings.append("root contents sit in several "
                                        "mothers; container uses %s" % m.name)
            own = [Zone(['+' + cb], [OBB((lo + hi) / 2, np.eye(3),
                                         (hi - lo) / 2)])]
            parts = self.rb.region_parts(own, tops, own[0].prox[0])
            mat = m.el.get('material') if m is not None else 'Air'
            for i, zones in enumerate(parts):
                name = container[:8] if len(parts) == 1 else \
                    container[:4] + base36(i + 1, 4)
                used.add(name)
                self.regions.append((name, zones, self.mats.fname(mat),
                                     m.field if m is not None else False,
                                     None, 'space inside body %s not '
                                     'occupied by %s' % (cb, self.root)))
        else:
            top = sel[0]
            lo, hi = aabb(top.shape.hprox)
            span = (hi - lo).max()
            bb = self.bt.add('RPP', list(np.ravel(list(zip(lo - span,
                                                           hi + span)))))
            self.container = None
            self.regions.append(('BLKHOLE', [Zone(['+' + bb,
                                                   lit_neg(top.shape.hull)],
                                                  [])],
                                 'BLCKHOLE', False, None, 'outside world'))
        # HDDS geometry layers: a volume on a higher layer gives way to
        # its siblings on lower layers (and so do all its descendants)
        blockers = {}
        for p in sel:
            b = list(blockers.get(id(p.mother), []))
            if p.mother is not None and p.layer > p.mother.layer:
                b += [s for s in p.mother.daughters
                      if s.layer < p.layer and s is not p and s.inroot]
            blockers[id(p)] = b
        self.nlayered = sum(1 for p in sel if blockers[id(p)])
        t0, step = time.time(), max(1, len(sel) // 20)
        for k, p in enumerate(sel):
            if len(sel) > 5000 and k % step == 0 and k:
                sys.stderr.write("  regions: %3d%% (%d of %d volumes, %.0f s)\n"
                                 % (100 * k // len(sel), k, len(sel),
                                    time.time() - t0))
            own = self.rb.solid_zones(p.shape)
            try:
                parts = self.rb.region_parts(own, p.daughters +
                                             blockers[id(p)],
                                             p.shape.hprox[0])
            except HDDSError as e:
                raise HDDSError("%s (%s): %s" % (p.name, p.path, e))
            mat = self.mats.fname(p.el.get('material'))
            for i, zones in enumerate(parts):
                name = rname(p.name)
                if i == 0:
                    p.region = name
                self.regions.append((name, zones, mat, p.field, p,
                                     'part %d of %d' % (i + 1, len(parts))
                                     if len(parts) > 1 else ''))

    # ---- output -----------------------------------------------------------
    def write(self, out, title):
        stem = os.path.basename(out)
        geo_b = []
        byrot = {}
        used = {l[1:] for _, zones, *_ in self.regions for z in zones
                for l in z.lits}
        if self.container is not None:
            used.add(self.container[0])
        bodies = [b for b in self.bt.bodies if b[0] in used]
        self.nbodies_out = len(bodies)
        rots_used = {b[3] for b in bodies if b[3] is not None}
        for name, btype, params, rot in bodies:
            if rot is None:
                geo_b.extend(body_lines(name, btype, params))
            else:
                byrot.setdefault(rot, []).append((name, btype, params))
        for rot, bl in byrot.items():
            geo_b.append('$start_transform ' + rot)
            for name, btype, params in bl:
                geo_b.extend(body_lines(name, btype, params))
            geo_b.append('$end_transform')
        rot_l = []
        rlist = [r for r in self.bt.rotations.values() if r[0] in rots_used]
        self.nrot_out = len(rlist)
        for i, (name, R, cards) in enumerate(rlist):
            for th, ph in cards:
                rot_l.append(card('ROT-DEFI', [1000 * (i + 1) + 3, th, ph],
                                  name))
        geo_r = []
        for name, zones, mat, fld, pv, note in self.regions:
            geo_r.extend(region_lines(name, zones))
        mat_l = []
        for kind, vals, name, hname in self.mats.cards:
            mat_l.append("* HDDS material %s" % hname)
            if kind == 'MATERIAL':
                z, a, rho = vals
                mat_l.append(card('MATERIAL', [z or '', a or '', rho], name))
            else:
                for i in range(0, len(vals), 3):
                    w = []
                    for amt, el in vals[i:i + 3]:
                        w += [amt, el]
                    mat_l.append(card('COMPOUND', w, name))
        asg = []
        for name, zones, mat, fld, pv, note in self.regions:
            asg.append(card('ASSIGNMA', [mat, name, '', '',
                                         1.0 if (fld and self.field) else '']))
        hdr = ["* generated by hdds2fluka.py from %s" % title]

        def put(suffix, lines):
            with open(out + suffix, 'w') as f:
                f.write('\n'.join(hdr + lines) + '\n')

        put('_bodies.inp', geo_b)
        put('_rotdefi.inp', rot_l)
        put('_regions.inp', geo_r)
        put('_materials.inp', mat_l)
        put('_assignma.inp', asg)
        with open(out + '_regions.csv', 'w') as f:
            f.write("region,material,field,hdds_volume,hdds_shape,"
                    "sensitive,hdds_path,note\n")
            for name, zones, mat, fld, pv, note in self.regions:
                if pv is None:
                    f.write("%s,%s,%d,,,,,%s\n" % (name, mat, fld, note))
                else:
                    f.write("%s,%s,%d,%s,%s,%s,%s,%s\n" % (
                        name, mat, fld, pv.name, pv.el.tag,
                        pv.el.get('sensitive', 'false'), pv.path, note))
        # a self-contained input, handy for the flair geometry viewer
        std = ["TITLE", title[:80]] + rot_l + [
               card('GEOBEGIN', [], 'COMBNAME'),
               "    0    0          %s" % title[:60]]
        extra_b, extra_r, extra_a = [], [], []
        if self.container is not None:
            cb, lo, hi = self.container
            span = (hi - lo).max()
            extra_b = body_lines('blkbody', 'RPP',
                                 list(np.ravel(list(zip(lo - span, hi + span)))))
            extra_r = region_lines('BLKHOLE', [Zone(['+blkbody', '-' + cb],
                                                    [])])
            extra_a = [card('ASSIGNMA', ['BLCKHOLE', 'BLKHOLE'])]
        std += geo_b + extra_b + ['END'] + geo_r + extra_r + ['END',
                                                             card('GEOEND', [])]
        std += mat_l + asg + extra_a + [card('STOP', [])]
        with open(out + '.inp', 'w') as f:
            f.write('\n'.join(hdr + std) + '\n')

    def summary(self):
        nz = [len(z) for _, z, *_ in self.regions]
        nl = [sum(len(x.lits) for x in z) for _, z, *_ in self.regions]
        worst = sorted(self.regions, key=lambda r: -sum(len(x.lits)
                                                        for x in r[1]))[:5]
        lines = ["%d regions, %d bodies, %d zones, %d literals"
                 % (len(self.regions), getattr(self, 'nbodies_out',
                                               len(self.bt.bodies)),
                    sum(nz), sum(nl)),
                 "largest regions: " + ", ".join(
                     "%s (%d zones, %d terms)" % (r[0], len(r[1]),
                                                  sum(len(x.lits) for x in r[1]))
                     for r in worst)]
        if self.container is not None:
            lines.append("container body %s: x %.3f..%.3f  y %.3f..%.3f  "
                         "z %.3f..%.3f cm" % ((self.container[0],) + tuple(
                             np.ravel(list(zip(self.container[1],
                                               self.container[2]))))))
        for k, v in DERIVED_DENSITY.items():
            lines.append("material %s has no density in HDDS; used the "
                         "HDDS mixture rule: %.4g g/cm3" % (k, v))
        if self.nlayered:
            lines.append("%d regions give way to lower-layer siblings "
                         "(HDDS geometry_layer)" % self.nlayered)
        if self.rb.nsplit:
            lines.append("%d plane cuts split large mother regions into "
                         "parts" % self.rb.nsplit)
        if getattr(self, 'nrot_out', 0):
            lines.append("%d rotations written as ROT-DEFI transformations "
                         "for rotated boxes" % self.nrot_out)
        if self.bt.ntiny:
            lines.append("%d cone apex radii set to 1e-6 cm" % self.bt.ntiny)
        lines += ["warning: " + w for w in self.rb.warnings]
        return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('mainfile', help='HDDS main xml (e.g. main_HDDS.xml)')
    ap.add_argument('-o', '--out', required=True,
                    help='output stem; writes STEM.inp and STEM_*.inp/.csv')
    ap.add_argument('--top', default='everything',
                    help='top composition of the HDDS tree (default: '
                         'everything)')
    ap.add_argument('--root', help='translate only this volume (positions '
                    'are still the global ones); its surroundings become an '
                    'RPP container region')
    ap.add_argument('--container', default='HDDSBOX',
                    help='region name for the --root container; its body '
                         'is the same name in lower case (default HDDSBOX, '
                         'body hddsbox)')
    ap.add_argument('--margin', type=float, default=1.0,
                    help='container margin around --root contents (cm)')
    ap.add_argument('--material-map', action='append', default=[],
                    metavar='HDDS=FLUKA', help='use an existing FLUKA '
                    'material instead of defining one (repeatable)')
    ap.add_argument('--no-field', action='store_true',
                    help='do not flag regions as having magnetic field')
    ap.add_argument('--box', action='store_true',
                    help='write rotated boxes as BOX bodies instead of RPPs '
                         'under ROT-DEFI transformations')
    ap.add_argument('--body-prefix', default='',
                    help='extra characters in body names to avoid clashes '
                         'with a host geometry')
    a = ap.parse_args(argv)
    mm = dict(x.split('=', 1) for x in a.material_map)
    tr = Translation(a.mainfile, a.top, a.root, a.margin, a.container, mm,
                     not a.no_field, a.body_prefix, not a.box)
    title = "%s%s" % (os.path.basename(a.mainfile),
                      (" root=" + a.root) if a.root else "")
    tr.write(a.out, title)
    print(tr.summary())


if __name__ == '__main__':
    try:
        main()
    except HDDSError as e:
        sys.exit("hdds2fluka: error: %s" % e)
