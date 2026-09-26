"""ukiyoe — Japanese woodblock print (numpy + Pillow only).

The look: every colour is its own carved block, printed flat onto washi with the wood grain showing
through, slightly uneven pressure and a little registration drift; skies and seas use *bokashi*
(a graded wipe of the block: strong at one edge, fading out); a black key block of confident outlines
sits on top; a title cartouche and a red seal finish the print.

    from ukiyoe import Ukiyoe
    u = Ukiyoe(1920, 1080, seed=1)
    u.bokashi(u.rect(0, 0, 1920, 600), '#2b4f8a', 0, 320)       # sky: blue at the top fading down
    u.block(u.poly(fuji), '#3d5a80')
    u.key(fuji_outline)
    u.cartouche(1640, 60, 110, 330, '富士曙')
    u.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts, cjk_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class Ukiyoe:
    def __init__(self, W=1920, H=1080, seed=0, washi='#efe2c4'):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        p = np.ones((H, W, 3), np.float32) * _c(washi)
        p *= (0.97 + 0.05 * noise2d(H, W, 220, 4, 1))[..., None]                 # age / foxing
        fib = Image.new('L', (W, H), 0); d = ImageDraw.Draw(fib)
        for _ in range(2200):
            x, y = self.rng.uniform(0, W), self.rng.uniform(0, H); a = self.rng.uniform(0, np.pi); L = self.rng.uniform(6, 30)
            d.line([(x, y), (x + np.cos(a) * L, y + np.sin(a) * L)], fill=int(self.rng.uniform(8, 20)), width=1)
        p *= (1 - 0.3 * blur(np.asarray(fib, np.float32) / 255, 0.5))[..., None]
        self.img = p
        self.offsets = {}
        self.texts = []
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ shapes
    def poly(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=2)

    def rect(self, x0, y0, x1, y1):
        return ((self.XX >= x0) & (self.XX < x1) & (self.YY >= y0) & (self.YY < y1)).astype(np.float32)

    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    # ------------------------------------------------------------ printing
    def _register(self, m, key):
        if key not in self.offsets:
            self.offsets[key] = (int(self.rng.integers(-2, 3)), int(self.rng.integers(-2, 3)))
        dx, dy = self.offsets[key]
        out = np.zeros_like(m)
        out[max(dy, 0):self.H + min(dy, 0), max(dx, 0):self.W + min(dx, 0)] = m[max(-dy, 0):self.H + min(-dy, 0), max(-dx, 0):self.W + min(-dx, 0)]
        return out

    def _wood(self, seed):
        """wood grain: noise stretched along x, plus a little pressure unevenness"""
        g = noise2d(max(2, self.H), max(2, self.W // 12), 3, 2, seed)
        g = np.asarray(Image.fromarray(g.astype(np.float32)).resize((self.W, self.H), Image.BILINEAR))
        return 0.88 + 0.12 * g + 0.06 * (noise2d(self.H, self.W, 160, 3, seed + 1) - 0.5)

    def block(self, mask, colour, strength=0.95, key=None):
        """print one flat colour block (opaque-ish pigment in water, shows wood grain)"""
        col = _c(colour)
        m = self._register(mask, key or (colour if isinstance(colour, str) else tuple(colour)))
        a = np.clip(m * strength * self._wood(self._seed()), 0, 1)[..., None]
        self.img = self.img * (1 - a) + col * a

    def bokashi(self, mask, colour, y_strong, y_fade, strength=0.95, key=None):
        """graded wipe: full colour at y_strong fading to nothing at y_fade (either direction)"""
        t = np.clip((self.YY - y_strong) / (y_fade - y_strong), 0, 1)
        grade = (1 - t) ** 1.4
        self.block(mask * grade, colour, strength, key)

    def key(self, pts, width=4, colour='#2a2320', closed=False):
        """black key-block outline: crisp but slightly varying, printed on top"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        n = len(P)
        wv = width * (0.85 + 0.3 * (fbm1d(n, max(3, n / 5), 2, self._seed()) + 1) / 2)
        im = Image.new('L', (self.W * 2, self.H * 2), 0); d = ImageDraw.Draw(im)
        for i in range(n - 1):
            d.line([(P[i, 0] * 2, P[i, 1] * 2), (P[i + 1, 0] * 2, P[i + 1, 1] * 2)], fill=255, width=max(1, int(wv[i] * 2)))
            r = wv[i]
            d.ellipse((P[i + 1, 0] * 2 - r, P[i + 1, 1] * 2 - r, P[i + 1, 0] * 2 + r, P[i + 1, 1] * 2 + r), fill=255)
        m = np.asarray(im.resize((self.W, self.H), Image.LANCZOS), np.float32) / 255
        self.block(m, colour, 0.97, key='__key__')

    # ------------------------------------------------------------ motifs
    def cloud_band(self, x0, x1, y, h, colour='#f4ebd5', outline=True, glow=None):
        """long stylised mist/cloud band with scalloped ends (Hiroshige style)"""
        top = [(x, y - h / 2 + 4 * np.sin(x / 37)) for x in np.linspace(x0 + h / 2, x1 - h / 2, 30)]
        right = [(x1 - h / 2 + np.cos(t) * h / 2, y + np.sin(t) * h / 2) for t in np.linspace(-np.pi / 2, np.pi / 2, 10)]
        bot = [(x, y + h / 2 + 4 * np.sin(x / 41)) for x in np.linspace(x1 - h / 2, x0 + h / 2, 30)]
        left = [(x0 + h / 2 + np.cos(t) * h / 2, y + np.sin(t) * h / 2) for t in np.linspace(np.pi / 2, 3 * np.pi / 2, 10)]
        pts = top + right + bot + left
        m = self.poly(pts)
        self.block(m, colour, 1.15)                                   # opaque: clouds cover what is behind
        if glow: self.bokashi(m, glow, y + h / 2, y - h * 0.1, 0.55)  # warm light on the underside
        if outline: self.key(pts, 2.4, closed=True)

    def seigaiha(self, mask, colour, r=34, width=2.2):
        """overlapping-wave pattern (rows of concentric half-circles, lower rows cover upper ones)"""
        ys = np.nonzero(mask.max(1) > 0)[0]
        if len(ys) == 0: return
        m = np.zeros((self.H, self.W), np.float32)
        for row, cy in enumerate(np.arange(ys.min() - r, ys.max() + r, r * 0.5)):
            off = (row % 2) * r
            dx = np.mod(self.XX - off + r, 2 * r) - r
            d = np.hypot(dx, self.YY - cy)
            disk = (d < r) & (self.YY <= cy)
            m[disk] = 0                                   # this row covers the arcs of the row above
            for k in (1.0, 0.72, 0.44):
                ring = np.clip(width / 2 - np.abs(d - r * k) + 0.5, 0, 1) * disk
                m = np.maximum(m, ring)
        self.block(m * mask, colour, 0.9)

    def cartouche(self, x, y, w, h, text, colour='#f6e7c3', text_colour='#2a2320'):
        """title cartouche: pale box, key-block outline, vertical title"""
        self.block(self.rect(x, y, x + w, y + h), colour, 0.97, key='__cartouche__')
        self.key([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], 3, closed=True)
        self.texts.append(('v', text, x + w * 0.16, y + w * 0.16, w * 0.68, text_colour))

    def seal(self, x, y, size, text, colour='#b8372d'):
        self.block(self.rect(x, y, x + size, y + size * 1.3), colour, 0.95, key='__seal__')
        self.texts.append(('v', text, x + size * 0.18, y + size * 0.12, size * 0.62, '#f6e7c3'))

    # ------------------------------------------------------------ output
    def composite(self):
        out = Image.fromarray((np.clip(self.img, 0, 1) * 255).astype(np.uint8))
        fp = cjk_font()
        if self.texts and fp:
            dr = ImageDraw.Draw(out)
            for kind, s, x, y, size, col in self.texts:
                f = ImageFont.truetype(fp, int(size), index=0)
                for i, ch in enumerate(s):
                    dr.text((x, y + i * size * 1.12), ch, font=f, fill=tuple(int(v * 255) for v in _c(col)))
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
