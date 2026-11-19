#!/usr/bin/env python3
"""Assembly tree of a STEP AP214 file: for every MANIFOLD_SOLID_BREP placed in
the assembly, the product path and the transformed vertex cloud; then match
each to a gmsh solid of vols.json (by containment of the vertices in its
bounding box).  Output: solids_named.json  {gmsh tag: {path, product, ...}}"""
import json
import re
import sys
import numpy as np

F = sys.argv[1]
UNIT = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
INV = len(sys.argv) > 4
ent = {}
cur = []
rx = re.compile(r'^#(\d+)\s*=\s*(.*)$', re.S)
with open(F, encoding='latin-1') as f:
    data = f.read()
body = data[data.index('DATA;') + 5:data.rindex('ENDSEC;')]
for stmt in body.split(';'):
    s = stmt.strip()
    if not s.startswith('#'):
        continue
    m = rx.match(s)
    if m:
        ent[int(m.group(1))] = m.group(2).replace('\n', '').replace('\r', '')
print(len(ent), "entities", file=sys.stderr)


def typ(i):
    s = ent[i]
    return s[:s.index('(')].strip() if not s.startswith('(') else 'COMPLEX'


def refs(s):
    return [int(x) for x in re.findall(r'#(\d+)', s)]


def args(i):
    s = ent[i]
    return s[s.index('(') + 1:s.rindex(')')]


def strs(s):
    return re.findall(r"'((?:[^']|'')*)'", s)


# products
pd_name = {}
for i, s in ent.items():
    if s.startswith('PRODUCT_DEFINITION('):
        r = refs(s)
        pdf = r[0]
        prod = refs(ent[pdf])[0]
        pd_name[i] = strs(ent[prod])[0]
# pd -> shape representation
pds_pd = {}
for i, s in ent.items():
    if s.startswith('PRODUCT_DEFINITION_SHAPE('):
        r = refs(s)
        if r and r[-1] in ent and ent[r[-1]].startswith(('PRODUCT_DEFINITION(', 'NEXT_ASSEMBLY')):
            pds_pd[i] = r[-1]
pd_sr = {}
for i, s in ent.items():
    if s.startswith('SHAPE_DEFINITION_REPRESENTATION('):
        pds, rep = refs(s)[:2]
        if pds in pds_pd and pds_pd[pds] in pd_name:
            pd_sr[pds_pd[pds]] = rep
# SR -> ABSR (no transform) and RRWT (child -> parent with transform)
sr_children = {}      # parent rep -> list of (child rep, transform id or None)
for i, s in ent.items():
    if s.startswith('SHAPE_REPRESENTATION_RELATIONSHIP('):
        r = refs(s)
        a, b = r[0], r[1]
        sr_children.setdefault(a, []).append((b, None))
        sr_children.setdefault(b, []).append((a, None))
    elif s.startswith('(') and 'REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION' in s:
        r = refs(s)
        rep1, rep2, tr = r[0], r[1], r[2]
        sr_children.setdefault(rep2, []).append((rep1, tr))
# NAUO: parent pd -> child pd ; CDSR links RRWT to NAUO
nauo = {}
for i, s in ent.items():
    if s.startswith('NEXT_ASSEMBLY_USAGE_OCCURRENCE('):
        r = refs(s)
        nauo[i] = (r[0], r[1], strs(s)[0])


def axis(i):
    """AXIS2_PLACEMENT_3D -> 4x4"""
    r = refs(ent[i])
    o = pt(r[0])
    z = np.array([0, 0, 1.0]); x = np.array([1.0, 0, 0])
    if len(r) > 1:
        z = dirn(r[1])
    if len(r) > 2:
        x = dirn(r[2])
    x = x - z * (x @ z); x /= np.linalg.norm(x)
    y = np.cross(z, x)
    M = np.eye(4); M[:3, 0] = x; M[:3, 1] = y; M[:3, 2] = z; M[:3, 3] = o
    return M


def pt(i):
    return np.array([float(v) for v in re.findall(r'[-+0-9.Ee]+', args(i).split(',', 1)[1])][:3])


def dirn(i):
    v = np.array([float(x) for x in re.findall(r'[-+0-9.Ee]+', args(i).split(',', 1)[1])][:3])
    return v / np.linalg.norm(v)


def idt(i):
    r = refs(ent[i])
    return r[0], r[1]


# vertices of a solid
def solid_vertices(i):
    seen, stack, out = set(), [i], []
    while stack:
        j = stack.pop()
        if j in seen:
            continue
        seen.add(j)
        s = ent[j]
        t = s[:s.index('(')] if not s.startswith('(') else ''
        if t == 'CARTESIAN_POINT':
            continue
        if t == 'VERTEX_POINT':
            out.append(pt(refs(s)[0])); continue
        if t in ('MANIFOLD_SOLID_BREP', 'BREP_WITH_VOIDS', 'CLOSED_SHELL', 'ORIENTED_CLOSED_SHELL',
                 'ADVANCED_FACE', 'FACE_OUTER_BOUND', 'FACE_BOUND', 'EDGE_LOOP',
                 'ORIENTED_EDGE', 'EDGE_CURVE', 'VERTEX_LOOP'):
            rr = refs(s)
            if t == 'ADVANCED_FACE':
                rr = rr[:-1]            # skip the surface
            if t == 'EDGE_CURVE':
                rr = rr[:2]             # the two vertices
            stack += rr
    return np.array(out)


SOLID_T = ('MANIFOLD_SOLID_BREP(', 'BREP_WITH_VOIDS(')


def solid_faces(i, M):
    """analytic surfaces of a solid, transformed to the global frame (mm)"""
    out, seen, stack = [], set(), [i]
    R = M[:3, :3]
    while stack:
        j = stack.pop()
        if j in seen:
            continue
        seen.add(j)
        s = ent[j]
        if s.startswith(('MANIFOLD_SOLID_BREP(', 'BREP_WITH_VOIDS(', 'CLOSED_SHELL(', 'ORIENTED_CLOSED_SHELL(')):
            stack += refs(s)
        elif s.startswith('ADVANCED_FACE('):
            surf = refs(s)[-1]
            ss = ent[surf]
            t = ss[:ss.index('(')]
            r = refs(ss)
            nums = [float(x) for x in re.findall(r',\s*([-+0-9.Ee]+)', ss.split(')')[0] + ')')]
            try:
                A = axis(r[0])
            except Exception:
                out.append(dict(t=t)); continue
            G = M @ A
            o = (G[:3, 3]) * UNIT; d = G[:3, 2]; xd = G[:3, 0]
            out.append(dict(t=t, o=list(o), d=list(d), x=list(xd), p=[v * UNIT if t != 'CONICAL_SURFACE' or k == 0 else v for k, v in enumerate(nums)]))
    return out
placed = []          # (product path, solid id, 4x4)


def walk_rep(rep, M, path, depth=0):
    s = ent[rep]
    for it in refs(s[s.index('(') + 1:])[:-1] if not s.startswith('(') else []:
        if ent[it].startswith(SOLID_T):
            placed.append((path, it, M))
        elif ent[it].startswith('MAPPED_ITEM('):
            rm, tgt = refs(ent[it])[:2]
            origin, mrep = refs(ent[rm])[:2]
            walk_rep(mrep, M @ axis(tgt) @ np.linalg.inv(axis(origin)), path, depth + 1)
    for child, tr in sr_children.get(rep, []):
        if tr is None:
            if child not in visited_plain:
                visited_plain.add(child)
                walk_rep(child, M, path, depth + 1)


visited_plain = set()
# build the product tree from NAUOs
children = {}
for k, (par, chi, nm) in nauo.items():
    children.setdefault(par, []).append((chi, k, nm))
roots = [p for p in pd_name if all(p != c for v in children.values() for c, _, _ in v)]
# transform of a NAUO: find RRWT whose CDSR points to the NAUO's PDS
nauo_pds = {pds: n for pds, n in pds_pd.items() if n in nauo}
nauo_tr = {}
for i, s in ent.items():
    if s.startswith('CONTEXT_DEPENDENT_SHAPE_REPRESENTATION('):
        rr, pds = refs(s)[:2]
        if pds in nauo_pds:
            r = refs(ent[rr])
            nauo_tr[nauo_pds[pds]] = r[2]


def walk_pd(pd, M, path):
    rep = pd_sr.get(pd)
    if rep is not None:
        visited_plain.clear()
        walk_rep(rep, M, path)
    for chi, k, nm in children.get(pd, []):
        tr = nauo_tr.get(k)
        T = np.eye(4)
        if tr is not None:
            a, b = idt(tr)
            T = axis(b) @ np.linalg.inv(axis(a)) if not INV else axis(a) @ np.linalg.inv(axis(b))
        walk_pd(chi, M @ T, path + [nm])


for r in roots:
    walk_pd(r, np.eye(4), [pd_name[r]])
print(len(placed), "placed solids", file=sys.stderr)

V = json.load(open(sys.argv[2]))
B = np.array([e['bb'] for e in V])
res = {}
used = {}
for path, sid, M in placed:
    P = solid_vertices(sid)
    if not len(P):
        continue
    Q = ((M[:3, :3] @ P.T).T + M[:3, 3]) * UNIT
    lo, hi = Q.min(0), Q.max(0)
    inside = np.all((B[:, :3] <= lo + 0.05) & (B[:, 3:] >= hi - 0.05), axis=1)
    cand = np.nonzero(inside)[0]
    if not len(cand):
        res.setdefault('_unmatched', []).append(dict(path=path, lo=list(lo), hi=list(hi)))
        continue
    vol = np.prod(B[cand, 3:] - B[cand, :3], axis=1)
    k = cand[np.argmin(vol)]
    tag = V[k]['tag']
    used[tag] = used.get(tag, 0) + 1
    res[str(tag)] = dict(path=path, product=path[-1], gmsh_name=V[k]['name'],
                         lo=list(lo), hi=list(hi), sid=sid, M=M.tolist(),
                         faces=solid_faces(sid, M))
dup = {t: n for t, n in used.items() if n > 1}
print("matched %d gmsh solids, %d matched more than once, %d unmatched"
      % (len(used), len(dup), len(res.get('_unmatched', []))), file=sys.stderr)
json.dump(res, open('solids_named.json', 'w'), indent=0)
