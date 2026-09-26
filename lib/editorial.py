"""editorial — modern editorial illustration with a risograph-print feel (numpy + Pillow only).

The look: a limited palette of spot inks on cream stock; each ink is printed as its own layer with
fine stochastic grain, slightly uneven density and a little mis-registration; inks are translucent,
so overlaps *overprint* (multiply) into new colours; shading is done with halftone dots; a wobbly
hand-drawn ink line holds it together; big simple shapes and stylised figures carry the idea.

    from editorial import Editorial, hexc
    e = Editorial(1920, 1080, seed=1)
    e.fill(e.circle(1500, 300, 260), '#ffc857')             # spot ink
    e.halftone(e.circle(1500, 300, 260) * shadow, '#ff6b57')
    e.line(pts, '#26335c', 4)
    e.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class Editorial:
    def __init__(self, W=1920, H=1080, seed=0, stock='#f4eee3', misreg=3.0):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        paper = np.ones((H, W, 3), np.float32) * _c(stock)
        paper *= (0.985 + 0.03 * noise2d(H, W, 180, 3, 1))[..., None]
        specks = (self.rng.random((H, W)) > 0.9993).astype(np.float32)
        paper *= (1 - 0.25 * blur(specks, 0.7))[..., None]
        self.img = paper
        self.misreg = misreg
        self.offsets = {}                                  # per-ink registration offset
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ shapes
    def poly(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=2)

    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def ellipse(self, cx, cy, rx, ry):
        return np.clip((1 - (((self.XX - cx) / rx) ** 2 + ((self.YY - cy) / ry) ** 2)) * min(rx, ry) / 2, 0, 1)

    def rrect(self, x0, y0, x1, y1, r):
        cx = np.clip(self.XX, x0 + r, x1 - r); cy = np.clip(self.YY, y0 + r, y1 - r)
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def blob(self, cx, cy, rx, ry, rough=0.08, rot=0.0):
        return self.poly(blob_pts(cx, cy, rx, ry, rough=rough, n=90, seed=self._seed(), rot=rot))

    # ------------------------------------------------------------ inks
    def _shift(self, m, key):
        if key not in self.offsets:
            a = self.rng.uniform(0, 2 * np.pi)
            self.offsets[key] = (int(round(np.cos(a) * self.misreg)), int(round(np.sin(a) * self.misreg)))
        dx, dy = self.offsets[key]
        out = np.zeros_like(m)
        ys = slice(max(dy, 0), self.H + min(dy, 0)); ys0 = slice(max(-dy, 0), self.H + min(-dy, 0))
        xs = slice(max(dx, 0), self.W + min(dx, 0)); xs0 = slice(max(-dx, 0), self.W + min(-dx, 0))
        out[ys, xs] = m[ys0, xs0]
        return out

    def fill(self, mask, ink, density=0.92, grain=0.22):
        """print one spot ink over `mask`: grainy, slightly uneven, mis-registered, overprinting (multiply)"""
        col = _c(ink)
        m = self._shift(mask, ink if isinstance(ink, str) else tuple(ink))
        uneven = density - 0.08 * noise2d(self.H, self.W, 140, 3, self._seed())
        g = self.rng.random((self.H, self.W)).astype(np.float32)
        keep = smoothstep(-grain * 0.2, grain * 0.2, uneven - g)      # most pixels take ink; a few specks drop out
        dots = np.clip(blur(np.clip(m, 0, 1) * keep, 0.45), 0, 1)
        self.img *= (1 - dots[..., None] * (1 - col))

    def halftone(self, mask, ink, cell=11, angle=0.5, amount=0.6):
        """halftone dots: dot size follows `mask * amount` (use for shading, gradients, texture)"""
        c, s = np.cos(angle), np.sin(angle)
        u = (self.XX * c + self.YY * s) / cell; v = (-self.XX * s + self.YY * c) / cell
        du = u - np.round(u); dv = v - np.round(v)
        d = np.hypot(du, dv)
        rad = np.sqrt(np.clip(mask * amount, 0, 1)) * 0.62
        dots = np.clip((rad - d) * cell / 1.2, 0, 1)
        self.fill(dots, ink, density=0.95, grain=0.1)

    def line(self, pts, ink='#26335c', width=4, wobble=1.6, closed=False, breaks=0.0):
        """hand-drawn ink line: wobbly, slightly varying weight, optionally broken"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        n = len(P)
        wob = np.stack([fbm1d(n, max(3, n / 6), 3, self._seed()), fbm1d(n, max(3, n / 6), 3, self._seed())], 1) * wobble
        P = P + wob
        im = Image.new('L', (self.W * 2, self.H * 2), 0); d = ImageDraw.Draw(im)
        wv = width * (0.8 + 0.4 * (fbm1d(n, max(3, n / 4), 2, self._seed()) + 1) / 2)
        for i in range(n - 1):
            if breaks and self.rng.random() < breaks: continue
            d.line([(P[i, 0] * 2, P[i, 1] * 2), (P[i + 1, 0] * 2, P[i + 1, 1] * 2)], fill=255, width=max(1, int(wv[i] * 2)))
            r = wv[i]
            d.ellipse((P[i + 1, 0] * 2 - r, P[i + 1, 1] * 2 - r, P[i + 1, 0] * 2 + r, P[i + 1, 1] * 2 + r), fill=255)
        m = np.asarray(im.resize((self.W, self.H), Image.LANCZOS), np.float32) / 255
        self.fill(m, ink, density=0.97, grain=0.12)

    def dashes(self, pts, ink='#26335c', width=3, dash=14, gap=10):
        P = spline(pts, 20) if len(pts) > 2 else np.asarray(pts, np.float32)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)])
        t = 0.0
        while t < s[-1]:
            a, b = t, min(t + dash, s[-1])
            q = [(np.interp(x, s, P[:, 0]), np.interp(x, s, P[:, 1])) for x in np.linspace(a, b, 4)]
            self.line(q, ink, width, wobble=0.4)
            t += dash + gap

    def stars(self, items, ink='#26335c', width=3):
        """little sparkle marks: (x, y, size)"""
        for (x, y, r) in items:
            self.line([(x - r, y), (x + r, y)], ink, width, wobble=0.3)
            self.line([(x, y - r), (x, y + r)], ink, width, wobble=0.3)

    # ------------------------------------------------------------ output
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
