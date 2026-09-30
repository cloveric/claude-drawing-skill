"""Example (fuse beads / 拼豆): 草莓杯垫 · Strawberry Coaster — how a bead coaster is made, left to right on a
craft table: ① the printed pattern chart on graph paper (a strawberry in a 21-bead circle, legend with counts,
pencil ticks on the colours already placed); ② a clear square pegboard with the same pattern half done -- the
strawberry colours are in, the sky-blue background is going in row by row, tweezers hold the next bead above
its peg, loose beads spilled beside; a sorting tray with a heap of every colour; ③ the finished coaster, ironed:
the beads have flowed into one flat, waxy piece, holes shrunk, the ironing paper peeled off beside it.
Draw-on stages: empty pegboards -> reds -> seeds and leaves -> background -> border -> ironing paper -> peeled
-> the coaster off its board. No image model.
python3 perler_strawberry_coaster.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from perler import Perler

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'perler_strawberry_coaster.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

# ---- the pattern: a strawberry on a sky-blue 21-bead circle with a white rim and a few pearl sparkles
N = 21
STRAWBERRY = ['......gg.....',
              '......g......',
              '..GGG.g.GGG..',
              '.GGGGGgGGGGG.',
              '..DGGGgGGGD..',
              '.DRRGGDGGRRD.',
              'DRPRRDRDRRRRD',
              'DRPPRRRRYRRRD',
              'DRPRRYRRRRYRD',
              'DRRRRRRRRRRRD',
              '.DRYRRRYRRRD.',
              '.DRRRRRRRYRD.',
              '..DRYRRRRRD..',
              '...DRRRYRD...',
              '....DRRRD....',
              '.....DDD.....']
grid = [['.'] * N for _ in range(N)]
inside = lambda r, c: 0 <= r < N and 0 <= c < N and (r - 10) ** 2 + (c - 10) ** 2 <= 10.45 ** 2
for r in range(N):
    for c in range(N):
        if inside(r, c):
            rim = not all(inside(r + dr, c + dc) for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            grid[r][c] = 'W' if rim else 'B'
for i, line in enumerate(STRAWBERRY):
    for j, ch in enumerate(line):
        if ch != '.': grid[3 + i][4 + j] = ch
for r, c in [(2, 7), (3, 14), (6, 2), (5, 17), (11, 1), (14, 18), (17, 4), (18, 14), (9, 19)]:
    if grid[r][c] == 'B': grid[r][c] = 'o'
PATTERN = [''.join(row) for row in grid]
KEY = {'R': 'red', 'D': 'dark_red', 'P': 'pink', 'Y': 'yellow', 'G': 'green', 'g': 'dark_green',
       'B': 'sky', 'o': 'pearl', 'W': 'white'}
NAMES = {'R': '草莓红', 'D': '深红', 'P': '浅粉', 'Y': '柠檬黄', 'G': '叶绿', 'g': '墨绿', 'B': '天蓝',
         'o': '珠光白', 'W': '白'}

p = Perler(1920, 1080, seed=11, pitch=22, ss=2)
p.desk('#e0caa6')

# ---- ① the chart, taped to the table
chart = p.chart(PATTERN, KEY, 282, 338, cell=15, angle=-2.5, title='草莓杯垫', number='PATTERN  No.07',
                subtitle='STRAWBERRY COASTER  ·  21 x 21  ·  %d BEADS' % sum(len(l) - l.count('.') for l in PATTERN),
                names=NAMES)
t1 = p.tape('看图纸', 206, 74, angle=-4, size=24, sub='PATTERN', badge='1')

# ---- sorting tray: a heap of each colour
p.tray(292, 858, [['red', 'dark_red', 'pink'], ['yellow', 'green', 'dark_green'], ['sky', 'pearl', 'white']],
       cell=86, angle=4, fill=20)

# ---- ② the square pegboard (the one being made) and ③ the round one (the one that gets ironed)
sq = p.pegboard(905, 468, 29, colour='clear', angle=1.2)
rd = p.pegboard(1582, 420, 23, shape='circle', colour='#f3dfe4', angle=-6)
t2 = p.tape('按颜色摆豆', 706, 846, angle=2, size=24, sub='PLACE', badge='2')
t3 = p.tape('熨平  成杯垫', 1478, 738, angle=-3, size=24, sub='IRON', badge='3')
p.stage('empty_pegboards')

AT_SQ, AT_RD = (4, 4), (1, 1)
p.place(sq, PATTERN, KEY, at=AT_SQ, only='RDP'); p.place(rd, PATTERN, KEY, at=AT_RD, only='RDP')
chart.done.update('RDP')
p.stage('reds')
p.place(sq, PATTERN, KEY, at=AT_SQ, only='YGg'); p.place(rd, PATTERN, KEY, at=AT_RD, only='YGg')
chart.done.update('YGg')
p.stage('seeds_leaves')

# the square board stops half way through the background: placed row by row from the top, row 13 half done
front = lambda r, c: (r - AT_SQ[0]) < 13 or ((r - AT_SQ[0]) == 13 and (c - AT_SQ[1]) < 9)
p.place(sq, PATTERN, KEY, at=AT_SQ, only='Bo', keep=front)
p.place(rd, PATTERN, KEY, at=AT_RD, only='Bo')
# the next bead goes on the first empty background peg along the front, lower right of the strawberry
todo = [(r, c) for r in range(N) for c in range(N) if PATTERN[r][c] in 'Bo' and not front(r + AT_SQ[0], c + AT_SQ[1])
        and c > 12]
tr_, tc_ = min(todo, key=lambda rc: (rc[0], rc[1]))
target = sq.xy(AT_SQ[0] + tr_, AT_SQ[1] + tc_)
p.tweezers(target, angle=-38, length=330, lift=24, holding='sky')
p.spill(1268, 912, ['sky', 'sky', 'sky', 'pearl', 'white', 'clear'], n=18, spread=62, standing=0.45)
p.spill(560, 985, ['red', 'yellow', 'green'], n=7, spread=30, standing=0.3)
p.stage('background')

p.place(rd, PATTERN, KEY, at=AT_RD, only='W')
p.stage('border_done')

paper = p.ironing_paper(1590, 425, 600, 590, angle=4)
p.on_top(t3)
p.stage('ironing_paper')

p.iron(rd, 0.70)
p.remove(paper)
paper = p.ironing_paper(1590, 425, 600, 590, angle=4, cut=((1640, 425), (np.cos(0.3), np.sin(0.3))), curl=7)
p.on_top(t3)
p.stage('peeled')

# ---- the coaster comes off its board; the used ironing paper lies beside it
p.remove(paper)
p.lift_off(rd)
p.ironing_paper(1790, 700, 330, 300, angle=14, cut=((1640, 700), (0.97, -0.24)), curl=9, wrinkle=1.8)
p.on_top(rd, t1, t2, t3)                     # the coaster lies on the paper; labels stay on top

p.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
