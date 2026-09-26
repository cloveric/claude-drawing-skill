"""anime — Japanese anime background art, cel-shaded (numpy + Pillow only).

The look: saturated gradient skies, towering cumulus built from stacked puffs with *hard-edged*
light/shadow (cel shading), bloom and lens flare around the sun, crisp flat-shaded ground,
perspective roads, power lines, and characters with clean dark line art.

    from anime import Anime, hexc
    a = Anime(1920, 1080, seed=1)
    a.sky('#1f63c6', '#5aa9ec', '#d6f0ff', horizon=640)
    a.cumulus(1300, 520, 700, 380)
    a.sun_flare(1500, 180)
    a.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class Anime:
    def __init__(self, W=1920, H=1080, seed=0):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.img = np.ones((H, W, 3), np.float32)
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ compositing
    def fill(self, mask, colour, alpha=1.0):
        a = np.clip(mask * alpha, 0, 1)[..., None]
        self.img = self.img * (1 - a) + _c(colour) * a

    def screen(self, mask, colour, alpha=1.0):
        a = np.clip(mask * alpha, 0, 1)[..., None]
        c = _c(colour)
        self.img = 1 - (1 - self.img) * (1 - c * a)

    def gradient(self, mask, c0, c1, y0, y1, alpha=1.0):
        t = np.clip((self.YY - y0) / max(1, y1 - y0), 0, 1)[..., None]
        col = _c(c0) * (1 - t) + _c(c1) * t
        a = np.clip(mask * alpha, 0, 1)[..., None]
        self.img = self.img * (1 - a) + col * a

    def poly(self, pts, ss=2):
        return polygon_mask(self.H, self.W, pts, ss=ss)

    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def lines(self, pts, width, colour, alpha=1.0, closed=False):
        """clean anti-aliased line art"""
        im = Image.new('L', (self.W * 2, self.H * 2), 0)
        P = [(float(x) * 2, float(y) * 2) for x, y in pts]
        if closed: P = P + P[:1]
        ImageDraw.Draw(im).line(P, fill=255, width=max(1, int(round(width * 2))), joint='curve')
        m = np.asarray(im.resize((self.W, self.H), Image.LANCZOS), np.float32) / 255
        self.fill(m, colour, alpha)

    # ------------------------------------------------------------ sky
    def sky(self, top='#1f5fc4', mid='#58a6ec', horizon_col='#d9f1ff', horizon=640):
        t = np.clip(self.YY / horizon, 0, 1)
        c0, c1, c2 = _c(top), _c(mid), _c(horizon_col)
        k = smoothstep(0, 0.55, t)[..., None]; k2 = smoothstep(0.5, 1.0, t)[..., None]
        self.img = c0 * (1 - k) + c1 * k
        self.img = self.img * (1 - k2) + c2 * k2

    def cumulus(self, cx, base_y, w, h, light=(-0.6, -0.8), lit='#ffffff', mid='#edf3fc', shadow='#aec1e6',
                deep='#90a8d8', puffs=60, seed=None):
        """towering cumulus: many lumpy puffs stacked back-to-front. Each puff is cel-shaded with a
        crescent shadow = puff minus a copy of itself shifted toward the light (hard edge), so the
        shadows follow every bump like hand-painted anime clouds."""
        r = np.random.default_rng(seed if seed is not None else self._seed())
        lx, ly = light; ln = np.hypot(lx, ly); lx, ly = lx / ln, ly / ln
        items = []
        for i in range(puffs):
            x = cx + r.normal(0, w * 0.24)
            prof = np.exp(-((x - cx) / (w * 0.4)) ** 2)
            y = base_y - h * prof * r.uniform(0.1, 1.0) ** 0.8
            rad = (w * 0.035 + w * 0.075 * prof) * r.uniform(0.6, 1.3)
            items.append((y, x, rad))
        items.sort()                                      # far/top puffs first, lower/front puffs overlap them
        for (y, x, rad) in items:
            pts = blob_pts(x, y, rad, rad * r.uniform(0.85, 1.0), rough=0.06, n=48, seed=int(r.integers(1 << 30)))
            m = polygon_mask(self.H, self.W, pts, ss=2) * (self.YY < base_y + 2)
            litm = self.circle(x + lx * rad * 0.42, y + ly * rad * 0.42, rad * 0.98)
            core = self.circle(x - lx * rad * 0.35, y - ly * rad * 0.35, rad * 0.55)
            self.fill(m, shadow)                          # whole puff in shadow tone...
            self.fill(m * np.clip(litm, 0, 1), lit)       # ...then the lit part as a hard-edged disc toward the light
            self.fill(m * np.clip(litm, 0, 1) * np.clip(self.circle(x + lx * rad * 0.62, y + ly * rad * 0.62, rad * 0.9) * -1 + 1, 0, 1), mid, 0.8)
            self.fill(m * core * (1 - np.clip(litm, 0, 1)), deep, 0.45)
        base = self.poly([(cx - w * 0.55, base_y - h * 0.06), (cx + w * 0.55, base_y - h * 0.06), (cx + w * 0.6, base_y + 4), (cx - w * 0.6, base_y + 4)])
        self.fill(base * (self.YY > base_y - h * 0.09), shadow, 0.9)

    def sun_flare(self, x, y, strength=1.0, rays=9, flare=True):
        d = np.hypot(self.XX - x, self.YY - y)
        self.screen(np.exp(-(d / 60) ** 2), '#ffffff', 1.0 * strength)
        self.screen(np.exp(-(d / 260) ** 2), '#fff6d8', 0.55 * strength)
        self.screen(np.exp(-(d / 700) ** 2), '#fff1c8', 0.25 * strength)
        ang = np.arctan2(self.YY - y, self.XX - x)
        for k in range(rays):
            a0 = self.rng.uniform(-np.pi, np.pi); wdt = self.rng.uniform(0.015, 0.04)
            beam = np.exp(-((np.angle(np.exp(1j * (ang - a0)))) / wdt) ** 2) * np.exp(-d / 900)
            self.screen(beam, '#fffbe8', 0.22 * strength)
        if flare:
            cx, cy = self.W / 2, self.H / 2
            for t, r, col, al in [(0.45, 36, '#b7f0ff', 0.25), (0.7, 18, '#ffd0f0', 0.3), (1.05, 60, '#c9ffd9', 0.15), (1.35, 26, '#fff2b0', 0.25)]:
                fx, fy = x + (cx - x) * t * 2, y + (cy - y) * t * 2
                ring = np.clip(r - np.hypot(self.XX - fx, self.YY - fy), 0, 1) * 1.0
                self.screen(blur(ring, 1.5), col, al * strength)

    def sparkles(self, n=40, box=None, size=(1.5, 3.5), colour='#ffffff'):
        x0, y0, x1, y1 = box or (0, 0, self.W, self.H)
        for _ in range(n):
            x, y = self.rng.uniform(x0, x1), self.rng.uniform(y0, y1)
            r = self.rng.uniform(*size)
            self.screen(np.exp(-((self.XX - x) ** 2 + (self.YY - y) ** 2) / (2 * r * r)), colour, 0.9)

    # ------------------------------------------------------------ ground helpers
    def field(self, top_y, colours=('#7cc95a', '#4f9f45'), bands=6, vanish=(960, 600)):
        """cel-shaded field: alternating flat bands receding toward the horizon"""
        vx, vy = vanish
        for i in range(bands):
            t0, t1 = i / bands, (i + 1) / bands
            y_a = top_y + (self.H - top_y) * t0 ** 1.8
            y_b = top_y + (self.H - top_y) * t1 ** 1.8
            m = ((self.YY >= y_a) & (self.YY < y_b)).astype(np.float32)
            self.fill(m, colours[i % 2])

    def pole(self, x, base_y, height, width=6, colour='#3a3f4f'):
        self.lines([(x, base_y), (x, base_y - height)], width, colour)
        for k, cw in enumerate((height * 0.22, height * 0.16)):
            yy = base_y - height + 8 + k * height * 0.07
            self.lines([(x - cw / 2, yy), (x + cw / 2, yy)], max(2, width * 0.6), colour)
        return (x, base_y - height + 8)

    def wire(self, p0, p1, sag=30, width=1.6, colour='#2c3140'):
        t = np.linspace(0, 1, 40)
        xs = p0[0] + (p1[0] - p0[0]) * t
        ys = p0[1] + (p1[1] - p0[1]) * t + sag * 4 * t * (1 - t)
        self.lines(list(zip(xs, ys)), width, colour)

    # ------------------------------------------------------------ finishing
    def bloom(self, threshold=0.82, radius=18, amount=0.35):
        lum = self.img.mean(2)
        bright = np.clip((lum - threshold) / (1 - threshold), 0, 1)
        b = np.stack([blur(self.img[..., k] * bright, radius) for k in range(3)], 2)
        self.img = 1 - (1 - self.img) * (1 - b * amount)

    def vignette(self, amount=0.18):
        d = np.hypot((self.XX - self.W / 2) / (self.W / 2), (self.YY - self.H / 2) / (self.H / 2))
        self.img *= (1 - amount * np.clip(d - 0.55, 0, 1))[..., None]

    def composite(self):
        return Image.fromarray((np.clip(self.img, 0, 1) * 255).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite(); img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
