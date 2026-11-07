"""oilpastel — 油画棒肖像 / Oil-Pastel Portrait: bold dry waxy strokes, textured colour, beautifully imperfect
portraits on white paper (numpy + Pillow only).

The look: a figure drawn with oil pastels (wax crayons) on white, toothy cold-press paper and left floating as a
vignette -- no background, at most a smear of sky or a dry-brushed black cast shadow. A tight, high-chroma palette:
saffron / marigold, navy (a teal navy) and black, one cool blue, orange blush and red-orange lips. Big flat masses
(a sweater, a hat, a coat, a scarf) are laid in with parallel dry strokes: the wax rides on the peaks of the paper
tooth and skips the pits, so every mass is peppered with white specks pulled into short streaks along the stroke,
and the strokes end hard and streaky -- each run of the stick's worn face gives out at its own place, a comb of
uneven teeth. Black crayon accents only where they matter (eyes, brows, a nostril, a few contour and fold marks),
never a full outline. Faces are the paper itself with a few peach strokes on the shadow side, two hatched orange
blush patches and flat red-orange lips -- simplified, a little lopsided, expressive. Hair is a few loose energetic
strokes; stripes on knitwear are short bold dashes.

Physical model
  paper       White cold-press paper with a visible tooth `T` (rank-equalised to a uniform 0..1, so that "the wax
              catches where tooth > 1 - pressure" turns pressure straight into coverage), a faint mottle, and the
              tooth pre-averaged along 8 directions (`TD`, uint8, dragged further than for soft pastel) so the pits a
              stroke skips become short white streaks along it. The blank paper keeps about 3-4 levels of tooth
              shading (it is not a flat digital white).
  strokes     A stroke is a short centreline integrated through an orientation field (angles mod pi), drawn with a
              stick of constant width. Thousands go at once: Pillow draws every *segment* of every stroke with its
              own id into a 2x supersampled integer map; numpy looks each covered sub-pixel up to its segment and
              recovers its position along the stroke (u) and across it (v). The stick's worn face is split into
              lanes across the stroke; each lane has its own pressure (lengthwise streaks), its own small value shift
              (some lanes lighter or a second colour mixed in: `mix`) and its own end -- the lanes give out one by one
              over the last `dry` part of the stroke, so the stroke ends in a hard, uneven comb, not a soft fade. The
              start is blunt and full. Wax only lands where the pressure reaches the direction-matched tooth, with a
              steep threshold (crisp white specks, not a soft grain), and sums back with bincount; big batches are
              split into bands of rows to keep memory down.
  wax         Opaque: new = old + A x (target - old), target = (1 - opacity) x old x colour + opacity x colour; a
              stroke also drags a little of the wax already there into its own colour (`smear`, scaled by the wax
              buffer `F`). `F` records how much wax sits on the paper, so later layers fill more of the tooth.
  edges       A mass is clipped to its mask with a broken edge: the mask's rim is thresholded against a mid-scale
              noise plus the tooth (`edge`), so the outline breaks into the paper like a dragged stick, and strokes
              left unclipped at one end (`spill`) run out past the shape in streaky teeth.
  accents     `crayon()` a scratchy black line: the path wobbles and is split into overlapping pieces of different
              widths (the hand lifts and presses), each a narrow dry stroke with its own tooth skipping, sometimes
              doubled by a thinner offset stroke. `blush()` a patch of parallel hatched strokes in a ragged ellipse.
              `dashes()` short bold dashes along a path (stripes on knitwear, a fringe). `smear()` a dry-brushed
              cast shadow or a smear of sky: long dry strokes with big skips. `wisp()` a rising curl (steam, breath).
  faces       `eye()` a black crayon eye: the opening between a lowered upper lid (a downward gaze) and the lower
              lid, a big dark iris seen only inside it with a paper gap left as the catchlight, a heavy upper-lid
              stroke that thickens and flicks out at the outer corner, a faint peach crease and a light lower mark;
              `brow()` one chunky stroke and a few short hairs; `lips()` a flat red-orange mouth laid in short dense
              strokes with a darker parting; `hair()` long energetic strokes that start on a root line (or land in
              a region), follow a field with a strong bend and thin to a point.
  finish      `finish()` records the finishing, applied in render so every stage snapshot matches: the tooth showing
              through the wax, a little waxy relief at the edges of the deposit (lit from the upper left), a faint
              grain and a very slight softening.

API (canvas pixel coordinates; a number given as a field is a direction in degrees, 0 = to the right, 90 = down;
     field arrays are radians; colours are PAINTS names, '#rrggbb' or RGB triples)
  surface    OilPastel(W, H, seed, keep_stages, stages_dir); paper(tone, tooth, drag); finish(tooth, relief, grain,
             soft) -- call finish() before the first mark
  masks      poly(pts, smooth) / ellipse(cx, cy, rx, ry, rot) / blob(cx, cy, rx, ry, rough) / tube(path, w0, w1) /
             rect(x0, y0, x1, y1) / below(xs, ys) -> canvas-sized float masks; spot(cx, cy, rx, ry, rot, solid) a
             soft field; soften(mask, sigma)
  fields     flow(angle, turb, scale); field(f(x, y) -> degrees) -- or pass f itself; radial(cx, cy, offset);
             contour(mask, sigma, offset, fallback); blend(f1, f2, w); rotate(field, deg)
  strokes    fill(region, field, colour, length, width, density, pressure, alpha, dry, streak, smear, opacity,
             mix, spill, edge, passes, clip, avoid, fade); lines(paths, colour, width, pressure, ...); stroke(path,
             width, colour, ...)
  accents    crayon(path, width, colour, pressure, wobble, seg, gap, double); blush(cx, cy, rx, ry, colour,
             angle, strength); dashes(path, colour, spacing, length, width, angle); smear(region, colour, angle,
             length, width); wisp(x, y, height, sway, colour, width)
  faces      eye(cx, cy, w, h, look, lid, side, rot, lower, lash, iris, crease); brow(path, width); lips(cx, cy, w,
             h, smile, rot, side, parting); hair(region, flow, colours, n, length, width, bend, pressure, dry, taper,
             roots, clip)
  output     render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 88, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from oilpastel import OilPastel
    p = OilPastel(1200, 1200, seed=3); p.finish(); p.paper()
    body = p.poly([(300, 1100), (330, 760), (600, 700), (870, 760), (900, 1100)], smooth=True)
    p.fill(body, -95, {'navy': 3, 'black': 1}, length=(120, 260), width=(30, 48), spill=(0, 60))
    p.eye(560, 470, 46, 20, look=(0, 0.4)); p.eye(680, 470, 46, 20, look=(0, 0.4))
    p.blush(540, 540, 46, 34); p.blush(700, 540, 46, 34)
    p.lips(615, 600, 64, 26)
    p.save('pastel.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, spline, noise2d, smoothstep, blob_pts

PAINTS = {
    # paper and crayon black
    'paper': '#f6f5f1', 'white': '#fbfaf6', 'black': '#131716', 'charcoal': '#2b2f30',
    'warmgrey': '#9a928a', 'grey': '#c2bdb6',
    # the navy family (a teal navy) and the blues
    'navy_deep': '#0d2631', 'navy': '#15404f', 'navy_light': '#245a6d', 'indigo': '#1c3866', 'cobalt': '#1f5f8c',
    'cool_deep': '#3b6a94', 'cool': '#5a8cb6', 'cool_light': '#8db2cf', 'mist': '#bccbd6',
    # the saffron family
    'saffron_deep': '#e27c15', 'saffron': '#f39a20', 'marigold': '#f6b23a', 'yellow': '#f8c94c', 'butter': '#fadf8c',
    'orange': '#ee772a', 'ochre': '#c98d36',
    # skin, blush and lips
    'skin_pale': '#f5e5d7', 'peach_light': '#f6bc98', 'peach': '#f09768', 'peach_deep': '#e27c4c',
    'skin_tan': '#d4956a', 'skin_brown': '#7c4f3b', 'skin_deep': '#3e302c',
    'blush': '#ee7a34', 'blush_light': '#f3a065', 'vermilion': '#f2461a', 'lip': '#f24a1c', 'lip_dark': '#bd2f17',
    # extras
    'olive': '#3b5a2c', 'moss': '#64803a', 'kraft': '#c79b5f', 'kraft_dark': '#a2763f', 'rust': '#b9532a',
}
LIGHT = (-0.62, -0.62)                     # the relief light: from the upper left


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    return hexc(a) * (1 - t) + hexc(b) * t


def _equalise(a):
    """rank-equalise to a uniform 0..1 distribution"""
    flat = a.ravel()
    o = np.argsort(flat, kind='stable')
    out = np.empty(flat.size, np.float32)
    out[o] = np.linspace(0, 1, flat.size, dtype=np.float32)
    return out.reshape(a.shape)


def _lookup(field, x, y):
    if callable(field): return np.deg2rad(np.asarray(field(x, y), np.float32)).astype(np.float32)
    if np.ndim(field) == 0: return np.full(len(x), float(field), np.float32)
    H, W = field.shape[:2]
    return field[np.clip(y.astype(np.int32), 0, H - 1), np.clip(x.astype(np.int32), 0, W - 1)]


def _resample(P, step):
    P = np.asarray(P, np.float32)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-3: return P[:1]
    s = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)


def _resample_k(P, k):
    """resample a polyline to exactly k points by arc length"""
    P = np.asarray(P, np.float32)
    if len(P) == 1: return np.repeat(P, k, 0)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-4: return np.repeat(P[:1], k, 0)
    s = np.linspace(0, d[-1], k)
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)


def _hash(a, b):
    h = np.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return (h - np.floor(h)).astype(np.float32)


def _smooth_path(path, per=8):
    P = np.asarray(path, np.float32)
    return spline(P, per) if len(P) > 2 else _resample(P, 4)


class OilPastel:
    PAINTS = PAINTS

    def __init__(self, W=1600, H=1600, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = hexc('paper')
        self.F = np.zeros((H, W), np.float32)              # wax already on the paper
        self.T = None; self.TD = None; self.EN = None
        self.fin = None
        self.floor = 0.03                                   # wax a stick still pushes into the pits
        self.band_px = 0.6e6                                # sub-pixels per raster band (memory vs. speed)
        self.n_strokes = 0
        self._sid = 0                                       # running stroke id (per-lane randomness)

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== paper
    def paper(self, tone='paper', tooth=1.0, drag=5, seed=None):
        """white cold-press paper: an equalised tooth that shows as a faint grain on the blank paper, and the tooth
        dragged along 8 stroke directions (the pits a stick skips become streaks along it)"""
        H, W = self.H, self.W
        r = self._r(seed)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.7)
        g2 = noise2d(H, W, 3.2, 2, int(r.integers(1 << 30)))
        g3 = noise2d(H, W, 9.0, 2, int(r.integers(1 << 30)))
        self.T = _equalise(0.75 * z(g1) + 0.55 * z(g2) + 0.18 * z(g3))
        del g1, g2, g3
        mot = noise2d(H, W, 260, 3, int(r.integers(1 << 30))) - 0.5
        self.C = (hexc(tone)[None, None] * (1 + 0.012 * mot[..., None] + 0.05 * tooth * (self.T[..., None] - 0.5))
                  ).astype(np.float32)
        del mot
        self.F[:] = 0
        TD = np.empty((8, H, W), np.uint8)
        ks = np.arange(-drag, drag + 1); wk = 1.0 - np.abs(ks) / (drag + 1.0)
        for b in range(8):
            a = np.pi * b / 8
            acc = np.zeros_like(self.T)
            for k, w in zip(ks, wk):
                acc += w * np.roll(self.T, (int(round(k * np.sin(a))), int(round(k * np.cos(a)))), axis=(0, 1))
            TD[b] = np.round(_equalise(0.3 * self.T + 0.7 * acc / wk.sum()) * 255).astype(np.uint8)
            del acc
        self.TD = TD
        self.EN = (noise2d(H, W, 7.0, 3, int(r.integers(1 << 30))) - 0.5).astype(np.float32)
        self.EN2 = noise2d(H, W, 26.0, 2, int(r.integers(1 << 30))).astype(np.float32)   # ragged run-out lengths
        rg = np.random.default_rng(self.seed + 7)
        self._grain = rg.standard_normal((H, W), dtype=np.float32)
        return self

    def _need(self):
        if self.T is None: self.paper()

    # ================================================================== masks
    def poly(self, pts, smooth=False, ss=2):
        """filled polygon -> canvas-sized float mask (smooth=True: a closed Catmull-Rom spline through the points)"""
        P = np.asarray(pts, np.float32)
        if smooth:
            Q = np.vstack([P[-1:], P, P[:2]])
            P = spline(Q, 10)[10:-10]
        out = np.zeros((self.H, self.W), np.float32)
        x0, y0 = max(0, int(np.floor(P[:, 0].min())) - 1), max(0, int(np.floor(P[:, 1].min())) - 1)
        x1, y1 = min(self.W, int(np.ceil(P[:, 0].max())) + 2), min(self.H, int(np.ceil(P[:, 1].max())) + 2)
        if x1 <= x0 or y1 <= y0: return out
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((float(x) - x0) * ss, (float(y) - y0) * ss) for x, y in P], fill=255)
        out[y0:y1, x0:x1] = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return out

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        """anti-aliased ellipse mask (rot in degrees)"""
        ry = rx if ry is None else ry
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        R = max(rx, ry)
        x0, x1 = max(0, int(cx - R - 3)), min(self.W, int(cx + R + 4))
        y0, y1 = max(0, int(cy - R - 3)), min(self.H, int(cy + R + 4))
        out = np.zeros((self.H, self.W), np.float32)
        if x1 <= x0 or y1 <= y0: return out
        dx, dy = self.XX[y0:y1, x0:x1] - cx, self.YY[y0:y1, x0:x1] - cy
        u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
        out[y0:y1, x0:x1] = np.clip((1 - np.sqrt(u * u + v * v)) * min(rx, ry) + 0.5, 0, 1)
        return out

    def blob(self, cx, cy, rx, ry=None, rough=0.1, seed=None, rot=0.0):
        ry = rx if ry is None else ry
        return self.poly(blob_pts(cx, cy, rx, ry, rough, 120, int(self._r(seed).integers(1 << 30)), np.deg2rad(rot)))

    @staticmethod
    def tube_pts(path, w0, w1=None, per=8):
        """outline points of a tube of width w0 -> w1 along a path (an arm, a scarf end); w0 may be a list"""
        w1 = w0 if w1 is None else w1
        P = spline(path, per) if len(path) > 2 else _resample(path, 4)
        n = len(P)
        Tg = np.gradient(P, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-6
        Nn = np.stack([-Tg[:, 1], Tg[:, 0]], 1)
        w = (np.linspace(w0, w1, n) if np.ndim(w0) == 0
             else np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(w0)), w0))
        w = np.asarray(w, np.float32)[:, None] * 0.5
        return np.vstack([P + Nn * w, (P - Nn * w)[::-1]])

    def tube(self, path, w0, w1=None):
        return self.poly(self.tube_pts(path, w0, w1))

    def rect(self, x0, y0, x1, y1):
        X, Y = self.XX, self.YY
        return (np.clip(X - x0 + 0.5, 0, 1) * np.clip(x1 - X + 0.5, 0, 1) *
                np.clip(Y - y0 + 0.5, 0, 1) * np.clip(y1 - Y + 0.5, 0, 1)).astype(np.float32)

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

    def spot(self, cx, cy, rx, ry=None, rot=0.0, solid=0.3, power=1.2):
        """a soft 0..1 field: 1 inside `solid` of the ellipse, easing to 0 at its rim"""
        ry = rx if ry is None else ry
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        R = max(rx, ry)
        x0, x1 = max(0, int(cx - R - 2)), min(self.W, int(cx + R + 3))
        y0, y1 = max(0, int(cy - R - 2)), min(self.H, int(cy + R + 3))
        out = np.zeros((self.H, self.W), np.float32)
        if x1 <= x0 or y1 <= y0: return out
        dx, dy = self.XX[y0:y1, x0:x1] - cx, self.YY[y0:y1, x0:x1] - cy
        d = np.sqrt(((dx * c + dy * s) / rx) ** 2 + ((-dx * s + dy * c) / ry) ** 2)
        out[y0:y1, x0:x1] = smoothstep(1.0, solid, d) ** power
        return out

    def soften(self, mask, sigma):
        """a blurred copy of a mask, blurred only round the shape"""
        out = np.zeros((self.H, self.W), np.float32)
        bb = self._bbox(mask, pad=int(3 * sigma) + 4)
        if bb is None: return out
        x0, y0, x1, y1 = bb
        out[y0:y1, x0:x1] = blur(mask[y0:y1, x0:x1].astype(np.float32), sigma)
        return out

    def _mask(self, region):
        if isinstance(region, np.ndarray): return region.astype(np.float32, copy=False)
        x0, y0, x1, y1 = (int(round(v)) for v in region)
        M = np.zeros((self.H, self.W), np.float32)
        M[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = 1
        return M

    @staticmethod
    def _bbox(M, thr=0.004, pad=0):
        rows = np.flatnonzero(M.max(1) > thr); cols = np.flatnonzero(M.max(0) > thr)
        if not len(rows) or not len(cols): return None
        H, W = M.shape
        return (max(0, cols[0] - pad), max(0, rows[0] - pad), min(W, cols[-1] + 1 + pad), min(H, rows[-1] + 1 + pad))

    # ================================================================== fields
    def flow(self, angle=0.0, turb=8.0, scale=240.0, seed=None):
        """orientation field: `angle` degrees with +-turb degrees of low-frequency wander at `scale` px"""
        n = noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5
        return np.deg2rad(angle + 2 * turb * n).astype(np.float32)

    def field(self, f):
        """an orientation field from f(x, y) -> degrees, evaluated on the whole canvas"""
        return np.deg2rad(np.asarray(f(self.XX, self.YY), np.float32)).astype(np.float32)

    def radial(self, cx, cy, offset=0.0):
        """directions pointing away from (cx, cy), offset in degrees"""
        return (np.arctan2(self.YY - cy, self.XX - cx) + np.deg2rad(offset)).astype(np.float32)

    def contour(self, mask, sigma=8.0, offset=0.0, fallback=None):
        """directions along the iso-lines of a (blurred) shape: strokes that wrap round a roll of scarf, a sleeve.
        Only computed round the shape (outside it: `fallback` degrees or 0)."""
        if isinstance(fallback, np.ndarray): out = fallback.astype(np.float32).copy()
        else: out = np.full((self.H, self.W), 0 if fallback is None else np.deg2rad(fallback), np.float32)
        bb = self._bbox(mask, pad=int(3 * sigma) + 4)
        if bb is None: return out
        x0, y0, x1, y1 = bb
        d = blur(mask[y0:y1, x0:x1].astype(np.float32), sigma)
        gy, gx = np.gradient(d)
        a = np.arctan2(gy, gx) + np.pi / 2 + np.deg2rad(offset)
        if fallback is not None:
            g = np.hypot(gx, gy)
            w = smoothstep(0.0, 0.25 / max(sigma, 1.0), g)
            fb = np.deg2rad(fallback) if np.ndim(fallback) == 0 else fallback[y0:y1, x0:x1]
            a = self.blend(np.broadcast_to(np.float32(fb), a.shape) if np.ndim(fb) == 0 else fb, a, w)
        out[y0:y1, x0:x1] = a
        return out

    @staticmethod
    def blend(f1, f2, w):
        """blend two orientation fields (doubled-angle average, so 0 and pi are the same orientation)"""
        w = np.asarray(w, np.float32)
        c = (1 - w) * np.cos(2 * f1) + w * np.cos(2 * f2)
        s = (1 - w) * np.sin(2 * f1) + w * np.sin(2 * f2)
        return (0.5 * np.arctan2(s, c)).astype(np.float32)

    @staticmethod
    def rotate(field, deg):
        if np.ndim(field) == 0: return float(field) + deg
        return (field + np.deg2rad(deg)).astype(np.float32)

    # ================================================================== stroke machinery
    def _sizes(self, spec, x, y, r):
        n = len(x)
        if callable(spec):
            return (np.asarray(spec(x, y), np.float32) * r.uniform(0.85, 1.15, n)).astype(np.float32)
        if np.ndim(spec) == 0: return np.full(n, float(spec), np.float32) * r.uniform(0.88, 1.12, n).astype(np.float32)
        return r.uniform(spec[0], spec[1], n).astype(np.float32)

    def _colours(self, spec, x, y, r):
        """'canvas' (the colour under the point) | paint | list of paints (picked at random) | {paint: weight} |
        f(x, y) -> (N, 3) | RGB"""
        n = len(x)
        if isinstance(spec, str) and spec == 'canvas': return _lookup(self.C, x, y).astype(np.float32).copy()
        if callable(spec): return np.asarray(spec(x, y), np.float32).reshape(n, 3).copy()
        if isinstance(spec, dict):
            names = list(spec); w = np.array([spec[k] for k in names], np.float64); w /= w.sum()
            R = np.stack([hexc(c) for c in names])
            return R[r.choice(len(names), n, p=w)].astype(np.float32)
        if isinstance(spec, str): return np.broadcast_to(hexc(spec), (n, 3)).astype(np.float32).copy()
        if isinstance(spec, (tuple, list)) and all(isinstance(c, str) for c in spec):
            R = np.stack([hexc(c) for c in spec])
            return R[r.integers(0, len(R), n)].astype(np.float32)
        return np.broadcast_to(hexc(spec), (n, 3)).astype(np.float32).copy()

    @staticmethod
    def _field_rad(field):
        if callable(field): return field
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

    def _edge_clip(self, M, edge, spill=None):
        """the clip of a mass: its rim thresholded against noise + tooth, so the edge breaks like a dragged stick.
        spill = (dx, dy): the mask is smeared up to that far that way, each stretch of the edge its own distance
        (the strokes run out past the shape in a ragged comb, not to a ruled line)"""
        S = M
        if spill is not None:
            dx, dy = spill
            S = M.copy()
            n = 24
            reach = np.clip(0.15 + 1.1 * self.EN2, 0, 1)
            for i in range(1, n + 1):
                sx, sy = int(round(dx * i / n)), int(round(dy * i / n))
                sh = np.zeros_like(M)
                ys0, ys1 = max(0, sy), min(self.H, self.H + sy)
                xs0, xs1 = max(0, sx), min(self.W, self.W + sx)
                sh[ys0:ys1, xs0:xs1] = M[ys0 - sy:ys1 - sy, xs0 - sx:xs1 - sx]
                sh *= smoothstep(i / n - 0.08, i / n, reach)
                np.maximum(S, sh, out=S)
                del sh
        g = smoothstep(0.0, 1.0, S)
        rim = (g > 0.01) & (g < 0.99)
        out = g.copy()
        out[rim] = np.clip((g[rim] - 0.5) * 2.2 + 0.5 + edge * (0.9 * self.EN[rim] + 0.35 * (self.T[rim] - 0.5)), 0, 1)
        return out

    def fill(self, region, field=-90.0, colour='navy', length=(70, 160), width=(26, 44), density=2.6, pressure=0.92,
             alpha=1.0, dry=0.3, streak=0.4, smear=0.12, opacity=0.94, mix=None, spill=None, edge=0.5, soft=0.16,
             taper=0.08, jitter=0.08, bend=0.02, value=0.05, lane_value=0.05, hue=0.0, passes=3, clip='auto',
             avoid=None, fade=None, k=5, sidep=0.12, seed=None):
        """scumble-fill `region` (a 0..1 landing-probability mask or a box) with parallel dry waxy strokes along
        `field` (degrees or a radians field, or f(x, y) -> degrees). density ~ how many times the strokes tile the
        region; length / width: (lo, hi), a number or f(x, y); colour: a paint, a list (picked at random), a dict
        {paint: weight}, 'canvas' or f(x, y) -> (N, 3); pressure: how deep the wax reaches into the tooth (lower =
        more white specks); dry: the last part of each stroke over which its lanes give out (streaky ends);
        streak: how much weaker some lanes are (lengthwise streaks); smear: how much of the wax already there the
        stick drags along; opacity: how fully a stroke covers what is under it; mix = (paint, fraction) mixes a
        second colour into some lanes; spill = (dx, dy) lets the strokes run out past the shape that way; edge: how
        broken the clipped rim is; clip: a mask the strokes are cut to ('auto' = the region with a broken rim);
        fade: a 0..1 field easing the pressure off; avoid: a mask to leave alone. Returns the number of strokes."""
        self._need()
        r = self._r(seed)
        M = self._mask(region)
        if avoid is not None:
            keep = 1 - np.clip(avoid, 0, 1)
            M = M * keep
        bb = self._bbox(M)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        if float(M[y0:y1, x0:x1].sum()) < 1: return 0
        sx = r.uniform(x0, x1, 600).astype(np.float32); sy = r.uniform(y0, y1, 600).astype(np.float32)
        Lm = float(self._sizes(length, sx, sy, r).mean()); Wm = float(self._sizes(width, sx, sy, r).mean())
        n_cells = int(density * (x1 - x0) * (y1 - y0) / (0.8 * Lm * Wm)) + 1
        arr = isinstance(region, np.ndarray)
        x, y = self._seed_points(np.sqrt(M) if arr else M, bb, n_cells, r)
        n = len(x)
        if not n: return 0
        o = r.permutation(n); x, y = x[o], y[o]
        L = self._sizes(length, x, y, r); Wd = self._sizes(width, x, y, r)
        cols = self._colours(colour, x, y, r)
        if value: cols *= (1 + value * r.normal(0, 1, n).astype(np.float32))[:, None]
        if hue:
            g = cols.mean(1, keepdims=True)
            cols = g + (cols - g) * (1 + hue * r.normal(0, 1, (n, 1)).astype(np.float32))
        cols = np.clip(cols, 0, 1)
        P = self._centrelines(x, y, L, self._field_rad(field), (jitter * r.normal(0, 1, n)).astype(np.float32),
                              (bend * r.normal(0.5, 0.7, n)).astype(np.float32), k)
        if isinstance(clip, str) and clip == 'auto':
            clip = self._edge_clip(M, edge, spill) if arr else None
        if avoid is not None:
            clip = keep if clip is None else clip * keep
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (n,)) * r.uniform(0.9, 1.06, n).astype(np.float32)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,)) * r.uniform(0.9, 1.0, n).astype(np.float32)
        dr = np.broadcast_to(np.asarray(dry, np.float32), (n,)) * r.uniform(0.6, 1.3, n).astype(np.float32)
        st = np.broadcast_to(np.asarray(streak, np.float32), (n,)) * r.uniform(0.6, 1.3, n).astype(np.float32)
        self._draw(P, Wd, cols, al, pr, dr, st, taper, opacity, smear, mix, lane_value, clip, fade, passes, soft, r,
                   sidep=sidep)
        self.n_strokes += n
        return n

    def lines(self, paths, colour='black', width=8.0, pressure=0.9, alpha=1.0, dry=0.2, streak=0.3, smear=0.08,
              opacity=0.95, mix=None, soft=0.22, taper=0.1, value=0.03, lane_value=0.04, clip=None, fade=None,
              passes=1, k=None, seed=None, sidep=0.2):
        """draw explicit strokes: a list of polylines (each (m, 2)), resampled to k points each; painted in order
        (later on top) within each pass. width / pressure / dry may be numbers, (lo, hi) or per-path lists."""
        self._need()
        r = self._r(seed)
        if not len(paths): return 0
        if k is None: k = max(3, min(13, int(np.median([len(p) for p in paths]))))
        P = np.stack([_resample_k(np.asarray(p, np.float32), k) for p in paths]).astype(np.float32)
        n = len(P)
        mid = P[:, k // 2]

        def per(spec, lo=0.92, hi=1.06):
            if isinstance(spec, (list, np.ndarray)) and len(spec) == n:
                return np.asarray(spec, np.float32)
            if isinstance(spec, tuple): return r.uniform(spec[0], spec[1], n).astype(np.float32)
            return np.full(n, float(spec), np.float32) * r.uniform(lo, hi, n).astype(np.float32)
        Wd = per(width, 0.94, 1.06)
        cols = self._colours(colour, mid[:, 0], mid[:, 1], r)
        if value: cols = np.clip(cols * (1 + value * r.normal(0, 1, n).astype(np.float32))[:, None], 0, 1)
        pr = per(pressure, 0.95, 1.04); al = per(alpha, 1.0, 1.0); dr = per(dry, 0.7, 1.3); st = per(streak, 0.8, 1.2)
        self._draw(P, Wd, cols, al, pr, dr, st, taper, opacity, smear, mix, lane_value, clip, fade, passes, soft, r,
                   sidep=sidep)
        self.n_strokes += n
        return n

    def stroke(self, path, width=24.0, colour='navy', **kw):
        """one explicit dry stroke along `path` (smoothed if it has more than two points)"""
        P = _smooth_path(path, 6)
        return self.lines([P], colour, width, k=int(np.clip(len(P), 3, 13)), **kw)

    def _draw(self, P, Wd, cols, al, pr, dr, st, taper, opacity, smear, mix, lane_value, clip, fade, passes, soft, r,
              ss=2, sidep=0.2):
        n = len(P)
        sp = np.broadcast_to(np.asarray(sidep, np.float32), (n,)).astype(np.float32)
        tw = np.broadcast_to(np.asarray(taper, np.float32), (n,)).astype(np.float32)
        so = np.broadcast_to(np.asarray(soft, np.float32), (n,)) * r.uniform(0.8, 1.2, n).astype(np.float32)
        nb = np.clip(Wd / r.uniform(3.0, 4.6, n), 1.6, 16).astype(np.float32)          # lanes of the worn face
        sid = (self._sid + np.arange(n)).astype(np.float32) * 0.6180339 + float(self.seed % 997)
        self._sid += n
        if mix is not None:
            mc = hexc(mix[0]); mf = float(mix[1])
        else:
            mc = None; mf = 0.0
        passes = max(1, int(passes))
        my = P[:, P.shape[1] // 2, 1]
        for g in range(passes):
            sel = np.arange(g, n, passes)
            if not len(sel): continue
            lo = P[sel].reshape(-1, 2).min(0); hi = P[sel].reshape(-1, 2).max(0)
            area = (hi[0] - lo[0] + 2 * Wd.max()) * (hi[1] - lo[1] + 2 * Wd.max()) * ss * ss
            nband = int(np.clip(np.ceil(area / self.band_px), 1, 200))
            if nband > 1:
                edges = np.quantile(my[sel], np.linspace(0, 1, nband + 1))
                groups = [sel[(my[sel] >= edges[b]) & ((my[sel] < edges[b + 1]) | (b == nband - 1))]
                          for b in range(nband)]
            else:
                groups = [sel]
            for gs in groups:
                if len(gs):
                    self._raster(P[gs], Wd[gs], cols[gs], al[gs], pr[gs], dr[gs], st[gs], tw[gs], so[gs], nb[gs],
                                 sid[gs], sp[gs], opacity, smear, mc, mf, lane_value, clip, fade, ss)

    def _raster(self, P, Wd, cols, al, pr, dr, st, tw, so, nb, sid, sp, opacity, smear, mc, mf, lane_value, clip,
                fade, ss):
        n, k = P.shape[:2]
        ns = k - 1
        pad = float(Wd.max()) + 3
        lo = P.reshape(-1, 2).min(0) - pad; hi = P.reshape(-1, 2).max(0) + pad
        x0, y0 = max(0, int(np.floor(lo[0]))), max(0, int(np.floor(lo[1])))
        x1, y1 = min(self.W, int(np.ceil(hi[0]))), min(self.H, int(np.ceil(hi[1])))
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        A = P[:, :-1]; B = P[:, 1:]
        seg = B - A
        sl = np.linalg.norm(seg, axis=2) + 1e-4
        D = seg / sl[..., None]
        cum = np.cumsum(sl, axis=1) - sl
        LT = sl.sum(1)
        # every segment drawn with its own id; segments lengthened so a bend leaves no notch
        ext = np.minimum(Wd[:, None] * 0.35, sl * 0.5)[..., None] * D
        ext[:, -1] = 0
        A2 = (A - np.array([x0, y0], np.float32)) * ss
        B2 = (B + ext - np.array([x0, y0], np.float32)) * ss
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        a2 = A2.tolist(); b2 = B2.tolist()
        wi = np.maximum(1, np.round(Wd * ss)).astype(np.int32).tolist()
        for i in range(n):
            ai, bi, wv = a2[i], b2[i], wi[i]
            base = i * ns + 1
            for j in range(ns):
                d.line((ai[j][0], ai[j][1], bi[j][0], bi[j][1]), fill=base + j, width=wv)
        flat = np.asarray(im, dtype=np.int32).ravel()
        nz = np.flatnonzero(flat).astype(np.int32)
        del im
        if not len(nz): return
        sg = flat[nz]
        del flat
        W2 = w * ss
        sy = nz // W2; sx = nz - sy * W2
        del nz
        si = np.r_[0, np.repeat(np.arange(n), ns)]
        z1 = lambda a: np.r_[0, np.asarray(a, np.float32).ravel()].astype(np.float32)
        AX, AY = z1(A[..., 0]), z1(A[..., 1])
        DX, DY = z1(D[..., 0]), z1(D[..., 1])
        SL, CU = z1(sl), z1(cum)
        ang = np.mod(np.arctan2(D[..., 1], D[..., 0]), np.pi).ravel()
        BIN = np.r_[0, (np.round(ang / np.pi * 8).astype(np.int32) % 8)]
        stk = si[sg].astype(np.int32)
        X = (sx.astype(np.float32) + 0.5) * (1.0 / ss) + x0; Y = (sy.astype(np.float32) + 0.5) * (1.0 / ss) + y0
        rx = X - AX[sg]; ry = Y - AY[sg]
        t = np.clip(rx * DX[sg] + ry * DY[sg], 0, SL[sg])
        u = np.clip((CU[sg] + t) / LT[stk], 0, 1)
        del t
        sv = (rx * (-DY[sg]) + ry * DX[sg]) / (0.5 * Wd[stk] + 0.25)
        del rx, ry
        s0 = sid[stk]
        # the stick's sides are not ruled: a slow sideways waver along the stroke
        sv = sv + 0.1 * np.sin(u * LT[stk] / 37.0 + s0 * 5.3) + 0.05 * np.sin(u * LT[stk] / 11.0 + s0 * 2.1)
        # the stick: a blunt full start with rounded corners, a constant width (or tapering toward the end)
        wf = (1 - tw[stk] * u) * (0.55 + 0.45 * np.sqrt(np.clip(u / 0.05, 0, 1)))
        av = np.abs(sv) / np.maximum(wf, 0.05)
        lat = smoothstep(1.0, 1.0 - so[stk], av)
        # lanes across the worn face: each its own pressure, value and end (the comb of the streaky end)
        li = np.floor(np.clip(sv / np.maximum(wf, 0.05) * 0.5 + 0.5, 0, 0.999) * nb[stk]).astype(np.float32)
        h1 = _hash(s0, li); h2 = _hash(s0 + 3.17, li * 1.3 + 0.5); h3 = _hash(s0 + 7.31, li * 0.7 + 2.0)
        lp = 1 - st[stk] * 0.4 * h1 ** 1.6
        ue = 1 + 0.03 - (dr[stk] + 0.03) * (0.08 + 0.92 * h2 ** 0.8)
        ef = smoothstep(ue + 0.02, ue - 0.05, u) * (1 - np.minimum(1.6 * dr[stk], 0.5) * smoothstep(ue - 0.22, ue, u))
        sf = smoothstep(0.0, 0.025 + 0.03 * h3, u)
        p = pr[stk] * lp * ef * (0.7 + 0.3 * sf) * (1 - sp[stk] * np.clip(av, 0, 1) ** 2)
        del ef
        iy = y0 + sy // ss; ix = x0 + sx // ss
        if fade is not None:
            p = p * (0.35 + 0.65 * fade[iy, ix])
        Tt = self.TD[BIN[sg], iy, ix].astype(np.float32) * (1.0 / 255)
        # wax already on the paper takes more wax (a second layer covers the first), but the bare pits stay bare
        catch = np.clip((Tt + 0.55 * np.minimum(self.F[iy, ix], 1) - (1 - p)) * 7.0 + 0.5, 0, 1)
        catch = self.floor * np.clip(p, 0, 1) + (1 - self.floor) * catch
        del Tt
        Aa = al[stk] * catch * lat * sf
        lv = 1 + lane_value * (h3 - 0.5) * 2
        pix = (sy // ss) * w + (sx // ss)
        npx = w * h
        k2 = 1.0 / (ss * ss)
        a1 = np.bincount(pix, Aa, npx).astype(np.float32) * k2
        c3 = np.empty((npx, 3), np.float32)
        if mc is not None:
            mw = (h2 < mf).astype(np.float32)
            for ch in range(3):
                cc = cols[stk, ch] * (1 - mw) + mc[ch] * mw
                c3[:, ch] = np.bincount(pix, Aa * cc * lv, npx) * k2
        else:
            for ch in range(3):
                c3[:, ch] = np.bincount(pix, Aa * cols[stk, ch] * lv, npx) * k2
        a1 = a1.reshape(h, w); c3 = c3.reshape(h, w, 3)
        if clip is not None:
            cf = clip[y0:y1, x0:x1]
            a1 = a1 * cf; c3 = c3 * cf[..., None]
        if fade is not None:
            ff = fade[y0:y1, x0:x1]
            a1 = a1 * ff; c3 = c3 * ff[..., None]
        m = a1 > 1e-4
        if not m.any(): return
        col = np.clip(c3[m] / a1[m][:, None], 0, 1)
        Cb = self.C[y0:y1, x0:x1]
        Fb = self.F[y0:y1, x0:x1]
        old = Cb[m]
        if smear:
            sm = (smear * np.clip(Fb[m], 0, 1))[:, None]
            col = col * (1 - sm) + old * sm
        tgt = (1 - opacity) * old * col / np.maximum(hexc('paper'), 0.5) + opacity * col
        A1 = np.minimum(a1[m], 1)[:, None]
        Cb[m] = old + A1 * (tgt - old)
        Fb[m] = np.minimum(1.5, Fb[m] + a1[m] * 0.6)

    # ================================================================== accents
    def crayon(self, path, width=7.0, colour='black', pressure=0.92, alpha=1.0, wobble=1.2, seg=(50, 150), gap=0.08,
               double=0.35, dry=0.25, taper=0.1, clip=None, smooth=True, seed=None):
        """a scratchy crayon line along `path`: it wobbles, and is split into overlapping pieces of different
        widths and pressures (the hand lifts and presses again); `gap` is the chance that a join is left open;
        `double` the chance that a piece gets a thinner second stroke slightly off it (a scratchy, re-stated line)."""
        r = self._r(seed)
        P = _resample(_smooth_path(path, 8) if smooth else np.asarray(path, np.float32), 2.0)
        if len(P) < 2: return 0
        Tg = np.gradient(P, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-6
        Nn = np.stack([-Tg[:, 1], Tg[:, 0]], 1)
        nn = len(P)
        if wobble:
            off = np.interp(np.arange(nn), np.linspace(0, nn - 1, max(2, nn // 14)),
                            r.normal(0, wobble, max(2, nn // 14)))
            P = P + Nn * off[:, None].astype(np.float32)
        paths, ws, ps = [], [], []
        i = 0
        while i < nn - 1:
            m = int(r.uniform(seg[0], seg[1]) / 2.0)
            j = min(nn, i + max(3, m))
            if nn - j < 6: j = nn
            piece = P[i:j]
            paths.append(piece); ws.append(width * r.uniform(0.72, 1.18)); ps.append(pressure * r.uniform(0.85, 1.04))
            if r.random() < double and len(piece) > 4:
                o = Nn[i:j] * (width * r.uniform(0.25, 0.5) * r.choice([-1, 1]))
                paths.append(piece + o); ws.append(width * r.uniform(0.4, 0.6))
                ps.append(pressure * r.uniform(0.6, 0.8))
            back = int(r.uniform(5, 12))                            # the next piece starts over the end of this
            if r.random() < gap: back = -int(r.uniform(2, 5))       # ... or the hand lifts: a small break
            i = max(i + 2, j - back)
        return self.lines(paths, colour, ws, ps, alpha, dry, 0.4, 0.04, 0.97, None, 0.3, taper, 0.02, 0.04, clip,
                          None, 1, None, int(r.integers(1 << 30)), sidep=0.5)

    def blush(self, cx, cy, rx, ry=None, colour='blush', angle=-58.0, strength=0.85, width=(7, 12), rot=0.0,
              clip=None, seed=None):
        """a cheek patch of parallel hatched strokes in a ragged ellipse: dense in the middle, broken at the rim"""
        ry = rx if ry is None else ry
        reg = self.spot(cx, cy, rx, ry, rot, solid=0.45, power=1.0)
        cl = self._edge_clip(self.ellipse(cx, cy, rx * 1.05, ry * 1.05, rot), 0.9)
        if clip is not None: cl = cl * clip
        return self.fill(reg, angle, colour, length=(0.55 * min(rx, ry), 1.1 * min(rx, ry)), width=width,
                         density=2.6 * strength, pressure=0.6 + 0.3 * strength, dry=0.35, streak=0.45, smear=0.2,
                         opacity=0.9, clip=cl, passes=2, value=0.05, seed=seed)

    def dashes(self, path, colour='navy', spacing=26.0, length=(26, 40), width=(11, 16), angle=90.0, jitter=7.0,
               pressure=0.92, dry=0.2, clip=None, along=0.0, seed=None):
        """short bold dashes centred along `path`, each turned `angle` degrees from the path (90 = across it):
        stripes on knitwear, the ribs of a cuff, a fringe"""
        r = self._r(seed)
        P = _resample(_smooth_path(path, 8), 1.0)
        if len(P) < 2: return 0
        d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        s = np.arange(spacing * r.uniform(0.2, 0.8), d[-1], spacing)
        if not len(s): return 0
        s = s + r.normal(0, spacing * 0.08, len(s))
        cx = np.interp(s, d, P[:, 0]); cy = np.interp(s, d, P[:, 1])
        Tg = np.gradient(P, axis=0)
        tx = np.interp(s, d, Tg[:, 0]); ty = np.interp(s, d, Tg[:, 1])
        a = np.arctan2(ty, tx) + np.deg2rad(angle + r.normal(0, jitter, len(s)))
        L = r.uniform(length[0], length[1], len(s)) if isinstance(length, tuple) else np.full(len(s), float(length))
        sh = (L * along)[:, None] * np.stack([np.cos(a), np.sin(a)], 1)
        c = np.stack([cx, cy], 1) + sh
        e = 0.5 * L[:, None] * np.stack([np.cos(a), np.sin(a)], 1)
        bend = r.normal(0, 0.06, len(s))[:, None] * L[:, None] * np.stack([-np.sin(a), np.cos(a)], 1)
        paths = [np.array([c[i] - e[i], c[i] + bend[i], c[i] + e[i]], np.float32) for i in range(len(s))]
        wd = r.uniform(width[0], width[1], len(s)) if isinstance(width, tuple) else np.full(len(s), float(width))
        return self.lines(paths, colour, list(wd), pressure, 1.0, dry, 0.35, 0.1, 0.96, None, 0.2, 0.12, 0.04, 0.05,
                          clip, None, 1, 3, int(r.integers(1 << 30)))

    def smear(self, region, colour='black', angle=0.0, length=(90, 240), width=(18, 34), density=0.9, pressure=0.8,
              dry=0.55, streak=0.65, edge=0.9, seed=None, **kw):
        """a dry-brushed smear: a cast shadow on the ground, a smear of sky -- long dry strokes with big skips and
        torn ends"""
        return self.fill(region, angle, colour, length=length, width=width, density=density, pressure=pressure,
                         dry=dry, streak=streak, edge=edge, passes=2, seed=seed, **kw)

    def wisp(self, x, y, height, sway=28.0, colour='mist', width=7.0, pressure=0.6, turns=1.6, lean=-0.15, seed=None):
        """a rising curl (steam, breath): an S-curve drawn as a light broken crayon line"""
        r = self._r(seed)
        t = np.linspace(0, 1, 40)
        ph = r.uniform(0, 2 * np.pi)
        xs = x + sway * np.sin(t * turns * 2 * np.pi + ph) * (0.4 + 0.6 * t) + lean * height * t
        ys = y - height * t
        return self.crayon(np.stack([xs, ys], 1), width, colour, pressure, alpha=0.9, wobble=0.6, seg=(70, 160),
                           gap=0.1, double=0.1, dry=0.45, taper=0.5, smooth=False, seed=int(r.integers(1 << 30)))

    # ================================================================== faces
    def eye(self, cx, cy, w, h, look=(0.0, 0.0), lid=0.5, side=1, rot=0.0, colour='black', width=None, lower=0.4,
            lash=0.6, iris=0.42, crease=0.5, seed=None):
        """a black crayon eye of width w and height h (`side` = +1 if the outer corner is on the right): the opening
        between a lowered upper lid (`lid` 0..1: 0 wide open, 1 nearly shut -- a downward gaze) and the lower lid;
        a big dark iris (`iris` x w across, moved by `look` (dx, dy) in -1..1) seen only inside the opening, with a
        small paper gap as the catchlight; a heavy upper-lid stroke that thickens toward the outer corner and
        flicks out, a faint crease above it and a short light mark for the lower lid"""
        r = self._r(seed)
        width = max(3.0, 0.12 * w) if width is None else width
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        L = lambda pts: [(cx + u * c - v * s, cy + u * s + v * c) for u, v in pts]
        hw = 0.5 * w
        dl = lid * 0.55 * h
        up = [(-side * hw, 0.1 * h), (-side * 0.55 * hw, -0.36 * h + 0.8 * dl), (0, -0.48 * h + dl),
              (side * 0.6 * hw, -0.38 * h + 0.9 * dl), (side * hw, 0.02 * h)]
        lo = [(side * 0.55 * hw, 0.38 * h), (0, 0.48 * h), (-side * 0.55 * hw, 0.36 * h)]
        opening = self.poly(L(up + lo), smooth=True)
        ir = 0.5 * iris * w
        ic = L([(look[0] * 0.28 * hw, look[1] * 0.16 * h + 0.05 * h)])[0]
        disc = self.ellipse(ic[0], ic[1], ir, ir * 1.03)
        hl = self.ellipse(ic[0] - side * 0.28 * ir, ic[1] - 0.05 * ir, 0.2 * ir, 0.17 * ir)
        cut = disc * self.soften(opening, 0.8) * (1 - hl)
        n = self.fill(cut, rot + 75, {colour: 3, 'charcoal': 1}, length=(0.9 * ir, 1.8 * ir),
                      width=(0.4 * ir, 0.65 * ir), density=3.0, pressure=0.96, dry=0.1, streak=0.2,
                      clip=self._edge_clip(cut, 0.25), passes=2, seed=int(r.integers(1 << 30)))
        # the upper lid: one heavy stroke, heavier and longer at the outer corner
        n += self.crayon(L(up), width, colour, pressure=0.96, wobble=0.4, seg=(w * 0.7, w * 1.4), gap=0.0,
                         double=0.4, dry=0.12, taper=0.2, seed=int(r.integers(1 << 30)))
        n += self.crayon(L([(side * 0.05 * hw, -0.47 * h + dl), (side * 0.62 * hw, -0.38 * h + 0.9 * dl),
                            (side * 1.04 * hw, 0.0)]), width * 1.45, colour, pressure=0.98, wobble=0.3,
                         seg=(w, w * 2), gap=0.0, double=0.0, dry=0.2, taper=0.35, seed=int(r.integers(1 << 30)))
        if lash:
            n += self.crayon(L([(side * 0.98 * hw, 0.0), (side * (1.0 + 0.3 * lash) * hw, -0.32 * h)]), width * 0.75,
                             colour, pressure=0.9, wobble=0.0, seg=(w, w), gap=0.0, double=0.0, dry=0.3, taper=0.6,
                             seed=int(r.integers(1 << 30)))
        if crease:
            n += self.crayon(L([(-side * 0.45 * hw, -0.62 * h), (side * 0.1 * hw, -0.82 * h),
                                (side * 0.75 * hw, -0.62 * h)]),
                             width * 0.5, 'peach_deep', pressure=0.55 + 0.35 * crease, wobble=0.4, seg=(w, w * 2),
                             gap=0.0, double=0.0, dry=0.35, taper=0.4, seed=int(r.integers(1 << 30)))
        if lower:
            n += self.crayon(L(lo), width * 0.42, colour, pressure=0.45 + 0.45 * lower, wobble=0.3, seg=(w, w * 2),
                             gap=0.0, double=0.0, dry=0.45, taper=0.5, seed=int(r.integers(1 << 30)))
        return n

    def brow(self, path, width=10.0, colour='black', pressure=0.9, seed=None):
        """a brow: one crayon stroke thicker at the head, with a few short hairs along it"""
        r = self._r(seed)
        P = _resample(_smooth_path(path, 8), 2.0)
        n = self.lines([P], colour, width, pressure, 1.0, 0.4, 0.5, 0.05, 0.97, None, 0.25, 0.4, 0.02, 0.04,
                       seed=int(r.integers(1 << 30)), k=9, sidep=0.45)
        m = len(P)
        hairs = []
        for t in np.linspace(0.05, 0.8, 5):
            i = int(t * (m - 1)); j = min(m - 1, i + max(2, m // 5))
            o = r.normal(0, width * 0.15, 2)
            hairs.append(np.array([P[i] + o, P[j] + o * 0.5], np.float32))
        n += self.lines(hairs, colour, width * 0.45, pressure * 0.85, 1.0, 0.4, 0.3, 0.0, 0.97, None, 0.3, 0.5,
                        seed=int(r.integers(1 << 30)), k=3)
        return n

    def lips(self, cx, cy, w, h, colour='lip', dark='lip_dark', smile=0.0, rot=0.0, side=0.0, parting=0.7, seed=None):
        """a flat red-orange mouth of width w and height h laid in short dense strokes: an upper lip with a soft
        bow, a fuller lower lip, a darker parting; side shifts the bow (a three-quarter view), smile lifts the
        corners"""
        r = self._r(seed)
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        L = lambda pts: [(cx + u * c - v * s, cy + u * s + v * c) for u, v in pts]
        hw = 0.5 * w; b = side * 0.18 * hw; sm = smile * 0.35 * h
        upper = L([(-hw, -sm), (-0.55 * hw + b, -0.42 * h), (-0.12 * hw + b, -0.5 * h), (b, -0.36 * h),
                   (0.14 * hw + b, -0.52 * h), (0.6 * hw + b, -0.4 * h), (hw, -sm), (0.3 * hw + b, 0.02 * h),
                   (-0.3 * hw + b, 0.02 * h)])
        lower = L([(-0.92 * hw, -sm * 0.9), (-0.3 * hw + b, 0.05 * h), (0.32 * hw + b, 0.05 * h),
                   (0.92 * hw, -sm * 0.9), (0.6 * hw + b, 0.42 * h), (b, 0.56 * h), (-0.58 * hw + b, 0.4 * h)])
        mu = self.poly(upper, smooth=True); ml = self.poly(lower, smooth=True)
        n = 0
        for m in (mu, ml):
            n += self.fill(m, rot + r.normal(0, 6), colour, length=(0.35 * w, 0.7 * w), width=(0.18 * h, 0.3 * h),
                           density=2.6, pressure=0.96, dry=0.15, streak=0.2, value=0.04, smear=0.0,
                           clip=self._edge_clip(m, 0.25), passes=2, seed=int(r.integers(1 << 30)))
        if parting:
            n += self.crayon(L([(-0.88 * hw, -sm * 0.9), (-0.3 * hw + b, 0.04 * h), (0.3 * hw + b, 0.04 * h),
                                (0.88 * hw, -sm * 0.9)]), max(2.0, 0.11 * h), dark, pressure=0.75 * parting + 0.2,
                             wobble=0.5, seg=(w, w * 2), gap=0.0, double=0.0, dry=0.3, taper=0.4,
                             seed=int(r.integers(1 << 30)))
        return n

    def hair(self, region, flow, colours=('black',), n=60, length=(120, 260), width=(7, 14), bend=0.06, pressure=0.9,
             dry=0.45, taper=0.75, roots=None, clip=None, jitter=0.12, seed=None):
        """loose energetic hair strokes: n long strokes that land in `region` (or start on `roots`), follow `flow`
        (degrees, a radians field or f(x, y)) with a strong bend and thin to a point; colours are picked at random"""
        r = self._r(seed)
        M = self._mask(roots if roots is not None else region)
        bb = self._bbox(M)
        if bb is None: return 0
        x, y = self._seed_points(M, bb, n * 6, r)
        if not len(x): return 0
        sel = r.choice(len(x), min(n, len(x)), replace=False)
        x, y = x[sel], y[sel]
        m = len(x)
        L = self._sizes(length, x, y, r); Wd = self._sizes(width, x, y, r)
        k = 9
        field = self._field_rad(flow)
        if roots is not None:
            # start at the root: integrate forward only
            P = np.zeros((m, k, 2), np.float32)
            P[:, 0, 0] = x; P[:, 0, 1] = y
            st = L / (k - 1)
            jit = (jitter * r.normal(0, 1, m)).astype(np.float32)
            bd = (bend * r.normal(0, 1.2, m)).astype(np.float32)
            px, py = x.copy(), y.copy()
            for j in range(1, k):
                a = _lookup(field, px, py) + jit + bd * j
                px = px + np.cos(a) * st; py = py + np.sin(a) * st
                P[:, j, 0] = px; P[:, j, 1] = py
        else:
            P = self._centrelines(x, y, L, field, (jitter * r.normal(0, 1, m)).astype(np.float32),
                                  (bend * r.normal(0, 1.2, m)).astype(np.float32), k)
        cols = self._colours(list(colours) if not isinstance(colours, (str, dict)) else colours, x, y, r)
        pr = (pressure * r.uniform(0.85, 1.05, m)).astype(np.float32)
        al = np.ones(m, np.float32)
        dr = (dry * r.uniform(0.6, 1.3, m)).astype(np.float32)
        st2 = np.full(m, 0.45, np.float32)
        self._draw(P, Wd, cols, al, pr, dr, st2, taper, 0.96, 0.05, None, 0.04, clip, None, 2, 0.25, r)
        self.n_strokes += m
        return m

    # ================================================================== output
    def finish(self, tooth=1.0, relief=1.0, grain=1.0, soft=0.15):
        """record the finishing (applied in render, so every stage snapshot matches the final look; call it before
        the first mark): the tooth showing through the wax, a little waxy relief at the edges of the deposit, a
        faint grain, a very slight softening"""
        self.fin = dict(tooth=tooth, relief=relief, grain=grain, soft=soft)
        return self

    def render(self):
        """the finished picture (the canvas is untouched)"""
        C = self.C
        f = self.fin
        if not f: return np.clip(C, 0, 1)
        self._need()
        out = C.copy()
        wax = np.clip(self.F, 0, 1)
        if f['relief']:
            # a little body at the edges of the deposit (lit from the upper left); pale wax shows it least
            Hs = blur(np.minimum(self.F, 1.2), 1.5)
            gy, gx = np.gradient(Hs)
            sh = np.clip(-(LIGHT[0] * gx + LIGHT[1] * gy) * 0.5 * f['relief'], -0.05, 0.05)
            sh *= 1 - 0.75 * smoothstep(0.55, 0.92, out.mean(-1))
            out *= (1 + sh)[..., None]
            del Hs, gx, gy, sh
        if f['tooth']:
            out *= (1 + f['tooth'] * 0.07 * wax * (self.T - 0.5))[..., None]
        if f['grain']:
            out *= (1 + f['grain'] * 0.006 * self._grain)[..., None]
        if f['soft']:
            for c in range(3): out[..., c] = out[..., c] * (1 - f['soft']) + blur(out[..., c], 0.6) * f['soft']
        return np.clip(out, 0, 1)

    def composite(self):
        out = self.render()
        out *= 255; out += 0.5
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
