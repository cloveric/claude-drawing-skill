"""Example (lab notebook x stickers): 咖啡萃取实验 / Coffee Brewing Experiment — a page of a wire-o lab notebook
lying on a graphite desk: a filled-in header with a label-maker date, a pencil-ruled table of six pour-over
trials (grind, water temperature, brew time, taste score), a pencil chart of brew time against score with a
hatched sweet spot, the best trial highlighted and looped in red pen, a mint sticky note with the conclusion,
die-cut stickers for the key numbers, an old coffee ring in the margin, and a pencil lying beside the notebook.
No image model.
python3 notebook_brewing.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from notebook import Notebook, INK, SOFT, LEAD, RED, MINT, MINTD
from core import polygon_mask

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'notebook_brewing.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

nb = Notebook(1920, 1080, seed=27)
PX0, PY0, PX1, PY1 = 112, 100, 1796, 1018

# ---- desk, notebook, binding
nb.desk()
nb.stage('desk')
nb.notebook(PX0, PY0, PX1, PY1)
nb.stain(182, 912, 60, strength=0.3)                                    # an old mug ring in the margin
nb.binding()
nb.stage('notebook')

# ---- header form, filled in; title
for (x, w, lab) in [(300, 330, '实验编号  EXP. NO.'), (690, 350, '日期  DATE'), (1100, 470, '方法  METHOD'), (1630, 110, '页  PAGE')]:
    nb.text(lab, x, 176, 15, SOFT, 'sans_bold', spacing=2.5, medium='print')
    nb.rule(x, 228, x + w, 228, 2.0, 0.55)
nb.text('CB-07', 302, 214, 32, INK, 'typewriter', medium='typed')
nb.text('手冲 Pour-over · 15 g : 240 g', 1102, 214, 27, INK, 'sans_bold')
nb.text('07', 1632, 214, 32, INK, 'typewriter', medium='typed')
nb.text('COFFEE BREWING EXPERIMENT', 304, 296, 19, MINTD, 'sans_bold', spacing=5)
nb.text('咖啡萃取实验', 298, 404, 104, INK, 'cjk_sans', weight=1.6)
nb.text('同一包豆子，六组对照  ·  one bag of beans, six trials', 304, 452, 25, SOFT, 'sans')
nb.stage('header')

# ---- trial table: pencil-ruled, typed values
TRIALS = [('01', '1000', '90', '2:15', '6.1'), ('02', '850', '92', '2:40', '7.2'), ('03', '700', '93', '3:05', '8.1'),
          ('04', '600', '93', '3:20', '8.8'), ('05', '500', '94', '3:45', '7.6'), ('06', '400', '96', '4:20', '6.0')]
COLS = [326, 470, 632, 792, 955]
for x, cn, en in zip(COLS, ['#', '研磨', '水温', '时间', '评分'], ['TRIAL', 'GRIND µm', 'TEMP °C', 'TIME min', 'SCORE /10']):
    nb.text(cn, x, 508, 19, SOFT, 'sans_bold', 'ms', medium='print')
    nb.text(en, x, 532, 12, SOFT, 'sans_bold', 'ms', spacing=2, medium='print')
nb.rule(300, 548, 1040, 548, 2.2, 0.8)
nb.rule(300, 553, 1040, 553, 1.6, 0.55)
ROW0, RH = 590, 60
for i, row in enumerate(TRIALS):
    y = ROW0 + i * RH
    for x, val in zip(COLS, row):
        nb.text(val, x, y + 12, 33, INK, 'typewriter', 'ms', medium='typed')
    if i < len(TRIALS) - 1:
        nb.rule(304, y + RH / 2, 1036, y + RH / 2, 1.8, 0.45)
nb.rule(300, ROW0 + 5.5 * RH, 1040, ROW0 + 5.5 * RH, 2.2, 0.8)
nb.rule(378, 516, 378, ROW0 + 5.5 * RH, 1.8, 0.45)
for i, (x, lab, done) in enumerate([(300, '滤纸预湿 rinse', True), (556, '闷蒸 30 s bloom', True), (830, '下次试 92 °C', False)]):
    nb.checkbox(x, 952, 22, checked=done)
    nb.text(lab, x + 34, 971, 21, INK, 'sans')
nb.stage('table')

# ---- chart: brew time vs score, pencil on graph paper
X0, X1, Y0, Y1 = 1200, 1690, 290, 620
to_px = nb.axes(X0, Y0, X1, Y1, (2.0, 4.5), (5, 10), [2.0, 2.5, 3.0, 3.5, 4.0, 4.5], [5, 6, 7, 8, 9, 10],
                ['2:00', '2:30', '3:00', '3:30', '4:00', '4:30'], ['5', '6', '7', '8', '9', '10'], size=18)
nb.text('评分 SCORE', X0 + 22, Y0 - 8, 16, SOFT, 'sans_bold', medium='print')
nb.text('min', X1 + 24, Y1 - 16, 16, SOFT, 'sans_bold', 'ms', medium='print')
nb.text('FIG. 1  时间 vs 评分', X0, 700, 16, SOFT, 'sans_bold', spacing=1, medium='print')
tt = np.array([2.25, 2.667, 3.083, 3.333, 3.75, 4.333]); sc = np.array([6.1, 7.2, 8.1, 8.8, 7.6, 6.0])
fit = np.polyfit(tt, sc, 2)
ts = np.linspace(2.12, 4.45, 30)
curve = [to_px(t, np.polyval(fit, t)) for t in ts]
band = [to_px(3.0, 5.0)] + [to_px(t, np.polyval(fit, t) - 0.12) for t in np.linspace(3.0, 3.5, 12)] + [to_px(3.5, 5.0)]
nb.hatch(polygon_mask(nb.H, nb.W, band, 2), angle=50, spacing=7.5, pressure=0.5, width=1.8)
nb.pencil(curve[:17], 3.2, 0.8, 1.6)                                   # drawn in two strokes that overlap a little
nb.pencil([(x + 0.8, y + 1.2) for x, y in curve[15:]], 3.2, 0.8, 1.6)
for t, s in zip(tt, sc):                                                 # data points: small pressed-in dots
    x, y = to_px(t, s)
    nb.pencil([(x + r * np.cos(a), y + r * np.sin(a)) for r, a in zip(np.linspace(3.8, 0.6, 18), np.linspace(0, 4 * np.pi, 18))], 2.8, 1.0, 0.15)
bx, by = to_px(3.333, 8.8)
nb.pencils([[(X0 + 8 + k * 14, by), (X0 + 16 + k * 14, by)] for k in range(int((bx - X0 - 24) / 14))], 1.8, 0.55, 0.2, smooth=False)
nb.pencils([[(bx, by + 14 + k * 14), (bx, by + 22 + k * 14)] for k in range(int((Y1 - by - 20) / 14))], 2.0, 0.7, 0.2, smooth=False)
nb.text('SWEET SPOT', 1532, 598, 16, LEAD, 'typewriter', medium='typed')
nb.pencil([(1526, 590), (1510, 584), (1490, 582)], 2.0, 0.7, 0.4)
nb.arrowhead((1488, 582), 182, 10, 2.0)
nb.stage('chart')

# ---- highlighter: the best trial, and the key phrase of the title
YB = ROW0 + 3 * RH
nb.highlight(306, 1034, YB + 1, 46, tilt=-3)
nb.highlight(298 + 2 * 104 - 2, 298 + 4 * 104 + 14, 372, 50, tilt=-2, alpha=0.7)
nb.stage('highlighter')

# ---- red pen: loop the best row and the best point, arrows to the conclusion
nb.pen_loop(668, YB + 1, 392, 38, rot=-1.0)
nb.pen_loop(bx, by, 24, 22, rot=8, a0=150, width=3.6)
nb.pen_arrow([(1066, YB + 14), (1104, YB + 52), (1150, YB + 74)], 3.8, 18)
nb.pen_arrow([(bx + 22, by - 18), (bx + 52, by - 40), (bx + 78, by - 48)], 3.6, 15)
nb.stage('red_pen')

# ---- paper bits: sticky note with the conclusion, die-cut stickers, label-maker date
f = nb.sticky(1376, 858, 392, 200, rot=1.6)
nb.text('结论  CONCLUSION', *f.pt(26, 40), 16, MINTD, 'sans_bold', rot=f.rot, spacing=3)
nb.text('中细研磨 600 µm', *f.pt(26, 94), 34, INK, 'sans_bold', rot=f.rot)
nb.text('93 °C · 3:20 · 8.8 / 10', *f.pt(26, 138), 27, INK, 'sans_bold', rot=f.rot)
nb.text('酸甜平衡，回甘最长', *f.pt(26, 176), 23, SOFT, 'sans', rot=f.rot)
u0 = 26 + nb.text_width('中细研磨 ', 34, 'sans_bold'); u1 = 26 + nb.text_width('中细研磨 600 µm', 34, 'sans_bold')
nb.pen([f.pt(u0 - 4, 107), f.pt((u0 + u1) / 2, 109.5), f.pt(u1 + 8, 105)], 3.6)
nb.sticker(1618, 322, 146, 84, rot=-6, colour=RED, radius=16,
           lines=[('BEST', 73, 29, 16, 'sans_bold', '#ffffff'), ('8.8', 73, 72, 44, 'sans_bold', '#ffffff')])
nb.sticker(1016, 356, 118, 118, rot=8, colour=MINT, shape='circle',
           lines=[('粉水比 RATIO', 59, 40, 13, 'sans_bold', MINTD), ('1:16', 59, 82, 40, 'sans_bold', INK)])
nb.sticker(bx, 690, 96, 40, rot=-4, colour='#2c3846', radius=20,
           lines=[('3:20', 48, 30, 25, 'sans_bold', '#ffffff')])
nb.label_tape('2026.09.27', 692, 204, 22, rot=-1.2)
nb.stage('stickers')

# ---- a pencil lying beside the notebook
nb.pencil_prop(1872, 262, angle=88.6, length=1000, width=32, label='HB')

nb.save(out, stages_dir=stages)
print('saved', out)
