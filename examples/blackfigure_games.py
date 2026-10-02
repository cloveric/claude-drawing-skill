"""Example (Greek black-figure vase / 古希腊黑绘陶瓶): 赛跑与赛车 · Games on a Vase.

An Attic black-figure neck amphora on a museum plinth, and beside it the two friezes that run all the way round
it, unrolled flat on a panel.  Upper frieze: a four-horse chariot race -- on the front (the half you can see) the
leader and, right on his tail, the challenger whose far trace horse is white; round the back the turning post, the straggler,
the prize tripod and the official holding the victor's wreath.  Lower frieze: the foot race -- five sprinters
on the front, the finish post, the umpire with his forked rod, a table with the prize (a little amphora just
like this one) and two stragglers round the back.  Neck: palmettes and lotus; shoulder: black and red tongues;
a running meander between the friezes; rays above the foot.

Draw-on stages: thrown clay pot -> wheel-painted bands -> ornament -> silhouettes in slip -> incision ->
added red and white -> firing (the slip turns glossy black) -> 2,500 years -> the rollout panel.  No image model.
python3 blackfigure_games.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from blackfigure import BlackFigure

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'blackfigure_games.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

bf = BlackFigure(1920, 1080, seed=8)
bf.museum(wall='#1c2427', plinth='#cbc2b4')
H = 930
pot = bf.throw(cx=470, foot=990, height=H)
Y = lambda f: f * H                                   # heights on the pot as fractions of its height
bf.stage('thrown')

# ---- on the wheel: lip, neck, foot and the frame lines of every frieze
pot.paint_handles()
for a, b in [(0, .062), (.062, .080), (.212, .244), (.320, .326), (.570, .576), (.601, .606), (.722, .745),
             (.751, .756), (.850, .928), (.940, .994)]:
    pot.band(Y(a), Y(b))
bf.stage('wheel_bands')

# ---- ornament
pot.palmettes(Y(.084), Y(.210), n=5)
pot.tongues(Y(.247), Y(.316))
pot.meander(Y(.578), Y(.600))
pot.rays(Y(.756), Y(.850))
pot.paint()
bf.stage('ornament')

# ---- upper frieze: the chariot race (x = arc length round the pot from the left handle; front half = 0..C/2)
cz = pot.zone(Y(.326), Y(.570))
hw = 146
cz.quadriga(262, hw, white_horse=0, red_manes=(2,), bends=(0.20, -0.06, 0.12, -0.04))
cz.letters('ΗΟ ΠΑΙΣ', 262 - 0.62 * hw, cz.y0 + 16, size=13)
cz.quadriga(700, hw, red_manes=(1, 3), bends=(0.14, -0.04, 0.07, -0.10))
cz.letters('ΚΑΛΟΣ', 700 - 0.55 * hw, cz.y0 + 16, size=13)
cz.column(965, height=(cz.y1 - cz.y0) * 0.9)
cz.letters('ΤΕΡΜΑ', 995, cz.y0 + 40, size=12, vertical=True)
cz.bird(1275, cz.y0 + 34, size=44, facing=1, flap=0.1)
cz.quadriga(1300, hw * 0.97, red_manes=(2,), bends=(0.04, 0.12, -0.05, 0.08))
cz.tripod(1540, height=(cz.y1 - cz.y0) * 0.6)
cz.judge(1665, height=(cz.y1 - cz.y0) * 0.86, facing=-1, holds='wreath')
cz.letters('ΚΑΛΟΣ', 1735, cz.y0 + 40, size=12, vertical=True, retro=True)

# ---- lower frieze: the foot race
rz = pot.zone(Y(.606), Y(.722))
for i, x in enumerate((95, 236, 377, 518, 660)):
    rz.runner(x, phase=i % 2, beard=(i == 2), back_arm='up' if i % 2 else 'down')
rz.column(840, height=(rz.y1 - rz.y0) * 0.78, red=False)
rz.judge(915, height=(rz.y1 - rz.y0) * 0.86, facing=-1, holds='rod')
rz.prize_table(1020)
rz.runner(1240, phase=1, back_arm='up')
rz.runner(1410, phase=0, back_arm='down', beard=True)

pot.paint()
bf.stage('silhouettes')
pot.incise()
bf.stage('incision')
pot.add_colour()
bf.stage('added_colours')
pot.fire()
bf.stage('fired')

# ---- 2,500 years: flaking white, encrustation and root marks, chips, a mended loss, a misfired patch
pot.age(mend=(282, Y(.69), 34, 24), misfire=(pot.TW * 0.6, Y(.47), 70), chips=7, roots=14)
bf.stage('aged')

# ---- the panel: both friezes unrolled, front half and back half
bands = [(Y(.326), Y(.576)), (Y(.576), Y(.606)), (Y(.606), Y(.728))]
bf.panel((905, 52, 1872, 1028), title='赛跑与赛车', subtitle='黑绘颈柄双耳瓶 · 瓶身两圈饰带展开',
         english='Black-figure neck amphora: the two friezes unrolled', greek='ΤΕΘΡΙΠΠΟΝ · ΔΡΟΜΟΣ')
bf.rollout(pot, bands, 1388, 258, scale=0.82, half=0, caption='A 面 · 正面（瓶上看得见的半圈）', ticks=('0°', '180°'))
bf.rollout(pot, bands, 1388, 630, scale=0.82, half=1, caption='B 面 · 背面（转到瓶后才看得见）', ticks=('180°', '360°'))
bf.legend(945, 1003, [('赤陶', 'clay'), ('黑釉', 'black'), ('刻线', 'incision'), ('加红', 'red'), ('加白', 'white')])

bf.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
