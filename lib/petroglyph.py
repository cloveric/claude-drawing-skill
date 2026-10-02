"""petroglyph -- pecked rock art on desert-varnished sandstone (numpy + Pillow only).

A petroglyph is not painted on: it is a picture made by knocking the dark skin off a rock. Everything below is
height (in px) and colour fields that the actions change, lit at the end by one low sun.

Model:
  rock      a sandstone face is a height field (broad undulations, thin wavy bedding laminae, sand-grain tooth) and
            an albedo: warm buff-orange stone, cloudy and banded, with scattered dark lithic and pale quartz grains.
            `ledge()` sets the face below a wavy line back by a step (a lower, sheltered face under an overhang lip).
  varnish   desert varnish is a paper-thin coat of clay with manganese and iron oxides that grows over centuries where
            rain water runs down the face. It is a thickness field v (0 bare stone .. 1 thick) plus a manganese field:
            red-brown where iron-rich, blue-black where manganese-rich. Near-uniform and dark, with crisp vertical
            runoff streaks (each narrows and fades downward, wanders a little, mostly starts near the top), paler
            streaks where the flow kept it thin, a darker band under the top lip, seep streaks below cracks, and
            thinner near the ground where blown sand scours it. It adds no height.
  peck      the maker struck the face with a hammerstone. Every blow leaves an irregular pit a few px wide that breaks
            through the varnish to the paler stone and crushes the grains white. A glyph is rasterised to a mask and
            hammered out of it with hundreds to thousands of pits: centres are sampled inside the mask with uneven
            density and a few stray blows past the outline; each pit is a random-polygon sprite with a bowl-shaped
            depth. Depths add up and saturate, so a densely pecked interior is a shallow granular depression and the
            outline is ragged at the scale of one pit.
  abrade    grinding / incising with a stone edge: a smooth V-groove along a stroke, fine striations along it, the
            varnish polished off in the bottom (tally marks, fine lines). Reads smoother and lighter than pecking.
  age       repatination: an old glyph slowly re-varnishes back toward the rock around it and its pits round off.
            age 0 = struck this season (bright, crisp), 0.5 = centuries, 0.85 = a faint ghost under newer work.
            Superimposition comes free: a new glyph pecked over an old one is brighter and cuts deeper.
  fracture  a crack: a jagged narrow slot with rounded shoulders and side branches; water seeping out of it lays a
            darker varnish streak that runs down the face below.
  spall     exfoliation: a flake of the face broke away, taking whatever glyph was on it. The scar is a step down (a
            sharp lip of small scallops that casts a shadow), conchoidal ripples around the impact point, fresh
            orange stone with its own iron banding and a pale rind at the lip; age > 0 lets new varnish film it over.
  lichen    crustose lichen rosettes (olive map lichen, orange, grey): lobed rims, areolate (cracked) centres, tiny
            dark fruiting discs, satellite dots, slightly raised.
  light     a low sun from the upper left (raking light, the way rock art is photographed) plus cool sky light:
            Lambert shading from the height-field normals, cast shadows marched along the light (each pit is dark on
            its upper-left wall and lit on the lower-right), ambient occlusion in pits and cracks.
Order: rock -> ledge -> varnish -> fractures -> old (aged) glyphs -> newer glyphs -> spalls -> lichen.
Glyphs are drafted first (`Draft`, or the helpers bighorn / hunter / sun_spiral / crescent / concentric / hand /
hoofprints / meander, which all return a Draft and accept `into=` to collect several figures into one), then
`peck()`ed; tally marks and fine lines are `abrade()`d. Coordinates are px, y down; angles in degrees,
counter-clockwise.

    from petroglyph import Petroglyph
    pg = Petroglyph(1920, 1080, seed=3)
    pg.rock(); pg.ledge(900, drop=34); pg.varnish()
    pg.fracture([(900, 0), (860, 300)])
    pg.peck(pg.meander([(300, 800), (700, 760), (1100, 820)], 14), age=0.8)     # an old, re-varnished line
    pg.peck(pg.bighorn(800, 600, 180))                                         # a fresh bighorn sheep
    pg.abrade_tally(200, 150, [10, 10], length=60)
    pg.spall([(1700, 0), (1920, 0), (1920, 160), (1760, 120)])
    pg.lichen(1000, 980, 40, 'green')
    pg.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, height_normals, height_shadow, ambient_occlusion

STONE, STONE_PALE, STONE_RED = '#c3855a', '#d9aa7e', '#b0643e'      # sandstone under the varnish
SCAR = '#d4865a'                                                      # fresh stone in a spall scar
CRUSH = '#ecd3b0'                                                     # hammer-crushed grains
VARNISH_FE, VARNISH_MN = '#4a2517', '#20150e'                         # iron-rich / manganese-rich varnish
LICHEN = {'green': ('#9c9f52', '#bdbb72'), 'orange': ('#b8742e', '#d39445'), 'grey': ('#8f9180', '#b0b09c')}
SUN, SKY = np.array([1.0, 0.92, 0.80], np.float32), np.array([0.62, 0.68, 0.80], np.float32)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _resample(pts, step):
    """polyline -> points every `step` px"""
    P = np.asarray(pts, np.float32)
    if len(P) < 2: return P
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(s[-1] / step) + 1)
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1)


# ---------------------------------------------------------------- glyph drafting
class Draft:
    """the design a maker would chalk on the rock before hammering: a mask built from strokes, fills and dots
    (2x supersampled). Strokes wobble a little in path and width, like a hand-laid line."""

    def __init__(self, W, H, ss=2, seed=0):
        self.W, self.H, self.ss = W, H, ss
        self.im = Image.new('L', (W * ss, H * ss), 0)
        self.d = ImageDraw.Draw(self.im)
        self.rng = np.random.default_rng(seed)
        self.extra = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def stroke(self, pts, width, end_width=None, wobble=0.12, smooth=True, value=255):
        """a line of round dabs from width to end_width (taper); wobble = relative wander of path and width"""
        P = spline(pts, 10) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32)
        P = _resample(P, max(0.8, width * 0.18))
        n = len(P)
        w1 = width if end_width is None else end_width
        w = np.linspace(width, w1, n) * (1 + wobble * fbm1d(n, max(4, n / 3), 3, self._seed()))
        if n > 2 and wobble:
            t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-6
            nrm = np.stack([-t[:, 1], t[:, 0]], 1)
            P = P + nrm * (wobble * width * 0.35 * fbm1d(n, max(4, n / 4), 3, self._seed()))[:, None]
        s = self.ss
        for (x, y), ww in zip(P, w):
            r = max(0.5, ww / 2) * s
            self.d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r], fill=value)
        return self

    def fill(self, pts, smooth=True, value=255):
        """a filled outline (closed spline through the points when smooth)"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 3:
            P = _closed_spline(P)
        s = self.ss
        self.d.polygon([(float(x) * s, float(y) * s) for x, y in P], fill=value)
        return self

    def dot(self, x, y, r, value=255):
        s = self.ss
        self.d.ellipse([(x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s], fill=value)
        return self

    def ring(self, x, y, r, width, wobble=0.08):
        t = np.linspace(0, 2 * np.pi, max(24, int(r * 0.9)) + 1)
        rr = r * (1 + 0.03 * fbm1d(len(t), len(t) / 5, 3, self._seed()))
        return self.stroke(np.stack([x + rr * np.cos(t), y + rr * np.sin(t)], 1), width, wobble=wobble, smooth=False)

    def add(self, mask):
        """merge a full-frame float mask (0..1)"""
        self.extra = mask.astype(np.float32) if self.extra is None else np.maximum(self.extra, mask)
        return self

    def mask(self):
        m = np.asarray(self.im.resize((self.W, self.H), Image.BILINEAR), np.float32) / 255 if self.ss > 1 else \
            np.asarray(self.im, np.float32) / 255
        return m if self.extra is None else np.maximum(m, self.extra)


def _closed_spline(P, per=10):
    """Catmull-Rom through a closed loop of points"""
    P = np.asarray(P, np.float32)
    n = len(P)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out, np.float32)


# ---------------------------------------------------------------- the rock
class Petroglyph:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.62, -0.50, 0.60)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        L = np.asarray(light, np.float32)
        self.L = L / np.linalg.norm(L)
        self.h = np.zeros((H, W), np.float32)                 # height, px
        self.rockc = np.ones((H, W, 3), np.float32) * hexc(STONE)
        self.v = np.zeros((H, W), np.float32)                 # varnish thickness
        self.v0 = None                                        # varnish as it grew (before any pecking)
        self.mn = np.zeros((H, W), np.float32)                # manganese share of the varnish
        self.crush = np.zeros((H, W), np.float32)             # freshly crushed grains (whitening)
        self.paint = None; self.pa = None                     # lichen layer
        self.stages = []
        self._sprites = {}

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def draft(self):
        return Draft(self.W, self.H, seed=self._seed())

    # ------------------------------------------------------------ stone
    def rock(self, colour=STONE, relief=1.0, bedding=1.0, grain=1.0, bed_angle=-3.0):
        """the sandstone face: height (broad swells, bedding laminae, grain tooth) and the stone colour beneath"""
        H, W = self.H, self.W
        big = noise2d(H, W, 900, 3, self._seed()) - 0.5
        mid = noise2d(H, W, 170, 3, self._seed()) - 0.5
        small = noise2d(H, W, 38, 2, self._seed()) - 0.5
        self.h = ((big * 50 + mid * 14 + small * 1.6) * relief).astype(np.float32)
        # weathering dimples: shallow solution pockets a few px across
        for _ in range(int(150 * relief)):
            x, y = self.rng.uniform(0, W), self.rng.uniform(0, H)
            r = self.rng.uniform(7, 26); dz = self.rng.uniform(0.5, 1.6)
            x0, x1, y0, y1 = int(max(0, x - 2 * r)), int(min(W, x + 2 * r + 1)), int(max(0, y - 2 * r)), int(min(H, y + 2 * r + 1))
            if x1 <= x0 or y1 <= y0: continue
            dd = ((self.XX[y0:y1, x0:x1] - x) ** 2 + (self.YY[y0:y1, x0:x1] - y) ** 2) / (r * r)
            self.h[y0:y1, x0:x1] -= dz * np.exp(-dd * 1.6)
        # bedding: thin laminae, slightly tilted and warped, irregular in spacing
        a = np.deg2rad(bed_angle)
        yb = self.YY * np.cos(a) - self.XX * np.sin(a) + (noise2d(H, W, 520, 2, self._seed()) - 0.5) * 70
        n = H + 2 * W
        lam1 = fbm1d(n, 9, 3, self._seed()); lam2 = fbm1d(n, 60, 3, self._seed())
        grid = np.arange(n, dtype=np.float32) - W
        lam = np.interp(yb, grid, lam1).astype(np.float32)
        band = np.interp(yb, grid, lam2).astype(np.float32)
        lam *= 0.4 + 0.6 * noise2d(H, W, 220, 2, self._seed())                 # laminae come and go
        self.h += (0.45 * lam + 1.3 * band) * bedding
        # grain tooth: sand grains 1-2 px
        g = self.rng.random((H, W), dtype=np.float32)
        self.h += (blur(g, 0.6) - 0.5) * 0.95 * grain
        # stone colour: cloudy patches between paler buff and redder iron-stained stone, banded along the bedding
        col = _c(colour); pale = hexc(STONE_PALE); red = hexc(STONE_RED)
        p = noise2d(H, W, 380, 3, self._seed()); q = noise2d(H, W, 140, 3, self._seed())
        t1 = smoothstep(0.45, 0.85, p)[..., None]; t2 = smoothstep(0.5, 0.9, q)[..., None] * 0.6
        rc = col * (1 - t1) + pale * t1
        rc = rc * (1 - t2) + red * t2
        rc *= (1 + 0.035 * band + 0.012 * lam)[..., None]
        g2 = self.rng.random((H, W), dtype=np.float32)
        rc *= (0.94 + 0.12 * blur(g2, 0.5))[..., None]
        dark = (self.rng.random((H, W), dtype=np.float32) > 0.9965)
        bright = (self.rng.random((H, W), dtype=np.float32) > 0.997)
        rc[dark] *= 0.55; rc[bright] = rc[bright] * 0.5 + 0.5
        self.rockc = rc.astype(np.float32)
        return self

    def ledge(self, y, drop=16, wander=18, soft=2.0):
        """set the face below a wavy line back by `drop` px (a lower face under an overhang lip)"""
        H, W = self.H, self.W
        k = max(3, W // 70)
        knots = np.linspace(0, W - 1, k)
        ang = np.interp(np.arange(W), knots, self.rng.normal(0, 1, k)) * wander * 0.5     # broken, angular lip
        line = y + wander * fbm1d(W, 300, 3, self._seed()) + ang + 2.5 * fbm1d(W, 14, 2, self._seed())
        dy = self.YY - line[None, :]
        below = smoothstep(-soft, soft, dy)
        bevel = smoothstep(-7, 1, dy)                        # the lip is rounded off by weathering
        self.h -= drop * (0.75 * below + 0.25 * bevel)
        self._ledge = line
        return self

    def _streaks(self, n, width=(2.9, 0.55), length=(90, 560), top_bias=2.2, reach=0.7):
        """a field of vertical runoff streaks: crisp-edged, narrowing and fading downward, wandering a little,
        mostly starting near the top (top_bias), each with its own strength"""
        H, W = self.H, self.W
        r = self.rng
        F = np.zeros((H, W), np.float32)
        for i in range(int(n)):
            x = r.uniform(-20, W + 20); w = float(np.clip(np.exp(r.normal(*width)), 5, 110))
            y0 = H * reach * r.random() ** top_bias - 30; L = r.uniform(*length); a = r.uniform(0.35, 1.0)
            xs, xe = int(max(0, x - w - 14)), int(min(W, x + w + 15)); ys, ye = int(max(0, y0)), int(min(H, y0 + L))
            if xe <= xs or ye <= ys: continue
            X = self.XX[ys:ye, xs:xe] - x; Y = self.YY[ys:ye, xs:xe] - y0
            X = X - 7 * np.sin(Y / L * np.pi * r.uniform(0.6, 2.2) + r.uniform(0, 6))
            hw = w / 2 * (1 - 0.55 * Y / L)
            across = smoothstep(hw + 2.5, hw - 2.5, np.abs(X))
            along = smoothstep(0, 50, Y) * (1 - smoothstep(L * 0.3, L, Y))
            F[ys:ye, xs:xe] = np.maximum(F[ys:ye, xs:xe], a * across * along)
        fine = Image.fromarray(r.random((max(2, H // 50), max(2, W // 2))).astype(np.float32))
        fine = np.asarray(fine.resize((W, H), Image.BICUBIC), np.float32)
        return blur(F * (0.75 + 0.35 * fine), 0.7)

    def varnish(self, strength=0.93, streaks=1.0, top=0.14, scour=0.45, patches=1.0):
        """grow desert varnish over the face: a near-uniform dark coat, crisp blue-black runoff streaks and paler
        streaks where the flow kept it thin, thicker under the top lip, sand-scoured near the ground"""
        H, W = self.H, self.W
        base = noise2d(H, W, 420, 4, self._seed())
        v = 0.86 + 0.18 * patches * (base - 0.5)
        zone = np.clip(smoothstep(0.25, 0.7, noise2d(H, W, 450, 3, self._seed())) * 0.7 + 0.5 * smoothstep(H * 0.55, 0, self.YY), 0.15, 1)
        dark = self._streaks(110 * streaks) * zone
        pale = self._streaks(26 * patches, width=(3.6, 0.5), length=(160, 700), top_bias=1.2, reach=0.8)
        v += streaks * 0.20 * dark - 0.24 * patches * pale
        v += top * smoothstep(H * 0.42, 0, self.YY) * (0.55 + 0.45 * base)
        v *= 1 - scour * smoothstep(H * 0.72, H * 1.02, self.YY) * (0.55 + 0.45 * noise2d(H, W, 90, 2, self._seed()))
        if hasattr(self, '_ledge'):          # the sheltered lower face carries less varnish
            under = smoothstep(0, 40, self.YY - self._ledge[None, :])
            v *= 1 - 0.30 * under
        self.v = np.clip(v * strength, 0, 0.97).astype(np.float32)
        self.mn = np.clip(0.35 + 0.5 * (noise2d(H, W, 200, 3, self._seed()) - 0.5) + 0.6 * smoothstep(0.05, 0.6, dark), 0, 1).astype(np.float32)
        self.v0 = self.v.copy()
        return self

    def _runoff(self, src, length=220, decay=None):
        """smear a source mask straight down the face with decay (water running down from it)"""
        k = decay or np.exp(-1.0 / length)
        out = np.empty_like(src); acc = np.zeros(src.shape[1], np.float32)
        for y in range(src.shape[0]):
            acc = np.maximum(src[y], acc * k)
            out[y] = acc
        return out

    def fracture(self, pts, width=3.0, depth=9.0, seep=0.5, branches=2, jag=1.0):
        """a crack along the rough path `pts`: jagged slot with rounded shoulders, side branches, a seep streak below"""
        H, W = self.H, self.W
        d = Draft(W, H, seed=self._seed())
        P = _resample(spline(pts, 12) if len(pts) > 2 else pts, 3.0)
        n = len(P)
        t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-t[:, 1], t[:, 0]], 1)
        P = P + nrm * (jag * (6 * fbm1d(n, 30, 3, self._seed()) + 1.6 * fbm1d(n, 4, 2, self._seed())))[:, None]
        wv = width * (0.55 + 0.9 * (0.5 + 0.5 * fbm1d(n, 25, 3, self._seed())))
        s = d.ss
        for (x, y), ww in zip(P, wv):
            rr = ww / 2 * s
            d.d.ellipse([x * s - rr, y * s - rr, x * s + rr, y * s + rr], fill=255)
        for _ in range(branches):
            i = int(self.rng.integers(n // 6, max(n // 6 + 1, n - n // 6)))
            ang = np.arctan2(t[i, 1], t[i, 0]) + self.rng.choice([-1, 1]) * self.rng.uniform(0.5, 1.0)
            L = self.rng.uniform(0.12, 0.3) * n * 3.0
            m = max(4, int(L / 3))
            q = P[i] + np.stack([np.cos(ang + 0.3 * fbm1d(m, 8, 2, self._seed())), np.sin(ang + 0.3 * fbm1d(m, 8, 2, self._seed()))], 1).cumsum(0) * 3.0
            for j, (x, y) in enumerate(q):
                rr = width * 0.45 * (1 - j / m) * s + 0.4
                d.d.ellipse([x * s - rr, y * s - rr, x * s + rr, y * s + rr], fill=255)
        m = d.mask()
        slot = blur(m, 0.5)
        shoulder = blur(m, width * 1.6)
        self.h -= depth * slot + 2.2 * np.clip(shoulder * 2.2, 0, 1)
        self.crush *= (1 - slot)
        if seep:
            drip = self._runoff(np.clip(shoulder * 3, 0, 1), 260)
            coarse = Image.fromarray(self.rng.random((max(2, H // 90), max(2, W // 5))).astype(np.float32))
            fing = np.asarray(coarse.resize((W, H), Image.BICUBIC), np.float32)
            drip *= np.clip(0.3 + fing, 0, 1.2)
            self.v = np.clip(self.v + seep * 0.5 * drip * (1 - self.v), 0, 0.98)
            self.mn = np.clip(self.mn + seep * 0.6 * drip, 0, 1)
            if self.v0 is not None: self.v0 = np.maximum(self.v0, self.v)
        return self

    # ------------------------------------------------------------ hammer, grinder, age
    def _peck_sprites(self, size):
        key = round(float(size), 2)
        if key in self._sprites: return self._sprites[key]
        r = np.random.default_rng(1234 + int(key * 100))
        K, S = 48, int(np.ceil(5.2 * size)) * 2 + 1
        SS = 4
        c0 = S // 2
        yy, xx = (np.mgrid[0:S * SS, 0:S * SS].astype(np.float32) + 0.5) / SS - S / 2
        cov = np.zeros((K, S, S), np.float32); dep = np.zeros((K, S, S), np.float32)
        for k in range(K):
            rad = r.uniform(1.9, 4.6) * size
            m = r.integers(5, 9)
            ang = np.sort(r.uniform(0, 2 * np.pi, m))
            rr = rad * r.uniform(0.62, 1.18, m)
            pts = [(float((S / 2 + rr[i] * np.cos(ang[i])) * SS), float((S / 2 + rr[i] * np.sin(ang[i])) * SS)) for i in range(m)]
            im = Image.new('L', (S * SS, S * SS), 0)
            ImageDraw.Draw(im).polygon(pts, fill=255)
            hi = np.asarray(im, np.float32) / 255
            rho = np.hypot(xx, yy) / (rad * 1.12)
            bowl = np.clip(1 - rho ** 2, 0, 1) ** 0.55 * hi
            cov[k] = hi.reshape(S, SS, S, SS).mean((1, 3))
            dep[k] = bowl.reshape(S, SS, S, SS).mean((1, 3)) * r.uniform(0.7, 1.3)
        self._sprites[key] = (cov, dep, c0)
        return self._sprites[key]

    def _as_mask(self, glyph):
        return glyph.mask() if isinstance(glyph, Draft) else np.asarray(glyph, np.float32)

    def peck(self, glyph, density=1.0, size=1.0, depth=1.0, age=0.0, scatter=1.0, crush=1.0):
        """hammer a glyph (Draft or float mask) out of the varnish with irregular pits.
        density ~1 = solidly pecked, 0.4 = open stipple; size scales the pits; age 0 fresh .. 0.85 ghost"""
        M = self._as_mask(glyph)
        cov, dep, c0 = self._peck_sprites(size)
        K, S = cov.shape[0], cov.shape[1]
        ys, xs = np.nonzero(M > 0.02)
        if len(ys) == 0: return self
        pad = S + int(6 * scatter * size)
        y0, y1 = max(0, ys.min() - pad), min(self.H, ys.max() + pad + 1)
        x0, x1 = max(0, xs.min() - pad), min(self.W, xs.max() + pad + 1)
        sub = M[y0:y1, x0:x1]
        bh, bw = sub.shape
        soft = blur(sub, 1.3 * scatter * size)
        dens = 0.72 + 0.56 * noise2d(bh, bw, 45, 2, self._seed())
        prob = (smoothstep(0.30, 0.72, soft) + 0.05 * scatter * smoothstep(0.03, 0.3, soft)) * dens
        area = float(sub.sum())
        n_want = int(density * 3.4 * area / (np.pi * (3.25 * size) ** 2)) + 1
        r = self.rng
        cx, cy = [], []
        got, tries = 0, 0
        while got < n_want and tries < 40:
            m = int((n_want - got) * 2.5) + 16
            px = r.uniform(0, bw - 1, m); py = r.uniform(0, bh - 1, m)
            ok = r.random(m) < prob[py.astype(int), px.astype(int)]
            cx.append(px[ok]); cy.append(py[ok]); got += int(ok.sum()); tries += 1
        cx = np.concatenate(cx)[:n_want]; cy = np.concatenate(cy)[:n_want]
        # pits are stamped into a padded local buffer
        PB = S
        Hb, Wb = bh + 2 * PB, bw + 2 * PB
        D = np.zeros((Hb, Wb), np.float32); Sx = np.zeros((Hb, Wb), np.float32)
        Bs = np.zeros((Hb, Wb), np.float32); Cs = np.zeros((Hb, Wb), np.float32)
        ix = np.round(cx).astype(np.int64) + PB - c0; iy = np.round(cy).astype(np.int64) + PB - c0
        kk = r.integers(0, K, len(ix))
        bright = r.uniform(0.45, 1.0, len(ix)).astype(np.float32)
        oy, ox = np.mgrid[0:S, 0:S]
        idx = ((iy[:, None, None] + oy[None]) * Wb + (ix[:, None, None] + ox[None])).ravel()
        cv = cov[kk]
        np.add.at(D.ravel(), idx, dep[kk].ravel())
        np.add.at(Sx.ravel(), idx, (-np.log(1 - 0.93 * cv)).ravel())
        np.add.at(Bs.ravel(), idx, (cv * bright[:, None, None]).ravel())
        np.add.at(Cs.ravel(), idx, cv.ravel())
        crop = (slice(PB, PB + bh), slice(PB, PB + bw))
        D, Sx, Bs, Cs = D[crop], Sx[crop], Bs[crop], Cs[crop]
        R = 1 - np.exp(-Sx)                                      # share of varnish knocked off
        bri = np.clip(Bs / np.maximum(Cs, 1e-3), 0, 1)          # coverage-weighted whiteness of the pits
        dmax = 2.9 * depth * (1 - 0.4 * age)
        Deff = dmax * (1 - np.exp(-1.35 * D * depth / dmax))
        if age > 0:                                             # weathering rounds the pits off
            Deff = blur(Deff, 0.3 + 1.4 * age)
            R = blur(R, 0.6 * age)
        sl = (slice(y0, y1), slice(x0, x1))
        self.h[sl] -= Deff
        v = self.v[sl]; vref = (self.v0[sl] if self.v0 is not None else v)
        regrow = np.clip(age, 0, 1) ** 0.8 * 0.92 * vref        # old pecks re-varnish toward the rock around them
        self.v[sl] = v * (1 - R) + R * regrow
        fresh = R * (0.35 + 0.65 * bri) * crush * (1 - age) ** 1.6
        self.crush[sl] = np.maximum(self.crush[sl] * (1 - R * 0.5), fresh)
        return self

    def abrade(self, pts, width=8.0, depth=1.6, age=0.0, polish=1.0, smooth=False):
        """grind a V-groove along a polyline (incised lines, tally marks): smooth floor, fine striations along it"""
        P = spline(pts, 10) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32)
        pad = int(width + 4)
        X0, X1 = int(max(0, P[:, 0].min() - pad)), int(min(self.W, P[:, 0].max() + pad + 1))
        Y0, Y1 = int(max(0, P[:, 1].min() - pad)), int(min(self.H, P[:, 1].max() + pad + 1))
        if X1 <= X0 or Y1 <= Y0: return self
        box = (slice(Y0, Y1), slice(X0, X1))
        G = np.zeros((Y1 - Y0, X1 - X0), np.float32); STR = np.zeros_like(G)
        X = self.XX[box]; Y = self.YY[box]
        hw = width / 2
        for a, b in zip(P[:-1], P[1:]):
            d = b - a; L = float(np.linalg.norm(d))
            if L < 0.5: continue
            u = d / L; p = np.array([-u[1], u[0]], np.float32)
            al = (X - a[0]) * u[0] + (Y - a[1]) * u[1]; pe = (X - a[0]) * p[0] + (Y - a[1]) * p[1]
            hwv = hw * (1 + 0.12 * np.sin(al * 0.21 + float(self.rng.uniform(0, 6))))
            ends = smoothstep(-hw * 0.2, hw * 0.9, al) * smoothstep(L + hw * 0.2, L - hw * 0.9, al) if len(P) == 2 else \
                np.clip(1 - np.maximum(np.maximum(-al, al - L), 0) / hw, 0, 1)
            prof = np.clip(1 - np.abs(pe) / hwv, 0, 1) ** 0.85 * ends
            stri = 0.5 + 0.5 * np.sin(pe * 2 * np.pi / 1.4 + 2.5 * np.sin(al * 0.05))
            G = np.maximum(G, prof)
            STR = np.maximum(STR, stri * prof)
        G = blur(G, 0.5)
        self.h[box] -= depth * (1 - 0.35 * age) * G
        R = smoothstep(0.04, 0.45, G) * polish
        vref = (self.v0 if self.v0 is not None else self.v)[box]
        self.v[box] = self.v[box] * (1 - R) + R * (age ** 0.8 * 0.92 * vref)
        self.crush[box] = np.maximum(self.crush[box], R * (0.55 + 0.3 * STR) * (1 - age) ** 1.6)
        return self

    def abrade_tally(self, x, y, counts, gap=24.0, length=60.0, width=8.0, row_gap=None, slant=4.0, age=0.0,
                     strike_every=0, depth=1.6):
        """rows of ground tally marks (a day count). counts: marks per row; slant: px the tops lean; strike_every=5
        adds a cross-stroke through each group of five"""
        row_gap = row_gap or length * 1.45
        for ri, n in enumerate(counts):
            yy = y + ri * row_gap
            for i in range(n):
                xx = x + i * gap + self.rng.normal(0, 2.2)
                y_ = yy + self.rng.normal(0, 2.5)
                ln = length * self.rng.uniform(0.84, 1.1)
                sk = slant + self.rng.normal(0, 2.6)
                self.abrade([(xx + sk, y_), (xx - sk * 0.2, y_ + ln)], width * self.rng.uniform(0.82, 1.12),
                            depth * self.rng.uniform(0.8, 1.15), age)
                if strike_every and (i + 1) % strike_every == 0:
                    self.abrade([(xx - gap * (strike_every - 0.4), yy + ln * 0.62), (xx + gap * 0.45, yy + ln * 0.38)],
                                width * 0.85, depth, age)
        return self

    # ------------------------------------------------------------ glyph helpers (each returns a Draft)
    def _frame(self, x, y, size, facing=1, rot=0.0):
        c, s = np.cos(np.deg2rad(-rot)), np.sin(np.deg2rad(-rot))

        def T(pts):
            P = np.asarray(pts, np.float32) * size
            P[:, 0] *= facing
            return np.stack([x + P[:, 0] * c - P[:, 1] * s, y + P[:, 0] * s + P[:, 1] * c], 1)
        return T

    def bighorn(self, x, y, size, facing=1, kind='ram', gait=0.0, rot=0.0, into=None):
        """a bighorn sheep in profile (twisted-perspective horns), centred on its body. size ~ body + head length.
        kind: 'ram' (great curled horns), 'ewe' (short horns), 'lamb' (none); gait -1..1 swings the legs"""
        d = into or self.draft()
        T = self._frame(x, y, size, facing, rot)
        j = lambda: self.rng.normal(0, 0.012)
        body = [(-0.36, -0.12), (-0.18, -0.19 + j()), (0.06, -0.20 + j()), (0.24, -0.18), (0.34, -0.10), (0.36, 0.03),
                (0.27, 0.13), (0.0, 0.15 + j()), (-0.28, 0.13), (-0.40, 0.05), (-0.42, -0.05)]
        d.fill(T(body))
        w = 1.0 if kind != 'lamb' else 1.15
        d.stroke(T([(0.22, -0.12), (0.32, -0.24), (0.40, -0.32)]), 0.15 * size * w, 0.11 * size * w)
        d.fill(T([(0.34, -0.38), (0.47, -0.41), (0.57, -0.35), (0.635, -0.265), (0.55, -0.225), (0.43, -0.255), (0.33, -0.30)]))
        if kind == 'ram':
            d.stroke(T([(0.40, -0.38), (0.35, -0.52), (0.24, -0.59), (0.12, -0.55), (0.07, -0.44), (0.11, -0.35)]), 0.10 * size, 0.05 * size)
            d.stroke(T([(0.47, -0.40), (0.47, -0.55), (0.39, -0.66), (0.26, -0.70), (0.15, -0.66), (0.11, -0.58)]), 0.08 * size, 0.042 * size)
        elif kind == 'ewe':
            d.stroke(T([(0.41, -0.38), (0.38, -0.49), (0.30, -0.53)]), 0.075 * size, 0.04 * size)
            d.stroke(T([(0.47, -0.40), (0.47, -0.50), (0.40, -0.56)]), 0.06 * size, 0.035 * size)
        else:
            d.stroke(T([(0.42, -0.39), (0.38, -0.47)]), 0.06 * size, 0.045 * size)
        g = gait * 0.06
        lw = 0.064 * size * (1.15 if kind == 'lamb' else 1.0)
        ll = 0.46 if kind != 'lamb' else 0.50
        for (ax, ay), (bx, by) in [((0.27, 0.08), (0.31 + g, ll)), ((0.18, 0.10), (0.13 - g, ll)),
                                   ((-0.29, 0.08), (-0.25 + g, ll)), ((-0.37, 0.05), (-0.41 - g, ll))]:
            d.stroke(T([(ax, ay), ((ax + bx) / 2 + 0.01, (ay + by) / 2), (bx, by)]), lw * 1.1, lw * 0.85)
        d.stroke(T([(-0.40, -0.08), (-0.47, -0.17)]), 0.055 * size, 0.035 * size)
        return d

    def hunter(self, x, y, size, facing=1, weapon='bow', rot=0.0, into=None):
        """a stick-figure hunter, size = height. facing +1 looks right. weapon 'bow' (drawn, arrow nocked) or
        'atlatl' (dart raised over the head)"""
        d = into or self.draft()
        T = self._frame(x, y, size, facing, rot)
        d.dot(*T([(0.0, -0.405)])[0], 0.068 * size)
        d.stroke(T([(-0.005, -0.46), (-0.05, -0.53), (-0.07, -0.58)]), 0.035 * size, 0.022 * size)
        d.stroke(T([(0.025, -0.46), (0.04, -0.53), (0.03, -0.59)]), 0.035 * size, 0.022 * size)
        d.stroke(T([(0.0, -0.34), (0.005, -0.15), (0.0, 0.03)]), 0.078 * size, 0.062 * size)
        d.stroke(T([(0.0, 0.02), (0.09, 0.22), (0.13, 0.44), (0.19, 0.45)]), 0.06 * size, 0.05 * size)
        d.stroke(T([(0.0, 0.02), (-0.07, 0.22), (-0.15, 0.43), (-0.09, 0.45)]), 0.06 * size, 0.05 * size)
        if weapon == 'bow':
            d.stroke(T([(0.0, -0.28), (0.15, -0.265), (0.30, -0.255)]), 0.05 * size, 0.042 * size)
            d.stroke(T([(0.0, -0.28), (-0.10, -0.22), (-0.03, -0.255)]), 0.048 * size, 0.04 * size)
            d.stroke(T([(0.23, -0.53), (0.33, -0.40), (0.36, -0.255), (0.33, -0.11), (0.23, 0.02)]), 0.045 * size, 0.04 * size)
            d.stroke(T([(-0.03, -0.255), (0.50, -0.255)]), 0.034 * size, 0.034 * size, smooth=False)
            d.fill(T([(0.585, -0.255), (0.48, -0.30), (0.50, -0.255), (0.48, -0.21)]), smooth=False)
        else:
            d.stroke(T([(0.0, -0.28), (0.17, -0.20), (0.30, -0.25)]), 0.05 * size, 0.042 * size)
            d.stroke(T([(0.0, -0.29), (-0.13, -0.40), (-0.12, -0.53)]), 0.05 * size, 0.042 * size)
            d.stroke(T([(-0.34, -0.50), (0.55, -0.68)]), 0.034 * size, 0.034 * size, smooth=False)
            d.fill(T([(0.63, -0.70), (0.53, -0.72), (0.545, -0.68), (0.56, -0.64)]), smooth=False)
            for k in (0, 1):
                d.stroke(T([(-0.30 + k * 0.06, -0.51 - k * 0.012), (-0.34 + k * 0.06, -0.58 - k * 0.012)]), 0.026 * size, 0.022 * size, smooth=False)
                d.stroke(T([(-0.30 + k * 0.06, -0.51 - k * 0.012), (-0.36 + k * 0.06, -0.45 - k * 0.012)]), 0.026 * size, 0.022 * size, smooth=False)
        return d

    def sun_spiral(self, x, y, r, turns=3.0, rays=12, width=None, ray_len=(0.30, 0.46), into=None):
        """an Archimedean spiral sun ringed by short rays"""
        d = into or self.draft()
        w = width or r * 0.11
        th = np.linspace(1.4, 2 * np.pi * turns, int(70 * turns))
        rr = r * (0.10 + 0.90 * (th - th[0]) / (th[-1] - th[0]))
        d.stroke(np.stack([x + rr * np.cos(th), y + rr * np.sin(th)], 1), w * 0.85, w * 1.08, smooth=False)
        d.dot(x, y, w * 0.55)
        a0 = self.rng.uniform(0, 2 * np.pi)
        for i in range(rays):
            a = a0 + 2 * np.pi * i / rays + self.rng.normal(0, 0.05)
            r0 = r + w * 1.7; r1 = r0 + r * self.rng.uniform(*ray_len)
            d.stroke([(x + r0 * np.cos(a), y + r0 * np.sin(a)), (x + r1 * np.cos(a), y + r1 * np.sin(a))], w * 0.95, w * 0.8, smooth=False)
        return d

    def crescent(self, x, y, r, thick=0.42, rot=0.0, into=None):
        """a crescent moon, horns pointing away from rot (degrees ccw; 0 = horns to the left)"""
        d = into or self.draft()
        t = np.linspace(-np.pi / 2, np.pi / 2, 40)
        outer = np.stack([r * np.cos(t), r * np.sin(t)], 1)
        inner = np.stack([r * thick * np.cos(t[::-1]) * 1.0 + 0.0, r * np.sin(t[::-1])], 1)
        P = np.vstack([outer, inner])
        c, s = np.cos(np.deg2rad(-rot)), np.sin(np.deg2rad(-rot))
        P = np.stack([x + P[:, 0] * c - P[:, 1] * s, y + P[:, 0] * s + P[:, 1] * c], 1)
        d.fill(P, smooth=False)
        return d

    def concentric(self, x, y, r, rings=3, width=None, dot=True, into=None):
        """concentric rings (a waterhole / spring), optional centre dot"""
        d = into or self.draft()
        w = width or max(7.0, r * 0.16)
        for i in range(rings):
            rr = r * (i + 1) / rings
            if rr > w * 0.9: d.ring(x, y, rr, w)
        if dot: d.dot(x, y, w * 0.75)
        return d

    def hand(self, x, y, size, rot=0.0, outline=False, line=None, spread=1.0, into=None):
        """a hand (palm and five fingers, wrist down), size = wrist-to-fingertip; outline=True pecks only the contour"""
        d = into or self.draft()
        T = self._frame(x, y, size, 1, rot)
        h = Draft(self.W, self.H, seed=self._seed()) if outline else d
        h.fill(T([(-0.20, 0.15), (-0.21, -0.02), (-0.15, -0.14), (0.0, -0.17), (0.15, -0.14), (0.20, -0.02), (0.18, 0.16), (0.10, 0.27), (-0.10, 0.27)]))
        h.stroke(T([(-0.08, 0.25), (-0.07, 0.44)]), 0.17 * size, 0.15 * size)
        h.stroke(T([(0.07, 0.25), (0.06, 0.44)]), 0.17 * size, 0.15 * size)
        fingers = [((-0.17, 0.08), -62, 0.30, 0.105), ((-0.13, -0.10), -14, 0.37, 0.095), ((-0.03, -0.13), -3, 0.41, 0.095),
                   ((0.07, -0.12), 9, 0.38, 0.09), ((0.15, -0.07), 24, 0.29, 0.082)]
        for (bx, by), ang, ln, wd in fingers:
            a = np.deg2rad(ang * spread)
            ex, ey = bx + np.sin(a) * ln, by - np.cos(a) * ln
            h.stroke(T([(bx, by), ((bx + ex) / 2 + 0.005, (by + ey) / 2), (ex, ey)]), wd * size, wd * size * 0.85)
        if outline:
            m = h.mask()
            lw = line or size * 0.07
            inner = smoothstep(0.88, 0.99, blur(m, lw * 0.55))
            d.add(np.clip(m - inner, 0, 1) * smoothstep(0.1, 0.5, m))
        return d

    def hoofprints(self, pts, size=16.0, every=34.0, stagger=7.0, into=None):
        """a trail of cloven hoofprints (two teardrops each) walking along `pts`"""
        d = into or self.draft()
        P = _resample(spline(pts, 12) if len(pts) > 2 else pts, every)
        for i in range(len(P)):
            a = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
            a = a / (np.linalg.norm(a) + 1e-6)
            nrm = np.array([-a[1], a[0]])
            c = P[i] + nrm * stagger * (1 if i % 2 else -1) + self.rng.normal(0, 1.2, 2)
            for side in (-1, 1):
                heel = c - a * size * 0.36 + nrm * side * size * 0.27
                mid = c + a * size * 0.02 + nrm * side * size * 0.24
                tip = c + a * size * 0.42 + nrm * side * size * 0.09
                d.stroke([heel, mid, tip], size * 0.34, size * 0.14, wobble=0.04)
        return d

    def meander(self, pts, width, end_width=None, smooth=True, into=None):
        """any pecked line: a wavy river, a path, a zigzag (smooth=False keeps the corners)"""
        d = into or self.draft()
        return d.stroke(pts, width, end_width, smooth=smooth)

    # ------------------------------------------------------------ weathering
    def _scallops(self, pts, chunk=(14, 40), bow=0.16):
        """conchoidal edge: the outline is broken into short chunks, each bowing inward as a small scallop"""
        P = np.asarray(pts, np.float32)
        Q = np.roll(P, -1, 0)
        sgn = 1.0 if float((P[:, 0] * Q[:, 1] - Q[:, 0] * P[:, 1]).sum()) > 0 else -1.0
        out = []
        for i in range(len(P)):
            a, b = P[i], P[(i + 1) % len(P)]
            dd = b - a; L = float(np.linalg.norm(dd)) + 1e-6
            nrm = sgn * np.array([-dd[1], dd[0]]) / L               # inward, whichever way the outline winds
            cuts = [0.0]
            while cuts[-1] < L:
                cuts.append(cuts[-1] + self.rng.uniform(*chunk))
            cuts = np.array(cuts[:-1] + [L]) / L
            for t0, t1 in zip(cuts[:-1], cuts[1:]):
                seg = (t1 - t0) * L
                t = np.linspace(0, 1, max(3, int(seg / 3)), endpoint=False)
                b_ = 4 * t * (1 - t) * bow * seg * self.rng.uniform(0.3, 1.3)
                tt = t0 + (t1 - t0) * t
                jit = self.rng.normal(0, 1.2)
                out.append(a + dd * tt[:, None] + nrm * (b_ + jit * (t < 0.01) + self.rng.normal(0, 0.35, len(t)))[:, None])
        return np.vstack(out)

    def spall(self, pts, depth=7.0, impact=None, stone=SCAR, age=0.0):
        """a flake of the face has broken off: step-down scar with a scalloped lip, conchoidal ripples, fresh stone.
        pts: rough outline (either winding); age 0 = fresh orange scar .. 0.6 = partly re-varnished"""
        H, W = self.H, self.W
        P = self._scallops(pts)
        im = Image.new('L', (W * 2, H * 2), 0)
        ImageDraw.Draw(im).polygon([(float(x) * 2, float(y) * 2) for x, y in P], fill=255)
        M = np.asarray(im.resize((W, H), Image.BILINEAR), np.float32) / 255
        M = blur(M, 0.4)
        ys, xs = np.nonzero(M > 0.01)
        if len(ys) == 0: return self
        cx, cy = (impact if impact is not None else (xs.mean(), ys.mean()))
        dist = np.hypot(self.XX - cx, self.YY - cy)
        rmax = float(np.percentile(np.hypot(xs - cx, ys - cy), 98)) + 1
        warp = noise2d(H, W, 70, 2, self._seed())
        ripple = 1.1 * np.sin(dist / 7.5 + warp * 4) * np.exp(-dist / (rmax * 0.8))       # conchoidal rings
        bowl = depth * (0.7 + 0.3 * np.clip(1 - dist / rmax, 0, 1)) * (0.85 + 0.3 * noise2d(H, W, 120, 2, self._seed()))
        base = blur(self.h, 12) - bowl + ripple
        g = self.rng.random((H, W), dtype=np.float32)
        base += (blur(g, 0.6) - 0.5) * 0.8                                                  # a fresh break is smoother
        self.h = self.h * (1 - M) + base * M
        sc = _c(stone)
        band = 0.5 + 0.5 * np.sin(dist / 13.0 + 4 * noise2d(H, W, 180, 2, self._seed()))   # Liesegang-like iron bands
        tone = noise2d(H, W, 90, 3, self._seed())
        sc_map = sc * (0.90 + 0.12 * band + 0.1 * (tone - 0.5))[..., None]
        rind = np.clip(M - smoothstep(0.6, 0.98, blur(M, 3.5)), 0, 1)                       # pale weathering rind at the lip
        sc_map = sc_map * (1 - 0.6 * rind[..., None]) + hexc(STONE_PALE) * 1.08 * 0.6 * rind[..., None]
        self.rockc = self.rockc * (1 - M[..., None]) + sc_map * M[..., None]
        film = (0.04 + 0.75 * age) * (self.v0 if self.v0 is not None else self.v) * (0.5 + noise2d(H, W, 40, 2, self._seed()))
        self.v = self.v * (1 - M) + M * np.clip(film, 0, 0.95)
        self.crush *= (1 - M)
        if self.pa is not None: self.pa *= (1 - M)
        return self

    def lichen(self, x, y, r, kind='green', n=5, raise_=0.5):
        """a cluster of crustose lichen rosettes around (x, y) within r: lobed rims, areolate (cracked) centres,
        tiny dark fruiting discs. kind: 'green' (yellow-green map lichen), 'orange', 'grey' or a colour"""
        H, W = self.H, self.W
        if self.paint is None:
            self.paint = np.zeros((H, W, 3), np.float32); self.pa = np.zeros((H, W), np.float32)
        c0, c1 = (hexc(LICHEN[kind][0]), hexc(LICHEN[kind][1])) if kind in LICHEN else (_c(kind), _c(kind) * 1.15)
        d = Draft(W, H, seed=self._seed())
        cents = []
        for i in range(n):
            a = self.rng.uniform(0, 2 * np.pi); rr = r * np.sqrt(self.rng.random())
            px, py = x + rr * np.cos(a), y + rr * np.sin(a)
            rad = self.rng.uniform(0.14, 0.34) * r
            cents.append((px, py, rad))
            t = np.linspace(0, 2 * np.pi, 160, endpoint=False)
            k = self.rng.integers(9, 16)
            lobes = 1 + 0.14 * np.abs(np.sin(t * k / 2 + self.rng.uniform(0, 3))) ** 0.6 + 0.3 * fbm1d(160, 40, 3, self._seed())
            ex, rot_ = self.rng.uniform(0.65, 1.0), self.rng.uniform(0, np.pi)
            u, w_ = rad * lobes * np.cos(t), rad * lobes * np.sin(t) * ex
            d.fill(np.stack([px + u * np.cos(rot_) - w_ * np.sin(rot_), py + u * np.sin(rot_) + w_ * np.cos(rot_)], 1), smooth=False)
            for _ in range(int(self.rng.integers(2, 6))):                                  # young satellite thalli
                b = self.rng.uniform(0, 2 * np.pi); q = rad * self.rng.uniform(1.1, 1.6)
                d.dot(px + q * np.cos(b), py + q * np.sin(b), self.rng.uniform(1.2, 0.22 * rad + 1.3))
        m = d.mask()
        x0, x1 = int(max(0, x - r * 1.6)), int(min(W, x + r * 1.6 + 1)); y0, y1 = int(max(0, y - r * 1.6)), int(min(H, y + r * 1.6 + 1))
        sl = (slice(y0, y1), slice(x0, x1))
        mb = m[sl]; bh, bw = mb.shape
        rim = np.clip(mb - smoothstep(0.7, 0.98, blur(mb, 2.5)), 0, 1)
        cell = noise2d(bh, bw, 5, 2, self._seed())
        cracks = smoothstep(0.035, 0.0, np.abs(cell - 0.5)) * (1 - rim)                     # areoles
        speck = noise2d(bh, bw, 3, 1, self._seed())
        col = c0 * (1 - rim[..., None]) + c1 * rim[..., None]
        col = col * (0.82 + 0.3 * speck)[..., None] * (1 - 0.55 * cracks)[..., None]
        for (px, py, rad) in cents:                                                          # fruiting discs
            for _ in range(int(rad * 0.5)):
                b = self.rng.uniform(0, 2 * np.pi); q = rad * 0.6 * np.sqrt(self.rng.random())
                fx, fy = px + q * np.cos(b) - x0, py + q * np.sin(b) - y0
                if 1 <= fx < bw - 2 and 1 <= fy < bh - 2:
                    col[int(fy):int(fy) + 2, int(fx):int(fx) + 2] *= 0.45
        a = mb * (0.7 + 0.28 * speck)
        self.paint[sl] = self.paint[sl] * (1 - a[..., None]) + col * a[..., None]
        self.pa[sl] = np.maximum(self.pa[sl], a)
        self.h[sl] += raise_ * blur(mb, 1.0) - 0.4 * cracks
        return self

    # ------------------------------------------------------------ light and output
    def albedo(self):
        cr = self.crush[..., None]
        fresh = self.rockc * (1 - 0.48 * cr) + hexc(CRUSH) * 0.48 * cr
        vc = hexc(VARNISH_FE) * (1 - self.mn[..., None]) + hexc(VARNISH_MN) * self.mn[..., None]
        v = self.v[..., None]
        alb = fresh * (1 - v) + vc * v
        if self.pa is not None:
            alb = alb * (1 - self.pa[..., None]) + self.paint * self.pa[..., None]
        return alb

    def composite(self, sun=1.0, sky=0.42, shadow=0.82, vignette=0.22):
        h = blur(self.h, 0.55)
        N = height_normals(h)
        L = self.L
        ndl = np.clip(N[..., 0] * L[0] + N[..., 1] * L[1] + N[..., 2] * L[2], 0, 1)
        del N
        P = 58                                                    # pad by edge so the frame border casts no shadow
        sh = height_shadow(np.pad(h, P, mode='edge'), tuple(L), reach=56, step=1.0, soft=0.9)[P:-P, P:-P]
        ao = ambient_occlusion(h, radii=(2, 6, 18), depth=(2.4, 7.0, 22.0))
        direct = (ndl / L[2]) * (1 - shadow * sh)
        light = SKY[None, None, :] * (sky * (1 - 0.6 * ao))[..., None] + SUN[None, None, :] * (sun * 0.66 * direct)[..., None]
        img = self.albedo() * light
        r = np.hypot((self.XX - self.W * 0.45) / self.W, (self.YY - self.H * 0.42) / self.H)
        img *= (1 - vignette * r ** 2 * 2.0)[..., None]
        img = np.clip(img, 0, 1) ** 0.96
        return Image.fromarray((img * 255 + 0.5).astype(np.uint8))

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
