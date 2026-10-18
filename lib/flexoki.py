"""flexoki — Flexoki 纸面 / Flexoki Paper: explainer sheets on warm paper, with diagrams drawn the way a lightweight
diagram renderer draws them (numpy + Pillow only).

The look of a documentation site themed with the Flexoki palette (an "inky" scheme for prose and code): warm paper
#FFFCF0, ink-black type, a ladder of warm greys for surfaces, borders and muted text, and eight accents in two shades
(600 for text, 400 for fills). On the paper sit light-grey rounded panels (#F2F0E5, radius 28, no border, no shadow)
with a heavy CJK title, a grey English tag and a mono index number. Inside them, diagrams drawn the way a small
Mermaid-compatible renderer draws them: boxes filled one step off their ground with a 2 px grey border (rect r 5,
round r 14, stadium, diamond, cylinder, circle), 2.4 px ink lines ending in small filled triangular heads, plain
semibold sans labels on a patch of ground colour, dashed lifelines and replies, pies with paper-coloured gaps, bar
charts on hairline grids, tables with a tinted header row. Accents only where they mean something; no texture, no
gradients, no shadows (one optional CSS-style shadow for a lifted card).

  shapes     signed-distance fields with 1 px analytic anti-aliasing (pixel centres at i + 0.5): rounded rectangles,
             discs, rings, capsules, rhombi, cylinders, pie sectors, polylines; arrowheads and other free polygons are
             rasterised 4x and box-filtered.
  lines      a polyline knows its arc length, so a line can be drawn on to any fraction p (the cut end keeps its round
             cap), dashed along its length, and trimmed under its arrowhead. `bezier`, `curve` (tangent-directed
             cubic) and `rounded` (an orthogonal route with filleted corners) make the polylines.
  groups     a node (fill, border, label) is composited as one group, so a node popping in at 40 % opacity fades as a
             whole (SVG <g opacity>), and its scale-in (0.85 -> 1) scales the label too.
  type       PingFang SC for CJK (the heavy weight is Semibold with a hairline of faux bold -- close to the black
             headings of the film), SF Pro for Latin (variable weight; big numbers tracked tight), SF Mono for index
             numbers and code; elsewhere Hiragino / Noto Sans CJK / Microsoft YaHei and Helvetica / DejaVu. Override
             with $INKPAINT_FONT_FLEXOKI_<CJK|HEAVY|LATIN|MONO>.
  layers     as in pastelui: named layers (premultiplied RGBA, cropped when closed) with a depth and a pose (offset,
             scale about an origin, opacity, left-to-right reveal). `layer(name, fresh=True)` empties a layer so it
             can be redrawn at the next progress value -- an edge drawing on, a number rolling, a pie sweeping, a bar
             growing -- which is how the draw-on animation is made. `stage()` composites the current poses.

    import sys; sys.path.insert(0, 'lib')
    from flexoki import FlexokiPaper, ORANGE4, GREEN4, curve
    fx = FlexokiPaper(1920, 1080, seed=1)
    fx.paper()
    fx.layer('head')
    fx.chip(120, 84, '图解')
    fx.heading(120, 170, '一张流程图', 'Flowchart')
    fx.layer('panel')
    box = fx.panel(120, 220, 900, 420, title='从想法到上线', tag='Flowchart', num='01')
    fx.layer('flow')
    a = fx.node(300, 430, 150, 56, 'Idea')
    b = fx.node(560, 430, 150, 100, 'Go?', shape='diamond')
    fx.edge([a.side('r'), b.side('l')], label='yes', label_fill=GREEN4)
    for p in (0.2, 0.6, 1.0):                         # draw it on, stage by stage
        fx.layer('e', fresh=True); fx.edge([b.side('r'), (820, 430)], p=p); fx.stage(f'e{p}')
    fx.save('out.jpg')
"""
import glob
import io
import os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, load_font

# ---------------------------------------------------------------- the Flexoki palette
PAPER = '#FFFCF0'
BASE50, BASE100, BASE150, BASE200 = '#F2F0E5', '#E6E4D9', '#DAD8CE', '#CECDC3'
BASE300, BASE500, BASE600 = '#B7B5AC', '#878580', '#6F6E69'
BASE800, BASE900, BASE950, BLACK = '#403E3C', '#282726', '#1C1B1A', '#100F0F'
# roles (the names the site's CSS uses): surface, ui borders, faint / muted text, ink
BG2, UI, UI2, UI3, TX3, TX2, TX1B, INK = BASE50, BASE100, BASE150, BASE200, BASE300, BASE500, BASE600, BLACK
RED, RED4 = '#AF3029', '#D14D41'
ORANGE, ORANGE4 = '#BC5215', '#DA702C'
YELLOW, YELLOW4 = '#AD8301', '#D0A215'
GREEN, GREEN4 = '#66800B', '#879A39'
CYAN, CYAN4 = '#24837B', '#3AA99F'
BLUE, BLUE4 = '#205EA6', '#4385BE'
PURPLE, PURPLE4 = '#5E409D', '#8B7EC8'
MAGENTA, MAGENTA4 = '#A02F6F', '#CE5D97'
ACCENTS = {'red': (RED, RED4), 'orange': (ORANGE, ORANGE4), 'yellow': (YELLOW, YELLOW4), 'green': (GREEN, GREEN4),
           'cyan': (CYAN, CYAN4), 'blue': (BLUE, BLUE4), 'purple': (PURPLE, PURPLE4), 'magenta': (MAGENTA, MAGENTA4)}
SERIES = [BLUE4, ORANGE4, GREEN4, PURPLE4, CYAN4, RED4, YELLOW4, MAGENTA4]   # chart series, in this order
THEMES = {  # what a diagram is drawn with, on light paper and on the dark (950) ground
    'light': dict(bg=PAPER, surface=BG2, border=UI3, line=INK, fg=INK, muted=TX1B, faint=TX3, track=UI, hair=UI2),
    'dark': dict(bg=BASE950, surface=BASE900, border=BASE800, line=UI2, fg=UI, muted=TX2, faint=BASE600,
                 track=BASE800, hair=BASE800),
}
PALETTE = [PAPER, BASE50, BASE100, BASE150, BASE200, BASE300, BASE500, BASE600, BASE800, BASE900, BASE950, BLACK,
           RED, RED4, ORANGE, ORANGE4, YELLOW, YELLOW4, GREEN, GREEN4, CYAN, CYAN4, BLUE, BLUE4, PURPLE, PURPLE4,
           MAGENTA, MAGENTA4]


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    """colour: '#rrggbb', an accent name ('orange' -> the 400 shade, 'orange6' -> the 600 shade) or rgb 0..1"""
    if isinstance(c, str):
        if c in ACCENTS: return hexc(ACCENTS[c][1])
        if c[:-1] in ACCENTS and c[-1] == '6': return hexc(ACCENTS[c[:-1]][0])
        return hexc(c)
    return np.asarray(c, np.float32)


def mix(a, b, t):
    """a colour between a and b (hex string out)"""
    v = _c(a) * (1 - t) + _c(b) * t
    return '#' + ''.join(f'{int(round(x * 255)):02x}' for x in np.clip(v, 0, 1))


# ---------------------------------------------------------------- distances (negative inside)
def sdf_rrect(u, v, hw, hh, r):
    r = max(0.0, min(r, hw, hh))
    qx, qy = np.abs(u) - (hw - r), np.abs(v) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sdf_rhombus(u, v, hw, hh):
    """exact distance to a rhombus with half-diagonals hw, hh"""
    px, py = np.abs(u), np.abs(v)
    bb = hw * hw + hh * hh
    h = np.clip(((hw - 2 * px) * hw - (hh - 2 * py) * hh) / bb, -1, 1)
    d = np.hypot(px - 0.5 * hw * (1 - h), py - 0.5 * hh * (1 + h))
    return d * np.sign(px * hh + py * hw - hw * hh)


def sdf_ellipse(u, v, rx, ry):
    """first-order distance to an ellipse (exact enough for 1 px anti-aliasing)"""
    g = np.hypot(u / rx, v / ry)
    grad = np.hypot(u / (rx * rx), v / (ry * ry)) + 1e-6
    return (g - 1) * g / grad


def sdf_segment(X, Y, a, b):
    ax, ay = float(a[0]), float(a[1]); bx, by = float(b[0]), float(b[1])
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy + 1e-9
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / l2, 0, 1)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy)), t


def sdf_polyline(X, Y, P):
    """-> (distance, arc length at the nearest point) to the polyline P (n, 2)"""
    shape = np.broadcast(X, Y).shape
    d = np.full(shape, 1e9, np.float32); s = np.zeros(shape, np.float32)
    acc = 0.0
    for a, b in zip(P[:-1], P[1:]):
        L = float(np.hypot(b[0] - a[0], b[1] - a[1]))
        e, t = sdf_segment(X, Y, a, b)
        m = e < d
        d = np.where(m, e, d); s = np.where(m, acc + t * L, s)
        acc += L
    return d, s


def _cov(d):
    return np.clip(0.5 - d, 0, 1).astype(np.float32)


def _clip01(x):
    return float(min(1.0, max(0.0, x)))


# ---------------------------------------------------------------- paths
def bezier(p0, p1, p2, p3, n=40):
    """cubic Bezier p0 -> p3 with control points p1, p2, sampled into n + 1 points"""
    t = np.linspace(0, 1, n + 1)[:, None]
    P = [np.asarray(p, np.float32) for p in (p0, p1, p2, p3)]
    return ((1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1] + 3 * (1 - t) * t * t * P[2] + t ** 3 * P[3]).astype(np.float32)


def curve(a, b, da=(1, 0), db=(1, 0), k=None, n=40):
    """the renderer's curved edge: leaves a along direction da, arrives at b along direction db (k: handle length,
    default 0.45 x the distance)"""
    a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
    k = 0.45 * float(np.hypot(*(b - a))) if k is None else k
    da = np.asarray(da, np.float32) / (np.hypot(*da) + 1e-9); db = np.asarray(db, np.float32) / (np.hypot(*db) + 1e-9)
    return bezier(a, a + da * k, b - db * k, b, n)


def rounded(pts, r=14.0, n=8):
    """an orthogonal (or any) route through pts with every inner corner filleted by radius r"""
    P = [np.asarray(p, np.float32) for p in pts]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, c, b = P[i - 1], P[i], P[i + 1]
        u = (a - c) / (np.hypot(*(a - c)) + 1e-9); w = (b - c) / (np.hypot(*(b - c)) + 1e-9)
        rr = min(r, np.hypot(*(a - c)) / 2, np.hypot(*(b - c)) / 2)
        p0, p1 = c + u * rr, c + w * rr
        out += list(bezier(p0, c + u * rr * 0.45, c + w * rr * 0.45, p1, n))
    out.append(P[-1])
    return np.array(out, np.float32)


def _length(P):
    return float(np.hypot(*np.diff(P, axis=0).T).sum()) if len(P) > 1 else 0.0


def _cut(P, L0, L1):
    """the part of polyline P between arc lengths L0 and L1"""
    seg = np.hypot(*np.diff(P, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    L1 = min(L1, cum[-1]); L0 = max(0.0, L0)
    if L1 <= L0: return P[:1]

    def at(L):
        i = int(np.clip(np.searchsorted(cum, L) - 1, 0, len(seg) - 1))
        t = (L - cum[i]) / (seg[i] + 1e-9)
        return P[i] + (P[i + 1] - P[i]) * t

    inner = [P[i] for i in range(len(P)) if L0 < cum[i] < L1]
    return np.array([at(L0)] + inner + [at(L1)], np.float32)


def _point_at(P, L):
    return _cut(P, 0, L)[-1]


# ---------------------------------------------------------------- fonts
_AD = '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
_CJK_FACES = [  # (glob, {weight: face index or file-name token}) -- first hit wins: macOS, Linux, Windows
    (_AD + 'PingFang.ttc', {'regular': 3, 'medium': 7, 'semibold': 11, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/PingFang.ttc', {'regular': 3, 'medium': 7, 'semibold': 11, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/Hiragino Sans GB.ttc', {'regular': 0, 'medium': 0, 'semibold': 2, 'bold': 2, 'heavy': 2}),
    ('/usr/share/fonts/**/NotoSansCJK*-{W}.tt[cf]', {'regular': 'Regular', 'medium': 'Medium', 'semibold': 'Bold',
                                                    'bold': 'Bold', 'heavy': 'Black'}),
    ('/usr/share/fonts/**/NotoSansSC-{W}.[ot]tf', {'regular': 'Regular', 'medium': 'Medium', 'semibold': 'Bold',
                                                   'bold': 'Bold', 'heavy': 'Black'}),
    ('C:/Windows/Fonts/msyh{W}.ttc', {'regular': '', 'medium': '', 'semibold': 'bd', 'bold': 'bd', 'heavy': 'bd'}),
]
_LATIN_W = {'regular': 400, 'medium': 510, 'semibold': 600, 'bold': 700, 'heavy': 800}
_MONO_W = {'regular': 400, 'medium': 500, 'semibold': 600, 'bold': 700, 'heavy': 800}
_FONTS = {}


def _find(pat):
    fs = sorted(glob.glob(pat, recursive=True))
    return fs[0] if fs else None


def _truetype(path, size, idx):
    for i in ([idx, 0] if idx else [0]):
        try:
            return ImageFont.truetype(path, size, index=i)
        except OSError:
            continue
    return None


def _cjk(weight, size):
    """-> (font, faux-bold stroke px)"""
    env = os.environ.get('INKPAINT_FONT_FLEXOKI_HEAVY' if weight == 'heavy' else 'INKPAINT_FONT_FLEXOKI_CJK')
    if env and os.path.exists(env):
        return ImageFont.truetype(env, size), 0
    for pat, faces in _CJK_FACES:
        tok = faces[weight]
        p = _find(pat.replace('{W}', tok)) if isinstance(tok, str) else _find(pat)
        if not p: continue
        f = _truetype(p, size, 2 if (isinstance(tok, str) and p.endswith('.ttc') and 'Noto' in p)
                      else (tok if isinstance(tok, int) else 0))
        if f:
            fake = size / 50 if (weight == 'heavy' and 'Black' not in p) else 0
            return f, fake
    return load_font('cjk_sans', size), (size / 40 if weight in ('bold', 'heavy') else 0)


def _latin(weight, size, mono=False):
    env = os.environ.get('INKPAINT_FONT_FLEXOKI_' + ('MONO' if mono else 'LATIN'))
    if env and os.path.exists(env):
        return ImageFont.truetype(env, size)
    p = '/System/Library/Fonts/SFNSMono.ttf' if mono else '/System/Library/Fonts/SFNS.ttf'
    if os.path.exists(p):
        try:
            f = ImageFont.truetype(p, size)
            if mono:
                w = float(np.clip(_MONO_W[weight], 294, 900)); f.set_variation_by_axes([w, w])
            else:
                f.set_variation_by_axes([100, float(np.clip(size * 0.75, 17, 96)), 400, _LATIN_W[weight]])
            return f
        except (OSError, ValueError):
            pass
    if mono:
        for q, i in [('/System/Library/Fonts/Menlo.ttc', 1 if weight in ('bold', 'heavy') else 0),
                     ('/usr/share/fonts/**/DejaVuSansMono*.ttf', 0), ('C:/Windows/Fonts/consola.ttf', 0)]:
            pp = _find(q)
            if pp:
                f = _truetype(pp, size, i)
                if f: return f
        return load_font('typewriter', size)
    if os.path.exists('/System/Library/Fonts/HelveticaNeue.ttc'):
        return ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', size,
                                  index={'regular': 0, 'medium': 10, 'semibold': 10, 'bold': 1, 'heavy': 1}[weight])
    return load_font('sans_bold' if weight in ('semibold', 'bold', 'heavy') else 'sans', size)


def _font(kind, weight, size):
    key = (kind, weight, int(size))
    if key not in _FONTS:
        _FONTS[key] = _cjk(weight, int(size)) if kind == 'cjk' else (_latin(weight, int(size), kind == 'mono'), 0)
    return _FONTS[key]


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


# ---------------------------------------------------------------- data holders
class Box:
    """a rectangle in canvas pixels"""

    def __init__(self, x0, y0, x1, y1, r=0.0):
        self.x0, self.y0, self.x1, self.y1, self.r = x0, y0, x1, y1, r
        self.w, self.h = x1 - x0, y1 - y0
        self.cx, self.cy = (x0 + x1) / 2, (y0 + y1) / 2

    def __iter__(self):
        return iter((self.x0, self.y0, self.x1, self.y1))


class Node(Box):
    """a diagram node: its box plus where edges attach"""

    def __init__(self, cx, cy, w, h, shape):
        super().__init__(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, 0)
        self.shape = shape

    def side(self, s, gap=0.0):
        """mid-point of a side ('l' 'r' 't' 'b'; for a diamond its vertices), pushed out by gap px"""
        dx, dy = {'l': (-1, 0), 'r': (1, 0), 't': (0, -1), 'b': (0, 1)}[s]
        return (self.cx + dx * (self.w / 2 + gap), self.cy + dy * (self.h / 2 + gap))

    def toward(self, x, y, gap=0.0):
        """where the ray from the centre toward (x, y) leaves the node (+ gap px)"""
        ux, uy = x - self.cx, y - self.cy
        n = np.hypot(ux, uy) + 1e-9; ux, uy = ux / n, uy / n
        hw, hh = self.w / 2, self.h / 2
        if self.shape == 'diamond':
            t = 1 / (abs(ux) / hw + abs(uy) / hh)
        elif self.shape == 'circle':
            t = hw
        else:
            t = min(hw / abs(ux) if abs(ux) > 1e-6 else 1e9, hh / abs(uy) if abs(uy) > 1e-6 else 1e9)
        return (self.cx + ux * (t + gap), self.cy + uy * (t + gap))


class Table:
    """geometry of a table: x, y, column widths, header height, row height, number of body rows"""

    def __init__(self, x, y, widths, head_h, row_h, n_rows, r):
        self.x, self.y, self.widths, self.head_h, self.row_h, self.n, self.r = x, y, list(widths), head_h, row_h, n_rows, r
        self.xs = [x + sum(widths[:i]) for i in range(len(widths) + 1)]
        self.box = Box(x, y, self.xs[-1], y + head_h + row_h * n_rows, r)

    def cell(self, i, j):
        """cell box: row i (-1 = the header), column j"""
        y0 = self.y if i < 0 else self.y + self.head_h + i * self.row_h
        return Box(self.xs[j], y0, self.xs[j + 1], y0 + (self.head_h if i < 0 else self.row_h))

    def col(self, j):
        return Box(self.xs[j], self.y, self.xs[j + 1], self.box.y1)


class Layer:
    def __init__(self, name, z, order, W, H):
        self.name, self.z, self.order = name, z, order
        self.rgb = np.zeros((H, W, 3), np.float32)     # premultiplied
        self.a = np.zeros((H, W), np.float32)
        self.x0 = self.y0 = 0
        self.open = True
        self.pose = dict(dx=0.0, dy=0.0, scale=1.0, alpha=1.0, reveal=1.0, origin=None, feather=14.0)


# ---------------------------------------------------------------- the canvas
class FlexokiPaper:
    THEMES = THEMES

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, theme='light'):
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages = keep_stages
        self.stages = []
        self.th = dict(THEMES[theme])
        self.base = np.ones((H, W, 3), np.float32) * hexc(self.th['bg'])
        self.ground = self.th['bg']           # what diagrams are drawn on (label patches, pie gaps, node fill)
        self.layers = {}
        self.cur = None
        self._clip = None
        g = np.random.default_rng(seed + 7).random((H, W)).astype(np.float32)
        self._grain = (g - 0.5) * (1.0 / 255)            # sub-level dither only

    # ------------------------------------------------------------ layers (as in pastelui)
    def layer(self, name, z=None, fresh=False):
        """start drawing into layer `name` (re-opens it if it exists; fresh=True empties it first, for redrawing
        a progress state). z: depth (default: creation order); lower z is further back"""
        self._close()
        if name in self.layers and not fresh:
            L = self.layers[name]
            full_rgb = np.zeros((self.H, self.W, 3), np.float32); full_a = np.zeros((self.H, self.W), np.float32)
            h, w = L.a.shape
            full_rgb[L.y0:L.y0 + h, L.x0:L.x0 + w] = L.rgb; full_a[L.y0:L.y0 + h, L.x0:L.x0 + w] = L.a
            L.rgb, L.a, L.x0, L.y0, L.open = full_rgb, full_a, 0, 0, True
            if z is not None: L.z = z
        elif name in self.layers:
            L = self.layers[name]
            L.rgb = np.zeros((self.H, self.W, 3), np.float32); L.a = np.zeros((self.H, self.W), np.float32)
            L.x0 = L.y0 = 0; L.open = True
            if z is not None: L.z = z
        else:
            n = len(self.layers)
            L = Layer(name, n if z is None else z, n, self.W, self.H)
            self.layers[name] = L
        self.cur = L
        return name

    def end(self):
        """stop drawing into the current layer (later drawing goes onto the paper)"""
        self._close()

    @staticmethod
    def _view(L):
        if not L.open: return L.rgb, L.a, L.x0, L.y0
        rows = np.nonzero(L.a.max(1) > 0.5 / 255)[0]
        cols = np.nonzero(L.a.max(0) > 0.5 / 255)[0]
        if not len(cols): return L.rgb[:1, :1], L.a[:1, :1] * 0, 0, 0
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        return L.rgb[y0:y1, x0:x1], L.a[y0:y1, x0:x1], int(x0), int(y0)

    def _close(self):
        L = self.cur
        self.cur = None
        if L is None or not L.open: return
        rgb, a, x0, y0 = self._view(L)
        L.rgb, L.a, L.x0, L.y0, L.open = rgb.copy(), a.copy(), x0, y0, False

    def pose(self, name, dx=0.0, dy=0.0, scale=1.0, alpha=1.0, reveal=1.0, origin=None, feather=14.0):
        """how layer `name` is shown: offset, scale about `origin` (default its centre), opacity, left-to-right
        reveal (0..1, soft edge `feather` px). pose(name) = as drawn"""
        self.layers[name].pose = dict(dx=dx, dy=dy, scale=scale, alpha=alpha, reveal=reveal, origin=origin,
                                      feather=feather)

    def show(self, *names, alpha=1.0):
        for n in names: self.layers[n].pose['alpha'] = alpha

    def hide(self, *names):
        for n in names: self.layers[n].pose['alpha'] = 0.0

    def bounds(self, name):
        rgb, a, x0, y0 = self._view(self.layers[name])
        return x0, y0, x0 + a.shape[1], y0 + a.shape[0]

    @contextmanager
    def clip(self, x0, y0, x1, y1, r=0.0):
        """everything drawn inside is clipped to this rounded rectangle"""
        old = self._clip
        self._clip = (x0, y0, x1, y1, r)
        try:
            yield
        finally:
            self._clip = old

    # ------------------------------------------------------------ low level
    def _grid(self, x0, y0, x1, y1):
        """clipped pixel box -> (slices, X (1, w), Y (h, 1)) with pixel centres at i + 0.5, or None"""
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1)) + 1), min(self.H, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None
        X = np.arange(x0, x1, dtype=np.float32)[None, :] + 0.5
        Y = np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5
        return (slice(y0, y1), slice(x0, x1)), X, Y

    def _over(self, sl, cov, col):
        """paint colour `col` (rgb or an (h, w, 3) array) with coverage `cov` over the current target"""
        cov = np.clip(cov, 0, 1).astype(np.float32)
        if self._clip is not None:
            cx0, cy0, cx1, cy1, cr = self._clip
            X = np.arange(sl[1].start, sl[1].stop, dtype=np.float32)[None, :] + 0.5
            Y = np.arange(sl[0].start, sl[0].stop, dtype=np.float32)[:, None] + 0.5
            cov = cov * _cov(sdf_rrect(X - (cx0 + cx1) / 2, Y - (cy0 + cy1) / 2, (cx1 - cx0) / 2, (cy1 - cy0) / 2, cr))
        col = col if (isinstance(col, np.ndarray) and col.ndim == 3) else _c(col)
        c3 = cov[..., None]
        if self.cur is None:
            self.base[sl] = self.base[sl] * (1 - c3) + col * c3
        else:
            L = self.cur
            L.rgb[sl] = L.rgb[sl] * (1 - c3) + col * c3
            L.a[sl] = L.a[sl] * (1 - cov) + cov

    def _group(self, sl, paints, alpha=1.0):
        """composite several (coverage, colour) paints into one group first, then lay the group down at `alpha`"""
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        rgb = np.zeros((h, w, 3), np.float32); a = np.zeros((h, w), np.float32)
        for cov, col in paints:
            if cov is None: continue
            cov = np.broadcast_to(np.clip(cov, 0, 1), (h, w)).astype(np.float32)
            rgb = rgb * (1 - cov[..., None]) + _c(col) * cov[..., None]
            a = a * (1 - cov) + cov
        self._over(sl, a * alpha, rgb / np.maximum(a, 1e-6)[..., None])

    # ------------------------------------------------------------ the page
    def paper(self, colour=None):
        """flat warm paper (#FFFCF0, or the theme's ground)"""
        colour = colour or self.th['bg']
        self.base[:] = _c(colour)
        self.ground = colour

    # ------------------------------------------------------------ shapes
    def rrect(self, x0, y0, x1, y1, r=0.0, fill=None, alpha=1.0, ring=0.0, inset=True):
        """rounded rectangle; ring=w draws only a w px line along the edge (inside if inset, else outside)"""
        fill = fill or self.th['surface']
        g = self._grid(x0 - ring - 2, y0 - ring - 2, x1 + ring + 2, y1 + ring + 2)
        if not g: return None
        sl, X, Y = g
        d = sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r)
        if ring:
            d = np.abs(d + ring / 2) - ring / 2 if inset else np.abs(d - ring / 2) - ring / 2
        self._over(sl, _cov(d) * alpha, fill)

    def circle(self, cx, cy, r, fill=INK, alpha=1.0, ring=0.0):
        """disc (or with ring=w a circular line w px wide, inside radius r)"""
        g = self._grid(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        if not g: return None
        sl, X, Y = g
        d = np.hypot(X - cx, Y - cy) - r
        if ring: d = np.abs(d + ring / 2) - ring / 2
        self._over(sl, _cov(d) * alpha, fill)

    def poly(self, pts, fill=INK, alpha=1.0, ss=4):
        """filled polygon, rasterised ss x and box-filtered"""
        P = np.asarray(pts, np.float32)
        x0, y0 = int(np.floor(P[:, 0].min())) - 1, int(np.floor(P[:, 1].min())) - 1
        x1, y1 = int(np.ceil(P[:, 0].max())) + 2, int(np.ceil(P[:, 1].max())) + 2
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P.tolist()], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        g = self._grid(x0, y0, x1 - 1, y1 - 1)
        if not g: return
        sl = g[0]
        m = m[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0]
        self._over(sl, m * alpha, fill)

    def line(self, pts, width=2.4, fill=None, alpha=1.0, p=1.0, dash=None, phase=0.0, cap='round'):
        """polyline with round caps and joins. p: draw it on to this fraction of its length (the cut end keeps
        its cap); dash=(on, off) px along the length (butt ends). Returns the drawn polyline"""
        fill = fill or self.th['line']
        P = np.asarray(pts, np.float32)
        if p < 1: P = _cut(P, 0, _length(P) * max(0.0, p))
        if p <= 0 or len(P) < 2: return P
        pad = width / 2 + 2
        g = self._grid(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if not g: return P
        sl, X, Y = g
        d, s = sdf_polyline(X, Y, P)
        cov = _cov(d - width / 2)
        if cap == 'butt':      # cut square at both ends: half-planes through the end points
            u0 = (P[1] - P[0]) / (np.hypot(*(P[1] - P[0])) + 1e-9)
            un = (P[-1] - P[-2]) / (np.hypot(*(P[-1] - P[-2])) + 1e-9)
            cov = cov * np.clip(0.5 + (X - P[0][0]) * u0[0] + (Y - P[0][1]) * u0[1], 0, 1) \
                      * np.clip(0.5 - (X - P[-1][0]) * un[0] - (Y - P[-1][1]) * un[1], 0, 1)
        if dash:
            on, off = dash
            sm = np.mod(s + phase, on + off)
            cov = cov * np.clip(0.5 + np.minimum(sm, on - sm), 0, 1)
        self._over(sl, cov * alpha, fill)
        return P

    def head(self, x, y, deg, fill=None, length=11.0, width=10.4, alpha=1.0):
        """small filled triangular arrowhead, tip at (x, y), pointing along `deg` (0 = right, 90 = down)"""
        fill = fill or self.th['line']
        a = np.deg2rad(deg); c, s = np.cos(a), np.sin(a)
        P = [(0, 0), (-length, -width / 2), (-length, width / 2)]
        self.poly([(x + px * c - py * s, y + px * s + py * c) for px, py in P], fill, alpha)

    def shadow(self, x0, y0, x1, y1, r=0.0, dx=0.0, dy=0.0, blur_px=0.0, spread=0.0, colour=BASE600, alpha=0.2):
        """CSS box-shadow of a rounded rectangle, painted only outside it (for one lifted card, if any)"""
        sig = blur_px / 2
        pad = 3 * sig + abs(spread) + 3
        g = self._grid(min(x0, x0 + dx) - pad, min(y0, y0 + dy) - pad, max(x1, x1 + dx) + pad, max(y1, y1 + dy) + pad)
        if not g: return
        sl, X, Y = g
        sx0, sy0, sx1, sy1 = x0 - spread + dx, y0 - spread + dy, x1 + spread + dx, y1 + spread + dy
        m = _cov(sdf_rrect(X - (sx0 + sx1) / 2, Y - (sy0 + sy1) / 2, (sx1 - sx0) / 2, (sy1 - sy0) / 2, max(0.0, r + spread)))
        own = _cov(sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r))
        if sig > 0.3: m = blur(m, sig)
        self._over(sl, m * (1 - own) * alpha, colour)

    # ------------------------------------------------------------ text
    def _glyphs(self, s, size, weight, spacing, family):
        out, x = [], 0.0
        runs = []
        for ch in s:
            k = _is_cjk(ch)
            if runs and runs[-1][1] == k: runs[-1][0] += ch
            else: runs.append([ch, k])
        for piece, k in runs:
            f, fake = _font('cjk' if k else ('mono' if family == 'mono' else 'latin'), weight, size)
            if spacing:
                for ch in piece:
                    out.append((f, ch, x, fake)); x += f.getlength(ch) + spacing
            else:
                out.append((f, piece, x, fake)); x += f.getlength(piece)
        return out, (x - spacing if (spacing and s) else x)

    def measure(self, s, size, weight='regular', spacing=0.0, family='sans'):
        """advance width of a string in px"""
        return self._glyphs(s, int(round(size)), weight, spacing, family)[1]

    def _text_mask(self, s, x, y, size, weight='regular', anchor='ls', spacing=0.0, family='sans'):
        """-> (coverage mask, left, top, width) of a string; anchor [l m r] + [s baseline, m middle of the CJK
        body, t top of the CJK body]"""
        size = int(round(size))
        gl, tw = self._glyphs(s, size, weight, spacing, family)
        x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        base = y + {'s': 0.0, 'm': 0.36 * size, 't': 0.86 * size}[anchor[1]]
        bx0, by0 = int(np.floor(x0)) - 6, int(np.floor(base - size * 1.25))
        bw, bh = int(tw) + 14, int(size * 1.65) + 8
        im = Image.new('L', (bw, bh), 0)
        dr = ImageDraw.Draw(im)
        for f, piece, off, fake in gl:
            try:
                dr.text((x0 - bx0 + off, base - by0), piece, font=f, fill=255, anchor='ls', stroke_width=fake,
                        stroke_fill=255)
            except (TypeError, ValueError):
                dr.text((x0 - bx0 + off, base - by0), piece, font=f, fill=255, anchor='ls',
                        stroke_width=int(round(fake)), stroke_fill=255)
        return np.asarray(im, np.float32) / 255, bx0, by0, tw

    def text(self, s, x, y, size, fill=None, weight='regular', anchor='ls', alpha=1.0, spacing=0.0, family='sans'):
        """text (CJK / Latin runs split automatically). weight: regular / medium / semibold / bold / heavy;
        family: sans / mono. anchor: [l m r] + [s baseline, m middle, t top]. Returns the width"""
        fill = fill or self.th['fg']
        m, bx0, by0, tw = self._text_mask(s, x, y, size, weight, anchor, spacing, family)
        g = self._grid(bx0, by0, bx0 + m.shape[1] - 1, by0 + m.shape[0] - 1)
        if not g: return tw
        sl = g[0]
        m = m[sl[0].start - by0:sl[0].stop - by0, sl[1].start - bx0:sl[1].stop - bx0]
        self._over(sl, m * alpha, fill)
        return tw

    @staticmethod
    def _paste(mask, bx0, by0, sl):
        """a text mask placed into the grid `sl` (cropped / padded)"""
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        out = np.zeros((h, w), np.float32)
        ys, xs = by0 - sl[0].start, bx0 - sl[1].start
        y0, x0 = max(0, ys), max(0, xs)
        y1, x1 = min(h, ys + mask.shape[0]), min(w, xs + mask.shape[1])
        if y1 > y0 and x1 > x0:
            out[y0:y1, x0:x1] = mask[y0 - ys:y1 - ys, x0 - xs:x1 - xs]
        return out

    # ------------------------------------------------------------ page parts
    def heading(self, x, base, zh, en=None, size=62, en_size=None, fill=None, en_fill=TX2, gap=None, alpha=1.0):
        """a heavy CJK heading with a grey English tag on the same baseline. Returns the right edge"""
        w = self.text(zh, x, base, size, fill, 'heavy', alpha=alpha)
        if en:
            es = en_size or round(size * 0.5)
            w += (gap if gap is not None else size * 0.36)
            w += self.text(en, x + w, base, es, en_fill, 'semibold', alpha=alpha)
        return x + w

    def number(self, x, base, s, size=104, fill=None, anchor='ls', track=-0.03, alpha=1.0, weight='heavy'):
        """a big number (Latin heavy, tracked tight): a counter, a timer, a measurement. Returns the width"""
        return self.text(s, x, base, size, fill, weight, anchor, alpha, spacing=track * size)

    def chip(self, x, cy, text, fg=None, bg=None, size=24, anchor='l', weight='bold', glyph=None, alpha=1.0):
        """capsule label: ink with paper text by default (a section tag), or any fg / bg. glyph 'check' / 'dot'
        puts a mark in front. Returns its Box"""
        fg = fg or self.th['bg']; bg = bg or self.th['fg']
        tw = self.measure(text, size, weight)
        gw = size * 0.95 if glyph else 0
        px, py = size * 0.6, size * 0.28
        h = size * 1.36 + 2 * py
        w = tw + gw + 2 * px
        x0 = x - w * {'l': 0, 'm': 0.5, 'r': 1}[anchor]
        self.rrect(x0, cy - h / 2, x0 + w, cy + h / 2, h / 2, bg, alpha)
        tx = x0 + px
        if glyph == 'dot':
            self.circle(tx + size * 0.28, cy, size * 0.22, fg, alpha)
        elif glyph == 'check':
            self.circle(tx + size * 0.34, cy, size * 0.36, fg, alpha, ring=size * 0.08)
            self.line([(tx + size * 0.17, cy + size * 0.01), (tx + size * 0.3, cy + size * 0.14),
                       (tx + size * 0.52, cy - size * 0.12)], size * 0.1, fg, alpha)
        self.text(text, tx + gw, cy, size, fg, weight, 'lm', alpha)
        return Box(x0, cy - h / 2, x0 + w, cy + h / 2, h / 2)

    def step(self, x, cy, label, lit=1.0, size=26, accent=ORANGE4, mute=False):
        """a step chip: dim (ui ground, faint text, empty circle) -> lit (accent ground, paper text, a check drawn
        on as lit goes 0 -> 1). mute=True: the neutral variant (ui2 ground, a minus). Returns the right edge"""
        on = _clip01(lit)
        bg = (UI2 if mute else accent) if on > 0.5 else UI
        fg = (INK if mute else PAPER) if on > 0.5 else TX3
        tw = self.measure(label, size, 'bold')
        h = size * 1.36 + size * 0.52
        cs = size * 0.9
        w = size * 0.42 + cs + 10 + tw + size * 0.62
        self.rrect(x, cy - h / 2, x + w, cy + h / 2, h / 2, bg)
        ccx = x + size * 0.42 + cs / 2
        self.circle(ccx, cy, cs * 10.5 / 24 + cs * 1.1 / 24, fg, ring=cs * 2.2 / 24)
        k = cs / 24
        if mute:
            self.line([(ccx - 4.5 * k, cy), (ccx + 4.5 * k, cy)], 2.6 * k, fg, on)
        elif on > 0:
            self.line([(ccx - 5 * k, cy + 0.4 * k), (ccx - 1.4 * k, cy + 4 * k), (ccx + 5.4 * k, cy - 3.4 * k)],
                      2.6 * k, fg, p=on)
        self.text(label, ccx + cs / 2 + 10, cy, size, fg, 'bold', 'lm')
        return x + w

    def panel(self, x, y, w, h, r=28, tone='surface', title=None, tag=None, num=None, title_size=34, pad=32,
              alpha=1.0):
        """a rounded panel: tone 'surface' (#F2F0E5, no border), 'paper' (paper with a 2 px ui2 border) or 'dark'
        (950). Optional header: heavy CJK title, grey English tag, mono index number at the top right.
        Sets the ground for what is drawn next. Returns a Box with .inner (the content area under the header)"""
        fill = {'surface': BG2, 'paper': PAPER, 'dark': BASE950}[tone]
        if tone == 'paper':
            self.rrect(x, y, x + w, y + h, r, UI2, alpha)
            self.rrect(x + 2, y + 2, x + w - 2, y + h - 2, r - 2, fill, alpha)
        else:
            self.rrect(x, y, x + w, y + h, r, fill, alpha)
        self.ground = fill
        fg = UI if tone == 'dark' else INK
        top = y
        if title:
            base = y + pad + title_size * 0.86
            tx = self.text(title, x + pad, base, title_size, fg, 'heavy', alpha=alpha)
            if tag:
                self.text(tag, x + pad + tx + title_size * 0.4, base, round(title_size * 0.68), TX2, 'semibold',
                          alpha=alpha)
            if num:
                self.text(num, x + w - pad + 2, base - 2, round(title_size * 0.66), TX3, 'regular', 'rs', alpha,
                          family='mono')
            top = base + title_size * 0.5
        b = Box(x, y, x + w, y + h, r)
        b.inner = Box(x + pad, top, x + w - pad, y + h - pad * 0.8)
        b.fill = fill
        return b

    def focus(self, box, colour=ORANGE4, width=4.0, alpha=1.0, r=None, out=0.0):
        """the focus ring: an inset accent line along a box's rounded edge (out > 0 pushes it outside)"""
        x0, y0, x1, y1 = box
        rr = (box.r if r is None else r) + out
        self.rrect(x0 - out, y0 - out, x1 + out, y1 + out, rr, colour, alpha, ring=width)

    def meter(self, x0, x1, cy, frac, colour=ORANGE4, h=22, track=None, min_w=None):
        """a capsule track (ui) with a filled part (a size, a share, a range on a common scale)"""
        self.rrect(x0, cy - h / 2, x1, cy + h / 2, h / 2, track or self.th['track'])
        if frac > 0:
            self.rrect(x0, cy - h / 2, x0 + max(min_w or h, (x1 - x0) * frac), cy + h / 2, h / 2, colour)

    def window(self, x, y, w, h, r=22, bar=34, fill=None):
        """the screen a diagram is shown in: paper body, 3 px ui3 border, a surface title bar with three grey
        dots. Returns a Box with .body (the area under the bar)"""
        fill = fill or self.th['bg']
        self.rrect(x, y, x + w, y + h, r, UI3)
        self.rrect(x + 3, y + 3, x + w - 3, y + h - 3, r - 3, fill)
        with self.clip(x + 3, y + 3, x + w - 3, y + h - 3, r - 3):
            self.rrect(x, y, x + w, y + 3 + bar, 0, BG2)
            self.rrect(x, y + 3 + bar - 2, x + w, y + 3 + bar, 0, UI2)
        for i in range(3):
            self.circle(x + 3 + 18.5 + i * 20, y + 3 + bar / 2, 5.5, UI3)
        b = Box(x, y, x + w, y + h, r)
        b.body = Box(x + 3, y + 3 + bar, x + w - 3, y + h - 3)
        self.ground = fill
        return b

    def dashed_rect(self, x0, y0, x1, y1, r=16, colour=ORANGE4, width=3.0, dash=(10, 8), alpha=1.0):
        """a dashed rounded rectangle (a container boundary, 'element')"""
        k = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        pts = rounded([(x0 + k, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0), (x0 + k + 0.01, y0)], k, 10)
        self.line(pts, width, colour, alpha, dash=dash)

    def dimension(self, x0, x1, y, label, colour=ORANGE4, size=28, tick=52, width=3.0):
        """a width dimension: a line between two dashed end ticks, the label on a patch of ground in the middle"""
        self.line([(x0, y), (x1, y)], width, colour, cap='butt')
        for xx in (x0, x1):
            self.line([(xx, y - 14), (xx, y + tick)], width, colour, dash=(8, 6), cap='butt')
        tw = self.measure(label, size, 'heavy')
        self.rrect((x0 + x1) / 2 - tw / 2 - 16, y - size * 0.7, (x0 + x1) / 2 + tw / 2 + 16, y + size * 0.7, 4,
                   self.ground)
        self.text(label, (x0 + x1) / 2, y, size, colour, 'heavy', 'mm')

    def code(self, x, base, tokens, size=28, mark=None, mark_colour=ORANGE4):
        """one line of code in SF Mono from (text, colour) tokens; mark = index of a token to sit on a tinted
        highlight. Returns the right edge"""
        cx = x
        for i, (s, col) in enumerate(tokens):
            w = self.measure(s, size, 'regular', family='mono')
            if mark == i:
                self.rrect(cx - 4, base - size * 0.95, cx + w + 4, base + size * 0.32, 5, mark_colour, 0.2)
            self.text(s, cx, base, size, col, 'regular', 'ls', family='mono')
            cx += w
        return cx

    # ------------------------------------------------------------ the renderer: nodes and edges
    def _node_fill(self):
        """a node is filled one step off its ground: surface on paper, paper on a surface panel"""
        return self.th['bg'] if _c(self.ground).tolist() == _c(self.th['surface']).tolist() else self.th['surface']

    def node(self, cx, cy, w, h, label='', shape='rect', size=22, p=1.0, fill=None, stroke=None, sw=2.0, fg=None,
             weight='semibold', lh=None, r=None):
        """a diagram node centred at (cx, cy), w x h its full box (a diamond's diagonals). shape: rect (r 5), round
        (r 14), stadium, diamond, cyl, circle. label: a string ('\\n' for more lines). p: pop-in 0..1 (scale
        0.85 -> 1 and fade, as one group). Returns a Node (side(), toward() for edges)"""
        n = Node(cx, cy, w, h, shape)
        if p <= 0.001: return n
        th = self.th
        fill = fill or self._node_fill()
        stroke = stroke or th['border']
        fg = fg or th['fg']
        s = 0.85 + 0.15 * _clip01(p)
        al = min(1.0, 1.6 * p)
        W_, H_ = w * s, h * s
        pad = sw + 3
        g = self._grid(cx - W_ / 2 - pad, cy - H_ / 2 - pad, cx + W_ / 2 + pad, cy + H_ / 2 + pad)
        if not g: return n
        sl, X, Y = g
        u, v = X - cx, Y - cy
        rim = None
        if shape == 'diamond':
            d = sdf_rhombus(u, v, W_ / 2, H_ / 2)
        elif shape == 'circle':
            d = np.hypot(u, v) - min(W_, H_) / 2
        elif shape == 'cyl':
            ry = min(H_ * 0.16, 11 * s)
            body = sdf_rrect(u, v, W_ / 2, H_ / 2 - ry, 0)
            top = sdf_ellipse(u, v + H_ / 2 - ry, W_ / 2, ry)
            bot = sdf_ellipse(u, v - H_ / 2 + ry, W_ / 2, ry)
            d = np.minimum(np.minimum(body, top), bot)
            rim = _cov(np.abs(top) - sw * s / 2)
        else:
            rr = {'rect': 5, 'round': 14, 'stadium': H_ / 2}.get(shape, 5) if r is None else r * s
            d = sdf_rrect(u, v, W_ / 2, H_ / 2, rr)
        paints = [(_cov(d), fill), (_cov(np.abs(d) - sw * s / 2), stroke), (rim, stroke)]
        lines = label.split('\n') if label else []
        if lines:
            fs = size * s
            L = (lh or size * 1.28) * s
            y0 = cy - (len(lines) - 1) * L / 2 + (4 * s if shape == 'cyl' else 0)
            for i, t in enumerate(lines):
                m, bx0, by0, _ = self._text_mask(t, cx, y0 + i * L, fs, weight, 'mm')
                paints.append((self._paste(m, bx0, by0, sl), fg))
        self._group(sl, paints, al)
        return n

    def edge(self, pts, p=1.0, head=True, dash=None, width=2.4, colour=None, head_len=11.0, head_w=10.4,
             label=None, label_t=0.5, label_size=19, label_fill=None, label_bg=None, label_weight='semibold'):
        """an edge along the polyline pts (use curve() / rounded() / bezier() for bends), ending in a small
        filled triangular head whose tip is the last point (the line stops under it). p: drawn on to this
        fraction (the head lands at the end). dash=(on, off) for dotted links and replies. label: drawn on a patch
        of ground at label_t along the edge, once the line has passed it. Returns the full polyline"""
        colour = colour or self.th['line']
        P = np.asarray(pts, np.float32)
        L = _length(P)
        if L < 1 or p <= 0: return P
        trim = head_len * 0.7 if head else 0.0
        self.line(_cut(P, 0, min(L * p, L - trim)), width, colour, dash=dash, cap='round' if not dash else 'butt')
        if head and p > 0.94:
            tail = _point_at(P, max(0.0, L - head_len))
            ang = np.degrees(np.arctan2(P[-1][1] - tail[1], P[-1][0] - tail[0]))
            self.head(P[-1][0], P[-1][1], ang, colour, head_len, head_w, alpha=_clip01((p - 0.94) / 0.06))
        if label and p > label_t:
            a = _clip01((p - label_t) / 0.12)
            lx, ly = _point_at(P, L * label_t)
            tw = self.measure(label, label_size, label_weight)
            self.rrect(lx - tw / 2 - 7, ly - label_size * 0.72, lx + tw / 2 + 7, ly + label_size * 0.72, 5,
                       label_bg or self.ground, a)
            self.text(label, lx, ly, label_size, label_fill or self.th['fg'], label_weight, 'mm', a)
        return P

    # ------------------------------------------------------------ sequence diagrams
    def lifeline(self, x, y0, y1, p=1.0, colour=None, width=2.0, dash=(6, 6)):
        """a dashed lifeline from y0 down to y1 (drawn on with p)"""
        self.line([(x, y0), (x, y1)], width, colour or self.th['border'], p=p, dash=dash, cap='butt')

    def activation(self, x, y0, y1, w=14, p=1.0):
        """an activation bar on a lifeline (grows down with p)"""
        if p <= 0: return
        y1 = y0 + (y1 - y0) * _clip01(p)
        self.rrect(x - w / 2, y0, x + w / 2, y1, 0, self.th['border'])
        self.rrect(x - w / 2 + 2, y0 + 2, x + w / 2 - 2, y1 - 2, 0, self.th['track'])

    def message(self, x0, x1, y, label=None, p=1.0, reply=False, size=19, label_fill=None, gap=10, width=2.2):
        """a message arrow from lifeline x0 to x1 at height y (a dashed reply if reply), its label centred above"""
        self.edge([(x0, y), (x1, y)], p, dash=(7, 6) if reply else None, width=width)
        if label and p > 0.3:
            self.text(label, (x0 + x1) / 2, y - gap, size, label_fill or self.th['muted'], 'medium', 'ms',
                      _clip01((p - 0.3) / 0.4))

    def note(self, x0, y0, x1, y1, text, size=18, fill=None, stroke=None, colour=None, p=1.0):
        """a note box (yellow-tinted surface, grey border) with centred text; p pops it in"""
        if p <= 0: return
        al = min(1.0, 1.6 * p)
        self.rrect(x0, y0, x1, y1, 4, stroke or UI3, al)
        self.rrect(x0 + 2, y0 + 2, x1 - 2, y1 - 2, 3, fill or mix(PAPER, YELLOW4, 0.16), al)
        self.text(text, (x0 + x1) / 2, (y0 + y1) / 2, size, colour or self.th['fg'], 'medium', 'mm', al)

    # ------------------------------------------------------------ charts
    def pie(self, cx, cy, r, values, colours=None, sweep=1.0, gap=3.0, gap_colour=None, labels=None,
            label_size=20, label_fill=PAPER, label_r=0.62):
        """a pie, slices clockwise from twelve o'clock, separated by gap px of ground colour (paper by default).
        sweep 0..1 draws it on clockwise. labels: one string per slice (e.g. percentages), shown once swept"""
        colours = colours or SERIES
        v = np.asarray(values, np.float32); fr = v / v.sum()
        edges = np.concatenate([[0], np.cumsum(fr)]) * 2 * np.pi
        A = 2 * np.pi * _clip01(sweep)
        if A <= 1e-3: return
        g = self._grid(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        sl, X, Y = g
        u, v_ = X - cx, Y - cy
        th = np.mod(np.arctan2(u, -v_), 2 * np.pi)
        disc = _cov(np.hypot(u, v_) - r)
        if A < 2 * np.pi - 1e-3:   # the swept sector, with anti-aliased straight edges
            def ray(a):
                return sdf_segment(X, Y, (cx, cy), (cx + (r + 3) * np.sin(a), cy - (r + 3) * np.cos(a)))[0]
            inside = th < A
            dr = np.minimum(ray(0.0), ray(A))
            sect = np.where(inside, np.clip(0.5 + dr, 0, 1), np.clip(0.5 - dr, 0, 1))
            disc = disc * sect
        idx = np.clip(np.searchsorted(edges, th, side='right') - 1, 0, len(fr) - 1)
        cols = np.stack([_c(colours[i % len(colours)]) for i in range(len(fr))])
        self._over(sl, disc, cols[idx])
        gc = gap_colour or self.ground
        if gap > 0:
            for a in list(edges[:-1]) + ([A] if A < 2 * np.pi - 1e-3 else []):
                if a > A + 1e-4: continue
                self.line([(cx, cy), (cx + (r + 2) * np.sin(a), cy - (r + 2) * np.cos(a))], gap, gc, cap='butt')
        if labels:
            for i, t in enumerate(labels):
                if not t: continue
                a = (edges[i] + edges[i + 1]) / 2
                al = _clip01((A - edges[i + 1]) / 0.35 + 1)
                if al <= 0: continue
                self.text(t, cx + r * label_r * np.sin(a), cy - r * label_r * np.cos(a), label_size, label_fill,
                          'bold', 'mm', al)

    def legend(self, x, y, items, size=21, pitch=44, swatch=22, value_x=None, alpha=1.0, value_family='sans'):
        """legend rows from (colour, label[, value]) at (x, y = middle of the first row); values right-aligned at
        value_x. alpha: one number or one per row"""
        als = alpha if isinstance(alpha, (list, tuple)) else [alpha] * len(items)
        for i, it in enumerate(items):
            col, lab = it[0], it[1]
            a = als[i]
            if a <= 0: continue
            cy = y + i * pitch
            self.rrect(x, cy - swatch / 2, x + swatch, cy + swatch / 2, 4, col, a)
            self.text(lab, x + swatch + 12, cy, size, self.th['fg'], 'semibold', 'lm', a)
            if len(it) > 2 and value_x is not None:
                self.text(it[2], value_x, cy, size - 1, self.th['muted'], 'regular', 'rm', a, family=value_family)

    def bars(self, x0, y0, x1, y1, values, labels=None, colours=None, vmax=None, ticks=None, tick_fmt=str, p=1.0,
             value_fmt=None, bar_w=0.56, size=20, r=5, value_colours=None):
        """a bar chart in the plot box (x0, y0)-(x1, y1): hairline grid at `ticks` with mono labels left of x0,
        a ui3 baseline, bars (round top, square foot) growing with p (one number or one per bar), the value rolling
        above each bar (value_fmt(v)), category labels under the baseline. Returns the bar Boxes"""
        n = len(values)
        colours = colours or [BLUE4] * n
        ps = p if isinstance(p, (list, tuple)) else [p] * n
        vmax = vmax or max(values) * 1.15
        sy = lambda val: y1 - (y1 - y0) * val / vmax
        for t in (ticks or []):
            yy = sy(t)
            if t > 0: self.line([(x0, yy), (x1, yy)], 2, self.th['track'], cap='butt')
            self.text(tick_fmt(t), x0 - 12, yy, size - 3, self.th['faint'], 'regular', 'rm', family='mono')
        self.line([(x0, y1), (x1, y1)], 2, self.th['border'], cap='butt')
        pitch = (x1 - x0) / n
        boxes = []
        for i, val in enumerate(values):
            cxb = x0 + pitch * (i + 0.5)
            bw = pitch * bar_w
            q = _clip01(ps[i])
            top = sy(val * q)
            boxes.append(Box(cxb - bw / 2, sy(val), cxb + bw / 2, y1))
            if q > 0 and y1 - top > 0.5:
                rr = min(r, (y1 - top) / 2)
                self.rrect(cxb - bw / 2, top, cxb + bw / 2, y1 - 1, rr, colours[i % len(colours)])
                self.rrect(cxb - bw / 2, max(top + rr, y1 - 1 - rr), cxb + bw / 2, y1 - 1, 0, colours[i % len(colours)])
            if value_fmt and q > 0:
                vc = (value_colours or [self.th['fg']] * n)[i]
                self.text(value_fmt(val * q), cxb, top - 12, size, vc, 'semibold', 'ms', min(1.0, 2 * q))
            if labels:
                self.text(labels[i], cxb, y1 + 14 + size * 0.86, size, self.th['muted'], 'medium', 'ms')
        return boxes

    def table(self, x, y, widths, n_rows, row_h=52, head_h=None, header=None, size=21, r=12, fill=None,
              head_fill=None, border=None, line=None, dots=None, head_colour=None, align=None):
        """a renderer table: a rounded frame (1.5 px border) on paper, a tinted header row with bold labels
        (optional accent dots in front), hairlines between rows. Body rows are drawn with table_row(), so they
        can live in their own layers. Returns a Table (cell(i, j), col(j), box)"""
        head_h = head_h or row_h
        t = Table(x, y, widths, head_h, row_h, n_rows, r)
        x1, y1 = t.box.x1, t.box.y1
        self.rrect(x, y, x1, y1, r, border or self.th['border'])
        self.rrect(x + 1.5, y + 1.5, x1 - 1.5, y1 - 1.5, r - 1.5, fill or self.th['bg'])
        with self.clip(x + 1.5, y + 1.5, x1 - 1.5, y1 - 1.5, r - 1.5):
            self.rrect(x, y, x1, y + head_h, 0, head_fill or self.th['track'])
            self.rrect(x, y + head_h - 1.5, x1, y + head_h, 0, border or self.th['border'])
            for i in range(1, n_rows):
                yy = y + head_h + i * row_h
                self.rrect(x + 1.5, yy - 0.75, x1 - 1.5, yy + 0.75, 0, line or self.th['hair'])
        if header:
            for j, s in enumerate(header):
                if not s: continue
                c = t.cell(-1, j)
                a = (align or ['l'] + ['m'] * (len(widths) - 1))[j]
                tx = c.x0 + 18 if a == 'l' else c.cx
                if dots and dots[j]:
                    tw = self.measure(s, size, 'bold')
                    dx = (tx - tw / 2 - 9) if a == 'm' else tx + 4
                    self.circle(dx, c.cy, 5.5, dots[j])
                    tx += 7 if a == 'm' else 16
                self.text(s, tx, c.cy, size, head_colour or self.th['fg'], 'bold', a + 'm')
        return t

    def table_row(self, t, i, cells, colours=None, weights=None, size=21, align=None, alpha=1.0):
        """the contents of body row i: first column muted (row names), the rest ink; colours / weights per cell"""
        for j, s in enumerate(cells):
            if not s: continue
            c = t.cell(i, j)
            a = (align or ['l'] + ['m'] * (len(cells) - 1))[j]
            col = (colours[j] if colours and colours[j] else (self.th['muted'] if j == 0 else self.th['fg']))
            wt = (weights[j] if weights and weights[j] else ('semibold' if j == 0 else 'medium'))
            self.text(s, c.x0 + 18 if a == 'l' else c.cx, c.cy, size, col, wt, a + 'm', alpha)

    # ------------------------------------------------------------ compositing
    def _posed(self, L):
        p = L.pose
        rgb, a, lx0, ly0 = self._view(L)
        h, w = a.shape
        x0, y0 = float(lx0), float(ly0)
        s = p['scale']
        if abs(s - 1) > 1e-4:
            ox, oy = p['origin'] or (lx0 + w / 2, ly0 + h / 2)
            nw, nh = max(1, int(round(w * s))), max(1, int(round(h * s)))
            rs = lambda ch: np.asarray(Image.fromarray(np.ascontiguousarray(ch), 'F').resize((nw, nh), Image.BILINEAR), np.float32)
            rgb = np.stack([rs(rgb[..., k]) for k in range(3)], -1)
            a = rs(a)
            x0, y0 = ox + (x0 - ox) * s, oy + (y0 - oy) * s
            w, h = nw, nh
        if p['reveal'] < 1:
            cut = w * p['reveal']
            xs = np.arange(w, dtype=np.float32)
            m = np.clip((cut - xs) / max(p['feather'], 1) + 0.5, 0, 1) if p['reveal'] > 0 else np.zeros(w, np.float32)
            rgb = rgb * m[None, :, None]; a = a * m[None, :]
        return rgb, a, int(round(x0 + p['dx'])), int(round(y0 + p['dy']))

    def render(self):
        """composite the paper and every layer under its current pose -> float RGB"""
        out = self.base.copy()
        for L in sorted(self.layers.values(), key=lambda q: (q.z, q.order)):
            al = L.pose['alpha']
            if al <= 0: continue
            rgb, a, x0, y0 = self._posed(L)
            h, w = a.shape
            X0, Y0 = max(0, x0), max(0, y0)
            X1, Y1 = min(self.W, x0 + w), min(self.H, y0 + h)
            if X1 <= X0 or Y1 <= Y0: continue
            cr = rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]; ca = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
            out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - ca[..., None] * al) + cr * al
        return out

    def composite(self):
        I = self.render() + self._grain[..., None]
        return Image.fromarray((np.clip(I, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        """snapshot the current poses (kept PNG-compressed in memory)"""
        if self.keep_stages:
            buf = io.BytesIO()
            self.composite().save(buf, 'PNG', compress_level=1)
            self.stages.append((name, buf.getvalue()))

    def save(self, path, stages_dir=None, quality=88):
        self._close()
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, png) in enumerate(self.stages):
                with open(f'{stages_dir}/{i:03d}_{name}.png', 'wb') as fh:
                    fh.write(png)
            img.save(f'{stages_dir}/{len(self.stages):03d}_final.png')
        return img
