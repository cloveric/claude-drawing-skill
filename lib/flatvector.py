"""flatvector — layered flat vector landscape: big simple geometric shapes, a bold but small palette, a soft
ambient shadow where one layer overlaps the next, and a fine print grain (numpy + Pillow only).

Model: an artboard in a vector app where every object is a *layer* stacked in front of the last one -- the look of
modern motion-graphics backgrounds and editorial landscape posters, not of a painting.
  shapes     every mark is a closed geometric shape with a crisp anti-aliased edge: circles and ellipses (analytic
             coverage), polygons whose corners can be filleted (`round=`), tapered capsules, smooth land profiles
             (a spline top edge filled down to the bottom of the board), stars. A shape is a `Mask`: a coverage patch
             plus its offset on the board, so union `|`, intersection `&`, difference `-` and `moved()` only touch
             the overlap of bounding boxes. No outlines anywhere: neighbouring layers are told apart by value and
             hue only, so every object is planned against what sits behind it.
  palette    five to seven flat hues (here NIGHT navy, PLUM, BERRY magenta, EMBER orange, SAND, PINE teal, CREAM).
             Every other colour is a *tone* of one of them (`tone(c, -k)` toward the night ink, `+k` toward cream)
             or a `mix()` of two of them, so the whole picture stays in one family.
  light      one light (here the moon, upper left) for the whole board: every object is split into a lit face and a
             shade face along a straight or kinked line (`face()`), shade faces always on the side away from the
             light. Mountains get a faceted ridge line, pines are split down the middle, clouds get a darker belly
             (the cloud minus itself nudged up). No gradients: glow is a stack of flat translucent rings (`glow()`),
             a beam is one translucent flat polygon.
  layers     the "vector paper" depth cue: `fill(..., lift=px)` first drops a soft, short ambient shadow of the shape
             onto whatever is already on the board (a blurred copy, nudged down a little, multiplied by a night-blue
             tint so shadows stay in the palette), then lays the flat colour on top. The shadow shows as a thin
             dark seam above and below every overlap -- under snow caps, along the crest of each hill band, under
             each tier of a pine -- so the landscape reads as stacked layers without a single line.
  texture    two quiet textures, both fixed per seed so successive stages keep the same pixels: inside each layer a
             very faint fibrous streak field (sampled at a different offset per layer, so each layer looks like its
             own sheet), and over the finished board a fine monochrome grain. Both are around 1-2 % in value; large
             flat fields must still read as flat.
  rhythm     the picture is carried by the rhythm of a few big shapes (triangles of the ranges, waves of the hills,
             the moon disc and its rays) and generous empty sky. Small things (stars, dashes on the sand, pebbles)
             are sparse and tiny, and only one or two warm accents carry the story.
Coordinates are pixels on the board; angles are degrees counter-clockwise.

    from flatvector import FlatVector, NIGHT, PLUM, BERRY, EMBER, SAND, PINE, CREAM
    fv = FlatVector(1920, 1080, seed=3)
    fv.backdrop(NIGHT); fv.moon(420, 260, 110, rays=18); fv.stars(120)
    fv.mountain((1380, 300), (880, 720), (1920, 720), PLUM, snow=0.22)
    fv.land([(0, 640), (600, 610), (1300, 650), (1920, 620)], BERRY, lift=9)
    fv.land([(0, 760), (1920, 750)], SAND, lift=10)
    fv.pine(300, 760, 260)
    fv.tent(1250, 880, 260, 170); fv.campfire(1020, 885, 1.0)
    fv.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, spline, noise2d

NIGHT, PLUM, BERRY, EMBER, SAND, PINE, CREAM = ('#1f2a55', '#8d6bb5', '#b8336b', '#e5733a', '#e7b84e',
                                                 '#2b8f77', '#f4e9cf')
PALETTE = dict(night=NIGHT, plum=PLUM, berry=BERRY, ember=EMBER, sand=SAND, pine=PINE, cream=CREAM)
_MARGIN = 96                           # masks may hang this far off the board (for blur and moves)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str): return hexc(PALETTE.get(c, c))
    return np.asarray(c, np.float32)


def tone(c, k):
    """k < 0 mixes toward the night ink, k > 0 toward cream: every shade stays inside the palette's family"""
    c = _c(c)
    return c + (_c(NIGHT) * 0.75 - c) * (-k) if k < 0 else c + (_c(CREAM) - c) * k


def mix(a, b, t):
    a, b = _c(a), _c(b)
    return a + (b - a) * t


class Mask:
    """a coverage patch `a` (float32 0..1) whose top-left corner sits at (x0, y0) on the board"""
    __slots__ = ('x0', 'y0', 'a')

    def __init__(self, x0, y0, a):
        self.x0, self.y0, self.a = int(x0), int(y0), a.astype(np.float32, copy=False)

    @property
    def x1(self): return self.x0 + self.a.shape[1]

    @property
    def y1(self): return self.y0 + self.a.shape[0]

    def _on(self, x0, y0, x1, y1):
        """this mask resampled onto box (x0, y0, x1, y1), zero outside"""
        out = np.zeros((max(0, y1 - y0), max(0, x1 - x0)), np.float32)
        ix0, iy0, ix1, iy1 = max(x0, self.x0), max(y0, self.y0), min(x1, self.x1), min(y1, self.y1)
        if ix1 > ix0 and iy1 > iy0:
            out[iy0 - y0:iy1 - y0, ix0 - x0:ix1 - x0] = self.a[iy0 - self.y0:iy1 - self.y0, ix0 - self.x0:ix1 - self.x0]
        return out

    def __or__(self, o):
        if o is None: return self
        b = (min(self.x0, o.x0), min(self.y0, o.y0), max(self.x1, o.x1), max(self.y1, o.y1))
        return Mask(b[0], b[1], np.maximum(self._on(*b), o._on(*b)))

    def __and__(self, o):
        b = (max(self.x0, o.x0), max(self.y0, o.y0), min(self.x1, o.x1), min(self.y1, o.y1))
        if b[2] <= b[0] or b[3] <= b[1]: return Mask(self.x0, self.y0, np.zeros((1, 1), np.float32))
        return Mask(b[0], b[1], np.minimum(self._on(*b), o._on(*b)))

    def __sub__(self, o):
        if o is None: return self
        b = (self.x0, self.y0, self.x1, self.y1)
        return Mask(self.x0, self.y0, self.a * (1 - o._on(*b)))

    def moved(self, dx, dy):
        return Mask(self.x0 + int(round(dx)), self.y0 + int(round(dy)), self.a)

    def scaled(self, k):
        return Mask(self.x0, self.y0, np.clip(self.a * k, 0, 1))


def _fillet(pts, r):
    """round every corner of a closed polygon with radius r (quadratic arcs tangent to both edges)"""
    P = np.asarray(pts, np.float32)
    n = len(P); out = []
    rs = r if np.ndim(r) else [r] * n
    for i in range(n):
        p, a, b = P[i], P[i - 1], P[(i + 1) % n]
        if rs[i] <= 0:
            out.append(p); continue
        u, v = a - p, b - p
        lu, lv = np.linalg.norm(u) + 1e-6, np.linalg.norm(v) + 1e-6
        u, v = u / lu, v / lv
        ang = np.arccos(np.clip(np.dot(u, v), -1, 1))
        t = min(rs[i] / max(np.tan(ang / 2), 1e-3), lu * 0.45, lv * 0.45)
        p0, p1 = p + u * t, p + v * t
        for s in np.linspace(0, 1, 9):
            out.append((1 - s) ** 2 * p0 + 2 * (1 - s) * s * p + s * s * p1)
    return np.array(out, np.float32)


class FlatVector:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.7, -0.7)):
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.light = np.array(light, np.float32) / (np.hypot(*light) + 1e-6)   # screen direction toward the light
        self.img = np.zeros((H, W, 3), np.float32)
        self.stages = []
        self.shadow_tint = mix(NIGHT, PLUM, 0.25) * 0.9           # shadows multiply by this: navy-violet, never grey
        P = 256
        r = np.random.default_rng(seed + 101)
        streak = np.asarray(Image.fromarray(r.random(((H + P) // 14 + 2, (W + P) // 2 + 2)).astype(np.float32))
                            .resize((W + P, H + P), Image.BICUBIC), np.float32)
        blot = noise2d(H + P, W + P, 90, 3, seed + 7)
        f = 0.65 * (streak - streak.mean()) / (streak.std() + 1e-6) + 0.35 * (blot - blot.mean()) / (blot.std() + 1e-6)
        self._fibre = f.astype(np.float32)
        g = np.random.default_rng(seed + 202).normal(0, 1, (H, W)).astype(np.float32)
        self._grain = (0.75 * g + 0.6 * blur(g, 0.9) * 2.2).astype(np.float32)

    # ------------------------------------------------------------------ shapes (all return Mask)
    def _box(self, x0, y0, x1, y1):
        M = _MARGIN
        x0, y0 = max(int(np.floor(x0)) - 2, -M), max(int(np.floor(y0)) - 2, -M)
        x1, y1 = min(int(np.ceil(x1)) + 2, self.W + M), min(int(np.ceil(y1)) + 2, self.H + M)
        return x0, y0, max(x1, x0 + 1), max(y1, y0 + 1)

    def _grid(self, x0, y0, x1, y1):
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        return xs + 0.5, ys + 0.5

    def poly(self, pts, round=0):
        """filled polygon; round = corner radius (one number, or one per vertex)"""
        P = _fillet(pts, round) if np.any(np.asarray(round) > 0) else np.asarray(pts, np.float32)
        x0, y0, x1, y1 = self._box(P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max())
        ss = 4
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P], fill=255)
        a = np.asarray(im, np.float32).reshape(y1 - y0, ss, x1 - x0, ss).mean((1, 3)) / 255
        return Mask(x0, y0, a)

    def ellipse(self, cx, cy, rx, ry=None, rot=0):
        ry = rx if ry is None else ry
        R = max(rx, ry)
        x0, y0, x1, y1 = self._box(cx - R, cy - R, cx + R, cy + R)
        X, Y = self._grid(x0, y0, x1, y1)
        c, s = np.cos(np.radians(rot)), np.sin(np.radians(rot))
        u, v = (X - cx) * c - (Y - cy) * s, (X - cx) * s + (Y - cy) * c
        f = np.sqrt((u / rx) ** 2 + (v / ry) ** 2) + 1e-6
        g = np.sqrt((u / rx ** 2) ** 2 + (v / ry ** 2) ** 2) / f + 1e-6
        return Mask(x0, y0, np.clip(0.5 - (f - 1) / g, 0, 1))

    def circle(self, cx, cy, r):
        return self.ellipse(cx, cy, r, r)

    def rect(self, x0, y0, x1, y1, round=0):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], round=round)

    def capsule(self, p0, p1, r0, r1=None):
        """a stroke with round ends from p0 (radius r0) to p1 (radius r1): stems, poles, logs, dashes"""
        r1 = r0 if r1 is None else r1
        (ax, ay), (bx, by) = p0, p1
        R = max(r0, r1)
        x0, y0, x1, y1 = self._box(min(ax, bx) - R, min(ay, by) - R, max(ax, bx) + R, max(ay, by) + R)
        X, Y = self._grid(x0, y0, x1, y1)
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy + 1e-6
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1)
        d = np.hypot(X - ax - t * dx, Y - ay - t * dy) - (r0 + (r1 - r0) * t)
        return Mask(x0, y0, np.clip(0.5 - d, 0, 1))

    def star(self, cx, cy, r_out, r_in, n=5, rot=90):
        a = np.radians(rot) + np.arange(2 * n) * np.pi / n
        rr = np.where(np.arange(2 * n) % 2 == 0, r_out, r_in)
        return self.poly(np.stack([cx + rr * np.cos(a), cy - rr * np.sin(a)], 1))

    def profile(self, pts, bottom=None, per=24):
        """land: the area under a smooth top edge through `pts` (x, y), filled down to `bottom`"""
        top = spline(pts, per)
        bottom = self.H + 60 if bottom is None else bottom
        P = np.vstack([top, [[top[-1, 0], bottom], [top[0, 0], bottom]]])
        return self.poly(P)

    def half(self, m, p0, p1):
        """the part of mask m to the right of the directed line p0 -> p1 (screen coordinates, y down)"""
        X, Y = self._grid(m.x0, m.y0, m.x1, m.y1)
        (ax, ay), (bx, by) = p0, p1
        d = ((bx - ax) * (Y - ay) - (by - ay) * (X - ax)) / (np.hypot(bx - ax, by - ay) + 1e-6)
        return Mask(m.x0, m.y0, m.a * np.clip(0.5 - d, 0, 1))

    # ------------------------------------------------------------------ paint
    def _slices(self, m):
        x0, y0, x1, y1 = max(m.x0, 0), max(m.y0, 0), min(m.x1, self.W), min(m.y1, self.H)
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1)), (slice(y0 - m.y0, y1 - m.y0), slice(x0 - m.x0, x1 - m.x0))

    def backdrop(self, colour):
        self.img[:] = _c(colour)
        self._texture(Mask(0, 0, np.ones((self.H, self.W), np.float32)), 0.6)

    def drop(self, m, lift=8, strength=0.36):
        """the ambient shadow a layer lifted `lift` px off the board throws on what is already there"""
        sig = max(1.0, lift * 0.9)
        pad = int(sig * 3 + lift)
        a = np.pad(m.a, pad, mode='constant')
        a = blur(a, sig)
        sm = Mask(m.x0 - pad, m.y0 - pad, a).moved(0, lift * 0.45)
        sl = self._slices(sm)
        if sl is None: return
        (cy, cx), (my, mx) = sl
        k = (strength * sm.a[my, mx])[..., None]
        self.img[cy, cx] *= 1 - k * (1 - self.shadow_tint)

    def _texture(self, m, amount):
        if amount <= 0: return
        sl = self._slices(m)
        if sl is None: return
        (cy, cx), (my, mx) = sl
        ox, oy = int(self.rng.integers(0, 256)), int(self.rng.integers(0, 256))
        f = self._fibre[cy.start + oy:cy.stop + oy, cx.start + ox:cx.stop + ox]
        self.img[cy, cx] *= (1 + 0.008 * amount * f * m.a[my, mx])[..., None]

    def fill(self, m, colour, alpha=1.0, lift=0, texture=1.0, shadow=0.36):
        """lay one flat layer: its ambient shadow first (if lifted), then the colour, then its faint sheet fibre"""
        if m is None: return m
        if lift: self.drop(m, lift, shadow)
        sl = self._slices(m)
        if sl is None: return m
        (cy, cx), (my, mx) = sl
        k = (m.a[my, mx] * alpha)[..., None]
        self.img[cy, cx] += (_c(colour) - self.img[cy, cx]) * k
        self._texture(m.scaled(alpha), texture)
        return m

    def face(self, m, p0, p1, colour, alpha=1.0):
        """shade face: recolour the part of m to the right of the line p0 -> p1"""
        return self.fill(self.half(m, p0, p1), colour, alpha, texture=0)

    def glow(self, cx, cy, rx, ry, colour, rings=4, alpha=0.13, shrink=0.72):
        """flat light: concentric translucent ellipses, each one a hard-edged step (no gradient)"""
        for i in range(rings):
            k = shrink ** i
            self.fill(self.ellipse(cx, cy, rx * k, ry * k), colour, alpha, texture=0)

    # ------------------------------------------------------------------ sky
    def stars(self, n=120, box=None, avoid=(), size=(1.0, 3.0), colour=CREAM):
        """sparse dots of different sizes and strengths; `avoid` = [(cx, cy, r), ...] keeps them off the moon"""
        x0, y0, x1, y1 = box or (0, 0, self.W, self.H * 0.55)
        placed = 0; tries = 0
        while placed < n and tries < n * 20:
            tries += 1
            x, y = self.rng.uniform(x0, x1), self.rng.uniform(y0, y1)
            if any(np.hypot(x - ax, y - ay) < ar for ax, ay, ar in avoid): continue
            r = size[0] + (size[1] - size[0]) * self.rng.random() ** 3
            self.fill(self.circle(x, y, r), colour, self.rng.uniform(0.45, 1.0), texture=0)
            placed += 1

    def sparkle(self, x, y, r, colour=CREAM, alpha=1.0):
        """four-point star (a bright star)"""
        return self.fill(self.star(x, y, r, r * 0.22, 4, 90), colour, alpha, texture=0)

    def moon(self, cx, cy, r, rays=18, ray_colour=EMBER, ray_len=(0.62, 0.38), halo=True, craters=True):
        """the moon as a flat disc with a crown of alternating long / short triangular rays and stepped halo"""
        if halo:
            for i, k in enumerate((2.15, 1.72)):
                self.fill(self.circle(cx, cy, r * k), tone(NIGHT, 0.045 * (i + 1)), texture=0)
        if rays:
            for i in range(rays):
                a = np.radians(90 + 360 * i / rays)
                L = r * (1.16 + (ray_len[0] if i % 2 == 0 else ray_len[1]))
                w = np.radians(360 / rays * (0.22 if i % 2 == 0 else 0.18))
                base = r * 1.12
                pts = [(cx + base * np.cos(a - w), cy - base * np.sin(a - w)),
                       (cx + L * np.cos(a), cy - L * np.sin(a)),
                       (cx + base * np.cos(a + w), cy - base * np.sin(a + w))]
                col = ray_colour if i % 2 == 0 else tone(ray_colour, 0.25)
                self.fill(self.poly(pts, round=[2, 4, 2]), col, lift=4, shadow=0.25)
        disc = self.circle(cx, cy, r)
        self.fill(disc, CREAM, lift=7, shadow=0.4)
        self.fill(disc - disc.moved(-r * 0.16, -r * 0.12), tone(CREAM, -0.07), texture=0)   # quiet shade crescent
        if craters:
            for dx, dy, k in ((-0.32, -0.18, 0.2), (0.28, 0.22, 0.14), (0.05, 0.42, 0.1), (0.36, -0.3, 0.08)):
                self.fill(self.circle(cx + dx * r, cy + dy * r, k * r), tone(CREAM, -0.06), texture=0)
        return disc

    def shooting_star(self, head, tail, r=3.0, colour=CREAM):
        """a meteor: a tapered streak, brighter at the head, in two flat alpha steps"""
        (hx, hy), (tx, ty) = head, tail
        mid = (hx + (tx - hx) * 0.45, hy + (ty - hy) * 0.45)
        self.fill(self.capsule(mid, tail, r * 0.55, 0.3), colour, 0.35, texture=0)
        self.fill(self.capsule(head, mid, r, r * 0.55), colour, 0.85, texture=0)
        self.sparkle(hx, hy, r * 3.2, colour)

    def cloud(self, cx, cy, w, colour=CREAM, belly=None, alpha=1.0, lift=6, seed=0):
        """flat cloud: three or four circles of different sizes sitting on one flat base line, a thin pill under
        them; the shade is the cloud minus itself nudged toward the light (a crescent on the far lower edge)"""
        g = np.random.default_rng(self.seed * 31 + seed)
        base = cy + w * 0.16
        bumps = [(-0.31, 0.15), (-0.1, 0.25), (0.15, 0.2), (0.33, 0.12)]
        if g.random() < 0.5: bumps = [(-dx, r) for dx, r in bumps]
        m = self.rect(cx - w * 0.46, base - w * 0.13, cx + w * 0.46, base, round=w * 0.065)
        for dx, rr in bumps:
            rr *= w * g.uniform(0.92, 1.08)
            m = m | self.circle(cx + dx * w, base - rr * 0.95, rr)
        m = m & self.rect(cx - w, cy - w, cx + w, base)
        self.fill(m, colour, alpha, lift=lift, shadow=0.3)
        belly = mix(colour, PLUM, 0.3) if belly is None else belly
        k = w * 0.045
        self.fill(m - m.moved(self.light[0] * k, self.light[1] * k), belly, alpha, texture=0)
        return m

    # ------------------------------------------------------------------ land
    def mountain(self, peak, left, right, colour, snow=0.0, ridge=None, lift=7, shade=-0.2, seed=0):
        """a flat triangular peak, lit face toward the light and a faceted shade face, optional zig-zag snow cap.
        ridge: the kinked line from the peak down to the foot that splits the faces (auto if None).
        Returns dict(body, shade, snow) masks, e.g. to recolour a trail where it crosses the snow."""
        r = np.random.default_rng(self.seed * 17 + seed)
        (px, py), (lx, ly), (rx, ry) = peak, left, right
        tri = self.poly([left, peak, right], round=[0, 9, 0])
        self.fill(tri, colour, lift=lift)
        if ridge is None:
            h = ly - py
            ridge = [(px + h * 0.06, py + h * 0.3), (px - h * 0.03, py + h * 0.55), (px + h * 0.09, max(ly, ry) + 40)]
        shade_poly = [peak] + list(ridge) + [(rx + 40, ry + 40), (rx + 40, py - 10)]
        side = self.poly(shade_poly) & tri
        self.fill(side, tone(colour, shade), texture=0)
        if snow:
            def on(edge, t): return (px + (edge[0] - px) * t, py + (edge[1] - py) * t)
            tl, tr = snow * r.uniform(0.85, 1.15), snow * r.uniform(0.85, 1.15)
            a, b = np.array(on(left, tl)), np.array(on(right, tr))
            zig = []
            k = 5
            for i in range(1, k):
                p = a + (b - a) * i / k
                zig.append((p[0] + r.uniform(-6, 6), p[1] + (-1) ** i * (ly - py) * snow * 0.18 + (ly - py) * snow * 0.06))
            cap = self.poly([peak, tuple(b)] + zig[::-1] + [tuple(a)], round=[9] + [3] * (len(zig) + 2)) & tri
            self.fill(cap, CREAM, lift=3, shadow=0.3)
            self.fill(cap & side, mix(CREAM, colour, 0.28), texture=0)
        else:
            cap = None
        return dict(body=tri, shade=side, snow=cap)

    def land(self, pts, colour, lift=9, shadow=0.38, texture=1.0):
        """one hill band: everything under a smooth top edge through pts"""
        m = self.profile(pts)
        return self.fill(m, colour, lift=lift, shadow=shadow, texture=texture)

    def pine(self, x, base, h, colour=PINE, tiers=3, width=0.62, shade=-0.22, trunk=None, lift=5):
        """stacked triangle tiers, split down the middle into lit and shade halves; each tier throws a soft
        shadow on the tier below"""
        trunk = tone(EMBER, -0.6) if trunk is None else trunk
        tw = max(3, h * 0.038)
        self.fill(self.rect(x - tw, base - h * 0.2, x + tw, base), trunk, lift=lift)
        top = base - h
        total = h * 0.9                              # the crown stops a little above the ground: trunk shows
        th = total * (0.5 if tiers > 2 else 0.62)    # height of one tier; tiers overlap
        step = (total - th) / max(1, tiers - 1)
        for j in range(tiers - 1, -1, -1):           # bottom (widest) tier first, each upper tier lies on it
            t0 = top + j * step
            t1 = t0 + th
            half = h * width / 2 * (0.55 + 0.45 * (j + 1) / tiers)
            tri = self.poly([(x - half, t1), (x, t0), (x + half, t1)], round=[4, 5, 4])
            self.fill(tri, colour, lift=lift, shadow=0.42)
            self.face(tri, (x, t0 - 5), (x, t1 + 5), tone(colour, shade))

    def round_tree(self, x, base, r, colour=PINE, shade=-0.22, trunk=None, fruit=None, lift=6, seed=0):
        """a crown of two or three overlapping discs on a short trunk; back disc darker"""
        g = np.random.default_rng(self.seed * 13 + seed)
        trunk = tone(EMBER, -0.6) if trunk is None else trunk
        tw = r * 0.13
        self.fill(self.rect(x - tw, base - r * 1.0, x + tw, base), trunk, lift=lift)
        cy = base - r * 1.55
        back = self.circle(x + r * 0.32, cy - r * 0.18, r * 0.82)
        self.fill(back, tone(colour, shade), lift=lift)
        front = self.circle(x - r * 0.18, cy + r * 0.06, r * 0.9)
        self.fill(front, colour, lift=lift)
        self.fill(front - front.moved(-r * 0.2, -r * 0.2), tone(colour, shade * 0.6), texture=0)
        if fruit is not None:
            for k in range(4):
                a = g.uniform(0, 2 * np.pi); d = g.uniform(0.2, 0.7) * r
                self.fill(self.circle(x - r * 0.18 + d * np.cos(a), cy + d * np.sin(a), r * 0.08), fruit, lift=2)

    def dashes(self, box, colours, n=14, length=(50, 150), thick=(5, 9), seed=0, horizon=None):
        """sparse horizontal capsules (lighter / darker sand strokes); shorter and thinner toward the horizon"""
        g = np.random.default_rng(self.seed * 7 + seed)
        x0, y0, x1, y1 = box
        hz = y0 if horizon is None else horizon
        out = []
        for i in range(n):
            y = y0 + (y1 - y0) * g.random() ** 0.8
            k = 0.4 + 0.6 * (y - hz) / max(1, (y1 - hz))
            L = g.uniform(*length) * k; t = g.uniform(*thick) * k
            x = g.uniform(x0, x1)
            m = self.capsule((x - L / 2, y), (x + L / 2, y), t / 2)
            self.fill(m, colours[i % len(colours)], texture=0)
            out.append(m)
        return out

    def pebble(self, x, y, r, colour, lit=None):
        m = self.ellipse(x, y, r, r * 0.62)
        self.fill(m, colour, lift=2, shadow=0.3)
        self.fill(m - m.moved(r * 0.25, r * 0.3), tone(colour, 0.25) if lit is None else lit, texture=0)

    def tuft(self, x, y, h, colour=PINE):
        """three blades of grass: thin filleted triangles"""
        for dx, k, lean in ((-0.35, 0.7, -0.35), (0, 1.0, 0.0), (0.35, 0.8, 0.3)):
            bx = x + dx * h * 0.5
            self.fill(self.poly([(bx - h * 0.09, y), (bx + lean * h * 0.5, y - h * k), (bx + h * 0.09, y)], round=[0, 1.5, 0]),
                      colour, texture=0)

    # ------------------------------------------------------------------ story props
    def trail(self, pts, colour=CREAM, width=(2.5, 5.0), dash=(9, 20), gap=(9, 16), alpha=1.0, per=30):
        """a dashed path through control points; dashes grow with y (nearer = lower on the board = bigger)"""
        P = spline(pts, per)
        seg = np.hypot(*np.diff(P, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        ymin, ymax = P[:, 1].min(), P[:, 1].max()
        at = lambda d: np.array([np.interp(d, s, P[:, 0]), np.interp(d, s, P[:, 1])])
        k = lambda y: (y - ymin) / max(1, ymax - ymin)
        d = 0.0; m = None
        while d < s[-1]:
            y = at(d)[1]; t = k(y)
            L = dash[0] + (dash[1] - dash[0]) * t
            G = gap[0] + (gap[1] - gap[0]) * t
            a, b = at(d), at(min(d + L, s[-1]))
            w = width[0] + (width[1] - width[0]) * t
            m = self.capsule(tuple(a), tuple(b), w / 2) | m
            d += L + G
        self.fill(m, colour, alpha, texture=0)
        return m

    def flag(self, x, y, h, colour=EMBER, pole=CREAM):
        """a small summit flag: pole planted at (x, y), pennant flying right"""
        self.fill(self.capsule((x, y), (x, y - h), max(1.2, h * 0.035)), pole, texture=0)
        self.fill(self.poly([(x + 1, y - h), (x + h * 0.62, y - h * 0.84), (x + 1, y - h * 0.66)], round=[1, 2, 1]),
                  colour, lift=2, shadow=0.3)

    def tent(self, x, base, w, h, colour=EMBER, depth=0.42, inside=SAND, door=0.55, lift=10):
        """an A-frame tent seen three-quarter: front triangle (lit), side roof panel receding right (shade),
        a glowing door opening with a folded-back flap, guy lines and stakes"""
        apex = (x, base - h)
        fl, fr = (x - w / 2, base), (x + w / 2, base)
        dx, dy = w * depth, -h * 0.16
        roof = self.poly([apex, (apex[0] + dx, apex[1] + dy), (fr[0] + dx, fr[1] + dy), fr], round=[3, 3, 0, 0])
        front = self.poly([fl, apex, fr], round=[0, 5, 0])
        self.fill(roof | front, tone(colour, -0.28), lift=lift, shadow=0.45)
        self.fill(roof - front, tone(colour, -0.28), texture=0.6)
        self.fill(front, colour)
        dh = h * door
        dw = w * door * 0.42
        opening = self.poly([(x - dw, base), (x, base - dh), (x + dw * 0.9, base)], round=[0, 3, 0])
        self.fill(opening, inside, texture=0)
        self.fill(self.poly([(x - dw * 0.55, base), (x, base - dh * 0.62), (x + dw * 0.5, base)], round=[0, 3, 0]),
                  tone(inside, 0.4), texture=0)
        flap = self.poly([(x + dw * 0.9, base), (x, base - dh), (x + dw * 1.55, base)], round=[0, 2, 0])
        self.fill(flap, tone(colour, 0.22), lift=3, shadow=0.3)
        self.fill(self.capsule(apex, (apex[0], apex[1] - h * 0.08), max(1.5, w * 0.012)), tone(colour, -0.5), texture=0)
        for p0, p1 in ((apex, (x - w * 0.66, base + h * 0.02)), ((apex[0] + dx, apex[1] + dy), (fr[0] + dx + w * 0.2, base - h * 0.1))):
            self.fill(self.capsule(p0, p1, 1.1), tone(CREAM, -0.1), 0.85, texture=0)
            self.fill(self.capsule((p1[0], p1[1] - 6), (p1[0], p1[1] + 4), 2), tone(EMBER, -0.6), texture=0)
        return front

    def teardrop(self, x, bottom, r, h, lean=0.0):
        """a flame / drop: a disc of radius r resting on `bottom`, closed by tangents to a tip h above the bottom;
        lean tilts the tip sideways (degrees, + = to the right)"""
        cx, cy = x, bottom - r
        d = h - r
        th = np.arccos(np.clip(r / d, -1, 1))
        a = np.radians(lean)
        tip = (cx + d * np.sin(a), cy - d * np.cos(a))
        pl = (cx + r * np.sin(a - th), cy - r * np.cos(a - th))
        pr = (cx + r * np.sin(a + th), cy - r * np.cos(a + th))
        return self.circle(cx, cy, r) | self.poly([pl, tip, pr], round=[0, r * 0.18, 0])

    def campfire(self, x, base, s=1.0, flame=(EMBER, SAND, CREAM), log=None, stone=None, sparks=6, seed=0):
        """a few stones, a flame of three nested teardrops (outer one with two side tongues), crossed logs in front
        of its foot, and a few sparks"""
        g = np.random.default_rng(self.seed * 5 + seed)
        log = tone(EMBER, -0.55) if log is None else log
        stone = mix(PLUM, CREAM, 0.35) if stone is None else stone
        for sx, sy, sr in ((-54, -4, 11), (-30, 4, 12), (34, 4, 12), (56, -4, 10)):
            self.pebble(x + sx * s, base + sy * s, sr * s, tone(stone, -0.12), lit=stone)
        yb = base - 8 * s
        outer = self.teardrop(x, yb, 36 * s, 128 * s, 4) | self.teardrop(x - 26 * s, yb - 4 * s, 18 * s, 78 * s, -24) | \
            self.teardrop(x + 27 * s, yb - 4 * s, 16 * s, 66 * s, 26)
        self.fill(outer, flame[0], lift=4, shadow=0.22, texture=0)
        self.fill(self.teardrop(x + 2 * s, yb, 24 * s, 88 * s, 2), flame[1], texture=0)
        self.fill(self.teardrop(x + 3 * s, yb, 13 * s, 50 * s, 0), flame[2], texture=0)
        for p0, p1, c in (((x - 52 * s, base + 4 * s), (x + 44 * s, base - 16 * s), log),
                          ((x + 52 * s, base + 4 * s), (x - 44 * s, base - 16 * s), tone(log, 0.14))):
            self.fill(self.capsule(p0, p1, 8.5 * s), c, lift=3, shadow=0.3, texture=0)
            self.fill(self.circle(p0[0], p0[1], 6 * s), tone(SAND, -0.08), texture=0)        # sawn end
        for i in range(sparks):
            sx = x + g.uniform(-40, 40) * s
            sy = base - (120 + g.uniform(0, 70)) * s
            self.fill(self.circle(sx, sy, g.uniform(2, 3.6) * s), flame[1 + i % 2], g.uniform(0.6, 1.0), texture=0)

    def hiker(self, x, base, h, colour=None, pack=EMBER, facing=1, lamp=True, beam=CREAM, step=0.5):
        """a tiny walking silhouette (no face): leaning into the walk, backpack, stick, head torch with a flat beam"""
        colour = tone(NIGHT, -0.15) if colour is None else colour
        f = facing; u = h / 10.0
        hip = (x, base - 4.6 * u)
        head = (x + f * 0.9 * u, base - 8.9 * u)
        if lamp:
            lx, ly = head[0] + f * 0.9 * u, head[1] - 0.1 * u
            self.fill(self.poly([(lx, ly), (lx + f * 9 * u, ly + 3.6 * u), (lx + f * 8.2 * u, ly + 6.3 * u)]), beam, 0.22, texture=0)
        stride = 1.9 * u * (0.6 + step * 0.4)
        m = self.capsule(hip, (x - f * stride * 0.7, base - 2.2 * u), 0.75 * u, 0.6 * u) | \
            self.capsule((x - f * stride * 0.7, base - 2.2 * u), (x - f * stride * 1.1, base - 0.3 * u), 0.6 * u, 0.5 * u)
        m = m | self.capsule(hip, (x + f * stride * 0.8, base - 2.4 * u), 0.75 * u, 0.6 * u) | \
            self.capsule((x + f * stride * 0.8, base - 2.4 * u), (x + f * stride * 0.95, base - 0.3 * u), 0.6 * u, 0.5 * u)
        m = m | self.capsule(hip, (x + f * 0.55 * u, base - 7.4 * u), 1.05 * u, 1.2 * u)
        m = m | self.circle(*head, 1.05 * u)
        m = m | self.capsule((x + f * 0.5 * u, base - 7.0 * u), (x + f * 2.1 * u, base - 5.0 * u), 0.45 * u, 0.4 * u)
        self.fill(self.capsule((x + f * 2.2 * u, base - 5.6 * u), (x + f * 3.0 * u, base - 0.1 * u), 0.22 * u), tone(CREAM, -0.2), texture=0)
        self.fill(m, colour, lift=3, shadow=0.3, texture=0)
        bp = self.poly([(x - f * 1.9 * u, base - 7.6 * u), (x - f * 0.2 * u, base - 7.9 * u), (x - f * 0.0 * u, base - 4.9 * u),
                        (x - f * 1.7 * u, base - 4.7 * u)], round=0.6 * u)
        self.fill(bp, pack, texture=0)
        self.fill(self.half(bp, (x - f * 0.9 * u, base - 9 * u), (x - f * 0.9 * u, base - 4 * u)) if f > 0 else
                  self.half(bp, (x - f * 0.9 * u, base - 4 * u), (x - f * 0.9 * u, base - 9 * u)), tone(pack, -0.25), texture=0)
        if lamp:
            self.fill(self.circle(head[0] + f * 0.85 * u, head[1] - 0.15 * u, 0.42 * u), beam, texture=0)

    # ------------------------------------------------------------------ output
    def render(self):
        img = self.img * (1 + 0.011 * self._grain)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.render()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.render()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
