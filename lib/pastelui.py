"""pastelui — 粉彩界面 / Pastel UI: product-film interface frames on flat pastel fields (numpy + Pillow only).

The look of a modern product launch film: a flat pastel field (blue, pink, yellow, lilac, mint, peach) with one big
soft pool of light and a few white bokeh discs; on it, crisp macOS-style window cards and side panels; a headline in
heavy black type with a translucent marker stroke under the key words; pills, status chips, round check / cross
badges, text highlights and a magnifier; and three small flat companions peeking over the card edges (a starburst
in a cream circle, a violet cloud with a `>_` prompt, a pixel critter). Clean, bright, no texture, no plush.

  shapes      every rounded rectangle, disc, ring, capsule and icon stroke is a signed-distance field with 1 px
              analytic anti-aliasing (pixel centres at i + 0.5, so integer coordinates give crisp edges); the few
              free polygons (pointer triangles) are rasterised 4x and box-filtered.
  shadows     CSS box-shadow semantics: offset, blur radius (sigma = blur / 2), spread, colour, opacity; painted
              only outside the element. Cards stack two or three: a hairline ring, a wide shadow tinted with the
              field's colour (so cards float without a grey halo) and a tight neutral key shadow.
  windows     a frosted rim (white at 55 % with a white hairline inside), a white body with a 1 px border at 8 %,
              a title bar with the red / yellow / green lights, an app icon and a centred title, split panes with a
              pale left pane and hairline dividers. `clip()` keeps pane fills inside the body's rounded corners.
  type        PingFang SC (CJK) + SF Pro (Latin, variable weight) on macOS, Lantinghei SC Heavy for the heavy
              headline weight, SF Mono for ids and tags; script runs are split automatically. Elsewhere Noto Sans
              CJK / Microsoft YaHei and the core fonts. Override with $INKPAINT_FONT_PASTELUI_<CJK|HEAVY|LATIN|MONO>.
  layers      everything is drawn into named layers (premultiplied RGBA, cropped to what was drawn). A layer has a
              depth and a pose -- offset, scale about an origin, opacity, left-to-right reveal -- so one drawing
              can be shown in many states: a window popping up, a line being written, a companion rising from
              behind a card, a badge popping in. Two drawings of the same thing in two states (a check row before
              and after) are two layers; switch them with show / hide. `stage()` composites the current poses.
  magnifier   a lens layer: when composited it magnifies the real pixels under it (bilinear), adds a faint tint
              ring, then draws its white rim, glint and violet handle on top.
  wipe        `wipe(cx, cy, r, prev)`: everything shows inside a growing circle, the previous field colour
              outside, a coloured rim leads the edge (the section change of the film).

    import sys; sys.path.insert(0, 'lib')
    from pastelui import PastelUI, BLUE, GREEN, PINK
    ui = PastelUI(1920, 1080, seed=1)
    ui.field('blue', glow=(520, 150))
    ui.layer('title')
    x = ui.pill(140, 110, '一个例子', BLUE)
    ui.headline(137, 230, '一张工单，走完整个流程', 66, mark='走完整个流程')
    ui.layer('window')
    win = ui.window(140, 300, 1060, 560, title='客服工作台', icon='inbox', sub='· 工单 #0412', split=400)
    ui.layer('panel')
    card = ui.card(1290, 330, 490, 520)
    ui.check_row(card.x0 + 28, card.y0 + 120, card.w - 56, 96, '引用条款', tag='代码规则', sub='引用了手册条款？',
                 glyph='code', state='pass', result='通过')
    ui.layer('buddy', z=-1)                 # behind the window: only the top peeks out
    ui.spark(1468, 290, 124)
    ui.pose('window', dy=60, scale=0.97, alpha=0.6); ui.stage('window_in')
    ui.pose('window'); ui.save('out.jpg')
"""
import glob
import io
import os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, load_font

# ---------------------------------------------------------------- palette (the Dot-film kit)
INK = '#1b1b1f'
BLUE, LILAC, GREEN, PINK = '#1f8ff0', '#8a4fe0', '#1fa866', '#f25c92'
YELLOW, MINT, PEACH = '#f5b400', '#2fb35f', '#f2643a'
CLAY, PIXINK = '#d97757', '#1b1a18'
LINE, GREY = '#e9eef4', '#6f7a88'
PANE = '#f7f9fc'
WHITE = '#ffffff'
FIELDS = {  # name: (field, accent, shadow tint, marker under a headline)
    'blue': ('#d6effd', BLUE, '#2878c8', '#a6d4fb'),
    'pink': ('#fae3ed', PINK, '#c8507e', '#ffbdd5'),
    'yellow': ('#fff3c4', YELLOW, '#c08a10', '#ffdf7e'),
    'lilac': ('#ece3fb', LILAC, '#6e3cc8', '#d6c4fb'),
    'mint': ('#ddf6e4', MINT, '#2a9a5a', '#a6e6bd'),
    'peach': ('#ffe6da', PEACH, '#d06a40', '#ffc4ad'),
}
BOKEH = [(0.05, 0.9, 56, 0.45), (0.955, 0.13, 38, 0.7), (0.975, 0.86, 70, 0.45), (0.47, 0.965, 30, 0.7), (0.6, 0.05, 22, 0.45)]
LIGHTS = ('#ff5f57', '#febc2e', '#28c840')
RAYS = [(0, 1), (31, 0.86), (64, 0.97), (97, 0.83), (128, 1), (160, 0.88), (193, 0.96), (226, 0.84), (258, 1),
        (291, 0.9), (326, 0.95)]                       # starburst rays: (angle clockwise from up, length)
CRITTER = ['.########.', '.#o####o#.', '##########', '.########.', '.#.#..#.#.', '.#.#..#.#.']

# line icons on a 24-unit grid (stroked): ('p', points, closed) polyline, ('c', cx, cy, r) circle, ('a', cx, cy, r, a0, a1)
# arc (degrees, 0 = +x, 90 = down), ('d', cx, cy, r) filled dot, ('r', x0, y0, x1, y1, radius) rounded rectangle
GLYPHS = {
    'more': [('d', 5, 12, 1.3), ('d', 12, 12, 1.3), ('d', 19, 12, 1.3)],
    'user': [('c', 12, 8, 4), ('a', 12, 21, 8, 180, 360)],
    'code': [('p', [(8, 7), (3, 12), (8, 17)]), ('p', [(16, 7), (21, 12), (16, 17)]), ('p', [(14, 4), (10, 20)])],
    'lens': [('c', 10.5, 10.5, 6.5), ('p', [(15.5, 15.5), (20, 20)])],
    'spark': [('p', [(12, 3), (13.9, 8.1), (19, 10), (13.9, 11.9), (12, 17), (10.1, 11.9), (5, 10), (10.1, 8.1)], True),
              ('p', [(18.5, 15.5), (19.3, 17.7), (21.5, 18.5), (19.3, 19.3), (18.5, 21.5), (17.7, 19.3), (15.5, 18.5), (17.7, 17.7)], True)],
    'book': [('p', [(5, 19.5), (5, 5.5)]), ('a', 6.5, 5.5, 1.5, 180, 270), ('p', [(6.5, 4), (18, 4), (18, 18), (6.5, 18)]),
             ('a', 6.5, 19.5, 1.5, 90, 270), ('p', [(6.5, 21), (18, 21), (18, 18)])],
    'inbox': [('p', [(4, 13), (6.5, 5), (17.5, 5), (20, 13), (20, 19), (4, 19)], True),
              ('p', [(4, 13), (8.5, 13), (10, 15.5), (14, 15.5), (15.5, 13), (20, 13)])],
    'tag': [('p', [(4, 4), (11, 4), (20, 13), (13, 20), (4, 11)], True), ('d', 8.5, 8.5, 1.2)],
    'check': [('p', [(5, 12.5), (9.5, 17), (19, 7)])],
    'x': [('p', [(7, 7), (17, 17)]), ('p', [(17, 7), (7, 17)])],
    'suitcase': [('r', 4.5, 7.5, 19.5, 20.5, 2.5), ('p', [(9, 7.5), (9, 4.5), (15, 4.5), (15, 7.5)]),
                 ('p', [(9, 11), (9, 17)]), ('p', [(15, 11), (15, 17)])],
    'umbrella': [('a', 12, 12.5, 8.5, 180, 360), ('p', [(3.5, 12.5), (20.5, 12.5)]), ('p', [(12, 12.5), (12, 18.5)]),
                 ('a', 10, 18.5, 2, 0, 180)],
    'plug': [('p', [(9, 3), (9, 7)]), ('p', [(15, 3), (15, 7)]), ('r', 6, 7, 18, 12.5, 1.5),
             ('p', [(8.5, 12.5), (10, 16), (14, 16), (15.5, 12.5)]), ('p', [(12, 16), (12, 21)])],
    'passport': [('r', 5.5, 3, 18.5, 21, 2), ('c', 12, 10.5, 3.2), ('p', [(9, 16.5), (15, 16.5)])],
    'calendar': [('r', 4, 5, 20, 20, 2), ('p', [(4, 9.5), (20, 9.5)]), ('p', [(8, 3), (8, 6.5)]), ('p', [(16, 3), (16, 6.5)])],
    'pin': [('a', 12, 10, 6, 150, 390), ('p', [(6.8, 13), (12, 21), (17.2, 13)]), ('c', 12, 10, 2.2)],
    'sun': [('c', 12, 12, 4)] + [('p', [(12 + 6.5 * np.cos(a), 12 + 6.5 * np.sin(a)), (12 + 9 * np.cos(a), 12 + 9 * np.sin(a))])
                                 for a in np.arange(8) * np.pi / 4],
    'bolt': [('p', [(13, 3), (6, 13.5), (12, 13.5), (11, 21), (18, 10.5), (12, 10.5)], True)],
    'leaf': [('a', 12, 12, 8, 135, 315), ('a', 12, 12, 8, 315, 495), ('p', [(6.5, 17.5), (17.5, 6.5)])],
}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str):
        return hexc(FIELDS[c][1]) if c in FIELDS else hexc(c)
    return np.asarray(c, np.float32)


def ramp(t, stops):
    """colours along stops (hex or rgb; evenly spaced, or (pos, colour) pairs) -> t.shape + (3,)"""
    if isinstance(stops[0], tuple) and len(stops[0]) == 2 and not isinstance(stops[0][1], (int, float)):
        pos = np.array([p for p, _ in stops], np.float32); cols = np.stack([_c(c) for _, c in stops])
    else:
        cols = np.stack([_c(c) for c in stops]); pos = np.linspace(0, 1, len(cols)).astype(np.float32)
    t = np.clip(np.asarray(t, np.float32), 0, 1)
    return np.stack([np.interp(t, pos, cols[:, k]) for k in range(3)], -1).astype(np.float32)


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


def smin(a, b, k):
    """smooth union of two distance fields (k px of fillet)"""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _cov(d):
    return np.clip(0.5 - d, 0, 1).astype(np.float32)


def _arc_pts(cx, cy, r, a0, a1):
    n = max(6, int(abs(a1 - a0) / 9))
    t = np.deg2rad(np.linspace(a0, a1, n))
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1)


# ---------------------------------------------------------------- fonts
_HERE_AD = '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
_CJK_FACES = [  # (glob, {weight: face index or file-name token}); first hit wins -- macOS, Linux, Windows
    (_HERE_AD + 'PingFang.ttc', {'regular': 3, 'medium': 7, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/PingFang.ttc', {'regular': 3, 'medium': 7, 'bold': 11, 'heavy': 11}),
    ('/System/Library/Fonts/Hiragino Sans GB.ttc', {'regular': 0, 'medium': 0, 'bold': 2, 'heavy': 2}),
    ('/usr/share/fonts/**/NotoSansCJK*-{W}.tt[cf]', {'regular': 'Regular', 'medium': 'Medium', 'bold': 'Bold', 'heavy': 'Black'}),
    ('/usr/share/fonts/**/NotoSansSC-{W}.[ot]tf', {'regular': 'Regular', 'medium': 'Medium', 'bold': 'Bold', 'heavy': 'Black'}),
    ('C:/Windows/Fonts/msyh{W}.ttc', {'regular': '', 'medium': '', 'bold': 'bd', 'heavy': 'bd'}),
]
_HEAVY_FACES = [(_HERE_AD + 'Lantinghei.ttc', 2), ('/System/Library/Fonts/Lantinghei.ttc', 2)]
_LATIN_W = {'regular': 400, 'medium': 510, 'bold': 680, 'heavy': 860}
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


def _cjk(weight, size):
    """-> (font, faux-bold stroke px)"""
    env = os.environ.get('INKPAINT_FONT_PASTELUI_HEAVY' if weight == 'heavy' else 'INKPAINT_FONT_PASTELUI_CJK')
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
            fake = max(1, round(size / 46)) if weight == 'heavy' and not ('Black' in p) else 0
            return f, fake
    return load_font('cjk_sans', size), (max(1, round(size / 40)) if weight in ('bold', 'heavy') else 0)


def _latin(weight, size, mono=False):
    env = os.environ.get('INKPAINT_FONT_PASTELUI_' + ('MONO' if mono else 'LATIN'))
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
                                  index={'regular': 0, 'medium': 10, 'bold': 1, 'heavy': 1}[weight])
    return load_font('sans_bold' if weight in ('bold', 'heavy') else 'sans', size)


def _font(kind, weight, size):
    key = (kind, weight, int(size))
    if key not in _FONTS:
        _FONTS[key] = _cjk(weight, int(size)) if kind == 'cjk' else (_latin(weight, int(size), kind == 'mono'), 0)
    return _FONTS[key]


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


# ---------------------------------------------------------------- data holders
class Box:
    """a rectangle in canvas pixels (cards, windows, panes, chips)"""

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
        self.lens = None
        self.pose = dict(dx=0.0, dy=0.0, scale=1.0, alpha=1.0, reveal=1.0, origin=None, feather=14.0)


# ---------------------------------------------------------------- the canvas
class PastelUI:
    FIELDS = FIELDS
    GLYPHS = GLYPHS

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True):
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages = keep_stages
        self.stages = []
        self.base = np.ones((H, W, 3), np.float32) * hexc(FIELDS['blue'][0])
        self.layers = {}
        self.cur = None
        self._clip = None
        self._wipe = None
        self.field_name = 'blue'
        self.accent, self.tint, self.mark_colour = BLUE, FIELDS['blue'][2], FIELDS['blue'][3]
        g = np.random.default_rng(seed + 7).random((H, W)).astype(np.float32)
        self._grain = (g - 0.5) * (1.2 / 255)            # fixed sub-level dither: no banding in big soft glows

    # ------------------------------------------------------------ layers
    def layer(self, name, z=None):
        """start drawing into layer `name` (re-opens it if it exists). z: depth (default: creation order);
        lower z is further back -- a companion with a lower z than a card hides behind it"""
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
        """stop drawing into the current layer (later drawing goes onto the field)"""
        self._close()

    @staticmethod
    def _view(L):
        """(rgb, a, x0, y0) of what was drawn into L, cropped (a view while the layer is still open)"""
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
        """how layer `name` is shown: offset, scale about `origin` (default: its centre; a magnifier: the lens
        centre), opacity and a left-to-right reveal (0..1, soft edge `feather` px). pose(name) = drawn as is"""
        L = self.layers[name]
        if origin is None and L.lens: origin = L.lens[:2]
        L.pose = dict(dx=dx, dy=dy, scale=scale, alpha=alpha, reveal=reveal, origin=origin, feather=feather)

    def show(self, *names, alpha=1.0):
        for n in names: self.layers[n].pose['alpha'] = alpha

    def hide(self, *names):
        for n in names: self.layers[n].pose['alpha'] = 0.0

    def bounds(self, name):
        """(x0, y0, x1, y1) of what was drawn into layer `name`"""
        rgb, a, x0, y0 = self._view(self.layers[name])
        return x0, y0, x0 + a.shape[1], y0 + a.shape[0]

    @contextmanager
    def clip(self, x0, y0, x1, y1, r=0.0):
        """everything drawn inside is clipped to this rounded rectangle (pane fills inside a window body)"""
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
        """paint colour `col` (rgb, or an (h, w, 3) array) with coverage `cov` over the current target"""
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

    def _fill(self, sl, d, fill, alpha=1.0, grad=None, angle=180.0, box=None, X=None, Y=None):
        cov = _cov(d) * alpha
        if grad is not None:
            bx0, by0, bx1, by1 = box
            a = np.deg2rad(angle); ux, uy = np.sin(a), -np.cos(a)             # CSS: 0deg = up, 90deg = right
            L = abs((bx1 - bx0) * ux) + abs((by1 - by0) * uy)
            t = ((X - (bx0 + bx1) / 2) * ux + (Y - (by0 + by1) / 2) * uy) / max(L, 1e-3) + 0.5
            self._over(sl, cov, ramp(np.broadcast_to(t, cov.shape), grad))
        else:
            self._over(sl, cov, fill)
        return cov

    # ------------------------------------------------------------ the field
    def field(self, colour='blue', glow=(520, 150), glow_size=(1200, 900), glow_alpha=0.62, bokeh=BOKEH, drift=(0, 0)):
        """the flat pastel field: a FIELDS name (sets the accent, shadow tint and marker colour) or a hex colour;
        one big soft pool of white light (top-left corner of its 1200 x 900 ellipse at `glow`) and bokeh discs"""
        if colour in FIELDS:
            bg, self.accent, self.tint, self.mark_colour = FIELDS[colour]
            self.field_name = colour
        else:
            bg = colour
        self.base[:] = hexc(bg)
        gx, gy = glow[0] + glow_size[0] / 2, glow[1] + glow_size[1] / 2
        rx, ry = glow_size[0] / 2, glow_size[1] / 2
        g = self._grid(gx - rx, gy - ry, gx + rx, gy + ry)
        if g:
            sl, X, Y = g
            t = np.hypot((X - gx) / rx, (Y - gy) / ry)
            a = glow_alpha * np.clip(1 - t, 0, 1) ** 1.15
            old, self.cur = self.cur, None
            self._over(sl, a, WHITE)
            self.cur = old
        old, self.cur = self.cur, None
        for (fx, fy, r, al) in (bokeh or ()):
            self.circle(fx * self.W + drift[0], fy * self.H + drift[1], r, WHITE, al)
        self.cur = old

    def wipe(self, cx=None, cy=None, r=0.0, prev='lilac', rim=None, rim_width=26.0):
        """circular colour wipe for the next stage(s): inside radius r everything shows, outside the previous
        field colour `prev`; a rim in `rim` (default: the accent) leads the edge. wipe() with no args clears it"""
        if cx is None:
            self._wipe = None
        else:
            pc = hexc(FIELDS[prev][0]) if prev in FIELDS else _c(prev)
            self._wipe = (cx, cy, r, pc, _c(rim or self.accent), rim_width)

    # ------------------------------------------------------------ shapes
    def rrect(self, x0, y0, x1, y1, r=0.0, fill=WHITE, alpha=1.0, grad=None, angle=180.0, ring=0.0, inset=True):
        """rounded rectangle; ring=w draws only a w px line along the edge (inside if inset, else outside)"""
        g = self._grid(x0 - ring - 2, y0 - ring - 2, x1 + ring + 2, y1 + ring + 2)
        if not g: return None
        sl, X, Y = g
        d = sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, r)
        if ring:
            d = np.abs(d + ring / 2) - ring / 2 if inset else np.abs(d - ring / 2) - ring / 2
        return self._fill(sl, d, fill, alpha, grad, angle, (x0, y0, x1, y1), X, Y)

    def circle(self, cx, cy, r, fill=WHITE, alpha=1.0, ring=0.0, grad=None, angle=180.0):
        """disc (or with ring=w a circular line w px wide, centred on radius r - w / 2)"""
        g = self._grid(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        if not g: return None
        sl, X, Y = g
        d = np.hypot(X - cx, Y - cy) - r
        if ring: d = np.abs(d + ring / 2) - ring / 2
        return self._fill(sl, d, fill, alpha, grad, angle, (cx - r, cy - r, cx + r, cy + r), X, Y)

    def line(self, pts, width=2.0, fill=INK, alpha=1.0, closed=False):
        """polyline with round caps and joins"""
        P = np.asarray(pts, np.float32)
        pad = width / 2 + 2
        g = self._grid(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if not g: return None
        sl, X, Y = g
        return self._fill(sl, sdf_polyline(X, Y, P, closed) - width / 2, fill, alpha)

    def poly(self, pts, fill=INK, alpha=1.0, ss=4):
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

    def shadow(self, x0, y0, x1, y1, r=0.0, dx=0.0, dy=0.0, blur_px=0.0, spread=0.0, colour='#000000', alpha=0.25,
               shape=None):
        """CSS box-shadow of a rounded rectangle (offset dx dy, blur radius blur_px, spread), painted only outside the
        element. shape=(cx, cy, r) casts the shadow of a disc instead"""
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

    def soft_shadow(self, cov_fn, box, dx=0.0, dy=3.0, blur_px=6.0, colour='#2a2080', alpha=0.35):
        """drop shadow that follows any shape (CSS filter: drop-shadow): cov_fn(X, Y) -> coverage"""
        sig = blur_px / 2
        pad = 3 * sig + 3
        g = self._grid(box[0] - pad + min(dx, 0), box[1] - pad + min(dy, 0), box[2] + pad + max(dx, 0), box[3] + pad + max(dy, 0))
        if not g: return
        sl, X, Y = g
        m = cov_fn(X - dx, Y - dy)
        if sig > 0.3: m = blur(m, sig)
        self._over(sl, m * alpha, colour)

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

    def text(self, s, x, y, size, fill=INK, weight='regular', anchor='ls', alpha=1.0, spacing=0.0, family='sans'):
        """text (CJK / Latin runs split automatically). weight: regular / medium / bold / heavy; family: sans / mono.
        anchor: [l m r] + [s baseline, m middle of the CJK body, t top of the CJK body]. Returns the width"""
        size = int(round(size))
        gl, tw = self._glyphs(s, size, weight, spacing, family)
        x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        base = y + {'s': 0.0, 'm': 0.37 * size, 't': 0.86 * size}[anchor[1]]
        bx0, by0 = int(np.floor(x0)) - 6, int(np.floor(base - size * 1.25))
        bw, bh = int(tw) + 14, int(size * 1.65) + 8
        im = Image.new('L', (bw, bh), 0)
        dr = ImageDraw.Draw(im)
        for f, piece, off, fake in gl:
            dr.text((x0 - bx0 + off, base - by0), piece, font=f, fill=255, anchor='ls', stroke_width=fake, stroke_fill=255)
        m = np.asarray(im, np.float32) / 255
        g = self._grid(bx0, by0, bx0 + bw - 1, by0 + bh - 1)
        if not g: return tw
        sl = g[0]
        m = m[sl[0].start - by0:sl[0].stop - by0, sl[1].start - bx0:sl[1].stop - bx0]
        self._over(sl, m * alpha, fill)
        return tw

    def marker(self, x0, x1, base, h=20.0, colour=None, alpha=0.85, drop=6.0, r=6.0):
        """a translucent marker stroke under words on baseline `base`: from base + drop - h to base + drop,
        5 px wider than the words on each side"""
        self.rrect(x0 - 5, base + drop - h, x1 + 5, base + drop, r, colour or self.mark_colour, alpha)

    # ------------------------------------------------------------ icons
    def glyph(self, name, cx, cy, size=18, fill='#8a8a92', sw=1.7, rot=0.0):
        """a line icon from GLYPHS (24-unit grid, stroke sw in grid units), centred on (cx, cy)"""
        k = size / 24.0
        pad = size * 0.6 + 2
        g = self._grid(cx - pad, cy - pad, cx + pad, cy + pad)
        if not g: return
        sl, X, Y = g
        u, v = (X - cx) / k + 12, (Y - cy) / k + 12
        if rot:
            c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
            u, v = (u - 12) * c + (v - 12) * s + 12, -(u - 12) * s + (v - 12) * c + 12
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
        self._over(sl, _cov(d * k), fill)

    def tile(self, x, y, size=46, fill=None, glyph=None, radius=None, grad=None, glyph_size=None, sw=2.1, shadow=True):
        """an app-icon tile (rounded square) with a white line icon; grad=(c0, c1) for a 140deg gradient"""
        fill = fill or self.accent
        r = size * 0.3 if radius is None else radius
        if shadow:
            self.shadow(x, y, x + size, y + size, r, 0, size * 0.17, size * 0.35, -size * 0.17, grad[1] if grad else fill, 0.9)
        self.rrect(x, y, x + size, y + size, r, fill, grad=grad, angle=140)
        if glyph:
            self.glyph(glyph, x + size / 2, y + size / 2, glyph_size or size * 0.52, WHITE, sw)

    def avatar(self, cx, cy, r=21, glyph='user', fill='#dcebfb', colour='#4f86c0'):
        self.circle(cx, cy, r, fill)
        self.glyph(glyph, cx, cy, r * 1.05, colour, 2.0)

    def weather(self, kind, cx, cy, size=44):
        """flat weather icon: sun, cloud, partly (sun behind a cloud), rain"""
        k = size / 44.0
        if kind in ('sun', 'partly'):
            sx, sy = (cx, cy) if kind == 'sun' else (cx + 7 * k, cy - 6 * k)
            r = (11 if kind == 'sun' else 9) * k
            for a in np.arange(8) * np.pi / 4:
                self.line([(sx + (r + 4.5 * k) * np.cos(a), sy + (r + 4.5 * k) * np.sin(a)),
                           (sx + (r + 9 * k) * np.cos(a), sy + (r + 9 * k) * np.sin(a))], 3.2 * k, '#ffbf2e')
            self.circle(sx, sy, r, '#ffc93d')
        if kind in ('cloud', 'partly', 'rain'):
            oy = 3 * k if kind == 'partly' else (-3 * k if kind == 'rain' else 0)
            ox = -3 * k if kind == 'partly' else 0
            col = {'cloud': '#c9d8ea', 'partly': '#d9e5f2', 'rain': '#aebfd6'}[kind]
            g = self._grid(cx - 24 * k, cy - 20 * k, cx + 24 * k, cy + 22 * k)
            sl, X, Y = g
            u, v = (X - cx - ox) / k, (Y - cy - oy) / k
            d = np.hypot(u + 7, v - 2) - 9
            d = smin(d, np.hypot(u - 2, v + 3) - 11, 3)
            d = smin(d, np.hypot(u - 11, v - 3) - 8, 3)
            d = smin(d, sdf_rrect(u - 2, v - 6, 18, 5, 5), 2)
            self._over(sl, _cov(d * k), col)
            if kind == 'rain':
                for i, dx_ in enumerate((-9, 0, 9)):
                    x0_, y0_ = cx + (dx_ + 2) * k, cy + 13 * k + (i % 2) * 3 * k
                    self.line([(x0_, y0_), (x0_ - 2.5 * k, y0_ + 7 * k)], 3.6 * k, '#3d9bf0')

    # ------------------------------------------------------------ UI parts
    def lights(self, x, cy, d=13, gap=9):
        """the red / yellow / green window buttons, first one's left edge at x"""
        for i, c in enumerate(LIGHTS):
            px = x + d / 2 + i * (d + gap)
            self.circle(px, cy, d / 2, c)
            self.circle(px, cy, d / 2, '#000000', 0.18, ring=0.6)

    def window(self, x, y, w, h, title='', icon='inbox', icon_fill=None, sub='', split=None, bar=50, radius=22, rim=9,
               tint=None):
        """a macOS window card: frosted rim, layered shadows, white body, title bar with lights and a centred
        title (app icon + bold title + mono sub), optional pale left pane `split` px wide.
        Returns a Box with .bar (y of the title bar's bottom), .left and .right (pane Boxes)"""
        tint = tint or self.tint
        X0, Y0, X1, Y1, R = x - rim, y - rim, x + w + rim, y + h + rim, radius + rim - 1
        self.shadow(X0, Y0, X1, Y1, R, 0, 50, 90, -30, tint, 0.30)
        self.shadow(X0, Y0, X1, Y1, R, 0, 16, 40, -18, '#1e3250', 0.22)
        self.rrect(X0, Y0, X1, Y1, R, WHITE, 0.55)
        self.rrect(X0, Y0, X1, Y1, R, WHITE, 0.7, ring=1.0)
        self.rrect(x, y, x + w, y + h, radius, '#141e32', 0.08, ring=1.0, inset=False)
        self.rrect(x, y, x + w, y + h, radius, WHITE)
        with self.clip(x, y, x + w, y + h, radius):
            self.rrect(x, y, x + w, y + bar, 0, '#f6f8fa')
            self.rrect(x, y + bar - 1, x + w, y + bar, 0, LINE)
            if split:
                self.rrect(x, y + bar, x + split, y + h, 0, PANE)
                self.rrect(x + split - 1, y + bar, x + split, y + h, 0, LINE)
        self.lights(x + 20, y + bar / 2)
        if title:
            tw = self.measure(title, 16, 'bold')
            sw_ = self.measure(sub, 14, 'regular', family='mono') if sub else 0
            total = (20 + 10 if icon else 0) + tw + (10 + sw_ if sub else 0)
            tx = x + w / 2 - total / 2
            if icon:
                self.tile(tx, y + bar / 2 - 10, 20, icon_fill or self.accent, icon, radius=6, glyph_size=13, sw=2.2, shadow=False)
                tx += 30
            self.text(title, tx, y + bar / 2, 16, '#5a6472', 'bold', 'lm')
            if sub:
                self.text(sub, tx + tw + 10, y + bar / 2, 14, '#9aa3af', 'regular', 'lm', family='mono')
        self.glyph('more', x + w - 29, y + bar / 2, 18, '#8a8a92', 1.7)
        b = Box(x, y, x + w, y + h, radius)
        b.bar = y + bar
        b.left = Box(x, y + bar, x + split, y + h) if split else None
        b.right = Box(x + (split or 0), y + bar, x + w, y + h)
        return b

    def card(self, x, y, w, h, r=26, tint=None, fill=WHITE):
        """a floating white panel: hairline ring, a wide shadow tinted with the field colour, a tight key shadow"""
        tint = tint or self.tint
        self.shadow(x, y, x + w, y + h, r, 0, 40, 80, -34, tint, 0.45)
        self.shadow(x, y, x + w, y + h, r, 0, 12, 30, -16, '#142850', 0.2)
        self.rrect(x, y, x + w, y + h, r, '#142850', 0.07, ring=1.0, inset=False)
        self.rrect(x, y, x + w, y + h, r, fill)
        return Box(x, y, x + w, y + h, r)

    def pill(self, x, cy, text, dot=None, size=21):
        """the section pill: white 72 % capsule with a coloured dot (and its halo). Returns the right edge"""
        dot = dot or self.accent
        tw = self.measure(text, size, 'bold', spacing=1)
        h = size * 1.5 + 18
        x1 = x + 15 + 10 + 12 + tw + 20
        y0, y1 = cy - h / 2, cy + h / 2
        self.shadow(x, y0, x1, y1, h / 2, 0, 6, 18, -10, '#143c78', 0.25)
        self.rrect(x, y0, x1, y1, h / 2, '#000000', 0.05, ring=1.0, inset=False)
        self.rrect(x, y0, x1, y1, h / 2, WHITE, 0.72)
        self.circle(x + 20, cy, 9, dot, 0.2)
        self.circle(x + 20, cy, 5, dot)
        self.text(text, x + 37, cy, size, '#2a2a30', 'bold', 'lm', spacing=1)
        return x1

    def steps(self, x, cy, labels, lit=0, current=None, size=19, accent=None):
        """a row of step chips joined by arrows; the first `lit` are filled with the accent, `current` gets a
        halo. Returns the right edge"""
        accent = accent or self.accent
        for i, s in enumerate(labels):
            on = i < lit
            if i:
                col = accent if on else '#9fbbd6'
                self.line([(x + 1, cy), (x + 18, cy)], 2.2, col)
                self.line([(x + 13, cy - 5), (x + 18, cy), (x + 13, cy + 5)], 2.2, col)
                x += 22 + 8
            tw = self.measure(s, size, 'bold')
            h = size * 1.5 + 14
            x1 = x + tw + 32
            y0, y1 = cy - h / 2, cy + h / 2
            if on:
                if i == current:
                    self.rrect(x - 5, y0 - 5, x1 + 5, y1 + 5, h / 2 + 5, accent, 0.22)
                self.shadow(x, y0, x1, y1, h / 2, 0, 8, 16, -10, accent, 0.8)
                self.rrect(x, y0, x1, y1, h / 2, accent)
                self.text(s, x + 16, cy, size, WHITE, 'bold', 'lm')
            else:
                self.rrect(x, y0, x1, y1, h / 2, WHITE, 0.8, ring=1.0, inset=False)
                self.rrect(x, y0, x1, y1, h / 2, WHITE, 0.55)
                self.text(s, x + 16, cy, size, '#7a8ea4', 'bold', 'lm')
            x = x1 + 8
        return x - 8

    def headline(self, x, base, text, size=62, fill=INK, mark=None, mark_colour=None, mark_h=None, spacing=1.0,
                 draw_text=True, draw_mark=True):
        """heavy headline on baseline `base`; `mark` = the substring that gets a marker stroke under it.
        Returns (width, (mark_x0, mark_x1) or None) -- with draw_text / draw_mark you can put the marker and the
        words in different layers (the marker goes in the layer behind)"""
        span = None
        if mark and mark in text:
            i = text.index(mark)
            mx0 = x + self.measure(text[:i], size, 'heavy', spacing) + (spacing if i else 0)
            mx1 = mx0 + self.measure(mark, size, 'heavy', spacing)
            span = (mx0, mx1)
            if draw_mark:
                self.marker(mx0, mx1, base, mark_h or size * 0.32, mark_colour, 0.9, drop=size * 0.1)
        w = self.measure(text, size, 'heavy', spacing)
        if draw_text:
            self.text(text, x, base, size, fill, 'heavy', 'ls', spacing=spacing)
        return w, span

    def chip(self, x, cy, text, colour=None, size=15, solid=False, glyph=None, anchor='l', pad=11, family='sans'):
        """status chip: a capsule tinted 10 % with a 25 % ring and bold coloured text, or solid with white text and a
        coloured glow. anchor 'l' / 'r' / 'm' on x. Returns its Box"""
        colour = colour or self.accent
        tw = self.measure(text, size, 'bold', family=family)
        gw = size * 1.15 + 6 if glyph else 0
        w = tw + gw + 2 * pad
        h = size * 1.45 + 8
        x0 = x - w * {'l': 0, 'm': 0.5, 'r': 1}[anchor]
        x1, y0, y1 = x0 + w, cy - h / 2, cy + h / 2
        if solid:
            self.shadow(x0, y0, x1, y1, h / 2, 0, 8, 16, -8, colour, 0.9)
            self.rrect(x0, y0, x1, y1, h / 2, colour)
            fg = WHITE
        else:
            self.rrect(x0, y0, x1, y1, h / 2, colour, 0.10)
            self.rrect(x0, y0, x1, y1, h / 2, colour, 0.25, ring=1.0)
            fg = colour
        tx = x0 + pad
        if glyph:
            self.glyph(glyph, tx + size * 0.55, cy, size * 1.1, fg, 3.0 if glyph in ('x', 'check') else 2.2)
            tx += gw
        self.text(text, tx, cy, size, fg, 'bold', 'lm', family=family)
        return Box(x0, y0, x1, y1, h / 2)

    def mono_tag(self, x1, cy, text, size=13):
        """a small grey mono tag (GRADERS, #0412...) right-aligned at x1"""
        tw = self.measure(text, size, 'bold', spacing=1.5, family='mono')
        self.rrect(x1 - tw - 20, cy - size, x1, cy + size, 8, '#f2f4f7')
        self.text(text, x1 - 10, cy, size, '#8a94a3', 'bold', 'rm', spacing=1.5, family='mono')

    def callout(self, x, cy, text, colour=None, glyph=None, size=17):
        """solid pill with a pointer on its left (points at x): a verdict tag next to a highlighted line"""
        colour = colour or PINK
        self.poly([(x, cy), (x + 9, cy - 7.5), (x + 9, cy + 7.5)], colour)
        b = self.chip(x + 8, cy, text, colour, size, solid=True, glyph=glyph, pad=12)
        return b

    def ref_chip(self, x, base, text, glyph='book', colour='#1774c9', ok=True, size=22):
        """an inline reference chip sitting on a text line (baseline `base`), with a green check bubble if ok.
        Returns the right edge"""
        tw = self.measure(text, size, 'bold')
        h = size * 1.55
        x0, x1 = x, x + 11 + size * 0.8 + 6 + tw + 11
        y1 = base + size * 0.22
        y0 = y1 - h
        if ok:
            self.rrect(x0, y0, x1, y1, 9, GREEN, 1.0, ring=2.5, inset=False)
        self.rrect(x0, y0, x1, y1, 9, '#e7f2fe')
        self.rrect(x0, y0, x1, y1, 9, BLUE, 0.25, ring=1.0)
        self.glyph(glyph, x0 + 11 + size * 0.4, (y0 + y1) / 2, size * 0.8, colour, 2.0)
        self.text(text, x0 + 11 + size * 0.8 + 6, (y0 + y1) / 2, size, colour, 'bold', 'lm')
        if ok:
            self.circle(x1, y0, 13.5, WHITE)
            self.circle(x1, y0, 11, GREEN)
            self.glyph('check', x1, y0, 14, WHITE, 3.2)
        return x1

    def badge(self, cx, cy, kind='pass', size=30):
        """round badge: green disc with a white check, or pink with a white cross"""
        c = GREEN if kind == 'pass' else PINK
        self.shadow(0, 0, 0, 0, 0, 0, 6, 14, -6, c, 0.9, shape=(cx, cy, size / 2))
        self.circle(cx, cy, size / 2, c)
        self.glyph('check' if kind == 'pass' else 'x', cx, cy, size * 0.62, WHITE, 3.2)

    def spinner(self, cx, cy, size=22, colour=None, angle=0.0):
        colour = colour or LILAC
        r = size * 7.5 / 20
        self.circle(cx, cy, r + 1.3, colour, 0.2, ring=2.6)
        pts = _arc_pts(cx, cy, r, angle - 90, angle)
        self.line(pts, 2.6 * size / 20, colour)

    def bar(self, x0, x1, cy, frac, colour=None, h=6):
        """progress bar: tinted track and a filled part"""
        colour = colour or self.accent
        self.rrect(x0, cy - h / 2, x1, cy + h / 2, h / 2, colour, 0.15)
        if frac > 0:
            self.rrect(x0, cy - h / 2, x0 + (x1 - x0) * frac, cy + h / 2, h / 2, colour)

    def check_row(self, x, y, w, h=94, label='', tag=None, sub=None, glyph='code', tone=None, state='idle',
                  result=None, status=True, progress=0.6):
        """a checklist row (rounded 18): icon tile, bold label + tag chip, grey question underneath, status on the
        right. state: idle (white, dashed ring, 待检查) / active (tone ring + glow, spinner, progress bar) /
        pass (green tint, check badge) / fail (pink tint, cross badge). status=False leaves the right side empty
        (draw it in another layer with row_status). Returns the status anchor (x1, cy)"""
        tone = tone or self.accent
        x1, y1, cy = x + w, y + h, y + h / 2
        if state == 'pass':
            self.rrect(x, y, x1, y1, 18, '#effaf3'); self.rrect(x, y, x1, y1, 18, '#bfe8cc', ring=1.5)
        elif state == 'fail':
            self.rrect(x, y, x1, y1, 18, '#fff1f6'); self.rrect(x, y, x1, y1, 18, '#f9c0d5', ring=1.5)
        elif state == 'active':
            self.shadow(x, y, x1, y1, 18, 0, 14, 26, -16, tone, 1.0)
            self.rrect(x, y, x1, y1, 18, WHITE)
            self.rrect(x, y, x1, y1, 18, tone, 0.05)
            self.rrect(x, y, x1, y1, 18, tone, ring=2.0)
        else:
            self.rrect(x, y, x1, y1, 18, WHITE); self.rrect(x, y, x1, y1, 18, LINE, ring=1.0)
        ts = h * 0.49
        self.tile(x + 18, cy - ts / 2, ts, tone, glyph, glyph_size=ts * 0.52)
        tx = x + 18 + ts + 15
        ls = h * 0.27
        lw = self.text(label, tx, cy - h * 0.035, ls, '#18202b', 'heavy')
        if tag:
            self.chip(tx + lw + 10, cy - h * 0.035 - ls * 0.37, tag, tone, size=h * 0.14, pad=9)
        if sub:
            self.text(sub, tx, cy + h * 0.29, h * 0.175, '#7c8694')
        if state == 'active' and progress is not None:
            self.bar(x + 18, x1 - 18, y1 - 10, progress, tone, 4)
        if status:
            self.row_status(x1 - 18, cy, state, result, tone, h)
        return x1 - 18, cy

    def row_status(self, x1, cy, state='pass', text=None, tone=None, h=94):
        """the right end of a check row, right-aligned at x1: badge + 通过 / 不通过, spinner + 检查中, or 待检查"""
        tone = tone or self.accent
        fs = h * 0.18
        if state in ('pass', 'fail'):
            text = text or ('通过' if state == 'pass' else '不通过')
            col = GREEN if state == 'pass' else PINK
            tw = self.text(text, x1, cy, fs, col, 'bold', 'rm')
            self.badge(x1 - tw - 8 - 15 * h / 94, cy, state, 30 * h / 94)
        elif state == 'active':
            tw = self.text(text or '检查中', x1, cy, fs * 0.95, tone, 'bold', 'rm')
            self.spinner(x1 - tw - 8 - 11, cy, 22, tone, 120)
        else:
            tw = self.text(text or '待检查', x1, cy, fs * 0.95, '#a3acb8', 'regular', 'rm')
            for a in range(0, 360, 30):
                p = _arc_pts(x1 - tw - 8 - 12, cy, 11, a, a + 16)
                self.line(p, 2, '#c6cfda')

    # ------------------------------------------------------------ magnifier
    def magnifier(self, cx, cy, r=52, mag=1.32, colour=None, name='lens', z=None, handle=45.0):
        """a lens in its own layer: it magnifies the real pixels under it when composited (move it with pose:
        the view follows), with a white rim, a violet handle toward `handle` degrees and a glint"""
        colour = colour or LILAC
        prev = self.cur.name if self.cur is not None else None
        self.layer(name, z)
        a = np.deg2rad(handle); ux, uy = np.cos(a), np.sin(a)
        p0 = (cx + ux * (r + 6), cy + uy * (r + 6)); p1 = (cx + ux * (r + 62), cy + uy * (r + 62))
        g = self._grid(min(p0[0], p1[0]) - 30, min(p0[1], p1[1]) - 30, max(p0[0], p1[0]) + 30, max(p0[1], p1[1]) + 34)
        sl, X, Y = g
        d = sdf_segment(X, Y, p0, p1) - 9
        self.soft_shadow(lambda XX, YY: _cov(sdf_segment(XX, YY, p0, p1) - 9), (p0[0] - 12, p0[1] - 12, p1[0] + 12, p1[1] + 12),
                         0, 10, 18, '#3c1e78', 0.4)
        t = ((X - cx) * (-uy) + (Y - cy) * ux) / 18 + 0.5                        # across the handle
        self._over(sl, _cov(d), ramp(np.broadcast_to(t, d.shape), ('#7442d0', '#9a6cf2')))
        self.shadow(0, 0, 0, 0, 0, 0, 18, 30, -12, '#3c1e78', 0.45, shape=(cx, cy, r + 7))
        self.circle(cx, cy, r + 8.5, colour, 0.6, ring=1.5)
        self.circle(cx, cy, r + 7, WHITE, ring=7)
        self.circle(cx, cy, r, colour, 0.35, ring=1.5)
        gg = self._grid(cx - r, cy - r, cx + r, cy + r)
        sl, X, Y = gg
        rad = np.hypot(X - cx, Y - cy) / r
        self._over(sl, np.clip((rad - 0.62) / 0.38, 0, 1) * 0.10 * _cov(np.hypot(X - cx, Y - cy) - r), colour)
        gx, gy = cx - 0.6 * r, cy - 0.6 * r
        b = np.deg2rad(42); vx, vy = np.sin(b), -np.cos(b)
        self.line([(gx - vx * r * 0.18, gy - vy * r * 0.18), (gx + vx * r * 0.18, gy + vy * r * 0.18)], r * 0.13, WHITE, 0.55)
        L = self.layers[name]
        L.lens = (cx, cy, r, mag)
        L.pose['origin'] = (cx, cy)
        self._close()
        if prev is not None: self.layer(prev)
        return name

    # ------------------------------------------------------------ companions
    def spark(self, cx, cy, size=124, spin=0.0, colour=CLAY):
        """starburst in a cream circle with a white ring and a warm shadow (spin: degrees)"""
        r = size / 2
        self.shadow(0, 0, 0, 0, 0, 0, 16, 30, -14, '#783c1e', 0.45, shape=(cx, cy, r))
        self.circle(cx, cy, r + 5, WHITE)
        self.circle(cx, cy, r, '#fbf4ec')
        k = size * 0.66 / 100
        g = self._grid(cx - 46 * k, cy - 46 * k, cx + 46 * k, cy + 46 * k)
        sl, X, Y = g
        d = np.hypot(X - cx, Y - cy) - 9 * k
        for a, l in RAYS:
            t = np.deg2rad(a + spin)
            tip = (cx + np.sin(t) * 40 * l * k, cy - np.cos(t) * 40 * l * k)
            d = np.minimum(d, sdf_segment(X, Y, (cx, cy), tip) - 5.5 * k)
        self._over(sl, _cov(d), colour)

    def cloud(self, cx, cy, size=118, rot=0.0):
        """violet puffy cloud with a white >_ prompt: radial gradient, soft drop shadow, a gloss highlight"""
        k = size / 100
        bumps = [(50, 50, 33)] + [(50 + 31 * np.cos(t), 52 + 31 * np.sin(t), 15 + 2.5 * np.sin(3 * t + 1))
                                  for t in np.linspace(-np.pi / 2, 1.5 * np.pi, 10, endpoint=False)]
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))

        def dist(X, Y):
            u, v = (X - cx) / k, (Y - cy) / k
            u, v = u * c + v * s + 50, -u * s + v * c + 50
            d = np.full(np.broadcast(u, v).shape, 1e9, np.float32)
            for bx, by, br in bumps:
                d = smin(d, np.hypot(u - bx, v - by) - br, 4.0)
            return d * k, u, v

        box = (cx - 52 * k, cy - 52 * k, cx + 52 * k, cy + 52 * k)
        self.soft_shadow(lambda X, Y: _cov(dist(X, Y)[0]), box, 0, 3 * k, 6 * k, '#2a2080', 0.35)
        g = self._grid(*box)
        sl, X, Y = g
        d, u, v = dist(X, Y)
        t = np.hypot(u - 35, v - 28) / 80
        self._over(sl, _cov(d), ramp(t, [(0.0, '#9a90ff'), (0.55, '#6b5cff'), (1.0, '#3f33c4')]))
        hl = _cov((np.hypot((u - 38) / 16, (v - 28) / 8) - 1) * 8 * k) * _cov(d)
        self._over(sl, hl * 0.22, WHITE)
        P = lambda q: (cx + ((q[0] - 50) * c - (q[1] - 50) * s) * k, cy + ((q[0] - 50) * s + (q[1] - 50) * c) * k)
        self.line([P((30, 40)), P((44, 52)), P((30, 64))], 8 * k, WHITE)
        self.line([P((52, 66)), P((70, 66))], 8 * k, WHITE)

    def critter(self, x, y, px=9, colour=CLAY, eye=PIXINK, blink=False):
        """the orange pixel critter (10 x 6 cells of px), top-left at (x, y); blink closes the eyes"""
        x, y = round(x), round(y)
        for j, row in enumerate(CRITTER):
            for i, ch in enumerate(row):
                if ch == '.': continue
                x0, y0 = x + i * px, y + j * px
                if ch == 'o':
                    self.rrect(x0, y0, x0 + px, y0 + px, 0, colour if blink else eye)
                    if blink: self.rrect(x0, y0 + px * 0.6, x0 + px, y0 + px, 0, eye)
                else:
                    self.rrect(x0, y0, x0 + px, y0 + px, 0, colour)

    # ------------------------------------------------------------ compositing
    def _posed(self, L):
        """-> (rgb, a, x0, y0) of layer L under its pose (scale about origin, offset, reveal)"""
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

    def _magnify(self, out, cx, cy, r, mag, alpha):
        g = self._grid(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1)
        if not g: return
        sl, X, Y = g
        sx = cx + (X - cx) / mag - 0.5
        sy = cy + (Y - cy) / mag - 0.5
        sx = np.clip(np.broadcast_to(sx, (Y.shape[0], X.shape[1])), 0, self.W - 1.001)
        sy = np.clip(np.broadcast_to(sy, (Y.shape[0], X.shape[1])), 0, self.H - 1.001)
        x0, y0 = sx.astype(np.int32), sy.astype(np.int32)
        fx, fy = (sx - x0)[..., None], (sy - y0)[..., None]
        v = (out[y0, x0] * (1 - fx) + out[y0, x0 + 1] * fx) * (1 - fy) + (out[y0 + 1, x0] * (1 - fx) + out[y0 + 1, x0 + 1] * fx) * fy
        m = (_cov(np.hypot(X - cx, Y - cy) - r) * alpha)[..., None]
        out[sl] = out[sl] * (1 - m) + v * m

    def render(self):
        """composite the field and every layer under its current pose -> float RGB"""
        out = self.base.copy()
        for L in sorted(self.layers.values(), key=lambda q: (q.z, q.order)):
            al = L.pose['alpha']
            if al <= 0: continue
            rgb, a, x0, y0 = self._posed(L)
            if L.lens:
                cx, cy, r, mag = L.lens
                s = L.pose['scale']
                self._magnify(out, cx + L.pose['dx'], cy + L.pose['dy'], r * s, mag, al)
            h, w = a.shape
            X0, Y0 = max(0, x0), max(0, y0)
            X1, Y1 = min(self.W, x0 + w), min(self.H, y0 + h)
            if X1 <= X0 or Y1 <= Y0: continue
            cr = rgb[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]; ca = a[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
            out[Y0:Y1, X0:X1] = out[Y0:Y1, X0:X1] * (1 - ca[..., None] * al) + cr * al
        if self._wipe:
            cx, cy, r, pc, rc, rw = self._wipe
            Y = np.arange(self.H, dtype=np.float32)[:, None] + 0.5
            X = np.arange(self.W, dtype=np.float32)[None, :] + 0.5
            d = np.hypot(X - cx, Y - cy)
            inside = _cov(d - r)[..., None]
            out = out * inside + pc * (1 - inside)
            ring = _cov(np.abs(d - r + rw / 2) - rw / 2)[..., None] * 0.9
            out = out * (1 - ring) + rc * ring
        return out

    def composite(self):
        I = self.render() + self._grain[..., None]
        return Image.fromarray((np.clip(I, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        """snapshot the current poses (kept PNG-compressed in memory: a draw-on sequence has 80+ of them)"""
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
                with open(f'{stages_dir}/{i:02d}_{name}.png', 'wb') as fh:
                    fh.write(png)
            img.save(f'{stages_dir}/{len(self.stages):02d}_final.png')
        return img
