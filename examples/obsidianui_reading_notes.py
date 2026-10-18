"""Example (Obsidian UI): 小王子 · 读书笔记 / Reading Notes — a dark note-taking app window with one book's notes.

A near-black page with a soft violet glow; on it the app window: tab bar (小王子 · 狐狸), icon ribbon, a file explorer
(the folder 2026 读书 open, the note 小王子 highlighted), the note pane and a right sidebar. In the note: the H1 「小王子」
with a short violet bar, a properties block (#童话 #读书笔记, the date it was finished), two lines of body text with
internal links in violet, **bold** and `inline code`; a ```mermaid block typed line by line -- a click flips the note
from 源码 to 阅读 and the block renders as a flowchart, 陌生 -花时间-> 驯养 -> 彼此需要 -> 独一无二, with 驯养 lit violet;
then the fox's line in a quote callout. In the sidebar the local graph: grey nodes and links for the book's
characters and places, the four notes linked from this one (小王子, 狐狸, 玫瑰, 驯养) lit violet with a soft glow, and the
backlinks under it; a status bar in the corner. One accent (violet), everything else greys. No logos, no image model.
python3 obsidianui_reading_notes.py [out.jpg] [--stages DIR] [--accent violet|blue|teal|amber|rose]
"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from obsidianui import ObsidianUI, BORDER, TEXT, BRIGHT, MUTED, FAINT

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'obsidianui_reading_notes.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None
ACC = sys.argv[sys.argv.index('--accent') + 1] if '--accent' in sys.argv else 'violet'
T0 = time.time()
tick = lambda name: print(f'{name:14s} {time.time() - T0:5.1f}s') if os.environ.get('OBSIDIANUI_TIMING') else None

ob = ObsidianUI(1920, 1080, seed=3, keep_stages=bool(stages), accent=ACC)
ob.page()

# ===================================================================== layout
WX, WY, WW, WH, SIDE, RIGHT = 120, 96, 1680, 884, 300, 470
PAD = 64
FILES = [('2026 读书', 0, 'open'), ('小王子', 1, 'file'), ('狐狸', 1, 'file'), ('玫瑰', 1, 'file'), ('驯养', 1, 'file'),
         ('人物', 0, 'folder'), ('摘抄', 0, 'folder'), ('每日笔记', 0, 'folder'), ('模板', 0, 'folder'),
         ('附件', 0, 'folder'), ('读书清单', 0, 'file'), ('想读的书', 0, 'file')]
H1_BASE, H1_SIZE = 290, 76
PROP_Y = [358, 398]
BODY, BODY_LH, BODY_Y0 = 28, 48, 476
CODE_Y, CODE_SIZE = 554, 25
CODE = [
    [('```mermaid', 'fence')],
    [('flowchart', 'kw'), (' LR', 'op')],
    [('  A', 'text'), ('[陌生]', 'str'), (' -->', 'op'), ('|花时间|', 'cm'), (' B', 'text'), ('[驯养]', 'str')],
    [('  B', 'text'), (' -->', 'op'), (' C', 'text'), ('[彼此需要]', 'str'), (' -->', 'op'), (' D', 'text'), ('([独一无二])', 'str')],
    [('```', 'fence')],
]

# ===================================================================== the window chrome
ob.layer('window', z=10)
win = ob.window(WX, WY, WW, WH, tabs=['小王子', '狐狸'], active=0, side=SIDE, right=RIGHT)
N, E, R = win.note, win.explorer, win.right
CX0, CX1 = N.x0 + PAD, N.x1 - PAD                                  # note column
CW = CX1 - CX0

ob.layer('explorer', z=12)
ob.explorer(win, FILES, active=1)
ob.rrect(E.x0 + 14, E.y1 - 58, E.x1 - 14, E.y1 - 57, 0, BORDER)
ob.text('读书笔记', E.x0 + 26, E.y1 - 29, 18, MUTED, 'semibold', 'lm')
ob.glyph('collapse', E.x1 - 34, E.y1 - 29, 16, FAINT, 2.0)

ob.layer('header', z=12)
ob.view_header(win, ['2026 读书', '小王子'])
tick('chrome')

# ===================================================================== the note
TOG = (CX1 - 196, H1_BASE - H1_SIZE * 0.37 - 23, 196, 46)
for name, on in [('toggle_src', 0), ('toggle_read', 1)]:
    ob.layer(name, z=14)
    ob.toggle(*TOG, on=on)

ob.layer('h1', z=14)
ob.h1(CX0, H1_BASE, '小王子', H1_SIZE, bar=False)
ob.layer('h1_bar', z=14)
ob.h1(CX0, H1_BASE, '小王子', H1_SIZE, bar_w=150, bar_gap=20, draw_text=False)

ob.layer('props', z=14)
vx = ob.prop(CX0, PROP_Y[0], 'tag', '标签', 128)
x = ob.tag(vx, PROP_Y[0], '#童话', 18) + 10
ob.tag(x, PROP_Y[0], '#读书笔记', 18)
vx = ob.prop(CX0, PROP_Y[1], 'calendar', '读完', 128)
x = vx + ob.text('2026-10-12', vx, PROP_Y[1], 19, TEXT, 'regular', 'lm') + 18
ob.text('·  第 21 章重读', x, PROP_Y[1], 19, FAINT, 'regular', 'lm')
ob.rrect(CX0, PROP_Y[1] + 30, CX1, PROP_Y[1] + 31, 0, BORDER)

PARA = [
    [('第 21 章，', None), ('狐狸', 'link'), ('教小王子什么叫', None), ('驯养', 'link'), ('：', None)],
    [('不是占有，而是', None), ('建立联系', 'code'), ('，从此', None), ('彼此需要', 'b'), ('。', None)],
]
for i, runs in enumerate(PARA):
    ob.layer(f'para{i}', z=14)
    ob.rich(CX0, BODY_Y0 + i * BODY_LH, runs, BODY)

# the mermaid block (source view): the box, then each line in its own layer (typed), a caret per line
ob.layer('code_box', z=13)
cb = ob.code_block(CX0, CODE_Y, CW, CODE, size=CODE_SIZE, draw=False)
CODE_W = []
for i, toks in enumerate(CODE):
    ob.layer(f'code{i}', z=14)
    CODE_W.append(ob.code_line(cb.tx, cb.bases[i], toks, CODE_SIZE) - cb.tx)
    ob.layer(f'caret{i}', z=15)
    ob.caret(cb.tx + CODE_W[i], cb.bases[i], CODE_SIZE)
tick('note')

# the rendered flowchart (reading view), centred where the block was
DY = cb.cy + 4
WIDTHS, GAPS = [108, 122, 156, 156], [120, 60, 60]
xs, x = [], CX0 + (CW - sum(WIDTHS) - sum(GAPS)) / 2
for w_, g_ in zip(WIDTHS, GAPS + [0]):
    xs.append(x + w_ / 2); x += w_ + g_
NODES = [('陌生', 'stadium'), ('驯养', 'rect'), ('彼此需要', 'rect'), ('独一无二', 'round')]
NH = 80
for k, (lab, shape) in enumerate(NODES):
    ob.layer(f'dg{k}', z=14)
    ob.dnode(xs[k], DY, WIDTHS[k], NH, lab, shape, size=26)
ob.layer('dg1_hi', z=15)
ob.dnode(xs[1], DY, WIDTHS[1], NH, '驯养', 'rect', hi=True, size=26, focus=True)
for k in range(3):
    ob.layer(f'dge{k}', z=13)
    a, b = xs[k] + WIDTHS[k] / 2 + 3, xs[k + 1] - WIDTHS[k + 1] / 2 - (17 if k == 0 else 3)
    ob.dedge([(a, DY), (b, DY)], label='花时间' if k == 0 else None, label_at=0.47)

# the fox's line
ob.layer('callout', z=14)
CALL_Y = cb.y1 + 30
ob.callout(CX0, CALL_Y, CW, '狐狸说', [[('“你在你的', None), ('玫瑰', 'link'), ('身上花的时间，使她变得这么重要。”', None)]],
           size=BODY, title_size=24)
tick('diagram')

# ===================================================================== the right sidebar: local graph + backlinks
ob.layer('side_tools', z=12)
ty = ob.sidebar_tools(win, lit=1)
ob.layer('graph_head', z=12)
ob.text('局部关系图谱', R.x0 + 28, ty + 40, 21, BRIGHT, 'bold', 'lm')
ob.text('深度 2', R.x1 - 28, ty + 40, 16, FAINT, 'regular', 'rm')

GC = (R.cx - 4, ty + 250)                                           # the current note sits in the middle
G = lambda dx, dy, r, lab: (GC[0] + dx, GC[1] + dy, r, lab)
GN = [G(0, 0, 12, '小王子'),                                         # 0  (lit: this note and what it links to)
      G(-122, -78, 9, '狐狸'), G(112, -100, 9, '玫瑰'), G(-70, 104, 9, '驯养'),
      G(126, 78, 7, '飞行员'), G(186, 22, 6, '蛇'), G(36, -170, 7, 'B612'), G(176, -176, 5, '猴面包树'),
      G(196, 150, 6, '沙漠'), G(-194, 40, 7, '六颗星球'), G(-206, 128, 5, '国王'), G(-200, -108, 5, '点灯人'),
      G(-118, 184, 5, '商人'), G(46, 176, 5, '地理学家')]
GL = [(0, 1), (0, 2), (0, 3), (1, 3), (1, 2), (0, 4), (0, 5), (6, 2), (6, 7), (4, 8), (5, 8), (0, 9),
      (9, 10), (9, 11), (9, 12), (4, 13), (6, 0)]
LIT = [0, 1, 2, 3]
ob.layer('graph_grey', z=13)
ob.graph(GN, GL, LIT, label_size=15, only='grey')
ob.layer('graph_lit', z=14)
ob.graph(GN, GL, LIT, label_size=15, only='lit')

ob.layer('backlinks', z=12)
BY = GC[1] + 226
ob.rrect(R.x0 + 20, BY, R.x1 - 20, BY + 1, 0, BORDER)
ob.glyph('chev_d', R.x0 + 34, BY + 36, 15, FAINT, 2.2)
ob.text('反向链接', R.x0 + 50, BY + 36, 19, TEXT, 'semibold', 'lm')
ob.rrect(R.x0 + 142, BY + 24, R.x0 + 170, BY + 48, 12, '#2e2e2e')
ob.text('3', R.x0 + 156, BY + 36, 15, MUTED, 'semibold', 'mm')
BACK = [('狐狸', [('……他就是这样被', None), ('小王子', 'link'), ('驯养的。', None)]),
        ('玫瑰', [('……', None), ('小王子', 'link'), ('每晚给她罩上玻璃罩。', None)]),
        ('驯养', [('出自', None), ('小王子', 'link'), ('第 21 章，狐狸的话。', None)])]
for i, (name, runs) in enumerate(BACK):
    y = BY + 66 + i * 66
    ob.glyph('file', R.x0 + 36, y + 10, 17, FAINT, 1.9)
    ob.text(name, R.x0 + 54, y + 10, 18, TEXT, 'semibold', 'lm')
    ob.rich(R.x0 + 54, y + 44, runs, 16, MUTED)

ob.layer('status', z=16)
ob.status_bar(win, ['3 个反向链接', '268 字', '阅读视图'])
tick('sidebar')

# ===================================================================== the pointer (GIF only)
TX_READ = (TOG[0] + TOG[2] * 0.74, TOG[1] + TOG[3] * 0.62)
ob.layer('cursor', z=50)
ob.cursor(*TX_READ)
ob.layer('ring', z=49)                                               # the click ring (scaled up as it fades)
ob.circle(TX_READ[0], TX_READ[1], 34, '#ece4ff', 0.95, ring=3.5)
ob.end()
tick('drawn')

# ===================================================================== stage by stage (the draw-on GIF), then the final frame
# Things that move get in-between poses (stage names 'mv_*': the GIF shows them as quick hard cuts, i.e. real motion);
# everything else cross-fades from stage to stage.
ALL = list(ob.layers)
ease_out = lambda u: 1 - (1 - u) ** 3
ease_back = lambda u: 1 + 2.4 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2          # overshoots ~6 % and settles
ease_io = lambda u: 3 * u * u - 2 * u ** 3
lin = lambda u: u
REST = dict(dx=0.0, dy=0.0, scale=1.0, alpha=1.0, reveal=1.0)


def move(names, frm, to=REST, n=5, tag='', ease=ease_out, last=True, origin=None, mode='x', feather=14.0, between=None):
    """pose one or more layers from `frm` to `to` over n stages; the last stage is named `tag`"""
    names = [names] if isinstance(names, str) else names
    for k in range(1, n + 1):
        u = ease(k / n)
        p = {key: frm.get(key, REST[key]) + (to.get(key, REST[key]) - frm.get(key, REST[key])) * u for key in REST}
        p['alpha'] = min(1.0, max(0.0, p['alpha']))
        if between: between(p, k / n)
        for nm in names: ob.pose(nm, origin=origin, mode=mode, feather=feather, **p)
        if k < n: ob.stage(f'mv_{tag}{k}')
        elif last: ob.stage(tag)


def pop(name, tag, cx, cy, n=3):
    move(name, dict(scale=0.85, alpha=0.0), n=n, tag=tag, ease=ease_back, origin=(cx, cy))


if stages:
    for n in ALL: ob.hide(n)
    ob.stage('page')
    move('window', dict(dy=60, scale=0.97, alpha=0.0), n=6, tag='window', ease=ease_back)
    ob.show('explorer'); ob.stage('explorer')
    ob.show('header', 'toggle_src', 'side_tools'); ob.stage('header')
    move('h1', dict(reveal=0.0), n=3, tag='h1', ease=ease_io)
    move('h1_bar', dict(reveal=0.0), n=3, tag='bar')
    ob.show('props'); ob.stage('props')
    for i in range(2):
        move(f'para{i}', dict(reveal=0.0), n=4, tag=f'para{i}', ease=lin)
    ob.show('code_box'); ob.stage('code_box')
    for i in range(len(CODE)):                         # typed: the line reveals and the caret rides its end
        w_ = CODE_W[i]
        ob.show(f'caret{i}')
        if i: ob.hide(f'caret{i - 1}')
        steps = 2 if w_ < 200 else 4
        move([f'code{i}'], dict(reveal=0.0), n=steps, tag=f'code{i}', ease=lin, feather=2.0,
             between=lambda p, u, w_=w_, i=i: ob.pose(f'caret{i}', dx=-(1 - u) * (w_ + 4)))
    # the pointer glides to 阅读 and clicks: the toggle flips, the source fades, the chart renders node by node
    sx, sy = cb.tx + CODE_W[-1] + 260 - TX_READ[0], cb.bases[-1] - 30 - TX_READ[1]
    move('cursor', dict(dx=sx, dy=sy, alpha=0.0), n=6, tag='cursor', ease=ease_io,
         between=lambda p, u: p.update(alpha=min(1.0, 3 * u)))
    TC = (TOG[0] + TOG[2] / 2, TOG[1] + TOG[3] / 2)
    ob.show('ring'); ob.pose('ring', scale=0.4, alpha=1.0, origin=TX_READ)
    ob.pose('toggle_src', scale=0.97, origin=TC); ob.stage('mv_click1')
    ob.hide('toggle_src'); ob.pose('toggle_read', scale=1.06, origin=TC)
    ob.pose('ring', scale=0.8, alpha=0.8, origin=TX_READ); ob.stage('mv_click2')
    ob.pose('toggle_read'); ob.pose('ring', scale=1.15, alpha=0.35, origin=TX_READ); ob.stage('click')
    ob.hide('ring', *[f'code{i}' for i in range(len(CODE))], 'code_box', f'caret{len(CODE) - 1}'); ob.stage('reading')
    move('cursor', dict(), dict(dx=40, dy=40, alpha=0.0), n=2, tag='cursor_out', last=False)
    ob.hide('cursor')
    pop('dg0', 'node0', xs[0], DY)
    for k in range(3):
        move(f'dge{k}', dict(reveal=0.0), n=3, tag=f'edge{k}', ease=lin, feather=6.0)
        pop(f'dg{k + 1}', f'node{k + 1}', xs[k + 1], DY)
    move('dg1_hi', dict(alpha=0.0, scale=1.08), n=3, tag='node_hi', origin=(xs[1], DY))
    move('callout', dict(dy=28, alpha=0.0), n=5, tag='callout', ease=ease_back)
    ob.show('graph_head'); ob.stage('graph_head')
    move('graph_grey', dict(reveal=0.0), n=7, tag='graph', ease=ease_io, mode='r', origin=GC[:2], feather=40.0)
    move('graph_lit', dict(alpha=0.0), n=4, tag='lit', ease=ease_io)
    ob.show('backlinks'); ob.stage('backlinks')
    ob.show('status'); ob.stage('status')

# final poses: everything finished, in reading view
for n in ALL:
    ob.pose(n)
for n in ['toggle_src', 'code_box', 'cursor', 'ring'] + [f'code{i}' for i in range(len(CODE))] + [f'caret{i}' for i in range(len(CODE))]:
    ob.hide(n)
ob.save(out, stages_dir=stages)
tick('saved')
print('saved', out)
