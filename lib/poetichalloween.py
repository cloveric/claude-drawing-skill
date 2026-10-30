"""poetichalloween — 诗意万圣夜 / Poetic Halloween: melancholic, surreal picture-book portraits for an autumn night
(numpy + Pillow only).

The look: a quiet, slightly unsettling picture-book portrait for autumn and Halloween, painted in opaque gouache
and fine coloured-pencil hatching on a dark toned board and then printed. Pale porcelain faces with a strong red
flush on the nose, the cheeks, the eyelids and round the eyes (red-rimmed lower lids), heavy half-closed sad eyes
and a small unsmiling mouth, the volumes very simplified. Hair is one solid sculpted mass -- a blunt jet-black (or
silver-white) bob with a dead-straight fringe, almost no visible strands, a soft sheen. Clothes are tactile
textiles painted in: coarse burlap and felt hats, chunky wool scarves and mittens, tartan coats. The grounds are
dark and moody (night indigo with stars, dense dark foliage), and every picture has ONE luminous accent: little
sheet-ghosts with glowing eyes and glowing fringe tips whose warm light picks out the leaves, the wool and the
underside of a face. Fine painterly grain over everything, like a print with a tooth. Poetic, never gory.

Physical model
  board       A dark toned board with a fine tooth `T`, rank-equalised to a uniform 0..1 so that "the paint reaches
              where tooth > 1 - pressure" turns pressure straight into coverage; the same tooth is pre-averaged along
              8 directions (`TD`, uint8) so a dry stroke skips the pits in short streaks along itself; a separate
              single-pixel stipple `ST` (uint8) is kept for the speckled flush. A pigment buffer `F` records how much
              paint already sits in the tooth (later layers reach a little deeper).
  strokes     Opaque gouache strokes and fine pencil hatching are short centrelines integrated through an
              orientation field (angles mod pi) with a slight wrist arc. Tens of thousands go at once: Pillow draws
              every *segment* of every stroke with its own id into a 2x supersampled integer map; numpy looks each
              covered sub-pixel up to its segment, recovers the position along the stroke (a pressure profile with
              rounded ends) and across it (soft sides, bristle lanes that open as the stroke runs dry), lays pigment
              where the pressure reaches the direction-matched tooth and sums back with bincount. A stroke can take
              its colour from the canvas under its centre (`colour='canvas'`): a painterly repaint of a computed
              base (a tartan, a modelled face) that keeps the colour but adds the hand. Big batches are split into
              bands of rows (`band_px` sub-pixels each) to keep the memory down.
  pigment     Opaque paint: new = old + A x (target - old), target = (1 - opacity) x old x colour + opacity x colour
              (the white-referenced multiply, so it also works on a dark board).
  layers      `wash()` a smooth opaque coat (colour may be a ramp looked up by a field), with the deepest pits of the
              tooth left a touch lighter and an edge that breaks into the tooth (computed in bands of rows, so a
              canvas-wide coat makes no canvas-wide RGB temporaries); `model()` lays a soft dome light on a shape and
              washes a dark -> light ramp over it -- the simplified volumes of the faces. `soften()` blurs a mask only
              round its shape.
  hair        A bob is a solid mass: modelled with a near-black -> slate ramp, then `sheen()` streaks a soft
              anisotropic highlight band along the flow (long thin strokes where a dome light sits in a narrow band),
              and only a few low-contrast `strands()` show the lie of the hair; the blunt cut is the mask's edge plus
              a few fine tips.
  faces       `eye()` a heavy-lidded sad eye: an almond of off-white ball shaded grey under a thick lid that covers
              about half of the iris and droops at the outer corner, a dark lid line, a red wet rim along the lower
              lid, a small catchlight and, optionally, the warm glint of a light below mirrored low in the iris.
              `flush()` lays the red flush as a smooth glaze plus a fine stipple of single specks, denser where the
              flush is stronger (the speckled red flush); `spot()` and `ring()` make the soft fields it takes.
              `nose()` a long simplified nose that is its own small volume -- lit, a mauve shadow side, a small cast
              shadow -- reddening to a red tip; `mouth()` small, closed, unsmiling lips.
  textiles    `burlap()` a plain weave of coarse slubby threads (each row and column its own thickness, lumps along
              it, over-under alternation, dark holes between), lit as a height field and multiplied onto the paint,
              plus loose fibres and a fuzzy edge; it can follow a curve (`coords`, e.g. from `along()`); `knit()`
              stockinette V stitches (rows can follow a path: a scarf) and `rib()` ribbing, lit the same way;
              `tartan()` a symmetric sett woven 2/2 twill (warp or weft shows by a diagonal rule, each thread
              rounded), over a light field and a fold warp; `fuzz()` fibres growing out of a silhouette, coloured from
              the paint just inside it.
  foliage     `leaf()` a broad palmate, double-serrated (currant / maple-like) leaf, foreshortened at random: each
              lobe folded along its midrib (one half lighter), veins, a mottle, a soft shadow cast down and to the
              right on what is behind (the depth of a hedge), optionally lit by the light map; `foliage()` scatters
              hundreds back to front, the far ones smaller and darker.
  light       `light()` registers warm point lights (falloff 1 / (1 + (d / r)^2)^2) summed into a light map;
              `illuminate()` lights painted surfaces by it: C <- 1 - (1 - C) exp(-L x receptivity x (base + albedo C)),
              so pale wool and porcelain warm up strongly, dark leaves turn olive-orange near a ghost and black hair
              barely changes. `emit()` writes into an emission buffer that `render()` blooms (three blurs, screened).
  ghosts      `ghost()` a small sheet-ghost: a translucent dome-and-bell body made of hundreds of fine silver strands
              that fall from the crown like hair to a fringe of locks, two glowing eyes (cream core, amber ring, halo),
              a warm glowing bead at the end of every lock, a hem lit warm and a faint halo round the whole sheet.
  sky         `stars()` pinpricks with a few larger ones and a faint halo.
  finish      `finish()` records a slight softness, the bloom, a fine print grain with a coarser tooth that shows in
              the darks (a risograph-like grain), and lifted blacks -- applied in render (in bands of rows; the grain
              is made in `ground()` while memory is low), so every stage snapshot matches the final look.

API (canvas pixel coordinates; a number given as a field is a direction in degrees, 0 = to the right, 90 = down;
     field arrays are radians; colours are PAINTS names, '#rrggbb' or RGB triples; ramps are RAMPS names or lists,
     dark -> light)
  surface    PoeticHalloween(W, H, seed, keep_stages, stages_dir); ground(tone, tooth); finish(soft, grain, tooth,
             bloom, lift)
  masks      poly(pts, smooth) / ellipse(cx, cy, rx, ry, rot) / blob(cx, cy, rx, ry, rough) / tube(path, w0, w1) /
             rect(x0, y0, x1, y1) / below(xs, ys) -> canvas-sized float masks; spot(cx, cy, rx, ry, rot, solid) /
             ring(cx, cy, rx, ry, width, rot) soft fields; soften(mask, sigma) a blur done only round the shape
  fields     flow(angle, turb, scale); field(f(x, y) -> degrees) -- or pass f itself, evaluated only where it is
             needed; radial(cx, cy, offset); contour(mask, sigma,
             offset, fallback); blend(f1, f2, w); rotate(field, deg); value(top, bottom, y0, y1); shading(mask, light,
             sigma, wrap)
  strokes    strokes(region, field, colour, length, width, density, pressure, opacity, alpha, streak, soft, taper,
             passes, clip, avoid, fade); lines(paths, colour, width, ...); sketch(path, colour, width, alpha)
  layers     wash(mask, colour, alpha, grain, edge, dry, clip, opacity); model(mask, colours, light, lit, sigma,
             wrap, gamma, lo, hi); glaze(mask, colour, alpha, mode, soft); dab(x, y, r, colour, alpha, soft, ry,
             rot); line(path, width, colour, alpha, taper, dry, clip)
  hair       strands(region, flow, colours, n, length, width, curl, jitter, shade, alpha, clip, roots, lock);
             sheen(mask, flow, lit, band, colour, alpha, strokes)
  faces      eye(cx, cy, rx, ry, iris, look, lid, lower, droop, fold, rim, reflect, rot, side, clip); flush(field,
             colour, strength, speckle, clip); nose(path, width, tip_r, side, shade, tip, tip_strength, clip);
             mouth(x, y, w, droop, colour, rot)
  textiles   burlap(mask, angle, period, coords, holes, slub, rust, fibres, fuzz); knit(mask, stitch, angle, path,
             origin, curve); rib(mask, path, period); tartan(mask, sett, scale, angle, coords, lit, lo, hi);
             fuzz(mask, length, n, width, out); along(path, mask) -> (S, T) coordinates that bend with a tube
  foliage    leaf(x, y, size, angle, colours, value, fold, lit, veins, squash, shadow); foliage(region, n, size,
             colours, value, angle, fold, lit, veins, squash, shadow)
  light      light(x, y, r, colour, power, squash, fall); lightmap(); illuminate(receptivity, gain, base, albedo);
             emit(x, y, r, power, ry)
  ghosts     ghost(cx, top, w, h, look, tips, strands, glow, lean, eye_r, body_alpha, sheet, clip)
  sky        stars(region, n, size, bright, warm)
  output     render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 88, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from poetichalloween import PoeticHalloween
    p = PoeticHalloween(1920, 1080, seed=3); p.finish(); p.ground()
    p.wash(p.rect(0, 0, 1920, 1080), ('night', p.value(0.2, 0.7)))
    face = p.ellipse(960, 520, 130, 160)
    p.model(face, 'porcelain')
    p.flush(p.ring(910, 500, 40, 26, 22) + p.spot(960, 560, 30, 40), 'flush', 0.7)
    p.eye(905, 500, 34, 22, look=(0, 0.4), lid=0.52, side=-1); p.eye(1015, 500, 34, 22, look=(0, 0.4), lid=0.52)
    p.light(1300, 760, 260, 'glow', 1.2); p.illuminate(1.0)
    p.ghost(1300, 640, 110, 150)
    p.save('halloween.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, blob_pts

PAINTS = {
    # the board, chalk underdrawing
    'board': '#14131c', 'chalk': '#cfc6b4', 'chalk_warm': '#d9b78c',
    # night sky and stars
    'night_deep': '#0b0f24', 'night': '#141a38', 'indigo': '#1c2349', 'dusk': '#2a2c58', 'haze': '#3b3f6e',
    'star': '#eef0ff', 'warmstar': '#ffe7c6',
    # porcelain skin and the red flush
    'porcelain': '#f1e8e2', 'porcelain_light': '#fbf7f3', 'porcelain_shade': '#cdbdbd', 'porcelain_deep': '#9f8b93',
    'flush': '#d8443b', 'flush_light': '#e8735e', 'flush_deep': '#b02f2e', 'rim': '#c23b36', 'lip': '#c45a54',
    'lip_dark': '#7e2d2e', 'lid_line': '#3a1d1f', 'crease': '#a5585a',
    # eyes
    'eye_white': '#e9e5e1', 'eye_shade': '#9a9db0', 'iris': '#2b2427', 'iris_light': '#6d5a50', 'pupil': '#0d0a0c',
    # hair
    'jet': '#0a090f', 'hair_black': '#111019', 'hair_dark': '#1a1b27', 'hair': '#262b3d', 'hair_sheen': '#4d5876',
    'hair_shine': '#7d88a6', 'silver': '#c9ccd6', 'silver_light': '#eceef3',
    # textiles
    'burlap_dark': '#1d1816', 'burlap': '#2e2622', 'burlap_light': '#4b3e35', 'burlap_hi': '#6e5c4d',
    'burlap_rust': '#6a3a22', 'oxblood_deep': '#3a0c10', 'oxblood_dark': '#5c1418', 'oxblood': '#7d1d21',
    'oxblood_light': '#a03230', 'oxblood_pale': '#c4584a', 'navy': '#141b31', 'bottle': '#1b2b24', 'tar': '#0c0d12',
    'rust': '#8a3b22', 'ochre': '#a47a34', 'mustard': '#c2953c',
    # foliage
    'leaf_black': '#0b120f', 'leaf_deep': '#13201a', 'leaf': '#1e3023', 'leaf_olive': '#35432a', 'leaf_moss': '#4f5a33',
    'leaf_maroon': '#3a171a', 'leaf_rust': '#6b2c18', 'leaf_orange': '#b4501f',
    # ghosts and their glow
    'ghost_dark': '#4a5167', 'ghost': '#8c95ab', 'ghost_light': '#c6ccd9', 'ghost_white': '#eef0f5',
    'glow': '#ffb04a', 'glow_core': '#fff2d2', 'glow_ring': '#e08a2e', 'ember': '#ff8a2c',
}
RAMPS = {                                   # dark -> light
    'night': ('#090c1f', '#0f1430', '#161c3c', '#1f2548', '#2c2f5a'),
    'porcelain': ('#a8949a', '#cbbbbb', '#e3d8d4', '#f2ebe6', '#fcf9f6'),
    'hair': ('#07070b', '#0d0d14', '#15161f', '#20243a', '#3a4462'),
    'silver': ('#7f8596', '#a3a8b6', '#c4c8d2', '#dfe2e9', '#f5f6f9'),
    'burlap': ('#151110', '#231d1a', '#342b26', '#4a3d34', '#65544a'),
    'oxblood': ('#24070a', '#3e0d12', '#5c161a', '#7a2124', '#983630'),
    'leaf': ('#070c0a', '#0d1712', '#15231a', '#203121', '#34442a'),
    'leaf_olive': ('#0e120b', '#1a2214', '#29331c', '#3d4726', '#56603a'),
    'leaf_maroon': ('#12080a', '#230e10', '#381618', '#4f2020', '#6a2d24'),
    'leaf_rust': ('#1e0c07', '#3a170c', '#5c2412', '#83361a', '#a84d24'),
    'ghost': ('#3b4157', '#5f677f', '#8a93a9', '#b8bfcd', '#e9ecf2'),
    'glow': ('#7a2e0c', '#c4561a', '#f08a2e', '#ffbf5c', '#fff1cc'),
}
LIGHT = (-0.5, -0.62, 0.6)                  # upper left, a little in front (cool night light)
GLOW = (1.0, 0.68, 0.32)                    # the ghosts' warm light (amber), as an RGB triple


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


def _wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


def _maple(size, angle, r, lobes=5):
    """outline of a broad palmate, double-serrated leaf (currant / maple: shallow sinuses, wide lobes), polar round
    the point where the veins meet, main lobe toward `angle` degrees; returns (points (N, 2) relative to that
    point, lobe tips (k, 2))"""
    if lobes >= 5:
        spec = [(-118, 0.52, 0.36), (-60, 0.84, 0.4), (0, 1.0, 0.4), (60, 0.84, 0.4), (118, 0.52, 0.36)]
        sinus = [0.42, 0.56, 0.56, 0.42]
    else:
        spec = [(-62, 0.8, 0.46), (0, 1.0, 0.44), (62, 0.8, 0.46)]
        sinus = [0.55, 0.55]
    pts = [(np.pi, 0.2)]
    tips = []
    for i, (a, L, w) in enumerate(spec):
        a = np.deg2rad(a + r.normal(0, 5)); L = L * r.uniform(0.9, 1.08); w = w * r.uniform(0.88, 1.12)
        lobe = [(a - w, 0.62 * L), (a - 0.62 * w, 0.8 * L), (a - 0.28 * w, 0.94 * L), (a, L), (a + 0.28 * w, 0.94 * L),
                (a + 0.62 * w, 0.8 * L), (a + w, 0.62 * L)]
        pts += lobe
        tips.append((a, L))
        if i < len(sinus):
            an = np.deg2rad((spec[i][0] + spec[i + 1][0]) / 2 + r.normal(0, 3))
            pts.append((an, sinus[i] * r.uniform(0.92, 1.08)))
    pts.append((np.pi, 0.2))
    P = np.array(pts, np.float32)
    # densify in polar coordinates, then serrate: teeth along the lobes, every third one bigger (double-serrate)
    th = np.unwrap(P[:, 0]); rr = P[:, 1]
    k = 5
    t = np.linspace(0, len(P) - 1, (len(P) - 1) * k + 1)
    th2 = np.interp(t, np.arange(len(P)), th); r2 = np.interp(t, np.arange(len(P)), rr)
    j = np.arange(len(t))
    tooth = np.where(j % 2 == 0, 1.0, -0.5) * np.where(j % 6 == 0, 0.06, 0.032) * smoothstep(0.45, 0.66, r2)
    r2 = (r2 + tooth) * size
    a0 = np.deg2rad(angle)
    out = np.stack([np.cos(th2 + a0) * r2, np.sin(th2 + a0) * r2], 1)
    tp = np.array([(np.cos(a + a0) * L * size, np.sin(a + a0) * L * size) for a, L in tips], np.float32)
    return out.astype(np.float32), tp


class PoeticHalloween:
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
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = hexc('board')
        self.F = np.zeros((H, W), np.float32)             # pigment already sitting in the tooth
        self.E = np.zeros((H, W), np.float32)             # emission (what glows), bloomed in render
        self._bloom = None                                 # cached bloom of E
        self.T = None; self.TD = None; self.EN = None; self.ST = None
        self.lights, self._L = [], None
        self.fin = None
        self.floor = 0.24                                  # pigment a brush still leaves in the pits of the tooth
        self.band_px = 0.8e6                               # sub-pixels per raster band (memory vs. speed)
        self.n_strokes = 0

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== board
    def ground(self, tone='board', tooth=1.0, drag=3, seed=None):
        """a dark toned board: an equalised fine tooth (showing as a faint mottle) and the tooth dragged along 8
        stroke directions for the dry strokes"""
        H, W = self.H, self.W
        r = self._r(seed)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.6)
        g2 = noise2d(H, W, 2.6, 2, int(r.integers(1 << 30)))
        g3 = noise2d(H, W, 8.0, 2, int(r.integers(1 << 30)))
        self.T = _equalise(0.75 * z(g1) + 0.45 * z(g2) + 0.18 * z(g3))
        mot = noise2d(H, W, 180, 3, int(r.integers(1 << 30))) - 0.5
        self.C = (hexc(tone)[None, None] * (1 + 0.1 * mot[..., None] + 0.05 * tooth * (self.T[..., None] - 0.5))
                  ).astype(np.float32)
        self.F[:] = 0
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
        # a fine stipple (single pixels and pairs) for the speckled flush, kept as uint8
        self.ST = np.round(_equalise(blur(r.random((H, W)).astype(np.float32), 0.45)) * 255).astype(np.uint8)
        # the print grain and the coarser printed tooth used by render(), made now while memory is low
        rg = np.random.default_rng(self.seed + 7)
        g = rg.standard_normal((H, W), dtype=np.float32)
        self._grain = (0.7 * g + 0.6 * blur(g, 0.8)).astype(np.float32)
        del g
        self._tooth = (noise2d(H, W, 2.2, 2, self.seed + 11) - 0.5).astype(np.float32)
        return self

    def _need(self):
        if self.T is None: self.ground()

    # ================================================================== masks
    def poly(self, pts, smooth=False, ss=2):
        """filled polygon -> canvas-sized float mask (smooth=True runs a closed Catmull-Rom spline through the points)"""
        sl, m = self._poly_crop(pts, smooth, ss)
        out = np.zeros((self.H, self.W), np.float32)
        if sl is not None: out[sl] = m
        return out

    def _poly_crop(self, pts, smooth=False, ss=2):
        """filled polygon rasterised only over its own bounding box -> (slice, crop)"""
        P = np.asarray(pts, np.float32)
        if smooth:
            Q = np.vstack([P[-1:], P, P[:2]])
            P = spline(Q, 10)[10:-10]
        x0, y0 = max(0, int(np.floor(P[:, 0].min())) - 1), max(0, int(np.floor(P[:, 1].min())) - 1)
        x1, y1 = min(self.W, int(np.ceil(P[:, 0].max())) + 2), min(self.H, int(np.ceil(P[:, 1].max())) + 2)
        if x1 <= x0 or y1 <= y0: return None, None
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((float(x) - x0) * ss, (float(y) - y0) * ss) for x, y in P], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return (slice(y0, y1), slice(x0, x1)), m

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
        """outline points of a tube of width w0 -> w1 along a path (arms, a scarf end, a stem)"""
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

    def spot(self, cx, cy, rx, ry=None, rot=0.0, solid=0.2, power=1.3):
        """a soft 0..1 field: 1 inside `solid` of the ellipse, easing to 0 at its rim (cheeks, a red nose, glows)"""
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

    def ring(self, cx, cy, rx, ry=None, width=20.0, rot=0.0, power=1.2, below=0.0):
        """a soft 0..1 ring round an ellipse (the red round an eye); below > 0 makes the lower half stronger"""
        ry = rx if ry is None else ry
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        R = max(rx, ry) + width
        x0, x1 = max(0, int(cx - R - 2)), min(self.W, int(cx + R + 3))
        y0, y1 = max(0, int(cy - R - 2)), min(self.H, int(cy + R + 3))
        out = np.zeros((self.H, self.W), np.float32)
        if x1 <= x0 or y1 <= y0: return out
        dx, dy = self.XX[y0:y1, x0:x1] - cx, self.YY[y0:y1, x0:x1] - cy
        u, v = dx * c + dy * s, -dx * s + dy * c
        d = np.sqrt((u / rx) ** 2 + (v / ry) ** 2)
        dist = (d - 1) * min(rx, ry)                        # approximate distance outside the ellipse
        f = smoothstep(width, 0.0, np.abs(dist)) ** power
        if below: f = f * (1 - below + below * smoothstep(-0.6 * ry, 0.4 * ry, v))
        out[y0:y1, x0:x1] = f
        return out

    def soften(self, mask, sigma):
        """a blurred copy of a mask, blurred only round the shape (a canvas-wide blur makes canvas-wide float64
        temporaries for a shape that covers a few percent of it)"""
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

    def radial(self, cx, cy, offset=0.0, turb=4.0, scale=120.0, seed=None):
        """directions pointing away from (cx, cy), offset in degrees"""
        a = np.arctan2(self.YY - cy, self.XX - cx) + np.deg2rad(offset)
        if turb:
            a = a + np.deg2rad(2 * turb * (noise2d(self.H, self.W, scale, 3, int(self._r(seed).integers(1 << 30))) - 0.5))
        return a.astype(np.float32)

    def contour(self, mask, sigma=8.0, offset=0.0, fallback=None):
        """directions along the iso-lines of a (blurred) shape: strokes that wrap round a cheek, a sleeve, a scarf.
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
        """'canvas' (the paint under the point) | paint | list of paints (picked at random) | (ramp, value field or
        f(x, y)) | f(x, y) -> (N, 3) | RGB"""
        n = len(x)
        if isinstance(spec, str) and spec == 'canvas': return _lookup(self.C, x, y).astype(np.float32).copy()
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
        """degrees -> radians for a number; a radians field or a callable f(x, y) -> degrees passes through (it is
        evaluated only at the points that need it)"""
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

    def strokes(self, region, field=-60.0, colour='canvas', length=(30, 70), width=(8, 16), density=1.0,
                pressure=0.78, opacity=0.9, alpha=0.8, streak=0.45, soft=0.6, jitter=0.07, bend=0.03, value=0.035,
                hue=0.02, taper=(0.55, 0.1), passes=2, clip='auto', avoid=None, fade='auto', k=5, seed=None):
        """lay opaque dry strokes (gouache) or, thin and long, pencil hatching over `region` (a 0..1 landing-
        probability mask or a box) following `field` (degrees or a radians field). density ~ how many times the
        strokes would tile the region; length / width: (lo, hi), a number or f(x, y); colour: 'canvas' (the paint
        under each stroke's centre: a painterly repaint), a paint, a list of paints, (ramp, value field or f(x, y))
        or f(x, y) -> (N, 3); pressure: how deep the pigment reaches into the tooth; opacity: how much a pale stroke
        covers what is under it; streak: how much the bristle lanes open up as the stroke runs dry; soft: the soft
        fraction of the half-width; taper: pressure at (start, end); clip: a mask the strokes are cut to ('auto' =
        the region's support); fade: a 0..1 field easing the pressure off ('auto' = region ** 0.65); avoid: things
        to paint round. Returns the number of strokes."""
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

    def lines(self, paths, colour='chalk', width=2.0, pressure=0.8, opacity=0.9, alpha=0.9, taper=(0.4, 0.2),
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
            nband = int(np.clip(np.ceil(area / self.band_px), 1, 160))
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
        tgt = (1 - opacity) * old * col + opacity * col
        Cb[m] = old + np.minimum(a1[m], 1)[:, None] * (tgt - old)
        Fb = self.F[y0:y1, x0:x1]
        Fb[m] = np.minimum(1.4, Fb[m] + a1[m] * 0.5)

    # ================================================================== smooth layers
    def _field_colour(self, colour, sl):
        """colour spec -> (h, w, 3) or (3,) for the slice: paint | (ramp, field) | array (H, W, 3) | f(X, Y)"""
        ys, xs = sl
        if isinstance(colour, np.ndarray) and colour.ndim == 3: return colour[ys, xs]
        if isinstance(colour, (tuple, list)) and len(colour) == 2 and isinstance(colour[1], np.ndarray):
            return ramp_at(ramp(colour[0]), colour[1][ys, xs])
        if callable(colour): return np.asarray(colour(self.XX[ys, xs], self.YY[ys, xs]), np.float32)
        return hexc(colour)

    def wash(self, mask, colour, alpha=1.0, grain=0.25, edge=0.5, dry=0.0, clip=None, opacity=1.0):
        """a smooth opaque coat over `mask`. colour: a paint, (ramp, 0..1 field), an (H, W, 3) array or f(X, Y).
        grain: the deepest pits of the tooth stay a little lighter; edge: within the soft rim of the mask the coat
        breaks up into the tooth; dry: the same over the whole area (a scumbled coat); opacity < 1 multiplies."""
        self._need()
        bb = self._bbox(mask)
        if bb is None: return
        x0, y0, x1, y1 = bb
        for ya in range(y0, y1, 240):                        # row bands keep the temporaries small
            self._wash_sl((slice(ya, min(y1, ya + 240)), slice(x0, x1)), mask, colour, alpha, grain, edge, dry, clip,
                          opacity)

    def _wash_sl(self, sl, mask, colour, alpha, grain, edge, dry, clip, opacity):
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
            col = (1 - opacity) * Cs * col + opacity * col
        Cs += (col - Cs) * A[..., None]
        np.clip(Cs, 0, 1, out=Cs)
        self.F[sl] = np.minimum(1.4, self.F[sl] + A * 0.6)

    def model(self, mask, colours, light=LIGHT, lit=None, sigma=None, wrap=0.3, gamma=1.0, lo=0.0, hi=1.0,
              alpha=1.0, grain=0.25, edge=0.5, clip=None, mottle=0.05, seed=None):
        """a softly modelled, simplified volume: a dome light (or `lit`) picks colours from a dark -> light ramp,
        mapped to lo..hi of the ramp, with a faint low-frequency mottle. Returns the light field."""
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
        m = self.soften(mask, soft) if soft else mask
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
        """a small soft round touch of opaque paint (catchlights, a glint, a glowing eye)"""
        ry = r if ry is None else ry
        R = max(r, ry)
        x0, x1 = max(0, int(x - R - 3)), min(self.W, int(x + R + 4))
        y0, y1 = max(0, int(y - R - 3)), min(self.H, int(y + R + 4))
        if x1 <= x0 or y1 <= y0: return
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        dx, dy = self.XX[y0:y1, x0:x1] - x, self.YY[y0:y1, x0:x1] - y
        dd = np.sqrt(((dx * c + dy * s) / r) ** 2 + ((-dx * s + dy * c) / ry) ** 2)
        A = smoothstep(1.0, max(0.0, 1.0 - soft - 0.6 / max(r, 1.0)), dd) * alpha
        Cs = self.C[y0:y1, x0:x1]
        Cs += (hexc(colour) - Cs) * A[..., None]

    # ================================================================== smooth painted lines
    def _lines_mask(self, paths, widths, taper=(0.15, 0.5), ss=3):
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
        """a smooth line painted with a small round brush, tapering in and out (lid lines, a red rim, veins);
        dry > 0 lets it break up a little on the tooth"""
        self._need()
        Q = np.asarray(path, np.float32)
        if smooth and len(Q) > 2: Q = spline(Q, 8)
        sl, m = self._lines_mask([Q], [width], taper)
        if sl is None: return
        A = m * alpha
        if dry: A = A * smoothstep(0.15, 0.6, self.T[sl] + (1 - dry) * 0.55)
        if clip is not None: A = A * clip[sl]
        Cs = self.C[sl]
        Cs += (hexc(colour) - Cs) * A[..., None]

    def sketch(self, path, colour='chalk', width=1.8, alpha=0.6, pressure=0.6, seg=(40, 110), wobble=0.8,
               gaps=0.12, smooth=True, seed=None):
        """a light chalk underdrawing line on the dark board: several overlapping sketchy strokes, some left out"""
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
        return self.lines(paths, colour, width, pressure, 0.9, alpha, (0.35, 0.2), soft=0.6,
                          k=7, seed=int(r.integers(1 << 30)))

    # ================================================================== hair
    def strands(self, region, flow, colours, n=800, length=(40, 140), width=(1.0, 2.0), curl=0.0, jitter=6.0,
                step=4.0, shade=None, spread=0.2, alpha=0.9, pressure=0.92, opacity=0.95, taper=(0.3, 0.05),
                clip=True, pad=5.0, roots=None, lock=None, k=9, seed=None):
        """many fine strands (hair, ghost-sheet threads, fibres): each starts inside `region` (or `roots`), follows
        `flow` (degrees: a number, a canvas field in radians or f(x, y) -> degrees) with its own jitter and steady
        bend (`curl` degrees per step), drawn as a fine line pressed at the root and lifting off at the tip. Each
        picks a colour from `colours` (dark -> light) by the 0..1 field `shade` plus noise; dark first, light
        last. lock=(strands per lock, lock width px) groups them into locks sharing a root area, wander, curl and
        shade. clip=True keeps them within `pad` px of the region; False lets them fly loose; or a mask."""
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
            cm = smoothstep(0.03, 0.3, self.soften(region, pad))
        elif clip is False or clip is None:
            cm = None
        else:
            cm = clip
        return self.lines(paths, lambda xx, yy, c=cols: c, width, pressure, opacity, alpha, taper, streak=0.0,
                          soft=0.55, value=0.05, clip=cm, k=k, seed=int(r.integers(1 << 30)))

    def sheen(self, mask, flow, lit=None, band=(0.6, 0.78, 0.92), colour='hair_sheen', alpha=0.5, strokes=0.25,
              length=(60, 140), width=(1.2, 2.4), density=1.4, light=LIGHT, sigma=None, seed=None):
        """the soft sheen of a solid, sculpted hair mass: a smooth band of `colour` where the dome light sits in a
        narrow band (lo, peak, hi), brightest at the peak, then a few long thin strokes along the flow inside it
        (`strokes` their alpha) so the highlight is streaked along the hair without the mass breaking into
        strands. Returns the band field."""
        if lit is None: lit = self.shading(mask, light, sigma)
        lo, pk, hi = band
        b = smoothstep(lo, pk, lit) * smoothstep(hi + 0.02, pk, lit) * mask
        self.wash(self.soften(b, 2.0) * mask, colour, alpha, grain=0.2, edge=0.0)
        if strokes:
            self.strokes(b, flow, colour, length, width, density, pressure=0.62, opacity=0.95, alpha=strokes,
                         streak=0.3, soft=0.8, taper=(0.25, 0.05), clip=mask, value=0.05, seed=seed)
        return b

    # ================================================================== faces
    def eye(self, cx, cy, rx, ry=None, iris='iris', iris_light='iris_light', iris_r=0.62, look=(0.0, 0.3), lid=0.5,
            lower=0.1, droop=0.3, lid_skin='porcelain', fold='#e2b5ad', line_colour='lid_line', line_w=None,
            rim='rim', rim_alpha=0.85, crease=0.45, catch=True, reflect=None, white='eye_white', shade='eye_shade',
            rot=0.0, side=1, clip=None):
        """a heavy-lidded, sad picture-book eye: an off-white ball shaded grey under the lid and at the corners, a
        dark iris (lighter low) with a pupil, a thick upper lid covering `lid` of the ball whose line droops toward
        the outer corner (`side` +1 = outer corner to the right; `droop` how much), the lid skin a modelled bulge
        flushed pink, a dark lid line, a red wet rim along the lower lid, a faint crease above, a small catchlight
        and, if `reflect` is a colour, a warm glint low in the iris (a light below her, mirrored in the eye).
        look = (dx, dy) in -1..1 moves the iris (dy > 0: looking down). Returns the visible-eye mask."""
        self._need()
        ry = rx * 0.62 if ry is None else ry
        a = np.deg2rad(rot); ca, sa = np.cos(a), np.sin(a)
        to = lambda u, v: (cx + u * ca - v * sa, cy + u * sa + v * ca)
        R = max(rx, ry) * 1.9 + 6
        x0, x1 = max(0, int(cx - R)), min(self.W, int(cx + R) + 1)
        y0, y1 = max(0, int(cy - R)), min(self.H, int(cy + R) + 1)
        sl = (slice(y0, y1), slice(x0, x1))
        X, Y = self.XX[sl], self.YY[sl]
        U = (X - cx) * ca + (Y - cy) * sa; V = -(X - cx) * sa + (Y - cy) * ca
        un = U / rx
        # an almond: the ball, cut by the upper lid line and the lower lid line
        ball = np.clip((1 - np.sqrt(un ** 2 + (V / ry) ** 2)) * min(rx, ry) + 0.5, 0, 1)
        vlid = -ry + 2 * ry * lid + ry * 0.2 * un ** 2 + droop * ry * 0.5 * (side * un)
        vlow = ry - 2 * ry * lower - ry * 0.18 * un ** 2 - droop * ry * 0.12 * (side * un)
        vis = ball * np.clip(V - vlid + 0.5, 0, 1) * np.clip(vlow - V + 0.5, 0, 1)
        if clip is not None: vis = vis * clip[sl]
        Cs = self.C[sl]
        # the white, grey under the lid and toward the corners
        q = np.clip((V - vlid) / (2 * ry), 0, 1)
        sideshade = np.clip(np.abs(un), 0, 1) ** 2.5
        sh_ = np.clip(0.9 * (1 - smoothstep(0.0, 0.55, q)) + 0.45 * sideshade, 0, 1)
        wf = hexc(white) + (hexc(shade) - hexc(white)) * sh_[..., None]
        Cs += (wf - Cs) * vis[..., None]
        # iris and pupil
        ir = iris_r * ry * 1.25
        iu, iv = look[0] * (rx - ir * 0.95), look[1] * (ry - ir * 0.5)
        ix, iy = to(iu, iv)
        dd = np.sqrt((X - ix) ** 2 + (Y - iy) ** 2) / ir
        im = np.clip((1 - dd) * ir + 0.5, 0, 1) * vis
        ic, il = hexc(iris), hexc(iris_light)
        qq = np.clip((Y - (iy - ir)) / (2 * ir), 0, 1)
        th = np.arctan2(Y - iy, X - ix)
        rad = 0.5 + 0.5 * np.sin(th * 21 + 1.3) * np.sin(th * 8 + 0.4)
        f = ic + (il - ic) * (smoothstep(0.45, 1.0, qq) * smoothstep(0.98, 0.4, dd) * (0.7 + 0.3 * rad))[..., None]
        f = f * (1 - 0.4 * smoothstep(0.7, 1.0, dd))[..., None]
        Cs += (f - Cs) * im[..., None]
        pm = np.clip((1 - dd / 0.45) * ir * 0.45 + 0.5, 0, 1) * vis
        Cs += (hexc('pupil') - Cs) * (pm * 0.95)[..., None]
        # the lid's shadow on the ball
        shadow = vis * smoothstep(vlid + ry * 0.55, vlid, V)
        Cs *= (1 - 0.42 * shadow[..., None] * (1 - hexc('#5e5a78')))
        # the heavy upper lid: a modelled bulge of flushed skin above the lid line
        bulge = np.clip((1 - np.sqrt((un / 1.12) ** 2 + ((V - vlid + ry * 0.05) / (ry * 0.95)) ** 2)) * ry + 0.5, 0, 1)
        bulge = bulge * np.clip(vlid - V + 0.5, 0, 1)
        if clip is not None: bulge = bulge * clip[sl]
        lt = np.clip(0.55 - 0.45 * ((V - vlid) / ry + 0.45) + 0.12 * (-un * np.sign(LIGHT[0])), 0, 1)
        lc = hexc(lid_skin) * (0.86 + 0.18 * lt)[..., None]
        lc = lc + (hexc(fold) - lc) * (0.55 * smoothstep(-ry * 0.9, 0, V - vlid))[..., None]
        Cs += (lc - Cs) * (bulge * 0.92)[..., None]
        np.clip(Cs, 0, 1, out=Cs)
        lw = max(1.8, ry * 0.2) if line_w is None else line_w
        us = np.linspace(-1.02, 1.02, 30)
        vl = -ry + 2 * ry * lid + ry * 0.2 * us ** 2 + droop * ry * 0.5 * (side * us)
        vb = ry - 2 * ry * lower - ry * 0.18 * us ** 2 - droop * ry * 0.12 * (side * us)
        ok = vl < vb + 1
        # the lower lid: a red wet rim, a lighter wet line just inside it
        lowp = [to(u * rx, v) for u, v in zip(us, vb)]
        self.line(lowp, max(1.6, lw * 0.75), rim, rim_alpha, taper=(0.3, 0.25))
        self.line([to(u * rx * 0.9, v - lw * 0.55) for u, v in zip(us, vb)], max(1.0, lw * 0.3), '#f0b8ad',
                  0.35, taper=(0.4, 0.4))
        # the lid line: thick in the middle, fine at the corners, a touch past the outer corner
        lidp = [to(u * rx, v - lw * 0.1) for u, v, o in zip(us, vl, ok) if o or abs(u) > 0.9]
        if len(lidp) > 2:
            self.line(lidp, lw, line_colour, 0.95, taper=(0.3, 0.2))
        if crease:
            cp = [to(u * rx * 1.04, v - ry * 0.95 - ry * 0.12 * (1 - u * u)) for u, v in zip(us[3:-2], vl[3:-2])]
            self.line(cp, max(1.0, lw * 0.4), 'crease', crease, taper=(0.5, 0.5), dry=0.3)
        if catch:
            cu, cv = iu - ir * 0.32, max(iv - ir * 0.25, -ry + 2 * ry * lid + ry * 0.12)
            self.dab(*to(cu, cv), max(1.2, ir * 0.13), '#f6f2ee', 0.85, soft=0.4)
        if reflect is not None:
            gx, gy = to(iu + ir * 0.22, min(iv + ir * 0.5, ry - 2 * ry * lower - ry * 0.3))
            self.dab(gx, gy, max(1.2, ir * 0.16), reflect, 0.8, soft=0.6, ry=max(1.0, ir * 0.1))
        out = np.zeros((self.H, self.W), np.float32); out[sl] = vis
        return out

    def flush(self, field, colour='flush', strength=0.6, speckle=0.55, clip=None):
        """the red flush on porcelain: a smooth glaze of `colour` over the 0..1 `field` plus a stipple that only
        catches the high points of the tooth (more of it where the flush is stronger) -- the speckled red"""
        self._need()
        bb = self._bbox(field)
        if bb is None: return
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        f = np.clip(field[sl], 0, 1)
        if clip is not None: f = f * clip[sl]
        Tt = self.ST[sl].astype(np.float32) * (1.0 / 255)
        smooth_ = f * strength * (1 - 0.5 * speckle)
        th = 1.0 - f * (0.3 + 0.55 * strength)
        stip = smoothstep(th, th + 0.08, Tt) * f ** 0.5 * speckle
        A = np.clip(smooth_ + stip * strength * 1.1, 0, 1)
        Cs = self.C[sl]
        col = hexc(colour)
        # a light flush reads as rosy, a strong one as red: keep the value of what is under it a little
        tgt = col * (0.8 + 0.25 * Cs.mean(-1, keepdims=True))
        Cs += (tgt - Cs) * A[..., None]
        np.clip(Cs, 0, 1, out=Cs)

    def nose(self, path, width=26.0, tip_r=None, side=1, shade=0.55, shadow='#8c7480', tip='flush',
             tip_strength=0.8, nostril=0.7, highlight=0.5, cast=0.35, clip=None):
        """a long, simplified nose down `path` (bridge -> tip): its own little volume -- a tube widening to a round
        tip, lit from the upper left, so the side away from the light (`side` +1 = right) is a soft mauve plane --
        a flush that strengthens toward a red tip, a soft shadow cast under the tip, a little nostril and a pale
        line of light down the bridge"""
        P = np.asarray(spline(np.asarray(path, np.float32), 10), np.float32)
        n = len(P)
        tp = P[-1]
        tip_r = width * 0.6 if tip_r is None else tip_r
        d = P[-1] - P[-2]; d /= np.linalg.norm(d) + 1e-6
        nrm = np.array([-d[1], d[0]], np.float32)
        if nrm[0] * side < 0: nrm = -nrm                         # nrm points to the shadow side
        m = np.maximum(self.tube(P, np.linspace(width * 0.45, width * 0.85, n)),
                       self.ellipse(tp[0], tp[1], tip_r * 1.05, tip_r * 0.92))
        if clip is not None: m = m * clip
        lit = self.shading(m, LIGHT, sigma=width * 0.45, wrap=0.2)
        sh = self.soften(m, width * 0.12) * smoothstep(0.62, 0.25, lit)
        self.glaze(sh, shadow, shade, 'multiply')
        if cast:
            cs = self.soften(np.roll(np.roll(self.ellipse(tp[0], tp[1], tip_r * 1.1, tip_r * 0.8), int(tip_r * 0.7), 0),
                              int(side * tip_r * 0.5), 1), tip_r * 0.4) * (1 - m)
            if clip is not None: cs = cs * clip
            self.glaze(cs, shadow, cast, 'multiply')
        f = np.zeros((self.H, self.W), np.float32)
        for i in range(0, n, 3):
            t = i / (n - 1)
            f = np.maximum(f, self.spot(P[i, 0], P[i, 1], width * (0.5 + 0.4 * t), width * (0.5 + 0.4 * t),
                                        solid=0.0, power=1.4) * (0.1 + 0.9 * t ** 2.4))
        f = np.maximum(f, self.spot(tp[0], tp[1], tip_r * 1.35, tip_r * 1.15, solid=0.3))
        if clip is not None: f = f * clip
        self.flush(f, tip, tip_strength, speckle=0.4)
        if nostril:
            self.line([tp + nrm * tip_r * 0.05 + d * tip_r * 0.62, tp + nrm * tip_r * 0.45 + d * tip_r * 0.7,
                       tp + nrm * tip_r * 0.85 + d * tip_r * 0.4], max(1.2, width * 0.08), '#6e2a2c', nostril,
                      taper=(0.4, 0.3))
        if highlight:
            hp = P[int(n * 0.1):int(n * 0.85)] - nrm * width * 0.16
            if len(hp) > 2: self.line(hp, max(1.5, width * 0.14), '#fbf4f0', highlight * 0.55, taper=(0.6, 0.6), dry=0.2)
            self.dab(*(tp - nrm * tip_r * 0.32 - d * tip_r * 0.28), max(1.2, tip_r * 0.22), '#ffe9e0', highlight,
                     soft=0.7)

    def mouth(self, x, y, w=32.0, droop=0.15, colour='lip', dark='lip_dark', alpha=1.0, rot=0.0):
        """a small closed, unsmiling mouth: a thin upper lip, a slightly fuller lower lip, a dark parting line whose
        corners turn down by `droop`, a faint shadow under the lower lip"""
        h = w * 0.3
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        to = lambda pts: [(x + u * c - v * s, y + u * s + v * c) for u, v in pts]
        up = to([(-w * 0.5, droop * h), (-w * 0.22, -h * 0.42), (0, -h * 0.26), (w * 0.22, -h * 0.42),
                 (w * 0.5, droop * h), (0, h * 0.06)])
        lo = to([(-w * 0.42, droop * h * 0.9), (-w * 0.15, h * 0.12), (w * 0.15, h * 0.12), (w * 0.42, droop * h * 0.9),
                 (w * 0.2, h * 0.78), (-w * 0.2, h * 0.78)])
        self.wash(self.soften(self.poly(up, smooth=True), 0.8), mix(colour, dark, 0.3), 0.8 * alpha, grain=0.1, edge=0.2)
        self.wash(self.soften(self.poly(lo, smooth=True), 0.9), colour, 0.72 * alpha, grain=0.1, edge=0.2)
        self.dab(*to([(w * 0.04, h * 0.42)])[0], w * 0.12, '#efc1b8', 0.4 * alpha, ry=h * 0.12, soft=0.8, rot=rot)
        self.line(to([(-w * 0.52, droop * h * 1.5), (-w * 0.2, h * 0.04), (0, h * 0.08), (w * 0.2, h * 0.04),
                      (w * 0.52, droop * h * 1.5)]), max(1.2, w * 0.05), dark, 0.8 * alpha, taper=(0.4, 0.4))
        sh = self.spot(*to([(0, h * 1.25)])[0], w * 0.3, h * 0.45, rot, solid=0.0)
        self.glaze(sh, 'porcelain_deep', 0.35 * alpha, 'multiply')

    # ================================================================== textiles
    def _lit_height(self, Hh, depth, light=LIGHT):
        hh = Hh * depth
        gy, gx = np.gradient(hh)
        Lv = np.asarray(light, np.float32); Lv = Lv / np.linalg.norm(Lv)
        nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
        return np.clip((-gx * Lv[0] - gy * Lv[1] + Lv[2]) * nz, 0, 1)

    def _coords(self, sl, angle, coords):
        if coords is not None:
            return coords[0][sl].astype(np.float32), coords[1][sl].astype(np.float32)
        X, Y = self.XX[sl], self.YY[sl]
        a = np.deg2rad(angle); c, s = np.cos(a), np.sin(a)
        return X * c + Y * s, -X * s + Y * c

    def burlap(self, mask, angle=0.0, period=9.0, coords=None, thread=0.66, slub=0.4, wander=0.18, holes=0.85,
               hole_colour='#0a0807', strength=0.9, highlight=0.4, rust=0.0, fibres=1.0, fuzz=1.0, light=LIGHT,
               seed=None):
        """coarse burlap (hessian) multiplied onto the paint that is there: a plain weave of slubby threads -- each
        row and column its own thickness, lumps along it, rows and columns wandering a little, over-under
        alternation -- lit as a height field, dark holes between the threads, a share `rust` of rust-coloured
        threads (0 by default: whole rust threads read as seams), loose fibres on the surface and sticking out of
        the silhouette. coords = (U, V) canvas arrays (px) to make the
        weave follow a shape; else the canvas rotated by `angle`."""
        r = self._r(seed)
        bb = self._bbox(mask, pad=2)
        if bb is None: return
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        h, w = y1 - y0, x1 - x0
        U, V = self._coords(sl, angle, coords)
        sd = float(r.integers(1, 9999))
        nU = noise2d(h, w, period * 9, 2, int(r.integers(1 << 30))) - 0.5
        nV = noise2d(h, w, period * 9, 2, int(r.integers(1 << 30))) - 0.5
        Up = U / period + wander * 2 * nU
        Vp = V / period + wander * 2 * nV
        i = np.floor(Vp + 0.5); fv = Vp - i                       # nearest row (weft) and the offset from it
        k = np.floor(Up + 0.5); fu = Up - k                       # nearest column (warp)

        def slubs(idx, along):
            # thickness lumps along a thread: a hash per thread, interpolated every ~3 periods
            a = along / 3.0
            a0 = np.floor(a); t = a - a0
            t = t * t * (3 - 2 * t)
            return (1 - t) * _hash(idx + sd, a0) + t * _hash(idx + sd, a0 + 1)
        hw_r = 0.5 * thread * (0.82 + 0.36 * _hash(i, sd + 0.5)) * (1 + slub * (slubs(i, Up) - 0.5))
        hw_c = 0.5 * thread * (0.82 + 0.36 * _hash(k + 0.31, sd)) * (1 + slub * (slubs(k + 77.0, Vp) - 0.5))
        pr = np.sqrt(np.clip(1 - (fv / hw_r) ** 2, 0, 1))
        pc = np.sqrt(np.clip(1 - (fu / hw_c) ** 2, 0, 1))
        # over / under: a row is on top of a column where (row + column) is even
        hr = pr * (0.7 + 0.3 * np.cos(np.pi * (Up + i)))
        hc = pc * (0.7 + 0.3 * np.cos(np.pi * (Vp + k + 1)))
        top_r = hr >= hc
        Hh = np.maximum(hr, hc)
        lam = self._lit_height(Hh, period * 0.55, light)
        ao = 0.3 + 0.7 * smoothstep(0.0, 0.6, Hh)
        tj = np.where(top_r, _hash(i, sd + 3.1), _hash(k, sd + 5.7)) - 0.5   # every thread its own value
        kf = ao * (0.55 + 0.75 * lam) * (1 + 0.28 * tj)
        kf = kf * (1 + 0.12 * (noise2d(h, w, 1.5, 2, int(r.integers(1 << 30))) - 0.5))   # the hairy fibre
        m = mask[sl]
        mk = float((kf * m).sum() / (m.sum() + 1e-6))
        kf = kf / max(mk, 1e-3)
        Cs = self.C[sl]
        Cs *= (1 + strength * (kf - 1) * m)[..., None]
        if rust:
            rt = (np.where(top_r, _hash(i, sd + 9.3), _hash(k, sd + 2.2)) < rust) * smoothstep(0.2, 0.6, Hh) * m
            Cs += (hexc('burlap_rust') * kf[..., None] * 0.8 - Cs) * (rt * 0.55)[..., None]
        hole = (1 - smoothstep(0.0, 0.3, Hh)) * m * holes
        Cs += (hexc(hole_colour) - Cs) * hole[..., None]
        if highlight:
            hl = smoothstep(0.62, 0.92, lam * Hh) * smoothstep(0.45, 0.65, self.T[sl] + 0.1) * m
            Cs += (np.clip(Cs * 1.35 + 0.05, 0, 1) - Cs) * (hl * highlight)[..., None]
        np.clip(Cs, 0, 1, out=Cs)
        if fibres:
            mean = (Cs * m[..., None]).sum((0, 1)) / (m.sum() + 1e-6)
            nf = int(m.sum() / 260 * fibres)
            if nf > 0:
                sub = np.zeros((self.H, self.W), np.float32); sub[sl] = m
                self.strands(sub, angle if coords is None else 0.0, [mean * 1.25 + 0.02, mean * 1.6 + 0.04],
                             n=nf, length=(4, 14), width=(0.6, 1.0), step=1.5, jitter=70, curl=14, alpha=0.45,
                             clip=sub, seed=int(r.integers(1 << 30)))
        if fuzz:
            sub = np.zeros((self.H, self.W), np.float32); sub[sl] = m
            self.fuzz(sub, (4, 12), n=int(np.sqrt(m.sum()) * 2.2 * fuzz), width=(0.7, 1.1), out=0.6, alpha=0.6,
                      lift=0.25, curl=18, seed=int(r.integers(1 << 30)))

    def along(self, path, mask, pad=4):
        """(S, T) canvas arrays round `mask`: arc length along `path` of the nearest point and the signed offset from
        it (px) -- coordinates that bend with a tube (a drooping hat tip, a scarf) for burlap(), tartan() or knit()"""
        bb = self._bbox(mask, pad=pad)
        S = np.zeros((self.H, self.W), np.float32); T = np.zeros((self.H, self.W), np.float32)
        if bb is None: return S, T
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        Q = np.asarray(spline(np.asarray(path, np.float32), 8) if len(path) > 2 else path, np.float32)
        S[sl], T[sl] = self._path_st(Q, sl)
        return S, T

    def _path_st(self, Q, sl):
        """for every pixel in sl: arc length of the nearest point on polyline Q and the signed offset"""
        X = self.XX[sl]; Y = self.YY[sl]
        seg = Q[1:] - Q[:-1]
        Ls = np.hypot(seg[:, 0], seg[:, 1]) + 1e-6
        cum = np.concatenate([[0], np.cumsum(Ls)])
        best = np.full(X.shape, 1e12, np.float32); S = np.zeros_like(X); Tt = np.zeros_like(X)
        for k in range(len(seg)):
            dx, dy = seg[k] / Ls[k]
            rx, ry = X - Q[k, 0], Y - Q[k, 1]
            a = np.clip(rx * dx + ry * dy, 0, Ls[k])
            px, py = rx - a * dx, ry - a * dy
            d2 = px * px + py * py
            m = d2 < best
            best = np.where(m, d2, best)
            S = np.where(m, cum[k] + a, S)
            Tt = np.where(m, -rx * dy + ry * dx, Tt)
        return S, Tt

    def knit(self, mask, stitch=(16, 12), angle=0.0, path=None, origin=None, curve=0.0, strength=0.8,
             highlight=0.3, fuzz=0.6, depth=0.5, light=LIGHT, seed=None):
        """chunky stockinette (rows of V stitches) multiplied onto the paint that is there. Each leg of a V is a
        rotated ellipse with a cylinder profile and faint ply grooves, the valleys between legs dark; lit as a
        height field. path: the stitch columns run along a polyline (a scarf); else rows are rotated by `angle`
        and bow by `curve` rows at the sides of `origin`."""
        r = self._r(seed)
        bb = self._bbox(mask, pad=1)
        if bb is None: return
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        sw, sh = stitch
        if path is not None:
            Q = np.asarray(spline(np.asarray(path, np.float32), 8) if len(path) > 2 else path, np.float32)
            S, Tt = self._path_st(Q, sl)
            Xr, Yr = Tt, S
            ox, hw = 0.0, 1.0
        else:
            Xr, Yr = self._coords(sl, angle, None)
            ox = (origin[0] if origin is not None else (x0 + x1) / 2)
            if angle:
                a = np.deg2rad(angle); ox = ox * np.cos(a) + (origin[1] if origin is not None else (y0 + y1) / 2) * np.sin(a)
            hw = max(1.0, (x1 - x0) / 2)
        U = (Xr - ox) / sw + 0.5
        V = Yr / sh + curve * ((Xr - ox) / hw) ** 2
        iu = np.floor(U); fu = U - iu - 0.5
        Hh = np.zeros_like(U); win_v = np.zeros_like(U)
        legd = np.array([0.44 * sw, 1.1 * sh]); legl = float(np.linalg.norm(legd))
        a_ = 0.5 * legl; b_ = 0.215 * sw
        for dv in (-1, 0, 1):
            iv = np.floor(V) + dv
            hj1 = _hash(iu + 0.37, iv) - 0.5; hj2 = _hash(iu, iv + 0.71) - 0.5; hj3 = _hash(iu + 0.13, iv + 0.29)
            fv = V - iv - 0.5 - hj2 * 0.12
            px, py = (fu - hj1 * 0.10) * sw, fv * sh
            sc = 0.9 + 0.2 * hj3
            for sd in (-1, 1):
                dx, dy = -sd * legd[0] / legl, legd[1] / legl
                rx_, ry_ = px - sd * 0.235 * sw, py
                al = rx_ * dx + ry_ * dy
                ac = -rx_ * dy + ry_ * dx
                e = (al / (a_ * sc)) ** 2 + (ac / (b_ * sc)) ** 2
                hl = np.sqrt(np.clip(1 - e, 0, 1))
                hl = hl * (0.86 + 0.14 * np.sin((al / a_ * 2.6 + ac / b_ * 0.9) * np.pi + hj3 * 3))
                hl = hl * (1.0 + 0.06 * dv)
                win = hl > Hh
                Hh = np.where(win, hl, Hh); win_v = np.where(win, iv, win_v)
        jit = _hash(iu, win_v) - 0.5
        lam = self._lit_height(Hh, depth * sw, light)
        ao = 0.38 + 0.62 * smoothstep(0.0, 0.55, Hh)
        kf = ao * (0.55 + 0.75 * lam) * (1 + 0.16 * jit)
        h, w = kf.shape
        kf = blur(kf, 0.55)
        if fuzz:
            kf = kf * (1 + fuzz * 0.12 * (noise2d(h, w, 1.6, 2, int(r.integers(1 << 30))) - 0.5))
        m = mask[sl]
        kf = kf / max(float((kf * m).sum() / (m.sum() + 1e-6)), 1e-3)
        Cs = self.C[sl]
        Cs *= (1 + strength * (kf - 1) * m)[..., None]
        if highlight:
            hl = smoothstep(0.62, 0.9, lam * Hh) * smoothstep(0.45, 0.65, self.T[sl] + 0.1) * m
            Cs += (np.clip(Cs * 1.25 + 0.05, 0, 1) - Cs) * (hl * highlight)[..., None]
        np.clip(Cs, 0, 1, out=Cs)

    def rib(self, mask, path, period=9.0, strength=0.75, highlight=0.25, rows=0.85, light=LIGHT):
        """ribbing across a band (a cuff, a hem): raised knit columns and sunken purl columns at right angles to
        `path` (the band's centre line), with small chevrons of stitches along each column"""
        bb = self._bbox(mask, pad=1)
        if bb is None: return
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        Q = np.asarray(path, np.float32)
        if len(Q) > 2: Q = spline(Q, 8)
        S, Tt = self._path_st(Q, sl)
        ph = S / period
        f = ph - np.floor(ph) - 0.5
        Hh = np.sqrt(np.clip(1 - (f / 0.34) ** 2, 0, 1))
        if rows:
            g = Tt / (period * 0.62) + np.abs(f) * 1.4
            Hh = Hh * (1 - 0.22 * rows + 0.22 * rows * np.abs(np.cos(g * np.pi)))
        lam = self._lit_height(Hh, period * 0.45, light)
        kf = (0.42 + 0.58 * smoothstep(0, 0.5, Hh)) * (0.55 + 0.75 * lam)
        m = mask[sl]
        kf = kf / max(float((kf * m).sum() / (m.sum() + 1e-6)), 1e-3)
        Cs = self.C[sl]
        Cs *= (1 + strength * (kf - 1) * m)[..., None]
        if highlight:
            hl = smoothstep(0.6, 0.92, lam * Hh) * smoothstep(0.45, 0.65, self.T[sl] + 0.1) * m
            Cs += (np.clip(Cs * 1.2 + 0.05, 0, 1) - Cs) * (hl * highlight)[..., None]
        np.clip(Cs, 0, 1, out=Cs)

    def tartan(self, mask, sett, scale=3.0, angle=0.0, coords=None, lit=None, lo=0.35, hi=1.05, alpha=1.0,
               threadshade=0.22, fuzz=0.5, gamma=1.0, seed=None):
        """a tartan cloth: `sett` is the half-sett [(colour, threads), ...] mirrored into a symmetric repeat, each
        thread `scale` px wide; woven 2/2 twill, so at every cell either the warp or the weft colour shows by a
        diagonal rule, and every thread is a little rounded (darker at its sides). The cloth colour is multiplied by
        lo..hi of the light field `lit` (the folds) and laid as an opaque coat. coords = (U, V) canvas arrays (px)
        to make the checks follow the folds; else the canvas rotated by `angle`."""
        r = self._r(seed)
        bb = self._bbox(mask, pad=1)
        if bb is None: return
        x0, y0, x1, y1 = bb
        sl = (slice(y0, y1), slice(x0, x1))
        h, w = y1 - y0, x1 - x0
        half = []
        for c, nthr in sett: half += [hexc(c)] * int(nthr)
        full = np.array(half + half[::-1], np.float32)
        per = len(full)
        U, V = self._coords(sl, angle, coords)
        uu, vv = U / scale, V / scale
        iu = np.floor(uu).astype(np.int64); iv = np.floor(vv).astype(np.int64)
        warp = full[np.mod(iu, per)]; weft = full[np.mod(iv, per)]
        show_warp = (np.mod(iu + iv, 4) < 2)[..., None]
        fu = uu - iu; fv = vv - iv
        rw = 1 - threadshade * (1 - np.sin(np.pi * fu)) ** 2
        rf = 1 - threadshade * (1 - np.sin(np.pi * fv)) ** 2
        col = np.where(show_warp, warp * rw[..., None], weft * rf[..., None])
        col = np.stack([blur(col[..., c], 0.45) for c in range(3)], -1)
        if fuzz:
            col = col * (1 + fuzz * 0.16 * (noise2d(h, w, 1.4, 2, int(r.integers(1 << 30))) - 0.5))[..., None]
        if lit is not None:
            col = col * (lo + (hi - lo) * np.clip(lit[sl], 0, 1) ** gamma)[..., None]
        m = mask[sl] * alpha
        Cs = self.C[sl]
        Cs += (np.clip(col, 0, 1) - Cs) * m[..., None]
        np.clip(Cs, 0, 1, out=Cs)
        self.F[sl] = np.minimum(1.4, self.F[sl] + m * 0.6)

    def fuzz(self, mask, length=(6, 16), n=None, width=(0.8, 1.3), out=0.7, field=None, alpha=0.7, lift=0.08,
             band=2.5, inset=4.0, curl=8.0, light=None, seed=None):
        """fibres growing out of a silhouette (wool, felt, burlap, a ghost's sheet): short strands rooted just inside
        the edge of `mask`, leaning outward (`out` 0..1 blends the outward normal with `field`), each coloured from
        the paint a few px inside it (lifted a touch, more on the lit side), so the edge is soft and hairy"""
        r = self._r(seed)
        b = self.soften(mask, band)
        rim = (smoothstep(0.35, 0.6, b) * smoothstep(0.98, 0.75, b))
        bb = self._bbox(rim, 0.3)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        sub = rim[y0:y1, x0:x1] > 0.3
        idx = np.flatnonzero(sub)
        if not len(idx): return 0
        if n is None: n = int(len(idx) / 6)
        if n <= 0: return 0
        pick = r.choice(idx, n)
        y = (pick // sub.shape[1] + y0).astype(np.float32) + r.random(n).astype(np.float32)
        x = (pick % sub.shape[1] + x0).astype(np.float32) + r.random(n).astype(np.float32)
        g = self.soften(mask, 5.0)
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
        sx_ = np.clip(x - ox * inset, 0, self.W - 1).astype(int); sy_ = np.clip(y - oy * inset, 0, self.H - 1).astype(int)
        col = self.C[sy_, sx_].copy()
        lf = np.full((n, 1), lift, np.float32)
        if light is not None:
            L2 = np.asarray(light[:2], np.float32); L2 /= np.linalg.norm(L2)
            lf = lf * (1 + 1.5 * np.clip(ox * L2[0] + oy * L2[1], 0, 1))[:, None]
        col = np.clip(col * (1 + lf) + 0.015, 0, 1).astype(np.float32)
        lens = r.uniform(*length, n).astype(np.float32)
        k = 6
        a0 = np.deg2rad(ang + r.normal(0, 16, n))[:, None]; cv = np.deg2rad(r.normal(0, curl, n))[:, None]
        j = np.arange(k, dtype=np.float32)[None]
        st = (lens / (k - 1))[:, None]
        dx = np.cumsum(np.c_[np.zeros(n), (np.cos(a0 + cv * j[:, :-1]) * st)], 1)
        dy = np.cumsum(np.c_[np.zeros(n), (np.sin(a0 + cv * j[:, :-1]) * st)], 1)
        paths = [np.stack([x[i] + dx[i], y[i] + dy[i]], 1).astype(np.float32) for i in range(n)]
        return self.lines(paths, lambda xx, yy, c=col: c, width, 0.9, 0.95, alpha, (0.6, 0.0), soft=0.55,
                          value=0.04, k=k, seed=int(r.integers(1 << 30)))

    # ================================================================== foliage
    def leaf(self, x, y, size, angle=-90.0, colours='leaf', value=0.5, fold=0.16, lit=0.0, rec=1.0, alpha=1.0,
             veins=0.45, lobes=5, mottle=0.08, squash=0.55, shadow=0.5, seed=None):
        """a palmate, serrated (maple-like) leaf whose veins meet at (x, y), main lobe toward `angle`, foreshortened
        by up to `squash` (seen at an angle): each lobe is folded along its midrib (one half lighter by `fold`),
        lighter toward the tips, mottled, with pale veins; first it casts a soft shadow (`shadow`) down and to the
        right on what is behind, which gives a hedge its depth. lit > 0 lights it by the light map (a leaf near a
        ghost turns warm). Returns the outline points."""
        r = self._r(seed)
        pts, tips = _maple(size, angle, r, lobes)
        if squash < 1:                                        # seen at an angle: squashed along a random axis
            sa = r.uniform(0, np.pi); k = r.uniform(squash, 1.0)
            Rm = np.array([[np.cos(sa), -np.sin(sa)], [np.sin(sa), np.cos(sa)]], np.float32)
            S = Rm @ np.diag([1.0, k]).astype(np.float32) @ Rm.T
            pts = pts @ S.T; tips = tips @ S.T
        pts = pts + np.array([x, y], np.float32)
        if shadow:
            off = np.array([size * 0.07, size * 0.11], np.float32)
            s2, ms = self._poly_crop(pts + off)
            if s2 is not None:
                k = max(1.0, size * 0.06)
                ys, xs = s2
                pad = int(3 * k) + 2
                y0, y1 = max(0, ys.start - pad), min(self.H, ys.stop + pad)
                x0, x1 = max(0, xs.start - pad), min(self.W, xs.stop + pad)
                big = np.zeros((y1 - y0, x1 - x0), np.float32)
                big[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0] = ms
                Cs = self.C[y0:y1, x0:x1]
                Cs *= (1 - shadow * blur(big, k))[..., None]
        sl, m = self._poly_crop(pts)
        if sl is None: return pts
        X, Y = self.XX[sl], self.YY[sl]
        dx, dy = X - x, Y - y
        rad = np.sqrt(dx * dx + dy * dy) / size
        phi = np.arctan2(dy, dx)
        ta = np.arctan2(tips[:, 1], tips[:, 0])
        dif = _wrap(phi[..., None] - ta[None, None, :])
        near = np.argmin(np.abs(dif), -1)
        side = np.sign(np.take_along_axis(dif, near[..., None], -1)[..., 0])
        s = 1.0 if r.random() < 0.5 else -1.0
        h, w = m.shape
        mot = noise2d(h, w, max(4, size * 0.3), 2, int(r.integers(1 << 30))) - 0.5
        v = value + fold * 0.5 * side * s + 0.16 * (rad - 0.45) + mottle * 2 * mot
        col = ramp_at(ramp(colours), v)
        Cs = self.C[sl]
        A = m * alpha
        Cs += (col - Cs) * A[..., None]
        # veins: a pale midrib to every lobe, a few side veins
        vc = ramp_at(ramp(colours), min(1.0, value + 0.3))
        if veins:
            for (tx, ty) in tips:
                self.line([(x, y), (x + tx * 0.5, y + ty * 0.5), (x + tx * 0.92, y + ty * 0.92)], max(0.9, size * 0.018),
                          vc, veins * alpha, taper=(0.1, 0.8))
                L = np.hypot(tx, ty); d = np.array([tx, ty]) / (L + 1e-6); nrm = np.array([-d[1], d[0]])
                for t in (0.38, 0.62):
                    for sg in (-1, 1):
                        p0 = np.array([x, y]) + d * L * t
                        p1 = p0 + (d * 0.7 + nrm * sg * 0.7) * L * 0.22
                        self.line([p0, p1], max(0.7, size * 0.01), vc, veins * 0.6 * alpha, taper=(0.1, 0.8))
        if lit:
            self._illuminate_sl(sl, A * rec * lit, 1.0, 0.3, 1.8)
        np.clip(Cs, 0, 1, out=Cs)
        return pts

    def foliage(self, region, n=200, size=(60, 120), colours=('leaf',), value=(0.25, 0.7), angle=(-180, 180),
                fold=0.16, lit=0.0, veins=0.45, depth_size=0.4, squash=0.55, shadow=0.5, seed=None):
        """scatter `n` leaves over `region` (a 0..1 probability mask) back to front: each draws a depth; deeper
        leaves are smaller and darker; colours is a list of ramps picked at random; angle is the range of the main
        lobe's direction (degrees)"""
        r = self._r(seed)
        M = self._mask(region)
        bb = self._bbox(M)
        if bb is None: return 0
        x0, y0, x1, y1 = bb
        xs, ys = [], []
        tries = 0
        while len(xs) < n and tries < 60:
            cx = r.uniform(x0, x1, n * 3); cy = r.uniform(y0, y1, n * 3)
            ok = r.random(n * 3) < _lookup(M, cx, cy)
            xs += list(cx[ok]); ys += list(cy[ok]); tries += 1
        xs, ys = np.array(xs[:n]), np.array(ys[:n])
        depth = np.sort(r.random(len(xs)))
        o = r.permutation(len(xs))
        xs, ys = xs[o], ys[o]
        for i in range(len(xs)):
            d = depth[i]
            sz = r.uniform(*size) * (1 - depth_size + depth_size * d)
            v = value[0] + (value[1] - value[0]) * d + r.normal(0, 0.05)
            c = colours[int(r.integers(len(colours)))]
            self.leaf(xs[i], ys[i], sz, r.uniform(*angle), c, v, fold, lit, 1.0, 1.0, veins, squash=squash,
                      shadow=shadow, seed=int(r.integers(1 << 30)))
        return len(xs)

    # ================================================================== light
    def light(self, x, y, r, colour=GLOW, power=1.0, squash=1.0, fall=2.0):
        """register a warm point light (falloff 1 / (1 + (d / r)^2)^fall -- steep, so a small ghost lights only
        what is near it; squash < 1 flattens it vertically)"""
        self.lights.append((float(x), float(y), float(r), hexc(colour), float(power), float(squash), float(fall)))
        self._L = None

    def lightmap(self):
        if self._L is None:
            L = np.zeros((self.H, self.W, 3), np.float32)
            for (x, y, rr, col, pw, sq, fa) in self.lights:
                d2 = ((self.XX - x) / rr) ** 2 + ((self.YY - y) / (rr * sq)) ** 2
                L += (pw / (1 + d2) ** fa)[..., None] * col
            self._L = L
        return self._L

    def _illuminate_sl(self, sl, rec, gain, base, albedo):
        L = self.lightmap()[sl]
        Cs = self.C[sl]
        l = L * (rec * gain)[..., None]
        Cs[:] = 1 - (1 - Cs) * np.exp(-l * (base + albedo * Cs))

    def illuminate(self, receptivity=1.0, gain=1.0, base=0.3, albedo=1.6, rows=270):
        """light what is painted by the registered lights: C <- 1 - (1 - C) exp(-L x receptivity x (base + albedo C)).
        receptivity: a number or a canvas field (what faces the light, what is near it)"""
        self.lightmap()
        for y0 in range(0, self.H, rows):
            sl = (slice(y0, min(self.H, y0 + rows)), slice(0, self.W))
            rec = receptivity[sl] if isinstance(receptivity, np.ndarray) else np.full((sl[0].stop - y0, self.W),
                                                                                     float(receptivity), np.float32)
            self._illuminate_sl(sl, rec, gain, base, albedo)

    def emit(self, x, y, r, power=1.0, ry=None, rot=0.0):
        """add a soft spot to the emission buffer (bloomed in render: the halo of a glowing eye or tip)"""
        ry = r if ry is None else ry
        R = max(r, ry) * 2.2
        x0, x1 = max(0, int(x - R)), min(self.W, int(x + R) + 1)
        y0, y1 = max(0, int(y - R)), min(self.H, int(y + R) + 1)
        if x1 <= x0 or y1 <= y0: return
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        dx, dy = self.XX[y0:y1, x0:x1] - x, self.YY[y0:y1, x0:x1] - y
        d2 = ((dx * c + dy * s) / r) ** 2 + ((-dx * s + dy * c) / ry) ** 2
        self.E[y0:y1, x0:x1] += power * np.exp(-d2 * 1.6)
        self._bloom = None

    # ================================================================== ghosts
    def ghost(self, cx, top, w, h, look=(0.0, 0.0), tips=7, strands=None, glow=1.0, lean=0.0, eye_r=0.1,
              body_alpha=0.32, sheet=0.42, colours=('ghost_dark', 'ghost', 'ghost_light', 'ghost_white'), clip=None,
              seed=None):
        """a small sheet-ghost: a translucent dome-and-bell body of fine silver strands flowing over the crown and
        falling to a fringe of `tips` locks, two glowing eyes (cream core, amber ring, halo; `look` shifts them,
        -1..1) and a warm glowing bead at the end of every lock. `lean` tilts the fall of the sheet (degrees).
        clip: a mask the ghost is painted into (to hide it behind leaves). Returns the body mask."""
        r = self._r(seed)
        R = w / 2.0
        cy = top + R                                             # centre of the dome
        bot = top + h
        ln = np.tan(np.deg2rad(lean))
        # outline: the dome, the sides falling and flaring a little, a scalloped fringe of locks
        th = np.linspace(np.pi, 2 * np.pi, 24)
        dome = [(cx + R * np.cos(t), cy + R * 0.98 * np.sin(t)) for t in th]
        side = lambda sg, ts: [(cx + sg * R * (1.0 + 0.1 * t) + ln * (bot - cy) * t, cy + (bot - cy) * t * 0.92) for t in ts]
        right = side(1, np.linspace(0.1, 1, 6))
        xs_t = np.linspace(cx + R * 1.1, cx - R * 1.1, tips * 2 + 1) + ln * (bot - cy)
        fringe = []
        for j, xt in enumerate(xs_t):
            if j % 2 == 1: fringe.append((xt + r.normal(0, w * 0.015), bot + r.normal(0, h * 0.02)))
            else: fringe.append((xt, bot - h * (0.07 + 0.03 * r.random())))
        left = side(-1, np.linspace(1, 0.1, 6))
        body = self.poly(dome + right + fringe + left, smooth=True)
        if clip is not None: body = body * clip
        tip_pts = [p for j, p in enumerate(fringe) if j % 2 == 1]
        # a translucent sheet: some of the dark shows through, lighter over the crown, warm at the hem
        val = np.clip(0.75 - 0.6 * (self.YY - top) / h, 0, 1)
        self.wash(body, ('ghost', val), body_alpha, grain=0.4, edge=0.6)
        hem = body * smoothstep(bot - h * 0.4, bot, self.YY)
        self.glaze(hem, 'glow', 0.25 * glow, 'screen')
        bb = self._bbox(body, pad=2)
        if bb is not None:                                       # the whole sheet glows a little (a soft halo)
            x0, y0, x1, y1 = bb
            self.E[y0:y1, x0:x1] += body[y0:y1, x0:x1] * 0.05 * glow
            self._bloom = None

        def flow(x, y):
            # the sheet falls from the crown like hair: away from a point just above it, turning to hang down
            a_fall = np.degrees(np.arctan2(y - (top - 0.35 * R), x - cx))
            a_down = 90 - 12 * np.clip((x - cx) / R, -1.2, 1.2) - lean
            g = smoothstep(cy - 0.2 * R, cy + 0.6 * R, y)
            return a_fall * (1 - g) + a_down * g
        shade = np.clip(1.0 - 0.75 * (self.YY - top) / h, 0, 1) * \
            (1 - 0.35 * np.clip(np.abs(self.XX - cx) / (R * 1.1), 0, 1) ** 2)
        crown = body * (self.YY < cy - 0.45 * R)
        ns = int(w * 6) if strands is None else strands
        cm = smoothstep(0.05, 0.4, self.soften(body, 2.0))
        self.strands(crown, flow, colours, n=ns, length=(h * 0.55, h * 1.05), width=(0.7, 1.3), step=3.0,
                     shade=shade, spread=0.28, curl=0.15, jitter=4, alpha=sheet, clip=cm, lock=(10, 4),
                     seed=int(r.integers(1 << 30)))
        self.strands(body, flow, colours, n=int(ns * 0.7), length=(h * 0.25, h * 0.6), width=(0.7, 1.2), step=3.0,
                     shade=shade, spread=0.28, curl=0.2, jitter=6, alpha=sheet * 0.85, clip=cm,
                     seed=int(r.integers(1 << 30)))
        # glowing eyes
        er = eye_r * w
        for sg in (-1, 1):
            ex = cx + sg * 0.22 * w + look[0] * 0.08 * w
            ey = top + 0.43 * w + look[1] * 0.06 * w
            if clip is not None and clip[int(np.clip(ey, 0, self.H - 1)), int(np.clip(ex, 0, self.W - 1))] < 0.5:
                continue
            self.dab(ex, ey, er * 2.0, 'glow', 0.25 * glow, soft=1.0)
            self.dab(ex, ey, er * 1.08, 'glow_ring', 0.95, soft=0.25)
            self.dab(ex, ey, er * 0.82, 'glow', 0.95, soft=0.3)
            self.dab(ex - er * 0.08, ey - er * 0.08, er * 0.55, 'glow_core', 1.0, soft=0.45)
            self.emit(ex, ey, er * 1.3, 0.75 * glow)
        # the glowing tips: the last part of every lock lit warm, a small elongated bead of light at its end
        for (tx, ty) in tip_pts:
            if clip is not None and clip[int(np.clip(ty - 3, 0, self.H - 1)), int(np.clip(tx, 0, self.W - 1))] < 0.5:
                continue
            paths = []
            for _ in range(5):
                ox = r.normal(0, w * 0.018)
                paths.append(np.array([(tx + ox - ln * h * 0.14, ty - h * r.uniform(0.1, 0.18)), (tx + ox, ty - h * 0.05),
                                       (tx + ox * 0.8, ty + r.uniform(-2, 1))], np.float32))
            self.lines(paths, ('glow_ring', 'glow', 'glow'), (0.7, 1.1), 0.85, 0.95, 0.45, (0.05, 0.5), k=5,
                       seed=int(r.integers(1 << 30)))
            bw, bh = max(1.4, w * 0.016), max(2.4, h * 0.036)
            self.dab(tx, ty - bh * 0.4, bw * 1.6, 'glow', 0.55, soft=0.9, ry=bh * 1.5)
            self.dab(tx, ty - bh * 0.4, bw, 'glow', 0.9, soft=0.6, ry=bh)
            self.dab(tx, ty - bh * 0.5, bw * 0.55, 'glow_core', 0.95, soft=0.6, ry=bh * 0.6)
            self.emit(tx, ty - bh * 0.5, max(2.0, w * 0.028), 0.55 * glow, ry=max(3.0, h * 0.05))
        return body

    # ================================================================== sky
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

    def stars(self, region, n=150, size=(0.5, 1.5), bright=0.06, colour='star', warm=0.15, seed=None):
        """pinpricks of light over the sky; `bright` of them larger with a faint halo"""
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
            amp = r.uniform(0.4, 1.0) * (1.0 if big else 0.75)
            self._dot(Sw if r.random() < warm else S, xs[i] + r.random(), ys[i] + r.random(), rad, amp)
            if big: self._dot(S, xs[i] + 0.5, ys[i] + 0.5, rad * 4, 0.1)
            cnt += 1
            if cnt >= n: break
        for buf, c in ((S, colour), (Sw, 'warmstar')):
            self.C += (hexc(c) - self.C) * np.clip(buf, 0, 1)[..., None]

    # ================================================================== finish and output
    def finish(self, soft=0.2, grain=1.0, tooth=1.0, bloom=1.0, lift=0.025, warmth=0.0):
        """record the finishing (applied in render, so every stage snapshot matches the final look; call it before
        the first mark): a slight softness, the bloom of what glows, a fine print grain plus a coarser tooth that
        shows in the darks, lifted blacks"""
        self.fin = dict(soft=soft, grain=grain, tooth=tooth, bloom=bloom, lift=lift, warmth=warmth)
        return self

    def render(self, rows=216):
        """the finished picture (the canvas is untouched): softened channel by channel, then bloom, grain, tooth and
        lifted blacks applied in row bands so the temporaries stay small"""
        C = self.C
        f = self.fin
        if not f: return np.clip(C, 0, 1)
        out = np.empty_like(C)
        if f['soft']:
            for c in range(3): out[..., c] = C[..., c] * (1 - f['soft']) + blur(C[..., c], 0.7) * f['soft']
        else:
            out[:] = C
        if f['bloom'] and self._bloom is None and self.E.max() > 0:
            E = self.E
            self._bloom = 0.55 * self.soften(E, 2.5)
            self._bloom += 0.4 * self.soften(E, 9.0)
            self._bloom += 0.3 * self.soften(E, 28.0)
        self._need()
        glow = np.asarray(GLOW, np.float32)
        lift = hexc('#151424')
        for y0 in range(0, self.H, rows):
            o = out[y0:y0 + rows]
            if f['bloom'] and self._bloom is not None:
                g = np.clip(self._bloom[y0:y0 + rows] * f['bloom'], 0, 4)[..., None] * glow
                o[:] = 1 - (1 - o) * np.exp(-g)
            lum = o.mean(-1, keepdims=True)
            if f['grain']:
                o *= 1 + f['grain'] * 0.022 * self._grain[y0:y0 + rows, :, None]
            if f['tooth']:
                # a printed tooth: the coarse grain lifts the darks a little (paper showing through the ink)
                dk = 1 - smoothstep(0.05, 0.5, lum)
                o += f['tooth'] * (0.035 * dk + 0.012) * self._tooth[y0:y0 + rows, :, None]
            if f['warmth']:
                o *= 1 + f['warmth'] * np.array([0.012, 0.002, -0.016], np.float32)
            if f['lift']:
                o[:] = f['lift'] * lift + o * (1 - f['lift'])
            np.clip(o, 0, 1, out=o)
        return out

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
