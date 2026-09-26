"""colorpencil — soft Korean-style coloured-pencil illustration (numpy + Pillow only).

Model: pencil wax only catches on the *peaks* of the paper tooth, so every pass is
  deposit = strokes x pressure, thresholded against the paper tooth  -> the classic grainy pencil look.
Colour is built up in many light, short, directional strokes (hatching), layered and blended
multiplicatively like wax; edges fade softly; outlines are a light brown pencil; white gel-pen
highlights sparkle on top.

    from colorpencil import ColorPencil, hexc
    p = ColorPencil(1920, 1080, seed=1)
    p.paper()
    m = p.mask_poly(pts)
    p.hatch(m, '#f4a7b9', pressure=0.6, angle=0.9)       # base
    p.hatch(m * shadow, '#d9728f', pressure=0.5, angle=2.2)  # cross-hatched shading
    p.outline(pts, '#8a6a5a')
    p.sparkle(x, y, 8)
    p.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts, cjk_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


class ColorPencil:
    def __init__(self, W=1920, H=1080, seed=0, paper_tone='#fcf8f0'):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.base = np.ones((H, W, 3), np.float32) * hexc(paper_tone)
        self.img = self.base.copy()
        self.tooth = np.full((H, W), 0.5, np.float32)
        self.texts = []
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def noise(self, scale, octaves=3, seed=None):
        return noise2d(self.H, self.W, scale, octaves, seed if seed is not None else self._seed())

    # ------------------------------------------------------------ paper
    def paper(self):
        """drawing paper with a fine, slightly fibrous tooth"""
        t = 0.6 * self.noise(1.3, 2) + 0.3 * self.noise(4, 2) + 0.1 * self.noise(40, 2)
        self.tooth = (t - t.min()) / (t.max() - t.min())
        self.base = self.base * (0.985 + 0.02 * self.noise(200, 3))[..., None] * (1 - 0.018 * (self.tooth - 0.5))[..., None]
        self.img = self.base.copy()

    # ------------------------------------------------------------ masks
    def mask_poly(self, pts, feather=1.5):
        return blur(polygon_mask(self.H, self.W, pts, ss=2), feather)

    def mask_blob(self, cx, cy, rx, ry, rough=0.05, rot=0.0, feather=1.5):
        return self.mask_poly(blob_pts(cx, cy, rx, ry, rough=rough, n=120, seed=self._seed(), rot=rot), feather)

    def mask_ellipse(self, cx, cy, rx, ry, feather=1.2):
        return blur(np.clip(1 - (((self.XX - cx) / rx) ** 2 + ((self.YY - cy) / ry) ** 2), 0, 1) * 50, feather).clip(0, 1)

    # ------------------------------------------------------------ pencil
    def _strokes(self, mask, angle, spacing, length, width, jitter):
        """rasterise many short directional pencil strokes over the mask's bounding box -> coverage 0..1"""
        ys, xs = np.nonzero(mask > 0.02)
        if len(xs) == 0: return np.zeros((self.H, self.W), np.float32)
        x0, x1, y0, y1 = xs.min() - 20, xs.max() + 20, ys.min() - 20, ys.max() + 20
        acc = np.zeros((self.H, self.W), np.float32)
        area = (x1 - x0) * (y1 - y0)
        n = int(area / (spacing * np.mean(length)) * 3.5)
        dx, dy = np.cos(angle), np.sin(angle)
        for layer in range(3):                          # three passes so overlaps accumulate
            im = Image.new('L', (self.W, self.H), 0); d = ImageDraw.Draw(im)
            for _ in range(n // 3):
                cx, cy = self.rng.uniform(x0, x1), self.rng.uniform(y0, y1)
                L = self.rng.uniform(*length)
                a = angle + self.rng.normal(0, jitter)
                ex, ey = np.cos(a) * L / 2, np.sin(a) * L / 2
                bend = self.rng.normal(0, L * 0.04)
                pts = [(cx - ex, cy - ey), (cx - dy * bend, cy + dx * bend), (cx + ex, cy + ey)]
                d.line(pts, fill=int(self.rng.uniform(150, 255)), width=int(width))
            acc += np.asarray(im, np.float32) / 255
        return 1 - np.exp(-blur(acc, 0.5) * 1.3)          # overlapping strokes saturate

    def hatch(self, mask, colour, pressure=0.55, angle=0.9, spacing=5, length=(30, 90), width=2, jitter=0.12, edge_fade=10):
        """lay colour with short directional strokes; lighter toward the mask edge (soft pencil edge)"""
        col = hexc(colour) if isinstance(colour, str) else colour
        cov = self._strokes(mask, angle, spacing, length, width, jitter)
        soft = mask * (blur((mask > 0.5).astype(np.float32), edge_fade) * 0.6 + 0.4) if edge_fade else mask
        fill = smoothstep(0.15, 0.85, self.tooth + (pressure - 0.5) * 0.8)     # wax catches on tooth peaks; pressing harder reaches the valleys
        dep = np.clip(cov * soft * fill * (0.4 + pressure), 0, 0.95)
        self.img *= (1 - dep[..., None] * (1 - col))

    def shade(self, mask, colour, pressure=0.45, angle=2.2, **kw):
        """cross-hatched shading layer (different angle)"""
        self.hatch(mask, colour, pressure, angle, **kw)

    def outline(self, pts, colour='#8a6a5a', width=2.2, pressure=0.7, closed=True):
        """soft pencil line with slight wobble and varying pressure"""
        col = hexc(colour) if isinstance(colour, str) else colour
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        n = len(P)
        wob = fbm1d(n, max(4, n / 8), 3, self._seed())[:, None] * 1.2
        seg = P + np.stack([wob[:, 0], np.roll(wob[:, 0], 7)], 1)
        im = Image.new('L', (self.W, self.H), 0)
        ImageDraw.Draw(im).line([tuple(map(float, q)) for q in seg], fill=255, width=int(round(width)), joint='curve')
        line = blur(np.asarray(im, np.float32) / 255, 0.6)
        press = 0.55 + 0.45 * self.noise(90, 2)
        dep = np.clip(line * press * pressure * (0.75 + 0.6 * self.tooth) * 1.3, 0, 1)
        self.img *= (1 - dep[..., None] * (1 - col))

    def line(self, pts, colour='#8a6a5a', width=2.0, pressure=0.7):
        self.outline(pts, colour, width, pressure, closed=False)

    def sparkle(self, x, y, r=6, cross=True):
        """white gel-pen highlight: dot, or a small four-point sparkle"""
        a = np.clip((r * 0.45 - np.hypot(self.XX - x, self.YY - y)) / 0.8, 0, 1)
        if cross:
            a = np.maximum(a, np.clip((1.3 - np.abs(self.XX - x)) / 0.8, 0, 1) * (np.abs(self.YY - y) < r))
            a = np.maximum(a, np.clip((1.3 - np.abs(self.YY - y)) / 0.8, 0, 1) * (np.abs(self.XX - x) < r))
        self.img = self.img * (1 - a[..., None]) + np.array([1, 1, 1], np.float32) * a[..., None]

    def dots(self, mask, colour, n=20, r=(2, 4)):
        """seeds, sprinkles: small pencil dots inside a mask"""
        col = hexc(colour) if isinstance(colour, str) else colour
        ys, xs = np.nonzero(mask > 0.6)
        if len(xs) == 0: return
        for _ in range(n):
            k = int(self.rng.integers(len(xs)))
            rr = self.rng.uniform(*r)
            a = np.clip((rr - np.hypot(self.XX - xs[k], self.YY - ys[k] * 1.0)) / 1.0, 0, 1) * (0.6 + 0.4 * self.tooth)
            self.img *= (1 - a[..., None] * (1 - col))

    # ------------------------------------------------------------ text / output
    def text(self, s, x, y, size=48, colour='#8a6a5a'):
        self.texts.append((s, x, y, size, colour))

    def composite(self):
        out = Image.fromarray((np.clip(self.img, 0, 1) * 255).astype(np.uint8))
        fp = cjk_font()
        if self.texts and fp:
            dr = ImageDraw.Draw(out)
            for s, x, y, size, colour in self.texts:
                dr.text((x, y), s, font=ImageFont.truetype(fp, size, index=0), fill=tuple(int(v * 255) for v in hexc(colour)))
        return out

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
