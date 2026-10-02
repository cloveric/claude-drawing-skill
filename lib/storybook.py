"""storybook — picture-book character animation: one tiny character with two eyes acts out a little journey and
the world is painted in around it as it goes (numpy + Pillow only).

Model: an animator's shot, not a still. Everything is a function of time t (seconds), so the same scene renders a
real animation (`frame(t)`, `gif()`) and a single "journey" poster (`journey()`: the finished world with the
character multiply-exposed at its key poses on a pencil motion arc).
  paper      warm beige drawing paper: big soft cloudy mottling, a slight vignette, fine tooth and a few fibres.
             The tooth multiplies the whole frame at the end and never moves, so a still background costs nothing
             between frames of the GIF.
  world      every piece of scenery is pre-painted once into its own cropped layer (colour, alpha) together with a
             REVEAL MAP: for every pixel, the moment (0..1) within that layer's own draw-on at which the brush or
             pen reaches it. Ink lines reveal along their arc length (the pen travels), washes spread from a point
             or sweep sideways with a ragged, slightly darker wet front, small props pop in with an overshoot
             (scale 0 -> 1.1 -> 1). A layer's progress comes either from a time window `when=(t0, t1)` or from
             `follow=lead`: it is drawn up to `lead` px ahead of the furthest x the character has reached, which is
             what makes the hills, flowers and banks appear just as the character passes.
  materials  washes are transparent watercolour/gouache: mottled pigment, granulation in the paper tooth, a darker
             dried edge, a light-to-dark vertical gradient and optional coloured-pencil dashes inside (the short
             crayon strokes on a picture-book hill). Ink is a dark navy fine-liner with pressure taper and a little
             hand tremor; distant hills only get a thin grey contour on top. Clouds are thick white paint with a
             lavender shadow; the sun is a yellow wash disc with crayon rays drawn one by one.
  character  `acorn` -- a nut with a scaly cap, drawn per frame from implicit shapes in its own local frame:
             the whole body is transformed by an affine squash/stretch along any axis (volume-preserving:
             k along the axis, 1/sqrt(k) across) and a roll angle, positioned so its lowest point sits exactly on
             the ground (`rest()`), lit by one world-fixed light (so the highlight stays put while it rolls) and
             given a soft contact shadow that shrinks as it leaves the ground. The face rides on the body: eyes
             with an openness (blink / sleepy / happy lids), pupils that look anywhere, brows, mouth, blush.
  acting     choreography is a list of `act(t0, t1, fn)` segments, fn(u, t) -> pose dict; helpers give the
             Disney basics: ease in / out, back (overshoot) and spring settles, ballistic arcs, impact squash.
             FX are timed events: impact lines, dust puffs (white circles with a grey rim), water ripples, dirt
             specks, sparkles and confetti; speed lines are added automatically when the character moves fast.
  lettering  a cursive line is written stroke by stroke: the text mask is thinned to a one-pixel skeleton
             (Zhang-Suen), the skeleton is walked like a pen (left-most stroke first, keep going straight at
             junctions, lift and jump at dead ends), and every inked pixel takes the time of its nearest skeleton
             pixel -- so loops, ascenders and joins fill in the order a hand would write them.
Coordinates are given in design pixels on a 1920 x 1080 canvas at any output size (y down; angles in degrees,
counter-clockwise). A 720 x 405 GIF and the 1920 x 1080 poster are just two instances of the same scene.

    from storybook import Storybook
    sb = Storybook(720, 405, seed=1)
    sb.paper()
    sb.ground([(0, 700), (960, 690), (1920, 700)], when=(0, 0.6))
    sb.act(0, 1.2, lambda u, t: dict(x=600 + 600 * sb.ease(u), y=sb.rest(600 + 600 * sb.ease(u), 690)[1]))
    sb.gif('walk.gif', fps=12.5, t_end=1.2)
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font

PAPER = '#efe7da'
INK = '#1f2534'
PENCIL = '#8b8a92'
WHITE = '#fdfbf6'
GRASS, GRASS_DARK = '#93cf86', '#6db466'
MINT, LAVENDER = '#a7dcc9', '#b9bfe6'
SUN, SUN_RAY = '#f5c548', '#ee8c3a'
WATER = '#8ccbe2'
NUT, CAP, CAP_LINE = '#d39050', '#8a5634', '#58321e'
CONFETTI = ('#ee8a3c', '#f2c14e', '#d9534f', '#3fae8c', '#8c7ae6', '#5bb8dc', '#e8739b', '#7cc36a')


def hexc(h):
    if not isinstance(h, str): return np.asarray(h, np.float32)
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    return hexc(a) * (1 - t) + hexc(b) * t


def _resample(P, step, closed=False):
    P = np.asarray(P, np.float32)
    if closed: P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-6: return P[:1].copy()
    n = max(2, int(s[-1] / step) + 1)
    ss = np.linspace(0, s[-1], n)
    Q = np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1)
    return Q[:-1] if closed else Q


def _normals(P, closed=False):
    if closed: d = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else: d = np.gradient(P, axis=0)
    d /= np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-6
    return np.stack([-d[:, 1], d[:, 0]], 1)


def _closed_spline(pts, per=10):
    P = np.asarray(pts, np.float32)
    Q = spline(np.vstack([P[-1:], P, P[:2]]), per)
    return Q[per:-per - 1]


def oak_leaf(length, width=None, lobes=3, base=(0.0, 0.0), angle=-90.0, curl=0.0, seed=0):
    """outline of a lobed oak leaf, stalk at `base`, pointing at `angle` (deg ccw); returns (outline, midrib)"""
    width = width or length * 0.36
    r = np.random.default_rng(seed)
    s = np.linspace(0, 1, 90)
    prof = np.sin(np.pi * np.clip(s * 1.04, 0, 1)) ** 0.75
    lobe = 0.72 + 0.28 * np.abs(np.cos(np.pi * (lobes + 0.5) * s + r.uniform(-0.15, 0.15))) ** 0.6
    half = width * 0.5 * prof * lobe
    mid = np.stack([s * length, curl * length * np.sin(np.pi * s)], 1)
    left = mid + np.stack([np.zeros_like(s), -half], 1)
    right = mid + np.stack([np.zeros_like(s), half], 1)
    out = np.vstack([left, right[::-1]])
    a = np.deg2rad(angle)
    R = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]], np.float32)
    f = lambda P: P @ R + np.asarray(base, np.float32)
    return f(out), f(mid)


class _Layer:
    """a pre-painted piece of scenery: crop origin (x0, y0) in px, colour, alpha, reveal map and timing"""

    def __init__(self, x0, y0, rgb, a, rev=None, z=10.0, when=(0.0, 0.0), follow=None, soft=0.06, pop=None,
                 wet=0.0, ease='inout', name=''):
        self.x0, self.y0, self.rgb, self.a, self.rev = x0, y0, rgb, a, rev
        self.z, self.when, self.follow, self.soft, self.pop, self.wet, self.ease, self.name = \
            z, when, follow, soft, pop, wet, ease, name
        self.pre = None


class Storybook:
    PAPER, INK = PAPER, INK

    def __init__(self, W=1920, H=1080, seed=0, actor_size=44.0):
        self.W, self.H, self.s = W, H, W / 1920.0
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.layers, self.acts, self.props, self.fxs, self.stages = [], [], [], [], []
        self.actor_size = actor_size          # half-width of the nut in design px
        self.light = np.array([-0.5, -0.62, 0.6], np.float32); self.light /= np.linalg.norm(self.light)
        self._lead = None
        self.canvas = None
        self.paper()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------------ easing and motion helpers
    @staticmethod
    def ease(u, kind='inout'):
        u = float(np.clip(u, 0, 1))
        if kind == 'linear': return u
        if kind == 'in': return u ** 3
        if kind == 'in2': return u * u
        if kind == 'out': return 1 - (1 - u) ** 3
        if kind == 'out2': return 1 - (1 - u) ** 2
        if kind == 'sine': return 0.5 - 0.5 * np.cos(np.pi * u)
        if kind == 'back':                                  # overshoot then settle
            c1 = 1.70158; c3 = c1 + 1
            return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
        if kind == 'elastic':
            return 1 - np.exp(-6.5 * u) * np.cos(3.2 * np.pi * u) if u < 1 else 1.0
        return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2

    @staticmethod
    def spring(u, cycles=2.0, damp=5.0):
        """a decaying wobble that starts at 1 and dies out: multiply by an amplitude"""
        u = max(0.0, u)
        return float(np.exp(-damp * u) * np.cos(2 * np.pi * cycles * u))

    @staticmethod
    def arc(p0, p1, height, u):
        """ballistic hop from p0 to p1 peaking `height` px above the higher end"""
        u = float(np.clip(u, 0, 1))
        x = p0[0] + (p1[0] - p0[0]) * u
        top = min(p0[1], p1[1]) - height
        # parabola through p0, apex, p1 with apex at the u where it would be for constant gravity
        a0, a1 = np.sqrt(max(p0[1] - top, 1e-6)), np.sqrt(max(p1[1] - top, 1e-6))
        ua = a0 / (a0 + a1)
        y = top + (p0[1] - top) * ((u - ua) / ua) ** 2 if u < ua else top + (p1[1] - top) * ((u - ua) / (1 - ua)) ** 2
        return x, y

    @staticmethod
    def lerp(a, b, u):
        return a + (b - a) * u

    # ------------------------------------------------------------------ paper
    def paper(self, colour=PAPER, mottle=1.0, grain=1.0, fibres=220):
        H, W, s = self.H, self.W, self.s
        base = hexc(colour)
        m1 = noise2d(H, W, 520 * s + 8, 3, self.seed + 11)
        m2 = noise2d(H, W, 120 * s + 4, 3, self.seed + 12)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = ((xx / W - 0.5) * 1.6) ** 2 + ((yy / H - 0.47) * 1.5) ** 2
        tone = (m1 - 0.5) * 0.07 * mottle + (m2 - 0.5) * 0.025 * mottle - 0.045 * r2
        rgb = base[None, None, :] * (1 + tone[..., None])
        rgb[..., 2] -= (m1 - 0.5) * 0.012 * mottle          # warmer in the darker clouds
        self.tooth = noise2d(H, W, max(1.2, 2.0 * s), 2, self.seed + 13)
        fib = Image.new('L', (W, H), 0); d = ImageDraw.Draw(fib)
        r = np.random.default_rng(self.seed + 14)
        for _ in range(int(fibres)):
            x, y = r.uniform(0, W), r.uniform(0, H)
            L = r.uniform(8, 26) * s; a = r.uniform(0, np.pi)
            pts = [(x + np.cos(a) * L * t + np.sin(t * 3) * 2 * s, y + np.sin(a) * L * t) for t in np.linspace(-0.5, 0.5, 6)]
            d.line(pts, fill=int(r.uniform(60, 140)), width=1)
        fib = blur(np.asarray(fib, np.float32) / 255, 0.6 * s)
        rgb *= (1 - 0.035 * fib[..., None])
        self.base = np.clip(rgb, 0, 1).astype(np.float32)
        self.grain = (1 + 0.05 * grain * (self.tooth - 0.5)).astype(np.float32)[..., None]
        self.canvas = self.base.copy()

    # ------------------------------------------------------------------ low-level raster helpers
    def _px(self, pts):
        return np.asarray(pts, np.float32) * self.s

    def _bbox(self, P, pad):
        x0 = int(np.floor(P[:, 0].min() - pad)); y0 = int(np.floor(P[:, 1].min() - pad))
        x1 = int(np.ceil(P[:, 0].max() + pad)); y1 = int(np.ceil(P[:, 1].max() + pad))
        return x0, y0, max(x1, x0 + 2), max(y1, y0 + 2)

    def _poly(self, polys, box, ss=3):
        """union of polygons (px) -> antialiased mask over box"""
        x0, y0, x1, y1 = box
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0); d = ImageDraw.Draw(im)
        for P in polys:
            d.polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P], fill=255)
        im = im.resize((x1 - x0, y1 - y0), Image.BOX)
        return np.asarray(im, np.float32) / 255

    def _wobble(self, P, amp, closed=True, scale=None):
        """displace an outline along its normals by 1D fractal noise (hand-cut, hand-painted edges)"""
        if amp <= 0: return P
        Q = _resample(P, max(1.5, 3 * self.s), closed)
        n = _normals(Q, closed)
        w = fbm1d(len(Q), scale or max(8, len(Q) / 18), 3, self._seed()) * amp
        return Q + n * w[:, None]

    def _strokes(self, strokes, box, ss=3):
        """variable-width pen strokes -> (alpha, reveal). strokes: list of (P px (n,2), widths px (n,), r0, r1).
        The reveal map keeps the EARLIEST moment the nib touches each pixel."""
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        im = Image.new('L', (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
        rv = Image.new('F', (w, h), 9.0); dr = ImageDraw.Draw(rv)
        for P, wd, r0, r1 in strokes:
            n = len(P)
            for i in range(n):
                x, y = (P[i, 0] - x0) * ss, (P[i, 1] - y0) * ss
                rr = max(0.35, wd[i] * 0.5) * ss
                d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=255)
        for P, wd, r0, r1 in reversed(strokes):
            n = len(P)
            vals = np.linspace(r0, r1, n)
            for i in range(n - 1, -1, -1):
                x, y = P[i, 0] - x0, P[i, 1] - y0
                rr = wd[i] * 0.5 + 1.6
                dr.ellipse((x - rr, y - rr, x + rr, y + rr), fill=float(vals[i]))
        a = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        rev = np.minimum(np.asarray(rv, np.float32), 1.0)
        return a, rev

    def _pen(self, pts, width, taper=(0.12, 0.2), tremor=0.6, smooth=True, press=0.16, step=None):
        """design-space polyline -> (px points, px widths) with pressure taper and a little tremor"""
        P = self._px(pts)
        if smooth and len(P) > 2: P = spline(P, 10)
        P = _resample(P, step or max(0.5, 0.9 * self.s))
        n = len(P)
        if n < 2: P = np.vstack([P, P + 0.1]); n = 2
        t = np.linspace(0, 1, n)
        L = float(np.hypot(*np.diff(P, axis=0).T).sum()) + 1e-6
        ta, tb = taper
        env = np.clip(np.minimum(t / max(ta, 1e-3), (1 - t) / max(tb, 1e-3)), 0, 1) ** 0.6
        env = 0.3 + 0.7 * env if (ta or tb) else np.ones(n)
        wob = 1 + press * fbm1d(n, max(6, n / 6), 3, self._seed())
        wd = width * self.s * env * wob
        if tremor:
            P = P + _normals(P) * (fbm1d(n, max(6, L / (40 * self.s + 1)), 2, self._seed()) * tremor * self.s)[:, None]
        return P.astype(np.float32), wd.astype(np.float32)

    def _x_rev(self, box, xa, xb, noise=26.0, wave=0.0):
        """reveal map that sweeps left to right between design x = xa and xb, with a ragged front (noise: design px)"""
        x0, y0, x1, y1 = box
        X = (np.arange(x0, x1, dtype=np.float32) + 0.5) / self.s
        rev = np.clip((X - xa) / max(xb - xa, 1e-3), 0, 1)[None, :].repeat(y1 - y0, 0)
        if noise:
            rev = rev + (noise2d(y1 - y0, x1 - x0, 40 * self.s + 2, 2, self._seed()) - 0.5) * 2 * noise / max(xb - xa, 1)
        if wave:
            Y = (np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5) / self.s
            rev = rev + wave * (Y - Y.min()) / max(1.0, float(Y.max() - Y.min()))
        return np.clip(rev, 0, 1).astype(np.float32)

    def _radial_rev(self, box, origin, noise=0.08):
        x0, y0, x1, y1 = box
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        ox, oy = origin[0] * self.s, origin[1] * self.s
        d = np.hypot(xx - ox, yy - oy)
        rev = d / max(float(d.max()), 1.0)
        if noise:
            rev = rev + (noise2d(y1 - y0, x1 - x0, 30 * self.s + 2, 3, self._seed()) - 0.5) * 2 * noise
        return np.clip(rev, 0, 1).astype(np.float32)

    def _add(self, box, rgb, a, rev=None, z=10.0, when=(0.0, 0.0), follow=None, soft=0.06, pop=None, wet=0.0,
             ease='inout', name='', xa=None, xb=None, rev_noise=26.0, pre=None):
        x0, y0, x1, y1 = box
        if follow is not None:
            xa = x0 / self.s if xa is None else xa
            xb = x1 / self.s if xb is None else xb
            if rev is None or rev == 'x':
                rev = self._x_rev(box, xa, xb, rev_noise)
            follow = (follow, xa, xb)
            soft = min(soft, 14.0 / max(xb - xa, 1.0))        # a crisp wet front, not a fog bank
        if isinstance(rev, str):
            if rev == 'x': rev = self._x_rev(box, x0 / self.s, x1 / self.s, rev_noise)
            elif rev == '-x': rev = 1 - self._x_rev(box, x0 / self.s, x1 / self.s, rev_noise)
            else: raise ValueError(rev)
            soft = min(soft, 14.0 * self.s / max(x1 - x0, 1.0))
        L = _Layer(x0, y0, rgb.astype(np.float32), a.astype(np.float32),
                   None if rev is None else rev.astype(np.float32), z + len(self.layers) * 1e-4, when, follow, soft,
                   pop, wet, ease, name)
        L.pre = pre
        self.layers.append(L)
        return L

    # ------------------------------------------------------------------ materials
    def _wash_rgb(self, box, a, colour, light=0.12, edge=0.5, mottle=1.0, dark=None):
        """watercolour / gouache: mottled pigment, granulation in the tooth, darker dried edge, vertical light"""
        x0, y0, x1, y1 = box
        h, w = y1 - y0, x1 - x0
        s = self.s
        n1 = noise2d(h, w, 80 * s + 3, 3, self._seed())
        n2 = noise2d(h, w, 16 * s + 2, 2, self._seed())
        tooth = self._crop(self.tooth, box)
        rim = np.clip(a - blur(a, 3.5 * s + 0.6), 0, 1) * 2.2
        yy = np.linspace(-1, 1, h, dtype=np.float32)[:, None]
        dens = (1 + 0.16 * mottle * (n1 - 0.5) + 0.08 * mottle * (n2 - 0.5) + edge * np.clip(rim, 0, 1)
                + 0.10 * (tooth - 0.5) + light * yy)
        c = hexc(colour)
        dk = hexc(dark) if dark is not None else c * 0.8
        t = np.clip((dens - 1) * 1.6, -1, 1)[..., None]
        rgb = np.where(t > 0, c + (dk - c) * t, c + (np.minimum(c * 1.08 + 0.04, 1) - c) * (-t))
        return rgb.astype(np.float32)

    def _crop(self, arr, box):
        """crop of a full-frame array (zero outside the frame)"""
        x0, y0, x1, y1 = box
        out = np.zeros((y1 - y0, x1 - x0) + arr.shape[2:], arr.dtype)
        ax0, ay0, ax1, ay1 = max(x0, 0), max(y0, 0), min(x1, self.W), min(y1, self.H)
        if ax1 > ax0 and ay1 > ay0:
            out[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0] = arr[ay0:ay1, ax0:ax1]
        return out

    def _dashes(self, rgb, a, box, colour, n=40, length=26, width=3.2, angle=0.0, alpha=0.75, inset=6, seed=None,
                sag=0.0, top_bias=0.0):
        """coloured-pencil dashes inside a wash (the short crayon strokes on a picture-book hill).
        sag: px the middle of each dash bows (a ripple on water); top_bias > 0 crowds them toward the top"""
        x0, y0, x1, y1 = box
        s = self.s
        r = np.random.default_rng(seed if seed is not None else self._seed())
        inner = blur(a, inset * s + 0.5) > 0.97 * float(a.max())
        ys, xs = np.nonzero(inner)
        if len(xs) == 0: return rgb
        wgt = None
        if top_bias:
            v = (ys - ys.min()) / max(1.0, float(ys.max() - ys.min()))
            wgt = (1 - v) ** top_bias + 0.05; wgt = wgt / wgt.sum()
        ss = 3
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0); d = ImageDraw.Draw(im)
        for i in r.choice(len(xs), min(n, len(xs)), replace=False, p=wgt):
            cx, cy = xs[i], ys[i]
            L = length * s * r.uniform(0.6, 1.3); ang = np.deg2rad(angle + r.uniform(-5, 5))
            ca, sa = np.cos(ang), np.sin(ang)
            sg = (sag * r.uniform(0.6, 1.2) if sag else r.uniform(-1, 1)) * s
            pts = [(cx + ca * L * (t - 0.5), cy - sa * L * (t - 0.5) - sg * 4 * t * (1 - t)) for t in np.linspace(0, 1, 7)]
            d.line([(px * ss, py * ss) for px, py in pts], fill=255, width=max(1, int(width * s * ss)), joint='curve')
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        grain = noise2d(y1 - y0, x1 - x0, max(1.5, 3.5 * s), 2, int(r.integers(1 << 30)))
        m = m * np.clip(0.35 + (grain - 0.25) * 1.6, 0.15, 1) * a / max(float(a.max()), 1e-3) * alpha
        return rgb * (1 - m[..., None]) + hexc(colour) * m[..., None]

    # ------------------------------------------------------------------ scenery
    def wash(self, pts, colour, z=10.0, when=(0.0, 0.0), follow=None, reveal='x', origin=None, light=0.12, edge=0.5,
             wobble=2.2, dashes=0, dash_colour=None, dash_angle=0.0, dash_len=26, opacity=0.97, dark=None, smooth=True,
             wet=0.18, name='wash', xa=None, xb=None, pre=None):
        """a watercolour / gouache shape. reveal: 'x', '-x', 'radial' (from origin) or 'pop' (scale in)"""
        P = self._px(pts)
        if smooth and len(P) > 3: P = _closed_spline(P, 6)
        P = self._wobble(P, wobble * self.s)
        box = self._bbox(P, 6 * self.s + 3)
        a = self._poly([P], box) * opacity
        rgb = self._wash_rgb(box, a, colour, light, edge, dark=dark)
        if dashes: rgb = self._dashes(rgb, a, box, dash_colour or mix(colour, INK, 0.25), dashes, dash_len,
                                      angle=dash_angle)
        pop = None
        rev = None
        if follow is None:
            if reveal == 'radial':
                rev = self._radial_rev(box, origin if origin is not None else P.mean(0) / self.s)
            elif reveal == 'pop':
                o = origin if origin is not None else (P.mean(0) / self.s)
                pop = (o[0] * self.s, o[1] * self.s)
            elif reveal in ('x', '-x'):
                rev = reveal
        return self._add(box, rgb, a, rev, z, when, follow, 0.08, pop, wet, name=name, xa=xa, xb=xb, pre=pre)

    def ink(self, pts, width=4.0, colour=INK, z=20.0, when=(0.0, 0.0), follow=None, taper=(0.06, 0.12), tremor=0.6,
            smooth=True, name='ink', alpha=1.0, xa=None, xb=None, pre=None):
        """a fine-liner stroke drawn on along its length"""
        return self.inks([pts], width, colour, z, when, follow, taper, tremor, smooth, name, alpha, xa=xa, xb=xb,
                         pre=pre)

    def inks(self, paths, width=4.0, colour=INK, z=20.0, when=(0.0, 0.0), follow=None, taper=(0.06, 0.12),
             tremor=0.6, smooth=True, name='ink', alpha=1.0, widths=None, xa=None, xb=None, pre=None):
        """several strokes drawn one after another inside one time window"""
        strokes = []
        pens = [self._pen(p, (widths[i] if widths else width), taper, tremor, smooth) for i, p in enumerate(paths)]
        lens = [float(np.hypot(*np.diff(P, axis=0).T).sum()) + 1 for P, _ in pens]
        tot = sum(lens); acc = 0.0
        for (P, wd), L in zip(pens, lens):
            strokes.append((P, wd, acc / tot, (acc + L) / tot)); acc += L
        allP = np.vstack([P for P, _ in pens])
        box = self._bbox(allP, max(float(np.max(w)) for _, w in pens) + 4)
        a, rev = self._strokes(strokes, box)
        a = a * alpha
        tex = 0.9 + 0.1 * self._crop(self.tooth, box)              # ink catches a little tooth
        rgb = np.broadcast_to(hexc(colour), a.shape + (3,)).astype(np.float32) * (2 - tex[..., None]) ** 0.4
        return self._add(box, rgb, a * tex, None if follow is not None else rev, z, when, follow, 0.03,
                         name=name, ease='linear', xa=xa, xb=xb, pre=pre, rev_noise=4.0)

    def ground(self, pts, width=4.6, z=20.0, when=(0.0, 0.0), follow=None, ticks=True, tick_every=(70, 120),
               tick_h=15, name='ground', xa=None, xb=None, pre=None):
        """the black horizon / ground line with little 'v' grass ticks standing on it"""
        P = self._px(pts)
        P = spline(P, 10) if len(P) > 2 else P
        Pd = P / self.s
        paths = [Pd]
        if ticks:
            r = np.random.default_rng(self._seed())
            Q = _resample(Pd, 2.0)
            s_ = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
            pos = r.uniform(*tick_every) * 0.5
            while pos < s_[-1] - 20:
                i = int(np.searchsorted(s_, pos))
                x, y = Q[i]
                h = tick_h * r.uniform(0.7, 1.3); sp = h * r.uniform(0.35, 0.55)
                paths.append([(x - sp, y - h), (x, y - 1)]); paths.append([(x, y - 1), (x + sp * 0.8, y - h * 0.9)])
                pos += r.uniform(*tick_every)
        widths = [width] + [width * 0.55] * (len(paths) - 1)
        return self.inks(paths, width, INK, z, when, follow, (0.03, 0.05), 0.5, False, name, widths=widths, xa=xa,
                         xb=xb, pre=pre)

    def land(self, top, colour=GRASS, bottom=None, z=12.0, when=(0.0, 0.0), follow=None, dashes=60, dash_colour=None,
             reveal='x', name='land', wobble=1.5, left_edge=None, right_edge=None, xa=None, xb=None, pre=None):
        """a hill body: wash from a top contour (Catmull-Rom through the points) down to the bottom of the frame
        (or `bottom` y), crayon dashes inside. left_edge / right_edge: ragged cliff points, top to bottom"""
        top = [tuple(p) for p in (spline(np.asarray(top, np.float32), 8) if len(top) > 2 else top)]
        bottom = 1080 + 40 if bottom is None else bottom
        R = [tuple(p) for p in right_edge] if right_edge else [(top[-1][0], bottom)]
        Lf = [tuple(p) for p in left_edge] if left_edge else [(top[0][0], bottom)]
        poly = top + R + [(R[-1][0], bottom), (Lf[-1][0], bottom)] + Lf[::-1]
        P = self._px(poly)
        P = self._wobble(P, wobble * self.s)
        box = self._bbox(P, 4)
        a = self._poly([P], box) * 0.97
        rgb = self._wash_rgb(box, a, colour, light=0.10, edge=0.25)
        if dashes: rgb = self._dashes(rgb, a, box, dash_colour or GRASS_DARK, dashes, 44, 5.0, angle=0, alpha=0.55,
                                      inset=12)
        rev = None if follow is not None else reveal
        return self._add(box, rgb, a, rev, z, when, follow, 0.06, None, 0.15, name=name, xa=xa, xb=xb, pre=pre)

    def hill(self, top, colour=MINT, bottom=None, z=5.0, when=(0.0, 0.0), follow=None, outline='#7d8496',
             line=2.4, name='hill', xa=None, xb=None, pre=None):
        """a distant hill: a flat pale wash with a thin grey contour along its top only"""
        L = self.land(top, colour, bottom, z, when, follow, dashes=0, name=name, xa=xa, xb=xb, pre=pre)
        if outline:
            self.ink(top, line, outline, z + 0.5, when, follow, (0.02, 0.06), 0.4, True, name + '_line', xa=xa, xb=xb,
                     pre=pre)
        return L

    def tree(self, x, base, top, canopy, colour='#eaa23d', shade='#d9782f', branch=None, when=(0.0, 0.6), z=8.0,
             trunk=13.0, ticks=7):
        """a storybook oak: navy ink trunk and branches, a canopy of overlapping wash circles with a darker
        crescent and a few leaf ticks. canopy: list of (cx, cy, r). branch: list of polylines."""
        t0, t1 = when
        tm = t0 + (t1 - t0) * 0.45
        hgt = base - top
        self.inks([[(x, base), (x - 7, base - hgt * 0.35), (x + 1, base - hgt * 0.72), (x + 10, top)]] + (branch or []),
                  trunk, INK, z - 0.3, (t0, tm), taper=(0.0, 0.5), tremor=0.8,
                  widths=[trunk] + [trunk * 0.5] * len(branch or []), name='trunk')
        polys = [np.stack([cx + r * np.cos(a), cy + r * np.sin(a)], 1)
                 for cx, cy, r in canopy for a in [np.linspace(0, 2 * np.pi, 72, endpoint=False)]]
        P = [self._wobble(self._px(p), 2.2 * self.s) for p in polys]
        box = self._bbox(np.vstack(P), 8 * self.s + 3)
        a = self._poly(P, box) * 0.98
        rgb = self._wash_rgb(box, a, colour, light=0.18, edge=0.6, dark=shade)
        # darker crescent: canopy minus itself shifted toward the light
        sh = self._poly([p + np.array([-40, -46], np.float32) * self.s for p in P], box)
        cres = np.clip(a - sh, 0, 1)
        cres = blur(cres, 10 * self.s + 0.5) * a
        rgb = rgb * (1 - 0.8 * cres[..., None]) + hexc(shade) * 0.8 * cres[..., None]
        # clumps of foliage in a second and third autumn colour, dabbed on with a round brush
        r = np.random.default_rng(self._seed())
        x0, y0, x1, y1 = box
        dab = Image.new('L', ((x1 - x0) * 2, (y1 - y0) * 2), 0); dd = ImageDraw.Draw(dab)
        dab2 = Image.new('L', dab.size, 0); dd2 = ImageDraw.Draw(dab2)
        for _ in range(34):                                 # little oak leaves stamped on with a loaded brush
            c = canopy[r.integers(len(canopy))]
            ang = r.uniform(0, 2 * np.pi); dist = r.uniform(0.1, 0.82) * c[2]
            lx, ly = c[0] + np.cos(ang) * dist, c[1] + np.sin(ang) * dist
            lf, _ = oak_leaf(r.uniform(22, 34), None, 2, (lx, ly), r.uniform(0, 360), seed=int(r.integers(1 << 20)))
            q = [((u - x0 / self.s) * self.s * 2, (v - y0 / self.s) * self.s * 2) for u, v in lf]
            (dd if r.random() < 0.55 else dd2).polygon(q, fill=255)
        for im_, col, k in ((dab, '#d4592f', 0.5), (dab2, '#f8cf62', 0.55)):
            m = np.asarray(im_.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
            m = blur(m, 0.6 * self.s) * a * k * np.clip(0.6 + 0.8 * self._crop(self.tooth, box), 0, 1)
            rgb = rgb * (1 - m[..., None]) + hexc(col) * m[..., None]
        rgb = self._dashes(rgb, a, box, mix(colour, '#fff2c9', 0.5), 14, 18, 3.0, angle=35, alpha=0.5)
        cx = np.mean([c[0] for c in canopy]); cy = np.mean([c[1] for c in canopy])
        rev = self._radial_rev(box, (cx, cy + 40), 0.1)
        self._add(box, rgb, a, rev, z, (t0 + (t1 - t0) * 0.25, t1), soft=0.1, wet=0.2, name='canopy')
        if ticks:
            r = np.random.default_rng(self._seed())
            paths = []
            for _ in range(ticks):
                c = canopy[r.integers(len(canopy))]
                ang = r.uniform(0, 2 * np.pi); d = r.uniform(0.2, 0.7) * c[2]
                px, py = c[0] + np.cos(ang) * d, c[1] + np.sin(ang) * d
                paths.append([(px, py), (px + 7, py + 12)])
            self.inks(paths, 3.0, mix(shade, INK, 0.45), z + 0.2, (t1 - 0.15, t1), taper=(0.2, 0.3), name='leafticks')

    def sun(self, cx, cy, r, when=(0.0, 1.0), rays=12, z=4.0, colour=SUN, ray_colour=SUN_RAY):
        """a yellow wash disc that pops in, then crayon rays drawn round one by one"""
        t0, t1 = when
        tm = t0 + (t1 - t0) * 0.4
        ang = np.linspace(0, 2 * np.pi, 80, endpoint=False)
        P = self._wobble(self._px(np.stack([cx + r * np.cos(ang), cy + r * np.sin(ang)], 1)), 1.4 * self.s)
        pad = r * 0.5 * self.s + 6
        box = self._bbox(P, pad)
        a = self._poly([P], box)
        x0, y0, x1, y1 = box
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.hypot(xx - (cx - r * 0.25) * self.s, yy - (cy - r * 0.3) * self.s) / (r * self.s * 1.25)
        c0, c1 = hexc('#fbe48f'), hexc('#efa93a')
        g = np.clip(d, 0, 1)[..., None] ** 1.6
        rgb = c0 * (1 - g) + c1 * g
        rgb = rgb * (1 + 0.06 * (noise2d(y1 - y0, x1 - x0, 14 * self.s + 2, 2, self._seed()) - 0.5)[..., None])
        halo = np.exp(-np.clip(np.hypot(xx - cx * self.s, yy - cy * self.s) / (r * self.s) - 1, 0, None) * 3.2) * 0.22
        aa = np.maximum(a, halo * (1 - a))
        rgb = np.where(a[..., None] > 0.02, rgb, hexc('#f8d77a'))
        self._add(box, rgb, aa, None, z, (t0, tm), pop=(cx * self.s, cy * self.s), ease='linear', name='sun')
        r_ = np.random.default_rng(self._seed())
        paths, w = [], []
        for i in range(rays):
            a_ = -np.pi / 2 + 2 * np.pi * i / rays + r_.uniform(-0.06, 0.06)
            r0 = r * 1.32; r1 = r * (1.72 if i % 2 == 0 else 1.55)
            paths.append([(cx + r0 * np.cos(a_), cy + r0 * np.sin(a_)), (cx + r1 * np.cos(a_), cy + r1 * np.sin(a_))])
            w.append(7.5)
        L = self.inks(paths, 7.5, ray_colour, z + 0.1, (tm, t1), taper=(0.25, 0.35), tremor=0.3, smooth=False,
                      name='rays', widths=w)
        L.rgb = self._crayon_tex(L)
        return L

    def _crayon_tex(self, L):
        box = (L.x0, L.y0, L.x0 + L.a.shape[1], L.y0 + L.a.shape[0])
        tooth = self._crop(self.tooth, box)
        L.a = L.a * np.clip(0.35 + (tooth - 0.2) * 1.6, 0.25, 1)
        return L.rgb

    def cloud(self, cx, cy, w, when=(0.0, 0.4), z=6.0, colour=WHITE, shadow='#bcc0e6'):
        """thick white paint: three or four bumps on a flat-ish bottom, a lavender shadow under the right side"""
        r = np.random.default_rng(self._seed())
        bumps = [(-0.30, 0.05, 0.26), (-0.05, -0.12, 0.34), (0.24, -0.02, 0.27), (0.40, 0.08, 0.17), (-0.45, 0.12, 0.15)]
        polys = []
        for bx, by, br in bumps:
            br *= r.uniform(0.92, 1.08)
            a = np.linspace(0, 2 * np.pi, 60, endpoint=False)
            polys.append(np.stack([cx + bx * w + br * w * np.cos(a), cy + by * w + br * w * 0.9 * np.sin(a)], 1))
        polys.append(np.array([(cx - 0.52 * w, cy + 0.08 * w), (cx + 0.52 * w, cy + 0.08 * w),
                               (cx + 0.5 * w, cy + 0.2 * w), (cx - 0.5 * w, cy + 0.2 * w)]))
        P = [self._wobble(self._px(p), 1.0 * self.s) for p in polys]
        off = np.array([7, 9], np.float32) * self.s
        box = self._bbox(np.vstack(P + [p + off for p in P]), 6 * self.s + 4)
        a = self._poly(P, box)
        a = np.clip(blur(a, 0.9 * self.s), 0, 1)
        sh = self._poly([p + off for p in P], box)
        x0, y0, x1, y1 = box
        yy = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None]
        streak = noise2d(y1 - y0, x1 - x0, 10 * self.s + 2, 2, self._seed())
        streak = blur(streak, 0.5) if self.s > 0.6 else streak
        base = hexc(colour)
        inner = np.clip(a - np.roll(np.roll(a, int(-8 * self.s), 0), int(-6 * self.s), 1), 0, 1)
        shade = np.clip(0.06 + 0.10 * yy + 0.35 * blur(inner, 4 * self.s + 0.5), 0, 0.5)
        body = base * (1 - shade[..., None]) + hexc('#d7dbf2') * shade[..., None]
        body = body * (0.97 + 0.06 * streak[..., None])
        shc = hexc(shadow)
        rgb = np.where(a[..., None] > 0.01, body, shc)
        alpha = np.maximum(a, sh * 0.85)
        rgb = (body * a[..., None] + shc * (alpha - a)[..., None]) / np.maximum(alpha, 1e-4)[..., None]
        return self._add(box, rgb, alpha, None, z, when, pop=(cx * self.s, (cy + 0.15 * w) * self.s), name='cloud')

    def shape(self, polys, fill, outline=INK, line=2.6, z=30.0, when=(0.0, 0.3), pop=None, reveal=None, origin=None,
              light=0.08, name='shape', dark=None, wobble=0.8):
        """filled wash shapes with a thin ink outline (petals, leaves, mushrooms): pops in from `pop` (design xy)"""
        P = [self._wobble(self._px(p), wobble * self.s) for p in polys]
        lw = line * self.s
        box = self._bbox(np.vstack(P), lw + 4)
        a = self._poly(P, box)
        rgb = self._wash_rgb(box, a, fill, light=light, edge=0.35, dark=dark)
        if outline and line > 0:
            x0, y0, x1, y1 = box
            ss = 3
            im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0); d = ImageDraw.Draw(im)
            for p in P:
                q = [((x - x0) * ss, (y - y0) * ss) for x, y in np.vstack([p, p[:1]])]
                d.line(q, fill=255, width=max(1, int(round(lw * ss))), joint='curve')
            o = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
            rgb = rgb * (1 - o[..., None]) + hexc(outline) * o[..., None]
            a = np.maximum(a, o)
        popxy = None if pop is None else (pop[0] * self.s, pop[1] * self.s)
        rev = None
        if reveal == 'radial': rev = self._radial_rev(box, origin)
        return self._add(box, rgb, a, rev, z, when, None, 0.08, popxy, 0.0, name=name)

    def flower(self, x, y, h=70, kind='aster', colour='#b48ae0', centre='#f4c242', when=(0.0, 0.5), z=30.0, lean=0.0,
               petals=None):
        """stem drawn up from the ground, then the head pops open with an overshoot"""
        t0, t1 = when
        tm = t0 + (t1 - t0) * 0.45
        hx, hy = x + lean * h, y - h
        self.ink([(x, y), (x + lean * h * 0.3 + 3, y - h * 0.5), (hx, hy)], 3.2, '#2f5a3c', z, (t0, tm), taper=(0, 0.2),
                 name='stem')
        lf, _ = oak_leaf(h * 0.32, h * 0.13, 1, (x + 1, y - h * 0.35), 35, seed=self._seed())
        self.shape([lf], '#7cc36a', INK, 2.0, z - 0.1, (tm - 0.05, tm + 0.15), pop=(x, y - h * 0.35), name='stemleaf')
        rr = h * 0.17
        polys = []
        n = petals or (12 if kind == 'aster' else 8)
        for i in range(n):
            a = 2 * np.pi * i / n
            pl = rr * (1.0 if kind == 'aster' else 1.1); pw = rr * (0.32 if kind == 'aster' else 0.55)
            t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
            ex = pl * 0.55 + pl * 0.55 * np.cos(t); ey = pw * 0.5 * np.sin(t)
            polys.append(np.stack([hx + ex * np.cos(a) - ey * np.sin(a), hy + ex * np.sin(a) + ey * np.cos(a)], 1))
        self.shape(polys, colour, INK, 1.8, z + 0.1, (tm, t1), pop=(hx, hy), name='petals')
        t = np.linspace(0, 2 * np.pi, 30, endpoint=False)
        self.shape([np.stack([hx + rr * 0.42 * np.cos(t), hy + rr * 0.42 * np.sin(t)], 1)], centre, INK, 1.8, z + 0.2,
                   (tm + 0.04, t1), pop=(hx, hy), name='centre')

    def tuft(self, x, y, h=26, when=(0.0, 0.25), z=29.0, colour='#3e7a4a'):
        """a little fan of grass blades flicked up from the ground"""
        r = np.random.default_rng(self._seed())
        paths = []
        for k in range(r.integers(3, 6)):
            a = np.deg2rad(r.uniform(-35, 35)); L = h * r.uniform(0.6, 1.1)
            paths.append([(x + k * 2 - 4, y), (x + np.sin(a) * L * 0.5, y - L * 0.55), (x + np.sin(a) * L, y - L)])
        return self.inks(paths, 3.2, colour, z, when, taper=(0.0, 0.6), name='tuft')

    def cattail(self, x, y, h=150, when=(0.0, 0.5), z=31.0, lean=0.08):
        t0, t1 = when
        tm = t0 + (t1 - t0) * 0.55
        top = (x + lean * h, y - h)
        self.ink([(x, y), (x + lean * h * 0.4, y - h * 0.5), top], 3.4, '#2f5a3c', z, (t0, tm), taper=(0, 0.15))
        self.ink([(x - 2, y), (x - 26, y - h * 0.45), (x - 46, y - h * 0.62)], 5.0, '#5f9d58', z - 0.1, (t0, tm),
                 taper=(0, 0.8), name='blade')
        hx, hy = x + lean * h * 0.86, y - h * 0.82
        t = np.linspace(0, 2 * np.pi, 40, endpoint=False)
        ang = np.arctan2(-h, lean * h)
        ca, sa = np.cos(ang), np.sin(ang)
        ex, ey = 0.11 * h * np.cos(t), 0.035 * h * np.sin(t)
        P = np.stack([hx + ex * ca - ey * sa, hy + ex * sa + ey * ca], 1)
        self.shape([P], '#7a4a2c', INK, 2.0, z + 0.1, (tm, t1), pop=(hx, hy), dark='#4c2b19', name='cattail')

    def leaf_on_ground(self, x, y, size=26, colour='#d9603a', angle=None, when=(0.0, 0.25), z=29.0):
        r = np.random.default_rng(self._seed())
        ang = angle if angle is not None else r.uniform(-30, 30)
        out, mid = oak_leaf(size, size * 0.45, 2, (0, 0), ang, seed=self._seed())
        out = out * np.array([1.0, 0.55]) + np.array([x, y]); mid = mid * np.array([1.0, 0.55]) + np.array([x, y])
        L = self.shape([out], colour, INK, 1.6, z, when, pop=(x, y), name='fallen')
        return L

    def mound(self, x, y, w=120, h=34, when=(0.0, 0.4), z=55.0, colour='#a46a3e'):
        """a heap of fresh soil pushed up around a hole (drawn over the character, so it can bury it)"""
        t = np.linspace(0, np.pi, 40)
        top = np.stack([x - w / 2 + w * (1 - np.cos(t)) / 2, y - h * np.sin(t) ** 0.8 - 2], 1)
        P = np.vstack([top, [(x + w / 2 + 6, y + 6), (x - w / 2 - 6, y + 6)]])
        L = self.shape([P], colour, INK, 2.4, z, when, pop=(x, y + 4), dark='#6d4224', name='mound')
        # soil crumbs
        box = (L.x0, L.y0, L.x0 + L.a.shape[1], L.y0 + L.a.shape[0])
        r = np.random.default_rng(self._seed())
        im = Image.new('L', (L.a.shape[1] * 3, L.a.shape[0] * 3), 0); d = ImageDraw.Draw(im)
        for _ in range(16):
            px = (x + r.uniform(-0.4, 0.4) * w) * self.s; py = (y - r.uniform(0.1, 0.7) * h) * self.s
            rr = r.uniform(1.2, 2.6) * self.s * 3
            d.ellipse(((px - box[0]) * 3 - rr, (py - box[1]) * 3 - rr, (px - box[0]) * 3 + rr, (py - box[1]) * 3 + rr),
                      fill=255)
        m = np.asarray(im.resize((L.a.shape[1], L.a.shape[0]), Image.BOX), np.float32)[..., None] / 255
        L.rgb = L.rgb * (1 - 0.8 * m) + hexc('#4a2c18') * 0.8 * m
        return L

    def water(self, x0, x1, y, depth=260, when=(0.0, 1.0), z=9.0, follow=None, colour=WATER):
        """a stream between two banks: blue wash, darker with depth, white glints and ink-blue ripple dashes"""
        top = [(x0 + (x1 - x0) * u, y + 3 * np.sin(u * 9)) for u in np.linspace(0, 1, 16)]
        poly = top + [(x1, y + depth), (x0, y + depth)]
        P = self._px(poly)
        box = self._bbox(P, 4)
        a = self._poly([P], box) * 0.96
        rgb = self._wash_rgb(box, a, colour, light=0.35, edge=0.2, dark='#5c9fc4')
        r = np.random.default_rng(self._seed())
        rgb = self._dashes(rgb, a, box, '#f7fcff', 16, 80, 5.0, 0, 0.9, inset=14, seed=self._seed(), sag=-3,
                           top_bias=2.0)
        rgb = self._dashes(rgb, a, box, '#4a82ad', 9, 60, 3.6, 0, 0.6, inset=14, seed=self._seed(), sag=5,
                           top_bias=1.0)
        L = self._add(box, rgb, a, None if follow is not None else 'x', z, when, follow, 0.08, None, 0.12,
                      name='water')
        self.ink(top, 2.4, '#3d6f94', z + 0.2, when, follow, (0.02, 0.04), 0.3, True, 'waterline')
        return L

    def write(self, text, x, y, size=130, when=(0.0, 1.2), colour=INK, font='script', z=80.0, anchor='mm',
              underline=None, weight=1.6):
        """a handwritten line that writes itself stroke by stroke (see `_write_order`). weight: extra pen width in
        design px (keeps the hairlines of a script font alive in a small GIF)"""
        ss = 2
        s = self.s
        ft = load_font(font, size * s * ss)
        W2, H2 = self.W * ss, self.H * ss
        im = Image.new('L', (W2, H2), 0)
        ImageDraw.Draw(im).text((x * s * ss, y * s * ss), text, font=ft, fill=255, anchor=anchor,
                                stroke_width=int(round(weight * 0.5 * s * ss)), stroke_fill=255)
        m2 = np.asarray(im, np.float32) / 255
        ys, xs = np.nonzero(m2 > 0.02)
        if len(xs) == 0: return None
        bx0, by0 = max(0, xs.min() - 6), max(0, ys.min() - 6)
        bx1, by1 = min(W2, xs.max() + 7), min(H2, ys.max() + 7)
        bx0 -= bx0 % ss; by0 -= by0 % ss; bx1 += (-bx1) % ss; by1 += (-by1) % ss
        sub = m2[by0:by1, bx0:bx1]
        T = self._write_order(sub > 0.5, sub > 0.02)
        T = np.where(sub > 0.02, T, 9.0)
        h, w = sub.shape[0] // ss, sub.shape[1] // ss
        a = sub.reshape(h, ss, w, ss).mean((1, 3))
        rev = T.reshape(h, ss, w, ss).min((1, 3))
        rev = np.where(rev > 1.5, 1.0, rev)
        box = (bx0 // ss, by0 // ss, bx0 // ss + w, by0 // ss + h)
        tooth = self._crop(self.tooth, box)
        a = a * (0.9 + 0.1 * tooth)
        rgb = np.broadcast_to(hexc(colour), a.shape + (3,)).astype(np.float32).copy()
        L = self._add(box, rgb, a, rev, z, when, None, 0.012, ease='linear', name='write')
        if underline:
            (u0, u1), uy = underline
            t0, t1 = when
            self.ink([(u0, uy + 6), ((u0 + u1) / 2, uy - 4), (u1, uy + 2)], 3.4, colour, z, (t1, t1 + 0.35),
                     taper=(0.1, 0.5), name='underline')
        return L

    @staticmethod
    def _thin(m):
        """Zhang-Suen thinning of a boolean mask -> one-pixel skeleton"""
        img = np.pad(m.astype(np.uint8), 1)
        while True:
            changed = False
            for step in (0, 1):
                P = img
                p2, p3, p4 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:]
                p5, p6, p7 = P[2:, 2:], P[2:, 1:-1], P[2:, :-2]
                p8, p9 = P[1:-1, :-2], P[:-2, :-2]
                c = P[1:-1, 1:-1]
                B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9
                seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
                A = sum(((seq[i] == 0) & (seq[i + 1] == 1)).astype(np.uint8) for i in range(8))
                if step == 0: k1, k2 = p2 * p4 * p6, p4 * p6 * p8
                else: k1, k2 = p2 * p4 * p8, p2 * p6 * p8
                rm = (c == 1) & (B >= 2) & (B <= 6) & (A == 1) & (k1 == 0) & (k2 == 0)
                if rm.any():
                    c[rm] = 0; changed = True
            if not changed: break
        return img[1:-1, 1:-1].astype(bool)

    def _write_order(self, m, fill=None):
        """time 0..1 at which a pen reaches each inked pixel: walk the skeleton like a hand would"""
        sk = self._thin(m)
        fill = m if fill is None else fill
        ys, xs = np.nonzero(sk)
        n = len(xs)
        if n == 0: return np.zeros(m.shape, np.float32)
        idx = -np.ones(m.shape, np.int64); idx[ys, xs] = np.arange(n)
        H, W = m.shape
        nb = []
        for i in range(n):
            y, x = ys[i], xs[i]
            l = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0: continue
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and idx[yy, xx] >= 0: l.append(int(idx[yy, xx]))
            nb.append(l)
        comp = -np.ones(n, np.int64); comps = []
        for i in range(n):
            if comp[i] >= 0: continue
            st = [i]; comp[i] = len(comps); mem = []
            while st:
                j = st.pop(); mem.append(j)
                for k in nb[j]:
                    if comp[k] < 0: comp[k] = len(comps); st.append(k)
            comps.append(mem)
        # small marks (i-dots, commas, cross-bars) are written right after the stroke they sit on
        comps.sort(key=lambda c: xs[c].min() + (0.6 * (xs[c].max() - xs[c].min()) if len(c) < 60 else 0))
        T = np.full(n, -1.0)
        seen = np.zeros(n, bool)
        clock = 0.0
        for c in comps:
            ends = [j for j in c if len(nb[j]) == 1]
            pool = ends if ends else c
            start = min(pool, key=lambda j: (xs[j] + 0.35 * ys[j], ys[j]))      # de-slanted left-most end
            cur = start; seen[cur] = True; T[cur] = clock; prev = None; stack = []
            while True:
                cand = [k for k in nb[cur] if not seen[k]]
                if cand:
                    if len(cand) > 1: stack.append(cur)
                    if prev is None:
                        nxt = min(cand, key=lambda k: (ys[k] - ys[cur]) + 0.5 * (xs[k] - xs[cur]))
                    else:
                        dv = (xs[cur] - xs[prev], ys[cur] - ys[prev])
                        nxt = max(cand, key=lambda k: (xs[k] - xs[cur]) * dv[0] + (ys[k] - ys[cur]) * dv[1])
                    step = 1.414 if (xs[nxt] != xs[cur] and ys[nxt] != ys[cur]) else 1.0
                    prev, cur = cur, nxt
                    seen[cur] = True; clock += step; T[cur] = clock
                else:
                    while stack and not any(not seen[k] for k in nb[stack[-1]]): stack.pop()
                    if not stack: break
                    cur = stack.pop(); prev = None; clock += 2.0
            clock += 12.0
        T /= max(clock, 1.0)
        # spread the skeleton times over the whole stroke width (nearest skeleton pixel)
        Tm = np.full(m.shape, np.inf, np.float32); Tm[ys, xs] = T
        for _ in range(int(max(m.shape) * 0.06) + 4):
            P = np.pad(Tm, 1, constant_values=np.inf)
            nbmin = np.minimum.reduce([P[1 + dy:1 + dy + m.shape[0], 1 + dx:1 + dx + m.shape[1]]
                                       for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
            new = np.where(fill & ~np.isfinite(Tm), nbmin, Tm)
            if np.array_equal(np.isfinite(new), np.isfinite(Tm)): Tm = new; break
            Tm = new
        Tm[~np.isfinite(Tm)] = 1.0
        return Tm

    # ------------------------------------------------------------------ props (moving sprites: the leaf boat)
    def sprite(self, polys, fill, outline=INK, line=2.4, veins=None, dark=None):
        """pre-paint a small prop at design scale around its own origin (0, 0); returns a sprite dict"""
        allp = np.vstack(polys)
        pad = 6
        ox, oy = allp[:, 0].min() - pad, allp[:, 1].min() - pad
        w = int(np.ceil((allp[:, 0].max() - ox + pad) * self.s)) + 2
        h = int(np.ceil((allp[:, 1].max() - oy + pad) * self.s)) + 2
        P = [(np.asarray(p, np.float32) - [ox, oy]) * self.s for p in polys]
        box = (0, 0, w, h)
        a = self._poly(P, box)
        rgb = self._wash_rgb(box, a, fill, light=0.1, edge=0.45, dark=dark)
        ss = 3
        im = Image.new('L', (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
        for p in P:
            d.line([(x * ss, y * ss) for x, y in np.vstack([p, p[:1]])], fill=255, width=max(1, int(line * self.s * ss)),
                   joint='curve')
        for v in (veins or []):
            q = (np.asarray(v, np.float32) - [ox, oy]) * self.s
            d.line([(x * ss, y * ss) for x, y in q], fill=255, width=max(1, int(line * 0.8 * self.s * ss)), joint='curve')
        o = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        rgb = rgb * (1 - o[..., None]) + hexc(outline) * o[..., None]
        a = np.maximum(a, o)
        return dict(rgb=rgb.astype(np.float32), a=a.astype(np.float32), origin=(-ox * self.s, -oy * self.s))

    def prop(self, sprite, t0, t1, fn, z=45.0):
        """a moving prop: fn(u, t) -> dict(x, y, rot=0, sx=1, sy=1, alpha=1) in design units, or None"""
        self.props.append((sprite, t0, t1, fn, z))

    def _prop_pose(self, t0, t1, fn, t):
        if t < t0: return None
        u = 1.0 if t1 <= t0 else min(1.0, (t - t0) / (t1 - t0))
        return fn(u, t)

    def _affine(self, cv, rgb, a, origin, M, pos, alpha=1.0):
        """draw a pre-painted sprite through a 2x2 matrix M (sprite px -> canvas px) at canvas pixel pos"""
        h, w = a.shape
        ox, oy = origin
        corners = np.array([[-ox, -oy], [w - ox, -oy], [w - ox, h - oy], [-ox, h - oy]], np.float32) @ M.T + pos
        x0, y0 = int(np.floor(corners[:, 0].min())) - 1, int(np.floor(corners[:, 1].min())) - 1
        x1, y1 = int(np.ceil(corners[:, 0].max())) + 2, int(np.ceil(corners[:, 1].max())) + 2
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, self.W), min(y1, self.H)
        if x1 <= x0 or y1 <= y0: return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        Mi = np.linalg.inv(M)
        dx, dy = xx + 0.5 - pos[0], yy + 0.5 - pos[1]
        sx = Mi[0, 0] * dx + Mi[0, 1] * dy + ox - 0.5
        sy = Mi[1, 0] * dx + Mi[1, 1] * dy + oy - 0.5
        i0 = np.floor(sx).astype(np.int64); j0 = np.floor(sy).astype(np.int64)
        fx, fy = (sx - i0).astype(np.float32), (sy - j0).astype(np.float32)
        pm = np.concatenate([rgb * a[..., None], a[..., None]], -1)
        pm = np.pad(pm, ((1, 1), (1, 1), (0, 0)))
        i0c = np.clip(i0 + 1, 0, w + 1); i1c = np.clip(i0 + 2, 0, w + 1)
        j0c = np.clip(j0 + 1, 0, h + 1); j1c = np.clip(j0 + 2, 0, h + 1)
        out = (pm[j0c, i0c] * ((1 - fx) * (1 - fy))[..., None] + pm[j0c, i1c] * (fx * (1 - fy))[..., None]
               + pm[j1c, i0c] * ((1 - fx) * fy)[..., None] + pm[j1c, i1c] * (fx * fy)[..., None])
        out *= alpha
        sl = cv[y0:y1, x0:x1]
        sl *= (1 - out[..., 3:4]); sl += out[..., :3]

    def _draw_prop(self, cv, sprite, p):
        if p is None: return
        rot = np.deg2rad(p.get('rot', 0.0))
        c, s_ = np.cos(rot), np.sin(rot)
        R = np.array([[c, s_], [-s_, c]], np.float32)
        S = np.diag([p.get('sx', 1.0), p.get('sy', 1.0)]).astype(np.float32)
        M = R @ S
        self._affine(cv, sprite['rgb'], sprite['a'], sprite['origin'], M,
                     np.array([p['x'] * self.s, p['y'] * self.s], np.float32), p.get('alpha', 1.0))

    # ------------------------------------------------------------------ the character
    def act(self, t0, t1, fn):
        """a piece of choreography: fn(u, t) -> pose dict (see `_actor`) or None (hidden)"""
        self.acts.append((t0, t1, fn))
        self._lead = None

    def pose(self, t):
        best = None
        for t0, t1, fn in self.acts:
            if t0 <= t: best = (t0, t1, fn)
        if best is None: return None
        t0, t1, fn = best
        u = 1.0 if t1 <= t0 else min(1.0, (t - t0) / (t1 - t0))
        return fn(u, t)

    def lead_x(self, t):
        """the furthest x (design) the character has reached by time t"""
        if self._lead is None:
            ts = np.arange(0, max(a[1] for a in self.acts) + 1, 0.01) if self.acts else np.zeros(1)
            xs = []
            for tt in ts:
                p = self.pose(tt)
                xs.append(p['x'] if p and p.get('lead', True) else -1e9)
            self._lead = (ts, np.maximum.accumulate(np.array(xs)))
        ts, xm = self._lead
        return float(np.interp(t, ts, xm))

    _OUT = None

    def _outline_local(self):
        if Storybook._OUT is None:
            t = np.linspace(0, 2 * np.pi, 90, endpoint=False)
            nut = []
            for a in t:
                x, y = np.cos(a), np.sin(a)
                y = y * (1.12 if y >= 0 else 0.95)
                x = x * (1 - 0.17 * max(0.0, y / 1.12))
                nut.append((x, y))
            cap = [(1.13 * np.cos(a), -0.5 + 0.68 * np.sin(a)) for a in t if np.sin(a) < -0.2]
            Storybook._OUT = np.array(nut + cap + [(0.0, 1.2), (0.16, -1.48)], np.float32)
        return Storybook._OUT

    def _matrix(self, rot=0.0, k=1.0, axis=90.0, scale=1.0, flip=False):
        u = self.actor_size * self.s * scale
        ph = np.deg2rad(axis)
        av = np.array([np.cos(ph), -np.sin(ph)], np.float32)
        S = k * np.outer(av, av) + k ** -0.5 * (np.eye(2, dtype=np.float32) - np.outer(av, av))
        r = np.deg2rad(rot)
        c, s_ = np.cos(r), np.sin(r)
        R = np.array([[c, s_], [-s_, c]], np.float32)
        F = np.diag([-1.0, 1.0]).astype(np.float32) if flip else np.eye(2, dtype=np.float32)
        return (u * S @ R @ F).astype(np.float32)

    def rest(self, gx, gy, rot=0.0, k=1.0, axis=90.0, scale=1.0, normal=(0.0, -1.0)):
        """centre (design) that puts the character's lowest point exactly on the ground point (gx, gy)"""
        M = self._matrix(rot, k, axis, scale) / self.s
        n = np.asarray(normal, np.float32); n /= np.linalg.norm(n)
        P = self._outline_local() @ M.T
        d = float((-(P @ n)).max())
        return gx + n[0] * d, gy + n[1] * d

    def anchor(self, px, py, local=(0.16, -1.46), rot=0.0, k=1.0, axis=90.0, scale=1.0):
        """centre that puts the character's local point (default: the tip of the stem) at design point (px, py)"""
        M = self._matrix(rot, k, axis, scale) / self.s
        o = M @ np.asarray(local, np.float32)
        return px - float(o[0]), py - float(o[1])

    def when_at(self, x, lead=0.0, dur=0.35, delay=0.0):
        """time window that starts when the character (plus `lead`) first reaches design x"""
        if self.acts: self.lead_x(0)
        ts, xm = self._lead
        i = int(np.searchsorted(xm, x - lead))
        t = float(ts[min(i, len(ts) - 1)]) + delay
        return (t, t + dur)

    def _actor(self, cv, pose, alpha=1.0):
        """render the acorn at a pose. pose keys: x, y (centre of the nut, design px), rot (deg, ccw), k (stretch
        along `axis`, <1 squash), axis (deg), scale, eyes (0 closed .. 1 open), lid ('blink' | 'sleep' | 'happy'),
        look (dx, dy in -1..1), brow (None | 'determined' | 'up' | 'worried'), mouth (None | 'smile' | 'grin' |
        'o' | 'flat'), blush, clip (ground y in design px: hide everything below), only ('cap')"""
        s = self.s
        M = self._matrix(pose.get('rot', 0.0), pose.get('k', 1.0), pose.get('axis', 90.0), pose.get('scale', 1.0))
        if abs(np.linalg.det(M)) < 1e-6: return
        Mi = np.linalg.inv(M)
        cx, cy = pose['x'] * s, pose['y'] * s
        corners = np.array([[-1.3, -1.65], [1.3, -1.65], [1.3, 1.4], [-1.3, 1.4]], np.float32) @ M.T + [cx, cy]
        x0, y0 = max(int(corners[:, 0].min()) - 2, 0), max(int(corners[:, 1].min()) - 2, 0)
        x1, y1 = min(int(corners[:, 0].max()) + 3, self.W), min(int(corners[:, 1].max()) + 3, self.H)
        if x1 <= x0 or y1 <= y0: return
        ss = 2
        yy, xx = np.mgrid[0:(y1 - y0) * ss, 0:(x1 - x0) * ss].astype(np.float32)
        px = x0 + (xx + 0.5) / ss - cx; py = y0 + (yy + 0.5) / ss - cy
        X = Mi[0, 0] * px + Mi[0, 1] * py
        Y = Mi[1, 0] * px + Mi[1, 1] * py
        sv = np.linalg.svd(M, compute_uv=False)
        pu = 1.0 / (float(sv.min()) * ss)                         # local units per (super)pixel
        cov = lambda d: np.clip(0.5 - d / pu, 0, 1)
        rot = np.deg2rad(pose.get('rot', 0.0))
        cr, sr = np.cos(rot), np.sin(rot)
        Lx, Ly, Lz = self.light
        Hn = self.light + np.array([0, 0, 1], np.float32); Hn /= np.linalg.norm(Hn)
        rgb = np.zeros(X.shape + (3,), np.float32); A = np.zeros(X.shape, np.float32)

        def over(c, col):
            nonlocal rgb, A
            c = c[..., None] if c.ndim == 2 else c
            rgb = rgb * (1 - c) + col * c
            A[:] = A + c[..., 0] * (1 - A)

        def lit(nx, ny, nz):
            wx, wy = cr * nx + sr * ny, -sr * nx + cr * ny
            diff = np.clip(wx * Lx + wy * Ly + nz * Lz, 0, 1)
            spec = np.clip(wx * Hn[0] + wy * Hn[1] + nz * Hn[2], 0, 1) ** 24
            return diff, spec, wy

        only = pose.get('only')
        if only != 'cap':
            yb = np.where(Y >= 0, Y / 1.12, Y / 0.95)
            xs = X / (1 - 0.17 * np.clip(Y / 1.12, 0, 1))
            r = np.hypot(xs, yb)
            c_nut = cov(r - 1)
            z = np.sqrt(np.clip(1 - r * r, 0, 1))
            nn = np.sqrt(xs * xs + yb * yb + z * z) + 1e-6
            diff, spec, wy = lit(xs / nn, yb / nn, z / nn)
            base = hexc(pose.get('body', NUT))
            col = base * (0.55 + 0.58 * diff)[..., None]
            col = col + hexc('#f0b070') * (0.14 * np.clip(wy, 0, 1) * (1 - diff))[..., None]   # warm bounce
            col = col * (1 - 0.16 * smoothstep(0.8, 1.0, r))[..., None]
            stripes = smoothstep(0.82, 1.0, np.cos(xs * np.pi * 3.3)) * (1 - smoothstep(0.6, 0.95, r)) * (Y > -0.1)
            col = col * (1 + 0.06 * stripes)[..., None]
            col = col * (1 - 0.6 * spec[..., None]) + 0.6 * spec[..., None]
            over(c_nut, col)
            over(cov(np.hypot(X, Y - 1.13) - 0.09) * c_nut, hexc('#6d4224'))
            self._face(pose, X, Y, cov, over, c_nut)
        # cap
        rc = np.hypot(X / 1.13, (Y + 0.5) / 0.68)
        rim = -0.28 + 0.15 * (1 - np.clip(X / 1.13, -1, 1) ** 2)
        c_cap = cov(rc - 1) * cov(Y - rim)
        z = np.sqrt(np.clip(1 - rc * rc, 0, 1))
        nx_, ny_ = X / 1.13, (Y + 0.5) / 0.68
        nn = np.sqrt(nx_ ** 2 + ny_ ** 2 + z ** 2) + 1e-6
        diff, spec, wy = lit(nx_ / nn, ny_ / nn, z / nn)
        col = hexc(pose.get('cap', CAP)) * (0.55 + 0.6 * diff)[..., None]
        g1, g2 = (X + Y) * 4.4, (X - Y) * 4.4
        dl = np.minimum(np.abs(g1 - np.round(g1)), np.abs(g2 - np.round(g2))) / 4.4
        c_line = cov(dl - 0.032) * cov(Y - (rim - 0.1))
        col = col * (1 - 0.45 * c_line[..., None]) + hexc(CAP_LINE) * 0.45 * c_line[..., None]
        band = cov(-(Y - (rim - 0.11)))
        col = col * (1 - 0.5 * band[..., None]) + (hexc('#b07a4a') * (0.7 + 0.4 * diff)[..., None]) * 0.5 * band[..., None]
        col = col * (1 - 0.35 * spec[..., None]) + 0.35 * spec[..., None]
        over(c_cap, col)
        # stem
        ax_, ay_, bx_, by_ = 0.03, -1.12, 0.16, -1.46
        t = np.clip(((X - ax_) * (bx_ - ax_) + (Y - ay_) * (by_ - ay_)) / ((bx_ - ax_) ** 2 + (by_ - ay_) ** 2), 0, 1)
        d = np.hypot(X - ax_ - t * (bx_ - ax_), Y - ay_ - t * (by_ - ay_))
        over(cov(d - 0.085), hexc('#5e3820') * (1 + 0.25 * (t < 0.35))[..., None])
        if pose.get('brow') and only != 'cap': self._brows(pose, X, Y, cov, over)
        # downsample, clip under the ground
        h, w = y1 - y0, x1 - x0
        prem = (rgb * A[..., None]).reshape(h, ss, w, ss, 3).mean((1, 3))
        A = A.reshape(h, ss, w, ss).mean((1, 3))
        if pose.get('clip') is not None:
            gy = pose['clip'] * s
            rows = np.arange(y0, y1, dtype=np.float32) + 0.5
            keep = np.clip(gy - rows, 0, 1)[:, None]
            prem *= keep[..., None]; A = A * keep
        A = A * alpha; prem = prem * alpha
        sl = cv[y0:y1, x0:x1]
        sl *= (1 - A[..., None]); sl += prem

    def _face(self, pose, X, Y, cov, over, c_nut):
        if pose.get('blush', True):
            for sx in (-1, 1):
                d = np.hypot((X - sx * 0.6) / 0.17, (Y - 0.56) / 0.09) - 1
                over(np.clip(0.5 - d * 2.5, 0, 1) * 0.35 * c_nut, hexc('#e9776a'))
        o = float(pose.get('eyes', 1.0))
        lx, ly = pose.get('look', (0.0, 0.0))
        lid = pose.get('lid', 'blink')
        for sx in (-1, 1):
            ex, ey = sx * 0.36, 0.30
            if o > 0.22:
                ry = 0.255 * o
                d = np.hypot((X - ex) / 0.19, (Y - ey) / ry) - 1
                ce = cov(d * 0.19) * c_nut
                white = np.ones(X.shape + (3,), np.float32) * hexc('#fffdf8')
                white = white * (1 - 0.12 * np.clip((Y - ey) / ry, 0, 1))[..., None]
                over(ce, white)
                pxc, pyc = ex + lx * 0.075, ey + ly * 0.09 * o
                dp = np.hypot(X - pxc, (Y - pyc) / max(min(1.0, o * 1.1), 0.3)) - 0.118
                over(cov(dp) * ce, hexc('#161a26'))
                dh = np.hypot(X - (pxc - 0.04), Y - (pyc - 0.05)) - 0.042
                over(cov(dh) * ce, hexc('#ffffff'))
            else:
                w = 0.17
                tt = np.clip((X - ex) / w, -1, 1)
                if lid == 'sleep': yc = ey + 0.05 * (1 - tt * tt)
                elif lid == 'happy': yc = ey + 0.06 - 0.09 * (1 - tt * tt)
                else: yc = ey + 0.02 * np.ones_like(tt)
                d = np.maximum(np.abs(Y - yc), (np.abs(X - ex) - w) * 3) - 0.035
                over(cov(d) * c_nut, hexc('#2a1d14'))
        mouth = pose.get('mouth')
        if mouth == 'smile' or mouth == 'flat':
            w, dep = 0.17, (0.08 if mouth == 'smile' else 0.0)
            tt = np.clip(X / w, -1, 1)
            yc = 0.64 + dep * (1 - tt * tt)
            d = np.maximum(np.abs(Y - yc), (np.abs(X) - w) * 3) - 0.032
            over(cov(d) * c_nut, hexc('#3a2216'))
        elif mouth == 'grin':
            d = np.maximum(np.hypot(X / 0.2, (Y - 0.6) / 0.17) - 1, -(Y - 0.6) / 0.17) * 0.17
            over(cov(d) * c_nut, hexc('#4a2018'))
            dt = np.hypot((X + 0.02) / 0.1, (Y - 0.72) / 0.05) - 1
            over(cov(np.maximum(dt * 0.05, d)) * c_nut, hexc('#e0736a'))
        elif mouth == 'o':
            d = np.hypot(X / 0.085, (Y - 0.66) / 0.11) - 1
            over(cov(d * 0.085) * c_nut, hexc('#4a2018'))

    def _brows(self, pose, X, Y, cov, over):
        b = pose['brow']
        for sx in (-1, 1):
            if b == 'determined': (ax_, ay_), (bx_, by_) = (sx * 0.62, -0.04), (sx * 0.16, 0.07)
            elif b == 'worried': (ax_, ay_), (bx_, by_) = (sx * 0.6, 0.06), (sx * 0.18, -0.04)
            else: (ax_, ay_), (bx_, by_) = (sx * 0.58, -0.05), (sx * 0.16, -0.08)
            t = np.clip(((X - ax_) * (bx_ - ax_) + (Y - ay_) * (by_ - ay_)) / ((bx_ - ax_) ** 2 + (by_ - ay_) ** 2), 0, 1)
            d = np.hypot(X - ax_ - t * (bx_ - ax_), Y - ay_ - t * (by_ - ay_))
            over(cov(d - 0.05 * (1 - 0.4 * t)), hexc('#2a1a10'))

    def _shadow(self, cv, x, y, w, strength=0.22):
        s = self.s
        rx, ry = w * s, w * 0.2 * s
        x0, x1 = max(int(x * s - rx * 1.6), 0), min(int(x * s + rx * 1.6) + 1, self.W)
        y0, y1 = max(int(y * s - ry * 2.2), 0), min(int(y * s + ry * 2.2) + 1, self.H)
        if x1 <= x0 or y1 <= y0: return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = ((xx + 0.5 - x * s) / rx) ** 2 + ((yy + 0.5 - y * s) / ry) ** 2
        a = strength * np.exp(-d * 1.6)
        cv[y0:y1, x0:x1] *= (1 - a[..., None] * (1 - hexc('#6f6457')))

    # ------------------------------------------------------------------ FX (timed events, drawn per frame)
    def fx(self, kind, t0, x, y, **kw):
        """timed effect at design point (x, y): 'impact', 'dust', 'ripple', 'specks', 'sparkle', 'confetti'"""
        kw.setdefault('seed', self._seed())
        if kind == 'confetti':
            r = np.random.default_rng(kw['seed'])
            n = kw.get('n', 60)
            kw['pieces'] = [dict(kind=r.choice(['rect', 'rect', 'squig', 'dot', 'tri']),
                                 col=CONFETTI[r.integers(len(CONFETTI))],
                                 vx=r.uniform(-1, 1) * kw.get('spread', 520), vy=-r.uniform(0.4, 1.0) * kw.get('up', 900),
                                 x0=x + r.uniform(-1, 1) * kw.get('wide', 20), y0=y,
                                 size=r.uniform(10, 19) * kw.get('size', 1.0), spin=r.uniform(-9, 9),
                                 flip=r.uniform(5, 13),
                                 ph=r.uniform(0, 6.28), sway=r.uniform(8, 26), delay=r.uniform(0, kw.get('stagger', 0.25)),
                                 life=r.uniform(1.1, 1.8) * kw.get('life', 1.0), th=r.uniform(0, 6.28))
                            for _ in range(n)]
        self.fxs.append((kind, t0, x, y, kw))

    def _fx_draw(self, d, ss, t, only=None, exclude=()):
        s = self.s * ss
        ink = tuple(int(c * 255) for c in hexc(INK))
        for kind, t0, x, y, kw in self.fxs:
            if only is not None and kind not in only: continue
            if kind in exclude: continue
            tau = t - t0
            if tau < 0: continue
            if kind == 'impact':
                life = kw.get('life', 0.26)
                if tau > life: continue
                u = tau / life
                r = np.random.default_rng(kw['seed'])
                n = kw.get('n', 7); R0 = kw.get('r', 60)
                for i in range(n):
                    a = np.deg2rad(kw.get('a0', 195) + (kw.get('a1', 345) - kw.get('a0', 195)) * i / (n - 1)
                                   + r.uniform(-6, 6))
                    ri = R0 * (0.95 + 0.55 * self.ease(u, 'out'))
                    L = R0 * 0.32 * (1 - u) * r.uniform(0.7, 1.2)
                    p0 = (x + np.cos(a) * ri, y + np.sin(a) * ri)
                    p1 = (x + np.cos(a) * (ri + L), y + np.sin(a) * (ri + L))
                    d.line([(p0[0] * s, p0[1] * s), (p1[0] * s, p1[1] * s)], fill=ink + (255,),
                           width=max(1, int(3.2 * s)))
            elif kind == 'dust':
                life = kw.get('life', 0.5)
                if tau > life: continue
                r = np.random.default_rng(kw['seed'])
                n = kw.get('n', 6); spread = kw.get('spread', 70); size = kw.get('size', 13)
                dirs = kw.get('dirs', (-1, 1))
                for i in range(n):
                    dl = r.uniform(0, 0.08)
                    u = (tau - dl) / (life - dl)
                    if u < 0 or u > 1: continue
                    sd = dirs[i % len(dirs)]
                    ex = self.ease(u, 'out')
                    px = x + sd * (14 + spread * r.uniform(0.5, 1.1) * ex)
                    py = y - 4 - r.uniform(4, 22) * ex
                    rr = size * r.uniform(0.6, 1.2) * np.sin(np.pi * min(1, u * 1.15)) ** 0.6
                    if rr < 0.6: continue
                    bb = [(px - rr) * s, (py - rr) * s, (px + rr) * s, (py + rr) * s]
                    d.ellipse(bb, fill=(253, 251, 246, 255), outline=(128, 132, 156, 255), width=max(1, int(1.8 * s)))
            elif kind == 'ripple':
                life = kw.get('life', 0.8)
                if tau > life: continue
                for j in range(kw.get('n', 2)):
                    u = tau / life - j * 0.22
                    if u < 0 or u > 1: continue
                    rx = 16 + kw.get('r', 90) * self.ease(u, 'out'); ry = rx * 0.2
                    al = int(255 * (1 - u) ** 1.2)
                    d.ellipse([(x - rx) * s, (y - ry) * s, (x + rx) * s, (y + ry) * s],
                              outline=(61, 111, 148, al), width=max(1, int(2.6 * s)))
            elif kind == 'specks':
                life = kw.get('life', 0.55)
                if tau > life: continue
                r = np.random.default_rng(kw['seed'])
                col = tuple(int(c * 255) for c in hexc(kw.get('colour', '#6d4224')))
                for i in range(kw.get('n', 9)):
                    vx = r.uniform(-1, 1) * 260; vy = -r.uniform(250, 520)
                    px = x + vx * tau; py = y + vy * tau + 0.5 * 2200 * tau * tau
                    rr = r.uniform(2.8, 5.5)
                    if py > y + 4: continue                         # landed back on the ground
                    d.ellipse([(px - rr) * s, (py - rr) * s, (px + rr) * s, (py + rr) * s], fill=col + (255,))
            elif kind == 'sparkle':
                life = kw.get('life', 0.5)
                if tau > life: continue
                u = tau / life
                R = kw.get('r', 14) * np.sin(np.pi * u) ** 0.7
                col = tuple(int(c * 255) for c in hexc(kw.get('colour', '#f2b632')))
                k = 0.28
                pts = []
                for i in range(8):
                    a = np.pi / 4 * i
                    rr = R if i % 2 == 0 else R * k
                    pts.append(((x + np.cos(a) * rr) * s, (y + np.sin(a) * rr) * s))
                d.polygon(pts, fill=col + (255,))
            elif kind == 'confetti':
                for pc in kw['pieces']:
                    tt = tau - pc['delay']
                    if tt < 0 or tt > pc['life']: continue
                    c_ = 3.2
                    e = (1 - np.exp(-c_ * tt)) / c_
                    vt = 120.0
                    px = pc['x0'] + pc['vx'] * e + pc['sway'] * np.sin(pc['flip'] * 0.5 * tt + pc['ph'])
                    py = pc['y0'] + (pc['vy'] - vt) * e + vt * tt + 160 * tt * tt
                    al = int(255 * min(1, (pc['life'] - tt) / 0.3))
                    col = tuple(int(c * 255) for c in hexc(pc['col'])) + (al,)
                    th = pc['th'] + pc['spin'] * tt
                    fl = np.cos(pc['flip'] * tt + pc['ph'])
                    sz = pc['size']
                    ca, sa = np.cos(th), np.sin(th)
                    if pc['kind'] == 'rect':
                        loc = [(-sz * 0.5 * fl, -sz * 0.22), (sz * 0.5 * fl, -sz * 0.22), (sz * 0.5 * fl, sz * 0.22),
                               (-sz * 0.5 * fl, sz * 0.22)]
                        d.polygon([((px + lx * ca - ly * sa) * s, (py + lx * sa + ly * ca) * s) for lx, ly in loc], fill=col)
                    elif pc['kind'] == 'tri':
                        loc = [(0, -sz * 0.45), (sz * 0.42 * fl, sz * 0.3), (-sz * 0.42 * fl, sz * 0.3)]
                        d.polygon([((px + lx * ca - ly * sa) * s, (py + lx * sa + ly * ca) * s) for lx, ly in loc], fill=col)
                    elif pc['kind'] == 'dot':
                        rr = sz * 0.28
                        d.ellipse([(px - rr) * s, (py - rr) * s, (px + rr) * s, (py + rr) * s], fill=col)
                    else:
                        loc = [(-sz * 0.7 + sz * 0.35 * i, sz * 0.18 * (1 if i % 2 else -1)) for i in range(5)]
                        d.line([((px + lx * ca - ly * sa) * s, (py + lx * sa + ly * ca) * s) for lx, ly in loc], fill=col,
                               width=max(1, int(2.2 * s)), joint='curve')

    def _speedlines(self, d, ss, t, pose):
        dt = 1 / 30
        p0 = self.pose(t - dt)
        if p0 is None or pose.get('speed') is False: return
        vx, vy = (pose['x'] - p0['x']) / dt, (pose['y'] - p0['y']) / dt
        v = np.hypot(vx, vy)
        thr = pose.get('speed_min', 650)
        if v < thr: return
        s = self.s * ss
        ux, uy = vx / v, vy / v
        nx, ny = -uy, ux
        u = self.actor_size * pose.get('scale', 1.0)
        k = min(1.0, (v - thr) / 500)
        r = np.random.default_rng(int(t * 1000) % 100000)
        col = tuple(int(c * 255) for c in hexc('#77767f'))
        for off in (-0.75, -0.1, 0.6):
            o = off * u + r.uniform(-4, 4)
            st = 1.0 * u + r.uniform(0, 10)
            L = u * (0.9 + 1.0 * k) * r.uniform(0.7, 1.2)
            a = (pose['x'] - ux * st + nx * o, pose['y'] - uy * st + ny * o)
            b = (a[0] - ux * L, a[1] - uy * L)
            d.line([(a[0] * s, a[1] * s), (b[0] * s, b[1] * s)], fill=col + (int(220 * (0.55 + 0.45 * k)),),
                   width=max(1, int(3.0 * s)))

    def _overlay(self, cv, t, pose=None, fx=True, only=None):
        ss = 2
        im = Image.new('RGBA', (self.W * ss, self.H * ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if fx: self._fx_draw(d, ss, t, only)
        if pose is not None: self._speedlines(d, ss, t, pose)
        bb = im.getbbox()
        if not bb: return
        x0, y0 = bb[0] // ss, bb[1] // ss
        x1, y1 = min(self.W, -(-bb[2] // ss)), min(self.H, -(-bb[3] // ss))
        crop = im.crop((x0 * ss, y0 * ss, x1 * ss, y1 * ss)).resize((x1 - x0, y1 - y0), Image.BOX)
        o = np.asarray(crop, np.float32) / 255
        a = o[..., 3:4]
        sl = cv[y0:y1, x0:x1]
        sl *= (1 - a); sl += o[..., :3] * a

    # ------------------------------------------------------------------ compositing
    def _draw_layer(self, cv, L, t, full=False):
        p = 1.0 if full else self._progress(L, t)
        if p <= 0: return
        a, rgb = L.a, L.rgb
        if p < 1 and L.pop is not None:
            sc = max(1e-3, self.ease(p, 'back'))
            M = np.eye(2, dtype=np.float32) * sc
            org = (L.pop[0] - L.x0, L.pop[1] - L.y0)
            self._affine(cv, rgb, a, org, M, np.array(L.pop, np.float32), min(1.0, p * 3))
            return
        if p < 1 and L.rev is not None:
            q = p * (1 + L.soft)
            m = np.clip((q - L.rev) / L.soft, 0, 1)
            if L.wet:
                front = (m * (1 - m) * 4)[..., None]
                rgb = rgb * (1 - L.wet * front)
            a = a * m
        elif p < 1 and L.rev is None:
            a = a * p
        h, w = a.shape
        x0, y0 = L.x0, L.y0
        ax0, ay0, ax1, ay1 = max(x0, 0), max(y0, 0), min(x0 + w, self.W), min(y0 + h, self.H)
        if ax1 <= ax0 or ay1 <= ay0: return
        aa = a[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0, None]
        cc = rgb[ay0 - y0:ay1 - y0, ax0 - x0:ax1 - x0]
        sl = cv[ay0:ay1, ax0:ax1]
        sl *= (1 - aa); sl += cc * aa

    def _progress(self, L, t):
        if L.follow is not None:
            lead, xa, xb = L.follow
            p = float(np.clip((self.lead_x(t) + lead - xa) / max(xb - xa, 1e-3), 0, 1))
            if L.pre is not None:                               # the part left of the start is drawn by time
                t0, t1, upto = L.pre
                p = max(p, upto * self.ease((t - t0) / max(t1 - t0, 1e-3), 'sine') if t > t0 else 0.0)
            return p
        t0, t1 = L.when
        if t <= t0: return 0.0 if t1 > t0 or t < t0 else 1.0
        if t >= t1: return 1.0
        return self.ease((t - t0) / (t1 - t0), L.ease)

    def _compose(self, t, actor=True, fx=True, full=False, ghosts=None, props=True):
        cv = self.base.copy()
        pose = self.pose(t) if actor else None
        items = [(L.z, 0, L) for L in self.layers]
        if props: items += [(z, 1, (sp, t0, t1, fn)) for sp, t0, t1, fn, z in self.props]
        items.append((50.0, 2, None))
        items.sort(key=lambda it: it[0])
        for z, kind, obj in items:
            if kind == 0: self._draw_layer(cv, obj, t, full)
            elif kind == 1:
                sp, t0, t1, fn = obj
                self._draw_prop(cv, sp, self._prop_pose(t0, t1, fn, t))
            elif kind == 2:
                if ghosts: ghosts(cv)
                if pose is not None:
                    if pose.get('shadow'):
                        gx, gy, wsh, st = pose['shadow']
                        self._shadow(cv, gx, gy, wsh, st)
                    self._actor(cv, pose)
                    for extra in pose.get('also', []):
                        self._actor(cv, extra)
        if fx or pose is not None: self._overlay(cv, t, pose, fx)
        return cv

    def _to_image(self, cv):
        return Image.fromarray((np.clip(cv * self.grain, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')

    def frame(self, t):
        """the animation frame at time t (seconds) as a PIL image"""
        return self._to_image(self._compose(t))

    # ------------------------------------------------------------------ outputs
    def gif(self, path, fps=15.0, t_end=None, hold=1.6, colours=255, sample_every=5, bayer=2.4, start=0.0):
        """render the animation frame by frame into a looping GIF: one shared palette (sampled from every
        `sample_every`-th frame, saturated pixels weighted x4), a fixed 4x4 Bayer dither, unchanged pixels written
        as a transparent magenta index so LZW only pays for what moves. Only one frame is held as floats at a time."""
        t_end = t_end if t_end is not None else max(a[1] for a in self.acts)
        times = np.arange(start, t_end + 1e-6, 1 / fps)
        if times[-1] < t_end - 1e-6: times = np.append(times, t_end)
        B = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 - 0.5
        dith = np.tile(B, (self.H // 4 + 1, self.W // 4 + 1))[:self.H, :self.W, None] * bayer

        def render(t):
            a = np.asarray(self.frame(t), np.float32) + dith
            return Image.fromarray(np.clip(a + 0.5, 0, 255).astype(np.uint8), 'RGB')

        samples = []
        for t in list(times[::sample_every]) + [times[-1]]:
            px = np.asarray(render(t)).reshape(-1, 3)
            samples.append(px[::3])
        px = np.concatenate(samples)
        sat = px.max(1).astype(int) - px.min(1).astype(int)
        px = np.concatenate([px] + [px[sat > 70]] * 4)
        wq = 512
        px = px[:(len(px) // wq) * wq].reshape(-1, wq, 3)
        pal_im = Image.fromarray(px, 'RGB').quantize(colors=colours, method=Image.Quantize.MEDIANCUT,
                                                     dither=Image.Dither.NONE)
        palette = pal_im.getpalette()[:colours * 3]
        palette += palette[:3] * (256 - colours)                 # spare slots repeat colour 0 while quantizing ...
        pal_im.putpalette(palette)
        palette = palette[:765] + [255, 0, 255]                  # ... and 255 becomes the magenta 'unchanged' marker
        idx, prev = [], None
        for t in times:
            q = np.asarray(render(t).quantize(palette=pal_im, dither=Image.Dither.NONE)).copy()
            q[q == 255] = 0
            o = q.copy()
            if prev is not None: o[q == prev] = 255
            prev = q
            idx.append(o)
        frames = []
        for o in idx:
            im = Image.fromarray(o.astype(np.uint8), 'P'); im.putpalette(palette); frames.append(im)
        cs = [int(round(100 * (i + 1) / fps)) - int(round(100 * i / fps)) for i in range(len(frames))]
        dur = [10 * c for c in cs]                               # GIF delays are centiseconds: 15 fps -> 7, 7, 6, ...
        dur[-1] = int(hold * 1000)
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=dur, loop=0, optimize=False,
                       transparency=255, disposal=1)
        _strip_local_tables(path)
        return len(frames)

    def journey(self, times, t_world=None, arc=None, arc_colour=PENCIL, ghost_alpha=None, labels=None, label_font='hand',
                prop_arcs=(), world_fx=False, final=True, props=True, prop_arc_colour='#e39a62'):
        """the finished world with the character multiply-exposed at the poses `times` on a pencil motion arc.
        arc = (t0, t1) of the path to trace; ghost_alpha: list of alphas (default rising 0.62 -> 1);
        labels: list of (text, dx, dy) sound-words in pencil next to each pose; prop_arcs: [(t0, t1, fn)] faint
        dotted paths for moving props"""
        t_world = t_world if t_world is not None else max(a[1] for a in self.acts)
        n = len(times)
        ghost_alpha = ghost_alpha or list(np.linspace(0.62, 1.0, n))
        s = self.s

        def ghosts(cv):
            ss = 2
            im = Image.new('RGBA', (self.W * ss, self.H * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            col = tuple(int(c * 255) for c in hexc(arc_colour))
            pcol = tuple(int(c * 255) for c in hexc(prop_arc_colour))
            for (pt0, pt1, fn) in prop_arcs:
                pts = [fn(min(1, (tt - pt0) / (pt1 - pt0)), tt) for tt in np.arange(pt0, pt1, 1 / 120)]
                self._dotted(d, [(p['x'], p['y']) for p in pts if p], ss, pcol + (150,), 11, 2.2)
            if arc:
                pts = [self.pose(tt) for tt in np.arange(arc[0], arc[1], 1 / 200)]
                pts = [(p['x'], p['y']) for p in pts if p is not None and p.get('clip') is None]
                self._dotted(d, pts, ss, col + (210,), 15, 3.0, chevrons=6)
            self._paste_overlay(cv, im, ss)
            for i, tt in enumerate(times):
                p = self.pose(tt)
                for sp, t0, t1, fn, z in self.props:
                    pp = self._prop_pose(t0, t1, fn, tt)
                    if pp is not None and pp.get('ghost', False):
                        self._draw_prop(cv, sp, dict(pp, alpha=ghost_alpha[i] * pp.get('alpha', 1.0)))
                if p is None: continue
                if p.get('shadow'):
                    gx, gy, wsh, st = p['shadow']
                    self._shadow(cv, gx, gy, wsh, st * ghost_alpha[i])
                im2 = Image.new('RGBA', (self.W * ss, self.H * ss), (0, 0, 0, 0)); d2 = ImageDraw.Draw(im2)
                self._fx_draw(d2, ss, tt, exclude=('confetti',))
                self._speedlines(d2, ss, tt, p)
                self._paste_overlay(cv, im2, ss, ghost_alpha[i])
                self._actor(cv, p, ghost_alpha[i])
                for extra in p.get('also', []):
                    self._actor(cv, extra, ghost_alpha[i])
            if final:
                p = self.pose(t_world)
                if p is not None: self._actor(cv, p)
            if labels:
                im = Image.new('RGBA', (self.W * ss, self.H * ss), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
                ft = load_font(label_font, 34 * s * ss)
                col = tuple(int(c * 255) for c in hexc('#6f6e78'))
                for i, lab in enumerate(labels):
                    if not lab: continue
                    txt, dx, dy = lab
                    p = self.pose(times[i])
                    d.text(((p['x'] + dx) * s * ss, (p['y'] + dy) * s * ss), txt, font=ft, fill=col + (235,),
                           anchor='mm')
                self._paste_overlay(cv, im, ss)

        self.canvas = self._compose(t_world, actor=False, fx=False, full=True, ghosts=ghosts, props=props)
        if world_fx:
            ss = 2
            im = Image.new('RGBA', (self.W * ss, self.H * ss), (0, 0, 0, 0))
            self._fx_draw(ImageDraw.Draw(im), ss, t_world, only=('confetti',))
            self._paste_overlay(self.canvas, im, ss)
        return self._to_image(self.canvas)

    def _dotted(self, d, pts, ss, col, gap, r, chevrons=0):
        if len(pts) < 2: return
        P = _resample(np.asarray(pts, np.float32), 1.0)
        s = self.s * ss
        cum = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        for g in np.arange(gap / 2, cum[-1], gap):
            i = int(np.searchsorted(cum, g))
            x, y = P[min(i, len(P) - 1)]
            d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=col)
        if chevrons:
            for g in np.linspace(0, cum[-1], chevrons + 2)[1:-1]:
                i = int(np.searchsorted(cum, g))
                i = min(max(i, 2), len(P) - 3)
                x, y = P[i]; tx, ty = P[i + 2] - P[i - 2]; tl = np.hypot(tx, ty) + 1e-6; tx, ty = tx / tl, ty / tl
                k = 11
                a = (x - tx * k + ty * k * 0.7, y - ty * k - tx * k * 0.7)
                b = (x - tx * k - ty * k * 0.7, y - ty * k + tx * k * 0.7)
                d.line([(a[0] * s, a[1] * s), (x * s, y * s), (b[0] * s, b[1] * s)], fill=col,
                       width=max(1, int(2.8 * s)), joint='curve')

    def _paste_overlay(self, cv, im, ss, alpha=1.0):
        bb = im.getbbox()
        if not bb: return
        x0, y0 = bb[0] // ss, bb[1] // ss
        x1, y1 = min(self.W, -(-bb[2] // ss)), min(self.H, -(-bb[3] // ss))
        o = np.asarray(im.crop((x0 * ss, y0 * ss, x1 * ss, y1 * ss)).resize((x1 - x0, y1 - y0), Image.BOX),
                       np.float32) / 255
        a = o[..., 3:4] * alpha
        sl = cv[y0:y1, x0:x1]
        sl *= (1 - a); sl += o[..., :3] * a

    def stage(self, name, t=None):
        """keyframe snapshot for the stage tools: frame(t), or the current poster canvas when t is None"""
        img = self.frame(t) if t is not None else self._to_image(self.canvas)
        self.stages.append((name, img))

    def save(self, path, stages_dir=None, quality=88):
        img = self._to_image(self.canvas)
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


def _strip_local_tables(path):
    """Pillow repeats the palette as a local colour table on every frame; drop copies equal to the global table"""
    b = bytearray(open(path, 'rb').read())
    flags = b[10]; gsize = 2 << (flags & 7); gct = bytes(b[13:13 + 3 * gsize]) if flags & 0x80 else None
    out = b[:13 + (3 * gsize if gct else 0)]; i = len(out)
    while i < len(b):
        t = b[i]
        if t == 0x21:
            j = i + 2
            while b[j]: j += b[j] + 1
            out += b[i:j + 1]; i = j + 1
        elif t == 0x2C:
            pf = b[i + 9]; desc = bytearray(b[i:i + 10]); i += 10
            if pf & 0x80:
                n = 3 * (2 << (pf & 7)); tab = bytes(b[i:i + n])
                if tab == gct: desc[9] = pf & 0x78; i += n
                else: desc += tab; i += n
            j = i + 1
            while b[j]: j += b[j] + 1
            out += desc + b[i:j + 1]; i = j + 1
        else:
            out += b[i:]; break
    open(path, 'wb').write(bytes(out))
