"""spotillo — 日系扁平小插画 / Flat Spot Illustration: small Japanese-style everyday-life vignettes floating on white
(numpy + Pillow only).

The look: several small scenes of ordinary life (someone sipping from a mug, two people baking, a walk with a
bicycle, a nap) set apart on a white sheet with generous space between them -- no ground, no background, at most a
sliver of shadow or a bench leg. Every shape is a flat, opaque cut of one colour: no gradients, no shading, only a
faint print grain. Edges are slightly irregular, as if cut by hand or laid with a marker, never vector-perfect. The
palette is restrained -- navy, slate and powder blue, mustard, olive and forest green, a few greys, near-black
hair -- with skin left as the white paper (or a pale warm tone), and ONE warm red that recurs as the accent in
every vignette (a mug, a bowl, a bag, an umbrella, a pair of socks). Lines are few and thin: folds and seams cut
in white into dark fabric (or drawn a shade darker on pale fabric), a profile line down the face, fingers, chair
legs. Faces are almost blank: a tiny dot eye, a nose bump in the profile line. Hair is one solid dark blob with a
couple of white strands cut into it. Action is told with little hand marks: steam squiggles, three dashes of
surprise, z's, rain.

Model
  paper       A warm white sheet (#fbfaf6); `finish()` adds a very faint tooth to the bare paper.
  shapes      A shape is a closed outline (a point list). Before it is cut, the outline is resampled and pushed in
              and out along its normals by a periodic low-frequency wobble plus a finer one (`wobble` px x k,
              `lumps` its wavelength), so a circle is a little lumpy and a straight edge breathes. Pillow fills it
              into a 3x supersampled patch the size of its bounding box; the edge is then thresholded against a
              fine noise so it frays by a fraction of a pixel. Paint is opaque: new = old + mask x (colour - old). A
              patch can be clipped to (or kept out of) other patches (`clip=`, `avoid=`).
  gaps        `gap=` cuts a thin white gap round a shape before it is laid -- the paper showing between two shapes
              of one colour (an arm over a sweater, trousers over a hoodie, a seat cushion on a sofa). The gap is
              the shape's blurred mask thresholded against a mid-scale noise, so it is wider here, narrower there
              and missing on (1 - `gap_keep`) of the edge.
  lines       A line is a tapered ribbon along a slightly wobbling path (round ends, thin tips), rasterised at 4x.
              `fold()` picks its colour from what is under it: a white cut on dark and mid fabric (luminance < 0.74),
              a darker shade of a pale one. `cut()` is a white line.
  people      Built from simple parts in a fixed back-to-front order (far leg, far arm and hand, near leg, neck and
              torso, head and hair, near arm and hand; the crouch puts the near leg in front of the torso):
              `limb()` a sleeve or trouser leg as a fat tube with a flat cuff; `torso()` a boxy oversized top built
              in its own frame; `head()` a paper-white face with a profile line (nose bump, lips, chin), a dot eye and
              a lumpy hair blob with white strands cut in; `hand()` a white mitten with finger bumps, a thin outline
              and red finger lines; `shoe()` a sneaker or a stocking foot. `person()` draws a whole figure from a
              pose preset ('stand', 'walk', 'sit', 'crouch', 'reach') with joints overridden in head units (`rel`),
              turned (`rot`, -90 lays it on its back), automatic folds at elbows, knees, shins and hem, and hooks to
              slip props in between the layers.
  props       mug, bowl, pot, bag, umbrella, bicycle, bench, chair, armchair (its near arm drawn later, over the
              sitter), sofa, stool, table, stove / counter, plant, book (open, closed, tented face-down), cat_sit,
              cat_curl, window -- all from the same flat shapes and lines.
  marks       steam squiggles, three dashes of surprise ('!'), z's, rain dashes, motion ticks, a sliver of shadow.
  finish      `finish()` records the print grain (a soft mottle and a fine tooth in the ink, a few paper-light specks,
              a very slight softening), applied in render so every stage snapshot matches the final picture.

API (canvas pixel coordinates; colours are PAINTS names, '#rrggbb' or RGB triples; k = min(W, H) / 1000 scales the
     default widths; u = a figure's head height in px)
  surface   SpotIllustration(W, H, seed, keep_stages, stages_dir); paper(tone); finish(grain, speckle, soft) -- call
            finish() before the first mark
  outlines  ellipse(cx, cy, rx, ry, rot) / rrect(x0, y0, x1, y1, r) / blob(cx, cy, rx, ry, rough, rot) /
            curve(pts) (closed Catmull-Rom) / tube(path, widths, cap) -> point arrays
  paint     shape(pts, colour, smooth, wobble, rough, gap, gap_keep, clip, avoid, alpha, lumps) -> Patch;
            knock(pts) (a paper-white shape); line(path, width, colour, taper, wobble, clip, avoid, smooth, closed,
            tip); cut(path, width); fold(path, width, colour, clip); dot(x, y, r, colour); union(*patches);
            grow(patch, px); under(path) (the mean colour under a path)
  people    limb(path, widths, colour, cap, gap, gap_keep); torso(sh_back, sh_front, hem_back, hem_front, colour,
            facing, collar, bulge, gap, hood); head(cx, cy, r, facing, turn, tilt, hair, hair_colour, eye, ear,
            strands, skin, line, mouth, fringe, hat) -> dict of points; hair(head, style, colour, strands, fringe,
            hat); neck(top, bottom, w); hand(x, y, angle, size, pose, facing, finger) (pose 'grip' / 'fist' /
            'open' / 'flat' / 'cup'); shoe(x, y, angle, size, colour, facing, sole, line, laces);
            pose(name, x, y, u, facing, rot, rel, **joints) -> joints; person(x, y, u, facing, pose, outfit, hooks,
            rel, rot, J, order, folds, **joints)
  props     mug(x, y, h) / bowl(x, y, w, fill) / pot(x, y, w) / bag(x, y, w, h) / umbrella(x, y, r, angle,
            handle_len) / bicycle(x, y, size, facing) / bench(x0, x1, y, h) / chair(x, y, h, facing) /
            armchair(x, y, w, h, facing) -> {'arm': fn} / sofa(x0, x1, y, h) / stool(x, y, w, h) /
            table(x0, x1, y, h) / stove(x0, x1, y, h) / plant(x, y, h, pot, leaf) / book(x, y, w, angle, open_) /
            cat_sit(x, y, h, facing, head_down, eye) / cat_curl(x, y, w) / window(x0, y0, x1, y1)
  marks     steam(x, y, h, n) / bang(x, y, r, angle) / zzz(x, y, size) / rain(x0, y0, x1, y1, n, slant) /
            ticks(x, y, r, angle, n) / shadow(cx, cy, rx, ry)
  output    render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 92, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from spotillo import SpotIllustration
    s = SpotIllustration(1200, 900, seed=1); s.finish(); s.paper()
    u = 110                                                  # one head height
    s.person(560, 820, u, facing=1, pose='stand', outfit=dict(top='mustard', bottom='grey', hand_n=('grip', -5)),
             rel=dict(elbow_n=(0.0, -3.4), wrist_n=(0.55, -3.7)),
             hooks={'hand_near': lambda: s.mug(560 + 0.95 * u, 820 - 3.45 * u, 0.5 * u)})
    s.steam(560 + 0.95 * u, 820 - 4.1 * u, 0.8 * u)
    s.save('spot.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, spline, smoothstep, fbm1d

PAINTS = {
    # paper and lines
    'paper': '#fbfaf6', 'white': '#ffffff', 'ink': '#262d3d', 'line': '#3a4152', 'black': '#252b3b',
    # blues
    'navy_deep': '#222b40', 'navy': '#2c3956', 'blue': '#35548a', 'slate': '#5d7290', 'powder': '#92b5d0',
    'powder_light': '#bcd3e5',
    # yellows and greens
    'mustard': '#d6a235', 'mustard_light': '#e8c46a', 'olive': '#66804a', 'green': '#4d7b55', 'sage': '#a3b48c',
    # greys and creams
    'grey_light': '#e0e0de', 'grey': '#c7c8c8', 'grey_mid': '#a7aaae', 'grey_dark': '#6f747c', 'cream': '#efe8da',
    'skin': '#f7eadf', 'wood': '#c49a68', 'wood_light': '#dcc09a',
    # the one warm accent
    'red': '#e2432a', 'red_deep': '#c3331f', 'red_line': '#e0563f', 'pink': '#f0b1a2',
}


def hexc(c):
    if isinstance(c, str):
        c = PAINTS.get(c, c).lstrip('#')
        return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255
    c = np.asarray(c, np.float32)
    return c / 255 if c.max() > 1.0 else c


def mix(a, b, t):
    return hexc(a) * (1 - t) + hexc(b) * t


def _lum(c):
    return float(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])


def _resample(P, step, closed):
    P = np.asarray(P, np.float64)
    if closed: P = np.vstack([P, P[:1]])
    d = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(d)])
    L = s[-1]
    if L < 1e-6: return P[:1].copy(), 0.0
    n = max(4 if closed else 2, int(np.ceil(L / step)) + (0 if closed else 1))
    t = np.linspace(0, L, n, endpoint=not closed)
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1), L


def _normals(P, closed):
    if closed: T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else: T = np.gradient(P, axis=0)
    n = np.hypot(T[:, 0], T[:, 1])[:, None] + 1e-9
    T = T / n
    return np.stack([-T[:, 1], T[:, 0]], 1), T


def _pnoise(n, cycles, rng):
    """periodic 1D noise over n samples with about `cycles` waves, roughly in [-1, 1]"""
    s = np.arange(n) / n
    k0 = max(1, int(cycles * 0.6)); k1 = max(k0 + 1, int(cycles * 1.6) + 1)
    out = np.zeros(n)
    for k in range(k0, k1 + 1):
        out += rng.normal() / (k / max(cycles, 1)) ** 0.7 * np.sin(2 * np.pi * (k * s + rng.random()))
    return out / (np.abs(out).max() + 1e-9)


def closed_spline(pts, per=10):
    """closed Catmull-Rom through the control points"""
    P = np.asarray(pts, np.float64)
    n = len(P)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def open_spline(pts, per=10):
    P = np.asarray(pts, np.float64)
    if len(P) < 3:
        t = np.linspace(0, 1, per * 2)[:, None]
        return P[0] + (P[-1] - P[0]) * t
    return spline(P, per).astype(np.float64)


class Patch:
    """a mask on a box of the canvas: x0, y0 and an (h, w) float array"""
    __slots__ = ('x0', 'y0', 'm')

    def __init__(self, x0, y0, m):
        self.x0, self.y0, self.m = int(x0), int(y0), m

    @property
    def box(self):
        return self.x0, self.y0, self.x0 + self.m.shape[1], self.y0 + self.m.shape[0]

    def at(self, x0, y0, x1, y1):
        """this patch's values on the box (zeros outside it)"""
        out = np.zeros((y1 - y0, x1 - x0), np.float32)
        a0, b0, a1, b1 = self.box
        ix0, iy0, ix1, iy1 = max(x0, a0), max(y0, b0), min(x1, a1), min(y1, b1)
        if ix1 > ix0 and iy1 > iy0:
            out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = self.m[iy0 - b0:iy1 - b0, ix0 - a0:ix1 - a0]
        return out


class SpotIllustration:
    def __init__(self, W=1500, H=2000, seed=0, keep_stages=True, stages_dir=None):
        self.W, self.H = int(W), int(H)
        self.k = min(W, H) / 1000.0
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.paper_rgb = hexc('paper')
        self.C = np.ones((self.H, self.W, 3), np.float32) * self.paper_rgb
        self.fine = noise2d(self.H, self.W, 1.3, 2, seed + 11)            # print grain, fraying of edges
        self.mid = noise2d(self.H, self.W, 34 * self.k, 3, seed + 12)      # gaps that come and go, mottle
        self.fin = {}

    # ------------------------------------------------------------------ surface
    def paper(self, tone='paper', grain=1.0):
        self.paper_rgb = hexc(tone)
        self.C[:] = self.paper_rgb
        self.paper_grain = grain
        return self

    def finish(self, grain=1.0, speckle=1.0, soft=0.25):
        """record the print finish (applied in render so every stage snapshot matches the final look)"""
        self.fin = dict(grain=grain, speckle=speckle, soft=soft)
        return self

    def _r(self, seed=None):
        return np.random.default_rng(self.rng.integers(1 << 30) if seed is None else seed)

    # ------------------------------------------------------------------ outlines
    def ellipse(self, cx, cy, rx, ry=None, rot=0.0, n=None):
        ry = rx if ry is None else ry
        n = n or max(24, int(2 * np.pi * max(rx, ry) / 3))
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        x, y = np.cos(t) * rx, np.sin(t) * ry
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)

    def rrect(self, x0, y0, x1, y1, r=None):
        r = min(abs(x1 - x0), abs(y1 - y0)) * 0.18 if r is None else r
        r = min(r, abs(x1 - x0) / 2, abs(y1 - y0) / 2)
        out = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for a in np.linspace(a0, a0 + 90, 8):
                out.append((cx + r * np.cos(np.deg2rad(a)), cy + r * np.sin(np.deg2rad(a))))
        return np.array(out)

    def blob(self, cx, cy, rx, ry=None, rough=0.08, rot=0.0, seed=None):
        ry = rx if ry is None else ry
        n = max(30, int(2 * np.pi * max(rx, ry) / 4))
        r = self._r(seed)
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        w = 1 + rough * _pnoise(n, 5, r)
        x, y = np.cos(t) * rx * w, np.sin(t) * ry * w
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)

    def curve(self, pts, per=10):
        return closed_spline(pts, per)

    def tube(self, path, widths, cap='round', smooth=True):
        """closed outline of a ribbon along `path` (widths: a number or one per control point; cap 'round' /
        'flat' / ('flat', 'round') for start / end)"""
        P = open_spline(path, 10) if smooth else np.asarray(path, np.float64)
        P, L = _resample(P, max(1.0, 1.5 * self.k), closed=False)
        w = np.atleast_1d(np.asarray(widths, np.float64))
        wt = np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, len(w)), w) if len(w) > 1 else np.full(len(P), w[0])
        N, T = _normals(P, False)
        left, right = P + N * wt[:, None] / 2, P - N * wt[:, None] / 2
        caps = (cap, cap) if isinstance(cap, str) else cap
        th = np.linspace(0, np.pi, 9)[1:-1]
        end = P[-1] + (wt[-1] / 2) * (np.cos(th)[:, None] * N[-1] + np.sin(th)[:, None] * T[-1]) if caps[1] == 'round' else np.zeros((0, 2))
        start = P[0] + (wt[0] / 2) * (np.cos(th)[:, None] * -N[0] + np.sin(th)[:, None] * -T[0]) if caps[0] == 'round' else np.zeros((0, 2))
        return np.vstack([left, end, right[::-1], start])

    # ------------------------------------------------------------------ rasterising
    def _wobble(self, pts, amp, r, lam=80.0):
        P, L = _resample(pts, max(1.2, 2.2 * self.k), closed=True)
        if amp <= 0 or len(P) < 8: return P
        N, _ = _normals(P, True)
        lam = lam * self.k
        d = amp * self.k * (1.0 * _pnoise(len(P), L / lam, r) + 0.35 * _pnoise(len(P), L / (lam / 5), r))
        return P + N * d[:, None]

    def _raster(self, pts, pad=2, ss=3):
        pts = np.asarray(pts, np.float64)
        x0 = max(0, int(np.floor(pts[:, 0].min())) - pad); x1 = min(self.W, int(np.ceil(pts[:, 0].max())) + pad + 1)
        y0 = max(0, int(np.floor(pts[:, 1].min())) - pad); y1 = min(self.H, int(np.ceil(pts[:, 1].max())) + pad + 1)
        if x1 <= x0 or y1 <= y0: return None
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        q = (pts - [x0, y0]) * ss
        ImageDraw.Draw(im).polygon([tuple(p) for p in q], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return Patch(x0, y0, m)

    def _fray(self, P, rough):
        if rough <= 0: return P
        x0, y0, x1, y1 = P.box
        n = self.fine[y0:y1, x0:x1]
        P.m = np.clip((P.m - 0.5) * 1.3 + 0.5 + rough * 0.3 * (n - 0.5), 0, 1)
        return P

    def _restrict(self, P, clip=None, avoid=None):
        if clip is None and avoid is None: return P
        x0, y0, x1, y1 = P.box
        m = P.m
        if clip is not None:
            for c in (clip if isinstance(clip, (list, tuple)) else [clip]): m = m * c.at(x0, y0, x1, y1)
        if avoid is not None:
            for a in (avoid if isinstance(avoid, (list, tuple)) else [avoid]): m = m * (1 - a.at(x0, y0, x1, y1))
        return Patch(x0, y0, m)

    def _apply(self, P, colour, alpha=1.0):
        x0, y0, x1, y1 = P.box
        sl = self.C[y0:y1, x0:x1]
        a = (P.m * alpha)[..., None]
        sl += (hexc(colour) - sl) * a

    def union(self, *patches):
        ps = [p for p in patches if p is not None]
        x0 = min(p.x0 for p in ps); y0 = min(p.y0 for p in ps)
        x1 = max(p.box[2] for p in ps); y1 = max(p.box[3] for p in ps)
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        for p in ps: m = np.maximum(m, p.at(x0, y0, x1, y1))
        return Patch(x0, y0, m)

    def grow(self, P, px):
        """a patch grown (px > 0) or shrunk (px < 0) by about px"""
        pad = int(abs(px) * 2) + 2
        x0, y0, x1, y1 = P.box
        X0, Y0, X1, Y1 = max(0, x0 - pad), max(0, y0 - pad), min(self.W, x1 + pad), min(self.H, y1 + pad)
        m = blur(P.at(X0, Y0, X1, Y1), abs(px) * 0.6)
        thr = 0.18 if px > 0 else 0.82
        return Patch(X0, Y0, np.clip((m - thr) * 6 + 0.5, 0, 1))

    # ------------------------------------------------------------------ painting
    def shape(self, pts, colour, smooth=False, wobble=1.0, rough=1.0, gap=0.0, gap_keep=0.75, clip=None, avoid=None,
              alpha=1.0, lumps=80.0, seed=None):
        """a flat, opaque, hand-cut shape. `gap` cuts a white gap of about that many px round it first (on
        `gap_keep` of its edge, in stretches). Returns the patch."""
        r = self._r(seed)
        pts = closed_spline(pts, 8) if smooth else np.asarray(pts, np.float64)
        pts = self._wobble(pts, wobble, r, lumps)
        P = self._raster(pts, pad=int(gap * 3) + 3 if gap else 2)
        if P is None: return None
        self._fray(P, rough)
        if gap > 0:
            x0, y0, x1, y1 = P.box
            D = blur(P.m, gap * 0.55)
            n = self.mid[y0:y1, x0:x1]
            n = (n - 0.5) * 1.6 + 0.5
            thr = 0.06 + 0.5 * smoothstep(gap_keep - 0.06, gap_keep + 0.06, n)
            ring = np.clip((D - thr) * 9, 0, 1) * (1 - P.m)
            G = self._restrict(Patch(x0, y0, ring), clip=None, avoid=avoid)
            self._apply(G, self.paper_rgb)
        P = self._restrict(P, clip, avoid)
        self._apply(P, colour, alpha)
        return P

    def knock(self, pts, smooth=False, wobble=1.0, gap=0.0, **kw):
        """a paper-white shape (skin, a white mug, the gap of a handle)"""
        return self.shape(pts, self.paper_rgb, smooth=smooth, wobble=wobble, gap=gap, **kw)

    def line(self, path, width=None, colour='ink', taper=(0.2, 0.25), wobble=0.6, clip=None, avoid=None, smooth=True,
             closed=False, tip=0.35, alpha=1.0, seed=None):
        """a thin hand line: a ribbon tapering to `tip` x width over the first / last `taper` of its length"""
        r = self._r(seed)
        width = (2.6 * self.k) if width is None else width
        P = np.asarray(path, np.float64)
        if closed: P = np.vstack([P, P[:1]])
        P = open_spline(P, 10) if smooth and len(P) > 2 else P
        P, L = _resample(P, max(0.8, 1.2 * self.k), closed=False)
        if len(P) < 2: return None
        n = len(P)
        N, T = _normals(P, False)
        if wobble:
            P = P + N * (wobble * self.k * fbm1d(n, max(4, 40 * self.k / max(L / n, 1e-3)), 3, int(r.integers(1 << 30))))[:, None]
            N, T = _normals(P, False)
        t = np.linspace(0, 1, n)
        ta, tb = (taper, taper) if np.isscalar(taper) else taper
        prof = np.ones(n)
        if ta > 0: prof = np.minimum(prof, tip + (1 - tip) * np.clip(t / ta, 0, 1) ** 0.6)
        if tb > 0: prof = np.minimum(prof, tip + (1 - tip) * np.clip((1 - t) / tb, 0, 1) ** 0.6)
        wv = width * prof * (1 + 0.12 * fbm1d(n, max(3, n / 3), 2, int(r.integers(1 << 30))))
        left, right = P + N * wv[:, None] / 2, P - N * wv[:, None] / 2
        th = np.linspace(0, np.pi, 7)[1:-1]
        end = P[-1] + (wv[-1] / 2) * (np.cos(th)[:, None] * N[-1] + np.sin(th)[:, None] * T[-1])
        start = P[0] + (wv[0] / 2) * (np.cos(th)[:, None] * -N[0] + np.sin(th)[:, None] * -T[0])
        Pp = self._raster(np.vstack([left, end, right[::-1], start]), pad=2, ss=4)
        if Pp is None: return None
        Pp = self._restrict(Pp, clip, avoid)
        self._apply(Pp, colour, alpha)
        return Pp

    def cut(self, path, width=None, **kw):
        """a white line cut into a colour (a fold, a seam, a strand of hair)"""
        return self.line(path, width, self.paper_rgb, **kw)

    def under(self, path):
        """the mean colour on the canvas under a path"""
        P = np.asarray(path, np.float64)
        xs = np.clip(P[:, 0].astype(int), 0, self.W - 1); ys = np.clip(P[:, 1].astype(int), 0, self.H - 1)
        return self.C[ys, xs].mean(0)

    def fold(self, path, width=None, colour=None, clip=None, **kw):
        """a fold or seam: white on dark and mid fabric, a darker shade on pale fabric (pass colour= to force)"""
        if colour is None:
            c = self.under(path)
            colour = self.paper_rgb if _lum(c) < 0.74 else c * 0.78 + hexc('ink') * 0.1
        return self.line(path, width, colour, clip=clip, **kw)

    def dot(self, x, y, r, colour='ink', **kw):
        return self.shape(self.ellipse(x, y, r, r), colour, wobble=0.25, rough=0.3, **kw)

    # ------------------------------------------------------------------ people: parts
    def limb(self, path, widths, colour, cap=('round', 'flat'), gap=0.0, gap_keep=0.75, clip=None, avoid=None, seed=None):
        """a sleeve or a trouser leg: a fat tube along [shoulder/hip, elbow/knee, wrist/ankle], flat at the cuff"""
        return self.shape(self.tube(path, widths, cap), colour, wobble=1.2, gap=gap, gap_keep=gap_keep, clip=clip,
                          avoid=avoid, seed=seed)

    def torso(self, sh_back, sh_front, hem_back, hem_front, colour, facing=1, collar=None, bulge=0.12, gap=0.0,
              hood=False, seed=None):
        """a boxy oversized top from its shoulders (back, front) and hem corners (back, front), built in its own
        frame (so it works for a figure lying down); `collar` = the neck base -- the neckline dips round it"""
        sb, sf, hb, hf = (np.asarray(p, np.float64) for p in (sh_back, sh_front, hem_back, hem_front))
        up = (sb + sf) / 2 - (hb + hf) / 2; up /= (np.hypot(*up) + 1e-9)
        fw = np.array([-up[1], up[0]])
        if np.dot(fw, sf - sb) < 0: fw = -fw
        dn = -up
        wid = np.hypot(*(sf - sb))
        cx = (sb + sf) / 2 if collar is None else np.asarray(collar, np.float64)

        def V(a, b):
            return fw * a * wid + dn * b * wid

        pts = [cx + V(-0.18, -0.02), sb + V(0.05, -0.06), sb + V(-0.07, 0.12), (sb + hb) / 2 + V(-bulge, 0),
               hb + V(-0.02, -0.04), hb + V(0.08, 0.015), (hb + hf) / 2 + V(0, 0.03), hf + V(-0.08, 0.015),
               hf + V(0.02, -0.04), (sf + hf) / 2 + V(bulge * 0.7, 0), sf + V(0.06, 0.12), sf + V(-0.04, -0.05),
               cx + V(0.2, 0.02), cx + V(0.0, 0.07)]
        if hood:
            pts[0] = cx + V(-0.3, -0.12)
            pts.insert(1, cx + V(-0.45, 0.0))
        return self.shape(pts, colour, smooth=True, wobble=1.3, gap=gap, seed=seed)

    def head(self, cx, cy, r, facing=1, turn=0.5, tilt=0.0, hair='bob', hair_colour='black', eye='dot', ear=False,
             strands=2, skin='paper', line='ink', mouth=None, fringe=1.0, hat='mustard', seed=None, draw_hair=True):
        """a head seen in profile (turn=0) to three-quarter (turn=1) facing right (+1) or left (-1): a white face
        with a profile line, a dot eye, a hair blob with cut strands. `eye`: 'dot', 'closed', 'smile', 'down',
        None. `hair`: 'bob', 'short', 'bun', 'long', 'cap', None. Returns a dict of useful points (chin, nape,
        eye, nose, mouth, top) and the face patch."""
        r_ = self._r(seed)
        ca, sa = np.cos(np.deg2rad(tilt)), np.sin(np.deg2rad(tilt))

        def X(pts):
            p = np.asarray(pts, np.float64) * r
            x, y = p[:, 0] * facing, p[:, 1]
            return np.stack([cx + x * ca - y * sa, cy + x * sa + y * ca], 1)

        nose = 0.13 * (1 - 0.55 * turn)
        face = [(0.0, -1.0), (0.5, -0.86), (0.78, -0.55), (0.86, -0.24), (0.85, -0.04), (0.86 + nose, 0.15),
                (0.83, 0.26), (0.845, 0.35), (0.82, 0.41), (0.835, 0.47), (0.79, 0.6), (0.77, 0.7), (0.66, 0.81),
                (0.42, 0.86), (0.12, 0.7), (-0.15, 0.55), (-0.72, 0.42), (-0.95, 0.0), (-0.74, -0.66)]
        skin_rgb = self.paper_rgb if skin == 'paper' else hexc(skin)
        F = self.shape(X(closed_spline(face, 6)), skin_rgb, wobble=0.5, rough=0.5, seed=int(r_.integers(1 << 30)))
        prof = [(0.84, -0.3), (0.85, -0.04), (0.86 + nose, 0.15), (0.83, 0.26), (0.845, 0.35), (0.82, 0.41),
                (0.835, 0.47), (0.79, 0.6), (0.77, 0.7), (0.66, 0.81), (0.45, 0.86)]
        lw = 0.042 * r
        self.line(X(prof), lw, line, taper=(0.25, 0.35), tip=0.15, wobble=0.3)
        out = dict(face=F, chin=X([(0.7, 0.82)])[0], nape=X([(-0.25, 0.55)])[0], eye=X([(0.5 + 0.08 * turn, -0.02)])[0],
                   nose=X([(0.86 + nose, 0.15)])[0], mouth=X([(0.8, 0.43)])[0], top=X([(0.0, -1.0)])[0],
                   neck_top=X([(0.2, 0.7)])[0], X=X)
        if ear:
            self.line(X([(-0.02, -0.05), (0.1, -0.12), (0.16, 0.05), (0.08, 0.22), (0.0, 0.2)]), lw * 0.9, line,
                      taper=0.3, wobble=0.2)
        if draw_hair and hair:
            self.hair(out, hair, hair_colour, strands, fringe, hat, seed=int(r_.integers(1 << 30)))
        ex, ey = out['eye']
        if eye == 'dot':
            self.dot(ex, ey, 0.055 * r, line)
        elif eye == 'down':
            self.line(X([(0.43 + 0.08 * turn, 0.0), (0.5 + 0.08 * turn, 0.03), (0.57 + 0.08 * turn, 0.01)]), lw * 1.1,
                      line, taper=0.3, wobble=0.1)
        elif eye == 'closed':
            self.line(X([(0.42 + 0.08 * turn, -0.01), (0.5 + 0.08 * turn, 0.04), (0.58 + 0.08 * turn, 0.0)]), lw * 1.1,
                      line, taper=0.3, wobble=0.1)
        elif eye == 'smile':
            self.line(X([(0.42 + 0.08 * turn, 0.03), (0.5 + 0.08 * turn, -0.03), (0.58 + 0.08 * turn, 0.02)]), lw * 1.1,
                      line, taper=0.3, wobble=0.1)
        if mouth == 'open':
            self.dot(*X([(0.78, 0.44)])[0], 0.045 * r, line)
        return out

    def hair(self, h, style='bob', colour='black', strands=2, fringe=1.0, hat='mustard', seed=None):
        """the hair blob for a head() result `h` (drawn by head() unless draw_hair=False)"""
        X = h['X']
        r_ = self._r(seed)
        fr = fringe
        if style == 'bob':
            pts = [(0.56, -0.84), (0.76, -0.6), (0.77, -0.34 + 0.08 * (1 - fr)), (0.66, -0.42), (0.56, -0.28), (0.46, -0.42),
                   (0.34, -0.3), (0.24, -0.4), (0.15, -0.14), (0.14, 0.18), (0.1, 0.46), (0.02, 0.62), (-0.16, 0.56),
                   (-0.36, 0.68), (-0.6, 0.56), (-0.84, 0.6), (-0.98, 0.3), (-1.08, -0.06), (-1.0, -0.5), (-0.84, -0.84),
                   (-0.5, -1.06), (-0.12, -1.1), (0.26, -1.06)]
        elif style == 'short':
            pts = [(0.56, -0.86), (0.76, -0.62), (0.74, -0.44), (0.6, -0.5), (0.48, -0.38), (0.34, -0.48), (0.2, -0.36),
                   (0.14, -0.12), (0.06, 0.1), (-0.1, 0.32), (-0.34, 0.3), (-0.6, 0.42), (-0.86, 0.26), (-1.02, -0.12),
                   (-0.94, -0.6), (-0.66, -0.94), (-0.24, -1.1), (0.22, -1.06)]
        elif style == 'bun':
            pts = [(0.56, -0.84), (0.74, -0.6), (0.66, -0.5), (0.5, -0.56), (0.32, -0.46), (0.16, -0.24), (0.08, 0.06),
                   (-0.08, 0.32), (-0.36, 0.36), (-0.66, 0.38), (-0.9, 0.18), (-1.02, -0.2), (-0.9, -0.66), (-0.5, -1.0),
                   (-0.04, -1.08), (0.3, -1.02)]
        elif style == 'long':
            pts = [(0.56, -0.84), (0.76, -0.6), (0.76, -0.36), (0.64, -0.42), (0.54, -0.3), (0.44, -0.42), (0.32, -0.3),
                   (0.22, -0.4), (0.14, -0.12), (0.12, 0.3), (0.06, 0.9), (-0.08, 1.38), (-0.32, 1.28), (-0.56, 1.46),
                   (-0.86, 1.3), (-1.04, 0.8), (-1.08, 0.1), (-1.0, -0.5), (-0.84, -0.84), (-0.5, -1.06), (-0.12, -1.1),
                   (0.26, -1.06)]
        elif style == 'cap':
            pts = [(0.4, -0.5), (0.2, -0.36), (0.12, -0.12), (0.06, 0.1), (-0.1, 0.32), (-0.34, 0.3), (-0.6, 0.42),
                   (-0.86, 0.26), (-1.0, -0.12), (-0.9, -0.5)]
        else:
            return None
        P = self.shape(X(closed_spline(pts, 5)), colour, wobble=2.4, rough=1.0, lumps=34.0, seed=int(r_.integers(1 << 30)))
        flicks = {'bob': [((-0.3, 0.62), (-0.22, 0.8)), ((-0.72, 0.52), (-0.78, 0.68))],
                  'short': [((-0.4, 0.33), (-0.36, 0.48))],
                  'long': [((-0.3, 1.32), (-0.24, 1.5)), ((-0.8, 1.3), (-0.86, 1.46))]}.get(style, [])
        u_ = self._unit(X)
        for a_, b_ in flicks:
            self.shape(self.tube(X([a_, b_]), [0.1 * u_, 0.01 * u_], ('round', 'round'), smooth=False), colour, wobble=0.3)
        if style == 'bun':
            self.shape(self.blob(*X([(-0.62, -0.92)])[0], 0.36 * self._unit(X), rough=0.12), colour, wobble=1.5)
        if style == 'cap':
            crown = [(-0.96, -0.36), (-0.86, -0.82), (-0.4, -1.1), (0.2, -1.08), (0.6, -0.84), (0.72, -0.5), (0.2, -0.42),
                     (-0.5, -0.4)]
            Cp = self.shape(X(closed_spline(crown, 6)), hat, wobble=1.2)
            self.shape(X(closed_spline([(0.5, -0.56), (0.9, -0.5), (1.12, -0.4), (0.9, -0.34), (0.5, -0.4)], 5)), hat,
                       wobble=0.6)
            self.fold(X([(-0.2, -1.06), (-0.1, -0.7), (-0.12, -0.44)]), 2.0 * self.k, clip=Cp)
            self.dot(*X([(-0.12, -1.1)])[0], 0.05 * self._unit(X), hat)
            return self.union(P, Cp)
        # a couple of strands cut in white near the crown, along the hair's flow toward the face
        cand = [[(-0.5, -0.84), (-0.3, -0.8), (-0.1, -0.7)], [(-0.7, -0.5), (-0.6, -0.36), (-0.52, -0.22)],
                [(-0.14, -0.98), (0.06, -0.92), (0.22, -0.8)], [(-0.86, -0.1), (-0.8, 0.08), (-0.78, 0.24)]]
        if style == 'cap':
            cand = [[(-0.78, -0.3), (-0.66, -0.1), (-0.62, 0.1)]]
        w = 0.045 * self._unit(X)
        for c in cand[:strands]:
            j = np.asarray(c) + r_.normal(0, 0.025, (len(c), 2))
            self.cut(X(j), w, taper=(0.35, 0.45), tip=0.1, wobble=0.2, clip=P)
        return P

    @staticmethod
    def _unit(X):
        a, b = X([(0, 0), (1, 0)])
        return float(np.hypot(*(b - a)))

    def neck(self, top, bottom, w, skin='paper', line='ink', facing=1):
        """a white neck between the jaw and the collar, a thin line down its front"""
        top, bottom = np.asarray(top, np.float64), np.asarray(bottom, np.float64)
        skin_rgb = self.paper_rgb if skin == 'paper' else hexc(skin)
        P = self.shape(self.tube([top, bottom], w, 'flat', smooth=False), skin_rgb, wobble=0.4, rough=0.4)
        d = bottom - top
        n = np.array([d[1], -d[0]]) / (np.hypot(*d) + 1e-9) * facing
        a = top + n * w * 0.42 * -1
        self.line([a + d * 0.05, a + d * 0.4], 1.8 * self.k, line, taper=0.4, wobble=0.15)
        return P

    def hand(self, x, y, angle=0.0, size=40.0, pose='grip', facing=1, finger='red_line', skin='paper', line='ink',
             seed=None):
        """a white mitten-like hand with a thin outline and finger lines. (x, y) is the wrist; `angle` the direction
        the hand points (degrees, 0 = right); `pose`: 'grip' (closed round something, back of the hand seen),
        'open' (flat, fingers together, thumb out), 'fist', 'flat' (palm down, resting), 'cup' (palm up). The
        finger lines are in the accent red by default (pass finger='ink' for dark)."""
        a = np.deg2rad(angle)
        ca, sa = np.cos(a), np.sin(a)
        s = size

        def X(pts):
            p = np.asarray(pts, np.float64) * s
            px, py = p[:, 0], p[:, 1] * facing
            return np.stack([x + px * ca - py * sa, y + px * sa + py * ca], 1)

        skin_rgb = self.paper_rgb if skin == 'paper' else hexc(skin)
        lw = max(1.6 * self.k, 0.055 * s)
        if pose in ('grip', 'fist'):
            # the back of a hand closed round something: four finger bumps along the front edge, red lines between
            front = []
            for i, yc in enumerate((-0.24, -0.08, 0.08, 0.24)):
                for t in np.linspace(-np.pi / 2, np.pi / 2, 5):
                    front.append((0.8 + 0.07 * np.cos(t) - 0.03 * i * (pose == 'fist'), yc + 0.08 * np.sin(t)))
            body = [(-0.04, -0.27), (0.4, -0.33)] + front + [(0.45, 0.33), (0.0, 0.28)]
            P = self.shape(X(body), skin_rgb, wobble=0.25, rough=0.3)
            self.line(X([(0.3, -0.33)] + front + [(0.5, 0.33)]), lw, line, taper=(0.15, 0.3), wobble=0.1)
            for yy in (-0.16, 0.0, 0.16):
                self.line(X([(0.84, yy), (0.7, yy), (0.58, yy + 0.01)]), lw * 0.95, finger, taper=(0.1, 0.4), tip=0.3,
                          wobble=0.05, clip=P)
            self.line(X([(0.12, -0.28), (0.36, -0.2), (0.56, -0.24)]), lw * 0.9, line, taper=0.3, wobble=0.1)
        elif pose == 'open':
            body = [(-0.05, -0.25), (0.4, -0.3), (0.9, -0.24), (1.08, -0.06), (1.06, 0.1), (0.82, 0.24), (0.4, 0.28),
                    (0.0, 0.25)]
            thumb = [(0.18, -0.2), (0.42, -0.52), (0.55, -0.56), (0.55, -0.4), (0.42, -0.18)]
            T = self.shape(X(closed_spline(thumb, 5)), skin_rgb, wobble=0.3, rough=0.4)
            P = self.shape(X(closed_spline(body, 6)), skin_rgb, wobble=0.4, rough=0.4)
            self.line(X(open_spline([(0.25, -0.3), (0.45, -0.52), (0.56, -0.48), (0.48, -0.3)], 6)), lw, line, taper=0.3, wobble=0.1)
            self.line(X(open_spline([(0.5, -0.3), (0.9, -0.24), (1.08, -0.06), (1.06, 0.1), (0.82, 0.24), (0.45, 0.28)], 6)),
                      lw, line, taper=(0.2, 0.3), wobble=0.15)
            for yy in (-0.12, 0.06):
                self.line(X([(0.62, yy - 0.01), (0.82, yy), (0.98, yy + 0.01)]), lw, finger, taper=0.35, wobble=0.1, clip=P)
            P = self.union(P, T)
        elif pose == 'flat':
            body = [(-0.05, -0.2), (0.4, -0.24), (0.95, -0.14), (1.08, 0.02), (0.95, 0.16), (0.4, 0.2), (0.0, 0.2)]
            P = self.shape(X(closed_spline(body, 6)), skin_rgb, wobble=0.4, rough=0.4)
            self.line(X(open_spline([(0.4, -0.24), (0.95, -0.14), (1.08, 0.02), (0.95, 0.16), (0.5, 0.2)], 6)), lw, line,
                      taper=(0.2, 0.3), wobble=0.15)
            for yy in (-0.07, 0.07):
                self.line(X([(0.66, yy), (0.84, yy), (0.98, yy * 0.8)]), lw, finger, taper=0.35, wobble=0.1, clip=P)
        else:  # 'cup': palm up, fingers curled up a little
            body = [(-0.05, -0.2), (0.4, -0.22), (0.8, -0.2), (1.0, -0.38), (1.06, -0.22), (0.96, 0.1), (0.6, 0.26),
                    (0.1, 0.24)]
            P = self.shape(X(closed_spline(body, 6)), skin_rgb, wobble=0.4, rough=0.4)
            self.line(X(open_spline([(0.8, -0.2), (1.0, -0.38), (1.06, -0.22), (0.96, 0.1), (0.6, 0.26), (0.2, 0.25)], 6)),
                      lw, line, taper=(0.2, 0.3), wobble=0.15)
            self.line(X([(0.7, -0.1), (0.86, -0.12), (0.96, -0.24)]), lw, finger, taper=0.35, wobble=0.1, clip=P)
        return P

    def shoe(self, x, y, angle=0.0, size=60.0, colour='paper', facing=1, sole='grey_mid', line='grey_dark', laces=True):
        """a sneaker: (x, y) the ankle, `size` the length heel to toe, `angle` the tilt of the sole (degrees)"""
        a = np.deg2rad(angle * facing)
        ca, sa = np.cos(a), np.sin(a)

        def X(pts):
            p = np.asarray(pts, np.float64) * size
            px, py = p[:, 0] * facing, p[:, 1]
            return np.stack([x + px * ca - py * sa, y + px * sa + py * ca], 1)

        body = [(-0.32, -0.12), (-0.08, -0.2), (0.12, -0.12), (0.38, 0.0), (0.66, 0.07), (0.72, 0.2), (0.66, 0.3),
                (-0.3, 0.3), (-0.38, 0.12)]
        if line is None:     # a stocking foot: slimmer, the toe rounder, no sole
            body = [(-0.22, -0.16), (0.0, -0.14), (0.3, 0.0), (0.62, 0.06), (0.7, 0.16), (0.6, 0.24), (-0.22, 0.2),
                    (-0.3, 0.04)]
        col = self.paper_rgb if colour == 'paper' else hexc(colour)
        P = self.shape(X(closed_spline(body, 6)), col, wobble=0.5, rough=0.5)
        if line is None: return P
        self.line(X(open_spline(body + [body[0]], 6)), max(1.5 * self.k, 0.04 * size), line, taper=0.05, wobble=0.15)
        self.line(X([(-0.34, 0.22), (0.2, 0.25), (0.7, 0.22)]), max(1.6 * self.k, 0.05 * size), sole, taper=0.2, wobble=0.1)
        if laces:
            for t in (0.0, 0.14):
                self.line(X([(0.08 + t, -0.06 + t * 0.4), (0.16 + t, 0.06 + t * 0.4)]), max(1.4 * self.k, 0.035 * size),
                          line, taper=0.3, wobble=0.1)
        return P

    # ------------------------------------------------------------------ people: poses
    POSES = {
        # joints in head-heights (u), origin on the ground between the feet, facing right; y grows downward
        'stand': dict(head=(0.14, -5.2), neck=(0.04, -4.74), sh_b=(-0.42, -4.48), sh_f=(0.42, -4.5), hem_b=(-0.5, -2.6),
                      hem_f=(0.5, -2.62), hip_n=(-0.08, -2.75), hip_f=(0.16, -2.75), knee_n=(-0.04, -1.45),
                      knee_f=(0.18, -1.45), ankle_n=(-0.06, -0.24), ankle_f=(0.22, -0.24), elbow_n=(-0.2, -3.45),
                      wrist_n=(0.3, -3.0), elbow_f=(0.5, -3.5), wrist_f=(0.8, -3.1)),
        'walk': dict(head=(0.26, -5.18), neck=(0.14, -4.72), sh_b=(-0.32, -4.46), sh_f=(0.5, -4.48), hem_b=(-0.42, -2.6),
                     hem_f=(0.55, -2.62), hip_n=(0.0, -2.75), hip_f=(0.2, -2.75), knee_n=(0.5, -1.5), knee_f=(-0.12, -1.42),
                     ankle_n=(0.7, -0.26), ankle_f=(-0.55, -0.34), elbow_n=(-0.28, -3.5), wrist_n=(-0.46, -2.7),
                     elbow_f=(0.62, -3.55), wrist_f=(0.82, -2.8)),
        'sit': dict(head=(0.2, -4.62), neck=(0.08, -4.16), sh_b=(-0.4, -3.92), sh_f=(0.42, -3.95), hem_b=(-0.52, -2.18),
                    hem_f=(0.52, -2.2), hip_n=(-0.05, -2.05), hip_f=(0.1, -2.05), knee_n=(1.15, -2.15), knee_f=(1.2, -2.12),
                    ankle_n=(1.12, -0.24), ankle_f=(1.28, -0.24), elbow_n=(0.0, -2.9), wrist_n=(0.68, -2.75),
                    elbow_f=(0.5, -3.0), wrist_f=(0.95, -2.85)),
        'crouch': dict(head=(0.78, -3.12), neck=(0.42, -2.72), sh_b=(-0.12, -2.72), sh_f=(0.62, -2.42), hem_b=(-0.6, -0.95),
                       hem_f=(0.12, -0.9), hip_n=(-0.3, -0.85), hip_f=(-0.12, -0.85), knee_n=(0.55, -1.5), knee_f=(0.72, -1.4),
                       ankle_n=(0.12, -0.22), ankle_f=(0.34, -0.2), elbow_n=(0.72, -1.82), wrist_n=(1.2, -1.05),
                       elbow_f=(0.95, -2.05), wrist_f=(1.05, -1.5)),
        'reach': dict(head=(0.2, -5.18), neck=(0.08, -4.74), sh_b=(-0.38, -4.48), sh_f=(0.45, -4.5), hem_b=(-0.48, -2.6),
                      hem_f=(0.52, -2.62), hip_n=(-0.06, -2.75), hip_f=(0.16, -2.75), knee_n=(-0.02, -1.45),
                      knee_f=(0.2, -1.45), ankle_n=(-0.05, -0.24), ankle_f=(0.26, -0.24), elbow_n=(0.2, -3.35),
                      wrist_n=(0.95, -3.25), elbow_f=(0.7, -3.4), wrist_f=(1.3, -3.4)),
    }
    ORDER = {'crouch': ('leg_far', 'arm_far', 'hand_far', 'torso', 'leg_near', 'head', 'arm_near', 'hand_near'),
             'default': ('leg_far', 'arm_far', 'hand_far', 'leg_near', 'torso', 'head', 'arm_near', 'hand_near')}

    def pose(self, name, x, y, u, facing=1, rot=0.0, rel=None, **joints):
        """joint positions (canvas px) for a preset pose, mirrored by `facing` and turned by `rot` degrees about
        (x, y); `rel` overrides joints in head units in the preset's own frame, keyword joints in canvas px"""
        P = dict(self.POSES[name])
        P.update(rel or {})
        c, s_ = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        J = {}
        for k, (jx, jy) in P.items():
            dx, dy = jx * u * facing, jy * u
            J[k] = np.array([x + dx * c - dy * s_, y + dx * s_ + dy * c])
        for k, v in joints.items():
            if v is not None and k in J: J[k] = np.asarray(v, np.float64)
        return J

    def person(self, x, y, u, facing=1, pose='stand', outfit=None, hooks=None, rel=None, rot=0.0, J=None, order=None,
               folds=True, **joints):
        """a whole figure from a pose preset. `u` = one head height in px; `rot` turns the whole figure (degrees,
        -90 lays a right-facing figure on its back, head to the left); `rel` overrides joints in head units (the
        preset's frame), keyword joints in canvas px. `outfit` keys: top, bottom, hair, hair_style, shoes, sole,
        laces, socks, eye, turn, tilt, skin, hood, sleeve (if not the top's colour), apron, hand_n / hand_f (a
        hand pose, (pose, angle) or None to hide it), strands, fringe, coat (hem lower). `hooks` maps a layer name
        ('leg_far', 'arm_far', 'hand_far', 'leg_near', 'torso', 'head', 'arm_near', 'hand_near', 'end') to a
        function called *before* that layer -- slip props in between. `order` overrides the layer order. Returns
        the joints and the patches."""
        o = dict(top='mustard', bottom='navy', hair='black', hair_style='bob', shoes='paper', sole='grey_mid',
                 laces=True, socks=None, eye='dot', turn=0.5, tilt=0.0, skin='paper', hood=False, sleeve=None,
                 apron=None, hand_n='grip', hand_f='grip', strands=2, fringe=1.0, hat='mustard')
        o.update(outfit or {})
        hooks = hooks or {}
        J = J if J is not None else self.pose(pose, x, y, u, facing, rot, rel, **joints)
        f = facing
        cr, sr = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        out = dict(J=J)
        top_c = o['top']; slv = o['sleeve'] or top_c
        legw = [0.62 * u, 0.56 * u, 0.5 * u]
        armw = [0.5 * u, 0.54 * u, 0.42 * u]
        order = order or self.ORDER.get(pose, self.ORDER['default'])

        def V(dx, dy):
            """an offset in the figure's frame (x forward, y down, head units) -> canvas px"""
            dx, dy = dx * u * f, dy * u
            return np.array([dx * cr - dy * sr, dx * sr + dy * cr])

        def unit(v):
            return v / (np.hypot(*v) + 1e-9)

        def leg(n):
            hip, knee, ank = J['hip_' + n], J['knee_' + n], J['ankle_' + n]
            d = unit(ank - knee)
            if o['socks']:
                self.limb([ank - d * 0.3 * u, ank + d * 0.06 * u], [0.28 * u, 0.28 * u], o['socks'], cap='flat')
            P = self.limb([hip, knee, ank - d * (0.2 if o['socks'] else 0.02) * u], legw, o['bottom'], cap=('round', 'flat'),
                          gap=3.0 * self.k if n == 'n' else 0.0, gap_keep=0.85)
            if folds:
                t = unit(knee - hip); nn = np.array([-d[1], d[0]])
                fwd = V(1, 0) / u
                side = 1 if np.dot(nn, fwd) > 0 else -1
                self.fold([knee + d * 0.25 * u + nn * side * 0.06 * u, knee + d * 0.7 * u + nn * side * 0.1 * u,
                           ank - d * 0.4 * u + nn * side * 0.08 * u], 2.4 * self.k, clip=P, taper=(0.3, 0.4))
                if np.hypot(*(knee - hip)) > 0.8 * u and np.dot(t, V(0, -1) / u) < 0.35:
                    tn = np.array([-t[1], t[0]])
                    self.fold([hip + t * 0.45 * u - tn * 0.1 * u, knee - t * 0.12 * u - tn * 0.04 * u], 2.2 * self.k, clip=P,
                              taper=(0.35, 0.3))
            ang = 0.0
            if pose == 'walk': ang = 6 if n == 'n' else -16
            if pose == 'crouch': ang = 6 if n == 'n' else 2
            sp = ank + V(0.02, 0.07)
            if o['shoes'] is None:      # stocking feet: the sock carries on into a foot
                self.shoe(sp[0], sp[1], ang + rot * f, 0.44 * u, o['socks'] or 'grey_light', f, line=None)
            else:
                self.shoe(sp[0], sp[1], ang + rot * f, 0.56 * u, o['shoes'], f, o['sole'], laces=o['laces'])
            return P

        def arm(n):
            sh = J['sh_b'] + V(0.14, 0.22) if n == 'n' else J['sh_f'] + V(-0.1, 0.2)
            e, w = J['elbow_' + n], J['wrist_' + n]
            P = self.limb([sh, e, w], armw, slv, cap=('round', 'flat'), gap=3.2 * self.k if n == 'n' else 0.0,
                          gap_keep=0.92)
            if folds:
                a1, b1 = unit(e - sh), unit(w - e)
                cr_ = a1[0] * b1[1] - a1[1] * b1[0]
                nin = np.array([-a1[1], a1[0]]) * (1 if cr_ > 0 else -1)
                if abs(cr_) > 0.25:
                    self.fold([e + nin * 0.24 * u - a1 * 0.1 * u, e + nin * 0.06 * u + (b1 - a1) * 0.02 * u,
                               e - nin * 0.08 * u + b1 * 0.1 * u], 2.3 * self.k, clip=P, taper=(0.35, 0.45))
                    self.fold([e + nin * 0.22 * u + b1 * 0.12 * u, e + nin * 0.08 * u + b1 * 0.22 * u], 2.0 * self.k, clip=P,
                              taper=0.4)
                pb = np.array([-b1[1], b1[0]])
                self.fold([w - b1 * 0.2 * u + pb * 0.15 * u, w - b1 * 0.17 * u - pb * 0.12 * u], 2.0 * self.k, clip=P,
                          taper=0.3)
            return P

        def hand(n):
            hp = o['hand_' + n]
            if hp is None: return None
            pose_, ang = (hp if isinstance(hp, tuple) else (hp, None))
            w, e = J['wrist_' + n], J['elbow_' + n]
            d = w - e
            if ang is None: ang = np.rad2deg(np.arctan2(d[1], d[0]))
            dd = unit(d)
            return self.hand(w[0] - dd[0] * 0.08 * u, w[1] - dd[1] * 0.08 * u, ang, 0.36 * u, pose_, f)

        def torso():
            hd = J['head']
            nt = hd + V(0.09, 0.25)
            self.neck(nt, J['neck'] + V(0.04, 0.14), 0.25 * u, facing=f)
            P = self.torso(J['sh_b'], J['sh_f'], J['hem_b'], J['hem_f'], top_c, f, collar=J['neck'], hood=o['hood'])
            if folds:
                hb, hf = J['hem_b'], J['hem_f']
                up = unit((J['sh_b'] + J['sh_f']) / 2 - (hb + hf) / 2)
                acr = np.array([-up[1], up[0]])
                c = hb + (hf - hb) * 0.3 + up * 0.12 * u
                self.fold([c, c + up * 0.32 * u + acr * 0.05 * u], 2.2 * self.k, clip=P, taper=0.35)
            if o['apron']:
                hb, hf = J['hem_b'], J['hem_f']
                top_l = J['neck'] + V(-0.08, 0.32); top_r = J['neck'] + V(0.36, 0.3)
                bot_l = (hb + hf) / 2 + V(-0.2, 0.95); bot_r = hf + V(0.14, 1.0)
                out['apron'] = self.shape([top_l, top_r, (top_r + bot_r) / 2 + V(0.14, 0), bot_r, bot_l,
                                           (top_l + bot_l) / 2 + V(-0.04, 0)], o['apron'], wobble=1.2)
                self.line([top_l, J['neck'] + V(-0.22, 0.04)], 2.4 * self.k, o['apron'], taper=0.0)
            return P

        def head():
            hd = J['head']
            return self.head(hd[0], hd[1], 0.5 * u, f, o['turn'], o['tilt'] + rot, o['hair_style'], o['hair'], o['eye'],
                             strands=o['strands'], skin=o['skin'], fringe=o['fringe'], hat=o['hat'])

        parts = dict(leg_far=lambda: leg('f'), arm_far=lambda: arm('f'), hand_far=lambda: hand('f'),
                     leg_near=lambda: leg('n'), torso=torso, head=head, arm_near=lambda: arm('n'),
                     hand_near=lambda: hand('n'))
        for name in order:
            if name in hooks: hooks[name]()
            out[name] = parts[name]()
        if 'end' in hooks: hooks['end']()
        return out

    # ------------------------------------------------------------------ props
    def mug(self, x, y, h, colour='red', facing=1, handle=True, inner=None):
        """a mug standing on (x, y) (bottom centre), height h, the handle on the `facing` side, a darker rim
        ellipse (or `inner`)"""
        w = h * 0.86
        body = [(x - w / 2, y - h), (x + w / 2, y - h), (x + w / 2 * 0.97, y - h * 0.1), (x + w / 2 * 0.88, y),
                (x - w / 2 * 0.88, y), (x - w / 2 * 0.97, y - h * 0.1)]
        if handle:
            hx = x + facing * w / 2
            ring = self.tube([(hx - facing * 2, y - h * 0.78), (hx + facing * h * 0.32, y - h * 0.72),
                              (hx + facing * h * 0.34, y - h * 0.38), (hx - facing * 2, y - h * 0.3)], h * 0.13, 'round')
            self.shape(ring, colour, wobble=0.5)
        P = self.shape(body, colour, wobble=0.6)
        self.shape(self.ellipse(x, y - h, w / 2 * 0.97, h * 0.1), inner or mix(colour, 'ink', 0.25), wobble=0.4, clip=P)
        return P

    def bowl(self, x, y, w, h=None, colour='red', inner='pale', fill=None):
        """a bowl sitting on (x, y) (bottom centre), width w; the rim shows a pale inside ('pale' = the colour mixed
        with paper) and `fill` paints what's in it"""
        h = w * 0.45 if h is None else h
        rim = self.ellipse(x, y - h, w / 2, w * 0.1)
        body = [(x - w / 2, y - h), (x + w / 2, y - h), (x + w * 0.4, y - h * 0.35), (x + w * 0.22, y - h * 0.03),
                (x - w * 0.22, y - h * 0.03), (x - w * 0.4, y - h * 0.35)]
        P = self.shape(closed_spline(body, 6), colour, wobble=0.7)
        self.shape(rim, mix(colour, 'paper', 0.7) if inner == 'pale' else inner, wobble=0.5)
        if fill:
            self.shape(self.ellipse(x, y - h + w * 0.02, w / 2 * 0.86, w * 0.07), fill, wobble=0.5)
        self.shape([(x - w * 0.2, y - h * 0.08), (x + w * 0.2, y - h * 0.08), (x + w * 0.22, y + 1), (x - w * 0.22, y + 1)],
                   colour, wobble=0.4)
        return P

    def pot(self, x, y, w, colour='red', lid=True):
        """an enamel cooking pot on (x, y) (bottom centre), width w; two side handles, a lid with a dark knob"""
        h = w * 0.62
        P = self.shape(self.rrect(x - w / 2, y - h, x + w / 2, y, w * 0.08), colour, wobble=0.8)
        self.shape(self.rrect(x + w / 2 - 2, y - h * 0.82, x + w / 2 + w * 0.13, y - h * 0.7, w * 0.03), colour, wobble=0.4)
        self.shape(self.rrect(x - w / 2 - w * 0.13, y - h * 0.84, x - w / 2 + 2, y - h * 0.7, w * 0.03), colour, wobble=0.4)
        if lid:
            self.shape(self.ellipse(x, y - h, w * 0.52, w * 0.07), mix(colour, 'ink', 0.2), wobble=0.5)
            self.shape(self.ellipse(x, y - h - w * 0.06, w * 0.07, w * 0.04), 'ink', wobble=0.3)
        self.fold([(x - w * 0.36, y - h * 0.18), (x + w * 0.36, y - h * 0.18)], 2.0 * self.k, clip=P)
        return P

    def bag(self, x, y, w, h=None, colour='red', handles=True):
        """a tote bag, (x, y) its bottom centre, width w, height h; two strap loops on top"""
        h = w * 1.0 if h is None else h
        if handles:
            for dx in (-0.22, 0.22):
                self.line([(x + (dx - 0.1) * w, y - h * 0.95), (x + dx * w, y - h * 1.45), (x + (dx + 0.1) * w, y - h * 0.95)],
                          w * 0.07, colour, taper=0.0, wobble=0.4)
        body = [(x - w * 0.46, y - h), (x + w * 0.46, y - h), (x + w * 0.5, y - h * 0.5), (x + w * 0.52, y),
                (x - w * 0.52, y), (x - w * 0.5, y - h * 0.5)]
        return self.shape(body, colour, smooth=False, wobble=1.0)

    def umbrella(self, x, y, r, angle=0.0, colour='red', handle_len=None, line='ink'):
        """an open umbrella: (x, y) the top of the shaft, r the canopy radius, `angle` its tilt (deg, + leans the top
        to the right), `handle_len` the shaft length in canopy radii (default 1.75), a crook at the end"""
        a = np.deg2rad(angle)
        ca, sa = np.cos(a), np.sin(a)

        def X(pts):
            p = np.asarray(pts, np.float64) * r
            return np.stack([x + p[:, 0] * ca - p[:, 1] * sa, y + p[:, 0] * sa + p[:, 1] * ca], 1)

        L = 1.75 if handle_len is None else handle_len
        self.line(X([(0, 0.02), (0, L)]), max(2.2 * self.k, 0.045 * r), line, taper=0.0, wobble=0.15, smooth=False)
        self.line(X([(0, L - 0.02), (0.0, L + 0.12), (0.1, L + 0.2), (0.2, L + 0.12)]), max(2.4 * self.k, 0.05 * r), line,
                  taper=(0, 0.3), wobble=0.1)
        t = np.linspace(np.pi, 2 * np.pi, 40)
        dome = list(zip(np.cos(t) * 1.0, np.sin(t) * 0.72 + 0.36))
        sc = []
        for i in range(4):
            x0_, x1_ = 1.0 - i * 0.5, 1.0 - (i + 1) * 0.5
            for tt in np.linspace(0, 1, 8)[1:]:
                xx = x0_ + (x1_ - x0_) * tt
                sc.append((xx, 0.36 - 0.1 * np.sin(np.pi * tt)))
        P = self.shape(X(dome + sc), colour, wobble=1.0)
        for xx in (-0.5, 0.0, 0.5):
            self.cut(X([(0, -0.34), (xx * 0.6, -0.1), (xx, 0.27)]), 2.2 * self.k, taper=(0.1, 0.3), clip=P, wobble=0.2)
        self.shape(X(self.ellipse(0, -0.4, 0.04, 0.05) / 1.0), line, wobble=0.2)
        return P

    def bench(self, x0, x1, y, h, colour='grey_light', legs='ink', back=True):
        """a park bench seen from the front: floor at y, seat height h (seat top at y - h), a back rail above it"""
        t = h * 0.13
        if back:
            self.shape(self.rrect(x0 + h * 0.1, y - h * 1.78, x1 - h * 0.1, y - h * 1.6, 3 * self.k), colour, wobble=0.8)
            for xx in (x0 + h * 0.3, x1 - h * 0.3):
                self.line([(xx, y - h * 1.62), (xx, y - h)], 3.0 * self.k, legs, taper=(0, 0.1), wobble=0.3)
        for xx in (x0 + h * 0.18, x0 + h * 0.36, x1 - h * 0.36, x1 - h * 0.18):
            self.line([(xx, y - h + t * 0.5), (xx + (xx - (x0 + x1) / 2) * 0.03, y)], 3.2 * self.k, legs, taper=(0, 0.1),
                      wobble=0.3)
        return self.shape(self.rrect(x0, y - h - t * 0.5, x1, y - h + t * 0.6, 3 * self.k), colour, wobble=0.8)

    def chair(self, x, y, h, facing=1, colour='wood', legs='ink'):
        """a simple chair in profile, seat at (x, y) (seat front-back centre), seat height h"""
        f = facing
        d = h * 0.5
        for xx in (x - f * d * 0.42, x + f * d * 0.42):
            self.line([(xx, y), (xx, y + h)], 3.0 * self.k, legs, taper=(0, 0.1), wobble=0.3)
        self.line([(x - f * d * 0.48, y), (x - f * d * 0.56, y - h * 1.0)], 3.0 * self.k, legs, taper=(0, 0.1), wobble=0.3)
        self.shape(self.rrect(x - f * d * 0.62 - 1, y - h * 1.0, x - f * d * 0.42, y - h * 0.62, 3 * self.k) if f > 0 else
                   self.rrect(x + d * 0.42, y - h * 1.0, x + d * 0.62, y - h * 0.62, 3 * self.k), colour, wobble=0.7)
        return self.shape(self.rrect(x - d * 0.55, y - h * 0.05, x + d * 0.55, y + h * 0.07, 3 * self.k), colour, wobble=0.7)

    def armchair(self, x, y, w, h, facing=1, colour='olive', legs='ink'):
        """a soft armchair in profile: (x, y) the floor under its middle, width w, height h (top of the back).
        Draws the legs, back and seat; returns a dict with 'arm' -- call it after the sitter's legs and body to lay
        the near armrest over them."""
        f = facing
        for xx in (x - f * w * 0.4, x + f * w * 0.4):
            self.line([(xx, y - h * 0.12), (xx + (xx - x) * 0.05, y)], 3.4 * self.k, legs, taper=(0, 0.1), wobble=0.3)
        back = [(x - f * w * 0.52, y - h * 0.9), (x - f * w * 0.44, y - h), (x - f * w * 0.26, y - h * 0.99),
                (x - f * w * 0.18, y - h * 0.9), (x - f * w * 0.22, y - h * 0.5), (x - f * w * 0.3, y - h * 0.3),
                (x - f * w * 0.52, y - h * 0.3), (x - f * w * 0.56, y - h * 0.6)]
        B = self.shape(back, colour, smooth=True, wobble=1.0)
        seat = [(x - f * w * 0.38, y - h * 0.44), (x + f * w * 0.44, y - h * 0.45), (x + f * w * 0.5, y - h * 0.39),
                (x + f * w * 0.5, y - h * 0.3), (x - f * w * 0.48, y - h * 0.3)]
        S = self.shape(seat, colour, smooth=False, wobble=1.0, gap=2.6 * self.k)
        base = self.shape(self.rrect(x - w * 0.54, y - h * 0.31, x + w * 0.54, y - h * 0.12, h * 0.04), colour, wobble=0.8,
                          gap=2.6 * self.k)

        def arm():
            pts = [(x - f * w * 0.3, y - h * 0.55), (x + f * w * 0.3, y - h * 0.565), (x + f * w * 0.4, y - h * 0.52),
                   (x + f * w * 0.38, y - h * 0.31), (x - f * w * 0.3, y - h * 0.31)]
            A = self.shape(pts, colour, smooth=True, wobble=1.0, gap=2.8 * self.k)
            self.fold([(x + f * w * 0.3, y - h * 0.5), (x + f * w * 0.32, y - h * 0.36)], 2.2 * self.k, clip=A)
            return A
        return dict(back=B, seat=S, base=base, arm=arm)

    def sofa(self, x0, x1, y, h, colour='grey_light', legs='ink', arm_colour=None):
        """a low sofa from the front: floor at y, height h"""
        w = x1 - x0
        for xx in (x0 + w * 0.06, x1 - w * 0.06):
            self.line([(xx, y - h * 0.12), (xx, y)], 3.2 * self.k, legs, taper=(0, 0.1), wobble=0.3)
        B = self.shape(self.rrect(x0 + w * 0.05, y - h, x1 - w * 0.05, y - h * 0.4, h * 0.14), colour, wobble=1.0)
        S = self.shape(self.rrect(x0 + w * 0.04, y - h * 0.5, x1 - w * 0.04, y - h * 0.12, h * 0.08), colour, wobble=1.0,
                       gap=2.4 * self.k)
        ac = arm_colour or colour
        A1 = self.shape(self.rrect(x0, y - h * 0.72, x0 + w * 0.09, y - h * 0.12, h * 0.1), ac, wobble=1.0, gap=2.4 * self.k)
        A2 = self.shape(self.rrect(x1 - w * 0.09, y - h * 0.72, x1, y - h * 0.12, h * 0.1), ac, wobble=1.0, gap=2.4 * self.k)
        return dict(back=B, seat=S, arms=(A1, A2))

    def stool(self, x, y, w, h, colour='wood', legs='ink'):
        """a small side stool: top at (x, y - h) ... floor at y"""
        for dx in (-0.36, 0.36):
            self.line([(x + dx * w, y - h), (x + dx * w * 1.15, y)], 3.0 * self.k, legs, taper=(0, 0.1), wobble=0.3)
        return self.shape(self.rrect(x - w / 2, y - h - w * 0.08, x + w / 2, y - h + w * 0.02, 3 * self.k), colour, wobble=0.6)

    def table(self, x0, x1, y, h, colour='wood_light', legs='ink'):
        for xx in (x0 + (x1 - x0) * 0.08, x1 - (x1 - x0) * 0.08):
            self.line([(xx, y - h), (xx, y)], 3.2 * self.k, legs, taper=(0, 0.1), wobble=0.3)
        return self.shape(self.rrect(x0, y - h - 6 * self.k, x1, y - h + 6 * self.k, 3 * self.k), colour, wobble=0.6)

    def stove(self, x0, x1, y, h, colour='grey_light', knobs='ink', top='wood_light'):
        """a kitchen counter / stove block: worktop at y - h, floor at y; a door seam and a row of small knobs"""
        P = self.shape(self.rrect(x0, y - h, x1, y, 4 * self.k), colour, wobble=0.8)
        self.shape(self.rrect(x0 - 6 * self.k, y - h - 7 * self.k, x1 + 6 * self.k, y - h + 9 * self.k, 3 * self.k), top,
                   wobble=0.6)
        w = x1 - x0
        self.fold([(x0 + w * 0.5, y - h * 0.8), (x0 + w * 0.5, y - h * 0.06)], 2.2 * self.k, clip=P)
        self.fold([(x0 + w * 0.08, y - h * 0.8), (x1 - w * 0.08, y - h * 0.8)], 2.2 * self.k, clip=P)
        for i in range(3):
            self.dot(x0 + w * (0.25 + 0.25 * i), y - h * 0.9, max(2.5, h * 0.025), knobs)
        for xx in (x0 + w * 0.42, x0 + w * 0.58):
            self.line([(xx, y - h * 0.52), (xx, y - h * 0.38)], 2.6 * self.k, knobs, taper=0.1, wobble=0.1)
        return P

    def plant(self, x, y, h, pot='red', leaf='green', leaves=7, seed=None):
        """a potted plant on (x, y): a small pot and long flat leaves"""
        r = self._r(seed)
        w = h * 0.42
        for i in range(leaves):
            a = np.deg2rad(-90 + (i - (leaves - 1) / 2) * (110 / max(leaves - 1, 1)) + r.normal(0, 6))
            L = h * (0.75 + 0.35 * r.random())
            base = np.array([x + (i - (leaves - 1) / 2) * w * 0.06, y - w * 0.7])
            tip = base + np.array([np.cos(a), np.sin(a)]) * L
            mid = (base + tip) / 2 + np.array([-np.sin(a), np.cos(a)]) * L * 0.12 * (1 if i % 2 else -1)
            pts = self.tube([base, mid, tip], [w * 0.2, w * 0.26, w * 0.02], ('round', 'round'))
            P = self.shape(pts, leaf if i % 3 else mix(leaf, 'ink', 0.18), wobble=0.6)
            self.fold([base + (tip - base) * 0.15, mid, base + (tip - base) * 0.85], 1.6 * self.k, clip=P)
        return self.shape([(x - w / 2, y - w * 0.8), (x + w / 2, y - w * 0.8), (x + w * 0.38, y), (x - w * 0.38, y)], pot,
                          wobble=0.7)

    def book(self, x, y, w, angle=0.0, colour='blue', pages='paper', open_=True, line='ink'):
        """a book held open (x, y centre, width w across both pages) or closed"""
        a = np.deg2rad(angle)
        ca, sa = np.cos(a), np.sin(a)

        def X(pts):
            p = np.asarray(pts, np.float64) * w
            return np.stack([x + p[:, 0] * ca - p[:, 1] * sa, y + p[:, 0] * sa + p[:, 1] * ca], 1)

        if open_ == 'tent':
            # lying open, face down: the back cover is a low solid tent, the page edges a pale strip at its foot
            C = self.shape(X(closed_spline([(-0.52, 0.02), (-0.2, -0.24), (0.0, -0.36), (0.2, -0.24), (0.52, 0.02)], 5)),
                           colour, wobble=0.6)
            self.shape(X([(-0.46, -0.02), (0.46, -0.02), (0.44, 0.06), (-0.44, 0.06)]), pages, wobble=0.4)
            self.cut(X([(0.0, -0.34), (0.03, -0.14), (0.04, 0.0)]), 2.2 * self.k, taper=0.3, clip=C)
            return C
        if open_:
            C = self.shape(X([(-0.52, -0.3), (0.0, -0.26), (0.52, -0.3), (0.53, 0.32), (0.0, 0.36), (-0.53, 0.32)]), colour,
                           wobble=0.6)
            Pg = self.shape(X([(-0.47, -0.36), (-0.2, -0.38), (0.0, -0.3), (0.2, -0.38), (0.47, -0.36), (0.48, 0.26),
                               (0.2, 0.24), (0.0, 0.3), (-0.2, 0.24), (-0.48, 0.26)]), pages, smooth=False, wobble=0.5)
            self.line(X([(0.0, -0.3), (0.0, 0.3)]), 1.8 * self.k, line, taper=0.2, wobble=0.1)
            for yy in (-0.18, -0.06, 0.06):
                for s_ in (-1, 1):
                    self.line(X([(s_ * 0.1, yy), (s_ * 0.38, yy - 0.01)]), 1.4 * self.k, 'grey', taper=0.2, wobble=0.1)
            return self.union(C, Pg)
        C = self.shape(X(self.rrect(-0.5, -0.36, 0.5, 0.36, 0.03)), colour, wobble=0.6)
        self.fold(X([(-0.38, -0.36), (-0.38, 0.36)]), 2.0 * self.k, clip=C, smooth=False)
        return C

    def cat_sit(self, x, y, h, facing=1, colour='black', head_down=0.0, eye='dot', tail=True, seed=None):
        """a sitting cat on (x, y) (between its front paws), height h; head_down 0..1 lowers the head (eating)"""
        f = facing
        u = h

        def X(pts):
            p = np.asarray(pts, np.float64) * u
            return np.stack([x + p[:, 0] * f, y + p[:, 1]], 1)

        if tail:
            self.limb(X([(-0.42, -0.06), (-0.75, -0.02), (-0.86, -0.18)]), [0.1 * u, 0.09 * u, 0.07 * u], colour,
                      cap='round')
        body = [(0.12, -0.62 + 0.2 * head_down), (0.22, -0.3), (0.22, -0.02), (-0.1, 0.0), (-0.48, -0.02), (-0.56, -0.24),
                (-0.38, -0.5), (-0.1, -0.64 + 0.15 * head_down)]
        B = self.shape(X(closed_spline(body, 6)), colour, wobble=1.0)
        hx, hy = 0.2 + 0.18 * head_down, -0.72 + 0.5 * head_down
        Hd = self.shape(X(closed_spline([(hx - 0.2, hy - 0.04), (hx - 0.16, hy - 0.2), (hx - 0.08, hy - 0.34),
                                         (hx, hy - 0.2), (hx + 0.1, hy - 0.22), (hx + 0.16, hy - 0.36), (hx + 0.22, hy - 0.16),
                                         (hx + 0.24, hy + 0.04), (hx + 0.06, hy + 0.14), (hx - 0.14, hy + 0.12)], 5)),
                        colour, wobble=0.8)
        self.fold(X([(0.02, -0.12), (0.06, -0.01)]), 1.8 * self.k, clip=B)
        self.fold(X([(-0.26, -0.36), (-0.36, -0.2), (-0.32, -0.06)]), 1.8 * self.k, clip=B)
        if eye == 'dot':
            self.dot(*X([(hx + 0.12, hy - 0.02)])[0], 0.025 * u, 'paper')
        elif eye == 'closed':
            self.cut(X([(hx + 0.06, hy - 0.0), (hx + 0.11, hy + 0.025), (hx + 0.16, hy + 0.0)]), 1.8 * self.k, taper=0.3)
        return self.union(B, Hd)

    def cat_curl(self, x, y, w, colour='black', facing=1):
        """a cat curled up asleep, (x, y) the bottom centre, width w"""
        f = facing

        def X(pts):
            p = np.asarray(pts, np.float64) * w
            return np.stack([x + p[:, 0] * f, y + p[:, 1]], 1)

        B = self.shape(X(closed_spline([(-0.5, -0.02), (-0.46, -0.24), (-0.18, -0.4), (0.18, -0.38), (0.44, -0.22),
                                        (0.5, 0.0)], 6)), colour, wobble=1.0)
        Hd = self.shape(X(closed_spline([(0.12, -0.02), (0.14, -0.22), (0.22, -0.36), (0.3, -0.24), (0.42, -0.26),
                                         (0.48, -0.36), (0.52, -0.16), (0.5, 0.0)], 5)), colour, wobble=0.7, gap=2.0 * self.k)
        self.cut(X([(0.33, -0.12), (0.37, -0.1), (0.41, -0.12)]), 1.6 * self.k, taper=0.3)
        self.cut(X([(-0.42, -0.06), (-0.2, -0.12), (0.06, -0.08)]), 1.8 * self.k, taper=0.3, clip=B)
        return self.union(B, Hd)

    def window(self, x0, y0, x1, y1, frame='ink', rain=True, seed=None):
        """a window frame drawn in thin lines, a few rain streaks behind the glass"""
        lw = 2.4 * self.k
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], lw, frame, taper=0.0, wobble=0.4, smooth=False)
        self.line([((x0 + x1) / 2, y0), ((x0 + x1) / 2, y1)], lw, frame, taper=0.0, wobble=0.3, smooth=False)
        self.line([(x0, (y0 + y1) / 2), (x1, (y0 + y1) / 2)], lw, frame, taper=0.0, wobble=0.3, smooth=False)
        if rain:
            self.rain(x0 + 10 * self.k, y0 + 10 * self.k, x1 - 10 * self.k, y1 - 10 * self.k, n=14, colour='powder',
                      slant=0.0, seed=seed)

    def bicycle(self, x, y, size, facing=1, frame='red', wheels='ink', basket=True, saddle='ink'):
        """a city bicycle on the ground at (x, y) (between the wheels), wheelbase `size`"""
        f = facing
        R = size * 0.36
        rw = (x - f * size / 2, y - R); fw = (x + f * size / 2, y - R)
        for cx, cy in (rw, fw):
            self.line(self.ellipse(cx, cy, R, R, n=80), 3.4 * self.k, wheels, taper=0.0, wobble=0.4, closed=True)
            for a in np.linspace(0, 2 * np.pi, 9)[:-1] + 0.3:
                self.line([(cx + np.cos(a) * R * 0.45, cy + np.sin(a) * R * 0.45), (cx + np.cos(a) * R * 0.7, cy + np.sin(a) * R * 0.7)],
                          1.8 * self.k, wheels, taper=0.2, wobble=0.1, smooth=False)
            self.dot(cx, cy, 3.5 * self.k, frame)
        crank = (x - f * size * 0.05, y - R * 0.95)
        seat = (x - f * size * 0.18, y - R * 2.25)
        head = (x + f * size * 0.32, y - R * 2.2)
        fw_ = np.array(fw)
        w = 4.2 * self.k
        for a_, b_ in ((rw, crank), (crank, seat), (rw, seat), (crank, head), (seat, head), (head, fw_)):
            self.line([a_, b_], w, frame, taper=0.0, wobble=0.3, smooth=False)
        self.line([seat, (seat[0] - f * size * 0.02, seat[1] - R * 0.25)], w, frame, taper=0.0, smooth=False)
        self.shape(self.rrect(seat[0] - f * size * 0.1 - size * 0.02, seat[1] - R * 0.34, seat[0] + f * size * 0.06 + size * 0.02,
                              seat[1] - R * 0.22, R * 0.06), saddle, wobble=0.5)
        hb = (head[0] - f * size * 0.04, head[1] - R * 0.3)
        self.line([head, hb, (hb[0] - f * size * 0.12, hb[1] - R * 0.04)], w * 0.9, wheels, taper=0.0, wobble=0.3)
        self.dot(crank[0], crank[1], 6 * self.k, wheels)
        if basket:
            bx = fw[0] + f * size * 0.02
            pts = [(bx - size * 0.13, head[1] - R * 0.05), (bx + size * 0.13, head[1] - R * 0.05),
                   (bx + size * 0.11, head[1] + R * 0.5), (bx - size * 0.11, head[1] + R * 0.5)]
            self.line(pts + [pts[0]], 2.0 * self.k, 'grey_mid', taper=0.0, wobble=0.3, smooth=False)
            for t in (0.33, 0.66):
                self.line([(pts[0][0] + (pts[1][0] - pts[0][0]) * t, pts[0][1]), (pts[3][0] + (pts[2][0] - pts[3][0]) * t, pts[3][1])],
                          1.6 * self.k, 'grey_mid', taper=0.0, smooth=False)
            self.line([(pts[0][0], (pts[0][1] + pts[3][1]) / 2), (pts[1][0], (pts[1][1] + pts[2][1]) / 2)], 1.6 * self.k,
                      'grey_mid', taper=0.0, smooth=False)
        return dict(rear=rw, front=fw, seat=seat, bars=(hb[0] - f * size * 0.12, hb[1] - R * 0.04), crank=crank)

    # ------------------------------------------------------------------ marks
    def steam(self, x, y, h, n=2, colour='red_line', width=None, seed=None):
        """steam: n thin S-squiggles rising from (x, y)"""
        r = self._r(seed)
        width = 2.6 * self.k if width is None else width
        for i in range(n):
            x0 = x + (i - (n - 1) / 2) * h * 0.32 + r.normal(0, h * 0.03)
            t = np.linspace(0, 1, 18)
            ph = r.random() * np.pi
            xs = x0 + np.sin(t * 2.6 * np.pi + ph) * h * 0.1 * (0.6 + t)
            ys = y - t * h * (0.85 + 0.25 * r.random())
            self.line(np.stack([xs, ys], 1), width, colour, taper=(0.2, 0.35), tip=0.3, wobble=0.2)

    def bang(self, x, y, r, angle=-90.0, colour='red_line', n=3, width=None):
        """three short dashes fanning out from a point (surprise, a sound): drawn around (x, y) at radius r"""
        width = 2.8 * self.k if width is None else width
        for i in range(n):
            a = np.deg2rad(angle + (i - (n - 1) / 2) * 32)
            p0 = (x + np.cos(a) * r, y + np.sin(a) * r)
            L = r * (0.75 if i != (n - 1) // 2 else 0.95)
            p1 = (x + np.cos(a) * (r + L), y + np.sin(a) * (r + L))
            self.line([p0, p1], width, colour, taper=(0.1, 0.3), wobble=0.1, smooth=False)

    def zzz(self, x, y, size, colour='navy', n=2, width=None):
        """small z's rising up and to the right from (x, y)"""
        width = 2.6 * self.k if width is None else width
        for i in range(n):
            sz = size * (1 - 0.3 * i)
            zx, zy = x + i * size * 1.25, y - i * size * 1.05
            self.line([(zx, zy), (zx + sz, zy + sz * 0.04), (zx + sz * 0.08, zy + sz), (zx + sz * 1.02, zy + sz * 0.96)],
                      width, colour, taper=0.05, wobble=0.15, smooth=False)

    def rain(self, x0, y0, x1, y1, n=20, colour='powder', slant=0.25, length=None, width=None, seed=None, avoid=None):
        """short slanted rain dashes scattered in a box"""
        r = self._r(seed)
        length = 26 * self.k if length is None else length
        width = 2.4 * self.k if width is None else width
        for _ in range(n):
            px, py = r.uniform(x0, x1), r.uniform(y0, y1)
            L = length * r.uniform(0.6, 1.3)
            self.line([(px, py), (px - slant * L, py + L)], width, colour, taper=0.3, wobble=0.1, smooth=False, avoid=avoid)

    def ticks(self, x, y, r, angle=180.0, n=3, colour='red_line', spread=26.0, width=None):
        """motion ticks: short parallel dashes behind something moving (angle = direction they point)"""
        width = 2.6 * self.k if width is None else width
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), np.sin(a)]); nrm = np.array([-d[1], d[0]])
        for i in range(n):
            o = (i - (n - 1) / 2) * spread * self.k
            p0 = np.array([x, y]) + nrm * o + d * abs(o) * 0.3
            self.line([p0, p0 + d * r * (0.8 if i != (n - 1) // 2 else 1.0)], width, colour, taper=0.2, wobble=0.1, smooth=False)

    def shadow(self, cx, cy, rx, ry=None, colour='grey_light'):
        """a sliver of shadow under something"""
        ry = rx * 0.08 if ry is None else ry
        return self.shape(self.ellipse(cx, cy, rx, ry), colour, wobble=0.8)

    # ------------------------------------------------------------------ output
    def render(self):
        C = self.C
        f = self.fin
        if not f: return np.clip(C, 0, 1)
        out = C.copy()
        ink = np.clip(np.abs(C - self.paper_rgb).max(-1) / 0.06, 0, 1)
        g = f['grain']
        if g:
            # a print's grain: a soft mottle and a fine tooth in the ink, the faintest tooth on the bare paper
            k = (0.028 * (self.mid - 0.5) + 0.05 * (self.fine - 0.5)) * g
            out *= (1 + k * ink + 0.012 * g * (self.fine - 0.5) * (1 - ink))[..., None]
        sp = f['speckle']
        if sp:
            s = smoothstep(0.78, 0.95, self.fine) * smoothstep(0.35, 0.75, self.mid) * 0.16 * sp * ink
            out += (self.paper_rgb - out) * s[..., None]
        if f['soft']:
            for c in range(3): out[..., c] = out[..., c] * (1 - f['soft']) + blur(out[..., c], 0.55) * f['soft']
        return np.clip(out, 0, 1)

    def composite(self):
        out = self.render() * 255 + 0.5
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

    def save(self, path, stages_dir=None, quality=92):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages and self.stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, b) in enumerate(self.stages):
                with open(f'{sd}/{i:02d}_{name}.png', 'wb') as fh: fh.write(b)
