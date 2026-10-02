"""cave -- Ice-Age cave painting: ochre and charcoal on a firelit limestone wall (numpy + Pillow only).

A cave painting is pigment laid on a rock surface in the dark, and seen only by a flame. It is the opposite of a
petroglyph (petroglyph.py), which knocks the dark skin off a sunlit rock: here nothing is cut, the colour sits on top
of pale limestone, the rock's own bulges give the animals their volume, and the only light is a fire on the floor.

Model:
  wall      a limestone cave wall is a height field (px) and an albedo. Broad undulations; `boss()` adds the rounded
            bulges the painters chose to put a bison's belly or a horse's flank on; solution scallops (shallow
            spoon-shaped dishes with sharp rims, left by the water that dissolved the cave); grain and small pits.
            The stone is cream to buff with ochre and grey stains and a whiter calcite crust on the convex parts.
            `fold()` lifts the face on one side of a line (where the wall changes plane, with a lit crest);
            `flowstone()` hangs calcite drapery with orange "bacon" bands that stays wet and glints; `crack()` cuts
            fissures; `floor()` puts a packed-clay floor below the wall base (tilted toward the viewer).
  pigment   red ochre (hematite), yellow ochre (goethite), brown, charcoal and manganese black. Every deposit is a
            coverage field multiplied into the albedo: the rock's own mottling shows through even a dense coat.
            How it gets there decides how it looks:
              sketch   a charcoal stick dragged lightly, twice, round a slightly wandering contour (searching lines);
              line     a charcoal stick or a finger loaded with wet paint along a stroke; the dry stick only catches
                       the rock's high points (the "tooth"), so it breaks up in the hollows;
              outline  the finished contour: a black band inside the silhouette, thicker along the back and at the
                       top edges, thinner on the belly, with gaps where the stick skipped;
              blow     pigment spat or blown through a hollow bone: a soft-edged coat with a faint halo past the edge,
                       a speckle of droplets around it and an uneven density; `rim` makes it denser toward the
                       outline, `gradient` darker on the back, `relief` heavier where the wall turns away from the
                       fire (the painters used the rock's shape for volume), `exclude` leaves a pale belly;
              daub     a fur pad dabbed on: blotchy, more on the rock's high points;
              paint    a drafted shape (hunter, spear) filled solid with a finger / stick / brush;
              dots     palm-sized red dots;
              stencil  a hand held flat on the wall and pigment blown round it: the hand stays bare rock inside a
                       sprayed halo; a later stencil cuts its hand out of an earlier halo;
              handprint  a paint-covered palm pressed on: only the rock's high points take the paint.
  figures   drafted in a unit frame and placed with (x, y, size, facing, rot): bison, horse, deer (stag / hind),
            hunter (red Levantine-style runner with a spear), spear, hand, plus generic `shape()`.  A Figure holds
            named masks in a local box (body, legs, tail, horns, antlers, mane, ears + painting regions head, hump,
            belly, back, front); `fig.sel('head', 'mane')` picks some of them; every paint method takes a Figure
            or a selection.
  time      `calcite()` a milky veil (moonmilk) over part of a painting, `flake()` paint lost in small flakes,
            `claws()` a cave bear's claw marks scratched into the soft surface (fresh pale grooves through the
            paint), `soot()` the plume of soot the fire laid on the wall and ceiling.
  fire      `fire()` a campfire on the floor: ring of stones, ash, glowing logs, layered flame tongues (white-yellow
            core, orange body, red tips), sparks and a smoke plume; `lamp()` a stone fat lamp with a small flame.
            Both are point lights: half-Lambert shading from the height-field normals (raking light from below makes
            every bulge read), inverse-square falloff, shadows marched along the light per pixel, specular glints on
            wet calcite, a little cool ambient in the hollows; then flame emission, bloom, smoke and a filmic
            tone curve. Light is cached and only recomputed when the height field changes.
  props     `stone()` a slab or pebble on the floor, `heap()` a mound of ground pigment, `stick()` a charcoal stick
            or a hollow bone blowpipe.
Order: wall -> boss / flowstone / crack -> floor -> fire / lamp / props -> sketch -> colour (blow / daub) ->
black (blow / outline / line) -> hunters, hands, dots -> calcite / flake / claws / soot.
Coordinates are px, y down; angles in degrees, counter-clockwise; facing 1 = right, -1 = left.

    from cave import CavePainting
    cv = CavePainting(1920, 1080, seed=3)
    cv.wall(); cv.boss(1400, 450, 260, 170, 45); cv.floor(965)
    cv.fire(240, 1050, 230); cv.lamp(1690, 1000, 120)
    b = cv.bison(1430, 480, 440, facing=1)
    cv.sketch(b); cv.blow(b.sel('body'), 'red', exclude=b.sel('belly'), rim=0.35)
    cv.blow(b.sel('head', 'hump', 'legs'), 'black', clip=b); cv.outline(b)
    cv.stencil(cv.hand(160, 230, 130, rot=-12), 'red')
    cv.soot(240, 860, amount=0.5)
    cv.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, height_normals, ambient_occlusion

LIMESTONE = '#d3c0a2'
CALCITE = '#e9e0d1'
FLOOR = '#6e5240'
SOOT = '#120d0a'
PIGMENTS = {
    'red': '#93281a',        # red ochre (hematite)
    'darkred': '#5e1c11',
    'orange': '#a9592a',     # burnt yellow ochre
    'yellow': '#c4903f',     # yellow ochre (goethite)
    'brown': '#5f3620',      # umber
    'black': '#120e0c',      # charcoal
    'manganese': '#26221f',  # manganese oxide, a cooler black
    'white': '#ddd3c3',      # kaolin
}
FIRE = np.array([1.00, 0.60, 0.29], np.float32)
LAMPLIGHT = np.array([1.00, 0.68, 0.36], np.float32)
REGIONS = ('head', 'hump', 'belly', 'back', 'front', 'eye')


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str):
        return hexc(PIGMENTS.get(c, c)) if not c.startswith('#') else hexc(c)
    return np.asarray(c, np.float32)


def _closed(P, per=8):
    """closed Catmull-Rom through control points"""
    P = np.asarray(P, np.float32)
    Q = np.vstack([P[-1:], P, P[:2]])
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out, np.float32)


def _open(P, widths, per=10):
    """open spline through control points + width per sample (widths given at the control points)"""
    P = np.asarray(P, np.float32)
    if len(P) < 3:
        P = np.vstack([P[0], (P[0] + P[-1]) / 2, P[-1]]) if len(P) == 2 else P
        if np.ndim(widths) and len(widths) == 2: widths = [widths[0], (widths[0] + widths[1]) / 2, widths[1]]
    S = spline(P, per)
    w = np.broadcast_to(np.asarray(widths, np.float32), (len(P),)) if np.ndim(widths) else np.full(len(P), widths, np.float32)
    idx = np.arange(len(S), dtype=np.float32) / per
    return S, np.interp(idx, np.arange(len(P)), w).astype(np.float32)


def _dense(S, w):
    """resample a stroke so circles of radius w/2 overlap smoothly"""
    seg = np.linalg.norm(np.diff(S, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    step = max(0.5, float(np.min(w)) * 0.25)
    t = np.arange(0, s[-1] + 1e-3, step)
    return np.stack([np.interp(t, s, S[:, 0]), np.interp(t, s, S[:, 1])], 1), np.interp(t, s, w)


class Sel:
    """a mask in a local box (x0, y0, x1, y1) -- what every paint method works on"""
    def __init__(self, box, m):
        self.box, self.m = box, m


class Figure:
    """a drafted shape: named float masks in one local box; anchors are named points in image px"""
    def __init__(self, box, kind=''):
        self.box, self.kind = box, kind
        self.parts, self.anchors = {}, {}

    @property
    def shape(self):
        return self.box[3] - self.box[1], self.box[2] - self.box[0]

    def add(self, name, m):
        self.parts[name] = np.maximum(self.parts[name], m) if name in self.parts else m

    def mask(self, *names):
        names = names or [k for k in self.parts if k not in REGIONS]
        out = np.zeros(self.shape, np.float32)
        for k in names:
            if k in self.parts: np.maximum(out, self.parts[k], out=out)
        return out

    def sel(self, *names):
        return Sel(self.box, self.mask(*names))

    @property
    def m(self):
        return self.mask()


class CavePainting:
    def __init__(self, W=1920, H=1080, seed=0):
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.h = np.zeros((H, W), np.float32)
        self.rock = np.ones((H, W, 3), np.float32) * hexc(LIMESTONE)
        self.alb = self.rock.copy()
        self.load = np.zeros((H, W), np.float32)      # how much paint sits on each pixel (flaking takes it off)
        self.wet = np.zeros((H, W), np.float32)
        self.lights, self.fires, self.lamps = [], [], []
        self.floor_line = None
        self._grain = np.zeros((H, W), np.float32)
        self._rock_mean = float(self.rock.mean())
        self._floor_m = np.zeros((H, W), np.float32)
        self.stages = []
        self._lit = None
        self._fx = None
        self._aux = None

    # ------------------------------------------------------------------ helpers
    def _s(self):
        return int(self.rng.integers(1 << 30))

    def _grid(self):
        return np.mgrid[0:self.H, 0:self.W].astype(np.float32)

    def _dirty(self):
        self._lit = None; self._aux = None

    def _box(self, pts, pad=70):
        P = np.asarray(pts, np.float32).reshape(-1, 2)
        x0 = int(max(0, np.floor(P[:, 0].min() - pad))); x1 = int(min(self.W, np.ceil(P[:, 0].max() + pad)))
        y0 = int(max(0, np.floor(P[:, 1].min() - pad))); y1 = int(min(self.H, np.ceil(P[:, 1].max() + pad)))
        return (x0, y0, max(x1, x0 + 2), max(y1, y0 + 2))

    @staticmethod
    def _sl(box):
        return slice(box[1], box[3]), slice(box[0], box[2])

    def _raster(self, box, polys=(), strokes=(), discs=(), ss=2):
        """polygons (closed point lists), strokes ((pts, widths) sampled densely) and discs ((x, y, r)) -> float mask"""
        x0, y0, x1, y1 = box
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        d = ImageDraw.Draw(im)
        for P in polys:
            d.polygon([((float(x) - x0) * ss, (float(y) - y0) * ss) for x, y in P], fill=255)
        for S, w in strokes:
            S, w = _dense(np.asarray(S, np.float32), np.asarray(w, np.float32))
            for (x, y), ww in zip(S, w):
                r = max(0.35, ww / 2) * ss
                cx, cy = (x - x0) * ss, (y - y0) * ss
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        for x, y, r in discs:
            r *= ss; cx, cy = (x - x0) * ss, (y - y0) * ss
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
        if ss > 1: im = im.resize((x1 - x0, y1 - y0), Image.BOX)
        return np.asarray(im, np.float32) / 255

    def _target(self, t):
        if isinstance(t, (Sel, Figure)): return t.box, t.m
        raise TypeError('paint target must be a Figure or Figure.sel(...)')

    def _local(self, mask_obj, box):
        """another Figure/Sel's mask re-cut to `box`"""
        if mask_obj is None: return None
        b2, m2 = self._target(mask_obj)
        out = np.zeros((box[3] - box[1], box[2] - box[0]), np.float32)
        ix0, iy0 = max(box[0], b2[0]), max(box[1], b2[1]); ix1, iy1 = min(box[2], b2[2]), min(box[3], b2[3])
        if ix1 > ix0 and iy1 > iy0:
            out[iy0 - box[1]:iy1 - box[1], ix0 - box[0]:ix1 - box[0]] = m2[iy0 - b2[1]:iy1 - b2[1], ix0 - b2[0]:ix1 - b2[0]]
        return out

    def _noise(self, box, scale, octaves=3):
        h, w = box[3] - box[1], box[2] - box[0]
        return noise2d(h, w, scale, octaves, self._s())

    def _auxiliary(self):
        """rock tooth (how much a dry stick catches) and the large-scale wall normal (for relief shading)"""
        if self._aux is None:
            h = self.h
            hp = h - blur(h, 2.5)
            tooth = hp / (hp.std() + 1e-6) + 0.9 * self._grain
            hb = blur(h, 14)
            gy, gx = np.gradient(hb)
            self._aux = (tooth.astype(np.float32), gx.astype(np.float32), gy.astype(np.float32))
        return self._aux

    def _catch(self, box, press):
        """dry pigment on rock: high points take it first; press 0..1"""
        tooth = self._auxiliary()[0][self._sl(box)]
        return smoothstep(-1.4, 0.9, tooth + (press - 0.5) * 2.6)

    def _deposit(self, box, cov, pigment):
        sl = self._sl(box)
        col = _c(pigment)
        rock = self.rock[sl]
        tex = 0.80 + 0.20 * rock.mean(-1, keepdims=True) / self._rock_mean
        g = self._grain[sl][..., None]
        paint = col * tex * (1 + 0.05 * g)
        a = np.clip(cov, 0, 1)[..., None]
        self.alb[sl] = self.alb[sl] * (1 - a) + paint * a
        np.maximum(self.load[sl], np.clip(cov, 0, 1), out=self.load[sl])

    # ------------------------------------------------------------------ the wall
    def wall(self, colour=LIMESTONE, relief=1.0, scallops=1.0, grain=1.0):
        """limestone height field (undulations, scallops, grain, pits) and its stains"""
        H, W = self.H, self.W
        r = self.rng
        big = noise2d(H, W, 460, 3, self._s()) - 0.5
        mid = noise2d(H, W, 120, 4, self._s()) - 0.5
        rid = 1 - np.abs(noise2d(H, W, 240, 3, self._s()) * 2 - 1)            # ridged: crests where the rock folds
        h = relief * (big * 46 + mid * 10 + rid ** 2 * 10)
        sc = self._scallops(110, depth=1.8)
        patch = smoothstep(0.45, 0.75, noise2d(H, W, 380, 2, self._s()))
        h += scallops * sc * (0.15 + 0.85 * patch)
        self._grain = blur(r.normal(0, 1, (H, W)).astype(np.float32), 0.7)
        self._grain /= self._grain.std() + 1e-6
        h += grain * (0.12 * self._grain + 0.7 * (noise2d(H, W, 9, 2, self._s()) - 0.5)
                      + 1.1 * (noise2d(H, W, 40, 3, self._s()) - 0.5))
        pits = np.zeros((H, W), np.float32)
        for _ in range(int(60 * W * H / 2.07e6)):            # small solution pits, clay settles in them
            x, y, rr = r.uniform(0, W), r.uniform(0, H), r.uniform(1.5, 4.0)
            R = int(rr * 2 + 2); ix, iy = int(x), int(y)
            if ix < R or iy < R or ix >= W - R or iy >= H - R: continue
            yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
            d2 = ((xx - (x - ix)) ** 2 + (yy - (y - iy)) ** 2) / (rr * rr)
            h[iy - R:iy + R + 1, ix - R:ix + R + 1] -= np.clip(1 - d2, 0, 1) * rr * 0.3
            np.maximum(pits[iy - R:iy + R + 1, ix - R:ix + R + 1], np.clip(1.2 - d2, 0, 1),
                       out=pits[iy - R:iy + R + 1, ix - R:ix + R + 1])
        self.h = h.astype(np.float32)
        # albedo: cream to buff, ochre and grey stains, calcite crust on convex parts
        base = hexc(colour)
        t1 = noise2d(H, W, 300, 4, self._s())[..., None]
        alb = base * (0.86 + 0.24 * t1)
        alb = alb * np.array([1.0, 0.985, 0.96], np.float32) ** (2 * (noise2d(H, W, 160, 3, self._s())[..., None] - 0.5))
        st = smoothstep(0.58, 0.80, noise2d(H, W, 210, 4, self._s()))[..., None]
        alb = alb * (1 - 0.45 * st) + hexc('#c5975c') * 0.45 * st
        gr = smoothstep(0.66, 0.86, noise2d(H, W, 230, 4, self._s()))[..., None]
        alb = alb * (1 - 0.22 * gr) + hexc('#9a9184') * 0.22 * gr
        conv = self.h - blur(self.h, 16)
        cal = (smoothstep(1.0, 7.0, conv) * noise2d(H, W, 60, 3, self._s()))[..., None]
        alb = alb * (1 - 0.45 * cal) + hexc(CALCITE) * 0.45 * cal
        alb *= (1 + 0.022 * self._grain)[..., None]
        alb *= (1 - 0.3 * blur(pits, 0.8))[..., None]
        self.rock = np.clip(alb, 0, 1).astype(np.float32)
        self.alb = self.rock.copy()
        self._rock_mean = float(self.rock.mean())
        self._dirty()

    def _scallops(self, cell=70, depth=6.0):
        """solution scallops: min of paraboloids round jittered seeds -> spoon-shaped dishes with sharp rims"""
        H, W = self.H, self.W
        r = self.rng
        gh, gw = H // cell + 3, W // cell + 3
        sx = (np.arange(gw)[None, :] - 1 + r.uniform(0.15, 0.85, (gh, gw))) * cell
        sy = (np.arange(gh)[:, None] - 1 + r.uniform(0.15, 0.85, (gh, gw))) * cell
        Y, X = self._grid()
        ci = (X // cell).astype(np.int32) + 1; cj = (Y // cell).astype(np.int32) + 1
        best = np.full((H, W), np.inf, np.float32)
        for dj in (-1, 0, 1):
            for di in (-1, 0, 1):
                jj, ii = np.clip(cj + dj, 0, gh - 1), np.clip(ci + di, 0, gw - 1)
                px, py = sx[jj, ii], sy[jj, ii]
                d2 = (X - px) ** 2 + ((Y - py) * 1.3) ** 2 + (X - px) * cell * 0.25   # steeper upstream side
                np.minimum(best, d2, out=best)
        v = np.clip(best / (0.55 * cell * cell), 0, 1.4)
        return ((v - v.mean()) * depth).astype(np.float32)

    def boss(self, x, y, rx, ry, height=40.0, rot=0.0):
        """a rounded bulge of the wall (put an animal's belly or flank on it)"""
        box = self._box([(x - rx, y - ry), (x + rx, y + ry), (x - ry, y - rx), (x + ry, y + rx)], 4)
        Y, X = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
        a = np.radians(rot); c, s = np.cos(a), np.sin(a)
        u = ((X - x) * c - (Y - y) * s) / rx; v = ((X - x) * s + (Y - y) * c) / ry
        r2 = u * u + v * v
        self.h[self._sl(box)] += height * np.clip(1 - r2, 0, 1) ** 2
        self._dirty()

    def fold(self, pts, height=14.0, soft=6.0, side=1):
        """a fold where the wall changes plane: the face on one side of the line stands proud by `height` px,
        with a rounded crest (side=1 raises the face below / right of the line's direction)"""
        P = spline(np.asarray(pts, np.float32), 16)
        n = len(P)
        P = P + np.stack([fbm1d(n, 18, 3, self._s()), fbm1d(n, 18, 3, self._s())], 1) * 5
        Y, X = self._grid()
        best = np.full((self.H, self.W), 1e9, np.float32); sgn = np.zeros((self.H, self.W), np.float32)
        arc = np.zeros((self.H, self.W), np.float32)
        cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        for i in range(0, n - 1, 2):                             # signed distance to the polyline (coarse)
            a, b = P[i], P[min(i + 2, n - 1)]
            d = b - a; L2 = float(d @ d) + 1e-6
            t = np.clip(((X - a[0]) * d[0] + (Y - a[1]) * d[1]) / L2, 0, 1)
            qx, qy = X - (a[0] + t * d[0]), Y - (a[1] + t * d[1])
            dist = qx * qx + qy * qy
            closer = dist < best
            best = np.where(closer, dist, best)
            sgn = np.where(closer, np.sign(d[0] * qy - d[1] * qx), sgn)
            arc = np.where(closer, cum[i] + t * (cum[min(i + 2, n - 1)] - cum[i]), arc)
        sd = np.sqrt(best) * sgn * side
        ends = smoothstep(0, 220, arc) * smoothstep(cum[-1], cum[-1] - 220, arc)
        reach = smoothstep(260, 120, np.sqrt(best)) * ends
        self.h += (height * smoothstep(-soft, soft * 2.5, sd) - height * 0.5) * reach
        self._dirty()

    def flowstone(self, x0, x1, top=0, length=420, thick=18.0, folds=44.0):
        """calcite drapery hanging from the top: rounded folds, orange bands, lobed lower edge, wet"""
        H, W = self.H, self.W
        box = (max(0, int(x0) - 20), max(0, int(top)), min(W, int(x1) + 20), min(H, int(top + length * 1.25)))
        Y, X = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
        n = box[2] - box[0]
        L = length * (0.55 + 0.45 * (fbm1d(n, 40, 3, self._s()) * 0.5 + 0.5))[None, :]
        warp = fbm1d(box[3] - box[1], 90, 3, self._s())[:, None] * folds * 0.35
        xw = X + warp + folds * 0.9 * fbm1d(n, 60, 2, self._s())[None, :]
        ph = xw / folds * 2 * np.pi
        ridge = (0.5 + 0.5 * np.cos(ph)) ** 0.8
        side = smoothstep(x0 - 10, x0 + 30, X) * smoothstep(x1 + 10, x1 - 30, X)
        drop = smoothstep(L + 8, L - 40, Y - top)
        m = side * drop
        sl = self._sl(box)
        self.h[sl] += m * (thick * 0.7 + thick * 0.3 * ridge)
        band = 0.5 + 0.5 * np.sin((Y - top) / 9.0 + 3 * fbm1d(n, 30, 2, self._s())[None, :])
        col = hexc(CALCITE) * (1 - 0.25 * band[..., None]) + hexc('#c08a55') * 0.25 * band[..., None]
        col *= (0.88 + 0.12 * ridge)[..., None]
        a = m[..., None] * 0.85
        self.rock[sl] = self.rock[sl] * (1 - a) + col * a
        self.alb[sl] = self.alb[sl] * (1 - a) + col * a
        self.wet[sl] = np.maximum(self.wet[sl], m * (0.55 + 0.45 * ridge))
        self._dirty()

    def crack(self, pts, width=2.0, depth=4.0, branches=1):
        """a fissure: a thin zigzag dark slot (jagged at a few px, tapering at both ends), short side branches"""
        P = spline(np.asarray(pts, np.float32), 18)
        n = len(P)
        d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        zig = np.sign(np.sin(np.arange(n) * self.rng.uniform(0.9, 1.4))) * 0.5 + fbm1d(n, 4, 3, self._s())
        P = P + nrm * (zig * width * 1.6)[:, None] + nrm * fbm1d(n, 25, 3, self._s())[:, None] * width * 3
        taper = np.clip(np.minimum(np.arange(n) / (n * 0.2), (n - 1 - np.arange(n)) / (n * 0.35)), 0.1, 1)
        strokes = [(P, width * taper * (0.5 + 0.7 * (fbm1d(n, 8, 3, self._s()) * 0.5 + 0.5)))]
        for _ in range(branches):
            i = int(self.rng.integers(n // 4, n * 3 // 4))
            side = self.rng.choice([-1, 1]); ang = np.radians(self.rng.uniform(30, 60)) * side
            R = np.array([[np.cos(ang), -np.sin(ang)], [np.sin(ang), np.cos(ang)]])
            dd = R @ d[i]
            ln = self.rng.uniform(25, 60)
            B = [P[i], P[i] + dd * ln * 0.5 + self.rng.normal(0, 3, 2), P[i] + dd * ln]
            strokes.append(_open(B, [width * 0.6, width * 0.4, width * 0.15], 8))
        box = self._box(P, 20)
        m = self._raster(box, strokes=strokes)
        sl = self._sl(box)
        self.h[sl] -= blur(m, 0.7) * depth
        a = blur(m, 0.6)[..., None] * 0.85
        self.rock[sl] = self.rock[sl] * (1 - a) + hexc('#2a1f18') * a
        self.alb[sl] = self.alb[sl] * (1 - a) + hexc('#2a1f18') * a
        self._dirty()

    def floor(self, y=965, tilt=1.3, colour=FLOOR, wobble=14.0):
        """packed clay floor below a wavy wall-base line; tilted toward the viewer (height grows downward)"""
        H, W = self.H, self.W
        line = y + fbm1d(W, 260, 4, self._s()) * wobble
        self.floor_line = line.astype(np.float32)
        Y, X = self._grid()
        dy = Y - line[None, :]
        m = smoothstep(-1.5, 1.5, dy)
        rub = (noise2d(H, W, 26, 3, self._s()) - 0.5) * 4 + (noise2d(H, W, 6, 2, self._s()) - 0.5) * 1.2
        self.h += m * (tilt * np.clip(dy, 0, None) + rub)
        col = hexc(colour) * (0.75 + 0.45 * noise2d(H, W, 90, 4, self._s()))[..., None]
        pebble = smoothstep(0.72, 0.8, noise2d(H, W, 7, 2, self._s()))[..., None]
        col = col * (1 - 0.5 * pebble) + hexc('#9a8a76') * 0.5 * pebble
        damp = (smoothstep(-34, -2, dy) * (1 - m))[..., None]                    # splash line at the wall base
        a = m[..., None]
        self.rock = self.rock * (1 - a) + col * a
        self.rock *= 1 - 0.35 * damp
        self.alb = self.alb * (1 - a) + col * a
        self.alb *= 1 - 0.35 * damp
        self._floor_m = m.astype(np.float32)
        self._dirty()

    def floor_h(self, x, y):
        """floor height at (x, y), for putting things on the floor"""
        if self.floor_line is None: return 0.0
        xi = int(np.clip(x, 0, self.W - 1)); yi = int(np.clip(y, 0, self.H - 1))
        return float(self.h[yi, xi])

    # ------------------------------------------------------------------ props on the floor
    def _dome(self, box, m, height, power=0.85, sigma=None):
        sigma = sigma or max(2.0, min(box[2] - box[0], box[3] - box[1]) / 7)
        b = blur(m, sigma)
        return height * np.clip((b - 0.5) * 2, 0, 1) ** power * (m > 0.02)

    def stone(self, pts, colour='#7d6a58', height=12.0, rough=1.0, wet=0.0):
        """a slab or pebble lying on the floor (any closed outline)"""
        P = _closed(pts, 8)
        box = self._box(P, 10)
        m = self._raster(box, polys=[P])
        sl = self._sl(box)
        n = self._noise(box, 18, 3)
        self.h[sl] += self._dome(box, m, height) + m * (n - 0.5) * 3 * rough
        col = _c(colour) * (0.8 + 0.35 * self._noise(box, 30, 3))[..., None]
        a = blur(m, 0.6)[..., None]
        self.rock[sl] = self.rock[sl] * (1 - a) + col * a
        self.alb[sl] = self.alb[sl] * (1 - a) + col * a
        self.wet[sl] = np.maximum(self.wet[sl], m * wet)
        self._dirty()

    def heap(self, x, y, r, pigment='red', height=None, spill=1.0):
        """a little mound of ground pigment, with powder spilled round it"""
        height = height or r * 1.3
        box = self._box([(x - r * 2, y - r * 1.4), (x + r * 2, y + r)], 6)
        Y, X = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
        d = np.sqrt(((X - x) / r) ** 2 + ((Y - y) / (r * 0.55)) ** 2)
        d = d * (1 + 0.12 * (self._noise(box, 6, 2) - 0.5))
        cone = np.clip(1 - d, 0, 1) ** 1.25
        sl = self._sl(box)
        self.h[sl] += cone * height
        dust = np.clip(1.4 - d, 0, 1) * smoothstep(0.45, 0.75, self._noise(box, 4, 2)) * spill
        a = np.clip(smoothstep(0.0, 0.25, cone) + dust * 0.7, 0, 1)[..., None]
        col = _c(pigment) * (0.85 + 0.3 * self._noise(box, 3, 2))[..., None]
        self.rock[sl] = self.rock[sl] * (1 - a) + col * a
        self.alb[sl] = self.alb[sl] * (1 - a) + col * a
        self._dirty()

    def stick(self, p0, p1, width, colour='black', hollow=False, tip=None):
        """a cylinder lying on the floor: a charcoal stick, or a hollow bone blowpipe (hollow=True)"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        box = self._box([p0, p1], width * 2)
        Y, X = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
        d = p1 - p0; L = float(np.linalg.norm(d)); u = d / L
        t = np.clip(((X - p0[0]) * u[0] + (Y - p0[1]) * u[1]) / L, 0, 1)
        qx, qy = p0[0] + t * d[0] - X, p0[1] + t * d[1] - Y
        dist = np.sqrt(qx * qx + qy * qy) / (width / 2)
        cyl = np.sqrt(np.clip(1 - dist * dist, 0, 1))
        m = smoothstep(1.05, 0.9, dist)
        sl = self._sl(box)
        self.h[sl] = np.maximum(self.h[sl], self.h[sl] * (1 - m) + (self.h[sl] + cyl * width * 0.5) * m)
        col = _c(colour) * (0.85 + 0.25 * self._noise(box, 10, 2))[..., None]
        if colour in ('black', 'manganese'):                                  # charcoal: a faint satin sheen
            self.wet[sl] = np.maximum(self.wet[sl], m * 0.25)
        a = m[..., None]
        if tip is not None:                                                   # pigment stain at the far end
            ta = (smoothstep(0.75, 0.95, t) * m)[..., None]
            col = col * (1 - ta * 0.8) + _c(tip) * ta * 0.8
        self.rock[sl] = self.rock[sl] * (1 - a) + col * a
        self.alb[sl] = self.alb[sl] * (1 - a) + col * a
        if hollow:                                                            # the open end of the bone
            r = width * 0.26
            e = np.sqrt((X - p0[0]) ** 2 + (Y - p0[1]) ** 2)
            hole = smoothstep(r + 0.8, r - 0.8, e)
            self.h[sl] -= hole * width * 0.3
            self.alb[sl] *= (1 - 0.8 * hole)[..., None]
        self._dirty()

    # ------------------------------------------------------------------ fire and lamp
    def fire(self, x, y, size=220, power=1.6, reach=1150):
        """campfire on the floor at (x, y) (base of the flames): stones, ash, logs, flames, sparks, smoke + light"""
        r = self.rng
        # ash and charcoal on the floor
        box = self._box([(x - size * 0.9, y - size * 0.3), (x + size * 0.9, y + size * 0.3)], 6)
        Y, X = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
        d = np.sqrt(((X - x) / (size * 0.75)) ** 2 + ((Y - y) / (size * 0.2)) ** 2)
        ash = smoothstep(1.0, 0.55, d * (1 + 0.25 * (self._noise(box, 20, 3) - 0.5)))
        sl = self._sl(box)
        col = hexc('#5f5852') * (0.7 + 0.5 * self._noise(box, 5, 2))[..., None]
        a = (ash * 0.8)[..., None]
        self.rock[sl] = self.rock[sl] * (1 - a) + col * a
        self.alb[sl] = self.alb[sl] * (1 - a) + col * a
        # a ring of stones round the front and sides
        for k in range(16):
            ang = np.radians(-30 + k * 240 / 15 + r.uniform(-5, 5))
            sx, sy = x + np.cos(ang) * size * 0.66, y + np.sin(ang) * size * 0.19 + 8
            if sy > self.H + 10: continue
            rr = size * r.uniform(0.05, 0.08)
            wob = 1 + 0.25 * fbm1d(11, 4, 2, int(r.integers(1 << 30)))
            self.stone([(sx + np.cos(t) * rr * w_, sy + np.sin(t) * rr * 0.6 * w_)
                        for t, w_ in zip(np.linspace(0, 2 * np.pi, 11, endpoint=False), wob)],
                       colour=r.choice(['#4f443a', '#463c34', '#5a4c40']), height=rr * 0.9, rough=1.6)
        fz = self.floor_h(x, y)
        self.fires.append(dict(x=x, y=y, size=size, seed=self._s()))
        self.lights.append(dict(x=x, y=y - size * 0.42, z=fz + size * 0.45, col=FIRE, power=power, reach=reach,
                                wrap=0.2, shadow=True))
        self._fx = None; self._dirty()

    def lamp(self, x, y, size=120, power=0.5, reach=560):
        """a stone fat lamp on the floor (red sandstone bowl with a handle, glossy fat, a small flame)"""
        rx, ry = size * 0.42, size * 0.17
        P = [(x + np.cos(t) * rx, y + np.sin(t) * ry) for t in np.linspace(0, 2 * np.pi, 16, endpoint=False)]
        self.stone(P, colour='#8d4e34', height=size * 0.12, rough=0.5)
        self.stick((x + rx * 0.85, y + 2), (x + rx * 1.75, y + ry * 0.55), size * 0.17, colour='#7f452e')
        box = self._box([(x - rx, y - ry), (x + rx, y + ry)], 4)
        Y, X = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
        d = np.sqrt(((X - x + rx * 0.05) / (rx * 0.66)) ** 2 + ((Y - y + ry * 0.12) / (ry * 0.58)) ** 2)
        pool = smoothstep(1.0, 0.85, d)
        sl = self._sl(box)
        self.h[sl] -= pool * size * 0.06
        col = hexc('#4a2c12') * (0.85 + 0.3 * self._noise(box, 8, 2))[..., None]
        a = pool[..., None]
        self.alb[sl] = self.alb[sl] * (1 - a) + col * a
        self.wet[sl] = np.maximum(self.wet[sl], pool * 0.9)
        wx, wy = x - rx * 0.42, y - ry * 0.15
        self.stick((wx - size * 0.05, wy + 3), (wx + size * 0.06, wy - 1), size * 0.05, colour='#2b2018')
        fz = self.floor_h(x, y)
        self.lamps.append(dict(x=wx, y=wy, size=size, seed=self._s()))
        self.lights.append(dict(x=wx, y=wy - size * 0.3, z=fz + size * 0.32, col=LAMPLIGHT, power=power, reach=reach,
                                wrap=0.4, shadow=False))
        self._fx = None; self._dirty()

    # ------------------------------------------------------------------ figures (drafted in a unit frame)
    def _T(self, x, y, s, facing=1, rot=0.0):
        a = np.radians(rot); c, sn = np.cos(a), np.sin(a)

        def T(P):
            P = np.asarray(P, np.float32).reshape(-1, 2) * s
            u = P[:, 0] * facing; v = P[:, 1]
            return np.stack([x + u * c + v * sn, y - u * sn + v * c], 1)
        return T

    def _build(self, kind, T, s, polys=(), strokes=(), regions=(), discs=(), pad=80):
        """polys: [(part, unit pts)], strokes: [(part, unit pts, unit widths)], regions: [(name, unit polygon)]"""
        allp = [T(P) for _, P in polys] + [T(P) for _, P, _ in strokes]
        box = self._box(np.vstack(allp), pad)
        fig = Figure(box, kind)
        for part, P in polys:
            fig.add(part, self._raster(box, polys=[_closed(T(P), 8)]))
        for part, P, w in strokes:
            S, ww = _open(T(P), np.asarray(w, np.float32) * s, 10)
            fig.add(part, self._raster(box, strokes=[(S, ww)]))
        for part, P, r in discs:
            p = T([P])[0]
            fig.add(part, self._raster(box, discs=[(p[0], p[1], r * s)]))
        body = fig.mask('body')
        if 'legs' in fig.parts:                                    # legs = the part below / outside the body
            fig.parts['legs'] = fig.parts['legs'] * (1 - smoothstep(0.3, 1.0, blur(body, 2.0)))
        for name, P in regions:
            fig.add(name, self._raster(box, polys=[T(P)]) * body)
        return fig

    def shape(self, x, y, size, polys=(), strokes=(), regions=(), facing=1, rot=0.0, kind='shape'):
        """any figure from unit-frame outlines and strokes (see bison / horse for the format)"""
        return self._build(kind, self._T(x, y, size, facing, rot), size, polys, strokes, regions)

    def bison(self, x, y, size, facing=1, rot=0.0, head_drop=0.0):
        """steppe bison in profile: great hump, small low head, short horns, beard, short legs.
        (x, y) = body centre, size = body length (rump to chest) px"""
        hd = head_drop
        body = [(-0.50, -0.08), (-0.42, -0.16), (-0.25, -0.20), (-0.05, -0.27), (0.06, -0.40), (0.18, -0.50),
                (0.30, -0.47), (0.40, -0.36), (0.47, -0.22 + hd * 0.4), (0.53, -0.08 + hd), (0.58, 0.05 + hd),
                (0.61, 0.13 + hd), (0.56, 0.18 + hd), (0.49, 0.16 + hd * 0.6), (0.45, 0.26 + hd * 0.4), (0.39, 0.34),
                (0.33, 0.28), (0.24, 0.29), (0.08, 0.26), (-0.12, 0.22), (-0.30, 0.17), (-0.44, 0.12), (-0.53, 0.02)]
        legs = [((0.28, 0.24), (0.31, 0.42), (0.29, 0.57), [0.10, 0.05, 0.04]),
                ((0.17, 0.25), (0.15, 0.42), (0.11, 0.56), [0.085, 0.045, 0.036]),
                ((-0.40, 0.10), (-0.35, 0.34), (-0.40, 0.56), [0.13, 0.045, 0.036]),
                ((-0.30, 0.15), (-0.24, 0.36), (-0.27, 0.55), [0.10, 0.042, 0.034])]
        strokes = [('legs', [a, b, c], w) for a, b, c, w in legs]
        strokes += [('legs', [(c[0] - 0.012, c[1] - 0.012), (c[0] + 0.028, c[1] + 0.006)], [w[2] * 1.3, w[2] * 1.2])
                    for a, b, c, w in legs]                                          # hooves
        strokes += [('horns', [(0.465, -0.21 + hd * 0.4), (0.53, -0.27 + hd * 0.4), (0.575, -0.36 + hd * 0.4), (0.56, -0.42 + hd * 0.4)], [0.04, 0.03, 0.018, 0.008]),
                    ('horns', [(0.41, -0.29 + hd * 0.3), (0.425, -0.38 + hd * 0.3), (0.465, -0.44 + hd * 0.3)], [0.034, 0.02, 0.008]),
                    ('tail', [(-0.515, -0.06), (-0.575, 0.06), (-0.58, 0.20)], [0.024, 0.018, 0.016]),
                    ('tail', [(-0.58, 0.19), (-0.592, 0.25), (-0.585, 0.31)], [0.03, 0.045, 0.012])]   # tuft
        discs = []
        regions = [('head', [(0.36, -0.60), (0.80, -0.60), (0.80, 0.50), (0.43, 0.50), (0.41, 0.10)]),
                   ('hump', [(-0.04, -0.70), (0.42, -0.70), (0.42, -0.20), (0.28, -0.25), (0.10, -0.25), (-0.04, -0.23)]),
                   ('belly', [(-0.46, 0.08), (-0.25, 0.08), (0.00, 0.14), (0.22, 0.17), (0.34, 0.22), (0.34, 0.50), (-0.55, 0.50)]),
                   ('back', [(-0.60, -0.60), (0.10, -0.60), (0.10, -0.17), (-0.20, -0.12), (-0.60, -0.03)]),
                   ('front', [(0.10, -0.70), (0.80, -0.70), (0.80, 0.60), (0.10, 0.60)])]
        fig = self._build('bison', self._T(x, y, size, facing, rot), size, [('body', body)], strokes, regions, discs)
        T = self._T(x, y, size, facing, rot)
        fig.anchors = {k: T([p])[0] for k, p in dict(eye=(0.505, -0.06 + hd * 0.8), nostril=(0.585, 0.07 + hd),
                                                       shoulder=(0.18, -0.05), flank=(-0.12, 0.02),
                                                       beard=(0.40, 0.24)).items()}
        fig.size, fig.facing = size, facing
        return fig

    def horse(self, x, y, size, facing=1, rot=0.0, gait='run'):
        """small-headed Ice-Age horse with a heavy belly and an upright mane; gait 'run', 'gallop' (flying) or 'stand'"""
        body = [(-0.50, -0.14), (-0.30, -0.20), (-0.05, -0.21), (0.18, -0.25), (0.30, -0.34), (0.40, -0.45),
                (0.46, -0.52), (0.51, -0.50), (0.58, -0.41), (0.655, -0.31), (0.675, -0.25), (0.635, -0.205),
                (0.56, -0.215), (0.495, -0.245), (0.44, -0.17), (0.42, -0.05), (0.40, 0.08), (0.30, 0.17),
                (0.10, 0.24), (-0.12, 0.25), (-0.30, 0.20), (-0.44, 0.11), (-0.54, -0.02)]
        if gait == 'gallop':
            legs = [((0.32, 0.10), (0.48, 0.26), (0.63, 0.30), [0.10, 0.05, 0.034]),
                    ((0.25, 0.13), (0.39, 0.30), (0.35, 0.45), [0.09, 0.046, 0.032]),
                    ((-0.40, 0.08), (-0.58, 0.24), (-0.76, 0.29), [0.13, 0.05, 0.034]),
                    ((-0.33, 0.12), (-0.45, 0.32), (-0.60, 0.42), [0.11, 0.046, 0.032])]
        elif gait == 'run':
            legs = [((0.32, 0.10), (0.45, 0.27), (0.52, 0.44), [0.10, 0.05, 0.034]),
                    ((0.25, 0.13), (0.24, 0.31), (0.13, 0.41), [0.09, 0.046, 0.032]),
                    ((-0.40, 0.08), (-0.50, 0.28), (-0.64, 0.41), [0.13, 0.05, 0.034]),
                    ((-0.32, 0.12), (-0.22, 0.30), (-0.19, 0.46), [0.11, 0.046, 0.032])]
        else:
            legs = [((0.30, 0.12), (0.32, 0.33), (0.30, 0.50), [0.10, 0.05, 0.034]),
                    ((0.21, 0.15), (0.20, 0.34), (0.19, 0.50), [0.09, 0.046, 0.032]),
                    ((-0.38, 0.10), (-0.33, 0.31), (-0.38, 0.50), [0.13, 0.05, 0.034]),
                    ((-0.29, 0.14), (-0.24, 0.33), (-0.27, 0.50), [0.11, 0.046, 0.032])]
        strokes = [('legs', [a, b, c], w) for a, b, c, w in legs]
        strokes += [('legs', [c, (c[0] + 0.02, c[1] + 0.012)], [w[2] * 1.35, w[2] * 1.2]) for a, b, c, w in legs]
        strokes += [('ears', [(0.455, -0.50), (0.44, -0.585)], [0.04, 0.012]),
                    ('mane', [(0.15, -0.255), (0.265, -0.345), (0.375, -0.46), (0.445, -0.535)], [0.05, 0.075, 0.07, 0.045]),
                    ('tail', [(-0.52, -0.11), (-0.66, -0.05), (-0.80, 0.08), (-0.86, 0.18)] if gait != 'stand'
                     else [(-0.52, -0.11), (-0.60, 0.02), (-0.62, 0.20), (-0.60, 0.32)], [0.06, 0.065, 0.045, 0.02])]
        regions = [('head', [(0.42, -0.70), (0.80, -0.70), (0.80, 0.10), (0.46, 0.10), (0.43, -0.12)]),
                   ('belly', [(-0.46, 0.07), (-0.30, 0.04), (-0.05, 0.10), (0.20, 0.07), (0.38, 0.02), (0.40, 0.50), (-0.55, 0.50)]),
                   ('back', [(-0.60, -0.60), (0.20, -0.60), (0.20, -0.17), (-0.10, -0.13), (-0.40, -0.09), (-0.60, -0.05)]),
                   ('front', [(0.20, -0.80), (0.90, -0.80), (0.90, 0.60), (0.20, 0.60)])]
        fig = self._build('horse', self._T(x, y, size, facing, rot), size, [('body', body)], strokes, regions)
        T = self._T(x, y, size, facing, rot)
        fig.anchors = {k: T([p])[0] for k, p in dict(eye=(0.525, -0.425), nostril=(0.655, -0.27), mouth=(0.64, -0.225),
                                                       shoulder=(0.25, -0.05), flank=(-0.15, 0.0)).items()}
        fig.size, fig.facing = size, facing
        return fig

    def deer(self, x, y, size, facing=1, rot=0.0, kind='stag', gait='leap'):
        """red deer: kind 'stag' (antlers) or 'hind' (big ears); gait 'leap' or 'stand'"""
        body = [(-0.48, -0.10), (-0.30, -0.15), (-0.05, -0.16), (0.18, -0.19), (0.30, -0.30), (0.40, -0.46),
                (0.46, -0.575), (0.52, -0.60), (0.62, -0.565), (0.72, -0.505), (0.715, -0.465), (0.63, -0.45),
                (0.55, -0.455), (0.49, -0.41), (0.42, -0.22), (0.37, -0.02), (0.25, 0.09), (0.02, 0.13),
                (-0.24, 0.11), (-0.40, 0.06), (-0.50, -0.02)]
        if gait == 'leap':
            legs = [((0.28, 0.05), (0.47, 0.17), (0.53, 0.37), [0.09, 0.04, 0.026]),
                    ((0.23, 0.07), (0.41, 0.24), (0.42, 0.41), [0.08, 0.036, 0.024]),
                    ((-0.40, 0.03), (-0.62, 0.20), (-0.89, 0.30), [0.12, 0.04, 0.026]),
                    ((-0.35, 0.06), (-0.55, 0.27), (-0.79, 0.41), [0.10, 0.038, 0.024])]
        else:
            legs = [((0.27, 0.06), (0.30, 0.30), (0.28, 0.52), [0.085, 0.035, 0.022]),
                    ((0.19, 0.09), (0.18, 0.31), (0.17, 0.52), [0.075, 0.032, 0.02]),
                    ((-0.38, 0.04), (-0.31, 0.29), (-0.37, 0.52), [0.11, 0.036, 0.022]),
                    ((-0.30, 0.07), (-0.24, 0.31), (-0.27, 0.52), [0.095, 0.034, 0.02])]
        strokes = [('legs', [a, b, c], w) for a, b, c, w in legs]
        strokes += [('tail', [(-0.48, -0.10), (-0.555, -0.135)], [0.035, 0.02])]
        ear = 0.05 if kind == 'stag' else 0.075
        strokes += [('ears', [(0.475, -0.58), (0.43, -0.64), (0.39, -0.67)], [ear * 0.7, ear, 0.012])]
        if kind == 'stag':
            for dx, dy, sc in ((0.0, 0.0, 1.0), (-0.06, 0.02, 0.9)):
                beam = [(0.50 + dx, -0.60 + dy), (0.44 + dx, -0.80 * sc + dy), (0.32 + dx, -0.98 * sc + dy),
                        (0.22 + dx, -1.12 * sc + dy), (0.20 + dx, -1.28 * sc + dy)]
                strokes.append(('antlers', beam, [0.04, 0.034, 0.028, 0.022, 0.012]))
                for (bx, by), (tx, ty) in (((0.49, -0.66), (0.63, -0.75)), ((0.44, -0.80), (0.57, -0.93)),
                                           ((0.33, -0.97), (0.43, -1.13)), ((0.22, -1.13), (0.10, -1.24)),
                                           ((0.21, -1.25), (0.29, -1.38))):
                    strokes.append(('antlers', [(bx + dx, by * sc + dy), ((bx + tx) / 2 + dx + 0.012, (by + ty) / 2 * sc + dy - 0.012),
                                                (tx + dx, ty * sc + dy)], [0.026, 0.019, 0.009]))
        regions = [('head', [(0.42, -0.80), (0.90, -0.80), (0.90, -0.30), (0.46, -0.30)]),
                   ('belly', [(-0.45, 0.03), (-0.20, 0.03), (0.10, 0.06), (0.32, 0.0), (0.40, 0.50), (-0.55, 0.50)]),
                   ('back', [(-0.60, -0.60), (0.25, -0.60), (0.25, -0.13), (-0.60, -0.04)]),
                   ('front', [(0.25, -0.90), (0.90, -0.90), (0.90, 0.60), (0.25, 0.60)])]
        fig = self._build('deer', self._T(x, y, size, facing, rot), size, [('body', body)], strokes, regions)
        T = self._T(x, y, size, facing, rot)
        fig.anchors = {k: T([p])[0] for k, p in dict(eye=(0.565, -0.535), nostril=(0.705, -0.495),
                                                       shoulder=(0.22, -0.05), flank=(-0.12, 0.0)).items()}
        fig.size, fig.facing = size, facing
        return fig

    def hunter(self, x, y, size, facing=1, rot=0.0, pose='throw'):
        """a running hunter in the red Levantine manner: triangular torso, long legs; pose 'throw' (spear raised
        back over the shoulder) or 'run' (spear held level). (x, y) = feet, size = height. The spear is separate:
        fig.anchors['grip'] and ['spear_dir'] say where it goes."""
        if pose == 'throw':
            P = dict(head=(0.06, -0.90), neck=(0.04, -0.82), sh=(0.02, -0.76), hip=(-0.04, -0.44),
                     arm_b=[(0.0, -0.75), (-0.13, -0.82), (-0.20, -0.95)], arm_f=[(0.04, -0.74), (0.18, -0.70), (0.30, -0.72)],
                     leg_f=[(-0.02, -0.44), (0.14, -0.26), (0.20, -0.02)], leg_b=[(-0.06, -0.44), (-0.16, -0.24), (-0.34, -0.10)],
                     grip=(-0.20, -0.95), sdir=(0.95, -0.30))
        else:
            P = dict(head=(0.12, -0.88), neck=(0.09, -0.80), sh=(0.07, -0.75), hip=(-0.04, -0.44),
                     arm_b=[(0.05, -0.74), (-0.08, -0.62), (-0.18, -0.58)], arm_f=[(0.08, -0.73), (0.16, -0.62), (0.26, -0.60)],
                     leg_f=[(-0.02, -0.44), (0.18, -0.30), (0.26, -0.06)], leg_b=[(-0.06, -0.44), (-0.18, -0.22), (-0.38, -0.16)],
                     grip=(0.10, -0.60), sdir=(1.0, -0.02))
        sh, hip = P['sh'], P['hip']
        torso = [(sh[0] - 0.075, sh[1] - 0.01), (sh[0] + 0.075, sh[1] + 0.01), (hip[0] + 0.03, hip[1]), (hip[0] - 0.03, hip[1])]
        strokes = [('body', [P['neck'], sh], [0.05, 0.06]),
                   ('body', P['arm_b'], [0.04, 0.03, 0.025]), ('body', P['arm_f'], [0.04, 0.03, 0.025]),
                   ('body', P['leg_f'], [0.055, 0.04, 0.022]), ('body', P['leg_b'], [0.055, 0.04, 0.022]),
                   ('body', [(hip[0] - 0.035, hip[1] - 0.02), (hip[0] + 0.035, hip[1] + 0.02)], [0.07, 0.07])]
        T = self._T(x, y, size, facing, rot)
        fig = self._build('hunter', T, size, [('body', torso)], strokes, discs=[('body', P['head'], 0.065)], pad=60)
        a = np.radians(rot)
        sd = np.array([P['sdir'][0] * facing, P['sdir'][1]], np.float32)
        sd = np.array([sd[0] * np.cos(a) + sd[1] * np.sin(a), -sd[0] * np.sin(a) + sd[1] * np.cos(a)])
        fig.anchors = dict(grip=T([P['grip']])[0], spear_dir=sd / np.linalg.norm(sd), head=T([P['head']])[0])
        fig.size, fig.facing = size, facing
        return fig

    def spear(self, p0, p1, width=4.0, point=1.0):
        """a spear from butt p0 to tip p1 with a leaf-shaped point (Figure with parts 'shaft' and 'point')"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        d = p1 - p0; L = float(np.linalg.norm(d)); u = d / L; n = np.array([-u[1], u[0]])
        pl = width * 7 * point
        box = self._box([p0, p1], 40)
        fig = Figure(box, 'spear')
        sway = n * L * 0.01
        S, w = _open([p0, (p0 + p1) / 2 + sway, p1 - u * pl * 0.8], [width * 0.8, width, width * 0.9], 10)
        fig.add('shaft', self._raster(box, strokes=[(S, w)]))
        b = p1 - u * pl
        leaf = [p1, b + u * pl * 0.45 + n * width * 1.5, b + n * width * 0.5, b - n * width * 0.5, b + u * pl * 0.45 - n * width * 1.5]
        fig.add('point', self._raster(box, polys=[leaf]))
        return fig

    def hand(self, x, y, size, rot=0.0, side='left', spread=1.0, fold=(), arm=0.3):
        """a hand flat on the wall, fingers up (rot turns it). (x, y) = wrist, size = wrist to middle fingertip.
        fold: fingers bent down out of sight (0 thumb .. 4 little) -- the short-finger stencils of the old caves"""
        f = 1 if side == 'right' else -1
        palm = [(-0.20, 0.0), (-0.225, -0.22), (-0.205, -0.45), (-0.10, -0.50), (0.02, -0.52), (0.13, -0.50),
                (0.205, -0.44), (0.225, -0.24), (0.19, -0.04)]
        fingers = [((0.13, -0.47), 9, 0.40, 0.088), ((0.035, -0.51), 1, 0.46, 0.094),
                   ((-0.06, -0.49), -6, 0.41, 0.09), ((-0.15, -0.43), -15, 0.31, 0.082)]
        strokes = []
        for i, ((bx, by), ang, ln, w) in enumerate(fingers):
            if (i + 1) in fold: ln *= 0.32
            a = np.radians(ang * spread)
            tip = (bx + np.sin(a) * ln, by - np.cos(a) * ln)
            mid = (bx + np.sin(a) * ln * 0.5, by - np.cos(a) * ln * 0.5)
            strokes.append(('hand', [(bx, by + 0.04), mid, tip], [w * 1.05, w * 0.95, w * 0.82]))
        tl = 0.36 * (0.35 if 0 in fold else 1)
        ta = np.radians(48 * spread)
        strokes.append(('hand', [(0.15, -0.12), (0.15 + np.sin(ta) * tl * 0.55, -0.16 - np.cos(ta) * tl * 0.5),
                                 (0.15 + np.sin(ta) * tl, -0.18 - np.cos(ta) * tl * 0.85)], [0.13, 0.11, 0.085]))
        if arm:
            strokes.append(('arm', [(0.0, -0.05), (0.01, arm * 0.5), (0.02, arm)], [0.36, 0.38, 0.42]))
        T = self._T(x, y, size, f, rot)
        return self._build('hand', T, size, [('hand', palm)], strokes, pad=100)

    # ------------------------------------------------------------------ painting
    def sketch(self, target, pigment='black', width=2.6, passes=2, strength=0.7, wander=3.0):
        """charcoal searching lines round the silhouette (each pass on a slightly wandering contour)"""
        box, m = self._target(target)
        h, w = m.shape
        for k in range(passes):
            dx = (self._noise(box, 60, 2) - 0.5) * 2 * wander
            dy = (self._noise(box, 60, 2) - 0.5) * 2 * wander
            Y, X = np.mgrid[0:h, 0:w]
            mw = m[np.clip(Y + dy, 0, h - 1).astype(np.int32), np.clip(X + dx, 0, w - 1).astype(np.int32)]
            mw = blur(mw, max(0.8, width * 0.55))
            band = smoothstep(0.12, 0.5, mw) * smoothstep(0.88, 0.5, mw)              # a line about `width` wide
            press = 0.45 + 0.45 * self._noise(box, 50, 2)
            cov = band * self._catch(box, press) * strength * (0.75 if k else 1.0)
            cov *= smoothstep(0.15, 0.28, self._noise(box, 35, 2))                    # lifts between strokes
            self._deposit(box, cov, pigment)

    def line(self, pts, width, pigment='black', end_width=None, kind='charcoal', strength=0.95, smooth=True):
        """a stroke: kind 'charcoal' (dry stick, breaks up in the hollows), 'finger' (wet paint, soft edges) or
        'brush' (fur brush, even)"""
        P = np.asarray(pts, np.float32)
        w = [width, end_width if end_width is not None else width]
        if smooth and len(P) > 2:
            S, ww = _open(P, np.interp(np.linspace(0, 1, len(P)), [0, 1], w), 10)
        else:
            S = P if len(P) > 1 else P
            ww = np.interp(np.linspace(0, 1, len(S)), [0, 1], w)
        box = self._box(S, width * 2 + 12)
        m = self._raster(box, strokes=[(S, ww)])
        self._stroke_paint(box, m, pigment, kind, strength)
        return Sel(box, m)

    def _stroke_paint(self, box, m, pigment, kind, strength):
        if kind == 'charcoal':
            cov = blur(m, 0.7) * self._catch(box, 0.75) * strength
        elif kind == 'finger':
            mm = blur(m, 1.4)
            cov = mm * (0.72 + 0.28 * self._catch(box, 0.85)) * (0.85 + 0.15 * self._noise(box, 8, 2)) * strength
        else:
            cov = blur(m, 0.9) * (0.85 + 0.15 * self._catch(box, 0.9)) * strength
        self._deposit(box, cov, pigment)

    def paint(self, target, pigment='black', kind='finger', strength=0.95):
        """paint a drafted shape (e.g. a hunter or a spear Figure) solid with a finger / stick / brush"""
        box, m = self._target(target)
        self._stroke_paint(box, m, pigment, kind, strength)

    def blow(self, target, pigment, density=0.85, edge=2.5, halo=16.0, halo_amt=0.18, speckle=1.0, mottle=0.25,
             rim=0.0, gradient=0.0, relief=0.0, clip=None, exclude=None, soft_clip=2.0):
        """pigment spat / blown through a bone tube: soft edge, halo, droplet speckle, uneven density.
        rim: denser toward the outline; gradient: darker on top (back); relief: heavier where the wall turns away
        from the fire; clip: keep inside another Figure/Sel; exclude: leave a region (e.g. a pale belly)"""
        box, m = self._target(target)
        core = blur(m, edge)
        cov = core * density
        if rim:
            inner = blur(m, max(6.0, (box[2] - box[0]) / 22))
            cov *= 1 - rim * smoothstep(0.55, 1.0, inner)
        if gradient:
            rows = np.where(m.max(1) > 0.5)[0]
            if len(rows):
                t = np.clip((np.arange(m.shape[0], dtype=np.float32) - rows[0]) / max(1, rows[-1] - rows[0]), 0, 1)
                cov *= (1 - gradient * t ** 1.2)[:, None]
        if relief:
            _, gx, gy = self._auxiliary()
            sl = self._sl(box)
            L = self.lights[0] if self.lights else dict(x=self.W * 0.2, y=self.H)
            Y, X = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
            lx, ly = L['x'] - X, L['y'] - Y
            ll = np.sqrt(lx * lx + ly * ly) + 1e-3
            facing = (-gx[sl] * lx - gy[sl] * ly) / ll                  # >0 turned toward the fire
            cov *= 1 - relief + relief * smoothstep(0.25, -0.35, facing)
        if exclude is not None:
            cov *= 1 - blur(self._local(exclude, box), 5.0)
        cov *= 1 - mottle + mottle * self._noise(box, 22, 3) * 1.2
        hal = blur(m, halo)
        cov = cov + halo_amt * hal * (1 - core) * density
        if speckle:
            cov = np.maximum(cov, self._speckle(box, hal * (1 - core), speckle) * density)
        if clip is not None:
            cov *= np.clip(blur(self._local(clip, box), soft_clip) * 1.15, 0, 1)
        self._deposit(box, np.clip(cov, 0, 1), pigment)

    def _speckle(self, box, field, amount):
        """droplets of a blown spray: sparse little discs where the halo thins out"""
        h, w = field.shape
        r = self.rng
        n = int(h * w * 0.004 * amount)
        xs, ys = r.uniform(0, w, n), r.uniform(0, h, n)
        p = field[ys.astype(int), xs.astype(int)]
        keep = r.random(n) < np.clip(p * 2.2, 0, 1) * (p > 0.02)
        im = Image.new('L', (w * 2, h * 2), 0)
        d = ImageDraw.Draw(im)
        for x, y, rad, v in zip(xs[keep], ys[keep], r.uniform(0.5, 2.0, keep.sum()), r.uniform(0.45, 0.95, keep.sum())):
            d.ellipse([(x - rad) * 2, (y - rad) * 2, (x + rad) * 2, (y + rad) * 2], fill=int(255 * v))
        return np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255

    def daub(self, target, pigment, density=0.8, blotch=0.4, press=0.6):
        """a fur pad dabbed on: blotchy, more pigment on the rock's high points"""
        box, m = self._target(target)
        n = self._noise(box, 11, 3)
        cov = blur(m, 1.4) * density * (1 - blotch + blotch * n * 1.3) * (0.6 + 0.4 * self._catch(box, press))
        self._deposit(box, np.clip(cov, 0, 1), pigment)

    @staticmethod
    def _inside_dist(m, K):
        """chamfer distance from the outline inward (px), up to K"""
        cur = m > 0.5
        d = np.zeros(m.shape, np.float32)
        for k in range(int(K)):
            d += cur
            e = cur.copy()
            e[1:] &= cur[:-1]; e[:-1] &= cur[1:]; e[:, 1:] &= cur[:, :-1]; e[:, :-1] &= cur[:, 1:]
            if k % 2:
                e[1:, 1:] &= cur[:-1, :-1]; e[:-1, :-1] &= cur[1:, 1:]; e[1:, :-1] &= cur[:-1, 1:]; e[:-1, 1:] &= cur[1:, :-1]
            cur = e
            if not cur.any(): break
        return d

    def outline(self, target, pigment='black', width=6.0, var=0.45, top=0.7, gaps=0.12, kind='charcoal',
                strength=0.95, parts=None):
        """the finished contour: a band inside the silhouette, thicker on top edges / the back, thinner on the
        belly, with gaps where the stick skipped; kind 'charcoal' or 'blow' (sprayed, soft)"""
        if isinstance(target, Figure) and parts:
            target = target.sel(*parts)
        box, m = self._target(target)
        d = self._inside_dist(m, width * 2.6 + 2)
        mb = blur(m, 3.0)
        gy = np.gradient(mb, axis=0)
        up = smoothstep(-0.02, 0.06, gy)                         # top edges (mask grows downward)
        wv = width * (0.62 + var * 1.1 * self._noise(box, 45, 2)) * (1 - top * 0.45 + top * 0.9 * up)
        band = smoothstep(wv + 1.0, wv - 1.0, d) * (m > 0.5)
        band = np.maximum(band, smoothstep(0.15, 0.5, m) * (m <= 0.5))      # antialiased outer edge
        if gaps:
            band *= smoothstep(gaps - 0.04, gaps + 0.06, self._noise(box, 28, 2))
        if kind == 'blow':
            cov = np.clip(blur(band, 1.6) * 1.2, 0, 1) * strength
            cov = np.maximum(cov, self._speckle(box, blur(band, 6) * 0.5, 0.5) * strength)
        else:
            cov = blur(band, 0.7) * (0.5 + 0.5 * self._catch(box, 0.9)) * strength
        self._deposit(box, cov, pigment)

    def dots(self, pts, r=14.0, pigment='red', press=0.8, strength=0.92):
        """palm / fingertip dots"""
        polys = []
        for i, (x, y) in enumerate(pts):
            rr = r * self.rng.uniform(0.85, 1.12)
            polys.append(_closed([(x + np.cos(t) * rr * (1 + 0.12 * self.rng.normal()), y + np.sin(t) * rr * 0.9 * (1 + 0.12 * self.rng.normal()))
                                  for t in np.linspace(0, 2 * np.pi, 9, endpoint=False)], 6))
        box = self._box(np.vstack(polys), 10)
        m = self._raster(box, polys=polys)
        cov = blur(m, 1.3) * (0.62 + 0.38 * self._catch(box, press)) * (0.85 + 0.15 * self._noise(box, 6, 2)) * strength
        self._deposit(box, cov, pigment)

    def stencil(self, hand, pigment='red', density=0.9, spread=34.0, puffs=11, speckle=1.0):
        """negative hand: pigment blown round a hand pressed on the wall, in several puffs aimed at the fingertips
        and sides -> a bare-rock hand inside a soft, uneven sprayed halo"""
        box = hand.box
        hm = hand.mask('hand'); am = hand.mask('arm')
        h, w = hm.shape
        r = self.rng
        thick = np.clip(blur(np.maximum(hm, am * 0.3), 6) * 4, 0, 1)
        edge = np.argwhere((thick > 0.3) & (thick < 0.7))
        cloud = np.zeros((h, w), np.float32)
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
        top = edge[edge[:, 0] < np.percentile(edge[:, 0], 70)] if len(edge) else edge
        for k in range(puffs):
            src = top if (k % 3 and len(top)) else edge
            if not len(src): break
            cy, cx = src[r.integers(len(src))]
            sg = spread * r.uniform(0.6, 1.25)
            cloud += r.uniform(0.55, 1.0) * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (2 * sg * sg))
        cloud += 0.5 * thick                                              # the hand's own edge always gets some
        cloud = blur(cloud, 3) * (0.75 + 0.5 * self._noise(box, 20, 3))
        cov = density * (1 - np.exp(-1.8 * cloud))
        hard = blur(np.maximum(hm, am * 0.55), 0.9)
        cov *= 1 - hard
        fringe = np.clip(cloud, 0, 1) * (1 - np.clip(cloud * 2.5, 0, 1))
        cov = np.maximum(cov, self._speckle(box, fringe * 1.4, speckle) * density * (1 - hard))
        self._deposit(box, np.clip(cov, 0, 1), pigment)

    def handprint(self, hand, pigment='red', press=0.65, strength=0.9):
        """positive hand: a painted palm pressed on -- only the high points take the paint"""
        box = hand.box
        m = blur(hand.mask('hand'), 1.0)
        cov = m * self._catch(box, press) * strength * (0.8 + 0.2 * self._noise(box, 5, 2))
        self._deposit(box, cov, pigment)

    # ------------------------------------------------------------------ time
    def calcite(self, x, y, rx, ry, amount=0.45, rot=0.0, popcorn=0.6):
        """a milky calcite veil grown over part of the wall (and whatever is painted there)"""
        P = [(x + np.cos(t) * rx, y + np.sin(t) * ry) for t in np.linspace(0, 2 * np.pi, 40, endpoint=False)]
        a_ = np.radians(rot)
        P = [(x + (px - x) * np.cos(a_) + (py - y) * np.sin(a_), y - (px - x) * np.sin(a_) + (py - y) * np.cos(a_)) for px, py in P]
        box = self._box(P, 20)
        m = self._raster(box, polys=[P], ss=1)
        m = blur(m, min(rx, ry) * 0.35) * (0.45 + 0.75 * self._noise(box, 40, 4))
        m = np.clip(m, 0, 1)
        sl = self._sl(box)
        nod = smoothstep(0.62, 0.8, self._noise(box, 5, 2)) * smoothstep(0.25, 0.6, m)
        self.h[sl] += nod * 0.7 * popcorn + m * 0.8
        a = (m * amount)[..., None]
        self.alb[sl] = self.alb[sl] * (1 - a) + hexc('#f2ebe0') * a
        self.alb[sl] = self.alb[sl] * (1 - 0.25 * nod[..., None] * popcorn) + hexc('#f1eadf') * 0.25 * nod[..., None] * popcorn
        self.wet[sl] = np.maximum(self.wet[sl], m * 0.35)
        self._dirty()

    def flake(self, n=40, size=(1.5, 4.0), box=None, min_load=0.5):
        """paint lost in small flakes (only where there is paint), showing the fresher rock underneath"""
        r = self.rng
        x0, y0, x1, y1 = box or (0, 0, self.W, self.H)
        cand = np.argwhere(self.load[y0:y1, x0:x1] > min_load)
        if not len(cand): return
        pick = cand[r.integers(0, len(cand), n)]
        im = Image.new('L', (self.W, self.H), 0)
        d = ImageDraw.Draw(im)
        for yy, xx in pick:
            cx, cy = xx + x0, yy + y0
            rr = r.uniform(*size)
            k = 12
            wob = 1 + 0.22 * fbm1d(k, 4, 2, int(r.integers(1 << 30)))
            pts = [(cx + np.cos(t) * rr * w_, cy + np.sin(t) * rr * w_ * 0.8) for t, w_ in
                   zip(np.linspace(0, 2 * np.pi, k, endpoint=False) + r.uniform(0, 6.3), wob)]
            d.polygon(pts, fill=255)
        m = blur(np.asarray(im, np.float32) / 255, 0.7)
        a = m[..., None]
        self.alb = self.alb * (1 - a * 0.85) + self.rock * 0.93 * a * 0.85
        self.load *= 1 - m
        self.h -= m * 0.3
        self._dirty()

    def claws(self, x, y, angle=-75.0, n=4, length=170.0, spread=20.0, depth=3.2, width=6.0, curve=0.12):
        """a cave bear's claw marks: n parallel grooves scratched into the soft surface, pale and fresh"""
        a = np.radians(angle)
        u = np.array([np.cos(a), -np.sin(a)]); nv = np.array([-u[1], u[0]])
        strokes = []
        for i in range(n):
            o = (i - (n - 1) / 2) * spread
            L = length * self.rng.uniform(0.75, 1.05)
            p0 = np.array([x, y]) + nv * o + u * self.rng.uniform(-8, 8)
            P = [p0, p0 + u * L * 0.5 + nv * (L * curve + o * 0.15), p0 + u * L + nv * (L * curve * 0.6 + o * 0.3)]
            strokes.append(_open(P, [width * 0.4, width, width * 0.25], 12))
        box = self._box(np.vstack([s for s, _ in strokes]), 16)
        m = self._raster(box, strokes=strokes)
        sl = self._sl(box)
        mb = blur(m, 1.0)
        rim = np.clip(blur(m, 2.6) - mb, 0, 1)
        self.h[sl] += -mb * depth + rim * depth * 0.6
        fresh = np.clip(self.rock[sl] * 1.05 + 0.04, 0, 1) * 0.6 + hexc(CALCITE) * 0.4
        aa = (mb * 0.85)[..., None]
        self.alb[sl] = self.alb[sl] * (1 - aa) + fresh * aa
        self.load[sl] *= 1 - mb
        self._dirty()

    def soot(self, x, y, amount=0.55, drift=0.22, spread=0.45, ceiling=90.0):
        """soot the fire laid on the wall: a plume rising (and leaning by `drift`) from (x, y), plus the ceiling"""
        H, W = self.H, self.W
        Y, X = self._grid()
        up = np.clip(y - Y, 0, None)
        cx = x + drift * up + 40 * fbm1d(H, 200, 3, self._s())[:, None]
        wid = 50 + spread * up
        plume = np.exp(-((X - cx) / wid) ** 2) * smoothstep(0, 220, up) * (y > Y)
        plume *= 0.55 + 0.45 * smoothstep(0, y, up)
        top = smoothstep(ceiling * 1.6, 0, Y) * 0.7
        n = noise2d(H, W, 70, 4, self._s())
        s = np.clip((plume + top * (0.6 + 0.4 * plume)) * (0.55 + 0.75 * n), 0, 1) * amount
        s *= 1 - self._floor_m
        a = s[..., None]
        self.alb = self.alb * (1 - a) + hexc(SOOT) * a

    # ------------------------------------------------------------------ light
    def _shadow(self, L, dx, dy, dz, reach=140, step=3.0, K=5, soft=5.0):
        """shadow from a point light: march along the in-plane direction to the light, per-pixel climb rate"""
        H, W = self.H, self.W
        dist = np.sqrt(dx * dx + dy * dy) + 1e-3
        slope = dz / dist
        ang = np.arctan2(dy, dx)
        far = dist > 40
        lo, hi = np.percentile(ang[far], [0.5, 99.5]) if far.any() else (-np.pi, np.pi)
        angs = np.linspace(lo, hi, K)
        da = (hi - lo) / max(K - 1, 1) + 1e-6
        R = int(reach + 2)
        hp = np.pad(self.h, R, mode='edge')
        acc = np.zeros((H, W), np.float32); wsum = np.zeros((H, W), np.float32)
        for a in angs:
            wgt = np.clip(1 - np.abs(ang - a) / da, 0, 1)
            if wgt.max() <= 0: continue
            ux, uy = np.cos(a), np.sin(a)
            m = np.full((H, W), -1e9, np.float32)
            t = step
            while t <= reach:
                ox, oy = int(round(ux * t)), int(round(uy * t))
                np.maximum(m, hp[R + oy:R + oy + H, R + ox:R + ox + W] - slope * t, out=m)
                t += step
            acc += wgt * smoothstep(0.0, soft, m - self.h); wsum += wgt
        return acc / (wsum + 1e-6)

    def _lighting(self):
        if self._lit is not None: return self._lit
        H, W = self.H, self.W
        n = height_normals(self.h)
        Y, X = self._grid()
        I = np.zeros((H, W, 3), np.float32); S = np.zeros((H, W, 3), np.float32)
        for L in self.lights:
            dx = L['x'] - X; dy = L['y'] - Y; dz = L['z'] - self.h
            d = np.sqrt(dx * dx + dy * dy + dz * dz) + 1e-3
            lam = (n[..., 0] * dx + n[..., 1] * dy + n[..., 2] * dz) / d
            s = np.clip((lam + L['wrap']) / (1 + L['wrap']), 0, None)
            fall = 1 / (1 + (d / L['reach']) ** 2)
            sh = self._shadow(L, dx, dy, dz) if L['shadow'] else 0.0
            e = s * fall * (1 - 0.7 * sh) * L['power']
            I += e[..., None] * L['col']
            hx, hy, hz = dx / d, dy / d, dz / d + 1
            hn = np.sqrt(hx * hx + hy * hy + hz * hz)
            ndh = np.clip((n[..., 0] * hx + n[..., 1] * hy + n[..., 2] * hz) / hn, 0, 1)
            spec = self.wet * ndh ** 36 * fall * (1 - sh) * L['power'] * 1.6
            S += spec[..., None] * L['col']
        ao = ambient_occlusion(self.h, radii=(3, 10, 30), depth=(3.0, 8.0, 20.0))
        amb = (np.array([0.040, 0.044, 0.056], np.float32) * (1 - ao)[..., None])
        I = I * (1 - 0.45 * ao)[..., None] + amb
        self._lit = (I, S)
        return self._lit

    # ------------------------------------------------------------------ fire layer (in front of the wall)
    def _tongue(self, E, box, x, y, hgt, wid, lean, phase, r):
        n = 36
        t = np.linspace(0, 1, n)
        cx = x + lean * hgt * t ** 1.6 + wid * 0.45 * np.sin(phase + t * 5.2) * t + r.normal(0, 1) * wid * 0.1 * t
        cy = y - hgt * t
        w = wid * (1 - t) ** 0.85 * np.clip(0.55 + t * 4, 0, 1)
        S = np.stack([cx, cy], 1)
        mo = blur(self._raster(box, strokes=[(S, np.maximum(w, 0.6))], ss=2), 1.3)
        k = int(n * 0.6)
        mc = blur(self._raster(box, strokes=[(S[:k], np.maximum(w[:k] * 0.48, 0.6))], ss=2), 1.8)
        E += mo[..., None] * np.array([0.95, 0.26, 0.04], np.float32) * 0.5
        E += mc[..., None] * np.array([1.0, 0.62, 0.20], np.float32) * 0.5

    def _fire_layer(self):
        if self._fx is not None: return self._fx
        H, W = self.H, self.W
        E = np.zeros((H, W, 3), np.float32)
        A = np.zeros((H, W), np.float32); C = np.zeros((H, W, 3), np.float32)
        smoke = np.zeros((H, W), np.float32)
        for f in self.fires:
            r = np.random.default_rng(f['seed'])
            x, y, s = f['x'], f['y'], f['size']
            box = self._box([(x - s * 0.9, y - s * 1.35), (x + s * 0.9, y + s * 0.35)], 30)
            sl = self._sl(box)
            # logs: charred, lit on top by the flames, glowing cracks
            for k in range(4):
                ang = np.radians([205, 335, 240, 300][k] + r.uniform(-6, 6))
                ln = s * r.uniform(0.5, 0.62)
                p1 = np.array([x + np.cos(ang) * ln, y + 10 - np.sin(ang) * s * 0.16])
                p0 = np.array([x + np.cos(ang) * s * 0.05, y - s * 0.06])
                wd = s * r.uniform(0.08, 0.1)
                lm = self._raster(box, strokes=[(np.array([p0, p1]), np.array([wd, wd * 0.9]))], ss=2)
                Yl, Xl = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
                d = p1 - p0; L = np.linalg.norm(d); nrm = np.array([-d[1], d[0]]) / L
                if nrm[1] > 0: nrm = -nrm
                across = ((Xl - p0[0]) * nrm[0] + (Yl - p0[1]) * nrm[1]) / (wd / 2)       # +1 top edge
                lit = np.clip(across, -1, 1) * 0.5 + 0.5
                cyl = np.sqrt(np.clip(1 - np.clip(across, -1, 1) ** 2, 0, 1))
                bark = 0.75 + 0.5 * self._noise(box, 4, 2)
                col = (np.array([0.035, 0.026, 0.02], np.float32)
                       + (cyl * lit ** 1.5 * bark)[..., None] * np.array([0.62, 0.26, 0.08], np.float32))
                ncr = self._noise(box, 6, 2)
                crack = smoothstep(0.66, 0.74, ncr) * smoothstep(0.2, 0.9, lit) * lm
                A[sl] = np.maximum(A[sl], lm)
                C[sl] = C[sl] * (1 - lm[..., None]) + col * lm[..., None]
                E[sl] += crack[..., None] * np.array([1.0, 0.38, 0.08], np.float32) * 1.4
            # ember bed
            Yl, Xl = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32)
            dd = np.sqrt(((Xl - x) / (s * 0.42)) ** 2 + ((Yl - y - 4) / (s * 0.1)) ** 2)
            emb = smoothstep(1.0, 0.3, dd) * (0.4 + 0.9 * smoothstep(0.45, 0.8, self._noise(box, 7, 2)))
            E[sl] += emb[..., None] * np.array([1.0, 0.32, 0.06], np.float32) * 1.2
            # flame tongues
            Eloc = np.zeros(E[sl].shape, np.float32)
            for k in range(15):
                off = r.uniform(-1, 1)
                bx = x + off * s * 0.3
                hgt = s * r.uniform(0.5, 1.0) * (1 - 0.5 * abs(off))
                self._tongue(Eloc, box, bx, y + 2, hgt, s * r.uniform(0.15, 0.24) * (1 - 0.35 * abs(off)),
                             0.1 + r.uniform(-0.06, 0.08), r.uniform(0, 6.28), r)
            for k in range(5):                                               # detached licks above
                bx = x + r.uniform(-0.18, 0.22) * s; by = y - s * r.uniform(0.75, 1.05)
                self._tongue(Eloc, box, bx, by, s * r.uniform(0.12, 0.25), s * r.uniform(0.03, 0.06), 0.3, r.uniform(0, 6), r)
            core = np.exp(-(((Xl - x) / (s * 0.24)) ** 2 + ((Yl - y + s * 0.15) / (s * 0.18)) ** 2))
            Eloc += core[..., None] * np.array([1.0, 0.82, 0.5], np.float32) * 0.55
            E[sl] += Eloc
            # sparks
            for k in range(11):
                sx = x + r.normal(0, s * 0.18) + r.uniform(0, s * 0.2); sy = y - s * r.uniform(0.85, 1.45)
                ln = r.uniform(2, 6)
                b2 = self._box([(sx, sy), (sx + 3, sy - ln)], 3)
                pm = self._raster(b2, strokes=[(np.array([(sx, sy), (sx + r.uniform(-1, 2), sy - ln)]), np.array([2.2, 1.4]))], ss=2)
                E[self._sl(b2)] += pm[..., None] * np.array([1.0, 0.5, 0.12], np.float32) * r.uniform(1.0, 2.0)
            # smoke: a plume rising from the flame tips, leaning right, widening
            Y, X = self._grid()
            up = np.clip(y - s * 0.7 - Y, 0, None)
            cx = x + 0.18 * up + 50 * fbm1d(H, 260, 3, int(r.integers(1 << 30)))[:, None] * smoothstep(0, 300, up)[:, 0:1]
            wid = s * 0.3 + 0.32 * up
            sm = np.exp(-((X - cx) / wid) ** 2) * smoothstep(-20, 120, up) * smoothstep(y + 40, y - s * 0.5, Y)
            sm *= 0.4 + 0.8 * noise2d(H, W, 90, 4, int(r.integers(1 << 30)))
            smoke = np.maximum(smoke, sm)
        for lp in self.lamps:
            r = np.random.default_rng(lp['seed'])
            x, y, s = lp['x'], lp['y'], lp['size']
            box = self._box([(x - s * 0.3, y - s * 0.6), (x + s * 0.3, y + s * 0.1)], 20)
            sl = self._sl(box)
            Eloc = np.zeros(E[sl].shape, np.float32)
            for k in range(3):
                self._tongue(Eloc, box, x + r.uniform(-2, 2), y, s * r.uniform(0.32, 0.42), s * 0.07, 0.05, r.uniform(0, 6), r)
            E[sl] += Eloc
        # bloom on a quarter-size copy
        Es = np.asarray(Image.fromarray(np.clip(E * 60, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BOX),
                        np.float32) / 60
        g1 = np.stack([blur(Es[..., i], 4) for i in range(3)], -1)
        g2 = np.stack([blur(Es[..., i], 22) for i in range(3)], -1)
        up4 = lambda a: np.stack([np.asarray(Image.fromarray(a[..., i]).resize((W, H), Image.BILINEAR), np.float32)
                                  for i in range(3)], -1)
        bloom = up4(g1 * 0.5 + g2 * 1.4)
        self._fx = (E, bloom, A, C, np.clip(smoke, 0, 1))
        return self._fx

    # ------------------------------------------------------------------ output
    def composite(self, exposure=1.7, smoke=0.16, vignette=0.55, grain=0.012, contrast=1.18, saturation=1.18):
        I, S = self._lighting()
        R = self.alb * I + S
        if self.fires or self.lamps:
            E, bloom, A, C, sm = self._fire_layer()
            if smoke:
                a = (sm * smoke)[..., None]
                scol = np.array([0.10, 0.085, 0.075], np.float32) + I * 0.22
                R = R * (1 - a) + scol * a
            R = R * (1 - A[..., None]) + C * A[..., None]
            R = R + E + bloom * 0.55
        out = 1 - np.exp(-R * exposure)
        out = np.clip(out, 0, 1) ** contrast
        lum = out.mean(-1, keepdims=True)
        out = np.clip(lum + (out - lum) * saturation, 0, 1)
        Y, X = self._grid()
        v = ((X / self.W - 0.5) * 1.6) ** 2 + ((Y / self.H - 0.5) * 1.5) ** 2
        out *= (1 - vignette * smoothstep(0.25, 1.25, v))[..., None]
        out = np.clip(out, 0, 1) ** 0.95
        gr = np.random.default_rng(self.seed + 101).normal(0, grain, out.shape[:2]).astype(np.float32)
        out += gr[..., None] * (0.5 + out)
        return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=88, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
