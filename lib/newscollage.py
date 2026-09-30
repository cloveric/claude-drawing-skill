"""newscollage -- a Dada / magazine cut-and-paste collage on a kraft board (numpy + Pillow only).

Old newspaper torn by hand, halftone "photographs" of objects cut out with scissors, a big disc of red paper,
ransom-note letters snipped one by one out of different magazines, masking tape and rubber stamps.

Model: everything is a piece of paper that was printed first, then torn or cut, then glued down.
  board      kraft paper: warm brown, cloudy (unevenly pulped), full of short dark and pale fibres and a few bark
             flecks, plus a per-pixel tooth field that stamp ink catches on.
  sheet      one piece of paper in its own frame: paper colour, printed ink (multiplied, with a little ink spread
             and uneven density) and an outline. Printing happens before the paper is torn or cut, so the ink runs
             right up to a scissor cut.
  tear       tearing splits the paper in its thickness. The outline wanders (slow bays plus fine jaggies), and along
             some stretches the printed top layer comes away further than the bottom, so a band of pale, unprinted
             paper core shows (the torn rim), with loose fibres sticking out past the edge. Sides that are not torn
             are scissor-cut: straight, with a slight kink wherever the blades were re-opened.
  cutout     scissors follow a silhouette at a small distance: the outline is a chain of short straight cuts
             (Douglas-Peucker on the offset outline) that skips the narrow gaps a blade cannot get into, with an
             occasional overcut nick.
  newsprint  greyish-yellow paper, columns of justified fake text (generated pseudo-words, never real news), a
             folio line, kicker, headline and deck, subheads, column rules, a boxed advertisement, a halftone picture
             with a caption; yellowing toward the edges, foxing, and the reverse page showing through, mirrored.
  photo      an "old photograph" is actually rendered: a studio still life built as a height field with albedo /
             metal / gloss maps (discs, domes, rings, rods, gears, spirals, screws, printed marks), lit by one key
             light (Lambert + Blinn; chrome reflects a bright sky over a dark floor), with cast shadows on itself and
             on the backdrop and ambient occlusion in the crevices. It is then printed as an AM halftone: a 45-degree
             screen of round dots that grow, join into a chequerboard at 50 % and leave only white holes in the
             shadows; ragged dot edges from the paper fibres, dot gain, uneven ink.
  paste      a sheet is rotated into place and glued: a tight contact shadow plus a softer lifted one, the cut edge
             catching the light on the upper-left and going dark on the lower-right; optional glue ripples (a wrinkle
             height field lit by the same light).
  letters    ransom-note lettering: every character cut from a different magazine, with its own typeface, size,
             paper and ink (black on white, knocked out of red or black, black on newsprint with neighbouring text,
             on mustard, on a halftone tint), its own tilt and bounce, and a crooked scissor cut round it.
  tape       masking tape: crepe paper, translucent (what is under it shows through, dimmed), fine crepe ridges
             across its width, serrated torn ends; wherever it bridges a paper edge the edge shows as a lit ridge.
  stamp      a rubber stamp: ink pressed unevenly (a pressure gradient, voids where the rubber did not take), ink
             piling up at the glyph edges, soaked into whatever paper is underneath (multiply).
Order: board -> big sheets (newsprint) -> colour fields (red disc) -> photos -> letters and labels -> tape, stamps.
Rotations are degrees counter-clockwise, like PIL.

    from newscollage import NewsCollage, Photo, RED, INK
    nc = NewsCollage(1920, 1080, seed=1)
    nc.board()
    s = nc.newsprint(600, 900, columns=3); s.tear('rtb'); nc.paste(s, 320, 540, rot=-3)
    nc.disc(1100, 520, 330, RED)
    p = Photo(420, 420, seed=2); p.gear(210, 210, 170, teeth=40, spokes=5)
    s = nc.print_photo(p); s.cutout(14); nc.paste(s, 1100, 520, rot=8)
    nc.ransom('拆开看看', 90, 820, 150)
    nc.tape(400, 120, 180, rot=-8)
    nc.stamp(1700, 950, [('第 42 期', 40), ('No.42', 30)], rot=6)
    nc.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import (blur, fbm1d, spline, noise2d, smoothstep, shift, load_font, height_normals, height_shadow,
                  ambient_occlusion)

INK, BLACK, RED, MUSTARD = '#1f1c1a', '#1b1918', '#c8281d', '#d9a531'
KRAFT, NEWS, PAPER, TAPE = '#b28a5b', '#e6ddc5', '#f1ece0', '#e8d9ae'
NEWS_CORE, PAPER_CORE = '#f5f1e6', '#fbf8f1'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- fonts: newspaper and magazine faces
_FACES = {   # (glob, face index), first hit wins -- macOS, Linux, Windows; anything missing falls back to core fonts
    'news': [('/System/Library/Fonts/Supplemental/Times New Roman.ttf', 0), ('/usr/share/fonts/**/LiberationSerif-Regular.ttf', 0),
             ('/usr/share/fonts/**/DejaVuSerif.ttf', 0), ('C:/Windows/Fonts/times.ttf', 0)],
    'news_bold': [('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf', 0), ('/usr/share/fonts/**/LiberationSerif-Bold.ttf', 0),
                  ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0), ('C:/Windows/Fonts/timesbd.ttf', 0)],
    'news_italic': [('/System/Library/Fonts/Supplemental/Times New Roman Italic.ttf', 0), ('/usr/share/fonts/**/LiberationSerif-Italic.ttf', 0),
                    ('/usr/share/fonts/**/DejaVuSerif-Italic.ttf', 0), ('C:/Windows/Fonts/timesi.ttf', 0)],
    'serif_bold': [('/System/Library/Fonts/Supplemental/Georgia Bold.ttf', 0), ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0),
                   ('C:/Windows/Fonts/georgiab.ttf', 0)],
    'slab': [('/System/Library/Fonts/Supplemental/Rockwell.ttc', 2), ('/System/Library/Fonts/Supplemental/SuperClarendon.ttc', 7),
             ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0), ('C:/Windows/Fonts/ROCKB.TTF', 0)],
    'clarendon': [('/System/Library/Fonts/Supplemental/SuperClarendon.ttc', 7), ('/System/Library/Fonts/Supplemental/Rockwell.ttc', 2),
                  ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0)],
    'didone': [('/System/Library/Fonts/Supplemental/Bodoni 72.ttc', 2), ('/System/Library/Fonts/Supplemental/Didot.ttc', 2),
               ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0), ('C:/Windows/Fonts/BOD_B.TTF', 0)],
    'poster': [('/System/Library/Fonts/Supplemental/Impact.ttf', 0), ('/System/Library/Fonts/HelveticaNeue.ttc', 9),
               ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', 0), ('C:/Windows/Fonts/impact.ttf', 0)],
    'futura': [('/System/Library/Fonts/Supplemental/Futura.ttc', 4), ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', 0),
               ('C:/Windows/Fonts/GOTHICB.TTF', 0)],
    'grotesk': [('/System/Library/Fonts/HelveticaNeue.ttc', 4), ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', 0),
                ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'typewriter': [('/System/Library/Fonts/Supplemental/AmericanTypewriter.ttc', 0), ('/System/Library/Fonts/Supplemental/Courier New.ttf', 0),
                   ('/usr/share/fonts/**/DejaVuSansMono.ttf', 0), ('C:/Windows/Fonts/cour.ttf', 0)],
    'typewriter_bold': [('/System/Library/Fonts/Supplemental/AmericanTypewriter.ttc', 2), ('/System/Library/Fonts/Supplemental/Courier New Bold.ttf', 0),
                        ('/usr/share/fonts/**/DejaVuSansMono-Bold.ttf', 0), ('C:/Windows/Fonts/courbd.ttf', 0)],
    'cjk_song': [('/System/Library/Fonts/Supplemental/Songti.ttc', 0), ('/usr/share/fonts/**/NotoSerifCJK*Black*.tt[cf]', 0),
                 ('/usr/share/fonts/**/NotoSerifCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/simsun.ttc', 0)],
    'cjk_hei': [('/System/Library/Fonts/STHeiti Medium.ttc', 1), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2),
                ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0)],
    'cjk_round': [('/System/Library/Fonts/Hiragino Sans GB.ttc', 2), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
                  ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0)],
}
_GENERIC = {'news': 'serif', 'news_bold': 'serif', 'news_italic': 'serif', 'serif_bold': 'serif', 'slab': 'serif',
            'clarendon': 'serif', 'didone': 'serif', 'poster': 'condensed', 'futura': 'condensed', 'grotesk': 'sans_bold',
            'typewriter_bold': 'typewriter', 'cjk_song': 'cjk', 'cjk_hei': 'cjk_sans', 'cjk_round': 'cjk_sans', 'cjk_kai': 'cjk'}
_FONT_CACHE, _PATH_CACHE = {}, {}


def font(style, size):
    """PIL font for a collage style: news, news_bold, news_italic, serif_bold, slab, clarendon, didone, poster, futura,
    grotesk, typewriter(_bold), cjk_song, cjk_hei, cjk_round, cjk_kai, or any core.load_font style"""
    key = (style, int(size))
    if key in _FONT_CACHE: return _FONT_CACHE[key]
    if style not in _PATH_CACHE:
        _PATH_CACHE[style] = None
        env = os.environ.get('INKPAINT_FONT_' + style.upper())
        if env and os.path.exists(env):
            _PATH_CACHE[style] = (env, 0)
        for pat, idx in _FACES.get(style, []):
            if _PATH_CACHE[style]: break
            for p in glob.glob(pat, recursive=True):
                try:
                    ImageFont.truetype(p, 12, index=idx)
                    _PATH_CACHE[style] = (p, idx); break
                except OSError:
                    pass
    hit = _PATH_CACHE[style]
    f = ImageFont.truetype(hit[0], int(size), index=hit[1]) if hit else load_font(_GENERIC.get(style, style), size)
    _FONT_CACHE[key] = f
    return f


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


_HAS = {}


def _has(style, ch):
    """does the face for `style` really have a glyph for ch (not the .notdef box)?"""
    key = (style, ch)
    if key not in _HAS:
        f = font(style, 40)
        _HAS[key] = ch.isspace() or bytes(f.getmask(ch)) != bytes(f.getmask('\uffff'))
    return _HAS[key]


def _runs(s, style):
    """split text into CJK / Latin runs, each with a face that has its glyphs (arrows etc. fall back to CJK)"""
    cjk = style if style.startswith('cjk') else ('cjk_song' if style in ('news', 'news_bold', 'serif_bold', 'didone', 'slab', 'clarendon') else 'cjk_hei')
    lat = style if not style.startswith('cjk') else {'cjk_song': 'serif_bold', 'cjk_kai': 'serif_bold'}.get(style, 'sans_bold')
    runs = []
    for ch in s:
        k = _is_cjk(ch) or not _has(lat, ch)
        if runs and runs[-1][1] == k: runs[-1][0] += ch
        else: runs.append([ch, k])
    return [(t, cjk if k else lat) for t, k in runs]


def text_width(s, size, style='serif_bold', spacing=0.0):
    w = 0.0
    for t, st in _runs(s, style):
        f = font(st, size)
        w += sum(f.getlength(ch) + spacing for ch in t) if spacing else f.getlength(t)
    return w - (spacing if spacing else 0)


def text_mask(h, w, s, x, y, size, style='serif_bold', anchor='ls', spacing=0.0, rot=0.0, weight=0.0, ss=2):
    """text -> float mask (h, w). Mixed CJK / Latin, letter spacing, faux-bold weight (px), rotation about (x, y).
    anchor: first letter l/m/r, second s (baseline) / m (middle of the capitals) / t (top of the capitals)"""
    runs = _runs(s, style)
    items = []
    for t, st in runs:
        f = font(st, size * ss)
        if spacing:
            for ch in t: items.append((ch, f, f.getlength(ch) + spacing * ss))
        else:
            items.append((t, f, f.getlength(t)))
    total = sum(a for _, _, a in items) - (spacing * ss if spacing else 0)
    f0 = items[0][1]
    ref = '中' if _is_cjk(s.strip()[:1] or 'H') else 'H'
    capH = -f0.getbbox(ref, anchor='ls')[1]
    dyb = {'s': 0, 'm': capH / 2, 't': capH}.get(anchor[1], 0)
    im = Image.new('L', (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    cx = x * ss - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
    by = y * ss + dyb
    sw = int(round(weight * ss))
    for t, f, adv in items:
        d.text((cx, by), t, font=f, fill=255, anchor='ls', stroke_width=sw, stroke_fill=255)
        cx += adv
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, center=(x * ss, y * ss))
    if ss > 1:
        im = im.resize((w, h), Image.BOX)
    return np.asarray(im, np.float32) / 255


def poly_mask(h, w, pts, ss=3):
    im = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in pts], fill=255)
    if ss > 1: im = im.resize((w, h), Image.BOX)
    return np.asarray(im, np.float32) / 255


def lines_mask(h, w, paths, width, ss=3):
    """polylines of a given width (px) -> float mask"""
    im = Image.new('L', (w * ss, h * ss), 0)
    d = ImageDraw.Draw(im)
    for P in paths:
        P = [(float(x) * ss, float(y) * ss) for x, y in P]
        d.line(P, fill=255, width=max(1, int(round(width * ss))), joint='curve')
        r = width * ss / 2
        for q in (P[0], P[-1]):
            d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)
    if ss > 1: im = im.resize((w, h), Image.BOX)
    return np.asarray(im, np.float32) / 255


def _dp(P, tol):
    """Douglas-Peucker simplification of an open polyline"""
    if len(P) < 3: return P
    a, b = P[0], P[-1]
    ab = b - a; L = np.hypot(*ab) + 1e-9
    d = np.abs(ab[0] * (P[:, 1] - a[1]) - ab[1] * (P[:, 0] - a[0])) / L
    i = int(np.argmax(d))
    if d[i] > tol:
        return np.vstack([_dp(P[:i + 1], tol)[:-1], _dp(P[i:], tol)])
    return np.vstack([a, b])


def halftone(tone, cell=6.5, angle=45.0, rough=0.08, seed=0, gain=0.5):
    """AM halftone screen: tone (0 black .. 1 white) -> ink coverage 0..1.
    Round dots on a screen at `angle`, `cell` px apart; they grow with darkness, touch in a chequerboard at 50 %
    and leave white holes in the shadows. rough: ragged dot edges from paper fibres; gain: dot gain (ink spread, px)."""
    h, w = tone.shape
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.deg2rad(angle)
    u = (X * np.cos(a) + Y * np.sin(a)) / cell
    v = (-X * np.sin(a) + Y * np.cos(a)) / cell
    spot = 0.5 - 0.25 * (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v))
    grad = (np.pi / (2 * cell)) * np.sqrt(np.sin(2 * np.pi * u) ** 2 + np.sin(2 * np.pi * v) ** 2) + 0.035
    if rough:
        n = blur(np.random.default_rng(seed).random((h, w)).astype(np.float32), 0.7)
        spot = spot + rough * (n - 0.5) / (n.std() * 3.4 + 1e-6)
    c = np.clip(1 - tone, 0, 1)
    ink = np.clip((c - spot) / grad + 0.5, 0, 1) * smoothstep(0.0, 0.04, c)
    ink = np.maximum(ink, smoothstep(0.93, 1.0, c))
    if gain:
        ink = np.clip(blur(ink, gain) * 1.12, 0, 1)
    return ink


class Frame:
    """a rotated rectangle on the board. pt(lx, ly) maps a point measured from the sheet's top-left corner (in its
    own rotated axes) to canvas coordinates; rot is the rotation to use for anything written on it."""

    def __init__(self, cx, cy, w, h, rot):
        self.cx, self.cy, self.w, self.h, self.rot = cx, cy, w, h, rot

    def pt(self, lx, ly):
        u, v = lx - self.w / 2, ly - self.h / 2
        t = np.deg2rad(self.rot)
        return (self.cx + u * np.cos(t) + v * np.sin(t), self.cy - u * np.sin(t) + v * np.cos(t))


# ================================================================ a piece of paper
class Sheet:
    """one piece of paper in its own frame (w x h px): colour, printed ink, outline, torn rim.
    core: the colour of the paper's inside (shows along torn edges); kind is informational ('news', 'photo', ...)"""

    def __init__(self, w, h, colour=PAPER, seed=0, core=None, kind='paper'):
        self.w, self.h = int(round(w)), int(round(h))
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        col = _c(colour)
        self.colour = col
        self.core = _c(core) if core is not None else np.clip(col + (1 - col) * 0.55, 0, 1)
        self.kind = kind
        g = blur(self.rng.random((self.h, self.w)).astype(np.float32), 0.6)
        mt = noise2d(self.h, self.w, 70, 3, self._seed())
        self.tooth = np.clip(0.5 + (g - g.mean()) / (g.std() * 5 + 1e-6), 0, 1)
        self.rgb = np.ones((self.h, self.w, 3), np.float32) * col * (1 + 0.035 * (mt - 0.5) + 0.02 * (self.tooth - 0.5))[..., None]
        self.mask = np.ones((self.h, self.w), np.float32)
        self.obj = None
        self.centre = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def copy(self):
        s = Sheet.__new__(Sheet)
        s.__dict__.update(self.__dict__)
        s.rgb, s.mask = self.rgb.copy(), self.mask.copy()
        s.rng = np.random.default_rng(self._seed())
        return s

    # ------------------------------------------------------------ printing
    def ink(self, m, colour=INK, alpha=0.94, spread=0.35, mottle=0.14):
        """print ink through mask m (0..1): a little spread, uneven density, multiplied onto the paper"""
        m = np.clip(m, 0, 1)
        if spread: m = np.maximum(m, np.clip(blur(m, spread) * 1.08, 0, 1))
        dens = alpha * (1 - mottle + mottle * self.tooth) * (0.96 + 0.04 * noise2d(self.h, self.w, 40, 2, self._seed()))
        self.rgb *= 1 - (m * dens)[..., None] * (1 - _c(colour))

    def paint(self, m, colour, alpha=1.0):
        """opaque colour (not multiplied): white-out, pasted-in paper colour"""
        a = np.clip(m, 0, 1)[..., None] * alpha
        self.rgb = self.rgb * (1 - a) + _c(colour) * (1 + 0.02 * (self.tooth - 0.5))[..., None] * a

    def rect(self, x0, y0, x1, y1):
        X, Y = self.XX, self.YY
        return np.clip(X - x0 + 0.5, 0, 1) * np.clip(x1 - X + 0.5, 0, 1) * np.clip(Y - y0 + 0.5, 0, 1) * np.clip(y1 - Y + 0.5, 0, 1)

    def text_mask(self, s, x, y, size, font='serif_bold', anchor='ls', spacing=0.0, rot=0.0, weight=0.0):
        return text_mask(self.h, self.w, s, x, y, size, font, anchor, spacing, rot, weight)

    def text(self, s, x, y, size, font='serif_bold', colour=INK, anchor='ls', spacing=0.0, rot=0.0, weight=0.0, alpha=0.95):
        m = self.text_mask(s, x, y, size, font, anchor, spacing, rot, weight)
        self.ink(m, colour, alpha)
        return m

    def block(self, x0, y0, x1, y1, colour=RED, minus=None, alpha=0.96):
        """a solid printed block; `minus` (a mask) is knocked out and stays paper-coloured (reversed type)"""
        m = self.rect(x0, y0, x1, y1)
        if minus is not None: m = m * (1 - np.clip(minus, 0, 1))
        self.ink(m, colour, alpha, spread=0.25, mottle=0.1)

    def rule(self, x0, y0, x1, y1, width=1.2, colour=INK, alpha=0.9):
        self.ink(lines_mask(self.h, self.w, [[(x0, y0), (x1, y1)]], width), colour, alpha, spread=0.2)

    # ------------------------------------------------------------ outline: tear, cut
    def tear(self, sides='rb', depth=9.0, rim=7.0, rough=1.0, fibres=True):
        """tear the listed sides ('t', 'r', 'b', 'l'); the others are scissor-cut. depth: how far the torn line
        wanders in from the edge; rim: max width of the pale torn core that shows where the top layer came away"""
        r = self.rng
        h, w = self.h, self.w
        X, Y = self.XX, self.YY
        paper = np.ones((h, w), np.float32); printed = np.ones((h, w), np.float32)
        fib_paths = []
        for side in 'trbl':
            L = w if side in 'tb' else h
            along = (X if side in 'tb' else Y).astype(np.int32).clip(0, L - 1)
            inward = {'t': Y, 'b': h - 1 - Y, 'l': X, 'r': w - 1 - X}[side]
            if side in sides:
                s0 = self._seed()
                big = fbm1d(L, 70, 4, s0)
                fine = fbm1d(L, 5, 3, s0 + 1)
                off = 1.5 + depth * (0.55 + 0.45 * big) + rough * 1.6 * fine
                bites = np.zeros(L, np.float32)                          # a few deeper bites where the tear turned
                for _ in range(max(1, L // 260)):
                    c0 = r.uniform(0, L); bw = r.uniform(14, 40)
                    bites += r.uniform(0.3, 0.9) * depth * np.exp(-((np.arange(L) - c0) / bw) ** 2)
                off = off + bites
                rw = rim * np.clip(0.35 + 1.1 * fbm1d(L, 45, 3, s0 + 2), 0, 1) + 0.6 * np.abs(fbm1d(L, 3, 2, s0 + 3))
                o, rr = off[along], rw[along]
                paper *= np.clip(inward - o + 0.5, 0, 1)
                printed *= np.clip((inward - o - rr) / 1.3 + 0.5, 0, 1)
                if fibres:
                    for t in r.uniform(0, L, int(L / 9)):
                        ti = int(t); ln = r.uniform(1.5, 6.5); ang = r.uniform(-1.0, 1.0)
                        base = off[min(ti, L - 1)] + 0.8
                        if side == 't': p0 = (t, base); dv = (np.sin(ang), -np.cos(ang))
                        elif side == 'b': p0 = (t, h - 1 - base); dv = (np.sin(ang), np.cos(ang))
                        elif side == 'l': p0 = (base, t); dv = (-np.cos(ang), np.sin(ang))
                        else: p0 = (w - 1 - base, t); dv = (np.cos(ang), np.sin(ang))
                        fib_paths.append([p0, (p0[0] + dv[0] * ln, p0[1] + dv[1] * ln)])
            else:
                nk = int(r.integers(1, 4))
                kx = np.concatenate([[0], np.sort(r.uniform(0.15, 0.85, nk)) * L, [L - 1]])
                ky = r.uniform(0.6, 2.4, len(kx))
                o = np.interp(np.arange(L), kx, ky).astype(np.float32)[along]
                paper *= np.clip(inward - o + 0.5, 0, 1)
                printed *= np.clip(inward - o + 0.5, 0, 1)
        rimA = np.clip(paper - printed, 0, 1)
        corecol = self.core * (0.965 + 0.06 * self.tooth)[..., None]
        self.rgb = self.rgb * (1 - rimA[..., None]) + corecol * rimA[..., None]
        self.mask = self.mask * paper
        if fib_paths:
            fm = lines_mask(h, w, fib_paths, 0.8) * 0.75 * (1 - paper)
            self.rgb = self.rgb * (1 - fm[..., None]) + corecol * fm[..., None]
            self.mask = np.maximum(self.mask, fm)
        return self

    def cut(self, pts, ss=3):
        """scissor-cut the sheet to a polygon (local coordinates)"""
        self.mask = self.mask * poly_mask(self.h, self.w, pts, ss)
        return self

    def cut_rect(self, inset=2.0, jitter=2.5, snip=0.0):
        """scissor-cut a slightly crooked quadrilateral (corners jittered); snip: chance to snip each corner off"""
        r = self.rng
        w, h = self.w, self.h
        cs = [(inset, inset), (w - 1 - inset, inset), (w - 1 - inset, h - 1 - inset), (inset, h - 1 - inset)]
        pts = []
        for i, (x, y) in enumerate(cs):
            jx, jy = r.uniform(0, jitter), r.uniform(0, jitter)
            x = x + (jx if i in (0, 3) else -jx); y = y + (jy if i in (0, 1) else -jy)
            if r.random() < snip:
                k = r.uniform(5, 12)
                dx = k if i in (0, 3) else -k; dy = k * r.uniform(0.6, 1.4) if i in (0, 1) else -k * r.uniform(0.6, 1.4)
                pts += [(x, y + dy), (x + dx, y)] if i in (0, 2) else [(x + dx, y), (x, y + dy)]
            else:
                pts.append((x, y))
        return self.cut(pts)

    def cutout(self, margin=12.0, centre=None, tol=1.6, nicks=2, obj=None, wander=0.45):
        """cut round the object silhouette (self.obj, or `obj`) at `margin` px, the way scissors do: a chain of short
        straight cuts that bridges narrow gaps, the margin wandering wider and tighter (never into the object),
        plus a nick or two where the blade overshot"""
        obj = self.obj if obj is None else obj
        h, w = self.h, self.w
        sig = max(1.0, margin / 2.1)
        dil = blur(obj, sig) > 0.03
        dil = blur(dil.astype(np.float32), 1.0)
        if centre is None:
            ys, xs = np.nonzero(obj > 0.5)
            centre = (xs.mean(), ys.mean())
        cx, cy = centre
        N = 900
        th = np.linspace(0, 2 * np.pi, N, endpoint=False)
        R = np.arange(0, np.hypot(w, h), 1.0)
        px = cx + np.cos(th)[:, None] * R[None, :]; py = cy + np.sin(th)[:, None] * R[None, :]
        ok = (px >= 0) & (py >= 0) & (px < w - 1) & (py < h - 1)
        val = np.zeros(px.shape, np.float32)
        val[ok] = dil[py[ok].astype(int), px[ok].astype(int)]
        inside = val > 0.5
        last = np.where(inside.any(1), R.size - 1 - np.argmax(inside[:, ::-1], 1), 0).astype(np.float32)
        rad = np.maximum.reduce([np.roll(last, k) for k in range(-3, 4)])            # keep thin bits
        rad = np.convolve(np.concatenate([rad[-4:], rad, rad[:4]]), np.ones(9) / 9, 'same')[4:-4]
        if wander:                                                     # the hand drifts closer and further
            ov = np.zeros(px.shape, np.float32)
            ov[ok] = obj[py[ok].astype(int), px[ok].astype(int)]
            oin = ov > 0.3
            orad = np.where(oin.any(1), R.size - 1 - np.argmax(oin[:, ::-1], 1), 0).astype(np.float32)
            orad = np.maximum.reduce([np.roll(orad, k) for k in range(-6, 7)])
            ph = self.rng.uniform(0, 2 * np.pi, 3)
            wob = sum(np.sin(th * f + p) / f ** 0.5 for f, p in zip((2, 3, 5), ph)) / 1.9
            rad = np.maximum(rad + margin * wander * wob, orad + 2.5)
        P = np.stack([cx + np.cos(th) * rad, cy + np.sin(th) * rad], 1)
        k = int(np.argmin(P[:, 1]))
        P = np.vstack([P[k:], P[:k + 1]])
        j = int(np.argmax(np.hypot(P[:, 0] - P[0, 0], P[:, 1] - P[0, 1])))     # closed: simplify two open halves
        Q = np.vstack([_dp(P[:j + 1], tol)[:-1], _dp(P[j:], tol)[:-1]])
        r = self.rng
        Q = Q + r.normal(0, 0.5, Q.shape)
        pts = [tuple(q) for q in Q]
        for _ in range(nicks):
            i = int(r.integers(0, len(pts)))
            a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
            if np.hypot(*(b - a)) < 30: continue
            t = r.uniform(0.3, 0.7); m = a + (b - a) * t
            dvec = (b - a) / np.hypot(*(b - a)); nrm = np.array([dvec[1], -dvec[0]])
            inw = np.array([cx, cy]) - m; nrm = nrm if nrm @ inw > 0 else -nrm
            dep = r.uniform(4, 8)
            pts[i + 1:i + 1] = [tuple(m - dvec * 1.2), tuple(m + nrm * dep), tuple(m + dvec * 0.6)]
        self.mask = self.mask * poly_mask(h, w, pts)
        self.outline = pts
        return self

    def split(self, p0, p1, kinks=3, jag=3.0):
        """cut the sheet in two with scissors along p0 -> p1 (a few short straight cuts); returns (left, right),
        left being the part to the left of the direction of the cut"""
        r = self.rng
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
        d = p1 - p0; L = np.hypot(*d); d /= L; nrm = np.array([d[1], -d[0]])   # nrm points to the left (screen)
        ts = np.concatenate([[0], np.sort(r.uniform(0.1, 0.9, kinks)), [1]])
        pts = [p0 + d * t * L + nrm * (r.uniform(-jag, jag) if 0 < t < 1 else 0) for t in ts]
        far = 4 * (self.w + self.h)
        poly = [pts[0] - d * far] + pts + [pts[-1] + d * far, pts[-1] + d * far + nrm * far, pts[0] - d * far + nrm * far]
        mL = poly_mask(self.h, self.w, poly)
        a, b = self.copy(), self.copy()
        a.mask = self.mask * mL; b.mask = self.mask * (1 - mL)
        return a, b

    # ------------------------------------------------------------ ageing and glue
    def age(self, amount=1.0, foxing=6, yellow='#c9a85a'):
        """yellowing toward the edges, a few foxing spots"""
        X, Y = self.XX, self.YY
        e = np.minimum.reduce([X, Y, self.w - 1 - X, self.h - 1 - Y])
        n = noise2d(self.h, self.w, 90, 3, self._seed())
        yl = amount * (0.16 * np.exp(-e / 45) + 0.06 * n)
        self.rgb *= 1 - yl[..., None] * (1 - _c(yellow))
        r = self.rng
        for _ in range(int(foxing * amount)):
            cx, cy, rr = r.uniform(0, self.w), r.uniform(0, self.h), r.uniform(2, 9)
            d = np.hypot(X - cx, Y - cy)
            if d.min() > rr * 3: continue
            k = np.exp(-(d / rr) ** 2) * r.uniform(0.08, 0.2) * (0.7 + 0.6 * self.tooth)
            self.rgb *= 1 - k[..., None] * (1 - _c('#8b5a2b'))
        return self

    def wrinkle(self, amount=1.0, scale=70, light=(-0.5, -0.7, 0.5)):
        """glue ripples: the wet paste stretched the paper; shade a soft ridged height field with the room light"""
        n1 = noise2d(self.h, self.w, scale, 3, self._seed())
        n2 = noise2d(self.h, self.w, scale * 0.45, 2, self._seed())
        ridge = (1 - np.abs(2 * n1 - 1)) ** 4
        hm = (ridge * 3.0 + n2 * 2.0) * amount
        N = height_normals(blur(hm, 1.5))
        L = np.asarray(light, np.float32); L /= np.linalg.norm(L)
        sh = (N @ L) / L[2]
        self.rgb *= np.clip(1 + 0.5 * (sh - 1), 0.8, 1.15)[..., None]
        return self


# ================================================================ a studio photograph, as a height field
class Photo:
    """a black-and-white studio still life, built as a height field with material maps and lit, before printing.
    Primitives stack front to back in call order; z is the height a part sits at, height its own thickness.
    albedo 0..1 (paint / brass / steel brightness), metal 0..1 (reflects the studio instead of scattering light),
    gloss 0..1 (a varnish highlight on non-metals). Everything drawn becomes part of the object silhouette `obj`."""

    def __init__(self, w, h, seed=0, backdrop=(0.95, 0.8), light=(-0.55, -0.62, 0.56), lift=34):
        self.w, self.h = int(w), int(h)
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.hmap = np.zeros((self.h, self.w), np.float32)
        self.alb = np.zeros((self.h, self.w), np.float32)
        self.metal = np.zeros((self.h, self.w), np.float32)
        self.gloss = np.zeros((self.h, self.w), np.float32)
        self.obj = np.zeros((self.h, self.w), np.float32)
        self.extra = np.zeros((self.h, self.w), np.float32)
        self.L = np.asarray(light, np.float32) / np.linalg.norm(light)
        g = np.clip(self.XX / self.w * 0.4 + self.YY / self.h * 0.6, 0, 1)
        self.backdrop = backdrop[0] + (backdrop[1] - backdrop[0]) * g
        self.lift = lift

    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.w, int(np.ceil(x1)) + 1), min(self.h, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None, None, None
        sl = (slice(y0, y1), slice(x0, x1))
        return sl, self.XX[sl], self.YY[sl]

    def _part(self, sl, m, hgt, albedo, metal, gloss):
        m = np.clip(m, 0, 1)
        self.hmap[sl] = self.hmap[sl] * (1 - m) + hgt * m
        self.alb[sl] = self.alb[sl] * (1 - m) + albedo * m
        self.metal[sl] = self.metal[sl] * (1 - m) + metal * m
        self.gloss[sl] = self.gloss[sl] * (1 - m) + gloss * m
        self.obj[sl] = np.maximum(self.obj[sl], m)

    @staticmethod
    def _bevel(e, bevel):
        t = np.clip(e / max(bevel, 1e-3), 0, 1)
        return np.sqrt(1 - (1 - t) ** 2)

    # ------------------------------------------------------------ primitives
    def disc(self, cx, cy, r, z=0.0, height=8.0, bevel=3.0, albedo=0.8, metal=0.0, gloss=0.3, hole=0.0, turned=0.0):
        """a flat round part with a rounded edge (dial, plate, washer if hole > 0); turned: lathe rings"""
        sl, X, Y = self._box(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        if sl is None: return None
        d = np.hypot(X - cx, Y - cy)
        e = r - d
        if hole: e = np.minimum(e, d - hole)
        m = np.clip(e + 0.5, 0, 1)
        alb = albedo * (1 + turned * 0.08 * np.sin(d * 1.7)) if turned else albedo
        self._part(sl, m, z + height * self._bevel(e, bevel), alb, metal, gloss)
        return sl, m

    def dome(self, cx, cy, rx, ry=None, z=0.0, height=None, rot=0.0, cut=None, albedo=0.8, metal=0.0, gloss=0.3):
        """an elliptical cap (bell, knob, ball); cut keeps only local v < cut * ry (a dome sliced by a chord)"""
        ry = rx if ry is None else ry
        R = max(rx, ry) + 2
        sl, X, Y = self._box(cx - R, cy - R, cx + R, cy + R)
        if sl is None: return None
        t = np.deg2rad(rot); dx, dy = X - cx, Y - cy
        u = dx * np.cos(t) - dy * np.sin(t); v = dx * np.sin(t) + dy * np.cos(t)
        q = (u / rx) ** 2 + (v / ry) ** 2
        m = np.clip((1 - np.sqrt(q)) * min(rx, ry) + 0.5, 0, 1)
        if cut is not None: m = m * np.clip(cut * ry - v + 0.5, 0, 1)
        hh = min(rx, ry) * 0.8 if height is None else height
        self._part(sl, m, z + hh * np.sqrt(np.clip(1 - q, 0, 1)), albedo, metal, gloss)
        return sl, m

    def ring(self, cx, cy, r0, r1, z=0.0, height=None, albedo=0.8, metal=1.0, gloss=0.3):
        """a torus-like ring (bezel, rim)"""
        sl, X, Y = self._box(cx - r1 - 2, cy - r1 - 2, cx + r1 + 2, cy + r1 + 2)
        if sl is None: return None
        d = np.hypot(X - cx, Y - cy)
        rm, hw = (r0 + r1) / 2, (r1 - r0) / 2
        q = (d - rm) / hw
        m = np.clip(hw - np.abs(d - rm) + 0.5, 0, 1)
        self._part(sl, m, z + (hw if height is None else height) * np.sqrt(np.clip(1 - q * q, 0, 1)), albedo, metal, gloss)
        return sl, m

    def rod(self, p0, p1, r, z=0.0, albedo=0.8, metal=1.0, gloss=0.3):
        """a round bar between two points (legs, posts, arbors)"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        sl, X, Y = self._box(min(p0[0], p1[0]) - r - 2, min(p0[1], p1[1]) - r - 2, max(p0[0], p1[0]) + r + 2, max(p0[1], p1[1]) + r + 2)
        if sl is None: return None
        ab = p1 - p0; l2 = float(ab @ ab) + 1e-6
        t = np.clip(((X - p0[0]) * ab[0] + (Y - p0[1]) * ab[1]) / l2, 0, 1)
        d = np.hypot(X - p0[0] - t * ab[0], Y - p0[1] - t * ab[1])
        m = np.clip(r - d + 0.5, 0, 1)
        self._part(sl, m, z + r * np.sqrt(np.clip(1 - (d / r) ** 2, 0, 1)), albedo, metal, gloss)
        return sl, m

    def poly(self, pts, z=0.0, height=5.0, bevel=2.5, albedo=0.15, metal=0.3, gloss=0.4):
        """a flat part cut to a polygon (clock hands, levers, key wings), edges rounded over `bevel` px"""
        P = np.asarray(pts, np.float32)
        pad = bevel * 3 + 3
        sl, X, Y = self._box(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if sl is None: return None
        x0, y0 = sl[1].start, sl[0].start
        m = poly_mask(X.shape[0], X.shape[1], P - [x0, y0])
        prof = np.sqrt(np.clip((blur(m, bevel * 0.7) - 0.5) * 2, 0, 1))
        self._part(sl, m, z + height * prof, albedo, metal, gloss)
        return sl, m

    def gear(self, cx, cy, r, teeth=30, z=0.0, height=9.0, depth=None, spokes=5, hub=None, rim=None, rot=0.0,
             albedo=0.86, metal=0.35, gloss=0.5, pinion=None, bevel=2.5, turned=1.0):
        """a clock wheel: trapezoid teeth, a flat rim, `spokes` crossings with windows between them (the backdrop
        shows through), a raised hub, and optionally a steel pinion (leaves) and arbor in the middle"""
        depth = float(np.clip(r * 0.09, 3.5, 14)) if depth is None else depth
        sl, X, Y = self._box(cx - r - 3, cy - r - 3, cx + r + 3, cy + r + 3)
        if sl is None: return None
        dx, dy = X - cx, Y - cy
        d = np.hypot(dx, dy)
        th = np.arctan2(dy, dx) + np.deg2rad(rot)
        ph = (th * teeth / (2 * np.pi)) % 1.0
        tooth = smoothstep(0.06, 0.2, ph) * (1 - smoothstep(0.46, 0.6, ph))
        Rr = r - depth * (1 - tooth)
        m = np.clip(Rr - d + 0.5, 0, 1)
        hub = r * 0.2 if hub is None else hub
        rim = max(4.0, r * 0.11) if rim is None else rim
        if spokes:
            r_in, r_out = hub + 2, r - depth - rim
            sw = max(2.5, r * 0.055)
            ang = th * spokes / (2 * np.pi)
            dth = (ang - np.round(ang)) * 2 * np.pi / spokes
            perp = np.abs(d * np.sin(dth))
            win = np.clip(d - r_in + 0.5, 0, 1) * np.clip(r_out - d + 0.5, 0, 1) * np.clip(perp - sw + 0.5, 0, 1) * (np.cos(dth) > 0)
            m = m * (1 - win)
        prof = np.sqrt(np.clip((blur(m, bevel * 0.7) - 0.5) * 2, 0, 1))
        # circular graining from the lathe: fine rings, and the bow-tie sheen of turned metal across the light
        az = np.arctan2(-self.L[1], -self.L[0])
        bow = np.cos(2 * (np.arctan2(dy, dx) - az - np.pi / 2))
        alb = albedo * (1 + turned * (0.06 * np.sin(d * 1.3 + 0.8 * np.sin(th * 3)) + 0.28 * bow * smoothstep(hub, hub + 12, d)))
        hb = np.clip(hub - d + 0.5, 0, 1)
        hgt = z + height * prof + hb * height * 0.35
        self._part(sl, m, hgt, alb, metal, gloss)
        if pinion:
            self.gear(cx, cy, pinion, teeth=max(6, int(pinion / 3)), z=z + height, height=height * 1.2, depth=pinion * 0.3,
                      spokes=0, hub=0, rot=rot * 1.7, albedo=albedo * 0.72, metal=0.85, gloss=0.5, turned=0)
            self.disc(cx, cy, pinion * 0.34, z=z + height * 2.2, height=4, bevel=2, albedo=0.42, metal=0.9, gloss=0.5)
        return sl, m

    def spiral(self, cx, cy, r0, r1, turns=6, width=5.0, z=0.0, height=None, rot=0.0, albedo=0.45, metal=0.8, gloss=0.5,
               flare=1.0):
        """a coiled flat spring (mainspring, hairspring): a spiral ribbon from r0 to r1. flare > 1 packs the inner
        coils tight and lets the outer ones open up (a mainspring let down), so it reads as a spiral, not rings"""
        sl, X, Y = self._box(cx - r1 - width, cy - r1 - width, cx + r1 + width, cy + r1 + width)
        if sl is None: return None
        dx, dy = X - cx, Y - cy
        d = np.hypot(dx, dy)
        f = ((np.arctan2(dy, dx) + np.deg2rad(rot)) / (2 * np.pi)) % 1.0
        dd = np.full(d.shape, 1e9, np.float32)
        for k in range(int(np.ceil(turns)) + 1):
            ph = (f + k) / turns
            rs = r0 + (r1 - r0) * np.clip(ph, 0, 1) ** flare
            dd = np.where((ph <= 1) & (np.abs(d - rs) < dd), np.abs(d - rs), dd)
        hw = width / 2
        m = np.clip(hw - dd + 0.5, 0, 1)
        self._part(sl, m, z + (hw if height is None else height) * np.sqrt(np.clip(1 - (dd / hw) ** 2, 0, 1)), albedo, metal, gloss)
        return sl, m

    def screw(self, x, y, length, r, rot=0.0, z=0.0, pitch=None, albedo=0.62, metal=0.85, gloss=0.4):
        """a screw seen from the side, head at (x, y), shank running along rot (degrees, counter-clockwise):
        a cheese head with its slot, slanted threads, a pointed tip"""
        pitch = r * 0.75 if pitch is None else pitch
        t = np.deg2rad(rot)
        R = length + r * 2
        sl, X, Y = self._box(x - R, y - R, x + R, y + R)
        if sl is None: return None
        dx, dy = X - x, Y - y
        u = dx * np.cos(t) - dy * np.sin(t)
        v = dx * np.sin(t) + dy * np.cos(t)
        hl, hr = r * 1.4, r * 1.9
        head = np.clip(u + 0.5, 0, 1) * np.clip(hl - u + 0.5, 0, 1) * np.clip(hr - np.abs(v) + 0.5, 0, 1)
        slot = np.clip(r * 0.6 - u + 0.5, 0, 1) * np.clip(r * 0.28 - np.abs(v) + 0.5, 0, 1)
        head = head * (1 - slot)
        ph = (u + 0.4 * v) / pitch
        thread = 1 - 2 * np.abs(ph - np.floor(ph) - 0.5)
        tip = np.clip((length - u) / (r * 1.6), 0, 1)
        re = r * (0.8 + 0.2 * thread) * tip
        shank = np.clip(u - hl + 0.5, 0, 1) * np.clip(length - u + 0.5, 0, 1) * np.clip(re - np.abs(v) + 0.5, 0, 1)
        hh = np.where(head > 0, hr * 0.55 * np.sqrt(np.clip(1 - (v / hr) ** 2, 0, 1)) + 2, re * np.sqrt(np.clip(1 - (v / np.maximum(re, 1e-3)) ** 2, 0, 1)))
        m = np.maximum(head, shank)
        self._part(sl, m, z + hh, albedo, metal, gloss)
        return sl, m

    # ------------------------------------------------------------ printed marks, reflections
    def mark(self, m, tone=0.08, sl=None):
        """paint / print on a surface (dial numerals, ticks): changes albedo only"""
        sl = sl or (slice(0, self.h), slice(0, self.w))
        m = np.clip(m, 0, 1)
        self.alb[sl] = self.alb[sl] * (1 - m) + tone * m
        self.gloss[sl] = self.gloss[sl] * (1 - m * 0.5)

    def text(self, s, x, y, size, font='didone', tone=0.08, anchor='mm', rot=0.0, spacing=0.0):
        self.mark(text_mask(self.h, self.w, s, x, y, size, font, anchor, spacing, rot), tone)

    def lines(self, paths, width, tone=0.08):
        self.mark(lines_mask(self.h, self.w, paths, width), tone)

    def glare(self, cx, cy, r0, r1, a0, a1, strength=0.35, soft=6.0):
        """a reflection on glass: a soft crescent between radii r0..r1 and angles a0..a1 (degrees, screen)"""
        d = np.hypot(self.XX - cx, self.YY - cy)
        a = (np.rad2deg(np.arctan2(self.YY - cy, self.XX - cx)) - a0) % 360
        span = (a1 - a0) % 360
        ang = smoothstep(0, span * 0.3, a) * smoothstep(0, span * 0.3, span - a) * (a <= span)
        rad = smoothstep(r0 - soft, r0 + soft, d) * (1 - smoothstep(r1 - soft, r1 + soft, d))
        self.extra += ang * rad * strength

    # ------------------------------------------------------------ light it
    def develop(self, contrast=1.15, brightness=0.0, grain=0.03, soft=0.7, shadow=0.55, reach=170):
        """render the tone image (0 black .. 1 white): key light, chrome environment, cast shadows, occlusion"""
        H = self.hmap
        N = height_normals(H)
        nx, ny, nz = N[..., 0], N[..., 1], N[..., 2]
        L = self.L
        dif = np.clip(N @ L, 0, 1) / L[2]
        Hv = L + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        spec = np.clip(N @ Hv, 0, 1)
        rx, ry, rz = 2 * nz * nx, 2 * nz * ny, 2 * nz * nz - 1
        Ls = np.array([-0.62, -0.72, 0.32], np.float32); Ls /= np.linalg.norm(Ls)
        box = smoothstep(0.62, 0.9, rx * Ls[0] + ry * Ls[1] + rz * Ls[2])
        sky = smoothstep(0.35, -0.55, ry)
        env = 0.08 + 0.42 * sky + 0.75 * box - 0.05 * smoothstep(-0.2, 0.6, ry)
        zmap = H + self.obj * self.lift
        sh = height_shadow(zmap, tuple(L), reach, 1.5, 2.0)
        ao = ambient_occlusion(H, (3, 9, 22), (3.0, 8.0, 18.0))
        a, mt, gl = self.alb, self.metal, self.gloss
        diff = a * (0.2 + 0.8 * dif * (1 - 0.75 * sh))
        met = a * (env * (1 - 0.5 * sh) + 0.15 * dif) + 0.95 * spec ** 80 * (1 - sh)
        tone_o = diff * (1 - mt) + met * mt + gl * 0.45 * spec ** 30 * (1 - sh)
        tone_o *= 1 - 0.55 * ao
        shb = blur(sh, 5)
        bd = self.backdrop * (1 - shadow * shb)
        t = bd * (1 - self.obj) + tone_o * self.obj + self.extra
        t = np.clip((t - 0.5) * contrast + 0.5 + brightness, 0, 1)
        if soft: t = blur(t, soft)
        if grain: t = t + grain * (noise2d(self.h, self.w, 1.5, 2, int(self.rng.integers(1 << 30))) - 0.5)
        return np.clip(t, 0, 1)


# ================================================================ pseudo-text for newsprint
_ON = ['b', 'c', 'd', 'f', 'g', 'h', 'l', 'm', 'n', 'p', 'r', 's', 't', 'v', 'w', 'br', 'cl', 'dr', 'fr', 'gr', 'pl',
       'pr', 'st', 'tr', 'th', 'sh', 'ch', 'qu', '', '']
_NU = ['a', 'e', 'i', 'o', 'u', 'a', 'e', 'o', 'ea', 'ou', 'ai', 'ie', 'y']
_CO = ['', '', '', 'n', 'r', 's', 't', 'l', 'm', 'nd', 'rt', 'st', 'ck', 'ng', 'x']


class _Gib:
    """meaningless but word-shaped text (syllable soup) -- looks like a newspaper column, says nothing"""

    def __init__(self, rng):
        self.r = rng
        self.cap = True

    def word(self, syl=None):
        r = self.r
        n = syl or int(r.choice([1, 1, 1, 1, 1, 2, 2, 2, 3]))
        w = ''.join(str(r.choice(_ON)) + str(r.choice(_NU)) + str(r.choice(_CO)) for _ in range(n))
        return w or 'a'

    def next(self):
        r = self.r
        if r.random() < 0.035:
            w = str(int(r.integers(2, 1990)))
        else:
            w = self.word()
        if self.cap: w = w[0].upper() + w[1:]
        self.cap = False
        p = r.random()
        if p < 0.075: w += '.'; self.cap = True
        elif p < 0.14: w += ','
        return w

    def title(self, n):
        return ' '.join(self.word(int(self.r.integers(1, 4))).capitalize() for _ in range(n))


# ================================================================ the collage
class NewsCollage:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.5, -0.7, 0.5)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.L = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.img = np.ones((H, W, 3), np.float32) * _c(KRAFT)
        self.hmap = np.zeros((H, W), np.float32)
        self.tooth = np.full((H, W), 0.5, np.float32)
        self._grain = (noise2d(H, W, 1.2, 2, self._seed()) - 0.5).astype(np.float32)
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    # ------------------------------------------------------------ board
    def board(self, colour=KRAFT, fibres=1.0):
        """kraft paper: cloudy pulp, short dark and pale fibres, bark flecks, fine grain"""
        H, W = self.H, self.W
        r = self.rng
        mott = noise2d(H, W, 320, 3, self._seed()); cl = noise2d(H, W, 45, 3, self._seed())
        g = blur(r.random((H, W)).astype(np.float32), 0.7)
        g = (g - g.mean()) / (g.std() + 1e-6)
        self.tooth = np.clip(0.5 + g / 5, 0, 1).astype(np.float32)
        base = _c(colour)[None, None, :] * (1 + 0.07 * (mott - 0.5) + 0.05 * (cl - 0.5) + 0.018 * g)[..., None]
        ss = 2
        layers = []
        for n, lo, hi, wd in [(int(11000 * fibres), 4, 20, 1), (int(6000 * fibres), 4, 16, 1)]:
            im = Image.new('L', (W * ss, H * ss), 0); d = ImageDraw.Draw(im)
            for _ in range(n):
                x, y = r.uniform(0, W * ss), r.uniform(0, H * ss)
                ln = r.uniform(lo, hi) * ss; a = r.uniform(0, np.pi); bend = r.uniform(-0.25, 0.25)
                pts = [(x + np.cos(a + bend * k) * ln * k / 3, y + np.sin(a + bend * k) * ln * k / 3) for k in range(4)]
                d.line(pts, fill=int(r.uniform(90, 255)), width=wd)
            layers.append(np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255)
        dark, light = layers
        img = base * (1 - (dark * 0.2)[..., None] * (1 - _c('#5a3d1e')))
        img = img * (1 - (light * 0.22)[..., None]) + (light * 0.22)[..., None] * _c('#dcc29a')
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        for _ in range(int(700 * fibres)):
            x, y = r.uniform(0, W), r.uniform(0, H); s = r.uniform(0.5, 1.8)
            d.ellipse([x - s, y - s * r.uniform(0.5, 1), x + s, y + s * r.uniform(0.5, 1)], fill=int(r.uniform(80, 230)))
        fl = blur(np.asarray(im, np.float32) / 255, 0.5)
        img = img * (1 - (fl * 0.55)[..., None] * (1 - _c('#3b2612')))
        self.img = img.astype(np.float32)
        self.hmap[:] = 0

    # ------------------------------------------------------------ sheets
    def sheet(self, w, h, colour=PAPER, core=None, kind='paper'):
        return Sheet(w, h, colour, self._seed(), core, kind)

    def newsprint(self, w, h, columns=3, size=11, headline=2, head_font='news_bold', picture=True, ad=True,
                  colour=NEWS, ink=INK, margin=16, gutter=12, lead=1.24, folio=True, showthrough=0.045, age=1.0):
        """an old newspaper page (w x h px) full of generated pseudo-text: folio, kicker, headline, deck, justified
        columns with rules, subheads, a boxed ad, a halftone picture with caption. Returns a Sheet (tear it next)."""
        r = np.random.default_rng(self._seed())
        gib = _Gib(r)
        s = Sheet(w, h, colour, self._seed(), NEWS_CORE, 'news')
        im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
        fb, fbo, fi = font('news', size), font('news_bold', size), font('news_italic', size)
        extra = np.zeros((h, w), np.float32)
        y = margin
        W0 = w - 2 * margin
        if folio:
            fs = font('news_bold', size * 0.85)
            y += size
            left = f'No. {int(r.integers(100, 999))}   ·   {gib.title(2).upper()}'
            d.text((margin, y), left, font=fs, fill=255, anchor='ls')
            d.text((w - margin, y), f'{gib.title(1).upper()} {int(r.integers(1, 28))}', font=fs, fill=255, anchor='rs')
            y += size * 0.55
            d.line([(margin, y), (w - margin, y)], fill=255, width=1)
            y += size * 0.9
        if headline:
            ks = font('news_bold', size * 0.95)
            y += size
            d.text((margin, y), '  '.join(gib.word(2).upper() for _ in range(2)), font=ks, fill=255, anchor='ls')
            y += size * 0.5
            hs = size * r.uniform(2.7, 3.3)
            fh = font(head_font, hs)
            for _ in range(int(headline)):
                y += hs * 0.98
                words, tot = [], 0.0
                while True:
                    wd = gib.word(int(r.integers(1, 4))).capitalize()
                    wl = fh.getlength(wd + ' ')
                    if tot + wl > W0 * r.uniform(0.86, 1.0) and words: break
                    words.append(wd); tot += wl
                d.text((margin, y), ' '.join(words), font=fh, fill=255, anchor='ls')
            y += size * 1.6
            fdk = font('news_italic', size * 1.3)
            deck = ' '.join(gib.word() for _ in range(40))
            while fdk.getlength(deck) > W0 * 0.95: deck = deck.rsplit(' ', 1)[0]
            d.text((margin, y), deck.capitalize(), font=fdk, fill=255, anchor='ls')
            y += size * 0.8
            d.line([(margin, y), (w - margin, y)], fill=255, width=2)
            d.line([(margin, y + 3), (w - margin, y + 3)], fill=255, width=1)
            y += size * 0.9
        colw = (W0 - (columns - 1) * gutter) / columns
        lh = size * lead
        sp = fb.getlength(' ')
        pic_col = int(r.integers(columns)) if picture else -1
        ad_col = int((pic_col + 1 + r.integers(max(1, columns - 1))) % columns) if ad else -1
        for c in range(columns):
            x0 = margin + c * (colw + gutter)
            yy = y + size
            if c == pic_col:
                ph = colw * r.uniform(0.62, 0.8)
                if yy + ph < h - margin - lh * 3:
                    self._news_picture(extra, int(x0), int(yy - size * 0.8), int(colw), int(ph), r)
                    yy += ph + size * 0.6
                    cap = ' '.join(gib.word() for _ in range(12))
                    while fi.getlength(cap) > colw: cap = cap.rsplit(' ', 1)[0]
                    d.text((x0, yy), cap.capitalize(), font=fi, fill=255, anchor='ls')
                    yy += lh * 1.5
            ad_at = r.uniform(0.3, 0.6) * h if c == ad_col else 1e9
            first = True
            while yy + lh * 0.3 <= h - margin:
                if yy > ad_at and yy + lh * 9 < h - margin:
                    ad_at = 1e9
                    bh = lh * r.integers(6, 9)
                    top = yy - size
                    d.rectangle([x0, top, x0 + colw, top + bh], outline=255, width=2)
                    d.rectangle([x0 + 4, top + 4, x0 + colw - 4, top + bh - 4], outline=255, width=1)
                    fa = font('news_bold', size * 2.1)
                    word = gib.word(2).upper()
                    while fa.getlength(word) > colw - 20 and len(word) > 3: word = word[:-1]
                    d.text((x0 + colw / 2, top + bh * 0.45), word, font=fa, fill=255, anchor='ms')
                    for k in range(2):
                        ln = ' '.join(gib.word() for _ in range(8))
                        while fb.getlength(ln) > colw - 24: ln = ln.rsplit(' ', 1)[0]
                        d.text((x0 + colw / 2, top + bh * 0.45 + lh * (1.3 + k)), ln, font=fb, fill=255, anchor='ms')
                    yy += bh + lh * 0.4
                    continue
                if not first and r.random() < 0.09:
                    sub = gib.title(int(r.integers(2, 4))).upper()
                    while fbo.getlength(sub) > colw: sub = sub.rsplit(' ', 1)[0]
                    yy += lh * 0.35
                    d.text((x0 + colw / 2, yy), sub, font=fbo, fill=255, anchor='ms')
                    yy += lh * 1.15
                    continue
                first = False
                n = int(r.integers(3, 13))
                for i in range(n):
                    if yy > h - margin: break
                    last = i == n - 1
                    ind = size * 1.3 if i == 0 else 0
                    avail = colw - ind
                    if last: avail *= r.uniform(0.25, 0.85)
                    words, tot = [], 0.0
                    while True:
                        wd = gib.next(); wl = fb.getlength(wd)
                        if tot + wl + len(words) * sp > avail and words: break
                        words.append((wd, wl)); tot += wl
                    gap = sp if (last or len(words) < 2) else (colw - ind - tot) / (len(words) - 1)
                    xx = x0 + ind
                    for wd, wl in words:
                        d.text((xx, yy), wd, font=fb, fill=255, anchor='ls'); xx += wl + gap
                    yy += lh
                yy += lh * 0.15
            if c < columns - 1:
                xr = x0 + colw + gutter / 2
                d.line([(xr, y), (xr, h - margin)], fill=200, width=1)
        m = np.maximum(np.asarray(im, np.float32) / 255, extra)
        if showthrough:
            back = shift(blur(m[:, ::-1].copy(), 1.4), 3, 5)
            s.ink(back, '#6d6454', showthrough, spread=0, mottle=0.3)
        s.ink(m, ink, 0.9, spread=0.3, mottle=0.22)
        if age: s.age(age)
        return s

    def _news_picture(self, extra, x0, y0, pw, ph, r):
        """a small halftone news photograph: an abstract street or landscape, screened coarse"""
        Y, X = np.mgrid[0:ph, 0:pw].astype(np.float32)
        hz = ph * r.uniform(0.45, 0.65)
        t = 0.82 - 0.2 * Y / ph
        t = np.where(Y > hz, 0.5 - 0.15 * (Y - hz) / ph, t)
        for _ in range(int(r.integers(3, 7))):
            bx, bw = r.uniform(0, pw), r.uniform(pw * 0.08, pw * 0.25)
            bh = r.uniform(ph * 0.15, ph * 0.5)
            m = np.clip(bw / 2 - np.abs(X - bx) + 0.5, 0, 1) * np.clip(Y - (hz - bh) + 0.5, 0, 1) * (Y < hz + 4)
            t = t * (1 - m) + r.uniform(0.18, 0.4) * m
        for _ in range(int(r.integers(2, 5))):
            bx, by, rr = r.uniform(0, pw), hz + r.uniform(-5, 10), r.uniform(pw * 0.05, pw * 0.14)
            m = np.clip(rr - np.hypot(X - bx, (Y - by) * 1.3) + 0.5, 0, 1)
            t = t * (1 - m) + 0.15 * m
        t = np.clip(blur(t, 1.4) + 0.08 * (noise2d(ph, pw, 6, 2, int(r.integers(1 << 30))) - 0.5), 0, 1)
        ink = halftone(t, 3.4, 45, 0.1, int(r.integers(1 << 30)), 0.35)
        ink[:1, :] = 1; ink[-1:, :] = 1; ink[:, :1] = 1; ink[:, -1:] = 1
        H, W = extra.shape
        ys, xs = slice(max(0, y0), min(H, y0 + ph)), slice(max(0, x0), min(W, x0 + pw))
        extra[ys, xs] = np.maximum(extra[ys, xs], ink[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0])

    def print_photo(self, photo, cell=6.5, angle=45.0, ink=INK, paper=PAPER, rough=0.08, gain=0.5, alpha=0.93, **develop):
        """develop a Photo and print it as a halftone on magazine paper; the Sheet remembers the object silhouette
        (so .cutout() can follow it)"""
        tone = photo.develop(**develop)
        s = Sheet(photo.w, photo.h, paper, self._seed(), PAPER_CORE, 'photo')
        s.ink(halftone(tone, cell, angle, rough, self._seed(), gain), ink, alpha, spread=0, mottle=0.12)
        s.obj = photo.obj.copy()
        return s

    # ------------------------------------------------------------ gluing things down
    def _composite(self, rgbp, a, ox, oy, lift=1.0, shadow=0.34, thickness=1.0, edge=True, tint='#2b1a0b'):
        """rgbp: premultiplied colour, a: coverage (both already rotated); top-left at canvas (ox, oy)"""
        h, w = a.shape
        L2 = -self.L[:2] / (np.linalg.norm(self.L[:2]) + 1e-6)
        dist, soft = 1.5 + 6.5 * lift, 1.0 + 6.0 * lift
        pad = int(dist + 3 * soft + 4)
        sl = self._box(ox - pad, oy - pad, ox + w + pad, oy + h + pad)
        if sl is None: return
        rh, rw = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        ax, ay = ox - sl[1].start, oy - sl[0].start
        A = np.zeros((rh, rw), np.float32); C = np.zeros((rh, rw, 3), np.float32)
        ys0, xs0 = max(0, -ay), max(0, -ax)
        ys1, xs1 = min(h, rh - ay), min(w, rw - ax)
        if ys1 <= ys0 or xs1 <= xs0: return
        A[ay + ys0:ay + ys1, ax + xs0:ax + xs1] = a[ys0:ys1, xs0:xs1]
        C[ay + ys0:ay + ys1, ax + xs0:ax + xs1] = rgbp[ys0:ys1, xs0:xs1]
        if shadow:
            con = blur(shift(A, L2[0] * 1.3, L2[1] * 1.3), 1.1)
            drop = blur(shift(A, L2[0] * dist, L2[1] * dist), soft)
            sh = np.clip(con * 0.3 + drop * shadow, 0, 0.9)
            self.img[sl] *= 1 - sh[..., None] * (1 - _c(tint))
        if edge:
            tl = np.clip(A - shift(A, 1, 1), 0, 1)
            br = np.clip(A - shift(A, -1, -1), 0, 1)
            C = C * (1 - 0.14 * br)[..., None] + (tl * 0.07)[..., None] * A[..., None]
        self.img[sl] = self.img[sl] * (1 - A[..., None]) + C
        self.hmap[sl] += A * thickness

    @staticmethod
    def _rotate(arrs, rot, pad=4):
        out = []
        for arr in arrs:
            arr = np.pad(arr, pad)
            if rot:
                arr = np.asarray(Image.fromarray(arr.astype(np.float32), 'F').rotate(rot, resample=Image.BICUBIC, expand=True), np.float32)
            out.append(arr)
        return out

    def paste(self, sheet, cx, cy, rot=0.0, lift=1.0, shadow=0.34, edge=True):
        """glue a Sheet with its centre at (cx, cy), rotated `rot` degrees; returns a Frame for writing on it"""
        m = np.clip(sheet.mask, 0, 1)
        chans = self._rotate([m] + [sheet.rgb[..., k] * m for k in range(3)], rot)
        a = np.clip(chans[0], 0, 1)
        rgbp = np.clip(np.stack(chans[1:], -1), 0, 1) * (a > 0)[..., None]
        rgbp = np.minimum(rgbp, a[..., None])
        h, w = a.shape
        self._composite(rgbp, a, int(round(cx - w / 2)), int(round(cy - h / 2)), lift, shadow, edge=edge)
        return Frame(cx, cy, sheet.w, sheet.h, rot)

    def disc(self, cx, cy, r, colour=RED, lift=0.9, shadow=0.34, facets=None):
        """a disc cut from dyed paper with scissors: many short straight cuts, never a perfect circle"""
        rr = self.rng
        s = Sheet(2 * r + 14, 2 * r + 14, colour, self._seed(), None, 'colour')
        n = facets or max(16, int(2 * np.pi * r / 30))
        th = np.sort((np.arange(n) + rr.uniform(-0.3, 0.3, n)) / n * 2 * np.pi)
        wob = fbm1d(n + 1, 8, 2, self._seed())[:n]
        rad = r * (1 + 0.006 * wob) + rr.normal(0, 0.9, n)
        c0 = r + 7
        s.cut(list(zip(c0 + np.cos(th) * rad, c0 + np.sin(th) * rad)))
        n1 = noise2d(s.h, s.w, 25, 3, self._seed())
        s.rgb *= (1 + 0.05 * (n1 - 0.5))[..., None]
        return self.paste(s, cx, cy, 0.0, lift, shadow)

    # ------------------------------------------------------------ letters and labels
    CLIPPINGS = [   # (paper, printed block colour or None, glyph colour or 'knock' for reversed type, extra)
        (PAPER, None, INK, ''), (PAPER, RED, 'knock', ''), (PAPER, BLACK, 'knock', ''), (NEWS, None, INK, 'text'),
        (PAPER, None, RED, ''), ('#e9c46a', None, INK, ''), (NEWS, None, INK, 'tint'), ('#ece3cf', None, RED, 'text'),
    ]
    CJK_FACES = ['cjk_song', 'cjk_hei', 'cjk_kai', 'cjk_round']
    LATIN_FACES = ['didone', 'slab', 'poster', 'serif_bold', 'futura', 'typewriter_bold', 'clarendon', 'grotesk']

    def clipping(self, ch, size, face, paper=PAPER, block=None, fg=INK, extra='', pad=None):
        """one ransom-note letter: a character cut out of a magazine page (returns a Sheet, not yet pasted)"""
        r = self.rng
        f = font(face, size)
        x0, y0, x1, y1 = f.getbbox(ch, anchor='ls')
        gw, gh = x1 - x0, y1 - y0
        px = size * (r.uniform(0.08, 0.2) if pad is None else pad)
        py = size * (r.uniform(0.07, 0.16) if pad is None else pad * 0.8)
        w, h = int(gw + 2 * px + 6), int(gh + 2 * py + 6)
        s = Sheet(w, h, paper, self._seed(), PAPER_CORE, 'clipping')
        bx, by = (w - gw) / 2 - x0, (h - gh) / 2 - y0
        m = text_mask(h, w, ch, bx, by, size, face, 'ls')
        if extra == 'text':                                             # neighbouring text on the page
            gib = _Gib(r); fs = font('news', max(7, size * 0.075)); im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
            for yy in np.arange(size * 0.08, h + 4, max(8.5, size * 0.095)):
                d.text((2 - r.uniform(0, 20), yy), ' '.join(gib.next() for _ in range(12)), font=fs, fill=255, anchor='ls')
            bg = np.asarray(im, np.float32) / 255 * (1 - np.clip(blur(m, size * 0.06) * 4, 0, 1))
            s.ink(bg, INK, 0.62)
        if extra == 'tint':                                             # a grey halftone tint behind the letter
            s.ink(halftone(np.full((h, w), 0.72, np.float32), 4.5, 45, 0.06, self._seed(), 0.3) * (1 - np.clip(blur(m, 1.5) * 2, 0, 1)), INK, 0.85)
        if block is not None:
            s.block(0, 0, w, h, block, minus=m if fg == 'knock' else None)
        if fg != 'knock':
            s.ink(m, fg, 0.96, spread=0.3)
        s.cut_rect(1.5, max(2.0, size * 0.035), snip=0.25)
        return s

    def ransom(self, text, x, y, size, rot=0.0, gap=0.05, bounce=0.07, tilt=7.0, scale=(0.86, 1.14), styles=None,
               faces=None, lift=0.7, seed=None):
        """ransom-note lettering: each character its own clipping (face, paper, ink), pasted along a baseline from
        (x, y) at angle rot. styles: list of CLIPPINGS tuples to cycle through; faces: list of font styles.
        Returns [(Frame, char)] so later tape or stamps can find the letters."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        t = np.deg2rad(rot)
        ux, uy = np.cos(t), -np.sin(t)
        nx, ny = np.sin(t), np.cos(t)
        pos = 0.0
        out, last_style = [], None
        pool = list(styles or self.CLIPPINGS)
        for i, ch in enumerate(text):
            if ch == ' ':
                pos += size * 0.38; continue
            cjk = _is_cjk(ch)
            fl = faces[i % len(faces)] if faces else str(r.choice(self.CJK_FACES if cjk else self.LATIN_FACES))
            if styles:
                st = pool[i % len(pool)]
            else:
                st = pool[int(r.integers(len(pool)))]
                while st is last_style: st = pool[int(r.integers(len(pool)))]
            last_style = st
            sz = size * r.uniform(*scale) * (1.0 if cjk else 1.0)
            s = self.clipping(ch, sz, fl, *st)
            b = r.uniform(-bounce, bounce) * size
            cxl = pos + s.w / 2
            cx, cy = x + ux * cxl + nx * b, y + uy * cxl + ny * b - size * 0.35 * ny
            fr = self.paste(s, cx, cy, rot + r.uniform(-tilt, tilt), lift)
            out.append((fr, ch))
            pos += s.w * (1 + r.uniform(-0.04, 0.02)) + gap * size
        return out

    def label(self, text, x, y, size, face='typewriter', fg=INK, bg=PAPER, rot=0.0, pad=(0.55, 0.38), anchor='l',
              block=None, tear='', lift=0.6, spacing=0.0, weight=0.0):
        """a word or line of print on a scissor-cut strip (block: a printed colour field behind; fg 'knock' reverses
        the type out of the block); tear: sides to tear instead of cut. (x, y) is the strip's left end or centre."""
        tw = text_width(text, size, face, spacing)
        f = font(_runs(text, face)[0][1], size)
        ref = '中' if _is_cjk(text.strip()[0]) else 'H'
        capH = -f.getbbox(ref, anchor='ls')[1]
        w, h = tw + 2 * size * pad[0], capH + 2 * size * pad[1] + size * 0.15
        s = Sheet(w, h, bg, self._seed(), PAPER_CORE, 'label')
        m = s.text_mask(text, s.w / 2, s.h / 2 + capH / 2 - size * 0.02, size, face, 'ms', spacing, 0, weight)
        if block is not None:
            s.block(0, 0, s.w, s.h, block, minus=m if fg == 'knock' else None)
        if fg != 'knock':
            s.ink(m, fg, 0.95)
        if tear: s.tear(tear, depth=size * 0.12, rim=size * 0.1)
        if tear != 'tblr': s.cut_rect(1.0, 1.8)
        t = np.deg2rad(rot)
        cx = x + (s.w / 2 * np.cos(t) if anchor == 'l' else 0)
        cy = y - (s.w / 2 * np.sin(t) if anchor == 'l' else 0)
        return self.paste(s, cx, cy, rot, lift)

    # ------------------------------------------------------------ tape, stamps, pen
    def tape(self, cx, cy, length, rot=0.0, width=46, colour=TAPE, alpha=0.62):
        """masking tape: translucent crepe paper, fine crepe ridges across it, serrated torn ends; paper edges
        underneath show through as lit ridges"""
        r = self.rng
        w, h = int(length + 24), int(width + 12)
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
        u, v = X - w / 2, Y - h / 2
        rows = np.arange(h)
        def end(sgn):
            zig = np.abs(((rows / r.uniform(3.2, 4.6)) % 2) - 1) * 2.2 + fbm1d(h, 4, 2, self._seed()) * 1.6
            return sgn * length / 2 + r.uniform(-0.2, 0.2) * (rows - h / 2) + zig * (-sgn)
        eL, eR = end(-1)[:, None], end(1)[:, None]
        m = np.clip(u - eL + 0.5, 0, 1) * np.clip(eR - u + 0.5, 0, 1) * np.clip(width / 2 - np.abs(v) + 0.5, 0, 1)
        crepe = fbm1d(w, 1.8, 2, self._seed())[None, :] + 0.5 * fbm1d(w, 9, 2, self._seed())[None, :]
        wr = noise2d(h, w, 40, 2, self._seed())
        edge = np.exp(-(width / 2 - np.abs(v)) / 1.6)
        shade = (1 + 0.04 * crepe + 0.04 * (wr - 0.5) - 0.07 * edge)
        a = m * alpha * (1 + 0.06 * crepe)
        chans = self._rotate([a] + [_c(colour)[k] * shade * a for k in range(3)], rot)
        A = np.clip(chans[0], 0, 1)
        C = np.clip(np.stack(chans[1:], -1), 0, 1)
        hh, ww = A.shape
        ox, oy = int(round(cx - ww / 2)), int(round(cy - hh / 2))
        sl = self._box(ox, oy, ox + ww, oy + hh)
        if sl is None: return
        ys, xs = slice(sl[0].start - oy, sl[0].stop - oy), slice(sl[1].start - ox, sl[1].stop - ox)
        A, C = A[ys, xs], C[ys, xs]
        hb = blur(self.hmap[sl], 1.3)
        gy, gx = np.gradient(hb)
        ridge = np.clip(-(gx * self.L[0] + gy * self.L[1]) * 1.6, -0.35, 0.35)
        L2 = -self.L[:2] / np.linalg.norm(self.L[:2])
        sh = blur(shift(A, L2[0] * 1.5, L2[1] * 1.5), 1.2) * 0.22
        self.img[sl] *= 1 - sh[..., None] * (1 - _c('#2b1a0b'))
        base = self.img[sl] * (1 - A[..., None] * 0.1)
        self.img[sl] = base * (1 - A[..., None]) + C + (A * ridge * 0.9)[..., None] * np.where(ridge[..., None] > 0, 1.0, 0.8)
        self.hmap[sl] += (A > 0.2) * 0.3

    def stamp(self, cx, cy, lines, rot=0.0, colour=RED, shape='box', face='slab', w=None, h=None, r=None, ring=None,
              ring_face='grotesk', ring_size=None, alpha=0.86, pressure=None):
        """a rubber stamp. lines: [(text, size), ...] stacked in the middle. shape 'box' (double border, w x h) or
        'round' (radius r, `ring` text running round the rim). Ink is pressed unevenly and soaks into the paper."""
        rng = self.rng
        lines = [(t, 36) if isinstance(t, str) else t for t in lines]
        widths = [text_width(t, sz, face) for t, sz in lines]
        tot_h = sum(sz * 1.08 for _, sz in lines)
        if shape == 'box':
            w = w or max(widths) + 70
            h = h or tot_h + 50
            R = int(np.hypot(w, h) / 2 + 14)
        else:
            r = r or max(max(widths) / 2 + 44, 80)
            R = int(r + 14)
        S = 2 * R
        m = np.zeros((S, S), np.float32)
        im = Image.new('L', (S * 2, S * 2), 0); d = ImageDraw.Draw(im)
        c = R * 2
        if shape == 'box':
            d.rounded_rectangle([c - w, c - h, c + w, c + h], radius=10, outline=255, width=11)
            d.rounded_rectangle([c - w + 18, c - h + 18, c + w - 18, c + h - 18], radius=6, outline=255, width=4)
        else:
            d.ellipse([c - 2 * r, c - 2 * r, c + 2 * r, c + 2 * r], outline=255, width=10)
            ri = r * (0.66 if ring else 0.86)
            d.ellipse([c - 2 * ri, c - 2 * ri, c + 2 * ri, c + 2 * ri], outline=255, width=5)
        m = np.asarray(im.resize((S, S), Image.BOX), np.float32) / 255
        yy = R - tot_h / 2
        for t, sz in lines:
            yy += sz * 1.0
            m = np.maximum(m, text_mask(S, S, t, R, yy - sz * 0.08, sz, face, 'ms'))
            yy += sz * 0.08
        if shape == 'round' and ring:
            rs = ring_size or r * 0.2
            fr = font(ring_face, rs)
            rr = r * 0.83
            advs = [fr.getlength(ch) + rs * 0.12 for ch in ring]
            tot = sum(advs)
            span = min(tot / rr, 2 * np.pi * 0.96)
            a = -np.pi / 2 - span / 2
            for ch, adv in zip(ring, advs):
                aa = a + adv / 2 / rr * (span / (tot / rr))
                px, py = R + np.cos(aa) * rr, R + np.sin(aa) * rr
                m = np.maximum(m, text_mask(S, S, ch, px, py, rs, ring_face, 'mm', rot=-np.rad2deg(aa) - 90))
                a += adv / rr * (span / (tot / rr))
        # rubber: pressure gradient, voids, ink piling at the edges, a little bleed
        Y, X = np.mgrid[0:S, 0:S].astype(np.float32)
        pa = rng.uniform(0, 2 * np.pi) if pressure is None else np.deg2rad(pressure)
        grad = ((X - R) * np.cos(pa) + (Y - R) * np.sin(pa)) / R
        press = np.clip(0.8 + 0.28 * grad + 0.2 * (noise2d(S, S, 50, 3, self._seed()) - 0.5), 0.35, 1.1)
        n = noise2d(S, S, 3.5, 2, self._seed())
        keep = smoothstep(0.6 - 0.5 * press, 0.8 - 0.5 * press, n)
        edge = np.clip(m - blur(m, 1.6), 0, 1)
        ink = np.clip(blur(m, 0.6) * press * (0.3 + 0.7 * keep) * (1 + 0.6 * edge), 0, 1)
        ink = np.clip(ink * alpha, 0, 1)
        A = np.clip(self._rotate([ink], rot, pad=0)[0], 0, 1)
        hh, ww = A.shape
        ox, oy = int(round(cx - ww / 2)), int(round(cy - hh / 2))
        sl = self._box(ox, oy, ox + ww, oy + hh)
        if sl is None: return
        A = A[sl[0].start - oy:sl[0].stop - oy, sl[1].start - ox:sl[1].stop - ox]
        A = A * (0.8 + 0.4 * self.tooth[sl])
        self.img[sl] *= 1 - np.clip(A, 0, 1)[..., None] * (1 - _c(colour))

    def pen(self, pts, width=2.4, colour=INK, alpha=0.85, dash=None, smooth=True, jitter=0.5, dot=0.0):
        """an ink line drawn on the board (leader lines of the diagram): slight hand wobble, optional dashes
        (on, off) in px, optional dot of radius `dot` at the end"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 12)
        seg = np.hypot(*np.diff(P, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
        n = max(2, int(s[-1] / 1.2))
        ss_ = np.linspace(0, s[-1], n)
        P = np.stack([np.interp(ss_, s, P[:, 0]), np.interp(ss_, s, P[:, 1])], 1)
        tg = np.gradient(P, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        P = P + np.stack([-tg[:, 1], tg[:, 0]], 1) * (fbm1d(n, 60, 3, self._seed()) * jitter)[:, None]
        paths = []
        if dash:
            on, off = dash; per = on + off
            k = (ss_ % per) < on
            cur = []
            for i in range(n):
                if k[i]: cur.append(P[i])
                elif cur:
                    if len(cur) > 1: paths.append(cur)
                    cur = []
            if len(cur) > 1: paths.append(cur)
        else:
            paths = [P]
        pad = width + dot + 4
        sl = self._box(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if sl is None: return
        o = np.array([sl[1].start, sl[0].start], np.float32)
        bh, bw = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        m = lines_mask(bh, bw, [np.asarray(p) - o for p in paths], width)
        if dot:
            Y, X = np.mgrid[0:bh, 0:bw].astype(np.float32)
            e = P[-1] - o
            m = np.maximum(m, np.clip(dot - np.hypot(X - e[0], Y - e[1]) + 0.5, 0, 1))
        m = blur(m, 0.35)
        self.img[sl] *= 1 - (m * alpha * (0.85 + 0.3 * self.tooth[sl]))[..., None] * (1 - _c(colour))

    # ------------------------------------------------------------ output
    def composite(self, vignette=0.2, grain=0.03):
        r2 = ((self.XX - self.W * 0.42) / self.W) ** 2 + ((self.YY - self.H * 0.38) / self.H) ** 2
        light = 1.03 - vignette * r2 * 2.0
        img = self.img * light[..., None] + grain * self._grain[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=88, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
