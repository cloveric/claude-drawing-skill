"""sticker — sticker collage x thermal receipt: die-cut vinyl stickers, washi tape, a receipt, hanging price
tags, a rubber stamp and pen marks on a cream board (numpy + Pillow only).

Model: a flat-lay photographed from straight above under one soft key light from the upper left.
  board    cream or light-kraft card: fine paper grain, low-frequency mottling, pale and dark fibres, a few
           flecks, a warm fall-off of the light toward the corners.
  art      every object is first drawn as a flat-vector picture on its own transparent sheet (`Art`): masks
           (circle, ellipse, rrect, poly, blob, line, text) filled with flat colours, gradients and hard-edged
           shade/light crescents, like a vector illustration.
  sticker  `stick(art)` turns a sheet into a die-cut vinyl sticker: the silhouette is dilated with rounded
           corners into a thick white border (small gaps and notches fill in, as a die would cut them); the
           vinyl has thickness (a darker cut edge on the far side, a lit edge toward the light), a glossy
           laminate (a thin specular rim along the lit edges plus a faint diagonal sheen), a tight contact
           shadow plus a soft drop shadow, a slight rotation, and optionally a peeled corner folded back to
           show the paler backing side, with its own small shadow on the sticker.
  paper    `lay(art)` places paper that is not vinyl (receipt, tag): matte, no border; the paper curls a
           little (the ends of the long axis lift and turn toward or away from the light) and the lifted
           parts throw a longer, softer shadow.
  receipt  `Receipt` — thermal paper with serrated tear edges top and bottom; the print is grey rather than
           black and uneven the way a thermal head prints (weak head elements leave faint vertical streaks,
           density drifts along the paper feed, tiny dropouts); rows with dotted leaders, rules, a printed
           strike-through of an old price, emphasised (double-struck) totals, a barcode.
  tape     washi tape: translucent tinted paper (what is under it shows through), fibres running along its
           length, a printed pattern (stripes, dots, grid), hand-torn zigzag ends, a hair-line shadow.
  tag      `tag_art` — a card price tag with clipped top corners and a metal grommet around the hole; laid
           with more lift (it hangs), strung on twisted baker's twine (`twine`) drawn as a curve with ply
           stripes, a cylinder shade and a shadow of its own.
  stamp    a round rubber stamp: rings, text set around the circle, a centre word; the ink is translucent
           (it multiplies with whatever is under it), pools at the edges of the letters, is lighter where
           the stamp was pressed less and broken where the paper tooth did not take ink.
  pen      ballpoint marks (ticks, loops, strike-throughs) with pressure variation and tapered ends.

    from sticker import Sticker
    s = Sticker(1920, 1080, seed=1)
    s.board('#EFE5D1')
    a = s.art(300, 300)
    a.fill(a.circle(150, 150, 120), '#E04A2F')
    a.fill(a.text('SALE', 150, 150, 70, 'sans_bold'), '#FBF3E4')
    s.stick(a, 960, 540, rot=-6, border=16, peel='tr')
    s.tape(960, 380, 220, rot=8, colour='#E8AC2C', pattern='stripe')
    s.stamp(700, 700, 110, 'PAID · PAID · PAID · ', '已付', 'PAID', '#D8412B', rot=-12)
    s.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, shift, load_font, height_normals, blob_pts

SHADOW = '#3A2710'           # warm brown: shadows on a cream board are never grey


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- small helpers (kept inside this module)
_FONTS = {}


def _font(style, size):
    k = (style, int(round(size)))
    if k not in _FONTS:
        _FONTS[k] = load_font(style, max(4, int(round(size))))
    return _FONTS[k]


def _is_cjk(ch):
    o = ord(ch)
    return 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F


def _runs(s, font, cjk, size):
    """split a string into runs that share a font (Latin / CJK)"""
    out = []
    for ch in s:
        f = _font(cjk, size) if _is_cjk(ch) else _font(font, size)
        if out and out[-1][1] is f:
            out[-1][0] += ch
        else:
            out.append([ch, f])
    return out


def measure(s, size, font='sans_bold', spacing=0.0, cjk='cjk_sans'):
    """advance width of `s` in px (mixed Latin / CJK)"""
    w = 0.0
    for run, f in _runs(s, font, cjk, size):
        w += sum(f.getlength(ch) + spacing for ch in run) if spacing else f.getlength(run)
    return w - (spacing if s and spacing else 0)


def text_mask(w, h, s, x, y, size, font='sans_bold', anchor='mm', stroke=0, spacing=0.0, rot=0.0, cjk='cjk_sans'):
    """mixed Latin / CJK text -> float mask (h, w). anchor: first letter l/m/r, second m (cap middle),
    s (baseline), t (cap top), b (descender). stroke thickens the glyphs (bold); rot degrees clockwise."""
    total = measure(s, size, font, spacing, cjk) + 2 * stroke
    x0 = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]] + stroke
    base = y + {'m': 0.36, 's': 0.0, 't': 0.72, 'b': -0.22}[anchor[1]] * size
    im = Image.new('L', (int(w), int(h)), 0)
    d = ImageDraw.Draw(im)
    for run, f in _runs(s, font, cjk, size):
        if spacing:
            for ch in run:
                d.text((x0, base), ch, font=f, fill=255, anchor='ls', stroke_width=int(stroke), stroke_fill=255)
                x0 += f.getlength(ch) + spacing
        else:
            d.text((x0, base), run, font=f, fill=255, anchor='ls', stroke_width=int(stroke), stroke_fill=255)
            x0 += f.getlength(run)
    if rot:
        im = im.rotate(-rot, resample=Image.BICUBIC, center=(x, y))
    return np.asarray(im, np.float32) / 255


def _glyph(ch, size, font, cjk, stroke=0):
    """one character centred in a small square mask"""
    f = _font(cjk, size) if _is_cjk(ch) else _font(font, size)
    n = int(size * 1.6 + 2 * stroke + 4)
    im = Image.new('L', (n, n), 0)
    ImageDraw.Draw(im).text((n / 2, n / 2 + 0.36 * size), ch, font=f, fill=255, anchor='ms', stroke_width=int(stroke), stroke_fill=255)
    return im


def _rotate(a, deg):
    """rotate a float array by `deg` clockwise about its centre; the canvas grows to fit"""
    if abs(deg) < 1e-3:
        return a
    im = Image.fromarray(np.ascontiguousarray(a, np.float32), 'F')
    return np.asarray(im.rotate(-deg, resample=Image.BICUBIC, expand=True), np.float32)


def _sample(a, x, y):
    """bilinear lookup of a at float coords (zero outside)"""
    H, W = a.shape
    x0 = np.floor(x).astype(np.int32); y0 = np.floor(y).astype(np.int32)
    fx = x - x0; fy = y - y0

    def g(yy, xx):
        ok = (xx >= 0) & (xx < W) & (yy >= 0) & (yy < H)
        return np.where(ok, a[np.clip(yy, 0, H - 1), np.clip(xx, 0, W - 1)], 0)
    return (g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy)
            + g(y0 + 1, x0) * (1 - fx) * fy + g(y0 + 1, x0 + 1) * fx * fy)


def _resample(P, step):
    """polyline -> points evenly spaced by arc length, plus tangent angles"""
    P = np.asarray(P, np.float32)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(s[-1] / step) + 1)
    t = np.linspace(0, s[-1], n)
    x = np.interp(t, s, P[:, 0]); y = np.interp(t, s, P[:, 1])
    ang = np.arctan2(np.gradient(y), np.gradient(x))
    return x, y, ang, s[-1]


# ================================================================ Art: a flat-vector sheet
class Art:
    """A transparent sheet in local pixels (origin top-left). Draw with masks + fill; then hand it to
    Sticker.stick() (becomes a die-cut vinyl sticker) or Sticker.lay() (paper). Colour is stored
    premultiplied, so partial coverage composites correctly."""

    def __init__(self, w, h, seed=0):
        self.w, self.h = int(np.ceil(w)), int(np.ceil(h))
        self.rgb = np.zeros((self.h, self.w, 3), np.float32)
        self.a = np.zeros((self.h, self.w), np.float32)
        self.YY, self.XX = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.rng = np.random.default_rng(seed)

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _pil(self, fn, ss=3):
        im = Image.new('L', (self.w * ss, self.h * ss), 0)
        fn(ImageDraw.Draw(im), ss)
        return np.asarray(im.resize((self.w, self.h), Image.BOX), np.float32) / 255

    # ---- masks
    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def ring(self, cx, cy, r, width):
        return np.clip(width / 2 - np.abs(np.hypot(self.XX - cx, self.YY - cy) - r) + 0.5, 0, 1)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        t = np.deg2rad(rot); c, s = np.cos(t), np.sin(t)
        x = (self.XX - cx) * c + (self.YY - cy) * s; y = -(self.XX - cx) * s + (self.YY - cy) * c
        d = np.sqrt((x / rx) ** 2 + (y / ry) ** 2)
        return np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1)

    def rrect(self, x0, y0, x1, y1, r):
        return self._pil(lambda d, k: d.rounded_rectangle((x0 * k, y0 * k, x1 * k, y1 * k), r * k, fill=255))

    def poly(self, pts):
        return self._pil(lambda d, k: d.polygon([(float(x) * k, float(y) * k) for x, y in pts], fill=255))

    def blob(self, cx, cy, rx, ry, rough=0.06, rot=0.0, seed=None):
        return self.poly(blob_pts(cx, cy, rx, ry, rough, 120, self._seed() if seed is None else seed, rot))

    def line(self, pts, width, smooth=False):
        P = spline(pts, 12) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)

        def fn(d, k):
            q = [(float(x) * k, float(y) * k) for x, y in P]
            d.line(q, fill=255, width=max(1, int(round(width * k))), joint='curve')
            for x, y in (q[0], q[-1]):
                r = width * k / 2
                d.ellipse((x - r, y - r, x + r, y + r), fill=255)
        return self._pil(fn)

    def text(self, s, x, y, size, font='sans_bold', anchor='mm', stroke=0, spacing=0.0, rot=0.0, cjk='cjk_sans'):
        return text_mask(self.w, self.h, s, x, y, size, font, anchor, stroke, spacing, rot, cjk)

    def crescent(self, mask, dx, dy):
        """the rim of `mask` left uncovered by a copy shifted by (dx, dy): a shade or light crescent"""
        return np.clip(mask - shift(mask, dx, dy), 0, 1)

    # ---- paint
    def _over(self, m, col, clip):
        m = np.clip(m, 0, 1)
        if clip:                                   # paint inside what is already there, keep the silhouette
            self.rgb = self.rgb * (1 - m[..., None]) + col * (m * self.a)[..., None]
        else:
            self.rgb = self.rgb * (1 - m[..., None]) + col * m[..., None]
            self.a = self.a * (1 - m) + m

    def fill(self, mask, colour, alpha=1.0, clip=False):
        self._over(mask * alpha, _c(colour), clip)

    def gradient(self, mask, c0, c1, p0, p1, alpha=1.0, clip=False):
        """linear gradient c0 at p0 -> c1 at p1"""
        d = np.array(p1, np.float32) - np.array(p0, np.float32)
        t = np.clip(((self.XX - p0[0]) * d[0] + (self.YY - p0[1]) * d[1]) / (d @ d + 1e-6), 0, 1)[..., None]
        self._over(mask * alpha, _c(c0) * (1 - t) + _c(c1) * t, clip)

    def radial(self, mask, c0, c1, cx, cy, r, alpha=1.0, clip=False):
        """radial gradient c0 at (cx, cy) -> c1 at distance r"""
        t = np.clip(np.hypot(self.XX - cx, self.YY - cy) / r, 0, 1)[..., None]
        self._over(mask * alpha, _c(c0) * (1 - t) + _c(c1) * t, clip)

    def cut(self, mask):
        """punch a hole (the board shows through)"""
        m = np.clip(mask, 0, 1)
        self.rgb *= (1 - m)[..., None]; self.a *= (1 - m)

    def speckle(self, mask, colour, n, r=(0.8, 1.8), alpha=(0.35, 0.8), stretch=1.0, rot=0.0, seed=None):
        """n small dots scattered inside mask (flour, seeds, sugar); stretch > 1 makes short dashes"""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        ys, xs = np.nonzero(mask > 0.5)
        if len(xs) == 0: return
        pick = rng.integers(0, len(xs), n)
        m = np.zeros((self.h, self.w), np.float32)
        for i in pick:
            rr = rng.uniform(*r)
            e = self.ellipse(xs[i] + rng.uniform(-.5, .5), ys[i] + rng.uniform(-.5, .5), rr * stretch, rr, rot + rng.uniform(-25, 25))
            m = np.maximum(m, e * rng.uniform(*alpha))
        self.fill(m, colour, clip=True)

    def texture(self, kind='kraft', strength=1.0, seed=None):
        """card / paper tooth inside the sheet: fine grain, mottling, and (kraft) dark fibre flecks"""
        s = self._seed() if seed is None else seed
        h, w = self.h, self.w
        t = 1 + strength * (0.05 * (noise2d(h, w, 1.3, 2, s) - 0.5) + 0.06 * (noise2d(h, w, 45, 3, s + 1) - 0.5))
        if kind == 'kraft':
            rng = np.random.default_rng(s + 2)
            im = Image.new('L', (w * 2, h * 2), 0); d = ImageDraw.Draw(im)
            for _ in range(int(w * h / 900 * strength)):
                x, y = rng.uniform(0, w * 2), rng.uniform(0, h * 2)
                a, L = rng.uniform(0, np.pi), rng.uniform(3, 14)
                d.line((x, y, x + np.cos(a) * L, y + np.sin(a) * L), fill=int(rng.uniform(60, 200)), width=1)
            fl = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
            t = t * (1 - 0.22 * fl)
        self.rgb *= t[..., None]


# ================================================================ Receipt: thermal paper
class Receipt(Art):
    """A thermal-paper receipt: serrated tear edges, grey thermal print with head streaks and feed drift.
    Coordinates are local to the receipt; lay it with Sticker.lay(), which returns a local->global mapping
    for pen marks and stamps."""

    def __init__(self, w, h, seed=0, paper='#FDFCF9', ink='#4f525a', font='typewriter', tooth=15, depth=7, margin=34):
        super().__init__(w, h, seed)
        r = self.rng
        self.font, self.margin, self.ink = font, margin, _c(ink)
        n = int(w / tooth)
        xs = np.linspace(0, w, 2 * n + 1)
        top = [(x, (depth if i % 2 == 0 else 0.5) + r.uniform(-1.2, 1.2)) for i, x in enumerate(xs)]
        bot = [(x, h - (depth if i % 2 == 0 else 0.5) + r.uniform(-1.2, 1.2)) for i, x in enumerate(xs)][::-1]
        self.fill(self.poly(top + bot), paper)
        s = self._seed()
        tex = 1 + 0.016 * (noise2d(self.h, self.w, 1.4, 2, s) - 0.5) + 0.02 * (noise2d(self.h, self.w, 140, 3, s + 1) - 0.5)
        self.rgb *= tex[..., None]
        # thermal head: every column is one heating element; some are weak -> faint vertical streaks
        colv = np.interp(np.arange(self.w), np.linspace(0, self.w - 1, self.w // 2), r.random(self.w // 2))
        weak = np.zeros(self.w, np.float32)
        for c in r.integers(0, self.w, 3):
            weak[c:c + 1] = r.uniform(0.3, 0.5)
        feed = fbm1d(self.h, 70, 3, s + 2)
        dens = 0.8 + 0.08 * (colv[None, :] - 0.5) + 0.08 * feed[:, None]
        dens = dens * (1 - weak[None, :])
        dens = dens * smoothstep(0.04, 0.14, noise2d(self.h, self.w, 1.1, 1, s + 3))
        self.dens = np.clip(dens, 0, 1).astype(np.float32)

    def _ink(self, m, k=1.0, colour=None):
        m = blur(m, 0.35)                               # heated dots spread a little: soft edges
        self._over(np.clip(m * self.dens * k, 0, 1), self.ink if colour is None else _c(colour), clip=True)

    def print(self, s, x, y, size, anchor='ls', bold=False, spacing=0.0, k=1.0, font=None):
        """print a line of text; bold = emphasised mode (struck twice, one dot apart)"""
        m = self.text(s, x, y, size, font or self.font, anchor, 0, spacing)
        if bold:
            m = np.maximum(m, shift(m, 1, 0))
        self._ink(m, k)
        return measure(s, size, font or self.font, spacing)

    def centre(self, y, s, size=20, bold=False, spacing=0.0, k=1.0, font=None):
        self.print(s, self.w / 2, y, size, 'ms', bold, spacing, k, font)

    def row(self, y, left, right='', size=21, bold=False, leader=True, indent=0, was=None, k=1.0):
        """item row: name on the left, amount right-aligned, dotted leader between;
        was = an old price printed before the amount and struck through"""
        x0, x1 = self.margin + indent, self.w - self.margin
        wl = self.print(left, x0, y, size, 'ls', bold, k=k)
        wr = self.print(right, x1, y, size, 'rs', bold, k=k) if right else 0
        end = x1 - wr - 12
        if was:
            ww = measure(was, size * 0.86, self.font)
            xw = end - ww + 2
            self.print(was, end + 2, y, size * 0.86, 'rs', k=0.8 * k)
            self._ink(self.line([(xw - 3, y - size * 0.3), (end + 5, y - size * 0.3)], 1.8), 0.9 * k)
            end = xw - 12
        if leader and right:
            m = np.zeros((self.h, self.w), np.float32)
            for x in np.arange(x0 + wl + 10, end, 8.0):
                m = np.maximum(m, self.circle(x, y - 3, 1.25))
            self._ink(m, 0.85 * k)

    def rule(self, y, kind='dash', k=1.0):
        x0, x1 = self.margin, self.w - self.margin
        m = np.zeros((self.h, self.w), np.float32)
        if kind == 'dash':
            for x in np.arange(x0, x1 - 6, 13.0):
                m = np.maximum(m, self.rrect(x, y - 1, x + 7, y + 1, 0))
        elif kind == 'stars':
            n = int((x1 - x0) / 22)
            for i in range(n + 1):
                m = np.maximum(m, self.text('*', x0 + (x1 - x0) * i / n, y + 8, 22, self.font, 'ms'))
        elif kind == 'double':
            m = np.maximum(self.rrect(x0, y - 3, x1, y - 1.5, 0), self.rrect(x0, y + 1.5, x1, y + 3, 0))
        else:
            m = self.rrect(x0, y - 1, x1, y + 1, 0)
        self._ink(m, k)

    def crease(self, y0, y1=None, strength=1.0):
        """a fold line across the paper (it was folded once): a lit ridge on the light side, a soft dark
        valley on the other, slightly wavy"""
        y1 = y0 if y1 is None else y1
        yl = y0 + (y1 - y0) * self.XX / max(1, self.w) + 1.5 * np.interp(self.XX[0], np.linspace(0, self.w, 9), self.rng.normal(0, 1, 9))[None, :]
        d = self.YY - yl
        t = 1 + strength * (0.05 * np.exp(-((d + 2.5) / 2.2) ** 2) - 0.07 * np.exp(-((d - 1.5) / 1.4) ** 2) - 0.025 * np.exp(-((d - 8) / 7) ** 2))
        self.rgb *= t[..., None]

    def barcode(self, y, h, x0=None, x1=None, seed=None, k=1.0):
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        x0 = self.margin + 20 if x0 is None else x0
        x1 = self.w - self.margin - 20 if x1 is None else x1
        widths = [2, 1, 1, 2] + list(rng.integers(1, 5, 64)) + [2, 1, 1, 2]
        u = (x1 - x0) / sum(widths)
        m = np.zeros((self.h, self.w), np.float32); x = x0
        for i, wd in enumerate(widths):
            if i % 2 == 0:
                m = np.maximum(m, np.clip(np.minimum(self.XX - x, x + wd * u - self.XX) + 0.5, 0, 1) * (self.YY >= y) * (self.YY <= y + h))
            x += wd * u
        self._ink(m, k)


# ================================================================ Sticker: the board and everything on it
class Sticker:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.5, -0.62, 0.6)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.L = np.asarray(light, np.float32) / np.linalg.norm(light)
        d = np.array([-self.L[0], -self.L[1]]); self.away = d / np.linalg.norm(d)   # shadows fall this way
        self.img = np.ones((H, W, 3), np.float32) * _c('#EFE5D1')
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def art(self, w, h):
        return Art(w, h, self._seed())

    def receipt(self, w, h, **kw):
        return Receipt(w, h, self._seed(), **kw)

    # ------------------------------------------------------------ board
    def board(self, colour='#EFE5D1', kind='cream', fibres=None):
        """cream / light-kraft card: grain, mottling, pale and dark fibres, flecks"""
        H, W = self.H, self.W
        s = self._seed()
        mott = noise2d(H, W, 320, 4, s); blot = noise2d(H, W, 70, 3, s + 1); grain = noise2d(H, W, 1.4, 2, s + 2)
        k = 1.6 if kind == 'kraft' else 1.0
        t = 1 + k * (0.08 * (mott - 0.5) + 0.03 * (blot - 0.5)) + 0.035 * (grain - 0.5)
        img = _c(colour)[None, None, :] * t[..., None]
        img = img + ((mott - 0.5) * 0.03 * k)[..., None] * np.array([0.4, 0.1, -0.6], np.float32)   # darker patches warmer
        rng = np.random.default_rng(s + 3)
        n = fibres if fibres is not None else (520 if kind == 'kraft' else 380)
        lit = Image.new('L', (W, H), 0); dk = Image.new('L', (W, H), 0)
        dl, dd = ImageDraw.Draw(lit), ImageDraw.Draw(dk)
        for i in range(n):
            x, y = rng.uniform(-20, W + 20), rng.uniform(-20, H + 20)
            L, a = rng.uniform(14, 70), rng.uniform(0, np.pi)
            P = spline([(x, y), (x + np.cos(a) * L / 2 + rng.normal(0, 6), y + np.sin(a) * L / 2 + rng.normal(0, 6)),
                        (x + np.cos(a + rng.normal(0, .5)) * L, y + np.sin(a + rng.normal(0, .5)) * L)], 8)
            dark = rng.random() < (0.45 if kind == 'kraft' else 0.25)
            (dd if dark else dl).line([tuple(p) for p in P], fill=int(rng.uniform(70, 200)), width=1)
        for _ in range(int(n * (1.2 if kind == 'kraft' else 0.5))):
            x, y, r = rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0.5, 1.3)
            dd.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.uniform(90, 220)))
        fl = blur(np.asarray(lit, np.float32) / 255, 0.5); fd = blur(np.asarray(dk, np.float32) / 255, 0.5)
        img = img + (fl * 0.16)[..., None] * (1 - img)
        img = img * (1 - (fd * 0.22)[..., None] * (1 - _c('#6b4a22')))
        self.img = np.clip(img, 0, 1).astype(np.float32)

    # ------------------------------------------------------------ placement plumbing
    def _region(self, shape, cx, cy):
        h, w = shape[:2]
        x0 = int(round(cx - w / 2)); y0 = int(round(cy - h / 2))
        gx0, gy0, gx1, gy1 = max(0, x0), max(0, y0), min(self.W, x0 + w), min(self.H, y0 + h)
        if gx0 >= gx1 or gy0 >= gy1:
            return None, None
        return (slice(gy0, gy1), slice(gx0, gx1)), (slice(gy0 - y0, gy1 - y0), slice(gx0 - x0, gx1 - x0))

    @staticmethod
    def mapping(art, cx, cy, rot):
        """local art coords -> global board coords for an art laid/stuck at (cx, cy) with rotation rot"""
        t = np.deg2rad(rot); c, s = np.cos(t), np.sin(t)

        def T(x, y):
            dx, dy = x - art.w / 2, y - art.h / 2
            return (cx + dx * c - dy * s, cy + dx * s + dy * c)
        return T

    def _shade(self, reg, amount):
        """darken a region by a shadow amount (0..1), tinted warm"""
        return reg * (1 - amount[..., None] * (1 - _c(SHADOW)))

    # ------------------------------------------------------------ vinyl sticker
    def stick(self, art, cx, cy, rot=0.0, border=14, edge='#FBFAF6', peel=None, peel_size=44, lift=1.0,
              gloss=1.0, shadow=1.0, sheen=None):
        """die-cut vinyl sticker from an Art sheet, centred at (cx, cy), rot degrees clockwise.
        border: white die-cut margin in px (0 = cut on the art's own edge); peel: 'tr'|'tl'|'br'|'bl' folds
        that corner back; lift: how far it stands off (shadow length); gloss: laminate highlight strength;
        sheen: position 0..1 of the diagonal gloss streak (None = random)."""
        p = int(border * 2 + 18 + 10 * lift)
        A = np.pad(np.clip(art.a, 0, 1), p)
        P = np.pad(art.rgb, ((p, p), (p, p), (0, 0)))
        h, w = A.shape
        if border > 0:                                        # rounded dilation = the die line
            sg = border / 1.65
            b = blur(smoothstep(0.02, 0.3, A), sg)
            D = np.clip((b - 0.05) / (0.103 / sg * 1.5) + 0.5, 0, 1)
            D = np.maximum(D, A)
        else:
            D = A
        face = P + _c(edge) * (1 - A)[..., None]              # art printed over the white vinyl
        K, layers = D, None
        if peel:
            YY, XX = np.mgrid[0:h, 0:w].astype(np.float32)
            u = np.array({'tr': (1, -1), 'tl': (-1, -1), 'br': (1, 1), 'bl': (-1, 1)}[peel], np.float32) / np.sqrt(2)
            proj = XX * u[0] + YY * u[1]
            sd = proj - (proj[D > 0.5].max() - peel_size)      # > 0 inside the lifted corner
            K = D * np.clip(0.5 - sd, 0, 1)
            f = 0.78                                          # the flap is curled up: seen foreshortened
            along = XX * -u[1] + YY * u[0]
            ac = (along * (sd > -peel_size) * (sd < 0)).sum() / max(1, ((sd > -peel_size) * (sd < 0)).sum())
            bend = 1 + 0.25 * ((along - ac) / (peel_size * 1.6)) ** 2   # edges of the flap roll back more
            d = np.clip(-sd, 0, None)
            k = d * (1 + 1 / (f * bend))
            F = _sample(D, XX + u[0] * k, YY + u[1] * k) * np.clip(-sd * 2, 0, 1)
            tt = np.clip(d / (peel_size * f), 0, 1)
            Fs = 1.0 - 0.16 * tt ** 0.7 + 0.05 * np.exp(-d / 2.0)
            layers = (F, F * Fs)
        stack = [K, face[..., 0] * K, face[..., 1] * K, face[..., 2] * K]
        if layers: stack += list(layers)
        R = [_rotate(l, rot) for l in stack]
        K = np.clip(R[0], 0, 1)
        col = np.clip(np.stack(R[1:4], -1) / np.maximum(K, 1e-4)[..., None], 0, 1)
        F = np.clip(R[4], 0, 1) if layers else None
        U = np.clip(K + F, 0, 1) if layers else K
        gsl, lsl = self._region(K.shape, cx, cy)
        if gsl is None: return self.mapping(art, cx, cy, rot)
        ax, ay = self.away
        dist = 6 * lift
        soft = blur(shift(U, ax * dist, ay * dist), 4 + 4 * lift) * 0.30 * shadow
        cont = blur(shift(U, ax * 1.2, ay * 1.2), 1.3) * 0.40 * shadow
        sh = 1 - (1 - soft) * (1 - cont)
        # vinyl thickness: lit edge toward the light, darker cut edge away from it
        n = height_normals(blur(K, 1.0) * 2.4)
        lam = 1 + 1.0 * (n @ self.L - self.L[2])
        rim = np.clip(K - smoothstep(0.55, 0.95, blur(K, 1.3)), 0, 1)
        # laminate: specular rim on the lit edges and a faint diagonal sheen
        ng = height_normals(blur(K, 3.2) * 5.0)
        Hv = self.L + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        spec = np.clip((ng @ Hv - Hv[2]) / (1 - Hv[2]), 0, 1) ** 1.4 * 0.7 * gloss
        spec *= smoothstep(0.4, 0.9, K)
        YY, XX = np.mgrid[0:K.shape[0], 0:K.shape[1]].astype(np.float32)
        q = XX * 0.78 + YY
        qs = q[K > 0.5]
        if qs.size:
            pos = self.rng.uniform(0.25, 0.6) if sheen is None else sheen
            q0 = qs.min() + (qs.max() - qs.min()) * pos
            wd = (qs.max() - qs.min()) * 0.12
            band = smoothstep(wd, wd * 0.35, np.abs(q - q0)) * 0.09 + np.exp(-((q - q0 - wd * 1.6) / (wd * 0.18)) ** 2) * 0.06
        else:
            band = 0
        glow = np.clip(spec + band * gloss * K, 0, 1)
        fc = col * lam[..., None]
        fc = fc * (1 - (rim * 0.30)[..., None] * (1 - _c('#B9AE98')))
        fc = 1 - (1 - fc) * (1 - glow[..., None])
        reg = self._shade(self.img[gsl], sh[lsl])
        Kl = K[lsl][..., None]
        reg = reg * (1 - Kl) + np.clip(fc[lsl], 0, 1) * Kl
        if layers:                                            # the folded-back corner: pale backing side
            fsh = blur(shift(F, ax * 4, ay * 4), 3) * 0.45 * K * (1 - F)
            reg = self._shade(reg, fsh[lsl])
            shade = np.clip(R[5] / np.maximum(F, 1e-4), 0.5, 1.1)
            nf = height_normals(blur(F, 1.0) * 1.6)
            lf = 1 + 0.8 * (nf @ self.L - self.L[2])
            back = _c('#EEEBE3')[None, None, :] * (shade * lf)[..., None]
            frim = np.clip(F - smoothstep(0.55, 0.95, blur(F, 1.2)), 0, 1)
            back = back * (1 - (frim * 0.25)[..., None])
            Fl = F[lsl][..., None]
            reg = reg * (1 - Fl) + np.clip(back[lsl], 0, 1) * Fl
        self.img[gsl] = np.clip(reg, 0, 1)
        return self.mapping(art, cx, cy, rot)

    # ------------------------------------------------------------ paper laid on the board
    def lay(self, art, cx, cy, rot=0.0, curl=0.5, lift=1.0, shadow=1.0):
        """matte paper (receipt, tag): the ends of the long axis lift by `curl` (0..1), `lift` > 1 for a
        hanging tag. Returns the local -> global mapping."""
        p = int(34 + 16 * lift + 18 * curl)
        A = np.pad(np.clip(art.a, 0, 1), p)
        P = np.pad(art.rgb, ((p, p), (p, p), (0, 0)))
        h, w = A.shape
        YY, XX = np.mgrid[0:h, 0:w].astype(np.float32)
        if art.h >= art.w:
            v = (YY - h / 2) / (art.h / 2); u = (XX - w / 2) / (art.w / 2)
        else:
            v = (XX - w / 2) / (art.w / 2); u = (YY - h / 2) / (art.h / 2)
        hm = curl * (11 * np.clip(-v, 0, None) ** 3 + 7 * np.clip(v, 0, None) ** 3 + 0.5 * u ** 2)
        R = [_rotate(l, rot) for l in (A, P[..., 0], P[..., 1], P[..., 2], hm * A)]
        A = np.clip(R[0], 0, 1)
        col = np.clip(np.stack(R[1:4], -1) / np.maximum(A, 1e-4)[..., None], 0, 1)
        Hm = R[4] / np.maximum(A, 1e-3) * (A > 0.01)
        gsl, lsl = self._region(A.shape, cx, cy)
        if gsl is None: return self.mapping(art, cx, cy, rot)
        ax, ay = self.away
        hn = np.clip(Hm / (Hm.max() + 1e-6), 0, 1)
        cont = blur(shift(A, ax * 1.2, ay * 1.2), 1.6) * 0.26
        soft = blur(shift(A, ax * 4 * lift, ay * 4 * lift), 3 + 4 * lift) * 0.20
        up = blur(shift(A * smoothstep(0.15, 1.0, hn), ax * 14 * lift, ay * 14 * lift), 9 * lift + 4) * 0.22 * (curl > 0)
        sh = (1 - (1 - cont) * (1 - soft) * (1 - up)) * shadow
        n = height_normals(blur(Hm * A, 3))
        lam = 1 + 1.7 * (n @ self.L - self.L[2])
        ne = height_normals(blur(A, 0.8) * 1.2)               # paper thickness at the cut edge
        lam = lam * (1 + 0.6 * (ne @ self.L - self.L[2]))
        reg = self._shade(self.img[gsl], sh[lsl])
        Al = A[lsl][..., None]
        reg = reg * (1 - Al) + np.clip(col * lam[..., None], 0, 1)[lsl] * Al
        self.img[gsl] = np.clip(reg, 0, 1)
        return self.mapping(art, cx, cy, rot)

    # ------------------------------------------------------------ washi tape
    def tape(self, cx, cy, length, rot=0.0, colour='#E8AC2C', width=44, pattern='stripe', ink='#FFFFFF',
             alpha=0.8, seed=None):
        """a strip of washi tape; pattern: stripe | dot | grid | plain; ink = pattern colour"""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        m = int(width * 0.4 + 14)
        w, h = int(length + 2 * m), int(width + 2 * m)
        n = max(4, int(width / 6))

        def end(x0, sgn):
            ys = np.linspace(m, m + width, 2 * n + 1)
            tooth = np.where(np.arange(len(ys)) % 2 == 1, rng.uniform(2.5, 7.5, len(ys)), 0.0)
            return [(x0 + sgn * (t + rng.normal(0, 1.0)), y) for t, y in zip(tooth, ys)]
        left, right = end(m + 6, -1), end(m + length - 6, 1)
        M = polygon_mask(h, w, right + left[::-1], ss=3)
        YY, XX = np.mgrid[0:h, 0:w].astype(np.float32)
        fib = np.asarray(Image.fromarray(rng.random((h // 2 + 2, max(2, w // 16))).astype(np.float32)).resize((w, h), Image.BICUBIC), np.float32)
        fib = 0.94 + 0.09 * fib + 0.03 * (noise2d(h, w, 1.2, 1, int(rng.integers(1 << 30))) - 0.5)
        if pattern == 'stripe':
            q = (XX + YY) / (width * 0.42)
            pm = smoothstep(0.42, 0.58, np.abs((q % 1) - 0.5) * 2)
            pm = pm * 0.75
        elif pattern == 'dot':
            sp = width / 3.3
            row = np.round(YY / sp); xo = (row % 2) * sp / 2
            pm = np.clip(sp * 0.2 - np.hypot(XX - (np.round((XX - xo) / sp) * sp + xo), YY - row * sp) + 0.5, 0, 1) * 0.9
        elif pattern == 'grid':
            sp = width / 4.0
            gx = np.abs(((XX + 0.5 * sp) % sp) - 0.5 * sp); gy = np.abs(((YY + 0.5 * sp) % sp) - 0.5 * sp)
            pm = np.clip(1.4 - np.minimum(gx, gy), 0, 1) * 0.7
        else:
            pm = np.zeros((h, w), np.float32)
        col = _c(colour)[None, None, :] * fib[..., None]
        col = col * (1 - pm[..., None]) + _c(ink) * pm[..., None]
        edge_in = np.minimum(XX - m, m + length - XX)
        a = M * alpha * (0.93 + 0.07 * fib) * (0.82 + 0.18 * smoothstep(2, 10, edge_in))   # torn fibres thinner
        R = [_rotate(l, rot) for l in (a, col[..., 0] * a, col[..., 1] * a, col[..., 2] * a)]
        a = np.clip(R[0], 0, 1)
        col = np.clip(np.stack(R[1:4], -1) / np.maximum(a, 1e-4)[..., None], 0, 1)
        gsl, lsl = self._region(a.shape, cx, cy)
        if gsl is None: return
        ax, ay = self.away
        sh = blur(shift(a, ax * 1.3, ay * 1.3), 1.3) * 0.25
        reg = self._shade(self.img[gsl], sh[lsl])
        al = a[lsl][..., None]
        reg = reg * (1 - al) + al * col[lsl] * (0.55 + 0.45 * reg)     # translucent: dark things show through
        self.img[gsl] = np.clip(reg, 0, 1)

    # ------------------------------------------------------------ twine
    def twine(self, pts, width=4.2, colours=('#F4EEE2', '#D0402E'), shadow=0.32, drop=7, smooth=True):
        """twisted baker's twine along a curve through pts (drawn on top; put tape over its end)"""
        P = spline(pts, 30) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        x, y, ang, L = _resample(P, width * 0.42)
        mg = int(width * 3 + drop + 12)
        x0, y0 = int(np.floor(x.min())) - mg, int(np.floor(y.min())) - mg
        x1, y1 = int(np.ceil(x.max())) + mg, int(np.ceil(y.max())) + mg
        pw, ph = x1 - x0, y1 - y0
        ss = 3
        ci = Image.new('RGB', (pw * ss, ph * ss)); mi = Image.new('L', (pw * ss, ph * ss), 0)
        dc, dm = ImageDraw.Draw(ci), ImageDraw.Draw(mi)
        q = [((a - x0) * ss, (b - y0) * ss) for a, b in zip(x, y)]
        dm.line(q, fill=255, width=int(width * ss), joint='curve')
        for a, b in (q[0], q[-1]):
            r = width * ss / 2; dm.ellipse((a - r, b - r, a + r, b + r), fill=255)
        cols = [tuple(int(v * 255) for v in _c(c)) for c in colours]
        t = np.linspace(0, 2 * np.pi, 10, endpoint=False)
        for i, (a, b, th) in enumerate(zip(x, y, ang)):
            ph_ = th + 0.95
            ex, ey = np.cos(t) * width * 0.78, np.sin(t) * width * 0.30
            px = (a - x0 + ex * np.cos(ph_) - ey * np.sin(ph_)) * ss
            py = (b - y0 + ex * np.sin(ph_) + ey * np.cos(ph_)) * ss
            dc.polygon(list(zip(px, py)), fill=cols[(i // 2) % len(cols)])
        col = np.asarray(ci.resize((pw, ph), Image.BOX), np.float32) / 255
        M = np.asarray(mi.resize((pw, ph), Image.BOX), np.float32) / 255
        n = height_normals(blur(M, width * 0.3) * width * 0.9)
        lam = 1 + 1.3 * (n @ self.L - self.L[2])
        ax, ay = self.away
        sd = blur(shift(M, ax * drop, ay * drop), 2.2) * shadow
        cxm, cym = x0 + pw / 2, y0 + ph / 2
        gsl, lsl = self._region(M.shape, cxm, cym)
        if gsl is None: return
        reg = self._shade(self.img[gsl], sd[lsl])
        Ml = M[lsl][..., None]
        reg = reg * (1 - Ml) + np.clip(col * lam[..., None], 0, 1)[lsl] * Ml
        self.img[gsl] = np.clip(reg, 0, 1)

    # ------------------------------------------------------------ rubber stamp
    def stamp(self, cx, cy, r, ring='', centre='', sub='', colour='#D8412B', rot=0.0, strength=0.9,
              font='sans_bold', cjk='cjk_sans', centre_size=None, seed=None):
        """round rubber-stamp impression in translucent ink (multiplies with what is under it)"""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        S = int(r * 2 + 24); c = S / 2
        a = Art(S, S)
        m = np.maximum(a.ring(c, c, r * 0.965, r * 0.07), a.ring(c, c, r * 0.845, r * 0.02))
        m = np.maximum(m, a.ring(c, c, r * 0.575, r * 0.022))
        if ring:
            size = r * 0.155
            rt = r * 0.705
            adv = np.array([measure(ch, size, font, 0, cjk) + size * 0.18 for ch in ring])
            angs = np.cumsum(adv) - adv / 2
            angs = angs / adv.sum() * 360.0
            im = Image.new('L', (S, S), 0)
            for ch, ag in zip(ring, angs):
                if ch == ' ': continue
                g = _glyph(ch, size, font, cjk).rotate(-ag, resample=Image.BICUBIC)
                t = np.deg2rad(ag)
                px, py = c + np.sin(t) * rt - g.width / 2, c - np.cos(t) * rt - g.height / 2
                im.paste(255, (int(round(px)), int(round(py))), g)
            m = np.maximum(m, np.asarray(im, np.float32) / 255)
        if centre:
            cs = centre_size or r * 0.34
            m = np.maximum(m, a.text(centre, c, c - (r * 0.08 if sub else 0), cs, font, 'mm', stroke=max(1, int(cs * 0.03))))
        if sub:
            m = np.maximum(m, a.rrect(c - r * 0.3, c + r * 0.155, c + r * 0.3, c + r * 0.175, 0))
            m = np.maximum(m, a.text(sub, c, c + r * 0.32, r * 0.115, font, 'mm', stroke=1, spacing=r * 0.03))
        # ink: uneven pressure, paper tooth, pooled edges, slight bleed
        s0 = int(rng.integers(1 << 30))
        YY, XX = a.YY, a.XX
        phi = rng.uniform(0, 2 * np.pi)
        tilt = ((XX - c) * np.cos(phi) + (YY - c) * np.sin(phi)) / S
        press = 0.58 + 0.6 * (noise2d(S, S, S * 0.35, 2, s0) - 0.5) - 1.1 * tilt
        tooth = noise2d(S, S, 1.25, 2, s0 + 1)
        cover = smoothstep(0.24, 0.56, 0.6 * tooth + 0.6 * press)
        cover *= smoothstep(0.1, 0.24, noise2d(S, S, 2.2, 2, s0 + 3))          # pits where the rubber missed
        pool = np.clip(m - blur(m, 1.1), 0, 1)
        ink = m * cover * (0.78 + 0.22 * noise2d(S, S, 6, 2, s0 + 2)) + 0.35 * pool * cover
        ink = np.clip(blur(ink, 0.55), 0, 1)
        ink = np.clip(_rotate(ink, rot), 0, 1)
        gsl, lsl = self._region(ink.shape, cx, cy)
        if gsl is None: return
        k = (ink[lsl] * strength)[..., None]
        self.img[gsl] = self.img[gsl] * (1 - k * (1 - _c(colour)))

    # ------------------------------------------------------------ ballpoint pen
    def pen(self, pts, colour='#C9302A', width=3.0, smooth=True, strength=0.88, seed=None):
        """a ballpoint line through pts (global coords): tapered ends, pressure wobble, rare skips"""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        P = spline(pts, 14) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        x, y, _, L = _resample(P, 0.6)
        n = len(x)
        t = np.linspace(0, 1, n)
        press = (0.78 + 0.22 * fbm1d(n, 60, 3, int(rng.integers(1 << 30)))) * np.clip(np.minimum(t * L / 7, (1 - t) * L / 10), 0.25, 1) ** 0.5
        gate = fbm1d(n, 25, 2, int(rng.integers(1 << 30))) > -0.62
        mg = int(width * 2 + 4)
        x0, y0 = int(np.floor(x.min())) - mg, int(np.floor(y.min())) - mg
        pw, ph = int(np.ceil(x.max())) + mg - x0, int(np.ceil(y.max())) + mg - y0
        ss = 3
        im = Image.new('L', (pw * ss, ph * ss), 0); d = ImageDraw.Draw(im)
        for a, b, pr, g in zip(x, y, press, gate):
            rr = width / 2 * pr * ss
            v = int(255 * (0.55 + 0.45 * pr) * (1 if g else 0.35))
            X, Y = (a - x0) * ss, (b - y0) * ss
            d.ellipse((X - rr, Y - rr, X + rr, Y + rr), fill=v)
        M = np.asarray(im.resize((pw, ph), Image.BOX), np.float32) / 255
        gsl, lsl = self._region(M.shape, x0 + pw / 2, y0 + ph / 2)
        if gsl is None: return
        k = (np.clip(M[lsl] * 1.15, 0, 1) * strength)[..., None]
        self.img[gsl] = self.img[gsl] * (1 - k * (1 - _c(colour)))

    # ------------------------------------------------------------ ready-made sheets
    def lettering_art(self, parts, size, font='cjk_sans', weight=None, spacing=0.0, pad=None):
        """bold sticker lettering: parts = [(text, colour), ...] set on one line"""
        weight = max(1, int(size * 0.028)) if weight is None else weight
        pad = size * 0.12 if pad is None else pad
        ws = [measure(t, size, font, spacing) for t, _ in parts]
        a = self.art(sum(ws) + 2 * pad + 2 * weight + spacing * (len(parts) - 1), size * 1.12 + 2 * pad)
        x = pad + weight
        for (t, col), wd in zip(parts, ws):
            a.fill(a.text(t, x, a.h / 2, size, font, 'lm', stroke=weight, spacing=spacing), col)
            x += wd + spacing
        return a

    def label_art(self, s, size, bg, fg, font='sans_bold', dot=None, spacing=0.0, padx=None, height=None, radius=None):
        """pill-shaped label sticker (optional coloured dot before the text)"""
        tw = measure(s, size, font, spacing)
        padx = size * 0.75 if padx is None else padx
        hh = size * 1.9 if height is None else height
        dw = size * 0.85 if dot else 0
        a = self.art(tw + 2 * padx + dw, hh)
        a.fill(a.rrect(0, 0, a.w - 1, a.h - 1, hh / 2 if radius is None else radius), bg)
        if dot:
            a.fill(a.circle(padx + size * 0.22, hh / 2, size * 0.2), dot)
        a.fill(a.text(s, padx + dw, hh / 2, size, font, 'lm', spacing=spacing), fg)
        return a

    def badge_art(self, r, colour, big, top='', bottom='', ink='#FBF3E4', scallops=24, depth=0.035,
                  big_size=None, font='sans_bold', light=None):
        """round sale badge with a scalloped rim, a dotted inner ring and three lines of text"""
        S = int(2 * r + 6); c = S / 2
        a = self.art(S, S)
        th = np.arctan2(a.YY - c, a.XX - c); rr = np.hypot(a.XX - c, a.YY - c)
        R = r * (1 - depth + depth * np.cos(scallops * th))
        m = np.clip(R - rr + 0.5, 0, 1)
        lc = light or tuple(np.clip(_c(colour) * 1.12 + 0.04, 0, 1))
        a.radial(m, lc, colour, c - r * 0.35, c - r * 0.4, r * 1.5)
        dots = np.zeros((S, S), np.float32)
        for t in np.linspace(0, 2 * np.pi, 44, endpoint=False):
            dots = np.maximum(dots, a.circle(c + np.cos(t) * r * 0.82, c + np.sin(t) * r * 0.82, r * 0.016))
        a.fill(dots, ink, 0.9, clip=True)
        a.fill(a.text(big, c, c + r * 0.02, big_size or r * 0.44, font, 'mm', stroke=max(1, int(r * 0.012))), ink)
        if top:
            a.fill(a.text(top, c, c - r * 0.42, r * 0.13, font, 'mm', spacing=r * 0.035), ink)
        if bottom:
            a.fill(a.text(bottom, c, c + r * 0.45, r * 0.15, font, 'mm', spacing=r * 0.01), ink)
        return a

    def tag_art(self, w, h, colour='#D9C7A3', grommet='#C9A55C', clip=None, hole_r=8.0, kind='kraft'):
        """card price tag: clipped top corners, a hole near the top with a metal grommet; .hole = (x, y)"""
        a = self.art(w, h)
        c = clip or w * 0.28
        m = a.poly([(c, 1), (w - 1 - c, 1), (w - 1, c), (w - 1, h - 1), (1, h - 1), (1, c)])
        m = smoothstep(0.3, 0.7, blur(m, 2.2))
        a.fill(m, colour)
        a.texture(kind, 1.0)
        hx, hy = w / 2, c * 0.92
        ro = hole_r * 1.95
        rim = np.clip(a.circle(hx, hy, ro) - a.circle(hx, hy, hole_r), 0, 1)
        lit = np.clip(-((a.XX - hx) * self.L[0] + (a.YY - hy) * self.L[1]) / ro, -1, 1)
        rr = np.hypot(a.XX - hx, a.YY - hy)
        inner = np.clip(1 - (rr - hole_r) / (ro - hole_r), 0, 1)
        g = 0.82 + 0.35 * lit * (1 - inner) - 0.35 * lit * inner ** 3
        gcol = np.clip(_c(grommet)[None, None, :] * g[..., None], 0, 1)
        a.fill(np.clip(blur(rim, 1.2) * 0.5 * (1 - rim), 0, 1), '#5a4a30', 0.6, clip=True)   # the rolled lip's shadow on the card
        a._over(rim, gcol, clip=False)
        a.cut(a.circle(hx, hy, hole_r))
        a.hole = (hx, hy)
        return a

    # ------------------------------------------------------------ output
    def composite(self, vignette=0.16):
        g = np.exp(-(((self.XX - self.W * 0.3) / (self.W * 0.7)) ** 2 + ((self.YY - self.H * 0.2) / (self.H * 0.9)) ** 2))
        r = np.hypot((self.XX - self.W / 2) / self.W, (self.YY - self.H / 2) / self.H)
        img = self.img * (0.95 + 0.07 * g)[..., None] * (1 - vignette * r ** 2 * 2.2)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite(); img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
