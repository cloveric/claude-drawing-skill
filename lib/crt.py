"""crt — a green-screen CRT video terminal showing ASCII art in glowing phosphor (numpy + Pillow only).

Model:
  memory    a character terminal: `cols` x `rows` cells of character memory, each with an intensity attribute
            (dim / normal / bold), reverse video and underline. A line can be double-width, or the top / bottom
            half of a double-height line, as on the video terminals of the late 1970s. Nothing is ever drawn
            between cells: everything on the screen is a character.
  ROM       the character generator: 5 x 7 dot glyphs (lower case with two descender rows) in a 7 x 10 dot cell,
            plus a graphics set: box drawing, the five 'scan line' bars used for plotting (one scan line each, at
            five heights in the cell), block eighths, shades, degree sign, triangles, arrows.
  art       pictures are painted into a hidden map at dot resolution (7 x 10 samples per cell): regions with a
            *material* (which characters and intensities it may use) and a *tone* (how brightly it should glow),
            and strokes. `compose()` picks every cell's character: interior cells from the material's ramp by
            tone (error diffusion inside the material, so ramps blend instead of banding), silhouette cells by the
            direction and position of the edge in real pixels ( _ . - ' / \\ ( ) | ), stroke cells by the
            stroke's direction. On a screen dense means *bright*: a storm cloud is sparse and dim, the sun dense
            and bold -- the opposite of ink on paper.
  beam      every character row is 10 scan lines. On each scan line the video signal is the row of dots, every
            dot stretched by half a dot (so one-dot verticals stay visible) and smeared by the video amplifier's
            limited bandwidth (soft rising edge, a short trail to the right). The beam lays down a gaussian spot
            whose size grows with the current: dim lines are thin with dark gaps between them, bright ones swell
            and close the gaps (blooming). The brightness control is up a little, so the whole raster glows
            faintly and its scan lines show even where nothing is written.
  phosphor  P1 green (or P3 amber, P4 white). Emission saturates the way a camera sees it: bold cores go pale
            mint. Persistence: whatever moved in the last frames is still fading (`trail`). Burn-in: a status
            line that sat in one place for years has worn the phosphor (`burn`).
  tube      the raster is bent by the curved faceplate (barrel: the edges bow out, the corners pull in) and
            falls off toward the edges; light scattered in the thick glass gives bloom and a wide halation halo.
            The unlit face is dark grey-green glass with the room in it (a window, a ceiling sheen) and the bezel's
            shadow along the top.
  case      a moulded putty-coloured plastic bezel: stippled texture, a chamfered opening whose slopes catch the
            green spill of the screen, a mould seam, a power LED and two thumbwheels.

    from crt import CRTTerminal
    t = CRTTerminal(1920, 1080, seed=3, cols=120, rows=36)
    t.power()
    t.write(0, 0, 'wx@lookout:~$ ', 'bold'); t.write(14, 0, 'forecast --today')
    t.material('sun', [' ', '.', ':', '+', '*', '#', '@'], attrs=['dim', 'dim', 'normal', 'normal', 'bold', 'bold', 'bold'])
    t.fill(t.circle(20, 12, 6), 'sun', t.sphere_tone(20, 12, 6))
    t.compose(); t.reveal()
    t.cursor(14, 1)
    t.save('out.jpg')
Cell coordinates are (col, row), floats allowed; (c, r) is the top-left corner of cell (c, r).
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep, spline, height_normals, load_font, fbm1d


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ================================================================ character generator ROM
# 5 x 7 glyphs ('#' = dot). Rows 7-8, when given, are descenders. Placed at dots 1-5 of a 7-dot cell,
# rows 1-9 of a 10-line cell (row 0 is the gap between text lines).
_FONT = {
    ' ': ['.....'] * 7,
    '!': ['..#..', '..#..', '..#..', '..#..', '..#..', '.....', '..#..'],
    '"': ['.#.#.', '.#.#.', '.....', '.....', '.....', '.....', '.....'],
    '#': ['.#.#.', '.#.#.', '#####', '.#.#.', '#####', '.#.#.', '.#.#.'],
    '$': ['..#..', '.####', '#.#..', '.###.', '..#.#', '####.', '..#..'],
    '%': ['##...', '##..#', '...#.', '..#..', '.#...', '#..##', '...##'],
    '&': ['.##..', '#..#.', '#.#..', '.#...', '#.#.#', '#..#.', '.##.#'],
    "'": ['..#..', '..#..', '.....', '.....', '.....', '.....', '.....'],
    '(': ['...#.', '..#..', '.#...', '.#...', '.#...', '..#..', '...#.'],
    ')': ['.#...', '..#..', '...#.', '...#.', '...#.', '..#..', '.#...'],
    '*': ['.....', '..#..', '#.#.#', '.###.', '#.#.#', '..#..', '.....'],
    '+': ['.....', '..#..', '..#..', '#####', '..#..', '..#..', '.....'],
    ',': ['.....', '.....', '.....', '.....', '.....', '..#..', '..#..', '.#...'],
    '-': ['.....', '.....', '.....', '#####', '.....', '.....', '.....'],
    '.': ['.....', '.....', '.....', '.....', '.....', '.....', '..#..'],
    '0': ['.###.', '#...#', '#..##', '#.#.#', '##..#', '#...#', '.###.'],
    '1': ['..#..', '.##..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    '2': ['.###.', '#...#', '....#', '...#.', '..#..', '.#...', '#####'],
    '3': ['#####', '...#.', '..#..', '...#.', '....#', '#...#', '.###.'],
    '4': ['...#.', '..##.', '.#.#.', '#..#.', '#####', '...#.', '...#.'],
    '5': ['#####', '#....', '####.', '....#', '....#', '#...#', '.###.'],
    '6': ['..##.', '.#...', '#....', '####.', '#...#', '#...#', '.###.'],
    '7': ['#####', '....#', '...#.', '..#..', '.#...', '.#...', '.#...'],
    '8': ['.###.', '#...#', '#...#', '.###.', '#...#', '#...#', '.###.'],
    '9': ['.###.', '#...#', '#...#', '.####', '....#', '...#.', '.##..'],
    ':': ['.....', '.....', '..#..', '.....', '.....', '..#..', '.....'],
    ';': ['.....', '.....', '..#..', '.....', '.....', '..#..', '..#..', '.#...'],
    '<': ['...#.', '..#..', '.#...', '#....', '.#...', '..#..', '...#.'],
    '=': ['.....', '.....', '#####', '.....', '#####', '.....', '.....'],
    '>': ['.#...', '..#..', '...#.', '....#', '...#.', '..#..', '.#...'],
    '?': ['.###.', '#...#', '....#', '...#.', '..#..', '.....', '..#..'],
    '@': ['.###.', '#...#', '....#', '.##.#', '#.#.#', '#.#.#', '.###.'],
    'A': ['.###.', '#...#', '#...#', '#...#', '#####', '#...#', '#...#'],
    'B': ['####.', '#...#', '#...#', '####.', '#...#', '#...#', '####.'],
    'C': ['.###.', '#...#', '#....', '#....', '#....', '#...#', '.###.'],
    'D': ['###..', '#..#.', '#...#', '#...#', '#...#', '#..#.', '###..'],
    'E': ['#####', '#....', '#....', '####.', '#....', '#....', '#####'],
    'F': ['#####', '#....', '#....', '####.', '#....', '#....', '#....'],
    'G': ['.###.', '#...#', '#....', '#.###', '#...#', '#...#', '.####'],
    'H': ['#...#', '#...#', '#...#', '#####', '#...#', '#...#', '#...#'],
    'I': ['.###.', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'J': ['..###', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'],
    'K': ['#...#', '#..#.', '#.#..', '##...', '#.#..', '#..#.', '#...#'],
    'L': ['#....', '#....', '#....', '#....', '#....', '#....', '#####'],
    'M': ['#...#', '##.##', '#.#.#', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#...#', '#...#', '##..#', '#.#.#', '#..##', '#...#', '#...#'],
    'O': ['.###.', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'P': ['####.', '#...#', '#...#', '####.', '#....', '#....', '#....'],
    'Q': ['.###.', '#...#', '#...#', '#...#', '#.#.#', '#..#.', '.##.#'],
    'R': ['####.', '#...#', '#...#', '####.', '#.#..', '#..#.', '#...#'],
    'S': ['.####', '#....', '#....', '.###.', '....#', '....#', '####.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#...#', '#...#', '#...#', '#...#', '#...#', '#...#', '.###.'],
    'V': ['#...#', '#...#', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#...#', '#.#.#', '#.#.#', '#.#.#', '.#.#.'],
    'X': ['#...#', '#...#', '.#.#.', '..#..', '.#.#.', '#...#', '#...#'],
    'Y': ['#...#', '#...#', '#...#', '.#.#.', '..#..', '..#..', '..#..'],
    'Z': ['#####', '....#', '...#.', '..#..', '.#...', '#....', '#####'],
    '[': ['.###.', '.#...', '.#...', '.#...', '.#...', '.#...', '.###.'],
    ']': ['.###.', '...#.', '...#.', '...#.', '...#.', '...#.', '.###.'],
    '^': ['..#..', '.#.#.', '#...#', '.....', '.....', '.....', '.....'],
    '`': ['.#...', '..#..', '.....', '.....', '.....', '.....', '.....'],
    'a': ['.....', '.....', '.###.', '....#', '.####', '#...#', '.####'],
    'b': ['#....', '#....', '#.##.', '##..#', '#...#', '#...#', '####.'],
    'c': ['.....', '.....', '.###.', '#....', '#....', '#...#', '.###.'],
    'd': ['....#', '....#', '.##.#', '#..##', '#...#', '#...#', '.####'],
    'e': ['.....', '.....', '.###.', '#...#', '#####', '#....', '.###.'],
    'f': ['..##.', '.#..#', '.#...', '###..', '.#...', '.#...', '.#...'],
    'g': ['.....', '.....', '.####', '#...#', '#...#', '#...#', '.####', '....#', '.###.'],
    'h': ['#....', '#....', '#.##.', '##..#', '#...#', '#...#', '#...#'],
    'i': ['..#..', '.....', '.##..', '..#..', '..#..', '..#..', '.###.'],
    'j': ['...#.', '.....', '..##.', '...#.', '...#.', '...#.', '...#.', '#..#.', '.##..'],
    'k': ['#....', '#....', '#..#.', '#.#..', '##...', '#.#..', '#..#.'],
    'l': ['.##..', '..#..', '..#..', '..#..', '..#..', '..#..', '.###.'],
    'm': ['.....', '.....', '##.#.', '#.#.#', '#.#.#', '#...#', '#...#'],
    'n': ['.....', '.....', '#.##.', '##..#', '#...#', '#...#', '#...#'],
    'o': ['.....', '.....', '.###.', '#...#', '#...#', '#...#', '.###.'],
    'p': ['.....', '.....', '####.', '#...#', '#...#', '#...#', '####.', '#....', '#....'],
    'q': ['.....', '.....', '.####', '#...#', '#...#', '#...#', '.####', '....#', '....#'],
    'r': ['.....', '.....', '#.##.', '##..#', '#....', '#....', '#....'],
    's': ['.....', '.....', '.###.', '#....', '.###.', '....#', '####.'],
    't': ['.#...', '.#...', '####.', '.#...', '.#...', '.#..#', '..##.'],
    'u': ['.....', '.....', '#...#', '#...#', '#...#', '#..##', '.##.#'],
    'v': ['.....', '.....', '#...#', '#...#', '#...#', '.#.#.', '..#..'],
    'w': ['.....', '.....', '#...#', '#...#', '#.#.#', '#.#.#', '.#.#.'],
    'x': ['.....', '.....', '#...#', '.#.#.', '..#..', '.#.#.', '#...#'],
    'y': ['.....', '.....', '#...#', '#...#', '#...#', '#...#', '.####', '....#', '.###.'],
    'z': ['.....', '.....', '#####', '...#.', '..#..', '.#...', '#####'],
    '{': ['...#.', '..#..', '..#..', '.#...', '..#..', '..#..', '...#.'],
    '}': ['.#...', '..#..', '..#..', '...#.', '..#..', '..#..', '.#...'],
    '~': ['.....', '.....', '.#...', '#.#.#', '...#.', '.....', '.....'],
    '°': ['.#...', '#.#..', '.#...', '.....', '.....', '.....', '.....'],
    '·': ['.....', '.....', '.....', '..#..', '.....', '.....', '.....'],
    '▲': ['.....', '.....', '..#..', '.###.', '.###.', '#####', '.....'],
    '▼': ['.....', '#####', '.###.', '.###.', '..#..', '.....', '.....'],
    '◆': ['.....', '..#..', '.###.', '#####', '.###.', '..#..', '.....'],
    '→': ['.....', '..#..', '...#.', '#####', '...#.', '..#..', '.....'],
    '←': ['.....', '..#..', '.#...', '#####', '.#...', '..#..', '.....'],
    '↑': ['..#..', '.###.', '#.#.#', '..#..', '..#..', '..#..', '..#..'],
    '↓': ['..#..', '..#..', '..#..', '..#..', '#.#.#', '.###.', '..#..'],
    '↗': ['..###', '...##', '..#.#', '.#...', '#....', '.....', '.....'],
    '↘': ['.....', '.....', '#....', '.#...', '..#.#', '...##', '..###'],
}


def _build_rom():
    rom = {}
    for ch, rows in _FONT.items():
        a = np.zeros((10, 7), np.uint8)
        for g, line in enumerate(rows):
            assert len(line) == 5, ch
            for j, px in enumerate(line):
                if px == '#': a[g + 1, j + 1] = 1
        rom[ch] = a

    def cell():
        return np.zeros((10, 7), np.uint8)
    # art-friendly full-cell strokes: verticals and diagonals run the whole cell height, '_' the whole width,
    # so stacked characters join into lines
    a = cell(); a[:, 3] = 1; rom['|'] = a
    a = cell()
    for r in range(10): a[r, 5 - r // 2] = 1
    rom['/'] = a; rom['\\'] = a[:, ::-1].copy()
    a = cell(); a[9, :] = 1; rom['_'] = a
    # box drawing: horizontals on line 4, verticals on dot 3, meeting in the cell centre
    H, V = 4, 3

    def bx(l, r, u, d):
        a = cell()
        if l: a[H, :V + 1] = 1
        if r: a[H, V:] = 1
        if u: a[:H + 1, V] = 1
        if d: a[H:, V] = 1
        return a
    for ch, k in zip('─│┌┐└┘├┤┬┴┼', [(1, 1, 0, 0), (0, 0, 1, 1), (0, 1, 0, 1), (1, 0, 0, 1), (0, 1, 1, 0), (1, 0, 1, 0),
                                     (0, 1, 1, 1), (1, 0, 1, 1), (1, 1, 0, 1), (1, 1, 1, 0), (1, 1, 1, 1)]):
        rom[ch] = bx(*k)
    # the five scan-line bars of the plotting set (scan 1, 3, 5, 7, 9)
    for ch, r in zip('⎺⎻─⎼⎽', (0, 2, 4, 6, 8)):
        a = cell(); a[r, :] = 1; rom[ch] = a
    for ch, n in zip('▁▂▃▄▅▆▇█', (1, 2, 4, 5, 6, 8, 9, 10)):
        a = cell(); a[10 - n:, :] = 1; rom[ch] = a
    yy, xx = np.mgrid[0:10, 0:7]
    rom['░'] = ((yy % 2 == 0) & (xx % 2 == 0)).astype(np.uint8)
    rom['▒'] = ((yy + xx) % 2 == 0).astype(np.uint8)
    rom['▓'] = (~((yy % 2 == 1) & (xx % 2 == 1))).astype(np.uint8)
    chars = list(rom.keys())
    return chars, np.stack([rom[c] for c in chars]), {c: i for i, c in enumerate(chars)}


ROM_CHARS, ROM, ROM_INDEX = _build_rom()
SCAN = '⎽⎼─⎻⎺'                       # plotting bars, lowest to highest
EIGHTHS = ' ▁▂▃▄▅▆▇█'
LEVELS = {'dim': 0.40, 'normal': 0.70, 'bold': 1.0}
PHOSPHORS = {                        # emission tint (how fast each channel saturates) and the unlit face colour
    'green': dict(tint=(0.30, 1.0, 0.40), face=(0.036, 0.047, 0.042)),   # P1
    'amber': dict(tint=(1.0, 0.60, 0.14), face=(0.048, 0.042, 0.034)),   # P3
    'white': dict(tint=(0.88, 0.94, 1.0), face=(0.042, 0.045, 0.048)),   # P4
}
PUTTY = '#c9c0ac'                    # the bezel plastic


def _attr(a):
    """'bold', 'dim+rev', 'normal+ul' ... -> (level, reverse, underline)"""
    parts = (a or 'normal').split('+')
    lvl = LEVELS['normal']
    for p in parts:
        if p in LEVELS: lvl = LEVELS[p]
    return lvl, 'rev' in parts, 'ul' in parts


class CRTTerminal:
    def __init__(self, W=1920, H=1080, seed=0, cols=120, rows=36, phosphor='green',
                 opening=(88, 60, 1832, 958), radius=62, raster=(0.955, 0.93), curve=0.065,
                 bezel=PUTTY):
        """opening: the hole in the bezel (glass), px; raster: the undistorted raster size as a fraction of the
        opening; curve: radial barrel strength (the raster's corners pull in by about curve x the half-width)"""
        self.W, self.H, self.cols, self.rows = W, H, cols, rows
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.ph = PHOSPHORS[phosphor]
        self.opening, self.radius = opening, radius
        x0, y0, x1, y1 = opening
        self.ocx, self.ocy = (x0 + x1) / 2, (y0 + y1) / 2
        self.rw, self.rh = (x1 - x0) * raster[0], (y1 - y0) * raster[1]     # raster, undistorted, 1x px
        self.curve = curve
        self.pad = 1.0                                                        # raster margin round the text, cells
        self.cw = self.rw / (cols + 2 * self.pad)                             # cell size, px (undistorted)
        self.ch = self.rh / (rows + 2 * self.pad)
        # ---- character memory
        self.text = np.full((rows, cols), ' ', dtype='<U1')
        self.lvl = np.full((rows, cols), LEVELS['normal'], np.float32)
        self.rev = np.zeros((rows, cols), bool)
        self.ul = np.zeros((rows, cols), bool)
        self.mode = [''] * rows                       # '', 'dw', 'dht' (double height top), 'dhb'
        self.glow = np.zeros((rows * 10, cols * 7), np.float32)   # afterglow (persistence) dots
        self.worn = np.zeros((rows * 10, cols * 7), np.float32)   # burn-in, 0..1 loss of efficiency
        self.cur = None
        self.on = False
        self.brightness = 0.016                       # raster floor: the brightness knob is up a little
        self.tears = []
        # ---- hidden art map at dot resolution
        SY, SX = rows * 10, cols * 7
        self.inst = np.zeros((SY, SX), np.int32)
        self.tone = np.zeros((SY, SX), np.float32)
        self.dirx = np.zeros((SY, SX), np.float32)
        self.diry = np.zeros((SY, SX), np.float32)
        self.items = [None]
        self.materials = {}
        self.art_text = np.full((rows, cols), '', dtype='<U1')
        self.art_lvl = np.zeros((rows, cols), np.float32)
        self.stages = []
        self._case = None
        self._geom = None

    # ================================================================ terminal memory
    def write(self, col, row, s, attr='normal'):
        """put text into character memory at (col, row); attr: 'dim' | 'normal' | 'bold', '+rev', '+ul'"""
        lvl, rev, ul = _attr(attr)
        r = int(row)
        if not 0 <= r < self.rows: return
        step = 2 if self.mode[r] else 1
        for i, chx in enumerate(s):
            c = int(col) + i * step
            if not 0 <= c < self.cols: continue
            self.text[r, c] = chx if chx in ROM_INDEX else '?'
            self.lvl[r, c], self.rev[r, c], self.ul[r, c] = lvl, rev, ul

    def clear(self, c0=0, r0=0, c1=None, r1=None):
        c1 = self.cols if c1 is None else c1; r1 = self.rows if r1 is None else r1
        self.text[r0:r1, c0:c1] = ' '; self.rev[r0:r1, c0:c1] = False; self.ul[r0:r1, c0:c1] = False

    def big(self, col, row, s, attr='bold'):
        """a double-height, double-width line: rows `row` and `row + 1`; every character takes two columns"""
        self.mode[row], self.mode[row + 1] = 'dht', 'dhb'
        self.write(col, row, s, attr); self.write(col, row + 1, s, attr)

    def wide(self, col, row, s, attr='normal'):
        self.mode[row] = 'dw'
        self.write(col, row, s, attr)

    def cursor(self, col, row, shape='block'):
        self.cur = None if col is None else (int(col), int(row), shape)

    def hline(self, c0, c1, row, attr='dim', ch='─'):
        self.write(c0, row, ch * (c1 - c0 + 1), attr)

    def vline(self, col, r0, r1, attr='dim', ch='│'):
        for r in range(r0, r1 + 1): self.write(col, r, ch, attr)

    def box(self, c0, r0, c1, r1, attr='dim', title=None, title_attr='bold'):
        self.hline(c0 + 1, c1 - 1, r0, attr); self.hline(c0 + 1, c1 - 1, r1, attr)
        self.vline(c0, r0 + 1, r1 - 1, attr); self.vline(c1, r0 + 1, r1 - 1, attr)
        for (c, r), ch in zip([(c0, r0), (c1, r0), (c0, r1), (c1, r1)], '┌┐└┘'): self.write(c, r, ch, attr)
        if title:
            self.write(c0 + 2, r0, '┤', attr); self.write(c0 + 3, r0, ' ' + title + ' ', title_attr)
            self.write(c0 + 5 + len(title), r0, '├', attr)

    def trail(self, col, row, s, level=0.3):
        """afterglow: `s` was on screen at (col, row) a frame or two ago and is still fading (persistence).
        level: what is left of a bold character (0.3 one frame back, 0.1 two frames back)"""
        for i, chx in enumerate(s):
            c, r = int(col) + i, int(row)
            if not (0 <= c < self.cols and 0 <= r < self.rows) or chx == ' ': continue
            g = ROM[ROM_INDEX.get(chx, ROM_INDEX['?'])].astype(np.float32) * level
            sl = self.glow[r * 10:r * 10 + 10, c * 7:c * 7 + 7]
            np.maximum(sl, g, out=sl)

    def burn(self, col, row, s, depth=0.3):
        """burn-in: `s` sat at (col, row) for years and wore the phosphor (less light wherever its dots were)"""
        for i, chx in enumerate(s):
            c, r = int(col) + i, int(row)
            if not (0 <= c < self.cols and 0 <= r < self.rows) or chx == ' ': continue
            g = ROM[ROM_INDEX.get(chx, ROM_INDEX['?'])].astype(np.float32) * depth
            sl = self.worn[r * 10:r * 10 + 10, c * 7:c * 7 + 7]
            np.maximum(sl, g, out=sl)

    def tear(self, row, dx=6.0, lines=3):
        """a horizontal-sync slip: from scan line `row * 10 + 5` the beam starts `dx` px late for `lines` lines"""
        self.tears.append((float(row), float(dx), int(lines)))

    def power(self, on=True):
        self.on = on

    def listing(self, path=None):
        s = '\n'.join(''.join(r).rstrip() for r in self.text)
        if path:
            with open(path, 'w') as f: f.write(s + '\n')
        return s

    # ================================================================ hidden art map
    def material(self, name, ramp, attrs=None, outline='round', group=None, edge=None, dither=0.12):
        """a glyph vocabulary for a kind of thing. ramp: characters from faint to bright, e.g. ' .:-=+*#%@';
        attrs: one intensity per ramp entry (default: dim for the faint third, normal, bold for the top);
        outline: 'round' (( ) at upright sides, / \\ on slopes), 'cloud' (( ) on every slope, _ . - ' on flat
        tops and bases), 'straight' (| / \\), or None (no silhouette characters, tone only);
        group: materials in the same group are not outlined against each other;
        edge: fixed intensity for outline characters (default: from the tone at the edge); dither: tone noise"""
        n = len(ramp)
        if attrs is None:
            attrs = ['dim' if i < n / 3 else 'normal' if i < 2 * n / 3 else 'bold' for i in range(n)]
        self.materials[name] = dict(ramp=list(ramp), lv=[LEVELS[a] for a in attrs], outline=outline,
                                    group=group or name, edge=edge, dither=dither)

    def _grid(self):
        if not hasattr(self, '_gx'):
            SY, SX = self.rows * 10, self.cols * 7
            self._gy = ((np.arange(SY, dtype=np.float32) + 0.5) / 10)[:, None]
            self._gx = ((np.arange(SX, dtype=np.float32) + 0.5) / 7)[None, :]
        return self._gx, self._gy

    def _poly_mask(self, pts):
        SY, SX = self.rows * 10, self.cols * 7
        im = Image.new('L', (SX * 2, SY * 2), 0)
        ImageDraw.Draw(im).polygon([(float(c) * 14, float(r) * 20) for c, r in pts], fill=255)
        return np.asarray(im.resize((SX, SY), Image.BILINEAR), np.float32) / 255

    def ellipse(self, col, row, rx, ry):
        """rx in columns, ry in rows"""
        gx, gy = self._grid()
        d = np.sqrt(((gx - col) / rx) ** 2 + ((gy - row) / ry) ** 2)
        return np.clip((1 - d) * min(rx * 7, ry * 10) * 0.5 + 0.5, 0, 1)

    def circle(self, col, row, r):
        """a round disc of radius r columns (made round in pixels: cells are tall)"""
        return self.ellipse(col, row, r, r * self.cw / self.ch)

    def poly(self, pts):
        return self._poly_mask(pts)

    def shape(self, pts, per=10):
        """smooth closed outline through control points (col, row)"""
        P = np.asarray(pts, np.float32)
        return self._poly_mask(spline(np.vstack([P, P[:2]]), per)[per:-per + 1] if len(P) > 2 else P)

    def rect(self, c0, r0, c1, r1):
        return self._poly_mask([(c0, r0), (c1, r0), (c1, r1), (c0, r1)])

    def sphere_tone(self, col, row, r, light=(-0.5, -0.7, 0.5), amb=0.15, rim=0.0):
        """lit-sphere tone for a disc of radius r columns centred at (col, row)"""
        gx, gy = self._grid()
        ry = r * self.cw / self.ch
        u, v = (gx - col) / r, (gy - row) / ry
        z = np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
        L = np.array(light, np.float32); L /= np.linalg.norm(L)
        t = amb + (1 - amb) * np.clip(u * L[0] + v * L[1] + z * L[2], 0, 1)
        return np.clip(t + rim * (1 - z) ** 2, 0, 1)

    def radial_tone(self, col, row, r, t0=1.0, t1=0.0, power=1.0):
        gx, gy = self._grid()
        d = np.sqrt(((gx - col) / r) ** 2 + ((gy - row) / (r * self.cw / self.ch)) ** 2)
        return t1 + (t0 - t1) * np.clip(1 - d, 0, 1) ** power

    def ramp_tone(self, p0, p1, t0, t1):
        gx, gy = self._grid()
        d = np.array(p1, np.float32) - np.array(p0, np.float32)
        s = ((gx - p0[0]) * d[0] + (gy - p0[1]) * d[1]) / float(d @ d)
        return t0 + (t1 - t0) * np.clip(s, 0, 1)

    def fill(self, mask, material, tone=0.5):
        """paint a region (mask) with a material and tone (scalar or array); later fills cover earlier ones"""
        m = mask > 0.5
        self.items.append(dict(kind='fill', mat=material))
        k = len(self.items) - 1
        self.inst[m] = k
        t = np.broadcast_to(np.asarray(tone, np.float32), m.shape)
        self.tone[m] = t[m]
        return k

    def erase(self, mask):
        self.inst[mask > 0.5] = 0

    def stroke(self, pts, material, width=1.3, glyph=None, smooth=False, tone=0.7):
        """a line through (col, row) points; cells choose | / \\ _ - . ' by its direction, or `glyph` if given"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 10)
        SY, SX = self.rows * 10, self.cols * 7
        im = Image.new('L', (SX, SY), 0)
        dr = ImageDraw.Draw(im)
        dxy = np.zeros((SY, SX, 2), np.float32)
        for a, b in zip(P[:-1], P[1:]):
            seg = Image.new('L', (SX, SY), 0)
            ImageDraw.Draw(seg).line([(a[0] * 7, a[1] * 10), (b[0] * 7, b[1] * 10)], fill=255,
                                     width=max(1, int(round(width))))
            m = np.asarray(seg) > 0
            vx, vy = (b[0] - a[0]) * self.cw, (b[1] - a[1]) * self.ch          # direction in real pixels
            n = np.hypot(vx, vy) + 1e-6
            dxy[m] = (vx / n, vy / n)
            dr.line([(a[0] * 7, a[1] * 10), (b[0] * 7, b[1] * 10)], fill=255, width=max(1, int(round(width))))
        m = np.asarray(im) > 0
        self.items.append(dict(kind='stroke', mat=material, glyph=glyph))
        k = len(self.items) - 1
        self.inst[m] = k
        self.tone[m] = tone
        self.dirx[m], self.diry[m] = dxy[m, 0], dxy[m, 1]
        return k

    def puffs(self, puffs, material, light=(-0.5, -0.75, 0.45), amb=0.12, base=None, base_dark=0.35, flat=1.2):
        """a cloud made of round puffs [(col, row, r), ...]: one silhouette, each puff lit like a ball.
        base=row: the cloud is cut flat there (use a whole row number so the base prints as '_'), and the
        `flat` rows above it are filled out to the cloud's width (a flat underside, no scallops); the underside
        is shaded darker by base_dark"""
        mask = np.zeros_like(self.tone)
        tone = np.zeros_like(self.tone)
        for c, r, rad in puffs:
            m = self.circle(c, r, rad)
            t = self.sphere_tone(c, r, rad, light, amb)
            tone = np.where(m > 0.5, t, tone)                     # later puffs sit in front
            mask = np.maximum(mask, m)
        if base is not None:
            gx, gy = self._grid()
            k = int(np.clip((base - flat) * 10, 0, mask.shape[0] - 1))
            k1 = int(np.clip(base * 10, k + 1, mask.shape[0]))
            prof = (mask[k:k1].max(axis=0) > 0.5).astype(np.float32)
            for op, w in ((np.maximum, 9), (np.minimum, 9)):                 # close small gaps between puffs
                pp = np.pad(prof, w, mode='edge')
                prof = op.reduce([pp[i:i + len(prof)] for i in range(2 * w + 1)])
            prof = prof[None, :]
            band = (gy >= base - flat) & (gy < base)
            tone = np.where(band & (mask < 0.5), np.max(tone[k - 3:k + 1], axis=0, keepdims=True), tone)
            mask = np.where(band, np.maximum(mask, prof), mask)
            tone = tone * (1 - base_dark * smoothstep(base - 3, base, gy))
            mask = mask * (gy < base)
        return self.fill(mask, material, tone)

    def put(self, col, row, s, attr='normal', opaque=False):
        """place characters straight into the art layer (stars, rain, little hand-drawn sprites); they appear
        with the art on `reveal`. Spaces are transparent unless opaque=True (then they blank what is under)"""
        lvl = _attr(attr)[0]
        for i, chx in enumerate(s):
            c, r = int(col) + i, int(row)
            if (chx == ' ' and not opaque) or not (0 <= c < self.cols and 0 <= r < self.rows): continue
            self.art_text[r, c] = chx if chx in ROM_INDEX else '?'
            self.art_lvl[r, c] = lvl

    def sprite(self, col, row, lines, attr='normal', attrs=None, swap=None):
        """a small piece of hand-made ASCII art (list of strings) into the art layer, top-left at (col, row).
        Spaces between a line's first and last character are opaque (a house hides the hill behind it).
        attrs: {character: attr} for single characters; swap: {character: replacement} (lit windows...)"""
        for j, line in enumerate(lines):
            s0, s1 = len(line) - len(line.lstrip()), len(line.rstrip())
            for i in range(s0, s1):
                chx = line[i]
                a = (attrs or {}).get(chx, attr)
                chx = (swap or {}).get(chx, chx)
                self.put(col + i, row + j, chx, a, opaque=True)

    def plot(self, col, row, w, h, xs, ys, xlim, ylim, attr='bold', glyphs=SCAN):
        """a curve plotted the terminal way: one scan-line bar per column, five heights per character row.
        Returns a function (x, y) -> (col, row) for labels"""
        xs, ys = np.asarray(xs, np.float32), np.asarray(ys, np.float32)
        n = len(glyphs)
        for c in range(int(col), int(col + w)):
            x = xlim[0] + (c + 0.5 - col) / w * (xlim[1] - xlim[0])
            if x < xs.min() or x > xs.max(): continue
            y = float(np.interp(x, xs, ys))
            lev = int(np.clip(np.round((y - ylim[0]) / (ylim[1] - ylim[0]) * (h * n - 1)), 0, h * n - 1))
            self.write(c, row + h - 1 - lev // n, glyphs[lev % n], attr)

        def at(x, y):
            return (col + (x - xlim[0]) / (xlim[1] - xlim[0]) * w,
                    row + h - 1 - (y - ylim[0]) / (ylim[1] - ylim[0]) * (h - 0.2))
        return at

    def bars(self, col, row, h, values, vmax, attr='normal'):
        """a column of block characters per value (eighths of a row), standing on row + h - 1"""
        for i, v in enumerate(values):
            e = int(round(np.clip(v / vmax, 0, 1) * h * 8))
            for k in range(h):
                q = int(np.clip(e - 8 * k, 0, 8))
                if q: self.write(col + i, row + h - 1 - k, EIGHTHS[q], attr)

    # ================================================================ characters from the art map
    def _edge_glyph(self, nx, ny, py, outline, stroke=False):
        """outward normal (nx, ny) in px, py = where the edge sits in the cell (0 top .. 1 bottom)"""
        tx, ty = -ny, nx
        phi = np.degrees(np.arctan2(abs(ty), abs(tx) + 1e-9))
        if phi < (30 if outline == 'cloud' else 24):      # flat
            if py < 0.3: return "'" if not stroke else '-'
            if py < 0.58: return '-'
            if py < 0.82: return '.' if not stroke else '-'
            return '_'
        if outline == 'cloud':                            # puffs: every slope is a ( or a )
            return '(' if nx < 0 else ')'
        if phi > 64:                                      # upright
            if outline == 'round': return '(' if nx < 0 else ')'
            return '|'
        return '/' if nx * ny > 0 else '\\'

    def compose(self, region=None):
        """turn the hidden art map into characters (stored; `reveal` copies them into character memory).
        Every cell is one of: a stroke cell (the stroke's direction), an edge cell (a silhouette runs through it:
        the edge's direction and height in the cell), a border cell (a silhouette runs along one of its sides),
        or an interior cell (the material's ramp by tone, error diffusion within the material's group)."""
        R, C = self.rows, self.cols
        r0, r1, c0, c1 = region or (0, R, 0, C)
        cw, ch = self.cw, self.ch
        yy, xx = np.mgrid[0:10, 0:7].astype(np.float32)
        yy = (yy + 0.5) / 10; xx = (xx + 0.5) / 7
        I = self.inst.reshape(R, 10, C, 7).transpose(0, 2, 1, 3)
        T = self.tone.reshape(R, 10, C, 7).transpose(0, 2, 1, 3)
        DX = self.dirx.reshape(R, 10, C, 7).transpose(0, 2, 1, 3)
        DY = self.diry.reshape(R, 10, C, 7).transpose(0, 2, 1, 3)
        # coverage of every material group per cell (silhouettes are between groups)
        groups = sorted({m['group'] for m in self.materials.values()})
        gid = {g: i + 1 for i, g in enumerate(groups)}
        inst_g = np.zeros(len(self.items), np.int32)
        for k, it in enumerate(self.items[1:], 1): inst_g[k] = gid[self.materials[it['mat']]['group']]
        G = inst_g[self.inst]
        fills_only = np.array([0] + [it['kind'] == 'fill' for it in self.items[1:]], bool)[self.inst]
        gcov = {g: ((G == g) & fills_only).reshape(R, 10, C, 7).mean(axis=(1, 3)) for g in gid.values()}
        anyart = (self.inst > 0).reshape(R, 10, C, 7).any(axis=(1, 3))
        out = np.full((R, C), '', dtype='<U1'); lv = np.zeros((R, C), np.float32)
        kind = np.zeros((R, C), np.int8)                   # 1 interior, 2 edge, 3 border, 4 stroke
        who = np.zeros((R, C), np.int32); strength = np.zeros((R, C), np.float32)
        tone = np.zeros((R, C), np.float32)
        cov = np.zeros((R, C), np.float32)
        for r in range(r0, r1):
            for c in range(c0, c1):
                P = I[r, c]
                if not anyart[r, c]: continue
                ids, cnt = np.unique(P, return_counts=True)
                st = [(i, n) for i, n in zip(ids, cnt) if i and self.items[i]['kind'] == 'stroke' and n >= 5]
                if st:                                        # strokes win where they really cross the cell
                    i, n = max(st, key=lambda a: a[0])
                    it = self.items[i]; mt = self.materials[it['mat']]
                    m = P == i
                    if it['glyph']:
                        g = it['glyph']
                    else:
                        ax, ay = DX[r, c][m], DY[r, c][m]
                        th = 0.5 * np.arctan2(np.mean(2 * ax * ay), np.mean(ax * ax - ay * ay))
                        tx, ty = np.cos(th), np.sin(th)
                        g = self._edge_glyph(-ty, tx, float(yy[m].mean()), 'straight', stroke=True)
                        if len(st) > 1:                           # two strokes crossing
                            j = sorted(st, key=lambda a: -a[0])[1][0]
                            bx_, by_ = DX[r, c][P == j], DY[r, c][P == j]
                            th2 = 0.5 * np.arctan2(np.mean(2 * bx_ * by_), np.mean(bx_ * bx_ - by_ * by_))
                            if abs(np.sin(th - th2)) > 0.6:
                                g = 'X' if abs(np.sin(2 * th)) > 0.5 else '+'
                    t = float(T[r, c][m].mean())
                    out[r, c] = g; lv[r, c] = mt['edge'] or self._lv_for(t)
                    kind[r, c] = 4; strength[r, c] = n; who[r, c] = i
                    continue
                fl = [(i, n) for i, n in zip(ids, cnt) if i and self.items[i]['kind'] == 'fill']
                if not fl: continue
                big = [i for i, n in fl if n >= 7]
                A = max(big) if big else max(fl, key=lambda a: a[1])[0]
                mA = P == A
                f = float(mA.mean())
                mt = self.materials[self.items[A]['mat']]
                ga = inst_g[A]
                t = float(T[r, c][mA].mean())
                who[r, c] = A; tone[r, c] = t
                same = (G[r * 10:r * 10 + 10, c * 7:c * 7 + 7] == ga) & fills_only[r * 10:r * 10 + 10, c * 7:c * 7 + 7]
                fg = float(same.mean())
                cov[r, c] = fg
                if mt['outline'] is None:
                    if fg < 0.3: continue
                    tone[r, c] = float(T[r, c][same].mean()) * min(1.0, fg / 0.8)
                    kind[r, c] = 1
                    continue
                if fg >= 0.86:
                    # interior -- unless a side of the cell is a silhouette
                    nb = []
                    for dc, dr_ in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        rr, cc = r + dr_, c + dc
                        if 0 <= rr < R and 0 <= cc < C and gcov[ga][rr, cc] < 0.07:
                            nb.append((dc, dr_))
                    if not nb:
                        kind[r, c] = 1
                        continue
                    nx = sum(d[0] for d in nb) / cw; ny = sum(d[1] for d in nb) / ch
                    if abs(nx) + abs(ny) < 1e-6:
                        kind[r, c] = 1
                        continue
                    nn = np.hypot(nx, ny); nx, ny = nx / nn, ny / nn
                    if abs(ny) > 0.9 and ny < 0:              # flat top on the cell boundary: '_' in the cell above
                        if r - 1 >= r0 and not anyart[r - 1, c] and out[r - 1, c] == '':
                            out[r - 1, c] = '_'; lv[r - 1, c] = mt['edge'] or self._lv_for(t)
                            kind[r - 1, c] = 3; who[r - 1, c] = A
                        kind[r, c] = 1
                        continue
                    py = 1.0 if ny > 0 else 0.5
                    out[r, c] = self._edge_glyph(nx, ny, py, mt['outline'])
                    lv[r, c] = mt['edge'] or self._lv_for(t)
                    kind[r, c] = 3
                    continue
                if f < 0.07: continue
                # an edge runs through the cell: its direction from the first moment of the covered samples
                mx = float((xx * mA).sum() / mA.sum() - 0.5); my = float((yy * mA).sum() / mA.sum() - 0.5)
                nx, ny = -mx / cw, -my / ch                   # a normal: scales inversely with the cell size
                if abs(nx) + abs(ny) < 1e-3: continue
                nn = np.hypot(nx, ny); nx, ny = nx / nn, ny / nn
                py = (1 - f) if ny < 0 else f
                if ny < -0.9 and py < 0.3 and r - 1 >= r0 and not anyart[r - 1, c] and out[r - 1, c] == '':
                    out[r - 1, c] = '_'; lv[r - 1, c] = mt['edge'] or self._lv_for(t)
                    kind[r - 1, c] = 3; who[r - 1, c] = A
                    kind[r, c] = 1
                    continue
                out[r, c] = self._edge_glyph(nx, ny, py, mt['outline'])
                lv[r, c] = mt['edge'] or self._lv_for(t)
                kind[r, c] = 2; strength[r, c] = f
        # a silhouette is one character thick: of two touching edge cells with the same upright / slanted
        # character keep the one the edge runs closest to the middle of; the other becomes inside or outside
        for r in range(r0, r1):
            for c in range(c0, c1 - 1):
                if kind[r, c] in (2, 3) and kind[r, c + 1] in (2, 3) and out[r, c] == out[r, c + 1] and \
                        out[r, c] in '/\\()|' and inst_g[who[r, c]] == inst_g[who[r, c + 1]]:
                    k = c if abs(cov[r, c] - 0.5) > abs(cov[r, c + 1] - 0.5) else c + 1
                    out[r, k] = ''
                    kind[r, k] = 1 if cov[r, k] >= 0.5 else 0
        for r in range(r0, r1 - 1):
            for c in range(c0, c1):
                if kind[r, c] in (2, 3) and kind[r + 1, c] in (2, 3) and out[r, c] in "_.-'" and \
                        out[r + 1, c] in "_.-'" and inst_g[who[r, c]] == inst_g[who[r + 1, c]]:
                    k = r if abs(cov[r, c] - 0.5) > abs(cov[r + 1, c] - 0.5) else r + 1
                    out[k, c] = ''
                    kind[k, c] = 1 if cov[k, c] >= 0.5 else 0
        # interiors: each material's ramp by tone, Floyd-Steinberg within the group
        err = np.zeros((R + 1, C + 2), np.float32)
        rng = np.random.default_rng(self.seed + 11)
        for r in range(r0, r1):
            for c in range(c0, c1):
                if kind[r, c] != 1: continue
                A = who[r, c]; mt = self.materials[self.items[A]['mat']]; ga = inst_g[A]
                n = len(mt['ramp'])
                x = tone[r, c] * (n - 1) + err[r, c + 1] + rng.normal(0, mt['dither'])
                q = int(np.clip(np.round(x), 0, n - 1))
                e = x - q
                for dc, dr_, w in ((1, 0, 7 / 16), (-1, 1, 3 / 16), (0, 1, 5 / 16), (1, 1, 1 / 16)):
                    rr, cc = r + dr_, c + dc
                    if rr < R and 0 <= cc < C and kind[rr, cc] == 1 and inst_g[who[rr, cc]] == ga:
                        err[rr, cc + 1] += e * w
                g = mt['ramp'][q]
                if g != ' ':
                    out[r, c] = g; lv[r, c] = mt['lv'][q]
        # one stroke cell per row across, one per column up: keep the stronger of two touching duplicates
        for r in range(r0, r1):
            for c in range(c0, c1 - 1):
                if kind[r, c] == 4 and kind[r, c + 1] == 4 and who[r, c] == who[r, c + 1] and \
                        out[r, c] == out[r, c + 1] and out[r, c] in '|/\\':
                    k = c if strength[r, c] < strength[r, c + 1] else c + 1
                    out[r, k] = ''; kind[r, k] = 0
        for r in range(r0, r1 - 1):
            for c in range(c0, c1):
                if kind[r, c] == 4 and kind[r + 1, c] == 4 and who[r, c] == who[r + 1, c] and \
                        out[r, c] in "_.-'" and out[r + 1, c] in "_.-'":
                    k = r if strength[r, c] < strength[r + 1, c] else r + 1
                    out[k, c] = ''; kind[k, c] = 0
        sel = (slice(r0, r1), slice(c0, c1))
        self.art_text[sel] = out[sel]
        self.art_lvl[sel] = lv[sel]
        self.art_kind = kind
        return out

    @staticmethod
    def _lv_for(t):
        return LEVELS['bold'] if t > 0.62 else LEVELS['normal'] if t > 0.3 else LEVELS['dim']

    def reveal(self, r0=0, r1=None, c0=0, c1=None):
        """copy composed art into character memory (rows r0..r1); blank art cells leave the text alone"""
        r1 = self.rows if r1 is None else r1; c1 = self.cols if c1 is None else c1
        m = np.zeros((self.rows, self.cols), bool)
        m[r0:r1, c0:c1] = self.art_text[r0:r1, c0:c1] != ''
        self.text[m] = self.art_text[m]
        self.lvl[m] = self.art_lvl[m]
        self.rev[m] = False

    # ================================================================ the beam
    def _dots(self):
        """character memory -> dot raster at half-dot resolution (rows*10, cols*14) of beam levels.
        Dot stretching (each lit dot lasts half a dot longer) happens here, before reverse video, so the dark
        strokes of reversed characters stay as readable as the lit strokes of normal ones"""
        R, C = self.rows, self.cols
        code = np.vectorize(lambda s: ROM_INDEX.get(s, ROM_INDEX['?']))(self.text)
        G = ROM[code].astype(np.float32)                                       # (R, C, 10, 7)
        G[..., 9, :] = np.where(self.ul[..., None], 1.0, G[..., 9, :])
        G = np.repeat(G, 2, axis=3)                                            # half dots: (R, C, 10, 14)
        G[..., 1:] = np.maximum(G[..., 1:], G[..., :-1])                       # dot stretching
        if self.cur:
            c, r, shape = self.cur
            if 0 <= r < R and 0 <= c < C:
                if shape == 'block': self.rev[r, c] = not self.rev[r, c]
                else: G[r, c, 8:10, :] = 1
        G = np.where(self.rev[..., None, None], 1 - G, G)
        if self.cur and self.cur[2] == 'block':
            c, r, _ = self.cur
            if 0 <= r < R and 0 <= c < C: self.rev[r, c] = not self.rev[r, c]
        G *= self.lvl[..., None, None]
        for r, md in enumerate(self.mode):                                   # double width / height lines
            if not md: continue
            for c in range(0, C - 1, 2):
                g = G[r, c]
                if md == 'dht': g = g[np.arange(10) // 2]
                elif md == 'dhb': g = g[5 + np.arange(10) // 2]
                g2 = np.repeat(g[:, ::2], 4, axis=1)                           # (10, 28): every dot twice as wide
                g2[:, 1:] = np.maximum(g2[:, 1:], g2[:, :-1])
                G[r, c], G[r, c + 1] = g2[:, :14], g2[:, 14:]
        D = G.transpose(0, 2, 1, 3).reshape(R * 10, C * 14)
        D = np.maximum(D, np.repeat(self.glow, 2, axis=1))
        return D * (1 - np.repeat(self.worn, 2, axis=1))

    def _raster(self):
        """dot raster -> beam-painted raster at 2x (unwarped), float32 light"""
        D = self._dots()
        p = int(round(self.pad))
        D = np.pad(D, ((p * 10, p * 10), (p * 14, p * 14)))
        Hs, Ws = D.shape
        RW2, RH2 = int(round(self.rw * 2)), int(round(self.rh * 2))
        q = RW2 / Ws * 2                                                        # px per dot
        xs = (np.arange(RW2) + 0.5) / (q / 2)
        S = D[:, np.clip(xs.astype(np.int32), 0, Ws - 1)]
        # video amplifier bandwidth: causal exponential smoothing (soft rise, a trail to the right)
        a = 1 - np.exp(-1.0 / (0.30 * q))
        K = int(4 * 0.30 * q) + 2
        ker = a * (1 - a) ** np.arange(K, dtype=np.float32)
        ker /= ker.sum()
        Sm = np.zeros_like(S)
        for k, w in enumerate(ker):
            Sm[:, k:] += w * S[:, :RW2 - k]
        S = Sm
        for row, dx, lines in self.tears:                                       # sync slips
            k0 = int((row + self.pad) * 10 + 5)
            sh = int(round(dx * 2))
            for k in range(k0, min(Hs, k0 + lines)):
                S[k] = np.concatenate([np.zeros(sh, np.float32), S[k, :-sh]]) + 0.06 * (S[k] > 0.05).mean()
        S = S + self.brightness                                                 # the whole raster glows a little
        # the beam: a gaussian spot per scan line that grows with the current (blooming)
        pitch = RH2 / Hs
        y = np.arange(RH2, dtype=np.float32) + 0.5
        k0 = np.floor(y / pitch - 0.5).astype(np.int32)
        out = np.zeros((RH2, RW2), np.float32)
        for n in (-1, 0, 1, 2):
            k = k0 + n
            ok = (k >= 0) & (k < Hs)
            kk = np.clip(k, 0, Hs - 1)
            d = (y - (kk + 0.5) * pitch)[:, None]
            V = S[kk]
            sig = pitch * (0.17 + 0.20 * np.sqrt(np.clip(V, 0, 1.5)))
            out += np.where(ok[:, None], V * np.exp(-0.5 * (d / sig) ** 2), 0)
        return out

    # ================================================================ the tube
    def _geometry(self):
        """per output pixel (2 x 2 sub-samples) inside the opening: where it lands on the raster.
        Radial barrel in real pixels: src = p (1 + k |p|^2 / hw^2), so letters are not sheared sideways"""
        if self._geom is not None: return self._geom
        x0, y0, x1, y1 = self.opening
        H, W = y1 - y0, x1 - x0
        cx, cy = self.ocx - x0, self.ocy - y0
        hw, hh = self.rw / 2, self.rh / 2
        k = self.curve
        subs = []
        for oy in (0.25, 0.75):
            for ox in (0.25, 0.75):
                px = (np.arange(W, dtype=np.float32) + ox - cx)[None, :]
                py = (np.arange(H, dtype=np.float32) + oy - cy)[:, None]
                f = 1 + k * (px * px + py * py) / (hw * hw)
                subs.append(((px * f + hw) * 2 - 0.5, (py * f + hh) * 2 - 0.5))
        u = ((np.arange(W, dtype=np.float32) + 0.5 - cx) / hw)[None, :]
        v = ((np.arange(H, dtype=np.float32) + 0.5 - cy) / hh)[:, None]
        self._geom = (subs, u, v)
        return self._geom

    @staticmethod
    def _bilinear(img, sx, sy):
        Hs, Ws = img.shape
        x0 = np.floor(sx).astype(np.int32); y0 = np.floor(sy).astype(np.int32)
        fx = (sx - x0).astype(np.float32); fy = (sy - y0).astype(np.float32)
        out = np.zeros(np.broadcast(sx, sy).shape, np.float32)
        for dy, wy in ((0, 1 - fy), (1, fy)):
            for dx, wx in ((0, 1 - fx), (1, fx)):
                xx, yy = x0 + dx, y0 + dy
                ok = (xx >= 0) & (xx < Ws) & (yy >= 0) & (yy < Hs)
                out += np.where(ok, img[np.clip(yy, 0, Hs - 1), np.clip(xx, 0, Ws - 1)], 0) * wx * wy
        return out

    def _opening_sdf(self, X, Y):
        x0, y0, x1, y1 = self.opening
        a, b, r = (x1 - x0) / 2, (y1 - y0) / 2, self.radius
        qx = np.abs(X - self.ocx) - (a - r)
        qy = np.abs(Y - self.ocy) - (b - r)
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r

    def _screen_light(self):
        """phosphor light inside the opening at 1x (before glow), and the raster-space coordinates"""
        subs, u, v = self._geometry()
        x0, y0, x1, y1 = self.opening
        if not self.on:
            return np.zeros((y1 - y0, x1 - x0), np.float32)
        R2 = self._raster()
        L = np.zeros((y1 - y0, x1 - x0), np.float32)
        for sx, sy in subs:
            L += self._bilinear(R2, sx, sy)
        L *= 0.25
        # brightness falls off toward the edges of the tube; a faint hum bar rolls through
        f = 1 - 0.10 * (u * u + v * v) - 0.22 * (u * u) * (v * v)
        L *= np.clip(f, 0.4, 1) * (1 + 0.025 * np.sin(2 * np.pi * (v * 0.55 + 0.18)))
        # phosphor grain
        g = self.rng.random(L.shape, dtype=np.float32)
        L *= 1 + 0.10 * (g - 0.5)
        return L

    def _glass(self):
        """the unlit face: tinted glass, room reflections, the bezel's shadow (cached), at 1x inside the opening"""
        if hasattr(self, '_glass_rgb'): return self._glass_rgb
        x0, y0, x1, y1 = self.opening
        H, W = y1 - y0, x1 - x0
        _, u, v = self._geometry()
        face = np.array(self.ph['face'], np.float32)
        r2 = u * u + v * v
        base = face[None, None, :] * (1.0 + 0.35 * (1 - np.clip(r2, 0, 1.6) / 1.6))[..., None]
        # a ceiling sheen bending with the bulge of the glass
        sheen = np.exp(-((v + 0.80 - 0.10 * u * u) / 0.16) ** 2) * (1 - 0.6 * u * u) * 0.020
        # a window over the viewer's left shoulder, shrunk and bent by the convex glass
        wu, wv = u * (1 + 0.22 * r2), v * (1 + 0.22 * r2)
        win = ((wu > -0.86) & (wu < -0.44) & (wv > -0.80) & (wv < -0.28)).astype(np.float32)
        bars = (np.abs(wu + 0.65) < 0.012) | (np.abs(wv + 0.54) < 0.018)
        win = win * (1 - 0.85 * bars)
        win = blur(win, 11) * (0.55 + 0.45 * smoothstep(-0.28, -0.80, wv))
        refl = sheen[..., None] * np.array([0.85, 0.9, 1.0], np.float32) + \
            (win * 0.075)[..., None] * np.array([0.80, 0.86, 0.95], np.float32)
        # specks of dust catch the room light
        n = int(W * H / 9000)
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        for _ in range(n):
            x, y = self.rng.uniform(0, W), self.rng.uniform(0, H)
            rr = self.rng.uniform(0.5, 1.3)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=int(self.rng.uniform(30, 110)))
        dust = blur(np.asarray(im, np.float32) / 255, 0.6) * 0.05
        # the bezel shadows the top of the recessed glass; the corners are darker
        Y, X = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        sd = -self._opening_sdf(X, Y)                                      # distance inside the opening
        top = np.clip((Y - y0) / 36, 0, 1)
        shade = smoothstep(0, 22, sd) * (0.55 + 0.45 * top) * (1 - 0.25 * smoothstep(0.6, 1.3, r2))
        rgb = (base + refl + dust[..., None]) * shade[..., None]
        self._glass_rgb = (rgb.astype(np.float32), shade.astype(np.float32))
        return self._glass_rgb

    # ================================================================ the case
    def _case_rgb(self):
        """the putty plastic bezel, lit by the room (cached, with the static part of the green spill: how much
        each point of the chamfer faces the screen). Small parts (wheels, LED, icons) are worked in local windows"""
        if self._case is not None: return self._case
        H, W = self.H, self.W
        Y = np.arange(H, dtype=np.float32)[:, None]
        X = np.arange(W, dtype=np.float32)[None, :]
        d = self._opening_sdf(X, Y).astype(np.float32)
        bw, depth = 30.0, 17.0
        h = depth * smoothstep(0, 1, np.clip(d / bw, 0, 1)) ** 0.85
        h -= 1.1 * np.exp(-((d - bw - 13) / 1.8) ** 2)                      # mould seam round the opening
        # moulded stipple and a few sink marks
        h += noise2d(H, W, 2.5, 2, self.seed + 5) * 0.55
        h += noise2d(H, W, 9, 2, self.seed + 6) * 0.35
        h += noise2d(H, W, 220, 3, self.seed + 7) * 2.5
        # controls along the bottom: two thumbwheel slots and the LED's ring
        x0, y0, x1, y1 = self.opening
        by = min(H - 34.0, (y1 + H) / 2 + 16)
        self._wheels = [(W - 300, by), (W - 236, by)]
        self._led = (W - 150, by)
        for wx, wy in self._wheels:
            h[int(wy - 26):int(wy + 26), int(wx - 13):int(wx + 13)] -= 6.0
        lx, ly = self._led
        ys, xs = slice(int(ly - 14), int(ly + 14)), slice(int(lx - 14), int(lx + 14))
        rr = np.hypot(X[:, xs] - lx, Y[ys] - ly)
        h[ys, xs] += 1.6 * smoothstep(9.5, 7.5, rr) - 1.6 * smoothstep(7.5, 6.0, rr)
        n = height_normals(h)
        del h
        Lg = np.array([-0.32, -0.62, 0.72], np.float32); Lg /= np.linalg.norm(Lg)
        Hv = Lg + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        lam = np.clip(n @ Lg, 0, 1)
        shade = (0.30 + 0.62 * lam / Lg[2]) * (1.06 - 0.16 * (Y / H))         # nearer the ceiling light at the top
        shade *= 1 + 0.03 * (noise2d(H, W, 300, 2, self.seed + 8) - 0.5)     # uneven yellowing
        spec = np.clip(n @ Hv, 0, 1) ** 28 * 0.07
        rgb = _c(PUTTY)[None, None, :] * shade[..., None]
        rgb += spec[..., None]
        del lam, shade, spec
        # how much the chamfer faces the screen centre (for the green spill)
        dxs, dys = self.ocx - X, self.ocy - Y
        dn = np.hypot(dxs, dys) + 1e-3
        self._facing = (np.clip((n[..., 0] * dxs + n[..., 1] * dys) / dn, 0, 1) * (d > 0)).astype(np.float32)
        del n, dxs, dys, dn
        # thumbwheels: knurled discs standing in their slots, lit from above
        for wx, wy in self._wheels:
            ys, xs = slice(int(wy - 26), int(wy + 26)), slice(int(wx - 13), int(wx + 13))
            win = rgb[ys, xs]
            win *= 0.22                                                       # the dark slot
            yy = Y[ys] - wy; xx = X[:, xs] - wx
            m = (np.abs(xx) < 10) & (np.abs(yy) < 23.5)
            vy = np.clip(yy / 25, -0.999, 0.999)
            cyl = np.sqrt(1 - vy * vy)
            ang = np.arcsin(vy)
            ridge = np.abs(np.sin(ang * 13 + 0.6))                            # knurls, crowding toward the ends
            face = np.clip(-np.sin(ang * 13 + 0.6) * np.cos(ang * 13 + 0.6) * 2, -1, 1)
            lit = (0.18 + 0.75 * np.clip(-vy * 0.55 + cyl * 0.8, 0, 1)) * (0.62 + 0.38 * ridge) + 0.10 * face * cyl
            lit = np.clip(lit, 0.03, 1.2) * (0.55 + 0.45 * smoothstep(10, 8.5, np.abs(xx)))
            wc = np.array([0.46, 0.44, 0.41], np.float32)
            win[:] = np.where(m[..., None], wc * lit[..., None], win)
        # embossed icons beside the wheels: a sun (brightness) and a half disc (contrast)
        ox, oy = int(self._wheels[0][0] - 60), int(by - 20)
        iw, ih = int(self._wheels[1][0] + 60) - ox, 40
        ic = Image.new('L', (iw, ih), 0); dd = ImageDraw.Draw(ic)
        sx, sy = self._wheels[0][0] - 34 - ox, by - oy
        dd.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], outline=255, width=2)
        for k in range(8):
            a = k * np.pi / 4
            dd.line([(sx + 6.5 * np.cos(a), sy + 6.5 * np.sin(a)), (sx + 9.5 * np.cos(a), sy + 9.5 * np.sin(a))],
                    fill=255, width=2)
        cx2 = self._wheels[1][0] + 34 - ox
        dd.ellipse([cx2 - 8, sy - 8, cx2 + 8, sy + 8], outline=255, width=2)
        dd.pieslice([cx2 - 8, sy - 8, cx2 + 8, sy + 8], 90, 270, fill=255)
        icon = blur(np.asarray(ic, np.float32) / 255, 0.6)
        gy_, gx_ = np.gradient(icon)
        rgb[oy:oy + ih, ox:ox + iw] *= ((1 + (-gx_ * 0.6 - gy_ * 1.2) * 1.2) * (1 - 0.05 * icon))[..., None]
        np.clip(rgb, 0, 1, out=rgb)
        self._case = (rgb.astype(np.float32), d)
        return self._case

    # ================================================================ compositing
    def composite(self):
        W, H = self.W, self.H
        case, sdf = self._case_rgb()
        out = case.copy()
        x0, y0, x1, y1 = self.opening
        glass, gshade = self._glass()
        L = self._screen_light()
        tint = np.array(self.ph['tint'], np.float32)
        # light scattered in the faceplate: bloom close in, halation far out
        Lb = L * np.clip(L, 0, 1.6)                     # the brightest strokes scatter most (bold glows, dim doesn't)
        Lt = 1.25 * L + 0.55 * blur(L, 2.0) + 0.42 * blur(Lb, 13) + 0.24 * blur(Lb, 50)
        del Lb
        emit = 1 - np.exp(-Lt[..., None] * 2.4 * tint[None, None, :])
        del Lt
        scr = 1 - (1 - glass) * (1 - emit * (0.94 + 0.06 * gshade[..., None]))
        del emit
        # the opening: glass inside, a dark gasket line at the edge
        ins = smoothstep(0.5, -0.5, sdf[y0:y1, x0:x1])[..., None]
        gasket = np.exp(-((sdf[y0:y1, x0:x1] + 1.5) / 2.2) ** 2) * 0.75
        reg = out[y0:y1, x0:x1]
        reg[:] = reg * (1 - ins) + scr * ins
        reg *= (1 - gasket)[..., None]
        del scr
        lx, ly = self._led
        ys, xs = slice(int(ly - 40), int(ly + 40)), slice(int(lx - 40), int(lx + 40))
        rr = np.hypot(np.arange(xs.start, xs.stop, dtype=np.float32)[None, :] - lx,
                      np.arange(ys.start, ys.stop, dtype=np.float32)[:, None] - ly)
        led = smoothstep(6.0, 4.5, rr)[..., None]
        if self.on:
            # green spill from the screen onto the chamfer (the more it faces the screen, the more) and the face
            big = np.zeros((H, W), np.float32)
            big[y0:y1, x0:x1] = blur(L, 40) + blur(L, 120) * 0.6
            amt = blur(big, 30) * 5.0
            del big
            amt *= (0.20 + 2.2 * self._facing) * (sdf > 0)
            col = 1 - np.exp(-amt[..., None] * 1.6 * tint[None, None, :])
            del amt
            col *= 0.9
            out = 1 - (1 - out) * (1 - col)
            del col
            # the power LED
            lc = np.array([0.45, 1.0, 0.35], np.float32)
            w = out[ys, xs]
            w[:] = w * (1 - led) + (lc * 0.75 + 0.25) * led
            glow = (np.exp(-(rr / 9) ** 2) * 0.5 + np.exp(-(rr / 22) ** 2) * 0.12)[..., None]
            w[:] = 1 - (1 - w) * (1 - glow * lc)
        else:
            w = out[ys, xs]
            w[:] = w * (1 - led) + np.array([0.10, 0.16, 0.10], np.float32) * led
        return Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        """snapshot for the draw-on animation"""
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
