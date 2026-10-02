"""patch — machine-embroidered patches sewn onto denim: tatami fill, satin stitch, merrowed and hot-cut edges,
running / sashiko stitch, French knots, a needle and thread (numpy + Pillow only).

Model:
  denim     3/1 right-hand twill. Indigo warp yarns float over three white weft picks and dive under one, and the
            float steps one pick every row, so the blue wales climb to the right and a pale weft fleck shows at every
            fourth crossing. Warp yarns are ring-dyed and slubby: dye depth and thickness wander along every yarn
            (faint vertical streaks), and the high points are worn toward the white core. Rendered at 2x, averaged.
  seam      a felled seam: the panel above is folded over the one below and held by two rows of lockstitch in
            tobacco thread; the folded ridge is worn pale ("roping") and throws a little shadow.
  thread    polyester embroidery thread, lit as a round glossy fibre: a cylinder across the stitch that dives into
            the cloth at both needle holes (so every needle hole is a small dark dimple), with an anisotropic
            Kajiya-Kay highlight that depends on the stitch *direction*. The same colour sewn at two angles catches
            the light differently, which is exactly why a real patch reads as stitched and not printed.
  digitizer every filled shape is stitched the way an embroidery machine does it: parallel rows at a chosen angle
            (scan lines through the shape), and each row is cut into stitches.
    tatami   short stitches (`length`, about 3 mm) whose needle holes shift a fraction of a stitch every row ->
             the fine brick / diagonal texture of a background fill;
    satin    one long float across the whole row -> the smooth glossy columns of letters, peaks, flames.
             Floats longer than `maxlen` are split (split satin) as a digitizer would.
            The rows end where the shape ends, so the edge of every fill is made of stitch ends; later fills lie
            on top of earlier ones and cast a thin shadow; each fill is slightly padded (its edges catch light).
  edges     merrow: an overlock wraps thread round and round the cut edge -> a raised rolled cord of slanted wraps
            around round, oval and rocker patches. Hot-cut: a wide satin column laid along the outline of a
            die-cut shape, its stitches square to the edge. Both are evaluated at 4 sub-pixel positions (2-3 px wraps
            would beat against the pixel grid), and where stitches crowd below ~2 px in a tight corner their ridges
            fade into a smooth fan instead of aliasing into a starburst.
  attach    `blank()` lays the cut twill blank on the denim (a soft shadow, the patch's thickness); `whip()` sews a
            merrowed patch on by hand with slanted stitches over the edge; `thread()` and `needle()` leave the
            needle lying on the cloth with the thread still running back to the last stitch.

    from patch import Patch
    p = Patch(1920, 1080, seed=1)
    p.denim()
    b = p.blank(p.circle_pts(960, 540, 200), '#20294a')                       # a round twill blank
    p.fill(p.circle(960, 540, 200), '#20294a', angle=30)                       # tatami background
    p.fill(p.poly([(820, 640), (960, 420), (1100, 640)]), '#8aa1c4', angle=60) # a peak
    p.fill(p.poly([(920, 485), (960, 420), (1000, 485)]), '#f2efe8', angle=-35, kind='satin')
    p.arc_text('HIGH CAMP', 960, 540, 170, size=40, colour='#f3e6c4')
    p.merrow(b, '#d79b32')                                                   # rolled edge
    p.save('out.jpg')
Coordinates are output pixels, y down; angles in degrees, counter-clockwise (0 = stitches run left-right).
Masks are float arrays (H, W) in 0..1, as in stitch.py: combine them with *, np.maximum, 1 - m.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from core import blur, noise2d, smoothstep, polygon_mask, shift, load_font, text_mask, spline, fbm1d


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _h01(*keys):
    """deterministic per-stitch random numbers in [0, 1) from integer keys (row, stitch, salt ...)"""
    arrs = [np.asarray(k).astype(np.int64).astype(np.uint64) for k in keys]
    out = np.zeros(np.broadcast(*arrs).shape, np.uint64) + np.uint64(0x9E3779B97F4A7C15)
    with np.errstate(over='ignore'):
        for k in arrs:
            out = out ^ (k + np.uint64(0x9E3779B97F4A7C15) + (out << np.uint64(6)) + (out >> np.uint64(2)))
            out = out * np.uint64(0xBF58476D1CE4E5B9)
            out = out ^ (out >> np.uint64(31))
    return ((out >> np.uint64(40)).astype(np.float64) / float(1 << 24)).astype(np.float32)


def _resample(P, step, closed):
    P = np.asarray(P, np.float32)
    if closed: P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    n = max(3, int(cum[-1] / step) + 1)
    t = np.linspace(0, cum[-1], n, endpoint=not closed)
    return np.stack([np.interp(t, cum, P[:, 0]), np.interp(t, cum, P[:, 1])], 1).astype(np.float32)


def smooth_closed(pts, iters=3):
    """Chaikin corner cutting on a closed outline: rounds every corner a little (die-cut patches have no sharp corners)"""
    P = np.asarray(pts, np.float32)
    for _ in range(iters):
        Q = np.roll(P, -1, 0)
        P = np.stack([0.75 * P + 0.25 * Q, 0.25 * P + 0.75 * Q], 1).reshape(-1, 2)
    return P


class Blank:
    """a cut patch blank: its outline (closed polyline, px) and coverage mask"""
    def __init__(self, pts, mask, colour):
        self.pts, self.mask, self.colour = pts, mask, colour


class Patch:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.5, -0.62, 0.6)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        L = np.asarray(light, np.float32)
        self.L = L / np.linalg.norm(L)
        Hv = self.L + np.array([0, 0, 1], np.float32)
        self.Hv = Hv / np.linalg.norm(Hv)
        self.img = np.full((H, W, 3), 0.45, np.float32)
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================ masks and outlines
    def circle(self, cx, cy, r):
        return polygon_mask(self.H, self.W, self.circle_pts(cx, cy, r), ss=2)

    def ring(self, cx, cy, r0, r1):
        return self.circle(cx, cy, r1) * (1 - self.circle(cx, cy, r0))

    def poly(self, pts, smooth=0):
        P = smooth_closed(pts, smooth) if smooth else pts
        return polygon_mask(self.H, self.W, P, ss=2)

    @staticmethod
    def circle_pts(cx, cy, r, step=2.0):
        n = max(24, int(2 * np.pi * r / step))
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        return np.stack([cx + r * np.cos(t), cy - r * np.sin(t)], 1).astype(np.float32)

    @staticmethod
    def arch_pts(cx, top, w, h, corner=26.0):
        """die-cut 'tombstone': a half-circle top on straight sides, rounded bottom corners"""
        r = w / 2; cyc = top + r; bot = top + h
        t = np.linspace(0, np.pi, 90)
        arc = np.stack([cx + r * np.cos(t), cyc - r * np.sin(t)], 1)          # right -> left over the top
        pts = [*arc, (cx - r, bot - corner)]
        t = np.linspace(np.pi, 1.5 * np.pi, 14)
        pts += list(np.stack([cx - r + corner + corner * np.cos(t), bot - corner - corner * np.sin(t)], 1))
        t = np.linspace(1.5 * np.pi, 2 * np.pi, 14)
        pts += list(np.stack([cx + r - corner + corner * np.cos(t), bot - corner - corner * np.sin(t)], 1))
        return _resample(np.array(pts, np.float32), 2.0, True)

    @staticmethod
    def rocker_pts(cx, cy, r0, r1, span=90.0, centre=90.0, corner=2):
        """a 'rocker': the curved banner patch that sits above (centre=90) or below (270) a round patch"""
        a0, a1 = np.deg2rad(centre + span / 2), np.deg2rad(centre - span / 2)
        t = np.linspace(a0, a1, 120)
        outer = np.stack([cx + r1 * np.cos(t), cy - r1 * np.sin(t)], 1)
        inner = np.stack([cx + r0 * np.cos(t[::-1]), cy - r0 * np.sin(t[::-1])], 1)
        P = np.vstack([outer, inner])
        P = _resample(P, 6.0, True)
        return _resample(smooth_closed(P, corner), 2.0, True)

    def text_mask(self, s, x, y, size, font='rounded', anchor='mm', spacing=0.0, rot=0.0):
        return text_mask(self.H, self.W, s, load_font(font, size), (x, y), anchor, spacing, rot)

    # ================================================================ the denim
    def denim(self, colour='#3b5d96', weft='#b9c2cf', warp_px=1.5, pick_px=2.5, fade=0.6, worn='#a3b9da'):
        """3/1 right-hand twill, rendered at 2x in bands and averaged down. Warp yarns (indigo) are packed tighter
        than weft picks (ecru), so the wales climb at about 60 degrees, as on real jeans."""
        ss = 2
        cw, ch = warp_px * ss, pick_px * ss
        W2 = self.W * ss
        rng = np.random.default_rng(self._seed())
        ncol = int(W2 / cw) + 3
        nrow = int(self.H * ss / ch) + 3
        kn = 7                                                     # slub knots every 7 picks along each warp yarn
        G1 = rng.random((nrow // kn + 3, ncol)).astype(np.float32)
        G2 = rng.random((nrow // 2 + 3, ncol)).astype(np.float32)
        dye = rng.normal(0, 1, ncol).astype(np.float32)            # dye depth differs yarn to yarn
        pick = rng.normal(0, 1, nrow).astype(np.float32)           # and weft pick to pick
        cellr = rng.random((nrow, ncol)).astype(np.float32)        # how much of each weft fleck peeks out
        wear = noise2d(self.H // 4, self.W // 4, 60, 4, self._seed())
        wear = np.asarray(Image.fromarray(wear).resize((self.W, self.H), Image.BICUBIC), np.float32)
        fold = noise2d(self.H // 4, self.W // 4, 160, 3, self._seed())
        fold = np.asarray(Image.fromarray(fold).resize((self.W, self.H), Image.BICUBIC), np.float32)
        col, wcol, wn = _c(colour), _c(weft), _c(worn)
        L = self.L
        out = np.empty((self.H, self.W, 3), np.float32)
        band = 120
        for yb in range(0, self.H, band):
            ye = min(self.H, yb + band)
            yy, xx = np.mgrid[yb * ss:ye * ss, 0:W2].astype(np.float32)
            yy += 0.5; xx += 0.5
            cx = (xx / cw).astype(np.int32); cy = (yy / ch).astype(np.int32)
            fx = xx / cw - cx; fy = yy / ch - cy
            k = (cx + cy) % 4
            isw = k == 0                                            # weft on top
            tw = ((k - 1) + fy) / 3.0                               # position along the 3-pick warp float
            across = np.where(isw, (fy - 0.5) * 2, (fx - 0.5) * 2)
            along = np.where(isw, fx, tw)
            nzc = np.sqrt(np.clip(1 - 0.8 * across ** 2, 0.05, 1))
            end = np.clip(np.sin(np.pi * np.clip(along, 0, 1)), 0, 1) ** np.where(isw, 1.2, 0.35)
            side = np.where(isw, across * L[1], across * L[0]) / np.hypot(L[0], L[1])
            shade = 0.6 + 0.32 * nzc * end - 0.1 * side
            # slubs: dye and thickness wander along every warp yarn
            fyk = yy / (ch * kn); i0 = np.minimum(fyk.astype(np.int32), G1.shape[0] - 2); w = fyk - i0
            sl1 = G1[i0, cx] * (1 - w) + G1[i0 + 1, cx] * w
            fyk = yy / (ch * 2); i0 = np.minimum(fyk.astype(np.int32), G2.shape[0] - 2); w = fyk - i0
            sl2 = G2[i0, cx] * (1 - w) + G2[i0 + 1, cx] * w
            depth = 1 + 0.06 * dye[cx] + 0.2 * (sl1 - 0.5) + 0.12 * (sl2 - 0.5)
            twist = 0.05 * np.sin(2 * np.pi * (fy * 1.6 + fx * 1.1))
            wr = wear[np.minimum(yy.astype(np.int32) // ss, self.H - 1), np.minimum(xx.astype(np.int32) // ss, self.W - 1)]
            top = np.clip(nzc * end, 0, 1) ** 2
            ring = np.clip(fade * (0.25 + 0.75 * smoothstep(0.3, 0.9, wr)) * top * np.clip(1.3 - depth, 0, 1) * 0.8, 0, 0.8)
            warp = col * (depth * (shade + twist))[..., None]
            warp = warp * (1 - ring[..., None]) + wn * shade[..., None] * ring[..., None]
            peek = cellr[cy, cx]
            wv = (0.45 + 0.55 * nzc * end) * (0.55 + 0.6 * peek) * (1 + 0.04 * pick[cy])
            wf = wcol * wv[..., None]
            wf = wf * 0.8 + col * 0.2 * shade[..., None]
            px = np.where(isw[..., None], wf, warp)
            out[yb:ye] = px.reshape(ye - yb, ss, self.W, ss, 3).mean((1, 3))
        gy, gx = np.gradient(fold * 40)
        lightf = 1 + 0.5 * np.clip(-(gx * L[0] + gy * L[1]), -0.2, 0.2)
        YY, XX = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        grad = 1.06 - 0.12 * (XX / self.W * 0.6 + YY / self.H * 0.4)
        self.img = out * (lightf * grad)[..., None]
        self.denim_colour = col

    def seam(self, pts, thread='#d49a35', rows=(10.0, 25.0), stitch=9.0, gap=2.6, fold=34.0, wear=0.8):
        """a felled seam along `pts` (left to right): the panel above is folded over the one below, two rows of
        lockstitch hold it, and the folded ridge is worn pale"""
        P = spline(pts, 40)
        g = self._pparam(P, False, fold + 16)
        if g is None: return
        ys, xs, s, d, tx, ty, win = g['ys'], g['xs'], g['s'], g['d'], g['tx'], g['ty'], g['win']
        y0, y1, x0, x1 = win
        nx, ny = -ty, tx                                            # d > 0 below the line
        # height across the seam: fold ridge, double-layer plateau, then the buried edge of the allowance
        ridge = np.exp(-((d + 1.5) / 3.2) ** 2) * 2.6
        plate = smoothstep(-2, 1, d) * (1 - smoothstep(fold - 1, fold + 4, d)) * 2.0
        pull = sum(np.exp(-((d - r) / 2.2) ** 2) for r in rows) * 0.9
        h = ridge + plate - pull
        # slope by finite difference of the same profile
        e = 0.5
        def prof(dd):
            return (np.exp(-((dd + 1.5) / 3.2) ** 2) * 2.6 + smoothstep(-2, 1, dd) * (1 - smoothstep(fold - 1, fold + 4, dd)) * 2.0
                    - sum(np.exp(-((dd - r) / 2.2) ** 2) for r in rows) * 0.9)
        dh = (prof(d + e) - prof(d - e)) / (2 * e)
        lit = 1 - 0.35 * dh * (nx * self.L[0] + ny * self.L[1]) / np.hypot(self.L[0], self.L[1])
        groove = 1 - 0.28 * np.exp(-((d - 0.8) / 1.6) ** 2) - 0.12 * np.exp(-((d - fold - 3) / 2.5) ** 2)
        n1 = fbm1d(int(s.max()) + 64, 60, 4, self._seed())
        rope = smoothstep(0.05, 0.6, n1[np.clip(s.astype(np.int64), 0, len(n1) - 1)])
        worn = wear * np.clip(ridge / 2.6, 0, 1) * (0.35 + 0.65 * rope)
        sub = self.img[y0:y1, x0:x1]
        cur = sub[ys, xs]
        cur = cur * (lit * groove)[:, None]
        cur = cur * (1 - 0.55 * worn[:, None]) + _c('#a9bfdc') * (0.95 * worn)[:, None]
        sub[ys, xs] = cur
        # two rows of topstitching
        tg = np.gradient(P, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
        for i, r in enumerate(rows):
            self.run(P + nrm * r, thread, stitch=stitch, gap=gap, width=3.1, smooth=False, sheen=0.55,
                     twist=0.6, start=i * 3.0, shadow=0.45)

    # ================================================================ blanks
    def blank(self, pts, colour='#ece2c9', shadow=0.5):
        """lay a cut twill blank on the denim; returns a Blank for the edge and whip stitches"""
        P = np.asarray(pts, np.float32)
        m = polygon_mask(self.H, self.W, P, ss=2)
        x0, y0, x1, y1 = self._bbox(m, 16)
        sub = self.img[y0:y1, x0:x1]; mm = m[y0:y1, x0:x1]
        sh = blur(shift(mm, 4, 6), 5.0)
        sub *= (1 - shadow * sh * (1 - mm))[..., None]
        sub *= (1 - 0.25 * blur(mm, 1.5) * (1 - mm))[..., None]
        YY, XX = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        tw = 0.94 + 0.06 * (((XX + YY) // 2) % 2) + 0.03 * np.sin((XX - YY) * 0.9)
        cut = smoothstep(0.0, 3.0, blur(mm, 1.2) * 6)               # the cut edge frays a hair darker
        face = _c(colour) * (tw * (0.9 + 0.1 * cut))[..., None]
        sub[:] = sub * (1 - mm[..., None]) + face * mm[..., None]
        return Blank(P, m, colour)

    # ================================================================ lighting of a thread
    def _thread_rgb(self, col, v, g, d, p, ao=1.0, rnd=0.0, sheen=1.0, gloss=14.0, twist=0.0, along=None, width=3.0):
        """colour of a round glossy thread. v: -1..1 across the thread; g: slope dz/ds along it;
        d / p: unit vectors (x, y) along / across the thread (scalars or arrays)"""
        L, Hv = self.L, self.Hv
        nzc = np.sqrt(np.clip(1 - 0.9 * v * v, 0.04, 1))
        nx = p[0] * v - g * nzc * d[0]
        ny = p[1] * v - g * nzc * d[1]
        nz = nzc
        nn = np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / nn, ny / nn, nz / nn
        diff = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        tn = np.sqrt(1 + g * g)
        TH = (d[0] * Hv[0] + d[1] * Hv[1] + g * Hv[2]) / tn
        aniso = np.sqrt(np.clip(1 - TH * TH, 0, 1)) ** gloss         # Kajiya-Kay: sheen depends on stitch direction
        nh = np.clip(nx * Hv[0] + ny * Hv[1] + nz * Hv[2], 0, 1)
        spec = sheen * (0.42 * aniso * nh ** 6 + 0.2 * nh ** 40)
        shade = (0.28 + 0.98 * diff) * ao * (1 + rnd)
        if twist and along is not None:
            shade = shade * (1 + 0.07 * twist * np.sin(2 * np.pi * (along + v * width * 0.7) / (width * 1.3)) * nzc)
        col = _c(col)
        rgb = col * shade[..., None] + (spec * 0.62)[..., None] * (0.5 + 0.5 * col)
        return rgb

    def _put(self, win, a, rgb, shadow=0.35, off=(1.4, 1.9), soft=1.3):
        y0, y1, x0, x1 = win
        sub = self.img[y0:y1, x0:x1]
        if shadow:
            sh = blur(shift(a, off[0], off[1]), soft)
            sub *= (1 - shadow * sh * (1 - a))[..., None]
        sub[:] = sub * (1 - a[..., None]) + np.clip(rgb, 0, 1.2) * a[..., None]

    def _bbox(self, m, pad):
        ys, xs = np.nonzero(m > 0.01)
        if len(ys) == 0: return None
        return (max(0, xs.min() - pad), max(0, ys.min() - pad), min(self.W, xs.max() + pad + 1), min(self.H, ys.max() + pad + 1))

    # ================================================================ the digitizer: rows of stitches through a shape
    def _scan(self, m, x0, y0, angle, pitch, length=None, stagger=0.3, maxlen=None, jitter=0.6, salt=0):
        h, w = m.shape
        th = np.deg2rad(angle)
        dx, dy = float(np.cos(th)), float(-np.sin(th))              # along the stitches
        px, py = -dy, dx                                            # across the rows
        yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w].astype(np.float32)
        A = xx * dx + yy * dy
        C = xx * px + yy * py
        rowf = C / pitch
        rfl = np.floor(rowf)
        v = (rowf - rfl) * 2 - 1
        r0 = int(rfl.min()); ri = (rfl - r0).astype(np.int32); nr = int(ri.max()) + 1
        a0 = float(np.floor(A.min())) - 1; n = int(np.ceil(A.max() - a0)) + 2
        ks = a0 + np.arange(n, dtype=np.float32)
        cs = (r0 + np.arange(nr, dtype=np.float32) + 0.5) * pitch
        SX = ks[None, :] * dx + cs[:, None] * px - x0
        SY = ks[None, :] * dy + cs[:, None] * py - y0
        ix = np.rint(SX).astype(np.int32); iy = np.rint(SY).astype(np.int32)
        ok = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
        samp = np.zeros((nr, n), bool)
        samp[ok] = m[iy[ok], ix[ok]] > 0.5
        prev = np.zeros_like(samp); prev[:, 1:] = samp[:, :-1]
        nxt = np.zeros_like(samp); nxt[:, :-1] = samp[:, 1:]
        st = samp & ~prev; en = samp & ~nxt
        cum = np.cumsum(st.ravel()).reshape(nr, n)
        nrun = int(cum[-1, -1])
        if nrun == 0: return None
        fs = np.flatnonzero(st); fe = np.flatnonzero(en)
        RS = np.zeros(nrun + 2, np.float32); RE = np.zeros(nrun + 2, np.float32); RR = np.full(nrun + 2, -1, np.int64)
        RS[1:nrun + 1] = fs % n; RE[1:nrun + 1] = fe % n; RR[1:nrun + 1] = fs // n
        rows = np.arange(nr)[:, None]; kk = np.arange(n)[None, :]
        pid = cum; nid = np.minimum(cum + 1, nrun + 1)
        pok = RR[pid] == rows; nok = RR[nid] == rows
        dp = np.where(pok, kk - RE[pid], 1e9); dn = np.where(nok, RS[nid] - kk, 1e9)
        ID = np.where(samp, cum, np.where(dp <= dn, np.where(pok, pid, 0), np.where(nok, nid, 0)))
        kp = np.clip(np.rint(A - a0).astype(np.int32), 0, n - 1)
        rid = ID[ri, kp]
        valid = rid > 0
        S = a0 + RS[rid] - 0.5 + (_h01(rid, salt, 1) - 0.5) * 2 * jitter
        E = a0 + RE[rid] + 0.5 + (_h01(rid, salt, 2) - 0.5) * 2 * jitter
        rowg = ri + r0
        if length:
            Ls = float(length)
            off = (np.mod(rowg * stagger, 1.0) + (_h01(rowg, salt, 5) - 0.5) * 0.12) * Ls   # machines drift a little
            j = np.floor((A + off) / Ls)
            s0 = np.maximum(j * Ls - off, S); s1 = np.minimum(j * Ls - off + Ls, E)
        elif maxlen:
            Lr = np.maximum(E - S, 1.0)
            m_ = np.maximum(1, np.ceil(Lr / maxlen)); Lg = Lr / m_
            off = (rowg % 2) * 0.5 * Lg * (m_ > 1)
            j = np.floor((A - S + off) / Lg)
            s0 = np.maximum(S + j * Lg - off, S); s1 = np.minimum(S + (j + 1) * Lg - off, E)
        else:
            j = np.zeros_like(A); s0, s1 = S, E
        Lst = np.maximum(s1 - s0, 0.6)
        t = np.clip((A - s0) / Lst, 0, 1)
        dout = np.maximum(np.maximum(S - A, A - E), 0)
        cap = np.where(dout > 0, np.hypot(dout, np.abs(v) * pitch * 0.5), 0)
        a = np.clip((pitch * 0.5 - cap) / 0.9 + 0.5, 0, 1) * valid
        de = np.minimum(A - s0, s1 - A)
        rho = pitch * 0.8
        u = np.clip(1 - np.maximum(de, 0) / rho, 0, 0.96)
        hz = np.sqrt(1 - u * u)
        g = np.clip(u / hz, 0, 3) * np.where(A - s0 < s1 - A, 1.0, -1.0)
        if not length:
            hb = np.minimum(Lst * 0.11, 3.2)
            g = g + hb * np.pi * np.cos(np.pi * t) / Lst
        rnd = (_h01(rid, j.astype(np.int64), salt) - 0.5) * 2
        return dict(a=a, v=v, g=g, hz=hz, rnd=rnd, d=(dx, dy), p=(px, py), A=A)

    def fill(self, mask, colour, angle=45.0, kind='tatami', pitch=None, length=None, stagger=0.3, maxlen=None,
             sheen=1.0, shadow=0.32, jitter=None, pad=1.0):
        """stitch a shape. kind='tatami': short staggered stitches (backgrounds, big areas);
        kind='satin': one float per row (letters, narrow shapes; split above `maxlen` px)"""
        satin = kind == 'satin'
        pitch = pitch or (2.2 if satin else 2.6)
        if not satin: length = length or 15.0
        if satin and maxlen is None: maxlen = 64.0
        jitter = (0.5 if satin else 0.7) if jitter is None else jitter
        bb = self._bbox(mask, 8)
        if bb is None: return
        x0, y0, x1, y1 = bb
        m = mask[y0:y1, x0:x1]
        r = self._scan(m, x0, y0, angle, pitch, None if satin else length, stagger, maxlen if satin else None,
                       jitter, salt=self._seed() % 100000)
        if r is None: return
        gro = 0.74 if satin else 0.62
        ao = (gro + (1 - gro) * np.sqrt(np.clip(1 - 0.9 * r['v'] ** 2, 0, 1)) ** 0.7) * (0.7 + 0.3 * r['hz'])
        if pad:
            dome = blur(m, pitch * 1.6)
            gy, gx = np.gradient(dome)
            ao = ao * (1 + np.clip(-(gx * self.L[0] + gy * self.L[1]) * 5 * pad, -0.22, 0.22))
        rgb = self._thread_rgb(colour, r['v'] * (0.7 if satin else 1.0), r['g'], r['d'], r['p'], ao, r['rnd'] * (0.035 if satin else 0.05), sheen,
                               gloss=16 if satin else 12)
        self._put((y0, y1, x0, x1), r['a'], rgb, shadow)

    # ================================================================ stitches along a path
    def _pparam(self, P, closed, maxd, inside=None):
        """for every pixel within maxd of polyline P: arclength s of the nearest point, signed distance d
        (closed: + outside; open: + on the left-hand normal (-ty, tx)), the unit tangent there"""
        P = np.asarray(P, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        seg = P[1:] - P[:-1]
        sl = np.hypot(seg[:, 0], seg[:, 1])
        keep = sl > 1e-3
        A0, seg, sl = P[:-1][keep], seg[keep], sl[keep]
        if len(sl) == 0: return None
        cum = np.concatenate([[0], np.cumsum(sl)]).astype(np.float32)
        x0 = int(max(0, np.floor(P[:, 0].min() - maxd - 3))); x1 = int(min(self.W, np.ceil(P[:, 0].max() + maxd + 4)))
        y0 = int(max(0, np.floor(P[:, 1].min() - maxd - 3))); y1 = int(min(self.H, np.ceil(P[:, 1].max() + maxd + 4)))
        if x1 <= x0 or y1 <= y0: return None
        im = Image.new('L', (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(im).line([(float(x) - x0, float(y) - y0) for x, y in P], fill=255, width=int(2 * maxd + 6), joint='curve')
        for q in (P[0], P[-1]):
            ImageDraw.Draw(im).ellipse((q[0] - x0 - maxd - 3, q[1] - y0 - maxd - 3, q[0] - x0 + maxd + 3, q[1] - y0 + maxd + 3), fill=255)
        im = im.filter(ImageFilter.MaxFilter(5))                     # PIL's wide polylines leave pinholes
        ys, xs = np.nonzero(np.asarray(im) > 0)
        X = xs.astype(np.float32) + x0; Y = ys.astype(np.float32) + y0
        N = len(X); M = len(sl)
        s = np.empty(N, np.float32); dist = np.empty(N, np.float32); tx = np.empty(N, np.float32); ty = np.empty(N, np.float32)
        side = np.empty(N, np.float32)
        ch = max(256, 3_000_000 // M)
        ux, uy = seg[:, 0] / sl, seg[:, 1] / sl
        for i in range(0, N, ch):
            wx = X[i:i + ch, None] - A0[None, :, 0]; wy = Y[i:i + ch, None] - A0[None, :, 1]
            proj = wx * ux[None] + wy * uy[None]
            tt = np.clip(proj, 0, sl[None])
            ex = wx - tt * ux[None]; ey = wy - tt * uy[None]
            dd = ex * ex + ey * ey
            k = np.argmin(dd, axis=1); rr = np.arange(len(k))
            pk = proj[rr, k]
            if not closed:                                          # extend s beyond the two ends
                pk = np.where(k == 0, np.minimum(pk, sl[0]), pk)
                pk = np.where(k == M - 1, np.maximum(pk, 0), pk)
                pk = np.where((k > 0) & (k < M - 1), tt[rr, k], pk)
            else:
                pk = tt[rr, k]
            s[i:i + ch] = cum[k] + pk
            dist[i:i + ch] = np.sqrt(dd[rr, k])
            tx[i:i + ch] = ux[k]; ty[i:i + ch] = uy[k]
            side[i:i + ch] = np.sign(ux[k] * ey[rr, k] - uy[k] * ex[rr, k] + 1e-9)
        sel = dist <= maxd
        ys, xs, s, dist, tx, ty, side = ys[sel], xs[sel], s[sel], dist[sel], tx[sel], ty[sel], side[sel]
        if closed:
            if inside is None: inside = polygon_mask(self.H, self.W, P, ss=1)
            ins = inside[ys + y0, xs + x0] > 0.5
            d = np.where(ins, -dist, dist)
            nrm = np.where(ins, -side, side)                         # +1 when the left normal points outward
            o = np.sign(np.mean(nrm) + 1e-9)
            nx, ny = -ty * o, tx * o                                 # outward normal
        else:
            d = dist * side
            nx, ny = -ty, tx
        return dict(ys=ys, xs=xs, s=s, d=d, tx=tx, ty=ty, nx=nx, ny=ny, win=(y0, y1, x0, x1), length=float(cum[-1]))

    def _resolve(self, g, ph, lo=1.2, hi=2.1):
        """0..1 per band pixel: how well the stitches resolve. Inside tight curves radial stitches crowd below a pixel
        and would alias into a starburst; there the ridges are faded and the thread reads as a smooth fan."""
        y0, y1, x0, x1 = g['win']
        F = np.zeros((y1 - y0, x1 - x0), np.float32); M = np.zeros_like(F)
        F[g['ys'], g['xs']] = ph; M[g['ys'], g['xs']] = 1
        gy, gx = np.gradient(F)
        f = np.hypot(gx, gy)[g['ys'], g['xs']]
        f = np.where(f > 4.0, 0.0, f)                               # the closing seam / band edge: ignore
        return smoothstep(lo, hi, 1.0 / np.maximum(f, 1e-3))

    def _scatter(self, g, a, rgb):
        y0, y1, x0, x1 = g['win']
        A = np.zeros((y1 - y0, x1 - x0), np.float32); R = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
        A[g['ys'], g['xs']] = a; R[g['ys'], g['xs']] = rgb
        return A, R

    def run(self, pts, colour, stitch=10.0, gap=3.0, width=2.6, smooth=True, sheen=1.0, twist=0.0, shadow=0.4,
            start=0.0, off=(1.4, 1.9), soft=1.3, clip=None):
        """running stitch along a path: `stitch` px on top, `gap` px under. gap=0 and a huge stitch = one
        continuous thread (see thread()). clip: a mask the stitches must stay inside (e.g. a patch)"""
        P = spline(pts, 12) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        rho = width / 2
        g = self._pparam(P, False, rho + 2)
        if g is None: return
        s, d = g['s'], g['d']
        Ltot = g['length']
        per = stitch + gap
        q = (s - start) / per
        j = np.floor(q); loc = (q - j) * per
        ins = loc <= stitch
        ds = np.where(ins, 0, np.minimum(loc - stitch, per - loc))
        ds = np.maximum(ds, np.maximum(-s, s - Ltot))
        rr = np.hypot(ds, d)
        a = np.clip((rho - rr) / 0.8 + 0.5, 0, 1)
        v = np.clip(d / rho, -1, 1)
        e0 = np.minimum(np.where(ins, np.minimum(loc, stitch - loc), 0), np.minimum(s, Ltot - s))
        rho_e = rho * 1.3
        u = np.clip(1 - np.maximum(e0, 0) / rho_e, 0, 0.96)
        hz = np.sqrt(1 - u * u)
        first = np.where(ins, loc < stitch / 2, loc - stitch > per - loc)
        first = np.where(s < rho_e, True, np.where(Ltot - s < rho_e, False, first))
        gz = np.clip(u / hz, 0, 3) * np.where(first, 1.0, -1.0)
        ao = (0.62 + 0.38 * np.sqrt(np.clip(1 - 0.9 * v * v, 0, 1))) * (0.6 + 0.4 * hz)
        jj = np.where(ins | (loc - stitch < per - loc), j, j + 1).astype(np.int64)
        rnd = (_h01(jj, 7) - 0.5) * 0.08
        rgb = self._thread_rgb(colour, v, gz, (g['tx'], g['ty']), (g['nx'], g['ny']), ao, rnd, sheen,
                               twist=twist, along=s, width=width)
        if clip is not None:
            y0, x0 = g['win'][0], g['win'][2]
            a = a * clip[g['ys'] + y0, g['xs'] + x0]
        A, R = self._scatter(g, a, rgb)
        self._put(g['win'], A, R, shadow, off, soft)

    def thread(self, pts, colour, width=2.6, sheen=0.5, twist=1.0, shadow=0.45, lift=1.0):
        """a loose length of sewing thread lying on the cloth (twisted plies, a shadow that grows with `lift`)"""
        self.run(pts, colour, stitch=1e7, gap=0.0, width=width, sheen=sheen, twist=twist, shadow=shadow,
                 off=(2.0 * lift + 0.5, 2.6 * lift + 0.6), soft=1.2 + 0.8 * lift)

    def knot(self, x, y, colour, r=4.5, shadow=0.45):
        """French knot / satin dot: a small bead of wrapped thread (stars, sparks)"""
        m = int(r + 6)
        x0, x1, y0, y1 = int(max(0, x - m)), int(min(self.W, x + m + 1)), int(max(0, y - m)), int(min(self.H, y + m + 1))
        YY, XX = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        X, Y = XX - x, YY - y
        dd = np.hypot(X, Y) / r
        a = np.clip((1 - dd) * r / 0.8 + 0.5, 0, 1)
        nz = np.sqrt(np.clip(1 - dd ** 2, 0.02, 1)); nx, ny = X / r, Y / r
        nn = np.sqrt(nx * nx + ny * ny + nz * nz); nx, ny, nz = nx / nn, ny / nn, nz / nn
        diff = np.clip(nx * self.L[0] + ny * self.L[1] + nz * self.L[2], 0, 1)
        wrap = np.sin(np.arctan2(Y, X) * 3 + dd * 7)
        nh = np.clip(nx * self.Hv[0] + ny * self.Hv[1] + nz * self.Hv[2], 0, 1)
        col = _c(colour)
        rgb = col * ((0.3 + 0.95 * diff) * (1 + 0.1 * wrap * nz))[..., None] + (0.35 * nh ** 30)[..., None] * (0.6 + 0.4 * col)
        self._put((y0, y1, x0, x1), a, rgb, shadow)

    def star(self, x, y, r, colour, angle=0.0, inner=0.3, points=4):
        """a little satin star (each arm its own satin column, stitched along the arm)"""
        for k in range(points):
            ph = np.deg2rad(angle + 360.0 * k / points)
            tip = (x + r * np.cos(ph), y - r * np.sin(ph))
            w = r * inner
            l = (x + w * np.cos(ph + np.pi / 2), y - w * np.sin(ph + np.pi / 2))
            rr = (x + w * np.cos(ph - np.pi / 2), y - w * np.sin(ph - np.pi / 2))
            self.fill(self.poly([l, tip, rr, (x, y)]), colour, angle=np.rad2deg(ph) + 90, kind='satin', pitch=1.8,
                      shadow=0.25, pad=0.5)

    # ================================================================ edges
    _SUB = ((-0.25, -0.25), (0.25, -0.25), (-0.25, 0.25), (0.25, 0.25))

    def _supersample(self, g, fn):
        """evaluate fn(s, d) -> (coverage, rgb) at 4 sub-pixel positions (moved along the local tangent / normal)
        and average: wraps and stitches 2-3 px apart would otherwise beat against the pixel grid (moire)"""
        A = 0; C = 0
        for ox, oy in self._SUB:
            ds = ox * g['tx'] + oy * g['ty']; dd = ox * g['nx'] + oy * g['ny']
            a, rgb = fn(g['s'] + ds, g['d'] + dd)
            A = A + a; C = C + rgb * a[:, None]
        A = A / len(self._SUB)
        return A, C / np.maximum(A * len(self._SUB), 1e-6)[:, None]

    def merrow(self, blank, colour, width=18.0, pitch=2.6, slant=0.55, shadow=0.55):
        """merrowed (overlocked) edge: thread wrapped round and round the cut edge -> a raised rolled cord"""
        P = blank.pts
        R = width / 2; c_off = -0.3 * width
        g = self._pparam(P, True, abs(c_off) + R + 3, inside=blank.mask)
        if g is None: return
        tx, ty, nx, ny = g['tx'], g['ty'], g['nx'], g['ny']
        per = g['length']
        nw = max(8, int(round(per / pitch))); pit = per / nw
        si = np.clip(g['s'].astype(np.int64), 0, int(per) + 7)
        Rr = R * (1 + 0.04 * fbm1d(int(per) + 8, 40, 3, self._seed())[si])
        jit = fbm1d(int(per) + 8, 24, 2, self._seed())[si] * 0.08
        res = self._resolve(g, (g['s'] + slant * (g['d'] - c_off)) / pit + jit)
        L, Hv = self.L, self.Hv
        col = _c(colour)

        def ev(s, d):
            dc = d - c_off
            u = np.clip(dc / Rr, -1, 1)
            a = np.clip((Rr - np.abs(dc)) / 0.9 + 0.5, 0, 1)
            ph = (s + slant * dc) / pit + jit
            w = ((ph - np.floor(ph)) * 2 - 1) * res
            nzt = np.sqrt(np.clip(1 - u * u, 0.03, 1))
            wz = np.sqrt(np.clip(1 - 0.85 * w * w, 0.05, 1))
            Nx = nx * u * wz + tx * w * 0.6; Ny = ny * u * wz + ty * w * 0.6; Nz = nzt * wz
            nn = np.sqrt(Nx * Nx + Ny * Ny + Nz * Nz); Nx, Ny, Nz = Nx / nn, Ny / nn, Nz / nn
            Tx = nx * nzt - tx * slant * 0.6; Ty = ny * nzt - ty * slant * 0.6; Tz = -u
            tn = np.sqrt(Tx * Tx + Ty * Ty + Tz * Tz); Tx, Ty, Tz = Tx / tn, Ty / tn, Tz / tn
            diff = np.clip(Nx * L[0] + Ny * L[1] + Nz * L[2], 0, 1)
            TH = Tx * Hv[0] + Ty * Hv[1] + Tz * Hv[2]
            aniso = np.sqrt(np.clip(1 - TH * TH, 0, 1)) ** 10
            nh = np.clip(Nx * Hv[0] + Ny * Hv[1] + Nz * Hv[2], 0, 1)
            spec = 0.42 * aniso * nh ** 5 + 0.18 * nh ** 36
            rnd = (_h01(np.floor(ph).astype(np.int64), 3) - 0.5) * 0.07
            ao = (0.6 + 0.4 * wz) * (0.7 + 0.3 * nzt)
            rgb = col * ((0.28 + 0.98 * diff) * ao * (1 + rnd))[:, None] + (spec * 0.7)[:, None] * (0.5 + 0.5 * col)
            return a, rgb

        a, rgb = self._supersample(g, ev)
        A, Rg = self._scatter(g, a, rgb)
        self._put(g['win'], A, Rg, shadow, off=(2.2, 3.0), soft=2.4)

    def column(self, pts, colour, width=8.0, closed=False, pitch=2.2, smooth=True, inset=None, shadow=0.4, blank=None):
        """satin column along a path: stitches laid square to the path, side by side (ring separators, logs,
        tent poles, the hot-cut border). For a closed outline `inset` moves the column inward (0 = centred)."""
        P = np.asarray(pts, np.float32)
        if smooth and not closed and len(P) > 2: P = spline(P, 12)
        hw = width / 2
        off = 0.0 if inset is None else -inset
        g = self._pparam(P, closed, abs(off) + hw + 3, inside=None if blank is None else blank.mask)
        if g is None: return
        tx, ty, nx, ny = g['tx'], g['ty'], g['nx'], g['ny']
        per = g['length']
        n = max(4, int(round(per / pitch))); pit = per / n
        res = self._resolve(g, g['s'] / pit)
        col = colour

        def ev(s, d):
            ph = s / pit; j = np.floor(ph).astype(np.int64)
            v = ((ph - j) * 2 - 1) * res
            jj = j % n if closed else j
            din = off - hw + (_h01(jj, 11) - 0.5) * 0.9
            dout = off + hw + (_h01(jj, 12) - 0.5) * (0.6 if blank is not None else 1.6)
            if not closed:                                          # square ends: stitches only between 0..length
                v = np.where((s < 0) | (s > per), 1.0, v)
            Lc = dout - din
            e = np.minimum(d - din, dout - d)
            a = np.clip(e / 0.8 + 0.5, 0, 1)
            if not closed:
                a = a * np.clip((np.minimum(s, per - s) + 0.6) / 0.9, 0, 1)
            t = np.clip((d - din) / Lc, 0, 1)
            rho = pitch * 0.9
            u = np.clip(1 - np.maximum(e, 0) / rho, 0, 0.96); hz = np.sqrt(1 - u * u)
            gz = np.clip(u / hz, 0, 3) * np.where(d - din < dout - d, 1.0, -1.0)
            hb = min(1.8, width * 0.12)
            gz = gz + hb * np.pi * np.cos(np.pi * t) / Lc
            ao = (0.74 + 0.26 * np.sqrt(np.clip(1 - 0.9 * v * v, 0, 1))) * (0.62 + 0.38 * hz)
            rnd = (_h01(jj, 13) - 0.5) * 0.035
            return a, self._thread_rgb(col, v * 0.6, gz, (nx, ny), (tx, ty), ao, rnd, 1.0, gloss=16)

        a, rgb = self._supersample(g, ev)
        A, R = self._scatter(g, a, rgb)
        self._put(g['win'], A, R, shadow, off=(1.6, 2.2), soft=1.6)

    def satin_border(self, blank, colour, width=16.0, pitch=2.2, shadow=0.45):
        """hot-cut border of a die-cut patch: a wide satin column along the outline, stitches square to the edge,
        reaching a hair past the cut edge (the twill is melted flush underneath)"""
        self.column(blank.pts, colour, width=width + 1.6, closed=True, pitch=pitch, inset=width / 2 - 0.8,
                    shadow=shadow, blank=blank)

    def whip(self, blank, colour, frm=0.0, to=1.0, spacing=20.0, reach=(5.0, 16.0), lean=6.0, width=2.4):
        """hand-sew a patch on: slanted whip stitches over the edge from the denim into the patch, for the part of
        the outline between fractions frm..to of its length. Returns the point where the last stitch went in."""
        P = _resample(blank.pts, 1.0, True)
        n = len(P)
        tg = np.roll(P, -2, 0) - np.roll(P, 2, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([tg[:, 1], -tg[:, 0]], 1)
        cen = P.mean(0)
        if np.mean(np.sum((P - cen) * nrm, 1)) < 0: nrm = -nrm          # outward
        k0, k1 = int(frm * n), int(to * n)
        step = max(1, int(spacing))
        last = None
        for i, k in enumerate(range(k0, k1, step)):
            k = k % n; kb = (k + int(lean)) % n
            jit = (_h01(np.array([i]), 21)[0] - 0.5) * 3
            pa = P[k] + nrm[k] * (reach[0] + jit * 0.4)
            pb = P[kb] - nrm[kb] * (reach[1] + jit)
            self.run([pa, pb], colour, stitch=1e6, gap=0, width=width, smooth=False, sheen=0.4, twist=1.0,
                     shadow=0.4, off=(1.2, 1.6))
            last = pa
        return last

    # ================================================================ lettering
    def text(self, s, x, y, size, colour, font='rounded', angle=55.0, anchor='mm', spacing=0.0, rot=0.0, pitch=1.9):
        """satin letters (one satin angle for the whole word, slanted across the strokes)"""
        self.fill(self.text_mask(s, x, y, size, font, anchor, spacing, rot), colour, angle=angle + rot, kind='satin',
                  pitch=pitch, shadow=0.35, pad=0.6)

    def arc_text(self, s, cx, cy, r, size=40, colour='#f3e6c4', centre=90.0, font='rounded', spacing=0.06,
                 bottom=False, angle=55.0, pitch=1.9):
        """satin letters set on a circle: centre=90 reads along the top (letters stand outward),
        bottom=True reads along the bottom (letters stand inward)"""
        f = load_font(font, size)
        adv = [f.getlength(ch) + spacing * size for ch in s]
        total = sum(adv) - spacing * size
        pos = np.cumsum([0] + adv[:-1]) + np.array([f.getlength(ch) / 2 for ch in s])
        for ch, p_ in zip(s, pos):
            if ch == ' ': continue
            off = (total / 2 - p_) / r
            if not bottom:
                phi = np.deg2rad(centre) + off; rot = np.rad2deg(phi) - 90
            else:
                phi = np.deg2rad(centre) - off; rot = np.rad2deg(phi) - 270
            x, y = cx + r * np.cos(phi), cy - r * np.sin(phi)
            m = text_mask(self.H, self.W, ch, f, (x, y), 'mm', 0.0, rot)
            self.fill(m, colour, angle=rot + angle, kind='satin', pitch=pitch, shadow=0.35, pad=0.6)

    # ================================================================ the needle
    def needle(self, eye, tip, radius=3.3, colour='#c4c8cf', shadow=0.5):
        """a steel hand-sewing needle lying on the cloth: eye end at `eye`, point at `tip`. Draw the thread first:
        it shows through the eye."""
        P = np.array([eye, tip], np.float32)
        g = self._pparam(P, False, radius + 3)
        if g is None: return
        s, d = g['s'], g['d']; Lt = g['length']
        taper = 46.0
        rs = radius * np.where(s > Lt - taper, np.clip((Lt - s) / taper, 0.02, 1) ** 0.75, 1.0)
        rs = np.where(s < 0, radius, rs)
        a = np.clip((rs - np.abs(d)) / 0.8 + 0.5, 0, 1) * np.clip((s + 0.5) / 1.0, 0, 1) * np.clip((Lt - s) / 0.8 + 0.3, 0, 1)
        a = a * np.where(s < radius, np.clip((radius - np.hypot(radius - s, d)) / 0.8 + 0.5, 0, 1), 1)
        # the eye: an elongated slot near the blunt end
        es, el, ew = 9.0, 9.0, radius * 0.42
        eu = (s - (es + el)) / el; ev = d / ew
        hole = np.clip((1 - np.sqrt(eu * eu + ev * ev)) * 6, 0, 1)
        rim = np.exp(-((np.sqrt(eu * eu + ev * ev) - 1) / 0.35) ** 2)
        a = a * (1 - hole)
        v = np.clip(d / np.maximum(rs, 0.3), -1, 1)
        nzc = np.sqrt(np.clip(1 - v * v, 0.02, 1))
        nx, ny, nz = g['nx'] * v, g['ny'] * v, nzc
        L, Hv = self.L, self.Hv
        ndl = nx * L[0] + ny * L[1] + nz * L[2]
        nh = np.clip(nx * Hv[0] + ny * Hv[1] + nz * Hv[2], 0, 1)
        # polished steel: mostly reflection. A soft room (dark floor at the flanks, bright ceiling on top),
        # the window as a crisp streak, and the denim's blue picked up on the lower flank
        room = 0.1 + 0.55 * smoothstep(-0.2, 0.95, ndl) + 0.22 * nzc ** 3
        streak = 1.3 * nh ** 90 + 0.35 * nh ** 12
        col = _c(colour)
        blue = getattr(self, 'denim_colour', col)
        flank = np.clip(-v * np.sign(g['nx'] * L[0] + g['ny'] * L[1] + 1e-6), 0, 1) ** 2 * 0.5
        rgb = (col * room[:, None] * (1 - flank[:, None]) + blue * 0.6 * flank[:, None]) * (1 - 0.5 * rim)[:, None] \
            + streak[:, None]
        A, R = self._scatter(g, a, rgb)
        self._put(g['win'], A, R, shadow, off=(3.5, 4.5), soft=2.6)

    # ================================================================ output
    def composite(self, vignette=0.14, grain=0.012):
        YY, XX = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        r = np.hypot((XX - self.W / 2) / self.W, (YY - self.H / 2) / self.H)
        img = self.img * (1 - vignette * r ** 2 * 2.4)[..., None]
        if grain:
            img = img + np.random.default_rng(7).normal(0, grain, (self.H, self.W, 1)).astype(np.float32)
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        """snapshot for the draw-on animation"""
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
