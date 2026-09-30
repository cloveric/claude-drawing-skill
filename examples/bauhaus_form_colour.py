"""Example (Bauhaus geometric poster): 形与色 · Form & Colour — a screen-printed poster for a (fictional) foundation-
course lecture. It diagrams one small idea: the sharper a shape's corners, the brighter its colour. Three shapes
stand on a heavy black ground line, each in its colour: the triangle (three acute 60° corners) in yellow, the square
(four right angles) in red, the circle (no corners at all) in blue, with angle marks drawn over them and big
corner counts 3 / 4 / 0 underneath. Title 形与色, the thesis knocked out of a black bar, the lecture details, a
construction grid, register targets, crop marks, a colour bar and a pencilled edition number. Printed screen by
screen, light to dark: tint grid -> yellow -> red -> blue -> black. No image model.
python3 bauhaus_form_colour.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from bauhaus import Bauhaus, YELLOW, RED, BLUE, BLACK

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'bauhaus_form_colour.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

b = Bauhaus(1920, 1080, seed=19, misreg=2.6)
W, H = b.W, b.H

# ---- the sheet: cream stock, a 15 x 8 grid of 120 px modules inside a 60 px printer's margin
b.paper(margin=60, module=120)
GROUND = 840                                   # top of the black ground line (half a module under row 6)
b.marks(targets=[(960, 30), (960, 1050), (30, 540), (1890, 540)], bar=(1712, 1040))
b.stage('paper')

# ---- screen 0: pale tint, the construction grid
b.grid()
b.stage('grid')

# ---- screen 1: yellow -- the triangle, three acute corners
TX0, TX1 = 60, 600
b.pull(b.triangle(TX0, TX1, GROUND), YELLOW)
b.stage('yellow')

# ---- screen 2: red -- the square, four right angles
SX0, SX1 = 720, 1200
b.pull(b.rect(SX0, GROUND - (SX1 - SX0), SX1, GROUND), RED)
b.stage('red')

# ---- screen 3: blue -- the circle, no corners
CR = 240
CX, CY = 1560, GROUND - CR
# the circle's centre and radius are cut out of the blue stencil, so they print as bare paper
radius = np.maximum.reduce([b.circle(CX, CY, 12), b.bar(CX, CY, CX + CR - 18, CY, 7),
                            b.text_mask('r', CX + CR / 2 - 6, CY - 20, 46, anchor='ms')])
b.pull(b.circle(CX, CY, CR), BLUE, knock=radius)
b.stage('blue')

# ---- screen 4: black -- ground line, thesis bar (type knocked out), angle marks
b.pull(b.rect(60, GROUND, 1860, GROUND + 26), BLACK)
knock = np.maximum(b.text_mask('角越尖，色越亮。', 752, 258, 58, font='cjk'),
                   b.text_mask('SHARPER CORNERS · BRIGHTER COLOUR', 1830, 250, 20, anchor='rs', spacing=3.2))
b.pull(b.rect(720, 190, 1860, 282), BLACK, knock=knock)
# triangle: the 60° corner
b.pull(b.arc(TX0, GROUND, 96, 0, 60, 6), BLACK)
b.text('60°', TX0 + 118, GROUND - 40, 34)
# square: the right angle
b.pull(np.maximum(b.bar(SX0, GROUND - 80, SX0 + 80, GROUND - 80, 6, cap='square'),
                  b.bar(SX0 + 80, GROUND - 80, SX0 + 80, GROUND, 6, cap='square')), BLACK)
b.text('90°', SX0 + 104, GROUND - 40, 34)
b.stage('bars')

# ---- black: the title
b.text('形与色', 52, 262, 210, font='cjk')
b.text('FORM & COLOUR', 720, 150, 56, spacing=2)
b.stage('title')

# ---- black: lecture details and the three captions under the ground line
b.text('基础课 · 第 3 讲', 1860, 104, 32, font='cjk', anchor='rs')
b.text('10 月 16 日 周五 19:00 · 北楼 204', 1860, 146, 23, font='cjk', anchor='rs')
for x, n, l1, l2, l3 in [(TX0, '3', '三个锐角 → 黄', '最尖，所以最亮', 'TRIANGLE · 60° · YELLOW'),
                         (SX0, '4', '四个直角 → 红', '最稳，所以最重', 'SQUARE · 90° · RED'),
                         (1320, '0', '没有角 → 蓝', '最静，所以最深', 'CIRCLE · NO CORNERS · BLUE')]:
    b.text(n, x - 4, 1012, 150)
    nx = x + b.text_width(n, 150) + 26
    b.text(l1, nx, 934, 34, font='cjk')
    b.text(l2, nx, 974, 24, font='cjk')
    b.text(l3, nx, 1008, 15, spacing=2.4)
# margin slugs
b.text('形与色 · FORM & COLOUR — 基础课讲座海报', 86, 38, 14, font='cjk_book', spacing=1.2)
b.text('SHEET 03 / 12 · SCREEN PRINT · Y  R  B  K', 1834, 38, 13, anchor='rs', spacing=2.2)
b.text('丝网四色 · 先浅后深 · 黄 → 红 → 蓝 → 黑', 200, 1057, 14, font='cjk_book', spacing=1.2)

# ---- after printing: the edition number in pencil
b.pencil('7/40', 86, 1060, 28, pressure=0.85)

b.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
