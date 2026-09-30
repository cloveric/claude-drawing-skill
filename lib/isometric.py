"""isometric — a pastel isometric 2.5D diorama: a tiny world of blocks on a floating slab, seen through an
orthographic camera and lit by one low, soft sun and a lavender sky (numpy + Pillow only).

Model: a small ray tracer, not a painter's algorithm.
  camera     a true isometric orthographic camera (azimuth 45 deg, elevation 35.26 deg). World x runs to the
             lower left of the screen, y to the lower right, z straight up; one world unit is one ground tile.
             Parallel lines stay parallel and nothing shrinks with distance -- the "model on a desk" look.
  solids     every part is an exact analytic solid, traced per pixel:
               convex polyhedra given as planes (boxes with chamfered edges, gable and hip roofs, rotated
               panels, low-poly rocks, boat hulls, card panels),
               frustums along any axis (cylinders, cones, masts, trunks, tubes, arms),
               ellipsoids that may be cut by planes (tree crowns, cups, domes, a balloon, flat-bottomed clouds).
             The camera pass writes a G-buffer -- depth, normal, albedo, material -- so what hides what never
             depends on drawing order. Surfaces can carry a `paint(P, n, tag)` function evaluated at the exact
             world point: tile edges, soil layers, roof courses, louvres, solar cells, text on a card.
  sun        the same solids are traced again from the sun into a shadow map and from straight above into a
             height map. Shading is  albedo x (sky ambient x occlusion + sun x N.L x visibility).
             Axis-aligned faces therefore come out in three clean values: tops brightest, the sun side (+x,
             facing lower left) a step darker, the far side (+y, facing lower right) lit only by the sky. The
             three-tone look of isometric art falls out of the lighting, it is not painted on.
  shadows    percentage-closer soft shadows: a blocker search measures how far the receiver is from what
             shades it, and the penumbra widens with that distance -- crisp where a wall meets the ground,
             blurred at the tip of a long shadow, very soft under a floating cloud or balloon. Filter taps are
             corrected for the receiver's slope, so wide filters do not self-shadow.
  occlusion  from the top-down map, which keeps for every ground point the top *and the bottom* of the
             highest column above it (touching solids merge; an eave or a tree crown is a slab in the air).
             Upward faces: how far the blurred surroundings rise above the point, at three radii -- tile gaps
             go deep, the ground darkens round every footing. Side faces: the horizon seen out along the normal
             (and 40 deg either side), where a column only hides the band of sky it really covers -- a wall is
             never darkened by its own building or its own eaves, only by what stands in front of it, plus a
             small crease where it meets the ground. Column extents are sampled nearest, never interpolated.
             Floating things (clouds, cards, the balloon) and hairlines (guy wires) stay out of the map.
  colour     pastel albedos, a lilac-blue sky ambient (shadows are cool lilac, never grey), a warm low sun.
             Chamfers on box edges catch a thin line of light. Materials: matte, water (shore foam, shallow to
             deep tint, glassy side walls), glass (sky sheen), soft (wrapped light for foliage and clouds),
             gloss (a small highlight), card (printed panels that stay legible). No glow, no bloom, no outline.
  backdrop   a light vertical gradient with an invisible floor far below the slab: the slab's own shadow and a
             broad contact shade land on it, which is what makes the diorama float.
  finish     rendered at `ss` x resolution and box-filtered down, so edges are clean; titles, a compass and
             captions are typeset on top in 2D. `stage()` shades a half-size preview (fast) for drawing animations.

    from isometric import Isometric
    iso = Isometric(1920, 1080, seed=3, scale=72, look=(5, 5, 0), at=(0.56, 0.52))
    iso.backdrop()
    iso.slab(0, 0, 10, 10)                                   # the floating base with its soil layers
    iso.tiles(levels)            # 10x10 ints: 0 sea, 1 sand, 2 grass (top 0.32), 3 terrace (0.60), 4 paving
    iso.sea()                                                # water in the 0 cells, foam along the shore
    iso.building(3, 3, 5, 4.4, z=0.32, h=0.9, roof='gable', axis='y', windows=(1, 2, 2), door=('+x', 3.6))
    iso.tree(6.5, 2.5, iso.top_z(6.5, 2.5), size=1.0, kind='round')
    iso.windmill(2, 7, 0.32, h=2.6, yaw=30)
    x, y, z = iso.unproject(1500, 250, z=3.0)                # place a floating card by its screen position
    iso.card(x, y, z, 2.9, 1.65, title='风速', tag='WIND', value='4.6', unit='m/s', anchor=(2.2, 7, 2.9))
    iso.text('Island Station', 120, 150, 64)
    iso.save('out.jpg')
Coordinates are world units (x, y on the ground, z up); `iso.iso(x, y, z)` gives the screen point.
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, smoothstep, load_font

MATTE, WATER, GLASS, CARD, SOFT, GLOSS = 1, 2, 3, 4, 5, 6
_MAT = {'matte': MATTE, 'water': WATER, 'glass': GLASS, 'card': CARD, 'soft': SOFT, 'gloss': GLOSS}
INK = '#34305a'          # deep indigo for type
LILAC, MINT, PEACH, BUTTER, CORAL, SKY = '#c9b8f2', '#a9e0c2', '#f6cdb4', '#f7df97', '#f19a8e', '#a9cdf2'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _unit(v):
    v = np.asarray(v, np.float64)
    return v / (np.linalg.norm(v) + 1e-12)


def rot(yaw=0.0, pitch=0.0, roll=0.0):
    """rotation matrix local -> world (degrees): roll about x, then pitch about y, then yaw about z"""
    a, b, c = np.radians([yaw, pitch, roll])
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    Ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(c), -np.sin(c)], [0, np.sin(c), np.cos(c)]])
    return Rz @ Ry @ Rx


def _hash(ix, iy, seed=0):
    """integer lattice -> [0, 1) (vectorised)"""
    n = (np.asarray(ix, np.int64) * 374761393 + np.asarray(iy, np.int64) * 668265263 + seed * 144269477) & 0xffffffff
    n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
    return ((n ^ (n >> 16)) & 0xffff).astype(np.float32) / 65536.0


def _bilerp(M, i, j):
    """bilinear sample of a 2D map at float (row, col) index coordinates, clamped to the edge"""
    H, W = M.shape
    i = np.clip(i, 0, H - 1.001); j = np.clip(j, 0, W - 1.001)
    i0 = i.astype(np.int32); j0 = j.astype(np.int32)
    fi = (i - i0).astype(np.float32); fj = (j - j0).astype(np.float32)
    return ((M[i0, j0] * (1 - fj) + M[i0, j0 + 1] * fj) * (1 - fi)
            + (M[i0 + 1, j0] * (1 - fj) + M[i0 + 1, j0 + 1] * fj) * fi)


def _tex(T, u, v):
    """bilinear sample of an (h, w, C) texture at u, v in 0..1 (u right, v down)"""
    h, w = T.shape[:2]
    x = np.clip(u * w - 0.5, 0, w - 1.001); y = np.clip(v * h - 0.5, 0, h - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32)
    fx = (x - x0)[:, None]; fy = (y - y0)[:, None]
    return ((T[y0, x0] * (1 - fx) + T[y0, x0 + 1] * fx) * (1 - fy)
            + (T[y0 + 1, x0] * (1 - fx) + T[y0 + 1, x0 + 1] * fx) * fy)


# ------------------------------------------------------------------ cameras
class _Cam:
    """orthographic camera: pixel (i, j) looks along v from C + a*r - b*u, a = (j+.5-W/2)/S, b = (i+.5-H/2)/S"""

    def __init__(self, C, r, u, v, S, W, H):
        self.C = np.asarray(C, np.float64); self.r = _unit(r); self.u = _unit(u); self.v = _unit(v)
        self.S = float(S); self.W = int(W); self.H = int(H)

    def cols(self, j):
        return ((np.asarray(j, np.float64) + 0.5 - self.W / 2) / self.S).astype(np.float32)[None, :]

    def rows(self, i):
        return ((np.asarray(i, np.float64) + 0.5 - self.H / 2) / self.S).astype(np.float32)[:, None]

    def project(self, P):
        d = np.asarray(P, np.float64) - self.C
        return (d @ self.r * self.S + self.W / 2 - 0.5, -(d @ self.u) * self.S + self.H / 2 - 0.5, d @ self.v)

    def bbox(self, lo, hi, pad=2):
        lo, hi = np.asarray(lo, np.float64), np.asarray(hi, np.float64)
        cs = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        j, i, _ = self.project(cs)
        return (max(0, int(np.floor(i.min())) - pad), min(self.H, int(np.ceil(i.max())) + pad + 1),
                max(0, int(np.floor(j.min())) - pad), min(self.W, int(np.ceil(j.max())) + pad + 1))

    def points(self, a, b, t):
        return (self.C[None] + a[:, None] * self.r[None] - b[:, None] * self.u[None]
                + np.asarray(t, np.float64)[:, None] * self.v[None])


# ------------------------------------------------------------------ analytic solids
class _Convex:
    """intersection of half-spaces n.X <= d; tag = index of the face hit"""

    def __init__(self, N, d, lo, hi):
        N = np.asarray(N, np.float64)
        nn = np.linalg.norm(N, axis=1, keepdims=True)
        self.N = N / nn; self.d = np.asarray(d, np.float64) / nn[:, 0]
        self.lo = np.asarray(lo, np.float64); self.hi = np.asarray(hi, np.float64)

    def trace(self, cam, a, b):
        shape = (b.shape[0], a.shape[1])
        tn = np.full(shape, -np.inf, np.float32); tf = np.full(shape, np.inf, np.float32)
        tag = np.zeros(shape, np.int16)
        for k, (n, d) in enumerate(zip(self.N, self.d)):
            dn = float(n @ cam.v)
            num = np.float32(d - n @ cam.C) - a * np.float32(n @ cam.r) + b * np.float32(n @ cam.u)
            if dn < -1e-9:
                t = num / np.float32(dn)
                upd = t > tn
                np.copyto(tn, t, where=upd); np.copyto(tag, np.int16(k), where=upd)
            elif dn > 1e-9:
                np.minimum(tf, num / np.float32(dn), out=tf)
            else:
                tf[num < 0] = -np.inf
        hit = tn <= tf
        return np.where(hit, tn, np.inf).astype(np.float32), tag, np.where(hit, tf, -np.inf).astype(np.float32)

    def normal(self, P, tag):
        return self.N[tag]


class _Frustum:
    """solid cone frustum (cylinder when r0 == r1) from base B along unit axis A, length h; tag 0 side, 1 base, 2 top"""

    def __init__(self, B, A, h, r0, r1):
        self.B = np.asarray(B, np.float64); self.A = _unit(A); self.h = float(h); self.r0 = float(r0); self.r1 = float(r1)
        self.k = (self.r1 - self.r0) / self.h
        E = self.B + self.A * self.h; R = max(self.r0, self.r1)
        self.lo = np.minimum(self.B, E) - R; self.hi = np.maximum(self.B, E) + R

    def trace(self, cam, a, b):
        A = self.A; w0 = cam.C - self.B
        va = float(cam.v @ A); wv = float(w0 @ cam.v)
        wa = np.float32(w0 @ A) + a * np.float32(cam.r @ A) - b * np.float32(cam.u @ A)
        ww = (np.float32(w0 @ w0) + a * a + b * b + 2 * a * np.float32(w0 @ cam.r) - 2 * b * np.float32(w0 @ cam.u))
        pq = np.float32(wv) - wa * np.float32(va); pp = ww - wa * wa; qq = np.float32(1 - va * va)
        al = self.r0 + self.k * wa; be = np.float32(self.k * va)
        Aq = qq - be * be
        if abs(Aq) < 1e-7: Aq = np.float32(1e-7)
        Bq = pq - al * be; Cq = pp - al * al
        disc = Bq * Bq - Aq * Cq
        sq = np.sqrt(np.maximum(disc, 0))
        best = np.full(disc.shape, np.inf, np.float32); tag = np.zeros(disc.shape, np.int16)
        far = np.full(disc.shape, -np.inf, np.float32)
        for sgn in (-1, 1):
            t = (-Bq + sgn * sq) / Aq
            s = wa + t * np.float32(va)
            ok = (disc >= 0) & (s >= 0) & (s <= self.h)
            np.copyto(far, np.maximum(far, t), where=ok)
            np.copyto(best, t, where=ok & (t < best))
        if abs(va) > 1e-9:
            for tg, s0, rr in ((1, 0.0, self.r0), (2, self.h, self.r1)):
                t = (np.float32(s0) - wa) / np.float32(va)
                rad2 = pp + 2 * t * pq + t * t * qq
                ok = rad2 <= rr * rr
                np.copyto(far, np.maximum(far, t), where=ok)
                ok &= t < best
                np.copyto(best, t, where=ok); np.copyto(tag, np.int16(tg), where=ok)
        return best, tag, far

    def normal(self, P, tag):
        w = P - self.B
        s = w @ self.A
        m = w - s[:, None] * self.A[None]
        m = m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-9)
        n = m - self.k * self.A[None]
        n = n / np.linalg.norm(n, axis=1, keepdims=True)
        n[tag == 1] = -self.A; n[tag == 2] = self.A
        return n


class _Ellipsoid:
    """ellipsoid (centre c, semi-axes R along the columns of M) cut by optional half-spaces n.X <= d; tag 0 = curved"""

    def __init__(self, c, R, M=None, clip=()):
        self.c = np.asarray(c, np.float64); self.R = np.asarray(R, np.float64)
        self.M = np.eye(3) if M is None else np.asarray(M, np.float64)           # local -> world
        self.clip = [(_unit(n), float(d) / np.linalg.norm(n)) for n, d in clip]
        ext = np.sqrt(((self.M * self.R[None]) ** 2).sum(1))
        self.lo = self.c - ext; self.hi = self.c + ext

    def trace(self, cam, a, b):
        Mt = self.M.T                                                         # world -> local
        o0 = Mt @ (cam.C - self.c) / self.R; orr = Mt @ cam.r / self.R; ou = Mt @ cam.u / self.R
        dv = Mt @ cam.v / self.R
        A = float(dv @ dv)
        Bq = np.float32(o0 @ dv) + a * np.float32(orr @ dv) - b * np.float32(ou @ dv)
        oo = 0
        for k in range(3):
            ok = np.float32(o0[k]) + a * np.float32(orr[k]) - b * np.float32(ou[k])
            oo = oo + ok * ok
        disc = Bq * Bq - A * (oo - 1)
        sq = np.sqrt(np.maximum(disc, 0))
        tn = np.where(disc >= 0, (-Bq - sq) / A, np.inf).astype(np.float32)
        tf = np.where(disc >= 0, (-Bq + sq) / A, -np.inf).astype(np.float32)
        tag = np.zeros(tn.shape, np.int16)
        for k, (n, d) in enumerate(self.clip):
            dn = float(n @ cam.v)
            num = np.float32(d - n @ cam.C) - a * np.float32(n @ cam.r) + b * np.float32(n @ cam.u)
            if dn < -1e-9:
                t = num / np.float32(dn); upd = t > tn
                np.copyto(tn, t, where=upd); np.copyto(tag, np.int16(k + 1), where=upd)
            elif dn > 1e-9:
                np.minimum(tf, num / np.float32(dn), out=tf)
            else:
                tf[num < 0] = -np.inf
        hit = tn <= tf
        return np.where(hit, tn, np.inf).astype(np.float32), tag, np.where(hit, tf, -np.inf).astype(np.float32)

    def normal(self, P, tag):
        p = (P - self.c) @ self.M / self.R
        n = (p / self.R) @ self.M.T
        n = n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-12)
        for k, (cn, _) in enumerate(self.clip):
            n[tag == k + 1] = cn
        return n


def _box_planes(lo, hi, bevel=0.0):
    N, d = [], []
    for ax in range(3):
        e = np.zeros(3); e[ax] = 1
        N += [e, -e]; d += [hi[ax], -lo[ax]]
    if bevel > 0:
        for a1, a2 in ((0, 1), (0, 2), (1, 2)):
            for s1 in (1, -1):
                for s2 in (1, -1):
                    n = np.zeros(3); n[a1] = s1; n[a2] = s2
                    e1 = hi[a1] if s1 > 0 else lo[a1]; e2 = hi[a2] if s2 > 0 else lo[a2]
                    N.append(n); d.append(s1 * e1 + s2 * e2 - bevel)
    return np.array(N, np.float64), np.array(d, np.float64)


class _Prim:
    __slots__ = ('solid', 'colour', 'paint', 'mat', 'cast', 'ao')

    def __init__(self, solid, colour, paint, mat, cast, ao):
        self.solid = solid; self.colour = colour; self.paint = paint; self.mat = mat; self.cast = cast; self.ao = ao


# ------------------------------------------------------------------ the diorama
class Isometric:
    def __init__(self, W=1920, H=1080, seed=0, scale=72.0, look=(5.0, 5.0, 0.0), at=(0.56, 0.52),
                 bounds=(-3, -3, -1.6, 13, 13, 8), sun=(0.36, -0.72, 0.52), ss=2, floor=-2.4, record=True,
                 elevation=35.264, azimuth=45.0):
        self.W, self.H, self.ss = int(W), int(H), int(ss)
        self.seed = seed; self.rng = np.random.default_rng(seed)
        self.record = record; self.stages = []; self.overlays = []
        self.floor = float(floor)
        Ws, Hs = self.W * self.ss, self.H * self.ss
        self.Ws, self.Hs = Ws, Hs
        el, az = np.radians(elevation), np.radians(azimuth)
        v = -np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
        r = np.array([-np.sin(az), np.cos(az), 0.0])
        u = np.array([-np.cos(az) * np.sin(el), -np.sin(az) * np.sin(el), np.cos(el)])
        S = scale * self.ss
        look = np.asarray(look, np.float64)
        C = look - ((at[0] * Ws - Ws / 2) / S) * r + ((at[1] * Hs - Hs / 2) / S) * u
        self.cam = _Cam(C, r, u, v, S, Ws, Hs)
        self.scale = float(scale)
        # sun and its shadow camera
        self.L = _unit(sun)
        lv = -self.L; lr = _unit(np.cross([0, 0, 1.0], lv)); lu = np.cross(lv, lr)
        b0, b1 = np.array(bounds[:3], np.float64), np.array(bounds[3:], np.float64)
        cs = np.array([[x, y, z] for x in (b0[0], b1[0]) for y in (b0[1], b1[1]) for z in (b0[2], b1[2])])
        cen = (b0 + b1) / 2
        er = np.abs((cs - cen) @ lr).max(); eu = np.abs((cs - cen) @ lu).max()
        Sl = min(150.0, 2600 / (2 * max(er, eu)))
        self.lcam = _Cam(cen, lr, lu, lv, Sl, int(2 * er * Sl) + 8, int(2 * eu * Sl) + 8)
        St = 90.0
        self.tcam = _Cam((cen[0], cen[1], b1[2] + 1), (1, 0, 0), (0, -1, 0), (0, 0, -1), St,
                         int((b1[0] - b0[0]) * St) + 8, int((b1[1] - b0[1]) * St) + 8)
        # buffers
        self.dep = np.full((Hs, Ws), np.inf, np.float32)
        self.nrm = np.zeros((Hs, Ws, 3), np.float16)
        self.alb = np.zeros((Hs, Ws, 3), np.float16)
        self.mat = np.zeros((Hs, Ws), np.uint8)
        self.ldep = np.full((self.lcam.H, self.lcam.W), np.inf, np.float32)
        self.tdep = np.full((self.tcam.H, self.tcam.W), np.inf, np.float32)
        self.tbot = np.full((self.tcam.H, self.tcam.W), -np.inf, np.float32)
        # light: a warm low sun, a lilac-blue sky, a warm bounce from below
        self.sun_c = np.array([1.0, 0.955, 0.87], np.float32) * 0.52
        self.sky_c = np.array([0.735, 0.735, 0.875], np.float32)
        self.hor_c = np.array([0.705, 0.690, 0.790], np.float32)
        self.gnd_c = np.array([0.760, 0.700, 0.700], np.float32)
        self.soft = 0.085            # penumbra growth per unit of receiver-blocker distance (the sun's size)
        self.pen = (0.012, 0.55)     # smallest / largest penumbra radius (world units)
        self.bg = ('#e6e1f4', '#f6efef', '#fbf8ff')
        self.glow_centre = tuple(look)
        self.sea_z = 0.14

    # ------------------------------------------------------------ helpers
    def iso(self, x, y, z=0.0):
        """world point -> output-image pixel (x, y)"""
        j, i, _ = self.cam.project(np.array([x, y, z], np.float64))
        return float((j + 0.5) / self.ss), float((i + 0.5) / self.ss)

    def unproject(self, sx, sy, z=0.0):
        """output-image pixel (sx, sy) -> the world point on the horizontal plane at height z that lands there"""
        cam = self.cam
        a = (sx * self.ss - self.Ws / 2) / cam.S; b = (sy * self.ss - self.Hs / 2) / cam.S
        Q = cam.C + a * cam.r - b * cam.u
        t = (z - Q[2]) / cam.v[2]
        P = Q + t * cam.v
        return float(P[0]), float(P[1]), float(z)

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def add(self, solid, colour='#ffffff', paint=None, mat='matte', cast=True, ao=True):
        """rasterise any analytic solid into the camera G-buffer, the sun's shadow map and the height map"""
        pr = _Prim(solid, _c(colour), paint, _MAT[mat] if isinstance(mat, str) else mat, cast, ao)
        self._raster_g(pr)
        if cast: self._raster_d(self.lcam, self.ldep, solid)
        if ao: self._raster_d(self.tcam, self.tdep, solid, self.tbot)
        return pr

    def _raster_g(self, pr):
        cam = self.cam
        i0, i1, j0, j1 = cam.bbox(pr.solid.lo, pr.solid.hi)
        if i1 <= i0 or j1 <= j0: return
        a = cam.cols(np.arange(j0, j1))
        step = max(8, 600000 // max(1, j1 - j0))
        for r0 in range(i0, i1, step):
            r1 = min(i1, r0 + step)
            b = cam.rows(np.arange(r0, r1))
            t, tag, _ = pr.solid.trace(cam, a, b)
            sub = self.dep[r0:r1, j0:j1]
            m = t < sub
            if not m.any(): continue
            ii, jj = np.nonzero(m)
            tt = t[ii, jj]; tg = tag[ii, jj]
            P = cam.points(a[0, jj].astype(np.float64), b[ii, 0].astype(np.float64), tt)
            n = pr.solid.normal(P, tg)
            if pr.paint is not None:
                col = np.asarray(pr.paint(P, n, tg), np.float32)
            else:
                col = np.broadcast_to(pr.colour, (len(tt), 3))
            sub[ii, jj] = tt
            self.nrm[r0 + ii, j0 + jj] = n
            self.alb[r0 + ii, j0 + jj] = col
            self.mat[r0 + ii, j0 + jj] = pr.mat

    def _raster_d(self, cam, buf, solid, bot=None):
        """depth-only pass (shadow map, or the top-down map). For the top-down map `bot` keeps the bottom of the
        topmost column: solids that touch or overlap merge into one column, a solid floating above replaces it
        (so an eave or a tree crown is a slab in the air, not a pillar down to the ground)"""
        i0, i1, j0, j1 = cam.bbox(solid.lo, solid.hi)
        if i1 <= i0 or j1 <= j0: return
        a = cam.cols(np.arange(j0, j1))
        step = max(8, 600000 // max(1, j1 - j0))
        for r0 in range(i0, i1, step):
            r1 = min(i1, r0 + step)
            t, _, tout = solid.trace(cam, a, cam.rows(np.arange(r0, r1)))
            T = buf[r0:r1, j0:j1]
            if bot is None:
                np.minimum(T, t, out=T); continue
            B = bot[r0:r1, j0:j1]
            hit = np.isfinite(t)
            touch = hit & (t <= B + 0.004) & (tout >= T - 0.004)
            above = hit & ~touch & (t < T)
            np.copyto(B, np.maximum(B, tout), where=touch); np.copyto(T, np.minimum(T, t), where=touch)
            np.copyto(B, tout, where=above); np.copyto(T, t, where=above)

    # ------------------------------------------------------------ primitives
    def box(self, x0, y0, z0, x1, y1, z1, colour='#f4f1ee', side=None, bevel=0.022, paint=None, **kw):
        """axis-aligned block with chamfered edges; `side` colours the walls (default: same as the top)"""
        lo = np.array([min(x0, x1), min(y0, y1), min(z0, z1)]); hi = np.array([max(x0, x1), max(y0, y1), max(z0, z1)])
        bev = min(bevel, 0.45 * (hi - lo).min())
        N, d = _box_planes(lo, hi, bev)
        if paint is None and side is not None:
            ct, cs = _c(colour), _c(side)
            paint = lambda P, n, t: np.where(n[:, 2:3] > 0.5, ct, cs)
        return self.add(_Convex(N, d, lo, hi), colour, paint, **kw)

    def obox(self, centre, size, yaw=0.0, pitch=0.0, roll=0.0, colour='#f4f1ee', bevel=0.015, paint=None, **kw):
        """oriented block: `size` = full extents along its local axes, rotated by yaw / pitch / roll (degrees)"""
        R = rot(yaw, pitch, roll); c = np.asarray(centre, np.float64); h = np.asarray(size, np.float64) / 2
        N, d = _box_planes(-h, h, min(bevel, 0.45 * (2 * h).min()))
        Nw = N @ R.T
        dw = d + Nw @ c
        ext = np.abs(R) @ h
        return self.add(_Convex(Nw, dw, c - ext, c + ext), colour, paint, **kw)

    def convex(self, planes, lo, hi, colour='#f4f1ee', paint=None, **kw):
        """any convex solid given as [(normal, d), ...] meaning normal . X <= d, with its world bounding box"""
        N = [p[0] for p in planes]; d = [p[1] for p in planes]
        return self.add(_Convex(N, d, lo, hi), colour, paint, **kw)

    def prism(self, pts, z0, z1, colour='#f4f1ee', paint=None, **kw):
        """vertical extrusion of a convex footprint polygon (counter-clockwise or clockwise, any order of turn)"""
        P = np.asarray(pts, np.float64); c = P.mean(0)
        N, d = [[0, 0, 1], [0, 0, -1]], [z1, -z0]
        for k in range(len(P)):
            p, q = P[k], P[(k + 1) % len(P)]
            n = np.array([q[1] - p[1], -(q[0] - p[0]), 0.0])
            if n[:2] @ (c - p) > 0: n = -n
            N.append(n); d.append(n[:2] @ p)
        lo = np.r_[P.min(0), z0]; hi = np.r_[P.max(0), z1]
        return self.add(_Convex(N, d, lo, hi), colour, paint, **kw)

    def cylinder(self, x, y, z0, z1, r, colour='#f4f1ee', r1=None, paint=None, **kw):
        """upright cylinder, or a cone / frustum when r1 is given"""
        return self.add(_Frustum((x, y, z0), (0, 0, 1), z1 - z0, r, r if r1 is None else r1), colour, paint, **kw)

    def tube(self, p0, p1, r, colour='#f4f1ee', r1=None, paint=None, **kw):
        """cylinder (or cone) between two world points: arms, rails, wires, masts, pipes"""
        p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
        L = float(np.linalg.norm(p1 - p0))
        return self.add(_Frustum(p0, p1 - p0, L, r, r if r1 is None else r1), colour, paint, **kw)

    def ellipsoid(self, centre, radii, colour='#f4f1ee', yaw=0.0, pitch=0.0, roll=0.0, clip=(), paint=None, **kw):
        """ellipsoid with semi-axes `radii`, rotated; `clip` = [(normal, d)] half-spaces cut it (flat bottoms, cups)"""
        return self.add(_Ellipsoid(centre, radii, rot(yaw, pitch, roll), clip), colour, paint, **kw)

    def sphere(self, x, y, z, r, colour='#f4f1ee', **kw):
        return self.ellipsoid((x, y, z), (r, r, r), colour, **kw)

    def dome(self, x, y, z, r, colour='#f4f1ee', h=None, **kw):
        """half ellipsoid sitting on z (radius r, height h)"""
        return self.ellipsoid((x, y, z), (r, r, r if h is None else h), colour, clip=[((0, 0, -1), -z)], **kw)

    # ------------------------------------------------------------ ground
    def backdrop(self, top='#e6e1f4', bottom='#f6efef', glow='#fbf8ff', centre=None):
        """the light vertical gradient the diorama floats in front of, with a soft pale glow behind world point
        `centre` (default: the look point). Its invisible floor lies at `floor`, far below the slab, and takes the
        slab's shadow."""
        self.bg = (top, bottom, glow)
        if centre is not None: self.glow_centre = tuple(centre)

    def slab(self, x0, y0, x1, y1, z0=-1.1, z1=0.0, top='#e4dcf2',
             layers=(('#f1dccb', 0.10), ('#dccff1', 0.30), ('#cdbfec', 0.28), ('#bfb0e6', 0.42)), bevel=0.05):
        """the floating base: a thick block whose walls show layered strata with gently wavy boundaries"""
        cols = [_c(c) for c, _ in layers]
        edges = np.cumsum([h for _, h in layers])
        ct = _c(top); seed = self._seed()
        ph = np.random.default_rng(seed).uniform(0, 6.28, (len(layers), 3))

        def paint(P, n, t):
            s = P[:, 0] + P[:, 1]
            depth = z1 - P[:, 2]
            k = np.zeros(len(P), np.int32)
            for li in range(len(layers) - 1):
                wav = 0.025 * np.sin(s * 1.7 + ph[li, 0]) + 0.012 * np.sin(s * 4.3 + ph[li, 1])
                k += (depth > edges[li] + wav * (li > 0)).astype(np.int32)
            out = np.stack(cols)[np.minimum(k, len(cols) - 1)]
            return np.where(n[:, 2:3] > 0.5, ct, out)
        self.box(x0, y0, z0, x1, y1, z1, top, bevel=bevel, paint=paint)

    def tiles(self, levels, x0=0.0, y0=0.0, heights=None, colours=None, soil=None, gap=0.028, bevel=0.03, paved=(4,)):
        """ground tiles on a grid: levels[i][j] is the level of cell (x0 + i, y0 + j); 0 = none (sea).
        Default levels: 1 sand, 2 grass, 3 raised grass (terrace), 4 paving. Each tile is its own chamfered block
        with a gap round it; the terrace shows a soil band under the turf; paved levels are cut into flagstones."""
        L = np.asarray(levels)
        heights = heights or {1: 0.22, 2: 0.32, 3: 0.60, 4: 0.30}
        colours = colours or {1: ['#f7e3c6', '#f4ddbd', '#f8e8cf'], 2: ['#a9e0c2', '#a1dbba', '#b1e5c9'],
                              3: ['#9dd8b8', '#a6dfc0', '#95d1b0'], 4: ['#e3ddef', '#ddd6ec', '#e8e3f3']}
        soil = soil or {1: '#f1d6b8', 2: '#e9cdb4', 3: '#e3c3a8', 4: '#d3cbe6'}
        rng = np.random.default_rng(self._seed())
        self.levels = L; self.grid0 = (x0, y0); self.heights = heights
        for i in range(L.shape[0]):
            for j in range(L.shape[1]):
                lv = int(L[i, j])
                if lv <= 0: continue
                h = heights[lv]; ct = _c(colours[lv][rng.integers(len(colours[lv]))]); cs = _c(soil[lv])
                turf = 0.07 if lv == 3 else h
                cside = ct * 0.96
                pave = lv in paved

                def paint(P, n, t, h=h, ct=ct, cs=cs, turf=turf, cside=cside, pave=pave):
                    top = n[:, 2:3] > 0.5
                    band = (P[:, 2:3] > h - turf)
                    col = np.where(top, ct, np.where(band, cside, cs))
                    if pave:
                        fx = np.mod(P[:, 0] - x0, 0.5); fy = np.mod(P[:, 1] - y0 + 0.25 * (np.floor((P[:, 0] - x0) * 2) % 2), 0.5)
                        jt = ((np.minimum(fx, 0.5 - fx) < 0.011) | (np.minimum(fy, 0.5 - fy) < 0.011)) & top[:, 0]
                        col = np.where(jt[:, None], ct * 0.9, col)
                    return col
                self.box(x0 + i + gap, y0 + j + gap, 0.0, x0 + i + 1 - gap, y0 + j + 1 - gap, h, ct, bevel=bevel, paint=paint)

    def top_z(self, x, y):
        """height of the tile under world point (x, y) (0.14 on the sea)"""
        i, j = int(np.floor(x - self.grid0[0])), int(np.floor(y - self.grid0[1]))
        if 0 <= i < self.levels.shape[0] and 0 <= j < self.levels.shape[1] and self.levels[i, j] > 0:
            return self.heights[int(self.levels[i, j])]
        return self.sea_z

    def sea(self, levels=None, x0=None, y0=None, z=0.14, shallow='#bfe8e6', deep='#a6c9f0', foam='#fbfdff',
            side='#c5dcf6', waves=0.6):
        """water in every level-0 cell: shore foam hugging the tiles, a second broken wave line, a tint from
        shallow to deep with distance from land, sparse wave dashes, and clear glassy walls at the slab edge"""
        L = self.levels if levels is None else np.asarray(levels)
        gx0, gy0 = (self.grid0 if x0 is None else (x0, y0))
        self.sea_z = z
        # distance to the nearest land cell, on a fine grid
        R = 40; nx, ny = L.shape
        xs = (np.arange(nx * R) + 0.5) / R; ys = (np.arange(ny * R) + 0.5) / R
        X, Y = np.meshgrid(xs, ys, indexing='ij')
        D = np.full(X.shape, 9.0, np.float32)
        for i, j in zip(*np.nonzero(L > 0)):
            dx = np.maximum(np.maximum(i - X, X - (i + 1)), 0); dy = np.maximum(np.maximum(j - Y, Y - (j + 1)), 0)
            np.minimum(D, np.hypot(dx, dy), out=D)
        cs, cd, cf, cw = _c(shallow), _c(deep), _c(foam), _c(side)
        seed = self._seed()

        def paint(P, n, t):
            lx, ly = P[:, 0] - gx0, P[:, 1] - gy0
            d = _bilerp(D, lx * R - 0.5, ly * R - 0.5)
            k = smoothstep(0.0, 1.6, d)[:, None]
            col = cs * (1 - k) + cd * k
            wob = 0.018 * np.sin(lx * 9.0 + ly * 3.1) + 0.012 * np.sin(ly * 11.0 - lx * 2.3)
            f1 = 1 - smoothstep(0.045, 0.075, d + wob)
            line = np.abs(d - 0.19 + wob * 1.4)
            brk = _hash(np.floor((lx - ly) * 3.1).astype(np.int64), np.floor((lx + ly) * 1.3).astype(np.int64), seed) > 0.28
            f2 = (1 - smoothstep(0.010, 0.020, line)) * brk * 0.85
            # sparse wave dashes out at sea: short strokes along the x - y diagonal
            cu, cv = (ly - lx) * 0.55, (lx + ly) * 2.2
            iu, iv = np.floor(cu).astype(np.int64), np.floor(cv).astype(np.int64)
            hsh = _hash(iu, iv, seed + 7)
            fu, fv = cu - iu, cv - iv
            dash = (hsh < 0.16 * waves) & (np.abs(fv - 0.5) < 0.075) & (np.abs(fu - 0.5 - 0.1 * (hsh - 0.1)) < 0.09 + 0.1 * hsh)
            f3 = dash * smoothstep(0.35, 0.8, d) * 0.8
            f = np.clip(np.maximum(np.maximum(f1, f2), f3), 0, 1)[:, None]
            top = n[:, 2:3] > 0.5
            wall = cw * (0.92 + 0.08 * np.clip((P[:, 2:3] + 0.0) / z, 0, 1))
            lip = (P[:, 2:3] > z - 0.02)
            wall = np.where(lip, cf * 0.97, wall)
            return np.where(top, col * (1 - f) + cf * f, wall)
        for i in range(nx):                                                   # runs of sea cells along y
            j = 0
            while j < ny:
                if L[i, j] > 0: j += 1; continue
                j1 = j
                while j1 < ny and L[i, j1] == 0: j1 += 1
                self.box(gx0 + i, gy0 + j, 0.0, gx0 + i + 1, gy0 + j1, z, shallow, bevel=0.0, paint=paint, mat='water')
                j = j1

    def road(self, x0, y0, x1, y1, z=0.0, h=0.05, colour='#d9d4e8', line='#fbfaff', dash=(0.22, 0.16), kerb=None):
        """a flat road slab with a dashed centre line along its long axis (and optional lighter kerbs)"""
        along_x = abs(x1 - x0) >= abs(y1 - y0)
        cc, cl = _c(colour), _c(line); ck = _c(kerb) if kerb else None
        mid = (y0 + y1) / 2 if along_x else (x0 + x1) / 2
        half = (abs(y1 - y0) if along_x else abs(x1 - x0)) / 2

        def paint(P, n, t):
            s = P[:, 0] if along_x else P[:, 1]; q = (P[:, 1] if along_x else P[:, 0]) - mid
            on = (np.abs(q) < 0.028) & (np.mod(s, dash[0] + dash[1]) < dash[0]) & (n[:, 2] > 0.5)
            out = np.where(on[:, None], cl, cc)
            if ck is not None:
                out = np.where((np.abs(q) > half - 0.07)[:, None] & (n[:, 2:3] > 0.5), ck, out)
            return out
        return self.box(x0, y0, z, x1, y1, z + h, colour, bevel=0.012, paint=paint)

    def path(self, cells, z=None, colour='#e6e0f1', joint='#cfc6e4', h=0.26, gap=0.035):
        """paved slabs on any list of cells (x, y), e.g. a walkway on a roof or a quay; each is cut into four
        flagstones by fine joints (for paving inside the ground grid use level 4 in `tiles`)"""
        cc, cj = _c(colour), _c(joint)
        for (x, y) in cells:
            zz = 0.0 if z is None else z

            def paint(P, n, t):
                fx = np.mod(P[:, 0], 0.5); fy = np.mod(P[:, 1], 0.5)
                jt = ((np.minimum(fx, 0.5 - fx) < 0.012) | (np.minimum(fy, 0.5 - fy) < 0.012)) & (n[:, 2] > 0.5)
                return np.where(jt[:, None], cj, cc)
            self.box(x + gap, y + gap, zz, x + 1 - gap, y + 1 - gap, zz + h, colour, bevel=0.03, paint=paint)

    # ------------------------------------------------------------ architecture
    def roof(self, x0, y0, x1, y1, z, h, kind='gable', axis='x', overhang=0.08, colour='#f2a494', gable='#f7f2ee',
             courses=0.11, thick=0.05):
        """gable (ridge along `axis`), hip (all four sides at one pitch) or shed (falling toward +x) roof on the
        rectangle, with eaves, tile courses and a light fascia along the lower edge; gable ends take the wall colour"""
        x0, x1 = x0 - overhang, x1 + overhang; y0, y1 = y0 - overhang, y1 + overhang
        z0 = z - thick
        cr, cg = _c(colour), _c(gable)
        N, d, slopes = [(0, 0, -1)], [-z0], []
        if kind == 'gable':
            if axis == 'x':
                k = h / ((y1 - y0) / 2)
                N += [(0, k, 1), (0, -k, 1), (1, 0, 0), (-1, 0, 0)]; d += [k * y1 + z, -k * y0 + z, x1, -x0]
            else:
                k = h / ((x1 - x0) / 2)
                N += [(k, 0, 1), (-k, 0, 1), (0, 1, 0), (0, -1, 0)]; d += [k * x1 + z, -k * x0 + z, y1, -y0]
            slopes = [1, 2]
        elif kind == 'hip':
            k = h / (min(x1 - x0, y1 - y0) / 2)
            N += [(k, 0, 1), (-k, 0, 1), (0, k, 1), (0, -k, 1)]; d += [k * x1 + z, -k * x0 + z, k * y1 + z, -k * y0 + z]
            slopes = [1, 2, 3, 4]
        else:
            k = h / (x1 - x0)
            N += [(k, 0, 1), (-1, 0, 0), (1, 0, 0), (0, 1, 0), (0, -1, 0)]; d += [k * x0 + z + h, -x0, x1, y1, -y0]
            slopes = [1]
        N = np.array(N, np.float64); d = np.array(d, np.float64)

        def paint(P, n, t):
            slope = np.isin(t, slopes)[:, None]
            zz = P[:, 2:3]
            crs = np.mod((zz - z0) / courses, 1.0)
            line = (crs < 0.13) & slope
            fas = (zz < z0 + thick * 0.95) & slope
            col = np.where(line, cr * 0.91, cr)
            col = np.where(fas, np.minimum(cr * 1.1 + 0.02, 1.0), col)
            return np.where(slope, col, np.where(np.abs(n[:, 2:3]) > 0.9, cr * 0.8, cg))
        lo = (x0, y0, z0); hi = (x1, y1, z + h + 0.01)
        return self.add(_Convex(N, d, lo, hi), colour, paint)

    def window(self, x, y, z, w=0.22, h=0.28, facing='+x', frame='#fbfaf8', glass='#a9c8ee', sill=True, mullion=True):
        """a window on a wall: (x, y) is the wall point under its centre, z its bottom. A white frame, glass with a
        diagonal sky sheen and a cross mullion, and a sill that throws a thin shadow"""
        ax = 0 if facing[1] == 'x' else 1; sg = 1 if facing[0] == '+' else -1
        o = np.array([x, y], np.float64)
        e = np.zeros(2); e[ax] = sg                  # out of the wall
        t = np.zeros(2); t[1 - ax] = 1               # along the wall
        cg, cf = _c(glass), _c(frame)

        def seg(u0, u1, out0, out1, z0, z1, col, paint=None, mat='matte', bev=0.006):
            p0 = o + t * u0 + e * out0; p1 = o + t * u1 + e * out1
            self.box(p0[0], p0[1], z0, p1[0], p1[1], z1, col, bevel=bev, paint=paint, mat=mat, ao=False)
        seg(-w / 2 - 0.025, w / 2 + 0.025, -0.01, 0.018, z - 0.025, z + h + 0.025, frame)

        def gpaint(P, n, tg):
            along = (P[:, :2] - o) @ t
            vz = (P[:, 2] - z) / h
            sheen = np.abs((along / w + 0.5) * 0.8 + vz - 0.95) < 0.09
            sheen |= np.abs((along / w + 0.5) * 0.8 + vz - 1.2) < 0.035
            col = cg * (0.92 + 0.14 * vz[:, None])
            col = np.where(sheen[:, None], np.minimum(col * 1.18 + 0.05, 1), col)
            if mullion:
                mm = (np.abs(along) < 0.011) | (np.abs(vz - 0.52) * h < 0.011)
                col = np.where(mm[:, None], cf, col)
            return col
        seg(-w / 2, w / 2, -0.01, 0.024, z, z + h, glass, paint=gpaint, mat='glass', bev=0.0)
        if sill:
            seg(-w / 2 - 0.04, w / 2 + 0.04, -0.01, 0.06, z - 0.045, z - 0.012, frame)

    def door(self, x, y, z, w=0.26, h=0.46, facing='+x', colour='#f6d98a', frame='#fbfaf8', canopy=True):
        """a door with a frame, a small window pane, a knob and a little canopy above it"""
        ax = 0 if facing[1] == 'x' else 1; sg = 1 if facing[0] == '+' else -1
        o = np.array([x, y], np.float64); e = np.zeros(2); e[ax] = sg; t = np.zeros(2); t[1 - ax] = 1

        def seg(u0, u1, out0, out1, z0, z1, col, **kw):
            p0 = o + t * u0 + e * out0; p1 = o + t * u1 + e * out1
            self.box(p0[0], p0[1], z0, p1[0], p1[1], z1, col, ao=False, **kw)
        seg(-w / 2 - 0.03, w / 2 + 0.03, -0.01, 0.016, z, z + h + 0.03, frame, bevel=0.006)
        cd = _c(colour)

        def dpaint(P, n, tg):
            along = (P[:, :2] - o) @ t; vz = (P[:, 2] - z) / h
            pane = (np.abs(along) < w * 0.26) & (vz > 0.62) & (vz < 0.86)
            panel = (np.abs(np.abs(along) - w * 0.3) < 0.006) & (vz < 0.5) & (vz > 0.12)
            col = np.where(pane[:, None], _c('#bcd5f2'), cd)
            return np.where(panel[:, None], cd * 0.9, col)
        seg(-w / 2, w / 2, -0.01, 0.022, z, z + h, colour, bevel=0.004, paint=dpaint)
        k = o + t * (w * 0.3) + e * 0.03
        self.sphere(k[0], k[1], z + h * 0.45, 0.014, '#f7f3ea', ao=False)
        if canopy:
            seg(-w / 2 - 0.08, w / 2 + 0.08, -0.01, 0.16, z + h + 0.06, z + h + 0.1, frame, bevel=0.01)

    def building(self, x0, y0, x1, y1, z=0.0, h=1.0, wall='#f7f3ef', roof='gable', roof_colour='#f2a494', axis='x',
                 roof_h=None, windows=(1, 2, 2), window_h=0.26, door=None, trim=None):
        """a house or block: walls, a roof ('gable' / 'hip' / 'shed' / 'flat'), windows = (rows, n on the +x wall,
        n on the +y wall) -- the two walls the camera sees (+x faces lower left, +y lower right) --, an optional
        door = ('+x' or '+y', position along that wall) and an optional trim band at the foot of the walls"""
        cw = _c(wall); tr = _c(trim) if trim else None

        def wpaint(P, n, t):
            if tr is None: return np.broadcast_to(cw, (len(P), 3))
            band = (P[:, 2:3] < z + 0.07)
            return np.where(band & (np.abs(n[:, 2:3]) < 0.5), tr, cw)
        self.box(x0, y0, z, x1, y1, z + h, wall, bevel=0.02, paint=wpaint)
        if roof == 'flat':
            self.box(x0 - 0.03, y0 - 0.03, z + h, x1 + 0.03, y1 + 0.03, z + h + 0.07, roof_colour, bevel=0.015)
        else:
            rh = roof_h if roof_h is not None else 0.42 * ((y1 - y0) if axis == 'x' else (x1 - x0))
            self.roof(x0, y0, x1, y1, z + h, rh, kind=roof, axis=axis, colour=roof_colour, gable=wall)
        rows, nx, ny = windows
        for face, (a0, a1), fixed, n in (('+x', (y0, y1), x1, nx), ('+y', (x0, x1), y1, ny)):
            for rr in range(rows):
                zz = z + (rr + 0.5) * h / rows - window_h / 2 + 0.02
                for cc in range(n):
                    s = a0 + (cc + 0.5) * (a1 - a0) / n
                    if door and door[0] == face and abs(s - door[1]) < 0.3 and rr == 0: continue
                    if face == '+x': self.window(fixed, s, zz, 0.2, window_h, '+x')
                    else: self.window(s, fixed, zz, 0.2, window_h, '+y')
        if door:
            face, s = door
            if face == '+x': self.door(x1, s, z, facing='+x')
            else: self.door(s, y1, z, facing='+y')

    # ------------------------------------------------------------ nature
    def tree(self, x, y, z=0.0, size=1.0, kind='round', colour=None, trunk='#d7b49c', seed=None, flowers=None):
        """'round' (lumpy crown of three puffs), 'pine' (stacked cones), 'poplar' (tall column), 'bush';
        a bush can carry `flowers` (a colour or a list): small blossoms dotted over the top of its puffs"""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        s = size
        if kind == 'bush':
            col = colour or ['#9fdcb9', '#93d3ae', '#abe3c3'][rng.integers(3)]
            puffs = []
            for k in range(3):
                a = rng.uniform(0, 6.28) + k * 2.1; d = 0.06 * s
                r = s * rng.uniform(0.07, 0.1)
                c = (x + d * np.cos(a), y + d * np.sin(a), z + r * 0.55); puffs.append((c, r))
                self.ellipsoid(c, (r, r, r * 0.85), col, mat='soft', clip=[((0, 0, -1), -z)])
            if flowers:
                fl = [flowers] if isinstance(flowers, str) else list(flowers)
                for k in range(9):
                    (cx, cy, cz), r = puffs[k % 3]
                    th, ph = rng.uniform(0, 6.28), rng.uniform(0.15, 0.95)
                    p = (cx + r * np.sin(ph) * np.cos(th), cy + r * np.sin(ph) * np.sin(th), cz + r * 0.85 * np.cos(ph))
                    self.sphere(*p, 0.018 * s, fl[k % len(fl)], ao=False)
            return
        if kind == 'pine':
            col = colour or ['#86cfa3', '#7cc79b', '#8fd6ab'][rng.integers(3)]
            self.cylinder(x, y, z, z + 0.16 * s, 0.03 * s, trunk)
            zz = z + 0.1 * s
            for k, (r, hh) in enumerate(((0.2, 0.3), (0.16, 0.27), (0.11, 0.24))):
                self.cylinder(x, y, zz, zz + hh * s, r * s, col, r1=0.012 * s, mat='soft')
                zz += hh * s * 0.52
            return
        if kind == 'poplar':
            col = colour or ['#addfc4', '#a6dcc0'][rng.integers(2)]
            self.cylinder(x, y, z, z + 0.14 * s, 0.028 * s, trunk)
            self.ellipsoid((x, y, z + 0.5 * s), (0.13 * s, 0.13 * s, 0.4 * s), col, mat='soft')
            return
        col = colour or ['#a3dfbd', '#97d6b2', '#aee6c6', '#9bd8c0'][rng.integers(4)]
        th = 0.2 * s
        self.cylinder(x, y, z, z + th + 0.1 * s, 0.035 * s, trunk)
        R = 0.25 * s
        cz = z + th + R * 0.9
        self.ellipsoid((x, y, cz), (R, R, R * 0.95), col, mat='soft')
        for k in range(2):
            a = rng.uniform(0, 6.28)
            rr = R * rng.uniform(0.55, 0.7)
            self.ellipsoid((x + np.cos(a) * R * 0.55, y + np.sin(a) * R * 0.55, cz + R * rng.uniform(-0.15, 0.35)),
                           (rr, rr, rr * 0.95), _c(col) * rng.uniform(0.97, 1.02), mat='soft')

    def rock(self, x, y, z=0.0, r=0.14, colour='#d8d0ea', seed=None):
        """a low-poly boulder: random facets around a squashed sphere, flat on the ground"""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        N, d = [(0, 0, -1)], [-z]
        c = np.array([x, y, z + r * 0.2])
        k = np.arange(13) + 0.5                                        # facets spread evenly over the upper half
        th = k * 2.39996 + rng.uniform(0, 6.28); ph = np.arccos(1 - k / 13 * 0.95)
        for t_, p_ in zip(th, ph):
            n = _unit(np.array([np.sin(p_) * np.cos(t_), np.sin(p_) * np.sin(t_), np.cos(p_)]) + rng.normal(0, 0.12, 3))
            N.append(n); d.append(n @ c + r * rng.uniform(0.8, 1.0) * np.sqrt(n[0] ** 2 + n[1] ** 2 + (0.62 * n[2]) ** 2))
        return self.convex(list(zip(N, d)), c - r * 1.3, c + r * 1.3, colour)

    def cloud(self, x, y, z, size=1.0, colour='#fbfaff', seed=None, cast=True):
        """a flat-bottomed cloud of overlapping puffs, softly lit; floats, so it casts a very soft shadow"""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        s = size
        puffs = [(0, 0, 0.42), (0.34, -0.3, 0.3), (-0.36, 0.32, 0.3), (0.12, 0.42, 0.26), (-0.1, -0.44, 0.24)]
        for dx, dy, r in puffs:
            r = r * s * rng.uniform(0.9, 1.1)
            self.ellipsoid((x + dx * s, y + dy * s, z + r * 0.15), (r, r, r * 0.9), colour, mat='soft',
                           clip=[((0, 0, -1), -(z - 0.02 * s))], cast=cast, ao=False)

    # ------------------------------------------------------------ machines and props
    def windmill(self, x, y, z=0.0, h=2.4, yaw=35.0, spin=15.0, colour='#fbfaf8', accent='#f19a8e', blade=0.9):
        """a small wind turbine: tapered tower, nacelle, hub and three slim blades (accent-tipped)"""
        self.cylinder(x, y, z, z + h, 0.055, colour, r1=0.03)
        R = rot(yaw)
        f = R @ np.array([1.0, 0, 0])                                         # the way the rotor faces
        top = np.array([x, y, z + h])
        self.obox(top + f * 0.03 + np.array([0, 0, 0.02]), (0.26, 0.09, 0.09), yaw=yaw, colour=colour, bevel=0.02)
        hub = top + f * 0.19 + np.array([0, 0, 0.02])
        self.ellipsoid(hub, (0.07, 0.045, 0.045), colour, yaw=yaw)
        ca = _c(accent); cc = _c(colour)
        for k in range(3):
            ang = spin + 120 * k
            ctr = hub + (R @ np.array([0.0, np.cos(np.radians(ang)), np.sin(np.radians(ang))])) * (blade / 2 + 0.03)

            def bp(P, n, t, hub=hub):
                dd = np.linalg.norm(P - hub, axis=1)
                return np.where((dd > blade * 0.86)[:, None], ca, cc)
            self.ellipsoid(ctr, (0.012, blade / 2, 0.045), colour, yaw=yaw, roll=ang, paint=bp)

    def dish(self, x, y, z=0.0, r=0.2, yaw=35.0, tilt=50.0, h=0.45, colour='#fbfaf8', face='#eeeaf6', accent='#f19a8e'):
        """a satellite dish on a post: a shallow bowl (half an ellipsoid; its flat face is the reflector, shaded
        darker toward the rim), a feed arm and a small receiver at the focus. The dish looks along yaw / tilt"""
        el = np.radians(90 - tilt); az = np.radians(yaw)
        f = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])       # where it looks
        c = np.array([x, y, z + h])
        self.cylinder(x, y, z, z + h - 0.02, 0.022, colour)
        # local frame: third axis = f
        e3 = f; e1 = _unit(np.cross([0, 0, 1.0], e3)); e2 = np.cross(e3, e1)
        M = np.stack([e1, e2, e3], 1)
        cf = _c(face)

        def paint(P, n, t):
            q = np.linalg.norm((P - c) - ((P - c) @ e3)[:, None] * e3[None], axis=1) / r
            bowl = cf * (0.86 + 0.16 * q[:, None] ** 2)                 # a concave face: darker in the middle
            bowl = np.where((q > 0.9)[:, None], _c(colour), bowl)         # the rolled rim
            return np.where((t == 1)[:, None], bowl, _c(colour))
        self.add(_Ellipsoid(c, (r, r, r * 0.35), M, clip=[(e3, e3 @ c)]), colour, paint)
        tip = c + f * r * 0.75
        self.tube(c + f * 0.005, tip, 0.008, colour, ao=False)
        self.sphere(*tip, 0.028, accent, ao=False)

    def windsock(self, x, y, z=0.0, h=0.9, yaw=30.0, droop=12.0, length=0.55, colour='#f19a8e', stripe='#fbfaf8',
                 pole='#fbfaf8'):
        """an airfield windsock: a pole, a ring, and a tapered striped sock streaming downwind (yaw) and drooping"""
        self.cylinder(x, y, z, z + h + 0.06, 0.018, pole)
        top = np.array([x, y, z + h])
        d = np.array([np.cos(np.radians(yaw)) * np.cos(np.radians(droop)),
                      np.sin(np.radians(yaw)) * np.cos(np.radians(droop)), -np.sin(np.radians(droop))])
        base = top + d * 0.03
        cs, cc = _c(stripe), _c(colour)

        def paint(P, n, t):
            k = ((P - base) @ d) / length
            return np.where((np.floor(k * 5) % 2 == 1)[:, None], cs, cc)
        self.add(_Frustum(base, d, length, 0.075, 0.035), colour, paint)
        self.tube(top - d * 0.02, top + d * 0.03, 0.08, pole, r1=0.08)

    def solar_panel(self, x, y, z=0.0, w=0.9, d=0.5, tilt=28.0, yaw=0.0, colour='#8fb0e6', frame='#f4f1f8', h=0.18):
        """a tilted solar panel on two legs: glass with a cell grid and a pale frame"""
        R = rot(yaw, -tilt)
        c = np.array([x, y, z + h + np.sin(np.radians(tilt)) * d / 2])
        cp, cf = _c(colour), _c(frame)

        def paint(P, n, t):
            q = (P - c) @ R                                                  # local coordinates
            top = (n @ (R @ np.array([0, 0, 1.0]))) > 0.9
            gu = np.mod(q[:, 1] / (w / 6), 1.0); gv = np.mod(q[:, 0] / (d / 3), 1.0)
            grid = (np.minimum(gu, 1 - gu) < 0.05) | (np.minimum(gv, 1 - gv) < 0.06)
            rim = (np.abs(q[:, 1]) > w / 2 - 0.025) | (np.abs(q[:, 0]) > d / 2 - 0.025)
            col = np.where(grid[:, None], cp * 1.14, cp)
            col = np.where(rim[:, None] | ~top[:, None], cf, col)
            return np.minimum(col, 1)
        self.obox(c, (d, w, 0.03), yaw=yaw, pitch=-tilt, colour=colour, paint=paint, mat='glass', bevel=0.008)
        for s in (-1, 1):
            p = np.array([x, y]) + (R @ np.array([0, s * w * 0.36, 0]))[:2]
            self.cylinder(p[0], p[1], z, c[2], 0.018, frame)

    def fence(self, pts, z=0.0, h=0.2, colour='#fbfaf8', spacing=0.2, closed=False):
        """a picket fence along a polyline of (x, y): posts with pointed tops and two rails"""
        P = [np.asarray(p, np.float64) for p in pts] + ([np.asarray(pts[0], np.float64)] if closed else [])
        zz = z if np.isscalar(z) else None
        for a, b in zip(P[:-1], P[1:]):
            L = np.linalg.norm(b - a); n = max(1, int(round(L / spacing)))
            z0 = zz if zz is not None else z(a[0], a[1])
            for k in range(n + 1):
                q = a + (b - a) * k / n
                self.box(q[0] - 0.018, q[1] - 0.018, z0, q[0] + 0.018, q[1] + 0.018, z0 + h, colour, bevel=0.008)
            for rz in (0.35, 0.75):
                self.tube((a[0], a[1], z0 + h * rz), (b[0], b[1], z0 + h * rz), 0.011, colour, ao=False)

    def pier(self, x0, y0, x1, y1, z=0.26, colour='#ecd7c4', post='#d9bca5', plank=0.12, bottom=0.0):
        """a jetty: planks across its length with small gaps, on round posts standing in the water"""
        along_x = abs(x1 - x0) >= abs(y1 - y0)
        L = abs(x1 - x0) if along_x else abs(y1 - y0)
        n = int(L / plank)
        rng = np.random.default_rng(self._seed())
        for k in range(n):
            s0 = k * L / n + 0.008; s1 = (k + 1) * L / n - 0.008
            col = _c(colour) * rng.uniform(0.97, 1.02)
            if along_x: self.box(min(x0, x1) + s0, y0, z - 0.04, min(x0, x1) + s1, y1, z, col, bevel=0.008)
            else: self.box(x0, min(y0, y1) + s0, z - 0.04, x1, min(y0, y1) + s1, z, col, bevel=0.008)
        m = max(2, int(L / 0.7) + 1)
        for k in range(m):
            s = 0.08 + k * (L - 0.16) / (m - 1)
            for side in (0, 1):
                if along_x: px, py = min(x0, x1) + s, (y0 + 0.06 if side == 0 else y1 - 0.06)
                else: px, py = (x0 + 0.06 if side == 0 else x1 - 0.06), min(y0, y1) + s
                self.cylinder(px, py, bottom, z - 0.04 + 0.05, 0.035, post)

    def boat(self, x, y, z=0.14, length=0.9, width=0.36, yaw=0.0, hull='#fbfaf8', stripe='#f19a8e', deck='#ecd7c4',
             cabin='#fbfaf8'):
        """a small boat afloat at water level z: a convex hull with a pointed bow and raked keel, a coloured band,
        a wooden deck and a little cabin with a coloured roof. The bow points along `yaw` (degrees from +x)"""
        R = rot(yaw); c = np.array([x, y, z], np.float64)
        l, w, hd, hb, bl = length / 2, width / 2, 0.11, 0.08, length * 0.32
        loc = [((0, 0, 1), hd), ((0, 0, -1), hb), ((0, 1, 0), w), ((0, -1, 0), w), ((-1, 0, 0), l),
               ((w, bl, 0), w * l), ((w, -bl, 0), w * l), ((0.9, 0, -1), 0.9 * l * 0.25 + hb), ((-0.7, 0, -1), 0.7 * l * 0.7 + hb)]
        N, d = [], []
        for n, dd in loc:
            n = np.asarray(n, np.float64); nn = np.linalg.norm(n)
            nw = R @ (n / nn); N.append(nw); d.append(dd / nn + nw @ c)
        cs, ch, cd = _c(stripe), _c(hull), _c(deck)

        def paint(P, n, t):
            zz = P[:, 2:3] - z
            top = n[:, 2:3] > 0.9
            band = (zz > hd * 0.35) & (zz < hd * 0.72)
            return np.where(top, cd, np.where(band, cs, ch))
        self.convex(list(zip(N, d)), c - l - 0.05, c + l + 0.05, hull, paint=paint)
        self.obox(c + R @ np.array([-l * 0.28, 0, hd + 0.08]), (length * 0.32, width * 0.6, 0.16), yaw=yaw,
                  colour=cabin, bevel=0.02)
        self.obox(c + R @ np.array([-l * 0.28, 0, hd + 0.175]), (length * 0.38, width * 0.7, 0.03), yaw=yaw,
                  colour=stripe, bevel=0.01)

    def balloon(self, x, y, z, r=0.42, colour='#fbe4ea', string=0.9, payload='#fbfaf8'):
        """a weather balloon: a glossy sphere with a neck, a string and a small instrument box hanging below"""
        self.sphere(x, y, z, r, colour, mat='gloss', ao=False)
        self.cylinder(x, y, z - r - 0.05, z - r * 0.8, 0.03, colour, r1=0.07, ao=False)
        self.tube((x, y, z - r - 0.05), (x, y, z - r - string), 0.006, '#9f98c0', ao=False)
        bz = z - r - string
        self.box(x - 0.06, y - 0.05, bz - 0.12, x + 0.06, y + 0.05, bz, payload, bevel=0.012, ao=False)

    # ------------------------------------------------------------ infographics
    def card(self, x, y, z, w=2.4, h=1.5, facing='+x', title='', tag='', value='', unit='', note='', series=None,
             accent='#9d86e8', icon=None, anchor=None, paper='#fdfcff', ink=INK, thick=0.05, stamp=''):
        """a floating data card: a thin panel standing upright (its face towards `facing`), printed with a label,
        a big value, a unit, a note and a small trend line; a slim leader drops from it to `anchor`.
        (x, y) is the centre of the card's bottom edge, z its bottom."""
        ax = 0 if facing[1] == 'x' else 1
        tex = self._card_texture(w, h, title, tag, value, unit, note, series, accent, icon, paper, ink, stamp)
        if ax == 0:
            lo, hi = (x - thick, y - w / 2, z), (x, y + w / 2, z + h)
            ev = np.array([0, 1.0, 0]); org = np.array([x, y - w / 2, z + h])
        else:
            lo, hi = (x - w / 2, y - thick, z), (x + w / 2, y, z + h)
            ev = np.array([-1.0, 0, 0]); org = np.array([x + w / 2, y, z + h])
        cp = _c(paper); cedge = _c(accent) * 0.35 + cp * 0.65

        def paint(P, n, t):
            front = n[:, ax] > 0.9
            u = ((P - org) @ ev) / w; v = (org[2] - P[:, 2]) / h
            rgba = _tex(tex, u, v)
            col = rgba[:, :3] * rgba[:, 3:4] + cp * (1 - rgba[:, 3:4])
            return np.where(front[:, None], col, cedge)
        self.box(*lo, *hi, paper, bevel=0.02, paint=paint, mat='card', ao=False, cast=True)
        if anchor is not None:
            a = np.asarray(anchor, np.float64)
            s = np.array([x - (thick / 2 if ax == 0 else 0), y - (thick / 2 if ax == 1 else 0), z])
            self.tube(s, a, 0.009, '#a49bd0', ao=False, cast=False)
            self.sphere(*a, 0.035, accent, ao=False, cast=False)
            self.sphere(*s, 0.02, '#a49bd0', ao=False, cast=False)

    def sign(self, x, y, z, w, h, text, facing='+x', colour='#fbfaf8', ink=INK, font='cjk_sans', thick=0.025):
        """a small plate on a wall or post with centred lettering; (x, y) = wall point under its centre, z = bottom"""
        ax = 0 if facing[1] == 'x' else 1; sg = 1 if facing[0] == '+' else -1
        ppu = 260; TW, TH = max(8, int(w * ppu)), max(8, int(h * ppu))
        im = Image.new('RGBA', (TW, TH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        f = load_font(font, int(TH * 0.62))
        d.text((TW / 2, TH / 2), text, font=f, fill=tuple(int(c * 255) for c in _c(ink)) + (255,), anchor='mm')
        tex = np.asarray(im, np.float32) / 255
        cp = _c(colour)
        if ax == 0:
            lo, hi = (x, y - w / 2, z), (x + sg * thick, y + w / 2, z + h)
            org = np.array([x, y - w / 2 if sg > 0 else y + w / 2, z + h]); ev = np.array([0, float(sg), 0])
        else:
            lo, hi = (x - w / 2, y, z), (x + w / 2, y + sg * thick, z + h)
            org = np.array([x + w / 2 if sg > 0 else x - w / 2, y, z + h]); ev = np.array([-float(sg), 0, 0])

        def paint(P, n, t):
            front = n[:, ax] * sg > 0.9
            rgba = _tex(tex, ((P - org) @ ev) / w, (org[2] - P[:, 2]) / h)
            col = rgba[:, :3] * rgba[:, 3:4] + cp * (1 - rgba[:, 3:4])
            return np.where(front[:, None], col, cp)
        self.box(*lo, *hi, colour, bevel=0.006, paint=paint, ao=False)

    def _card_texture(self, w, h, title, tag, value, unit, note, series, accent, icon, paper, ink, stamp):
        ppu = 220
        TW, TH = int(w * ppu), int(h * ppu)
        im = Image.new('RGBA', (TW, TH), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        A = tuple(int(c * 255) for c in _c(accent)); K = tuple(int(c * 255) for c in _c(ink))
        soft = tuple(int(c * 255) for c in (_c(ink) * 0.5 + _c(paper) * 0.5))
        U = lambda v: int(v * ppu)
        m = U(0.16)
        d.rectangle([0, 0, U(0.06), TH], fill=A + (255,))                        # accent spine
        x0 = m + U(0.04)
        f_cn = load_font('cjk_sans', U(0.25)); f_tag = load_font('sans_bold', U(0.12))
        f_val = load_font('geometric', U(0.7)); f_unit = load_font('sans', U(0.22))
        f_note = load_font('cjk_sans', U(0.17))
        cy = m + U(0.15)
        ix = x0
        if icon:
            self._icon(d, icon, x0 + U(0.12), cy, U(0.12), A)
            ix = x0 + U(0.33)
        d.text((ix, cy), title, font=f_cn, fill=K + (255,), anchor='lm')
        xx = ix + d.textlength(title, font=f_cn) + U(0.1)
        for ch in tag:
            d.text((xx, cy + U(0.01)), ch, font=f_tag, fill=soft + (255,), anchor='lm')
            xx += d.textlength(ch, font=f_tag) + U(0.025)
        if stamp:
            d.text((TW - m, cy + U(0.01)), stamp, font=f_tag, fill=soft + (255,), anchor='rm')
        by = m + U(1.0)
        d.text((x0 - U(0.02), by), value, font=f_val, fill=K + (255,), anchor='ls')
        vw = d.textlength(value, font=f_val)
        d.text((x0 + vw + U(0.05), by), unit, font=f_unit, fill=soft + (255,), anchor='ls')
        vend = x0 + vw + U(0.05) + d.textlength(unit, font=f_unit)
        if note:
            d.text((x0, TH - m + U(0.02)), note, font=f_note, fill=soft + (255,), anchor='ls')
        if series is not None and len(series) > 1:
            s = np.asarray(series, np.float64)
            cx0, cx1 = max(int(TW * 0.58), int(vend + U(0.2))), TW - m
            cy0, cy1 = m + U(0.5), by - U(0.02)
            lo_, hi_ = s.min(), s.max(); rng_ = max(hi_ - lo_, 1e-6)
            pts = [(cx0 + (cx1 - cx0) * k / (len(s) - 1), cy1 - (cy1 - cy0) * (v - lo_) / rng_) for k, v in enumerate(s)]
            A2 = tuple(int(c * 255) for c in (_c(accent) * 0.22 + _c(paper) * 0.78))
            d.polygon(pts + [(cx1, cy1), (cx0, cy1)], fill=A2 + (255,))
            d.line([(cx0, cy1), (cx1, cy1)], fill=soft + (255,), width=max(1, U(0.01)))
            d.line(pts, fill=A + (255,), width=U(0.03), joint='curve')
            px, py = pts[-1]; rr = U(0.05)
            d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=A + (255,), outline=(255, 255, 255, 255), width=U(0.018))
        return np.asarray(im, np.float32) / 255

    @staticmethod
    def _icon(d, kind, cx, cy, r, col):
        c = col + (255,); lw = max(2, r // 5)
        if kind == 'wind':
            for dy, x0, x1 in ((-0.62, -1.0, 0.7), (0.0, -0.6, 1.1), (0.62, -1.0, 0.4)):
                y = cy + dy * r
                d.line([(cx + x0 * r, y), (cx + x1 * r, y)], fill=c, width=lw)
                for xe in (x0, x1):
                    d.ellipse([cx + xe * r - lw / 2, y - lw / 2, cx + xe * r + lw / 2, y + lw / 2], fill=c)
        elif kind == 'temp':
            d.rounded_rectangle([cx - 0.28 * r, cy - 1.1 * r, cx + 0.28 * r, cy + 0.4 * r], radius=int(0.28 * r), outline=c, width=lw)
            d.ellipse([cx - 0.55 * r, cy + 0.1 * r, cx + 0.55 * r, cy + 1.2 * r], fill=c)
        elif kind == 'rain':
            d.polygon([(cx, cy - 1.15 * r), (cx - 0.72 * r, cy + 0.15 * r), (cx + 0.72 * r, cy + 0.15 * r)], fill=c)
            d.ellipse([cx - 0.75 * r, cy - 0.45 * r, cx + 0.75 * r, cy + 1.05 * r], fill=c)
        elif kind == 'balloon':
            d.ellipse([cx - 0.7 * r, cy - 1.15 * r, cx + 0.7 * r, cy + 0.35 * r], fill=c)
            d.line([(cx, cy + 0.35 * r), (cx, cy + 1.05 * r)], fill=c, width=max(1, lw // 2))
            d.rectangle([cx - 0.22 * r, cy + 0.95 * r, cx + 0.22 * r, cy + 1.25 * r], fill=c)
        elif kind == 'sun':
            d.ellipse([cx - 0.5 * r, cy - 0.5 * r, cx + 0.5 * r, cy + 0.5 * r], fill=c)
            for k in range(8):
                a = k * np.pi / 4
                d.line([(cx + np.cos(a) * 0.72 * r, cy + np.sin(a) * 0.72 * r), (cx + np.cos(a) * 1.05 * r, cy + np.sin(a) * 1.05 * r)], fill=c, width=lw)

    # ------------------------------------------------------------ 2D type on top
    def text(self, s, x, y, size, colour=INK, font='cjk_sans', anchor='ls', spacing=0.0, alpha=1.0):
        """type set flat on the finished image (titles, captions); x, y in output pixels"""
        self.overlays.append(('text', s, x, y, size, colour, font, anchor, spacing, alpha))

    def rule(self, x0, y0, x1, y1, colour=INK, width=2, alpha=1.0):
        self.overlays.append(('rule', x0, y0, x1, y1, colour, width, alpha))

    def dot(self, x, y, r, colour=INK, alpha=1.0):
        self.overlays.append(('dot', x, y, r, colour, alpha))

    def compass(self, x, y, z=0.0, r=0.6, north=(0.0, 1.0), colour='#8a80b8', label='N', size=20):
        """a map compass lying flat in the iso ground plane at (x, y, z): a ring with four ticks, a two-tone north
        needle and its letter (drawn on top, like the titles)"""
        nx, ny = _unit([north[0], north[1], 0])[:2]; ex, ey = ny, -nx
        P = lambda a, b: self.iso(x + a, y + b, z)
        self.overlays.append(('poly', [P(r * np.cos(t), r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 97)], colour, 2, 0.75, False))
        for k in range(4):
            c, s_ = np.cos(k * np.pi / 2), np.sin(k * np.pi / 2)
            dx, dy = nx * c - ex * s_, ny * c - ey * s_
            self.overlays.append(('poly', [P(dx * r * 0.84, dy * r * 0.84), P(dx * r, dy * r)], colour, 2, 0.75, False))
        tip, tail = P(nx * r * 0.78, ny * r * 0.78), P(-nx * r * 0.78, -ny * r * 0.78)
        left, right, mid = P(ex * r * 0.15, ey * r * 0.15), P(-ex * r * 0.15, -ey * r * 0.15), P(0, 0)
        self.overlays.append(('poly', [tip, left, mid, right], colour, 0, 0.95, True))
        self.overlays.append(('poly', [tail, left, mid, right], colour, 0, 0.3, True))
        lx, ly = P(nx * r * 1.3, ny * r * 1.3)
        self.text(label, lx, ly, size, colour, font='sans_bold', anchor='mm')

    def _draw_overlays(self, img):
        if not self.overlays: return img
        lay = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for o in self.overlays:
            if o[0] == 'text':
                _, s, x, y, size, colour, font, anchor, spacing, alpha = o
                f = load_font(font, size); c = tuple(int(v * 255) for v in _c(colour)) + (int(alpha * 255),)
                if not spacing:
                    d.text((x, y), s, font=f, fill=c, anchor=anchor)
                else:
                    adv = [f.getlength(ch) + spacing for ch in s]; tot = sum(adv) - spacing
                    xx = x - tot * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
                    for ch, a in zip(s, adv):
                        d.text((xx, y), ch, font=f, fill=c, anchor='l' + anchor[1]); xx += a
            elif o[0] == 'rule':
                _, x0, y0, x1, y1, colour, width, alpha = o
                d.line([(x0, y0), (x1, y1)], fill=tuple(int(v * 255) for v in _c(colour)) + (int(alpha * 255),), width=width)
            elif o[0] == 'poly':
                _, pts, colour, width, alpha, fill = o
                c = tuple(int(v * 255) for v in _c(colour)) + (int(alpha * 255),)
                if fill: d.polygon([tuple(p) for p in pts], fill=c)
                else: d.line([tuple(p) for p in pts], fill=c, width=width, joint='curve')
            elif o[0] == 'dot':
                _, x, y, r, colour, alpha = o
                d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * 255) for v in _c(colour)) + (int(alpha * 255),))
        return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

    # ------------------------------------------------------------ lighting
    def _maps(self):
        tc = self.tcam
        Hm = np.where(np.isfinite(self.tdep), (tc.C[2] - self.tdep), self.floor).astype(np.float32)
        ao = []
        for r, k, w in ((0.05, 0.07, 0.40), (0.16, 0.22, 0.35), (0.5, 0.6, 0.25)):
            ao.append((blur(Hm, r * tc.S), r, k, w))
        occ_top = blur((Hm > self.floor + 0.3).astype(np.float32), 0.7 * tc.S)
        h0 = Hm
        hb = np.minimum(np.where(np.isfinite(self.tbot), (tc.C[2] - self.tbot), self.floor).astype(np.float32), h0)
        k = 4
        lo = np.isfinite(self.ldep).astype(np.float32)
        Hl, Wl = lo.shape
        small = np.asarray(Image.fromarray(lo, 'F').resize((max(2, Wl // k), max(2, Hl // k)), Image.BOX), np.float32)
        occ_l = blur(small, 0.55 * self.lcam.S / k)
        return {'ao': ao, 'occ_top': occ_top, 'occ_l': occ_l, 'occ_k': k, 'h0': h0, 'hb': hb}

    def _pcss(self, P, n, ndl, jit):
        lc = self.lcam; D = self.ldep; Hh, Ww = D.shape
        j, i, d = lc.project(P + n * 0.02)
        j = j.astype(np.float32); i = i.astype(np.float32); d = d.astype(np.float32)
        inv = 1.0 / np.maximum(ndl, 0.25)
        gx = ((n @ lc.r) * inv).astype(np.float32); gy = ((n @ lc.u) * inv).astype(np.float32)
        S = np.float32(lc.S); bias = np.float32(0.012)
        c, s = np.cos(jit).astype(np.float32), np.sin(jit).astype(np.float32)
        Rb = np.float32(self.pen[1])

        def taps(K, R):
            k = np.arange(K) + 0.5
            rr = np.sqrt(k / K); th = k * 2.39996323
            for px, py in zip(rr * np.cos(th), rr * np.sin(th)):
                ox = (px * c - py * s) * R; oy = (px * s + py * c) * R
                jj = np.clip(np.rint(j + ox * S), 0, Ww - 1).astype(np.int32)
                ii = np.clip(np.rint(i - oy * S), 0, Hh - 1).astype(np.int32)
                yield D[ii, jj], d + ox * gx + oy * gy
        sd = np.zeros_like(d); cnt = np.zeros_like(d)
        for z, ref in taps(14, Rb):
            blk = z < ref - bias
            sd += np.where(blk, ref - z, 0); cnt += blk
        has = cnt > 0
        dist = sd / np.maximum(cnt, 1)
        w = np.clip(dist * np.float32(self.soft) + np.float32(self.pen[0]), self.pen[0], self.pen[1]).astype(np.float32)
        vis = np.zeros_like(d)
        K = 28
        for z, ref in taps(K, w):
            vis += z >= ref - bias
        vis /= K
        return np.where(has, vis, 1.0).astype(np.float32)

    def _ao(self, P, n, maps):
        """ambient occlusion. Upward faces: how far the blurred surroundings rise above the point (three radii).
        Side and downward faces: the horizon seen along the normal (and 40 deg either side) on the raw height
        map -- a wall is not darkened by its own building, only by what stands in front of it -- plus a
        small crease where it meets the ground."""
        tc = self.tcam
        z = P[:, 2]

        def hmap(M, x, y):
            return _bilerp(M, (y - tc.C[1]) * tc.S + tc.H / 2 - 0.5, (x - tc.C[0]) * tc.S + tc.W / 2 - 0.5)

        def hnear(M, x, y):                      # column extents must not be interpolated across an edge
            i = np.clip(np.rint((y - tc.C[1]) * tc.S + tc.H / 2 - 0.5), 0, tc.H - 1).astype(np.int32)
            j = np.clip(np.rint((x - tc.C[0]) * tc.S + tc.W / 2 - 0.5), 0, tc.W - 1).astype(np.int32)
            return M[i, j]
        top = np.zeros(len(P), np.float32)
        for Hr, r, k, w in maps['ao']:
            top += w * np.clip((hmap(Hr, P[:, 0] + n[:, 0] * r * 0.5, P[:, 1] + n[:, 1] * r * 0.5) - z) / k, 0, 1)
        wt = smoothstep(0.35, 0.75, n[:, 2]).astype(np.float32)
        side = np.zeros(len(P), np.float32)
        need = wt < 0.999
        if need.any():
            Ps, ns = P[need], n[need]; zs = z[need]
            h = np.hypot(ns[:, 0], ns[:, 1]) + 1e-6
            dx, dy = ns[:, 0] / h, ns[:, 1] / h
            H0, HB = maps['h0'], maps['hb']
            occ = np.zeros(len(Ps), np.float32)
            for ang in (-0.7, 0.0, 0.7):
                ca, sa = np.cos(ang), np.sin(ang)
                ux, uy = dx * ca - dy * sa, dx * sa + dy * ca
                best = np.zeros(len(Ps), np.float32)
                for dd in (0.04, 0.09, 0.18, 0.35, 0.7):
                    x, y = Ps[:, 0] + ux * dd, Ps[:, 1] + uy * dd
                    t1 = np.maximum(hnear(H0, x, y) - zs, 0) / dd; t0 = np.maximum(hnear(HB, x, y) - zs, 0) / dd
                    band = t1 / np.sqrt(1 + t1 * t1) - t0 / np.sqrt(1 + t0 * t0)   # sky band this column hides
                    np.maximum(best, band, out=best)
                occ += best * (0.4 if ang == 0.0 else 0.3)
            gx, gy = Ps[:, 0] + dx * 0.05, Ps[:, 1] + dy * 0.05
            g = hnear(H0, gx, gy)
            under = hnear(HB, gx, gy) > zs - 0.02                       # a floating slab (eave) there: no crease
            crease = np.where(under, 0, np.clip(1 - np.abs(zs - g) / 0.14, 0, 1) ** 2 * 0.35)
            side[need] = np.clip(occ * 0.95 + crease, 0, 1)
        return np.clip(wt * top + (1 - wt) * side, 0, 1)

    def _colour(self, P, n, alb, mat, vis, ao):
        L = self.L.astype(np.float32)
        ndl = n @ L
        nz = n[:, 2:3]
        amb = np.where(nz >= 0, self.hor_c + (self.sky_c - self.hor_c) * nz, self.hor_c + (self.gnd_c - self.hor_c) * (-nz))
        soft = mat == SOFT
        nd = np.where(soft, (ndl + 0.35) / 1.35, ndl)
        direct = np.clip(nd, 0, 1) * vis
        aok = np.where(mat == WATER, 0.5, 1.0)[:, None] * ao[:, None]
        light = amb * (1 - 0.55 * aok) + self.sun_c * direct[:, None]
        light = light * (1 - 0.14 * aok)
        col = alb * light
        g = mat == GLASS
        if g.any():
            vdir = -self.cam.v.astype(np.float32)
            fr = 0.06 + 0.2 * (1 - np.clip(n[g] @ vdir, 0, 1)) ** 3
            col[g] = col[g] * (1 - fr[:, None]) + self.sky_c * 1.12 * fr[:, None]
        w = mat == WATER
        if w.any():                                    # water lets light through: its walls glow a little
            wall = (np.abs(n[w, 2]) < 0.5)[:, None]
            col[w] = np.where(wall, col[w] * 0.7 + alb[w] * 0.34, col[w])
        gl = (mat == GLOSS)
        if gl.any():
            Hv = _unit(self.L - self.cam.v).astype(np.float32)
            sp = np.clip(n[gl] @ Hv, 0, 1) ** 40 * vis[gl]
            col[gl] = col[gl] + (0.5 * sp)[:, None]
        c = mat == CARD
        if c.any():
            col[c] = alb[c] * (0.8 + 0.2 * light[c])
        return col

    def _vis_blur(self, V, D, radius):
        """depth-aware separable blur of the shadow term: removes the grain of wide penumbras, keeps edges"""
        fin = np.isfinite(D)
        Dz = np.where(fin, D, 1e6).astype(np.float32)
        for ax in (0, 1):
            num = np.zeros_like(V); den = np.zeros_like(V)
            for o in range(-radius, radius + 1):
                Vs = np.roll(V, o, axis=ax); Ds = np.roll(Dz, o, axis=ax)
                wgt = np.exp(-((Ds - Dz) / 0.04) ** 2) * np.float32(np.exp(-(o / (0.6 * radius + 0.5)) ** 2))
                num += wgt * Vs; den += wgt
            V = num / np.maximum(den, 1e-6)
        return V

    def shade(self, k=1):
        """light the current G-buffer; k = stride in supersampled pixels (1 = final quality)"""
        maps = self._maps()
        cam, lc, tc = self.cam, self.lcam, self.tcam
        rows = np.arange(k // 2, self.Hs, k); cols = np.arange(k // 2, self.Ws, k)
        if k == 1:
            DEP, NRM, ALB, MAT = self.dep, self.nrm, self.alb, self.mat
        else:
            ix = np.ix_(rows, cols)
            DEP, NRM, ALB, MAT = self.dep[ix], self.nrm[ix], self.alb[ix], self.mat[ix]
        Hk, Wk = DEP.shape
        acols = cam.cols(cols)
        VIS = np.ones((Hk, Wk), np.float32); AO = np.zeros((Hk, Wk), np.float32)
        step = max(1, 500000 // Wk)
        L = self.L.astype(np.float32)
        # ---- pass 1: sun visibility (soft shadows) and occlusion
        for s0 in range(0, Hk, step):
            sl = slice(s0, min(Hk, s0 + step))
            dep = DEP[sl]
            ii, jj = np.nonzero(np.isfinite(dep))
            if not len(ii): continue
            b = cam.rows(rows[sl])
            P = cam.points(acols[0, jj].astype(np.float64), b[ii, 0].astype(np.float64), dep[ii, jj]).astype(np.float32)
            n = NRM[sl][ii, jj].astype(np.float32); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-6
            ndl = n @ L
            vis = np.zeros(len(P), np.float32)
            lit = ndl > -0.3
            if lit.any():
                gi = rows[sl][ii][lit].astype(np.float32); gj = cols[jj][lit].astype(np.float32)
                jit = (2 * np.pi * np.mod(52.9829189 * np.mod(0.06711056 * gj + 0.00583715 * gi, 1.0), 1.0)).astype(np.float32)
                vis[lit] = self._pcss(P[lit], n[lit], np.maximum(ndl[lit], 0.05), jit)
            VIS[sl][ii, jj] = vis
            AO[sl][ii, jj] = self._ao(P, n, maps)
        VIS = self._vis_blur(VIS, DEP, 3 if k == 1 else 1)
        # ---- pass 2: colour
        out = np.empty((Hk, Wk, 3), np.float32)
        top, bottom, glow = (_c(c) for c in self.bg)
        gx, gy = self.iso(*self.glow_centre)
        gx *= self.ss; gy *= self.ss
        for s0 in range(0, Hk, step):
            sl = slice(s0, min(Hk, s0 + step))
            rr = rows[sl]; dep = DEP[sl]; b = cam.rows(rr)
            blk = np.empty((len(rr), Wk, 3), np.float32)
            ty = (rr.astype(np.float32) / self.Hs)[:, None, None]
            bgc = top * (1 - ty) + bottom * ty
            X, Y = np.meshgrid(cols.astype(np.float32), rr.astype(np.float32))
            gd = ((X - gx) / (0.55 * self.Ws)) ** 2 + ((Y - gy) / (0.45 * self.Hs)) ** 2
            bgc = bgc + (glow - bgc) * (np.exp(-gd * 2.2) * 0.8)[..., None]
            miss = ~np.isfinite(dep)
            if miss.any():
                ii, jj = np.nonzero(miss)
                Q = cam.points(acols[0, jj].astype(np.float64), b[ii, 0].astype(np.float64), np.zeros(len(ii)))
                t = (self.floor - Q[:, 2]) / cam.v[2]
                Pf = Q + t[:, None] * cam.v[None]
                lj, li, _ = lc.project(Pf)
                kk = maps['occ_k']
                shl = _bilerp(maps['occ_l'], (li + 0.5) / kk - 0.5, (lj + 0.5) / kk - 0.5)
                tj = (Pf[:, 0] - tc.C[0]) * tc.S + tc.W / 2 - 0.5; ti = (Pf[:, 1] - tc.C[1]) * tc.S + tc.H / 2 - 0.5
                inside = (tj > 0) & (tj < tc.W - 1) & (ti > 0) & (ti < tc.H - 1)
                aof = np.where(inside, _bilerp(maps['occ_top'], ti, tj), 0)
                tint = np.array([0.78, 0.76, 0.93], np.float32)
                amt = np.clip(0.55 * shl + 0.45 * aof, 0, 1)[:, None] * 0.55
                blk[ii, jj] = bgc[ii, jj] * (1 - amt * (1 - tint))
            ii, jj = np.nonzero(~miss)
            if len(ii):
                P = cam.points(acols[0, jj].astype(np.float64), b[ii, 0].astype(np.float64), dep[ii, jj]).astype(np.float32)
                n = NRM[sl][ii, jj].astype(np.float32); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-6
                blk[ii, jj] = self._colour(P, n, ALB[sl][ii, jj].astype(np.float32), MAT[sl][ii, jj],
                                           VIS[sl][ii, jj], AO[sl][ii, jj])
            out[sl] = blk
        out = np.where(out > 0.9, 0.9 + 0.1 * np.tanh((out - 0.9) / 0.1), out)
        return np.clip(out, 0, 1)

    # ------------------------------------------------------------ output
    def composite(self, preview=False):
        if preview:
            img = self.shade(k=2 * self.ss)
            im = Image.fromarray((img * 255 + 0.5).astype(np.uint8)).resize((self.W, self.H), Image.BILINEAR)
        else:
            img = self.shade(k=1)
            s = self.ss
            img = img[:self.H * s, :self.W * s].reshape(self.H, s, self.W, s, 3).mean((1, 3))
            im = Image.fromarray((img * 255 + 0.5).astype(np.uint8))
        return self._draw_overlays(im)

    def stage(self, name):
        if self.record: self.stages.append((name, self.composite(preview=True)))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
