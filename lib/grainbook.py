"""grainbook — 颗粒童书 / Grainy Picture Book: sweet mid-century children's-book scenes painted in big flat shapes
with a dry, chalky, grainy brush (numpy + Pillow only).

The look: a full-bleed picture-book page -- no white margin, no vignette -- in a small, saturated palette: cobalt and
ultramarine night skies or a dusty-blue ground, vermilion / tomato red, orange, pine green, cream, peach snow and
black hair. Every thing is one big flat shape, and every shape is laid with a dry, chalky brush: the colour breaks
up into a fine sandy grain (light and dark specks), runs in faint streaks along the stroke, skips the tooth here and
there so the layer underneath shows through, and its edge is a dry, frayed fringe -- shapes meet colour to colour,
with no outline. A few dark crayon strokes for accents (a brow, a window bar, a leash, a smile). Light comes as a
lighter dry-brush scumble on one side; shadows are flat, darker shapes laid over what is there. Faces are simple and
sweet: big round black-and-white eyes or dot eyes, round coral cheeks, a tiny mouth, a button or triangle nose.

Model
  paper       The page starts as one warm cream underlayer, so wherever a later layer skips the tooth, cream shows
              through like the ground of a gouache / crayon painting. Shared textures are made once per page: the
              tooth `T` (fine, rank-equalised, uint8), a grain `G` (pixel noise plus a ~1 px-clustered one,
              z-scored), a mid noise `EN` (edge wander), a big mottle `MOT`, a speck map `SP`, and, made on demand and
              cached per 7.5 degrees, a streak texture for each stroke direction: independent noise on grids whose
              cells are long and thin (about 26 x 3.6, 11 x 1.6 and 80 x 13 px x k), upsampled bicubic so each cell
              becomes a streak, summed, rotated to the stroke angle and kept as uint8 in a square larger than the
              page, so every fill reads it at its own random offset.
  regions     A shape is a `Region`: a float mask the size of its bounding box plus its offset on the page (so a
              small shape costs a small array). Pillow fills polygons into it at 2x and box-averages back. Regions
              combine with `|` (union), `&` (intersection) and `-` (cut away).
  fill        The one paint operation. Inside the region's padded box: the mask is blurred a little and
              thresholded against the streak texture, the tooth and the mid noise, so the edge frays into a crumbly,
              fibrous fringe along the stroke (fingers at the ends of strokes, a wavy edge along them) and the colour
              is a shade darker in that fringe (`rim`); a pressure that falls off toward the edge (`dry`, over
              `dry_px`) is compared with a mix of tooth and streak (`skip`), so the colour skips in specks and thins
              out near the edge; the colour itself moves toward a lighter `hi` on the high streaks and a darker `lo`
              on the low ones (`streak`), with a fine grain and a big soft mottle. Opaque paint:
              new = old + A x (colour - old); `mode='multiply'` lays a shadow over what is there, `mode='screen'` a
              light.
  strokes     `brush()` one dry, tapered stroke (a tube region filled along its own direction); `crayon()` a dark
              crayon accent: a tapered ribbon on a wobbling path whose width swells and thins, its coverage broken by
              the tooth and a pressure that wanders along it; `dots()` fuzzy grainy specks (snow, stars, crumbs).
  layers      `bands()` paints a region in layered colour bands whose borders are wavy, frayed brush edges, each new
              colour also dry-brushed a little way up into the band above (`blend`) -- a sky stepped like a
              painting, never a digital gradient; `mottle()` loose patches of a second colour; `scumble()` a
              dry-brush pass with low pressure that skips along the streaks (highlights, snow on a roof, light snow
              on the ground); `shadow()` a flat multiplied shape; `glow()` two stepped, dry-edged screen discs.
  finish      `finish()` records the finishing (applied in render, so every stage snapshot matches): a fine overall
              grain, sparse light and dark specks (more light ones on dark colour, dark ones on light), and a very
              slight softening.

API (page pixel coordinates; angles in degrees, 0 = to the right, 90 = down; colours are PAINTS names, '#rrggbb' or
     RGB triples; k = min(W, H) / 1000 scales default widths)
  page      GrainBook(W, H, seed, keep_stages, stages_dir); finish(grain, speckle, soft) -- before the first mark;
            paper(tone)
  regions   poly(pts, smooth) / ellipse(cx, cy, rx, ry, rot) / blob(cx, cy, rx, ry, rough, rot, seed) /
            rect(x0, y0, x1, y1) / tube(path, w0, w1, taper) / below(xs, ys) / above(xs, ys) / full();
            r1 | r2, r1 & r2, r1 - r2; wavy(x0, x1, y, amp, period, seed, slope) -> (xs, ys)
  paint     fill(region, colour, angle, streak, grain, mottle, pressure, dry, edge, soft, hi, lo, alpha, clip,
            avoid, mode, seed, dry_px, rim, skip); scumble(region, colour, angle, cover, ...);
            shadow(region, colour, depth, angle); glow(region, colour, strength); bands(region, colours, ys,
            angle, wave, period, blend, ...); mottle(region, colour, scale, cover, angle, ...);
            brush(path, width, colour, taper, ...); crayon(path, width, colour, pressure, taper, wobble);
            dots(pts, r, colour, ...)
  faces     face(cx, cy, r, turn, eyes, look, skin, cheeks, mouth, nose, brows, ears, eye_size) -> anchors
            (eyes 'big' / 'dot' / 'closed'); eye_big(cx, cy, w, h, look, highlight, lid) / eye_dot(cx, cy, r) /
            cheek(cx, cy, r) / nose(cx, cy, size, kind) ('button' 'tri' 'line' 'dot') / mouth(cx, cy, w, kind)
            ('smile' 'lips' 'o' 'open') / brow(cx, cy, w, tilt); hair(cx, cy, r, style, colour, turn, layer,
            length) ('bob' 'long' 'short' 'bun'; layer 'back' / 'front'); beanie(cx, cy, r, colour, band, pompom,
            turn)
  figures   limb(path, w0, w1, colour, angle); mitten(x, y, r, colour, angle, thumb); boot(x, y, w, colour,
            facing); child(x, y, h, facing, pose, outfit, hooks, **joints) -> joints (pose 'stand' / 'walk' /
            'sit')
  props     house(x, y, w, h, ...) -> anchors; pine(x, y, h, w, ...); fir_far(x, y, h, w, colour);
            round_tree(x, y, h, w, ...); bush(x, y, w, h, colour); shrub(x, y, h, w, ...); cup(x, y, w, ...);
            parcel(x, y, w, h, ...); bag(x, y, w, h, colour); potted(x, y, h, ...); reeds(x, y, h, n, ...);
            tuft(x, y, w, h, ...); lamp(x, y, h, ...); dog(x, y, s, facing, ...) -> anchors;
            duck(x, y, s, facing, ...); fence(x0, x1, y, h, ...)
  sky       snow(x0, y0, x1, y1, n, r, ..., avoid); stars(x0, y0, x1, y1, n, ...); moon(x, y, r, colour, halo,
            crescent); smoke(x, y, h, ...); wisp(x, y, h, ...); ripples(x, y, w, n, ...); footprints(pts, size, ...)
  output    render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 92, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from grainbook import GrainBook
    g = GrainBook(1200, 1500, seed=1); g.finish(); g.paper()
    g.bands(g.full(), ['cobalt_deep', 'cobalt', 'cobalt_bright'], [500, 900], angle=-8)
    g.fill(g.below(*g.wavy(0, 1200, 1100, 30, 900)), 'snow', angle=-5)
    g.house(700, 1150, 260, 220)
    g.child(420, 1300, 520, facing=1, pose='walk', outfit=dict(coat='vermilion', hat='cream'))
    g.snow(0, 0, 1200, 1400, 160)
    g.save('page.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, spline, smoothstep, fbm1d

PAINTS = {
    # the cream underlayer and lights
    'paper': '#f1e2c6', 'cream': '#fbf0d6', 'white': '#fff8ea', 'cream_dark': '#e9d4ae',
    # blues: night skies, dusty grounds, water
    'navy': '#0a2a60', 'cobalt_deep': '#063f8c', 'cobalt': '#0763bd', 'cobalt_bright': '#0d82ec',
    'ultramarine': '#2450c4', 'sky_pale': '#7cb9ee', 'dusty': '#4c8db0', 'dusty_light': '#7cb4cc',
    'dusty_dark': '#336f90', 'teal': '#0f6c8a', 'ice': '#bcdcf2',
    # reds and oranges
    'vermilion': '#ec3415', 'tomato': '#f7552f', 'red_deep': '#bc2814', 'brick': '#922814', 'orange': '#fc7a28',
    'orange_light': '#fc9c58', 'apricot': '#f9ae74',
    # greens
    'pine': '#0f3a30', 'pine_mid': '#1f5a3e', 'green': '#457a3a', 'moss': '#6a9140', 'olive': '#9aa83f',
    'sage': '#8fae8a',
    # yellows
    'mustard': '#eaaa38', 'window': '#f8cb50', 'lamp': '#ffe39a', 'gold': '#d99a36',
    # snow at night (peach), its shade
    'snow': '#f7b8a0', 'snow_light': '#fcd6c3', 'snow_shade': '#df9796', 'snow_blue': '#a6b6dc',
    # skin, cheeks, features
    'skin': '#fac7a6', 'skin_shade': '#efa98a', 'cheek': '#f4836c', 'nose': '#f06a4c', 'lip': '#e4553c',
    # dark and browns
    'hair': '#16110e', 'black': '#141110', 'ink': '#241812', 'brown': '#5b3522', 'brown_light': '#8c5a37',
    'wood': '#a8683c', 'wood_dark': '#6e3f24', 'kraft': '#d2a56c', 'coffee': '#4a2a17', 'shadow': '#c6a6b8', 'shadow_blue': '#8f9cc8',
}


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    return hexc(a) * (1 - t) + hexc(b) * t


def _resample(P, step):
    P = np.asarray(P, np.float32)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-3: return P[:1]
    s = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)


def _smooth(path, per=10):
    P = np.asarray(path, np.float32)
    return spline(P, per) if len(P) > 2 else _resample(P, 3)


def _rot(pts, cx, cy, deg):
    a = np.deg2rad(deg); c, s = np.cos(a), np.sin(a)
    P = np.asarray(pts, np.float32) - (cx, cy)
    return np.stack([P[:, 0] * c - P[:, 1] * s + cx, P[:, 0] * s + P[:, 1] * c + cy], 1)


def _ncdf(z):
    """a normal-ish noise -> roughly uniform 0..1"""
    return 0.5 * (1 + np.tanh(0.7978 * (z + 0.0447 * z * z * z)))


class Region:
    """a float mask the size of its bounding box, at offset (y0, x0) on the page"""
    __slots__ = ('y0', 'x0', 'a')

    def __init__(self, y0, x0, a):
        self.y0, self.x0, self.a = int(y0), int(x0), a.astype(np.float32, copy=False)

    @property
    def box(self):
        return self.y0, self.x0, self.y0 + self.a.shape[0], self.x0 + self.a.shape[1]

    def crop(self, y0, x0, y1, x1):
        out = np.zeros((y1 - y0, x1 - x0), np.float32)
        a0, b0, a1, b1 = self.box
        iy0, ix0, iy1, ix1 = max(y0, a0), max(x0, b0), min(y1, a1), min(x1, b1)
        if iy1 > iy0 and ix1 > ix0:
            out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = self.a[iy0 - a0:iy1 - a0, ix0 - b0:ix1 - b0]
        return out

    def _pair(self, o, inter=False):
        a, b = self.box, o.box
        if inter: box = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
        else: box = (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))
        if box[2] <= box[0] or box[3] <= box[1]: box = (a[0], a[1], a[0] + 1, a[1] + 1)
        return box, self.crop(*box), o.crop(*box)

    def __or__(self, o):
        box, p, q = self._pair(o)
        return Region(box[0], box[1], np.maximum(p, q))

    def __and__(self, o):
        box, p, q = self._pair(o, True)
        return Region(box[0], box[1], np.minimum(p, q))

    def __sub__(self, o):
        p = self.a * (1 - o.crop(*self.box))
        return Region(self.y0, self.x0, p)

    def scaled(self, f):
        return Region(self.y0, self.x0, np.clip(self.a * f, 0, 1))

    def empty(self):
        return not (self.a > 0.02).any()


class GrainBook:
    PAINTS = PAINTS

    def __init__(self, W=1600, H=2000, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('page larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.k = min(W, H) / 1000
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = hexc('paper')
        self.fin = None
        self.T = None
        self._streaks = {}
        self.L = int(np.ceil(np.hypot(W, H))) + 16          # side of the streak squares

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== textures
    def _textures(self):
        H, W, k = self.H, self.W, self.k
        r = np.random.default_rng(self.seed * 7919 + 13)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        t = 0.8 * z(blur(r.standard_normal((H, W)).astype(np.float32), 0.65)) + \
            0.6 * z(noise2d(H, W, 2.6 * k, 2, int(r.integers(1 << 30))))
        self.T = np.round(_ncdf(z(t)) * 255).astype(np.uint8)
        g = r.standard_normal((H, W)).astype(np.float32)
        g2 = r.standard_normal((H, W)).astype(np.float32)
        self.G = z(0.75 * z(g) + 0.5 * z(blur(g2, 0.7 * k))).astype(np.float32)
        del g2
        self.EN = noise2d(H, W, 9.0 * k, 3, int(r.integers(1 << 30))).astype(np.float32)
        self.MOT = noise2d(H, W, 170.0 * k, 3, int(r.integers(1 << 30))).astype(np.float32)
        self.SP = r.random((H, W)).astype(np.float32)
        del t, g

    def _need(self):
        if self.T is None: self._textures()

    def _streak(self, angle):
        """the streak square for a stroke direction (cached per 7.5 degrees), uint8, L x L"""
        key = int(round((angle % 180) / 7.5)) % 24
        if key in self._streaks: return self._streaks[key]
        L, k = self.L, self.k
        L2 = int(L * 1.42) + 8
        r = np.random.default_rng(self.seed * 101 + key * 7 + 3)
        acc = np.zeros((L2, L2), np.float32)
        for ln, wd, amp in ((26 * k, 3.6 * k, 1.0), (11 * k, 1.6 * k, 0.6), (80 * k, 13 * k, 0.75)):
            gh, gw = int(L2 / max(wd, 1.0)) + 3, int(L2 / ln) + 3
            g = Image.fromarray(r.standard_normal((gh, gw)).astype(np.float32))
            acc += amp * np.asarray(g.resize((L2, L2), Image.BICUBIC), np.float32)
        acc = (acc - acc.mean()) / (acc.std() + 1e-6)
        im = Image.fromarray(acc).rotate(-key * 7.5, resample=Image.BILINEAR)
        o = (L2 - L) // 2
        sq = np.asarray(im, np.float32)[o:o + L, o:o + L]
        sq = (sq - sq.mean()) / (sq.std() + 1e-6)
        out = np.round(_ncdf(sq) * 255).astype(np.uint8)
        self._streaks[key] = out
        return out

    def _streak_at(self, angle, y0, x0, y1, x1, r):
        S = self._streak(angle)
        oy = int(r.integers(0, self.L - self.H + 1)); ox = int(r.integers(0, self.L - self.W + 1))
        return S[y0 + oy:y1 + oy, x0 + ox:x1 + ox].astype(np.float32) / 255

    # ================================================================== page
    def paper(self, tone='paper', angle=-80.0, streak=0.5):
        """the warm underlayer the whole page starts from (it shows wherever a later layer skips)"""
        self._need()
        R = self.full()
        self.C[:] = hexc(tone)
        self.fill(R, tone, angle=angle, streak=streak, pressure=1.2, dry=0, edge=0, mottle=0.25,
                  hi=mix(tone, 'white', 0.35), lo=mix(tone, 'cream_dark', 0.9))
        return self

    # ================================================================== regions
    def full(self):
        return Region(0, 0, np.ones((self.H, self.W), np.float32))

    def poly(self, pts, smooth=False, per=10):
        P = np.asarray(pts, np.float32)
        if smooth: P = spline(np.vstack([P, P[:1]]), per)[:-1]
        ss = 2
        x0 = int(np.floor(P[:, 0].min())) - 2; x1 = int(np.ceil(P[:, 0].max())) + 3
        y0 = int(np.floor(P[:, 1].min())) - 2; y1 = int(np.ceil(P[:, 1].max())) + 3
        x0, y0 = max(x0, -4), max(y0, -4)
        x1, y1 = min(x1, self.W + 4), min(y1, self.H + 4)
        if x1 <= x0 or y1 <= y0: return Region(0, 0, np.zeros((1, 1), np.float32))
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P], fill=255)
        a = np.asarray(im, np.float32).reshape(y1 - y0, ss, x1 - x0, ss).mean((1, 3)) / 255
        return Region(y0, x0, a)

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0, n=None):
        ry = rx if ry is None else ry
        n = n or int(np.clip(max(rx, ry) * 0.6, 24, 240))
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        P = np.stack([cx + rx * np.cos(t), cy + ry * np.sin(t)], 1)
        return self.poly(_rot(P, cx, cy, rot) if rot else P)

    def blob(self, cx, cy, rx, ry=None, rough=0.08, rot=0.0, seed=None):
        ry = rx if ry is None else ry
        r = self._r(seed)
        n = int(np.clip(max(rx, ry) * 0.6, 40, 260))
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        wob = 1 + rough * fbm1d(n, n / 5, 4, int(r.integers(1 << 30)))
        P = np.stack([cx + rx * wob * np.cos(t), cy + ry * wob * np.sin(t)], 1)
        return self.poly(_rot(P, cx, cy, rot) if rot else P)

    def rect(self, x0, y0, x1, y1):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    @staticmethod
    def tube_pts(path, w0, w1=None, taper=(0.0, 0.0), per=10):
        """outline of a ribbon along a path, width w0 -> w1, tapering to a point over the first / last fraction"""
        P = _smooth(path, per)
        P = _resample(P, 2.0)
        n = len(P)
        if n < 2: P = np.vstack([P, P + 0.5]); n = 2
        w1 = w0 if w1 is None else w1
        t = np.linspace(0, 1, n)
        w = (w0 + (w1 - w0) * t) / 2
        if taper[0] > 0: w = w * np.clip(np.sqrt(np.clip(t / taper[0], 0, 1)), 0.08, 1)
        if taper[1] > 0: w = w * np.clip(np.sqrt(np.clip((1 - t) / taper[1], 0, 1)), 0.08, 1)
        d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        return np.vstack([P + nrm * w[:, None], (P - nrm * w[:, None])[::-1]])

    def tube(self, path, w0, w1=None, taper=(0.0, 0.0)):
        return self.poly(self.tube_pts(path, w0, w1, taper))

    def below(self, xs, ys):
        """everything under a curve (xs ascending) down to the bottom of the page"""
        P = np.stack([np.asarray(xs, np.float32), np.asarray(ys, np.float32)], 1)
        return self.poly(np.vstack([P, [(P[-1, 0], self.H + 4), (P[0, 0], self.H + 4)]]))

    def above(self, xs, ys):
        P = np.stack([np.asarray(xs, np.float32), np.asarray(ys, np.float32)], 1)
        return self.poly(np.vstack([P, [(P[-1, 0], -4), (P[0, 0], -4)]]))

    def wavy(self, x0, x1, y, amp=20.0, period=600.0, seed=None, slope=0.0, n=None):
        """a wavy horizon: xs, ys from x0 to x1 around y (amp px, wavelength ~period px), optional slope (px per px)"""
        r = self._r(seed)
        n = n or max(8, int((x1 - x0) / 6))
        xs = np.linspace(x0, x1, n)
        ys = y + amp * fbm1d(n, max(2.0, n * period / max(x1 - x0, 1) / 2), 3, int(r.integers(1 << 30))) + \
            slope * (xs - (x0 + x1) / 2)
        return xs, ys

    def _region(self, r):
        if isinstance(r, Region): return r
        if isinstance(r, np.ndarray) and r.shape == (self.H, self.W): return Region(0, 0, r)
        return self.poly(r)

    # ================================================================== paint
    def fill(self, region, colour, angle=0.0, streak=0.28, grain=1.0, mottle=0.12, pressure=1.0, dry=0.3,
             edge=1.0, soft=1.0, hi=None, lo=None, alpha=1.0, clip=None, avoid=None, mode='paint', seed=None,
             dry_px=None, rim=0.07, skip=0.5):
        """lay one colour into a region with a dry, chalky brush (see the module doc)"""
        self._need()
        R = self._region(region)
        if R.empty(): return
        k = self.k
        r = self._r(seed)
        dpx = (9.0 * k) if dry_px is None else dry_px
        pad = int(np.ceil(max(3 * dpx, 8 * k * max(edge, 0.3)) + 4))
        Y0, X0, Y1, X1 = R.box
        y0, x0 = max(0, Y0 - pad), max(0, X0 - pad)
        y1, x1 = min(self.H, Y1 + pad), min(self.W, X1 + pad)
        if y1 <= y0 or x1 <= x0: return
        m = R.crop(y0, x0, y1, x1)
        S = self._streak_at(angle, y0, x0, y1, x1, r)
        G = self.G[y0:y1, x0:x1]
        T = self.T[y0:y1, x0:x1].astype(np.float32) / 255
        EN = self.EN[y0:y1, x0:x1]
        if edge > 0:
            ss = blur(m, 2.2 * k * soft) if soft > 0 else m
            n = 0.42 * (S - 0.5) + 0.6 * (T - 0.5) + 0.35 * (EN - 0.5)
            me = smoothstep(0.35, 0.65, ss + 0.52 * edge * n)
            band = smoothstep(0.25, 0.5, ss) * (1 - smoothstep(0.62, 0.9, ss))   # the edge zone (for the rim)
        else:
            me = m; band = None
        if dry > 0:
            deep = blur(m, dpx)
            p = pressure - dry * (1 - smoothstep(0.5, 0.92, deep))
        else:
            p = pressure
        tex = (1 - skip) * T + skip * S
        cov = smoothstep(tex - 0.07, tex + 0.07, p + 0.03)
        A = alpha * me * cov
        if clip is not None: A *= self._region(clip).crop(y0, x0, y1, x1)
        if avoid is not None: A *= 1 - self._region(avoid).crop(y0, x0, y1, x1)
        if not (A > 0.003).any(): return
        base = hexc(colour)
        hi = mix(base, 'white', 0.16) if hi is None else hexc(hi)
        lo = base * 0.88 if lo is None else hexc(lo)
        t = np.clip((S - 0.5) * 2.2 * streak, -1, 1)[..., None]
        col = base + np.maximum(t, 0) * (hi - base) + np.maximum(-t, 0) * (lo - base)
        v = 1 + 0.042 * grain * G + mottle * 0.3 * (self.MOT[y0:y1, x0:x1] - 0.5)
        if rim and band is not None and mode == 'paint': v = v - rim * band
        col = col * v[..., None]
        C = self.C[y0:y1, x0:x1]
        A3 = A[..., None]
        if mode == 'paint': C += A3 * (col - C)
        elif mode == 'multiply': C *= 1 - A3 * (1 - np.clip(col, 0, 1))
        elif mode == 'screen': C += A3 * np.clip(col, 0, 1) * (1 - C)
        else: raise ValueError(mode)
        np.clip(C, 0, 1.2, out=C)

    def scumble(self, region, colour, angle=0.0, cover=0.45, streak=0.5, **kw):
        """a dry-brush pass: colour only on the high tooth and streaks (a highlight, snow on a roof)"""
        kw.setdefault('dry', 0.15); kw.setdefault('edge', 1.3); kw.setdefault('skip', 0.8)
        self.fill(region, colour, angle=angle, pressure=cover, streak=streak, **kw)

    def shadow(self, region, colour='shadow', depth=1.0, angle=0.0, **kw):
        """a flat cast shadow laid over what is there (multiplied)"""
        kw.setdefault('dry', 0.1); kw.setdefault('streak', 0.25); kw.setdefault('mottle', 0.05)
        c = 1 - depth * (1 - hexc(colour))
        self.fill(region, c, angle=angle, mode='multiply', hi=mix(c, 'white', 0.25), lo=c * 0.95, **kw)

    def glow(self, region, colour='lamp', strength=0.5, angle=0.0, **kw):
        """a grainy screen-blended light (a lit window's spill, a lamp's halo): a faint outer step and a brighter
        inner one, both with dry, broken edges -- a painted halo, not a smooth radial gradient"""
        R = self._region(region)
        kw.setdefault('dry', 0.6); kw.setdefault('edge', 1.8); kw.setdefault('soft', 2.4)
        kw.setdefault('pressure', 0.9); kw.setdefault('skip', 0.7)
        y0, x0, y1, x1 = R.box
        inner = Region(y0, x0, smoothstep(0.35, 0.65, blur(R.a, 0.22 * min(y1 - y0, x1 - x0))))
        self.fill(R, hexc(colour) * strength * 0.45, angle=angle, mode='screen', **kw)
        self.fill(inner, hexc(colour) * strength * 0.6, angle=angle, mode='screen', **kw)

    def bands(self, region, colours, ys, angle=0.0, wave=None, period=None, blend=None, seed=None, **kw):
        """colours[0] over the whole region, then colours[i + 1] below the wavy border ys[i] (a stepped sky); each
        new colour is also dry-brushed `blend` px up into the band above it, so a border breaks up like a painted
        one instead of a cut"""
        R = self._region(region)
        r = self._r(seed)
        wave = 26 * self.k if wave is None else wave
        period = 500 * self.k if period is None else period
        blend = 40 * self.k if blend is None else blend
        self.fill(R, colours[0], angle=angle, seed=int(r.integers(1 << 30)), **kw)
        for c, y in zip(colours[1:], ys):
            xs, yy = self.wavy(-20, self.W + 20, y, wave, period, int(r.integers(1 << 30)))
            if blend > 0:
                strip = R & (self.below(xs, yy - blend) - self.below(xs, yy + 4))
                self.scumble(strip, c, angle=angle, cover=0.4, alpha=0.9, seed=int(r.integers(1 << 30)))
            self.fill(R & self.below(xs, yy), c, angle=angle, seed=int(r.integers(1 << 30)), **kw)

    def mottle(self, region, colour, scale=None, cover=0.35, angle=0.0, seed=None, **kw):
        """loose patches of a second colour over a region (the uneven body of a painted sky or field)"""
        R = self._region(region)
        r = self._r(seed)
        scale = 120 * self.k if scale is None else scale
        y0, x0, y1, x1 = R.box
        n = noise2d(y1 - y0, x1 - x0, scale, 3, int(r.integers(1 << 30)))
        q = np.quantile(n, 1 - cover)
        patch = Region(y0, x0, R.a * smoothstep(q - 0.05, q + 0.05, n))
        kw.setdefault('dry', 0.55); kw.setdefault('edge', 1.8); kw.setdefault('soft', 2.5)
        self.fill(patch, colour, angle=angle, seed=int(r.integers(1 << 30)), **kw)

    def brush(self, path, width, colour, taper=(0.12, 0.35), w1=None, angle=None, **kw):
        """one dry, tapered brush stroke along a path"""
        P = np.asarray(path, np.float32)
        if angle is None:
            d = P[-1] - P[0]
            angle = float(np.degrees(np.arctan2(d[1], d[0])))
        kw.setdefault('dry', 0.25); kw.setdefault('dry_px', max(2.0, width * 0.35)); kw.setdefault('soft', 0.7)
        self.fill(self.tube(P, width, w1, taper), colour, angle=angle, **kw)

    def crayon(self, path, width=None, colour='ink', pressure=0.85, taper=(0.15, 0.25), wobble=1.0, alpha=1.0,
               w1=None, seed=None):
        """a dark crayon accent: a tapered ribbon on a wobbling path, broken by the tooth"""
        self._need()
        k = self.k
        r = self._r(seed)
        width = 5 * k if width is None else width
        P = _resample(_smooth(path), 2.0)
        if len(P) < 2: return
        n = len(P)
        if wobble:
            d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
            nrm = np.stack([-d[:, 1], d[:, 0]], 1)
            P = P + nrm * (wobble * 0.9 * k * fbm1d(n, max(4, n / 5), 3, int(r.integers(1 << 30))))[:, None]
        wv = 1 + 0.18 * fbm1d(n, max(4, n / 4), 2, int(r.integers(1 << 30)))
        d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        t = np.linspace(0, 1, n)
        w = (width + ((width if w1 is None else w1) - width) * t) / 2 * wv
        if taper[0] > 0: w = w * np.clip(np.sqrt(np.clip(t / taper[0], 0, 1)), 0.1, 1)
        if taper[1] > 0: w = w * np.clip(np.sqrt(np.clip((1 - t) / taper[1], 0, 1)), 0.1, 1)
        pts = np.vstack([P + nrm * w[:, None], (P - nrm * w[:, None])[::-1]])
        R = self.poly(pts)
        y0, x0, y1, x1 = R.box
        y0, x0, y1, x1 = max(0, y0), max(0, x0), min(self.H, y1), min(self.W, x1)
        if y1 <= y0 or x1 <= x0: return
        m = blur(R.crop(y0, x0, y1, x1), 0.6 * k)
        T = self.T[y0:y1, x0:x1].astype(np.float32) / 255
        G = self.G[y0:y1, x0:x1]
        EN = self.EN[y0:y1, x0:x1]
        me = smoothstep(0.32, 0.62, m + 0.16 * (EN - 0.5) + 0.04 * G)
        p = pressure + 0.25 * (EN - 0.5)
        cov = smoothstep(T - 0.12, T + 0.12, p + 0.08)
        A = (alpha * me * cov)[..., None]
        col = hexc(colour) * (1 + 0.06 * G)[..., None]
        C = self.C[y0:y1, x0:x1]
        C += A * (col - C)

    def dots(self, pts, r, colour='cream', alpha=1.0, seed=None, **kw):
        """fuzzy, grainy specks at points (snow, stars, crumbs); r a number or one per point"""
        pts = np.asarray(pts, np.float32).reshape(-1, 2)
        if not len(pts): return
        rr = np.broadcast_to(np.asarray(r, np.float32), (len(pts),))
        x0 = int(np.floor((pts[:, 0] - rr).min())) - 3; x1 = int(np.ceil((pts[:, 0] + rr).max())) + 4
        y0 = int(np.floor((pts[:, 1] - rr).min())) - 3; y1 = int(np.ceil((pts[:, 1] + rr).max())) + 4
        ss = 2
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        dr = ImageDraw.Draw(im)
        q = self._r(seed)
        for (x, y), a in zip(pts, rr):
            ax, ay = a * (1 + 0.15 * q.standard_normal()), a * (1 + 0.15 * q.standard_normal())
            dr.ellipse([((x - ax) - x0) * ss, ((y - ay) - y0) * ss, ((x + ax) - x0) * ss, ((y + ay) - y0) * ss],
                       fill=255)
        a = np.asarray(im, np.float32).reshape(y1 - y0, ss, x1 - x0, ss).mean((1, 3)) / 255
        kw.setdefault('dry', 0.0); kw.setdefault('edge', 0.6); kw.setdefault('soft', 0.7)
        kw.setdefault('streak', 0.15); kw.setdefault('mottle', 0.0)
        self.fill(Region(y0, x0, a), colour, alpha=alpha, seed=int(q.integers(1 << 30)), **kw)

    # ================================================================== faces
    def eye_big(self, cx, cy, w, h=None, look=(0.0, 0.0), highlight=True, lid='ink', iris='black', white='white',
                lower=False, seed=None):
        """a big round black-and-white eye: a white almond, a big dark iris tucked under the upper lid, a catchlight,
        a crayon upper lid"""
        k = self.k
        h = 0.8 * w if h is None else h
        r = self._r(seed)
        t = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        top = np.sin(t) < 0
        ry = np.where(top, h * 0.47, h * 0.53)
        P = np.stack([cx + w / 2 * np.cos(t), cy + ry * np.sin(t) * np.where(top, 0.92, 1.0)], 1)
        sclera = self.poly(P)
        self.fill(sclera, white, angle=0, streak=0.12, dry=0, edge=0.35, soft=0.5, mottle=0, seed=int(r.integers(1 << 30)))
        ir = 0.25 * w
        ix, iy = cx + look[0] * w * 0.22, cy - h * 0.04 + look[1] * h * 0.16
        self.fill(self.ellipse(ix, iy, ir, ir * 1.04), iris, angle=90, streak=0.15, dry=0, edge=0.35, soft=0.5,
                  mottle=0, clip=sclera, seed=int(r.integers(1 << 30)))
        if highlight:
            self.fill(self.ellipse(ix - ir * 0.33, iy - ir * 0.36, ir * 0.24), 'white', dry=0, edge=0.25, soft=0.4,
                      streak=0, mottle=0, seed=int(r.integers(1 << 30)))
        if lid:
            a = np.linspace(np.pi * 1.04, np.pi * 1.96, 16)
            path = np.stack([cx + w / 2 * 1.04 * np.cos(a), cy + h * 0.47 * np.sin(a) * 0.95], 1)
            self.crayon(path, max(2.2 * k, 0.085 * w), lid, taper=(0.25, 0.12), wobble=0.4, seed=int(r.integers(1 << 30)))
        if lower:
            a = np.linspace(np.pi * 0.25, np.pi * 0.75, 10)
            path = np.stack([cx + w / 2 * np.cos(a), cy + h * 0.55 * np.sin(a)], 1)
            self.crayon(path, max(1.4 * k, 0.03 * w), lid, taper=(0.4, 0.4), alpha=0.5, wobble=0.3)

    def eye_dot(self, cx, cy, r, colour='black', highlight=True):
        self.fill(self.ellipse(cx, cy, r * 0.86, r), colour, angle=90, streak=0.1, dry=0, edge=0.3, soft=0.4, mottle=0)
        if highlight and r > 4 * self.k:
            self.fill(self.ellipse(cx - r * 0.3, cy - r * 0.38, r * 0.26), 'white', dry=0, edge=0.2, soft=0.3,
                      streak=0, mottle=0)

    def cheek(self, cx, cy, r, colour='cheek', alpha=0.85):
        self.fill(self.ellipse(cx, cy, r, r * 0.9), colour, angle=-30, streak=0.25, dry=0.25, dry_px=r * 0.3,
                  edge=1.0, soft=1.6, mottle=0, alpha=alpha)

    def nose(self, cx, cy, size, kind='button', colour='nose', facing=0.0):
        """'button' a small oval, 'tri' an upward triangle (a carrot nose), 'line' a crayon line with a flick, 'dot'"""
        if kind == 'button':
            self.fill(self.ellipse(cx, cy, size * 0.55, size * 0.42), colour, dry=0, edge=0.5, soft=0.6, streak=0.15)
        elif kind == 'dot':
            self.fill(self.ellipse(cx, cy, size * 0.3), colour, dry=0, edge=0.4, soft=0.5, streak=0)
        elif kind == 'tri':
            self.fill(self.poly([(cx - size * 0.42, cy + size * 0.5), (cx + size * 0.42, cy + size * 0.5),
                                 (cx + facing * size * 0.15, cy - size * 1.1)], smooth=False), colour, angle=90,
                      dry=0.1, dry_px=size * 0.2, edge=0.6, soft=0.6, streak=0.3)
        elif kind == 'line':
            f = 1 if facing >= 0 else -1
            self.crayon([(cx, cy - size * 1.6), (cx + f * size * 0.1, cy - size * 0.5), (cx + f * size * 0.15, cy),
                         (cx - f * size * 0.25, cy + size * 0.2)], size * 0.2, colour, taper=(0.3, 0.2))

    def mouth(self, cx, cy, w, kind='smile', colour='ink', lip='lip'):
        """'smile' a small crayon arc, 'lips' a small coral mouth, 'o' a little round open mouth, 'open' a happy
        open mouth"""
        k = self.k
        if kind == 'smile':
            a = np.linspace(0.15 * np.pi, 0.85 * np.pi, 12)
            self.crayon(np.stack([cx + w / 2 * np.cos(a), cy - w * 0.12 + w * 0.3 * np.sin(a)], 1),
                        max(2.0 * k, 0.11 * w), colour, taper=(0.3, 0.3), wobble=0.3)
        elif kind == 'lips':
            P = [(cx - w / 2, cy), (cx - w * 0.2, cy - w * 0.16), (cx, cy - w * 0.1), (cx + w * 0.2, cy - w * 0.16),
                 (cx + w / 2, cy), (cx + w * 0.15, cy + w * 0.2), (cx - w * 0.15, cy + w * 0.2)]
            self.fill(self.poly(P, smooth=True), lip, dry=0, edge=0.5, soft=0.5, streak=0.2)
        elif kind == 'o':
            self.fill(self.ellipse(cx, cy, w * 0.28, w * 0.34), 'brick', dry=0, edge=0.4, soft=0.5, streak=0.1)
        elif kind == 'open':
            a = np.linspace(0, np.pi, 16)
            P = np.vstack([[(cx - w / 2, cy - w * 0.05), (cx + w / 2, cy - w * 0.05)],
                           np.stack([cx + w / 2 * np.cos(a), cy - w * 0.05 + w * 0.45 * np.sin(a)], 1)[1:-1]])
            m = self.poly(P)
            self.fill(m, 'brick', dry=0, edge=0.4, soft=0.5, streak=0.1)
            self.fill(self.ellipse(cx, cy + w * 0.28, w * 0.24, w * 0.12), 'tomato', clip=m, dry=0, edge=0.3,
                      soft=0.4, streak=0)

    def brow(self, cx, cy, w, tilt=0.0, colour='brown', width=None):
        k = self.k
        a = np.deg2rad(tilt)
        d = np.array([np.cos(a), np.sin(a)]) * w / 2
        mid = np.array([cx, cy - w * 0.08])
        self.crayon([np.array([cx, cy]) - d, mid, np.array([cx, cy]) + d], width or max(2.5 * k, 0.16 * w), colour,
                    taper=(0.2, 0.35), wobble=0.4)

    def face(self, cx, cy, r, turn=0.0, eyes='dot', look=(0.0, 0.0), skin='skin', cheeks=True, mouth='smile',
             nose='button', brows=False, ears=True, eye_size=1.0, seed=None):
        """a sweet face (head radius r; turn -1..1 swings the features left / right). Returns anchors: chin, top,
        eyes, nose, mouth, ears"""
        k = self.k
        rr = self._r(seed)
        fx = cx + turn * 0.26 * r
        out = dict(top=(cx, cy - r * 1.04), chin=(fx, cy + r * 1.0))
        if ears:
            for side in (-1, 1):
                if turn * side > 0.35: continue
                ex = cx + side * r * (0.96 - 0.22 * max(0.0, -turn * side))
                self.fill(self.ellipse(ex, cy + 0.12 * r, 0.2 * r, 0.24 * r), skin, dry=0, edge=0.6, soft=0.7,
                          streak=0.15, lo=hexc(skin) * 0.95)
                self.fill(self.ellipse(ex + side * 0.03 * r, cy + 0.12 * r, 0.09 * r, 0.12 * r), 'skin_shade',
                          dry=0, edge=0.5, soft=0.6, streak=0, alpha=0.7)
        t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
        sx = np.where(np.sin(t) > 0, 1.0 - 0.06 * np.sin(t) ** 2, 1.0)
        P = np.stack([cx + r * np.cos(t) * sx, cy + r * 1.02 * np.sin(t)], 1)
        head = self.poly(P)
        self.fill(head, skin, angle=80, streak=0.22, dry=0.15, dry_px=r * 0.15, edge=0.8, soft=0.9,
                  seed=int(rr.integers(1 << 30)))
        out['head'] = head
        sp = 0.37 * r * (1 - 0.22 * abs(turn))
        ey = cy + 0.06 * r
        E = []
        for side in (-1, 1):
            far = turn * side < -0.1
            sc = (1 - 0.18 * abs(turn)) if far else 1.0
            ex = fx + side * sp * (0.85 if far else 1.0)
            E.append((ex, ey))
            if eyes == 'big':
                self.eye_big(ex, ey, 0.36 * r * eye_size * sc, 0.3 * r * eye_size, look=look,
                             seed=int(rr.integers(1 << 30)))
            elif eyes == 'dot':
                self.eye_dot(ex + look[0] * 0.03 * r, ey + look[1] * 0.03 * r, 0.085 * r * eye_size * sc)
            elif eyes == 'closed':
                a = np.linspace(0.1 * np.pi, 0.9 * np.pi, 10)
                self.crayon(np.stack([ex + 0.11 * r * np.cos(a), ey - 0.02 * r + 0.07 * r * np.sin(a)], 1),
                            max(2.0 * k, 0.035 * r), 'ink', taper=(0.3, 0.3), wobble=0.2)
            if brows:
                self.brow(ex, ey - (0.3 if eyes == 'big' else 0.2) * r, 0.24 * r * sc, tilt=-side * 6,
                          colour='brown')
        out['eyes'] = E
        if cheeks:
            for side in (-1, 1):
                far = turn * side < -0.1
                ccx = fx + side * (0.56 * r if not far else 0.46 * r)
                self.cheek(ccx, cy + 0.36 * r, 0.17 * r * (0.85 if far else 1.0), alpha=0.8)
        ny = cy + 0.27 * r
        nx = fx + turn * 0.1 * r
        if nose: self.nose(nx, ny, 0.12 * r, nose, facing=turn)
        out['nose'] = (nx, ny)
        my = cy + 0.5 * r
        if mouth: self.mouth(fx + turn * 0.05 * r, my, 0.2 * r, mouth)
        out['mouth'] = (fx, my)
        return out

    def hair(self, cx, cy, r, style='bob', colour='hair', turn=0.0, layer='back', length=1.0, strands=True,
             seed=None):
        """hair as one big grainy shape behind the head ('back') and a fringe / side locks in front ('front').
        styles: 'bob', 'long' (middle part, past the shoulders), 'short', 'bun'"""
        k = self.k
        rr = self._r(seed)
        sd = int(rr.integers(1 << 30))
        kw = dict(angle=90, streak=0.3, dry=0.2, dry_px=r * 0.1, edge=1.2, soft=1.0, mottle=0.1)
        if layer == 'back':
            if style in ('bob', 'bun'):
                bot = cy + 0.72 * r * length
                P = [(cx - 1.12 * r, bot), (cx - 1.16 * r, cy), (cx - 0.95 * r, cy - 0.85 * r), (cx, cy - 1.18 * r),
                     (cx + 0.95 * r, cy - 0.85 * r), (cx + 1.16 * r, cy), (cx + 1.12 * r, bot)]
                self.fill(self.poly(P, smooth=True) | self.rect(cx - 1.13 * r, cy, cx + 1.13 * r, bot), colour,
                          seed=sd, **kw)
                if style == 'bun':
                    self.fill(self.blob(cx - turn * 0.3 * r, cy - 1.25 * r, 0.42 * r, 0.38 * r, rough=0.05), colour,
                              seed=sd + 1, **kw)
            elif style == 'long':
                # the mass falls behind the shoulders: wider and longer on the back side of a turned head
                t = np.linspace(np.pi, 2 * np.pi, 24)
                topc = np.stack([cx + 1.08 * r * np.cos(t), cy - 0.05 * r + 1.12 * r * np.sin(t)], 1)
                wR = 1.12 + 0.3 * max(0.0, -turn); wL = 1.12 + 0.3 * max(0.0, turn)
                bR = cy + (1.9 + 0.5 * max(0.0, -turn)) * r * length
                bL = cy + (1.9 + 0.5 * max(0.0, turn)) * r * length
                ends = []
                for i in range(9):
                    u = i / 8
                    xe = cx + wR * 1.08 * r - (wR + wL) * 1.08 * r * u
                    ye = bR * (1 - u) + bL * u - (0.16 * r if i % 2 else 0.0) - 0.18 * r * np.sin(np.pi * u) ** 2
                    ends.append((xe, ye))
                P = np.vstack([topc, [(cx + wR * r, cy + 0.4 * r), (cx + wR * 1.06 * r, cy + 1.2 * r)], ends,
                               [(cx - wL * 1.06 * r, cy + 1.2 * r), (cx - wL * r, cy + 0.4 * r)]])
                self.fill(self.poly(P), colour, seed=sd, **kw)
                if strands:
                    for i in range(4):
                        side = -1 if i % 2 else 1
                        wq = wR if side > 0 else wL
                        bq = bR if side > 0 else bL
                        x0 = cx + side * (wq - 0.1) * r
                        self.crayon([(x0, cy - 0.2 * r), (x0 + side * 0.18 * r, cy + 0.9 * r),
                                     (x0 + side * (0.3 + 0.08 * i) * r, bq + (0.05 * i) * r)],
                                    max(1.4 * k, 0.011 * r), colour, taper=(0.1, 0.6), alpha=0.85, seed=sd + i)
            elif style == 'short':
                P = [(cx - 1.06 * r, cy + 0.1 * r), (cx - 1.0 * r, cy - 0.7 * r), (cx, cy - 1.16 * r),
                     (cx + 1.0 * r, cy - 0.7 * r), (cx + 1.06 * r, cy + 0.1 * r), (cx, cy - 0.2 * r)]
                self.fill(self.poly(P, smooth=True), colour, seed=sd, **kw)
            return
        # front: the fringe and side locks over the face
        fx = cx + turn * 0.26 * r
        if style in ('bob', 'bun', 'short'):
            line = cy - (0.42 if style != 'short' else 0.5) * r
            part = fx - 0.25 * r * (1 if turn >= 0 else -1)
            t = np.linspace(np.pi * 1.02, np.pi * 1.98, 40)
            cap = np.stack([cx + 1.06 * r * np.cos(t), cy - 0.05 * r + 1.1 * r * np.sin(t)], 1)
            fr = np.array([(cx + 1.06 * r, line + 0.3 * r), (fx + 0.55 * r, line + 0.02 * r), (part + 0.15 * r, line - 0.1 * r),
                           (part, line - 0.28 * r), (part - 0.2 * r, line - 0.05 * r), (fx - 0.6 * r, line + 0.05 * r),
                           (cx - 1.06 * r, line + 0.32 * r)])
            self.fill(self.poly(np.vstack([cap, fr]), smooth=True), colour, seed=sd, **kw)
            if style in ('bob', 'bun'):
                for side in (-1, 1):
                    if turn * side > 0.4: continue
                    ox = cx + side * 1.12 * r
                    ix = cx + side * (0.84 - 0.1 * max(0, -turn * side)) * r
                    P = [(ox, line - 0.1 * r), (ix, line + 0.2 * r), (ix + side * 0.04 * r, cy + 0.55 * r),
                         (ix + side * 0.1 * r, cy + 0.72 * r * length), (ox, cy + 0.74 * r * length)]
                    self.fill(self.poly(P), colour, seed=sd + 2 + side, **kw)
        elif style == 'long':
            px, py = fx - 0.05 * r, cy - 1.1 * r
            for side in (-1, 1):
                P = [(px, py), (px + side * 0.12 * r, cy - 0.85 * r), (px + side * 0.55 * r, cy - 0.5 * r),
                     (fx + side * 0.86 * r, cy - 0.05 * r), (fx + side * 0.9 * r, cy + 0.7 * r),
                     (cx + side * 1.25 * r, cy + 0.9 * r), (cx + side * 1.15 * r, cy - 0.7 * r),
                     (px + side * 0.4 * r, py - 0.02 * r)]
                self.fill(self.poly(P, smooth=True), colour, seed=sd + 3 + side, **kw)

    def beanie(self, cx, cy, r, colour='cream', band=None, pompom=True, turn=0.0, seed=None):
        """a knitted hat over the top of a head (band at the forehead, rib dashes, a pompom)"""
        k = self.k
        rr = self._r(seed)
        band = band or colour
        line = cy - 0.36 * r
        t = np.linspace(np.pi, 2 * np.pi, 40)
        dome = np.stack([cx + 1.1 * r * np.cos(t), line - 0.02 * r + 1.0 * r * np.sin(t) * 0.98], 1)
        dome = np.vstack([dome, [(cx + 1.1 * r, line + 0.05 * r), (cx - 1.1 * r, line + 0.05 * r)]])
        self.fill(self.poly(dome), colour, angle=90, streak=0.3, dry=0.2, dry_px=r * 0.1, edge=1.0,
                  seed=int(rr.integers(1 << 30)))
        bnd = self.poly([(cx - 1.16 * r, line - 0.24 * r), (cx, line - 0.3 * r), (cx + 1.16 * r, line - 0.24 * r),
                         (cx + 1.14 * r, line + 0.12 * r), (cx, line + 0.18 * r), (cx - 1.14 * r, line + 0.12 * r)],
                        smooth=True)
        self.fill(bnd, band, angle=0, streak=0.3, dry=0.15, dry_px=r * 0.06, edge=1.0, lo=hexc(band) * 0.86,
                  seed=int(rr.integers(1 << 30)))
        for i in range(9):
            x = cx + (i - 4) * 0.24 * r + turn * 0.1 * r
            self.crayon([(x, line - 0.2 * r), (x, line + 0.1 * r)], max(1.6 * k, 0.03 * r),
                        hexc(band) * 0.78, taper=(0.3, 0.3), alpha=0.7, wobble=0.3)
        if pompom:
            self.fill(self.blob(cx + turn * 0.15 * r, line - 1.1 * r, 0.3 * r, 0.28 * r, rough=0.12), band, angle=60,
                      streak=0.4, dry=0.3, dry_px=r * 0.06, edge=1.8, soft=1.4, seed=int(rr.integers(1 << 30)))

    # ================================================================== figures
    def limb(self, path, w0, w1=None, colour='vermilion', angle=None, **kw):
        """an arm or a leg: a soft tube"""
        P = np.asarray(path, np.float32)
        if angle is None:
            d = P[-1] - P[0]; angle = float(np.degrees(np.arctan2(d[1], d[0])))
        kw.setdefault('dry', 0.15); kw.setdefault('dry_px', w0 * 0.2); kw.setdefault('streak', 0.3)
        self.fill(self.tube(P, w0, w1), colour, angle=angle, **kw)

    def mitten(self, x, y, r, colour='pine_mid', angle=90.0, thumb=1):
        a = np.deg2rad(angle)
        self.fill(self.blob(x, y, r * 0.95, r * 1.1, rough=0.04, rot=a - np.pi / 2), colour, angle=angle, dry=0,
                  edge=0.7, soft=0.7, streak=0.25)
        if thumb:
            tx = x + np.cos(a + thumb * 1.2) * r * 0.75; ty = y + np.sin(a + thumb * 1.2) * r * 0.75
            self.fill(self.ellipse(tx, ty, r * 0.38, r * 0.48, rot=np.degrees(a)), colour, dry=0, edge=0.6, soft=0.6,
                      streak=0.2)

    def boot(self, x, y, w, colour='black', facing=1):
        """a little boot standing at (x, y) (the sole), toe toward `facing`"""
        f = facing
        P = [(x - f * 0.42 * w, y), (x - f * 0.42 * w, y - 0.75 * w), (x + f * 0.12 * w, y - 0.75 * w),
             (x + f * 0.2 * w, y - 0.38 * w), (x + f * 0.58 * w, y - 0.3 * w), (x + f * 0.62 * w, y - 0.05 * w),
             (x + f * 0.5 * w, y + 0.02 * w)]
        self.fill(self.poly(P, smooth=True), colour, angle=0, dry=0.05, dry_px=w * 0.1, edge=0.7, soft=0.7,
                  streak=0.25)

    POSES = {
        # joints in units of the figure's height h, origin on the ground between the feet, facing right
        'stand': dict(sh_n=(0.115, -0.66), sh_f=(-0.115, -0.66), el_n=(0.16, -0.52), el_f=(-0.16, -0.52),
                      wr_n=(0.17, -0.40), wr_f=(-0.17, -0.40), hip_n=(0.06, -0.30), hip_f=(-0.06, -0.30),
                      kn_n=(0.065, -0.17), kn_f=(-0.065, -0.17), an_n=(0.07, -0.035), an_f=(-0.07, -0.035),
                      head=(0.0, -0.835), lean=0.0),
        'walk': dict(sh_n=(0.11, -0.66), sh_f=(-0.11, -0.66), el_n=(0.19, -0.54), el_f=(-0.17, -0.55),
                     wr_n=(0.27, -0.45), wr_f=(-0.22, -0.43), hip_n=(0.05, -0.30), hip_f=(-0.05, -0.30),
                     kn_n=(0.11, -0.17), kn_f=(-0.07, -0.16), an_n=(0.15, -0.04), an_f=(-0.13, -0.06),
                     head=(0.015, -0.835), lean=0.0),
        # sitting on an edge (x, y = the seat under the hips), legs hanging over it
        'sit': dict(sh_n=(0.11, -0.40), sh_f=(-0.11, -0.40), el_n=(0.17, -0.27), el_f=(-0.15, -0.27),
                    wr_n=(0.2, -0.15), wr_f=(-0.16, -0.15), hip_n=(0.03, -0.04), hip_f=(-0.02, -0.04),
                    kn_n=(0.22, -0.035), kn_f=(0.18, -0.045), an_n=(0.25, 0.17), an_f=(0.19, 0.15),
                    head=(0.015, -0.575), lean=0.0),
    }

    def child(self, x, y, h, facing=1, pose='stand', outfit=None, hooks=None, **joints):
        """a picture-book child about h px tall standing on (x, y). outfit keys: coat, sleeve, legs, boots, hair,
        hair_style, hat, hat_band, scarf, mittens, skin, eyes, mouth, nose, turn, look, collar, buttons, dress
        (a hem below the coat), hem (coat length, 0..1). pose 'stand' / 'walk' (x, y on the ground between the
        feet) or 'sit' (x, y on the seat edge under the hips, legs hanging). hooks: callables run at 'behind',
        'hand_far', 'before_head', 'hand_near', 'end'. joints override POSES entries (units of h). Returns pixel
        joints."""
        o = dict(coat='vermilion', sleeve=None, legs='brick', boots='black', hair='hair', hair_style='bob', hat=None,
                 hat_band=None, scarf=None, mittens='pine_mid', skin='skin', eyes='dot', mouth='smile',
                 nose='button', turn=0.35 * facing, look=(0.4 * facing, 0.0), collar=None, buttons='cream',
                 dress=None, hem=1.0, brows=False, hair_len=1.0, eye_size=1.0)
        o.update(outfit or {})
        hooks = hooks or {}
        J0 = dict(self.POSES[pose]); J0.update(joints)
        f = facing
        J = {kk: (x + f * v[0] * h, y + v[1] * h) for kk, v in J0.items() if kk != 'lean'}
        sleeve = o['sleeve'] or (hexc(o['coat']) * 0.86)
        k = self.k
        if 'behind' in hooks: hooks['behind']()
        aw = 0.075 * h
        # far arm (behind the coat), far leg, near leg
        self.limb([J['sh_f'], J['el_f'], J['wr_f']], aw, aw * 0.85, sleeve)
        if o['mittens']: self.mitten(*J['wr_f'], 0.04 * h, o['mittens'], angle=90 - f * 20, thumb=f)
        if 'hand_far' in hooks: hooks['hand_far']()
        lw = 0.062 * h
        for s in ('f', 'n'):
            col = o['legs'] if s == 'n' else hexc(o['legs']) * 0.85
            self.limb([J['hip_' + s], J['kn_' + s], J['an_' + s]], lw, lw * 0.9, col)
            bx, by = J['an_' + s]
            self.boot(bx + f * 0.01 * h, by + 0.035 * h, 0.105 * h,
                      o['boots'] if s == 'n' else hexc(o['boots']) * 0.85 + 0.02, facing=f)
        # the coat: an A-line from the shoulders to the hem
        sh_y = (J['sh_n'][1] + J['sh_f'][1]) / 2
        cx0 = (J['sh_n'][0] + J['sh_f'][0]) / 2
        hem_y = y - (0.27 + 0.1 * (1 - o['hem'])) * h if pose != 'sit' else y + 0.005 * h
        sw, hw = 0.13 * h, 0.235 * h
        neck_y = sh_y - 0.025 * h
        if o['dress']:
            self.fill(self.poly([(cx0 - hw * 0.95, hem_y - 0.05 * h), (cx0 + hw * 0.95, hem_y - 0.05 * h),
                                 (cx0 + hw * 1.02, hem_y + 0.05 * h), (cx0 - hw * 1.02, hem_y + 0.05 * h)]),
                      o['dress'], angle=0, streak=0.3, dry=0.1, dry_px=0.01 * h)
        P = [(cx0 - 0.045 * h, neck_y), (cx0 - sw * 0.85, sh_y - 0.005 * h), (cx0 - sw * 1.05, sh_y + 0.04 * h),
             (cx0 - sw * 1.15, sh_y + 0.12 * h), (cx0 - hw, hem_y - 0.01 * h), (cx0 - hw * 0.3, hem_y + 0.012 * h),
             (cx0 + hw * 0.3, hem_y + 0.012 * h), (cx0 + hw, hem_y - 0.01 * h), (cx0 + sw * 1.15, sh_y + 0.12 * h),
             (cx0 + sw * 1.05, sh_y + 0.04 * h), (cx0 + sw * 0.85, sh_y - 0.005 * h), (cx0 + 0.045 * h, neck_y)]
        coat = self.poly(P, smooth=True)
        self.fill(coat, o['coat'], angle=88, streak=0.35, dry=0.2, dry_px=0.02 * h)
        J['coat'] = coat
        J['hem'] = (cx0, hem_y)
        if o['buttons']:
            for i in range(3):
                self.dots([(cx0 + f * 0.012 * h, sh_y + (0.07 + i * 0.075) * h)], 0.011 * h, o['buttons'])
        if o['collar']:
            for s in (-1, 1):
                self.fill(self.poly([(cx0, neck_y + 0.04 * h), (cx0 + s * 0.085 * h, neck_y - 0.005 * h),
                                     (cx0 + s * 0.1 * h, neck_y + 0.045 * h)]), o['collar'], dry=0, edge=0.7)
        if o['scarf']:
            sc = o['scarf']
            self.fill(self.blob(cx0, neck_y + 0.01 * h, 0.1 * h, 0.035 * h, rough=0.05), sc, angle=0, streak=0.35,
                      dry=0.1, dry_px=0.008 * h)
            tail = [(cx0 + f * 0.03 * h, neck_y + 0.02 * h), (cx0 + f * 0.05 * h, neck_y + 0.1 * h),
                    (cx0 + f * 0.055 * h, neck_y + 0.17 * h)]
            if pose == 'walk':
                tail = [(cx0 - f * 0.06 * h, neck_y + 0.015 * h), (cx0 - f * 0.13 * h, neck_y + 0.05 * h),
                        (cx0 - f * 0.17 * h, neck_y + 0.13 * h)]
            self.fill(self.tube(tail, 0.05 * h, 0.045 * h), sc, angle=90 if pose != 'walk' else 60, streak=0.35,
                      dry=0.1, dry_px=0.008 * h, lo=hexc(sc) * 0.9)
            end = np.array(tail[-1]); d = end - np.array(tail[-2]); d = d / (np.linalg.norm(d) + 1e-6)
            nrm = np.array([-d[1], d[0]])
            for i in range(-2, 3):
                p0 = end + nrm * i * 0.009 * h
                self.crayon([p0, p0 + d * 0.025 * h], max(1.5 * k, 0.006 * h), hexc(sc) * 0.9, taper=(0, 0.5))
        if 'before_head' in hooks: hooks['before_head']()
        # near arm over the coat
        self.limb([J['sh_n'], J['el_n'], J['wr_n']], aw, aw * 0.85, sleeve)
        self.shadow(self.tube([J['sh_n'], J['el_n'], J['wr_n']], aw * 1.25, aw * 1.05) - self.tube(
            [J['sh_n'], J['el_n'], J['wr_n']], aw * 0.95, aw * 0.8), 'shadow', depth=0.5, edge=0.6)
        if o['mittens']: self.mitten(*J['wr_n'], 0.04 * h, o['mittens'], angle=90 + f * 10, thumb=-f)
        if 'hand_near' in hooks: hooks['hand_near']()
        # the head
        hx, hy = J['head']
        r = 0.135 * h
        J['r'] = r
        self.fill(self.tube([(cx0, neck_y + 0.015 * h), (hx, hy + 0.75 * r)], 0.07 * h), o['skin'], angle=90, dry=0,
                  edge=0.5, lo=hexc(o['skin']) * 0.93)
        self.hair(hx, hy, r, o['hair_style'], o['hair'], o['turn'], 'back', length=o['hair_len'])
        F = self.face(hx, hy, r, turn=o['turn'], eyes=o['eyes'], look=o['look'], skin=o['skin'], mouth=o['mouth'],
                      nose=o['nose'], brows=o['brows'], ears=True, eye_size=o['eye_size'])
        self.hair(hx, hy, r, o['hair_style'], o['hair'], o['turn'], 'front', length=o['hair_len'])
        if o['hat']: self.beanie(hx, hy, r, o['hat'], o['hat_band'], turn=o['turn'])
        J['face'] = F
        if 'end' in hooks: hooks['end']()
        return J

    # ================================================================== props
    def house(self, x, y, w, h, wall='vermilion', side=None, roof='snow_light', snow=True, depth=None,
              window='window', door='brick', chimney='brick', windows=None, seed=None):
        """a little gabled cottage: the gable end (x .. x + w, ground y, wall height h) and a side wall running off to
        the left (depth px) under a snowy roof. Returns anchors (apex, chimney top, windows)"""
        k = self.k
        rr = self._r(seed)
        side = side or hexc(wall) * 0.8
        d = 0.9 * w if depth is None else depth
        apex = (x + w / 2, y - h - 0.62 * w)
        e = 0.07 * w
        # side wall and its roof
        self.fill(self.rect(x - d, y - h, x + 2, y), side, angle=88, streak=0.35, dry=0.15, seed=int(rr.integers(1 << 30)))
        self.fill(self.rect(x, y - h, x + w, y) | self.poly([(x, y - h + 2), apex, (x + w, y - h + 2)]), wall,
                  angle=80, streak=0.35, dry=0.15, seed=int(rr.integers(1 << 30)))
        roofP = [(apex[0], apex[1] - 0.02 * w), (x - e, y - h + 0.02 * w), (x - e - d, y - h + 0.02 * w),
                 (apex[0] - d, apex[1] - 0.02 * w)]
        out = dict(apex=apex)
        # chimney (behind the snow lip) on the roof
        cxm = apex[0] - d * 0.62
        top = apex[1] - 0.18 * w
        self.fill(self.rect(cxm - 0.09 * w, top, cxm + 0.09 * w, apex[1] + 0.25 * w), chimney, angle=90, streak=0.3,
                  dry=0.05, dry_px=4 * k, seed=int(rr.integers(1 << 30)))
        self.fill(self.rect(cxm - 0.105 * w, top - 0.03 * w, cxm + 0.105 * w, top + 0.02 * w), hexc(chimney) * 0.85,
                  dry=0, edge=0.6)
        out['chimney'] = (cxm, top - 0.03 * w)
        self.fill(self.poly(roofP), roof if snow else hexc(wall) * 0.7, angle=-35, streak=0.45, dry=0.25,
                  dry_px=0.03 * w, mottle=0.25, seed=int(rr.integers(1 << 30)))
        if snow:
            self.mottle(self.poly(roofP), 'snow', scale=0.25 * w, cover=0.3, angle=-35, streak=0.4)
            # the snow lip along the eaves, hanging a little
            xs = np.linspace(x - e - d, x - e, 30)
            ys = y - h + 0.02 * w + 0.025 * w + 0.012 * w * np.sin(xs * 0.05)
            P = np.vstack([np.stack([xs, ys - 0.04 * w], 1), np.stack([xs[::-1], ys[::-1] + 0.015 * w], 1)])
            self.fill(self.poly(P), 'white', angle=0, streak=0.3, dry=0.1, dry_px=3 * k)
        # the bargeboard (snow on the gable edges)
        for a, b in ((apex, (x - e, y - h + 0.02 * w)), (apex, (x + w + e, y - h + 0.02 * w))):
            self.brush([a, b], 0.075 * w, roof if snow else hexc(wall) * 0.7, taper=(0.02, 0.02), dry=0.1, streak=0.4)
        if snow:
            self.scumble(self.tube([apex, (x + w + e, y - h + 0.02 * w)], 0.07 * w), 'white', angle=-30, cover=0.55)
        # windows: two on the gable end, one in the gable, one on the side wall; a door on the side
        W_ = windows or [(x + 0.18 * w, y - 0.78 * h, 0.24 * w, 0.32 * h), (x + 0.58 * w, y - 0.78 * h, 0.24 * w, 0.32 * h),
                         (x + 0.4 * w, y - h - 0.32 * w, 0.2 * w, 0.18 * w), (x - 0.72 * d, y - 0.8 * h, 0.22 * w, 0.3 * h)]
        out['windows'] = []
        for (wx, wy, ww, wh) in W_:
            reg = self.rect(wx, wy, wx + ww, wy + wh)
            self.fill(reg, window, angle=90, streak=0.3, dry=0.05, dry_px=3 * k, edge=0.6,
                      hi='lamp', lo='gold', mottle=0.3)
            self.mottle(reg, 'orange_light', scale=ww * 0.6, cover=0.25, edge=0.6, soft=1, streak=0.2, dry=0.2)
            bw = max(2.5 * k, 0.045 * ww + 2 * k)
            self.crayon([(wx + ww / 2, wy + 2), (wx + ww / 2, wy + wh - 2)], bw, 'brown', taper=(0.05, 0.05))
            self.crayon([(wx + 2, wy + wh * 0.48), (wx + ww - 2, wy + wh * 0.48)], bw, 'brown', taper=(0.05, 0.05))
            out['windows'].append((wx + ww / 2, wy + wh / 2, ww, wh))
        if door:
            dx = x - 0.32 * d
            self.fill(self.rect(dx - 0.13 * w, y - 0.62 * h, dx + 0.13 * w, y + 2), door, angle=90, streak=0.35,
                      dry=0.05, dry_px=3 * k)
            self.dots([(dx + 0.08 * w, y - 0.3 * h)], 0.018 * w, 'mustard')
        return out

    def pine(self, x, y, h, w=None, colour='pine', light='pine_mid', tiers=None, snow=None, lean=0.0, seed=None):
        """a wild, feathery pine: a trunk and uneven tiers of dry, tapered fronds sweeping up -- lengths jump about,
        a few are missing, the crown leans -- so it reads as a tree in a wood, not a tidy cone (snow= a colour for
        snow lying on the top side of some fronds)"""
        k = self.k
        rr = self._r(seed)
        w = 0.55 * h if w is None else w
        n = tiers or max(5, int(h / (40 * k)))
        self.crayon([(x, y), (x + lean * h * 0.3, y - h * 0.3)], max(4 * k, 0.04 * w), 'ink', taper=(0.0, 0.3))
        self.crayon([(x + lean * h * 0.25, y - h * 0.25), (x + lean * h * 0.6, y - h * 0.6), (x + lean * h, y - h * 0.97)],
                    max(3 * k, 0.03 * w), colour, taper=(0.0, 0.6))
        for i in range(n):
            t = i / (n - 1)
            yb = y - h * (0.16 + 0.78 * t)
            xb = x + lean * h * (0.16 + 0.78 * t)
            base = w * 0.5 * (1 - t) ** 0.7 + w * 0.08
            for s in (-1, 1):
                if i < n - 2 and rr.random() < 0.14: continue
                L = base * rr.uniform(0.62, 1.22)
                up = np.deg2rad(24 + 26 * t + rr.uniform(-9, 9))
                tip = (xb + s * L * np.cos(up), yb - L * np.sin(up))
                mid = (xb + s * L * 0.5 * np.cos(up), yb - L * 0.5 * np.sin(up) + 0.05 * L)
                col = colour if rr.random() > 0.22 else light
                self.brush([(xb, yb + 0.02 * L), mid, tip], max(7 * k, 0.36 * L), col, taper=(0.15, 0.65),
                           streak=0.4, dry=0.25, seed=int(rr.integers(1 << 30)))
                if rr.random() < 0.6:
                    up2 = up - np.deg2rad(14 + rr.uniform(0, 10))
                    tip2 = (xb + s * 0.7 * L * np.cos(up2), yb + 0.04 * L - 0.7 * L * np.sin(up2))
                    self.brush([(xb, yb + 0.06 * L), tip2], max(5 * k, 0.24 * L), light if col == colour else colour,
                               taper=(0.2, 0.7), streak=0.4, dry=0.3, pressure=0.92, seed=int(rr.integers(1 << 30)))
                if snow and rr.random() < 0.45:
                    self.brush([(xb + s * 0.3 * L * np.cos(up), yb - 0.3 * L * np.sin(up) - 0.07 * L),
                                (tip[0] - s * 0.15 * L, tip[1] - 0.03 * L)], max(3 * k, 0.08 * L), snow,
                               taper=(0.3, 0.5), streak=0.3, dry=0.3, pressure=0.85)
        self.brush([(x + lean * h * 0.88, y - h * 0.88), (x + lean * h * 1.02, y - h * 1.02)], max(5 * k, 0.07 * w),
                   colour, taper=(0.1, 0.7))

    def fir_far(self, x, y, h, w=None, colour='dusty', seed=None):
        """a small distant fir: one narrow, jagged spire"""
        rr = self._r(seed)
        w = 0.42 * h if w is None else w
        n = 4
        P = [(x, y - h)]
        for i in range(1, n + 1):
            t = i / n
            P += [(x + w / 2 * t, y - h + h * t * 0.92), (x + w / 2 * t * 0.55, y - h + h * t * 0.92 - 0.04 * h)]
        P = P[:-1] + [(x + w * 0.05, y), (x - w * 0.05, y)]
        L = [(2 * x - px, py) for px, py in P[1:-2][::-1]]
        self.fill(self.poly(P + L), colour, angle=90, streak=0.3, dry=0.1, dry_px=0.04 * w, seed=int(rr.integers(1 << 30)))

    def round_tree(self, x, y, h, w=None, crown='green', light='moss', trunk='brown', seed=None):
        k = self.k
        rr = self._r(seed)
        w = 0.7 * h if w is None else w
        self.limb([(x, y), (x, y - 0.5 * h)], 0.09 * w, 0.06 * w, trunk, dry=0.05)
        cx, cy = x, y - 0.62 * h
        crown_r = self.blob(cx, cy, w / 2, 0.38 * h, rough=0.08, seed=int(rr.integers(1 << 30)))
        self.fill(crown_r, crown, angle=-60, streak=0.25, dry=0.3, dry_px=0.05 * w, mottle=0.2)
        self.scumble(crown_r & self.ellipse(cx - 0.18 * w, cy - 0.12 * h, 0.32 * w, 0.24 * h), light, angle=-60,
                     cover=0.55)

    def bush(self, x, y, w, h, colour='pine_mid', light=None, seed=None):
        """a rounded bush standing on (x, y): three overlapping lumps"""
        rr = self._r(seed)
        reg = self.blob(x, y - 0.45 * h, w * 0.3, h * 0.6, rough=0.1, seed=int(rr.integers(1 << 30)))
        for s in (-1, 1):
            reg = reg | self.blob(x + s * w * 0.24, y - 0.3 * h, w * 0.27, h * 0.45, rough=0.1,
                                  seed=int(rr.integers(1 << 30)))
        reg = reg & self.above([x - w, x + w], [y + 2, y + 2])
        self.fill(reg, colour, angle=-70, streak=0.4, dry=0.3, dry_px=0.05 * w)
        if light: self.scumble(reg, light, angle=-70, cover=0.4)

    def shrub(self, x, y, h, w=None, colour='pine_mid', light='green', snow=None, n=9, seed=None):
        """a low bush of dry fronds fanning up out of the ground (or the snow) from one base"""
        k = self.k
        rr = self._r(seed)
        w = 1.2 * h if w is None else w
        for i in range(n):
            t = i / max(n - 1, 1) - 0.5
            a = np.deg2rad(-90 + t * 150 + rr.uniform(-8, 8))
            L = h * (1 - 0.55 * abs(t) * 2 * 0.6) * rr.uniform(0.75, 1.05)
            tip = (x + np.cos(a) * L * (w / h) * 0.6, y + np.sin(a) * L)
            mid = (x + np.cos(a) * L * 0.45 * (w / h) * 0.6, y + np.sin(a) * L * 0.52 + 0.04 * L)
            col = colour if rr.random() > 0.3 else light
            self.brush([(x + t * 0.25 * w, y + 0.04 * h), mid, tip], max(6 * k, 0.26 * L), col, taper=(0.1, 0.7),
                       streak=0.4, dry=0.25, seed=int(rr.integers(1 << 30)))
            if snow and rr.random() < 0.5:
                self.brush([mid, (tip[0] * 0.8 + mid[0] * 0.2, tip[1] * 0.8 + mid[1] * 0.2 - 0.04 * L)],
                           max(3 * k, 0.07 * L), snow, taper=(0.3, 0.5), dry=0.3, pressure=0.85)

    def cup(self, x, y, w, colour='orange', inside='coffee', rim='cream', handle=1, light=None, steam=None, seed=None):
        """a round cup standing at (x, y) (bottom centre), w wide; a lighter dry-brushed side, a saucer-free foot"""
        k = self.k
        rr = self._r(seed)
        h = 0.72 * w
        top = y - h
        if handle:
            hx = x + handle * w * 0.48
            a = np.linspace(-0.5 * np.pi, 0.5 * np.pi, 20)
            path = np.stack([hx + handle * 0.22 * w * np.cos(a), top + 0.36 * h + 0.24 * h * np.sin(a)], 1)
            self.fill(self.tube(path, 0.08 * w), colour, angle=90, dry=0, edge=0.7)
        t = np.linspace(0, np.pi, 30)
        body = np.vstack([[(x - w / 2, top)], np.stack([x - w / 2 * np.cos(t) * (1 - 0.18 * np.sin(t) ** 3),
                                                        top + 0.06 * h + 0.92 * h * np.sin(t) ** 0.6], 1)[1:-1][::1],
                          [(x + w / 2, top)]])
        bodyR = self.poly(body)
        self.fill(bodyR, colour, angle=80, streak=0.4, dry=0.2, dry_px=0.03 * w)
        lt = light or mix(colour, 'cream', 0.4)
        self.scumble(bodyR & self.rect(x + 0.12 * w, top, x + w, y), lt, angle=80, cover=0.6)
        self.fill(self.ellipse(x, top, w / 2, 0.12 * w), rim, dry=0, edge=0.6, streak=0.3)
        self.fill(self.ellipse(x, top + 0.01 * w, w * 0.43, 0.09 * w), inside, dry=0, edge=0.5, streak=0.3)
        self.fill(self.ellipse(x, y - 0.02 * w, w * 0.22, 0.04 * w), hexc(colour) * 0.8, dry=0, edge=0.5)
        if steam:
            for i in range(3):
                self.wisp(x + (i - 1) * 0.16 * w, top - 0.12 * w, (0.55 + 0.2 * (i == 1)) * w, steam, seed=int(rr.integers(1 << 30)))

    def parcel(self, x, y, w, h, colour='cobalt_bright', top=None, string='ink', bow=True, seed=None):
        """a plain box standing at (x, y) (front bottom-left corner): a front, a lighter top and a crayon string"""
        k = self.k
        top = top or mix(colour, 'white', 0.18)
        dd = 0.18 * w
        self.fill(self.rect(x, y - h, x + w, y), colour, angle=90, streak=0.35, dry=0.15, dry_px=0.04 * w)
        self.fill(self.poly([(x, y - h), (x + dd, y - h - dd * 0.6), (x + w + dd * 0.3, y - h - dd * 0.6),
                             (x + w, y - h)]), top, angle=0, streak=0.3, dry=0.05, dry_px=3 * k)
        if string:
            sw = max(2.5 * k, 0.05 * w)
            self.crayon([(x + w * 0.5, y - h), (x + w * 0.5, y)], sw, string, taper=(0.02, 0.02))
            self.crayon([(x + w * 0.5, y - h), (x + w * 0.5 + dd * 0.6, y - h - dd * 0.6)], sw, string, taper=(0, 0))
            if bow:
                bx, by = x + w * 0.5 + dd * 0.3, y - h - dd * 0.3
                for s in (-1, 1):
                    a = np.linspace(0, 2 * np.pi, 20)
                    self.crayon(np.stack([bx + s * 0.1 * w + s * 0.1 * w * np.cos(a), by - 0.06 * w * np.sin(a) * 1.2], 1),
                                sw * 0.9, string, taper=(0, 0))

    def bag(self, x, y, w, h, colour='kraft', seed=None):
        """a paper bag standing at (x, y) (bottom centre): a folded, crumpled top and a crease"""
        k = self.k
        top = y - h
        P = [(x - w / 2, y), (x - w * 0.47, top + 0.12 * h), (x - w * 0.3, top + 0.02 * h), (x - w * 0.1, top + 0.1 * h),
             (x + w * 0.12, top), (x + w * 0.33, top + 0.08 * h), (x + w * 0.47, top + 0.1 * h), (x + w / 2, y)]
        self.fill(self.poly(P), colour, angle=90, streak=0.35, dry=0.1, dry_px=0.04 * w)
        self.fill(self.poly([(x - w * 0.48, top + 0.12 * h), (x + w * 0.48, top + 0.1 * h), (x + w * 0.49, top + 0.24 * h),
                             (x - w * 0.49, top + 0.25 * h)]), hexc(colour) * 0.86, angle=0, dry=0, edge=0.6)
        self.crayon([(x + w * 0.2, top + 0.3 * h), (x + w * 0.22, y - 0.05 * h)], max(2 * k, 0.03 * w),
                    hexc(colour) * 0.7, taper=(0.3, 0.3), alpha=0.7)

    def potted(self, x, y, h, pot='tomato', leaf='green', seed=None):
        rr = self._r(seed)
        pw = 0.45 * h
        self.fill(self.poly([(x - pw / 2, y - 0.38 * h), (x + pw / 2, y - 0.38 * h), (x + pw * 0.38, y),
                             (x - pw * 0.38, y)]), pot, angle=90, streak=0.3, dry=0.1, dry_px=0.03 * h)
        self.fill(self.rect(x - pw * 0.56, y - 0.44 * h, x + pw * 0.56, y - 0.36 * h), hexc(pot) * 0.88, dry=0,
                  edge=0.6)
        for i in range(7):
            a = np.deg2rad(-90 + (i - 3) * 22 + rr.uniform(-6, 6))
            L = h * (0.45 + 0.2 * rr.random())
            p0 = (x, y - 0.42 * h)
            self.brush([p0, (x + np.cos(a) * L * 0.5, y - 0.42 * h + np.sin(a) * L * 0.55),
                        (x + np.cos(a) * L, y - 0.42 * h + np.sin(a) * L)], 0.12 * h, leaf, taper=(0.3, 0.5))

    def reeds(self, x, y, h, n=5, colour='pine_mid', head='brown', spread=None, seed=None):
        k = self.k
        rr = self._r(seed)
        spread = 0.25 * h if spread is None else spread
        for i in range(n):
            x0 = x + (i - (n - 1) / 2) * spread / max(n - 1, 1) + rr.uniform(-4, 4) * k
            hh = h * rr.uniform(0.7, 1.0)
            lean = rr.uniform(-0.12, 0.12) * hh
            self.brush([(x0, y), (x0 + lean * 0.4, y - hh * 0.5), (x0 + lean, y - hh)], max(4 * k, 0.025 * h), colour,
                       taper=(0.05, 0.4), dry=0.1)
            if head and rr.random() < 0.7:
                self.fill(self.tube([(x0 + lean * 0.86, y - hh * 0.78), (x0 + lean * 0.95, y - hh * 0.93)],
                                    max(8 * k, 0.06 * h)), head, angle=90, dry=0, edge=0.8)
            if rr.random() < 0.6:
                s = -1 if rr.random() < 0.5 else 1
                self.brush([(x0, y - hh * 0.1), (x0 + s * 0.12 * hh, y - hh * 0.45), (x0 + s * 0.25 * hh, y - hh * 0.6)],
                           max(5 * k, 0.035 * h), colour, taper=(0.05, 0.8), dry=0.1)

    def tuft(self, x, y, w, h, colour='green', n=7, seed=None):
        k = self.k
        rr = self._r(seed)
        for i in range(n):
            t = i / max(n - 1, 1) - 0.5
            x0 = x + t * w * 0.6
            tip = (x + t * w + rr.uniform(-0.05, 0.05) * w, y - h * (0.6 + 0.4 * rr.random()) * (1 - abs(t)))
            self.brush([(x0, y + 2 * k), tip], max(4 * k, 0.12 * w), colour, taper=(0.05, 0.85), dry=0.1)

    def lamp(self, x, y, h, colour='ink', light='lamp', glow=0.55, seed=None):
        k = self.k
        self.limb([(x, y), (x, y - 0.9 * h)], 0.035 * h, 0.03 * h, colour, dry=0)
        self.fill(self.poly([(x - 0.07 * h, y - 0.9 * h), (x + 0.07 * h, y - 0.9 * h), (x + 0.05 * h, y - 1.02 * h),
                             (x - 0.05 * h, y - 1.02 * h)]), light, dry=0, edge=0.6)
        self.fill(self.poly([(x - 0.09 * h, y - 1.02 * h), (x + 0.09 * h, y - 1.02 * h), (x, y - 1.09 * h)]), colour,
                  dry=0, edge=0.6)
        if glow: self.glow(self.ellipse(x, y - 0.96 * h, 0.28 * h), light, glow)

    def dog(self, x, y, s, facing=1, colour='orange', patch='cream', ear=None, collar='vermilion', nose='black',
            tail_up=True, seed=None):
        """a small dog trotting, standing on (x, y), about s px from tail to nose; returns anchors (collar, nose,
        head)"""
        k = self.k
        rr = self._r(seed)
        f = facing
        ear = ear or hexc(colour) * 0.78
        dark = hexc(colour) * 0.84
        P = lambda a, b: (x + f * a * s, y - b * s)
        lw = 0.1 * s
        # far legs (trotting: far front back, far hind forward)
        self.limb([P(0.2, 0.34), P(0.17, 0.17), P(0.12, 0.02)], lw, lw * 0.9, dark, dry=0)
        self.limb([P(-0.2, 0.36), P(-0.14, 0.18), P(-0.1, 0.02)], lw, lw * 0.9, dark, dry=0)
        tail = [P(-0.3, 0.46), P(-0.43, 0.58), P(-0.45, 0.74)] if tail_up else [P(-0.3, 0.4), P(-0.48, 0.34), P(-0.55, 0.24)]
        self.brush(tail, 0.1 * s, colour, taper=(0.05, 0.7), dry=0.1)
        body = self.blob(*P(-0.01, 0.43), 0.33 * s, 0.155 * s, rough=0.03, seed=int(rr.integers(1 << 30)))
        self.fill(body, colour, angle=0, streak=0.35, dry=0.15, dry_px=0.03 * s)
        # near legs (near front forward, near hind back)
        for path in ([P(0.22, 0.36), P(0.28, 0.17), P(0.33, 0.02)], [P(-0.2, 0.38), P(-0.27, 0.18), P(-0.3, 0.02)]):
            self.limb(path, lw * 1.05, lw * 0.92, colour, dry=0)
            self.fill(self.ellipse(path[-1][0] + f * 0.025 * s, path[-1][1] - 0.005 * s, 0.065 * s, 0.032 * s),
                      colour, dry=0, edge=0.6)
        # neck, head, chest patch, muzzle, ear
        hx, hy = P(0.36, 0.66)
        self.fill(self.tube([P(0.2, 0.44), (hx, hy)], 0.22 * s, 0.18 * s), colour, angle=-50, dry=0.1, dry_px=0.02 * s)
        self.fill(self.blob(*P(0.27, 0.42), 0.09 * s, 0.13 * s, rough=0.05, rot=np.deg2rad(-f * 20)), patch,
                  angle=80, dry=0.15, dry_px=0.015 * s, edge=1.1)
        self.fill(self.ellipse(hx, hy, 0.165 * s, 0.15 * s), colour, angle=0, dry=0.1, dry_px=0.02 * s)
        sn = self.ellipse(*P(0.51, 0.62), 0.105 * s, 0.072 * s, rot=f * 8)
        self.fill(sn, patch, dry=0.05, dry_px=0.01 * s, edge=0.7)
        self.fill(self.ellipse(*P(0.6, 0.645), 0.034 * s, 0.03 * s), nose, dry=0, edge=0.4)
        self.eye_dot(*P(0.41, 0.71), 0.027 * s)
        self.fill(self.blob(*P(0.27, 0.66), 0.07 * s, 0.13 * s, rough=0.05, rot=np.deg2rad(f * 18)), ear,
                  angle=80, dry=0.05, dry_px=0.01 * s, edge=0.7)
        self.cheek(*P(0.44, 0.6), 0.033 * s, alpha=0.6)
        if collar:
            self.brush([P(0.22, 0.6), P(0.3, 0.48)], 0.05 * s, collar, taper=(0.05, 0.05), dry=0)
        return dict(collar=P(0.26, 0.54), nose=P(0.6, 0.645), head=(hx, hy))

    def duck(self, x, y, s, facing=1, colour='cream', wing=None, beak='orange', swim=True, seed=None):
        """a duck at (x, y) (the waterline / feet), s px long"""
        k = self.k
        rr = self._r(seed)
        f = facing
        wing = wing or mix(colour, 'cream_dark', 0.6)
        P = lambda a, b: (x + f * a * s, y - b * s)
        bodyP = [P(-0.5, 0.3), P(-0.38, 0.2), P(-0.1, 0.02), P(0.25, 0.02), P(0.42, 0.15), P(0.38, 0.32),
                 P(0.1, 0.36), P(-0.25, 0.33)]
        body = self.poly(bodyP, smooth=True)
        if swim: body = body & self.above([x - s, x + s], [y, y])
        self.fill(body, colour, angle=0, streak=0.35, dry=0.15, dry_px=0.03 * s)
        self.fill(self.poly([P(-0.25, 0.26), P(0.15, 0.28), P(0.05, 0.14), P(-0.3, 0.17)], smooth=True), wing,
                  angle=0, dry=0.05, dry_px=0.01 * s, edge=0.8)
        self.fill(self.tube([P(0.28, 0.3), P(0.32, 0.5)], 0.17 * s, 0.15 * s), colour, angle=90, dry=0.05, dry_px=0.02 * s)
        hx, hy = P(0.32, 0.56)
        self.fill(self.ellipse(hx, hy, 0.13 * s, 0.12 * s), colour, dry=0.05, dry_px=0.02 * s)
        self.fill(self.poly([P(0.4, 0.58), P(0.6, 0.53), P(0.58, 0.49), P(0.4, 0.5)], smooth=True), beak, dry=0,
                  edge=0.6)
        self.eye_dot(*P(0.36, 0.59), 0.025 * s)
        self.cheek(*P(0.3, 0.52), 0.035 * s, alpha=0.55)
        return dict(head=(hx, hy))

    def fence(self, x0, x1, y, h, colour='brown', n=None, seed=None):
        k = self.k
        n = n or max(2, int((x1 - x0) / (h * 0.9)))
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i / n
            self.limb([(x, y), (x, y - h)], 0.1 * h, 0.09 * h, colour, dry=0)
        for t in (0.35, 0.75):
            self.brush([(x0 - 0.05 * h, y - t * h), (x1 + 0.05 * h, y - t * h)], 0.08 * h, colour, taper=(0.02, 0.05))

    # ================================================================== sky and marks
    def snow(self, x0, y0, x1, y1, n=120, r=None, colour='cream', alpha=0.95, avoid=None, seed=None):
        """falling snow: fuzzy dots of a few sizes"""
        k = self.k
        rr = self._r(seed)
        r = (2.8 * k, 6.5 * k) if r is None else r
        pts = np.stack([rr.uniform(x0, x1, n), rr.uniform(y0, y1, n)], 1)
        rad = rr.uniform(r[0], r[1], n) ** 1.0
        self.dots(pts, rad, colour, alpha=alpha, avoid=avoid, seed=int(rr.integers(1 << 30)))

    def stars(self, x0, y0, x1, y1, n=40, colour='cream', seed=None):
        k = self.k
        rr = self._r(seed)
        pts = np.stack([rr.uniform(x0, x1, n), rr.uniform(y0, y1, n)], 1)
        self.dots(pts, rr.uniform(1.4 * k, 3.0 * k, n), colour, alpha=0.9)

    def moon(self, x, y, r, colour='cream', halo=0.35, crescent=0.0):
        """a chalky moon; crescent > 0 bites a disc out of it (0.3 a fat crescent, 0.6 a thin one)"""
        if halo: self.glow(self.ellipse(x, y, r * 1.9), colour, halo, soft=4.0, edge=2.0)
        reg = self.ellipse(x, y, r)
        if crescent: reg = reg - self.ellipse(x + crescent * r * 1.1, y - crescent * r * 0.45, r * 0.98)
        self.fill(reg, colour, angle=-40, streak=0.35, dry=0.2, dry_px=0.1 * r, mottle=0.3)
        self.mottle(reg, mix(colour, 'cream_dark', 0.6), scale=0.5 * r, cover=0.25, edge=1, soft=1.5, alpha=0.6)

    def smoke(self, x, y, h, colour='ice', n=3, drift=0.3, alpha=0.55, seed=None):
        """chalky smoke from a chimney: a few soft, round, overlapping puffs, growing, fading and drifting downwind"""
        rr = self._r(seed)
        for i in range(n):
            t = i / max(n - 1, 1)
            rad = h * (0.1 + 0.1 * t)
            cx = x + drift * h * t ** 1.2 + rr.uniform(-0.02, 0.02) * h
            cy = y - rad * 0.7 - h * 0.4 * t
            self.fill(self.blob(cx, cy, rad, rad * 0.88, rough=0.08, seed=int(rr.integers(1 << 30))), colour,
                      angle=-20, streak=0.15, pressure=0.95, dry=0.7, dry_px=rad * 0.45, edge=1.6, soft=2.6,
                      alpha=alpha * (1 - 0.4 * t), mottle=0, skip=0.25)

    def wisp(self, x, y, h, colour='cream', sway=None, width=None, seed=None):
        """a curl of steam: a tapered S stroke rising from (x, y)"""
        k = self.k
        rr = self._r(seed)
        sway = 0.18 * h if sway is None else sway
        width = 0.08 * h if width is None else width
        s = 1 if rr.random() < 0.5 else -1
        P = [(x, y), (x + s * sway, y - 0.3 * h), (x - s * sway * 0.6, y - 0.62 * h), (x + s * sway * 0.4, y - h)]
        self.brush(P, width, colour, taper=(0.35, 0.6), dry=0.2, pressure=0.9, streak=0.3)

    def ripples(self, x, y, w, n=3, colour='ice', width=None, alpha=0.8, seed=None):
        """short light arcs on water around (x, y)"""
        k = self.k
        rr = self._r(seed)
        width = 3.2 * k if width is None else width
        for i in range(n):
            ww = w * (0.45 + 0.55 * (i + 1) / n)
            yy = y + i * 0.06 * w
            a = np.linspace(0.12 * np.pi, 0.88 * np.pi, 14)
            P = np.stack([x + ww / 2 * np.cos(a), yy + 0.05 * ww * np.sin(a)], 1)
            seg = rr.uniform(0.0, 0.25)
            P = P[int(seg * 14):] if rr.random() < 0.5 else P[:14 - int(seg * 14)]
            self.crayon(P, width, colour, taper=(0.3, 0.3), alpha=alpha, wobble=0.5)

    def footprints(self, pts, size, colour='snow_shade', depth=0.7):
        for (x, y) in pts:
            self.shadow(self.ellipse(x, y, size, size * 0.42), colour, depth=depth, edge=0.8, dry=0)

    # ================================================================== output
    def finish(self, grain=1.0, speckle=1.0, soft=0.25):
        """record the finishing (applied in render, so every stage snapshot matches; call before the first mark)"""
        self.fin = dict(grain=grain, speckle=speckle, soft=soft)
        return self

    def render(self):
        """the finished picture (the page buffer is untouched)"""
        C = self.C
        f = self.fin
        if not f: return np.clip(C, 0, 1)
        self._need()
        out = np.clip(C, 0, 1.0).copy()
        if f['grain']:
            out *= (1 + 0.03 * f['grain'] * self.G)[..., None]
        sp = f['speckle']
        if sp:
            lum = out.mean(-1)
            light = (self.SP < 0.005 * sp * (0.3 + 1.4 * (1 - lum))).astype(np.float32)
            dark = (self.SP > 1 - 0.0035 * sp * (0.3 + 1.4 * lum)).astype(np.float32)
            sg = 0.3 * self.k
            light = blur(light, sg) * 2.2; dark = blur(dark, sg) * 2.2
            out += (np.clip(light, 0, 1) * 0.2)[..., None] * (1.05 - out)
            out *= (1 - np.clip(dark, 0, 1) * 0.18)[..., None]
        if f['soft']:
            s = f['soft']
            for c in range(3): out[..., c] = out[..., c] * (1 - s) + blur(out[..., c], 0.7) * s
        return np.clip(out, 0, 1)

    def composite(self):
        out = self.render() * 255 + 0.5
        return Image.fromarray(out.astype(np.uint8))

    def stage(self, name):
        if not self.keep_stages: return
        im = self.composite()
        if self.stages_dir:
            os.makedirs(self.stages_dir, exist_ok=True)
            im.save(f'{self.stages_dir}/{self._n_stages:02d}_{name}.png', compress_level=1)
        else:
            b = io.BytesIO(); im.save(b, 'PNG', compress_level=1)
            self.stages.append((name, b.getvalue()))
        self._n_stages += 1

    def save(self, path, stages_dir=None, quality=92):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, b) in enumerate(self.stages):
                with open(f'{sd}/{i:02d}_{name}.png', 'wb') as fh: fh.write(b)
            img.save(f'{sd}/{self._n_stages:02d}_final.png', compress_level=1)
        return img
