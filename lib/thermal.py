"""thermal — a thermal-camera (long-wave infrared) picture: paint a temperature field, then look at it through an
uncooled microbolometer camera (numpy + Pillow only).

A thermal camera sees no colour and no light, only how warm every surface is, so the picture is never painted in RGB.
It is built in three passes, the same way the real thing works:

  1. scene (degrees C)   a float field at 2x the sensor resolution. The room sits at ambient, with warm air
                         layered under the ceiling and a cooler floor (`room`). Every object is painted at its own
                         temperature with its own gradients (`surface`): a pot is hottest at the base, a cat's nose
                         and ears run cooler than its eyes, window glass is coldest at the bottom. Shiny metal does
                         not show its own temperature but the room it reflects: apparent T = e*T + (1-e)*T_reflected
                         (`emissivity=`). Heat then leaks out of hot things:
                           soak     conduction / radiation stains nearby surfaces (the splashback behind a stove);
                           plume    buoyant hot air and steam rise along a wavering path, widen, cool while they
                                    mix and break into eddies and wisps; the same call with a downward path is cold
                                    air pouring out of an open fridge;
                           pool     cold air spreading over the floor in soft tongues;
                           prints   warm feet leave prints that fade and spread out with age;
                           reflect  glazed tiles mirror warm things (blurred, faint, fading with distance).
  2. camera              the field goes through the optics (blur), is box-sampled onto the sensor grid (640 x 360 by
                         default), gets temporal noise (NETD) and fixed-pattern column / row stripes and the
                         centre-cool "narcissus" vignette; a detail enhancer boosts small differences (seams, tile
                         grout, fur edges) while leaving big steps alone; automatic gain control maps degrees to
                         0..1 as a mix of a linear span and plateau histogram equalisation, so a room at 18-24 C
                         still gets most of the colours while the stove saturates; the 0..1 image is upscaled
                         (bilinear, a touch of the pixel grid kept) and coloured through a false-colour palette
                         (iron, rainbow, white_hot, black_hot, arctic).
  3. OSD                 drawn crisp at output resolution on top: translucent status bars (REC timer, date,
                         battery, emissivity), spot meters, boxes, hottest / coldest markers, a line profile inset and
                         a scale bar whose ticks sit where the (non-linear) AGC puts them. Every number is read off
                         the sensor image of that stage, so the readings always agree with the colours.

Stages are cheap: `stage(name)` keeps a copy of the field and the OSD items so far; `save()` renders every stage
with the final gain settings, so colours do not jump between snapshots.

Canvas coordinates (px of the output picture) are used everywhere; temperatures in degrees C.

    from thermal import Thermal
    t = Thermal(1920, 1080, seed=1, ambient=21)
    t.room(top=25, bottom=19)
    pot = t.rect(860, 380, 1000, 470, r=8)
    t.soak(pot, 95, reach=60, strength=0.4)             # the wall behind warms up
    t.surface(pot, t.ramp((0, 470), 98, (0, 380), 88))  # hottest at the base
    t.plume(t.rise(960, 380, 300, sway=30), 99, w0=10, w1=90)
    t.statusbar(rec='00:01:12'); t.scalebar(560, 1018, 1360, 1034)
    t.spot(930, 430, 'Sp1'); t.hottest()
    t.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font, blob_pts


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


# false-colour palettes: (position 0..1, colour) stops
PALETTES = {
    'iron': [(0.00, '#000005'), (0.06, '#0d0a40'), (0.14, '#1f0e6e'), (0.24, '#3d1192'), (0.36, '#6a14a0'),
             (0.47, '#9c1c94'), (0.57, '#c92f72'), (0.66, '#e64d45'), (0.75, '#f57322'), (0.84, '#faa012'),
             (0.92, '#fdd23a'), (0.97, '#fff38f'), (1.00, '#fffff0')],
    'rainbow': [(0.00, '#000000'), (0.10, '#16106a'), (0.24, '#1d4fd6'), (0.38, '#13b8d4'), (0.50, '#1fbf5a'),
                (0.62, '#c9dc1e'), (0.74, '#f7a215'), (0.87, '#e8301c'), (1.00, '#fff0ee')],
    'white_hot': [(0.0, '#000000'), (1.0, '#ffffff')],
    'black_hot': [(0.0, '#ffffff'), (1.0, '#000000')],
    'arctic': [(0.00, '#030719'), (0.25, '#0d2f7c'), (0.50, '#2a92cf'), (0.66, '#9fb7b0'), (0.80, '#e8a62a'),
               (1.00, '#fff3c4')],
}

WHITE, BLACK, RED, BLUE = (255, 255, 255), (0, 0, 0), (235, 40, 40), (70, 150, 255)


def lut(name, n=1024):
    stops = PALETTES[name]
    pos = np.array([p for p, _ in stops], np.float32)
    cols = np.stack([hexc(c) for _, c in stops])
    x = np.linspace(0, 1, n, dtype=np.float32)
    return np.stack([np.interp(x, pos, cols[:, i]) for i in range(3)], 1)


class Thermal:
    def __init__(self, W=1920, H=1080, sensor=(640, 360), ss=2, seed=0, ambient=21.0):
        self.W, self.H = W, H
        self.sw, self.sh = sensor
        self.ss = ss
        self.fw, self.fh = self.sw * ss, self.sh * ss
        self.kx, self.ky = self.fw / W, self.fh / H
        self.k = 0.5 * (self.kx + self.ky)
        self.amb = float(ambient)
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        yy, xx = np.mgrid[0:self.fh, 0:self.fw].astype(np.float32)
        self.X = (xx + 0.5) / self.kx
        self.Y = (yy + 0.5) / self.ky
        self.T = np.full((self.fh, self.fw), self.amb, np.float32)
        r = np.random.default_rng(seed + 7919)
        self._netd = r.normal(0, 1, (self.sh, self.sw)).astype(np.float32)
        self._col = r.normal(0, 1, self.sw).astype(np.float32)
        self._row = r.normal(0, 1, self.sh).astype(np.float32)
        self._cache = {}
        self.osd, self.stages = [], []
        self._lastfit = None
        self.camera()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------------ shapes -> masks (field resolution)
    def _fpts(self, pts):
        P = np.asarray(pts, np.float32).reshape(-1, 2)
        return np.stack([P[:, 0] * self.kx, P[:, 1] * self.ky], 1)

    def _draw(self, P, pad, fn, ss=3):
        """rasterise in a supersampled bounding-box tile only (fast for small shapes)"""
        m = np.zeros((self.fh, self.fw), np.float32)
        x0, y0 = np.floor(P.min(0) - pad).astype(int)
        x1, y1 = np.ceil(P.max(0) + pad).astype(int) + 1
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, self.fw), min(y1, self.fh)
        if x1 <= x0 or y1 <= y0: return m
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        fn(ImageDraw.Draw(im), [((x - x0) * ss, (y - y0) * ss) for x, y in P], ss)
        m[y0:y1, x0:x1] = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return m

    def poly(self, pts):
        """filled polygon (canvas px) -> anti-aliased mask"""
        return self._draw(self._fpts(pts), 1, lambda d, q, ss: d.polygon(q, fill=255))

    @staticmethod
    def closed(pts, per=10):
        """closed Catmull-Rom outline through control points"""
        P = np.asarray(pts, np.float32)
        Q = np.vstack([P[-1:], P, P[:2]])
        return spline(Q, per)[per:-per - 1] if len(P) > 2 else P

    def shape(self, pts, per=10):
        """smooth closed shape through control points"""
        return self.poly(self.closed(pts, per))

    def rect(self, x0, y0, x1, y1, r=0):
        if r <= 0: return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
        a = np.linspace(0, np.pi / 2, 8)
        pts = []
        for cx, cy, a0 in ((x1 - r, y0 + r, -np.pi / 2), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, np.pi / 2), (x0 + r, y0 + r, np.pi)):
            pts += [(cx + r * np.cos(a0 + t), cy + r * np.sin(a0 + t)) for t in a]
        return self.poly(pts)

    def ellipse(self, cx, cy, rx, ry, rot=0.0, n=72):
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        c, s = np.cos(np.radians(rot)), np.sin(np.radians(rot))
        x, y = rx * np.cos(t), ry * np.sin(t)
        return self.poly(np.stack([cx + x * c - y * s, cy + x * s + y * c], 1))

    def blob(self, cx, cy, rx, ry, rough=0.15, seed=None, rot=0.0, n=120):
        return self.poly(blob_pts(cx, cy, rx, ry, rough, n, self._seed() if seed is None else seed, np.radians(rot)))

    def line(self, pts, width):
        """stroke along a polyline (canvas px), round joints"""
        P = self._fpts(pts); w = width * self.k

        def fn(d, q, ss):
            d.line(q, fill=255, width=max(1, int(round(w * ss))), joint='curve')
            for x, y in (q[0], q[-1]):
                d.ellipse((x - w * ss / 2, y - w * ss / 2, x + w * ss / 2, y + w * ss / 2), fill=255)
        return self._draw(P, w + 2, fn)

    # ------------------------------------------------------------------ temperature fields
    def ramp(self, p0, t0, p1, t1, ease=1.0):
        """linear temperature ramp from canvas point p0 (t0) to p1 (t1), clamped beyond the ends"""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        u = ((self.X - p0[0]) * dx + (self.Y - p0[1]) * dy) / (dx * dx + dy * dy + 1e-9)
        u = np.clip(u, 0, 1) ** ease
        return (t0 + (t1 - t0) * u).astype(np.float32)

    def radial(self, cx, cy, rx, ry, t0, t1, power=1.0):
        """t0 at (cx, cy) falling to t1 at the ellipse rx, ry (and beyond)"""
        u = np.clip(np.hypot((self.X - cx) / rx, (self.Y - cy) / ry), 0, 1) ** power
        return (t0 + (t1 - t0) * u).astype(np.float32)

    def texture(self, scale, seed=0, octaves=3):
        """value noise in -0.5..0.5 at canvas feature size `scale` (cached)"""
        key = ('tex', int(scale), seed, octaves)
        if key not in self._cache:
            self._cache[key] = noise2d(self.fh, self.fw, max(2.0, scale * self.k), octaves, seed) - 0.5
        return self._cache[key]

    def room(self, top=25.0, bottom=19.0, y_top=0, y_bottom=None, wobble=0.25):
        """the background: still air layers warm under the ceiling and cool over the floor"""
        y_bottom = self.H if y_bottom is None else y_bottom
        self.T = self.ramp((0, y_top), top, (0, y_bottom), bottom) + wobble * 2 * self.texture(260, 11)

    def surface(self, mask, temp, emissivity=1.0, reflected=None, grain=0.0, grain_scale=14, soft=0.0, fuzz=0.0,
                fuzz_scale=6, limb=0.0, limb_px=12.0, seed=None):
        """paint an object: mask (0..1) at `temp` (a number or a field from ramp / radial).
        emissivity < 1 pulls it towards `reflected` (default ambient): polished metal reads like the room.
        grain: material non-uniformity in degrees; soft: blurred edge (px); fuzz: ragged fur edge (0..1);
        limb: degrees lost towards the silhouette of a rounded body (emissivity falls at grazing angles, and fur
        tips are cooler), over `limb_px` px."""
        m = mask
        if soft: m = blur(m, soft * self.k)
        if fuzz:
            n = self.texture(fuzz_scale, 101 if seed is None else seed, 2)
            m = smoothstep(0.5 - 0.22 * fuzz, 0.5 + 0.22 * fuzz, blur(m, 0.9 * fuzz_scale * self.k * fuzz) + 1.6 * fuzz * n)
            m = m * (blur(mask, 1.2 * fuzz_scale * self.k) > 0.02)
        T = np.asarray(temp, np.float32)
        if grain: T = T + 2 * grain * self.texture(grain_scale, 37 if seed is None else seed)
        if limb:
            inner = smoothstep(0.5, 0.97, blur(mask, limb_px * self.k))
            T = T - limb * (1 - inner)
        if emissivity < 1:
            Tr = self.amb if reflected is None else np.asarray(reflected, np.float32)
            T = emissivity * T + (1 - emissivity) * Tr
        self.T += m * (T - self.T)
        return m

    def warm(self, mask, dT):
        """add (or with dT < 0 remove) heat under a mask"""
        self.T += mask * np.asarray(dT, np.float32)

    def seam(self, pts, dT=-0.6, width=3.0):
        """a gap, joint or grout line: a thin line a little cooler (or warmer) than its surroundings"""
        self.T += self.line(pts, width) * dT

    def soak(self, mask, temp, reach=40.0, strength=0.5, onto=None):
        """heat soaking out of a hot (or cold) object into the surfaces around it: a blurred halo of its excess
        temperature. Call it before painting the object itself so the object keeps its own temperature."""
        ex = mask * (np.asarray(temp, np.float32) - self.amb)
        h = blur(ex, reach * self.k) * strength
        if onto is not None: h = h * onto
        self.T += h

    # ------------------------------------------------------------------ moving air: plumes and pools
    def _tex(self, seed, n=512):
        key = ('ptex', seed)
        if key not in self._cache: self._cache[key] = noise2d(n, n, 40, 4, seed)
        return self._cache[key]

    @staticmethod
    def _sample(tex, u, v):
        n = tex.shape[0] - 1
        u = np.mod(u, n); v = np.mod(v, n)
        i = u.astype(np.int32); j = v.astype(np.int32)
        fu, fv = u - i, v - j
        a, b, c, d = tex[j, i], tex[j, i + 1], tex[j + 1, i], tex[j + 1, i + 1]
        return (a * (1 - fu) + b * fu) * (1 - fv) + (c * (1 - fu) + d * fu) * fv

    def rise(self, x, y, height, sway=25.0, lean=0.0, n=9, seed=None):
        """control points of a buoyant plume rising from (x, y) by `height` px, swaying sideways, leaning (px/px)"""
        s = self._seed() if seed is None else seed
        w = fbm1d(n, 3, 3, s)
        hs = np.linspace(0, 1, n)
        return [(x + lean * h * height + sway * w[i] * h ** 0.8, y - h * height) for i, h in enumerate(hs)]

    def plume(self, path, temp, w0=8.0, w1=80.0, opacity=0.9, cool=1.7, eddy=0.8, puffs=0.4, wisp=0.5, seed=None,
              fade_in=0.04, fade_out=0.25):
        """a column of hot air / steam (temp > ambient) or cold air (temp < ambient) along a path (canvas control
        points, source first). It widens from w0 to w1 px, cools towards ambient as it mixes (`cool`), breaks
        into eddies (`eddy`) and wisps (`wisp`) the further it goes and pulses in puffs along its length."""
        s0 = self._seed() if seed is None else seed
        P = self._fpts(spline(path, 12))
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        S = np.concatenate([[0], np.cumsum(seg)]); L = float(S[-1])
        if L < 2: return
        m = max(4, int(L / 3)); ss = np.linspace(0, L, m)
        P = np.stack([np.interp(ss, S, P[:, 0]), np.interp(ss, S, P[:, 1])], 1); S = ss
        W0, W1 = w0 * self.k, w1 * self.k
        pad = W1 * 1.8 + 4
        x0, y0 = np.floor(P.min(0) - pad).astype(int); x1, y1 = np.ceil(P.max(0) + pad).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, self.fw), min(y1, self.fh)
        if x1 <= x0 or y1 <= y0: return
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        best = np.full(xx.shape, 1e9, np.float32); s_at = np.zeros_like(best); n_at = np.zeros_like(best)
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]; d = b - a; l2 = float(d @ d) + 1e-9
            t = np.clip(((xx - a[0]) * d[0] + (yy - a[1]) * d[1]) / l2, 0, 1)
            px, py = a[0] + t * d[0] - xx, a[1] + t * d[1] - yy
            dist = px * px + py * py
            sel = dist < best
            best = np.where(sel, dist, best)
            s_at = np.where(sel, S[i] + t * np.sqrt(l2), s_at)
            n_at = np.where(sel, (d[0] * (yy - a[1]) - d[1] * (xx - a[0])) / np.sqrt(l2), n_at)
        u = np.clip(s_at / L, 0, 1)
        w = W0 + (W1 - W0) * u ** 0.85
        lam = 0.55 * w + 3
        ta, tb = self._tex(s0 % 997), self._tex(s0 % 991 + 3)
        q = self._sample(tb, s_at * 40 / (lam * 2.2) + 17, n_at * 40 / (lam * 2.2) + 91) - 0.5
        e = self._sample(ta, s_at * 40 / lam + 60 * q + 113, n_at * 40 / lam + 60 * q + 29)
        n2 = n_at + (e - 0.5) * w * 1.1 * u ** 0.6
        across = np.exp(-2.2 * (n2 / w) ** 2)
        along = smoothstep(0, fade_in, u) * (1 - smoothstep(1 - fade_out, 1.0, u))
        th = 0.30 + 0.32 * u
        wisps = smoothstep(th - 0.16, th + 0.16, e)
        brk = np.clip(u * 2.5, 0, 1) * eddy
        dens = across * along * (1 - brk + brk * wisps)
        if wisp:
            fil = self._sample(ta, s_at * 40 / (lam * 0.45) + 300, n_at * 40 / (lam * 0.32) + 200)
            dens = dens * (1 - wisp * u * (1 - smoothstep(0.35, 0.65, fil)))
        if puffs:
            pf = fbm1d(1024, 90, 3, s0 % 9973)
            dens = dens * (1 - puffs * 0.5 * (1 + np.interp(s_at / (lam * 4 + 1) * 6, np.arange(1024), pf)) * u)
        dens = dens * (best < (w * 2.4) ** 2)
        Tp = self.amb + (temp - self.amb) * np.exp(-cool * u)
        a = np.clip(opacity * dens, 0, 1)
        sub = self.T[y0:y1, x0:x1]
        if temp >= self.amb: sub += a * np.maximum(Tp - sub, 0)
        else: sub += a * np.minimum(Tp - sub, 0)

    def pool(self, x, y, temp, reach=300.0, spread=(-30, 210), tongues=7, squash=0.42, width=0.35, soft=14.0,
             seed=None):
        """air that has fallen to the floor and spreads out over it in soft tongues from (x, y): cold air from
        an open fridge (temp < ambient) or warm air under a heater. reach: tongue length (px, on the floor);
        spread: range of directions in degrees on the floor plane (0 = right, 90 = towards the camera);
        squash: how flat the floor looks; strength falls off along each tongue"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        m = np.zeros((self.fh, self.fw), np.float32)
        for a in np.linspace(spread[0], spread[1], tongues) + r.uniform(-8, 8, tongues):
            L = reach * r.uniform(0.55, 1.0)
            c, s_ = np.cos(np.radians(a)), np.sin(np.radians(a))
            ts = np.linspace(0, 1, 14)
            half = L * width * (0.35 + 0.65 * np.sin(np.pi * np.clip(ts * 0.85 + 0.15, 0, 1)))
            cen = [(x + c * L * t_, y + s_ * L * t_ * squash) for t_ in ts]
            left = [(px - s_ * h, py + c * h * squash) for (px, py), h in zip(cen, half)]
            right = [(px + s_ * h, py - c * h * squash) for (px, py), h in zip(cen, half)]
            tongue = self.poly(left + right[::-1])
            dist = np.hypot(self.X - x, (self.Y - y) / squash) / L
            m = np.maximum(m, tongue * np.clip(1.15 - dist, 0, 1) ** 0.8)
        m = np.clip(blur(m, soft * self.k) * 1.3, 0, 1)
        d = np.asarray(temp, np.float32) - self.T
        self.T += m * (np.minimum(d, 0) if temp < self.amb else np.maximum(d, 0))

    # ------------------------------------------------------------------ traces
    def paw(self, x, y, size, heading=0.0, squash=0.45):
        """outline mask of one paw print (main pad + four toes) on a floor seen at an angle; heading in degrees
        (0 = walking to the right on the floor), squash = how flat the floor looks"""
        h = np.radians(heading)
        fx, fy = np.cos(h), np.sin(h)
        m = np.zeros((self.fh, self.fw), np.float32)
        parts = [(0.0, 0.0, 0.42, 0.36)] + [(0.5 * np.cos(a) - 0.0, 0.5 * np.sin(a), 0.15, 0.13)
                                           for a in np.radians([-62, -22, 22, 62])]
        for ax, ay, rx, ry in parts:
            cx = x + (ax * fx - ay * fy) * size
            cy = y + (ax * fy + ay * fx) * size * squash
            m = np.maximum(m, self.ellipse(cx, cy, rx * size, ry * size * squash * 1.2, n=24))
        return m

    def prints(self, steps, temp, size=16.0, squash=0.45, spread=1.0, kind='paw'):
        """footprints that cool and spread with age. steps: [(x, y, heading_deg, scale, age 0 fresh .. 1 gone)]"""
        for x, y, hd, sc, age in steps:
            if age >= 1: continue
            m = self.paw(x, y, size * sc, hd, squash) if kind == 'paw' else self.ellipse(x, y, size * sc * 0.5, size * sc * squash, hd)
            m = blur(m, (0.6 + 4.5 * age * spread) * self.k * sc)
            m = m / (m.max() + 1e-6)
            a = (1 - age) ** 1.4
            self.T += a * m * np.maximum(temp - self.T, 0)

    def reflect(self, region, axis_y, strength=0.25, blur_px=8.0, fade=160.0):
        """a glossy surface below `axis_y` (canvas px) mirrors whatever is warmer above it"""
        ay = axis_y * self.ky
        rows = np.arange(self.fh, dtype=np.float32) + 0.5
        src = np.clip(np.round(2 * ay - rows).astype(int), 0, self.fh - 1)
        R = blur(self.T[src, :], blur_px * self.k)
        f = (np.exp(-np.maximum(rows - ay, 0) / (fade * self.ky)) * (rows > ay))[:, None]
        self.T += np.maximum(R - self.T, 0) * strength * f * region

    # ------------------------------------------------------------------ camera
    def camera(self, palette='iron', span=None, agc=0.6, plateau=3.0, curve=None, netd=0.07, fpn=0.05, optics=0.7,
               dde=1.2, dde_clip=1.0, narcissus=0.35, pixel=0.25, saturate=None):
        """palette: iron / rainbow / white_hot / black_hot / arctic. span=(lo, hi) degrees or None (auto from the
        final scene); agc: 0 = plain linear span .. 1 = full plateau histogram equalisation; curve: optional manual
        tone curve [(degrees, level 0..1), ...] used instead of the linear span (agc still mixes HE on top) -- the
        hand-set level / span an operator dials in to give the room, the cat and the stove each their own colours;
        netd / fpn: temporal noise and column-stripe strength (degrees); optics: lens blur (sensor px); dde: detail
        enhancement gain for differences up to dde_clip degrees; narcissus: centre-cool vignette (degrees); pixel:
        how much of the sensor's pixel grid survives the upscale (0 smooth .. 1 hard blocks); saturate: a colour
        for everything above the span (off by default: the palette's white end)"""
        self.cam = dict(palette=palette, span=span, agc=agc, plateau=plateau, curve=curve, netd=netd, fpn=fpn, optics=optics,
                        dde=dde, dde_clip=dde_clip, narcissus=narcissus, pixel=pixel, saturate=saturate)

    def _sense(self, T):
        c = self.cam
        Tb = blur(T, c['optics'] * self.ss) if c['optics'] else T
        S = Tb.reshape(self.sh, self.ss, self.sw, self.ss).mean((1, 3))
        S = S + c['netd'] * self._netd + c['fpn'] * self._col[None, :] + 0.4 * c['fpn'] * self._row[:, None]
        yy, xx = np.mgrid[0:self.sh, 0:self.sw].astype(np.float32)
        r2 = ((xx / self.sw - 0.5) ** 2 + (yy / self.sh - 0.5) ** 2) / 0.5
        return (S - c['narcissus'] * (1 - r2)).astype(np.float32)

    def _enhance(self, S):
        g, cl = self.cam['dde'], self.cam['dde_clip']
        if not g: return S
        d = S - blur(S, 1.6)
        return S + g * d / (1 + np.abs(d) / cl)

    def _fit(self, S):
        c = self.cam
        if c['span']: lo, hi = c['span']
        elif c['curve']: lo, hi = c['curve'][0][0], c['curve'][-1][0]
        else: lo, hi = float(np.percentile(S, 0.2)), float(np.percentile(S, 99.8))
        edges = np.linspace(lo, hi, 513)
        h, _ = np.histogram(np.clip(S, lo, hi), edges)
        h = np.minimum(h.astype(np.float64), c['plateau'] * h.mean())
        cdf = np.concatenate([[0], np.cumsum(h)]); cdf /= cdf[-1]
        return dict(lo=lo, hi=hi, edges=edges.astype(np.float32), cdf=cdf.astype(np.float32))

    def level(self, v, fit=None):
        """where temperature v lands on the palette (0..1) under the current gain"""
        f = fit or self._lastfit
        v = np.asarray(v, np.float32)
        c = self.cam['curve']
        if c: lin = np.interp(v, [a for a, _ in c], [b for _, b in c])
        else: lin = np.clip((v - f['lo']) / (f['hi'] - f['lo']), 0, 1)
        he = np.interp(np.clip(v, f['lo'], f['hi']), f['edges'], f['cdf'])
        return (1 - self.cam['agc']) * lin + self.cam['agc'] * he

    def _colour(self, S, fit):
        t = self.level(self._enhance(S), fit).astype(np.float32)
        a = Image.fromarray(t, 'F')
        up = np.asarray(a.resize((self.W, self.H), Image.BILINEAR), np.float32)
        if self.cam['pixel']:
            nn = np.asarray(a.resize((self.W, self.H), Image.NEAREST), np.float32)
            up = up + self.cam['pixel'] * (nn - up)
        L = lut(self.cam['palette'])
        rgb = L[np.clip((up * (len(L) - 1)).astype(np.int32), 0, len(L) - 1)]
        if self.cam['saturate'] is not None:
            hot = np.asarray(Image.fromarray(((S > fit['hi']) * 255).astype(np.uint8)).resize((self.W, self.H), Image.NEAREST)) > 127
            rgb[hot] = hexc(self.cam['saturate'])
        return Image.fromarray((rgb * 255).astype(np.uint8))

    # ------------------------------------------------------------------ readings (sensor image of a stage)
    def _s(self, x, y):
        return x * self.sw / self.W, y * self.sh / self.H

    def _read(self, S, x, y, r=1):
        sx, sy = self._s(x, y)
        i, j = int(sx), int(sy)
        return float(S[max(j - r, 0):j + r + 1, max(i - r, 0):i + r + 1].mean())

    def _box(self, S, x0, y0, x1, y1):
        a, b = self._s(x0, y0); c, d = self._s(x1, y1)
        sub = S[int(b):int(d) + 1, int(a):int(c) + 1]
        j, i = np.unravel_index(np.argmax(sub), sub.shape)
        return float(sub.max()), float(sub.min()), float(sub.mean()), ((int(a) + i + 0.5) * self.W / self.sw, (int(b) + j + 0.5) * self.H / self.sh)

    def _extreme(self, S, kind, region):
        x0, y0, x1, y1 = region or (0, 0, self.W, self.H)
        a, b = self._s(x0, y0); c, d = self._s(x1, y1)
        sub = S[int(b):int(d), int(a):int(c)]
        idx = np.argmax(sub) if kind == 'max' else np.argmin(sub)
        j, i = np.unravel_index(idx, sub.shape)
        return float(sub[j, i]), ((int(a) + i + 0.5) * self.W / self.sw, (int(b) + j + 0.5) * self.H / self.sh)

    def _profile(self, S, p0, p1, n=160):
        t = np.linspace(0, 1, n)
        xs = (p0[0] + (p1[0] - p0[0]) * t) * self.sw / self.W
        ys = (p0[1] + (p1[1] - p0[1]) * t) * self.sh / self.H
        Sb = blur(S, 0.8)
        return self._sample_plain(Sb, xs, ys)

    @staticmethod
    def _sample_plain(A, xs, ys):
        h, w = A.shape
        xs = np.clip(xs - 0.5, 0, w - 1.001); ys = np.clip(ys - 0.5, 0, h - 1.001)
        i, j = xs.astype(int), ys.astype(int); fx, fy = xs - i, ys - j
        return (A[j, i] * (1 - fx) + A[j, i + 1] * fx) * (1 - fy) + (A[j + 1, i] * (1 - fx) + A[j + 1, i + 1] * fx) * fy

    # ------------------------------------------------------------------ OSD (recorded now, drawn at render time)
    def statusbar(self, rec='00:00:00', date='2026-01-01', clock='12:00:00', battery=0.8, emissivity=0.95,
                  mode='AUTO', height=58, reflected=None):
        """translucent top bar: red REC dot and timer, date / time, reflected temperature, emissivity, gain mode,
        SD card, battery"""
        self.osd.append(('status', dict(rec=rec, date=date, clock=clock, battery=battery, emissivity=emissivity,
                                        mode=mode, height=height, reflected=reflected)))

    def scalebar(self, x0, y0, x1, y1, ticks=None, unit='°C', label=None, height=None):
        """the colour scale with the AGC's tick positions; horizontal if wider than tall. A translucent bottom
        band is drawn under it when `height` is given"""
        self.osd.append(('scale', dict(box=(x0, y0, x1, y1), ticks=ticks, unit=unit, label=label, height=height)))

    def spot(self, x, y, label='Sp1', r=15, name=None, side='ne'):
        """spot meter: crosshair + label; its reading goes in the results table"""
        self.osd.append(('spot', dict(x=x, y=y, label=label, r=r, name=name, side=side)))

    def box(self, x0, y0, x1, y1, label='Bx1', name=None):
        """area meter: max / avg of a rectangle; marks the hottest pixel inside"""
        self.osd.append(('box', dict(b=(x0, y0, x1, y1), label=label, name=name)))

    def hottest(self, region=None):
        """red triangle + value on the hottest sensor pixel (in region=(x0, y0, x1, y1) or the whole frame)"""
        self.osd.append(('ext', dict(kind='max', region=region)))

    def coldest(self, region=None):
        """blue triangle + value on the coldest sensor pixel"""
        self.osd.append(('ext', dict(kind='min', region=region)))

    def profile(self, p0, p1, inset, label='L1', name=None, dash=12):
        """line profile: dashed line on the picture + an inset graph (x, y, w, h) of the temperature along it,
        the curve coloured through the palette"""
        self.osd.append(('profile', dict(p0=p0, p1=p1, inset=inset, label=label, name=name, dash=dash)))

    def results(self, x, y, width=330):
        """the measurement table (spots, boxes, profile) with their readings"""
        self.osd.append(('table', dict(x=x, y=y, width=width)))

    def reticle(self, x=None, y=None, r=26):
        """the centre crosshair with its live reading beside it"""
        self.osd.append(('reticle', dict(x=self.W / 2 if x is None else x, y=self.H / 2 if y is None else y, r=r)))

    def text(self, s, x, y, size=24, anchor='la', fill=WHITE, bold=False):
        self.osd.append(('text', dict(s=s, x=x, y=y, size=size, anchor=anchor, fill=fill, bold=bold)))

    # ------------------------------------------------------------------ OSD drawing
    def _font(self, size, bold=False):
        key = ('font', size, bold)
        if key not in self._cache: self._cache[key] = load_font('sans_bold' if bold else 'sans', size)
        return self._cache[key]

    def _t(self, d, xy, s, size, fill=WHITE, anchor='la', bold=False, stroke=2):
        d.text(xy, s, font=self._font(size, bold), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=BLACK)

    @staticmethod
    def _ln(d, pts, w=2, fill=WHITE, outline=BLACK):
        d.line(pts, fill=outline, width=w + 2)
        d.line(pts, fill=fill, width=w)

    def _cross(self, d, x, y, r, fill=WHITE):
        g = r * 0.35
        for a, b in (((x - r, y), (x - g, y)), ((x + g, y), (x + r, y)), ((x, y - r), (x, y - g)), ((x, y + g), (x, y + r))):
            self._ln(d, [a, b], 2, fill)

    def _tri(self, d, x, y, up, fill):
        s = 13
        pts = [(x, y), (x - s * 0.7, y + s), (x + s * 0.7, y + s)] if up else [(x, y), (x - s * 0.7, y - s), (x + s * 0.7, y - s)]
        d.polygon(pts, fill=fill, outline=BLACK)

    def _draw_osd(self, img, S, items, fit):
        base = img.convert('RGBA')
        over = Image.new('RGBA', img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        rows = []
        for kind, p in items:                       # translucent bands first
            if kind == 'status':
                d.rectangle((0, 0, self.W, p['height']), fill=(0, 0, 0, 105))
            if kind == 'scale' and p['height']:
                d.rectangle((0, self.H - p['height'], self.W, self.H), fill=(0, 0, 0, 105))
        for kind, p in items:
            if kind == 'status':
                h = p['height']; cy = h / 2
                d.ellipse((26, cy - 10, 46, cy + 10), fill=RED + (255,), outline=BLACK)
                self._t(d, (58, cy), 'REC', 26, anchor='lm', bold=True)
                self._t(d, (124, cy), p['rec'], 26, anchor='lm')
                self._t(d, (self.W / 2, cy), f"{p['date']}   {p['clock']}", 24, anchor='mm')
                bx = self.W - 120
                d.rectangle((bx, cy - 12, bx + 54, cy + 12), outline=WHITE + (255,), width=2)
                d.rectangle((bx + 54, cy - 5, bx + 59, cy + 5), fill=WHITE + (255,))
                for i in range(4):
                    if i < round(p['battery'] * 4):
                        d.rectangle((bx + 4 + i * 12.5, cy - 8, bx + 13 + i * 12.5, cy + 8), fill=WHITE + (255,))
                sx = bx - 52
                d.polygon([(sx, cy - 13), (sx + 16, cy - 13), (sx + 22, cy - 7), (sx + 22, cy + 13), (sx, cy + 13)], outline=WHITE + (255,), width=2)
                for i in range(3): d.line([(sx + 5 + i * 5, cy - 9), (sx + 5 + i * 5, cy - 3)], fill=WHITE + (255,), width=2)
                self._t(d, (sx - 26, cy), p['mode'], 24, anchor='rm', bold=True)
                self._t(d, (sx - 120, cy), f"ε {p['emissivity']:.2f}", 24, anchor='rm')
                if p.get('reflected') is not None:
                    self._t(d, (sx - 230, cy), f"Tr {p['reflected']:.0f}°C", 24, anchor='rm')
            elif kind == 'scale':
                self._draw_scale(d, p, fit)
            elif kind == 'spot':
                v = self._read(S, p['x'], p['y'])
                self._cross(d, p['x'], p['y'], p['r'])
                dx, dy = {'ne': (1, -1), 'nw': (-1, -1), 'se': (1, 1), 'sw': (-1, 1)}[p['side']]
                self._t(d, (p['x'] + dx * (p['r'] * 0.55 + 4), p['y'] + dy * (p['r'] * 0.55 + 4)), p['label'], 20,
                        anchor=('l' if dx > 0 else 'r') + ('d' if dy < 0 else 'a'), bold=True)
                rows.append((p['label'], p['name'], f'{v:5.1f}'))
            elif kind == 'box':
                x0, y0, x1, y1 = p['b']
                mx, mn, av, (hx, hy) = self._box(S, x0, y0, x1, y1)
                for seg in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                    self._ln(d, list(seg), 2)
                self._t(d, (x0 + 4, y0 - 4), p['label'], 20, anchor='ld', bold=True)
                self._cross(d, hx, hy, 8)
                rows.append((p['label'], p['name'], f'max {mx:.1f}  avg {av:.1f}'))
            elif kind == 'ext':
                v, (x, y) = self._extreme(S, p['kind'], p['region'])
                up = p['kind'] == 'max'
                self._tri(d, x, y + (3 if up else -3), up, (RED if up else BLUE) + (255,))
                self._t(d, (x + 14, y + (20 if up else -20)), f'{v:.1f}', 20, anchor='lm', bold=True)
            elif kind == 'profile':
                self._draw_profile(d, S, p, fit)
                pr = self._profile(S, p['p0'], p['p1'])
                rows.append((p['label'], p['name'], f'min {pr.min():.1f}  max {pr.max():.1f}'))
            elif kind == 'reticle':
                v = self._read(S, p['x'], p['y'])
                self._cross(d, p['x'], p['y'], p['r'])
                self._t(d, (p['x'] + p['r'] + 8, p['y'] - p['r'] * 0.4), f'{v:.1f}', 22, anchor='ls', bold=True)
            elif kind == 'text':
                self._t(d, (p['x'], p['y']), p['s'], p['size'], p['fill'] + (255,) if len(p['fill']) == 3 else p['fill'],
                        p['anchor'], p['bold'])
        for kind, p in items:
            if kind == 'table' and rows:
                x, y, w = p['x'], p['y'], p['width']
                lh = 34
                d.rectangle((x, y, x + w, y + 12 + lh * len(rows)), fill=(0, 0, 0, 110))
                for i, (lab, name, val) in enumerate(rows):
                    yy = y + 6 + lh * i + lh / 2
                    self._t(d, (x + 12, yy), lab, 21, anchor='lm', bold=True, stroke=1)
                    if name: self._t(d, (x + 66, yy), name, 19, anchor='lm', stroke=1)
                    self._t(d, (x + w - 12, yy), val + ('' if 'max' in val else ' °C'), 21, anchor='rm', stroke=1)
        return Image.alpha_composite(base, over).convert('RGB')

    def _draw_scale(self, d, p, fit):
        x0, y0, x1, y1 = p['box']
        horiz = (x1 - x0) >= (y1 - y0)
        L = lut(self.cam['palette'], 512)
        n = int(x1 - x0) if horiz else int(y1 - y0)
        for i in range(n):
            c = tuple(int(v * 255) for v in L[int(i / max(n - 1, 1) * 511) if horiz else int((1 - i / max(n - 1, 1)) * 511)]) + (255,)
            if horiz: d.line([(x0 + i, y0), (x0 + i, y1)], fill=c)
            else: d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)
        d.rectangle((x0 - 1, y0 - 1, x1 + 1, y1 + 1), outline=BLACK + (255,), width=1)
        d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), outline=WHITE + (200,), width=1)
        lo, hi = fit['lo'], fit['hi']
        ticks = p['ticks'] or [v for v in (0, 10, 20, 30, 40, 60, 80, 100, 150, 200) if lo < v < hi]
        last = -1e9
        for v in ticks:
            u = float(self.level(v, fit))
            if horiz:
                x = x0 + u * (x1 - x0)
                if x - last < 44: continue
                last = x
                d.line([(x, y1 + 2), (x, y1 + 9)], fill=WHITE + (255,), width=2)
                self._t(d, (x, y1 + 11), f'{v:g}', 19, anchor='ma', stroke=1)
            else:
                y = y1 - u * (y1 - y0)
                if abs(y - last) < 24: continue
                last = y
                d.line([(x0 - 9, y), (x0 - 2, y)], fill=WHITE + (255,), width=2)
                self._t(d, (x0 - 12, y), f'{v:g}', 19, anchor='rm', stroke=1)
        if horiz:
            self._t(d, (x0 - 14, (y0 + y1) / 2), f'{lo:.1f}', 22, anchor='rm', bold=True)
            self._t(d, (x1 + 14, (y0 + y1) / 2), f'{hi:.1f} {p["unit"]}', 22, anchor='lm', bold=True)
            if p['label']: self._t(d, (x0, y0 - 6), p['label'], 18, anchor='ld', stroke=1)
        else:
            self._t(d, ((x0 + x1) / 2, y0 - 10), f'{hi:.1f}', 22, anchor='md', bold=True)
            self._t(d, ((x0 + x1) / 2, y1 + 10), f'{lo:.1f}', 22, anchor='ma', bold=True)

    def _draw_profile(self, d, S, p, fit):
        (ax, ay), (bx, by) = p['p0'], p['p1']
        L = np.hypot(bx - ax, by - ay); dash = p['dash']
        k = 0
        while k * dash < L:
            t0, t1 = k * dash / L, min((k + 0.6) * dash / L, 1)
            self._ln(d, [(ax + (bx - ax) * t0, ay + (by - ay) * t0), (ax + (bx - ax) * t1, ay + (by - ay) * t1)], 1)
            k += 1
        self._t(d, (ax - 6, ay - 4), p['label'], 20, anchor='rd', bold=True)
        for (x, y) in (p['p0'], p['p1']): d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=WHITE + (255,), outline=BLACK)
        x, y, w, h = p['inset']
        d.rectangle((x, y, x + w, y + h), fill=(0, 0, 0, 120), outline=WHITE + (150,))
        pr = self._profile(S, p['p0'], p['p1'])
        lo, hi = float(np.floor(pr.min() - 1)), float(np.ceil(pr.max() + 1))
        gx0, gx1, gy0, gy1 = x + 52, x + w - 12, y + 34, y + h - 22
        for v in (lo, (lo + hi) / 2, hi):
            yy = gy1 - (v - lo) / (hi - lo) * (gy1 - gy0)
            d.line([(gx0, yy), (gx1, yy)], fill=(255, 255, 255, 60), width=1)
            self._t(d, (gx0 - 6, yy), f'{v:.0f}', 16, anchor='rm', stroke=1)
        Lp = lut(self.cam['palette'], 512)
        xs = gx0 + np.linspace(0, 1, len(pr)) * (gx1 - gx0)
        ys = gy1 - (pr - lo) / (hi - lo) * (gy1 - gy0)
        lev = self.level(pr, fit)
        for i in range(len(pr) - 1):                       # the palette colour of every sample, as a strip
            c = tuple(int(v * 255) for v in Lp[int(np.clip(lev[i], 0, 1) * 511)]) + (255,)
            d.rectangle((xs[i], gy1 + 4, xs[i + 1] + 1, gy1 + 12), fill=c)
        pts = list(zip(xs, ys))
        d.line(pts, fill=BLACK + (255,), width=5, joint='curve')
        d.line(pts, fill=WHITE + (255,), width=2, joint='curve')
        self._t(d, (x + 10, y + 6), p['label'] + (f'  {p["name"]}' if p['name'] else ''), 18, anchor='la', bold=True, stroke=1)
        self._t(d, (x + w - 10, y + 6), '°C', 16, anchor='ra', stroke=1)

    # ------------------------------------------------------------------ output
    def _render(self, T, n_osd, fit=None):
        S = self._sense(T)
        fit = fit or self._fit(S)
        self._lastfit = fit
        img = self._colour(S, fit)
        return self._draw_osd(img, S, self.osd[:n_osd], fit) if n_osd else img

    def render(self):
        S = self._sense(self.T)
        self._lastfit = self._fit(S)
        return self._render(self.T, len(self.osd), self._lastfit)

    def stage(self, name):
        self.stages.append((name, self.T.copy(), len(self.osd)))

    def save(self, path, stages_dir=None, quality=88):
        fit = self._fit(self._sense(self.T))
        img = self._render(self.T, len(self.osd), fit)
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, T, n) in enumerate(self.stages):
                self._render(T, n, fit).save(f'{stages_dir}/{i:02d}_{name}.png')
            img.save(f'{stages_dir}/{len(self.stages):02d}_final.png')
        return img
