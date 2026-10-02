"""Example (Soviet constructivism / 苏联构成主义): РАДИО · Radio -- the cover poster of a (fictional) 1920s magazine
for radio amateurs, printed in red and black. It diagrams one small thing: how a broadcast reaches you.
① a hyperboloid lattice radio tower, photographed from below (the transmitter), ② its waves running down a red
wedge as concentric fronts that thin out as they spread, ③ a valve receiver with a horn loudspeaker, cut out of a
photograph with scissors, the horn's bell catching the end of the wedge. A red disc behind the tower, a black diagonal slab with СЛУШАЙТЕ ВЕСЬ МИР ("listen to
the whole world") reversed out, the title РАДИО in heavy condensed grotesque, numbered labels, price and the
printer's imprint; then a century of folds, foxing and pin holes.
Draw-on stages: paper -> red plate -> waves -> black slab -> tower photo -> receiver photo -> title -> labels
-> age.
No image model; the two "photographs" are rendered meshes screened into a 45-degree halftone.
python3 constructivism_radio.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from constructivism import Constructivism, Photo

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'constructivism_radio.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

c = Constructivism(1920, 1080, seed=26, misreg=2.6)


# ---------------------------------------------------------------- photo 1: the lattice tower, from below
def tower_photo():
    a = np.deg2rad(235)
    d = 104
    eye = np.array((d * np.cos(a), d * np.sin(a), 1.7))
    p = Photo(900, 1080, eye=eye, target=(0, 0, 84), fov=46, ss=2, seed=4, key=(-0.55, -0.2, 0.75),
              fill=(0.6, -0.5, 0.2), key_k=0.8, fill_k=0.3, amb=0.3, haze=2600, haze_tone=0.85, shift=(0, -0.11),
              grain=0.02)
    cam = eye[:2] / np.linalg.norm(eye[:2])

    def far_side(pos, n):                     # the far half of the lattice, seen through the near half, is paler
        f = (pos[:, 0] * cam[0] + pos[:, 1] * cam[1]) / (np.hypot(pos[:, 0], pos[:, 1]) + 1e-6)
        return 1 + 5.5 * (1 - np.clip((f + 0.3) / 0.6, 0, 1))

    steel = p.material(albedo=0.11, gloss=0.12, shine=14, tex=far_side)
    R = [20, 15.2, 11.6, 8.9, 6.9, 5.4, 4.3]                   # ring radii at the joints of the six sections
    N = [16, 14, 12, 10, 9, 8]                                  # members per family, thinned out toward the top
    for k in range(6):
        p.hyperboloid(25 * k, 25 * (k + 1), R[k], R[k + 1], N[k], 360 / N[k] * 3, steel, member=0.55 - 0.055 * k,
                      rings=3 if k < 3 else 2, ring_member=0.36 - 0.03 * k, phase=7 * k)
    p.cylinder((0, 0, 150), (0, 0, 168), 0.45, steel, sides=8, r1=0.22)          # the mast on top
    for z, L in ((154, 3.4), (159, 2.6), (164, 1.8)):
        p.cylinder((-L, 0, z), (L, 0, z), 0.16, steel, sides=5)
    return p, p.project([(0, 0, 168)])


# ---------------------------------------------------------------- photo 2: a valve receiver with a horn speaker
def receiver_photo():
    p = Photo(760, 700, eye=(-0.7, -1.75, 0.95), target=(-0.25, 0, 0.36), fov=40, ss=2, seed=7,
              key=(-0.6, -0.55, 0.6), fill=(0.8, -0.3, 0.15), key_k=1.0, fill_k=0.35, amb=0.3, grain=0.025)
    X0, X1, Y0, Y1, ZT = -0.34, 0.34, -0.15, 0.15, 0.2

    def wood(pos, n):
        x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
        u = np.where(np.abs(n[:, 2]) > 0.7, y, z)
        g = np.sin(2 * np.pi * (u * 23 + 0.6 * np.sin(x * 7 + u * 31) + 0.25 * np.sin(x * 23)))
        return 0.9 + 0.1 * g * (0.6 + 0.4 * np.sin(x * 5 + u * 3))

    def scale(cx, cz, r0, r1):                     # white engraved ticks on black bakelite, every 3rd long
        def tex(pos, n):
            dx, dz = pos[:, 0] - cx, pos[:, 2] - cz
            r = np.hypot(dx, dz)
            ang = np.degrees(np.arctan2(dz, dx)) % 360
            arc = (ang < 200) | (ang > 340)
            tick = (np.abs(((ang + 2.5) % 10) - 2.5) < 1.0) & (r > r1 - 0.012) & (r < r1 - 0.002) & arc
            big = (np.abs(((ang + 2.5) % 30) - 2.5) < 1.4) & (r > r0) & (r < r1 - 0.002) & arc
            return np.where(tick | big, 9.0, 1.0)
        return tex

    def valve(pos, n):
        z = pos[:, 2]
        return np.where((z > ZT + 0.06) & (z < ZT + 0.105), 0.35, 1.0) * np.where(z > ZT + 0.13, 0.6, 1.0)

    def coil(pos, n):                              # honeycomb winding: criss-cross wire
        a = np.arctan2(pos[:, 1] - 0.06, pos[:, 0] - 0.24)
        z = pos[:, 2]
        w = np.sin(a * 18 + z * 520) * np.sin(a * 18 - z * 520)
        return 0.75 + 0.25 * np.sign(w)

    wood_m = p.material(albedo=0.4, gloss=0.12, shine=12, tex=wood)
    ebon = p.material(albedo=0.06, gloss=0.4, shine=40)
    dial = p.material(albedo=0.08, gloss=0.5, shine=40, tex=scale(-0.14, 0.11, 0.05, 0.078))
    knob = p.material(albedo=0.07, gloss=0.6, shine=50)
    nickel = p.material(albedo=0.7, gloss=0.5, shine=60, metal=0.85)
    brass = p.material(albedo=0.45, gloss=0.35, shine=30, metal=0.5, interior=0.4)
    japan = p.material(albedo=0.1, gloss=0.5, shine=40)
    glass = p.material(albedo=0.42, gloss=1.0, shine=90, tex=valve)
    ivory = p.material(albedo=0.8, gloss=0.2, shine=30)
    coil_m = p.material(albedo=0.55, gloss=0.1, shine=10, tex=coil)

    p.box((X0, Y0, 0.0), (X1, Y1, ZT), wood_m)                                    # the cabinet
    p.box((X0 - 0.015, Y0 - 0.015, ZT - 0.004), (X1 + 0.015, Y1 + 0.015, ZT + 0.014), wood_m)   # its lid
    p.box((X0 + 0.03, Y0 - 0.008, 0.022), (X1 - 0.03, Y0, ZT - 0.022), ebon)      # ebonite front panel
    F = Y0 - 0.008                                                                 # panel front face
    # the big tuning dial: nickel bezel, black bakelite scale with white ticks, fluted knob; ivory pointer above
    p.lathe((-0.14, F, 0.11), (0, -1, 0), [(0, 0.084), (0.004, 0.086), (0.008, 0.08)], nickel, sides=56, cap=False)
    p.lathe((-0.14, F, 0.11), (0, -1, 0), [(0, 0.079), (0.006, 0.079)], dial, sides=56)
    p.lathe((-0.14, F - 0.006, 0.11), (0, -1, 0), [(0, 0.032), (0.008, 0.034), (0.03, 0.03), (0.038, 0.024),
                                                     (0.042, 0.0)], knob, sides=28)
    p.box((-0.146, F - 0.006, 0.192), (-0.134, F, 0.2), ivory)
    for cx, cz in ((0.06, 0.135), (0.17, 0.135)):                                  # two small knobs
        p.lathe((cx, F, cz), (0, -1, 0), [(0, 0.03), (0.003, 0.031), (0.006, 0.0)], nickel, sides=32)
        p.lathe((cx, F - 0.005, cz), (0, -1, 0), [(0, 0.02), (0.006, 0.021), (0.022, 0.018), (0.026, 0.0)],
                knob, sides=24)
    p.box((0.03, F - 0.004, 0.052), (0.1, F, 0.068), ivory)                         # makers' plate
    for k in range(4):                                                             # terminal posts
        x = 0.16 + 0.03 * k
        p.lathe((x, F, 0.06), (0, -1, 0), [(0, 0.009), (0.012, 0.009), (0.014, 0.012), (0.022, 0.012),
                                            (0.024, 0.0)], brass, sides=14)
    for x in (-0.22, -0.1, 0.02):                                                  # three valves on top
        p.cylinder((x, 0.0, ZT + 0.014), (x, 0.0, ZT + 0.036), 0.026, knob, sides=20, cap=True)
        p.lathe((x, 0.0, ZT + 0.036), (0, 0, 1), [(0, 0.017), (0.012, 0.02), (0.03, 0.03), (0.06, 0.032),
                                                   (0.085, 0.028), (0.1, 0.016), (0.108, 0.007), (0.114, 0.0)],
                glass, sides=28)
    p.lathe((0.24, 0.06, ZT + 0.014), (0, 0, 1), [(0, 0.0), (0.0, 0.07), (0.03, 0.07), (0.03, 0.0)], coil_m, sides=40)
    # horn
    bx, by = -0.5, 0.07
    p.lathe((bx, by, 0.0), (0, 0, 1), [(0, 0.1), (0.014, 0.1), (0.026, 0.088), (0.032, 0.05), (0.085, 0.046),
                                        (0.1, 0.03), (0.105, 0.0)], japan, sides=36)
    d = np.array([-0.75, -0.2, 0.55]); d /= np.linalg.norm(d)
    P0 = np.array([bx, by, 0.1]); P1 = P0 + [0, 0, 0.26]; P3 = P0 + [0, 0, 0.36] + d * 0.26; P2 = P3 - d * 0.16
    s = np.linspace(0, 1, 110)[:, None]
    path = (1 - s) ** 3 * P0 + 3 * (1 - s) ** 2 * s * P1 + 3 * (1 - s) * s ** 2 * P2 + s ** 3 * P3
    t = s[:, 0]
    rad = np.where(t < 0.45, 0.016 + 0.006 * t,
                   0.0187 * np.exp(np.log(0.19 / 0.0187) * np.clip((t - 0.45) / 0.55, 0, 1) ** 1.7))
    p.sweep(path, rad, brass, sides=40)
    p.lathe(P3 - d * 0.005, d, [(0, 0.186), (0.005, 0.197), (0.01, 0.19)], brass, sides=56, cap=False)
    # the flex from the horn to the terminals
    c0 = np.array([bx + 0.06, by - 0.05, 0.01]); c3 = np.array([X0 + 0.01, -0.02, 0.05])
    s = np.linspace(0, 1, 40)[:, None]
    cord = (1 - s) ** 2 * c0 + 2 * (1 - s) * s * (np.array([(c0[0] + c3[0]) / 2, -0.2, -0.02])) + s ** 2 * c3
    p.sweep(cord, np.full(40, 0.006), japan, sides=10)
    return p, p.project([P3])


# ---------------------------------------------------------------- the sheet
c.paper()
c.stage('paper')

tp, (tx, ty, _) = tower_photo()
TCX, TCY = 400, 540                                   # where the tower photo is centred on the poster
TIP = (TCX - 450 + float(tx[0]), TCY - 540 + float(ty[0]))

rp, (hx, hy, _) = receiver_photo()
RCX, RCY, RROT, RS = 1500, 560, 10.5, 1.16            # the receiver photo: centre, tilt (= the slab's), scale
t = np.deg2rad(RROT)
u, v = (float(hx[0]) - 380) * RS, (float(hy[0]) - 350) * RS
BELL = (RCX + u * np.cos(t) + v * np.sin(t), RCY - u * np.sin(t) + v * np.cos(t))   # the horn's mouth on the poster
REACH = float(np.hypot(BELL[0] - TIP[0], BELL[1] - TIP[1]))

# ---- red plate: the disc behind the tower, the wedge of the broadcast from the mast to the horn
c.ink(c.circle(TCX + 12, 330, 222), 'red')
BEAM = -np.degrees(np.arctan2(BELL[1] - TIP[1], BELL[0] - TIP[0]))
c.ink(c.wedge(TIP, BEAM, 5.6, REACH + 20), 'red')
S0, S1 = (470, 1052), (1990, 772)                     # the slab's axis (printed in black later)
ang = np.degrees(np.arctan2(S0[1] - S1[1], S1[0] - S0[0]))
c.ink(c.poly([c.along(S0, ang, a, b) for a, b in ((930, 0), (1700, 0), (1700, 410), (930, 410))]), 'red')
c.stage('red')

# ---- waves: fronts radiating from the mast, black over the red, thinning as they spread, ending at the horn
c.waves(TIP[0], TIP[1], 120, REACH - 60, 76, 12, BEAM - 9, BEAM + 6.5, plates=('black',), grow=-0.045)
c.stage('waves')

# ---- the black slab rising under the receiver, the line reversed out of it
mid = c.along(S0, ang, 600, 0)
slab = c.bar(S0[0], S0[1], S1[0], S1[1], 112)
c.ink(slab, 'black', knock=c.text_mask('СЛУШАЙТЕ ВЕСЬ МИР', mid[0], mid[1], 66, 'grotesk', anchor='mm',
                                         spacing=5, rot=ang))
c.knock(slab, 'red')
c.stage('slab')

# ---- photo 1: tower, retouched out of its sky, printed over the red
c.montage(tp, TCX, TCY, cell=5.5, contrast=1.1, soften=0.12)       # thin blur keeps the lattice open
c.stage('tower')

# ---- photo 2: receiver, cut out with scissors, standing on the slab
c.montage(rp, RCX, RCY, rot=RROT, scale=RS, cut=13, close=16, cell=5.5, contrast=1.2)
c.stage('receiver')

# ---- type
c.text('ЖУРНАЛ ДЛЯ РАДИОЛЮБИТЕЛЕЙ  ·  № 7  ·  1926', 1868, 74, 30, 'black', 'din', anchor='rs', spacing=2)
c.text('ЦЕНА 15 КОП.', 1868 - c.text_width('ЖУРНАЛ ДЛЯ РАДИОЛЮБИТЕЛЕЙ  ·  № 7  ·  1926', 30, 'din', 2) - 40, 74, 30, 'red',
       'din', anchor='rs', spacing=2)
c.text('РАДИО', 1868, 300, 268, 'black', anchor='rs', wobble=0.7)
c.ink(c.bar(1300, 332, 1868, 332, 7), 'black')
c.stage('title')


def label(n, text, x, y, rot=0.0, plate='black'):
    """a numbered label: the number reversed out of a black square, the word beside it; (x, y) = bottom-left"""
    sq = c.poly([c.along((x, y), rot, a, b) for a, b in ((0, 0), (46, 0), (46, 46), (0, 46))])
    cx, cy = c.along((x, y), rot, 23, 23)
    c.ink(sq, 'black', knock=c.text_mask(n, cx, cy, 40, 'din', anchor='mm', rot=rot))
    lx, ly = c.along((x, y), rot, 60, 5)
    c.text(text, lx, ly, 40, plate, 'din', spacing=1.5, rot=rot)


label('1', 'ПЕРЕДАТЧИК', 640, 600)
wx, wy = c.along(TIP, BEAM, 400, -175)
label('2', 'ВОЛНА 1450 М', wx, wy, rot=BEAM)
lx, ly = c.along(S0, ang, 1060, 330)
label('3', 'ПРИЁМНИК', lx, ly, rot=ang)
# the contents of the issue, a small block of type in the open field
for k, line in enumerate(['В НОМЕРЕ:', 'ДЕТЕКТОРНЫЙ ПРИЁМНИК', 'АНТЕННА НА КРЫШЕ', 'ЛАМПЫ И БАТАРЕИ']):
    y = 750 + k * 40
    if k:
        c.ink(c.rect(642, y - 22, 658, y - 6), 'red')
    c.text(line, 640 + (30 if k else 0), y, 30, 'black', 'din', spacing=1.2)
c.text('ТИП. № 3  ·  ТИРАЖ 5000 ЭКЗ.', 30, 1040, 17, 'black', 'din', anchor='ls', spacing=1.5, rot=90)
c.stage('labels')

# ---- a hundred years later
c.age(folds=(1, 1))
c.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s')
