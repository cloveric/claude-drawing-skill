"""Example (Flexoki paper): 一杯手冲咖啡，拆成五张图 / Pour-over, in five diagrams — an explainer sheet on warm paper.

Warm Flexoki paper (#FFFCF0); an ink chip, a heavy heading with a grey English tag, a big timer at the top right
(2:30, from bloom to cup). Five light-grey rounded panels, each with a heavy title, a grey chart-type tag and a mono
index number, each holding one diagram drawn the way a lightweight diagram renderer draws it:
  01 flowchart  从豆子到一杯: 称豆 -> 研磨 -> 冲洗滤纸 -> 闷蒸, down to a diamond 「鼓包平了？」, 是 -> 分两段注水
                -> 出杯, 否 loops back to 闷蒸 (a filleted orthogonal edge); paper-filled boxes with grey borders,
                ink lines, small triangular heads, green / red edge labels on a patch of panel colour;
  02 sequence   两分半里发生了什么: 水壶 / 滤杯 / 分享壶, dashed lifelines, an activation bar, three pours with a
                time column (0:00 0:45 1:15), a note 「排气 · 45 s」, the dashed reply 「约 210 g 咖啡液」 at 2:30;
  03 bar chart  磨多细，滴多久: drawdown time by grind on a hairline grid, the chosen grind in orange;
  04 pie        240 g 水分三次: 30 / 120 / 90 g with paper gaps, fractions on the slices, a legend;
  05 table      三种冲法: pour-over / French press / espresso, a tinted header with accent dots, the pour-over
                column ringed in orange.
A footnote with the recipe. No logos, no image model.
--stages DIR writes the draw-on sequence: the heading rises, the panels rise dim, then one by one each panel lights
up with an orange focus ring while its diagram draws -- nodes pop, edges draw on edge by edge and land their heads,
messages fly, the timer rolls 0:00 -> 2:30, bars grow with their values rolling, the pie sweeps, table rows slide in.
Stage names: 'x~nn' = an in-between frame of something moving (hard cut), 'x@ms' = hold, the rest cross-fade.
python3 flexoki_pour_over.py [out.jpg] [--stages DIR]
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from flexoki import (FlexokiPaper, Node, rounded, PAPER, INK, UI, TX1B, TX2, TX3, ORANGE4, RED4, GREEN4, BLUE4,
                     CYAN4, PURPLE4)

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'flexoki_pour_over.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
T0 = time.time()
fx = FlexokiPaper(1920, 1080, seed=3, keep_stages=bool(stages))
fx.paper()

ease_out = lambda u: 1 - (1 - min(1.0, max(0.0, u))) ** 3
ease_io = lambda u: (lambda v: 3 * v * v - 2 * v ** 3)(min(1.0, max(0.0, u)))
q = lambda p, a, b: min(1.0, max(0.0, (p - a) / (b - a)))            # progress of a sub-interval [a, b] of p
mmss = lambda s: f'{int(s) // 60}:{int(s) % 60:02d}'

# ===================================================================== layout
X0, X1 = 120, 1800
PANELS = {  # name: (x0, y0, x1, y1, title, tag, index)
    'p1': (120, 208, 1136, 622, '从豆子到一杯', 'Flowchart', '01'),
    'p2': (1160, 208, 1800, 622, '两分半里发生了什么', 'Sequence', '02'),
    'p3': (120, 646, 616, 1004, '磨多细，滴多久', 'Bar chart', '03'),
    'p4': (640, 646, 1136, 1004, '240 g 水分三次', 'Pie', '04'),
    'p5': (1160, 646, 1800, 1004, '三种冲法', 'Compare', '05'),
}
BOX = {}

# ===================================================================== header: chip, heading, timer, footnote
fx.layer('chip', z=10)
fx.chip(X0, 78, '图解 · 手冲咖啡', size=24)
fx.layer('heading', z=10)
fx.heading(X0 - 3, 170, '一杯手冲咖啡', 'Pour-over, in five diagrams', size=62, en_size=31)
TIMER_W = fx.measure('2:30', 108, 'heavy', spacing=-0.03 * 108)
fx.layer('timer_label', z=10)
fx.chip(X1 - TIMER_W - 22, 170 - 108 * 0.36, '总时长', fg=INK, bg=UI, size=24, anchor='r')


def draw_timer(sec, dim=False):
    fx.layer('timer', z=10, fresh=True)
    fx.number(X1 + 2, 170, mmss(sec), 108, TX3 if dim else INK, anchor='rs')


draw_timer(150)
fx.layer('foot', z=10)
fx.text('配方：15 g 咖啡粉 · 240 g 热水（93 °C，粉水比 1 : 16）· 中细研磨。时间和数字是示意，换了豆子要再调。',
        X0, 1050, 20, TX2, 'medium')

# ===================================================================== the five panels (and their focus rings)
for k, (name, (x0, y0, x1, y1, title, tag, num)) in enumerate(PANELS.items()):
    fx.layer(name, z=1)
    BOX[name] = fx.panel(x0, y0, x1 - x0, y1 - y0, title=title, tag=tag, num=num, title_size=32, pad=30)
    fx.layer('ring' + name[1], z=3)
    fx.focus(BOX[name], ORANGE4, 4)
fx.end()
print(f'panels {time.time() - T0:5.1f}s') if os.environ.get('FLEXOKI_TIMING') else None

# ===================================================================== 01 flowchart (snake: row 1 left -> right, row 2 right -> left)
R1Y, R2Y = 352, 532
ROW1 = [('称豆 15 g', 144, 'rect'), ('研磨 · 中细', 160, 'rect'), ('冲洗滤纸', 148, 'round'), ('闷蒸 30 g 水', 168, 'rect')]
FL0, FL1 = 152, 1038
gap = (FL1 - FL0 - sum(w for _, w, _ in ROW1)) / 3
xs, x = [], FL0
for _, w, _ in ROW1:
    xs.append(x + w / 2); x += w + gap
N1 = [Node(cx, R1Y, w, 56, sh) for cx, (_, w, sh) in zip(xs, ROW1)]
ND = Node(xs[3], R2Y, 204, 104, 'diamond')
N6 = Node(xs[0], R2Y, 120, 56, 'stadium')
N5 = Node((N6.x1 + ND.x0) / 2, R2Y, 172, 56, 'rect')           # equal edges either side
LX = ND.x1 + 34                                                         # the 否 loop runs up this x
FLOW = [  # in drawing order: ('n', node, label) or ('e', points, kwargs)
    ('n', N1[0], ROW1[0][0]), ('e', [N1[0].side('r'), N1[1].side('l')], {}),
    ('n', N1[1], ROW1[1][0]), ('e', [N1[1].side('r'), N1[2].side('l')], {}),
    ('n', N1[2], ROW1[2][0]), ('e', [N1[2].side('r'), N1[3].side('l')], {}),
    ('n', N1[3], ROW1[3][0]), ('e', [N1[3].side('b'), ND.side('t')], {}),
    ('n', ND, '鼓包平了？'), ('e', [ND.side('l'), N5.side('r')], dict(label='是', label_fill=GREEN4)),
    ('n', N5, '分两段注水'), ('e', [N5.side('l'), N6.side('r')], {}),
    ('n', N6, '出杯'),
    ('e', rounded([ND.side('r'), (LX, R2Y), (LX, R1Y), N1[3].side('r')], 16), dict(label='否', label_fill=RED4)),
]


def draw_flow(p):
    fx.layer('flow', z=5, fresh=True)
    n = len(FLOW)
    for i, (kind, obj, arg) in enumerate(FLOW):
        a = i / (n - 1) * 0.86
        t = q(p, a, a + 0.14)
        if t <= 0: continue
        if kind == 'n':
            fx.node(obj.cx, obj.cy, obj.w, obj.h, arg, obj.shape, size=22, p=ease_out(t))
        else:
            fx.edge(obj, p=ease_io(t), **arg)


# ===================================================================== 02 sequence diagram (+ the timer)
LL = [1330, 1518, 1704]                                                 # lifelines: 水壶 滤杯 分享壶
PART = ['水壶', '滤杯', '分享壶']
PY, LY1 = 318, 600
ACT = (380, 584)                                                        # activation on 滤杯
MSG = [  # (y, from, to, label, time, reply)
    (386, 0, 1, '闷蒸 30 g', 0, False), (476, 0, 1, '注水至 150 g', 45, False),
    (526, 0, 1, '注水至 240 g', 75, False), (576, 1, 2, '约 210 g 咖啡液', 150, True),
]
NOTE = (1538, 398, 1672, 436, '排气 · 45 s')
MSG_T = [(0.30, 0.42), (0.50, 0.62), (0.62, 0.74), (0.78, 0.92)]       # when each message flies (in p)


def tip(i, j):
    """message end x: the edge of the activation bar on 滤杯, the lifeline elsewhere"""
    if j == 1: return LL[1] - 7 if i < j else LL[1] + 7
    return LL[j]


def draw_seq(p):
    fx.layer('seq', z=5, fresh=True)
    for k, x in enumerate(LL):
        fx.lifeline(x, PY + 22, LY1, p=ease_io(q(p, 0.08 + 0.04 * k, 0.3 + 0.04 * k)))
    fx.activation(LL[1], ACT[0], ACT[1], 14, p=q(p, MSG_T[0][0], MSG_T[3][1]))
    for k, (x, s) in enumerate(zip(LL, PART)):
        fx.node(x, PY, 132, 44, s, size=21, p=ease_out(q(p, 0.04 * k, 0.12 + 0.04 * k)))
    for (y, i, j, lab, sec, rep), (a, b) in zip(MSG, MSG_T):
        t = q(p, a, b)
        if t <= 0: continue
        x0 = LL[i] + (7 if i == 1 else 0)
        fx.message(x0, tip(i, j), y, lab, ease_io(t), reply=rep, size=19)
        fx.text(mmss(sec), 1236, y, 19, TX2, 'medium', 'rm', min(1.0, 2 * t), family='mono')
    fx.note(*NOTE, size=18, p=ease_out(q(p, 0.42, 0.5)))


def seq_clock(p):
    """the timer while the sequence draws: 0:00 at the first pour, then each message's time as it lands"""
    keys = [(MSG_T[0][0], 0), (MSG_T[0][1], 0)] + [(b, MSG[k][4]) for k, (a, b) in enumerate(MSG_T) if k]
    ps, vs = zip(*keys)
    return float(np.interp(p, ps, vs))


# ===================================================================== 03 bar chart
GRIND = ['粗', '中', '中细', '细']
DRAW_S = [110, 135, 150, 200]                                            # drawdown seconds (illustrative)
B3 = BOX['p3']
PLOT = (B3.x0 + 92, B3.y0 + 104, B3.x1 - 30, B3.y1 - 62)


def draw_bars(p):
    fx.layer('bars', z=5, fresh=True)
    ps = [ease_out(q(p, 0.1 * i, 0.1 * i + 0.62)) for i in range(4)]
    fx.bars(*PLOT, DRAW_S, GRIND, [CYAN4, CYAN4, ORANGE4, CYAN4], vmax=240, ticks=[0, 60, 120, 180, 240],
            tick_fmt=mmss, p=ps, value_fmt=mmss, bar_w=0.5, size=20, value_colours=[INK, INK, ORANGE4, INK])


# ===================================================================== 04 pie
B4 = BOX['p4']
POUR = [('闷蒸', 30, ORANGE4), ('第一段', 120, BLUE4), ('第二段', 90, GREEN4)]
PC = (B4.x0 + 148, B4.y0 + 210)


def draw_pie(p):
    fx.layer('pie', z=5, fresh=True)
    fx.pie(*PC, 112, [v for _, v, _ in POUR], [c for _, _, c in POUR], sweep=ease_io(q(p, 0, 0.72)), gap=3,
           labels=['1/8', '1/2', '3/8'], label_size=21, label_r=0.64)
    al = [ease_out(q(p, 0.3 + 0.16 * i, 0.5 + 0.16 * i)) for i in range(3)]
    items = [(c, s, f'{round(v * a)} g') for (s, v, c), a in zip(POUR, al)]
    fx.legend(B4.x0 + 296, B4.y0 + 158, items, size=21, pitch=52, swatch=22, value_x=B4.x1 - 30, alpha=al,
              value_family='sans')


# ===================================================================== 05 comparison table
B5 = BOX['p5']
fx.layer('tbl', z=5)
TB = fx.table(B5.x0 + 30, B5.y0 + 82, [114, 156, 156, 154], 4, row_h=50, head_h=50,
              header=['', '手冲', '法压壶', '意式'], dots=[None, ORANGE4, PURPLE4, CYAN4], size=21)
ROWS = [['方式', '滴滤', '浸泡', '9 bar 加压'], ['研磨', '中细', '粗', '极细'], ['时间', '2:30', '4:00', '0:30'],
        ['口感', '干净明亮', '醇厚', '浓厚']]
for i, row in enumerate(ROWS):
    fx.layer(f'tbl_r{i}', z=6)
    fx.table_row(TB, i, row, size=21)
fx.layer('tbl_ring', z=7)
fx.focus(TB.col(1), ORANGE4, 3, r=10)
fx.end()

# everything in its final state
draw_flow(1); draw_seq(1); draw_bars(1); draw_pie(1)
fx.end()
print(f'drawn  {time.time() - T0:5.1f}s') if os.environ.get('FLEXOKI_TIMING') else None

# ===================================================================== the draw-on sequence
REST = dict(dx=0.0, dy=0.0, scale=1.0, alpha=1.0, reveal=1.0)
DIM = 0.42
RINGS = ['ring1', 'ring2', 'ring3', 'ring4', 'ring5']
if stages:
    for n in fx.layers: fx.hide(n)
    fx.stage('paper@400')
    for k in range(1, 6):                                    # chip and heading rise, a frame apart
        u1, u2 = ease_out(k / 4), ease_out((k - 1) / 4)
        fx.pose('chip', dy=18 * (1 - u1), alpha=u1)
        fx.pose('heading', dy=24 * (1 - u2), alpha=u2)
        fx.stage(f'head~{k}')
    draw_timer(0, dim=True)
    for k in range(1, 4):
        u = ease_out(k / 3)
        fx.pose('timer', dy=16 * (1 - u), alpha=u); fx.pose('timer_label', dy=16 * (1 - u), alpha=u)
        fx.stage(f'timer~{k}')
    fx.stage('header@250')
    names = list(PANELS)
    for k in range(1, 15):                                   # the five panels rise dim, two frames apart
        for i, n in enumerate(names):
            u = ease_out((k - 2 * i) / 5)
            fx.pose(n, dy=26 * (1 - u), alpha=DIM * u)
        fx.pose('foot', alpha=ease_out((k - 8) / 5))
        fx.stage(f'panels~{k:02d}')
    fx.stage('panels@300')

    def light(i, steps=3):
        """panel i comes up to full strength and takes the ring; the previous ring fades"""
        if i < 4: fx.show(['flow', 'seq', 'bars', 'pie'][i])     # its content layer (redrawn as it draws on)
        for k in range(1, steps + 1):
            u = k / steps
            fx.pose(names[i], alpha=DIM + (1 - DIM) * u)
            fx.show(RINGS[i], alpha=u)
            if i: fx.show(RINGS[i - 1], alpha=1 - u)
            fx.stage(f'light{i + 1}~{k}')

    light(0)
    for k in range(1, 29):
        draw_flow(k / 28); fx.stage(f'flow~{k:02d}')
    fx.stage('flow@350')
    light(1)
    for k in range(1, 31):
        p = k / 30
        draw_seq(p)
        if p >= MSG_T[0][0]: draw_timer(seq_clock(p))
        fx.stage(f'seq~{k:02d}')
    draw_timer(150); fx.stage('seq@350')
    light(2)
    for k in range(1, 15):
        draw_bars(k / 14); fx.stage(f'bars~{k:02d}')
    fx.stage('bars@300')
    light(3)
    for k in range(1, 15):
        draw_pie(k / 14); fx.stage(f'pie~{k:02d}')
    fx.stage('pie@300')
    light(4)
    for k in range(1, 4):
        u = ease_out(k / 3); fx.pose('tbl', dy=14 * (1 - u), alpha=u); fx.stage(f'tbl~{k}')
    for i in range(4):
        for k in range(1, 4):
            u = ease_io(k / 3); fx.pose(f'tbl_r{i}', reveal=u, feather=60); fx.stage(f'row{i}~{k}')
    for k, (sc, al) in enumerate([(1.06, 0.4), (1.03, 0.8), (1.0, 1.0)], 1):
        fx.pose('tbl_ring', scale=sc, alpha=al); fx.stage(f'colring~{k}')
    fx.stage('table@300')
    for k in range(1, 3):
        fx.show('ring5', alpha=1 - k / 2); fx.stage(f'unfocus~{k}')

# final poses: everything drawn, no panel ring
for n in fx.layers:
    fx.pose(n)
fx.hide(*RINGS)
draw_flow(1); draw_seq(1); draw_bars(1); draw_pie(1); draw_timer(150)
fx.save(out, stages_dir=stages)
print(f'saved  {time.time() - T0:5.1f}s') if os.environ.get('FLEXOKI_TIMING') else None
print('saved', out)
