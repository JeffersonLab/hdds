#!/usr/bin/env python3
"""For each selected CAD solid, find the HDDS primitive that encloses it most
tightly: a pcon about the solid's own symmetry axis (profile from sections
in four half-planes through the axis, holes filled) or a box (along the
solid's plane directions, else its principal axes).  Output prims.json with
frame, parameters and fill factor f = V_CAD / V_primitive (in mm, CAD frame).
usage: analyze_solids.py TAGLIST.json OUT.json"""
import json
import math
import sys
import time

import gmsh
import numpy as np

sys.path.insert(0, '/home/claude/klf-geometry/lh2tgt-hdds')
from profile import chain, to_pcon, pcon_volume   # noqa: E402

tags = json.load(open(sys.argv[1]))
S = json.load(open('solids_named.json'))
V = {e['tag']: e for e in json.load(open('vols.json'))}
gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.model.occ.importShapes('tgt.brep')
gmsh.model.occ.synchronize()


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def frame_from_axis(o, d):
    d = unit(d)
    t = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1.0, 0])
    x = unit(t - d * (t @ d))
    y = np.cross(d, x)
    return np.array(o, float), np.c_[x, y, d]


def surface_points(t, n=7):
    P = []
    for _, f in gmsh.model.getBoundary([(3, t)], oriented=False):
        f = abs(f)
        lo, hi = gmsh.model.getParametrizationBounds(2, f)
        uv = [c for a in np.linspace(lo[0], hi[0], n) for b in np.linspace(lo[1], hi[1], n)
              for c in (a, b)]
        P.append(np.array(gmsh.model.getValue(2, f, uv)).reshape(-1, 3))
        # curves of the face (exact outline)
        for _, c in gmsh.model.getBoundary([(2, f)], oriented=False):
            c = abs(c)
            l0, l1 = gmsh.model.getParametrizationBounds(1, c)
            P.append(np.array(gmsh.model.getValue(1, c, list(np.linspace(l0[0], l1[0], 9)))).reshape(-1, 3))
    return np.vstack(P)


def box_fit(P, R):
    Q = P @ R
    lo, hi = Q.min(0), Q.max(0)
    c = R @ ((lo + hi) / 2)
    return c, (hi - lo), float(np.prod(hi - lo))


def axis_clusters(faces):
    ax = [f for f in faces if f.get('t') in ('CYLINDRICAL_SURFACE', 'CONICAL_SURFACE',
                                              'TOROIDAL_SURFACE') and 'd' in f]
    cl = []
    for f in ax:
        o, d = np.array(f['o']), unit(f['d'])
        for c in cl:
            if abs(abs(c['d'] @ d) - 1) < 1e-6:
                w = o - c['o']
                if np.linalg.norm(w - c['d'] * (w @ c['d'])) < 0.05:
                    c['n'] += 1
                    c['r'] = max(c['r'], f['p'][0] if f['p'] else 0)
                    break
        else:
            cl.append(dict(o=o, d=d, n=1, r=(f['p'][0] if f['p'] else 0)))
    cl.sort(key=lambda c: (-c['n'] * max(c['r'], 1), ))
    return cl


def rev_profile(t, o, R, L, rmax):
    """union of the sections in 4 half-planes through the axis -> polygons (r, s)"""
    polys = []
    pending = []
    for k in range(4):
        phi = k * math.pi / 2
        rect = gmsh.model.occ.addRectangle(0, -L, 0, rmax, 2 * L)    # x = r, y = s
        # local (r, s, 0) -> global o + r*(cos phi x + sin phi y) + s*d
        e1 = R[:, 0] * math.cos(phi) + R[:, 1] * math.sin(phi)
        A = np.c_[e1, R[:, 2], np.cross(e1, R[:, 2]), o]
        gmsh.model.occ.affineTransform([(2, rect)], list(A.ravel()))
        try:
            r, _ = gmsh.model.occ.intersect([(3, t)], [(2, rect)], removeObject=False, removeTool=True)
            pending.append((e1, [f for d, f in r if d == 2]))
        except Exception:
            pass
    gmsh.model.occ.synchronize()
    for e1, fs in pending:
        for f in fs:
            edges = []
            for _, c in gmsh.model.getBoundary([(2, f)], oriented=False):
                c = abs(c)
                typ = gmsh.model.getType(1, c)
                l0, l1 = gmsh.model.getParametrizationBounds(1, c)
                n = 2 if typ == 'Line' else 17
                P = np.array(gmsh.model.getValue(1, c, list(np.linspace(l0[0], l1[0], n)))).reshape(-1, 3)
                rr = (P - o) @ e1
                ss = (P - o) @ R[:, 2]
                edges.append(dict(rz=[[max(a, 0.0), b] for a, b in zip(rr, ss)]))
            try:
                polys.append(chain(edges, tol=2e-3))
            except Exception:
                pass
        gmsh.model.occ.remove([(2, f) for f in fs], recursive=True)
    gmsh.model.occ.synchronize()
    return polys


out = {}
t0 = time.time()
for i, t in enumerate(tags):
    e = V[t]
    vol = e['vol']
    faces = S.get(str(t), {}).get('faces', [])
    P = surface_points(t)
    best = None
    # box candidates: plane directions, then principal axes
    pn = [unit(f['d']) for f in faces if f.get('t') == 'PLANE' and 'd' in f]
    dirs = []
    for n in pn:
        if not any(abs(abs(n @ d) - 1) < 1e-4 for d in dirs):
            dirs.append(n)
    cands = []
    if len(dirs) >= 2:
        for a in range(len(dirs)):
            for b in range(a + 1, len(dirs)):
                if abs(dirs[a] @ dirs[b]) < 1e-4:
                    x, y = dirs[a], dirs[b]
                    cands.append(np.c_[x, y, np.cross(x, y)])
    c0 = np.array(gmsh.model.occ.getCenterOfMass(3, t))
    I = np.array(gmsh.model.occ.getMatrixOfInertia(3, t)).reshape(3, 3)
    w, U = np.linalg.eigh(I)
    if np.linalg.det(U) < 0:
        U[:, 2] *= -1
    cands.append(U)
    for R in cands:
        c, dims, vb = box_fit(P, R)
        if best is None or vb < best['vmodel']:
            best = dict(type='box', c=c.tolist(), R=R.tolist(), dims=dims.tolist(), vmodel=vb)
    # revolution candidate
    cl = axis_clusters(faces)
    if cl:
        a = cl[0]
        o, R = frame_from_axis(a['o'], a['d'])
        Q = (P - o) @ R
        rmax = float(np.hypot(Q[:, 0], Q[:, 1]).max()) * 1.05 + 1
        L = float(np.abs(Q[:, 2]).max()) * 1.05 + 1
        try:
            polys = rev_profile(t, o, R, L, rmax)
            if polys:
                # group polygons whose s ranges overlap: one pcon per group
                rng = sorted([(float(p[:, 1].min()), float(p[:, 1].max()), p) for p in polys], key=lambda q: q[0])
                groups = []
                for a0, a1, p in rng:
                    if groups and a0 <= groups[-1][1] + 1e-3:
                        groups[-1][1] = max(groups[-1][1], a1); groups[-1][2].append(p)
                    else:
                        groups.append([a0, a1, [p]])
                pls = [to_pcon(g[2]) for g in groups]
                vr = sum(pcon_volume(pl) for pl in pls)
                if vr >= 0.95 * vol and vr < best['vmodel']:
                    best = dict(type='pcon', o=o.tolist(), R=R.tolist(), planes=pls, vmodel=vr)
        except Exception as ex:
            best.setdefault('note', str(ex)[:80])
    best['vcad'] = vol
    best['f'] = min(1.0, vol / best['vmodel']) if best['vmodel'] > 0 else 1.0
    out[str(t)] = best
    if i % 20 == 0:
        print(i, len(tags), "%.0fs" % (time.time() - t0), flush=True)
        json.dump(out, open(sys.argv[2], 'w'))
json.dump(out, open(sys.argv[2], 'w'))
print("done", len(out), "%.0fs" % (time.time() - t0))
