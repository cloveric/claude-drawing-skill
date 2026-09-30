"""bauhaus — a geometric-constructivist poster in the Bauhaus manner, hand-pulled as a screen print on cream stock:
red, yellow and blue plus black, circles, triangles, squares and heavy bars on a strict grid, big geometric sans
lettering (numpy + Pillow only).

Model: the picture is a press sheet. Every colour is its own screen, pulled one after another, light to dark.
  stock      uncoated cream paper: a cloudy, slightly warmer tone where the pulp is thicker, short fibres, a few dark
             flecks in the pulp, a per-pixel "tooth" (the tiny hills and pits of the surface) and a very low
             cockle -- the sheet is never perfectly flat, so the room light rolls across it.
  grid       a pale warm-grey tint screen prints the construction grid (the module every shape and every line of
             type sits on), the way a designer's proof sheet shows it.
  screens    one per ink. A screen is laid down once per colour, so everything printed in one ink shares that
             screen's registration error: a small shift (and a hair of rotation about the sheet centre) against
             the other colours. Where a colour meets black exactly, the error opens a sliver of bare paper on one
             side and a dark overlap on the other; the register targets and crop marks are on every screen, so
             they print as a little stack of coloured crosshairs, and each screen adds its own patch (and the
             overprint patches) to the colour bar.
  ink film   the squeegee pulls the ink through the mesh in one direction. The film is a little thicker or thinner
             in long streaks along the pull, blotchy on a larger scale, and runs slightly thin toward the end of
             the stroke. Where the film is thin the deepest pits of the tooth stay bare (fine paper-coloured grain),
             dust on the stencil leaves pinholes, the stencil edge is ragged at the scale of the mesh and the ink
             squeezes a hair past it, and the edge of a solid carries slightly more ink than its middle.
  inks       semi-opaque, like real screen inks: a pull partly covers what is under it and partly multiplies with
             it (yellow is the most transparent, black the least), so overprints turn into darker mixed colours.
  type       a heavy geometric sans (Futura Bold via core.latin_font('geometric'), else the system bold sans) for
             Latin, a heavy system Hei (黑体) for Chinese; mixed strings switch font per character. Type is just a
             stencil on the black screen, so it has the same grain and edge as the shapes, and can be knocked out
             of a solid (`knock=`), leaving the paper to show through.
  pencil     after printing, the edition number is written in the margin in soft graphite, which only catches the
             tops of the paper tooth.
Coordinates are pixels; `at(col, row)` converts grid cells (fractions allowed) into pixels. Angles are degrees
counter-clockwise from 3 o'clock (like a maths diagram); `rot` of rectangles and text is counter-clockwise too.

    from bauhaus import Bauhaus, YELLOW, RED, BLUE, BLACK
    b = Bauhaus(1920, 1080, seed=3)
    b.paper(margin=60, module=120)
    b.marks(targets=[(960, 30), (960, 1050)], bar=(1712, 1040))   # register targets, crop marks, colour bar
    b.grid()                                                      # tint screen: construction grid
    b.pull(b.triangle(60, 600, 840), YELLOW)                      # one pull of the yellow screen
    b.pull(b.rect(720, 360, 1200, 840), RED)
    b.pull(b.circle(1560, 600, 240), BLUE)
    b.pull(b.rect(60, 840, 1860, 866), BLACK)                     # a heavy black bar
    b.text('形与色', 60, 262, 210, font='cjk')
    b.pull(b.rect(720, 190, 1860, 282), BLACK, knock=b.text_mask('FORM', 752, 258, 60))   # type knocked out
    b.pencil('7/40', 86, 1060, 28)
    b.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, noise2d, smoothstep, shift, latin_font

YELLOW, RED, BLUE, BLACK = '#f2bd1b', '#d63129', '#1f4e9c', '#1a1917'
PAPER, TINT = '#f0e7d4', '#d6cab4'
OPACITY = {YELLOW: 0.62, RED: 0.84, BLUE: 0.88, BLACK: 0.97, TINT: 0.35}     # the rest multiplies with what's under
GRAIN = {YELLOW: 0.9, RED: 0.72, BLUE: 0.66, BLACK: 0.4, TINT: 0.3}            # how much bare tooth shows in thin film


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- fonts (kept inside this module)
_STYLE, _FONTS, _HAS = {}, {}, {}


def _face_of(hit, want, avoid=()):
    """in the collection `hit` = (path, index), the first face whose style name has every word of `want`"""
    if not hit: return None
    for i in range(32):
        try:
            f = ImageFont.truetype(hit[0], 20, index=i)
        except (OSError, ValueError):
            break
        sty = f.getname()[1] or ''
        if all(w in sty for w in want) and not any(a in sty for a in avoid):
            return hit[0], i
    return None


def _find(style):
    """(path, index) for a style: geo (heavy geometric sans), geo_book, geo_cond, cjk (heavy Hei), cjk_book, hand"""
    if style in _STYLE: return _STYLE[style]
    env = os.environ.get('INKPAINT_FONT_' + style.upper())
    if env and os.path.exists(env):
        hit = (env, 0)
    elif style == 'geo':
        hit = _face_of(latin_font('geometric'), ('Bold',), ('Italic', 'Oblique', 'Condensed')) or latin_font('sans_bold')
    elif style == 'geo_book':
        hit = latin_font('geometric') or latin_font('sans')
    elif style == 'geo_cond':
        hit = (_face_of(latin_font('geometric'), ('Condensed', 'Bold'), ('Italic',)) or latin_font('condensed')
               or latin_font('sans_bold'))
    elif style == 'cjk':
        hg = '/System/Library/Fonts/Hiragino Sans GB.ttc'                  # 冬青黑体 W6 if present (macOS)
        hit = (_face_of((hg, 0), ('W6',)) if os.path.exists(hg) else None) or latin_font('cjk_sans') or latin_font('cjk')
    elif style == 'cjk_book':
        hit = latin_font('cjk_sans') or latin_font('cjk')
    elif style == 'hand':
        hit = latin_font('hand') or latin_font('sans')
    else:
        hit = latin_font(style)
    _STYLE[style] = hit
    return hit


def _font(style, size):
    k = (style, int(round(size)))
    if k not in _FONTS:
        hit = _find(style)
        size = max(4, int(round(size)))
        _FONTS[k] = ImageFont.truetype(hit[0], size, index=hit[1]) if hit else ImageFont.load_default(size)
    return _FONTS[k]


def _box3(a):
    """3 x 3 box average (a very light blur that keeps corners sharp)"""
    p = np.pad(a, 1, mode='edge')
    h, w = a.shape
    return sum(p[i:i + h, j:j + w] for i in range(3) for j in range(3)) / 9


_KERN = {'°': -0.1}                                                         # em; the degree sign sits too far off


def _is_cjk(ch):
    o = ord(ch)
    return 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F


def _has(style, ch):
    """does the font for `style` draw a real glyph for ch (not the .notdef box)?"""
    k = (style, ch)
    if k not in _HAS:
        f = _font(style, 48)
        a, b = f.getmask(ch), f.getmask('')
        _HAS[k] = ch.isspace() or not (a.size == b.size and bytes(a) == bytes(b))
    return _HAS[k]


def _pick(ch, style):
    """per-character font: Chinese in the Hei, Latin in the geometric sans; a missing glyph falls back to the other"""
    cjk_style = 'cjk_book' if style == 'cjk_book' else 'cjk'
    lat_style = 'geo' if style in ('cjk', 'cjk_book') else style
    if _is_cjk(ch):
        return cjk_style
    if _has(lat_style, ch): return lat_style
    return cjk_style if _has(cjk_style, ch) else lat_style


class Bauhaus:
    def __init__(self, W=1920, H=1080, seed=0, misreg=2.6, pull=90.0):
        """misreg: typical registration error of a screen, px. pull: squeegee direction in degrees (90 = the stroke
        runs down the sheet, 0 = left to right)"""
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.misreg, self.pull_dir = misreg, pull
        self.paper_col = _c(PAPER)
        self.img = np.ones((H, W, 3), np.float32) * self.paper_col
        self.fibre = np.ones((H, W), np.float32)
        self.light = np.ones((H, W), np.float32)
        g = self.rng.random((H, W)).astype(np.float32)                     # pixel-sized pits ...
        c = noise2d(H, W, 6.0, 2, self._seed())                             # ... a little clumped
        t = 0.8 * (g - 0.5) / 0.29 + 0.5 * (c - c.mean()) / (c.std() + 1e-6)
        self.tooth = np.clip(0.5 + t / 3.8, 0, 1).astype(np.float32)        # 1 = the deepest pits of the surface
        self.screens = {}
        self._reg = None                                                    # register targets + crop marks
        self._patches = []                                                  # colour-bar patches: (mask, inks)
        self._mark_inks = ()
        self.x0, self.y0, self.x1, self.y1, self.M = 0, 0, W, H, 120
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ the sheet
    def paper(self, colour=PAPER, margin=60, module=120, warm='#e6d6b6'):
        """uncoated cream stock. Sets the design area (the sheet minus `margin`) and the grid module."""
        H, W, r = self.H, self.W, self.rng
        self.paper_col = _c(colour)
        self.x0, self.y0, self.x1, self.y1, self.M = margin, margin, W - margin, H - margin, module
        cloud = noise2d(H, W, 360, 4, self._seed())
        t = smoothstep(0.35, 0.9, cloud)[..., None] * 0.22                  # thicker pulp: a touch warmer, darker
        base = self.paper_col * (1 - t) + _c(warm) * t
        base = base * (1 + 0.012 * (noise2d(H, W, 60, 3, self._seed()) - 0.5))[..., None]
        self.img = base.astype(np.float32)
        # short fibres, some lighter and some darker than the sheet
        fim = Image.new('L', (W, H), 128)
        d = ImageDraw.Draw(fim)
        for _ in range(int(W * H / 700)):
            x, y = r.uniform(0, W), r.uniform(0, H)
            a, L = r.uniform(0, np.pi), r.uniform(5, 26)
            bend = r.normal(0, 0.25)
            pts = [(x + np.cos(a + bend * s) * L * s, y + np.sin(a + bend * s) * L * s) for s in np.linspace(-0.5, 0.5, 5)]
            d.line(pts, fill=int(128 + r.choice([-1, 1]) * r.uniform(10, 30)), width=1)
        fib = blur((np.asarray(fim, np.float32) - 128) / 128, 0.6)
        fine = blur(r.random((H, W)).astype(np.float32), 0.7)
        fine = (fine - fine.mean()) / (fine.std() + 1e-6)
        self.fibre = (1 + 0.05 * fib + 0.006 * fine).astype(np.float32)
        # flecks in the pulp (they sit under the ink)
        fl = Image.new('L', (W * 2, H * 2), 0)
        d = ImageDraw.Draw(fl)
        for _ in range(int(W * H / 9000)):
            x, y, rr = r.uniform(0, W * 2), r.uniform(0, H * 2), r.uniform(0.7, 2.6) * (3 if r.random() < 0.04 else 1)
            d.ellipse((x - rr, y - rr * r.uniform(0.5, 1), x + rr, y + rr * r.uniform(0.5, 1)), fill=int(r.uniform(70, 200)))
        fl = np.asarray(fl.resize((W, H), Image.BOX), np.float32) / 255
        self.img *= (1 - fl[..., None] * (1 - _c('#6a5a45')))
        # room light rolling over a sheet that is not quite flat
        cockle = noise2d(H, W, 520, 2, self._seed()) - 0.5
        grad = 1 + 0.03 * (0.5 - (self.XX / W * 0.65 + self.YY / H * 0.35))
        vig = 1 - 0.06 * (((self.XX - W * 0.5) / W) ** 2 + ((self.YY - H * 0.48) / H) ** 2) * 2
        self.light = (grad * vig + 0.022 * cockle).astype(np.float32)

    def at(self, c, r):
        """grid cell (col, row) -> pixel (x, y); fractions allowed"""
        return self.x0 + c * self.M, self.y0 + r * self.M

    # ------------------------------------------------------------ masks (full canvas, anti-aliased, 0..1)
    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def ring(self, cx, cy, r, width):
        return np.clip(width / 2 - np.abs(np.hypot(self.XX - cx, self.YY - cy) - r) + 0.5, 0, 1)

    def _wedge(self, cx, cy, a0, a1):
        """signed distance to the wedge between angles a0 -> a1 (ccw, degrees)"""
        dx, dy = self.XX - cx, self.YY - cy
        t0, t1 = np.deg2rad(a0), np.deg2rad(a1)
        h0 = -np.cos(t0) * dy - np.sin(t0) * dx                            # left of the a0 ray
        h1 = np.cos(t1) * dy + np.sin(t1) * dx                             # right of the a1 ray
        span = (a1 - a0) % 360
        return np.minimum(h0, h1) if span <= 180 else np.maximum(h0, h1)

    def sector(self, cx, cy, r, a0, a1):
        """a slice of a disc from angle a0 to a1 (ccw): (0, 180) is the upper half, (270, 360) the lower-right quarter"""
        return np.minimum(self.circle(cx, cy, r), np.clip(self._wedge(cx, cy, a0, a1) + 0.5, 0, 1))

    def arc(self, cx, cy, r, a0, a1, width):
        """a line arc of radius r from a0 to a1 (ccw), butt ends"""
        return np.minimum(self.ring(cx, cy, r, width), np.clip(self._wedge(cx, cy, a0, a1) + 0.5, 0, 1))

    def rect(self, x0, y0, x1, y1, rot=0.0):
        if not rot:
            return (np.clip(np.minimum(self.XX - x0, x1 - self.XX) + 0.5, 0, 1)
                    * np.clip(np.minimum(self.YY - y0, y1 - self.YY) + 0.5, 0, 1))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        t = np.deg2rad(rot)
        c, s = np.cos(t), np.sin(t)
        pts = [(cx + u * c + v * s, cy - u * s + v * c) for u, v in
               [(x0 - cx, y0 - cy), (x1 - cx, y0 - cy), (x1 - cx, y1 - cy), (x0 - cx, y1 - cy)]]
        return self.poly(pts)

    def bar(self, x0, y0, x1, y1, width, cap='butt'):
        """a straight bar (or a rule, when thin) from (x0, y0) to (x1, y1); cap 'butt' | 'square' | 'round'"""
        dx, dy = x1 - x0, y1 - y0
        L = float(np.hypot(dx, dy)) + 1e-6
        ux, uy = dx / L, dy / L
        u = (self.XX - x0) * ux + (self.YY - y0) * uy
        v = -(self.XX - x0) * uy + (self.YY - y0) * ux
        if cap == 'round':
            uc = np.clip(u, 0, L)
            return np.clip(width / 2 - np.hypot(u - uc, v) + 0.5, 0, 1)
        ext = width / 2 if cap == 'square' else 0
        return np.clip(np.minimum(width / 2 - np.abs(v), np.minimum(u + ext, L + ext - u)) + 0.5, 0, 1)

    def poly(self, pts):
        """filled polygon; convex ones are exact (half-plane distances), others are supersampled"""
        P = np.asarray(pts, np.float64)
        n = len(P)
        e = np.roll(P, -1, 0) - P
        cr = e[:, 0] * np.roll(e, -1, 0)[:, 1] - e[:, 1] * np.roll(e, -1, 0)[:, 0]
        if np.all(cr >= -1e-9) or np.all(cr <= 1e-9):
            sgn = 1.0 if cr.sum() > 0 else -1.0
            d = np.full((self.H, self.W), 1e9, np.float32)
            for i in range(n):
                ex, ey = e[i] / (np.hypot(*e[i]) + 1e-9)
                # inside is to the right of each edge for clockwise-on-screen order, flip for the other order
                np.minimum(d, sgn * ((self.XX - P[i, 0]) * ey - (self.YY - P[i, 1]) * ex) * -1, out=d)
            return np.clip(d + 0.5, 0, 1)
        ss = 4
        x0, y0 = int(np.floor(P[:, 0].min())) - 2, int(np.floor(P[:, 1].min())) - 2
        x1, y1 = int(np.ceil(P[:, 0].max())) + 2, int(np.ceil(P[:, 1].max())) + 2
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P], fill=255)
        a = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return self._place(a, x0, y0)

    def triangle(self, x0, x1, base_y, apex=None, height=None):
        """a triangle standing on the line base_y between x0 and x1; equilateral unless apex / height is given"""
        if apex is None:
            h = height if height is not None else (x1 - x0) * np.sqrt(3) / 2
            apex = ((x0 + x1) / 2, base_y - h)
        return self.poly([(x0, base_y), apex, (x1, base_y)])

    def _place(self, a, x0, y0):
        out = np.zeros((self.H, self.W), np.float32)
        h, w = a.shape
        ys, xs = max(0, y0), max(0, x0)
        ye, xe = min(self.H, y0 + h), min(self.W, x0 + w)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = a[ys - y0:ye - y0, xs - x0:xe - x0]
        return out

    # ------------------------------------------------------------ type
    def text_mask(self, s, x, y, size, font='geo', anchor='ls', spacing=0.0, rot=0.0, weight=0.0, ss=2):
        """lettering -> full-canvas mask. anchor: l/m/r then s (baseline), m (middle of the capitals), t (cap top).
        font: geo (heavy geometric sans), geo_book, geo_cond, cjk (heavy Hei), cjk_book. spacing: extra px per letter.
        rot: degrees ccw about (x, y). weight: faux-bold px."""
        chars = [(ch, _pick(ch, font)) for ch in s]
        runs = []                                                          # consecutive same-font chars keep kerning
        for ch, st in chars:
            if runs and runs[-1][1] == st and not spacing and ch not in _KERN:
                runs[-1][0] += ch
            else:
                runs.append([ch, st])
        advs = [_font(st, size).getlength(t) + spacing * len(t) + _KERN.get(t[0], 0) * size for t, st in runs]
        total = sum(advs) - (spacing if s else 0)
        if any(_is_cjk(ch) for ch in s):
            capH = -_font('cjk' if font != 'cjk_book' else 'cjk_book', size).getbbox('中', anchor='ls')[1] * 0.93
        else:
            capH = -_font(_pick('H', font), size).getbbox('H', anchor='ls')[1]
        desc = size * 0.28
        dyb = {'s': 0, 'm': capH / 2, 't': capH, 'a': capH, 'b': -desc, 'd': -desc}.get(anchor[1], 0)
        xs0 = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        base = y + dyb
        pad = int(size * 0.3 + weight + 6)
        bx0, by0 = int(np.floor(xs0)) - pad, int(np.floor(base - capH * 1.3)) - pad
        bx1, by1 = int(np.ceil(xs0 + total)) + pad, int(np.ceil(base + desc)) + pad
        im = Image.new('L', ((bx1 - bx0) * ss, (by1 - by0) * ss), 0)
        d = ImageDraw.Draw(im)
        cx = (xs0 - bx0) * ss
        for (t, st), adv in zip(runs, advs):
            f = _font(st, size * ss)
            cx += _KERN.get(t[0], 0) * size * ss
            if spacing:
                for ch in t:
                    if not ch.isspace():
                        d.text((cx, (base - by0) * ss), ch, font=f, fill=255, anchor='ls',
                               stroke_width=int(round(weight * ss)), stroke_fill=255)
                    cx += (f.getlength(ch) + spacing * ss)
            else:
                d.text((cx, (base - by0) * ss), t, font=f, fill=255, anchor='ls',
                       stroke_width=int(round(weight * ss)), stroke_fill=255)
                cx += (adv - _KERN.get(t[0], 0) * size) * ss
        a = np.asarray(im.resize((bx1 - bx0, by1 - by0), Image.BOX), np.float32) / 255
        if rot:
            R = int(np.hypot(bx1 - bx0, by1 - by0)) + 4
            big = np.zeros((2 * R, 2 * R), np.float32)
            ox, oy = int(round(x)) - R, int(round(y)) - R
            big[by0 - oy:by1 - oy, bx0 - ox:bx1 - ox] = a
            bim = Image.fromarray((big * 255).astype(np.uint8)).rotate(rot, resample=Image.BICUBIC,
                                                                     center=(x - ox, y - oy))
            return self._place(np.asarray(bim, np.float32) / 255, ox, oy)
        return self._place(a, bx0, by0)

    def text_width(self, s, size, font='geo', spacing=0.0):
        return sum(_font(_pick(ch, font), size).getlength(ch) + spacing + _KERN.get(ch, 0) * size for ch in s) - (spacing if s else 0)

    def text(self, s, x, y, size, ink=BLACK, font='geo', anchor='ls', spacing=0.0, rot=0.0, weight=0.0):
        """print lettering through the screen of `ink` (default black)"""
        m = self.text_mask(s, x, y, size, font, anchor, spacing, rot, weight)
        self.pull(m, ink, edge=float(np.clip((size - 14) / 50, 0, 1)))
        return m

    # ------------------------------------------------------------ printer's marks
    def marks(self, targets=(), crop=True, bar=None, patch=22, gap=4, inks=(YELLOW, RED, BLUE, BLACK),
              overprints=False, r=10, hair=1.4):
        """register targets (ring + crosshair) at `targets`, crop marks at the corners of the design area and a colour
        bar whose top-left is `bar`. They are carried by every screen in `inks`: each pull of a new ink prints its
        copy (with that screen's registration error) and its patches."""
        m = np.zeros((self.H, self.W), np.float32)
        for (x, y) in targets:
            m = np.maximum(m, self.ring(x, y, r, hair))
            m = np.maximum(m, self.bar(x - r - 9, y, x + r + 9, y, hair))
            m = np.maximum(m, self.bar(x, y - r - 9, x, y + r + 9, hair))
        if crop:
            g, L = 10, 30
            for (cx, cy, sx, sy) in [(self.x0, self.y0, -1, -1), (self.x1, self.y0, 1, -1),
                                     (self.x0, self.y1, -1, 1), (self.x1, self.y1, 1, 1)]:
                m = np.maximum(m, self.bar(cx + sx * g, cy, cx + sx * (g + L), cy, hair))
                m = np.maximum(m, self.bar(cx, cy + sy * g, cx, cy + sy * (g + L), hair))
        self._reg = m
        self._patches = []
        if bar is not None:
            sets = [(k,) for k in inks]
            if overprints:
                col = [k for k in inks if k != BLACK]
                sets += [(a, b) for i, a in enumerate(col) for b in col[i + 1:]]
            x, y = bar
            for k, st in enumerate(sets):
                px = x + k * (patch + gap)
                self._patches.append((self.rect(px, y, px + patch, y + patch), set(st)))
        self._mark_inks = tuple(inks)
        for k in list(self.screens):                                       # screens already used print theirs now
            self._print_marks(k)

    def _print_marks(self, ink):
        if ink not in self._mark_inks or self._reg is None: return
        m = self._reg.copy()
        for pm, st in self._patches:
            if ink in st: m = np.maximum(m, pm)
        self.pull(m, ink, edge=0.0)

    # ------------------------------------------------------------ screens and the pull
    def _screen(self, ink):
        if ink in self.screens: return self.screens[ink]
        H, W, r = self.H, self.W, self.rng
        a = r.uniform(0, 2 * np.pi)
        mag = self.misreg * r.uniform(0.55, 1.0) * (0.4 if ink == TINT else 1.0)
        t = np.deg2rad(self.pull_dir)
        # film thickness: long streaks along the pull, blotches, thinning toward the end of the stroke
        along = (self.XX * np.cos(t) + self.YY * np.sin(t))
        along = (along - along.min()) / (along.max() - along.min() + 1e-6)
        k = bool(abs(np.sin(t)) > 0.5)                                      # streaks run along y for a vertical pull
        gh, gw = (H // 40 + 3, W // 2 + 3) if k else (H // 2 + 3, W // 40 + 3)
        st = np.asarray(Image.fromarray(r.random((gh, gw)).astype(np.float32)).resize((W, H), Image.BICUBIC))
        bh, bw = (3, W // 70 + 3) if k else (H // 70 + 3, 3)
        band = np.asarray(Image.fromarray(r.random((bh, bw)).astype(np.float32)).resize((W, H), Image.BICUBIC))
        blot = noise2d(H, W, 70, 3, self._seed())
        film = 1.0 - 0.04 * (st - 0.5) - 0.05 * (band - 0.5) - 0.06 * (blot - 0.5) - 0.04 * smoothstep(0.55, 1, along)
        # pinholes: dust on the stencil
        pim = Image.new('L', (W * 2, H * 2), 0)
        d = ImageDraw.Draw(pim)
        for _ in range(int(W * H / 16000)):
            x, y, rr = r.uniform(0, W * 2), r.uniform(0, H * 2), r.uniform(0.8, 2.4)
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=int(r.uniform(120, 255)))
        pins = np.asarray(pim.resize((W, H), Image.BOX), np.float32) / 255
        fine = blur(r.random((H, W)).astype(np.float32), 1.0)
        fine = np.clip(0.5 + (fine - fine.mean()) / (fine.std() + 1e-6) * 0.18, 0, 1)
        scr = dict(t=(np.cos(a) * mag, np.sin(a) * mag), rot=r.normal(0, 0.00032), film=film.astype(np.float32),
                   pins=pins, fine=fine.astype(np.float32),
                   roll=(int(r.integers(0, H)), int(r.integers(0, W))))
        self.screens[ink] = scr
        self._print_marks(ink)
        return scr

    def _subshift(self, a, dx, dy):
        ix, iy = int(np.floor(dx)), int(np.floor(dy))
        fx, fy = dx - ix, dy - iy
        return ((1 - fx) * (1 - fy) * shift(a, ix, iy) + fx * (1 - fy) * shift(a, ix + 1, iy)
                + (1 - fx) * fy * shift(a, ix, iy + 1) + fx * fy * shift(a, ix + 1, iy + 1))

    def pull(self, mask, ink, knock=None, edge=1.0, density=1.0, opacity=None):
        """one pull of the squeegee: print `mask` in `ink` through that ink's screen.
        knock: a mask cut out of the stencil (knocked-out type). edge: 0 keeps hairlines clean, 1 = full
        ragged mesh edge. density scales the ink film; opacity overrides the ink's own covering power."""
        m = np.clip(mask if knock is None else mask - knock, 0, 1).astype(np.float32)
        rows, cols = np.flatnonzero(m.max(1) > 0.002), np.flatnonzero(m.max(0) > 0.002)
        if not len(rows): return
        scr = self._screen(ink)
        p = int(self.misreg * 2 + 10)
        y0, y1 = max(0, rows[0] - p), min(self.H, rows[-1] + p + 1)
        x0, x1 = max(0, cols[0] - p), min(self.W, cols[-1] + p + 1)
        sl = (slice(y0, y1), slice(x0, x1))
        # this screen's registration error, evaluated where the shape is
        cx, cy = (x0 + x1) / 2 - self.W / 2, (y0 + y1) / 2 - self.H / 2
        dx = scr['t'][0] - scr['rot'] * cy
        dy = scr['t'][1] + scr['rot'] * cx
        mm = self._subshift(m[sl], dx, dy)
        if edge > 0:                                                       # ragged stencil edge, ink spread
            fine = np.roll(scr['fine'], scr['roll'], (0, 1))[sl]
            mb = _box3(mm)
            e = mb + (fine - 0.5) * 0.3 * edge + 0.03
            m2 = smoothstep(0.5 - 0.2, 0.5 + 0.2, e) * np.clip(mb * 3, 0, 1)
            m2 = mm * (1 - edge) + m2 * edge
        else:
            m2 = mm
        film = scr['film'][sl] * density
        tooth = self.tooth[sl]
        g = GRAIN.get(ink, 0.8)
        bare = smoothstep(0.91, 1.0, tooth + (1.0 - film) * 2.6 - 0.02) * g         # pits the thin film misses
        cover = np.clip(1 - bare - scr['pins'][sl] * 0.85, 0, 1)
        rim = np.clip(m2 - blur(m2, 2.5), 0, 1) if edge > 0 else 0
        micro = 1 - 0.05 * (tooth - 0.5)                                           # the film follows the tooth
        dd = np.clip(m2 * np.clip(film, 0, 1) * cover * micro, 0, 1)[..., None]
        op = OPACITY.get(ink, 0.8) if opacity is None else opacity
        col = _c(ink)[None, None, :] * (1 - 0.07 * (rim[..., None] if edge > 0 else 0))
        cur = self.img[sl]
        T = cur * (1 - dd + dd * np.clip(col / self.paper_col, 0, 1.2))          # the transparent part multiplies
        O = cur * (1 - dd) + dd * col                                              # the pigment part covers
        self.img[sl] = T * (1 - op) + O * op

    # ------------------------------------------------------------ construction grid
    def grid(self, colour=TINT, width=1.5, every=1, extend=0):
        """print the construction grid (every `every` modules) inside the design area through a pale tint screen"""
        M = self.M * every
        x0, y0, x1, y1 = self.x0 - extend, self.y0 - extend, self.x1 + extend, self.y1 + extend
        rx = np.mod(self.XX - self.x0 + M / 2, M) - M / 2
        ry = np.mod(self.YY - self.y0 + M / 2, M) - M / 2
        inside = (np.clip(np.minimum(self.XX - x0, x1 - self.XX) + 1, 0, 1)
                  * np.clip(np.minimum(self.YY - y0, y1 - self.YY) + 1, 0, 1))
        m = np.maximum(np.clip(width / 2 - np.abs(rx) + 0.5, 0, 1), np.clip(width / 2 - np.abs(ry) + 0.5, 0, 1))
        self.pull(m * inside, colour, edge=0.0)

    # ------------------------------------------------------------ pencil, after printing
    def pencil(self, s, x, y, size, colour='#4a4b4f', pressure=0.7, font='hand', anchor='ls', rot=0.0):
        """soft graphite in the margin (the edition number): only the tops of the tooth take it"""
        m = self.text_mask(s, x, y, size, font, anchor, rot=rot)
        rows, cols = np.flatnonzero(m.max(1) > 0), np.flatnonzero(m.max(0) > 0)
        if not len(rows): return
        sl = (slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1))
        catch = smoothstep(0.62 - pressure * 0.25, 0.3 - pressure * 0.25, self.tooth[sl])
        a = np.clip(m[sl] * (0.35 + 0.65 * catch) * pressure, 0, 1)[..., None]
        self.img[sl] *= 1 - a * (1 - _c(colour))

    # ------------------------------------------------------------ output
    def composite(self):
        img = self.img * (self.fibre * self.light)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)                 # 4:4:4 keeps red edges crisp
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
