"""macpaint — a 1984-style 1-bit paint program: the picture and the program it is being painted in (numpy + Pillow).

The look is a screen, not a print: a 640 x 360 framebuffer with exactly two values, ink and paper, blown up x3 with
no smoothing, so every pixel is a hard square. Nothing is grey; tone only ever comes from *8 x 8 patterns*.

Model:
  framebuffer  `doc` is the document bitmap (1 = black). Everything you draw goes into it with the program's own
               tools and their rules, and the interface is drawn around it at render time, so the same picture can be
               snapshotted with a different tool, pattern, cursor or menu showing (draw-on stages for free).
  patterns     each pattern is 8 bytes (8 x 8 bits) and is anchored to the document origin, not to the shape: two
               shapes filled with the same pattern line up seamlessly, and the pattern does not follow a curve or a
               perspective. Shading = picking a lighter or darker pattern for a region; gradients = bands of
               patterns (`bands`), never dithering noise. 38 of them live in the palette along the bottom.
  shapes       every tool is a rasteriser with the era's habits: lines are Bresenham with a square pen of 1-4 px
               (so diagonals are staircases and curves have jaggies), rectangles / rounded rectangles / ovals /
               freeforms are a pattern fill plus a border of the current line width drawn *inside* the outline,
               polygons and freeforms go through a non-antialiased scan fill.
  bucket       flood fill of the 4-connected run of same-coloured pixels under the cursor; a one-pixel gap in an
               outline leaks, and a fill clicked on a patterned area only fills one speck. Outlines must be closed.
  brush        a brush shape (round, square, slash, back-slash, bar, dot) stamped along the path, painting the
               current pattern opaquely; `spray` drops random pixels in a disc along the path, OR-ed in, so it can
               build shading and haze over anything.
  type         the text tool stamps bitmap glyphs: a built-in bold system face (9-px capitals, 2-px stems) and any
               TrueType face rendered with antialiasing *off*; styles are bitmap operations on the glyph mask:
               bold (smear right by 1), italic (shear in steps), underline, outline (dilate minus self) and shadow
               (outline plus a second dilation pushed down-right).
  editing      `copy(rect, to, flip, mask)` is select + option-drag (Flip Horizontal with flip=True; `mask` makes it a
               lasso selection, so a shape travels without its patterned background); `invert` is XOR (white
               whiskers on a black cat, black where they leave it); `erase` is the eraser; `dotted` a dotted trail.
  selection    marquee and lasso are overlays, not ink: marching ants, i.e. the outline pixels coloured by
               ((x + y) // 4) % 2. The lasso shrink-wraps around the black pixels it encloses, as the real one did
               (on a patterned background it wraps the pattern too: pass the object's own mask, or use the marquee).
  interface    menu bar with a small app glyph and invented menu names, rounded black screen corners, tool palette
               (2 x 10 tools, the active one inverted), line-width box with a check mark, pattern palette with the
               current-fill box, one document window: striped title bar with close box, centred title, scroll bars
               with a 50 % grey track, arrows, thumbs and size box, 1-px drop shadow. Pull-down menus have a 1-px
               shadow and inverted highlight; a zoom window shows a patch of the document at x`fat` with white gaps
               between the fat bits; cursors (arrow, cross, I-beam, bucket, spray, brush, pencil) have a white halo.

    from macpaint import MacPaint
    m = MacPaint(seed=1, title='untitled')
    m.rect(20, 20, 200, 120, fill='bricks', line=2)
    m.oval(300, 80, 60, 40, fill='gray')
    m.bucket(100, 200, 'scales')
    m.text('hello', 40, 150, size=24, font='serif', style=('shadow',))
    m.use('spray', pattern='black'); m.cursor('spray', 320, 160)
    m.stage('first')
    m.save('out.jpg')
Coordinates: document pixels (0, 0 = top-left of the window's content area), y down; the screen is 640 x 360 and
the output is `scale` times that (default 3 -> 1920 x 1080). Only numpy + Pillow.
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import spline, load_font


# ---------------------------------------------------------------- patterns (8 x 8, 1 = ink)
def _rows(*rows):
    w = max(len(r) for r in rows)
    return np.array([[1 if c == '#' else 0 for c in r.ljust(w, '.')] for r in rows], np.uint8)


def _fn(f):
    y, x = np.mgrid[0:8, 0:8]
    return f(x, y).astype(np.uint8)


PATTERNS = {
    # flat tones
    'white': np.zeros((8, 8), np.uint8),
    'black': np.ones((8, 8), np.uint8),
    'gray': _fn(lambda x, y: (x + y) % 2 == 0),                                                          # 50 %
    'light': _rows('#...#...', '..#...#.', '#...#...', '..#...#.', '#...#...', '..#...#.', '#...#...', '..#...#.'),  # 25 %
    'lighter': _rows('#...#...', '........', '..#...#.', '........', '#...#...', '........', '..#...#.', '........'),  # 12.5 %
    'mist': _rows('#.......', '........', '....#...', '........', '#.......', '........', '....#...', '........'),     # 6 %
    'faint': _rows('#.......', '........', '........', '........', '....#...', '........', '........', '........'),    # 3 %
    # dots and lines
    'dots': _rows('........', '.#...#..', '........', '...#...#', '........', '.#...#..', '........', '...#...#'),
    'polka': _rows('.##.....', '####....', '.##.....', '........', '.....##.', '....####', '.....##.', '........'),
    'hlines': _fn(lambda x, y: y % 4 == 0),
    'vlines': _fn(lambda x, y: x % 4 == 0),
    'diag': _fn(lambda x, y: (x + y) % 4 == 3),
    'rdiag': _fn(lambda x, y: (x - y) % 4 == 0),
    'wide_diag': _fn(lambda x, y: (x + y) % 8 == 7),
    'thick_diag': _fn(lambda x, y: (x + y) % 4 < 2),
    'grid': _fn(lambda x, y: (x == 0) | (y == 0)),
    'fine_grid': _fn(lambda x, y: (x % 4 == 0) | (y % 4 == 0)),
    'xhatch': _fn(lambda x, y: ((x + y) % 8 == 0) | ((x - y) % 8 == 0)),
    'hstripes': _fn(lambda x, y: y % 4 < 2),
    'vstripes': _fn(lambda x, y: x % 4 < 2),
    # textures
    'bricks': _rows('########', '#.......', '#.......', '#.......', '########', '....#...', '....#...', '....#...'),
    'scales': _rows('...#....', '...#....', '..#.#...', '##...###', '.......#', '.......#', '#.....#.', '.#####..'),
    'weave': _rows('####.#.#', '.....#.#', '####.#.#', '.....#.#', '.#.#####', '.#.#....', '.#.#####', '.#.#....'),
    'basket': _fn(lambda x, y: np.where((x // 4 + y // 4) % 2 == 0, y % 2 == 0, x % 2 == 0)),
    'diamonds': _fn(lambda x, y: (np.abs(x - 3.5) + np.abs(y - 3.5)).astype(int) == 3),
    'shingles': _rows('########', '#.......', '#.......', '.#.....#', '..#####.', '....#...', '....#...', '...#.#..'),
    'waves': _rows('........', '..##....', '.#..#...', '#....###', '........', '..##....', '.#..#...', '#....###'),
    'zigzag': _fn(lambda x, y: (y - np.abs(x - 4)) % 4 == 0),
    'stars': _rows('..#.....', '.###....', '..#.....', '........', '........', '......#.', '.....###', '......#.'),
    'sprigs': _rows('........', '..#.....', '.#.#....', '........', '........', '......#.', '.....#.#', '........'),
    'checker': _fn(lambda x, y: (x // 4 + y // 4) % 2 == 0),
    'gingham': _fn(lambda x, y: ((x // 4 % 2 == 0) & (y // 4 % 2 == 0))
                   | (((x // 4 % 2 == 0) ^ (y // 4 % 2 == 0)) & ((x + y) % 2 == 0))),
    'wood': _rows('######..', '........', '..#####.', '........', '#....###', '........', '.######.', '........'),
    'grass': _rows('........', '#.......', '#..#....', '.#.#....', '........', '....#...', '....#..#', '.....#.#'),
    'pebbles': _rows('.##.....', '#..#..#.', '#..#.#.#', '.##...#.', '....##..', '.#.#..#.', '#.##..#.', '.#..##..'),
    'circles': _rows('..###...', '.#...#..', '#.....#.', '#.....#.', '#.....#.', '.#...#..', '..###...', '........'),
    'plus': _rows('...#....', '...#....', '.#####..', '...#....', '...#....', '........', '........', '........'),
    'confetti': _rows('#.......', '.....#..', '..#.....', '.......#', '...#....', '#.......', '......#.', '.#......'),
    'denim': _fn(lambda x, y: (x + 2 * y) % 4 < 2),
}
PATTERNS['dark'] = 1 - PATTERNS['light']                                                                # 75 %
PATTERNS['darker'] = 1 - PATTERNS['lighter']                                                            # 87.5 %

PALETTE = ['white', 'black', 'gray', 'light', 'dark', 'lighter', 'mist', 'faint', 'dots', 'polka', 'hlines', 'vlines',
           'diag', 'rdiag', 'wide_diag', 'thick_diag', 'grid', 'fine_grid', 'xhatch',
           'bricks', 'scales', 'weave', 'diamonds', 'shingles', 'waves', 'zigzag', 'stars', 'sprigs', 'checker',
           'gingham', 'hstripes', 'vstripes', 'wood', 'grass', 'pebbles', 'circles', 'basket', 'darker']

# ---------------------------------------------------------------- the system face: bold, 9-px capitals, 2-px stems
# each glyph: (top row, rows); cap height 9 rows (0..8), baseline under row 8, descenders on rows 9..10
_G = {}


def _g(chars, top, *rows):
    _G[chars] = (top, rows)


_g('A', 0, '.####.', '##..##', '##..##', '##..##', '######', '##..##', '##..##', '##..##', '##..##')
_g('B', 0, '#####.', '##..##', '##..##', '##..##', '#####.', '##..##', '##..##', '##..##', '#####.')
_g('C', 0, '.####.', '##..##', '##....', '##....', '##....', '##....', '##....', '##..##', '.####.')
_g('D', 0, '#####.', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '#####.')
_g('E', 0, '######', '##....', '##....', '##....', '#####.', '##....', '##....', '##....', '######')
_g('F', 0, '######', '##....', '##....', '##....', '#####.', '##....', '##....', '##....', '##....')
_g('G', 0, '.####.', '##..##', '##....', '##....', '##.###', '##..##', '##..##', '##..##', '.#####')
_g('H', 0, '##..##', '##..##', '##..##', '##..##', '######', '##..##', '##..##', '##..##', '##..##')
_g('I', 0, '##', '##', '##', '##', '##', '##', '##', '##', '##')
_g('J', 0, '....##', '....##', '....##', '....##', '....##', '....##', '##..##', '##..##', '.####.')
_g('K', 0, '##...##', '##..##.', '##.##..', '####...', '###....', '####...', '##.##..', '##..##.', '##...##')
_g('L', 0, '##....', '##....', '##....', '##....', '##....', '##....', '##....', '##....', '######')
_g('M', 0, '##.....##', '###...###', '####.####', '##.###.##', '##..#..##', '##.....##', '##.....##', '##.....##', '##.....##')
_g('N', 0, '##...##', '###..##', '####.##', '##.####', '##..###', '##...##', '##...##', '##...##', '##...##')
_g('O', 0, '.####.', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '.####.')
_g('P', 0, '#####.', '##..##', '##..##', '##..##', '#####.', '##....', '##....', '##....', '##....')
_g('Q', 0, '.####.', '##..##', '##..##', '##..##', '##..##', '##..##', '##.###', '##..##', '.##.##')
_g('R', 0, '#####.', '##..##', '##..##', '##..##', '#####.', '##.##.', '##..##', '##..##', '##..##')
_g('S', 0, '.####.', '##..##', '##....', '.##...', '..##..', '...##.', '....##', '##..##', '.####.')
_g('T', 0, '######', '..##..', '..##..', '..##..', '..##..', '..##..', '..##..', '..##..', '..##..')
_g('U', 0, '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '.####.')
_g('V', 0, '##..##', '##..##', '##..##', '##..##', '##..##', '##..##', '.####.', '.####.', '..##..')
_g('W', 0, '##.....##', '##.....##', '##.....##', '##..#..##', '##.###.##', '####.####', '###...###', '##.....##', '#.......#')
_g('X', 0, '##..##', '##..##', '.####.', '..##..', '..##..', '.####.', '##..##', '##..##', '##..##')
_g('Y', 0, '##..##', '##..##', '##..##', '.####.', '..##..', '..##..', '..##..', '..##..', '..##..')
_g('Z', 0, '######', '....##', '....##', '...##.', '..##..', '.##...', '##....', '##....', '######')
_g('a', 3, '.####.', '....##', '.#####', '##..##', '##..##', '.#####')
_g('b', 0, '##....', '##....', '##....', '#####.', '##..##', '##..##', '##..##', '##..##', '#####.')
_g('c', 3, '.####.', '##..##', '##....', '##....', '##..##', '.####.')
_g('d', 0, '....##', '....##', '....##', '.#####', '##..##', '##..##', '##..##', '##..##', '.#####')
_g('e', 3, '.####.', '##..##', '######', '##....', '##..##', '.####.')
_g('f', 0, '..###', '.##..', '.##..', '#####', '.##..', '.##..', '.##..', '.##..', '.##..')
_g('g', 3, '.#####', '##..##', '##..##', '##..##', '##..##', '.#####', '....##', '.####.')
_g('h', 0, '##....', '##....', '##....', '#####.', '##..##', '##..##', '##..##', '##..##', '##..##')
_g('i', 1, '##', '..', '##', '##', '##', '##', '##', '##')
_g('j', 1, '..##', '....', '..##', '..##', '..##', '..##', '..##', '..##', '..##', '###.')
_g('k', 0, '##....', '##....', '##....', '##..##', '##.##.', '####..', '####..', '##.##.', '##..##')
_g('l', 0, '##', '##', '##', '##', '##', '##', '##', '##', '##')
_g('m', 3, '#########.', '##..##..##', '##..##..##', '##..##..##', '##..##..##', '##..##..##')
_g('n', 3, '#####.', '##..##', '##..##', '##..##', '##..##', '##..##')
_g('o', 3, '.####.', '##..##', '##..##', '##..##', '##..##', '.####.')
_g('p', 3, '#####.', '##..##', '##..##', '##..##', '##..##', '#####.', '##....', '##....')
_g('q', 3, '.#####', '##..##', '##..##', '##..##', '##..##', '.#####', '....##', '....##')
_g('r', 3, '##.###', '####..', '###...', '##....', '##....', '##....')
_g('s', 3, '.#####', '##....', '.####.', '....##', '....##', '#####.')
_g('t', 1, '.##..', '.##..', '#####', '.##..', '.##..', '.##..', '.##..', '..###')
_g('u', 3, '##..##', '##..##', '##..##', '##..##', '##..##', '.#####')
_g('v', 3, '##..##', '##..##', '##..##', '.####.', '.####.', '..##..')
_g('w', 3, '##......##', '##..##..##', '##..##..##', '##..##..##', '##..##..##', '.###..###.')
_g('x', 3, '##..##', '.####.', '..##..', '..##..', '.####.', '##..##')
_g('y', 3, '##..##', '##..##', '##..##', '##..##', '##..##', '.#####', '....##', '.####.')
_g('z', 3, '######', '...##.', '..##..', '.##...', '##....', '######')
_g('0', 0, '.####.', '##..##', '##..##', '##.###', '######', '###.##', '##..##', '##..##', '.####.')
_g('1', 0, '.##.', '###.', '.##.', '.##.', '.##.', '.##.', '.##.', '.##.', '####')
_g('2', 0, '.####.', '##..##', '....##', '....##', '...##.', '..##..', '.##...', '##....', '######')
_g('3', 0, '.####.', '##..##', '....##', '....##', '..###.', '....##', '....##', '##..##', '.####.')
_g('4', 0, '...###', '..####', '.##.##', '##..##', '##..##', '######', '....##', '....##', '....##')
_g('5', 0, '######', '##....', '##....', '#####.', '....##', '....##', '....##', '##..##', '.####.')
_g('6', 0, '.####.', '##....', '##....', '#####.', '##..##', '##..##', '##..##', '##..##', '.####.')
_g('7', 0, '######', '....##', '....##', '...##.', '..##..', '..##..', '.##...', '.##...', '.##...')
_g('8', 0, '.####.', '##..##', '##..##', '##..##', '.####.', '##..##', '##..##', '##..##', '.####.')
_g('9', 0, '.####.', '##..##', '##..##', '##..##', '.#####', '....##', '....##', '....##', '.####.')
_g(' ', 0, '....')
_g('.', 7, '##', '##')
_g(',', 7, '##', '##', '.#', '#.')
_g(':', 3, '##', '##', '..', '..', '##', '##')
_g('-', 4, '#####')
_g("'", 0, '##', '##', '#.')
_g('!', 0, '##', '##', '##', '##', '##', '##', '..', '##', '##')
_g('?', 0, '.####.', '##..##', '....##', '...##.', '..##..', '..##..', '......', '..##..', '..##..')
_g('/', 0, '....##', '....##', '...##.', '...##.', '..##..', '.##...', '.##...', '##....', '##....')
_g('(', 0, '..##', '.##.', '##..', '##..', '##..', '##..', '##..', '.##.', '..##')
_g(')', 0, '##..', '.##.', '..##', '..##', '..##', '..##', '..##', '.##.', '##..')
_g('%', 0, '.#...##', '#.#.##.', '.#..##.', '...##..', '..##...', '.##..#.', '.##.#.#', '##...#.', '.......')
_g('>', 1, '##....', '.##...', '..##..', '...##.', '..##..', '.##...', '##....')
_g('…', 7, '##.##.##', '##.##.##')                          # ellipsis
_g('✓', 2, '......#', '.....##', '#...##.', '##.##..', '.###...', '..#....')   # check mark
_g('→', 2, '....#...', '....##..', '#######.', '########', '#######.', '....##..', '....#...')  # arrow
_g('×', 3, '##..##', '.####.', '..##..', '.####.', '##..##')    # times


def system_text_mask(s, style=()):
    """bitmap of string `s` in the system face (rows 0..10, baseline under row 8), padded by 3 px for the styles"""
    cols = []
    for ch in s:
        top, rows = _G.get(ch, _G['?'])
        w = len(rows[0])
        g = np.zeros((11, w), np.uint8)
        g[top:top + len(rows)] = _rows(*rows)
        cols.append(g)
        cols.append(np.zeros((11, 1), np.uint8))
    m = np.concatenate(cols[:-1] or [np.zeros((11, 1), np.uint8)], axis=1)
    return _style(m, style)


def _dilate(m, r=1, square=True):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if not square and abs(dx) + abs(dy) > r: continue
            out |= _shift(m, dx, dy)
    return out


def _erode(m, r=1, square=False):
    return 1 - _dilate(1 - m, r, square)


def _shift(m, dx, dy):
    H, W = m.shape
    out = np.zeros_like(m)
    if abs(dx) >= W or abs(dy) >= H: return out
    out[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)] = m[max(-dy, 0):H + min(-dy, 0), max(-dx, 0):W + min(-dx, 0)]
    return out


def _style(m, style):
    """bitmap type styles, applied the way the old toolbox did it: on the glyph mask"""
    style = tuple(style or ())
    p = 3
    m = np.pad(m, p)
    if 'bold' in style:
        m = m | _shift(m, 1, 0)
    if 'italic' in style:
        H = m.shape[0]
        out = np.zeros_like(m)
        for y in range(H):
            out[y] = np.roll(m[y], (H - 1 - y) // 4 - 1)
        m = out
    if 'outline' in style or 'shadow' in style:
        d = _dilate(m, 1, square=True)
        ring = d & (1 - m)
        if 'shadow' in style:
            sh = _shift(d, 1, 1) | _shift(d, 2, 2)
            ring = ring | (sh & (1 - d))
        m = ring
    if 'underline' in style:
        ys = np.nonzero(m.any(1))[0]
        if len(ys):
            m[min(ys[-1] + 1, m.shape[0] - 1), p:-p] = 1
    return m


# ---------------------------------------------------------------- tool icons (16 x 16) and cursors
ICONS = {
    'marquee': ('................', '................', '.##.##.##.##.##.', '................', '.#............#.',
                '................', '.#............#.', '................', '.#............#.', '................',
                '.#............#.', '................', '.##.##.##.##.##.', '................', '................',
                '................'),
    'lasso': ('................', '.....######.....', '...##......##...', '..#..........#..', '.#............#.',
              '.#............#.', '..#..........#..', '...##......##...', '.....###.###....', '........#.......',
              '.......#.#......', '.......#........', '........#.......', '.........##.....', '...........#....',
              '................'),
    'zoom': ('................', '....####........', '..##....##......', '.#........#.....', '.#...##...#.....',
             '#...#.....#.....', '#..#......#.....', '#.........#.....', '.#........#.....', '.#.......#......',
             '..##....###.....', '....####.###....', '..........###...', '...........###..', '............##..',
             '................'),
    'text': ('................', '.......##.......', '......####......', '......####......', '.....##.###.....',
             '.....##.###.....', '....##...###....', '....##...###....', '...#########....', '...##.....###...',
             '..##......###...', '..##.......###..', '.####.....#####.', '................', '................',
             '................'),
    'bucket': ('................', '.....#..........', '....#.#.........', '....#..#........', '...##...#.......',
               '..#.#....#......', '.#..#.....#.....', '#...##.....#....', '#..#.#......#...', '#.#..#.....#.#..',
               '.#....#...#..#..', '..#....#.#...#..', '...#....#....##.', '....#..#.....##.', '.....##.......#.',
               '..............#.'),
    'spray': ('.....##.........', '....#..#..#.#...', '...######.......', '...#....#.#.#.#.', '...#....#.......',
              '...#....#..#.#..', '...#....#.......', '...#....#.#.....', '...#....#.......', '...#....#.......',
              '...#....#.......', '...#....#.......', '...#....#.......', '...#....#.......', '...######.......',
              '................'),
    'brush': ('............##..', '...........#.##.', '..........#..##.', '.........#..#...', '........#..#....',
              '.......#..#.....', '......#..#......', '.....##.#.......', '....####........', '...#####........',
              '...####.........', '..####..........', '..###...........', '.##.............', '.#..............',
              '................'),
    'pencil': ('............##..', '...........#..#.', '..........#..##.', '.........#..#.#.', '........#..#.#..',
               '.......#..#.#...', '......#..#.#....', '.....#..#.#.....', '....#..#.#......', '...#..#.#.......',
               '...##.#.#.......', '..#.###.........', '..##.#..........', '.###............', '.##.............',
               '................'),
    'line': ('................', '.............#..', '............#...', '...........#....', '..........#.....',
             '.........#......', '........#.......', '.......#........', '......#.........', '.....#..........',
             '....#...........', '...#............', '..#.............', '................', '................',
             '................'),
    'eraser': ('................', '................', '.......########.', '......#......##.', '.....#......#.#.',
               '....#......#..#.', '...#......#...#.', '..#......#...#..', '.########...#...', '.#......#..#....',
               '.#......#.#.....', '.#......##......', '.########.......', '................', '................',
               '................'),
}
CURSORS = {   # (rows, hotspot) ; '#' ink, 'o' white halo
    'arrow': (('#..........', '##.........', '#o#........', '#oo#.......', '#ooo#......', '#oooo#.....', '#ooooo#....',
               '#oooooo#...', '#ooooooo#..', '#oooooooo#.', '#ooooo#####', '#oo#oo#....', '#o#.#oo#...', '##..#oo#...',
               '#....#oo#..', '.....#oo#..', '......##...'), (0, 0)),
    'cross': (('.....ooo.....', '.....o#o.....', '.....o#o.....', '.....o#o.....', '.....o#o.....', 'oooooo#oooooo',
               '#############', 'oooooo#oooooo', '.....o#o.....', '.....o#o.....', '.....o#o.....', '.....o#o.....',
               '.....ooo.....'), (6, 6)),
    'ibeam': (('o##.##o', '.oo#oo.', '..o#o..', '..o#o..', '..o#o..', '..o#o..', 'oo###oo', '..o#o..', '..o#o..',
               '..o#o..', '..o#o..', '.oo#oo.', 'o##.##o'), (3, 7)),
    'bucket': (('.....#..........', '....#o#.........', '....#oo#........', '...##ooo#.......', '..#o#oooo#......',
                '.#oo#ooooo#.....', '#ooo##ooooo#....', '#oo#o#oooooo#...', '#o#oo#ooooo#o#..', '.#oooo#ooo#oo#..',
                '..#oooo#o#ooo#..', '...#oooo#oooo##.', '....#oo#.....##.', '.....##.......#.', '..............#.',
                '..............#.'), (14, 15)),
    'spray': (('.....##.........', '....#oo#..#.#...', '...######.......', '...#oooo#.#.#.#.', '...#oooo#.......',
               '...#oooo#..#.#..', '...#oooo#.......', '...#oooo#.#.....', '...#oooo#.......', '...#oooo#.......',
               '...######.......'), (12, 3)),
    'brush': (('..ooo..', '.o###o.', 'o#####o', 'o#####o', 'o#####o', '.o###o.', '..ooo..'), (3, 3)),
    'pencil': (('............##..', '...........#oo#.', '..........#oo##.', '.........#oo#o#.', '........#oo#o#..',
                '.......#oo#o#...', '......#oo#o#....', '.....#oo#o#.....', '....#oo#o#......', '...#oo#o#.......',
                '...##o#o#.......', '..#o###........', '..##.#..........', '.##.............', '.#..............',
                '................'), (1, 14)),
}


def _bitmap(rows):
    """'#' -> 1 ink, 'o' -> 2 white halo, '.' -> 0 transparent"""
    w = max(len(r) for r in rows)
    return np.array([[{'#': 1, 'o': 2}.get(c, 0) for c in r.ljust(w, '.')] for r in rows], np.uint8)


# ---------------------------------------------------------------- the program
class MacPaint:
    TOOLS = ['marquee', 'lasso', 'zoom', 'text', 'bucket', 'spray', 'brush', 'pencil', 'line', 'eraser',
             'rect', 'frect', 'rrect', 'frrect', 'oval', 'foval', 'free', 'ffree', 'poly', 'fpoly']

    def __init__(self, seed=0, title='untitled', menus=('Paper', 'Tools', 'Brushes', 'Patterns', 'Type', 'Zoom'),
                 screen=(640, 360), scale=3, ink='#000000', paper='#ffffff', doc=None, scroll=(0.0, 0.0)):
        self.SW, self.SH = screen
        self.scale = scale
        self.rng = np.random.default_rng(seed)
        self.title, self.menus = title, list(menus)
        self.ink, self.paper = ink, paper
        # ---- layout (screen px)
        self.tools_box = (4, 25, 57, 226)                    # 2 x 10 cells of 26 x 20
        self.lines_box = (4, 234, 57, 300)
        self.pat_box = (4, 313, 57, 355)                     # current fill
        self.pats_box = (62, 313, 635, 355)                  # 2 x 19 swatches
        self.win = (62, 24, 633, 305)                        # outer frame incl. title bar and scroll bars
        x0, y0, x1, y1 = self.win
        self.view = (x0 + 1, y0 + 19, x1 - 16, y1 - 16)      # content rect (x0, y0, x1, y1) exclusive ends
        vw, vh = self.view[2] - self.view[0], self.view[3] - self.view[1]
        self.VW, self.VH = vw, vh
        dw, dh = doc or (vw, vh)
        self.W, self.H = dw, dh
        self.doc = np.zeros((dh, dw), np.uint8)
        self.scroll = scroll
        self.YY, self.XX = np.mgrid[0:dh, 0:dw]
        # ---- interface state
        self.state = dict(tool='pencil', pattern='black', line=1, cursor=None, select=None, menu=None, zoom=None,
                          title=title)
        self.stages = []
        self._tiles = {}

    # ------------------------------------------------------------ patterns
    def tile(self, pat):
        """the pattern as a full-document bitmap, anchored to the document origin (as the real patterns were)"""
        key = pat if isinstance(pat, str) else id(pat)
        if key not in self._tiles:
            p = PATTERNS[pat] if isinstance(pat, str) else np.asarray(pat, np.uint8)
            self._tiles[key] = np.tile(p, (self.H // 8 + 1, self.W // 8 + 1))[:self.H, :self.W]
        return self._tiles[key]

    def paint(self, mask, pat='black', mode='opaque'):
        """put pattern `pat` through `mask` (bool/0-1 array). mode: opaque (replace), or (ink only), erase, invert"""
        m = np.asarray(mask).astype(bool)
        if mode == 'opaque': self.doc[m] = self.tile(pat)[m]
        elif mode == 'or': self.doc[m] |= self.tile(pat)[m]
        elif mode == 'erase': self.doc[m] = 0
        elif mode == 'invert': self.doc[m] ^= 1
        return m

    # ------------------------------------------------------------ masks (no antialiasing anywhere)
    def _canvas(self):
        return Image.new('L', (self.W, self.H), 0)

    def mask_poly(self, pts, smooth=False):
        P = spline(pts, 10) if smooth else np.asarray(pts, np.float32)
        im = self._canvas()
        ImageDraw.Draw(im).polygon([(float(x), float(y)) for x, y in P], fill=1)
        return np.asarray(im, np.uint8)

    def mask_oval(self, cx, cy, rx, ry):
        im = self._canvas()
        ImageDraw.Draw(im).ellipse([cx - rx, cy - ry, cx + rx - 1, cy + ry - 1], fill=1)
        return np.asarray(im, np.uint8)

    def mask_rect(self, x0, y0, x1, y1, radius=0):
        im = self._canvas()
        if radius: ImageDraw.Draw(im).rounded_rectangle([x0, y0, x1 - 1, y1 - 1], radius=radius, fill=1)
        else: ImageDraw.Draw(im).rectangle([x0, y0, x1 - 1, y1 - 1], fill=1)
        return np.asarray(im, np.uint8)

    def mask_path(self, pts, width=1, smooth=False, closed=False):
        """1-px Bresenham path (PIL's line rasteriser draws no antialiasing) widened by a square pen"""
        P = spline(pts, 10) if smooth else np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        im = self._canvas()
        d = ImageDraw.Draw(im)
        Q = [(int(round(x)), int(round(y))) for x, y in P]
        if len(Q) == 1: d.point(Q, fill=1)
        else: d.line(Q, fill=1, width=1)
        m = np.asarray(im, np.uint8)
        if width > 1:
            m = self.pen(m, width)
        return m

    def pen(self, m, w):
        """thicken a mask with a w x w square pen (how the era widened lines; also handy to pad a selection)"""
        out = m.copy()
        a = -(w // 2)
        for dy in range(a, a + w):
            for dx in range(a, a + w):
                out |= _shift(m, dx, dy)
        return out

    @staticmethod
    def border(mask, width=1):
        """the frame of a shape, drawn inside its outline, `width` px thick"""
        m = np.asarray(mask, np.uint8)
        return m & (1 - _erode(m, width, square=True))

    # ------------------------------------------------------------ shape tools
    def _shape(self, m, fill, line, line_pat='black'):
        if fill is not None: self.paint(m, fill)
        if line: self.paint(self.border(m, line), line_pat)
        return m

    def rect(self, x0, y0, x1, y1, fill=None, line=1, radius=0, line_pat='black'):
        """rectangle / rounded rectangle tool: pattern fill + border of `line` px inside the outline"""
        return self._shape(self.mask_rect(x0, y0, x1, y1, radius), fill, line, line_pat)

    def oval(self, cx, cy, rx, ry, fill=None, line=1, line_pat='black'):
        return self._shape(self.mask_oval(cx, cy, rx, ry), fill, line, line_pat)

    def shape(self, pts, fill=None, line=1, smooth=True, line_pat='black'):
        """freeform (smooth=True, a Catmull-Rom through the points) or polygon tool"""
        return self._shape(self.mask_poly(pts, smooth), fill, line, line_pat)

    def line(self, p0, p1, width=1, pat='black'):
        return self.paint(self.mask_path([p0, p1], width), pat)

    def pencil(self, pts, smooth=False, pat='black', mode='opaque'):
        """1-px freehand line through the points"""
        return self.paint(self.mask_path(pts, 1, smooth), pat, mode)

    def brush(self, pts, size=4, shape='round', pat='black', smooth=True, mode='opaque'):
        """brush shape stamped along the path, painting the pattern. shape: round, square, slash, backslash,
        bar (horizontal), vbar, dot (scatter of single pixels)"""
        path = self.mask_path(pts, 1, smooth)
        k = self._brush_kernel(size, shape)
        out = np.zeros_like(path)
        r = k.shape[0] // 2
        for dy, dx in zip(*np.nonzero(k)):
            out |= _shift(path, int(dx) - r, int(dy) - r)
        return self.paint(out, pat, mode)

    @staticmethod
    def _brush_kernel(size, shape):
        n = max(1, int(size))
        y, x = np.mgrid[0:n, 0:n] - (n - 1) / 2
        if shape == 'round': k = x * x + y * y <= (n / 2) ** 2 + 0.3
        elif shape == 'square': k = np.ones((n, n), bool)
        elif shape == 'slash': k = np.abs(x + y) <= 0.6
        elif shape == 'backslash': k = np.abs(x - y) <= 0.6
        elif shape == 'bar': k = np.abs(y) <= 0.6
        elif shape == 'vbar': k = np.abs(x) <= 0.6
        elif shape == 'dot': k = ((x.astype(int) + y.astype(int)) % 2 == 0) & (x * x + y * y <= (n / 2) ** 2)
        else: raise ValueError(shape)
        return k.astype(np.uint8)

    def dotted(self, pts, gap=4, size=1, smooth=True, pat='black'):
        """a dotted trail (a motion path, a seam): single dots (size x size) every `gap` px along the path"""
        P = spline(pts, 12) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        ss = np.arange(0, s[-1], gap)
        m = np.zeros((self.H, self.W), np.uint8)
        xs = np.round(np.interp(ss, s, P[:, 0])).astype(int); ys = np.round(np.interp(ss, s, P[:, 1])).astype(int)
        ok = (xs >= 0) & (xs < self.W - size) & (ys >= 0) & (ys < self.H - size)
        for dy in range(size):
            for dx in range(size):
                m[ys[ok] + dy, xs[ok] + dx] = 1
        return self.paint(m, pat)

    def bucket(self, x, y, pat='black'):
        """paint bucket: flood the 4-connected run of same-coloured pixels under (x, y) with the pattern"""
        im = Image.fromarray(self.doc * 1).copy()          # (a fromarray image is read-only: floodfill would be a no-op)
        ImageDraw.floodfill(im, (int(x), int(y)), 7)
        m = np.asarray(im) == 7
        self.paint(m, pat)
        return m

    def spray(self, pts, radius=9, density=0.35, pat='black', clip=None, smooth=True, seed=None):
        """spray can along a path: random single pixels inside a disc, OR-ed onto the picture.
        density ~ fraction of the disc's pixels hit per diameter of travel"""
        rng = np.random.default_rng(seed) if seed is not None else self.rng
        P = spline(pts, 12) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32)
        if len(P) > 1:
            seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
            s = np.concatenate([[0], np.cumsum(seg)])
            n = max(2, int(s[-1] / 2) + 1)
            ss = np.linspace(0, s[-1], n)
            P = np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1)
        per = max(1, int(np.pi * radius * radius * density * 2 / (2 * radius)))
        m = np.zeros((self.H, self.W), np.uint8)
        for cx, cy in P:
            a = rng.random(per) * 2 * np.pi
            r = radius * np.sqrt(rng.random(per))
            xs = np.round(cx + r * np.cos(a)).astype(int); ys = np.round(cy + r * np.sin(a)).astype(int)
            ok = (xs >= 0) & (xs < self.W) & (ys >= 0) & (ys < self.H)
            m[ys[ok], xs[ok]] = 1
        if clip is not None: m &= np.asarray(clip, np.uint8)
        t = self.tile(pat)
        self.doc |= (m & t)
        return m

    def bands(self, mask, pats, y0, y1, edge='spray', seed=None):
        """a 'gradient' the 1984 way: horizontal bands of patterns from y0 to y1 inside mask; the band seams are
        broken up with a little spray so they do not read as ruled lines"""
        m = np.asarray(mask).astype(bool)
        n = len(pats)
        cuts = np.linspace(y0, y1, n + 1)
        for i, p in enumerate(pats):
            band = m & (self.YY >= (cuts[i] if i else -1)) & (self.YY < (cuts[i + 1] if i < n - 1 else 10 ** 6))
            self.paint(band, p)
        if edge == 'spray':
            rng = np.random.default_rng(seed) if seed is not None else self.rng
            for i in range(1, n):
                y = cuts[i]
                below = m & (self.YY >= y) & (self.YY < y + 5)
                above = m & (self.YY < y) & (self.YY >= y - 5)
                ta, tb = self.tile(pats[i - 1]), self.tile(pats[i])
                # interleave the two patterns ragged-edge across the seam
                r = rng.random(m.shape) < np.clip(1 - np.abs(self.YY - y) / 5.5, 0, 1) * 0.5
                self.doc[below & r] = ta[below & r]
                self.doc[above & r] = tb[above & r]
        return m

    def erase(self, mask_or_rect):
        m = self.mask_rect(*mask_or_rect) if isinstance(mask_or_rect, (tuple, list)) else mask_or_rect
        return self.paint(m, mode='erase')

    def invert(self, mask_or_rect):
        m = self.mask_rect(*mask_or_rect) if isinstance(mask_or_rect, (tuple, list)) else mask_or_rect
        return self.paint(m, mode='invert')

    def copy(self, rect, to, flip=False, mask=None, mode='opaque'):
        """select a rectangle and option-drag a copy of it to `to` (its new top-left); flip=True mirrors it
        left-right (the Flip Horizontal of the era). mask: only the pixels inside it travel, like a lasso selection,
        so a shape can be copied off a patterned background without dragging the background along"""
        x0, y0, x1, y1 = rect
        piece = self.doc[y0:y1, x0:x1].copy()
        keep = np.ones_like(piece) if mask is None else np.asarray(mask, np.uint8)[y0:y1, x0:x1].copy()
        if flip: piece, keep = piece[:, ::-1], keep[:, ::-1]
        tx, ty = to
        h, w = piece.shape
        tgt = self.doc[ty:ty + h, tx:tx + w]
        piece, keep = piece[:tgt.shape[0], :tgt.shape[1]], keep[:tgt.shape[0], :tgt.shape[1]].astype(bool)
        if mode == 'opaque': tgt[keep] = piece[keep]
        else: tgt[keep] |= piece[keep]

    # ------------------------------------------------------------ type
    def text_mask(self, s, x, y, size=12, font='system', style=(), anchor='l'):
        """glyph mask for text tool. font='system' is the built-in bold bitmap face (size ignored; style still
        applies); any other value is a core.load_font style (serif, sans_bold, rounded, ...) rendered without
        antialiasing at `size` px. (x, y): baseline-left for 'l', baseline-centre for 'm', baseline-right for 'r'."""
        if font == 'system':
            g = system_text_mask(s, style)                       # padded by 3 on every side
            base = 3 + 9                                          # row under the baseline in the padded mask
        else:
            f = load_font(font, size)
            asc, desc = f.getmetrics()
            w = int(f.getlength(s)) + 8
            im = Image.new('L', (w + 6, asc + desc + 6), 0)
            d = ImageDraw.Draw(im)
            d.fontmode = '1'
            d.text((3, 3 + asc), s, font=f, fill=255, anchor='ls')
            g = (np.asarray(im) > 127).astype(np.uint8)
            if style: g = _style(g, style)[3:-3, 3:-3]          # the canvas already has a 3-px margin for the styles
            base = 3 + asc
        cols = np.nonzero(g.any(0))[0]
        if len(cols) == 0: return np.zeros((self.H, self.W), np.uint8)
        g = g[:, cols[0]:cols[-1] + 1]
        h, w = g.shape
        ox = int(x) - {'l': 0, 'm': w // 2, 'r': w}[anchor]
        oy = int(y) - base
        m = np.zeros((self.H, self.W), np.uint8)
        xa, ya = max(ox, 0), max(oy, 0)
        xb, yb = min(ox + w, self.W), min(oy + h, self.H)
        if xb > xa and yb > ya:
            m[ya:yb, xa:xb] = g[ya - oy:yb - oy, xa - ox:xb - ox]
        return m

    def text(self, s, x, y, size=12, font='system', style=(), anchor='l', opaque=False):
        """text tool. opaque=True first clears the glyphs' bounding box (+2 px), like typing into white"""
        m = self.text_mask(s, x, y, size, font, style, anchor)
        if opaque:
            ys, xs = np.nonzero(m)
            if len(xs): self.erase((xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3))
        if 'outline' in style or 'shadow' in style:
            # outline styles are hollow: clear the inside of the letters first
            inner = _fill_holes(m)
            self.paint(inner & (1 - m), mode='erase')
        self.paint(m, 'black')
        return m

    # ------------------------------------------------------------ interface state
    def use(self, tool=None, pattern=None, line=None):
        """select a tool / pattern / line width in the palettes (shown in the next snapshot)"""
        if tool: self.state['tool'] = tool
        if pattern: self.state['pattern'] = pattern
        if line: self.state['line'] = line

    def cursor(self, kind=None, x=0, y=0):
        """put the mouse cursor (arrow, cross, ibeam, bucket, spray, brush, pencil) at document (x, y); None hides it"""
        self.state['cursor'] = None if kind is None else (kind, int(x), int(y))

    def select(self, rect=None, lasso=None):
        """marching-ants selection: rect=(x0, y0, x1, y1), or lasso=mask -> shrink-wrapped around its ink"""
        if rect is not None:
            self.state['select'] = ('rect', tuple(int(v) for v in rect))
        elif lasso is not None:
            m = np.asarray(lasso, np.uint8) & self.doc
            self.state['select'] = ('lasso', m)
        else:
            self.state['select'] = None

    def menu(self, name=None, items=(), checked=(), hilite=None, styled=False):
        """pull down menu `name` with `items` ('-' is a dotted separator); `hilite` is the item under the mouse;
        styled=True draws each item in the type style it names (Bold in bold, Outline in outline, ...)"""
        self.state['menu'] = None if name is None else (name, list(items), set(checked), hilite, styled)

    def zoom(self, x=None, y=None, w=13, h=11, at=(470, 40), fat=7, title='zoom'):
        """a small window showing document pixels (x..x+w, y..y+h) as fat bits, top-left at screen `at`"""
        self.state['zoom'] = None if x is None else (int(x), int(y), w, h, at, fat, title)

    def retitle(self, title):
        self.state['title'] = title

    # ------------------------------------------------------------ render the screen
    def render(self):
        S = np.zeros((self.SH, self.SW), np.uint8)
        st = self.state
        self._menubar(S, st)
        self._tools(S, st)
        self._lines(S, st)
        self._patterns(S, st)
        self._window(S, st)
        if st['zoom']: self._zoom(S, st['zoom'])
        if st['menu']: self._pulldown(S, st)
        if st['cursor']: self._cursor(S, *st['cursor'])
        self._corners(S)
        return S

    # -- primitives on the screen buffer
    @staticmethod
    def _box(S, x0, y0, x1, y1, fill=0, border=1):
        """rect with exclusive ends; fill 0 white / 1 black / pattern array"""
        if isinstance(fill, np.ndarray):
            yy, xx = np.mgrid[y0:y1, x0:x1]
            S[y0:y1, x0:x1] = fill[yy % 8, xx % 8]
        else:
            S[y0:y1, x0:x1] = fill
        if border:
            S[y0, x0:x1] = 1; S[y1 - 1, x0:x1] = 1; S[y0:y1, x0] = 1; S[y0:y1, x1 - 1] = 1

    @staticmethod
    def _blit(S, bm, x, y, value=None):
        """paste bitmap: value None -> '#'=1 ink and 'o'=2 white; else set ink pixels to value"""
        h, w = bm.shape
        x, y = int(x), int(y)
        xa, ya, xb, yb = max(x, 0), max(y, 0), min(x + w, S.shape[1]), min(y + h, S.shape[0])
        if xb <= xa or yb <= ya: return
        sub = bm[ya - y:yb - y, xa - x:xb - x]
        tgt = S[ya:yb, xa:xb]
        if value is None:
            tgt[sub == 1] = 1; tgt[sub == 2] = 0
        else:
            tgt[sub == 1] = value

    def _str(self, S, s, x, y, value=1, style=()):
        """system text with baseline-left at screen (x, y)"""
        g = system_text_mask(s, style)
        cols = np.nonzero(g.any(0))[0]
        if len(cols) == 0: return 0
        g = g[:, cols[0]:]
        self._blit(S, g, x, y - 12, value)
        return g.shape[1] - 3

    @staticmethod
    def _str_w(s, style=()):
        g = system_text_mask(s, style)
        cols = np.nonzero(g.any(0))[0]
        return int(cols[-1] - cols[0] + 1) if len(cols) else 0

    # -- pieces of the interface
    def _menubar(self, S, st):
        S[0:20, :] = 0
        S[19, :] = 1
        self._menu_x = []
        # app glyph: a seedling in a pot (stands where a system glyph would be)
        sprout = _rows('...##.##', '..####.#', '..###..#', '...#.##.', '....#...', '..#####.', '..#####.', '...###..', '...###..')
        self._blit(S, sprout, 14, 5)
        x = 40
        for name in self.menus:
            w = self._str_w(name)
            self._menu_x.append((name, x - 8, x + w + 8))
            open_ = st['menu'] and st['menu'][0] == name
            if open_: S[1:19, x - 8:x + w + 8] = 1
            self._str(S, name, x, 14, 0 if open_ else 1)
            x += w + 20

    def _tools(self, S, st):
        x0, y0, x1, y1 = self.tools_box
        self._box(S, x0, y0, x1, y1)
        cw, chh = 26, 20
        for i, name in enumerate(self.TOOLS):
            cx, cy = x0 + (i % 2) * cw, y0 + (i // 2) * chh
            if i % 2 == 0 and i: S[cy, x0:x1] = 1
            if i % 2 == 1: S[cy:cy + chh, cx] = 1
            icon = self._icon(name)
            on = st['tool'] == name
            if on: S[cy + 1:cy + chh, cx + (1 if i % 2 else 1):cx + cw] = 1
            self._blit(S, icon, cx + 5, cy + 2, 0 if on else 1)

    def _icon(self, name):
        if name in ICONS: return _rows(*ICONS[name])
        gray = PATTERNS['gray']
        yy, xx = np.mgrid[0:16, 0:16]
        filled = name in ('frect', 'frrect', 'foval', 'ffree', 'fpoly')
        base = name[1:] if filled else name
        im = Image.new('L', (16, 16), 0); d = ImageDraw.Draw(im)
        if base == 'rect': d.rectangle([1, 3, 14, 12], fill=1)
        elif base == 'rrect': d.rounded_rectangle([1, 3, 14, 12], radius=3, fill=1)
        elif base == 'oval': d.ellipse([1, 3, 14, 12], fill=1)
        elif base == 'free': d.polygon([(3, 3), (8, 2), (13, 5), (11, 8), (14, 12), (6, 13), (2, 10), (5, 7)], fill=1)
        elif base == 'poly': d.polygon([(2, 12), (5, 3), (10, 6), (14, 2), (13, 12)], fill=1)
        m = np.asarray(im, np.uint8)
        b = self.border(m, 1)
        if filled: ic = np.where(m.astype(bool), gray[yy % 8, xx % 8], 0).astype(np.uint8) | b
        else: ic = b
        return ic

    def _lines(self, S, st):
        x0, y0, x1, y1 = self.lines_box
        self._box(S, x0, y0, x1, y1)
        rows = [('dash', 0), (1, 1), (2, 2), (3, 3), (4, 4)]
        for i, (key, w) in enumerate(rows):
            cy = y0 + 8 + i * 12
            if key == 'dash':
                S[cy, x0 + 14:x1 - 6:2] = 1
            else:
                S[cy - w // 2:cy - w // 2 + w, x0 + 14:x1 - 6] = 1
            if st['line'] == key:
                ck = _rows('....#', '...##', '#.##.', '###..', '.#...')
                self._blit(S, ck, x0 + 4, cy - 3)

    def _patterns(self, S, st):
        x0, y0, x1, y1 = self.pat_box
        self._box(S, x0, y0, x1, y1)
        cur = PATTERNS[st['pattern']] if isinstance(st['pattern'], str) else st['pattern']
        # current fill: a pattern-filled card with a little drop shadow
        self._box(S, x0 + 7, y0 + 6, x1 - 9, y1 - 8, cur, 1)
        S[y0 + 8:y1 - 7, x1 - 9] = 1; S[y1 - 8, x0 + 9:x1 - 8] = 1
        px0, py0, px1, py1 = self.pats_box
        n = len(PALETTE); per = (n + 1) // 2
        cw = (px1 - px0 - 1) / per
        ch = (py1 - py0 - 1) // 2
        for i, name in enumerate(PALETTE):
            r, c = divmod(i, per)
            a, b = int(round(px0 + c * cw)), int(round(px0 + (c + 1) * cw))
            self._box(S, a, py0 + r * ch, b + 1, py0 + (r + 1) * ch + 1, PATTERNS[name], 1)
        S[py1 - 1, px0:px1] = 1

    def _window(self, S, st):
        x0, y0, x1, y1 = self.win
        vx0, vy0, vx1, vy1 = self.view
        self._box(S, x0, y0, x1, y1, 0, 1)
        S[y0 + 1:y1 + 1, x1] = 1; S[y1, x0 + 1:x1 + 1] = 1                 # 1-px drop shadow
        # title bar: six fine stripes, a close box, the title in a white gap
        S[y0 + 18, x0:x1] = 1
        for k in range(6):
            S[y0 + 4 + 2 * k, x0 + 2:x1 - 2] = 1
        S[y0 + 3:y0 + 16, x0 + 8:x0 + 23] = 0
        self._box(S, x0 + 9, y0 + 4, x0 + 22, y0 + 15, 0, 1)
        t = st['title']
        tw = self._str_w(t)
        tx = (x0 + x1) // 2 - tw // 2
        S[y0 + 3:y0 + 16, tx - 7:tx + tw + 7] = 0
        self._str(S, t, tx, y0 + 14, 1)
        # content
        sx, sy = int(self.scroll[0] * max(0, self.W - self.VW)), int(self.scroll[1] * max(0, self.H - self.VH))
        part = self.doc[sy:sy + self.VH, sx:sx + self.VW]
        S[vy0:vy0 + part.shape[0], vx0:vx0 + part.shape[1]] = part
        sel = st['select']
        if sel: self._ants(S, sel, vx0 - sx, vy0 - sy, (vx0, vy0, vx1, vy1))
        # scroll bars
        S[vy0 - 1:y1, vx1] = 1; S[vy1, x0:x1] = 1
        gray = PATTERNS['gray']
        self._box(S, vx1, vy0 - 1, x1, vy1 + 1, gray, 1)
        self._box(S, x0, vy1, vx1 + 1, y1, gray, 1)
        up = _rows('....#....', '...#.#...', '..#...#..', '.#.....#.', '###...###', '..#...#..', '..#...#..', '..#####..')
        self._box(S, vx1, vy0 - 1, x1, vy0 + 15, 0, 1); self._blit(S, up, vx1 + 4, vy0 + 3)
        self._box(S, vx1, vy1 - 16, x1, vy1 + 1, 0, 1); self._blit(S, up[::-1], vx1 + 4, vy1 - 12)
        lt = up.T
        self._box(S, x0, vy1, x0 + 16, y1, 0, 1); self._blit(S, lt, x0 + 4, vy1 + 4)
        self._box(S, vx1 - 15, vy1, vx1 + 1, y1, 0, 1); self._blit(S, lt[:, ::-1], vx1 - 12, vy1 + 4)
        # thumbs
        ty = vy0 + 15 + int((vy1 - vy0 - 47) * self.scroll[1])
        self._box(S, vx1, ty, x1, ty + 17, 0, 1)
        tx2 = x0 + 15 + int((vx1 - x0 - 47) * self.scroll[0])
        self._box(S, tx2, vy1, tx2 + 17, y1, 0, 1)
        # size box
        self._box(S, vx1, vy1, x1, y1, 0, 1)
        self._box(S, vx1 + 6, vy1 + 6, x1 - 2, y1 - 2, 0, 1)
        self._box(S, vx1 + 3, vy1 + 3, vx1 + 10, vy1 + 10, 0, 1)

    def _ants(self, S, sel, ox, oy, clip):
        cx0, cy0, cx1, cy1 = clip
        if sel[0] == 'rect':
            x0, y0, x1, y1 = sel[1]
            m = np.zeros((self.H, self.W), np.uint8)
            m[max(y0, 0):y1, max(x0, 0):x1] = 1
            edge = self.border(m, 1)
        else:
            m = _dilate(sel[1], 1, square=True)
            edge = m & (1 - _erode(m, 1, square=False))
        ys, xs = np.nonzero(edge)
        X, Y = xs + ox, ys + oy
        ok = (X >= cx0) & (X < cx1) & (Y >= cy0) & (Y < cy1)
        S[Y[ok], X[ok]] = (((X[ok] + Y[ok]) // 4) % 2 == 0).astype(np.uint8)

    def _pulldown(self, S, st):
        name, items, checked, hilite, styled = st['menu']
        hit = [m for m in self._menu_x if m[0] == name]
        if not hit: return
        _, mx0, _ = hit[0]
        widths = [self._str_w(it, (it.lower(),) if styled and it.lower() in ('bold', 'italic', 'underline', 'outline', 'shadow') else ())
                  for it in items if it != '-']
        w = max(widths + [40]) + 34
        h = sum(6 if it == '-' else 16 for it in items) + 4
        x0, y0 = mx0, 19
        self._box(S, x0, y0, x0 + w, y0 + h, 0, 1)
        S[y0 + 2:y0 + h + 1, x0 + w] = 1; S[y0 + h, x0 + 2:x0 + w + 1] = 1        # shadow
        y = y0 + 2
        for it in items:
            if it == '-':
                S[y + 3, x0 + 1:x0 + w - 1:2] = 1
                y += 6; continue
            on = it == hilite
            if on: S[y:y + 16, x0 + 1:x0 + w - 1] = 1
            v = 0 if on else 1
            style = (it.lower(),) if styled and it.lower() in ('bold', 'italic', 'underline', 'outline', 'shadow') else ()
            self._str(S, it, x0 + 18, y + 13, v, style)
            if it in checked:
                ck = _rows('......#', '.....##', '#...##.', '##.##..', '.###...', '..#....')
                self._blit(S, ck, x0 + 5, y + 5, v)
            y += 16

    def _zoom(self, S, z):
        x, y, w, h, at, fat, title = z
        ax, ay = at
        W, H = w * fat + 3, h * fat + 3 + 18
        self._box(S, ax, ay, ax + W, ay + H, 0, 1)
        S[ay + 1:ay + H + 1, ax + W] = 1; S[ay + H, ax + 1:ax + W + 1] = 1
        S[ay + 18, ax:ax + W] = 1
        for k in range(6): S[ay + 4 + 2 * k, ax + 2:ax + W - 2] = 1
        tw = self._str_w(title)
        tx = ax + W // 2 - tw // 2
        S[ay + 3:ay + 16, tx - 5:tx + tw + 5] = 0
        self._str(S, title, tx, ay + 14, 1)
        patch = self.doc[y:y + h, x:x + w]
        for j in range(patch.shape[0]):
            for i in range(patch.shape[1]):
                if patch[j, i]:
                    px, py = ax + 2 + i * fat, ay + 20 + j * fat
                    S[py:py + fat - 1, px:px + fat - 1] = 1

    def _cursor(self, S, kind, x, y):
        rows, (hx, hy) = CURSORS[kind]
        bm = _bitmap(rows)
        # every cursor gets a white halo so it reads over any pattern
        ink = (bm == 1).astype(np.uint8)
        halo = _dilate(np.pad(ink, 1), 1, square=True)
        full = np.where(np.pad(ink, 1) == 1, 1, np.where((halo == 1) | (np.pad(bm, 1) == 2), 2, 0)).astype(np.uint8)
        sx, sy = self.view[0] + x - int(self.scroll[0] * max(0, self.W - self.VW)), \
            self.view[1] + y - int(self.scroll[1] * max(0, self.H - self.VH))
        self._blit(S, full, sx - hx - 1, sy - hy - 1)

    def _corners(self, S):
        r = 6
        yy, xx = np.mgrid[0:r, 0:r]
        outside = (xx - r + 0.5) ** 2 + (yy - r + 0.5) ** 2 > r * r
        S[:r, :r][outside] = 1
        S[:r, -r:][outside[:, ::-1]] = 1
        S[-r:, :r][outside[::-1]] = 1
        S[-r:, -r:][outside[::-1, ::-1]] = 1

    # ------------------------------------------------------------ output
    def image(self, S=None):
        S = self.render() if S is None else S
        big = np.repeat(np.repeat(S, self.scale, 0), self.scale, 1)
        ink = np.array(Image.new('RGB', (1, 1), self.ink).getpixel((0, 0)), np.uint8)
        pap = np.array(Image.new('RGB', (1, 1), self.paper).getpixel((0, 0)), np.uint8)
        rgb = np.where(big[..., None] == 1, ink, pap).astype(np.uint8)
        im = Image.fromarray(rgb, 'RGB')
        if self.ink in ('#000000', 'black') and self.paper in ('#ffffff', 'white'): im = im.convert('L')
        return im

    def stage(self, name):
        self.stages.append((name, self.image()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.image()
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img


def _fill_holes(m):
    """pixels enclosed by m (the inside of outlined letters)"""
    H, W = m.shape
    im = Image.fromarray(np.pad(m, 1) * 1).copy()
    ImageDraw.floodfill(im, (0, 0), 7)
    outside = (np.asarray(im) == 7)[1:-1, 1:-1]
    return (~outside).astype(np.uint8)
