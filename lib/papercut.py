"""papercut — torn-paper collage with crayon texture (numpy + Pillow only).

Each `piece` is a sheet of paper cut or torn to a shape and glued on:
  - torn edges : the outline is broken up by fine + medium noise
  - white rim  : where paper tears, its pale core shows as a fibrous light edge
  - shadow     : every piece casts a small soft shadow onto what is below (paper depth)
  - texture    : plain coloured paper / kraft / crayon (waxy grain) / newsprint / ruled notebook
Plus crayon strokes (waxy lines with paper showing through), stars, and simple cute faces.

    from papercut import Collage, hexc
    c = Collage(1920, 1080, seed=1)
    c.background('#1f2a5c', texture='crayon')
    c.piece(pts, '#f6d77a', texture='crayon')
    c.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts, bristle_stroke, cjk_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


PAPER_WHITE = hexc('#f7f1e4')


class Collage:
    def __init__(self, W=1920, H=1080, seed=0):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.img = np.ones((H, W, 3), np.float32) * PAPER_WHITE
        self.texts = []
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def noise(self, scale, octaves=3, seed=None):
        return noise2d(self.H, self.W, scale, octaves, seed if seed is not None else self._seed())

    # ------------------------------------------------------------ textures
    def _crayon_grain(self, angle=0.6, density=0.62):
        """waxy directional grain: 1 where wax sits on the tooth, 0 where paper shows"""
        n = self.noise(1.6, 2)
        k = 7
        dx, dy = np.cos(angle), np.sin(angle)
        acc = np.zeros_like(n)
        for i in range(-k, k + 1):                    # smear along the stroke direction
            acc += np.roll(np.roll(n, int(round(i * dy)), 0), int(round(i * dx)), 1)
        acc /= (2 * k + 1)
        acc = (acc - acc.mean()) / (acc.std() + 1e-6)
        return smoothstep(-1.2 + 2.4 * (1 - density) - 0.6, -1.2 + 2.4 * (1 - density) + 0.6, acc)

    def _texture(self, colour, texture, angle=0.6):
        H, W = self.H, self.W
        base = np.ones((H, W, 3), np.float32) * colour
        mott = (0.95 + 0.08 * self.noise(50, 3))[..., None]
        if texture == 'paper':
            return base * mott
        if texture == 'kraft':
            fib = self.noise(2.5, 2)
            return base * mott * (0.94 + 0.1 * fib)[..., None]
        if texture == 'crayon':
            # waxy coverage: gaps show a lighter tint of the same colour (not bare white) -> subtle, not scratchy
            g = self._crayon_grain(angle, density=0.8)[..., None]
            under = base * 0.6 + PAPER_WHITE * 0.4
            return (base * mott) * g + under * (1 - g)
        if texture == 'newsprint':
            paper = np.ones((H, W, 3), np.float32) * hexc('#ebe6da') * mott
            im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
            y = 0
            while y < H:
                x = int(self.rng.integers(0, 14))
                while x < W:
                    wl = int(self.rng.integers(8, 46))
                    d.rectangle((x, y, x + wl, y + 4), fill=int(self.rng.integers(120, 200)))
                    x += wl + int(self.rng.integers(5, 9))
                y += 11 if self.rng.random() > 0.05 else 26
            ink = blur(np.asarray(im, np.float32) / 255, 0.6)[..., None]
            return paper * (1 - 0.6 * ink)
        if texture == 'notebook':
            paper = np.ones((H, W, 3), np.float32) * hexc('#fbf8ef') * mott
            lines = ((self.YY % 36) < 2).astype(np.float32) * 0.55
            paper = paper * (1 - lines[..., None] * (1 - hexc('#7fa3d8')))
            return paper
        raise ValueError(texture)

    # ------------------------------------------------------------ pieces
    def background(self, colour, texture='crayon', angle=0.5):
        self.img = self._texture(hexc(colour) if isinstance(colour, str) else colour, texture, angle)

    def mask_from(self, pts=None, mask=None):
        return mask if mask is not None else polygon_mask(self.H, self.W, pts, ss=2)

    def piece(self, pts=None, colour='#e07a5f', texture='paper', mask=None, torn=0.6, rim=0.8, shadow=0.35,
              angle=0.6, cut_side=None):
        """glue a sheet of paper: outline `pts` (or `mask`), colour, texture.
        torn: 0 clean scissor cut .. 1 very ragged; rim: white torn edge strength; shadow: depth shadow strength."""
        col = hexc(colour) if isinstance(colour, str) else colour
        m0 = self.mask_from(pts, mask)
        if torn > 0:
            s1 = self._seed()
            jag = (noise2d(self.H, self.W, 3, 2, s1) - 0.5) * 0.9 + (noise2d(self.H, self.W, 14, 3, s1 + 1) - 0.5) * 0.9
            soft = blur(m0, 2.5)
            m = smoothstep(0.47, 0.53, soft + jag * 0.35 * torn)
            wide = blur(m0, 6.0)                                  # the torn white core reaches ~5-8 px beyond the colour
            outer = smoothstep(0.17, 0.23, wide + jag * 0.22 * torn)
            gate = smoothstep(0.35, 0.6, noise2d(self.H, self.W, 60, 2, s1 + 2))   # tears only along parts of the edge
            rim_m = np.clip(outer - m, 0, 1) * gate * rim
            m_all = np.maximum(m, rim_m)
        else:
            m = smoothstep(0.4, 0.6, blur(m0, 0.8)); rim_m = np.zeros_like(m); m_all = m
        if shadow > 0:
            shifted = np.zeros_like(m_all); shifted[7:, 5:] = m_all[:-7, :-5]       # no wrap-around
            sh = blur(shifted, 6)
            self.img *= (1 - shadow * sh * (1 - m_all))[..., None]
        fill = self._texture(col, texture, angle)
        self.img = self.img * (1 - m[..., None]) + fill * m[..., None]
        self.img = self.img * (1 - rim_m[..., None]) + (PAPER_WHITE * (0.97 + 0.05 * self.noise(3, 1)[..., None])) * rim_m[..., None]
        return m

    def circle_mask(self, cx, cy, r):
        return np.clip((r - np.hypot(self.XX - cx, self.YY - cy)) + 0.5, 0, 1)

    def cloud_mask(self, cx, cy, w, h, puffs=5, seed=None):
        rng = np.random.default_rng(seed if seed is not None else self._seed())
        m = np.zeros((self.H, self.W), np.float32)
        for i in range(puffs):
            x = cx - w / 2 + w * (i + 0.5) / puffs + rng.normal(0, w * 0.03)
            r = h * (0.45 + 0.4 * np.sin(np.pi * (i + 0.5) / puffs)) * rng.uniform(0.85, 1.1)
            m = np.maximum(m, self.circle_mask(x, cy + h * 0.25 - r * 0.6, r))
        m = np.maximum(m, polygon_mask(self.H, self.W, [(cx - w / 2, cy + h * 0.25), (cx + w / 2, cy + h * 0.25), (cx + w / 2 - 10, cy + h * 0.45), (cx - w / 2 + 10, cy + h * 0.45)]))
        return m

    @staticmethod
    def star_pts(cx, cy, r, points=5, inner=0.45, rot=-np.pi / 2):
        t = np.linspace(0, 2 * np.pi, points * 2, endpoint=False) + rot
        rr = np.where(np.arange(points * 2) % 2 == 0, r, r * inner)
        return np.stack([cx + np.cos(t) * rr, cy + np.sin(t) * rr], 1)

    # ------------------------------------------------------------ crayon marks
    def crayon(self, pts, width, colour, strength=0.9, angle=None):
        """waxy crayon line: paper tooth breaks it up"""
        col = hexc(colour) if isinstance(colour, str) else colour
        buf = np.zeros((self.H, self.W), np.float32)
        bristle_stroke(buf, pts, width, 1.0, 0.15, (0.1, 0.15), 0.3, self._seed())
        P = np.asarray(pts, np.float32)
        ang = angle if angle is not None else float(np.arctan2(P[-1, 1] - P[0, 1], P[-1, 0] - P[0, 0]))
        g = self._crayon_grain(ang, density=0.7)
        a = np.clip(buf * 1.4, 0, 1) * g * strength
        self.img = self.img * (1 - a[..., None]) + col * a[..., None]

    def dot(self, x, y, r, colour, soft=0.8):
        col = hexc(colour) if isinstance(colour, str) else colour
        a = np.clip((r - np.hypot(self.XX - x, self.YY - y)) / soft, 0, 1)
        self.img = self.img * (1 - a[..., None]) + col * a[..., None]

    def glow(self, x, y, r, colour, strength=0.35):
        col = hexc(colour) if isinstance(colour, str) else colour
        a = strength * np.exp(-((self.XX - x) ** 2 + (self.YY - y) ** 2) / (2 * r * r))
        self.img = self.img * (1 - a[..., None]) + col * a[..., None]

    def face(self, cx, cy, r, mood='smile', ink='#2b2430', blush='#f09aa0'):
        """cute face: closed happy eyes (^ ^) or dot eyes, small smile, blush cheeks"""
        e = r * 0.34; ey = cy - r * 0.05
        lw = max(2.0, r * 0.035)
        if mood in ('smile', 'sleep'):
            for sx in (-1, 1):
                x0 = cx + sx * e
                self.crayon(spline([(x0 - r * 0.11, ey), (x0, ey - r * 0.08 * (1 if mood == 'smile' else -1)), (x0 + r * 0.11, ey)], 6), lw, ink, 1.0)
        else:
            for sx in (-1, 1):
                self.dot(cx + sx * e, ey, max(3, r * 0.07), ink)
        self.crayon(spline([(cx - r * 0.1, cy + r * 0.22), (cx, cy + r * 0.29), (cx + r * 0.1, cy + r * 0.22)], 6), lw, ink, 1.0)
        for sx in (-1, 1):
            self.glow(cx + sx * r * 0.52, cy + r * 0.2, r * 0.1, blush, 0.8)

    # ------------------------------------------------------------ text / output
    def text(self, s, x, y, size=48, colour='#3a5fa8', vertical=False):
        self.texts.append((s, x, y, size, colour, vertical))

    def composite(self):
        out = Image.fromarray((np.clip(self.img, 0, 1) * 255).astype(np.uint8))
        fp = cjk_font()
        if self.texts and fp:
            dr = ImageDraw.Draw(out)
            for s, x, y, size, colour, vertical in self.texts:
                f = ImageFont.truetype(fp, size, index=0)
                c = tuple(int(v * 255) for v in hexc(colour))
                if vertical:
                    for i, ch in enumerate(s): dr.text((x, y + i * size * 1.15), ch, font=f, fill=c)
                else:
                    dr.text((x, y), s, font=f, fill=c)
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
