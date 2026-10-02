"""Example (illuminated manuscript / 泥金手抄本): 星辰之书 · Liber Stellarum — an opening of a (fictional) early-15th-
century astronomy book lying on a dark desk. It teaches two small things. Left leaf: the order of the planets -- a
historiated initial Q (rose letter with white-lead tracery on tooled burnished gold; in its counter a night sky, a
crescent moon and an observatory tower on a hill), a textura column in iron-gall ink with vermilion rubrics, a gold /
azure / rose bar border sprouting ivy sprays, and a roundel of the spheres: the earth as a T-O map, the seven planets
on a spiral with their names written round the rings, the azure sphere of the fixed stars in a gold frame. Right leaf:
how to take the altitude of a star -- a blue penwork initial O with red filigree, and an astrolabe drawn with
compass and rule (a real stereographic plate for latitude 48, shell-gold rete and limb), its rule sighted along a red
dotted line to a gilded star in the margin, the angle marked "xl gradus".
Draw-on stages follow the workshop: vellum -> ruling -> scribe -> rubricator -> diagrams -> gilder -> painter -> pen.
No image model.
python3 illuminated_starchart.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from illuminated import Illuminated

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'illuminated_starchart.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
t0 = time.time()

il = Illuminated(1920, 1080, seed=14)
XH, LEAD = 18, 50                      # x-height and line pitch of the main hand
TOP = 140                              # first baseline

# ---- the book: two leaves of hair-side vellum, a flaw hole the scribe wrote round
il.desk()
(L0, LY0, L1, LY1), (R0, RY0, R1, RY1) = il.codex(200, 40, 1720, 1040)
il.flaw(1655, 985, 9, 5.5, rot=12)

# ---- ruling: prickings in the outer margins, a ruled line at every x-height; the far side shows through
LX0, LX1 = 350, 885                    # left text column
RX0, RX1 = 1035, 1570                  # right text column
ys = [TOP - XH + LEAD * i for i in range(17)]
il.show_through(LX0, LX1, [TOP + LEAD * i for i in range(17)], XH, opacity=0.03)
il.show_through(RX0, RX1, [TOP + LEAD * i for i in range(17)], XH, opacity=0.03)
il.rule(LX0, LX1, ys, prick_x=214)
il.rule(RX0, RX1, ys, prick_x=1706)
il.stage('vellum')

# ---- left leaf: the order of the planets
PANEL = 4 * LEAD + XH + 12
left = il.column(
    '*incipit liber de ordine planetarum.* | '
    'uoniam planete circa terram mouentur, ordinem eorum hic breuiter describimus. '
    '^prima est luna, deinde mercurius et uenus, in medio sol; postea mars, iupiter et saturnus tardus. '
    '^super omnes est firmamentum stellarum fixarum, ut in hac figura patet. |',
    LX0, LX1, TOP, XH, LEAD, indent=[(1, LX0), (5, LX0 + PANEL + 14)])
q = il.initial('Q', LX0, TOP + LEAD - XH - 6, PANEL)
orbs = il.spheres(618, 805, 178)

# ---- right leaf: the altitude of a star
right = il.column(
    '*de altitudine stelle per astrolabium.* | '
    'stendit hec figura quomodo altitudo stelle inuenitur. ^suspende astrolabium ꝑ anulum ut pendeat recte, '
    '7 uide stellam per ambo foramina regule; postea numera gradus in limbo ab orizonte: *hic sunt xl gradus.* |',
    RX0, RX1, TOP, XH, LEAD, indent=[(1, RX0), (2, RX0 + 2 * LEAD - 18)])
coda = il.column('^nota quod in nocte serena melius uidentur. |', RX0, RX1, TOP + 16 * LEAD, XH, LEAD)
o = il.versal('O', RX0, TOP + LEAD - XH - 8, 2 * LEAD - 30, reach=(70, 120))
ACX, ACY, AR = 1262, 700, 180
astro = il.astrolabe(ACX, ACY, AR, lat=48, rete=24, rule=40,
                     star=(ACX + 2.28 * AR * np.cos(np.radians(40)), ACY - 2.28 * AR * np.sin(np.radians(40))))
border = il.border([(282, 92), (282, 985)], width=12, seed=5, every=88,
                   avoid=[(LX0, TOP - XH - 30, LX1, TOP + 8 * LEAD + 12), (436, 623, 800, 987)],
                   bounds=(L0 + 6, LY0 + 6, LX1, LY1 - 8))

# ---- the scribe: black text, leaving the rubrics and the initials blank
il.scribe(left)
il.scribe(right)
il.scribe(coda)
il.write('xxiij', 1648, 96, 13, 'iron', load=0.7)          # folio number, upper outer corner
il.stage('text')

# ---- the rubricator
il.rubricate(left)
il.rubricate(right)
il.rubricate(coda, blue_first=True)
il.stage('rubrics')

# ---- the draftsman: compass work in brown ink
orbs.draw()
astro.draw()
il.stage('diagrams')

# ---- the gilder: gold first, before any paint
q.gild()
border.gild()
orbs.gild()
astro.gild()
il.stage('gold')

# ---- the painter
q.paint()
border.paint()
orbs.paint()
astro.paint()
o.paint()
il.stage('colours')

# ---- pen work: outlines, white tracery, ivy sprays, filigree, labels
q.pen()
border.pen()
orbs.pen()
o.pen()
sx, sy = astro.star_xy
astro.pen(labels=[('anulus', (RX0 + 8, 452), (ACX - 0.13 * AR, ACY - 1.36 * AR)),
                  ('rete', (RX0 + 8, 590), (ACX - 0.60 * AR, ACY - 0.42 * AR)),
                  ('limbus', (RX0 + 8, 820), (ACX - 0.85 * AR, ACY + 0.45 * AR)),
                  ('regula', (RX0 + 8, 900), (ACX - 0.72 * AR, ACY + 0.62 * AR)),
                  ('orizon', (ACX + 1.36 * AR, ACY + 5), (ACX + 1.3 * AR, ACY)),
                  ('xl gradus', (ACX + 1.20 * AR, ACY - 0.22 * AR), (ACX + 1.16 * AR, ACY - 0.2 * AR)),
                  ('stella', (sx + 30, sy + 6), (sx + 26, sy))], xh=12)
il.stage('penwork')

# ---- six hundred years
il.age(foxing=36)
il.save(out, stages)
print(out, f'{time.time() - t0:.1f}s')
