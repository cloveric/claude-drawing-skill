"""Example (ASCII art, 1970s line printer): Liftoff Trace / 发射记录 — sheet 2 of a launch report, a whole 8.5 in
greenbar sheet lying on the desk between two tear lines. On the left, an ASCII picture of the moment of liftoff: a
slender rocket with a roll pattern rising beside its lattice service tower (arms swung back, an umbilical hose still
swinging), a white-hot column widening from the nozzle (! | ' . streaks inside a % @ # smoke sheath) that runs
into rolling exhaust clouds shaded % -> @ -> # with overstruck cores, a limb-darkened sun and a V of birds. On the
right, what the computer logged: the countdown events and a printer plot of altitude against time (planned
'.' vs measured '*', X = this picture). A reader went over it with a red ballpoint. No image model.
python3 lineprinter_launch.py [out.jpg] [--stages DIR] [--txt]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from lineprinter import LinePrinter
from core import smoothstep

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'lineprinter_launch.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

lp = LinePrinter(1920, 1080, seed=7, top=14, ppi=123.8, page_in=8.5)   # a whole 8.5 in sheet, tear line to tear line
BOTTOM = lp.page_rows - 2       # the picture stops two lines above the next tear line
rng = np.random.default_rng(7)
lp.form()
lp.stage('form')

# ------------------------------------------------------------------ roles: which characters each thing is made of
lp.role('hull', ['', '.', ':', '+', '%', '#', '#@'], dither=0.35, group='rocket')
lp.role('paint', ['#@', '#@', '#@M'], dither=0.0, noise=0.0, group='rocket')
lp.role('metal', ['', '=', '=', '#', '#='], dither=0.3, group='rocket')
lp.role('plume', ['', '.', ':', '%', '@', '#'], edge=None, dither=0.2, noise=0.0, group='rocket')
lp.role('core', ['', "'", '.', ':', '!', '|'], edge=None, dither=0.0, noise=0.0, group='rocket')
lp.role('smoke', ['', '.', ':', '%', '@', '#', '#@'], edge='all', outline='round', dither=0.2, noise=0.0,
        inner_max=0.5)
lp.role('land', ['', '.', ',', ':'], edge=None, dither=0.9, noise=0.06)
lp.role('sun', ['', '.', '.', ':', ':'], outline=dict(left='(', right=')', top='_'), dither=0.7, noise=0.03)
lp.role('tank', ['', '.', ':', '%', '#'], outline=dict(left='(', right=')', top='_'), dither=0.3)

CX = 44.0                       # rocket axis (column)
H0, NB, BASE = 3.0, 11.0, 30.4  # nose tip, nose base, body base (rows)
R = 4.8                         # body radius in columns
GROUND = 42.5

lp.fill(lp.rect(0, GROUND, 94, lp.rows), 'land', lp.ramp_tone((0, GROUND), (0, lp.rows), 0.15, 0.5))
lp.stroke([(0, GROUND), (94, GROUND)], glyphs='_')

# ------------------------------------------------------------------ a water tower further off (deluge water for the pad)
WX, WY, WR = 81.5, 27.0, 4.2
for x0, x1 in ((WX - 2.6, WX - 5.6), (WX + 2.6, WX + 5.6), (WX - 0.9, WX - 1.9), (WX + 0.9, WX + 1.9)):
    lp.stroke([(x0, WY + 1.5), (x1, GROUND)])
for yb in (32.5, 37.5):                                              # braces on a row centre, or they split in two
    k = (yb - WY - 1.5) / (GROUND - WY - 1.5)
    lp.stroke([(WX - 2.6 - 3.0 * k, yb), (WX + 2.6 + 3.0 * k, yb)], glyphs='-')
lp.fill(lp.circle(WX, WY, WR), 'tank', lp.sphere_tone(WX, WY, WR, (-0.6, -0.5, 0.6), amb=0.1) * 0.9)
lp.stroke([(WX, WY - WR * lp.cw / lp.ch - 0.2), (WX, WY - WR * lp.cw / lp.ch - 1.6)], glyphs='|')

# ------------------------------------------------------------------ the service tower (behind the rocket)
TL, TW, TT = 58.5, 6, 8.0       # left leg (cell centre), width in columns, top row
TR = TL + TW
lp.stroke([(TL, TT), (TL, GROUND)])
lp.stroke([(TR, TT), (TR, GROUND)])
lp.stroke([(TL - 0.5, TT + 0.5), (TR + 0.5, TT + 0.5)], glyphs='=')
y = TT + 1                        # bays: braces go one column per row, so each cell gets one clean \ or /
while y + TW < GROUND:
    lp.stroke([(TL + 0.5, y), (TR - 0.5, y + TW - 1)])        # crossing lands in a cell centre -> X
    lp.stroke([(TR - 0.5, y), (TL + 0.5, y + TW - 1)])
    lp.stroke([(TL - 0.5, y + TW - 0.5), (TR + 0.5, y + TW - 0.5)], glyphs='=')
    y += TW
# crane jib and hook, mast, warning light
lp.stroke([(TL - 5, TT - 0.5), (TR + 2, TT - 0.5)], glyphs='=')
lp.stroke([(TL - 4.0, TT), (TL - 4.0, TT + 2.5)], glyphs='|')
lp.text('J', int(TL - 4.0), int(TT + 2.6))
lp.stroke([((TL + TR) / 2, TT - 4.2), ((TL + TR) / 2, TT - 0.8)], glyphs='|')
lp.text('O', int((TL + TR) / 2), int(TT - 5), strike=2)
# swing arms, retracted; one umbilical hose still swinging
for ya in (15.5, 25.5):
    lp.stroke([(TL - 3.5, ya), (TL - 0.5, ya)], glyphs='=')
lp.stroke([(TL - 3.4, 16.0), (TL - 4.4, 18.0), (TL - 3.6, 20.0), (TL - 1.8, 21.2)], smooth=True)

# ------------------------------------------------------------------ the rocket
body_light = (-0.7, -0.15, 0.7)
sv = np.linspace(0, 1, 40)                                           # ogive nose: half-width grows like a bullet
half = R * (2 * sv - sv * sv)
nose = lp.poly([(CX + h, H0 + s_ * (NB - H0)) for s_, h in zip(sv, half)] + [(CX + R, NB + 0.3), (CX - R, NB + 0.3)]
               + [(CX - h, H0 + s_ * (NB - H0)) for s_, h in zip(sv[::-1], half[::-1])])
body = lp.rect(CX - R, NB, CX + R, BASE)
tone = lp.cylinder_tone(CX - R, CX + R, body_light, amb=0.12)
for sgn in (-1, 1):                                                  # fins first so the body covers their roots
    fin = lp.poly([(CX + sgn * (R - 0.4), BASE - 6.0), (CX + sgn * (R + 3.6), BASE + 0.2),
                   (CX + sgn * (R + 3.6), BASE + 0.9), (CX + sgn * (R - 0.4), BASE + 0.9)])
    lp.fill(fin, 'hull', 0.15 if sgn < 0 else 0.75)
lp.fill(np.maximum(nose, body), 'hull', tone)
for (r0, r1, side) in ((12.6, 16.0, -1), (16.0, 19.4, 1)):       # roll pattern: black quarters
    q = lp.rect(CX if side > 0 else CX - R, r0, CX + R if side > 0 else CX, r1)
    lp.fill(q * body, 'paint', tone)
lp.fill(lp.rect(CX - R, 22.4, CX + R, 23.4), 'metal', np.clip(tone + 0.3, 0, 1))
lp.text_v('LARK', int(CX - 2), 24, strike=2)                         # painted name, on the sunlit side

# ------------------------------------------------------------------ the flame: a hot white column widening from the nozzle
FT, FB = BASE, 46.0
ys = np.linspace(FT, FB, 40)
hw = 2.6 + 5.0 * np.clip((ys - FT) / 9.0, 0, 1) ** 0.8 + 0.3 * np.maximum(ys - FT - 9.0, 0)   # half-width (columns)
hw_at = np.interp(lp.Y, ys, hw)
u = np.abs(lp.X - CX) / hw_at                                         # 0 on the axis .. 1 at the plume's edge
plume = lp.poly([(CX + h, y_) for y_, h in zip(ys, hw)] + [(CX - h, y_) for y_, h in zip(ys[::-1], hw[::-1])])
lp.fill(plume, 'plume', np.clip(0.2 + 0.95 * smoothstep(0.45, 1.0, u), 0, 1))  # smoke sheath, thickening outwards
# white-hot inside: streaks that fan out from the nozzle, flickering along their length
d = lp.Y - FT
lanes = np.zeros_like(lp.X)
for off, k, amp in ((-0.5, 0.0, 1.0), (0.5, 0.0, 1.0), (-1.5, 0.18, 0.75), (1.5, 0.18, 0.75), (-2.6, 0.3, 0.5), (2.6, 0.3, 0.5)):
    xc = CX + off * (1 + k * d)
    flick = 0.62 + 0.38 * np.sin(d * 1.9 + off * 2.1)
    lanes = np.maximum(lanes, amp * flick * np.exp(-((lp.X - xc) / 0.42) ** 2))
inner = lp.poly([(CX + 0.6 * h, y_) for y_, h in zip(ys, hw)] + [(CX - 0.6 * h, y_) for y_, h in zip(ys[::-1], hw[::-1])])
lp.fill(inner, 'core', np.clip(1.6 * lanes * (1.0 - 0.55 * np.clip(d / 10.0, 0, 1)), 0, 1))

# ------------------------------------------------------------------ exhaust clouds rolling out both ways
puffs = [(CX - 9.6, 39.6, 3.6), (CX + 9.6, 39.8, 3.6)]                               # smoke peeling off the plume
puffs += [(CX - 14, 39.5, 7.0), (CX + 14, 40.0, 7.0),                                # back, high
         (CX - 29, 42.0, 8.0), (CX + 28, 42.5, 7.5), (CX - 13.5, 44.0, 7.0), (CX + 13.5, 44.0, 7.0),
         (CX - 39, 45.5, 6.0), (CX + 38, 46.0, 5.5),                                  # rolling out sideways
         (CX - 20, 47.0, 10.0), (CX + 19, 47.5, 9.5),                                 # front, on the pad
         (CX - 35, 50.5, 8.5), (CX + 34, 51.0, 8.0), (CX, 49.5, 10.0)]
puffs = [(c + rng.uniform(-0.8, 0.8), r + rng.uniform(-0.3, 0.3), R_ * rng.uniform(0.95, 1.05)) for c, r, R_ in puffs]
sink = 0.32 * np.clip((lp.Y - 41.0) / 8.0, 0, 1)                    # the cloud's underside is in its own shade
lp.billow(puffs, 'smoke', light=(-0.35, -0.85, 0.4), amb=0.2, shadow=0.3, glow=(CX, 42.5, 8.0, 0.3), lift=sink)

# ------------------------------------------------------------------ the low morning sun the light comes from
SC, SR, SRAD = 15.5, 9.5, 4.6
rr = np.hypot(lp.X - SC, (lp.Y - SR) * lp.ch / lp.cw) / SRAD         # limb darkening: . in the middle, : at the rim
lp.fill(lp.circle(SC, SR, SRAD), 'sun', np.clip(0.28 + 0.75 * rr ** 1.6, 0, 1))
for k in range(8):
    a = k / 8 * 2 * np.pi
    ca, sa = np.cos(a), np.sin(a) * lp.cw / lp.ch
    r0, r1 = SRAD + 1.0, SRAD + 3.0
    lp.stroke([(SC + ca * r0, SR + sa * r0), (SC + ca * r1, SR + sa * r1)])

# ------------------------------------------------------------------ birds leaving in a hurry
for (c, r) in [(23, 16), (26, 15), (29, 14), (32, 13), (26, 17), (29, 18), (35, 15)]:   # a loose V heading off left
    lp.text('\\/', c, r)

# ------------------------------------------------------------------ header and the right-hand column
lp.text('LARK-7  ASCENT TRACE', 0, 1, strike=2)
lp.text('PAD 2      JOB 4471   74.103  06:41:10      LP02', 38, 1)
lp.text('SHEET  2', 124, 1)
L0 = 97
lp.text('EVENT LOG', L0, 4, strike=2)
lp.text('-' * 35, L0, 5)
events = [('T-00:10', 'GUIDANCE', 'INTERNAL'), ('T-00:05', 'IGNITION', 'START'), ('T-00:02', 'MAIN STAGE', '100 PCT'),
          ('T+00:00', 'HOLD-DOWN', 'RELEASE'), ('T+00:01', 'LIFTOFF', '06:41:07'), ('T+00:03', 'CLEARING TOWER', '11 M')]
for i, (t, ev, val) in enumerate(events + [('T+00:06', 'TOWER CLEAR', 'NEXT')]):
    lp.text(f'{t}  {ev} ' + '.' * (16 - len(ev)) + f' {val}', L0, 6 + i)

lp.text('ALTITUDE (M)', L0, 15, strike=2)
lp.text('* MEASURED  . PLAN', L0 + 17, 15)
tt = np.linspace(0, 6, 49)
plan = 0.5 * 2.4 * tt ** 2
tm = np.linspace(0, 3, 13)
meas = 0.5 * 2.45 * tm ** 2 + np.array([0, .1, -.1, .2, 0, -.2, .1, .3, 0, .2, .4, .2, 0])
cell = lp.plot(L0, 17, 25, 13, (0, 6), (0, 40), [(tt, plan, '.'), (tm[:-1], meas[:-1], '*'), (tm[-1:], meas[-1:], 'X')],
               xticks=[0, 1, 2, 3, 4, 5, 6], yticks=[0, 10, 20, 30, 40], ylab_w=4)
lp.text('T+ SECONDS', L0 + 21, 32)
stat = [('CHANNEL', 'VALUE', 'LIMIT', ''), ('THRUST PCT', '101.2', '95.0', 'OK'), ('CHAMBER P', '48.7', '45.0', 'OK'),
        ('ROLL DEG', '+0.4', '2.0', 'OK'), ('PITCH DEG', '-0.1', '2.0', 'OK'), ('VIBRATION G', '1.8', '3.5', 'OK')]
for i, (a, b, c, d) in enumerate(stat):
    lp.text(f'{a:<12}{b:>6}{c:>8}   {d}', L0, 36 + i, strike=2 if i == 0 else 1)
lp.text('ALL CHANNELS WITHIN LIMITS', L0, 43)

lp.erase(lp.rect(0, BOTTOM, lp.cols, lp.rows))                     # bottom margin and the next sheet stay blank
lp.compose()
if '--txt' in sys.argv: lp.listing(os.path.splitext(out)[0] + '.txt')

# ------------------------------------------------------------------ print, a few lines at a time
for r0, r1, name in ((0, 8, 'print_header'), (8, 16, 'print_tower_top'), (16, 24, 'print_body'),
                     (24, 32, 'print_fins'), (32, 40, 'print_flame'), (40, lp.rows, 'print_clouds')):
    lp.print_rows(r0, r1)
    lp.stage(name)

# ------------------------------------------------------------------ somebody read it with a red ballpoint
RED = '#b3312b'
for i in range(6):
    x, y = lp.xy(L0 - 1.2, 6 + i + 0.8)
    lp.tick(x, y, size=13, colour=RED, width=1.4)
cx, cy = lp.centre(*[int(round(v)) for v in cell(3, meas[-1])])
lp.ring(cx, cy, 30, 20, colour=RED, width=1.5)
lp.pen([(cx + 26, cy - 14), (cx + 60, cy - 46), (cx + 95, cy - 58)], colour=RED, width=1.4)
lp.pen_text('on plan', cx + 100, cy - 52, size=24, colour=RED, rot=6)

lp.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
