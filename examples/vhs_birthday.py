"""Example (VHS home video / VHS 家庭录像): 吹蜡烛 · Blow Out the Candles — one frame of a family's home video.
A 1970s living room (avocado-and-orange ring wallpaper, walnut panelling on the side wall, flowered drapes at a dusk
window, a console TV with rabbit ears, a rust velour sofa, gold shag carpet) is dressed for a birthday: crepe
streamers, a pennant string HAPPY BIRTHDAY, balloons tied to the TV, one escaped to the ceiling, a teddy bear guest
in a party hat. On the coffee table: the cake with six candles -- four just blown out and smoking, the last two
still bending away -- paper plates, striped cups, a blower, a present. The birthday child leans in over the cake,
seen from behind, out of focus right in front of the lens: whoever is filming stands just behind and is zooming in.
The camcorder is on 'outdoor' white balance under tungsten light (orange room, blue window); the candles and the
lamp clip, bloom, smear vertically and leave a short lag tail; the OSD is mixed in and goes on tape with the picture;
the tape adds chroma bleed, edge halos, noise, jitter, a tracking band, head-switching noise and dropouts.
Draw-on stages: walls -> window & furniture -> party -> cake -> child -> camera -> tape -> wear -> OSD.
python3 vhs_birthday.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from vhs import VHSCamcorder

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'vhs_birthday.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

# one-point perspective: camera 1.1 m up, back wall 4 m away
F, VX, VY, EYE = 1150.0, 1000.0, 430.0, 1.1


def P(X, Y, Z):
    return (VX + F * X / Z, VY - F * (Y - EYE) / Z)


v = VHSCamcorder(1920, 1080, seed=16, keep_stages=stages is not None)
v.ambient('#ffd9a8', 0.34)
v.light(1000, -260, 1500, '#ffe2b8', 0.12)                 # ceiling bounce

# ================================================================ 1. walls, ceiling, carpet
xb_l, y_ceil = P(-2.6, 2.4, 4.0); _, y_floor = P(0, 0, 4.0)
v.ceiling(v.poly([(0, -300), (1920, -300), (1920, y_ceil), (xb_l, y_ceil), (0, y_ceil - xb_l * 0.5)]))
back = v.rect(xb_l, y_ceil, 1920, y_floor)
v.wallpaper(back, tile=118, x0=xb_l, y0=y_ceil, contrast=0.72)
v.paint(v.rect(xb_l, y_floor - 22, 1920, y_floor), '#d9c9a2', form=0.3, form_r=4)          # baseboard
left = v.poly([(0, y_ceil - xb_l * 0.5), (xb_l, y_ceil), (xb_l, y_floor), (0, y_floor + xb_l * 0.423)])
v.paneling(left, [P(-2.6, 0, z)[0] for z in (4.0, 3.75, 3.5, 3.25, 3.02)])
v.shadow(v.rect(xb_l - 4, y_ceil, xb_l + 4, y_floor), 0.5, 10)                              # the corner
floor = v.poly([(0, y_floor + xb_l * 0.423), (xb_l, y_floor), (1920, y_floor), (1920, 1080), (0, 1080)])
v.shag(floor, '#c8962e')
v.shadow(v.rect(0, y_floor - 4, 1920, y_floor + 6), 0.35, 8)
v.stage('walls')

# ================================================================ 2. window, drapes, TV, lamp, sofa
wx0, wy0 = P(-2.25, 2.05, 4.0); wx1, wy1 = P(-1.15, 0.95, 4.0)
v.window(wx0, wy0, wx1, wy1)
v.light((wx0 + wx1) / 2, (wy0 + wy1) / 2, 360, '#86a2ff', 0.10)
v.rod(wx0 - 70, wx1 + 70, wy0 - 30)
v.curtain(wx0 - 66, wx0 + 44, wy0 - 30, wy1 + 70, folds=3, seed=4)
v.curtain(wx1 - 46, wx1 + 64, wy0 - 30, wy1 + 70, folds=3, seed=9)

tx0, ty0 = P(-0.6, 0.8, 3.55); tx1, ty1 = P(0.75, 0, 3.55)
v.console_tv(tx0, ty0, tx1, ty1)
v.rabbit_ears(tx1 - 90, ty0 - 8)
lx, lf = P(0.95, 0, 3.85)
v.floor_lamp(lx + 6, lf, 296, shade_w=124, shade_h=90)
v.sofa(1352, 2010, 500, 640, 712, 812, colour='#667c30')
v.stage('furniture')

# ================================================================ 3. party: streamers, pennants, balloons, teddy
v.streamer((xb_l + 10, y_ceil + 2), (1010, y_ceil - 8), 46, '#e8702a', width=18, twists=11)
v.streamer((1010, y_ceil - 8), (1925, y_ceil + 4), 52, '#3a7ad0', width=18, twists=12)
v.pennants((372, 92), (1858, 102), 84, 'HAPPY BIRTHDAY', ['#d83a2e', '#f2b51e', '#2f6fc8', '#4aa04a', '#e8702a'], size=96)
tie = (tx0 + 34, ty0 - 4)
for x, y, r, c, rot in ((880, 352, 50, '#d42a22', -12), (968, 300, 48, '#f2c21e', 6), (1052, 362, 46, '#2f6fc8', 14),
                        (920, 430, 44, '#3f9a3c', -4)):
    v.balloon(x, y, r, c, string_to=tie, sag=-14 if x < 930 else 18, rot=rot)
v.balloon(1724, 104, 44, '#e85a8c', rot=4)                                   # got away: pressed to the ceiling
v.paint(v.line([(1726, 160), (1716, 260), (1730, 360), (1722, 450)], 1.6), '#d9d2c4', 0.8)
v.teddy(1574, 560, 46, fur='#b0743a')
v.stage('party')

# ================================================================ 4. the table: cake, plates, cups, present
q = [P(-0.7, 0.42, 2.2), P(1.1, 0.42, 2.2), P(1.1, 0.42, 1.6), P(-0.7, 0.42, 1.6)]
v.coffee_table(q, thick=28, legs=[(560, 948, 1080), (1735, 948, 1080)], gloss=(1330, 808))
v.plates(812, 840, 74, 20)
v.blower(1000, 902, colour='#2f6fc8')
v.cup(1372, 842, 46, 64, '#d23a2e')
v.cup(1442, 880, 48, 66, '#2f6fc8')
v.present(1500, 772, 118, 82, 52)
v.confetti((560, 800, 1700, 930), n=70)
cx, ctop = P(0.2, 0.53, 1.95)
candles = [(150, '#e8702a', 1.0), (90, '#2f6fc8', 0.9), (210, '#d83a2e', 0.8), (30, '#4aa04a', 0.7),
           (270, '#f2b51e', 'lit'), (330, '#e85a8c', 'lit')]
tips = v.cake(cx, ctop, 110, 33, 68, candles, sprinkles=['#e04848', '#f2c230', '#3a8ad8', '#5cb85c'], lean=(1.0, -0.2))
for x, y in tips:
    v.light(x, y, 280, '#ffa048', 0.3)
    v.glow(v.ellipse(x - 10, ctop + 110, 300, 70), '#ff9a40', 0.12)
v.stage('cake')

# ================================================================ 5. the birthday child, out of focus in front of the lens
with v.layer(defocus=4.5):
    v.child_back(668, 600, 92, lean=24, glow_from=(cx + 20, ctop - 40))
v.stage('child')

# ================================================================ 6-8. camcorder, tape, playback wear
v.camera(tilt=-1.6, white_balance=(1.06, 0.95, 0.74), exposure=1.07, knee=0.74, lag=(-24, 0, 0.3))
v.stage('camera')
v.record()
v.stage('tape')
v.wear(tracking=(0.94, 0.04))
v.stage('wear')

# ================================================================ 9. the camcorder's OSD (mixed into the signal before the tape)
v.rec(150, 100)
v.battery(150, 178, px=7, level=1)
v.counter('0:14:32', 1770, 100)
v.datestamp('7:42 PM', 'JUN.16.1984', 150, 864)
v.zoom_bar(1300, 934, pos=0.72, px=7, width=300)
v.save(out, stages_dir=stages)
print(f'{out}  {time.time() - t0:.1f}s')
