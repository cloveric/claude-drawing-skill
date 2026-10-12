"""nocturne — 排线夜景 / Hatched Nocturne: a small night-scene print built entirely from short directional strokes
(numpy + Pillow only).

The look: a contemporary pastel / coloured-pencil nocturne printed small on cream paper. Sky, cloud, land and sea
are all laid with dense short strokes, like pastel hatching or a dry brush dragged across the sheet; the strokes of
one area all follow one "wind" (the sky streams diagonally, steam curls round its billows, the sea drags in long
horizontals), each stroke a hair different in hue and value, with fine dark gaps of the underpaint between them. The
palette is a deep indigo / navy / cold grey-blue night with exactly one warm light (red-orange); where that light
falls, more strokes are laid on top by adding light (yellow-white at the core, orange then red further out, then
the strokes of whatever it lights). Glowing filaments with bright tips, scattered sparks, a broken warm reflection
on the water, a tiny figure for scale, and the whole thing mounted as a small print: cream margins with paper tooth,
an embossed plate mark, a pencilled title bottom left and a smaller note bottom right in a thin plain face.

Physical model
  sheet       Cream paper with an equalised tooth `T` (uniform 0..1), low mottling and a few fibres. The picture area
              is underpainted with a dark ground; every mark later is clipped to the picture (a taped edge), so the
              margins stay clean. `mount()` presses a plate mark round the picture (a soft groove: dark on the top
              and left walls, a light lip at the bottom and right), `caption()` pencils the text.
  strokes     The unit of paint is one short stroke: a centreline integrated through an orientation field (angles
              mod pi, so a stroke never flips direction halfway), bent a little, outlined with a blunt landing and a
              tapering tail. Tens of thousands are rasterised at once: Pillow fills each outline with its own id into
              a 2x supersampled integer map (later ids cover earlier ones), and for every covered pixel numpy looks
              up that stroke's colour, start, direction, length and width, recovers the pixel's position along the
              stroke (u) and across it (v), and from v its bristle lane: each stroke has six lanes with their own
              value and load, lanes run dry toward the tail (`dry`), and the pigment only catches the paper where the
              tooth is below the pressure (`pressure`), so every stroke is streaky and grainy and the dark ground
              shows through in hairline gaps. Then it is box-averaged back to 1x. Within one batch the top stroke
              wins (no muddy accumulation); the layers come from several passes.
  colour      A stroke takes one colour: a paint, a ramp indexed by a value field, or any function of position; then
              its own value (`value`) and hue (`hue`, a true rotation about the grey axis) jitter, and `lit` adds the
              light map at its centre, so strokes inside the glow are themselves warm.
  light       Lights are registered (`light()` for a point, `light_from()` for an emitting mask such as lava
              threads) and summed into a light map. `glow()` lays light strokes: they land with a probability that
              follows (light x receptivity), coloured by the light map, so a glow is many warm strokes thinning out
              into the dark, never a smooth blob. Receptivity says what catches the light: the undersides of steam
              billows most, sky a little, slopes near the lava. Air and glare are added (screen); a lit surface is
              painted as light x receptivity (`blend='paint'`) -- adding orange to a blue-grey cloud turns it pink,
              painting it turns it red-orange -- and `whiten` pulls the hottest of those toward a warm white.
  source      `source()` is the hot point: a tight cluster of white-yellow strokes, a fan of orange then red strokes
              radiating from it, a tiny white core and a small bloom.
  filaments   `threads()` grows braided rivulets: a walk with momentum that keeps turning toward its end (and down
              the fall line away from a summit), so it meanders instead of zig-zagging like lightning; sub-strands
              drift apart toward the end, low-angle side branches peel off and fade out or stop in a bead, and the
              intensity is patchy (crusted stretches), hottest at the fronts.
              `filaments()` draws them as emission into a 2x float buffer (thin lines whose intensity follows crusted
              patches), adds a tight halo, lays light strokes on whatever they light, and puts bright beads on the
              tips. `sparks()` throws ballistic sparks as short fading streaks with a hot head.
  water       `reflect()` paints horizontal strokes on the sea whose colour is the mirrored picture above the
              waterline (stretched by the waves, pushed sideways by ripples, darkened toward the sea colour), and
              only where that mirror is bright, so the reflection is broken into strokes; `glitter()` is the column
              a light on the waterline throws toward the viewer: hot near the source, widening and breaking up.
  figures     `figure()` is a tiny seated silhouette (a few dozen px): head, torso, bent legs, arms, an accent
              (scarf, hat) and a warm rim on the side that faces the light. `silhouette()` paints a dark mass (rock,
              island, mountain) with strokes and an optional lit rim.
  finish      `render()` adds a restrained bloom round the brightest light and a fine pastel grain.

API (canvas pixel coordinates; angles of fields in radians, `flow()` takes degrees; colours are PAINTS names,
     '#rrggbb' or RGB triples; ramps are RAMPS names or lists)
  surface    Nocturne(W, H, seed, keep_stages, stages_dir); sheet(box, paper, ground); poly(pts) / ellipse(cx, cy,
             rx, ry) / blob(cx, cy, rx, ry, rough) / below(xs, ys) masks
  fields     flow(angle_deg, turb, scale); radial(cx, cy, offset, turb); contour(density, sigma); blend(f1, f2, w);
             value(top, bottom, y0, y1, mottle, scale) value fields
  strokes    hatch(region, field, colour, length, width, density, jitter, bend, value, hue, alpha, pressure, dry,
             lanes, lit, mode='paint'|'light', taper, clip)
  light      light(x, y, r, colour, power, squash); light_from(emission, spread, colour, power); lightmap();
             glow(receptivity, field, length, width, density, power, reach, blend='light'|'paint', ambient,
             whiten); source(x, y, r, power, field, squash, core)
  threads    threads(start, ends, wander, strands, spread, branches, branch_len, width, fall, heat) -> paths;
             filaments(paths, gain, halo, light, receptivity, field, beads); sparks(x, y, n, spread, speed);
             embers(region, n); stars(region, n, size, bright)
  water      reflect(waterline, region, src, stretch, ripple, darken, thr, ...); glitter(x, y_water, y_end, w0, w1)
  figures    silhouette(mask, ramp, field, rim, rim_from); figure(x, y, h, facing, accent, legs, rim_from)
  finish     mount(plate, depth); caption(text, x, y, size, anchor, weight); bloom(amount); grain(amount);
             render(); composite(); stage(name); save(path, stages_dir)

    import sys; sys.path.insert(0, 'lib')
    from nocturne import Nocturne
    n = Nocturne(1920, 1080, seed=3)
    n.sheet((80, 56, 1840, 966))
    sky = n.below(None, 600, invert=True)
    n.hatch(sky, n.flow(14), ('sky', n.value(0.15, 0.7, 56, 600)), density=2.2)
    n.light(1150, 610, 240, 'ember', 1.2); n.source(1150, 610, 40)
    n.mount(); n.caption('Forty seconds', 80, 1030, 27); n.save('night.jpg')
"""
import io
import os
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, noise2d, smoothstep, spline, blob_pts, load_font


PAINTS = {
    'paper': '#e8dfcb', 'pencil': '#57544f', 'ground': '#0d1331',
    'night': '#111842', 'indigo': '#18225a', 'navy': '#15204c', 'dusk': '#2a386b', 'haze': '#46557f',
    'starlight': '#9eaed6', 'mist': '#7383b0', 'slate': '#363f62', 'steam': '#585e7c', 'steam_lit': '#dcc6b3',
    'rock': '#0a0d1b', 'rock_lit': '#232842', 'sea': '#13204a', 'sea_deep': '#0b1334', 'glint': '#8ea1d0',
    'blood': '#a51f0c', 'ember': '#ff5a1a', 'lava': '#ff8a2a', 'flame': '#ffbf5e', 'core': '#fff3d2',
    'scarf': '#e8502a', 'star': '#eef2ff', 'warmstar': '#ffe6c4',
}

RAMPS = {
    'fire':  ['#2a0602', '#781505', '#c42e0a', '#f25814', '#ff8a2a', '#ffc05c', '#ffe8a6', '#fffbea'],
    'ember': ['#3a0804', '#7d1607', '#b8280a', '#e2470f', '#f86e1d', '#ff9a3c'],
    'sky':   ['#0b1130', '#11183e', '#17204a', '#1f2a55', '#2c3863', '#414f78', '#66769c', '#95a2c2'],
    'sea':   ['#080d27', '#0d1434', '#121c41', '#1a264e', '#25335c', '#364772', '#5a6c98', '#8c9cc1'],
    'steam': ['#161b38', '#232947', '#343a5a', '#4d5371', '#6c708b', '#9192a8'],
    'land':  ['#050714', '#080b1d', '#0c1025', '#11162e', '#191f39', '#232a47'],
    'isle':  ['#0c1230', '#111839', '#172042', '#1e284c', '#273257', '#323e63'],
}

NL = 6                                    # bristle lanes per stroke


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def ramp(spec):
    """a RAMPS name or a list of colours -> (K, 3) array, dark -> light"""
    if isinstance(spec, np.ndarray): return spec.astype(np.float32)
    if isinstance(spec, str): spec = RAMPS[spec]
    return np.stack([hexc(c) for c in spec]).astype(np.float32)


def ramp_at(R, l):
    """colour at 0..1 positions l along ramp R (vectorised)"""
    l = np.clip(np.asarray(l, np.float32), 0, 1) * (len(R) - 1)
    i = np.minimum(l.astype(np.int32), len(R) - 2)
    f = (l - i)[..., None]
    return R[i] * (1 - f) + R[i + 1] * f


def hue_rotate(c, theta):
    """rotate RGB colours (N, 3) about the grey axis by theta radians (N,): a real hue shift, value kept"""
    cs, sn = np.cos(theta)[:, None], np.sin(theta)[:, None]
    m = c.mean(1, keepdims=True)
    cr = np.stack([c[:, 2] - c[:, 1], c[:, 0] - c[:, 2], c[:, 1] - c[:, 0]], 1) / np.sqrt(3)
    return (c * cs + cr * sn + m * (1 - cs)).astype(np.float32)


def _equalise(a):
    """rank-equalise to a uniform 0..1 distribution"""
    flat = a.ravel()
    o = np.argsort(flat, kind='stable')
    out = np.empty(flat.size, np.float32)
    out[o] = np.linspace(0, 1, flat.size, dtype=np.float32)
    return out.reshape(a.shape)


def _lookup(field, x, y):
    if np.ndim(field) == 0: return np.full(len(x), float(field), np.float32)
    H, W = field.shape[:2]
    return field[np.clip(y.astype(np.int32), 0, H - 1), np.clip(x.astype(np.int32), 0, W - 1)]


def _font(weight, size):
    """a thin plain face (no script / handwriting): Helvetica Neue Light / Thin, Avenir Light, DejaVu ExtraLight..."""
    cands = {'light': [('/System/Library/Fonts/HelveticaNeue.ttc', 7), ('/System/Library/Fonts/Avenir.ttc', 6),
                       ('/usr/share/fonts/**/DejaVuSans-ExtraLight.ttf', 0), ('/usr/share/fonts/**/Lato-Light.ttf', 0),
                       ('C:/Windows/Fonts/segoeuil.ttf', 0), ('C:/Windows/Fonts/arial.ttf', 0)],
             'thin': [('/System/Library/Fonts/HelveticaNeue.ttc', 12), ('/System/Library/Fonts/Avenir Next.ttc', 10),
                      ('/usr/share/fonts/**/DejaVuSans-ExtraLight.ttf', 0), ('/usr/share/fonts/**/Lato-Hairline.ttf', 0),
                      ('C:/Windows/Fonts/segoeuisl.ttf', 0), ('C:/Windows/Fonts/arial.ttf', 0)]}
    env = os.environ.get('INKPAINT_FONT_' + weight.upper())
    if env and os.path.exists(env): return ImageFont.truetype(env, int(size))
    for pat, idx in cands.get(weight, cands['light']):
        for p in glob.glob(pat, recursive=True):
            try: return ImageFont.truetype(p, int(size), index=idx)
            except OSError: pass
    return load_font('sans', size)


class Nocturne:
    PAINTS = PAINTS
    RAMPS = RAMPS

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = hexc('paper')
        r = np.random.default_rng(seed + 101)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.6)
        g2 = noise2d(H, W, 2.4, 2, seed + 102)
        g3 = noise2d(H, W, 8.0, 2, seed + 103)
        self.T = _equalise(0.55 * z(g1) + 0.35 * z(g2) + 0.2 * z(g3))       # paper tooth, uniform 0..1
        self.TD = None                                                        # tooth dragged along 8 directions (lazy)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.pic = None; self.box = (0, 0, W, H)
        self.lights = []; self._L = None
        self.bloom_amt = 0.0; self.grain_amt = 0.0
        self.n_strokes = 0

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== masks
    def poly(self, pts, smooth=False, ss=2):
        """filled polygon -> canvas-sized float mask (smooth=True runs a Catmull-Rom spline through the points)"""
        P = spline(pts, 10) if smooth else np.asarray(pts, np.float32)
        im = Image.new('L', (self.W * ss, self.H * ss), 0)
        ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in P], fill=255)
        return np.asarray(im.resize((self.W, self.H), Image.BOX), np.float32) / 255

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        ry = rx if ry is None else ry
        c, s = np.cos(rot), np.sin(rot)
        dx, dy = self.XX - cx, self.YY - cy
        u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
        d = np.sqrt(u * u + v * v)
        return np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1).astype(np.float32)

    def blob(self, cx, cy, rx, ry, rough=0.12, seed=None, rot=0.0):
        return self.poly(blob_pts(cx, cy, rx, ry, rough, 120, int(self._r(seed).integers(1 << 30)), rot))

    def below(self, xs, ys, invert=False):
        """mask of everything below a line through (xs, ys) (spline), or a constant y if xs is None"""
        if xs is None:
            m = np.clip(self.YY - float(ys) + 0.5, 0, 1)
        else:
            x = np.arange(self.W, dtype=np.float32)
            P = spline(np.stack([xs, ys], 1), 12)
            o = np.argsort(P[:, 0])
            yl = np.interp(x, P[o, 0], P[o, 1]).astype(np.float32)
            m = np.clip(self.YY - yl[None] + 0.5, 0, 1)
        return (1 - m if invert else m).astype(np.float32)

    def _mask(self, region):
        if isinstance(region, np.ndarray): return region.astype(np.float32, copy=False)
        x0, y0, x1, y1 = (int(round(v)) for v in region)
        M = np.zeros((self.H, self.W), np.float32)
        M[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1
        return M

    # ================================================================== fields
    def flow(self, angle=0.0, turb=10.0, scale=260.0, seed=None):
        """orientation field: `angle` degrees (screen y down: positive tilts down to the right), +-turb degrees
        of low-frequency wander at `scale` px"""
        n = noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5
        return np.deg2rad(angle + 2 * turb * n).astype(np.float32)

    def radial(self, cx, cy, offset=0.0, turb=6.0, scale=120.0, seed=None):
        """strokes pointing away from (cx, cy) (fall lines of a cone, rays of a light), offset in degrees"""
        a = np.arctan2(self.YY - cy, self.XX - cx) + np.deg2rad(offset)
        if turb:
            a = a + np.deg2rad(2 * turb * (noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5))
        return a.astype(np.float32)

    def contour(self, density, sigma=6.0):
        """strokes running along the contours of a density (round a billow, along a ridge)"""
        d = blur(density, sigma)
        gy, gx = np.gradient(d)
        return (np.arctan2(gy, gx) + np.pi / 2).astype(np.float32)

    @staticmethod
    def blend(f1, f2, w):
        """blend two orientation fields (doubled-angle average, so 0 and pi are the same orientation)"""
        w = np.asarray(w, np.float32)
        c = (1 - w) * np.cos(2 * f1) + w * np.cos(2 * f2)
        s = (1 - w) * np.sin(2 * f1) + w * np.sin(2 * f2)
        return (0.5 * np.arctan2(s, c)).astype(np.float32)

    def value(self, top=0.15, bottom=0.7, y0=0, y1=None, mottle=0.08, scale=200.0, seed=None):
        """a 0..1 value field: a vertical ramp from `top` at y0 to `bottom` at y1, with low-frequency mottling"""
        y1 = self.H if y1 is None else y1
        t = np.clip((self.YY - y0) / max(1, y1 - y0), 0, 1)
        v = top + (bottom - top) * t
        if mottle:
            v = v + 2 * mottle * (noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5)
        return v.astype(np.float32)

    # ================================================================== the sheet
    def sheet(self, box=None, paper='paper', ground='ground', edge=0.5, fibres=220, seed=None):
        """cream paper with tooth, mottling and fibres; the picture area `box` underpainted with a dark ground"""
        H, W = self.H, self.W
        r = self._r(seed)
        if box is None:
            mx, my = int(W * 0.042), int(H * 0.052)
            box = (mx, my, W - mx, H - int(H * 0.105))
        self.box = tuple(int(v) for v in box)
        x0, y0, x1, y1 = self.box
        mot = noise2d(H, W, 150, 4, int(r.integers(1 << 30))) - 0.5
        C = hexc(paper)[None, None] * (1 + 0.03 * mot[..., None] - 0.022 * (self.T[..., None] - 0.5))
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        for _ in range(fibres):
            px, py = r.uniform(0, W), r.uniform(0, H)
            a = r.uniform(0, np.pi); L = r.uniform(6, 26)
            pts = [(px + np.cos(a) * L * t + r.normal(0, 1.2), py + np.sin(a) * L * t + r.normal(0, 1.2)) for t in np.linspace(-0.5, 0.5, 5)]
            d.line(pts, fill=int(r.uniform(40, 110)), width=1)
        fib = blur(np.asarray(im, np.float32) / 255, 0.5)
        C = C * (1 - 0.05 * fib[..., None])
        # the taped picture edge: crisp, with a hair of wobble
        wob_x = fbm1d(H, 40, 3, int(r.integers(1 << 30))) * edge
        wob_y = fbm1d(W, 40, 3, int(r.integers(1 << 30))) * edge
        X, Y = self.XX, self.YY
        dl = X - (x0 + wob_x[:, None]); dr = (x1 + wob_x[::-1, None]) - X
        dt = Y - (y0 + wob_y[None]); db = (y1 + wob_y[None, ::-1]) - Y
        self.pic = np.clip(np.minimum(np.minimum(dl, dr), np.minimum(dt, db)) + 0.5, 0, 1).astype(np.float32)
        g = hexc(ground)[None, None] * (1 + 0.08 * mot[..., None])
        self.C = (C * (1 - self.pic[..., None]) + g * self.pic[..., None]).astype(np.float32)

    # ================================================================== strokes
    def _dragged(self, drag=6):
        """the tooth smeared along 8 stroke directions: a dry stroke skips the paper in short streaks along itself"""
        if self.TD is None:
            T = self.T
            TD = np.empty((8, self.H, self.W), np.float32)
            ks = np.arange(-drag, drag + 1); wk = 1.0 - np.abs(ks) / (drag + 1.0)
            for b in range(8):
                a = np.pi * b / 8
                acc = np.zeros_like(T)
                for k, w in zip(ks, wk):
                    acc += w * np.roll(T, (int(round(k * np.sin(a))), int(round(k * np.cos(a)))), axis=(0, 1))
                TD[b] = _equalise(0.3 * T + 0.7 * acc / wk.sum())
            self.TD = TD
        return self.TD

    def _sizes(self, spec, x, y, r):
        n = len(x)
        if callable(spec):
            return (np.asarray(spec(x, y), np.float32) * r.uniform(0.75, 1.25, n)).astype(np.float32)
        if np.ndim(spec) == 0: return np.full(n, float(spec), np.float32) * r.uniform(0.85, 1.15, n).astype(np.float32)
        return r.uniform(spec[0], spec[1], n).astype(np.float32)

    def _colours(self, spec, x, y, r):
        n = len(x)
        if callable(spec): return np.asarray(spec(x, y), np.float32).reshape(n, 3).copy()
        if isinstance(spec, tuple) and len(spec) == 2 and not np.isscalar(spec[1]):
            R = ramp(spec[0]); f = spec[1]
            v = f(x, y) if callable(f) else _lookup(f, x, y)
            return ramp_at(R, v).astype(np.float32)
        return np.broadcast_to(hexc(spec), (n, 3)).astype(np.float32).copy()

    def _centrelines(self, x, y, L, field, jit, bend, k):
        n = len(x)
        P = np.zeros((n, k, 2), np.float32)
        c = k // 2
        P[:, c, 0] = x; P[:, c, 1] = y
        st = L / (k - 1)
        a0 = _lookup(field, x, y) + jit
        d0 = np.stack([np.cos(a0), np.sin(a0)], 1).astype(np.float32)
        for sgn in (1, -1):
            px, py = x.copy(), y.copy()
            prev = d0 * sgn
            for j in range(1, k - c if sgn > 0 else c + 1):
                a = _lookup(field, px, py) + jit + sgn * bend * j
                v = np.stack([np.cos(a), np.sin(a)], 1).astype(np.float32)
                flip = (v * prev).sum(1) < 0
                v[flip] *= -1
                px = px + v[:, 0] * st; py = py + v[:, 1] * st
                P[:, c + sgn * j, 0] = px; P[:, c + sgn * j, 1] = py
                prev = v
        return P

    @staticmethod
    def _outline(P, Wd, taper):
        n, k, _ = P.shape
        t = np.linspace(0, 1, k, dtype=np.float32)
        Tg = np.gradient(P, axis=1)
        Tg /= np.linalg.norm(Tg, axis=2, keepdims=True) + 1e-6
        Nn = np.stack([-Tg[..., 1], Tg[..., 0]], -1)
        s0, s1 = taper
        prof = np.minimum(np.clip(s0 + (1 - s0) * t / 0.22, 0, 1), np.clip(s1 + (1 - s1) * (1 - t) / 0.5, 0, 1)) ** 0.8
        hw = (Wd[:, None] * 0.5) * prof[None]
        left = P + Nn * hw[..., None]; right = P - Nn * hw[..., None]
        return np.concatenate([left, right[:, ::-1]], 1)

    def hatch(self, region, field=0.0, colour='indigo', length=(16, 34), width=(2.2, 3.4), density=1.0,
              jitter=0.1, bend=0.06, value=0.08, hue=0.04, alpha=0.95, pressure=0.95, dry=0.35, lanes=0.14,
              lit=0.0, mode='paint', taper=(0.5, 0.12), clip=None, seed=None):
        """lay strokes over `region` (mask = landing probability, or a box) following orientation `field`.
        density ~ how many times the strokes would tile the region; length / width: (lo, hi), a number or
        f(x, y); colour: paint, (ramp, value field or f(x, y)) or f(x, y) -> (N, 3); value / hue: per-stroke
        jitter; pressure: how far the pigment sinks into the tooth (1 = solid); dry: lanes running out toward the
        tail; lanes: value spread between bristle lanes; lit: add the light map; mode 'paint' covers,
        'light' adds light (screen)."""
        r = self._r(seed)
        M = self._mask(region)
        rows = np.flatnonzero(M.max(1) > 0.004); cols_ = np.flatnonzero(M.max(0) > 0.004)
        if not len(rows) or not len(cols_): return 0
        bx0, bx1, by0, by1 = cols_[0], cols_[-1] + 1, rows[0], rows[-1] + 1
        area = float(M[by0:by1, bx0:bx1].sum())
        if area < 1: return 0
        px_ = r.uniform(bx0, bx1, 4000).astype(np.float32); py_ = r.uniform(by0, by1, 4000).astype(np.float32)
        keep = r.random(4000) < _lookup(M, px_, py_)
        if keep.sum() < 10: keep[:] = True
        Lm = float(self._sizes(length, px_[keep], py_[keep], r).mean()); Wm = float(self._sizes(width, px_[keep], py_[keep], r).mean())
        n = int(density * area / (0.62 * Lm * Wm))
        if n < 1: return 0
        cand = int(n * (bx1 - bx0) * (by1 - by0) / area * 1.02) + 8
        x = r.uniform(bx0, bx1, cand).astype(np.float32); y = r.uniform(by0, by1, cand).astype(np.float32)
        ok = r.random(cand) < _lookup(M, x, y)
        x, y = x[ok], y[ok]
        n = len(x)
        if not n: return 0
        L = self._sizes(length, x, y, r); Wd = self._sizes(width, x, y, r)
        cols = self._colours(colour, x, y, r)
        if value: cols *= (1 + value * r.normal(0, 1, n).astype(np.float32))[:, None]
        if hue: cols = hue_rotate(cols, (hue * r.normal(0, 1, n)).astype(np.float32))
        if lit: cols += lit * _lookup(self.lightmap(), x, y)
        cols = np.clip(cols, 0, 1)
        k = 5 if Lm < 48 else 7
        P = self._centrelines(x, y, L, field, (jitter * r.normal(0, 1, n)).astype(np.float32),
                              (bend * r.normal(0, 1, n)).astype(np.float32), k)
        poly = self._outline(P, Wd, taper)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,)) * r.uniform(0.88, 1.0, n).astype(np.float32)
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (n,)) * r.uniform(0.95, 1.03, n).astype(np.float32)
        self._raster(poly, P[:, 0], P[:, -1], Wd, cols, al, pr, dry, lanes, mode, clip, r)
        self.n_strokes += n
        return n

    def _raster(self, poly, s, e, Wd, cols, al, pr, dry, lanes, mode, clip, r, ss=2):
        n = len(poly)
        lo = poly.reshape(-1, 2).min(0); hi = poly.reshape(-1, 2).max(0)
        x0, y0 = max(0, int(np.floor(lo[0])) - 1), max(0, int(np.floor(lo[1])) - 1)
        x1, y1 = min(self.W, int(np.ceil(hi[0])) + 2), min(self.H, int(np.ceil(hi[1])) + 2)
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        Q = ((poly - np.array([x0, y0], np.float32)) * ss).reshape(n, -1).tolist()
        for i, q in enumerate(Q): d.polygon(q, fill=i + 1)
        ids = np.asarray(im)
        dv = e - s
        Ls = np.linalg.norm(dv, axis=1) + 1e-3
        dv = dv / Ls[:, None]
        tab = np.zeros((n + 1, 12), np.float32)
        tab[1:, :3] = cols; tab[1:, 3] = al; tab[1:, 4:6] = s; tab[1:, 6:8] = dv
        tab[1:, 8] = 1 / Ls; tab[1:, 9] = 1 / np.maximum(Wd, 0.5); tab[1:, 10] = pr; tab[1:, 11] = dry
        BIN = np.zeros(n + 1, np.int32)
        BIN[1:] = np.round(np.mod(np.arctan2(dv[:, 1], dv[:, 0]), np.pi) / np.pi * 8).astype(np.int32) % 8
        TD = self._dragged()
        LN = np.zeros((n + 1, NL), np.float32); LN[1:] = r.random((n, NL))
        Cs = self.C[y0:y1, x0:x1]
        CH = max(4, int(6e5 / (w * ss * ss)))
        xx = (x0 + (np.arange(w * ss, dtype=np.float32) + 0.5) / ss)[None, :]
        for r0 in range(0, h, CH):
            r1 = min(h, r0 + CH)
            sub = ids[r0 * ss:r1 * ss]
            if not sub.any(): continue
            tb = tab[sub]
            yy = (y0 + (np.arange(r0 * ss, r1 * ss, dtype=np.float32) + 0.5) / ss)[:, None]
            qx = xx - tb[..., 4]; qy = yy - tb[..., 5]
            u = np.clip((qx * tb[..., 6] + qy * tb[..., 7]) * tb[..., 8], 0, 1)
            v = (qy * tb[..., 6] - qx * tb[..., 7]) * tb[..., 9] + 0.5
            li = np.clip((v * NL).astype(np.int32), 0, NL - 1)
            lv = LN[sub, li]
            cover = np.clip((lv - tb[..., 11] * u ** 1.5) * 7 + 0.5, 0, 1)
            iy = (y0 + np.arange(r0 * ss, r1 * ss) // ss)[:, None]; ix = (x0 + np.arange(w * ss) // ss)[None, :]
            Tt = TD[BIN[sub], iy, ix]
            grain = np.clip((tb[..., 10] * (0.97 + 0.06 * lv) - Tt) * 9 + 0.5, 0, 1)
            A = tb[..., 3] * cover * grain * (1 - 0.22 * u * u)
            Pm = tb[..., :3] * ((1 + lanes * (lv - 0.5) * 2) * A)[..., None]
            hh = r1 - r0
            A1 = A.reshape(hh, ss, w, ss).mean((1, 3))
            P1 = Pm.reshape(hh, ss, w, ss, 3).mean((1, 3))
            f = None
            if self.pic is not None: f = self.pic[y0 + r0:y0 + r1, x0:x1]
            if clip is not None:
                cf = clip[y0 + r0:y0 + r1, x0:x1]
                f = cf if f is None else f * cf
            if f is not None: A1 = A1 * f; P1 = P1 * f[..., None]
            seg = Cs[r0:r1]
            if mode == 'light':
                seg += P1 * (1 - seg)
            else:
                seg[:] = seg * (1 - A1[..., None]) + P1

    # ================================================================== light
    def light(self, x, y, r, colour='ember', power=1.0, squash=1.0):
        """register a point light (falloff 1 / (1 + (d / r)^2)^1.2; squash < 1 flattens it vertically)"""
        self.lights.append(('pt', float(x), float(y), float(r), hexc(colour), float(power), float(squash)))
        self._L = None

    def light_from(self, emission, spread=20.0, colour='ember', power=1.0):
        """register an emitting mask (lava threads, a lit window) as a soft area light"""
        b = blur(emission.astype(np.float32), spread)
        b = b / (b.max() + 1e-6)
        self.lights.append(('em', b, hexc(colour), float(power)))
        self._L = None

    def lightmap(self):
        if self._L is None:
            L = np.zeros((self.H, self.W, 3), np.float32)
            for lt in self.lights:
                if lt[0] == 'pt':
                    _, x, y, rr, col, pw, sq = lt
                    d2 = ((self.XX - x) / rr) ** 2 + ((self.YY - y) / (rr * sq)) ** 2
                    L += (pw / (1 + d2) ** 1.2)[..., None] * col
                else:
                    _, b, col, pw = lt
                    L += (pw * b)[..., None] * col
            self._L = L
        return self._L

    def glow(self, receptivity, field=0.0, length=(12, 28), width=(2.0, 3.2), density=1.2, power=1.0, reach=1.6,
             value=0.14, hue=0.05, pressure=0.86, dry=0.45, alpha=1.0, blend='light', ambient=None, whiten=0.0,
             seed=None, **kw):
        """light strokes: land where light x receptivity is high (thinning out into the dark), coloured by the light
        map -- a glow made of strokes. blend='light' adds them (screen: air, glare); blend='paint' lays them as lit
        paint, colour = light x receptivity (+ `ambient`), so a lit cloud turns red-orange instead of the pink you
        get from adding orange to blue-grey; `whiten` pulls the most strongly lit strokes toward a warm white (a
        white thing near a hot light)"""
        Lm = self.lightmap()
        rec = self._mask(receptivity) if not isinstance(receptivity, np.ndarray) else receptivity
        prob = np.clip(rec * Lm.max(-1) * reach, 0, 1) ** 0.75
        amb = None if ambient is None else hexc(ambient)

        def col(x, y):
            c = _lookup(Lm, x, y) * _lookup(rec, x, y)[:, None] * power
            if whiten:
                mx = c.max(1, keepdims=True)
                c = c + (np.minimum(mx, 1.0) * np.array([1.0, 0.93, 0.84], np.float32) - c) * whiten * smoothstep(0.7, 1.6, mx)
            if amb is not None: c = c + amb * np.clip(1 - c.max(1, keepdims=True) * 1.5, 0, 1)
            return np.clip(c, 0, 1)
        return self.hatch(prob, field, col, length, width, density, value=value, hue=hue, pressure=pressure, dry=dry,
                          alpha=alpha, mode='light' if blend == 'light' else 'paint', seed=seed, **kw)

    def source(self, x, y, r=40.0, power=1.0, field=None, squash=0.6, core=1.0, seed=None):
        """the hot point: a fan of red -> orange -> yellow-white light strokes, a tiny white core, a small bloom"""
        rr = self._r(seed)
        f = self.radial(x, y, turb=10, seed=int(rr.integers(1 << 30))) if field is None else field
        R = ramp('fire')
        dist = np.sqrt((self.XX - x) ** 2 + ((self.YY - y) / squash) ** 2)
        for k, (reach, dens, ln, wd, lo) in enumerate([(3.2, 1.0, (10, 26), (1.8, 3.0), 0.28), (2.0, 1.3, (8, 20), (1.6, 2.6), 0.42),
                                                      (1.1, 1.6, (5, 13), (1.4, 2.2), 0.58), (0.55, 2.0, (3, 8), (1.2, 2.0), 0.72)]):
            prob = np.clip(1 - dist / (r * reach), 0, 1) ** 1.3

            def col(xs, ys, reach=reach, lo=lo):
                dd = _lookup(dist, xs, ys) / (r * reach)
                return ramp_at(R, lo + (1 - lo) * (1 - dd) ** 1.6) * power
            self.hatch(prob, f, col, ln, wd, dens, jitter=0.25, value=0.12, hue=0.03, pressure=0.85, dry=0.4,
                       mode='light', seed=int(rr.integers(1 << 30)))
        cr = np.exp(-(dist / (r * 0.11)) ** 2) * core
        halo = blur(np.clip(1 - dist / (r * 0.8), 0, 1) ** 2, r * 0.25)
        add = cr[..., None] * hexc('core') * 0.9 + halo[..., None] * hexc('lava') * 0.18 * power * core
        if self.pic is not None: add *= self.pic[..., None]
        self.C += add * (1 - self.C)

    # ================================================================== threads, filaments, sparks, stars
    def _walk(self, p, target, step, wander, fall, r, max_len=None):
        """a walk with momentum that keeps turning toward `target` (and away from `fall`, a summit, if given):
        meanders like a rivulet, never zig-zags like a spark"""
        p = np.asarray(p, np.float32).copy(); tgt = np.asarray(target, np.float32)
        d = tgt - p; d /= np.linalg.norm(d) + 1e-6
        pts = [p.copy()]; turn = 0.0; L = 0.0
        D0 = float(np.linalg.norm(tgt - p))
        for _ in range(4000):
            to = tgt - p; dist = float(np.linalg.norm(to))
            if dist < step * 1.5 or (max_len and L >= max_len): break
            to /= dist
            if fall is not None:
                fl = p - np.asarray(fall, np.float32); fl /= np.linalg.norm(fl) + 1e-6
                k = 0.4 * min(1.0, dist / (0.5 * D0 + 1e-6))
                to = (1 - k) * to + k * fl; to /= np.linalg.norm(to) + 1e-6
            turn = 0.85 * turn + r.normal(0, wander * 0.035)
            pull = 0.16 + 0.3 * (1 - min(1.0, dist / (D0 + 1e-6)))
            d = (1 - pull) * d + pull * to
            c, s_ = np.cos(turn), np.sin(turn)
            d = np.array([d[0] * c - d[1] * s_, d[0] * s_ + d[1] * c], np.float32); d /= np.linalg.norm(d) + 1e-6
            p = p + d * step; L += step
            pts.append(p.copy())
        if not max_len: pts.append(tgt)
        return np.array(pts, np.float32)

    def threads(self, start, ends, wander=1.0, strands=3, spread=4.0, branches=8, branch_len=(30, 110),
                width=(1.6, 1.1), step=2.5, fall=None, heat=(0.35, 0.8), seed=None):
        """meandering, braided paths from `start` to each of `ends`; returns a list of path dicts
        {'pts', 'w': (w0, w1), 'i': intensity per point, 'tip': bead brightness at the end (0 = fades out)}.
        Sub-strands drift apart and cross (a braid); low-angle side branches peel off and fade or stop in a bead;
        intensity is patchy (crusted stretches) between heat[0] and heat[1], hottest at the fronts."""
        r = self._r(seed)
        out = []
        for e in ends:
            main = self._walk(start, e, step, wander, fall, r)
            m = len(main)
            t = np.linspace(0, 1, m, dtype=np.float32)
            tg = np.gradient(main, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
            nn = np.stack([-tg[:, 1], tg[:, 0]], 1)
            crust = smoothstep(-0.3, 0.3, fbm1d(m, max(4, m / 6), 3, int(r.integers(1 << 30))))
            for s_ in range(strands):
                so = fbm1d(m, max(4, m / 4), 2, int(r.integers(1 << 30))) * spread * (0.2 + 1.3 * t) * (s_ > 0)
                pts = main + nn * so[:, None]
                it = (heat[0] + (heat[1] - heat[0]) * crust) * (0.5 + 0.5 * smoothstep(0.0, 0.08, t)) * r.uniform(0.8, 1.0)
                it = it * (1 + 0.45 * smoothstep(0.9, 1.0, t)) * (1.0 if s_ == 0 else r.uniform(0.6, 0.85))
                out.append({'pts': pts, 'w': (width[0] * (1 if s_ == 0 else 0.7), width[1] * (1 if s_ == 0 else 0.7)),
                            'i': it.astype(np.float32), 'tip': 1.0 if s_ == 0 else r.uniform(0.0, 0.6)})
            for _ in range(max(0, branches // max(1, len(ends)))):
                i0 = int(r.uniform(0.15, 0.85) * (m - 1))
                ang = np.arctan2(tg[i0, 1], tg[i0, 0]) + r.choice([-1, 1]) * r.uniform(0.18, 0.5)
                bl = r.uniform(*branch_len)
                tgt = main[i0] + np.array([np.cos(ang), np.sin(ang)], np.float32) * bl
                pts = self._walk(main[i0], tgt, step, wander * 1.2, fall, r, max_len=bl)
                mb = len(pts)
                if mb < 3: continue
                tt = np.linspace(0, 1, mb, dtype=np.float32)
                bead = r.random() < 0.5
                it = (heat[0] + (heat[1] - heat[0]) * 0.6) * r.uniform(0.6, 0.95) * (1 - (0 if bead else 1) * smoothstep(0.45, 1.0, tt))
                out.append({'pts': pts, 'w': (width[1] * 0.8, width[1] * 0.5), 'i': it.astype(np.float32),
                            'tip': r.uniform(0.5, 0.9) if bead else 0.0})
        return out

    def _emission(self, paths, ss=2):
        im = Image.new('F', (self.W * ss, self.H * ss), 0.0)
        d = ImageDraw.Draw(im)
        for p in sorted(paths, key=lambda p: float(np.mean(p['i']))):
            P = p['pts'] * ss; it = p['i']; m = len(P)
            ws = np.linspace(p['w'][0], p['w'][1], m) * ss
            for j in range(m - 1):
                d.line([tuple(P[j]), tuple(P[j + 1])], fill=float(0.5 * (it[j] + it[j + 1])), width=max(1, int(round(ws[j]))))
        E = np.asarray(im, np.float32).reshape(self.H, ss, self.W, ss).mean((1, 3))
        return E

    def _emit(self, E, gain=1.0, halo=1.0, colour_ramp='fire'):
        """composite an emission buffer: a tight halo, then the hot lines (screen)"""
        R = ramp(colour_ramp)
        h1 = blur(E, 1.5); h2 = blur(E, 4.5)
        add = (np.clip(h1 * 0.9 * halo, 0, 1)[..., None] * hexc('ember') * 0.45
               + np.clip(h2 * 0.9 * halo, 0, 1)[..., None] * hexc('blood') * 0.4)
        lvl = np.clip(E * gain, 0, 1)
        add = add + ramp_at(R, 0.3 + 0.62 * lvl ** 1.4) * np.clip(E * gain * 2.0, 0, 1)[..., None]
        add = np.clip(add, 0, 1)
        if self.pic is not None: add *= self.pic[..., None]
        self.C += add * (1 - self.C)

    def filaments(self, paths, gain=1.0, halo=1.0, light=0.0, receptivity=None, field=0.0, beads=0.35, seed=None):
        """glowing threads: light strokes on what they light (if `light`), a tight halo, hot lines, bright tips"""
        r = self._r(seed)
        E = self._emission(paths)
        if light:
            rec = np.ones((self.H, self.W), np.float32) if receptivity is None else receptivity
            g = blur(E, 14.0); g = g / (g.max() + 1e-6)
            prob = np.clip(g * rec * 2.2, 0, 1) ** 0.8
            R = ramp('ember')

            def col(x, y):
                gv = _lookup(g, x, y)
                return ramp_at(R, 0.2 + 0.8 * np.clip(gv * 1.6, 0, 1)) * (light * np.clip(gv * 2.0, 0, 1))[:, None]
            self.hatch(prob, field, col, (8, 22), (1.6, 2.8), 1.0, jitter=0.2, value=0.15, pressure=0.85, dry=0.45,
                       mode='light', seed=int(r.integers(1 << 30)))
        self._emit(E, gain, halo)
        # tips and beads: small hot dots
        T = np.zeros((self.H, self.W), np.float32)
        for p in paths:
            P = p['pts']
            if p['tip'] > 0: self._dot(T, P[-1][0], P[-1][1], 1.4 + 1.2 * p['tip'], p['tip'] * 1.2)
            nb = r.poisson(beads * len(P) / 25)
            for _ in range(nb):
                j = int(r.integers(0, len(P)))
                self._dot(T, P[j][0] + r.normal(0, 1.5), P[j][1] + r.normal(0, 1.5), r.uniform(0.6, 1.3), r.uniform(0.3, 0.8) * p['i'][j])
        self._emit(T, 1.2, 0.8)
        return E

    @staticmethod
    def _dot(buf, x, y, rad, amp):
        H, W = buf.shape
        k = int(rad * 3 + 2)
        ix, iy = int(x), int(y)
        if ix < k or iy < k or ix >= W - k or iy >= H - k: return
        yy, xx = np.mgrid[-k:k + 1, -k:k + 1].astype(np.float32)
        g = np.exp(-((xx - (x - ix)) ** 2 + (yy - (y - iy)) ** 2) / (2 * (rad * 0.6) ** 2)) * amp
        sl = buf[iy - k:iy + k + 1, ix - k:ix + k + 1]
        np.maximum(sl, g, out=sl)

    def sparks(self, x, y, n=60, spread=0.7, speed=(30, 120), up=-np.pi / 2, gravity=90.0, streak=(5, 18),
               size=(0.5, 1.2), lean=0.0, seed=None):
        """ballistic sparks thrown from (x, y): short fading streaks with a hot head"""
        r = self._r(seed)
        paths = []
        for _ in range(n):
            a = up + lean + spread * r.normal(0, 1)
            v = r.uniform(*speed)
            tf = r.uniform(0.25, 1.2)
            ts = np.linspace(max(0, tf - r.uniform(*streak) / max(v, 1)), tf, 6)
            px = x + np.cos(a) * v * ts + r.normal(0, 3)
            py = y + np.sin(a) * v * ts + 0.5 * gravity * ts ** 2
            it = np.linspace(0.1, 1, 6).astype(np.float32) * r.uniform(0.5, 1.0)
            paths.append({'pts': np.stack([px, py], 1).astype(np.float32), 'w': (r.uniform(*size), r.uniform(*size) * 1.2),
                          'i': it, 'tip': r.uniform(0.3, 0.9)})
        E = self._emission(paths)
        self._emit(E, 1.1, 0.7)
        T = np.zeros((self.H, self.W), np.float32)
        for p in paths: self._dot(T, p['pts'][-1][0], p['pts'][-1][1], 0.9, p['tip'])
        self._emit(T, 1.2, 0.6)

    def embers(self, region, n=80, size=(0.5, 1.1), heat=(0.4, 1.0), seed=None):
        """scattered single hot specks (sparks caught in the air)"""
        r = self._r(seed)
        M = self._mask(region)
        ys, xs = np.nonzero(M > 0.02)
        if not len(xs): return
        T = np.zeros((self.H, self.W), np.float32)
        idx = r.choice(len(xs), size=min(n * 4, len(xs)))
        cnt = 0
        for i in idx:
            if r.random() > M[ys[i], xs[i]]: continue
            self._dot(T, xs[i] + r.random(), ys[i] + r.random(), r.uniform(*size), r.uniform(*heat))
            cnt += 1
            if cnt >= n: break
        self._emit(T, 1.0, 0.7)

    def stars(self, region, n=150, size=(0.5, 1.5), bright=0.06, colour='star', warm=0.15, seed=None):
        """a few pinpricks of light on top of the sky strokes; `bright` of them larger with a faint halo"""
        r = self._r(seed)
        M = self._mask(region)
        ys, xs = np.nonzero(M > 0.05)
        if not len(xs): return
        S = np.zeros((self.H, self.W), np.float32); Sw = np.zeros((self.H, self.W), np.float32)
        cnt = 0
        for i in r.choice(len(xs), size=min(n * 5, len(xs))):
            if r.random() > M[ys[i], xs[i]]: continue
            big = r.random() < bright
            rad = r.uniform(*size) * (1.7 if big else 1.0)
            amp = r.uniform(0.45, 1.0) * (1.0 if big else 0.8)
            self._dot(Sw if r.random() < warm else S, xs[i] + r.random(), ys[i] + r.random(), rad, amp)
            if big: self._dot(S, xs[i] + 0.5, ys[i] + 0.5, rad * 4, 0.12)
            cnt += 1
            if cnt >= n: break
        for buf, c in ((S, colour), (Sw, 'warmstar')):
            a = np.clip(buf, 0, 1)
            if self.pic is not None: a = a * self.pic
            self.C += (hexc(c) - self.C) * a[..., None]

    # ================================================================== water
    def reflect(self, waterline, region, src, stretch=1.3, ripple=5.0, darken=0.7, tint='sea', mixw=0.35, thr=0.1,
                length=(30, 80), width=(2.2, 3.4), density=1.3, alpha=0.9, seed=None, **kw):
        """horizontal strokes coloured by the mirrored picture above the waterline (stretched, rippled, darkened),
        laid only where that mirror is bright -- a reflection broken into strokes"""
        r = self._r(seed)
        wl = np.asarray(waterline, np.float32)
        if wl.ndim == 0: wl = np.full(self.W, float(wl), np.float32)
        M = self._mask(region)
        rip = fbm1d(self.W, 30, 3, int(r.integers(1 << 30)))
        rows = fbm1d(self.H, 9, 3, int(r.integers(1 << 30)))
        depth = np.clip(self.YY - wl[None], 0, None)
        bx0, by0, bx1, by1 = self.box
        sx = np.clip(self.XX + ripple * rows[:, None] * (1 + depth / 60) + ripple * 0.5 * rip[None], bx0 + 2, bx1 - 3)
        sy = np.clip(wl[None] - depth / stretch, by0 + 2, self.H - 1)
        Mi = src[sy.astype(np.int32), sx.astype(np.int32)]
        lum = Mi.max(-1)
        prob = M * smoothstep(thr, thr * 3.0, lum) * (depth > 0)
        tc = hexc(tint)
        Mi = (Mi * darken) * (1 - mixw) + tc * mixw

        def col(x, y): return _lookup(Mi, x, y)
        return self.hatch(prob.astype(np.float32), 0.0, col, length, width, density, jitter=0.03, bend=0.01,
                          value=0.12, hue=0.03, alpha=alpha, pressure=0.96, dry=0.4, seed=int(r.integers(1 << 30)), **kw)

    def glitter(self, x, y_water, y_end, w0=10.0, w1=140.0, power=1.0, density=1.6, length=(18, 70), width=(2.0, 3.4),
                seed=None):
        """the broken column a light on the waterline throws toward the viewer: hot and narrow near the source,
        widening, redder and more broken further down"""
        r = self._r(seed)
        t = np.clip((self.YY - y_water) / max(1.0, y_end - y_water), 0, 1)
        hw = w0 + (w1 - w0) * t
        wob = fbm1d(self.H, 14, 3, int(r.integers(1 << 30)))[:, None] * (6 + 30 * t)
        dx = np.abs(self.XX - x - wob) / hw
        prob = (np.exp(-dx ** 2 * 1.6) * (1 - 0.55 * t) * (self.YY > y_water)).astype(np.float32)
        brk = noise2d(self.H, self.W, 7, 2, int(r.integers(1 << 30)))
        prob = prob * smoothstep(0.25, 0.6, brk + 0.25 * (1 - t))
        R = ramp('fire')
        level = np.clip((1 - t) ** 1.4 * np.exp(-dx ** 2 * 0.9), 0, 1)

        def col(xs, ys): return ramp_at(R, 0.25 + 0.75 * _lookup(level, xs, ys)) * power
        self.hatch(prob, 0.0, col, length, width, density, jitter=0.03, bend=0.01, value=0.15, hue=0.04,
                   pressure=0.96, dry=0.4, alpha=0.95, seed=int(r.integers(1 << 30)))
        hot = (prob * level ** 1.5).astype(np.float32)

        def col2(xs, ys): return ramp_at(R, 0.5 + 0.5 * _lookup(level, xs, ys)) * power * 0.8
        self.hatch(hot, 0.0, col2, (10, 40), (1.6, 2.6), 0.9, jitter=0.03, bend=0.01, value=0.1, pressure=0.85,
                   dry=0.5, mode='light', seed=int(r.integers(1 << 30)))

    # ================================================================== masses and figures
    def silhouette(self, mask, ramp_='land', field=0.0, val=None, density=2.2, length=(12, 28), width=(2.2, 3.4),
                   rim=0.0, rim_from=None, rim_colour='ember', seed=None):
        """a dark mass (rock, island, mountain) painted in strokes: a dense dark body, a sparser lighter pass, and
        optionally a warm rim on the edge that faces a light at rim_from = (x, y)"""
        r = self._r(seed)
        v = self.value(0.25, 0.45, 0, self.H, 0.12, 90, seed=int(r.integers(1 << 30))) if val is None else val
        self.hatch(mask, field, (ramp_, v), length, width, density, value=0.1, hue=0.04, pressure=0.93,
                   dry=0.3, seed=int(r.integers(1 << 30)))
        self.hatch(mask * 0.5, field, (ramp_, np.clip(v + 0.3, 0, 1)), (8, 20), (1.6, 2.4), 0.35, value=0.12,
                   pressure=0.85, dry=0.5, seed=int(r.integers(1 << 30)))
        if rim and rim_from is not None:
            lx, ly = rim_from
            dx, dy = lx - self.XX, ly - self.YY
            dn = np.sqrt(dx * dx + dy * dy) + 1e-3
            m = mask
            sh = np.zeros_like(m)
            # how much of the mask lies toward the light within a few px: an edge facing the light
            for k in (2, 4):
                ox = np.round(dx / dn * k).astype(np.int32); oy = np.round(dy / dn * k).astype(np.int32)
                yy = np.clip(self.YY.astype(np.int32) + oy, 0, self.H - 1); xx = np.clip(self.XX.astype(np.int32) + ox, 0, self.W - 1)
                sh = np.maximum(sh, m - m[yy, xx])
            edge = np.clip(sh, 0, 1) * m
            Lm = self.lightmap().max(-1)
            prob = np.clip(blur(edge, 1.0) * 2.5 * np.clip(Lm * 2, 0, 1), 0, 1)
            R = ramp('ember')

            def col(x, y): return ramp_at(R, 0.3 + 0.7 * _lookup(np.clip(Lm, 0, 1), x, y)) * rim
            self.hatch(prob, field, col, (5, 12), (1.2, 2.0), 1.2, value=0.15, pressure=0.85, dry=0.4, mode='light',
                       seed=int(r.integers(1 << 30)))

    def figure(self, x, y, h=44.0, facing=1, accent='scarf', accent2=None, legs='dangle', lean=0.12, body='#0b0d19',
               coat='#151a2c', rim_from=None, rim=0.7, hat=False, seed=None):
        """a tiny seated person (h px from the seat to the top of the head), silhouette-dark with one small accent
        (`accent` scarf colour, `accent2` hat colour) and a warm rim on the side facing rim_from = (x, y).
        Returns the figure's mask."""
        ss = 4
        s = h / 10.0
        pad = int(h * 1.2)
        ox, oy = x - pad, y - pad * 1.4
        Wl, Hl = int(pad * 2), int(pad * 2.2)
        F = lambda px, py: ((px - ox) * ss, (py - oy) * ss)
        def canvas(): return Image.new('L', (Wl * ss, Hl * ss), 0)
        def caps(d, pts, w):
            q = [F(*p) for p in pts]
            d.line(q, fill=255, width=int(w * ss), joint='curve')
            for p in (q[0], q[-1]):
                d.ellipse([p[0] - w * ss / 2, p[1] - w * ss / 2, p[0] + w * ss / 2, p[1] + w * ss / 2], fill=255)
        f = facing
        hip = (x, y - 0.6 * s)
        sh = (x + f * lean * 7.0 * s, y - 7.2 * s)
        head = (sh[0] + f * 0.5 * s, sh[1] - 1.75 * s)
        knee = (x + f * 3.9 * s, y - (2.2 * s if legs == 'knees' else 0.5 * s))
        foot = (knee[0] + f * (0.9 * s if legs == 'knees' else 0.4 * s), y + (0.2 * s if legs == 'knees' else 3.9 * s))
        im_b = canvas(); d = ImageDraw.Draw(im_b)
        # torso: a tapered quad from shoulders to hips, rounded by caps
        tw0, tw1 = 2.9 * s, 2.5 * s
        nx_, ny_ = (hip[1] - sh[1]), -(hip[0] - sh[0]); nl = np.hypot(nx_, ny_); nx_, ny_ = nx_ / nl, ny_ / nl
        quad = [F(sh[0] + nx_ * tw0 / 2, sh[1] + ny_ * tw0 / 2), F(hip[0] + nx_ * tw1 / 2, hip[1] + ny_ * tw1 / 2),
                F(hip[0] - nx_ * tw1 / 2, hip[1] - ny_ * tw1 / 2), F(sh[0] - nx_ * tw0 / 2, sh[1] - ny_ * tw0 / 2)]
        d.polygon(quad, fill=255)
        caps(d, [sh, (sh[0] + f * 0.2 * s, sh[1] + 0.3 * s)], 2.9 * s)
        caps(d, [hip, knee], 1.9 * s)
        caps(d, [knee, foot], 1.4 * s)
        caps(d, [(foot[0] - f * 0.1 * s, foot[1]), (foot[0] + f * 0.8 * s, foot[1] + 0.1 * s)], 0.9 * s)
        # arm resting on the knee
        caps(d, [(sh[0] + f * 0.4 * s, sh[1] + 0.6 * s), (sh[0] + f * 1.6 * s, sh[1] + 3.6 * s), (knee[0] - f * 0.4 * s, knee[1] - 0.6 * s)], 1.1 * s)
        hr = 1.05 * s
        hx, hy = F(*head)
        d.ellipse([hx - hr * ss, hy - hr * ss * 1.08, hx + hr * ss, hy + hr * ss * 1.08], fill=255)
        im_a = canvas(); da = ImageDraw.Draw(im_a)            # scarf: a band round the neck and a short tail
        nk = (sh[0] + f * 0.25 * s, sh[1] - 0.35 * s)
        caps(da, [(nk[0] - f * 1.0 * s, nk[1] + 0.1 * s), (nk[0] + f * 1.0 * s, nk[1] - 0.05 * s)], 0.95 * s)
        caps(da, [(nk[0] - f * 0.5 * s, nk[1] + 0.2 * s), (nk[0] - f * 0.9 * s, nk[1] + 2.0 * s)], 0.75 * s)
        im_h = canvas(); dh = ImageDraw.Draw(im_h)
        if hat or accent2 is not None:
            dh.pieslice([hx - hr * ss * 1.08, hy - hr * ss * 1.25, hx + hr * ss * 1.08, hy + hr * ss * 0.75], 180, 360, fill=255)
        down = lambda im: np.asarray(im.resize((Wl, Hl), Image.BOX), np.float32) / 255
        mb, ma, mh = down(im_b), down(im_a) * (1.0 if accent else 0.0), down(im_h)
        m_all = np.maximum(np.maximum(mb, ma), mh)
        # place into the canvas
        x0, y0 = int(round(ox)), int(round(oy))
        sl = (slice(max(0, y0), min(self.H, y0 + Hl)), slice(max(0, x0), min(self.W, x0 + Wl)))
        ly = slice(sl[0].start - y0, sl[0].stop - y0); lx = slice(sl[1].start - x0, sl[1].stop - x0)
        Cs = self.C[sl]
        r = self._r(seed)
        tex = 1 + 0.12 * (r.random(mb[ly, lx].shape) - 0.5)
        base = np.where((np.arange(Hl)[:, None] * 1.0 + oy < sh[1] + 2.5 * s), 1.0, 0.0)[ly, lx]
        cbody = hexc(coat) * base[..., None] + hexc(body) * (1 - base[..., None])
        Cs[:] = Cs * (1 - mb[ly, lx, None]) + cbody * tex[..., None] * mb[ly, lx, None]
        if accent2 is not None:
            Cs[:] = Cs * (1 - mh[ly, lx, None]) + hexc(accent2) * mh[ly, lx, None]
        if accent:
            ac = hexc(accent) * (0.92 + 0.16 * (r.random(ma[ly, lx].shape) - 0.5))[..., None]
            Cs[:] = Cs * (1 - ma[ly, lx, None]) + ac * ma[ly, lx, None]
        if rim_from is not None and rim:
            lx_, ly_ = rim_from
            ang = np.arctan2(ly_ - y, lx_ - x)
            ddx, ddy = np.cos(ang), np.sin(ang)
            m = m_all
            Hm, Wm = m.shape
            yy, xx = np.mgrid[0:Hm, 0:Wm]
            sh1 = m[np.clip(yy + int(round(ddy * 1.3)), 0, Hm - 1), np.clip(xx + int(round(ddx * 1.3)), 0, Wm - 1)]
            edge = np.clip(m - sh1, 0, 1) * m
            rc = hexc('ember') * 0.9 + hexc('flame') * 0.1
            a = np.clip(edge * rim, 0, 1)[ly, lx]
            Cs[:] = Cs + (rc - Cs) * a[..., None] * 0.8
        full = np.zeros((self.H, self.W), np.float32); full[sl] = m_all[ly, lx]
        return full

    # ================================================================== the mount and the pencil text
    def mount(self, plate=16, depth=0.06, seed=None):
        """press a plate mark round the picture: a soft groove `plate` px outside it, the plate area a touch smoother"""
        x0, y0, x1, y1 = self.box
        X, Y = self.XX, self.YY
        px0, py0, px1, py1 = x0 - plate, y0 - plate, x1 + plate, y1 + plate
        sd = np.minimum(np.minimum(X - px0, px1 - X), np.minimum(Y - py0, py1 - Y))   # signed: + inside the plate
        ox = np.maximum(np.maximum(px0 - X, X - px1), 0); oy = np.maximum(np.maximum(py0 - Y, Y - py1), 0)
        dist = np.where(sd >= 0, sd, np.sqrt(ox * ox + oy * oy))
        inside = np.clip(sd + 0.5, 0, 1)
        groove = np.exp(-(dist / 1.4) ** 2) * inside
        # walls: the top and left walls of the recess face away from the light (dark), the bottom and right catch it
        top_left = (((np.abs(Y - py0) < 4) & (X > px0 - 4) & (X < px1 + 4)) | ((np.abs(X - px0) < 4) & (Y > py0 - 4) & (Y < py1 + 4))).astype(np.float32)
        lip = np.exp(-((dist - 2.2) / 1.2) ** 2) * (1 - inside)
        shade = groove * (0.55 + 0.45 * top_left) * depth * 2.2
        light = lip * (1 - top_left) * depth * 1.4
        pm = 1 - (self.pic if self.pic is not None else 0)
        smooth = inside * pm * 0.012
        f = (1 - shade + light + smooth) * pm + (1 - pm)
        self.C *= f[..., None]

    def caption(self, text, x, y, size=26, anchor='ls', colour='pencil', weight='light', alpha=0.82, jitter=0.45,
                tracking=0.6, seed=None):
        """pencilled text in a thin plain face, glyph by glyph with a hair of baseline / angle wobble, the graphite
        skipping on the paper tooth"""
        r = self._r(seed)
        f = _font(weight, size * 3)
        adv = [f.getlength(ch) / 3 + tracking for ch in text]
        total = sum(adv) - tracking
        x0 = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        acc = np.zeros((self.H, self.W), np.float32)
        cx = x0
        for ch, a in zip(text, adv):
            if ch.strip():
                gw, gh = int(a * 3 + size * 3), int(size * 3 * 2)
                g = Image.new('L', (gw, gh), 0)
                ImageDraw.Draw(g).text((size * 1.5, gh * 0.7), ch, font=f, fill=255, anchor='ls')
                g = g.rotate(r.normal(0, jitter * 1.6), resample=Image.BICUBIC, center=(size * 1.5, gh * 0.7))
                g = g.resize((gw // 3, gh // 3), Image.BOX)
                gx = int(round(cx - size * 0.5 + r.normal(0, jitter * 0.3))); gy = int(round(y - gh / 3 * 0.7 + r.normal(0, jitter * 0.5)))
                ga = np.asarray(g, np.float32) / 255 * r.uniform(0.85, 1.0)
                ys_, xs_ = slice(max(0, gy), min(self.H, gy + ga.shape[0])), slice(max(0, gx), min(self.W, gx + ga.shape[1]))
                acc[ys_, xs_] = np.maximum(acc[ys_, xs_], ga[ys_.start - gy:ys_.stop - gy, xs_.start - gx:xs_.stop - gx])
            cx += a
        tooth = np.clip((0.9 - self.T) * 5 + 0.55, 0, 1)
        A = np.clip(acc * 1.15, 0, 1) * tooth * alpha
        self.C += (hexc(colour) - self.C) * A[..., None]

    # ================================================================== finish
    def bloom(self, amount=1.0):
        """a restrained bloom round the brightest lights (applied in render)"""
        self.bloom_amt = float(amount)

    def grain(self, amount=1.0):
        """fine pastel grain over the picture and the paper (applied in render)"""
        self.grain_amt = float(amount)

    def render(self):
        out = self.C
        if self.bloom_amt:
            lum = out.max(-1)
            if self.pic is not None: lum = lum * self.pic            # only the picture's own lights, not the margin
            b = blur(np.clip(lum - 0.62, 0, 1), 9.0) * 0.8 + blur(np.clip(lum - 0.5, 0, 1), 26.0) * 0.5
            add = b[..., None] * hexc('lava') * self.bloom_amt
            if self.pic is not None: add *= self.pic[..., None]
            out = out + add * (1 - out)
        if self.grain_amt:
            if not hasattr(self, '_grain'):
                r = np.random.default_rng(self.seed + 7)
                g = r.normal(0, 1, (self.H, self.W)).astype(np.float32)
                g = 0.65 * g + 0.35 * blur(g, 0.8) * 2.0
                self._grain = (0.016 * g).astype(np.float32)
            out = out * (1 + self.grain_amt * self._grain[..., None])
        return np.clip(out, 0, 1)

    def composite(self):
        return Image.fromarray((self.render() * 255 + 0.5).astype(np.uint8))

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

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, b) in enumerate(self.stages):
                with open(f'{sd}/{i:02d}_{name}.png', 'wb') as f: f.write(b)
            img.save(f'{sd}/{self._n_stages:02d}_final.png', compress_level=1)
        return img
