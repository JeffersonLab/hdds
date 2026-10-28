#!/usr/bin/env python3
"""
verify.py - independent check of an hdds2fluka translation.

  1. reads back the generated FLUKA input (bodies + regions) with its own
     parser and evaluates region membership of sample points,
  2. classifies the same points directly against the HDDS placement tree
     with exact point-in-shape tests written from the HDDS conventions,
  3. requires every point to be in exactly one FLUKA region, and that
     region to be the HDDS volume the point is in (or the container /
     blackhole region outside everything).

usage: verify.py MAIN_HDDS.xml STEM [--root VOL] [--per-volume N]
                 [--uniform N] [--max-volumes N] [--seed S]
"""

import argparse
import csv
import math
import sys
import time

import numpy as np

import hdds2fluka as H


# ---------------------------------------------------------------- FLUKA side

def rot_matrix(cards):
    """ROT-DEFI chain (z-axis cards, degrees) as written by the FLUKA
    manual / pyg4ometry: each card is Ry(-theta) Rz(-phi), applied in order"""
    M = np.eye(3)
    for th, ph in cards:
        t, p = math.radians(th), math.radians(ph)
        ry = np.array([[math.cos(t), 0, -math.sin(t)], [0, 1, 0],
                       [math.sin(t), 0, math.cos(t)]])
        rz = np.array([[math.cos(p), math.sin(p), 0],
                       [-math.sin(p), math.cos(p), 0], [0, 0, 1]])
        M = ry @ rz @ M
    return M


def read_fluka(path):
    lines = open(path).read().split('\n')
    g = next(k for k, l in enumerate(lines) if l.startswith('GEOBEGIN'))
    rots = {}
    for l in lines[:g]:
        if l.startswith('ROT-DEFI'):
            w = [l[10 + 10 * k:20 + 10 * k].strip() for k in range(6)]
            if int(float(w[0])) % 10 != 3:
                raise ValueError("only z-axis ROT-DEFI cards are handled")
            rots.setdefault(l[70:].strip(), []).append(
                (float(w[1] or 0), float(w[2] or 0)))
    mats = {k: rot_matrix(c) for k, c in rots.items()}
    i = g + 2
    bodies, regions = {}, {}
    cur = None
    section = 'bodies'
    xform = None
    for l in lines[i:]:
        if l.startswith('*') or not l.strip():
            continue
        if l.startswith('$start_transform'):
            xform = mats[l.split()[1]]
            continue
        if l.startswith('$end_transform'):
            xform = None
            continue
        if l.startswith('END'):
            if section == 'bodies':
                section, cur = 'regions', None
                continue
            break
        if section == 'bodies':
            if l[0] != ' ':
                t = l.split()
                cur = [t[0], t[1], [float(x) for x in t[2:]], xform]
                bodies[cur[1]] = cur
            else:
                cur[2].extend(float(x) for x in l.split())
        else:
            if l[0] != ' ':
                t = l.split()
                cur = [[]]
                regions[t[0]] = cur
                toks = t[2:]
            else:
                toks = l.split()
            for tk in toks:
                if tk == '|':
                    cur.append([])
                else:
                    cur[-1].append(tk)
    return bodies, regions


def inside_body(b, P):
    if b[3] is not None:              # body defined in a rotated frame
        P = P @ b[3]                  # x_local = M^T x_global
    t, _, v = b[:3]
    v = np.asarray(v)
    if t == 'RPP':
        return ((P[:, 0] > v[0]) & (P[:, 0] < v[1]) & (P[:, 1] > v[2]) &
                (P[:, 1] < v[3]) & (P[:, 2] > v[4]) & (P[:, 2] < v[5]))
    if t == 'PLA':
        return (P - v[3:6]) @ v[0:3] < 0
    if t == 'BOX':
        d = P - v[0:3]
        m = np.ones(len(P), bool)
        for k in range(3):
            h = v[3 + 3 * k:6 + 3 * k]
            s = d @ h / (h @ h)
            m &= (s > 0) & (s < 1)
        return m
    if t in ('RCC', 'TRC'):
        V, Hh = v[0:3], v[3:6]
        d = P - V
        s = d @ Hh / (Hh @ Hh)
        r = v[6] if t == 'RCC' else v[6] + (v[7] - v[6]) * s
        perp = d - np.outer(s, Hh)
        return (s > 0) & (s < 1) & (np.einsum('ij,ij->i', perp, perp) < r * r)
    if t == 'REC':
        V, Hh, a, b2 = v[0:3], v[3:6], v[6:9], v[9:12]
        d = P - V
        s = d @ Hh / (Hh @ Hh)
        u = d @ a / (a @ a)
        w = d @ b2 / (b2 @ b2)
        return (s > 0) & (s < 1) & (u * u + w * w < 1)
    raise ValueError(t)


def body_box(b):
    """axis-aligned bounds of a finite body (None for half-spaces)"""
    if b[3] is not None:
        lb = body_box(b[:3] + [None])
        if lb is None:
            return None
        cs = np.array([[x, y, z] for x in (lb[0][0], lb[1][0])
                       for y in (lb[0][1], lb[1][1])
                       for z in (lb[0][2], lb[1][2])]) @ b[3].T
        return cs.min(axis=0), cs.max(axis=0)
    t, _, p = b[:3]
    p = np.asarray(p)
    if t == 'RPP':
        return p[0::2], p[1::2]
    if t == 'BOX':
        V = p[0:3]
        cs = [V + i * p[3:6] + j * p[6:9] + k * p[9:12]
              for i in (0, 1) for j in (0, 1) for k in (0, 1)]
        return np.min(cs, axis=0), np.max(cs, axis=0)
    if t in ('RCC', 'TRC', 'REC'):
        V, H = p[0:3], p[3:6]
        r = p[6] if t == 'RCC' else (max(p[6], p[7]) if t == 'TRC' else
                                     max(np.linalg.norm(p[6:9]),
                                         np.linalg.norm(p[9:12])))
        ends = np.array([V, V + H])
        return ends.min(axis=0) - r, ends.max(axis=0) + r
    return None


def fluka_classify(bodies, regions, P):
    """count of regions containing each point and the (last) region index;
    zones are only evaluated on points inside their bounding box"""
    boxes = {}
    names = list(regions)
    count = np.zeros(len(P), int)
    which = np.full(len(P), -1)
    order = np.argsort(P[:, 0])
    xs = P[order, 0]
    for ri, n in enumerate(names):
        hits = []
        for z in regions[n]:
            lo = np.full(3, -np.inf)
            hi = np.full(3, np.inf)
            for l in z:
                if l[0] != '+':
                    continue
                if l[1:] not in boxes:
                    boxes[l[1:]] = body_box(bodies[l[1:]])
                bb = boxes[l[1:]]
                if bb is not None:
                    lo, hi = np.maximum(lo, bb[0]), np.minimum(hi, bb[1])
            if not np.all(np.isfinite(lo)):
                idx = np.arange(len(P))
            else:
                i0, i1 = np.searchsorted(xs, [lo[0], hi[0]])
                idx = order[i0:i1]
                idx = idx[np.all((P[idx] >= lo) & (P[idx] <= hi), axis=1)]
            if not len(idx):
                continue
            Q = P[idx]
            m = np.ones(len(idx), bool)
            for l in z:
                ib = inside_body(bodies[l[1:]], Q[m])
                if l[0] == '-':
                    ib = ~ib
                sub = np.nonzero(m)[0]
                m[sub[~ib]] = False
                if not m.any():
                    break
            hits.append(idx[m])
        if hits:
            h = np.unique(np.concatenate(hits))
            count[h] += 1
            which[h] = ri
    return names, count, which


# ---------------------------------------------------------------- HDDS side

def local(pv, P):
    return (P - pv.frame.t) @ pv.frame.R


def in_phi(el, x, y):
    if el.get('profile') is None:
        return np.ones(len(x), bool)
    p0, dp = [v * H.uang(el) for v in H.floats(el.get('profile'), 2)]
    if dp >= 2 * math.pi - 1e-12:
        return np.ones(len(x), bool)
    phi = np.mod(np.arctan2(y, x) - p0, 2 * math.pi)
    return phi < dp


def planes_of(el):
    L = H.ulen(el)
    if el.tag == 'tubs':
        ri, ro, z = [v * L for v in H.floats(el.get('Rio_Z'), 3)]
        return [(-z / 2, ri, ro), (z / 2, ri, ro)]
    if el.tag == 'cons':
        a, b, c, d, z = [v * L for v in H.floats(el.get('Rio1_Rio2_Z'), 5)]
        return [(-z / 2, a, b), (z / 2, c, d)]
    out = []
    for pp in el.findall('polyplane'):
        ri, ro, z = [v * H.ulen(pp) for v in H.floats(pp.get('Rio_Z'), 3)]
        out.append((z, ri, ro))
    return out


def interp(planes, z):
    """rmin, rmax at z (nan outside); first matching segment wins"""
    rmin = np.full(len(z), np.nan)
    rmax = np.full(len(z), np.nan)
    for (za, ia, oa), (zb, ib, ob) in zip(planes[:-1], planes[1:]):
        if zb - za <= 1e-9:
            continue
        m = (z > za) & (z < zb) & np.isnan(rmin)
        f = (z[m] - za) / (zb - za)
        rmin[m] = ia + (ib - ia) * f
        rmax[m] = oa + (ob - oa) * f
    return rmin, rmax


def hdds_inside(pv, P):
    el = pv.el
    q = local(pv, P)
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    L, A = H.ulen(el), H.uang(el)
    t = el.tag
    if t == 'box':
        a, b, c = [v * L / 2 for v in H.floats(el.get('X_Y_Z'), 3)]
        return (abs(x) < a) & (abs(y) < b) & (abs(z) < c)
    if t in ('tubs', 'cons', 'pcon'):
        rmin, rmax = interp(planes_of(el), z)
        r = np.hypot(x, y)
        with np.errstate(invalid='ignore'):
            return (r > rmin) & (r < rmax) & in_phi(el, x, y)
    if t == 'pgon':
        p0, dp = [v * A for v in H.floats(el.get('profile'), 2)]
        n = int(el.get('segments'))
        rmin, rmax = interp(planes_of(el), z)
        phi = np.mod(np.arctan2(y, x) - p0, 2 * math.pi)
        k = np.floor(phi / (dp / n))
        ang = p0 + (k + 0.5) * dp / n
        d = x * np.cos(ang) + y * np.sin(ang)
        with np.errstate(invalid='ignore'):
            return (k < n) & (d > rmin) & (d < rmax)
    if t == 'trd':
        xm, xp, ym, yp, zl = [v * L for v in H.floats(el.get('Xmp_Ymp_Z'), 5)]
        axz, ayz = [v * A for v in H.floats(el.get('inclination', '0 0'), 2)]
        dz = zl / 2
        f = (z + dz) / zl
        hx = (xm + (xp - xm) * f) / 2
        hy = (ym + (yp - ym) * f) / 2
        return ((abs(z) < dz) & (abs(x - z * math.tan(axz)) < hx) &
                (abs(y - z * math.tan(ayz)) < hy))
    if t == 'eltu':
        rx, ry, zl = [v * L for v in H.floats(el.get('Rxy_Z'), 3)]
        return ((x / rx) ** 2 + (y / ry) ** 2 < 1) & (abs(z) < zl / 2)
    raise ValueError(t)


def hdds_classify(pvs, P, lohi):
    """HDDS volume owning each point: descend from the top volumes; among
    siblings containing a point the lowest geometry layer wins (HDDS 1.1),
    and a point outside every daughter belongs to the mother.
    Returns index array (-1 = none) and a count of same-layer overlaps."""
    best = np.full(len(P), -1)
    ambiguous = np.zeros(len(P), int)

    def inside(pv, idx):
        lo, hi = lohi[pv.id]
        idx = idx[np.all((P[idx] > lo) & (P[idx] < hi), axis=1)]
        return idx[hdds_inside(pv, P[idx])] if len(idx) else idx

    def descend(level):
        # level: list of (pv list of siblings, point indices inside mother)
        stack = level
        while stack:
            sibs, idx = stack.pop()
            claimed = np.zeros(len(P), bool)
            for L in sorted({s.layer for s in sibs}):
                taken = np.zeros(len(P), bool)
                for s in (x for x in sibs if x.layer == L):
                    m = inside(s, idx)
                    m = m[~claimed[m]]
                    ambiguous[m[taken[m]]] += 1
                    taken[m] = True
                    best[m] = s.id
                    if s.daughters:
                        stack.append((s.daughters, m))
                claimed |= taken

    tops = [p for p in pvs if p.mother is None or not p.mother.inroot]
    descend([(tops, np.arange(len(P)))])
    return best, ambiguous


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('mainfile')
    ap.add_argument('stem')
    ap.add_argument('--root')
    ap.add_argument('--top', default='everything')
    ap.add_argument('--per-volume', type=int, default=40)
    ap.add_argument('--uniform', type=int, default=20000)
    ap.add_argument('--max-volumes', type=int, default=0,
                    help='sample around at most this many volumes')
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    t0 = time.time()

    root_el, table = H.load_hdds(a.mainfile)
    fl = H.Flattener(table, a.root)
    pvs = [p for p in fl.run(a.top) if p.inroot]
    bt = H.BodyTable()
    lohi = {}
    for p in pvs:
        s = H.make_solid(bt, p)          # used only for bounding boxes
        lohi[p.id] = H.aabb(s.hprox)
        p.shape = s
    reg = {}
    with open(a.stem + '_regions.csv') as f:
        for row in csv.DictReader(f):
            reg[row['region']] = row
    regions_of_path = {}
    for k, r in reg.items():
        if r['hdds_volume']:
            regions_of_path.setdefault(r['hdds_path'], set()).add(k)
    outside = {k for k, r in reg.items() if not r['hdds_volume']}
    if not outside:
        sys.exit("no outside/container region in the map")

    # sample points: around each volume, plus uniform in the bounding box
    vols = pvs
    if a.max_volumes and len(vols) > a.max_volumes:
        idx = rng.choice(len(vols), a.max_volumes, replace=False)
        vols = [vols[i] for i in sorted(idx)]
    pts = []
    for p in vols:
        o = p.shape.hprox[0]
        u = rng.uniform(-1.1, 1.1, (a.per_volume, 3)) * o.h
        pts.append(o.c + u @ o.R.T)
    lo = np.min([v[0] for v in lohi.values()], axis=0)
    hi = np.max([v[1] for v in lohi.values()], axis=0)
    pts.append(rng.uniform(lo - 2, hi + 2, (a.uniform, 3)))
    P = np.vstack(pts)
    print("%d volumes, %d sample points" % (len(pvs), len(P)))

    bodies, regions = read_fluka(a.stem + '.inp')
    names, count, which = fluka_classify(bodies, regions, P)
    print("FLUKA evaluation done (%.0f s)" % (time.time() - t0))
    best, amb = hdds_classify(pvs, P, lohi)
    print("HDDS classification done (%.0f s)" % (time.time() - t0))

    byid = {p.id: p for p in pvs}
    blk = 'BLKHOLE'
    expect = [outside if b < 0 else regions_of_path[byid[b].path]
              for b in best]
    got = [names[w] if w >= 0 else None for w in which]
    nzero = int(np.sum(count == 0))
    nmulti = int(np.sum(count > 1))
    ok = np.array([g in e or (g == blk and e is outside)
                   for g, e in zip(got, expect)])
    # points outside the container are BLKHOLE in the standalone input
    bad = np.nonzero(~ok & (count == 1))[0]
    namb = int(np.sum(amb > 0))
    print("points in no region: %d, in more than one region: %d" %
          (nzero, nmulti))
    print("points whose region differs from the HDDS volume: %d" % len(bad))
    print("points where HDDS itself has overlapping siblings: %d" % namb)
    for i in bad[:15]:
        print("  ", P[i], "fluka:", got[i], "hdds:", sorted(expect[i])[:3],
              byid[best[i]].path if best[i] >= 0 else '-')
    for i in np.nonzero(count != 1)[0][:10]:
        print("  count", count[i], P[i], "hdds:", sorted(expect[i])[:3])
    status = (nzero == 0 and nmulti == 0 and len(bad) == 0)
    print("PASS" if status else "FAIL")
    return 0 if status else 1


if __name__ == '__main__':
    sys.exit(main())
