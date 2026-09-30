"""Example (isometric 2.5D): 岛上的气象站 · Island Weather Station — a pastel isometric diorama of a small island that
turns its weather into four numbers: a fenced observation plot on a raised terrace (a louvred thermometer screen,
a rain gauge, a wind mast with cup anemometer and vane), the keeper's house with a satellite dish and solar panels,
a jetty with a boat, trees, rocks and a shore of foam; a weather balloon rising with its radiosonde and two
flat-bottomed clouds. Floating data cards (wind, temperature, rain, upper air) drop slim leaders to the
instrument each number comes from. Everything is traced solids lit by one soft sun. No image model.
python3 isometric_weather_island.py [out.jpg] [--stages DIR]
"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from isometric import Isometric, INK, CORAL

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'isometric_weather_island.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

iso = Isometric(1920, 1080, seed=11, scale=80, look=(5, 5, 0), at=(0.515, 0.55), record=stages is not None)

WHITE, LAV, LAVD = '#fbfaf8', '#e7e1f3', '#b9addc'

# ---- 1. the floating slab
iso.backdrop('#e4def3', '#f5eeee', '#fbf8ff')
iso.slab(0, 0, 10, 10, z0=-0.95)
iso.stage('slab')

# ---- 2. land and sea: 0 sea, 1 sand, 2 grass, 3 the raised terrace of the observation plot, 4 a paved path
levels = np.array([
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 1, 2, 3, 3, 3, 2, 1, 0, 0],
    [0, 1, 2, 3, 3, 3, 2, 2, 1, 0],
    [0, 1, 2, 3, 3, 3, 2, 2, 1, 0],
    [0, 2, 2, 4, 2, 2, 2, 2, 1, 0],
    [0, 2, 2, 4, 2, 2, 2, 1, 0, 0],
    [0, 1, 1, 4, 2, 2, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]])
iso.tiles(levels)
iso.sea(shallow='#c3eae6', deep='#abc9f1', waves=1.0)
iso.stage('land')

G, T = 0.32, 0.60                       # grass and terrace tile tops

# ---- 3. jetty, steps from the path up to the terrace, rocks on the shore
iso.pier(7.2, 1.72, 9.85, 2.2, z=0.27)
for k in range(3):                                     # three steps from the grass up to the terrace
    x0 = 5.02 + 0.13 * (2 - k)
    iso.box(x0, 3.22, 0.0, x0 + 0.13, 3.78, 0.3 + (T - 0.3) * (k + 1) / 3.3, LAV, bevel=0.012)
for (x, y, r) in [(1.3, 1.55, 0.12), (1.15, 1.9, 0.08), (8.3, 3.25, 0.13), (7.35, 7.35, 0.11), (2.25, 7.7, 0.1),
                  (8.6, 5.9, 0.1)]:
    z = iso.top_z(x, y)
    iso.rock(x, y, z - (0.05 if z < 0.2 else 0), r)
for (x, y, col) in [(9.0, 6.3, CORAL), (6.4, 9.1, '#f7df97')]:             # two channel buoys
    iso.cylinder(x, y, 0.04, 0.24, 0.13, col, r1=0.11)
    iso.cylinder(x, y, 0.24, 0.3, 0.11, WHITE, r1=0.1)
    iso.cylinder(x, y, 0.3, 0.62, 0.035, WHITE)
    iso.cylinder(x, y, 0.62, 0.74, 0.07, col, r1=0.0)
iso.stage('shore')

# ---- 4. the keeper's house, dish and solar panels
iso.building(5.25, 1.25, 6.65, 2.75, z=G, h=0.72, wall=WHITE, roof='gable', axis='y', roof_colour='#f3a597',
             windows=(1, 2, 1), door=('+x', 2.0), trim='#e9e2f3')
iso.dish(4.5, 2.0, G, r=0.22, yaw=125, tilt=40, h=0.42)
iso.windsock(7.55, 1.1, 0.22, h=0.85, yaw=135)          # streams north-west: a south-east wind
for k in range(2):
    iso.solar_panel(6.05, 4.35 + k * 1.05, G, w=0.92, d=0.62, tilt=26, yaw=0)
iso.stage('station')

# ---- 5. the observation plot: fence, thermometer screen, rain gauge, wind mast


def stevenson(x, y, z):
    """a louvred thermometer screen on four legs, white, with a double roof"""
    for dx in (-0.14, 0.14):
        for dy in (-0.11, 0.11):
            iso.box(x + dx - 0.014, y + dy - 0.014, z, x + dx + 0.014, y + dy + 0.014, z + 0.52, WHITE, bevel=0.005)
    zb = z + 0.5
    c = np.array([1.0, 1.0, 1.0], np.float32) * np.array([0.985, 0.978, 0.972], np.float32)

    def louvre(P, n, t):
        v = np.mod((P[:, 2] - zb) / 0.042, 1.0)
        side = np.abs(n[:, 2]) < 0.5
        k = np.where(side & (v < 0.34), 0.82, np.where(side & (v < 0.42), 0.93, 1.0))
        return c * k[:, None]
    iso.box(x - 0.2, y - 0.17, zb, x + 0.2, y + 0.17, zb + 0.36, WHITE, bevel=0.01, paint=louvre)
    iso.box(x - 0.23, y - 0.2, zb + 0.38, x + 0.23, y + 0.2, zb + 0.405, WHITE, bevel=0.008)
    iso.box(x - 0.25, y - 0.22, zb + 0.43, x + 0.25, y + 0.22, zb + 0.455, WHITE, bevel=0.008)
    return np.array([x, y, zb + 0.46])


def rain_gauge(x, y, z):
    """a copper-free white gauge: base ring, body, a darker funnel opening"""
    iso.cylinder(x, y, z, z + 0.03, 0.11, LAV)
    rim = np.array([0.30, 0.28, 0.40], np.float32)

    def top(P, n, t):
        r = np.hypot(P[:, 0] - x, P[:, 1] - y)
        c = np.where((n[:, 2] > 0.9) & (r < 0.062), 0.55, 1.0)[:, None]
        return np.array([0.975, 0.97, 0.965], np.float32) * c + rim * (1 - c) * 0.0
    iso.cylinder(x, y, z + 0.03, z + 0.33, 0.08, WHITE, paint=top)
    iso.cylinder(x, y, z + 0.33, z + 0.36, 0.088, WHITE, r1=0.09)
    return np.array([x, y, z + 0.37])


def wind_mast(x, y, z, h=2.7):
    """a slim white mast with coral bands, three guy wires, a cross-arm carrying a cup anemometer and a vane"""
    top = z + h
    band = np.array([0.95, 0.62, 0.57], np.float32); wh = np.array([0.985, 0.98, 0.975], np.float32)

    def bands(P, n, t):
        f = (P[:, 2] - z) / h
        on = ((f > 0.62) & (f < 0.68)) | ((f > 0.82) & (f < 0.88))
        return np.where(on[:, None], band, wh)
    iso.cylinder(x, y, z, top, 0.032, WHITE, r1=0.024, paint=bands)
    for a in (100, 220, 340):
        ax_, ay_ = x + 0.55 * np.cos(np.radians(a)), y + 0.55 * np.sin(np.radians(a))
        iso.tube((x, y, z + h * 0.6), (ax_, ay_, z + 0.01), 0.005, '#cfc8e4', ao=False)
        iso.box(ax_ - 0.03, ay_ - 0.03, z, ax_ + 0.03, ay_ + 0.03, z + 0.04, LAVD, bevel=0.01)
    arm0, arm1 = np.array([x, y - 0.38, top - 0.02]), np.array([x, y + 0.38, top - 0.02])
    iso.tube(arm0, arm1, 0.016, WHITE)
    # cup anemometer on the +y end
    ax_, ay_ = arm1[0], arm1[1]
    iso.cylinder(ax_, ay_, top - 0.02, top + 0.2, 0.014, WHITE)
    iso.cylinder(ax_, ay_, top + 0.17, top + 0.23, 0.035, WHITE)
    for k in range(3):
        a = np.radians(20 + 120 * k)
        e = np.array([ax_ + 0.24 * np.cos(a), ay_ + 0.24 * np.sin(a), top + 0.2])
        iso.tube((ax_, ay_, top + 0.2), e, 0.008, WHITE)
        tng = np.degrees(a) + 90                                       # cups open sideways, all the same way round
        iso.ellipsoid(e, (0.062, 0.062, 0.062), CORAL, yaw=tng, clip=[((np.cos(np.radians(tng)), np.sin(np.radians(tng)), 0),
                                                                    np.cos(np.radians(tng)) * e[0] + np.sin(np.radians(tng)) * e[1])])
    # wind vane on the -y end: shaft, pointer, tail fin
    vx, vy = arm0[0], arm0[1]
    iso.cylinder(vx, vy, top - 0.02, top + 0.16, 0.014, WHITE)
    yaw = -45.0                                                        # points into the wind: south-east (north is +y)
    d = np.array([np.cos(np.radians(yaw)), np.sin(np.radians(yaw)), 0])
    c = np.array([vx, vy, top + 0.16])
    iso.tube(c - d * 0.27, c + d * 0.24, 0.011, WHITE)
    iso.tube(c + d * 0.24, c + d * 0.37, 0.038, CORAL, r1=0.0)
    iso.obox(c - d * 0.25, (0.2, 0.014, 0.16), yaw=yaw, colour=CORAL, bevel=0.005)
    iso.sphere(x, y, top + 0.035, 0.028, CORAL)                          # obstruction light
    return np.array([ax_, ay_, top + 0.24])


iso.fence([(2.12, 3.12), (4.88, 3.12), (4.88, 5.88), (2.12, 5.88)], z=T, h=0.18, closed=True, spacing=0.23)
a_screen = stevenson(3.75, 3.95, T)
a_rain = rain_gauge(3.2, 5.25, T)
a_wind = wind_mast(2.55, 3.55, T, h=3.1)
iso.stage('instruments')

# ---- 6. trees, bushes, the boat
for (x, y, s_, k) in [(2.5, 6.55, 1.05, 'round'), (3.45, 7.35, 0.9, 'round'), (4.3, 7.5, 1.0, 'pine'),
                      (5.45, 7.15, 1.05, 'round'), (6.45, 6.55, 0.95, 'pine'), (1.55, 2.55, 0.9, 'pine'),
                      (1.6, 6.35, 0.85, 'round'), (4.45, 6.75, 0.85, 'poplar'), (5.4, 6.2, 0.8, 'poplar'),
                      (7.3, 4.5, 0.85, 'round'), (3.5, 1.5, 0.9, 'round')]:
    iso.tree(x, y, iso.top_z(x, y), s_, k)
for (x, y, fl) in [(6.85, 3.25, '#f6b3c4'), (5.15, 1.05, None), (7.35, 5.65, '#f7df97'), (1.7, 4.4, None),
                  (6.6, 6.35, '#f6b3c4'), (2.95, 6.2, '#fbfaf8'), (4.6, 2.8, '#c9b8f2'), (7.3, 3.8, None)]:
    iso.tree(x, y, iso.top_z(x, y), 1.1 if fl else 1.0, 'bush', flowers=fl)
iso.boat(8.9, 2.72, 0.14, length=0.95, width=0.38, yaw=0)
iso.stage('trees')

# ---- 7. the sky: a rising weather balloon and two clouds
bx, by, bz = iso.unproject(1440, 300, 4.4)
iso.balloon(bx, by, bz, r=0.4, colour='#fbe3ea', string=0.85)
a_ball = np.array([bx, by, bz - 0.4 - 0.85 - 0.06])
cx, cy, cz = iso.unproject(470, 470, 3.0)
iso.cloud(cx, cy, cz, 0.95)
cx, cy, cz = iso.unproject(1760, 760, 2.4)
iso.cloud(cx, cy, cz, 0.7)
iso.stage('sky')

# ---- 8. data cards, each with a leader to its instrument
cards = [
    dict(at=(700, 300), z=2.6, title='气温', tag='TEMP', value='21.4', unit='°C', note='百叶箱内，离地 1.5 m', icon='temp',
         series=[16.2, 16.8, 18.1, 19.6, 20.4, 21.0, 21.6, 21.4], anchor=a_screen, accent='#f08f86'),
    dict(at=(1265, 215), z=4.2, title='风速', tag='WIND', value='4.6', unit='m/s', note='东南风，3 级', icon='wind',
         series=[3.1, 3.8, 3.4, 4.4, 5.2, 4.1, 4.9, 4.6], anchor=a_wind, accent='#8f7ee6'),
    dict(at=(1700, 350), z=3.6, title='探空', tag='UPPER AIR', value='12.8', unit='km', note='每分钟升约 300 m', icon='balloon',
         series=[0, 1.6, 3.3, 5.0, 6.8, 8.6, 10.6, 12.8], anchor=a_ball, accent='#e98bb4'),
    dict(at=(1560, 640), z=1.8, title='降水', tag='RAIN', value='0.6', unit='mm', note='近 1 小时累计', icon='rain',
         series=[0, 0, 0.1, 0.1, 0.3, 0.4, 0.5, 0.6], anchor=a_rain, accent='#6fa8e8'),
]
for c in cards:
    x, y, z = iso.unproject(*c['at'], z=c['z'])
    iso.card(x, y, z, 2.9, 1.65, facing='+x', title=c['title'], tag=c['tag'], value=c['value'], unit=c['unit'],
             note=c['note'], icon=c['icon'], series=c['series'], anchor=c['anchor'], accent=c['accent'])

# ---- title and caption, set flat on top
iso.text('ISLAND WEATHER STATION', 112, 118, 20, '#8a80b8', font='sans_bold', spacing=4.5)
iso.text('岛上的气象站', 108, 196, 70, INK)
iso.rule(112, 226, 176, 226, '#9d86e8', 4)
iso.text('风杆测风，百叶箱测温，雨量筒接雨，', 112, 272, 25, '#5b5782')
iso.text('探空气球把高空的数据发回来。', 112, 308, 25, '#5b5782')
iso.text('每 10 分钟记一次，经卫星天线回传', 112, 352, 19, '#8f88b0')
kx, ky, kz = iso.unproject(292, 858, iso.floor)
iso.compass(kx, ky, kz, r=0.95, north=(0, 1))                       # north is +y: the 10:40 sun stands in the south-east
iso.save(out, stages_dir=stages)
print('saved', out, f'{time.time() - t0:.1f}s')
