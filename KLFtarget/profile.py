"""r-z section polygons (from sections_dense.json) -> HDDS pcon polyplanes."""
import json, math
import numpy as np

def chain(edges, tol=1e-3):
    segs = [e['rz'] for e in edges]
    poly = list(segs.pop(0))
    while segs:
        end = poly[-1]
        for i, s in enumerate(segs):
            if math.dist(s[0], end) < tol:
                poly += s[1:]; segs.pop(i); break
            if math.dist(s[-1], end) < tol:
                poly += s[::-1][1:]; segs.pop(i); break
        else:
            raise ValueError("open loop at %s" % (end,))
    if math.dist(poly[0], poly[-1]) < tol:
        poly.pop()
    return np.array(poly)

def revolved_volume(P):
    r, z = P[:, 0], P[:, 1]
    r2, z2 = np.roll(r, -1), np.roll(z, -1)
    # Pappus: V = 2 pi * integral r dA ; Green: integral r dA = -1/2 oint r^2 dz ... use exact polygon formula
    a = r * z2 - r2 * z
    A = a.sum() / 2
    rc = ((r + r2) * a).sum() / (6 * A)
    return abs(2 * math.pi * A * rc)

def intervals_at(P, z):
    """r intervals of the polygon on the line z (z must not be a vertex z)"""
    rs = []
    n = len(P)
    for i in range(n):
        (r1, z1), (r2, z2) = P[i], P[(i + 1) % n]
        if (z1 - z) * (z2 - z) < 0:
            rs.append(r1 + (z - z1) * (r2 - r1) / (z2 - z1))
    rs.sort()
    return [(rs[k], rs[k + 1]) for k in range(0, len(rs), 2)]

def to_pcon(Ps, zmerge=2e-3, rsnap=2e-3, fill=True, log=None):
    """polyplanes (z, rmin, rmax) for one or more polygons (union).
    Where a z line crosses several separate r intervals (grooves, undercuts,
    two loops) the gaps are filled when fill=True (logged)."""
    if isinstance(Ps, np.ndarray): Ps = [Ps]
    Ps = [P.copy() for P in Ps]
    zs = sorted(set(np.round(np.concatenate([P[:, 1] for P in Ps]), 5)))
    # merge near-duplicate z levels
    zl = [zs[0]]
    for z in zs[1:]:
        if z - zl[-1] > zmerge: zl.append(z)
    zl = np.array(zl)
    for P in Ps:                       # snap vertex z to the merged levels
        for k in range(len(P)):
            j = np.abs(zl - P[k, 1]).argmin()
            if abs(zl[j] - P[k, 1]) <= zmerge: P[k, 1] = zl[j]
    zl = list(zl)
    planes = []
    for za, zb in zip(zl[:-1], zl[1:]):
        eps = 1e-6 * max(1.0, zb - za)
        def iv(z):
            I = sorted(i for P in Ps for i in intervals_at(P, z))
            if not I:
                raise ValueError("no material at z=%.4f" % z)
            if len(I) != 1:
                gap = sum(max(0, b[0] - a[1]) for a, b in zip(I[:-1], I[1:]))
                if not fill:
                    raise ValueError("%d intervals at z=%.4f" % (len(I), z))
                if log is not None: log.append((round(z, 3), len(I), round(gap, 3)))
            return (I[0][0], max(i[1] for i in I))
        # interpolate edges to slab ends: evaluate just inside and extrapolate
        d = (zb - za) * 1e-4
        (a0, b0), (a1, b1) = iv(za + d), iv(zb - d)
        ra = (a0 - (a1 - a0) * d / (zb - za - 2 * d), b0 - (b1 - b0) * d / (zb - za - 2 * d))
        rb = (a1 + (a1 - a0) * d / (zb - za - 2 * d), b1 + (b1 - b0) * d / (zb - za - 2 * d))
        planes.append((za, max(ra[0], 0.0), ra[1]))
        planes.append((zb, max(rb[0], 0.0), rb[1]))
    for k, (z, a, b) in enumerate(planes):
        planes[k] = (z, 0.0 if a < rsnap else a, b)
    # drop redundant planes: identical consecutive and collinear interior
    out = [planes[0]]
    for p in planes[1:]:
        if abs(p[0] - out[-1][0]) < 1e-9 and abs(p[1] - out[-1][1]) < 1e-5 and abs(p[2] - out[-1][2]) < 1e-5:
            continue
        out.append(p)
    changed = True
    while changed:
        changed = False
        for k in range(1, len(out) - 1):
            p0, p1, p2 = out[k - 1], out[k], out[k + 1]
            if p2[0] - p0[0] < 1e-9 or abs(p1[0]-p0[0])<1e-9 or abs(p2[0]-p1[0])<1e-9:
                continue
            t = (p1[0] - p0[0]) / (p2[0] - p0[0])
            if all(abs(p0[j] + t * (p2[j] - p0[j]) - p1[j]) < 1e-4 for j in (1, 2)):
                out.pop(k); changed = True; break
    return out

def pcon_volume(planes):
    V = 0.0
    for (z1, a1, b1), (z2, a2, b2) in zip(planes[:-1], planes[1:]):
        h = z2 - z1
        V += math.pi * h / 3 * ((b1*b1 + b1*b2 + b2*b2) - (a1*a1 + a1*a2 + a2*a2))
    return V
