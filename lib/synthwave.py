"""synthwave — an 80s retro-future poster played back off a worn VHS tape (numpy + Pillow only).

Model: one pinhole camera over an endless flat world at dusk, painted like an airbrushed record sleeve, then
recorded to tape and played back on a CRT.
  camera     a level camera `eye` metres above the ground looking along +Z (X right, Y up, Z into the picture).
             A point lands at (vx + f*X/Z, horizon + f*(eye - Y)/Z): every line along Z runs to the vanishing
             point, sizes fall off as 1/Z. Ground pixels know their own world coordinates (Xg, Zg), so the grid,
             the sea and the road are evaluated per pixel and stay correct right down to the horizon.
  buffers    a display-space colour buffer painted far to near (sky, sun, mountains, city, ground, objects,
             lettering), and an emission buffer: anything that gives off light (sun, neon lines, windows, tail
             lights, the rim of the chrome title) writes its colour there too, and opaque things painted later
             blank the emission behind them. At the end the emission is bloomed at four radii and added, and a
             shoulder curve lets over-driven channels spill into the others, so neon cores burn toward white
             while their halos keep the colour.
  sky        a banded dusk gradient (ink-blue zenith, violet, magenta, coral at the horizon), stars thinning
             toward the bright horizon with a few four-point sparkles, optional thin streak clouds lit from below.
  sun        a disc with a vertical yellow-orange-pink gradient cut by horizontal slits that get thicker toward the
             bottom (the retro "venetian blind" sun); the slits are real gaps, the sky and its halo show through.
  mountains  a height field on a jittered world grid, split into triangles, painted back to front with flat
             dark faces and glowing edges whose colour runs from magenta at the foot to cyan on the ridges;
             distant rows dim, the foot sinks into the horizon haze.
  grid       analytic neon lines on the ground plane: the distance to the nearest line is measured in *screen*
             pixels (world distance / gradient), so lines keep an honest anti-aliased width, sub-pixel lines keep
             their energy, and where the cells shrink below a few pixels the pattern is replaced by its average
             instead of shimmering into moire. Lines fade into a pink ground haze with depth; the glossy ground
             carries a soft streak of the sun.
  sea        everything above the horizon mirrored about it, torn into horizontal bars: rows are shifted
             sideways in world-space bands and modulated by elongated dashes, so the sun's reflection breaks
             into the stacked glowing strokes of 80s airbrush art; Fresnel makes the far water the better mirror.
  road       glossy asphalt with a blurred reflection, neon edge lines and dashed centre line (all per pixel).
  objects    palm silhouettes (tapered, ring-notched trunk; fronds as drooping rachises with leaflets hanging on
             both sides, foreshortened by their azimuth; coconuts; a rim of sunset light on the sun side), a low
             city skyline with tiny lit windows and red aviation lights, a car seen from behind with a full-width
             tail-light bar reflected in the road.
  lettering  chrome: heavy italic caps with a dark keyline, a stepped extrusion, a pale rim that glows, a face
             that mirrors a sky (deep blue to almost white) above a sharp horizon and a warm ground below it, a
             bevel lit from the upper left and four-point glints. Neon script: a coloured tube with a white-hot
             core. Letter-spaced captions with side rules. VCR on-screen display in a 5x7 block font.
  tape       the last pass (only in the finished frame): luma softened with a faint ghost and ringing, chroma
             blurred and pulled to the right (YIQ), per-line jitter, one tracking band, head-switching noise at
             the bottom, streaky noise and a few dropouts; then the OSD, CRT scanlines, lifted blacks, vignette.

    from synthwave import Synthwave, MAGENTA, CYAN
    s = Synthwave(1920, 1080, seed=87, horizon=610, vp_x=1060, eye=3.5)
    s.sky(); s.stars(); s.sun(560, 640, 270)
    s.mountains(30, 1100, 900, 1700, 190)
    s.floor(); s.sea(coast=-9); s.road(-7, -2)
    s.palm(-8.5, 29, 11)
    s.chrome_text('COASTLINE', 1450, 230, 150)
    s.neon_script('Last Sunset', 1560, 370, 110)
    s.osd('PLAY \u25b6', 90, 70); s.vhs()
    s.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core import blur, smoothstep, load_font, text_mask, shift

MAGENTA, CYAN, VIOLET, ORANGE, YELLOW = '#ff2bd6', '#35e8ff', '#9b4dff', '#ff8a3d', '#ffe45c'
PINK, RED, WHITE = '#ff4f9a', '#ff2a3a', '#fff6fb'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _stops(t, stops):
    """piecewise-linear colour ramp: t (any shape) -> (..., 3); stops = [(t0, colour), ...] ascending"""
    t = np.asarray(t, np.float32)
    ts = np.array([s[0] for s in stops], np.float32)
    cs = np.stack([_c(s[1]) for s in stops])
    return np.stack([np.interp(t, ts, cs[:, i]) for i in range(3)], -1).astype(np.float32)


def _gblur(a, s):
    """gaussian blur of (H, W) or (H, W, C); large radii run at reduced resolution (same look, much faster)"""
    if s <= 0: return a.astype(np.float32).copy()
    if a.ndim == 3: return np.stack([_gblur(a[..., i], s) for i in range(a.shape[2])], -1)
    k = int(min(8, max(1, s // 4)))
    if k == 1: return blur(a, s)
    H, W = a.shape
    sm = np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize((max(2, W // k), max(2, H // k)), Image.BOX))
    sm = blur(sm, s / k)
    return np.asarray(Image.fromarray(sm, 'F').resize((W, H), Image.BILINEAR))


def _blur_axis(a, s, axis):
    """gaussian (three box passes) along one axis only"""
    if s < 0.3: return a.astype(np.float32).copy()
    out = a.astype(np.float32)
    w = int(np.sqrt(12 * s * s / 3 + 1)); w += (w % 2 == 0); r = w // 2
    for _ in range(3):
        pad = [(0, 0)] * out.ndim; pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(out, pad, mode='edge'), axis=axis, dtype=np.float64)
        n = c.shape[axis]
        out = ((np.take(c, np.arange(w, n), axis=axis) - np.take(c, np.arange(0, n - w), axis=axis)) / w).astype(np.float32)
    return out


def _sample(img, x, y):
    """bilinear sample of (H, W) or (H, W, C) at float pixel coordinates (clamped to the edge)"""
    H, W = img.shape[:2]
    x = np.clip(x, 0, W - 1.001); y = np.clip(y, 0, H - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32)
    fx = (x - x0).astype(np.float32); fy = (y - y0).astype(np.float32)
    if img.ndim == 3: fx = fx[..., None]; fy = fy[..., None]
    return ((img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx) * (1 - fy)
            + (img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx) * fy)


def _vnoise(x, y, seed=0):
    """smooth value noise at float coordinates (lattice spacing 1), in [0, 1]"""
    xi = np.floor(x); yi = np.floor(y)
    fx = x - xi; fy = y - yi
    fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy)
    xi = xi.astype(np.int64); yi = yi.astype(np.int64)

    def h(a, b):
        n = (a * 374761393 + b * 668265263 + seed * 144269477) & 0xffffffff
        n = ((n ^ (n >> 13)) * 1274126177) & 0xffffffff
        return ((n ^ (n >> 16)) & 0xffff).astype(np.float32) / 65535.0
    return ((h(xi, yi) * (1 - fx) + h(xi + 1, yi) * fx) * (1 - fy)
            + (h(xi, yi + 1) * (1 - fx) + h(xi + 1, yi + 1) * fx) * fy).astype(np.float32)


def _fbm(x, y, octaves=4, seed=0):
    out = 0.0; amp = 1.0; tot = 0.0; fr = 1.0
    for o in range(octaves):
        out = out + amp * _vnoise(x * fr, y * fr, seed + o * 7919); tot += amp; amp *= 0.5; fr *= 2.0
    return (out / tot).astype(np.float32)


def _dilate(m, r):
    """grow a 0..1 mask by about r px (max filter on an 8-bit copy)"""
    if r <= 0: return m
    im = Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8))
    n = int(r)
    while n > 0:
        k = min(n, 3); im = im.filter(ImageFilter.MaxFilter(2 * k + 1)); n -= k
    return np.asarray(im, np.float32) / 255


# ---------------------------------------------------------------- lettering fonts (never committed to the repo)
_FONTS = {   # (glob pattern, face index, already italic)
    'chrome': [('/System/Library/Fonts/Avenir Next.ttc', 9, True), ('/System/Library/Fonts/Supplemental/Futura.ttc', 4, False),
               ('/System/Library/Fonts/Supplemental/Arial Black.ttf', 0, False), ('/usr/share/fonts/**/DejaVuSans-BoldOblique.ttf', 0, True),
               ('/usr/share/fonts/**/LiberationSans-BoldItalic.ttf', 0, True), ('C:/Windows/Fonts/ariblk.ttf', 0, False)],
    'script': [('/System/Library/Fonts/Supplemental/Brush Script.ttf', 0, True), ('/System/Library/Fonts/Supplemental/SnellRoundhand.ttc', 2, True),
               ('/usr/share/fonts/**/z003*.[ot]tf', 0, True), ('C:/Windows/Fonts/BRUSHSCI.TTF', 0, True), ('C:/Windows/Fonts/segoesc.ttf', 0, True)],
    'caption': [('/System/Library/Fonts/Hiragino Sans GB.ttc', 2, False), ('/System/Library/Fonts/STHeiti Medium.ttc', 0, False),
                ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0, False), ('/usr/share/fonts/**/NotoSansCJK*.tt[cf]', 0, False),
                ('C:/Windows/Fonts/msyhbd.ttc', 0, False)],
}
_FCACHE = {}


def synth_font(kind, size):
    """(PIL font, is_italic) for 'chrome' (heavy italic caps), 'script' (brush script) or 'caption' (CJK sans).
    Override with $INKPAINT_FONT_CHROME / _SCRIPT / _CAPTION."""
    key = (kind, int(size))
    if key in _FCACHE: return _FCACHE[key]
    env = os.environ.get('INKPAINT_FONT_' + kind.upper())
    hit = None
    for pat, idx, it in ([(env, 0, kind == 'script')] if env else []) + _FONTS.get(kind, []):
        for p in glob.glob(pat, recursive=True):
            try:
                hit = (ImageFont.truetype(p, max(4, int(size)), index=idx), it); break
            except OSError:
                pass
        if hit: break
    if hit is None: hit = (load_font({'chrome': 'sans_bold', 'script': 'script'}.get(kind, 'cjk_sans'), size), False)
    _FCACHE[key] = hit
    return hit


# ---------------------------------------------------------------- VCR on-screen display: 5x7 block glyphs
_OSD = {
    'A': '.###.|#...#|#...#|#####|#...#|#...#|#...#', 'B': '####.|#...#|#...#|####.|#...#|#...#|####.',
    'C': '.###.|#...#|#....|#....|#....|#...#|.###.', 'D': '####.|#...#|#...#|#...#|#...#|#...#|####.',
    'E': '#####|#....|#....|####.|#....|#....|#####', 'F': '#####|#....|#....|####.|#....|#....|#....',
    'G': '.###.|#...#|#....|#.###|#...#|#...#|.####', 'H': '#...#|#...#|#...#|#####|#...#|#...#|#...#',
    'I': '.###.|..#..|..#..|..#..|..#..|..#..|.###.', 'J': '..###|...#.|...#.|...#.|...#.|#..#.|.##..',
    'K': '#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#', 'L': '#....|#....|#....|#....|#....|#....|#####',
    'M': '#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#', 'N': '#...#|#...#|##..#|#.#.#|#..##|#...#|#...#',
    'O': '.###.|#...#|#...#|#...#|#...#|#...#|.###.', 'P': '####.|#...#|#...#|####.|#....|#....|#....',
    'Q': '.###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#', 'R': '####.|#...#|#...#|####.|#.#..|#..#.|#...#',
    'S': '.####|#....|#....|.###.|....#|....#|####.', 'T': '#####|..#..|..#..|..#..|..#..|..#..|..#..',
    'U': '#...#|#...#|#...#|#...#|#...#|#...#|.###.', 'V': '#...#|#...#|#...#|#...#|#...#|.#.#.|..#..',
    'W': '#...#|#...#|#...#|#.#.#|#.#.#|#.#.#|.#.#.', 'X': '#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#',
    'Y': '#...#|#...#|.#.#.|..#..|..#..|..#..|..#..', 'Z': '#####|....#|...#.|..#..|.#...|#....|#####',
    '0': '.###.|#...#|#..##|#.#.#|##..#|#...#|.###.', '1': '..#..|.##..|..#..|..#..|..#..|..#..|.###.',
    '2': '.###.|#...#|....#|...#.|..#..|.#...|#####', '3': '#####|...#.|..#..|...#.|....#|#...#|.###.',
    '4': '...#.|..##.|.#.#.|#..#.|#####|...#.|...#.', '5': '#####|#....|####.|....#|....#|#...#|.###.',
    '6': '..##.|.#...|#....|####.|#...#|#...#|.###.', '7': '#####|....#|...#.|..#..|.#...|.#...|.#...',
    '8': '.###.|#...#|#...#|.###.|#...#|#...#|.###.', '9': '.###.|#...#|#...#|.####|....#|...#.|.##..',
    ':': '.....|..#..|..#..|.....|..#..|..#..|.....', '.': '.....|.....|.....|.....|.....|.##..|.##..',
    '-': '.....|.....|.....|#####|.....|.....|.....', '/': '....#|....#|...#.|..#..|.#...|#....|#....',
    "'": '..#..|..#..|.#...|.....|.....|.....|.....', ' ': '.....|.....|.....|.....|.....|.....|.....',
    '\u25b6': '#....|##...|###..|####.|###..|##...|#....', '\u25a0': '.....|#####|#####|#####|#####|#####|.....',
    '\u25c0': '....#|...##|..###|.####|..###|...##|....#', '\u2016': '##.##|##.##|##.##|##.##|##.##|##.##|##.##',
}


class Synthwave:
    def __init__(self, W=1920, H=1080, seed=0, horizon=None, vp_x=None, focal=1100.0, eye=3.5, record=True):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.hy = H * 0.565 if horizon is None else float(horizon)
        self.vx = W * 0.55 if vp_x is None else float(vp_x)
        self.f, self.eye = float(focal), float(eye)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.img = np.zeros((H, W, 3), np.float32)
        self.emi = np.zeros((H, W, 3), np.float32)
        dy = self.YY - self.hy
        self.below = np.clip(dy + 0.5, 0, 1)                               # ground coverage (horizon row anti-aliased)
        self.dyc = np.maximum(dy, 0.35)
        self.Zg = self.f * self.eye / self.dyc                            # world coordinates of every ground pixel
        self.Xg = (self.XX - self.vx) * self.Zg / self.f
        self.dXdx = self.Zg / self.f                                       # metres per pixel, used for anti-aliasing
        self.dXdy = -self.Xg / self.dyc
        self.dZdy = -self.Zg / self.dyc
        self.sun_info = None
        self.horizon_col = hexc('#ff5a86')
        self.osd_items, self.vhs_opts = [], None
        self.record = record
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ camera
    def project(self, X, Y, Z):
        """world metres -> screen pixels"""
        Z = np.maximum(Z, 1e-3)
        return self.vx + self.f * np.asarray(X) / Z, self.hy + self.f * (self.eye - np.asarray(Y)) / Z

    def ground_row(self, Z):
        return self.hy + self.f * self.eye / np.maximum(Z, 1e-3)

    # ------------------------------------------------------------ compositing
    def _over(self, mask, colour, emit=0.0, at=(0, 0)):
        """paint `colour` (3,) or an array shaped like `mask` + (3,) over the picture with coverage `mask`,
        placed with its top-left corner at `at`; emission behind it is replaced by colour * emit"""
        m = np.asarray(mask, np.float32)
        x0, y0 = int(at[0]), int(at[1])
        h, w = m.shape
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(self.W, x0 + w), min(self.H, y0 + h)
        if X1 <= X0 or Y1 <= Y0: return
        lm = m[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
        rows = np.nonzero(lm.max(1) > 1e-4)[0]; cols = np.nonzero(lm.max(0) > 1e-4)[0]
        if not len(rows): return
        ly0, ly1, lx0, lx1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        a = lm[ly0:ly1, lx0:lx1][..., None]
        sl = (slice(Y0 + ly0, Y0 + ly1), slice(X0 + lx0, X0 + lx1))
        col = np.asarray(colour, np.float32)
        if col.ndim == 3: col = col[Y0 - y0 + ly0:Y0 - y0 + ly1, X0 - x0 + lx0:X0 - x0 + lx1]
        e = np.asarray(emit, np.float32)
        if e.ndim >= 2: e = e[Y0 - y0 + ly0:Y0 - y0 + ly1, X0 - x0 + lx0:X0 - x0 + lx1]
        if e.ndim == 2: e = e[..., None]
        self.img[sl] = self.img[sl] * (1 - a) + col * a
        self.emi[sl] = self.emi[sl] * (1 - a) + col * e * a

    def _canvas(self, x0, y0, x1, y1, ss):
        """a supersampled local drawing surface; returns (image, draw, origin, to_local)"""
        x0, y0 = int(np.floor(x0)), int(np.floor(y0))
        w, h = max(1, int(np.ceil(x1)) - x0), max(1, int(np.ceil(y1)) - y0)
        im = Image.new('L', (w * ss, h * ss), 0)
        return im, ImageDraw.Draw(im), (x0, y0), (lambda px, py: ((px - x0) * ss, (py - y0) * ss))

    @staticmethod
    def _down(im, ss):
        w, h = im.size
        return np.asarray(im.resize((w // ss, h // ss), Image.BOX), np.float32) / 255

    # ------------------------------------------------------------ sky
    def sky(self, stops=None, ground=('#2a0834', '#08020f')):
        """dusk gradient from the zenith to the horizon; below it an unlit ground (horizon, bottom colours)
        until the floor, sea or road are laid over it"""
        stops = stops or [(0.0, '#03010f'), (0.3, '#0e0630'), (0.55, '#2a0b52'), (0.76, '#661470'),
                          (0.91, '#c02a78'), (1.0, '#ff6a6a')]
        t = np.clip(self.YY / self.hy, 0, 1)
        self.img[:] = _stops(t, stops)
        self.horizon_col = _c(stops[-1][1])
        if ground:
            g = np.clip((self.YY - self.hy) / (self.H - self.hy), 0, 1) ** 0.5
            self._over(self.below, _stops(g, [(0, ground[0]), (1, ground[1])]))

    def stars(self, n=1600, bright=14, y_max=None, seed=None):
        """stars thinning toward the bright horizon; the `bright` brightest get four-point sparkles"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        ym = self.hy * 0.82 if y_max is None else y_max
        H, W = self.H, self.W
        ys = ym * (1 - np.sqrt(1 - r.random(n))); xs = r.uniform(0, W - 1, n)
        mag = np.clip(r.pareto(2.4, n) * 0.22 + 0.06, 0, 1.6)
        mag *= np.clip(1 - ys / (self.hy * 0.9), 0, 1) ** 0.8               # the sky outshines them lower down
        tint = np.stack([_c('#ffffff'), _c('#cfe4ff'), _c('#ffd6f4'), _c('#fff1c9')])[r.integers(0, 4, n)]
        lay = np.zeros((H, W, 3), np.float32)
        x0 = xs.astype(int); y0 = ys.astype(int); fx = xs - x0; fy = ys - y0
        for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            yy = np.clip(y0 + dy, 0, H - 1); xx = np.clip(x0 + dx, 0, W - 1)
            np.add.at(lay, (yy, xx), (mag * wgt)[:, None] * tint)
        lay = np.stack([blur(lay[..., i], 0.5) for i in range(3)], -1) * 2.2
        # sparkles on the brightest
        top = np.argsort(-mag)[:bright]
        for i in top:
            L = 6 + 16 * min(1.0, mag[i])
            sl = (slice(max(0, int(ys[i] - L)), min(H, int(ys[i] + L) + 1)), slice(max(0, int(xs[i] - L)), min(W, int(xs[i] + L) + 1)))
            dx = self.XX[sl] - xs[i]; dy = self.YY[sl] - ys[i]
            spike = (np.exp(-np.abs(dx) / (L * 0.28)) * np.exp(-(dy / 0.7) ** 2) + np.exp(-np.abs(dy) / (L * 0.28)) * np.exp(-(dx / 0.7) ** 2))
            spike += np.exp(-(dx * dx + dy * dy) / 3.0) * 1.5
            lay[sl] += (spike * mag[i] * 0.9)[..., None] * tint[i]
        self.img += lay; self.emi += lay * 0.5

    def streaks(self, bands, colour='#2a0a44', lit='#ff6a8a', seed=None):
        """thin horizontal streak clouds: bands = [(y, x0, x1, thickness_px), ...]; dark bodies lit from below"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        for (y, x0, x1, th) in bands:
            sd = int(r.integers(1 << 20))
            u = (self.XX - x0) / max(1, x1 - x0)
            prof = smoothstep(0, 0.25, u) * smoothstep(1, 0.7, u)
            wav = (_fbm(self.XX / 260.0, np.full_like(self.XX, sd % 997), 3, sd) - 0.5) * th * 1.6
            thick = th * (0.35 + 0.9 * _fbm(self.XX / 140.0, np.full_like(self.XX, 3.0), 3, sd + 1)) * prof
            d = (self.YY - (y + wav))
            m = np.clip(thick * 0.5 + 0.5 - np.abs(d), 0, 1) * (prof > 0.01)
            under = smoothstep(-thick * 0.1, thick * 0.5, d)                # the underside catches the sunset
            col = _c(colour)[None, None] * (1 - under[..., None]) + _c(lit)[None, None] * under[..., None]
            self._over(m * 0.92, col, emit=under * 0.25)

    def sun(self, x, y, r, stops=None, bands=8, band_top=0.34, gaps=(0.2, 0.7), glow=1.0, level=0.4, gain=0.72):
        """the retro sun: a vertical gradient cut by horizontal slits that thicken toward the bottom.
        The slits are spread over the part above the horizon; glow is the halo painted into the sky first."""
        stops = stops or [(0.0, '#ffe95a'), (0.3, '#ffc03a'), (0.56, '#ff7a3a'), (0.8, '#ff3d7a'), (1.0, '#ff1f9f')]
        d = np.hypot(self.XX - x, self.YY - y)
        halo = np.exp(-(d / (r * 1.3)) ** 2) * 0.2 + np.exp(-(d / (r * 2.6)) ** 2) * 0.12 + np.exp(-(d / (r * 5)) ** 2) * 0.05
        hc = _stops(np.clip((self.YY - (y - r)) / (2 * r), 0, 1), [(0, '#ff9a4a'), (1, '#ff3d8a')])
        above = np.clip(self.hy - self.YY + 0.5, 0, 1)
        self.img += hc * (halo * above * glow)[..., None]
        top = y - r; bot = min(y + r, self.hy)
        v = np.clip((self.YY - top) / max(1.0, bot - top), 0, 1)
        col = _stops(v, stops)
        col = col * gain * (1 + 0.12 * np.exp(-(d / (r * 0.6)) ** 2))[..., None]    # bloom brings it back up
        disc = np.clip(r - d + 0.5, 0, 1) * above                          # it sets: nothing below the horizon
        y0 = top + band_top * (bot - top); pitch = (bot - y0) / max(1, bands)
        cut = np.zeros_like(disc)
        for k in range(bands):
            g = pitch * (gaps[0] + (gaps[1] - gaps[0]) * k / max(1, bands - 1))
            yc = y0 + pitch * (k + 0.62)
            cut = np.maximum(cut, np.clip(g / 2 + 0.5 - np.abs(self.YY - yc), 0, 1))
        self._over(disc * (1 - cut), col, emit=level)
        self.sun_info = (float(x), float(y), float(r))

    # ------------------------------------------------------------ far things
    def mountains(self, x0, x1, z0, z1, height, cell=(55.0, 80.0), seed=None, fill='#150629', edge=(MAGENTA, CYAN),
                  width=1.5, level=0.9, taper=(True, True), scale=320.0, haze=0.55, light=(-0.8, 0.35, 0.45), ss=3):
        """a wireframe range: a height field on a jittered world grid (x0..x1, z0..z1 metres), split into
        triangles and painted far to near: flat dark faces faintly lit by the sun, glowing edges magenta at the
        foot to cyan on the ridges. taper=(left, right): let the range fade to the ground at that end."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        cx, cz = cell
        nx = max(2, int(round((x1 - x0) / cx))); nz = max(2, int(round((z1 - z0) / cz)))
        X, Z = np.meshgrid(np.linspace(x0, x1, nx + 1), np.linspace(z0, z1, nz + 1))
        X[:, 1:-1] += r.uniform(-0.32, 0.32, (nz + 1, nx - 1)) * cx
        Z[1:-1, :] += r.uniform(-0.3, 0.3, (nz - 1, nx + 1)) * cz
        u = (X - x0) / (x1 - x0); w = (Z - z0) / (z1 - z0)
        envx = (smoothstep(0, 0.14, u) if taper[0] else 1.0) * (smoothstep(1, 0.86, u) if taper[1] else 1.0)
        envz = np.sin(np.pi * np.clip(0.1 + 0.75 * w, 0, 1)) ** 0.8 * smoothstep(0.0, 0.3, w)
        sd = int(r.integers(1 << 20))
        n = _fbm(X / scale, Z / scale, 4, sd)
        ridge = 1 - np.abs(2 * n - 1)
        Hh = height * envx * envz * (0.2 + 0.8 * ridge ** 1.5) * r.uniform(0.85, 1.15, X.shape)
        Hh[0, :] = 0
        sx, sy = self.project(X, Hh, Z)
        bx0, bx1 = max(0, sx.min() - 4), min(self.W, sx.max() + 4)
        by0, by1 = max(0, sy.min() - 4), min(self.H, sy.max() + 4)
        if bx1 <= bx0 or by1 <= by0: return
        cw, ch = int(np.ceil(bx1 - bx0)), int(np.ceil(by1 - by0))
        ox, oy = int(np.floor(bx0)), int(np.floor(by0))
        col = Image.new('RGB', (cw * ss, ch * ss)); alp = Image.new('L', (cw * ss, ch * ss)); emi = Image.new('RGB', (cw * ss, ch * ss))
        dc, da, de = ImageDraw.Draw(col), ImageDraw.Draw(alp), ImageDraw.Draw(emi)
        P = lambda j, i: ((sx[j, i] - ox) * ss, (sy[j, i] - oy) * ss)
        L = np.array(light, np.float32); L /= np.linalg.norm(L)
        fc = _c(fill); sunc = _c('#ff6a7a'); e0, e1 = _c(edge[0]), _c(edge[1])
        lw = max(1, int(round(width * ss)))
        for j in reversed(range(nz)):                                     # far rows first
            tris = []
            for i in range(nx):
                a, b, c, d = (j, i), (j, i + 1), (j + 1, i), (j + 1, i + 1)
                tris += [(a, b, d), (a, d, c)] if r.random() < 0.5 else [(a, b, c), (b, d, c)]
            fade = np.exp(-(Z[j, 0] - z0) / (2.2 * (z1 - z0)))
            for t in tris:
                p = np.array([(X[q], Hh[q], Z[q]) for q in t], np.float32)
                nrm = np.cross(p[1] - p[0], p[2] - p[0]); nrm /= np.linalg.norm(nrm) + 1e-6
                if nrm[1] < 0: nrm = -nrm
                lam = max(0.0, float(nrm @ L))
                cf = fc * (0.8 + 0.35 * lam) + sunc * 0.1 * lam
                poly = [P(*q) for q in t]
                dc.polygon(poly, fill=tuple(int(v) for v in np.clip(cf * 255, 0, 255))); da.polygon(poly, fill=255); de.polygon(poly, fill=(0, 0, 0))
            for t in tris:
                for q0, q1 in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
                    hgt = 0.5 * (Hh[q0] + Hh[q1]) / max(1e-6, height)
                    ce = e0 + (e1 - e0) * np.clip(hgt * 1.5, 0, 1) ** 0.9
                    cl = tuple(int(v) for v in np.clip(ce * 255 * (0.55 + 0.45 * fade), 0, 255))
                    cm = tuple(int(v) for v in np.clip(ce * 127 * level * fade, 0, 255))
                    dc.line([P(*q0), P(*q1)], fill=cl, width=lw); da.line([P(*q0), P(*q1)], fill=255, width=lw)
                    de.line([P(*q0), P(*q1)], fill=cm, width=lw)
        dn = lambda im: np.asarray(im.resize((cw, ch), Image.BOX), np.float32) / 255
        A = dn(alp); C = dn(col); E = dn(emi) * 2
        hz = haze * np.exp(-np.maximum(0, self.hy - (self.YY[oy:oy + ch, ox:ox + cw])) / 26.0)[..., None]
        C = C * (1 - hz) + self.horizon_col * hz * A[..., None]
        C = C / np.maximum(A, 1e-4)[..., None]
        self._over(A, C, emit=0.0, at=(ox, oy))
        sl = (slice(oy, oy + A.shape[0]), slice(ox, ox + A.shape[1]))
        self.emi[sl] += E

    def skyline(self, X0, X1, Z, heights=(18, 80), widths=(12, 34), colour='#1c0934', windows=0.2, tall=None,
                seed=None, haze=0.55, ss=3):
        """a distant city: blocks, setbacks, antennas with red lights, tiny lit windows; its foot in the haze.
        tall = (X, height) forces one landmark tower."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        s = self.f / Z
        gy = self.ground_row(Z)
        blocks = []
        X = X0
        while X < X1:
            wdt = r.uniform(*widths)
            mid = 1 - abs((X + wdt / 2 - (X0 + X1) / 2) / ((X1 - X0) / 2))
            h = r.uniform(heights[0], heights[0] + (heights[1] - heights[0]) * (0.35 + 0.65 * mid))
            blocks.append([X, wdt, h]); X += wdt * r.uniform(0.7, 1.05)
        if tall: blocks.append([tall[0] - 7, 14, tall[1]])
        top_px = max(b[2] for b in blocks) * s + 30
        x0p, x1p = self.vx + X0 * s - 10, self.vx + X1 * s + 10
        im, d, (ox, oy), T = self._canvas(x0p, gy - top_px, x1p, gy + 2, ss)
        win = Image.new('RGB', im.size); dw = ImageDraw.Draw(win)
        red = Image.new('L', im.size); dr = ImageDraw.Draw(red)
        wcols = [(255, 214, 140), (255, 190, 120), (140, 240, 255), (255, 140, 210)]
        for bx, bw, bh in sorted(blocks, key=lambda b: b[2]):
            L, R = self.vx + bx * s, self.vx + (bx + bw) * s
            topy = gy - bh * s
            d.rectangle([T(L, topy), T(R, gy + 1)], fill=255)
            kind = r.random()
            if kind < 0.3:                                               # setback crown
                inset = bw * r.uniform(0.18, 0.3) * s; th = bh * r.uniform(0.12, 0.2) * s
                d.rectangle([T(L + inset, topy - th), T(R - inset, topy)], fill=255); topy -= th
            elif kind < 0.42:                                            # spire
                cxp = (L + R) / 2; d.polygon([T(L + (R - L) * 0.3, topy), T(cxp, topy - bh * 0.25 * s), T(R - (R - L) * 0.3, topy)], fill=255)
                topy -= bh * 0.25 * s
            if bh > heights[1] * 0.55 and r.random() < 0.7:            # antenna + aviation light
                ax = L + (R - L) * r.uniform(0.3, 0.7); ah = r.uniform(6, 14) * s
                d.line([T(ax, topy), T(ax, topy - ah)], fill=255, width=max(1, int(0.8 * s * ss)))
                dr.ellipse([T(ax - 1.2, topy - ah - 1.2), T(ax + 1.2, topy - ah + 1.2)], fill=255)
            # windows: rows every 3.6 m, columns every 3 m
            rows = int(bh / 3.6); cols = max(1, int(bw / 3.0))
            for i in range(rows):
                wy = gy - (i + 0.6) * 3.6 * s
                if wy < gy - bh * s + 2: continue
                for k in range(cols):
                    if r.random() > windows: continue
                    wx = L + (k + 0.3) * (R - L) / cols
                    dw.rectangle([T(wx, wy), T(wx + 1.3 * s, wy + 1.4 * s)], fill=wcols[int(r.integers(0, 4)) if r.random() < 0.35 else 0])
        A = self._down(im, ss)
        Wn = np.asarray(win.resize(A.shape[::-1], Image.BOX), np.float32) / 255
        Rd = self._down(red, ss)
        yy = self.YY[oy:oy + A.shape[0], ox:ox + A.shape[1]]
        hz = (haze * np.exp(-np.maximum(0, gy - yy) / (0.35 * top_px)))[..., None]
        C = _c(colour) * (1 - hz) + self.horizon_col * 0.8 * hz
        self._over(A, C, at=(ox, oy))
        sl = (slice(oy, oy + A.shape[0]), slice(ox, ox + A.shape[1]))
        lights = Wn * 1.3 + Rd[..., None] * _c(RED) * 2.2
        self.img[sl] += lights * (1 - hz * 0.5); self.emi[sl] += lights * 0.9

    # ------------------------------------------------------------ ground
    def _lines(self, g, gdx, gdy, halfw, min_px=1.0):
        """coverage of neon lines at integer values of g (lines of half-width `halfw` in g units);
        gdx, gdy: derivatives of g per pixel. Sub-pixel lines keep their energy; dense lines fade to their mean."""
        grad = np.hypot(gdx, gdy) + 1e-9
        d = np.abs(g - np.round(g)) / grad                                  # px to the nearest line
        hw = halfw / grad
        hwe = np.maximum(hw, min_px * 0.5)
        cov = np.clip(hwe + 0.5 - d, 0, 1) * (hw / hwe)
        k = smoothstep(2.0, 7.0, 1 / grad)
        return cov * k + np.clip(2 * halfw, 0, 1) * (1 - k)

    def _region(self, X0, X1):
        """anti-aliased coverage of the ground strip X0 < X < X1"""
        gx = np.hypot(self.dXdx, self.dXdy) + 1e-9
        a = np.ones_like(self.Xg)
        if X0 is not None: a = a * np.clip(0.5 + (self.Xg - X0) / gx, 0, 1)
        if X1 is not None: a = a * np.clip(0.5 + (X1 - self.Xg) / gx, 0, 1)
        return a * self.below

    def _mirror(self, stretch=0.9, xs=None):
        """the picture above the horizon mirrored into the rows below it (sampled at columns xs)"""
        ys = self.hy - (self.YY - self.hy) * stretch
        ys = np.clip(ys, 0, self.hy - 1)
        xs = self.XX if xs is None else xs
        return _sample(self.img, xs, ys), _sample(self.emi, xs, ys)

    def floor(self, colour=MAGENTA, spacing=(2.4, 2.4), width=0.07, base='#12031f', haze=None, fog=150.0,
              level=1.0, scroll=0.0, gloss=0.3, x_range=(None, None)):
        """the neon grid: lines along Z every spacing[0] m and across it every spacing[1] m, `width` m wide,
        on a dark glossy floor fading into a pink haze toward the horizon; a soft streak of the sun on it"""
        hz = _c(haze) if haze is not None else self.horizon_col * 0.55 + _c(MAGENTA) * 0.25
        sx, sz = spacing
        T = np.exp(-self.Zg / fog)[..., None]
        near = np.clip((self.YY - self.hy) / (self.H - self.hy), 0, 1)
        basec = _c(base) * (0.8 + 0.4 * near[..., None])
        col = basec * T + hz * 0.6 * (1 - T)
        Ll = self._lines(self.Xg / sx, self.dXdx / sx, self.dXdy / sx, width / (2 * sx))
        Lt = self._lines((self.Zg - scroll) / sz, 0.0, self.dZdy / sz, width / (2 * sz))
        Lg = 1 - (1 - Ll) * (1 - Lt)
        vis = T ** 0.55
        lc = _c(colour)
        col = col * (1 - Lg[..., None] * vis) + lc * 1.45 * (Lg[..., None] * vis)
        em = lc * (Lg[..., None] * vis) * level
        if self.sun_info and gloss:
            x, y, r = self.sun_info
            wdt = r * (0.55 + 0.6 * near)
            st = np.exp(-((self.XX - x) / wdt) ** 2) * np.exp(-near * 2.2) * gloss
            col = col + _c('#ff6a6a') * st[..., None]
        hl = np.exp(-((self.YY - self.hy) / 2.2) ** 2) + 0.4 * np.exp(-((self.YY - self.hy) / 9) ** 2)
        col = col + hz * 0.6 * hl[..., None]; em = em + hz * 0.5 * hl[..., None]
        a = self._region(*x_range)
        self._over(a, col, emit=0.0)
        self.emi += em * a[..., None]

    def neon_line(self, X, colour=CYAN, width=0.12, level=1.1, dash=None, fog=140.0):
        """a neon line lying on the ground along Z at X (coastline, road edge); dash=(on, period) metres"""
        g = self.Xg - X
        cov = self._lines(g / 1000.0, self.dXdx / 1000.0, self.dXdy / 1000.0, width / 2000.0) * (np.abs(g) < 500)
        if dash:
            on, per = dash
            ph = np.mod(self.Zg, per)
            dz = np.abs(self.dZdy) + 1e-6
            cov = cov * np.clip(np.minimum(ph, on - ph) / dz + 0.5, 0, 1) * (1 - smoothstep(0.5, 2.0, dz / per * 4)) \
                + cov * (on / per) * smoothstep(0.5, 2.0, dz / per * 4)
        cov = cov * self.below
        T = np.exp(-self.Zg / fog) ** 0.5
        c = _c(colour)
        self._over(cov * T, c * 1.45, emit=level)

    def sea(self, coast=-9.0, base='#0a0520', reflect=(0.45, 0.95), bar=(4.0, 0.9), ripple=1.0, stretch=1.0,
            spread=0.5, sky=0.75, glitter=1.8, lines=0.16, line_colour=CYAN, seed=None):
        """water on the side X < coast: the sky, sun and far shore mirrored about the horizon and torn into
        horizontal bars. The water is cut into world bands bar[1] m deep; every band shifts sideways and is
        stretched or squeezed about the sun's column by up to +-spread, so the sun's reflection becomes a stack
        of glowing strokes of different lengths instead of a second disc; dashes bar[0] m long break them up.
        Light sources (the emission buffer) reflect `glitter` times stronger than the sky (`sky`)."""
        sd = self._seed() if seed is None else seed
        near = np.clip((self.YY - self.hy) / (self.H - self.hy), 0, 1)
        band = self.Zg / bar[1]
        bpx = np.abs(self.dZdy) / bar[1]                                     # bands per pixel
        res = 1 - smoothstep(0.25, 0.8, bpx)                                  # 1 where bands are resolved
        bi = np.floor(band); fr = band - bi
        one = np.ones_like(band)
        cx = self.sun_info[0] if self.sun_info else self.vx
        sc = 1 + (_vnoise(bi * 0.83, one * 1.5, sd + 3) - 0.5) * 2 * spread * (0.5 + 1.2 * near) * res
        dx = (_vnoise(bi * 0.9, one * 0.5, sd) - 0.5) * (6 + 50 * near) * ripple * res
        dx += (_vnoise(band * 0.23, one * 3.5, sd + 1) - 0.5) * (3 + 20 * near) * ripple
        m = smoothstep(0.3, 0.5, _vnoise(self.Xg / bar[0] + bi * 1.7, bi * 0.37 + 0.5, sd + 2))
        gap = smoothstep(0.0, 0.25, fr) * smoothstep(1.0, 0.75, fr)
        m = (m * (0.15 + 0.85 * gap)) * res + 0.5 * (1 - res)
        mir, mem = self._mirror(stretch, cx + (self.XX - cx) * sc + dx)
        mir = _blur_axis(_blur_axis(mir, 1.2, 0), 2.0, 1); mem = _blur_axis(_blur_axis(mem, 2.0, 0), 3.0, 1)
        R = reflect[0] + (reflect[1] - reflect[0]) * (1 - near) ** 2.5
        k = (0.08 + 0.92 * m) * R
        col = _c(base) * (1 - 0.5 * R[..., None]) + (mir * sky + mem * glitter) * k[..., None]
        em = mem * (k * 1.2)[..., None]
        if lines:
            Lt = self._lines(self.Zg / 3.0, 0.0, self.dZdy / 3.0, 0.03)
            T = np.exp(-self.Zg / 60.0) ** 0.5
            col = col + _c(line_colour) * (Lt * T * lines)[..., None]
            em = em + _c(line_colour) * (Lt * T * lines * 0.6)[..., None]
        a = self._region(None, coast)
        self._over(a, col, emit=0.0)
        self.emi = self.emi + em * a[..., None]

    def road(self, x0, x1, surface='#0b0316', edge=CYAN, centre='#ffe6a0', dash=(3.0, 8.0), gloss=0.35, level=1.0):
        """a glossy two-lane road between x0 and x1 (metres): blurred reflection, neon edges, dashed centre"""
        near = np.clip((self.YY - self.hy) / (self.H - self.hy), 0, 1)
        mir, mem = self._mirror(0.8)
        mir = _blur_axis(_blur_axis(mir, 16, 0), 2.5, 1)
        R = gloss * (0.35 + 0.65 * (1 - near) ** 2)
        col = _c(surface) * (0.8 + 0.4 * near[..., None]) + mir * R[..., None]
        a = self._region(x0, x1)
        self._over(a, col)
        self.emi += _blur_axis(mem, 16, 0) * (R * 0.5 * a)[..., None]
        self.neon_line(x0, edge, 0.14, level); self.neon_line(x1, edge, 0.14, level)
        self.neon_line((x0 + x1) / 2, centre, 0.12, level * 0.7, dash=dash)

    # ------------------------------------------------------------ objects
    def palm(self, X, Z, height=11.0, lean=0.1, fronds=10, seed=None, colour='#0a0314', rim='#ff5a8a', rim_side=None,
             spread=1.0, ss=3):
        """a palm silhouette standing at ground point (X, Z): tapered ring-notched trunk leaning by `lean`
        (fraction of height, + is right), a crown of drooping fronds with hanging leaflets, coconuts, and a thin
        rim of sunset light on the side facing the sun"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        s = self.f / Z
        bx, by = self.project(X, 0, Z)
        crown = 4.6 * spread
        x0p = bx - (crown + abs(lean) * height + 1) * s; x1p = bx + (crown + abs(lean) * height + 1) * s
        y0p = by - (height + crown * 0.8) * s; y1p = by + 3
        im, d, (ox, oy), T = self._canvas(x0p, y0p, x1p, y1p, ss)
        # trunk centreline (metres, y up) -> pixels
        u = np.linspace(0, 1, 90)
        bend = r.uniform(-0.04, 0.04) * height
        cxm = lean * height * u ** 1.7 + bend * np.sin(np.pi * u)
        cym = height * u
        px = bx + cxm * s; py = by - cym * s
        tx = np.gradient(px); ty = np.gradient(py); tl = np.hypot(tx, ty) + 1e-6; nx, ny = -ty / tl, tx / tl
        ring = 1 - 0.14 * (np.mod(cym / 0.32, 1.0) < 0.3)
        half = (0.27 - 0.12 * u + 0.12 * np.exp(-u / 0.05)) * s * ring
        left = [T(px[i] + nx[i] * half[i], py[i] + ny[i] * half[i]) for i in range(len(u))]
        right = [T(px[i] - nx[i] * half[i], py[i] - ny[i] * half[i]) for i in range(len(u))][::-1]
        d.polygon(left + right, fill=255)
        topx, topy = px[-1], py[-1]

        def blade(p0, p1, w0, w1):
            p0 = np.array(p0); p1 = np.array(p1); dv = p1 - p0; L = np.hypot(*dv) + 1e-6; nv = np.array([-dv[1], dv[0]]) / L
            d.polygon([T(*(p0 + nv * w0)), T(*(p1 + nv * w1)), T(*(p1 - nv * w1)), T(*(p0 - nv * w0))], fill=255)
        # fronds spread evenly round the crown (azimuth phi: 0 = to the right, pi/2 = toward the camera)
        az = np.linspace(0, 2 * np.pi, fronds, endpoint=False) + r.uniform(0, 2 * np.pi) + r.normal(0, 0.18, fronds)
        elevs = np.linspace(1.05, 0.12, fronds - 2)[r.permutation(fronds - 2)]  # a spread from steep to flat fronds
        for k, phi in enumerate(az):
            dead = k < 2                                                        # two old fronds hang down the trunk
            L = r.uniform(3.8, 4.8) * spread * (0.75 if dead else 1)
            elev = r.uniform(-0.6, -0.3) if dead else elevs[k - 2] + r.normal(0, 0.08)
            droop = (r.uniform(0.9, 1.2) + 0.5 * elev) if not dead else r.uniform(0.6, 0.9)
            beta = r.uniform(0.7, 0.95) if not dead else 1.25                 # how steeply the leaflets hang
            t = np.linspace(0, 1, 30)
            hor = L * t * np.cos(elev)
            ver = L * (np.sin(elev) * t - droop * 0.5 * t * t)
            fx = topx + hor * np.cos(phi) * s; fy = topy - ver * s               # cos(phi): foreshortened toward camera
            for i in range(len(t) - 1):
                blade((fx[i], fy[i]), (fx[i + 1], fy[i + 1]), 0.075 * s * (1 - 0.75 * t[i]), 0.075 * s * (1 - 0.75 * t[i + 1]))
            # leaflets on both sides, built in 3D and projected: a sweep along the rachis toward the tip, a
            # sideways part (only seen when the frond points at us) and a droop
            dh = np.gradient(hor); dv = np.gradient(ver); dl = np.hypot(dh, dv) + 1e-6; dh /= dl; dv /= dl
            side = np.array([-np.sin(phi), 0.0, np.cos(phi)])
            for i in range(2, len(t) - 1):
                ll = (0.3 + 1.1 * np.sin(np.pi * min(1.0, t[i] * 1.02)) ** 0.7) * (1 - 0.2 * t[i]) * spread * (0.75 if dead else 1)
                tan = np.array([np.cos(phi) * dh[i], dv[i], np.sin(phi) * dh[i]])
                for sgn in (-1, 1):
                    b = beta + r.normal(0, 0.06)
                    v3 = tan * 0.62 + side * sgn * np.cos(b) + np.array([0.0, -np.sin(b), 0.0])
                    v3 /= np.linalg.norm(v3)
                    blade((fx[i], fy[i]), (fx[i] + v3[0] * ll * s, fy[i] - v3[1] * ll * s), 0.05 * s, 0.006 * s)
        for _ in range(4):                                                     # coconuts
            cx_ = topx + r.normal(0, 0.18) * s; cy_ = topy + r.uniform(0.1, 0.45) * s; rr = 0.19 * s
            d.ellipse([T(cx_ - rr, cy_ - rr), T(cx_ + rr, cy_ + rr)], fill=255)
        A = self._down(im, ss)
        self._over(A, _c(colour), at=(ox, oy))
        # rim light on the side facing the sun
        if rim:
            sgn = rim_side if rim_side is not None else (-1 if (self.sun_info and self.sun_info[0] < bx) else 1)
            k = max(1.2, 0.08 * s)
            rimm = np.clip(A - shift(A, -sgn * k, k * 0.6), 0, 1) * A
            self._over(rimm, _c(rim), emit=0.9, at=(ox, oy))

    def car(self, X, Z, body='#10041c', light=RED, level=2.2, ss=4):
        """a low 80s coupe seen from behind: body, cabin, full-width tail-light bar, and the lights' streak
        reflected in the glossy road below"""
        s = self.f / Z
        bx, by = self.project(X, 0, Z)
        im, d, (ox, oy), T = self._canvas(bx - 1.3 * s, by - 1.5 * s, bx + 1.3 * s, by + 0.2 * s, ss)
        lt = Image.new('L', im.size); dl = ImageDraw.Draw(lt)
        hl = Image.new('L', im.size); dh = ImageDraw.Draw(hl)
        P = lambda mx, my: T(bx + mx * s, by - my * s)
        d.polygon([P(-0.92, 0.18), P(-0.95, 0.62), P(-0.86, 0.78), P(0.86, 0.78), P(0.95, 0.62), P(0.92, 0.18)], fill=255)
        d.polygon([P(-0.66, 0.78), P(-0.48, 1.12), P(0.48, 1.12), P(0.66, 0.78)], fill=255)          # cabin
        d.rectangle([P(-0.86, 0.2), P(-0.56, 0.0)], fill=255); d.rectangle([P(0.56, 0.2), P(0.86, 0.0)], fill=255)   # tyres
        dh.polygon([P(-0.62, 0.8), P(-0.47, 1.1), P(0.47, 1.1), P(0.62, 0.8)], fill=110)            # rear glass catches the sky
        dh.line([P(-0.86, 0.77), P(0.86, 0.77)], fill=200, width=max(1, int(0.05 * s * ss)))
        dl.rectangle([P(-0.9, 0.62), P(0.9, 0.5)], fill=255)                                        # tail-light bar
        dh.rectangle([P(-0.18, 0.4), P(0.18, 0.28)], fill=90)                                       # plate
        A = self._down(im, ss); Lm = self._down(lt, ss) * A; Hm = self._down(hl, ss) * A
        self._over(A, _c(body), at=(ox, oy))
        sl = (slice(oy, oy + A.shape[0]), slice(ox, ox + A.shape[1]))
        self.img[sl] += Hm[..., None] * _c('#b04aa0') * 0.5
        lc = _c(light)
        self.img[sl] = self.img[sl] * (1 - Lm[..., None]) + lc * 1.6 * Lm[..., None]
        self.emi[sl] += lc * level * Lm[..., None]
        # the tail lights smeared down the glossy road
        ly = by - 0.56 * s
        wdt = 0.9 * s
        st = np.exp(-((self.XX - bx) / wdt) ** 8) * smoothstep(by + 1, by + 4, self.YY) * np.exp(-(self.YY - by) / (4.5 * s))
        st *= (_vnoise(self.YY / 2.5, self.XX / 9.0, 5) * 0.7 + 0.3)
        self.img += lc * (st * 0.55)[..., None]; self.emi += lc * (st * 0.6)[..., None]

    # ------------------------------------------------------------ lettering
    def chrome_text(self, s, x, y, size, spacing=0.02, italic=0.22, depth=18, direction=(0.3, 1.0),
                    sky=('#0e2a78', '#3f95ff', '#e9f8ff'), ground=('#3a0c30', '#ff4f96', '#ffd98a'), horizon=0.54,
                    rim='#ffe6f6', keyline='#090318', side=('#ff3fae', '#2a0636'), glow=MAGENTA, level=0.4,
                    glints=(0, 4, 8), bevel=1.0):
        """80s chrome caps centred on (x, y) (the middle of the cap height). The face mirrors a sky (deep blue
        to almost white) above a sharp horizon and a warm ground below it; a stepped extrusion `depth` px along
        `direction`, a dark keyline, a pale rim that glows, a bevel lit from the upper left, and four-point
        glints at the top-left corners of the letters listed in `glints`."""
        font, is_it = synth_font('chrome', size)
        sp = spacing * size
        adv = [font.getlength(ch) + sp for ch in s]
        tw = sum(adv) - sp
        cap = -font.getbbox('H', anchor='ls')[1]
        pad = int(depth * 1.6 + size * 0.5)
        w, h = int(tw + 2 * pad + size * 0.4), int(cap * 1.6 + 2 * pad)
        base_y = pad + cap * 1.25
        x_l = pad + size * 0.2
        im = Image.new('L', (w, h), 0); dd = ImageDraw.Draw(im)
        xs = [x_l]
        for a in adv[:-1]: xs.append(xs[-1] + a)
        for ch, xx in zip(s, xs): dd.text((xx, base_y), ch, font=font, fill=255, anchor='ls')
        sh = 0.0 if is_it else italic
        if sh:
            im = im.transform(im.size, Image.AFFINE, (1, sh, -sh * base_y, 0, 1, 0), resample=Image.BICUBIC)
        M = np.asarray(im, np.float32) / 255
        ox = int(round(x - (x_l + tw / 2))); oy = int(round(y - (base_y - cap / 2)))
        YL = np.arange(h, dtype=np.float32)[:, None] + np.zeros((1, w), np.float32)
        XL = np.arange(w, dtype=np.float32)[None, :] + np.zeros((h, 1), np.float32)
        # extrusion + keyline
        ddx, ddy = direction
        ext = M.copy()
        for k in range(1, depth + 1): ext = np.maximum(ext, shift(M, ddx * k, ddy * k))
        self._over(_dilate(ext, 3), _c(keyline), at=(ox, oy))
        s0, s1 = _c(side[0]), _c(side[1])
        for k in range(depth, 0, -1):
            lay = shift(M, ddx * k, ddy * k)
            t = k / depth
            vv = np.clip((YL - (base_y - cap)) / (cap + depth), 0, 1)[..., None]
            c = s0 * (1 - t) + s1 * t
            c = c * (1.1 - 0.5 * vv)
            self._over(lay, c, at=(ox, oy))
        # rim (glows)
        rimm = _dilate(M, 2)
        self._over(rimm, _c(rim), emit=0.0, at=(ox, oy))
        sl = (slice(max(0, oy), min(self.H, oy + h)), slice(max(0, ox), min(self.W, ox + w)))
        crop = (slice(sl[0].start - oy, sl[0].stop - oy), slice(sl[1].start - ox, sl[1].stop - ox))
        halo = np.clip(_dilate(M, 4) - M * 0.7, 0, 1)
        self.emi[sl] += (halo[crop] * level)[..., None] * _c(glow)
        # face: sky / horizon / ground reflection, then bevel light
        v = (YL - (base_y - cap)) / cap
        vs = np.clip(v / horizon, 0, 1); vg = np.clip((v - horizon) / (1 - horizon), 0, 1)
        skyc = _stops(vs, [(0, sky[0]), (0.6, sky[1]), (1, sky[2])])
        grc = _stops(vg, [(0, ground[0]), (0.45, ground[1]), (1, ground[2])])
        face = np.where((v < horizon)[..., None], skyc, grc)
        edge = np.exp(-(((v - horizon) * cap) / 1.8) ** 2)
        face = face * (1 - 0.6 * edge[..., None])
        above = np.exp(-(((horizon - v) * cap - 3.5) / 2.2) ** 2) * (v < horizon)
        face = face + (1.0 - face) * (0.7 * above)[..., None]
        hb = blur(M, max(1.5, size * 0.03))
        gy_, gx_ = np.gradient(hb)
        lit = np.clip(-(gx_ * -0.6 + gy_ * -0.8) * size * 0.09, -1, 1) * bevel
        face = face + (1.0 - face) * np.clip(lit, 0, 1)[..., None] * 0.85
        face = face * (1 - 0.45 * np.clip(-lit, 0, 1))[..., None]
        self._over(M, face, at=(ox, oy))
        # glints
        for gi in glints:
            if gi >= len(s): continue
            x_a, x_b = xs[gi], xs[gi] + (adv[gi] - sp) * 0.6
            cols = (XL >= x_a) & (XL <= x_b) & (M > 0.6)
            if not cols.any(): continue
            score = np.where(cols, YL + 0.35 * (XL - x_a), 1e9)
            j = np.unravel_index(np.argmin(score), score.shape)
            self.glint(ox + j[1] + 2, oy + j[0] + 2, size * 0.32)

    def glint(self, x, y, length, colour=WHITE, level=1.3):
        """a four-point star flare (long horizontal and vertical spikes, short diagonals)"""
        L = length
        sl = (slice(max(0, int(y - L)), min(self.H, int(y + L) + 1)), slice(max(0, int(x - L)), min(self.W, int(x + L) + 1)))
        dx = self.XX[sl] - x; dy = self.YY[sl] - y
        sp = np.exp(-np.abs(dx) / (L * 0.22)) * np.exp(-(dy / 1.1) ** 2) + np.exp(-np.abs(dy) / (L * 0.22)) * np.exp(-(dx / 1.1) ** 2)
        u = (dx + dy) / 1.414; v = (dx - dy) / 1.414
        sp += 0.35 * (np.exp(-np.abs(u) / (L * 0.08)) * np.exp(-(v / 0.9) ** 2) + np.exp(-np.abs(v) / (L * 0.08)) * np.exp(-(u / 0.9) ** 2))
        sp += 1.4 * np.exp(-(dx * dx + dy * dy) / (L * 0.05) ** 2)
        c = _c(colour)
        self.img[sl] += (sp * level)[..., None] * c; self.emi[sl] += (sp * level * 0.6)[..., None] * c

    def neon_script(self, s, x, y, size, colour=PINK, rot=8.0, anchor='mm', level=1.1, core=0.5, breaks=0, seed=None):
        """a neon tube in brush script: a coloured tube with a white-hot core; breaks=n paints n dark joints
        over the glass (as on real signs; off by default, it easily reads as a rendering fault)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        font, _ = synth_font('script', size)
        M = text_mask(self.H, self.W, s, font, (x, y), anchor=anchor, rot=rot)
        ys, xs = np.nonzero(M > 0.5)
        for _ in range(breaks if len(xs) else 0):
            i = int(r.integers(0, len(xs)))
            gx, gy = xs[i], ys[i]
            cut = np.exp(-(((self.XX - gx) * np.cos(0.4) + (self.YY - gy) * np.sin(0.4)) / 1.4) ** 2) * (np.hypot(self.XX - gx, self.YY - gy) < size * 0.12)
            M = M * (1 - 0.85 * cut)
        cm = smoothstep(0.75, 0.98, blur(M, max(1.0, size * 0.014))) * M
        c = _c(colour)
        tube = c * 1.25 + (1 - c) * 0.1
        col = tube[None, None] * (1 - core * cm[..., None]) + _c(WHITE) * 1.3 * (core * cm[..., None])
        self._over(M, col, emit=level)

    def caption(self, s, x, y, size, colour=CYAN, spacing=0.35, anchor='mm', rules=(90, 22), level=0.45, font='caption'):
        """a letter-spaced line of small type with thin rules on both sides"""
        f, _ = synth_font(font, size) if font in _FONTS else (load_font(font, size), False)
        sp = spacing * size
        M = text_mask(self.H, self.W, s, f, (x, y), anchor=anchor, spacing=sp)
        c = _c(colour)
        if rules:
            tw = sum(f.getlength(ch) + sp for ch in s) - sp
            x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
            L, g = rules
            yr = y + (size * 0.05 if anchor[1] == 'm' else 0)
            for a, b in ((x0 - g - L, x0 - g), (x0 + tw + g, x0 + tw + g + L)):
                M = np.maximum(M, np.clip(1.1 - np.abs(self.YY - yr), 0, 1) * np.clip(np.minimum(self.XX - a, b - self.XX) + 0.5, 0, 1)
                               * smoothstep(0, L * 0.6, np.where(a < x0, self.XX - a, b - self.XX)))
        self._over(M, c * 1.2, emit=level)

    def osd(self, s, x, y, px=6, colour=WHITE, anchor='la'):
        """VCR on-screen display text in a 5x7 block font (drawn onto the finished frame, over the tape noise)"""
        self.osd_items.append((s, x, y, px, colour, anchor))

    def _osd_mask(self, s, x, y, px, anchor):
        w = len(s) * 6 * px - px; h = 7 * px
        x0 = x - w * {'l': 0, 'm': 0.5, 'r': 1}[anchor[0]]; y0 = y - h * {'a': 0, 'm': 0.5, 'b': 1}.get(anchor[1], 0)
        m = np.zeros((self.H, self.W), np.float32)
        for k, ch in enumerate(s.upper()):
            g = _OSD.get(ch, _OSD[' ']).split('|')
            for j, row in enumerate(g):
                for i, c in enumerate(row):
                    if c != '#': continue
                    xa = int(round(x0 + (k * 6 + i) * px)); ya = int(round(y0 + j * px))
                    m[max(0, ya):max(0, ya + px), max(0, xa):max(0, xa + px)] = 1
        return m

    # ------------------------------------------------------------ tape and output
    def vhs(self, bleed=3.5, shift_px=3.0, ghost=0.06, jitter=0.35, noise=0.014, scan=0.1, pitch=3.0,
            tracking=(0.83, 12, 5.0), head=12, dropouts=14, seed=None):
        """play the finished frame back off tape: chroma bleed and shift, ghost and ringing, line jitter, one
        tracking band (y as a fraction of H, height px, shift px), head-switching noise, noise, dropouts, OSD,
        scanlines. Only the finished frame gets this; stage snapshots stay clean."""
        self.vhs_opts = dict(bleed=bleed, shift_px=shift_px, ghost=ghost, jitter=jitter, noise=noise, scan=scan, pitch=pitch,
                             tracking=tracking, head=head, dropouts=dropouts, seed=self._seed() if seed is None else seed)

    def _tape(self, out):
        o = self.vhs_opts; H, W = self.H, self.W
        r = np.random.default_rng(o['seed'])
        Y = out @ np.array([0.299, 0.587, 0.114], np.float32)
        I = out @ np.array([0.596, -0.274, -0.322], np.float32)
        Q = out @ np.array([0.211, -0.523, 0.312], np.float32)
        Yb = _blur_axis(Y, 0.8, 1)
        Yb = Yb * (1 - o['ghost']) + shift(Yb, 9, 0) * o['ghost']
        Yb = Yb + 0.35 * (Yb - _blur_axis(Yb, 2.2, 1))                       # playback sharpening rings at edges
        I = shift(_blur_axis(_blur_axis(I, o['bleed'], 1), 0.8, 0), o['shift_px'], 0)
        Q = shift(_blur_axis(_blur_axis(Q, o['bleed'] * 1.3, 1), 0.8, 0), o['shift_px'] * 1.4, 0)
        rows = np.arange(H, dtype=np.float32)
        off = (_vnoise(rows / 3.0, np.zeros(H), o['seed']) - 0.5) * 2 * o['jitter']
        ty, th, tsh = o['tracking']; ty = ty * H
        tb = np.exp(-((rows - ty) / th) ** 2)
        off += tb * tsh * (0.6 + 0.8 * _vnoise(rows / 1.5, np.ones(H), o['seed'] + 1))
        hb = rows >= H - o['head']
        off += hb * (8 + 14 * (_vnoise(rows / 2.0, np.full(H, 2.0), o['seed'] + 2)))
        xs = self.XX - off[:, None]
        Yb, I, Q = _sample(Yb, xs, self.YY), _sample(I, xs, self.YY), _sample(Q, xs, self.YY)
        n = _blur_axis(r.normal(0, 1, (H, W)).astype(np.float32), 2.5, 1); n /= n.std() + 1e-6
        Yb = Yb + n * o['noise'] * (0.5 + 0.8 * np.sqrt(np.clip(Yb, 0, 1)))
        spk = (r.random((H, W)) < 0.02).astype(np.float32)
        spk = _blur_axis(spk, 3.0, 1) * 4
        Yb = Yb + spk * (tb[:, None] * 0.35 + hb[:, None] * 0.5)
        Yb[hb] *= 0.8
        for _ in range(o['dropouts']):                                       # oxide dropouts: short white streaks
            yy = int(r.integers(0, H)); xx = int(r.integers(0, W)); L = int(r.integers(12, 70))
            Yb[yy, xx:xx + L] += np.linspace(0.6, 0.0, len(Yb[yy, xx:xx + L])) * r.uniform(0.3, 0.8)
        out = np.stack([Yb + 0.956 * I + 0.621 * Q, Yb - 0.272 * I - 0.647 * Q, Yb - 1.106 * I + 1.703 * Q], -1)
        # OSD: drawn by the deck, crisp-ish, with a dark edge
        for (s, x, y, px, colour, anchor) in self.osd_items:
            m = self._osd_mask(s, x, y, px, anchor)
            sh = np.clip(shift(m, px * 0.5, px * 0.5) + _gblur(m, px * 0.5) * 0.6, 0, 1)
            m = blur(m, 0.6)
            out = out * (1 - 0.75 * sh[..., None])
            out = out * (1 - m[..., None]) + _c(colour) * 0.95 * m[..., None]
        # CRT scanlines, lifted blacks
        out = out * (1 - o['scan'] * (0.5 + 0.5 * np.cos(2 * np.pi * self.YY / o['pitch'])))[..., None]
        out = 0.03 + out * 0.96
        return out

    def _tone(self, x):
        over = np.clip(x - 1.0, 0, None).sum(-1, keepdims=True)
        x = x + over * 0.28                                                   # over-driven channels spill: cores go white
        k = 0.8
        return np.clip(np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k)))), 0, 1)

    def render(self, final=True):
        e = self.emi
        bloom = _gblur(e, 3) * 0.5 + _gblur(e, 10) * 0.42 + _gblur(e, 32) * 0.34 + _gblur(e, 100) * 0.28
        out = self._tone(self.img + bloom)
        rr = np.hypot((self.XX - self.W / 2) / (self.W / 2), (self.YY - self.H / 2) / (self.H / 2)) / np.sqrt(2)
        out = out * (1 - 0.3 * rr ** 2.4)[..., None]
        if final and self.vhs_opts: out = self._tape(out)
        return np.clip(out, 0, 1)

    def composite(self, final=True):
        return Image.fromarray((self.render(final) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        if self.record: self.stages.append((name, self.composite(final=False)))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite(final=True)
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
