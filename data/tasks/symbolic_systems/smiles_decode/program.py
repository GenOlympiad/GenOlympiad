# code: helpers
from genolympiad.task_helpers import join_box_reads, list_items_per_box
# end of helpers

# code: skeleton_graph_code

def _pil(image):
    from PIL import Image
    return image.convert("RGB") if hasattr(image, "convert") else Image.open(str(image)).convert("RGB")


def _ink(image, cap):
    import numpy as np
    import cv2
    a = np.asarray(_pil(image))
    bgr = cv2.cvtColor(a, cv2.COLOR_RGB2BGR)
    H, W = bgr.shape[:2]
    if max(H, W) > cap:
        s = float(cap) / max(H, W)
        bgr = cv2.resize(bgr, (int(round(W * s)), int(round(H * s))), interpolation=cv2.INTER_AREA)
        H, W = bgr.shape[:2]
    g = cv2.GaussianBlur(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), (3, 3), 0)
    _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    m = (th > 0).astype(np.uint8)
    if float(m.mean()) > 0.5:
        m = 1 - m
    return m, H, W


def _drop_border(m, H, W, band=0.07, frac=0.42):
    import numpy as np
    import cv2
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    by, bx = max(2, int(band * H)), max(2, int(band * W))
    edge = np.zeros((H, W), np.uint8)
    edge[:by] = 1
    edge[H - by:] = 1
    edge[:, :bx] = 1
    edge[:, W - bx:] = 1
    out = m.copy()
    for i in range(1, n):
        sel = (lab == i)
        a = int(sel.sum())
        if a < 10 or float((sel & (edge > 0)).sum()) / a > frac:
            out[sel] = 0
    return out


def _thin(m):
    import cv2
    try:
        return (cv2.ximgproc.thinning(m * 255, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN) > 0).astype(m.dtype)
    except Exception:
        from skimage.morphology import skeletonize
        import numpy as np
        return skeletonize(m > 0).astype(np.uint8)


_RING = [(-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)]
_NB8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _cn_nb(sk):
    import numpy as np
    p = np.pad(sk, 1).astype(np.int32)
    h, w = sk.shape
    vals = [p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dy, dx in _RING]
    nb = sum(vals)
    cn = np.zeros_like(nb)
    for i in range(8):
        cn += np.abs(vals[(i + 1) % 8] - vals[i])
    return (cn // 2) * sk, nb * sk


def _paths(sk):
    import numpy as np
    import cv2
    H, W = sk.shape
    cn, nb = _cn_nb(sk)
    nodepx = ((cn >= 3) | (nb == 1)) & (sk > 0)
    nn, lab = cv2.connectedComponents(nodepx.astype(np.uint8), 8)
    nid = -np.ones(sk.shape, np.int32)
    nid[nodepx] = lab[nodepx] - 1
    out, seen = [], set()
    ny, nx = np.nonzero(nodepx)
    for y0, x0 in zip(ny, nx):
        for dy, dx in _NB8:
            y, x = int(y0) + dy, int(x0) + dx
            if not (0 <= y < H and 0 <= x < W) or not sk[y, x] or nid[y, x] >= 0 or (y, x) in seen:
                continue
            py, px, cy, cx = int(y0), int(x0), y, x
            pts = [(float(x0), float(y0))]
            while True:
                seen.add((cy, cx))
                pts.append((float(cx), float(cy)))
                cand = []
                for dy2, dx2 in _NB8:
                    yy, xx = cy + dy2, cx + dx2
                    if not (0 <= yy < H and 0 <= xx < W) or not sk[yy, xx] or (yy, xx) == (py, px):
                        continue
                    cand.append((yy, xx))
                tg = [q for q in cand if nid[q[0], q[1]] >= 0]
                if tg:
                    pts.append((float(tg[0][1]), float(tg[0][0])))
                    break
                cand = [q for q in cand if q not in seen]
                if not cand:
                    break
                py, px = cy, cx
                cy, cx = cand[0]
            if len(pts) >= 2:
                out.append(pts)
    rest = ((sk > 0) & (~nodepx)).astype(np.uint8)
    for (y, x) in seen:
        rest[y, x] = 0
    nl, ll = cv2.connectedComponents(rest, 8)
    for i in range(1, nl):
        ys, xs = np.nonzero(ll == i)
        if len(ys) < 16:
            continue
        used, cur, chain = set(), (int(ys[0]), int(xs[0])), []
        for _ in range(len(ys) + 2):
            chain.append((float(cur[1]), float(cur[0])))
            used.add(cur)
            nxt = None
            for dy, dx in _NB8:
                q = (cur[0] + dy, cur[1] + dx)
                if 0 <= q[0] < H and 0 <= q[1] < W and rest[q[0], q[1]] and q not in used:
                    nxt = q
                    break
            if nxt is None:
                break
            cur = nxt
        if len(chain) >= 16:
            chain.append(chain[0])
            out.append(chain)
    return out


def _rdp(pts, eps):
    import numpy as np
    import cv2
    P = np.asarray(pts, dtype=np.float32).reshape(-1, 1, 2)
    ap = cv2.approxPolyDP(P, eps, False)
    return [(float(p[0][0]), float(p[0][1])) for p in ap]


class _UF(object):
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, a):
        while self.p[a] != a:
            self.p[a] = self.p[self.p[a]]
            a = self.p[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra

    def groups(self):
        g = {}
        for i in range(len(self.p)):
            g.setdefault(self.find(i), []).append(i)
        return list(g.values())


def _cluster(pts, rad):
    import numpy as np
    n = len(pts)
    uf = _UF(n)
    P = np.asarray(pts, dtype=np.float64)
    for i in range(n - 1):
        d = np.hypot(P[i + 1:, 0] - P[i, 0], P[i + 1:, 1] - P[i, 1])
        for j in np.nonzero(d < rad)[0]:
            uf.union(i, i + 1 + int(j))
    cent, lab = [], {}
    for k, ids in enumerate(uf.groups()):
        cent.append((float(P[ids, 0].mean()), float(P[ids, 1].mean())))
        for i in ids:
            lab[i] = k
    return cent, lab


def _comps(nv, edges):
    adj = {i: set() for i in range(nv)}
    for a, b in edges:
        adj[a].add(b)
        adj[b].add(a)
    seen, comps = set(), []
    for s in range(nv):
        if s in seen:
            continue
        st, cur = [s], []
        seen.add(s)
        while st:
            u = st.pop()
            cur.append(u)
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    st.append(v)
        comps.append(sorted(cur))
    return comps, adj


def _cycles(nv, edges, adj):
    comps, _ = _comps(nv, edges)
    used = [i for i in range(nv) if adj[i]]
    ncomp = len([c for c in comps if len(c) > 1])
    cyc = len(edges) - len(used) + ncomp
    found = set()

    def walk(start, u, path):
        if len(path) > 12:
            return
        for v in adj[u]:
            if v == start and len(path) >= 3:
                found.add(tuple(sorted(path)))
            elif v not in path and v > start:
                walk(start, v, path + [v])
    for s in range(nv):
        if adj[s]:
            walk(s, s, [s])
    return cyc, max((len(c) for c in found), default=0), found


def _elen(vc, e):
    import math
    return math.hypot(vc[e[0]][0] - vc[e[1]][0], vc[e[0]][1] - vc[e[1]][1])


def _reindex(vc, E):
    used = sorted({x for e in E for x in e})
    ren = {v: k for k, v in enumerate(used)}
    return [vc[v] for v in used], sorted({(min(ren[a], ren[b]), max(ren[a], ren[b])) for a, b in E})


def _line_meet(p1, p2, q1, q2):
    d1 = (p2[0] - p1[0], p2[1] - p1[1])
    d2 = (q2[0] - q1[0], q2[1] - q1[1])
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-9:
        return None
    t = ((q1[0] - p1[0]) * d2[1] - (q1[1] - p1[1]) * d2[0]) / den
    return (p1[0] + t * d1[0], p1[1] + t * d1[1])


def _merge2(vc, E, a, b, at=None):
    if at is None:
        at = ((vc[a][0] + vc[b][0]) / 2.0, (vc[a][1] + vc[b][1]) / 2.0)
    vc = list(vc) + [at]
    nid = len(vc) - 1
    NE = set()
    for (x, y) in E:
        x2 = nid if x in (a, b) else x
        y2 = nid if y in (a, b) else y
        if x2 != y2:
            NE.add((min(x2, y2), max(x2, y2)))
    return vc, NE


def _clean(vc, E, med, spur, merge, bridge, collin=153.0):
    import math
    vc = [tuple(p) for p in vc]
    E = set(E)
    for _ in range(600):
        adj = {}
        for a, b in E:
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)
        kill = {(a, b) for (a, b) in E if _elen(vc, (a, b)) < spur * med
                and (len(adj.get(a, ())) == 1 or len(adj.get(b, ())) == 1)}
        if kill:
            E -= kill
            continue
        did = False
        for v, nb in list(adj.items()):
            if len(nb) != 2:
                continue
            p, q = list(nb)
            a1 = math.atan2(vc[p][1] - vc[v][1], vc[p][0] - vc[v][0])
            a2 = math.atan2(vc[q][1] - vc[v][1], vc[q][0] - vc[v][0])
            d = abs(math.degrees(a1 - a2)) % 360.0
            if min(d, 360.0 - d) >= collin:
                E.discard((min(v, p), max(v, p)))
                E.discard((min(v, q), max(v, q)))
                if p != q:
                    E.add((min(p, q), max(p, q)))
                did = True
                break
        if did:
            continue
        used = sorted({x for e in E for x in e})
        for i in range(len(used)):
            for j in range(i + 1, len(used)):
                a, b = used[i], used[j]
                if math.hypot(vc[a][0] - vc[b][0], vc[a][1] - vc[b][1]) < merge * med:
                    vc, E = _merge2(vc, E, a, b)
                    did = True
                    break
            if did:
                break
        if did:
            continue
        if bridge > 0:
            adj = {}
            for a, b in E:
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
            ends = [v for v in adj if len(adj[v]) == 1
                    and _elen(vc, (v, list(adj[v])[0])) > 0.62 * med]
            for i in range(len(ends)):
                for j in range(i + 1, len(ends)):
                    a, b = ends[i], ends[j]
                    if math.hypot(vc[a][0] - vc[b][0], vc[a][1] - vc[b][1]) >= bridge * med:
                        continue
                    na, nb2 = list(adj[a])[0], list(adj[b])[0]
                    at = _line_meet(vc[na], vc[a], vc[nb2], vc[b])
                    if at is None or (math.hypot(at[0] - vc[a][0], at[1] - vc[a][1]) > 0.9 * med
                                      or math.hypot(at[0] - vc[b][0], at[1] - vc[b][1]) > 0.9 * med):
                        at = None
                    vc, E = _merge2(vc, E, a, b, at)
                    did = True
                    break
                if did:
                    break
            if did:
                continue
        break
    return _reindex(vc, E)


def _bond_orders(mask, H, W, vc, E):
    import math
    import numpy as np
    out = []
    for (a, b) in E:
        pa, pb = vc[a], vc[b]
        L = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        if L < 8:
            out.append(1)
            continue
        ux, uy = (pb[0] - pa[0]) / L, (pb[1] - pa[1]) / L
        nx, ny = -uy, ux
        votes = []
        for f in (0.40, 0.50, 0.60):
            mx, my = pa[0] + ux * L * f, pa[1] + uy * L * f
            vals, t = [], -0.26 * L
            while t <= 0.26 * L:
                x, y = int(round(mx + nx * t)), int(round(my + ny * t))
                vals.append(1 if (0 <= x < W and 0 <= y < H and mask[y, x]) else 0)
                t += 0.5
            runs, prev = 0, 0
            for v in vals:
                if v and not prev:
                    runs += 1
                prev = v
            votes.append(runs)
        out.append(int(np.median(votes)))
    return out


def _one(image, cap, eps_frac, spur, merge=0.34, bridge=0.70):
    import math
    import numpy as np
    import cv2
    m0, H, W = _ink(image, cap)
    m = _drop_border(m0, H, W)
    if int(m.sum()) < 200:
        m = m0
    sk = _thin(cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)))
    paths = _paths(sk)
    if not paths:
        return {"no_read": True, "reason": "no_paths"}
    eps = max(2.0, eps_frac * float(min(H, W)))
    pts, segs = [], []
    for poly in [_rdp(p, eps) for p in paths]:
        for k in range(len(poly) - 1):
            segs.append((len(pts), len(pts) + 1))
            pts.append(poly[k])
            pts.append(poly[k + 1])
    if len(segs) < 3:
        return {"no_read": True, "reason": "few_segments"}
    Ls = sorted(math.hypot(pts[a][0] - pts[b][0], pts[a][1] - pts[b][1]) for a, b in segs)
    med = float(np.median(Ls[len(Ls) // 2:]))
    if med < 10:
        return {"no_read": True, "reason": "scale"}
    vc, lab = _cluster(pts, 0.22 * med)
    E = sorted({(min(lab[a], lab[b]), max(lab[a], lab[b])) for a, b in segs if lab[a] != lab[b]})
    if len(E) < 3:
        return {"no_read": True, "reason": "few_edges"}
    for _ in range(5):
        vc, E = _clean(vc, E, med, spur, merge, 0.0)
        if len(E) < 3:
            return {"no_read": True, "reason": "few_edges"}
        nm = float(np.median([_elen(vc, e) for e in E]))
        if abs(nm - med) < 0.02 * med:
            med = nm
            break
        med = nm
    vc, E = _clean(vc, E, med, spur, merge, bridge)
    if len(E) < 3:
        return {"no_read": True, "reason": "few_edges"}
    comps, adj = _comps(len(vc), E)

    def ink_weight(c):
        s = set(c)
        return sum(_elen(vc, e) for e in E if e[0] in s and e[1] in s)
    big = max(comps, key=ink_weight)
    ren = {v: k for k, v in enumerate(big)}
    V = [vc[v] for v in big]
    EE = sorted({(min(ren[a], ren[b]), max(ren[a], ren[b])) for a, b in E if a in ren and b in ren})
    _c, adj2 = _comps(len(V), EE)
    cyc, big_ring, found = _cycles(len(V), EE, adj2)
    deg = {i: len(adj2[i]) for i in range(len(V))}
    ring_v = set()
    for c in found:
        ring_v |= set(c)
    pend, pend_paths = [], []
    for t in range(len(V)):
        if deg[t] != 1:
            continue
        k, prev, cur, walk = 0, t, list(adj2[t])[0], [t]
        while True:
            k += 1
            walk.append(cur)
            if deg[cur] != 2 or cur in ring_v:
                break
            nxt = [x for x in adj2[cur] if x != prev]
            if not nxt:
                break
            prev, cur = cur, nxt[0]
            if k > 40:
                break
        pend.append(k)
        pend_paths.append(walk)
    gaps = []
    for c in sorted(found):
        cyc_v = list(c)
        seq = [cyc_v[0]]
        while len(seq) < len(cyc_v):
            nxt = [v for v in adj2[seq[-1]] if v in c and v not in seq]
            if not nxt:
                break
            seq.append(nxt[0])
        if len(seq) != len(cyc_v):
            continue
        marks = [k for k, v in enumerate(seq) if deg[v] >= 3]
        if len(marks) >= 2:
            g = [marks[k + 1] - marks[k] for k in range(len(marks) - 1)]
            g.append(len(seq) - marks[-1] + marks[0])
            gaps.append(sorted(g))
        else:
            gaps.append([])
    orders = _bond_orders(m0, H, W, V, EE)
    return {"no_read": False, "V": len(V), "E": len(EE), "rings": int(cyc),
            "largest_ring": int(big_ring), "pend": sorted(pend), "gaps": sorted(gaps),
            "orders_multi": sorted([o for o in orders if o >= 2], reverse=True),
            "vc": V, "edges": EE, "ring_v": sorted(ring_v), "pend_paths": pend_paths,
            "orders": orders, "hw": [H, W], "med": round(med, 1)}


_GRID = [(1100, 0.0040, 0.32), (1200, 0.0045, 0.32), (1300, 0.0050, 0.32),
         (1100, 0.0050, 0.36), (1400, 0.0040, 0.36), (1200, 0.0035, 0.30),
         (1000, 0.0045, 0.32), (1500, 0.0045, 0.34), (1200, 0.0060, 0.32)]


def _cache_key(image):
    import hashlib
    import os
    try:
        st = os.stat(str(image))
        return hashlib.md5(("%s|%d|%d" % (str(image), st.st_size, int(st.st_mtime))).encode("utf-8", "replace")).hexdigest()
    except Exception:
        return hashlib.md5(str(image).encode("utf-8", "replace")).hexdigest()


def _overlay_path(image, tag):
    import hashlib
    import os
    import tempfile
    d = os.path.join(tempfile.gettempdir(), "genolympiad_overlay")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    h = hashlib.md5(("%s|%s" % (str(image), tag)).encode("utf-8", "replace")).hexdigest()[:12]
    return os.path.join(d, "e7bsmiles_%s_%s.png" % (tag, h))


def skeleton_graph(image, geom=0):
    """Trace the drawn molecule into atoms, bonds, rings and branch chains by majority."""
    import json
    import os
    import tempfile
    import collections
    ck = _cache_key(image)
    cache_path = os.path.join(tempfile.gettempdir(), "genolympiad_overlay", "e7bsmiles_cache_%s.json" % ck)
    rows = None
    if not geom and os.path.exists(cache_path):
        try:
            rows = json.load(open(cache_path, encoding="utf-8"))
        except Exception:
            rows = None
    if rows is None:
        rows = []
        for cap, ef, sp in _GRID:
            try:
                r = _one(image, cap, ef, sp)
            except Exception as e:
                r = {"no_read": True, "reason": "%s:%s" % (type(e).__name__, e)}
            rows.append(r)
        if not geom:
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                json.dump([{k: v for k, v in r.items()
                            if k in ("no_read", "reason", "V", "E", "rings", "largest_ring",
                                     "pend", "gaps", "orders_multi")} for r in rows],
                          open(cache_path, "w", encoding="utf-8"))
            except Exception:
                pass
    good = [r for r in rows if not r.get("no_read")]
    if len(good) < 3:
        return {"no_read": True, "reason": "unreadable", "n_ok": len(good)}

    def mode(key):
        c = collections.Counter(json.dumps(r.get(key)) for r in good)
        return json.loads(c.most_common(1)[0][0])
    out = {"no_read": False, "n_ok": len(good), "V": mode("V"), "E": mode("E"),
           "rings": mode("rings"), "largest_ring": mode("largest_ring"),
           "pend": mode("pend"), "gaps": mode("gaps"), "orders_multi": mode("orders_multi")}
    if geom:
        for r in good:
            if r.get("V") == out["V"] and r.get("pend") == out["pend"]:
                out["geom"] = {k: r[k] for k in ("vc", "edges", "ring_v", "pend_paths", "orders", "hw")}
                break
        if "geom" not in out:
            g = good[0]
            out["geom"] = {k: g[k] for k in ("vc", "edges", "ring_v", "pend_paths", "orders", "hw")}
    return out


def draw_skeleton_overlay(image, tag="skeleton"):
    """Draw the traced atoms, bonds, rings and branch chains over the image."""
    import math
    from PIL import Image, ImageDraw, ImageFont
    r = skeleton_graph(image, geom=1)
    pil = _pil(image)
    W0, H0 = pil.size
    im = pil.copy()
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype("arialbd.ttf", max(16, int(0.026 * min(W0, H0))))
    except Exception:
        f = ImageFont.load_default()
    if r.get("no_read"):
        d.text((14, 14), "NO READ: %s" % r.get("reason"), fill=(230, 20, 20), font=f)
        p = _overlay_path(image, tag)
        im.save(p)
        return {"path": p, "no_read": True}
    g = r["geom"]
    H, W = g["hw"]
    sx, sy = W0 / float(W), H0 / float(H)
    COLS = [(0, 150, 235), (220, 90, 0), (140, 0, 190), (0, 150, 60), (200, 0, 90), (110, 90, 0)]
    lw = max(2, int(0.004 * min(W0, H0)))
    for k, (a, b) in enumerate(g["edges"]):
        pa, pb = g["vc"][a], g["vc"][b]
        o = g["orders"][k]
        col = (110, 110, 118) if o == 1 else ((235, 30, 30) if o == 2 else (0, 170, 90))
        d.line([pa[0] * sx, pa[1] * sy, pb[0] * sx, pb[1] * sy], fill=col, width=lw + 1)
    for k, walk in enumerate(g["pend_paths"]):
        col = COLS[k % len(COLS)]
        for t in range(len(walk) - 1):
            pa, pb = g["vc"][walk[t]], g["vc"][walk[t + 1]]
            d.line([pa[0] * sx, pa[1] * sy, pb[0] * sx, pb[1] * sy], fill=col, width=lw + 3)
        tip = g["vc"][walk[0]]
        nxt = g["vc"][walk[1]]
        ux, uy = tip[0] - nxt[0], tip[1] - nxt[1]
        n = math.hypot(ux, uy) or 1.0
        ex, ey = (tip[0] + ux / n * 0.55 * n) * sx, (tip[1] + uy / n * 0.55 * n) * sy
        d.line([tip[0] * sx, tip[1] * sy, ex, ey], fill=col, width=lw)
        d.text((ex + 6, ey - 10), "%d" % (len(walk) - 1), fill=col, font=f)
    for k, (a, b) in enumerate(g["edges"]):
        if g["orders"][k] < 2:
            continue
        pa, pb = g["vc"][a], g["vc"][b]
        col = (235, 30, 30) if g["orders"][k] == 2 else (0, 170, 90)
        d.line([pa[0] * sx, pa[1] * sy, pb[0] * sx, pb[1] * sy], fill=col, width=max(2, lw - 1))
    for i, p in enumerate(g["vc"]):
        x, y = p[0] * sx, p[1] * sy
        rr = max(5, int(0.009 * min(W0, H0)))
        c = (255, 150, 0) if i in g["ring_v"] else (30, 30, 200)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=c, width=lw)
    d.text((14, 14), "atoms=%d  bonds=%d  rings=%d  largest ring=%d  branch chains=%s"
           % (r["V"], r["E"], r["rings"], r["largest_ring"], r["pend"]),
           fill=(20, 20, 20), font=f)
    p = _overlay_path(image, tag)
    im.save(p)
    return {"path": p, "no_read": False, "V": r["V"], "pend": r["pend"]}

# end of skeleton_graph_code

# code: cmp_code
def enough_atoms_and_bonds(graph, reference):
    """1 if the traced molecule has at least six atoms and five bonds, else 0."""
    return 1.0 if (int(graph['V']) >= 6 and int(graph['E']) >= 5) else 0.0

# end of cmp_code

# code: cmp_code_2
def hetero_atoms_match(answer, reference):
    """1 if the non carbon elements named in the answer match the reference set, else 0."""
    import re
    s = str(answer)
    low = s.strip().lower().rstrip('.')
    want = set(str(x) for x in reference['hetero_letters'])
    if low in ('none', 'no', 'n/a', 'nothing'):
        return 1.0 if not want else 0.0
    NAMES = {'chlorine': 'Cl', 'bromine': 'Br', 'nitrogen': 'N', 'oxygen': 'O',
             'fluorine': 'F', 'sulfur': 'S', 'sulphur': 'S', 'phosphorus': 'P',
             'iodine': 'I', 'silicon': 'Si', 'carbon': 'C', 'hydrogen': 'H'}
    got = set(v for k, v in NAMES.items() if k in low)
    if not got:
        CANON = {'cl': 'Cl', 'br': 'Br', 'si': 'Si'}
        got = set(CANON.get(tok, tok.upper())
                  for tok in re.findall(r'cl|br|si|[bcnofpsik]', low))
    got -= set(['C', 'H'])
    return 1.0 if got == want else 0.0

# end of cmp_code_2

# code: cmp_code_3
def ring_count_matches(graph, reference):
    """1 if the traced ring count equals the reference, else 0."""
    return 1.0 if int(graph['rings']) == int(reference['rings']) else 0.0

# end of cmp_code_3

# code: cmp_code_4
def largest_ring_matches(graph, reference):
    """1 if the traced largest ring size equals the reference, else 0."""
    return 1.0 if int(graph['largest_ring']) == int(reference['largest_ring']) else 0.0

# end of cmp_code_4

# code: cmp_code_5
def bond_orders_match(graph, reference):
    """1 if the traced double and triple bond orders match the reference list, else 0."""
    return 1.0 if [int(x) for x in graph['orders_multi']] == [int(x) for x in reference['multiple_bond_orders']] else 0.0

# end of cmp_code_5

# code: cmp_code_6
def atom_count_matches(graph, reference):
    """1 if the traced atom count equals the reference heavy atom count, else 0."""
    return 1.0 if int(graph['V']) == int(reference['heavy_atoms']) else 0.0

# end of cmp_code_6

# code: cmp_code_7
def ring_gaps_match(graph, reference):
    """1 if the traced gaps between ring attachments match the reference, else 0."""
    a = [[int(x) for x in g] for g in graph['gaps']]
    b = [[int(x) for x in g] for g in reference['ring_attachment_gaps']]
    return 1.0 if a == b else 0.0

# end of cmp_code_7

# code: cmp_code_8
def branch_lengths_match(graph, reference):
    """1 if the traced branch chain lengths match the reference list, else 0."""
    return 1.0 if [int(x) for x in graph['pend']] == [int(x) for x in reference['branch_chain_lengths']] else 0.0

# end of cmp_code_8

# code: cmp_code_9
def overlay_was_drawn(overlay):
    """1 if the skeleton overlay was traced and drawn, else 0."""
    return 0.0 if overlay.get('no_read') else 1.0

# end of cmp_code_9
