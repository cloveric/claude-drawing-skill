"""tomb -- an Egyptian tomb wall painting, Theban New Kingdom style (numpy + Pillow only).

The wall is built the way the painters of the Theban necropolis built it, layer by layer, and every layer stays
in memory so that 3,300 years of damage can later take the top ones away again.

Model:
  wall      rough mud plaster (brown, chopped straw, grit) under a thin skin of fine gypsum plaster (warm white,
            trowel undulation, pits); `under` keeps this plaster plus everything drawn straight onto it.
  grid      before anything was drawn, red-ochre cords were snapped onto the plaster: a squared grid whose cell is
            one canon unit of the figures in that area (18 units from sole to hairline), plus register guide lines.
  sketch    the outline draughtsman drew every figure, animal, plant and sign in thin red ochre, searching a
            little (a second, lighter pass a pixel or two off); hidden parts are sketched too.
  ground    the background wash (yellow ochre, or the bluish white of some tombs) brushed round the figures in
            broad, patchy sweeps -- the shapes still to be coloured are left as bare plaster with their red sketch;
            the wash is not perfectly opaque, so streaks of plaster and the grid ghost through.
  colour    secco (dry) painting, one pigment pot at a time: red-ochre skin of men, yellow ochre of women, white
            linen, orpiment yellow, Egyptian blue (coarse, glittery grains), green frit, carbon black.  Each fill is
            flat and matte with brush streaks, mottling and grain; edges wander a pixel over or short of the line.
            Fills are z-ordered (a per-pixel z map), so pigments can be laid in any order and still overlap right.
            Linen can be translucent: the leg shows through a pleated overkilt.
  ink       the final outline: confident, nearly even lines (red-brown round the skin, black everywhere else)
            masked by whatever is painted above them, so overlapping parts read correctly.
  canon     figures follow the composite view: profile head with a frontal eye and kohl line, frontal shoulders and
            collar, torso turning to profile at the waist, profile legs with both feet seen from the big-toe side.
            Poses are joint positions in canon units (sole = 0, hairline = 18), elbows found by two-bone IK.
  props     what the figures hold and work with, each anchored to the figure's hands / canon units: staff, sickle,
            the inverted-V hoe, plough rods, baskets, tied grain sacks, a grain measure (heqat) with a poured stream,
            winnowing scoops, papyrus and palette; long-horned oxen (far legs a step apart so all four show), a
            standing emmer field with stubble and stalks gathered into a reaper's fist, sheaves, grain heaps,
            a sycamore with scale-like rows of leaves and a waterskin, papyrus clumps.
  frame     the decorative system round the scenes: block border, kheker frieze, striped register bands, a river
            band with zigzag water, fish and lotus.
  text      hieroglyphs drawn as small polychrome signs (reed leaf, water, mouth, loaf, chick, owl, viper, foot,
            basket, house, hand, cloth, sun, sickle, grain, jar, scroll, pool, flax, bolt, hoe, numerals ...),
            laid out in columns by quadrats (tall signs paired, flat signs stacked).  The text is pseudo-text.
  age       what time does: paint flakes off in clusters (blue and the crack edges first), deeper flakes down to the
            plaster (where the red grid and sketch reappear; `zones` places a few on purpose), paint rubbed thin in
            soft patches, plaster losses down to the straw-tempered mud as a real height field (a broken gypsum rim,
            paint flaked back in steps around it, cast shadow on the upper-left inner wall), cracks with a dark
            groove and a lit lip, blue decaying toward grey-green, soot and grime near the ceiling, a moisture
            tide-line and salt bloom near the floor, fly specks, a lamp-lit falloff to the corners.

    from tomb import TombPainting
    tp = TombPainting(1920, 1080, seed=3)
    tp.wall(); tp.grid((100, 100, 900, 600), cell=12, base=600)
    f = tp.figure(400, 600, 216, 'walk', facing=1)          # declare (nothing is painted yet)
    tp.column(600, 120, 650, 560, n=7)                       # a column of pseudo-hieroglyphs
    tp.sketch(); tp.ground('#d8bd84')
    tp.colour(); tp.ink(); tp.colour(layer='text'); tp.ink(layer='text')
    tp.age(); tp.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, shift, height_shadow

PIGMENTS = {
    'skin': '#a24e2c',      # red ochre: men
    'skin_f': '#d6a45a',    # yellow ochre: women
    'red': '#ad4129',
    'brown': '#7b4a2c',
    'ochre': '#c48a3a',
    'yellow': '#dfb245',    # orpiment
    'linen': '#ebe2cc',
    'white': '#efe8d8',
    'blue': '#2c5d9a',      # Egyptian blue
    'lblue': '#6f9cc4',
    'green': '#3b8566',     # green frit / malachite
    'lgreen': '#7eaa6a',
    'dkgreen': '#2f6e50',
    'black': '#211c1a',
    'grey': '#8d8b84',
}
INK, REDLINE, SKETCH = '#201a17', '#5e2412', '#b3533a'

#              mottle  streak  grain   opacity  thin   (thin: how much a streak thins the coat)
_TEX = {'skin': (0.07, 0.05, 0.04, 0.97, 0.05), 'skin_f': (0.07, 0.05, 0.04, 0.96, 0.06),
        'red': (0.07, 0.05, 0.05, 0.97, 0.05), 'brown': (0.08, 0.05, 0.05, 0.97, 0.04),
        'ochre': (0.07, 0.05, 0.05, 0.96, 0.05), 'yellow': (0.06, 0.05, 0.06, 0.95, 0.07),
        'linen': (0.035, 0.04, 0.018, 0.90, 0.10), 'white': (0.035, 0.04, 0.02, 0.93, 0.08),
        'blue': (0.10, 0.06, 0.06, 0.97, 0.04), 'lblue': (0.08, 0.05, 0.05, 0.95, 0.05),
        'green': (0.09, 0.06, 0.05, 0.97, 0.04), 'lgreen': (0.08, 0.05, 0.05, 0.95, 0.05),
        'dkgreen': (0.08, 0.05, 0.12, 0.97, 0.04),
        'black': (0.05, 0.06, 0.04, 0.97, 0.04), 'grey': (0.06, 0.05, 0.05, 0.95, 0.05)}


_CRYST = {'blue': 0.22, 'lblue': 0.14, 'green': 0.15, 'lgreen': 0.1, 'dkgreen': 0.12}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str):
        return hexc(PIGMENTS.get(c, c))
    return np.asarray(c, np.float32)


def _closed_spline(pts, per=8):
    P = np.asarray(pts, np.float32)
    ext = np.vstack([P[-2:], P, P[:2]])
    out = spline(ext, per)
    return out[2 * per:-2 * per - 1] if len(out) > 4 * per + 1 else out


def _rot(v, a):
    c, s = np.cos(a), np.sin(a)
    v = np.asarray(v, np.float32)
    return np.stack([v[..., 0] * c - v[..., 1] * s, v[..., 0] * s + v[..., 1] * c], -1)


def _ik(S, W, a, b, bend):
    """two-bone IK: joint between S and W with bone lengths a, b; bend = +1/-1 picks the side"""
    S, W = np.asarray(S, np.float32), np.asarray(W, np.float32)
    d = W - S; L = float(np.hypot(*d))
    L = min(max(L, abs(a - b) + 1e-3), a + b - 1e-3)
    u = d / (np.hypot(*d) + 1e-9)
    x = (a * a - b * b + L * L) / (2 * L)
    h = np.sqrt(max(a * a - x * x, 0))
    n = np.array([-u[1], u[0]], np.float32) * bend
    return S + u * x + n * h


def _arc(P):
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    return s


def _limb(joints, wf, wb, per=10, cap0=False):
    """tapered limb along a smooth path through `joints` (units, y up).
    wf / wb: lists of (fraction of path length, half width) for the front (+x-ish) and back sides.
    returns (polygon, outline paths without the end caps)"""
    P = spline(np.asarray(joints, np.float32), per)
    s = _arc(P); t = s / (s[-1] + 1e-9)
    T = np.gradient(P, axis=0); T /= np.hypot(T[:, 0], T[:, 1])[:, None] + 1e-9
    N = np.stack([-T[:, 1], T[:, 0]], 1)
    hf = np.interp(t, [k for k, _ in wf], [v for _, v in wf])
    hb = np.interp(t, [k for k, _ in wb], [v for _, v in wb])
    if np.mean(N[:, 0]) < 0: hf, hb = hb, hf                     # left normal points backward: swap sides
    A = P + N * hf[:, None]; B = P - N * hb[:, None]
    paths = [A, B]
    poly = np.vstack([A, B[::-1]])
    if cap0:                                                     # rounded end (shoulder): A[0] -> around the back -> B[0]
        r = (hf[0] + hb[0]) / 2
        ang0 = np.arctan2(N[0, 1], N[0, 0])
        th = np.linspace(ang0, ang0 + np.pi, 14)
        cap = P[0] + np.stack([np.cos(th), np.sin(th)], 1) * r
        poly = np.vstack([A, B[::-1], cap[::-1][1:-1]])
        paths = [np.vstack([A[::-1], cap[1:-1], B])]
    return poly, paths


# --------------------------------------------------------------------------- figure poses (canon units, x forward)
POSES = {
    # hip, lean (deg, + = forward), lead leg (knee, ankle, foot angle), back leg, wrists, elbow bends, hands
    'stand': dict(hip=(0.0, 9.0), lean=0, kf=(0.9, 5.9), af=(1.6, 0.85), kb=(-0.4, 5.9), ab=(-0.85, 0.85),
                  wf=(2.75, 8.7), wb=(-2.75, 8.7), bf=-1, bb=1, hf='open', hb='open'),
    'walk': dict(hip=(0.0, 9.0), lean=0, kf=(1.35, 5.9), af=(2.9, 0.85), kb=(-0.45, 5.9), ab=(-0.95, 0.85),
                 wf=(2.8, 8.7), wb=(-2.7, 8.7), bf=-1, bb=1, hf='open', hb='open'),
    'staff': dict(hip=(0.0, 9.0), lean=0, kf=(1.55, 5.9), af=(3.3, 0.85), kb=(-0.45, 5.9), ab=(-0.95, 0.85),
                  wf=(6.2, 13.4), wb=(-2.7, 8.8), bf=-1, bb=1, hf='fist', hb='fist'),
    'plough': dict(hip=(0.0, 8.7), lean=24, kf=(2.0, 5.5), af=(3.1, 0.85), kb=(-1.1, 5.4), ab=(-2.9, 0.85),
                   fb=22, wf=(7.3, 9.6), wb=(6.6, 9.2), bf=-1, bb=-1, hf='fist', hb='fist', cross=True),
    'reap': dict(hip=(0.0, 8.2), lean=36, kf=(2.2, 5.1), af=(3.0, 0.85), kb=(-1.0, 5.0), ab=(-2.1, 0.85),
                 fb=12, wf=(7.4, 9.0), wb=(6.5, 7.5), bf=-1, bb=-1, hf='fist', hb='fist', cross=True),
    'sow': dict(hip=(0.0, 9.0), lean=6, kf=(1.4, 5.9), af=(3.0, 0.85), kb=(-0.5, 5.9), ab=(-1.1, 0.85),
                fb=8, wf=(6.6, 11.6), wb=(-1.0, 10.6), bf=-1, bb=1, hf='open', hb='fist'),
    'hoe': dict(hip=(0.0, 8.4), lean=40, kf=(2.2, 5.3), af=(3.2, 0.85), kb=(-1.0, 5.2), ab=(-2.4, 0.85),
                fb=15, wf=(6.4, 8.4), wb=(4.9, 9.9), bf=-1, bb=-1, hf='fist', hb='fist', cross=True),
    'glean': dict(hip=(0.0, 8.6), lean=48, kf=(1.9, 5.4), af=(2.6, 0.85), kb=(-0.6, 5.3), ab=(-1.4, 0.85),
                  fb=10, wf=(7.0, 3.6), wb=(4.6, 6.4), bf=-1, bb=-1, hf='open', hb='fist', cross=True),
    'carry': dict(hip=(0.0, 9.0), lean=3, kf=(1.35, 5.9), af=(2.85, 0.85), kb=(-0.45, 5.9), ab=(-1.0, 0.85),
                  fb=6, wf=(2.9, 8.9), wb=(-2.7, 18.7), bf=-1, bb=1, hf='open', hb='fist'),
    'hold': dict(hip=(0.0, 9.0), lean=4, kf=(1.2, 5.9), af=(2.5, 0.85), kb=(-0.45, 5.9), ab=(-0.9, 0.85),
                 wf=(5.2, 10.6), wb=(4.4, 9.9), bf=-1, bb=-1, hf='fist', hb='fist', cross=True),
    'scoop': dict(hip=(0.0, 8.5), lean=34, kf=(2.0, 5.4), af=(2.9, 0.85), kb=(-1.0, 5.3), ab=(-2.0, 0.85),
                  fb=10, wf=(7.0, 10.6), wb=(6.0, 8.6), bf=-1, bb=-1, hf='fist', hb='fist', cross=True),
    'squat': dict(hip=(0.0, 1.35), lean=0, kf=(2.55, 4.95), af=(3.0, 0.85), kb=(3.7, 0.95), ab=(-0.25, 0.72),
                  mb=True, wf=(4.3, 5.75), wb=(3.0, 6.9), bf=-1, bb=-1, hf='fist', hb='fist', cross=True, seated=True,
                  turn=0.45),
}


class TombPainting:
    def __init__(self, W=1920, H=1080, seed=0, ss=3, light=(-0.6, -0.8)):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.light = np.asarray(light, np.float32) / np.hypot(*light)
        self.parts = []
        self._z = 1.0
        self.stages = []
        self.zmap = np.full((H, W), -1.0, np.float32)
        self.bluemap = np.zeros((H, W), np.float32)
        self.paintmap = np.zeros((H, W), np.float32)
        sd = self._seed
        self.T_mottle = noise2d(H, W, 80, 4, sd())
        g = self.rng.random((H, W)).astype(np.float32)
        self.T_grain = np.clip((blur(g, 0.6) - 0.5) * 3.2 + 0.5, 0, 1)
        self.T_edge = noise2d(H, W, 5, 2, sd())
        c = self.rng.random((H, W)).astype(np.float32)
        self.T_cryst = blur((c > 0.94).astype(np.float32), 0.45) * 1.6 - blur((c < 0.05).astype(np.float32), 0.45) * 1.2
        self.T_streak = {'h': self._streak(False), 'v': self._streak(True)}
        self.img = np.ones((H, W, 3), np.float32) * hexc('#e4d9c3')
        self.under = self.img.copy()
        self.ground_img = self.img.copy()
        self.plaster = self.img.copy()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _streak(self, vertical):
        H, W = self.H, self.W
        out = np.zeros((H, W), np.float32)
        for k, (a, b, amp) in enumerate([(3, 60, 1.0), (2, 22, 0.6), (8, 140, 0.5)]):
            if vertical:
                g = self.rng.random((H // b + 2, W // a + 2)).astype(np.float32)
            else:
                g = self.rng.random((H // a + 2, W // b + 2)).astype(np.float32)
            out += amp * np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC), np.float32)
        out -= out.min(); out /= out.max() + 1e-6
        return out

    # ------------------------------------------------------------------ raster helpers
    def _bbox(self, P, pad):
        x0 = int(max(0, np.floor(P[:, 0].min() - pad))); x1 = int(min(self.W, np.ceil(P[:, 0].max() + pad)))
        y0 = int(max(0, np.floor(P[:, 1].min() - pad))); y1 = int(min(self.H, np.ceil(P[:, 1].max() + pad)))
        return x0, y0, x1, y1

    def _poly_mask(self, polys, holes=(), box=None):
        allp = np.vstack([np.asarray(p, np.float32) for p in polys])
        x0, y0, x1, y1 = box or self._bbox(allp, 3)
        if x1 <= x0 or y1 <= y0: return None
        S = self.ss
        im = Image.new('L', ((x1 - x0) * S, (y1 - y0) * S), 0)
        d = ImageDraw.Draw(im)
        for p, f in [(p, 255) for p in polys] + [(h, 0) for h in holes]:
            p = np.asarray(p, np.float32)
            if len(p) < 3: continue
            d.polygon([((x - x0) * S, (y - y0) * S) for x, y in p], fill=f)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return m, (x0, y0, x1, y1)

    def _stroke_mask(self, paths, width, closed=False, var=0.14, taper=0.0, seed=0, box=None, jitter=0.0):
        paths = [np.asarray(p, np.float32) for p in paths if len(p) >= 2]
        if not paths: return None
        allp = np.vstack(paths)
        x0, y0, x1, y1 = box or self._bbox(allp, width + 3 + jitter)
        if x1 <= x0 or y1 <= y0: return None
        S = self.ss
        im = Image.new('L', ((x1 - x0) * S, (y1 - y0) * S), 0)
        d = ImageDraw.Draw(im)
        r = np.random.default_rng(seed)
        for P in paths:
            if closed: P = np.vstack([P, P[:1]])
            s = _arc(P); L = s[-1]
            if L < 0.5: continue
            n = max(2, int(L / max(0.45, width * 0.3)) + 1)
            ss_ = np.linspace(0, L, n)
            px = np.interp(ss_, s, P[:, 0]); py = np.interp(ss_, s, P[:, 1])
            if jitter:
                px = px + fbm1d(n, max(6, n / max(1, L / 30)), 2, int(r.integers(1 << 30))) * jitter
                py = py + fbm1d(n, max(6, n / max(1, L / 30)), 2, int(r.integers(1 << 30))) * jitter
            wv = width * (1 + var * fbm1d(n, max(4, n / max(1, L / 50)), 2, int(r.integers(1 << 30))))
            if taper and not closed:
                tp = np.clip(np.minimum(ss_, L - ss_) / max(taper, 1e-3), 0, 1)
                wv = wv * (0.35 + 0.65 * tp)
            rad = np.maximum(wv * 0.5 * S, 0.6)
            X = (px - x0) * S; Y = (py - y0) * S
            for xi, yi, ri in zip(X, Y, rad):
                d.ellipse([xi - ri, yi - ri, xi + ri, yi + ri], fill=255)
        m = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return m, (x0, y0, x1, y1)

    # ------------------------------------------------------------------ the wall
    def wall(self, plaster='#e6dcc6', mud='#74563c'):
        """mud plaster under a skin of fine gypsum plaster"""
        H, W = self.H, self.W
        sd = self._seed
        # mud: brown, lumpy, chopped straw and grit
        m = np.ones((H, W, 3), np.float32) * hexc(mud)
        lump = noise2d(H, W, 18, 4, sd())
        m *= (0.72 + 0.45 * lump)[..., None]
        m *= (0.84 + 0.3 * self.T_grain)[..., None]
        straw = Image.new('L', (W, H), 0); d = ImageDraw.Draw(straw)
        r = self.rng
        for _ in range(int(W * H / 900)):
            x, y = r.uniform(0, W), r.uniform(0, H); a = r.uniform(0, np.pi); L = r.uniform(4, 16)
            d.line([(x, y), (x + np.cos(a) * L, y + np.sin(a) * L)], fill=int(r.uniform(90, 200)), width=1)
        st = np.asarray(straw, np.float32) / 255
        m = m * (1 - 0.55 * st[..., None]) + hexc('#c9a86c') * 0.55 * st[..., None]
        grit = (r.random((H, W)) > 0.985).astype(np.float32)
        m *= (1 - 0.35 * blur(grit, 0.5))[..., None]
        hm = blur(lump, 1.0) * 10 + blur(noise2d(H, W, 4, 2, sd()), 0.6) * 2.5
        gy, gx = np.gradient(hm)
        m *= np.clip(1 + 1.1 * (gx * self.light[0] + gy * self.light[1]), 0.55, 1.45)[..., None]
        self.mud = np.clip(m, 0, 1)
        # gypsum plaster skin
        p = np.ones((H, W, 3), np.float32) * hexc(plaster)
        und = noise2d(H, W, 260, 3, sd())                      # trowel undulation
        stain = noise2d(H, W, 140, 4, sd())
        p *= (0.95 + 0.07 * und)[..., None]
        p = p * (1 - 0.08 * smoothstep(0.55, 0.85, stain)[..., None]) + hexc('#d7b98e') * 0.08 * smoothstep(0.55, 0.85, stain)[..., None]
        relief = blur(noise2d(H, W, 7, 3, sd()), 1.2) * 1.2 + und * 8
        pits = (r.random((H, W)) > 0.998).astype(np.float32)
        relief -= blur(pits, 0.9) * 2
        gy, gx = np.gradient(relief)
        p *= np.clip(1 + 0.3 * (gx * self.light[0] + gy * self.light[1]), 0.88, 1.12)[..., None]
        p *= (0.985 + 0.03 * self.T_grain)[..., None]
        self.plaster = np.clip(p, 0, 1)
        self.under = self.plaster.copy()
        self.img = self.plaster.copy()
        self.ground_img = self.img.copy()

    def _draw_under(self, m, box, colour, alpha):
        x0, y0, x1, y1 = box
        col = _c(colour)
        a = (m * alpha)[..., None]
        for buf in (self.under, self.img):
            sl = buf[y0:y1, x0:x1]
            sl[:] = sl * (1 - a) + col * a

    def grid(self, box, cell, base=None, colour=SKETCH, alpha=0.42, width=1.1):
        """red-ochre squaring grid snapped onto the plaster, aligned to a baseline"""
        x0, y0, x1, y1 = box
        base = y1 if base is None else base
        paths = []
        k0 = int(np.floor((y0 - base) / cell)); k1 = int(np.ceil((y1 - base) / cell))
        for k in range(k0, k1 + 1):
            y = base + k * cell
            if y0 - 0.5 <= y <= y1 + 0.5: paths.append(np.array([[x0, y], [x1, y]], np.float32))
        x = x0
        while x <= x1 + 0.5:
            paths.append(np.array([[x, y0], [x, y1]], np.float32)); x += cell
        res = self._stroke_mask(paths, width, var=0.25, seed=self._seed())
        if res:
            m, b = res
            m = m * (0.6 + 0.4 * self.T_mottle[b[1]:b[3], b[0]:b[2]])
            self._draw_under(m, b, colour, alpha)

    def guide(self, p0, p1, colour=SKETCH, alpha=0.5, width=1.2):
        res = self._stroke_mask([np.array([p0, p1], np.float32)], width, var=0.3, seed=self._seed())
        if res: self._draw_under(res[0], res[1], colour, alpha)

    # ------------------------------------------------------------------ parts (declared, painted later)
    def part(self, pts=None, colour=None, outline=True, paths=None, closed=None, ink=None, width=None,
             z=None, alpha=None, clip=None, holes=(), layer='scene', sketch=True, streak=None, rag=1.0):
        """declare one painted shape.  pts: polygon (screen px) or None for a pure line part.
        outline: True -> ink the polygon boundary; paths: explicit ink paths instead (open unless closed=True).
        colour: pigment name (PIGMENTS key) or '#rrggbb'.  clip: polygon or list of polygons that limit fill & ink.
        z: stacking order (default: next).  Returns the part dict."""
        if z is None:
            z = self._z; self._z += 1.0
        multi = isinstance(pts, (list, tuple)) and len(pts) > 0 and np.asarray(pts[0]).ndim == 2
        polys = None if pts is None else ([np.asarray(q, np.float32) for q in pts] if multi else [np.asarray(pts, np.float32)])
        p = dict(pts=None if pts is None else polys[0], polys=polys, colour=colour, z=float(z),
                 ink=ink or INK, width=width or 2.0, alpha=alpha, clip=clip, holes=[np.asarray(h, np.float32) for h in holes],
                 layer=layer, sketch=sketch, streak=streak, rag=rag, painted=False, inked=False)
        if paths is not None:
            p['paths'] = [np.asarray(q, np.float32) for q in paths]
            p['closed'] = bool(closed)
        elif outline and pts is not None:
            p['paths'] = list(polys); p['closed'] = True
        else:
            p['paths'] = []; p['closed'] = False
        self.parts.append(p)
        return p

    def _clip_mask(self, clip, box):
        if clip is None: return None
        polys = clip if isinstance(clip, (list, tuple)) else [clip]
        res = self._poly_mask(polys, box=box)
        return res[0] if res else None

    # ------------------------------------------------------------------ painting passes
    def sketch(self, alpha=0.6, layer=None):
        """red-ochre underdrawing of every declared part, with a lighter searching pass"""
        for p in self.parts:
            if not p['sketch'] or not p['paths'] or (layer and p['layer'] != layer): continue
            w = max(1.0, p['width'] * 0.6)
            for k, (a, j) in enumerate([(alpha, 0.5), (alpha * 0.45, 1.6)]):
                if k == 1 and self.rng.random() > 0.5: continue
                res = self._stroke_mask(p['paths'], w, closed=p['closed'], var=0.3, seed=self._seed(), jitter=j)
                if res:
                    m, b = res
                    m = m * (0.55 + 0.45 * self.T_mottle[b[1]:b[3], b[0]:b[2]])
                    self._draw_under(m, b, SKETCH, a)

    def ground(self, colour='#d6bb83', box=None, alpha=0.93, around=True):
        """background wash brushed over the wall in broad strokes (not quite opaque).  around: leave the declared
        opaque shapes unwashed, as the painters did, so their red sketch stays visible until they are coloured"""
        H, W = self.H, self.W
        x0, y0, x1, y1 = box or (0, 0, W, H)
        col = _c(colour)
        st = 0.5 * self.T_streak['h'] + 0.5 * self.T_streak['v']
        sweep = noise2d(H, W, 45, 3, self._seed())
        # broad diagonal brush sweeps: a stretched noise rotated 30 degrees
        g = np.zeros((H, W), np.float32)
        for ang in (28, -34):                                   # two directions of broad brush sweeps, patchy
            gi = Image.fromarray(self.rng.random((H // 6 + 2, W // 50 + 2)).astype(np.float32)).resize((W * 2, H * 2), Image.BICUBIC)
            gi = np.asarray(gi.rotate(ang, resample=Image.BILINEAR).resize((W, H), Image.BILINEAR), np.float32)
            g += (gi - gi.mean()) / (gi.std() + 1e-6) * smoothstep(0.35, 0.65, noise2d(H, W, 200, 2, self._seed()))
        g *= 0.5
        a = np.clip(alpha + 0.05 * (self.T_mottle - 0.5) * 2 - 0.08 * smoothstep(0.6, 0.95, sweep) + 0.015 * g, 0, 1)
        f = col * (1 + 0.07 * (self.T_mottle - 0.5) * 2 + 0.035 * (st - 0.5) * 2 + 0.03 * (self.T_grain - 0.5) + 0.012 * g)[..., None]
        if around:                                         # the painter brushed the ground round the figures
            ex = Image.new('L', (W, H), 0); d = ImageDraw.Draw(ex)
            for p in self.parts:
                if p['polys'] is None or p['colour'] is None or p['alpha'] is not None or p['clip'] is not None: continue
                for q in p['polys']:
                    if len(q) >= 3: d.polygon([(float(x), float(y)) for x, y in q], fill=255)
            e = np.asarray(ex, np.float32) / 255
            e = smoothstep(0.75, 1.0, blur(e, 1.6))                # pull in ~1.5 px: the wash runs under the edge
            a = a * (1 - e)
        sl = (slice(y0, y1), slice(x0, x1))
        aa = a[sl][..., None]
        self.img[sl] = self.img[sl] * (1 - aa) + np.clip(f[sl], 0, 1) * aa
        self.ground_img = self.img.copy()
        self.zmap[sl] = np.maximum(self.zmap[sl], 0)

    def _fill(self, p):
        if p['pts'] is None or p['colour'] is None: return
        res = self._poly_mask(p['polys'], holes=p['holes'])
        if res is None: return
        m, (x0, y0, x1, y1) = res
        cm = self._clip_mask(p['clip'], (x0, y0, x1, y1))
        if cm is not None: m = m * cm
        sl = (slice(y0, y1), slice(x0, x1))
        name = p['colour'] if isinstance(p['colour'], str) and p['colour'] in PIGMENTS else None
        mot, stk, grn, opa, thin = _TEX.get(name, (0.06, 0.05, 0.05, 0.96, 0.05))
        if p['alpha'] is not None: opa = p['alpha']
        col = _c(p['colour'])
        h, w = m.shape
        sdir = p['streak'] or ('v' if h > w * 1.3 else 'h')
        st = self.T_streak[sdir][sl]
        if p['rag'] > 0 and min(h, w) > 4:              # brush edge wanders a pixel over / short of the line
            mb = blur(m, 0.7)
            m = smoothstep(0.32, 0.68, mb + (self.T_edge[sl] - 0.5) * 0.55 * p['rag'])
        z = p['z']
        vis = (self.zmap[sl] <= z).astype(np.float32)
        a = m * vis * np.clip(opa - thin * smoothstep(0.55, 0.9, st), 0, 1)
        shade = 1 + mot * (self.T_mottle[sl] - 0.5) * 2 + stk * (st - 0.5) * 2 + grn * (self.T_grain[sl] - 0.5) * 2
        if name in _CRYST: shade = shade + _CRYST[name] * self.T_cryst[sl]       # coarse frit crystals glitter
        f = np.clip(col[None, None, :] * shade[..., None], 0, 1)
        a3 = a[..., None]
        self.img[sl] = self.img[sl] * (1 - a3) + f * a3
        hit = (m > 0.5) & (vis > 0)
        self.zmap[sl] = np.where(hit, z, self.zmap[sl])
        self.paintmap[sl] = np.maximum(self.paintmap[sl], a)
        if name in ('blue', 'lblue'):
            self.bluemap[sl] = np.maximum(self.bluemap[sl] * (1 - a), a)
        else:
            self.bluemap[sl] *= (1 - a)

    def _ink(self, p):
        if not p['paths']: return
        res = self._stroke_mask(p['paths'], p['width'], closed=p['closed'], var=0.16, seed=self._seed(),
                                taper=p['width'] * 2.5 if not p['closed'] else 0)
        if res is None: return
        m, (x0, y0, x1, y1) = res
        cm = self._clip_mask(p['clip'], (x0, y0, x1, y1))
        if cm is not None: m = m * cm
        sl = (slice(y0, y1), slice(x0, x1))
        vis = (self.zmap[sl] <= p['z'] + 1e-3).astype(np.float32)
        a = m * vis * (0.86 + 0.14 * self.T_mottle[sl]) * (0.94 + 0.06 * self.T_grain[sl])
        col = _c(p['ink'])
        a3 = a[..., None]
        self.img[sl] = self.img[sl] * (1 - a3) + col * a3
        self.paintmap[sl] = np.maximum(self.paintmap[sl], a)
        self.bluemap[sl] *= (1 - a)

    def colour(self, pigments=None, layer='scene'):
        """paint the fills of declared parts (only these pigments, if given), each once"""
        if isinstance(pigments, str): pigments = [pigments]
        for p in self.parts:
            if p['painted'] or p['layer'] != layer: continue
            if pigments is not None and p['colour'] not in pigments: continue
            self._fill(p); p['painted'] = True

    def ink(self, layer='scene'):
        """the final outlines of every painted part of this layer"""
        for p in self.parts:
            if p['inked'] or p['layer'] != layer: continue
            self._ink(p); p['inked'] = True

    # ------------------------------------------------------------------ figures
    def figure(self, x, y, height, pose='walk', facing=1, skin='skin', sex='m', wig='short', dress='kilt',
               collar=True, z=None, lw=None, apron=True, **over):
        """a figure in the composite view.  (x, y): point on the baseline under the hip; height: sole to top of
        the wig in px; facing +1 right / -1 left.  pose: a POSES name, overridden by keyword args (same keys).
        dress: 'kilt' | 'long' (calf-length translucent overkilt) | 'loin' | 'dress' (women's sheath).
        wig: 'short' | 'long' | 'woman' | 'cap'.  Returns a dict of anchor points (screen px) and z values."""
        P = dict(POSES[pose]); P.update(over)
        u = height / 19.6
        F = 1 if facing >= 0 else -1
        fem = sex == 'f'
        lw = lw or float(np.clip(0.14 * u, 1.6, 3.6))
        z0 = self._z if z is None else z
        self._z = z0 + 20

        def S(pt):
            pt = np.asarray(pt, np.float32)
            return np.stack([x + F * u * pt[..., 0], y - u * pt[..., 1]], -1)

        lean = np.radians(P['lean'])
        hip = np.array(P['hip'], np.float32)
        wk = 1 - 0.85 * float(smoothstep(4, 32, P['lean']))    # bending figures turn toward profile: narrower shoulders
        if 'turn' in P: wk = 1 - P['turn']

        def T(pt):                                          # torso frame -> body units
            return hip + _rot(np.asarray(pt, np.float32), -lean)

        def narrow(pts):
            q = np.array(pts, np.float32)
            ax = np.abs(q[:, 0]); s = np.sign(q[:, 0])
            q[:, 0] = s * (np.minimum(ax, 1.45) + np.maximum(ax - 1.45, 0) * wk)
            return q

        sk = 'skin_f' if fem else skin
        skin_ink = REDLINE if not fem else '#7a3f1c'
        k = 0.88 if fem else 1.0
        out = {'u': u, 'z0': z0}

        def add(pts, colour, z, paths=None, closed=None, ink=INK, alpha=None, outline=True, clip=None, width=None):
            pts_s = S(pts) if pts is not None else None
            pths = [S(q) for q in paths] if paths is not None else None
            clip_s = None if clip is None else ([S(c) for c in clip] if isinstance(clip, list) else S(clip))
            return self.part(pts_s, colour, outline=outline, paths=pths, closed=closed, ink=ink, width=width or lw,
                             z=z0 + z, alpha=alpha, clip=clip_s)

        # ---- legs (lead leg first: it is the far one)
        legs = {}
        for side, zz in (('f', 0.0), ('b', 1.0)):
            hj = T((0.45 * (1 if side == 'f' else -1), 0.25))
            knee = np.array(P['k' + side], np.float32); ank = np.array(P['a' + side], np.float32)
            wf = [(0, 1.05 * k), (0.22, 0.95 * k), (0.42, 0.56 * k), (0.58, 0.55 * k), (0.97, 0.36 * k), (1, 0.36 * k)]
            wb = [(0, 1.05 * k), (0.22, 0.9 * k), (0.42, 0.6 * k), (0.56, 0.86 * k), (0.97, 0.36 * k), (1, 0.36 * k)]
            poly, paths = _limb([hj, knee, ank - (0, 0.3)], wf, wb)
            legs[side] = (hj, knee, ank)
            add(poly, sk, zz, paths=paths, ink=skin_ink)
            fa = np.radians(P.get('f' + side, 0))
            foot = np.array([(-0.32, 0.12), (-0.62, -0.25), (-0.78, -0.62), (-0.66, -0.85), (0.9, -0.85), (1.9, -0.85),
                             (2.42, -0.8), (2.5, -0.68), (2.36, -0.58), (1.25, -0.33), (0.36, 0.12)], np.float32)
            foot[:, 0] *= 0.95 * k
            ball = np.array([1.8, -0.85], np.float32)
            if fa:
                foot = ball + _rot(foot - ball, fa)
            mir = P.get('m' + side, False)
            if mir: foot[:, 0] *= -1                           # foot tucked under, toes pointing back
            fp = foot + ank
            add(fp, sk, zz + 0.05, paths=[fp[:-1], ], ink=skin_ink)
            toe = (np.array([[1.95, -0.62], [2.38, -0.66]], np.float32) - ball)
            toe = (ball + _rot(toe, fa) if fa else toe + ball)
            if mir: toe[:, 0] *= -1
            add(None, None, zz + 0.06, paths=[toe + ank], ink=skin_ink, width=lw * 0.7)
            out['foot_' + side] = S(fp)
        # ---- torso
        if fem:
            tp = [(1.15, 0.0), (1.25, 1.1), (1.05, 2.1), (1.3, 3.5), (2.05, 4.0), (2.15, 4.55), (1.7, 5.0), (2.35, 5.55),
                  (2.25, 6.25), (1.05, 6.7), (0.5, 6.95), (-0.45, 7.0), (-1.05, 6.7), (-2.3, 6.25), (-2.45, 5.55),
                  (-1.8, 5.0), (-1.15, 3.6), (-0.95, 2.1), (-1.4, 0.6), (-1.25, 0.0)]
        else:
            tp = [(1.25, 0.0), (1.36, 1.15), (1.08, 2.1), (1.45, 3.6), (1.95, 4.45), (2.15, 5.0), (3.0, 5.6), (2.85, 6.3),
                  (1.2, 6.75), (0.55, 7.0), (-0.45, 7.05), (-1.2, 6.75), (-2.85, 6.3), (-3.05, 5.6), (-2.1, 5.0),
                  (-1.35, 3.6), (-0.95, 2.1), (-1.45, 0.6), (-1.3, 0.0)]
        torso = T(_closed_spline(narrow(tp), 6))
        add(torso, sk, 2.0, ink=skin_ink)
        if not fem:                                          # nipple: a small dot on the chest profile
            nip = T(np.array([(1.62, 4.38)], np.float32))[0]
            th = np.linspace(0, 2 * np.pi, 10)
            add(nip + np.stack([np.cos(th), np.sin(th)], 1) * 0.11, skin_ink, 2.1, outline=False)
        else:
            th = np.linspace(-0.3, 1.9, 12)
            add(None, None, 2.1, paths=[T(np.stack([1.75 + 0.42 * np.cos(th) - 0.42, 4.25 + 0.4 * np.sin(th) - 0.05], 1) * 1.0)],
                ink=skin_ink, width=lw * 0.6)
        # ---- dress / kilt
        def legpt(side, frac, off):
            hj, kn, an = legs[side]
            Pp = spline(np.array([hj, kn, an], np.float32), 10)
            s = _arc(Pp); t = s / s[-1]
            q = np.array([np.interp(frac, t, Pp[:, 0]), np.interp(frac, t, Pp[:, 1])], np.float32)
            i = min(int(np.searchsorted(t, frac)), len(Pp) - 2)
            tg = Pp[i + 1] - Pp[i]; tg /= np.hypot(*tg) + 1e-9
            n = np.array([-tg[1], tg[0]], np.float32)
            if n[0] < 0: n = -n
            return q + n * off
        if dress in ('kilt', 'long', 'loin'):
            hf = {'kilt': 0.3, 'long': 0.74, 'loin': 0.18}[dress]
            seated = P.get('seated', False)
            if seated:
                hemF = legpt('f', 0.52, 1.1); hemB = legpt('b', 0.18, -1.1)
                kp = [T((-1.2, 2.35)), T((1.25, 2.05)), legpt('f', 0.52, -1.1), hemF, legpt('b', 0.18, 1.05),
                      hemB, T((-1.7, 0.4))]
            else:
                hemF = legpt('f', hf, 1.45 * k); hemB = legpt('b', hf, -(1.2 * k))
                kp = [T((-1.2, 2.35)), T((1.3, 2.05)), T((1.62, 0.85)), hemF, hemB, T((-1.72, 0.5))]
            kilt = np.array(kp, np.float32)
            if dress != 'loin':                                 # round the corners a little, keep the edges straight
                kilt = _closed_spline(np.vstack([kilt[i] * 0.8 + kilt[(i + 1) % len(kilt)] * 0.2 if j else kilt[i]
                                                 for i in range(len(kilt)) for j in (0, 1)]), 3)
            add(kilt, 'linen', 3.0, alpha=0.78 if dress == 'long' else None)
            if dress == 'long':
                inner_f = legpt('f', 0.34, 1.0); inner_b = legpt('b', 0.34, -1.05)
                short = np.array([T((-1.2, 2.35)), T((1.3, 2.05)), T((1.5, 0.9)), inner_f, inner_b, T((-1.6, 0.5))])
                add(_closed_spline(short, 4), 'linen', 3.1)
                for i in range(7):                              # pleats of the overkilt
                    a0 = T((1.2 - i * 0.32, 1.9)); a1 = hemF + (hemB - hemF) * (0.12 + i * 0.13)
                    add(None, None, 3.2, paths=[np.array([a0, a1])], ink='#b9a58c', width=lw * 0.5,
                        clip=kilt)
            belt = [T((-1.2, 2.35)), T((1.3, 2.05)), T((1.32, 2.5)), T((-1.18, 2.8))]
            add(np.array(belt), 'linen' if dress != 'long' else 'red', 3.3)
            if apron and dress == 'kilt' and not seated:
                ap = [T((1.0, 2.05)), T((1.45, 1.0)), hemF + (hemB - hemF) * 0.02, hemF + (hemB - hemF) * 0.32]
                add(None, None, 3.25, paths=[np.array([ap[0], ap[3]])], ink=INK, width=lw * 0.7)
                for i in range(3):
                    a0 = T((0.75 - 0.25 * i, 2.0)); a1 = hemF + (hemB - hemF) * (0.1 + 0.07 * i)
                    add(None, None, 3.25, paths=[np.array([a0, a1])], ink='#b9a58c', width=lw * 0.45, clip=kilt)
            out['kilt'] = S(kilt)
        elif dress == 'dress':
            hemF = legpt('f', 0.93, 1.2); hemB = legpt('b', 0.93, -1.2)
            kneeF = legpt('f', 0.45, 1.05)
            dp = [T((-1.3, 4.75)), T((1.75, 4.6)), T((1.4, 3.0)), T((1.4, 1.2)), kneeF, hemF, hemB,
                  legpt('b', 0.45, -1.15), T((-1.55, 0.6)), T((-1.15, 2.4))]
            dr = _closed_spline(np.array(dp), 4)
            add(dr, 'linen', 3.0, alpha=0.84)
            for s_ in (-1.0, 0.9):                               # shoulder straps
                add(None, None, 3.2, paths=[np.array([T((s_ * 0.55, 6.6)), T((s_ * 0.9 + 0.25, 4.7))])],
                    ink='#e9e0cc', width=lw * 1.6)
            out['kilt'] = S(dr)
        # ---- arms
        cross = P.get('cross', False)
        for side, zz in (('f', 4.0), ('b', 6.5 if cross else 4.5)):
            full = (2.0 if fem else 2.42) * (1 if side == 'f' else -1)
            prof = 0.8 if side == 'f' else 0.05                  # in profile both shoulders sit over the chest
            sh = T((prof + (full - prof) * wk, 6.0 - 0.25 * (1 - wk)))
            wr = np.array(P['w' + side], np.float32)
            el = _ik(sh, wr, 3.35, 3.05, P['b' + side])
            poly, paths = _limb([sh, el, wr], [(0, 0.66 * k), (0.25, 0.56 * k), (0.52, 0.43 * k), (0.68, 0.47 * k), (1, 0.31 * k)],
                                [(0, 0.66 * k), (0.25, 0.56 * k), (0.52, 0.43 * k), (0.68, 0.45 * k), (1, 0.31 * k)],
                                cap0=True)
            add(poly, sk, zz, paths=paths, ink=skin_ink)
            d = wr - el; d /= np.hypot(*d) + 1e-9
            ang = np.arctan2(d[1], d[0])
            hand = P.get('h' + side, 'open')
            if hand == 'open':
                hp = np.array([(-0.25, -0.3), (0.75, -0.33), (1.55, -0.24), (1.85, -0.12), (1.9, 0.0), (1.75, 0.12),
                               (1.05, 0.22), (0.6, 0.33), (-0.25, 0.3)], np.float32)
                th_ = np.array([(0.25, 0.26), (0.7, 0.58), (1.05, 0.64), (1.12, 0.52), (0.75, 0.32)], np.float32)
            else:
                hp = np.array([(-0.25, -0.32), (0.5, -0.43), (0.92, -0.4), (1.08, -0.12), (1.04, 0.24), (0.78, 0.4),
                               (0.3, 0.38), (-0.25, 0.3)], np.float32)
                th_ = np.array([(0.35, 0.3), (0.85, 0.48), (1.02, 0.36), (0.6, 0.22)], np.float32)
            sgn = 1.0 if (np.cos(ang) >= -0.2) else -1.0     # thumb up for forward arms
            hp[:, 1] *= sgn; th_[:, 1] *= sgn
            hp *= k; th_ *= k
            hpw = wr + _rot(hp, ang); thw = wr + _rot(th_, ang)
            add(hpw, sk, zz + 0.02, paths=[hpw[1:-1]], ink=skin_ink)
            add(thw, sk, zz + 0.03, paths=[thw[1:-1]], ink=skin_ink)
            if hand != 'open':
                fl = wr + _rot(np.array([(0.95, -0.3 * sgn), (0.55, -0.05 * sgn), (0.95, 0.15 * sgn)], np.float32) * k, ang)
                add(None, None, zz + 0.04, paths=[fl[:2]], ink=skin_ink, width=lw * 0.6)
            out['hand_' + side] = S(wr + _rot(np.array([0.55 * k, 0.0], np.float32), ang))
            out['wrist_' + side] = S(wr)
            out['z_hand_' + side] = z0 + zz + 0.02
            out['dir_' + side] = np.array([F * d[0], -d[1]], np.float32)
        # ---- collar
        if collar:
            cc = (0.0, 6.75)
            bands = [('blue', 0.62, 0.95), ('red', 0.95, 1.28), ('green', 1.28, 1.62), ('blue', 1.62, 1.95)]
            if u < 16: bands = [('blue', 0.62, 1.05), ('red', 1.05, 1.45), ('green', 1.45, 1.95)]
            th = np.linspace(np.pi * 1.03, np.pi * 1.97, 40)
            sy = 0.78
            for i, (cl, r0, r1) in enumerate(bands):
                r0 *= k; r1 *= k
                cx_ = 1.18 * (0.55 + 0.45 * wk)
                outer = np.stack([cc[0] + np.cos(th) * r1 * cx_, cc[1] + np.sin(th) * r1 * sy], 1)
                inner = np.stack([cc[0] + np.cos(th) * r0 * cx_, cc[1] + np.sin(th) * r0 * sy], 1)[::-1]
                band = T(np.vstack([outer, inner]))
                add(band, cl, 5.0 + i * 0.01, width=lw * 0.6)
            if u >= 16:                                     # drop beads on the outer edge
                rr = bands[-1][2] * k
                for a in np.linspace(np.pi * 1.08, np.pi * 1.92, 13):
                    c0 = np.array([cc[0] + np.cos(a) * rr * cx_, cc[1] + np.sin(a) * rr * sy])
                    dd = np.array([np.cos(a) * cx_, np.sin(a) * sy]); dd /= np.hypot(*dd)
                    nn = np.array([-dd[1], dd[0]])
                    drop = np.array([c0 - nn * 0.12, c0 + dd * 0.32 - nn * 0.1, c0 + dd * 0.42, c0 + dd * 0.32 + nn * 0.1,
                                     c0 + nn * 0.12])
                    add(T(drop), 'yellow' if int(a * 10) % 2 else 'red', 5.2, width=lw * 0.5)
        # ---- head
        ha = -lean * (0.55 if not P.get('seated') else 1.0)
        neck_top = T((0.32, 7.25))

        def Hd(pt):
            return neck_top + _rot(np.asarray(pt, np.float32) * (0.97 if fem else 1.0), ha)
        face = [(-0.55, -1.25), (-0.6, -0.2), (-0.75, 0.35), (-1.15, 1.2), (-0.5, 2.35), (0.35, 2.4), (0.68, 2.15),
                (0.85, 1.85), (0.92, 1.55), (0.86, 1.4), (1.06, 1.08), (1.22, 0.86), (1.04, 0.76), (0.97, 0.74),
                (1.02, 0.6), (0.92, 0.53), (0.98, 0.45), (0.86, 0.34), (0.9, 0.2), (0.76, 0.03), (0.35, -0.02),
                (0.32, -0.25), (0.38, -1.25)]
        fpts = Hd(np.array(face, np.float32))
        add(fpts, sk, 5.5, paths=[fpts[1:-1]], ink=skin_ink)
        if fem:
            wp = [(0.66, 2.16), (0.45, 2.6), (-0.3, 2.82), (-1.15, 2.55), (-1.65, 1.6), (-1.75, 0.2), (-1.75, -1.6),
                  (-1.5, -2.8), (-0.9, -2.95), (-0.6, -1.0), (0.05, -0.1), (0.25, -0.3), (0.55, -1.6), (0.75, -2.7),
                  (1.15, -2.55), (0.75, -0.9), (0.3, 0.6), (0.18, 1.5), (0.35, 1.95)]
        elif wig == 'long':
            wp = [(0.7, 2.14), (0.45, 2.62), (-0.3, 2.85), (-1.2, 2.6), (-1.7, 1.7), (-1.85, 0.3), (-1.8, -1.0),
                  (-1.55, -1.3), (-0.4, -1.2), (0.12, -1.05), (0.18, 0.2), (0.16, 1.2), (0.32, 1.9)]
        elif wig == 'cap':
            wp = [(0.6, 2.2), (0.35, 2.5), (-0.4, 2.55), (-1.05, 2.2), (-1.3, 1.4), (-1.15, 0.85), (-0.55, 0.95),
                  (0.0, 1.55), (0.3, 1.95)]
        else:
            wp = [(0.72, 2.12), (0.45, 2.55), (-0.2, 2.72), (-0.95, 2.5), (-1.42, 1.75), (-1.52, 0.9), (-1.38, 0.15),
                  (-0.85, 0.02), (-0.15, 0.18), (0.1, 0.42), (0.13, 1.0), (0.17, 1.5), (0.35, 1.92)]
        wpts = Hd(_closed_spline(wp, 5) if wig != 'cap' else _closed_spline(wp, 5))
        add(wpts, 'black', 7.0)
        if u >= 10:                                          # wig strands
            strands = []
            nst = 9 if u < 20 else 16
            for i in range(nst):
                f = (i + 0.5) / nst
                a0 = np.array([0.55 - 1.9 * f, 2.75 - 0.3 * f], np.float32)
                bot = -2.9 if (fem or wig == 'long') else 0.0
                a1 = np.array([0.15 - 1.75 * f, bot + 0.2 * f], np.float32)
                c = (a0 + a1) / 2 + np.array([-0.35, 0.0])
                strands.append(Hd(spline(np.array([a0, c, a1]), 6)))
            for s_ in strands:
                self.part(None, None, paths=[S(s_)], ink='#3c4250', width=max(1.0, lw * 0.45), z=z0 + 7.05,
                          clip=S(wpts), sketch=False)
        if fem:                                              # fillet round the wig
            fb = Hd(np.array([(0.55, 2.0), (-0.4, 2.15), (-1.55, 1.85)], np.float32))
            add(None, None, 7.1, paths=[spline(fb, 6)], ink='#c84a32', width=lw * 1.4)
        if wig == 'cap':                                     # ear for close-cropped heads
            th = np.linspace(0, 2 * np.pi, 16)
            ear = Hd(np.stack([-0.08 + 0.2 * np.cos(th), 1.08 + 0.34 * np.sin(th)], 1))
            add(ear, sk, 7.2, ink=skin_ink)
        # eye: frontal almond, iris, kohl line, brow
        t_ = np.linspace(0, 1, 12)
        e0, e1 = np.array([0.34, 1.42]), np.array([0.82, 1.45])
        top = np.stack([e0[0] + (e1[0] - e0[0]) * t_, e0[1] + (e1[1] - e0[1]) * t_ + 0.13 * np.sin(np.pi * t_)], 1)
        bot = np.stack([e0[0] + (e1[0] - e0[0]) * t_, e0[1] + (e1[1] - e0[1]) * t_ - 0.08 * np.sin(np.pi * t_)], 1)[::-1]
        eye = Hd(np.vstack([top, bot]))
        add(eye, 'white', 7.3, width=lw * 0.7)
        th = np.linspace(0, 2 * np.pi, 14)
        iris = Hd(np.stack([0.62 + 0.085 * np.cos(th), 1.46 + 0.095 * np.sin(th)], 1))
        add(iris, 'black', 7.4, outline=False)
        kohl = Hd(np.array([[0.36, 1.42], [0.22, 1.38], [0.1, 1.34]], np.float32))
        add(None, None, 7.5, paths=[kohl], ink=INK, width=lw * 0.8)
        brow = Hd(np.stack([0.3 + 0.58 * t_, 1.66 + 0.06 * np.sin(np.pi * t_) + 0.02 * t_], 1))
        add(None, None, 7.5, paths=[brow], ink=INK, width=lw * 0.9)
        mouth = Hd(np.array([[0.92, 0.53], [0.78, 0.52]], np.float32))
        add(None, None, 7.5, paths=[mouth], ink=skin_ink, width=lw * 0.6)
        out['head'] = S(Hd(np.array([0.0, 1.4], np.float32)))
        out['head_top'] = S(Hd(np.array([-0.3, 2.8], np.float32)))
        out['ear'] = S(Hd(np.array([-0.1, 1.15], np.float32)))
        out['shoulder_b'] = S(T((0.05 + (-2.42 - 0.05) * wk, 6.0)))
        out['shoulder_f'] = S(T((0.8 + (2.42 - 0.8) * wk, 6.0)))
        out['T'] = lambda pt: S(T(pt))
        out['S'] = S
        out['lw'] = lw
        out['z_top'] = z0 + 8
        return out

    # ------------------------------------------------------------------ props held or used by figures
    def _xf(self, x, y, s, facing):
        F = 1 if facing >= 0 else -1
        return lambda q: np.stack([x + F * s * np.asarray(q, np.float32)[..., 0], y - s * np.asarray(q, np.float32)[..., 1]], -1)

    def rod(self, p0, p1, width, colour='ochre', z=None, lw=2.0):
        """a straight wooden rod (staff, handle, pole) as a filled band"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        d = p1 - p0; d /= np.hypot(*d) + 1e-9; n = np.array([-d[1], d[0]]) * width / 2
        pts = np.array([p0 + n, p1 + n, p1 - n, p0 - n])
        return self.part(pts, colour, z=z, width=lw)

    def staff(self, hand, length, facing=1, z=None, lw=2.0, width=None):
        """a long walking staff held upright in the fist, foot on the ground in front"""
        x, y = hand
        w = width or max(4, lw * 2.2)
        return self.rod((x + facing * lw, y - length * 0.18), (x - facing * lw * 0.5, y + length * 0.82), w, 'ochre', z=z, lw=lw)

    def sickle(self, hand, size, facing=1, angle=0.0, z=None, lw=2.0):
        """wooden sickle with a flint-toothed curved blade; the grip sits in `hand`"""
        F = 1 if facing >= 0 else -1
        th = np.linspace(np.radians(200), np.radians(355), 18)
        outer = np.stack([0.55 + 0.55 * np.cos(th), 0.15 + 0.55 * np.sin(th)], 1)
        inner = np.stack([0.58 + 0.38 * np.cos(th[::-1]), 0.2 + 0.4 * np.sin(th[::-1])], 1)
        blade = np.vstack([[[-0.3, -0.02], [-0.25, 0.1]], outer[2:], inner[:-2], [[-0.15, -0.06]]])
        blade = _rot(blade, np.radians(angle))
        P = np.stack([hand[0] + F * size * blade[:, 0], hand[1] - size * blade[:, 1]], 1)
        return self.part(P, 'ochre', z=z, width=lw)

    def hoe(self, fig, apex=(8.7, 6.2), strike=(6.3, 0.35), grip=(3.9, 10.7), width=None):
        """the Egyptian hoe (an inverted V): a handle held in both fists, a broad wooden blade lashed to its top
        end and striking the soil, a rope tying the two.  Points are in the figure's canon units."""
        S = fig['S']; lw = fig['lw']; u = fig['u']
        w = width or max(4.0, u * 0.5)
        a, s, g = S(np.array(apex, np.float32)), S(np.array(strike, np.float32)), S(np.array(grip, np.float32))
        z = fig['z_hand_b'] - 0.01
        self.rod(g, a, w, 'ochre', z=z, lw=lw)
        d = s - a; L = np.hypot(*d); d /= L; n = np.array([-d[1], d[0]])
        blade = np.array([a - n * w * 0.45, a + n * w * 0.45, s + n * w * 1.25 + d * 2, s - n * w * 0.9])
        self.part(blade, 'brown', z=z + 0.002, width=lw)
        m0 = g + (a - g) * 0.55; m1 = a + (s - a) * 0.5
        self.part(None, None, paths=[np.array([m0, m1])], ink='#6b5a3a', width=lw * 0.9, z=z + 0.003)

    def basket(self, cx, cy, w, h, colour='lgreen', z=None, lw=2.0, full=None):
        """a round woven basket (rim at cy), optional heap of ears or grain on top"""
        t = np.linspace(0, np.pi, 20)
        body = np.vstack([[[cx - w / 2, cy]], np.stack([cx - np.cos(t) * w / 2 * (0.92 - 0.1 * np.sin(t)), cy + np.sin(t) * h], 1),
                          [[cx + w / 2, cy]]])
        p = self.part(body, colour, z=z, width=lw)
        lines = [np.array([[cx - w / 2 + w * f, cy + 2], [cx - w / 2 + w * (f + 0.12), cy + h * 0.9]]) for f in np.linspace(0.08, 0.8, 7)]
        lines += [np.array([[cx - w / 2 + w * (f + 0.12), cy + 2], [cx - w / 2 + w * f, cy + h * 0.9]]) for f in np.linspace(0.08, 0.8, 7)]
        self.part(None, None, paths=lines, ink='#2e5b3c', width=lw * 0.5, z=p['z'] + 0.002, clip=body)
        if full:
            t2 = np.linspace(0, np.pi, 16)
            top = np.vstack([np.stack([cx + np.cos(t2) * w / 2 * 0.95, cy - np.sin(t2) * h * 0.55], 1)])
            self.part(top, full, z=p['z'] - 0.003, width=lw)
        return p

    def sack(self, cx, base, w, h, colour='linen', tie='red', z=None, lw=2.0, lean=0.0):
        """a tied linen grain sack standing on its base"""
        q = np.array([(-0.5, 0.08), (-0.47, 0.5), (-0.38, 0.72), (-0.16, 0.84), (-0.1, 0.9), (-0.2, 1.0), (0.0, 0.95),
                      (0.2, 1.0), (0.1, 0.9), (0.16, 0.84), (0.38, 0.72), (0.47, 0.5), (0.5, 0.08), (0.4, 0.0), (-0.4, 0.0)],
                     np.float32)
        q = _rot(q, lean)
        P = np.stack([cx + q[:, 0] * w, base - q[:, 1] * h], 1)
        p = self.part(_closed_spline(P, 4), colour, z=z, width=lw)
        band = np.array([(-0.17, 0.8), (0.17, 0.8), (0.15, 0.87), (-0.15, 0.87)], np.float32)
        band = _rot(band, lean)
        self.part(np.stack([cx + band[:, 0] * w, base - band[:, 1] * h], 1), tie, z=p['z'] + 0.002, width=lw * 0.6)
        sm = _rot(np.array([(0.22, 0.62), (0.3, 0.35), (0.26, 0.12)], np.float32), lean)
        self.part(None, None, paths=[np.stack([cx + sm[:, 0] * w, base - sm[:, 1] * h], 1)], ink='#b9a58c', width=lw * 0.5,
                  z=p['z'] + 0.002)
        return p

    def heap(self, cx, base, w, h, z=None, lw=2.0):
        """a heap of threshed grain: a dome stippled with grain dots"""
        t = np.linspace(0, 1, 40)
        xs = cx - w / 2 + w * t
        ys = base - h * (np.sin(np.pi * t) ** 0.85) * (1 + 0.06 * np.cos(2 * np.pi * t))
        P = np.vstack([np.stack([xs, ys], 1), [[cx + w / 2, base], [cx - w / 2, base]]])
        p = self.part(P, 'yellow', z=z, width=lw)
        dots = []
        r = self.rng
        for yy in np.arange(base - 6, base - h, -7.0):
            frac = (base - yy) / h
            half = w / 2 * np.sqrt(max(0, 1 - frac ** 1.6)) * 0.92
            for xx in np.arange(cx - half + 4 + (yy % 14) * 0.5, cx + half - 4, 8.0):
                th = np.linspace(0, 2 * np.pi, 7)
                rr = r.uniform(1.2, 1.8)
                dots.append(np.stack([xx + r.normal(0, 0.8) + np.cos(th) * rr * 1.3, yy + np.sin(th) * rr], 1))
        if dots:
            self.part(dots, 'ochre', z=p['z'] + 0.002, outline=False, clip=P, rag=0, sketch=False)
        return p

    def measure(self, cx, base, w, h, z=None, lw=2.0, tilt=0.0):
        """a wooden grain measure (heqat): a tapering tub with bands"""
        tf = lambda q: np.stack([cx + (_rot(np.asarray(q, np.float32) - (0, 0.5), tilt) + (0, 0.5))[:, 0] * w,
                                 base - (_rot(np.asarray(q, np.float32) - (0, 0.5), tilt) + (0, 0.5))[:, 1] * h], 1)
        t = np.linspace(0, np.pi, 12)
        grain = np.vstack([np.stack([-np.cos(t) * 0.5, 1.0 + np.sin(t) * 0.22], 1)])
        p = self.part(tf(grain), 'yellow', z=z - 0.002 if z is not None else None, width=lw * 0.7)
        body = tf([(-0.56, 1.0), (0.56, 1.0), (0.42, 0.05), (0.3, 0.0), (-0.3, 0.0), (-0.42, 0.05)])
        p = self.part(body, 'brown', z=p['z'] + 0.001, width=lw)
        for f in (0.25, 0.75):
            k = 0.42 + 0.14 * f
            self.part(None, None, paths=[tf([(-k, f), (k, f)])], ink='#d9b56a', width=lw * 0.9, z=p['z'] + 0.001)
        return p

    def papyrus(self, p0, p1, width, z=None, lw=2.0, lines=3):
        """an unrolled papyrus sheet between two points with a roll at the far end and lines of writing"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        d = p1 - p0; L = np.hypot(*d); d /= L; n = np.array([-d[1], d[0]])
        P = np.array([p0 - n * width / 2, p1 - n * width / 2, p1 + n * width / 2, p0 + n * width / 2])
        p = self.part(P, 'white', z=z, width=lw)
        roll = np.array([p1 - n * width * 0.62 - d * 3, p1 - n * width * 0.62 + d * 4, p1 + n * width * 0.62 + d * 4,
                         p1 + n * width * 0.62 - d * 3])
        self.part(roll, 'white', z=p['z'] + 0.003, width=lw)
        paths = []
        for i in range(lines):
            o = (i + 1) / (lines + 1) - 0.5
            a = p0 + d * L * 0.12 + n * width * o; b = p0 + d * L * (0.82 - 0.2 * (i == lines - 1)) + n * width * o
            paths.append(np.array([a, b]))
        self.part(None, None, paths=paths, ink='#3a2a22', width=lw * 0.55, z=p['z'] + 0.002)
        return p

    def palette(self, cx, cy, length, angle=0.0, z=None, lw=2.0):
        """a scribe's palette: a long slat with a red and a black ink cake and a pen slot"""
        d = np.array([np.cos(angle), -np.sin(angle)]); n = np.array([-d[1], d[0]])
        c = np.array([cx, cy], np.float32); w = length * 0.16
        P = np.array([c - d * length / 2 - n * w / 2, c + d * length / 2 - n * w / 2, c + d * length / 2 + n * w / 2,
                      c - d * length / 2 + n * w / 2])
        p = self.part(P, 'white', z=z, width=lw)
        th = np.linspace(0, 2 * np.pi, 10)
        for k, col in ((0.32, 'black'), (0.18, 'red')):
            q = c - d * length * k
            self.part(q + np.stack([np.cos(th), np.sin(th)], 1) * w * 0.3, col, z=p['z'] + 0.002, outline=False)
        self.part(None, None, paths=[np.array([c - d * length * 0.02, c + d * length * 0.44])], ink='#6b5a44',
                  width=lw * 0.6, z=p['z'] + 0.002)
        return p


    def papyrus_clump(self, x, base, h, n=5, z=None, lw=1.6, spread=None, seed=None):
        """papyrus stems rising from water or a bank, each topped by a fan-shaped umbel"""
        r = np.random.default_rng(seed if seed is not None else self._seed())
        spread = spread if spread is not None else h * 0.45
        z0 = self._z if z is None else z
        self._z = z0 + 2
        stems, umb, rays = [], [], []
        for i in range(n):
            f = (i + 0.5) / n - 0.5
            top = np.array([x + f * spread * 1.6, base - h * (0.78 + 0.22 * r.random())])
            b = np.array([x + f * spread * 0.4, base])
            stems.append(spline(np.array([b, (b + top) / 2 + (f * 6, 0), top]), 6))
            ang = np.radians(-90 + f * 40)
            R = h * 0.15
            th = np.linspace(ang - 0.9, ang + 0.9, 14)
            fan = np.vstack([[top], np.stack([top[0] + np.cos(th) * R, top[1] + np.sin(th) * R], 1)])
            umb.append(fan)
            for t in np.linspace(ang - 0.75, ang + 0.75, 5):
                rays.append(np.array([top, top + np.array([np.cos(t), np.sin(t)]) * R * 0.9]))
        self.part(None, None, paths=stems, ink='#2f6e50', width=lw * 1.8, z=z0)
        self.part(umb, 'green', z=z0 + 1, width=lw)
        self.part(None, None, paths=rays, ink='#1f4a34', width=lw * 0.5, z=z0 + 1.1, sketch=False)

    def scoop(self, hand, size, angle=0.0, facing=1, z=None, lw=2.0):
        """a wooden winnowing scoop held by its handle"""
        F = 1 if facing >= 0 else -1
        q = np.array([(-0.15, -0.07), (0.3, -0.1), (0.5, -0.3), (1.05, -0.28), (1.22, -0.1), (1.2, 0.1), (1.0, 0.24),
                      (0.5, 0.26), (0.3, 0.1), (-0.15, 0.07)], np.float32)
        q = _rot(q, np.radians(angle))
        P = np.stack([hand[0] + F * q[:, 0] * size, hand[1] - q[:, 1] * size], 1)
        return self.part(_closed_spline(P, 3), 'ochre', z=z, width=lw)

    def grain_stream(self, p0, p1, n=24, spread=4.0, z=None, colour='ochre', chaff=0):
        """grain falling from p0 to p1 (a poured stream, or a winnowed cloud when spread is large)"""
        r = self.rng; pts = []
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        for i in range(n):
            t = r.uniform(0, 1)
            c = p0 + (p1 - p0) * t + r.normal(0, spread * (0.3 + t), 2)
            th = np.linspace(0, 2 * np.pi, 6)
            pts.append(np.stack([c[0] + np.cos(th) * 2.1, c[1] + np.sin(th) * 1.5], 1))
        p = self.part(pts, colour, z=z, outline=False, rag=0, sketch=False)
        if chaff:
            lines = []
            for i in range(chaff):
                c = p0 + (p1 - p0) * r.uniform(-0.3, 0.5) + r.normal(0, spread * 1.4, 2)
                a = r.uniform(0, np.pi)
                lines.append(np.array([c, c + np.array([np.cos(a), np.sin(a)]) * r.uniform(4, 8)]))
            self.part(None, None, paths=lines, ink='#a88a52', width=1.2, z=p['z'] + 0.01, sketch=False)
        return p

    # ------------------------------------------------------------------ animals and plants
    def ox(self, x, base, length, facing=1, colour='white', patches='black', z=None, lw=2.0, seed=None,
           horn='#e9dfc6', far=False):
        """a long-horned ox in profile (x: the hindquarters on the ground line).  Four legs: the far pair is
        drawn first and a step apart from the near pair, so every leg is seen, as Egyptian painters did."""
        s = length / 15.4
        X = self._xf(x, base, s, facing)
        z0 = self._z if z is None else z
        self._z = z0 + 10
        r = np.random.default_rng(seed if seed is not None else self._seed())
        body = [(0.9, 8.1), (0.45, 7.75), (0.2, 6.7), (0.45, 5.3), (1.3, 4.3), (2.6, 3.75), (4.5, 3.45), (7.0, 3.5),
                (8.9, 3.8), (10.0, 3.9), (10.9, 4.25), (11.45, 4.8), (11.9, 5.5), (12.35, 6.1), (12.55, 7.3),
                (12.0, 8.45), (10.6, 8.6), (9.4, 8.3), (7.0, 8.0), (4.0, 8.1), (2.0, 8.4)]
        bpts = _closed_spline(body, 6)
        dark = colour in ('red', 'brown', 'black', 'ochre')
        legcol = colour

        def leg(kind, dx, zz):
            if kind == 'hind':
                q = [(1.0, 5.3), (0.85, 3.5), (1.2, 2.0), (1.28, 0.75), (1.22, 0.32), (2.0, 0.32), (1.95, 0.8), (1.92, 1.5),
                     (2.05, 2.8), (2.75, 4.0), (2.9, 4.8)]
            else:
                q = [(9.1, 4.6), (9.05, 3.0), (9.18, 2.1), (9.15, 0.9), (9.2, 0.32), (9.98, 0.32), (9.9, 0.9), (9.95, 2.0),
                     (10.05, 2.5), (10.25, 3.6), (10.45, 4.6)]
            q = np.array(q, np.float32) + (dx, 0)
            P = X(q)
            self.part(P, legcol, z=z0 + zz, paths=[P[:-1]], width=lw)
            hoof = np.array([q[4] + (0, 0.02), q[5] + (0, 0.02), q[5] + (0.06, -0.32), q[4] + (-0.1, -0.32)], np.float32)
            self.part(X(hoof), 'black', z=z0 + zz + 0.05, width=lw * 0.7)
        leg('hind', 1.3, 0.0); leg('fore', -1.1, 0.1)
        # tail behind the far legs
        tail = X(np.array([(0.75, 8.0), (0.15, 7.3), (-0.05, 5.6), (0.1, 3.8), (0.2, 2.6)], np.float32))
        self.part(None, None, paths=[spline(tail, 6)], ink=INK, width=lw * 1.6, z=z0 + 0.2)
        tuft = X(np.array([(0.2, 2.9), (-0.15, 2.2), (0.05, 1.5), (0.35, 1.45), (0.45, 2.1)], np.float32))
        self.part(_closed_spline(tuft, 4), 'black', z=z0 + 0.25, width=lw * 0.6)
        bp = self.part(X(bpts), colour, z=z0 + 1.0, width=lw)
        leg('hind', 0.0, 1.5); leg('fore', 0.0, 1.6)
        # patches (clipped to the body)
        if patches:
            blobs = []
            for i in range(r.integers(3, 6)):
                cx_, cy_ = r.uniform(1.5, 10.5), r.uniform(4.2, 8.2)
                rx, ry = r.uniform(0.9, 2.0), r.uniform(0.7, 1.5)
                th = np.linspace(0, 2 * np.pi, 24, endpoint=False)
                wob = 1 + 0.25 * fbm1d(24, 6, 2, int(r.integers(1 << 30)))
                blobs.append(X(np.stack([cx_ + np.cos(th) * rx * wob, cy_ + np.sin(th) * ry * wob], 1)))
            self.part(blobs, patches, z=z0 + 1.2, clip=X(bpts), outline=False, sketch=False)
        # head
        head = [(12.1, 8.65), (12.95, 8.35), (13.6, 7.6), (14.25, 6.3), (14.85, 5.1), (15.1, 4.65), (14.85, 4.35),
                (14.25, 4.45), (13.55, 5.15), (12.85, 5.9), (12.25, 6.6), (11.95, 7.6)]
        hp = _closed_spline(head, 5)
        self.part(X(hp), colour, z=z0 + 2.0, width=lw)
        if patches and r.random() < 0.6:
            th = np.linspace(0, 2 * np.pi, 20, endpoint=False)
            self.part(X(np.stack([13.3 + np.cos(th) * 0.8, 6.7 + np.sin(th) * 0.9], 1)), patches, z=z0 + 2.05,
                      clip=X(hp), outline=False, sketch=False)
        ear = np.array([(12.15, 8.2), (11.4, 8.35), (10.85, 8.05), (11.5, 7.75), (12.1, 7.75)], np.float32)
        self.part(X(_closed_spline(ear, 4)), colour, z=z0 + 2.1, width=lw)
        # lyre horns, both seen
        for hz, pts in ((1.9, [(12.35, 8.5), (11.75, 9.4), (11.75, 10.6), (12.25, 11.4)]),
                        (2.2, [(12.75, 8.45), (13.55, 9.4), (13.55, 10.6), (13.05, 11.35)])):
            c = spline(np.array(pts, np.float32), 8)
            T_ = np.gradient(c, axis=0); T_ /= np.hypot(T_[:, 0], T_[:, 1])[:, None]
            N_ = np.stack([-T_[:, 1], T_[:, 0]], 1)
            wv = np.linspace(0.36, 0.08, len(c))[:, None]
            self.part(X(np.vstack([c + N_ * wv, (c - N_ * wv)[::-1]])), horn, z=z0 + hz, width=lw * 0.8)
        # face details
        t_ = np.linspace(0, 1, 10)
        eye = np.vstack([np.stack([13.0 + 0.55 * t_, 7.45 + 0.18 * np.sin(np.pi * t_) - 0.15 * t_], 1),
                         np.stack([13.0 + 0.55 * t_, 7.45 - 0.12 * np.sin(np.pi * t_) - 0.15 * t_], 1)[::-1]])
        self.part(X(eye), 'white', z=z0 + 2.3, width=lw * 0.7)
        th = np.linspace(0, 2 * np.pi, 10)
        self.part(X(np.stack([13.3 + 0.12 * np.cos(th), 7.4 + 0.12 * np.sin(th)], 1)), 'black', z=z0 + 2.35, outline=False)
        self.part(None, None, paths=[X(np.array([(14.55, 5.2), (14.8, 5.05), (14.85, 4.85)], np.float32))], width=lw * 0.7,
                  z=z0 + 2.3)
        self.part(None, None, paths=[X(spline(np.array([(11.5, 4.7), (11.0, 5.4), (11.3, 6.4)], np.float32), 5)),
                                     X(spline(np.array([(11.85, 5.3), (11.55, 6.0), (11.85, 6.8)], np.float32), 5))],
                  width=lw * 0.6, z=z0 + 1.3, clip=X(bpts))
        return {'poll': X(np.array([12.5, 8.7], np.float32)), 'z': z0 + 2.5, 'horns': X(np.array([12.55, 9.6], np.float32)),
                'nose': X(np.array([15.0, 4.6], np.float32)), 'X': X, 'body': X(bpts)}

    def wheat(self, x0, x1, base, top, every=9.0, z=None, lw=1.8, stubble=(), grab=(), seed=None):
        """a standing field of emmer: stalks, ears with awns.  stubble: list of (xa, xb) ranges already cut
        (short stubs); grab: list of (x, y, (xa, xb)) -- stalks in [xa, xb] bend toward a fist at (x, y)."""
        r = np.random.default_rng(seed if seed is not None else self._seed())
        z0 = self._z if z is None else z
        self._z = z0 + 3
        stalks, ears, awns, stubs = [], [], [], []
        H = base - top
        xs = np.arange(x0, x1, every) + r.uniform(-every * 0.3, every * 0.3, len(np.arange(x0, x1, every)))
        for x in xs:
            if any(a <= x <= b for a, b in stubble):
                h = r.uniform(0.08, 0.14) * H
                stubs.append(np.array([[x, base], [x + r.normal(0, 1), base - h]]))
                continue
            tx = x + r.normal(0, every * 0.25); ty = top + r.uniform(0, H * 0.12)
            mid = None
            for gx, gy, (ga, gb) in grab:
                if ga <= x <= gb:
                    mid = (gx + r.normal(0, 1.5), gy + r.normal(0, 2)); tx = gx + (tx - gx) * 0.6 + (gx - x) * 0.25
            if mid is None:
                path = np.array([[x, base], [(x + tx) / 2 + r.normal(0, 1.5), (base + ty) / 2], [tx, ty]], np.float32)
            else:
                path = np.array([[x, base], [mid[0], mid[1]], [tx, ty]], np.float32)
            P = spline(path, 6)
            stalks.append(P)
            d = P[-1] - P[-4]; d /= np.hypot(*d) + 1e-9; n = np.array([-d[1], d[0]])
            L = H * r.uniform(0.13, 0.17); W = L * 0.18
            tip = P[-1] + d * L
            t = np.linspace(0, 1, 9)
            sh = np.sin(np.pi * np.clip(t * 1.1, 0, 1)) ** 0.7
            left = P[-1][None] + d[None] * (t * L)[:, None] + n[None] * (sh * W)[:, None]
            right = P[-1][None] + d[None] * (t * L)[:, None] - n[None] * (sh * W)[:, None]
            ears.append(np.vstack([left, right[::-1]]))
            for k in range(4):
                a = P[-1] + d * L * (0.3 + 0.18 * k)
                for sgn in (-1, 1):
                    awns.append(np.array([a + n * sgn * W * 0.8, a + n * sgn * W * 1.6 + d * L * 0.5]))
        if stalks: self.part(None, None, paths=stalks, ink='#9b6b2c', width=lw * 0.75, z=z0)
        if stubs: self.part(None, None, paths=stubs, ink='#9b6b2c', width=lw * 0.8, z=z0)
        if ears: self.part(ears, 'yellow', z=z0 + 1, width=lw * 0.6, ink='#7a4a1c')
        if awns: self.part(None, None, paths=awns, ink='#9b6b2c', width=lw * 0.35, z=z0 + 1.1, sketch=False)

    def sheaf(self, cx, base, w, h, z=None, lw=1.8):
        """a bound sheaf of cut emmer lying ready to carry"""
        r = self.rng
        z0 = self._z if z is None else z
        self._z = z0 + 2
        stalks, ears = [], []
        for i in range(14):
            a = np.radians(r.uniform(-14, 14))
            p0 = np.array([cx + r.normal(0, w * 0.06), base]); p1 = p0 + np.array([np.sin(a), -np.cos(a)]) * h * 0.75
            stalks.append(np.array([p0, (p0 + p1) / 2 + (r.normal(0, 1), 0), p1]))
            d = (p1 - p0) / np.hypot(*(p1 - p0)); n = np.array([-d[1], d[0]])
            L = h * 0.28; W = L * 0.17; t = np.linspace(0, 1, 8); sh = np.sin(np.pi * np.clip(t * 1.1, 0, 1)) ** 0.7
            ears.append(np.vstack([p1 + np.outer(t * L, d) + np.outer(sh * W, n), (p1 + np.outer(t * L, d) - np.outer(sh * W, n))[::-1]]))
        self.part(None, None, paths=stalks, ink='#9b6b2c', width=lw * 0.8, z=z0)
        self.part(ears, 'yellow', z=z0 + 1, width=lw * 0.6, ink='#7a4a1c')
        band = np.array([[cx - w * 0.22, base - h * 0.3], [cx + w * 0.22, base - h * 0.3], [cx + w * 0.2, base - h * 0.38],
                         [cx - w * 0.2, base - h * 0.38]])
        self.part(band, 'green', z=z0 + 1.2, width=lw * 0.6)

    def tree(self, cx, base, h, w, z=None, lw=2.0, figs=True, waterskin=None):
        """a sycamore fig: a trunk and a round crown packed with outlined leaves and red figs;
        waterskin=(dx, drop) hangs a skin from a branch"""
        r = self.rng
        z0 = self._z if z is None else z
        self._z = z0 + 6
        tw = w * 0.09
        trunk = np.array([[cx - tw * 1.3, base], [cx - tw * 0.6, base - h * 0.15], [cx - tw * 0.5, base - h * 0.55],
                          [cx + tw * 0.5, base - h * 0.55], [cx + tw * 0.6, base - h * 0.15], [cx + tw * 1.3, base]])
        self.part(trunk, 'brown', z=z0, width=lw)
        ccy = base - h * 0.62; rx, ry = w / 2, h * 0.36
        th = np.linspace(0, 2 * np.pi, 40, endpoint=False)
        wob = 1 + 0.07 * np.sin(th * 7 + r.uniform(0, 6))
        crown = np.stack([cx + np.cos(th) * rx * wob, ccy + np.sin(th) * ry * wob], 1)
        self.part(crown, 'green', z=z0 + 1, width=lw)
        rows = []
        L = ry * 0.24; Wd = L * 0.5
        ys = np.arange(ccy - ry * 0.95, ccy + ry * 0.92, L * 0.52)
        for j, yy in enumerate(ys):
            row = []
            off = (j % 2) * Wd * 0.95
            for xx in np.arange(cx - rx - Wd + off, cx + rx + Wd, Wd * 1.9):
                if ((xx - cx) / (rx * 0.97)) ** 2 + ((yy + L * 0.3 - ccy) / (ry * 0.97)) ** 2 > 1.0: continue
                t = np.linspace(0, 1, 9)
                side = np.sin(np.pi * t) ** 0.9 * Wd / 2
                q = np.vstack([np.stack([xx + side, yy + L * (1 - t)], 1), np.stack([xx - side, yy + L * (1 - t)], 1)[::-1]])
                row.append(q)
            if row: rows.append(row)
        for j, row in enumerate(rows):                              # lower rows overlap the ones above, like scales
            self.part(row, 'dkgreen' if j % 2 == 0 else 'lgreen', z=z0 + 2 + j * 0.01, width=lw * 0.5, sketch=j % 2 == 0,
                      clip=crown)
        if figs:
            fg = []
            for i in range(14):
                a = r.uniform(0, 2 * np.pi); rr = np.sqrt(r.uniform(0.05, 0.75))
                t = np.linspace(0, 2 * np.pi, 8)
                fg.append(np.stack([cx + np.cos(a) * rx * rr + np.cos(t) * 2.6, ccy + np.sin(a) * ry * rr + np.sin(t) * 2.6], 1))
            self.part(fg, 'red', z=z0 + 2.2, width=lw * 0.4)
        out = {'crown': crown, 'z': z0 + 3}
        if waterskin:                                          # a goatskin of water hung from a lopped branch
            dx, drop = waterskin
            bx0, by0 = cx + np.sign(dx) * tw * 0.4, base - h * 0.42
            hx, hy = cx + dx, base - h * 0.47
            self.rod((bx0, by0), (hx + np.sign(dx) * 6, hy), max(3, tw * 0.45), 'brown', z=z0 + 0.5, lw=lw)
            self.part(None, None, paths=[np.array([[hx, hy], [hx - np.sign(dx) * 3, hy + drop * 0.22]])], ink=INK,
                      width=lw * 0.8, z=z0 + 3)
            sk = np.array([(0.0, 0.18), (0.22, 0.24), (0.38, 0.5), (0.5, 0.62), (0.58, 0.55), (0.52, 0.8), (0.3, 1.0),
                           (-0.3, 1.0), (-0.48, 0.82), (-0.56, 0.6), (-0.42, 0.62), (-0.36, 0.42), (-0.2, 0.24)], np.float32)
            P = np.stack([hx + sk[:, 0] * drop * 0.62, hy + drop * 0.18 + sk[:, 1] * drop * 0.82], 1)
            self.part(_closed_spline(P, 4), 'brown', z=z0 + 3.1, width=lw)
            self.part(None, None, paths=[np.array([[hx - drop * 0.12, hy + drop * 0.34], [hx + drop * 0.12, hy + drop * 0.34]])],
                      ink='#e9dfc6', width=lw * 1.2, z=z0 + 3.2)
            out['skin'] = (hx, hy + drop * 0.7)
        return out

    # ------------------------------------------------------------------ frame: borders, frieze, bands, river
    def block_border(self, x0, y0, x1, y1, block=30, colours=('blue', 'red', 'green', 'red'), spacer=8, lw=1.8):
        """the block border: coloured blocks with white spacers between black rules"""
        horiz = (x1 - x0) >= (y1 - y0)
        L0, L1 = (x0, x1) if horiz else (y0, y1)
        pos, k = L0, 0
        rects, whites = {}, []
        while pos < L1:
            e = min(L1, pos + block)
            rects.setdefault(colours[k % len(colours)], []).append((pos, e))
            pos = e
            if pos < L1:
                whites.append((pos, min(L1, pos + spacer))); pos += spacer
            k += 1
        def R(a, b):
            return np.array([[a, y0], [b, y0], [b, y1], [a, y1]], np.float32) if horiz else \
                np.array([[x0, a], [x1, a], [x1, b], [x0, b]], np.float32)
        for col, segs in rects.items():
            self.part([R(a, b) for a, b in segs], col, width=lw, rag=0.5)
        if whites:
            self.part([R(a, b) for a, b in whites], 'white', width=lw, rag=0.5)

    def band(self, x0, x1, y, stripes, lw=1.6):
        """horizontal stripes from y downward: stripes = [(colour, height), ...] with black rules between"""
        yy = y
        for col, h in stripes:
            if col == 'rule':
                self.part(None, None, paths=[np.array([[x0, yy + h / 2], [x1, yy + h / 2]])], width=h, ink=INK, sketch=False)
            else:
                self.part(np.array([[x0, yy], [x1, yy], [x1, yy + h], [x0, yy + h]], np.float32), col, outline=False, rag=0.4)
            yy += h
        return yy

    def kheker(self, x0, x1, y0, y1, w=30, colours=('green', 'red', 'blue'), lw=1.8):
        """the kheker frieze: a row of tied bundles of reeds with knobbed tops"""
        n = int((x1 - x0) // w)
        w = (x1 - x0) / n
        H = y1 - y0
        bodies = {}
        knobs, ties = [], []
        for i in range(n):
            cx = x0 + (i + 0.5) * w
            col = colours[i % len(colours)]
            q = np.array([(-0.42, 1.0), (-0.38, 0.62), (-0.2, 0.46), (-0.16, 0.34), (-0.26, 0.24), (-0.26, 0.14),
                          (0.26, 0.14), (0.26, 0.24), (0.16, 0.34), (0.2, 0.46), (0.38, 0.62), (0.42, 1.0)], np.float32)
            P = np.stack([cx + q[:, 0] * w, y0 + q[:, 1] * H], 1)
            bodies.setdefault(col, []).append(P)
            th = np.linspace(0, 2 * np.pi, 16)
            knobs.append(np.stack([cx + np.cos(th) * w * 0.27, y0 + 0.09 * H + np.sin(th) * w * 0.22], 1))
            for f in (0.5, 0.58):
                hw = 0.17 + (f - 0.46) * 1.2
                ties.append(np.array([[cx - w * hw, y0 + f * H], [cx + w * hw, y0 + f * H], [cx + w * hw, y0 + (f + 0.05) * H],
                                      [cx - w * hw, y0 + (f + 0.05) * H]], np.float32))
        for col, ps in bodies.items():
            self.part(ps, col, width=lw)
        self.part(knobs, 'red', width=lw)
        self.part(ties, 'yellow', width=lw * 0.7)
        mids = [np.array([[x0 + (i + 0.5) * w, y0 + 0.66 * H], [x0 + (i + 0.5) * w, y1 - 2]]) for i in range(n)]
        self.part(None, None, paths=mids, width=lw * 0.6, sketch=False)

    def river(self, x0, y0, x1, y1, fish=4, lotus=5, lw=1.8, seed=None):
        """the river: Egyptian-blue water with rows of black zigzags, fish and lotus"""
        r = np.random.default_rng(seed if seed is not None else self._seed())
        P = np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], np.float32)
        p = self.part(P, 'blue', width=lw, rag=0.4)
        rows = []
        hz = (y1 - y0)
        for k, yy in enumerate(np.arange(y0 + hz * 0.22, y1 - hz * 0.1, hz * 0.26)):
            xs = np.arange(x0 + 6 + (k % 2) * 7, x1 - 6, 14.0)
            pts = np.stack([np.repeat(xs, 2)[:-1] + np.tile([0, 7], len(xs))[:-1], np.tile([yy - 4, yy + 4], len(xs))[:-1]], 1)
            rows.append(pts)
        self.part(None, None, paths=rows, width=lw * 0.75, z=p['z'] + 0.002, sketch=False)
        out = []
        for i in range(fish):
            fx = x0 + (i + 0.5) / fish * (x1 - x0) + r.normal(0, 30); fy = y0 + hz * r.uniform(0.38, 0.62)
            F = 1 if r.random() < 0.5 else -1
            L = hz * 0.62
            q = np.array([(0.0, 0.0), (0.18, 0.2), (0.45, 0.26), (0.7, 0.18), (0.82, 0.05), (0.98, 0.17), (0.94, 0.0),
                          (0.98, -0.17), (0.82, -0.05), (0.7, -0.16), (0.45, -0.24), (0.18, -0.18)], np.float32)
            Pq = np.stack([fx + F * (0.5 - q[:, 0]) * L, fy - q[:, 1] * L], 1)
            fp = self.part(_closed_spline(Pq, 4), 'lblue', z=p['z'] + 1, width=lw * 0.8)
            th = np.linspace(0, 2 * np.pi, 8)
            self.part(np.stack([fx + F * 0.38 * L + np.cos(th) * 1.8, fy - 0.04 * L + np.sin(th) * 1.8], 1), 'black',
                      z=fp['z'] + 0.002, outline=False)
            fin = np.array([[fx + F * 0.1 * L, fy - 0.2 * L], [fx - F * 0.12 * L, fy - 0.36 * L], [fx - F * 0.25 * L, fy - 0.18 * L]])
            self.part(fin, 'red', z=fp['z'] - 0.002, width=lw * 0.6)
        for i in range(lotus):
            lx = x0 + (i + 0.3 + r.uniform(0, 0.4)) / lotus * (x1 - x0); ly = y0 + hz * 0.08
            stem = np.array([[lx, ly + hz * 0.25], [lx + r.normal(0, 4), y1 - 2]])
            self.part(None, None, paths=[stem], ink='#2f6e50', width=lw * 1.2, z=p['z'] + 0.5)
            pet = []
            for a in (-0.55, 0.0, 0.55):
                c = np.array([lx, ly + hz * 0.24]); d = np.array([np.sin(a), -np.cos(a)]); n = np.array([-d[1], d[0]])
                L = hz * 0.32
                pet.append(np.array([c, c + d * L * 0.5 + n * L * 0.17, c + d * L, c + d * L * 0.5 - n * L * 0.17]))
            self.part(pet, 'lblue', z=p['z'] + 0.6, width=lw * 0.7)
        return p

    # ------------------------------------------------------------------ hieroglyphs (pseudo-text)
    def _sign(self, name):
        """polygons / lines of one sign in a unit em box (y down, facing right): list of (kind, geom, colour)"""
        th = np.linspace(0, 2 * np.pi, 20, endpoint=False)
        E = lambda cx, cy, rx, ry: np.stack([cx + np.cos(th) * rx, cy + np.sin(th) * ry], 1)
        A = lambda *pts: np.array(pts, np.float32)
        cs = lambda pts, per=4: _closed_spline(np.array(pts, np.float32), per)
        if name == 'reed':
            return [('f', A((0.44, 1.0), (0.37, 0.78), (0.35, 0.52), (0.4, 0.3), (0.5, 0.12), (0.64, 0.0), (0.6, 0.22),
                            (0.57, 0.48), (0.55, 0.74), (0.5, 1.0)), 'green'),
                    ('l', A((0.47, 0.95), (0.5, 0.5), (0.6, 0.1)), None)]
        if name == 'water':
            xs = np.linspace(0.02, 0.98, 15); ys = np.where(np.arange(15) % 2 == 0, 0.45, 0.56)
            top = np.stack([xs, ys - 0.05], 1); bot = np.stack([xs, ys + 0.05], 1)[::-1]
            return [('f', np.vstack([top, bot]), 'blue')]
        if name == 'mouth':
            t = np.linspace(0, 1, 14)
            return [('f', np.vstack([np.stack([0.05 + 0.9 * t, 0.5 - 0.17 * np.sin(np.pi * t)], 1),
                                     np.stack([0.95 - 0.9 * t, 0.5 + 0.15 * np.sin(np.pi * t)], 1)]), 'red')]
        if name == 'loaf':
            t = np.linspace(0, np.pi, 16)
            return [('f', np.vstack([np.stack([0.5 - np.cos(t) * 0.32, 0.72 - np.sin(t) * 0.34], 1)]), 'ochre')]
        if name == 'sun':
            return [('f', E(0.5, 0.5, 0.31, 0.31), 'red'), ('f', E(0.5, 0.5, 0.07, 0.07), 'black')]
        if name == 'stroke':
            return [('f', A((0.45, 0.1), (0.57, 0.1), (0.56, 0.9), (0.44, 0.9)), 'black')]
        if name == 'heel':
            t = np.linspace(0, np.pi, 16)
            o = np.stack([0.5 - np.cos(t) * 0.33, 0.95 - np.sin(t) * 0.82], 1)
            i_ = np.stack([0.5 - np.cos(t[::-1]) * 0.18, 0.95 - np.sin(t[::-1]) * 0.64], 1)
            return [('f', np.vstack([o, i_]), 'black')]
        if name == 'coil':
            t = np.linspace(0, 2.6 * np.pi, 40)
            sp = np.stack([0.5 + np.cos(t) * (0.06 + 0.035 * t), 0.36 + np.sin(t) * (0.06 + 0.035 * t)], 1)
            return [('l', np.vstack([sp, [[0.5, 0.95]]]), 'thick')]
        if name == 'foot':
            return [('f', cs([(0.22, 0.04), (0.42, 0.04), (0.44, 0.6), (0.62, 0.72), (0.95, 0.8), (0.97, 0.94), (0.2, 0.94)], 3), 'skin')]
        if name == 'hand':
            return [('f', A((0.02, 0.56), (0.3, 0.46), (0.86, 0.43), (0.98, 0.5), (0.92, 0.58), (0.3, 0.64), (0.02, 0.62)), 'skin'),
                    ('f', A((0.28, 0.48), (0.48, 0.3), (0.6, 0.31), (0.5, 0.46)), 'skin')]
        if name == 'basket':
            return [('f', cs([(0.04, 0.38), (0.86, 0.38), (0.8, 0.6), (0.58, 0.72), (0.38, 0.72), (0.14, 0.6)], 4), 'green'),
                    ('l', A((0.86, 0.42), (0.98, 0.44), (0.97, 0.56), (0.83, 0.55)), None)]
        if name == 'house':
            return [('f', A((0.1, 0.25), (0.9, 0.25), (0.9, 0.8), (0.6, 0.8), (0.6, 0.66), (0.78, 0.66), (0.78, 0.37),
                            (0.22, 0.37), (0.22, 0.66), (0.4, 0.66), (0.4, 0.8), (0.1, 0.8)), 'red')]
        if name == 'cloth':
            return [('f', cs([(0.38, 0.95), (0.38, 0.36), (0.29, 0.25), (0.34, 0.08), (0.56, 0.05), (0.63, 0.2), (0.52, 0.33),
                              (0.6, 0.95)], 3), 'red')]
        if name == 'chick':
            return [('f', cs([(0.08, 0.55), (0.3, 0.36), (0.58, 0.3), (0.7, 0.14), (0.84, 0.17), (0.96, 0.27), (0.84, 0.31),
                              (0.79, 0.4), (0.83, 0.58), (0.62, 0.75), (0.42, 0.75), (0.15, 0.63)]), 'yellow'),
                    ('l', A((0.55, 0.74), (0.52, 0.95), (0.63, 0.97)), None), ('l', A((0.45, 0.74), (0.4, 0.95), (0.5, 0.97)), None),
                    ('l', A((0.3, 0.48), (0.62, 0.52)), None), ('f', E(0.77, 0.24, 0.03, 0.03), 'black')]
        if name == 'owl':
            return [('f', cs([(0.3, 0.9), (0.24, 0.6), (0.33, 0.3), (0.44, 0.12), (0.62, 0.07), (0.8, 0.14), (0.83, 0.34),
                              (0.73, 0.55), (0.68, 0.8), (0.55, 0.9)]), 'ochre'),
                    ('f', E(0.6, 0.22, 0.06, 0.06), 'white'), ('f', E(0.75, 0.22, 0.06, 0.06), 'white'),
                    ('f', E(0.6, 0.22, 0.025, 0.025), 'black'), ('f', E(0.75, 0.22, 0.025, 0.025), 'black'),
                    ('l', A((0.47, 0.88), (0.45, 0.98)), None), ('l', A((0.58, 0.88), (0.6, 0.98)), None),
                    ('l', A((0.32, 0.45), (0.55, 0.7)), None)]
        if name == 'vulture':
            return [('f', cs([(0.04, 0.66), (0.24, 0.42), (0.46, 0.34), (0.6, 0.29), (0.64, 0.13), (0.78, 0.06), (0.9, 0.12),
                              (0.93, 0.2), (0.83, 0.2), (0.79, 0.32), (0.82, 0.52), (0.7, 0.74), (0.45, 0.8), (0.2, 0.76)]), 'lblue'),
                    ('l', A((0.6, 0.78), (0.58, 0.97), (0.7, 0.98)), None), ('l', A((0.24, 0.5), (0.55, 0.62)), None),
                    ('f', E(0.8, 0.14, 0.025, 0.025), 'black')]
        if name == 'duck':
            return [('f', cs([(0.02, 0.56), (0.25, 0.46), (0.55, 0.43), (0.68, 0.3), (0.72, 0.13), (0.82, 0.08), (0.88, 0.14),
                              (0.98, 0.21), (0.86, 0.23), (0.8, 0.31), (0.85, 0.55), (0.7, 0.72), (0.35, 0.72)]), 'green'),
                    ('l', A((0.55, 0.72), (0.55, 0.92), (0.64, 0.93)), None), ('l', A((0.3, 0.55), (0.65, 0.6)), None),
                    ('f', E(0.8, 0.15, 0.025, 0.025), 'black')]
        if name == 'viper':
            c = spline(A((0.02, 0.86), (0.3, 0.82), (0.5, 0.6), (0.7, 0.8), (0.9, 0.78)), 8)
            T_ = np.gradient(c, axis=0); T_ /= np.hypot(T_[:, 0], T_[:, 1])[:, None]; N_ = np.stack([-T_[:, 1], T_[:, 0]], 1)
            wv = np.linspace(0.02, 0.07, len(c))[:, None]
            body = np.vstack([c + N_ * wv, A((0.98, 0.78), (0.9, 0.7)), (c - N_ * wv)[::-1]])
            return [('f', body, 'yellow'), ('l', A((0.86, 0.71), (0.84, 0.6)), None), ('l', A((0.92, 0.71), (0.93, 0.6)), None)]
        if name == 'sickle':
            return [('f', cs([(0.12, 0.95), (0.1, 0.55), (0.2, 0.3), (0.42, 0.12), (0.7, 0.08), (0.92, 0.15), (0.72, 0.19),
                              (0.46, 0.26), (0.31, 0.42), (0.26, 0.6), (0.27, 0.95)], 3), 'ochre')]
        if name == 'grain':
            return [('f', E(0.3, 0.68, 0.1, 0.14), 'ochre'), ('f', E(0.5, 0.42, 0.1, 0.14), 'ochre'), ('f', E(0.7, 0.68, 0.1, 0.14), 'ochre')]
        if name == 'jar':
            return [('f', cs([(0.36, 0.95), (0.25, 0.75), (0.22, 0.5), (0.3, 0.32), (0.39, 0.25), (0.37, 0.14), (0.63, 0.14),
                              (0.61, 0.25), (0.7, 0.32), (0.78, 0.5), (0.75, 0.75), (0.64, 0.95)], 3), 'red'),
                    ('l', A((0.3, 0.33), (0.18, 0.4), (0.24, 0.52)), None), ('l', A((0.7, 0.33), (0.82, 0.4), (0.76, 0.52)), None)]
        if name == 'scroll':
            return [('f', A((0.05, 0.38), (0.95, 0.38), (0.95, 0.62), (0.05, 0.62)), 'white'),
                    ('f', A((0.45, 0.33), (0.55, 0.33), (0.55, 0.67), (0.45, 0.67)), 'red')]
        if name == 'pool':
            return [('f', A((0.05, 0.3), (0.95, 0.3), (0.95, 0.68), (0.05, 0.68)), 'blue'),
                    ('l', A((0.2, 0.36), (0.2, 0.62)), None), ('l', A((0.4, 0.36), (0.4, 0.62)), None),
                    ('l', A((0.6, 0.36), (0.6, 0.62)), None), ('l', A((0.8, 0.36), (0.8, 0.62)), None)]
        if name == 'flax':
            t = np.linspace(0, 1, 50)
            return [('l', np.stack([0.5 + 0.13 * np.sin(t * 6 * np.pi), 0.05 + 0.9 * t + 0.04 * np.cos(t * 6 * np.pi)], 1), 'blue')]
        if name == 'bolt':
            return [('f', A((0.05, 0.43), (0.78, 0.43), (0.95, 0.5), (0.78, 0.57), (0.05, 0.57)), 'green'),
                    ('f', A((0.2, 0.38), (0.28, 0.38), (0.28, 0.62), (0.2, 0.62)), 'green')]
        if name == 'hoe':
            return [('f', A((0.2, 0.06), (0.3, 0.1), (0.95, 0.86), (0.88, 0.93)), 'ochre'),
                    ('f', A((0.2, 0.06), (0.28, 0.1), (0.3, 0.9), (0.04, 0.95)), 'brown'),
                    ('l', A((0.22, 0.5), (0.55, 0.47)), None)]
        if name == 'nfr':
            return [('f', E(0.5, 0.74, 0.19, 0.2), 'red'), ('f', A((0.46, 0.05), (0.54, 0.05), (0.54, 0.56), (0.46, 0.56)), 'black'),
                    ('l', A((0.36, 0.2), (0.64, 0.2)), None)]
        raise KeyError(name)

    SIGNS = ['reed', 'water', 'mouth', 'loaf', 'sun', 'foot', 'hand', 'basket', 'house', 'cloth', 'chick', 'owl', 'vulture',
             'duck', 'viper', 'sickle', 'grain', 'jar', 'scroll', 'pool', 'flax', 'bolt', 'nfr']

    def _sign_box(self, name):
        g = self._sign(name)
        allp = np.vstack([q for _, q, _ in g])
        return allp[:, 0].min(), allp[:, 1].min(), allp[:, 0].max(), allp[:, 1].max()

    def glyph(self, name, x, y, size, facing=1, z=None, lw=None, mono=None):
        """one sign whose em box has its top-left at (x, y); facing +1 looks right.  mono: paint it in one colour"""
        lw = lw or max(1.0, size * 0.035)
        F = 1 if facing >= 0 else -1
        z0 = self._z if z is None else z
        self._z = z0 + 1
        for k, (kind, q, col) in enumerate(self._sign(name)):
            q = np.asarray(q, np.float32)
            P = np.stack([x + (q[:, 0] if F > 0 else 1 - q[:, 0]) * size, y + q[:, 1] * size], 1)
            if kind == 'f':
                c = mono if (mono and col not in ('white', 'black')) else col
                self.part(P, c, z=z0 + k * 0.01, width=lw, layer='text', rag=0.3)
            else:
                ink = INK; w = lw
                if col == 'thick': w = size * 0.08; ink = INK
                elif col == 'thickb': w = size * 0.1; ink = '#7b4a2c'
                elif col == 'blue': w = size * 0.07; ink = PIGMENTS['blue']
                self.part(None, None, paths=[P], ink=ink, width=w, z=z0 + k * 0.01, layer='text')

    def text(self, n=8, seed=None, signs=None):
        """a pseudo-text: a list of sign names (no repeats in a row)"""
        r = np.random.default_rng(seed if seed is not None else self._seed())
        pool = signs or self.SIGNS
        out = []
        for i in range(n):
            s = pool[int(r.integers(len(pool)))]
            while out and s == out[-1]:
                s = pool[int(r.integers(len(pool)))]
            out.append(s)
        return out

    def column(self, x0, y0, x1, y1, signs=None, facing=1, n=40, gap=0.14, rules=True, seed=None, mono=None, lw=1.6):
        """a vertical column of signs between x0 and x1, laid out by quadrats from the top; stops when full.
        rules: draw the black dividing lines on both sides.  Returns the y where the text ended."""
        W = x1 - x0
        em = W * 0.86
        seq = list(signs) if signs is not None else self.text(n, seed)
        boxes = {s: self._sign_box(s) for s in set(seq)}
        y = y0 + em * 0.08
        i = 0
        while i < len(seq):
            a = seq[i]; bx = boxes[a]; wa, ha = bx[2] - bx[0], bx[3] - bx[1]
            group = [a]
            if i + 1 < len(seq):
                b = seq[i + 1]; bb = boxes[b]; wb_, hb = bb[2] - bb[0], bb[3] - bb[1]
                if (wa <= 0.5 and wb_ <= 0.5) or (wa <= 0.7 and ha <= 0.7 and wb_ <= 0.7 and hb <= 0.7 and wa + wb_ <= 1.3):
                    group = [a, b]; mode = 'side'
                elif ha <= 0.45 and hb <= 0.45:
                    group = [a, b]; mode = 'stack'
            if len(group) == 1:
                mode = 'one'
            if mode == 'side':
                ws = [boxes[s][2] - boxes[s][0] for s in group]; hs = [boxes[s][3] - boxes[s][1] for s in group]
                scale = min(1.0, 0.95 / (sum(ws) + 0.08))
                rowh = max(hs) * em * scale
                xx = x0 + (W - (sum(ws) + 0.08) * em * scale) / 2
                if y + rowh > y1: break
                order = group if facing >= 0 else group[::-1]
                for s in order:
                    b = boxes[s]
                    gx = xx - (b[0] if facing >= 0 else (1 - b[2])) * em * scale
                    gy = y + (rowh - (b[3] - b[1]) * em * scale) / 2 - b[1] * em * scale
                    self.glyph(s, gx, gy, em * scale, facing, mono=mono)
                    xx += ((b[2] - b[0]) + 0.08) * em * scale
                y += rowh + gap * em; i += 2
            elif mode == 'stack':
                hs = [boxes[s][3] - boxes[s][1] for s in group]
                rowh = (sum(hs) + 0.06) * em
                if y + rowh > y1: break
                yy = y
                for s in group:
                    b = boxes[s]; wdt = b[2] - b[0]
                    gx = x0 + (W - wdt * em) / 2 - (b[0] if facing >= 0 else (1 - b[2])) * em
                    self.glyph(s, gx, yy - b[1] * em, em, facing, mono=mono)
                    yy += ((b[3] - b[1]) + 0.06) * em
                y += rowh + gap * em; i += 2
            else:
                b = boxes[a]
                rowh = (b[3] - b[1]) * em
                if y + rowh > y1: break
                gx = x0 + (W - wa * em) / 2 - (b[0] if facing >= 0 else (1 - b[2])) * em
                self.glyph(a, gx, y - b[1] * em, em, facing, mono=mono)
                y += rowh + gap * em; i += 1
        if rules:
            for xx in (x0, x1):
                self.part(None, None, paths=[np.array([[xx, y0], [xx, y1]], np.float32)], width=lw, layer='text')
        return y

    def numerals(self, value, x, y, size, facing=1):
        """a hieroglyphic number: hundreds as coils, tens as heel-bones, units as strokes (left to right)"""
        h, t, u = value // 100, (value // 10) % 10, value % 10
        xx = x
        for _ in range(h):
            self.glyph('coil', xx - size * 0.2, y, size, facing); xx += size * 0.5
        for _ in range(t):
            self.glyph('heel', xx - size * 0.15, y, size, facing); xx += size * 0.78
        for i in range(u):
            self.glyph('stroke', xx - size * 0.42, y, size, facing); xx += size * 0.3
        return xx

    # ------------------------------------------------------------------ 3,300 years
    def age(self, losses=(), cracks=9, flake=1.0, soot=0.5, fade=0.55, salt=0.5, specks=1.0, wear_amt=1.0, tide=0.5,
            zones=(), seed=None):
        """what time does to a secco painting.  losses: [(x, y, rx, ry), ...] plaster lost down to the mud;
        zones: [(x, y, r), ...] patches where the paint has come away down to the plaster (the red grid and
        sketch show through there)."""
        H, W = self.H, self.W
        r = np.random.default_rng(seed if seed is not None else self._seed())
        sd = lambda: int(r.integers(1 << 30))
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
        # ---- cracks: wandering grooves with branches
        crk = Image.new('L', (W * 2, H * 2), 0); d = ImageDraw.Draw(crk)
        crack_paths = []
        for i in range(cracks):
            x, y = r.uniform(0, W), r.choice([r.uniform(0, H * 0.3), r.uniform(H * 0.7, H), r.uniform(0, H)])
            a = r.uniform(0, 2 * np.pi); L = r.uniform(180, 620)
            pts = [(x, y)]
            for s in range(int(L / 5)):
                a += r.normal(0, 0.28); x += np.cos(a) * 5; y += np.sin(a) * 5
                pts.append((x, y))
                if r.random() < 0.012:
                    b = a + r.choice([-1, 1]) * r.uniform(0.6, 1.2); bx, by = x, y; br = [(bx, by)]
                    for _ in range(int(r.uniform(10, 40))):
                        b += r.normal(0, 0.3); bx += np.cos(b) * 4; by += np.sin(b) * 4; br.append((bx, by))
                    crack_paths.append((br, 1.6))
            crack_paths.append((pts, 2.6))
        for pts, wdt in crack_paths:
            d.line([(px * 2, py * 2) for px, py in pts], fill=255, width=int(wdt), joint='curve')
        C = np.asarray(crk.resize((W, H), Image.BOX), np.float32) / 255
        near_crack = blur(C, 3.0) * 4
        # ---- paint flakes (to the ground) and deeper flakes (to the plaster)
        vul = 0.25 + 0.3 * self.bluemap + 0.35 * np.clip(near_crack, 0, 1) + 0.2 * salt * smoothstep(0.78, 1.0, yy)
        vul += 0.25 * smoothstep(0.82, 1.0, np.maximum(np.abs(xx - 0.5) * 2, 0))
        n1 = noise2d(H, W, 7, 3, sd()); n2 = noise2d(H, W, 60, 3, sd())
        f1 = smoothstep(0.66, 0.7, n1 * 0.4 + n2 * 0.6 + (vul - 0.5) * 0.35 * flake)
        f1 = np.maximum(f1, smoothstep(0.5, 0.56, np.clip(near_crack, 0, 1) * noise2d(H, W, 4, 2, sd()) * 1.2) * flake)
        f1 *= smoothstep(0.02, 0.2, self.paintmap)                  # only where something was painted over the ground
        n3 = noise2d(H, W, 5, 2, sd())
        f2 = smoothstep(0.72, 0.76, n1 * 0.4 + n2 * 0.6 + (vul - 0.5) * 0.3 * flake) * smoothstep(0.35, 0.6, n3)
        if zones:
            zm = np.zeros((H, W), np.float32)
            Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
            for (zx, zy, zr) in zones:
                y0_, y1_ = int(max(0, zy - 2 * zr)), int(min(H, zy + 2 * zr)); x0_, x1_ = int(max(0, zx - 2 * zr)), int(min(W, zx + 2 * zr))
                dd = np.hypot(X[y0_:y1_, x0_:x1_] - zx, Y[y0_:y1_, x0_:x1_] - zy) / zr
                zm[y0_:y1_, x0_:x1_] = np.maximum(zm[y0_:y1_, x0_:x1_], np.clip(1.3 - dd, 0, 1))
            edge = noise2d(H, W, 14, 3, sd()) * 0.55 + n1 * 0.25 + noise2d(H, W, 3, 2, sd()) * 0.2
            zf = smoothstep(0.5, 0.54, zm * 0.8 + (edge - 0.5) * 1.1)
            f2 = np.maximum(f2, zf)
            f1 = np.maximum(f1, smoothstep(0.42, 0.46, zm * 0.8 + (edge - 0.5) * 1.1))   # a stepped halo of lost paint
        # ---- losses down to the mud
        f3 = np.zeros((H, W), np.float32)
        for (lx, ly, rx, ry) in losses:
            th = np.linspace(0, 2 * np.pi, 64, endpoint=False)
            wob = 1 + 0.22 * fbm1d(64, 8, 4, sd())
            pts = np.stack([lx + np.cos(th) * rx * wob, ly + np.sin(th) * ry * wob], 1)
            res = self._poly_mask([pts])
            if res:
                m, (x0, y0, x1, y1) = res
                f3[y0:y1, x0:x1] = np.maximum(f3[y0:y1, x0:x1], m)
        edge_noise = noise2d(H, W, 10, 3, sd()) * 0.7 + noise2d(H, W, 3, 2, sd()) * 0.3
        f3 = smoothstep(0.47, 0.53, blur(f3, 3) + (edge_noise - 0.5) * 0.6)
        chips = smoothstep(0.85, 0.89, noise2d(H, W, 9, 3, sd()) * 0.6 + n2 * 0.25 + 0.3 * smoothstep(0.86, 1.0, yy)
                           + 0.25 * smoothstep(0.9, 1.0, np.abs(xx - 0.5) * 2))
        f3 = np.maximum(f3, chips * salt)
        # around a loss the paint has flaked back in steps, and a ragged band of white gypsum shows
        around = np.clip(blur(f3, 7) * 3, 0, 1)
        f1 = np.maximum(f1, smoothstep(0.35, 0.6, around * (0.6 + 0.6 * n1)))
        f2 = np.maximum(f2, smoothstep(0.55, 0.8, around * (0.5 + 0.7 * n3)))
        rim = np.clip(smoothstep(0.22, 0.5, blur(f3, 1.4) + (edge_noise - 0.5) * 0.7) - f3, 0, 1)
        # paint rubbed thin in soft patches (hands, dust, brushing): partly back toward the ground or plaster
        wear = smoothstep(0.62, 0.9, noise2d(H, W, 26, 3, sd()) * 0.6 + n2 * 0.4) * 0.55 * wear_amt
        # ---- composite the strata
        img = self.img.copy()
        img = img * (1 - wear[..., None]) + (self.ground_img * 0.6 + self.under * 0.4) * wear[..., None]
        img = img * (1 - f1[..., None]) + self.ground_img * f1[..., None]
        img = img * (1 - f2[..., None]) + self.under * f2[..., None]
        img = img * (1 - rim[..., None]) + self.plaster * 0.93 * rim[..., None]
        img = img * (1 - f3[..., None]) + self.mud * f3[..., None]
        # ---- relief: a height field of the strata (px), lit from the upper left, shadows cast into the holes
        hgt = -0.5 * f1 - 0.6 * f2 - 1.0 * rim - 8.0 * f3 + (self.mud.mean(-1) - 0.3) * 3.0 * f3
        hb = blur(hgt, 0.7)
        gy, gx = np.gradient(hb)
        lit = np.clip(1 - 0.5 * (gx * self.light[0] + gy * self.light[1]), 0.5, 1.15)
        img *= lit[..., None]
        shd = height_shadow(hb, light=(self.light[0], self.light[1], 0.62), reach=30, step=1.0, soft=1.2)
        img *= (1 - 0.55 * shd)[..., None]
        ao = np.clip(blur(1 - f3, 6) * 1.6, 0, 1) * f3                # the floor of a hole gets less light near its walls
        img *= (1 - 0.3 * ao)[..., None]
        # cracks: dark groove, lit lower lip
        img *= (1 - 0.6 * C)[..., None]
        lip = np.clip(shift(C, 1, 1) - C, 0, 1)
        img = img + (1 - img) * 0.18 * lip[..., None]
        # ---- Egyptian blue decaying toward grey-green, pigments dulling
        fz = self.bluemap * fade * (0.45 + 0.55 * noise2d(H, W, 40, 3, sd()))
        img = img * (1 - fz[..., None]) + (img.mean(-1, keepdims=True) * 0.5 + hexc('#6f8b84') * 0.5) * fz[..., None]
        grey = img.mean(-1, keepdims=True)
        img = img * 0.9 + grey * 0.1
        # ---- grime and soot (lamp smoke rising to the ceiling), salt bloom near the floor
        g = noise2d(H, W, 220, 4, sd())
        grime = soot * (0.35 * smoothstep(0.4, 0.0, yy) + 0.12) * (0.4 + 0.8 * g)
        img *= (1 - 0.35 * grime[..., None] * (1 - hexc('#4a3a2c')[None, None, :]))
        blob = smoothstep(0.55, 0.85, noise2d(H, W, 300, 2, sd())) * smoothstep(0.5, 0.0, yy)
        img *= (1 - 0.14 * soot * blob)[..., None]
        if tide:                                              # moisture rose from the floor and dried at a ragged line
            tl = 0.82 + 0.04 * fbm1d(W, 400, 4, sd())[None, :]
            below = smoothstep(tl - 0.004, tl + 0.05, yy)
            line = np.exp(-((yy - tl) / 0.012) ** 2) * (0.6 + 0.4 * noise2d(H, W, 40, 2, sd()))
            img *= (1 - tide * (0.08 * below + 0.12 * line))[..., None]
            img = img * (1 - (tide * 0.12 * below)[..., None]) + hexc('#8a6a48') * (tide * 0.12 * below)[..., None]
        sb = salt * smoothstep(0.75, 1.0, yy) * smoothstep(0.55, 0.8, noise2d(H, W, 30, 3, sd()))
        img = img * (1 - 0.35 * sb[..., None]) + hexc('#efe9dd') * 0.35 * sb[..., None]
        # ---- fly specks and dust
        if specks:
            sp2 = Image.new('L', (W * 2, H * 2), 0); d2 = ImageDraw.Draw(sp2)
            for _ in range(int(350 * specks)):
                x, y = r.uniform(0, W * 2), r.uniform(0, H * 2); rr = r.uniform(0.9, 2.4)
                d2.ellipse([x - rr, y - rr, x + rr, y + rr], fill=int(r.uniform(140, 255)))
            S = np.asarray(sp2.resize((W, H), Image.BOX), np.float32) / 255
            img *= (1 - 0.55 * S[..., None])
        img += (self.T_grain[..., None] - 0.5) * 0.025
        vg = ((xx - 0.5) ** 2 * 1.2 + (yy - 0.48) ** 2 * 1.6)           # lamp-lit falloff toward the corners
        img *= (1 - 0.16 * vg)[..., None]
        self.img = np.clip(img, 0, 1)
        self.flakemap = np.clip(f1 + f2 + f3, 0, 1)

    # ------------------------------------------------------------------ stages
    def stage(self, name):
        self.stages.append((name, self.image()))

    def image(self):
        return Image.fromarray((np.clip(self.img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def save(self, path, stages_dir=None, quality=88):
        img = self.image()
        if str(path).lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
