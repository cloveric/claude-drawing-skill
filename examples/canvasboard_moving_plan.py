"""Example (canvas board): 搬家计划 / Moving Plan — a dark, dotted infinite whiteboard in a note app's canvas view.

The app window (tab 「搬家计划.canvas」, a ribbon of line icons) and in it a board of grey dots seen through a camera.
Three groups, labels floating above them: 「收拾 · 第 1 周」 holds the plan card (violet, selected: 搬家计划, 老城区 → 河边新家,
the date with a highlight, tag pills), a red checklist of what goes before the move (three ticked and struck through,
two still open) and a small shopping card with a progress bar; 「搬家当天 · 11/8」 holds a timeline (08:00 → 13:30, a
violet dot on the last stop) and a yellow card of box numbers -- colour chips 厨房 K1–K6, 书房 S1–S9, 卧室 B1–B5, 易碎 ×4;
「新家 · 河边 3 楼」 holds an image card 「新家平面图.png」 (a floor plan sketched with hand-drawn strokes on dark grid paper:
walls, doors, windows, a bed in the bedroom's green, a desk in the study's cyan, the kitchen counter in orange, a violet
dashed route from the front door to the bed), a quote card (先把床装好，其他的明天再说。) and a green checklist for the
first night. Curved edges with arrowheads and labels tie the cards together; the zoom buttons sit top right.
The stages drop the cards in one by one, tick the tasks, draw the edges on while the camera pans from group to group,
sketch the floor plan stroke by stroke, and finally click 「fit」 and zoom out to the whole board. No image model.
python3 canvasboard_moving_plan.py [out.jpg] [--stages DIR]
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from canvasboard import (CanvasBoard, ACCENT, ACCENT2, TEXT, BRIGHT, MUTED, FAINT, EDGE, BORDER2, CARD_COLOURS as CC)

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'canvasboard_moving_plan.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
T0 = time.time()
tick = lambda name: print(f'{name:14s} {time.time() - T0:5.1f}s') if os.environ.get('CANVASBOARD_TIMING') else None

cb = CanvasBoard(1920, 1080, seed=8, keep_stages=bool(stages), stages_dir=stages, window=(40, 34, 1840, 1012),
                 tab='搬家计划.canvas')
ROOM = {'kitchen': 'orange', 'study': 'cyan', 'bed': 'green', 'fragile': 'red'}

# ===================================================================== group 1 · 收拾 (and a loose card under it)
cb.group('gA', 0, 0, 640, 724, '收拾 · 第 1 周')
A1 = cb.card('A1', 30, 36, 580, 262, colour='purple', selected=True)
A1.h1('搬家计划', 54)
A1.gap(2)
A1.p('老城区 → 河边新家', 30, BRIGHT, 'medium')
A1.p('11 月 8 日 · 周六 · ==还有 12 天==', 26, MUTED, hl='hl')
A1.gap(12)
A1.tags(['#搬家', '#待办', '#11月'])

A2 = cb.card('A2', 30, 338, 580, 356, colour='red')
A2.h2('先清掉的东西')
A2.gap(2)
for i, (s, done) in enumerate([('旧书 → 捐给社区图书馆', True), ('书桌 → 挂到二手群', True), ('冬衣 → 真空压缩袋', True),
                               ('冰箱提前一天断电', False), ('宽带、水电改到新地址', False)]):
    A2.task(s, done, key=f't{i}', lh=1.72)

A3 = cb.card('A3', 30, 808, 580, 114)
A3.p('纸箱 30 个 · 胶带 6 卷 · 记号笔', 26, TEXT)
A3.gap(8)
A3.bar(2 / 3, 10, ACCENT, label='已买 2/3', var='buy')

# ===================================================================== group 2 · 搬家当天
cb.group('gB', 800, 170, 620, 836, '搬家当天 · 11/8')
B1 = cb.card('B1', 830, 206, 560, 452)
B1.h2('时间线')
TL = [('08:00', '搬家师傅到楼下'), ('09:30', '先搬大件：床、沙发、冰箱'), ('11:00', '装车，按编号点箱子'), ('13:30', '==新家卸货==')]
ty0, tdy = B1.y + 36, 78
cb.node('B1')
cb.line([(B1.left + 9, ty0), (B1.left + 9, ty0 + tdy * 3)], 3, '#4d4d4d', var=('tl', 0.0, 0.85))
for i, (tm, what) in enumerate(TL):
    y = ty0 + i * tdy
    last = i == len(TL) - 1
    v = ('tl', i / 4, (i + 1) / 4)
    if last:
        cb.circle(B1.left + 9, y, 16, ACCENT, 0.25, var=v, mode='pop')
    cb.circle(B1.left + 9, y, 8.5, ACCENT if last else '#6a6a6a', var=v, mode='pop')
    cb.text(tm, B1.left + 40, y, 24, ACCENT2 if last else MUTED, 'medium', 'lm', family='mono', var=v, mode='fade')
    cb.rich(what, B1.left + 136, y, 28, TEXT, var=v, hl=('hl', 0, 1))
cb.end()
B1.y = ty0 + tdy * 3 + 30
B1.rule(10)
B1.p('4 位师傅 · 1 辆厢式车 · 约 3 小时', 24, MUTED)

B2 = cb.card('B2', 830, 702, 560, 270, colour='yellow')
B2.h2('箱子编号')
B2.gap(6)
B2.chips([('厨房', 'K1–K6', ROOM['kitchen']), ('书房', 'S1–S9', ROOM['study']),
          ('卧室', 'B1–B5', ROOM['bed']), ('易碎', '×4', ROOM['fragile'])], 26, var=[('chip', i / 4, (i + 1) / 4) for i in range(4)])
B2.p('一共 24 箱，两面都写上编号', 22, MUTED)

# ===================================================================== group 3 · 新家
cb.group('gC', 1580, 0, 740, 1050, '新家 · 河边 3 楼')
C1 = cb.image_card('C1', 1610, 64, 680, 430, label='新家平面图.png')
X0, Y0 = C1.x0, C1.y0
U = lambda u, v: (X0 + u, Y0 + v)
INK, INK2 = '#d4d4d4', '#9a9a9a'
strokes = []          # (fn, weight in the drawing order)


def S(fn, w=1.0):
    strokes.append((fn, w))


# outer walls (with gaps for the front door and two windows), inner walls, doors, windows, furniture, labels, route
S(lambda v: cb.rough([U(250, 372), U(50, 372), U(50, 50), U(110, 50)], 4.2, INK, seed=1, rough=1.35, var=v), 1.4)
S(lambda v: cb.rough([U(282, 50), U(430, 50)], 4.2, INK, seed=2, rough=1.35, var=v), 0.6)
S(lambda v: cb.rough([U(562, 50), U(612, 50), U(612, 372), U(318, 372)], 4.2, INK, seed=3, rough=1.35, var=v), 1.4)
S(lambda v: cb.rough([U(362, 50), U(362, 150)], 3.4, INK, seed=4, rough=1.35, var=v), 0.4)
S(lambda v: cb.rough([U(362, 202), U(362, 268)], 3.4, INK, seed=5, rough=1.35, var=v), 0.4)
S(lambda v: cb.rough([U(362, 330), U(362, 372)], 3.4, INK, seed=6, rough=1.35, var=v), 0.3)
S(lambda v: cb.rough([U(362, 222), U(612, 222)], 3.4, INK, seed=7, rough=1.35, var=v), 0.6)
S(lambda v: cb.rough([U(492, 222), U(492, 290)], 3.4, INK, seed=8, rough=1.35, var=v), 0.3)
S(lambda v: cb.rough([U(492, 336), U(492, 372)], 3.4, INK, seed=9, rough=1.35, var=v), 0.3)
for (u0, u1, sd) in [(110, 282, 10), (430, 562, 11)]:                        # windows: a double thin line in the gap
    S(lambda v, u0=u0, u1=u1, sd=sd: (cb.rough([U(u0, 45), U(u1, 45)], 1.6, INK2, seed=sd, passes=1, var=v),
                                       cb.rough([U(u0, 55), U(u1, 55)], 1.6, INK2, seed=sd + 20, passes=1, var=v)), 0.5)
S(lambda v: (cb.rough([U(318, 372), U(318, 318)], 2.2, INK2, seed=12, passes=1, var=v),               # front door + swing
             cb.rough_ellipse(*U(318, 372), 66, 54, 1.6, INK2, a0=180, sweep=90, passes=1, seed=13, var=v)), 0.5)
S(lambda v: (cb.rough([U(362, 150), U(410, 150)], 2.2, INK2, seed=14, passes=1, var=v),               # bedroom door
             cb.rough_ellipse(*U(362, 150), 48, 52, 1.6, INK2, a0=0, sweep=90, passes=1, seed=15, var=v)), 0.4)
S(lambda v: cb.rough_rect(*U(480, 74), *U(592, 186), width=3.2, fill=CC['green'], seed=16, var=v), 0.8)  # bed
S(lambda v: (cb.rough([U(480, 100), U(592, 100)], 2.2, CC['green'], seed=17, passes=1, var=v),
             cb.rough_rect(*U(492, 81), *U(530, 96), width=2.0, fill=CC['green'], passes=1, seed=18, var=v),
             cb.rough_rect(*U(542, 81), *U(580, 96), width=2.0, fill=CC['green'], passes=1, seed=19, var=v)), 0.5)
S(lambda v: cb.rough_rect(*U(70, 74), *U(190, 116), width=3.0, fill=CC['cyan'], seed=20, var=v), 0.6)    # desk
S(lambda v: cb.rough_ellipse(*U(130, 140), 15, 15, 2.4, CC['cyan'], seed=21, var=v), 0.3)               # chair
S(lambda v: cb.rough([U(376, 240), U(376, 356), U(470, 356)], 3.0, CC['orange'], seed=22, var=v), 0.6)  # counter
S(lambda v: cb.rough([U(398, 240), U(398, 334), U(470, 334)], 2.0, CC['orange'], seed=23, passes=1, var=v), 0.4)
S(lambda v: (cb.rough_rect(*U(80, 286), *U(222, 338), width=2.6, fill=INK2, seed=24, var=v),            # sofa
             cb.rough([U(80, 300), U(222, 300)], 1.8, INK2, seed=25, passes=1, var=v)), 0.6)
S(lambda v: cb.rough_ellipse(*U(150, 236), 24, 24, 2.2, INK2, seed=26, var=v), 0.3)                     # tea table
for (s, u, v_, sz) in [('客厅', 222, 178, 30), ('卧室', 410, 104, 28), ('厨房', 430, 296, 26), ('卫', 552, 296, 26),
                        ('书桌', 130, 96, 22), ('床', 536, 146, 24)]:
    S(lambda v, s=s, u=u, v_=v_, sz=sz: cb.text(s, *U(u, v_), sz, INK2 if len(s) > 1 or s == '卫' else BRIGHT, 'regular',
                                                'mm', family='hand', var=v), 0.25)
ROUTE = [U(300, 412), U(300, 340), U(292, 262), U(318, 196), U(376, 176), U(432, 166), U(470, 150)]
S(lambda v: cb.rough(ROUTE, 3.0, ACCENT2, seed=27, passes=1, rough=0.6, dash=(14, 10), var=v), 1.4)
S(lambda v: (cb.arrow_head(U(474, 148), -22, 16, ACCENT2, var=v),
             cb.text('床先进卧室', *U(324, 404), 26, ACCENT2, 'regular', 'lm', family='hand', var=v)), 0.4)
S(lambda v: cb.text('约 68 m² · 朝南', *U(54, 404), 22, FAINT, 'regular', 'lm', family='hand', var=v), 0.3)

cb.node('C1')
with cb.clip(C1.x0 + 2, C1.y0 + 2, C1.x1 - 2, C1.y1 - 2, 10):
    tot, acc = sum(w for _, w in strokes), 0.0
    for fn, w in strokes:
        fn(('ink', acc / tot, (acc + w) / tot))
        acc += w
cb.end()

C2 = cb.card('C2', 1610, 538, 680, 178)
C2.gap(6)
C2.quote(['先把床装好，', '其他的明天再说。'], 34, BRIGHT, by='写给搬家那天晚上的自己', var='q')

C3 = cb.card('C3', 1610, 760, 680, 262, colour='green')
C3.h2('第一晚要用的')
for i, (s, done) in enumerate([('床单、枕头', True), ('牙刷、毛巾', True), ('手机充电器、台灯', False)]):
    C3.task(s, done, key=f't{i}')
C3.p('都装在 `B1` 箱，最后一个上车', 24, MUTED)

# ===================================================================== edges
cb.edge('e1', ('A1', 'r', 0.5), ('B1', 'l', 0.16), colour=ACCENT, label='当天')
cb.edge('e2', ('A2', 'r', 0.6), ('B2', 'l', 0.3), colour=EDGE, label='装箱')
cb.edge('e3', ('B1', 'r', 0.84), ('C1', 'l', 0.7), colour=EDGE, label='13:30')
cb.edge('e4', ('B2', 'r', 0.62), ('C3', 'l', 0.5), colour=CC['green'], label='B1 先开')
tick('drawn')

# ===================================================================== cameras
OVER = cb.fit(-30, -64, 2320, 1050, pad=36, right=40)     # the whole board (the final frame)
K_A = (430, 300, 1.15)                                    # the plan card and the checklist
K_A3 = (470, 560, 1.0)                                    # down to the loose shopping card
K_B = (1110, 590, 1.0)                                    # the day of the move
K_C1 = (1950, 286, 1.22)                                  # close on the floor plan
K_C = (1960, 590, 1.0)                                    # the quote and the first-night list
cb.camera(*OVER)

# ===================================================================== stage by stage (the draw-on GIF), then the final frame
# Things that move get a few in-between stages (names 'mv_*': the GIF shows them as quick hard cuts -- real motion);
# everything else cross-fades. A card drops in from above: held up (big shadow, 5 % larger, half transparent), it falls,
# bounces a little and settles.
CARDS = ['A1', 'A2', 'A3', 'B1', 'B2', 'C1', 'C2', 'C3']
GROUPS = ['gA', 'gB', 'gC']
EDGES = ['e1', 'e2', 'e3', 'e4']
LIFT = dict(dy=-110, scale=1.05, alpha=0.55, lift=1.0)


def drop(name, tag, n=5, also=(), cam=None):
    cb.tween(tag, n, 'drop', moves=[(name, LIFT, None)] + list(also), cam=cam)


if stages:
    for n in CARDS + GROUPS: cb.hide(n)
    for n in EDGES: cb.set(n, p=0.0)
    cb.set('A1', hl=0.0); cb.set('A2', t0=0.0, t1=0.0, t2=0.0); cb.set('A3', buy=0.0)
    cb.set('B1', tl=0.0, hl=0.0); cb.set('B2', chip=0.0); cb.set('C1', ink=0.0); cb.set('C2', q=0.0)
    cb.set('C3', t0=0.0, t1=0.0)
    cb.camera(*K_A); cb.stage('board')
    cb.tween('grpA', 3, 'out', moves=[('gA', dict(alpha=0.0), None)])
    drop('A1', 'A1')
    cb.tween('hl', 3, 'io', moves=[('A1', dict(hl=0.0), None)])
    drop('A2', 'A2')
    for i in range(3):
        cb.tween(f'tick{i}', 3, 'out', moves=[('A2', {f't{i}': 0.0}, None)])
    drop('A3', 'A3', n=5, cam=(K_A, K_A3), also=[('A3', dict(buy=0.0), None)])
    # pan to the day of the move: the violet edge leads, the group frame fades in, then the timeline drops onto it
    cb.tween('panB', 6, 'io', moves=[('e1', dict(p=0.0), None), ('gB', dict(alpha=0.0), None)], cam=(K_A3, K_B))
    drop('B1', 'B1')
    cb.tween('tl', 4, 'linear', moves=[('B1', dict(tl=0.0, hl=0.0), None)])
    cb.tween('e2', 5, 'io', moves=[('e2', dict(p=0.0), None)])
    drop('B2', 'B2')
    cb.tween('chips', 4, 'linear', moves=[('B2', dict(chip=0.0), None)])
    # pan to the new flat, closing in on the floor plan; then sketch it stroke by stroke
    cb.tween('panC', 6, 'io', moves=[('e3', dict(p=0.0), None), ('gC', dict(alpha=0.0), None)], cam=(K_B, K_C1))
    drop('C1', 'C1')
    cb.tween('ink', 8, 'linear', moves=[('C1', dict(ink=0.0), None)])
    cb.tween('downC', 4, 'io', cam=(K_C1, K_C))
    drop('C2', 'C2')
    cb.tween('quote', 4, 'linear', moves=[('C2', dict(q=0.0), None)])
    cb.tween('e4', 5, 'io', moves=[('e4', dict(p=0.0), None)])
    drop('C3', 'C3')
    for i in range(2):
        cb.tween(f'tick_c{i}', 3, 'out', moves=[('C3', {f't{i}': 0.0}, None)])
    # the pointer comes up to the zoom buttons and clicks 'fit': the camera pulls back to the whole board
    fx, fy = cb.control(2)
    sx, sy = cb.to_screen(2120, 980)
    cb.tween('pointer', 5, 'io', between=lambda u: cb.cursor(sx + (fx - sx) * u, sy + (fy - sy) * u - 90 * np.sin(np.pi * u),
                                                            alpha=min(1.0, 3 * u)))
    cb.hover = 2
    cb.cursor(fx, fy, click=0.3, press=True); cb.stage('mv_click1')
    cb.cursor(fx, fy, click=0.65); cb.stage('click')
    cb.tween('zoom', 7, 'io', cam=(K_C, OVER), last=False,
             between=lambda u: cb.cursor(fx, fy, alpha=max(0.0, 1 - 1.6 * u)))

# final: everything at rest and finished, the whole board
cb.cursor(); cb.hover = None
for n in cb.nodes:
    cb.pose(n); cb.reset(n)
cb.camera(*OVER)
cb.save(out, stages_dir=stages)
tick('saved')
print('saved', out)
