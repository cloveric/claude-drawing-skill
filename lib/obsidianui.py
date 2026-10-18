"""obsidianui — 笔记应用界面 / Obsidian UI: a dark note-taking app drawn in code (numpy + Pillow only).

The look of a Markdown note app in its default dark theme, as an explainer film shows it: a near-black page with a
soft violet glow, and on it the app window -- a tab bar with the traffic lights, a slim icon ribbon, a file explorer
(folders, indent guides, the open note highlighted), the note pane and a right sidebar. In the note: a big heavy H1
with a short violet bar under it, a properties block with #tags, body text with **bold**, internal links in violet and
`inline code`, a dark ```mermaid code block typed in mono with syntax colours -- which, flipped from 源码 to 阅读, renders
as a flowchart of flat dark boxes, thin grey edges with small arrowheads and one violet node -- and a callout with a
violet edge. In the sidebar, the graph view: grey nodes and links, the notes linked to this one lit violet with a soft
glow. ONE accent (violet), everything else greys. No logos.

  shapes      rounded rectangles, discs, rings, capsules and icon strokes are signed-distance fields with 1 px analytic
              anti-aliasing (pixel centres at i + 0.5, so integer coordinates give crisp edges); free polygons (the
              pointer, arrowheads, diamonds) are rasterised 4x and box-filtered.
  shadows     CSS box-shadow semantics (offset, blur radius, spread, colour, opacity), painted only outside the
              element; with zero offset it is the violet glow of a lit card. `halo()` is a soft radial glow (graph
              nodes, the H1 bar).
  window      `window()` draws the chrome: shadow and 1 px ring, title bar with lights and tabs (the active tab is
              open at the bottom and joins the note), ribbon icons, explorer and sidebar panes with hairline borders.
              It returns a Box with .note / .explorer / .right panes; contents are drawn with explorer(),
              view_header(), toggle(), sidebar_tools(), status_bar().
  type        PingFang SC (CJK; Lantinghei SC Heavy for the heavy H1), SF Pro (Latin, variable weight, slight negative
              tracking when large), SF Mono for code; script runs split automatically. Elsewhere Noto Sans CJK /
              Microsoft YaHei and the core fonts. Override with $INKPAINT_FONT_OBSIDIAN_<CJK|HEAVY|LATIN|MONO>.
              `rich()` lays out one line of note text from runs: plain, 'b', 'link', 'code', 'hl', 'faint', 'tag'.
  layers      everything is drawn into named layers (premultiplied RGBA, cropped to what was drawn). A layer has a
              depth and a pose -- offset, scale about an origin, opacity, a reveal (left to right, top to bottom, or a
              circle growing from the origin) -- so one drawing can be shown in many states: the window rising, a code
              line being typed, a node popping in, the graph growing out of the current note. `stage()` composites.

    import sys; sys.path.insert(0, 'lib')
    from obsidianui import ObsidianUI
    ob = ObsidianUI(1920, 1080, seed=1)
    ob.page()
    ob.layer('window')
    win = ob.window(120, 96, 1680, 880, tabs=['小王子', '狐狸'], side=300, right=480)
    ob.explorer(win, [('读书笔记', 0, 'open'), ('小王子', 1, 'file'), ('狐狸', 1, 'file')], active=1)
    ob.layer('note')
    ob.h1(win.note.x0 + 56, 300, '小王子')
    ob.rich(win.note.x0 + 56, 380, [('狐狸教他什么叫 ', None), ('驯养', 'code'), ('。', None)])
    ob.save('out.jpg')
"""
import glob
import io
import os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, load_font

# ---------------------------------------------------------------- palette (the app's default dark theme)
PAGE = '#161616'                                     # the film's page behind the window
BG, BG2, BG3, SIDE = '#1e1e1e', '#262626', '#2e2e2e', '#202020'
BORDER, BORDER2, RING = '#363636', '#444444', '#3a3a3a'
TEXT, BRIGHT, MUTED, FAINT = '#dadada', '#f2f2f2', '#a3a3a3', '#6b6b6b'
ACCENT, ACCENT2 = '#8a5cf5', '#a88bfa'               # the one accent and its lighter text tone
CODE_BG, CODE_TEXT, INLINE = '#1b1b1b', '#d4d4d4', '#e06c75'
SYNTAX = {'kw': '#c792ea', 'str': '#c3e88d', 'num': '#f78c6c', 'op': '#89ddff', 'cm': '#6b6b6b', 'fence': '#6b6b6b',
          'text': CODE_TEXT}
NODE_FILL, NODE_EDGE, NODE_LINE = '#2b2b2b', '#505050', '#b9b9b9'     # rendered diagram parts
LINK, GNODE = '#4a4a4a', '#8f8f8f'                                    # graph view
LIGHTS = ('#ff5f57', '#febc2e', '#28c840')
WHITE = '#ffffff'
ACCENTS = {  # the app lets you pick the accent: (accent, lighter text tone)
    'violet': (ACCENT, ACCENT2), 'blue': ('#3b82f6', '#7aa7f9'), 'teal': ('#14b8a6', '#5fd4c8'),
    'amber': ('#e59a16', '#f2bd5e'), 'rose': ('#e5486e', '#f08aa3'),
}

# line icons on a 24-unit grid (stroked): ('p', points, closed) polyline, ('c', cx, cy, r) circle, ('a', cx, cy, r, a0, a1)
# arc (degrees, 0 = +x, 90 = down), ('d', cx, cy, r) filled dot, ('r', x0, y0, x1, y1, radius) rounded rectangle
_EYE = [(3, 12), (5.2, 9.4), (8.2, 7.5), (12, 6.8), (15.8, 7.5), (18.8, 9.4), (21, 12)]
GLYPHS = {
    'menu': [('p', [(4, 6), (20, 6)]), ('p', [(4, 12), (20, 12)]), ('p', [(4, 18), (20, 18)])],
    'search': [('c', 11, 11, 6.5), ('p', [(16, 16), (20.5, 20.5)])],
    'file': [('p', [(6, 3), (14.5, 3), (18.5, 7), (18.5, 21), (6, 21)], True), ('p', [(14.5, 3), (14.5, 7), (18.5, 7)])],
    'files': [('p', [(8, 3), (15.5, 3), (19, 6.5), (19, 17), (8, 17)], True), ('p', [(5, 7), (5, 21), (15, 21)])],
    'plus': [('p', [(12, 5), (12, 19)]), ('p', [(5, 12), (19, 12)])],
    'grid': [('r', 4, 4, 10.5, 10.5, 1.5), ('r', 13.5, 4, 20, 10.5, 1.5), ('r', 4, 13.5, 10.5, 20, 1.5), ('r', 13.5, 13.5, 20, 20, 1.5)],
    'graph': [('c', 6, 7, 2.6), ('c', 18, 6, 2.6), ('c', 12, 18.5, 2.8), ('p', [(8.6, 6.8), (15.4, 6.2)]),
              ('p', [(7.3, 9.3), (10.6, 16.1)]), ('p', [(16.8, 8.4), (13.4, 16.1)])],
    'canvas': [('r', 3, 4, 21, 20, 2.5), ('r', 6.5, 7.5, 11.5, 12, 1), ('r', 12.5, 12, 17.5, 16.5, 1), ('p', [(11.5, 9.75), (15, 9.75), (15, 12)])],
    'calendar': [('r', 4, 5, 20, 20, 2), ('p', [(4, 9.5), (20, 9.5)]), ('p', [(8, 3), (8, 6.5)]), ('p', [(16, 3), (16, 6.5)])],
    'terminal': [('r', 3, 4, 21, 20, 2.5), ('p', [(7, 9), (10, 12), (7, 15)]), ('p', [(12.5, 15), (17, 15)])],
    'gear': [('c', 12, 12, 3), ('c', 12, 12, 7)] + [('p', [(12 + 7 * np.cos(a), 12 + 7 * np.sin(a)), (12 + 9.5 * np.cos(a), 12 + 9.5 * np.sin(a))])
                                                    for a in np.arange(8) * np.pi / 4 + np.pi / 8],
    'help': [('c', 12, 12, 9), ('a', 12, 9.6, 2.6, 180, 395), ('p', [(13.1, 12), (12, 13.6)]), ('d', 12, 16.8, 1.1)],
    'back': [('p', [(14.5, 5.5), (8, 12), (14.5, 18.5)])],
    'fwd': [('p', [(9.5, 5.5), (16, 12), (9.5, 18.5)])],
    'chev_d': [('p', [(7.5, 10), (12, 14.5), (16.5, 10)])],
    'chev_r': [('p', [(10, 7.5), (14.5, 12), (10, 16.5)])],
    'edit': [('p', [(4.5, 19.5), (5.2, 15.6), (15.5, 5.3), (18.7, 8.5), (8.4, 18.8)], True), ('p', [(13.4, 7.4), (16.6, 10.6)])],
    'folder_plus': [('p', [(3, 6), (3, 19), (21, 19), (21, 8.5), (11, 8.5), (9, 6)], True), ('p', [(12, 11.5), (12, 16.5)]), ('p', [(9.5, 14), (14.5, 14)])],
    'sort': [('p', [(7.5, 4.5), (7.5, 19.5)]), ('p', [(4.5, 16.5), (7.5, 19.5), (10.5, 16.5)]), ('p', [(16.5, 19.5), (16.5, 4.5)]),
             ('p', [(13.5, 7.5), (16.5, 4.5), (19.5, 7.5)])],
    'collapse': [('p', [(7.5, 4.5), (12, 9), (16.5, 4.5)]), ('p', [(7.5, 19.5), (12, 15), (16.5, 19.5)])],
    'list': [('p', [(4, 6), (20, 6)]), ('p', [(7.5, 12), (20, 12)]), ('p', [(11, 18), (20, 18)])],
    'layout': [('r', 4, 4, 20, 20, 2.5), ('p', [(4, 10), (20, 10)])],
    'bars': [('p', [(6, 19), (6, 10)]), ('p', [(12, 19), (12, 5)]), ('p', [(18, 19), (18, 13)])],
    'link': [('a', 8.5, 15.5, 4.2, 45, 225), ('a', 15.5, 8.5, 4.2, 225, 405), ('p', [(5.53, 12.53), (11.47, 6.6)]),
             ('p', [(12.53, 17.4), (18.47, 11.47)]), ('p', [(9.5, 14.5), (14.5, 9.5)])],
    'tag': [('p', [(4, 4), (11, 4), (20, 13), (13, 20), (4, 11)], True), ('d', 8.5, 8.5, 1.2)],
    'hash': [('p', [(9.5, 4), (7.5, 20)]), ('p', [(16.5, 4), (14.5, 20)]), ('p', [(4.5, 9), (20, 9)]), ('p', [(4, 15), (19.5, 15)])],
    'book': [('p', [(5, 19.5), (5, 5.5)]), ('a', 6.5, 5.5, 1.5, 180, 270), ('p', [(6.5, 4), (18, 4), (18, 18), (6.5, 18)]),
             ('a', 6.5, 19.5, 1.5, 90, 270), ('p', [(6.5, 21), (18, 21), (18, 18)])],
    'eye': [('p', _EYE), ('p', [(x, 24 - y) for x, y in _EYE]), ('c', 12, 12, 3)],
    'quote': [('d', 7.5, 9.5, 2.7), ('p', [(10.1, 10), (9.4, 13.4), (6.6, 16.6)]),
              ('d', 15.5, 9.5, 2.7), ('p', [(18.1, 10), (17.4, 13.4), (14.6, 16.6)])],
    'more': [('d', 5, 12, 1.3), ('d', 12, 12, 1.3), ('d', 19, 12, 1.3)],
    'check': [('p', [(5, 12.5), (9.5, 17), (19, 7)])],
    'x': [('p', [(7, 7), (17, 17)]), ('p', [(17, 7), (7, 17)])],
    'star': [('p', [(12, 3.5), (14.5, 9), (20.5, 9.5), (16, 13.5), (17.4, 19.6), (12, 16.4), (6.6, 19.6), (8, 13.5), (3.5, 9.5), (9.5, 9)], True)],
}
RIBBON = ['files', 'search', 'graph', 'canvas', 'calendar', 'terminal']
CURSOR = [(1, 1), (1, 25), (7.5, 19.5), (12, 30), (16, 28.3), (11.6, 18), (20, 18)]    # pointer, tip at (1, 1)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- signed distances (negative inside)
def sdf_rrect(u, v, hw, hh, r):
    r = min(r, hw, hh)
    qx, qy = np.abs(u) - (hw - r), np.abs(v) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sdf_segment(X, Y, a, b):
    ax, ay = float(a[0]), float(a[1]); bx, by = float(b[0]), float(b[1])
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy + 1e-9
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / l2, 0, 1)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy))


def sdf_polyline(X, Y, pts, closed=False):
    P = [tuple(p) for p in pts]
    if closed: P = P + [P[0]]
    d = np.full(np.broadcast(X, Y).shape, 1e9, np.float32)
    for a, b in zip(P[:-1], P[1:]):
        d = np.minimum(d, sdf_segment(X, Y, a, b))
    return d


def _cov(d):
    return np.clip(0.5 - d, 0, 1).astype(np.float32)


def _arc_pts(cx, cy, r, a0, a1):
    n = max(6, int(abs(a1 - a0) / 9))
    t = np.deg2rad(np.linspace(a0, a1, n))
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1)


# ---------------------------------------------------------------- fonts
_AD = '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
_CJK_FACES = [  # (glob, {weight: face index or file-name token}); first hit wins -- macOS, Linux, Windows
    (_AD + 'PingFang.ttc', {'regular': 3, 'medium': 7, 'semibold': 11, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/PingFang.ttc', {'regular': 3, 'medium': 7, 'semibold': 11, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/Hiragino Sans GB.ttc', {'regular': 0, 'medium': 0, 'semibold': 2, 'bold': 2, 'heavy': 2}),
    ('/usr/share/fonts/**/NotoSansCJK*-{W}.tt[cf]', {'regular': 'Regular', 'medium': 'Medium', 'semibold': 'Bold', 'bold': 'Bold', 'heavy': 'Black'}),
    ('/usr/share/fonts/**/NotoSansSC-{W}.[ot]tf', {'regular': 'Regular', 'medium': 'Medium', 'semibold': 'Bold', 'bold': 'Bold', 'heavy': 'Black'}),
    ('C:/Windows/Fonts/msyh{W}.ttc', {'regular': '', 'medium': '', 'semibold': 'bd', 'bold': 'bd', 'heavy': 'bd'}),
]
_HEAVY_FACES = [(_AD + 'Lantinghei.ttc', 2), ('/System/Library/Fonts/Lantinghei.ttc', 2)]
_LATIN_W = {'regular': 400, 'medium': 510, 'semibold': 590, 'bold': 680, 'heavy': 790}
_MONO_W = {'regular': 400, 'medium': 500, 'semibold': 600, 'bold': 680, 'heavy': 800}
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
    env = os.environ.get('INKPAINT_FONT_OBSIDIAN_HEAVY' if weight == 'heavy' else 'INKPAINT_FONT_OBSIDIAN_CJK')
    if env and os.path.exists(env):
        return ImageFont.truetype(env, size), 0
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
        if f:
            fake = max(1, round(size / 46)) if weight == 'heavy' and 'Black' not in p else 0
            return f, fake
    return load_font('cjk_sans', size), (max(1, round(size / 40)) if weight in ('semibold', 'bold', 'heavy') else 0)


def _latin(weight, size, mono=False):
    env = os.environ.get('INKPAINT_FONT_OBSIDIAN_' + ('MONO' if mono else 'LATIN'))
    if env and os.path.exists(env):
        return ImageFont.truetype(env, size)
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
    """a rectangle in canvas pixels (window, panes, blocks, nodes)"""

    def __init__(self, x0, y0, x1, y1, r=0.0):
        self.x0, self.y0, self.x1, self.y1, self.r = x0, y0, x1, y1, r
        self.w, self.h = x1 - x0, y1 - y0
        self.cx, self.cy = (x0 + x1) / 2, (y0 + y1) / 2

    def __iter__(self):
        return iter((self.x0, self.y0, self.x1, self.y1))


class Layer:
    def __init__(self, name, z, order, W, H):
        self.name, self.z, self.order = name, z, order
        self.rgb = np.zeros((H, W, 3), np.float32)     # premultiplied
        self.a = np.zeros((H, W), np.float32)
        self.x0 = self.y0 = 0
        self.open = True
        self.pose = dict(dx=0.0, dy=0.0, scale=1.0, alpha=1.0, reveal=1.0, mode='x', origin=None, feather=14.0)


# ---------------------------------------------------------------- the canvas
class ObsidianUI:
    GLYPHS = GLYPHS
    ACCENTS = ACCENTS

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, accent='violet'):
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages = keep_stages
        self.stages = []
        self.accent, self.accent2 = ACCENTS[accent] if isinstance(accent, str) else accent
        self.base = np.ones((H, W, 3), np.float32) * hexc(PAGE)
        self.layers = {}
        self.cur = None
        self._clip = None
        g = np.random.default_rng(seed + 7).random((H, W)).astype(np.float32)
        self._grain = (g - 0.5) * (1.4 / 255)            # fixed sub-level dither: no banding in the dark glows

    # ------------------------------------------------------------ layers
    def layer(self, name, z=None):
        """start drawing into layer `name` (re-opens it if it exists). z: depth (default: creation order)"""
        self._close()
        if name in self.layers:
            L = self.layers[name]
            full_rgb = np.zeros((self.H, self.W, 3), np.float32); full_a = np.zeros((self.H, self.W), np.float32)
            h, w = L.a.shape
            full_rgb[L.y0:L.y0 + h, L.x0:L.x0 + w] = L.rgb; full_a[L.y0:L.y0 + h, L.x0:L.x0 + w] = L.a
            L.rgb, L.a, L.x0, L.y0, L.open = full_rgb, full_a, 0, 0, True
            if z is not None: L.z = z
        else:
            n = len(self.layers)
            L = Layer(name, n if z is None else z, n, self.W, self.H)
            self.layers[name] = L
        self.cur = L
        return name

    def end(self):
        """stop drawing into the current layer (later drawing goes onto the page)"""
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

    def pose(self, name, dx=0.0, dy=0.0, scale=1.0, alpha=1.0, reveal=1.0, mode='x', origin=None, feather=14.0):
        """how layer `name` is shown: offset, scale about `origin` (default: its centre), opacity and a reveal
        0..1 with a soft edge `feather` px -- mode 'x' left to right (typing), 'y' top to bottom, 'r' a circle
        growing from `origin` (the graph growing out of a node). pose(name) = drawn as is"""
        self.layers[name].pose = dict(dx=dx, dy=dy, scale=scale, alpha=alpha, reveal=reveal, mode=mode, origin=origin,
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
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1)) + 1), min(self.H, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None
        X = np.arange(x0, x1, dtype=np.float32)[None, :] + 0.5
        Y = np.arange(y0, y1, dtype=np.float32)[:, None] + 0.5
        return (slice(y0, y1), slice(x0, x1)), X, Y

    def _over(self, sl, cov, col):
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

    # ------------------------------------------------------------ the page
    def page(self, colour=PAGE, glows=((400, 150, 700, 550, 0.20), (1670, 1030, 650, 550, 0.12))):
        """the dark page behind the window, with soft violet glows: (cx, cy, rx, ry, alpha) ellipses fading
        linearly to nothing at their edge (CSS radial-gradient closest-side)"""
        self.base[:] = hexc(colour)
        old, self.cur = self.cur, None
        for cx, cy, rx, ry, al in glows or ():
            g = self._grid(cx - rx, cy - ry, cx + rx, cy + ry)
            if not g: continue
            sl, X, Y = g
            t = np.hypot((X - cx) / rx, (Y - cy) / ry)
            self._over(sl, al * np.clip(1 - t, 0, 1), self.accent)
        self.cur = old

    # ------------------------------------------------------------ shapes
    def rrect(self, x0, y0, x1, y1, r=0.0, fill=BG, alpha=1.0, ring=0.0, inset=True):
        """rounded rectangle; ring=w draws only a w px line along the edge (inside if inset, else outside)"""
        g = self._grid(x0 - ring - 2, y0 - ring - 2, x1 + ring + 2, y1 + ring + 2)
        if not g: return None
        sl, X, Y = g
        d = sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r)
        if ring:
            d = np.abs(d + ring / 2) - ring / 2 if inset else np.abs(d - ring / 2) - ring / 2
        self._over(sl, _cov(d) * alpha, fill)

    def circle(self, cx, cy, r, fill=GNODE, alpha=1.0, ring=0.0):
        g = self._grid(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        if not g: return None
        sl, X, Y = g
        d = np.hypot(X - cx, Y - cy) - r
        if ring: d = np.abs(d + ring / 2) - ring / 2
        self._over(sl, _cov(d) * alpha, fill)

    def line(self, pts, width=2.0, fill=TEXT, alpha=1.0, closed=False):
        """polyline with round caps and joins"""
        P = np.asarray(pts, np.float32)
        pad = width / 2 + 2
        g = self._grid(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if not g: return None
        sl, X, Y = g
        self._over(sl, _cov(sdf_polyline(X, Y, P, closed) - width / 2) * alpha, fill)

    def poly(self, pts, fill=TEXT, alpha=1.0, ss=4):
        """filled polygon, rasterised ss x and box-filtered"""
        P = np.asarray(pts, np.float32)
        x0, y0 = int(np.floor(P[:, 0].min())) - 1, int(np.floor(P[:, 1].min())) - 1
        x1, y1 = int(np.ceil(P[:, 0].max())) + 2, int(np.ceil(P[:, 1].max())) + 2
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P.tolist()], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        g = self._grid(x0, y0, x1 - 1, y1 - 1)
        if not g: return None
        sl = g[0]
        m = m[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0]
        self._over(sl, m * alpha, fill)
        return m

    def shadow(self, x0, y0, x1, y1, r=0.0, dx=0.0, dy=0.0, blur_px=0.0, spread=0.0, colour='#000000', alpha=0.5,
               shape=None):
        """CSS box-shadow of a rounded rectangle, painted only outside the element (zero offset = a glow).
        shape=(cx, cy, r) casts the shadow of a disc instead"""
        sig = blur_px / 2
        pad = 3 * sig + abs(spread) + 3
        if shape is not None:
            cx, cy, rr = shape
            x0, y0, x1, y1 = cx - rr, cy - rr, cx + rr, cy + rr
        g = self._grid(min(x0, x0 + dx) - pad, min(y0, y0 + dy) - pad, max(x1, x1 + dx) + pad, max(y1, y1 + dy) + pad)
        if not g: return
        sl, X, Y = g
        if shape is not None:
            m = _cov(np.hypot(X - cx - dx, Y - cy - dy) - (rr + spread))
            own = _cov(np.hypot(X - cx, Y - cy) - rr)
        else:
            sx0, sy0, sx1, sy1 = x0 - spread + dx, y0 - spread + dy, x1 + spread + dx, y1 + spread + dy
            if sx1 <= sx0 or sy1 <= sy0: return
            m = _cov(sdf_rrect(X - (sx0 + sx1) / 2, Y - (sy0 + sy1) / 2, (sx1 - sx0) / 2, (sy1 - sy0) / 2, max(0.0, r + spread)))
            own = _cov(sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r))
        if sig > 0.3: m = blur(m, sig)
        self._over(sl, m * (1 - own) * alpha, colour)

    def soft_shadow(self, cov, box, dx=0.0, dy=4.0, blur_px=6.0, colour='#000000', alpha=0.6):
        """drop shadow of any coverage mask `cov` whose top-left pixel is at box[:2] (CSS drop-shadow)"""
        sig = blur_px / 2
        pad = int(3 * sig + 3 + max(abs(dx), abs(dy)))
        h, w = cov.shape
        m = np.zeros((h + 2 * pad, w + 2 * pad), np.float32)
        m[pad:pad + h, pad:pad + w] = cov
        if sig > 0.3: m = blur(m, sig)
        x0, y0 = int(box[0]) - pad + int(round(dx)), int(box[1]) - pad + int(round(dy))
        g = self._grid(x0, y0, x0 + m.shape[1] - 1, y0 + m.shape[0] - 1)
        if not g: return
        sl = g[0]
        self._over(sl, m[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0] * alpha, colour)

    def halo(self, cx, cy, r, colour=None, alpha=0.5, power=2.0):
        """soft radial glow fading to nothing at radius r (lit graph nodes, the glow under a bar)"""
        g = self._grid(cx - r, cy - r, cx + r, cy + r)
        if not g: return
        sl, X, Y = g
        t = np.clip(1 - np.hypot(X - cx, Y - cy) / r, 0, 1)
        self._over(sl, alpha * t ** power, colour or self.accent)

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

    def text(self, s, x, y, size, fill=TEXT, weight='regular', anchor='ls', alpha=1.0, spacing=0.0, family='sans',
             halo=0, halo_fill=SIDE):
        """text (CJK / Latin runs split automatically). weight: regular / medium / semibold / bold / heavy;
        family: sans / mono. anchor: [l m r] + [s baseline, m middle of the CJK body, t top of the CJK body].
        halo=px first lays a halo_fill outline that px wide (graph labels: links stop short of the words).
        Returns the width"""
        size = int(round(size))
        gl, tw = self._glyphs(s, size, weight, spacing, family)
        x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        base = y + {'s': 0.0, 'm': 0.37 * size, 't': 0.86 * size}[anchor[1]]
        bx0, by0 = int(np.floor(x0)) - 6 - halo, int(np.floor(base - size * 1.25)) - halo
        bw, bh = int(tw) + 14 + 2 * halo, int(size * 1.65) + 8 + 2 * halo
        g = self._grid(bx0, by0, bx0 + bw - 1, by0 + bh - 1)
        if not g: return tw
        sl = g[0]
        for extra, col in ([(halo, halo_fill)] if halo else []) + [(0, fill)]:
            im = Image.new('L', (bw, bh), 0)
            dr = ImageDraw.Draw(im)
            for f, piece, off, fake in gl:
                dr.text((x0 - bx0 + off, base - by0), piece, font=f, fill=255, anchor='ls', stroke_width=fake + extra,
                        stroke_fill=255)
            m = np.asarray(im, np.float32) / 255
            m = m[sl[0].start - by0:sl[0].stop - by0, sl[1].start - bx0:sl[1].stop - bx0]
            self._over(sl, m * alpha, col)
        return tw

    def rich(self, x, base, runs, size=26, fill=TEXT, weight='regular', alpha=1.0):
        """one line of note text from runs [(text, style), ...] on baseline `base`; style None (body), 'b' (bold,
        bright), 'link' (internal link, accent text), 'code' (inline code: mono on a rounded dark chip), 'hl'
        (accent highlight behind bright bold words), 'faint', 'accent', 'tag' (#tag pill). Returns the end x"""
        for s, st in runs:
            if st is None:
                x += self.text(s, x, base, size, fill, weight, alpha=alpha)
            elif st == 'b':
                x += self.text(s, x, base, size, BRIGHT, 'semibold', alpha=alpha)
            elif st == 'link':
                x += self.text(s, x, base, size, self.accent2, weight, alpha=alpha)
            elif st == 'faint':
                x += self.text(s, x, base, size, FAINT, weight, alpha=alpha)
            elif st == 'accent':
                x += self.text(s, x, base, size, self.accent2, 'semibold', alpha=alpha)
            elif st == 'code':
                cs = size * 0.86
                tw = self.measure(s, cs, family='mono')
                self.rrect(x + 3, base - size * 0.9, x + 3 + tw + 16, base + size * 0.3, 6, BG3, alpha)
                self.text(s, x + 11, base - size * 0.02, cs, INLINE, family='mono', alpha=alpha)
                x += tw + 22
            elif st == 'hl':
                tw = self.measure(s, size, 'semibold')
                self.rrect(x + 2, base - size * 0.98, x + tw + 18, base + size * 0.3, 8, self.accent, 0.5 * alpha)
                self.text(s, x + 10, base, size, BRIGHT, 'semibold', alpha=alpha)
                x += tw + 20
            elif st == 'tag':
                x = self.tag(x, base - size * 0.37, s, size * 0.8) + 8
        return x

    # ------------------------------------------------------------ icons
    def glyph(self, name, cx, cy, size=22, fill=FAINT, sw=1.8, alpha=1.0):
        """a line icon from GLYPHS (24-unit grid, stroke sw in grid units), centred on (cx, cy)"""
        k = size / 24.0
        pad = size * 0.6 + 2
        g = self._grid(cx - pad, cy - pad, cx + pad, cy + pad)
        if not g: return
        sl, X, Y = g
        u, v = (X - cx) / k + 12, (Y - cy) / k + 12
        d = np.full(np.broadcast(u, v).shape, 1e9, np.float32)
        for p in GLYPHS[name]:
            kind = p[0]
            if kind == 'p':
                e = sdf_polyline(u, v, p[1], len(p) > 2 and p[2]) - sw / 2
            elif kind == 'c':
                e = np.abs(np.hypot(u - p[1], v - p[2]) - p[3]) - sw / 2
            elif kind == 'a':
                e = sdf_polyline(u, v, _arc_pts(*p[1:])) - sw / 2
            elif kind == 'd':
                e = np.hypot(u - p[1], v - p[2]) - p[3]
            else:  # 'r'
                x0, y0, x1, y1, rr = p[1:]
                e = np.abs(sdf_rrect(u - (x0 + x1) / 2, v - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, rr)) - sw / 2
            d = np.minimum(d, e)
        self._over(sl, _cov(d * k) * alpha, fill)

    # ------------------------------------------------------------ the app window
    def lights(self, x, cy, d=13, gap=9):
        for i, c in enumerate(LIGHTS):
            self.circle(x + d / 2 + i * (d + gap), cy, d / 2, c)

    def window(self, x, y, w, h, tabs=('未命名',), active=0, side=300, right=0, bar=52, ribbon=52, radius=14,
               ribbon_icons=RIBBON, lit_icon=None, tab_x=None):
        """the app window: shadow and 1 px ring, title bar (lights, tabs -- the active one open at the bottom so it
        joins the note -- and a + for a new tab), the icon ribbon, an explorer pane `side` px from the left edge
        (ribbon included; 0 = none) and a right sidebar `right` px wide (0 = none). Returns a Box with .bar (y of
        the title bar's bottom), .explorer, .note, .right (pane Boxes) and .tabs (tab Boxes)"""
        self.shadow(x, y, x + w, y + h, radius, 0, 40, 90, -30, '#000000', 0.8)
        self.rrect(x, y, x + w, y + h, radius, RING, ring=1.0, inset=False)
        self.rrect(x, y, x + w, y + h, radius, BG)
        yb = y + bar
        with self.clip(x, y, x + w, y + h, radius):
            self.rrect(x, y, x + w, yb, 0, SIDE)
            self.rrect(x, yb - 1, x + w, yb, 0, BORDER)
            self.rrect(x, yb, x + ribbon, y + h, 0, SIDE)
            self.rrect(x + ribbon - 1, yb, x + ribbon, y + h, 0, BORDER)
            if side:
                self.rrect(x + ribbon, yb, x + side, y + h, 0, SIDE)
                self.rrect(x + side - 1, yb, x + side, y + h, 0, BORDER)
            if right:
                self.rrect(x + w - right, yb, x + w, y + h, 0, SIDE)
                self.rrect(x + w - right, yb, x + w - right + 1, y + h, 0, BORDER)
        self.lights(x + 18, y + bar / 2)
        # tabs
        tx = tab_x if tab_x is not None else (x + side + 14 if side else x + 150)
        boxes = []
        for i, t in enumerate(tabs):
            on = i == active
            tw = self.measure(t, 19, 'semibold')
            x1 = tx + 22 + tw + 14 + 16 + 18
            b = Box(tx, yb - 40, x1, yb)
            if on:
                with self.clip(tx - 1, yb - 41, x1 + 1, yb + 1):
                    self.rrect(tx - 1, yb - 41, x1 + 1, yb + 12, 11, BORDER)
                    self.rrect(tx, yb - 40, x1, yb + 12, 10, BG)
            elif i and i - 1 != active:
                self.rrect(tx - 1, yb - 29, tx, yb - 11, 0, BORDER)
            self.text(t, tx + 22, yb - 20, 19, TEXT if on else MUTED, 'semibold', 'lm')
            self.glyph('x', x1 - 26, yb - 20, 15, FAINT if on else '#575757', 2.2)
            boxes.append(b)
            tx = x1 + 2
        self.glyph('plus', tx + 22, yb - 20, 19, FAINT, 2.0)
        self.glyph('chev_d', x + w - 34, y + bar / 2, 18, FAINT, 2.0)
        # ribbon
        for i, nm in enumerate(ribbon_icons):
            self.glyph(nm, x + ribbon / 2, yb + 30 + i * 46, 22, self.accent2 if nm == lit_icon else FAINT, 1.8)
        for i, nm in enumerate(['help', 'gear']):
            self.glyph(nm, x + ribbon / 2, y + h - 74 + i * 44, 22, FAINT, 1.8)
        B = Box(x, y, x + w, y + h, radius)
        B.bar, B.tabs = yb, boxes
        B.explorer = Box(x + ribbon, yb, x + side, y + h) if side else None
        B.note = Box(x + (side or ribbon), yb, x + w - right, y + h)
        B.right = Box(x + w - right, yb, x + w, y + h) if right else None
        return B

    def explorer(self, win, items, active=None, size=20, row=40, top=None, tools=True):
        """the file explorer in win.explorer: a row of small tool icons, then items (label, depth, kind) with kind
        'open' (expanded folder), 'folder' (collapsed) or 'file'; the `active` index gets the highlight. Nested items
        hang off a faint indent guide. Returns a list of the rows' Boxes"""
        E = win.explorer
        if tools:
            names = ['edit', 'folder_plus', 'sort', 'collapse']
            for i, nm in enumerate(names):
                self.glyph(nm, E.cx + (i - 1.5) * 42, E.y0 + 30, 19, FAINT, 1.8)
        y = (top if top is not None else E.y0 + 66)
        rows, stack = [], []
        for i, (label, depth, kind) in enumerate(items):
            ix = E.x0 + 16 + depth * 20
            b = Box(E.x0 + 10, y, E.x1 - 10, y + row - 4, 6)
            if i == active:
                self.rrect(b.x0 + depth * 20, b.y0, b.x1, b.y1, 6, BG3)
            cy = b.cy
            if kind in ('open', 'folder'):
                self.glyph('chev_d' if kind == 'open' else 'chev_r', ix + 8, cy, 16, FAINT, 2.2)
                self.text(label, ix + 24, cy, size, MUTED, 'medium', 'lm')
            else:
                self.text(label, ix + 24, cy, size, BRIGHT if i == active else MUTED, 'medium' if i == active else 'regular', 'lm')
            rows.append(b)
            y += row
        # indent guides: from under each open folder's chevron down to its last child
        for i, (label, depth, kind) in enumerate(items):
            if kind != 'open': continue
            j = i + 1
            while j < len(items) and items[j][1] > depth: j += 1
            if j > i + 1:
                gx = E.x0 + 16 + depth * 20 + 8
                self.rrect(gx - 0.5, rows[i + 1].y0 + 2, gx + 0.5, rows[j - 1].y1 - 2, 0, BORDER2, 0.8)
        return rows

    def view_header(self, win, crumbs, size=17, h=56):
        """the note's view header: back / forward arrows and a breadcrumb (last crumb bright), with a more-icon
        at the right end. Returns the header Box"""
        N = win.note
        cy = N.y0 + h / 2
        self.glyph('back', N.x0 + 26, cy, 19, FAINT, 2.0)
        self.glyph('fwd', N.x0 + 56, cy, 19, '#4e4e4e', 2.0)
        parts = list(crumbs)
        widths = [self.measure(c, size, 'medium') for c in parts]
        sep = self.measure(' / ', size)
        total = sum(widths) + sep * (len(parts) - 1)
        x = N.cx - total / 2
        for i, c in enumerate(parts):
            last = i == len(parts) - 1
            x += self.text(c, x, cy, size, TEXT if last else FAINT, 'medium', 'lm')
            if not last: x += self.text(' / ', x, cy, size, '#555555', 'regular', 'lm')
        self.glyph('more', N.x1 - 28, cy, 19, FAINT, 1.8)
        return Box(N.x0, N.y0, N.x1, N.y0 + h)

    def toggle(self, x, y, w, h=44, labels=('源码', '阅读'), on=1, size=19):
        """segmented switch (source / reading): dark track with a 1 px ring, the `on` segment filled with the accent
        and white text, the other muted"""
        self.rrect(x, y, x + w, y + h, 11, BG3)
        self.rrect(x, y, x + w, y + h, 11, BORDER2, ring=1.0)
        n = len(labels)
        sw = (w - 8 - 4 * (n - 1)) / n
        for i, t in enumerate(labels):
            sx = x + 4 + i * (sw + 4)
            if i == on:
                self.shadow(sx, y + 4, sx + sw, y + h - 4, 8, 0, 0, 14, 0, self.accent, 0.35)
                self.rrect(sx, y + 4, sx + sw, y + h - 4, 8, self.accent)
            self.text(t, sx + sw / 2, y + h / 2, size, WHITE if i == on else MUTED, 'semibold', 'mm')
        return Box(x, y, x + w, y + h, 11)

    def sidebar_tools(self, win, icons=('link', 'graph', 'list'), lit=1, h=56):
        """the right sidebar's header row: small tab icons (the `lit` one in the accent) over a hairline"""
        R = win.right
        for i, nm in enumerate(icons):
            self.glyph(nm, R.x0 + 38 + i * 44, R.y0 + h / 2, 21, self.accent2 if i == lit else FAINT, 1.9)
        self.rrect(R.x0 + 20, R.y0 + h - 1, R.x1 - 20, R.y0 + h, 0, BORDER)
        return R.y0 + h

    def status_bar(self, win, items, size=15):
        """the floating status bar in the window's bottom-right corner (rounded top-left, hairline edge)"""
        gap = 22
        widths = [self.measure(t, size) for t in items]
        w = sum(widths) + gap * (len(items) - 1) + 32
        x1, y1 = win.x1, win.y1
        x0, y0 = x1 - w, y1 - 34
        with self.clip(win.x0, win.y0, win.x1, win.y1, win.r):
            self.rrect(x0 - 1, y0 - 1, x1 + 20, y1 + 20, 9, BORDER)
            self.rrect(x0, y0, x1 + 20, y1 + 20, 8, SIDE)
        x = x0 + 16
        for t, tw in zip(items, widths):
            self.text(t, x, y0 + 17, size, FAINT, 'regular', 'lm')
            x += tw + gap
        return Box(x0, y0, x1, y1)

    # ------------------------------------------------------------ note content
    def h1(self, x, base, s, size=80, fill=BRIGHT, bar=True, bar_w=None, bar_gap=18, weight='heavy', draw_text=True):
        """the note's H1 (heavy, slightly tight tracking for Latin) with a short accent bar and its glow under it.
        bar=False / draw_text=False draw only one of the two (put them in two layers to animate the bar).
        Returns (width, bar Box or None)"""
        latin = not any(_is_cjk(c) for c in s)
        sp = -size * 0.02 if latin else 0.0
        tw = self.measure(s, size, weight, sp)
        if draw_text:
            self.text(s, x, base, size, fill, weight, spacing=sp)
        bb = None
        if bar:
            bw = bar_w or min(tw, 230)
            y0 = base + bar_gap
            self.shadow(x, y0, x + bw, y0 + 7, 3.5, 0, 0, 18, 0, self.accent, 0.55)
            self.rrect(x, y0, x + bw, y0 + 7, 3.5, self.accent)
            bb = Box(x, y0, x + bw, y0 + 7, 3.5)
        return tw, bb

    def heading(self, x, base, s, size=40, fill=BRIGHT, marker=False):
        """an H2 / H3 (marker=True also shows the faint ## of the source view)"""
        if marker:
            x += self.text('## ', x, base, size * 0.7, FAINT, 'semibold') + 4
        return self.text(s, x, base, size, fill, 'bold')

    def tag(self, x, cy, s, size=20):
        """#tag pill: accent text on a 20 % accent capsule. Returns the right edge"""
        tw = self.measure(s, size, 'medium')
        h = size * 1.5
        self.rrect(x, cy - h / 2, x + tw + size * 1.2, cy + h / 2, h / 2, self.accent, 0.2)
        self.text(s, x + size * 0.6, cy, size, self.accent2, 'medium', 'lm')
        return x + tw + size * 1.2

    def prop(self, x, cy, glyph, key, key_w=150, size=19):
        """one row of the properties block: icon + key in faint grey; the value starts at the returned x"""
        self.glyph(glyph, x + 10, cy, size, FAINT, 1.9)
        self.text(key, x + 32, cy, size, MUTED, 'regular', 'lm')
        return x + key_w

    def code_line(self, x, base, toks, size=24):
        """one line of a code block: toks = [(text, kind), ...], kind in SYNTAX (kw str num op cm fence text) or a
        hex colour. Returns the end x"""
        for t, k in toks:
            col = SYNTAX.get(k, k) if k else CODE_TEXT
            x += self.text(t, x, base, size, col, 'regular', family='mono')
        return x

    def code_block(self, x, y, w, lines=(), size=24, lang='mermaid', pad=(26, 30), lh=1.6, n_lines=None, draw=True):
        """dark code block (1 px border, radius 10, language label top right). lines: list of token lists for
        code_line; draw=False only draws the block (lines go in other layers). Returns a Box with .bases (line
        baselines), .tx (text x) and .lh"""
        n = n_lines or len(lines)
        step = size * lh
        h = pad[0] * 2 + step * n - (step - size * 1.15)
        self.rrect(x, y, x + w, y + h, 10, BORDER, ring=1.0)
        self.rrect(x + 1, y + 1, x + w - 1, y + h - 1, 9, CODE_BG)
        if lang:
            self.text(lang, x + w - 18, y + 26, 16, FAINT, 'bold', 'rm', family='mono')
        b = Box(x, y, x + w, y + h, 10)
        b.tx, b.lh = x + pad[1], step
        b.bases = [y + pad[0] + size * 0.95 + i * step for i in range(n)]
        if draw:
            for toks, base in zip(lines, b.bases):
                self.code_line(b.tx, base, toks, size)
        return b

    def caret(self, x, base, size=24, colour=None):
        """the block caret at the end of a typed line"""
        self.rrect(x + 3, base - size * 0.9, x + 3 + size * 0.5, base + size * 0.22, 1.5, colour or self.accent2)

    def callout(self, x, y, w, title, lines=(), size=26, title_size=None, colour=None, glyph='quote', lh=1.6, pad=(20, 26)):
        """callout (> [!quote]): tinted 16 % with a 4 px left edge in the callout colour (default: the accent), an
        icon and a bold title in the light tone, then body lines (each a runs list for rich(), or a string).
        Returns its Box"""
        c = colour or self.accent
        light = self.accent2 if colour is None else colour
        ts = title_size or size
        h = pad[0] * 2 + ts * 1.1 + len(lines) * size * lh + (6 if lines else 0)
        self.rrect(x, y, x + w, y + h, 8, c, 0.16)
        with self.clip(x, y, x + w, y + h, 8):
            self.rrect(x, y, x + 4, y + h, 0, c)
        tb = y + pad[0] + ts * 0.92
        gx = x + pad[1] + 4
        if glyph:
            self.glyph(glyph, gx + ts * 0.42, tb - ts * 0.37, ts * 0.95, light, 2.0)
            gx += ts * 0.95 + 10
        self.text(title, gx, tb, ts, light, 'bold')
        for i, ln in enumerate(lines):
            base = tb + 6 + (i + 1) * size * lh
            self.rich(x + pad[1] + 4, base, ln if isinstance(ln, (list, tuple)) else [(ln, None)], size)
        return Box(x, y, x + w, y + h, 8)

    def checkbox(self, x, y, size=30, checked=True):
        """task-list checkbox, top-left at (x, y): accent fill with a white tick, or an empty faint ring"""
        r = size * 0.24
        if checked:
            self.rrect(x, y, x + size, y + size, r, self.accent)
            self.glyph('check', x + size / 2, y + size / 2, size * 0.78, WHITE, 3.4)
        else:
            self.rrect(x, y, x + size, y + size, r, FAINT, ring=size * 0.075)

    # ------------------------------------------------------------ rendered diagram (reading view)
    def dnode(self, cx, cy, w, h, label, shape='rect', hi=False, size=24, focus=False):
        """a diagram node centred on (cx, cy): shape rect (r 5) / round (r 14) / stadium / diamond; flat dark fill,
        2 px grey border, text centred; hi = the accent node (accent tint, light border); focus adds a soft
        accent ring 14 px outside. Returns its Box"""
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        edge = self.accent2 if hi else NODE_EDGE
        if focus:
            rr = {'rect': 5, 'round': 14, 'stadium': h / 2}.get(shape, 14) + 13
            self.shadow(x0 - 14, y0 - 14, x1 + 14, y1 + 14, rr, 0, 0, 30, 0, self.accent, 0.35)
            self.rrect(x0 - 14, y0 - 14, x1 + 14, y1 + 14, rr, self.accent, 0.75, ring=2.5)
        if shape == 'diamond':
            P = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
            self.poly(P, NODE_FILL)
            if hi: self.poly(P, self.accent, 0.24)
            self.line(P, 2.0, edge, closed=True)
        else:
            r = {'rect': 5, 'round': 14, 'stadium': h / 2}[shape]
            self.rrect(x0, y0, x1, y1, r, NODE_FILL)
            if hi: self.rrect(x0, y0, x1, y1, r, self.accent, 0.24)
            self.rrect(x0, y0, x1, y1, r, edge, ring=2.0)
        self.text(label, cx, cy, size, BRIGHT if hi else TEXT, 'medium', 'mm')
        return Box(x0, y0, x1, y1)

    def dedge(self, pts, width=2.6, colour=None, head=11.0, label=None, size=17, label_at=0.5):
        """a diagram edge along pts (2+ points) with a small filled arrowhead at the end; optional label in a
        dark chip at fraction `label_at` of the way (a mermaid -->|label| edge)"""
        col = colour or NODE_LINE
        P = np.asarray(pts, np.float32)
        d = P[-1] - P[-2]; d = d / (np.hypot(*d) + 1e-9); n = np.array([-d[1], d[0]])
        tip = P[-1]; back = tip - d * head
        self.line(np.vstack([P[:-1], back + d * 1.0]), width, col)
        self.poly([tuple(tip), tuple(back + n * head * 0.47), tuple(back - n * head * 0.47)], col)
        if label:
            seg = np.cumsum(np.r_[0, np.hypot(*np.diff(P, axis=0).T)])
            s = seg[-1] * label_at
            i = min(int(np.searchsorted(seg, s)) - 1, len(P) - 2); i = max(i, 0)
            t = (s - seg[i]) / max(seg[i + 1] - seg[i], 1e-6)
            lx, ly = P[i] + (P[i + 1] - P[i]) * t
            tw = self.measure(label, size, 'medium')
            self.rrect(lx - tw / 2 - 9, ly - size * 0.8, lx + tw / 2 + 9, ly + size * 0.8, 6, BG2)
            self.rrect(lx - tw / 2 - 9, ly - size * 0.8, lx + tw / 2 + 9, ly + size * 0.8, 6, BORDER2, ring=1.0)
            self.text(label, lx, ly, size, MUTED, 'medium', 'mm')

    # ------------------------------------------------------------ graph view
    def glink(self, a, b, lit=False, alpha=1.0):
        """a graph-view link between two points: thin grey, or the accent (thicker) when both ends are lit"""
        self.line([a, b], 2.6 if lit else 1.6, self.accent if lit else LINK, alpha)

    def gnode(self, x, y, r=8.0, label=None, lit=False, label_size=16, glow=1.0, bg=SIDE):
        """a graph-view node: grey disc, or (lit) the light accent with a soft glow round it; label under it with a
        thin outline in the pane colour `bg`, so links stop short of the words"""
        if lit:
            self.halo(x, y, r * 4.2, self.accent, 0.42 * glow, 1.6)
            self.circle(x, y, r * 1.9, self.accent, 0.16 * glow)
        self.circle(x, y, r, self.accent2 if lit else GNODE)
        if label:
            self.text(label, x, y + r + 8 + label_size * 0.86, label_size, BRIGHT if lit else MUTED,
                      'semibold' if lit else 'regular', 'ms', halo=3 if bg else 0, halo_fill=bg)

    def graph(self, nodes, links, lit=(), label_size=16, only=None, bg=SIDE):
        """a whole graph view: nodes [(x, y, r, label), ...], links [(i, j), ...]; `lit` = indices drawn in the accent
        (a link is lit when both ends are). only='grey' / 'lit' draws just one half (two layers to fade between)"""
        lit = set(lit)
        for i, j in links:
            on = i in lit and j in lit
            if only == 'lit' and not on: continue
            if only == 'grey' and on: on = False
            self.glink(nodes[i][:2], nodes[j][:2], on)
        for k, (x, y, r, lab) in enumerate(nodes):
            on = k in lit
            if only == 'lit' and not on: continue
            self.gnode(x, y, r, lab, on and only != 'grey', label_size, bg=bg)

    # ------------------------------------------------------------ pointer
    def cursor(self, x, y, scale=1.4, click=0.0):
        """the white mouse pointer (dark outline, soft drop shadow), tip at (x, y); click 0..1 draws the expanding
        accent ring of a click"""
        if click > 0:
            self.circle(x, y, 8 + 26 * click, self.accent2, 1 - click, ring=3.0)
        P = [(x + (px - 1) * scale, y + (py - 1) * scale) for px, py in CURSOR]
        P_ = np.asarray(P, np.float32)
        x0, y0 = int(np.floor(P_[:, 0].min())) - 1, int(np.floor(P_[:, 1].min())) - 1
        x1, y1 = int(np.ceil(P_[:, 0].max())) + 2, int(np.ceil(P_[:, 1].max())) + 2
        im = Image.new('L', ((x1 - x0) * 4, (y1 - y0) * 4), 0)
        ImageDraw.Draw(im).polygon([((px - x0) * 4, (py - y0) * 4) for px, py in P], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        self.soft_shadow(m, (x0, y0), 0, 4, 8, '#000000', 0.6)
        self.poly(P, WHITE)
        self.line(P, 1.6 * scale, '#111111', closed=True)

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
            fe = max(p['feather'], 1)
            if p['mode'] == 'r':
                ox, oy = p['origin'] or (x0 + w / 2, y0 + h / 2)
                xs = np.arange(w, dtype=np.float32)[None, :] + x0 + 0.5 - ox
                ys = np.arange(h, dtype=np.float32)[:, None] + y0 + 0.5 - oy
                dist = np.hypot(xs, ys)
                far = max(np.hypot(x0 - ox, y0 - oy), np.hypot(x0 + w - ox, y0 - oy), np.hypot(x0 - ox, y0 + h - oy),
                          np.hypot(x0 + w - ox, y0 + h - oy))
                m = np.clip((far * p['reveal'] - dist) / fe + 0.5, 0, 1) if p['reveal'] > 0 else np.zeros((h, w), np.float32)
                rgb = rgb * m[..., None]; a = a * m
            else:
                n = w if p['mode'] == 'x' else h
                cut = n * p['reveal']
                xs = np.arange(n, dtype=np.float32)
                m = np.clip((cut - xs) / fe + 0.5, 0, 1) if p['reveal'] > 0 else np.zeros(n, np.float32)
                if p['mode'] == 'x':
                    rgb = rgb * m[None, :, None]; a = a * m[None, :]
                else:
                    rgb = rgb * m[:, None, None]; a = a * m[:, None]
        return rgb, a, int(round(x0 + p['dx'])), int(round(y0 + p['dy']))

    def render(self):
        """composite the page and every layer under its current pose -> float RGB"""
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
