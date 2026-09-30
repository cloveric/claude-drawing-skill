"""flatvector — modern flat vector illustration: geometric shapes, no outlines, a small saturated palette, volume
built from overlapping blocks of flat colour, a whisper of print grain, and faceless grown-up people
(numpy + Pillow only).

Model: an artboard in a vector app, not a canvas with paint on it.
  shapes     every mark is a closed geometric shape with a crisp anti-aliased edge: circles, ellipses, rounded
             rectangles (per-corner radii), tapered capsules (limbs, stems, cords), polygons whose corners are
             filleted with true arcs, ring segments and pies, leaves (a vesica between two points). A shape is a
             `Mask`: a coverage patch plus its offset on the artboard, so union `|`, intersection `&`,
             difference `-` and `moved()` only touch the overlap of bounding boxes -- a picture of a thousand
             shapes stays fast.
  no lines   there are no outlines. Two neighbouring shapes are told apart only by value and hue, so every
             object is planned against what sits behind it (a cream shelf on a blue wall, a mustard coat on a
             cream shelf). Thin things (cords, rails, steam, dashes) are themselves filled capsules.
  palette    five to seven flat hues (here INK, BLUE, CORAL, MUSTARD, TEAL, PEACH, CREAM). Every other colour
             is a *tone* of one of them: `tone(c, -k)` mixes toward the palette's ink, `tone(c, +k)` toward its
             cream. Shadows are never grey or black -- they are the ink mixed in, so they stay in the family.
  volume     flat colour blocks stacked on top of each other, the way you would cut them in a vector app:
             `shade()` lays a darker block on the side away from the light, cut out as "the shape minus a
             copy of itself nudged toward the light" (a crisp crescent that follows the silhouette);
             `plane()` cuts an object with a straight line (the side face of a box, the dark half of a leaf);
             `glint()` is the same crescent in a lighter tone on the lit side; `cast()` drops a hard-edged
             flat shadow onto whatever is already underneath (it multiplies by an ink tint, so a shadow that
             falls across three colours darkens each in its own hue). No gradients, no blur.
  light      a lamp's beam or a patch of low sun is one translucent flat shape (`fill(..., alpha)`), its alpha
             lightly broken by grain so it reads as light, not as a pane of glass.
  grain      the finished artboard gets a very light monochrome print grain (about 1% in value, a little
             clumpy), just enough to stop large flat fields looking like a screen.
  people     simplified, faceless, adult proportions (7.5 heads tall): a skeleton of hip, shoulders, elbows,
             wrists, knees and ankles driven by joint angles, or by hand / foot targets (two-bone IK: elbows
             drop, knees go forward); a 3/4 torso (shoulders wider than waist, rounded
             shoulder fillets), tapered limbs, mitten hands, flat shoes; a head that is one ellipse whose hair
             is "a slightly bigger ellipse minus the face ellipse nudged forward and down" (plus a bun, bob,
             long panel or pony). The far arm and far leg are one tone darker, so the body turns in space
             without a single line. Clothes: top, trousers or skirt, coat, apron, tote bag.
  objects    a row of book spines (varied heights and widths, bands and a title dash in tones of the spine's
             own colour, a pile lying flat, the neighbour of a taken-out book tipped into the gap, the last book
             of a short row leaning on the side panel, each dropping a flat shadow on the shelf back), a single
             book (closed or open),
             potted plants (split two-tone leaves), a pendant lamp with a flat beam, a sitting cat, clouds,
             sun, dashed motion paths, four-point sparkles, and set lettering (geometric sans + CJK sans).
Angles: `rot` for shapes is degrees counter-clockwise; a person's joint angles are degrees measured from
"straight down", positive toward the way the person faces.

    from flatvector import FlatVector, INK, BLUE, CORAL, MUSTARD, TEAL, PEACH, CREAM
    fv = FlatVector(1920, 1080, seed=3)
    fv.backdrop(BLUE)
    floor = fv.rect(0, 880, 1920, 1080); fv.fill(floor, fv.tone(MUSTARD, -0.3))
    sofa = fv.rrect(1200, 700, 1700, 900, (60, 60, 12, 12)); fv.cast(sofa, 30, 0, clip=floor); fv.fill(sofa, TEAL)
    fv.shade(sofa, 0.2, depth=40)                          # a darker block on the side away from the light
    p = fv.person((1450, 760), 400, facing=-1, sit=True, top=CORAL, hair_style='bun')
    fv.book(*p['hand'], 90, 60, rot=10, colour=MUSTARD, open=True)
    fv.pendant(1450, 0, 320, 70, beam_to=(1300, 1600, 760))
    fv.text('周末 WEEKEND', 120, 160, 64, CREAM)
    fv.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, spline, noise2d, load_font

INK, BLUE, CORAL, MUSTARD, TEAL, PEACH, CREAM = '#1e1b45', '#3346d3', '#ff6150', '#ffb838', '#19b39a', '#f6b39b', '#fbf1df'
PALETTE = dict(ink=INK, blue=BLUE, coral=CORAL, mustard=MUSTARD, teal=TEAL, peach=PEACH, cream=CREAM)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str): return hexc(PALETTE.get(c, c))
    return np.asarray(c, np.float32)


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


# ---------------------------------------------------------------- fonts (local list; falls back to core.load_font)
_FONTS = {
    'geo': [('/System/Library/Fonts/Supplemental/Futura.ttc', 2), ('/System/Library/Fonts/Avenir Next.ttc', 0),
            ('/usr/share/fonts/**/URWGothic-Demi.*', 0), ('/usr/share/fonts/**/Montserrat-Bold.ttf', 0),
            ('C:/Windows/Fonts/GOTHICB.TTF', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'geo_medium': [('/System/Library/Fonts/Supplemental/Futura.ttc', 0), ('/System/Library/Fonts/Avenir Next.ttc', 5),
                   ('/usr/share/fonts/**/URWGothic-Book.*', 0), ('C:/Windows/Fonts/GOTHIC.TTF', 0), ('C:/Windows/Fonts/arial.ttf', 0)],
    'cjk': [('/System/Library/Fonts/Hiragino Sans GB.ttc', 2), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
            ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSansCJK*.tt[cf]', 0),
            ('C:/Windows/Fonts/msyhbd.ttc', 0), ('C:/Windows/Fonts/msyh.ttc', 0)],
    'cjk_light': [('/System/Library/Fonts/Hiragino Sans GB.ttc', 0), ('/System/Library/Fonts/STHeiti Light.ttc', 1),
                  ('/usr/share/fonts/**/NotoSansCJK*Regular*.tt[cf]', 0), ('C:/Windows/Fonts/msyh.ttc', 0)],
}
_FONT_CACHE = {}


def font(style, size):
    """PIL font for 'geo' (geometric sans bold), 'geo_medium', 'cjk' (CJK sans bold), 'cjk_light';
    any other name goes to core.load_font (sans, sans_bold, rounded, ...). $INKPAINT_FONT_<STYLE> overrides."""
    key = (style, int(size))
    if key in _FONT_CACHE: return _FONT_CACHE[key]
    f = None
    env = os.environ.get('INKPAINT_FONT_' + style.upper())
    cands = ([(env, 0)] if env and os.path.exists(env) else []) + _FONTS.get(style, [])
    for pat, idx in cands:
        for p in glob.glob(pat, recursive=True):
            try:
                f = ImageFont.truetype(p, int(size), index=idx); break
            except OSError:
                pass
        if f: break
    if f is None:
        f = load_font({'geo': 'sans_bold', 'geo_medium': 'sans', 'cjk': 'cjk_sans', 'cjk_light': 'cjk_sans'}.get(style, style), size)
    _FONT_CACHE[key] = f
    return f


# ---------------------------------------------------------------- Mask: a coverage patch with an offset
class Mask:
    """anti-aliased coverage `a` (0..1, float32) whose top-left pixel sits at artboard (x0, y0).
    a | b union, a & b intersection, a - b difference, a * k fade, a.moved(dx, dy) nudge (free)."""
    __slots__ = ('a', 'x0', 'y0')

    def __init__(self, a, x0=0, y0=0):
        self.a, self.x0, self.y0 = np.asarray(a, np.float32), int(x0), int(y0)

    @property
    def x1(self): return self.x0 + self.a.shape[1]

    @property
    def y1(self): return self.y0 + self.a.shape[0]

    @property
    def empty(self): return self.a.size == 0 or not self.a.any()

    def on(self, x0, y0, x1, y1):
        """this mask sampled on the box [x0, x1) x [y0, y1) (zero outside itself)"""
        out = np.zeros((max(0, y1 - y0), max(0, x1 - x0)), np.float32)
        ix0, iy0, ix1, iy1 = max(x0, self.x0), max(y0, self.y0), min(x1, self.x1), min(y1, self.y1)
        if ix1 > ix0 and iy1 > iy0:
            out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = self.a[iy0 - self.y0:iy1 - self.y0, ix0 - self.x0:ix1 - self.x0]
        return out

    def __or__(self, o):
        if o is None or o.a.size == 0: return self
        if self.a.size == 0: return o
        b = (min(self.x0, o.x0), min(self.y0, o.y0), max(self.x1, o.x1), max(self.y1, o.y1))
        return Mask(np.maximum(self.on(*b), o.on(*b)), b[0], b[1])

    def __and__(self, o):
        b = (max(self.x0, o.x0), max(self.y0, o.y0), min(self.x1, o.x1), min(self.y1, o.y1))
        if b[2] <= b[0] or b[3] <= b[1]: return Mask(np.zeros((0, 0)), 0, 0)
        return Mask(self.on(*b) * o.on(*b), b[0], b[1])

    def __sub__(self, o):
        if o is None or o.a.size == 0: return self
        return Mask(self.a * (1 - o.on(self.x0, self.y0, self.x1, self.y1)), self.x0, self.y0)

    def __mul__(self, k):
        return Mask(self.a * k, self.x0, self.y0)

    def moved(self, dx, dy):
        return Mask(self.a, self.x0 + int(round(dx)), self.y0 + int(round(dy)))

    def grown(self, r):
        """dilate (r > 0) or erode (r < 0) by about |r| px, keeping a crisp edge"""
        p = int(abs(r)) + 3
        a = np.pad(self.a, p)
        b = blur(a, abs(r) * 0.6 + 0.5)
        t = 0.5 - 0.42 * np.sign(r) * min(1.0, abs(r) / (abs(r) + 1.2))
        return Mask(np.clip((b - t) * 3.0 + 0.5, 0, 1) if r else a, self.x0 - p, self.y0 - p)

    @staticmethod
    def union(*ms):
        out = Mask(np.zeros((0, 0)))
        for m in ms: out = out | m
        return out


def _fillet(pts, r, n=10):
    """polygon with every corner replaced by a true circular arc of radius r (scalar or per-vertex list)"""
    P = np.asarray(pts, np.float64)
    k = len(P)
    rs = np.broadcast_to(np.asarray(r, np.float64), (k,))
    out = []
    for i in range(k):
        p, a, b = P[i], P[i - 1], P[(i + 1) % k]
        if rs[i] <= 0.5:
            out.append(p); continue
        u, v = a - p, b - p
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        if lu < 1e-6 or lv < 1e-6:
            out.append(p); continue
        u, v = u / lu, v / lv
        th = np.arccos(np.clip(u @ v, -1, 1))
        if th < 1e-3 or th > np.pi - 1e-3:
            out.append(p); continue
        t = min(rs[i] / np.tan(th / 2), 0.5 * lu, 0.5 * lv)
        rr = t * np.tan(th / 2)
        w = (u + v) / np.linalg.norm(u + v)
        c = p + w * rr / np.sin(th / 2)
        t1, t2 = p + u * t, p + v * t
        for s in np.linspace(0, 1, n):
            q = t1 * (1 - s) + t2 * s - c
            out.append(c + q / (np.linalg.norm(q) + 1e-9) * rr)
    return np.array(out)


class FlatVector:
    def __init__(self, W=1920, H=1080, seed=0, light=(0.8, -0.6), ink=INK, cream=CREAM):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.img = np.ones((H, W, 3), np.float32)
        self.ink, self.cream = _c(ink), _c(cream)
        l = np.asarray(light, np.float32)
        self.light = l / (np.linalg.norm(l) + 1e-9)            # unit vector pointing toward the light (screen)
        self._noise = None
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ colour
    def tone(self, c, k):
        """a tone of palette colour c: k < 0 mixes toward the ink (shade), k > 0 toward the cream (tint)"""
        c = _c(c)
        return c + (self.ink - c) * (-k) if k < 0 else c + (self.cream - c) * k

    @staticmethod
    def mix(a, b, t):
        return _c(a) * (1 - t) + _c(b) * t

    # ------------------------------------------------------------ shape masks
    def _grid(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0)) - 2), max(0, int(np.floor(y0)) - 2)
        x1, y1 = min(self.W, int(np.ceil(x1)) + 2), min(self.H, int(np.ceil(y1)) + 2)
        if x1 <= x0 or y1 <= y0: return None
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        return X + 0.5, Y + 0.5, x0, y0

    @staticmethod
    def _cov(d):
        return np.clip(0.5 - d, 0, 1).astype(np.float32)

    def _mk(self, g, d):
        if g is None: return Mask(np.zeros((0, 0)))
        return Mask(self._cov(d), g[2], g[3])

    def circle(self, cx, cy, r):
        g = self._grid(cx - r, cy - r, cx + r, cy + r)
        return self._mk(g, None if g is None else np.hypot(g[0] - cx, g[1] - cy) - r)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        R = max(rx, ry)
        g = self._grid(cx - R, cy - R, cx + R, cy + R)
        if g is None: return self._mk(g, None)
        t = np.deg2rad(rot)
        dx, dy = g[0] - cx, g[1] - cy
        u, v = dx * np.cos(t) - dy * np.sin(t), dx * np.sin(t) + dy * np.cos(t)
        k0 = np.hypot(u / rx, v / ry)
        k1 = np.hypot(u / rx ** 2, v / ry ** 2) + 1e-9
        return self._mk(g, k0 * (k0 - 1) / k1)

    def rect(self, x0, y0, x1, y1):
        return self.rrect(x0, y0, x1, y1, 0)

    def rrect(self, x0, y0, x1, y1, r=0, rot=0.0):
        """rounded rectangle; r scalar or (top-left, top-right, bottom-right, bottom-left); rot about its centre"""
        cx, cy, hw, hh = (x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0) / 2, abs(y1 - y0) / 2
        R = np.hypot(hw, hh) if rot else 0
        g = self._grid(cx - (R or hw), cy - (R or hh), cx + (R or hw), cy + (R or hh))
        if g is None: return self._mk(g, None)
        t = np.deg2rad(rot)
        dx, dy = g[0] - cx, g[1] - cy
        u, v = dx * np.cos(t) - dy * np.sin(t), dx * np.sin(t) + dy * np.cos(t)
        rs = np.broadcast_to(np.asarray(r, np.float32), (4,))
        rr = np.where(v < 0, np.where(u < 0, rs[0], rs[1]), np.where(u < 0, rs[3], rs[2]))
        rr = np.minimum(rr, min(hw, hh))
        qx, qy = np.abs(u) - hw + rr, np.abs(v) - hh + rr
        d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rr
        return self._mk(g, d)

    def capsule(self, p0, p1, r0, r1=None):
        """a bar with round ends from p0 (radius r0) to p1 (radius r1): limbs, stems, cords, dashes"""
        r1 = r0 if r1 is None else r1
        (ax, ay), (bx, by) = p0, p1
        R = max(r0, r1)
        g = self._grid(min(ax, bx) - R, min(ay, by) - R, max(ax, bx) + R, max(ay, by) + R)
        if g is None: return self._mk(g, None)
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy + 1e-9
        t = np.clip(((g[0] - ax) * dx + (g[1] - ay) * dy) / L2, 0, 1)
        d = np.hypot(g[0] - ax - t * dx, g[1] - ay - t * dy) - (r0 + (r1 - r0) * t)
        return self._mk(g, d)

    def limb(self, pts, radii):
        """a chain of tapered capsules through pts with a radius per point (arms, legs, tails)"""
        m = Mask(np.zeros((0, 0)))
        for i in range(len(pts) - 1):
            m = m | self.capsule(pts[i], pts[i + 1], radii[i], radii[i + 1])
        return m

    def tube(self, pts, r, per=10):
        """a smooth capsule along a Catmull-Rom curve (cords, tails, steam)"""
        P = spline(pts, per) if len(pts) > 2 else np.asarray(pts, np.float32)
        rr = np.broadcast_to(np.asarray(r, np.float32), (len(P),)) if np.ndim(r) == 0 else np.interp(
            np.linspace(0, 1, len(P)), np.linspace(0, 1, len(r)), r)
        return self.limb(P, rr)

    def poly(self, pts, round=0, ss=4):
        """filled polygon; `round` fillets every corner (scalar or one radius per vertex) with a true arc"""
        P = _fillet(pts, round) if np.any(np.asarray(round) > 0) else np.asarray(pts, np.float64)
        x0, y0 = P.min(0); x1, y1 = P.max(0)
        g = self._grid(x0, y0, x1, y1)
        if g is None: return Mask(np.zeros((0, 0)))
        gx, gy = g[2], g[3]
        w, h = g[0].shape[1], g[0].shape[0]
        im = Image.new('L', (w * ss, h * ss), 0)
        ImageDraw.Draw(im).polygon([((x - gx) * ss, (y - gy) * ss) for x, y in P], fill=255)
        a = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        return Mask(a, gx, gy)

    def arc(self, cx, cy, r0, r1, a0, a1):
        """ring segment between radii r0 < r1, from angle a0 to a1 (degrees, counter-clockwise from +x)"""
        g = self._grid(cx - r1, cy - r1, cx + r1, cy + r1)
        if g is None: return self._mk(g, None)
        dx, dy = g[0] - cx, -(g[1] - cy)
        rad = np.hypot(dx, dy)
        dr = np.maximum(r0 - rad, rad - r1)
        mid, half = np.deg2rad((a0 + a1) / 2), np.deg2rad(abs(a1 - a0) / 2)
        ang = np.abs((np.arctan2(dy, dx) - mid + np.pi) % (2 * np.pi) - np.pi)
        da = (ang - half) * np.maximum(rad, 1)
        return self._mk(g, np.maximum(dr, da))

    def pie(self, cx, cy, r, a0, a1):
        return self.arc(cx, cy, -1, r, a0, a1)

    def leaf(self, p0, p1, width, bend=0.0, n=28):
        """a leaf / petal: a pointed vesica from base p0 to tip p1, `bend` bows it sideways (px)"""
        p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
        d = p1 - p0; L = np.linalg.norm(d) + 1e-9
        nrm = np.array([-d[1], d[0]]) / L
        t = np.linspace(0, 1, n)
        spine = p0 + d * t[:, None] + nrm * (4 * t * (1 - t) * bend)[:, None]
        w = width / 2 * np.sin(np.pi * t) ** 0.75 * (1 - 0.25 * t)
        left = spine + nrm * w[:, None]; right = spine - nrm * w[:, None]
        return self.poly(np.vstack([left, right[::-1]]))

    def star(self, cx, cy, r, points=4, inner=0.28, rot=0.0):
        """a sparkle / star polygon"""
        a = np.deg2rad(rot) + np.arange(points * 2) * np.pi / points - np.pi / 2
        rr = np.where(np.arange(points * 2) % 2 == 0, r, r * inner)
        return self.poly(np.stack([cx + rr * np.cos(a), cy + rr * np.sin(a)], 1), round=r * 0.04)

    def split(self, m, p0, p1):
        """the part of m on the left of the line p0 -> p1 as you walk along it on screen
        (a line drawn left -> right keeps what is above it; top -> bottom keeps what is to its right)"""
        if m.a.size == 0: return m
        Y, X = np.mgrid[m.y0:m.y1, m.x0:m.x1].astype(np.float32)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = np.hypot(dx, dy) + 1e-9
        d = -((X + 0.5 - p0[0]) * dy - (Y + 0.5 - p0[1]) * dx) / L
        return Mask(m.a * self._cov(d), m.x0, m.y0)

    def text_mask(self, s, x, y, size, font_style='geo', anchor='ls', spacing=0.0, cjk='cjk'):
        """set lettering as a mask. Latin runs use `font_style`, CJK runs `cjk`; anchor: l/m/r + s (baseline)/m"""
        runs = []
        for ch in s:
            st = cjk if _is_cjk(ch) else font_style
            if runs and runs[-1][0] == st: runs[-1][1] += ch
            else: runs.append([st, ch])
        adv = []
        for st, t in runs:
            f = font(st, size)
            adv.append(sum(f.getlength(ch) + spacing for ch in t))
        total = sum(adv) - spacing
        x0 = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        if anchor[1] == 'm':
            y = y + size * 0.36
        pad = int(size * 0.6) + 4
        bx0, by0 = int(x0) - pad, int(y - size * 1.3) - pad
        w, h = int(total) + 2 * pad, int(size * 1.9) + 2 * pad
        im = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(im)
        cx = x0 - bx0
        for (st, t), a in zip(runs, adv):
            f = font(st, size)
            if spacing:
                for ch in t:
                    d.text((cx, y - by0), ch, font=f, fill=255, anchor='ls'); cx += f.getlength(ch) + spacing
            else:
                d.text((cx, y - by0), t, font=f, fill=255, anchor='ls'); cx += a
        return Mask(np.asarray(im, np.float32) / 255, bx0, by0)

    def text_width(self, s, size, font_style='geo', spacing=0.0, cjk='cjk'):
        return sum(font(cjk if _is_cjk(ch) else font_style, size).getlength(ch) + spacing for ch in s) - spacing

    # ------------------------------------------------------------ painting
    def _region(self, m):
        x0, y0, x1, y1 = max(0, m.x0), max(0, m.y0), min(self.W, m.x1), min(self.H, m.y1)
        if x1 <= x0 or y1 <= y0: return None, None
        return (slice(y0, y1), slice(x0, x1)), m.a[y0 - m.y0:y1 - m.y0, x0 - m.x0:x1 - m.x0]

    def _grain_field(self):
        if self._noise is None:
            r = np.random.default_rng(12345)
            fine = blur(r.random((self.H, self.W)).astype(np.float32), 0.55)
            fine = (fine - fine.mean()) / (fine.std() + 1e-6)
            clump = noise2d(self.H, self.W, 3.0, 2, 777)
            self._noise = (0.85 * fine + 0.25 * (clump - 0.5) / 0.15).astype(np.float32)
        return self._noise

    def fill(self, m, colour, alpha=1.0, grain=0.0):
        """lay a flat colour through mask m. alpha < 1 is a translucent sheet; grain breaks its alpha into a
        fine speckle (light beams, sun patches)"""
        sl, a = self._region(m)
        if sl is None: return m
        a = a * alpha
        if grain:
            a = np.clip(a * (1 + grain * self._grain_field()[sl] * 0.5), 0, 1)
        c = _c(colour)
        self.img[sl] += (c - self.img[sl]) * a[..., None]
        return m

    def darken(self, m, strength=0.25, tint=None):
        """multiply what is already there by an ink tint (flat shadow on any colour, stays in the palette)"""
        sl, a = self._region(m)
        if sl is None: return m
        t = self.ink if tint is None else _c(tint)
        k = 1 + (t - 1) * strength
        self.img[sl] *= 1 + (k - 1) * a[..., None]
        return m

    def lighten(self, m, strength=0.25, tint=None):
        """screen toward the cream (a lit plane on any colour)"""
        sl, a = self._region(m)
        if sl is None: return m
        t = self.cream if tint is None else _c(tint)
        self.img[sl] += (t - self.img[sl]) * (a * strength)[..., None]
        return m

    def shade(self, m, strength=0.22, depth=14, colour=None):
        """a crisp crescent on the side away from the light: m minus m nudged `depth` px toward the light"""
        cr = m - m.moved(self.light[0] * depth, self.light[1] * depth)
        return self.fill(cr, colour) if colour is not None else self.darken(cr, strength)

    def glint(self, m, strength=0.3, depth=8, colour=None):
        """the lit-side crescent in a lighter tone"""
        cr = m - m.moved(-self.light[0] * depth, -self.light[1] * depth)
        return self.fill(cr, colour) if colour is not None else self.lighten(cr, strength)

    def plane(self, m, p0, p1, strength=0.22, colour=None):
        """cut m with the line p0 -> p1 and shade the part on its left (see split): box side faces, the dark half
        of a leaf. Pass colour for a flat block instead of a multiply"""
        part = self.split(m, p0, p1)
        return self.fill(part, colour) if colour is not None else self.darken(part, strength)

    def cast(self, m, dx, dy, strength=0.22, clip=None):
        """a hard flat shadow of m, offset (dx, dy), onto whatever is already painted (clip limits the surface).
        Call it before painting the object itself."""
        s = m.moved(dx, dy)
        if clip is not None: s = s & clip
        return self.darken(s, strength)

    def backdrop(self, colour):
        self.img[:] = _c(colour)

    # ------------------------------------------------------------ lettering and graphic marks
    def text(self, s, x, y, size, colour=INK, font_style='geo', anchor='ls', spacing=0.0, cjk='cjk', alpha=1.0):
        m = self.text_mask(s, x, y, size, font_style, anchor, spacing, cjk)
        return self.fill(m, colour, alpha)

    def dashes(self, pts, width=6, dash=22, gap=16, colour=CREAM, per=16, arrow=None):
        """a dashed motion path along a smooth curve (round-capped dashes); arrow=size puts a head at the end"""
        P = spline(pts, per)
        seg = np.hypot(*np.diff(P, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        L = s[-1]
        m = Mask(np.zeros((0, 0)))
        t = 0.0
        stop = L - (arrow * 0.9 if arrow else 0)
        while t < stop:
            t1 = min(t + dash, stop)
            a = (np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1]))
            b = (np.interp(t1, s, P[:, 0]), np.interp(t1, s, P[:, 1]))
            m = m | self.capsule(a, b, width / 2)
            t += dash + gap
        if arrow:
            tip = P[-1]; back = np.array([np.interp(L - arrow, s, P[:, 0]), np.interp(L - arrow, s, P[:, 1])])
            d = (tip - back) / (np.linalg.norm(tip - back) + 1e-9); n = np.array([-d[1], d[0]])
            m = m | self.poly([tip + d * arrow * 0.2, back + n * arrow * 0.62, back - n * arrow * 0.62], round=arrow * 0.14)
        return self.fill(m, colour)

    def sparkle(self, cx, cy, r, colour=CREAM, rot=0.0):
        return self.fill(self.star(cx, cy, r, 4, 0.26, rot), colour)

    def sun(self, cx, cy, r, colour=MUSTARD, rays=0, ray_colour=None, ray_len=0.45, ray_w=0.07):
        """a flat disc; rays > 0 adds that many short round-capped rays"""
        m = self.fill(self.circle(cx, cy, r), colour)
        for i in range(rays):
            a = 2 * np.pi * i / rays
            p0 = (cx + np.cos(a) * r * 1.25, cy + np.sin(a) * r * 1.25)
            p1 = (cx + np.cos(a) * r * (1.25 + ray_len), cy + np.sin(a) * r * (1.25 + ray_len))
            self.fill(self.capsule(p0, p1, r * ray_w), ray_colour or colour)
        return m

    def cloud(self, cx, cy, w, colour=CREAM, seed=None):
        """flat cloud: a rounded base bar with three or four bumps on top"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        h = w * 0.26
        m = self.rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, h / 2)
        k = int(r.integers(2, 4))
        xs = np.linspace(cx - w * 0.2, cx + w * 0.16, k) + r.uniform(-0.03, 0.03, k) * w
        for i, x in enumerate(xs):
            rr = w * (0.14 + 0.05 * r.random()) * (1.35 if i == k // 2 else 1)
            m = m | self.circle(x, cy + h / 2 - rr * 1.05, rr)
        m = m & self.rect(cx - w, cy - w, cx + w, cy + h / 2)
        return self.fill(m, colour)

    # ------------------------------------------------------------ objects
    def book(self, cx, cy, w, h, rot=0.0, colour=CORAL, open=False, pages=CREAM, band=None):
        """a single book seen from the front: closed (cover, page block showing on the fore-edge, spine band)
        or open (two pages fanning from the gutter over a slightly larger cover)"""
        t = np.deg2rad(rot)
        ca, sa = np.cos(t), np.sin(t)
        P = lambda lx, ly: (cx + lx * ca + ly * sa, cy - lx * sa + ly * ca)
        if not open:
            cover = self.rrect(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, (w * 0.06, w * 0.12, w * 0.12, w * 0.06), rot)
            bx, by = P(w * 0.08, 0)                                               # page block peeks out on the fore-edge
            block = self.rrect(bx - w * 0.48, by - h * 0.45, bx + w * 0.48, by + h * 0.45, w * 0.06, rot)
            self.fill(block, pages)
            self.fill(cover, colour)
            hinge = self.split(cover, P(-w / 2 + w * 0.16, -h), P(-w / 2 + w * 0.16, h))   # the cover right of the hinge
            self.fill(cover - hinge, self.tone(colour, -0.18))                                  # the spine strip
            b = self.rrect(cx - w * 0.18, cy - h * 0.2, cx + w * 0.34, cy - h * 0.06, h * 0.07, rot)
            self.fill(b & cover, band or self.tone(colour, 0.55))
            return cover
        # open: two page quads over a cover
        cov = self.poly([P(-w / 2 - w * 0.03, -h / 2 + h * 0.02), P(0, -h / 2 + h * 0.1), P(w / 2 + w * 0.03, -h / 2 + h * 0.02),
                         P(w / 2 + w * 0.03, h / 2 + h * 0.04), P(0, h / 2 + h * 0.12), P(-w / 2 - w * 0.03, h / 2 + h * 0.04)], round=w * 0.03)
        self.fill(cov, colour)
        left = self.poly([P(-w / 2, -h / 2), P(0, -h / 2 + h * 0.09), P(0, h / 2 + h * 0.06), P(-w / 2, h / 2 - h * 0.02)], round=w * 0.02)
        right = self.poly([P(0, -h / 2 + h * 0.09), P(w / 2, -h / 2), P(w / 2, h / 2 - h * 0.02), P(0, h / 2 + h * 0.06)], round=w * 0.02)
        self.fill(left, pages); self.fill(right, self.tone(pages, -0.08))
        for i in range(3):                                                        # three lines of text
            for side in (-1, 1):
                y = -h * 0.22 + i * h * 0.16
                self.fill(self.capsule(P(side * w * 0.08, y), P(side * w * 0.36, y - side * 0), h * 0.022), self.tone(pages, -0.2))
        return cov

    def books(self, x0, x1, y_base, h_max, colours, seed=None, w_range=(0.13, 0.3), gap_at=None, gap_w=0,
              stack_at=None, back=None, shadow=0.3, title=True):
        """a row of spines standing on a shelf from x0 to x1 with their feet at y_base (h_max = tallest book).
        colours: palette colours to draw from (neighbours never repeat). gap_at / gap_w: one book has been taken
        out there -- the book on the left of the gap has tipped over into it, pivoting on its bottom corner until
        its top rests on the next book. stack_at: x of a small pile lying flat. If the row does not fill the
        shelf, the last book leans against the side panel. Each spine: base colour, a darker block on the side
        away from the light, bands and a title dash in tones of its own colour, and a hard flat shadow on the
        shelf `back` mask. Returns a list of (mask, colour)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        plan, x, prev = [], float(x0), None
        while True:
            if stack_at is not None and x <= stack_at < x + h_max * 0.3:
                plan.append(dict(kind='stack', x=x, w=h_max * 0.84)); x += h_max * 0.9; prev = None; continue
            if gap_at is not None and x <= gap_at < x + h_max * 0.3:
                if plan and plan[-1]['kind'] == 'stand': plan[-1]['lean'] = gap_at + gap_w - (plan[-1]['x'] + plan[-1]['w'])
                x = gap_at + gap_w; prev = None; continue
            bw = h_max * r.uniform(*w_range)
            if x + bw > x1: break
            opts = [c for c in colours if prev is None or not np.allclose(_c(c), _c(prev))]
            c = opts[r.integers(len(opts))]
            plan.append(dict(kind='stand', x=x, w=bw, h=h_max * r.uniform(0.68, 0.98), c=c, lean=0.0))
            prev = c
            x += bw + (h_max * 0.012 if r.random() < 0.3 else 0)
        if plan and plan[-1]['kind'] == 'stand' and x1 - x > h_max * 0.12:
            plan[-1]['lean'] = x1 - (plan[-1]['x'] + plan[-1]['w'])
        out = []
        for b in plan:
            if b['kind'] == 'stack':
                sw, yb = b['w'], y_base
                for i in range(int(r.integers(3, 5))):
                    bh = h_max * r.uniform(0.1, 0.16); bw = sw * r.uniform(0.8, 1.0)
                    c = colours[r.integers(len(colours))]
                    xa = b['x'] + (sw - bw) / 2 + r.uniform(-0.04, 0.04) * sw
                    bm = self.rrect(xa, yb - bh, xa + bw, yb, 2)
                    if back is not None: self.cast(bm, -h_max * 0.06, 0, shadow, clip=back)
                    self.fill(bm, c)
                    self.fill(self.rect(xa, yb - bh * 0.62, xa + bw * 0.9, yb - bh * 0.38), self.tone(c, 0.5))
                    self.fill(self.rect(xa + bw * 0.92, yb - bh, xa + bw, yb) & bm, self.tone(c, -0.2))
                    out.append((bm, c)); yb -= bh
                continue
            x, bw, bh, c = b['x'], b['w'], b['h'], b['c']
            if b['lean'] > 1:                                                     # tipped over to the right
                th = np.arcsin(min(b['lean'] / bh, 0.55))
                t = -th
                px, py = x + bw, y_base                                           # pivot: bottom-right corner
                ox = bw / 2 * np.cos(t) + bh / 2 * np.sin(t); oy = -bw / 2 * np.sin(t) + bh / 2 * np.cos(t)
                cx, cy = px - ox, py - oy
                m = self.rrect(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, (bw * 0.12, bw * 0.12, 0, 0), np.rad2deg(t))
                if back is not None: self.cast(m, -bw * 0.45, 0, shadow, clip=back)
                self.fill(m, c)
                P = lambda lx, ly: (cx + lx * np.cos(t) + ly * np.sin(t), cy - lx * np.sin(t) + ly * np.cos(t))
                self.fill(self.split(m, P(-bw * 0.26, bh), P(-bw * 0.26, -bh)), self.tone(c, -0.2))   # left strip
                q0, q1 = P(-bw * 0.26, -bh * 0.2), P(bw * 0.5, -bh * 0.2)
                self.fill(self.capsule(q0, q1, bh * 0.03) & m, self.tone(c, 0.55))
                out.append((m, c)); continue
            m = self.rrect(x, y_base - bh, x + bw, y_base, (bw * 0.12, bw * 0.12, 0, 0))
            if back is not None: self.cast(m, -bw * 0.45, 0, shadow, clip=back)
            self.fill(m, c)
            self.fill(self.rect(x, y_base - bh, x + bw * 0.26, y_base) & m, self.tone(c, -0.2))
            bc = self.tone(c, 0.55) if r.random() < 0.6 else self.tone(c, -0.35)   # bands sit near the head and foot
            style = r.integers(0, 4)
            if style in (1, 3):
                yy = r.uniform(0.8, 0.88)
                self.fill(self.rect(x + bw * 0.26, y_base - bh * yy - bh * 0.03, x + bw, y_base - bh * yy + bh * 0.03), bc)
            if style in (2, 3):
                yy = r.uniform(0.1, 0.16)
                self.fill(self.rect(x + bw * 0.26, y_base - bh * yy - bh * 0.03, x + bw, y_base - bh * yy + bh * 0.03), bc)
            if title and bw > h_max * 0.15 and r.random() < 0.75:                  # the title: one dash in the middle
                ty = y_base - bh * r.uniform(0.44, 0.54)
                self.fill(self.capsule((x + bw * 0.62, ty - bh * 0.13), (x + bw * 0.62, ty + bh * 0.13), bw * 0.09),
                          self.tone(c, 0.6) if r.random() < 0.7 else self.tone(c, -0.4))
            out.append((m, c))
        return out

    def plant(self, x, y, h, pot=CORAL, leaf=TEAL, kind='leafy', seed=None, n=None):
        """a potted plant standing at (x, y) (pot bottom centre), total height h.
        kind: 'leafy' (split two-tone leaves on stems), 'snake' (upright blades with bands), 'round' (bushy)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        pw, ph = h * 0.34, h * 0.26
        top = y - ph
        stems, leaves = Mask(np.zeros((0, 0))), []
        if kind == 'snake':
            for i in range(n or 6):
                bx = x + (i - (n or 6) / 2 + 0.5) * pw * 0.16
                tip = (bx + r.uniform(-0.2, 0.2) * h * 0.4, top - h * r.uniform(0.45, 0.72))
                leaves.append(((bx, top + 4), tip, pw * r.uniform(0.2, 0.28), r.uniform(-8, 8)))
        else:
            k = n or (7 if kind == 'leafy' else 11)
            for i in range(k):
                a = np.deg2rad(-90 + (i - (k - 1) / 2) * (150 / k) + r.uniform(-8, 8))
                L = h * r.uniform(0.38, 0.62) * (1 - 0.35 * abs(np.cos(a)))
                base = (x + r.uniform(-0.1, 0.1) * pw, top + 2)
                mid = (base[0] + np.cos(a) * L * 0.55, base[1] + np.sin(a) * L * 0.55)
                if kind == 'leafy':
                    stems = stems | self.tube([base, (base[0] + np.cos(a) * L * 0.3, base[1] + np.sin(a) * L * 0.34), mid], max(2, h * 0.008))
                    tip = (mid[0] + np.cos(a + 0.35 * np.sign(np.cos(a))) * L * 0.5, mid[1] + np.sin(a + 0.35 * np.sign(np.cos(a))) * L * 0.5)
                    leaves.append((mid, tip, L * 0.42, np.sign(np.cos(a)) * L * 0.06))
                else:
                    leaves.append((base, (base[0] + np.cos(a) * L, base[1] + np.sin(a) * L), L * 0.34, 0))
        self.fill(stems, self.tone(leaf, -0.35))
        order = sorted(range(len(leaves)), key=lambda i: -abs(leaves[i][1][0] - x))
        for i in order:
            p0, p1, wd, bend = leaves[i]
            m = self.leaf(p0, p1, wd, bend)
            self.fill(m, leaf)
            if kind == 'snake': self.plane(m, p0, p1, colour=self.tone(leaf, -0.2))           # left half of an upright blade
            elif p1[0] > p0[0]: self.plane(m, p1, p0, colour=self.tone(leaf, -0.2))           # lower half of the leaf
            else: self.plane(m, p0, p1, colour=self.tone(leaf, -0.2))
            if kind == 'snake':
                for j in range(3):
                    tt = 0.25 + j * 0.2
                    q = (p0[0] + (p1[0] - p0[0]) * tt, p0[1] + (p1[1] - p0[1]) * tt)
                    self.fill(self.ellipse(q[0], q[1], wd * 0.34, wd * 0.08, -np.rad2deg(np.arctan2(-(p1[1] - p0[1]), p1[0] - p0[0])) + 90) & m,
                              self.tone(leaf, 0.35))
        body = self.poly([(x - pw / 2, top + ph * 0.18), (x + pw / 2, top + ph * 0.18), (x + pw * 0.38, y), (x - pw * 0.38, y)],
                         round=[0, 0, pw * 0.08, pw * 0.08])
        rim = self.rrect(x - pw / 2 - pw * 0.04, top, x + pw / 2 + pw * 0.04, top + ph * 0.24, ph * 0.05)
        self.fill(body, pot)
        self.shade(body, 0.2, pw * 0.3)
        self.fill(rim, self.tone(pot, 0.12))
        self.shade(rim, 0.2, pw * 0.2)
        return body | rim

    def pendant(self, x, y_top, y, r, shade=INK, bulb=CREAM, beam_to=None, beam_alpha=0.13, beam_colour=None, cord=3):
        """a pendant lamp hanging from y_top: a cord, a dome shade of radius r whose bottom edge is at y, a bulb,
        and optionally a flat translucent beam spreading down to (x_left, x_right, y_floor)"""
        if beam_to is not None:
            bl, br, by = beam_to
            beam = self.poly([(x - r * 0.72, y), (x + r * 0.72, y), (br, by), (bl, by)])
            self.fill(beam, beam_colour or self.tone(bulb, 0.2), beam_alpha, grain=0.35)
        self.fill(self.capsule((x, y_top), (x, y - r * 0.95), cord), self.tone(shade, 0.05))
        dome = self.pie(x, y, r, 0, 180)
        self.fill(self.circle(x, y + r * 0.05, r * 0.3), bulb)
        self.fill(dome, shade)
        self.plane(dome, (x + r * 0.08, y - r - 10), (x + r * 0.34, y + 10), colour=self.tone(shade, 0.12))    # lit right side
        self.fill(self.rrect(x - r * 0.12, y - r - r * 0.12, x + r * 0.12, y - r + r * 0.05, r * 0.04), self.tone(shade, 0.12))
        return dome

    def cat(self, x, y, size, colour=INK, facing=1, pose='sit', tail_down=None):
        """a flat cat seen from behind / side, sitting with its base centre at (x, y); size = body height.
        tail_down: a y to let the tail hang down to (over a sill edge)"""
        s = size
        f = facing
        body = self.ellipse(x, y - s * 0.38, s * 0.34, s * 0.42) | self.ellipse(x, y - s * 0.12, s * 0.42, s * 0.2)
        body = body & self.rect(x - s, y - s * 2, x + s, y)
        hx, hy = x + f * s * 0.08, y - s * 0.86
        head = self.ellipse(hx, hy, s * 0.26, s * 0.22)
        ears = self.poly([(hx - s * 0.24, hy - s * 0.02), (hx - s * 0.2, hy - s * 0.34), (hx - s * 0.04, hy - s * 0.16)], round=s * 0.03) | \
            self.poly([(hx + s * 0.24, hy - s * 0.02), (hx + s * 0.2, hy - s * 0.34), (hx + s * 0.04, hy - s * 0.16)], round=s * 0.03)
        if tail_down is not None:
            tail = self.tube([(x - f * s * 0.2, y - s * 0.08), (x - f * s * 0.42, y + s * 0.05), (x - f * s * 0.46, (y + tail_down) / 2),
                              (x - f * s * 0.36, tail_down)], [s * 0.07, s * 0.07, s * 0.065, s * 0.06])
        else:
            tail = self.tube([(x - f * s * 0.3, y - s * 0.05), (x + f * s * 0.1, y + s * 0.02), (x + f * s * 0.5, y - s * 0.04),
                              (x + f * s * 0.62, y - s * 0.18)], s * 0.065)
        allm = body | head | ears | tail
        self.fill(allm, colour)
        self.shade(body | head, 0.0, s * 0.12, colour=self.tone(colour, 0.12) if _c(colour).mean() < 0.3 else self.tone(colour, -0.2))
        return allm

    # ------------------------------------------------------------ people
    def person(self, hip, height, facing=1, lean=0.0, head_tilt=0.0, arm=(10, 20), arm_far=(-8, -2),
               leg=(2, 0), leg_far=(-4, 0), sit=False, top=MUSTARD, bottom=INK, shoes=None, skin=PEACH,
               hair=INK, hair_style='short', sleeve='long', coat=False, skirt=False, apron=None, bag=None,
               collar=None, build=1.0, far_tone=-0.2, draw_near_arm=True, hand_to=None, hand_far_to=None,
               foot_to=None, foot_far_to=None):
        """a faceless adult (about 7.5 heads tall) with the hip centre at `hip`, facing +1 right / -1 left.
        Joint angles are degrees from straight down, positive toward the facing side:
          arm=(upper, fore) of the near arm, arm_far the far arm, leg=(thigh, shin), leg_far the far leg.
          sit=True is a shortcut for thighs forward (90) and shins down.
          hand_to / hand_far_to / foot_to / foot_far_to: put that hand or ankle on a point instead (two-bone IK:
          elbows drop, knees go forward; a point out of reach gets the limb stretched straight toward it).
        Clothes: top (sweater / shirt colour), bottom (trousers), skirt=colour, coat=True (top becomes a long coat),
        apron=colour, bag=colour (a tote hanging from the near shoulder), collar=colour. hair_style: short, bun, bob, long, pony.
        Returns the joints: head, neck, shoulder, hand, hand_far, elbow, knee, knee_far, foot, foot_far, u."""
        f = 1 if facing >= 0 else -1
        u = height / 7.5
        H = np.array(hip, np.float64)
        lam = np.deg2rad(lean)
        up = np.array([f * np.sin(lam), -np.cos(lam)])
        fwd = np.array([f * np.cos(lam), np.sin(lam)])

        def dv(a):
            a = np.deg2rad(a)
            return np.array([f * np.sin(a), np.cos(a)])

        if sit:
            leg = leg if leg != (2, 0) else (88, 4)
            leg_far = leg_far if leg_far != (-4, 0) else (92, 0)
        shoes = shoes if shoes is not None else self.tone(bottom, -0.35)
        S = H + up * 2.78 * u
        N = H + up * 3.02 * u
        tilt = np.deg2rad(head_tilt)
        head_up = np.array([f * np.sin(lam + tilt), -np.cos(lam + tilt)])
        C = N + head_up * 0.62 * u + fwd * 0.1 * u
        sh_n, sh_f = S - fwd * 0.36 * u * build, S + fwd * 0.34 * u * build
        hp_n, hp_f = H - fwd * 0.26 * u, H + fwd * 0.22 * u
        joints = dict(u=u, hip=tuple(H), shoulder=tuple(S), neck=tuple(N), head=tuple(C))

        def ang(v):
            return float(np.rad2deg(np.arctan2(f * v[0], v[1])))

        def ik(root, target, L1, L2, knee):
            d = np.asarray(target, np.float64) - root
            dist = float(np.clip(np.linalg.norm(d), abs(L1 - L2) + 1e-3, L1 + L2 - 1e-3))
            base = np.arctan2(d[1], d[0])
            al = np.arccos(np.clip((L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist), -1, 1))
            cands = [root + L1 * np.array([np.cos(base + s_ * al), np.sin(base + s_ * al)]) for s_ in (1, -1)]
            J = max(cands, key=lambda e: f * e[0]) if knee else max(cands, key=lambda e: e[1] - 0.3 * f * e[0])
            tip = root + d / (np.linalg.norm(d) + 1e-9) * dist
            return (ang(J - root), ang(tip - J))

        if hand_to is not None: arm = ik(S - fwd * 0.36 * u * build, hand_to, 1.42 * u, 1.42 * u, False)
        if hand_far_to is not None: arm_far = ik(S + fwd * 0.34 * u * build, hand_far_to, 1.42 * u, 1.42 * u, False)
        if foot_to is not None: leg = ik(H - fwd * 0.26 * u, foot_to, 1.92 * u, 1.86 * u, True)
        if foot_far_to is not None: leg_far = ik(H + fwd * 0.22 * u, foot_far_to, 1.92 * u, 1.86 * u, True)

        def arm_pts(sh, a):
            E = sh + dv(a[0]) * 1.42 * u
            Wr = E + dv(a[1]) * 1.22 * u
            Hd = Wr + dv(a[1]) * 0.2 * u
            return E, Wr, Hd

        def leg_pts(hp, a):
            K = hp + dv(a[0]) * 1.92 * u
            A = K + dv(a[1]) * 1.86 * u
            return K, A

        def tn(c, k):                                                             # a darker far limb; a dark colour
            return self.tone(c, k) if k >= 0 or _c(c).mean() > 0.3 else self.tone(c, -k * 0.6)   # lifts instead

        def draw_arm(sh, a, tone_k):
            E, Wr, Hd = arm_pts(sh, a)
            sc = tn(top, tone_k)
            if sleeve == 'long':
                am = self.fill(self.limb([sh, E, Wr], [0.27 * u, 0.22 * u, 0.18 * u]), sc)
                self.shade(am, 0.16, 0.1 * u)
                self.fill(self.capsule(Hd - dv(a[1]) * 0.05 * u, Hd + dv(a[1]) * 0.05 * u, 0.16 * u), tn(skin, tone_k))
                self.fill(self.capsule(Wr - dv(a[1]) * 0.14 * u, Wr - dv(a[1]) * 0.02 * u, 0.2 * u), tn(top, tone_k - 0.1))
            else:
                self.fill(self.limb([E, Wr], [0.19 * u, 0.15 * u]), tn(skin, tone_k))
                self.fill(self.capsule(Hd - dv(a[1]) * 0.05 * u, Hd + dv(a[1]) * 0.05 * u, 0.16 * u), tn(skin, tone_k))
                self.fill(self.limb([sh, sh + dv(a[0]) * 0.8 * u], [0.3 * u, 0.25 * u]), sc)
            return E, Wr, Hd

        def draw_leg(hp, a, tone_k):
            K, A = leg_pts(hp, a)
            m = self.limb([hp, K, A], [0.38 * u, 0.27 * u, 0.2 * u])
            self.fill(m, tn(bottom, tone_k))
            toe = A + np.array([f * 0.78 * u, 0.1 * u])
            heel = A + np.array([-f * 0.18 * u, 0.1 * u])
            if a[1] < -25:                                                        # on tiptoe / foot on a rung behind
                toe = A + np.array([f * 0.7 * u, 0.26 * u])
            shoe = self.capsule(heel, toe, 0.2 * u, 0.17 * u) | self.rrect(min(heel[0], toe[0]), A[1] - 0.05 * u, max(heel[0], toe[0]),
                                                                           A[1] + 0.3 * u, (0.14 * u, 0.14 * u, 0.04 * u, 0.04 * u)) & \
                self.rect(min(heel[0], toe[0]) - u, A[1] - u, max(heel[0], toe[0]) + u, max(heel[1], toe[1]) + 0.3 * u)
            self.fill(self.limb([A - dv(a[1]) * 0.12 * u, A + np.array([0, 0.06 * u])], [0.21 * u, 0.21 * u]), tn(bottom, tone_k - 0.05))
            self.fill(shoe, tn(shoes, tone_k * 0.5))
            return K, A, m

        # long hair panel sits behind everything
        if hair_style == 'long':
            self.fill(self.rrect(C[0] - f * 0.55 * u - 0.1 * u, C[1] - 0.2 * u, C[0] + f * 0.2 * u + 0.1 * u, S[1] + 1.0 * u, 0.3 * u)
                      if f > 0 else self.rrect(C[0] - 0.3 * u, C[1] - 0.2 * u, C[0] + 0.65 * u, S[1] + 1.0 * u, 0.3 * u), self.tone(hair, -0.1))
        E_f, W_f, H_f = draw_arm(sh_f, arm_far, far_tone)
        K_f, A_f, _ = draw_leg(hp_f, leg_far, far_tone)
        pelvis = self.ellipse(H[0], H[1] + 0.05 * u, 0.72 * u, 0.5 * u, -np.rad2deg(lam) * f)
        self.fill(pelvis, bottom)
        K_n, A_n, legm = draw_leg(hp_n, leg, 0.0)
        self.shade(legm, 0.16, 0.1 * u)
        if skirt:
            sk_len = 1.9 * u
            if sit:
                K = K_n
                sk = self.poly([H - fwd * 0.72 * u + up * 0.3 * u, H + fwd * 0.6 * u + up * 0.3 * u, K + np.array([f * 0.2 * u, -0.3 * u]),
                                K + np.array([f * 0.25 * u, 0.4 * u]), H - fwd * 0.8 * u + np.array([0, 0.6 * u])], round=0.15 * u)
            else:
                sk = self.poly([H - fwd * 0.7 * u + up * 0.3 * u, H + fwd * 0.62 * u + up * 0.3 * u, H + fwd * 0.9 * u + np.array([0, sk_len]),
                                H - fwd * 1.0 * u + np.array([0, sk_len])], round=[0.2 * u, 0.2 * u, 0.1 * u, 0.1 * u])
            self.fill(sk, skirt)
            self.shade(sk, 0.18, 0.3 * u)
        # torso
        def at(k, w_front, w_back):
            c = H + up * k * u
            return c + fwd * w_front * u * build, c - fwd * w_back * u * build
        s_f, s_b = at(2.82, 0.72, 0.78)
        c_f, c_b = at(2.1, 0.78, 0.7)
        w_f, w_b = at(1.1, 0.62, 0.66)
        hem = -0.12 if not coat else -2.1
        if coat and sit: hem = -0.5
        h_f, h_b = at(hem, 0.72 if not coat else 0.95, 0.76 if not coat else 1.0)
        torso = self.poly([s_b, s_f, c_f, w_f, h_f, h_b, w_b, c_b],
                          round=[0.55 * u, 0.5 * u, 0.3 * u, 0.2 * u, 0.1 * u, 0.1 * u, 0.2 * u, 0.3 * u])
        self.fill(torso, top)
        self.shade(torso, 0.2, 0.34 * u)
        if coat:                                                                  # front panel overlaps: a placket block
            pl = self.split(torso, tuple(H + fwd * 0.3 * u + up * 3 * u), tuple(H + fwd * 0.42 * u - up * 3 * u))
            self.fill(pl, self.tone(top, -0.1))
            self.fill(self.poly([N + fwd * 0.05 * u, N + fwd * 0.5 * u + up * -0.1 * u, H + fwd * 0.42 * u + up * 1.7 * u]), self.tone(top, -0.16))
        if apron is not None:
            ap = self.poly([H + fwd * 0.05 * u + up * 2.35 * u, H + fwd * 0.78 * u + up * 2.35 * u, H + fwd * 0.95 * u - up * 1.3 * u,
                            H - fwd * 0.35 * u - up * 1.3 * u], round=[0.08 * u, 0.08 * u, 0.12 * u, 0.12 * u])
            self.fill(ap, apron)
            self.shade(ap, 0.16, 0.2 * u)
            self.fill(self.capsule(H + fwd * 0.2 * u + up * 2.35 * u, N + fwd * 0.12 * u, 0.06 * u), self.tone(apron, -0.1))
            self.fill(self.capsule(H - fwd * 0.4 * u + up * 1.1 * u, H + fwd * 0.4 * u + up * 1.1 * u, 0.07 * u), self.tone(apron, -0.12))
            self.fill(self.rrect(*(H + fwd * 0.18 * u + up * 0.1 * u + np.array([-0.26, -0.22]) * u),
                                 *(H + fwd * 0.18 * u + up * 0.1 * u + np.array([0.26, 0.22]) * u), 0.06 * u), self.tone(apron, -0.12))
        # neck and head
        neck = self.capsule(N - up * 0.1 * u, C, 0.17 * u)
        self.fill(neck, skin)
        self.darken(neck & self.circle(C[0] + f * 0.02 * u, C[1] + 0.3 * u, 0.4 * u), 0.22)
        if collar is not None:
            self.fill(self.poly([N - fwd * 0.3 * u, N + fwd * 0.35 * u, N + fwd * 0.05 * u + up * -0.35 * u], round=0.05 * u), collar)
        else:
            self.fill(self.ellipse(N[0], N[1], 0.34 * u, 0.13 * u, -np.rad2deg(lam) * f) & torso.grown(2), self.tone(top, -0.14))
        rot_h = -np.rad2deg(lam + tilt) * f
        hr = self.ellipse(C[0], C[1], 0.42 * u, 0.52 * u, rot_h)
        self.fill(hr, skin)
        # hair = a slightly bigger ellipse minus the face (the head nudged forward and down), then cut at the
        # hairline: from the nape at the back up to the temple in front, so the jaw and the ear show below it
        face = hr.moved(*(fwd * 0.2 * u + np.array([0, 0.2 * u])))
        cap = self.ellipse(C[0] - f * 0.03 * u, C[1] - 0.04 * u, 0.47 * u, 0.56 * u, rot_h) - face
        back_pt = C - fwd * 0.6 * u
        front_pt = C + fwd * 0.6 * u
        nape, temple = {'short': (0.2, -0.16), 'bun': (0.16, -0.12), 'pony': (0.16, -0.12)}.get(hair_style, (0.62, 0.1))
        bp = back_pt + np.array([0, nape * u]) + head_up * 0; fp = front_pt + np.array([0, temple * u])
        lo, hi = (bp, fp) if bp[0] < fp[0] else (fp, bp)
        cap = self.split(cap, tuple(lo), tuple(hi))                               # keep what is above the hairline
        extra = Mask(np.zeros((0, 0)))
        if hair_style == 'bun':
            extra = self.circle(*(C - fwd * 0.3 * u + np.array([0, -0.5 * u])), 0.23 * u)
        elif hair_style == 'pony':
            extra = self.tube([C - fwd * 0.4 * u + np.array([0, -0.2 * u]), C - fwd * 0.7 * u + np.array([0, 0.25 * u]),
                               C - fwd * 0.6 * u + np.array([0, 0.85 * u])], [0.2 * u, 0.16 * u, 0.08 * u])
        elif hair_style in ('bob', 'long'):                                       # a curtain behind the jaw, down to the chin
            bx0, bx1 = sorted([C[0] - f * 0.5 * u, C[0] + f * 0.02 * u])
            extra = self.rrect(bx0, C[1] - 0.2 * u, bx1, C[1] + 0.62 * u, (0, 0, 0.18 * u, 0.18 * u) if f > 0 else (0, 0, 0.18 * u, 0.18 * u)) - face
        if not extra.empty and hair_style in ('bun', 'pony'):
            self.fill(extra, self.tone(hair, -0.08))
        self.fill(cap | (extra if hair_style in ('bob', 'long') else Mask(np.zeros((0, 0)))), hair)
        self.glint(cap, 0.14, 0.06 * u)
        if hair_style in ('short', 'bun', 'pony'):
            ear = self.ellipse(*(C - fwd * 0.12 * u + np.array([0, 0.08 * u])), 0.085 * u, 0.12 * u, rot_h)
            self.fill(ear, self.tone(skin, -0.1))
        if bag is not None:                                                       # a tote on the near shoulder
            bc = H - fwd * 0.62 * u + np.array([0, 0.62 * u])
            bw_, bh_ = 1.05 * u, 1.15 * u
            for dx in (-0.36, 0.3):
                self.fill(self.capsule(sh_n + np.array([0, 0.05 * u]), bc + np.array([dx * u, -bh_ / 2 + 0.05 * u]), 0.055 * u),
                          self.tone(bag, -0.3))
            bm = self.rrect(bc[0] - bw_ / 2, bc[1] - bh_ / 2, bc[0] + bw_ / 2, bc[1] + bh_ / 2, (0.05 * u, 0.05 * u, 0.12 * u, 0.12 * u))
            self.fill(bm, bag); self.shade(bm, 0.0, 0.22 * u, colour=self.tone(bag, -0.14))
            self.fill(self.rect(bc[0] - bw_ / 2, bc[1] + 0.08 * u, bc[0] + bw_ / 2, bc[1] + 0.26 * u) & bm, self.tone(bag, -0.3)
                      if _c(bag).mean() > 0.6 else self.tone(bag, 0.5))
        E_n, W_n, H_n = draw_arm(sh_n, arm, 0.0) if draw_near_arm else arm_pts(sh_n, arm)
        joints.update(hand=tuple(H_n), hand_far=tuple(H_f), elbow=tuple(E_n),
                      knee=tuple(K_n), knee_far=tuple(K_f), foot=tuple(A_n), foot_far=tuple(A_f), shoulder_near=tuple(sh_n),
                      shoulder_far=tuple(sh_f))
        self._last_person = dict(sh_n=sh_n, arm=arm, top=top, skin=skin, sleeve=sleeve, u=u, f=f, draw=draw_arm)
        return joints

    def near_arm(self):
        """draw the near arm of the last person() called with draw_near_arm=False (after a prop it should cover)"""
        p = self._last_person
        E, Wr, Hd = p['draw'](p['sh_n'], p['arm'], 0.0)
        return tuple(Hd)

    def hand(self, x, y, r, skin=PEACH):
        return self.fill(self.circle(x, y, r), skin)

    # ------------------------------------------------------------ output
    def composite(self, grain=0.012):
        img = self.img
        if grain:
            n = self._grain_field()
            img = img * (1 + grain * n[..., None])
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

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
