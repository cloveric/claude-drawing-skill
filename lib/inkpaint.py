"""inkpaint — procedural painting toolkit (numpy + Pillow only, no image model).

Everything is computed: rice paper, layered ink-wash mountains with mist, bristle brush strokes
with flying-white (飞白), texture strokes (皴), moss dots, pines, vermilion sun, birds, calligraphy.

    import sys; sys.path.insert(0, "<skill>/lib")
    from inkpaint import Painting, spline, curve, fbm1d
    p = Painting(1920, 1080, seed=7)
    p.paper()
    far = p.ridge(560, peaks=[(420, 150, 330), (1650, 110, 260)], rough=26)
    p.wash(far, dens=0.16, decay=170, mist_y=700)
    ...
    p.save("out.png")

Ink model: every mark adds density to a float buffer (ink `D` or vermilion `R`) with
over(): D = 1-(1-D)(1-a). Final colour = paper multiplied by ink, like pigment on paper.
Front wash layers occlude what is behind them (see wash()).
"""
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont

INK = np.array([28, 26, 24], np.float32) / 255
VERMILION = np.array([176, 52, 40], np.float32) / 255
PAPER = np.array([242, 236, 223], np.float32) / 255


# ================================================================ generic helpers
def blur(a, sigma):
    """fast gaussian approximation: 3 separable box blurs via cumulative sums (numpy only)"""
    if sigma <= 0: return a.copy()
    out = a.astype(np.float32)
    w = int(np.sqrt(12 * sigma * sigma / 3 + 1))
    w += (w % 2 == 0)
    r = w // 2
    for _ in range(3):
        for ax in (0, 1):
            pad = [(0, 0), (0, 0)]; pad[ax] = (r + 1, r)
            c = np.cumsum(np.pad(out, pad, mode='edge'), axis=ax, dtype=np.float64)
            hi = np.take(c, np.arange(w, c.shape[ax]), axis=ax)
            lo = np.take(c, np.arange(0, c.shape[ax] - w), axis=ax)
            out = ((hi - lo) / w).astype(np.float32)
    return out


def fbm1d(n, scale, octaves=5, seed=0):
    """1D fractal noise in [-1, 1] (ridgelines, wobble)"""
    r = np.random.default_rng(seed)
    x = np.arange(n, dtype=np.float32)
    out = np.zeros(n, np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        k = max(2, int(n / scale * 2 ** o) + 2)
        out += amp * np.interp(x, np.linspace(0, n - 1, k), r.random(k).astype(np.float32) * 2 - 1)
        tot += amp; amp *= 0.5
    return out / tot


def curve(p0, p1, bend, n=24, wig=0.0, seed=0):
    """curve from p0 to p1 bowing sideways by `bend` px, optional wiggle"""
    p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
    t = np.linspace(0, 1, n)[:, None]
    d = p1 - p0; nrm = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
    off = (4 * t * (1 - t)) * bend
    if wig: off = off + fbm1d(n, 6, 2, seed)[:, None] * wig
    return p0 + d * t + nrm * off


def spline(pts, per=14):
    """Catmull-Rom through control points — always use this instead of straight zig-zags"""
    P = np.asarray(pts, np.float32)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out, np.float32)


def kaiti_font():
    """a brush-like CJK font for titles/seals: $INKPAINT_FONT, else Kaiti/Songti (macOS), Noto CJK (Linux), KaiTi/SimSun (Windows)"""
    import os
    env = os.environ.get('INKPAINT_FONT')
    if env and os.path.exists(env): return env
    pats = ['/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/Kaiti.ttc',
            '/System/Library/Fonts/Supplemental/Songti.ttc', '/System/Library/Fonts/STHeiti Medium.ttc',
            '/usr/share/fonts/**/NotoSerifCJK*.tt[cf]', '/usr/share/fonts/**/NotoSansCJK*.tt[cf]',
            'C:/Windows/Fonts/simkai.ttf', 'C:/Windows/Fonts/simsun.ttc']
    for pat in pats:
        fs = glob.glob(pat, recursive=True)
        if fs: return fs[0]
    return None


# ================================================================ the painting
class Painting:
    def __init__(self, W=1920, H=1080, seed=0):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.xs = np.arange(W, dtype=np.float32)
        self.paper_rgb = np.ones((H, W, 3), np.float32) * PAPER
        self.D = np.zeros((H, W), np.float32)   # ink density
        self.R = np.zeros((H, W), np.float32)   # vermilion density
        self.texts = []                         # (kind, args) drawn at save time
        self.stages = []                        # snapshots for draw-on animation

    # ------------------------------------------------------------ noise / compositing
    def noise2d(self, scale, octaves=4, seed=0):
        r = np.random.default_rng(seed)
        out = np.zeros((self.H, self.W), np.float32); amp = 1.0; tot = 0.0
        for o in range(octaves):
            gh, gw = max(2, int(self.H / scale * 2 ** o) + 2), max(2, int(self.W / scale * 2 ** o) + 2)
            g = Image.fromarray(r.random((gh, gw)).astype(np.float32), mode='F')
            out += amp * np.asarray(g.resize((self.W, self.H), Image.BICUBIC), np.float32)
            tot += amp; amp *= 0.5
        out /= tot
        return (out - out.min()) / (out.max() - out.min() + 1e-6)

    @staticmethod
    def over(buf, a):
        np.copyto(buf, 1 - (1 - buf) * (1 - np.clip(a, 0, 1)))

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ paper
    def paper(self, fibers=2600, tone=PAPER):
        H, W, rng = self.H, self.W, self.rng
        p = np.ones((H, W, 3), np.float32) * np.asarray(tone, np.float32)
        p *= (0.965 + 0.05 * self.noise2d(260, 5, 1))[..., None]
        p *= (1 + 0.012 * blur(rng.normal(0, 1, (H, W)).astype(np.float32), 0.6))[..., None]
        fib = Image.new('L', (W, H), 0); fd = ImageDraw.Draw(fib)
        for _ in range(fibers):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            ang, ln = rng.uniform(0, np.pi), rng.uniform(8, 40)
            fd.line([(x + np.cos(ang + 0.3 * np.sin(t)) * t, y + np.sin(ang + 0.3 * np.sin(t)) * t) for t in np.linspace(0, ln, 6)],
                    fill=int(rng.uniform(10, 26)), width=1)
        p *= (1 - 0.35 * blur(np.asarray(fib, np.float32) / 255, 0.5))[..., None]
        self.paper_rgb = p

    # ------------------------------------------------------------ brush
    def stroke(self, pts, width, ink, dry=0.35, taper=(0.25, 0.35), jitter=0.6, red=False, seed=None):
        """bristle brush along polyline `pts`. width px; ink = peak opacity 0..1;
        dry = flying-white amount (0 wet .. 0.8 very dry); taper = (start, end) fraction."""
        buf = self.R if red else self.D
        W, H = self.W, self.H
        r = np.random.default_rng(seed if seed is not None else self._seed())
        pts = np.asarray(pts, np.float32)
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        L = float(seg.sum())
        if L < 2: return
        s = np.concatenate([[0], np.cumsum(seg)])
        nb = max(3, int(width * 1.3))
        br = max(0.6, width / nb * 1.7)                      # bristles overlap -> no stripes
        step = max(0.5, min(width * 0.22, br * 0.7))         # dab spacing relative to bristle -> no beads
        n = int(L / step) + 2
        ss = np.linspace(0, L, n)
        px = np.interp(ss, s, pts[:, 0]); py = np.interp(ss, s, pts[:, 1])
        tx = np.gradient(px); ty = np.gradient(py)
        tl = np.hypot(tx, ty) + 1e-6; tx /= tl; ty /= tl
        nx, ny = -ty, tx
        t = ss / L
        press = 0.35 + 0.65 * np.clip(np.minimum(t / max(taper[0], 1e-3), (1 - t) / max(taper[1], 1e-3)), 0, 1) ** 0.6
        offs = np.linspace(-0.5, 0.5, nb) + r.normal(0, 0.04, nb)
        load0 = r.uniform(0.75, 1.0, nb)
        wob = fbm1d(n, 40, 3, int(r.integers(1 << 30))) * jitter * width * 0.5
        rad = int(br * 2 + 2)
        ky, kx = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
        for b in range(nb):
            load = load0[b] * (1 - dry * t ** 1.2 * r.uniform(0.6, 1.4))
            gate = fbm1d(n, 25, 3, int(r.integers(1 << 30)))
            alive = (load * (0.75 + 0.5 * gate)) > (dry * 0.9)
            for i in range(n):
                if not alive[i]: continue
                w = width * press[i]
                cx = px[i] + nx[i] * (offs[b] * w + wob[i]); cy = py[i] + ny[i] * (offs[b] * w + wob[i])
                ix, iy = int(cx), int(cy)
                if ix < rad or iy < rad or ix >= W - rad - 1 or iy >= H - rad - 1: continue
                k = np.exp(-((kx - (cx - ix)) ** 2 + (ky - (cy - iy)) ** 2) / (2 * (br * press[i]) ** 2 + 1e-3))
                sl = buf[iy - rad:iy + rad + 1, ix - rad:ix + rad + 1]
                np.copyto(sl, 1 - (1 - sl) * (1 - k * ink * load[i] * 0.55))

    def dot(self, x, y, r, ink=0.8, squash=1.4, red=False):
        """moss dot / head / seed: soft ellipse"""
        self.over(self.R if red else self.D, ink * np.exp(-((self.XX - x) ** 2 + ((self.YY - y) * squash) ** 2) / (2 * r * r)))

    # ------------------------------------------------------------ landscape
    def ridge(self, base, peaks=(), rough=24, rough_scale=180, seed=None):
        """ridgeline y(x): base minus gaussian peaks (x, height, width) plus fractal roughness"""
        y = np.full(self.W, float(base), np.float32)
        for (px, h, w) in peaks:
            y -= h * np.exp(-((self.xs - px) / w) ** 2)
        return y + rough * fbm1d(self.W, rough_scale, 5, seed if seed is not None else self._seed())

    def peak(self, sx, sy, height=560, left_w=360, right_w=470, power=1.15, shoulders=(), rough=26, seed=None):
        """a main mountain: cone-ish peak at (sx, sy) with asymmetric slopes and optional shoulders (x, h, w)"""
        xs = self.xs
        y = sy + height * (1 - np.exp(-np.abs(xs - sx) / np.where(xs < sx, left_w, right_w))) ** power
        for (x, h, w) in shoulders:
            y -= h * np.exp(-((xs - x) / w) ** 2)
        y += rough * fbm1d(self.W, 70, 5, seed if seed is not None else self._seed()) * np.clip(np.abs(xs - sx) / 120, 0, 1)
        return y

    def wash(self, ridge, dens=0.3, decay=180, tex=110, edge=0.35, mist_y=None, mist_h=100, occlude=True, seed=None):
        """ink-wash mass below `ridge`: dark at the top edge, fading downward, textured, with a wet rim.
        Front layers occlude what was painted behind (paint far -> near)."""
        seed = seed if seed is not None else self._seed()
        depth = self.YY - ridge[None, :]
        body = np.where(depth > 0, np.exp(-depth / decay), 0).astype(np.float32)
        tx = 0.55 + 0.45 * self.noise2d(tex, 4, seed)
        a = body * np.clip((depth + 2) / 5, 0, 1) * tx * (0.85 + 0.15 * self.noise2d(6, 2, seed + 1)) * dens
        m = (depth > 0).astype(np.float32)
        a += np.clip(blur(m, 2.2) - blur(m, 9), 0, None) * dens * edge * tx
        if mist_y is not None:
            a *= 1 - 0.92 * np.exp(-((self.YY - mist_y - 60 * (self.noise2d(400, 3, seed + 2) - 0.5)) / mist_h) ** 2)
        if occlude:
            np.multiply(self.D, 1 - 0.97 * np.clip((depth + 1) / 6, 0, 1), out=self.D)
        self.over(self.D, a)
        return a

    def mist(self, y, h=70, strength=0.8, patchy=True, seed=None):
        """horizontal mist band that lifts ink (paint it after the things it should swallow)"""
        seed = seed if seed is not None else self._seed()
        m = np.exp(-((self.YY - y - 50 * (self.noise2d(380, 3, seed) - 0.5)) / h) ** 2)
        if patchy: m *= 0.6 + 0.4 * self.noise2d(160, 3, seed + 1)
        np.multiply(self.D, 1 - strength * m, out=self.D)

    def cun(self, ridge, x0, x1, n=150, shadow_x=None, spread=70, max_y=None, ink=0.26):
        """dry texture strokes (皴) hanging from a ridge, denser/darker on the shadow side (x < shadow_x)"""
        rng = self.rng
        max_y = max_y if max_y is not None else self.H - 60
        sx = shadow_x if shadow_x is not None else (x0 + x1) / 2
        for _ in range(n):
            left = rng.random() < 0.72
            x = rng.uniform(x0, sx - 20) if left else rng.uniform(sx + 20, x1)
            top = ridge[int(np.clip(x, 0, self.W - 1))]
            dd = abs(rng.normal(0, spread)); y = top + 10 + dd
            if y > max_y: continue
            dirx = np.sign(sx - x)
            ln = rng.uniform(40, 120)
            ctrl = [(x, y), (x - dirx * ln * 0.25 + rng.normal(0, 6), y + ln * 0.5), (x - dirx * ln * 0.55 + rng.normal(0, 10), y + ln)]
            self.stroke(spline(ctrl, 8), rng.uniform(1.6, 3.6), (ink if left else ink * 0.55) * np.exp(-dd / 150), dry=0.65)

    def moss(self, ridge, x0, x1, n=70, depth=(2, 26)):
        """moss dots (苔点) along a ridge"""
        for _ in range(n):
            x = self.rng.uniform(x0, x1)
            self.dot(x, ridge[int(np.clip(x, 0, self.W - 1))] + self.rng.uniform(*depth), self.rng.uniform(1.6, 3.4), 0.75)

    def ridge_line(self, ridge, x0, x1, width=2.2, ink=0.3):
        """light, broken ridge accent — keep it light or it reads as a cartoon outline"""
        pts = np.stack([self.xs[::6], ridge[::6] + 2], 1)
        pts = pts[(pts[:, 0] > x0) & (pts[:, 0] < x1)]
        self.stroke(pts, width, ink, dry=0.6, taper=(0.1, 0.1))

    def trails(self, ridge, summit, n=16, x_range=None, start_y=(930, 990), red_index=None, seed=None):
        """winding switchback trails from the foot to one summit; returns the list of trail polylines"""
        rng = np.random.default_rng(seed if seed is not None else self._seed())
        SX, SY = summit
        lo, hi = x_range if x_range else (SX - 560, SX + 620)
        out = []
        for i in range(n):
            for _ in range(50):
                sx = rng.uniform(lo, hi)
                if ridge[int(np.clip(sx, 0, self.W - 1))] < start_y[0] - 30: break
            sy = rng.uniform(*start_y)
            zig = int(rng.integers(4, 8)); pts = []
            for k in range(zig + 1):
                t = k / zig
                amp = (1 - t) * rng.uniform(40, 110)
                pts.append((sx + (SX - sx) * t ** 0.9 + amp * (1 if k % 2 else -1), sy + (SY + 10 - sy) * t))
            pts[-1] = (SX + rng.normal(0, 2), SY + 10)
            c = spline(pts, 16)
            c[:, 1] = np.maximum(c[:, 1], ridge[np.clip(c[:, 0].astype(int), 0, self.W - 1)] + 5)
            out.append(c)
        for i, c in enumerate(out):
            if i == red_index:
                self.stroke(c, 2.0, 0.8, dry=0.3, jitter=0.2, red=True)
            else:
                self.stroke(c, rng.uniform(1.1, 1.5), rng.uniform(0.24, 0.34), dry=0.55, jitter=0.3)
        return out

    # ------------------------------------------------------------ motifs
    def pine(self, root, top, bend=70, branches=(), extra_tufts=(), trunk_w=16):
        """写意 pine: trunk + bark arcs + branches + fan-shaped needle tufts over a soft wash"""
        rng = self.rng
        trunk = curve(root, top, bend, 30, wig=12, seed=self._seed())
        self.stroke(trunk, trunk_w, 0.62, dry=0.35, taper=(0.02, 0.45), jitter=0.5)
        for _ in range(18):
            q = trunk[int(rng.integers(3, 26))]
            self.stroke(curve((q[0] - 7, q[1] + rng.uniform(-3, 3)), (q[0] + 5, q[1] + rng.uniform(4, 10)), rng.normal(-3, 2), 8), 1.4, 0.3, dry=0.5, taper=(0.3, 0.3))
        tips = list(extra_tufts)
        for (a0, b0, bnd) in branches:
            c = curve(a0, b0, bnd, 20, wig=7, seed=self._seed())
            self.stroke(c, trunk_w * 0.44, 0.62, dry=0.4, taper=(0.03, 0.55))
            tips += [tuple(b0), tuple(c[12])]
        for (bx, by) in tips:
            for _ in range(2):
                cx, cy = bx + rng.normal(0, 16), by + rng.normal(0, 8)
                self.over(self.D, 0.22 * np.exp(-(((self.XX - cx) / 46) ** 2 + ((self.YY - cy + 8) / 20) ** 2)))
                for a in np.linspace(-np.pi * 0.95, -np.pi * 0.05, 17):
                    ln = rng.uniform(26, 42)
                    self.stroke([(cx, cy + 4), (cx + np.cos(a) * ln, cy + np.sin(a) * ln * 0.5)], 1.2, 0.55, dry=0.25, taper=(0.05, 0.6))

    def rock(self, ridge, dens=0.7, texture=45):
        """dense foreground rock mass with dry texture"""
        self.wash(ridge, dens=dens, decay=260, tex=50, edge=0.6)
        rng = self.rng
        xs_ok = np.where(ridge < self.H)[0]
        if len(xs_ok) == 0: return
        for _ in range(texture):
            x = rng.uniform(xs_ok.min() + 10, xs_ok.max() - 10); top = ridge[int(x)]
            y = top + abs(rng.normal(0, 60)) + 6
            if y > self.H - 5: continue
            self.stroke(curve((x, y), (x + rng.normal(-12, 10), y + rng.uniform(20, 60)), rng.normal(0, 8), 10), rng.uniform(2.5, 5), 0.3, dry=0.7)

    def sun(self, x, y, r=46, red=True):
        dist = np.hypot(self.XX - x, self.YY - y)
        disc = (dist < r).astype(np.float32)
        s = np.clip((r - dist) / 2.5, 0, 1) * (0.78 + 0.22 * self.noise2d(12, 3, self._seed()))
        s += np.clip(blur(disc, 3) - blur(disc, 10), 0, None) * 0.35
        self.over(self.R if red else self.D, s * 0.9)

    def birds(self, items):
        """items: [(x, y, scale)] — two-stroke flying birds"""
        for (bx, by, s) in items:
            self.stroke(curve((bx - 14 * s, by), (bx, by + 2 * s), -6 * s, 8), 1.6, 0.7, dry=0.2)
            self.stroke(curve((bx, by + 2 * s), (bx + 14 * s, by - 2 * s), -6 * s, 8), 1.6, 0.7, dry=0.2)

    def pagoda(self, x, y):
        """tiny pagoda/pavilion sitting on (x, y)"""
        for (a, b) in [((x - 16, y - 6), (x + 16, y - 6)), ((x - 12, y - 16), (x + 12, y - 16)), ((x - 8, y - 25), (x + 8, y - 25))]:
            self.stroke(curve(a, b, -3, 10), 2.2, 0.8, dry=0.15, taper=(0.2, 0.2))
        self.stroke([(x, y - 36), (x, y - 25)], 1.6, 0.8, dry=0.1)
        for a in (-6, 6):
            self.stroke([(x + a, y - 6), (x + a, y + 6)], 1.6, 0.7, dry=0.1)

    def traveller(self, x, y):
        """a tiny walking figure standing at (x, y)"""
        self.stroke([(x, y - 7), (x + 0.5, y + 3)], 2.4, 0.75, dry=0.1, taper=(0.3, 0.3))
        self.dot(x, y - 11, 1.5, 0.8, squash=1.0)

    # ------------------------------------------------------------ text (rendered at save time, on top)
    def title_vertical(self, text, x, y, size=92, gap=1.17, color=(34, 31, 29)):
        self.texts.append(('vtext', (text, x, y, size, gap, color)))

    def seal(self, text, x, y, size=40, color=(172, 50, 40)):
        self.texts.append(('seal', (text, x, y, size, color)))

    # ------------------------------------------------------------ output
    def composite(self):
        img = self.paper_rgb * (1 - self.D[..., None] * (1 - INK))
        img = img * (1 - self.R[..., None] * (1 - VERMILION / np.maximum(self.paper_rgb, 1e-3)).clip(0, 1))
        out = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
        font_path = kaiti_font()
        if self.texts and not font_path:
            print('inkpaint: no CJK font found (set INKPAINT_FONT); titles/seals skipped')
        if font_path and self.texts:
            dr = ImageDraw.Draw(out)
            for kind, args in self.texts:
                if kind == 'vtext':
                    text, x, y, size, gap, color = args
                    f = ImageFont.truetype(font_path, size, index=0)
                    for i, ch in enumerate(text):
                        dr.text((x, y + i * size * gap), ch, font=f, fill=color)
                else:
                    text, x, y, size, color = args
                    f = ImageFont.truetype(font_path, size, index=0)
                    w, h = size * 1.4, size * 1.25 * len(text) + size * 0.3
                    dr.rectangle((x, y, x + w, y + h), fill=color)
                    for i, ch in enumerate(text):
                        dr.text((x + size * 0.2, y + size * 0.2 + i * size * 1.25), ch, font=f, fill=(244, 238, 226))
        return out

    def stage(self, name):
        """snapshot the painting so far (for a stage-by-stage draw-on animation)"""
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite()
        img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
