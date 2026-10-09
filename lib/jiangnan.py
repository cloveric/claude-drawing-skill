"""jiangnan — 江南园林 / Jiangnan Garden: a lush, finely painted spring garden illustration (numpy + Pillow only).

The look: a contemporary digital-gouache illustration of a Chinese water garden in spring. Dark grey tiled roofs
with upturned eaves, whitewashed or coral walls, jade-green lattice, red lanterns, stone steps and balustrades; and
above all plants -- trees built from thousands of small leaf-shaped dabs, blossom trees of white and pale pink
clusters, weeping willows that are curtains of fine hanging strands -- over a still jade lake that mirrors them,
with hazy blue-green hills behind and a foreground of branches framing the view. Nothing here is a filter on flat
shapes: every coloured pixel is laid by a dab, a stroke or a modelled surface, in the order a painter works.

Physical model
  order       The picture is painted back to front, as a landscape painter does: sky, far hills, haze, distant tree
              lines, the trees behind the buildings, the buildings, the garden in front of them, the water (which can
              only be painted once everything it mirrors exists), things on the water, and last the foreground
              branches that frame the view. Opaque paint covers what is under it, so the order is the occlusion.
  atmosphere  Air between the eye and a distant thing scatters a pale blue-green veil over it: the further away, the
              more its colours move toward the haze colour and the less contrast it has (`far` in 0..1 on every
              painting call). Between depth planes `haze()` lays a soft veil band, strongest where the ground meets
              the hills, so each plane separates from the one behind it.
  dabs        The unit of paint is a dab: a small opaque polygon (a pointed leaf, a rounded petal, a sword blade, a
              soft round) with its own size, angle and colour. Thousands of dabs are rasterised in one go: Pillow
              fills each polygon with its own integer id into a 2x supersampled id map (painter's order = id order,
              later dabs cover earlier ones), numpy looks every id up in a colour/alpha table and box-averages back
              to 1x, so every edge is anti-aliased and a dab costs well under a microsecond. Inside the paint a fine
              fixed canvas-tooth texture varies the value by a few percent.
  light       One sun from the upper left and a little in front (LIGHT). A foliage mass is a set of clumps (ellipses;
              later clumps are in front). Each dab asks which clump it sits on (the front-most one that contains it)
              and treats that clump as a dome: its normal gives a diffuse term, lower parts of the mass are darker
              (occlusion), and a low-frequency noise breaks it up. That 0..1 value picks the dab's colour from a ramp
              of mixed greens (deep blue-green core -> mid green -> yellow-green -> pale sunlit green).
  foliage     A tree is painted the way a gouache painter builds it: a dark underpaint (the clump cores, then big
              dark leaf dabs, so even the underpaint has a leafy edge), a body of mid-dark leaf dabs everywhere, leaves
              breaking out across the silhouette, then the light: dabs gathered in small clusters (5-14 leaves around
              a centre) where the light value is high, so each clump gets a sunny upper-left rim and a dark core, and
              finally a sprinkle of the palest dabs on the very top. Leaves point outward from their clump and droop a
              little; `veins` adds a pale midrib to the lit leaves of near shrubs. A pine is a crooked trunk with flat
              tiers of needle pads (the same model with needle-thin dabs and little droop).
  blossom     A blossom tree is a few dark branches, an underpaint of shadowed petals and dark green leaves (dabs, not
              a flat blob), twigs, a few young green leaves, then hundreds of small clusters of round petal dabs; clusters are sorted dark to light, so the
              sunlit ones lie on top of the shaded ones, and inside each cluster the petals facing the sun are paler
              -- the clustered highlights of a blooming crown, with branches showing through the gaps.
              `blossom_branch()` paints a near branch with individual five-petal flowers, buds and young leaves.
  willow      A weeping willow is a trunk, a few arching boughs hidden under a domed crown of drooping leaves, and
              many hundred hanging strands gathered in tresses (a few strands from nearly the same point, with gaps
              between tresses). A strand leaves its bough or the crown, arches out briefly and hangs down with a
              little sway; it is a hair-thin stem with small narrow leaves along it, on random sides, splayed a little
              from the stem and angled down. Strands are painted back (darker, bluer) to front (lighter,
              yellower), the lit side of the crown is brighter and the tips carry the new growth, so it reads as a
              curtain of separate strands with gaps, not a green sheet.
  roof        A hip-and-gable roof seen from the front is a surface S(u, v): u across (-1..1), v from the ridge (0) to
              the eave (1). The slope is concave (steep at the ridge, flatter and foreshortened at the eave), it widens
              toward the eave, the corners flare outward and the eave curve rises sharply at both ends (upturned
              corners). The surface is rasterised as a mesh of small quads into an id map, and every pixel's exact
              (u, v) is recovered with two Newton steps on the mesh, so the tiles can be shaded analytically: rows of
              half-round roll tiles (lit on their left flank, dark seam beside them) alternate with concave pan
              tiles, every course has a bright lip and a shadow below it, every tile has its own small value jitter.
              Round tile ends and drip tiles line the eave; under it the underside (soffit) with rafter ends and a
              soft shadow fall on the facade; a ridge with openwork and curled ends crowns it and hip ridges run down
              to the flying corner tips.
  buildings   Plaster walls are flat paint with low-frequency mottling, rain stains from the coping, a damp,
              greener base and a layer of faint brush marks. Sunlight falling through leaves leaves dappled shade on
              a sunlit surface (`dapple()`: a thresholded noise of soft cool patches, strongest near the tree that
              casts it). Lattice (grid, lantern-frame or cracked-ice pattern) is drawn as a bar mask at 3x, lit on
              its upper-left edges, shadowed on its lower-right ones, and casts a small shadow on the dark interior
              or on the paper behind it. Columns are lacquered cylinders on stone bases; lanterns are ribbed red
              ellipsoids with gold caps and tassels; plaques are framed boards with gilded characters; steps, the
              platform and the bridge are stone blocks with joints, each block with its own value. The zigzag bridge
              is real geometry: segments, slabs, piers, posts, pierced panels and rails are projected through a
              pinhole camera (`camera()`, `project()`), every face shaded by its normal and culled when it faces
              away; a rear-only balustrade keeps the deck visible from a low eye.
  water       The lake is a jade body colour, paler where it reflects the far sky. A reflection is the canvas above
              the bank mirrored about the bank line, pulled sideways by small ripples, blurred vertically (more with
              distance from the bank), darkened and mixed with the body colour (more toward the viewer, as Fresnel
              says), so it matches what stands above it, only softer and darker. Things standing in the water (the
              bridge, a boat, an egret) get their own reflection: the bridge by projecting its geometry with heights
              negated, the others by mirroring their own painted layer about their waterline. Then horizontal brush
              marks sampled from the water as painted, faint ripple lines (pale where they catch the sky, dark where
              they catch the bank) and a fine vertical streak texture. Lily pads lie on the water plane through the
              camera (ellipses foreshortened by eye height / distance) with a notch, veins, a lit far rim, a shaded
              near half and a soft shadow.
  finish      `grain()`: a slight painterly softness, a soft glow around the lights (spring haze), shadows nudged
              toward a cool blue-green, a fine grain, the faintest canvas weave and vertical streak; `seal()`: a small
              red seal with white characters, its edge worn.

API (canvas pixel coordinates; colours are names in PAINTS / RAMPS or '#rrggbb'; `far` 0 near .. 1 very far)
  surface    JiangnanGarden(W, H, seed, keep_stages, stages_dir); camera(horizon, eye, focal, cx); project(X, Y, Z);
             ground_y(Z); depth_at(y); px_per_m(Z); clipped(mask) context
  low level  dabs(xs, ys, length, width, colours, angle, shape, alpha, far); stroke(path, w0, w1, colour);
             fill(mask, colour, alpha); poly(pts) / ellipse(cx, cy, rx, ry) masks; crown(cx, cy, w, h, n) -> clumps
  air        sky(top, bottom, y1, clouds); hills(ridge, base, colour, far); haze(y0, y1, y2, colour, strength)
  plants     foliage(clumps, ramp, leaf, density, far, light, droop, veins); blossom_tree(branches, clumps, kind,
             petal, far); blossom_branch(path, w0, w1, kind, flowers); willow(trunk, boughs, strands, length, ramp,
             leaf, far, crown, tips); pine(trunk, limbs, pads); branch(path, w0, w1); reeds(x0, x1, y, n, height);
             petals(region, n, kind, water); rock(cx, cy, rx, ry); pot(x, y, w, h, colour)
  buildings  wall(x0, y0, x1, y1, colour); dapple(x0, y0, x1, y1, amount, falloff, mask); roof(cx, y_ridge, y_eave,
             ridge_w, eave_w, upturn, flare); coping(x0, x1, y, h); column(x, y0, y1, w); beam(x0, x1, y0, y1);
             lattice(x0, y0, x1, y1, pattern, kind, back); fretwork(x0, x1, y0, h); round_window(cx, cy, r, ring,
             pattern | inside, ground);
             stonework(x0, y0, x1, y1); steps(x0, x1, y, n, rise, tread); bridge(path, width, deck, rail,
             reflection, rails); lantern(x, y, h); plaque(cx, cy, w, h, text)
  water      lake(y0, y1, far_colour, near_colour, bank); reflect(bank, strength, blur, ripple, src); layer() +
             reflect_layer(before, axis, box); ripples(box, n, brush); lily_pads(pads, flowers); lotus(x, y, s);
             boat(x0, x1, y, h); egret(x, y, s, pose)
  finish     seal(x, y, w, h, text); grain(amount); render(); composite(); stage(name); save(path, stages_dir)

    import sys; sys.path.insert(0, 'lib')
    from jiangnan import JiangnanGarden
    g = JiangnanGarden(1920, 1080, seed=3)
    g.camera(horizon=450, eye=3.0, focal=1400)
    g.sky(); g.hills([(0, 300), (500, 220), (1100, 280), (1920, 240)], base=520, far=0.8)
    g.foliage(g.crown(600, 380, 420, 220, n=14), 'jade', leaf=(4, 7), far=0.3)
    g.roof(960, 300, 400, 360, 640, upturn=44, flare=26)
    g.lake(600, 1080, bank=600); g.reflect(600)
    g.seal(1840, 980, 26, 46, '春水'); g.grain(); g.save('garden.jpg')
"""
import io
import os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, blob_pts, cjk_font


PAINTS = {
    'sky': '#7fa6c2', 'sky_low': '#cbdcd8', 'haze': '#b7cbc5', 'cloud': '#f3f4ef',
    'plaster': '#efebe2', 'coral': '#d8695b', 'jade': '#3f8b73', 'jade_dark': '#1f5244', 'jade_light': '#86c3a8',
    'lacquer': '#a3402f', 'beam': '#5b3128', 'interior': '#1d2a27', 'paper': '#e8e1cc',
    'stone': '#bdb9ab', 'tile': '#46524f', 'board': '#2c2620', 'gold': '#d9b45c', 'wood': '#6e5038',
    'lantern': '#d63a2a', 'seal': '#b9312a', 'bark': '#3f332e', 'bark_light': '#8c7c6c',
    'water': '#5c9d8c', 'water_deep': '#2e6c60', 'water_far': '#94c0b3',
    'terracotta': '#b8663f', 'porcelain': '#dfe6e6', 'egret': '#f6f5f0',
}

RAMPS = {
    'spring': ['#18302a', '#284a36', '#3f6a3c', '#638a43', '#97b45a', '#cbd98e'],
    'jade':   ['#11262a', '#1b3c3a', '#2a594c', '#467a59', '#759f6e', '#adc795'],
    'deep':   ['#0b1d1a', '#13302a', '#1f4b37', '#3a7041', '#6f9c56', '#aac884'],
    'olive':  ['#25301e', '#3a4829', '#566834', '#7c8f46', '#a8b664', '#d0d897'],
    'willow': ['#1b372d', '#2e512f', '#4a6f33', '#6f9240', '#9cb75e', '#cbd996'],
    'far':    ['#4c6e69', '#5f8078', '#759384', '#8ea891', '#a9bea4', '#c6d4bc'],
    'white':  ['#7d8584', '#a6a8ab', '#cbc6ca', '#e8e1e0', '#f8f3ee', '#fffefa'],
    'pink':   ['#9a4d68', '#bd6c88', '#dc93a8', '#efb6c3', '#f8d4db', '#fff0f1'],
    'azalea': ['#7a2a45', '#a73d5f', '#cf5d80', '#e886a2', '#f5b0c3', '#fdd9e2'],
    'tile':   ['#20272b', '#323d42', '#4a5759', '#6b7a79', '#95a3a0', '#bfcac6'],
    'stone':  ['#5d5c55', '#7d7c72', '#9d9b8f', '#bdbaad', '#d7d4c7', '#ecebe0'],
    'rock':   ['#4f5552', '#6c716c', '#8b8f88', '#aaada4', '#c8cac0', '#e3e4da'],
    'pad':    ['#1c3a33', '#2b5440', '#3f6f46', '#5f8c4c', '#8fae62', '#c0d18e'],
}
LIGHT = (-0.52, -0.62, 0.58)          # toward the sun: left, up (screen y is down) and toward the viewer

_LEAF = np.array([(1, 0), (0.62, 0.36), (0.15, 0.5), (-0.35, 0.44), (-0.78, 0.24), (-1, 0), (-0.78, -0.24),
                  (-0.35, -0.44), (0.15, -0.5), (0.62, -0.36)], np.float32)
_t = np.linspace(0, 2 * np.pi, 10, endpoint=False)
_ROUND = np.stack([np.cos(_t), 0.5 * np.sin(_t)], 1).astype(np.float32)
_BLADE = np.array([(1, 0), (0.55, 0.36), (-0.2, 0.5), (-0.8, 0.42), (-1, 0.15), (-1, -0.15), (-0.8, -0.42),
                   (-0.2, -0.5), (0.55, -0.36)], np.float32)
_t = np.linspace(0, 2 * np.pi, 7, endpoint=False)
_DOT = np.stack([np.cos(_t), 0.5 * np.sin(_t)], 1).astype(np.float32)
SHAPES = {'leaf': _LEAF, 'round': _ROUND, 'blade': _BLADE, 'dot': _DOT}


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    a, b = hexc(a), hexc(b)
    return (a + (b - a) * t).astype(np.float32)


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


def _blur1(a, sigma, axis):
    """gaussian-ish blur along one axis (3 box passes via cumulative sums)"""
    if sigma <= 0.3: return a.astype(np.float32)
    w = int(np.sqrt(12 * sigma * sigma / 3 + 1)); w += (w % 2 == 0); r = w // 2
    out = a.astype(np.float32)
    for _ in range(3):
        pad = [(0, 0)] * out.ndim; pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(out, pad, mode='edge'), axis=axis, dtype=np.float64)
        n = c.shape[axis]
        out = ((np.take(c, np.arange(w, n), axis=axis) - np.take(c, np.arange(0, n - w), axis=axis)) / w).astype(np.float32)
    return out


def _tube(path, w0, w1=None, per=6, wob=0.0, seed=0):
    """outline polygon of a thick path (width w0 at the start -> w1 at the end)"""
    P = np.asarray(path, np.float32)
    Q = spline(P, per) if len(P) > 2 else np.stack([np.linspace(P[0, 0], P[-1, 0], 8), np.linspace(P[0, 1], P[-1, 1], 8)], 1)
    w1 = w0 if w1 is None else w1
    d = np.gradient(Q, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    hw = np.linspace(w0, w1, len(Q))[:, None] / 2
    if wob: hw = hw * (1 + wob * fbm1d(len(Q), 12, 3, seed)[:, None])
    L, R = Q + nrm * hw, Q - nrm * hw
    tip = [Q[-1] + d[-1] * hw[-1, 0] * 0.6]
    base = [Q[0] - d[0] * hw[0, 0] * 0.4]
    return np.vstack([L, tip, R[::-1], base]).astype(np.float32), Q, nrm


class JiangnanGarden:
    PAINTS = PAINTS
    RAMPS = RAMPS
    LIGHT = LIGHT

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = hexc('sky_low')
        r = np.random.default_rng(seed + 11)
        t = blur(r.random((H, W)).astype(np.float32), 0.6)
        self.TX = ((t - t.mean()) / (t.std() + 1e-6)).astype(np.float32)          # canvas tooth inside the paint
        self.N1 = noise2d(H, W, 46, 3, seed + 12)                                   # light breakup for masses
        L = np.asarray(LIGHT, np.float32); self.L = L / np.linalg.norm(L)
        self.haze_col = hexc('haze')
        self._clip = None
        self.grain_amt = 0.0
        self.camera()

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== camera (for things on the water plane)
    def camera(self, horizon=450.0, eye=3.0, focal=1400.0, cx=None):
        """pinhole camera over the lake: eye height in metres, horizon row, focal length in px"""
        self.cam = (float(horizon), float(eye), float(focal), float(self.W / 2 if cx is None else cx))

    def project(self, X, Y, Z):
        """world metres (X right, Y up from the water, Z away from the eye) -> canvas px"""
        hz, e, f, cx = self.cam
        X, Y, Z = (np.asarray(v, np.float32) for v in (X, Y, Z))
        return cx + f * X / Z, hz + f * (e - Y) / Z

    def ground_y(self, Z):
        hz, e, f, _ = self.cam
        return hz + f * e / np.asarray(Z, np.float32)

    def depth_at(self, y):
        hz, e, f, _ = self.cam
        return f * e / np.maximum(np.asarray(y, np.float32) - hz, 1e-3)

    def px_per_m(self, Z):
        return self.cam[2] / np.asarray(Z, np.float32)

    # ================================================================== the dab rasteriser
    @contextmanager
    def clipped(self, mask):
        """paint only inside mask (e.g. the view through a moon gate)"""
        old = self._clip
        self._clip = mask if old is None else mask * old
        try: yield
        finally: self._clip = old

    def _far(self, cols, far):
        if not far: return cols
        a = 0.82 * float(np.clip(far, 0, 1)) ** 0.9
        lum = cols.mean(-1, keepdims=True)
        c = lum + (cols - lum) * (1 - 0.35 * far)
        return c * (1 - a) + self.haze_col * a

    def _paint(self, groups, ss=2, tex=0.04):
        """rasterise groups of polygons in order: [(P, colours, alpha), ...]; P is (N, k, 2) or a list of (k, 2)"""
        groups = [g for g in groups if g is not None and len(g[0])]
        if not groups: return
        lo = np.array([1e9, 1e9]); hi = np.array([-1e9, -1e9])
        for P, _, _ in groups:
            if isinstance(P, np.ndarray):
                lo = np.minimum(lo, P.reshape(-1, 2).min(0)); hi = np.maximum(hi, P.reshape(-1, 2).max(0))
            else:
                for p in P:
                    lo = np.minimum(lo, np.min(p, 0)); hi = np.maximum(hi, np.max(p, 0))
        x0, y0 = max(0, int(np.floor(lo[0])) - 1), max(0, int(np.floor(lo[1])) - 1)
        x1, y1 = min(self.W, int(np.ceil(hi[0])) + 2), min(self.H, int(np.ceil(hi[1])) + 2)
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        cols_all, alph_all = [np.zeros((1, 3), np.float32)], [np.zeros(1, np.float32)]
        idx = 1
        off = np.array([x0, y0], np.float32)
        for P, cols, alpha in groups:
            if isinstance(P, np.ndarray):
                Q = ((P - off) * ss).reshape(len(P), -1).tolist()
            else:
                Q = [((np.asarray(p, np.float32) - off) * ss).ravel().tolist() for p in P]
            n = len(Q)
            for q in Q:
                if len(q) >= 6: d.polygon(q, fill=idx)
                idx += 1
            cols_all.append(np.broadcast_to(np.asarray(cols, np.float32), (n, 3)))
            alph_all.append(np.broadcast_to(np.asarray(alpha, np.float32), (n,)))
        cols = np.concatenate(cols_all); alph = np.concatenate(alph_all)
        pal = np.empty((idx, 4), np.float32)
        pal[:, :3] = np.clip(cols, 0, 1) * alph[:, None]; pal[:, 3] = alph
        ids = np.asarray(im)
        Cs = self.C[y0:y1, x0:x1]
        for r0 in range(0, h, 200):
            r1 = min(h, r0 + 200)
            look = pal[ids[r0 * ss:r1 * ss]].reshape(r1 - r0, ss, w, ss, 4).mean((1, 3))
            A = look[..., 3]; Pm = look[..., :3]
            if self._clip is not None:
                f = self._clip[y0 + r0:y0 + r1, x0:x1]; A = A * f; Pm = Pm * f[..., None]
            if tex: Pm = Pm * (1 + tex * self.TX[y0 + r0:y0 + r1, x0:x1, None])
            Cs[r0:r1] = Cs[r0:r1] * (1 - A[..., None]) + Pm

    def _shapes(self, xs, ys, length, width, angle, shape='leaf', jitter=0.08, r=None):
        """(N, k, 2) polygons of dabs"""
        r = r if r is not None else self._r()
        T = SHAPES[shape] if isinstance(shape, str) else np.asarray(shape, np.float32)
        n = len(xs)
        Lh = np.broadcast_to(np.asarray(length, np.float32), (n,))[:, None] / 2
        Wd = np.broadcast_to(np.asarray(width, np.float32), (n,))[:, None]
        a = np.broadcast_to(np.asarray(angle, np.float32), (n,))[:, None]
        jit = 1 + jitter * r.normal(0, 1, (n, len(T))).astype(np.float32)
        lx = T[None, :, 0] * Lh * jit; ly = T[None, :, 1] * Wd * jit
        c, s = np.cos(a), np.sin(a)
        P = np.empty((n, len(T), 2), np.float32)
        P[..., 0] = np.asarray(xs, np.float32)[:, None] + lx * c - ly * s
        P[..., 1] = np.asarray(ys, np.float32)[:, None] + lx * s + ly * c
        return P

    def dabs(self, xs, ys, length, width, colours, angle=0.0, shape='leaf', alpha=1.0, far=0.0, ss=2, tex=0.04, seed=None):
        """paint many dabs at once (angles in radians)"""
        cols = self._far(np.broadcast_to(np.asarray(colours, np.float32), (len(xs), 3)).copy(), far)
        self._paint([(self._shapes(xs, ys, length, width, angle, shape, r=self._r(seed)), cols, alpha)], ss, tex)

    def stroke(self, path, w0, w1=None, colour='bark', alpha=1.0, far=0.0, wob=0.0, ss=2):
        """one tapered stroke along a path"""
        P, _, _ = _tube(path, w0, w1, wob=wob, seed=int(self.rng.integers(1 << 30)))
        self._paint([([P], self._far(hexc(colour)[None], far), alpha)], ss)

    def fill(self, mask, colour, alpha=1.0, sl=None):
        """flat paint through a float mask (full canvas, or the region sl)"""
        sl = sl or (slice(None), slice(None))
        A = mask[sl] * alpha if mask.shape[:2] == self.C.shape[:2] else mask * alpha
        if self._clip is not None: A = A * self._clip[sl]
        Cs = self.C[sl]
        col = np.asarray(colour, np.float32) if np.ndim(colour) == 3 else hexc(colour)
        Cs += (col - Cs) * A[..., None]

    def poly(self, pts, ss=2):
        im = Image.new('L', (self.W * ss, self.H * ss), 0)
        ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in pts], fill=255)
        if ss > 1: im = im.resize((self.W, self.H), Image.BOX)
        return np.asarray(im, np.float32) / 255

    def ellipse(self, cx, cy, rx, ry=None):
        ry = rx if ry is None else ry
        yy = np.arange(self.H, dtype=np.float32)[:, None]; xx = np.arange(self.W, dtype=np.float32)[None, :]
        dd = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        e = 1.0 / max(1.5, min(rx, ry))
        return smoothstep(1 + e, 1 - e, dd).astype(np.float32)

    # ================================================================== sky, hills, haze
    def sky(self, top='sky', bottom='sky_low', y1=None, clouds=0.5, seed=None):
        """soft spring sky: a slightly desaturated blue going pale toward the horizon, thin clouds, broad soft dabs"""
        r = self._r(seed)
        y1 = self.H * 0.5 if y1 is None else y1
        yy = np.arange(self.H, dtype=np.float32)
        t = smoothstep(-0.1 * y1, y1, yy) ** 0.85
        col = hexc(top)[None] * (1 - t[:, None]) + hexc(bottom)[None] * t[:, None]
        self.C[:] = col[:, None, :]
        if clouds:
            n = noise2d(self.H, self.W, 260, 4, int(r.integers(1 << 30)))
            n2 = noise2d(self.H, self.W, 60, 3, int(r.integers(1 << 30)))
            band = smoothstep(0.0, 0.25 * y1, yy)[:, None] * (1 - smoothstep(0.75 * y1, 1.05 * y1, yy))[:, None]
            a = smoothstep(0.52, 0.82, n * 0.85 + n2 * 0.15) * band * clouds
            self.fill(a, 'cloud', 0.7)
            self.fill(smoothstep(0.62, 0.9, n) * band * clouds, mix('cloud', '#c9cfd8', 0.6), 0.25)
        k = 380
        xs = r.uniform(-60, self.W + 60, k); ys = r.uniform(-40, y1 * 1.1, k)
        tt = np.clip(smoothstep(-0.1 * y1, y1, ys) ** 0.85, 0, 1)[:, None]
        cc = hexc(top)[None] * (1 - tt) + hexc(bottom)[None] * tt + r.normal(0, 0.012, (k, 3))
        L = r.uniform(80, 220, k)
        self.dabs(xs, ys, L, L * r.uniform(0.25, 0.45, k), cc, r.normal(0, 0.12, k), 'round', alpha=0.22, ss=1, tex=0.02)

    def hills(self, ridge, base=None, colour='#7f9f98', far=0.7, trees=1.0, light=0.0, seed=None):
        """a hazy range: filled ridge, slopes shaded by an embossed noise, a tree-bumped silhouette and tiny dabs"""
        r = self._r(seed)
        Q = spline(np.asarray(ridge, np.float32), 24)
        base = self.H if base is None else base
        pts = np.vstack([Q, [(Q[-1, 0], base), (Q[0, 0], base)]])
        m = self.poly(pts)
        y0 = int(max(0, Q[:, 1].min() - 12)); sl = (slice(y0, int(base)), slice(None))
        h = int(base) - y0
        n = noise2d(h, self.W, 70, 4, int(r.integers(1 << 30)))
        emb = (np.roll(n, 3, 1) - np.roll(n, -3, 1)) * 0.8 + (np.roll(n, 3, 0) - np.roll(n, -3, 0)) * 0.6
        yy = np.arange(y0, base, dtype=np.float32)[:, None]
        ridge_y = np.interp(np.arange(self.W), Q[:, 0], Q[:, 1])[None]
        depth = np.clip((yy - ridge_y) / max(1.0, h * 0.8), 0, 1)
        sh = np.clip(0.5 + 2.2 * emb + light - 0.25 * depth, 0, 1)
        base_c = hexc(colour)
        dark, lite = base_c * 0.82, mix(base_c, '#e8eee2', 0.22)
        col = dark * (1 - sh[..., None]) + lite * sh[..., None]
        col = col * (1 - depth[..., None] * 0.35) + self.haze_col * depth[..., None] * 0.35
        col = self._far(col, far)
        A = m[sl] * smoothstep(base, base - 60, yy)
        if self._clip is not None: A = A * self._clip[sl]
        self.C[sl] += (col - self.C[sl]) * A[..., None]
        if trees:
            k = int(len(Q) * 1.6 * trees)
            i = r.integers(0, len(Q), k)
            xs = Q[i, 0] + r.normal(0, 2, k); ys = Q[i, 1] + r.uniform(-3, 7, k)
            s = r.uniform(4, 11, k) * (0.6 + 0.6 * (1 - far))
            cc = self._far(np.repeat(mix(base_c, '#e8eee2', 0.05)[None], k, 0) * r.uniform(0.86, 1.04, (k, 1)), far)
            self._paint([(self._shapes(xs, ys, s, s * 0.8, 0, 'round', 0.15, r), cc, 0.95)], 2, 0.02)
            k = int(h * self.W / 90 * trees)
            xs = r.uniform(0, self.W, k); ys = r.uniform(y0, base, k)
            inside = m[ys.astype(int).clip(0, self.H - 1), xs.astype(int).clip(0, self.W - 1)] > 0.5
            xs, ys = xs[inside], ys[inside]
            if len(xs):
                iy = (ys - y0).astype(int).clip(0, h - 1); ix = xs.astype(int).clip(0, self.W - 1)
                c = col[iy, ix] * r.uniform(0.94, 1.05, (len(xs), 1))
                s = r.uniform(3, 7, len(xs)) * (0.6 + 0.6 * (1 - far))
                self._paint([(self._shapes(xs, ys, s, s * 0.8, 0, 'round', 0.15, r), c, 0.8)], 2, 0.02)
        return m

    def haze(self, y0, y1, y2=None, colour='haze', strength=0.6, mask=None, seed=None):
        """a veil of air: rising from 0 at y0 to `strength` at y1, fading out again by y2 (if given)"""
        r = self._r(seed)
        a0, a1 = int(max(0, y0)), int(min(self.H, y2 if y2 is not None else self.H))
        yy = np.arange(a0, a1, dtype=np.float32)[:, None]
        a = smoothstep(y0, y1, yy)
        if y2 is not None: a = a * (1 - smoothstep(y1, y2, yy))
        n = noise2d(a1 - a0, self.W, 160, 3, int(r.integers(1 << 30)))
        a = a * strength * (0.75 + 0.5 * n)
        if mask is not None: a = a * mask[a0:a1]
        if self._clip is not None: a = a * self._clip[a0:a1]
        Cs = self.C[a0:a1]
        Cs += (hexc(colour) - Cs) * a[..., None]

    # ================================================================== plants
    def crown(self, cx, cy, w, h, n=12, size=(0.26, 0.46), seed=None, flat=0.85):
        """clumps (cx, cy, rx, ry) filling an ellipse, sorted so the lower ones are in front"""
        r = self._r(seed)
        out = [(cx, cy + h * 0.05, w * 0.3, h * 0.32)]
        for i in range(n):
            s = r.uniform(*size) * (0.75 if i > n * 0.6 else 1.0)
            a = r.uniform(0, 2 * np.pi)
            d = (0.35 + 0.65 * np.sqrt(r.uniform(0, 1))) * (1 - s * 0.75)
            x = cx + np.cos(a) * d * w / 2; y = cy + np.sin(a) * d * h / 2 * (0.8 if np.sin(a) > 0 else 1.0)
            rx = s * w / 2; out.append((x, y, rx, rx * r.uniform(flat - 0.15, flat + 0.05)))
        out = np.array(out, np.float32)
        return out[np.argsort(out[:, 1] + r.normal(0, h * 0.06, len(out)))]

    def _lit(self, x, y, K, light=None):
        """light value 0..1 of points on a clumped mass, the owning clump and the normalised radius on it"""
        Lv = self.L if light is None else light
        n = len(x)
        dif = np.empty(n, np.float32); own = np.empty(n, np.int32); dd = np.empty(n, np.float32)
        dmin = np.empty(n, np.float32)
        for a in range(0, n, 20000):
            b = min(n, a + 20000)
            qx = (x[a:b, None] - K[None, :, 0]) / K[None, :, 2]
            qy = (y[a:b, None] - K[None, :, 1]) / K[None, :, 3]
            d2 = qx * qx + qy * qy
            inside = d2 < 1
            anyin = inside.any(1)
            o = np.where(anyin, K.shape[0] - 1 - np.argmax(inside[:, ::-1], 1), np.argmin(d2, 1))
            ar = np.arange(b - a)
            ox, oy = qx[ar, o], qy[ar, o]
            dr = np.sqrt(ox * ox + oy * oy)
            nz = np.sqrt(np.clip(1 - np.minimum(dr, 1) ** 2, 0.04, 1))
            nn = np.stack([ox, oy, nz], 1); nn /= np.linalg.norm(nn, axis=1, keepdims=True)
            dif[a:b] = np.clip(nn @ Lv, 0, 1)
            own[a:b] = o; dd[a:b] = dr; dmin[a:b] = np.sqrt(d2.min(1))
        return dif, own, dd, dmin

    def _noise_at(self, x, y):
        return self.N1[np.clip(y.astype(np.int32), 0, self.H - 1), np.clip(x.astype(np.int32), 0, self.W - 1)]

    def _sample(self, K, n, r, dmax=1.0, dmin_=0.0):
        """n points on the clumped mass (normalised distance to the nearest clump in [dmin_, dmax], with a ragged rim)"""
        x0 = (K[:, 0] - K[:, 2]).min() * 1.0 - 4; x1 = (K[:, 0] + K[:, 2]).max() + 4
        y0 = (K[:, 1] - K[:, 3]).min() - 4; y1 = (K[:, 1] + K[:, 3]).max() + 4
        xs, ys = [], []
        got, tries = 0, 0
        while got < n and tries < 12:
            m = int((n - got) * 2.5) + 64
            x = r.uniform(x0, x1, m).astype(np.float32); y = r.uniform(y0, y1, m).astype(np.float32)
            dm = np.full(m, 9.0, np.float32)
            for k in K:
                dm = np.minimum(dm, np.sqrt(((x - k[0]) / k[2]) ** 2 + ((y - k[1]) / k[3]) ** 2))
            dm = dm * (1 + 0.16 * (self._noise_at(x, y) - 0.5))
            ok = (dm <= dmax) & (dm >= dmin_)
            xs.append(x[ok]); ys.append(y[ok]); got += int(ok.sum()); tries += 1
        x = np.concatenate(xs)[:n]; y = np.concatenate(ys)[:n]
        return x, y

    def _area(self, K, r):
        x0 = (K[:, 0] - K[:, 2]).min(); x1 = (K[:, 0] + K[:, 2]).max()
        y0 = (K[:, 1] - K[:, 3]).min(); y1 = (K[:, 1] + K[:, 3]).max()
        m = 6000
        x = r.uniform(x0, x1, m); y = r.uniform(y0, y1, m)
        dm = np.full(m, 9.0)
        for k in K: dm = np.minimum(dm, ((x - k[0]) / k[2]) ** 2 + ((y - k[1]) / k[3]) ** 2)
        return float((dm < 1).mean() * (x1 - x0) * (y1 - y0))

    def _light_value(self, x, y, K, occl=0.35, light=0.0, noise=0.16):
        dif, own, dd, dmin = self._lit(x, y, K)
        ytop = (K[:, 1] - K[:, 3]).min(); ybot = (K[:, 1] + K[:, 3]).max()
        vert = np.clip((y - ytop) / max(1.0, ybot - ytop), 0, 1)
        l = 0.1 + 0.9 * dif
        l = l * (1 - occl * vert ** 1.3) + noise * (self._noise_at(x, y) - 0.5) + light
        return np.clip(l, 0, 1), own, dd, dmin

    def _leaf_angle(self, x, y, K, own, droop, r):
        ox = x - K[own, 0]; oy = y - K[own, 1]
        nrm = np.sqrt(ox * ox + oy * oy) + 1e-3
        vx = ox / nrm * (1 - droop); vy = oy / nrm * (1 - droop) + droop
        return np.arctan2(vy, vx) + r.normal(0, 0.55, len(x))

    def foliage(self, clumps, ramp_='spring', leaf=(5, 9), density=1.0, far=0.0, light=0.0, droop=0.35,
                highlights=1.0, edge=1.0, aspect=0.48, shape='leaf', occl=0.35, veins=False, under=True,
                tex=0.05, seed=None):
        """a foliage mass built from leaf dabs: dark underpaint, mid body, leaves across the rim, lit clusters, sparkle"""
        r = self._r(seed)
        K = np.asarray(clumps, np.float32).reshape(-1, 4)
        R = ramp(ramp_)
        L0, L1 = leaf; la = 0.5 * (L0 + L1)
        area = self._area(K, r)
        groups = []
        jit = lambda n: r.normal(0, 0.016, (n, 3)).astype(np.float32)
        if under:
            polys = [blob_pts(k[0], k[1], k[2] * 0.7, k[3] * 0.7, 0.14, 40, int(r.integers(1 << 20))) for k in K]
            yk = (K[:, 1] - K[:, 1].min()) / max(1.0, np.ptp(K[:, 1]))
            cols = ramp_at(R, 0.04 + 0.1 * (1 - yk) + light * 0.4)
            groups.append((polys, self._far(cols, far), 1.0))
            n0 = int(area / (la * la * aspect * 3.2) * 1.2 * density)
            x, y = self._sample(K, n0, r, 0.97)
            l, own, dd, dmin = self._light_value(x, y, K, occl, light)
            Ls = r.uniform(L0, L1, len(x)) * 1.7
            groups.append((self._shapes(x, y, Ls, Ls * aspect, self._leaf_angle(x, y, K, own, droop, r), shape, 0.1, r),
                           self._far(ramp_at(R, l * 0.42 + r.uniform(-0.04, 0.05, len(x))) + jit(len(x)), far), 1.0))
        # body
        n1 = int(area / (la * la * aspect) * 1.5 * density)
        x, y = self._sample(K, n1, r, 1.0)
        l, own, dd, dmin = self._light_value(x, y, K, occl, light)
        cols = ramp_at(R, l * 0.78 + r.uniform(-0.07, 0.07, len(x))) + jit(len(x))
        Ls = r.uniform(L0, L1, len(x))
        groups.append((self._shapes(x, y, Ls, Ls * aspect, self._leaf_angle(x, y, K, own, droop, r), shape, 0.08, r),
                       self._far(cols, far), 1.0))
        # leaves across the silhouette
        if edge:
            n2 = int(np.sqrt(area) * 2.4 * edge * density * 6 / la)
            x, y = self._sample(K, n2, r, 1.13, 0.86)
            l, own, dd, dmin = self._light_value(x, y, K, occl, light)
            cols = ramp_at(R, l * 0.9 + r.uniform(-0.06, 0.06, len(x))) + jit(len(x))
            Ls = r.uniform(L0, L1 * 1.1, len(x))
            groups.append((self._shapes(x, y, Ls, Ls * aspect, self._leaf_angle(x, y, K, own, droop * 0.6, r), shape, 0.08, r),
                           self._far(cols, far), 1.0))
        # light, in clusters
        nc = int(area / (la * la * aspect) * 0.11 * highlights * density)
        cx, cy = self._sample(K, nc * 3, r, 1.0)
        lc, own, dd, dmin = self._light_value(cx, cy, K, occl, light)
        keep = r.random(len(cx)) < smoothstep(0.4, 0.85, lc)
        cx, cy, lc = cx[keep][:nc], cy[keep][:nc], lc[keep][:nc]
        if len(cx):
            m = r.integers(5, 15, len(cx))
            ci = np.repeat(np.arange(len(cx)), m)
            x = cx[ci] + r.normal(0, la * 1.1, len(ci)); y = cy[ci] + r.normal(0, la * 0.9, len(ci))
            l2, own, dd, dmin = self._light_value(x, y, K, occl, light)
            ok = dmin < 1.06
            x, y, l2, own, ci = x[ok], y[ok], l2[ok], own[ok], ci[ok]
            o = np.argsort(lc[ci])
            x, y, l2, own, ci = x[o], y[o], l2[o], own[o], ci[o]
            ll = 0.5 * lc[ci] + 0.45 * l2 + 0.1 + r.uniform(-0.09, 0.07, len(x))
            cols = ramp_at(R, ll) + jit(len(x))
            Ls = r.uniform(L0 * 0.85, L1 * 0.95, len(x))
            groups.append((self._shapes(x, y, Ls, Ls * aspect, self._leaf_angle(x, y, K, own, droop, r), shape, 0.08, r),
                           self._far(cols, far), 1.0))
            if veins:
                sel = ll > 0.62
                xv, yv = x[sel], y[sel]
                av = self._leaf_angle(xv, yv, K, own[sel], droop, r)
                groups.append((self._shapes(xv, yv, Ls[sel] * 0.75, Ls[sel] * 0.07, av, 'leaf', 0.0, r),
                               self._far(ramp_at(R, ll[sel] + 0.2), far), 0.5))
            # sparkle: the palest dabs on the very top of the light
            sel = ll > 0.82
            if sel.any():
                xs_, ys_ = x[sel], y[sel]
                k = len(xs_)
                Ls = r.uniform(L0 * 0.6, L0 * 1.0, k)
                groups.append((self._shapes(xs_ + r.normal(0, 1.5, k), ys_ + r.normal(0, 1.5, k), Ls, Ls * aspect,
                                            r.uniform(0, np.pi, k), shape, 0.1, r),
                               self._far(ramp_at(R, np.full(k, 0.97)) + jit(k), far), 0.9))
        self._paint(groups, 2, tex)

    def branch(self, path, w0, w1=None, colour='bark', lit='bark_light', far=0.0, light=0.55, wob=0.12, ss=2):
        """a woody limb: dark tube, a lit flank toward the sun, a few bark marks"""
        r = self._r()
        P, Q, nrm = _tube(path, w0, w1, wob=wob, seed=int(r.integers(1 << 30)))
        groups = [([P], self._far(hexc(colour)[None], far), 1.0)]
        w1 = w0 if w1 is None else w1
        hw = np.linspace(w0, w1, len(Q)) / 2
        side = np.sign((nrm @ self.L[:2]).mean() + 1e-6)
        lp = Q + nrm * side * hw[:, None] * 0.42
        if len(Q) > 3 and light > 0:
            P2, _, _ = _tube(lp[::max(1, len(lp) // 12)], w0 * 0.42, w1 * 0.3)
            groups.append(([P2], self._far(hexc(lit)[None], far), light))
        self._paint(groups, ss)

    def blossom_tree(self, branches, clumps, kind='white', petal=(3.0, 5.5), density=1.0, far=0.0, leaves=0.14,
                     light=0.0, twigs=1.0, occl=0.3, gaps=0.35, seed=None):
        """a tree in bloom: branches, shadow underpaint, twigs, young leaves, then clusters of petal dabs dark -> light"""
        r = self._r(seed)
        K = np.asarray(clumps, np.float32).reshape(-1, 4)
        R = ramp(kind)
        G = ramp('spring')
        for b in branches: self.branch(b[0], b[1], b[2], far=far)
        p0, p1 = petal; pa = 0.5 * (p0 + p1)
        area = self._area(K, r)
        groups = []
        polys = [blob_pts(k[0], k[1], k[2] * 0.55, k[3] * 0.55, 0.2, 36, int(r.integers(1 << 20))) for k in K]
        sh = mix(ramp_at(R, 0.08), '#3c5a46', 0.6)
        groups.append((polys, self._far(np.repeat(sh[None], len(K), 0) * r.uniform(0.9, 1.06, (len(K), 1)), far), 1.0))
        n0 = int(area / (pa * pa * 3.0) * 1.1 * density)
        x, y = self._sample(K, n0, r, 0.95)
        l, own, dd, dmin = self._light_value(x, y, K, occl, light)
        Ls = r.uniform(p0 * 1.5, p1 * 1.9, len(x))
        green = r.random(len(x)) < 0.45
        cu = np.where(green[:, None], ramp_at(G, l * 0.38 + 0.04), ramp_at(R, l * 0.3 + 0.04) * 0.92 + hexc('#3c5a46') * 0.08)
        groups.append((self._shapes(x, y, Ls, Ls * np.where(green, 0.45, 0.6), r.uniform(0, np.pi, len(x)), 'leaf', 0.12, r),
                       self._far(cu, far), 1.0))
        self._paint(groups, 2); groups = []
        if twigs:
            tw = []
            for k in K:
                for _ in range(int(3 * twigs)):
                    a = r.uniform(0, 2 * np.pi); L = r.uniform(0.5, 1.0)
                    p0_ = (k[0] + r.normal(0, k[2] * 0.2), k[1] + r.normal(0, k[3] * 0.2))
                    p1_ = (p0_[0] + np.cos(a) * k[2] * L, p0_[1] + np.sin(a) * k[3] * L)
                    mid = ((p0_[0] + p1_[0]) / 2 + r.normal(0, 4), (p0_[1] + p1_[1]) / 2 + r.normal(0, 4))
                    tw.append(_tube([p0_, mid, p1_], max(1.2, pa * 0.45), 0.6)[0])
            groups.append((tw, self._far(hexc('bark')[None] * 1.1, far), 0.9))
        if leaves:
            nl = int(area / (pa * pa) * 0.22 * leaves * density)
            x, y = self._sample(K, nl, r, 1.0)
            l, own, dd, dmin = self._light_value(x, y, K, occl, light)
            Ls = r.uniform(p0 * 1.3, p1 * 1.6, len(x))
            groups.append((self._shapes(x, y, Ls, Ls * 0.45, r.uniform(0, np.pi, len(x)), 'leaf', 0.08, r),
                           self._far(ramp_at(G, 0.25 + 0.6 * l), far), 1.0))
        # clusters of petals
        rc = pa * 3.2
        nc = int(area / (np.pi * rc * rc) * 4.0 * density)
        cx, cy = self._sample(K, nc, r, 1.02)
        lc, own, dd, dmin = self._light_value(cx, cy, K, occl, light)
        if gaps:
            keep = (self._noise_at(cx * 1.7 % self.W, cy * 1.7 % self.H) > gaps * 0.55) | (lc > 0.55)
            cx, cy, lc = cx[keep], cy[keep], lc[keep]
        o = np.argsort(lc + r.normal(0, 0.05, len(lc)))
        cx, cy, lc = cx[o], cy[o], lc[o]
        m = r.integers(12, 26, len(cx))
        ci = np.repeat(np.arange(len(cx)), m)
        dx = r.normal(0, rc * 0.5, len(ci)); dy = r.normal(0, rc * 0.42, len(ci))
        x = cx[ci] + dx; y = cy[ci] + dy
        side = -(dx * self.L[0] + dy * self.L[1]) / rc
        ll = lc[ci] * 0.75 + 0.17 + 0.22 * side + r.uniform(-0.06, 0.06, len(ci))
        Ls = r.uniform(p0, p1, len(ci))
        groups.append((self._shapes(x, y, Ls, Ls * 0.42 * r.uniform(0.8, 1.0, len(ci)), r.uniform(0, np.pi, len(ci)),
                                    'round', 0.14, r),
                       self._far(ramp_at(R, ll) + r.normal(0, 0.012, (len(ci), 3)), far), 1.0))
        sel = ll > 0.78
        if sel.any():
            k = int(sel.sum())
            Ls = r.uniform(p0 * 0.7, p0 * 1.1, k)
            groups.append((self._shapes(x[sel] + r.normal(0, 1.2, k), y[sel] + r.normal(0, 1.2, k), Ls, Ls * 0.45,
                                        r.uniform(0, np.pi, k), 'round', 0.1, r),
                           self._far(ramp_at(R, np.full(k, 1.0)), far), 0.95))
        self._paint(groups, 2, 0.03)

    def blossom_branch(self, path, w0, w1, kind='pink', flowers=60, spread=26, size=(9, 15), leaves=0.5, buds=0.3,
                       far=0.0, twigs=6, seed=None):
        """a near branch in bloom: a limb, short twigs, five-petal flowers, buds and young leaves"""
        r = self._r(seed)
        self.branch(path, w0, w1, far=far)
        _, Q, nrm = _tube(path, w0, w1)
        R = ramp(kind); G = ramp('spring')
        tw = []
        ends = []
        for _ in range(twigs):
            i = r.integers(len(Q) // 6, len(Q) - 1)
            a0 = np.arctan2(*(np.gradient(Q, axis=0)[i][::-1]))
            a = a0 + r.choice([-1, 1]) * r.uniform(0.5, 1.1)
            L = r.uniform(spread * 1.2, spread * 2.6)
            p0_ = Q[i]; p1_ = p0_ + L * np.array([np.cos(a), np.sin(a)])
            mid = (p0_ + p1_) / 2 + r.normal(0, 5, 2)
            tw.append(_tube([p0_, mid, p1_], max(2.0, w1 * 0.8), 1.2)[0])
            ends.append(spline(np.array([p0_, mid, p1_]), 6))
        self._paint([(tw, self._far(hexc('bark')[None], far), 1.0)])
        # flower positions along the limb and twigs
        tracks = [Q] + ends
        fx, fy = [], []
        for _ in range(flowers):
            T = tracks[r.integers(0, len(tracks))]
            j = r.integers(0, len(T))
            fx.append(T[j, 0] + r.normal(0, spread * 0.45)); fy.append(T[j, 1] + r.normal(0, spread * 0.4))
        fx, fy = np.array(fx, np.float32), np.array(fy, np.float32)
        o = np.argsort(fy + r.normal(0, 10, len(fy)))
        fx, fy = fx[o], fy[o]
        groups = []
        if leaves:
            nl = int(flowers * leaves * 2)
            T = np.vstack(tracks)
            j = r.integers(0, len(T), nl)
            lx = T[j, 0] + r.normal(0, spread * 0.5, nl); ly = T[j, 1] + r.normal(0, spread * 0.45, nl)
            Ls = r.uniform(size[0] * 0.9, size[1] * 1.3, nl)
            la = r.uniform(0, 2 * np.pi, nl)
            ll = 0.35 + 0.5 * r.random(nl)
            groups.append((self._shapes(lx, ly, Ls, Ls * 0.42, la, 'leaf', 0.06, r), self._far(ramp_at(G, ll), far), 1.0))
            groups.append((self._shapes(lx, ly, Ls * 0.8, Ls * 0.05, la, 'leaf', 0.0, r), self._far(ramp_at(G, ll + 0.18), far), 0.6))
        S = r.uniform(*size, len(fx))
        tilt = r.uniform(0.55, 1.0, len(fx)); rot = r.uniform(0, 2 * np.pi, len(fx))
        lit = np.clip(0.55 + 0.35 * r.random(len(fx)), 0, 1)
        Pp, Cp = [], []
        for i in range(len(fx)):
            for k in range(5):
                a = rot[i] + k * 2 * np.pi / 5
                ox, oy = np.cos(a) * S[i] * 0.33, np.sin(a) * S[i] * 0.33 * tilt[i]
                Pp.append((fx[i] + ox, fy[i] + oy, S[i] * 0.62, S[i] * 0.27, np.arctan2(oy, ox + 1e-6)))
                sidel = -(ox * self.L[0] + oy * self.L[1]) / S[i]
                Cp.append(lit[i] + 0.35 * sidel)
        Pp = np.array(Pp, np.float32); Cp = np.array(Cp, np.float32)
        groups.append((self._shapes(Pp[:, 0], Pp[:, 1], Pp[:, 2], Pp[:, 3], Pp[:, 4], 'round', 0.06, r),
                       self._far(ramp_at(R, Cp), far), 1.0))
        cen = np.repeat(mix('#e9d36a', '#b8524f', 0.25)[None], len(fx), 0)
        groups.append((self._shapes(fx, fy, S * 0.22, S * 0.11, 0, 'round', 0.1, r), self._far(cen, far), 1.0))
        k = int(len(fx) * 4)
        a = r.uniform(0, 2 * np.pi, k); ii = r.integers(0, len(fx), k)
        groups.append((self._shapes(fx[ii] + np.cos(a) * S[ii] * 0.16, fy[ii] + np.sin(a) * S[ii] * 0.12, 2.2, 1.1, 0, 'dot', 0.1, r),
                       self._far(np.repeat(mix('#b04a52', '#e6c05a', 0.3)[None], k, 0), far), 0.9))
        if buds:
            nb = int(flowers * buds)
            T = np.vstack(tracks); j = r.integers(0, len(T), nb)
            bx = T[j, 0] + r.normal(0, spread * 0.3, nb); by = T[j, 1] + r.normal(0, spread * 0.3, nb)
            Ls = r.uniform(size[0] * 0.45, size[0] * 0.7, nb)
            groups.append((self._shapes(bx, by, Ls, Ls * 0.55, r.uniform(-2.5, -0.6, nb), 'leaf', 0.05, r),
                           self._far(ramp_at(R, r.uniform(0.15, 0.45, nb)), far), 1.0))
        self._paint(groups, 2, 0.03)

    def willow(self, trunk, boughs, strands=500, length=(120, 260), ramp_='willow', leaf=(3.5, 6.0), far=0.0,
               sway=0.25, light=0.0, crown=None, tips=None, gap=2.8, stem=1.0, bundle=(3, 9), spread=7.0, splay=(0.1, 0.34),
               aspect=0.28, crown_anchor=0.0, show_boughs=True, seed=None):
        """a weeping willow: trunk and boughs, then strands hanging from the boughs in tresses, back (dark) to front
        (light). trunk = (path, w0, w1) or None; boughs = list of (path, w0, w1); tips: lowest row the strands reach"""
        r = self._r(seed)
        R = ramp(ramp_)
        if trunk is not None: self.branch(*trunk, far=far)
        anchors = []
        for b in boughs:
            if show_boughs: self.branch(b[0], b[1], b[2], far=far, light=0.4)
            Q = spline(np.asarray(b[0], np.float32), 10)
            anchors.append(Q[len(Q) // 6:])
        if crown is not None and crown_anchor > 0:
            Kc = np.asarray(crown, np.float32)
            xc, yc = self._sample(Kc, int(sum(len(a) for a in anchors) * crown_anchor / (1 - crown_anchor + 1e-3)) + 1, r, 0.9)
            anchors.append(np.stack([xc, yc], 1))
        if crown is not None:
            self.foliage(crown, ramp_, leaf=(leaf[0] * 1.2, leaf[1] * 1.4), density=1.1, far=far, droop=0.9,
                         aspect=0.3, light=light - 0.1, edge=0.7, highlights=0.5)
        A = np.vstack(anchors)
        cxm = A[:, 0].mean(); wx = max(1.0, np.ptp(A[:, 0]))
        nb = max(1, strands // int(np.mean(bundle)))
        bid = r.integers(0, len(A), nb)
        bdepth = r.random(nb)
        bL = r.uniform(*length, nb)
        recs = []
        for k in range(nb):
            for _ in range(r.integers(bundle[0], bundle[1] + 1)):
                recs.append((bdepth[k] + r.normal(0, 0.06), k))
        recs.sort()
        stems, scol, Pl, Cl = [], [], [], []
        for dep, k in recs:
            x0, y0 = A[bid[k]] + r.normal(0, spread, 2) * np.array([1.0, 0.4])
            L = bL[k] * r.uniform(0.8, 1.15)
            if tips is not None: L = min(L, max(20.0, tips - y0 + r.normal(0, 14)))
            n = max(4, int(L / 6))
            t = np.linspace(0, 1, n)
            out = np.sign(x0 - cxm + 1e-3) * r.uniform(3, 12)
            sw = sway * L * 0.1 * (r.normal(0, 1) * 0.6 + 0.4 * np.sin(k))
            xs = x0 + out * np.sin(np.minimum(t * 3.0, 1.0) * np.pi / 2) + sw * t ** 2 + r.normal(0, 0.5, n).cumsum() * 0.3
            ys = y0 - 5 * np.sin(np.minimum(t * 4, 1) * np.pi) * r.uniform(0.2, 1) + L * t
            path = np.stack([xs, ys], 1)
            side = np.clip(0.5 - 0.6 * (x0 - cxm) / wx, 0, 1)
            base_l = 0.06 + 0.62 * np.clip(dep, 0, 1) + 0.16 * side + light
            stems.append(_tube(path, stem, stem * 0.6, per=3)[0]); scol.append(ramp_at(R, base_l * 0.55))
            Q = spline(path, 3)
            seg = np.linalg.norm(np.diff(Q, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
            m = max(2, int(s[-1] / gap))
            sp = np.sort(r.uniform(0.04, 1.0, m)) * s[-1]
            px = np.interp(sp, s, Q[:, 0]); py = np.interp(sp, s, Q[:, 1])
            tx = np.interp(sp + 1, s, Q[:, 0]) - px; ty = np.interp(sp + 1, s, Q[:, 1]) - py
            ta = np.arctan2(ty, tx)
            alt = np.where(r.random(m) < 0.5, 1.0, -1.0)
            ang = ta + alt * r.uniform(splay[0], splay[1], m) + r.normal(0, 0.06, m)
            Ls = r.uniform(*leaf, m) * (0.8 + 0.3 * sp / s[-1]) * r.uniform(0.7, 1.15, m)
            ll = base_l + 0.14 * sp / s[-1] + r.uniform(-0.08, 0.08, m) + (self._noise_at(px, py) - 0.5) * 0.18 + 0.07 * alt
            off = alt * Ls * r.uniform(0.08, 0.28, m)
            Pl.append(np.stack([px + np.cos(ta) * Ls * 0.35 - np.sin(ta) * off, py + np.sin(ta) * Ls * 0.35 + np.cos(ta) * off, Ls, ang], 1))
            Cl.append(ramp_at(R, ll))
        groups = []
        nslice = 8
        bounds = np.linspace(0, len(recs), nslice + 1).astype(int)
        for a, b in zip(bounds[:-1], bounds[1:]):
            if b <= a: continue
            groups.append((stems[a:b], self._far(np.array(scol[a:b], np.float32), far), 0.65))
            P = np.vstack(Pl[a:b]); Cc = np.vstack(Cl[a:b])
            groups.append((self._shapes(P[:, 0], P[:, 1], P[:, 2], P[:, 2] * aspect, P[:, 3], 'leaf', 0.08, r),
                           self._far(Cc + r.normal(0, 0.012, Cc.shape), far), 1.0))
        self._paint(groups, 2, 0.03)

    def reeds(self, x0, x1, y, n=60, height=(20, 50), ramp_='spring', far=0.0, lean=0.25, width=0.12, bend=0.5, seed=None):
        """sword-leaved plants (iris, grass) rising from a base line y (number or function of x): tapered, curving
        blades, darker in the clump, lit along the edge that faces the sun"""
        r = self._r(seed)
        R = ramp(ramp_)
        xs = r.uniform(x0, x1, n)
        ys = y(xs) if callable(y) else np.full(n, float(y))
        L = r.uniform(*height, n)
        a0 = -np.pi / 2 + r.normal(0, lean, n)
        c = (a0 + np.pi / 2) * bend * 2 + r.normal(0, 0.15, n)
        l = np.clip(0.25 + 0.45 * r.random(n) + 0.2 * (a0 < -np.pi / 2), 0, 1)
        o = np.argsort(l)
        blades, cols, lit, lcols = [], [], [], []
        for i in o:
            t = np.linspace(0, 1, 7)
            ang = a0[i] + c[i] * t ** 1.6
            step = L[i] / 6
            px = xs[i] + np.concatenate([[0], np.cumsum(np.cos(ang[:-1]) * step)])
            py = ys[i] + np.concatenate([[0], np.cumsum(np.sin(ang[:-1]) * step)])
            path = np.stack([px, py], 1)
            w0 = max(1.5, L[i] * width)
            blades.append(_tube(path, w0, 0.5, per=4)[0]); cols.append(ramp_at(R, l[i]))
            if L[i] > 30:
                side = -1.0 if np.cos(a0[i]) < 0 else 1.0
                lit.append(_tube(path + np.array([side * -w0 * 0.22, 0]), w0 * 0.3, 0.3, per=4)[0])
                lcols.append(ramp_at(R, l[i] + 0.25))
        self._paint([(blades, self._far(np.array(cols), far), 1.0), (lit, self._far(np.array(lcols), far), 0.6)], 2, 0.03)

    def pine(self, trunk, limbs, pads, ramp_='deep', needle=(4, 7), far=0.0, light=0.0, seed=None):
        """a garden pine: a leaning, crooked trunk, a few limbs, and flat tiers of needle pads (needle-thin dabs)"""
        r = self._r(seed)
        self.branch(*trunk, far=far, wob=0.25)
        for lb in limbs: self.branch(*lb, far=far, wob=0.2)
        P = np.asarray(pads, np.float32).reshape(-1, 4)
        for k in P[np.argsort(P[:, 1])]:
            K = np.array([[k[0] - k[2] * 0.35, k[1] + k[3] * 0.1, k[2] * 0.6, k[3] * 0.85],
                          [k[0] + k[2] * 0.3, k[1] + k[3] * 0.05, k[2] * 0.62, k[3] * 0.8],
                          [k[0] + r.normal(0, k[2] * 0.1), k[1] - k[3] * 0.3, k[2] * 0.55, k[3] * 0.7]], np.float32)
            self.foliage(K, ramp_, leaf=needle, density=1.2, far=far, light=light, droop=0.05, aspect=0.2, occl=0.55,
                         highlights=1.2, edge=1.2)

    def petals(self, region, n=200, kind='pink', size=(2.5, 5), water=False, far=0.0, alpha=0.95, seed=None):
        """loose petals in the air (tumbling) or lying on the water (flat, with a tiny shadow); region = (x0, y0, x1, y1)"""
        r = self._r(seed)
        x0, y0, x1, y1 = region
        x = r.uniform(x0, x1, n); y = r.uniform(y0, y1, n)
        s = r.uniform(*size, n)
        R = ramp(kind)
        if water:
            ang = r.normal(0, 0.25, n); asp = 0.32
            self.dabs(x + 0.8, y + 1.2, s, s * asp, np.repeat(hexc('water_deep')[None] * 0.8, n, 0), ang, 'round', 0.35, far)
        else:
            ang = r.uniform(0, np.pi, n); asp = r.uniform(0.3, 0.5, n)
        self.dabs(x, y, s, s * asp, ramp_at(R, r.uniform(0.55, 1.0, n)), ang, 'round', alpha, far)

    def rock(self, cx, cy, rx, ry, ramp_='rock', far=0.0, moss=0.3, seed=None):
        """a weathered garden stone: lumpy outline, lit as a dome, painted with small dabs, dark crevices, moss"""
        r = self._r(seed)
        R = ramp(ramp_)
        pts = blob_pts(cx, cy, rx, ry, 0.12, 48, int(r.integers(1 << 20)))
        pts[:, 1] = np.minimum(pts[:, 1], cy + ry * 0.55)
        groups = [([pts], self._far(ramp_at(R, 0.3)[None], far), 1.0)]
        K = np.array([[cx, cy, rx, ry]], np.float32)
        n = int(rx * ry * 0.5)
        x = cx + r.uniform(-1, 1, n) * rx * 0.95; y = cy + r.uniform(-1, 0.55, n) * ry * 0.95
        ok = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 0.9
        x, y = x[ok], y[ok]
        l, own, dd, dmin = self._light_value(x, y, K, 0.25, 0.0, 0.3)
        s = r.uniform(3, 7, len(x)) * max(0.6, min(1.6, rx / 40))
        groups.append((self._shapes(x, y, s, s * 0.6, r.uniform(-0.4, 0.4, len(x)), 'round', 0.2, r),
                       self._far(ramp_at(R, l * 1.05), far), 1.0))
        cr = []
        for _ in range(int(3 + rx / 15)):
            a = r.uniform(cx - rx * 0.6, cx + rx * 0.6); b = r.uniform(cy - ry * 0.4, cy + ry * 0.3)
            cr.append(_tube([(a, b), (a + r.normal(0, rx * 0.2), b + r.uniform(2, ry * 0.3))], 1.6, 0.6)[0])
        groups.append((cr, self._far(ramp_at(R, 0.05)[None], far), 0.6))
        if moss:
            k = int(rx * moss * 3)
            x = cx + r.uniform(-0.9, 0.9, k) * rx; y = cy + ry * r.uniform(0.15, 0.5, k)
            groups.append((self._shapes(x, y, r.uniform(2, 5, k), 1.6, 0, 'round', 0.2, r),
                           self._far(ramp_at(ramp('olive'), r.uniform(0.3, 0.7, k)), far), 0.9))
        self._paint(groups)

    def pot(self, x, y, w, h, colour='terracotta', band=None, far=0.0):
        """a flowerpot standing on y (its foot), lit from the left; returns the rim centre and width"""
        P = np.array([(x - w / 2, y - h), (x + w / 2, y - h), (x + w * 0.36, y), (x - w * 0.36, y)], np.float32)
        base = hexc(colour)
        groups = [([P], self._far(base[None], far), 1.0)]
        k = 10
        for i in range(k):
            t0, t1 = i / k, (i + 1) / k
            sh = 0.78 + 0.42 * np.cos((t0 - 0.3) * np.pi) ** 2 if t0 < 0.8 else 0.7
            q = np.array([(x - w / 2 + w * t0, y - h), (x - w / 2 + w * t1, y - h),
                          (x - w * 0.36 + w * 0.72 * t1, y), (x - w * 0.36 + w * 0.72 * t0, y)], np.float32)
            groups.append(([q], self._far((base * sh)[None], far), 0.85))
        rim = np.array([(x - w / 2 - 2, y - h - 4), (x + w / 2 + 2, y - h - 4), (x + w / 2 + 1, y - h + 3), (x - w / 2 - 1, y - h + 3)], np.float32)
        groups.append(([rim], self._far((base * 1.08)[None], far), 1.0))
        if band:
            b = np.array([(x - w * 0.47, y - h * 0.7), (x + w * 0.47, y - h * 0.7), (x + w * 0.43, y - h * 0.5), (x - w * 0.43, y - h * 0.5)], np.float32)
            groups.append(([b], self._far(hexc(band)[None], far), 0.9))
        groups.append(([np.array([(x - w * 0.42, y - 1), (x + w * 0.46, y - 1), (x + w * 0.5, y + 3), (x - w * 0.36, y + 3)], np.float32)],
                       self._far(np.array([[0.2, 0.2, 0.18]], np.float32), far), 0.35))
        self._paint(groups)
        return x, y - h

    # ================================================================== architecture
    def wall(self, x0, y0, x1, y1, colour='plaster', stains=0.5, damp=0.5, far=0.0, seed=None):
        """a plastered wall: flat paint, low-frequency mottling, rain stains from the top, a damp greener base"""
        r = self._r(seed)
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        h, w = y1 - y0, x1 - x0
        sl = (slice(y0, y1), slice(x0, x1))
        base = hexc(colour)
        n = noise2d(h, w, 90, 4, int(r.integers(1 << 30)))
        col = base * (0.965 + 0.06 * n[..., None])
        st = _blur1(_blur1(r.random((h, w)).astype(np.float32), 0.8, 1), 14, 0)
        st = (st - st.mean()) / (st.std() + 1e-6)
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        drip = smoothstep(0.5, 2.2, st) * (1 - yy) ** 1.5 * stains
        col = col * (1 - 0.1 * drip[..., None]) + hexc('#8c8a80') * 0.1 * drip[..., None]
        dmp = smoothstep(0.78, 1.0, yy + 0.06 * (n - 0.5)) * damp
        col = col * (1 - 0.18 * dmp[..., None]) + hexc('#7d8c74') * 0.18 * dmp[..., None]
        col = self._far(col, far)
        A = np.ones((h, w), np.float32)
        if self._clip is not None: A = self._clip[sl]
        self.C[sl] += (col - self.C[sl]) * A[..., None]
        k = int(w * h / 260)
        xs = r.uniform(x0, x1, k); ys = r.uniform(y0, y1, k)
        c = col[(ys - y0).astype(int).clip(0, h - 1), (xs - x0).astype(int).clip(0, w - 1)] * r.uniform(0.965, 1.025, (k, 1))
        s = r.uniform(8, 26, k)
        self._paint([(self._shapes(xs, ys, s, s * 0.3, r.normal(0, 0.18, k), 'round', 0.12, r), c, 0.6)], 2, 0.03)

    def _roof_surface(self, cx, y_ridge, y_eave, wr, we, upturn, flare):
        D = y_eave - y_ridge

        def surf(u, v):
            v = np.clip(v, 0, 1); au = np.abs(u)
            x = cx + u * (wr + (we - wr) * v ** 1.7) + np.sign(u) * flare * au ** 6 * v ** 3
            y = y_ridge + D * (0.35 * v + 0.65 * (1 - (1 - v) ** 2)) - upturn * au ** 4 * v ** 2.5
            return x, y
        return surf

    def roof(self, cx, y_ridge, y_eave, ridge_w, eave_w, upturn=40.0, flare=24.0, rows=None, courses=None,
             ridge_h=14.0, soffit=10.0, shadow=40.0, ramp_='tile', far=0.0, ends=True, hips=True, ridge_ends=True,
             openwork=True, seed=None):
        """a grey-tiled hip-and-gable roof seen from the front, with upturned flying corners"""
        r = self._r(seed)
        R = ramp(ramp_)
        wr, we = ridge_w / 2, eave_w / 2
        surf = self._roof_surface(cx, y_ridge, y_eave, wr, we, upturn, flare)
        rows = rows or int(eave_w / 13)
        courses = courses or max(6, int((y_eave - y_ridge) / 7))
        # shadow of the eave on whatever stands below it
        if shadow:
            us = np.linspace(-1, 1, 200); ex, ey = surf(us, np.ones_like(us))
            xa, xb = int(max(0, ex.min() + 10)), int(min(self.W, ex.max() - 10))
            ya, yb = int(max(0, ey.min())), int(min(self.H, y_eave + soffit + shadow))
            if xb > xa and yb > ya:
                yy = np.arange(ya, yb, dtype=np.float32)[:, None]; xx = np.arange(xa, xb, dtype=np.float32)[None]
                e = np.interp(xx, ex, ey)
                prof = smoothstep(e + soffit + shadow, e + soffit * 0.6, yy) * (yy > e)
                edge = smoothstep(xa, xa + 30, xx) * smoothstep(xb, xb - 30, xx)
                a = prof * edge * 0.5
                if self._clip is not None: a = a * self._clip[ya:yb, xa:xb]
                Cs = self.C[ya:yb, xa:xb]
                Cs *= (1 - a[..., None] * (1 - hexc('#56607a')[None, None] * 0.9))
        # soffit: the underside of the eave, rafter ends, fascia
        nu_s = 120
        us = np.linspace(-1, 1, nu_s)
        ex, ey = surf(us, np.ones_like(us))
        sof = soffit * (1 + 0.6 * np.abs(us) ** 4)
        P = np.vstack([np.stack([ex, ey], 1), np.stack([ex, ey + sof], 1)[::-1]]).astype(np.float32)
        groups = [([P], self._far(hexc('#3a2c26')[None], far), 1.0)]
        nr = int(eave_w / 9)
        ur = np.linspace(-0.97, 0.97, nr)
        rx_, ry_ = surf(ur, np.ones_like(ur))
        rs = soffit * (1 + 0.6 * np.abs(ur) ** 4)
        groups.append((self._shapes(rx_, ry_ + rs * 0.45, np.full(nr, 3.2), np.full(nr, 1.7 * rs / soffit), np.pi / 2, 'round', 0.05, r),
                       self._far(hexc('#8a6a52')[None] * r.uniform(0.85, 1.05, (nr, 1)), far), 1.0))
        P2 = np.vstack([np.stack([ex, ey + sof - 2.2], 1), np.stack([ex, ey + sof], 1)[::-1]]).astype(np.float32)
        groups.append(([P2], self._far(hexc('#241b18')[None], far), 0.9))
        self._paint(groups)
        # the tiled slope: mesh -> id map -> (u, v) by Newton steps -> analytic tiles
        ss = 2
        nu, nv = int(eave_w / 3) + 8, int((y_eave - y_ridge) / 3) + 8
        ug = np.linspace(-1, 1, nu + 1); vg = np.linspace(0, 1, nv + 1)
        UX, VX = np.meshgrid(ug, vg)
        GX, GY = surf(UX, VX)
        x0 = int(max(0, GX.min() - 3)); x1 = int(min(self.W, GX.max() + 4))
        y0 = int(max(0, GY.min() - 3)); y1 = int(min(self.H, GY.max() + 4))
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
        for j in range(nv):
            for i in range(nu):
                q = [((GX[j, i] - x0) * ss, (GY[j, i] - y0) * ss), ((GX[j, i + 1] - x0) * ss, (GY[j, i + 1] - y0) * ss),
                     ((GX[j + 1, i + 1] - x0) * ss, (GY[j + 1, i + 1] - y0) * ss), ((GX[j + 1, i] - x0) * ss, (GY[j + 1, i] - y0) * ss)]
                d.polygon(q, fill=j * nu + i + 1)
        ids = np.asarray(im).astype(np.int64)
        M = ids > 0
        jj, ii = np.divmod(np.maximum(ids - 1, 0), nu)
        u = ug[ii] + (ug[1] - ug[0]) * 0.5; v = vg[jj] + (vg[1] - vg[0]) * 0.5
        Y, X = np.mgrid[0:h * ss, 0:w * ss].astype(np.float32)
        X = X / ss + x0 + 0.25; Y = Y / ss + y0 + 0.25
        eps = 1e-3
        for _ in range(2):
            fx, fy = surf(u, v)
            ax, ay = surf(u + eps, v); bx, by = surf(u, v + eps)
            J11, J21 = (ax - fx) / eps, (ay - fy) / eps
            J12, J22 = (bx - fx) / eps, (by - fy) / eps
            det = J11 * J22 - J12 * J21
            det = np.where(np.abs(det) < 1e-6, 1e-6, det)
            ex_, ey_ = X - fx, Y - fy
            du = (J22 * ex_ - J12 * ey_) / det; dv = (-J21 * ex_ + J11 * ey_) / det
            u = np.clip(u + np.clip(du, -0.02, 0.02), -1, 1); v = np.clip(v + np.clip(dv, -0.05, 0.05), 0, 1)
        U = (u + 1) / 2 * rows
        ci = np.floor(U); f = U - ci - 0.5
        Vc = v * courses
        cj = np.floor(Vc); g = Vc - cj
        hsh = np.sin(ci * 12.9898 + cj * 78.233) * 43758.5453; hsh = hsh - np.floor(hsh)
        roll = np.abs(f) < 0.23
        p = f / 0.23
        val = np.where(roll, 0.6 - 0.34 * p - 0.22 * p * p, 0.3 + 0.07 * np.cos(np.clip((np.abs(f) - 0.23) / 0.27, 0, 1) * np.pi))
        seam = smoothstep(0.17, 0.0, np.abs(np.abs(f) - 0.23))
        val = val - 0.16 * seam
        lip = smoothstep(0.7, 0.86, g) * (1 - smoothstep(0.9, 0.97, g))
        shd = smoothstep(0.14, 0.0, g)
        val = val + np.where(roll, 0.3 * lip - 0.26 * shd, 0.07 * lip - 0.12 * shd)
        val = val + 0.08 * (hsh - 0.5) + 0.1 * v - 0.08 * u * np.abs(u) ** 3 - 0.06 * (1 - v) ** 3
        col = ramp_at(R, val)
        moss = (hsh > 0.86) & ~roll
        col = np.where(moss[..., None], col * 0.85 + hexc('#5f6e48') * 0.15, col)
        col = self._far(col, far)
        A = M.astype(np.float32)
        col = (col * A[..., None]).reshape(h, ss, w, ss, 3).mean((1, 3))
        A = A.reshape(h, ss, w, ss).mean((1, 3))
        col = col / np.maximum(A[..., None], 1e-4)
        if self._clip is not None: A = A * self._clip[y0:y1, x0:x1]
        col = col * (1 + 0.035 * self.TX[y0:y1, x0:x1, None])
        Cs = self.C[y0:y1, x0:x1]
        Cs += (col - Cs) * A[..., None]
        groups = []
        # tile ends and drip tiles along the eave
        if ends:
            uc = ((np.arange(rows) + 0.5) / rows) * 2 - 1
            ex, ey = surf(uc, np.ones_like(uc))
            sp = (we * 2 / rows) * (1 + 3 * np.abs(uc) ** 5 * flare / max(we, 1))
            rr = sp * 0.36
            up = (np.arange(rows - 1) + 1) / rows * 2 - 1
            dx_, dy_ = surf(up, np.ones_like(up))
            dsp = (we * 2 / rows)
            tri = np.stack([np.stack([dx_ - dsp * 0.3, dy_ - 1], 1), np.stack([dx_ + dsp * 0.3, dy_ - 1], 1),
                            np.stack([dx_, dy_ + dsp * 0.42], 1)], 1)
            groups.append((tri, self._far(ramp_at(R, 0.32)[None] * r.uniform(0.9, 1.1, (len(up), 1)), far), 1.0))
            groups.append((self._shapes(ex, ey, rr * 2, rr, 0, 'round', 0.04, r),
                           self._far(ramp_at(R, 0.55)[None] * r.uniform(0.92, 1.08, (rows, 1)), far), 1.0))
            groups.append((self._shapes(ex + rr * 0.15, ey + rr * 0.15, rr * 1.35, rr * 0.68, 0, 'round', 0.04, r),
                           self._far(ramp_at(R, 0.18)[None], far), 1.0))
            groups.append((self._shapes(ex - rr * 0.32, ey - rr * 0.32, rr * 0.7, rr * 0.18, -0.8, 'leaf', 0.0, r),
                           self._far(ramp_at(R, 0.95)[None], far), 0.7))
        # hip ridges down to the flying corners
        if hips:
            for sgn in (-1, 1):
                vv = np.linspace(0.02, 1, 24)
                hx, hy = surf(np.full_like(vv, sgn), vv)
                c_x, c_y = hx[-1], hy[-1]
                tx, ty = hx[-1] - hx[-3], hy[-1] - hy[-3]
                tn = np.hypot(tx, ty) + 1e-6
                tip = [(c_x + tx / tn * upturn * 0.25 + sgn * upturn * 0.15, c_y - upturn * 0.35),
                       (c_x + sgn * upturn * 0.42, c_y - upturn * 0.85), (c_x + sgn * upturn * 0.36, c_y - upturn * 1.15)]
                path = np.vstack([np.stack([hx, hy], 1), tip])
                Ph, Qh, nh = _tube(path, ridge_h * 0.72, 2.0, per=3)
                groups.append(([Ph], self._far(ramp_at(R, 0.2)[None], far), 1.0))
                Pl, _, _ = _tube(Qh[:: max(1, len(Qh) // 20)] + np.array([sgn * 0.6, -ridge_h * 0.18]), ridge_h * 0.22, 0.8, per=2)
                groups.append(([Pl], self._far(ramp_at(R, 0.62 if sgn < 0 else 0.45)[None], far), 0.9))
        # the main ridge, its openwork and curled ends
        if ridge_h:
            xr0, xr1 = cx - wr - ridge_h * 0.3, cx + wr + ridge_h * 0.3
            body = np.array([(xr0, y_ridge + 2), (xr0, y_ridge - ridge_h), (xr1, y_ridge - ridge_h), (xr1, y_ridge + 2)], np.float32)
            groups.append(([body], self._far(ramp_at(R, 0.24)[None], far), 1.0))
            yc0, yc1 = y_ridge - ridge_h - 3, y_ridge - ridge_h + 1
            cap = np.array([(xr0 - 2, yc0), (xr1 + 2, yc0), (xr1 + 2, yc1), (xr0 - 2, yc1)], np.float32)
            groups.append(([cap], self._far(ramp_at(R, 0.5)[None], far), 1.0))
            if openwork and ridge_h >= 9:
                k = int((xr1 - xr0) / (ridge_h * 0.7))
                xs = np.linspace(xr0 + ridge_h, xr1 - ridge_h, k)
                groups.append((self._shapes(xs, np.full(k, y_ridge - ridge_h * 0.45), np.full(k, ridge_h * 0.5),
                                            np.full(k, ridge_h * 0.26), 0, 'round', 0.03, r),
                               self._far(ramp_at(R, 0.05)[None], far), 1.0))
                groups.append((self._shapes(xs - ridge_h * 0.06, np.full(k, y_ridge - ridge_h * 0.52), np.full(k, ridge_h * 0.3),
                                            np.full(k, ridge_h * 0.08), 0, 'round', 0.03, r),
                               self._far(ramp_at(R, 0.6)[None], far), 0.7))
            if ridge_ends:
                for sgn, xe in ((-1, xr0), (1, xr1)):
                    hh = ridge_h
                    path = [(xe - sgn * hh * 0.6, y_ridge - hh * 0.5), (xe + sgn * hh * 0.5, y_ridge - hh * 0.9),
                            (xe + sgn * hh * 1.2, y_ridge - hh * 1.9), (xe + sgn * hh * 1.25, y_ridge - hh * 2.8),
                            (xe + sgn * hh * 0.85, y_ridge - hh * 3.25)]
                    Pe, Qe, _ = _tube(path, hh * 1.05, hh * 0.32, per=4)
                    groups.append(([Pe], self._far(ramp_at(R, 0.22)[None], far), 1.0))
                    Pl, _, _ = _tube(np.array(path) + np.array([-sgn * hh * 0.18, -hh * 0.12]), hh * 0.25, hh * 0.08, per=4)
                    groups.append(([Pl], self._far(ramp_at(R, 0.62)[None], far), 0.85))
        self._paint(groups)
        return surf

    def dapple(self, x0, y0, x1, y1, amount=0.3, scale=16.0, cover=0.5, falloff=None, mask=None, colour='#4e6680', seed=None):
        """dappled shade cast by leaves onto a sunlit surface: soft-edged patches of cool shadow with sun flecks
        between them; falloff = (x, y, radius): strongest near the tree that casts it"""
        r = self._r(seed)
        x0, y0, x1, y1 = (int(max(0, v)) for v in (x0, y0, x1, y1))
        x1, y1 = min(self.W, x1), min(self.H, y1)
        h, w = y1 - y0, x1 - x0
        if h <= 0 or w <= 0: return
        n = noise2d(h, w, scale, 3, int(r.integers(1 << 30)))
        a = smoothstep(cover - 0.06, cover + 0.06, n) * amount
        if falloff is not None:
            fx, fy, fr = falloff
            yy = np.arange(y0, y1, dtype=np.float32)[:, None]; xx = np.arange(x0, x1, dtype=np.float32)[None]
            a = a * np.clip(1 - np.hypot(xx - fx, yy - fy) / fr, 0, 1) ** 0.8
        if mask is not None: a = a * mask[y0:y1, x0:x1]
        if self._clip is not None: a = a * self._clip[y0:y1, x0:x1]
        Cs = self.C[y0:y1, x0:x1]
        Cs *= (1 - a[..., None] * (1 - hexc(colour)[None, None]))

    def coping(self, x0, x1, y, h=20, far=0.0, seed=None):
        """the little tiled roof along the top of a garden wall"""
        return self.roof((x0 + x1) / 2, y - h, y, (x1 - x0) - h * 0.8, x1 - x0, upturn=h * 0.45, flare=h * 0.2,
                         rows=int((x1 - x0) / 8.5), courses=max(4, int(h / 5)), ridge_h=max(4.0, h * 0.32),
                         soffit=max(3.0, h * 0.2), shadow=h * 0.9, far=far, openwork=False, seed=seed)

    def column(self, x, y0, y1, w=12, colour='lacquer', base='stone', far=0.0):
        """a lacquered round column on a stone base, lit from the left"""
        k = 9
        groups = []
        c = hexc(colour)
        for i in range(k):
            t0, t1 = i / k, (i + 1) / k
            tm = (t0 + t1) / 2
            sh = 0.62 + 0.6 * np.cos((tm - 0.28) * np.pi * 0.9) ** 2 * (tm < 0.85) + 0.05
            q = np.array([(x - w / 2 + w * t0, y0), (x - w / 2 + w * t1, y0), (x - w / 2 + w * t1, y1), (x - w / 2 + w * t0, y1)], np.float32)
            groups.append(([q], self._far((c * sh)[None], far), 1.0))
        bw = w * 1.7; bh = w * 0.8
        b = np.array([(x - bw / 2, y1 - bh), (x + bw / 2, y1 - bh), (x + bw * 0.56, y1), (x - bw * 0.56, y1)], np.float32)
        groups.append(([b], self._far(ramp_at(ramp('stone'), 0.6)[None], far), 1.0))
        b2 = np.array([(x + bw * 0.1, y1 - bh), (x + bw / 2, y1 - bh), (x + bw * 0.56, y1), (x + bw * 0.1, y1)], np.float32)
        groups.append(([b2], self._far(ramp_at(ramp('stone'), 0.35)[None], far), 0.8))
        self._paint(groups)

    def beam(self, x0, x1, y0, y1, colour='beam', band='jade_dark', far=0.0):
        """a lacquered lintel between columns, a painted band along it and a lit upper edge"""
        h = y1 - y0
        q = lambda a, b: np.array([(x0, a), (x1, a), (x1, b), (x0, b)], np.float32)
        self._paint([([q(y0, y1)], self._far(hexc(colour)[None], far), 1.0),
                     ([q(y0 + h * 0.44, y0 + h * 0.62)], self._far(hexc(band)[None], far), 0.9),
                     ([q(y0, y0 + 1.5)], self._far(mix(colour, '#f0d0b0', 0.35)[None], far), 0.8)], 2, 0.03)

    def lattice(self, x0, y0, x1, y1, pattern='lantern', cell=13, bar=2.0, frame=4.0, colour='jade', back='interior',
                kind='window', far=0.0, seed=None):
        """jade lattice: window (all lattice), door (lattice, waist panel, skirt panel) or open fretwork (back=None)"""
        r = self._r(seed)
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        w, h = x1 - x0, y1 - y0
        if w < 4 or h < 4: return
        ss = 3
        im = Image.new('L', (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
        pm = Image.new('L', (w * ss, h * ss), 0); dp = ImageDraw.Draw(pm)
        fw = max(1, int(frame * ss)); bw = max(1, int(bar * ss))
        d.rectangle([0, 0, w * ss - 1, h * ss - 1], outline=255, width=fw)
        zones = [(fw, h * ss - fw)]
        if kind == 'door':
            a = int(h * ss * 0.58); b = int(h * ss * 0.67); c = int(h * ss * 0.71)
            zones = [(fw, a)]
            d.rectangle([0, a, w * ss, a + fw], fill=255); d.rectangle([0, b, w * ss, c], fill=255)
            dp.rectangle([fw, a + fw, w * ss - fw, b], fill=255)
            dp.rectangle([fw, c, w * ss - fw, h * ss - fw], fill=255)
        for za, zb in zones:
            X0, X1 = fw, w * ss - fw
            if pattern == 'grid':
                cs = cell * ss
                for x in np.arange(X0 + cs, X1, cs): d.line([(x, za), (x, zb)], fill=255, width=bw)
                for y in np.arange(za + cs, zb, cs): d.line([(X0, y), (X1, y)], fill=255, width=bw)
            elif pattern == 'diamond':
                cs = cell * ss
                for k in np.arange(-(zb - za), X1 - X0 + (zb - za), cs):
                    d.line([(X0 + k, za), (X0 + k + (zb - za), zb)], fill=255, width=bw)
                    d.line([(X0 + k, zb), (X0 + k + (zb - za), za)], fill=255, width=bw)
            elif pattern == 'ice':
                hh, ww = (zb - za) // ss, (X1 - X0) // ss
                npt = max(4, int(hh * ww / (cell * cell * 1.3)))
                px = r.uniform(0, ww, npt); py = r.uniform(0, hh, npt)
                yy, xx = np.mgrid[0:hh, 0:ww]
                dd = (xx[..., None] - px) ** 2 + (yy[..., None] - py) ** 2
                lab = np.argmin(dd, -1)
                edge = np.zeros((hh, ww), bool)
                edge[:, 1:] |= lab[:, 1:] != lab[:, :-1]; edge[1:, :] |= lab[1:, :] != lab[:-1, :]
                e = Image.fromarray((edge * 255).astype(np.uint8)).resize((ww * ss, hh * ss), Image.NEAREST)
                e = e.filter(ImageFilter.MaxFilter(max(3, bw | 1)))
                im.paste(255, (X0, za), e)
            else:   # 'lantern' (灯笼锦): an open centre framed by bars, short ties out to the frame, small grid around
                W_, H_ = X1 - X0, zb - za
                cx0, cx1 = X0 + W_ * 0.3, X1 - W_ * 0.3
                cy0, cy1 = za + H_ * 0.33, zb - H_ * 0.33
                d.rectangle([cx0, cy0, cx1, cy1], outline=255, width=bw)
                cs = cell * ss
                for x in np.arange(X0 + cs * 0.8, X1, cs):
                    if x < cx0 or x > cx1: d.line([(x, za), (x, zb)], fill=255, width=bw)
                    else:
                        d.line([(x, za), (x, cy0)], fill=255, width=bw); d.line([(x, cy1), (x, zb)], fill=255, width=bw)
                for y in np.arange(za + cs * 0.8, zb, cs):
                    if y < cy0 or y > cy1: d.line([(X0, y), (X1, y)], fill=255, width=bw)
                    else:
                        d.line([(X0, y), (cx0, y)], fill=255, width=bw); d.line([(cx1, y), (X1, y)], fill=255, width=bw)
        Bm = np.asarray(im, np.float32) / 255
        Pm = np.asarray(pm, np.float32) / 255
        jade = hexc(colour)
        lite, dark = mix(jade, '#d8f0dc', 0.42), jade * 0.5
        o = max(1, int(ss * 1.0))
        up = np.zeros_like(Bm); up[o:, o:] = Bm[:-o, :-o]          # bar shifted down-right
        dn = np.zeros_like(Bm); dn[:-o, :-o] = Bm[o:, o:]
        litE = np.clip(Bm - up, 0, 1); darkE = np.clip(Bm - dn, 0, 1)
        so = 2 * ss
        sh = np.zeros_like(Bm); sh[so:, so:] = Bm[:-so, :-so]
        yy = np.linspace(0, 1, h * ss, dtype=np.float32)[:, None]
        if back is not None:
            if back == 'interior':
                bcol = hexc('interior')[None, None] * (1.15 - 0.3 * yy[..., None])
                xx = np.linspace(0, 1, w * ss, dtype=np.float32)[None]
                sheen = smoothstep(0.1, 0.0, np.abs((xx + yy * 0.6) - 0.55 - 0.2 * r.random()))
                bcol = bcol + 0.08 * sheen[..., None]
            else:
                bcol = hexc(back)[None, None] * (1.04 - 0.12 * yy[..., None])
            Cb = np.broadcast_to(bcol, (h * ss, w * ss, 3)).copy()
            Cb *= (1 - 0.45 * sh * (1 - Bm))[..., None]
            A0 = np.ones((h * ss, w * ss), np.float32)
        else:
            Cb = np.zeros((h * ss, w * ss, 3), np.float32); A0 = np.zeros((h * ss, w * ss), np.float32)
        pan = jade * (0.95 - 0.12 * yy[..., None])
        Cb = Cb * (1 - Pm[..., None]) + pan * Pm[..., None]
        A0 = np.maximum(A0, Pm)
        if kind == 'door':
            ip = Image.new('L', (w * ss, h * ss), 0); di = ImageDraw.Draw(ip)
            for a, b in ((0.585, 0.665), (0.73, 0.98)):
                di.rectangle([fw + 2.5 * ss, int(h * ss * a) + 2 * ss, w * ss - fw - 2.5 * ss, int(h * ss * b) - 2 * ss], outline=255, width=max(1, ss))
            Im = np.asarray(ip, np.float32) / 255
            Cb = Cb * (1 - 0.35 * Im[..., None]) + dark * 0.35 * Im[..., None]
            Im2 = np.zeros_like(Im); Im2[ss:, ss:] = Im[:-ss, :-ss]
            Cb = Cb * (1 - 0.4 * Im2[..., None]) + lite * 0.4 * Im2[..., None]
        barc = jade[None, None] * (1 + 0.04 * r.normal(0, 1)) * np.ones((h * ss, w * ss, 1), np.float32)
        barc = barc * (1 - litE[..., None]) + lite * litE[..., None]
        barc = barc * (1 - 0.7 * darkE[..., None]) + dark * 0.7 * darkE[..., None]
        Cb = Cb * (1 - Bm[..., None]) + barc * Bm[..., None]
        A0 = np.maximum(A0, Bm)
        Cb = self._far(Cb, far)
        Cd = (Cb * A0[..., None]).reshape(h, ss, w, ss, 3).mean((1, 3))
        Ad = A0.reshape(h, ss, w, ss).mean((1, 3))
        sl = (slice(y0, y1), slice(x0, x1))
        if self._clip is not None:
            f = self._clip[sl]; Ad = Ad * f; Cd = Cd * f[..., None]
        self.C[sl] = self.C[sl] * (1 - Ad[..., None]) + Cd

    def fretwork(self, x0, x1, y0, h=18, cell=8, colour='jade', far=0.0):
        """挂落: the open lattice frieze hanging under a beam between two columns, with a stepped lower edge"""
        self.lattice(x0, y0, x1, y0 + h, 'grid', cell, 1.6, 2.2, colour, None, 'window', far)
        step = int(cell * 1.5)
        for x in range(int(x0) + step, int(x1) - step, step * 2):
            self.lattice(x, y0 + h - 2, x + step, y0 + h + cell * 0.8, 'grid', cell, 1.6, 2.2, colour, None, 'window', far)

    def round_window(self, cx, cy, r, ring=7.0, pattern='ice', inside=None, ground=None, far=0.0, reveal=4.0,
                     colour='#a4a8a2', cell=12, back='paper'):
        """a round opening in a wall: a lattice window (pattern) or, with inside=callable(mask), a moon gate showing
        another view; ground cuts the circle at that row (a gate standing on its threshold)"""
        opening = self.ellipse(cx, cy, r, r)
        if ground is not None:
            yy = np.arange(self.H, dtype=np.float32)[:, None]
            opening = opening * (yy < ground)
        if inside is not None:
            with self.clipped(opening): inside(opening)
        else:
            with self.clipped(opening):
                self.lattice(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2, pattern, cell, 2.0, 0.0, 'jade', back, 'window', far)
        if reveal:
            rv = np.clip(self.ellipse(cx, cy, r, r) - self.ellipse(cx + reveal, cy - reveal * 0.6, r, r), 0, 1)
            if ground is not None: rv = rv * (np.arange(self.H)[:, None] < ground)
            self.fill(rv, self._far(mix('plaster', '#b9b4a6', 0.35)[None, None], far)[0, 0], 0.95)
        outer = self.ellipse(cx, cy, r + ring, r + ring)
        band = np.clip(outer - self.ellipse(cx, cy, r, r), 0, 1)
        if ground is not None: band = band * (np.arange(self.H)[:, None] < ground)
        yy = np.arange(self.H, dtype=np.float32)[:, None]; xx = np.arange(self.W, dtype=np.float32)[None]
        ang = np.arctan2(yy - cy, xx - cx)
        lt = 0.5 - 0.5 * np.cos(ang - np.arctan2(-self.L[1], -self.L[0]))
        c0 = hexc(colour)
        y_a, y_b = int(max(0, cy - r - ring - 2)), int(min(self.H, cy + r + ring + 2))
        x_a, x_b = int(max(0, cx - r - ring - 2)), int(min(self.W, cx + r + ring + 2))
        sl = (slice(y_a, y_b), slice(x_a, x_b))
        col = c0 * (0.78 + 0.4 * lt[sl][..., None])
        col = self._far(col, far)
        A = band[sl]
        if self._clip is not None: A = A * self._clip[sl]
        self.C[sl] += (col - self.C[sl]) * A[..., None]
        inner = np.clip(self.ellipse(cx, cy, r + 1.2, r + 1.2) - self.ellipse(cx, cy, r - 0.3, r - 0.3), 0, 1)
        if ground is not None: inner = inner * (yy < ground)
        self.fill(inner, self._far(c0[None, None] * 0.45, far)[0, 0], 0.7)
        return opening

    def stonework(self, x0, y0, x1, y1, course=(10, 14), block=(26, 60), ramp_='stone', far=0.0, damp=0.4, light=0.0, seed=None):
        """a dressed-stone face: courses of blocks with mortar joints, each block its own value, a lit top edge"""
        r = self._r(seed)
        R = ramp(ramp_)
        groups = [([np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], np.float32)], self._far(ramp_at(R, 0.2)[None], far), 1.0)]
        P, Cc = [], []
        y = y0
        while y < y1 - 1:
            hh = min(r.uniform(*course), y1 - y)
            x = x0 - r.uniform(0, block[1] * 0.6)
            while x < x1:
                ww = r.uniform(*block)
                a, b = max(x, x0), min(x + ww, x1)
                if b - a > 2:
                    P.append(np.array([(a + 0.7, y + 0.6), (b - 0.7, y + 0.6), (b - 0.7, y + hh - 0.7), (a + 0.7, y + hh - 0.7)], np.float32))
                    t = (y + hh / 2 - y0) / max(1, y1 - y0)
                    Cc.append(0.62 + light + r.uniform(-0.1, 0.08) - damp * 0.35 * t ** 2)
                x += ww
            y += hh
        groups.append((P, self._far(ramp_at(R, np.array(Cc)), far), 1.0))
        groups.append(([np.array([(x0, y0), (x1, y0), (x1, y0 + 2.2), (x0, y0 + 2.2)], np.float32)], self._far(ramp_at(R, 0.9)[None], far), 0.9))
        self._paint(groups, 2, 0.06)

    def steps(self, x0, x1, y, n=4, rise=8.0, tread=5.0, grow=3.0, ramp_='stone', far=0.0, moss=0.4, seed=None):
        """a flight of stone steps coming toward the viewer from row y: treads (lit), risers (shaded), slab joints"""
        r = self._r(seed)
        R = ramp(ramp_)
        groups = []
        for k in range(n):
            a, b = x0 - grow * k, x1 + grow * k
            yt = y + k * (rise + tread)
            t = k / max(1, n - 1)
            tr = np.array([(a, yt), (b, yt), (b + grow, yt + tread), (a - grow, yt + tread)], np.float32)
            rs = np.array([(a - grow, yt + tread), (b + grow, yt + tread), (b + grow, yt + tread + rise), (a - grow, yt + tread + rise)], np.float32)
            groups.append(([tr], self._far(ramp_at(R, 0.82 - 0.18 * t * moss)[None], far), 1.0))
            groups.append(([rs], self._far(ramp_at(R, 0.42 - 0.15 * t * moss)[None], far), 1.0))
            nj = int((b - a) / r.uniform(28, 46))
            for xj in r.uniform(a + 6, b - 6, nj):
                groups.append(([np.array([(xj, yt + tread), (xj + 1.3, yt + tread), (xj + 1.3, yt + tread + rise), (xj, yt + tread + rise)], np.float32)],
                               self._far(ramp_at(R, 0.15)[None], far), 0.8))
            if moss and k >= n // 2:
                m = int((b - a) / 5 * moss)
                groups.append((self._shapes(r.uniform(a, b, m), np.full(m, yt + tread + rise) - r.uniform(0, 3, m),
                                            r.uniform(3, 7, m), 1.8, 0, 'round', 0.2, r),
                               self._far(ramp_at(ramp('olive'), r.uniform(0.3, 0.65, m)), far), 0.9))
        self._paint(groups, 2, 0.06)
        return y + n * (rise + tread)

    def _proj(self, pts):
        p = np.asarray(pts, np.float32)
        x, y = self.project(p[:, 0], p[:, 1], p[:, 2])
        return np.stack([x, y], 1)

    def bridge(self, path, width=1.6, deck=0.45, thick=0.22, rail=0.62, post=1.3, ramp_='stone', reflection=False,
               rails='both', far=0.0, seed=None):
        """a zigzag stone bridge on the water plane: path = [(X, Z), ...] in metres, near -> far; each segment has
        stone piers, a slab deck with joints and two balustrades of posts, pierced panels and a top rail.
        reflection=True paints the mirror image (heights negated, softened) for the water; rails = 'both', 'rear'
        (the far balustrade only, so the deck shows from a low eye) or 'none'"""
        r = self._r(seed)
        R = ramp(ramp_)
        sg = -1.0 if reflection else 1.0
        before = self.C.copy() if reflection else None
        Lw = np.array([-0.5, 0.72, -0.48], np.float32); Lw /= np.linalg.norm(Lw)
        P = np.asarray(path, np.float32)
        groups = []

        def face(pts3, normal, base=0.0, a=1.0, jit=0.0):
            nrm = np.asarray(normal, np.float32); nrm = nrm / (np.linalg.norm(nrm) + 1e-6)
            if reflection: nrm = nrm * np.array([1, -1, 1], np.float32)
            lam = float(np.clip(nrm @ Lw, 0, 1))
            val = 0.25 + 0.62 * lam + base + jit * r.normal()
            q = np.asarray(pts3, np.float32).copy(); q[:, 1] *= sg
            groups.append(([self._proj(q)], self._far(ramp_at(R, val)[None], far), a))

        def visible(pts3, normal):
            c = np.asarray(pts3, np.float32).mean(0); c[1] *= sg
            n = np.asarray(normal, np.float32).copy(); n[1] *= sg
            eye = np.array([0, self.cam[1], 0], np.float32)
            return float(n @ (eye - c)) > 0

        nseg = len(P) - 1
        for si in range(nseg - 1, -1, -1):
            A, B = P[si], P[si + 1]
            dvec = (B - A); Ls = float(np.linalg.norm(dvec)); dvec = dvec / Ls
            nvec = np.array([-dvec[1], dvec[0]], np.float32)
            ext = width * 0.5
            A2 = A - dvec * (ext if si > 0 else 0); B2 = B + dvec * (ext if si < nseg - 1 else 0)

            def pt(p2, off, yv):
                q = p2 + nvec * off
                return (q[0], yv, q[1])
            # piers
            for t in np.linspace(0, 1, max(2, int(Ls / 2.6) + 1)):
                c = A + (B - A) * t
                pw, pd = 0.28, width * 0.42
                f4 = [(c - dvec * pw + nvec * pd), (c + dvec * pw + nvec * pd), (c + dvec * pw - nvec * pd), (c - dvec * pw - nvec * pd)]
                for i in range(4):
                    a3, b3 = f4[i], f4[(i + 1) % 4]
                    q = [(a3[0], 0.0, a3[1]), (b3[0], 0.0, b3[1]), (b3[0], deck - thick, b3[1]), (a3[0], deck - thick, a3[1])]
                    e = b3 - a3; nn = np.array([-e[1], 0, e[0]], np.float32)
                    if visible(q, nn): face(q, nn, -0.18, 1.0, 0.03)
            # deck slab
            top = [pt(A2, width / 2, deck), pt(B2, width / 2, deck), pt(B2, -width / 2, deck), pt(A2, -width / 2, deck)]
            bot = [(x, deck - thick, z) for x, _, z in top]
            for i in range(4):
                q = [top[i], top[(i + 1) % 4], bot[(i + 1) % 4], bot[i]]
                e = np.array(top[(i + 1) % 4]) - np.array(top[i]); nn = np.array([-e[2], 0, e[0]], np.float32)
                if visible(q, nn): face(q, nn, -0.05, 1.0, 0.02)
            if not reflection:
                face(top, (0, 1, 0), 0.08)
                nj = int(Ls / 0.9)
                for t in np.linspace(0.05, 0.95, max(1, nj)):
                    c = A2 + (B2 - A2) * t
                    q = [pt(c, width / 2, deck + 0.001), pt(c + dvec * 0.04, width / 2, deck + 0.001),
                         pt(c + dvec * 0.04, -width / 2, deck + 0.001), pt(c, -width / 2, deck + 0.001)]
                    groups.append(([self._proj(q)], self._far(ramp_at(R, 0.3)[None], far), 0.7))
            else:
                face(bot, (0, -1, 0), -0.25)
            # balustrades: rear one first
            sides = sorted((-1, 1), key=lambda s: -np.linalg.norm((A + B) / 2 + nvec * s * width / 2))
            if rails == 'rear': sides = sides[:1]
            elif rails == 'none': sides = []
            for s in sides:
                off = s * (width / 2 - 0.08)
                npost = max(2, int(Ls / post) + 1)
                ts = np.linspace(0, 1, npost)
                outward = np.array([nvec[0] * s, 0, nvec[1] * s], np.float32)
                facing = outward if visible([pt(A + (B - A) * 0.5, off, deck + rail / 2)], outward) else -outward
                for k in range(npost - 1):
                    pa_ = A + (B - A) * ts[k]; pb_ = A + (B - A) * ts[k + 1]
                    pa_ = pa_ + dvec * 0.08; pb_ = pb_ - dvec * 0.08
                    y_lo, y_hi = deck + 0.06, deck + rail - 0.07
                    # pierced panel: four strips around an opening
                    def q2(s0, s1, h0, h1):
                        a3 = pa_ + (pb_ - pa_) * s0; b3 = pa_ + (pb_ - pa_) * s1
                        return [pt(a3, off, y_lo + (y_hi - y_lo) * h0), pt(b3, off, y_lo + (y_hi - y_lo) * h0),
                                pt(b3, off, y_lo + (y_hi - y_lo) * h1), pt(a3, off, y_lo + (y_hi - y_lo) * h1)]
                    for qq in (q2(0, 1, 0, 0.28), q2(0, 1, 0.72, 1), q2(0, 0.16, 0.28, 0.72), q2(0.84, 1, 0.28, 0.72)):
                        face(qq, facing, -0.06, 1.0, 0.02)
                    lip = q2(0.16, 0.84, 0.66, 0.72)
                    face(lip, (0, -1, 0), -0.2, 0.8)
                # top rail
                ra, rb = A + dvec * 0.02, B - dvec * 0.02
                yr = deck + rail - 0.07
                face([pt(ra, off, yr + 0.07), pt(rb, off, yr + 0.07), pt(rb, off, yr), pt(ra, off, yr)], facing, 0.0)
                if not reflection:
                    yt_ = yr + 0.07
                    face([pt(ra, off - 0.07, yt_), pt(rb, off - 0.07, yt_), pt(rb, off + 0.07, yt_), pt(ra, off + 0.07, yt_)], (0, 1, 0), 0.06)
                # posts
                for t in ts:
                    c = A + (B - A) * t
                    pw = 0.075
                    yb, yt = deck, deck + rail + 0.1
                    for nn2 in (np.array([dvec[0], 0, dvec[1]]), -np.array([dvec[0], 0, dvec[1]]), outward, -outward):
                        cen = c + np.array([nn2[0], nn2[2]]) * pw
                        tang = np.array([-nn2[2], nn2[0]]) * pw
                        q = [(cen[0] - tang[0] + nvec[0] * off, yb, cen[1] - tang[1] + nvec[1] * off),
                             (cen[0] + tang[0] + nvec[0] * off, yb, cen[1] + tang[1] + nvec[1] * off),
                             (cen[0] + tang[0] + nvec[0] * off, yt, cen[1] + tang[1] + nvec[1] * off),
                             (cen[0] - tang[0] + nvec[0] * off, yt, cen[1] - tang[1] + nvec[1] * off)]
                        if visible(q, nn2): face(q, nn2, 0.02, 1.0, 0.03)
                    if not reflection:
                        cc = c + nvec * off
                        cap = [(cc[0] - pw * 1.2, yt + 0.03, cc[1] - pw * 1.2), (cc[0] + pw * 1.2, yt + 0.03, cc[1] - pw * 1.2),
                               (cc[0] + pw * 1.2, yt + 0.03, cc[1] + pw * 1.2), (cc[0] - pw * 1.2, yt + 0.03, cc[1] + pw * 1.2)]
                        face(cap, (0, 1, 0), 0.12)
        self._paint(groups, 2, 0.025)
        if reflection:      # a reflection is softer and a little transparent
            D = _blur1(_blur1(self.C - before, 3.0, 0), 1.0, 1)
            self.C[:] = before + D * 0.8

    def lantern(self, x, y, h=40, colour='lantern', cord=14, far=0.0, seed=None):
        """a red silk lantern hanging from (x, y): cord, gold caps, ribbed lit body, tassel"""
        r = self._r(seed)
        rx, ry = h * 0.42, h * 0.5
        cy = y + cord + h * 0.09 + ry
        groups = [([_tube([(x, y), (x, y + cord + 2)], 1.4, 1.2)[0]], self._far(hexc('#2b211d')[None], far), 1.0)]
        groups.append(([np.array([(x - rx * 0.45, cy - ry - h * 0.1), (x + rx * 0.45, cy - ry - h * 0.1),
                                  (x + rx * 0.5, cy - ry + h * 0.04), (x - rx * 0.5, cy - ry + h * 0.04)], np.float32)],
                       self._far(hexc('#8a6a2c')[None], far), 1.0))
        t = np.linspace(0, 2 * np.pi, 48)
        body = np.stack([x + rx * np.cos(t), cy + ry * np.sin(t) * 0.94], 1).astype(np.float32)
        base = hexc(colour)
        groups.append(([body], self._far(base[None] * 0.72, far), 1.0))
        for k, (sx, sy, a) in enumerate([(0.86, 0.88, 1.0), (0.66, 0.78, 1.0), (0.44, 0.6, 1.0)]):
            ox, oy = -rx * 0.18 * (k + 1) * 0.6, -ry * 0.12 * (k + 1) * 0.6
            e = np.stack([x + ox + rx * sx * np.cos(t), cy + oy + ry * sy * np.sin(t) * 0.94], 1).astype(np.float32)
            groups.append(([e], self._far(mix(base, '#ffb07a', 0.12 + 0.18 * k)[None], far), 0.8))
        ribs = []
        for s in np.linspace(-0.8, 0.8, 5):
            yy = np.linspace(-0.92, 0.92, 14)
            xs = x + rx * s * np.sqrt(1 - yy ** 2); ys = cy + ry * yy * 0.94
            ribs.append(_tube(np.stack([xs, ys], 1), 1.1, 1.1, per=2)[0])
        groups.append((ribs, self._far(base[None] * 0.55, far), 0.55))
        groups.append(([np.array([(x - rx * 0.45, cy + ry * 0.86), (x + rx * 0.45, cy + ry * 0.86),
                                  (x + rx * 0.4, cy + ry + h * 0.1), (x - rx * 0.4, cy + ry + h * 0.1)], np.float32)],
                       self._far(hexc('#8a6a2c')[None], far), 1.0))
        ty = cy + ry + h * 0.1
        tas = [_tube([(x + dx, ty), (x + dx * 1.4 + r.normal(0, 0.6), ty + h * 0.55)], 1.2, 0.8, per=2)[0] for dx in np.linspace(-rx * 0.22, rx * 0.22, 7)]
        groups.append((tas, self._far(base[None] * 0.9, far), 0.95))
        groups.append(([np.stack([x + 2.2 * np.cos(t), ty + 2.5 + 2.2 * np.sin(t)], 1).astype(np.float32)], self._far(hexc('gold')[None], far), 1.0))
        self._paint(groups, 3, 0.02)

    def plaque(self, cx, cy, w, h, text, board='board', letters='gold', frame='#6b4a2f', far=0.0, size=None, font=None):
        """a framed name board with gilded characters (read left to right)"""
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        groups = [([np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], np.float32)], self._far(hexc(frame)[None], far), 1.0)]
        b = 3.0
        groups.append(([np.array([(x0 + b, y0 + b), (x1 - b, y0 + b), (x1 - b, y1 - b), (x0 + b, y1 - b)], np.float32)],
                       self._far(hexc(board)[None], far), 1.0))
        groups.append(([np.array([(x0, y0), (x1, y0), (x1, y0 + 1.4), (x0, y0 + 1.4)], np.float32)], self._far(mix(frame, '#f0d7a0', 0.4)[None], far), 0.9))
        self._paint(groups, 3, 0.03)
        fp = font or cjk_font()
        if not fp: return
        size = size or h * 0.66
        f = ImageFont.truetype(fp, int(size * 3))
        im = Image.new('L', (int(w * 3), int(h * 3)), 0)
        ImageDraw.Draw(im).text((w * 1.5, h * 1.5), text, font=f, fill=255, anchor='mm')
        m = np.asarray(im.resize((int(w), int(h)), Image.BOX), np.float32) / 255
        x0i, y0i = int(round(x0)), int(round(y0))
        sl = (slice(y0i, y0i + m.shape[0]), slice(x0i, x0i + m.shape[1]))
        sh = np.zeros_like(m); sh[1:, 1:] = m[:-1, :-1]
        g = hexc(letters)
        A = sh * 0.6
        self.C[sl] = self.C[sl] * (1 - A[..., None]) + self._far(hexc('#120d0a')[None, None], far) * A[..., None]
        yy = np.linspace(0, 1, m.shape[0], dtype=np.float32)[:, None, None]
        gc = self._far(mix(g, '#fff0c0', 0.3) * (1 - yy) + g * 0.85 * yy, far)
        self.C[sl] = self.C[sl] * (1 - m[..., None]) + gc * m[..., None]

    # ================================================================== water
    def lake(self, y0, y1, far_colour='water_far', near_colour='water_deep', mid='water', bank=None, seed=None):
        """the still jade body colour: paler far away (where it mirrors the hazy sky), deeper toward the viewer"""
        r = self._r(seed)
        y0, y1 = int(y0), int(y1)
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]
        t = ((yy - y0) / max(1, y1 - y0)) ** 0.8
        c = np.where(t[..., None] < 0.35, mix(far_colour, mid, 0)[None, None] * (1 - t[..., None] / 0.35) + hexc(mid) * (t[..., None] / 0.35),
                     hexc(mid) * (1 - (t[..., None] - 0.35) / 0.65) + hexc(near_colour) * ((t[..., None] - 0.35) / 0.65))
        n = noise2d(y1 - y0, self.W, 120, 3, int(r.integers(1 << 30)))
        c = c * (0.97 + 0.06 * n[..., None])
        A = np.ones((y1 - y0, self.W), np.float32)
        if bank is not None:
            b = np.broadcast_to(np.asarray(bank, np.float32), (self.W,))
            A = smoothstep(b[None] - 0.5, b[None] + 1.0, yy)
        if self._clip is not None: A = A * self._clip[y0:y1]
        self.C[y0:y1] += (np.broadcast_to(c, (y1 - y0, self.W, 3)) - self.C[y0:y1]) * A[..., None]
        self.water_y0, self.water_y1 = y0, y1
        self.water_bank = np.broadcast_to(np.asarray(bank if bank is not None else y0, np.float32), (self.W,)).copy()
        self._water_body = self.C.copy()

    def reflect(self, bank=None, strength=0.85, blur=(2.0, 9.0), ripple=2.2, darken=0.82, tint='water', fresnel=0.55,
                y1=None, src=None, mask=None, seed=None):
        """mirror what stands above the bank line into the water: rippled sideways, blurred vertically (more with
        distance), darkened and mixed with the body colour (more toward the viewer)"""
        r = self._r(seed)
        bank = self.water_bank if bank is None else np.broadcast_to(np.asarray(bank, np.float32), (self.W,))
        S = self.C if src is None else src
        y0 = int(np.floor(bank.min())); y1 = int(self.H if y1 is None else y1)
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]
        xx = np.arange(self.W, dtype=np.float32)[None]
        dist = yy - bank[None]
        ph = fbm1d(y1 - y0 + 1, 9, 3, int(r.integers(1 << 30)))[: y1 - y0, None]
        rn = noise2d(y1 - y0, self.W, 40, 2, int(r.integers(1 << 30))) - 0.5
        dx = ripple * (np.sin(yy * 0.9 + ph * 6) * 0.6 + rn * 1.6) * (0.4 + 0.6 * np.clip(dist / 200, 0, 1.5))
        sy = np.clip(np.round(bank[None] - dist * 1.0), 0, self.H - 1).astype(np.int32)
        sx = np.clip(np.round(xx + dx), 0, self.W - 1).astype(np.int32)
        Rf = S[sy, sx]
        b1 = _blur1(Rf, blur[0], 0); b2 = _blur1(_blur1(Rf, blur[1], 0), 1.2, 1)
        k = np.clip(dist / 260, 0, 1)[..., None]
        Rf = b1 * (1 - k) + b2 * k
        body = self._water_body[y0:y1]
        Rf = Rf * darken
        fr = np.clip(dist / max(1, self.H - bank.mean()), 0, 1)[..., None]
        Rf = Rf * (1 - fresnel * fr) + body * fresnel * fr
        Rf = Rf * 0.86 + hexc(tint) * 0.14
        A = (dist > 0).astype(np.float32) * strength
        A = A * smoothstep(0, 3, dist)
        if mask is not None: A = A * mask[y0:y1]
        if self._clip is not None: A = A * self._clip[y0:y1]
        Cs = self.C[y0:y1]
        Cs += (Rf - Cs) * A[..., None]

    def layer(self):
        """snapshot before painting something that stands in the water (see reflect_layer)"""
        return self.C.copy()

    def reflect_layer(self, before, axis, box, strength=0.75, blur=(1.5, 5.0), ripple=1.5, darken=0.72, below=None, seed=None):
        """mirror only what was painted since `before` (a boat, an egret) about its waterline row `axis`"""
        r = self._r(seed)
        x0, y0, x1, y1 = (int(v) for v in box)
        x0, x1 = max(0, x0), min(self.W, x1); y0 = max(0, y0)
        axis = int(axis)
        D = self.C[y0:axis] - before[y0:axis, :, :][..., :]
        D = D[:, x0:x1]
        A = (np.abs(D).max(-1) > 0.004).astype(np.float32)
        hgt = axis - y0
        yb = int(min(self.H, axis + hgt * 1.0))
        n = yb - axis
        if n <= 0: return
        src = self.C[y0:axis, x0:x1] * A[..., None]
        M = src[::-1][:n]; Am = A[::-1][:n]
        yy = np.arange(n, dtype=np.float32)[:, None]
        sh = np.round(ripple * np.sin(yy * 0.8 + r.uniform(0, 6))).astype(int)
        Mx = np.empty_like(M); Ax = np.empty_like(Am)
        for i in range(n):
            Mx[i] = np.roll(M[i], sh[i, 0], 0); Ax[i] = np.roll(Am[i], sh[i, 0], 0)
        Mx = _blur1(_blur1(Mx, blur[1], 0), blur[0], 1); Ax = _blur1(_blur1(Ax, blur[1], 0), blur[0], 1)
        col = Mx / np.maximum(Ax[..., None], 1e-3) * darken
        body = self._water_body[axis:yb, x0:x1]
        col = col * 0.8 + body * 0.2
        a = np.clip(Ax, 0, 1) * strength * (1 - 0.5 * yy / max(1, n))
        if below is not None: a = a * below[axis:yb, x0:x1]
        Cs = self.C[axis:yb, x0:x1]
        Cs += (col - Cs) * a[..., None]

    def ripples(self, box, n=400, light='#d6e6e0', dark=None, alpha=0.35, length=(10, 60), brush=1.0, seed=None):
        """faint horizontal ripple lines: pale where they catch the sky, dark where they catch the bank;
        longer and thicker toward the viewer; plus a fine vertical streak texture over the water"""
        r = self._r(seed)
        x0, y0, x1, y1 = box
        y = y0 + (y1 - y0) * r.random(n) ** 0.8
        t = (y - y0) / max(1, y1 - y0)
        x = r.uniform(x0, x1, n)
        L = r.uniform(*length, n) * (0.4 + 0.9 * t)
        wd = 0.8 + 1.6 * t
        cols = np.repeat(hexc(light)[None], n, 0)
        if dark is not None:
            dk = r.random(n) < 0.45
            cols[dk] = hexc(dark)
        if brush:
            k = int((x1 - x0) * (y1 - y0) / 260 * brush)
            bx = r.uniform(x0, x1, k); by = y0 + (y1 - y0) * r.random(k) ** 0.9
            bank = getattr(self, 'water_bank', None)
            if bank is not None:
                ok = by > bank[np.clip(bx.astype(int), 0, self.W - 1)] + 3
                bx, by = bx[ok], by[ok]
            tb = (by - y0) / max(1, y1 - y0)
            bc = self.C[np.clip(by.astype(int), 0, self.H - 1), np.clip(bx.astype(int), 0, self.W - 1)] * r.uniform(0.95, 1.05, (len(bx), 1))
            self.dabs(bx, by, r.uniform(20, 70, len(bx)) * (0.5 + tb), 1.5 + 3 * tb, bc, r.normal(0, 0.015, len(bx)), 'leaf', 0.4, 0.0, 2, 0.0)
        self.dabs(x, y, L, wd, cols, r.normal(0, 0.01, n), 'leaf', alpha, 0.0, 2, 0.0)
        ya, yb = int(y0), int(y1)
        st = _blur1(_blur1(r.normal(0, 1, (yb - ya, self.W)).astype(np.float32), 14, 0), 0.7, 1)
        st = st / (st.std() + 1e-6)
        A = np.zeros((yb - ya, self.W), np.float32); A[:, int(x0):int(x1)] = 1
        if self._clip is not None: A = A * self._clip[ya:yb]
        bank = getattr(self, 'water_bank', None)
        if bank is not None: A = A * (np.arange(ya, yb)[:, None] > bank[None] + 1)
        self.C[ya:yb] *= (1 + 0.013 * st * A)[..., None]

    def lily_pads(self, pads, ramp_='pad', far=0.0, flowers=(), seed=None):
        """water-lily pads lying on the lake: pads = [(X, Z, radius_m), ...] through the camera; each pad an
        ellipse with its notch, a shadow, lit veins and a pale rim, some curled to show a red underside"""
        r = self._r(seed)
        R = ramp(ramp_)
        pads = sorted(pads, key=lambda p: -p[1])
        e = self.cam[1]
        groups_sh, groups, rims, veins, shades = [], [], [], [], []
        csh, cpad, crim, cvn, cshade = [], [], [], [], []
        for X, Z, rad in pads:
            x, y = self.project(X, 0.0, Z)
            rx = float(self.px_per_m(Z) * rad); ry = rx * min(0.6, e / Z * 1.35)
            rot = r.uniform(0, 2 * np.pi)
            gap = r.uniform(0.32, 0.5)
            t = np.linspace(rot + gap / 2, rot + 2 * np.pi - gap / 2, 30)
            rr = 1 + 0.03 * r.normal(0, 1, len(t))
            pts = np.vstack([np.stack([x + rx * rr * np.cos(t), y + ry * rr * np.sin(t)], 1), [(x + rx * 0.05 * np.cos(rot), y)]]).astype(np.float32)
            groups_sh.append(pts + np.array([1.0, max(1.0, ry * 0.18)], np.float32)); csh.append(hexc('water_deep') * 0.6)
            lv = r.uniform(0.35, 0.7)
            groups.append(pts); cpad.append(ramp_at(R, lv))
            if r.random() < 0.12:
                t2 = np.linspace(np.pi * 0.25, np.pi * 0.75, 12)
                cr = np.vstack([np.stack([x + rx * np.cos(t2), y + ry * np.sin(t2)], 1),
                                np.stack([x + rx * 0.95 * np.cos(t2[::-1]), y + ry * 0.86 * np.sin(t2[::-1]) - ry * 0.04], 1)]).astype(np.float32)
                rims.append(cr); crim.append(mix('#8a5040', '#b07a5a', r.random()))
            t4 = np.linspace(0.1, np.pi - 0.1, 12)
            sh2 = np.vstack([np.stack([x + rx * 0.98 * np.cos(t4), y + ry * 0.98 * np.sin(t4)], 1),
                             np.stack([x + rx * 0.55 * np.cos(t4[::-1]), y + ry * 0.3 * np.sin(t4[::-1])], 1)]).astype(np.float32)
            shades.append(sh2); cshade.append(ramp_at(R, lv - 0.22))
            t3 = np.linspace(np.pi * 1.05, np.pi * 1.95, 12)
            ar = np.vstack([np.stack([x + rx * 0.97 * np.cos(t3), y + ry * 0.97 * np.sin(t3)], 1),
                            np.stack([x + rx * 0.86 * np.cos(t3[::-1]), y + ry * 0.8 * np.sin(t3[::-1])], 1)]).astype(np.float32)
            rims.append(ar); crim.append(mix(ramp_at(R, lv + 0.25), '#cfe0d6', 0.25))
            for va in np.linspace(rot + 0.6, rot + 2 * np.pi - 0.6, 6):
                veins.append(_tube([(x, y), (x + rx * 0.85 * np.cos(va), y + ry * 0.85 * np.sin(va))], max(0.6, rx * 0.03), 0.4, per=2)[0])
                cvn.append(ramp_at(R, lv + 0.22))
        self._paint([(groups_sh, np.array(csh), 0.4)], 2, 0.0)
        self._paint([(groups, self._far(np.array(cpad) + r.normal(0, 0.015, (len(cpad), 3)), far), 1.0),
                     (shades, self._far(np.array(cshade), far), 0.45), (veins, self._far(np.array(cvn), far), 0.4),
                     (rims, self._far(np.array(crim), far), 0.75)], 2, 0.04)
        for X, Z, s in flowers:
            x, y = self.project(X, 0.0, Z)
            self.lotus(float(x), float(y), float(self.px_per_m(Z) * s), far=far)

    def lotus(self, x, y, s, kind='pink', far=0.0, seed=None):
        """a pink water lily lying on its pad: a flat ring of outer petals, an upright cup of inner petals, gold heart"""
        r = self._r(seed)
        R = ramp(kind)
        groups = []
        k = 10
        a = np.linspace(0, 2 * np.pi, k, endpoint=False) + r.uniform(0, 1)
        flat = 0.42
        ox, oy = np.cos(a) * s * 0.42, np.sin(a) * s * 0.42 * flat
        ang = np.arctan2(oy, ox)
        back = oy < 0
        lv = np.where(back, 0.35, 0.55) + r.uniform(-0.08, 0.08, k)
        o = np.argsort(oy)
        groups.append((self._shapes(x + ox[o], y + oy[o], np.full(k, s * 0.62), np.full(k, s * 0.2), ang[o], 'leaf', 0.05, r),
                       self._far(ramp_at(R, lv[o]), far), 1.0))
        m = 7
        a2 = np.linspace(-np.pi * 0.85, -np.pi * 0.15, m) + r.normal(0, 0.06, m)
        cx_ = x + np.cos(a2) * s * 0.14; cy_ = y - s * 0.12 + np.sin(a2) * s * 0.18
        lv2 = 0.62 + 0.3 * (np.cos(a2) < 0) + r.uniform(-0.05, 0.05, m)
        groups.append((self._shapes(cx_, cy_, np.full(m, s * 0.5), np.full(m, s * 0.18), a2, 'leaf', 0.05, r),
                       self._far(ramp_at(R, lv2), far), 1.0))
        groups.append((self._shapes(np.array([x]), np.array([y - s * 0.08]), np.array([s * 0.2]), np.array([s * 0.07]), 0, 'round', 0.0, r),
                       self._far(hexc('#f0c95a')[None], far), 1.0))
        groups.append((self._shapes(cx_, cy_ - s * 0.06, np.full(m, s * 0.18), np.full(m, s * 0.05), a2, 'leaf', 0.0, r),
                       self._far(ramp_at(R, np.full(m, 1.0)), far), 0.8))
        self._paint(groups, 3, 0.0)

    def boat(self, x0, x1, y, h=26, colour='wood', far=0.0, pole=True, seed=None):
        """a small wooden boat lying along the bank, waterline at row y, seen a little from above"""
        r = self._r(seed)
        n = 40
        t = np.linspace(0, 1, n)
        L = x1 - x0
        xs = x0 + L * t
        sheer = y - h - h * 0.95 * np.abs(2 * t - 1) ** 3.2
        far_g = sheer - h * 0.42 * (1 - np.abs(2 * t - 1) ** 2.4)
        wl = y + 1.5 * np.sin(t * np.pi)
        base = hexc(colour)
        groups = []
        inner = np.vstack([np.stack([xs, far_g], 1), np.stack([xs[::-1], sheer[::-1]], 1)]).astype(np.float32)
        groups.append(([inner], self._far((base * 0.55)[None], far), 1.0))
        floor = np.vstack([np.stack([xs[8:-8], (far_g[8:-8] * 0.4 + sheer[8:-8] * 0.6)], 1),
                           np.stack([xs[8:-8][::-1], sheer[8:-8][::-1] - 1], 1)]).astype(np.float32)
        groups.append(([floor], self._far((base * 0.8)[None], far), 1.0))
        ribs = []
        for tt in np.linspace(0.2, 0.8, 6):
            i = int(tt * (n - 1))
            ribs.append(_tube([(xs[i], far_g[i]), (xs[i], sheer[i])], 1.6, 1.6, per=2)[0])
        groups.append((ribs, self._far((base * 0.4)[None], far), 0.9))
        hull = np.vstack([np.stack([xs, sheer], 1), np.stack([xs[::-1], wl[::-1]], 1)]).astype(np.float32)
        groups.append(([hull], self._far(base[None] * 0.9, far), 1.0))
        for k, f in enumerate((0.33, 0.62)):
            yk = sheer + (wl - sheer) * f
            groups.append(([_tube(np.stack([xs[2:-2], yk[2:-2]], 1), 1.2, 1.2, per=1)[0]], self._far((base * 0.6)[None], far), 0.8))
        band = np.vstack([np.stack([xs, sheer - 1.5], 1), np.stack([xs[::-1], sheer[::-1] + 3.2], 1)]).astype(np.float32)
        groups.append(([band], self._far(mix(base, '#e8d2a8', 0.45)[None], far), 1.0))
        dk = np.vstack([np.stack([xs, wl - h * 0.25], 1), np.stack([xs[::-1], wl[::-1]], 1)]).astype(np.float32)
        groups.append(([dk], self._far((base * 0.55)[None], far), 0.6))
        gl = np.vstack([np.stack([xs, far_g - 1.2], 1), np.stack([xs[::-1], far_g[::-1] + 1.8], 1)]).astype(np.float32)
        groups.append(([gl], self._far(mix(base, '#d9c39a', 0.3)[None], far), 1.0))
        if pole:
            groups.append(([_tube([(x0 + L * 0.18, far_g[7] - 2), (x0 + L * 0.95, far_g[-6] - h * 0.6)], 2.4, 2.0, per=2)[0]],
                           self._far(hexc('#c2a46a')[None], far), 1.0))
        self._paint(groups, 2, 0.05)

    def egret(self, x, y, s=40, pose='stand', facing=-1, far=0.0, seed=None):
        """a little white egret: standing (feet at (x, y), s = height) or flying (body at (x, y), s = wing length)"""
        r = self._r(seed)
        W_ = hexc('egret'); Sh = mix('egret', '#93a2b4', 0.5); Mid = mix('egret', '#b9c3cc', 0.5)
        f = float(facing)
        t = np.linspace(0, 2 * np.pi, 40)

        def P(pts):
            q = np.asarray(pts, np.float32).copy(); q[:, 0] = x + f * q[:, 0] * s; q[:, 1] = y + q[:, 1] * s
            return q
        groups = []
        if pose == 'stand':
            legs = [_tube(P([(0.02, -0.44), (0.0, -0.22), (-0.01, 0.0)]), s * 0.022, s * 0.016, per=3)[0],
                    _tube(P([(-0.04, -0.44), (-0.09, -0.24), (-0.1, -0.02)]), s * 0.022, s * 0.016, per=3)[0]]
            groups.append((legs, self._far(hexc('#26251f')[None], far), 1.0))
            body = np.stack([0.24 * np.cos(t), 0.1 * np.sin(t)], 1)
            rot = 0.42
            body = np.stack([body[:, 0] * np.cos(rot) - body[:, 1] * np.sin(rot), body[:, 0] * np.sin(rot) + body[:, 1] * np.cos(rot)], 1)
            body = body + np.array([-0.02, -0.52])
            body[:, 1] -= np.clip(body[:, 0], 0, None) * 0.15
            groups.append(([P(body)], self._far(Mid[None], far), 1.0))
            groups.append(([P(body * np.array([0.92, 0.86]) + np.array([0.0, -0.075]))], self._far(W_[None], far), 1.0))
            tail = [(-0.18, -0.48), (-0.32, -0.36), (-0.3, -0.33), (-0.14, -0.43)]
            groups.append(([P(tail)], self._far(Sh[None], far), 1.0))
            neck = [(0.13, -0.6), (0.2, -0.72), (0.12, -0.83), (0.11, -0.93), (0.17, -1.0)]
            groups.append(([_tube(P(neck), s * 0.075, s * 0.055, per=6)[0]], self._far(W_[None], far), 1.0))
            groups.append(([P(np.stack([0.18 + 0.055 * np.cos(t), -1.0 + 0.042 * np.sin(t)], 1))], self._far(W_[None], far), 1.0))
            groups.append(([P([(0.22, -1.015), (0.46, -0.99), (0.22, -0.985)])], self._far(hexc('#d9a53a')[None], far), 1.0))
            groups.append(([P(np.stack([0.2 + 0.012 * np.cos(t), -1.012 + 0.012 * np.sin(t)], 1))], self._far(hexc('#1a1a18')[None], far), 1.0))
            groups.append(([_tube(P([(0.1, -0.56), (0.02, -0.5), (-0.12, -0.44)]), s * 0.03, s * 0.01, per=3)[0]],
                           self._far(Sh[None], far), 0.7))
        else:
            def wing(root, tip, sweep, width, k=14):
                # a broad rounded wing from a root on the back to a tip, its trailing edge swept back
                rt, tp = np.array(root, np.float32), np.array(tip, np.float32)
                tt = np.linspace(0, 1, k)[:, None]
                lead = rt + (tp - rt) * tt + np.array([0.06, 0.0]) * np.sin(tt * np.pi)
                trail = rt + np.array([-width, 0.04]) + (tp - rt - np.array([-width, 0.04])) * tt + np.array([-sweep, 0.0]) * np.sin(tt * np.pi)
                return np.vstack([lead, trail[::-1]])
            groups.append(([P(wing((0.1, -0.03), (0.18, -0.8), 0.1, 0.2))], self._far(Sh[None], far), 1.0))
            groups.append(([P(np.stack([0.27 * np.cos(t), 0.075 * np.sin(t)], 1) + np.array([0.0, 0.015]))], self._far(Mid[None], far), 1.0))
            groups.append(([P(np.stack([0.25 * np.cos(t), 0.055 * np.sin(t)], 1))], self._far(W_[None], far), 1.0))
            groups.append(([_tube(P([(0.18, -0.01), (0.27, -0.06), (0.31, -0.04)]), s * 0.075, s * 0.055, per=3)[0]], self._far(W_[None], far), 1.0))
            groups.append(([P([(0.33, -0.055), (0.56, -0.03), (0.33, -0.025)])], self._far(hexc('#d9a53a')[None], far), 1.0))
            groups.append(([_tube(P([(-0.2, 0.02), (-0.44, 0.05), (-0.6, 0.06)]), s * 0.02, s * 0.015, per=2)[0]],
                           self._far(hexc('#26251f')[None], far), 1.0))
            nw = wing((0.06, -0.02), (-0.16, -0.9), 0.16, 0.26)
            groups.append(([P(nw)], self._far(W_[None], far), 1.0))
            for k in range(5):
                tp = np.array([-0.16 - 0.05 * k, -0.9 + 0.07 * k])
                groups.append(([P([tp + (0.03, 0.02), tp + (-0.06, -0.01), tp + (0.0, 0.08)])], self._far(W_[None], far), 1.0))
            groups.append(([P(wing((0.0, -0.03), (-0.14, -0.62), 0.08, 0.12) + np.array([-0.04, 0.02]))], self._far(Mid[None], far), 0.5))
        self._paint(groups, 3, 0.0)

    # ================================================================== finish
    def seal(self, x, y, w=26, h=46, text='春水', colour='seal', seed=None):
        """a small red seal, characters cut out in white, edges worn"""
        r = self._r(seed)
        x0, y0 = int(x), int(y); w, h = int(w), int(h)
        ss = 3
        im = Image.new('L', (w * ss, h * ss), 0); d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w * ss - 1, h * ss - 1], fill=255)
        fp = cjk_font()
        if fp:
            n = len(text)
            fs = int(min(w * 0.78, h * 0.86 / n) * ss)
            f = ImageFont.truetype(fp, fs)
            for i, ch in enumerate(text):
                d.text((w * ss / 2, (h * (i + 0.5) / n) * ss), ch, font=f, fill=0, anchor='mm')
        d.rectangle([2 * ss, 2 * ss, w * ss - 2 * ss - 1, h * ss - 2 * ss - 1], outline=0, width=ss)
        m = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        n = noise2d(h, w, 5, 2, int(r.integers(1 << 30)))
        m = m * smoothstep(0.06, 0.22, n + 0.25)
        edge = np.ones_like(m); edge[0, :] *= r.uniform(0.3, 1, w); edge[-1, :] *= r.uniform(0.3, 1, w)
        edge[:, 0] *= r.uniform(0.3, 1, h); edge[:, -1] *= r.uniform(0.3, 1, h)
        A = np.clip(m * edge, 0, 1) * 0.96
        sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        c = hexc(colour)[None, None] * (0.94 + 0.12 * n[..., None])
        self.C[sl] = self.C[sl] * (1 - A[..., None]) + c * A[..., None]

    def grain(self, amount=1.0):
        """finish: slight painterly softness, fine grain and the faintest canvas weave (applied in render)"""
        self.grain_amt = float(amount)

    def render(self):
        out = self.C
        p = self.grain_amt
        if p:
            soft = np.stack([blur(out[..., i], 0.9) for i in range(3)], -1)
            out = out * (1 - 0.32 * p) + soft * 0.32 * p
            lum = out.mean(-1)
            glow = blur(np.clip(lum - 0.6, 0, 1), 16)
            out = out + p * 0.22 * glow[..., None] * hexc('#fff3dc')
            lum = out.mean(-1, keepdims=True)
            out = lum + (out - lum) * (1 - 0.05 * p)
            out = out + p * 0.035 * (1 - lum) ** 2 * (hexc('#3d6470') - 0.25)
            if not hasattr(self, '_grain'):
                r = np.random.default_rng(self.seed + 7)
                g = r.normal(0, 1, (self.H, self.W)).astype(np.float32)
                g = 0.6 * g + 0.4 * blur(g, 0.9) * 2.0
                yy = np.arange(self.H, dtype=np.float32)[:, None]; xx = np.arange(self.W, dtype=np.float32)[None]
                weave = np.sin(xx * 2.1 + 0.5 * np.sin(yy * 0.07)) * np.sin(yy * 2.0) * 0.5
                st = _blur1(r.normal(0, 1, (self.H, self.W)).astype(np.float32), 5, 0)
                st = st / (st.std() + 1e-6)
                self._grain = (0.013 * g + 0.006 * weave + 0.006 * st).astype(np.float32)
            out = out * (1 + p * self._grain[..., None])
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
