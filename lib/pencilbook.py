"""pencilbook — 暖调彩铅绘本 / Warm Pencil Storybook: a picture-book spread in soft, layered coloured pencil on warm
toothy paper (numpy + Pillow only).

The look: a children's storybook page drawn in coloured pencil. Every surface -- sky, hills, grass, water, a giant
gentle creature, a small child -- is built from many fine directional pencil strokes laid in layers: a light
under-layer, the local colour, darker strokes of the same family in the shade, a warm glaze where the light falls and
a cool one in the shadow, each layer at a slightly different angle so the strokes cross. The wax only catches the
peaks of the paper's tooth, so tiny specks of warm white paper show through all the colour, fewer where the pencil
was pressed hard or the layers have filled the tooth. Fur and grass are tufts of fine strokes that follow the lie of
the hair. Edges are soft; there are no ink lines, at most a faint pencil contour in a darker version of the local
colour. The light is warm (late afternoon, dusk), lanterns and lit windows glow as layered orange-yellow strokes,
the palette is warm and only medium-saturated (yellow, orange, grass green, cobalt, ochre) and has no black.

Physical model
  paper       A warm white sheet with a fine tooth `T`: a 1-3 px grain over a softer ripple, rank-equalised to a uniform
              0..1 so "the wax reaches where tooth > 1 - pressure" turns a pressure straight into a coverage
              fraction. A pencil dragged across the paper rides from peak to peak, so the pits it skips are drawn out
              a little along the stroke: the tooth is pre-averaged along 8 directions (`TD`) and every stroke reads
              the version that matches its own direction. A wax-fill buffer `F` records how much wax already sits
              in the tooth: later layers reach a little deeper (`fill`), so heavily worked areas close up while
              light ones stay speckled -- but the same pits stay white through every layer, as on real paper.
  stroke      One pencil stroke is a centreline integrated through an orientation field (angles mod pi, so it never
              flips halfway), with a slight wrist arc. Thousands are rasterised at once: Pillow draws every stroke as
              a polyline with its own id into a 2x supersampled integer map, then, for every covered sub-pixel, numpy
              looks up that stroke's colour, start, direction, length, pressure and taper, recovers the position
              along the stroke (u) and from it the pressure profile (pressed at the start, lifting off at the end),
              and where the pressure reaches the (direction-matched) tooth the wax is laid. Sub-pixels are summed back
              to pixels with bincount (only covered pixels are touched), so a pass costs about one Pillow line per
              stroke. Within one pass the top stroke wins; layers come from several passes (`passes`), so
              overlapping strokes of different passes build up like real hatching. Strokes are seeded on a jittered
              grid (even hatching, no clumps); the region is both where they land and, pixel by pixel, how hard the
              pencil is pressed (`fade`), so a shadow field gives a smooth gradation instead of scattered dark
              dashes; `avoid` colours round things that come later (an illustrator leaves the tortoise blank while
              laying the sky, so its colours don't mix with the blue).
  wax         Coloured pencil is semi-transparent: new = old + A x (target - old), target = (1 - opacity) x
              old x colour / paper + opacity x colour. Over bare paper a stroke is exactly its colour; blue over
              yellow goes green, a dark over its own colour goes deeper; light pencils (white, cream, yellow) over a
              dark need a high `opacity` (burnishing).
  form        `shading(mask, light)` turns a silhouette into a soft dome (sum of blurs), takes its normals and gives
              a 0..1 light field for a light from the upper left (default). `form()` paints a shape the way a
              pencil illustrator models it: a light under-layer all over, the local colour, the shadow colour where
              the light falls off, the deepest tone in the core shadow, then a warm glaze on the lit side and a cool
              glaze in the shadow, the layers crossing at +-`cross` degrees around the form's own direction field.
  fields      `flow()` a drifting direction (sky, water), `contour()` along the iso-lines of a shape (strokes that
              wrap round a dome or a stone), `radial()` away from a point (glow, petals), `blend()` with doubled
              angles (0 and pi are the same direction), `rotate()`.
  fur, grass  `fur()` lays tufts: each tuft is a clump of 4-12 fine strokes whose roots spread across the clump and
              whose tips converge (hair lies in locks), curling a little the same way, pressed at the root and
              lifting off at the tip, all following the lie of the hair; the strands on the side of a lock away from
              the light are a little darker, so every lock has a lit and a shadowed flank. `pelt()` is a whole coat:
              a soft under-layer, dark short locks in the shadow, the local colour, light-tipped locks on the lit
              side. `grass()` is the opposite clump -- blades rising from a base and fanning out; `leaves()` packs
              short curved leaf strokes in clumps for tree crowns.
  storybook   `tree()` (a trunk, branches and a crown of separately lit clumps; `tree_plan()` gives its masks first),
              `cottage()` (walls along the vertical, roof along its slopes, lit windows, door, chimney), `stone()`
              (contour-hatched, flattish top, optional moss), `scales()` (staggered small domes with a crease on the
              shadow side), `flowers()` (rounded petal strokes round a centre dab, optional stems).
  light       `glow()` lays warm light as strokes that follow the surface round a point (white-yellow near the
              source, orange further out, thinning into the surroundings -- not rays), over a soft tooth-textured
              lift of the paper (never a smooth blob); `window()` is a lit window: orange at the frame, butter-yellow
              at the centre, a few muntins; `lift()` is a kneaded eraser / white-pencil lift.
  water       `reflect()` paints horizontal strokes whose colour is the mirrored picture above the waterline (pushed
              sideways by ripples, softened and mixed with the water colour), so a reflection is made of strokes
              too; `ripples()` are broken elliptical pencil rings round something standing in the water.
  people      `child()` is a small storybook child (a few hundred px at most): a raincoat with a hood down, boots,
              a bob of hair in smooth locks, a dot eye, a rosy cheek, one hand forward for a lantern
              (`paint=False` only plans its mask); `lantern()` a small round paper lantern; `eye()` a soft dot eye
              with a glint and an optional lid; `blush()`.
  finish      `finish()` (call it before the first stroke; applied in render so every stage snapshot matches the
              final): a slight softness, fine grain and a faint warm vignette.

API (canvas pixel coordinates; a number given as a field is a direction in degrees, 0 = to the right, 90 = down;
     field arrays are radians; colours are PAINTS names, '#rrggbb' or RGB triples; ramps are RAMPS names or lists)
  surface    PencilStorybook(W, H, seed, keep_stages, stages_dir); paper(tone, tooth, mottle, fibres)
  masks      poly(pts, smooth) / ellipse(cx, cy, rx, ry, rot) / blob(cx, cy, rx, ry, rough) / tube(path, w0, w1) /
             below(xs, ys, invert) / rect(x0, y0, x1, y1) -> canvas-sized float masks
  fields     flow(angle_deg, turb, scale); contour(mask, sigma, offset); radial(cx, cy, offset); blend(f1, f2, w);
             rotate(field, deg); value(top, bottom, y0, y1, mottle) value fields; shading(mask, light, sigma, wrap)
  strokes    hatch(region, field, colour, length, width, density, pressure, opacity, alpha, jitter, bend, value, hue,
             taper, passes, clip, avoid, fade); strokes(paths, colour, width, pressure, opacity, taper, clip);
             line(path, colour, width, pressure, seg, wobble, clip, gaps); edge(mask, colour, width, density, where)
  form       form(mask, colours, field, light, cross, length, width, density, pressure, warm, cool, edge, lit, avoid)
  hair       fur(region, field, colour, length, width, density, tuft, spread, curl, converge, pressure, side, light);
             pelt(mask, colours, field, light, length, density, lit); grass(region, colour, height, lean, sway,
             density, tuft, fan); leaves(region, colour, size, density, field)
  storybook  tree(x, y, h, r, colours, trunk, clumps, leaf, light, lean, seed) / tree_plan(...); cottage(x, y, w, h,
             wall, roof, windows, door, chimney, light, glow); stone(cx, cy, rx, ry, colours, moss, light);
             scales(mask, size, colours, groove, field, light, lit); flowers(region, kinds, n, size, stems)
  light      glow(x, y, r, colours, strength, density, halo, squash, clip); window(x0, y0, x1, y1, panes, frame);
             lift(mask, colour, amount)
  water      reflect(waterline, region, src, ripple, stretch, darken, tint, length, width, density);
             ripples(cx, cy, rx, ry, rings, colour)
  people     child(x, y, h, facing, coat, hair, boots, legs, look, paint) -> anchors; lantern(x, y, size, glow) -> centre;
             eye(x, y, r, lid, look); blush(x, y, r); dots(region, colours, n, size)
  finish     finish(soft, grain, vignette); render(); composite(); stage(name); save(path, stages_dir)

    import sys; sys.path.insert(0, 'lib')
    from pencilbook import PencilStorybook
    p = PencilStorybook(1920, 1080, seed=3)
    p.finish(); p.paper()
    sky = p.below(None, 620, invert=True)
    p.hatch(sky, p.flow(-4, 6), ('dusk_sky', p.value(0, 1, 0, 620)), length=(60, 140), density=1.4)
    hill = p.below([0, 600, 1200, 1920], [640, 560, 600, 580])
    p.form(hill, ('sage', 'grass', 'leaf', 'forest'), p.flow(-8, 12), warm='butter', cool='periwinkle')
    p.grass(p.below(None, 900), ('grass', 'leaf', 'yellowgreen'), height=(30, 70))
    p.tree(1400, 640, 120, 90, seed=4)
    c = p.child(700, 900, 200, 1, light=p.LIGHT)
    p.glow(*p.lantern(c['hand'][0], c['hand'][1], 28), 60)
    p.save('page.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, noise2d, smoothstep, spline, blob_pts


PAINTS = {
    # paper and the lightest pencils
    'paper': '#f6eedc', 'white': '#fffaf0', 'cream': '#fbf0d6', 'ivory': '#f8ead0',
    # sky and cool colours
    'sky_top': '#4f78bd', 'cobalt': '#4469b0', 'sky': '#6f97d0', 'cornflower': '#86a7d9', 'sky_pale': '#b8cce6',
    'powder': '#cad9ec', 'periwinkle': '#8f9bd0', 'lavender': '#ac9fc8', 'mauve': '#b58fa6', 'violet': '#6b5f99',
    'ultramarine': '#3a4e98', 'indigo': '#373f73', 'slate': '#68718c', 'teal': '#4e8584', 'aqua': '#93c3c3',
    # warm light
    'lemon': '#f5e27c', 'butter': '#f7d877', 'sun': '#fbe7a6', 'apricot': '#f4bd78', 'peach': '#f2ad86',
    'glow': '#ffe39a', 'lantern': '#ffc457', 'flame': '#f89a3a', 'orange': '#ec8a36', 'tangerine': '#e9742f',
    # greens
    'meadow': '#c3c86a', 'yellowgreen': '#b3c24d', 'grass': '#88a843', 'leaf': '#5f8d3c', 'sage': '#9fb07c',
    'moss': '#748a38', 'olive': '#7f7a3c', 'forest': '#3f6038', 'pine': '#2f4b3e', 'lichen': '#b7bd88',
    # earth
    'ochre': '#cc9642', 'gold': '#dca84b', 'amber': '#c97a30', 'sienna': '#a6582f', 'brown': '#7c5236',
    'umber': '#6a4a33', 'sepia': '#553d30', 'tan': '#c9a77c', 'sand': '#dcc39a', 'stone': '#a39a8c',
    'warmgrey': '#8f8478', 'pebble': '#bfb5a4',
    # reds and pinks
    'terracotta': '#c86c47', 'brick': '#a9503a', 'rose': '#df8b86', 'coral': '#e9785e', 'vermilion': '#d65a3a',
    'red': '#c4443a', 'cheek': '#ea8f7c', 'pink': '#efb0a6',
    # people
    'skin': '#f2c9a4', 'skin_shade': '#dc9c7c', 'hair': '#6e4630', 'hair_light': '#a2683f',
    'raincoat': '#f3c53e', 'raincoat_shade': '#dc982f', 'raincoat_deep': '#b8722c',
    'denim': '#5b74a8', 'boot': '#d2553f', 'eye': '#3b2c2a',
}

RAMPS = {
    'dusk_sky':  ['#7096cb', '#7f9fd2', '#96b0da', '#b4c6e2', '#d9d4dc', '#f1d2b6', '#f5cc9c', '#f7dca2'],
    'day_sky':   ['#4672b9', '#5f8ac8', '#83a6d6', '#a9c1e2', '#cbd9ec'],
    'glow':      ['#ffefc0', '#ffe39a', '#ffd172', '#fbb757', '#f39a42', '#e67e38'],
    'water':     ['#5d84bf', '#7a9dcf', '#a0bad9', '#d5ccc9', '#efc9a2', '#f4d49a'],
    'meadow':    ['#5f8d3c', '#7d9f40', '#9fb34a', '#bcc25a', '#d8cc76'],
    'hills':     ['#7f86b4', '#9196bd', '#a8a5c3', '#bcb4c6'],
    'shell':     ['#5e3e2b', '#7e5232', '#a06a35', '#c08940', '#d8aa58', '#ecca7d'],
    'skin':      ['#5f5d3c', '#7a7646', '#959054', '#b0a96a', '#cbc287'],
    'stone':     ['#6f6a62', '#8c857a', '#a79e90', '#c2b8a6', '#dcd1bd'],
    'autumn':    ['#8a5a2c', '#b8742c', '#d9973a', '#e8b84a', '#efd06a', '#b9b84e', '#8ea443'],
}


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def ramp(spec):
    """a RAMPS name or a list of colours -> (K, 3) array"""
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


def _resample(P, step):
    P = np.asarray(P, np.float32)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-3: return P[:1]
    s = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)


class PencilStorybook:
    PAINTS = PAINTS
    RAMPS = RAMPS
    LIGHT = (-0.62, -0.58, 0.53)            # the default light: upper left, a little in front

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.P = hexc('paper')
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = self.P
        self.F = np.zeros((H, W), np.float32)             # wax already sitting in the tooth
        self.T = None; self.TD = None
        self.EN = None                                     # edge wobble noise
        self.fin = None
        self.floor = 0.34                                  # wax a pencil still leaves in the pits of the tooth
        self.n_strokes = 0

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== paper
    def paper(self, tone='paper', tooth=1.0, mottle=0.028, fibres=160, drag=3, seed=None):
        """warm white drawing paper: equalised tooth, faint low mottling and a few fibres"""
        H, W = self.H, self.W
        r = self._r(seed)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.55)
        g2 = noise2d(H, W, 2.2, 2, int(r.integers(1 << 30)))
        g3 = noise2d(H, W, 6.5, 2, int(r.integers(1 << 30)))
        g4 = noise2d(H, W, 22.0, 2, int(r.integers(1 << 30)))
        self.T = _equalise(0.8 * z(g1) + 0.38 * z(g2) + 0.12 * z(g3) + 0.05 * z(g4))
        self.P = hexc(tone)
        mot = noise2d(H, W, 180, 4, int(r.integers(1 << 30))) - 0.5
        C = self.P[None, None] * (1 + mottle * mot[..., None] - 0.03 * tooth * (0.5 - self.T[..., None]) * 0.6)
        if fibres:
            im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
            for _ in range(fibres):
                px, py = r.uniform(0, W), r.uniform(0, H)
                a = r.uniform(0, np.pi); L = r.uniform(5, 22)
                pts = [(px + np.cos(a) * L * t + r.normal(0, 1.0), py + np.sin(a) * L * t + r.normal(0, 1.0))
                       for t in np.linspace(-0.5, 0.5, 5)]
                d.line(pts, fill=int(r.uniform(30, 90)), width=1)
            fib = blur(np.asarray(im, np.float32) / 255, 0.5)
            C = C * (1 - 0.035 * fib[..., None])
        self.C = C.astype(np.float32)
        self.F[:] = 0
        # tooth dragged along 8 stroke directions
        TD = np.empty((8, H, W), np.float32)
        ks = np.arange(-drag, drag + 1); wk = 1.0 - np.abs(ks) / (drag + 1.0)
        for b in range(8):
            a = np.pi * b / 8
            acc = np.zeros_like(self.T)
            for k, w in zip(ks, wk):
                acc += w * np.roll(self.T, (int(round(k * np.sin(a))), int(round(k * np.cos(a)))), axis=(0, 1))
            TD[b] = _equalise(0.45 * self.T + 0.55 * acc / wk.sum())
        self.TD = TD
        self.EN = noise2d(H, W, 3.5, 2, int(r.integers(1 << 30))) - 0.5
        return self

    def _need(self):
        if self.T is None: self.paper()

    # ================================================================== masks
    def poly(self, pts, smooth=False, ss=2):
        """filled polygon -> canvas-sized float mask (smooth=True runs a closed Catmull-Rom spline through the points)"""
        P = np.asarray(pts, np.float32)
        if smooth:
            Q = np.vstack([P[-1:], P, P[:2]])
            P = spline(Q, 10)[10:-10]
        im = Image.new('L', (self.W * ss, self.H * ss), 0)
        ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in P], fill=255)
        return np.asarray(im.resize((self.W, self.H), Image.BOX), np.float32) / 255

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        """anti-aliased ellipse mask (rot in degrees)"""
        ry = rx if ry is None else ry
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        dx, dy = self.XX - cx, self.YY - cy
        u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
        d = np.sqrt(u * u + v * v)
        return np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1).astype(np.float32)

    def blob(self, cx, cy, rx, ry=None, rough=0.1, seed=None, rot=0.0):
        ry = rx if ry is None else ry
        return self.poly(blob_pts(cx, cy, rx, ry, rough, 120, int(self._r(seed).integers(1 << 30)), np.deg2rad(rot)))

    @staticmethod
    def tube_pts(path, w0, w1=None, per=8):
        """outline points of a tube of width w0 -> w1 along a path (limbs, trunks, necks)"""
        w1 = w0 if w1 is None else w1
        P = spline(path, per) if len(path) > 2 else _resample(path, 4)
        n = len(P)
        Tg = np.gradient(P, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-6
        Nn = np.stack([-Tg[:, 1], Tg[:, 0]], 1)
        w = np.linspace(w0, w1, n)[:, None] * 0.5
        return np.vstack([P + Nn * w, (P - Nn * w)[::-1]])

    def tube(self, path, w0, w1=None):
        return self.poly(self.tube_pts(path, w0, w1))

    def below(self, xs, ys, invert=False):
        """mask of everything below a line through (xs, ys) (spline), or a constant y if xs is None"""
        if xs is None:
            m = np.clip(self.YY - float(ys) + 0.5, 0, 1)
        else:
            x = np.arange(self.W, dtype=np.float32)
            P = spline(np.stack([np.asarray(xs, np.float32), np.asarray(ys, np.float32)], 1), 12)
            o = np.argsort(P[:, 0])
            yl = np.interp(x, P[o, 0], P[o, 1]).astype(np.float32)
            m = np.clip(self.YY - yl[None] + 0.5, 0, 1)
        return (1 - m if invert else m).astype(np.float32)

    def line_y(self, xs, ys):
        """the y of a spline through (xs, ys) at every column"""
        x = np.arange(self.W, dtype=np.float32)
        P = spline(np.stack([np.asarray(xs, np.float32), np.asarray(ys, np.float32)], 1), 12)
        o = np.argsort(P[:, 0])
        return np.interp(x, P[o, 0], P[o, 1]).astype(np.float32)

    def rect(self, x0, y0, x1, y1):
        X, Y = self.XX, self.YY
        return (np.clip(X - x0 + 0.5, 0, 1) * np.clip(x1 - X + 0.5, 0, 1) *
                np.clip(Y - y0 + 0.5, 0, 1) * np.clip(y1 - Y + 0.5, 0, 1)).astype(np.float32)

    def _mask(self, region):
        if isinstance(region, np.ndarray): return region.astype(np.float32, copy=False)
        x0, y0, x1, y1 = (int(round(v)) for v in region)
        M = np.zeros((self.H, self.W), np.float32)
        M[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1
        return M

    @staticmethod
    def _bbox(M, thr=0.004, pad=0, W=None, H=None):
        rows = np.flatnonzero(M.max(1) > thr); cols = np.flatnonzero(M.max(0) > thr)
        if not len(rows) or not len(cols): return None
        H, W = M.shape
        return (max(0, cols[0] - pad), max(0, rows[0] - pad), min(W, cols[-1] + 1 + pad), min(H, rows[-1] + 1 + pad))

    # ================================================================== fields
    def flow(self, angle=0.0, turb=8.0, scale=240.0, seed=None):
        """orientation field: `angle` degrees (screen y down: positive tilts down to the right), +-turb degrees
        of low-frequency wander at `scale` px"""
        n = noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5
        return np.deg2rad(angle + 2 * turb * n).astype(np.float32)

    def radial(self, cx, cy, offset=0.0, turb=4.0, scale=120.0, seed=None):
        """directions pointing away from (cx, cy), offset in degrees"""
        a = np.arctan2(self.YY - cy, self.XX - cx) + np.deg2rad(offset)
        if turb:
            a = a + np.deg2rad(2 * turb * (noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5))
        return a.astype(np.float32)

    def contour(self, mask, sigma=8.0, offset=0.0, fallback=None):
        """directions along the iso-lines of a (blurred) shape: strokes that wrap round a dome, a stone, a cheek.
        Where the shape is flat the direction comes from `fallback` (degrees or a field)."""
        d = blur(mask.astype(np.float32), sigma)
        gy, gx = np.gradient(d)
        a = np.arctan2(gy, gx) + np.pi / 2 + np.deg2rad(offset)
        if fallback is not None:
            g = np.hypot(gx, gy)
            w = smoothstep(0.0, 0.25 / max(sigma, 1.0), g)
            fb = np.deg2rad(fallback) if np.ndim(fallback) == 0 else fallback
            a = self.blend(np.broadcast_to(np.float32(fb), a.shape) if np.ndim(fb) == 0 else fb, a, w)
        return a.astype(np.float32)

    @staticmethod
    def blend(f1, f2, w):
        """blend two orientation fields (doubled-angle average, so 0 and pi are the same orientation)"""
        w = np.asarray(w, np.float32)
        c = (1 - w) * np.cos(2 * f1) + w * np.cos(2 * f2)
        s = (1 - w) * np.sin(2 * f1) + w * np.sin(2 * f2)
        return (0.5 * np.arctan2(s, c)).astype(np.float32)

    @staticmethod
    def rotate(field, deg):
        """turn a field (radians array) or a direction in degrees by `deg` degrees; returns the same kind"""
        if np.ndim(field) == 0: return float(field) + deg
        return (field + np.deg2rad(deg)).astype(np.float32)

    def value(self, top=0.0, bottom=1.0, y0=0, y1=None, mottle=0.04, scale=220.0, seed=None):
        """a 0..1 field: a vertical ramp from `top` at y0 to `bottom` at y1, with low-frequency mottling"""
        y1 = self.H if y1 is None else y1
        t = np.clip((self.YY - y0) / max(1, y1 - y0), 0, 1)
        v = top + (bottom - top) * t
        if mottle:
            v = v + 2 * mottle * (noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5)
        return np.clip(v, 0, 1).astype(np.float32)

    def shading(self, mask, light=(-0.62, -0.58, 0.53), sigma=None, wrap=0.2, flat=0.0):
        """0..1 light on a soft dome raised from the silhouette (sum of blurs), lit from `light` (x, y, z; screen y
        down, default upper left). wrap > 0 lets the light creep round the terminator; flat mixes toward 0.5."""
        bb = self._bbox(mask)
        out = np.zeros((self.H, self.W), np.float32)
        if bb is None: return out
        m = mask.astype(np.float32)
        if sigma is None: sigma = max(4.0, np.sqrt(m.sum()) / 7.0)
        pad = int(sigma * 3) + 4
        x0, y0, x1, y1 = max(0, bb[0] - pad), max(0, bb[1] - pad), min(self.W, bb[2] + pad), min(self.H, bb[3] + pad)
        mm = m[y0:y1, x0:x1]
        h = 0.45 * blur(mm, sigma * 0.33) + 0.35 * blur(mm, sigma * 0.7) + 0.2 * blur(mm, sigma * 1.4)
        gy, gx = np.gradient(h)
        k = sigma * 2.2
        nx, ny, nz = -gx * k, -gy * k, np.ones_like(h)
        nn = np.sqrt(nx * nx + ny * ny + nz * nz)
        L = np.asarray(light, np.float32); L = L / np.linalg.norm(L)
        lam = (nx * L[0] + ny * L[1] + nz * L[2]) / nn
        lam = np.clip((lam + wrap) / (1 + wrap), 0, 1)
        if flat: lam = lam * (1 - flat) + 0.5 * flat
        out[y0:y1, x0:x1] = lam
        return out * (m > 0.001)

    # ================================================================== stroke machinery
    def _sizes(self, spec, x, y, r):
        n = len(x)
        if callable(spec):
            return (np.asarray(spec(x, y), np.float32) * r.uniform(0.8, 1.2, n)).astype(np.float32)
        if np.ndim(spec) == 0: return np.full(n, float(spec), np.float32) * r.uniform(0.85, 1.15, n).astype(np.float32)
        return r.uniform(spec[0], spec[1], n).astype(np.float32)

    def _colours(self, spec, x, y, r):
        """paint | list of paints (picked at random) | (ramp, value field or f(x, y)) | f(x, y) -> (N, 3) | RGB"""
        n = len(x)
        if callable(spec): return np.asarray(spec(x, y), np.float32).reshape(n, 3).copy()
        if isinstance(spec, str): return np.broadcast_to(hexc(spec), (n, 3)).astype(np.float32).copy()
        if isinstance(spec, (tuple, list)) and len(spec) == 2 and (callable(spec[1]) or isinstance(spec[1], np.ndarray)):
            R = ramp(spec[0]); f = spec[1]
            v = f(x, y) if callable(f) else _lookup(f, x, y)
            return ramp_at(R, v).astype(np.float32)
        if isinstance(spec, (tuple, list)) and all(isinstance(c, str) for c in spec):
            R = ramp(list(spec))
            return R[r.integers(0, len(R), n)].astype(np.float32)
        return np.broadcast_to(hexc(spec), (n, 3)).astype(np.float32).copy()

    @staticmethod
    def _field_rad(field):
        return np.float32(np.deg2rad(field)) if np.ndim(field) == 0 else field

    def _centrelines(self, x, y, L, field, jit, bend, k):
        """integrate k points through an orientation field from the centre outward (no flips)"""
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
            for j in range(1, (k - c) if sgn > 0 else (c + 1)):
                a = _lookup(field, px, py) + jit + sgn * bend * j
                v = np.stack([np.cos(a), np.sin(a)], 1).astype(np.float32)
                flip = (v * prev).sum(1) < 0
                v[flip] *= -1
                px = px + v[:, 0] * st; py = py + v[:, 1] * st
                P[:, c + sgn * j, 0] = px; P[:, c + sgn * j, 1] = py
                prev = v
        return P

    def _seed_points(self, M, bb, n_cells, r):
        """stratified (jittered-grid) candidate points over a box, accepted with probability M"""
        x0, y0, x1, y1 = bb
        bw, bh = x1 - x0, y1 - y0
        cell = max(1.0, np.sqrt(bw * bh / max(1, n_cells)))
        nx, ny = max(1, int(np.ceil(bw / cell))), max(1, int(np.ceil(bh / cell)))
        gx, gy = np.meshgrid(np.arange(nx, dtype=np.float32), np.arange(ny, dtype=np.float32))
        x = x0 + (gx.ravel() + r.random(nx * ny).astype(np.float32)) * cell
        y = y0 + (gy.ravel() + r.random(nx * ny).astype(np.float32)) * cell
        ok = (x < x1) & (y < y1)
        x, y = x[ok], y[ok]
        keep = r.random(len(x)) < _lookup(M, x, y)
        return x[keep], y[keep]

    def hatch(self, region, field=-35.0, colour='cobalt', length=(18, 46), width=(1.7, 2.6), density=1.5,
              pressure=0.74, opacity=0.3, alpha=0.62, jitter=0.07, bend=0.035, value=0.045, hue=0.025,
              taper=(0.45, 0.15), passes=2, clip='auto', avoid=None, fade='auto', k=5, seed=None):
        """lay pencil strokes over `region` (a 0..1 landing-probability mask or a box) following `field` (a
        direction in degrees or a radians field). density ~ how many times the strokes would tile the region;
        length / width: (lo, hi), a number or f(x, y); colour: a paint, a list of paints (picked at random), (ramp,
        value field or f(x, y)) or f(x, y) -> (N, 3); pressure: how deep the wax reaches into the tooth (1 = solid);
        opacity: how much a light pencil covers what is under it; value / hue: per-stroke jitter; taper: pressure
        at the (start, end) of the stroke; passes: sub-passes that build up on each other; clip: a mask the strokes
        are cut to ('auto' = the region's support with a soft, wandering edge; None = no clip); fade: a 0..1 field
        that eases the pressure off pixel by pixel ('auto' = region ** 0.65, so a shadow field gives a smooth
        gradation rather than scattered dark dashes); avoid: a mask of things to colour round (the strokes neither
        land nor run there). Returns the number of strokes."""
        self._need()
        r = self._r(seed)
        M = self._mask(region)
        if avoid is not None:
            keep = 1 - np.clip(avoid, 0, 1)
            M = M * keep
        bb = self._bbox(M)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        area = float(M[y0:y1, x0:x1].sum())
        if area < 1: return 0
        # mean stroke footprint from a sample
        sx = r.uniform(x0, x1, 600).astype(np.float32); sy = r.uniform(y0, y1, 600).astype(np.float32)
        Lm = float(self._sizes(length, sx, sy, r).mean()); Wm = float(self._sizes(width, sx, sy, r).mean())
        n_cells = int(density * (x1 - x0) * (y1 - y0) / (0.75 * Lm * Wm)) + 1
        arr = isinstance(region, np.ndarray)
        x, y = self._seed_points(np.sqrt(M) if arr else M, bb, n_cells, r)
        n = len(x)
        if not n: return 0
        o = r.permutation(n); x, y = x[o], y[o]
        L = self._sizes(length, x, y, r); Wd = self._sizes(width, x, y, r)
        cols = self._colours(colour, x, y, r)
        if value: cols *= (1 + value * r.normal(0, 1, n).astype(np.float32))[:, None]
        if hue: cols = hue_rotate(cols, (hue * r.normal(0, 1, n)).astype(np.float32))
        cols = np.clip(cols, 0, 1)
        fld = self._field_rad(field)
        P = self._centrelines(x, y, L, fld, (jitter * r.normal(0, 1, n)).astype(np.float32),
                              (bend * r.normal(0.6, 0.6, n)).astype(np.float32), k)
        if isinstance(clip, str) and clip == 'auto':
            clip = smoothstep(0.0, 0.06, M) if arr else None
        if avoid is not None:
            clip = keep if clip is None else clip * keep
        if isinstance(fade, str) and fade == 'auto':
            fade = (M ** 0.65) if arr else None
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (n,)) * r.uniform(0.92, 1.06, n).astype(np.float32)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,)) * r.uniform(0.85, 1.0, n).astype(np.float32)
        self._draw(P, Wd, cols, al, pr, taper, opacity, clip, passes, r, fade=fade)
        self.n_strokes += n
        return n

    def strokes(self, paths, colour='umber', width=2.0, pressure=0.7, opacity=0.3, alpha=0.9, taper=(0.4, 0.15),
                value=0.05, hue=0.02, clip=None, passes=1, k=None, seed=None):
        """draw explicit strokes: a list of polylines (each (m, 2)); they are resampled to k points each"""
        self._need()
        r = self._r(seed)
        if not len(paths): return 0
        if k is None: k = max(3, min(9, int(np.median([len(p) for p in paths]))))
        P = np.stack([_resample_k(np.asarray(p, np.float32), k) for p in paths]).astype(np.float32)
        n = len(P)
        mid = P[:, k // 2]
        Wd = self._sizes(width, mid[:, 0], mid[:, 1], r)
        cols = self._colours(colour, mid[:, 0], mid[:, 1], r)
        if value: cols *= (1 + value * r.normal(0, 1, n).astype(np.float32))[:, None]
        if hue: cols = hue_rotate(cols, (hue * r.normal(0, 1, n)).astype(np.float32))
        cols = np.clip(cols, 0, 1)
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (n,)) * r.uniform(0.94, 1.04, n).astype(np.float32)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,)) * r.uniform(0.88, 1.0, n).astype(np.float32)
        self._draw(P, Wd, cols, al, pr, taper, opacity, clip, passes, r)
        self.n_strokes += n
        return n

    def _draw(self, P, Wd, cols, al, pr, taper, opacity, clip, passes, r, ss=2, fill=0.4, fade=None):
        n = len(P)
        tp = np.broadcast_to(np.asarray(taper, np.float32), (n, 2))
        passes = max(1, int(passes))
        for g in range(passes):
            sel = np.arange(g, n, passes)
            if len(sel):
                self._raster(P[sel], Wd[sel], cols[sel], al[sel], pr[sel], tp[sel], opacity, clip, ss, fill, fade)

    def _raster(self, P, Wd, cols, al, pr, tp, opacity, clip, ss, fill, fade=None):
        n = len(P)
        lo = P.reshape(-1, 2).min(0) - Wd.max() - 2; hi = P.reshape(-1, 2).max(0) + Wd.max() + 2
        x0, y0 = max(0, int(np.floor(lo[0]))), max(0, int(np.floor(lo[1])))
        x1, y1 = min(self.W, int(np.ceil(hi[0]))), min(self.H, int(np.ceil(hi[1])))
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        Q = ((P - np.array([x0, y0], np.float32)) * ss).reshape(n, -1).tolist()
        wi = np.maximum(1, np.round(Wd * ss)).astype(np.int32).tolist()
        for i in range(n):
            d.line(Q[i], fill=i + 1, width=wi[i])
        flat = np.asarray(im, dtype=np.int32).ravel()
        nz = np.flatnonzero(flat)
        if not len(nz): return
        sid = flat[nz]
        W2 = w * ss
        sy = nz // W2; sx = nz - sy * W2
        # per-stroke tables (index 0 unused)
        s = P[:, 0]; e = P[:, -1]
        dv = e - s
        Ls = np.linalg.norm(dv, axis=1) + 1e-3
        dv = dv / Ls[:, None]
        ang = np.mod(np.arctan2(dv[:, 1], dv[:, 0]), np.pi)
        BIN = np.r_[0, (np.round(ang / np.pi * 8).astype(np.int32) % 8)]
        SX = np.r_[0, s[:, 0]].astype(np.float32); SY = np.r_[0, s[:, 1]].astype(np.float32)
        DX = np.r_[0, dv[:, 0]].astype(np.float32); DY = np.r_[0, dv[:, 1]].astype(np.float32)
        IL = np.r_[0, 1 / Ls].astype(np.float32)
        PR = np.r_[0, pr].astype(np.float32); AL = np.r_[0, al].astype(np.float32)
        T0 = np.r_[0, tp[:, 0]].astype(np.float32); T1 = np.r_[0, tp[:, 1]].astype(np.float32)
        X = x0 + (sx + 0.5) / ss; Y = y0 + (sy + 0.5) / ss
        u = np.clip(((X - SX[sid]) * DX[sid] + (Y - SY[sid]) * DY[sid]) * IL[sid], 0, 1)
        t0 = T0[sid]; t1 = T1[sid]
        prof = np.minimum(np.clip(t0 + (1 - t0) * u / 0.16, 0, 1), np.clip(t1 + (1 - t1) * (1 - u) / 0.5, 0, 1))
        iy = y0 + sy // ss; ix = x0 + sx // ss
        Tt = self.TD[BIN[sid], iy, ix]
        p = PR[sid] * (0.6 + 0.4 * prof)
        catch = np.clip((Tt + fill * self.F[iy, ix] - (1 - p)) * 4.5 + 0.5, 0, 1)
        catch = self.floor + (1 - self.floor) * catch
        A = AL[sid] * catch * (0.45 + 0.55 * prof)
        pix = (sy // ss) * w + (sx // ss)
        npx = w * h
        k2 = 1.0 / (ss * ss)
        a1 = np.bincount(pix, A, npx).astype(np.float32) * k2
        c3 = np.empty((npx, 3), np.float32)
        CL = np.vstack([np.zeros((1, 3), np.float32), cols])
        for ch in range(3):
            c3[:, ch] = np.bincount(pix, A * CL[sid, ch], npx) * k2
        a1 = a1.reshape(h, w); c3 = c3.reshape(h, w, 3)
        if clip is not None:
            cf = clip[y0:y1, x0:x1]
            # a soft, slightly wandering edge
            cf = np.clip((cf - 0.5) * 1.6 + 0.5 + 0.35 * self.EN[y0:y1, x0:x1] * (cf > 0.02) * (cf < 0.98), 0, 1)
            a1 = a1 * cf; c3 = c3 * cf[..., None]
        if fade is not None:
            ff = fade[y0:y1, x0:x1]
            a1 = a1 * ff; c3 = c3 * ff[..., None]
        m = a1 > 1e-4
        if not m.any(): return
        col = c3[m] / a1[m][:, None]
        Cb = self.C[y0:y1, x0:x1]
        old = Cb[m]
        tgt = (1 - opacity) * np.clip(old * col / self.P, 0, 1) + opacity * col
        Cb[m] = old + a1[m][:, None] * (tgt - old)
        Fb = self.F[y0:y1, x0:x1]
        Fb[m] = np.minimum(1.4, Fb[m] + a1[m] * 0.5)

    # ================================================================== lines and edges
    def line(self, path, colour='umber', width=2.0, pressure=0.62, alpha=0.8, opacity=0.3, seg=(36, 90),
             wobble=0.7, taper=(0.3, 0.15), smooth=True, clip=None, gaps=0.0, seed=None):
        """a soft pencil line along a path, drawn as several overlapping sketchy strokes (gaps: the chance that a
        stroke is left out, for a broken line)"""
        r = self._r(seed)
        P = spline(path, 10) if (smooth and len(path) > 2) else np.asarray(path, np.float32)
        P = _resample(P, 2.0)
        if len(P) < 2: return 0
        total = len(P) * 2.0
        paths = []
        i = 0
        while i < len(P) - 1:
            L = r.uniform(*seg) / 2.0
            j = min(len(P), int(i + L))
            q = P[i:j].copy()
            if len(q) >= 2:
                nn = np.array([-(q[-1, 1] - q[0, 1]), q[-1, 0] - q[0, 0]], np.float32)
                nn /= np.linalg.norm(nn) + 1e-6
                q += nn * (r.normal(0, wobble) + fbm1d(len(q), max(3, len(q) / 2), 2, int(r.integers(1 << 30)))[:, None] * wobble * 0.6)
                if not (gaps and r.random() < gaps): paths.append(q)
            i = max(i + 1, int(j - r.uniform(0.15, 0.35) * L))
        if total < 3 or not paths: return 0
        return self.strokes(paths, colour, width, pressure, opacity, alpha, taper, clip=clip, k=7, seed=int(r.integers(1 << 30)))

    def edge(self, mask, colour='umber', width=(1.3, 2.0), density=0.7, pressure=0.55, alpha=0.75, band=2.2,
             length=(14, 34), opacity=0.3, where=None, seed=None):
        """a faint, broken pencil contour in the local colour: short strokes along the outline of a mask
        (`where` restricts it, e.g. to the shadow side)"""
        m = blur(mask.astype(np.float32), band)
        b = smoothstep(0.12, 0.45, m) * smoothstep(0.88, 0.5, m)
        if where is not None: b = b * where
        b = b * (0.55 + 0.45 * smoothstep(0.3, 0.7, noise2d(self.H, self.W, 40, 2, int(self._r(seed).integers(1 << 30)))))
        return self.hatch(b, self.contour(mask, 2.5), colour, length, width, density, pressure, opacity, alpha,
                          jitter=0.04, bend=0.02, clip=None, passes=1, seed=seed)

    # ================================================================== modelling
    def form(self, mask, colours, field=-35.0, light=(-0.62, -0.58, 0.53), cross=26.0, length=(16, 38),
             width=(1.6, 2.5), density=1.2, pressure=0.74, warm=None, cool=None, edge=None, lit=None,
             opacity=0.3, sigma=None, wrap=0.2, deep_from=0.62, avoid=None, passes=2, seed=None):
        """model a shape in layered pencil. colours = (light, local, shadow[, deepest]) of one family; field is the
        form's own stroke direction (degrees or a field); layers cross at +-cross degrees. warm: a glaze on the lit
        side (a paint), cool: a glaze in the shadow. lit: a precomputed 0..1 light field (else shading(mask, light)).
        Returns the light field."""
        r = self._r(seed)
        if lit is None: lit = self.shading(mask, light, sigma, wrap)
        sh = 1 - lit
        f0 = self._field_rad(field)
        f1 = self.rotate(f0, cross); f2 = self.rotate(f0, -cross * 0.7)
        sd = lambda: int(r.integers(1 << 30))
        cl = smoothstep(0.02, 0.5, mask)
        kw = dict(clip=cl, avoid=avoid, passes=passes)
        self.hatch(mask, f0, colours[0], length, width, density * 0.9, pressure * 0.9, opacity, seed=sd(), **kw)
        self.hatch(mask * (0.3 + 0.7 * smoothstep(0.05, 0.6, sh)), f1, colours[1], length, width, density,
                   pressure, opacity, seed=sd(), **kw)
        self.hatch(mask * smoothstep(0.3, 0.85, sh), f2, colours[2], length, width, density * 0.95,
                   min(0.95, pressure * 1.05), opacity, seed=sd(), **kw)
        if len(colours) > 3:
            sl = (length[0] * 0.8, length[1] * 0.8) if not np.isscalar(length) and not callable(length) else length
            self.hatch(mask * smoothstep(deep_from, 1.05, sh) ** 1.1, f0, colours[3], sl, width, density * 0.8,
                       min(0.95, pressure * 1.08), opacity, seed=sd(), **kw)
        if warm is not None:
            self.hatch(mask * smoothstep(0.4, 1.0, lit), f1, warm, length, width, density * 0.75, pressure * 0.92,
                       max(opacity, 0.5), alpha=0.8, seed=sd(), **kw)
        if cool is not None:
            self.hatch(mask * smoothstep(0.45, 1.0, sh) * 0.75, f2, cool, length, width, density * 0.55,
                       pressure * 0.88, opacity, alpha=0.75, seed=sd(), **kw)
        if edge is not None:
            self.edge(mask, edge, where=0.35 + 0.65 * smoothstep(0.3, 0.8, sh), seed=sd())
        return lit

    # ================================================================== hair, grass, leaves
    def fur(self, region, field, colour, length=(14, 30), width=(1.0, 1.6), density=0.9, tuft=(5, 12), spread=0.3,
            curl=0.12, converge=1.0, pressure=0.74, opacity=0.32, alpha=0.6, taper=(0.75, 0.04), clip='auto',
            value=0.05, hue=0.025, k=7, avoid=None, fade='auto', side=0.14, light=(-0.62, -0.58), seed=None):
        """tufts of fine strokes following the lie of the hair. Each tuft: `tuft` strands whose roots spread
        across the clump (spread x length) and whose tips converge (converge 1) or fan out (converge -1),
        curling `curl` the same way, pressed at the root and lifting off at the tip. side: the strands on the
        side of a tuft away from `light` are darker by this much (each lock has a lit and a shadowed flank).
        density ~ how many times the tufts tile the region."""
        self._need()
        r = self._r(seed)
        M = self._mask(region)
        if avoid is not None: M = M * (1 - np.clip(avoid, 0, 1))
        bb = self._bbox(M)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        sx = r.uniform(x0, x1, 400).astype(np.float32); sy = r.uniform(y0, y1, 400).astype(np.float32)
        Lm = float(self._sizes(length, sx, sy, r).mean())
        tw = spread * Lm
        n_cells = int(density * (x1 - x0) * (y1 - y0) / (0.8 * Lm * max(tw, 2.0))) + 1
        arr = isinstance(region, np.ndarray)
        cx, cy = self._seed_points(np.sqrt(M) if arr else M, bb, n_cells, r)
        nt = len(cx)
        if not nt: return 0
        fld = self._field_rad(field)
        a = _lookup(fld, cx, cy) + r.normal(0, 0.09, nt).astype(np.float32)
        # flip so that a field given mod pi still points the same way locally: keep as is (hair direction given)
        L = self._sizes(length, cx, cy, r)
        cnt = r.integers(tuft[0], tuft[1] + 1, nt)
        cv = (curl * r.normal(1.0, 0.5, nt) * np.sign(r.normal(0, 1, nt) + 0.6)).astype(np.float32)
        paths = []; tcol = []; lat = []
        L2 = np.asarray(light[:2], np.float32); L2 = L2 / (np.linalg.norm(L2) + 1e-6)
        for i in range(nt):
            d = np.array([np.cos(a[i]), np.sin(a[i])], np.float32)
            nrm = np.array([-d[1], d[0]], np.float32)
            m = int(cnt[i])
            off = (np.linspace(-0.5, 0.5, m) + r.normal(0, 0.12, m)) * spread * L[i]
            base = np.array([cx[i], cy[i]], np.float32)
            tip = base + d * L[i]
            sgn = 1.0 if float(nrm @ L2) > 0 else -1.0
            for j in range(m):
                lj = L[i] * r.uniform(0.7, 1.08)
                root = base + nrm * off[j] - d * r.uniform(0, 0.25) * L[i]
                end = tip + nrm * off[j] * (1 - converge * 0.85) + d * (lj - L[i]) + r.normal(0, 0.06 * L[i], 2)
                ctrl = (root + end) / 2 + nrm * cv[i] * lj + r.normal(0, 0.03 * L[i], 2)
                t = np.linspace(0, 1, k)[:, None]
                paths.append(((1 - t) ** 2 * root + 2 * t * (1 - t) * ctrl + t * t * end).astype(np.float32))
                tcol.append(i); lat.append(sgn * off[j] / max(1e-3, spread * L[i]))
        P = np.stack(paths).astype(np.float32)
        n = len(P)
        tcol = np.asarray(tcol)
        mid = P[:, k // 2]
        Wd = self._sizes(width, mid[:, 0], mid[:, 1], r)
        tc = self._colours(colour, cx, cy, r)
        cols = tc[tcol] * (1 + 0.5 * value * r.normal(0, 1, n).astype(np.float32))[:, None]
        cols *= (1 + value * r.normal(0, 1, nt).astype(np.float32))[tcol][:, None]
        if side: cols *= (1 + side * 2 * np.clip(np.asarray(lat, np.float32), -0.6, 0.6))[:, None]
        if hue: cols = hue_rotate(cols, (hue * r.normal(0, 1, n)).astype(np.float32))
        cols = np.clip(cols, 0, 1)
        if isinstance(clip, str) and clip == 'auto':
            clip = None
        if avoid is not None:
            keep = 1 - np.clip(avoid, 0, 1)
            clip = keep if clip is None else clip * keep
        if isinstance(fade, str) and fade == 'auto':
            fade = blur(M, 3.0) ** 0.6 if arr else None
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (n,)) * r.uniform(0.9, 1.06, n).astype(np.float32)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,)) * r.uniform(0.85, 1.0, n).astype(np.float32)
        o = r.permutation(n)
        self._draw(P[o], Wd[o], cols[o], al[o], pr[o], taper, opacity, clip, 2, r, fade=fade)
        self.n_strokes += n
        return n

    def grass(self, region, colour=('grass', 'leaf', 'yellowgreen'), height=(26, 60), lean=-90.0, sway=14.0,
              width=(1.3, 2.1), density=0.5, tuft=(3, 7), fan=0.5, curl=0.1, pressure=0.74, opacity=0.32,
              clip=None, avoid=None, seed=None):
        """tufts of grass: blades rising from the region (lean = direction in degrees, -90 = up), fanning out"""
        f = self.flow(lean, sway, 160)
        return self.fur(region, f, colour, height, width, density, tuft, spread=0.18, curl=curl, converge=-fan,
                        pressure=pressure, opacity=opacity, taper=(0.85, 0.02), clip=clip, avoid=avoid, seed=seed)

    def leaves(self, region, colour, size=(8, 16), density=0.9, field=None, curl=0.35, pressure=0.74,
               opacity=0.32, width=(1.4, 2.2), clip=None, avoid=None, seed=None):
        """a crown laid as clumps of short curved leaf strokes (3-6 per clump, fanned)"""
        f = self.flow(-60, 70, 50) if field is None else field
        return self.fur(region, f, colour, size, width, density, (3, 6), spread=0.6, curl=curl, converge=0.2,
                        pressure=pressure, opacity=opacity, taper=(0.55, 0.2), clip=clip, avoid=avoid, seed=seed)

    def pelt(self, mask, colours, field, light=(-0.62, -0.58, 0.53), length=(12, 26), width=(1.0, 1.6),
             density=1.0, tuft=(5, 11), spread=0.3, curl=0.12, lit=None, under=True, avoid=None, seed=None):
        """a whole fur coat: a soft pencil under-layer, dark short locks in the shadow, locks of the local colour
        all over, light-tipped locks on the lit side. colours = (light, local, shadow[, deepest]). Returns light."""
        r = self._r(seed)
        sd = lambda: int(r.integers(1 << 30))
        if lit is None: lit = self.shading(mask, light)
        if under:
            self.form(mask, colours, field, light, length=(length[0] * 1.3, length[1] * 1.6), density=0.8 * density,
                      lit=lit, avoid=avoid, seed=sd())
        dark = colours[3] if len(colours) > 3 else colours[2]
        kw = dict(width=width, tuft=tuft, spread=spread, curl=curl, avoid=avoid, light=light[:2])
        self.fur(mask * smoothstep(0.3, 0.9, 1 - lit), field, dark, (length[0] * 0.8, length[1] * 0.85),
                 density=0.8 * density, pressure=0.8, seed=sd(), **kw)
        self.fur(mask * (0.4 + 0.6 * smoothstep(0.1, 0.7, 1 - lit)), field, colours[2], length, density=0.8 * density,
                 seed=sd(), **kw)
        self.fur(mask, field, colours[1], length, density=density, seed=sd(), **kw)
        self.fur(mask * smoothstep(0.35, 0.95, lit), field, colours[0], (length[0] * 0.8, length[1] * 0.85),
                 density=0.75 * density, opacity=0.5, seed=sd(), **kw)
        return lit

    def scales(self, mask, size=16.0, colours=('sand', 'tan'), groove='umber', field=0.0, light=(-0.62, -0.58),
               lit=None, density=1.0, pressure=0.72, seed=None):
        """overlapping reptile scales: a staggered grid of small domes along `field` (degrees or a field), each
        filled with a few short strokes, lighter on its lit side, with a darker crease along its shadowed rim"""
        r = self._r(seed)
        bb = self._bbox(mask)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        cs = []
        row = 0
        yy = y0 + r.uniform(0, size * 0.5)
        while yy < y1 + size:
            xx = x0 + (size * 0.5 if row % 2 else 0) + r.uniform(-0.15, 0.15) * size
            while xx < x1 + size:
                cs.append((xx + r.normal(0, 0.1 * size), yy + r.normal(0, 0.1 * size)))
                xx += size * r.uniform(0.92, 1.08)
            yy += size * 0.78; row += 1
        cs = np.asarray(cs, np.float32)
        inside = _lookup(mask, cs[:, 0], cs[:, 1]) > 0.6
        cs = cs[inside]
        if not len(cs): return 0
        fld = self._field_rad(field)
        ang = _lookup(fld, cs[:, 0], cs[:, 1])
        L2 = np.asarray(light[:2], np.float32); L2 = L2 / (np.linalg.norm(L2) + 1e-6)
        fills, rims, fc, li = [], [], [], []
        lv = _lookup(lit, cs[:, 0], cs[:, 1]) if lit is not None else np.full(len(cs), 0.6, np.float32)
        for (cx, cy), a, l in zip(cs, ang, lv):
            s_ = size * r.uniform(0.42, 0.55)
            d = np.array([np.cos(a), np.sin(a)], np.float32); nrm = np.array([-d[1], d[0]], np.float32)
            nst = max(2, int(4 * density))
            for j in range(nst):
                o = (j / (nst - 1) - 0.5) * 1.4 * s_
                ln = s_ * np.sqrt(max(0.05, 1 - (o / s_) ** 2)) * 0.9
                c = np.array([cx, cy], np.float32) + nrm * o
                fills.append(np.stack([c - d * ln, c, c + d * ln]))
                fc.append(1.0 + 0.12 * np.sign(float(nrm @ L2)) * (o / s_))
                li.append(l)
            # the crease on the side away from the light
            t = np.linspace(-1.1, 1.1, 7) + np.arctan2(-L2[1], -L2[0])
            rims.append(np.stack([cx + s_ * 1.02 * np.cos(t), cy + s_ * 0.86 * np.sin(t)], 1))
        R = ramp(list(colours))
        li = np.asarray(li, np.float32)
        base = ramp_at(R, li) * np.asarray(fc, np.float32)[:, None]
        self.strokes(fills, lambda x, y, c=np.clip(base, 0, 1): c, (1.2, 1.7), pressure, 0.32, 0.7, (0.6, 0.4),
                     clip=mask, k=3, seed=int(r.integers(1 << 30)))
        self.strokes(rims, groove, (1.2, 1.6), pressure, 0.3, 0.55, (0.2, 0.2), clip=mask, k=7,
                     seed=int(r.integers(1 << 30)))
        return len(cs)

    FLOWERS = {'daisy': ('white', 'butter'), 'buttercup': ('lemon', 'ochre'), 'poppy': ('vermilion', 'umber'),
               'forgetmenot': ('cornflower', 'butter'), 'pink': ('pink', 'gold'), 'clover': ('rose', 'mauve'),
               'cornflower': ('cobalt', 'indigo'), 'marigold': ('orange', 'amber')}

    def flowers(self, region, kinds=('daisy', 'buttercup', 'poppy', 'forgetmenot'), n=40, size=(4.0, 8.0),
                petals=(5, 6), stems=None, seed=None):
        """little wildflowers: petals as short rounded strokes round a centre dot; `stems` (a paint) draws a thin
        stem below each. kinds are FLOWERS names."""
        r = self._r(seed)
        M = self._mask(region)
        bb = self._bbox(M)
        if bb is None: return 0
        x, y = self._seed_points(M, bb, n * 4, r)
        if len(x) > n:
            pick = r.choice(len(x), n, replace=False); x, y = x[pick], y[pick]
        if not len(x): return 0
        if stems:
            sp = [np.array([[xi, yi + 1], [xi + r.normal(0, 1.5), yi + r.uniform(2.5, 4.5) * sz]], np.float32)
                  for xi, yi, sz in zip(x, y, r.uniform(*size, len(x)))]
            self.strokes(sp, stems, (1.0, 1.4), 0.7, 0.3, 0.7, (0.5, 0.3), k=3, seed=int(r.integers(1 << 30)))
        P, C, D, DC = [], [], [], []
        for xi, yi in zip(x, y):
            kind = kinds[int(r.integers(len(kinds)))]
            pc, cc = self.FLOWERS.get(kind, (kind, 'butter'))
            s_ = r.uniform(*size)
            np_ = int(r.integers(petals[0], petals[1] + 1))
            a0 = r.uniform(0, 2 * np.pi); sq = r.uniform(0.6, 0.95)        # seen a little from the side
            for j in range(np_):
                a = a0 + 2 * np.pi * j / np_ + r.normal(0, 0.12)
                for k_ in (-0.18, 0.18):
                    b = a + k_
                    p0 = (xi + np.cos(b) * s_ * 0.2, yi + np.sin(b) * s_ * 0.2 * sq)
                    p1 = (xi + np.cos(b) * s_, yi + np.sin(b) * s_ * sq)
                    P.append(np.array([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2), p1], np.float32))
                    C.append(hexc(pc))
            D.append((xi, yi, s_)); DC.append(hexc(cc))
        cols = np.asarray(C, np.float32)
        self.strokes(P, lambda xx, yy, c=cols: c, (1.4, 2.0), 0.8, 0.6, 0.85, (0.9, 0.55), k=3,
                     seed=int(r.integers(1 << 30)))
        cp = []
        for (xi, yi, s_) in D:
            q = s_ * 0.22
            cp += [np.array([[xi - q, yi], [xi + q, yi]], np.float32), np.array([[xi, yi - q], [xi, yi + q]], np.float32)]
        cc = np.repeat(np.asarray(DC, np.float32), 2, 0)
        self.strokes(cp, lambda xx, yy, c=cc: c, (1.5, 2.0), 0.85, 0.6, 0.9, (0.9, 0.8), k=2,
                     seed=int(r.integers(1 << 30)))
        return len(x)

    def stone(self, cx, cy, rx, ry, colours=('pebble', 'stone', 'warmgrey', 'umber'), moss=None, flat=0.35,
              light=(-0.62, -0.58, 0.53), warm='sand', cool='periwinkle', avoid=None, seed=None):
        """a rounded stone with a flattish top: contour-hatched, lit from `light`, an optional mossy cap
        (moss = list of paints). Returns its mask."""
        r = self._r(seed)
        sd = lambda: int(r.integers(1 << 30))
        pts = blob_pts(cx, cy, rx, ry, 0.07, 60, sd())
        pts[:, 1] = np.where(pts[:, 1] < cy, cy - (cy - pts[:, 1]) * (1 - flat * 0.5), pts[:, 1])
        m = self.poly(pts, smooth=True)
        if avoid is not None: m = m * (1 - avoid)
        self.form(m, colours, self.contour(m, max(2.0, ry * 0.15), fallback=-20), light, length=(rx * 0.12, rx * 0.35),
                  width=(1.4, 2.1), warm=warm, cool=cool, sigma=max(3.0, ry * 0.5), seed=sd())
        self.edge(m, colours[-1], density=0.5, where=smoothstep(cy - ry * 0.2, cy + ry, self.YY), seed=sd())
        if moss:
            top = m * smoothstep(cy - ry * 0.1, cy - ry * 0.7, self.YY)
            self.fur(top, -90, list(moss), (3, 7), (1.0, 1.4), 1.1, (3, 6), 0.4, 0.15, seed=sd())
        return m

    def cottage(self, x, y, w, h, wall=('cream', 'ivory', 'sand', 'tan'), roof=('peach', 'terracotta', 'brick', 'sienna'),
                windows=((0.25, 0.35, 0.22, 0.3),), door=(0.62, 0.24, 0.5), chimney=0.72, roof_h=0.75,
                light=(-0.7, -0.5, 0.5), glow=1.0, avoid=None, seed=None):
        """a small storybook cottage standing on y (bottom), x = left, w wide, walls h high, a pitched roof
        roof_h x w tall; windows are (fx, fy, fw, fh) fractions of the wall, lit; door (fx, fw, fh) or None.
        Returns its mask."""
        r = self._r(seed)
        sd = lambda: int(r.integers(1 << 30))
        top = y - h
        wallm = self.rect(x, top, x + w, y)
        rf = [(x - w * 0.09, top + 2), (x + w * 0.5, top - roof_h * w), (x + w * 1.09, top + 2)]
        roofm = self.poly(rf)
        chm = None
        if chimney:
            cxp = x + w * chimney
            yr = top - roof_h * w * (1 - abs(chimney - 0.5) * 2) + 4
            chm = self.rect(cxp - w * 0.06, yr - roof_h * w * 0.38, cxp + w * 0.06, yr + 6) * (1 - roofm * 0)
        whole = np.clip(wallm + roofm + (chm if chm is not None else 0), 0, 1)
        if avoid is not None:
            wallm = wallm * (1 - avoid); roofm = roofm * (1 - avoid); whole = whole * (1 - avoid)
        sl = (max(4, w * 0.08), max(8, w * 0.22))
        self.form(wallm, wall, 92, light, length=sl, width=(1.3, 1.9), density=1.4, sigma=w * 0.4, seed=sd())
        # shadow under the eaves
        self.hatch(wallm * smoothstep(top + h * 0.3, top, self.YY), 0, wall[-1], sl, (1.3, 1.8), 0.9, 0.7,
                   alpha=0.5, seed=sd())
        a = np.rad2deg(np.arctan2(roof_h * w, w * 0.59))
        rfld = np.where(self.XX < x + w * 0.5, np.deg2rad(-a), np.deg2rad(a)).astype(np.float32)
        self.form(roofm, roof, rfld, light, length=sl, width=(1.3, 1.9), density=1.4, sigma=w * 0.3, seed=sd())
        self.line([rf[0], rf[1], rf[2]], roof[-1], 1.5, 0.66, 0.6, 0.35, seg=(w * 0.3, w * 0.6), smooth=False, seed=sd())
        if chm is not None:
            cm = chm * (1 - roofm * 0.0)
            self.form(cm, roof[1:] if len(roof) > 3 else roof, 90, light, length=(4, 10), width=(1.2, 1.7),
                      density=1.4, seed=sd())
        for (fx, fy, fw, fh) in windows:
            self.window(x + w * fx, top + h * fy, x + w * (fx + fw), top + h * (fy + fh), glow=glow, seed=sd())
        if door:
            fx, fw, fh = door
            dm = self.rect(x + w * fx, y - h * fh, x + w * (fx + fw), y)
            self.form(dm, ('tan', 'brown', 'umber'), 90, light, length=(4, 10), width=(1.2, 1.7), density=1.4, seed=sd())
        self.edge(wallm, wall[-1], density=0.4, seed=sd())
        return whole

    def tree_plan(self, x, y, h, r, clumps=7, lean=0.0, seed=0):
        """the layout of tree(): (crown mask, trunk mask, per-clump light, blobs) -- deterministic for a seed, so a
        background can be coloured round a tree before the tree itself is drawn"""
        rr = np.random.default_rng(seed)
        top = (x + lean * h, y - h)
        tm = self.tube([(x, y + 4), (x + lean * h * 0.4, y - h * 0.45), top], max(4.0, r * 0.16), max(2.5, r * 0.07))
        cx, cy = top[0], top[1] - r * 0.25
        blobs = []
        for k in range(clumps):
            a = 2 * np.pi * k / clumps + rr.normal(0, 0.25)
            d = r * rr.uniform(0.42, 0.7)
            blobs.append((cx + np.cos(a) * d * 1.12, cy + np.sin(a) * d * 0.78, r * rr.uniform(0.3, 0.44),
                          int(rr.integers(1 << 30))))
        for k in range(max(2, clumps // 3)):
            a = rr.uniform(0, 2 * np.pi)
            blobs.append((cx + np.cos(a) * r * 0.2, cy + np.sin(a) * r * 0.15, r * rr.uniform(0.36, 0.48),
                          int(rr.integers(1 << 30))))
        crown = np.zeros((self.H, self.W), np.float32)
        for (bx, by, br, bs) in blobs:
            crown = np.maximum(crown, self.blob(bx, by, br, br * 0.86, 0.14, seed=bs))
        return crown, tm, blobs, top

    def tree(self, x, y, h, r, colours=('lemon', 'gold', 'amber', 'olive'), trunk=('tan', 'brown', 'umber'), clumps=7,
             leaf=(7, 14), light=(-0.62, -0.58, 0.53), lean=0.0, avoid=None, branches=True, seed=0):
        """a storybook tree: a trunk from (x, y) rising h px, a crown of `clumps` rounded clumps of radius ~r,
        each lit from `light` and laid as short curved leaf strokes (dark clump under-layer, local, light tops),
        branches showing in the gaps. Returns the crown mask (same layout as tree_plan with the same seed)."""
        crown, tm, blobs, top = self.tree_plan(x, y, h, r, clumps, lean, seed)
        rr = np.random.default_rng(seed + 1)
        sd = lambda: int(rr.integers(1 << 30))
        lits = np.zeros_like(crown)
        for (bx, by, br, bs) in sorted(blobs, key=lambda b: -b[1]):
            m = self.blob(bx, by, br, br * 0.86, 0.14, seed=bs)
            lits = lits * (1 - m) + self.shading(m, light, br * 0.5) * m
        if avoid is not None:
            crown = crown * (1 - avoid); tm = tm * (1 - avoid)
        self.form(tm, trunk, 90, light, length=(max(5, r * 0.12), max(10, r * 0.3)), width=(1.3, 1.9), density=1.4,
                  seed=sd())
        if branches:
            for k in range(4):
                a = np.deg2rad(-90 + rr.uniform(-70, 70))
                L = r * rr.uniform(0.5, 0.95)
                p1 = (top[0] + np.cos(a) * L, top[1] + np.sin(a) * L * 0.8)
                bm = self.tube([(top[0], top[1] + r * 0.3), ((top[0] + p1[0]) / 2, (top[1] + p1[1]) / 2 + 3), p1],
                               max(2.5, r * 0.07), 1.5)
                self.hatch(bm, a * 180 / np.pi, trunk[2], (6, 14), (1.2, 1.6), 1.6, 0.8, 0.35, alpha=0.7, seed=sd())
        cfield = self.flow(-55, 60, max(20, r * 0.4), seed=sd())
        self.form(crown, colours, cfield, light, length=(leaf[0] * 1.4, leaf[1] * 1.8), width=(1.4, 2.0),
                  density=0.9, lit=lits, seed=sd())
        dk = colours[3] if len(colours) > 3 else colours[2]
        self.leaves(crown * smoothstep(0.45, 0.9, 1 - lits), dk, leaf, 0.9, pressure=0.8, seed=sd())
        self.leaves(crown * (0.2 + 0.8 * smoothstep(0.2, 0.7, 1 - lits)), colours[2], leaf, 0.8, seed=sd())
        self.leaves(crown * (0.3 + 0.7 * smoothstep(0.25, 0.7, lits)), colours[1], leaf, 0.9, seed=sd())
        self.leaves(crown * smoothstep(0.5, 0.95, lits), colours[0], leaf, 0.85, opacity=0.6, seed=sd())
        return crown

    # ================================================================== light
    def glow(self, x, y, r, colours='glow', strength=1.0, density=1.3, length=(10, 26), width=(1.5, 2.3),
             halo=0.45, squash=1.0, clip=None, opacity=0.7, pressure=0.72, field=None, seed=None):
        """warm light as strokes radiating from (x, y): white-yellow near the source, orange further out, thinning
        into the surroundings, over a soft tooth-textured lift of the paper (halo)"""
        R = ramp(colours)
        d = np.sqrt((self.XX - x) ** 2 + ((self.YY - y) / squash) ** 2) / r
        if halo:
            hm = (halo * strength * np.exp(-d * d * 1.6) * (0.7 + 0.3 * self.T))
            if clip is not None: hm = hm * clip
            col = ramp_at(R, np.clip(d * 0.55, 0, 1))
            self.C += hm[..., None] * (col - self.C)
        prob = np.clip(strength * np.exp(-d * d * 0.9), 0, 1) * (d < 2.6)
        if clip is not None: prob = prob * clip
        fld = self.flow(-25, 35, 30) if field is None else field
        return self.hatch(prob, fld, (R, lambda xx, yy: np.clip(np.sqrt((xx - x) ** 2 + ((yy - y) / squash) ** 2) / r * 0.55, 0, 1)),
                          length, width, density, pressure, opacity, 0.7, jitter=0.12, bend=0.02, value=0.04,
                          hue=0.02, taper=(0.6, 0.1), clip=clip, seed=seed)

    def lift(self, mask, colour='cream', amount=0.6, tooth=0.5):
        """kneaded-eraser / white-pencil lift: pull an area toward a light colour, more on the tooth peaks"""
        a = np.clip(mask * amount * (1 - tooth + tooth * self.T * 1.4), 0, 1)
        self.C += a[..., None] * (hexc(colour) - self.C)

    def window(self, x0, y0, x1, y1, panes=(2, 2), frame='umber', light=('glow', 'lantern', 'flame'), sill=True,
               glow=0.9, seed=None):
        """a lit window: butter-yellow at the centre, orange toward the frame, a few muntins, a small glow"""
        r = self._r(seed)
        sd = lambda: int(r.integers(1 << 30))
        m = self.rect(x0, y0, x1, y1)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rr = max(x1 - x0, y1 - y0) * 0.6
        d = np.clip(np.sqrt(((self.XX - cx) / (x1 - x0)) ** 2 + ((self.YY - cy) / (y1 - y0)) ** 2) * 1.6, 0, 1)
        R = ramp(light)
        self.lift(m, 'cream', 0.85, 0.2)
        s = max(4.0, (x1 - x0) * 0.35)
        self.hatch(m, 80, (R, lambda xx, yy: d[yy.astype(int).clip(0, self.H - 1), xx.astype(int).clip(0, self.W - 1)] * 0.9),
                   (s * 0.6, s * 1.3), (1.4, 2.0), 2.2, 0.8, 0.7, clip=m, seed=sd())
        self.hatch(m * smoothstep(0.55, 1.0, d), 20, light[-1], (s * 0.5, s), (1.3, 1.8), 0.9, 0.7, 0.5, clip=m, seed=sd())
        fw = max(1.4, (x1 - x0) * 0.07)
        for i in range(1, panes[0]):
            xx = x0 + (x1 - x0) * i / panes[0]
            self.line([(xx, y0), (xx, y1)], frame, fw, 0.8, 0.85, 0.5, seg=(200, 300), wobble=0.2, smooth=False)
        for j in range(1, panes[1]):
            yy = y0 + (y1 - y0) * j / panes[1]
            self.line([(x0, yy), (x1, yy)], frame, fw, 0.8, 0.85, 0.5, seg=(200, 300), wobble=0.2, smooth=False)
        fr = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        self.line(fr, frame, fw * 1.25, 0.8, 0.85, 0.5, seg=(40, 90), wobble=0.3, smooth=False)
        if sill:
            self.line([(x0 - fw * 1.5, y1 + fw), (x1 + fw * 1.5, y1 + fw)], frame, fw * 1.6, 0.8, 0.85, 0.5,
                      seg=(200, 300), wobble=0.2, smooth=False)
        if glow:
            self.glow(cx, cy, rr * 1.1, strength=0.5 * glow, density=0.7, length=(6, 14), width=(1.2, 1.8),
                      halo=0.25 * glow, seed=sd())

    # ================================================================== water
    def reflect(self, waterline, region, src=None, ripple=6.0, stretch=1.0, darken=0.1, tint='sky', mixw=0.25,
                soft=2.0, length=(30, 80), width=(1.6, 2.4), density=1.2, pressure=0.66, opacity=0.4,
                field=0.0, seed=None):
        """horizontal strokes whose colour is the mirrored picture above the waterline (an int, or a per-column
        array), pushed sideways by ripples and mixed toward `tint`: a reflection made of strokes"""
        S = (self.C if src is None else src)
        S = np.stack([blur(S[..., c], soft) for c in range(3)], -1) if soft else S
        wl = np.broadcast_to(np.asarray(waterline, np.float32), (self.W,)) if np.ndim(waterline) == 0 else \
            np.asarray(waterline, np.float32)
        rr = self._r(seed)
        rx = noise2d(self.H, self.W, 30, 2, int(rr.integers(1 << 30))) - 0.5
        tc = hexc(tint)

        def col(x, y):
            xi = np.clip(x.astype(np.int32), 0, self.W - 1)
            w0 = wl[xi]
            dy = np.maximum(0, y - w0) / stretch
            sy = np.clip(w0 - dy, 0, self.H - 1)
            sx = np.clip(x + ripple * 2 * _lookup(rx, x, y) * (1 + dy / 60), 0, self.W - 1)
            c = S[sy.astype(np.int32), sx.astype(np.int32)]
            return np.clip(c * (1 - darken) * (1 - mixw) + tc * mixw, 0, 1)

        return self.hatch(region, field, col, length, width, density, pressure, opacity, 0.9, jitter=0.03,
                          bend=0.01, value=0.04, hue=0.01, taper=(0.4, 0.2), seed=seed)

    def ripples(self, cx, cy, rx, ry, rings=3, colour='cream', width=1.8, pressure=0.7, opacity=0.6, gap=0.4,
                grow=1.35, seed=None):
        """broken elliptical pencil rings round something standing in the water"""
        r = self._r(seed)
        paths = []
        for k in range(rings):
            sx, sy = rx * grow ** k, ry * grow ** k
            a = r.uniform(0, 2 * np.pi)
            while a < 2 * np.pi + r.uniform(0, 1):
                L = r.uniform(0.5, 1.3)
                t = np.linspace(a, a + L, 9)
                if np.sin((a + L / 2)) > -0.65:          # mostly the near half of the ring
                    paths.append(np.stack([cx + sx * np.cos(t), cy + sy * np.sin(t)], 1))
                a += L + r.uniform(0.15, 0.5) * (1 + gap)
        if not paths: return 0
        return self.strokes(paths, colour, width, pressure, opacity, 0.85, (0.3, 0.2), k=9, seed=int(r.integers(1 << 30)))

    # ================================================================== small things and people
    def dots(self, region, colours, n=60, size=(2.0, 4.0), pressure=0.8, opacity=0.6, seed=None):
        """little pencil dabs (wildflowers far off, seeds): tiny tight scribbles"""
        r = self._r(seed)
        M = self._mask(region)
        bb = self._bbox(M)
        if bb is None: return 0
        x, y = self._seed_points(M, bb, n * 3, r)
        if len(x) > n:
            pick = r.choice(len(x), n, replace=False); x, y = x[pick], y[pick]
        paths = []; cl = []
        for i in range(len(x)):
            s = r.uniform(*size)
            a = r.uniform(0, np.pi)
            for j in range(3):
                b = a + j * np.pi / 3
                d = np.array([np.cos(b), np.sin(b)]) * s
                paths.append(np.array([[x[i] - d[0], y[i] - d[1]], [x[i], y[i]], [x[i] + d[0], y[i] + d[1]]], np.float32))
                cl.append(i)
        if not paths: return 0
        C = self._colours(colours, x, y, r)
        cols = C[np.asarray(cl)]
        return self.strokes(paths, lambda xx, yy, c=cols: c, (1.5, 2.2), pressure, opacity, 0.95, (0.8, 0.6), k=3,
                            seed=int(r.integers(1 << 30)))

    def eye(self, x, y, r=4.0, colour='eye', lid=None, look=(0.0, 0.0), glint=True, seed=None):
        """a gentle dot eye (soft-edged, pencil-dark, never black), optional heavy lid line above it"""
        m = self.ellipse(x + look[0], y + look[1], r, r * 1.12)
        self.hatch(m, 60, colour, (r * 0.8, r * 1.6), (1.1, 1.5), 3.0, 0.92, 0.6, clip=m, seed=seed)
        self.hatch(m, -30, colour, (r * 0.8, r * 1.6), (1.1, 1.5), 2.0, 0.9, 0.6, clip=m, seed=seed)
        if glint:
            g = self.ellipse(x + look[0] - r * 0.3, y + look[1] - r * 0.35, max(0.9, r * 0.28))
            self.lift(g, 'white', 0.85, 0.15)
        if lid is not None:
            w, sag, col = lid
            self.line([(x - w * 0.55, y - r * 0.9 + sag * 0.3), (x, y - r * 1.25 - sag), (x + w * 0.55, y - r * 0.8)],
                      col, 1.6, 0.66, 0.8, 0.35, seg=(200, 300), wobble=0.2)

    def blush(self, x, y, r=10.0, colour='cheek', amount=0.8, seed=None):
        """a rosy cheek: a soft round patch of fine circular strokes"""
        m = self.ellipse(x, y, r, r * 0.82)
        mm = blur(m, r * 0.35) * amount
        self.hatch(mm, self.contour(m, r * 0.3), colour, (r * 0.4, r * 0.9), (1.2, 1.7), 1.6, 0.6, 0.4, 0.75,
                   clip=None, seed=seed)

    def lantern(self, x, y, size=26.0, body='lantern', ribs='tangerine', cap='umber', handle=True, glow=None,
                seed=None):
        """a small round paper lantern hanging with its top at (x, y): warm ribs, a glowing middle, dark caps.
        Returns its centre. glow=r draws its light now (otherwise call glow() later)."""
        r = self._r(seed)
        sd = lambda: int(r.integers(1 << 30))
        s = size
        cx, cy = x, y + s * 0.62
        bodym = self.ellipse(cx, cy, s * 0.5, s * 0.46)
        self.lift(bodym, 'sun', 0.85, 0.1)
        self.hatch(bodym, 90, ('glow', np.clip(self.value(0.15, 0.75, cy - s * 0.45, cy + s * 0.45, 0), 0, 1)),
                   (s * 0.3, s * 0.6), (1.3, 1.8), 2.2, 0.8, 0.8, clip=bodym, seed=sd())
        d = np.sqrt(((self.XX - cx) / (s * 0.5)) ** 2 + ((self.YY - cy) / (s * 0.46)) ** 2)
        self.hatch(bodym * smoothstep(0.25, 1.0, d), 90, body, (s * 0.25, s * 0.5), (1.3, 1.8), 2.0, 0.82, 0.65,
                   clip=bodym, seed=sd())
        self.hatch(bodym * smoothstep(0.7, 1.05, d), 90, ribs, (s * 0.2, s * 0.4), (1.2, 1.6), 1.0, 0.8, 0.45,
                   clip=bodym, seed=sd())
        for k in (-0.6, -0.2, 0.2, 0.6):                    # ribs: vertical arcs
            xs = cx + k * s * 0.5
            ww = np.sqrt(max(0.0, 1 - k * k))
            self.line([(cx + k * s * 0.35, cy - s * 0.4 * ww), (xs, cy), (cx + k * s * 0.35, cy + s * 0.4 * ww)],
                      ribs, 1.3, 0.7, 0.7, 0.4, seg=(200, 300), wobble=0.15)
        for yy, w in ((cy - s * 0.46, s * 0.42), (cy + s * 0.46, s * 0.38)):
            cm = self.rect(cx - w / 2, yy - s * 0.07, cx + w / 2, yy + s * 0.07)
            self.hatch(cm, 0, cap, (s * 0.15, s * 0.3), (1.3, 1.8), 3.0, 0.85, 0.5, clip=cm, seed=sd())
        if handle:
            self.line([(cx, cy - s * 0.52), (cx, y)], cap, 1.4, 0.7, 0.8, 0.4, seg=(200, 300), wobble=0.1)
        self.line([(cx, cy + s * 0.53), (cx + 0.5, cy + s * 0.75)], ribs, 1.6, 0.7, 0.8, 0.4, seg=(200, 300), wobble=0.1)
        if glow: self.glow(cx, cy, glow, seed=sd())
        return cx, cy

    def child(self, x, y, h=160.0, facing=1, coat=('cream', 'raincoat', 'raincoat_shade', 'raincoat_deep'),
              hair=('hair_light', 'hair', 'umber'), boots=('pink', 'boot', 'brick'), legs=('cornflower', 'denim', 'indigo'),
              skin=('pink', 'skin', 'skin_shade'), look=(0.0, 0.0), light=(-0.62, -0.58, 0.53), arm='lantern',
              paint=True, seed=0):
        """a small storybook child in a raincoat with the hood down, standing with feet at (x, y), `h` px tall,
        facing +1 (right) or -1. Returns anchors: hand (lantern grip), head (cx, cy, r), eye, mask.
        paint=False only plans it (the mask, to colour a background round it); the same seed gives the same child."""
        r = np.random.default_rng(seed)
        sd = lambda: int(r.integers(1 << 30))
        f = float(facing)
        X = lambda dx: x + dx * h * f
        Y = lambda dy: y - dy * h
        legm = np.maximum(self.tube([(X(-0.06), Y(0.27)), (X(-0.065), Y(0.1))], h * 0.07, h * 0.065),
                          self.tube([(X(0.05), Y(0.27)), (X(0.06), Y(0.1))], h * 0.07, h * 0.065))
        bootm = np.maximum(self.poly([(X(-0.105), Y(0.15)), (X(-0.025), Y(0.15)), (X(-0.02), Y(0.02)), (X(0.0), Y(0.0)),
                                      (X(-0.13), Y(0.0)), (X(-0.12), Y(0.04))], smooth=True),
                           self.poly([(X(0.015), Y(0.15)), (X(0.095), Y(0.15)), (X(0.10), Y(0.04)), (X(0.15), Y(0.02)),
                                      (X(0.15), Y(-0.005)), (X(0.01), Y(0.0)), (X(0.012), Y(0.05))], smooth=True))
        back = self.tube([(X(-0.05), Y(0.66)), (X(-0.12), Y(0.52)), (X(-0.13), Y(0.42))], h * 0.085, h * 0.075)
        coatpts = [(X(-0.08), Y(0.72)), (X(0.03), Y(0.73)), (X(0.11), Y(0.68)), (X(0.17), Y(0.45)), (X(0.22), Y(0.27)),
                   (X(0.13), Y(0.24)), (X(0.0), Y(0.235)), (X(-0.14), Y(0.24)), (X(-0.22), Y(0.27)), (X(-0.15), Y(0.47))]
        coatm = self.poly(coatpts, smooth=True)
        hood = self.blob(X(-0.06), Y(0.73), h * 0.1, h * 0.06, 0.12, seed=sd(), rot=-15 * f)
        hr = h * 0.12
        hx, hy = X(0.035), Y(0.86)
        head = self.ellipse(hx, hy, hr * 0.98, hr)
        ear = self.ellipse(X(0.015), Y(0.85), hr * 0.17, hr * 0.22)
        nose = self.ellipse(hx + f * hr * 0.92, hy + hr * 0.18, hr * 0.16, hr * 0.15)
        cap = self.poly([(hx - f * hr * 1.08, hy + hr * 0.62), (hx - f * hr * 1.12, hy - hr * 0.2),
                         (hx - f * hr * 0.6, hy - hr * 1.02), (hx + f * hr * 0.25, hy - hr * 1.1),
                         (hx + f * hr * 0.85, hy - hr * 0.72), (hx + f * hr * 1.0, hy - hr * 0.32),
                         (hx + f * hr * 0.7, hy - hr * 0.38), (hx + f * hr * 0.3, hy - hr * 0.48),
                         (hx + f * hr * 0.05, hy - hr * 0.1), (hx - f * hr * 0.2, hy + hr * 0.3),
                         (hx - f * hr * 0.45, hy + hr * 0.66)], smooth=True)
        sh_ = (X(0.06), Y(0.66))
        hand = (X(0.2), Y(0.43)) if arm == 'lantern' else (X(0.14), Y(0.42))
        elbow = (X(0.15), Y(0.53))
        armm = self.tube([sh_, elbow, hand], h * 0.088, h * 0.074)
        hm = self.ellipse(hand[0] + f * h * 0.012, hand[1] + h * 0.018, h * 0.03, h * 0.032)
        eyex, eyey = hx + f * hr * 0.55 + look[0], hy - hr * 0.02 + look[1]
        out = dict(hand=(hand[0] + f * h * 0.014, hand[1] + h * 0.04), head=(hx, hy, hr), eye=(eyex, eyey),
                   mask=np.clip(legm + bootm + back + coatm + hood + head + cap + armm + hm + nose, 0, 1),
                   coat=coatm)
        if not paint: return out
        st = dict(length=(h * 0.05, h * 0.12), width=(1.2, 1.8), density=1.25)
        self.form(legm, legs, 90, light, length=st['length'], width=st['width'], density=st['density'], seed=sd())
        self.form(bootm, boots, 0, light, length=st['length'], width=st['width'], density=1.4, seed=sd())
        self.form(back, coat[1:], 80, light, length=st['length'], width=st['width'], density=1.2, seed=sd())
        cf = self.blend(np.full((self.H, self.W), np.deg2rad(95 - 12 * f), np.float32), self.contour(coatm, 6), 0.25)
        self.form(coatm, coat, cf, light, length=(h * 0.06, h * 0.15), width=(1.3, 1.9), density=1.3,
                  warm='lemon', cool='lavender', seed=sd())
        for k in range(4):                                   # soft folds down from the chest
            fx = -0.12 + 0.08 * k + r.normal(0, 0.01)
            self.line([(X(fx * 0.6), Y(0.55)), (X(fx * 0.85), Y(0.42)), (X(fx * 1.1), Y(0.27))], coat[2], 1.4, 0.55,
                      0.6, 0.3, seg=(h * 0.12, h * 0.3), seed=sd())
        self.line([(X(-0.215), Y(0.27)), (X(0.0), Y(0.245)), (X(0.215), Y(0.275))], coat[3], 1.5, 0.6, 0.7, 0.3,
                  seg=(h * 0.15, h * 0.3), seed=sd())
        for k in range(3):                                   # toggles
            bx, by = X(0.115 - 0.01 * k), Y(0.6 - 0.1 * k)
            self.hatch(self.ellipse(bx, by, h * 0.012, h * 0.014), 0, coat[3], (2, 4), (1.2, 1.5), 2.5, 0.9, 0.5,
                       clip=None, seed=sd())
        self.edge(coatm, coat[3], density=0.7, seed=sd())
        # the arm's soft shadow on the coat
        dx, dy = 3 * f, 5
        ash = np.roll(np.roll(blur(armm, 2.5), int(dy), 0), int(dx), 1) * coatm * (1 - armm)
        self.hatch(ash, 95 - 12 * f, (coat[2], coat[3]), (h * 0.03, h * 0.08), (1.2, 1.6), 1.6, 0.8, 0.35, seed=sd())
        self.form(hood, coat, self.contour(hood, 3), light, length=(h * 0.04, h * 0.09), width=(1.2, 1.7), density=1.3,
                  seed=sd())
        self.form(head, skin, self.contour(head, 4), light, length=(hr * 0.3, hr * 0.7), width=(1.2, 1.6), density=1.6,
                  pressure=0.74, seed=sd())
        self.edge(np.clip(head + nose, 0, 1), skin[2], (1.1, 1.5), 1.1, 0.7, 0.8, band=1.4, length=(4, 10), seed=sd())
        self.hatch(ear, 60, skin[2], (3, 6), (1.2, 1.5), 1.8, 0.72, 0.35, clip=ear, seed=sd())
        self.hatch(nose, 60, skin[1], (3, 6), (1.2, 1.5), 1.6, 0.7, 0.35, clip=nose, seed=sd())
        self.blush(hx + f * hr * 0.52, hy + hr * 0.36, hr * 0.2, amount=0.6, seed=sd())
        self.eye(eyex, eyey, max(1.6, hr * 0.1), seed=sd())
        hlit = self.shading(cap, light, hr * 0.5)
        # hair falls from the crown in smooth locks (a bob): strokes from a point above the forehead
        hf = self.radial(hx + f * hr * 0.15, hy - hr * 1.6, 0, 3, 40)
        self.hatch(cap, hf, hair[1], (hr * 0.5, hr * 1.0), (1.2, 1.6), 1.6, 0.76, 0.35, bend=0.01, clip=cap, seed=sd())
        kw = dict(spread=0.22, curl=0.03, converge=0.6, light=light[:2], clip=cap)
        self.fur(cap, hf, hair[1], (hr * 0.6, hr * 1.1), (1.1, 1.5), 1.3, (4, 7), pressure=0.78, seed=sd(), **kw)
        self.fur(cap * smoothstep(0.3, 0.8, 1 - hlit), hf, hair[2], (hr * 0.5, hr * 0.9), (1.1, 1.4), 1.0, (3, 6),
                 pressure=0.8, seed=sd(), **kw)
        self.fur(cap * smoothstep(0.45, 0.95, hlit), hf, hair[0], (hr * 0.5, hr * 0.9), (1.0, 1.4), 0.7, (3, 5),
                 pressure=0.7, opacity=0.5, seed=sd(), **kw)
        self.form(armm, coat, self.contour(armm, 3), light, length=(h * 0.04, h * 0.09), width=(1.2, 1.7),
                  density=1.3, warm='lemon', seed=sd())
        self.edge(armm, coat[3], density=0.9, seed=sd())
        self.form(hm, skin, 60, light, length=(3, 6), width=(1.2, 1.5), density=1.6, seed=sd())
        return out

    # ================================================================== finish and output
    def finish(self, soft=0.3, grain=1.0, vignette=0.6, warmth=0.5):
        """record the finishing (applied in render, so every stage snapshot matches the final look)"""
        self.fin = dict(soft=soft, grain=grain, vignette=vignette, warmth=warmth)
        return self

    def render(self):
        out = self.C
        f = self.fin
        if f:
            if f['soft']:
                b = np.stack([blur(out[..., c], 0.8) for c in range(3)], -1)
                out = out * (1 - f['soft']) + b * f['soft']
            if f['vignette']:
                if not hasattr(self, '_vig'):
                    dx = (self.XX / self.W - 0.5) * 2; dy = (self.YY / self.H - 0.5) * 2
                    self._vig = smoothstep(0.75, 1.55, np.sqrt(dx * dx * 0.8 + dy * dy)).astype(np.float32)
                v = self._vig[..., None] * f['vignette'] * 0.12
                out = out * (1 - v) + out * hexc('#d9b48a') * v
            if f['warmth']:
                out = out * (1 + f['warmth'] * np.array([0.012, 0.0, -0.02], np.float32))
            if f['grain']:
                if not hasattr(self, '_grain'):
                    r = np.random.default_rng(self.seed + 7)
                    g = r.normal(0, 1, (self.H, self.W)).astype(np.float32)
                    self._grain = (0.011 * (0.7 * g + 0.3 * blur(g, 0.8) * 2.0)).astype(np.float32)
                out = out * (1 + f['grain'] * self._grain[..., None])
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


def _resample_k(P, k):
    """resample a polyline to exactly k points by arc length"""
    if len(P) == 1: return np.repeat(P, k, 0)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-4: return np.repeat(P[:1], k, 0)
    s = np.linspace(0, d[-1], k)
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)
