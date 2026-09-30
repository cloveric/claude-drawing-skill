"""Example (shape morph): 一滴水的旅程 / A Drop's Round Trip — the water cycle told by one outline.
A single 256-point outline turns into six things in a row -- a drop, a cloud, a snowflake, a snowy peak, a river,
a breaking wave -- and the background colour switches with it. The poster freezes the animation like a film
strip: six flat colour panels, the solid keyframe in each, onion-skin ghosts of the in-between frames (bunched
near the keys, spread out in the middle because of the easing), squash & stretch in the fast middle, a dashed
motion path through the centroids, the resampled points dotted on every middle frame, and an animation timeline
underneath with keyframe diamonds and the ease curve of every transition. No image model.
python3 morph_water_cycle.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from morph import Morph, INK

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'morph_water_cycle.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

PAPER, CREAM, BLUE = '#efe9dd', '#f4efe4', '#2437d6'
m = Morph(1920, 1080, seed=6)
m.paper(PAPER)

Y0, Y1, PW = 300, 780, 320                              # the film strip: six panels, 320 px each
EASE = 'sine'
U = [0.25, 0.5, 0.75]                                   # frame times of the ghosts (even in time)
# name, label, english, (cx, cy, size), background, shape colour, ink on this background
KEYS = [('drop', '水滴', 'DROP', (160, 540, 180), '#f2b93b', BLUE, INK),
        ('cloud', '云', 'CLOUD', (480, 460, 214), BLUE, CREAM, CREAM),
        ('snowflake', '雪花', 'SNOWFLAKE', (800, 530, 190), '#171a3c', '#ffffff', CREAM),
        ('mountain', '雪山', 'SNOWPACK', (1120, 575, 214), '#ee5a3c', INK, INK),
        ('river', '河', 'RIVER', (1440, 575, 200), '#2e9a68', '#bfe0ff', CREAM),
        ('wave', '海', 'SEA', (1760, 585, 206), '#10707f', CREAM, CREAM)]
VERBS = [('凝结', 'CONDENSE'), ('降雪', 'SNOWFALL'), ('积存', 'SETTLE'), ('融化', 'MELT'), ('入海', 'FLOW')]

outlines = m.chain([m.shape(n, *p) for n, _, _, p, _, _, _ in KEYS])
cents = [m.centroid(P) for P in outlines]
route = m.path(cents, 60)                               # motion path through the centroids
segs = [route[60 * k:60 * (k + 1) + 1] for k in range(len(KEYS) - 1)]


def keyframe(k):
    """the solid shape of keyframe k plus the details that live inside it"""
    name, _, _, (cx, cy, sz), bg, fg, ink = KEYS[k]
    P = outlines[k]
    m.fill(P, fg)
    if name == 'drop':                                  # a highlight on the belly
        a = np.linspace(np.deg2rad(200), np.deg2rad(250), 12)
        m.stroke(np.stack([cx + 0.2 * sz * np.cos(a), cy + 0.15 * sz - 0.2 * sz * np.sin(a)], 1), CREAM, sz * 0.05, 0.9)
    if name == 'mountain':                              # a lighter right flank, snow cap with a zigzag hem
        top = P[np.argmin(P[:, 1])]
        m.fill(P, '#2b2f5a', half=((top[0], top[1]), (top[0] - 60, top[1] + 400)))
        cap = [(top[0], top[1] - 4), (top[0] + 0.14 * sz, top[1] + 0.22 * sz), (top[0] + 0.07 * sz, top[1] + 0.18 * sz),
               (top[0] + 0.01 * sz, top[1] + 0.25 * sz), (top[0] - 0.06 * sz, top[1] + 0.17 * sz),
               (top[0] - 0.12 * sz, top[1] + 0.21 * sz)]
        m.fill(np.array(cap), CREAM, clip=P)
    if name == 'river':                                 # current lines on the water
        for (x0, y0, x1, y1) in [(-0.04, 0.24, 0.1, 0.3), (-0.02, 0.02, 0.07, -0.02), (0.0, -0.24, 0.04, -0.28)]:
            m.stroke([(cx + x0 * sz, cy + y0 * sz), (cx + x1 * sz, cy + y1 * sz)], '#7fb3e6', sz * 0.022, 1.0)


def extras(k):
    """details around keyframe k that are drawn once"""
    name, _, _, (cx, cy, sz), bg, fg, ink = KEYS[k]
    if name == 'drop':                                  # heat shimmer under the drop: it is evaporating
        for dx in (-34, 0, 34):
            y = np.linspace(0, 1, 30)
            m.stroke(np.stack([cx + dx + 6 * np.sin(y * 2 * np.pi * 1.2), cy + 112 + y * 52], 1), ink, 4.5, 0.5)
    if name == 'snowflake':                             # a few flakes still falling
        r = np.random.default_rng(3)
        for _ in range(9):
            x, y = r.uniform(k * PW + 30, (k + 1) * PW - 30), r.uniform(Y0 + 30, Y1 - 90)
            if np.hypot(x - cx, y - cy) > sz * 0.62: m.dot(x, y, r.uniform(3, 6), CREAM, 0.7)
    if name == 'wave':                                  # spray off the lip
        for dx, dy, rr in [(-0.46, -0.3, 7), (-0.5, -0.18, 5), (-0.42, -0.42, 4.5)]:
            m.dot(cx + dx * sz, cy + dy * sz, rr, CREAM, 0.9)


def label(k):
    name, cn, en, _, bg, fg, ink = KEYS[k]
    x = k * PW + 26
    m.text('BG ' + bg.upper(), (k + 1) * PW - 22, Y0 + 36, 12, ink, 'mono', anchor='r', spacing=1.5, alpha=0.7)
    w = m.text(f'{k + 1:02d}', x, Y1 - 26, 17, ink, 'mono_bold')
    m.text(f'/{len(KEYS):02d}', x + w, Y1 - 26, 17, ink, 'mono', alpha=0.55)
    m.text(cn, x + 72, Y1 - 24, 24, ink, 'cjk_bold')
    m.text(en, x + 72 + m.text_width(cn, 24, 'cjk_bold') + 10, Y1 - 26, 12, ink, 'mono', spacing=2.5, alpha=0.75)


def transition(k):
    """onion skin from keyframe k to k+1: ghosts, the sampled points of the middle frame, a path chevron"""
    A, B = outlines[k], outlines[k + 1]
    fa, fb = KEYS[k][5], KEYS[k + 1][5]
    for u in U:
        s = float(m.ease(u, EASE))
        c, d = m.along(segs[k], s)
        G = m.tween(A, B, s, at=c, stretch=0.16 * np.sin(np.pi * s), direction=d)
        mid = u == 0.5
        m.ghost(G, fill=m.mix(fa, fb, s), fill_alpha=0.42 if mid else 0.14, line_alpha=0.75 if mid else 0.42,
                width=2.6 if mid else 2.0)
        if mid: m.points(G, every=8, r=2.8, alpha=0.95)
    c, d = m.along(segs[k], 0.34)
    m.chevron(c[0], c[1], d, 11, None, 2.6, 0.6)


# ---- header
m.fill(np.array([(80, 88), (122, 88), (122, 94), (80, 94)]), BLUE)
m.text('形变动画  ·  SHAPE TWEEN', 136, 97, 17, INK, 'mono_bold', spacing=1.5)
m.text('一滴水的旅程', 74, 196, 84, INK, 'cjk_bold')
m.text('THE ROUND TRIP OF A WATER DROP', 80, 244, 17, INK, 'mono', spacing=4, alpha=0.7)
m.text('同一条轮廓线，256 个点，先后变成六样东西：', 1190, 132, 26, INK, 'cjk')
m.text('蒸发、凝结、降雪、积存、融化，再流回大海。', 1190, 172, 26, INK, 'cjk')
lx = 1192                                               # legend
m.diamond(lx + 8, 226, 8, fill=BLUE, line=INK, width=2)
lx += 40 + m.text('关键帧', lx + 24, 232, 16, INK, 'cjk')
m.outline(m.shape('circle', lx + 10, 226, 20), INK, 2, 0.8)
lx += 44 + m.text('残影', lx + 26, 232, 16, INK, 'cjk')
m.trail(np.array([(lx, 226), (lx + 36, 226)]), INK, 2.2, dash=(8, 6), alpha=0.8)
lx += 62 + m.text('轨迹', lx + 46, 232, 16, INK, 'cjk')
for i in range(4): m.dot(lx + i * 10, 226, 2.6, INK)
m.text('对应点', lx + 46, 232, 16, INK, 'cjk')
m.stage('title')

# ---- the strip, panel by panel
for k in range(len(KEYS)):
    m.panel(k * PW, Y0, (k + 1) * PW, Y1, KEYS[k][4], ink=KEYS[k][6])
    if k > 0:
        m.trail(segs[k - 1], None, 2.2, dash=(9, 9), alpha=0.5)
        transition(k - 1)
        keyframe(k - 1)                                  # the previous key stays on top of its own ghosts
    keyframe(k)
    extras(k)
    label(k)
    m.stage(f'{k + 1:02d}_{KEYS[k][0]}')

# ---- timeline: keyframe diamonds and the ease curve of every transition
TY, TH = 988, 92
m.outline(np.array([(60, TY), (1860, TY)]), INK, 2.0, 0.8, closed=False)
for k in range(len(KEYS)):
    x = k * PW + PW / 2
    if k < len(KEYS) - 1:
        m.ease_curve(x + 26, TY, x + PW - 26, TY - TH, EASE, INK, 2.6, ticks=U, tick_colour=INK)
        cn, en = VERBS[k]
        w = m.text_width(cn, 20, 'cjk_bold') + 8 + m.text_width(en, 12, 'mono', 2)
        m.text(cn, x + PW / 2 - w / 2, 1036, 20, INK, 'cjk_bold')
        m.text(en, x + PW / 2 - w / 2 + m.text_width(cn, 20, 'cjk_bold') + 8, 1034, 12, INK, 'mono', spacing=2, alpha=0.7)
    m.diamond(x, TY, 12, fill=KEYS[k][4], line=INK, width=2.4)
    m.text(f'00:{k * 2:02d}', x, TY + 40, 14, INK, 'mono', anchor='m', alpha=0.7)
a = np.linspace(np.deg2rad(-150), np.deg2rad(150), 40)       # loop back to 01
m.outline(np.stack([1832 + 16 * np.cos(a), TY - 44 - 16 * np.sin(a)], 1), INK, 2.6, closed=False)
m.chevron(1832 + 16 * np.cos(a[-1]), TY - 44 - 16 * np.sin(a[-1]), 240, 9, INK, 2.6, 1.0)
m.text('蒸发 · 回到 01', 1806, TY - 38, 16, INK, 'cjk_bold', anchor='r')
m.text('EASE IN-OUT  ·  3 ONION-SKIN FRAMES PER TRANSITION', 60, TY - TH - 22, 13, INK, 'mono', spacing=2, alpha=0.7)

m.save(out, stages_dir=stages)
print('saved', out)
