"""Example (shadow puppetry): 蹴鞠 · Cuju by Lamplight — a shadow-play match of the old Chinese football, at the
moment the ball goes through the eye of the net.

A carved proscenium (plaque 蹴鞠, an openwork valance, corner brackets, two red lanterns) frames a lamp-lit screen.
On it, in dyed and hollow-carved donkey hide: a pailou archway as the goal (球门) with a lattice net and its round
eye (风流眼), the ornamental floor band, and four players on jointed rods. On the left the red side: the captain has
just kicked, one leg high, and his team-mate strikes the pose (亮相) with an arm over his head and a knee raised; on the
right the teal side: one leaps for the ball a little off the cloth (so his edges go soft and double), the other points
up at it. The ball sits in the eye. Two small plaques hang on threads: 球头 over the captain and 骁色 over the leaper
(two of the positions of a cuju team).

The draw-on (--stages) is real in-between motion: the lamp is lit and its glow spreads, the lintel drops in and the
lanterns swing and light, the floor band and the goal come up pressed to the cloth, the players slide in from the
wings blurred and doubled and sharpen as they are pressed to the screen, take their places, the captain kicks, the
ball flies through the eye, everyone snaps into the final pose (亮相), the plaques come down on their threads, and the
lamp gutters once before the last frame.
No image model.
python3 shadowpuppet_cuju.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from shadowpuppet import ShadowPuppet, Puppet

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'shadowpuppet_cuju.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
T0 = time.time()
tick = lambda name: print(f'{name:16s} {time.time() - T0:5.1f}s') if os.environ.get('SP_TIMING') else None

W, H = 1920, 1080
FLOOR = 932
sp = ShadowPuppet(W, H, seed=11, keep_stages=bool(stages), stages_dir=stages)
sp.screen()
sp.proscenium('蹴鞠')
lanterns = [sp.lantern(190, r=56), sp.lantern(W - 190, r=56)]
border = sp.border()
gate = sp.gate(w=270, h=540, net_h=240, eye=(0, -392), eye_r=44)
ball = sp.ball(28)
plate = sp.nameplate('球头', dye='red', size=30, string=30)
plate2 = sp.nameplate('骁色', dye='teal', size=30, string=30)
tick('props')

# ===================================================================== the players
S = 1.12
captain = sp.figure(robe='red', trim='black', accent='ochre', trousers='teal', headdress='plume', pom='teal',
                    pattern='cloud', hands=('open', 'open'), scale=S, name='captain')
mate = sp.figure(robe='red', trim='black', accent='ochre', trousers='green', headdress='crown', pom='teal',
                 pattern='flower', hands=('open', 'open'), scale=S, name='mate')
leaper = sp.figure(robe='teal', trim='black', accent='ochre', trousers='red', headdress='plume', plume='ochre', pom='red',
                   pattern='cloud', hands=('open', 'open'), scale=S, name='leaper')
pointer = sp.figure(robe='teal', trim='black', accent='ochre', trousers='ochre', headdress='crown', face='solid',
                    facedye='red', pom='red', pattern='flower', hands=('open', 'fist'), scale=S, name='pointer')
for p in (captain, mate, leaper, pointer):
    p.rod('torso', (4, -128), lean=-10)
    p.rod('hand_f', (0, 16), lean=30)
    p.rod('hand_b', (0, 16), lean=-30)
tick('figures')

# final poses (angles counter-clockwise as seen facing right; leaper and pointer are flipped to face left)
FINAL = {
    captain: dict(x=612, flip=False, rot=10, d=0.0, ground='shin_b',
                  angles=dict(torso=6, head=8, thigh_f=122, shin_f=-8, thigh_b=-12, shin_b=-4,
                              arm_f=-64, fore_f=34, hand_f=10, arm_b=74, fore_b=30)),
    mate: dict(x=262, flip=False, rot=0, d=0.0, ground='shin_b',
               angles=dict(torso=-3, head=12, thigh_f=82, shin_f=-100, thigh_b=-4,
                           arm_b=-112, fore_b=-18, hand_b=-14, arm_f=48, fore_f=24, hand_f=-26)),
    leaper: dict(x=1338, flip=True, rot=-4, d=0.05, lift=58,
                 angles=dict(torso=-2, head=22, thigh_f=78, shin_f=-104, thigh_b=-26, shin_b=-56,
                             arm_f=147, fore_f=16, hand_f=8, arm_b=128, fore_b=24)),
    pointer: dict(x=1648, flip=True, rot=-5, d=0.0, ground='shin_b',
                  angles=dict(torso=-4, head=10, thigh_f=30, shin_f=-34, thigh_b=-30, shin_b=-4,
                              arm_f=122, fore_f=16, arm_b=-58, fore_b=72)),
}


def set_final(p):
    f = FINAL[p]
    sp.place(p, x=f['x'], y=600, rot=f['rot'], d=f['d'], flip=f['flip'], **f['angles'])
    if 'ground' in f: p.ground(FLOOR, [f['ground']])
    else: p.ground(FLOOR - f['lift'])
    return p.state()


sp.place(border, 0, 0)
sp.place(gate, W / 2, FLOOR)
EYE = (W / 2, FLOOR - 392)
sp.place(ball, EYE[0] + 10, EYE[1] - 2, rot=-20)
finals = {p: set_final(p) for p in (captain, mate, leaper, pointer)}
sp.place(plate, captain.point('head', (0, -60))[0] + 6, sp.box[1] + 4)
sp.place(plate2, leaper.point('head', (0, -60))[0] + 10, sp.box[1] + 4)
tick('placed')

if stages:
    # ================================================================= the draw-on: real in-between poses.
    # Stage names carry the GIF timing: '~' = a motion frame (shown as is, no cross-fade), '@ms' = how long it stays.
    ease_out = lambda t: 1 - (1 - t) ** 3
    ease = lambda t: t * t * (3 - 2 * t)

    def back(t, s=1.6):
        t = t - 1
        return 1 + t * t * ((s + 1) * t + s)

    keep = {p: p.state() for p in sp.items}
    for p in list(sp.items): sp.hide(p)
    for ln in lanterns: ln.set(lit=0.0, swing=0.0)

    # ---- in the dark, the lamp is lit behind the screen: a small glow that spreads, flickering
    sp.frame(dy=-560); sp.lamp(0.0, 0.08)
    sp.stage('dark@700')
    for i, (rad, lv, fl) in enumerate(((0.07, 0.35, 0.0), (0.11, 0.55, 0.10), (0.17, 0.62, -0.08), (0.28, 0.8, 0.05),
                                       (0.50, 0.92, -0.03))):
        sp.lamp(lv, rad, fl); sp.stage(f'lamp~{i}@{160 if i < 3 else 120}')
    sp.lamp(1.0, 1.0); sp.stage('lit@600')

    # ---- the lintel drops in with the lanterns, which swing and light
    for i, dy in enumerate((-430, -270, -120, -14, 12, -4)):
        sp.frame(dy=dy)
        for j, ln in enumerate(lanterns): ln.set(swing=(0, 0, 0, 2, 7, -5)[i] * (1 if j == 0 else -1))
        sp.stage(f'frame~{i}@60')
    sp.frame(dy=0)
    for i, (lt, sw) in enumerate(((0.25, 3.5), (0.6, -2.5), (0.9, 1.4), (1.0, -0.5))):
        for j, ln in enumerate(lanterns): ln.set(lit=lt, swing=sw * (1 if j == 0 else -1))
        sp.stage(f'lantern~{i}@90')
    for ln in lanterns: ln.set(swing=0.0)
    sp.stage('frame@600')

    # ---- the floor band and the goal come up from below, pressed to the cloth as they arrive
    for i, t in enumerate((0.3, 0.6, 0.85, 1.0)):
        u = ease_out(t)
        sp.place(border, x=0, y=74 * (1 - u), d=0.45 * (1 - u))
        sp.stage(f'border~{i}@60')
    gs = keep[gate]
    for i, t in enumerate((0.18, 0.36, 0.54, 0.72, 0.88, 1.0)):
        sp.place(gate, x=gs['x'], y=gs['y'] + 640 * (1 - back(t, 1.1)), d=0.6 * (1 - t) ** 1.3)
        sp.stage(f'gate~{i}@70')
    sp.stage('gate@500')

    # ---- the players slide in from the wings, far from the cloth (soft, doubled) and pressed flat as they arrive
    READY = dict(torso=2, head=4, thigh_f=8, shin_f=-6, thigh_b=-8, shin_b=-2, arm_f=28, fore_f=38, hand_f=0,
                 arm_b=-22, fore_b=30, hand_b=0)
    ready = {}
    for p in (captain, mate, leaper, pointer):
        sp.place(p, x=finals[p]['x'], y=600, rot=0, d=0.0, **READY); p.ground(FLOOR)
        ready[p] = p.state()
    start = {captain: -300, mate: -560, leaper: W + 300, pointer: W + 560}
    n = 8
    for i in range(1, n + 1):
        t = i / n; u = ease_out(t); ph = i * 1.4
        for p in (captain, mate, leaper, pointer):
            sw = np.sin(ph + (0.8 if p in (mate, pointer) else 0)) * (1 - t) ** 0.6
            ang = dict(READY, thigh_f=READY['thigh_f'] + 30 * sw, thigh_b=READY['thigh_b'] - 30 * sw,
                       shin_f=-6 - 24 * max(0.0, -sw), shin_b=-2 - 24 * max(0.0, sw),
                       arm_f=READY['arm_f'] - 26 * sw, arm_b=READY['arm_b'] + 26 * sw)
            x = start[p] + (ready[p]['x'] - start[p]) * u
            sp.place(p, x=x, y=600, rot=-4 * (1 - t), d=0.72 * (1 - t) ** 1.4, **ang); p.ground(FLOOR)
        sp.stage(f'enter~{i}@70')
    for p in (captain, mate, leaper, pointer): sp.place(p); p.load(ready[p])
    sp.stage('ready@500')

    # ---- the mate passes: a flick of the foot, the ball arcs over to the captain
    def bez(p0, p1, p2, t):
        return [(1 - t) ** 2 * a + 2 * (1 - t) * t * b + t * t * c for a, b, c in zip(p0, p1, p2)]

    flick = (24, 52, 30, 14, 8)
    toe = lambda p: p.point('shin_f', (34, 100))
    for i, th in enumerate(flick):
        mate.pose(thigh_f=th, shin_f=-6 - 0.3 * th); mate.ground(FLOOR, ['shin_b'])
        if i >= 1:
            t = i / (len(flick) - 1)
            bx, by = bez((420, 840), (520, 560), (700, 820), t)
            sp.place(ball, x=bx, y=by, rot=-50 * i, d=0.0)
        sp.stage(f'pass~{i}@70')

    # ---- the captain winds up and kicks; the ball flies through the eye. The leaper jumps for it, the pointer
    #      points, the mate swings into his pose
    for i, (th, rt) in enumerate(((-22, -4), (-34, -6))):
        captain.pose(thigh_f=th, shin_f=-30, arm_f=40, arm_b=-40, torso=-4); captain.set(rot=rt); captain.ground(FLOOR, ['shin_b'])
        sp.place(ball, x=700 + 10 * i, y=840 + 20 * i, rot=-150 - 30 * i)
        sp.stage(f'wind~{i}@{90 if i else 70}')
    capf = finals[captain]
    others = (mate, leaper, pointer)
    ball_from = None
    nk = 7
    for i in range(1, nk + 1):
        tk = min(1.0, i / 3)                     # the kick is over in three frames, the ball keeps flying
        captain.load(Puppet.tween(ready[captain], capf, ease_out(tk)))
        if i == 1:
            captain.pose(thigh_f=60, shin_f=-20)
        captain.ground(FLOOR, ['shin_b'])
        if i == 1: ball_from = toe(captain)
        tb = (i - 1) / (nk - 1)
        bx, by = bez(ball_from, (870, 430), (EYE[0] + 10, EYE[1] - 2), ease(tb) * 0.6 + tb * 0.4)
        sp.place(ball, x=bx, y=by, rot=-200 - 45 * i)
        to = max(0.0, (i - 2) / (nk - 2))
        for p in others:
            p.load(Puppet.tween(ready[p], finals[p], ease_out(to)))
            sp.place(p)
        sp.stage(f'kick~{i}@{70 if i < nk else 120}')

    # ---- 亮相: everyone snaps into the final pose with a small overshoot, and holds
    for i, t in enumerate((0.55, 0.85)):
        for p in (captain, mate, leaper, pointer):
            p.load(Puppet.tween(ready[p], finals[p], back(t, 2.2)))
        sp.stage(f'pose~{i}@70')
    for p in (captain, mate, leaper, pointer): p.load(finals[p])
    sp.place(ball, x=EYE[0] + 10, y=EYE[1] - 2, rot=-20)
    sp.stage('liangxiang@1100')

    # ---- the name plaques come down on their threads
    for i, t in enumerate((0.35, 0.7, 0.92, 1.0)):
        for pl in (plate, plate2):
            st = keep[pl]
            sp.place(pl, x=st['x'], y=st['y'] - 170 * (1 - back(t, 1.4)))
        sp.stage(f'plates~{i}@70')

    # ---- the lamp gutters once, then the final frame
    sp.lamp(0.93, 1.0, -0.05); sp.stage('flicker~@110')
    sp.lamp(1.0, 1.0)
    for p, st in keep.items(): sp.place(p); p.load(st)

img = sp.save(out, stages_dir=stages)
tick('saved')
print('saved', out)
