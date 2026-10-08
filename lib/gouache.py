"""gouache — 复古水粉 / Retro Gouache: picture-book character portraits in opaque gouache (numpy + Pillow only).

The look of a mid-century picture book painted in gouache (or matte acrylic used the same way): tight head-and-
shoulders portraits of goofy characters with huge rosy noses, round eyes, blush circles, big ears, bushy brows and
beards, wide necks and small shoulders, in a bold retro palette (vermilion, cobalt, cerulean, teal, mustard, warm
peach) against one scumbled background colour; knit sweaters, strand-y hair and felt hats you can almost touch, and
the grain of the board and of the printed page over everything. Nothing here is a filter on flat shapes: every
coloured pixel was laid by a brush stroke, a painted line or a texture model, in the order a painter works.

Physical model
  ground      Gouache is painted on a board or heavy paper. The board has a tooth: fine bumps (a blurred white noise
              at ~1 px), a softer undulation and a very faint canvas-like weave, kept as one height field `G` in 0..1.
              The tooth decides where a dry brush catches. Before any colour each panel gets a thin warm imprimatura
              (toned ground) scrubbed on with big low-alpha strokes; it glows through wherever later coats break.
  paint       Gouache is opaque and dries matte: a coat REPLACES what is under it (C <- C + (paint - C) * A), it does
              not glaze over it like watercolour. A wet brush picks up a little of the layer below (`pickup`), so
              neighbouring strokes blend at their seams. Each stroke also leaves a little body (`T`), and the final
              picture is lit very gently from the upper left, so stroke ridges and the tooth read as a matte relief,
              not as gloss. Layers go on dark to light and big to small: toned ground, underdrawing in thinned umber,
              background, flat masses, value steps, textures, features, highlights.
  dry brush   One stroke is a flat brush dragged along a short arc. Across it the hairs carry different loads
              (a random bristle profile, so streaks run along the stroke and the colour varies slightly per hair);
              along it the paint runs out (load falls with distance, faster for a drier brush). Where the load is
              high the paint covers everything under the brush; as it falls, paint is deposited only where a loaded
              bristle passes over a high point of the tooth, so the tail of the stroke breaks into streaks and
              specks -- the scumbled, dragged look of a gouache background. The sides of the stroke are ragged
              (the half-width wobbles along it) and the ends are rounded where the brush lands. `dry_brush()` does
              the same along any polyline (long sweeps, steam), `strokes()` scatters many strokes over a region
              with an orientation field (so they follow a form) and a colour field (so they pick their colour from
              where they land).
  edges       A shape's edge is crisp but never vector-clean: the mask is blurred by a pixel and re-thresholded
              against a low-frequency wobble and the tooth (`rough()`), so the edge wanders a little and is
              broken where the brush skipped.
  modelling   Forms are modelled in a few value steps, as a picture-book painter does: the shape is inflated into a
              soft pillow (a blurred mask taken as a height field; `sphere_shade()` uses an exact ellipsoid), lit
              by one light from the upper left, the light quantised into 3-5 soft steps, and each step mapped onto a
              ramp of mixed colours (deep shadow -> shadow -> local colour -> light -> pale light, shadows shifted
              toward violet / red, lights toward warm white). The ramp is laid first as a wet blend (soft) and then
              brushed over with short strokes that run ALONG the form (along the contour lines of the height, or
              around the centre of a sphere), each stroke taking its colour from the step it lands in, so the steps
              meet in brushy, slightly blended seams. Core shadows under a hat brim, a nose, a beard or a chin are
              thin multiply glazes of a shifted copy of the caster (`cast_shadow()`); cheeks are soft, powdery
              blush glazes broken by the tooth (`blush()`).
  knit        A stockinette stitch is a V: two yarn legs leaning in from the top corners of a cell to its bottom
              centre. Each leg is a rotated ellipse with a cylinder profile (a raised yarn), twisted plies cut faint
              diagonal grooves across it, neighbouring rows overlap a little, and the valleys between legs are dark
              (occlusion). The height is lit with the same light, normalised and multiplied onto the paint that is
              already there, so the large-scale value steps of the garment survive and the stitches ride on top.
              Rows can bow (above eye level they arch, below they sag), follow a rotation, or follow a path (a scarf).
              Cables are two tubes twisting round each other in a column, one in front then the other, with a groove
              at each side. Every stitch gets a small hash-based value jitter and the lit tops get dry-brush
              highlights that only catch on the tooth. `rib()` is ribbing: raised knit columns and sunken purl
              columns across a band (collars, cuffs, a hat brim), with tiny chevrons of stitches along each column.
  hair        Hair, brows, beards, curls, pompoms and fur are many fine painted strands over a darker mass. Each
              strand starts inside the mass (or on a root line), follows a flow field (an angle per pixel or a
              function: combed, radiating, curling round centres) with its own small bend and jitter, is drawn as a
              tapered line with a round brush (3x supersampled), and picks its value from a light field over the
              mass (dark strands in the shadow, light ones on the lit side) with some randomness, so the mass keeps
              its volume and still reads as hundreds of hairs; strays run a little past the silhouette.
  felt        Felt is matted fibre: a fine two-scale mottle multiplied onto the paint, short random fibres in a
              lighter and a darker tone, and fibres sticking out across the silhouette so the edge is fuzzy.
  grain       The finished painting is reproduced in a book: `grain()` adds the printed-page feel -- a fine paper
              speckle, a warm paper tone in the lights, ink that never reaches black and a slight softening of the
              most saturated colours -- over the matte relief of tooth and paint body.

API (panel-local coordinates in px; angles in degrees, 0 = to the right, 90 = down; colours are names in PAINTS
or '#rrggbb')
  surface   GouachePortrait(W, H, seed, keep_stages, stages_dir); panel(x0, y0, w, h) -> panel (current), use(p);
            ground(tone, paper, alpha) gutters + toned imprimatura; sketch(mask, colour, width, alpha) underdrawing
  shapes    ellipse(cx, cy, rx, ry, rot), poly(pts, smooth), blob(cx, cy, rx, ry, rough, seed, rot),
            band(path, w0, w1) a thick path; all return panel-size float masks (combine with np.maximum, *, 1 -)
  brush     stroke(x, y, angle, length, width, colour, bend, dry, alpha); dry_brush(path, width, colour, dry, alpha);
            strokes(mask, colour|field, angle|field|callable, length, width, density, dry, alpha, clip);
            rough(mask, amount) a broken painted edge
  painting  scumble_background(colour, bottom, avoid); block_in(mask, colour); form_light(mask, height) -> 0..1;
            model_form(mask, colours, steps, height, angle); sphere_shade(cx, cy, rx, ry, colours, mask);
            dry_highlight(mask, colour, above) broken light strokes on the lit side; glaze(mask, colour, alpha, mode);
            cast_shadow(caster, dx, dy, soft, alpha, on); blush(cx, cy, rx);
            dab(x, y, r, colour); line(path, width, colour, taper); spatter(mask, colour, n, size)
  features  eye(cx, cy, r, iris, look, lid, lid_colour, lashes); nose(cx, cy, rx, ry, colour); ear(cx, cy, rx, ry,
            colour, side)
  textures  knit(mask, stitch, origin, curve, angle, path, cables); rib(mask, path, period);
            hair_strands(mask, flow, colours, n, length, width, shade, curl); felt(mask, strength)
  finish    grain(amount); render(); composite(); stage(name); save(path, stages_dir)
  helpers   hexc(c), mix(a, b, t), ramp(base, ...) -> 5 colours dark -> light, PAINTS, LIGHT

    import sys; sys.path.insert(0, 'lib')
    import numpy as np
    from gouache import GouachePortrait, ramp
    g = GouachePortrait(1920, 1080, seed=5)
    p = g.panel(650, 15, 620, 1050)
    g.ground('#c88f5a')
    face = g.ellipse(310, 540, 190, 210)
    g.scumble_background('green', avoid=face)
    g.block_in(face, 'skin')
    g.model_form(face, ramp('skin', cool='#a02a3a'), steps=4)        # skin shadows go warm, not violet
    g.blush(200, 600, 60); g.blush(420, 600, 60)
    g.nose(310, 580, 80, 70, 'nose')
    g.eye(230, 500, 26, look=(0.2, 0.1)); g.eye(390, 500, 26, look=(0.2, 0.1))
    g.grain(); g.save('portrait.jpg')
"""
import io
import os
from types import SimpleNamespace
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep, spline, polygon_mask, blob_pts
from core import shift as _shift


PAINTS = {
    'vermilion': '#e2512c', 'red': '#d33a2c', 'orange': '#ee7a22', 'mustard': '#e0a52b', 'yellow': '#f0c43c',
    'ochre': '#c98a3a', 'cobalt': '#2c5bb0', 'cerulean': '#4d9bd0', 'navy': '#20325f', 'teal': '#1d877f',
    'seaglass': '#7fbcb6', 'green': '#4d9a5c', 'olive': '#8d9a52', 'peach': '#f2c3a0', 'skin': '#efbb98',
    'ruddy': '#e7a585', 'nose': '#e0563f', 'rose': '#e06d5c', 'blush': '#e9604c', 'pink': '#f0a59a',
    'umber': '#5c3b28', 'sienna': '#b0603a', 'cream': '#f3ead6', 'white': '#f6f1e6', 'grey': '#9a9a98',
    'ink': '#1c1a20', 'brown': '#6b4228', 'cocoa': '#5a3322',
}
PAPER = '#f2ead9'                 # the board / gutters
LIGHT = (-0.44, -0.56, 0.70)      # one light from the upper left and in front


def hexc(c):
    """'#rrggbb', a PAINTS name, or an RGB triple -> float32 RGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    a, b = hexc(a), hexc(b)
    return (a + (b - a) * t).astype(np.float32)


def ramp(base, deep=0.50, shadow=0.74, light=0.26, pale=0.52, cool='#3b2450', warm='#fff2d8'):
    """five mixed colours, dark -> light, for modelling a form painted in `base`: shadows deepen and drift toward
    a violet-red, lights toward warm white (the way gouache is mixed, not a grey scale)"""
    b = hexc(base)
    return [mix(b * deep, cool, 0.20), mix(b * shadow, cool, 0.07), b, mix(b, warm, light), mix(b, warm, pale)]


def _closed_spline(P, per=8):
    P = np.asarray(P, np.float32)
    n = len(P)
    t = np.linspace(0, 1, per, endpoint=False, dtype=np.float32)[:, None]
    t2, t3 = t * t, t * t * t
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.concatenate(out).astype(np.float32)


def _hash(a, b):
    h = np.sin(a * 12.9898 + b * 78.233) * 43758.5453
    return (h - np.floor(h)).astype(np.float32)


def _steps(q, n, soft):
    """soft staircase: q in 0..1 -> n value steps with blended seams (soft 0.5 = no steps)"""
    x = np.clip(q, 0, 1) * n
    k = np.floor(np.minimum(x, n - 1e-4))
    f = x - k
    return np.clip((k + smoothstep(0.5 - soft, 0.5 + soft, f)) / n, 0, 1)


def _ramp_field(q, colours):
    cols = np.stack([hexc(c) for c in colours])
    pos = np.linspace(0, 1, len(cols))
    out = np.empty(q.shape + (3,), np.float32)
    for ch in range(3):
        out[..., ch] = np.interp(q, pos, cols[:, ch])
    return out


class GouachePortrait:
    PAINTS = PAINTS
    LIGHT = LIGHT

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32)
        self.C[:] = hexc(PAPER)
        self.T = np.zeros((H, W), np.float32)                 # paint body left by the strokes
        r = np.random.default_rng(seed + 101)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.7)
        g1 = (g1 - g1.mean()) / (g1.std() + 1e-6)
        g2 = noise2d(H, W, 7, 3, seed + 102)
        g2 = (g2 - g2.mean()) / (g2.std() + 1e-6)
        yy = np.arange(H, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None, :]
        weave = np.sin(xx * 2.07 + 0.6 * np.sin(yy * 0.05)) * np.sin(yy * 1.93)
        self.G = np.clip(0.5 + 0.16 * (0.66 * g1 + 0.30 * g2 + 0.22 * weave), 0, 1).astype(np.float32)
        L = np.asarray(LIGHT, np.float32)
        self.light = L / np.linalg.norm(L)
        self.print_amt = 0.0
        self.panels, self.P = [], None

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== board and panels
    def panel(self, x0, y0, w, h):
        """a picture area on the board; becomes current. Drawing coordinates are local to it."""
        x0, y0, w, h = int(x0), int(y0), int(w), int(h)
        p = SimpleNamespace(x0=x0, y0=y0, w=w, h=h)
        p.YY, p.XX = np.mgrid[0:h, 0:w].astype(np.float32)
        p.C = self.C[y0:y0 + h, x0:x0 + w]          # views: painting a panel paints the board
        p.T = self.T[y0:y0 + h, x0:x0 + w]
        p.G = self.G[y0:y0 + h, x0:x0 + w]
        self.panels.append(p)
        self.P = p
        return p

    def use(self, p):
        self.P = p
        return p

    def ground(self, tone='#c88f5a', paper=PAPER, alpha=0.5):
        """cream board in the gutters, and a thin warm imprimatura scrubbed over every panel with big loose strokes"""
        self.C[:] = hexc(paper) * (0.975 + 0.05 * (self.G[..., None] - 0.5))
        cur = self.P
        for p in self.panels:
            self.use(p)
            full = np.ones((p.h, p.w), np.float32)
            mot = noise2d(p.h, p.w, 140, 3, int(self.rng.integers(1 << 30))) - 0.5
            self._put((slice(None), slice(None)), full * alpha * (0.8 + 0.5 * mot), hexc(tone))
            self.strokes(full, tone, angle=-35, jitter=25, length=(240, 480), width=(60, 120), density=2.6,
                         dry=0.6, alpha=alpha * 0.7, vj=0.06, pickup=0.0, bend=0.15, streak=1.0, load=0.82)
        self.P = cur

    # ================================================================== shapes (panel-size masks)
    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        P = self.P
        ry = rx if ry is None else ry
        X, Y = P.XX - cx, P.YY - cy
        if rot:
            a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
            X, Y = X * c + Y * s, -X * s + Y * c
        d = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2)
        e = 1.0 / max(2.0, min(rx, ry))
        return smoothstep(1 + e, 1 - e, d).astype(np.float32)

    def poly(self, pts, smooth=True, per=8):
        P = self.P
        pts = np.asarray(pts, np.float32)
        if smooth and len(pts) > 2: pts = _closed_spline(pts, per)
        return polygon_mask(P.h, P.w, pts, ss=2)

    def blob(self, cx, cy, rx, ry=None, rough=0.08, seed=0, rot=0.0):
        return self.poly(blob_pts(cx, cy, rx, rx if ry is None else ry, rough, 120, seed, np.deg2rad(rot)), smooth=False)

    @staticmethod
    def tube(path, w0, w1=None, per=8):
        """outline polygon of a thick path (width w0 at the start -> w1 at the end), rounded ends"""
        Q = spline(np.asarray(path, np.float32), per) if len(path) > 2 else np.asarray(path, np.float32)
        w1 = w0 if w1 is None else w1
        d = np.gradient(Q, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        hw = np.linspace(w0, w1, len(Q))[:, None] / 2
        L, R = Q + nrm * hw, Q - nrm * hw
        a0 = np.arctan2(nrm[0, 1], nrm[0, 0]); a1 = np.arctan2(nrm[-1, 1], nrm[-1, 0])
        cap1 = [Q[-1] + hw[-1] * np.array([np.cos(a1 - t), np.sin(a1 - t)]) for t in np.linspace(0, np.pi, 9)[1:-1]]
        cap0 = [Q[0] + hw[0] * np.array([np.cos(a0 + np.pi - t), np.sin(a0 + np.pi - t)]) for t in np.linspace(0, np.pi, 9)[1:-1]]
        return np.vstack([L, np.array(cap1).reshape(-1, 2), R[::-1], np.array(cap0).reshape(-1, 2)]).astype(np.float32)

    def band(self, path, w0, w1=None):
        return self.poly(self.tube(path, w0, w1), smooth=False)

    def _bbox(self, m, pad=0, thr=0.004):
        P = self.P
        rows = np.flatnonzero(m.max(1) > thr)
        if not len(rows): return None
        cols = np.flatnonzero(m.max(0) > thr)
        pad = int(np.ceil(pad))
        return (slice(max(0, rows[0] - pad), min(P.h, rows[-1] + 1 + pad)),
                slice(max(0, cols[0] - pad), min(P.w, cols[-1] + 1 + pad)))

    def _put(self, sl, A, col):
        """opaque paint over what is there: C <- C + (col - C) * A"""
        Cs = self.P.C[sl]
        col = col if np.ndim(col) == 3 else np.asarray(col, np.float32)
        Cs += (col - Cs) * A[..., None]

    def rough(self, mask, amount=1.0, wobble=1.0, seed=None):
        """the painted edge of a shape: crisp, but wandering a little and broken by the tooth"""
        P = self.P
        sl = self._bbox(mask, 4)
        out = np.zeros_like(mask)
        if sl is None: return out
        m = blur(mask[sl], 0.9)
        h, w = m.shape
        lo = noise2d(h, w, 16, 2, int(self._r(seed).integers(1 << 30))) - 0.5
        out[sl] = smoothstep(0.40, 0.60, m + amount * (0.16 * wobble * lo + 0.20 * (P.G[sl] - 0.5)))
        return out

    # ================================================================== the brush
    def _stroke(self, cx, cy, ang, L, w, col, bend=0.0, dry=0.3, alpha=1.0, clip=None, pickup=0.1, streak=0.5,
                soft=0.8, r=None, thick=0.6, vjit=0.09, load0=1.0):
        """one flat-brush stroke centred at (cx, cy), angle in radians, bowing sideways by `bend` x half-length;
        load0 < 1 is a brush that is already nearly dry when it touches down (a scumble)"""
        P = self.P
        r = r if r is not None else self._r()
        ca, sa = np.cos(ang), np.sin(ang)
        hl, hw = max(L, 1.0) / 2, max(w, 1.0) / 2
        ex = abs(ca) * hl + abs(sa) * hw + abs(bend) * hl + 2
        ey = abs(sa) * hl + abs(ca) * hw + abs(bend) * hl + 2
        x0, x1 = max(0, int(cx - ex)), min(P.w, int(cx + ex) + 2)
        y0, y1 = max(0, int(cy - ey)), min(P.h, int(cy + ey) + 2)
        if x1 <= x0 or y1 <= y0: return
        sl = (slice(y0, y1), slice(x0, x1))
        X = P.XX[sl] - cx; Y = P.YY[sl] - cy
        u = X * ca + Y * sa
        v = -X * sa + Y * ca
        un = u / hl
        t = (v - bend * hl * (1 - np.clip(un, -1, 1) ** 2)) / hw
        k = 7
        wob = 1 + 0.11 * np.interp(un, np.linspace(-1.05, 1.05, k), r.normal(0, 1, k))
        c = min(0.45, hw / hl)
        a_ = np.maximum(np.abs(un) - (1 - c), 0) / c
        dist = np.sqrt(a_ * a_ + t * t) / wob
        body = smoothstep(1.0, 0.92 - 0.3 * soft, dist)
        if body.max() <= 0: return
        nb = max(5, int(w / 2.2))
        loads = r.uniform(0.3, 1.0, nb)
        B = np.interp(t, np.linspace(-1, 1, nb), loads)
        s = np.clip((un + 1) * 0.5, 0, 1)
        load = load0 - dry * 1.25 * r.uniform(0.8, 1.2) * s ** 1.4
        edge = smoothstep(0.55, 1.0, np.abs(t))                       # outer hairs run dry first
        paint = load * (1 - 0.45 * streak + 0.45 * streak * B) * (1 - 0.35 * edge * streak) + (P.G[sl] - 0.5) * 0.6
        A = body * smoothstep(0.38, 0.58, paint) * alpha
        if clip is not None: A = A * clip[sl]
        Cs = P.C[sl]
        colv = np.asarray(col, np.float32) * (1 + vjit * streak * (B - 0.65))[..., None]
        if pickup: colv = colv * (1 - pickup) + Cs * pickup
        Cs += (colv - Cs) * A[..., None]
        P.T[sl] += A * thick * np.clip(load, 0, 1)

    def stroke(self, x, y, angle, length, width, colour, bend=0.0, dry=0.3, alpha=1.0, clip=None, pickup=0.1, streak=0.5):
        """one brush stroke (angle in degrees)"""
        self._stroke(x, y, np.deg2rad(angle), length, width, hexc(colour), bend, dry, alpha, clip, pickup, streak)

    def _angles(self, angle, xs, ys, r):
        n = len(xs)
        if angle is None: return r.uniform(0, 360, n)
        if callable(angle): return np.asarray(angle(xs, ys), np.float32) * np.ones(n)
        if np.ndim(angle) == 2:
            P = self.P
            return angle[np.clip(ys.astype(int), 0, P.h - 1), np.clip(xs.astype(int), 0, P.w - 1)]
        return np.full(n, float(angle))

    def strokes(self, mask, colour, angle=None, length=(30, 60), width=(10, 18), density=1.0, dry=0.3, alpha=1.0,
                bend=0.15, jitter=12.0, vj=0.03, clip=None, pickup=0.1, streak=0.5, soft=0.8, n=None, seed=None,
                thick=0.6, vjit=0.09, load=1.0):
        """lay many strokes with centres inside `mask` (> 0.5). colour: one colour or a panel-size colour field
        (each stroke takes the colour where it lands); angle (degrees): None = random, a number, a panel-size
        field, or f(x, y) -> degrees; clip: a mask the paint is confined to (default: none)"""
        P = self.P
        r = self._r(seed)
        sl = self._bbox(mask)
        if sl is None: return
        sub = mask[sl] > 0.5
        idx = np.flatnonzero(sub)
        if not len(idx): return
        if n is None:
            n = int(len(idx) / (np.mean(length) * np.mean(width)) * density) + 1
        pick = r.choice(idx, n)
        ys = (pick // sub.shape[1] + sl[0].start).astype(np.float32) + r.random(n)
        xs = (pick % sub.shape[1] + sl[1].start).astype(np.float32) + r.random(n)
        ang = np.deg2rad(self._angles(angle, xs, ys, r) + r.normal(0, jitter, n))
        if np.ndim(colour) == 3:
            cols = colour[np.clip(ys.astype(int), 0, P.h - 1), np.clip(xs.astype(int), 0, P.w - 1)]
        else:
            cols = np.broadcast_to(hexc(colour), (n, 3))
        cols = np.clip(cols * (1 + r.normal(0, vj, (n, 1))) + r.normal(0, vj * 0.35, (n, 3)), 0, 1)
        Ls = r.uniform(*length, n); Ws = r.uniform(*width, n)
        bends = r.uniform(-bend, bend, n); drys = np.clip(dry * r.uniform(0.6, 1.35, n), 0, 1)
        for i in range(n):
            self._stroke(xs[i], ys[i], ang[i], Ls[i], Ws[i], cols[i], bends[i], drys[i], alpha, clip, pickup,
                         streak, soft, r, thick, vjit, load * r.uniform(0.85, 1.12))

    def _path_st(self, Q, sl):
        """for every pixel in sl: arc length of the nearest point on polyline Q, signed offset, squared distance"""
        P = self.P
        X = P.XX[sl]; Y = P.YY[sl]
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
        return S, Tt, best, float(cum[-1])

    def dry_brush(self, path, width, colour, dry=0.35, alpha=1.0, clip=None, streak=0.6, pickup=0.08,
                  taper=(0.12, 0.3), smooth=True, seed=None):
        """one long stroke along a polyline: bristle streaks, paint running out toward the end, tapered ends"""
        P = self.P
        r = self._r(seed)
        Q = np.asarray(path, np.float32)
        if smooth and len(Q) > 2: Q = spline(Q, 8)
        pad = width / 2 + 3
        x0, x1 = max(0, int(Q[:, 0].min() - pad)), min(P.w, int(Q[:, 0].max() + pad) + 1)
        y0, y1 = max(0, int(Q[:, 1].min() - pad)), min(P.h, int(Q[:, 1].max() + pad) + 1)
        if x1 <= x0 or y1 <= y0: return
        sl = (slice(y0, y1), slice(x0, x1))
        S, Tt, d2, L = self._path_st(Q, sl)
        s = S / max(L, 1e-3)
        prof = 0.25 + 0.75 * np.clip(np.minimum(s / max(taper[0], 1e-3), (1 - s) / max(taper[1], 1e-3)), 0, 1) ** 0.6
        hw = width / 2 * prof
        k = 9
        wob = 1 + 0.10 * np.interp(s, np.linspace(0, 1, k), r.normal(0, 1, k))
        dist = np.sqrt(d2) / (hw * wob + 1e-3)
        body = smoothstep(1.0, 0.7, dist)
        nb = max(5, int(width / 2.2))
        B = np.interp(np.clip(Tt / (hw + 1e-3), -1, 1), np.linspace(-1, 1, nb), r.uniform(0.3, 1.0, nb))
        load = 1.0 - dry * 1.25 * s ** 1.3
        paint = load * (1 - 0.45 * streak + 0.45 * streak * B) + (P.G[sl] - 0.5) * 0.6
        A = body * smoothstep(0.38, 0.58, paint) * alpha
        if clip is not None: A = A * clip[sl]
        Cs = P.C[sl]
        colv = hexc(colour) * (1 + 0.05 * streak * (B - 0.65))[..., None]
        if pickup: colv = colv * (1 - pickup) + Cs * pickup
        Cs += (colv - Cs) * A[..., None]
        P.T[sl] += A * 0.6 * np.clip(load, 0, 1)

    # ================================================================== painting
    def sketch(self, mask, colour='#8a4426', width=2.2, alpha=0.8, breaks=0.3, seed=None):
        """underdrawing: the contour of a shape in thinned paint with a small round brush, broken here and there"""
        P = self.P
        sl = self._bbox(mask, width * 3 + 4)
        if sl is None: return
        m = blur(mask[sl], width * 0.7)
        e = np.exp(-((m - 0.5) / 0.16) ** 2)
        h, w = m.shape
        brk = smoothstep(breaks - 0.15, breaks + 0.1, noise2d(h, w, 40, 2, int(self._r(seed).integers(1 << 30))))
        A = e * brk * alpha * smoothstep(0.25, 0.6, P.G[sl] + 0.2)
        Cs = P.C[sl]
        Cs *= 1 - A[..., None] * (1 - hexc(colour))

    def scumble_background(self, colour, bottom=None, avoid=None, light=0.15, dark=0.12, angle=-30, spread=40,
                           dry=0.8, scratches=120, flecks=900, blend=(0.12, 0.92), seed=None):
        """the backdrop: one colour (or a top -> bottom blend) laid solid with long loaded strokes, then scrubbed
        over with an almost dry brush in lighter and darker mixes of the same colour, so the strokes break into
        streaks on the tooth and earlier coats show through; then short light scratches and a sprinkle of flecks.
        `avoid` (a mask) is painted around, a few px into it."""
        P = self.P
        r = self._r(seed)
        top = hexc(colour); bot = top if bottom is None else hexc(bottom)
        wob = (noise2d(P.h, P.w, 260, 2, int(r.integers(1 << 30))) - 0.5) * 0.25
        t = smoothstep(blend[0], blend[1], P.YY / P.h + wob)[..., None]
        field = top + (bot - top) * t
        mot = noise2d(P.h, P.w, 120, 3, int(r.integers(1 << 30))) - 0.5
        field = np.clip(field * (1 + 0.06 * mot[..., None]), 0, 1)
        if avoid is not None:
            clipm = 1 - smoothstep(0.55, 0.85, blur(avoid, 2.5))
        else:
            clipm = np.ones((P.h, P.w), np.float32)
        where = (clipm > 0.5).astype(np.float32)
        self._put((slice(None), slice(None)), clipm * 0.9, field)
        sd = lambda: int(r.integers(1 << 30))
        self.strokes(where, field, angle=angle, jitter=spread, length=(220, 420), width=(60, 110), density=1.3,
                     dry=0.42, alpha=0.95, vj=0.012, clip=clipm, pickup=0.15, streak=1.0, seed=sd(), vjit=0.07)
        lite = field + (hexc('#fff6e2') - field) * light
        dk = field * (1 - dark) + hexc('#2a2440') * dark * 0.2
        self.strokes(where, lite, angle=angle + 60, jitter=spread, length=(140, 360), width=(22, 60), density=1.1,
                     dry=dry * 0.6, alpha=0.75, vj=0.02, clip=clipm, pickup=0.0, streak=1.0, seed=sd(), vjit=0.1,
                     load=0.74)
        self.strokes(where, dk, angle=angle, jitter=spread, length=(140, 340), width=(22, 56), density=0.6,
                     dry=dry * 0.6, alpha=0.6, vj=0.02, clip=clipm, pickup=0.0, streak=1.0, seed=sd(), vjit=0.1,
                     load=0.72)
        lite2 = field + (hexc('#fffaf0') - field) * (light * 2.4)
        if scratches:
            self.strokes(where, lite2, angle=angle + 25, jitter=spread * 1.2, length=(18, 70), width=(1.5, 3.5),
                         n=scratches, dry=0.7, alpha=0.6, vj=0.03, clip=clipm, pickup=0.0, streak=1.0, seed=sd())
        if flecks:
            self.spatter(where * clipm, lite2, n=flecks // 2, size=(0.5, 1.4), alpha=0.5, seed=sd())
            self.spatter(where * clipm, dk * 0.92, n=flecks // 2, size=(0.5, 1.3), alpha=0.4, seed=sd())

    def block_in(self, mask, colour, angle=None, length=(34, 80), width=(14, 28), density=1.3, dry=0.15, edge=1.0,
                 vj=0.03, alpha=0.97, flat=0.92, seed=None):
        """lay a shape in as a flat opaque mass: a near-solid coat with a broken edge, then brushed over in the same
        colour so the coat has direction and a little value drift. Returns the painted (rough) mask."""
        P = self.P
        r = self._r(seed)
        clip = self.rough(mask, edge, seed=int(r.integers(1 << 30)))
        sl = self._bbox(clip)
        if sl is None: return clip
        h, w = clip[sl].shape
        mot = (noise2d(h, w, 50, 3, int(r.integers(1 << 30))) - 0.5) * 0.05
        col = hexc(colour)
        self._put(sl, clip[sl] * flat, col * (1 + mot[..., None]))
        self.strokes(mask, colour, angle, length, width, density, dry, alpha, clip=clip, vj=vj, pickup=0.1,
                     seed=int(r.integers(1 << 30)))
        return clip

    def form_light(self, mask, height=None, light=None, round_=0.5, ambient=0.0, relief=0.55):
        """light falling on a soft-modelled form, 0 (turned away) .. 1 (facing the light). The mask is inflated
        into a pillow unless `height` (panel-size, px) is given. Also returns the height and its gradient."""
        P = self.P
        Lv = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        sl0 = self._bbox(mask)
        out = np.zeros_like(mask)
        if sl0 is None: return out, None, None
        if height is None:
            m0 = mask[sl0]
            re = float(np.sqrt(m0.sum() / np.pi)) + 1
            sig = max(2.0, re * round_)
            sl = self._bbox(mask, sig * 2.5)
            b = blur(mask[sl], sig)
            bm = float(b.max())
            inside = mask[sl] > 0.5
            b0 = float(np.percentile(b[inside], 0.5)) if inside.any() else 0.5
            hn = np.clip((b - b0) / max(bm - b0, 1e-3), 0, 1) * smoothstep(0.3, 0.6, mask[sl])
            hh = np.sqrt(hn) * re * relief
        else:
            sl = sl0
            hh = height[sl]
        gy, gx = np.gradient(hh)
        nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
        lam = np.clip((-gx * Lv[0] - gy * Lv[1] + Lv[2]) * nz, 0, 1)
        out[sl] = ambient + (1 - ambient) * lam
        H = np.zeros_like(mask); H[sl] = hh
        GX = np.zeros_like(mask); GY = np.zeros_like(mask); GX[sl] = gx; GY[sl] = gy
        return out, H, (GX, GY)

    def _paint_field(self, mask, field, ang, clip, wet, length, width, density, dry, alpha, pickup, streak, vj, r,
                     soft=0.8):
        sl = self._bbox(clip)
        if sl is None: return
        if wet:
            fb = np.stack([blur(field[sl][..., c], 2.0) for c in range(3)], -1)
            self._put(sl, clip[sl] * wet, fb)
        self.strokes(mask, field, ang, length, width, density, dry, alpha, bend=0.25, jitter=9, vj=vj, clip=clip,
                     pickup=pickup, streak=streak, soft=soft, seed=int(r.integers(1 << 30)))

    def model_form(self, mask, colours, steps=4, soft=0.22, height=None, light=None, angle='contour', round_=0.5, relief=0.55,
                   ambient=0.08, wet=0.75, length=(18, 44), width=(7, 15), density=2.2, dry=0.18, alpha=0.8,
                   pickup=0.18, streak=0.45, vj=0.02, clip=None, bias=0.0, gamma=1.0, seed=None):
        """model a form in a few value steps (dark -> light ramp `colours`), wet-blended and then brushed ALONG the
        form. angle: 'contour' (strokes follow the contour lines of the height), 'fall' (down the slope), a number,
        a field or a function. bias / gamma shift the light (bias > 0 lighter). Returns the light field."""
        r = self._r(seed)
        lam, H, grad = self.form_light(mask, height, light, round_, ambient, relief)
        if H is None: return lam
        q = _steps(np.clip(lam ** gamma + bias, 0, 1), steps, soft)
        field = _ramp_field(q, colours)
        if isinstance(angle, str):
            GX, GY = grad
            base = np.degrees(np.arctan2(GY, GX + 1e-6))
            ang = base + 90 if angle == 'contour' else base
        else:
            ang = angle
        clip = self.rough(mask, 0.8, seed=int(r.integers(1 << 30))) if clip is None else clip
        self._paint_field(mask, field, ang, clip, wet, length, width, density, dry, alpha, pickup, streak, vj, r)
        return lam

    def sphere_shade(self, cx, cy, rx, ry=None, colours=None, steps=4, soft=0.3, mask=None, light=None, rot=0.0,
                     reflect=0.18, wet=0.9, length=(10, 26), width=(5, 10), density=3.2, dry=0.1, alpha=0.55,
                     pickup=0.25, streak=0.35, vj=0.008, clip=None, bias=0.0, seed=None):
        """model a round form (an ellipsoid) in value steps, strokes curving round its centre; a little reflected
        light comes back into the lower rim. Returns the light field."""
        P = self.P
        r = self._r(seed)
        ry = rx if ry is None else ry
        Lv = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        X, Y = P.XX - cx, P.YY - cy
        if rot:
            a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
            X, Y = X * c + Y * s, -X * s + Y * c
        nx, ny = X / rx, Y / ry
        r2 = nx * nx + ny * ny
        nz = np.sqrt(np.clip(1 - r2, 0, 1))
        lam = np.clip(nx * Lv[0] + ny * Lv[1] + nz * Lv[2], 0, 1)
        lam = lam + reflect * smoothstep(0.55, 1.0, r2) * np.clip(ny, 0, 1) * (r2 < 1.2)
        lam = np.clip(lam + bias, 0, 1)
        m = self.ellipse(cx, cy, rx, ry, rot) if mask is None else mask
        field = _ramp_field(_steps(lam, steps, soft), colours if colours is not None else ramp('nose'))
        ang = np.degrees(np.arctan2(ny, nx)) + 90 + rot
        clip = self.rough(m, 0.6, seed=int(r.integers(1 << 30))) if clip is None else clip
        self._paint_field(m, field, ang, clip, wet, length, width, density, dry, alpha, pickup, streak, vj, r)
        return lam

    def dry_highlight(self, mask, colour, above=0.62, height=None, angle='contour', length=(24, 60), width=(6, 14),
                      density=0.6, alpha=0.7, load=0.7, dry=0.6, relief=0.55, seed=None):
        """the last touches on the lit side of a form: a nearly dry brush of a lighter mix dragged along the form,
        only where the light is strong, so it catches on the tooth and leaves broken streaks"""
        lam, H, grad = self.form_light(mask, height, relief=relief)
        if H is None: return
        where = mask * (lam > above)
        if isinstance(angle, str):
            ang = np.degrees(np.arctan2(grad[1], grad[0] + 1e-6)) + (90 if angle == 'contour' else 0)
        else:
            ang = angle
        clip = self.rough(mask, 0.5)
        self.strokes(where, colour, ang, length, width, density, dry, alpha, bend=0.2, jitter=10, vj=0.02,
                     clip=clip, pickup=0.0, streak=1.0, seed=seed, load=load)

    def glaze(self, mask, colour, alpha=0.5, mode='multiply', soft=0.0):
        """a thin layer over what is there: 'multiply' (shadows), 'screen' (lights) or 'normal'"""
        m = blur(mask, soft) if soft else mask
        sl = self._bbox(m)
        if sl is None: return
        A = m[sl] * alpha
        Cs = self.P.C[sl]
        col = hexc(colour)
        if mode == 'multiply': tgt = Cs * col
        elif mode == 'screen': tgt = 1 - (1 - Cs) * (1 - col)
        else: tgt = np.broadcast_to(col, Cs.shape)
        Cs += (tgt - Cs) * A[..., None]

    def cast_shadow(self, caster, dx, dy, soft=8.0, alpha=0.4, colour='#7a4a52', on=None):
        """soft core / cast shadow of `caster` shifted by (dx, dy), only on `on` (default: anywhere), not on itself"""
        sh = blur(_shift(caster, dx, dy), soft) * (1 - caster)
        if on is not None: sh = sh * on
        self.glaze(sh, colour, alpha, 'multiply')

    def blush(self, cx, cy, rx, ry=None, colour='blush', strength=0.55, grain=0.6, mask=None, solid=0.45):
        """a round cheek of thinned colour: solid-ish in the middle, powdery toward the rim where only the tooth takes it"""
        P = self.P
        ry = rx if ry is None else ry
        d = np.sqrt(((P.XX - cx) / rx) ** 2 + ((P.YY - cy) / ry) ** 2)
        a = smoothstep(1.0, solid, d)
        sl = self._bbox(a)
        if sl is None: return
        a = a[sl]
        a = a * (1 - grain * 0.75 * (1 - smoothstep(0.25, 0.75, P.G[sl] + a * 0.45)))
        A = a * strength
        if mask is not None: A = A * mask[sl]
        self._put(sl, A, hexc(colour))

    def dab(self, x, y, r, colour='white', alpha=0.95, angle=-30, dry=0.15, clip=None):
        """a small round touch of paint (highlights, catchlights, buttons)"""
        self._stroke(x, y, np.deg2rad(angle), r * 2.2, r * 2.0, hexc(colour), 0.0, dry, alpha, clip, 0.0, 0.3, 0.6)

    # ------------------------------------------------------------------ painted lines (round brush)
    def _strands_mask(self, paths, widths, taper=(0.15, 0.5), fills=None, ss=3):
        """anti-aliased coverage of many tapered polylines (panel coords) -> (slice, crop)"""
        P = self.P
        allp = np.concatenate(paths)
        pad = float(np.max(widths)) + 3
        x0, x1 = max(0, int(allp[:, 0].min() - pad)), min(P.w, int(allp[:, 0].max() + pad) + 1)
        y0, y1 = max(0, int(allp[:, 1].min() - pad)), min(P.h, int(allp[:, 1].max() + pad) + 1)
        if x1 <= x0 or y1 <= y0: return None, None
        bw, bh = x1 - x0, y1 - y0
        ss = max(1, min(ss, 4096 // max(bw, bh)))                     # never draw larger than 4096 px a side
        im = Image.new('L', (bw * ss, bh * ss), 0)
        d = ImageDraw.Draw(im)
        o = np.array([x0, y0], np.float32)
        for i, Q in enumerate(paths):
            q = (np.asarray(Q, np.float32) - o) * ss
            n = len(q)
            f = 255 if fills is None else int(fills[i])
            if n < 2:
                rr = widths[i] * ss / 2
                d.ellipse([q[0, 0] - rr, q[0, 1] - rr, q[0, 0] + rr, q[0, 1] + rr], fill=f); continue
            tt = np.linspace(0, 1, n)
            prof = 0.2 + 0.8 * np.clip(np.minimum(tt / max(taper[0], 1e-3), (1 - tt) / max(taper[1], 1e-3)), 0, 1)
            ww = np.maximum(1, np.round(widths[i] * ss * prof)).astype(int)
            ql = [tuple(p) for p in q.tolist()]
            a = 0
            while a < n - 1:
                b = a + 1
                while b < n - 1 and ww[b] == ww[a]: b += 1
                d.line(ql[a:b + 1], fill=f, width=int(ww[a]), joint='curve' if ww[a] > 2 else None)
                a = b
            if widths[i] * ss > 4:
                for k in (0, n - 1):
                    rr = ww[k] / 2
                    d.ellipse([q[k, 0] - rr, q[k, 1] - rr, q[k, 0] + rr, q[k, 1] + rr], fill=f)
        cov = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        return (slice(y0, y1), slice(x0, x1)), cov

    def line(self, path, width, colour, alpha=1.0, taper=(0.2, 0.35), smooth=True, dry=0.0, clip=None):
        """a line painted with a small round brush, tapering in and out"""
        Q = np.asarray(path, np.float32)
        if smooth and len(Q) > 2: Q = spline(Q, 10)
        sl, m = self._strands_mask([Q], [width], taper)
        if sl is None: return
        A = m * alpha
        if dry: A = A * smoothstep(0.2, 0.55, self.P.G[sl] + (1 - dry) * 0.45)
        if clip is not None: A = A * clip[sl]
        self._put(sl, A, hexc(colour))

    def spatter(self, mask, colour, n=300, size=(0.6, 2.0), alpha=0.8, seed=None):
        """flecks of paint (a flicked brush or a sponge): tiny dots inside mask"""
        P = self.P
        r = self._r(seed)
        sl = self._bbox(mask)
        if sl is None: return
        sub = mask[sl] > 0.5
        idx = np.flatnonzero(sub)
        if not len(idx): return
        pick = r.choice(idx, n)
        ys = pick // sub.shape[1] + sl[0].start + r.random(n)
        xs = pick % sub.shape[1] + sl[1].start + r.random(n)
        paths = [np.array([[x, y]], np.float32) for x, y in zip(xs, ys)]
        s2, m = self._strands_mask(paths, r.uniform(*size, n) * 2, fills=r.uniform(120, 255, n))
        if s2 is None: return
        col = colour if np.ndim(colour) != 3 else colour[s2]
        self._put(s2, m * alpha * mask[s2], col if np.ndim(col) == 3 else hexc(col))

    # ================================================================== faces
    def eye(self, cx, cy, r, ry=None, iris='#1d2b2e', iris_r=0.58, look=(0.0, 0.0), lid=0.22, lid_colour=None,
            white='#f4efe3', outline='#4a2a22', ring=None, catch=(-0.38, -0.42), lashes=0, lash_dir=1, rot=0.0,
            lower=0.35, iris_light=None):
        """a round picture-book eye: an off-white ball shaded under the lid, a dark (or teal) iris with a lighter
        lower half, a black pupil, a white catchlight, a small lid with a dark lid line, and a thin warm outline.
        look = (dx, dy) in -1..1 moves the iris (1 = touching the rim); lid = how far the upper lid comes down (0..1)."""
        P = self.P
        ry = r if ry is None else ry
        ball = self.ellipse(cx, cy, r, ry, rot)
        clip = self.rough(ball, 0.35)
        wh = hexc(white)
        sh = mix(white, '#8d93a8', 0.55)
        q = np.clip((P.YY - (cy - ry)) / (2 * ry), 0, 1)
        field = wh + (sh - wh) * (0.9 * (1 - smoothstep(0.0, 0.62, q)))[..., None]
        sl = self._bbox(clip)
        self._put(sl, clip[sl], field[sl])
        self.strokes(ball, field, angle=0, length=(r * 0.5, r * 1.1), width=(r * 0.2, r * 0.38), density=1.6,
                     dry=0.1, alpha=0.6, clip=clip, pickup=0.2, vj=0.01)
        # iris and pupil
        ir = r * iris_r
        ix, iy = cx + look[0] * (r - ir * 0.92), cy + look[1] * (ry - ir * 0.92)
        im = self.ellipse(ix, iy, ir, ir * 1.02) * clip
        ic = hexc(iris)
        il = hexc(iris_light) if iris_light is not None else mix(ic, '#7fb3a8', 0.35)
        qq = np.clip((P.YY - (iy - ir)) / (2 * ir), 0, 1)
        dd = np.sqrt((P.XX - ix) ** 2 + (P.YY - iy) ** 2) / ir
        ifield = ic + (il - ic) * (smoothstep(0.45, 1.0, qq) * smoothstep(1.0, 0.55, dd) * 0.8)[..., None]
        ifield = ifield * (1 - 0.35 * smoothstep(0.78, 1.0, dd))[..., None]
        s2 = self._bbox(im)
        if s2 is not None:
            self._put(s2, im[s2], ifield[s2])
            if ring is not None:
                rg = (smoothstep(0.42, 0.62, dd) * smoothstep(0.92, 0.7, dd))
                self._put(s2, (rg * im)[s2] * 0.75 * smoothstep(0.3, 0.7, P.G[s2] + 0.2), hexc(ring))
            pm = self.ellipse(ix, iy, ir * 0.55, ir * 0.56) * clip
            self._put(s2, pm[s2] * 0.95, hexc('#0d0c10'))
        # the lid and its shadow on the ball
        if lid > 0:
            yl = cy - ry + 2 * ry * lid
            arc = yl + (ry * 0.18) * ((P.XX - cx) / r) ** 2
            lm = ball * smoothstep(arc + 1.2, arc - 1.2, P.YY)
            self.glaze(ball * smoothstep(arc + ry * 0.45, arc, P.YY), '#6c6a86', 0.45, 'multiply')
            lc = lid_colour if lid_colour is not None else '#e2a688'
            sl3 = self._bbox(lm)
            if sl3 is not None:
                self._put(sl3, self.rough(lm, 0.3)[sl3], hexc(lc))
            xs = np.linspace(cx - r * 1.04, cx + r * 1.04, 24)
            ys = yl + (ry * 0.18) * ((xs - cx) / r) ** 2
            ys = np.minimum(ys, cy + ry * np.sqrt(np.clip(1 - ((xs - cx) / (r * 1.04)) ** 2, 0, 1)))
            self.line(np.stack([xs, ys], 1), max(1.6, r * 0.13), outline, 0.92, taper=(0.25, 0.25))
            for k in range(lashes):
                t = 0.62 + 0.36 * k / max(1, lashes - 1)
                sgn = lash_dir
                x0 = cx + sgn * (t - 0.5) * 2 * r * 0.98
                y0 = yl + (ry * 0.18) * ((x0 - cx) / r) ** 2
                self.line([(x0, y0), (x0 + sgn * r * 0.28, y0 - r * 0.22), (x0 + sgn * r * 0.48, y0 - r * 0.28)],
                          max(1.2, r * 0.07), outline, 0.9, taper=(0.1, 0.9))
        # thin warm outline round the lower part of the ball, and a soft lower lid
        tt = np.linspace(0.08 * np.pi, 0.92 * np.pi, 30)
        a = np.deg2rad(rot)
        ox, oy = np.cos(tt) * r * 1.02, np.sin(tt) * ry * 1.02
        pts = np.stack([cx + ox * np.cos(a) - oy * np.sin(a), cy + ox * np.sin(a) + oy * np.cos(a)], 1)
        self.line(pts, max(1.0, r * 0.07), outline, 0.55, taper=(0.4, 0.4), dry=0.4)
        if lower:
            tt = np.linspace(0.22 * np.pi, 0.78 * np.pi, 20)
            pts = np.stack([cx + np.cos(tt) * r * 1.18, cy + np.sin(tt) * ry * 1.22], 1)
            self.line(pts, max(1.0, r * 0.08), '#b46a58', lower, taper=(0.5, 0.5), dry=0.5)
        # catchlights
        if catch is not None:
            self.dab(ix + catch[0] * ir, iy + catch[1] * ir, max(1.6, ir * 0.24), '#fbf8f0', 0.97, dry=0.0)
            self.dab(ix + catch[0] * ir * -0.7, iy + catch[1] * ir * -0.8, max(0.9, ir * 0.09), '#fbf8f0', 0.75, dry=0.0)
        return ball

    def nose(self, cx, cy, rx, ry=None, colour='nose', mask=None, cast=(0.22, 0.48, 0.42), nostrils=0.9,
             highlight=0.9, steps=4, shadow_colour='#8a3f3a', on=None, rot=0.0):
        """a big bulbous nose: a soft core shadow on the face below it, the bulb modelled as a sphere in value steps
        with strokes curving round it, warm reflected light in the lower rim, two dark nostril marks and a soft
        pinkish highlight with a sharp white glint"""
        ry = rx * 0.9 if ry is None else ry
        m = self.ellipse(cx, cy, rx, ry, rot) if mask is None else mask
        if cast:
            sh = blur(_shift(m, rx * cast[0], ry * cast[1]), max(3, rx * 0.22)) * (1 - m)
            if on is not None: sh = sh * on
            self.glaze(sh, shadow_colour, cast[2], 'multiply')
        cols = ramp(colour, deep=0.52, shadow=0.76, light=0.22, pale=0.5, cool='#4a1830')
        self.sphere_shade(cx, cy, rx, ry, cols, steps=steps, mask=m, rot=rot, reflect=0.22,
                          length=(rx * 0.25, rx * 0.6), width=(rx * 0.1, rx * 0.2))
        if nostrils:
            for sgn in (-1, 1):
                x0 = cx + sgn * rx * 0.38; y0 = cy + ry * 0.62
                self.line([(x0 - sgn * rx * 0.13, y0 - ry * 0.05), (x0, y0 + ry * 0.07), (x0 + sgn * rx * 0.12, y0 + ry * 0.02)],
                          max(1.6, rx * 0.085), mix(colour, '#3a0f1a', 0.6), nostrils, taper=(0.3, 0.6))
        if highlight:
            hx, hy = cx - rx * 0.36, cy - ry * 0.4
            self.blush(hx, hy, rx * 0.34, ry * 0.3, mix(colour, '#fff1e0', 0.62), 0.7 * highlight, grain=0.4,
                       mask=m, solid=0.3)
            self.dab(hx - rx * 0.04, hy - ry * 0.04, max(1.5, rx * 0.075), '#fffaf2', 0.9 * highlight, dry=0.05)
        return m

    def ear(self, cx, cy, rx, ry, colour='ruddy', side=-1, rot=0.0, steps=3):
        """a big ear: modelled as a soft disc, the inner fold as a darker C-curve with a lit rim"""
        m = self.blob(cx, cy, rx, ry, 0.05, int(self.rng.integers(1 << 20)), rot)
        self.block_in(m, colour, length=(10, 26), width=(6, 12))
        self.model_form(m, ramp(colour), steps=steps, round_=0.4, length=(10, 24), width=(5, 10))
        k = -side
        tt = np.linspace(-0.85, 0.8, 18) * np.pi / 2
        pts = np.stack([cx + k * (np.cos(tt) * rx * 0.42 - rx * 0.05), cy + np.sin(tt) * ry * 0.58], 1)
        self.line(pts, max(2.0, rx * 0.16), mix(colour, '#5a1e28', 0.45), 0.6, taper=(0.4, 0.5), dry=0.2)
        self.line(pts + np.array([-k * rx * 0.12, -ry * 0.04]), max(1.5, rx * 0.08), mix(colour, '#fff0dc', 0.4),
                  0.5, taper=(0.4, 0.5), dry=0.3)
        return m

    # ================================================================== textures
    def knit(self, mask, stitch=(15, 11), origin=None, curve=0.0, angle=0.0, path=None, cables=(), cable_period=None,
             strength=0.75, highlight=0.3, fuzz=0.5, depth=0.45, seed=None):
        """stockinette (rows of V stitches) multiplied onto the paint that is already there. origin: the centre
        of the garment (rows bow away from it by `curve` rows at the sides: > 0 sag, < 0 arch); angle rotates
        the rows; path: the stitch columns follow a polyline (a scarf). cables: [(x, width)] columns (in the
        rotated frame) where two strands twist round each other instead."""
        P = self.P
        r = self._r(seed)
        sl = self._bbox(mask, 1)
        if sl is None: return
        sw, sh = stitch
        X, Y = P.XX[sl], P.YY[sl]
        if path is not None:
            S, Tt, _, _ = self._path_st(np.asarray(spline(np.asarray(path, np.float32), 8) if len(path) > 2 else path, np.float32), sl)
            Xr, Yr = Tt, S
            ox, hw = 0.0, max(1.0, float(np.abs(Tt[mask[sl] > 0.5]).max()) if (mask[sl] > 0.5).any() else 1.0)
        else:
            if angle:
                a = np.deg2rad(angle); c, s = np.cos(a), np.sin(a)
                Xr, Yr = X * c + Y * s, -X * s + Y * c
            else:
                Xr, Yr = X, Y
            ox = origin[0] if origin is not None else (sl[1].start + sl[1].stop) / 2
            hw = (sl[1].stop - sl[1].start) / 2
        U = (Xr - ox) / sw + 0.5
        V = Yr / sh + curve * ((Xr - ox) / hw) ** 2
        iu = np.floor(U); fu = U - iu - 0.5
        Hh = np.zeros_like(U); win_v = np.zeros_like(U)
        legd = np.array([0.44 * sw, 1.1 * sh]); legl = float(np.linalg.norm(legd))
        a_ = 0.5 * legl * 1.0; b_ = 0.215 * sw
        for dv in (-1, 0, 1):
            iv = np.floor(V) + dv
            hj1 = _hash(iu + 0.37, iv) - 0.5; hj2 = _hash(iu, iv + 0.71) - 0.5; hj3 = _hash(iu + 0.13, iv + 0.29)
            fv = V - iv - 0.5 - hj2 * 0.12
            px, py = (fu - hj1 * 0.10) * sw, fv * sh
            sc = 0.9 + 0.2 * hj3
            for side in (-1, 1):
                dx, dy = -side * legd[0] / legl, legd[1] / legl
                rx_, ry_ = px - side * 0.235 * sw, py
                al = rx_ * dx + ry_ * dy
                ac = -rx_ * dy + ry_ * dx
                e = (al / (a_ * sc)) ** 2 + (ac / (b_ * sc)) ** 2
                hl = np.sqrt(np.clip(1 - e, 0, 1))
                hl = hl * (0.86 + 0.14 * np.sin((al / a_ * 2.6 + ac / b_ * 0.9) * np.pi + hj3 * 3))
                # the leg of the row below sits over the bottom of this one: favour the lower row a little
                hl = hl * (1.0 + 0.06 * dv)
                win = hl > Hh
                Hh = np.where(win, hl, Hh); win_v = np.where(win, iv, win_v)
        jit = _hash(iu, win_v) - 0.5
        if cables:
            per = cable_period or sh * 7
            for xc, cw in cables:
                d = Xr - xc
                inside = smoothstep(cw / 2 + 1.5, cw / 2 - 1.5, np.abs(d))
                if not inside.any(): continue
                ph = Yr / per * 2 * np.pi
                off = 0.21 * cw * np.cos(ph)
                rs = 0.27 * cw
                hA = np.sqrt(np.clip(1 - ((d - off) / rs) ** 2, 0, 1))
                hB = np.sqrt(np.clip(1 - ((d + off) / rs) ** 2, 0, 1))
                front = np.sin(ph) > 0
                hc = np.where(front, np.maximum(hA * 1.1, hB * 0.75), np.maximum(hB * 1.1, hA * 0.75))
                hc = hc * (0.84 + 0.16 * np.abs(np.cos(Yr / (sh * 0.95) * np.pi + np.abs(d) * 0.25)))
                groove = smoothstep(cw / 2 - 1, cw / 2 - 3.5, np.abs(d))
                hc = hc * groove
                Hh = Hh * (1 - inside) + hc * inside
        hh = Hh * depth * sw
        gy, gx = np.gradient(hh)
        Lv = self.light
        nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
        lam = np.clip((-gx * Lv[0] - gy * Lv[1] + Lv[2]) * nz, 0, 1)
        ao = 0.42 + 0.58 * smoothstep(0.0, 0.55, Hh)
        k = ao * (0.55 + 0.75 * lam) * (1 + 0.16 * jit)
        h, w = k.shape
        k = blur(k, 0.55)
        if fuzz:
            k = k * (1 + fuzz * 0.10 * (noise2d(h, w, 1.6, 2, int(r.integers(1 << 30))) - 0.5))
        m = mask[sl]
        mk = float((k * m).sum() / (m.sum() + 1e-6))
        k = k / mk
        Cs = P.C[sl]
        loose = 0.6 + 0.4 * smoothstep(0.25, 0.7, noise2d(h, w, 60, 2, int(r.integers(1 << 30))))
        f = 1 + strength * loose * (k - 1) * m
        Cs *= f[..., None]
        if highlight:
            hl = smoothstep(0.62, 0.9, lam * Hh) * smoothstep(0.45, 0.65, P.G[sl] + 0.1) * m
            tgt = np.clip(Cs * 1.22 + 0.06, 0, 1)
            Cs += (tgt - Cs) * (hl * highlight)[..., None]
        np.clip(Cs, 0, 1, out=Cs)

    def rib(self, mask, path, period=8.0, strength=0.75, highlight=0.25, rows=0.85, seed=None):
        """ribbing across a band (collar, cuff, hat brim): raised knit columns and sunken purl columns at right
        angles to `path` (the band's centre line), with small chevrons of stitches along each column"""
        P = self.P
        sl = self._bbox(mask, 1)
        if sl is None: return
        Q = np.asarray(path, np.float32)
        if len(Q) > 2: Q = spline(Q, 8)
        S, Tt, _, _ = self._path_st(Q, sl)
        ph = S / period
        f = ph - np.floor(ph) - 0.5
        Hh = np.sqrt(np.clip(1 - (f / 0.34) ** 2, 0, 1))
        if rows:
            g = Tt / (period * 0.62) + np.abs(f) * 1.4
            Hh = Hh * (1 - 0.22 * rows + 0.22 * rows * np.abs(np.cos(g * np.pi)))
        hh = Hh * period * 0.45
        gy, gx = np.gradient(hh)
        Lv = self.light
        nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
        lam = np.clip((-gx * Lv[0] - gy * Lv[1] + Lv[2]) * nz, 0, 1)
        k = (0.42 + 0.58 * smoothstep(0, 0.5, Hh)) * (0.55 + 0.75 * lam)
        m = mask[sl]
        k = k / float((k * m).sum() / (m.sum() + 1e-6))
        Cs = P.C[sl]
        Cs *= (1 + strength * (k - 1) * m)[..., None]
        if highlight:
            hl = smoothstep(0.6, 0.92, lam * Hh) * smoothstep(0.45, 0.65, P.G[sl] + 0.1) * m
            tgt = np.clip(Cs * 1.2 + 0.05, 0, 1)
            Cs += (tgt - Cs) * (hl * highlight)[..., None]
        np.clip(Cs, 0, 1, out=Cs)

    def _flow_at(self, flow, x, y):
        P = self.P
        if callable(flow): return np.asarray(flow(x, y), np.float32)
        if np.ndim(flow) == 2:
            return flow[np.clip(y.astype(int), 0, P.h - 1), np.clip(x.astype(int), 0, P.w - 1)]
        return np.full(len(x), float(flow), np.float32)

    def hair_strands(self, mask, flow, colours, n=600, length=(18, 50), width=(0.9, 2.0), shade=None, spread=0.22,
                     curl=0.0, jitter=8.0, step=3.0, alpha=0.95, clip=True, pad=4.0, roots=None,
                     taper=(0.08, 0.6), opacity=(0.75, 1.0), seed=None):
        """many fine painted hairs over a mass: each starts inside `mask` (or `roots`), follows `flow` (degrees:
        a number, a panel-size field, or f(x, y)) with its own jitter and steady bend (`curl` degrees per step),
        and is drawn as a tapered round-brush line. Each picks a colour from `colours` (dark -> light) by the
        light field `shade` (0..1 panel-size) plus noise, and they are painted dark first, light last."""
        P = self.P
        r = self._r(seed)
        src = roots if roots is not None else mask
        sl = self._bbox(src)
        if sl is None: return
        sub = src[sl] > 0.5
        idx = np.flatnonzero(sub)
        if not len(idx): return
        pick = r.choice(idx, n)
        y = (pick // sub.shape[1] + sl[0].start).astype(np.float32) + r.random(n)
        x = (pick % sub.shape[1] + sl[1].start).astype(np.float32) + r.random(n)
        lens = r.uniform(*length, n)
        ns = max(2, int(lens.max() / step) + 1)
        jit = r.normal(0, jitter, n) if flow is not None else r.uniform(0, 360, n)
        if flow is None: flow = 0.0
        bend = r.normal(0, 1, n) * curl
        Xs = np.zeros((n, ns + 1), np.float32); Ys = np.zeros((n, ns + 1), np.float32)
        Xs[:, 0], Ys[:, 0] = x, y
        for k in range(ns):
            a = np.deg2rad(self._flow_at(flow, Xs[:, k], Ys[:, k]) + jit + bend * k)
            Xs[:, k + 1] = Xs[:, k] + np.cos(a) * step
            Ys[:, k + 1] = Ys[:, k] + np.sin(a) * step
        npts = np.clip((lens / step).astype(int) + 1, 2, ns + 1)
        nc = len(colours)
        base = shade[np.clip(y.astype(int), 0, P.h - 1), np.clip(x.astype(int), 0, P.w - 1)] if shade is not None else np.full(n, 0.5)
        cls = np.clip(np.floor((base + r.normal(0, spread, n)) * nc), 0, nc - 1).astype(int)
        widths = r.uniform(*width, n)
        fills = r.uniform(opacity[0], opacity[1], n) * 255
        cm = None
        if clip is True:
            cm = smoothstep(0.03, 0.3, blur(mask, pad))
        elif clip is not None and clip is not False:
            cm = clip
        for c in range(nc):
            sel = np.flatnonzero(cls == c)
            if not len(sel): continue
            paths = [np.stack([Xs[i, :npts[i]], Ys[i, :npts[i]]], 1) for i in sel]
            s2, m = self._strands_mask(paths, widths[sel], taper, fills[sel])
            if s2 is None: continue
            A = m * alpha
            if cm is not None: A = A * cm[s2]
            self._put(s2, A, hexc(colours[c]))

    def felt(self, mask, strength=0.7, fibres=1.0, fuzz=1.0, seed=None):
        """matted fibre: a fine two-scale mottle, short random fibres a little lighter and darker than the paint
        under them, and fibres sticking out across the silhouette"""
        P = self.P
        r = self._r(seed)
        sl = self._bbox(mask, 6)
        if sl is None: return
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        n1 = noise2d(h, w, 1.8, 2, int(r.integers(1 << 30))) - 0.5
        n2 = noise2d(h, w, 9, 3, int(r.integers(1 << 30))) - 0.5
        m = mask[sl]
        Cs = P.C[sl]
        Cs *= (1 + strength * (0.16 * n1 + 0.14 * n2) * m)[..., None]
        np.clip(Cs, 0, 1, out=Cs)
        if fibres:
            area = float(m.sum())
            mean = (Cs * m[..., None]).sum((0, 1)) / (area + 1e-6)
            nfib = int(area / 55 * fibres)
            if nfib > 0:
                self.hair_strands(mask, None, [mean * 0.8, np.clip(mean * 1.18 + 0.03, 0, 1)], n=nfib,
                                  length=(3, 8), width=(0.6, 1.0), step=1.5, jitter=60, curl=12, alpha=0.4,
                                  clip=mask, seed=int(r.integers(1 << 30)))
        if fuzz:
            b = blur(mask, 1.5)
            edge = (smoothstep(0.15, 0.5, b) * smoothstep(0.95, 0.6, b) > 0.5).astype(np.float32)
            if edge.any():
                Cs2 = P.C[sl]
                mean = (Cs2 * m[..., None]).sum((0, 1)) / (m.sum() + 1e-6)
                gy, gx = np.gradient(blur(mask, 3))
                out_ang = np.degrees(np.arctan2(-gy, -gx))
                ne = int(edge.sum() / 3 * fuzz)
                if ne > 0:
                    self.hair_strands(mask, out_ang, [mean * 0.9, mean], n=ne, roots=edge, length=(3, 7),
                                      width=(0.6, 1.0), step=1.5, jitter=35, alpha=0.6, clip=False,
                                      seed=int(r.integers(1 << 30)))

    # ================================================================== finish
    def grain(self, amount=1.0):
        """reproduce the painting in a book: paper speckle, warm paper in the lights, ink that never reaches black"""
        self.print_amt = float(amount)

    def render(self):
        C = self.C
        Lv = self.light
        h = self.G * 1.1 + np.minimum(blur(self.T, 0.8), 3.0) * 0.55
        gy, gx = np.gradient(h)
        lit = 1 + (-gx * Lv[0] - gy * Lv[1]) * 0.09
        out = C * lit[..., None]
        p = self.print_amt
        if p:
            if not hasattr(self, '_speck'):
                r = np.random.default_rng(self.seed + 7)
                sp = r.normal(0, 1, (self.H, self.W)).astype(np.float32)
                self._speck = 0.65 * sp + 0.35 * blur(sp, 1.2) * 2.0
            lum = out.mean(-1, keepdims=True)
            out = lum + (out - lum) * (1 - 0.05 * p)                           # ink saturation a touch lower
            paper = hexc('#f7f0e2')
            out = out * (1 - 0.06 * p * smoothstep(0.6, 1.0, lum)) + paper * 0.06 * p * smoothstep(0.6, 1.0, lum)
            out = 0.045 * p * hexc('#2a1f2a') + out * (1 - 0.045 * p)          # blacks lift to the darkest ink
            out = out * (1 + 0.022 * p * self._speck[..., None])
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
