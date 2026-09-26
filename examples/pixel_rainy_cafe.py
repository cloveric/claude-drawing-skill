"""Example (pixel art): Rainy Night Cafe / 雨夜咖啡店 — a 320x180 scene painted pixel by pixel with a
limited palette, dithered sky and glows, neon sign in a 3x5 bitmap font, wet-street reflections,
rain, a passer-by with an umbrella and a cat; upscaled x6 with nearest-neighbour. No image model.
python3 pixel_rainy_cafe.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from pixelart import PixelArt

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'pixel_rainy_cafe.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

p = PixelArt(320, 180, scale=6, seed=2084)
rng = p.rng
W, H = p.w, p.h

# ---- sky and skyline
p.gradient(0, 0, W, 138, '#0d1030', '#2c2a5c', steps=6)
x = 0
while x < W:                                                      # far skyline with lit windows
    bw = int(rng.integers(14, 30)); bh = int(rng.integers(30, 75))
    p.rect(x, 118 - bh, x + bw, 138, '#1a1d40')
    for wy in range(118 - bh + 4, 134, 5):
        for wx in range(x + 3, x + bw - 3, 4):
            if rng.random() < 0.28:
                p.rect(wx, wy, wx + 2, wy + 2, '#f2c14e' if rng.random() < 0.8 else '#6fd3e8')
    x += bw + int(rng.integers(0, 3))
p.rect(170, 40, 230, 138, '#23264c')                              # a closer building behind the lamp
for wy in range(48, 130, 9):
    for wx in (178, 192, 206, 218):
        p.rect(wx, wy, wx + 6, wy + 5, '#f2b24a' if rng.random() < 0.35 else '#171a38')
p.stage('skyline')

# ---- the cafe: brick facade, upper windows, striped awning, glowing shop window, door, neon sign
p.rect(30, 58, 162, 138, '#6e3a3a')
for yy in range(60, 138, 4):                                      # brick courses
    p.rect(30, yy, 162, yy + 1, '#552c2c')
    off = 0 if (yy // 4) % 2 == 0 else 4
    for xx in range(30 + off, 162, 8):
        p.rect(xx, yy, xx + 1, yy + 4, '#552c2c')
p.rect(28, 56, 164, 60, '#3a1f25')                                # cornice
for (wx, lit) in [(44, False), (78, True), (112, False), (140, False)]:
    p.rect(wx - 1, 63, wx + 15, 79, '#2a1a1e')
    p.rect(wx, 64, wx + 14, 78, '#ffd27a' if lit else '#1b2244')
    p.rect(wx + 6, 64, wx + 8, 78, '#2a1a1e'); p.rect(wx, 70, wx + 14, 72, '#2a1a1e')
for k, xx in enumerate(range(34, 158, 6)):                        # awning stripes with a scalloped edge
    p.rect(xx, 90, xx + 6, 99, '#d64b4b' if k % 2 == 0 else '#f1e3c6')
    p.rect(xx + 1, 99, xx + 5, 101, '#d64b4b' if k % 2 == 0 else '#f1e3c6')
p.rect(34, 89, 158, 90, '#8a2a2a')
p.rect(42, 103, 112, 136, '#2a1a1e')                              # shop window frame
p.gradient(44, 105, 110, 134, '#ffdc8a', '#e79a45', steps=4)
p.rect(44, 118, 110, 119, '#9a5a2a'); p.rect(44, 127, 110, 128, '#9a5a2a')          # shelves
for sx in range(48, 106, 7):
    p.rect(sx, 113 + (sx % 3), sx + 3, 118, '#b0662e')           # jars and cups
    p.rect(sx + 1, 123, sx + 4, 127, '#8e4f28')
p.rect(58, 105, 59, 110, '#5a3a22'); p.rect(55, 110, 62, 112, '#fff1b8')            # hanging lamp
p.rect(116, 103, 142, 138, '#2a1a1e'); p.rect(118, 105, 140, 138, '#6b4326')        # door
p.rect(122, 108, 136, 118, '#ffd27a'); p.put(137, 122, '#e8c35a')
p.glow(96, 83, 22, '#ff5fa2', 0.42, squash=0.45)                 # neon glow, then the tube letters
p.text('CAFE', 81, 78, '#ffd1e6', size=2)
p.stage('cafe')

# ---- street lamp with a pool of light
p.rect(248, 62, 251, 146, '#2b2d3f'); p.rect(244, 58, 256, 62, '#2b2d3f'); p.rect(246, 62, 254, 65, '#ffe7a1')
p.glow(250, 64, 20, '#ffe7a1', 0.5)
p.glow(250, 146, 30, '#d9c27a', 0.45, squash=0.2)

# ---- sidewalk and wet street with broken reflections
p.rect(0, 138, W, 146, '#2a2c46'); p.rect(0, 146, W, 148, '#3c3f63')
p.gradient(0, 148, W, H, '#161831', '#0c0d1f', steps=3)
for (x0, x1, col, a0) in [(44, 110, '#e8a44f', 0.75), (78, 92, '#ffd27a', 0.45), (80, 112, '#ff5fa2', 0.35), (242, 258, '#ffe7a1', 0.8), (178, 226, '#f2b24a', 0.25)]:
    m = np.zeros((H, W), bool); m[150:H, x0:x1] = True
    ripple = ((p.YY % 3) != 0)                                    # horizontal ripple gaps
    fade = np.clip(1 - (p.YY - 150) / 34, 0, 1) * a0
    p.dither(m & ripple, col, fade)
p.stage('street')

# ---- a passer-by with an umbrella, and a cat on the step
UX, UY = 206, 118
dome = ((p.XX - UX) ** 2 + (p.YY - (UY + 8)) ** 2 <= 121) & (p.YY <= UY + 8)       # half-disc umbrella
p.buf[dome] = np.array([62, 193, 201], np.float32) / 255
p.outline(dome, '#2a8a91')
for k in range(-10, 11, 5):
    p.put(UX + k, UY + 8, '#2a8a91')
p.rect(UX, UY + 8, UX + 1, UY + 16, '#1b1c2e')                   # handle
p.rect(UX - 3, UY + 14, UX + 4, UY + 25, '#23243a'); p.rect(UX - 3, UY + 14, UX + 4, UY + 16, '#c9a07a')
p.rect(UX - 2, UY + 25, UX, UY + 31, '#1b1c2e'); p.rect(UX + 2, UY + 25, UX + 4, UY + 30, '#1b1c2e')
p.rect(126, 133, 134, 138, '#e08a3c'); p.rect(127, 130, 131, 134, '#e08a3c')        # cat
p.put(127, 129, '#e08a3c'); p.put(130, 129, '#e08a3c'); p.put(128, 131, '#1b1c2e'); p.put(130, 131, '#1b1c2e')
p.rect(134, 132, 136, 134, '#e08a3c'); p.rect(135, 130, 136, 132, '#e08a3c')

# ---- rain and ripples
p.rain(260, '#8fa4c8', (4, 8), slant=1)
for _ in range(14):
    rx, ry = int(rng.integers(5, W - 5)), int(rng.integers(152, H - 3))
    p.put(rx - 1, ry, '#5c6a93'); p.put(rx + 1, ry, '#5c6a93'); p.put(rx, ry - 1, '#5c6a93')
p.save(out, stages_dir=stages)
print('saved', out)
