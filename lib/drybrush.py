"""drybrush — 干刷色块 / Dry-Brush Blocks: a mid-century poster / gouache-collage illustration built from a few big
dry-brushed blocks of colour on cream paper (numpy + Pillow only).

The look: a confident editorial illustration in a strictly limited palette (forest and sage green, teal-blue, navy,
a near-black, vermilion, a little sky blue and pale celadon, cream). Every form is a handful of big flat-ish planes
laid with a dry, loaded brush or a roller: ragged, combed ends where the brush lifted, streaky drag marks and
scratchy scumble inside the block, paper showing through. Blocks overlap like layered screenprint or torn-paper
collage; a solid slab of colour stands behind the subject; one small red square sits off to the side. No outlines,
no gradients. Nothing here is a filter on flat shapes: every block is laid by a modelled brush on a modelled sheet.

Physical model
  brush frame  Each block is painted in its own frame: the mask is rotated (Pillow) so the stroke direction runs
               along +u, everything is computed there with axis-aligned arrays, and the coverage, value and
               colour-mix fields are rotated back. So bristle streaks, lanes and dry ends always follow the stroke.
  textures     Four tiles are made once per canvas in the brush frame: a bristle streak texture (noise grids that
               are ~40 px long and ~1 px across, upsampled), a dry tooth (those streaks + an isotropic paper grain,
               histogram-equalised to 0..1, so "paint reaches the tooth where tooth > 1 - contact" turns a contact
               pressure straight into a coverage fraction), broad lanes (value variation of the brush passes) and a
               stretched mottle (where a dry, scumbled pass skips). Every block reads them at a random offset.
  lanes        A big block is laid in parallel passes of a wide brush or roller (`lane` px, each a little wider or
               narrower). A pass starts loaded where it enters the shape and runs dry toward its end (`dry`), so the
               ends break into streaks; `direction` says which way the passes run (+1, -1, 0 random, 2 back and
               forth). Passes differ a little in value (`vary`) and leave faint seams (`seam`); `passes=2` lays a
               second set over the first so the body closes up while the ends stay streaky.
  edges        The mask is softened a little across the stroke (`side`: a slightly wobbly cut edge) and a lot along
               it (`fringe`), then thresholded against the bristle streaks: the sides come out nearly straight, the
               ends come out as a comb of tines of different lengths, longer at the dry end (`tines`).
  scumble      Inside the block the contact pressure dips where the mottle is high (`scumble`), so paint only
               catches the tooth there: scratchy patches with paper (or the colour below) showing through. Dry
               stretches along the outline (`edge`) sit mostly on the sides that run along the stroke.
  roller       `tooth='roller'` swaps the bristle tooth for a roller / sponge one (isotropic speckle in clusters),
               so a big slab stays nearly flat with stippled dry sides; `backdrop()` uses it, starts each pass loaded
               at the top and adds a few fine `scratches()` (thin lines a little paler than the paint).
  colour       Opaque gouache by default: new = old + (colour - old) * coverage, so a dry pass over another block
               lets the block below show through its streaks. `mode='multiply'` overprints like screen ink (two pale
               pieces make a darker overlap). A second colour can ride in the same brush (`mix`), as streaks.
  pieces       `piece()` is a torn / cut paper piece: the outline is displaced by fractal noise only along some
               stretches (the rest stays a clean cut), with an optional pale fibrous rim on the torn bits; inside it
               is painted paper (a dry block with a full load).
  strokes      `stroke()` lays one dry brush mark along a path: every pixel knows its arc length and offset across
               (Pillow rasterises segment ids, then exact projection), so the tooth streaks run along the curve,
               the brush tapers and runs dry along its length. `scumble()` scatters short dry strokes in a mask
               (beards, hair, steam, highlights).
  figures      `head()`, `glasses()`, `beard()`, `jacket()`, `sleeve()`, `hand()` build a person from a few big
               planes: a warm tan head with a lit plane, a shadow plane, a darker nose side with a warm tip, a warm
               cheek and ear, cropped hair (or a bald crown); rough black glasses; a white beard and moustache as dry
               scumble; a jacket whose lit and dark halves are brushed in different directions, lapels, a shirt V
               and a collar; sleeves brushed along the arm; a hand seen from the thumb side as stacked finger
               bands. Every helper works in a local unit frame (centre, size, tilt), so poses are a few numbers.
  vessels      `bottle()` is a silhouette (body, shoulder, neck, lip) brushed vertically with a dark side and one
               light streak, a label as a small block (or two), a cap; `bowl()` and `cup()` are side views.
  accents      `accent()` is a small, nearly solid square (vermilion by default) with a clean cut edge.
  print        `printed()` finishes like an offset print of the painting: a slight softness, a fine paper grain,
               sparse paper-coloured specks knocked out of the darks and sparse dust on the paper.

API (canvas px; angles in degrees, 0 = to the right, 90 = down; colours are names in PAINTS or '#rrggbb')
  paper    DryBrushBlocks(W, H, seed, keep_stages, stages_dir); paper(tone)
  shapes   rect(x0, y0, x1, y1, rot), poly(pts, smooth), ellipse(cx, cy, rx, ry, rot), tube(path, w0, w1),
           quad(pts) -> canvas-size float masks
  blocks   slab(shape, colour, angle, load, dry, lane, fringe, side, tines, scumble, streak, vary, direction,
                passes, seam, edge, stagger, dry_from, stroke_len, tooth, mix, mode, alpha, avoid, clip)
                the dry-brushed block (returns its coverage)
           piece(shape, colour, torn, cut, rim, angle, load, mode, ...)  torn / cut paper piece
           backdrop(box, colour, angle, rough, scratches, ...)  the big roller slab behind the subject;
           accent(x, y, size, colour, rot)  the small solid square; scratches(mask, colour, n, length, width)
  marks    stroke(path, width, colour, load, dry, taper, wobble, square, mode, alpha, clip); scumble(mask, colour,
           n, length, width, angle, spread, load, dry, clip)
  figures  head(cx, cy, w, h, tilt, turn, light, skin, lit, shade, warm, ear, hair, crown) -> dict;
           glasses(head, colour, lens, frame); beard(head, colour, shade, length, width); jacket(neck, shoulders,
           bottom, lit, shade, dark, shirt, collar, light); sleeve(path, w0, w1, colour); hand(x, y, size, angle,
           grip, cuff)
  vessels  bottle(x, base, w, h, ...), bowl(cx, rim_y, w, h, ...), cup(cx, base, w, h, ...)
  finish   printed(amount); render(); composite(); stage(name); save(path, stages_dir)

    import sys; sys.path.insert(0, 'lib')
    from drybrush import DryBrushBlocks
    d = DryBrushBlocks(1600, 1200, seed=3)
    d.paper()
    d.backdrop((180, 90, 1120, 820), 'slab')                          # the green roller slab behind the subject
    d.slab(d.poly([(380, 520), (900, 500), (980, 830), (330, 830)]), 'navy', angle=-70, dry=0.4, stroke_len=180)
    H = d.head(640, 330, 230, 280, hair='bone'); d.glasses(H); d.beard(H)
    d.bottle(1250, 830, 110, 380, 'forest', label=('cream', 0.45, 0.7))
    d.accent(1380, 930, 58)
    d.printed(); d.save('drybrush.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, noise2d, smoothstep, spline, polygon_mask, blob_pts


PAINTS = {
    'paper': '#f2eee5', 'cream': '#efe8d6', 'bone': '#e2d9c3', 'white': '#f6f2e8',
    'ink': '#0c1611', 'black': '#101310',
    'forest': '#1d5636', 'green': '#2a7a4b', 'slab': '#5a865f', 'sage': '#77a26f', 'leaf': '#4f9a52',
    'ash': '#bdb7a6', 'celadon': '#c4dabf', 'mint': '#a9cdb4', 'khaki': '#8d8b66',
    'teal': '#0d6b67', 'lagoon': '#14919a', 'tealblue': '#14566b', 'navy': '#173a57', 'deep': '#0f2b3a',
    'sky': '#a2cadb', 'ice': '#d4e5e6',
    'vermilion': '#e0431f', 'tomato': '#e65a37', 'coral': '#ec8a68', 'blush': '#f0b7a0',
    'ochre': '#9b7f56', 'tan': '#bf9a6c', 'skin': '#c88f62', 'skin_light': '#dcb48a', 'terracotta': '#bc6845',
    'umber': '#5a3521', 'brown': '#3b2417', 'mustard': '#d2a13e',
}


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 RGB 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _equalise(t, bins=1024):
    hist, edges = np.histogram(t, bins)
    cdf = np.cumsum(hist).astype(np.float32); cdf /= cdf[-1]
    return np.interp(t, edges[1:], cdf).astype(np.float32)


def _blur1(a, sigma, axis, mode='constant'):
    """1D gaussian-ish blur along one axis (3 box passes via cumulative sums); mode 'constant' (zero outside, for
    masks) or 'wrap' (periodic, for noise tiles)"""
    if sigma <= 0.3: return a
    out = a.astype(np.float32)
    w = int(np.sqrt(12 * sigma * sigma / 3 + 1)); w += (w % 2 == 0)
    r = w // 2
    for _ in range(3):
        pad = [(0, 0), (0, 0)]; pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(out, pad, mode=mode), axis=axis, dtype=np.float64)
        hi = np.take(c, np.arange(w, c.shape[axis]), axis=axis)
        lo = np.take(c, np.arange(0, c.shape[axis] - w), axis=axis)
        out = ((hi - lo) / w).astype(np.float32)
    return out


def _aniso(N, cu, cv, rng):
    """N x N periodic, stationary noise (z-scored) whose features are ~cu px long along x (u) and ~cv px across
    (v): white noise blurred anisotropically with wrap-around, made at 1/f resolution along u and stretched back
    (no grid alignment, so thresholding it never makes rungs; periodic, so tiles can be indexed mod N)"""
    f = int(max(1, min(8, cu // 8)))
    while N % f: f -= 1
    n = N // f
    a = rng.random((N, n)).astype(np.float32)
    a = _blur1(a, max(0.35, cu / f / 2.6), 1, 'wrap')
    if cv > 1.1: a = _blur1(a, cv / 2.6, 0, 'wrap')
    if f > 1:
        a = np.concatenate([a[:, -1:], a, a[:, :1]], 1)
        a = np.asarray(Image.fromarray(a, 'F').resize(((n + 2) * f, N), Image.BILINEAR), np.float32)
        a = a[:, f:f + N]
    return ((a - a.mean()) / (a.std() + 1e-6)).astype(np.float32)


def _rot(a, angle, resample=Image.BILINEAR):
    """rotate a float array counter-clockwise by `angle` deg with expand (a stroke at canvas angle -> +u)"""
    if abs(angle) % 360 < 1e-6: return np.ascontiguousarray(a, np.float32)
    return np.asarray(Image.fromarray(np.ascontiguousarray(a, np.float32), 'F').rotate(angle, resample=resample, expand=True),
                      np.float32)


def _unrot(a, angle, h, w, resample=Image.BICUBIC):
    """inverse of _rot, cropped back to the original (h, w)"""
    if abs(angle) % 360 < 1e-6: return a[:h, :w]
    b = np.asarray(Image.fromarray(np.ascontiguousarray(a, np.float32), 'F').rotate(-angle, resample=resample, expand=True),
                   np.float32)
    y0, x0 = (b.shape[0] - h) // 2, (b.shape[1] - w) // 2
    return b[y0:y0 + h, x0:x0 + w]


def _closed_spline(P, per=8):
    P = np.asarray(P, np.float32)
    n = len(P)
    ext = np.vstack([P[-1:], P, P[:2]])
    out = []
    for i in range(1, n + 1):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out, np.float32)


def _resample(P, step):
    P = np.asarray(P, np.float32)
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(np.ceil(s[-1] / step)) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


class DryBrushBlocks:
    PAINTS = PAINTS

    def __init__(self, W=1600, H=1200, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32)
        self.C[:] = hexc('paper')
        self.print_amt = 0.0
        self._tex = None

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== paper and brush-frame textures
    def paper(self, tone='paper'):
        """cream paper: the colour with a faint fibre mottle (the grain itself is added in printed())"""
        H, W = self.H, self.W
        mot = noise2d(H, W, 220, 3, self.seed + 104) - 0.5
        fib = _blur1(np.random.default_rng(self.seed + 105).normal(0, 1, (H, W)).astype(np.float32), 3.0, 1)
        self.C[:] = hexc(tone) * (1 + 0.012 * mot[..., None] + 0.004 * fib[..., None])
        self._textures()

    def _textures(self):
        if self._tex is not None: return
        N = int(max(1024, np.ceil((np.hypot(self.W, self.H) + 24) / 64) * 64))
        r = np.random.default_rng(self.seed + 900)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        # bristle streaks: long along u, 1-3 px across
        sb = 0.5 * _aniso(N, 40, 1.0, r) + 0.2 * _aniso(N, 14, 0.8, r) + 0.3 * _aniso(N, 90, 3.0, r)
        SB = _equalise(sb)
        # the dry tooth: bristle streaks + chunkier drag streaks + paper grain, so the voids of a dry pass are
        # streaky specks of many widths that cluster, not hairlines
        g = z(_blur1(_blur1(r.random((N, N)).astype(np.float32), 0.8, 0, 'wrap'), 0.8, 1, 'wrap'))
        TD = _equalise(0.34 * z(sb) + 0.36 * _aniso(N, 44, 4.5, r) + 0.22 * _aniso(N, 130, 13, r) + 0.2 * g)
        # roller / sponge tooth: isotropic speckle in clusters, a hint of drag
        RT = _equalise(0.42 * g + 0.3 * _aniso(N, 3.5, 3.0, r) + 0.18 * _aniso(N, 14, 5, r) + 0.22 * _aniso(N, 40, 30, r))
        # edge noise for the combed ends: tines 2-10 px wide, of many lengths
        EN = _equalise(0.4 * _aniso(N, 70, 2.6, r) + 0.4 * _aniso(N, 160, 9, r) + 0.2 * z(sb)) * 2 - 1
        # broad lanes (value of the passes) and a stretched mottle (where a dry pass skips)
        SL = _equalise(0.6 * _aniso(N, 320, 10, r) + 0.4 * _aniso(N, 90, 3.5, r))
        MO = _equalise(0.55 * _aniso(N, 300, 80, r) + 0.3 * _aniso(N, 100, 28, r) + 0.15 * _aniso(N, 34, 9, r))
        LO = _equalise(0.7 * _aniso(N, 220, 60, r) + 0.3 * _aniso(N, 60, 14, r))
        self._tex = dict(N=N, SB=SB, TD=TD, RT=RT, EN=EN, SL=SL, MO=MO, LO=LO)

    def _tile(self, h, w, r):
        """random window of the brush-frame textures, (h, w) <= N"""
        self._textures()
        T = self._tex
        N = T['N']
        if h > N or w > N:
            reps = (int(np.ceil(h / N)), int(np.ceil(w / N)))
            return {k: np.tile(v, reps)[:h, :w] for k, v in T.items() if k != 'N'}
        y0, x0 = int(r.integers(0, N - h + 1)), int(r.integers(0, N - w + 1))
        return {k: v[y0:y0 + h, x0:x0 + w] for k, v in T.items() if k != 'N'}

    # ================================================================== shapes (canvas-size masks)
    def _grid(self, sl):
        ys = np.arange(sl[0].start, sl[0].stop, dtype=np.float32)[:, None]
        xs = np.arange(sl[1].start, sl[1].stop, dtype=np.float32)[None, :]
        return xs, ys

    def _clip_box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _bbox(self, m, pad=0, thr=0.004):
        rows = np.flatnonzero(m.max(1) > thr)
        if not len(rows): return None
        cols = np.flatnonzero(m.max(0) > thr)
        pad = int(np.ceil(pad))
        return (slice(max(0, rows[0] - pad), min(self.H, rows[-1] + 1 + pad)),
                slice(max(0, cols[0] - pad), min(self.W, cols[-1] + 1 + pad)))

    def poly(self, pts, smooth=False, per=8):
        pts = np.asarray(pts, np.float32)
        if smooth and len(pts) > 2: pts = _closed_spline(pts, per)
        return polygon_mask(self.H, self.W, pts, ss=2)

    def quad(self, pts):
        return self.poly(pts, smooth=False)

    def rect(self, x0, y0, x1, y1, rot=0.0):
        """axis-aligned box, or rotated by `rot` deg about its centre"""
        if not rot:
            return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
        P = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], np.float32) - (cx, cy)
        return self.poly(np.stack([cx + P[:, 0] * c - P[:, 1] * s, cy + P[:, 0] * s + P[:, 1] * c], 1))

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        ry = rx if ry is None else ry
        R = max(rx, ry) + 3
        out = np.zeros((self.H, self.W), np.float32)
        sl = self._clip_box(cx - R, cy - R, cx + R + 1, cy + R + 1)
        if sl is None: return out
        X, Y = self._grid(sl)
        X, Y = X - cx, Y - cy
        if rot:
            a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
            X, Y = X * c + Y * s, -X * s + Y * c
        d = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2)
        e = 1.0 / max(2.0, min(rx, ry))
        out[sl] = smoothstep(1 + e, 1 - e, d)
        return out

    @staticmethod
    def tube_pts(path, w0, w1=None, per=8):
        """outline polygon of a thick path (width w0 -> w1), squarish ends"""
        P = np.asarray(path, np.float32)
        Q = spline(P, per) if len(P) > 2 else _resample(P, 4.0)
        w1 = w0 if w1 is None else w1
        d = np.gradient(Q, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        hw = np.linspace(w0, w1, len(Q))[:, None] / 2
        return np.vstack([Q + nrm * hw, (Q - nrm * hw)[::-1]]).astype(np.float32)

    def tube(self, path, w0, w1=None):
        return self.poly(self.tube_pts(path, w0, w1))

    def _mask(self, shape):
        if isinstance(shape, np.ndarray) and shape.shape == (self.H, self.W): return shape.astype(np.float32)
        a = np.asarray(shape, np.float32)
        if a.ndim == 1 and len(a) == 4: return self.rect(*a)
        return self.poly(a)

    # ================================================================== laying paint
    def _lay(self, sl, cov, col, mode='opaque'):
        C = self.C[sl]
        a = np.clip(cov, 0, 1)[..., None]
        if mode == 'multiply':
            self.C[sl] = C * (1 - a + a * col)
        elif mode == 'screen':
            self.C[sl] = 1 - (1 - C) * (1 - a * col)
        else:
            self.C[sl] = C + (col - C) * a

    def _brush(self, M, sl, angle, load, dry, lane, fringe, side, tines, scumble, streak, vary, direction, passes,
               seam, mix_amt, edge, stagger, dry_from, stroke_len, tooth, r):
        """the dry-brush coverage, value and mix fields of a block, computed in its brush frame"""
        crop = M[sl]
        h0, w0 = crop.shape
        R = _rot(crop, angle)
        h, w = R.shape
        T = self._tile(h, w, r)
        inside = R > 0.5
        rows_in = inside.any(1)
        if not rows_in.any(): return None
        first = np.where(rows_in, inside.argmax(1), 0)
        last = np.where(rows_in, w - 1 - inside[:, ::-1].argmax(1), 0)
        ext_u = float(np.median((last - first)[rows_in]))
        ext_v = float(rows_in.sum())
        fr = float(min(fringe, 0.3 * ext_u))
        sd = float(min(side, 0.2 * ext_v))
        lane = float(min(lane, max(6.0, ext_v)))
        # ---- shape: nearly straight sides, combed ends
        Mi = blur(R, max(0.5, sd * 0.6)) if sd > 0.3 else R
        Mb = _blur1(Mi, max(0.4, fr * 0.5), 1) if fr > 0.6 else Mi
        U = np.arange(w, dtype=np.float32)[None, :]
        Vv = np.arange(h, dtype=np.float32)[:, None]
        patch = smoothstep(0.58, 0.95, T['MO'])
        # dry stretches along the outline (a side where the brush only grazed the paper)
        if edge:
            ew = max(3.0, min(lane * 0.35, ext_v * 0.15, ext_u * 0.15))
            inner = blur(R, ew)
            stretch = smoothstep(0.55, 0.8, T['LO'])
            gv, gu = np.gradient(inner)                          # sides run along u, ends across it
            side_w = np.abs(gv) / (np.abs(gu) + np.abs(gv) + 1e-6)
            side_w = 0.25 + 0.75 * smoothstep(0.35, 0.8, blur(side_w, ew))
            edge_drop = edge * stretch * side_w * (1 - smoothstep(0.5, 0.97, inner))
        else:
            edge_drop = 0.0

        cov_total = np.zeros((h, w), np.float32)
        val = np.zeros((h, w), np.float32)
        t_dry = np.zeros((h, w), np.float32)
        shift = np.zeros((h, w), np.float32)
        for p in range(max(1, passes)):
            key = 'RT' if tooth == 'roller' else 'TD'
            TDp = T[key] if p == 0 else self._tile(h, w, r)[key]       # each pass drags its own bristle pattern
            # lanes across v, with wobbly borders
            lw = lane * r.uniform(0.9, 1.1)
            bounds = [float(r.uniform(-lw, 0))]
            while bounds[-1] < h + lw:
                bounds.append(bounds[-1] + lw * r.uniform(0.6, 1.4))
            B = np.array(bounds, np.float32)
            nl = len(B) - 1
            wob = (fbm1d(w, max(40.0, lane * 2.5), 3, int(r.integers(1 << 30))) * lane * 0.12)[None, :]
            vq = Vv + wob
            lid = np.clip(np.searchsorted(B, vq) - 1, 0, nl - 1)
            frac = (vq - B[lid]) / (B[lid + 1] - B[lid])
            # lane extents along u from the rows it covers
            row_lane = np.clip(np.searchsorted(B, np.arange(h, dtype=np.float32)) - 1, 0, nl - 1)
            u0 = np.full(nl, np.inf, np.float32); u1 = np.full(nl, -np.inf, np.float32)
            np.minimum.at(u0, row_lane[rows_in], first[rows_in].astype(np.float32))
            np.maximum.at(u1, row_lane[rows_in], last[rows_in].astype(np.float32))
            bad = ~np.isfinite(u0)
            u0[bad], u1[bad] = 0, w
            if direction == 2:
                sgn = np.where(np.arange(nl) % 2 == 0, 1.0, -1.0) * (1 if r.random() < 0.5 else -1)
            elif direction in (1, -1):
                sgn = np.full(nl, float(direction))
            else:
                sgn = r.choice([-1.0, 1.0], nl)
            # each lane is one pass, or (stroke_len) a row of overlapping strokes of different lengths
            if stroke_len:
                K = int(np.ceil((w + 2 * stroke_len) / (stroke_len * 0.6))) + 2
                st = np.full((nl, K), np.inf, np.float32)
                for i in range(nl):
                    a_, c = float(u0[i]) - stroke_len * r.uniform(0.0, 0.6), []
                    while a_ < u1[i] and len(c) < K:
                        c.append(a_); a_ += stroke_len * r.uniform(0.55, 1.45)
                    c.append(max(a_, float(u1[i]) + 1)); c = c[:K]
                    st[i, :len(c)] = c
                j = np.clip((U[..., None] >= st[lid]).sum(-1) - 1, 0, K - 2)
                s0 = np.take_along_axis(st[lid], j[..., None], -1)[..., 0]
                s1 = np.take_along_axis(st[lid], (j + 1)[..., None], -1)[..., 0]
                s1 = np.where(np.isfinite(s1), s1, s0 + stroke_len)
                ov = stroke_len * 0.12                                   # strokes overlap a little
                t = (U - s0 + ov) / np.maximum(s1 - s0 + 2 * ov, 6.0)
                sid = lid * K + j
                nsid = nl * K
            else:
                L = np.maximum(u1 - u0, 8.0)
                t = (U - u0[lid]) / L[lid]
                sid, nsid = lid, nl
            sgn_s = np.repeat(sgn, nsid // nl) if stroke_len else sgn
            if stroke_len and direction == 0:
                sgn_s = r.choice([-1.0, 1.0], nsid)
            t = np.where(sgn_s[sid] > 0, t, 1 - t)
            # each pass / stroke runs dry toward its end by its own amount (some hardly at all)
            dl = (dry * r.uniform(0.0, 1.6, nsid) ** 1.2).astype(np.float32)
            ld = (load * r.uniform(0.985, 1.01, nsid)).astype(np.float32)
            dstart = r.uniform(*dry_from, nsid).astype(np.float32)
            lane_load = ld[sid] * (1 - dl[sid] * smoothstep(dstart[sid], 1.08, t) ** 1.1)
            if seam:
                lane_load = lane_load * (1 - seam * smoothstep(0.84, 1.0, np.abs(frac - 0.5) * 2))
            contact = np.clip(lane_load * (1 - scumble * patch) * (1 - edge_drop), 0, 1.08)
            paint = smoothstep(-0.04, 0.04, TDp - (1 - contact))
            cov_total = 1 - (1 - cov_total) * (1 - paint)
            off = r.normal(0, 1, nsid).astype(np.float32)
            val = val + off[sid] / max(1, passes)
            # the comb only matters where a pass ends at the outline, so t_dry follows the lane, not the stroke
            tl = (U - u0[lid]) / np.maximum(u1 - u0, 8.0)[lid]
            tl = np.where(sgn[lid] > 0, tl, 1 - tl)
            t_dry = np.maximum(t_dry, smoothstep(0.5, 1.0, tl) * (0.6 + 0.4 * (dry > 0)))
            shift = shift + (r.normal(0, 1, nl).astype(np.float32))[lid] / max(1, passes)
        amp = tines * (0.3 + 0.7 * t_dry)
        reach = smoothstep(0.03, 0.3, Mb)                       # tines only grow out of the fringe, never far beyond
        en = T['EN'] if tooth != 'roller' else (T['RT'] - 0.5) * 2 * 0.6 + (T['LO'] - 0.5) * 2 * 0.4
        shape = smoothstep(0.47, 0.53, Mb + reach * (amp * en * 0.42 + stagger * 0.16 * shift))
        cov = shape * cov_total
        if tooth == 'roller':
            V = 1 + vary * val + streak * 0.05 * (T['LO'] - 0.5) * 2 + streak * 0.03 * (T['RT'] - 0.5) * 2
        else:
            V = 1 + vary * val + streak * 0.10 * (T['SL'] - 0.5) * 2 + streak * 0.045 * (T['SB'] - 0.5) * 2
        Mx = None
        if mix_amt:
            q = 0.65 * T['SL'] + 0.35 * T['MO']
            Mx = smoothstep(1 - mix_amt - 0.05, 1 - mix_amt + 0.05, q)
        cov = np.clip(_unrot(cov, angle, h0, w0), 0, 1)
        V = _unrot(V, angle, h0, w0, Image.BILINEAR)
        if Mx is not None: Mx = np.clip(_unrot(Mx, angle, h0, w0, Image.BILINEAR), 0, 1)
        return cov, V, Mx

    def slab(self, shape, colour, angle=0.0, load=0.99, dry=0.45, lane=90.0, fringe=30.0, side=3.0, tines=0.8,
             scumble=0.25, streak=0.6, vary=0.025, direction=0, passes=1, seam=0.03, edge=0.35, stagger=1.0,
             dry_from=(0.5, 0.8), stroke_len=None, tooth='brush', mix=None, mode='opaque', alpha=1.0, avoid=None,
             halo=0.0, clip=None, seed=None):
        """a dry-brushed block of colour. shape: canvas mask | (x0, y0, x1, y1) | polygon points.
        angle: stroke direction (deg); load: contact of a loaded brush (0.97 leaves fine specks, 0.7 is scratchy,
        above 1 is an overloaded brush that stays solid even where it starts to run dry);
        dry: how much the passes run out toward their ends (each by its own amount); lane: brush / roller width (px);
        dry_from: where along a pass (0..1) it starts to run dry; stroke_len: break every pass into overlapping
        strokes of about this length (px), each with its own tone and dry end (None: one stroke per pass); tooth:
        'brush' (bristle streaks along the stroke) or 'roller' (a roller / sponge: clustered speckle); edge: dry stretches along the outline; stagger: how
        much the ends of neighbouring passes differ; fringe: length of the
        combed ends (px); side: wobble of the sides along the stroke (px); tines: strength of the comb; scumble:
        scratchy patches inside; streak: value streaks along the stroke; vary: value difference between passes;
        direction: +1 / -1 / 0 random / 2 back and forth; passes: 2 closes up the body; seam: faint pass seams;
        mix: (colour2, amount) streaks of a second colour in the same brush; mode: 'opaque' | 'multiply' | 'screen'.
        Returns the coverage (canvas-size)."""
        r = self._r(seed)
        self._textures()
        M = self._mask(shape)
        sl = self._bbox(M, fringe * 1.6 + side * 3 + 6)
        out = np.zeros((self.H, self.W), np.float32)
        if sl is None: return out
        res = self._brush(M, sl, angle, load, dry, lane, fringe, side, tines, scumble, streak, vary, direction,
                          passes, seam, (mix[1] if mix else 0.0), edge, stagger, dry_from, stroke_len, tooth, r)
        if res is None: return out
        cov, V, Mx = res
        cov = cov * alpha
        if avoid is not None:
            av = avoid[sl]
            if halo: av = smoothstep(0.1, 0.5, blur(av, halo))
            cov = cov * (1 - av)
        if clip is not None: cov = cov * clip[sl]
        c1 = hexc(colour)
        col = c1[None, None, :] * np.ones_like(cov)[..., None]
        if Mx is not None:
            col = col + (hexc(mix[0]) - c1)[None, None, :] * Mx[..., None]
        col = np.clip(col * V[..., None], 0, 1)
        self._lay(sl, cov, col, mode)
        out[sl] = cov
        return out

    def backdrop(self, box, colour='slab', angle=-90.0, rough=(6, 14), scratches=40, seed=None, **kw):
        """the big colour slab behind the subject, laid with a roller: nearly flat colour with clustered speckle,
        a crisp loaded start, stippled dry stretches along the sides and a few fine scratches.
        box = (x0, y0, x1, y1); angle: direction of the passes (-90 = upward, so the top is where it starts)"""
        r = self._r(seed)
        x0, y0, x1, y1 = box
        a, b = rough
        P = np.array([(x0 + r.normal(0, a * 0.3), y0 + r.normal(0, a * 0.3)), (x1 + r.normal(0, a * 0.3), y0 + r.normal(0, a * 0.3)),
                      (x1 + r.normal(0, a * 0.3), y1 + r.normal(0, a * 0.3)), (x0 + r.normal(0, a * 0.3), y1 + r.normal(0, a * 0.3))])
        kw.setdefault('load', 1.0); kw.setdefault('dry', 0.35); kw.setdefault('lane', 160)
        kw.setdefault('fringe', b); kw.setdefault('side', a * 0.5); kw.setdefault('scumble', 0.12)
        kw.setdefault('streak', 0.6); kw.setdefault('vary', 0.012); kw.setdefault('passes', 2)
        kw.setdefault('dry_from', (0.8, 0.97)); kw.setdefault('tines', 0.35); kw.setdefault('edge', 0.6)
        kw.setdefault('tooth', 'roller'); kw.setdefault('direction', -1); kw.setdefault('seam', 0.0)
        cov = self.slab(self.poly(P), colour, angle, seed=int(r.integers(1 << 30)), **kw)
        if scratches:
            self.scratches(cov, colour, n=scratches, seed=int(r.integers(1 << 30)))
        return cov

    def scratches(self, mask, colour, n=40, length=(20, 120), width=(0.8, 1.8), angle=None, lift=0.22, seed=None):
        """fine scratches scraped into dry paint: thin lines a little paler than the paint (lift toward the
        paper), at loose random angles (or around `angle`), only inside the mask"""
        r = self._r(seed)
        yy, xx = np.nonzero(mask > 0.8)
        if not len(yy): return
        base = hexc(colour)
        col = base + (hexc('paper') - base) * lift
        for i in r.integers(0, len(yy), n):
            x, y = xx[i] + r.random(), yy[i] + r.random()
            a = np.deg2rad(r.uniform(0, 180) if angle is None else angle + r.normal(0, 12))
            L = r.uniform(*length) / 2
            p = [(x - np.cos(a) * L, y - np.sin(a) * L), (x + np.cos(a) * L * 0.1 + r.normal(0, 1), y + np.sin(a) * L * 0.1),
                 (x + np.cos(a) * L, y + np.sin(a) * L)]
            self.stroke(p, r.uniform(*width), col, load=0.85, dry=0.6, taper=(0.2, 0.4), wobble=0.3, rough=0.3,
                        clip=mask, seed=int(r.integers(1 << 30)))

    def piece(self, shape, colour, torn=7.0, cut=0.5, rim=0.0, rim_colour='paper', angle=0.0, load=0.985, dry=0.12,
              lane=70.0, scumble=0.1, streak=0.45, mode='opaque', alpha=1.0, avoid=None, clip=None, seed=None, **kw):
        """a torn / cut paper piece: torn = amplitude of the tear (px); cut = fraction of the outline left as a
        clean cut; rim = width of a pale fibrous rim on the torn stretches (px). Inside it is painted paper."""
        r = self._r(seed)
        M = self._mask(shape)
        sl = self._bbox(M, torn * 3 + 6)
        if sl is None: return np.zeros((self.H, self.W), np.float32)
        m = M[sl]
        h, w = m.shape
        if torn > 0:
            mb = blur(m, max(1.0, torn * 0.55))
            nz = (0.55 * (noise2d(h, w, max(6.0, torn * 3.5), 3, int(r.integers(1 << 30))) - 0.5)
                  + 0.45 * (noise2d(h, w, max(2.0, torn * 0.9), 2, int(r.integers(1 << 30))) - 0.5)) * 2
            stretch = smoothstep(cut - 0.08, cut + 0.08, noise2d(h, w, max(40.0, np.sqrt(h * w) * 0.35), 2,
                                                                   int(r.integers(1 << 30))))
            mt = smoothstep(0.46, 0.54, mb + 0.42 * nz * stretch + (m - mb) * (1 - stretch))
        else:
            mt, stretch = m, np.zeros_like(m)
        Mt = np.zeros((self.H, self.W), np.float32); Mt[sl] = mt
        if rim > 0 and torn > 0:
            band = smoothstep(0.08, 0.5, blur(mt, rim * 0.5)) * (1 - smoothstep(0.5, 0.92, blur(mt, rim * 0.5)))
            band = band * stretch * smoothstep(0.35, 0.65, noise2d(h, w, 18, 2, int(r.integers(1 << 30))))
            self._lay(sl, band * 0.85 * alpha, hexc(rim_colour)[None, None, :], 'opaque')
        kw.setdefault('fringe', 0.0); kw.setdefault('side', 0.8); kw.setdefault('tines', 0.3)
        return self.slab(Mt, colour, angle, load=load, dry=dry, lane=lane, scumble=scumble, streak=streak, mode=mode,
                         alpha=alpha, avoid=avoid, clip=clip, seed=int(r.integers(1 << 30)), **kw)

    def accent(self, x, y, size=56.0, colour='vermilion', rot=0.0, h=None, seed=None):
        """the small solid accent square (x, y = top-left corner), a clean cut edge and a faint print grain"""
        h = size if h is None else h
        r = self._r(seed)
        return self.slab(self.rect(x, y, x + size, y + h, rot), colour, angle=rot + r.choice([0.0, 90.0]), load=1.03,
                         dry=0.05, lane=size * 2, fringe=0, side=0.6, tines=0.15, scumble=0.04, streak=0.12,
                         vary=0.0, seam=0.0, edge=0.05, seed=int(r.integers(1 << 30)))

    # ================================================================== a dry stroke along a path
    def _footprint(self, Q, reach):
        """pixels within `reach` of polyline Q with the index of the segment they belong to: round joins first,
        then one float quad per segment, perpendicular to it, on top (Pillow fills ids into an int image)"""
        x0 = max(0, int(np.floor(Q[:, 0].min() - reach - 2))); x1 = min(self.W, int(np.ceil(Q[:, 0].max() + reach + 3)))
        y0 = max(0, int(np.floor(Q[:, 1].min() - reach - 2))); y1 = min(self.H, int(np.ceil(Q[:, 1].max() + reach + 3)))
        if x1 <= x0 or y1 <= y0: return None
        im = Image.new('I', (x1 - x0, y1 - y0), 0)
        d = ImageDraw.Draw(im)
        q = Q - [x0 - 0.5, y0 - 0.5]
        n = len(q)
        rr = reach + 0.5
        for k in range(n):
            j = min(k, n - 2) + 1
            d.ellipse([q[k][0] - rr, q[k][1] - rr, q[k][0] + rr, q[k][1] + rr], fill=int(j))
        seg = q[1:] - q[:-1]
        L = np.hypot(seg[:, 0], seg[:, 1]) + 1e-6
        t = seg / L[:, None]
        nr = np.stack([-t[:, 1], t[:, 0]], 1) * rr
        e = t * 0.6
        A, B = q[:-1] - e, q[1:] + e
        quads = np.stack([A + nr, B + nr, B - nr, A - nr], 1)
        for k in range(n - 1):
            d.polygon([tuple(p) for p in quads[k].tolist()], fill=k + 1)
        a = np.asarray(im, np.int32)
        yy, xx = np.nonzero(a)
        if not len(yy): return None
        return yy + y0, xx + x0, a[yy, xx] - 1

    def stroke(self, path, width, colour, load=0.95, dry=0.45, taper=(0.06, 0.25), wobble=1.0, smooth=True,
               streak=0.5, rough=1.0, square=0.6, mode='opaque', alpha=1.0, clip=None, seed=None):
        """one dry brush mark along a path: streaks along the curve, a flat brush (square = how blunt the ends
        are), tapering and running dry along its length"""
        r = self._r(seed)
        self._textures()
        P = np.asarray(path, np.float32).reshape(-1, 2)
        if len(P) < 2: return
        if smooth and len(P) > 2: P = spline(P, 8)
        Q = _resample(P, 2.0)
        n = len(Q)
        if wobble and n > 3:
            d = np.gradient(Q, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
            nrm = np.stack([-d[:, 1], d[:, 0]], 1)
            Q = Q + nrm * (fbm1d(n, 40, 3, int(r.integers(1 << 30))) * 1.2 * wobble)[:, None]
        seg = Q[1:] - Q[:-1]
        sL = np.hypot(seg[:, 0], seg[:, 1]) + 1e-6
        cum = np.concatenate([[0], np.cumsum(sL)])
        L = float(cum[-1])
        if L < 1.0: return
        reach = width * 0.5 + 2 + rough
        fp = self._footprint(Q, reach)
        if fp is None: return
        ys, xs, k = fp
        k = np.clip(k, 0, len(seg) - 1)
        dx, dy = seg[k, 0] / sL[k], seg[k, 1] / sL[k]
        rx, ry = xs - Q[k, 0], ys - Q[k, 1]
        p = rx * dx + ry * dy
        u = np.clip(p, 0, sL[k])
        over = np.where(k == 0, np.maximum(0, -p), 0) + np.where(k == len(seg) - 1, np.maximum(0, p - sL[k]), 0)
        px, py = rx - p * dx, ry - p * dy                       # offset across the stroke (no round caps)
        dist = np.hypot(px, py)
        side = np.sign(-rx * dy + ry * dx)
        s = cum[k] + np.where(over > 0, p, u)                    # texture runs on past the ends
        s01 = np.clip((cum[k] + u) / L, 0, 1)
        prof = np.clip(np.minimum(s01 / max(taper[0], 1e-3), (1 - s01) / max(taper[1], 1e-3)), 0, 1)
        prof = square + (1 - square) * prof ** 0.7
        hw = 0.5 * width * prof
        T = self._tex
        N = T['N']
        oy, ox = int(r.integers(0, N)), int(r.integers(0, N))
        iv = (np.round(side * dist).astype(np.int64) + oy) % N
        iu = (np.round(s).astype(np.int64) + ox) % N
        Td, Sb, Sl = T['TD'][iv, iu], T['SB'][iv, iu], T['SL'][iv, iu]
        e = dist - hw - rough * 1.3 * (Sb - 0.5) * 2
        body = smoothstep(0.7, -0.7, e) * smoothstep(0.7, -0.7, over * 1.6 - (0.5 + 2.2 * rough) * (T['EN'][iv, iu] + 0.4))
        contact = load * (1 - dry * smoothstep(0.15, 1.0, s01) ** 1.2) * (1 - 0.25 * smoothstep(0.6, 1.0, dist / (hw + 1e-3)))
        dep = body * smoothstep(-0.05, 0.05, Td - (1 - contact)) * alpha
        if clip is not None: dep = dep * clip[ys, xs]
        keep = dep > 0.003
        if not keep.any(): return
        ys, xs, dep = ys[keep], xs[keep], dep[keep]
        col = hexc(colour)[None, :] * (1 + streak * 0.12 * (Sl[keep] - 0.5) * 2)[:, None]
        idx = (ys, xs)
        C = self.C[idx]
        a = dep[:, None]
        if mode == 'multiply': self.C[idx] = C * (1 - a + a * col)
        else: self.C[idx] = C + (np.clip(col, 0, 1) - C) * a

    def scumble(self, mask, colour, n=40, length=(30, 90), width=(8, 20), angle=0.0, spread=25.0, load=0.8,
                dry=0.55, bend=0.15, alpha=1.0, clip=None, seed=None):
        """short dry strokes scattered in a mask (white beard, hair, steam, highlights); angle may be a number or
        a function f(x, y) -> deg"""
        r = self._r(seed)
        yy, xx = np.nonzero(mask > 0.5)
        if not len(yy): return
        for i in r.integers(0, len(yy), n):
            x, y = xx[i] + r.random(), yy[i] + r.random()
            a0 = angle(x, y) if callable(angle) else angle
            a = np.deg2rad(a0 + r.normal(0, spread * 0.5))
            Lh = r.uniform(*length) / 2
            d = np.array([np.cos(a), np.sin(a)]); nr = np.array([-d[1], d[0]])
            b = r.uniform(-bend, bend) * Lh
            pts = [(x - d[0] * Lh, y - d[1] * Lh), (x + nr[0] * b, y + nr[1] * b), (x + d[0] * Lh, y + d[1] * Lh)]
            self.stroke(pts, r.uniform(*width), colour, load * r.uniform(0.9, 1.05), dry * r.uniform(0.7, 1.3),
                        (0.05, 0.4), 0.6, alpha=alpha, clip=clip if clip is not None else None,
                        seed=int(r.integers(1 << 30)))

    # ================================================================== figures (a person from a few big planes)
    @staticmethod
    def _frame(cx, cy, w, h, tilt=0.0):
        """local unit frame of a part: (-1..1, -1..1) -> canvas, rotated by tilt (deg)"""
        a = np.deg2rad(tilt); c, s = np.cos(a), np.sin(a)

        def P(pts):
            q = np.asarray(pts, np.float32).reshape(-1, 2) * (w / 2, h / 2)
            return np.stack([cx + q[:, 0] * c - q[:, 1] * s, cy + q[:, 0] * s + q[:, 1] * c], 1)
        return P

    def head(self, cx, cy, w, h, tilt=0.0, turn=0.0, light=-1, skin='tan', lit='skin_light', shade='umber',
             warm='tomato', ear='terracotta', highlight='cream', crown=None, hair=None, hair_shade='bone', seed=None):
        """a head from planes: base skin, a shadow plane on the side away from the light (light=-1: light from the
        viewer's left), a pale lit plane, a warm cheek, a warm ear on the shadow side, a nose plane with a warm tip
        and a shadow under it, a few dry highlights. turn (-1..1) moves the features toward one side; crown: colour
        of a bald, lit crown; hair: colour of short cropped hair (a flat-top scumbled over the top and down the
        temples, hair_shade on the shadow side). Returns a dict of anchor points and masks for
        glasses(), beard() and the like."""
        r = self._r(seed)
        P = self._frame(cx, cy, w, h, tilt)
        ls = float(light)
        out = [(-0.80, -0.78), (-0.35, -0.98), (0.1, -1.0), (0.55, -0.92), (0.86, -0.62), (0.96, -0.18), (0.92, 0.28),
               (0.74, 0.66), (0.42, 0.92), (0.02, 1.0), (-0.42, 0.92), (-0.74, 0.66), (-0.92, 0.28), (-0.96, -0.2)]
        face = self.poly(P(out), smooth=True)
        ang = tilt - 90
        self.slab(face, skin, ang, load=0.99, dry=0.25, lane=w * 0.3, fringe=6, side=2.5, scumble=0.15, edge=0.25,
                  mix=(lit, 0.18), seed=int(r.integers(1 << 30)))
        # shadow plane on the side away from the light: a jagged inner boundary down the cheek
        sx = -ls
        tb = 0.34 * sx + turn * 0.3
        sh = [(tb + 0.12 * sx, -0.95), (1.1 * sx, -0.95), (1.1 * sx, 0.95), (0.25 * sx + turn * 0.2, 1.05),
              (tb + 0.02 * sx, 0.55), (tb + 0.14 * sx, 0.25), (tb - 0.02 * sx, -0.05), (tb + 0.1 * sx, -0.4)]
        shadow = self.poly(P(sh)) * face
        self.slab(shadow, shade, tilt - 90 + 8 * sx, load=0.97, dry=0.45, lane=w * 0.16, fringe=10, side=3,
                  scumble=0.3, edge=0.5, mix=(skin, 0.15), seed=int(r.integers(1 << 30)))
        # brow shadow band across the eyes
        bw = [(-0.9, -0.3), (0.9, -0.3), (0.9, -0.06), (-0.9, -0.02)]
        self.slab(self.poly(P(bw)) * face, shade, tilt + 0, load=0.9, dry=0.5, lane=h * 0.08, fringe=14, side=2,
                  scumble=0.4, alpha=0.75, seed=int(r.integers(1 << 30)))
        # lit plane: forehead and cheek on the light side
        lp = [(-0.15 * sx + turn * 0.3, -0.9), (-0.85 * sx, -0.7), (-0.9 * sx, 0.15), (-0.55 * sx, 0.45),
              (-0.2 * sx + turn * 0.3, 0.2), (-0.12 * sx + turn * 0.3, -0.35)]
        lit_m = self.poly(P(lp), smooth=True) * face
        self.slab(lit_m, lit, tilt - 90 - 10 * sx, load=0.86, dry=0.55, lane=w * 0.14, fringe=12, side=3,
                  scumble=0.45, edge=0.6, seed=int(r.integers(1 << 30)))
        # warm cheek on the light side, warm ear on the shadow side
        ck = [(-0.66 * sx, 0.14), (-0.42 * sx + turn * 0.2, 0.1), (-0.36 * sx + turn * 0.2, 0.3), (-0.5 * sx, 0.42),
              (-0.68 * sx, 0.36)]
        self.slab(self.poly(P(ck), smooth=True) * face, warm, tilt - 70, load=0.86, dry=0.55, lane=w * 0.06, fringe=10,
                  side=5, scumble=0.45, edge=0.6, alpha=0.8, seed=int(r.integers(1 << 30)))
        ex = 0.97 * sx
        er = [(ex - 0.06 * sx, -0.22), (ex + 0.16 * sx, -0.28), (ex + 0.2 * sx, 0.1), (ex + 0.08 * sx, 0.32),
              (ex - 0.06 * sx, 0.26)]
        ear_m = self.poly(P(er), smooth=True)
        if ear:
            self.slab(ear_m, ear, tilt - 90, load=0.97, dry=0.35, lane=w * 0.1, fringe=6, side=2, scumble=0.2,
                      mix=(warm, 0.3), seed=int(r.integers(1 << 30)))
            self.slab(self.poly(P([(ex + 0.02 * sx, -0.12), (ex + 0.12 * sx, -0.1), (ex + 0.1 * sx, 0.16),
                                   (ex + 0.0 * sx, 0.12)])), shade, tilt - 90, load=0.9, dry=0.4, lane=8, fringe=4,
                      side=1.5, alpha=0.8, seed=int(r.integers(1 << 30)))
        # nose: a darker shadow side than the cheek plane, a lit bridge, a small warm tip, the shadow under it
        nx = turn * 0.32
        ns = [(nx + 0.0 * sx, -0.22), (nx + 0.1 * sx, -0.2), (nx + 0.2 * sx, 0.12), (nx + 0.22 * sx, 0.36),
              (nx + 0.02 * sx, 0.4), (nx + 0.02 * sx, 0.1)]
        self.slab(self.poly(P(ns), smooth=True), 'brown', tilt - 90, load=0.98, dry=0.35, lane=w * 0.06, fringe=6,
                  side=2, scumble=0.2, mix=(shade, 0.3), seed=int(r.integers(1 << 30)))
        self.stroke([P([(nx - 0.03 * sx, -0.16)])[0], P([(nx - 0.05 * sx, 0.1)])[0], P([(nx - 0.08 * sx, 0.3)])[0]],
                    w * 0.06, lit, load=0.9, dry=0.45, taper=(0.15, 0.3), seed=int(r.integers(1 << 30)))
        tip = self.ellipse(*P([(nx + 0.04 * sx, 0.34)])[0], w * 0.075, h * 0.045, rot=tilt)
        self.slab(tip, warm, tilt, load=0.92, dry=0.35, lane=10, fringe=5, side=2, alpha=0.9,
                  seed=int(r.integers(1 << 30)))
        self.slab(self.poly(P([(nx - 0.1 * sx, 0.4), (nx + 0.24 * sx, 0.38), (nx + 0.18 * sx, 0.46), (nx - 0.06 * sx, 0.47)])),
                  'brown', tilt, load=0.92, dry=0.4, lane=8, fringe=6, side=1.5, alpha=0.9, seed=int(r.integers(1 << 30)))
        if crown:
            cr = [(-0.7, -0.75), (-0.2, -0.97), (0.35, -0.95), (0.72, -0.72), (0.4, -0.55), (-0.3, -0.58)]
            self.slab(self.poly(P(cr), smooth=True) * face, crown, tilt - 10 * sx, load=0.84, dry=0.6, lane=w * 0.12,
                      fringe=20, side=4, scumble=0.5, edge=0.6, seed=int(r.integers(1 << 30)))
        if hair:
            hp = [(-1.0, -0.2), (-0.98, -0.7), (-0.82, -0.96), (-0.3, -1.06), (0.3, -1.06), (0.82, -0.96), (0.98, -0.7),
                  (1.0, -0.2), (0.9, -0.22), (0.86, -0.55), (0.5, -0.66), (0.0, -0.7), (-0.5, -0.66), (-0.86, -0.55),
                  (-0.9, -0.22)]
            hm_ = self.poly(P(hp), smooth=True)
            self.slab(hm_, hair, tilt - 90 - 12 * sx, load=0.92, dry=0.5, lane=w * 0.06, fringe=h * 0.06, side=5,
                      tines=1.0, scumble=0.4, edge=0.6, stroke_len=h * 0.16, passes=2, direction=1,
                      seed=int(r.integers(1 << 30)))
            hs = hm_ * self.poly(P([(0.3 * sx, -1.3), (1.3 * sx, -1.3), (1.3 * sx, 0.0), (0.45 * sx, 0.0)]))
            self.slab(hs, hair_shade, tilt - 80 * sx, load=0.86, dry=0.6, lane=w * 0.06, fringe=w * 0.05, side=4,
                      scumble=0.5, alpha=0.9, seed=int(r.integers(1 << 30)))
            self.scumble(hm_, hair, n=10, length=(0.08 * w, 0.2 * w), width=(0.02 * w, 0.04 * w), angle=tilt - 90,
                         spread=40, load=0.8, dry=0.6, seed=int(r.integers(1 << 30)))
        if highlight:
            hm = self.poly(P([(-0.7 * sx, -0.62), (-0.35 * sx, -0.75), (-0.3 * sx, -0.45), (-0.62 * sx, -0.38)]))
            self.scumble(hm * face, highlight, n=5, length=(0.12 * w, 0.3 * w), width=(0.03 * w, 0.06 * w),
                         angle=tilt - 80 * sx, spread=20, load=0.8, dry=0.6, seed=int(r.integers(1 << 30)))
            hc = self.poly(P([(-0.75 * sx, 0.0), (-0.55 * sx, -0.05), (-0.5 * sx, 0.12), (-0.72 * sx, 0.16)]))
            self.scumble(hc * face, highlight, n=3, length=(0.08 * w, 0.18 * w), width=(0.025 * w, 0.045 * w),
                         angle=tilt - 75 * sx, spread=15, load=0.75, dry=0.6, seed=int(r.integers(1 << 30)))
        return dict(P=P, face=face, shadow=shadow, ear=ear_m, nose=P([(nx, 0.3)])[0], eyes=P([(-0.42 + turn * 0.25, -0.12),
                    (0.42 + turn * 0.25, -0.12)]), mouth=P([(nx, 0.6)])[0], chin=P([(0.0, 1.0)])[0], w=w, h=h,
                    tilt=tilt, turn=turn, light=ls)

    def glasses(self, H, colour='ink', lens=(0.36, 0.2), frame=0.07, brow=1.6, tint='umber', glint='cream', seed=None):
        """rough black glasses on a head() dict: thick dry-brushed frames (a heavier top bar), a bridge, the arm
        running to the ear, a faint tint in the lenses and one dry glint"""
        r = self._r(seed)
        P, w, tilt = H['P'], H['w'], H['tilt']
        fw = frame * w
        (lx, ly), (rx_, ry_) = H['eyes']
        lens_px = (lens[0] * w, lens[1] * H['h'])
        for k, (ex, ey) in enumerate(((lx, ly), (rx_, ry_))):
            far = (k == 1) == (H['light'] < 0)
            sc = 0.86 if far else 1.0
            lw, lh = lens_px[0] * sc, lens_px[1]
            Q = self._frame(ex, ey, lw, lh, tilt)
            box = Q([(-1, -1), (1, -1), (1, 0.75), (0.6, 1), (-0.6, 1), (-1, 0.75)])
            inner = self.poly(Q([(-0.78, -0.62), (0.78, -0.62), (0.8, 0.5), (0.5, 0.74), (-0.5, 0.74), (-0.8, 0.5)]), smooth=True)
            if tint:
                self.slab(inner, tint, tilt - 90, load=0.8, dry=0.5, lane=12, fringe=4, side=2, scumble=0.5, alpha=0.22,
                          mode='multiply', seed=int(r.integers(1 << 30)))
            outer = self.poly(box, smooth=True)
            ring = np.clip(outer - self.poly(Q([(-0.8, -0.52), (0.8, -0.52), (0.82, 0.52), (0.52, 0.78), (-0.52, 0.78),
                                                  (-0.82, 0.52)]), smooth=True), 0, 1)
            topbar = self.poly(Q([(-1.08, -1.12), (1.08, -1.12), (1.04, -1 + 0.5 * brow * fw / max(lh, 1)), (-1.04, -1 + 0.5 * brow * fw / max(lh, 1))]))
            self.slab(np.maximum(ring, topbar), colour, tilt + r.uniform(-8, 8), load=0.985, dry=0.4, lane=fw * 1.2,
                      fringe=6, side=1.2, tines=0.5, scumble=0.2, seed=int(r.integers(1 << 30)))
            if glint and not far:
                self.stroke([Q([(-0.5, -0.25)])[0], Q([(-0.05, -0.38)])[0]], fw * 0.8, glint, load=0.8, dry=0.6,
                            seed=int(r.integers(1 << 30)))
        # bridge and the arm toward the ear
        self.stroke([(lx + lens_px[0] * 0.45, ly - lens_px[1] * 0.35), ((lx + rx_) / 2, (ly + ry_) / 2 - lens_px[1] * 0.5),
                     (rx_ - lens_px[0] * 0.4, ry_ - lens_px[1] * 0.35)], fw * 0.9, colour, load=0.97, dry=0.3,
                    seed=int(r.integers(1 << 30)))
        ex, ey = (rx_, ry_) if H['light'] < 0 else (lx, ly)
        sgn = 1 if H['light'] < 0 else -1
        a0 = (ex + sgn * lens_px[0] * 0.48, ey - lens_px[1] * 0.4)
        a1 = P([(0.98 * -H['light'], -0.18)])[0]
        self.stroke([a0, a1], fw * 0.85, colour, load=0.95, dry=0.45, seed=int(r.integers(1 << 30)))

    def beard(self, H, colour='white', shade='bone', length=0.42, width=0.95, moustache=True, density=1.0, seed=None):
        """a white beard and moustache as dry scumble over a head() dict: a ragged pale block brushed downward,
        dry strokes that fan out past its edge, a grey shadow side and a moustache under the nose"""
        r = self._r(seed)
        P, w, h, tilt, sx = H['P'], H['w'], H['h'], H['tilt'], -H['light']
        nx = H['turn'] * 0.32
        bd = [(-0.9 * width, 0.25), (-0.5 * width + nx, 0.5), (nx, 0.56), (0.5 * width + nx, 0.5), (0.9 * width, 0.25),
              (0.82 * width, 0.7), (0.45 * width, 1.0 + length * 0.7), (0.0 + nx * 0.5, 1.0 + length),
              (-0.45 * width, 1.0 + length * 0.7), (-0.82 * width, 0.7)]
        bm = self.poly(P(bd), smooth=True)
        self.slab(bm, colour, tilt + 90, load=0.9, dry=0.6, lane=w * 0.1, fringe=w * 0.14, side=6, tines=1.0,
                  scumble=0.45, edge=0.6, direction=1, dry_from=(0.3, 0.6), seed=int(r.integers(1 << 30)))
        shm = bm * self.poly(P([(0.35 * sx + nx, 0.3), (1.2 * sx, 0.3), (1.2 * sx, 1.6), (0.2 * sx, 1.6)]))
        self.slab(shm, shade, tilt + 90, load=0.85, dry=0.6, lane=w * 0.08, fringe=w * 0.1, side=4, scumble=0.5,
                  alpha=0.85, direction=1, seed=int(r.integers(1 << 30)))
        def fan(x, y):
            dx = (x - P([(nx, 0.5)])[0][0]) / (w * 0.5)
            return tilt + 90 - 28 * np.clip(dx, -1, 1)
        self.scumble(bm, colour, n=int(26 * density), length=(0.1 * w, 0.32 * w), width=(0.025 * w, 0.06 * w),
                     angle=fan, spread=14, load=0.85, dry=0.55, bend=0.12, seed=int(r.integers(1 << 30)))
        self.scumble(shm, shade, n=int(8 * density), length=(0.08 * w, 0.22 * w), width=(0.02 * w, 0.04 * w),
                     angle=fan, spread=14, load=0.8, dry=0.6, seed=int(r.integers(1 << 30)))
        if moustache:
            for k in (-1, 1):
                p0 = P([(nx + 0.04 * k, 0.48)])[0]; p1 = P([(nx + 0.42 * k, 0.6)])[0]; pm = P([(nx + 0.24 * k, 0.5)])[0]
                self.stroke([p0, pm, p1], w * 0.12, colour, load=0.92, dry=0.55, taper=(0.05, 0.5), seed=int(r.integers(1 << 30)))
        return bm

    def jacket(self, neck, shoulders, bottom, lit='tealblue', shade='navy', dark='ink', shirt='cream', collar=None,
               light=-1, lapel=0.32, open_=0.16, seed=None):
        """a jacket from planes: neck = (x, y) of the throat, shoulders = (xl, yl, xr, yr), bottom = y of the
        lowest edge. The lit half is brushed one way, the shadow half (near-black with streaks of the jacket colour)
        another; a shirt V, two lapel blocks, an optional stand collar. Returns the jacket mask."""
        r = self._r(seed)
        nxp, nyp = neck
        xl, yl, xr, yr = shoulders
        Wd = xr - xl
        body = [(xl + Wd * 0.08, yl - Wd * 0.02), (nxp - Wd * 0.12, nyp - Wd * 0.03), (nxp + Wd * 0.12, nyp - Wd * 0.03),
                (xr - Wd * 0.08, yr - Wd * 0.02), (xr + Wd * 0.03, yr + Wd * 0.12), (xr + Wd * 0.06, bottom),
                (xl - Wd * 0.06, bottom), (xl - Wd * 0.03, yl + Wd * 0.12)]
        J = self.poly(body, smooth=False)
        ls = float(light)
        midx = nxp + Wd * 0.02 * -ls
        lit_side = [(midx, nyp - 40), (xl - 60 if ls < 0 else xr + 60, nyp - 40), (xl - 60 if ls < 0 else xr + 60, bottom + 5),
                    (midx, bottom + 5)]
        Ml = J * self.poly(lit_side)
        Ms = J * (1 - self.poly(lit_side))
        self.slab(Ms, dark, -90 + 22 * -ls, load=1.02, dry=0.35, lane=Wd * 0.08, fringe=22, side=5, scumble=0.12,
                  edge=0.35, mix=(shade, 0.07), passes=2, stroke_len=Wd * 0.34, seed=int(r.integers(1 << 30)))
        self.slab(Ml, lit, -90 - 25 * -ls, load=0.993, dry=0.4, lane=Wd * 0.07, fringe=34, side=5, scumble=0.2,
                  edge=0.45, mix=(shade, 0.14), passes=2, stroke_len=Wd * 0.26, seed=int(r.integers(1 << 30)))
        # streaks of the jacket colour dragged over the dark half
        for _ in range(3):
            x0 = midx - ls * r.uniform(0.1, 0.42) * Wd                  # on the dark half, whichever side it is
            y0 = r.uniform(nyp + 0.1 * Wd, bottom - 0.1 * Wd)
            a = np.deg2rad(r.uniform(-120, -60))
            Lh = r.uniform(0.08, 0.2) * Wd
            self.stroke([(x0 - np.cos(a) * Lh, y0 - np.sin(a) * Lh), (x0 + np.cos(a) * Lh, y0 + np.sin(a) * Lh)],
                        r.uniform(0.03, 0.06) * Wd, shade, load=0.8, dry=0.7, clip=Ms, seed=int(r.integers(1 << 30)))
        # shirt V and lapels
        vh = lapel * Wd * 0.9
        sv = [(nxp - open_ * Wd, nyp - 6), (nxp + open_ * Wd, nyp - 6), (nxp + 0.01 * Wd, nyp + vh)]
        self.slab(self.poly(sv), shirt, -90, load=0.97, dry=0.4, lane=open_ * Wd, fringe=10, side=3, scumble=0.3,
                  seed=int(r.integers(1 << 30)))
        for k in (-1, 1):
            lp = [(nxp + k * open_ * Wd, nyp - 8), (nxp + k * (open_ + 0.12) * Wd, nyp + 0.02 * Wd),
                  (nxp + k * 0.05 * Wd, nyp + vh * 1.08), (nxp + k * 0.01 * Wd, nyp + vh * 0.98)]
            col = shade if (k < 0) == (ls < 0) else dark
            self.slab(self.poly(lp), col, -90 + k * 25, load=0.98, dry=0.35, lane=0.05 * Wd, fringe=10, side=2.5,
                      scumble=0.2, mix=(lit, 0.15), seed=int(r.integers(1 << 30)))
        if collar:
            cl = [(nxp - (open_ + 0.06) * Wd, nyp - 0.07 * Wd), (nxp + (open_ + 0.06) * Wd, nyp - 0.07 * Wd),
                  (nxp + (open_ + 0.04) * Wd, nyp + 0.01 * Wd), (nxp - (open_ + 0.04) * Wd, nyp + 0.01 * Wd)]
            self.slab(self.poly(cl), collar, 0, load=0.98, dry=0.4, lane=0.04 * Wd, fringe=8, side=2,
                      seed=int(r.integers(1 << 30)))
        return J

    def sleeve(self, path, w0, w1=None, colour='navy', angle=None, mix=None, seed=None, **kw):
        """an arm / sleeve: a tapering band brushed along its own direction"""
        P = np.asarray(path, np.float32)
        a = np.degrees(np.arctan2(P[-1, 1] - P[0, 1], P[-1, 0] - P[0, 0])) if angle is None else angle
        kw.setdefault('load', 0.98); kw.setdefault('dry', 0.5); kw.setdefault('lane', max(10.0, w0 * 0.35))
        kw.setdefault('fringe', 14); kw.setdefault('side', 4); kw.setdefault('scumble', 0.25)
        kw.setdefault('tines', 0.6)
        return self.slab(self.tube(P, w0, w1), colour, a, mix=mix, seed=seed, **kw)

    def hand(self, x, y, size, angle=0.0, skin='tan', lit='skin_light', shade='umber', grip=True, cuff=None,
             seed=None):
        """a hand seen from the thumb side in a few planes: the lit back of the hand, four stacked finger bands of
        alternating tone (the lowest in shadow) with a dark line between them, a thumb along the top, a dry
        highlight on the knuckles and an optional cuff at the wrist. (x, y) is the centre, angle the direction the
        fingers point (deg); grip=True curls the fingers into a fist (chopsticks), False lays them out longer
        (holding a bowl). Returns the hand mask."""
        r = self._r(seed)
        P = self._frame(x, y, size, size * 0.85, angle)
        reach = 0.92 if grip else 1.35
        back = [(-1.0, -0.4), (-0.2, -0.56), (0.45, -0.56), (0.45, 0.62), (-0.2, 0.55), (-0.95, 0.38)]
        Mb = self.poly(P(back), smooth=True)
        self.slab(Mb, lit, angle, load=0.985, dry=0.4, lane=size * 0.14, fringe=8, side=3, scumble=0.3, edge=0.35,
                  mix=(skin, 0.3), seed=int(r.integers(1 << 30)))
        M = Mb
        bands = ((-0.44, -0.14), (-0.14, 0.16), (0.16, 0.46), (0.46, 0.76))
        cols = (skin, lit, skin, shade)
        for i, (v0, v1) in enumerate(bands):
            x1 = reach - 0.06 * i * (1 if grip else -1)
            f = [(0.28, v0 + 0.02), (x1 - 0.12, v0), (x1, v0 + 0.06), (x1 + 0.04, (v0 + v1) / 2), (x1, v1 - 0.04),
                 (x1 - 0.12, v1), (0.28, v1 - 0.02)]
            Mf = self.poly(P(f), smooth=True)
            self.slab(Mf, cols[i], angle, load=0.98, dry=0.4, lane=size * 0.08, fringe=6, side=2, scumble=0.3,
                      mix=(shade, 0.25) if i == 2 else None, seed=int(r.integers(1 << 30)))
            if i:
                self.stroke([P([(0.34, v0)])[0], P([(x1 - 0.08, v0 + 0.01)])[0]], size * 0.04, 'brown', load=0.85,
                            dry=0.45, taper=(0.1, 0.35), seed=int(r.integers(1 << 30)))
            M = np.maximum(M, Mf)
        # thumb along the top, a crease, a dry knuckle highlight
        th = [(-0.6, -0.46), (0.1, -0.7), (0.6, -0.72), (0.74, -0.58), (0.3, -0.44), (-0.4, -0.3)]
        Mt = self.poly(P(th), smooth=True)
        self.slab(Mt, lit, angle - 8, load=0.96, dry=0.4, lane=size * 0.08, fringe=6, side=2, mix=(skin, 0.3),
                  seed=int(r.integers(1 << 30)))
        self.stroke([P([(-0.2, -0.44)])[0], P([(0.55, -0.56)])[0]], size * 0.035, shade, load=0.8, dry=0.5,
                    seed=int(r.integers(1 << 30)))
        self.stroke([P([(0.3, -0.3)])[0], P([(0.36, 0.4)])[0]], size * 0.07, 'cream', load=0.7, dry=0.65,
                    seed=int(r.integers(1 << 30)))
        M = np.maximum(M, Mt)
        if cuff:
            cf = [(-1.14, -0.46), (-0.88, -0.5), (-0.86, 0.5), (-1.12, 0.46)]
            self.slab(self.poly(P(cf)), cuff, angle + 90, load=0.97, dry=0.4, lane=size * 0.1, fringe=6,
                      side=2, scumble=0.3, seed=int(r.integers(1 << 30)))
        return M

    # ================================================================== vessels
    def bottle(self, x, base, w, h, colour='forest', shoulder=0.42, neck=0.3, neck_w=0.34, lip=0.05,
               dark='ink', light='sage', label=None, label2=None, cap=None, glass=False, angle=-90.0, seed=None):
        """a bottle silhouette standing on y = base: body, curved shoulder, neck and lip, brushed vertically, with a
        dark side, one light streak, an optional label block ((colour, y0, y1) as fractions of the height from the
        base), a second small block on the label and a cap colour. glass=True paints it as pale glass (multiply)."""
        r = self._r(seed)
        hw, nw = w / 2, w * neck_w / 2
        ys = base - h * (1 - shoulder - neck - lip)          # top of the straight body
        yn = base - h * (1 - neck - lip)                     # bottom of the neck
        yt = base - h
        pts = [(x - hw, base), (x - hw, ys)]
        for t in np.linspace(0, 1, 9)[1:]:
            pts.append((x - hw + (hw - nw) * (1 - np.cos(t * np.pi / 2)) ** 1.0 * 1.0 - 0 * t,
                        ys + (yn - ys) * np.sin(t * np.pi / 2)))
        pts += [(x - nw, yt + h * lip), (x - nw * 1.15, yt + h * lip * 0.9), (x - nw * 1.15, yt), (x + nw * 1.15, yt),
                (x + nw * 1.15, yt + h * lip * 0.9), (x + nw, yt + h * lip)]
        for t in np.linspace(0, 1, 9)[::-1][1:]:
            pts.append((x + hw - (hw - nw) * (1 - np.cos(t * np.pi / 2)), ys + (yn - ys) * np.sin(t * np.pi / 2)))
        pts += [(x + hw, ys), (x + hw, base)]
        B = self.poly(pts)
        mode = 'multiply' if glass else 'opaque'
        self.slab(B, colour, angle, load=0.985, dry=0.4, lane=w * 0.22, fringe=10, side=2.5, tines=0.6, scumble=0.25,
                  edge=0.3, mix=(dark, 0.12) if (dark and not glass) else None, mode=mode, direction=1,
                  seed=int(r.integers(1 << 30)))
        if not glass and dark:
            ds = B * self.poly([(x + hw * 0.35, yt - 5), (x + hw + 20, yt - 5), (x + hw + 20, base + 5), (x + hw * 0.3, base + 5)])
            self.slab(ds, dark, angle, load=0.95, dry=0.5, lane=w * 0.12, fringe=12, side=2, scumble=0.3, alpha=0.9,
                      direction=1, seed=int(r.integers(1 << 30)))
        if light:
            lx = x - hw * 0.45
            self.stroke([(lx, base - h * 0.08), (lx + 1, ys + h * 0.02), (x - nw * 0.4, yn + h * 0.04)],
                        max(4.0, w * 0.09), light, load=0.9, dry=0.55, taper=(0.1, 0.3), seed=int(r.integers(1 << 30)))
        if cap:
            self.slab(self.rect(x - nw * 1.2, yt - 2, x + nw * 1.2, yt + h * (lip + 0.04)), cap, 0, load=0.98, dry=0.3,
                      lane=8, fringe=4, side=1.5, seed=int(r.integers(1 << 30)))
        if label:
            col, f0, f1 = label
            y0, y1 = base - h * f1, base - h * f0
            self.slab(self.rect(x - hw * 0.98, y0, x + hw * 0.98, y1), col, 0, load=0.985, dry=0.3, lane=(y1 - y0) * 0.5,
                      fringe=8, side=1.5, scumble=0.2, seed=int(r.integers(1 << 30)))
            if label2:
                col2, fx0, fx1, fy0, fy1 = label2
                self.slab(self.rect(x - hw + w * fx0, y0 + (y1 - y0) * fy0, x - hw + w * fx1, y0 + (y1 - y0) * fy1), col2,
                          90, load=0.99, dry=0.2, lane=w, fringe=0, side=0.8, scumble=0.1, seed=int(r.integers(1 << 30)))
        return B

    def bowl(self, cx, rim_y, w, h, colour='white', band='teal', inside='bone', shade='bone', foot=0.42, seed=None):
        """a bowl seen a little from above: the rim ellipse with what is inside, a body that curves in to a foot,
        a band of colour under the rim and a shadow side. Returns (body mask, inside mask)."""
        r = self._r(seed)
        ry = h * 0.16
        top = self.ellipse(cx, rim_y, w / 2, ry)
        body = [(cx - w / 2, rim_y)]
        n = 16
        for k in range(n + 1):
            s = k / n
            xs = (w / 2) * (1 - (1 - foot) * s ** 1.6)
            body.append((cx - xs, rim_y + h * s * 0.92))
        body += [(cx - w * foot / 2, rim_y + h), (cx + w * foot / 2, rim_y + h)]
        for k in range(n, -1, -1):
            s = k / n
            xs = (w / 2) * (1 - (1 - foot) * s ** 1.6)
            body.append((cx + xs, rim_y + h * s * 0.92))
        Bm = self.poly(body)
        self.slab(Bm, colour, -6, load=1.05, dry=0.12, lane=h * 0.22, fringe=4, side=2, scumble=0.06, edge=0.08,
                  tines=0.4, seed=int(r.integers(1 << 30)))
        sd = Bm * self.poly([(cx + w * 0.14, rim_y - 5), (cx + w, rim_y - 5), (cx + w, rim_y + h + 5), (cx + w * 0.02, rim_y + h + 5)])
        self.slab(sd, shade, -78, load=1.0, dry=0.45, lane=h * 0.16, fringe=10, side=2, scumble=0.3, edge=0.5,
                  seed=int(r.integers(1 << 30)))
        if band:
            bd = Bm * self.poly([(cx - w, rim_y + h * 0.14), (cx + w, rim_y + h * 0.14), (cx + w, rim_y + h * 0.3),
                                 (cx - w, rim_y + h * 0.3)])
            self.slab(bd, band, 0, load=0.975, dry=0.4, lane=h * 0.16, fringe=6, side=1.5, scumble=0.25,
                      seed=int(r.integers(1 << 30)))
        inner = self.ellipse(cx, rim_y + ry * 0.12, w / 2 * 0.94, ry * 0.8)
        self.slab(top, colour, 0, load=1.04, dry=0.2, lane=ry, fringe=6, side=1.5, seed=int(r.integers(1 << 30)))
        self.slab(inner, inside, 0, load=1.0, dry=0.35, lane=ry * 0.6, fringe=8, side=1.5, scumble=0.25,
                  seed=int(r.integers(1 << 30)))
        return Bm, inner

    def cup(self, cx, base, w, h, colour='celadon', glass=True, level=0.62, tea='khaki', rim='white', seed=None):
        """a tall drinking glass / cup: a tapering block (pale glass is laid as multiply), the tea level, a rim"""
        r = self._r(seed)
        pts = [(cx - w * 0.5, base - h), (cx + w * 0.5, base - h), (cx + w * 0.42, base), (cx - w * 0.42, base)]
        G = self.poly(pts)
        self.slab(G, colour, -90, load=0.97, dry=0.4, lane=w * 0.25, fringe=10, side=2, scumble=0.35, edge=0.4,
                  mode='multiply' if glass else 'opaque', seed=int(r.integers(1 << 30)))
        if tea:
            tl = base - h * level
            T_ = G * self.poly([(cx - w, tl), (cx + w, tl), (cx + w, base + 4), (cx - w, base + 4)])
            self.slab(T_, tea, 0, load=0.95, dry=0.45, lane=w * 0.2, fringe=8, side=2, scumble=0.35, alpha=0.75,
                      mode='multiply', seed=int(r.integers(1 << 30)))
        if rim:
            self.stroke([(cx - w * 0.48, base - h + 3), (cx + w * 0.48, base - h + 3)], max(3.0, w * 0.05), rim, load=0.9,
                        dry=0.5, seed=int(r.integers(1 << 30)))
            self.stroke([(cx - w * 0.3, base - h * 0.85), (cx - w * 0.26, base - h * 0.2)], max(3.0, w * 0.06), rim,
                        load=0.8, dry=0.6, seed=int(r.integers(1 << 30)))
        return G

    # ================================================================== finish
    def printed(self, amount=1.0):
        """reproduce like an offset print of the painting: slight softness, paper grain, sparse knocked-out specks
        in the darks and sparse dust on the paper (applied in render())"""
        self.print_amt = float(amount)

    def render(self):
        out = self.C.copy()
        p = self.print_amt
        if p:
            soft = np.stack([blur(out[..., i], 0.65) for i in range(3)], -1)
            out = out * (1 - 0.35 * p) + soft * 0.35 * p
            if not hasattr(self, '_print'):
                r = np.random.default_rng(self.seed + 7)
                H, W = self.H, self.W
                g = r.normal(0, 1, (H, W)).astype(np.float32)
                g = 0.55 * g + 0.45 * blur(g, 1.0) * 2.2
                fib = _blur1(r.normal(0, 1, (H, W)).astype(np.float32), 4.0, 1) * 1.6
                # knocked-out specks: small clusters, sparse; dust: sparser, smaller
                sp = blur((r.random((H, W)) < 0.0016).astype(np.float32), 0.8)
                sp = smoothstep(0.05, 0.22, sp) * smoothstep(0.35, 0.7, noise2d(H, W, 90, 2, self.seed + 8))
                du = smoothstep(0.08, 0.3, blur((r.random((H, W)) < 0.00025).astype(np.float32), 0.6))
                self._print = (g, fib, sp, du)
            g, fib, sp, du = self._print
            lum = out.mean(-1, keepdims=True)
            dark = smoothstep(0.75, 0.3, lum)
            out = out * (1 + p * (0.016 * g + 0.006 * fib)[..., None])
            out = out + (hexc('paper') - out) * (p * 0.75 * sp[..., None] * dark)
            out = out + (hexc('#3b3a33') - out) * (p * 0.45 * du[..., None] * (1 - dark))
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
