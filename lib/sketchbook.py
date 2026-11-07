"""sketchbook — 手账线描 / Sketchbook Doodle: delicate ink lines, playful stripes of colour pencil, charming little
characters floating on a big warm page (numpy + Pillow only).

The look: a page from an illustrator's sketchbook. Warm off-white paper with a faint blush, mostly left empty; one
small character in the lower middle with two or three sparse props, everything lightly floating (no ground, no
background). The drawing is hair-thin dark ink that wobbles a little, tapers in and out and leaves gaps -- a contour
is one or two strokes that do not quite close. Hair is many separate fine strands that flow together, paper showing
between them. Faces are tiny and simple: closed arcs with a few lashes (or dot eyes), a short nose line, a small red
mouth and two round pink blush dots. Clothes are filled with playful stripes laid in colour pencil and marker -- red,
yellow, teal, orange, magenta, blue -- loose hand-drawn bands with streaky texture, white paper gaps between them,
edges that wander and overrun or fall short of the ink line. Props are drawn in thin coloured lines: single leaves
with vein hatching, small flowers, thin multi-line trees, a steam curl, a curled-up cat.

Physical model
  paper     A warm off-white with a faint blush: a fine equalised tooth `T` (used by the pencil and to break the ink a
            little), a very low mottle and a scatter of faint fibres. Most of the page stays bare.
  ink       A fine pen line. Every stroke is the drawn path smoothed, resampled at 1 px and pushed sideways by a slow
            hand wobble plus a tiny tremor; its width tapers in where the nib lands and out in a longer flick where it
            lifts, drifts +-12 % along the way, and its ink flow varies a little (some stretches greyer). `gaps` lifts
            the pen for a few px now and then; `contour()` draws a closed shape as one to three strokes that leave a
            gap or overlap at the joins. Strokes are drawn with per-run width and darkness into a 4x supersampled
            layer (Pillow), box-filtered down, broken a touch by the tooth and multiplied into the page (ink is
            transparent: colour under it stays, lines over colour stay dark).
  pencil    Colour is laid as colour pencil / marker: a coverage target (a band, a shape) is turned into strokes
            along a direction -- long streak noise along the stroke and a finer elongated grain -- and the pigment
            catches the tooth (grainy, white specks) or lies flatter (marker), `grain` mixing the two. Colours
            multiply, so a red band over a yellow one turns orange, as real pencil does.
  stripes   `stripes()` lays bands across a garment: band positions along a coordinate `s` (straight across an
            angle, bent into a smile with `bend`, or wrapped round a sleeve's centre-line with `path`), each band its
            own colour, width, small tilt, grain and pressure, its two edges wandering independently, and its ends
            re-found on a blurred copy of the garment mask with a threshold of its own -- so each band overruns the
            ink line a little or stops short of it, and the whole layer can slip a few px (`shift`).
  props     `leaf()` an ink or coloured outline with a midrib and paired veins (herringbone hatching), an optional
            pencil fill set slightly off the line, or veins reserved in white; `flower()` a scribbled rose, a daisy
            of petal loops or a pencil tulip; `tree()` a trunk of several thin parallel lines that part into
            branches and twigs, with optional blossom dots; `steam()` a fine rising curl; `ticks()` short marks
            (fur, grass); `squiggle()` a tiny spiral or sparkle doodle (never fake writing).
  faces     `eye_closed()` a little downward arc with lashes; `eye_dot()`; `mouth()` a small red bow; `blush()` a
            round pink dot with a slightly darker rim and a fine grain; `hair()` a lock of strands interpolated
            between guide curves, each with a coherent wave (neighbours wave together), its own length and a long
            tapering tip, plus a few strays.
  finish    `finish()` records a faint paper grain over everything and a very slight softening, applied in render
            (every stage snapshot matches).

API (canvas pixel coordinates; directions in degrees, 0 = to the right, 90 = down; colours are PAINTS names,
     '#rrggbb' or RGB triples)
  surface   Sketchbook(W, H, seed, keep_stages, stages_dir); paper(tone, tooth, mottle, fibres); finish(grain, soft)
  masks     poly(pts, smooth) / ellipse(cx, cy, rx, ry, rot) / blob(cx, cy, rx, ry, rough) / tube(path, w0, w1) ->
            canvas-sized float masks; tube_pts(path, w0, w1), ellipse_pts(...), closed_pts(pts) (outline points);
            soften(mask, sigma); grow(mask, px) (pass as `avoid` so a line stops short of what is in front)
  lines     ink(path, width, colour, alpha, wobble, tremor, taper, flow, grain, gaps, closed, clip, avoid);
            inks(paths, ...) (per-path lists allowed); contour(pts, pieces, gap, overlap, ...)
  colour    stripes(mask, colours, across, path, bend, band, gap, tilt, rough, overrun, grain, streak, pressure,
            shift, avoid); tint(mask, colour, angle, strength, grain, streak, hatch, spacing, overrun, shift);
            blush(cx, cy, r, colour, strength); dots(pts, r, colour)
  faces     eye_closed(cx, cy, w, sag, lashes, side, rot); eye_dot(cx, cy, r); mouth(cx, cy, w, h, rot);
            hair(guides, n, width, colour, wave, length, start, spread, stray, clip, avoid)
  props     leaf(base, tip, width, fill, line, veins, vein, bend, stem); flower(x, y, r, colour, kind, stem);
            tree(x, y, height, colour, lines, branches, lean, blossoms); steam(x, y, height, colour, sway, curl);
            ticks(mask, n, length, angle, colour); squiggle(x, y, size, colour, kind)
  output    render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 88, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from sketchbook import Sketchbook
    p = Sketchbook(1200, 1200, seed=3); p.finish(); p.paper()
    body = [(520, 700), (680, 700), (700, 900), (500, 900)]
    p.contour(body); p.stripes(p.poly(body, smooth=True), ['red', 'yellow', 'teal', 'orange'], across=90, bend=8)
    p.contour([(600, 560), (660, 610), (600, 680), (540, 610)])
    p.eye_closed(578, 615, 22); p.eye_closed(624, 615, 22); p.blush(570, 640, 13); p.blush(632, 640, 13)
    p.mouth(601, 655, 12, 5)
    p.leaf((800, 900), (860, 700), 70, fill='olive'); p.save('sketch.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, spline, noise2d, smoothstep, blob_pts

PAINTS = {
    # paper and inks
    'paper': '#f2e9e1', 'paper_light': '#f7f1ea', 'white': '#fbf8f3',
    'ink': '#24201e', 'ink_soft': '#3e3733', 'sepia': '#6a4f3e', 'graphite': '#7a736d', 'grey': '#b4ada6',
    'forest_ink': '#1f3326',
    # the stripe colours
    'red': '#e3322c', 'scarlet': '#d42a30', 'vermilion': '#ec5a2c', 'coral': '#f07c5c', 'orange': '#f39232',
    'yellow': '#f6cb2a', 'gold': '#efb21c', 'mustard': '#d7a425', 'teal': '#17a19c', 'turquoise': '#38b6c0',
    'aqua': '#86d0cf', 'blue': '#2f62b0', 'cobalt': '#2b4f9e', 'navy': '#243a70', 'sky': '#90bde0',
    'magenta': '#d8287b', 'pink': '#ef93ab', 'rose': '#e56a80', 'violet': '#7b5aa6',
    # faces
    'cheek': '#f08e8a', 'blush': '#ec7d74', 'lip': '#d8262b',
    # props
    'leaf': '#7f9c48', 'olive': '#a09a35', 'sage': '#98b894', 'moss': '#66803a', 'forest': '#2f5c3c',
    'terracotta': '#c9663e', 'ochre': '#c9913c', 'tan': '#d9b68c', 'wood': '#b98650', 'cream': '#f5e9d0',
    'ginger': '#e39646', 'stone': '#9c948c',
}


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _equalise(a):
    """rank-equalise to a uniform 0..1 distribution"""
    flat = a.ravel()
    o = np.argsort(flat, kind='stable')
    out = np.empty(flat.size, np.float32)
    out[o] = np.linspace(0, 1, flat.size, dtype=np.float32)
    return out.reshape(a.shape)


def _resample(P, step):
    P = np.asarray(P, np.float32)
    if len(P) < 2: return P
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-3: return P[:1]
    s = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)


def _closed(P, per=10):
    """a closed Catmull-Rom loop through the points (first point repeated at the end)"""
    P = np.asarray(P, np.float32)
    Q = np.vstack([P[-1:], P, P[:2]])
    L = spline(Q, per)[per:-per]
    return np.vstack([L, L[:1]])


def _normals(P):
    Tg = np.gradient(P, axis=0) if len(P) > 1 else np.array([[1.0, 0.0]], np.float32)
    Tg = Tg / (np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-6)
    return Tg.astype(np.float32), np.stack([-Tg[:, 1], Tg[:, 0]], 1).astype(np.float32)


def _noise1(n, sigma, r):
    """smooth 1D noise of unit std, correlation length ~sigma samples"""
    if n < 1: return np.zeros(0, np.float32)
    sigma = float(np.clip(sigma, 0.5, 400))
    m = int(3 * sigma) + 1
    k = np.exp(-0.5 * (np.arange(-m, m + 1) / sigma) ** 2)
    k /= np.sqrt((k * k).sum())
    x = r.standard_normal(n + 2 * m)
    return np.convolve(x, k, mode='valid')[:n].astype(np.float32)


class Sketchbook:
    PAINTS = PAINTS

    def __init__(self, W=1600, H=1600, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.base = hexc('paper')
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = self.base
        self.T = None; self.NT = None
        self.fin = None
        self.n_lines = 0

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== paper
    def paper(self, tone='paper', tooth=1.0, mottle=1.0, fibres=1.0, seed=None):
        """warm off-white sketchbook paper: a fine tooth, a very low mottle and a scatter of faint fibres"""
        H, W = self.H, self.W
        r = self._r(seed)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.6)
        g2 = noise2d(H, W, 3.0, 2, int(r.integers(1 << 30)))
        g3 = noise2d(H, W, 11.0, 2, int(r.integers(1 << 30)))
        self.T = _equalise(0.8 * z(g1) + 0.5 * z(g2) + 0.2 * z(g3))
        del g1, g2, g3
        m1 = noise2d(H, W, 320, 3, int(r.integers(1 << 30))) - 0.5
        m2 = noise2d(H, W, 70, 2, int(r.integers(1 << 30))) - 0.5
        self.base = hexc(tone)
        self.C = (self.base[None, None] * (1 + mottle * (0.02 * m1[..., None] + 0.007 * m2[..., None])
                                           + 0.016 * tooth * (self.T[..., None] - 0.5))).astype(np.float32)
        del m1, m2
        # a tileable streak texture, sampled in stroke coordinates by the pencil
        q = blur(np.pad(r.random((256, 256)).astype(np.float32), 8, mode='wrap'), 0.8)[8:-8, 8:-8]
        self.NT = _equalise(q)
        rg = np.random.default_rng(self.seed + 7)
        self._grain = rg.standard_normal((H, W), dtype=np.float32)
        if fibres:
            n = int(W * H / 14000 * fibres)
            x = r.uniform(0, W, n); y = r.uniform(0, H, n)
            a = r.uniform(0, np.pi, n); L = r.uniform(4, 16, n)
            paths = []
            for i in range(n):
                bend = r.normal(0, 0.4)
                t = np.linspace(-0.5, 0.5, 5)
                px = x[i] + np.cos(a[i] + bend * t) * L[i] * t
                py = y[i] + np.sin(a[i] + bend * t) * L[i] * t
                paths.append(np.stack([px, py], 1))
            self.inks(paths, width=(0.6, 1.2), colour=['tan', 'stone', 'white'], alpha=(0.06, 0.16), wobble=0.2,
                      taper=(2, 3), grain=0.3, seed=int(r.integers(1 << 30)), count=False)
        return self

    def _need(self):
        if self.T is None: self.paper()

    def _tex(self, u, v):
        """bilinear lookup of the tileable streak texture (wraps every 256 texels)"""
        NT = self.NT
        u = np.mod(u, 256.0); v = np.mod(v, 256.0)
        i0 = np.floor(u).astype(np.int32); j0 = np.floor(v).astype(np.int32)
        fu = (u - i0).astype(np.float32); fv = (v - j0).astype(np.float32)
        i1 = (i0 + 1) & 255; j1 = (j0 + 1) & 255
        i0 &= 255; j0 &= 255
        a = NT[j0, i0] * (1 - fu) + NT[j0, i1] * fu
        b = NT[j1, i0] * (1 - fu) + NT[j1, i1] * fu
        return a * (1 - fv) + b * fv

    # ================================================================== masks
    def poly(self, pts, smooth=False, ss=2):
        """filled polygon -> canvas-sized float mask (smooth=True: a closed Catmull-Rom loop through the points)"""
        P = _closed(pts) if smooth else np.asarray(pts, np.float32)
        out = np.zeros((self.H, self.W), np.float32)
        x0, y0 = max(0, int(np.floor(P[:, 0].min())) - 1), max(0, int(np.floor(P[:, 1].min())) - 1)
        x1, y1 = min(self.W, int(np.ceil(P[:, 0].max())) + 2), min(self.H, int(np.ceil(P[:, 1].max())) + 2)
        if x1 <= x0 or y1 <= y0: return out
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((float(x) - x0) * ss, (float(y) - y0) * ss) for x, y in P], fill=255)
        out[y0:y1, x0:x1] = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return out

    @staticmethod
    def closed_pts(pts, per=10):
        """the smoothed closed outline through the points (what poly(smooth=True) fills)"""
        return _closed(pts, per)

    @staticmethod
    def ellipse_pts(cx, cy, rx, ry=None, rot=0.0, n=72):
        ry = rx if ry is None else ry
        t = np.linspace(0, 2 * np.pi, n + 1)
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        x, y = rx * np.cos(t), ry * np.sin(t)
        return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        return self.poly(self.ellipse_pts(cx, cy, rx, ry, rot, 120))

    def blob(self, cx, cy, rx, ry=None, rough=0.08, seed=None, rot=0.0):
        ry = rx if ry is None else ry
        return self.poly(blob_pts(cx, cy, rx, ry, rough, 120, int(self._r(seed).integers(1 << 30)), np.deg2rad(rot)))

    @staticmethod
    def tube_pts(path, w0, w1=None, per=8):
        """outline points of a tube of width w0 -> w1 along a path (an arm, a stem); w0 may be a list"""
        w1 = w0 if w1 is None else w1
        P = spline(path, per) if len(path) > 2 else _resample(path, 4)
        n = len(P)
        _, Nn = _normals(P)
        w = (np.linspace(w0, w1, n) if np.ndim(w0) == 0
             else np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(w0)), w0))
        w = np.asarray(w, np.float32)[:, None] * 0.5
        return np.vstack([P + Nn * w, (P - Nn * w)[::-1]])

    def tube(self, path, w0, w1=None):
        return self.poly(self.tube_pts(path, w0, w1))

    def soften(self, mask, sigma):
        """a blurred copy of a mask, blurred only round the shape"""
        out = np.zeros((self.H, self.W), np.float32)
        bb = self._bbox(mask, pad=int(3 * sigma) + 4)
        if bb is None: return out
        x0, y0, x1, y1 = bb
        out[y0:y1, x0:x1] = blur(np.asarray(mask[y0:y1, x0:x1], np.float32), sigma)
        return out

    def grow(self, mask, px=2.0):
        """a mask grown by about px (pass it as `avoid` so a line stops just short of what is in front)"""
        return np.clip(self.soften(mask, px) * 3.0, 0, 1)

    @staticmethod
    def _bbox(M, thr=0.004, pad=0):
        rows = np.flatnonzero(M.max(1) > thr); cols = np.flatnonzero(M.max(0) > thr)
        if not len(rows) or not len(cols): return None
        H, W = M.shape
        return (max(0, cols[0] - pad), max(0, rows[0] - pad), min(W, cols[-1] + 1 + pad), min(H, rows[-1] + 1 + pad))

    @staticmethod
    def _shifted(M, dx, dy):
        dx, dy = int(round(dx)), int(round(dy))
        if not dx and not dy: return M
        out = np.zeros_like(M)
        H, W = M.shape
        ys0, ys1 = max(0, dy), min(H, H + dy); xs0, xs1 = max(0, dx), min(W, W + dx)
        out[ys0:ys1, xs0:xs1] = M[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
        return out

    # ================================================================== ink lines
    def _profile(self, path, width, closed, smooth, wobble, wscale, tremor, taper, wvar, flow, gaps, r):
        P = np.asarray(path, np.float32)
        if len(P) < 2: return None
        if closed: P = _closed(P, 10)
        elif smooth and len(P) > 2: P = spline(P, 8)
        P = _resample(P, 1.0)
        n = len(P)
        if n < 3: return None
        _, Nn = _normals(P)
        off = wobble * _noise1(n, wscale, r) + tremor * _noise1(n, 2.5, r)
        P = P + Nn * off[:, None]
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))].astype(np.float32)
        L = float(s[-1])
        t0, t1 = taper
        t0 = min(t0, 0.3 * L); t1 = min(t1, 0.5 * L)
        tin = smoothstep(0, max(t0, 1e-3), s); tout = smoothstep(L, L - max(t1, 1e-3), s)
        w = width * (0.35 + 0.65 * tin) * (0.1 + 0.9 * tout) * (1 + wvar * _noise1(n, 22, r))
        dk = 1 - flow * np.abs(_noise1(n, 45, r))
        if gaps and L > 40:
            k = r.poisson(gaps * L / 220.0)
            for c in r.uniform(0.12 * L, 0.88 * L, k):
                hl = r.uniform(2.0, 5.5)
                w = w * smoothstep(0.5 * hl, 1.6 * hl, np.abs(s - c))
        return P, w.astype(np.float32), np.clip(dk, 0, 1).astype(np.float32)

    def _stamp(self, items, grain, clip, avoid, ss=4):
        """rasterise (P, width, darkness, colour) lines: grouped by colour, drawn run by run (constant width and
        darkness) into a 4x supersampled layer, box-filtered, broken a touch by the tooth, multiplied in"""
        groups = {}
        for P, w, dk, col in items:
            groups.setdefault(tuple(np.round(col, 4).tolist()), []).append((P, w, dk))
        for col, lines in groups.items():
            pad = max(float(np.max(l[1])) for l in lines) + 3
            lo = np.min([l[0].min(0) for l in lines], 0) - pad
            hi = np.max([l[0].max(0) for l in lines], 0) + pad
            x0, y0 = max(0, int(np.floor(lo[0]))), max(0, int(np.floor(lo[1])))
            x1, y1 = min(self.W, int(np.ceil(hi[0]))), min(self.H, int(np.ceil(hi[1])))
            if x1 <= x0 or y1 <= y0: continue
            w, h = x1 - x0, y1 - y0
            im = Image.new('L', (w * ss, h * ss), 0)
            d = ImageDraw.Draw(im)
            org = np.array([x0, y0], np.float32)
            for P, wd, dk in lines:
                Q = ((P - org) * ss).tolist()
                wi = np.round(0.5 * (wd[:-1] + wd[1:]) * ss).astype(np.int32)
                vi = (np.round(0.5 * (dk[:-1] + dk[1:]) * 31) * 8.2).astype(np.int32).clip(0, 255)
                key = wi * 1000 + vi
                j = 0; ns = len(wi)
                while j < ns:
                    e = j
                    while e + 1 < ns and key[e + 1] == key[j]: e += 1
                    if wi[j] > 0 and vi[j] > 0:
                        seg = Q[j:e + 2]
                        if wi[j] <= 1: d.line(seg, fill=int(vi[j]), width=1)
                        else: d.line(seg, fill=int(vi[j]), width=int(wi[j]), joint='curve')
                    j = e + 1
            a = np.asarray(im.resize((w, h), Image.BOX), np.float32) * (1.0 / 255)
            del im
            if grain:
                a *= 1 - grain * smoothstep(0.62, 1.0, 1 - self.T[y0:y1, x0:x1])
            if clip is not None: a *= clip[y0:y1, x0:x1]
            if avoid is not None: a *= 1 - np.clip(avoid[y0:y1, x0:x1], 0, 1)
            self._mul(x0, y0, a, np.array(col, np.float32))

    def _mul(self, x0, y0, a, col):
        """multiply a transparent colour into the page (pen ink, pencil, marker)"""
        h, w = a.shape
        k = np.clip(col / np.maximum(self.base, 0.3), 0, 1)
        Cb = self.C[y0:y0 + h, x0:x0 + w]
        Cb *= 1 - np.clip(a, 0, 1)[..., None] * (1 - k)

    def _lighten(self, x0, y0, a, col):
        h, w = a.shape
        Cb = self.C[y0:y0 + h, x0:x0 + w]
        Cb += np.clip(a, 0, 1)[..., None] * (np.asarray(col, np.float32) - Cb)

    def inks(self, paths, width=2.2, colour='ink', alpha=1.0, wobble=1.0, wscale=60.0, tremor=0.22, taper=(5.0, 14.0),
             wvar=0.12, flow=0.12, grain=0.15, gaps=0.0, smooth=True, closed=False, clip=None, avoid=None, seed=None,
             count=True):
        """fine pen lines along a list of paths. width / alpha / colour may be numbers (or names), (lo, hi) ranges
        or per-path lists; wobble: px of slow hand wobble (wscale: its length in px), tremor: px of fast jitter;
        taper: (in, out) px; flow: how much the ink greys along the line; grain: how much the tooth breaks it;
        gaps: pen lifts per 220 px; clip / avoid: masks the ink is kept to / kept off"""
        self._need()
        r = self._r(seed)
        n = len(paths)
        if not n: return 0

        def per(spec, i):
            if isinstance(spec, tuple) and len(spec) == 2: return float(r.uniform(spec[0], spec[1]))
            if isinstance(spec, (list, np.ndarray)) and len(spec) == n: return float(spec[i])
            return float(spec)
        items = []
        for i, path in enumerate(paths):
            col = colour
            if isinstance(colour, (list, tuple)) and colour and all(isinstance(c, str) for c in colour):
                col = colour[i] if len(colour) == n else colour[int(r.integers(len(colour)))]
            prof = self._profile(path, per(width, i), closed, smooth, wobble, wscale, tremor, taper, wvar, flow,
                                 gaps, r)
            if prof is None: continue
            P, w, dk = prof
            items.append((P, w, dk * per(alpha, i), hexc(col)))
        self._stamp(items, grain, clip, avoid)
        if count: self.n_lines += len(items)
        return len(items)

    def ink(self, path, width=2.2, colour='ink', **kw):
        """one fine pen line along `path` (smoothed through the points)"""
        return self.inks([path], width, colour, **kw)

    def contour(self, pts, pieces=(1, 3), gap=(3.0, 12.0), overlap=(4.0, 14.0), p_gap=0.6, smooth=True, closed=True,
                seed=None, **kw):
        """a closed outline drawn the quick way: one to three strokes that leave a small gap or run past each
        other at the joins (never a perfectly closed vector loop)"""
        r = self._r(seed)
        P = _closed(pts, 10) if (smooth and closed) else (spline(pts, 8) if smooth and len(pts) > 2
                                                          else np.asarray(pts, np.float32))
        P = _resample(P, 1.0)
        n = len(P)
        if n < 6: return 0
        k = int(r.integers(pieces[0], pieces[1] + 1)) if isinstance(pieces, tuple) else int(pieces)
        if not closed:
            return self.inks([P], seed=int(r.integers(1 << 30)), **kw)
        start = int(r.integers(n))
        cuts = np.sort((start + np.sort(r.uniform(0, n, k - 1)).astype(int)) % n) if k > 1 else np.array([], int)
        cuts = np.r_[start, cuts] if k > 1 else np.array([start])
        cuts = np.unique(cuts)
        paths = []
        for i in range(len(cuts)):
            a = cuts[i]; b = cuts[(i + 1) % len(cuts)] if len(cuts) > 1 else cuts[0] + n
            if b <= a: b += n
            if r.random() < p_gap:
                b = b - int(r.uniform(*gap))
            else:
                b = b + int(r.uniform(*overlap))
            idx = np.arange(a, max(a + 3, b)) % n
            paths.append(P[idx])
        return self.inks(paths, smooth=False, seed=int(r.integers(1 << 30)), **kw)

    # ================================================================== colour pencil / marker
    def _uv(self, bb, angle):
        """stroke coordinates in a box: u along `angle`, s across it"""
        x0, y0, x1, y1 = bb
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        a = np.deg2rad(angle)
        return X * np.cos(a) + Y * np.sin(a), -X * np.sin(a) + Y * np.cos(a)

    def _pencil(self, bb, A, colour, u, s, grain, streak, pressure, hatch=0.0, spacing=7.0, r=None):
        """lay colour pencil / marker over coverage A (box bb) with strokes along u: long streaks along the stroke,
        an elongated grain, the pigment catching the tooth (grain) or lying flat (marker)"""
        x0, y0, x1, y1 = bb
        o = r.uniform(0, 256, 4)
        St = self._tex(u / 17.0 + o[0], s / 1.4 + o[1])
        Sg = self._tex(u / 3.2 + o[2], s / 0.85 + o[3])
        p = pressure * (1 - streak * 0.55 * (St - 0.5) * 2)
        if hatch:
            ph = r.uniform(0, 2 * np.pi)
            p = p * (1 - hatch * 0.5 * (1 + np.cos(2 * np.pi * s / spacing + ph + 1.5 * St)))
        p = np.clip(p, 0, 1)
        g = 0.55 * self.T[y0:y1, x0:x1] + 0.45 * Sg
        cpen = smoothstep(1 - p - 0.13, 1 - p + 0.13, g)
        cov = (1 - grain) * p + grain * cpen
        col = hexc(colour)
        if colour == 'paper' or colour == 'white':
            self._lighten(x0, y0, A * cov, col)
        else:
            self._mul(x0, y0, A * cov, col)

    def _ends(self, M, bb, overrun):
        """blurred garment mask in the box (each band re-finds its ends on it with a threshold of its own)"""
        x0, y0, x1, y1 = bb
        return blur(M[y0:y1, x0:x1].astype(np.float32), max(0.5, overrun))

    def tint(self, mask, colour, angle=45.0, strength=0.9, grain=0.5, streak=0.5, pressure=0.9, hatch=0.0,
             spacing=7.0, overrun=2.5, shift=(0.0, 0.0), edge=0.12, clip=None, avoid=None, seed=None):
        """colour a shape with colour pencil / marker laid along `angle`: grain 0 = marker (flat with streaks),
        1 = pencil on the tooth (white specks); hatch draws visible parallel lines `spacing` px apart; the colour
        is set `shift` px off the shape and its edge overruns or falls short by up to ~overrun px"""
        self._need()
        r = self._r(seed)
        M = self._shifted(np.asarray(mask, np.float32), *shift)
        if avoid is not None: M = M * (1 - np.clip(avoid, 0, 1))
        bb = self._bbox(M, pad=int(2 * overrun) + 3)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        u, s = self._uv(bb, angle)
        G = self._ends(M, bb, overrun)
        th = 0.5 + 0.28 * (self._tex(u / 45.0 + r.uniform(0, 256), s / 45.0 + r.uniform(0, 256)) - 0.5) * 2
        St = self._tex(u / 6.0 + r.uniform(0, 256), s / 1.4 + r.uniform(0, 256))
        A = smoothstep(th - edge, th + edge, G + 0.1 * (St - 0.5)) * strength
        if clip is not None: A = A * clip[y0:y1, x0:x1]
        self._pencil(bb, A, colour, u, s, grain, streak, pressure, hatch, spacing, r)
        return 1

    def stripes(self, mask, colours, across=90.0, path=None, bend=0.0, band=(16.0, 28.0), gap=(5.0, 14.0), tilt=0.035,
                rough=2.2, overrun=3.0, grain=(0.2, 0.75), streak=0.55, pressure=(0.8, 0.97), shift=(0.0, 0.0),
                start=None, order='cycle', widths=None, clip=None, avoid=None, seed=None):
        """fill a garment mask with loose hand-drawn bands of colour pencil / marker. Bands run across `across`
        (degrees: 90 = horizontal bands stacked downward) or across a centre-line `path` (a sleeve: the bands wrap
        round it); bend (px) bows them into a smile (+) or a frown (-); each band takes the next colour (order
        'cycle' or 'random'), a width in `band` (or `widths`, a list), a paper gap in `gap`, its own small tilt,
        grain and pressure, two independently wandering edges (rough px) and ends that overrun or fall short of the
        mask by up to ~overrun px. Returns the list of (s0, s1, colour) bands."""
        self._need()
        r = self._r(seed)
        M = self._shifted(np.asarray(mask, np.float32), *shift)
        if avoid is not None: M = M * (1 - np.clip(avoid, 0, 1))
        bb = self._bbox(M, pad=int(2 * overrun) + 4)
        if bb is None: return []
        x0, y0, x1, y1 = bb
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        if path is not None:
            Pp = _resample(spline(path, 10) if len(path) > 2 else np.asarray(path, np.float32), 2.0)
            Tg, Nn = _normals(Pp)
            cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Pp, axis=0), axis=1))].astype(np.float32)
            xf, yf = X.ravel(), Y.ravel()
            best = np.zeros(len(xf), np.int32)
            bd = np.full(len(xf), 1e18, np.float32)
            for j in range(len(Pp)):
                dd = (xf - Pp[j, 0]) ** 2 + (yf - Pp[j, 1]) ** 2
                m = dd < bd
                bd[m] = dd[m]; best[m] = j
            dx, dy = xf - Pp[best, 0], yf - Pp[best, 1]
            s = (cum[best] + dx * Tg[best, 0] + dy * Tg[best, 1]).reshape(X.shape)
            u = (dx * Nn[best, 0] + dy * Nn[best, 1]).reshape(X.shape)
            del xf, yf, dx, dy, bd, best
        else:
            a = np.deg2rad(across)
            s = X * np.cos(a) + Y * np.sin(a); u = -X * np.sin(a) + Y * np.cos(a)
        Mb = M[y0:y1, x0:x1]
        inside = Mb > 0.5
        if not inside.any(): return []
        uc = float(u[inside].mean()); hw = max(1.0, 0.5 * float(u[inside].max() - u[inside].min()))
        if bend: s = s + bend * ((u - uc) / hw) ** 2
        smin, smax = float(s[inside].min()), float(s[inside].max())
        G = self._ends(M, bb, overrun)
        cols = list(colours)
        pos = smin - r.uniform(0, gap[1]) if start is None else smin + start
        bands = []
        i = 0
        while pos < smax:
            bw = widths[i % len(widths)] if widths is not None else r.uniform(*band)
            col = cols[i % len(cols)] if order == 'cycle' else cols[int(r.integers(len(cols)))]
            bands.append((pos, pos + bw, col))
            pos += bw + r.uniform(*gap)
            i += 1
        for k, (a0, a1, col) in enumerate(bands):
            tk = r.normal(0, tilt)
            sk = s + tk * (u - uc)
            sel = (sk > a0 - rough - 3) & (sk < a1 + rough + 3) & (G > 0.02)
            if not sel.any(): continue
            rows = np.flatnonzero(sel.any(1)); cs = np.flatnonzero(sel.any(0))
            ry0, ry1, rx0, rx1 = rows[0], rows[-1] + 1, cs[0], cs[-1] + 1
            sub = (x0 + rx0, y0 + ry0, x0 + rx1, y0 + ry1)
            uu = u[ry0:ry1, rx0:rx1]; ss_ = sk[ry0:ry1, rx0:rx1]
            o = r.uniform(0, 256, 6)
            e0 = rough * (self._tex(uu / 38.0 + o[0], o[1]) - 0.5) * 2
            e1 = rough * (self._tex(uu / 38.0 + o[2], o[3]) - 0.5) * 2
            fz = 0.9 * (self._tex(uu / 4.0 + o[4], ss_ / 3.0 + o[5]) - 0.5)
            B = smoothstep(a0 + e0 - 0.9, a0 + e0 + 0.9, ss_ + fz) * smoothstep(a1 + e1 + 0.9, a1 + e1 - 0.9, ss_ - fz)
            th = float(np.clip(r.normal(0.5, 0.13), 0.2, 0.8))
            Gs = G[ry0:ry1, rx0:rx1]
            St = self._tex(uu / 5.0 + o[1], ss_ / 1.3 + o[3])
            E = smoothstep(th - 0.1, th + 0.1, Gs + 0.16 * (St - 0.5))
            A = B * E
            if clip is not None: A = A * clip[sub[1]:sub[3], sub[0]:sub[2]]
            gk = r.uniform(*grain) if isinstance(grain, tuple) else grain
            pk = r.uniform(*pressure) if isinstance(pressure, tuple) else pressure
            self._pencil(sub, A, col, uu, ss_, gk, streak, pk, 0.0, 7.0, r)
        return bands

    def blush(self, cx, cy, r_, colour='cheek', strength=0.95, ry=None, grain=0.3, rim=0.3, rough=0.05, seed=None):
        """a round blush dot: a soft-edged disc of fine-grained colour with a slightly darker rim"""
        self._need()
        r = self._r(seed)
        ry = r_ if ry is None else ry
        P = blob_pts(cx, cy, r_, ry, rough, 90, int(r.integers(1 << 30)))
        M = self.poly(P)
        bb = self._bbox(M, pad=4)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        Mb = blur(M[y0:y1, x0:x1], 0.7)
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.sqrt(((X - cx) / r_) ** 2 + ((Y - cy) / ry) ** 2)
        A = Mb * strength * (0.82 + rim * smoothstep(0.55, 0.98, d)) * (1 + 0.08 * (self._tex(X / 9, Y / 9) - 0.5))
        u, s = self._uv(bb, r.uniform(20, 70))
        self._pencil(bb, A, colour, u, s, grain, 0.3, 0.95, 0.0, 7.0, r)
        return 1

    def dots(self, pts, r_=3.0, colour='pink', strength=0.85, seed=None):
        """small pencil / marker dots (blossoms, buttons, freckles)"""
        r = self._r(seed)
        for x, y in pts:
            rr = r_ * r.uniform(0.75, 1.2)
            self.blush(x, y, rr, colour, strength, rr * r.uniform(0.8, 1.1), 0.25, 0.15, 0.12,
                       seed=int(r.integers(1 << 30)))
        return len(pts)

    # ================================================================== faces
    def eye_closed(self, cx, cy, w, sag=None, lashes=3, side=1, rot=0.0, width=2.0, colour='ink', seed=None):
        """a closed eye: a small downward arc (a smile-shaped lid line) with `lashes` short lashes ticking down and
        out from its outer half (`side` = +1 if the outer corner is on the right)"""
        r = self._r(seed)
        sag = 0.28 * w if sag is None else sag
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        L = lambda pts: np.array([(cx + u * c - v * s, cy + u * s + v * c) for u, v in pts], np.float32)
        t = np.linspace(-1, 1, 9)
        arc = L([(0.5 * w * x, sag * (1 - x * x) - 0.08 * sag) for x in t])
        n = self.ink(arc, width, colour, taper=(2.5, 4.0), wobble=0.25, tremor=0.12, seed=int(r.integers(1 << 30)))
        paths = []
        for i in range(lashes):
            x = side * (0.15 + 0.75 * (i + 0.5) / max(1, lashes))
            y = sag * (1 - x * x) - 0.08 * sag
            ang = np.deg2rad(90 - side * (20 + 45 * (i + 0.5) / max(1, lashes)))
            ln = w * r.uniform(0.2, 0.3)
            p0 = (0.5 * w * x, y)
            paths.append(L([p0, (p0[0] + np.cos(ang) * ln, p0[1] + np.sin(ang) * ln)]))
        if paths:
            n += self.inks(paths, width * 0.75, colour, taper=(1.0, 3.0), wobble=0.1, tremor=0.08,
                           seed=int(r.integers(1 << 30)))
        return n

    def eye_dot(self, cx, cy, r_=3.2, colour='ink'):
        """a dot eye"""
        return self.dots([(cx, cy)], r_, colour, 0.95)

    def mouth(self, cx, cy, w, h=None, colour='lip', rot=0.0, smile=0.0, seed=None):
        """a small red mouth: a tiny bow of two lips laid in marker with a darker line between"""
        r = self._r(seed)
        h = 0.4 * w if h is None else h
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        L = lambda pts: [(cx + u * c - v * s, cy + u * s + v * c) for u, v in pts]
        hw = 0.5 * w; sm = smile * 0.3 * h
        up = L([(-hw, -sm), (-0.4 * hw, -0.45 * h), (0, -0.25 * h), (0.4 * hw, -0.45 * h), (hw, -sm), (0, 0.05 * h)])
        lo = L([(-0.8 * hw, -sm * 0.8), (0, 0.08 * h), (0.8 * hw, -sm * 0.8), (0.3 * hw, 0.5 * h), (-0.3 * hw, 0.5 * h)])
        M = np.clip(self.poly(up, smooth=True) + self.poly(lo, smooth=True), 0, 1)
        self.tint(M, colour, rot + 10, 0.92, 0.15, 0.3, 0.95, overrun=0.6, edge=0.2, seed=int(r.integers(1 << 30)))
        self.ink(L([(-0.85 * hw, -sm * 0.85), (0, 0.06 * h), (0.85 * hw, -sm * 0.85)]), max(1.0, 0.11 * h), 'scarlet',
                 alpha=0.8, taper=(1.5, 2.5), wobble=0.1, seed=int(r.integers(1 << 30)))
        return 1

    def hair(self, guides, n=40, width=2.2, colour='ink', wave=(4.0, 80.0), wave_root=0.25, length=(0.8, 1.0),
             start=(0.0, 0.05), spread=1.0, stray=0.06, alpha=(0.82, 1.0), taper=(4.0, 40.0), jitter=1.2,
             cohere=2.5, clip=None, avoid=None, seed=None):
        """a lock of hair as n separate fine strands interpolated between guide curves (two or more polylines from
        root to tip, in order across the lock): each strand starts near the root (`start`), ends at its own
        fraction of the length (`length`), waves (`wave` = (amplitude px, period px)) in phase with its
        neighbours (`cohere` turns of phase across the lock), the wave growing from root (`wave_root`) to tip, and
        thins to a long tip; `stray` is the share of strands that wander off as flyaways"""
        r = self._r(seed)
        K = len(guides)
        if K < 2: raise ValueError('hair() needs two or more guide curves')
        m = 90
        G = []
        for g in guides:
            g = np.asarray(g, np.float32)
            g = spline(g, 10) if len(g) > 2 else g
            d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(g, axis=0), axis=1))]
            q = np.linspace(0, d[-1], m)
            G.append(np.stack([np.interp(q, d, g[:, 0]), np.interp(q, d, g[:, 1])], 1))
        G = np.stack(G).astype(np.float32)
        ph0 = r.uniform(0, 2 * np.pi)
        paths, ws, als = [], [], []
        for i in range(n):
            t = (i + r.uniform(0.15, 0.85)) / n
            t = 0.5 + (t - 0.5) * spread
            g = np.clip(t, 0, 1) * (K - 1)
            k = min(int(g), K - 2); f = g - k
            B = G[k] * (1 - f) + G[k + 1] * f
            s0 = r.uniform(*start); s1 = r.uniform(*length)
            if s1 - s0 < 0.08: continue
            q = np.linspace(s0, s1, max(8, int((s1 - s0) * m)))
            idx = q * (m - 1)
            P = np.stack([np.interp(idx, np.arange(m), B[:, 0]), np.interp(idx, np.arange(m), B[:, 1])], 1)
            P = _resample(P, 2.0)
            if len(P) < 4: continue
            _, Nn = _normals(P)
            arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            frac = np.linspace(s0, s1, len(P))
            amp, per_ = wave
            is_stray = r.random() < stray
            if is_stray: amp, per_ = amp * r.uniform(1.6, 2.6), per_ * r.uniform(0.7, 1.3)
            ph = ph0 + 2 * np.pi * cohere * t + r.normal(0, 0.35) + (r.uniform(0, 2 * np.pi) if is_stray else 0)
            env = wave_root + (1 - wave_root) * frac
            off = amp * env * np.sin(2 * np.pi * (arc + s0 * 300) / per_ + ph) + jitter * r.normal() * frac
            if is_stray: off = off + r.normal(0, amp) * frac ** 2
            paths.append(P + Nn * off[:, None])
            ws.append(width * r.uniform(0.75, 1.15) * (0.75 if is_stray else 1.0))
            als.append(r.uniform(*alpha) if isinstance(alpha, tuple) else alpha)
        return self.inks(paths, ws, colour, als, wobble=0.5, wscale=40, tremor=0.15, taper=taper, flow=0.1,
                         grain=0.12, clip=clip, avoid=avoid, seed=int(r.integers(1 << 30)))

    # ================================================================== props
    def leaf(self, base, tip, width, fill=None, line='ink', veins=6, vein='line', vein_colour=None, bend=0.08,
             asym=0.08, stem=0.0, stem_bend=0.1, lw=1.8, fill_shift=(3.0, -2.0), strength=0.85, grain=0.5,
             hatch=0.0, rib=True, seed=None):
        """a single leaf from `base` to `tip`: an outline (ink or a coloured line, a small gap at the tip), a midrib,
        `veins` pairs of veins slanting toward the tip ('line' = drawn, 'white' = reserved in the fill, None),
        an optional colour-pencil `fill` set a little off the line, and an optional `stem` (px) below the base.
        Returns the leaf's mask."""
        r = self._r(seed)
        B = np.asarray(base, np.float32); Tp = np.asarray(tip, np.float32)
        ax = Tp - B; L = float(np.linalg.norm(ax)) + 1e-6
        dn = ax / L; nr = np.array([-dn[1], dn[0]], np.float32)
        t = np.linspace(0, 1, 40)[:, None]
        mid = B + ax * t + nr * (bend * L * np.sin(np.pi * t))
        prof = (np.sin(np.pi * np.clip(t, 0, 1) ** 0.85) ** 0.9) * 0.5 * width
        left = mid + nr * prof * (1 + asym); right = mid - nr * prof * (1 - asym)
        outline = np.vstack([left, right[::-1]])
        M = self.poly(outline)
        ang = float(np.degrees(np.arctan2(dn[1], dn[0])))
        if fill:
            self.tint(M, fill, ang + 50, strength, grain, 0.5, 0.92, hatch, 6.0, 2.0, fill_shift,
                      seed=int(r.integers(1 << 30)))
        lc = line
        if vein == 'white':
            paths = []
            for i in range(veins):
                tv = 0.12 + 0.75 * (i + 0.5) / veins
                for sd, ed in ((1, left), (-1, right)):
                    p0 = B + ax * tv + nr * (bend * L * np.sin(np.pi * tv))
                    te = min(0.98, tv + 0.16)
                    p1 = ed[int(te * 39)] * 0.85 + p0 * 0.15
                    paths.append(np.array([p0, 0.5 * (p0 + p1) + dn * 2, p1], np.float32))
            paths.append(mid[2:-3])
            self._lighten_lines(paths, lw * 1.2, M, r, hexc(vein_colour) if vein_colour else self.base * 1.01)
        if lc:
            self.contour(outline, pieces=(1, 2), gap=(2, 6), overlap=(3, 8), width=lw, colour=lc,
                         seed=int(r.integers(1 << 30)))
            if rib: self.ink(mid[1:-2], lw * 0.9, lc, taper=(2, 8), seed=int(r.integers(1 << 30)))
            if vein == 'line' and veins:
                paths = []
                for i in range(veins):
                    tv = 0.1 + 0.78 * (i + 0.5) / veins
                    for ed in (left, right):
                        p0 = B + ax * tv + nr * (bend * L * np.sin(np.pi * tv))
                        te = min(0.97, tv + r.uniform(0.1, 0.18))
                        wv = r.uniform(0.82, 0.95)
                        p1 = ed[int(te * 39)] * wv + p0 * (1 - wv)
                        paths.append(np.array([p0, 0.55 * p0 + 0.45 * p1 + dn * 1.5, p1], np.float32))
                self.inks(paths, lw * 0.7, vein_colour or lc, alpha=0.85, taper=(1.5, 5), wobble=0.3,
                          seed=int(r.integers(1 << 30)))
        if stem:
            sp = [B, B - dn * stem * 0.5 + nr * stem * stem_bend, B - dn * stem]
            self.ink(sp, lw, lc or 'ink', taper=(2, 10), seed=int(r.integers(1 << 30)))
        return M

    def _lighten_lines(self, paths, width, clip, r, col):
        """reserve veins in a fill: lift the colour back toward the paper (or `col`) along the lines"""
        items = []
        for P in paths:
            prof = self._profile(P, width, False, True, 0.3, 40, 0.1, (2, 5), 0.1, 0.05, 0, r)
            if prof is not None: items.append(prof)
        if not items: return
        pad = width + 3
        lo = np.min([p[0].min(0) for p in items], 0) - pad; hi = np.max([p[0].max(0) for p in items], 0) + pad
        x0, y0 = max(0, int(lo[0])), max(0, int(lo[1])); x1, y1 = min(self.W, int(hi[0]) + 1), min(self.H, int(hi[1]) + 1)
        ss = 4
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        d = ImageDraw.Draw(im)
        for P, w, _ in items:
            d.line(((P - [x0, y0]) * ss).tolist(), fill=255, width=max(1, int(round(float(np.median(w)) * ss))),
                   joint='curve')
        a = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        a *= clip[y0:y1, x0:x1] * 0.85
        self._lighten(x0, y0, a, col)

    def flower(self, x, y, r_=14.0, colour='red', kind='rose', stem=0.0, stem_colour='forest', leaves=1, lw=1.8,
               seed=None):
        """a little flower: 'rose' a scribbled spiral with a couple of loose petals, 'daisy' petal loops round a
        dot, 'tulip' a pencil-filled cup with three points; `stem` px of stem below with `leaves` small leaves"""
        r = self._r(seed)
        if stem:
            sx = x + r.normal(0, 0.1 * stem)
            sp = [(x, y + r_ * 0.6), (0.5 * (x + sx) + r.normal(0, 4), y + stem * 0.5), (sx, y + stem)]
            self.ink(sp, lw, stem_colour, taper=(2, 6), grain=0.35, seed=int(r.integers(1 << 30)))
            for i in range(leaves):
                ty = y + stem * r.uniform(0.35, 0.8)
                sd = 1 if i % 2 == 0 else -1
                bx = x + (sx - x) * (ty - y) / stem
                self.leaf((bx, ty), (bx + sd * r_ * 1.6, ty - r_ * 1.2), r_ * 0.7, line=stem_colour, veins=0,
                          rib=True, lw=lw * 0.9, seed=int(r.integers(1 << 30)))
        if kind == 'rose':
            th = np.linspace(0, 4.2 * np.pi, 80)
            rad = r_ * (0.15 + 0.85 * th / th[-1]) * (1 + 0.12 * np.sin(3 * th))
            P = np.stack([x + rad * np.cos(th), y + 0.85 * rad * np.sin(th)], 1)
            self.ink(P, lw, colour, taper=(2, 8), grain=0.35, seed=int(r.integers(1 << 30)))
            arcs = []
            for k in range(2):
                a0 = r.uniform(0, 2 * np.pi); t = np.linspace(a0, a0 + r.uniform(1.6, 2.6), 12)
                rr = r_ * r.uniform(1.05, 1.3)
                arcs.append(np.stack([x + rr * np.cos(t), y + 0.85 * rr * np.sin(t) + 2], 1))
            self.inks(arcs, lw * 0.9, colour, taper=(2, 6), grain=0.35, seed=int(r.integers(1 << 30)))
        elif kind == 'daisy':
            k = int(r.integers(6, 9))
            petals = []
            for i in range(k):
                a = 2 * np.pi * i / k + r.normal(0, 0.12)
                t = np.linspace(-1, 1, 11)
                px = (0.3 + 0.7 * (1 - t * t)) * r_ * (0.35 + 0.65 * np.abs(np.sin(np.pi * (t + 1) / 2)))
                ln = r_ * (0.3 + 0.7 * np.sin(np.pi * (t + 1) / 2))
                wdt = 0.3 * r_ * np.sin(np.pi * (t + 1))
                petals.append(np.stack([x + np.cos(a) * ln - np.sin(a) * wdt, y + np.sin(a) * ln + np.cos(a) * wdt], 1))
            self.inks(petals, lw * 0.9, colour, taper=(1.5, 4), grain=0.3, seed=int(r.integers(1 << 30)))
            self.dots([(x, y)], r_ * 0.22, 'gold')
        else:   # tulip
            pts = [(x - r_, y - 0.1 * r_), (x - 0.95 * r_, y - r_), (x - 0.45 * r_, y - 0.55 * r_), (x, y - 1.15 * r_),
                   (x + 0.45 * r_, y - 0.55 * r_), (x + 0.95 * r_, y - r_), (x + r_, y - 0.1 * r_),
                   (x + 0.6 * r_, y + 0.6 * r_), (x - 0.6 * r_, y + 0.6 * r_)]
            M = self.poly(pts, smooth=False)
            self.tint(M, colour, -60, 0.9, 0.65, 0.6, 0.9, 0.25, 4.0, 2.5, seed=int(r.integers(1 << 30)))
        return 1

    def tree(self, x, y, height, colour='forest', lines=4, branches=7, lean=0.03, spread=1.0, width=1.7, trunk=None,
             blossoms=None, n_blossom=10, alpha=0.95, grain=0.4, seed=None):
        """a thin tree drawn in coloured line: a trunk of `lines` roughly parallel wobbly strokes that part into
        `branches` up-and-out branches, each with a twig or two and a little fork at the tip; optional blossom dots"""
        r = self._r(seed)
        tw = height * 0.03 if trunk is None else trunk
        top = np.array([x + lean * height, y - height], np.float32)
        paths, wds = [], []
        for i in range(lines):
            o = (i / max(1, lines - 1) - 0.5) * tw + r.normal(0, tw * 0.12)
            ys = np.linspace(y, y - height * r.uniform(0.86, 1.0), 9)
            xs = x + o * np.linspace(1, 0.35, 9) + lean * (y - ys) + r.normal(0, tw * 0.08, 9)
            paths.append(np.stack([xs, ys], 1)); wds.append(width * r.uniform(0.8, 1.15))
        hs = np.sort(r.uniform(0.28, 0.92, branches))
        sides = np.where(np.arange(branches) % 2 == 0, 1, -1) * (1 if r.random() < 0.5 else -1)
        tips = []
        for h, sd in zip(hs, sides):
            b0 = np.array([x + lean * height * h + sd * tw * 0.3, y - height * h], np.float32)
            ang = np.deg2rad(-90 + sd * r.uniform(22, 48) * spread)
            ln = height * r.uniform(0.14, 0.3) * (1.15 - 0.6 * h)
            b1 = b0 + ln * np.array([np.cos(ang), np.sin(ang)], np.float32)
            bm = 0.5 * (b0 + b1) + r.normal(0, ln * 0.06, 2)
            for j in range(int(r.integers(1, 3))):
                off = np.array([sd * j * 2.5, 0], np.float32)
                paths.append(np.array([b0 + off, bm + off, b1 + off * 0.3], np.float32)); wds.append(width * 0.9)
            for j in range(int(r.integers(1, 3))):
                tt = r.uniform(0.4, 0.75)
                c0 = b0 + (b1 - b0) * tt
                a2 = ang + np.deg2rad(r.choice([-1, 1]) * r.uniform(25, 45))
                l2 = ln * r.uniform(0.3, 0.5)
                c1 = c0 + l2 * np.array([np.cos(a2), np.sin(a2)], np.float32)
                paths.append(np.array([c0, 0.5 * (c0 + c1) + r.normal(0, 1.5, 2), c1], np.float32))
                wds.append(width * 0.75); tips.append(c1)
            for j in (-1, 1):
                a3 = ang + np.deg2rad(j * r.uniform(12, 30))
                c1 = b1 + ln * r.uniform(0.12, 0.25) * np.array([np.cos(a3), np.sin(a3)], np.float32)
                paths.append(np.array([b1, c1], np.float32)); wds.append(width * 0.6); tips.append(c1)
        for j in (-1, 1):
            a3 = np.deg2rad(-90 + j * r.uniform(8, 25))
            c1 = top + height * 0.08 * np.array([np.cos(a3), np.sin(a3)], np.float32)
            paths.append(np.array([top + [0, height * 0.06], c1], np.float32)); wds.append(width * 0.7); tips.append(c1)
        self.inks(paths, wds, colour, alpha, taper=(3, 18), grain=grain, wobble=0.8, seed=int(r.integers(1 << 30)))
        if blossoms and tips:
            sel = r.choice(len(tips), min(n_blossom, len(tips)), replace=False)
            self.dots([tuple(np.asarray(tips[i]) + r.normal(0, 3, 2)) for i in sel], 2.6, blossoms, 0.8)
        return len(paths)

    def steam(self, x, y, height, colour='graphite', sway=18.0, curl=1.0, width=1.5, alpha=0.75, strands=1,
              lean=0.12, seed=None):
        """a fine curl of steam rising from (x, y): a lazy S-curve that ends in a loose spiral (`curl` its turns;
        0 = no curl); `strands` > 1 adds fainter, shorter companions without the curl"""
        r = self._r(seed)
        paths, als = [], []
        for k in range(strands):
            ph = r.uniform(0, 2 * np.pi)
            hk = height * (1 - 0.25 * k) * r.uniform(0.9, 1.05)
            t = np.linspace(0, 1, 9)
            xs = x + k * sway * 0.6 + sway * np.sin(2 * np.pi * 0.9 * t + ph) * (0.25 + 0.75 * t) + lean * hk * t
            ys = y - 0.78 * hk * t
            pts = list(zip(xs, ys))
            if curl and k == 0:
                ex, ey = pts[-1]
                dx = xs[-1] - xs[-2]
                sg = 1 if dx >= 0 else -1
                R = max(sway, 0.09 * hk) * r.uniform(0.9, 1.2)
                cx, cy = ex + sg * R, ey - 0.2 * R
                a0 = np.arctan2(ey - cy, ex - cx)
                th = a0 - sg * np.linspace(0, 2 * np.pi * curl, 24)[1:]
                rad = R * np.linspace(1, 0.35, len(th) + 1)[1:]
                pts += list(zip(cx + rad * np.cos(th), cy + rad * np.sin(th)))
            paths.append(np.array(pts, np.float32)); als.append(alpha * (1 - 0.4 * k))
        return self.inks(paths, width, colour, als, taper=(14, 30), wobble=0.5, flow=0.25, grain=0.2,
                         seed=int(r.integers(1 << 30)))

    def ticks(self, mask, n=30, length=(5, 10), angle=90.0, spread=20.0, width=1.4, colour='ink', alpha=0.8,
              seed=None):
        """short marks scattered inside a mask (fur, grass, texture), each `length` px along `angle` +- spread"""
        r = self._r(seed)
        M = np.asarray(mask, np.float32)
        bb = self._bbox(M)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        xs, ys = [], []
        tries = 0
        while len(xs) < n and tries < n * 40:
            tries += 1
            px, py = r.uniform(x0, x1), r.uniform(y0, y1)
            if M[int(py), int(px)] > 0.6: xs.append(px); ys.append(py)
        paths = []
        for px, py in zip(xs, ys):
            a = np.deg2rad(angle + r.normal(0, spread)); ln = r.uniform(*length)
            paths.append(np.array([(px, py), (px + np.cos(a) * ln * 0.5 + r.normal(0, 0.5), py + np.sin(a) * ln * 0.5),
                                   (px + np.cos(a) * ln, py + np.sin(a) * ln)], np.float32))
        return self.inks(paths, width, colour, alpha, taper=(1.5, 3.5), wobble=0.2, seed=int(r.integers(1 << 30)))

    def squiggle(self, x, y, size=16.0, colour='ink', kind='spiral', width=1.4, alpha=0.8, seed=None):
        """a tiny doodle mark in the empty paper: 'spiral', 'sparkle' (a four-line star) or 'loop' -- never fake
        writing"""
        r = self._r(seed)
        if kind == 'spiral':
            th = np.linspace(0, 3.3 * np.pi, 60)
            rad = size * 0.5 * th / th[-1]
            P = np.stack([x + rad * np.cos(th), y + rad * np.sin(th)], 1)
            return self.ink(P, width, colour, alpha=alpha, taper=(2, 6), seed=int(r.integers(1 << 30)))
        if kind == 'sparkle':
            paths = []
            for a in (0, 90, 45, 135):
                ln = size * (0.5 if a % 90 == 0 else 0.28)
                d = np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))]) * ln
                paths.append(np.array([(x - d[0], y - d[1]), (x + d[0], y + d[1])], np.float32))
            return self.inks(paths, width, colour, alpha, taper=(3, 3), seed=int(r.integers(1 << 30)))
        t = np.linspace(0, 1, 70)
        P = np.stack([x + size * (t - 0.5) * 1.6 + 0.3 * size * np.sin(2 * np.pi * 2 * t),
                      y - 0.35 * size * np.cos(2 * np.pi * 2 * t) * np.sin(np.pi * t)], 1)
        return self.ink(P, width, colour, alpha=alpha, taper=(3, 6), smooth=False, seed=int(r.integers(1 << 30)))

    # ================================================================== output
    def finish(self, grain=1.0, soft=0.12):
        """record the finishing (applied in render, so every stage snapshot matches; call it before the first mark):
        a faint paper grain over everything and a very slight softening"""
        self.fin = dict(grain=grain, soft=soft)
        return self

    def render(self):
        """the finished picture (the canvas is untouched)"""
        out = self.C
        f = self.fin
        if not f: return np.clip(out, 0, 1)
        self._need()
        out = out.copy()
        if f['grain']:
            out *= (1 + f['grain'] * 0.006 * self._grain)[..., None]
        if f['soft']:
            for c in range(3): out[..., c] = out[..., c] * (1 - f['soft']) + blur(out[..., c], 0.6) * f['soft']
        return np.clip(out, 0, 1)

    def composite(self):
        out = self.render()
        out *= 255; out += 0.5
        return Image.fromarray(out.astype(np.uint8))

    def stage(self, name):
        if not self.keep_stages: return
        im = self.composite()
        if self.stages_dir:
            os.makedirs(self.stages_dir, exist_ok=True)
            im.save(f'{self.stages_dir}/{self._n_stages:02d}_{name}.png', compress_level=1)
        else:
            b = io.BytesIO(); im.save(b, 'PNG', compress_level=1)
            self.stages.append((name, b.getvalue()))
        self._n_stages += 1

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, b) in enumerate(self.stages):
                with open(f'{sd}/{i:02d}_{name}.png', 'wb') as f: f.write(b)
            img.save(f'{sd}/{self._n_stages:02d}_final.png', compress_level=1)
        return img
