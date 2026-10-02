"""blueprint — engineering blueprints: an inked tracing contact-printed on ferro-prussiate paper (numpy + Pillow only).

Model (how a real blueprint of ~1880-1950 was made, and what happened to it afterwards):
  tracing : the draughtsman inks the drawing on translucent tracing linen with ruling pens of a few fixed widths
            (heavy outlines, medium edges, thin dimension and hatch lines, fine centre lines). Ink pools a little
            where the pen stops, so line ends are a hair fatter. Lettering is single-stroke capitals drawn through a
            lettering guide (`text`: a built-in stroke font, uniform pen width, optional slant), pencil guide lines
            and construction lines stay on the linen faintly (`pencil`). Mistakes are scraped off with a razor
            (`erase`). Everything follows drafting conventions: section hatching clipped to the cut material,
            dimension lines with extension lines and arrowheads, level datums, leaders, cutting-plane marks,
            detail bubbles, a north point, graphic scales, a border with zone marks, a title block.
  print   : the tracing is clamped over paper coated with iron salts and exposed to an arc lamp. Ink blocks the
            light, so under every line the salts stay unreduced and wash out WHITE; everywhere else Prussian blue
            forms. Exposure E = transmission x lamp; the density follows an S-curve (a threshold, not a linear
            ramp), so heavy lines print clean white, fine lines print pale blue, and the background saturates.
            Light creeps under the edges of lines (sharp where the glass pressed the tracing flat, softer where
            contact was poor) and a faint halo forms around them. The lamp is stronger in the middle of the frame
            (darker blue there, paler towards the edges); the coating has faint machine streaks and mottle; the
            paper fibres show through. Colour comes from Beer-Lambert absorption of Prussian blue on paper.
  life    : the sheet is folded to file size: creases crack the blue coat to a broken white line, the paper on
            each side of a fold catches the light differently, crossings wear through (`fold`). The panel that faced
            outwards fades and gets handled (`fade`, `grime`); alkaline water turns Prussian blue rust-brown inside
            a tide line (`stain`); drawing-pin holes rust (`tack`).
  redline : on site someone marks it up in red wax pencil -- clouds, notes, ticks (`red`, `red_text`, `cloud`).
            Red is the only colour that is not part of the print.

Coordinates are output pixels; drawing happens at `ss` x supersampling. Angles in degrees, counter-clockwise.

    from blueprint import Blueprint
    bp = Blueprint(1920, 1080, seed=3)
    bp.border(56, 30, 1890, 1050)
    bp.line([(300, 900), (300, 200)], 'thick'); bp.centerline([(300, 920), (300, 180)])
    bp.hatch([wall_poly], angle=45, spacing=6)
    bp.dim((200, 900), (400, 900), 30, '10.50')
    bp.text('SECTION A-A', 300, 980, 16, anchor='ms')
    bp.stage('drawn')
    bp.fold(xs=[640, 1280], ys=[540]); bp.stain(150, 980, 70)
    bp.cloud([(500, 300), (700, 300), (700, 360), (500, 360)]); bp.red_text('CHECK ON SITE', 720, 330, 26)
    bp.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFont
from core import blur, fbm1d, noise2d, smoothstep, polygon_mask, blob_pts, spline, load_font, text_mask, cjk_font

PENS = {'heavy': 3.3, 'thick': 2.5, 'medium': 1.8, 'thin': 1.25, 'fine': 0.9}
PAPER = np.array([0.94, 0.95, 0.93], np.float32)          # washed-out (unexposed) paper
ABSORB = np.array([2.85, 1.62, 0.70], np.float32)          # Prussian blue: eats red, some green, little blue
RED = np.array([0.90, 0.30, 0.22], np.float32)             # red wax pencil


# ---------------------------------------------------------------- single-stroke lettering (lettering-guide capitals)
def _A(cx, cy, rx, ry, a0, a1, n=None):
    """elliptical arc in glyph units (y down; 0 deg = +x, 90 deg = down)"""
    n = n or max(6, int(abs(a1 - a0) / 10) + 2)
    t = np.radians(np.linspace(a0, a1, n))
    return [(cx + rx * np.cos(a), cy + ry * np.sin(a)) for a in t]


def _S(*pts):
    """smooth stroke through control points"""
    return ('s', list(pts))


def _glyphs():
    G = {
        'A': (4.2, [[(0, 6), (2.1, 0), (4.2, 6)], [(0.75, 4), (3.45, 4)]]),
        'B': (3.8, [[(0, 3), (2.4, 3)] + _A(2.4, 4.5, 1.4, 1.5, -90, 90) + [(0, 6), (0, 0), (2.2, 0)] + _A(2.2, 1.5, 1.3, 1.5, -90, 90) + [(0, 3)]]),
        'C': (3.9, [_A(2.1, 3, 2.1, 3, -42, -318, 30)]),
        'D': (4.0, [[(1.4, 0), (0, 0), (0, 6), (1.4, 6)] + _A(1.4, 3, 2.6, 3, 90, -90, 20)]),
        'E': (3.5, [[(3.5, 0), (0, 0), (0, 6), (3.5, 6)], [(0, 3), (2.6, 3)]]),
        'F': (3.4, [[(3.4, 0), (0, 0), (0, 6)], [(0, 3), (2.6, 3)]]),
        'G': (4.2, [_A(2.1, 3, 2.1, 3, -40, -360, 32) + [(2.5, 3)]]),
        'H': (4.0, [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]]),
        'I': (0.0, [[(0, 0), (0, 6)]]),
        'J': (3.4, [[(3.4, 0), (3.4, 4.3)] + _A(1.7, 4.3, 1.7, 1.7, 0, 180, 14)]),
        'K': (3.8, [[(0, 0), (0, 6)], [(3.8, 0), (0, 4.1)], [(1.35, 2.65), (3.8, 6)]]),
        'L': (3.4, [[(0, 0), (0, 6), (3.4, 6)]]),
        'M': (4.8, [[(0, 6), (0, 0), (2.4, 6), (4.8, 0), (4.8, 6)]]),
        'N': (4.0, [[(0, 6), (0, 0), (4, 6), (4, 0)]]),
        'O': (4.4, [_A(2.2, 3, 2.2, 3, 0, 360, 36)]),
        'P': (3.8, [[(0, 6), (0, 0), (2.2, 0)] + _A(2.2, 1.6, 1.6, 1.6, -90, 90, 14) + [(0, 3.2)]]),
        'Q': (4.4, [_A(2.2, 3, 2.2, 3, 0, 360, 36), [(2.6, 4.3), (4.5, 6.4)]]),
        'R': (3.8, [[(0, 6), (0, 0), (2.2, 0)] + _A(2.2, 1.6, 1.6, 1.6, -90, 90, 14) + [(0, 3.2)], [(2.0, 3.2), (3.8, 6)]]),
        'S': (3.9, [_A(1.95, 1.5, 1.8, 1.5, -20, -270, 18) + _A(1.95, 4.5, 1.95, 1.5, -90, 160, 18)]),
        'T': (4.0, [[(0, 0), (4, 0)], [(2, 0), (2, 6)]]),
        'U': (4.0, [[(0, 0), (0, 4)] + _A(2, 4, 2, 2, 180, 0, 16) + [(4, 0)]]),
        'V': (4.2, [[(0, 0), (2.1, 6), (4.2, 0)]]),
        'W': (5.4, [[(0, 0), (1.35, 6), (2.7, 1.2), (4.05, 6), (5.4, 0)]]),
        'X': (4.0, [[(0, 0), (4, 6)], [(4, 0), (0, 6)]]),
        'Y': (4.2, [[(0, 0), (2.1, 3.1), (4.2, 0)], [(2.1, 3.1), (2.1, 6)]]),
        'Z': (4.0, [[(0, 0), (4, 0), (0, 6), (4, 6)]]),
        '0': (3.6, [_A(1.8, 3, 1.8, 3, 0, 360, 34)]),
        '1': (3.6, [[(0.9, 1.1), (2.1, 0), (2.1, 6)]]),
        '2': (3.6, [_A(1.8, 1.75, 1.8, 1.75, -170, 15, 18) + [(0, 6), (3.6, 6)]]),
        '3': (3.6, [_A(1.8, 1.5, 1.7, 1.5, -160, 90, 18) + _A(1.8, 4.5, 1.8, 1.5, -90, 160, 18)]),
        '4': (3.8, [[(2.8, 6), (2.8, 0), (0, 4.2), (3.8, 4.2)]]),
        '5': (3.6, [[(3.4, 0), (0.4, 0), (0.15, 2.75)] + _A(1.8, 4.1, 1.8, 1.9, -142, 150, 20)]),
        '6': (3.6, [_A(2.2, 4.0, 2.2, 4.0, -60, -180, 12), _A(1.8, 4.2, 1.8, 1.8, 0, 360, 26)]),
        '7': (3.6, [[(0, 0), (3.6, 0), (1.2, 6)]]),
        '8': (3.6, [_A(1.8, 1.45, 1.55, 1.45, 90, 450, 26), _A(1.8, 4.45, 1.8, 1.55, -90, 270, 28)]),
        '9': (3.6, [_A(1.8, 1.8, 1.8, 1.8, 0, 360, 26), _A(1.4, 2.0, 2.2, 4.0, 0, 120, 12)]),
        '.': (0.0, [[(0, 5.92), (0, 6)]]),
        ',': (0.5, [[(0.5, 5.6), (0.5, 6.0), (0, 6.9)]]),
        ':': (0.0, [[(0, 2.4), (0, 2.48)], [(0, 5.92), (0, 6)]]),
        ';': (0.5, [[(0.5, 2.4), (0.5, 2.48)], [(0.5, 5.6), (0.5, 6.0), (0, 6.9)]]),
        '-': (2.4, [[(0, 3.1), (2.4, 3.1)]]),
        '–': (3.6, [[(0, 3.1), (3.6, 3.1)]]),
        '—': (5.0, [[(0, 3.1), (5.0, 3.1)]]),
        '_': (4.0, [[(0, 6.8), (4.0, 6.8)]]),
        '/': (3.0, [[(0, 6.4), (3.0, -0.4)]]),
        '(': (1.5, [_S((1.5, -0.4), (0.45, 1.3), (0.05, 3), (0.45, 4.7), (1.5, 6.4))]),
        ')': (1.5, [_S((0, -0.4), (1.05, 1.3), (1.45, 3), (1.05, 4.7), (0, 6.4))]),
        '[': (1.4, [[(1.4, -0.4), (0, -0.4), (0, 6.4), (1.4, 6.4)]]),
        ']': (1.4, [[(0, -0.4), (1.4, -0.4), (1.4, 6.4), (0, 6.4)]]),
        '+': (3.6, [[(0, 3.2), (3.6, 3.2)], [(1.8, 1.4), (1.8, 5.0)]]),
        '=': (3.2, [[(0, 2.3), (3.2, 2.3)], [(0, 4.0), (3.2, 4.0)]]),
        '<': (3.2, [[(3.2, 1.2), (0, 3.2), (3.2, 5.2)]]),
        '>': (3.2, [[(0, 1.2), (3.2, 3.2), (0, 5.2)]]),
        '°': (1.6, [_A(0.8, 0.8, 0.8, 0.8, 0, 360, 16)]),
        '±': (3.6, [[(0, 2.6), (3.6, 2.6)], [(1.8, 0.8), (1.8, 4.4)], [(0, 6), (3.6, 6)]]),
        'Ø': (4.4, [_A(2.2, 3, 2.2, 3, 0, 360, 34), [(-0.2, 6.5), (4.6, -0.5)]]),
        '×': (3.0, [[(0, 1.7), (3, 4.7)], [(3, 1.7), (0, 4.7)]]),
        '·': (0.0, [[(0, 3.05), (0, 3.15)]]),
        "'": (0.0, [[(0, 0), (0, 1.6)]]),
        '"': (1.0, [[(0, 0), (0, 1.6)], [(1, 0), (1, 1.6)]]),
        '!': (0.0, [[(0, 0), (0, 4.3)], [(0, 5.92), (0, 6)]]),
        '?': (3.4, [_A(1.7, 1.6, 1.7, 1.6, -175, 60, 16) + [(1.7, 3.6), (1.7, 4.3)], [(1.7, 5.92), (1.7, 6)]]),
        '&': (4.2, [_S((4.2, 6), (1.3, 2.1), (1.2, 0.7), (2.0, 0), (2.9, 0.6), (2.8, 1.7), (0.5, 3.6), (0.2, 5.0), (1.2, 6), (2.6, 5.7), (3.9, 3.7))]),
        '#': (4.0, [[(1.2, 0.4), (0.8, 5.6)], [(3.2, 0.4), (2.8, 5.6)], [(0, 2.0), (4, 2.0)], [(0, 4.0), (4, 4.0)]]),
        '%': (4.0, [_A(0.8, 1.0, 0.8, 1.0, 0, 360, 14), _A(3.2, 5.0, 0.8, 1.0, 0, 360, 14), [(0, 6), (4, 0)]]),
        '℄': (4.4, [_A(2.4, 3, 2.0, 2.6, -40, -320, 24), [(2.0, -0.4), (2.0, 6.4), (4.4, 6.4)]]),
        '↑': (2.4, [[(1.2, 6), (1.2, 0)], [(0, 1.4), (1.2, 0), (2.4, 1.4)]]),
        '→': (4.0, [[(0, 3), (4, 3)], [(2.6, 1.8), (4, 3), (2.6, 4.2)]]),
        '✓': (4.0, [[(0, 3.6), (1.4, 6), (4, 0)]]),
        ' ': (2.2, []),
    }
    return G


GLYPHS = _glyphs()


def _glyph_polys(ch):
    w, strokes = GLYPHS.get(ch, GLYPHS.get(ch.upper(), GLYPHS['?']))
    out = []
    for st in strokes:
        if isinstance(st, tuple) and st[0] == 's':
            out.append(spline(st[1], per=6))
        else:
            out.append(np.asarray(st, np.float32))
    return w, out


def _fangsong():
    """a 'long FangSong' face for Chinese title-block text; falls back to the CJK font"""
    env = os.environ.get('INKPAINT_FONT_FANGSONG')
    if env and os.path.exists(env): return env
    for pat in ['/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/STFANGSO.ttf',
                '/System/Library/AssetsV2/PreinstalledAssetsV2/*/com_apple_MobileAsset_Font*/*/AssetData/STFANGSO.ttf',
                '/usr/share/fonts/**/*FangSong*.tt[fc]', '/usr/share/fonts/**/*fangsong*.tt[fc]',
                'C:/Windows/Fonts/simfang.ttf']:
        fs = glob.glob(pat, recursive=True)
        if fs: return fs[0]
    return cjk_font()


def _gauss(a, sigma):
    """true small-sigma gaussian (core.blur quantises sub-pixel sigmas to 0 or ~1.4 px)"""
    r = max(1, int(np.ceil(sigma * 3)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2).astype(np.float32); k /= k.sum()
    out = a.astype(np.float32)
    for ax in (0, 1):
        p = np.pad(out, [(r, r) if i == ax else (0, 0) for i in (0, 1)], mode='edge')
        acc = np.zeros_like(out)
        n = out.shape[ax]
        for i, w in enumerate(k):
            acc += w * (p[i:i + n] if ax == 0 else p[:, i:i + n])
        out = acc
    return out


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


class Blueprint:
    def __init__(self, W=1920, H=1080, seed=0, ss=3, tracing=None):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self._fs = [int(self.rng.integers(1 << 30)) for _ in range(16)]     # field seeds, fixed at birth
        self.ink = Image.new('L', (W * ss, H * ss), 0)                       # ink on the tracing linen
        self.d = ImageDraw.Draw(self.ink)
        self.lead = Image.new('L', (W * ss, H * ss), 0)                      # pencil left on the linen
        self.dl = ImageDraw.Draw(self.lead)
        self.tracing = tracing or (10, 8, W - 10, H - 8)                    # linen edge (outside: bare paper)
        self.time = 1.0                                                      # exposure time
        self.contact = 1.0                                                   # how uneven the frame contact is
        self.folds = []                                                      # ('v'|'h', pos, kind, wear)
        self.fades, self.grimes, self.stains, self.tacks, self.tears = [], [], [], [], []
        self.redl = Image.new('L', (W * 2, H * 2), 0)                        # red wax pencil (2x)
        self.dr = ImageDraw.Draw(self.redl)
        self.stages = []
        self._F = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================ pens
    def _P(self, pts):
        s = self.ss
        return [(float(x) * s, float(y) * s) for x, y in pts]

    def _w(self, pen):
        return PENS[pen] if isinstance(pen, str) else float(pen)

    def line(self, pts, pen='medium', closed=False, pool=True, layer=None):
        """a ruled ink line through `pts`; ink pools a little where the pen stops"""
        pts = [tuple(p) for p in pts]
        if len(pts) < 2: return
        if closed: pts = pts + [pts[0]]
        d = layer or self.d
        ws = max(1, int(round(self._w(pen) * self.ss)))
        P = self._P(pts)
        d.line(P, fill=255, width=ws, joint='curve')
        if not closed:
            r = ws / 2 * (1.18 if pool else 1.0)
            for (x, y) in (P[0], P[-1]):
                d.ellipse((x - r, y - r, x + r, y + r), fill=255)

    def lines(self, polylines, pen='medium'):
        for p in polylines: self.line(p, pen)

    @staticmethod
    def _cut(pts, pattern, phase=0.0, closed=False):
        """split a polyline into dashes; pattern = (on, off, on, off, ...) in px"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)]); L = float(s[-1])
        out, t, i = [], -float(phase), 0
        while t < L:
            l = pattern[i % len(pattern)]
            if i % 2 == 0:
                a, b = max(t, 0.0), min(t + l, L)
                if b > a:
                    k = (s > a) & (s < b)
                    xs = np.concatenate([[a], s[k], [b]])
                    out.append(np.stack([np.interp(xs, s, P[:, 0]), np.interp(xs, s, P[:, 1])], 1))
            t += l; i += 1
        return out

    def dashed(self, pts, pen='thin', dash=(9, 5), phase=0.0, closed=False):
        """hidden / phantom lines"""
        for seg in self._cut(pts, dash, phase, closed): self.line(seg, pen, pool=False)

    def centerline(self, pts, pen='fine', pattern=(28, 5, 4, 5), phase=6.0, closed=False):
        """long-short-long centre line"""
        self.dashed(pts, pen, pattern, phase, closed)

    @staticmethod
    def arc_pts(cx, cy, r, a0, a1, ry=None, n=None):
        """arc in drawing angles (deg, counter-clockwise from +x, y up on paper)"""
        ry = r if ry is None else ry
        n = n or max(8, int(abs(a1 - a0) / 360 * 2 * np.pi * max(r, ry) / 2.5) + 2)
        t = np.radians(np.linspace(a0, a1, n))
        return np.stack([cx + r * np.cos(t), cy - ry * np.sin(t)], 1)

    def circle(self, cx, cy, r, pen='medium', dash=None, ry=None):
        pts = self.arc_pts(cx, cy, r, 0, 360, ry)
        if dash: self.dashed(pts, pen, dash)
        else: self.line(pts, pen, closed=True)

    def arc(self, cx, cy, r, a0, a1, pen='medium', ry=None, dash=None):
        pts = self.arc_pts(cx, cy, r, a0, a1, ry)
        if dash: self.dashed(pts, pen, dash)
        else: self.line(pts, pen)

    def box(self, x0, y0, x1, y1, pen='medium'):
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], pen, closed=True)

    def fill(self, pts, layer=None):
        """solid ink (poché: thin cut metal, arrowheads, filled scale blocks)"""
        (layer or self.d).polygon(self._P(pts), fill=255)

    def dot(self, x, y, r=1.6):
        s = self.ss
        self.d.ellipse(((x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s), fill=255)

    def erase(self, pts):
        """razor scraping: take ink (and pencil) off the linen inside a polygon"""
        self.d.polygon(self._P(pts), fill=0)
        self.dl.polygon(self._P(pts), fill=0)

    def pencil(self, pts, width=1.0, closed=False):
        """graphite left on the tracing: construction and guide lines -> print as faint pale lines"""
        pts = [tuple(p) for p in pts]
        if closed: pts = pts + [pts[0]]
        self.dl.line(self._P(pts), fill=255, width=max(1, int(round(width * self.ss))))

    # ================================================================ hatching
    def hatch(self, polys, angle=45, spacing=6.0, pen='fine', holes=(), kind='lines', phase=0.0):
        """section hatching clipped to the cut material. kind: 'lines' (masonry / general), 'cross' (metal),
        'glass' (short triple strokes), 'rock' (broken fissures), 'stipple' (concrete), 'solid' (poché)"""
        polys = [np.asarray(p, np.float32) for p in polys]
        allp = np.vstack(polys)
        ss = self.ss
        x0 = max(0, int(np.floor(allp[:, 0].min())) - 3); y0 = max(0, int(np.floor(allp[:, 1].min())) - 3)
        x1 = min(self.W, int(np.ceil(allp[:, 0].max())) + 3); y1 = min(self.H, int(np.ceil(allp[:, 1].max())) + 3)
        if x1 <= x0 or y1 <= y0: return
        bw, bh = (x1 - x0) * ss, (y1 - y0) * ss
        mask = Image.new('L', (bw, bh), 0); dm = ImageDraw.Draw(mask)
        loc = lambda p: [((x - x0) * ss, (y - y0) * ss) for x, y in p]
        for p in polys: dm.polygon(loc(p), fill=255)
        for h in holes: dm.polygon(loc(np.asarray(h, np.float32)), fill=0)
        lay = Image.new('L', (bw, bh), 0); dh = ImageDraw.Draw(lay)
        ws = max(1, int(round(self._w(pen) * ss)))
        r = np.random.default_rng(self._seed())
        if kind == 'solid':
            lay = mask
        elif kind in ('lines', 'cross', 'glass'):
            angs = [angle] + ([angle + 90] if kind == 'cross' else [])
            for a in angs:
                u = np.array([np.cos(np.radians(a)), -np.sin(np.radians(a))])          # along the lines
                n = np.array([-u[1], u[0]])                                              # across
                corners = np.array([[x0, y0], [x1, y0], [x0, y1], [x1, y1]], np.float32)
                c = corners @ n
                k0, k1 = int(np.floor((c.min() - phase) / spacing)), int(np.ceil((c.max() - phase) / spacing))
                Lh = float(np.hypot(x1 - x0, y1 - y0)) + 10
                mid = np.array([(x0 + x1) / 2, (y0 + y1) / 2])
                for k in range(k0, k1 + 1):
                    off = k * spacing + phase - mid @ n
                    p = mid + n * off
                    if kind == 'glass':
                        # groups of three short strokes, staggered
                        t = -Lh / 2 + (k % 3) * spacing * 1.7
                        while t < Lh / 2:
                            for j in range(3):
                                q = p + n * (j * spacing * 0.28 - spacing * 0.28)
                                a0, b0 = q + u * t, q + u * (t + spacing * 1.1 - j * spacing * 0.25)
                                dh.line([((a0[0] - x0) * ss, (a0[1] - y0) * ss), ((b0[0] - x0) * ss, (b0[1] - y0) * ss)], fill=255, width=ws)
                            t += spacing * 5.5
                        continue
                    a0, b0 = p - u * Lh / 2, p + u * Lh / 2
                    dh.line([((a0[0] - x0) * ss, (a0[1] - y0) * ss), ((b0[0] - x0) * ss, (b0[1] - y0) * ss)], fill=255, width=ws)
        elif kind == 'rock':
            area = (x1 - x0) * (y1 - y0)
            for _ in range(int(area / (spacing * spacing * 9)) + 3):
                cx, cy = r.uniform(x0, x1), r.uniform(y0, y1)
                a = r.uniform(0, np.pi); L = r.uniform(spacing * 1.5, spacing * 4.5)
                pts = [(cx, cy)]
                for _s in range(int(r.integers(2, 4))):
                    a += r.normal(0, 0.6)
                    cx += np.cos(a) * L / 3; cy += np.sin(a) * L / 3
                    pts.append((cx, cy))
                dh.line([((x - x0) * ss, (y - y0) * ss) for x, y in pts], fill=255, width=ws, joint='curve')
        elif kind == 'stipple':
            area = (x1 - x0) * (y1 - y0)
            for _ in range(int(area / (spacing * spacing) * 1.6)):
                cx, cy = r.uniform(x0, x1) - x0, r.uniform(y0, y1) - y0
                rr = r.uniform(0.4, 0.9) * ss * self._w(pen)
                dh.ellipse((cx * ss - rr, cy * ss - rr, cx * ss + rr, cy * ss + rr), fill=255)
        if kind != 'solid':
            lay = ImageChops.multiply(lay, mask)
        box = (x0 * ss, y0 * ss, x1 * ss, y1 * ss)
        self.ink.paste(ImageChops.lighter(self.ink.crop(box), lay), box[:2])

    def ground(self, pts, depth=10, every=14, pen='thin', line_pen='thick'):
        """natural ground line with the usual groups of short ticks below it"""
        P = np.asarray(pts, np.float32)
        self.line(P, line_pen)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
        for t in np.arange(every * 0.5, s[-1] - 4, every):
            x, y = np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])
            for j in range(3):
                xx = x + (j - 1) * depth * 0.35
                self.line([(xx, y + 2), (xx - depth * 0.55, y + 2 + depth * (0.9 - 0.18 * abs(j - 1)))], pen, pool=False)

    def breakline(self, p0, p1, pen='thin', zig=7):
        """long break line with a single zig-zag in the middle"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        u = _unit(p1 - p0); n = np.array([-u[1], u[0]]); m = (p0 + p1) / 2
        self.line([p0, m - u * zig * 0.6, m - u * zig * 0.25 + n * zig, m + u * zig * 0.25 - n * zig, m + u * zig * 0.6, p1], pen)

    # ================================================================ lettering
    def text_width(self, s, size, spacing=0.22):
        k = size / 6.0
        w = 0.0
        for ch in s.upper():
            w += GLYPHS.get(ch, GLYPHS['?'])[0] * k + spacing * size
        return max(0.0, w - spacing * size)

    def text(self, s, x, y, size=12, anchor='ls', pen=None, slant=0.0, spacing=0.22, rot=0.0, guide=False,
             line_gap=1.7, clear=False):
        """single-stroke capitals; size = cap height px; anchor: [l|m|r][t|m|s] (s = baseline).
        rot in degrees counter-clockwise; slant e.g. 0.22 for inclined lettering; clear=True scrapes the hatching
        out from behind the text first (as draughtsmen leave hatching out around dimension figures). Returns the width."""
        lines = s.split('\n')
        if len(lines) > 1:
            dy = size * line_gap
            v = anchor[1]
            top = {'t': 0, 'm': -(len(lines) - 1) * dy / 2, 's': -(len(lines) - 1) * dy}.get(v, 0)
            c, sn = np.cos(np.radians(rot)), np.sin(np.radians(rot))
            for i, ln in enumerate(lines):
                o = top + i * dy
                self.text(ln, x - sn * o, y + c * o, size, anchor, pen, slant, spacing, rot, guide, clear=clear)
            return max(self.text_width(ln, size, spacing) for ln in lines)
        k = size / 6.0
        wpx = self.text_width(s, size, spacing)
        ax = {'l': 0.0, 'm': -wpx / 2, 'r': -wpx}[anchor[0]]
        ay = {'t': 0.0, 'a': 0.0, 'm': -3 * k, 's': -6 * k, 'b': -6 * k}[anchor[1]]
        c, sn = np.cos(np.radians(rot)), np.sin(np.radians(rot))

        def T(px, py):                                 # local (x right, y down) -> page
            lx, ly = px + ax, py + ay
            return (x + lx * c + ly * sn, y - lx * sn + ly * c)
        pw = pen if pen is not None else max(1.0, size * 0.11)
        if clear:
            m = size * 0.35
            self.erase([T(-m, -m), T(wpx + m, -m), T(wpx + m, 6 * k + m), T(-m, 6 * k + m)])
        if guide:
            for gy in (0.0, 6 * k):
                self.pencil([T(-size * 0.5, gy), T(wpx + size * 0.5, gy)], 0.8)
        cx = 0.0
        for ch in s.upper():
            gw, polys = _glyph_polys(ch)
            for P in polys:
                pts = [T(cx + (u + slant * (6 - v)) * k, v * k) for u, v in P]
                if len(P) == 2 and np.hypot(*(P[1] - P[0])) < 0.2:          # full stops, colons: a round dot
                    self.dot(pts[0][0], pts[0][1], max(pw * 0.85, 0.3 * k))
                else:
                    self.line(pts, pw, pool=False)
            cx += gw * k + spacing * size
        return wpx

    def cjk(self, s, x, y, size=18, anchor='ls', condense=0.72, font=None):
        """Chinese in long FangSong (narrowed as on engineering drawings), inked into the tracing"""
        path = font or _fangsong()
        ss = self.ss
        f = ImageFont.truetype(path, int(size * ss * 1.25)) if path else load_font('cjk', size * ss * 1.25)
        bb = f.getbbox(s)
        tw, th = bb[2] - bb[0] + 4, bb[3] - bb[1] + 4
        im = Image.new('L', (tw, th), 0)
        ImageDraw.Draw(im).text((-bb[0] + 2, -bb[1] + 2), s, font=f, fill=255)
        im = im.resize((max(1, int(tw * condense)), th), Image.LANCZOS)
        from PIL import ImageFilter                       # a lettering pen, not a hairline: thicken and solidify
        im = im.filter(ImageFilter.MaxFilter(3)).point(lambda v: min(255, int(v * 1.35)))
        w, h = im.size
        X = x * ss - {'l': 0, 'm': w / 2, 'r': w}[anchor[0]]
        Y = y * ss - {'t': 0, 'a': 0, 'm': h / 2, 's': h, 'b': h}[anchor[1]]
        X, Y = int(round(X)), int(round(Y))
        box = (X, Y, X + w, Y + h)
        self.ink.paste(ImageChops.lighter(self.ink.crop(box), im), box[:2])
        return w / ss

    # ================================================================ drafting conventions
    def arrowhead(self, tip, direction, size=9.0, kind='filled', pen='thin'):
        tip = np.asarray(tip, np.float32); u = _unit(direction); n = np.array([-u[1], u[0]])
        back = tip - u * size
        if kind == 'filled':
            self.fill([tip, back + n * size * 0.2, back - n * size * 0.2])
        elif kind == 'open':
            self.line([back + n * size * 0.3, tip, back - n * size * 0.3], pen)
        elif kind == 'tick':
            d = _unit(u + n) * size * 0.55
            self.line([tip - d, tip + d], 'medium')
        elif kind == 'dot':
            self.dot(tip[0], tip[1], size * 0.2)

    def dim(self, p0, p1, offset, text=None, size=11, pen='fine', arrows='filled', gap=3.0, ext=5.0,
            scale=None, fmt='{:.2f}', text_off=3.0, shift=0.0, clear=True):
        """linear dimension between p0 and p1, dimension line `offset` px to the left of p0->p1 (negative = right).
        text defaults to the length / scale. Text sits above the line, reading from the bottom or the right."""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        d = p1 - p0; L = float(np.linalg.norm(d)); u = d / (L + 1e-9)
        n = np.array([u[1], -u[0]])                         # left of travel on the page (y down)
        sg = 1.0 if offset >= 0 else -1.0
        q0, q1 = p0 + n * offset, p1 + n * offset
        if abs(offset) > gap + 1:
            self.line([p0 + n * sg * gap, q0 + n * sg * ext], pen, pool=False)
            self.line([p1 + n * sg * gap, q1 + n * sg * ext], pen, pool=False)
        self.line([q0, q1], pen, pool=False)
        asz = size * 0.8
        if L > asz * 2.6:
            self.arrowhead(q0, -u, asz, arrows); self.arrowhead(q1, u, asz, arrows)
        else:                                               # tight: arrows outside pointing in
            self.line([q0 - u * asz * 1.8, q0], pen, pool=False); self.line([q1, q1 + u * asz * 1.8], pen, pool=False)
            self.arrowhead(q0, u, asz, arrows); self.arrowhead(q1, -u, asz, arrows)
        if text is None:
            text = fmt.format(L / scale) if scale else fmt.format(L)
        if text:
            ang = np.degrees(np.arctan2(-u[1], u[0]))
            if ang > 90.5: ang -= 180
            if ang <= -89.5: ang += 180
            a = np.radians(ang)
            up = np.array([-np.sin(a), -np.cos(a)])
            along = np.array([np.cos(a), -np.sin(a)])
            m = (q0 + q1) / 2 + up * text_off + along * shift
            self.text(text, m[0], m[1], size, 'ms', rot=ang, clear=clear)

    def level(self, x, y, text, size=11, length=70, side='right', pen='thin', mark_at=None):
        """level datum: a horizontal line with the half-filled triangle sitting on it and the level above"""
        sgn = 1 if side == 'right' else -1
        self.line([(x, y), (x + sgn * length, y)], pen, pool=False)
        tx = mark_at if mark_at is not None else x + sgn * length * 0.32
        h = size * 0.85
        tri = [(tx, y), (tx - h * 0.58, y - h), (tx + h * 0.58, y - h)]
        self.line(tri, pen, closed=True)
        self.fill([(tx, y), (tx - h * 0.58, y - h), (tx, y - h)])
        self.text(text, tx + sgn * h * 0.9, y - 3, size, 'ls' if sgn > 0 else 'rs')

    def leader(self, pts, text, size=10, end='arrow', pen='fine', shoulder=12, gap=4):
        """leader from pts[0] (the thing) to pts[-1], a short shoulder, then the note"""
        P = [np.asarray(p, np.float32) for p in pts]
        last = P[-1]
        sgn = 1 if (len(P) < 2 or last[0] >= P[-2][0]) else -1
        sh = last + np.array([sgn * shoulder, 0])
        self.line(P + [sh], pen, pool=False)
        if end == 'arrow': self.arrowhead(P[0], P[0] - P[1], size * 0.8)
        elif end == 'dot': self.dot(P[0][0], P[0][1], max(1.6, size * 0.16))
        self.text(text, sh[0] + sgn * gap, sh[1], size, ('l' if sgn > 0 else 'r') + 'm')

    def cut_mark(self, p0, p1, label, view, size=16, through=True, arm=26):
        """cutting plane: heavy ends, arrows showing the viewing direction, the letter at each end"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        u = _unit(p1 - p0); v = _unit(view)
        if through: self.centerline([p0, p1], 'fine', (26, 4, 6, 4))
        for p, s in ((p0, 1), (p1, -1)):
            self.line([p, p + u * s * arm], 'heavy')
            self.line([p, p + v * size * 1.5], 'thin', pool=False)
            self.arrowhead(p + v * size * 1.6, v, size * 0.75)
            c = p + v * size * 1.0 - u * s * size * 0.9
            self.text(label, c[0], c[1], size, 'mm', pen=max(1.1, size * 0.12))

    def bubble(self, x, y, r, top, bottom=None, size=None, pen='medium'):
        """detail / section callout: a circle, split if it also names the sheet"""
        size = size or r * 0.62
        self.circle(x, y, r, pen)
        if bottom is None:
            self.text(top, x, y, size, 'mm')
        else:
            self.line([(x - r, y), (x + r, y)], 'thin', pool=False)
            self.text(top, x, y - r * 0.47, size * 0.8, 'mm')
            self.text(bottom, x, y + r * 0.47, size * 0.8, 'mm')

    def view_title(self, x, y, title, sub=None, size=16, bubble=None):
        """drawing title: lettering on a heavy + thin double underline, scale underneath"""
        w = self.text(title, x, y, size, 'ms', pen=max(1.2, size * 0.12))
        x0, x1 = x - w / 2 - 6, x + w / 2 + 6
        if bubble:
            bx = x0 - size * 1.4
            self.bubble(bx, y - size * 0.15, size * 1.05, *bubble)
            x0 = bx + size * 1.05
        self.line([(x0, y + 6), (x1, y + 6)], 'thick')
        self.line([(x0, y + 10), (x1, y + 10)], 'fine', pool=False)
        if sub: self.text(sub, x, y + 26, size * 0.62, 'ms')

    def north(self, x, y, r=26, rot=0.0):
        """north point: circle, half-inked arrow, N"""
        self.circle(x, y, r, 'thin')
        a = np.radians(90 + rot)
        u = np.array([np.cos(a), -np.sin(a)]); n = np.array([-u[1], u[0]])
        tip, tail = np.array([x, y]) + u * r * 1.25, np.array([x, y]) - u * r * 0.85
        L, R = np.array([x, y]) - u * r * 0.35 + n * r * 0.38, np.array([x, y]) - u * r * 0.35 - n * r * 0.38
        self.line([tail, L, tip, R, tail], 'thin', closed=True)
        self.fill([tail, L, tip])
        c = np.array([x, y]) + u * r * 1.75
        self.text('N', c[0], c[1], r * 0.55, 'mm', rot=rot, pen=1.3)

    def scale_bar(self, x, y, px_per_unit, units=(0, 1, 2, 3, 4, 5), sub=5, label=None, size=10, h=7):
        """graphic scale: alternate inked / open blocks, one division left of 0 subdivided.
        px_per_unit: drawing px per real unit (metre); units: tick values in real units"""
        xs = [x + (u - units[0]) * px_per_unit for u in units]
        unit_px = (units[1] - units[0]) * px_per_unit
        self.line([(x - unit_px, y), (xs[-1], y)], 'fine', pool=False)
        self.line([(x - unit_px, y + h), (xs[-1], y + h)], 'fine', pool=False)
        for i in range(len(xs) - 1):
            if i % 2 == 0: self.fill([(xs[i], y), (xs[i + 1], y), (xs[i + 1], y + h), (xs[i], y + h)])
        for i in range(sub):
            a = x - unit_px + i * unit_px / sub
            if i % 2 == 0: self.fill([(a, y + h / 2), (a + unit_px / sub, y + h / 2), (a + unit_px / sub, y + h), (a, y + h)])
        for xx in [x - unit_px] + xs:
            self.line([(xx, y - 2), (xx, y + h)], 'fine', pool=False)
        fmt = lambda v: ('%g' % v)
        self.text(fmt(units[1] - units[0]), x - unit_px, y - 5, size * 0.8, 'ms')
        for u, xx in zip(units, xs):
            self.text(fmt(u), xx, y - 5, size * 0.8, 'ms')
        if label: self.text(label, (x - unit_px + xs[-1]) / 2, y + h + size + 6, size, 'ms')

    def border(self, x0, y0, x1, y1, zones=(8, 4), pen='heavy', size=11):
        """drawing frame with zone ticks and zone letters / numbers in the margin"""
        self.box(x0, y0, x1, y1, pen)
        nx, ny = zones
        for i in range(nx + 1):
            xx = x0 + (x1 - x0) * i / nx
            if 0 < i < nx:
                self.line([(xx, y0), (xx, y0 - 10)], 'thin', pool=False); self.line([(xx, y1), (xx, y1 + 10)], 'thin', pool=False)
            if i < nx:
                xm = x0 + (x1 - x0) * (i + 0.5) / nx
                self.text(str(nx - i), xm, (y0) / 2 + 1, size * 0.8, 'mm')
                self.text(str(nx - i), xm, (y1 + self.H) / 2, size * 0.8, 'mm')
        for j in range(ny + 1):
            yy = y0 + (y1 - y0) * j / ny
            if 0 < j < ny:
                self.line([(x0, yy), (x0 - 10, yy)], 'thin', pool=False); self.line([(x1, yy), (x1 + 10, yy)], 'thin', pool=False)
            if j < ny:
                ym = y0 + (y1 - y0) * (j + 0.5) / ny
                L = 'ABCDEFGH'[j]
                self.text(L, x0 / 2, ym, size * 0.8, 'mm'); self.text(L, (x1 + self.W) / 2, ym, size * 0.8, 'mm')

    def table(self, x0, y0, widths, heights, pen='thin', outer='medium'):
        """ruled table (title block / revision block); returns cell rects [row][col]"""
        xs = np.concatenate([[x0], x0 + np.cumsum(widths)]); ys = np.concatenate([[y0], y0 + np.cumsum(heights)])
        for x in xs[1:-1]: self.line([(x, ys[0]), (x, ys[-1])], pen, pool=False)
        for y in ys[1:-1]: self.line([(xs[0], y), (xs[-1], y)], pen, pool=False)
        self.box(xs[0], ys[0], xs[-1], ys[-1], outer)
        return [[(xs[i], ys[j], xs[i + 1], ys[j + 1]) for i in range(len(widths))] for j in range(len(heights))]

    def revision(self, x, y, mark, size=11):
        """revision triangle with its letter"""
        h = size * 1.6
        self.line([(x, y - h * 0.62), (x - h * 0.58, y + h * 0.38), (x + h * 0.58, y + h * 0.38)], 'thin', closed=True)
        self.text(mark, x, y + h * 0.08, size * 0.72, 'mm')

    # ================================================================ the print
    def expose(self, time=1.0, contact=1.0):
        """exposure time (1 = correct; 0.8 under-exposed, paler; 1.3 over) and how uneven the frame contact is"""
        self.time, self.contact = time, contact

    def _fields(self):
        if self._F is not None: return self._F
        H, W, s = self.H, self.W, self._fs
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        F = {}
        r2 = ((xx - W * 0.53) / (W * 0.78)) ** 2 + ((yy - H * 0.46) / (H * 0.95)) ** 2
        F['lamp'] = (1.0 - 0.30 * r2) * (0.93 + 0.12 * noise2d(H, W, 380, 3, s[0]))
        streak = fbm1d(H, 5, 4, s[1])[:, None] * (0.6 + 0.4 * noise2d(H, W, 700, 2, s[2]))
        mott = noise2d(H, W, 120, 4, s[3])
        # wash marks: the print hung to dry after the water bath, so faint runs go down the sheet from the top
        runs = fbm1d(W, 9, 4, s[11])[None, :] * fbm1d(W, 60, 3, s[12])[None, :]
        fall = smoothstep(1.0, 0.0, yy / H * (0.8 + 0.5 * noise2d(H, W, 300, 2, s[13])))
        F['coat'] = (1.0 - 0.035 * streak - 0.07 * smoothstep(0.35, 0.9, mott)
                     - 0.10 * np.clip(runs * 3.0, 0, 1) * fall).astype(np.float32)
        F['contact'] = smoothstep(0.55, 0.9, noise2d(H, W, 450, 3, s[4])).astype(np.float32)
        g = np.random.default_rng(s[5])
        fib = np.asarray(Image.fromarray(g.random((H // 2, W // 7)).astype(np.float32)).resize((W, H), Image.BICUBIC))
        F['fibre'] = (0.55 * fib + 0.45 * noise2d(H, W, 2.2, 2, s[6])).astype(np.float32)
        F['grain'] = g.normal(0, 1, (H, W)).astype(np.float32)
        sk = noise2d(H, W, 3.0, 2, s[7])
        F['skip'] = (smoothstep(0.84, 0.96, sk) * smoothstep(0.55, 0.85, noise2d(H, W, 90, 2, s[8]))).astype(np.float32)
        F['resid'] = noise2d(H, W, 260, 3, s[9])
        self._F = F
        return F

    def _density(self):
        F = self._fields()
        W, H = self.W, self.H
        A = np.asarray(self.ink.resize((W, H), Image.BOX), np.float32) / 255
        Pn = np.asarray(self.lead.resize((W, H), Image.BOX), np.float32) / 255
        A = A * (1 - 0.45 * F['skip'])                                   # pen starved on the linen here and there
        opaque = 1 - (1 - 0.985 * A) * (1 - 0.5 * Pn * (0.7 + 0.6 * F['fibre']))
        tx0, ty0, tx1, ty1 = self.tracing
        lin = np.full((H, W), 1.0, np.float32)
        lin[ty0:ty1, tx0:tx1] = 0.90 + 0.03 * (F['fibre'][ty0:ty1, tx0:tx1] - 0.5)
        T = (1 - opaque) * lin
        c = np.clip(F['contact'] * self.contact, 0, 1)
        Tb = _gauss(T, 0.55) * (1 - c) + _gauss(T, 0.9) * c             # light creeping under the line edges
        Teff = 0.88 * Tb + 0.12 * blur(T, 6.0)                          # halo
        E = Teff * F['lamp'] * self.time
        e0, w = 0.46, 0.09
        sg = lambda z: 1 / (1 + np.exp(-z))
        D = (sg((E - e0) / w) - sg(-e0 / w)) / (1 - sg(-e0 / w))
        D = D * F['coat']
        return np.clip(D, 0, 1).astype(np.float32), E

    def _fold_profile(self, kind, pos, wear):
        """(crack, slope, worn) maps for one fold"""
        H, W = self.H, self.W
        F = self._fields()
        sd = int(pos * 7 + (13 if kind == 'v' else 29)) % (1 << 30)
        if kind == 'v':
            wob = pos + 1.4 * fbm1d(H, 120, 3, sd)
            d = np.arange(W, dtype=np.float32)[None, :] - wob[:, None]
            along = noise2d(H, 1, 6, 3, sd + 1)[:, 0][:, None] * np.ones((1, W), np.float32)
        else:
            wob = pos + 1.4 * fbm1d(W, 120, 3, sd)
            d = np.arange(H, dtype=np.float32)[:, None] - wob[None, :]
            along = noise2d(1, W, 6, 3, sd + 1)[0][None, :] * np.ones((H, 1), np.float32)
        broken = smoothstep(0.25, 0.65, along) * (0.6 + 0.4 * F['fibre'])
        crack = np.exp(-(d / 0.9) ** 2) * broken * wear
        scuff = np.exp(-(d / 3.2) ** 2) * (0.5 + 0.5 * F['fibre']) * wear
        slope = np.sign(d) * np.exp(-np.abs(d) / 22.0)
        return crack.astype(np.float32), scuff.astype(np.float32), slope.astype(np.float32)

    def render(self):
        H, W = self.H, self.W
        F = self._fields()
        D, E = self._density()
        yy, xx = None, None
        shade = np.zeros((H, W), np.float32)
        wearmap = np.zeros((H, W), np.float32)
        # ---- folds
        vs = [f for f in self.folds if f[0] == 'v']; hs = [f for f in self.folds if f[0] == 'h']
        for kind, pos, mount, wear in self.folds:
            crack, scuff, slope = self._fold_profile(kind, pos, wear)
            D = D * (1 - 0.85 * crack) * (1 - 0.16 * scuff)
            shade += 0.045 * mount * slope * wear
            wearmap = np.maximum(wearmap, crack)
        if vs and hs:
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            for _, px, _, w1 in vs:
                for _, py, _, w2 in hs:
                    rr = np.hypot(xx - px, (yy - py) * 1.0)
                    sp = np.exp(-(rr / 7.0) ** 2) * (0.55 + 0.45 * F['fibre']) * min(w1, w2)
                    D = D * (1 - 0.38 * sp)
                    wearmap = np.maximum(wearmap, sp)
        # ---- faded panels
        for (x0, y0, x1, y1, amt) in self.fades:
            m = self._rectmask(x0, y0, x1, y1, 2.5)
            D = D * (1 - amt * m * (0.85 + 0.3 * F['resid']))
        # ---- alkali / water stains
        stain_m = np.zeros((H, W), np.float32); tide = np.zeros((H, W), np.float32)
        for (x, y, r, sd, strength) in self.stains:
            # the water spread, then dried back in two fronts: each front leaves a crisp tide line
            for j, (sc, w) in enumerate(((1.0, 1.0), (0.62, 0.55))):
                pts = blob_pts(x + j * r * 0.12, y - j * r * 0.08, r * sc, r * sc * 0.8, rough=0.22 + 0.06 * j, n=160, seed=sd + 7 * j, rot=0.4)
                m = polygon_mask(H, W, pts, ss=2)
                mb = _gauss(m, 1.1)
                ring = smoothstep(0.12, 0.5, mb) * smoothstep(0.95, 0.55, mb)
                tide = np.maximum(tide, ring * w * strength * (0.65 + 0.35 * noise2d(H, W, 9, 2, sd + 3 + j)))
                if j == 0:
                    mot = noise2d(H, W, r * 0.3, 3, sd + 1)
                    stain_m = np.maximum(stain_m, _gauss(m, 2.0) * (0.35 + 0.65 * mot) * strength)
        D = D * (1 - 0.42 * stain_m)
        # ---- colour: Prussian blue on paper (Beer-Lambert), paper fibres, iron residue in the half-tones
        paper = PAPER[None, None, :] * (0.965 + 0.06 * F['fibre'][..., None])
        dens = 0.90 * D
        img = paper * np.exp(-dens[..., None] * ABSORB[None, None, :])
        resid = (D * (1 - D) * 4) * (0.35 + 0.65 * F['resid'])
        img[..., 2] *= 1 - 0.10 * resid
        img[..., 0] *= 1 + 0.06 * resid
        img *= (1 + 0.018 * F['grain'] * (0.5 + D))[..., None]
        # brown where alkali destroyed the blue, darker at the tide line
        brown = np.array([0.66, 0.52, 0.33], np.float32)
        img = img * (1 - 0.32 * stain_m[..., None]) + brown * paper * 0.32 * stain_m[..., None] * (0.75 + 0.25 * F['fibre'][..., None])
        img = img * (1 - 0.7 * tide[..., None]) + np.array([0.40, 0.28, 0.15], np.float32) * 0.7 * tide[..., None]
        # ---- handled / grubby panels
        for (x0, y0, x1, y1, amt) in self.grimes:
            m = self._rectmask(x0, y0, x1, y1, 3) * (0.6 + 0.4 * F['resid']) * amt
            img *= (1 - m[..., None] * np.array([0.10, 0.14, 0.22], np.float32))
        # ---- paper relief: fold shading, worn fibres at the cracks
        img *= (1 + shade)[..., None]
        img = img + (np.array([0.80, 0.84, 0.86]) - img) * (wearmap * 0.2)[..., None]
        # ---- drawing pins: hole, torn rim, rust halo
        if self.tacks:
            if yy is None: yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            for (x, y) in self.tacks:
                rr = np.hypot(xx - x, yy - y)
                halo = np.exp(-(rr / 9.0) ** 2) * (0.6 + 0.4 * F['fibre'])
                img *= (1 - 0.45 * halo[..., None] * np.array([0.2, 0.55, 0.95], np.float32))
                rim = smoothstep(3.6, 2.4, rr) * (0.6 + 0.4 * F['fibre'])
                img = img + (np.array([0.78, 0.80, 0.80]) - img) * rim[..., None] * 0.6
                hole = smoothstep(2.4, 1.4, rr)
                img = img * (1 - hole[..., None]) + np.array([0.07, 0.06, 0.05]) * hole[..., None]
        # ---- small edge tears where folds meet the edge
        for (x, y, dx, dy, L) in self.tears:
            if yy is None: yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            t = np.clip(((xx - x) * dx + (yy - y) * dy) / L, 0, 1)
            across = np.abs((xx - x) * -dy + (yy - y) * dx)
            notch = smoothstep(1.4 * (1 - t) + 0.2, 0.0, across) * ((((xx - x) * dx + (yy - y) * dy) >= 0) & (t < 1))
            img = img * (1 - notch[..., None]) + np.array([0.08, 0.07, 0.06]) * notch[..., None]
        # ---- sheet edge: a little darker where it has been handled
        if yy is None: yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        edge = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy))
        img *= (1 - 0.10 * np.exp(-edge / 5.0) * (0.6 + 0.4 * F['fibre']))[..., None]
        # ---- red wax pencil on top
        rc = self._red_cover()
        if rc is not None:
            img = img * (1 - rc[..., None] * 0.86) + RED * rc[..., None] * 0.86 * (0.92 + 0.12 * F['fibre'][..., None])
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def _rectmask(self, x0, y0, x1, y1, soft):
        H, W = self.H, self.W
        m = np.zeros((H, W), np.float32)
        m[max(0, int(y0)):min(H, int(y1)), max(0, int(x0)):min(W, int(x1))] = 1
        return blur(m, soft)

    # ================================================================ the life of the sheet
    def fold(self, xs=(), ys=(), wear=1.0, accordion=True):
        """fold the print to file size along vertical lines xs and horizontal lines ys"""
        for i, x in enumerate(xs): self.folds.append(('v', float(x), (1 if (i % 2 == 0 or not accordion) else -1), wear))
        for j, y in enumerate(ys): self.folds.append(('h', float(y), (1 if (j % 2 == 0 or not accordion) else -1), wear))

    def fade(self, x0, y0, x1, y1, amount=0.15):
        """the panel that faced the light (outermost when folded) has faded"""
        self.fades.append((x0, y0, x1, y1, amount))

    def grime(self, x0, y0, x1, y1, amount=1.0):
        """handled panel: grey-brown dirt from fingers and filing"""
        self.grimes.append((x0, y0, x1, y1, amount))

    def stain(self, x, y, r, strength=1.0):
        """alkaline water: blue turns rust-brown inside a darker tide line"""
        self.stains.append((x, y, r, self._seed(), strength))

    def tack(self, x, y):
        self.tacks.append((x, y))

    def tear(self, x, y, direction, length=10):
        """a little split in from the sheet edge (usually where a fold meets it)"""
        u = _unit(direction)
        self.tears.append((x, y, float(u[0]), float(u[1]), float(length)))

    # ================================================================ red wax pencil
    def red(self, pts, width=2.6, smooth=True):
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, per=8)
        r = np.random.default_rng(self._seed())
        P = P + r.normal(0, 0.25, P.shape).astype(np.float32)
        self.dr.line([(float(x) * 2, float(y) * 2) for x, y in P], fill=255, width=max(1, int(round(width * 2))), joint='curve')

    def cloud(self, pts, bump=22, width=2.4):
        """revision cloud: scalloped arcs bulging outwards along a closed path"""
        P = np.asarray(pts, np.float32)
        P = np.vstack([P, P[:1]])
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
        L = float(s[-1]); n = max(6, int(L / bump))
        t = np.linspace(0, L, n + 1)
        Q = np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1)
        area = 0.5 * np.sum(P[:-1, 0] * P[1:, 1] - P[1:, 0] * P[:-1, 1])
        out = []
        r = np.random.default_rng(self._seed())
        for i in range(n):
            a, b = Q[i], Q[i + 1]
            m = (a + b) / 2; u = _unit(b - a); nn = np.array([u[1], -u[0]]) * (1 if area > 0 else -1)
            hgt = np.linalg.norm(b - a) * r.uniform(0.38, 0.5)
            for k in np.linspace(0, 1, 7)[:-1]:
                p = a + (b - a) * k + nn * hgt * np.sin(np.pi * k)
                out.append(p)
        out.append(Q[-1] + np.array([3.0, 2.0]))
        self.red(np.array(out), width, smooth=False)

    def red_text(self, s, x, y, size=26, rot=0.0, anchor='ls', font='hand'):
        f = load_font(font, size * 2)
        m = text_mask(self.H * 2, self.W * 2, s, f, (x * 2, y * 2), anchor=anchor, rot=rot)
        self.redl.paste(ImageChops.lighter(self.redl, Image.fromarray((m * 255).astype(np.uint8))), (0, 0))

    def _red_cover(self):
        a = np.asarray(self.redl.resize((self.W, self.H), Image.BOX), np.float32) / 255
        if a.max() <= 0: return None
        F = self._fields()
        tooth = 0.55 * F['fibre'] + 0.45 * noise2d(self.H, self.W, 1.6, 1, self._fs[10])
        return np.clip((a * 1.15 - tooth * 0.55) / 0.6, 0, 1) * smoothstep(0.02, 0.3, a)

    # ================================================================ output
    def stage(self, name):
        self.stages.append((name, self.render()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.render()
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
