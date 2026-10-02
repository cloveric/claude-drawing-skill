"""comic — a golden-age comic-book cover of about 1940: brush-inked key lines on the black plate, flat process
colours separated by hand into Ben-Day tints, four plates printed a little out of register on cheap newsprint that
has since browned (numpy + Pillow only).

Model: the cover is made the way the shop made it, then printed the way a web press printed it.
  newsprint   groundwood pulp: cream gone tan, cloudy formation, short brown fibres and bark flecks, a fine tooth
              with pits that never take ink. Ink soaks in instead of sitting on top, so every print is a little
              fuzzy and a little flat, and the paper colour tints every ink printed on it.
  key plate   the inker's black: brush lines that land thin, swell and lift off to a point and run heavier on the
              side away from the light (`brush`, `outline`, `edge`), thin pen lines (`pen`), spotted blacks (`ink`),
              feathering -- rows of tapered strokes coming in from a shadow edge (`feather`), hatching, speed lines
              and hand lettering. Things in front hide what is behind them: every `part` first erases the key and
              the colour under itself, then gets its own outline.
  colour guide the colourist marks every area with a mix of the three process inks taken from a short list of
              Ben-Day tints -- 0, 20, 40, 70, 100 % -- so a whole cover has only a few dozen colours: skin is
              20 % red + 40 % yellow, sky blue 40 % blue, red is 100 % red + 100 % yellow ... (`flat`). The colour
              runs under the black lines. A graded sky is a stack of bands, because the separator cut a new
              piece of tint film for each step, along a hand-cut wavy edge (`graded`, `rings`). Grey is a black tint.
  separation  every plate is screened on its own: a tint becomes Ben-Day dots on a regular grid at that plate's
              angle (round dots that grow, touch at 50 % and turn into holes near 70 %); 100 % prints solid. Overlap
              two tints and the dot grids beat into rosettes. Separations were painted by hand, so each plate's
              flats wander a pixel or two off the line art.
  press       every plate lands a little off (`register`): the red slips out from under the black outline on one
              side and leaves a sliver of paper on the other. Newsprint drinks ink: dots spread and lose their round
              edge, small dots drop out, solids mottle and let paper pits and fibres through, the black is never
              quite black. Inks are transparent and multiply (yellow + red = red-orange, red + blue = purple).
  afterlife   the cover browned from the edges (`brown_edges`), the spine cracked into little white stress ticks
              and two staples rusted (`spine`), a corner got rubbed and dog-eared (`corner`), a crease broke the
              colour (`crease`), foxing spots (`foxing`).
Stages: `stage(name, plates='CMYK')` keeps the plates as they are now and proofs only the listed ones, so a
drawing animation can show the key line art first and then the progressive proofs (yellow, + red, + blue) the way
an engraver pulled them. Coordinates are pixels, y down; angles in degrees counter-clockwise (0 = 3 o'clock).

    from comic import ComicCover, YELLOW, RED, BLUE, SKY
    c = ComicCover(1920, 1080, seed=3)
    c.paper()
    c.graded(None, [BLUE, SKY, YELLOW], (0, 0), (0, 1080))      # banded sky, whole sheet
    c.part(c.ellipse_pts(960, 540, 200, 120), RED, width=7)    # a red shape in front, inked round
    c.feather(*c.edge_normals(c.ellipse_pts(960, 540, 200, 120)), length=40)
    c.balloon('HELLO THERE!', 1300, 300, 40, tail=(1100, 470))
    c.logo('THRILL', [(200, 60), (900, 40), (900, 230), (200, 210)], vp=(560, 2600))
    c.stage('key', plates='K'); c.stage('colour')
    c.spine(); c.brown_edges(); c.foxing()
    c.save('out.jpg', stages_dir='stages')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, shift, latin_font

# ---------------------------------------------------------------- inks and colours
# printed solid on bright paper; on newsprint they multiply with the paper colour
INK = {'C': np.array([0.15, 0.55, 0.83], np.float32),     # process blue of the period (greener than today's cyan)
       'M': np.array([0.91, 0.21, 0.39], np.float32),     # process red (warm magenta)
       'Y': np.array([0.99, 0.84, 0.13], np.float32),
       'K': np.array([0.13, 0.11, 0.11], np.float32)}
NEWS = (0.935, 0.872, 0.715)                              # newsprint, already toned
# colour guide values: (blue, red, yellow, black) Ben-Day tints, 0..1 -- the colourist's chart
WHITE = (0, 0, 0, 0)
CREAM = (0, 0, .2, 0)
PALE = (0, 0, .4, 0)
YELLOW = (0, 0, 1, 0)
GOLD = (0, .2, 1, 0)
ORANGE = (0, .4, 1, 0)
DEEP_ORANGE = (0, .7, 1, 0)
RED = (0, 1, 1, 0)
CRIMSON = (0, 1, .7, 0)
PINK = (0, .4, .2, 0)
SKIN = (0, .2, .4, 0)
TAN = (0, .4, .7, 0)
BROWN = (0, .7, 1, .4)                                   # no blue in browns: C+M+Y rosettes read green
DARK_BROWN = (0, .7, 1, .7)
SKY = (.4, 0, 0, 0)
LIGHT_BLUE = (.2, 0, 0, 0)
BLUE = (1, .4, 0, 0)
NAVY = (1, .7, 0, .2)
VIOLET = (.7, .7, 0, 0)
MAUVE = (.4, .4, .2, 0)
LILAC = (.2, .2, 0, 0)
GREEN = (1, 0, 1, 0)
LIME = (.4, 0, 1, 0)
GREY = (0, 0, 0, .4)
LIGHT_GREY = (0, 0, 0, .2)
SILVER = (.2, 0, 0, .2)
SCREEN_ANGLE = {'C': 15.0, 'M': 75.0, 'Y': 0.0, 'K': 45.0}
LIGHT = (-0.6, -0.8)                                      # light from the upper left: outlines swell lower right

_S = '/System/Library/Fonts/Supplemental/'
_FACES = {   # (glob, face index); first hit wins -- macOS, then Linux / Windows look-alikes; generic core style last
    'letter': [(_S + 'ChalkboardSE.ttc', 2), (_S + 'Comic Sans MS Bold.ttf', 0), ('/System/Library/Fonts/MarkerFelt.ttc', 1),
               ('/usr/share/fonts/**/*ComicNeue*Bold*.[ot]tf', 0), ('/usr/share/fonts/**/*Kalam*Bold*.ttf', 0),
               ('C:/Windows/Fonts/comicbd.ttf', 0), 'hand'],
    'logo': [(_S + 'Futura.ttc', 4), (_S + 'Impact.ttf', 0), ('/usr/share/fonts/**/*Oswald*Bold*.ttf', 0),
             ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', 0), ('C:/Windows/Fonts/impact.ttf', 0), 'condensed'],
    'bold': [(_S + 'Futura.ttc', 2), (_S + 'Arial Black.ttf', 0), ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0),
             ('C:/Windows/Fonts/ariblk.ttf', 0), 'sans_bold'],
    'slab': [(_S + 'Rockwell.ttc', 2), (_S + 'SuperClarendon.ttc', 7), ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0),
             ('C:/Windows/Fonts/ROCKB.TTF', 0), 'serif'],
    'heavy': [(_S + 'SuperClarendon.ttc', 7), (_S + 'Rockwell.ttc', 2), ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0),
              ('C:/Windows/Fonts/ROCKEB.TTF', 0), 'serif'],
}
_FONT_CACHE = {}


def _font(face, size):
    key = (face, int(size))
    if key in _FONT_CACHE: return _FONT_CACHE[key]
    env = os.environ.get('INKPAINT_FONT_' + face.upper())
    cands = ([(env, 0)] if env and os.path.exists(env) else []) + _FACES.get(face, [face])
    f = None
    for c in cands:
        if isinstance(c, str):
            hit = latin_font(c)
            if not hit: continue
            path, idx = hit
        else:
            fs = glob.glob(c[0], recursive=True)
            if not fs: continue
            path, idx = fs[0], c[1]
        try:
            f = ImageFont.truetype(path, int(size), index=idx); break
        except OSError:
            continue
    if f is None: f = ImageFont.load_default(int(size))
    _FONT_CACHE[key] = f
    return f


# ---------------------------------------------------------------- geometry helpers
def _resample(P, step, closed=False):
    P = np.asarray(P, np.float32)
    if closed: P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(s[-1] / step) + 1)
    ss = np.linspace(0, s[-1], n, endpoint=not closed)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


def _closed_spline(pts, per=10):
    """periodic Catmull-Rom through control points"""
    P = np.asarray(pts, np.float32)
    n = len(P)
    t = np.linspace(0, 1, per, endpoint=False)[:, None]
    t2, t3 = t * t, t * t * t
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.vstack(out).astype(np.float32)


def _normals(P):
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-6
    return T, np.stack([-T[:, 1], T[:, 0]], 1)


def _outward(P):
    """unit outward normals of a closed polygon (either winding)"""
    _, N = _normals(np.vstack([P[-1:], P, P[:1]]))
    N = N[1:-1]
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    return N if area < 0 else -N


def _persp(dst, src):
    """coefficients for Image.transform(PERSPECTIVE): output (dst) points -> input (src) points"""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return tuple(np.linalg.solve(np.array(A, np.float64), np.array(b, np.float64)))


def _norm_noise(rng, H, W, sigma):
    n = blur(rng.standard_normal((H, W)).astype(np.float32), sigma)
    return (n / (n.std() + 1e-6)).astype(np.float32)


class ComicCover:
    def __init__(self, W=1920, H=1080, seed=0, screen=11.0, misreg=4.0, slop=1.6, light=LIGHT):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.pitch = float(screen)
        self.slop = float(slop)
        l = np.asarray(light, np.float32)
        self.light = l / np.linalg.norm(l)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.g = {p: np.zeros((H, W), np.float32) for p in 'CMYk'}   # colour guide; 'k' = black tints
        self.key = np.zeros((H, W), np.float32)                        # line art (solid black)
        a = self.rng.uniform(0, 2 * np.pi, 3)
        self.reg = {'K': (0.0, 0.0, 0.0)}
        for p, ang, k in zip('MCY', a, (1.0, 0.85, 0.6)):
            self.reg[p] = (float(np.cos(ang) * misreg * k), float(np.sin(ang) * misreg * k), float(self.rng.normal(0, 0.03)))
        self.paper_rgb = np.ones((H, W, 3), np.float32) * np.array(NEWS, np.float32)
        self.tooth = np.full((H, W), 0.5, np.float32)
        self.wear_ops = []
        self.stages = []
        self._press_cache = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def register(self, plate, dx, dy, rot=0.0):
        """where plate C, M, Y or K lands relative to the sheet (px, px, degrees)"""
        self.reg[plate] = (float(dx), float(dy), float(rot))

    # ------------------------------------------------------------ newsprint
    def paper(self, colour=NEWS, tone=1.0, fibres=3200, flecks=420):
        """groundwood newsprint: cloudy formation, warm age patches, short fibres, bark flecks, pitted tooth"""
        H, W = self.H, self.W
        r = np.random.default_rng(self._seed())
        col = np.asarray(colour, np.float32)
        form = noise2d(H, W, 26, 3, self._seed()) - 0.5                       # pulp flocs
        cloud = noise2d(H, W, 260, 3, self._seed()) - 0.5
        warm = noise2d(H, W, 420, 3, self._seed())
        img = col[None, None, :] * (1 + 0.035 * form + 0.05 * cloud * tone)[..., None]
        img = img * (1 - 0.07 * tone * (warm ** 2)[..., None] * np.array([0.25, 0.55, 1.0], np.float32))
        im = Image.new('L', (W, H), 0)
        lt = Image.new('L', (W, H), 0)
        d, dl = ImageDraw.Draw(im), ImageDraw.Draw(lt)
        for i in range(fibres):
            x, y = r.uniform(0, W), r.uniform(0, H)
            L, a = r.uniform(3, 16), r.uniform(0, np.pi)
            k = r.uniform(-0.25, 0.25)
            pts = [(x + np.cos(a + k * t) * L * t, y + np.sin(a + k * t) * L * t) for t in np.linspace(-0.5, 0.5, 5)]
            if r.random() < 0.72:
                d.line(pts, fill=int(r.uniform(60, 200)), width=1)
            else:
                dl.line(pts, fill=int(r.uniform(80, 220)), width=1)
        for i in range(flecks):
            x, y, rr = r.uniform(0, W), r.uniform(0, H), r.uniform(0.5, 1.6)
            d.ellipse([x - rr, y - rr * r.uniform(0.6, 1.2), x + rr, y + rr], fill=int(r.uniform(150, 255)))
        fib = blur(np.asarray(im, np.float32) / 255, 0.45)
        lfb = blur(np.asarray(lt, np.float32) / 255, 0.45)
        brown = np.array([0.45, 0.32, 0.18], np.float32)
        img = img * (1 - 0.30 * fib[..., None] * (1 - brown)) + 0.05 * lfb[..., None]
        self.tooth = np.clip(0.5 + 0.16 * _norm_noise(r, H, W, 0.6) + 0.10 * form, 0, 1).astype(np.float32)
        img = img * (1 + 0.02 * (self.tooth - 0.5))[..., None]
        self.paper_rgb = np.clip(img, 0, 1).astype(np.float32)
        self._press_cache = None

    # ------------------------------------------------------------ shapes
    @staticmethod
    def ellipse_pts(cx, cy, rx, ry, rot=0.0, a0=0.0, a1=360.0, n=None):
        n = n or max(24, int(np.pi * (rx + ry) / 3))
        t = np.deg2rad(np.linspace(a0, a1, n, endpoint=(a1 - a0) % 360 != 0))
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        x, y = np.cos(t) * rx, -np.sin(t) * ry
        return np.stack([cx + x * c + y * s, cy - x * s + y * c], 1).astype(np.float32)

    @staticmethod
    def smooth(pts, per=10, closed=True):
        """Catmull-Rom through control points (closed by default)"""
        return _closed_spline(pts, per) if closed else spline(pts, per)

    @staticmethod
    def tube_pts(path, widths, per=10, caps=True):
        """outline of a limb / rope / flame tongue: a spline centreline with widths along it, round caps"""
        path = np.asarray(path, np.float32)
        P = spline(path, per) if len(path) > 2 else np.linspace(path[0], path[1], 16).astype(np.float32)
        P = _resample(P, 2.0)
        w = np.interp(np.linspace(0, 1, len(P)), np.linspace(0, 1, len(widths)), np.asarray(widths, np.float32))
        T, N = _normals(P)
        A = P + N * (w / 2)[:, None]
        B = P - N * (w / 2)[:, None]
        if not caps:
            return np.vstack([A, B[::-1]]).astype(np.float32)
        arc = np.linspace(0, np.pi, 12)[1:-1]

        def cap(i, angs):
            c, rr = P[i], w[i] / 2
            return np.stack([c[0] + np.cos(angs) * rr, c[1] + np.sin(angs) * rr], 1)
        b1 = np.arctan2(N[-1, 1], N[-1, 0])
        b0 = np.arctan2(N[0, 1], N[0, 0])
        return np.vstack([A, cap(-1, b1 - arc), B[::-1], cap(0, b0 + np.pi - arc)]).astype(np.float32)

    @staticmethod
    def burst_pts(cx, cy, rx, ry, spikes=14, depth=0.3, seed=0, rot=0.0):
        """a starburst: alternating points and notches with uneven spike lengths"""
        r = np.random.default_rng(seed)
        n = spikes * 2
        t = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.deg2rad(rot) + r.uniform(-0.08, 0.08, n)
        k = np.where(np.arange(n) % 2 == 0, 1 + r.uniform(-0.08, 0.12, n), 1 - depth + r.uniform(-0.05, 0.05, n))
        return np.stack([cx + np.cos(t) * rx * k, cy + np.sin(t) * ry * k], 1).astype(np.float32)

    def mask(self, pts, smooth=False, per=10, ss=3):
        """closed polygon (or control points if smooth) -> anti-aliased full-sheet mask"""
        P = np.asarray(pts, np.float32)
        if smooth: P = _closed_spline(P, per)
        m = np.zeros((self.H, self.W), np.float32)
        x0, y0 = int(max(0, np.floor(P[:, 0].min()) - 2)), int(max(0, np.floor(P[:, 1].min()) - 2))
        x1, y1 = int(min(self.W, np.ceil(P[:, 0].max()) + 3)), int(min(self.H, np.ceil(P[:, 1].max()) + 3))
        if x1 <= x0 or y1 <= y0: return m
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P.tolist()], fill=255)
        m[y0:y1, x0:x1] = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return m

    def circle(self, cx, cy, r):
        return np.clip(r + 0.5 - np.hypot(self.XX - cx, self.YY - cy), 0, 1)

    def _m(self, shape, smooth=False):
        if shape is None: return np.ones((self.H, self.W), np.float32)
        if isinstance(shape, np.ndarray) and shape.shape == (self.H, self.W): return shape
        return self.mask(shape, smooth)

    @staticmethod
    def _bbox(m, pad=0):
        ys, xs = np.nonzero(m > 0.003)
        if len(xs) == 0: return None
        H, W = m.shape
        return (slice(max(0, ys.min() - pad), min(H, ys.max() + pad + 1)), slice(max(0, xs.min() - pad), min(W, xs.max() + pad + 1)))

    def grow(self, m, r):
        """dilate a soft mask by about r px (round, anti-aliased)"""
        if r <= 0: return m
        sg = max(0.5, r * 0.6)
        q = 0.0478                                     # Phi(-1/0.6): a straight edge moves out by r
        dd = 0.05 / sg
        return smoothstep(q - dd, q + dd, blur(m, sg))

    def shrink(self, m, r):
        return 1 - self.grow(1 - m, r)

    # ------------------------------------------------------------ colour guide (the colourist's flats)
    def _set(self, a, colour, sl=None):
        c = [float(v) for v in colour] + [0.0] * (4 - len(colour))
        for p, v in zip('CMYk', c):
            g = self.g[p] if sl is None else self.g[p][sl]
            g *= 1 - a
            if v: g += a * v

    def flat(self, shape, colour, smooth=False):
        """paint an area of the colour guide with one Ben-Day mix (replaces what was there)"""
        a = self._m(shape, smooth)
        self._set(a, colour)
        return a

    def graded(self, shape, colours, p0, p1, edges=None, wave=7.0, scale=180.0, smooth=False):
        """stepped bands from p0 to p1, one Ben-Day colour per band, split along hand-cut wavy edges.
        edges: the inner band edges as fractions 0..1 (default: equal bands)"""
        a = self._m(shape, smooth)
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        d = p1 - p0
        L = float(np.linalg.norm(d)) + 1e-6
        t = ((self.XX - p0[0]) * d[0] + (self.YY - p0[1]) * d[1]) / (L * L)
        t = t + (noise2d(self.H, self.W, scale, 2, self._seed()) - 0.5) * 2 * wave / L
        n = len(colours)
        e = np.asarray(edges if edges is not None else np.arange(1, n) / n, np.float32)
        band = np.searchsorted(e, t.ravel()).reshape(t.shape)
        for i, col in enumerate(colours):
            self._set(a * (band == i), col)
        return a

    def rings(self, shape, cx, cy, colours, radii, wave=4.0, smooth=False):
        """concentric bands (a halo): colours[i] inside radii[i]; outermost first is not needed"""
        a = self._m(shape, smooth)
        rr = np.hypot(self.XX - cx, self.YY - cy) + (noise2d(self.H, self.W, 90, 2, self._seed()) - 0.5) * 2 * wave
        for col, rad in sorted(zip(colours, radii), key=lambda z: -z[1]):
            self._set(a * np.clip(rad + 0.5 - rr, 0, 1), col)
        return a

    def knock(self, shape, key=True, smooth=False):
        """white: no ink on any plate (stars, highlights, balloons)"""
        a = self._m(shape, smooth)
        self._set(a, WHITE)
        if key: self.key *= 1 - a
        return a

    # ------------------------------------------------------------ key plate (brush and pen)
    def _dense(self, pts, smooth=True, closed=False, step=1.5):
        P = np.asarray(pts, np.float32)
        if smooth and 3 <= len(P) < 80:
            P = _closed_spline(P, 10) if closed else spline(P, per=10)
        P = _resample(P, step, closed)
        return P if len(P) >= 2 else np.vstack([P, P + 0.5])

    def _ribbon(self, P, w, ss=3):
        """variable-width centreline -> (slices, alpha) at 1x, drawn at ss x with round joins"""
        r = float(w.max()) / 2 + 3
        x0, y0 = int(max(0, P[:, 0].min() - r)), int(max(0, P[:, 1].min() - r))
        x1, y1 = int(min(self.W, P[:, 0].max() + r + 1)), int(min(self.H, P[:, 1].max() + r + 1))
        if x1 - x0 < 1 or y1 - y0 < 1: return None, None
        bw, bh = x1 - x0, y1 - y0
        im = Image.new('L', (bw * ss, bh * ss), 0)
        d = ImageDraw.Draw(im)
        Q = (P - np.array([x0, y0], np.float32)) * ss
        R = np.maximum(w * ss / 2, 0.55)
        _, N = _normals(Q)
        A = (Q + N * R[:, None]).tolist(); B = (Q - N * R[:, None]).tolist()
        for i in range(len(Q) - 1):
            d.polygon(A[i] + A[i + 1] + B[i + 1] + B[i], fill=255)
        seg = np.diff(Q, axis=0)
        seg /= np.linalg.norm(seg, axis=1, keepdims=True) + 1e-6
        turn = np.concatenate([[1.0], np.sum(seg[1:] * seg[:-1], 1), [1.0]])
        idx = set(np.flatnonzero(turn < 0.97).tolist()) | set(range(0, len(Q), 3)) | {0, len(Q) - 1}
        Ql, Rl = Q.tolist(), R.tolist()
        for i in idx:
            (x, y), rr = Ql[i], Rl[i]
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
        return (slice(y0, y1), slice(x0, x1)), np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255

    def _put_key(self, sl, a, clip=None):
        if sl is None: return
        if clip is not None: a = a * clip[sl]
        np.maximum(self.key[sl], a, out=self.key[sl])

    def _profile(self, P, width, taper, swell, jitter):
        n = len(P)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        L = max(float(s[-1]), 1e-3)
        _, N = _normals(P)
        if jitter:
            P = P + N * (fbm1d(n, max(4, 60), 3, self._seed()) * jitter)[:, None]
        t0 = max(1e-3, min(taper[0] * L, 70.0)) if taper[0] else 1e-3
        t1 = max(1e-3, min(taper[1] * L, 90.0)) if taper[1] else 1e-3
        w = width * (1 + swell * np.sin(np.pi * s / L)) * (1 + 0.10 * fbm1d(n, max(4, 40), 3, self._seed()))
        if taper[0]: w = w * (0.12 + 0.88 * smoothstep(0, t0, s))
        if taper[1]: w = w * (0.04 + 0.96 * smoothstep(0, t1, L - s))
        return P.astype(np.float32), w.astype(np.float32)

    def brush(self, pts, width=6.0, taper=(0.25, 0.4), swell=0.2, smooth=True, jitter=0.5, clip=None):
        """an open brush stroke: lands thin, swells, lifts off to a point"""
        P, w = self._profile(self._dense(pts, smooth), width, taper, swell, jitter)
        sl, a = self._ribbon(P, w)
        self._put_key(sl, a, clip)
        return P

    def pen(self, pts, width=2.2, smooth=True, taper=(0.08, 0.12), clip=None):
        """a thin, even crow-quill line for small detail"""
        P, w = self._profile(self._dense(pts, smooth), width, taper, 0.0, 0.25)
        sl, a = self._ribbon(P, w)
        self._put_key(sl, a, clip)

    def dot(self, x, y, r=2.5):
        self.key = np.maximum(self.key, self.circle(x, y, r))

    def outline(self, pts, width=5.0, heavy=0.9, smooth=None, overlap=0.06, closed=True, taper=(0.03, 0.05), clip=None):
        """ink round a closed shape in one stroke: heavier on the side away from the light, the two ends
        overlapping where the brush came back round"""
        P = np.asarray(pts, np.float32)
        smooth = (len(P) < 80) if smooth is None else smooth
        if not closed:
            return self.edge(P, width, heavy, smooth=smooth, clip=clip)
        C = self._dense(P, smooth, closed=True)
        n = len(C)
        out = _outward(C)
        i0 = int(self.rng.integers(n))
        idx = (i0 + np.arange(int(n * (1 + overlap)))) % n
        Pp, O = C[idx], out[idx]
        Pr, w = self._profile(Pp, width, taper, 0.0, 0.45)
        w = w * (1 + heavy * np.clip(-(O @ self.light), -0.6, 1))
        sl, a = self._ribbon(Pr, w)
        self._put_key(sl, a, clip)
        return C

    def edge(self, pts, width=5.0, heavy=0.9, side=None, smooth=True, taper=(0.15, 0.25), clip=None):
        """an open contour line that also swells where it faces away from the light.
        side=+1/-1 picks which normal counts as 'outside' (default: the one facing away from the light)"""
        P = self._dense(pts, smooth)
        _, N = _normals(P)
        if side is None:
            side = 1.0 if float(np.mean(-(N @ self.light))) >= 0 else -1.0
        Pr, w = self._profile(P, width, taper, 0.1, 0.45)
        w = w * (1 + heavy * np.clip(-(side * N) @ self.light, -0.6, 1))
        sl, a = self._ribbon(Pr, w)
        self._put_key(sl, a, clip)
        return P

    def ink(self, shape, smooth=False):
        """spotted black: a solid area of key"""
        a = self._m(shape, smooth)
        np.maximum(self.key, a, out=self.key)
        return a

    def erase(self, shape, smooth=False):
        """white-out on the key (what a front object hides)"""
        a = self._m(shape, smooth)
        self.key *= 1 - a
        return a

    def mask_outline(self, m, width=5.0, heavy=4.0, clip=None, sl=None):
        """outline any soft mask (unions of circles, text): an even ring plus a crescent on the shadow side.
        sl: m is already the crop of the sheet at sl (with room for the line around it)"""
        if sl is None:
            sl = self._bbox(m, int(width + heavy + 6))
            if sl is None: return
            mm = m[sl]
        else:
            mm = m
        ring = np.clip(self.grow(mm, width * 0.5) - self.shrink(mm, width * 0.5), 0, 1)
        if heavy:
            dx, dy = -self.light * heavy
            cres = np.clip(shift(mm, dx, dy) - mm, 0, 1)
            cres = smoothstep(0.35, 0.65, blur(cres, 0.8 + heavy * 0.15))
            ring = np.maximum(ring, cres * self.grow(mm, width * 0.5 + heavy))
        if clip is not None: ring = ring * clip[sl]
        np.maximum(self.key[sl], ring, out=self.key[sl])

    def part(self, pts, colour=None, width=5.0, heavy=0.9, smooth=False, line=True, per=10):
        """a thing in front: erase key and colour under it, paint its flat, ink its outline. Returns its mask"""
        P = np.asarray(pts, np.float32)
        C = _closed_spline(P, per) if smooth else P
        a = self.mask(C)
        self.key *= 1 - a
        if colour is not None: self._set(a, colour)
        if line and width > 0: self.outline(C, width, heavy, smooth=False)
        return a

    @staticmethod
    def edge_normals(pts, smooth=False, step=4.0):
        """points along a closed outline and their outward normals (for feather)"""
        P = np.asarray(pts, np.float32)
        if smooth: P = _closed_spline(P, 10)
        P = _resample(P, step, closed=True)
        return P, _outward(P)

    def feather(self, P, N, length=40.0, width=3.4, spacing=8.0, thresh=0.1, clip=None, along=None,
                curl=0.15, toward=None, jitter=1.0):
        """golden-age feathering: tapered strokes that grow out of a shadow edge into the form -- long in the core
        of the shadow, shorter toward the light, their lengths drifting in waves rather than ticking like a ruler,
        each one a little curved and a little off parallel.
        P, N: edge points and outward normals (see edge_normals). Strokes are made only where the edge faces
        away from the light (or toward `toward`, a unit vector); `along` forces one direction for all strokes;
        clip (the shape's own mask) keeps them inside."""
        P = np.asarray(P, np.float32)
        N = np.asarray(N, np.float32)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        face = -(N @ self.light) if toward is None else N @ np.asarray(toward, np.float32)
        face = np.convolve(np.pad(face, 3, mode='edge'), np.ones(7) / 7, mode='valid')   # smooth over a few points
        n = len(P)
        wav = np.interp(s, np.linspace(0, s[-1] + 1e-3, 64), fbm1d(64, 9, 3, self._seed()))           # slow swell
        chop = np.interp(s, np.linspace(0, s[-1] + 1e-3, 256), fbm1d(256, 6, 2, self._seed()))        # quick unevenness
        r = self.rng
        last = -1e9
        for i in range(n):
            if s[i] - last < spacing * r.uniform(0.7, 1.3): continue
            f = (face[i] - thresh) / (1 - thresh)
            if f <= 0.05: continue
            last = s[i]
            Ln = length * f ** 0.7 * np.clip(0.62 + 0.38 * wav[i] + 0.3 * chop[i] * jitter, 0.25, 1.15)
            if Ln < 4: continue
            dirv = -N[i] if along is None else np.asarray(along, np.float32)
            tilt = r.normal(0, 0.07 * jitter)
            ct, st = np.cos(tilt), np.sin(tilt)
            dirv = np.array([dirv[0] * ct - dirv[1] * st, dirv[0] * st + dirv[1] * ct], np.float32)
            side = np.array([-dirv[1], dirv[0]], np.float32)
            cu = curl * r.uniform(0.6, 1.4)
            p0 = P[i] + N[i] * 1.5
            mid = p0 + dirv * Ln * 0.5 + side * Ln * cu * 0.3
            end = p0 + dirv * Ln + side * Ln * cu
            Pd = _resample(spline(np.array([p0, mid, end], np.float32), 6), 1.2)
            sd = np.linspace(0, 1, len(Pd))
            w = width * (0.75 + 0.25 * f) * (1 - sd) ** 1.15 * r.uniform(0.85, 1.15) + 0.2
            sl, a = self._ribbon(Pd, w.astype(np.float32))
            self._put_key(sl, a, clip)

    def hatch(self, shape, angle=-30, spacing=9.0, width=2.2, taper=0.3, clip=None, jitter=0.3, smooth=False):
        """parallel brush hatching clipped to a shape (ground shadows, cast shadows)"""
        m = self._m(shape, smooth)
        sl = self._bbox(m, 2)
        if sl is None: return
        y0, x0 = sl[0].start, sl[1].start
        M = m[sl]
        h, w = M.shape
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), -np.sin(a)], np.float32)
        p = np.array([-d[1], d[0]], np.float32)
        corners = np.array([[0, 0], [w, 0], [0, h], [w, h]], np.float32)
        pr, dr = corners @ p, corners @ d
        ts = np.arange(dr.min(), dr.max(), 1.5, dtype=np.float32)
        for o in np.arange(pr.min() + spacing * 0.5, pr.max(), spacing):
            o = o + self.rng.uniform(-0.12, 0.12) * spacing
            pts = o * p + ts[:, None] * d
            ix, iy = np.round(pts[:, 0]).astype(int), np.round(pts[:, 1]).astype(int)
            ok = (ix >= 0) & (iy >= 0) & (ix < w) & (iy < h)
            inside = np.zeros(len(ts), bool)
            inside[ok] = M[iy[ok], ix[ok]] > 0.5
            edges = np.flatnonzero(np.diff(np.concatenate([[0], inside.astype(np.int8), [0]])))
            for s0, s1 in zip(edges[::2], edges[1::2]):
                if s1 - s0 < 4: continue
                seg = pts[s0:s1] + np.array([x0, y0], np.float32)
                self.brush(seg, width, taper=(taper * 0.5, taper), swell=0.1, smooth=False, jitter=jitter, clip=clip)

    def speed(self, origin, direction, n=7, length=300.0, spread=120.0, width=4.0, gap=0.0, seed=None):
        """speed lines: a bundle of tapered strokes trailing behind a moving thing (direction = where it came from)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        d = np.asarray(direction, np.float32); d = d / np.linalg.norm(d)
        p = np.array([-d[1], d[0]], np.float32)
        o = np.asarray(origin, np.float32)
        for i in range(n):
            off = (i / max(n - 1, 1) - 0.5) * spread + r.normal(0, spread * 0.04)
            start = o + p * off + d * (gap + r.uniform(0, length * 0.25))
            L = length * r.uniform(0.45, 1.0)
            self.brush([start, start + d * L * 0.5, start + d * L], width * r.uniform(0.7, 1.15), taper=(0.05, 0.85),
                       swell=0.0, jitter=0.2)

    # ------------------------------------------------------------ lettering
    def text_mask(self, text, x, y, size, face='letter', align='centre', leading=1.18, jitter=1.0, rot=0.0,
                  anchor='mm', tracking=0.0):
        """hand lettering -> (full mask, (x0, y0, x1, y1)). Every glyph is placed by hand: a hair off the
        baseline and a hair rotated. anchor: 'mm' centres the block on (x, y), 'lt' puts its top-left there."""
        f = _font(face, size)
        lines = text.split('\n')
        r = self.rng
        asc = f.getbbox('H')[1]
        cap = f.getbbox('H')[3] - asc
        lh = size * leading
        widths = [sum(f.getlength(ch) + tracking * size for ch in ln) - tracking * size for ln in lines]
        bw = max(widths) if widths else 0
        bh = cap + lh * (len(lines) - 1)
        ox = x - bw / 2 if anchor[0] == 'm' else (x - bw if anchor[0] == 'r' else x)
        oy = y - bh / 2 if anchor[1] == 'm' else (y - bh if anchor[1] == 'b' else y)
        pad = int(size * 0.6) + 4
        cw, ch = int(bw + 2 * pad), int(bh + 2 * pad)
        buf = Image.new('L', (cw * 2, ch * 2), 0)
        for li, ln in enumerate(lines):
            lx = (bw - widths[li]) / 2 if align == 'centre' else (bw - widths[li] if align == 'right' else 0)
            cx = pad + lx
            by = pad + li * lh
            for chh in ln:
                adv = f.getlength(chh) + tracking * size
                if chh.strip():
                    gsz = int(size * 1.8) + 8
                    g = Image.new('L', (gsz * 2, gsz * 2), 0)
                    f2 = _font(face, size * 2)
                    ImageDraw.Draw(g).text((gsz * 0.5, gsz * 0.5 - asc * 2), chh, font=f2, fill=255)
                    if jitter:
                        g = g.rotate(r.normal(0, 2.2 * jitter), resample=Image.BICUBIC, center=(gsz * 0.5 + f2.getlength(chh) / 2, gsz * 0.5 + cap))
                    dy = r.normal(0, 0.035 * size * jitter)
                    px, py = int(round((cx - gsz * 0.25) * 2)), int(round((by + dy - gsz * 0.25) * 2))
                    reg = buf.crop((px, py, px + gsz * 2, py + gsz * 2))
                    buf.paste(Image.fromarray(np.maximum(np.asarray(reg), np.asarray(g))), (px, py))
                cx += adv
        sm = buf.resize((cw, ch), Image.BOX)
        if rot:
            sm = sm.rotate(rot, resample=Image.BICUBIC, expand=True)
        a = np.asarray(sm, np.float32) / 255
        m = np.zeros((self.H, self.W), np.float32)
        hh, ww = a.shape
        X0 = int(round(ox - pad - (ww - cw) / 2)); Y0 = int(round(oy - pad - (hh - ch) / 2))
        sx0, sy0 = max(0, -X0), max(0, -Y0)
        dx0, dy0 = max(0, X0), max(0, Y0)
        dx1, dy1 = min(self.W, X0 + ww), min(self.H, Y0 + hh)
        if dx1 > dx0 and dy1 > dy0:
            m[dy0:dy1, dx0:dx1] = a[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
        return m, (ox, oy, ox + bw, oy + bh)

    def letter(self, text, x, y, size=34, face='letter', align='centre', colour=None, **kw):
        """hand lettering in black (or in a colour on the colour plates). Returns the text block's box"""
        m, box = self.text_mask(text, x, y, size, face, align, **kw)
        if colour is None:
            np.maximum(self.key, m, out=self.key)
        else:
            self._set(m, colour)
        return box

    def balloon(self, text, x, y, size=36, tail=None, kind='speech', pad=(34, 24), width=4.2, face='letter',
                colour=WHITE, seed=None):
        """a speech balloon (kind='speech'), a shout ('yell': a jagged burst) or a thought ('thought'), lettered.
        tail: the point the tail aims at (the speaker's mouth). Returns the balloon mask"""
        m, (x0, y0, x1, y1) = self.text_mask(text, x, y, size, face, 'centre')
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = (x1 - x0) / 2 * 1.16 + pad[0], (y1 - y0) / 2 * 1.30 + pad[1]
        r = np.random.default_rng(self._seed() if seed is None else seed)
        if kind == 'yell':
            spikes = max(10, int((rx + ry) / 22))
            P = self.burst_pts(cx, cy, rx * 1.12, ry * 1.22, spikes, 0.2, int(r.integers(1 << 30)))
        elif kind == 'thought':                       # a cloud: scallops all the way round
            k = max(9, int((rx + ry) / 16))
            t = np.linspace(0, 2 * np.pi, k * 16, endpoint=False)
            bump = np.abs(np.sin(t * k / 2 + r.uniform(0, 3))) ** 0.6
            P = np.stack([cx + np.cos(t) * rx * (0.96 + 0.12 * bump), cy + np.sin(t) * ry * (0.94 + 0.16 * bump)], 1).astype(np.float32)
        else:
            t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
            wob = 1 + 0.025 * np.sin(3 * t + r.uniform(0, 6)) + 0.015 * np.sin(5 * t + r.uniform(0, 6))
            P = np.stack([cx + np.cos(t) * rx * wob, cy + np.sin(t) * ry * wob], 1).astype(np.float32)
        B = self.mask(P)
        if tail is not None and kind != 'thought':
            tx, ty = tail
            ang = np.arctan2((ty - cy) / ry, (tx - cx) / rx)
            base = []
            for da in (-0.20, 0.20):
                base.append((cx + np.cos(ang + da) * rx * 0.86, cy + np.sin(ang + da) * ry * 0.86))
            mid = ((base[0][0] + base[1][0]) / 2, (base[0][1] + base[1][1]) / 2)
            bend = np.array([-(ty - mid[1]), tx - mid[0]], np.float32) * 0.12
            ctrl = (mid[0] + (tx - mid[0]) * 0.5 + bend[0], mid[1] + (ty - mid[1]) * 0.5 + bend[1])
            T = np.vstack([spline([base[0], ((base[0][0] + ctrl[0]) / 2, (base[0][1] + ctrl[1]) / 2), (tx, ty)], 10),
                           spline([(tx, ty), ((base[1][0] + ctrl[0]) / 2, (base[1][1] + ctrl[1]) / 2), base[1]], 10)])
            B = np.maximum(B, self.mask(T))
        if kind == 'thought' and tail is not None:      # a trail of shrinking bubbles toward the thinker
            tx, ty = tail
            ang = np.arctan2((ty - cy) / ry, (tx - cx) / rx)
            ex, ey = cx + np.cos(ang) * rx * 1.08, cy + np.sin(ang) * ry * 1.08
            for k, f in enumerate((0.22, 0.55, 0.85)):
                bx, by = ex + (tx - ex) * f, ey + (ty - ey) * f
                B = np.maximum(B, self.circle(bx, by, max(4.0, size * (0.42 - 0.12 * k))))
        self.key *= 1 - B
        self._set(B, colour)
        self.mask_outline(B, width, heavy=width * 0.5)
        np.maximum(self.key, m, out=self.key)
        return B

    def caption(self, x0, y0, x1, y1, text, size=30, colour=YELLOW, width=4.0, face='letter', align='left', pad=18):
        """a caption box: a hand-ruled rectangle of flat colour with lettering"""
        r = self.rng
        j = lambda: r.normal(0, 1.2)
        P = np.array([(x0 + j(), y0 + j()), (x1 + j(), y0 + j()), (x1 + j(), y1 + j()), (x0 + j(), y1 + j())], np.float32)
        a = self.part(P, colour, width=0, line=False)
        for i in range(4):
            p, q = P[i], P[(i + 1) % 4]
            v = (q - p) / np.linalg.norm(q - p)
            self.brush([p - v * 2, (p + q) / 2, q + v * 2], width, taper=(0.02, 0.03), swell=0.0, jitter=0.3)
        if align == 'left':
            self.letter(text, x0 + pad, y0 + pad, size, face, 'left', anchor='lt')
        else:
            self.letter(text, (x0 + x1) / 2, (y0 + y1) / 2, size, face, 'centre')
        return a

    def sfx(self, text, x, y, size=120, colour=YELLOW, rot=0.0, width=6.0, shade=RED, shade_off=(7, 7), face='logo',
            tracking=0.04, bounce=0.06):
        """a sound effect: fat letters, each bounced a little, a colour face, a coloured drop shade, black outline"""
        f = _font(face, size)
        widths = [f.getlength(ch) + tracking * size for ch in text]
        total = sum(widths) - tracking * size
        a = np.deg2rad(rot)
        u = np.array([np.cos(a), -np.sin(a)], np.float32)
        v = np.array([np.sin(a), np.cos(a)], np.float32)
        M = np.zeros((self.H, self.W), np.float32)
        s = -total / 2
        for i, ch in enumerate(text):
            cxy = np.array([x, y], np.float32) + u * (s + widths[i] / 2)
            sz = size * (1 + bounce * np.sin(i * 1.7 + 0.5))
            m, _ = self.text_mask(ch, float(cxy[0]), float(cxy[1] + self.rng.normal(0, size * 0.03)), sz, face,
                                  jitter=0, rot=rot + self.rng.normal(0, 4))
            M = np.maximum(M, m)
            s += widths[i]
        if shade is not None:
            S = np.clip(shift(M, *shade_off) - M, 0, 1)
            self.key *= 1 - np.maximum(M, S)
            self._set(S, shade)
            self.mask_outline(np.maximum(M, shift(M, *shade_off)), width, heavy=0)
        else:
            self.key *= 1 - M
        self._set(M, colour)
        self.mask_outline(M, width * 0.6, heavy=0)
        return M

    def logo(self, text, quad, vp=None, depth=28.0, colours=(YELLOW, GOLD, ORANGE), shade=RED, shadow=BLUE,
             shadow_off=(10, 12), outline=8.0, inner=3.2, face='logo', tracking=0.02, glints=0):
        """a cover logo: block letters drawn in perspective onto `quad` (top-left, top-right, bottom-right,
        bottom-left), extruded `depth` px toward the vanishing point `vp`, a face banded light to dark from the top,
        a coloured extrusion, a drop shadow and a fat black outline round the whole block. Returns the face mask"""
        f = _font(face, 400)
        widths = [f.getlength(ch) for ch in text]
        tw = int(sum(widths) + tracking * 400 * (len(text) - 1)) + 40
        top = f.getbbox('H')[1]
        cap = f.getbbox('H')[3] - top
        src = Image.new('L', (tw, cap + 40), 0)
        d = ImageDraw.Draw(src)
        xx = 20
        for ch, wv in zip(text, widths):
            d.text((xx, 20 - top), ch, font=f, fill=255)
            xx += wv + tracking * 400
        bb = src.getbbox()
        src = src.crop(bb)
        sw, sh = src.size
        Q = np.asarray(quad, np.float32)
        pad = int(depth + max(abs(shadow_off[0]), abs(shadow_off[1])) + outline + inner + 14)
        x0, y0 = int(max(0, Q[:, 0].min() - pad)), int(max(0, Q[:, 1].min() - pad))
        x1, y1 = int(min(self.W, Q[:, 0].max() + pad)), int(min(self.H, Q[:, 1].max() + pad))
        sl = (slice(y0, y1), slice(x0, x1))
        w, h = x1 - x0, y1 - y0
        ss = 2
        co = _persp([((qx - x0) * ss, (qy - y0) * ss) for qx, qy in Q.tolist()], [(0, 0), (sw, 0), (sw, sh), (0, sh)])
        face_im = src.transform((w * ss, h * ss), Image.PERSPECTIVE, co, Image.BICUBIC).resize((w, h), Image.BOX)
        ramp = Image.fromarray(np.tile(np.linspace(0, 255, sh)[:, None], (1, sw)).astype(np.uint8))
        vmap_im = ramp.transform((w * ss, h * ss), Image.PERSPECTIVE, co, Image.BILINEAR).resize((w, h), Image.BOX)
        F = np.asarray(face_im, np.float32) / 255
        V = np.asarray(vmap_im, np.float32) / 255
        U = F.copy()
        if vp is not None and depth > 0:                      # extrude: the face shrunk step by step toward vp
            Fi = Image.fromarray((F * 255).astype(np.uint8))
            vx, vy = vp
            dist = float(np.hypot(Q[:, 0].mean() - vx, Q[:, 1].mean() - vy)) + 1e-3
            for k in np.linspace(0, 1, max(8, int(depth * 1.2)))[1:]:
                sc = 1 - depth / dist * k
                coef = (1 / sc, 0, (x0 - vx) / sc + vx - x0, 0, 1 / sc, (y0 - vy) / sc + vy - y0)
                np.maximum(U, np.asarray(Fi.transform((w, h), Image.AFFINE, coef, Image.BILINEAR), np.float32) / 255, out=U)
        E = np.clip(U - F, 0, 1)
        Sd = np.clip(shift(U, *shadow_off) - U, 0, 1) if shadow is not None else None
        self.key[sl] *= 1 - (U if Sd is None else np.maximum(U, Sd))
        if Sd is not None: self._set(Sd, shadow, sl)
        self._set(E, shade, sl)
        n = len(colours)
        band = np.clip((V * n).astype(np.int32), 0, n - 1)
        for i, col in enumerate(colours):
            self._set(F * (band == i), col, sl)
        if glints:
            r = self.rng
            for _ in range(glints):
                gx = r.uniform(Q[0, 0] + 30, Q[1, 0] - 30)
                gy = np.interp(gx, [Q[0, 0], Q[1, 0]], [Q[0, 1], Q[1, 1]])
                hgt = np.interp(gx, [Q[3, 0], Q[2, 0]], [Q[3, 1], Q[2, 1]]) - gy
                p0 = (gx, gy + hgt * 0.12); p1 = (gx + hgt * 0.10, gy + hgt * 0.36)
                g = self.mask(self.tube_pts([p0, p1], [hgt * 0.035, hgt * 0.05]))[sl]
                self._set(g * F, WHITE, sl)
        self.mask_outline(U, outline, heavy=outline * 0.4, sl=sl)
        if inner:
            ring = np.clip(self.grow(F, inner * 0.5) - self.shrink(F, inner * 0.5), 0, 1)
            np.maximum(self.key[sl], ring * self.grow(U, 1), out=self.key[sl])
        out = np.zeros((self.H, self.W), np.float32)
        out[sl] = F
        return out

    # ------------------------------------------------------------ press
    STRIP = 180                                   # the press works in bands of rows (keeps the memory small)

    def _rows(self):
        for y0 in range(0, self.H, self.STRIP):
            yield y0, min(self.H, y0 + self.STRIP)

    def _screen_maps(self):
        """per plate: the Ben-Day spot function, its anti-aliasing width, ink density, ragged-edge noise and paper
        pits (kept as float16), plus each colour separation's hand-painted wander"""
        if self._press_cache is not None: return self._press_cache
        H, W = self.H, self.W
        r = np.random.default_rng(self.seed + 4242)
        g = np.linspace(0, 1, 257)[:-1]
        uu, vv = np.meshgrid(g, g)
        sref = np.sort((0.5 - 0.25 * (np.cos(2 * np.pi * uu) + np.cos(2 * np.pi * vv))).ravel())
        cache = {'cdf': (np.linspace(0, 1, len(sref)).astype(np.float32), sref.astype(np.float32))}
        for p in 'CMYK':
            ang = np.deg2rad(SCREEN_ANGLE[p])
            ph = r.uniform(0, 1, 2)
            n1 = _norm_noise(r, H, W, 0.9)
            n2 = noise2d(H, W, self.pitch * 1.2, 1, int(r.integers(1 << 30)))
            S16, F16 = np.empty((H, W), np.float16), np.empty((H, W), np.float16)
            for y0, y1 in self._rows():
                X, Y = self.XX[y0:y1], self.YY[y0:y1]
                u = 2 * np.pi * ((X * np.cos(ang) + Y * np.sin(ang)) / self.pitch + ph[0])
                v = 2 * np.pi * ((-X * np.sin(ang) + Y * np.cos(ang)) / self.pitch + ph[1])
                su, sv = np.sin(u), np.sin(v)
                S16[y0:y1] = 0.5 - 0.25 * (np.cos(u) + np.cos(v)) + 0.022 * n1[y0:y1] + 0.03 * (n2[y0:y1] - 0.5)
                F16[y0:y1] = np.maximum(0.25 * 2 * np.pi / self.pitch * np.sqrt(su * su + sv * sv), 0.03)
            del n1, n2
            dens = (0.86 if p != 'K' else 0.94) + (0.16 if p != 'K' else 0.06) * noise2d(H, W, 70, 3, int(r.integers(1 << 30)))
            dens *= 1 - 0.10 * (noise2d(H, W, 6, 2, int(r.integers(1 << 30))) - 0.5)
            rag = (_norm_noise(r, H, W, 0.75) * 0.11).astype(np.float16)
            pits = smoothstep(0.80, 0.93, self.tooth + 0.08 * _norm_noise(r, H, W, 0.5)).astype(np.float16)
            cache[p] = (S16, F16, dens.astype(np.float16), rag, pits)
        if self.slop:
            cache['slop'] = {p: ((noise2d(H, W, 140, 2, int(r.integers(1 << 30))) - 0.5).astype(np.float16),
                                 (noise2d(H, W, 140, 2, int(r.integers(1 << 30))) - 0.5).astype(np.float16)) for p in 'CMY'}
        self._press_cache = cache
        return cache

    def _warp(self, a, p, a0, a1, slop=None):
        """rows a0..a1 of a plate as it actually lands: misregistration (+ the separation's hand-painted wander)"""
        dx, dy, rot = self.reg.get(p, (0, 0, 0))
        if not dx and not dy and not rot and slop is None: return a[a0:a1]
        th = np.deg2rad(rot)
        cx, cy = self.W / 2, self.H / 2
        XX, YY = self.XX[a0:a1] - cx - dx, self.YY[a0:a1] - cy - dy
        X = cx + XX * np.cos(th) - YY * np.sin(th)
        Y = cy + XX * np.sin(th) + YY * np.cos(th)
        if slop is not None:
            X += slop[0][a0:a1] * (2 * self.slop)
            Y += slop[1][a0:a1] * (2 * self.slop)
        X = np.clip(X, 0, self.W - 1.001); Y = np.clip(Y, 0, self.H - 1.001)
        x0 = X.astype(np.int32); y0 = Y.astype(np.int32)
        fx = X - x0; fy = Y - y0
        return (a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy) + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy

    def _screen(self, t, p, cache, a0, a1, gain=0.06):
        """tint -> Ben-Day dots: a threshold on the plate's spot function (with dot gain); 100 % prints solid"""
        s, fw = cache[p][0][a0:a1].astype(np.float32), cache[p][1][a0:a1].astype(np.float32)
        cdf_t, sref = cache['cdf']
        t = np.clip(t, 0, 1)
        t2 = np.clip(t + gain * 4 * t * (1 - t), 0, 1)                    # dot gain peaks at mid tones
        tau = np.interp(t2, cdf_t, sref).astype(np.float32)
        tau = np.where(t2 > 0.985, 1.5, tau)
        ink = np.clip((tau - s) / fw + 0.5, 0, 1)
        return ink * smoothstep(0.015, 0.05, t)

    def _soak(self, cov, p, cache, a0, a1):
        """newsprint drinks the ink: edges spread and go ragged, tiny dots drop out, pits stay bare"""
        rag, pits = cache[p][3][a0:a1], cache[p][4][a0:a1]
        b = blur(cov, 0.7)
        out = smoothstep(0.2, 0.8, b + rag)
        return out * (1 - (0.55 if p != 'K' else 0.35) * pits * smoothstep(0.6, 1.0, b))

    def _print(self, snap, plates, nwear):
        cache = self._screen_maps()
        img = self.paper_rgb.copy()
        pad = 6
        for y0, y1 in self._rows():
            a0, a1 = max(0, y0 - pad), min(self.H, y1 + pad)
            for p in 'YMCK':
                if p not in plates: continue
                if p == 'K':
                    t = self._warp(snap['k'], 'K', a0, a1)
                    cov = np.maximum(self._screen(t, 'K', cache, a0, a1), self._warp(snap['key'], 'K', a0, a1))
                else:
                    t = self._warp(snap[p], p, a0, a1, cache['slop'][p] if self.slop else None)
                    cov = self._screen(t, p, cache, a0, a1)
                cov = self._soak(cov, p, cache, a0, a1)[y0 - a0:y1 - a0]
                a = cov * cache[p][2][y0:y1]
                img[y0:y1] *= 1 - a[..., None] * (1 - INK[p])[None, None, :]
        for op in self.wear_ops[:nwear]:
            img = op(img)
        return np.clip(img, 0, 1)

    def _snap(self):
        q = lambda a: (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
        return {'C': q(self.g['C']), 'M': q(self.g['M']), 'Y': q(self.g['Y']), 'k': q(self.g['k']), 'key': q(self.key)}

    @staticmethod
    def _unsnap(s):
        return {k: v.astype(np.float32) / 255 for k, v in s.items()}

    # ------------------------------------------------------------ afterlife (wear)
    # every wear op is kept as a closure and applied after printing, only inside its own region

    def brown_edges(self, width=60.0, amount=1.0, colour=(0.80, 0.64, 0.42)):
        """the cover browned from the edges inward, unevenly"""
        H, W = self.H, self.W
        nz = noise2d(H, W, 150, 3, self._seed()).astype(np.float16)
        col = 1 - np.asarray(colour, np.float32)

        def op(img):
            for y0, y1 in self._rows():
                X, Y = self.XX[y0:y1], self.YY[y0:y1]
                d = np.minimum(np.minimum(X, W - 1 - X), np.minimum(Y, H - 1 - Y))
                f = np.clip(np.exp(-d / (width * (0.6 + 0.8 * nz[y0:y1]))) * amount, 0, 1)
                img[y0:y1] *= 1 - f[..., None] * col
            return img
        self.wear_ops.append(op)

    def spine(self, x=0.0, ticks=70, staples=(0.27, 0.73), reach=46.0):
        """the left edge is the spine fold: a soft roll, white stress ticks where the ink cracked, two staples
        with rust halos"""
        H = self.H
        RW = int(x + reach + 30)
        r = np.random.default_rng(self._seed())
        im = Image.new('L', (RW, H), 0)
        d = ImageDraw.Draw(im)
        for i in range(ticks):
            y = r.uniform(10, H - 10)
            L = reach * r.uniform(0.15, 1.0) ** 1.6
            a = r.normal(0, 0.12)
            n = max(3, int(L / 3))
            xs = x + 2 + np.linspace(0, L, n)
            ys = y + np.sin(a) * np.linspace(0, L, n) + r.normal(0, 0.7, n)
            wv = r.uniform(1.0, 2.4)
            for k in range(n - 1):
                d.line([(xs[k], ys[k]), (xs[k + 1], ys[k + 1])], fill=255, width=max(1, int(round(wv * (1 - k / n) + 0.3))))
        tick = blur(np.asarray(im, np.float32) / 255, 0.5)[..., None]
        X, Y = self.XX[:, :RW], self.YY[:, :RW]
        rust = 1 - np.array([0.62, 0.40, 0.22], np.float32)
        rust2 = 1 - np.array([0.55, 0.32, 0.15], np.float32)

        def op(img):
            sub = img[:, :RW]
            sub *= 1 - 0.10 * np.exp(-((X - x - 9) / 5.0) ** 2)[..., None]
            sub += 0.04 * np.exp(-((X - x - 15) / 4.0) ** 2)[..., None]
            sub *= 1 - tick
            sub += np.clip(self.paper_rgb[:, :RW] * 1.04, 0, 1) * tick
            for f in staples:
                yc = H * f
                y0, y1 = int(max(0, yc - 90)), int(min(H, yc + 90))
                s2, Xs, Ys = sub[y0:y1], X[y0:y1], Y[y0:y1]
                halo = np.exp(-(((Xs - x - 12) / 9.0) ** 2 + ((Ys - yc) / 44.0) ** 4))
                s2 *= 1 - 0.30 * halo[..., None] * rust
                bar = (np.clip(2.2 - np.abs(Xs - x - 12), 0, 1) * np.clip(31 - np.abs(Ys - yc), 0, 1))[..., None]
                sheen = 0.52 + 0.32 * np.clip(1 - np.abs(Xs - x - 11.3) / 1.6, 0, 1) - 0.12 * ((Ys - yc) / 31) ** 2
                metal = sheen[..., None] * np.array([0.97, 0.95, 0.92], np.float32)
                s2 *= 1 - bar
                s2 += metal * bar
                for end in (-1, 1):
                    ex = np.exp(-(((Xs - x - 12) / 3.0) ** 2 + ((Ys - yc - end * 31) / 3.5) ** 2))
                    s2 *= 1 - 0.35 * ex[..., None] * rust2
            return img
        self.wear_ops.append(op)

    def corner(self, which='br', radius=70.0, fold=True):
        """a rubbed, dog-eared corner: ink scuffed off toward the tip, a small diagonal crease"""
        H, W = self.H, self.W
        cx = W - 1 if which[1] == 'r' else 0
        cy = H - 1 if which[0] == 'b' else 0
        R = int(radius + 4)
        ys = slice(max(0, cy - R), cy + 1) if cy else slice(0, R)
        xs = slice(max(0, cx - R), cx + 1) if cx else slice(0, R)
        X, Y = self.XX[ys, xs], self.YY[ys, xs]
        h, w = X.shape
        nz = noise2d(h, w, 9, 3, self._seed())
        fib = _norm_noise(np.random.default_rng(self._seed()), h, w, 0.7)
        rub = np.clip(1 - np.hypot(X - cx, Y - cy) / radius, 0, 1) ** 1.5
        rub = (smoothstep(0.25, 0.75, rub + 0.45 * (nz - 0.5) + 0.12 * fib) * 0.85)[..., None]

        def op(img):
            img[ys, xs] = img[ys, xs] * (1 - rub) + self.paper_rgb[ys, xs] * 0.98 * rub
            return img
        self.wear_ops.append(op)
        if fold:
            sx = -1 if which[1] == 'r' else 1
            sy = -1 if which[0] == 'b' else 1
            self.crease((cx + sx * radius * 0.95, cy + sy * 2), (cx + sx * 2, cy + sy * radius * 0.85), 1.0)

    def crease(self, p0, p1, strength=1.0):
        """a colour-breaking crease from p0 to p1: a cracked white line with a soft roll beside it"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        pad = 12
        ys = slice(int(max(0, min(p0[1], p1[1]) - pad)), int(min(self.H, max(p0[1], p1[1]) + pad + 1)))
        xs = slice(int(max(0, min(p0[0], p1[0]) - pad)), int(min(self.W, max(p0[0], p1[0]) + pad + 1)))
        X, Y = self.XX[ys, xs], self.YY[ys, xs]
        d = p1 - p0
        L = float(np.linalg.norm(d)) + 1e-6
        u = d / L
        n = np.array([-u[1], u[0]], np.float32)
        t = ((X - p0[0]) * u[0] + (Y - p0[1]) * u[1]) / L
        off = (X - p0[0]) * n[0] + (Y - p0[1]) * n[1]
        o = off - np.interp(t, np.linspace(0, 1, 64), fbm1d(64, 10, 3, self._seed()) * 2.0)
        inside = smoothstep(-0.02, 0.03, t) * smoothstep(-0.02, 0.03, 1 - t)
        h, w = X.shape
        crack = (np.exp(-(o / 0.9) ** 2) * inside * smoothstep(0.35, 0.6, noise2d(h, w, 7, 2, self._seed())) * strength)[..., None]
        shade = (0.10 * strength * np.exp(-((o - 4) / 4.0) ** 2) * inside)[..., None]
        lift = (0.05 * strength * np.exp(-((o + 3) / 3.0) ** 2) * inside)[..., None]

        def op(img):
            sub = img[ys, xs] * (1 - shade) + lift
            img[ys, xs] = sub * (1 - crack) + self.paper_rgb[ys, xs] * 1.03 * crack
            return img
        self.wear_ops.append(op)

    def foxing(self, n=40, colour=(0.66, 0.46, 0.24)):
        """small rusty-brown age spots"""
        r = np.random.default_rng(self._seed())
        col = 1 - np.asarray(colour, np.float32)
        spots = []
        for i in range(n):
            x, y = r.uniform(0, self.W), r.uniform(0, self.H)
            if r.random() < 0.5:
                x = r.choice([r.uniform(0, 160), r.uniform(self.W - 160, self.W)])
            rr = r.uniform(1.5, 7) * (1 + 2 * (r.random() < 0.1))
            k = int(rr * 2 + 6)
            x0, y0 = int(max(0, x - k)), int(max(0, y - k))
            x1, y1 = int(min(self.W, x + k + 1)), int(min(self.H, y + k + 1))
            if x1 <= x0 or y1 <= y0: continue
            im = Image.new('L', (x1 - x0, y1 - y0), 0)
            ImageDraw.Draw(im).ellipse([x - rr - x0, y - rr - y0, x + rr - x0, y + rr - y0], fill=int(r.uniform(40, 105)))
            spots.append((slice(y0, y1), slice(x0, x1), blur(np.asarray(im, np.float32) / 255, 1.6)[..., None]))

        def op(img):
            for ys, xs, f in spots:
                img[ys, xs] *= 1 - f * col
            return img
        self.wear_ops.append(op)

    # ------------------------------------------------------------ output
    def stage(self, name, plates='CMYK'):
        """keep the plates as they are now; on save they are proofed with only `plates` printed"""
        self.stages.append((name, plates, self._snap(), len(self.wear_ops)))

    def render(self, plates='CMYK'):
        snap = {k: v for k, v in self.g.items()}
        snap['key'] = self.key
        img = self._print(snap, plates, len(self.wear_ops))
        return Image.fromarray((img * 255 + 0.5).astype(np.uint8))

    def save(self, path, stages_dir=None, quality=88):
        img = self.render()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, plates, snap, nw) in enumerate(self.stages):
                im = self._print(self._unsnap(snap), plates, nw)
                Image.fromarray((im * 255 + 0.5).astype(np.uint8)).save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
