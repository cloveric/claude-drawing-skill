"""morph — shape-morph motion graphics: one flat shape turns smoothly into the next while the background colour
switches with it, frozen into a poster (numpy + Pillow only).

Model: a motion designer's shape layer, not a drawing. Every object is ONE closed outline -- no strokes, no
gradients, no texture on the shape itself -- and the whole story is told by that outline changing.
  shapes     a library of flat icon silhouettes in a unit box (y down, about -0.5..0.5): drop, cloud, snowflake,
             mountain, river, wave, sun, moon, leaf, heart, star, bird, fish, pin, house, circle, square, triangle.
             Simple ones are written as curves; compound ones (a cloud is a capsule plus three circles, a
             snowflake is six branched arms) are drawn as a union of primitives into a mask and the outer
             contour is traced back out (Moore neighbour tracing, then smoothed), so any union of circles, lines
             and polygons becomes a single morphable outline.
  resample   an outline is re-sampled to N points spaced evenly along its arc length. Two shapes can only be
             blended point by point if they have the same number of points, run the same way round (winding),
             and start at corresponding places.
  align      same winding first, then the cyclic start offset of the second outline that minimises the summed
             squared distance to the first (both centred and scaled to unit RMS radius), found for all offsets
             at once with an FFT cross-correlation. Without this the in-betweens twist and self-intersect.
  tween      the outline relative to its own centroid is interpolated separately from the centroid itself, so
             the shape deforms in place while its centre travels a curved motion path. Time is eased (ease in
             and out: slow off the keyframe, fast in the middle, settling into the next), and a little squash
             and stretch along the direction of travel is added in the fast middle part.
  colour     background and shape colours switch with the shape; blends go through OKLab so blue -> yellow
             does not pass through grey.
  poster     the frozen animation reads left to right like a film strip: one flat colour panel per keyframe,
             the solid keyframe shape in the middle, onion-skin ghosts (thin outline + faint fill) at evenly
             spaced frame times between keyframes -- bunched up near the keys, spread out in the middle because
             of the easing --, the middle ghost filled more strongly and dotted with its resampled points, a
             dashed motion path through the centroids with chevrons, and an animation timeline under the strip:
             keyframe diamonds and the ease curve of every transition with its frame ticks. (`streaks` speed
             lines and `links` point-pair lines are there too, but read as clutter on a busy strip.)
  paper      a very light print grain over everything; bare paper (not panels, not shapes) gets a fine tooth.
Ghost and line colours default to the per-pixel "ink" of the panel underneath, so a ghost that straddles two
panels switches colour at the border, exactly like the background does.
Lettering: geometric sans / mono (Avenir Next, Menlo on macOS) plus a CJK sans; never handwriting fonts.
Angles are degrees counter-clockwise (like PIL); coordinates are pixels, y down.

    import numpy as np
    from morph import Morph
    m = Morph(1920, 1080, seed=1)
    m.paper('#efe9dd')
    A = m.shape('drop', 500, 540, 220)
    B = m.align(A, m.shape('cloud', 1400, 480, 260))
    m.panel(0, 0, 960, 1080, '#f2c13e', ink='#16182b'); m.panel(960, 0, 1920, 1080, '#2437d6', ink='#f4efe4')
    for u in (0.2, 0.4, 0.6, 0.8):
        s = m.ease(u)
        m.ghost(m.tween(A, B, s, stretch=0.16 * np.sin(np.pi * s)), fill=m.mix('#2437d6', '#f4efe4', s))
    m.fill(A, '#2437d6'); m.fill(B, '#f4efe4')
    m.save('out.png')
"""
import glob
import os
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, noise2d, spline, load_font

PAPER, INK = '#efe9dd', '#16182b'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ------------------------------------------------------------------ OKLab (colour switching without grey mud)
def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def _oklab(c):
    r, g, b = _lin(np.asarray(c, np.float64))
    l = np.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
    m = np.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
    s = np.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
    return np.array([0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
                     1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
                     0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s])


def _from_oklab(L):
    l = (L[0] + 0.3963377774 * L[1] + 0.2158037573 * L[2]) ** 3
    m = (L[0] - 0.1055613458 * L[1] - 0.0638541728 * L[2]) ** 3
    s = (L[0] - 0.0894841775 * L[1] - 1.2914855480 * L[2]) ** 3
    rgb = np.array([4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
                    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
                    -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s])
    return _srgb(rgb).astype(np.float32)


# ------------------------------------------------------------------ fonts (geometric sans, mono, CJK)
_FONTS = {
    'display': [('/System/Library/Fonts/Avenir Next.ttc', 0), ('/System/Library/Fonts/HelveticaNeue.ttc', 1),
                ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'sans': [('/System/Library/Fonts/Avenir Next.ttc', 5), ('/System/Library/Fonts/HelveticaNeue.ttc', 10),
             ('/usr/share/fonts/**/DejaVuSans.ttf', 0), ('C:/Windows/Fonts/arial.ttf', 0)],
    'mono': [('/System/Library/Fonts/Menlo.ttc', 0), ('/usr/share/fonts/**/DejaVuSansMono.ttf', 0),
             ('C:/Windows/Fonts/consola.ttf', 0)],
    'mono_bold': [('/System/Library/Fonts/Menlo.ttc', 1), ('/usr/share/fonts/**/DejaVuSansMono-Bold.ttf', 0),
                  ('C:/Windows/Fonts/consolab.ttf', 0)],
    'cjk_bold': [('/System/Library/Fonts/Hiragino Sans GB.ttc', 2), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
                 ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0)],
    'cjk': [('/System/Library/Fonts/Hiragino Sans GB.ttc', 0), ('/System/Library/Fonts/STHeiti Light.ttc', 1),
            ('/usr/share/fonts/**/NotoSansCJK*Regular*.tt[cf]', 0), ('C:/Windows/Fonts/msyh.ttc', 0)],
}
_CJK_FOR = {'display': 'cjk_bold', 'sans': 'cjk', 'mono': 'cjk', 'mono_bold': 'cjk_bold', 'cjk_bold': 'cjk_bold',
            'cjk': 'cjk'}


@lru_cache(maxsize=None)
def _font(style, size):
    env = os.environ.get('INKPAINT_FONT_' + style.upper())
    if env and os.path.exists(env): return ImageFont.truetype(env, int(size))
    for pat, idx in _FONTS.get(style, []):
        for f in glob.glob(pat, recursive=True):
            try:
                return ImageFont.truetype(f, int(size), index=idx)
            except OSError:
                pass
    return load_font('cjk_sans' if style.startswith('cjk') else 'sans', size)


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


def _runs(s, style):
    """split mixed CJK / Latin text into runs with the right font for each"""
    out = []
    for ch in s:
        st = _CJK_FOR[style] if _is_cjk(ch) else style
        if out and out[-1][1] == st: out[-1][0] += ch
        else: out.append([ch, st])
    return out


# ------------------------------------------------------------------ outline geometry
def _area(P):
    x, y = P[:, 0], P[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def _smooth_closed(P, sigma):
    if sigma <= 0: return P
    r = int(3 * sigma) + 1
    k = np.exp(-np.arange(-r, r + 1) ** 2 / (2 * sigma * sigma)); k /= k.sum()
    Q = np.vstack([P[-r:], P, P[:r]])
    return np.stack([np.convolve(Q[:, 0], k, 'valid'), np.convolve(Q[:, 1], k, 'valid')], 1)


def _trace(mask):
    """Moore-neighbour tracing of the outer boundary of a boolean mask -> (n, 2) pixel coords (x, y)"""
    h, w = mask.shape
    m = np.zeros((h + 2, w + 2), bool); m[1:-1, 1:-1] = mask
    ys, xs = np.nonzero(m)
    if len(ys) == 0: return np.zeros((0, 2), np.float64)
    i = int(np.argmin(ys * (w + 2) + xs)); cx, cy = int(xs[i]), int(ys[i])
    nbr = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1)]   # W NW N NE E SE S SW (clockwise)
    b = 0
    out = [(cx, cy)]; first = None
    for _ in range(8 * m.size):
        for k in range(8):
            d = (b + k) % 8
            nx, ny = cx + nbr[d][0], cy + nbr[d][1]
            if m[ny, nx]: break
        else:
            break
        pd = (d - 1) % 8
        b = nbr.index((cx + nbr[pd][0] - nx, cy + nbr[pd][1] - ny))
        cx, cy = nx, ny
        if first is None: first = (cx, cy, b)
        elif (cx, cy, b) == first: break
        out.append((cx, cy))
    P = np.array(out[:-1] if len(out) > 1 else out, np.float64) - 1
    return P


_RES = 900          # tracing resolution for a 1.4-unit box


def _draw_prims(prims, res=_RES, span=1.4):
    """rasterise a list of primitives (unit coords) -> boolean mask. ('poly', pts) ('circle', x, y, r)
    ('line', pts, width) with round caps; any primitive can be ('sub', prim) to cut it out."""
    k = res / span
    T = lambda x, y: ((x + span / 2) * k, (y + span / 2) * k)
    im = Image.new('L', (res, res), 0); d = ImageDraw.Draw(im)
    for p in prims:
        fill = 255
        if p[0] == 'sub': fill = 0; p = p[1]
        if p[0] == 'poly':
            d.polygon([T(x, y) for x, y in p[1]], fill=fill)
        elif p[0] == 'circle':
            (x, y), r = T(p[1], p[2]), p[3] * k
            d.ellipse([x - r, y - r, x + r, y + r], fill=fill)
        elif p[0] == 'line':
            pts = [T(x, y) for x, y in p[1]]; w = p[2] * k
            d.line(pts, fill=fill, width=max(1, int(round(w))), joint='curve')
            for x, y in (pts[0], pts[-1]):
                d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fill)
    return np.asarray(im) > 127, k, span


def _union(prims, smooth=1.6):
    m, k, span = _draw_prims(prims)
    P = _trace(m)
    P = _smooth_closed(P, smooth)
    return P / k - span / 2


def _circle(n=180, r=0.5, cx=0.0, cy=0.0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1)


def _rot(P, deg, c=(0.0, 0.0)):
    t = np.deg2rad(deg); c = np.asarray(c)
    R = np.array([[np.cos(t), np.sin(t)], [-np.sin(t), np.cos(t)]])      # counter-clockwise on screen (y down)
    return (np.asarray(P) - c) @ R.T + c


def _arm(ang, r0, r1):
    t = np.deg2rad(ang)
    return [(r0 * np.cos(t), -r0 * np.sin(t)), (r1 * np.cos(t), -r1 * np.sin(t))]


@lru_cache(maxsize=None)
def _unit_shape(name):
    """unit outline (y down, roughly inside -0.5..0.5) for a named shape"""
    if name == 'circle':
        return _circle(240, 0.46)
    if name == 'square':
        return _union([('line', [(-0.28, -0.28), (0.28, -0.28), (0.28, 0.28), (-0.28, 0.28), (-0.28, -0.28)], 0.26),
                       ('poly', [(-0.3, -0.3), (0.3, -0.3), (0.3, 0.3), (-0.3, 0.3)])])
    if name == 'triangle':
        return np.array([(0, -0.46), (0.5, 0.4), (-0.5, 0.4)])
    if name == 'star':
        t = np.deg2rad(90 + np.arange(10) * 36)
        r = np.where(np.arange(10) % 2 == 0, 0.52, 0.22)
        return np.stack([r * np.cos(t), -r * np.sin(t) + 0.04], 1)
    if name == 'heart':
        t = np.linspace(0, 2 * np.pi, 240, endpoint=False)
        x = 16 * np.sin(t) ** 3
        y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
        return np.stack([x, y + 1.5], 1) / 34
    if name == 'drop':                               # tip up, round belly: straight tangents into a circle
        cy, r, tip = 0.15, 0.34, -0.56
        b = np.arccos(r / (cy - tip))                # tangent points sit +-b either side of straight up
        th = np.linspace(np.pi / 2 + b, np.pi / 2 - b + 2 * np.pi, 200)
        arc = np.stack([r * np.cos(th), cy - r * np.sin(th)], 1)
        return np.vstack([[(0.0, tip)], arc])
    if name == 'cloud':
        return _union([('line', [(-0.33, 0.15), (0.33, 0.15)], 0.24),
                       ('circle', -0.19, 0.04, 0.17), ('circle', 0.03, -0.08, 0.25), ('circle', 0.25, 0.04, 0.155)])
    if name == 'snowflake':
        prims = [('circle', 0, 0, 0.1)]
        for i in range(6):
            a = 90 + 60 * i
            prims.append(('line', _arm(a, 0, 0.47), 0.07))
            for dist, ln in ((0.2, 0.14), (0.33, 0.1)):
                t = np.deg2rad(a); bx, by = dist * np.cos(t), -dist * np.sin(t)
                for s in (-1, 1):
                    u = np.deg2rad(a + s * 50)
                    prims.append(('line', [(bx, by), (bx + ln * np.cos(u), by - ln * np.sin(u))], 0.06))
        return _union(prims, smooth=1.2)
    if name == 'mountain':
        return np.array([(-0.56, 0.32), (-0.27, -0.1), (-0.17, 0.0), (0.08, -0.42), (0.56, 0.32)])
    if name == 'river':                              # a winding river seen in perspective: thin far, wide near
        C = spline([(0.05, -0.47), (-0.07, -0.33), (0.09, -0.14), (-0.09, 0.12), (0.0, 0.45)], 30)
        n = len(C); tg = np.gradient(C, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        w = (0.03 + 0.4 * np.linspace(0, 1, n) ** 1.5)[:, None] / 2
        return np.vstack([C + nr * w, (C - nr * w)[::-1]])
    if name == 'wave':                               # a breaking wave: body on the right, crest curling over to the left
        K = [(-0.5, 0.16), (-0.34, 0.12), (-0.2, 0.04), (-0.11, -0.08), (-0.08, -0.19), (-0.12, -0.27),
             (-0.19, -0.29), (-0.24, -0.25), (-0.26, -0.18), (-0.3, -0.14), (-0.36, -0.19), (-0.37, -0.3),
             (-0.3, -0.4), (-0.16, -0.46), (0.0, -0.44), (0.16, -0.34), (0.28, -0.17), (0.4, 0.04), (0.5, 0.2),
             (0.55, 0.3)]
        return np.vstack([spline(K, 16), [(0.54, 0.36), (-0.5, 0.36)]])
    if name == 'sun':                                # a disc with eight rounded wedge rays
        prims = [('circle', 0, 0, 0.26)]
        for i in range(8):
            t = np.deg2rad(22.5 + 45 * i); u = np.array([np.cos(t), -np.sin(t)]); v = np.array([-u[1], u[0]])
            prims.append(('poly', [tuple(u * 0.22 + v * 0.07), tuple(u * 0.44 + v * 0.02), tuple(u * 0.44 - v * 0.02),
                                   tuple(u * 0.22 - v * 0.07)]))
            prims.append(('circle', *(u * 0.44), 0.025))
        return _union(prims, smooth=1.2)
    if name == 'moon':
        return _union([('circle', 0, 0, 0.42), ('sub', ('circle', 0.2, -0.12, 0.36))])
    if name == 'leaf':
        t = np.linspace(0, np.pi, 90)
        up = np.stack([-0.42 * np.cos(t), -0.26 * np.sin(t) ** 0.9], 1)
        body = np.vstack([up, up[::-1][1:-1] * [1, -1]])
        body = _rot(body, 35)
        return _union([('poly', body), ('line', [(-0.28, 0.2), (-0.44, 0.36)], 0.05)])
    if name == 'bird':                               # a gull gliding: two long arched wings, a small body
        K = [(-0.52, 0.04), (-0.34, -0.14), (-0.14, -0.12), (0.0, 0.02), (0.14, -0.12), (0.34, -0.14), (0.52, 0.04),
             (0.34, -0.06), (0.16, -0.02), (0.05, 0.1), (0.0, 0.14), (-0.05, 0.1), (-0.16, -0.02), (-0.34, -0.06)]
        P = spline(K + K[:3], 14)
        return P[14:14 * (len(K) + 1)]
    if name == 'fish':
        return _union([('poly', _circle(160, 1.0) * [0.34, 0.2] + [-0.08, 0]),
                       ('poly', [(0.18, 0), (0.48, -0.2), (0.42, 0), (0.48, 0.2)])])
    if name == 'pin':
        c, r, tip = np.array([0, -0.12]), 0.31, np.array([0, 0.5])
        return _union([('circle', c[0], c[1], r),
                       ('poly', [(-r * 0.86, -0.02), (r * 0.86, -0.02), tuple(tip)])], smooth=2.0)
    if name == 'house':
        return _union([('poly', [(-0.36, 0.42), (-0.36, -0.02), (0, -0.4), (0.36, -0.02), (0.36, 0.42)]),
                       ('poly', [(0.14, -0.2), (0.14, -0.38), (0.25, -0.38), (0.25, -0.1)])], smooth=1.0)
    raise KeyError(name)


SHAPES = ('circle', 'square', 'triangle', 'star', 'heart', 'drop', 'cloud', 'snowflake', 'mountain', 'river',
          'wave', 'sun', 'moon', 'leaf', 'bird', 'fish', 'pin', 'house')


class Morph:
    N = 256          # points per outline for every morphable shape

    def __init__(self, W=1920, H=1080, seed=0, ss=4):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.img = np.ones((H, W, 3), np.float32) * hexc(PAPER)
        self.ink = np.ones((H, W, 3), np.float32) * hexc(INK)
        self.tooth = np.ones((H, W), np.float32)          # where bare paper shows (gets a little paper tooth)
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================ shapes and geometry (static)
    @staticmethod
    def resample(P, n=None):
        """closed outline -> n points evenly spaced along its arc length"""
        n = n or Morph.N
        P = np.asarray(P, np.float64)
        Q = np.vstack([P, P[:1]])
        seg = np.hypot(*np.diff(Q, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        t = np.linspace(0, s[-1], n, endpoint=False)
        return np.stack([np.interp(t, s, Q[:, 0]), np.interp(t, s, Q[:, 1])], 1)

    @staticmethod
    def shape(name, cx, cy, size, rot=0.0, n=None, flip=False, stretch=(1.0, 1.0)):
        """a library shape (see SHAPES) centred on (cx, cy), `size` px across the unit box, rotated `rot` degrees
        counter-clockwise, optionally mirrored and stretched (sx, sy); returned resampled to n points, clockwise
        on screen, starting at the top"""
        P = np.array(_unit_shape(name), np.float64)
        if flip: P[:, 0] *= -1
        P = P * np.asarray(stretch, np.float64)
        if rot: P = _rot(P, rot)
        return Morph.normalise(P * size + [cx, cy], n)

    @staticmethod
    def union(prims, cx, cy, size, n=None):
        """your own compound shape: primitives in unit coords (('circle', x, y, r), ('line', pts, width),
        ('poly', pts), ('sub', prim)) -> one traced, morphable outline"""
        return Morph.normalise(_union(prims) * size + [cx, cy], n)

    @staticmethod
    def normalise(P, n=None):
        """resample to n points, clockwise on screen (y down), first point = the topmost point above the centroid"""
        P = Morph.resample(P, n)
        if _area(P) < 0: P = P[::-1]
        c = P.mean(0)
        d = P - c
        ang = np.abs(np.arctan2(d[:, 0], -d[:, 1]))          # angle from straight up
        return np.roll(P, -int(np.argmin(ang)), axis=0)

    @staticmethod
    def align(A, B):
        """B re-indexed so that B[i] corresponds to A[i]: same winding, best cyclic start (FFT cross-correlation
        of the centred, RMS-normalised outlines). Both must have the same number of points."""
        A, B = np.asarray(A, np.float64), np.asarray(B, np.float64)
        if len(A) != len(B): B = Morph.resample(B, len(A))
        if np.sign(_area(A)) != np.sign(_area(B)): B = B[::-1]
        a = A - A.mean(0); b = B - B.mean(0)
        a /= np.sqrt((a ** 2).sum(1).mean()) + 1e-9; b /= np.sqrt((b ** 2).sum(1).mean()) + 1e-9
        corr = sum(np.real(np.fft.ifft(np.conj(np.fft.fft(a[:, i])) * np.fft.fft(b[:, i]))) for i in (0, 1))
        return np.roll(B, -int(np.argmax(corr)), axis=0)

    @staticmethod
    def chain(shapes):
        """align every shape in a sequence to the one before it"""
        out = [np.asarray(shapes[0], np.float64)]
        for s in shapes[1:]: out.append(Morph.align(out[-1], s))
        return out

    @staticmethod
    def ease(t, kind='inout'):
        """timing curves: linear, in, out, inout (cubic), sine, quad, back (overshoot), expo"""
        t = np.clip(np.asarray(t, np.float64), 0, 1)
        if kind == 'linear': return t
        if kind == 'in': return t ** 3
        if kind == 'out': return 1 - (1 - t) ** 3
        if kind == 'inout': return np.where(t < 0.5, 4 * t ** 3, 1 - (-2 * t + 2) ** 3 / 2)
        if kind == 'quad': return np.where(t < 0.5, 2 * t * t, 1 - (-2 * t + 2) ** 2 / 2)
        if kind == 'sine': return -(np.cos(np.pi * t) - 1) / 2
        if kind == 'back':
            c1 = 1.70158 * 1.525
            return np.where(t < 0.5, (2 * t) ** 2 * ((c1 + 1) * 2 * t - c1) / 2,
                            ((2 * t - 2) ** 2 * ((c1 + 1) * (t * 2 - 2) + c1) + 2) / 2)
        if kind == 'expo':
            return np.where(t < 0.5, 2 ** (20 * t - 10) / 2, (2 - 2 ** (-20 * t + 10)) / 2)
        raise KeyError(kind)

    @staticmethod
    def tween(A, B, s, at=None, stretch=0.0, direction=None, spin=0.0, scale=1.0):
        """in-between at eased progress s (0 = A, 1 = B; A and B aligned). The outline about its centroid is
        blended separately from the centroid, which moves to `at` if given (a point on your motion path).
        stretch: squash & stretch along `direction` (degrees, screen; default = the A->B direction);
        spin: extra rotation in degrees; scale: uniform scale."""
        A, B = np.asarray(A, np.float64), np.asarray(B, np.float64)
        cA, cB = A.mean(0), B.mean(0)
        rel = (1 - s) * (A - cA) + s * (B - cB)
        c = (1 - s) * cA + s * cB if at is None else np.asarray(at, np.float64)
        if direction is None:
            d = cB - cA; direction = np.degrees(np.arctan2(-d[1], d[0]))
        if stretch:
            t = np.deg2rad(direction); u = np.array([np.cos(t), -np.sin(t)]); v = np.array([-u[1], u[0]])
            a, b = rel @ u, rel @ v
            rel = np.outer(a * (1 + stretch), u) + np.outer(b / (1 + stretch), v)
        if spin: rel = _rot(rel, spin)
        return rel * scale + c

    @staticmethod
    def at(keys, T, kind='inout'):
        """for real animation: the outline at global time T (0 .. len(keys)-1) along an aligned chain of keys"""
        i = int(np.clip(np.floor(T), 0, len(keys) - 2))
        return Morph.tween(keys[i], keys[i + 1], float(Morph.ease(T - i, kind)))

    @staticmethod
    def mix(c0, c1, t):
        """colour blend through OKLab"""
        return _from_oklab((1 - t) * _oklab(_c(c0)) + t * _oklab(_c(c1)))

    @staticmethod
    def centroid(P):
        return np.asarray(P, np.float64).mean(0)

    # ================================================================ compositing
    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _over(self, sl, a, colour):
        a = np.clip(a, 0, 1)[..., None]
        col = self.ink[sl] if colour is None else (colour if isinstance(colour, np.ndarray) and colour.ndim == 3 else _c(colour))
        self.img[sl] = self.img[sl] * (1 - a) + col * a

    def _mask(self, polys, pad=4, width=None, closed=True, ss=None, round_caps=True):
        """supersampled polygon fill (width None) or polyline stroke -> (mask, slices)"""
        ss = ss or self.ss
        allp = np.concatenate([np.asarray(p, np.float64) for p in polys])
        pad = pad + (width or 0)
        sl = self._box(allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        if sl is None: return None, None
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (bw * ss, bh * ss), 0); d = ImageDraw.Draw(im)
        for p in polys:
            Q = [((x - x0) * ss, (y - y0) * ss) for x, y in np.asarray(p, np.float64)]
            if width is None:
                d.polygon(Q, fill=255)
            else:
                w = width * ss
                if closed: Q = Q + Q[:2]
                d.line(Q, fill=255, width=max(1, int(round(w))), joint='curve')
                if round_caps and not closed:
                    for x, y in (Q[0], Q[-1]):
                        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)
        return np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255, sl

    def _clipmask(self, sl, clip, half):
        m = 1.0
        if clip is not None:
            cm, csl = self._mask([clip])
            full = np.zeros((self.H, self.W), np.float32)
            if csl is not None: full[csl] = cm
            m = m * full[sl]
        if half is not None:
            (x0, y0), (x1, y1) = half
            X, Y = np.meshgrid(np.arange(sl[1].start, sl[1].stop) + 0.5, np.arange(sl[0].start, sl[0].stop) + 0.5)
            dx, dy = x1 - x0, y1 - y0; L = np.hypot(dx, dy) + 1e-9
            side = ((X - x0) * dy - (Y - y0) * dx) / L          # > 0: right of the directed line on screen
            m = m * np.clip(side + 0.5, 0, 1)
        return m

    # ================================================================ background
    def paper(self, colour=PAPER, ink=INK):
        """the whole sheet: flat pale paper (grain is added at composite time)"""
        self.img[:] = _c(colour); self.ink[:] = _c(ink); self.tooth[:] = 1

    def panel(self, x0, y0, x1, y1, colour, ink=INK):
        """a flat colour field (one keyframe's background); `ink` is the colour ghosts and lines take on it"""
        sl = self._box(x0, y0, x1, y1)
        if sl is None: return
        self.img[sl] = _c(colour); self.ink[sl] = _c(ink); self.tooth[sl] = 0

    def wipe(self, cx, cy, r, colour, ink=INK, clip_box=None):
        """a circular colour reveal frozen mid-way (background switching outward from a point)"""
        P = _circle(360, r, cx, cy)
        m, sl = self._mask([P])
        if sl is None: return
        if clip_box is not None:
            x0, y0, x1, y1 = clip_box
            X, Y = np.meshgrid(np.arange(sl[1].start, sl[1].stop), np.arange(sl[0].start, sl[0].stop))
            m = m * ((X >= x0) & (X < x1) & (Y >= y0) & (Y < y1))
        self._over(sl, m, colour)
        self.ink[sl] = self.ink[sl] * (1 - m[..., None]) + _c(ink) * m[..., None]
        self.tooth[sl] *= 1 - m

    # ================================================================ shape layer
    def fill(self, P, colour, alpha=1.0, clip=None, half=None):
        """a flat shape. clip: only inside another outline; half=((x0, y0), (x1, y1)): only right of that line
        (a two-tone fold / facet)"""
        m, sl = self._mask([P])
        if sl is None: return
        if clip is not None or half is not None: m = m * self._clipmask(sl, clip, half)
        self._over(sl, m * alpha, colour)
        self.tooth[sl] *= 1 - m * alpha
        return m, sl

    def outline(self, P, colour=None, width=3.0, alpha=1.0, closed=True, dash=None):
        """outline of a shape (or open path if closed=False). colour None = the panel ink underneath.
        dash=(on, off) in px"""
        P = np.asarray(P, np.float64)
        if dash is None:
            m, sl = self._mask([P], width=width, closed=closed, round_caps=not closed)
        else:
            m, sl = self._mask(self._dashes(P, dash, closed), width=width, closed=False)
        if sl is None: return
        self._over(sl, m * alpha, colour)

    def stroke(self, pts, colour=None, width=6.0, alpha=1.0, smooth=True):
        """a round-capped open line (sun rays, highlights, ripples, foam)"""
        P = np.asarray(pts, np.float64)
        if smooth and len(P) > 2: P = spline(P, 12)
        m, sl = self._mask([P], width=width, closed=False)
        if sl is not None: self._over(sl, m * alpha, colour)

    def dot(self, x, y, r, colour=None, alpha=1.0):
        m, sl = self._mask([_circle(max(24, int(r * 3)), r, x, y)])
        if sl is not None: self._over(sl, m * alpha, colour)

    @staticmethod
    def _dashes(P, dash, closed=True):
        on, off = dash
        Q = np.vstack([P, P[:1]]) if closed else P
        seg = np.hypot(*np.diff(Q, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        out = []; a = 0.0
        while a < s[-1]:
            b = min(a + on, s[-1])
            ts = np.linspace(a, b, max(2, int((b - a) / 2) + 2))
            out.append(np.stack([np.interp(ts, s, Q[:, 0]), np.interp(ts, s, Q[:, 1])], 1))
            a = b + off
        return out

    def ghost(self, P, fill=None, line=None, fill_alpha=0.16, line_alpha=0.62, width=2.4, dash=None):
        """an onion-skin frame: a faint fill plus a thin outline (line None = the panel ink underneath)"""
        if fill is not None: self.fill(P, fill, fill_alpha)
        self.outline(P, line, width, line_alpha, dash=dash)

    def points(self, P, every=4, r=2.6, colour=None, alpha=0.9):
        """dots on every `every`-th resampled point: shows that the outline is N matching points"""
        P = np.asarray(P)[::every]
        polys = [_circle(16, r, x, y) for x, y in P]
        m, sl = self._mask(polys)
        if sl is not None: self._over(sl, m * alpha, colour)

    def links(self, A, B, every=16, colour=None, width=1.2, alpha=0.35, dash=(5, 6)):
        """thin dashed lines from points of A to their partners on B (the correspondence the morph uses)"""
        segs = []
        for a, b in zip(np.asarray(A)[::every], np.asarray(B)[::every]):
            segs += self._dashes(np.array([a, b]), dash, closed=False)
        m, sl = self._mask(segs, width=width, closed=False)
        if sl is not None: self._over(sl, m * alpha, colour)

    # ================================================================ motion marks
    def path(self, pts, per=40):
        """a smooth motion path through control points (Catmull-Rom) -> dense polyline"""
        return spline(np.asarray(pts, np.float64), per).astype(np.float64)

    @staticmethod
    def along(P, u):
        """point and direction (degrees, screen) at fraction u of a polyline's length"""
        P = np.asarray(P, np.float64)
        seg = np.hypot(*np.diff(P, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
        t = float(np.clip(u, 0, 1)) * s[-1]
        x, y = np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])
        i = int(np.clip(np.searchsorted(s, t) - 1, 0, len(P) - 2))
        d = P[i + 1] - P[i]
        return np.array([x, y]), float(np.degrees(np.arctan2(-d[1], d[0])))

    def trail(self, P, colour=None, r=2.4, gap=15, alpha=0.7, dash=None):
        """the motion path: dots of radius r every `gap` px, or dashes if dash=(on, off) (then r = line width)"""
        P = np.asarray(P, np.float64)
        if dash is not None:
            m, sl = self._mask(self._dashes(P, dash, closed=False), width=r, closed=False)
        else:
            seg = np.hypot(*np.diff(P, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
            ts = np.arange(gap / 2, s[-1], gap)
            pts = np.stack([np.interp(ts, s, P[:, 0]), np.interp(ts, s, P[:, 1])], 1)
            m, sl = self._mask([_circle(16, r, x, y) for x, y in pts])
        if sl is not None: self._over(sl, m * alpha, colour)

    def chevron(self, x, y, direction, size=12, colour=None, width=3.0, alpha=0.8):
        """a small arrowhead pointing along `direction` (degrees)"""
        t = np.deg2rad(direction); u = np.array([np.cos(t), -np.sin(t)]); v = np.array([-u[1], u[0]])
        c = np.array([x, y]) + u * size * 0.4
        pts = np.array([c - u * size + v * size * 0.75, c, c - u * size - v * size * 0.75])
        m, sl = self._mask([pts], width=width, closed=False)
        if sl is not None: self._over(sl, m * alpha, colour)

    def streaks(self, x, y, direction, n=3, length=60, spread=26, colour=None, width=5.0, alpha=0.8, seed=None):
        """speed lines trailing behind a moving shape: they start at (x, y) (the shape's trailing edge) and run
        back against `direction`; uneven lengths and offsets so they never look like a ladder"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        t = np.deg2rad(direction); u = np.array([np.cos(t), -np.sin(t)]); v = np.array([-u[1], u[0]])
        segs = []
        for k in range(n):
            off = (k - (n - 1) / 2) * spread + r.uniform(-0.2, 0.2) * spread
            p0 = np.array([x, y]) - u * r.uniform(0, 0.35) * length + v * off
            segs.append(np.array([p0, p0 - u * length * r.uniform(0.4, 1.0) * (1.0 if k != (n - 1) // 2 else 1.25)]))
        m, sl = self._mask(segs, width=width, closed=False)
        if sl is not None: self._over(sl, m * alpha, colour)

    # ================================================================ timeline
    def diamond(self, x, y, r=11, fill=None, line=INK, width=2.4):
        P = np.array([(x, y - r), (x + r, y), (x, y + r), (x - r, y)])
        if fill is not None: self.fill(P, fill)
        self.outline(P, line, width)

    def ease_curve(self, x0, y0, x1, y1, kind='inout', colour=INK, width=3.0, ticks=(), tick_colour=None,
                   drop=True, alpha=1.0):
        """the value graph of one transition: eased progress from (x0, y0) (value 0) to (x1, y1) (value 1),
        with a dot on the curve at each frame time in `ticks` and a dashed drop line to the baseline"""
        t = np.linspace(0, 1, 120)
        P = np.stack([x0 + (x1 - x0) * t, y0 + (y1 - y0) * self.ease(t, kind)], 1)
        self.outline(P, colour, width, alpha, closed=False)
        for u in ticks:
            px, py = x0 + (x1 - x0) * u, y0 + (y1 - y0) * float(self.ease(u, kind))
            if drop: self.outline(np.array([(px, py), (px, y0)]), tick_colour or colour, 1.4, 0.45 * alpha,
                                  closed=False, dash=(4, 5))
            self.dot(px, py, width * 1.35, tick_colour or colour, alpha)

    # ================================================================ lettering
    def text_width(self, s, size, font='sans', spacing=0.0):
        return sum(_font(st, size).getlength(r) for r, st in _runs(s, font)) + spacing * max(0, len(s) - 1)

    def text(self, s, x, y, size, colour=INK, font='sans', anchor='l', spacing=0.0, alpha=1.0, baseline=True):
        """one line of text; x anchored left / middle / right ('l', 'm', 'r'), y is the baseline
        (baseline=False: y is the vertical middle of capitals). CJK runs switch to the CJK sans automatically."""
        runs = _runs(s, font)
        tw = self.text_width(s, size, font, spacing)
        x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor]
        if not baseline: y = y + size * 0.36
        pad = int(size * 1.6)
        sl = self._box(x0 - 4, y - pad, x0 + tw + 4, y + pad * 0.5)
        if sl is None: return tw
        bx, by = sl[1].start, sl[0].start
        im = Image.new('L', (sl[1].stop - bx, sl[0].stop - by), 0); d = ImageDraw.Draw(im)
        cx = x0 - bx
        for r, st in runs:
            f = _font(st, size)
            if spacing:
                for ch in r:
                    d.text((cx, y - by), ch, font=f, fill=255, anchor='ls'); cx += f.getlength(ch) + spacing
            else:
                d.text((cx, y - by), r, font=f, fill=255, anchor='ls'); cx += f.getlength(r)
        self._over(sl, np.asarray(im, np.float32) / 255 * alpha, colour)
        return tw

    # ================================================================ output
    def composite(self, grain=0.006, paper_tooth=0.011):
        img = self.img.copy()
        if not hasattr(self, '_grain'):
            r = np.random.default_rng(12345)
            g = r.standard_normal((self.H, self.W)).astype(np.float32)
            fib = noise2d(self.H, self.W, 2.0, 2, 777) - 0.5
            self._grain = (g * 0.5 + blur(g, 1.0) * 1.8 + fib * 1.6).astype(np.float32)
        k = grain + paper_tooth * self.tooth[..., None]                     # bare paper shows a bit more tooth
        img = img + self._grain[..., None] * k
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
