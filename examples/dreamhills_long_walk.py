"""Example (dreamy hills): 走过草丘 · The Long Walk -- one person walking over giant furred hills, three times of day.

A tall (1:2) phone wallpaper of huge, soft, rolling hills covered in a velvety fur of fine grass strokes, each hill a
luminous colour field, a clean deep sky over half the frame, a band of tall grass and wildflowers along the bottom,
and one walker a few dozen pixels tall on a far crest.
  --preset dawn   lavender and apricot: a low sun behind the right-hand hills warms every crest it reaches and the
                  rest of the grass is lit lilac by the sky; a sculpted cumulus lit apricot on its sunward side, a
                  small one lower down, a line of little trees on the farthest ridge; white and blue flowers.
  --preset night  burnt orange under a deep blue night: the hills lit from the left by a light out of frame,
                  falling into blue shade on the other side; a milky way across the sky, a comet and a field of
                  stars; the walker carries a small lantern on the top of the tallest hill.
  --preset noon   saffron: glowing yellow swells under a pale blue noon sky with a low bank of cumulus; the walker
                  comes down a shoulder of the hill; blue cornflowers along the bottom.
--layout page (1200 x 2400, the wallpaper) or wide (1920 x 1080: the same picture laid out 16:9, for the draw-on
GIF and for video); --stages writes a snapshot after each step (the blank canvas, the sky, the clouds or the night
sky, every hill from the back -- the walker with his hill -- then the foreground in the final). No image model.
python3 dreamhills_long_walk.py [out.jpg] [--preset dawn|night|noon] [--layout page|wide] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from dreamhills import DreamHills

# Every composition: palette and seed; sky stops, sun glow; clouds [(cx, base, w, h, seed, kwargs)] or the night sky;
# hills back to front [(ridge control points, hill kwargs)]; trees (hill index, xs, h); the walker (hill index, x,
# h, kwargs); the foreground band (top, kwargs).
DAWN_LIGHT = (0.75, 0.35, 0.5)
NOON_LIGHT = (0.35, 0.8, 0.45)
SCENES = {
    ('dawn', 'page'): dict(
        size=(1200, 2400), palette='lilac', seed=5,
        sky=dict(stops=[(0.0, '#2a66c4'), (0.25, '#4f8ddc'), (0.42, '#93b0ee'), (0.5, '#c8bff2'), (0.56, '#f4c6c0')],
                 sun_xy=(980, 1290), glow='#ffd2a8', glow_r=0.32, glow_strength=0.45),
        clouds=[(690, 760, 680, 400, 4, dict(light=DAWN_LIGHT, warm='#ffc6a0', warm_k=0.55)),
                (230, 1010, 280, 120, 9, dict(n=22, detail=16, towers=1, light=DAWN_LIGHT, warm='#ffc6a0', warm_k=0.5))],
        hills=[([(-60, 1268), (300, 1250), (640, 1272), (980, 1238), (1260, 1262)],
                dict(blade=3.5, foot=60, haze=0.5, swell_scale=(220, 30), rim=0.6)),
               ([(-60, 1360), (200, 1318), (520, 1380), (900, 1400), (1260, 1352)],
                dict(blade=5.5, foot=110, haze=0.28, swell_scale=(260, 50))),
               ([(-60, 1760), (250, 1600), (560, 1470), (820, 1420), (1050, 1460), (1260, 1530)],
                dict(blade=11, foot=300, haze=0.05, swell=0.55, swell_scale=(560, 120), rim=1.3)),
               ([(-60, 1930), (300, 1990), (700, 2060), (1000, 2010), (1260, 1940)],
                dict(blade=18, foot=260, swell=0.7, swell_scale=(420, 120)))],
        trees=(0, [600, 628, 760, 776, 800, 822, 990, 1016, 1120], 28, dict(haze=0.42)),
        walker=(2, 760, 34, dict(facing=1, grass='#e8c0b4')),
        foreground=(2190, dict(flowers=70))),
    ('night', 'page'): dict(
        size=(1200, 2400), palette='ember', seed=8, bloom=0.4,
        sky=dict(stops=[(0.0, '#040c2e'), (0.3, '#0a2160'), (0.55, '#163c86'), (0.62, '#2a5aa6')]),
        night=dict(stars=(4000, 0, 1500, (1100, 1450)), milky=((1180, 120), (80, 1380), 120, -120),
                   comet=(880, 820, -128, 380)),
        hills=[([(-60, 1420), (300, 1395), (640, 1430), (1000, 1380), (1260, 1400)],
                dict(blade=4, foot=70, haze=0.35, swell_scale=(240, 40), rim=0.6)),
               ([(-60, 1560), (260, 1470), (560, 1350), (760, 1320), (980, 1400), (1260, 1560)],
                dict(blade=10, foot=330, swell=0.35, swell_scale=(520, 120), rim=1.4)),
               ([(-60, 1820), (350, 1760), (800, 1850), (1260, 1720)],
                dict(blade=14, foot=260, swell=0.45, swell_scale=(480, 120), rim=1.2)),
               ([(-60, 2060), (400, 2010), (900, 2090), (1260, 2040)],
                dict(blade=18, foot=260, swell=0.45, swell_scale=(480, 120)))],
        walker=(1, 700, 34, dict(facing=-1, shirt='shirt_white', lamp='#ff9a30', grass='#d07a3a')),
        foreground=(2200, dict(flowers=40))),
    ('noon', 'page'): dict(
        size=(1200, 2400), palette='saffron', seed=12,
        sky=dict(stops=[(0.0, '#4f92ea'), (0.3, '#78aef4'), (0.5, '#a9cbf8'), (0.56, '#cfe0fa')]),
        clouds=[(930, 1170, 520, 260, 21, dict(light=NOON_LIGHT)),
                (1160, 1175, 300, 150, 22, dict(n=30, detail=30, towers=1, light=NOON_LIGHT)),
                (560, 1185, 260, 110, 23, dict(n=22, detail=16, towers=1, light=NOON_LIGHT))],
        hills=[([(-60, 1250), (400, 1232), (800, 1258), (1260, 1236)],
                dict(blade=3.5, foot=60, haze=0.45, swell_scale=(220, 30), rim=0.6)),
               ([(-60, 1400), (500, 1360), (900, 1300), (1260, 1330)],
                dict(blade=6, foot=110, haze=0.22, swell_scale=(300, 50))),
               ([(-60, 1240), (150, 1170), (380, 1160), (640, 1260), (950, 1420), (1260, 1500)],
                dict(blade=10, foot=320, haze=0.03, swell=0.5, swell_scale=(520, 120), rim=1.3)),
               ([(-60, 1820), (300, 1700), (700, 1600), (980, 1560), (1260, 1600)],
                dict(blade=13, foot=280, swell=0.5, swell_scale=(480, 120), rim=1.2)),
               ([(-60, 1990), (400, 2050), (800, 2000), (1260, 2060)],
                dict(blade=18, foot=260, swell=0.5, swell_scale=(480, 120)))],
        walker=(3, 900, 34, dict(facing=-1, grass='#ffc840')),
        foreground=(2150, dict(flowers=150, flower_colours=['cornflower_blue', 'cornflower_blue', 'flower_white']))),
    # ---- the same three pictures laid out 16:9 (the draw-on GIFs, video)
    ('dawn', 'wide'): dict(
        size=(1920, 1080), palette='lilac', seed=5,
        sky=dict(stops=[(0.0, '#3270c8'), (0.3, '#5f98e0'), (0.46, '#a6b6f0'), (0.55, '#d0c2f2'), (0.6, '#f4c6c0')],
                 sun_xy=(1600, 600), glow='#ffd2a8', glow_r=0.3, glow_strength=0.45),
        clouds=[(1180, 330, 600, 290, 4, dict(light=DAWN_LIGHT, warm='#ffc6a0', warm_k=0.55)),
                (420, 440, 240, 90, 9, dict(n=22, detail=16, towers=1, light=DAWN_LIGHT, warm='#ffc6a0', warm_k=0.5))],
        hills=[([(-60, 600), (500, 586), (1000, 606), (1500, 576), (1980, 596)],
                dict(blade=3.5, foot=50, haze=0.5, swell_scale=(260, 26), rim=0.6)),
               ([(-60, 660), (400, 632), (900, 676), (1450, 690), (1980, 650)],
                dict(blade=5.5, foot=90, haze=0.28, swell_scale=(300, 40))),
               ([(-60, 900), (400, 790), (800, 712), (1150, 688), (1500, 716), (1980, 800)],
                dict(blade=10, foot=220, haze=0.05, swell=0.55, swell_scale=(640, 90), rim=1.3)),
               ([(-60, 930), (500, 960), (1100, 1000), (1600, 950), (1980, 910)],
                dict(blade=15, foot=180, swell=0.7, swell_scale=(520, 90)))],
        trees=(0, [930, 958, 1180, 1196, 1222, 1246, 1520, 1548, 1720], 22, dict(haze=0.42)),
        walker=(2, 1150, 32, dict(facing=1, grass='#e8c0b4')),
        foreground=(985, dict(flowers=80))),
    ('night', 'wide'): dict(
        size=(1920, 1080), palette='ember', seed=8, bloom=0.4,
        sky=dict(stops=[(0.0, '#040c2e'), (0.3, '#0b2464'), (0.58, '#183f8a'), (0.66, '#2a5aa6')]),
        night=dict(stars=(3600, 0, 700, (520, 680)), milky=((1880, 40), (260, 680), 100, -90),
                   comet=(1420, 330, -150, 280)),
        hills=[([(-60, 660), (500, 645), (1000, 670), (1500, 640), (1980, 655)],
                dict(blade=4, foot=60, haze=0.35, swell_scale=(260, 34), rim=0.6)),
               ([(-60, 860), (350, 780), (700, 640), (930, 572), (1120, 600), (1450, 720), (1980, 800)],
                dict(blade=9, foot=240, swell=0.35, swell_scale=(600, 90), rim=1.4)),
               ([(-60, 860), (600, 820), (1200, 880), (1980, 800)],
                dict(blade=12, foot=200, swell=0.45, swell_scale=(560, 90), rim=1.2)),
               ([(-60, 970), (700, 940), (1400, 990), (1980, 950)],
                dict(blade=16, foot=180, swell=0.45, swell_scale=(560, 90)))],
        walker=(1, 900, 32, dict(facing=-1, shirt='shirt_white', lamp='#ff9a30', grass='#d07a3a')),
        foreground=(1000, dict(flowers=45))),
    ('noon', 'wide'): dict(
        size=(1920, 1080), palette='saffron', seed=12,
        sky=dict(stops=[(0.0, '#5294ea'), (0.35, '#7cb0f4'), (0.55, '#acccf8'), (0.62, '#d0e1fa')]),
        clouds=[(1380, 560, 640, 300, 21, dict(light=NOON_LIGHT)),
                (1800, 566, 360, 170, 22, dict(n=30, detail=30, towers=1, light=NOON_LIGHT)),
                (900, 572, 300, 120, 23, dict(n=22, detail=16, towers=1, light=NOON_LIGHT))],
        hills=[([(-60, 620), (600, 604), (1300, 630), (1980, 610)],
                dict(blade=3.5, foot=50, haze=0.45, swell_scale=(260, 26), rim=0.6)),
               ([(-60, 700), (800, 680), (1400, 650), (1980, 668)],
                dict(blade=5.5, foot=80, haze=0.22, swell_scale=(300, 40))),
               ([(-60, 560), (300, 500), (620, 494), (1000, 600), (1450, 720), (1980, 790)],
                dict(blade=9, foot=240, haze=0.03, swell=0.5, swell_scale=(620, 90), rim=1.3)),
               ([(-60, 900), (500, 820), (1050, 760), (1450, 742), (1980, 780)],
                dict(blade=12, foot=200, swell=0.5, swell_scale=(560, 90), rim=1.2)),
               ([(-60, 960), (600, 1000), (1300, 950), (1980, 1000)],
                dict(blade=16, foot=180, swell=0.5, swell_scale=(560, 90)))],
        walker=(3, 1400, 32, dict(facing=-1, grass='#ffc840')),
        foreground=(975, dict(flowers=170, flower_colours=['cornflower_blue', 'cornflower_blue', 'flower_white']))),
}


def scene(g, S, stage):
    g.sky(**S['sky'])
    stage('sky')
    for (cx, base, w, h, seed, kw) in S.get('clouds', []):
        g.cloud(cx, base, w, h, seed=seed, **kw)
    if 'night' in S:
        N = S['night']
        n, y0, y1, fade = N['stars']
        g.stars(n, y0, y1, fade=fade, spikes=4, bright=0.6, seed=31)
        p0, p1, wd, bend = N['milky']
        g.milky_way(p0, p1, wd, bend=bend, strength=0.26, stars=9000, seed=32)
        x, y, ang, ln = N['comet']
        g.comet(x, y, ang, ln, strength=0.6, spread=0.16, seed=33)
    stage('stars' if 'night' in S else 'clouds')
    ridges = [g.ridge(pts) for pts, _ in S['hills']]
    wi = S['walker'][0]
    for i, (r, (_, kw)) in enumerate(zip(ridges, S['hills'])):
        g.hill(r, front=ridges[i + 1:], seed=100 + i, **kw)
        if 'trees' in S and S['trees'][0] == i:
            _, xs, th, tkw = S['trees']
            g.trees(r, xs, th, seed=7, **tkw)
        if i == wi:
            _, wx, wh, wkw = S['walker']
            g.walker(wx, r.at(wx) + 2, wh, **wkw)
        stage('walker' if i == wi else f'hill{i}')
    top, fkw = S['foreground']
    g.foreground(top, seed=55, **fkw)


def main():
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    preset, layout = opt('--preset', 'dawn'), opt('--layout', 'page')
    stages = opt('--stages', None)
    name = 'dreamhills_long_walk' + ('' if preset == 'dawn' else '_' + preset) + ('' if layout == 'page' else '_wide')
    out = a[0] if a and not a[0].startswith('--') else name + '.jpg'
    S = SCENES[(preset, layout)]
    T0 = time.time()
    W, H = S['size']
    g = DreamHills(W, H, seed=S['seed'], palette=S['palette'], keep_stages=bool(stages), stages_dir=stages)
    g.finish(bloom=S.get('bloom', 0.3))
    g.stage('blank')
    scene(g, S, g.stage)
    g.save(out, stages_dir=stages)
    print('saved', out, f'{time.time() - T0:.1f}s')


if __name__ == '__main__':
    main()
