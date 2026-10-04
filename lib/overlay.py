"""overlay — 描图纸叠层 / Overlay Sheets: separations on a light box (numpy + Pillow only).

A soft light box glows warm white from below. On it lies a base sheet printed in black linework with grey flat
tones; on top of that, translucent tracing-paper or film sheets, each printed in ONE ink, are laid down on their
registration crosses. The light comes through everything, so the picture is a product of transmittances:

  light box   a dark bevelled case on a desk with a recessed opal panel. `lamp(level)` runs from off (a dull grey
              acrylic lit only by the room) through a warm, dim glow to full: warm white, brightest a little left
              of centre, falling off to a creamy edge, with a warm spill onto the inside of the bezel.
  sheets      every sheet keeps its own buffers in its own frame: paper (tint, backlit *formation* -- the cloudy
              flocs you only see against the light -- and stray fibres), a coverage map per ink, punched holes
              and a cut edge that reads as a thin darker line. Kinds: 'base' (bond paper, almost no texture),
              'tracing' (cloudy, fibrous, frosts what is under it a little even when flat), 'drafting' (matte
              film: a faint even tooth, less frost), 'film' (clear acetate: almost no loss and a gloss sheen).
  inks        coverage c is a printed tint: 0..1 is the share of the area under ink (a screen), so its
              transmittance is 1 - c (1 - ink); above 1 the ink is printed again (a double hit) and deepens as
              ink^(c-1). Overlapping inks on different sheets multiply, exactly like the real thing: blue over
              yellow makes green, magenta over yellow makes red, blue over magenta makes violet. One plate never
              doubles itself: drawing on the same ink keeps the max coverage. Prints get a faint ink mottle.
  lifting     `place(sheet, lift, dx, dy, rot)`. A lifted sheet floats above the stack: it is a little larger
              (closer to the eye), it casts a wide, soft, warm shadow that you also see through it, and -- being
              a diffuser held off the drawing -- it blurs everything under it. Laid down (lift 0, no offset) it
              is crisp, its shadow shrinks to a thin contact line and its crosses sit on the base crosses.
  curl        a corner that will not lie flat: a shading band across the corner, a soft shadow under it and a
              little blur of what is beneath the lifted tip.
  hardware    `peg_bar` -- a steel bar with a round, a slot and a round peg (the animation-desk standard); the
              base sheet's punched holes drop onto the pegs and the light shines through the gap around each
              peg. `tape` -- crepe drafting tape with torn ends, semi-opaque on the light.

Drawing happens in canvas coordinates of the *laid-down* position, on any sheet, so separations register by
construction: draw the river on the base and on the blue sheet with the same points.

    import sys; sys.path.insert(0, 'lib')
    from overlay import Overlay
    o = Overlay(1920, 1080, seed=3)
    o.desk(); o.lightbox(34, 24, 1886, 1056)
    o.lamp(1.0)
    base = o.sheet(160, 120, 1200, 840, 'base', ink='black')
    base.fill(o.circle(760, 540, 260), 0.2)               # grey flat tone (20 % black)
    base.line(o.circle_pts(760, 540, 260), 2.2, closed=True)
    base.cross(200, 160); base.cross(1320, 920)
    o.place(base)
    blue = o.sheet(150, 110, 1220, 860, 'tracing', ink='blue', curl=('br', 80))
    blue.fill(o.circle(900, 540, 200), 0.45); blue.cross(200, 160); blue.cross(1320, 920)
    o.place(blue, lift=1, dx=-30, dy=-24, rot=-1.5); o.stage('blue_lifted')
    o.place(blue)                                          # lands crisp, crosses on crosses
    o.tape(1360, 140, rot=40)
    o.save('overlay.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core import blur, spline, noise2d, smoothstep, shift, load_font

INKS = {
    'black': '#24211d',
    'blue': '#1d62cf',
    'yellow': '#f8c92c',
    'magenta': '#d8177d',
    'cyan': '#1d9fd8',
    'orange': '#f06a28',
    'green': '#279a57',
    'red': '#de3434',
}
PAPERS = {  # tint (transmittance), formation amplitude, fibres, frost (veil when flat), edge darkness, under-blur when lifted
    'base': dict(tint=(0.966, 0.957, 0.934), formation=0.010, fibres=0.30, frost=0.00, edge=0.34, diffuse=2.2),
    'tracing': dict(tint=(0.982, 0.978, 0.966), formation=0.020, fibres=0.80, frost=0.040, edge=0.40, diffuse=2.8),
    'drafting': dict(tint=(0.986, 0.986, 0.980), formation=0.009, fibres=0.20, frost=0.022, edge=0.42, diffuse=2.4),
    'film': dict(tint=(0.984, 0.989, 0.989), formation=0.000, fibres=0.00, frost=0.000, edge=0.55, diffuse=1.2),
}
SHADOW = (0.29, 0.20, 0.12)          # warm brown: the room light is warm, the shadow takes the light box's tint
TAPE = '#f7ebcf'

_FONT_TABLE = {   # (glob, face index); first hit wins -- macOS, Linux, Windows. Override: $INKPAINT_FONT_OVERLAY_<KIND>
    'map': [('/System/Library/Fonts/Supplemental/GillSans.ttc', 0), ('/usr/share/fonts/**/DejaVuSans.ttf', 0),
            ('C:/Windows/Fonts/GIL_____.TTF', 0), ('C:/Windows/Fonts/arial.ttf', 0)],
    'map_bold': [('/System/Library/Fonts/Supplemental/GillSans.ttc', 4), ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0),
                 ('C:/Windows/Fonts/GILB____.TTF', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'map_heavy': [('/System/Library/Fonts/Supplemental/GillSans.ttc', 6), ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0),
                  ('C:/Windows/Fonts/GILSANUB.TTF', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'map_italic': [('/System/Library/Fonts/Supplemental/GillSans.ttc', 2), ('/System/Library/Fonts/Supplemental/Georgia Italic.ttf', 0),
                   ('/usr/share/fonts/**/DejaVuSerif-Italic.ttf', 0), ('C:/Windows/Fonts/georgiai.ttf', 0)],
    'map_light': [('/System/Library/Fonts/Supplemental/GillSans.ttc', 7), ('/usr/share/fonts/**/DejaVuSans-ExtraLight.ttf', 0),
                  ('C:/Windows/Fonts/GIL_____.TTF', 0), ('C:/Windows/Fonts/arial.ttf', 0)],
    'title': [('/System/Library/Fonts/Avenir Next.ttc', 8), ('/System/Library/Fonts/HelveticaNeue.ttc', 1),
              ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'label': [('/System/Library/Fonts/Avenir Next.ttc', 2), ('/System/Library/Fonts/HelveticaNeue.ttc', 10),
              ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'cjk': [('/System/Library/Fonts/STHeiti Medium.ttc', 1), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2),
            ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSansCJK*.tt[cf]', 0),
            ('C:/Windows/Fonts/msyhbd.ttc', 0), ('C:/Windows/Fonts/msyh.ttc', 0)],
    'cjk_light': [('/System/Library/Fonts/STHeiti Light.ttc', 1), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
                  ('/usr/share/fonts/**/NotoSansCJK*Regular*.tt[cf]', 0), ('C:/Windows/Fonts/msyh.ttc', 0)],
}
_FONTS = {}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str):
        return hexc(INKS[c]) if c in INKS else hexc(c)
    return np.asarray(c, np.float32)


def font(kind, size):
    """PIL font: overlay kinds (map, map_bold, map_heavy, map_italic, map_light, title, label, cjk, cjk_light) or
    any core.load_font style (sans, sans_bold, serif, condensed, typewriter, ...)"""
    key = (kind, int(size))
    if key in _FONTS: return _FONTS[key]
    f = None
    env = os.environ.get('INKPAINT_FONT_OVERLAY_' + kind.upper())
    cands = ([(env, 0)] if env and os.path.exists(env) else []) + _FONT_TABLE.get(kind, [])
    for pat, idx in cands:
        for p in glob.glob(pat, recursive=True):
            try:
                f = ImageFont.truetype(p, int(size), index=idx); break
            except OSError:
                continue
        if f: break
    if f is None:
        f = load_font(kind if kind not in _FONT_TABLE else ('sans_bold' if 'bold' in kind or kind == 'title' else 'sans'), size)
    _FONTS[key] = f
    return f


def _closed_spline(P, per=8):
    P = np.asarray(P, np.float32)
    Q = np.vstack([P[-1:], P, P[:2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out, np.float32)


def _level(f, t, width):
    """anti-aliased line of `width` px along the level set f == t (gradient-normalised, so constant width)"""
    gy, gx = np.gradient(f)
    g = np.sqrt(gx * gx + gy * gy) + 1e-5
    return np.clip(width / 2 + 0.5 - np.abs(f - t) / g, 0, 1).astype(np.float32)


class Sheet:
    """One sheet on the light box. Create it with `Overlay.sheet()`; draw on it in canvas coordinates of its
    laid-down position; show it with `Overlay.place()`."""

    def __init__(self, ov, x, y, w, h, kind, ink, tint, fibre, curl, seed, edge):
        self.ov = ov
        self.x0, self.y0, self.w, self.h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        self.kind = kind
        self.P = dict(PAPERS[kind])
        if tint is not None: self.P['tint'] = tuple(_c(tint))
        if fibre is not None: self.P['fibres'] = fibre
        if edge is not None: self.P['edge'] = edge
        self.ink = ink
        self.cov = {}
        self.holes = np.zeros((self.h, self.w), np.float32)
        self.curl = curl
        self.rng = np.random.default_rng(seed)
        self.tex_seed = int(seed) + 7919              # paper texture: fixed, so a rebuild looks the same
        self.state = None                           # (lift, dx, dy, rot) once placed
        self.sheen = kind == 'film'
        self._cache = None

    # ------------------------------------------------------------ geometry
    def _local(self, sl_y, sl_x):
        """intersection of a canvas box with this sheet -> (canvas slices, local slices) or None"""
        y0, y1 = max(sl_y.start, self.y0), min(sl_y.stop, self.y0 + self.h)
        x0, x1 = max(sl_x.start, self.x0), min(sl_x.stop, self.x0 + self.w)
        if y1 <= y0 or x1 <= x0: return None
        return ((slice(y0 - sl_y.start, y1 - sl_y.start), slice(x0 - sl_x.start, x1 - sl_x.start)),
                (slice(y0 - self.y0, y1 - self.y0), slice(x0 - self.x0, x1 - self.x0)))

    def _buf(self, ink):
        ink = ink or self.ink
        if ink not in self.cov:
            self.cov[ink] = np.zeros((self.h, self.w), np.float32)
        return self.cov[ink]

    def _put(self, m, oy, ox, cover, ink):
        """max-merge a mask crop m (canvas origin oy, ox) into the ink plate"""
        self._cache = None
        hit = self._local(slice(oy, oy + m.shape[0]), slice(ox, ox + m.shape[1]))
        if hit is None: return
        (my, mx), (ly, lx) = hit
        b = self._buf(ink)
        np.maximum(b[ly, lx], m[my, mx] * cover, out=b[ly, lx])

    # ------------------------------------------------------------ printing
    def fill(self, m, cover=1.0, ink=None, smooth=False):
        """flat ink: `m` is a canvas mask or a polygon (list of points); cover < 1 is a tint, > 1 a double hit"""
        if not isinstance(m, np.ndarray) or m.ndim != 2 or m.shape != (self.ov.H, self.ov.W):
            m, oy, ox = self.ov._poly_crop([m], smooth)
        else:
            sl = (slice(self.y0, self.y0 + self.h), slice(self.x0, self.x0 + self.w))
            m, oy, ox = m[sl], self.y0, self.x0
        self._put(m, oy, ox, cover, ink)

    def line(self, pts, width=2.0, cover=1.0, ink=None, closed=False, smooth=False, dash=None, cap=True):
        """printed line along a polyline; dash=(on, off) in px; round caps"""
        self.lines([pts], width, cover, ink, closed, smooth, dash, cap)

    def lines(self, paths, width=2.0, cover=1.0, ink=None, closed=False, smooth=False, dash=None, cap=True):
        """many lines in one raster pass (streets, party walls, ticks)"""
        m, oy, ox = self.ov._lines_crop(paths, width, closed, smooth, dash, cap)
        if m is not None: self._put(m, oy, ox, cover, ink)

    def dots(self, pts, r=3.0, cover=1.0, ink=None):
        m, oy, ox = self.ov._dots_crop(pts, r)
        if m is not None: self._put(m, oy, ox, cover, ink)

    def circle(self, cx, cy, r, width=None, cover=1.0, ink=None):
        """filled disc (width None) or ring"""
        if width is None:
            self.dots([(cx, cy)], r, cover, ink)
        else:
            self.line(self.ov.circle_pts(cx, cy, r), width, cover, ink, closed=True)

    def hatch(self, m, spacing=8.0, angle=45.0, width=1.2, cover=1.0, ink=None):
        """parallel ruled lines clipped to a canvas mask (cross-hatched areas, slipways, sand)"""
        ys, xs = np.nonzero(m > 0.02)
        if not len(xs): return
        x0, x1, y0, y1 = xs.min() - 2, xs.max() + 3, ys.min() - 2, ys.max() + 3
        a = np.deg2rad(angle); d = np.array([np.cos(a), np.sin(a)]); nrm = np.array([-d[1], d[0]])
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; R = np.hypot(x1 - x0, y1 - y0) / 2 + 2
        paths = []
        for k in np.arange(-R, R, spacing):
            c = np.array([cx, cy]) + nrm * k
            paths.append([c - d * R, c + d * R])
        lm, oy, ox = self.ov._lines_crop(paths, width, False, False, None, False, box=(x0, y0, x1, y1))
        lm = lm * m[oy:oy + lm.shape[0], ox:ox + lm.shape[1]]
        self._put(lm, oy, ox, cover, ink)

    def stipple(self, m, n=400, r=1.6, cover=1.0, ink=None, seed=None):
        """random dots inside a canvas mask (sand, shingle, scrub)"""
        rng = np.random.default_rng(seed if seed is not None else int(self.rng.integers(1 << 30)))
        ys, xs = np.nonzero(m > 0.5)
        if not len(xs): return
        i = rng.choice(len(xs), size=min(n, len(xs)), replace=False)
        self.dots(np.stack([xs[i] + rng.uniform(0, 1, len(i)), ys[i] + rng.uniform(0, 1, len(i))], 1), r, cover, ink)

    def text(self, s, x, y, size, font_kind='map', cover=1.0, ink=None, anchor='mm', spacing=0.0, rot=0.0,
             halo=0.0, halo_inks=None, knock=False):
        """printed type. halo > 0 first clears ink (on `halo_inks`, default every plate of this sheet) in a
        band around the letters so a label reads over tone; knock=True clears the letters themselves out of the
        ink (reversed-out numbers in a solid disc)"""
        m, oy, ox = self.ov._text_crop(s, x, y, size, font_kind, anchor, spacing, rot, pad=int(halo) + 4)
        if m is None: return None
        if halo > 0:
            hm = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(int(2 * round(halo) + 1))), np.float32) / 255
            hm = blur(hm, 0.6)
            for k in (halo_inks or list(self.cov.keys())):
                self._clear(hm, oy, ox, k)
        if knock:
            for k in (halo_inks or [ink or self.ink]):
                self._clear(m, oy, ox, k)
        else:
            self._put(m, oy, ox, cover, ink)
        ys, xs = np.nonzero(m > 0.3)
        return (ox + xs.min(), oy + ys.min(), ox + xs.max(), oy + ys.max()) if len(xs) else None

    def _clear(self, m, oy, ox, ink):
        self._cache = None
        hit = self._local(slice(oy, oy + m.shape[0]), slice(ox, ox + m.shape[1]))
        if hit is None or ink not in self.cov: return
        (my, mx), (ly, lx) = hit
        self.cov[ink][ly, lx] *= (1 - np.clip(m[my, mx], 0, 1))

    def knock(self, m, ink=None):
        """clear ink inside a canvas mask (every plate of this sheet when ink is None)"""
        sl = (slice(self.y0, self.y0 + self.h), slice(self.x0, self.x0 + self.w))
        for k in ([ink] if ink else list(self.cov.keys())):
            self._clear(m[sl], self.y0, self.x0, k)

    def cross(self, x, y, size=20.0, r=11.0, width=None, ink=None, cover=1.0):
        """registration mark: a circle and a cross. Print the same point on every sheet -- laid down, they coincide"""
        w = width or (1.3 if (ink or self.ink) == 'black' else 2.4)
        self.lines([[(x - size, y), (x + size, y)], [(x, y - size), (x, y + size)]], w, cover, ink, cap=False)
        self.line(self.ov.circle_pts(x, y, r), w, cover, ink, closed=True)

    def arrow(self, tip, direction, size=14.0, cover=1.0, ink=None, spread=26.0):
        """solid arrowhead at `tip` pointing along `direction`"""
        d = np.asarray(direction, np.float32); d /= np.linalg.norm(d) + 1e-6
        a = np.deg2rad(spread)
        rot = lambda v, t: np.array([v[0] * np.cos(t) - v[1] * np.sin(t), v[0] * np.sin(t) + v[1] * np.cos(t)])
        p = np.asarray(tip, np.float32)
        self.fill([p, p - rot(d, a) * size, p - d * size * 0.72, p - rot(d, -a) * size], cover, ink)

    # ------------------------------------------------------------ the paper itself
    def punch(self, x, y, r=10.0):
        """a punched round hole (canvas coordinates of the laid-down sheet)"""
        self._cache = None
        m, oy, ox = self.ov._dots_crop([(x, y)], r)
        hit = self._local(slice(oy, oy + m.shape[0]), slice(ox, ox + m.shape[1]))
        if hit is None: return
        (my, mx), (ly, lx) = hit
        np.maximum(self.holes[ly, lx], m[my, mx], out=self.holes[ly, lx])

    def punch_slot(self, x, y, w=70.0, h=20.0):
        """a punched slot (the middle hole of an animation peg pattern)"""
        self._cache = None
        m, oy, ox = self.ov._lines_crop([[(x - w / 2 + h / 2, y), (x + w / 2 - h / 2, y)]], h, False, False, None, True)
        hit = self._local(slice(oy, oy + m.shape[0]), slice(ox, ox + m.shape[1]))
        if hit is None: return
        (my, mx), (ly, lx) = hit
        np.maximum(self.holes[ly, lx], m[my, mx], out=self.holes[ly, lx])

    def _build(self):
        """local transmittance T (h, w, 3), footprint F (h, w), curl weights -- cached until drawn on again"""
        if self._cache is not None: return self._cache
        h, w, P = self.h, self.w, self.P
        rng = np.random.default_rng(self.tex_seed)
        s = int(rng.integers(1 << 30))
        F = np.ones((h, w), np.float32)
        F[:, :1] = F[:, -1:] = 0.5; F[:1, :] = F[-1:, :] = 0.5
        F *= 1 - self.holes
        # paper: backlit formation (cloudy flocs), stray fibres, cut edge
        tint = np.asarray(P['tint'], np.float32)
        T = np.ones((h, w, 3), np.float32) * tint
        if P['formation'] > 0:
            form = 0.55 * noise2d(h, w, 6, 3, s) + 0.45 * noise2d(h, w, 22, 3, s + 1)
            form = (form - form.mean()) / (form.std() + 1e-6)
            T *= (1 - P['formation'] * 0.5 * form)[..., None]
        if P['fibres'] > 0:
            n = int(w * h / 2600 * P['fibres'])
            fib = Image.new('L', (w, h), 0); d = ImageDraw.Draw(fib)
            for _ in range(n):
                x, y = rng.uniform(0, w), rng.uniform(0, h)
                a = rng.uniform(0, np.pi); L = rng.uniform(8, 34); bend = rng.normal(0, 0.35)
                t = np.linspace(-0.5, 0.5, 6)
                xs = x + np.cos(a + bend * t) * L * t; ys = y + np.sin(a + bend * t) * L * t
                d.line(list(zip(xs.tolist(), ys.tolist())), fill=int(rng.uniform(30, 80)), width=1)
            fib = np.asarray(fib, np.float32) / 255
            T *= (1 - 0.11 * blur(fib, 0.5) * P['fibres'] ** 0.5)[..., None]
        if self.kind == 'drafting':                                     # matte film tooth: even and very fine
            T *= (1 - 0.012 * (noise2d(h, w, 1.4, 2, s + 2) - 0.5))[..., None]
        # inks
        mottle = 0.94 + 0.12 * noise2d(h, w, 2.2, 2, s + 3) + 0.05 * (noise2d(h, w, 90, 2, s + 4) - 0.5)
        for k, c in self.cov.items():
            c = blur(c, 0.45) * mottle
            ink = _c(k)
            lin = np.clip(c, 0, 1)[..., None]
            Tk = 1 - lin * (1 - ink)
            extra = np.clip(c - 1, 0, None)[..., None]
            if extra.max() > 0: Tk = Tk * ink ** extra
            T *= Tk
        # corner curl: a shading band across the corner, the tip a touch lighter (it tilts toward the room light)
        cw = np.zeros((h, w), np.float32); csh = np.zeros((h, w), np.float32)
        if self.curl:
            corner, R = (self.curl, 70.0) if isinstance(self.curl, str) else self.curl
            cx = 0 if 'l' in corner else w; cy = 0 if 't' in corner else h
            sx = 1 if 'l' in corner else -1; sy = 1 if 't' in corner else -1
            Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
            u = ((X - cx) * sx + (Y - cy) * sy) / np.sqrt(2) / R
            band = np.exp(-((u - 0.52) / 0.11) ** 2) * (u < 1.2)                # the roll, turned away from the room light
            crease = np.exp(-((u - 0.66) / 0.035) ** 2)                          # its top edge catches the light
            T *= (1 - 0.07 * band)[..., None]
            T = T + (1 - T) * (0.10 * np.clip(1 - u / 0.42, 0, 1) ** 1.5 + 0.35 * crease)[..., None]
            cw = (np.clip(1 - u, 0, 1) ** 2).astype(np.float32)
            d2 = (X - cx - sx * 0.2 * R) ** 2 + (Y - cy - sy * 0.26 * R) ** 2
            csh = (0.16 * np.exp(-d2 / (2 * (0.26 * R) ** 2))).astype(np.float32)
        # the cut edge (and the rims of the holes) catch as a thin darker line
        f = blur(F, 0.7)
        edge = _level(f, 0.5, 1.3)
        T *= 1 - P['edge'] * edge[..., None] * (1 - np.array([0.38, 0.30, 0.22], np.float32)) * 1.6
        T = np.clip(T, 0, 1)
        A = (1 - T) * F[..., None]                                       # what the sheet takes away; 0 off the paper
        sheen = None
        if self.sheen:
            Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
            dd = (X * 0.42 + Y) / max(h, w)
            sheen = (0.07 * np.exp(-((dd - 0.36) / 0.09) ** 2) + 0.04 * np.exp(-((dd - 0.55) / 0.03) ** 2)).astype(np.float32)
        self._cache = dict(A=A.astype(np.float32), F=F, cw=cw, csh=csh, sheen=sheen)
        return self._cache


class Overlay:
    INKS = INKS
    PAPERS = PAPERS

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.keep_stages = keep_stages              # False: stage() is free (no snapshot renders)
        self.stages = []
        self.items = []                              # z-order: peg bars, sheets (once placed), tapes
        self.level = 1.0
        self.bg = np.ones((H, W, 3), np.float32) * hexc('#3a3530')
        self.panel = None
        self._E = {}
        self._post = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ masks (canvas size, anti-aliased)
    def _blank(self, x0, y0, x1, y1, ss=2):
        x0, y0 = int(np.floor(x0)), int(np.floor(y0))
        x1, y1 = int(np.ceil(x1)) + 1, int(np.ceil(y1)) + 1
        x0, y0, x1, y1 = max(0, x0), max(0, y0), min(self.W, x1), min(self.H, y1)
        if x1 <= x0 or y1 <= y0: return None
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        return im, ImageDraw.Draw(im), x0, y0, x1, y1

    @staticmethod
    def _down(im, x0, y0, x1, y1):
        return np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255

    def _poly_crop(self, polys, smooth=False):
        polys = [np.asarray(_closed_spline(p) if smooth else p, np.float32) for p in polys]
        allp = np.vstack(polys)
        r = self._blank(allp[:, 0].min() - 2, allp[:, 1].min() - 2, allp[:, 0].max() + 2, allp[:, 1].max() + 2)
        if r is None: return np.zeros((1, 1), np.float32), 0, 0
        im, d, x0, y0, x1, y1 = r
        for p in polys:
            d.polygon([((x - x0) * 2, (y - y0) * 2) for x, y in p.tolist()], fill=255)
        return self._down(im, x0, y0, x1, y1), y0, x0

    def _expand(self, m, oy, ox):
        out = np.zeros((self.H, self.W), np.float32)
        out[oy:oy + m.shape[0], ox:ox + m.shape[1]] = m
        return out

    def poly(self, pts, smooth=False):
        """filled polygon (or a list of polygons); smooth=True runs a closed Catmull-Rom spline through the points"""
        polys = pts if (len(pts) and np.ndim(pts[0]) == 2) else [pts]
        return self._expand(*self._poly_crop(polys, smooth))

    def circle(self, cx, cy, r):
        m, oy, ox = self._dots_crop([(cx, cy)], r)
        return self._expand(m, oy, ox)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        x, y = np.cos(t) * rx, np.sin(t) * ry
        return self.poly(np.stack([cx + x * c - y * s, cy + x * s + y * c], 1))

    def rrect(self, x0, y0, x1, y1, r=0.0):
        rr = self._blank(x0 - 1, y0 - 1, x1 + 1, y1 + 1)
        im, d, bx, by, bx1, by1 = rr
        d.rounded_rectangle(((x0 - bx) * 2, (y0 - by) * 2, (x1 - bx) * 2, (y1 - by) * 2), r * 2, fill=255)
        return self._expand(self._down(im, bx, by, bx1, by1), by, bx)

    def band(self, pts, width, smooth=False):
        """a thick stroke along a polyline as a mask (roads, rivers, piers)"""
        m, oy, ox = self._lines_crop([pts], width, False, smooth, None, True)
        return self._expand(m, oy, ox)

    @staticmethod
    def circle_pts(cx, cy, r, ry=None, n=None, a0=0.0, a1=360.0):
        ry = r if ry is None else ry
        n = n or max(24, int(2 * np.pi * max(r, ry) / 3))
        t = np.deg2rad(np.linspace(a0, a1, n, endpoint=(a1 - a0) < 360))
        return np.stack([cx + np.cos(t) * r, cy + np.sin(t) * ry], 1)

    def edge(self, m, width=1.4):
        """the outline of a mask as a line mask of `width` px"""
        return _level(blur(m, 0.7), 0.5, width)

    def offset(self, m, d):
        """grow (d > 0) or shrink (d < 0) a mask by about d px, with rounded corners"""
        if d == 0: return m.copy()
        sig = abs(d) / 1.6
        f = blur(m, sig)
        t = 0.0548 if d > 0 else 1 - 0.0548
        gy, gx = np.gradient(f)
        g = np.sqrt(gx * gx + gy * gy) + 1e-5
        return np.clip(0.5 + (f - t) / g, 0, 1).astype(np.float32)

    def contour(self, m, d, width=1.2):
        """a line about d px outside (d > 0) or inside (d < 0) a mask's edge -- water-lining round a coast"""
        sig = max(0.7, abs(d) / 1.6)
        t = 0.0548 if d > 0 else 1 - 0.0548
        return _level(blur(m, sig), t, width)

    @staticmethod
    def inset(pts, d):
        """inset a convex polygon by d px (or a list of per-edge distances): a block inside its streets"""
        P = np.asarray(pts, np.float64); n = len(P)
        dd = np.full(n, d, np.float64) if np.isscalar(d) else np.asarray(d, np.float64)
        area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
        sgn = 1 if area > 0 else -1
        lines = []
        for i in range(n):
            a, b = P[i], P[(i + 1) % n]
            t = b - a; t /= np.linalg.norm(t) + 1e-9
            nrm = np.array([-t[1], t[0]]) * sgn                         # inward
            lines.append((a + nrm * dd[i], t))
        out = []
        for i in range(n):
            (p1, t1), (p2, t2) = lines[i - 1], lines[i]
            den = t1[0] * t2[1] - t1[1] * t2[0]
            if abs(den) < 1e-9: out.append(p2); continue
            s = ((p2[0] - p1[0]) * t2[1] - (p2[1] - p1[1]) * t2[0]) / den
            out.append(p1 + t1 * s)
        return np.array(out, np.float32)

    # ------------------------------------------------------------ raster helpers for sheets
    def _lines_crop(self, paths, width, closed, smooth, dash, cap, box=None):
        segs = []
        for p in paths:
            p = np.asarray(p, np.float32)
            if smooth and len(p) > 2:
                p = _closed_spline(p) if closed else spline(p, 8)
            if closed: p = np.vstack([p, p[:1]])
            if dash:
                seg = np.linalg.norm(np.diff(p, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
                on, off = dash; L = s[-1]; t = 0.0
                while t < L:
                    tt = np.linspace(t, min(t + on, L), max(2, int(on / 2)))
                    segs.append(np.stack([np.interp(tt, s, p[:, 0]), np.interp(tt, s, p[:, 1])], 1))
                    t += on + off
            else:
                segs.append(p)
        if not segs: return None, 0, 0
        allp = np.vstack(segs); pad = width + 3
        if box is None:
            box = (allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        r = self._blank(*box)
        if r is None: return None, 0, 0
        im, d, x0, y0, x1, y1 = r
        w2 = max(1, int(round(width * 2)))
        for p in segs:
            q = [((x - x0) * 2, (y - y0) * 2) for x, y in p.tolist()]
            if len(q) >= 2: d.line(q, fill=255, width=w2, joint='curve')
            if cap:
                for (x, y) in (q[0], q[-1]):
                    d.ellipse((x - w2 / 2, y - w2 / 2, x + w2 / 2, y + w2 / 2), fill=255)
        return self._down(im, x0, y0, x1, y1), y0, x0

    def _dots_crop(self, pts, r):
        pts = np.asarray(pts, np.float32).reshape(-1, 2)
        rr = self._blank(pts[:, 0].min() - r - 2, pts[:, 1].min() - r - 2, pts[:, 0].max() + r + 2, pts[:, 1].max() + r + 2)
        if rr is None: return None, 0, 0
        im, d, x0, y0, x1, y1 = rr
        for x, y in pts.tolist():
            d.ellipse(((x - x0 - r) * 2, (y - y0 - r) * 2, (x - x0 + r) * 2, (y - y0 + r) * 2), fill=255)
        return self._down(im, x0, y0, x1, y1), y0, x0

    def _text_crop(self, s, x, y, size, font_kind, anchor, spacing, rot, pad=4):
        f = font(font_kind, size)
        adv = [f.getlength(ch) + spacing for ch in s]
        total = sum(adv) - spacing if s else 0
        R = int(total + size * 2 + pad * 2)
        im = Image.new('L', (2 * R, 2 * R), 0); d = ImageDraw.Draw(im)
        if spacing:
            x0 = R - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
            for ch, a in zip(s, adv):
                d.text((x0, R), ch, font=f, fill=255, anchor='l' + anchor[1]); x0 += a
        else:
            d.text((R, R), s, font=f, fill=255, anchor=anchor)
        if rot:
            im = im.rotate(rot, resample=Image.BICUBIC, center=(R, R))
        a = np.asarray(im, np.float32) / 255
        ys, xs = np.nonzero(a > 0.002)
        if not len(xs): return None, 0, 0
        ya, yb, xa, xb = ys.min() - pad, ys.max() + pad + 1, xs.min() - pad, xs.max() + pad + 1
        ox, oy = int(round(x)) - R + xa, int(round(y)) - R + ya
        crop = a[max(ya, 0):yb, max(xa, 0):xb]
        # clip to canvas
        cy0, cx0 = max(0, -oy), max(0, -ox)
        crop = crop[cy0:, cx0:]
        oy, ox = oy + cy0, ox + cx0
        crop = crop[:max(0, self.H - oy), :max(0, self.W - ox)]
        return crop, oy, ox

    # ------------------------------------------------------------ the set: desk, light box, pegs, tape
    def desk(self, colour='#3a3530'):
        """the dark desk the light box stands on (fine grain, faint horizontal streaks)"""
        H, W = self.H, self.W
        s = self._seed()
        base = hexc(colour)
        grain = 0.75 * noise2d(H, W, 3, 2, s) + 0.25 * noise2d(H, W, 60, 2, s + 1)
        streak = np.interp(np.arange(H), np.linspace(0, H - 1, 140), self.rng.random(140))[:, None]
        self.bg = base * (0.86 + 0.18 * grain + 0.06 * streak)[..., None]

    def lightbox(self, x0, y0, x1, y1, radius=28, bezel=18, colour='#4b4743'):
        """the case (bevelled, darker toward the bottom, a soft shadow on the desk) and its opal panel"""
        H, W = self.H, self.W
        case = self.rrect(x0, y0, x1, y1, radius)
        sh = blur(shift(case, 0, 26), 30)
        self.bg *= (1 - 0.55 * sh * (1 - case))[..., None]
        Y = np.arange(H, dtype=np.float32)[:, None]
        g = np.clip((Y - y0) / max(1, y1 - y0), 0, 1)
        col = hexc(colour) * (1.12 - 0.42 * g)[..., None] * np.ones((1, W, 1), np.float32)
        col *= (0.97 + 0.04 * noise2d(H, W, 2.0, 2, self._seed()))[..., None]
        self.bg = self.bg * (1 - case[..., None]) + col * case[..., None]
        top = _level(blur(case, 0.8), 0.5, 1.2) * (Y < y0 + radius)
        self.bg += (top * 0.22)[..., None]
        self.box = (x0 + bezel, y0 + bezel, x1 - bezel, y1 - bezel)
        self.panel = self.rrect(*self.box, 12)
        self._E = {}

    def lamp(self, level=1.0):
        """0 = off (grey opal acrylic in room light) .. 1 = on (warm white). In between it is dim and warmer"""
        self.level = float(level)

    def _emission(self):
        key = round(self.level, 3)
        if key in self._E: return self._E[key]
        H, W = self.H, self.W
        x0, y0, x1, y1 = self.box
        Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.hypot((X - (x0 + 0.42 * (x1 - x0))) / ((x1 - x0) * 0.70), (Y - (y0 + 0.46 * (y1 - y0))) / ((y1 - y0) * 0.80))
        stops = [(0.0, '#ffffff'), (0.45, '#fffdf9'), (0.75, '#fcf7ee'), (1.0, '#f6ecdc'), (1.6, '#efe0c8')]
        on = np.zeros((H, W, 3), np.float32)
        for k in range(3):
            on[..., k] = np.interp(r, [p for p, _ in stops], [hexc(c)[k] for _, c in stops])
        on *= 0.985
        off = hexc('#9c968c') * (1.0 - 0.10 * np.clip(r, 0, 1.4))[..., None]
        lv = self.level
        warm = np.array([1.0, 1 - 0.06 * (1 - lv), 1 - 0.20 * (1 - lv)], np.float32)
        E = off * (1 - lv) + on * warm * lv ** 0.8
        E *= (1 + 0.005 * (noise2d(H, W, 24, 2, self.seed + 17) - 0.5))[..., None]
        # the panel sits in a recess: a dark line round it, and when lit a warm spill onto the bezel
        pm = self.panel
        lip = self.edge(pm, 2.0)
        spill = np.clip(blur(pm, 9) - pm, 0, 1) * 0.55 * lv
        img = self.bg * (1 - pm[..., None]) + E * pm[..., None]
        img = img + (spill[..., None] * np.array([1.0, 0.86, 0.62], np.float32) * 0.45)
        img *= (1 - 0.55 * lip)[..., None]
        img *= (1 - 0.10 * np.clip(blur(1 - pm, 6) * pm * 2, 0, 1))[..., None]
        self._E[key] = img.astype(np.float32)
        return self._E[key]

    def peg_bar(self, x0, x1, y0, y1, pegs=(), screws=True):
        """a steel peg bar lying on the light box (opaque, lit by the room). pegs: ('round', x, y, r) and
        ('slot', x, y, w, h); give the same points to `Sheet.punch` / `punch_slot` so sheets drop onto them"""
        H, W = self.H, self.W
        bar = self.rrect(x0, y0, x1, y1, 6)
        Y = np.arange(H, dtype=np.float32)[:, None] * np.ones((1, W), np.float32)
        X = np.ones((H, 1), np.float32) * np.arange(W, dtype=np.float32)[None, :]
        g = np.clip((Y - y0) / max(1, y1 - y0), 0, 1)
        steel = np.stack([np.interp(g, [0, 0.45, 1], [hexc(c)[k] for c in ('#f4f3f0', '#d3d0ca', '#a7a39c')]) for k in range(3)], -1)
        col = steel * (1 + 0.02 * (noise2d(H, W, 1.2, 1, self._seed())[..., None] - 0.5))
        alpha = bar.copy()
        col = col * (1 - 0.45 * self.edge(bar, 1.0)[..., None])
        col += (np.exp(-((Y - y0 - 2.5) / 0.8) ** 2) * bar * 0.12)[..., None]
        for p in pegs:
            if p[0] == 'round':
                _, px, py, pr = p
                m = self.circle(px, py, pr)
                rr = np.clip(np.hypot(X - (px - pr * 0.25), Y - (py - pr * 0.3)) / (pr * 1.5), 0, 1)
                c = hexc('#fbfaf8') * (1 - rr)[..., None] + hexc('#9d988f') * rr[..., None]
            else:
                _, px, py, pw, ph = p
                m = self.rrect(px - pw / 2, py - ph / 2, px + pw / 2, py + ph / 2, ph / 2)
                gg = np.clip((Y - (py - ph / 2)) / ph, 0, 1)
                c = np.stack([np.interp(gg, [0, 0.35, 1], [hexc(cc)[k] for cc in ('#fbfaf8', '#d8d5cf', '#9d988f')]) for k in range(3)], -1)
            c = c * (1 - 0.5 * self.edge(m, 1.0)[..., None])
            col = col * (1 - m[..., None]) + np.clip(c, 0, 1) * m[..., None]
            alpha = np.maximum(alpha, m)
        if screws:
            for sx in (x0 + 18, x1 - 18):
                sy = (y0 + y1) / 2
                m = self.circle(sx, sy, 5)
                col = col * (1 - m[..., None]) + hexc('#bdb9b2') * m[..., None]
                col = col * (1 - 0.6 * (self.edge(m, 0.9) + self.band([(sx - 3, sy), (sx + 3, sy)], 1.0) * m))[..., None]
        shadow = blur(shift(alpha, 4, 6), 3.0) * 0.35
        self.items.append(dict(kind='opaque', rgb=np.clip(col, 0, 1).astype(np.float32), alpha=alpha, shadow=shadow))

    def tape(self, cx, cy, w=84.0, h=28.0, rot=0.0, colour=TAPE):
        """a strip of crepe drafting tape with torn ends, pressed down on top of everything"""
        n = 8
        t = np.deg2rad(rot)
        u = np.array([np.cos(t), np.sin(t)], np.float32); v = np.array([-np.sin(t), np.cos(t)], np.float32)
        rng = self.rng
        pts = []
        for i in range(n + 1):                                          # torn left end, top to bottom
            jag = (rng.uniform(0.0, 0.06) if i % 2 else rng.uniform(0.0, 0.015)) * w
            pts.append((-w / 2 + jag, -h / 2 + h * i / n))
        for i in range(n, -1, -1):                                      # torn right end, bottom to top
            jag = (rng.uniform(0.0, 0.06) if i % 2 else rng.uniform(0.0, 0.015)) * w
            pts.append((w / 2 - jag, -h / 2 + h * i / n))
        P = [(cx + a * u[0] + b * v[0], cy + a * u[1] + b * v[1]) for a, b in pts]
        m = self.poly(P)
        x0, y0 = int(max(0, min(p[0] for p in P) - 4)), int(max(0, min(p[1] for p in P) - 4))
        x1, y1 = int(min(self.W, max(p[0] for p in P) + 5)), int(min(self.H, max(p[1] for p in P) + 5))
        sl = (slice(y0, y1), slice(x0, x1))
        hh, ww = y1 - y0, x1 - x0
        s = self._seed()
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        along = (X - cx) * u[0] + (Y - cy) * u[1]; across = (Y - cy) * v[1] + (X - cx) * v[0]
        crepe = np.sin(along * 0.9 + 2.0 * noise2d(hh, ww, 8, 2, s)) * 0.5 + 0.5
        fib = noise2d(hh, ww, 2.0, 2, s + 1)
        side = np.clip(np.abs(across) / (h / 2), 0, 1)
        T = _c(colour) * (1.0 - 0.03 * crepe - 0.04 * (fib - 0.5))[..., None]
        T = T * (1 - 0.08 * side ** 6)[..., None]
        self.items.append(dict(kind='tape', sl=sl, m=m[sl], T=np.clip(T, 0, 1).astype(np.float32),
                               shadow=(blur(shift(m, 1, 2), 1.4) * 0.16)))

    # ------------------------------------------------------------ sheets
    def sheet(self, x, y, w, h, kind='tracing', ink='blue', tint=None, fibre=None, curl=None, seed=None, edge=None):
        """a new sheet at its laid-down position (x, y, w, h). kind: base | tracing | drafting | film;
        ink: the plate this sheet prints by default (a name from INKS or '#rrggbb'); curl: 'br' or ('br', 80)"""
        return Sheet(self, x, y, w, h, kind, ink, tint, fibre, curl, seed if seed is not None else self._seed(), edge)

    def place(self, sheet, lift=0.0, dx=0.0, dy=0.0, rot=0.0):
        """show a sheet: laid down (all zero), or lifted `lift` (0..1) and held off by dx, dy px and rot degrees
        (counter-clockwise). The first place() puts the sheet on top of everything placed so far"""
        sheet.state = (float(lift), float(dx), float(dy), float(rot))
        if not any(it is sheet for it in self.items):
            k = len(self.items)
            while k > 0 and isinstance(self.items[k - 1], dict) and self.items[k - 1]['kind'] == 'tape':
                k -= 1
            self.items.insert(k, sheet)

    def remove(self, sheet):
        self.items = [it for it in self.items if it is not sheet]

    def _warp(self, sheet, arrs):
        """sample local arrays at the sheet's current pose -> canvas box (sl, list of arrays)"""
        lift, dx, dy, rot = sheet.state
        s = 1 + 0.03 * lift
        if lift == 0 and dx == 0 and dy == 0 and rot == 0:
            sl = (slice(sheet.y0, sheet.y0 + sheet.h), slice(sheet.x0, sheet.x0 + sheet.w))
            return sl, arrs
        w, h = sheet.w, sheet.h
        Cx, Cy = sheet.x0 + w / 2 + dx, sheet.y0 + h / 2 + dy
        th = np.deg2rad(rot); c, si = np.cos(th), np.sin(th)
        corners = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]]) * s
        P = np.stack([Cx + corners[:, 0] * c + corners[:, 1] * si, Cy - corners[:, 0] * si + corners[:, 1] * c], 1)
        bx0, by0 = int(max(0, np.floor(P[:, 0].min()) - 2)), int(max(0, np.floor(P[:, 1].min()) - 2))
        bx1, by1 = int(min(self.W, np.ceil(P[:, 0].max()) + 2)), int(min(self.H, np.ceil(P[:, 1].max()) + 2))
        # local = c_local + R^T (P - C) / s, R = [[c, si], [-si, c]]
        a, b = c / s, -si / s
        d_, e = si / s, c / s
        cc = w / 2 + a * (bx0 - Cx) + b * (by0 - Cy)
        f = h / 2 + d_ * (bx0 - Cx) + e * (by0 - Cy)
        out = []
        for arr in arrs:
            if arr.ndim == 3:
                out.append(np.stack([self._warp1(arr[..., k], (a, b, cc, d_, e, f), bx1 - bx0, by1 - by0) for k in range(arr.shape[2])], -1))
            else:
                out.append(self._warp1(arr, (a, b, cc, d_, e, f), bx1 - bx0, by1 - by0))
        return (slice(by0, by1), slice(bx0, bx1)), out

    @staticmethod
    def _warp1(a, data, ww, hh):
        return np.asarray(Image.fromarray(np.ascontiguousarray(a, np.float32), 'F').transform(
            (ww, hh), Image.AFFINE, data, resample=Image.BILINEAR), np.float32)

    # ------------------------------------------------------------ render
    def render(self):
        """the photograph of the light box as it is now (float H x W x 3)"""
        if self.panel is None:
            self.lightbox(34, 24, self.W - 34, self.H - 24)
        I = self._emission().copy()
        Eavg = 0.95 * self.level + 0.55 * (1 - self.level)
        for it in self.items:
            if isinstance(it, dict):
                if it['kind'] == 'opaque':
                    I *= 1 - it['shadow'][..., None] * (1 - np.array(SHADOW, np.float32))
                    a = it['alpha'][..., None]
                    room = 0.55 + 0.45 * self.level                                     # the room is lit a little by the box
                    I = I * (1 - a) + it['rgb'] * room * a
                elif it['kind'] == 'tape':
                    I *= (1 - it['shadow'][..., None] * (1 - np.array(SHADOW, np.float32)))
                    sl, m = it['sl'], it['m'][..., None]
                    T = it['T']
                    lit = I[sl] * T * 0.58 + T * 0.36 * (0.55 + 0.45 * self.level)       # crepe paper: half seen through, half lit by the room
                    I[sl] = I[sl] * (1 - m) + lit * m
                continue
            sheet = it
            if sheet.state is None: continue
            lift, dx, dy, rot = sheet.state
            C = sheet._build()
            arrs = [C['A'], C['F'], C['cw'], C['csh']] + ([C['sheen']] if C['sheen'] is not None else [])
            sl, warped = self._warp(sheet, arrs)
            A, F, cw, csh = warped[:4]
            sheen = warped[4] if len(warped) > 4 else None
            Fc = np.zeros((self.H, self.W), np.float32); Fc[sl] = F
            sh_col = 1 - np.array(SHADOW, np.float32)
            # 1. a lifted diffuser blurs what is under it (and a curled corner, a little, under its tip)
            if lift > 0.01:
                sub = I[sl]
                r = sheet.P['diffuse'] * lift
                sb = np.stack([blur(sub[..., k], r) for k in range(3)], -1)
                I[sl] = sub + (sb - sub) * F[..., None]
            if cw.max() > 0:
                sub = I[sl]
                sb = np.stack([blur(sub[..., k], 2.2) for k in range(3)], -1)
                I[sl] = sub + (sb - sub) * (cw * F)[..., None]
            # 2. shadows: wide and soft while lifted (seen through the sheet), a thin contact line once down
            if lift > 0.01:
                ox, oy = 3 + 16 * lift, 4 + 30 * lift
                sh = blur(shift(Fc, ox, oy), 2.5 + 16 * lift) * 0.22 * lift
                sh *= 1 - 0.55 * Fc                                          # under the sheet the room light still gets through
                I *= (1 - sh[..., None] * sh_col)
            down = 1 - min(1.0, lift)
            if down > 0:
                sh = (blur(shift(Fc, 1, 1.5), 1.3) * 0.30 + blur(shift(Fc, 2, 3.5), 4.5) * 0.09) * (1 - Fc) * down
                I *= (1 - sh[..., None] * sh_col)
            if csh.max() > 0:
                I[sl] *= (1 - (csh * F)[..., None] * sh_col)
            # 3. the sheet: transmittance, plus the frost of tracing paper (scattered light lifts the darks)
            sub = I[sl]
            T = 1 - A
            v = sheet.P['frost'] * (1 - 0.5 * min(1.0, lift))
            out = sub * T
            if v > 0:
                out = out * (1 - v * F[..., None]) + (v * F)[..., None] * T * Eavg
            if sheen is not None:
                out = 1 - (1 - out) * (1 - (sheen * F)[..., None] * (0.4 + 0.6 * self.level))
            I[sl] = out
        return I

    def composite(self):
        I = self.render()
        if self._post is None:
            H, W = self.H, self.W
            Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.hypot((X - W / 2) / W, (Y - H / 2) / H)
            vig = 1 - 0.07 * r ** 2 * 2.2
            grain = 1 + 0.010 * (noise2d(H, W, 1.0, 1, self.seed + 99) - 0.5)
            self._post = (vig * grain).astype(np.float32)
        I = I * self._post[..., None]
        return Image.fromarray((np.clip(I, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        if self.keep_stages:
            self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f'{stages_dir}/{i:02d}_{name}.png')
            img.save(f'{stages_dir}/{len(self.stages):02d}_final.png')
        return img
