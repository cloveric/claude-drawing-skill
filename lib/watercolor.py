"""watercolor — transparent watercolour on cold-press paper (numpy + Pillow only).

Model: the paper is white; every wash is a *glaze* that multiplies the image by the pigment's
transmittance  img *= 1 - d * (1 - colour)  (subtractive, so overlaps darken and mix like real paint).
Each glaze adds what makes watercolour read as watercolour:
  - wet edges   : pigment migrates to the rim of a wet shape -> darker outline
  - granulation : pigment settles into the paper tooth -> speckled texture
  - blooms      : back-runs, pale cauliflower patches with dark rims
  - soft edges  : wet-in-wet feathering (mask blurred and noise-thresholded)
  - lifting     : dabbing paint off to recover light (veins, highlights)

    from watercolor import Watercolor, hexc
    p = Watercolor(1920, 1080, seed=1)
    p.paper()
    p.gradient_wash(0, 600, top=hexc('#9cb8d4'), bottom=hexc('#f4d3b4'))
    p.glaze(p.shape(blob_pts(...), soft=3), hexc('#6f9a5b'), 0.8)
    p.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, curve, spline, noise2d, smoothstep, polygon_mask, blob_pts, bristle_stroke, cjk_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


class Watercolor:
    def __init__(self, W=1920, H=1080, seed=0, paper_tone='#fbf8f1'):
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

    def noise(self, scale, octaves=4, seed=None):
        return noise2d(self.H, self.W, scale, octaves, seed if seed is not None else self._seed())

    # ------------------------------------------------------------ paper
    def paper(self):
        """cold-press paper: tooth (height) texture with soft raking light"""
        t = 0.55 * self.noise(2.5, 2) + 0.3 * self.noise(10, 3) + 0.15 * self.noise(60, 3)
        self.tooth = t
        shade = np.gradient(blur(t, 1.0), axis=1) + np.gradient(blur(t, 1.0), axis=0)
        self.base = self.base * (1 - 0.3 * shade[..., None]) * (0.99 + 0.02 * self.noise(300, 3))[..., None]
        self.img = self.base.copy()

    # ------------------------------------------------------------ masks
    def shape(self, pts, soft=2.0, ragged=0.18, seed=None):
        """closed outline -> soft, slightly ragged mask (0..1). soft ~1-4 crisp wet edge; 15-40 wet-in-wet feather"""
        m = polygon_mask(self.H, self.W, pts, ss=2)
        if soft > 0:
            m = blur(m, soft)
            n = self.noise(max(6, soft * 3), 3, seed)
            m = smoothstep(0.5 - 0.25, 0.5 + 0.25, m + (n - 0.5) * ragged)
        return m

    def band(self, pts, width, soft=2.0):
        """a thick soft stroke (stems, reeds, rivers) as a mask"""
        im = Image.new('L', (self.W, self.H), 0)
        ImageDraw.Draw(im).line([tuple(map(float, p)) for p in pts], fill=255, width=int(width), joint='curve')
        return blur(np.asarray(im, np.float32) / 255, soft)

    # ------------------------------------------------------------ paint
    def glaze(self, mask, colour, strength=0.8, edge=0.6, gran=0.35, bloom=0, variation=0.25, seed=None):
        """transparent wash of `colour` over `mask`. edge: wet-edge darkening; gran: granulation;
        bloom: number of back-run blooms; variation: patchy pigment density."""
        seed = seed if seed is not None else self._seed()
        d = mask * (1 - variation + variation * noise2d(self.H, self.W, 90, 4, seed))
        ring = np.clip(mask - blur(mask, 5), 0, None)
        d = d + edge * 2.2 * ring * (mask > 0.2)
        d = d * (1 + gran * (self.tooth - 0.5) * 2.2)
        for _ in range(bloom):
            ys, xs = np.nonzero(mask > 0.6)
            if len(xs) == 0: break
            k = int(self.rng.integers(len(xs))); cx, cy = xs[k], ys[k]
            r0 = self.rng.uniform(25, 70)
            dist = np.hypot(self.XX - cx, self.YY - cy) / (r0 * (0.8 + 0.4 * noise2d(self.H, self.W, 20, 3, seed + 7)))
            inner = np.clip(1 - dist, 0, 1)
            rim = np.exp(-((dist - 1) / 0.08) ** 2)
            d = d * (1 - 0.55 * inner * mask) + 0.35 * rim * mask
        d = np.clip(d * strength, 0, 1.3)
        self.img *= (1 - d[..., None] * (1 - colour))

    def gradient_wash(self, y0, y1, top, bottom, strength=0.7, soft_bottom=60, gran=0.2):
        """wet-in-wet sky: two colours blending vertically between y0 and y1"""
        t = np.clip((self.YY - y0) / max(1, (y1 - y0)), 0, 1)
        t = np.clip(t + (self.noise(260, 4) - 0.5) * 0.25, 0, 1)
        mask = np.clip((y1 + soft_bottom - self.YY) / (2 * soft_bottom), 0, 1)
        col = top[None, None, :] * (1 - t[..., None]) + bottom[None, None, :] * t[..., None]
        d = mask * strength * (0.85 + 0.15 * self.noise(120, 3)) * (1 + gran * (self.tooth - 0.5) * 2)
        self.img *= (1 - d[..., None] * (1 - col))

    def stroke(self, pts, width, colour, strength=0.8, dry=0.3, taper=(0.2, 0.4), jitter=0.4):
        """bristle brush stroke in colour (dry-brush texture comes from `dry` + paper tooth)"""
        buf = np.zeros((self.H, self.W), np.float32)
        bristle_stroke(buf, pts, width, 1.0, dry, taper, jitter, self._seed())
        d = np.clip(buf * strength * (1 + 0.5 * (self.tooth - 0.5)), 0, 1)
        self.img *= (1 - d[..., None] * (1 - colour))

    def line(self, pts, width=1.4, colour=hexc('#5b4a3f'), strength=0.55):
        """fine pen/pencil line for line-and-wash definition"""
        self.stroke(pts, width, colour, strength, dry=0.15, taper=(0.1, 0.2), jitter=0.2)

    def lift(self, mask, amount=0.6):
        """lift paint back toward the paper (highlights, leaf veins)"""
        a = np.clip(mask * amount, 0, 1)[..., None]
        self.img = self.img + (self.base - self.img) * a

    def splatter(self, colour, n=40, box=None, size=(1.5, 5), strength=0.7):
        """flicked droplets"""
        x0, y0, x1, y1 = box or (0, 0, self.W, self.H)
        for _ in range(n):
            x, y = self.rng.uniform(x0, x1), self.rng.uniform(y0, y1)
            r = self.rng.uniform(*size)
            m = np.clip((r - np.hypot(self.XX - x, self.YY - y)) / 1.2, 0, 1)
            self.img *= (1 - (m * strength)[..., None] * (1 - colour))

    # ------------------------------------------------------------ helpers for common subjects
    @staticmethod
    def petal_pts(x, y, angle, length, width, n=40, curl=0.0):
        """a pointed petal/leaf outline from base (x, y) pointing at `angle` (radians)"""
        t = np.linspace(0, 1, n)
        half = width * np.sin(np.pi * t) ** 0.8 * (1 - 0.35 * t)
        ax = t * length
        off = curl * length * (t ** 2)
        left = np.stack([ax, half + off], 1); right = np.stack([ax, -half + off], 1)[::-1]
        P = np.vstack([left, right])
        c, s = np.cos(angle), np.sin(angle)
        return np.stack([x + P[:, 0] * c - P[:, 1] * s, y + P[:, 0] * s + P[:, 1] * c], 1)

    # ------------------------------------------------------------ text / output
    def title_vertical(self, text, x, y, size=84, gap=1.17, color=(70, 60, 55)):
        self.texts.append(('vtext', (text, x, y, size, gap, color)))

    def seal(self, text, x, y, size=36, color=(186, 58, 46)):
        self.texts.append(('seal', (text, x, y, size, color)))

    def composite(self):
        out = Image.fromarray((np.clip(self.img, 0, 1) * 255).astype(np.uint8))
        font_path = cjk_font()
        if self.texts and font_path:
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
                    dr.rectangle((x, y, x + size * 1.4, y + size * 1.25 * len(text) + size * 0.3), fill=color)
                    for i, ch in enumerate(text):
                        dr.text((x + size * 0.2, y + size * 0.2 + i * size * 1.25), ch, font=f, fill=(250, 244, 232))
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
