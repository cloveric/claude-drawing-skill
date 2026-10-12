"""Example (hatched nocturne): 熔岩入海 · Lava Meets the Sea -- a small night print laid entirely in short strokes.

Before dawn on a volcanic coast. Lava trickles down the dark flank of a volcano in glowing threads that braid and
fan out toward the shore; where they reach the sea, the water flashes to steam: a column of billows rises and leans
away on the wind, lit from below -- yellow-white at the waterline, orange and red above, warm grey further up,
cold slate at the top. Sparks fly; a few lava fronts stopped on the slope still glow as beads. The sea carries a
broken warm column back toward us. Far off, a low island; on a small reef in the middle of the water two people
sit side by side watching it, one in a red scarf. Indigo sky with stars, streaming diagonally with the wind.

Every area is built from short directional strokes (sky diagonal, steam round its billows, slopes down the fall
lines, sea in long horizontals), each a little different in hue and value, with hairline gaps of the dark ground;
the one warm light is added on top as light strokes. Mounted as a small print: cream margins, plate mark, a pencilled
title and note in a thin plain face.

Painted in this order: paper and dark ground -> sky -> far island and volcano -> steam -> the light (glow strokes and
the hot source) -> lava threads, sparks -> sea -> reflection -> reef and figures -> mount and captions.
--stages writes those steps as snapshots for the draw-on. No image model.
python3 nocturne_lava_sea.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from nocturne import Nocturne
from core import blur, spline, smoothstep, fbm1d, noise2d, blob_pts

W, H = 1920, 1080
BOX = (80, 56, 1840, 966)
HZ = 604                                   # the open-sea horizon
EX, EY = 1150, 614                         # where the lava meets the sea: the one warm light
RIDGE = [(880, 606), (960, 596), (1040, 578), (1120, 551), (1200, 516), (1280, 474), (1360, 426), (1430, 375),
         (1490, 325), (1530, 287), (1552, 266), (1572, 262), (1588, 272), (1604, 274), (1620, 263), (1640, 266),
         (1672, 290), (1720, 324), (1780, 360), (1860, 400)]
ISLE = [(130, 608), (180, 590), (240, 574), (300, 566), (350, 563), (410, 570), (470, 584), (530, 597), (590, 608)]
ISLE2 = [(640, 608), (680, 596), (726, 591), (772, 598), (812, 608)]
REEF = (490, 772)                          # the reef with the two watchers (centre, waterline)


def waterline():
    """per-column waterline: the open horizon, then the volcano's coast coming a little nearer toward the right,
    with the lava delta bulging out where the threads reach the sea"""
    x = np.arange(W, dtype=np.float32)
    c = HZ + np.clip(x - 900, 0, None) * 0.031 + 1.5 * np.sin(x / 37.0) * (x > 900)
    c = c + 6 * np.exp(-((x - 1168) / 95.0) ** 2)
    return c.astype(np.float32)


class Scene:
    def __init__(self, n):
        self.n = n
        self.wl = waterline()
        X, Y = n.XX, n.YY
        self.sea = np.clip(Y - self.wl[None] + 0.5, 0, 1).astype(np.float32)
        self.sky = n.below(None, HZ + 3, invert=True)
        ridge = np.array(RIDGE, np.float32)
        self.land = n.below(ridge[:, 0], ridge[:, 1]) * (1 - np.clip(Y - self.wl[None] - 2.5, 0, 1))
        i1, i2 = np.array(ISLE, np.float32), np.array(ISLE2, np.float32)
        self.isle = np.maximum(n.below(i1[:, 0], i1[:, 1]) * ((X > 140) & (X < 580)), n.below(i2[:, 0], i2[:, 1]) * ((X > 630) & (X < 806)))
        self.isle = self.isle * (1 - np.clip(Y - HZ - 3, 0, 1))
        self.puffs()

    # ------------------------------------------------------------ the steam column as billows
    def puffs(self):
        n = self.n
        r = np.random.default_rng(41)
        axis = spline([(EX, EY + 2), (EX - 18, 548), (EX - 60, 466), (EX - 125, 384), (EX - 200, 304), (EX - 275, 240),
                       (EX - 335, 200)], 20)
        seg = np.linalg.norm(np.diff(axis, axis=0), axis=1); s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1]
        tang = np.arctan2(np.gradient(axis[:, 1]), np.gradient(axis[:, 0]))
        wind = np.deg2rad(16)
        P = []
        for t in np.sort(r.random(64)) ** 1.15:
            cx, cy = np.interp(t, s, axis[:, 0]), np.interp(t, s, axis[:, 1])
            rad = (16 + 112 * t ** 0.85) * r.uniform(0.72, 1.12)
            P.append((cx + r.uniform(-0.55, 0.55) * rad, cy + r.uniform(-0.25, 0.25) * rad, rad, t, np.interp(t, s, tang)))
        for _ in range(16):                                    # the head spreading downwind
            cx = r.uniform(650, 1060); cy = 226 + r.uniform(-28, 28) + (cx - 860) * 0.1
            P.append((cx, cy, r.uniform(48, 88), 1.0, wind))
        for bx in (1080, 1236):                                # two smaller jets that join the column
            for k in range(7):
                t = k / 7
                P.append((bx - 30 * t - 8 * t * t + r.normal(0, 5), EY - 4 - 115 * t, 9 + 34 * t, 0.12 * t, -np.pi / 2 - 0.3))
        r.shuffle(P)
        P.sort(key=lambda p: p[3] < 0.15)                      # the low, hot billows in front
        H_, W_ = n.H, n.W
        D = np.zeros((H_, W_), np.float32); U = np.zeros((H_, W_), np.float32); RR = np.zeros((H_, W_), np.float32)
        A = np.zeros((H_, W_), np.float32); AX = np.zeros((H_, W_), np.float32); TT = np.zeros((H_, W_), np.float32)
        for i, (cx, cy, rad, t, ax) in enumerate(P):
            x0, x1 = int(max(0, cx - rad * 1.3)), int(min(W_, cx + rad * 1.3))
            y0, y1 = int(max(0, cy - rad * 1.3)), int(min(H_, cy + rad * 1.3))
            if x1 <= x0 or y1 <= y0: continue
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            th = np.arctan2(yy - cy, xx - cx)
            wob = 1 + 0.14 * np.sin(5 * th + i) + 0.08 * np.sin(9 * th + 2 * i)
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (rad * wob)
            dome = np.sqrt(np.clip(1 - d * d, 0, 1))
            on = dome > 0.02
            sl = (slice(y0, y1), slice(x0, x1))
            D[sl] = np.maximum(D[sl], dome)
            U[sl] = np.where(on, np.clip(0.5 + 0.6 * (yy - cy) / rad, 0, 1), U[sl])
            A[sl] = np.where(on, th + np.pi / 2, A[sl])
            AX[sl] = np.where(on, ax, AX[sl])
            RR[sl] = np.where(on, d, RR[sl])
            TT[sl] = np.where(on, t, TT[sl])
        self.D = np.clip(blur(D, 2.0) * 1.25, 0, 1)
        self.U, self.TT = U, TT
        # inside a billow the strokes stream with the rising column (with the wind in the head); only near its rim
        # do they curl round it -- curling everywhere makes whirlpools
        curl = smoothstep(0.55, 0.97, RR) * 0.75 + (1 - smoothstep(0.1, 0.35, TT)) * smoothstep(0.3, 0.8, RR) * 0.25
        self.steam_field = n.blend(AX, A, np.clip(curl, 0, 0.9))

    # ------------------------------------------------------------ 1 sky
    def sky_phase(self):
        n = self.n
        sky = self.sky
        self.sky_field = f = n.blend(n.flow(15, 8, 320, seed=1), self.steam_field, smoothstep(0.0, 0.5, blur(self.D, 18)) * 0.6)
        v = n.value(0.04, 0.6, 56, HZ, 0.08, 240, seed=2)
        n.hatch(sky, f, ('sky', np.clip(v - 0.12, 0, 1)), (22, 44), (2.4, 3.4), 1.5, value=0.1, hue=0.05, pressure=0.97, dry=0.25, seed=3)
        n.hatch(sky, f, ('sky', v), (18, 38), (1.8, 2.8), 1.7, value=0.11, hue=0.06, pressure=0.95, dry=0.35, seed=4)
        streaks = np.clip(n.value(0, 0, 0, H, 0.5, 90, seed=5) - 0.5, 0, 1) * 3.0 * sky
        n.hatch(streaks, f, ('sky', np.clip(v + 0.3, 0, 1)), (18, 42), (1.1, 1.7), 0.16, value=0.14, hue=0.05,
                pressure=0.93, dry=0.6, alpha=0.7, seed=6)
        n.hatch(sky * 0.5, f, ('sky', np.clip(v + 0.45, 0, 1)), (12, 26), (1.0, 1.4), 0.015, value=0.1, pressure=0.92,
                dry=0.65, alpha=0.65, seed=7)
        clear = sky * np.clip(1 - self.D * 3, 0, 1)
        n.stars(clear, 190, (0.55, 1.3), bright=0.07, seed=8)

    # ------------------------------------------------------------ 2 far island and the volcano
    def land_phase(self):
        n = self.n
        n.silhouette(self.isle, 'land', n.flow(4, 6, 120, seed=11), val=n.value(0.3, 0.42, 560, 610, 0.08, 60, seed=12),
                     density=2.4, length=(10, 22), width=(1.8, 2.8), seed=13)
        self.land_field = lf = n.blend(n.radial(1580, 250, turb=8, seed=14), n.flow(8, 4, 200, seed=15),
                                       np.clip((n.YY - 560) / 60, 0, 1) * 0.8)
        v = n.value(0.42, 0.18, 260, 640, 0.1, 80, seed=16)
        n.silhouette(self.land, 'land', lf, val=v, density=2.6, length=(12, 30), width=(2.0, 3.2), seed=17)
        # the ridge catches a little sky: a few lighter strokes along the skyline
        ridge = np.array(RIDGE, np.float32)
        edge = np.clip(self.land - n.below(ridge[:, 0], ridge[:, 1] + 7), 0, 1)
        n.hatch(edge, n.contour(self.land, 3), '#2a3150', (10, 22), (1.4, 2.2), 0.5, value=0.12, pressure=0.85, dry=0.5, seed=18)

    # ------------------------------------------------------------ 3 steam, unlit (cold slate, a little starlight on the tops)
    def steam_phase(self):
        n = self.n
        D, U = self.D, self.U
        top = 1 - U
        v = np.clip(0.1 + 0.32 * top * D + 0.1 * (noise2d(H, W, 60, 3, 21) - 0.5), 0, 1)
        n.hatch(D ** 0.8, self.steam_field, ('steam', v), (14, 30), (2.0, 3.2), 2.2, jitter=0.08, bend=0.08, value=0.1,
                hue=0.04, pressure=0.96, dry=0.3, seed=22)
        n.hatch(D * top, self.steam_field, ('steam', np.clip(v + 0.18, 0, 1)), (10, 24), (1.6, 2.4), 0.45, jitter=0.1,
                bend=0.1, value=0.12, pressure=0.92, dry=0.5, alpha=0.9, seed=23)
        n.hatch(np.clip(D * 2.5, 0, 1) * (D < 0.4), self.steam_field, ('steam', v * 0.8), (16, 34), (1.4, 2.2), 0.6,
                jitter=0.2, value=0.1, pressure=0.85, dry=0.6, alpha=0.75, seed=24)

    # ------------------------------------------------------------ 4 the light: glow strokes and the hot source
    def lights(self):
        n = self.n
        n.light(EX, EY - 6, 210, 'ember', 1.25, squash=0.85)
        n.light(EX - 40, EY - 120, 600, '#c2320e', 0.2)
        self.lava = self.lava_paths()
        E = n._emission(self.lava)
        n.light_from(E, 22, 'ember', 0.45)

    def glow_phase(self):
        n = self.n
        D, U = self.D, self.U
        rec = D * (0.18 + 0.82 * U ** 1.3)
        n.glow(rec, self.steam_field, (12, 26), (1.8, 3.0), 1.8, power=1.65, reach=2.2, blend='paint', ambient='#1c2038',
               whiten=0.6, alpha=0.93, jitter=0.08, pressure=0.97, dry=0.3, seed=31)
        n.glow(rec * U, self.steam_field, (8, 18), (1.6, 2.6), 0.8, power=0.8, reach=2.4, jitter=0.1, seed=32)
        n.glow(self.sky * (1 - D) * 0.3, self.sky_field, (16, 34), (1.6, 2.6), 0.9, power=0.6, reach=1.4, seed=33)
        n.glow(self.land * 0.45, self.land_field, (10, 24), (1.6, 2.6), 1.0, power=0.75, reach=1.6, seed=34)
        n.source(EX, EY - 3, 40, power=0.9, seed=35)
        n.source(EX - 52, EY - 3, 18, power=0.7, core=0.6, seed=36)
        n.source(EX + 74, EY + 1, 20, power=0.75, core=0.6, seed=37)

    # ------------------------------------------------------------ 5 lava threads, sparks
    def lava_paths(self):
        n = self.n
        top = (1580, 250)
        vent = (1408, 470)
        P = n.threads((1556, 290), [vent, (1440, 452)], wander=1.0, strands=2, spread=3, branches=2, branch_len=(20, 50),
                      width=(1.6, 1.4), fall=top, heat=(0.3, 0.65), seed=51)
        ends = [(1066, 610), (1104, 612), (1142, 614), (1180, 616), (1222, 617), (1266, 618)]
        P += n.threads(vent, ends, wander=1.0, strands=4, spread=5.0, branches=14, branch_len=(24, 80), width=(1.6, 1.2),
                       fall=top, heat=(0.35, 0.75), seed=52)
        P += n.threads((1600, 292), [(1650, 508), (1716, 556)], wander=1.0, strands=2, spread=3, branches=4,
                       branch_len=(16, 44), width=(1.4, 1.0), fall=top, heat=(0.3, 0.6), seed=53)
        P += n.threads((1505, 352), [(1336, 562)], wander=1.2, strands=2, spread=3, branches=3, width=(1.3, 1.0), fall=top,
                       heat=(0.25, 0.55), seed=54)
        mask = np.clip(blur(self.land, 1.0) * 1.4, 0, 1)
        for p in P:                                            # lava stays on the slope
            inside = mask[np.clip(p['pts'][:, 1].astype(int), 0, H - 1), np.clip(p['pts'][:, 0].astype(int), 0, W - 1)]
            p['i'] = (p['i'] * smoothstep(0.3, 0.9, inside)).astype(np.float32)
        return P

    def threads_phase(self):
        n = self.n
        n.filaments(self.lava, gain=1.05, halo=1.0, light=0.55, receptivity=self.land, field=self.land_field, beads=0.5, seed=61)
        n.sparks(EX, EY - 8, 46, spread=0.55, speed=(30, 120), streak=(5, 16), seed=62)
        n.sparks(EX - 60, EY - 6, 14, spread=0.5, speed=(20, 70), seed=63)
        n.embers(n.ellipse(EX - 30, EY - 120, 110, 130) * self.D, 50, seed=64)

    # ------------------------------------------------------------ 6 sea
    def sea_phase(self):
        n = self.n
        self.src = n.C.copy()
        sea = self.sea
        f = n.flow(0, 1.5, 300, seed=71)
        dep = lambda x, y: np.clip(y - HZ, 0, None)
        L = lambda x, y: 18 + 0.24 * dep(x, y)
        Wd = lambda x, y: 1.9 + 0.0045 * dep(x, y)
        v = n.value(0.62, 0.16, HZ, 966, 0.1, 160, seed=72)
        n.hatch(sea, f, ('sea', np.clip(v - 0.14, 0, 1)), L, Wd, 1.7, jitter=0.03, bend=0.01, value=0.1, hue=0.04,
                pressure=0.975, dry=0.3, lit=0.18, seed=73)
        n.hatch(sea, f, ('sea', v), lambda x, y: 0.85 * L(x, y), lambda x, y: 0.85 * Wd(x, y), 1.4, jitter=0.03,
                bend=0.01, value=0.12, hue=0.05, pressure=0.96, dry=0.4, lit=0.3, seed=74)
        waves = smoothstep(0.55, 0.75, noise2d(H, W, 22, 3, 75) * 0.6 + 0.4 * np.sin(n.YY / (3 + 0.03 * np.clip(n.YY - HZ, 0, None))) * 0.5 + 0.2)
        near_h = np.exp(-np.clip(n.YY - HZ, 0, None) / 90)
        glint = sea * np.clip(waves * 0.35 * (1 - 0.6 * np.clip((n.YY - HZ) / 360, 0, 1)) + near_h * 0.4, 0, 1)
        n.hatch(glint, f, ('sea', np.clip(v + 0.4, 0, 1)), lambda x, y: 0.5 * L(x, y), lambda x, y: 0.6 * Wd(x, y), 0.24,
                jitter=0.03, bend=0.01, value=0.14, pressure=0.88, dry=0.55, alpha=0.85, lit=0.2, seed=76)
        band = sea * (n.YY < HZ + 6) * (n.XX < 960)
        n.hatch(band, 0.0, '#8597c4', (30, 80), (1.6, 2.4), 0.8, jitter=0.01, bend=0.0, value=0.12, pressure=0.85, dry=0.5,
                alpha=0.8, seed=77)

    # ------------------------------------------------------------ 7 reflection
    def reflection_phase(self):
        n = self.n
        n.reflect(self.wl, self.sea, self.src, stretch=1.3, ripple=5, darken=0.85, mixw=0.25, thr=0.1,
                  length=lambda x, y: 16 + 0.2 * np.clip(y - HZ, 0, None), width=(2.0, 3.2), density=1.4, seed=81)
        n.glitter(EX, self.wl[EX] + 1, 966, w0=14, w1=150, power=1.0, density=1.5, seed=82)

    # ------------------------------------------------------------ 8 reef and the two watchers
    def figures_phase(self):
        n = self.n
        cx, wy = REEF
        pts = [(cx - 150, wy + 2), (cx - 128, wy - 8), (cx - 92, wy - 16), (cx - 52, wy - 22), (cx - 14, wy - 25), (cx + 30, wy - 24),
               (cx + 66, wy - 18), (cx + 98, wy - 12), (cx + 124, wy - 6), (cx + 146, wy + 2)]
        reef = n.poly(pts, smooth=True)
        reef = reef * (n.YY < wy + 2)
        behind = n.ellipse(cx + 20, wy - 30, 230, 34) * self.sea * (1 - reef)        # a few glints to silhouette them
        n.hatch(behind * 0.7, 0.0, '#6c7eac', (14, 40), (1.4, 2.2), 0.4, jitter=0.02, value=0.12, pressure=0.92, dry=0.5,
                alpha=0.75, seed=90)
        n.silhouette(reef, 'land', n.flow(-6, 10, 60, seed=91), val=n.value(0.32, 0.12, wy - 26, wy, 0.1, 30, seed=92),
                     density=2.6, length=(6, 16), width=(1.6, 2.6), rim=0.14, rim_from=(EX, EY - 40), seed=93)
        under = n.poly([(cx - 156, wy + 1), (cx + 152, wy + 1), (cx + 120, wy + 16), (cx - 120, wy + 16)]) * self.sea
        n.hatch(under, 0.0, '#0a1129', (20, 60), (1.8, 2.6), 1.4, jitter=0.02, value=0.1, pressure=0.9, alpha=0.8, seed=94)
        surf = n.poly([(cx - 160, wy - 1), (cx + 160, wy - 1), (cx + 160, wy + 3), (cx - 160, wy + 3)]) * (1 - reef * 0.7)
        n.hatch(surf * 0.5, 0.0, '#7d8db8', (6, 18), (1.2, 1.8), 0.5, value=0.1, pressure=0.88, dry=0.5, alpha=0.7, seed=95)
        n.figure(cx + 4, wy - 23, 44, facing=1, accent='scarf', legs='knees', rim_from=(EX, EY), rim=0.45, seed=96)
        n.figure(cx + 37, wy - 22, 40, facing=1, accent=None, legs='knees', lean=0.18, rim_from=(EX, EY), rim=0.45,
                 hat=True, accent2='#2b2f45', seed=97)

    def finish(self):
        n = self.n
        n.mount(plate=16, depth=0.06)
        x0, y0, x1, y1 = BOX
        n.caption('Forty seconds', x0 + 2, y1 + 58, 27, anchor='ls', weight='light', seed=101)
        n.caption('lava meeting the sea before dawn', x1 - 2, y1 + 58, 19, anchor='rs', weight='light', alpha=0.75, seed=102)
        n.bloom(1.0); n.grain(1.0)


PHASES = (('sky', 'sky_phase'), ('land', 'land_phase'), ('steam', 'steam_phase'), ('glow', 'glow_phase'),
          ('threads', 'threads_phase'), ('sea', 'sea_phase'), ('reflection', 'reflection_phase'), ('figures', 'figures_phase'))


def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'nocturne_lava_sea.jpg'
    stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
    T0 = time.time()
    tick = (lambda name: print(f'{name:10s} {time.time() - T0:5.1f}s')) if os.environ.get('NC_TIMING') else (lambda n: None)
    n = Nocturne(W, H, seed=12, keep_stages=bool(stages), stages_dir=stages)
    n.sheet(BOX)
    n.stage('sheet')
    sc = Scene(n)
    sc.lights()
    tick('setup')
    for name, ph in PHASES:
        getattr(sc, ph)()
        tick(name)
        n.stage(name)
    sc.finish()
    n.save(out, stages_dir=stages)
    tick('saved')
    print('saved', out, f'{time.time() - T0:.1f}s', n.n_strokes, 'strokes')


if __name__ == '__main__':
    main()
