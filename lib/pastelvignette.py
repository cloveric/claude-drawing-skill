"""pastelvignette — 色粉小像 / Pastel Vignette: a whimsical picture-book character vignette in soft chalk pastel and a
little gouache on white paper (numpy + Pillow only).

The look: one or two charming characters -- often a person with an animal companion -- painted half-length on pure
white paper with no background panel and no frame: the painting simply stops, and its edges dissolve into the white
in dry, feathered strokes. The medium is soft chalk pastel with a little gouache: the colours are soft and powdery
(pale powder blue, cream, warm skin) with one warm saturated accent family (orange, tangerine, yellow -- a fluffy
cat, a pom-pom, a bow); you can see the pastel grain and dry, directional, painterly strokes in the clothes, while
faces are blended smooth. The characters are whimsical: big round eyes with dark irises and white catchlights, very
large rosy blush circles, a red-tipped nose, a small mouth; hair and fur are hundreds of fine wispy strands, some
flying loose. Modelling is soft, with no hard ink outline -- only a few thin soft lines (an eyelid, a nostril, the
shadow side of a cheek). Behind them, at most a sprig of leaves or a faint pencil-grey sketch.

Physical model
  paper       A white drawing sheet with a fine tooth `T`, rank-equalised to a uniform 0..1 so that "the pastel reaches
              where tooth > 1 - pressure" turns pressure straight into coverage. A stick dragged over the paper rides
              from peak to peak, so the tooth is also pre-averaged along 8 directions (`TD`) and every stroke reads the
              one that matches its own direction: the pits it skips are drawn out a little along the stroke. A pigment
              buffer `F` records how much pastel already sits in the tooth: later layers reach a little deeper.
  stroke      A pastel / dry-brush stroke is a short centreline integrated through an orientation field (angles mod
              pi) with a slight wrist arc. Tens of thousands go at once: Pillow draws every *segment* of every stroke
              with its own id into a 2x supersampled integer map (segments are lengthened a little so a bend leaves
              no notch); for each covered sub-pixel numpy looks up the segment, recovers the position along the
              stroke (u, for the pressure profile: pressed at the start, lifting off at the end) and across it (v,
              for a soft edge and the bristle lanes of a dry stick: a few parallel streaks that open up as the stroke
              runs dry), compares the pressure with the direction-matched tooth and lays the pigment. Sub-pixels are
              summed back with bincount, so a pass costs about one Pillow line per segment. Within one pass the top
              stroke wins; layers come from several passes. Big passes are split into horizontal bands (memory).
  pigment     Soft pastel is nearly opaque: new = old + A x (target - old), target = (1 - opacity) x old x colour /
              paper + opacity x colour -- so a pale stroke covers a dark one (a white dry stroke over powder blue),
              and a thin one tints what is under it.
  blending    `wash()` is pastel rubbed in with a finger (or a thin gouache layer): a smooth, opaque coat whose colour
              can be a field (a ramp looked up by a light field), with the deepest pits of the tooth left a touch
              lighter, and an edge that wanders and breaks up into the tooth instead of being a vector edge.
              `model()` lays a soft dome light on a shape and washes the ramp over it (faces, fur under-colour).
  dissolve    The vignette has no frame: coats are given a ragged, low-frequency boundary and strokes near a region's
              border lose pressure (`fade`), so the colour breaks up into tooth speckle and single dry strokes that
              end at different places before the white.
  strands     `strands()` traces hundreds or thousands of fine hairs through a flow field (each with its own jitter and
              steady curl), coloured dark to light by a sheen field and painted dark first, light last; a few fly
              loose outside the silhouette. `fur()` lays tufts (strands whose roots spread and whose tips converge,
              darker on the side away from the light); `fluff()` sends short strands outward across a silhouette,
              coloured from the paint just inside it, so a fluffy edge melts into whatever is behind.
  faces       `eye()` a big round eye: an off-white ball shaded grey-blue under the lid, a dark iris with a lighter lower
              half and a darker rim, a pupil, a soft dark upper-lid line with a flick at the outer corner, a faint
              crease and lower lid, two white catchlights. `blush()` a big powdery round cheek, `nose()` a soft side
              shadow and a red tip, `mouth()` small lips, `brow()` a tapered line plus fine hairs.
  lines       `line()` a smooth tapered round-brush line (lid lines, whiskers, a thin soft contour); `pencil()` a faint
              graphite line laid as several sketchy overlapping strokes (the background sketch).
  plants      `leaf()` a leaf shape modelled lighter on one side with a pale midrib; `sprig()` a stem with leaves.
  finish      `finish()` records a slight softness and a fine grain (applied in render, so every stage snapshot
              matches the final look); the paper stays white.

API (canvas pixel coordinates; a number given as a field is a direction in degrees, 0 = to the right, 90 = down;
     field arrays are radians; colours are PAINTS names, '#rrggbb' or RGB triples; ramps are RAMPS names or lists,
     dark -> light)
  surface    PastelVignette(W, H, seed, keep_stages, stages_dir); paper(tone, tooth); finish(soft, grain, warmth)
  masks      poly(pts, smooth) / ellipse(cx, cy, rx, ry, rot) / blob(cx, cy, rx, ry, rough) / tube(path, w0, w1) /
             rect(x0, y0, x1, y1) / below(xs, ys) -> canvas-sized float masks; ragged(mask, amp, scale, edge)
  fields     flow(angle, turb, scale); radial(cx, cy, offset); contour(mask, sigma, offset, fallback);
             blend(f1, f2, w); rotate(field, deg); field(f(x, y) -> degrees); value(top, bottom, y0, y1);
             shading(mask, light, sigma, wrap)
  strokes    strokes(region, field, colour, length, width, density, pressure, opacity, alpha, streak, soft, taper,
             passes, clip, avoid, fade); lines(paths, colour, width, ...); pencil(path, colour, width, alpha)
  layers     wash(mask, colour, alpha, grain, edge, dry, clip); model(mask, colours, light, lit, gamma, lo, hi);
             glaze(mask, colour, alpha, mode); dab(x, y, r, colour, alpha, soft)
  hair, fur  strands(region, flow, colours, n, length, width, curl, jitter, shade, alpha, clip, roots, lock);
             fur(region, field, colour, length, width, density, tuft, spread, curl, converge, side, light);
             fluff(mask, length, n, width, out, alpha, lift)
  faces      eye(cx, cy, rx, ry, iris, look, lid, flick, lashes, side, rot); brow(path, width, colour);
             blush(cx, cy, rx, ry, colour, strength); nose(x, y, size, side, tip, shade); mouth(x, y, w, smile, colour);
             line(path, width, colour, alpha, taper, dry)
  plants     leaf(base, tip, width, colours, bend); sprig(path, n, size, colours, seed)
  output     render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 88, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from pastelvignette import PastelVignette
    p = PastelVignette(1920, 1080, seed=3); p.finish(); p.paper()
    face = p.ellipse(960, 420, 150, 175)
    p.model(face, 'skin')
    p.eye(900, 430, 34, 38, look=(-0.3, 0)); p.eye(1020, 430, 34, 38, look=(-0.3, 0))
    p.blush(880, 500, 50); p.blush(1040, 500, 50); p.nose(955, 495, 16)
    coat = p.ragged(p.poly([(700, 640), (1220, 640), (1300, 1000), (620, 1000)]), 40)
    p.model(coat, 'powder'); p.strokes(coat, -70, ('powder_light', 'white'), (40, 90), (8, 16), 0.8, streak=0.6)
    p.save('vignette.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, blob_pts

PAINTS = {
    # paper and pencil
    'paper': '#fcfbf8', 'white': '#ffffff', 'chalk': '#fbf8f1', 'pencil': '#8f8f96', 'pencil_light': '#bdbdc3',
    'graphite': '#5d5d66',
    # skin
    'skin': '#f5d6c4', 'skin_light': '#fbe8dc', 'skin_pale': '#fef3ec', 'skin_shade': '#e8b49e', 'skin_deep': '#c9877a',
    'blush': '#f0806b', 'nose': '#ea6d5c', 'lip': '#e0624f', 'lip_dark': '#b2443a', 'lid': '#3b2726',
    'brow': '#4a3633', 'crease': '#c98e80',
    # eyes
    'eye_white': '#f9f7f2', 'eye_shade': '#b9bccb', 'iris': '#5b3a29', 'iris_light': '#9c6b43', 'pupil': '#161013',
    'amber': '#d9a531', 'amber_light': '#f1d06a', 'olive_eye': '#9a8f3c',
    # hair
    'hair_black': '#17151d', 'hair_dark': '#24232e', 'hair': '#33354a', 'hair_blue': '#4a5470', 'hair_grey': '#7f8aa6',
    'hair_light': '#aeb8cf',
    # powder blues and creams (the soft family)
    'powder_deep': '#6e88ae', 'powder_shade': '#91a9c9', 'powder': '#b5cae2', 'powder_light': '#d6e3f0',
    'powder_pale': '#ecf2f8', 'cream': '#f3e8d4', 'cream_shade': '#dccbb0', 'cream_deep': '#bfa98a', 'ivory': '#faf5ea',
    # the warm accent family
    'ginger_deep': '#a9461c', 'ginger_dark': '#c95a22', 'ginger': '#e7772f', 'orange': '#f08c3e',
    'tangerine': '#f5a04f', 'apricot': '#f8bf7e', 'peach': '#fbd9ae', 'butter': '#f5d77a', 'mustard': '#e1ae47',
    'fur_cream': '#f7ecd8', 'fur_white': '#fdf8ef', 'ear_pink': '#f1b6a4',
    # greens and greys for the background
    'eucalyptus_deep': '#5f7d73', 'eucalyptus': '#86a196', 'eucalyptus_light': '#b0c5ba', 'sage': '#a7b58c',
    'olive': '#8f9a5c', 'ochre': '#d5a24c', 'stem': '#7d7a5a', 'mist': '#d9dadf', 'umber': '#5b4033',
}
RAMPS = {                                   # dark -> light
    'skin': ('#cf9282', '#e6b19d', '#f2cbb7', '#f8dfd0', '#fdeee5'),
    'neck': ('#c48475', '#d9a08c', '#ebbca7', '#f3d2c0', '#f8e1d4'),
    'powder': ('#7891b7', '#97afd0', '#b6cae2', '#d2e0ee', '#ebf1f8'),
    'cream': ('#c9b596', '#ddcdb2', '#eee3cf', '#f7f0e3', '#fdfaf3'),
    'ginger': ('#a7461b', '#cc5f24', '#e9792f', '#f39b4b', '#f9c487'),
    'hair': ('#141219', '#1d1c26', '#272836', '#363b50', '#58617d'),
    'eucalyptus': ('#5c7a70', '#7a978b', '#9db5a8', '#c0d1c6', '#dfe8e1'),
    'ochre': ('#a9752f', '#c69344', '#dcb160', '#ebcc88', '#f6e4b8'),
    'mist': ('#b9bbc3', '#cacbd1', '#d9dadf', '#e7e7ea', '#f2f2f3'),
}
LIGHT = (-0.55, -0.6, 0.58)                 # upper left, a little in front


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    return hexc(a) * (1 - t) + hexc(b) * t


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


def _resample_k(P, k):
    """resample a polyline to exactly k points by arc length"""
    P = np.asarray(P, np.float32)
    if len(P) == 1: return np.repeat(P, k, 0)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    if d[-1] < 1e-4: return np.repeat(P[:1], k, 0)
    s = np.linspace(0, d[-1], k)
    return np.stack([np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], 1).astype(np.float32)


class PastelVignette:
    PAINTS = PAINTS
    RAMPS = RAMPS
    LIGHT = LIGHT

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.P = hexc('paper')
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = self.P
        self.F = np.zeros((H, W), np.float32)             # pigment already sitting in the tooth
        self.T = None; self.TD = None; self.EN = None
        self.fin = None
        self.floor = 0.22                                  # pigment a stick still leaves in the pits of the tooth
        self.n_strokes = 0

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== paper
    def paper(self, tone='paper', tooth=1.0, drag=3, seed=None):
        """white drawing paper: an equalised fine tooth, shown on the bare sheet only as a whisper"""
        H, W = self.H, self.W
        r = self._r(seed)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.6)
        g2 = noise2d(H, W, 2.6, 2, int(r.integers(1 << 30)))
        g3 = noise2d(H, W, 8.0, 2, int(r.integers(1 << 30)))
        self.T = _equalise(0.75 * z(g1) + 0.45 * z(g2) + 0.18 * z(g3))
        self.P = hexc(tone)
        self.C = (self.P[None, None] * (1 - 0.006 * tooth * (0.5 - self.T[..., None]))).astype(np.float32)
        self.F[:] = 0
        # tooth dragged along 8 stroke directions (kept as uint8: 8 canvases of float32 would be 66 MB at 1080p)
        TD = np.empty((8, H, W), np.uint8)
        ks = np.arange(-drag, drag + 1); wk = 1.0 - np.abs(ks) / (drag + 1.0)
        for b in range(8):
            a = np.pi * b / 8
            acc = np.zeros_like(self.T)
            for k, w in zip(ks, wk):
                acc += w * np.roll(self.T, (int(round(k * np.sin(a))), int(round(k * np.cos(a)))), axis=(0, 1))
            TD[b] = np.round(_equalise(0.4 * self.T + 0.6 * acc / wk.sum()) * 255).astype(np.uint8)
            del acc
        self.TD = TD
        self.EN = noise2d(H, W, 4.0, 2, int(r.integers(1 << 30))) - 0.5
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
        x0, x1 = max(0, int(cx - max(rx, ry) - 3)), min(self.W, int(cx + max(rx, ry) + 4))
        y0, y1 = max(0, int(cy - max(rx, ry) - 3)), min(self.H, int(cy + max(rx, ry) + 4))
        out = np.zeros((self.H, self.W), np.float32)
        if x1 <= x0 or y1 <= y0: return out
        dx, dy = self.XX[y0:y1, x0:x1] - cx, self.YY[y0:y1, x0:x1] - cy
        u, v = (dx * c + dy * s) / rx, (-dx * s + dy * c) / ry
        d = np.sqrt(u * u + v * v)
        out[y0:y1, x0:x1] = np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1)
        return out

    def blob(self, cx, cy, rx, ry=None, rough=0.1, seed=None, rot=0.0):
        ry = rx if ry is None else ry
        return self.poly(blob_pts(cx, cy, rx, ry, rough, 120, int(self._r(seed).integers(1 << 30)), np.deg2rad(rot)))

    @staticmethod
    def tube_pts(path, w0, w1=None, per=8):
        """outline points of a tube of width w0 -> w1 along a path (limbs, tails, stems)"""
        w1 = w0 if w1 is None else w1
        P = spline(path, per) if len(path) > 2 else _resample(path, 4)
        n = len(P)
        Tg = np.gradient(P, axis=0); Tg /= np.linalg.norm(Tg, axis=1, keepdims=True) + 1e-6
        Nn = np.stack([-Tg[:, 1], Tg[:, 0]], 1)
        w = (np.linspace(w0, w1, n) if np.ndim(w0) == 0 else np.interp(np.linspace(0, 1, n), np.linspace(0, 1, len(w0)), w0))
        w = np.asarray(w, np.float32)[:, None] * 0.5
        return np.vstack([P + Nn * w, (P - Nn * w)[::-1]])

    def tube(self, path, w0, w1=None):
        """mask of a tube; w0 may be a list of widths along the path"""
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

    def ragged(self, mask, amp=24.0, scale=60.0, edge=1.0, seed=None):
        """give a mask an unfinished, dry boundary: the edge is pushed in and out by a low-frequency wander (amp px
        at `scale` px) and, within a few px of it, breaks up into the paper tooth -- where a vignette stops"""
        r = self._r(seed)
        bb = self._bbox(mask, pad=int(amp * 2) + 4)
        out = np.zeros_like(mask)
        if bb is None: return out
        x0, y0, x1, y1 = bb
        m = mask[y0:y1, x0:x1]
        h, w = m.shape
        sd = max(2.0, amp * 0.6)
        b = blur(m, sd)
        n = noise2d(h, w, scale, 3, int(r.integers(1 << 30))) - 0.5
        n2 = noise2d(h, w, scale * 0.25, 2, int(r.integers(1 << 30))) - 0.5
        # the edge sits where the blurred mask crosses a wandering threshold (never far outside: no islands)
        th = np.clip(0.5 + 1.1 * n + 0.45 * n2, 0.14, 0.86)
        core = smoothstep(th - 0.03, th + 0.03, b)
        if edge:
            zone = smoothstep(th - 0.22, th, b) * (1 - core)
            Tt = self.T[y0:y1, x0:x1] if self.T is not None else 0.5
            core = np.maximum(core, zone * smoothstep(0.55, 0.8, Tt + zone * 0.35) * edge)
        out[y0:y1, x0:x1] = core
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

    def radial(self, cx, cy, offset=0.0, turb=4.0, scale=120.0, seed=None):
        """directions pointing away from (cx, cy), offset in degrees"""
        a = np.arctan2(self.YY - cy, self.XX - cx) + np.deg2rad(offset)
        if turb:
            a = a + np.deg2rad(2 * turb * (noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5))
        return a.astype(np.float32)

    def contour(self, mask, sigma=8.0, offset=0.0, fallback=None):
        """directions along the iso-lines of a (blurred) shape: strokes that wrap round a dome, a sleeve, a cheek.
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

    def value(self, top=0.0, bottom=1.0, y0=0, y1=None, mottle=0.04, scale=220.0, seed=None):
        """a 0..1 field: a vertical ramp from `top` at y0 to `bottom` at y1, with low-frequency mottling"""
        y1 = self.H if y1 is None else y1
        t = np.clip((self.YY - y0) / max(1, y1 - y0), 0, 1)
        v = top + (bottom - top) * t
        if mottle:
            v = v + 2 * mottle * (noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5)
        return np.clip(v, 0, 1).astype(np.float32)

    def shading(self, mask, light=LIGHT, sigma=None, wrap=0.25, flat=0.0):
        """0..1 light on a soft dome raised from the silhouette (sum of blurs), lit from `light` (x, y, z; screen y
        down). wrap > 0 lets the light creep round the terminator; flat mixes toward 0.5."""
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

    def strokes(self, region, field=-60.0, colour='powder', length=(30, 70), width=(8, 16), density=1.0,
                pressure=0.78, opacity=0.85, alpha=0.8, streak=0.45, soft=0.6, jitter=0.07, bend=0.03, value=0.035,
                hue=0.02, taper=(0.55, 0.1), passes=2, clip='auto', avoid=None, fade='auto', k=5, seed=None):
        """lay dry pastel / dry-brush strokes over `region` (a 0..1 landing-probability mask or a box) following
        `field` (degrees or a radians field). density ~ how many times the strokes would tile the region;
        length / width: (lo, hi), a number or f(x, y); colour: a paint, a list of paints (picked at random), (ramp,
        value field or f(x, y)) or f(x, y) -> (N, 3); pressure: how deep the pigment reaches into the tooth;
        opacity: how much a pale stroke covers what is under it; streak: how much the bristle lanes open up as
        the stroke runs dry; soft: the soft fraction of the stroke's half-width; taper: pressure at (start, end);
        clip: a mask the strokes are cut to ('auto' = the region's support, with a wandering edge); fade: a 0..1
        field easing the pressure off pixel by pixel ('auto' = region ** 0.65 -- so a region that fades out makes
        the strokes break up into the tooth); avoid: things to paint round. Returns the number of strokes."""
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
        if hue: cols = hue_rotate(cols, (hue * r.normal(0, 1, n)).astype(np.float32))
        cols = np.clip(cols, 0, 1)
        P = self._centrelines(x, y, L, self._field_rad(field), (jitter * r.normal(0, 1, n)).astype(np.float32),
                              (bend * r.normal(0.6, 0.6, n)).astype(np.float32), k)
        if isinstance(clip, str) and clip == 'auto':
            clip = smoothstep(0.0, 0.08, M) if arr else None
        if avoid is not None:
            clip = keep if clip is None else clip * keep
        if isinstance(fade, str) and fade == 'auto':
            fade = (M ** 0.65) if arr else None
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (n,)) * r.uniform(0.9, 1.06, n).astype(np.float32)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,)) * r.uniform(0.82, 1.0, n).astype(np.float32)
        st = np.broadcast_to(np.asarray(streak, np.float32), (n,)) * r.uniform(0.6, 1.3, n).astype(np.float32)
        self._draw(P, Wd, cols, al, pr, taper, opacity, clip, passes, r, fade=fade, streak=st, soft=soft)
        self.n_strokes += n
        return n

    def lines(self, paths, colour='graphite', width=2.0, pressure=0.8, opacity=0.85, alpha=0.9, taper=(0.4, 0.2),
              streak=0.0, soft=0.5, value=0.03, hue=0.0, clip=None, fade=None, passes=1, k=None, seed=None):
        """draw explicit strokes: a list of polylines (each (m, 2)), resampled to k points each; painted in order
        (later on top) within each pass"""
        self._need()
        r = self._r(seed)
        if not len(paths): return 0
        if k is None: k = max(3, min(11, int(np.median([len(p) for p in paths]))))
        P = np.stack([_resample_k(np.asarray(p, np.float32), k) for p in paths]).astype(np.float32)
        n = len(P)
        mid = P[:, k // 2]
        Wd = self._sizes(width, mid[:, 0], mid[:, 1], r)
        cols = self._colours(colour, mid[:, 0], mid[:, 1], r)
        if value: cols *= (1 + value * r.normal(0, 1, n).astype(np.float32))[:, None]
        if hue: cols = hue_rotate(cols, (hue * r.normal(0, 1, n)).astype(np.float32))
        cols = np.clip(cols, 0, 1)
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (n,)) * r.uniform(0.95, 1.04, n).astype(np.float32)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,)).astype(np.float32)
        st = np.broadcast_to(np.asarray(streak, np.float32), (n,)).astype(np.float32)
        self._draw(P, Wd, cols, al, pr, taper, opacity, clip, passes, r, fade=fade, streak=st, soft=soft)
        self.n_strokes += n
        return n

    def _draw(self, P, Wd, cols, al, pr, taper, opacity, clip, passes, r, ss=2, fill=0.35, fade=None, streak=None,
              soft=0.45):
        n = len(P)
        tp = np.broadcast_to(np.asarray(taper, np.float32), (n, 2))
        st = np.zeros(n, np.float32) if streak is None else np.asarray(streak, np.float32)
        so = np.broadcast_to(np.asarray(soft, np.float32), (n,)) * r.uniform(0.8, 1.2, n).astype(np.float32)
        nb = np.clip(Wd / r.uniform(2.6, 4.2, n), 1.5, 9).astype(np.float32)        # bristle lanes per stroke
        ph = r.uniform(0, 2 * np.pi, (n, 2)).astype(np.float32)
        passes = max(1, int(passes))
        my = P[:, P.shape[1] // 2, 1]
        for g in range(passes):
            sel = np.arange(g, n, passes)
            if not len(sel): continue
            # split a big pass into horizontal bands so the supersampled id map stays small
            lo = P[sel].reshape(-1, 2).min(0); hi = P[sel].reshape(-1, 2).max(0)
            area = (hi[0] - lo[0] + 2 * Wd.max()) * (hi[1] - lo[1] + 2 * Wd.max()) * ss * ss
            nband = int(np.clip(np.ceil(area / 2.5e6), 1, 96))
            if nband > 1:
                edges = np.quantile(my[sel], np.linspace(0, 1, nband + 1))
                groups = [sel[(my[sel] >= edges[b]) & ((my[sel] < edges[b + 1]) | (b == nband - 1))]
                          for b in range(nband)]
            else:
                groups = [sel]
            for gs in groups:
                if len(gs):
                    self._raster(P[gs], Wd[gs], cols[gs], al[gs], pr[gs], tp[gs], opacity, clip, ss, fill, fade,
                                 st[gs], so[gs], nb[gs], ph[gs])

    def _raster(self, P, Wd, cols, al, pr, tp, opacity, clip, ss, fill, fade, st, so, nb, ph):
        n, k = P.shape[:2]
        ns = k - 1
        pad = float(Wd.max()) + 3
        lo = P.reshape(-1, 2).min(0) - pad; hi = P.reshape(-1, 2).max(0) + pad
        x0, y0 = max(0, int(np.floor(lo[0]))), max(0, int(np.floor(lo[1])))
        x1, y1 = min(self.W, int(np.ceil(hi[0]))), min(self.H, int(np.ceil(hi[1])))
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        # segment tables (canvas units)
        A = P[:, :-1]; B = P[:, 1:]
        seg = B - A
        sl = np.linalg.norm(seg, axis=2) + 1e-4
        D = seg / sl[..., None]
        cum = np.cumsum(sl, axis=1) - sl
        LT = sl.sum(1)
        # draw every segment with its own id; segments are lengthened so a bend leaves no notch
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
        sid = flat[nz]
        del flat
        W2 = w * ss
        sy = nz // W2; sx = nz - sy * W2
        del nz
        si = np.r_[0, np.repeat(np.arange(n), ns)]                 # stroke of each segment (index 0 unused)
        z1 = lambda a: np.r_[0, np.asarray(a, np.float32).ravel()].astype(np.float32)
        AX, AY = z1(A[..., 0]), z1(A[..., 1])
        DX, DY = z1(D[..., 0]), z1(D[..., 1])
        SL, CU = z1(sl), z1(cum)
        ang = np.mod(np.arctan2(D[..., 1], D[..., 0]), np.pi).ravel()
        BIN = np.r_[0, (np.round(ang / np.pi * 8).astype(np.int32) % 8)]
        stk = si[sid].astype(np.int32)
        X = (sx.astype(np.float32) + 0.5) * (1.0 / ss) + x0; Y = (sy.astype(np.float32) + 0.5) * (1.0 / ss) + y0
        rx = X - AX[sid]; ry = Y - AY[sid]
        t = np.clip(rx * DX[sid] + ry * DY[sid], 0, SL[sid])
        u = np.clip((CU[sid] + t) / LT[stk], 0, 1)
        v = np.abs(rx * (-DY[sid]) + ry * DX[sid]) / (0.5 * Wd[stk] + 0.25)
        # pressure profile along the stroke, soft sides, bristle lanes that open as the stroke runs dry
        t0 = tp[stk, 0]; t1 = tp[stk, 1]
        prof = np.minimum(np.clip(t0 + (1 - t0) * u / 0.15, 0, 1), np.clip(t1 + (1 - t1) * (1 - u) / 0.45, 0, 1))
        # the ends are rounded off (a blunt start, a narrowing lift-off), not the square caps of a ruled line
        wf = 0.3 + 0.7 * np.sqrt(np.clip(np.minimum(u / 0.1, (1 - u) / 0.28), 0, 1))
        lat = smoothstep(1.0, 1.0 - so[stk], v / wf)
        sv = (rx * (-DY[sid]) + ry * DX[sid]) / (0.5 * Wd[stk] + 0.25)
        lane = 0.6 * (0.5 + 0.5 * np.sin(sv * nb[stk] * np.pi + ph[stk, 0])) + \
            0.4 * (0.5 + 0.5 * np.sin(sv * nb[stk] * 2.3 * np.pi + ph[stk, 1]))
        p = pr[stk] * (0.55 + 0.45 * prof) * (1 - st[stk] * (1 - lane) * (0.3 + 0.7 * u))
        iy = y0 + sy // ss; ix = x0 + sx // ss
        if fade is not None:
            p = p * (0.4 + 0.6 * fade[iy, ix])                      # a fading region also dries the stroke out
        Tt = self.TD[BIN[sid], iy, ix].astype(np.float32) * (1.0 / 255)
        catch = np.clip((Tt + fill * self.F[iy, ix] - (1 - p)) * 4.0 + 0.5, 0, 1)
        catch = self.floor * np.clip(p, 0, 1) + (1 - self.floor * np.clip(p, 0, 1)) * catch
        Aa = al[stk] * catch * lat * (0.45 + 0.55 * prof)
        pix = (sy // ss) * w + (sx // ss)
        npx = w * h
        k2 = 1.0 / (ss * ss)
        a1 = np.bincount(pix, Aa, npx).astype(np.float32) * k2
        c3 = np.empty((npx, 3), np.float32)
        for ch in range(3):
            c3[:, ch] = np.bincount(pix, Aa * cols[stk, ch], npx) * k2
        a1 = a1.reshape(h, w); c3 = c3.reshape(h, w, 3)
        if clip is not None:
            cf = clip[y0:y1, x0:x1]
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
        Cb[m] = old + np.minimum(a1[m], 1)[:, None] * (tgt - old)
        Fb = self.F[y0:y1, x0:x1]
        Fb[m] = np.minimum(1.4, Fb[m] + a1[m] * 0.5)

    # ================================================================== blended layers
    def _field_colour(self, colour, sl):
        """colour spec -> (h, w, 3) or (3,) for the slice: paint | (ramp, field) | array (H, W, 3) | f(X, Y)"""
        ys, xs = sl
        if isinstance(colour, np.ndarray) and colour.ndim == 3: return colour[ys, xs]
        if isinstance(colour, (tuple, list)) and len(colour) == 2 and isinstance(colour[1], np.ndarray):
            return ramp_at(ramp(colour[0]), colour[1][ys, xs])
        if callable(colour): return np.asarray(colour(self.XX[ys, xs], self.YY[ys, xs]), np.float32)
        return hexc(colour)

    def wash(self, mask, colour, alpha=1.0, grain=0.25, edge=0.5, dry=0.0, clip=None, opacity=1.0):
        """pastel rubbed in with a finger (or a thin gouache coat): a smooth layer over `mask`. colour: a paint,
        (ramp, 0..1 field), an (H, W, 3) array or f(X, Y). grain: the deepest pits of the tooth stay a little
        lighter; edge: within the soft rim of the mask the coat breaks up into the tooth instead of fading
        smoothly; dry: the same over the whole area (a scumbled, dry coat); opacity < 1 mixes multiplicatively."""
        self._need()
        bb = self._bbox(mask)
        if bb is None: return
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        m = mask[sl].astype(np.float32)
        if clip is not None: m = m * clip[sl]
        Tt = self.T[sl]
        A = m * alpha
        if edge:
            rim = smoothstep(0.0, 0.85, m) * (1 - smoothstep(0.85, 1.0, m))
            br = smoothstep(0.35, 0.75, Tt + m * 0.55 - 0.15)
            A = A * (1 - edge * rim * (1 - br))
        if dry:
            A = A * (1 - dry * (1 - smoothstep(0.25, 0.65, Tt + (1 - dry) * 0.5)))
        if grain:
            A = A * (1 - grain * 0.35 * smoothstep(0.18, 0.0, Tt))
        col = self._field_colour(colour, sl)
        Cs = self.C[sl]
        if opacity < 1:
            col = (1 - opacity) * np.clip(Cs * col / self.P, 0, 1) + opacity * col
        Cs += (col - Cs) * A[..., None]
        np.clip(Cs, 0, 1, out=Cs)
        self.F[sl] = np.minimum(1.4, self.F[sl] + A * 0.6)

    def model(self, mask, colours, light=LIGHT, lit=None, sigma=None, wrap=0.3, gamma=1.0, lo=0.0, hi=1.0,
              alpha=1.0, grain=0.25, edge=0.5, clip=None, mottle=0.06, seed=None):
        """a softly modelled, blended shape: a dome light (or `lit`) picks colours from a dark -> light ramp,
        mapped to the range lo..hi of the ramp, with a faint low-frequency mottle. Returns the light field."""
        if lit is None: lit = self.shading(mask, light, sigma, wrap)
        v = lo + (hi - lo) * np.clip(lit, 0, 1) ** gamma
        if mottle:
            bb = self._bbox(mask)
            if bb is not None:
                x0, y0, x1, y1 = bb
                nz = noise2d(y1 - y0, x1 - x0, 70, 3, int(self._r(seed).integers(1 << 30))) - 0.5
                v = v.copy(); v[y0:y1, x0:x1] += 2 * mottle * nz
        self.wash(mask, (colours, np.clip(v, 0, 1)), alpha, grain, edge, clip=clip)
        return lit

    def glaze(self, mask, colour, alpha=0.5, mode='multiply', soft=0.0):
        """a thin layer over what is there: 'multiply' (shadows), 'screen' (lights) or 'normal'"""
        m = blur(mask, soft) if soft else mask
        bb = self._bbox(m)
        if bb is None: return
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        A = m[sl] * alpha
        Cs = self.C[sl]
        col = hexc(colour)
        if mode == 'multiply': tgt = Cs * col
        elif mode == 'screen': tgt = 1 - (1 - Cs) * (1 - col)
        else: tgt = np.broadcast_to(col, Cs.shape)
        Cs += (tgt - Cs) * A[..., None]

    def dab(self, x, y, r, colour='white', alpha=0.95, soft=0.35, ry=None, rot=0.0):
        """a small soft round touch of opaque paint (catchlights, a button, a glint)"""
        ry = r if ry is None else ry
        x0, x1 = max(0, int(x - r - 3)), min(self.W, int(x + r + 4))
        y0, y1 = max(0, int(y - ry - 3)), min(self.H, int(y + ry + 4))
        if x1 <= x0 or y1 <= y0: return
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        dx, dy = self.XX[y0:y1, x0:x1] - x, self.YY[y0:y1, x0:x1] - y
        dd = np.sqrt(((dx * c + dy * s) / r) ** 2 + ((-dx * s + dy * c) / ry) ** 2)
        A = smoothstep(1.0, max(0.0, 1.0 - soft - 0.6 / max(r, 1.0)), dd) * alpha
        Cs = self.C[y0:y1, x0:x1]
        Cs += (hexc(colour) - Cs) * A[..., None]

    # ================================================================== smooth painted lines
    def _strands_mask(self, paths, widths, taper=(0.15, 0.5), ss=3):
        """anti-aliased coverage of tapered polylines -> (slice, crop)"""
        allp = np.concatenate([np.asarray(p, np.float32) for p in paths])
        pad = float(np.max(widths)) + 3
        x0, x1 = max(0, int(allp[:, 0].min() - pad)), min(self.W, int(allp[:, 0].max() + pad) + 1)
        y0, y1 = max(0, int(allp[:, 1].min() - pad)), min(self.H, int(allp[:, 1].max() + pad) + 1)
        if x1 <= x0 or y1 <= y0: return None, None
        bw, bh = x1 - x0, y1 - y0
        ss = max(1, min(ss, 4096 // max(bw, bh)))
        im = Image.new('L', (bw * ss, bh * ss), 0)
        d = ImageDraw.Draw(im)
        o = np.array([x0, y0], np.float32)
        for i, Q in enumerate(paths):
            q = (np.asarray(Q, np.float32) - o) * ss
            n = len(q)
            if n < 2:
                rr = widths[i] * ss / 2
                d.ellipse([q[0, 0] - rr, q[0, 1] - rr, q[0, 0] + rr, q[0, 1] + rr], fill=255); continue
            tt = np.linspace(0, 1, n)
            prof = 0.15 + 0.85 * np.clip(np.minimum(tt / max(taper[0], 1e-3), (1 - tt) / max(taper[1], 1e-3)), 0, 1)
            ww = np.maximum(1, np.round(widths[i] * ss * prof)).astype(int)
            ql = [tuple(p) for p in q.tolist()]
            a = 0
            while a < n - 1:
                b = a + 1
                while b < n - 1 and ww[b] == ww[a]: b += 1
                d.line(ql[a:b + 1], fill=255, width=int(ww[a]), joint='curve' if ww[a] > 2 else None)
                a = b
            if widths[i] * ss > 4:
                for kk in (0, n - 1):
                    rr = ww[kk] / 2
                    d.ellipse([q[kk, 0] - rr, q[kk, 1] - rr, q[kk, 0] + rr, q[kk, 1] + rr], fill=255)
        cov = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        return (slice(y0, y1), slice(x0, x1)), cov

    def line(self, path, width, colour, alpha=1.0, taper=(0.2, 0.35), smooth=True, dry=0.0, clip=None):
        """a smooth line painted with a small round brush, tapering in and out (lids, whiskers, a soft contour);
        dry > 0 lets it break up a little on the tooth"""
        self._need()
        Q = np.asarray(path, np.float32)
        if smooth and len(Q) > 2: Q = spline(Q, 8)
        sl, m = self._strands_mask([Q], [width], taper)
        if sl is None: return
        A = m * alpha
        if dry: A = A * smoothstep(0.15, 0.6, self.T[sl] + (1 - dry) * 0.55)
        if clip is not None: A = A * clip[sl]
        Cs = self.C[sl]
        Cs += (hexc(colour) - Cs) * A[..., None]

    def pencil(self, path, colour='pencil', width=1.8, alpha=0.7, pressure=0.62, seg=(40, 110), wobble=0.8,
               gaps=0.12, smooth=True, seed=None):
        """a faint graphite line: several overlapping sketchy strokes along a path, some left out"""
        r = self._r(seed)
        P = spline(path, 10) if (smooth and len(path) > 2) else np.asarray(path, np.float32)
        P = _resample(P, 2.0)
        if len(P) < 2: return 0
        paths = []
        i = 0
        while i < len(P) - 1:
            L = r.uniform(*seg) / 2.0
            j = min(len(P), int(i + L))
            q = P[i:j].copy()
            if len(q) >= 2:
                nn = np.array([-(q[-1, 1] - q[0, 1]), q[-1, 0] - q[0, 0]], np.float32)
                nn /= np.linalg.norm(nn) + 1e-6
                q += nn * (r.normal(0, wobble) + fbm1d(len(q), max(3, len(q) / 2), 2,
                                                         int(r.integers(1 << 30)))[:, None] * wobble * 0.6)
                if not (gaps and r.random() < gaps): paths.append(q)
            i = max(i + 1, int(j - r.uniform(0.1, 0.3) * L))
        if not paths: return 0
        return self.lines(paths, colour, width, pressure, 0.25, alpha, (0.35, 0.2), soft=0.6,
                          k=7, seed=int(r.integers(1 << 30)))

    # ================================================================== hair and fur
    def strands(self, region, flow, colours, n=800, length=(40, 140), width=(1.0, 2.0), curl=0.0, jitter=6.0,
                step=4.0, shade=None, spread=0.2, alpha=0.9, pressure=0.92, opacity=0.9, taper=(0.3, 0.05),
                clip=True, pad=5.0, roots=None, lock=None, k=9, seed=None):
        """many fine hairs: each starts inside `region` (or `roots`), follows `flow` (degrees: a number, a canvas
        field in radians or f(x, y) -> degrees) with its own jitter and steady bend (`curl` degrees per step),
        and is drawn as a fine pastel-pencil line, pressed at the root and lifting off at the tip. Each picks a
        colour from `colours` (dark -> light) by the 0..1 field `shade` plus noise; they are painted dark first,
        light last. lock=(strands per lock, lock width px) groups them into locks that share a root area, a
        wander, a curl and a shade, so hair reads as wavy locks rather than combed lines. clip=True keeps them
        within `pad` px of the region; False lets them fly loose."""
        r = self._r(seed)
        src = roots if roots is not None else region
        bb = self._bbox(src, 0.5)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        sub = src[y0:y1, x0:x1] > 0.5
        idx = np.flatnonzero(sub)
        if not len(idx): return 0
        if lock:
            per, lw_ = lock
            nl = max(1, int(n / per))
            pick = r.choice(idx, nl)
            ly = (pick // sub.shape[1] + y0).astype(np.float32)
            lx = (pick % sub.shape[1] + x0).astype(np.float32)
            g = r.integers(0, nl, n)
            y = ly[g] + r.normal(0, lw_ * 0.5, n).astype(np.float32)
            x = lx[g] + r.normal(0, lw_ * 0.5, n).astype(np.float32)
            jit = (r.normal(0, jitter, nl)[g] + r.normal(0, jitter * 0.25, n)).astype(np.float32)
            bend = ((r.normal(0, 1, nl) * curl)[g] + r.normal(0, curl * 0.15 + 1e-6, n)).astype(np.float32)
            lshade = r.normal(0, spread, nl)[g] + r.normal(0, spread * 0.3, n)
        else:
            pick = r.choice(idx, n)
            y = (pick // sub.shape[1] + y0).astype(np.float32) + r.random(n).astype(np.float32)
            x = (pick % sub.shape[1] + x0).astype(np.float32) + r.random(n).astype(np.float32)
            jit = r.normal(0, jitter, n).astype(np.float32)
            bend = (r.normal(0, 1, n) * curl).astype(np.float32)
            lshade = r.normal(0, spread, n)
        lens = r.uniform(*length, n).astype(np.float32)
        nsteps = max(2, int(lens.max() / step) + 1)
        Xs = np.zeros((n, nsteps + 1), np.float32); Ys = np.zeros((n, nsteps + 1), np.float32)
        Xs[:, 0], Ys[:, 0] = x, y
        for s_ in range(nsteps):
            if callable(flow): a = np.asarray(flow(Xs[:, s_], Ys[:, s_]), np.float32)
            elif np.ndim(flow) == 2: a = np.rad2deg(_lookup(flow, Xs[:, s_], Ys[:, s_]))
            else: a = np.full(n, float(flow), np.float32)
            a = np.deg2rad(a + jit + bend * s_)
            Xs[:, s_ + 1] = Xs[:, s_] + np.cos(a) * step
            Ys[:, s_ + 1] = Ys[:, s_] + np.sin(a) * step
        npts = np.clip((lens / step).astype(int) + 1, 2, nsteps + 1)
        nc = len(colours)
        base = _lookup(shade, x, y) if shade is not None else np.full(n, 0.5, np.float32)
        cls = np.clip(np.floor((base + lshade) * nc), 0, nc - 1).astype(int)
        o = np.argsort(cls, kind='stable')
        paths = [np.stack([Xs[i, :npts[i]], Ys[i, :npts[i]]], 1) for i in o]
        R = ramp(list(colours))
        cols = R[cls[o]]
        if clip is True:
            cm = smoothstep(0.03, 0.3, blur(region.astype(np.float32), pad))
        elif clip is False or clip is None:
            cm = None
        else:
            cm = clip
        return self.lines(paths, lambda xx, yy, c=cols: c, width, pressure, opacity, alpha, taper, streak=0.0,
                          soft=0.55, value=0.05, clip=cm, k=k, seed=int(r.integers(1 << 30)))

    def fur(self, region, field, colour, length=(14, 30), width=(1.2, 2.0), density=0.9, tuft=(5, 11), spread=0.3,
            curl=0.12, converge=1.0, pressure=0.85, opacity=0.85, alpha=0.75, taper=(0.7, 0.04), clip='auto',
            value=0.05, hue=0.02, k=7, avoid=None, fade='auto', side=0.14, light=LIGHT[:2], seed=None):
        """tufts of fine strokes following the lie of the fur. Each tuft: `tuft` strands whose roots spread
        across the clump and whose tips converge (converge 1) or fan out (-1), curling `curl` the same way,
        pressed at the root and lifting off at the tip; strands on the side of a tuft away from `light` are
        darker by `side`, so every lock has a lit and a shadowed flank. density ~ how often tufts tile the region."""
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
        L = self._sizes(length, cx, cy, r)
        cnt = r.integers(tuft[0], tuft[1] + 1, nt)
        cv = (curl * r.normal(1.0, 0.5, nt) * np.sign(r.normal(0, 1, nt) + 0.6)).astype(np.float32)
        L2 = np.asarray(light[:2], np.float32); L2 = L2 / (np.linalg.norm(L2) + 1e-6)
        tot = int(cnt.sum())
        tid = np.repeat(np.arange(nt), cnt)
        jj = np.concatenate([np.arange(c) for c in cnt])
        mm = cnt[tid].astype(np.float32)
        off = ((jj / np.maximum(mm - 1, 1) - 0.5) + r.normal(0, 0.12, tot)) * spread * L[tid]
        d = np.stack([np.cos(a), np.sin(a)], 1)[tid]
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        lj = L[tid] * r.uniform(0.7, 1.08, tot)
        base = np.stack([cx, cy], 1)[tid]
        root = base + nrm * off[:, None] - d * (r.uniform(0, 0.25, tot) * L[tid])[:, None]
        tip = base + d * L[tid][:, None]
        end = tip + nrm * (off * (1 - converge * 0.85))[:, None] + d * (lj - L[tid])[:, None] + \
            r.normal(0, 1, (tot, 2)) * (0.06 * L[tid])[:, None]
        ctrl = (root + end) / 2 + nrm * (cv[tid] * lj)[:, None] + r.normal(0, 1, (tot, 2)) * (0.03 * L[tid])[:, None]
        t = np.linspace(0, 1, k)[None, :, None]
        P = ((1 - t) ** 2 * root[:, None] + 2 * t * (1 - t) * ctrl[:, None] + t * t * end[:, None]).astype(np.float32)
        sgn = np.sign((nrm @ L2) + 1e-6)
        lat = sgn * off / np.maximum(1e-3, spread * L[tid])
        mid = P[:, k // 2]
        Wd = self._sizes(width, mid[:, 0], mid[:, 1], r)
        tc = self._colours(colour, cx, cy, r)
        cols = tc[tid] * (1 + 0.5 * value * r.normal(0, 1, tot).astype(np.float32))[:, None]
        cols *= (1 + value * r.normal(0, 1, nt).astype(np.float32))[tid][:, None]
        if side: cols *= (1 + side * 2 * np.clip(lat, -0.6, 0.6))[:, None]
        if hue: cols = hue_rotate(cols, (hue * r.normal(0, 1, tot)).astype(np.float32))
        cols = np.clip(cols, 0, 1).astype(np.float32)
        if isinstance(clip, str) and clip == 'auto': clip = None
        if avoid is not None:
            keep = 1 - np.clip(avoid, 0, 1)
            clip = keep if clip is None else clip * keep
        if isinstance(fade, str) and fade == 'auto':
            fade = blur(M, 3.0) ** 0.6 if arr else None
        pr = np.broadcast_to(np.asarray(pressure, np.float32), (tot,)) * r.uniform(0.9, 1.06, tot).astype(np.float32)
        al = np.broadcast_to(np.asarray(alpha, np.float32), (tot,)) * r.uniform(0.85, 1.0, tot).astype(np.float32)
        o = r.permutation(tot)
        self._draw(P[o], Wd[o], cols[o], al[o], pr[o], taper, opacity, clip, 2, r, fade=fade,
                   streak=np.zeros(tot, np.float32), soft=0.55)
        self.n_strokes += tot
        return tot

    def fluff(self, mask, length=(10, 30), n=None, width=(1.0, 1.8), out=0.7, field=None, alpha=0.8, lift=0.06,
              band=3.0, inset=5.0, curl=4.0, light=None, seed=None):
        """a soft, fluffy silhouette: short strands rooted just inside the edge of `mask`, leaning outward
        (`out` 0..1 blends the outward normal with `field`), each coloured from the paint just inside it (lifted a
        touch, more on the lit side), so the fur melts into whatever is behind instead of having an edge"""
        r = self._r(seed)
        b = blur(mask.astype(np.float32), band)
        rim = (smoothstep(0.35, 0.6, b) * smoothstep(0.98, 0.75, b))
        bb = self._bbox(rim, 0.3)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        sub = rim[y0:y1, x0:x1] > 0.3
        idx = np.flatnonzero(sub)
        if not len(idx): return 0
        if n is None: n = int(len(idx) / 6)
        pick = r.choice(idx, n)
        y = (pick // sub.shape[1] + y0).astype(np.float32) + r.random(n).astype(np.float32)
        x = (pick % sub.shape[1] + x0).astype(np.float32) + r.random(n).astype(np.float32)
        g = blur(mask.astype(np.float32), 6.0)
        gy, gx = np.gradient(g)
        ox, oy = -_lookup(gx, x, y), -_lookup(gy, x, y)
        on = np.sqrt(ox * ox + oy * oy) + 1e-6
        ox, oy = ox / on, oy / on
        if field is not None:
            fa = _lookup(self._field_rad(field), x, y)
            fx, fy = np.cos(fa), np.sin(fa)
            flip = (fx * ox + fy * oy) < 0
            fx[flip] *= -1; fy[flip] *= -1
            ox, oy = out * ox + (1 - out) * fx, out * oy + (1 - out) * fy
        ang = np.degrees(np.arctan2(oy, ox)).astype(np.float32)
        # colour from the paint a few px inside
        sx_ = np.clip(x - ox * inset, 0, self.W - 1).astype(int); sy_ = np.clip(y - oy * inset, 0, self.H - 1).astype(int)
        col = self.C[sy_, sx_].copy()
        lf = np.full((n, 1), lift, np.float32)
        if light is not None:                                    # strands pointing toward the light lift more
            L2 = np.asarray(light[:2], np.float32); L2 /= np.linalg.norm(L2)
            lf = lf * (1 + 1.5 * np.clip(ox * L2[0] + oy * L2[1], 0, 1))[:, None]
        col = np.clip(col * (1 + lf) + 0.02, 0, 1).astype(np.float32)
        lens = r.uniform(*length, n).astype(np.float32)
        k = 7
        paths = []
        for i in range(n):
            a0 = np.deg2rad(ang[i] + r.normal(0, 14)); cv = np.deg2rad(r.normal(0, curl))
            pts = [(x[i], y[i])]
            px_, py_ = x[i], y[i]
            st = lens[i] / (k - 1)
            for j in range(k - 1):
                px_ += np.cos(a0 + cv * j) * st; py_ += np.sin(a0 + cv * j) * st
                pts.append((px_, py_))
            paths.append(np.array(pts, np.float32))
        return self.lines(paths, lambda xx, yy, c=col: c, width, 0.9, 0.9, alpha, (0.6, 0.0), soft=0.55,
                          value=0.03, k=k, seed=int(r.integers(1 << 30)))

    # ================================================================== faces
    def eye(self, cx, cy, rx, ry=None, iris='iris', iris_light='iris_light', iris_r=0.62, look=(0.0, 0.0), lid=0.12,
            lid_skin='skin_light', line_colour='lid', line_w=None, flick=0.35, lashes=3, crease=0.35, lower=0.35,
            white='eye_white', shade='eye_shade', catch=(-0.36, -0.40), rot=0.0, side=1, clip=None):
        """a big round picture-book eye: an off-white ball shaded grey-blue under the lid, a dark iris (lighter in
        the lower half, darker at the rim) with a pupil, the upper lid coming down `lid` of the ball with a soft
        dark lid line that flicks out at the outer corner (`side` +1 = outer corner to the right), a faint crease
        and lower lid, a few lashes and two white catchlights. look = (dx, dy) in -1..1 moves the iris."""
        self._need()
        ry = rx if ry is None else ry
        a = np.deg2rad(rot); ca, sa = np.cos(a), np.sin(a)
        to = lambda u, v: (cx + u * ca - v * sa, cy + u * sa + v * ca)
        ball = self.ellipse(cx, cy, rx, ry, rot)
        if clip is not None: ball = ball * clip
        bb = self._bbox(ball, pad=4)
        if bb is None: return ball
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        X, Y = self.XX[sl], self.YY[sl]
        U = (X - cx) * ca + (Y - cy) * sa; V = -(X - cx) * sa + (Y - cy) * ca
        q = np.clip((V + ry) / (2 * ry), 0, 1)
        sideshade = np.clip(np.abs(U) / rx, 0, 1) ** 3
        wf = hexc(white) + (hexc(shade) - hexc(white)) * (0.85 * (1 - smoothstep(0.05, 0.62, q)) + 0.35 * sideshade)[..., None]
        Cs = self.C[sl]
        A = ball[sl][..., None]
        Cs += (wf - Cs) * A
        # iris and pupil
        ir = iris_r * min(rx, ry)
        iu, iv = look[0] * (rx - ir * 0.9), look[1] * (ry - ir * 0.9)
        ix, iy = to(iu, iv)
        dd = np.sqrt((X - ix) ** 2 + (Y - iy) ** 2) / ir
        im = np.clip((1 - dd) * ir + 0.5, 0, 1) * ball[sl]
        ic, il = hexc(iris), hexc(iris_light)
        qq = np.clip((Y - (iy - ir)) / (2 * ir), 0, 1)
        th = np.arctan2(Y - iy, X - ix)
        rad = 0.5 + 0.5 * np.sin(th * 23 + 1.3) * np.sin(th * 9 + 0.4)
        f = ic + (il - ic) * (smoothstep(0.35, 1.0, qq) * smoothstep(0.98, 0.45, dd) * (0.75 + 0.25 * rad))[..., None]
        f = f * (1 - 0.45 * smoothstep(0.72, 1.0, dd))[..., None]
        Cs += (f - Cs) * im[..., None]
        pm = np.clip((1 - dd / 0.5) * ir * 0.5 + 0.5, 0, 1) * ball[sl]
        Cs += (hexc('pupil') - Cs) * (pm * 0.96)[..., None]
        # the lid's shadow on the ball, then the lid itself
        ytop = -ry + 2 * ry * lid
        arc = ytop + ry * 0.22 * (U / rx) ** 2
        shadow = ball[sl] * smoothstep(arc + ry * 0.55, arc, V)
        Cs *= (1 - 0.32 * shadow[..., None] * (1 - hexc('#6d6c8a')))
        if lid > 0:
            lm = ball[sl] * smoothstep(arc + 1.0, arc - 1.0, V)
            Cs += (hexc(lid_skin) - Cs) * lm[..., None]
        # catchlights
        if catch is not None:
            self.dab(ix + catch[0] * ir, iy + catch[1] * ir, max(1.5, ir * 0.26), 'white', 0.97, soft=0.25)
            self.dab(ix - catch[0] * ir * 0.55, iy - catch[1] * ir * 0.75, max(0.9, ir * 0.1), 'white', 0.8, soft=0.3)
        # lid line with a flick at the outer corner
        lw = max(1.6, ry * 0.16) if line_w is None else line_w
        us = np.linspace(-1.05, 1.05, 30)
        vs = ytop + ry * 0.22 * us ** 2
        vs = np.minimum(vs, ry * np.sqrt(np.clip(1 - (us / 1.08) ** 2, 0, 1)))
        pts = [to(u * rx, v - lw * 0.15) for u, v in zip(us, vs)]
        if flick:
            u_end = 1.05 * side
            v_end = ytop + ry * 0.22
            pts_f = [to(u_end * rx + side * rx * flick * t, v_end - ry * flick * 0.45 * t * t) for t in (0.4, 0.8, 1.0)]
            pts = (pts + pts_f) if side > 0 else (pts_f[::-1] + pts)
        self.line(pts, lw, line_colour, 0.92, taper=(0.18, 0.12) if side > 0 else (0.12, 0.18))
        # crease and lower lid (faint, warm)
        if crease:
            cp = [to(u * rx * 1.02, -ry * 1.18 + ry * 0.28 * u * u + ytop * 0.3) for u in np.linspace(-0.8, 0.9, 16)]
            self.line(cp, max(1.0, lw * 0.4), 'crease', crease, taper=(0.5, 0.5), dry=0.3)
        if lower:
            lp = [to(np.cos(t) * rx * 1.03, np.sin(t) * ry * 1.06) for t in np.linspace(0.2 * np.pi, 0.8 * np.pi, 18)]
            self.line(lp, max(1.0, lw * 0.35), 'crease', lower, taper=(0.5, 0.5), dry=0.4)
        for kk in range(lashes):
            t = 0.55 + 0.45 * kk / max(1, lashes - 1)
            u0 = side * (t * 1.0)
            v0 = ytop + ry * 0.22 * u0 * u0
            p0 = to(u0 * rx, v0)
            p1 = to(u0 * rx + side * rx * 0.2, v0 - ry * 0.22)
            p2 = to(u0 * rx + side * rx * 0.34, v0 - ry * 0.26)
            self.line([p0, p1, p2], max(1.0, lw * 0.32), line_colour, 0.85, taper=(0.1, 0.9))
        return ball

    def brow(self, path, width=6.0, colour='brow', alpha=0.85, hairs=24, seed=None):
        """an eyebrow: a soft tapered band (the pastel rubbed in) plus a few fine hairs along it"""
        r = self._r(seed)
        P = spline(np.asarray(path, np.float32), 8)
        self.line(P, width * 1.25, colour, alpha * 0.35, taper=(0.4, 0.6), dry=0.1)
        self.line(P, width * 0.7, colour, alpha * 0.55, taper=(0.3, 0.6), dry=0.25)
        if hairs:
            d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
            paths = []
            for _ in range(hairs):
                i = int(r.integers(0, len(P) - 1))
                t = i / (len(P) - 1)
                w = width * (0.5 + 0.5 * np.sin(np.pi * min(1, t * 1.4)))
                p = P[i] + np.array([-d[i, 1], d[i, 0]]) * r.normal(0, w * 0.25)
                L = r.uniform(width * 1.1, width * 2.4)
                dd = d[i] * np.cos(0.35) + np.array([d[i, 1], -d[i, 0]]) * np.sin(0.35)
                paths.append(np.array([p, p + dd * L * 0.5, p + dd * L], np.float32))
            self.lines(paths, colour, (0.9, 1.4), 0.85, 0.9, alpha * 0.45, (0.5, 0.0), k=3, seed=int(r.integers(1 << 30)))

    def blush(self, cx, cy, rx, ry=None, colour='blush', strength=0.55, solid=0.25, grain=0.5, clip=None):
        """a big round rosy cheek: strongest in the middle, softening to nothing, powdery toward the rim where
        only the tooth takes the pastel"""
        self._need()
        ry = rx * 0.85 if ry is None else ry
        x0, x1 = max(0, int(cx - rx - 2)), min(self.W, int(cx + rx + 3))
        y0, y1 = max(0, int(cy - ry - 2)), min(self.H, int(cy + ry + 3))
        if x1 <= x0 or y1 <= y0: return
        sl = (slice(y0, y1), slice(x0, x1))
        d = np.sqrt(((self.XX[sl] - cx) / rx) ** 2 + ((self.YY[sl] - cy) / ry) ** 2)
        a = smoothstep(1.0, solid, d) ** 1.3
        a = a * (1 - grain * (1 - a) * (1 - smoothstep(0.2, 0.7, self.T[sl])))
        if clip is not None: a = a * clip[sl]
        Cs = self.C[sl]
        Cs += (hexc(colour) - Cs) * (a * strength)[..., None]

    def nose(self, x, y, size=16.0, side=1, tip='nose', shadow='skin_deep', bridge=None, alpha=1.0, shade=0.28):
        """a small whimsical nose: a soft shadow on the side away from the light (`side` +1 = shadow to the
        right; `shade` its strength), a little nostril mark, a red-tipped ball and a soft highlight. (x, y) is the
        tip."""
        s = size
        # bridge shadow: a soft curve coming down to the tip
        if bridge is None: bridge = s * 3.2
        P = [(x + side * s * 0.3, y - bridge), (x + side * s * 0.55, y - bridge * 0.45), (x + side * s * 0.75, y - s * 0.2),
             (x + side * s * 0.3, y + s * 0.62)]
        m = self.tube(P, [s * 0.3, s * 0.5, s * 0.6, s * 0.4])
        self.glaze(blur(m, s * 0.25), shadow, shade * alpha, 'multiply')
        # the red tip
        self.blush(x, y, s * 1.15, s * 0.95, tip, 0.62 * alpha, solid=0.15, grain=0.3)
        self.blush(x + side * s * 0.15, y + s * 0.15, s * 0.6, s * 0.5, tip, 0.35 * alpha, solid=0.1, grain=0.2)
        # nostril and the underside line
        self.line([(x - side * s * 0.15, y + s * 0.62), (x + side * s * 0.25, y + s * 0.7), (x + side * s * 0.62, y + s * 0.45)],
                  max(1.2, s * 0.13), '#9c4b43', 0.55 * alpha, taper=(0.4, 0.3))
        self.dab(x - side * s * 0.25, y - s * 0.28, max(1.2, s * 0.22), '#fff4ee', 0.6 * alpha, soft=0.8)

    def mouth(self, x, y, w=30.0, smile=0.2, colour='lip', dark='lip_dark', alpha=1.0):
        """small whimsical lips: a soft upper lip, a fuller lower lip, a darker parting line turned up at the ends"""
        h = w * 0.32
        up = [(x - w * 0.5, y - smile * h), (x - w * 0.2, y - h * 0.55), (x, y - h * 0.38), (x + w * 0.2, y - h * 0.55),
              (x + w * 0.5, y - smile * h), (x, y + 0.05 * h)]
        lo = [(x - w * 0.45, y - smile * h * 0.6), (x - w * 0.15, y + h * 0.15), (x + w * 0.15, y + h * 0.15),
              (x + w * 0.45, y - smile * h * 0.6), (x + w * 0.2, y + h * 0.75), (x - w * 0.2, y + h * 0.75)]
        mu = self.poly(up, smooth=True); ml = self.poly(lo, smooth=True)
        self.wash(blur(mu, 0.8), mix(colour, dark, 0.25), 0.85 * alpha, grain=0.1, edge=0.2)
        self.wash(blur(ml, 0.8), colour, 0.8 * alpha, grain=0.1, edge=0.2)
        self.dab(x + w * 0.05, y + h * 0.42, w * 0.13, '#fbd3c6', 0.45 * alpha, ry=h * 0.14, soft=0.8)
        self.line([(x - w * 0.52, y - smile * h * 1.3), (x - w * 0.2, y + h * 0.05), (x, y + h * 0.1),
                   (x + w * 0.2, y + h * 0.05), (x + w * 0.52, y - smile * h * 1.3)], max(1.2, w * 0.05), dark,
                  0.75 * alpha, taper=(0.4, 0.4))

    # ================================================================== plants
    def leaf(self, base, tip, width, colours='eucalyptus', bend=0.12, light=LIGHT, alpha=1.0, rib=True, seed=None):
        """one leaf from base to tip: a pointed oval, lighter on the side toward the light, darker toward its
        base, with a pale midrib and a few dry strokes along it"""
        r = self._r(seed)
        b, t = np.asarray(base, np.float32), np.asarray(tip, np.float32)
        d = t - b; L = float(np.linalg.norm(d)) + 1e-6; d /= L
        nrm = np.array([-d[1], d[0]], np.float32)
        s = np.linspace(0, 1, 18)
        mid = b[None] + d[None] * (s * L)[:, None] + nrm[None] * (bend * L * 4 * s * (1 - s))[:, None]
        half = width * 0.5 * np.sin(np.pi * s) ** 0.75 * (1 - 0.25 * s)
        pts = np.vstack([mid + nrm * half[:, None], (mid - nrm * half[:, None])[::-1]])
        m = self.poly(pts)
        if m.max() < 0.05: return m
        L2 = np.asarray(light[:2], np.float32)
        lit_side = 1.0 if float(nrm @ L2) < 0 else -1.0
        bb = self._bbox(m, pad=2)
        x0, y0, x1, y1 = bb
        X, Y = self.XX[y0:y1, x0:x1], self.YY[y0:y1, x0:x1]
        along = np.clip(((X - b[0]) * d[0] + (Y - b[1]) * d[1]) / L, 0, 1)
        across = ((X - b[0]) * nrm[0] + (Y - b[1]) * nrm[1]) * lit_side / (width * 0.5)
        v = np.zeros((self.H, self.W), np.float32)
        v[y0:y1, x0:x1] = np.clip(0.45 + 0.35 * np.tanh(across * 2) + 0.15 * along + 0.05 * r.normal(), 0, 1)
        self.wash(m, (colours, v), alpha, grain=0.35, edge=0.8)
        self.strokes(m, np.degrees(np.arctan2(d[1], d[0])) + 25 * lit_side, (colours, v), (L * 0.25, L * 0.5),
                     (width * 0.12, width * 0.22), 0.6, pressure=0.6, opacity=0.8, alpha=0.5 * alpha, streak=0.5,
                     passes=1, seed=int(r.integers(1 << 30)))
        if rib:
            self.line(mid[2:-2], max(1.0, width * 0.05), mix(ramp(colours)[-1], 'white', 0.3), 0.45 * alpha,
                      taper=(0.2, 0.6), dry=0.4)
        return m

    def sprig(self, path, n=9, size=(40, 70), colours=('eucalyptus', 'eucalyptus'), stem='stem', width=4.0,
              round_=0.62, spread=48.0, fade=None, seed=None):
        """a stem along `path` (base first) with `n` leaves in loose opposite pairs, smaller toward the tip;
        colours is a ramp per leaf (picked in turn); fade(y) -> 0..1 dims leaves toward a dissolving end"""
        r = self._r(seed)
        P = spline(np.asarray(path, np.float32), 10)
        self.lines([P], stem, (width, width), 0.85, 0.85, 0.85, (0.3, 0.1), soft=0.6, k=min(15, len(P)),
                   seed=int(r.integers(1 << 30)))
        cum = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        out = []
        for i in range(n):
            t = 0.12 + 0.86 * (i + 0.5 * (i % 2) + r.uniform(-0.3, 0.3)) / max(1, n)
            t = float(np.clip(t, 0.05, 0.98))
            j = int(np.searchsorted(cum, t * cum[-1]))
            j = min(max(j, 1), len(P) - 2)
            p = P[j]; tg = P[j + 1] - P[j - 1]; tg /= np.linalg.norm(tg) + 1e-6
            sgn = 1 if i % 2 == 0 else -1
            ang = np.arctan2(tg[1], tg[0]) + sgn * np.deg2rad(spread + r.normal(0, 14))
            Ls = r.uniform(*size) * (1 - 0.45 * t)
            tip = p + np.array([np.cos(ang), np.sin(ang)]) * Ls
            al = 1.0 if fade is None else float(fade(p[1]))
            cl = colours[i % len(colours)]
            self.leaf(p, tip, Ls * round_, cl, bend=0.1 * sgn, alpha=al, seed=int(r.integers(1 << 30)))
            out.append((p, tip))
        return out

    # ================================================================== finish and output
    def finish(self, soft=0.25, grain=1.0, warmth=0.3):
        """record the finishing (applied in render, so every stage snapshot matches the final look)"""
        self.fin = dict(soft=soft, grain=grain, warmth=warmth)
        return self

    def render(self):
        out = self.C
        f = self.fin
        if f:
            if f['soft']:
                b = np.stack([blur(out[..., c], 0.7) for c in range(3)], -1)
                out = out * (1 - f['soft']) + b * f['soft']
            if f['warmth']:
                lum = out.mean(-1, keepdims=True)
                ink = 1 - smoothstep(0.9, 0.99, lum)                  # the bare paper stays as it is
                out = out * (1 + f['warmth'] * ink * np.array([0.012, 0.002, -0.016], np.float32))
            if f['grain']:
                if not hasattr(self, '_grain'):
                    r = np.random.default_rng(self.seed + 7)
                    g = r.normal(0, 1, (self.H, self.W)).astype(np.float32)
                    self._grain = (0.008 * (0.7 * g + 0.3 * blur(g, 0.8) * 2.0)).astype(np.float32)
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
