"""Example (sunlit greenery): 窗边的座位 · The Window Seat -- a white room full of summer light and a window to the trees.

A 9:16 phone wallpaper in the anime background-painting / digital gouache manner: a tall white-framed window full of
leafy trees and a clean blue sky with one small cumulus, a built-in window seat with a linen cushion, a navy check
pillow, a white one and an orange one, an open book and a cup of tea; a sheer curtain, a potted fig and a trailing
plant hanging from the ceiling; a sun patch with a window cross and leaf shadows on the wall, and the light through
the window falling across the wooden floor, broken by leaf shadows -- sun-bleached whites with warm cream light and
cool blue-grey shade. No outlines, no image model: every leaf is a flat painted shape.
--layout page (1152 x 2048, the wallpaper) or wide (1920 x 1080: the same room laid out 16:9, for the draw-on GIF
and for video); --preset noon (default) or late (the same room in late-afternoon gold, used only for a GIF);
--stages DIR writes a snapshot after each step (blank, sky, far trees, the near tree, the wall and window, the
sun on the wall, the floor, the seat, the light through the window, the plants -- then the final).
python3 sunlitgreen_window_seat.py [out.jpg] [--layout page|wide] [--preset noon|late] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from sunlitgreen import SunlitGreen

# Every layout: canvas, the window box (x0, y0, x1, y1), its columns and transom, the view outside (cloud; far,
# middle and near foliage clumps (cx, cy, rx, ry, shade); the near tree's trunk and limbs), the wall's sun patch,
# curtain, seat, floor, pillows and props, the light patch on the floor, the potted fig, the hanging plant, the stool
# and the foreground plant.
LAYOUTS = {
    'page': dict(
        size=(1152, 2048), win=(300, 150, 1070, 1200), cols=2, transom=0.22, mid_at=0.4,
        cloud=(470, 600, 300, 130),
        far=dict(y=1060, x0=220, step=70, n=13, r=(70, 70)),
        mid=[(380, 930, 140, 120, 0.04), (470, 860, 120, 100, 0), (330, 1030, 150, 110, 0.08), (520, 1010, 150, 110, 0.04),
             (640, 1060, 140, 100, 0.06)],
        trunk=[[(960, 1240), (930, 900), (900, 640), (880, 430)], 70, 34],
        limbs=[[[(915, 760), (800, 640), (700, 560)], 26, 10], [[(895, 560), (1000, 420), (1090, 330)], 22, 9]],
        near=[(860, 330, 200, 150, 0.0), (1010, 250, 170, 140, 0.02), (720, 470, 150, 110, 0.08),
              (990, 560, 170, 140, 0.05), (850, 620, 140, 110, 0.12), (640, 260, 150, 110, 0.02),
              (1060, 760, 130, 120, 0.12), (480, 200, 110, 80, 0.05)],
        patch=[(0, 300), (262, 262), (262, 1150), (0, 1230)], cross_x=(118, 140), cross_y=(590, 562, 18),
        curtain=(975, 1160, 70, 1560, 5),
        seat=dict(x0=250, x1=1110, top=1262, front=1330, floor=1565, xpad=10, panels=[(290, 660), (700, 1070)]),
        vp=(640, 980), boards=22,
        cushion=(680, 1266, 870, 74),
        pillows=[(420, 1165, 235, 200, -8, 'check'), (625, 1180, 210, 175, 6, 'white'), (960, 1185, 195, 165, 10, 'orange')],
        book=(800, 1250, 170, 70, -4), mug=(1030, 1262, 48, 52),
        floor_patch=[(250, 1575), (1110, 1575), (1152, 1880), (520, 1880)], bar=[(660, 1575), (690, 1575), (900, 1880), (860, 1880)],
        fig=dict(x=175, pot=1770, s=1.0, crown=[(150, 1080, 105, 95, 0.04), (70, 1190, 95, 90, 0.08), (240, 1160, 95, 90, 0.0),
                                               (150, 1280, 110, 85, 0.06), (250, 1330, 80, 70, 0.04), (55, 1370, 85, 75, 0.1),
                                               (190, 990, 80, 70, 0.02), (300, 1240, 60, 60, 0.02)]),
        hang=150, hang_len=1.0,
        stool=(820, 1040, 1730), fg=(1230, 2100, 1.0)),
    'wide': dict(
        size=(1920, 1080), win=(560, 60, 1400, 640), cols=3, transom=0.24, mid_at=0.42,
        cloud=(760, 280, 260, 110),
        far=dict(y=575, x0=500, step=68, n=15, r=(60, 52)),
        mid=[(640, 470, 110, 90, 0.04), (730, 420, 100, 80, 0), (600, 560, 120, 80, 0.08), (770, 545, 120, 80, 0.04),
             (900, 590, 110, 70, 0.06)],
        trunk=[[(1250, 700), (1235, 520), (1215, 360), (1200, 240)], 52, 26],
        limbs=[[[(1225, 430), (1130, 360), (1050, 320)], 20, 8], [[(1210, 330), (1300, 250), (1380, 200)], 17, 7]],
        near=[(1180, 170, 170, 110, 0.0), (1330, 120, 150, 100, 0.02), (1060, 270, 130, 80, 0.08),
              (1310, 330, 140, 100, 0.05), (1190, 370, 120, 80, 0.12), (980, 110, 130, 80, 0.02),
              (1380, 470, 110, 90, 0.12), (840, 80, 100, 60, 0.05)],
        patch=[(1530, 150), (1880, 110), (1880, 640), (1530, 690)], cross_x=(1700, 1720), cross_y=(360, 330, 16),
        curtain=(1340, 1500, 20, 880, 5),
        seat=dict(x0=470, x1=1490, top=688, front=742, floor=890, xpad=10, panels=[(510, 970), (1010, 1450)]),
        vp=(960, 560), boards=30,
        cushion=(980, 692, 1030, 60),
        pillows=[(680, 610, 190, 160, -8, 'check'), (860, 620, 170, 140, 6, 'white'), (1290, 622, 160, 135, 10, 'orange')],
        book=(1090, 680, 140, 56, -4), mug=(1395, 690, 46, 50),
        floor_patch=[(470, 898), (1490, 898), (1920, 1080), (760, 1080)], bar=[(940, 898), (968, 898), (1250, 1080), (1210, 1080)],
        fig=dict(x=260, pot=830, s=0.82, crown=[(240, 380, 95, 85, 0.04), (165, 470, 85, 80, 0.08), (325, 455, 85, 80, 0.0),
                                               (240, 560, 100, 75, 0.06), (330, 600, 70, 60, 0.04), (150, 630, 75, 65, 0.1),
                                               (275, 300, 70, 60, 0.02), (380, 520, 55, 55, 0.02)]),
        hang=120, hang_len=0.7,
        stool=(1560, 1760, 930), fg=(1960, 1130, 0.8)),
}
PRESETS = {
    'noon': dict(seed=21, light=(-0.55, -0.72, 0.42), sky=('#2470d0', '#4a93e0', '#a8d2f0'), sun='#fff1d2', tint=0.0,
                 floor_sun='#ffeccb', wall=('#d9dde6', '#e9e7e4'), tones=None),
    'late': dict(seed=21, light=(-0.75, -0.45, 0.5), sky=('#2a5cb6', '#6a9ad6', '#f4c493'), sun='#ffe0b4', tint=0.5,
                 floor_sun='#ffc888', wall=('#cfcbdc', '#ddd5d8'),
                 tones='gold'),
}


def scene(g, L, P, stage):
    W, H = g.W, g.H
    X0, Y0, X1, Y1 = L['win']
    tones = P['tones']
    # ---- outside: sky, a cloud, far / middle / near trees
    g.sky(*P['sky'], y0=Y0, y1=Y1, mid_at=L['mid_at'])
    cx, cy, cw, ch = L['cloud']
    g.cloud(cx, cy, cw, ch, seed=4)
    stage('sky')
    r = np.random.default_rng(2)
    F = L['far']
    far = [(F['x0'] + i * F['step'] + r.random() * 20, F['y'] + r.random() * 30, F['r'][0] + r.random() * 30,
            F['r'][1] + r.random() * 20, 0.04) for i in range(F['n'])]
    g.canopy(far, leaf=7, far=0.38, seed=5, holes=0.3, fill=1.0, tones=tones)
    g.canopy(L['mid'], leaf=10, seed=7, holes=0.5, fill=0.85, glint=0.4, tones=tones)
    stage('trees')
    path, w0, w1 = L['trunk']
    g.limb(path, w0, w1, colour='#6a665e', lit='#b8ad9c', bark=0.6, seed=71)
    for path, w0, w1 in L['limbs']:
        g.limb(path, w0, w1, colour='#6a665e', lit='#b8ad9c')
    g.canopy(L['near'], leaf=22, seed=6, holes=1.1, fill=0.0, sub=2.5, glint=0.6, mottle=0.3, twigs=10, airy=1.0,
             levels=(0.0, 0.34, 0.47, 0.6, 0.74), tones=tones)
    stage('near_tree')
    # ---- the room: wall (with the window opening), reveal, window frame, curtain
    OX0, OY0, OX1, OY1 = X0 - 26, Y0 - 26, X1 + 26, Y1 + 34
    opening = np.zeros((H, W), np.float32); opening[OY0:OY1, OX0:OX1] = 1
    wall = 1 - opening
    g.gradient(wall, P['wall'][0], P['wall'][1], axis=0, p0=0, p1=L['seat']['floor'])
    g.strokes(wall, n=int(220 * W * H / 2.36e6), size=70, var=0.018, angle=-80, seed=3)
    g.face([(OX0, OY0), (OX1, OY0), (X1, Y0), (X0, Y0)], 'white_shade')
    g.face([(OX0, OY0), (X0, Y0), (X0, Y1), (OX0, OY1)], 'white_half')
    g.face([(OX1, OY0), (OX1, OY1), (X1, Y1), (X1, Y0)], 'white_sun')
    g.face([(OX0, OY1), (OX1, OY1), (X1, Y1), (X0, Y1)], 'white_sun')
    g.window(X0, Y0, X1, Y1, cols=L['cols'], rows=[L['transom']], frame=16, bar=9)
    stage('window')
    # a sun patch on the wall (from a window out of frame): a window cross and leaf shadows inside it
    pt = np.array(L['patch'], np.float32)
    patch = g.mask([pt])
    cx0, cx1 = L['cross_x']; yl, yr, th = L['cross_y']
    xl, xr = pt[:, 0].min(), pt[:, 0].max()
    cross = g.mask([np.array([(cx0, pt[0, 1] + (pt[1, 1] - pt[0, 1]) * (cx0 - xl) / (xr - xl) - 4), (cx1, pt[0, 1] + (pt[1, 1] - pt[0, 1]) * (cx1 - xl) / (xr - xl) - 4),
                                (cx1, pt[3, 1] + (pt[2, 1] - pt[3, 1]) * (cx1 - xl) / (xr - xl) + 4), (cx0, pt[3, 1] + (pt[2, 1] - pt[3, 1]) * (cx0 - xl) / (xr - xl) + 4)], np.float32),
                    np.array([(xl, yl), (xr, yr), (xr, yr + th), (xl, yl + th)], np.float32)])
    sh = g.leaf_shadow((xl - 10, pt[:, 1].min() - 10, xr + 10, pt[:, 1].max() + 10), cover=0.32, leaf=17, scale=5, seed=8)
    g.sunlight(patch * (1 - cross) * (1 - sh), colour=P['sun'], strength=1.0, tint=P['tint'])
    g.curtain(L['curtain'][0], L['curtain'][1], L['curtain'][2], L['curtain'][3], folds=L['curtain'][4], alpha=0.72,
              seed=4, sway=0.03)
    stage('wall_sun')
    # ---- floor and the window seat
    S = L['seat']
    g.boards(S['floor'] - 10, H, L['vp'], n=L['boards'], tones=('#c3a790', '#c9ab93', '#cdb098', '#c6aa95'), gap='#8f7c80')
    stage('floor')
    sx0, sx1 = S['x0'], S['x1']
    g.box(front=[(sx0, S['front']), (sx1, S['front']), (sx1, S['floor']), (sx0, S['floor'])],
          top=[(sx0 - S['xpad'], S['top']), (sx1 + S['xpad'], S['top']), (sx1, S['front']), (sx0, S['front'])],
          tones=('#e4e5e8', 'white_sun', 'white_shade'))
    ph = S['floor'] - S['front']
    for a, b in S['panels']:
        g.panel(a, S['front'] + ph * 0.18, b, S['floor'] - ph * 0.16, colour='#dfe1e6', lit='#eceae6', shade='#b9c4d6')
    g.face([(sx0, S['floor'] - 10), (sx1, S['floor'] - 10), (sx1, S['floor'] + 10), (sx0, S['floor'] + 10)], 'white_shade',
           wobble=0.3)
    cx, cy, cw, chh = L['cushion']
    cushions = g.cushion(cx, cy, cw, chh, round_=0.35, seed=11, tones=('#c6c3c8', '#e3d8c8', '#f1e7d6', '#fbf4e6'))
    kinds = {'check': dict(tones=('#1e3570', '#26468e', '#2f56a6', '#3d68b8'), stripes=('#e8ecf4', 6, 0.06, -8, True)),
             'white': dict(tones=('#b8c2d4', '#dcdde2', '#f2eee6', '#fdf9f0')),
             'orange': dict(tones=('#a64a2a', '#c75d33', 'orange_cloth', '#f29a5e'))}
    for i, (px, py, pw, ph_, tilt, kind) in enumerate(L['pillows']):
        cushions = np.maximum(cushions, g.cushion(px, py, pw, ph_, round_=0.7, tilt=tilt, bulge=0.12, seed=12 + i,
                                                  **kinds[kind]))
    bx, by, bw, bh, bt = L['book']
    g.book(bx, by, bw, bh, tilt=bt)
    mx, my, mw, mh = L['mug']
    g.mug(mx, my, mw, mh)
    stage('seat')
    # ---- the light through the window: leaf shadows over the sunlit cushions, a sun patch on the floor
    g.dapple(cushions, cover=0.3, leaf=24, squash=0.7, scale=4, seed=19, flecks=0.3)
    win = g.mask([np.array(L['floor_patch'], np.float32)])
    bars = g.mask([np.array(L['bar'], np.float32)])
    sh2 = g.leaf_shadow((0, S['floor'] - 20, W, H), cover=0.3, leaf=34, squash=0.5, scale=4, seed=9, flecks=0.3)
    g.sunlight(win * (1 - bars) * (1 - sh2), colour=P['floor_sun'], strength=0.85, tint=P['tint'] * 0.6)
    stage('light')
    # ---- props and plants: the stool with books, the potted fig, the hanging plant, a plant in the foreground
    k0, k1, ky = L['stool']
    g.box(front=[(k0, ky + 30), (k1, ky + 30), (k1, ky + 60), (k0, ky + 60)],
          top=[(k0 + 10, ky), (k1 - 10, ky), (k1, ky + 30), (k0, ky + 30)], tones=('wood_shade', 'wood_sun', 'wood_deep'))
    for x in (k0 + 20, k1 - 30):
        g.face([(x, ky + 60), (x + 18, ky + 60), (x + 22, ky + 230), (x + 4, ky + 230)], 'wood')
        g.face([(x + 12, ky + 60), (x + 18, ky + 60), (x + 22, ky + 230), (x + 16, ky + 230)], 'wood_shade')
    km = (k0 + k1) / 2
    g.book(km, ky - 15, (k1 - k0) * 0.68, 30, open_=False, cover='book_red', tilt=-3)
    g.book(km - 5, ky - 40, (k1 - k0) * 0.6, 26, open_=False, cover='book_mustard', tilt=4)
    Fg = L['fig']
    fx, fp, s = Fg['x'], Fg['pot'], Fg['s']
    top_y = min(c[1] for c in Fg['crown'])
    for path, w0, w1 in (([(fx - 5, fp + 20), (fx - 15, fp - (fp - top_y) * 0.4), (fx - 35, fp - (fp - top_y) * 0.75),
                           (fx - 25, top_y + 60 * s)], 13 * s, 6 * s),
                         ([(fx + 5, fp + 20), (fx + 30, fp - (fp - top_y) * 0.35), (fx + 75, fp - (fp - top_y) * 0.6)], 11 * s, 5 * s),
                         ([(fx, fp - (fp - top_y) * 0.25), (fx - 65, fp - (fp - top_y) * 0.42), (fx - 115, fp - (fp - top_y) * 0.48)],
                          8 * s, 4 * s)):
        g.limb(path, w0, w1, colour='#6f5f50', lit='#a89480')
    g.canopy(Fg['crown'], leaf=19, seed=31, holes=0.6, fill=0.0, sub=2.2, glint=0.5, mottle=0.3, hole_colour='#e8e7e6',
             light=(0.6, -0.65, 0.45), levels=(0.0, 0.36, 0.5, 0.63, 0.76), tones=tones)
    g.pot(fx, fp, 220 * s, 230 * s, colour='#e9e4da')
    hx, hl = L['hang'], L['hang_len']
    vines = [[(hx, -10), (hx - 10, 160 * hl), (hx - 30, 330 * hl), (hx - 22, 470 * hl)], [(hx, -10), (hx + 40, 150 * hl), (hx + 80, 280 * hl)],
             [(hx, -10), (hx - 55, 120 * hl), (hx - 90, 260 * hl), (hx - 98, 380 * hl)],
             [(hx, -10), (hx + 15, 220 * hl), (hx + 28, 420 * hl), (hx + 20, 600 * hl)]]
    g.spray(vines, leaf=58, width=0.68, rosette=(2, 3), along=0.42, stem_w=2.2, seed=16, droop=0.6, bend=0.06, tones=tones)
    g.pot(hx, -40, 150, 90, colour='#d8d2c4')
    ex, ey, es = L['fg']
    fg = [[(ex, ey), (ex - 110 * es, ey - 140 * es), (ex - 210 * es, ey - 200 * es)],
          [(ex, ey), (ex - 80 * es, ey - 200 * es), (ex - 120 * es, ey - 320 * es)],
          [(ex, ey), (ex - 170 * es, ey - 70 * es), (ex - 300 * es, ey - 90 * es)],
          [(ex, ey), (ex - 40 * es, ey - 200 * es), (ex - 30 * es, ey - 340 * es)]]
    g.spray(fg, leaf=170 * es, width=0.5, rosette=(3, 4), along=0.5, stem_w=5, seed=33, bend=0.07, lit_bias=-0.2,
            tones=tones)


def main():
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    layout, preset, stages = opt('--layout', 'page'), opt('--preset', 'noon'), opt('--stages', None)
    name = 'sunlitgreen_window_seat' + ('' if preset == 'noon' else '_' + preset) + ('' if layout == 'page' else '_wide')
    out = a[0] if a and not a[0].startswith('--') else name + '.jpg'
    L, P = LAYOUTS[layout], PRESETS[preset]
    T0 = time.time()
    W, H = L['size']
    g = SunlitGreen(W, H, seed=P['seed'], keep_stages=bool(stages), stages_dir=stages, light=P['light'])
    g.finish()
    g.stage('blank')
    scene(g, L, P, g.stage)
    g.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s')


if __name__ == '__main__':
    main()
