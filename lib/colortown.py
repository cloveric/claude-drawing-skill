"""colortown — 彩色小镇 / Colour Town: a dense, cheerful European hill town in gouache and fine ink (numpy + Pillow only).

The look: a storybook street of tall, narrow, brightly painted townhouses piled up a hillside -- tomato red, mustard,
teal, mint, coral, cream -- under blue-grey slate mansard roofs with dormers, chimney pots, TV aerials and weather
vanes; a white clock tower above them against a pale sky with creamy clouds; strings of triangular bunting
criss-crossing the street at several depths; climbing red roses, window boxes, iron balconies, stone steps with
railings, lamps, hanging signs, shopfronts and painted doors; and a wet street in front that mirrors all of it.
Painted the way an illustrator paints it in gouache: flat opaque colour with a little brush texture, then a fine,
slightly shaky dark-brown ink line around almost everything. Soft light, almost no cast shadows, and more small
things than the eye can finish looking at.

Physical model
  paper       A warm white sheet with a fine tooth (`paper()`); it shows only where nothing is painted and, very
              faintly, through everything as a grain at the end.
  gouache     Gouache is opaque and dries matte: a coat replaces what is under it. A fill is a polygon; thousands of
              them are rasterised in one go: Pillow fills each polygon with its own integer id into a 2x
              supersampled id map (painter's order = id order, later fills cover earlier ones), numpy looks every
              id up in a table (colour, alpha, texture weights) and box-averages back to 1x, so every edge is
              anti-aliased and a fill costs a few microseconds. A coat is never perfectly even: three texture fields
              precomputed for the whole canvas -- vertical brush streaks, horizontal brush streaks and an isotropic
              scumble -- plus a low-frequency mottle modulate its value by a few percent, each fill choosing how much
              of which (walls: vertical streaks; sky, bands and street: horizontal; roofs and foliage: scumble).
              Polygon edges are resampled every few px and pushed sideways by a smooth random wobble, so long edges
              are hand-straight, not ruler-straight, and the colour never registers exactly with its ink line.
  ink         A fineliner / dip-pen line in dark warm brown, drawn after the colour of the same group (`flush()`):
              each line is its own id in a 3x id map (Pillow lines with round joints), so crossings do not bead;
              long lines are split into pieces of slightly different width, every line is resampled and wobbled by
              a low-frequency hand tremor, and the corners of boxes are separate strokes that sometimes overshoot.
              Ink is half transparent: on cream it reads dark brown, on red a deep red-brown, on glass nearly black.
  depth       `far` (0 near .. 1 very far, a context or an argument) pulls colours toward the pale blue haze of the
              sky and makes lines thinner and lighter; scale does the rest (near houses have big windows, the far
              ones tiny), with overlap from painting back to front.
  planes      Everything is drawn in canvas px. `plane(src, dst)` sets a homography that maps a rectangle onto a
              quad, so a whole facade can be laid out flat and then receded in one-point perspective (a canyon wall
              down the side of the street); line widths follow the local scale.
  houses      `house()` builds a whole townhouse from a few numbers: wall (plaster with bare-stone patches, painted
              boards, string courses, a cornice), ground floor (door, shopfront with fascia lettering and awning, or
              an archway), a grid of windows that are each a little different (cream frames, dark teal glass with a
              light reflection, glazing bars, sills, shutters with slats, curtains, round and arched variants), window
              boxes overflowing with flowers, iron balconies with pots, then the roof: slate laid tile by tile in
              staggered courses (each slate its own blue-grey, clipped to the roof, joints inked), mansard / hip /
              gable / side-gable shapes, dormers, chimneys with pots, aerials. The returned dict gives the windows,
              the roof line and anchor points for bunting and roses.
  plants      Climbing roses: a wandering stem up a wall, pairs of small dark leaves along it, red (or pink) roses as
              discs with a darker spiral of petals and a light lip, buds, clustered toward the top. Trees: a trunk
              and branches in ink, a crown of clumps, each a dark base and many small leaf dabs coloured by a dome
              light (light from the upper left). Window boxes and pots: leaves first, then flower dabs.
  bunting     A string sagging between two points (a parabola), pennants hanging from it at even spacing, each a
              triangle following the string's slope with a darker fold on one half, colours from a cheerful cycle,
              inked; strings are painted at several depths (small far ones between far houses, big near ones last).
  street      Paving in perspective (rows of rounded stones whose joints run toward the vanishing point), then the
              wet look: the picture above the street is mirrored about each column's base line, pushed sideways by
              ripples, smeared vertically (more the further from the base), darkened and mixed into the stone colour
              with vertical brush streaks; joints and light glints go on top.
  shading     Almost none, as in the look: a wall gets a thin multiply glaze that deepens toward its foot and a soft
              band of shade under its cornice (`glaze()`); light colours carry less brush texture than strong ones,
              so a white wall stays clean instead of looking grubby.
  finish      `finish()` records a slight softening, the paper grain and a gentle warm light (applied in render, so
              every stage snapshot matches the final look).

API (canvas px; colours are names in PAINTS or '#rrggbb'; `lw` is the ink line width in px, `t.lw` the default)
  surface    ColorTown(W, H, seed, keep_stages, stages_dir); paper(tone); finish(soft, grain, warmth, vignette)
  low level  fill(pts, colour, tex, dir, mot, hand, alpha, vary) -- dir 0 / 1 / 2 or a weight triple (PLASTER);
             ink(pts, width, closed, alpha, colour, hand, corners, over); box(x0, y0, x1, y1, colour); flush(clip);
             depth(far) and plane(src, dst) contexts; dab(x, y, r, colour); leaf(x, y, length, width, angle, colour);
             glaze(P, colour, top, bottom); mask(P, soft); paint_mask(mask, colour, alpha, tex, dir, sl); text(cx, cy, s, size)
  shapes     rect(), arch(), ellipse_pts(), leaf_pts() (module functions returning point arrays)
  sky        sky(top, mid, bottom, y1); clouds([(cx, cy, w, h)]); birds(region, n)
  buildings  house(x, base, w, h, wall, roof, roof_h, roof_col, floors, cols, frame, shutters, shutter_p, curtains,
             boxes, flowers, balconies, ground ('door' | 'shop' | 'arch' | None), shop, sign, letters, awning, stones,
             boards, bands, chimneys, dormers, aerials, top_window, ...) -> info (windows, roof, ridge, chimneys);
             window(x0, y0, x1, y1, kind, frame, glass, panes, shutters, curtains, lintel); door(...); shopfront(...);
             awning(...); balcony(...); flowerbox(...); roof(kind, x0, x1, y, h, colour, dormers); dormer(...);
             slates(P, tile, ramp); chimney(...); aerial(...); vane(...); patches(...);
             clock_tower(cx, base, w, h, dome, time, flag); stairs(bottom, top, n); parapet(top, bottom); railing(path, h)
  street     street(y0, vp, poly); reflect(src, base, y0, strength, smear, ripple, region); joints(alpha);
             mirror(base, x0, x1, top, strength) context (reflect what is painted inside it); glints(y0, y1, n)
  plants     roses(path, n, colour, dark, light, size); tree(x, base, h, rad, clumps, leaf); pot(x, base, w, h, plant)
  props      bunting(p0, p1, sag, size, colours); lamp(x, base, h, wall); sign(wall_x, y, r, colour, icon, side);
             person(x, base, h, coat, umbrella, balloon, basket, facing); cat(x, base, s); bistro(x, base, s);
             poster(x0, y0, x1, y1, colour)
  output     render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 88, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from colortown import ColorTown
    t = ColorTown(1500, 2000, seed=3); t.finish(); t.paper()
    t.sky(); t.clouds([(1000, 260, 420, 160)])
    t.house(200, 1500, 300, 700, 'tomato', roof='mansard', floors=4, cols=3)
    t.bunting((0, 600), (1500, 700), sag=80, size=40)
    t.save('town.jpg')
"""
import io
import os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font

PAINTS = {
    # paper and ink
    'paper': '#f5f0e4', 'ink': '#2a1f1b', 'ink_soft': '#5a4a40', 'iron': '#25252b',
    # sky
    'sky_top': '#8ec6d6', 'sky': '#a6d3dd', 'sky_low': '#d3e9e5', 'haze': '#cfe2e0',
    'cloud': '#fcf8ee', 'cloud_shade': '#e9e1d4', 'cloud_warm': '#f8e8d6',
    # walls -- saturated but soft gouache
    'tomato': '#d9493a', 'red': '#c93a30', 'brick': '#b9563d', 'coral': '#e9806a', 'salmon': '#ef9f87',
    'pink': '#eda7a0', 'rose_wall': '#e48d8c', 'mustard': '#e2b03f', 'ochre': '#d99b43', 'yellow': '#efc65a',
    'butter': '#f3d98e', 'orange': '#e9813d', 'apricot': '#f0a35e', 'teal': '#3f998e', 'teal_deep': '#2e7a74',
    'jade': '#58ae9f', 'mint': '#9cd2bd', 'aqua': '#7fc5c3', 'turquoise': '#4bb0ad', 'blue': '#4d7fb3',
    'cobalt': '#3d679f', 'powder': '#a8c7dc', 'cerulean': '#5aa2c8', 'green': '#5e9a5c', 'sage': '#a6c193',
    'cream': '#f5ead2', 'ivory': '#faf3e3', 'blush': '#f3c9bd', 'pale_yellow': '#f5e2a8', 'pale_mint': '#cfe7d8', 'white': '#fbf8f0', 'stone': '#d9cfbe', 'stone_mid': '#c2b5a2',
    'stone_dark': '#a39482', 'warmgrey': '#bdb1a2', 'lavender': '#b9a8cf',
    # roofs
    'slate': '#3f536b', 'slate_dark': '#2c3a4d', 'slate_light': '#60788f', 'slate_blue': '#4b6585',
    'tile': '#c4613e', 'tile_dark': '#9d4a33', 'verdigris': '#5c9c8a', 'copper': '#b7703f',
    # glass, wood, metal
    'glass': '#30515a', 'glass_light': '#5f8a8f', 'glass_dark': '#1f363d', 'curtain': '#f4ead8',
    'wood': '#9b6b46', 'wood_dark': '#6e4a32', 'gold': '#d9a83c',
    # plants
    'leaf_dark': '#2c5a36', 'leaf': '#4b8645', 'leaf_mid': '#679f4f', 'leaf_light': '#9cc263', 'leaf_pale': '#c8dc8a',
    'trunk': '#7a5a44', 'rose': '#d8312d', 'rose_dark': '#951d22', 'rose_light': '#f06a5c',
    'rose_pink': '#ef8fa0', 'rose_pink_dark': '#c4566e', 'blossom_white': '#fbf4ee', 'blossom_yellow': '#f3cf4f',
    'blossom_orange': '#f08c3c', 'blossom_purple': '#a77fc6', 'blossom_pink': '#f2a2b4',
    'terracotta': '#c2643f', 'pot_dark': '#93492f',
    # street
    'street': '#a7adab', 'street_far': '#c3c3ba', 'cobble': '#b8b2a6', 'cobble_dark': '#8f8d88', 'wet': '#7d8c95',
    # people
    'skin': '#efc4a0', 'hair': '#3b2a22', 'hair_light': '#a5683a',
}

BUNTING = ('#e24b3b', '#f08a3a', '#f3c84a', '#3fa597', '#4a85c1', '#7bb65a', '#ec8b9b', '#f5f0e2')
PLASTER = (0.5, 0.0, 0.7)              # walls: a little vertical brushwork in a scumbled coat
SLATE_RAMP = ('#34475e', '#3b5069', '#425873', '#4a617c', '#3f536b', '#3b5069', '#526b86')
TILE_RAMP = ('#b65438', '#c4613e', '#cf7048', '#a94a33', '#d77f55')
FLOWER_SETS = {
    'pink': ('#f2a2b4', '#e8607c', '#fbf4ee', '#f7c6d0'),
    'red': ('#d8312d', '#f06a5c', '#fbf4ee', '#f2a2b4'),
    'sunny': ('#f3cf4f', '#f08c3c', '#fbf4ee', '#e8607c'),
    'violet': ('#a77fc6', '#f2a2b4', '#fbf4ee', '#d8312d'),
    'white': ('#fbf4ee', '#f7e3c8', '#f2a2b4', '#f3cf4f'),
}


def hexc(c):
    """'#rrggbb', a PAINTS name or an rgb triple -> float32 rgb 0..1"""
    if isinstance(c, str):
        c = PAINTS.get(c, c).lstrip('#')
        return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255
    return np.asarray(c, np.float32)


def mix(a, b, t):
    return hexc(a) * (1 - t) + hexc(b) * t


def deepen(c, d=0.25):
    """a darker, slightly richer version of a colour (gouache shadow mixing, not grey)"""
    c = hexc(c)
    return np.clip(c ** (1 + 0.9 * d) * (1 - 0.35 * d), 0, 1)


def lighten(c, d=0.3, to='#fff7e6'):
    return mix(c, to, d)


def rect(x0, y0, x1, y1):
    return np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], np.float32)


def ellipse_pts(cx, cy, rx, ry=None, n=24, rot=0.0, a0=0.0, a1=2 * np.pi):
    ry = rx if ry is None else ry
    t = np.linspace(a0, a1, n, endpoint=(a1 - a0) < 2 * np.pi - 1e-6)
    x, y = np.cos(t) * rx, np.sin(t) * ry
    c, s = np.cos(rot), np.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)


def arch(x0, y0, x1, y1, rise=None, n=18):
    """rectangle with a round (or segmental, rise < half width) top; y0 is the crown of the arch"""
    w = x1 - x0
    rise = w / 2 if rise is None else min(rise, w / 2)
    cx = (x0 + x1) / 2
    if rise >= w / 2 - 1e-3:
        top = ellipse_pts(cx, y0 + rise, w / 2, rise, n, 0, np.pi, 2 * np.pi)
    else:
        R = (rise ** 2 + (w / 2) ** 2) / (2 * rise)
        a = np.arcsin((w / 2) / R)
        t = np.linspace(-np.pi / 2 - a, -np.pi / 2 + a, n)
        top = np.stack([cx + R * np.cos(t), y0 + R + R * np.sin(t)], 1)
    return np.vstack([[(x0, y1)], top, [(x1, y1)]]).astype(np.float32)


def leaf_pts(cx, cy, L, Wd, ang):
    T = np.array([(-0.5, 0), (-0.25, -0.42), (0.1, -0.5), (0.5, 0), (0.1, 0.5), (-0.25, 0.42)], np.float32)
    x, y = T[:, 0] * L, T[:, 1] * Wd
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)


def _resample_edges(P, step, closed):
    """resample a polyline keeping its vertices (so corners stay sharp)"""
    P = np.asarray(P, np.float32)
    if closed: P = np.vstack([P, P[:1]])
    out = [P[:1]]
    for a, b in zip(P[:-1], P[1:]):
        L = float(np.hypot(*(b - a)))
        n = max(1, int(np.ceil(L / step)))
        t = (np.arange(1, n + 1, dtype=np.float32) / n)[:, None]
        out.append(a + (b - a) * t)
    return np.vstack(out)


def _hand(P, closed=False, amp=0.6, wl=42.0, step=5.0, r=None):
    """push a polyline sideways by a smooth random wobble (hand-drawn, not ruler-drawn)"""
    P = np.asarray(P, np.float32)
    if amp <= 0 or len(P) < 2: return P
    r = r if r is not None else np.random.default_rng()
    Q = _resample_edges(P, step, closed)
    d = np.diff(Q, axis=0)
    s = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
    Lt = float(s[-1])
    if Lt < 1: return P
    k = max(2, int(Lt / wl) + 2)
    nz = np.interp(s, np.linspace(0, Lt, k), r.normal(0, 1, k))
    nz += 0.3 * np.interp(s, np.linspace(0, Lt, 3 * k), r.normal(0, 1, 3 * k))
    if closed: nz -= (nz[-1] - nz[0]) * s / Lt
    tx = np.gradient(Q[:, 0]); ty = np.gradient(Q[:, 1])
    tl = np.hypot(tx, ty) + 1e-6
    Q = Q + np.stack([-ty / tl, tx / tl], 1) * (nz * amp)[:, None]
    return Q[:-1] if closed else Q


def _homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y, -u])
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y, -v])
    _, _, Vt = np.linalg.svd(np.asarray(A, np.float64))
    Hm = Vt[-1].reshape(3, 3)
    return Hm / Hm[2, 2]


def _streaks(H, W, along, across, axis, seed, scales=((14, 1.2, 0.65), (48, 6.0, 0.75))):
    """anisotropic noise: brush streaks running along `axis` (0 vertical, 1 horizontal), zero mean, unit std"""
    r = np.random.default_rng(seed)
    out = np.zeros((H, W), np.float32)
    for al, ac, wgt in scales:
        n = r.random((H, W)).astype(np.float32)
        n = _box(_box(n, int(al * along), axis), int(al * along), axis)
        n = _box(n, max(0, int(ac * across)), 1 - axis)
        n = (n - n.mean()) / (n.std() + 1e-6)
        out += wgt * n
    return (out - out.mean()) / (out.std() + 1e-6)


def _box(a, r, axis):
    if r < 1: return a
    w = 2 * r + 1
    pad = [(0, 0), (0, 0)]; pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode='reflect'), axis=axis, dtype=np.float64)
    hi = np.take(c, np.arange(w, c.shape[axis]), axis=axis)
    lo = np.take(c, np.arange(0, c.shape[axis] - w), axis=axis)
    return ((hi - lo) / w).astype(np.float32)


class ColorTown:
    PAINTS = PAINTS

    def __init__(self, W=1500, H=2000, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = hexc('paper')
        # texture fields: vertical streaks, horizontal streaks, isotropic scumble, low-frequency mottle
        self.TV = _streaks(H, W, 1.0, 1.0, 0, seed + 11)
        self.TH = _streaks(H, W, 1.0, 1.0, 1, seed + 12)
        r = np.random.default_rng(seed + 13)
        s1 = blur(r.random((H, W)).astype(np.float32), 1.2); s2 = blur(r.random((H, W)).astype(np.float32), 4.0)
        s = 0.55 * (s1 - s1.mean()) / (s1.std() + 1e-6) + 0.75 * (s2 - s2.mean()) / (s2.std() + 1e-6)
        self.TS = (s / (s.std() + 1e-6)).astype(np.float32)
        m = noise2d(H, W, 110, 3, seed + 14)
        self.MOT = ((m - m.mean()) / (m.std() + 1e-6)).astype(np.float32)
        self._F, self._L = [], []
        self._far = 0.0
        self._T = None
        self.lw = 1.6
        self.ss_fill, self.ss_ink = 2, 3
        self.fin = None
        self.n_fills = self.n_lines = 0

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== paper, contexts
    def paper(self, tone='paper'):
        """the warm white sheet with a faint tooth"""
        r = self._r()
        t = blur(r.random((self.H, self.W)).astype(np.float32), 0.7)
        t = (t - t.mean()) / (t.std() + 1e-6)
        self.C[:] = hexc(tone) * (1 + 0.012 * t[..., None] + 0.01 * self.MOT[..., None])
        return self

    @contextmanager
    def depth(self, far):
        """everything inside is `far` away (0 near .. 1 very far): hazier colour, finer and lighter lines"""
        old = self._far
        self._far = float(far)
        try: yield
        finally: self._far = old

    @contextmanager
    def plane(self, src, dst):
        """draw a flat layout (src rectangle x0, y0, x1, y1) onto a quad dst [(x, y) x4: tl, tr, br, bl]"""
        x0, y0, x1, y1 = src
        old = self._T
        self._T = _homography([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], dst)
        try: yield
        finally:
            self.flush()
            self._T = old

    def _tf(self, P):
        P = np.asarray(P, np.float32)
        if self._T is None: return P
        Hm = self._T
        q = P @ Hm[:2, :2].T + Hm[:2, 2]
        w = P @ Hm[2, :2] + Hm[2, 2]
        return (q / w[:, None]).astype(np.float32)

    def _scale_at(self, p):
        """local linear scale of the current plane at point p"""
        if self._T is None: return 1.0
        p = np.asarray(p, np.float32)
        a = self._tf(np.array([p, p + (4, 0), p + (0, 4)], np.float32))
        dx, dy = (a[1] - a[0]) / 4, (a[2] - a[0]) / 4
        return float(np.sqrt(abs(dx[0] * dy[1] - dx[1] * dy[0])))

    def _haze(self, col, far=None):
        far = self._far if far is None else far
        if far <= 0: return col
        a = 0.62 * far
        lum = col.mean(-1, keepdims=True)
        col = lum + (col - lum) * (1 - 0.3 * far)
        return col * (1 - a) + hexc('haze') * a

    # ================================================================== low level: queue fills and ink
    def fill(self, pts, colour, tex=None, dir=0, mot=0.5, hand=0.55, alpha=1.0, far=None, vary=0.0, r=None):
        """queue an opaque gouache polygon. tex: texture strength (0..1.5); dir 0 vertical streaks, 1 horizontal,
        2 scumble; vary: random value jitter of the colour"""
        P = self._tf(pts)
        if hand and len(P) >= 3: P = _hand(P, True, hand, r=r if r is not None else self.rng)
        col = hexc(colour).copy()
        if vary:
            rr = r if r is not None else self.rng
            col = np.clip(col * (1 + vary * rr.normal(0, 1)) + vary * 0.35 * rr.normal(0, 1, 3), 0, 1)
        col = self._haze(col, far)
        tex = 0.6 if tex is None else tex
        lum = float(col @ np.array([0.3, 0.55, 0.15], np.float32))
        k = 1 - 0.55 * float(smoothstep(0.72, 0.95, lum))
        tex *= k; mot *= k
        if np.ndim(dir): w = tex * np.asarray(dir, np.float32)
        else: w = np.zeros(3, np.float32); w[dir] = tex
        self._F.append((P, col, float(alpha), w, float(mot)))
        return P

    def dab(self, x, y, r, colour, n=8, far=None, vary=0.0, rr=None):
        """a small round dab (flowers, berries, pots seen from above)"""
        return self.fill(ellipse_pts(x, y, r, r * 0.92, n, (rr or self.rng).uniform(0, 3)), colour, tex=0.25, dir=2,
                         hand=0, far=far, vary=vary, r=rr)

    def leaf(self, x, y, length, width, angle, colour, far=None, vary=0.0, r=None):
        return self.fill(leaf_pts(x, y, length, width, angle), colour, tex=0.3, dir=2, hand=0, far=far, vary=vary, r=r)

    def ink(self, pts, width=None, closed=False, alpha=0.9, colour='ink', hand=0.6, corners=False, over=(0.3, 1.3),
            far=None, split=70.0, r=None):
        """queue a hand-inked line. corners=True draws each edge as its own stroke (and lets some overshoot)"""
        r = r if r is not None else self.rng
        far = self._far if far is None else far
        width = self.lw if width is None else width
        P0 = np.asarray(pts, np.float32)
        if len(P0) < 2: return
        width = width * (1 - 0.35 * far)
        if self._T is not None: width *= float(np.clip(self._scale_at(P0[0]) ** 0.7, 0.45, 1.3))
        alpha = alpha * (1 - 0.45 * far)
        col = hexc(colour)
        if far: col = col * (1 - 0.45 * far) + hexc('haze') * 0.36 * far
        if corners:
            Q = np.vstack([P0, P0[:1]]) if closed else P0
            for a, b in zip(Q[:-1], Q[1:]):
                d = b - a; L = float(np.hypot(*d)) + 1e-6
                e0 = r.uniform(*over) if r.random() < 0.28 else r.uniform(-0.4, 0.3)
                e1 = r.uniform(*over) if r.random() < 0.28 else r.uniform(-0.4, 0.3)
                self._line(np.array([a - d / L * e0, b + d / L * e1]), width, alpha, col, hand, False, split, r)
            return
        self._line(P0, width, alpha, col, hand, closed, split, r)

    def _line(self, P, width, alpha, col, hand, closed, split, r):
        P = self._tf(P)
        if hand: P = _hand(P, closed, hand * min(1.0, 0.5 + width / 3), r=r)
        elif closed: P = np.vstack([P, P[:1]])
        if closed and hand: P = np.vstack([P, P[:1]])
        d = np.diff(P, axis=0)
        s = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
        Lt = float(s[-1])
        if Lt < 0.5: return
        npc = max(1, int(Lt / split))
        cuts = np.linspace(0, Lt, npc + 1)
        for i in range(npc):
            m = (s >= cuts[i] - 1e-3) & (s <= cuts[i + 1] + 1e-3)
            seg = P[m]
            if len(seg) < 2:
                seg = np.array([np.interp(cuts[i], s, P[:, 0]), np.interp(cuts[i], s, P[:, 1]),
                                np.interp(cuts[i + 1], s, P[:, 0]), np.interp(cuts[i + 1], s, P[:, 1])],
                               np.float32).reshape(2, 2)
            wv = width * (1 + 0.12 * r.normal(0, 1)) if npc > 1 else width
            av = float(np.clip(alpha * (1 + 0.08 * r.normal(0, 1)), 0, 1))
            self._L.append((seg, max(0.35, wv), av, col))

    def box(self, x0, y0, x1, y1, colour, line=True, lw=None, tex=0.5, dir=0, hand=0.5, alpha=0.9, vary=0.0, r=None):
        P = rect(x0, y0, x1, y1)
        self.fill(P, colour, tex=tex, dir=dir, hand=hand, vary=vary, r=r)
        if line: self.ink(P, lw, closed=True, corners=True, alpha=alpha, r=r)
        return P

    def flush(self, clip=None):
        """rasterise everything queued: the colour first, then its ink. clip: polygon (in the current plane)"""
        cl = None if clip is None else self._tf(clip)
        if self._F:
            self._raster_fills(self._F, cl); self.n_fills += len(self._F); self._F = []
        if self._L:
            self._raster_ink(self._L, cl); self.n_lines += len(self._L); self._L = []

    def _bbox(self, items, pad):
        lo = np.array([1e9, 1e9], np.float32); hi = -lo
        for it in items:
            lo = np.minimum(lo, it[0].min(0)); hi = np.maximum(hi, it[0].max(0))
        x0, y0 = max(0, int(np.floor(lo[0] - pad))), max(0, int(np.floor(lo[1] - pad)))
        x1, y1 = min(self.W, int(np.ceil(hi[0] + pad))), min(self.H, int(np.ceil(hi[1] + pad)))
        return x0, y0, x1, y1

    def _clipmask(self, cl, x0, y0, x1, y1, ss=2):
        if cl is None: return None
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon(((cl - (x0, y0)) * ss).ravel().tolist(), fill=255)
        im = im.resize((x1 - x0, y1 - y0), Image.BOX)
        return np.asarray(im, np.float32) / 255

    def _raster_fills(self, items, cl):
        ss = self.ss_fill
        x0, y0, x1, y1 = self._bbox(items, 2)
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        pal = np.zeros((len(items) + 1, 8), np.float32)
        off = np.array([x0, y0], np.float32)
        for i, (P, col, a, tw, mot) in enumerate(items, 1):
            if len(P) < 3: continue
            d.polygon(((P - off) * ss).ravel().tolist(), fill=i)
            pal[i, :3] = col * a; pal[i, 3] = a; pal[i, 4:7] = tw * a; pal[i, 7] = mot * a
        ids = np.asarray(im)
        clip = self._clipmask(cl, x0, y0, x1, y1)
        Cs = self.C[y0:y1, x0:x1]
        step = max(8, int(2_000_000 // max(1, w * ss * ss * 8)))
        for r0 in range(0, h, step):
            r1 = min(h, r0 + step)
            look = pal[ids[r0 * ss:r1 * ss]].reshape(r1 - r0, ss, w, ss, 8).mean((1, 3))
            A = look[..., 3]
            if not A.any(): continue
            sl = (slice(y0 + r0, y0 + r1), slice(x0, x1))
            tx = (look[..., 4] * self.TV[sl] + look[..., 5] * self.TH[sl] + look[..., 6] * self.TS[sl]) * 0.045 \
                + look[..., 7] * self.MOT[sl] * 0.03
            Pm = look[..., :3] * (1 + tx / np.maximum(A, 1e-4))[..., None]
            if clip is not None:
                c = clip[r0:r1]; A = A * c; Pm = Pm * c[..., None]
            Cs[r0:r1] = Cs[r0:r1] * (1 - A[..., None]) + Pm

    def _raster_ink(self, items, cl):
        ss = self.ss_ink
        x0, y0, x1, y1 = self._bbox(items, 4)
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        pal = np.zeros((len(items) + 1, 4), np.float32)
        off = np.array([x0, y0], np.float32)
        for i, (P, wd, a, col) in enumerate(items, 1):
            q = ((P - off) * ss).ravel().tolist()
            wpx = max(1, int(round(wd * ss)))
            d.line(q, fill=i, width=wpx, joint='curve' if wpx > 2 else None)
            if wpx > 3:              # round caps
                rr = wpx / 2
                for px, py in (q[:2], q[-2:]):
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=i)
            pal[i, :3] = col * a; pal[i, 3] = a
        ids = np.asarray(im)
        clip = self._clipmask(cl, x0, y0, x1, y1)
        Cs = self.C[y0:y1, x0:x1]
        step = max(8, int(2_000_000 // max(1, w * ss * ss * 4)))
        for r0 in range(0, h, step):
            r1 = min(h, r0 + step)
            look = pal[ids[r0 * ss:r1 * ss]].reshape(r1 - r0, ss, w, ss, 4).mean((1, 3))
            A = look[..., 3]
            if not A.any(): continue
            col = look[..., :3] / np.maximum(A, 1e-4)[..., None]
            if clip is not None: A = A * clip[r0:r1]
            base = Cs[r0:r1]
            eff = 0.6 * col + 0.4 * np.minimum(base * col * 2.2, 1)
            Cs[r0:r1] = base * (1 - A[..., None]) + eff * A[..., None]

    # ================================================================== direct (soft) painting
    def paint_mask(self, mask, colour, alpha=1.0, tex=0.6, dir=1, sl=None):
        """paint a soft float mask straight into the canvas (sky, clouds, glazes)"""
        sl = sl or (slice(None), slice(None))
        A = (mask * alpha)[..., None]
        col = colour if np.ndim(colour) == 3 else hexc(colour)
        T = (self.TV, self.TH, self.TS)[dir][sl]
        col = col * (1 + 0.045 * tex * T + 0.03 * 0.5 * self.MOT[sl])[..., None]
        self.C[sl] = self.C[sl] * (1 - A) + col * A

    def glaze(self, P, colour='#5a5470', top=0.0, bottom=0.12, y0=None, y1=None, soft=0.0):
        """a thin transparent wash over polygon P (multiply), its strength ramping from `top` at y0 to `bottom` at y1"""
        P = self._tf(P)
        x0_, y0_ = np.floor(P.min(0)).astype(int); x1_, y1_ = np.ceil(P.max(0)).astype(int)
        x0_, y0_ = max(0, x0_ - 2), max(0, y0_ - 2); x1_, y1_ = min(self.W, x1_ + 2), min(self.H, y1_ + 2)
        if x1_ <= x0_ or y1_ <= y0_: return
        m = self._mask(P, (y0_, y1_, x0_, x1_), soft=soft)
        ya = P[:, 1].min() if y0 is None else self._tf([(P[0, 0], y0)])[0, 1] if self._T is not None else y0
        yb = P[:, 1].max() if y1 is None else self._tf([(P[0, 0], y1)])[0, 1] if self._T is not None else y1
        yy = np.arange(y0_, y1_, dtype=np.float32)[:, None]
        t = np.clip((yy - ya) / max(1.0, yb - ya), 0, 1)
        a = (top + (bottom - top) * t) * m * (1 - 0.6 * self._far)
        sl = (slice(y0_, y1_), slice(x0_, x1_))
        C = self.C[sl]
        self.C[sl] = C * (1 - a[..., None]) + C * hexc(colour) * a[..., None]

    def mask(self, P, soft=0.0):
        """polygon -> anti-aliased float mask over the canvas (optionally softened by `soft` px)"""
        return self._mask(self._tf(P), soft=soft)

    def _mask(self, P, sl=None, ss=2, soft=0.0):
        """polygon -> float mask over the canvas (or the slice sl = (y0, y1, x0, x1))"""
        y0, y1, x0, x1 = sl if sl else (0, self.H, 0, self.W)
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon(((np.asarray(P, np.float32) - (x0, y0)) * ss).ravel().tolist(), fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return blur(m, soft) if soft else m

    # ================================================================== sky
    def sky(self, top='sky_top', mid='sky', bottom='sky_low', y1=None, mask=None):
        """pale blue gouache sky, a little lighter toward the horizon, laid in horizontal strokes"""
        y1 = self.H * 0.55 if y1 is None else y1
        yy = np.arange(self.H, dtype=np.float32)[:, None, None]
        t = np.clip(yy / y1, 0, 1)
        col = np.where(t < 0.5, hexc(top) * (1 - 2 * t) + hexc(mid) * 2 * t,
                       hexc(mid) * (2 - 2 * t) + hexc(bottom) * (2 * t - 1))
        col = np.broadcast_to(col, (self.H, self.W, 3)) * (1 + 0.012 * self.MOT[..., None])
        m = np.ones((self.H, self.W), np.float32) if mask is None else mask
        self.paint_mask(m, col, tex=0.35, dir=2)
        self.paint_mask(m, col, tex=0.25, dir=1, alpha=0.5)

    def clouds(self, specs, colour='cloud', shade='cloud_shade', warm=None, seed=None):
        """creamy gouache clouds: (cx, cy, w, h) each -- bumps on top, flatter bottom, a soft cooler underside"""
        r = self._r(seed)
        for cx, cy, w, h in specs:
            pad = 30
            x0, x1 = max(0, int(cx - w / 2 - pad)), min(self.W, int(cx + w / 2 + pad))
            y0, y1 = max(0, int(cy - h - pad)), min(self.H, int(cy + h * 0.5 + pad))
            if x1 <= x0 or y1 <= y0: continue
            YY, XX = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            m = np.zeros(YY.shape, np.float32)
            nb = int(r.integers(5, 9))
            xs = np.linspace(cx - w * 0.4, cx + w * 0.4, nb) + r.normal(0, w * 0.03, nb)
            for i, bx in enumerate(xs):
                edge = 1 - abs(i - (nb - 1) / 2) / ((nb - 1) / 2 + 1e-6)
                rad = h * (0.32 + 0.42 * edge) * r.uniform(0.85, 1.15)
                by = cy - rad * 0.55
                m = np.maximum(m, ((XX - bx) ** 2 + (YY - by) ** 2 < rad ** 2).astype(np.float32))
            m *= (YY < cy + h * 0.12)
            m = np.clip(blur(m, 1.6) * 1.5 - 0.25, 0, 1)
            sl = (slice(y0, y1), slice(x0, x1))
            under = smoothstep(cy - h * 0.55, cy + h * 0.1, YY)
            col = hexc(colour)[None, None] * (1 - 0.6 * under[..., None]) + hexc(shade) * 0.6 * under[..., None]
            if warm: col = col * 0.85 + hexc(warm) * 0.15
            self.paint_mask(m, col, tex=0.22, dir=2, sl=sl)

    def birds(self, region, n=5, size=(7, 12), seed=None):
        r = self._r(seed)
        x0, y0, x1, y1 = region
        for _ in range(n):
            x, y, s = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(*size)
            self.ink([(x - s, y - s * 0.25), (x - s * 0.45, y - s * 0.5), (x, y)], 1.2, hand=0.2, r=r)
            self.ink([(x, y), (x + s * 0.45, y - s * 0.55), (x + s, y - s * 0.3)], 1.2, hand=0.2, r=r)
        self.flush()

    # ================================================================== building parts
    def patches(self, x0, y0, x1, y1, wall, n=3, size=(30, 70), seed=None):
        """bare stone showing through flaking plaster: soft blobs with a few bricks outlined"""
        r = self._r(seed)
        for _ in range(n):
            w = r.uniform(*size); h = w * r.uniform(0.45, 0.8)
            cx, cy = r.uniform(x0 + w / 2, max(x0 + w / 2 + 1, x1 - w / 2)), r.uniform(y0 + h / 2, max(y0 + h / 2 + 1, y1 - h / 2))
            P = ellipse_pts(cx, cy, w / 2, h / 2, 14) + r.normal(0, w * 0.06, (14, 2))
            self.fill(P, mix(deepen(wall, 0.12), 'stone', 0.35), tex=0.9, dir=2, hand=1.0, r=r)
            bh = max(4.0, h / 3.2)
            rows = int(h / bh)
            for k in range(rows):
                yy = cy - h / 2 + (k + 0.5) * bh
                xs = cx - w / 2 + (r.uniform(0, 1) + np.arange(0, w / (bh * 2) + 1)) * bh * 2
                for xb in xs:
                    if abs(xb - cx) / (w / 2) + abs(yy - cy) / (h / 2) < 0.9 and r.random() < 0.7:
                        self.ink(rect(xb - bh * 0.9, yy - bh * 0.42, xb + bh * 0.9, yy + bh * 0.42), 0.8,
                                 closed=True, alpha=0.35, colour='ink_soft', hand=0.4, r=r)

    def window(self, x0, y0, x1, y1, kind='std', frame='cream', glass='glass', panes=None, shutters=None,
               curtains=None, sill=True, lintel=None, open_=False, lw=None, r=None):
        """a window: frame, glass with a light reflection, glazing bars, sill, optional shutters / curtains"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        ww, wh = x1 - x0, y1 - y0
        small = ww < 16
        fw = max(1.5, ww * 0.085)
        fr = hexc(frame) * (1 + 0.03 * r.normal())
        if shutters:
            sw = ww * 0.5 + fw
            for sx0, sx1 in ((x0 - fw - sw, x0 - fw), (x1 + fw, x1 + fw + sw)):
                self.fill(rect(sx0, y0 - fw, sx1, y1 + fw), shutters, tex=0.7, dir=0, vary=0.03, r=r)
                self.ink(rect(sx0, y0 - fw, sx1, y1 + fw), lw * 0.85, closed=True, corners=True, r=r)
                if not small:
                    for yy in np.arange(y0 + 2.5 * lw, y1 + fw - 2 * lw, max(4.0, 3.6 * lw)):
                        self.ink([(sx0 + lw * 1.4, yy), (sx1 - lw * 1.4, yy)], lw * 0.42, alpha=0.32, hand=0.2, r=r)
        if lintel == 'cap':
            self.fill(rect(x0 - fw * 2.2, y0 - fw * 3.2, x1 + fw * 2.2, y0 - fw * 1.4), frame, tex=0.4, r=r)
            self.ink(rect(x0 - fw * 2.2, y0 - fw * 3.2, x1 + fw * 2.2, y0 - fw * 1.4), lw * 0.8, closed=True, corners=True, r=r)
        elif lintel == 'pediment':
            P = np.array([(x0 - fw * 2.4, y0 - fw * 1.4), ((x0 + x1) / 2, y0 - fw * 1.4 - ww * 0.32), (x1 + fw * 2.4, y0 - fw * 1.4)], np.float32)
            self.fill(P, frame, tex=0.4, r=r)
            self.ink(P, lw * 0.8, closed=True, r=r)
        if kind == 'round':
            cx, cy, rr = (x0 + x1) / 2, (y0 + y1) / 2, ww / 2
            self.fill(ellipse_pts(cx, cy, rr + fw * 1.4, rr + fw * 1.4, 28), fr, tex=0.4, r=r, hand=0.3)
            self.fill(ellipse_pts(cx, cy, rr, rr, 28), glass, tex=0.3, dir=2, vary=0.05, r=r, hand=0.3)
            self.fill(ellipse_pts(cx - rr * 0.25, cy - rr * 0.25, rr * 0.45, rr * 0.3, 16, -0.7), lighten(glass, 0.28, '#e8f2ee'), tex=0.2, r=r, hand=0)
            self.ink(ellipse_pts(cx, cy, rr + fw * 1.4, rr + fw * 1.4, 28), lw, closed=True, r=r)
            self.ink(ellipse_pts(cx, cy, rr, rr, 28), lw * 0.8, closed=True, r=r)
            if not small:
                self.ink([(cx - rr, cy), (cx + rr, cy)], lw * 0.6, r=r)
                self.ink([(cx, cy - rr), (cx, cy + rr)], lw * 0.6, r=r)
            return
        outer = arch(x0 - fw, y0 - fw, x1 + fw, y1 + fw) if kind == 'arch' else rect(x0 - fw, y0 - fw, x1 + fw, y1 + fw)
        inner = arch(x0, y0, x1, y1) if kind == 'arch' else rect(x0, y0, x1, y1)
        self.fill(outer, fr, tex=0.4, r=r)
        gcol = hexc(glass) * (1 + 0.07 * r.normal()) + 0.02 * r.normal(0, 1, 3)
        if open_:
            gcol = deepen(gcol, 0.5)
        self.fill(inner, gcol, tex=0.5, dir=0, r=r, hand=0.3)
        gy0 = y0 + (ww / 2 if kind == 'arch' else 0)
        # light reflection: a pale slanted band across the upper-left of the glass
        if not open_ and r.random() < 0.85:
            t0, t1 = r.uniform(0.15, 0.35), r.uniform(0.45, 0.7)
            lc = lighten(gcol, r.uniform(0.18, 0.32), '#dfeeea')
            P = np.array([(x0 + ww * t0, gy0), (x0 + ww * t1, gy0), (x0, gy0 + wh * (t1 - 0.05) * 0.9),
                          (x0, gy0 + wh * (t0 - 0.05) * 0.9)], np.float32)
            P[:, 0] = np.clip(P[:, 0], x0, x1); P[:, 1] = np.clip(P[:, 1], gy0, y1)
            self.fill(P, lc, tex=0.3, r=r, hand=0)
        if curtains and not small:
            cw = ww * r.uniform(0.22, 0.32)
            cc = hexc(curtains)
            for side in (0, 1):
                if side == 0:
                    P = [(x0, gy0), (x0 + cw, gy0), (x0 + cw * 0.55, y0 + wh * 0.55), (x0 + cw * 0.35, y1), (x0, y1)]
                else:
                    P = [(x1, gy0), (x1 - cw, gy0), (x1 - cw * 0.55, y0 + wh * 0.55), (x1 - cw * 0.35, y1), (x1, y1)]
                self.fill(np.array(P, np.float32), cc, tex=0.6, dir=0, r=r, hand=0.3)
                self.ink(np.array(P[1:4], np.float32), lw * 0.5, alpha=0.5, r=r)
        # glazing bars
        if panes is None: panes = (2, 2) if wh > ww * 1.15 else (2, 1)
        nx, ny = panes
        bw = max(1.0, fw * 0.55)
        if not small or nx * ny <= 4:
            for i in range(1, nx):
                xx = x0 + ww * i / nx
                self.fill(rect(xx - bw / 2, gy0 if kind != 'arch' else y0, xx + bw / 2, y1), fr, tex=0.2, hand=0.2, r=r)
            for j in range(1, ny):
                yy = gy0 + (y1 - gy0) * j / ny
                self.fill(rect(x0, yy - bw / 2, x1, yy + bw / 2), fr, tex=0.2, hand=0.2, r=r)
        if sill:
            self.fill(rect(x0 - fw * 1.9, y1 + fw * 0.6, x1 + fw * 1.9, y1 + fw * 2.0), fr, tex=0.3, r=r)
            self.ink(rect(x0 - fw * 1.9, y1 + fw * 0.6, x1 + fw * 1.9, y1 + fw * 2.0), lw * 0.75, closed=True, corners=True, r=r)
        self.ink(outer, lw, closed=True, corners=kind != 'arch', r=r)
        self.ink(inner, lw * 0.7, closed=True, corners=kind != 'arch', alpha=0.8, r=r)
        if not small:
            for i in range(1, nx):
                xx = x0 + ww * i / nx
                self.ink([(xx - bw / 2, gy0), (xx - bw / 2, y1)], lw * 0.45, alpha=0.6, r=r)
                self.ink([(xx + bw / 2, gy0), (xx + bw / 2, y1)], lw * 0.45, alpha=0.6, r=r)
            for j in range(1, ny):
                yy = gy0 + (y1 - gy0) * j / ny
                self.ink([(x0, yy - bw / 2), (x1, yy - bw / 2)], lw * 0.45, alpha=0.6, r=r)
                self.ink([(x0, yy + bw / 2), (x1, yy + bw / 2)], lw * 0.45, alpha=0.6, r=r)

    def flowerbox(self, x0, x1, y, h, box='terracotta', flowers='pink', density=1.0, trail=0.6, mound=2.4, lw=None, r=None):
        """a window box (top edge at y, h tall) overflowing with a mound of leaves, flowers and trailing stems"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        w = x1 - x0
        cols = FLOWER_SETS.get(flowers, flowers) if isinstance(flowers, str) else flowers
        s = max(1.5, h * 0.32)
        mx, my, rx, ry = (x0 + x1) / 2, y + h * 0.15, w * 0.56, h * mound
        def in_mound(m):
            a = r.uniform(np.pi * 1.02, np.pi * 1.98, m); d = np.sqrt(r.random(m))
            return mx + np.cos(a) * d * rx, my + np.sin(a) * d * ry, d
        nl = int(rx * ry / (s * s) * 1.5 * density) + 4
        lx, ly, d = in_mound(nl)
        order = np.argsort(-d)
        for i in order:
            c = ('leaf_dark', 'leaf', 'leaf_mid', 'leaf_light')[min(3, int((1 - d[i]) * 2.2 + r.random() * 1.6))]
            self.leaf(lx[i], ly[i], s * r.uniform(1.6, 2.5), s * r.uniform(0.8, 1.1), r.uniform(-2.7, -0.4), c, r=r)
        P = rect(x0, y, x1, y + h)
        self.fill(P, box, tex=0.6, dir=1, vary=0.05, r=r)
        for _ in range(int(w / s * trail * 0.5)):
            tx_ = r.uniform(x0 + s, x1 - s); L = h * r.uniform(0.8, 2.6)
            for k in range(int(L / (s * 1.3)) + 1):
                self.leaf(tx_ + r.normal(0, s * 0.4), y + h * 0.7 + k * s * 1.3, s * r.uniform(1.3, 2.0), s * 0.8,
                          r.uniform(1.0, 2.1), ('leaf_dark', 'leaf', 'leaf_mid')[r.integers(0, 3)], r=r)
            if r.random() < 0.5:
                self.dab(tx_, y + h * 0.7 + L, s * 0.7, cols[0], rr=r)
        nf = int(rx * ry / (s * s) * 0.55 * density) + 2
        fx, fy, d = in_mound(nf)
        for i in np.argsort(-d):
            c = cols[min(len(cols) - 1, int(abs(r.normal(0, 1.1))))]
            rr_ = s * r.uniform(0.6, 1.0)
            self.dab(fx[i], fy[i], rr_, c, vary=0.04, rr=r)
            if rr_ > 2.2 and r.random() < 0.5:
                self.dab(fx[i] - rr_ * 0.2, fy[i] - rr_ * 0.25, rr_ * 0.35, lighten(c, 0.45), rr=r)
        self.ink(P, lw * 0.8, closed=True, corners=True, r=r)

    def balcony(self, x0, x1, y, h, slab='cream', iron='iron', pots=True, lw=None, r=None, style='bars'):
        """a small iron balcony: a stone slab at y, an iron railing of height h above it, pots behind the bars"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        ext = (x1 - x0) * 0.06
        th = max(2.5, h * 0.18)
        if pots:
            for px in np.arange(x0 + h * 0.4, x1 - h * 0.2, h * r.uniform(0.6, 0.95)):
                ph = h * r.uniform(0.3, 0.42)
                self.fill(np.array([(px - ph * 0.45, y - ph), (px + ph * 0.45, y - ph), (px + ph * 0.33, y), (px - ph * 0.33, y)], np.float32),
                          'terracotta', tex=0.4, vary=0.05, r=r, hand=0)
                for _ in range(7):
                    self.leaf(px + r.normal(0, ph * 0.4), y - ph - abs(r.normal(0, ph * 0.5)), ph * 0.6, ph * 0.3,
                              r.uniform(-2.8, -0.3), ('leaf_dark', 'leaf', 'leaf_mid')[r.integers(0, 3)], r=r)
                if r.random() < 0.6:
                    fc = FLOWER_SETS[('pink', 'red', 'sunny', 'violet')[r.integers(0, 4)]]
                    for _ in range(4):
                        self.dab(px + r.normal(0, ph * 0.35), y - ph - abs(r.normal(0, ph * 0.4)), ph * 0.16, fc[r.integers(0, 3)], rr=r)
        S = rect(x0 - ext, y, x1 + ext, y + th)
        self.fill(S, slab, tex=0.4, dir=1, r=r)
        self.ink(S, lw * 0.8, closed=True, corners=True, r=r)
        for bx in (x0 + ext, x1 - ext):
            B = np.array([(bx - th * 0.6, y + th), (bx + th * 0.6, y + th), (bx, y + th * 2.6)], np.float32)
            self.fill(B, slab, tex=0.3, r=r, hand=0)
            self.ink(B, lw * 0.6, closed=True, alpha=0.7, r=r)
        ic = iron
        self.ink([(x0, y - h), (x1, y - h)], lw * 1.25, colour=ic, r=r)
        self.ink([(x0, y - h * 0.12), (x1, y - h * 0.12)], lw * 0.8, colour=ic, r=r)
        for xx in (x0, x1):
            self.ink([(xx, y - h), (xx, y)], lw, colour=ic, r=r)
        sp = max(3.0, h * 0.16)
        for xx in np.arange(x0 + sp, x1 - sp * 0.4, sp):
            self.ink([(xx, y - h), (xx, y)], lw * 0.55, colour=ic, alpha=0.85, hand=0.2, r=r)
        if style == 'scroll' and h > 14:
            for xx in np.arange(x0 + sp * 1.5, x1 - sp, sp * 2):
                self.ink(ellipse_pts(xx, y - h * 0.55, sp * 0.45, h * 0.22, 12), lw * 0.5, closed=True, colour=ic, alpha=0.8, hand=0, r=r)

    def door(self, x0, y0, x1, y1, colour='teal', kind='arch', frame='stone', panels=True, fanlight=True, step=True,
             lw=None, r=None):
        """a painted front door in a stone surround, with panels, a fanlight, a knob and a step"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        w = x1 - x0
        fw = max(2.0, w * 0.12)
        outer = arch(x0 - fw, y0 - fw, x1 + fw, y1) if kind == 'arch' else rect(x0 - fw, y0 - fw, x1 + fw, y1)
        inner = arch(x0, y0, x1, y1) if kind == 'arch' else rect(x0, y0, x1, y1)
        self.fill(outer, frame, tex=0.6, dir=2, vary=0.03, r=r)
        self.fill(inner, colour, tex=0.8, dir=0, vary=0.04, r=r)
        top = y0 + (w / 2 if kind == 'arch' else 0)
        if fanlight:
            fh = w * 0.38 if kind != 'arch' else 0
            if kind == 'arch':
                fan = arch(x0 + w * 0.08, y0 + w * 0.08, x1 - w * 0.08, top + w * 0.08)
                self.fill(fan, 'glass', tex=0.3, r=r, hand=0.2)
                self.ink(fan, lw * 0.7, closed=True, r=r)
                for a in np.linspace(0.2, np.pi - 0.2, 4):
                    cx = (x0 + x1) / 2
                    self.ink([(cx, top + w * 0.08), (cx - np.cos(a) * w * 0.42, top + w * 0.08 - np.sin(a) * w * 0.42)], lw * 0.45, alpha=0.6, r=r)
                top = top + w * 0.12
            else:
                F = rect(x0 + w * 0.08, y0 + w * 0.08, x1 - w * 0.08, y0 + fh)
                self.fill(F, 'glass', tex=0.3, r=r, hand=0.2)
                self.ink(F, lw * 0.7, closed=True, corners=True, r=r)
                top = y0 + fh + w * 0.06
        if panels and w > 18:
            leaves = 2 if w > 34 else 1
            lw_ = w / leaves
            for k in range(leaves):
                lx0 = x0 + k * lw_
                for (a, b) in ((0.08, 0.46), (0.54, 0.9)):
                    py0 = top + (y1 - top) * a; py1 = top + (y1 - top) * b
                    self.ink(rect(lx0 + lw_ * 0.18, py0, lx0 + lw_ * 0.82, py1), lw * 0.6, closed=True, corners=True, alpha=0.65, r=r)
            if leaves == 2: self.ink([((x0 + x1) / 2, top), ((x0 + x1) / 2, y1)], lw * 0.7, r=r)
        kx = x1 - w * 0.18 if w <= 34 else (x0 + x1) / 2 + w * 0.08
        self.dab(kx, y0 + (y1 - y0) * 0.6, max(1.2, w * 0.035), 'gold', rr=r)
        self.ink(outer, lw, closed=True, corners=kind != 'arch', r=r)
        self.ink(inner, lw * 0.8, closed=True, corners=kind != 'arch', r=r)
        if step:
            S = rect(x0 - fw * 1.6, y1 - max(3, w * 0.1), x1 + fw * 1.6, y1)
            self.fill(S, 'stone_mid', tex=0.5, dir=1, r=r)
            self.ink(S, lw * 0.8, closed=True, corners=True, r=r)

    def awning(self, x0, x1, y, depth, colours=('tomato', 'cream'), stripes=None, lw=None, r=None):
        """a striped shop awning sloping out from the wall at y, with a scalloped valance"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        w = x1 - x0
        ext = depth * 0.35
        P = np.array([(x0, y), (x1, y), (x1 + ext, y + depth), (x0 - ext, y + depth)], np.float32)
        n = stripes or max(3, int(w / max(8, depth * 0.45)))
        for i in range(n):
            a, b = i / n, (i + 1) / n
            Q = np.array([(x0 + w * a, y), (x0 + w * b, y), (x0 - ext + (w + 2 * ext) * b, y + depth),
                          (x0 - ext + (w + 2 * ext) * a, y + depth)], np.float32)
            self.fill(Q, colours[i % len(colours)], tex=0.8, dir=0, r=r, hand=0.3)
        vh = depth * 0.28
        xs = np.linspace(x0 - ext, x1 + ext, n + 1)
        for i in range(n):
            V = np.vstack([[(xs[i], y + depth)], ellipse_pts((xs[i] + xs[i + 1]) / 2, y + depth, (xs[i + 1] - xs[i]) / 2, vh, 10, 0, np.pi, 0)[::-1]])
            col = deepen(colours[i % len(colours)], 0.12)
            self.fill(V, col, tex=0.5, r=r, hand=0)
            self.ink(V[1:], lw * 0.6, r=r, hand=0.2)
        self.ink(P, lw, closed=True, r=r)
        for i in range(1, n):
            self.ink([(x0 + w * i / n, y), (x0 - ext + (w + 2 * ext) * i / n, y + depth)], lw * 0.5, alpha=0.55, r=r)

    def shopfront(self, x0, y0, x1, y1, colour='teal_deep', text=None, letters='cream', door='center', goods=True,
                  awning=None, lw=None, r=None):
        """a painted wooden shopfront: fascia with lettering, pilasters, small-paned display windows, a door"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        w, h = x1 - x0, y1 - y0
        P = rect(x0, y0, x1, y1)
        self.fill(P, colour, tex=0.7, dir=0, vary=0.03, r=r)
        fh = h * 0.17
        self.fill(rect(x0 - 2, y0, x1 + 2, y0 + fh), deepen(colour, 0.15), tex=0.6, dir=1, r=r)
        self.ink(rect(x0 - 2, y0, x1 + 2, y0 + fh), lw, closed=True, corners=True, r=r)
        pw = max(3.0, w * 0.04)
        dw = w * 0.22
        dx0 = (x0 + x1) / 2 - dw / 2 if door == 'center' else (x1 - pw * 1.5 - dw if door == 'right' else x0 + pw * 1.5)
        gy0, gy1 = y0 + fh + h * 0.07, y1 - h * 0.2
        spans = [(x0 + pw * 1.6, dx0 - pw), (dx0 + dw + pw, x1 - pw * 1.6)]
        for sx0, sx1 in spans:
            if sx1 - sx0 < 8: continue
            G = rect(sx0, gy0, sx1, gy1)
            self.fill(G, 'glass', tex=0.5, vary=0.05, r=r)
            if goods:
                for k in range(int((sx1 - sx0) / 7)):
                    gx = r.uniform(sx0 + 3, sx1 - 3); gy = r.uniform(gy0 + (gy1 - gy0) * 0.45, gy1 - 3)
                    self.dab(gx, gy, r.uniform(1.5, 3.2), ('gold', 'cream', 'tomato', 'apricot', 'blossom_pink', 'mint')[r.integers(0, 6)], rr=r)
                self.fill(rect(sx0, gy1 - (gy1 - gy0) * 0.06, sx1, gy1), deepen(colour, 0.3), tex=0.3, r=r, hand=0.2)
            t0 = r.uniform(0.1, 0.3)
            self.fill(np.array([(sx0 + (sx1 - sx0) * t0, gy0), (sx0 + (sx1 - sx0) * (t0 + 0.18), gy0),
                                (sx0, gy0 + (gy1 - gy0) * 0.5), (sx0, gy0 + (gy1 - gy0) * 0.3)], np.float32),
                      lighten('glass', 0.22, '#dfeeea'), tex=0.2, hand=0, r=r)
            nx = max(1, int((sx1 - sx0) / max(14, h * 0.2)))
            for i in range(1, nx):
                xx = sx0 + (sx1 - sx0) * i / nx
                self.fill(rect(xx - 1.2, gy0, xx + 1.2, gy1), colour, tex=0.2, hand=0.2, r=r)
                self.ink([(xx, gy0), (xx, gy1)], lw * 0.5, alpha=0.6, r=r)
            yy = gy0 + (gy1 - gy0) * 0.32
            self.fill(rect(sx0, yy - 1.2, sx1, yy + 1.2), colour, tex=0.2, hand=0.2, r=r)
            self.ink(G, lw * 0.8, closed=True, corners=True, r=r)
            self.ink(rect(sx0 + 3, gy1 + h * 0.04, sx1 - 3, y1 - h * 0.04), lw * 0.55, closed=True, corners=True, alpha=0.6, r=r)
        self.door(dx0, gy0 - h * 0.02, dx0 + dw, y1, colour=deepen(colour, 0.12), kind='rect', frame=colour, panels=True,
                  fanlight=True, step=False, lw=lw, r=r)
        for px in (x0, x1 - pw):
            self.fill(rect(px, y0 + fh, px + pw, y1), lighten(colour, 0.12), tex=0.4, r=r)
            self.ink(rect(px, y0 + fh, px + pw, y1), lw * 0.7, closed=True, corners=True, r=r)
        self.ink(P, lw, closed=True, corners=True, r=r)
        if text:
            self._text_queue = getattr(self, '_text_queue', [])
            self._text_queue.append(((x0 + x1) / 2, y0 + fh / 2, text, fh * 0.62, letters))
        if awning:
            self.flush(); self._flush_text()
            self.awning(x0 + pw, x1 - pw, y0 + fh + 1, h * 0.2, awning, lw=lw, r=r)

    def _flush_text(self):
        q = getattr(self, '_text_queue', [])
        for cx, cy, s, size, col in q:
            self.text(cx, cy, s, size, col)
        self._text_queue = []

    def text(self, cx, cy, s, size, colour='cream', style='serif', anchor='mm'):
        """small painted lettering (signs); drawn at 2x and laid in opaque"""
        f = load_font(style, max(6, int(size * 2)))
        pad = int(size * 2 * len(s)) + 8
        im = Image.new('L', (pad * 2, int(size * 4) + 8), 0)
        ImageDraw.Draw(im).text((pad, im.height / 2), s, font=f, fill=255, anchor=anchor)
        bb = im.getbbox()
        if not bb: return
        im = im.resize((im.width // 2, im.height // 2), Image.BOX)
        m = np.asarray(im, np.float32) / 255
        x0 = int(round(cx - pad / 2)); y0 = int(round(cy - im.height / 2))
        if self._T is not None:
            return
        ys, xs = slice(max(0, y0), min(self.H, y0 + m.shape[0])), slice(max(0, x0), min(self.W, x0 + m.shape[1]))
        m = m[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
        self.paint_mask(m * 0.95, self._haze(hexc(colour)), tex=0.4, dir=2, sl=(ys, xs))

    def chimney(self, x, y, w, h, colour='cream', pots=2, lw=None, r=None):
        """a chimney stack standing on the roof at y (its foot), with a cap and terracotta pots"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        P = rect(x - w / 2, y - h, x + w / 2, y + h * 0.15)
        self.fill(P, colour, tex=0.7, dir=0, vary=0.04, r=r)
        cap = rect(x - w * 0.62, y - h - h * 0.12, x + w * 0.62, y - h + h * 0.03)
        self.fill(cap, deepen(colour, 0.08), tex=0.4, r=r)
        if w > 10 and r.random() < 0.6:
            for k in range(int(h / max(4, w * 0.35))):
                yy = y - h + h * 0.08 + k * max(4, w * 0.35)
                self.ink([(x - w / 2, yy), (x + w / 2, yy)], lw * 0.4, alpha=0.3, hand=0.2, r=r)
        self.ink(P, lw * 0.85, closed=True, corners=True, r=r)
        self.ink(cap, lw * 0.85, closed=True, corners=True, r=r)
        top = y - h - h * 0.12
        if pots:
            pw = w * 0.22
            xs = np.linspace(x - w * 0.3, x + w * 0.3, pots) if pots > 1 else [x]
            for px in xs:
                ph = pw * r.uniform(1.4, 2.0)
                Q = np.array([(px - pw / 2, top - ph), (px + pw / 2, top - ph), (px + pw * 0.62, top), (px - pw * 0.62, top)], np.float32)
                self.fill(Q, 'terracotta', tex=0.4, vary=0.06, r=r, hand=0)
                self.fill(rect(px - pw * 0.6, top - ph - pw * 0.3, px + pw * 0.6, top - ph), 'pot_dark', tex=0.3, r=r, hand=0)
                self.ink(Q, lw * 0.6, closed=True, alpha=0.8, r=r)
            top -= pw * 1.8
        return top

    def aerial(self, x, y, h, bars=3, lw=None, r=None):
        """a TV aerial: a mast and a few crossbars with little elements"""
        r = r or self.rng
        lw = (self.lw if lw is None else lw) * 0.7
        lean = r.normal(0, 0.03)
        self.ink([(x, y), (x + lean * h, y - h)], lw * 1.1, hand=0.15, r=r)
        for k in range(bars):
            yy = y - h * (0.55 + 0.42 * k / max(1, bars - 1)) if bars > 1 else y - h * 0.9
            xx = x + lean * (y - yy)
            half = h * r.uniform(0.18, 0.32) * (1 - 0.25 * k / max(1, bars))
            self.ink([(xx - half, yy), (xx + half, yy + r.normal(0, 0.8))], lw, hand=0.1, r=r)
            for t in np.linspace(-0.85, 0.85, 4):
                self.ink([(xx + half * t, yy - h * 0.035), (xx + half * t, yy + h * 0.035)], lw * 0.7, hand=0, r=r)
        if r.random() < 0.5:
            self.ink([(x + lean * h * 0.5, y - h * 0.5), (x + lean * h * 0.5 + h * 0.18, y - h * 0.38)], lw * 0.7, hand=0, r=r)

    def vane(self, x, y, h, flag=None, lw=None, r=None):
        """a weather vane (or a little flag) on a spire tip at (x, y)"""
        r = r or self.rng
        lw = (self.lw if lw is None else lw) * 0.8
        self.ink([(x, y), (x, y - h)], lw, hand=0.1, r=r)
        self.dab(x, y - h * 0.35, h * 0.06, 'gold', rr=r)
        if flag:
            F = np.array([(x, y - h), (x + h * 0.55, y - h * 0.9), (x + h * 0.45, y - h * 0.82), (x + h * 0.58, y - h * 0.7), (x, y - h * 0.72)], np.float32)
            self.fill(F, flag, tex=0.4, r=r, hand=0)
            self.ink(F, lw * 0.7, closed=True, r=r)
        else:
            self.ink([(x - h * 0.3, y - h * 0.8), (x + h * 0.3, y - h * 0.8)], lw, hand=0, r=r)
            self.fill(np.array([(x + h * 0.3, y - h * 0.86), (x + h * 0.42, y - h * 0.8), (x + h * 0.3, y - h * 0.74)], np.float32), 'ink', hand=0, r=r)
            self.fill(np.array([(x - h * 0.3, y - h * 0.88), (x - h * 0.22, y - h * 0.8), (x - h * 0.3, y - h * 0.72), (x - h * 0.4, y - h * 0.8)], np.float32), 'ink', hand=0, r=r)

    def slates(self, P, tile=(9, 6), ramp=SLATE_RAMP, lw=None, r=None, scallop=False):
        """lay slates tile by tile over polygon P (staggered courses), clip to P, ink the joints"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        P = np.asarray(P, np.float32)
        x0, y0 = P.min(0); x1, y1 = P.max(0)
        tw, th = tile
        ramp = [hexc(c) for c in ramp]
        rows = int(np.ceil((y1 - y0) / th)) + 1
        for j in range(rows):
            yy = y0 + j * th
            off = (j % 2) * tw * 0.5 + r.uniform(-tw * 0.1, tw * 0.1)
            xs = np.arange(x0 - tw + off, x1 + tw, tw)
            for xx in xs:
                c = ramp[r.integers(0, len(ramp))] * (1 + 0.04 * r.normal())
                if r.random() < 0.05: c = lighten(c, 0.22, '#c9d6e0')
                ww = tw * r.uniform(0.9, 1.05)
                if scallop:
                    T = np.vstack([[(xx, yy - th * 0.1), (xx + ww, yy - th * 0.1)],
                                   ellipse_pts(xx + ww / 2, yy + th * 0.55, ww / 2, th * 0.6, 8, 0, 0, np.pi)])
                else:
                    T = rect(xx, yy, xx + ww, yy + th * 1.08)
                    T[2:, 1] += r.normal(0, th * 0.06, 2)
                self.fill(T, c, tex=0.6, dir=2, hand=0, r=r)
        for j in range(1, rows):
            yy = y0 + j * th
            self.ink([(x0 - 2, yy), (x1 + 2, yy)], max(0.55, lw * 0.55), alpha=0.7, colour='#1f2a38', hand=0.35, split=1e9, r=r)
            off = (j % 2) * tw * 0.5
            for xx in np.arange(x0 - tw + off, x1 + tw, tw):
                if r.random() < 0.75:
                    self.ink([(xx, yy - th), (xx, yy)], max(0.5, lw * 0.5), alpha=0.6, colour='#1f2a38', hand=0, r=r)
        self.flush(clip=P)

    def roof(self, kind, x0, x1, y, h, colour='slate', overhang=None, tile=None, lw=None, r=None, dormers=0,
             dormer_frame='cream', wall=None):
        """a roof standing on the cornice line y between x0 and x1, h tall.
        kind: 'mansard' (steep slate face, curved sides), 'hip', 'side' (side gable, vertical ends),
        'gable' (front gable: the wall continues into a triangle and the roof shows as two slate verges),
        'pyramid', 'flat' (a parapet)."""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        w = x1 - x0
        ov = w * 0.035 if overhang is None else overhang
        ramp = TILE_RAMP if colour == 'tile' else SLATE_RAMP
        if tile is None:
            th = float(np.clip(h * 0.1, 3.5, 13.0)); tile = (th * 1.5, th)
        cx = (x0 + x1) / 2
        if kind == 'mansard':
            ins = h * 0.16
            L = spline([(x0 - ov, y), (x0 - ov + ins * 0.35, y - h * 0.55), (x0 - ov + ins, y - h)], 6)
            R = spline([(x1 + ov - ins, y - h), (x1 + ov - ins * 0.35, y - h * 0.55), (x1 + ov, y)], 6)
            P = np.vstack([L, R])
        elif kind == 'hip':
            P = np.array([(x0 - ov, y), (x0 - ov + h * 0.75, y - h), (x1 + ov - h * 0.75, y - h), (x1 + ov, y)], np.float32)
        elif kind == 'side':
            P = np.array([(x0 - ov, y), (x0 - ov * 0.5, y - h), (x1 + ov * 0.5, y - h), (x1 + ov, y)], np.float32)
        elif kind == 'pyramid':
            P = np.array([(x0 - ov, y), (cx, y - h), (x1 + ov, y)], np.float32)
        elif kind == 'gable':
            apex = (cx, y - h)
            G = np.array([(x0, y), apex, (x1, y)], np.float32)
            self.fill(G, wall or 'cream', tex=0.7, dir=0, r=r)
            self.flush()
            vw = max(4.0, w * 0.07)
            for side in (-1, 1):
                ex = x0 - ov if side < 0 else x1 + ov
                Vp = np.array([(cx, y - h - vw * 0.9), (ex, y + vw * 0.2), (ex - side * vw * 0.0, y + vw * 0.2 + vw * 0.9),
                               (cx, y - h + vw * 0.4)], np.float32)
                self.slates(Vp, (tile[0] * 0.8, tile[1] * 0.8), ramp, lw, r)
                self.ink(Vp, lw, closed=True, r=r)
            self.ink(G[[0, 1, 2]], lw * 0.8, r=r)
            self.flush()
            return np.array([(x0 - ov, y), (cx, y - h - vw), (x1 + ov, y)], np.float32)
        elif kind == 'flat':
            P = rect(x0 - ov, y - h, x1 + ov, y)
            self.fill(P, colour, tex=0.5, dir=1, r=r)
            self.ink(P, lw, closed=True, corners=True, r=r)
            self.flush()
            return P
        else:
            raise ValueError(kind)
        self.slates(P, tile, ramp, lw, r)
        # a light ridge on top of the slate, the outline, a soft shadow line under the eave
        self.ink(P, lw, closed=True, r=r)
        if kind in ('mansard', 'hip', 'side'):
            ty = P[:, 1].min()
            top = P[np.abs(P[:, 1] - ty) < 0.5]
            if len(top) >= 2:
                R_ = rect(top[:, 0].min(), ty - max(2.0, tile[1] * 0.45), top[:, 0].max(), ty + 0.5)
                self.fill(R_, 'slate_dark' if colour != 'tile' else 'tile_dark', tex=0.3, r=r)
                self.ink(R_, lw * 0.7, closed=True, corners=True, r=r)
        self.flush()
        if dormers and kind in ('mansard', 'hip', 'side'):
            n = dormers
            dw = min(w * 0.6 / n, h * 0.62)
            for k in range(n):
                dx = x0 + w * (k + 0.5) / n
                self.dormer(dx, y - h * 0.08, dw, h * 0.62, frame=dormer_frame, lw=lw, r=r, roof_col=colour)
            self.flush()
        return P

    def dormer(self, cx, y, w, h, frame='cream', lw=None, r=None, roof_col='slate', kind=None):
        """a dormer window on a roof face (foot at y): cheeks, a little pediment or slate gable, a window"""
        r = r or self.rng
        lw = self.lw if lw is None else lw
        kind = kind or ('gable', 'round', 'gable', 'flat')[r.integers(0, 4)]
        bh = h * 0.62
        body = rect(cx - w / 2, y - bh, cx + w / 2, y)
        self.fill(body, frame, tex=0.5, dir=0, r=r)
        self.ink(body, lw * 0.85, closed=True, corners=True, r=r)
        ww = w * 0.58
        self.window(cx - ww / 2, y - bh + bh * 0.16, cx + ww / 2, y - bh * 0.1, kind='std', frame=frame, sill=False,
                    panes=(2, 2), lw=lw * 0.85, r=r, curtains='curtain' if r.random() < 0.3 else None)
        if kind == 'gable':
            T = np.array([(cx - w * 0.62, y - bh + 1), (cx, y - bh - h * 0.42), (cx + w * 0.62, y - bh + 1)], np.float32)
            self.fill(T, deepen(roof_col if roof_col != 'tile' else 'tile', 0.05), tex=0.5, dir=2, r=r)
            self.ink(T, lw * 0.9, closed=True, r=r)
            Ti = np.array([(cx - w * 0.42, y - bh + 1), (cx, y - bh - h * 0.28), (cx + w * 0.42, y - bh + 1)], np.float32)
            self.fill(Ti, frame, tex=0.4, r=r, hand=0.2)
            self.ink(Ti, lw * 0.6, closed=True, alpha=0.7, r=r)
        elif kind == 'round':
            A = np.vstack([ellipse_pts(cx, y - bh + 1, w * 0.6, h * 0.36, 16, 0, np.pi, 2 * np.pi)])
            self.fill(A, roof_col if roof_col != 'tile' else 'tile', tex=0.5, dir=2, r=r)
            self.ink(A, lw * 0.9, closed=True, r=r)
        else:
            T = rect(cx - w * 0.6, y - bh - h * 0.1, cx + w * 0.6, y - bh + 1)
            self.fill(T, deepen(roof_col if roof_col != 'tile' else 'tile', 0.1), tex=0.4, r=r)
            self.ink(T, lw * 0.8, closed=True, corners=True, r=r)

    # ================================================================== a whole townhouse
    def house(self, x, base, w, h, wall='tomato', roof='mansard', roof_h=None, roof_col='slate', floors=4, cols=3,
              frame='cream', glass='glass', shutters=None, curtains=0.25, boxes=0.45, flowers=None, balconies=(),
              ground='door', door_col=None, shop=None, sign=None, awning=None, stones=0, boards=False, bands=True,
              chimneys=1, chimney_col=None, dormers=None, aerials=0.5, win_kind='std', win_w=0.5, win_h=0.56,
              arch_top=False, lw=None, far=None, seed=None, top_window=None, cornice='cream', arch_w=0.5, shutter_p=0.9,
              letters='cream'):
        """a tall narrow townhouse: wall x..x+w from `base` up h px, then its roof. Returns geometry."""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        if far is not None:
            with self.depth(far):
                return self.house(x, base, w, h, wall, roof, roof_h, roof_col, floors, cols, frame, glass, shutters,
                                  curtains, boxes, flowers, balconies, ground, door_col, shop, sign, awning, stones,
                                  boards, bands, chimneys, chimney_col, dormers, aerials, win_kind, win_w, win_h,
                                  arch_top, lw, None, seed, top_window, cornice, arch_w, shutter_p, letters)
        x0, x1, yb, yt = x, x + w, base, base - h
        info = dict(x0=x0, x1=x1, base=yb, top=yt, windows=[], wall=wall)
        gh = h / (floors + 0.2) * 1.2 if floors > 1 else h
        fh = (h - gh) / max(1, floors - 1)
        # wall
        WP = rect(x0, yt, x1, yb)
        if ground == 'arch':
            aw = w * arch_w; ah = gh * 0.92
            ax0, ax1 = x0 + (w - aw) / 2, x1 - (w - aw) / 2
            A = arch(ax0, yb - ah, ax1, yb)
            WP = np.vstack([[(x0, yb), (x0, yt), (x1, yt), (x1, yb)], A[::-1]])
        self.fill(WP, wall, tex=1.0, dir=PLASTER, mot=1.2, vary=0.02, r=r)
        self.flush()
        self.glaze(WP, top=0.0, bottom=0.1)
        gh_ = (h / (floors + 0.2) * 1.2 if floors > 1 else h)
        self.glaze(rect(x0, yt, x1, yt + min(h * 0.25, (h - gh_) / max(1, floors - 1) * 0.7)), top=0.2, bottom=0.0)
        if boards:
            for bx in np.arange(x0 + w * 0.04, x1, max(4.0, w * 0.055)):
                self.ink([(bx, yt + 2), (bx, yb - (gh if ground == 'shop' else 0))], lw * 0.45, alpha=0.4, hand=0.4, r=r)
        if stones:
            self.patches(x0 + 4, yt + fh * 0.3, x1 - 4, yb - 4, wall, n=stones, size=(w * 0.12, w * 0.3), seed=int(r.integers(1 << 30)))
        # string courses at each floor
        if bands:
            for k in range(1, floors):
                yy = yb - gh - (k - 1) * fh
                bh = max(2.0, fh * 0.05)
                B = rect(x0, yy - bh, x1, yy + bh * 0.5)
                self.fill(B, lighten(wall, 0.18) if bands is True else bands, tex=0.4, dir=1, r=r)
                self.ink([(x0, yy - bh), (x1, yy - bh)], lw * 0.6, alpha=0.7, r=r)
                self.ink([(x0, yy + bh * 0.5), (x1, yy + bh * 0.5)], lw * 0.5, alpha=0.55, r=r)
        # cornice
        ch = max(3.0, fh * 0.12)
        Cn = rect(x0 - w * 0.025, yt - ch * 0.2, x1 + w * 0.025, yt + ch)
        self.fill(Cn, cornice, tex=0.4, dir=1, r=r)
        # windows on the upper floors
        pitch = w / cols
        ww0 = pitch * win_w
        wh0 = fh * win_h
        later = []
        for k in range(1, floors):
            fy1 = yb - gh - (k - 1) * fh
            fy0 = fy1 - fh
            for c in range(cols):
                ww = ww0 * (1 + 0.025 * r.normal()); wh = wh0 * (1 + 0.025 * r.normal())
                cx = x0 + pitch * (c + 0.5) + r.normal(0, 0.6)
                wy0 = fy0 + fh * 0.2 + r.normal(0, 0.5)
                wx0, wx1, wy1 = cx - ww / 2, cx + ww / 2, wy0 + wh
                kind = win_kind
                if arch_top and k == floors - 1: kind = 'arch'
                is_bal = (k, c) in balconies or (k, -1) in balconies
                if is_bal: wy1 = fy1 - fh * 0.04
                sh = shutters if (shutters and r.random() < shutter_p) else None
                cur = 'curtain' if r.random() < curtains else None
                self.window(wx0, wy0, wx1, wy1, kind=kind, frame=frame, glass=glass, shutters=sh, curtains=cur,
                            sill=not is_bal, open_=r.random() < 0.05, lw=lw, r=r,
                            lintel='cap' if (k == 1 and h > 300 and not sh) else None)
                info['windows'].append((wx0, wy0, wx1, wy1))
                if is_bal:
                    later.append(('bal', wx0, wx1, wy1, ww))
                elif r.random() < boxes:
                    later.append(('box', wx0, wx1, wy1, ww))
        # ground floor
        gy0 = yb - gh
        if ground == 'shop':
            self.shopfront(x0 + w * 0.04, gy0 + gh * 0.08, x1 - w * 0.04, yb, colour=shop or 'teal_deep', text=sign,
                           letters=letters, awning=None, lw=lw, r=r)
            if awning: later.append(('awning',))
        elif ground == 'door':
            dc = door_col or ('teal', 'tomato', 'cobalt', 'green', 'mustard', 'wood')[r.integers(0, 6)]
            pos = int(r.integers(0, cols))
            for c in range(cols):
                cx = x0 + pitch * (c + 0.5)
                if c == pos:
                    dw = min(pitch * 0.62, gh * 0.48)
                    self.door(cx - dw / 2, yb - gh * 0.8, cx + dw / 2, yb, colour=dc, kind='arch' if r.random() < 0.6 else 'rect', lw=lw, r=r)
                    info['door'] = (cx - dw / 2, yb - gh * 0.8, cx + dw / 2, yb)
                else:
                    ww, wh = ww0, gh * 0.48
                    self.window(cx - ww / 2, yb - gh * 0.72, cx + ww / 2, yb - gh * 0.72 + wh, kind=win_kind, frame=frame,
                                glass=glass, shutters=shutters, lw=lw, r=r)
                    info['windows'].append((cx - ww / 2, yb - gh * 0.72, cx + ww / 2, yb - gh * 0.72 + wh))
                    if r.random() < boxes: later.append(('box', cx - ww / 2, cx + ww / 2, yb - gh * 0.72 + wh, ww))
        elif ground == 'arch':
            # soffit (inner face of the archway) and voussoirs
            A = arch(ax0, yb - ah, ax1, yb)
            In = arch(ax0 + aw * 0.07, yb - ah + aw * 0.07, ax1 - aw * 0.07, yb)
            info['arch'] = (ax0, yb - ah, ax1, yb)
            n = 11
            for i in range(n):
                a0, a1 = np.pi + np.pi * i / n, np.pi + np.pi * (i + 1) / n
                rr0, rr1 = aw / 2, aw / 2 + max(6, aw * 0.1)
                cxa, cya = (ax0 + ax1) / 2, yb - ah + aw / 2
                V = np.array([(cxa + rr0 * np.cos(a0), cya + rr0 * np.sin(a0)), (cxa + rr1 * np.cos(a0), cya + rr1 * np.sin(a0)),
                              (cxa + rr1 * np.cos(a1), cya + rr1 * np.sin(a1)), (cxa + rr0 * np.cos(a1), cya + rr0 * np.sin(a1))], np.float32)
                self.fill(V, 'stone', tex=0.6, dir=2, vary=0.04, r=r, hand=0.2)
                self.ink(V, lw * 0.6, closed=True, alpha=0.7, r=r)
            self.ink(A[1:-1], lw, r=r)
            self.ink([(ax0, yb - ah + aw / 2), (ax0, yb)], lw, r=r)
            self.ink([(ax1, yb - ah + aw / 2), (ax1, yb)], lw, r=r)
        # top window in a gable
        self.ink([(x0, yt), (x0, yb)], lw, r=r)
        self.ink([(x1, yt), (x1, yb)], lw, r=r)
        if ground != 'arch': self.ink([(x0 - 1, yb), (x1 + 1, yb)], lw, r=r)
        self.ink(Cn, lw, closed=True, corners=True, r=r)
        self.flush()
        self._flush_text()
        # balconies, boxes, awning
        fl = flowers
        for it in later:
            if it[0] == 'box':
                _, a, b, y1, ww = it
                fw = max(1.5, ww * 0.085)
                self.flowerbox(a - fw * 1.6, b + fw * 1.6, y1 + fw * 2.0, max(4.0, ww * 0.2),
                               box=('terracotta', 'wood', 'teal_deep', 'cream', 'terracotta')[r.integers(0, 5)],
                               flowers=fl or ('pink', 'red', 'sunny', 'violet', 'red', 'white')[r.integers(0, 6)], lw=lw, r=r)
            elif it[0] == 'bal':
                _, a, b, y1, ww = it
                self.balcony(a - ww * 0.35, b + ww * 0.35, y1, ww * 0.62, lw=lw, r=r, style='scroll' if r.random() < 0.5 else 'bars')
            elif it[0] == 'awning':
                self.awning(x0 + w * 0.06, x1 - w * 0.06, gy0 + gh * 0.08 + gh * 0.92 * 0.17 + 1, gh * 0.18, awning, lw=lw, r=r)
        self.flush()
        # roof
        rh = roof_h if roof_h is not None else w * 0.42
        if roof:
            nd = dormers if dormers is not None else (max(1, cols - 1) if roof == 'mansard' else 0)
            if roof == 'gable':
                RP = self.roof('gable', x0 - w * 0.025, x1 + w * 0.025, yt - ch * 0.2, rh, roof_col, lw=lw, r=r, wall=wall)
                if top_window != 'none':
                    tw_ = min(w * 0.22, rh * 0.32)
                    self.window(x0 + w / 2 - tw_ / 2, yt - rh * 0.5 - tw_ / 2, x0 + w / 2 + tw_ / 2, yt - rh * 0.5 + tw_ / 2,
                                kind=top_window or 'round', frame=frame, lw=lw * 0.9, r=r, sill=False)
                    self.flush()
            else:
                RP = self.roof(roof, x0 - w * 0.025, x1 + w * 0.025, yt - ch * 0.2, rh, roof_col, lw=lw, r=r,
                               dormers=nd, dormer_frame=frame)
            info['roof'] = RP
            ytop = float(RP[:, 1].min())
        else:
            ytop = yt
            info['roof'] = rect(x0, yt, x1, yt)
        info['ridge'] = ytop
        # chimneys and aerials
        tops = []
        for k in range(chimneys):
            cxk = x0 + w * (0.18 + 0.64 * (k + r.uniform(0.0, 1.0)) / max(1, chimneys)) if chimneys > 1 else x0 + w * r.uniform(0.2, 0.8)
            cwk = max(6.0, w * r.uniform(0.08, 0.12))
            chh = max(12.0, rh * r.uniform(0.35, 0.6)) if roof else w * 0.2
            foot = ytop + (rh * 0.15 if roof in ('mansard', 'hip', 'side') else 0)
            if roof == 'gable':
                foot = yt - rh * (1 - abs(cxk - (x0 + w / 2)) / (w / 2)) * 0.9
            tp = self.chimney(cxk, foot, cwk, chh, chimney_col or ('cream', 'brick', 'stone', wall)[r.integers(0, 4)],
                              pots=int(r.integers(1, 4)), lw=lw, r=r)
            tops.append((cxk, tp))
        if r.random() < aerials and tops:
            cxk, tp = tops[int(r.integers(0, len(tops)))]
            self.aerial(cxk, tp, max(26.0, w * r.uniform(0.35, 0.6)), bars=int(r.integers(2, 4)), lw=lw, r=r)
        self.flush()
        info['chimneys'] = tops
        return info

    # ================================================================== the clock tower
    def clock_tower(self, cx, base, w, h, body='ivory', quoins='stone', dome='slate', time=(9, 5), flag='tomato',
                    lw=None, seed=None):
        """a white clock tower: a shaft with tall arched windows and quoins, a clock stage, a belfry with three
        louvred arched openings, an onion dome (dome='slate' or 'verdigris') with a lantern, a spire and a flag"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        x0, x1 = cx - w / 2, cx + w / 2
        hs = h * 0.5                 # shaft
        hc = w * 1.05                # clock stage
        y_shaft = base - hs
        y_clock = y_shaft - hc
        bw = w * 0.86
        hb = w * 0.8                 # belfry
        y_bel = y_clock - hb
        # shaft
        S = rect(x0, y_shaft, x1, base)
        self.fill(S, body, tex=0.8, dir=0, r=r)
        qh = max(6.0, w * 0.1)
        for side in (0, 1):
            for k, yy in enumerate(np.arange(y_shaft + 4, base, qh)):
                qw = w * (0.16 if k % 2 == 0 else 0.1)
                qx0 = x0 if side == 0 else x1 - qw
                Q = rect(qx0, yy, qx0 + qw, yy + qh - 1)
                self.fill(Q, quoins, tex=0.6, dir=2, vary=0.03, r=r, hand=0.2)
                self.ink(Q, lw * 0.5, closed=True, alpha=0.55, r=r)
        ww = w * 0.2
        for yy in (y_shaft + hs * 0.12, y_shaft + hs * 0.55):
            self.window(cx - ww / 2, yy, cx + ww / 2, yy + hs * 0.3, kind='arch', frame='stone', panes=(2, 3), lw=lw * 0.9, r=r, sill=True)
        self.ink(S, lw, closed=True, corners=True, r=r)
        # cornice under the clock stage
        Cn = rect(x0 - w * 0.06, y_shaft - w * 0.05, x1 + w * 0.06, y_shaft + w * 0.03)
        self.fill(Cn, 'stone', tex=0.4, dir=1, r=r)
        self.ink(Cn, lw, closed=True, corners=True, r=r)
        # clock stage
        K = rect(x0 + w * 0.02, y_clock, x1 - w * 0.02, y_shaft - w * 0.05)
        self.fill(K, body, tex=0.8, dir=0, r=r)
        self.ink(K, lw, closed=True, corners=True, r=r)
        ccy = (y_clock + y_shaft) / 2
        R = w * 0.36
        self.fill(ellipse_pts(cx, ccy, R * 1.12, R * 1.12, 40), quoins, tex=0.4, r=r, hand=0.2)
        self.fill(ellipse_pts(cx, ccy, R, R, 40), '#fbf7ec', tex=0.3, dir=2, r=r, hand=0.2)
        self.ink(ellipse_pts(cx, ccy, R * 1.12, R * 1.12, 40), lw, closed=True, r=r)
        self.ink(ellipse_pts(cx, ccy, R, R, 40), lw * 1.2, closed=True, r=r)
        self.ink(ellipse_pts(cx, ccy, R * 0.8, R * 0.8, 40), lw * 0.5, closed=True, alpha=0.6, r=r)
        for k in range(12):
            a = k / 12 * 2 * np.pi
            l0 = 0.82 if k % 3 else 0.7
            self.ink([(cx + np.sin(a) * R * l0, ccy - np.cos(a) * R * l0), (cx + np.sin(a) * R * 0.93, ccy - np.cos(a) * R * 0.93)],
                     lw * (1.1 if k % 3 == 0 else 0.7), hand=0, r=r)
        hh, mm = time
        am = mm / 60 * 2 * np.pi; ah = (hh % 12 + mm / 60) / 12 * 2 * np.pi
        for a, L, wd in ((ah, 0.5, 0.075), (am, 0.74, 0.05)):
            d = np.array([np.sin(a), -np.cos(a)]); n = np.array([-d[1], d[0]])
            P = np.array([(cx, ccy) - d * R * 0.12 + n * R * wd * 0.5, (cx, ccy) + d * R * L, (cx, ccy) - d * R * 0.12 - n * R * wd * 0.5], np.float32)
            self.fill(P, 'ink', tex=0, hand=0, r=r)
        self.dab(cx, ccy, R * 0.06, 'ink', rr=r)
        Cn2 = rect(x0 - w * 0.05, y_clock - w * 0.05, x1 + w * 0.05, y_clock + w * 0.02)
        self.fill(Cn2, 'stone', tex=0.4, dir=1, r=r)
        self.ink(Cn2, lw, closed=True, corners=True, r=r)
        # belfry
        B = rect(cx - bw / 2, y_bel, cx + bw / 2, y_clock - w * 0.05)
        self.fill(B, body, tex=0.8, dir=0, r=r)
        ow = bw * 0.2
        for ox in (cx - bw * 0.28, cx, cx + bw * 0.28):
            O = arch(ox - ow / 2, y_bel + hb * 0.16, ox + ow / 2, y_clock - w * 0.16)
            self.fill(O, '#7a5f4a', tex=0.5, r=r)
            for yy in np.arange(y_bel + hb * 0.16 + ow * 0.55, y_clock - w * 0.18, max(3.0, ow * 0.2)):
                self.fill(rect(ox - ow / 2, yy, ox + ow / 2, yy + max(1.2, ow * 0.08)), '#a8876a', tex=0.2, hand=0, r=r)
                self.ink([(ox - ow / 2, yy + max(1.2, ow * 0.08)), (ox + ow / 2, yy + max(1.2, ow * 0.08))], lw * 0.4, alpha=0.6, hand=0, r=r)
            self.ink(O, lw * 0.9, closed=True, r=r)
        self.ink(B, lw, closed=True, corners=True, r=r)
        Cn3 = rect(cx - bw / 2 - w * 0.06, y_bel - w * 0.06, cx + bw / 2 + w * 0.06, y_bel + w * 0.02)
        self.fill(Cn3, 'stone', tex=0.4, dir=1, r=r)
        self.ink(Cn3, lw, closed=True, corners=True, r=r)
        # small urns on the corners
        for ux in (cx - bw / 2 - w * 0.02, cx + bw / 2 + w * 0.02):
            U = ellipse_pts(ux, y_bel - w * 0.12, w * 0.05, w * 0.07, 12)
            self.fill(U, 'stone', tex=0.3, r=r, hand=0)
            self.ink(U, lw * 0.7, closed=True, r=r)
        self.flush()
        # onion dome
        dy0 = y_bel - w * 0.06
        dh = w * 0.95
        dwid = bw * 0.62
        t = np.linspace(0, 1, 30)
        prof = np.sin(np.pi * np.clip(t * 1.1, 0, 1)) ** 0.75 * (1 - 0.15 * t) * (1 - t) ** 0.35
        prof = prof / prof.max()
        xs_r = cx + dwid * prof; ys = dy0 - dh * t
        D = np.vstack([np.stack([xs_r, ys], 1), np.stack([2 * cx - xs_r, ys], 1)[::-1]])
        self.fill(D, dome, tex=0.6, dir=2, r=r)
        for k in np.linspace(-0.66, 0.66, 5):
            rib = np.stack([cx + k * dwid * prof, ys], 1)
            self.ink(rib, lw * 0.55, alpha=0.6, colour='slate_dark' if dome == 'slate' else deepen(dome, 0.6), r=r)
        hl = np.stack([cx - 0.45 * dwid * prof[3:22], ys[3:22]], 1)
        self.ink(hl, lw * 1.6, alpha=0.35, colour='#e8eef0', hand=0.3, r=r)
        self.ink(D, lw, closed=True, r=r)
        self.flush()
        # lantern, cap, spire
        lt = dy0 - dh * 0.92
        lwid = dwid * 0.36
        Lb = rect(cx - lwid, lt - w * 0.32, cx + lwid, lt + 2)
        self.fill(Lb, body, tex=0.5, r=r)
        for ox in (cx - lwid * 0.45, cx + lwid * 0.45):
            O = arch(ox - lwid * 0.25, lt - w * 0.27, ox + lwid * 0.25, lt - w * 0.04)
            self.fill(O, '#3a4048', tex=0.3, r=r, hand=0.2)
        self.ink(Lb, lw * 0.9, closed=True, corners=True, r=r)
        capy = lt - w * 0.32
        Cp = ellipse_pts(cx, capy, lwid * 1.25, w * 0.16, 20, 0, np.pi, 2 * np.pi)
        Cp = np.vstack([Cp, [(cx + lwid * 1.25, capy)]])
        self.fill(Cp, dome, tex=0.5, r=r)
        self.ink(Cp, lw * 0.9, closed=True, r=r)
        sp = np.array([(cx - w * 0.05, capy - w * 0.14), (cx, capy - w * 0.62), (cx + w * 0.05, capy - w * 0.14)], np.float32)
        self.fill(sp, dome, tex=0.4, r=r, hand=0)
        self.ink(sp, lw * 0.8, closed=True, r=r)
        self.dab(cx, capy - w * 0.62, w * 0.045, 'gold', rr=r)
        self.flush()
        self.vane(cx, capy - w * 0.64, w * 0.5, flag=flag, lw=lw, r=r)
        self.flush()
        return dict(top=capy - w * 0.64 - w * 0.5, clock=(cx, ccy, R), belfry=y_bel, x0=x0, x1=x1, shaft=y_shaft)

    # ================================================================== stairs, walls, railings
    def stairs(self, bottom, top, n=14, tread='stone', riser='stone_mid', lw=None, seed=None, ratio=1.06):
        """a flight of stone steps going up and away: bottom = (xl, xr, y), top = (xl, xr, y).
        Steps shrink toward the top (they are further away)."""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        (bl, br, by), (tl, tr, ty) = bottom, top
        g = np.array([ratio ** k for k in range(n)], np.float32)[::-1]   # bottom steps bigger
        g = g / g.sum() * (by - ty)
        ys = ty + np.concatenate([[0], np.cumsum(g[::-1])])            # top -> bottom boundaries
        def xs(y):
            t = (y - ty) / (by - ty + 1e-6)
            return tl + (bl - tl) * t, tr + (br - tr) * t
        for k in range(n):
            ya, yb_ = ys[k], ys[k + 1]
            yn = ya + (yb_ - ya) * 0.38
            la, ra = xs(ya); lb, rb = xs(yb_); ln, rn = xs(yn)
            T = np.array([(la, ya), (ra, ya), (rn, yn), (ln, yn)], np.float32)
            Rr = np.array([(ln, yn), (rn, yn), (rb, yb_), (lb, yb_)], np.float32)
            self.fill(T, tread, tex=0.6, dir=1, vary=0.03, r=r, hand=0.3)
            self.fill(Rr, riser, tex=0.7, dir=1, vary=0.04, r=r, hand=0.3)
            nslab = int(r.integers(2, 4))
            for j in range(1, nslab):
                t = j / nslab + r.normal(0, 0.06)
                self.ink([(ln + (rn - ln) * t, yn), (lb + (rb - lb) * t, yb_)], lw * 0.5, alpha=0.45, hand=0, r=r)
            self.ink([(ln, yn), (rn, yn)], lw * 0.85, r=r)
            self.ink([(lb, yb_), (rb, yb_)], lw * 0.55, alpha=0.6, r=r)
        self.ink([(tl, ty), (bl, by)], lw, r=r)
        self.ink([(tr, ty), (br, by)], lw, r=r)
        self.flush()
        return ys, xs

    def parapet(self, pts_top, pts_bottom, colour='stone', cap=True, lw=None, seed=None, course=12.0):
        """a stone wall between a top edge and a bottom edge (polylines left->right), stonework inked"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        T = np.asarray(pts_top, np.float32); B = np.asarray(pts_bottom, np.float32)
        P = np.vstack([T, B[::-1]])
        self.fill(P, colour, tex=0.8, dir=2, vary=0.03, r=r)
        y0, y1 = P[:, 1].min(), P[:, 1].max()
        x0, x1 = P[:, 0].min(), P[:, 0].max()
        for yy in np.arange(y0 + course, y1, course):
            self.ink([(x0, yy), (x1, yy)], lw * 0.45, alpha=0.4, hand=0.6, split=1e9, r=r)
            off = r.uniform(0, course * 2.2)
            for xx in np.arange(x0 + off, x1, course * r.uniform(1.8, 2.6)):
                self.ink([(xx, yy - course), (xx, yy)], lw * 0.45, alpha=0.4, hand=0, r=r)
        self.flush(clip=P)
        if cap:
            Tc = np.vstack([T + (0, -max(3, course * 0.4)), T[::-1] + (0, max(2, course * 0.25))])
            self.fill(Tc, lighten(colour, 0.2), tex=0.4, dir=1, r=r)
            self.ink(Tc, lw * 0.9, closed=True, r=r)
        self.ink(P, lw, closed=True, r=r)
        self.flush()

    def railing(self, path, h, spacing=None, lw=None, colour='iron', posts=None, seed=None):
        """an iron handrail h px above `path` (a polyline along stairs or a terrace), balusters down to it"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        P = np.asarray(path, np.float32)
        top = P - (0, h)
        self.ink(top, lw * 1.3, colour=colour, r=r)
        self.ink(P - (0, h * 0.12), lw * 0.7, colour=colour, r=r)
        d = np.diff(P, axis=0); s = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))])
        sp = spacing or max(3.5, h * 0.12)
        for si in np.arange(0, s[-1] + 1e-3, sp):
            x = np.interp(si, s, P[:, 0]); y = np.interp(si, s, P[:, 1])
            self.ink([(x, y - h), (x, y)], lw * 0.5, colour=colour, alpha=0.85, hand=0.1, r=r)
        for si in np.arange(0, s[-1] + 1e-3, posts or sp * 8):
            x = np.interp(si, s, P[:, 0]); y = np.interp(si, s, P[:, 1])
            self.ink([(x, y - h - 3), (x, y)], lw * 1.2, colour=colour, r=r)
            self.dab(x, y - h - 3, lw * 1.3, colour, rr=r)
        self.flush()

    # ================================================================== plants
    def roses(self, path, n=40, colour='rose', dark='rose_dark', light='rose_light', size=6.0, leaves=1.0, spread=None,
              top_heavy=0.6, seed=None, lw=None, clusters=True):
        """a climbing rose: a wandering stem along `path` (bottom -> top), side shoots, pairs of leaves, and roses
        in small clusters, more of them toward the top"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        P = spline(np.asarray(path, np.float32), 10)
        d = np.diff(P, axis=0); s = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))]); L = s[-1]
        spread = size * 2.6 if spread is None else spread
        stem = '#56603a'
        P2 = P + np.stack([np.sin(s / (size * 4.5)) * size * 0.8, np.zeros_like(s)], 1)
        self.ink(P, lw * 1.15, colour=stem, alpha=0.9, hand=0.9, r=r)
        self.ink(P2, lw * 0.7, colour=stem, alpha=0.75, hand=0.9, r=r)
        for _ in range(int(L / (size * 6)) + 1):
            si = r.uniform(0.1, 1) * L
            bx, by = np.interp(si, s, P[:, 0]), np.interp(si, s, P[:, 1])
            sd = 1 if r.random() < 0.5 else -1
            self.ink([(bx, by), (bx + sd * spread * 0.7, by - size * 1.2), (bx + sd * spread * 1.1, by - size * 2.6)],
                     lw * 0.6, colour=stem, alpha=0.7, hand=0.5, r=r)
        nl = int(L / size * 2.6 * leaves)
        for _ in range(nl):
            si = r.uniform(0, L)
            x = np.interp(si, s, P[:, 0]) + r.normal(0, spread * 0.5); y = np.interp(si, s, P[:, 1]) + r.normal(0, spread * 0.3)
            ang = r.uniform(-2.7, -0.4)
            for k in (-1, 1):
                self.leaf(x + k * size * 0.4, y + k * size * 0.1, size * r.uniform(1.0, 1.5), size * r.uniform(0.55, 0.75),
                          ang + k * 0.7, ('leaf_dark', 'leaf', 'leaf_dark', 'leaf_mid')[r.integers(0, 4)], r=r)
        self.flush()
        u = 1 - (1 - r.random(n)) ** (1 + 2 * top_heavy)
        pts = []
        for i in range(n):
            si = u[i] * L
            x = np.interp(si, s, P[:, 0]) + r.normal(0, spread * 0.55); y = np.interp(si, s, P[:, 1]) + r.normal(0, spread * 0.3)
            pts.append((x, y))
            if clusters and r.random() < 0.45:
                for _ in range(int(r.integers(1, 3))):
                    pts.append((x + r.normal(0, size * 1.3), y + r.normal(0, size * 1.1)))
        pts.sort(key=lambda p: p[1])
        for x, y in pts:
            for _ in range(2):
                a = r.uniform(0, 2 * np.pi)
                self.leaf(x + np.cos(a) * size * 0.95, y + np.sin(a) * size * 0.75, size * r.uniform(1.0, 1.4), size * 0.62,
                          a + r.normal(0, 0.4), ('leaf_dark', 'leaf')[r.integers(0, 2)], r=r)
        for x, y in pts:
            rr = size * r.uniform(0.75, 1.2)
            if r.random() < 0.14:
                self.fill(leaf_pts(x, y, rr * 1.2, rr * 0.8, -np.pi / 2 + r.normal(0, 0.4)), dark, tex=0.3, hand=0, r=r)
                continue
            n_ = 16
            ang = np.linspace(0, 2 * np.pi, n_, endpoint=False) + r.uniform(0, 1)
            rad = rr * (1 + 0.12 * np.sin(ang * r.integers(4, 6) + r.uniform(0, 6)) + 0.05 * r.normal(0, 1, n_))
            cup = np.stack([x + np.cos(ang) * rad, y + np.sin(ang) * rad * 0.88], 1).astype(np.float32)
            self.fill(cup, colour, tex=0.4, dir=2, hand=0, vary=0.05, r=r)
            self.fill(ellipse_pts(x + rr * 0.08, y + rr * 0.08, rr * 0.5, rr * 0.42, 12, r.uniform(0, 3)), deepen(colour, 0.22),
                      tex=0.3, hand=0, r=r)
            self.fill(ellipse_pts(x - rr * 0.25, y - rr * 0.42, rr * 0.55, rr * 0.22, 10, -0.25), mix(colour, light, 0.45),
                      tex=0.3, hand=0, r=r)
            for k in range(3):
                a0 = r.uniform(0, 2 * np.pi); rk = rr * (0.28 + 0.2 * k)
                self.ink(ellipse_pts(x, y, rk, rk * 0.85, 10, 0, a0, a0 + r.uniform(1.8, 3.2)), max(0.55, min(lw * 0.6, rr * 0.14)),
                         colour=dark, alpha=0.85, hand=0, r=r)
            self.ink(cup, max(0.5, lw * 0.45), closed=True, colour=dark, alpha=0.55, hand=0, r=r)
        self.flush()

    def tree(self, x, base, h, rad, trunk='trunk', ramp=('leaf_dark', '#3a7040', 'leaf', 'leaf_mid', 'leaf_light'),
             clumps=9, leaf=(7, 12), density=1.0, lean=0.0, seed=None, lw=None):
        """a rounded street tree: trunk and branches in ink, a crown of clumps of small leaf dabs lit from the upper left"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        ccx, ccy = x + lean * h, base - h + rad * 0.85
        tw = max(4.0, rad * 0.09)
        T = spline([(x - tw, base), (x - tw * 0.8 + lean * h * 0.4, base - h * 0.4), (ccx - tw * 0.5, ccy + rad * 0.2)], 8)
        T2 = spline([(ccx + tw * 0.5, ccy + rad * 0.2), (x + tw * 0.8 + lean * h * 0.4, base - h * 0.4), (x + tw, base)], 8)
        TP = np.vstack([T, T2])
        self.fill(TP, trunk, tex=0.8, dir=0, r=r)
        self.ink(T, lw, r=r); self.ink(T2, lw, r=r)
        for k in range(4):
            a = -np.pi / 2 + r.uniform(-1.1, 1.1)
            sx, sy = ccx + r.normal(0, tw), ccy + rad * 0.25
            ex, ey = sx + np.cos(a) * rad * 0.6, sy + np.sin(a) * rad * 0.55
            self.ink([(sx, sy), ((sx + ex) / 2 + r.normal(0, 4), (sy + ey) / 2), (ex, ey)], lw * 1.2, colour='trunk', r=r)
        self.flush()
        cl = []
        for k in range(clumps):
            a = r.uniform(0, 2 * np.pi); d = r.uniform(0.25, 0.66) * (0 if k == 0 else 1)
            cr = rad * r.uniform(0.32, 0.46)
            cl.append((ccx + np.cos(a) * rad * d, ccy + np.sin(a) * rad * d * 0.8 - rad * 0.05, cr))
        cl.sort(key=lambda c: -c[1])                       # lower clumps first, the top ones lie over them
        ramp_c = [hexc(c) for c in ramp]
        Lx, Ly = -0.6, -0.8
        for (cx, cy, cr) in cl:
            self.fill(ellipse_pts(cx, cy + cr * 0.08, cr * 0.9, cr * 0.82, 22), ramp_c[0], tex=0.8, dir=2, hand=1.4, r=r)
        for (cx, cy, cr) in cl:
            m = int(cr * cr / (leaf[0] * leaf[1]) * 3.4 * density)
            ang = r.uniform(0, 2 * np.pi, m); rd = np.sqrt(r.random(m)) * cr * 1.06
            px, py = cx + np.cos(ang) * rd, cy + np.sin(ang) * rd * 0.9
            nx, ny = (px - cx) / cr, (py - cy) / cr
            nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
            dome = nx * Lx * 0.7 + ny * Ly * 0.7 + nz * 0.45
            glob_ = -0.25 * (cy - ccy) / rad - 0.12 * (cx - ccx) / rad
            lit = np.clip(0.18 + 0.7 * dome + glob_ + 0.12 * r.normal(0, 1, m), 0, 0.999)
            order = np.argsort(lit)
            for i in order:
                c = ramp_c[min(len(ramp_c) - 1, int(lit[i] ** 1.25 * len(ramp_c)))]
                self.leaf(px[i], py[i], r.uniform(*leaf), r.uniform(*leaf) * 0.55, np.arctan2(ny[i], nx[i]) * 0.6 - 0.9 + r.normal(0, 0.7),
                          c, vary=0.03, r=r)
        self.flush()

    def pot(self, x, base, w, h, plant='bush', colour='terracotta', flowers='red', lw=None, seed=None):
        """a terracotta pot on the ground with a bush, a tall plant or flowers"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        P = np.array([(x - w / 2, base - h), (x + w / 2, base - h), (x + w * 0.38, base), (x - w * 0.38, base)], np.float32)
        rim = rect(x - w * 0.56, base - h - h * 0.16, x + w * 0.56, base - h + h * 0.05)
        if plant == 'tall':
            for _ in range(int(14 * max(1, w / 20))):
                a = -np.pi / 2 + r.normal(0, 0.5)
                L = h * r.uniform(1.2, 2.6)
                self.leaf(x + np.cos(a) * L * 0.5, base - h + np.sin(a) * L * 0.5, L, w * 0.18, a, ('leaf_dark', 'leaf', 'leaf_mid')[r.integers(0, 3)], r=r)
        else:
            cr = w * 0.75
            for _ in range(int(cr * cr / 8)):
                a = r.uniform(np.pi, 2 * np.pi); d = np.sqrt(r.random()) * cr
                lx, ly = x + np.cos(a) * d, base - h - h * 0.1 + np.sin(a) * d * 0.85
                lit = np.clip(0.5 - 0.5 * (np.cos(a) * 0.6 + np.sin(a) * 0.8) * d / cr + 0.15 * r.normal(), 0, 0.99)
                self.leaf(lx, ly, cr * 0.32, cr * 0.18, a + r.normal(0, 0.5), ('leaf_dark', 'leaf', 'leaf_mid', 'leaf_light')[int(lit * 4)], r=r)
            if plant == 'flowers':
                fc = FLOWER_SETS.get(flowers, flowers)
                for _ in range(int(cr * 0.9)):
                    a = r.uniform(np.pi, 2 * np.pi); d = np.sqrt(r.random()) * cr * 0.9
                    self.dab(x + np.cos(a) * d, base - h - h * 0.1 + np.sin(a) * d * 0.85, cr * r.uniform(0.09, 0.14), fc[r.integers(0, 3)], rr=r)
        self.fill(P, colour, tex=0.6, dir=0, vary=0.05, r=r)
        self.fill(rim, deepen(colour, 0.08), tex=0.4, r=r)
        self.ink(P, lw * 0.9, closed=True, r=r)
        self.ink(rim, lw * 0.8, closed=True, corners=True, r=r)
        self.flush()

    # ================================================================== bunting, lamps, signs, people
    def bunting(self, p0, p1, sag=40.0, size=24.0, gap=0.25, colours=BUNTING, seed=None, lw=None, start=None):
        """a string of triangular pennants sagging from p0 to p1; size = pennant width in px"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        (ax, ay), (bx, by) = p0, p1
        n = 200
        t = np.linspace(0, 1, n)
        X = ax + (bx - ax) * t; Y = ay + (by - ay) * t + sag * 4 * t * (1 - t)
        S = np.stack([X, Y], 1)
        d = np.diff(S, axis=0); s = np.concatenate([[0], np.cumsum(np.hypot(d[:, 0], d[:, 1]))]); L = s[-1]
        step = size * (1 + gap)
        ci = int(r.integers(0, len(colours))) if start is None else start
        lw_s = max(0.6, min(lw, size * 0.06))
        for si in np.arange(step * 0.4, L - size, step):
            p = np.array([np.interp(si, s, X), np.interp(si, s, Y)])
            q = np.array([np.interp(si + size, s, X), np.interp(si + size, s, Y)])
            dv = q - p; dl = np.hypot(*dv) + 1e-6
            nv = np.array([-dv[1], dv[0]]) / dl
            if nv[1] < 0: nv = -nv
            # pennants hang more vertically than the string's normal
            hang = nv * 0.55 + np.array([0, 1]) * 0.45; hang /= np.hypot(*hang)
            hang = hang + r.normal(0, 0.05, 2)
            tip = (p + q) / 2 + hang * size * r.uniform(1.0, 1.15)
            col = hexc(colours[ci % len(colours)]); ci += 1 + (r.random() < 0.12)
            self.fill(np.array([p, q, tip], np.float32), col, tex=0.6, dir=2, hand=0, vary=0.03, r=r)
            mid = (p + q) / 2
            self.fill(np.array([mid, q, tip], np.float32), deepen(col, 0.13), tex=0.6, dir=2, hand=0, r=r)
            self.ink(np.array([p, tip, q], np.float32), lw_s, alpha=0.75, hand=0.15 if size > 20 else 0, r=r)
        self.ink(S, lw_s * 1.1, alpha=0.85, hand=0.2, r=r)
        self.flush()

    def lamp(self, x, base, h, wall=None, lw=None, seed=None, colour='iron'):
        """an iron street lamp on a post (or on a wall bracket, wall=x of the wall)"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        lh = h * 0.16; lwid = lh * 0.42
        if wall is None:
            pw = max(2.5, h * 0.025)
            self.fill(rect(x - pw, base - h, x + pw, base), colour, tex=0.2, hand=0.2, r=r)
            self.fill(np.array([(x - pw * 3, base), (x + pw * 3, base), (x + pw * 1.6, base - h * 0.08), (x - pw * 1.6, base - h * 0.08)], np.float32), colour, tex=0.2, hand=0, r=r)
            top = (x, base - h)
        else:
            dirx = 1 if x > wall else -1
            arm = spline([(wall, base - h), (wall + dirx * abs(x - wall) * 0.5, base - h - lh * 0.4), (x, base - h - lh * 0.1)], 8)
            self.ink(arm, lw * 1.5, colour=colour, r=r)
            self.ink(ellipse_pts(wall + dirx * abs(x - wall) * 0.35, base - h + lh * 0.25, lh * 0.25, lh * 0.25, 12, 0, 0, 5), lw, colour=colour, r=r)
            top = (x, base - h + lh * 0.2)
        tx, ty = top
        G = np.array([(tx - lwid, ty - lh), (tx + lwid, ty - lh), (tx + lwid * 0.7, ty), (tx - lwid * 0.7, ty)], np.float32)
        self.fill(G, '#f6e2a8', tex=0.3, r=r, hand=0)
        self.ink(G, lw, closed=True, colour=colour, r=r)
        self.ink([(tx, ty - lh), (tx, ty)], lw * 0.6, colour=colour, r=r)
        Cp = np.array([(tx - lwid * 1.3, ty - lh), (tx, ty - lh - lh * 0.45), (tx + lwid * 1.3, ty - lh)], np.float32)
        self.fill(Cp, colour, tex=0.2, hand=0, r=r)
        self.dab(tx, ty - lh - lh * 0.5, lwid * 0.25, colour, rr=r)
        self.flush()

    def sign(self, wall_x, y, r_, colour='tomato', icon='cup', side=1, lw=None, seed=None, text=None):
        """a hanging shop sign on a curly iron bracket sticking out from a wall"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        L = r_ * 2.6
        x1 = wall_x + side * L
        self.ink([(wall_x, y), (x1, y)], lw * 1.3, colour='iron', r=r)
        self.ink(spline([(wall_x, y + r_ * 0.9), (wall_x + side * L * 0.45, y + r_ * 0.15), (wall_x + side * L * 0.8, y)], 8), lw, colour='iron', r=r)
        self.ink(ellipse_pts(wall_x + side * L * 0.3, y - r_ * 0.28, r_ * 0.25, r_ * 0.25, 14, 0, 0, 5.2), lw * 0.8, colour='iron', r=r)
        cx, cy = wall_x + side * L * 0.62, y + r_ * 1.25
        self.ink([(cx - r_ * 0.4, y), (cx - r_ * 0.4, cy - r_)], lw * 0.6, colour='iron', r=r)
        self.ink([(cx + r_ * 0.4, y), (cx + r_ * 0.4, cy - r_)], lw * 0.6, colour='iron', r=r)
        D = ellipse_pts(cx, cy, r_, r_, 30)
        self.fill(D, colour, tex=0.6, dir=2, r=r)
        self.fill(ellipse_pts(cx, cy, r_ * 0.8, r_ * 0.8, 30), lighten(colour, 0.12), tex=0.5, r=r)
        if icon == 'cup':
            C = np.array([(cx - r_ * 0.38, cy - r_ * 0.22), (cx + r_ * 0.3, cy - r_ * 0.22), (cx + r_ * 0.22, cy + r_ * 0.32), (cx - r_ * 0.3, cy + r_ * 0.32)], np.float32)
            self.fill(C, 'cream', tex=0.3, hand=0, r=r)
            self.ink(ellipse_pts(cx + r_ * 0.36, cy, r_ * 0.13, r_ * 0.16, 12, 0, -1.6, 1.6), lw * 0.9, colour='cream', alpha=1, r=r)
            for k in (-1, 0, 1):
                self.ink([(cx + k * r_ * 0.15, cy - r_ * 0.35), (cx + k * r_ * 0.15 + r_ * 0.06, cy - r_ * 0.55)], lw * 0.6, colour='cream', alpha=0.9, r=r)
        elif icon == 'key':
            self.ink(ellipse_pts(cx - r_ * 0.3, cy, r_ * 0.2, r_ * 0.2, 14), lw * 1.2, closed=True, colour='gold', alpha=1, r=r)
            self.ink([(cx - r_ * 0.1, cy), (cx + r_ * 0.45, cy)], lw * 1.2, colour='gold', alpha=1, r=r)
            self.ink([(cx + r_ * 0.3, cy), (cx + r_ * 0.3, cy + r_ * 0.18)], lw * 1.1, colour='gold', alpha=1, r=r)
        elif icon == 'loaf':
            Lf = ellipse_pts(cx, cy, r_ * 0.48, r_ * 0.28, 20)
            self.fill(Lf, 'apricot', tex=0.3, hand=0, r=r)
            for k in (-1, 0, 1):
                self.ink([(cx + k * r_ * 0.18 - r_ * 0.06, cy - r_ * 0.12), (cx + k * r_ * 0.18 + r_ * 0.06, cy + r_ * 0.1)], lw * 0.7, r=r)
        elif icon == 'flower':
            for k in range(5):
                a = k / 5 * 2 * np.pi
                self.dab(cx + np.cos(a) * r_ * 0.25, cy + np.sin(a) * r_ * 0.25, r_ * 0.2, 'blossom_pink', rr=r)
            self.dab(cx, cy, r_ * 0.15, 'blossom_yellow', rr=r)
        self.ink(D, lw, closed=True, r=r)
        self.flush()

    def person(self, x, base, h, coat='cobalt', legs='#3b3b46', hair='hair', umbrella=None, bag=None, facing=1,
               reflect=False, lw=None, seed=None, stride=0.3, balloon=None, basket=None):
        """a small, very simple passer-by seen from behind / three-quarter (no face), optional umbrella"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        hr = h * 0.085
        def parts(sgn):
            # sgn = -1 draws the reflection upside down about the base line
            def P(pts):
                a = np.asarray(pts, np.float32).copy()
                if sgn < 0: a[:, 1] = 2 * base - a[:, 1]
                return a
            out = []
            hip = base - h * 0.44
            for k, st in ((-1, stride), (1, -stride)):
                lx = x + k * h * 0.05
                out.append((P([(lx - h * 0.035, hip), (lx + h * 0.035, hip), (lx + st * h * 0.18 + h * 0.03, base), (lx + st * h * 0.18 - h * 0.03, base)]), legs))
                out.append((P([(lx + st * h * 0.18 - h * 0.045, base - h * 0.03), (lx + st * h * 0.18 + h * 0.06 * facing, base - h * 0.03),
                               (lx + st * h * 0.18 + h * 0.06 * facing, base), (lx + st * h * 0.18 - h * 0.045, base)]), '#2a2420'))
            out.append((P([(x - h * 0.12, base - h * 0.82), (x + h * 0.12, base - h * 0.82), (x + h * 0.17, hip + h * 0.06), (x - h * 0.17, hip + h * 0.06)]), coat))
            out.append((P(ellipse_pts(x, base - h * 0.89, hr * 0.95, hr * 1.05, 16)), 'skin'))
            out.append((P(ellipse_pts(x - facing * hr * 0.25, base - h * 0.91, hr * 1.0, hr * 0.95, 16)), hair))
            return out
        if reflect:
            for Pp, c in parts(-1):
                self.fill(Pp, mix(mix(c, 'wet', 0.45), '#000000', 0.15), tex=0.6, dir=0, hand=0, alpha=0.55, r=r)
            self.flush()
        for Pp, c in parts(1):
            self.fill(Pp, c, tex=0.4, dir=0, hand=0, r=r)
            self.ink(Pp, lw * 0.6, closed=True, alpha=0.7, hand=0, r=r)
        if bag:
            B = rect(x + facing * h * 0.13, base - h * 0.6, x + facing * h * 0.24, base - h * 0.48)
            self.fill(B, bag, tex=0.3, hand=0, r=r); self.ink(B, lw * 0.6, closed=True, r=r)
        if balloon:
            hx, hy = x + facing * h * 0.16, base - h * 0.58
            bx, by = x + facing * h * 0.34, base - h * 1.55
            self.ink(spline([(hx, hy), (hx + facing * h * 0.12, base - h * 1.0), (bx, by + h * 0.16)], 8), lw * 0.5, alpha=0.8, r=r)
            Bl = ellipse_pts(bx, by, h * 0.13, h * 0.155, 24)
            self.fill(Bl, balloon, tex=0.3, hand=0, r=r)
            self.fill(ellipse_pts(bx - h * 0.045, by - h * 0.06, h * 0.035, h * 0.05, 10, -0.5), lighten(balloon, 0.55), tex=0.1, hand=0, r=r)
            self.fill(np.array([(bx - h * 0.02, by + h * 0.15), (bx + h * 0.02, by + h * 0.15), (bx, by + h * 0.18)], np.float32), deepen(balloon, 0.2), hand=0, r=r)
            self.ink(Bl, lw * 0.7, closed=True, r=r)
        if basket:
            bx0 = x + facing * h * 0.12
            Bk = np.array([(bx0 - h * 0.07, base - h * 0.55), (bx0 + h * 0.15, base - h * 0.55), (bx0 + h * 0.12, base - h * 0.43), (bx0 - h * 0.04, base - h * 0.43)], np.float32)
            if facing < 0: Bk[:, 0] = 2 * bx0 - Bk[:, 0]
            for k in range(6):
                self.dab(Bk[:, 0].mean() + r.normal(0, h * 0.04), base - h * 0.57 + r.normal(0, h * 0.015), h * 0.03, FLOWER_SETS[basket][k % 3], rr=r)
            self.fill(Bk, 'ochre', tex=0.4, hand=0, r=r)
            self.ink(Bk, lw * 0.6, closed=True, r=r)
        if umbrella:
            ux, uy = x + facing * h * 0.08, base - h * 1.08
            U = np.vstack([ellipse_pts(ux, uy, h * 0.36, h * 0.2, 20, 0, np.pi, 2 * np.pi), [(ux + h * 0.36, uy)]])
            self.ink([(ux, uy), (x + facing * h * 0.1, base - h * 0.62)], lw * 0.8, r=r)
            self.fill(U, umbrella, tex=0.4, hand=0, r=r)
            self.ink(U, lw * 0.8, closed=True, r=r)
            for k in (-0.5, 0, 0.5):
                self.ink([(ux, uy - h * 0.2), (ux + k * h * 0.36, uy)], lw * 0.5, alpha=0.6, r=r)
        self.flush()

    def bistro(self, x, base, s, top='ivory', iron='iron', chairs=2, cups=True, lw=None, seed=None):
        """a little cafe table (round top on a pedestal) with iron chairs either side; s = table height"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        for k in range(chairs):
            sd = -1 if k % 2 == 0 else 1
            cx = x + sd * s * 0.62
            seat = base - s * 0.48
            self.ink([(cx - s * 0.18, seat), (cx + s * 0.18, seat)], lw * 1.4, colour=iron, r=r)
            self.ink([(cx - sd * s * 0.16, seat), (cx - sd * s * 0.2, base)], lw, colour=iron, r=r)
            self.ink([(cx + sd * s * 0.16, seat), (cx + sd * s * 0.22, base)], lw, colour=iron, r=r)
            back = cx + sd * s * 0.16
            self.ink([(back, seat), (back + sd * s * 0.04, seat - s * 0.5)], lw, colour=iron, r=r)
            self.ink(ellipse_pts(back + sd * s * 0.02, seat - s * 0.42, s * 0.07, s * 0.1, 12), lw * 0.7, closed=True, colour=iron, r=r)
        self.ink([(x, base - s * 0.9), (x, base)], lw * 1.6, colour=iron, r=r)
        self.ink([(x - s * 0.2, base), (x + s * 0.2, base)], lw * 1.4, colour=iron, r=r)
        T = ellipse_pts(x, base - s * 0.92, s * 0.36, s * 0.07, 20)
        self.fill(T, top, tex=0.4, hand=0, r=r)
        self.ink(T, lw * 0.8, closed=True, r=r)
        if cups:
            for dx in (-0.14, 0.12):
                C = rect(x + dx * s - s * 0.05, base - s * 1.04, x + dx * s + s * 0.05, base - s * 0.95)
                self.fill(C, ('tomato', 'cream', 'cerulean')[r.integers(0, 3)], tex=0.2, hand=0, r=r)
                self.ink(C, lw * 0.5, closed=True, r=r)
        self.flush()

    def poster(self, x0, y0, x1, y1, colour='butter', seed=None, lw=None):
        """a small painted notice or poster on a wall: a coloured sheet with a few blocks of 'type'"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        P = rect(x0, y0, x1, y1)
        self.fill(P, colour, tex=0.5, dir=2, vary=0.04, r=r)
        w, h = x1 - x0, y1 - y0
        self.fill(rect(x0 + w * 0.15, y0 + h * 0.12, x1 - w * 0.15, y0 + h * 0.3), deepen(colour, 0.35), tex=0.2, hand=0.2, r=r)
        if r.random() < 0.6:
            self.fill(ellipse_pts((x0 + x1) / 2, y0 + h * 0.58, w * 0.22, w * 0.22, 14), ('tomato', 'teal', 'cobalt', 'mustard')[r.integers(0, 4)], tex=0.3, hand=0, r=r)
        for k in range(3):
            yy = y0 + h * (0.78 + 0.07 * k)
            self.ink([(x0 + w * 0.18, yy), (x1 - w * (0.18 + 0.15 * (k == 2)), yy)], lw * 0.5, alpha=0.6, hand=0.2, r=r)
        self.ink(P, lw * 0.8, closed=True, corners=True, r=r)
        self.flush()

    def cat(self, x, base, s, colour='#e9a65a', seed=None, lw=None):
        """a small sitting cat seen from behind"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        B = ellipse_pts(x, base - s * 0.35, s * 0.32, s * 0.36, 20)
        Hd = ellipse_pts(x, base - s * 0.8, s * 0.2, s * 0.18, 16)
        E1 = np.array([(x - s * 0.18, base - s * 0.86), (x - s * 0.13, base - s * 1.02), (x - s * 0.04, base - s * 0.93)], np.float32)
        E2 = E1 * (-1, 1) + (2 * x, 0)
        Tl = spline([(x + s * 0.25, base - s * 0.08), (x + s * 0.5, base - s * 0.1), (x + s * 0.55, base - s * 0.35)], 8)
        for Pp in (B, Hd, E1, E2):
            self.fill(Pp, colour, tex=0.5, hand=0, r=r)
        self.ink(Tl, lw * 2.2, colour=colour, alpha=1, hand=0, r=r)
        for Pp in (B, Hd, E1, E2):
            self.ink(Pp, lw * 0.7, closed=True, alpha=0.8, hand=0, r=r)
        for k in range(3):
            self.ink([(x - s * 0.1 + k * s * 0.1, base - s * 0.55), (x - s * 0.12 + k * s * 0.1, base - s * 0.4)], lw * 0.5, alpha=0.4, colour='#9a5a2a', hand=0, r=r)
        self.flush()

    # ================================================================== street and the wet reflection
    def street(self, y0, vp, colour='cobble', dark='#a29f98', rows=None, seed=None, lw=None, x_range=None, poly=None):
        """cobbled paving from y0 (far edge) to the bottom of the canvas, joints running toward the vanishing point"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        vx, vy = vp
        H = self.H
        P = poly if poly is not None else rect(-5, y0, self.W + 5, H + 5)
        self.fill(P, dark, tex=0.5, dir=2, hand=0, r=r)
        self.flush()
        # rows: their height grows toward the viewer (perspective)
        ys = [y0]
        while ys[-1] < H:
            ys.append(ys[-1] + max(4.0, (ys[-1] - vy) * 0.075))
        col = hexc(colour)
        for a, b in zip(ys[:-1], ys[1:]):
            hrow = b - a
            sw = hrow * 2.3
            off = r.uniform(0, sw)
            # stone widths in screen space follow the row; place stones from left to right
            xs = np.arange(-sw + off, self.W + sw, sw)
            for xx in xs:
                ww = sw * r.uniform(0.82, 0.95)
                c = col * (1 + 0.025 * r.normal()) + 0.006 * r.normal(0, 1, 3)
                # slant the stone toward the vanishing point
                k = (xx - vx) / max(1.0, (a - vy))
                Q = np.array([(xx, a + hrow * 0.08), (xx + ww, a + hrow * 0.08), (xx + ww + k * hrow * 0.85, b - hrow * 0.08),
                              (xx + k * hrow * 0.85, b - hrow * 0.08)], np.float32)
                cxq, cyq = Q.mean(0)
                Q = (Q - (cxq, cyq)) * 0.94 + (cxq, cyq)
                self.fill(Q, c, tex=0.6, dir=2, hand=0.25, r=r)
        self.flush(clip=P)
        self._street = (ys, P, vp)
        return ys

    def joints(self, alpha=0.3, seed=None, lw=None):
        """re-ink the paving joints faintly over the wet reflection so the stones still read"""
        r = self._r(seed)
        lw = self.lw if lw is None else lw
        ys, P, (vx, vy) = self._street
        for a, b in zip(ys[:-1], ys[1:]):
            self.ink([(-5, a), (self.W + 5, a)], lw * 0.6, alpha=alpha, colour='#4a5258', hand=0.6, split=1e9, r=r)
            hrow = b - a; sw = hrow * 2.3
            for xx in np.arange(-sw + r.uniform(0, sw), self.W + sw, sw * r.uniform(0.9, 1.1)):
                k = (xx - vx) / max(1.0, (a - vy))
                self.ink([(xx, a), (xx + k * hrow, b)], lw * 0.5, alpha=alpha * 0.8, colour='#4a5258', hand=0, r=r)
        self.flush(clip=P)

    def reflect(self, src, base, y0, y1=None, strength=0.62, smear=(2.0, 22.0), ripple=2.5, darken=0.86, tint='wet',
                region=None, seed=None, fade=0.55):
        """the wet street: mirror `src` (the canvas before the street was painted) about each column's base line
        `base` (array over x, or a number), smeared vertically, rippled, darkened and mixed into the paving"""
        r = self._r(seed)
        y1 = self.H if y1 is None else y1
        y0 = int(y0); y1 = int(y1)
        W = self.W
        base = np.broadcast_to(np.asarray(base, np.float32), (W,))
        ys = np.arange(y0, y1, dtype=np.float32)[:, None]
        xs = np.arange(W, dtype=np.float32)[None, :]
        dist = np.maximum(ys - base[None, :], 0)
        rip = (fbm1d(y1 - y0, 18, 3, int(r.integers(1 << 30)))[:, None] * ripple * (1 + dist / 260)).astype(np.float32)
        colj = (fbm1d(W, 9, 2, int(r.integers(1 << 30))) * ripple * 0.8)[None, :]
        sx = np.clip(xs + rip + colj * np.clip(dist / 80, 0, 1) + 0.35 * self.TH[y0:y1] * ripple, 0, W - 1)
        sy = np.clip(base[None, :] - dist * 1.0, 0, self.H - 1)
        ix = sx.astype(np.int32); iy = sy.astype(np.int32)
        R = src[iy, ix]
        # vertical smear grows with distance from the base line (two blurs, blended)
        s0, s1 = smear
        Rb1 = np.stack([_box(_box(R[..., c], int(s0), 0), 1, 1) for c in range(3)], -1)
        Rb2 = np.stack([_box(_box(_box(R[..., c], int(s1), 0), int(s1 * 0.6), 0), 3, 1) for c in range(3)], -1)
        t = np.clip(dist / 260, 0, 1)[..., None]
        R = Rb1 * (1 - t) + Rb2 * t
        R = R * darken + hexc(tint) * (1 - darken)
        k = strength * (1 - fade * np.clip(dist / max(1, (y1 - y0)), 0, 1))
        k = k * (1 + 0.2 * self.TV[y0:y1]) * (dist > 0)
        if region is not None: k = k * region[y0:y1]
        k = np.clip(k, 0, 1)[..., None]
        C = self.C[y0:y1]
        R = R * (1 + 0.05 * self.TV[y0:y1, :, None])
        self.C[y0:y1] = C * (1 - k) + R * k

    @contextmanager
    def mirror(self, base, x0, x1, top, strength=0.45, smear=10.0, darken=0.85, tint='wet'):
        """everything painted inside the block is also reflected in the wet ground below `base`"""
        x0, x1, top = max(0, int(x0)), min(self.W, int(x1)), max(0, int(top))
        y_end = min(self.H, int(2 * base - top) + 2)
        before = self.C[top:y_end, x0:x1].copy()
        try: yield
        finally:
            self.flush()
            after = self.C[top:y_end, x0:x1]
            m = (np.abs(after - before).max(-1) > 1e-3).astype(np.float32)
            b = int(round(base)) - top
            n = min(b, after.shape[0] - b)
            if n > 2:
                src = after[b - n:b][::-1]; ms = m[b - n:b][::-1]
                sm = int(smear)
                src = np.stack([_box(src[..., c] * ms, sm, 0) for c in range(3)], -1)
                ms_b = _box(ms, sm, 0)
                col = src / np.maximum(ms_b, 1e-4)[..., None]
                col = col * darken + hexc(tint) * (1 - darken)
                fade = np.linspace(1, 0.2, n, dtype=np.float32)[:, None]
                a = np.clip(ms_b * strength * fade * (1 - m[b:b + n]), 0, 1)[..., None]
                after[b:b + n] = after[b:b + n] * (1 - a) + col * a

    def glints(self, y0, y1, n=60, colour='#f4f4ee', seed=None, region=None):
        """small horizontal light glints on the wet paving"""
        r = self._r(seed)
        for _ in range(n):
            y = r.uniform(y0, y1); x = r.uniform(0, self.W)
            if region is not None and region[int(min(self.H - 1, y)), int(min(self.W - 1, x))] < 0.5: continue
            L = r.uniform(6, 26) * (0.5 + (y - y0) / max(1, y1 - y0))
            self.ink([(x, y), (x + L, y + r.normal(0, 0.4))], r.uniform(0.8, 1.8), colour=colour, alpha=0.5, hand=0.2, r=r)
        self.flush()

    # ================================================================== finish and output
    def finish(self, soft=0.25, grain=1.0, warmth=0.5, vignette=0.35):
        """record the finishing (applied in render, so every stage snapshot matches the final look)"""
        self.fin = dict(soft=soft, grain=grain, warmth=warmth, vignette=vignette)
        return self

    def render(self):
        out = self.C
        f = self.fin
        if f:
            if f['soft']:
                b = np.stack([blur(out[..., c], 0.6) for c in range(3)], -1)
                out = out * (1 - f['soft']) + b * f['soft']
            if f['warmth']:
                lum = out.mean(-1, keepdims=True)
                out = out * (1 - 0.04 * f['warmth']) + out * hexc('#fff3e0') * 0.04 * f['warmth'] + 0.004 * f['warmth']
                out = lum + (out - lum) * (1 + 0.04 * f['warmth'])
            if f['vignette']:
                yy = (np.arange(self.H, dtype=np.float32)[:, None] / self.H - 0.5) * 2
                xx = (np.arange(self.W, dtype=np.float32)[None, :] / self.W - 0.5) * 2
                v = 1 - f['vignette'] * 0.08 * np.clip(xx * xx + yy * yy - 0.5, 0, None)
                out = out * v[..., None]
            if f['grain']:
                if not hasattr(self, '_grain'):
                    r = np.random.default_rng(self.seed + 99)
                    g = r.normal(0, 1, (self.H, self.W)).astype(np.float32)
                    self._grain = 0.6 * g + 0.6 * blur(g, 0.9) * 2
                out = out * (1 + 0.016 * f['grain'] * self._grain[..., None])
        return np.clip(out, 0, 1)

    def composite(self):
        return Image.fromarray((self.render() * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        if not self.keep_stages: return
        self.flush()
        im = self.composite()
        if self.stages_dir:
            os.makedirs(self.stages_dir, exist_ok=True)
            im.save(f'{self.stages_dir}/{self._n_stages:02d}_{name}.png', compress_level=1)
        else:
            b = io.BytesIO(); im.save(b, 'PNG', compress_level=1)
            self.stages.append((name, b.getvalue()))
        self._n_stages += 1

    def save(self, path, stages_dir=None, quality=88):
        self.flush()
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
