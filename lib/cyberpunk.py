"""cyberpunk — a rain-soaked neon street canyon at night, lit like a film still (numpy + Pillow only).

Model: one physically-lit HDR scene seen through one camera, then finished like a frame of film.
  camera     a level pinhole camera `eye` metres above the street, looking straight down it (X right, Y up,
             Z into the scene). A point lands at (vx + f*X/Z, vy + f*(eye - Y)/Z): verticals stay vertical,
             every line along the street runs to the vanishing point, sizes fall off as 1/Z.
  buffers    painting fills screen-space buffers — albedo (surface colour), emission (light given off, HDR:
             a neon core is 5-10x paper white), depth in metres (a z-buffer, so draw order does not matter
             for solid things, and fog), and a mirror row (the screen row where that object's foot meets
             the ground, for reflections). Things made only of light (hologram, light trails, tube halos)
             go to an additive buffer, already faded by the fog in front of them.
  light      every surface is lit by a dim blue ambient plus the *spill* of the light sources near it on
             screen (emission blurred at three radii): a wall glows magenta beside a magenta sign, a sign's
             dark backing picks up its own colour. No light is painted by hand.
  buildings  perspective boxes: the street-side facade is an X = const plane, the front face a Z = const
             plane. Each is painted as a texture in metres — concrete with rain streaks, floor slabs, a
             window grid (lit / dark / blinds / TV-blue), air-conditioner boxes, a ground floor of lit
             shopfronts and roller shutters with light leaking underneath — and warped onto the screen by
             the exact inverse camera map, pre-filtered along the foreshortened axis so far windows melt
             into a glow instead of shimmering.
  neon       real glass tubes. A hairline skeleton (a W0 font glyph or a path) is widened into a tube of
             radius r; brightness follows the chord length through the glowing gas (hot centre line, dark
             rim), the core over-exposes toward white the way film does, a short coloured halo hugs the
             glass. A tube can `flicker` (caught mid-dip: dim and patchy along its length) or be `dead`
             (pale unlit glass with one specular line). Blade signs stick out over the street and face the
             camera: steel brackets, a box with depth, a dark backing, a border tube, letters. Lightboxes
             are backlit acrylic with the fluorescent tubes showing through as soft bands.
  hologram   a translucent projected panel, light only: the motif (a drifting jellyfish) and lettering in
             cyan with magenta fringes, scanlines at a fixed pitch on the panel, a slow brightness band,
             a few slices torn sideways, a dust of sparkle, soft edges. It lights the fog and the walls.
  street     wet asphalt evaluated per pixel in ground coordinates (aggregate, paint, puddles all
             foreshorten correctly and fade out below a pixel): kerbs, paving joints, worn lane paint, a
             zebra crossing, grates.
  reflection every upright thing is mirrored in the ground about its *own* contact row (a far wall about its
             far base, a hanging sign about the ground under it); pixels are splatted and the nearest
             object wins, so a figure's reflection covers the wall's. The mirror image is torn by ripples,
             kept sharp only in puddles, smeared into long vertical streaks on damp asphalt (the brightest
             lights smear farthest), and Fresnel makes the far street a better mirror than the near one.
  atmosphere depth fog whose colour is the city's light scattered in it (the end of the street glows);
             steam from grates (domain-warped noise, widening, bent by wind, lit by what is around it);
             rain in three depths (fine far rain, mid streaks, a few big defocused near streaks), each
             streak lit by the light around it, so rain only shows where it falls past neon; splash rings.
  lens/film  bloom at four radii, red film halation around hot lights, ACES filmic tone curve, cool shadows /
             warm highlights, radial chromatic aberration growing toward the corners, mid-tone film grain,
             one thin torn scanline band, vignette.

    from cyberpunk import Cyberpunk, MAGENTA, CYAN, AMBER
    c = Cyberpunk(1920, 1080, seed=7)
    c.sky(); c.street()
    c.building(-1, 12, 40, 45); c.building(+1, 12, 36, 60)
    c.blade_sign(-1, 20, 3.5, 9.5, '拉麺', AMBER, dead=[1])
    c.hologram(80, -6, 8, 10, 30, '海月', 'SEA MOON')
    c.steam(2.0, 16); c.rain()
    c.save('out.png')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font

MAGENTA, CYAN, AMBER = '#ff2a8c', '#2ed8ff', '#ffa93a'
RED, WHITE = '#ff3b3b', '#fff4e8'
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _lin(c):
    """'#rrggbb' or an RGB triple (display values) -> linear light"""
    c = hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)
    return c ** 2.2


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
    """gaussian (three box passes) along one axis only — for streaks and anisotropic texture filtering"""
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
    """bilinear sample of an (H, W) or (H, W, C) array at float pixel coordinates (clamped to the edge)"""
    H, W = img.shape[:2]
    x = np.clip(x, 0, W - 1.001); y = np.clip(y, 0, H - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32)
    fx = (x - x0).astype(np.float32); fy = (y - y0).astype(np.float32)
    if img.ndim == 3: fx = fx[..., None]; fy = fy[..., None]
    return ((img[y0, x0] * (1 - fx) + img[y0, x0 + 1] * fx) * (1 - fy)
            + (img[y0 + 1, x0] * (1 - fx) + img[y0 + 1, x0 + 1] * fx) * fy)


def _vnoise(x, y, seed=0):
    """smooth value noise at arbitrary float coordinates (lattice spacing 1), in [0, 1]"""
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


def _fbm(x, y, octaves=4, seed=0, foot=None):
    """fractal value noise in [0, 1]; `foot` (lattice cells per pixel) fades octaves finer than a pixel"""
    out = 0.0; amp = 1.0; tot = 0.0; fr = 1.0
    for o in range(octaves):
        n = _vnoise(x * fr, y * fr, seed + o * 7919)
        if foot is not None:
            n = 0.5 + (n - 0.5) * np.clip(1.4 - foot * fr, 0, 1)
        out = out + amp * n; tot += amp; amp *= 0.5; fr *= 2.0
    return (out / tot).astype(np.float32)


def _aces(x):
    return np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0, 1)


# ---------------------------------------------------------------- sign fonts (never committed to the repo)
_FONTS = {
    'neon': [('/System/Library/Fonts/ヒラギノ角ゴシック W0.ttc', 0), ('/System/Library/Fonts/ヒラギノ角ゴシック W1.ttc', 0),
             ('/usr/share/fonts/**/NotoSansCJK*Thin*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSansCJK*Light*.tt[cf]', 0),
             ('C:/Windows/Fonts/msyhl.ttc', 0), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
             ('/usr/share/fonts/**/NotoSansCJK*.tt[cf]', 0), ('C:/Windows/Fonts/msyh.ttc', 0)],
    'bold': [('/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', 0), ('/System/Library/Fonts/STHeiti Medium.ttc', 0),
             ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0)],
    'mincho': [('/System/Library/Fonts/ヒラギノ明朝 ProN.ttc', 0), ('/System/Library/Fonts/Supplemental/Songti.ttc', 0),
               ('/usr/share/fonts/**/NotoSerifCJK*.tt[cf]', 0), ('C:/Windows/Fonts/simsun.ttc', 0)],
    'thin': [('/System/Library/Fonts/HelveticaNeue.ttc', 12), ('/System/Library/Fonts/Avenir Next.ttc', 10),
             ('/usr/share/fonts/**/DejaVuSans-ExtraLight.ttf', 0), ('C:/Windows/Fonts/segoeuil.ttf', 0)],
    'light': [('/System/Library/Fonts/HelveticaNeue.ttc', 7), ('/System/Library/Fonts/Avenir Next.ttc', 7),
              ('/usr/share/fonts/**/DejaVuSans.ttf', 0), ('C:/Windows/Fonts/segoeuil.ttf', 0)],
}
_FCACHE = {}


def sign_font(kind, size):
    """PIL font for signs. kind: neon (hairline CJK+Latin, the tube skeleton), bold, mincho, thin / light (Latin).
    Override with $INKPAINT_FONT_NEON / _BOLD / _MINCHO / _THIN / _LIGHT."""
    key = (kind, int(size))
    if key in _FCACHE: return _FCACHE[key]
    env = os.environ.get('INKPAINT_FONT_' + kind.upper())
    font = None
    for pat, idx in ([(env, 0)] if env else []) + _FONTS.get(kind, []):
        for p in glob.glob(pat, recursive=True):
            try:
                font = ImageFont.truetype(p, max(4, int(size)), index=idx); break
            except OSError:
                pass
        if font: break
    if font is None: font = load_font('cjk_sans', size)
    _FCACHE[key] = font
    return font


def _glyph(ch, size, kind='neon'):
    """one character as a float mask centred in a square of side ~1.5*size"""
    f = sign_font(kind, size)
    n = int(size * 1.5) + 4
    im = Image.new('L', (n, n), 0)
    ImageDraw.Draw(im).text((n / 2, n / 2), ch, font=f, fill=255, anchor='mm')
    return np.asarray(im, np.float32) / 255


class Cyberpunk:
    def __init__(self, W=1920, H=1080, seed=0, focal=1150.0, vp=None, eye=1.7, fog=150.0, wall=9.5, road=6.0,
                 ambient='#3a4266', fog_colour='#1c2140', record=True):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.f = float(focal)
        self.vx, self.vy = (W * 0.5, H * 0.52) if vp is None else (float(vp[0]), float(vp[1]))
        self.eye, self.fog_m, self.wall, self.road = float(eye), float(fog), float(wall), float(road)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        z3 = lambda: np.zeros((H, W, 3), np.float32)
        self.alb, self.emi, self.add, self.lsrc = z3(), z3(), z3(), z3()
        self.dep = np.full((H, W), np.inf, np.float32)
        self.base = np.full((H, W), -1.0, np.float32)
        self.ground = np.zeros((H, W), np.float32)
        self.pools = np.zeros((H, W), np.float32)
        self.damp = np.zeros((H, W), np.float32)
        self.steam_d = np.zeros((H, W), np.float32)
        self.amb = _lin(ambient) * 0.3
        self.fogc = _lin(fog_colour)
        self.sky_t = 0.5                    # how much of the painted sky survives the haze
        self.fog_floor = 0.1                # far haze saturates: distant towers keep a trace of themselves
        self.spill_k, self.scatter_k = 0.55, 0.6
        self.exposure = 1.1
        self.rain_layers, self.rings = [], None
        self.glitch_bands = []
        self.street_on = False
        self.record = record
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ camera
    def project(self, X, Y, Z):
        """world metres -> screen pixels"""
        Z = np.maximum(Z, 1e-3)
        return self.vx + self.f * np.asarray(X) / Z, self.vy + self.f * (self.eye - np.asarray(Y)) / Z

    def ground_row(self, Z):
        """screen row where the ground at depth Z is seen (the mirror line of anything standing there)"""
        return self.vy + self.f * self.eye / np.maximum(Z, 1e-3)

    def fog_t(self, Z):
        """fraction of light that survives the haze over Z metres"""
        return float(np.exp(-Z / self.fog_m))

    def near_z(self, side, wall=None):
        """nearest depth of a facade at |X| = wall that is still on screen"""
        wall = self.wall if wall is None else wall
        edge = self.vx if side < 0 else self.W - self.vx
        return self.f * wall / edge

    # ------------------------------------------------------------ low-level compositing
    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1)) + 1), min(self.H, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _put(self, sl, a, alb=0.0, emi=0.0, depth=1.0, base=None, ztest=True):
        """paint an opaque surface: coverage `a` (cropped to sl), colours as linear RGB (3,) or (h, w, 3),
        depth scalar or (h, w). Z-tested, so nearer things always win whatever the order of the calls."""
        a = np.clip(a, 0, 1).astype(np.float32)
        D = self.dep[sl]
        if ztest: a = a * (depth < D)
        a3 = a[..., None]
        alb = np.asarray(alb, np.float32); emi = np.asarray(emi, np.float32)
        self.alb[sl] = self.alb[sl] * (1 - a3) + alb * a3
        self.emi[sl] = self.emi[sl] * (1 - a3) + emi * a3
        self.add[sl] *= 1 - a3
        hard = a > 0.5
        D[hard] = depth[hard] if np.ndim(depth) else depth
        if base is not None:
            B = self.base[sl]; B[hard] = base[hard] if np.ndim(base) else base
        G = self.ground[sl]; G *= 1 - a
        return a

    def _glow(self, sl, rgb, depth, light=0.0):
        """additive light in the air (halo, hologram, trail): faded by its own fog, hidden behind nearer solids"""
        vis = (depth < self.dep[sl]).astype(np.float32)[..., None]
        T = np.exp(-np.asarray(depth, np.float32) / self.fog_m)
        T = T[..., None] if np.ndim(T) else T
        self.add[sl] += rgb * vis * T
        if light: self.lsrc[sl] += rgb * vis * light

    def _poly(self, pts, ss=2):
        """antialiased polygon -> (slice, mask) cropped to its bounding box"""
        P = np.asarray(pts, np.float32)
        sl = self._box(P[:, 0].min() - 1, P[:, 1].min() - 1, P[:, 0].max() + 1, P[:, 1].max() + 1)
        if sl is None: return None, None
        y0, x0 = sl[0].start, sl[1].start
        h, w = sl[0].stop - y0, sl[1].stop - x0
        im = Image.new('L', (w * ss, h * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P], fill=255)
        return sl, np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255

    def _lines(self, sl, segs, ss=2):
        """antialiased strokes in a box: segs = [(points, width_px, value)], returns (coverage, value-weighted)"""
        y0, x0 = sl[0].start, sl[1].start
        h, w = sl[0].stop - y0, sl[1].stop - x0
        cov = Image.new('F', (w * ss, h * ss), 0.0); val = Image.new('F', (w * ss, h * ss), 0.0)
        dc, dv = ImageDraw.Draw(cov), ImageDraw.Draw(val)
        for pts, width, v in segs:
            q = [((x - x0) * ss, (y - y0) * ss) for x, y in pts]
            wd = max(1, int(round(width * ss)))
            dc.line(q, fill=1.0, width=wd, joint='curve'); dv.line(q, fill=float(v), width=wd, joint='curve')
        c = np.asarray(cov.resize((w, h), Image.BOX)); v = np.asarray(val.resize((w, h), Image.BOX))
        return np.clip(c, 0, 1), v

    # ------------------------------------------------------------ sky and the far city
    def sky(self, zenith='#04050c', mid='#0d0f26', horizon='#462660', glow='#ff4d8f', clouds=1.0, seed=None):
        """night sky over the city: near-black zenith, a low smog deck lit from underneath by the streets
        (magenta-amber near the horizon, fading upward), all of it emission (the sky has no albedo)"""
        seed = self._seed() if seed is None else seed
        H, W = self.H, self.W
        t = np.clip(self.YY / max(1.0, self.vy), 0, 1.2)[..., None]
        z, m, h = _lin(zenith), _lin(mid), _lin(horizon)
        col = np.where(t < 0.55, z + (m - z) * (t / 0.55), m + (h - m) * np.clip((t - 0.55) / 0.45, 0, 1) ** 1.6)
        n = np.asarray(Image.fromarray(noise2d(H // 3, W // 9, 18, 5, seed)).resize((W, H), Image.BICUBIC))
        n2 = np.asarray(Image.fromarray(noise2d(H // 2, W // 4, 14, 4, seed + 1)).resize((W, H), Image.BICUBIC))
        billow = smoothstep(0.38, 0.78, 0.65 * n + 0.35 * n2)
        under = np.clip(t[..., 0], 0, 1) ** 2.2
        col = col * (0.55 + 0.9 * billow[..., None])
        col = col + _lin(glow) * (billow * under * 0.16 * clouds)[..., None] + _lin(AMBER) * (billow ** 3 * under * 0.03 * clouds)[..., None]
        below = np.clip((self.YY - self.vy) / (H - self.vy + 1), 0, 1)[..., None]  # under the horizon: unlit haze
        col = np.where(below > 0, h * 0.35 * (1 - below) ** 3 + z * 0.4, col)
        self.alb[:] = 0; self.emi[:] = col.astype(np.float32)
        self.dep[:] = np.inf; self.base[:] = self.vy

    def skyline(self, z=420.0, x_range=(-420, 420), heights=(60, 300), widths=(18, 60), colour='#12152a',
                lights=0.5, beacons=0.5, seed=None):
        """a row of far towers at depth z: flat silhouettes with setback tops, pin-prick windows, red beacons"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        X = x_range[0]
        while X < x_range[1]:
            w = r.uniform(*widths); h = r.uniform(*heights) * (1.2 - 0.5 * min(1, abs(X) / max(abs(x_range[0]), 1)))
            if r.random() < 0.6:                                              # a setback crown
                i = w * r.uniform(0.12, 0.3)
                pts = [(X, 0), (X + w, 0), (X + w, h * 0.72), (X + w - i, h * 0.72), (X + w - i, h), (X + i, h), (X + i, h * 0.72), (X, h * 0.72)]
            else:
                pts = [(X, 0), (X + w, 0), (X + w, h), (X, h)]
            scr = [self.project(px, py, z) for px, py in pts]
            sl, m = self._poly(scr)
            if sl is not None:
                yy = self.YY[sl]
                shade = _lin(colour) * (0.8 + 0.4 * r.random())
                em = np.zeros(m.shape + (3,), np.float32)
                if lights:
                    dots = (r.random(m.shape) < 0.012 * lights) & (((yy.astype(int)) % 3) == 0)
                    tint = np.where(r.random(m.shape)[..., None] < 0.7, _lin('#ffc27a'), _lin('#9fd8ff'))
                    em = dots[..., None] * tint * r.uniform(0.3, 1.2, m.shape)[..., None]
                self._put(sl, m, shade, em, z, self.ground_row(z))
                if r.random() < beacons:
                    bx, by = self.project(X + w / 2, h + 2, z)
                    self.light(bx, by, 1.2, RED, z, 3.0)
            X += w + r.uniform(-4, 14)

    def light(self, x, y, r, colour, z, level=2.0, halo=4.0):
        """a small point light (beacon, lamp): a hot dot plus a soft halo in the air"""
        sl = self._box(x - r * halo * 3, y - r * halo * 3, x + r * halo * 3, y + r * halo * 3)
        if sl is None: return
        d = np.hypot(self.XX[sl] - x, self.YY[sl] - y)
        core = np.clip(1.2 - d / max(r, 0.6), 0, 1)
        col = _lin(colour)
        self._put(sl, core, 0.0, col * level * 2.5, z, self.ground_row(z))
        self._glow(sl, col * (np.exp(-(d / (r * halo)) ** 2) * level * 0.6)[..., None], z, 0.5)

    # ------------------------------------------------------------ buildings
    def _facade(self, wm, hm, ppu, ppv, colour, floor, bay, lit, shop, seed, signs=True, flip=False, mix=(0.45, 0.35, 0.2, 0.0)):
        """paint one wall as a texture in metres: returns albedo, emission (th, tw, 3); row 0 is the top (Y = hm)"""
        r = np.random.default_rng(seed)
        tw, th = max(4, int(np.ceil(wm * ppu))), max(4, int(np.ceil(hm * ppv)))
        u = (np.arange(tw, dtype=np.float32) + 0.5) / ppu
        v = hm - (np.arange(th, dtype=np.float32) + 0.5) / ppv
        U, V = np.meshgrid(u, v)
        n1 = _fbm(U / 3.0, V / 3.0, 3, seed)
        streak = _fbm(U / 0.35, V / 6.0, 3, seed + 1)
        shade = (0.7 + 0.55 * n1) * (0.72 + 0.5 * streak)
        alb = (_lin(colour)[None, None, :] * shade[..., None]).astype(np.float32)
        emi = np.zeros_like(alb)
        gf = 4.4 if shop else 0.0
        fv = V - gf
        k = np.floor(fv / floor).astype(np.int32); vv = fv - k * floor
        j = np.floor(U / bay).astype(np.int32); uu = U - j * bay
        up = (fv > 0) & (V < hm - 0.6)
        alb[up & (vv < 0.3)] *= 0.55                                          # floor slab
        alb[up & (vv >= 0.3) & (vv < 0.38)] *= 1.5                            # its lit lip
        nk, nj = int(hm / floor) + 3, int(wm / bay) + 3
        kk, jj = np.clip(k, 0, nk - 1), np.clip(j, 0, nj - 1)
        t_lit = r.random((nk, nj)) < lit
        pal = np.array([_lin(c) for c in ('#ffb46e', '#ffe0b8', '#d6e8ff', '#7fa6ff', '#ff9ccc', '#9ff0e2')], np.float32)
        t_col = r.choice(len(pal), (nk, nj), p=[0.5, 0.2, 0.17, 0.08, 0.03, 0.02])
        t_int = r.uniform(0.15, 1.0, (nk, nj)) ** 2.0 * 0.75
        t_bl = r.random((nk, nj)) < 0.4
        t_ac = r.random((nk, nj)) < 0.35
        t_acx = r.uniform(0.15, max(0.2, bay - 1.0), (nk, nj))
        win = up & (uu > 0.32) & (uu < bay - 0.32) & (vv > 0.95) & (vv < floor - 0.42)
        alb[win] = _lin('#0d1119') * (0.8 + 0.4 * n1[win])[..., None]
        Lw = win & t_lit[kk, jj]
        grad = 0.55 + 0.6 * np.clip((vv - 0.95) / (floor - 1.37), 0, 1)
        blind = np.where(t_bl[kk, jj], 0.35 + 0.65 * (np.sin(vv * 2 * np.pi / 0.09) > -0.1), 1.0)
        t_cur = r.uniform(-0.2, 1.0, (nk, nj))                                # a half-drawn curtain
        cur = np.where((uu - 0.32) / (bay - 0.64) < t_cur[kk, jj], 0.18, 1.0)
        e = pal[t_col[kk, jj]] * (t_int[kk, jj] * grad * blind * cur)[..., None]
        emi[Lw] = e[Lw]
        mull = win & (np.abs(uu - bay / 2) < 0.045)
        alb[mull] = _lin('#1a1d24'); emi[mull] = 0
        ac = up & t_ac[kk, jj] & (uu > t_acx[kk, jj]) & (uu < t_acx[kk, jj] + 0.85) & (vv > 0.36) & (vv < 0.88)
        grille = 0.75 + 0.25 * (np.sin((uu - t_acx[kk, jj]) * 2 * np.pi / 0.07) > 0)
        alb[ac] = (_lin('#6b7078') * 0.55 * grille[..., None])[ac]; emi[ac] = 0
        drip = up & t_ac[kk, jj] & (np.abs(uu - t_acx[kk, jj] - 0.42) < 0.05) & (vv < 0.36)
        alb[drip] *= 0.6
        if shop:
            sw = r.uniform(4.5, 7.0)
            si = np.floor(U / sw).astype(np.int32); su = U - si * sw
            ns = int(wm / sw) + 2
            ci = np.clip(si, 0, ns - 1)
            mix = np.asarray(mix, np.float64); kind = r.choice(4, ns, p=mix / mix.sum())[ci]   # lit shop, shutter, dark, vending
            spal = np.array([_lin(c) for c in ('#ffc98c', '#cfe6ff', '#ffab5c', '#b8ffd8', '#ffb8d8')], np.float32)
            inner = spal[r.choice(5, ns, p=[0.35, 0.25, 0.2, 0.1, 0.1])][ci] * r.uniform(0.2, 0.45, ns)[ci][..., None]
            g = V < gf
            glass = g & (V > 0.45) & (V < 3.0) & (su > 0.3) & (su < sw - 0.3)
            lit_s = glass & (kind == 0)
            ceil = 0.12 + 0.88 * np.clip((V - 0.45) / 2.3, 0, 1) ** 2.2            # lit from the ceiling down
            fix = (V > 2.78) & (V < 2.84) & (((su - 0.3) % 1.1) < 0.7)             # the tube fittings themselves
            shelf = (((su - 0.3 + 0.3 * _vnoise(si * 7.0, V * 0.0, seed)) % 0.9) < 0.08) & (V < 2.2)   # shelf ends, edge-on
            clutter = smoothstep(0.5, 0.75, _fbm(U / 0.3, V / 0.35, 3, seed + 7)) * (V < 1.9)
            counter = (V > 0.45) & (V < 1.05) & (_vnoise(U / 1.3, si * 3.0, seed + 5) > 0.55)
            pu = r.uniform(0.8, max(1.0, sw - 0.8), ns)[ci]; ph = r.random(ns)[ci] < 0.5
            person = ph & (np.hypot((su - pu) / 0.22, (V - 1.2) / 0.62) < 1) | ph & (np.hypot((su - pu) / 0.12, (V - 1.95) / 0.14) < 1)
            mull = (np.abs(((su - 0.3) % 1.7) - 0.85) > 0.8)
            side = np.clip(np.minimum(su - 0.3, sw - 0.3 - su) / 1.2, 0.3, 1.0)
            e_in = inner * (ceil * side * np.where(shelf, 0.45, 1.0) * np.where(counter, 0.35, 1.0) * (1 - 0.6 * clutter))[..., None]
            e_in = np.where(fix[..., None], inner * 2.2, e_in)
            e_in = np.where((person | mull)[..., None], e_in * 0.08, e_in)
            emi[lit_s] = e_in[lit_s]; alb[lit_s] = 0.015
            shut = glass & (kind == 1)
            rib = 0.65 + 0.35 * (np.sin(V * 2 * np.pi / 0.085) > 0)
            alb[shut] = (_lin('#5a6068') * 0.4 * rib[..., None])[shut]; emi[shut] = 0
            gap = r.random(ns)[ci] < 0.4
            leak = shut & gap & (V < 0.62)                                        # light leaking under a half-shut shutter
            emi[leak] = (spal[0] * 0.22 * np.clip((0.62 - V) / 0.17, 0, 1)[..., None])[leak]
            dark = glass & (kind == 2)
            alb[dark] = 0.01; emi[dark] = 0
            vend = g & (kind == 3)                                                 # vending machines against a shutter
            alb[vend & (V < 3.0)] = (_lin('#5a6068') * 0.4 * rib[..., None])[vend & (V < 3.0)]; emi[vend] = 0
            mu = su - 0.6; mi = np.floor(mu / 1.0); mx = mu - mi
            box = vend & (mi >= 0) & (mi < 3) & (mx > 0.04) & (mx < 0.96) & (V < 1.85)
            face = box & (mx > 0.1) & (mx < 0.9) & (V > 0.95) & (V < 1.75)
            row = np.floor((V - 1.0) / 0.25); rx = (mx - 0.1) / 0.8 * 6
            can = face & ((rx % 1) > 0.2) & ((rx % 1) < 0.8) & (((V - 1.0) % 0.25) > 0.07) & (((V - 1.0) % 0.25) < 0.19)
            ccol = np.array([_lin(c) for c in ('#ff4b5c', '#38c6ff', '#ffd23f', '#7dff9a', '#ffffff')], np.float32)
            cidx = (np.abs(np.sin(np.floor(rx) * 7.1 + row * 3.7 + mi * 1.3)) * 5).astype(int) % 5
            emi[box] = _lin('#1b2230') * 0.3
            emi[face] = _lin('#eaf4ff') * 0.75
            emi[can] = (ccol[cidx] * 0.9)[can]
            emi[box & (V > 1.76) & (V < 1.83)] = _lin(CYAN) * 0.6
            alb[box] = 0.05
            alb[g & ~glass & (V < 3.2)] *= 0.55
            if signs:                                                             # a fascia sign over each shop
                words = ['薬局', '食堂', '理髪', '酒場', '珈琲', '精肉', '鮮魚', '古書', '時計', '骨董', '写真', '洋服',
                         '餃子', '茶房', '花屋', '雑貨', 'DELI', 'REPAIR', 'PHOTO', 'LAUNDRY', 'NOODLE', 'PARTS', '24H']
                fcs = [MAGENTA, CYAN, AMBER, '#f4efe6', '#f4efe6']
                for i in range(ns):
                    if r.random() > 0.75: continue
                    u0, u1 = i * sw + 0.5, (i + 1) * sw - 0.5
                    c0, c1 = int(u0 * ppu), min(tw, int(u1 * ppu))
                    r0, r1 = int((hm - 4.05) * ppv), int((hm - 3.35) * ppv)
                    if c1 - c0 < 3 or r1 - r0 < 2 or c0 >= tw: continue
                    fc = _lin(fcs[r.integers(len(fcs))]) * r.uniform(0.3, 0.55)
                    ink = r.random() < 0.6                                    # dark letters on a lit face, or lit letters on dark
                    wd = words[r.integers(len(words))]
                    ht = 64; wt = max(8, int(ht * (u1 - u0) / 0.7))
                    im = Image.new('L', (wt, ht), 0)
                    fnt = sign_font('bold', ht * 0.66)
                    ImageDraw.Draw(im).text((wt * 0.5, ht * 0.52), wd, font=fnt, fill=255, anchor='mm')
                    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
                    m = np.asarray(im.resize((c1 - c0, r1 - r0), Image.BOX), np.float32) / 255
                    if ink: e = fc[None, None] * (1 - 0.9 * m)[..., None]
                    else: e = fc[None, None] * (0.06 + 1.6 * m)[..., None]
                    emi[r0:r1, c0:c1] = e; alb[r0:r1, c0:c1] = 0.04
        return alb, emi

    def _levels(self, tex, lo, hi):
        """anisotropic pre-filtering: level k blurs along u by 0.5*2^k texels (v gets the square root of that)"""
        out = {}
        for k in range(lo, hi + 1):
            if k == 0: out[k] = tex
            else: out[k] = _blur_axis(_blur_axis(tex, 0.5 * 2 ** k, 1), 0.5 * 2 ** (k / 2), 0)
        return out

    def _draw_side(self, side, wall, z0, z1, Y0, Y1, alb_t, emi_t, ppu, ppv, u0):
        """warp a facade texture (u = Z metres from u0, v from the top Y1) onto the plane X = side*wall"""
        Xp = side * wall
        xa, _ = self.project(Xp, 0, z0); xb, _ = self.project(Xp, 0, z1)
        ya = min(self.project(0, Y1, z0)[1], self.project(0, Y1, z1)[1])
        yb = max(self.project(0, Y0, z0)[1], self.project(0, Y0, z1)[1])
        sl = self._box(min(xa, xb) - 1, ya - 1, max(xa, xb) + 1, yb + 1)
        if sl is None: return
        X = self.XX[sl]; Y = self.YY[sl]
        dx = X - self.vx
        Z = np.where(dx * side > 0.5, self.f * Xp / np.where(np.abs(dx) < 0.5, 0.5, dx), 1e9)
        ax = np.clip(np.minimum(X - min(xa, xb), max(xa, xb) - X) + 0.5, 0, 1)
        Zc = np.clip(Z, z0, z1)
        yt = self.vy + self.f * (self.eye - Y1) / Zc; ybt = self.vy + self.f * (self.eye - Y0) / Zc
        ay = np.clip(np.minimum(Y - yt, ybt - Y) + 0.5, 0, 1)
        a = ax * ay * (Z <= z1 + 0.5) * (Z >= z0 - 0.5)
        idx = np.nonzero(a > 0)
        if len(idx[0]) == 0: return
        Zi = Zc[idx]; Yw = self.eye - (Y[idx] - self.vy) * Zi / self.f
        uu = (Zi - u0) * ppu - 0.5; vv = (Y1 - Yw) * ppv - 0.5
        fu = ppu * Zi * Zi / (self.f * wall)
        L = np.clip(np.log2(np.maximum(fu, 1.0)), 0, 6)
        k0 = np.floor(L).astype(int); t = (L - k0).astype(np.float32)
        tex = np.concatenate([alb_t, emi_t], -1)
        lv = self._levels(tex, int(k0.min()), int(min(6, k0.max() + 1)))
        acc = np.zeros((len(Zi), 6), np.float32)
        for k, tk in lv.items():
            w = np.where(k0 == k, 1 - t, 0) + np.where(k0 + 1 == k, t, 0)
            sel = w > 0
            if sel.any(): acc[sel] += w[sel, None] * _sample(tk, uu[sel], vv[sel])
        A = np.zeros(a.shape + (3,), np.float32); E = np.zeros_like(A)
        A[idx] = acc[:, :3]; E[idx] = acc[:, 3:]
        Zf = np.where(a > 0, Zc, np.inf).astype(np.float32)
        self._put(sl, a, A, E, Zf, self.ground_row(Zf))

    def _draw_front(self, side, wall, z, w0, w1, Y0, Y1, alb_t, emi_t, ppm):
        """warp a texture onto the plane Z = z; u runs outward from |X| = w0 to w1 on the given side"""
        xa, _ = self.project(side * w0, 0, z); xb, _ = self.project(side * w1, 0, z)
        _, ya = self.project(0, Y1, z); _, yb = self.project(0, Y0, z)
        sl = self._box(min(xa, xb) - 1, ya - 1, max(xa, xb) + 1, yb + 1)
        if sl is None: return
        X = self.XX[sl]; Y = self.YY[sl]
        ax = np.clip(np.minimum(X - min(xa, xb), max(xa, xb) - X) + 0.5, 0, 1)
        ay = np.clip(np.minimum(Y - ya, yb - Y) + 0.5, 0, 1)
        a = ax * ay
        Xw = (X - self.vx) * z / self.f; Yw = self.eye - (Y - self.vy) * z / self.f
        uu = (side * Xw - w0) * ppm - 0.5; vv = (Y1 - Yw) * ppm - 0.5
        A = _sample(alb_t, uu, vv); E = _sample(emi_t, uu, vv)
        self._put(sl, a, A, E, z, self.ground_row(z))

    def building(self, side, z0, z1, height, wall=None, depth=40.0, colour='#2a2f3d', floor=3.3, bay=2.6, lit=0.3,
                 shop=True, roof=True, shops=(0.45, 0.35, 0.2, 0.0), seed=None):
        """a block on one side of the street (side -1 left, +1 right) from depth z0 to z1, `height` metres tall,
        its street wall at |X| = wall: front face (Z = z0) plus the long street facade, textured and lit.
        shops = probabilities of (lit shop, roller shutter, dark shop, vending machines) along the ground floor"""
        seed = self._seed() if seed is None else seed
        wall = self.wall if wall is None else wall
        zv = max(z0, self.near_z(side, wall) * 0.98)
        if zv >= z1: return
        top = lambda z: min(height, self.eye + (self.vy + 4) * z / self.f + 1.0)
        # front face (only if it starts on screen)
        if z0 >= self.near_z(side, wall):
            Yt = top(z0); ppm = self.f / z0
            wm = min(depth, max(1.0, (self.vx if side < 0 else self.W - self.vx) * z0 / self.f - wall + 1))
            A, E = self._facade(wm, Yt, ppm, ppm, colour, floor, bay, lit, shop, seed + 3, flip=side < 0, mix=shops)
            A *= 0.8
            self._draw_front(side, wall, z0, wall, wall + wm, 0, Yt, A, E, ppm)
        # street facade
        Yt = top(z1)
        ppv = min(64.0, self.f / zv); ppu = min(64.0, max(6.0, self.f * wall / zv ** 2))
        A, E = self._facade(z1 - zv, Yt, ppu, ppv, colour, floor, bay, lit, shop, seed, flip=side > 0, mix=shops)
        self._draw_side(side, wall, zv, z1, 0, Yt, A, E, ppu, ppv, zv)
        if roof and height < top(z1) - 0.5:
            self._roof(side, wall, z0, z1, height, depth, seed + 5)

    def _roof(self, side, wall, z0, z1, height, depth, seed):
        """rooftop clutter seen against the sky: water tanks, masts with red beacons, a billboard frame"""
        r = np.random.default_rng(seed)
        for _ in range(r.integers(2, 5)):
            Z = r.uniform(z0 + 2, z1 - 2); X = side * (wall + r.uniform(0.5, 8))
            if r.random() < 0.5:
                w, h = r.uniform(1.5, 3.0), r.uniform(1.8, 3.2)
                pts = [self.project(X - w / 2, height, Z), self.project(X + w / 2, height, Z),
                       self.project(X + w / 2, height + h, Z), self.project(X - w / 2, height + h, Z)]
                sl, m = self._poly(pts)
                if sl is not None: self._put(sl, m, _lin('#20242e') * 0.6, 0.0, Z, self.ground_row(Z))
            else:
                h = r.uniform(4, 11)
                x0, y0 = self.project(X, height, Z); _, y1 = self.project(X, height + h, Z)
                wpx = max(1.0, 0.18 * self.f / Z)
                sl = self._box(x0 - wpx - 2, y1 - 2, x0 + wpx + 2, y0 + 2)
                if sl is None: continue
                c, _ = self._lines(sl, [([(x0, y0), (x0, y1)], wpx, 1.0)])
                self._put(sl, c, _lin('#1a1d26') * 0.6, 0.0, Z, self.ground_row(Z))
                if r.random() < 0.7: self.light(x0, y1, max(0.8, 0.12 * self.f / Z), RED, Z, 2.0)

    # ------------------------------------------------------------ neon
    def _tube(self, sl, skel, r, colour, depth, base=None, level=1.0, state='on', seed=None):
        """a glass tube along a thin skeleton mask (cropped to sl, with a margin of ~4r):
        light ~ chord length through the gas, near-white over-exposed core, halo in the air"""
        r = max(0.9, float(r)); s = r / 1.4
        g = blur(skel, s)
        on = skel > 0.5
        pk = np.percentile(g[on], 75) if on.sum() > 6 else g.max()
        n = np.clip(g / (pk + 1e-6), 1e-4, 2.0)
        chord = np.sqrt(np.clip(1 + 2 * (s / r) ** 2 * np.log(n), 0, 1)).astype(np.float32)
        body = smoothstep(0.0, 0.3, chord)
        col = _lin(colour)
        if state == 'dead':                                                    # unlit glass: pale, one glint
            glass = col * 0.12 + 0.07
            a = body * (depth < self.dep[sl])
            self.alb[sl] = self.alb[sl] * (1 - a[..., None]) + glass * a[..., None]
            self.emi[sl] += (chord ** 10 * 0.05)[..., None] * a[..., None]
            return
        lv = np.full(skel.shape, level, np.float32)
        if state == 'flicker':                                                 # caught mid-dip, patchy
            sd = self._seed() if seed is None else seed
            h, w = skel.shape
            nz = noise2d(h, w, max(3.0, 5 * r), 2, sd)
            lv = level * (0.08 + 0.42 * smoothstep(0.4, 0.7, nz))
        core = chord ** 5
        white = col * 0.3 + 0.7
        E = (col * (2.6 * chord)[..., None] + white * (5.5 * core)[..., None]) * lv[..., None]
        a = body * (depth < self.dep[sl])
        self.emi[sl] = self.emi[sl] * (1 - a[..., None]) + E * a[..., None]
        self.alb[sl] = self.alb[sl] * (1 - a[..., None]) + 0.2 * a[..., None]
        D = self.dep[sl]; D[a > 0.5] = depth
        if base is not None:
            B = self.base[sl]; B[a > 0.5] = base
        src = chord * lv
        halo = blur(src, 1.8 * r) * 0.9 + blur(src, 5.0 * r) * 0.45
        self._glow(sl, col * halo[..., None], depth + 0.02)

    def neon_path(self, pts, colour, z, r=None, level=1.0, state='on', closed=False, base=None, seed=None):
        """a tube bent along screen points `pts` (at depth z); r = tube radius in px"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        r = r if r is not None else max(1.0, 0.016 * self.f / z)
        m = 5 * r + 3
        sl = self._box(P[:, 0].min() - m, P[:, 1].min() - m, P[:, 0].max() + m, P[:, 1].max() + m)
        if sl is None: return
        skel, _ = self._lines(sl, [(P.tolist(), 1.4, 1.0)], ss=3)
        self._tube(sl, skel, r, colour, z - 0.03, self.ground_row(z) if base is None else base, level, state, seed)

    def neon_text(self, s, x, y, size, colour, z, vertical=False, spacing=0.0, dead=(), flicker=(), level=1.0,
                  r=None, base=None, kind='neon'):
        """neon lettering centred on screen point (x, y): one tube per character (so single characters can be
        `dead` or `flicker` by index); vertical stacks the characters top to bottom"""
        r = r if r is not None else max(0.9, size * 0.018)
        chars = list(s)
        if vertical:
            pitch = size * (1.0 + spacing)
            pos = [(x, y + (i - (len(chars) - 1) / 2) * pitch) for i in range(len(chars))]
        else:
            f = sign_font(kind, size)
            adv = [f.getlength(c) + spacing * size for c in chars]
            tot = sum(adv) - spacing * size
            cx = x - tot / 2; pos = []
            for c, a in zip(chars, adv):
                pos.append((cx + f.getlength(c) / 2, y)); cx += a
        for i, (c, (px, py)) in enumerate(zip(chars, pos)):
            if c == ' ': continue
            g = _glyph(c, size, kind)
            n = g.shape[0]
            m = int(5 * r + 3)
            sl = self._box(px - n / 2 - m, py - n / 2 - m, px + n / 2 + m, py + n / 2 + m)
            if sl is None: continue
            y0, x0 = sl[0].start, sl[1].start
            hh, ww = sl[0].stop - y0, sl[1].stop - x0
            canvas = np.zeros((hh, ww), np.float32)
            gy, gx = int(round(py - n / 2)) - y0, int(round(px - n / 2)) - x0
            ys0, xs0 = max(0, gy), max(0, gx)
            ys1, xs1 = min(hh, gy + n), min(ww, gx + n)
            if ys1 <= ys0 or xs1 <= xs0: continue
            canvas[ys0:ys1, xs0:xs1] = g[ys0 - gy:ys1 - gy, xs0 - gx:xs1 - gx]
            state = 'dead' if i in dead else 'flicker' if i in flicker else 'on'
            self._tube(sl, canvas, r, colour, z - 0.03, self.ground_row(z) if base is None else base, level, state)

    def sign(self, z, X0, X1, Y0, Y1, text='', colour=MAGENTA, kind='neon', vertical=True, face='#150f1a',
             border=None, latin=None, latin_colour=None, dead=(), flicker=(), level=1.0, char=0.74, box=0.35,
             text_colour=None, frame='#2a2c33'):
        """a sign board facing the camera at depth z (X0..X1, Y0..Y1 metres).
        kind='neon': dark backing, border tube (`border` colour, None = same as text) and tube lettering;
        kind='box':  a backlit lightbox — the acrylic glows `colour`, lettering in `text_colour` (dark = paint).
        `box` metres of depth show as a side panel toward the street centre."""
        s = self.f / z
        xa, ya = self.project(X0, Y1, z); xb, yb = self.project(X1, Y0, z)
        x0, x1 = min(xa, xb), max(xa, xb)
        base = self.ground_row(z)
        # side of the box, visible toward the vanishing point
        Xi = X1 if abs(X1) < abs(X0) else X0
        if box > 0:
            p = [self.project(Xi, Y1, z), self.project(Xi, Y1, z + box), self.project(Xi, Y0, z + box), self.project(Xi, Y0, z)]
            sl, m = self._poly(p)
            if sl is not None: self._put(sl, m, _lin(frame) * 0.5, 0.0, z + box / 2, base)
        # frame and face
        fr = max(1.0, 0.07 * s)
        sl = self._box(x0, ya, x1, yb)
        if sl is None: return
        X = self.XX[sl]; Y = self.YY[sl]
        a = np.clip(np.minimum(X - x0, x1 - X) + 0.5, 0, 1) * np.clip(np.minimum(Y - ya, yb - Y) + 0.5, 0, 1)
        inner = np.clip(np.minimum(np.minimum(X - x0, x1 - X), np.minimum(Y - ya, yb - Y)) - fr + 0.5, 0, 1)
        if kind == 'box':
            u = (X - x0) / max(1, x1 - x0); v = (Y - ya) / max(1, yb - ya)
            bands = 0.78 + 0.22 * (np.cos((u if vertical else v) * 2 * np.pi * 2) * 0.5 + 0.5)   # tubes behind the acrylic
            edge = smoothstep(0.0, 0.12, np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v)))
            E = _lin(colour) * (level * 1.2 * bands * (0.55 + 0.45 * edge) * inner)[..., None]
            self._put(sl, a, _lin(frame) * (1 - inner[..., None]) * 0.5 + 0.3 * inner[..., None], E, z, base)
        else:
            self._put(sl, a, _lin(frame) * 0.5 * (1 - inner[..., None]) + _lin(face) * inner[..., None], 0.0, z, base)
            ins = 0.14 * s
            bcol = colour if border is None else border
            if border is not False:
                rr = min(0.22 * s, (x1 - x0) * 0.2)
                P = self._rrect_path(x0 + ins, ya + ins, x1 - ins, yb - ins, rr)
                self.neon_path(P, bcol, z, r=max(0.9, 0.022 * s), level=level * 0.85, base=base)
        if not text: return
        w, h = x1 - x0, yb - ya
        pad = min(0.3 * s, 0.14 * w)
        lat_h = 0
        if latin:
            lat_h = min(0.2 * w, 0.42 * s)
            fl = sign_font('thin' if kind == 'box' else 'neon', lat_h)
            tw = sum(fl.getlength(ch) for ch in latin) + 0.1 * lat_h * (len(latin) - 1)
            if tw > 0.8 * w: lat_h *= 0.8 * w / tw
        n = len(text)
        if vertical:
            size = min((w - 2 * pad) * char, (h - 2 * pad - lat_h * 1.6) / n * 0.86)
            cx, cy = (x0 + x1) / 2, ya + pad + (h - 2 * pad - lat_h * 1.6) / 2
        else:
            size = min((h - 2 * pad - lat_h * 1.6) * char, (w - 2 * pad) / max(1, n) * 0.95)
            cx, cy = (x0 + x1) / 2, ya + pad + (h - 2 * pad - lat_h * 1.6) / 2
        if kind == 'box':
            self._painted_text(text, cx, cy, size, text_colour or '#1a0d10', z, vertical, level=level)
        else:
            self.neon_text(text, cx, cy, size, colour, z, vertical, 0.12 if vertical else 0.06, dead, flicker, level, base=base)
        if latin:
            ly = yb - pad - lat_h * 0.55
            if kind == 'box':
                self._painted_text(latin, cx, ly, lat_h, text_colour or '#1a0d10', z, False, level=level, kind='thin')
            else:
                self.neon_text(latin, cx, ly, lat_h, latin_colour or colour, z, False, 0.1, level=level, base=base,
                               r=max(0.8, lat_h * 0.03))

    def blade_sign(self, side, z, Y0, Y1, text='', colour=MAGENTA, reach=2.4, gap=0.3, wall=None, **kw):
        """a vertical sign sticking out over the street from the wall on `side`, facing the camera, on two
        steel brackets"""
        wall = self.wall if wall is None else wall
        Xo = side * (wall - gap); Xi = side * (wall - gap - reach)
        s = self.f / z
        for Yb in (Y1 - 0.25, Y0 + 0.25):                                   # brackets back to the wall
            xw, yw = self.project(side * wall, Yb, z); xs, ys = self.project(Xo, Yb, z)
            sl = self._box(min(xw, xs) - 3, yw - 3, max(xw, xs) + 3, yw + 3 + 0.08 * s)
            if sl is not None:
                c, _ = self._lines(sl, [([(xw, yw), (xs, ys)], max(1.0, 0.06 * s), 1.0)])
                self._put(sl, c, _lin('#2b2d33') * 0.5, 0.0, z + 0.05, self.ground_row(z))
        self.sign(z, Xo, Xi, Y0, Y1, text, colour, **kw)

    def _rrect_path(self, x0, y0, x1, y1, r, n=6):
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for t in np.linspace(a0, a0 + 90, n):
                pts.append((cx + r * np.cos(np.radians(t)), cy + r * np.sin(np.radians(t))))
        pts.append(pts[0])
        return pts

    def _painted_text(self, s, x, y, size, colour, z, vertical, level=1.0, kind='bold'):
        """lettering painted on a lightbox face: dark paint blocks the light, a colour glows as that colour"""
        f = sign_font(kind, size)
        n = int(size * 1.5) + 4
        chars = list(s) if vertical else [s]
        for i, c in enumerate(chars):
            if vertical:
                py = y + (i - (len(chars) - 1) / 2) * size * 1.08; px = x
                wbox = n
            else:
                py, px = y, x
                wbox = int(f.getlength(c)) + n
            sl2 = self._box(px - wbox / 2, py - n / 2, px + wbox / 2, py + n / 2)
            if sl2 is None: continue
            y0, x0 = sl2[0].start, sl2[1].start
            im = Image.new('L', (sl2[1].stop - x0, sl2[0].stop - y0), 0)
            ImageDraw.Draw(im).text((px - x0, py - y0), c, font=f, fill=255, anchor='mm')
            m = np.asarray(im, np.float32) / 255 * (z - 0.05 < self.dep[sl2] + 0.2)
            col = _lin(colour)
            lum = float(col @ LUMA)
            if lum < 0.02:                                                     # opaque paint
                self.emi[sl2] *= 1 - m[..., None] * 0.92
            else:
                self.emi[sl2] = self.emi[sl2] * (1 - m[..., None]) + col * (2.2 * level) * m[..., None]

    # ------------------------------------------------------------ hologram
    def hologram(self, z, X0, X1, Y0, Y1, title='海月', sub='SEA MOON', colour=CYAN, accent=MAGENTA, level=1.0,
                 scan=0.09, jelly=(0.4, 0.28), sub_y=0.9, seed=None):
        """a translucent projected ad panel at depth z (X0..X1, Y0..Y1 metres), light only: a moon jellyfish,
        a vertical mincho title on the right, a spaced Latin sub-line; scanlines at `scan` metres pitch on the
        panel, a slow brightness band, torn slices, colour fringes, soft edges and a faint projection edge.
        jelly = (x, y) of the bell as fractions of the panel; sub_y = baseline of the sub-line (fraction).
        It is additive light: walls behind it stay visible, and it lights the fog and the walls around it."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        xa, ya = self.project(X0, Y1, z); xb, yb = self.project(X1, Y0, z)
        sl = self._box(xa, ya, xb, yb)
        if sl is None: return
        y0, x0 = sl[0].start, sl[1].start
        h, w = sl[0].stop - y0, sl[1].stop - x0
        A = np.zeros((h, w), np.float32); B = np.zeros((h, w), np.float32)
        ox, oy = xa - x0, ya - y0                                              # panel origin inside the box
        pw, ph = xb - xa, yb - ya
        jx, jy, R = ox + pw * jelly[0], oy + ph * jelly[1], pw * 0.3
        self._jellyfish(A, B, jx, jy, R, r)
        # title: big vertical mincho on the right, filled light; sub-line in spaced Latin at the bottom
        tsize = pw * 0.2
        f = sign_font('mincho', tsize)
        im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
        for i, c in enumerate(title):
            d.text((ox + pw * 0.83, oy + ph * 0.2 + i * tsize * 1.12), c, font=f, fill=255, anchor='mm')
        T = np.asarray(im, np.float32) / 255
        A += blur(T, 0.6) * 1.3
        im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
        fs = sign_font('light', max(9, pw * 0.062))
        x = ox + pw * 0.08
        for c in sub:
            d.text((x, oy + ph * sub_y), c, font=fs, fill=255, anchor='ls'); x += fs.getlength(c) + pw * 0.022
        d.line([(ox + pw * 0.08, oy + ph * (sub_y + 0.02)), (ox + pw * 0.38, oy + ph * (sub_y + 0.02))], fill=160, width=1)
        B += np.asarray(im, np.float32) / 255 * 1.2
        # the panel itself: faint sheet with soft edges
        X = self.XX[sl] - x0; Y = self.YY[sl] - y0
        u = (X - ox) / pw; v = (Y - oy) / ph
        edge = smoothstep(0.0, 0.06, np.minimum(np.minimum(u, 1 - u), np.minimum(v, 1 - v)))
        rim_ = np.clip(1 - np.abs(np.minimum(np.minimum(u, 1 - u) * pw, np.minimum(v, 1 - v) * ph) - 1.5) / 1.2, 0, 1)
        A = A * edge + 0.014 * edge + 0.16 * rim_ * (0.6 + 0.4 * np.cos(v * 40))
        # scanlines at a fixed pitch on the panel, a slow bright band, torn slices
        p = max(3.2, scan * self.f / z)
        sc = 0.5 + 0.5 * (np.cos(Y * 2 * np.pi / p) * 0.5 + 0.5)
        band = 1 + 0.5 * np.exp(-((v - r.uniform(0.55, 0.75)) / 0.05) ** 2)
        flick = 1 + 0.12 * (fbm1d(h, 30, 3, int(r.integers(1 << 30)))[:, None])
        rgbA = A * sc * band * flick; rgbB = B * sc * band * flick
        img = rgbA[..., None] * _lin(colour) * 2.0 + rgbB[..., None] * _lin(accent) * 2.0
        for _ in range(3):                                                     # torn slices (kept off the lettering)
            yy = int(oy + r.uniform(0.4, 0.6) * ph); hh = int(r.uniform(2, 7))
            img[yy:yy + hh] = np.roll(img[yy:yy + hh], int(r.choice([-1, 1]) * r.uniform(5, 16)), axis=1)
        img[..., 0] = np.roll(img[..., 0], 2, axis=1); img[..., 2] = np.roll(img[..., 2], -2, axis=1)   # fringes
        dust = (r.random((h, w)) < 0.0025) * edge * r.uniform(0.5, 2.0, (h, w))
        img += dust[..., None] * _lin(colour)
        img = img * level * 2.4
        self._glow(sl, img + blur(img.mean(-1), 3)[..., None] * _lin(colour) * 0.4, z, light=0.6)

    def _jellyfish(self, A, B, cx, cy, R, r):
        """a moon jellyfish (海月) drawn in light, seen from the side and a little below: a translucent dome
        built as a 3-D surface (canals run over it, the front of the margin is bright and the back faint),
        four soft gonad rings glowing through it in the accent colour, a fringe of fine marginal tentacles and
        four frilly oral-arm ribbons trailing beneath"""
        h, w = A.shape
        dh, mh = R * 0.58, R * 0.13                                            # dome height, margin tilt
        P3 = lambda th, ph: (cx + R * np.sin(th) * np.cos(ph), cy - dh * np.cos(th) + mh * np.sin(th) * np.sin(ph))
        la = []                                                                # (points, width, value, fade-to-tip)
        la.append(([P3(th, 0.0) for th in np.linspace(np.pi / 2, 0, 40)] + [P3(th, np.pi) for th in np.linspace(0, np.pi / 2, 40)],
                   max(2.0, R * 0.026), 1.1, False))                           # silhouette of the dome
        la.append(([P3(np.pi / 2, ph) for ph in np.linspace(0, np.pi, 70)], max(2.0, R * 0.024), 1.0, False))        # margin, front
        la.append(([P3(np.pi / 2, ph) for ph in np.linspace(np.pi, 2 * np.pi, 70)], max(1.2, R * 0.012), 0.35, False))  # margin, back
        for k in range(16):                                                    # canals over the dome
            ph = 2 * np.pi * (k + 0.5) / 16
            v = 0.45 if np.sin(ph) > 0 else 0.18
            la.append(([P3(th, ph) for th in np.linspace(0.08, np.pi / 2, 16)], max(1.0, R * 0.01), v, False))
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        gon = np.zeros((h, w), np.float32)
        yg = cy - dh * 0.32                                                    # gonads lie on a plane inside the bell:
        for k in range(4):                                                     # seen nearly edge-on they flatten into a
            ph = np.pi / 4 + k * np.pi / 2                                     # soft cluster (never a pair of 'eyes')
            gx, gy = cx + R * 0.24 * np.cos(ph), yg + mh * 1.6 * 0.24 * np.sin(ph)
            d = np.hypot((xx - gx) / (R * 0.16), (yy - gy) / (R * 0.16 * mh * 1.6 / R + R * 0.03))
            gon += np.exp(-((d - 0.75) / 0.35) ** 2) * (0.8 if np.sin(ph) > 0 else 0.5)
        B += gon
        for k in range(64):                                                    # marginal tentacles
            ph = 2 * np.pi * k / 64
            x0, y0 = P3(np.pi / 2, ph)
            L = R * r.uniform(0.4, 0.95); sw = r.uniform(0, 6)
            v = 0.75 if np.sin(ph) > 0 else 0.35
            la.append(([(x0 + R * 0.05 * np.sin(q * 5 + sw) + R * 0.1 * q * q, y0 + q * L) for q in np.linspace(0, 1, 14)],
                       max(1.0, R * 0.011), v, True))
        arms = Image.new('F', (w * 2, h * 2), 0.0); da = ImageDraw.Draw(arms)
        for k in range(4):                                                     # oral arms: frilly ribbons
            x0 = cx + (k - 1.5) * R * 0.12
            L = R * r.uniform(1.4, 1.9); sw = r.uniform(0, 6)
            q = np.linspace(0, 1, 70)
            mid = x0 + R * 0.12 * np.sin(q * 5 + sw) * q + R * 0.08 * q * q
            half = R * (0.02 + 0.07 * np.sin(np.pi * np.clip(q * 1.1, 0, 1))) * (1 + 0.35 * np.sin(q * 38 + k * 2))
            ys = cy + mh + q * L
            left = list(zip(mid - half, ys)); right = list(zip(mid + half, ys))
            da.polygon([(x * 2, y * 2) for x, y in left + right[::-1]], fill=0.22)
            for edge in (left, right):
                la.append((edge, max(1.0, R * 0.012), 0.85, True))
        A += np.asarray(arms.resize((w, h), Image.BOX))
        im = Image.new('F', (w * 2, h * 2), 0.0); d = ImageDraw.Draw(im)
        for pts, wd, v, tip in la:
            q = [(x * 2, y * 2) for x, y in pts]
            n = len(q)
            for i in range(n - 1):
                fade = v * (1 - i / n) ** 0.9 if tip else v
                d.line([q[i], q[i + 1]], fill=float(fade), width=max(1, int(round(wd * 2))))
        A += np.asarray(im.resize((w, h), Image.BOX))
        dome = (((xx - cx) / R) ** 2 + ((yy - cy) / dh) ** 2 < 1) & (yy < cy + mh * 0.5)
        A += dome * (0.05 + 0.08 * np.clip((cy - yy) / dh, 0, 1))
        A += blur(A, R * 0.04) * 0.45
        B += blur(B, R * 0.05) * 0.5

    # ------------------------------------------------------------ bridges, cables, trails
    def walkway(self, z, Y, thick=2.4, deep=3.5, X0=None, X1=None, colour='#1b1e28', windows=AMBER, lamps=AMBER, seed=None):
        """a covered footbridge across the street at depth z, underside Y metres up: facing wall with a strip of
        lit windows, the underside (seen from below) with a row of lamps"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        X0 = -self.wall - 2 if X0 is None else X0; X1 = self.wall + 2 if X1 is None else X1
        # underside
        p = [self.project(X0, Y, z), self.project(X1, Y, z), self.project(X1, Y, z + deep), self.project(X0, Y, z + deep)]
        sl, m = self._poly(p)
        if sl is not None:
            self._put(sl, m, _lin(colour) * 0.7, 0.0, z + deep / 2, self.ground_row(z + deep / 2))
            zc = z + deep / 2
            for X in np.arange(X0 + 1.5, X1, 3.0):
                lx, ly = self.project(X, Y, zc)
                self.light(lx, ly, max(0.8, 0.07 * self.f / zc), lamps, zc, 1.6, 3.0)
        # face
        xa, ya = self.project(X0, Y + thick, z); xb, yb = self.project(X1, Y, z)
        sl = self._box(xa, ya, xb, yb)
        if sl is None: return
        X = self.XX[sl]; Yp = self.YY[sl]
        a = np.clip(np.minimum(X - xa, xb - X) + 0.5, 0, 1) * np.clip(np.minimum(Yp - ya, yb - Yp) + 0.5, 0, 1)
        s = self.f / z
        v = (yb - Yp) / s                                                     # metres above the underside
        Xw = (X - self.vx) / s
        n = _fbm(Xw / 1.5, v / 0.8, 3, int(r.integers(1 << 30)))
        alb = _lin(colour)[None, None] * (0.7 + 0.5 * n)[..., None]
        strip = (v > 0.75) & (v < 1.75)
        pane = strip & ((Xw % 1.6) > 0.1)
        wl = r.random(int((X1 - X0) / 1.6) + 4) < 0.7
        idx = np.clip(((Xw - X0) / 1.6).astype(int), 0, len(wl) - 1)
        E = np.zeros(a.shape + (3,), np.float32)
        if windows:
            E[pane & wl[idx]] = _lin(windows) * 0.6
            E *= (0.7 + 0.5 * (v - 0.75))[..., None]
        if windows: alb[strip] = 0.02
        self._put(sl, a, alb, E, z, self.ground_row(z))

    def cables(self, n=20, z=(12, 90), Y=(6, 16), sag=(0.3, 1.6), width=0.04, colour='#0b0c10', seed=None):
        """power and data lines strung across the street between the walls, sagging, thin, lit by the neon"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        segs = []
        for _ in range(n):
            za = r.uniform(*z); zb = za + r.uniform(-3, 3)
            ya = r.uniform(*Y); yb = ya + r.uniform(-1.5, 1.5)
            sg = r.uniform(*sag)
            t = np.linspace(0, 1, 60)
            Xs = -self.wall + 2 * self.wall * t; Zs = za + (zb - za) * t
            Ys = ya + (yb - ya) * t - sg * 4 * t * (1 - t)
            xs, ys = self.project(Xs, Ys, Zs)
            segs.append((np.stack([xs, ys], 1), Zs))
            if r.random() < 0.35:                                              # a second line in the same bundle
                xs2, ys2 = self.project(Xs, Ys - 0.25, Zs + 0.1)
                segs.append((np.stack([xs2, ys2], 1), Zs + 0.1))
        for P, Zs in segs:
            zm = float(Zs.mean())
            sl = self._box(P[:, 0].min() - 4, P[:, 1].min() - 4, P[:, 0].max() + 4, P[:, 1].max() + 4)
            if sl is None: continue
            wpx = width * self.f / zm
            c, _ = self._lines(sl, [(P.tolist(), max(1.1, wpx), 1.0)])
            self._put(sl, c * min(1.0, 0.4 + wpx), _lin(colour) * 0.8, 0.0, zm, self.ground_row(zm))

    def light_trail(self, pts, colour, level=1.4, width=0.06, pair=1.5, fade=(0.2, 0.3), strobe=0, head=True, seed=None):
        """a long-exposure trail of a flying car along 3-D control points (metres): two parallel lamps
        `pair` metres apart, fading in and out; `strobe` adds blinking nav-light dashes"""
        P = spline(np.asarray(pts, np.float32), 24)
        N = len(P)
        t = np.linspace(0, 1, N)
        env = np.clip(np.minimum(t / fade[0], (1 - t) / fade[1]), 0, 1) ** 1.5
        xs, ys = self.project(P[:, 0], P[:, 1], P[:, 2])
        m = 30
        sl = self._box(xs.min() - m, ys.min() - m, xs.max() + m, ys.max() + m)
        if sl is None: return
        y0, x0 = sl[0].start, sl[1].start
        h, w = sl[0].stop - y0, sl[1].stop - x0
        lay = Image.new('F', (w * 2, h * 2), 0.0); dep = Image.new('F', (w * 2, h * 2), 1e6)
        dl, dd = ImageDraw.Draw(lay), ImageDraw.Draw(dep)
        offs = (-pair / 2, pair / 2) if pair else (0.0,)
        for o in offs:
            xo, yo = self.project(P[:, 0] + o, P[:, 1], P[:, 2])
            for i in range(N - 1):
                Z = P[i, 2]
                wd = max(1, int(round(max(0.7, width * self.f / Z) * 2)))
                v = level * env[i] * self.fog_t(Z)
                if strobe and (i // max(1, N // strobe)) % 2: v *= 0.35
                seg = [((xo[i] - x0) * 2, (yo[i] - y0) * 2), ((xo[i + 1] - x0) * 2, (yo[i + 1] - y0) * 2)]
                dl.line(seg, fill=float(v), width=wd); dd.line(seg, fill=float(Z), width=wd + 2)
        L = np.asarray(lay.resize((w, h), Image.BOX))
        Dz = np.asarray(dep.resize((w, h), Image.NEAREST))
        vis = (Dz < self.dep[sl]).astype(np.float32)
        L = L * vis
        col = _lin(colour)
        g = L * 1.6 + blur(L, 1.5) * 1.0 + blur(L, 6) * 0.5
        self.add[sl] += g[..., None] * (col * 0.8 + 0.2)
        self.lsrc[sl] += (blur(L, 4) * 0.8)[..., None] * col
        if head:                                                              # the car itself, at the bright end
            for o in offs:
                hx, hy = self.project(P[-1, 0] + o, P[-1, 1], P[-1, 2])
                self.light(hx, hy, max(0.9, 0.12 * self.f / P[-1, 2]), colour, P[-1, 2], 2.2, 5.0)

    # ------------------------------------------------------------ street
    def street(self, asphalt='#1d2027', paving='#2c2f36', kerb='#555558', paint='#cfcabb', crossing=(15.0, 4.2),
               centre=True, puddles=0.5, seed=None):
        """the wet street, evaluated per pixel in ground coordinates: asphalt with aggregate and tar patches,
        kerbs, paving joints, worn lane paint, a zebra crossing, puddles (more along the gutters)"""
        seed = self._seed() if seed is None else seed
        y0 = int(np.floor(self.vy)) + 1
        sl = (slice(y0, self.H), slice(0, self.W))
        Y = self.YY[sl]; X = self.XX[sl]
        Z = (self.f * self.eye / np.maximum(Y - self.vy, 0.4)).astype(np.float32)
        Xg = ((X - self.vx) * Z / self.f).astype(np.float32)
        fx = Z / self.f; fz = Z * Z / (self.f * self.eye)
        foot = np.maximum(fx, fz)
        ax = np.abs(Xg); road = self.road

        def stripe(d, half, fw):                                              # antialiased band |d| < half
            return np.clip((half - np.abs(d)) / np.maximum(fw, 1e-4) + 0.5, 0, 1)

        agg = _fbm(Xg * 7, Z * 7, 3, seed, foot * 7)
        blot = _fbm(Xg * 0.35, Z * 0.2, 4, seed + 1, foot * 0.35)
        alb = _lin(asphalt)[None, None] * (0.8 + 0.35 * (agg - 0.5) + 0.5 * (blot - 0.5))[..., None]
        tar = _fbm(Xg * 0.9, Z * 0.5, 3, seed + 2, foot * 0.9)
        alb *= (1 - 0.35 * smoothstep(0.62, 0.66, tar))[..., None]
        walk = np.clip((ax - road - 0.22) / np.maximum(fx, 1e-3) + 0.5, 0, 1)
        kb = stripe(ax - road - 0.11, 0.11, fx)
        joints = np.maximum(stripe(((Xg + 0.3) % 0.6) - 0.3, 0.015, fx), stripe(((Z + 0.3) % 0.6) - 0.3, 0.015, fz))
        joints *= np.clip(0.03 / np.maximum(foot, 1e-3), 0, 1)
        pv = _lin(paving)[None, None] * (0.8 + 0.4 * (agg - 0.5) + 0.3 * (blot - 0.5))[..., None] * (1 - 0.55 * joints)[..., None]
        alb = alb * (1 - walk[..., None]) + pv * walk[..., None]
        alb = alb * (1 - kb[..., None]) + _lin(kerb) * (0.85 + 0.3 * agg)[..., None] * kb[..., None]
        gut = stripe(ax - road + 0.12, 0.1, fx)
        alb *= (1 - 0.5 * gut)[..., None]
        pm = np.zeros_like(Z)
        if centre:
            pm = np.maximum(pm, stripe(Xg, 0.07, fx) * stripe((Z % 9.0) - 2.0, 1.6, fz))
        pm = np.maximum(pm, stripe(ax - (road - 0.45), 0.06, fx))
        if crossing:
            zc, zw = crossing
            inz = stripe(Z - (zc + zw / 2), zw / 2, fz) * (ax < road - 0.2)
            pm = np.maximum(pm, inz * stripe(((Xg + 0.275) % 1.1) - 0.55, 0.26, fx))
        wear = smoothstep(0.3, 0.6, _fbm(Xg * 2.5, Z * 2.5, 3, seed + 5, foot * 2.5))
        pm = pm * (0.35 + 0.65 * wear) * (1 - walk)
        alb = alb * (1 - pm[..., None] * 0.85) + _lin(paint) * 0.55 * pm[..., None] * 0.85
        p = _fbm(Xg * 0.28, Z * 0.14, 4, seed + 7, foot * 0.28)
        edge = np.clip((ax - road + 1.4) / 1.4, 0, 1) * (1 - walk)            # water collects in the gutters
        pud = smoothstep(0.6 - 0.12 * puddles - 0.16 * edge, 0.66 - 0.12 * puddles - 0.16 * edge, p)
        pud *= 1 - 0.75 * walk
        damp = 0.45 + 0.55 * _fbm(Xg * 1.3, Z * 0.7, 3, seed + 9, foot * 1.3)
        glint = _fbm(Xg * 3.2, Z * 1.4, 3, seed + 11, foot * 3.2)                # wet film broken by the aggregate
        damp = damp * (0.2 + 0.8 * smoothstep(0.38, 0.7, glint)) * (1 - 0.5 * pm)
        a = np.ones_like(Z)
        self._put(sl, a, alb.astype(np.float32), 0.0, Z, None)
        vis = (np.abs(self.dep[sl] - Z) < 1e-3).astype(np.float32)
        self.ground[sl] = np.maximum(self.ground[sl], vis)
        self.pools[sl] = pud * vis; self.damp[sl] = damp * vis
        self.street_on = True

    def puddle(self, X, Z, rx, rz, seed=None):
        """a puddle on the street centred at ground point (X, Z), radii in metres, ragged edge"""
        sd = self._seed() if seed is None else seed
        pts = [self.project(X + sx * rx, 0, Z + sz * rz) for sx, sz in ((-1.3, -1.3), (1.3, -1.3), (1.3, 1.3), (-1.3, 1.3))]
        P = np.asarray(pts)
        sl = self._box(P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())
        if sl is None: return
        Zg = self.f * self.eye / np.maximum(self.YY[sl] - self.vy, 0.4)
        Xg = (self.XX[sl] - self.vx) * Zg / self.f
        d = np.hypot((Xg - X) / rx, (Zg - Z) / rz) + 0.35 * (_fbm(Xg * 1.2, Zg * 1.2, 3, sd) - 0.5)
        fw = np.maximum(Zg / self.f / rx, Zg * Zg / (self.f * self.eye) / rz)
        m = np.clip((1 - d) / np.maximum(fw * 4.0, 0.08), 0, 1) * self.ground[sl]
        self.pools[sl] = np.maximum(self.pools[sl], m)
        self.damp[sl] = np.maximum(self.damp[sl], np.clip((1.35 - d) / 0.35, 0, 1) * 0.9 * self.ground[sl])

    def grate(self, X, Z, w=1.0, d=0.6, glow='#ff9a4a', level=0.25):
        """a steel grate in the street (dry, dark slats, a faint warm glow from below)"""
        xs = [self.project(X + sx * w / 2, 0, Z + sz * d / 2) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        sl, m = self._poly(xs)
        if sl is None: return
        Y = self.YY[sl]; Xp = self.XX[sl]
        Zg = self.f * self.eye / np.maximum(Y - self.vy, 0.4)
        Xg = (Xp - self.vx) * Zg / self.f
        slat = (np.sin((Xg - X) * 2 * np.pi / 0.07) > 0.1).astype(np.float32)
        slat = 0.5 + 0.5 * slat * np.clip(0.035 / (Zg / self.f), 0, 1)
        m = m * (np.abs(self.dep[sl] - Zg) < 0.5)
        self.alb[sl] = self.alb[sl] * (1 - m[..., None]) + _lin('#15171b') * slat[..., None] * m[..., None]
        self.emi[sl] += _lin(glow) * (level * (1 - slat) * m)[..., None]
        self.pools[sl] *= 1 - m

    # ------------------------------------------------------------ figure
    def figure(self, X, Z, height=1.74, umbrella='clear', coat='#07080c', rim=(MAGENTA, CYAN), stride=0.16):
        """a lone figure walking away (seen from behind, no face) in a long coat, holding an umbrella; a thin rim
        of the two sides' neon on the silhouette. umbrella: 'clear' (see-through canopy: bright rim, faint ribs,
        beads of rain), 'dark', or None"""
        k = self.f / Z * height / 1.74
        xf, yf = self.project(X, 0, Z)
        sl = self._box(xf - 0.8 * k, yf - 2.35 * k, xf + 0.8 * k, yf + 3)
        if sl is None: return
        y0, x0 = sl[0].start, sl[1].start
        h, w = sl[0].stop - y0, sl[1].stop - x0
        S = 4
        T = lambda px, py: ((xf + px * k - x0) * S, (yf - py * k - y0) * S)
        im = Image.new('L', (w * S, h * S), 0); d = ImageDraw.Draw(im)
        coat_pts = spline([(-0.245, 0.56), (-0.24, 0.95), (-0.225, 1.3), (-0.17, 1.42), (-0.06, 1.465), (0.06, 1.465),
                           (0.17, 1.42), (0.225, 1.3), (0.235, 0.95), (0.26, 0.58)], 8)
        d.polygon([T(*p) for p in coat_pts] + [T(0.0, 0.6)], fill=255)
        d.polygon([T(-0.14, 0.0), T(-0.05, 0.0), T(-0.04, 0.7), T(-0.15, 0.7)], fill=255)                      # legs
        d.polygon([T(0.045, 0.02 + stride * 0.35), T(0.13, 0.03 + stride * 0.3), T(0.14, 0.7), T(0.03, 0.7)], fill=255)
        d.polygon([T(-0.05, 1.44), T(0.05, 1.44), T(0.045, 1.55), T(-0.045, 1.55)], fill=255)                  # neck
        hx, hy = T(0.0, 1.625); d.ellipse([hx - 0.093 * k * S, hy - 0.113 * k * S, hx + 0.093 * k * S, hy + 0.113 * k * S], fill=255)
        wa = max(2, int(0.085 * k * S))
        d.line([T(0.19, 1.38), T(0.27, 1.13), T(0.12, 1.2)], fill=255, width=wa, joint='curve')              # raised arm
        d.line([T(-0.2, 1.36), T(-0.265, 0.92)], fill=255, width=wa, joint='curve')                           # hanging arm
        body = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        shaft = Image.new('L', (w * S, h * S), 0)
        ImageDraw.Draw(shaft).line([T(0.1, 1.2), T(0.03, 2.13)], fill=255, width=max(1, int(0.022 * k * S)))
        shaft = np.asarray(shaft.resize((w, h), Image.BOX), np.float32) / 255
        can = Image.new('L', (w * S, h * S), 0); dc = ImageDraw.Draw(can)
        cx, apex, rimy, R = 0.03, 2.14, 1.86, 0.56
        top = [T(cx + R * np.cos(t), rimy + (apex - rimy) * np.sin(t)) for t in np.linspace(0, np.pi, 40)]
        tips = [cx - R + 2 * R * i / 8 for i in range(9)]
        scal = []
        for i in range(8):                                                     # the rim sags between rib tips
            for t in np.linspace(0, 1, 6):
                scal.append(T(tips[i] + (tips[i + 1] - tips[i]) * t, rimy + 0.035 * np.sin(np.pi * t)))
        dc.polygon(top + scal, fill=255)
        canopy = np.asarray(can.resize((w, h), Image.BOX), np.float32) / 255
        ribs = Image.new('L', (w * S, h * S), 0); dr = ImageDraw.Draw(ribs)
        for tx in tips[1:-1]:
            u = (tx - cx) / R
            dr.line([T(cx + R * u * q, apex - (apex - rimy) * q ** 2) for q in np.linspace(0, 1, 8)], fill=255, width=max(1, S // 2))
        ribs = np.asarray(ribs.resize((w, h), Image.BOX), np.float32) / 255 * canopy
        self._put(sl, np.maximum(body, shaft), _lin(coat), 0.0, Z, yf)
        for c, dx in zip(rim, (-1, 1)):                                        # rim light from each side of the street
            e = np.clip(body - np.roll(body, -dx * max(1, int(0.025 * k)), axis=1), 0, 1) * body
            self.emi[sl] += _lin(c) * (e * 0.55)[..., None]
        if umbrella == 'clear':
            a = canopy * 0.38
            self.alb[sl] = self.alb[sl] * (1 - a[..., None]) + 0.22 * a[..., None]
            edge = np.clip(canopy - blur(canopy, max(1.0, 0.03 * k)), 0, 1) * 2.5
            self.emi[sl] += (_lin('#dfe8ff') * 0.3 + _lin(rim[0]) * 0.45) * edge[..., None] + _lin('#dfe8ff') * (ribs * 0.18)[..., None]
            drops = (np.random.default_rng(3).random((h, w)) < 0.025) * canopy
            self.emi[sl] += drops[..., None] * 0.5
            D = self.dep[sl]; D[canopy > 0.5] = Z
            B = self.base[sl]; B[canopy > 0.5] = yf
            G = self.ground[sl]; G *= 1 - canopy
        elif umbrella:
            self._put(sl, canopy, _lin('#0b0c12'), 0.0, Z, yf)

    # ------------------------------------------------------------ atmosphere
    def steam(self, X, Z, height=5.0, width=0.6, drift=1.4, density=1.0, seed=None):
        """a plume rising from a grate at ground point (X, Z): widens, thins, curls and bends with the wind"""
        sd = self._seed() if seed is None else seed
        s = self.f / Z
        x0, y0 = self.project(X, 0, Z)
        hp = height * s
        m = (width * 2.2 + abs(drift)) * s
        sl = self._box(x0 - m, y0 - hp, x0 + m, y0 + 0.3 * s)
        if sl is None: return
        Yl = self.YY[sl]; Xl = self.XX[sl]
        v = np.clip((y0 - Yl) / hp, 0, 1)
        h, w = Yl.shape
        n1 = noise2d(h, w, max(4.0, 0.9 * s), 4, sd)
        n2 = noise2d(h, w, max(4.0, 1.4 * s), 3, sd + 1)
        wob = fbm1d(h, 20, 3, sd + 2)[:, None] * 0.35 * s * v
        cen = x0 + drift * s * v ** 1.7 + wob + (n2 - 0.5) * 0.6 * s * v
        wid = width * s * (0.35 + 1.5 * v)
        q = (Xl - cen) / wid
        warp = _sample(n1, np.clip(Xl - Xl.min() + (n2 - 0.5) * 0.8 * s, 0, w - 1), np.clip(Yl - Yl.min() + (n1 - 0.5) * 0.8 * s, 0, h - 1))
        d = np.exp(-q * q) * (0.25 + 1.1 * smoothstep(0.3, 0.8, warp)) * smoothstep(0.0, 0.06, v) * (1 - v) ** 1.4
        d = d * density * (Z < self.dep[sl] + 1.0)
        self.steam_d[sl] = np.maximum(self.steam_d[sl], 0) + d.astype(np.float32)

    def mist(self, y=None, h=70, density=0.35, seed=None):
        """a low drift of mist lying along the street toward the vanishing point"""
        sd = self._seed() if seed is None else seed
        y = self.vy + 8 if y is None else y
        n = np.asarray(Image.fromarray(noise2d(self.H // 2, self.W // 8, 10, 4, sd)).resize((self.W, self.H), Image.BICUBIC))
        band = np.exp(-((self.YY - y) / h) ** 2)
        far = smoothstep(25.0, 90.0, np.where(np.isfinite(self.dep), self.dep, 1e4))   # it lies down the street, not on you
        self.steam_d += (band * far * smoothstep(0.3, 0.8, n) * density).astype(np.float32)

    def rain(self, far=6000, mid=1500, near=90, slant=0.1, rings=380, seed=None):
        """rain in three depths (streak masks, lit later by the light around each streak) and splash rings"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        H, W = self.H, self.W
        self.rain_layers = []
        for n, L, wd, a, bl, gain in ((far, (8, 20), 1, (0.2, 0.55), 0.0, 0.22), (mid, (24, 55), 1, (0.3, 0.8), 0.35, 0.42),
                                      (near, (150, 330), 3, (0.25, 0.55), 2.6, 0.7)):
            im = Image.new('F', (W, H), 0.0); d = ImageDraw.Draw(im)
            xs = r.uniform(-60, W + 60, n); ys = r.uniform(-300, H, n)
            ls = r.uniform(*L, n); al = r.uniform(*a, n); sk = slant + r.normal(0, 0.012, n)
            for x, y, l, v, k in zip(xs, ys, ls, al, sk):
                d.line([(x, y), (x + k * l, y + l)], fill=float(v), width=wd)
            m = np.asarray(im)
            if bl: m = blur(m, bl)
            self.rain_layers.append((m.astype(np.float32), gain))
        # splash rings on the wet ground (ellipses flattened by perspective)
        im = Image.new('F', (W, H), 0.0); d = ImageDraw.Draw(im)
        for _ in range(rings):
            Z = 1.0 / r.uniform(1 / 60.0, 1 / 3.0); X = r.uniform(-self.wall, self.wall)
            x, y = self.project(X, 0, Z)
            if not (0 <= x < W and self.vy < y < H): continue
            rad = r.uniform(0.03, 0.11)
            rx = rad * self.f / Z; ry = rx * self.eye / Z
            if rx < 0.8: continue
            d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=float(r.uniform(0.3, 0.8)), width=1)
            if r.random() < 0.4:
                d.line([(x, y - ry - 0.6 * rx), (x, y - ry)], fill=0.8, width=1)       # the crown
        self.rings = np.asarray(im, np.float32)

    def glitch(self, y, h=16, shift=14, split=4):
        """one torn scanline band across the finished frame (used sparingly: one or two per picture)"""
        self.glitch_bands.append((int(y), int(h), int(shift), int(split)))

    # ------------------------------------------------------------ rendering passes
    def _reflect(self, img, haze):
        H, W = self.H, self.W
        src = (self.base > self.vy) & (self.YY < self.base) & (self.ground < 0.5)
        src |= np.isinf(self.dep) & (self.YY < self.vy)
        ys, xs = np.nonzero(src)
        b = self.base[ys, xs]
        yr = np.rint(2 * b - ys).astype(np.int64)
        ok = (yr < H) & (yr > self.vy)
        ys, xs, yr = ys[ok], xs[ok], yr[ok]
        d = self.dep[ys, xs]
        o = np.argsort(d, kind='stable')                                      # nearest first ...
        tgt = (yr * W + xs)[o]
        _, first = np.unique(tgt, return_index=True)                         # ... and the nearest wins
        sel = o[first]
        R = np.zeros((H, W, 3), np.float32); C = np.zeros((H, W), np.float32)
        R[yr[sel], xs[sel]] = img[ys[sel], xs[sel]]
        C[yr[sel], xs[sel]] = 1
        Rs = _blur_axis(R * C[..., None], 5, 0); Cs = _blur_axis(C, 5, 0)
        ym = np.clip(2 * (self.vy + 6) - self.YY, 0, H - 1).astype(np.int32)   # what hides behind near things: haze
        fill = haze[ym, self.XX.astype(np.int32)]
        R = np.where(C[..., None] > 0, R, np.where((Cs > 0.3)[..., None], Rs / np.maximum(Cs, 1e-3)[..., None], fill))
        # ripples: displacement noise in ground coordinates
        g = self.ground
        Yr = np.maximum(self.YY - self.vy, 0.4)
        Z = self.f * self.eye / Yr; Xg = (self.XX - self.vx) * Z / self.f
        near = np.clip(Yr / (H - self.vy), 0, 1)
        amp = 1.0 + 7.0 * near
        n1 = _vnoise(Xg * 2.2, Z * 5.0, 11) - 0.5; n2 = _vnoise(Xg * 1.1, Z * 2.3, 12) - 0.5
        dx = (n1 * 0.7 + n2 * 0.6) * amp * 2.0
        dy = (_vnoise(Xg * 3.0, Z * 6.0, 13) - 0.5) * amp * 0.8
        n3 = _vnoise(Xg * 9.0, Z * 14.0, 14) - 0.5                              # rain-drop chop, strongest near
        dx = dx + n3 * amp * 0.9 * self.pools; dy = dy + (_vnoise(Xg * 8.0, Z * 12.0, 15) - 0.5) * amp * 0.5 * self.pools
        Rd = _sample(R, self.XX + dx, self.YY + dy)
        sharp = _blur_axis(_blur_axis(Rd, 0.8, 1), 2.0, 0)
        soft = _blur_axis(_blur_axis(Rd, 2.4, 1), 14, 0)
        hot = np.clip(Rd - 0.6, 0, None)
        streak = _blur_axis(_blur_axis(hot, 3.0, 1), 46, 0)                    # the brightest lights smear farthest
        cos = Yr / np.sqrt(self.f ** 2 + Yr ** 2)
        fres = 0.02 + 0.98 * (1 - cos) ** 5
        Fp = (0.45 + 0.55 * fres ** 0.5) * g
        Fd = (0.07 + 0.5 * fres ** 0.7) * g * self.damp
        pud = self.pools
        refl = sharp * (pud * Fp)[..., None] + (soft * 0.8 + streak * 0.9) * ((1 - pud) * Fd)[..., None]
        out = img * (1 - 0.55 * pud * g)[..., None] + refl
        if self.rings is not None:
            env = _gblur(Rd, 3) * 0.9
            out += env * (self.rings * g * (0.1 + 0.9 * pud))[..., None]
        return out

    def _steam(self, img, spill):
        d = self.steam_d
        if d.max() <= 0: return img
        a = (1 - np.exp(-d * 1.3))[..., None]
        light = (self.amb + spill * self.spill_k) * 0.35 + _gblur(img, 30) * 0.6 + _gblur(img, 120) * 0.5
        return img * (1 - a) + light * a

    def _rain(self, img):
        if not self.rain_layers: return img
        Lr = _gblur(img, 6) * 0.9 + _gblur(img, 24) * 0.8 + _gblur(img, 80) * 0.25
        out = img.copy()
        for m, gain in self.rain_layers:
            out += Lr * (m * gain)[..., None]
        return out

    def _film(self, hdr, final):
        H, W = self.H, self.W
        lum = hdr @ LUMA
        bright = np.clip(hdr - 0.8, 0, None)
        bloom = _gblur(bright, 3) * 0.28 + _gblur(bright, 11) * 0.26 + _gblur(bright, 34) * 0.22 + _gblur(bright, 110) * 0.2
        hdr = hdr + bloom * 0.55
        hal = _gblur(np.clip(lum - 1.4, 0, None), 5)
        hdr = hdr + hal[..., None] * np.array([1.0, 0.2, 0.08], np.float32) * 0.22
        x = _aces(hdr * self.exposure)
        out = x ** (1 / 2.2)
        L = out @ LUMA
        out = out + ((1 - L) ** 3)[..., None] * np.array([-0.006, 0.004, 0.018], np.float32) + (L ** 2)[..., None] * np.array([0.02, 0.0, -0.015], np.float32)
        out = out * 0.975 + 0.012 * np.array([0.35, 0.45, 1.0], np.float32)
        if final:
            out = self._aberrate(out)
            gr = np.random.default_rng(len(self.glitch_bands) + 99)
            for (y, h, sh, sp) in self.glitch_bands:
                xa = int(gr.uniform(0.05, 0.3) * W)
                while xa < W * 0.95:                                              # torn segments of different lengths
                    xb = min(W, xa + int(gr.uniform(0.12, 0.3) * W))
                    yy = y + int(gr.integers(-2, 3)); hh = max(2, h + int(gr.integers(-3, 3)))
                    y0, y1 = max(0, yy), min(H, yy + hh)
                    k = int(sh * gr.uniform(0.4, 1.3) * gr.choice([-1, 1]))
                    band = out[y0:y1].copy()
                    for c, o in ((0, k + sp), (1, k), (2, k - sp)):
                        band[..., c] = np.roll(band[..., c], o, axis=1)
                    band[1::2] *= 0.9
                    ramp = np.clip(np.minimum(np.arange(W) - xa, xb - np.arange(W)) / 20.0, 0, 1)[None, :, None]
                    out[y0:y1] = out[y0:y1] * (1 - 0.7 * ramp) + band * 0.7 * ramp
                    xa = xb + int(gr.uniform(0.04, 0.2) * W)
            g = self.rng.normal(0, 1, (H, W)).astype(np.float32)
            g = blur(g, 0.6); g /= g.std() + 1e-6
            L = out @ LUMA
            amp = 0.022 * (0.35 + 2.4 * L * (1 - L))
            out = out + (g * amp)[..., None] + self.rng.normal(0, 0.004, (H, W, 3)).astype(np.float32)
        r = np.hypot((self.XX - W / 2) / (W / 2), (self.YY - H / 2) / (H / 2)) / np.sqrt(2)
        out = out * (1 - 0.42 * r ** 2.2)[..., None]
        return np.clip(out, 0, 1)

    def _aberrate(self, out, k=0.0016):
        """radial chromatic aberration: red magnified a little, blue not at all -> fringes grow toward the edges"""
        H, W = self.H, self.W
        ch = []
        for i, sc in enumerate((1 + 2 * k, 1 + k, 1.0)):
            if sc == 1.0: ch.append(out[..., i]); continue
            a = 1 / sc
            im = Image.fromarray(out[..., i].astype(np.float32), 'F').transform(
                (W, H), Image.AFFINE, (a, 0, W / 2 * (1 - a), 0, a, H / 2 * (1 - a)), resample=Image.BILINEAR)
            ch.append(np.asarray(im))
        return np.stack(ch, -1)

    # ------------------------------------------------------------ output
    def render(self, final=True):
        src = self.emi + self.lsrc
        spill = _gblur(src, 14) * 0.8 + _gblur(src, 55) * 1.1 + _gblur(src, 200) * 1.0
        down = np.zeros_like(src); dy = int(0.12 * self.H); down[dy:] = src[:-dy]
        spill = spill + (_gblur(down, 60) * 1.2 + _gblur(down, 180) * 1.2) * self.ground[..., None]
        lit = self.alb * (self.amb + spill * self.spill_k) + self.emi
        fin = np.isfinite(self.dep)
        T = np.where(fin, np.maximum(np.exp(-np.where(fin, self.dep, 0) / self.fog_m), self.fog_floor), self.sky_t).astype(np.float32)
        scat = _gblur(src, 40) * 0.45 + _gblur(src, 130) * 0.8 + _gblur(src, 320) * 0.6
        rowg = (0.55 + 0.9 * np.exp(-((self.YY - self.vy) / (0.22 * self.H)) ** 2))[..., None]
        fogc = self.fogc * rowg * 0.5 + scat * self.scatter_k
        img = lit * T[..., None] + fogc * (1 - T)[..., None] + self.add
        if self.street_on: img = self._reflect(img, fogc * (1 - np.exp(-300 / self.fog_m)))
        img = self._steam(img, spill)
        img = self._rain(img)
        return self._film(img, final)

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
