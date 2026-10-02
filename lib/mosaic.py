"""mosaic — a Roman floor mosaic: thousands of hand-cut stone and glass tesserae pressed in rows into lime mortar,
grouted, polished and then two thousand years old (numpy + Pillow only).

Model -- the way a mosaicist actually works:
  cartoon    a hidden full-size colour map (the "cartoon") painted with flat colours and gradients. Nobody ever
             sees it; every stone that is set looks at the cartoon under itself, takes the mean colour and picks
             the nearest stone in the box (`STONES`), with a little noise so that tone boundaries are dithered
             the way a mosaicist mixes two stones. Explicit colours (outlines, letters, eyes) skip the cartoon.
  sinopia    before laying, the design is brushed in red ochre on the wet setting bed; `sinopia()` draws it and
             it stays visible wherever no stone has been set yet (the first stage of the animation).
  andamento  the *flow* of the rows is what makes a mosaic read as a mosaic. Every laying method traces
             iso-lines of a scalar field (marching squares on a distance field or on a plain coordinate) and
             walks along each line cutting it into stones:
               line     one row along a path (letters, fins, rigging, net cords);
               outline  the first row(s) just inside a figure's edge, usually in a dark stone;
               fill     rows that follow the outline inward (opus vermiculatum). With wrap=True they also flow
                        round any stone already set inside the figure (an eye, a gill line), the way a
                        mosaicist rings an eye with concentric rows;
               halo     one or two background rows that follow the outline of everything already set, outside;
               rows     the background in straight (or wavy, any field) rows: opus tessellatum;
               frame    rows parallel to the sides of a rectangle, mitred at the corners, for borders;
               tuck     small filler pieces cut to fit the holes that are left.
             A row is fitted with a whole number of stones, so stones are a little longer or shorter than
             average; on a curve each stone becomes a slight wedge (its corners are offset along the local
             normals). Rows are split at sharp corners. Stones near a figure's spine stop at the ridge of the
             distance field, so the two sides of a fish meet along its back instead of overlapping.
  stones     every tessera is a small convex polygon: four corners jittered, now and then a corner knocked off,
             a degree or two of rotation, its own height and a slight tilt, because they are set by hand.
             A stone that would land mostly on stones already set is rejected; one that overlaps a little is
             cut to fit (earlier stones win, and keep a grout gap). Materials: limestone (matte, mottled),
             marble (veins, a little gloss), smalti glass (saturated, glossy, bubbles) and terracotta (porous).
  light      rendered at `ss` x supersampling as a height field: stone tops are domed and their edges worn round
             (each stone's own signed distance gives the bevel), grout sits lower with sand in it, the bed lower
             still. One raking light from the upper left: Lambert + Blinn-Phong per material, cast shadows from
             each stone onto the grout, ambient occlusion in the joints, the per-stone tilt making neighbouring
             stones of the same colour catch the light differently.
  time       `lacuna()` loses the stones in a patch: the old bed shows, with the sockets of the lost stones
             still printed in it; `crack()` runs a settling crack through stones and joints; `patina()` puts
             dirt in the joints and wears the polish.

    from mosaic import Mosaic
    m = Mosaic(1920, 1080, seed=1, tile=13)
    fish = m.ellipse(960, 540, 160, 60)
    m.shade(fish, 'slate', 'white', (960, 480), (960, 600))     # the cartoon: dark back, pale belly
    m.sinopia(fish); m.stage('sinopia')
    m.point(1060, 530, 'black', 9, 'round')                     # the eye first
    m.outline(fish, 'black', size=9); m.fill(fish, size=9)      # vermiculatum, rows ring the eye
    m.halo(rows=2, stones=['white', 'bone'])                    # background rows hugging the figure
    m.rows(m.free(), stones=['white', 'bone', 'cream'])         # tessellatum for the rest
    m.save('out.jpg')
Coordinates are output pixels, y down; angles in degrees, counter-clockwise; masks are float (H, W) in 0..1.
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep, polygon_mask, spline, fbm1d, height_shadow


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


# ---------------------------------------------------------------- the box of stones
MATERIALS = ('stone', 'marble', 'glass', 'terracotta')
STONES = {
    'white': ('#ece5d4', 'marble'), 'bone': ('#dfd5bd', 'stone'), 'cream': ('#d2c29f', 'stone'),
    'buff': ('#bfa980', 'stone'), 'grey': ('#a49e93', 'stone'), 'slate': ('#6c6964', 'stone'),
    'black': ('#2a2725', 'stone'), 'umber': ('#53382a', 'stone'), 'brown': ('#7c5437', 'stone'),
    'ochre': ('#bf924a', 'stone'), 'yellow': ('#d8b75f', 'stone'), 'red': ('#9c3d2a', 'stone'),
    'brick': ('#b45a3b', 'terracotta'), 'pink': ('#cd9780', 'marble'), 'rose': ('#e2bca7', 'marble'),
    'green': ('#5e6d4b', 'stone'), 'navy': ('#1c3453', 'glass'), 'blue': ('#2b5a88', 'glass'),
    'sky': ('#5a8eba', 'glass'), 'pale': ('#9bbfd3', 'glass'), 'teal': ('#2e7c80', 'glass'),
    'scarlet': ('#c02e23', 'glass'), 'flame': ('#dc6326', 'glass'), 'gold': ('#e5b039', 'glass'),
}
SINOPIA = '#a9563c'
#                 stone  marble glass  terra
_GLOSS = np.array([9.0, 28.0, 70.0, 5.0], np.float32)
_SPEC = np.array([0.035, 0.09, 0.34, 0.02], np.float32)
_MOTTLE = np.array([0.075, 0.04, 0.03, 0.09], np.float32)


def _opp(c):
    """rgb -> (lightness, red-green, yellow-blue): stones are matched on hue first, so greys stay grey"""
    c = np.asarray(c, np.float32)
    return np.stack([c[..., 0] * 0.3 + c[..., 1] * 0.59 + c[..., 2] * 0.11, c[..., 0] - c[..., 1],
                     (c[..., 0] + c[..., 1]) * 0.5 - c[..., 2]], -1)


# ---------------------------------------------------------------- distance fields and iso-lines
def _shift_fill(a, dy, dx, fill):
    """out[y, x] = a[y + dy, x + dx], `fill` where that falls outside"""
    H, W = a.shape
    out = np.full_like(a, fill)
    if abs(dy) >= H or abs(dx) >= W: return out
    ys, yd = (slice(dy, H), slice(0, H - dy)) if dy >= 0 else (slice(0, H + dy), slice(-dy, H))
    xs, xd = (slice(dx, W), slice(0, W - dx)) if dx >= 0 else (slice(0, W + dx), slice(-dx, W))
    out[yd, xd] = a[ys, xs]
    return out


def edt(seeds, reach=None):
    """Euclidean distance from every pixel to the nearest True pixel of `seeds` (jump flooding, numpy only).
    `reach` limits the first jump: distances beyond about 2 x reach may be overestimated (fine for row layout)."""
    H, W = seeds.shape
    if not seeds.any():
        return np.full((H, W), 1e6, np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    far = np.float32(-1e5)
    sy = np.where(seeds, yy, far).astype(np.float32)
    sx = np.where(seeds, xx, far).astype(np.float32)
    best = np.where(seeds, 0, 1e12).astype(np.float32)
    top = max(H, W) if reach is None else min(max(H, W), int(reach))
    step = 1 << int(np.ceil(np.log2(max(top, 2))))
    steps = []
    while step >= 1:
        steps.append(step); step //= 2
    for st in steps + [1]:
        for dy in (-st, 0, st):
            for dx in (-st, 0, st):
                if dx == 0 and dy == 0: continue
                cy = _shift_fill(sy, dy, dx, far); cx = _shift_fill(sx, dy, dx, far)
                d = (yy - cy) ** 2 + (xx - cx) ** 2
                bt = d < best
                sy = np.where(bt, cy, sy); sx = np.where(bt, cx, sx); best = np.where(bt, d, best)
    return np.sqrt(best)


def maxfilt(a, r):
    """square max filter of radius r (separable, doubling shifts)"""
    r = int(r)
    out = a.copy()
    for ax in (0, 1):
        cur, span = out, 0
        while span < r:
            st = min(span + 1, r - span)
            dy, dx = (st, 0) if ax == 0 else (0, st)
            cur = np.maximum(np.maximum(cur, _shift_fill(cur, dy, dx, -np.inf)), _shift_fill(cur, -dy, -dx, -np.inf))
            span += st
        out = cur
    return out


def iso_lines(f, step, offset=0.5):
    """every iso-line f = (k + offset) * step of the field f (NaN = outside), by marching squares.
    returns [(k, points (n, 2) as x, y in pixel-centre coordinates, closed)]"""
    h, w = f.shape
    with np.errstate(invalid='ignore'):
        q = np.floor(f / step - offset)
        tl, tr, br, bl = q[:-1, :-1], q[:-1, 1:], q[1:, 1:], q[1:, :-1]
        qmax = np.maximum(np.maximum(tl, tr), np.maximum(br, bl))         # NaN propagates -> no crossing
        qmin = np.minimum(np.minimum(tl, tr), np.minimum(br, bl))
        cross = qmax > qmin
    ii, jj = np.nonzero(cross)
    if len(ii) == 0: return []
    lev = qmax[ii, jj]
    Lv = ((lev + offset) * step).astype(np.float32)
    A = f[ii, jj] - Lv; B = f[ii, jj + 1] - Lv; C = f[ii + 1, jj + 1] - Lv; D = f[ii + 1, jj] - Lv
    sA, sB, sC, sD = A >= 0, B >= 0, C >= 0, D >= 0

    def lerp(u, v):
        den = u - v
        return np.clip(np.where(np.abs(den) > 1e-9, u / np.where(np.abs(den) > 1e-9, den, 1), 0.5), 0, 1)

    X = jj.astype(np.float32); Y = ii.astype(np.float32)
    pts = np.stack([np.stack([X + lerp(A, B), Y], 1), np.stack([X + 1, Y + lerp(B, C)], 1),
                    np.stack([X + lerp(D, C), Y + 1], 1), np.stack([X, Y + lerp(A, D)], 1)], 1)   # top right bottom left
    li = (lev - lev.min()).astype(np.int64); NL = int(li.max()) + 1
    base = (ii.astype(np.int64) * w + jj)
    keys = np.stack([2 * base, 2 * (base + 1) + 1, 2 * (base + w), 2 * base + 1], 1) * NL + li[:, None]
    flags = np.stack([sA != sB, sB != sC, sD != sC, sA != sD], 1)
    cnt = flags.sum(1)
    rows = np.nonzero(cnt == 2)[0]
    e = np.argsort(~flags[rows], axis=1, kind='stable')[:, :2]
    ka, kb = keys[rows, e[:, 0]], keys[rows, e[:, 1]]
    pa, pb = pts[rows, e[:, 0]], pts[rows, e[:, 1]]
    lv = lev[rows]
    sad = np.nonzero(cnt == 4)[0]
    if len(sad):
        cpos = (A[sad] + B[sad] + C[sad] + D[sad]) >= 0
        cutBD = (sA[sad] & sC[sad] & cpos) | (sB[sad] & sD[sad] & ~cpos)
        p1 = np.where(cutBD[:, None], np.array([[0, 1]]), np.array([[0, 3]]))
        p2 = np.where(cutBD[:, None], np.array([[2, 3]]), np.array([[1, 2]]))
        for pr in (p1, p2):
            ka = np.concatenate([ka, keys[sad, pr[:, 0]]]); kb = np.concatenate([kb, keys[sad, pr[:, 1]]])
            pa = np.concatenate([pa, pts[sad, pr[:, 0]]]); pb = np.concatenate([pb, pts[sad, pr[:, 1]]])
            lv = np.concatenate([lv, lev[sad]])
    n = len(ka)
    ends = np.concatenate([ka, kb])
    order = np.argsort(ends, kind='stable'); sk = ends[order]
    same = np.nonzero(sk[1:] == sk[:-1])[0]
    partner = np.full(2 * n, -1, np.int64)
    partner[order[same]] = order[same + 1]; partner[order[same + 1]] = order[same]
    partner = partner.tolist(); PA = (pa + 0.5).tolist(); PB = (pb + 0.5).tolist(); LV = lv.tolist()
    seen = [False] * n
    out = []
    for s0 in range(n):
        if seen[s0]: continue
        seen[s0] = True
        fwd, e, closed = [PB[s0]], s0 + n, False
        while True:
            p = partner[e]
            if p < 0: break
            s = p % n
            if s == s0: closed = True; break
            if seen[s]: break
            seen[s] = True
            if p < n: fwd.append(PB[s]); e = s + n
            else: fwd.append(PA[s]); e = s
        bwd = []
        if not closed:
            e = s0
            while True:
                p = partner[e]
                if p < 0: break
                s = p % n
                if seen[s]: break
                seen[s] = True
                if p < n: bwd.append(PB[s]); e = s + n
                else: bwd.append(PA[s]); e = s
        P = np.array(bwd[::-1] + [PA[s0]] + fwd, np.float32)
        out.append((int(LV[s0]), P, closed))
    return out


# ---------------------------------------------------------------- stroke capitals for inscriptions
def _arc(cx, cy, rx, ry, a0, a1, n=24):
    t = np.radians(np.linspace(a0, a1, n))
    return [(cx + rx * np.cos(x), cy - ry * np.sin(x)) for x in t]


LETTERS = {      # cap height 1, y down; each letter is a list of strokes; one row of stones per stroke
    'A': [[(0, 1), (0.34, 0), (0.68, 1)], [(0.17, 0.6), (0.51, 0.6)]],
    'B': [[(0.04, 1), (0.04, 0)], [(0.04, 0), (0.38, 0), (0.54, 0.12), (0.54, 0.36), (0.38, 0.48), (0.04, 0.48)],
          [(0.38, 0.48), (0.58, 0.6), (0.58, 0.88), (0.42, 1), (0.04, 1)]],
    'C': [_arc(0.4, 0.5, 0.4, 0.5, 48, 312)],
    'D': [[(0.04, 0), (0.04, 1)], [(0.04, 0), (0.3, 0)] + _arc(0.3, 0.5, 0.36, 0.5, 90, -90, 18)[1:] + [(0.04, 1)]],
    'E': [[(0.56, 0), (0.04, 0), (0.04, 1), (0.56, 1)], [(0.04, 0.5), (0.46, 0.5)]],
    'F': [[(0.56, 0), (0.04, 0), (0.04, 1)], [(0.04, 0.5), (0.46, 0.5)]],
    'G': [_arc(0.4, 0.5, 0.4, 0.5, 48, 330), [(0.8, 0.62), (0.8, 0.95)], [(0.56, 0.6), (0.8, 0.6)]],
    'H': [[(0.04, 0), (0.04, 1)], [(0.64, 0), (0.64, 1)], [(0.04, 0.5), (0.64, 0.5)]],
    'I': [[(0.04, 0), (0.04, 1)]],
    'L': [[(0.04, 0), (0.04, 1), (0.54, 1)]],
    'M': [[(0.0, 1), (0.06, 0), (0.4, 0.86), (0.74, 0), (0.8, 1)]],
    'N': [[(0.04, 1), (0.04, 0), (0.66, 1), (0.66, 0)]],
    'O': [_arc(0.42, 0.5, 0.42, 0.5, 90, 450, 40)],
    'P': [[(0.04, 1), (0.04, 0)], [(0.04, 0), (0.38, 0), (0.56, 0.11), (0.6, 0.27), (0.56, 0.42), (0.38, 0.52), (0.04, 0.52)]],
    'Q': [_arc(0.42, 0.5, 0.42, 0.5, 90, 450, 40), [(0.46, 0.8), (0.8, 1.08)]],
    'R': [[(0.04, 1), (0.04, 0)], [(0.04, 0), (0.38, 0), (0.56, 0.11), (0.6, 0.27), (0.56, 0.42), (0.38, 0.52), (0.04, 0.52)],
          [(0.3, 0.52), (0.64, 1)]],
    'S': [[(0.56, 0.1), (0.4, 0.0), (0.18, 0.02), (0.05, 0.16), (0.08, 0.36), (0.3, 0.48), (0.5, 0.58),
           (0.6, 0.76), (0.54, 0.94), (0.32, 1.0), (0.1, 0.96), (0.0, 0.86)]],
    'T': [[(0, 0), (0.68, 0)], [(0.34, 0), (0.34, 1)]],
    'V': [[(0, 0), (0.34, 1), (0.68, 0)]],
    'X': [[(0, 0), (0.62, 1)], [(0.62, 0), (0, 1)]],
    'Y': [[(0, 0), (0.34, 0.5), (0.68, 0)], [(0.34, 0.5), (0.34, 1)]],
}
_CURVED = set('BCDGOPQRS')


class Mosaic:
    def __init__(self, W=1920, H=1080, seed=0, tile=13, gap=1.8, ss=2, light=(-0.52, -0.66, 0.54),
                 bed='#d8cfbb', grout='#b3a892', stones=None):
        self.W, self.H, self.tile, self.gap, self.ss = W, H, float(tile), float(gap), ss
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        L = np.asarray(light, np.float32); self.L = L / np.linalg.norm(L)
        self.bed, self.grout = hexc(bed), hexc(grout)
        self.box = dict(STONES if stones is None else stones)
        self.cartoon = np.ones((H, W, 3), np.float32) * hexc('#e2dac8')
        self.sin = np.zeros((H, W), np.float32)
        self.occ = np.zeros((H, W), bool)
        self.poly, self.rgb, self.mat, self.ht, self.tilt = [], [], [], [], []
        self.lost = []                      # indices of stones lost to time
        self.cracks = []
        self.patina_amt = 0.0
        self.stages = []
        self.stage_ss = 1
        self._names = list(self.box)
        self._pal = np.stack([hexc(self.box[k][0]) for k in self._names])
        self._palmat = np.array([MATERIALS.index(self.box[k][1]) for k in self._names])
        self._opp = _opp(self._pal)
        self.dither = 0.035
        self._tex = {}

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ masks
    def poly_mask(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=2)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        t = np.linspace(0, 2 * np.pi, 120, endpoint=False); a = np.radians(rot)
        x, y = np.cos(t) * rx, np.sin(t) * ry
        return self.poly_mask(np.stack([cx + x * np.cos(a) + y * np.sin(a), cy - x * np.sin(a) + y * np.cos(a)], 1))

    def rect(self, x0, y0, x1, y1):
        m = np.zeros((self.H, self.W), np.float32)
        m[max(int(round(y0)), 0):max(int(round(y1)), 0), max(int(round(x0)), 0):max(int(round(x1)), 0)] = 1
        return m

    def band(self, pts, w0, w1=None):
        """a thick (optionally tapering, w0 -> w1) stroke along pts, as a mask: arms, masts, oars, poles"""
        w1 = w0 if w1 is None else w1
        P = np.asarray(pts, np.float32)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
        n = max(2, int(s[-1] / 1.5) + 2); ss = np.linspace(0, s[-1], n)
        x, y = np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1]); r = (w0 + (w1 - w0) * ss / max(s[-1], 1)) / 2
        k = 3
        bx0 = int(max(np.floor((x - r).min()) - 2, 0)); bx1 = int(min(np.ceil((x + r).max()) + 2, self.W))
        by0 = int(max(np.floor((y - r).min()) - 2, 0)); by1 = int(min(np.ceil((y + r).max()) + 2, self.H))
        out = np.zeros((self.H, self.W), np.float32)
        if bx1 <= bx0 or by1 <= by0: return out
        im = Image.new('L', ((bx1 - bx0) * k, (by1 - by0) * k), 0); d = ImageDraw.Draw(im)
        for xi, yi, ri in zip(x - bx0, y - by0, r):
            d.ellipse(((xi - ri) * k, (yi - ri) * k, (xi + ri) * k, (yi + ri) * k), fill=255)
        out[by0:by1, bx0:bx1] = np.asarray(im.resize((bx1 - bx0, by1 - by0), Image.BILINEAR), np.float32) / 255
        return out

    def everything(self):
        """mask of every stone set so far"""
        return self.occ.astype(np.float32)

    def free(self, region=None):
        """region (default whole picture) minus every stone set so far"""
        m = np.ones((self.H, self.W), np.float32) if region is None else region.copy()
        return m * (1 - self.occ)

    # ------------------------------------------------------------ the cartoon (hidden colour map) and sinopia
    def _col(self, c):
        if isinstance(c, str):
            return hexc(self.box[c][0]) if c in self.box else hexc(c)
        return np.asarray(c, np.float32)

    def _bb(self, mask, pad=0):
        """row/column slices of the part of `mask` that is not zero (whole canvas if empty)"""
        r = np.nonzero((mask > 1e-4).any(1))[0]; c = np.nonzero((mask > 1e-4).any(0))[0]
        if len(r) == 0: return slice(0, 0), slice(0, 0)
        return (slice(max(r[0] - pad, 0), min(r[-1] + pad + 1, self.H)), slice(max(c[0] - pad, 0), min(c[-1] + pad + 1, self.W)))

    def paint(self, mask, colour):
        ys, xs = self._bb(mask)
        a = np.clip(mask[ys, xs], 0, 1)[..., None]
        self.cartoon[ys, xs] = self.cartoon[ys, xs] * (1 - a) + self._col(colour) * a

    def shade(self, mask, c0, c1, p0, p1, gamma=1.0):
        """linear gradient c0 at p0 -> c1 at p1, inside mask"""
        ys, xs = self._bb(mask)
        yy, xx = np.mgrid[ys, xs].astype(np.float32)
        d = np.array(p1, np.float32) - np.array(p0, np.float32)
        t = np.clip(((xx - p0[0]) * d[0] + (yy - p0[1]) * d[1]) / (d @ d + 1e-6), 0, 1) ** gamma
        col = self._col(c0) * (1 - t[..., None]) + self._col(c1) * t[..., None]
        a = np.clip(mask[ys, xs], 0, 1)[..., None]
        self.cartoon[ys, xs] = self.cartoon[ys, xs] * (1 - a) + col * a

    def sinopia(self, mask=None, pts=None, width=3.0, strength=0.75):
        """red-ochre underdrawing on the wet bed: the outline of a mask, or a brushed line through pts"""
        if mask is None:
            mask = self.band(spline(pts, 8) if len(pts) > 2 else pts, width)
            ys, xs = self._bb(mask, 2)
            line = mask[ys, xs]
        else:
            ys, xs = self._bb(mask, 6)
            b = blur(np.clip(mask[ys, xs], 0, 1), 1.2)
            gy, gx = np.gradient(b)
            line = np.clip(np.hypot(gx, gy) * width * 1.6, 0, 1)
        if not hasattr(self, '_brk'):
            self._brk = 0.55 + 0.45 * smoothstep(0.3, 0.6, noise2d(self.H, self.W, 60, 3, self._seed()))
        self.sin[ys, xs] = np.maximum(self.sin[ys, xs], line * self._brk[ys, xs] * strength)

    # ------------------------------------------------------------ stones
    def _stone(self, colour, material, stones, rgb_sample=None):
        """pick a stone out of the box: explicit name / hex, or the nearest stone to the cartoon colour"""
        if colour is not None:
            if isinstance(colour, str) and colour in self.box:
                base = hexc(self.box[colour][0]); mat = MATERIALS.index(self.box[colour][1])
            else:
                base = self._col(colour)
                mat = int(self._palmat[np.argmin(((self._pal - base) ** 2).sum(1))])
        else:
            idx = np.arange(len(self._names)) if stones is None else np.array([self._names.index(s) for s in stones])
            c = _opp(rgb_sample) + self.rng.normal(0, 1, 3) * np.array([self.dither, self.dither * 0.3, self.dither * 0.3])
            dd = ((self._opp[idx] - c) ** 2 * np.array([1.0, 2.6, 2.6])).sum(1)
            k = idx[int(np.argmin(dd))]
            base, mat = self._pal[k], int(self._palmat[k])
        if material is not None: mat = MATERIALS.index(material)
        rgb = np.clip(base * self.rng.uniform(0.94, 1.05) + self.rng.normal(0, 0.011, 3), 0, 1)
        return rgb.astype(np.float32), mat

    def _patch(self, P, scale=1.0, H=None, W=None):
        """bbox and signed distance (px, positive inside) of convex polygon P, at pixel centres"""
        H = H or self.H; W = W or self.W
        P = np.asarray(P, np.float32) * scale
        x0 = max(int(np.floor(P[:, 0].min())) - 1, 0); x1 = min(int(np.ceil(P[:, 0].max())) + 1, W)
        y0 = max(int(np.floor(P[:, 1].min())) - 1, 0); y1 = min(int(np.ceil(P[:, 1].max())) + 1, H)
        if x1 <= x0 or y1 <= y0: return None
        X = np.arange(x0, x1, dtype=np.float32)[None, :] + 0.5
        Y = np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5
        Q = np.roll(P, -1, 0); E = Q - P
        area = float((P[:, 0] * Q[:, 1] - Q[:, 0] * P[:, 1]).sum())
        sg = 1.0 if area > 0 else -1.0
        sd = None
        for k in range(len(P)):
            ln = float(np.hypot(E[k, 0], E[k, 1]))
            if ln < 1e-4: continue
            d = sg * (E[k, 0] * (Y - P[k, 1]) - E[k, 1] * (X - P[k, 0])) / ln
            sd = d if sd is None else np.minimum(sd, d)
        if sd is None: return None
        return y0, x0, sd

    def _set(self, P, colour=None, material=None, stones=None, keep=0.55, height=None):
        """try to set one stone with outline P; refuse it when it would sit mostly on stones already set"""
        r = self._patch(P)
        if r is None: return False
        y0, x0, sd = r
        ins = sd > 0
        cnt = int(ins.sum())
        if cnt < 3: return False
        sub = self.occ[y0:y0 + sd.shape[0], x0:x0 + sd.shape[1]]
        over = int((sub & ins).sum())
        if over > (1 - keep) * cnt: return False
        cx, cy = P[:, 0].mean(), P[:, 1].mean()
        if 0 <= int(cy) < self.H and 0 <= int(cx) < self.W and self.occ[int(cy), int(cx)] and over > 0.12 * cnt:
            return False
        sample = None
        if colour is None:
            sample = self.cartoon[y0:y0 + sd.shape[0], x0:x0 + sd.shape[1]][ins & ~sub].mean(0) if cnt > over else \
                self.cartoon[int(np.clip(cy, 0, self.H - 1)), int(np.clip(cx, 0, self.W - 1))]
        rgb, mat = self._stone(colour, material, stones, sample)
        sub |= ins
        self.poly.append(np.asarray(P, np.float32)); self.rgb.append(rgb); self.mat.append(mat)
        self.ht.append(float(height if height is not None else self.rng.uniform(1.5, 2.0)))
        self.tilt.append(self.rng.normal(0, 0.06, 2).astype(np.float32))
        return True

    def _rough(self, Q, size, chip=0.2, jit=0.045):
        """hand-cut: jitter the corners, sometimes knock one off, turn the stone a hair"""
        Q = np.asarray(Q, np.float32) + self.rng.normal(0, jit * size, (len(Q), 2)).astype(np.float32)
        c = Q.mean(0)
        a = np.radians(self.rng.normal(0, 1.6)); R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]], np.float32)
        Q = (Q - c) @ R.T + c
        if len(Q) == 4 and self.rng.random() < chip:
            k = int(self.rng.integers(4)); f = self.rng.uniform(0.1, 0.24)
            p, a_, b_ = Q[k], Q[k - 1], Q[(k + 1) % 4]
            Q = np.concatenate([Q[:k], [p + (a_ - p) * f, p + (b_ - p) * f], Q[k + 1:]])
        return Q

    def _convex_ok(self, Q):
        Q = np.asarray(Q); R = np.roll(Q, -1, 0); S = np.roll(Q, -2, 0)
        cr = (R[:, 0] - Q[:, 0]) * (S[:, 1] - R[:, 1]) - (R[:, 1] - Q[:, 1]) * (S[:, 0] - R[:, 0])
        return bool((cr > -1e-3).all() or (cr < 1e-3).all())

    def _split(self, P, closed, ang=0.75, k=3):
        """cut a row at its sharp corners (a mosaicist turns a corner with a new stone, not a bent one)"""
        n = len(P)
        if n < 2 * k + 3: return [(P, closed)]
        idx = np.arange(n)
        if closed:
            a, b = P[(idx - k) % n], P[(idx + k) % n]
        else:
            a, b = P[np.clip(idx - k, 0, n - 1)], P[np.clip(idx + k, 0, n - 1)]
        v1, v2 = P - a, b - P
        turn = np.abs(np.arctan2(v1[:, 0] * v2[:, 1] - v1[:, 1] * v2[:, 0], (v1 * v2).sum(1)))
        if not closed: turn[:k + 1] = 0; turn[-k - 1:] = 0
        hot = turn > ang
        if not hot.any(): return [(P, closed)]
        cuts = []
        i = 0
        while i < n:
            if hot[i]:
                j = i
                while j + 1 < n and hot[j + 1]: j += 1
                cuts.append(i + int(np.argmax(turn[i:j + 1]))); i = j + 1
            else:
                i += 1
        if closed:
            P = np.concatenate([P[cuts[0]:], P[:cuts[0] + 1]]); cuts = [c - cuts[0] if c >= cuts[0] else c + n - cuts[0] for c in cuts] + [n]
            return [(P[cuts[i]:cuts[i + 1] + 1], False) for i in range(len(cuts) - 1)]
        cuts = [0] + cuts + [n - 1]
        return [(P[cuts[i]:cuts[i + 1] + 1], False) for i in range(len(cuts) - 1)]

    def _row(self, P, closed, size, across=None, colour=None, material=None, stones=None, var=0.2,
             ridge=None, level=None, keep=0.55, chip=0.2, jit=0.045, height=None):
        """cut one row (polyline P) into stones and try to set each of them"""
        across = size if across is None else across
        if len(P) < 2: return 0
        for Q, cl in self._split(P, closed):
            if cl: Q = np.concatenate([Q, Q[:1]])
            seg = np.linalg.norm(np.diff(Q, axis=0), axis=1)
            s = np.concatenate([[0], np.cumsum(seg)]); L = float(s[-1])
            pitch = size + self.gap
            if L < 0.45 * size: continue
            n = max(1, int(round(L / pitch)))
            if not cl and L < 0.8 * pitch: n = 1
            lens = self.rng.uniform(1 - var, 1 + var, n); lens *= L / lens.sum()
            b = np.concatenate([[0], np.cumsum(lens)]) + (self.rng.uniform(0, lens[0]) if cl else 0)
            kk = 2
            tx = np.gradient(Q[:, 0]); ty = np.gradient(Q[:, 1])
            if len(Q) > 2 * kk + 1:
                ker = np.ones(2 * kk + 1) / (2 * kk + 1)
                tx = np.convolve(np.pad(tx, kk, mode='edge'), ker, 'valid'); ty = np.convolve(np.pad(ty, kk, mode='edge'), ker, 'valid')
            tl = np.hypot(tx, ty) + 1e-6; tx, ty = tx / tl, ty / tl

            def at(u):
                u = u % L if cl else np.clip(u, 0, L)
                return (np.array([np.interp(u, s, Q[:, 0]), np.interp(u, s, Q[:, 1])], np.float32),
                        np.array([-np.interp(u, s, ty), np.interp(u, s, tx)], np.float32))

            for i in range(n):
                a0, a1 = b[i] + self.gap / 2, b[i + 1] - self.gap / 2
                if a1 - a0 < 0.3 * size: continue
                (p0, n0), (p1, n1) = at(a0), at(a1)
                n0 /= np.linalg.norm(n0) + 1e-6; n1 /= np.linalg.norm(n1) + 1e-6
                hw = (across / 2) * self.rng.uniform(0.92, 1.03)
                wi = wo = hw
                if ridge is not None:                                       # don't cross the figure's spine
                    pm = (p0 + p1) / 2
                    g = ridge(pm)
                    if g is not None:
                        room = g - level - self.gap / 2                     # distance to the ridge, inward side
                        nxt = g - (level + size + self.gap)                 # is there another row inside?
                        if nxt < 0.3 * size:
                            wi = float(np.clip(room, 0.3 * size, 1.15 * size))
                        else:
                            wi = min(hw, max(room, 0.3 * size))
                # inward = toward higher field: decided by caller via sign of normals (ridge rows: +n is inward)
                Qd = np.array([p0 + n0 * wi, p1 + n1 * wi, p1 - n1 * wo, p0 - n0 * wo], np.float32)
                if not self._convex_ok(Qd):
                    m = (Qd[0] + Qd[1]) / 2; Qd = np.array([m, Qd[2], Qd[3]], np.float32)
                Qd = self._rough(Qd, size, chip=chip, jit=jit)
                if not self._convex_ok(Qd): continue
                self._set(Qd, colour, material, stones, keep, height)
        return 1

    def _obstacle(self, y0, y1, x0, x1):
        o = self.occ[y0:y1, x0:x1].astype(np.float32)
        return blur(o, self.gap * 0.5) > 0.12

    def _bbox(self, mask, pad):
        ys, xs = np.nonzero(mask > 0.5)
        if len(ys) == 0: return None
        return (max(ys.min() - pad, 0), min(ys.max() + pad + 1, self.H), max(xs.min() - pad, 0), min(xs.max() + pad + 1, self.W))

    def _ridge_fn(self, din, y0, x0, size):
        M = maxfilt(np.where(np.isfinite(din), din, 0), int(2 * (size + self.gap)) + 2)   # must see past the next row

        def g(p):
            x, y = int(p[0]) - x0, int(p[1]) - y0
            if 0 <= y < M.shape[0] and 0 <= x < M.shape[1]: return float(M[y, x])
            return None
        return g

    @staticmethod
    def _orient(P, f):
        """reverse a row if needed so that its left normal (-ty, tx) points up the field (inward for figures)"""
        n = len(P)
        if n < 3: return P
        idx = np.linspace(1, n - 2, min(9, n - 2)).astype(int)
        t = P[idx + 1] - P[idx - 1]; t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-t[:, 1], t[:, 0]], 1)
        H, W = f.shape
        vote = 0.0
        for p, q in zip(P[idx], nrm):
            a, b = p + q * 1.6 - 0.5, p - q * 1.6 - 0.5
            ia, ib = (int(round(a[1])), int(round(a[0]))), (int(round(b[1])), int(round(b[0])))
            if 0 <= ia[0] < H and 0 <= ia[1] < W and 0 <= ib[0] < H and 0 <= ib[1] < W:
                fa, fb = f[ia], f[ib]
                if np.isfinite(fa) and np.isfinite(fb): vote += np.sign(fa - fb)
        return P[::-1].copy() if vote < 0 else P

    def _lay_field(self, field, y0, x0, size, levels=None, colour=None, material=None, stones=None, ridge=None,
                   var=0.2, keep=0.55, across=None, chip=0.2, height=None, order=None):
        """trace the iso-lines of `field` (crop at y0, x0) one stone-pitch apart and lay a row on each"""
        pitch = size + self.gap
        lines = iso_lines(field, pitch, 0.5)
        lines.sort(key=lambda t: t[0])
        if order == 'random':
            self.rng.shuffle(lines)
        for k, P, closed in lines:
            if levels is not None and not (levels[0] <= k < levels[1]): continue
            P = self._orient(P, field) + np.array([x0, y0], np.float32)
            col = colour(k) if callable(colour) else colour
            self._row(P, closed, size, across, col, material, stones, var, ridge,
                      (k + 0.5) * pitch if ridge is not None else None, keep, chip, height=height)

    # ------------------------------------------------------------ laying methods
    def point(self, x, y, colour, size=None, shape='square', angle=0.0, material=None):
        """set one stone by hand: an eye ('round'), a highlight, a stop between words ('tri')"""
        size = size or self.tile
        a = np.radians(angle)
        if shape == 'round':
            t = np.linspace(0, 2 * np.pi, 9, endpoint=False) + a
            Q = np.stack([x + np.cos(t) * size / 2, y - np.sin(t) * size / 2], 1)
        elif shape == 'tri':
            t = np.radians([90, 210, 330]) + a
            Q = np.stack([x + np.cos(t) * size * 0.6, y - np.sin(t) * size * 0.6], 1)
        else:
            t = np.radians([45, 135, 225, 315]) + a
            Q = np.stack([x + np.cos(t) * size * 0.7, y - np.sin(t) * size * 0.7], 1)
        Q = self._rough(Q, size, chip=0.0, jit=0.04)
        return self._set(Q.astype(np.float32), colour, material, None, keep=0.5)

    def line(self, pts, colour=None, size=None, across=None, smooth=True, material=None, keep=0.5, var=0.15, stones=None):
        """one row of stones along a path: a contour line, a fin ray, a mast, a net cord, a letter stroke.
        colour=None takes each stone's colour from the cartoon (a tentacle's spine row)"""
        size = size or self.tile * 0.8
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 10)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
        n = max(2, int(s[-1]) + 1); u = np.linspace(0, s[-1], n)
        P = np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1).astype(np.float32)
        self._row(P, False, size, across, colour, material, stones, var, keep=keep, chip=0.15)

    def outline(self, mask, colour='black', rows=1, size=None, material=None, stones=None):
        """the first row(s) of a figure, just inside its edge: the dark contour line of Roman figures"""
        size = size or self.tile * 0.8
        pitch = size + self.gap
        bb = self._bbox(mask, 4)
        if bb is None: return
        y0, y1, x0, x1 = bb
        m = mask[y0:y1, x0:x1] > 0.5
        din = edt(~m, reach=pitch * (rows + 2)) - 0.5
        f = np.where(m & ~self._obstacle(y0, y1, x0, x1), din, np.nan).astype(np.float32)
        f[din > pitch * (rows + 0.9)] = np.nan
        self._lay_field(f, y0, x0, size, levels=(0, rows), colour=colour, material=material, stones=stones,
                        ridge=self._ridge_fn(np.where(m, din, 0), y0, x0, size))

    def fill(self, mask, size=None, stones=None, material=None, wrap=True, tuck=True, colour=None):
        """rows that follow the figure's outline inward (opus vermiculatum); colours come from the cartoon"""
        size = size or self.tile * 0.8
        pitch = size + self.gap
        bb = self._bbox(mask, 4)
        if bb is None: return
        y0, y1, x0, x1 = bb
        m = mask[y0:y1, x0:x1] > 0.5
        din = edt(~m) - 0.5
        obs = self._obstacle(y0, y1, x0, x1)
        field = din
        if wrap and (obs & m).any():
            dob = edt(obs & m) - 0.5
            field = np.minimum(din, dob + 0.0)
        f = np.where(m & ~obs, field, np.nan).astype(np.float32)
        self._lay_field(f, y0, x0, size, colour=colour, material=material, stones=stones,
                        ridge=self._ridge_fn(np.where(m, field, 0), y0, x0, size))
        if tuck: self.tuck(mask, size, stones=stones, material=material, colour=colour)

    def figure(self, mask, outline='black', size=None, stones=None, rows=1, wrap=True):
        if outline is not None: self.outline(mask, outline, rows, size)
        self.fill(mask, size, stones, wrap=wrap)

    def halo(self, region=None, rows=2, size=None, stones=None, colour=None, around=None):
        """background rows that hug the outline of what is already set (or of `around`), outside it"""
        size = size or self.tile
        pitch = size + self.gap
        reg = np.ones((self.H, self.W), bool) if region is None else region > 0.5
        src = self.occ if around is None else (around > 0.5)
        bb = self._bbox(reg.astype(np.float32), 2)
        if bb is None: return
        y0, y1, x0, x1 = bb
        k = 2                                                       # distance field at half resolution
        s_ = src[y0:y1, x0:x1]
        dsmall = edt(s_[::k, ::k], reach=pitch * (rows + 2) / k) * k
        d = np.asarray(Image.fromarray(dsmall.astype(np.float32)).resize((x1 - x0, y1 - y0), Image.BILINEAR), np.float32)
        d = np.maximum(d - self.gap * 0.5 - 0.5, 0)
        obs = self._obstacle(y0, y1, x0, x1)
        f = np.where(reg[y0:y1, x0:x1] & ~obs & (d < pitch * (rows + 0.6)), d, np.nan).astype(np.float32)
        self._lay_field(f, y0, x0, size, levels=(0, rows), colour=colour, stones=stones, var=0.18)

    def rows(self, region, size=None, angle=0.0, wobble=0.0, field=None, stones=None, colour=None, tuck=True,
             var=0.18, material=None):
        """background in parallel rows (opus tessellatum); `field` (H, W) lays rows along its iso-lines instead"""
        size = size or self.tile
        reg = region > 0.5
        bb = self._bbox(region, 2)
        if bb is None: return
        y0, y1, x0, x1 = bb
        if field is None:
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            a = np.radians(angle)
            f = -xx * np.sin(a) + yy * np.cos(a)
            if wobble:
                f = f + wobble * (noise2d(y1 - y0, x1 - x0, 300, 3, self._seed()) - 0.5) * 2
        else:
            f = field[y0:y1, x0:x1].astype(np.float32)
        obs = self._obstacle(y0, y1, x0, x1)
        f = np.where(reg[y0:y1, x0:x1] & ~obs, f, np.nan).astype(np.float32)
        self._lay_field(f, y0, x0, size, colour=colour, stones=stones, var=var, material=material)
        if tuck: self.tuck(region, size, stones=stones, colour=colour, material=material)

    def frame(self, x0, y0, x1, y1, width, size=None, stones=None, colour=None, tuck=True):
        """rows running parallel to the four sides of a rectangle band (borders), mitred at the corners"""
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        d = np.minimum(np.minimum(xx + 0.5 - x0, x1 - xx - 0.5), np.minimum(yy + 0.5 - y0, y1 - yy - 0.5))
        reg = ((d >= 0) & (d < width)).astype(np.float32)
        self.rows(reg, size, field=d, stones=stones, colour=colour, tuck=tuck)
        return reg

    def tuck(self, region, size=None, stones=None, colour=None, material=None, small=0.32):
        """fill the holes that are left with pieces cut to fit, biggest holes first"""
        size = size or self.tile
        bb = self._bbox(region, 2)
        if bb is None: return
        y0, y1, x0, x1 = bb
        free = (region[y0:y1, x0:x1] > 0.5) & ~self._obstacle(y0, y1, x0, x1)
        if not free.any(): return
        df = edt(~free, reach=size * 2)
        st = max(2, int(size * 0.45))
        gy, gx = np.mgrid[st // 2:y1 - y0:st, st // 2:x1 - x0:st]
        gy = np.clip(gy + self.rng.integers(-st // 3, st // 3 + 1, gy.shape), 0, y1 - y0 - 1)
        gx = np.clip(gx + self.rng.integers(-st // 3, st // 3 + 1, gx.shape), 0, x1 - x0 - 1)
        dv = df[gy, gx]
        ok = dv > (small * size + self.gap) / 2
        gy, gx, dv = gy[ok], gx[ok], dv[ok]
        for i in np.argsort(-dv):
            y, x = int(gy[i]) + y0, int(gx[i]) + x0
            if self.occ[y, x]: continue
            s = float(np.clip(2 * dv[i] - self.gap, small * size, size))
            a = self.rng.uniform(0, np.pi / 2)
            t = np.array([0.25, 0.75, 1.25, 1.75]) * np.pi + a
            Q = np.stack([x + 0.5 + np.cos(t) * s * 0.7, y + 0.5 + np.sin(t) * s * 0.7], 1)
            Q = self._rough(Q, s, chip=0.2)
            self._set(Q.astype(np.float32), colour, material, stones, keep=0.7)

    # ------------------------------------------------------------ inscriptions
    def text_width(self, text, height, spacing=0.32):
        w = 0.0
        for ch in text:
            if ch == ' ': w += 0.5 * height; continue
            if ch in '·.': w += 0.36 * height; continue
            st = LETTERS.get(ch.upper())
            if st is None: continue
            w += (max(p[0] for s_ in st for p in s_) + spacing) * height
        return w - spacing * height

    def letters(self, text, x, y, height, colour='black', size=None, spacing=0.32, anchor='m'):
        """Roman capitals, each stroke one row of stones; '·' is a triangular stop. y is the cap top"""
        size = size or max(5.0, height / 6.2)
        w = self.text_width(text, height, spacing)
        cx = x - w / 2 if anchor == 'm' else x
        for ch in text:
            if ch == ' ': cx += 0.5 * height; continue
            if ch in '·.':
                self.point(cx + 0.14 * height, y + 0.55 * height, colour, size * 1.05, 'tri', angle=180)
                cx += 0.36 * height; continue
            st = LETTERS.get(ch.upper())
            if st is None: continue
            for s_ in st:
                P = [(cx + px * height, y + py * height) for px, py in s_]
                self.line(P, colour, size, smooth=ch.upper() in _CURVED or len(P) > 6, keep=0.45, var=0.12)
            cx += (max(p[0] for s_ in st for p in s_) + spacing) * height

    def tabula(self, x0, y0, x1, y1, lines, ear=60, frame=('black', 'red'), ground=('white', 'bone'), size=None):
        """tabula ansata: a framed plaque with a dovetail handle each side; lines = [(text, height, colour)]"""
        size = size or self.tile * 0.75
        cy = (y0 + y1) / 2; hh = (y1 - y0) / 2
        plaque = self.poly_mask([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        ears = []
        for sgn, xe in ((-1, x0), (1, x1)):
            e = [(xe - sgn * 2, cy), (xe + sgn * ear, cy - hh * 0.8), (xe + sgn * ear * 0.78, cy), (xe + sgn * ear, cy + hh * 0.8)]
            ears.append(self.poly_mask(e))
        shape = np.clip(plaque + ears[0] + ears[1], 0, 1)
        total = sum(h for _, h, _ in lines) * 1.0 + (len(lines) - 1) * lines[0][1] * 0.45
        ty = cy - total / 2
        for text, h, col in lines:
            self.letters(text, (x0 + x1) / 2, ty, h, col, size=max(5.6, h / 5.6))
            ty += h * 1.45
        self.outline(shape, frame[0], 1, size)
        if len(frame) > 1: self.outline(shape, frame[1], 2, size)
        inner = np.clip(plaque - self.everything(), 0, 1)
        self.rows(inner, size * 1.05, stones=list(ground))
        for e in ears:
            em = e * (1 - self.everything())
            self.fill(em, size, stones=[frame[1] if len(frame) > 1 else frame[0]], tuck=False)
            self.tuck(em, size, stones=[frame[1] if len(frame) > 1 else frame[0]], small=0.55)
        return shape

    # ------------------------------------------------------------ time
    def lacuna(self, mask, ragged=0.5):
        """the stones in this patch are lost; their sockets stay printed in the old bed"""
        m = mask > 0.5
        edge = (blur(mask.astype(np.float32), 6) > 0.12) & ~m
        for k, P in enumerate(self.poly):
            cx, cy = P.mean(0)
            yi, xi = int(np.clip(cy, 0, self.H - 1)), int(np.clip(cx, 0, self.W - 1))
            if m[yi, xi] or (edge[yi, xi] and self.rng.random() < ragged):
                self.lost.append(k)

    def crack(self, pts, width=1.3):
        """a settling crack: a dark hairline through stones and joints, one side sunk a little"""
        P = np.asarray(pts, np.float32)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
        n = max(8, int(s[-1] / 3)); u = np.linspace(0, s[-1], n)
        x, y = np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])
        d = np.stack([np.gradient(x), np.gradient(y)], 1); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        w = fbm1d(n, 12, 4, self._seed()) * 5 + fbm1d(n, 3, 2, self._seed()) * 1.5
        Q = np.stack([x - d[:, 1] * w, y + d[:, 0] * w], 1)
        self.cracks.append((Q, width))

    def patina(self, amount=1.0):
        self.patina_amt = amount

    # ------------------------------------------------------------ rendering
    def _textures(self, ss):
        if ss in self._tex: return self._tex[ss]
        r = np.random.default_rng(self.seed + 991)
        N = 256 * ss
        mott = (noise2d(N, N, 9 * ss, 3, self.seed + 1) - 0.5) * 2
        mott = mott * 0.7 + (r.random((N, N)).astype(np.float32) - 0.5) * 0.6
        vy, vx = np.mgrid[0:N, 0:N].astype(np.float32)
        warp = noise2d(N, N, 40 * ss, 3, self.seed + 2) * 40 * ss
        vein = np.abs(np.sin((vx * 0.6 + vy * 0.8 + warp) / (11.0 * ss)))
        vein = 1 - smoothstep(0.0, 0.07, vein)
        vein *= smoothstep(0.35, 0.7, noise2d(N, N, 60 * ss, 2, self.seed + 3))
        pits = np.zeros((N, N), np.float32)
        for _ in range(int(900)):
            x, y, rr = r.integers(0, N), r.integers(0, N), r.uniform(0.5, 1.6) * ss
            y0, y1, x0, x1 = max(y - 4 * ss, 0), min(y + 4 * ss, N), max(x - 4 * ss, 0), min(x + 4 * ss, N)
            pits[y0:y1, x0:x1] = np.maximum(pits[y0:y1, x0:x1], np.exp(-((vy[y0:y1, x0:x1] - y) ** 2 + (vx[y0:y1, x0:x1] - x) ** 2) / (2 * rr * rr)))
        sand = (r.random((N, N)).astype(np.float32) - 0.5)
        sand = sand * 0.6 + (noise2d(N, N, 3 * ss, 2, self.seed + 4) - 0.5) * 0.8
        self._tex[ss] = (mott.astype(np.float32), vein.astype(np.float32), pits.astype(np.float32), sand.astype(np.float32))
        return self._tex[ss]

    def _render(self, ss, n=None, aged=True):
        H, W = self.H * ss, self.W * ss
        n = len(self.poly) if n is None else n
        lost = set(self.lost) if aged else set()
        idm = np.zeros((H, W), np.int32)
        dep = np.zeros((H, W), np.float32)
        block = np.zeros((H, W), bool)
        sock = np.zeros((H, W), np.float32)
        rr = 0.7 * self.gap * ss
        for k in range(n):
            r = self._patch(self.poly[k], ss, H, W)
            if r is None: continue
            y0, x0, sd = r
            sl = (slice(y0, y0 + sd.shape[0]), slice(x0, x0 + sd.shape[1]))
            if k in lost:
                np.maximum(sock[sl], smoothstep(-0.5 * ss, 1.0 * ss, sd), out=sock[sl])
                continue
            ins = (sd > 0) & ~block[sl]
            idm[sl][ins] = k + 1
            dep[sl][ins] = sd[ins]
            block[sl] |= sd > -rr
        del block
        N = n + 1
        RGB = np.zeros((N, 3), np.float32); MAT = np.zeros(N, np.int32); HT = np.zeros(N, np.float32)
        TL = np.zeros((N, 2), np.float32); OFF = np.zeros((N, 2), np.int32); VEIN = np.zeros(N, np.float32)
        if n:
            RGB[1:] = np.array(self.rgb[:n]); MAT[1:] = self.mat[:n]; HT[1:] = self.ht[:n]; TL[1:] = np.array(self.tilt[:n])
            rr_ = np.random.default_rng(self.seed + 5)
            OFF[1:] = rr_.integers(0, 256 * ss, (n, 2)); VEIN[1:] = (rr_.random(n) < 0.45) * rr_.uniform(0.3, 1.0, n)
        mott, vein, pits, sand = self._textures(ss)
        T = mott.shape[0]
        # bed / sinopia / crack / weather maps stay at 1x and are enlarged one strip at a time (keeps memory low)
        crk1 = None
        if aged and self.cracks:
            im = Image.new('L', (self.W * 2, self.H * 2), 0); d = ImageDraw.Draw(im)
            for Q, w in self.cracks:
                d.line([tuple(p) for p in (Q * 2).tolist()], fill=255, width=max(1, int(round(w * 2))), joint='curve')
            crk1 = blur(np.asarray(im.resize((self.W, self.H), Image.BILINEAR), np.float32) / 255, 0.35)
        lowf1 = np.asarray(Image.fromarray(noise2d(self.H // 4, self.W // 4, 30, 4, self.seed + 7)).resize((self.W, self.H), Image.BILINEAR), np.float32)

        def up(a1, ya, yb):
            c = a1[ya // ss:(yb + ss - 1) // ss]
            if ss == 1: return c
            return np.asarray(Image.fromarray(c).resize((W, c.shape[0] * ss), Image.BILINEAR), np.float32)[:yb - ya]
        out = np.zeros((self.H, self.W, 3), np.float32)
        strip = 96 * ss; mg = 18 * ss                                    # thin strips keep memory low
        L = self.L; Hv = L + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        for ys in range(0, H, strip):
            ya, yb = max(ys - mg, 0), min(ys + strip + mg, H)
            ids = idm[ya:yb]; tile = ids > 0
            lf = up(lowf1, ya, yb); sn_ = up(self.sin, ya, yb)
            ck = up(crk1, ya, yb) if crk1 is not None else None
            yy, xx = np.mgrid[ya:yb, 0:W].astype(np.int32)
            # chamfer distance to any id change, so cut-to-fit edges are worn too
            ch = np.where(tile, 6.0 * ss, 0).astype(np.float32)
            edge = np.zeros_like(tile)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                edge |= ids != _shift_fill(ids, dy, dx, 0)
            ch[edge & tile] = 0.5
            for _ in range(int(3 * ss)):
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ch = np.minimum(ch, _shift_fill(ch, dy, dx, 0) + 1)
            dd = np.minimum(dep[ya:yb], ch)
            Rb = 1.7 * ss
            prof = smoothstep(0, Rb, dd)
            dome = smoothstep(0, 5 * Rb, dd)
            ht = HT[ids]
            gs = sand[yy % T, xx % T]
            near = blur(tile.astype(np.float32), 1.6 * ss)
            grouted = near > 0.06
            sk = sock[ya:yb]
            oldbed = (blur(sk, 3 * ss) > 0.02) if aged else np.zeros_like(tile)
            h_grout = 0.35 + 0.3 * near + 0.07 * gs
            h_bed = 0.7 + 0.06 * gs + 0.5 * (lf - 0.5)
            h_old = -0.2 + 0.3 * gs - 0.9 * sk
            hfield = np.where(tile, ht * (0.86 * prof + 0.14 * dome), np.where(oldbed, h_old, np.where(grouted, h_grout, h_bed)))
            if ck is not None:
                hfield = hfield - 1.6 * ck
            gy, gx = np.gradient(hfield)
            gx *= 1.0; gy *= 1.0
            tlt = TL[ids] * (prof * 0.9 + 0.1)[..., None] * tile[..., None]
            nx = -gx * ss + tlt[..., 0]; ny = -gy * ss + tlt[..., 1]; nz = np.ones_like(nx)
            nl = np.sqrt(nx * nx + ny * ny + 1); nx /= nl; ny /= nl; nz /= nl
            lam = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
            shd = 0.45 + 0.55 * lam / L[2]
            sh = height_shadow(hfield * ss, light=tuple(L), reach=7 * ss, step=max(1.0, 0.75 * ss), soft=0.9 * ss)
            ao = np.clip((blur(hfield, 1.2 * ss) - hfield) / 1.2, 0, 1) * 0.6 + np.clip((blur(hfield, 3.5 * ss) - hfield) / 2.0, 0, 1) * 0.4
            # albedo
            mt = MAT[ids]
            oy, ox = OFF[ids, 0], OFF[ids, 1]
            ty_, tx_ = (yy + oy) % T, (xx + ox) % T
            alb = RGB[ids].copy()
            mo = mott[ty_, tx_] * _MOTTLE[mt]
            alb *= (1 + mo)[..., None]
            vv = vein[ty_, tx_] * VEIN[ids] * (mt == 1)
            alb *= (1 - 0.22 * vv)[..., None]
            pp = pits[ty_, tx_] * ((mt == 0) | (mt == 3)) * 0.35 + pits[(ty_ + 97) % T, tx_] * (mt == 2) * 0.5
            alb *= (1 - 0.3 * pp)[..., None]
            gcol = self.grout * (1 + 0.16 * gs)[..., None]
            if aged and self.patina_amt:                                     # dirt settles in patches, not everywhere
                dirt = smoothstep(0.45, 0.85, lf) * 0.26 * self.patina_amt
                gcol = gcol * (1 - dirt)[..., None]
            bcol = self.bed * (1 + 0.07 * gs + 0.06 * (lf - 0.5))[..., None]
            sn = sn_[..., None]
            bcol = bcol * (1 - sn * 0.72) + hexc(SINOPIA) * sn * 0.72
            ocol = hexc('#8b7b63') * (1 + 0.16 * gs + 0.2 * (lf - 0.5))[..., None] * (1 - 0.22 * sk)[..., None]
            nont = np.where(oldbed[..., None], ocol, np.where(grouted[..., None], gcol, bcol))
            alb = np.where(tile[..., None], alb, nont)
            if ck is not None:
                alb *= (1 - 0.75 * np.clip(ck * 1.4, 0, 1))[..., None]
            nh = np.clip(nx * Hv[0] + ny * Hv[1] + nz * Hv[2], 0, 1)
            spec = np.where(tile, _SPEC[mt] * nh ** _GLOSS[mt], 0.01 * nh ** 6)
            if aged and self.patina_amt:
                spec *= 1 - 0.5 * self.patina_amt * smoothstep(0.45, 0.85, lf)
            col = alb * (shd * (1 - 0.32 * ao) * (1 - 0.22 * sh))[..., None] + spec[..., None]
            a0, a1 = ys - ya, ys - ya + min(strip, H - ys)
            c = col[a0:a1]
            h_, w_ = c.shape[0] // ss, c.shape[1] // ss
            out[ys // ss:ys // ss + h_] = c[:h_ * ss, :w_ * ss].reshape(h_, ss, w_, ss, 3).mean((1, 3))
        # a photograph of a floor: light falls off from the upper left, a touch of warmth
        yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        r2 = ((xx - self.W * 0.35) / self.W) ** 2 + ((yy - self.H * 0.3) / self.H) ** 2
        out *= (1.05 - 0.2 * r2)[..., None]
        out = np.clip(out, 0, 1) ** np.array([0.97, 1.0, 1.05], np.float32)
        return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))

    # ------------------------------------------------------------ output
    def stage(self, name):
        """remember how far the work has got; rendered (at stage_ss) only when save() gets a stages_dir"""
        self.stages.append((name, len(self.poly), bool(self.lost or self.cracks or self.patina_amt)))

    def save(self, path, stages_dir=None, quality=88):
        """the picture at ss x supersampling; with stages_dir also every stage, and the finished floor again, at
        stage_ss -- all snapshots at one resolution, so the animation's last cross-fade only changes what aged"""
        img = self._render(self.ss, aged=True)
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, n, aged) in enumerate(self.stages):
                self._render(self.stage_ss, n, aged).save(f"{stages_dir}/{i:02d}_{name}.png")
            last = img if self.stage_ss == self.ss else self._render(self.stage_ss, aged=True)
            last.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
