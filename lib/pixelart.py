"""pixelart — retro pixel art at low resolution, upscaled crisply (numpy + Pillow only).

The look: a small canvas (e.g. 320x180) painted pixel by pixel with a limited palette; gradients and
glows use *ordered (Bayer) dithering* instead of smooth blends; hard 1-px outlines; tiny bitmap text;
then a nearest-neighbour upscale (x6 -> 1920x1080) so every pixel stays a sharp square.

    from pixelart import PixelArt
    p = PixelArt(320, 180, scale=6, seed=1)
    p.gradient(0, 0, 320, 120, '#141a33', '#2b2f5c')
    p.rect(40, 60, 150, 140, '#6b3b3b')
    p.glow(250, 80, 30, '#ffcf6b', 0.8)
    p.text('CAFE', 70, 50, '#ff5fa2')
    p.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], np.float32) / 16 + 1 / 32

FONT = {  # 3x5 bitmap glyphs
    'A': ['010', '101', '111', '101', '101'], 'B': ['110', '101', '110', '101', '110'], 'C': ['011', '100', '100', '100', '011'],
    'D': ['110', '101', '101', '101', '110'], 'E': ['111', '100', '110', '100', '111'], 'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'], 'H': ['101', '101', '111', '101', '101'], 'I': ['111', '010', '010', '010', '111'],
    'K': ['101', '101', '110', '101', '101'], 'L': ['100', '100', '100', '100', '111'], 'M': ['101', '111', '111', '101', '101'],
    'N': ['110', '101', '101', '101', '101'], 'O': ['010', '101', '101', '101', '010'], 'P': ['110', '101', '110', '100', '100'],
    'R': ['110', '101', '110', '101', '101'], 'S': ['011', '100', '010', '001', '110'], 'T': ['111', '010', '010', '010', '010'],
    'U': ['101', '101', '101', '101', '011'], 'Y': ['101', '101', '010', '010', '010'], ' ': ['000'] * 5,
    '0': ['111', '101', '101', '101', '111'], '1': ['010', '110', '010', '010', '111'], '2': ['110', '001', '010', '100', '111'],
    '4': ['101', '101', '111', '001', '001'], '7': ['111', '001', '010', '010', '010'], '&': ['010', '101', '010', '101', '011'],
}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class PixelArt:
    def __init__(self, w=320, h=180, scale=6, seed=0, bg='#000000'):
        self.w, self.h, self.scale = w, h, scale
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:h, 0:w]
        self.buf = np.ones((h, w, 3), np.float32) * _c(bg)
        self.bayer = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
        self.stages = []

    # ------------------------------------------------------------ primitives (integer pixels)
    def put(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h: self.buf[int(y), int(x)] = _c(colour)

    def rect(self, x0, y0, x1, y1, colour):
        self.buf[max(0, int(y0)):min(self.h, int(y1)), max(0, int(x0)):min(self.w, int(x1))] = _c(colour)

    def mask_poly(self, pts):
        im = Image.new('L', (self.w, self.h), 0)
        ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in pts], fill=1)
        return np.asarray(im, bool)

    def poly(self, pts, colour):
        self.buf[self.mask_poly(pts)] = _c(colour)

    def circle(self, cx, cy, r, colour):
        self.buf[(self.XX - cx) ** 2 + (self.YY - cy) ** 2 <= r * r] = _c(colour)

    def line(self, x0, y0, x1, y1, colour):
        """Bresenham line"""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0); sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.put(x0, y0, colour)
            if x0 == x1 and y0 == y1: break
            e2 = 2 * err
            if e2 >= dy: err += dy; x0 += sx
            if e2 <= dx: err += dx; y0 += sy

    def outline(self, mask, colour):
        m = mask.astype(bool)
        edge = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
        self.buf[edge] = _c(colour)

    # ------------------------------------------------------------ dithering
    def dither(self, mask, colour, alpha):
        """ordered dither: paint `colour` where alpha beats the Bayer threshold (glows, fades, reflections)"""
        on = mask.astype(bool) & (np.broadcast_to(alpha, (self.h, self.w)) > self.bayer)
        self.buf[on] = _c(colour)

    def gradient(self, x0, y0, x1, y1, c0, c1, steps=None):
        """vertical gradient between two colours, banded through a small ramp and dithered between bands"""
        m = np.zeros((self.h, self.w), bool); m[int(y0):int(y1), int(x0):int(x1)] = True
        t = np.clip((self.YY - y0) / max(1, (y1 - y0)), 0, 1)
        steps = steps or 5
        ramp = [_c(c0) * (1 - k / (steps - 1)) + _c(c1) * (k / (steps - 1)) for k in range(steps)]
        f = t * (steps - 1); lo = np.floor(f).astype(int); frac = f - lo
        for k in range(steps):
            sel = m & (lo == k)
            self.buf[sel] = ramp[k]
            if k + 1 < steps:
                self.buf[sel & (frac > self.bayer)] = ramp[k + 1]

    def glow(self, cx, cy, r, colour, strength=0.8, mask=None, squash=1.0):
        d = np.hypot(self.XX - cx, (self.YY - cy) / squash) / r
        a = np.clip(1 - d, 0, 1) ** 1.6 * strength
        self.dither(np.ones((self.h, self.w), bool) if mask is None else mask, colour, a)

    def text(self, s, x, y, colour, size=1, spacing=1):
        cx = x
        for ch in s.upper():
            g = FONT.get(ch, FONT[' '])
            for r, row in enumerate(g):
                for c, bit in enumerate(row):
                    if bit == '1':
                        self.rect(cx + c * size, y + r * size, cx + (c + 1) * size, y + (r + 1) * size, colour)
            cx += (3 + spacing) * size

    def rain(self, n=220, colour='#8fa4c8', length=(4, 8), slant=1, box=None):
        x0, y0, x1, y1 = box or (0, 0, self.w, self.h)
        for _ in range(n):
            x, y = int(self.rng.uniform(x0, x1)), int(self.rng.uniform(y0, y1))
            L = int(self.rng.integers(*length))
            for k in range(L):
                if (k + x) % 2 == 0 or k < L - 1:
                    self.put(x - (k * slant) // 3, y + k, colour)

    # ------------------------------------------------------------ output
    def composite(self):
        im = Image.fromarray((np.clip(self.buf, 0, 1) * 255).astype(np.uint8))
        return im.resize((self.w * self.scale, self.h * self.scale), Image.NEAREST)

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
