"""Example (exam grading): 数学单元测验 · Unit Test, Graded — a primary-school maths quiz being marked on a green
felt desk. The answer sheet (two more sheets under it) is a printed form: timing marks, a heavy title, name and class
fields, a ticket number with its bubbles filled, a score / grader table, section one (three sums in a row) and
section two (a word problem in a tinted box, an answer box with ruled lines and a hatched grading column). On the
left, the answer key is clipped to a card with a black binder clip, and a slip gives the marking scheme.

The candidate writes the answers line by line in blue-black. Two rubber stamps land in the grading column (书写工整
✓, 列式正确 ✓): the set-up of the word problem is right. Then the red pen ticks the three sums, finds the slip in
128 ÷ 16 = 6: a wavy underline, a ring round 6（天）, a leader out to the grading column, the note 应为 8 天 and a
cross; it underlines the 6 in the answer sentence too, ticks ① and crosses ② on the key, and writes 75 in the score
box, circled.
No image model.
python3 grading_math_quiz.py [out.jpg] [--stages DIR]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from grading import Grading, INK, GRAY, NAVY, PAPERS

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'grading_math_quiz.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
T0 = time.time()
tick = lambda name: print(f'{name:16s} {time.time() - T0:5.1f}s') if os.environ.get('GRADING_TIMING') else None

W, H = 1920, 1080
g = Grading(W, H, seed=7, keep_stages=bool(stages), stages_dir=stages)
g.desk()
tick('desk')

# ===================================================================== the answer sheet (printed)
CX0, CX1, COL = 664, 1790, 1504
s = g.sheet(596, 28, 1250, 1110, stack=2)
s.corner_mark(612, 46); s.corner_mark(1806, 46)
s.timing_track(612, 104, 1130)
s.title('数学单元测验', CX0, 112, 50, sub='UNIT TEST · GRADE 3 · FORM A')
s.field('姓名', '林小禾', CX0, 214, 900)
s.field('班级', '三（2）班', 930, 214, 1118)
s.text('单元', CX0, 268, 19, 'body', GRAY)
s.text('第四单元 · 除法', CX0 + 54, 267, 22, 'body', INK)
s.line([(CX0 + 48, 278), (1118, 278)], 1.0, INK, 0.55)
s.ticket(1150, 98, '30215')
SCORE = s.score_box(1440, 64, note='满分 100', lines=('计算 ×3', '应用 ×1'))
s.fill_example(1440, 268)
s.line([(CX0, 298), (CX1, 298)], 2.2); s.line([(CX0, 303), (CX1, 303)], 0.8)

# section one: three sums in a row
s.section(CX0, 318, '一', '计算题', '每题 25 分')
SUMS = [('① 23 × 4 =', '92'), ('② 156 ÷ 3 =', '52'), ('③ 7 × 8 =', '56')]
SUM_X = [690, 1060, 1430]
SUM_Y = 410
sum_ans = []
for (q, a), x in zip(SUMS, SUM_X):
    end = s.text(q, x, SUM_Y, 32, 'body', INK)
    s.line([(end + 8, SUM_Y + 12), (end + 108, SUM_Y + 12)], 1.0, '#486880', 0.5)
    sum_ans.append((end + 22, a))

# section two: a word problem, an answer box with a grading column
s.section(CX0, 448, '二', '应用题', '25 分', meta='写出算式和答句', x1=CX1)
s.question(CX0, 494, CX1, 552, '一本书 128 页，每天读 16 页，几天能读完？', 30)
FY0, FY1 = 572, 924
LINES = [668, 762, 856]
s.answer_frame(CX0, FY0, CX1, FY1, col=COL, lines=[b + 12 for b in LINES],
               rows=[('批注', 630, 716), ('书写', 738, 820), ('列式', 842, None)])
s.text('第 1 页 · 共 2 页', (CX0 + CX1) / 2, 984, 15, 'body', GRAY, anchor='ms', spacing=2)
tick('sheet')

# ===================================================================== the answer key card and the slip
KX, KY, KW, KH = 70, 112, 506, 392
key = g.card(KX, KY, KW, KH, rot=-1.3)
key.band(KX, KY, KX + KW, KY + 96, NAVY)
key.text('标准答案', KX + 32, KY + 66, 46, 'heavy', mode='knock', spacing=4)
key.text('ANSWER KEY', KX + KW - 30, KY + 44, 13, 'latin', mode='knock', anchor='rs', spacing=3.5, alpha=0.75)
key.text('第二题', KX + KW - 30, KY + 74, 18, 'body', mode='knock', anchor='rs', spacing=1, alpha=0.85)
key.text('要 点', KX + 32, KY + 140, 19, 'bold', GRAY, spacing=4)
key.line([(KX + 32, KY + 156), (KX + KW - 32, KY + 156)], 1.0, INK, 0.25)
KEY_ROWS = [('列式  128 ÷ 16', KY + 206), ('得数  8 天', KY + 274)]
for i, (t, y) in enumerate(KEY_ROWS):
    key.circled(i + 1, KX + 52, y - 10)
    key.text(t, KX + 82, y, 30, 'bold', INK)
    key.checkbox(KX + KW - 74, y - 28, 30)
key.line([(KX + 32, KY + 322), (KX + KW - 32, KY + 322)], 1.2, GRAY, 0.5, dash=(5, 5))
key.text('验算', KX + 32, KY + 362, 20, 'body', GRAY)
key.text('16 × 8 = 128', KX + 86, KY + 362, 22, 'bold', INK)

SX, SY, SW, SH = 86, 590, 484, 182
slip = g.card(SX, SY, SW, SH, tint=PAPERS['slip'], rot=0.9)
slip.text('评分', SX + 26, SY + 46, 20, 'bold', INK, spacing=6)
slip.line([(SX + 26, SY + 64), (SX + SW - 26, SY + 64)], 1.0, INK, 0.25)
slip.text('每题 25 分', SX + 26, SY + 128, 44, 'heavy', INK, spacing=2)
slip.text('满分 100', SX + SW - 26, SY + 126, 20, 'body', GRAY, anchor='rs')
tick('cards')

# ===================================================================== what gets written
ans = [s.answer(a, x, SUM_Y, 32) for x, a in sum_ans]
EQ = '128 ÷ 16 =  6（天）'                              # a child's gap before the result
L1 = s.answer(EQ, 690, LINES[0], 34)
L2 = s.answer('答：6 天能读完。', 690, LINES[1], 34)
writing = ans + [L1, L2]

ST1 = s.stamp(1646, 780, '书写工整', h=60, size=28, rot=-2.5)
ST2 = s.stamp(1649, 884, '列式正确', h=60, size=28, rot=1.8)

x6a = 690 + s.width('128 ÷ 16 =  ', 34); x6b = 690 + s.width(EQ, 34)
ticks = [s.check(x + s.width(a, 32) + 34, SUM_Y - 12, 30) for x, a in sum_ans]
wave = s.wave(x6a + 2, x6b - 8, LINES[0] + 13)
ring = s.ring((x6a + x6b) / 2 + 3, LINES[0] - 11, (x6b - x6a) / 2 + 15, 31)
NOTE = (1524, 686)
lead = s.leader(ring.tip(1.0), (NOTE[0] - 10, NOTE[1] - 14), bend=36)
note = s.note('应为 8 天', NOTE[0], NOTE[1], 32)
cross = s.cross(1750, 672, 20)
u6 = s.underline(690 + s.width('答：', 34) - 2, 690 + s.width('答：6', 34) + 4, LINES[1] + 10)
kc = key.check(KX + KW - 58, KY + 206 - 16, 30)
kx = key.cross(KX + KW - 59, KY + 274 - 13, 11, width=3.0)
score = s.score('75', SCORE[0] - 14, SCORE[1] + 10, 62)
red = ticks + [wave, ring, lead, note, cross, u6, kc, kx, score]
tick('marks')
REST = (1648, 238)                                     # where the pen is put down at the end

if not stages:
    # ================================================================= just the finished picture
    g.place(s); g.place(key); g.place(slip)
    key.clip(KX + 250, KY + 2)
    for st in (ST1, ST2): st.progress = 1.0
    g.pen(*REST, lift=0.45)
    img = g.save(out)
    tick('saved')
    print('saved', out)
    sys.exit()

# ===================================================================== stage by stage (for the drawing GIF)
# names: 'x~...' are motion frames (shown briefly, no cross-fade), '@ms' sets how long a stage is held
for m in writing + red: m.progress = 0.0
for st in (ST1, ST2): st.progress = 0.0
g.stage('desk')
# the answer sheet comes down onto the felt
g.place(s, 1.0, -36, -64, -2.6); g.stage('sheet_up@260')
for k, (l, dx, dy, r) in enumerate([(0.55, -18, -30, -1.3), (0.2, -6, -10, -0.4)]):
    g.place(s, l, dx, dy, r); g.stage(f'sheet~{k}@80')
g.place(s); g.stage('sheet')
# the key card and the slip, then the clip
g.place(slip, 1.0, 30, 40, 3.0); g.place(key, 1.0, -40, -60, -3.5); g.stage('cards_up@260')
for k, l in enumerate((0.55, 0.2)):
    g.place(key, l, -40 * l, -60 * l, -3.5 * l); g.place(slip, l, 30 * l, 40 * l, 3.0 * l); g.stage(f'cards~{k}@80')
g.place(key); g.place(slip); g.stage('cards')
key.clip(KX + 250, KY + 2); g.stage('clip@600')
# the answers, line by line
for i, m in enumerate(writing):
    for k, p in enumerate((0.5,) if len(m.path[0]) < 6 else (0.34, 0.67)):
        m.progress = p; g.stage(f'ans{i}~{k}@110')
    m.progress = 1.0; g.stage(f'ans{i}@420')
# two stamps, one after the other: down, press, up
for i, st in enumerate((ST1, ST2)):
    for k, h in enumerate((0.9, 0.45)):
        g.stamper(st, h); g.stage(f'stamp{i}~down{k}@{110 if k == 0 else 70}')
    g.stamper(st, 0.0); g.stage(f'stamp{i}~press@360')
    g.stamper(st, 0.5); g.stage(f'stamp{i}~up@90')
    g.stamper(None); g.stage(f'stamp{i}@650')
for st in (ST1, ST2): st.wet = 0.0


# the red pen: travels lifted between marks, writes each one
def canvas_of(m, p):
    paper = m.paper if hasattr(m, 'paper') else m.parts[0].paper
    return paper.to_canvas(*m.tip(p))


def travel(m, name, n=1, ms=80, frm=None):
    x0, y0 = frm if frm else g._pen[:2]
    x1, y1 = canvas_of(m, 0.0)
    for k in range(1, n + 1):
        u = k / (n + 1)
        g.pen(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, lift=0.45 * np.sin(np.pi * u) + 0.08); g.stage(f'{name}~mv{k}@{ms}')


def draw(m, n, name, ms=70):
    for k in range(1, n + 1):
        g.write(m, k / n); g.stage(f'{name}~{k}@{ms}')


plan = [(ticks[0], 3, 'tick0'), (ticks[1], 3, 'tick1'), (ticks[2], 3, 'tick2'), (wave, 6, 'wave'), (ring, 9, 'ring'),
        (lead, 4, 'lead'), (note, 7, 'note'), (cross, 4, 'cross'), (u6, 2, 'under'), (kc, 3, 'keytick'), (kx, 3, 'keycross'),
        (score, 14, 'score')]
frm = (2060, 1180)
for i, (m, n, name) in enumerate(plan):
    travel(m, name, n=2 if i in (0, 9, 11) else 1, frm=frm); frm = None
    draw(m, n, name)
    if name in ('ring', 'note', 'cross', 'score'):
        g.stage(f'{name}_done@500')
g.pen(*REST, lift=0.45)
img = g.save(out, stages_dir=stages)
tick('saved')
print('saved', out)
