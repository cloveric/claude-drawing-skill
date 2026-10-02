"""Example (green-screen CRT terminal / 绿屏终端): 今天带伞吗 · Bring an Umbrella? -- a forecast typed into a 1980s
video terminal. Someone at a little harbour weather station asks the terminal for today's forecast and the answer
comes back as ASCII art in glowing P1 phosphor: the day drawn from left to right as one strip over an hour axis --
a low morning sun with its rays, fair-weather cumulus, a storm cloud raining on the town from 14:00 to 17:30, the
sky clearing, a crescent moon, lit windows and a lighthouse beam at night -- then a temperature curve plotted with
the terminal's scan-line bars, rain bars in block eighths, a summary, and the answer: YES, after 14:00.
The tube: scan lines, blooming bold characters, halation, a barrel-curved raster, afterglow trails behind the falling
rain, a double-height headline, a reverse-video status line with an older one burnt into the phosphor; a putty
plastic bezel whose chamfer catches the green glow, a power LED and two thumbwheels.
Draw-on stages: screen off -> power on -> command typed -> header -> the picture streams in row by row -> curve ->
rain bars and axis -> summary and answer. No image model.
python3 crt_weather.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from crt import CRTTerminal

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'crt_weather.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

COLS, ROWS = 120, 36
t = CRTTerminal(1920, 1080, seed=11, cols=COLS, rows=ROWS)
ASP = t.cw / t.ch                                  # a column is this many rows wide


def X(h):
    """hour of the day -> column (06:00 at column 6, 24:00 at column 114)"""
    return 6 + (h - 6) * 6.0


# ================================================================ the picture (hidden art map, rows 5-20)
TOP, GROUND = 5, 19.4

# ---- morning: a low sun -- bright core, faint corona, long and short rays above the horizon
t.material('corona', [' ', ' ', ' ', '.', ':'], attrs=['dim'] * 5, outline=None, dither=0.06)
t.material('sun', [' ', '.', ':', '+', '*', '%', '#', '@'],
           attrs=['dim', 'dim', 'normal', 'normal', 'bold', 'bold', 'bold', 'bold'], outline='cloud', edge=1.0, dither=0.10)
t.material('ray', ['.'], edge=0.70)
sx, sy, sr = X(8.6), 12.4, 5.4
t.fill(t.circle(sx, sy, sr * 1.6), 'corona', t.radial_tone(sx, sy, sr * 1.6, 1.0, 0.0, 1.6))
for k in range(9):                                 # the rays: only those above the hills
    a = np.radians(180 + k * 22.5)
    r0, r1 = sr * 1.3, sr * (2.05 if k % 2 == 0 else 1.65) * (0.72 if k == 8 else 1.0)
    t.stroke([(sx + r0 * np.cos(a), sy + r0 * np.sin(a) * ASP), (sx + r1 * np.cos(a), sy + r1 * np.sin(a) * ASP)],
             'ray', width=1.4)
t.fill(t.circle(sx, sy, sr), 'sun', t.radial_tone(sx, sy, sr, 1.0, 0.28, 1.0))

# ---- late morning: fair-weather cumulus, lit from the sun on the left
t.material('cumulus', [' ', '.', ':', '.', ':', ':', '*'], attrs=['dim', 'dim', 'dim', 'normal', 'normal', 'bold', 'bold'],
           outline='cloud', dither=0.10)                 # brighter by intensity, not by busier characters
t.puffs([(X(11.05), 11.3, 2.6), (X(11.45), 9.9, 3.4), (X(12.05), 9.3, 3.6), (X(12.55), 10.7, 2.5),
         (X(11.75), 11.6, 3.6)], 'cumulus', light=(-0.85, -0.5, 0.3), amb=0.0, base=13, base_dark=0.5)

# ---- afternoon: the storm -- a towering cloud with an anvil, a dark flat base, rain on the town 14:00-17:30
t.material('storm', [' ', ' ', '.', '.', ':', '.', ':', ':'], attrs=['dim'] * 5 + ['normal', 'normal', 'bold'],
           outline='cloud', dither=0.12)
storm = [(X(13.9), 12.2, 3.2), (X(14.6), 11.0, 3.9), (X(15.3), 9.4, 4.4), (X(15.9), 8.2, 3.8), (X(16.5), 9.2, 4.3),
         (X(17.2), 10.6, 4.0), (X(17.8), 11.8, 3.3), (X(14.7), 12.8, 4.4), (X(15.9), 12.4, 5.0), (X(17.0), 12.8, 4.4),
         (X(18.1), 13.1, 2.6), (X(13.6), 13.6, 2.4), (X(16.0), 13.8, 6.5)]
t.puffs(storm, 'storm', light=(-0.8, -0.55, 0.25), amb=0.0, base=15, base_dark=0.7)
anvil = t.poly([(X(14.9), 7.4), (X(15.5), 5.95), (X(18.6), 5.95), (X(19.3), 6.25), (X(18.2), 6.75), (X(16.9), 7.3),
                (X(16.0), 8.0)])
t.fill(anvil, 'storm', t.ramp_tone((X(15), 6), (X(19), 7), 0.75, 0.35))

# ---- evening: the last ragged cloud breaks up; night: a crescent moon
t.material('wisp', [' ', '.', '-', '~'], attrs=['dim'] * 4, outline=None, dither=0.15)
for (c, r, w, s) in [(X(18.9), 9.8, 3.6, 0.9), (X(19.6), 11.1, 2.8, 0.6), (X(18.6), 12.4, 2.2, 0.45)]:
    t.fill(t.ellipse(c, r, w, 0.42), 'wisp', s)

t.material('moon', [' ', '.', ':', '*', '%', '#', '@'], attrs=['dim', 'dim', 'normal', 'bold', 'bold', 'bold', 'bold'],
           outline=None, dither=0.05)
mx, my, mr = X(21.6), 9.8, 5.8
t.fill(t.circle(mx, my, mr) * (1 - t.circle(mx + 2.6, my - 0.35, mr * 0.97)), 'moon',
       t.radial_tone(mx - 2.0, my, mr * 1.4, 1.0, 0.6, 0.6))

# ---- the land: flat ground for the town, the sea on the right
t.material('hill', [' ', ' ', ' ', '.', ','], attrs=['dim'] * 5, outline='straight', dither=0.25)
t.fill(t.rect(-1, GROUND, 101, 21.0), 'hill', 0.22)
t.material('sea', [' ', ' ', '-', '~'], attrs=['dim'] * 4, outline=None, dither=0.3)
t.fill(t.rect(101, GROUND + 0.5, 121, 21.0), 'sea', t.ramp_tone((101, 0), (121, 0), 0.65, 0.95))

t.compose(region=(TOP, 21, 0, COLS))

# ---- hand-drawn pieces on top of the composed art
rng = np.random.default_rng(4)
for c, r, ch, a in [(2, 6, '.', 'dim'), (5, 8, '·', 'dim'), (9, 5, '.', 'dim'), (13, 7, '·', 'dim'),
                    (84, 6, '.', 'dim'), (88, 12, '·', 'dim'), (91, 7, '*', 'normal'), (94, 10, '.', 'dim'),
                    (90, 5, '+', 'normal'), (99, 16, '·', 'dim'), (110, 5, '*', 'bold'), (108, 12, '.', 'dim'),
                    (111, 9, '+', 'normal'), (114, 5, '.', 'dim'), (116, 11, '*', 'normal'), (118, 7, '·', 'dim'),
                    (103, 15, '.', 'dim'), (86, 15, '·', 'dim')]:
    t.put(c, r, ch, a)

# houses along the ground: dark windows by day, lit ones after dusk; the lighthouse on its rock, beam sweeping
H1 = ['  /\\  ', ' /  \\ ', '/____\\', '|o  o|']
H2 = [' ____ ', '/____\\', '|o  o|']
H3 = ['   _||_ ', '  /    \\', ' /______\\', ' |o [] o|']
H4 = [' ___ ', '/___\\', '|o o|']
TREE = [' .:. ', '(:::)', '  |  ']
for c0, spr in [(30, TREE), (35, H1), (43, H4), (52, H3), (62, H2), (69, TREE), (74, H1), (84, H4), (90, H3),
                (99, TREE)]:
    night = c0 >= 82
    t.sprite(c0, 20 - len(spr), spr, 'dim', attrs={'o': 'bold' if night else 'dim', '[': 'normal', ']': 'normal'},
             swap={'o': '#' if night else '.'})
LH = ['  _  ', ' [@] ', ' |=| ', ' | | ', ' |=| ', '/___\\']
t.sprite(110, 20 - len(LH), LH, 'normal', attrs={'@': 'bold'})
lr = 20 - len(LH) + 1
for k, (c, ch) in enumerate([(109, '-'), (108, '='), (107, '-'), (106, '='), (105, '-'), (104, '-'), (102, '-'), (100, '.')]):
    t.put(c, lr, ch, 'bold' if k < 3 else 'normal' if k < 6 else 'dim')
for c, ch in [(107, '.'), (105, "'"), (102, '.')]:
    t.put(c, lr - 1, ch, 'dim')
for c, ch in [(107, "'"), (105, '.'), (102, "'")]:
    t.put(c, lr + 1, ch, 'dim')

# rain: streaks from the cloud base down to the roofs; each drop leaves the afterglow of where it was a frame ago
RAIN = []
for c in range(int(X(14.0)), int(X(17.7))):
    dens = float(np.interp(c, [X(14.0), X(14.8), X(15.6), X(16.6), X(17.3), X(17.7)], [0.15, 0.55, 0.75, 0.7, 0.4, 0.1]))
    for r in range(15, 18):
        if not t.art_text[r, c] and rng.random() < dens * 0.5:      # not over the roofs
            RAIN.append((c, r))
# a lightning bolt out of the base at about 16:10 (no rain, and no afterglow, right next to it)
BOLT = [(66, 15, '/'), (65, 16, '/'), (66, 16, '_'), (66, 17, '/'), (65, 18, '/')]
near = {(c + dc, r + dr) for c, r, _ in BOLT for dc in (-1, 0, 1) for dr in (-1, 0, 1)}
RAIN = [(c, r) for c, r in RAIN if (c, r) not in near]
for c, r in RAIN:
    t.put(c, r, '/', 'normal')
for c, r, ch in BOLT:
    t.put(c, r, ch, 'bold')

# ================================================================ the session
t.stage('off')
t.power()
t.stage('power')

t.write(0, 0, 'wx@lookout:~$ ', 'bold')
t.write(14, 0, 'forecast --town "port wren" --today --art', 'normal')
t.cursor(56, 0)
t.stage('command')

t.big(0, 1, 'PORT WREN  THU 14 OCT', 'bold')
t.write(0, 3, 'harbour station 07   sunrise 07:21   sunset 18:24   wind SW 24 km/h   model run 06Z', 'dim')
t.box(1, 4, 118, 31, attr='dim', title='TODAY  06-24h')
t.cursor(0, 32)
t.stage('header')

t.reveal(TOP, 12)
t.stage('picture_top')
t.reveal(12, 20)
for c, r in RAIN:                                  # the drops one and two frames back, still glowing
    t.trail(c + 1, r - 1, '/', 0.32)
    t.trail(c + 2, r - 2, '/', 0.10)
t.stage('picture')

# temperature: a curve of scan-line bars (5 heights per row)
HOURS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
TEMP = [9.0, 9.1, 9.8, 11.2, 12.8, 14.6, 16.1, 17.0, 16.3, 13.4, 12.2, 12.3, 12.8, 12.4, 11.7, 11.1, 10.6, 10.2, 10.0]
xs = np.linspace(6, 24, 400)
ys = np.interp(xs, HOURS, TEMP)
ys = np.convolve(np.pad(ys, 6, mode='edge'), np.ones(13) / 13, mode='valid')     # a smooth curve
at = t.plot(X(6), 22, 108, 5, xs, ys, (6, 24), (8, 18), attr='bold')
for v in (16, 12, 8):
    c, r = at(6, v)
    t.write(2, int(round(r)), '%2d°' % v, 'dim')
c, r = at(13, 17.0)
t.write(int(c) + 2, int(round(r)), '17°', 'bold')
t.stage('curve')

# rain: block-eighth bars, mm per hour
rate_h = [13.9, 14.2, 14.8, 15.5, 16.2, 16.8, 17.3, 17.65]
rate_v = [0.0, 0.6, 1.6, 2.6, 2.4, 1.5, 0.6, 0.0]
vals = [float(np.interp(6 + (c + 0.5 - X(6)) / 6.0, rate_h, rate_v)) for c in range(int(X(6)), int(X(24)))]
t.bars(int(X(6)), 27, 2, vals, 3.0, 'dim')
t.write(2, 28, 'mm', 'dim')
t.write(int(X(17.8)), 28, '6.4 mm', 'normal')
# the hour axis
t.hline(int(X(6)), int(X(24)), 29, 'dim')
for h in range(6, 25, 3):
    c = int(round(X(h)))
    t.write(c, 29, '┴', 'dim')
    t.write(c - 1, 30, '%02d' % h, 'normal')
t.stage('bars')

t.write(0, 32, 'max 17° 13:00   min 9° 06:00   rain 6.4 mm 14:00-17:30   thunder 30%   gusts 50 km/h 15:00', 'normal')
t.write(0, 33, 'umbrella? ', 'bold')
t.write(10, 33, ' YES ', 'bold+rev')
t.write(16, 33, ' after 14:00 -- dry again by 18:00', 'bold')
t.write(0, 34, 'wx@lookout:~$ ', 'bold')
t.write(14, 34, 'forecast --tomorrow', 'normal')
t.cursor(33, 34)
t.write(0, 35, (' lookout   9600 8N1   ONLINE   LOCAL 06:12').ljust(COLS - 9) + 'F1 help  ', 'dim+rev')
t.burn(58, 35, 'SESSION 01   LINE 2   READY', 0.22)               # an old status line, years in the phosphor
t.tear(9.7, 5.0, 2)                                # a two-line horizontal-sync slip through the clouds

t.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s')
