"""canvasboard — 白板卡片 / Canvas Board: a dark, dotted, infinite whiteboard in a note app's window (numpy + Pillow only).

The look of a dark note-taking app's canvas view, the way a product film shows it: a dark page with a faint violet glow,
the app window (tab bar with the traffic lights and a `.canvas` tab, a ribbon of line icons on the left), and in it a
board of grey dots that pans and zooms with a camera. On the board: group frames with their labels floating above,
cards (dark, rounded, 2 px borders in the card colours -- red, orange, yellow, green, cyan, purple -- with a faint tint
of that colour), curved edges with arrowheads and labels, Markdown inside the cards (headings, body, ==highlights==,
`inline code`, task lists that tick, quotes with a violet bar, tag pills, colour chips), image cards with their file
name above them, a sketch drawn with hand-drawn strokes, and the zoom buttons in the top-right corner. One accent: violet.

  retained    nothing is rasterised when you call the drawing methods: every shape is recorded, in board (world)
              coordinates, into a named node (a group, a card, an edge ...). `render()` draws every node through the
              camera, so the board can be shown at any pan and zoom with crisp edges and type -- a real canvas.
  camera      `camera(x, y, z)`: the board point at the centre of the pane, and the zoom. The dot grid lives on the
              board (it moves and scales with the camera); the window chrome and the zoom buttons do not.
  shapes      rounded rectangles, discs, rings and strokes are signed-distance fields with 1 px analytic anti-aliasing
              (pixel centres at i + 0.5); polygons (arrowheads, the pointer) are rasterised 4x and box-filtered. Strokes
              are measured per segment, so a long curved edge or a sketch with hundreds of segments stays cheap.
              Shadows follow CSS box-shadow (offset, blur radius = 2 sigma, spread, colour, opacity; outside only).
  poses       each node has a pose -- offset, scale about its centre, opacity -- and named progress values (vars)
              that its shapes read: an edge draws on with `p`, a task ticks with its key, a highlight sweeps, a sketch
              is drawn stroke by stroke. A shape takes `var='name'` or `var=('name', a, b)` (its own 0..1 progress is
              the var mapped from a..b), and `mode` says what that progress does: fade / draw / reveal / pop.
  type        PingFang SC (CJK) + SF Pro (Latin, variable weight) + SF Mono, split into runs automatically; a 'hand'
              family (Hannotate SC, falling back to PingFang) for sketch notes; float sizes, so type zooms smoothly.
              Elsewhere Noto Sans CJK / Microsoft YaHei and the core fonts.
              Override with $INKPAINT_FONT_CANVASBOARD_<CJK|BOLD|LATIN|MONO|HAND>.

    import sys; sys.path.insert(0, 'lib')
    from canvasboard import CanvasBoard, ACCENT
    cb = CanvasBoard(1920, 1080, seed=1, tab='计划.canvas')
    cb.group('g', 0, 0, 700, 600, '第一周')
    a = cb.card('a', 30, 40, 640, 240, colour='purple')
    a.h1('计划'); a.p('先做 ==最重要的== 一件事'); a.task('列清单', key='t0')
    b = cb.card('b', 900, 80, 520, 200)
    b.h2('然后'); b.p('`v2` 上线')
    cb.edge('e', ('a', 'r'), ('b', 'l'), colour=ACCENT, label='下周')
    cb.camera(*cb.fit(-40, -80, 1460, 640))
    cb.pose('b', dy=-60, scale=1.05, alpha=0); cb.set('e', p=0); cb.stage('before')
    cb.pose('b'); cb.set('e', p=1); cb.save('out.jpg')
"""
import glob
import io
import os
import re
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, load_font

# ---------------------------------------------------------------- palette (dark note app, one violet accent)
PAGE = '#161616'                                   # the page behind the window
BG, BG2, BG3, SIDE = '#1e1e1e', '#262626', '#2e2e2e', '#202020'
BORDER, BORDER2 = '#363636', '#444444'
TEXT, BRIGHT, MUTED, FAINT = '#dadada', '#f2f2f2', '#a3a3a3', '#6b6b6b'
ACCENT, ACCENT2 = '#8a5cf5', '#a88bfa'
BOARD, DOT, EDGE = '#1c1c1c', '#3a3a3a', '#7d7d7d'
GROUP_LINE = '#3d3d3d'
CODE_BG, CODE_FG = '#2e2e2e', '#e06c75'
DONE = '#7c7c7c'                                   # a ticked task's text and strike
WHITE = '#ffffff'
CARD_COLOURS = {'red': '#fb464c', 'orange': '#e9973f', 'yellow': '#e0de71', 'green': '#44cf6e', 'cyan': '#53dfdd',
                'purple': '#a882ff', 'accent': ACCENT}
LIGHTS = ('#ff5f57', '#febc2e', '#28c840')

# line icons on a 24-unit grid: ('p', points[, closed]) polyline, ('c', cx, cy, r) circle, ('a', cx, cy, r, a0, a1) arc
# (degrees, 0 = +x, 90 = down), ('d', cx, cy, r) filled dot, ('r', x0, y0, x1, y1, radius) rounded rectangle
GLYPHS = {
    'menu': [('p', [(4, 6), (20, 6)]), ('p', [(4, 12), (20, 12)]), ('p', [(4, 18), (20, 18)])],
    'search': [('c', 11, 11, 7), ('p', [(16.2, 16.2), (21, 21)])],
    'file': [('p', [(6, 3), (15, 3), (18, 6), (18, 21), (6, 21)], True)],
    'plus': [('p', [(12, 5), (12, 19)]), ('p', [(5, 12), (19, 12)])],
    'plus_wide': [('p', [(12, 3), (12, 21)]), ('p', [(3, 12), (21, 12)])],
    'minus': [('p', [(5, 12), (19, 12)])],
    'grid': [('r', 5, 5, 11, 11, 0.5), ('r', 13, 13, 19, 19, 0.5), ('r', 13, 5, 19, 11, 0.5), ('r', 5, 13, 11, 19, 0.5)],
    'fit': [('p', [(4, 9), (4, 4), (9, 4)]), ('p', [(20, 9), (20, 4), (15, 4)]), ('p', [(4, 15), (4, 20), (9, 20)]),
            ('p', [(20, 15), (20, 20), (15, 20)])],
    'help': [('a', 12, 9, 3, 180, 395), ('p', [(14.3, 10.9), (12.6, 12.2), (12, 13.6)]), ('d', 12, 17.2, 1.15)],
    'check': [('p', [(6.8, 12.6), (10.2, 15.9), (17.2, 8.7)])],
    'x': [('p', [(7, 7), (17, 17)]), ('p', [(17, 7), (7, 17)])],
    'link': [('a', 9, 15, 4, 45, 315), ('a', 15, 9, 4, 225, 495), ('p', [(9.5, 14.5), (14.5, 9.5)])],
    'image': [('r', 3.5, 4.5, 20.5, 19.5, 2), ('c', 8.5, 9.5, 1.6), ('p', [(4, 17), (10, 12), (14, 15.5), (16.5, 13.5), (20, 16.5)])],
}
CONTROLS = ['plus', 'minus', 'fit', 'help']
RIBBON = ['menu', 'search', 'file', 'plus_wide', 'grid']
POINTER = [(2, 2), (2, 31), (9.5, 24), (14.5, 36), (19.5, 34), (14.6, 22.4), (25, 22.4)]   # the mouse pointer (30 x 40)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str):
        return hexc(CARD_COLOURS[c]) if c in CARD_COLOURS else hexc(c)
    return np.asarray(c, np.float32)


def mix(a, b, t):
    """mix two colours (hex / names / rgb) -> rgb array"""
    return _c(a) * (1 - t) + _c(b) * t


def tohex(c):
    c = np.clip(np.asarray(c, np.float32), 0, 1)
    return '#' + ''.join(f'{int(round(v * 255)):02x}' for v in c)


# ---------------------------------------------------------------- signed distances (negative inside)
def sdf_rrect(u, v, hw, hh, r):
    r = max(0.0, min(r, hw, hh))
    qx, qy = np.abs(u) - (hw - r), np.abs(v) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sdf_segment(X, Y, a, b):
    ax, ay = float(a[0]), float(a[1]); bx, by = float(b[0]), float(b[1])
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy + 1e-9
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / l2, 0, 1)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy))


def _cov(d):
    return np.clip(0.5 - d, 0, 1).astype(np.float32)


def _arc_pts(cx, cy, r, a0, a1, step=9.0):
    n = max(6, int(abs(a1 - a0) / step))
    t = np.deg2rad(np.linspace(a0, a1, n))
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1)


def _arclen(P):
    seg = np.hypot(*np.diff(P, axis=0).T) if len(P) > 1 else np.zeros(0)
    return np.concatenate([[0.0], np.cumsum(seg)])


def _cut(P, frac):
    """the first `frac` (0..1) of polyline P by arc length"""
    if frac >= 1 or len(P) < 2: return P
    s = _arclen(P); L = s[-1] * max(0.0, frac)
    i = int(np.searchsorted(s, L, side='right'))
    if i >= len(P): return P
    if i == 0: return P[:1]
    u = (L - s[i - 1]) / max(s[i] - s[i - 1], 1e-9)
    return np.vstack([P[:i], P[i - 1] + (P[i] - P[i - 1]) * u])


def _dashes(P, on, off, phase=0.0):
    """split polyline P into dash pieces (on / off along the arc length)"""
    s = _arclen(P); L = s[-1]
    if L <= 0: return []
    out, t = [], -phase
    while t < L:
        a, b = max(t, 0.0), min(t + on, L)
        if b > a:
            m = (s > a) & (s < b)
            pa = np.array([np.interp(a, s, P[:, 0]), np.interp(a, s, P[:, 1])])
            pb = np.array([np.interp(b, s, P[:, 0]), np.interp(b, s, P[:, 1])])
            out.append(np.vstack([pa, P[m], pb]))
        t += on + off
    return out


def bezier(p0, c0, c1, p1, n=48):
    t = np.linspace(0, 1, n)[:, None]
    p0, c0, c1, p1 = (np.asarray(q, np.float64) for q in (p0, c0, c1, p1))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c0 + 3 * (1 - t) * t ** 2 * c1 + t ** 3 * p1


EASE = {
    'linear': lambda u: u,
    'out': lambda u: 1 - (1 - u) ** 3,
    'io': lambda u: 3 * u * u - 2 * u ** 3,
    'back': lambda u: 1 + 2.4 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2,       # overshoots ~6 % and settles
    'drop': lambda u: (u / 0.72) ** 2 if u < 0.72 else 1 - 0.06 * np.sin(np.pi * (u - 0.72) / 0.28),  # falls, bounces 6 %
}

# ---------------------------------------------------------------- fonts
_AD = '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
_CJK_FACES = [  # (glob, {weight: face index or file-name token}); first hit wins -- macOS, Linux, Windows
    (_AD + 'PingFang.ttc', {'regular': 3, 'medium': 7, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/PingFang.ttc', {'regular': 3, 'medium': 7, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/Hiragino Sans GB.ttc', {'regular': 0, 'medium': 0, 'bold': 2, 'heavy': 2}),
    ('/usr/share/fonts/**/NotoSansCJK*-{W}.tt[cf]', {'regular': 'Regular', 'medium': 'Medium', 'bold': 'Bold', 'heavy': 'Black'}),
    ('/usr/share/fonts/**/NotoSansSC-{W}.[ot]tf', {'regular': 'Regular', 'medium': 'Medium', 'bold': 'Bold', 'heavy': 'Black'}),
    ('C:/Windows/Fonts/msyh{W}.ttc', {'regular': '', 'medium': '', 'bold': 'bd', 'heavy': 'bd'}),
]
_HEAVY_FACES = [(_AD + 'Lantinghei.ttc', 2), ('/System/Library/Fonts/Lantinghei.ttc', 2)]
_HAND_FACES = [(_AD + 'Hannotate.ttc', {'regular': 0, 'medium': 0, 'bold': 2, 'heavy': 2}),
               (_AD + 'Hanzipen.ttc', {'regular': 0, 'medium': 0, 'bold': 2, 'heavy': 2})]
_LATIN_W = {'regular': 400, 'medium': 520, 'bold': 700, 'heavy': 860}
_MONO_W = {'regular': 420, 'medium': 520, 'bold': 680, 'heavy': 800}
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


def _env(kind):
    p = os.environ.get('INKPAINT_FONT_CANVASBOARD_' + kind)
    return p if p and os.path.exists(p) else None


def _cjk(weight, size):
    """-> (font, faux-bold stroke px)"""
    env = _env('BOLD') if weight in ('bold', 'heavy') else None
    env = env or _env('CJK')
    if env: return ImageFont.truetype(env, size), 0
    if weight == 'heavy':
        for pat, idx in _HEAVY_FACES:
            p = _find(pat)
            f = p and _truetype(p, size, idx)
            if f: return f, 0
    for pat, faces in _CJK_FACES:
        tok = faces[weight]
        p = _find(pat.replace('{W}', tok)) if isinstance(tok, str) else _find(pat)
        if not p: continue
        f = _truetype(p, size, 2 if (isinstance(tok, str) and p.endswith('.ttc') and 'Noto' in p) else (tok if isinstance(tok, int) else 0))
        if f: return f, 0
    return load_font('cjk_sans', int(size)), (max(1, round(size / 40)) if weight in ('bold', 'heavy') else 0)


def _hand(weight, size):
    env = _env('HAND')
    if env: return ImageFont.truetype(env, size), 0
    for pat, faces in _HAND_FACES:
        p = _find(pat)
        f = p and _truetype(p, size, faces[weight])
        if f: return f, 0
    return _cjk(weight, size)


def _latin(weight, size, mono=False):
    env = _env('MONO' if mono else 'LATIN')
    if env: return ImageFont.truetype(env, size)
    p = '/System/Library/Fonts/SFNSMono.ttf' if mono else '/System/Library/Fonts/SFNS.ttf'
    if os.path.exists(p):
        try:
            f = ImageFont.truetype(p, size)
            if mono:
                w = _MONO_W[weight]; f.set_variation_by_axes([w, w])
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
        return load_font('typewriter', int(size))
    if os.path.exists('/System/Library/Fonts/HelveticaNeue.ttc'):
        return ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', size,
                                  index={'regular': 0, 'medium': 10, 'bold': 1, 'heavy': 1}[weight])
    return load_font('sans_bold' if weight in ('bold', 'heavy') else 'sans', int(size))


def _font(kind, weight, size):
    size = max(1.0, round(size * 4) / 4)
    key = (kind, weight, size)
    if key not in _FONTS:
        if len(_FONTS) > 160: _FONTS.clear()            # a zoom asks for a new size every frame: keep the cache small
        if kind == 'cjk': _FONTS[key] = _cjk(weight, size)
        elif kind == 'hand': _FONTS[key] = _hand(weight, size)
        else: _FONTS[key] = (_latin(weight, size, kind == 'mono'), 0)
    return _FONTS[key]


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


def spans(s):
    """inline Markdown of one line -> [(text, style)]: ==highlight== `code` **bold**, everything else plain"""
    out = []
    for t in re.split(r'(==.+?==|`.+?`|\*\*.+?\*\*)', s):
        if not t: continue
        if t.startswith('==') and t.endswith('==') and len(t) > 4: out.append((t[2:-2], 'hl'))
        elif t.startswith('`') and t.endswith('`') and len(t) > 2: out.append((t[1:-1], 'code'))
        elif t.startswith('**') and t.endswith('**') and len(t) > 4: out.append((t[2:-2], 'b'))
        else: out.append((t, ''))
    return out


# ---------------------------------------------------------------- data holders
class Box:
    """a rectangle in board coordinates (cards, groups); .anchor(side, frac) gives an edge anchor on its border"""

    def __init__(self, x0, y0, x1, y1, r=0.0):
        self.x0, self.y0, self.x1, self.y1, self.r = x0, y0, x1, y1, r
        self.w, self.h = x1 - x0, y1 - y0
        self.cx, self.cy = (x0 + x1) / 2, (y0 + y1) / 2

    def __iter__(self):
        return iter((self.x0, self.y0, self.x1, self.y1))

    def anchor(self, side, frac=0.5):
        return {'l': (self.x0, self.y0 + self.h * frac), 'r': (self.x1, self.y0 + self.h * frac),
                't': (self.x0 + self.w * frac, self.y0), 'b': (self.x0 + self.w * frac, self.y1)}[side]


class Prim:
    __slots__ = ('fn', 'box', 'var', 'clip')

    def __init__(self, fn, box, var, clip):
        self.fn, self.box, self.var, self.clip = fn, box, var, clip


class Node:
    def __init__(self, name, kind, z, order):
        self.name, self.kind, self.z, self.order = name, kind, z, order
        self.prims = []
        self.box = None                                      # union of what was drawn (board coords)
        self.rect = None                                     # the card / group Box
        self.pose = dict(dx=0.0, dy=0.0, scale=1.0, alpha=1.0, origin=None)
        self.vars, self.defaults = {}, {}

    def var(self, name):
        return self.vars.get(name, self.defaults.get(name, 1.0))


def _vspec(var):
    if var is None: return None
    if isinstance(var, str): return (var, 0.0, 1.0)
    return (var[0], float(var[1]), float(var[2]))


def _union(a, b):
    if a is None: return tuple(b)
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


class _Target:
    """where the pen draws: an RGB buffer (opaque) or a premultiplied RGBA layer, at pane offset (tx, ty)"""

    def __init__(self, rgb, a=None, tx=0, ty=0):
        self.rgb, self.a, self.tx, self.ty = rgb, a, tx, ty
        self.H, self.W = rgb.shape[:2]


# ---------------------------------------------------------------- a card's Markdown, laid out top to bottom
class Card(Box):
    """returned by CanvasBoard.card(): Markdown blocks stacked from the top (padding 24 / 22 inside a 2 px border).
    Every block takes var= (see CanvasBoard) and returns the y of its top; `self.y` is the next free y"""

    def __init__(self, cb, name, x0, y0, x1, y1, r, pad):
        super().__init__(x0, y0, x1, y1, r)
        self.cb, self.name = cb, name
        self.left, self.right = x0 + 2 + pad[0], x1 - 2 - pad[0]
        self.y = y0 + 2 + pad[1]

    def _go(self):
        return self.cb._at(self.name)

    def gap(self, px):
        self.y += px
        return self.y

    def h1(self, s, size=52, fill=BRIGHT, var=None, lh=1.3):
        top = self.y
        with self._go(): self.cb.text(s, self.left, top + lh * size / 2, size, fill, 'bold', 'lm', var=var)
        self.y += lh * size
        return top

    def h2(self, s, size=34, fill=BRIGHT, var=None, lh=1.45, glyph=None, glyph_fill=MUTED):
        top = self.y
        x = self.left
        with self._go():
            if glyph:
                self.cb.glyph(glyph, x + size * 0.45, top + lh * size / 2, size * 0.9, glyph_fill, 2.0, var=var)
                x += size * 1.2
            self.cb.text(s, x, top + lh * size / 2, size, fill, 'bold', 'lm', var=var)
        self.y += lh * size
        return top

    def p(self, s, size=28, fill=TEXT, weight='regular', var=None, hl=None, lh=1.55, x=None):
        """one line of inline Markdown (==highlight== `code` **bold**); hl= var that sweeps the highlights"""
        top = self.y
        with self._go(): self.cb.rich(s, self.left if x is None else x, top + lh * size / 2, size, fill, weight, var=var, hl=hl)
        self.y += lh * size
        return top

    def task(self, s, done=True, key=None, size=28, lh=1.62, var=None):
        """a task-list line; done=True draws it ticked. key= a var (0 -> 1) that animates the tick: the box fills
        violet, the check draws on, a strike runs through the text and the text greys"""
        top = self.y
        with self._go(): self.cb.task(s, self.left, top + lh * size / 2, size, done, key, var=var)
        self.y += lh * size
        return top

    def quote(self, lines, size=34, fill=BRIGHT, by=None, by_size=22, var=None, lh=1.45, bar=ACCENT):
        """a blockquote: a 4 px violet bar and the lines beside it; `by` = a small grey line underneath"""
        top = self.y
        lines = [lines] if isinstance(lines, str) else lines
        h = lh * size * len(lines)
        with self._go():
            self.cb.rrect(self.left, top + 4, self.left + 4, top + h - 4, 2, bar, var=var)
            for i, s in enumerate(lines):
                self.cb.rich(s, self.left + 24, top + lh * size * (i + 0.5), size, fill, 'medium', var=var)
            if by:
                self.cb.text(by, self.left + 24, top + h + by_size * 0.95, by_size, MUTED, 'regular', 'lm', var=var)
        self.y += h + (by_size * 1.9 if by else 0)
        return top

    def tags(self, tags, size=22, var=None, gap=10):
        top = self.y
        x = self.left
        with self._go():
            for t in tags:
                x = self.cb.tag(t, x, top + size * 0.85, size, var=var) + gap
        self.y += size * 1.9
        return top

    def chips(self, items, size=26, var=None, gap=14, per_row=2, row_h=None):
        """colour chips in rows: items = [(label, code, colour)], e.g. ('厨房', 'K1–K6', 'orange')"""
        top = self.y
        row_h = row_h or size * 2.3
        cw = (self.right - self.left - gap * (per_row - 1)) / per_row
        with self._go():
            for i, (label, code, colour) in enumerate(items):
                r, c = divmod(i, per_row)
                v = var[i] if isinstance(var, list) else var
                self.cb.chip(self.left + c * (cw + gap), top + r * row_h, cw, size * 1.85, label, code, colour, size, var=v)
        self.y += row_h * ((len(items) + per_row - 1) // per_row)
        return top

    def bar(self, frac, h=10, fill=ACCENT, var=None, label=None, size=22):
        top = self.y
        with self._go():
            x1 = self.right
            if label:
                self.cb.text(label, self.right, top + h / 2, size, MUTED, 'medium', 'rm', family='mono', var=var)
                x1 = self.right - self.cb.measure(label, size, 'medium', family='mono') - 16
            self.cb.rrect(self.left, top, x1, top + h, h / 2, '#333333', var=var)
            self.cb.rrect(self.left, top, self.left + (x1 - self.left) * frac, top + h, h / 2, fill, var=var,
                          mode='reveal')
        self.y += h
        return top

    def rule(self, pad=14, fill=BORDER, var=None):
        self.y += pad
        with self._go(): self.cb.rrect(self.left, self.y, self.right, self.y + 1.5, 0, fill, var=var)
        self.y += pad + 1.5
        return self.y


# ---------------------------------------------------------------- the board
class CanvasBoard:
    GLYPHS = GLYPHS
    CARD_COLOURS = CARD_COLOURS

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None, window=None, tab='未命名.canvas',
                 ribbon=True, controls=True, glow=True):
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._nstage = [], 0
        if stages_dir: os.makedirs(stages_dir, exist_ok=True)
        wx, wy, ww, wh = window or (round(W * 0.0208), round(H * 0.0315), W - 2 * round(W * 0.0208), H - 2 * round(H * 0.0315))
        self.win = Box(wx, wy, wx + ww, wy + wh, 14)
        self.tab, self.ribbon, self.controls, self.glow = tab, ribbon, controls, glow
        self.bar_h, self.rib_w = 52, (52 if ribbon else 0)
        self.pane = Box(wx + self.rib_w, wy + self.bar_h, wx + ww, wy + wh)
        self.VW, self.VH = int(self.pane.w), int(self.pane.h)
        self.cam = (0.0, 0.0, 1.0)
        self.grid, self.dot_r = 28.0, 1.6
        self.nodes = {}
        self.cur = None
        self._clip = None
        self._chrome = None
        self.hover = None                                   # index of a highlighted zoom button
        self._cursor = None
        g = np.random.default_rng(seed + 7).random((H, W)).astype(np.float32)
        self._grain = (g - 0.5) * (1.2 / 255)
        # pen state (set while rendering)
        self._tg = None
        self._k, self._ox, self._oy = 1.0, 0.0, 0.0
        self._clip_s = None

    # ------------------------------------------------------------ nodes, poses, vars
    def node(self, name, kind='shape', z=None):
        """start recording into node `name` (re-opens it if it exists). z: depth (default by kind: groups 0, edges 5,
        cards 10, everything else 20); lower z is drawn first"""
        if name not in self.nodes:
            zz = {'group': 0, 'edge': 5, 'card': 10}.get(kind, 20) if z is None else z
            self.nodes[name] = Node(name, kind, zz, len(self.nodes))
        elif z is not None:
            self.nodes[name].z = z
        self.cur = self.nodes[name]
        return self.cur

    def end(self):
        self.cur = None

    @contextmanager
    def _at(self, name):
        old = self.cur
        self.cur = self.nodes[name]
        try:
            yield
        finally:
            self.cur = old

    def pose(self, name, dx=0.0, dy=0.0, scale=1.0, alpha=1.0, origin=None):
        """how node `name` is shown: offset (board px), scale about `origin` (default: its centre) and opacity.
        pose(name) = at rest"""
        self.nodes[name].pose = dict(dx=dx, dy=dy, scale=scale, alpha=alpha, origin=origin)

    def set(self, name, **vars):
        """set progress vars of node `name` (unset vars read their default: 1 = finished, or what the node set)"""
        self.nodes[name].vars.update(vars)

    def reset(self, name):
        self.nodes[name].vars.clear()

    def show(self, *names, alpha=1.0):
        for n in names: self.nodes[n].pose['alpha'] = alpha

    def hide(self, *names):
        for n in names: self.nodes[n].pose['alpha'] = 0.0

    def rect(self, name):
        N = self.nodes[name]
        return N.rect or Box(*N.box)

    @contextmanager
    def clip(self, x0, y0=None, x1=None, y1=None, r=0.0):
        """shapes recorded inside are clipped to this rounded rectangle (board coords); clip(box) takes a Box"""
        if isinstance(x0, Box): x0, y0, x1, y1, r = x0.x0, x0.y0, x0.x1, x0.y1, x0.r
        old = self._clip
        self._clip = (x0, y0, x1, y1, r)
        try:
            yield
        finally:
            self._clip = old

    def _rec(self, fn, box, var=None):
        N = self.cur
        if N is None: raise ValueError('open a node first: node(name), group(), card() or edge()')
        N.prims.append(Prim(fn, box, _vspec(var), self._clip))
        N.box = _union(N.box, box)

    # ------------------------------------------------------------ camera
    def camera(self, x, y, z=1.0):
        """the board point (x, y) at the centre of the pane, zoom z"""
        self.cam = (float(x), float(y), float(z))

    def fit(self, x0, y0, x1, y1, pad=60, zmax=2.0, right=0):
        """-> (x, y, z): the camera that shows the board box with `pad` screen px around it (`right`: extra px
        kept free on the right, e.g. for the zoom buttons)"""
        z = min((self.VW - 2 * pad - right) / (x1 - x0), (self.VH - 2 * pad) / (y1 - y0), zmax)
        return ((x0 + x1) / 2 + right / 2 / z, (y0 + y1) / 2, z)

    def to_screen(self, x, y, cam=None):
        """board point -> canvas pixel (for a cursor over a card)"""
        cx, cy, z = cam or self.cam
        return self.pane.x0 + self.VW / 2 + (x - cx) * z, self.pane.y0 + self.VH / 2 + (y - cy) * z

    def control(self, i):
        """canvas-pixel centre of zoom button i (0 +, 1 -, 2 fit, 3 ?)"""
        x0 = self.pane.x1 - 18 - 50
        return x0 + 25, self.pane.y0 + 18 + 8 + 13 + i * 40

    def cursor(self, x=None, y=None, click=None, alpha=1.0, press=False):
        """the mouse pointer (tip at canvas pixel x, y); click = 0..1 progress of the violet click ring;
        cursor() hides it"""
        self._cursor = None if x is None else (x, y, click, alpha, press)

    # ------------------------------------------------------------ the pen (board coords -> current target)
    def _S(self, x, y):
        return x * self._k + self._ox, y * self._k + self._oy

    def _grid(self, x0, y0, x1, y1):
        T = self._tg
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(T.W, int(np.ceil(x1)) + 1), min(T.H, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None
        X = np.arange(x0, x1, dtype=np.float32)[None, :] + 0.5
        Y = np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5
        return (slice(y0, y1), slice(x0, x1)), X, Y

    def _over(self, sl, cov, col):
        cov = np.clip(cov, 0, 1).astype(np.float32)
        if self._clip_s is not None:
            cx0, cy0, cx1, cy1, cr = self._clip_s
            X = np.arange(sl[1].start, sl[1].stop, dtype=np.float32)[None, :] + 0.5
            Y = np.arange(sl[0].start, sl[0].stop, dtype=np.float32)[:, None] + 0.5
            cov = cov * _cov(sdf_rrect(X - (cx0 + cx1) / 2, Y - (cy0 + cy1) / 2, (cx1 - cx0) / 2, (cy1 - cy0) / 2, cr))
        col = col if (isinstance(col, np.ndarray) and col.ndim == 3) else _c(col)
        c3 = cov[..., None]
        T = self._tg
        T.rgb[sl] = T.rgb[sl] * (1 - c3) + col * c3
        if T.a is not None:
            T.a[sl] = T.a[sl] * (1 - cov) + cov

    def _w(self, w, floor=0.0):
        return max(w * self._k, floor)

    # screen-space primitives (already transformed coordinates)
    def _s_rrect(self, x0, y0, x1, y1, r, fill, alpha=1.0, ring=0.0, inset=True, reveal=1.0):
        g = self._grid(x0 - ring - 2, y0 - ring - 2, x1 + ring + 2, y1 + ring + 2)
        if not g or alpha <= 0: return
        sl, X, Y = g
        d = sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r)
        if ring:
            d = np.abs(d + ring / 2) - ring / 2 if inset else np.abs(d - ring / 2) - ring / 2
        cov = _cov(d) * alpha
        if reveal < 1:
            cov = cov * np.clip((x0 + (x1 - x0) * reveal - X) + 0.5, 0, 1)
        self._over(sl, cov, fill)

    def _s_circle(self, cx, cy, r, fill, alpha=1.0, ring=0.0):
        g = self._grid(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        if not g or alpha <= 0 or r <= 0: return
        sl, X, Y = g
        d = np.hypot(X - cx, Y - cy) - r
        if ring: d = np.abs(d + ring / 2) - ring / 2
        self._over(sl, _cov(d) * alpha, fill)

    def _s_line(self, P, width, fill, alpha=1.0):
        P = np.asarray(P, np.float32)
        if len(P) < 2 or alpha <= 0: return
        pad = width / 2 + 2
        g = self._grid(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if not g: return
        sl, X, Y = g
        gx0, gy0 = sl[1].start, sl[0].start
        cov = np.zeros((sl[0].stop - gy0, sl[1].stop - gx0), np.float32)
        for a, b in zip(P[:-1], P[1:]):
            sx0 = max(gx0, int(np.floor(min(a[0], b[0]) - pad))) - gx0
            sx1 = min(sl[1].stop, int(np.ceil(max(a[0], b[0]) + pad)) + 1) - gx0
            sy0 = max(gy0, int(np.floor(min(a[1], b[1]) - pad))) - gy0
            sy1 = min(sl[0].stop, int(np.ceil(max(a[1], b[1]) + pad)) + 1) - gy0
            if sx1 <= sx0 or sy1 <= sy0: continue
            d = sdf_segment(X[:, sx0:sx1], Y[sy0:sy1, :], a, b) - width / 2
            np.maximum(cov[sy0:sy1, sx0:sx1], _cov(d), out=cov[sy0:sy1, sx0:sx1])
        self._over(sl, cov * alpha, fill)

    def _s_poly(self, P, fill, alpha=1.0, ss=4):
        P = np.asarray(P, np.float32)
        x0, y0 = int(np.floor(P[:, 0].min())) - 1, int(np.floor(P[:, 1].min())) - 1
        x1, y1 = int(np.ceil(P[:, 0].max())) + 2, int(np.ceil(P[:, 1].max())) + 2
        g = self._grid(x0, y0, x1 - 1, y1 - 1)
        if not g or alpha <= 0: return
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P.tolist()], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        sl = g[0]
        m = m[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0]
        self._over(sl, m * alpha, fill)

    def _s_shadow(self, x0, y0, x1, y1, r, dx, dy, blur_px, spread, colour, alpha):
        sig = blur_px / 2
        pad = 3 * sig + abs(spread) + 3
        g = self._grid(min(x0, x0 + dx) - pad, min(y0, y0 + dy) - pad, max(x1, x1 + dx) + pad, max(y1, y1 + dy) + pad)
        if not g or alpha <= 0: return
        sl, X, Y = g
        sx0, sy0, sx1, sy1 = x0 - spread + dx, y0 - spread + dy, x1 + spread + dx, y1 + spread + dy
        if sx1 <= sx0 or sy1 <= sy0: return
        m = _cov(sdf_rrect(X - (sx0 + sx1) / 2, Y - (sy0 + sy1) / 2, (sx1 - sx0) / 2, (sy1 - sy0) / 2, max(0.0, r + spread)))
        own = _cov(sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r))
        if sig > 0.3: m = blur(m, sig)
        self._over(sl, m * (1 - own) * alpha, colour)

    def _glyphs(self, s, size, weight, spacing, family):
        out, x = [], 0.0
        if family == 'hand':
            f, fake = _font('hand', weight, size)
            return [(f, s, 0.0, fake)], f.getlength(s)
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

    def _s_text(self, s, x, y, size, fill, weight='regular', anchor='ls', alpha=1.0, spacing=0.0, family='sans',
                reveal=1.0, feather=10.0):
        if size < 3 or not s:
            return self._glyphs(s, max(size, 3), weight, spacing, family)[1] if s else 0.0
        gl, tw = self._glyphs(s, size, weight, spacing, family)
        x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        base = y + {'s': 0.0, 'm': 0.37 * size, 't': 0.86 * size}[anchor[1]]
        if alpha <= 0 or reveal <= 0: return tw
        bx0, by0 = int(np.floor(x0)) - 6, int(np.floor(base - size * 1.25))
        bw, bh = int(tw) + 14, int(size * 1.7) + 8
        g = self._grid(bx0, by0, bx0 + bw - 1, by0 + bh - 1)
        if not g: return tw
        im = Image.new('L', (bw, bh), 0)
        dr = ImageDraw.Draw(im)
        for f, piece, off, fake in gl:
            dr.text((x0 - bx0 + off, base - by0), piece, font=f, fill=255, anchor='ls', stroke_width=fake, stroke_fill=255)
        m = np.asarray(im, np.float32) / 255
        if reveal < 1:
            xs = np.arange(bw, dtype=np.float32) + bx0 + 0.5
            m = m * np.clip((x0 - 4 + (tw + 8) * reveal - xs) / max(feather, 1) + 0.5, 0, 1)[None, :]
        sl = g[0]
        m = m[sl[0].start - by0:sl[0].stop - by0, sl[1].start - bx0:sl[1].stop - bx0]
        self._over(sl, m * alpha, fill)
        return tw

    def _s_glyph(self, name, cx, cy, size, fill, sw=1.8, alpha=1.0, draw=1.0):
        k = size / 24.0
        pad = size * 0.6 + 2
        g = self._grid(cx - pad, cy - pad, cx + pad, cy + pad)
        if not g or alpha <= 0: return
        sl, X, Y = g
        u, v = (X - cx) / k + 12, (Y - cy) / k + 12
        d = np.full(np.broadcast(u, v).shape, 1e9, np.float32)
        for p in GLYPHS[name]:
            kind = p[0]
            if kind == 'p':
                P = np.asarray(p[1], np.float32)
                if len(p) > 2 and p[2]: P = np.vstack([P, P[:1]])
                if draw < 1: P = _cut(P, draw)
                e = np.full(d.shape, 1e9, np.float32)
                for a, b in zip(P[:-1], P[1:]):
                    e = np.minimum(e, sdf_segment(u, v, a, b))
                e = e - sw / 2
            elif kind == 'c':
                e = np.abs(np.hypot(u - p[1], v - p[2]) - p[3]) - sw / 2
            elif kind == 'a':
                P = _arc_pts(*p[1:])
                e = np.full(d.shape, 1e9, np.float32)
                for a, b in zip(P[:-1], P[1:]):
                    e = np.minimum(e, sdf_segment(u, v, a, b))
                e = e - sw / 2
            elif kind == 'd':
                e = np.hypot(u - p[1], v - p[2]) - p[3]
            else:
                x0, y0, x1, y1, rr = p[1:]
                e = np.abs(sdf_rrect(u - (x0 + x1) / 2, v - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, rr)) - sw / 2
            d = np.minimum(d, e)
        self._over(sl, _cov(d * k) * alpha, fill)

    # ------------------------------------------------------------ recorded shapes (board coords)
    @staticmethod
    def _amt(t, mode):
        """(alpha factor, draw fraction, reveal fraction, pop scale) for progress t under `mode`"""
        if mode == 'fade': return t, 1.0, 1.0, 1.0
        if mode == 'draw': return (1.0 if t > 0 else 0.0), t, 1.0, 1.0
        if mode == 'reveal': return (1.0 if t > 0 else 0.0), 1.0, t, 1.0
        if mode == 'pop': return min(1.0, 2.2 * t), 1.0, 1.0, (EASE['back'](t) * 0.7 + 0.3 if t > 0 else 0.0)
        return t, 1.0, 1.0, 1.0

    def rrect(self, x0, y0, x1, y1, r=0.0, fill=TEXT, alpha=1.0, ring=0.0, inset=True, var=None, mode='fade', hair=True):
        """rounded rectangle; ring=w draws only a w px line along the edge (inside if inset). hair: rings never get
        thinner than 1 screen px when zoomed out"""
        def fn(t):
            al, _, rv, sc = self._amt(t, mode)
            if al <= 0: return
            a, b = self._S(x0, y0); c, d = self._S(x1, y1)
            if sc != 1:
                mx, my = (a + c) / 2, (b + d) / 2
                a, c, b, d = mx + (a - mx) * sc, mx + (c - mx) * sc, my + (b - my) * sc, my + (d - my) * sc
            rw = self._w(ring, min(ring, 1.0) if hair else 0) if ring else 0.0
            self._s_rrect(a, b, c, d, r * self._k * sc, fill, alpha * al, rw, inset, rv)
        self._rec(fn, (x0 - ring - 2, y0 - ring - 2, x1 + ring + 2, y1 + ring + 2), var)

    def circle(self, cx, cy, r, fill=TEXT, alpha=1.0, ring=0.0, var=None, mode='fade'):
        def fn(t):
            al, _, _, sc = self._amt(t, mode)
            if al <= 0: return
            x, y = self._S(cx, cy)
            self._s_circle(x, y, r * self._k * sc, fill, alpha * al, self._w(ring, min(ring, 1.0)) * sc if ring else 0.0)
        self._rec(fn, (cx - r - ring - 2, cy - r - ring - 2, cx + r + ring + 2, cy + r + ring + 2), var)

    def line(self, pts, width=2.0, fill=TEXT, alpha=1.0, var=None, mode='draw', dash=None, closed=False, floor=0.9):
        """polyline with round caps and joins; mode 'draw' draws it on along its length; dash=(on, off) board px"""
        P = np.asarray(pts, np.float64)
        if closed: P = np.vstack([P, P[:1]])

        def fn(t):
            al, dr, _, _ = self._amt(t, mode)
            if al <= 0 or dr <= 0: return
            Q = _cut(P, dr) * self._k + np.array([self._ox, self._oy])
            w = self._w(width, floor)
            if dash:
                for piece in _dashes(Q, dash[0] * self._k, dash[1] * self._k):
                    self._s_line(piece, w, fill, alpha * al)
            else:
                self._s_line(Q, w, fill, alpha * al)
        self._rec(fn, (P[:, 0].min() - width - 2, P[:, 1].min() - width - 2, P[:, 0].max() + width + 2, P[:, 1].max() + width + 2), var)

    def poly(self, pts, fill=TEXT, alpha=1.0, var=None, mode='fade'):
        P = np.asarray(pts, np.float64)

        def fn(t):
            al, _, _, sc = self._amt(t, mode)
            if al <= 0: return
            Q = P * self._k + np.array([self._ox, self._oy])
            if sc != 1:
                m = Q.mean(0); Q = m + (Q - m) * sc
            self._s_poly(Q, fill, alpha * al)
        self._rec(fn, (P[:, 0].min() - 2, P[:, 1].min() - 2, P[:, 0].max() + 2, P[:, 1].max() + 2), var)

    def shadow(self, x0, y0, x1, y1, r=0.0, dx=0.0, dy=0.0, blur_px=0.0, spread=0.0, colour='#000000', alpha=0.3,
               var=None, mode='fade'):
        """CSS box-shadow of a rounded rectangle (board px; painted outside the element only)"""
        def fn(t):
            al = self._amt(t, mode)[0]
            if al <= 0: return
            a, b = self._S(x0, y0); c, d = self._S(x1, y1); k = self._k
            self._s_shadow(a, b, c, d, r * k, dx * k, dy * k, blur_px * k, spread * k, colour, alpha * al)
        p = 1.5 * blur_px + abs(spread) + max(abs(dx), abs(dy)) + 4
        self._rec(fn, (x0 - p, y0 - p, x1 + p, y1 + p), var)

    def text(self, s, x, y, size, fill=TEXT, weight='regular', anchor='ls', alpha=1.0, spacing=0.0, family='sans',
             var=None, mode='reveal'):
        """text at board (x, y); anchor [l m r] + [s baseline, m middle of the CJK body, t top]. weight: regular /
        medium / bold / heavy; family: sans / mono / hand. Returns the width (board px)"""
        tw = self.measure(s, size, weight, spacing, family)

        def fn(t):
            al, _, rv, _ = self._amt(t, mode)
            if al <= 0: return
            sx, sy = self._S(x, y)
            self._s_text(s, sx, sy, size * self._k, fill, weight, anchor, alpha * al, spacing * self._k, family, rv)
        x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        self._rec(fn, (x0 - 4, y - size * 1.4, x0 + tw + 4, y + size * 1.4), var)
        return tw

    def glyph(self, name, cx, cy, size=24, fill=MUTED, sw=1.8, alpha=1.0, var=None, mode='fade'):
        def fn(t):
            al, dr, _, sc = self._amt(t, mode)
            if al <= 0: return
            x, y = self._S(cx, cy)
            self._s_glyph(name, x, y, size * self._k * sc, fill, sw, alpha * al, dr)
        self._rec(fn, (cx - size, cy - size, cx + size, cy + size), var)

    def measure(self, s, size, weight='regular', spacing=0.0, family='sans'):
        """advance width in board px"""
        return self._glyphs(s, size, weight, spacing, family)[1]

    # ------------------------------------------------------------ Markdown pieces (used by Card, usable directly)
    def rich(self, s, x, y, size=28, fill=TEXT, weight='regular', var=None, hl=None):
        """one line of inline Markdown at board (x, y = middle of the line): ==highlight== (violet, sweeps with var
        `hl`), `code` (mono on a dark pill), **bold**. Laid out again at every zoom, so runs never drift apart"""
        sp = spans(s)
        hls = _vspec(hl)
        tw = 0.0
        for t, st in sp:
            tw += self._run_w(t, st, size, weight)

        def fn(t):
            al, _, rv, _ = self._amt(t, 'reveal')
            if al <= 0: return
            N = self._drawing
            q = 1.0
            if hls:
                v = N.var(hls[0]); q = float(np.clip((v - hls[1]) / max(hls[2] - hls[1], 1e-6), 0, 1))
            k = self._k
            sx, sy = self._S(x, y)
            fs = size * k
            cx = sx
            right = None if rv >= 1 else sx - 4 + (tw * k + 8) * rv           # a line being written, left to right
            for txt, st in sp:
                w = self._run_w(txt, st, fs, weight)
                rr = 1.0 if right is None else float(np.clip((right - cx) / max(w, 1e-6), 0, 1))
                if rr <= 0: break
                if st == 'hl' and q > 0:
                    self._s_rrect(cx - 3 * k, sy - 0.66 * fs, cx + (w + 3 * k) * q * rr, sy + 0.62 * fs, 6 * k,
                                  ACCENT, 0.45 * al)
                if st == 'code':
                    self._s_rrect(cx, sy - 0.62 * fs, cx + w, sy + 0.58 * fs, 6 * k, CODE_BG, al, reveal=rr)
                    self._s_text(txt, cx + 8 * k, sy, fs * 0.88, CODE_FG, 'regular', 'lm', al, family='mono', reveal=rr)
                else:
                    col = BRIGHT if (st == 'b' or (st == 'hl' and q > 0.35)) else fill
                    self._s_text(txt, cx, sy, fs, col, 'bold' if st == 'b' else weight, 'lm', al, reveal=rr)
                cx += w
        self._rec(fn, (x - 6, y - size, x + tw + 6, y + size), var)
        return tw

    def _run_w(self, txt, st, size, weight):
        if st == 'code':
            return self._glyphs(txt, size * 0.88, 'regular', 0.0, 'mono')[1] + 16 * size / 28
        return self._glyphs(txt, size, 'bold' if st == 'b' else weight, 0.0, 'sans')[1]

    def task(self, s, x, y, size=28, done=True, key=None, var=None):
        """a task-list line at board (x, y = middle): a checkbox and the text. done=True is ticked; key= a var
        (0..1) that animates the tick (fill pops, check draws, strike runs, text greys). Returns the text width"""
        bs = size * 0.8
        tx = x + bs + size * 0.55
        tw = self.measure(s, size)
        ks = _vspec(key)

        def fn(t):
            al = self._amt(t, 'fade')[0]
            if al <= 0: return
            N = self._drawing
            u = 1.0 if ks is None else float(np.clip((N.var(ks[0]) - ks[1]) / max(ks[2] - ks[1], 1e-6), 0, 1))
            if not done: u = 0.0
            k = self._k
            bx, by = self._S(x, y)
            S = bs * k
            pop = EASE['back'](min(1.0, u * 1.7)) if u > 0 else 0.0
            self._s_rrect(bx, by - S / 2, bx + S, by + S / 2, S * 0.24, FAINT, al * (1 - min(1, u * 2.5)), self._w(2.0, 1.0))
            if pop > 0:
                m = S / 2 * pop
                self._s_rrect(bx + S / 2 - m, by - m, bx + S / 2 + m, by + m, S * 0.24 * pop, ACCENT, al * min(1, u * 2.2))
                ck = float(np.clip(u * 1.6 - 0.35, 0, 1))
                if ck > 0:
                    self._s_glyph('check', bx + S / 2, by, S * 1.05, WHITE, 2.9, al, ck)
            col = mix(TEXT, DONE, float(np.clip((u - 0.25) / 0.6, 0, 1)))
            sx, _ = self._S(tx, y)
            w = self._s_text(s, sx, by, size * k, col, 'regular', 'lm', al)
            st = float(np.clip((u - 0.3) / 0.7, 0, 1))
            if st > 0:
                self._s_rrect(sx - 2 * k, by - 0.06 * size * k - max(1.0, 1.1 * k), sx - 2 * k + (w + 4 * k) * st,
                              by - 0.06 * size * k + max(1.0, 1.1 * k), 1.2 * k, DONE, al)
        self._rec(fn, (x - 4, y - size, tx + tw + 8, y + size), var)
        return tw

    def tag(self, s, x, y, size=22, var=None):
        """a #tag pill (violet text on a faint violet capsule), left edge at x, middle at y. Returns the right edge"""
        tw = self.measure(s, size, 'medium')
        h = size * 1.55
        x1 = x + tw + size * 1.1
        self.rrect(x, y - h / 2, x1, y + h / 2, h / 2, ACCENT, 0.16, var=var)
        self.text(s, x + size * 0.55, y, size, ACCENT2, 'medium', 'lm', var=var, mode='fade')
        return x1

    def chip(self, x, y, w, h, label, code=None, colour='orange', size=26, var=None):
        """a colour-coded chip (box labels, categories): tinted fill, coloured ring, a dot, the label and a mono code"""
        col = _c(colour)
        self.rrect(x, y, x + w, y + h, 10, tohex(mix(BG3, col, 0.12)), var=var)
        self.rrect(x, y, x + w, y + h, 10, tohex(col), 0.55, ring=2.0, var=var)
        self.circle(x + size * 0.85, y + h / 2, size * 0.24, tohex(col), var=var)
        lw = self.text(label, x + size * 1.45, y + h / 2, size, BRIGHT, 'medium', 'lm', var=var, mode='fade')
        if code:
            self.text(code, x + w - size * 0.7, y + h / 2, size * 0.9, tohex(col), 'medium', 'rm', family='mono', var=var,
                      mode='fade')
        return lw

    # ------------------------------------------------------------ canvas objects
    def group(self, name, x, y, w, h, label=None, colour=None, z=None, label_size=34):
        """a group frame (radius 20, 2 px line, a whisper of fill) with its label floating above the top-left
        corner, like the app. colour= tints the frame with a card colour"""
        self.node(name, 'group', z)
        line = tohex(mix(GROUP_LINE, colour, 0.75)) if colour else GROUP_LINE
        fill = tohex(_c(colour)) if colour else WHITE
        self.rrect(x, y, x + w, y + h, 20, fill, 0.045 if colour else 0.025, var='frame')
        self.rrect(x, y, x + w, y + h, 20, line, ring=2.0, var='frame')
        if label:
            self.text(label, x + 6, y - 18, label_size, tohex(mix(MUTED, colour, 0.6)) if colour else MUTED, 'bold', 'ls',
                      var='label', mode='fade')
        self.cur.rect = Box(x, y, x + w, y + h, 20)
        self.end()
        return self.nodes[name].rect

    def card(self, name, x, y, w, h, colour=None, label=None, z=None, pad=(24, 22), fill=None, selected=False,
             shadow=True, tint=0.05):
        """a card: dark rounded body (radius 12), a 2 px border in a card colour (red orange yellow green cyan purple,
        'accent', a hex, or None = grey) with a faint tint of it (5 %), a soft drop shadow, an optional file-name label above.
        selected=True: violet border and a faint violet halo (also var 'sel'). var 'lift' (default 0) adds the big
        shadow of a card held above the board. Returns a Card for its Markdown"""
        self.node(name, 'card', z)
        N = self.cur
        N.defaults.update(lift=0.0, sel=1.0 if selected else 0.0)
        col = _c(colour) if colour else None
        body = fill or (tohex(mix(BG2, col, tint)) if col is not None else BG2)
        edge = tohex(col) if col is not None else BORDER2
        x1, y1 = x + w, y + h
        if shadow:
            self.shadow(x, y, x1, y1, 12, 0, 20, 40, -24, '#000000', 0.8)
            self.shadow(x, y, x1, y1, 12, 0, 46, 70, -18, '#000000', 0.75, var='lift')
        self.rrect(x - 6, y - 6, x1 + 6, y1 + 6, 17, ACCENT, 0.18, var='sel')
        self.rrect(x, y, x1, y1, 12, body)
        self.rrect(x, y, x1, y1, 12, edge, ring=2.0)
        self.rrect(x, y, x1, y1, 12, ACCENT, ring=2.0, var='sel')
        if label:
            self.text(label, x + 4, y - 16, 28, MUTED, 'bold', 'ls', mode='fade')
        c = Card(self, name, x, y, x1, y1, 12, pad)
        N.rect = Box(x, y, x1, y1, 12)
        self.end()
        return c

    def image_card(self, name, x, y, w, h, label=None, bg='#191919', grid=22, grid_colour='#222222', z=None):
        """an image card (no padding, the picture fills it, file name above): returns the Card; draw the picture with
        `with cb.clip(card): ...` into node `name` (cb.node(name))"""
        c = self.card(name, x, y, w, h, None, label, z, (0, 0), fill=bg)
        self.node(name)
        if grid:
            with self.clip(x + 2, y + 2, x + w - 2, y + h - 2, 10):
                for gx in np.arange(x + grid, x + w, grid):
                    self.rrect(gx - 0.5, y, gx + 0.5, y + h, 0, grid_colour, hair=False)
                for gy in np.arange(y + grid, y + h, grid):
                    self.rrect(x, gy - 0.5, x + w, gy + 0.5, 0, grid_colour, hair=False)
        self.rrect(x, y, x + w, y + h, 12, BORDER2, ring=2.0)
        self.end()
        return c

    def _anchor(self, a):
        """(node, side[, frac]) or (x, y, side) -> (x, y, side)"""
        if isinstance(a[0], str):
            side = a[1]; frac = a[2] if len(a) > 2 else 0.5
            return (*self.rect(a[0]).anchor(side, frac), side)
        return a

    def edge(self, name, a, b, colour=EDGE, width=4.0, label=None, dashed=False, arrow=True, z=None, label_size=24,
             bend=1.0):
        """a curved edge between two anchors -- (card name, side 'l' 'r' 't' 'b'[, frac along the side]) or
        (x, y, side) -- a cubic that leaves and enters along the sides' normals, an arrowhead on the end, an optional
        label on a board-coloured pill at its middle. var 'p' (0..1) draws it on: the arrow grows over the last 14 %,
        the label fades in after half. Returns the board-coordinate polyline"""
        self.node(name, 'edge', z)
        ax, ay, sa = self._anchor(a)
        bx, by, sb = self._anchor(b)
        NV = {'l': (-1, 0), 'r': (1, 0), 't': (0, -1), 'b': (0, 1)}
        dist = np.hypot(bx - ax, by - ay)
        c = float(np.clip(dist * 0.45, 50, 240)) * bend
        P = bezier((ax, ay), (ax + NV[sa][0] * c, ay + NV[sa][1] * c), (bx + NV[sb][0] * c, by + NV[sb][1] * c), (bx, by), 64)
        nx, ny = NV[sb]
        ang = np.arctan2(-ny, -nx)
        head = np.array([(2, 0), (-18, -10), (-18, 10)], np.float64) * (width / 4) ** 0.5
        rot = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
        line_end = P.copy()
        if arrow:   # stop the line under the arrowhead so its round cap never peeks past the tip
            line_end = _cut(P, 1 - 10 * (width / 4) ** 0.5 / max(_arclen(P)[-1], 1))
        lab_box = None
        if label:
            mid = P[len(P) // 2]
            lw = self.measure(label, label_size, 'medium')
            lab_box = (mid[0] - lw / 2 - 12, mid[1] - label_size * 0.85, mid[0] + lw / 2 + 12, mid[1] + label_size * 0.85)

        def fn(t):
            if t <= 0: return
            k, o = self._k, np.array([self._ox, self._oy])
            Q = _cut(line_end, min(1.0, t / 0.97)) * k + o
            w = self._w(width, 1.0)
            if dashed:
                for piece in _dashes(Q, 12 * k, 12 * k):
                    self._s_line(piece, w, colour)
            else:
                self._s_line(Q, w, colour)
            hp = float(np.clip((t - 0.86) / 0.14, 0, 1))
            if arrow and hp > 0:
                H = (head * hp) @ rot.T + np.array([bx, by])
                self._s_poly(H * k + o, colour, hp)
            la = float(np.clip((t - 0.5) / 0.3, 0, 1))
            if label and la > 0:
                x0, y0 = self._S(lab_box[0], lab_box[1]); x1, y1 = self._S(lab_box[2], lab_box[3])
                self._s_rrect(x0, y0, x1, y1, 8 * k, BOARD, la)
                mx, my = self._S((lab_box[0] + lab_box[2]) / 2, (lab_box[1] + lab_box[3]) / 2)
                self._s_text(label, mx, my, label_size * k, MUTED, 'medium', 'mm', la)
        bb = (P[:, 0].min() - 24, P[:, 1].min() - 24, P[:, 0].max() + 24, P[:, 1].max() + 24)
        if lab_box: bb = _union(bb, lab_box)
        self._rec(fn, bb, 'p')
        self.end()
        return P

    # ------------------------------------------------------------ hand-drawn strokes (sketch cards)
    def _rough_seg(self, p0, p1, rng, rough):
        p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
        d = p1 - p0; L = float(np.hypot(*d)) + 1e-6; u = d / L; nrm = np.array([-u[1], u[0]])
        o = rough * min(2.4, 0.5 + L * 0.008)
        a = p0 - u * rng.uniform(-0.5, 3.0) * rough + nrm * rng.normal(0, o * 0.45)
        b = p1 + u * rng.uniform(-0.5, 3.0) * rough + nrm * rng.normal(0, o * 0.45)
        bow = nrm * rng.normal(0, rough * min(L * 0.01, 3.2))
        c0 = a + (b - a) * rng.uniform(0.25, 0.4) + bow + rng.normal(0, o * 0.35, 2)
        c1 = a + (b - a) * rng.uniform(0.6, 0.75) + bow + rng.normal(0, o * 0.35, 2)
        return bezier(a, c0, c1, b, max(6, int(L / 10)))

    def rough(self, pts, width=3.0, fill=TEXT, closed=False, rough=1.0, passes=2, seed=None, var=None, alpha=1.0,
              dash=None, second=0.55):
        """a hand-drawn polyline (sketch look): every segment is a slightly bowed, overshooting stroke drawn `passes`
        times with fresh jitter (the second pass at `second` x opacity). Draws on with var (mode 'draw')"""
        rng = np.random.default_rng(self.seed * 7919 + (seed if seed is not None else int(self.rng.integers(1 << 30))))
        P = [tuple(p) for p in pts] + ([tuple(pts[0])] if closed else [])
        for k in range(passes):
            segs = [self._rough_seg(a, b, rng, rough) for a, b in zip(P[:-1], P[1:])]
            Q = np.vstack(segs)
            self.line(Q, width * (1 if k == 0 else 0.8), fill, alpha * (1 if k == 0 else second), var=var, dash=dash)

    def rough_rect(self, x0, y0, x1, y1, **kw):
        self.rough([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], closed=True, **kw)

    def rough_ellipse(self, cx, cy, rx, ry, width=3.0, fill=TEXT, rough=1.0, passes=2, seed=None, var=None, alpha=1.0,
                      a0=None, sweep=None, second=0.55, dash=None):
        """a hand-drawn ellipse (or arc: a0 degrees, sweep degrees), closing with a little overlap like a pen"""
        rng = np.random.default_rng(self.seed * 7907 + (seed if seed is not None else int(self.rng.integers(1 << 30))))
        for k in range(passes):
            s0 = np.deg2rad(rng.uniform(0, 360) if a0 is None else a0 + rng.normal(0, 2))
            sw = np.deg2rad(sweep if sweep is not None else 372 + rng.uniform(0, 14))
            n = max(24, int(abs(sw) * max(rx, ry) / 6))
            t = s0 + np.linspace(0, sw, n)
            wob = 1 + rough * 0.025 * np.sin(t * rng.uniform(1.5, 2.5) + rng.uniform(0, 6)) + rough * rng.normal(0, 0.004, n)
            P = np.stack([cx + rx * wob * np.cos(t), cy + ry * wob * np.sin(t)], 1)
            self.line(P, width * (1 if k == 0 else 0.8), fill, alpha * (1 if k == 0 else second), var=var, dash=dash)

    def arrow_head(self, tip, direction, size=14, fill=TEXT, var=None, mode='fade'):
        """a filled arrowhead at board point `tip` pointing along `direction` (degrees, 0 = right, 90 = down)"""
        a = np.deg2rad(direction)
        R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        P = (np.array([(1.5, 0), (-size, -size * 0.55), (-size * 0.75, 0), (-size, size * 0.55)]) @ R.T) + np.asarray(tip)
        self.poly(P, fill, var=var, mode=mode)

    # ------------------------------------------------------------ the window (screen space, drawn once)
    def _screen_target(self, rgb):
        self._tg = _Target(rgb)
        self._k, self._ox, self._oy = 1.0, 0.0, 0.0
        self._clip_s = None

    def _build_chrome(self):
        out = np.ones((self.H, self.W, 3), np.float32) * hexc(PAGE)
        self._screen_target(out)
        if self.glow:   # a faint violet pool of light on the page, top left
            g = self._grid(0, 0, self.W, self.H)
            sl, X, Y = g
            t = np.hypot((X - 400) / 700, (Y + 150) / 650)
            self._over(sl, 0.2 * np.clip(1 - t, 0, 1), ACCENT)
        W_ = self.win
        x, y, x1, y1 = W_.x0, W_.y0, W_.x1, W_.y1
        self._s_shadow(x, y, x1, y1, 14, 0, 40, 90, -30, '#000000', 0.8)
        self._s_rrect(x, y, x1, y1, 14, '#3a3a3a', 1.0, 1.0, inset=False)
        self._s_rrect(x, y, x1, y1, 14, BG)
        self._clip_s = (x, y, x1, y1, 14)
        bh = self.bar_h
        self._s_rrect(x, y, x1, y + bh, 0, SIDE)
        self._s_rrect(x, y + bh - 1, x1, y + bh, 0, BORDER)
        if self.ribbon:
            rw = self.rib_w
            self._s_rrect(x, y + bh, x + rw, y1, 0, SIDE)
            self._s_rrect(x + rw - 1, y + bh, x + rw, y1, 0, BORDER)
            for i, gname in enumerate(RIBBON):
                self._s_glyph(gname, x + rw / 2, y + bh + 20 + 12 + i * 44, 24, FAINT, 1.8)
        for i, c in enumerate(LIGHTS):
            self._s_circle(x + 18 + 6.5 + i * 22, y + bh / 2, 6.5, c)
        if self.tab:
            tx = x + 18 + 57 + 22 + 30
            tw = self._glyphs(self.tab, 20, 'medium', 0, 'sans')[1]
            xw = self._glyphs('×', 18, 'medium', 0, 'sans')[1]
            tx1 = tx + 22 + tw + 12 + xw + 22
            ty0 = y + bh - 40
            self._s_rrect(tx, ty0, tx1, y + bh + 12, 10, BORDER)
            self._s_rrect(tx + 1, ty0 + 1, tx1 - 1, y + bh + 12, 9, BG)
            self._s_rrect(tx + 1, y + bh - 1, tx1 - 1, y + bh + 12, 0, BG)
            self._s_text(self.tab, tx + 22, ty0 + 20, 20, TEXT, 'medium', 'lm')
            self._s_text('×', tx + 22 + tw + 12, ty0 + 20, 18, FAINT, 'medium', 'lm')
        self._clip_s = None
        m = np.zeros((self.VH, self.VW), np.float32)
        p = self.pane
        X = np.arange(self.VW, dtype=np.float32)[None, :] + 0.5 + p.x0
        Y = np.arange(self.VH, dtype=np.float32)[:, None] + 0.5 + p.y0
        m[:] = _cov(sdf_rrect(X - (x + x1) / 2, Y - (y + y1) / 2, (x1 - x) / 2, (y1 - y) / 2, 14))
        self._pane_mask = m[..., None]
        self._chrome = out

    def _draw_controls(self, out):
        self._screen_target(out)
        x0 = self.pane.x1 - 18 - 50
        y0 = self.pane.y0 + 18
        h = 8 + 4 * 26 + 3 * 14 + 8
        self._s_shadow(x0, y0, x0 + 50, y0 + h, 10, 0, 10, 24, -12, '#000000', 0.8)
        self._s_rrect(x0, y0, x0 + 50, y0 + h, 10, BG2)
        self._s_rrect(x0, y0, x0 + 50, y0 + h, 10, BORDER, 1.0, 1.0)
        for i, gname in enumerate(CONTROLS):
            cx, cy = x0 + 25, y0 + 8 + 13 + i * 40
            if self.hover == i:
                self._s_rrect(cx - 19, cy - 17, cx + 19, cy + 17, 7, BG3)
            self._s_glyph(gname, cx, cy, 26, BRIGHT if self.hover == i else MUTED, 1.9)

    def _draw_cursor(self, out):
        x, y, click, alpha, press = self._cursor
        self._screen_target(out)
        if click is not None and 0 < click < 1:
            self._s_circle(x, y, 26 * (0.4 + click), ACCENT2, alpha * (1 - click), ring=3.0)
        s = 0.88 if press else 1.0
        P = (np.array(POINTER, np.float32) - 2) * s + np.array([x, y])
        sh = P + np.array([0, 4])
        g = self._grid(sh[:, 0].min() - 10, sh[:, 1].min() - 10, sh[:, 0].max() + 10, sh[:, 1].max() + 10)
        if g:
            sl, X, Y = g
            im = Image.new('L', (sl[1].stop - sl[1].start, sl[0].stop - sl[0].start), 0)
            ImageDraw.Draw(im).polygon([(px - sl[1].start, py - sl[0].start) for px, py in sh.tolist()], fill=255)
            m = blur(np.asarray(im, np.float32) / 255, 3)
            self._over(sl, m * 0.45 * alpha, '#000000')
        self._s_poly(P, '#111111', alpha)
        c = P.mean(0)
        self._s_poly(c + (P - c) * 0.86 + np.array([0.0, -0.2]), WHITE, alpha)

    # ------------------------------------------------------------ compositing
    def _board(self):
        """the pane: board colour and the dot grid for the current camera"""
        cx, cy, z = self.cam
        P = np.empty((self.VH, self.VW, 3), np.float32)
        P[:] = hexc(BOARD)
        g = self.grid
        X = (np.arange(self.VW, dtype=np.float32) + 0.5 - self.VW / 2) / z + cx
        Y = (np.arange(self.VH, dtype=np.float32) + 0.5 - self.VH / 2) / z + cy
        dx = ((X + g / 2) % g - g / 2) * z
        dy = ((Y + g / 2) % g - g / 2) * z
        r = max(self.dot_r * z, 1.05)
        d = np.sqrt(dx[None, :] ** 2 + dy[:, None] ** 2)
        cov = np.clip(r + 0.5 - d, 0, 1) * min(1.0, 0.55 + 0.45 * z)
        P += (hexc(DOT) - hexc(BOARD)) * cov[..., None]
        return P

    def _xf(self, N):
        p = N.pose
        s = p['scale']
        if p['origin'] is not None: ox, oy = p['origin']
        elif N.rect is not None: ox, oy = N.rect.cx, N.rect.cy
        elif N.box is not None: ox, oy = (N.box[0] + N.box[2]) / 2, (N.box[1] + N.box[3]) / 2
        else: ox = oy = 0.0
        cx, cy, z = self.cam
        return s * z, self.VW / 2 + (ox * (1 - s) + p['dx'] - cx) * z, self.VH / 2 + (oy * (1 - s) + p['dy'] - cy) * z

    def _draw_node(self, N):
        for pr in N.prims:
            if pr.var is None: t = 1.0
            else:
                v = N.var(pr.var[0]); t = float(np.clip((v - pr.var[1]) / max(pr.var[2] - pr.var[1], 1e-6), 0, 1))
            if pr.clip is not None:
                x0, y0 = self._S(pr.clip[0], pr.clip[1]); x1, y1 = self._S(pr.clip[2], pr.clip[3])
                self._clip_s = (x0, y0, x1, y1, pr.clip[4] * self._k)
            else:
                self._clip_s = None
            pr.fn(t)
        self._clip_s = None

    def render(self):
        """composite the page, the window and the board under the current camera and poses -> float RGB"""
        if self._chrome is None: self._build_chrome()
        out = self._chrome.copy()
        P = self._board()
        for N in sorted(self.nodes.values(), key=lambda q: (q.z, q.order)):
            al = N.pose['alpha']
            if al <= 0 or N.box is None: continue
            k, ox, oy = self._xf(N)
            bx0, by0, bx1, by1 = N.box[0] * k + ox, N.box[1] * k + oy, N.box[2] * k + ox, N.box[3] * k + oy
            if bx1 < 0 or by1 < 0 or bx0 > self.VW or by0 > self.VH: continue
            self._drawing = N
            if al >= 0.999:
                self._tg = _Target(P)
                self._k, self._ox, self._oy = k, ox, oy
                self._draw_node(N)
            else:
                X0, Y0 = max(0, int(np.floor(bx0))), max(0, int(np.floor(by0)))
                X1, Y1 = min(self.VW, int(np.ceil(bx1)) + 1), min(self.VH, int(np.ceil(by1)) + 1)
                if X1 <= X0 or Y1 <= Y0: continue
                L = _Target(np.zeros((Y1 - Y0, X1 - X0, 3), np.float32), np.zeros((Y1 - Y0, X1 - X0), np.float32), X0, Y0)
                self._tg = L
                self._k, self._ox, self._oy = k, ox - X0, oy - Y0
                self._draw_node(N)
                P[Y0:Y1, X0:X1] = P[Y0:Y1, X0:X1] * (1 - L.a[..., None] * al) + L.rgb * al
        p = self.pane
        sl = (slice(int(p.y0), int(p.y0) + self.VH), slice(int(p.x0), int(p.x0) + self.VW))
        out[sl] = out[sl] * (1 - self._pane_mask) + P * self._pane_mask
        if self.controls: self._draw_controls(out)
        if self._cursor: self._draw_cursor(out)
        self._tg = None
        return out

    def composite(self):
        I = self.render() + self._grain[..., None]
        return Image.fromarray((np.clip(I, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        """snapshot the current camera and poses (written to stages_dir at once if given, else kept PNG-compressed)"""
        if not self.keep_stages: return
        img = self.composite()
        if self.stages_dir:
            img.save(f'{self.stages_dir}/{self._nstage:03d}_{name}.png', compress_level=1)
        else:
            buf = io.BytesIO(); img.save(buf, 'PNG', compress_level=1)
            self.stages.append((name, buf.getvalue()))
        self._nstage += 1

    def tween(self, tag, n=5, ease='out', moves=(), cam=None, last=True, between=None, cam_ease='io'):
        """n stages of a motion: 'mv_<tag>1' .. 'mv_<tag>{n-1}' (in-betweens) and '<tag>' (unless last=False).
        moves: [(names, frm, to)]; frm / to are dicts of pose keys (dx dy scale alpha) and vars; to=None = at rest
        and finished. ease: a name in EASE (linear out io back drop) or a function. cam: (from, to) cameras (x, y, z),
        zoom interpolated geometrically, eased with cam_ease. between(u) is called with the eased progress before
        each stage"""
        E = EASE[ease] if isinstance(ease, str) else ease
        CE = EASE[cam_ease] if isinstance(cam_ease, str) else cam_ease
        REST = dict(dx=0.0, dy=0.0, scale=1.0, alpha=1.0)
        for i in range(1, n + 1):
            u = E(i / n)
            for names, frm, to in moves:
                names = [names] if isinstance(names, str) else names
                to = to or {}
                for nm in names:
                    N = self.nodes[nm]
                    pose = dict(N.pose)
                    for key in REST:
                        if key in frm or key in to:
                            a = frm.get(key, REST[key]); b = to.get(key, REST[key])
                            pose[key] = a + (b - a) * u
                    pose['alpha'] = float(np.clip(pose['alpha'], 0, 1))
                    N.pose = pose
                    for key in set(frm) | set(to):
                        if key in REST: continue
                        a = frm.get(key, N.defaults.get(key, 1.0)); b = to.get(key, N.defaults.get(key, 1.0))
                        N.vars[key] = a + (b - a) * u
            if cam:
                (x0, y0, z0), (x1, y1, z1) = cam
                c = CE(i / n)
                self.camera(x0 + (x1 - x0) * c, y0 + (y1 - y0) * c, z0 * (z1 / z0) ** c)
            if between: between(u)
            if i < n: self.stage(f'mv_{tag}{i}')
            elif last: self.stage(tag)

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir and not self.stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, png) in enumerate(self.stages):
                with open(f'{stages_dir}/{i:03d}_{name}.png', 'wb') as fh:
                    fh.write(png)
            img.save(f'{stages_dir}/{len(self.stages):03d}_final.png')
        elif self.stages_dir:
            img.save(f'{self.stages_dir}/{self._nstage:03d}_final.png')
        return img
