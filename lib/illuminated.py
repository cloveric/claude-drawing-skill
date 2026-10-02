"""illuminated — an opening of a late-medieval illuminated manuscript (c. 1400): vellum, textura written with a broad-
edged quill in iron-gall ink, vermilion rubrics, raised and burnished gold leaf, tempera initials with white-lead
tracery, an ivy-spray border and compass-drawn diagrams (numpy + Pillow only).

Model -- the page is made the way a scriptorium made it, one craft after another, and every craft is a method:
  codex      an open book seen from above on a dark desk: leather boards, a stack of page edges at the fore-edge,
             two leaves of vellum that darken and dip into the gutter (the page edges near the gutter bow inward).
  vellum     calf skin, scraped and pounced: warm cream with cloudy thicker (warmer) and thinner (cooler, more
             translucent) zones, a few faint veins, the hair-follicle speckle of the hair side, a fine scraped nap,
             and a low cockle -- the skin never lies flat, so the room light rolls across it.
  rule       prickings down the outer margin, pale plummet ruling at every line and the bounding verticals.
  scribe     textura quadrata from a simulated broad-edged quill. The nib is a short line segment held at a fixed
             angle (about 40 degrees); a stroke is the area that segment sweeps, so the width follows the direction
             of travel -- full on the diamond heads and feet, a hairline on the joins. Every letter is a handful of
             pen strokes (minims with diamond heads and feet, broken bows) with a little per-letter wobble. Iron-gall
             ink is nearly black where the quill was freshly dipped and browner as it runs dry (the scribe re-dips
             every few words), and darker along the stroke edges where it pooled. Long s inside words, round s at the
             end, '7' is the Tironian et, 'ꝑ' is p-with-a-bar for "per".
  rubricate  vermilion for titles and reserved words, capitals touched in red, paragraph marks alternating red and
             blue, and a pen line filler on short last lines.
  gild       gold leaf on a raised gesso cushion over red bole, burnished with a stone: a mirror, so its colour is
             the room it reflects. Every gold pixel takes its normal from the gesso dome (plus punched tooling, leaf
             seams and burnishing streaks), reflects the camera ray (a camera at finite height, so the angle changes
             across the page) and looks up a studio with a big soft window at the upper left. Flat gold reads gold,
             the cushion edges flare pale on the side facing the window and fall to dark olive on the other, and the
             punched dots glitter. Shell gold (powdered gold in gum) is matte and grainy instead.
  paint      tempera inside the outlines: granular azurite, rose, verdigris, vermilion, lead white; pigment pools a
             little at the edges and the paint has body (it catches the light). Then white-lead tracery, and a black
             pen outline round everything gilded or painted.
  penwork    ivy sprays: hairline tendrils grown recursively from a gold-and-colour bar border, ending in curls, gold
             ivy leaves, blue and rose flowers and gold bezants; red filigree round blue penwork initials.
  diagrams   compass-and-rule figures: an astrolabe whose plate is a real stereographic projection (tropics, equator,
             almucantars for a chosen latitude, horizon), with a shell-gold rete and a rule with sight vanes; a
             roundel of the planetary spheres with the names written round the rings.
  age        six hundred years: the writing on the other side of the leaf showing through, foxing, thumb soil on the
             lower outer corners, an iron-gall halo, flakes of gold lost down to the red bole, chips in the azurite.

Each large ornament is an object whose methods follow the workshop order, so a draw-on animation shows the page
being made: ink lines -> gold -> colours -> pen.

    from illuminated import Illuminated
    il = Illuminated(1920, 1080, seed=5)
    il.desk(); left, right = il.codex(200, 40, 1720, 1040)            # two page rects
    il.rule(350, 885, [122 + 50 * i for i in range(17)], prick_x=214)  # a ruled line at every x-height
    blk = il.column('*incipit liber.* | uoniam stelle circa terram mouentur ... ^prima est luna ... |',
                    350, 885, 140, 18, 50, indent=[(1, 350), (5, 596)])   # 5 lines wrap round the initial
    q = il.initial('Q', 350, 172, 232)
    il.scribe(blk); il.rubricate(blk)                                 # black text, then the red
    q.gild(); q.paint(); q.pen()                                      # gold first, then colour, then pen
    il.age(); il.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep, fbm1d


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- materials
VELLUM = '#eddcb6'
INK, INK_THIN = '#21160e', '#6b4a2d'                 # iron-gall: fresh / running dry
RED, RED_DARK, RED_THIN = '#c03a22', '#8e2312', '#d4643f'
AZURE, AZURE_DARK, AZURE_LIGHT = '#2f53a3', '#1b2f6e', '#5a7cc4'
ROSE, ROSE_DARK = '#c86576', '#8a3446'
GREEN, GREEN_DARK = '#4a8457', '#2b5636'
OCHRE = '#c79a4c'
WHITE = '#f5efe2'
SILVER = '#d9d6cc'
LEAD = '#5c5d62'
BOLE = '#9b4429'
RULE = '#a98a66'
DESK = '#2b1b11'
LEATHER = '#4c2918'

# burnished gold: brightness of the reflected room -> colour (dark olive .. gold .. pale highlight)
_GOLD_E = np.array([0.0, 0.2, 0.4, 0.58, 0.8, 1.1], np.float32)
_GOLD_C = np.array([[0.14, 0.08, 0.03], [0.36, 0.24, 0.08], [0.62, 0.44, 0.15], [0.85, 0.65, 0.26],
                    [0.98, 0.85, 0.50], [1.0, 0.97, 0.82]], np.float32)


def _gold_ramp(E):
    return np.stack([np.interp(E, _GOLD_E, _GOLD_C[:, k]) for k in range(3)], -1).astype(np.float32)


def _bbox(a, pad=0, thr=0.002):
    rows = np.flatnonzero((a > thr).any(1))
    if not len(rows): return None
    cols = np.flatnonzero((a > thr).any(0))
    H, W = a.shape
    return (slice(max(rows[0] - pad, 0), min(rows[-1] + 1 + pad, H)),
            slice(max(cols[0] - pad, 0), min(cols[-1] + 1 + pad, W)))


# ---------------------------------------------------------------- textura: every letter is a few broad-pen strokes
# units: x-height = 1, y down, y = 0 is the x-height line, y = 1 the baseline; ascenders reach -0.46, descenders 1.42.
P, D, DY = 0.40, 0.09, 0.11          # minim pitch, diamond reach (x), diamond drop (y)


def _post(x, t=0.0, b=1.0, head=True, foot=True):
    s = [(x - D, t), (x, t + DY)] if head else [(x, t)]
    s += [(x, b - DY), (x + D, b)] if foot else [(x, b)]
    return s


def _arch(x0, x1, b=1.0, foot=True):
    """hairline from the post at x0 up into a new post at x1"""
    s = [(x0, 0.17), (x1 - D, 0.0), (x1, DY)]
    s += [(x1, b - DY), (x1 + D, b)] if foot else [(x1, b)]
    return s


_O_L = [(0.17, -0.01), (0.0, 0.13), (0.0, 0.87), (0.15, 1.01)]
GLYPHS = {
    'a': ([[(0.02, 0.10), (0.16, -0.01), (0.36, 0.11), (0.36, 1 - DY), (0.36 + D, 1.0)],
           [(0.36, 0.42), (0.05, 0.53), (0.0, 0.63), (0.0, 0.88), (0.12, 1.0), (0.36, 0.86)]], 0.36 + P),
    'b': ([[(-D, -0.46), (0.0, -0.35), (0.0, 0.88), (0.14, 1.01), (0.37, 0.88), (0.37, 0.12), (0.22, -0.01), (0.0, 0.17)]],
          0.37 + P),
    'c': ([[(0.15, 0.0), (0.0, 0.13), (0.0, 1 - DY), (0.11, 1.0), (0.32, 0.88)], [(0.06, 0.0), (0.31, 0.12)]], 0.31 + 0.34),
    'd': ([[(0.27, -0.03), (0.0, 0.13), (0.0, 0.87), (0.15, 1.01)], [(-0.05, -0.42), (0.37, 0.12), (0.37, 0.88), (0.22, 1.01)]],
          0.37 + P),
    'e': ([[(0.15, 0.0), (0.0, 0.13), (0.0, 1 - DY), (0.11, 1.0), (0.33, 0.88)],
           [(0.06, 0.0), (0.32, 0.12), (0.32, 0.36), (0.0, 0.52)]], 0.33 + 0.36),
    'f': ([[(0.0, 1.0), (0.0, -0.28), (0.14, -0.44), (0.31, -0.35)], [(-0.12, 0.03), (0.22, 0.03)]], 0.52),
    'ſ': ([[(0.0, 1.0), (0.0, -0.28), (0.14, -0.44), (0.31, -0.35)]], 0.48),
    'g': ([[(0.17, -0.01), (0.0, 0.13), (0.0, 0.80), (0.14, 0.94), (0.37, 0.84)],
           [(0.15, -0.01), (0.37, 0.12), (0.37, 1.24), (0.22, 1.40), (-0.02, 1.32)], [(0.37, 0.03), (0.50, -0.04)]], 0.37 + P),
    'h': ([[(-D, -0.46), (0.0, -0.35), (0.0, 1 - DY), (D, 1.0)], [(0.0, 0.17), (P - D, 0.0), (P, DY), (P, 1.14), (P - 0.15, 1.34)]],
          2 * P),
    'i': ([_post(0.0), [(-0.04, -0.34), (0.05, -0.24)]], P),
    'j': ([[(-D, 0.0), (0.0, DY), (0.0, 1.2), (-0.13, 1.37)], [(-0.04, -0.34), (0.05, -0.24)]], P),
    'l': ([[(-D, -0.46), (0.0, -0.35), (0.0, 1 - DY), (0.12, 1.0)]], P + 0.04),
    'm': ([_post(0.0), _arch(0.0, P), _arch(P, 2 * P)], 3 * P),
    'n': ([_post(0.0), _arch(0.0, P)], 2 * P),
    'o': ([_O_L, [(0.15, -0.01), (0.38, 0.12), (0.38, 0.88), (0.22, 1.01)]], 0.38 + P),
    'p': ([[(-D, 0.0), (0.0, DY), (0.0, 1.42)], [(0.0, 0.17), (0.24, -0.01), (0.38, 0.12), (0.38, 0.88), (0.24, 1.01), (0.0, 0.88)],
           [(-0.12, 1.42), (0.12, 1.42)]], 0.38 + P),
    'ꝑ': ([[(-D, 0.0), (0.0, DY), (0.0, 1.42)], [(0.0, 0.17), (0.24, -0.01), (0.38, 0.12), (0.38, 0.88), (0.24, 1.01), (0.0, 0.88)],
           [(-0.12, 1.42), (0.12, 1.42)], [(-0.2, 1.2), (0.2, 1.2)]], 0.38 + P),
    'q': ([[(0.16, -0.01), (0.0, 0.13), (0.0, 0.87), (0.14, 1.01), (0.38, 0.86)], [(0.14, -0.02), (0.38, 0.12), (0.38, 1.42)],
           [(0.26, 1.42), (0.50, 1.42)]], 0.38 + P),
    'r': ([_post(0.0), [(0.0, 0.17), (0.14, 0.0), (0.27, 0.1)]], P + 0.22),
    's': ([[(0.32, 0.10), (0.18, -0.01), (0.02, 0.10), (0.02, 0.34), (0.30, 0.64), (0.30, 0.88), (0.16, 1.01), (-0.01, 0.92)]],
          0.32 + 0.38),
    't': ([[(0.0, -0.24), (0.0, 1 - DY), (0.12, 1.0)], [(-0.12, 0.03), (0.24, 0.03)]], P + 0.14),
    'u': ([[(-D, 0.0), (0.0, DY), (0.0, 1 - DY), (D, 1.0), (P, 0.83)], _post(P)], 2 * P),
    'v': ([[(-D, 0.0), (0.0, DY), (0.0, 0.72), (0.2, 1.0)], [(P - D, 0.0), (P, DY), (P, 0.6), (0.2, 1.0)]], 2 * P),
    'x': ([[(-0.06, 0.0), (0.04, 0.1), (0.32, 0.9), (0.42, 1.0)], [(0.36, 0.02), (0.0, 1.0)]], 0.42 + 0.32),
    'y': ([[(-D, 0.0), (0.0, DY), (0.0, 0.86), (0.1, 0.98), (P, 0.84)], [(P - D, 0.0), (P, DY), (P, 1.24), (P - 0.15, 1.40), (-0.04, 1.32)]],
          2 * P),
    'z': ([[(-0.04, 0.0), (0.06, 0.08), (0.34, 0.06), (0.02, 0.92), (0.32, 0.92), (0.42, 1.0)]], 0.38 + 0.32),
    '7': ([[(-0.08, 0.02), (0.28, 0.02), (0.14, 0.45), (0.14, 1.28)]], 0.30 + 0.32),
    '.': ([[(-0.03, 0.86), (0.06, 0.97)]], 0.30),
    '·': ([[(-0.03, 0.43), (0.06, 0.54)]], 0.30),
    ':': ([[(-0.03, 0.34), (0.06, 0.45)], [(-0.03, 0.86), (0.06, 0.97)]], 0.30),
    ',': ([[(-0.02, 0.86), (0.06, 0.96), (-0.04, 1.18)]], 0.28),
    ';': ([[(-0.03, 0.38), (0.06, 0.49)], [(-0.02, 0.86), (0.06, 0.96), (-0.04, 1.18)]], 0.30),
    '/': ([[(0.22, -0.05), (-0.02, 1.05)]], 0.34),
    '-': ([[(0.0, 0.50), (0.22, 0.36)], [(0.0, 0.66), (0.22, 0.52)]], 0.34),
    ' ': ([], 0.42),
}
GLYPHS = {k: ([np.array(s, np.float32) for s in v[0]], v[1]) for k, v in GLYPHS.items()}


def scribal(word):
    """modern spelling -> what the scribe writes: long s inside the word, round s at the end"""
    w = word.lower()
    out = []
    for i, ch in enumerate(w):
        nxt = w[i + 1] if i + 1 < len(w) else ''
        out.append('ſ' if ch == 's' and nxt.isalpha() else ch)
    return ''.join(out)


def word_width(word, xh):
    return sum(GLYPHS.get(ch, GLYPHS[' '])[1] for ch in word) * xh


def _hyphenate(tok, room, xh):
    """split a word token at a rough Latin syllable break so the first part plus a hyphen fits in `room` px"""
    w = tok['text']
    vow = set('aeiouy')
    core = w.rstrip('.,;:·')
    best = None
    for i in range(2, len(core) - 2):
        a, b = w[:i], w[i:]
        if not (set(b) & vow) or not (set(a) & vow): continue
        if not ((a[-1] in vow and b[0] not in vow) or (a[-1] not in vow and b[0] not in vow and a[-2] in vow)): continue
        if word_width(a + '-', xh) <= room: best = i
    if best is None or room < 3 * xh: return None
    a, b = w[:best] + '-', w[best:]
    return dict(tok, text=a, w=word_width(a, xh)), dict(tok, text=b, w=word_width(b, xh), touch=False)


class Block:
    """a laid-out column of text. words: list of dicts (text, x, y, xh, red, touch, kind); fillers: (x0, x1, y, xh)"""
    def __init__(self, words, fillers, lines, xh):
        self.words, self.fillers, self.lines, self.xh = words, fillers, lines, xh

    @property
    def bottom(self):
        return self.lines[-1] if self.lines else None


class Illuminated:
    def __init__(self, W=1920, H=1080, seed=0, ss=3, nib_angle=40.0):
        self.W, self.H, self.ss, self.nib_angle = W, H, ss, nib_angle
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.img = np.ones((H, W, 3), np.float32) * hexc(DESK)
        self.hmap = np.zeros((H, W), np.float32)       # relief seen by the room light (cockle, paint body)
        self.gold = np.zeros((H, W), np.float32)       # burnished leaf coverage
        self.gesso = np.zeros((H, W), np.float32)      # gilding cushion height + tooling, px
        self.shell = np.zeros((H, W), np.float32)      # shell-gold coverage
        self.inkm = np.zeros((H, W), np.float32)       # iron-gall coverage (for the halo)
        self.azm = np.zeros((H, W), np.float32)        # azurite coverage (it flakes)
        self.light = np.ones((H, W), np.float32)
        self.pagem = np.zeros((H, W), np.float32)
        self.t_fine = noise2d(H, W, 3, 2, self._seed())
        self.t_mid = noise2d(H, W, 18, 3, self._seed())
        self.t_big = noise2d(H, W, 260, 3, self._seed())
        self.t_wave = noise2d(H, W, 60, 2, self._seed())
        self.grain = self.rng.random((H, W)).astype(np.float32)
        self.gx, self.book, self.dip = W / 2, (0, 0, W, H), 0.0
        self._streak = None
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ rasterising (local box, ss x supersampled)
    def _raster(self, polys=(), lines=(), dots=(), pad=3, holes=()):
        """polys: [(N, 2)]; lines: [((N, 2), width)]; dots: [(x, y, r)]; holes: polys cut back out.
        Returns (mask, x0, y0) or None."""
        groups = [np.asarray(p, np.float32).reshape(-1, 2) for p in polys]
        groups += [np.asarray(l[0], np.float32).reshape(-1, 2) for l in lines]
        groups += [np.array([[x - r, y - r], [x + r, y + r]], np.float32) for x, y, r in dots]
        if not groups: return None
        allp = np.concatenate(groups)
        mw = max([0.0] + [float(l[1]) for l in lines])
        x0 = int(np.floor(allp[:, 0].min() - mw - pad)); y0 = int(np.floor(allp[:, 1].min() - mw - pad))
        x1 = int(np.ceil(allp[:, 0].max() + mw + pad)); y1 = int(np.ceil(allp[:, 1].max() + mw + pad))
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, self.W), min(y1, self.H)
        if x1 <= x0 or y1 <= y0: return None
        ss = self.ss
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        d = ImageDraw.Draw(im)
        off = np.array([x0, y0], np.float32)
        for p in polys:
            q = (np.asarray(p, np.float32).reshape(-1, 2) - off) * ss
            if len(q) >= 3: d.polygon(q.ravel().tolist(), fill=255)
        for p, w in lines:
            q = (np.asarray(p, np.float32).reshape(-1, 2) - off) * ss
            ww = max(1, int(round(w * ss)))
            if len(q) >= 2: d.line(q.ravel().tolist(), fill=255, width=ww, joint='curve')
            r = ww / 2
            for e in (q[0], q[-1]): d.ellipse((e[0] - r, e[1] - r, e[0] + r, e[1] + r), fill=255)
        for x, y, r in dots:
            cx, cy, rr = (x - x0) * ss, (y - y0) * ss, r * ss
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=255)
        for p in holes:
            q = (np.asarray(p, np.float32).reshape(-1, 2) - off) * ss
            if len(q) >= 3: d.polygon(q.ravel().tolist(), fill=0)
        return np.asarray(im.reduce(ss), np.float32) / 255, x0, y0

    def mask(self, polys=(), lines=(), dots=(), holes=()):
        """full-canvas anti-aliased mask of polygons, round-pen lines and dots (minus holes)"""
        out = np.zeros((self.H, self.W), np.float32)
        r = self._raster(polys, lines, dots, holes=holes)
        if r is not None:
            m, x0, y0 = r
            out[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m
        return out

    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def ring(self, cx, cy, r0, r1):
        d = np.hypot(self.XX - cx, self.YY - cy)
        return np.clip(np.minimum(r1 - d, d - r0) + 0.5, 0, 1)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        c, s = np.cos(np.radians(rot)), np.sin(np.radians(rot))
        u = (self.XX - cx) * c + (self.YY - cy) * s
        v = -(self.XX - cx) * s + (self.YY - cy) * c
        q = np.sqrt((u / rx) ** 2 + (v / ry) ** 2)
        return np.clip((1 - q) * min(rx, ry) + 0.5, 0, 1)

    # ------------------------------------------------------------ the desk and the book
    def desk(self, colour=DESK):
        """dark walnut: long grain along the boards, open pores, a lamp pool toward the book"""
        H, W, r = self.H, self.W, self.rng
        streak = np.asarray(Image.fromarray(r.random((H // 3, W // 40)).astype(np.float32)).resize((W, H), Image.BICUBIC))
        warp = noise2d(H, W, 300, 3, self._seed())
        band = 0.5 + 0.5 * np.sin(self.YY * 0.045 + warp * 18 + 3 * streak)
        fine = np.asarray(Image.fromarray(r.random((H, W // 12)).astype(np.float32)).resize((W, H), Image.BILINEAR))
        g = 0.72 + 0.22 * band + 0.10 * (fine - 0.5) + 0.12 * (streak - 0.5)
        pores = (r.random((H, W)) > 0.996).astype(np.float32)
        pores = blur(np.asarray(Image.fromarray(pores).resize((W, H))), 0.6) * 3
        g = g * (1 - 0.35 * np.clip(pores, 0, 1))
        col = _c(colour)[None, None] * g[..., None]
        col = col * (1 + 0.12 * (hexc('#5a3018') - _c(colour))[None, None] * (band[..., None] - 0.5))
        self.img = col.astype(np.float32)
        lamp = np.exp(-(((self.XX - W * 0.45) / (W * 0.62)) ** 2 + ((self.YY - H * 0.42) / (H * 0.85)) ** 2))
        self.light *= (0.55 + 0.55 * lamp).astype(np.float32)

    def codex(self, x0, y0, x1, y1, cover=LEATHER, squares=15, stack=7, dip=24):
        """an open book: boards, page stack, two vellum pages meeting at the gutter. Returns the two page rects."""
        gx = (x0 + x1) / 2
        self.gx, self.book, self.dip = gx, (x0, y0, x1, y1), dip
        # the book's shadow on the desk
        foot = self.mask([[(x0 - squares, y0 - squares), (x1 + squares, y0 - squares), (x1 + squares, y1 + squares),
                           (x0 - squares, y1 + squares)]])
        sh = blur(np.roll(np.roll(foot, 14, 0), 10, 1), 16)
        self.img *= (1 - 0.6 * sh * (1 - foot))[..., None]
        # leather boards (worn lighter at the edges)
        bx0, by0, bx1, by1 = x0 - squares, y0 - squares, x1 + squares, y1 + squares
        board = foot
        edge = np.minimum.reduce([self.XX - bx0, bx1 - self.XX, self.YY - by0, by1 - self.YY])
        wear = smoothstep(6, 0, edge) * (0.5 + 0.5 * self.t_mid)
        lc = _c(cover)[None, None] * (0.8 + 0.3 * self.t_mid[..., None] + 0.08 * (self.t_fine[..., None] - 0.5))
        lc = lc * (1 + 0.5 * wear[..., None]) + 0.05 * wear[..., None]
        self.img = self.img * (1 - board[..., None]) + lc * board[..., None]
        inner = self.mask([[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]])
        self.hmap += board * (1 - inner) * 0.8 * (self.t_fine - 0.5)
        # stack of page edges under the open leaves: outer edges fan out a little
        pages = [(x0, y0, gx, y1), (gx, y0, x1, y1)]
        vel = hexc(VELLUM)
        for k in range(stack, 0, -1):
            o = k * 1.6
            for (px0, py0, px1, py1), side in zip(pages, (-1, 1)):
                ox0 = px0 - o if side < 0 else px0
                ox1 = px1 + o if side > 0 else px1
                m = self.mask([[(ox0, py0 - o * 0.55), (ox1, py0 - o * 0.55), (ox1, py1 + o * 0.7), (ox0, py1 + o * 0.7)]])
                tone = (0.70 + 0.05 * (k % 2) - 0.02 * k) * vel
                self.img = self.img * (1 - m[..., None]) + tone * m[..., None]
        # the two open leaves
        for i, (px0, py0, px1, py1) in enumerate(pages):
            m = self.mask([self._page_outline(px0, py0, px1, py1, i)])
            self._vellum(m, i)
            self.pagem = np.maximum(self.pagem, m)
        # the leaves curl down into the gutter
        d = np.abs(self.XX - gx)
        inside = (self.YY > y0 - 30) & (self.YY < y1 + 30) & (self.XX > x0 - 30) & (self.XX < x1 + 30)
        g = 1 - 0.5 * np.exp(-d / 11) - 0.2 * np.exp(-d / 46) + 0.035 * np.exp(-((d - 120) / 55) ** 2)
        self.light *= np.where(inside, g, 1).astype(np.float32)
        return pages

    def _page_outline(self, px0, py0, px1, py1, i):
        n = 48
        w = lambda: 1.3 * fbm1d(n, 10, 3, self._seed())
        xs = np.linspace(px0, px1, n); ys = np.linspace(py0, py1, n)
        top = np.stack([xs, py0 + w()], 1)
        bot = np.stack([xs[::-1], py1 + w()], 1)
        if i == 0:   # left leaf: outer edge on the left, gutter straight
            right = np.array([[px1, py0], [px1, py1]], np.float32)
            left = np.stack([px0 + w(), ys[::-1]], 1)
            return np.concatenate([top, right, bot, left])
        left = np.array([[px0, py1], [px0, py0]], np.float32)
        right = np.stack([px1 + w(), ys], 1)
        return np.concatenate([top, right, bot, left])

    def _vellum(self, m, idx):
        """calf vellum inside mask m"""
        sl = _bbox(m, 2)
        h, w = m[sl].shape
        r = self.rng
        mm = m[sl][..., None]
        base = hexc(VELLUM)
        big = self.t_big[sl]
        warm = smoothstep(0.45, 0.85, noise2d(h, w, 150, 3, self._seed()))
        thin = smoothstep(0.62, 0.86, noise2d(h, w, 110, 3, self._seed()))
        col = base[None, None] * (1 + 0.07 * (big[..., None] - 0.5) + 0.025 * (self.t_wave[sl][..., None] - 0.5))
        col = col * (1 - 0.42 * warm[..., None]) + hexc('#dcc28e')[None, None] * 0.42 * warm[..., None]
        col = col * (1 - 0.22 * thin[..., None]) + hexc('#f3ead6')[None, None] * 0.22 * thin[..., None]
        # fine scraped nap
        nap = np.asarray(Image.fromarray(r.random((h // 2 + 1, w // 9 + 1)).astype(np.float32)).resize((w, h), Image.BICUBIC))
        col *= (1 + 0.016 * (nap - 0.5) + 0.010 * (self.t_fine[sl] - 0.5))[..., None]
        # hair-side follicles: tiny clusters of dark dots
        fol = Image.new('L', (w * 2, h * 2), 0)
        d = ImageDraw.Draw(fol)
        for _ in range(int(w * h / 900)):
            x, y = r.uniform(0, w * 2), r.uniform(0, h * 2)
            for k in range(r.integers(1, 4)):
                xx, yy, rr = x + r.normal(0, 2.4), y + r.normal(0, 2.4), r.uniform(0.6, 1.3)
                d.ellipse((xx - rr, yy - rr, xx + rr, yy + rr), fill=int(r.uniform(60, 170)))
        fol = np.asarray(fol.resize((w, h), Image.BOX), np.float32) / 255
        col *= (1 - 0.32 * fol[..., None] * (1 - hexc('#8a7058'))[None, None])
        # faint veins
        vim = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(vim)
        for _ in range(3):
            x, y = r.uniform(0, w), r.uniform(0, h)
            a = r.uniform(0, np.pi)
            n = 60
            wob = fbm1d(n, 14, 3, self._seed())
            pts = []
            for k in range(n):
                a += 0.05 * wob[k]
                x += 6 * np.cos(a); y += 6 * np.sin(a)
                pts.append((x, y))
            d.line(pts, fill=255, width=int(r.integers(2, 4)), joint='curve')
        vein = blur(np.asarray(vim, np.float32) / 255, 2.0)
        col *= (1 - 0.05 * vein[..., None] * (1 - hexc('#9a6a5a'))[None, None] * 3)
        # darker, grubbier toward the edges of the leaf
        ed = blur(m[sl], 14)
        col *= (1 - 0.08 * (1 - smoothstep(0.55, 0.98, ed)))[..., None]
        self.img[sl] = self.img[sl] * (1 - mm) + col * mm
        # cockle: the skin is never flat, more so toward the free edges
        ck = noise2d(h, w, 240, 2, self._seed()) - 0.5
        self.hmap[sl] += m[sl] * (6.0 * ck + 6.0 * (1 - smoothstep(0.5, 0.95, blur(m[sl], 40))) * ck)

    def flaw(self, cx, cy, rx, ry, rot=0.0):
        """a natural hole in the skin (the scribe wrote round it): you see the next leaf through it, with a shadow"""
        hole = self.ellipse(cx, cy, rx, ry, rot)
        lip = self.ellipse(cx, cy, rx + 2.2, ry + 2.2, rot) - hole
        under = hexc(VELLUM) * 0.78
        sh = np.clip(hole - np.roll(np.roll(hole, 3, 0), 2, 1), 0, 1)
        col = under[None, None] * (1 - 0.35 * sh[..., None])
        self.img = self.img * (1 - hole[..., None]) + col * hole[..., None]
        self.img *= (1 - 0.10 * lip)[..., None]
        self.hmap += lip * 1.5

    # ------------------------------------------------------------ ruling
    def rule(self, x0, x1, ys, prick_x=None, colour=RULE, opacity=0.3, top=None, bottom=None):
        """plummet ruling: a line at every y (x-height line of each text line), bounding verticals at x0/x1 running
        the height of the leaf, prickings at prick_x"""
        r = self.rng
        lines = []
        for y in ys:
            wob = r.normal(0, 0.25)
            lines.append(([(x0 - 4, y + wob), (x1 + 4, y + wob + r.normal(0, 0.4))], 0.7))
        bx0, by0, bx1, by1 = self.book
        t = top if top is not None else by0 + 6
        b = bottom if bottom is not None else by1 - 6
        for x in (x0, x1):
            lines.append(([(x + r.normal(0, 0.3), t), (x + r.normal(0, 0.6), b)], 0.7))
        res = self._raster(lines=lines)
        m, mx, my = res
        sl = (slice(my, my + m.shape[0]), slice(mx, mx + m.shape[1]))
        a = m * opacity * (0.7 + 0.6 * self.t_mid[sl])
        self.img[sl] = self.img[sl] * (1 - a[..., None]) + _c(colour) * a[..., None]
        if prick_x is not None:
            pm = self.mask(dots=[(prick_x + r.normal(0, 0.6), y + r.normal(0, 0.5), 1.1) for y in ys])
            self.img *= (1 - 0.65 * pm)[..., None]
            self.hmap -= pm * 1.2

    # ------------------------------------------------------------ the scribe's pen
    def _glyph_polys(self, ch, x, y, xh, rot=0.0, nib=0.2, jitter=1.0):
        g = GLYPHS.get(ch, GLYPHS[' '])
        strokes, adv = g
        r = self.rng
        dx, dy = r.normal(0, 0.012 * xh) * jitter, r.normal(0, 0.012 * xh) * jitter
        sc = 1 + r.normal(0, 0.012) * jitter
        th = np.radians(rot + r.normal(0, 0.6) * jitter)
        c, s = np.cos(th), np.sin(th)
        a = np.radians(self.nib_angle + rot + r.normal(0, 1.5) * jitter)
        nv = 0.5 * nib * xh * sc * np.array([np.cos(a), -np.sin(a)], np.float32)
        quads, hairs = [], []
        for st in strokes:
            u = st[:, 0] * xh * sc
            v = (st[:, 1] - 1.0) * xh * sc
            pts = np.stack([x + dx + u * c + v * s, y + dy - u * s + v * c], 1)
            for i in range(len(pts) - 1):
                p, q = pts[i], pts[i + 1]
                quads.append(np.array([p - nv, p + nv, q + nv, q - nv]))
            hairs.append(pts)
        return quads, hairs, adv * xh * sc

    def _pen_glyphs(self, items, kind='iron', nib=0.2, opacity=0.95, jitter=1.0):
        """items: (ch, x, y, xh, rot, load). Each glyph is its pen strokes; load (0..1) is how full the quill was."""
        if not items: return
        G = []
        for ch, x, y, xh, rot, load in items:
            q, h, _ = self._glyph_polys(ch, x, y, xh, rot, nib, jitter)
            if q: G.append((q, h, max(0.55, 0.045 * xh), load))
        if not G: return
        allp = np.concatenate([np.concatenate(g[0]) for g in G])
        pad = 4
        x0 = max(int(allp[:, 0].min()) - pad, 0); y0 = max(int(allp[:, 1].min()) - pad, 0)
        x1 = min(int(allp[:, 0].max()) + pad + 1, self.W); y1 = min(int(allp[:, 1].max()) + pad + 1, self.H)
        if x1 <= x0 or y1 <= y0: return
        ss = self.ss
        cim = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        lim = Image.new('L', cim.size, 0)
        dc, dl = ImageDraw.Draw(cim), ImageDraw.Draw(lim)
        off = np.array([x0, y0], np.float32)
        for quads, hairs, hw, load in G:
            f = int(30 + 225 * np.clip(load, 0, 1))
            for q in quads:
                qq = ((q - off) * ss).ravel().tolist()
                dc.polygon(qq, fill=255); dl.polygon(qq, fill=f)
            for hl in hairs:
                qq = ((hl - off) * ss).ravel().tolist()
                ww = max(1, int(round(hw * ss)))
                dc.line(qq, fill=255, width=ww); dl.line(qq, fill=f, width=ww)
        cov = np.asarray(cim.reduce(ss), np.float32) / 255
        ld = np.asarray(lim.reduce(ss), np.float32) / 255
        self._ink(cov, ld / np.maximum(cov, 1e-3), x0, y0, kind, opacity)

    def _ink(self, cov, load, x0, y0, kind='iron', opacity=0.95):
        h, w = cov.shape
        sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        load = np.clip(load, 0, 1)
        rim = np.clip((cov - blur(cov, 0.9)) * 2.2, 0, 1)
        tex = self.t_fine[sl] - 0.5
        if kind == 'iron':
            k = np.clip(0.30 + 0.62 * load + 0.55 * rim + 0.25 * tex, 0, 1)[..., None]
            col = hexc(INK_THIN) * (1 - k) + hexc(INK) * k
            a = cov * opacity * (0.80 + 0.20 * load)
            self.inkm[sl] = np.maximum(self.inkm[sl], a)
        elif kind == 'red':
            k = np.clip(0.25 + 0.35 * load + 0.7 * rim + 0.3 * tex, 0, 1)[..., None]
            col = np.where(k < 0.5, hexc(RED_THIN) * (1 - 2 * k) + hexc(RED) * 2 * k, hexc(RED) * (2 - 2 * k) + hexc(RED_DARK) * (2 * k - 1))
            a = cov * opacity * (0.82 + 0.18 * load)
        elif kind == 'blue':
            k = np.clip(0.3 + 0.4 * load + 0.6 * rim + 0.3 * tex, 0, 1)[..., None]
            col = hexc(AZURE_LIGHT) * (1 - k) + hexc(AZURE_DARK) * k
            a = cov * opacity
        elif kind == 'white':
            col = np.broadcast_to(hexc(WHITE), cov.shape + (3,)) * (1 - 0.04 * rim[..., None])
            a = cov * opacity * (0.75 + 0.25 * load)
        elif kind == 'diagram':                              # thin compass ink: browner, a little faded
            k = np.clip(0.35 + 0.3 * load + 0.5 * rim + 0.3 * tex, 0, 1)[..., None]
            col = hexc('#7a5536') * (1 - k) + hexc('#2e1f14') * k
            a = cov * opacity
            self.inkm[sl] = np.maximum(self.inkm[sl], a * 0.6)
        else:
            col = np.broadcast_to(_c(kind), cov.shape + (3,))
            a = cov * opacity
        a3 = a[..., None]
        self.img[sl] = self.img[sl] * (1 - a3) + col * a3
        self.gold[sl] *= 1 - a
        self.shell[sl] *= 1 - a
        self.hmap[sl] += a * 0.3

    def pen(self, paths, width=1.0, kind='iron', opacity=0.95, closed=False, dash=None):
        """round-nib pen lines (diagrams, hairline tendrils, outlines). paths: list of (N, 2); dash=(on, off) px"""
        lines = []
        for p in paths:
            p = np.asarray(p, np.float32)
            if closed: p = np.vstack([p, p[:1]])
            if dash:
                seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
                s = np.concatenate([[0], np.cumsum(seg)])
                on, off = dash
                t = 0.0
                while t < s[-1]:
                    tt = np.linspace(t, min(t + on, s[-1]), 4)
                    lines.append((np.stack([np.interp(tt, s, p[:, 0]), np.interp(tt, s, p[:, 1])], 1), width))
                    t += on + off
            else:
                lines.append((p, width))
        r = self._raster(lines=lines)
        if r is None: return
        m, x0, y0 = r
        self._ink(m, np.ones_like(m), x0, y0, kind, opacity)

    def outline(self, mask, width=1.4, kind='iron', opacity=0.92):
        """pen outline round a gilded or painted shape (centred on its edge)"""
        mb = blur(mask, max(0.45, width * 0.42))
        band = smoothstep(0.02, 0.32, mb) * smoothstep(0.98, 0.68, mb)
        sl = _bbox(band, 1)
        if sl is None: return
        b = np.clip(band[sl] * 1.25, 0, 1)
        y0, x0 = sl[0].start, sl[1].start
        self._ink(b, np.ones_like(b), x0, y0, kind, opacity)

    # ------------------------------------------------------------ writing
    def write(self, s, x, y, xh, kind='iron', rot=0.0, load=None, nib=0.2, spacing=0.0):
        """write a line of textura starting at baseline point (x, y). Returns the end x."""
        items = []
        cx = x
        c, sn = np.cos(np.radians(rot)), np.sin(np.radians(rot))
        lv = 1.0 if load is None else load
        for word in s.split(' '):
            for ch in scribal(word):
                items.append((ch, x + (cx - x) * c, y - (cx - x) * sn, xh, rot, lv))
                cx += (GLYPHS.get(ch, GLYPHS[' '])[1] + spacing) * xh
                if load is None: lv = max(0.4, lv - 0.025)
            cx += GLYPHS[' '][1] * xh
        self._pen_glyphs(items, kind, nib)
        return cx - GLYPHS[' '][1] * xh

    def text_width(self, s, xh, spacing=0.0):
        words = [scribal(w) for w in s.split(' ')]
        return sum(word_width(w, xh) + spacing * xh * len(w) for w in words) + GLYPHS[' '][1] * xh * (len(words) - 1)

    def arc_text(self, s, cx, cy, r, at=90.0, xh=10, kind='iron', nib=0.2, inside=False):
        """text round a circle, centred at angle `at` (degrees, counter-clockwise from 3 o'clock); baseline on radius r.
        Reads clockwise along the top (inside=False)."""
        chars = scribal(s.replace(' ', ' '))
        widths = [GLYPHS.get(ch, GLYPHS[' '])[1] * xh for ch in chars]
        L = sum(widths)
        sgn = 1 if not inside else -1
        pos = -L / 2
        items = []
        for ch, w in zip(chars, widths):
            th = np.radians(at) - sgn * pos / r
            tc = np.radians(at) - sgn * (pos + w / 2) / r
            rot = np.degrees(tc) - 90 if not inside else np.degrees(tc) + 90
            px, py = cx + r * np.cos(th), cy - r * np.sin(th)
            items.append((ch, px, py, xh, rot, 1.0))
            pos += w
        self._pen_glyphs(items, kind, nib, jitter=0.6)

    def column(self, text, x0, x1, y, xh, leading, indent=(), align='justify', filler=True):
        """lay text out in a column, first baseline at y. indent: [(n_lines, left_x)] to wrap round an initial.
        Markup: *red words* (reserved for the rubricator), ^word = capital touched in red, ¶ = paragraph mark,
        | = paragraph end. Returns a Block for scribe() and rubricate()."""
        toks = []
        red = False
        for t in text.split():
            if t == '|':
                toks.append({'kind': 'break'}); continue
            if t == '¶':
                toks.append({'kind': 'para', 'w': 0.75 * xh}); continue
            touch = t.startswith('^')
            t = t.lstrip('^')
            start = t.startswith('*'); end = t.endswith('*')
            t = t.strip('*')
            if start: red = True
            w = scribal(t)
            toks.append({'kind': 'word', 'text': w, 'w': word_width(w, xh), 'red': red, 'touch': touch})
            if end: red = False
        sp = GLYPHS[' '][1] * xh
        lefts = []
        for n, lx in indent: lefts += [lx] * n
        words, fillers, lines = [], [], []
        i, li = 0, 0
        while i < len(toks):
            lx = lefts[li] if li < len(lefts) else x0
            avail = x1 - lx
            line, wsum = [], 0.0
            while i < len(toks):
                t = toks[i]
                if t['kind'] == 'break':
                    i += 1; break
                need = t['w'] + (sp if line else 0)
                if line and wsum + need > avail:
                    cut = _hyphenate(t, avail - wsum - sp, xh) if t['kind'] == 'word' else None
                    if cut:                        # the scribe splits the word with a hairline hyphen
                        a, b = cut
                        line.append(a); wsum += sp + a['w']
                        toks[i] = b
                    break
                line.append(t); wsum += need; i += 1
            last = i >= len(toks) or toks[i - 1]['kind'] == 'break'
            by = y + li * leading
            gaps = len(line) - 1
            extra = avail - wsum
            stretch = extra / gaps if (align == 'justify' and gaps and not last and extra < 2.2 * sp * gaps) else 0.0
            cx = lx
            for t in line:
                words.append(dict(t, x=cx, y=by, xh=xh))
                cx += t['w'] + sp + stretch
            end = cx - sp - stretch
            if filler and last and x1 - end > 2.0 * xh:
                fillers.append((end + 0.5 * xh, x1, by, xh))
            lines.append(by)
            li += 1
        return Block(words, fillers, lines, xh)

    def scribe(self, blk, dip=(16, 30)):
        """the scribe writes every black word, re-dipping the quill every dip glyphs (ink load 1 -> ~0.4)"""
        r = self.rng
        items, left, load = [], 0, 1.0
        for w in blk.words:
            if w['kind'] != 'word' or w['red']: continue
            cx = w['x']
            for ch in w['text']:
                if left <= 0:
                    left = int(r.integers(*dip)); n0 = left; load = 1.0
                items.append((ch, cx, w['y'], w['xh'], 0.0, 0.42 + 0.58 * left / n0))
                cx += GLYPHS.get(ch, GLYPHS[' '])[1] * w['xh']
                left -= 1
        self._pen_glyphs(items, 'iron', 0.2)

    def rubricate(self, blk, blue_first=False):
        """red words, capitals touched in red, alternating red / blue paragraph marks, line fillers"""
        items = []
        for w in blk.words:
            if w['kind'] == 'word' and w['red']:
                cx = w['x']
                for ch in w['text']:
                    items.append((ch, cx, w['y'], w['xh'], 0.0, 0.9))
                    cx += GLYPHS.get(ch, GLYPHS[' '])[1] * w['xh']
        self._pen_glyphs(items, 'red', 0.2)
        # capitals touched in red: a translucent stroke of red wash down the first letter
        polys = []
        for w in blk.words:
            if w['kind'] == 'word' and w['touch']:
                x, y, xh = w['x'], w['y'], w['xh']
                polys.append([(x - 0.08 * xh, y - 1.05 * xh), (x + 0.10 * xh, y - 1.05 * xh), (x + 0.12 * xh, y - 0.02 * xh), (x - 0.06 * xh, y - 0.02 * xh)])
        if polys:
            r = self._raster(polys)
            m, x0, y0 = r
            self._ink(blur(m, 0.5), np.ones_like(m), x0, y0, 'red', 0.62)
        # paragraph marks
        k = 1 if blue_first else 0
        for w in blk.words:
            if w['kind'] == 'para':
                self.paraph(w['x'] + 0.05 * w['xh'], w['y'], w['xh'], 'blue' if k % 2 else 'red')
                k += 1
        for f in blk.fillers:
            self.line_filler(*f)

    def paraph(self, x, y, xh, kind='red'):
        """a paragraph mark: a solid bowl and a double stem, written with a wide pen"""
        u = lambda pts: [(x + a * xh, y + (b - 1) * xh) for a, b in pts]
        bowl = self.mask([u([(0.42, -0.02), (0.18, -0.04), (0.02, 0.08), (-0.02, 0.32), (0.06, 0.52), (0.24, 0.62), (0.42, 0.60)])])
        stems = self.mask(lines=[(u([(0.40, -0.04), (0.40, 1.15)]), 0.13 * xh), (u([(0.58, -0.04), (0.58, 1.15)]), 0.09 * xh),
                                 (u([(0.30, -0.05), (0.66, -0.05)]), 0.09 * xh)])
        m = np.maximum(bowl, stems)
        sl = _bbox(m, 2)
        self._ink(m[sl], np.ones_like(m[sl]), sl[1].start, sl[0].start, kind, 0.96)

    def line_filler(self, x0, x1, y, xh):
        """the rubricator closes a short last line: a red zigzag with blue dots in the valleys"""
        n = max(2, int((x1 - x0) / (0.5 * xh)))
        xs = np.linspace(x0, x1, n * 2 + 1)
        ys = y - 0.5 * xh + 0.22 * xh * np.where(np.arange(len(xs)) % 2, -1, 1)
        self.pen([np.stack([xs, ys], 1)], max(0.9, 0.07 * xh), 'red')
        dots = [(xs[i], y - 0.5 * xh + 0.42 * xh * (1 if i % 4 == 1 else -1), 0.11 * xh) for i in range(1, len(xs), 2)]
        m = self.mask(dots=dots)
        sl = _bbox(m, 2)
        self._ink(m[sl], np.ones_like(m[sl]), sl[1].start, sl[0].start, 'blue', 0.95)

    # ------------------------------------------------------------ gold
    def gild(self, mask, cushion=4.0):
        """lay burnished gold leaf on a raised gesso cushion (over red bole) inside mask"""
        sl = _bbox(mask, 6)
        if sl is None: return
        m = mask[sl]
        d = blur(m, 2.2)
        dome = np.clip((d - 0.2) / 0.8, 0, 1) ** 0.6
        self.gold[sl] = np.maximum(self.gold[sl], m)
        h = (cushion + 4.5 * (self.t_wave[sl] - 0.5)) * dome * m      # the burnisher never leaves it quite flat
        self.gesso[sl] = np.maximum(self.gesso[sl], h)
        self.img[sl] = self.img[sl] * (1 - m[..., None]) + hexc(BOLE) * m[..., None]

    def punch(self, pts, r=1.4, depth=1.4):
        """tooling: a punch pressed into the burnished gold leaves a small dimple that glitters"""
        m = blur(self.mask(dots=[(x, y, r) for x, y in pts]), 0.6)
        self.gesso -= depth * m * self.gold

    def shell_gold(self, mask, body=0.5):
        """shell gold: powdered gold in gum, painted on -- matte and grainy, no cushion"""
        sl = _bbox(mask, 2)
        if sl is None: return
        m = mask[sl]
        self.shell[sl] = np.maximum(self.shell[sl], m)
        self.img[sl] = self.img[sl] * (1 - m[..., None]) + hexc('#8c6a2c') * m[..., None]
        self.hmap[sl] += m * body

    # ------------------------------------------------------------ paint
    def paint(self, mask, colour, mix=None, texture=1.0, pool=1.0, opacity=0.97, body=0.7, granular=0.0):
        """tempera inside mask. mix=(colour2, field) blends toward colour2 by a 0..1 field (full canvas).
        granular: coarse pigment specks (azurite ~1)."""
        sl = _bbox(mask, 3)
        if sl is None: return
        m = mask[sl]
        col = np.broadcast_to(_c(colour), m.shape + (3,)).astype(np.float32)
        if mix is not None:
            c2, f = mix
            f = np.clip(f[sl], 0, 1)[..., None]
            col = col * (1 - f) + _c(c2) * f
        tex = 1 + texture * (0.07 * (self.t_mid[sl] - 0.5) + 0.06 * (self.t_fine[sl] - 0.5))
        if granular:
            g = self.grain[sl]
            tex = tex * (1 - granular * 0.28 * (g > 0.93)) * (1 + granular * 0.16 * (g < 0.04))
        col = col * tex[..., None]
        rim = np.clip((m - blur(m, 1.8)) * 2.0, 0, 1)
        col = col * (1 - 0.22 * pool * rim)[..., None]
        a = m * opacity
        self.img[sl] = self.img[sl] * (1 - a[..., None]) + col * a[..., None]
        self.gold[sl] *= 1 - a
        self.shell[sl] *= 1 - a
        self.hmap[sl] += m * body
        if _c(colour)[2] > 0.5 and _c(colour)[0] < 0.3:
            self.azm[sl] = np.maximum(self.azm[sl], m)

    def wash(self, mask, colour, opacity=0.25):
        """a thin transparent wash (multiplies, keeps the vellum showing)"""
        sl = _bbox(mask, 2)
        if sl is None: return
        a = (mask[sl] * opacity * (0.85 + 0.3 * self.t_mid[sl]))[..., None]
        self.img[sl] = self.img[sl] * (1 - a + a * _c(colour) / max(hexc(VELLUM).max(), 1e-3))

    # ------------------------------------------------------------ ornament objects
    def initial(self, letter, x0, y0, size, body=ROSE, scene='night'):
        return Initial(self, letter, x0, y0, size, body, scene)

    def border(self, path, width=10, avoid=(), bounds=None, seed=0, every=78, reach=1.0):
        return Border(self, path, width, avoid, bounds, seed, every, reach)

    def versal(self, letter, x, y, size, colour=AZURE, flourish=RED, reach=(160, 160)):
        return Versal(self, letter, x, y, size, colour, flourish, reach)

    def astrolabe(self, cx, cy, R, **kw):
        return Astrolabe(self, cx, cy, R, **kw)

    def spheres(self, cx, cy, R, **kw):
        return Spheres(self, cx, cy, R, **kw)

    def star(self, cx, cy, r, points=8, inner=0.42, rot=0.0):
        a = np.radians(rot) + np.arange(points * 2) * np.pi / points
        rr = np.where(np.arange(points * 2) % 2, r * inner, r)
        return np.stack([cx + rr * np.sin(a), cy - rr * np.cos(a)], 1)

    # ------------------------------------------------------------ time
    def show_through(self, x0, x1, ys, xh, avoid=(), opacity=0.06):
        """the writing on the other side of the leaf, mirrored and soft, showing through the skin"""
        r = self.rng
        vocab = 'et in de per ad cum est sunt quod circa terra motus orbis caelum gradus linea medium semper autem ' \
                'superior inferior numerus tempus annus dies hora signum umbra lumen quantitas distantia'.split()
        items = []
        for y in ys:
            x = x0 + r.uniform(0, 2) * xh
            while x < x1 - 2 * xh:
                w = scribal(vocab[r.integers(len(vocab))])
                ww = word_width(w, xh)
                if x + ww > x1: break
                if not any(a[0] - 4 < x < a[2] + 4 and a[1] - 4 < y < a[3] + 4 for a in avoid):
                    cx = x
                    for ch in w:
                        items.append((ch, x0 + x1 - cx, y, xh, 0.0, 1.0))      # mirrored position (letter flipped below)
                        cx += GLYPHS[ch][1] * xh
                x += ww + GLYPHS[' '][1] * xh * r.uniform(1, 1.6)
        polys = []
        for ch, x, y, xh_, rot, ld in items:
            q, h, _ = self._glyph_polys(ch, x, y, xh_, 0.0, 0.2, 1.0)
            for quad in q:
                quad = quad.copy(); quad[:, 0] = 2 * x - quad[:, 0]          # flip the letter itself
                polys.append(quad)
        res = self._raster(polys)
        if res is None: return
        m, mx, my = res
        m = blur(m, 1.6)
        sl = (slice(my, my + m.shape[0]), slice(mx, mx + m.shape[1]))
        a = (m * opacity * self.pagem[sl])[..., None]
        self.img[sl] = self.img[sl] * (1 - a) + hexc('#5a4632') * a

    def age(self, foxing=40, soil=1.0, flakes=1.0, halo=1.0):
        """six centuries: iron-gall halo, foxing, thumb soil, gold flaking to the bole, chipped azurite"""
        r = self.rng
        H, W = self.H, self.W
        # iron-gall halo (the ink browns the skin around it)
        hl = np.clip(blur(self.inkm, 2.4) - self.inkm, 0, 1) * halo
        self.img *= (1 - 0.10 * hl[..., None] * (1 - hexc('#8a6238'))[None, None] * 2.2)
        # foxing
        bx0, by0, bx1, by1 = self.book
        dots = [(r.uniform(bx0, bx1), r.uniform(by0, by1), r.uniform(1.0, 4.5)) for _ in range(foxing)]
        fx = blur(self.mask(dots=dots), 2.0) * self.pagem
        self.img *= (1 - 0.18 * fx[..., None] * (1 - hexc('#a0703e'))[None, None] * 1.6)
        # thumb soil on the lower outer corners (where the leaves are turned)
        for cx in (bx0, bx1):
            d = np.hypot((self.XX - cx) / 1.1, self.YY - by1)
            s = np.exp(-(d / 150) ** 2) * (0.6 + 0.6 * self.t_mid) * soil * self.pagem
            self.img *= (1 - 0.16 * s[..., None] * (1 - hexc('#8f7a5c'))[None, None] * 2.4)
        # gold flakes: small irregular losses, mostly toward the cushion edges, show the red bole
        if flakes:
            n = noise2d(H, W, 5, 2, self._seed())
            edge = 1 - smoothstep(0.5, 0.95, blur(self.gold, 2.5))
            lost = (n > 0.82 - 0.10 * edge * flakes) & (self.gold > 0.5) & (self.t_mid > 0.55)
            lost = blur(lost.astype(np.float32), 0.6) * self.gold
            self.gold *= 1 - lost
            deep = lost * (self.grain > 0.7)
            self.img = self.img * (1 - 0.5 * deep[..., None]) + hexc('#e8dcc4') * 0.5 * deep[..., None]
            # azurite chips (it is the first pigment to flake)
            n2 = noise2d(H, W, 4, 2, self._seed())
            chip = blur(((n2 > 0.86) & (self.azm > 0.5) & (self.t_big > 0.45)).astype(np.float32), 0.5) * self.azm
            self.img = self.img * (1 - chip[..., None]) + hexc('#d9c9a6') * chip[..., None]
            self.hmap -= chip * 0.6

    # ------------------------------------------------------------ light and output
    def _streaks(self):
        if self._streak is None:
            H, W, r = self.H, self.W, self.rng
            s = np.asarray(Image.fromarray(r.random((H // 2, W // 14)).astype(np.float32)).resize((W, H), Image.BICUBIC))
            s2 = np.asarray(Image.fromarray(r.random((H // 14, W // 2)).astype(np.float32)).resize((W, H), Image.BICUBIC))
            # gold leaf comes in squares: faint raised seams where two leaves overlap
            seam = np.zeros((H, W), np.float32)
            size = 64
            for row in range(H // size + 1):
                off = r.uniform(0, size)
                ys = slice(row * size, min((row + 1) * size, H))
                xx = (self.XX[ys] + off) % size
                seam[ys] = np.maximum(seam[ys], np.exp(-(np.minimum(xx, size - xx) / 0.9) ** 2))
            yy = self.YY % size
            seam = np.maximum(seam, np.exp(-(np.minimum(yy, size - yy) / 0.9) ** 2))
            self._streak = (0.04 * (s - 0.5) + 0.03 * (s2 - 0.5) + 0.12 * seam).astype(np.float32)
        return self._streak

    def composite(self):
        H, W = self.H, self.W
        img = self.img.copy()
        L = np.array([-0.48, -0.56, 0.68], np.float32); L /= np.linalg.norm(L)
        gy, gx = np.gradient(self.hmap)
        nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
        shade = (-gx * L[0] - gy * L[1] + L[2]) * nz / L[2]
        img *= np.clip(shade, 0.72, 1.22)[..., None]
        # shell gold: matte, grainy, follows the relief a little
        sl = _bbox(self.shell, 1)
        if sl is not None:
            g = self.grain[sl]
            E = 0.50 + 0.55 * (shade[sl] - 1) + 0.10 * (self.t_fine[sl] - 0.5) + 0.06 * (self.t_mid[sl] - 0.5)
            E = E + 0.35 * (g > 0.985)
            col = _gold_ramp(E * 0.96) * np.array([1.0, 0.97, 0.9], np.float32)
            a = self.shell[sl][..., None]
            img[sl] = img[sl] * (1 - a) + col * a
        # burnished gold: a mirror of the room
        sl = _bbox(self.gold, 2)
        if sl is not None:
            h = self.gesso[sl] + self._streaks()[sl] * (self.gold[sl] > 0)
            h = blur(h, 0.6)
            hy, hx = np.gradient(h)
            n = np.stack([-hx, -hy, np.ones_like(hx)], -1)
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            cam = np.array([W * 0.5, H * 0.45, 6000.0], np.float32)
            v = np.stack([cam[0] - self.XX[sl], cam[1] - self.YY[sl], np.full(hx.shape, cam[2], np.float32)], -1)
            v /= np.linalg.norm(v, axis=-1, keepdims=True)
            nv = (n * v).sum(-1, keepdims=True)
            rf = 2 * nv * n - v
            Lw = np.array([-0.40, -0.45, 0.80], np.float32); Lw /= np.linalg.norm(Lw)
            dd = (rf * Lw).sum(-1)
            E = 0.06 + 0.9 * smoothstep(0.55, 1.0, dd) ** 1.4 + 0.3 * smoothstep(0.975, 0.997, dd)
            E = E + 0.04 * (self.t_mid[sl] - 0.5)
            col = _gold_ramp(E)
            a = self.gold[sl][..., None]
            img[sl] = img[sl] * (1 - a) + col * a
        # the leaves bow down into the gutter: their top and bottom edges dip inward near the spine
        if self.dip:
            gxp = self.gx
            x0 = max(int(gxp - 110), 0); x1 = min(int(gxp + 110), W)
            bx0, by0, bx1, by1 = self.book
            cy = (by0 + by1) / 2
            hh = (by1 - by0) / 2
            xs = np.arange(x0, x1, dtype=np.float32)
            s = self.dip * np.exp(-np.abs(xs - gxp) / 26)
            yy = np.arange(H, dtype=np.float32)[:, None]
            src = cy + (yy - cy) * (1 + s[None, :] / hh)
            src = np.clip(src, 0, H - 1.001)
            i0 = np.floor(src).astype(np.int32); f = (src - i0)[..., None]
            slab = img[:, x0:x1]
            cols = np.arange(x1 - x0)[None, :]
            img[:, x0:x1] = slab[i0, cols] * (1 - f) + slab[i0 + 1, cols] * f
        img *= self.light[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
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


# ====================================================================== ornaments
def _lombard(il, cx, cy, R, letter='O', squash=0.94):
    """a Lombardic capital: body mask, counter mask. The bowl swells on the left and right (thin at top and bottom),
    with small pearls jutting into the counter; Q adds a sweeping tail."""
    X, Y = il.XX - cx, (il.YY - cy) / squash
    q = (np.abs(X / R) ** 2.3 + np.abs(Y / R) ** 2.3) ** (1 / 2.3)
    outer = np.clip((1 - q) * R + 0.5, 0, 1)
    rx, ry = 0.50 * R, 0.74 * R
    qi = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2)
    counter = np.clip((1 - qi) * rx + 0.5, 0, 1)
    # pearls: small pointed bumps on the inside of the thick sides
    for sx in (-1, 1):
        pearl = il.ellipse(cx + sx * rx * 0.98, cy, 0.13 * R, 0.07 * R)
        counter = np.clip(counter - pearl, 0, 1)
    body = np.clip(outer - counter, 0, 1)
    if letter == 'Q':
        t = np.linspace(0, 1, 40)
        p0 = np.array([cx + 0.40 * R, cy + 0.80 * R]); p1 = np.array([cx + 0.95 * R, cy + 1.10 * R])
        p2 = np.array([cx + 1.18 * R, cy + 1.02 * R])
        c = ((1 - t) ** 2)[:, None] * p0 + (2 * t * (1 - t))[:, None] * p1 + (t ** 2)[:, None] * p2
        tan = np.gradient(c, axis=0); tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
        w = 0.17 * R * (1 - t) ** 0.9 + 0.8
        tail = il.mask([np.concatenate([c + nrm * w[:, None], (c - nrm * w[:, None])[::-1]])])
        body = np.maximum(body, tail * (1 - counter))
    return body, counter


class Initial:
    """a historiated initial: a Lombardic letter in tempera with white tracery on a burnished, tooled gold panel;
    the counter holds a small night scene (sky, crescent moon, gold stars, a hill with an observatory tower)"""

    def __init__(self, il, letter, x0, y0, size, body=ROSE, scene='night'):
        self.il, self.letter, self.size, self.body_col, self.scene = il, letter, size, body, scene
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x0 + size, y0 + size
        self.cx, self.cy, self.R = x0 + size * 0.46, y0 + size * 0.45, size * 0.385
        self.panel = il.mask([[(x0, y0), (x0 + size, y0), (x0 + size, y0 + size), (x0, y0 + size)]])
        self.body, self.counter = _lombard(il, self.cx, self.cy, self.R, letter)
        self.ground = np.clip(self.panel - self.body - self.counter, 0, 1)
        R, cx, cy = self.R, self.cx, self.cy
        # the scene inside the counter
        rx, ry = 0.50 * R, 0.74 * R
        hx = np.linspace(cx - rx * 1.2, cx + rx * 1.2, 30)
        hy = cy + ry * 0.42 - 0.20 * ry * np.exp(-((hx - cx + 0.15 * rx) / (0.55 * rx)) ** 2) + 3 * fbm1d(30, 8, 2, 3)
        self.hill = il.mask([np.concatenate([np.stack([hx, hy], 1), [(cx + rx * 1.2, cy + ry * 1.2), (cx - rx * 1.2, cy + ry * 1.2)]])]) * self.counter
        tw, th = 0.20 * rx, 0.55 * ry
        tx, ty = cx + 0.12 * rx, cy + ry * 0.24
        self.tower_pts = [(tx - tw, ty), (tx - tw, ty - th), (tx - tw * 1.25, ty - th), (tx - tw * 1.25, ty - th - 0.12 * ry),
                          (tx - tw * 0.4, ty - th - 0.12 * ry), (tx - tw * 0.4, ty - th - 0.05 * ry), (tx + tw * 0.4, ty - th - 0.05 * ry),
                          (tx + tw * 0.4, ty - th - 0.12 * ry), (tx + tw * 1.25, ty - th - 0.12 * ry), (tx + tw * 1.25, ty - th),
                          (tx + tw, ty - th), (tx + tw, ty)]
        self.tower = il.mask([self.tower_pts]) * self.counter
        self.door = il.mask([[(tx - tw * 0.35, ty), (tx - tw * 0.35, ty - th * 0.28), (tx, ty - th * 0.36),
                              (tx + tw * 0.35, ty - th * 0.28), (tx + tw * 0.35, ty)]])
        self.window = il.mask([[(tx - tw * 0.18, ty - th * 0.62), (tx - tw * 0.18, ty - th * 0.78), (tx, ty - th * 0.84),
                                (tx + tw * 0.18, ty - th * 0.78), (tx + tw * 0.18, ty - th * 0.62)]])
        mx, my, mr = cx - 0.22 * rx, cy - 0.48 * ry, 0.30 * rx
        self.moon = np.clip(il.circle(mx, my, mr) - il.circle(mx + 0.42 * mr, my - 0.20 * mr, mr * 0.86), 0, 1)
        self.stars = [(cx + 0.38 * rx, cy - 0.55 * ry, 4.2), (cx + 0.05 * rx, cy - 0.20 * ry, 3.2), (cx - 0.55 * rx, cy - 0.05 * ry, 3.0),
                      (cx + 0.55 * rx, cy - 0.12 * ry, 2.6), (cx + 0.22 * rx, cy - 0.80 * ry, 2.6), (cx - 0.30 * rx, cy + 0.10 * ry, 2.2),
                      (cx + 0.62 * rx, cy - 0.36 * ry, 2.0), (cx - 0.05 * rx, cy - 0.66 * ry, 2.0)]

    def gild(self):
        il = self.il
        il.gild(self.ground, cushion=5.0)
        sm = il.mask([il.star(x, y, r * 1.5, 6, 0.45) for x, y, r in self.stars]) * self.counter
        il.gild(sm, cushion=1.5)
        # tooling: a row of punched dots inside the panel edge and rosettes in the open gold
        x0, y0, x1, y1, m = self.x0, self.y0, self.x1, self.y1, 9
        pts = []
        for t in np.arange(0, 1, 1 / 46):
            pts += [(x0 + m + (x1 - x0 - 2 * m) * t, y0 + m), (x1 - m, y0 + m + (y1 - y0 - 2 * m) * t),
                    (x1 - m - (x1 - x0 - 2 * m) * t, y1 - m), (x0 + m, y1 - m - (y1 - y0 - 2 * m) * t)]
        pts = [p for p in pts if self.ground[int(p[1]), int(p[0])] > 0.9]
        ros = []
        for gx in np.arange(x0 + 26, x1 - 10, 30):
            for gy in np.arange(y0 + 26, y1 - 10, 30):
                if all(self.ground[int(gy + dy), int(gx + dx)] > 0.9 for dx in (-8, 0, 8) for dy in (-8, 0, 8)):
                    ros += [(gx + 4 * np.cos(a), gy + 4 * np.sin(a)) for a in np.arange(6) * np.pi / 3] + [(gx, gy)]
        il.punch(pts, 1.3, 1.6)
        il.punch(ros, 1.0, 1.2)

    def paint(self):
        il = self.il
        R, cx, cy = self.R, self.cx, self.cy
        sky = smoothstep(cy - 0.8 * R, cy + 0.5 * R, il.YY)
        il.paint(np.clip(self.counter - self.hill - self.tower, 0, 1), '#1c2f6c', mix=(AZURE, sky), granular=1.0)
        il.paint(self.hill, GREEN, mix=(GREEN_DARK, smoothstep(cy + 0.25 * R, cy + 0.8 * R, il.YY)))
        il.paint(self.tower, '#d8c7a6', mix=('#a8916c', smoothstep(cx - 0.05 * R, cx + 0.1 * R, il.XX)))
        il.paint(self.door * self.tower, '#3a2a1e')
        il.paint(self.window * self.tower, '#f0c860')
        il.paint(self.moon, SILVER, mix=('#9a988f', smoothstep(cx - 0.35 * R, cx - 0.05 * R, il.XX)))
        # letter body: rose, darker toward the counter and on the lower right
        inner = blur(self.counter, R * 0.12)
        f = np.clip(1.6 * inner + 0.35 * smoothstep(-R, R, (il.XX - cx) + (il.YY - cy)), 0, 1)
        il.paint(self.body, self.body_col, mix=(ROSE_DARK, f))
        d = np.hypot(il.XX - cx, (il.YY - cy) / 0.94)
        lift = smoothstep(0.80 * R, 0.97 * R, d) * smoothstep(0.2 * R, -0.6 * R, (il.XX - cx) + (il.YY - cy))
        il.paint(self.body * lift, '#efc3c3', opacity=0.55, body=0.1)

    def pen(self):
        il = self.il
        R, cx, cy = self.R, self.cx, self.cy
        # white-lead tracery on the letter body: a line down the thick sides, dot triplets, short highlights
        rm = 0.75 * R
        paths = []
        for a0, a1 in ((110, 250), (-62, 62)):
            a = np.radians(np.linspace(a0, a1, 60))
            rr = np.where(np.cos(a) < 0, 0.765, 0.77) * R
            paths.append(np.stack([cx + rr * np.cos(a), cy - rr * np.sin(a) * 0.94], 1))
        il.pen(paths, 1.1, 'white', 0.9)
        dots = []
        for a in np.radians(np.arange(120, 245, 21)):
            px, py = cx + 0.885 * R * np.cos(a), cy - 0.885 * R * np.sin(a) * 0.94
            dots += [(px, py, 1.3), (px + 2.6 * np.cos(a + 1.57), py - 2.6 * np.sin(a + 1.57), 1.0),
                     (px - 2.6 * np.cos(a + 1.57), py + 2.6 * np.sin(a + 1.57), 1.0)]
        for a in np.radians(np.arange(-50, 55, 21)):
            dots.append((cx + 0.885 * R * np.cos(a), cy - 0.885 * R * np.sin(a) * 0.94, 1.2))
        m = il.mask(dots=dots)
        sl = _bbox(m, 2)
        il._ink(m[sl], np.ones_like(m[sl]), sl[1].start, sl[0].start, 'white', 0.92)
        # moon glow line and tower masonry
        il.outline(self.moon, 1.0)
        tx = [p[0] for p in self.tower_pts]; ty = [p[1] for p in self.tower_pts]
        courses = [[(min(tx) + 2, y), (max(tx) - 2, y)] for y in np.arange(max(ty) - 6, min(ty) + 8, -6.5)]
        il.pen(courses, 0.6, 'diagram', 0.5)
        il.outline(self.tower, 1.1)
        il.outline(self.door * self.tower, 0.8)
        il.outline(self.hill, 1.0)
        il.outline(il.mask([il.star(x, y, r * 1.5, 6, 0.45) for x, y, r in self.stars]) * self.counter, 0.7, opacity=0.7)
        il.outline(self.body, 1.6)
        il.outline(self.panel, 2.0)


class Border:
    """a bar border (segments of burnished gold, azure and rose with white tracery) along `path`, sprouting
    hairline ivy sprays: tendrils grown recursively, with gold ivy leaves, flowers, gold bezants and curls"""

    def __init__(self, il, path, width=10, avoid=(), bounds=None, seed=0, every=78, reach=1.0):
        self.il, self.width = il, width
        r = np.random.default_rng(seed)
        self.r = r
        p = np.asarray(path, np.float32)
        seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        n = int(s[-1] / 2) + 2
        ss = np.linspace(0, s[-1], n)
        self.path = np.stack([np.interp(ss, s, p[:, 0]), np.interp(ss, s, p[:, 1])], 1)
        self.length = s[-1]
        # bar segments
        cuts = [0.0]
        while cuts[-1] < s[-1]:
            cuts.append(cuts[-1] + r.uniform(38, 62))
        cuts[-1] = s[-1]
        kinds = ['gold', AZURE, 'gold', ROSE]
        self.segments = []
        for i in range(len(cuts) - 1):
            k = (ss >= cuts[i]) & (ss <= cuts[i + 1])
            self.segments.append((kinds[i % 4], self.path[k]))
        self.knots = [self.path[min(int(c / s[-1] * (n - 1)), n - 1)] for c in cuts[1:-1]]
        # sprays
        self.avoid = [tuple(a) for a in avoid]
        self.bounds = bounds or (0, 0, il.W, il.H)
        self.lines, self.leaves, self.flowers, self.balls = [], [], [], []
        tan = np.gradient(self.path, axis=0)
        tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6
        for k, t in enumerate(np.arange(r.uniform(20, 40), s[-1] - 10, every)):
            i = int(t / s[-1] * (n - 1))
            base = self.path[i]
            a_t = np.arctan2(tan[i, 1], tan[i, 0])
            for side in (-1, 1):
                if r.random() < 0.15: continue
                a = a_t + side * (np.pi / 2) + r.normal(0, 0.35)
                start = base + np.array([np.cos(a), np.sin(a)]) * (width / 2 + 1)
                self._spray(start, a, r.uniform(80, 130) * reach, 2, side)
        # finials at the ends of the bar: a long tendril continuing the bar's direction
        for end, sgn in ((0, -1), (n - 1, 1)):
            a = np.arctan2(tan[end, 1], tan[end, 0]) * 1.0 + (np.pi if sgn < 0 else 0)
            self._spray(self.path[end] + np.array([np.cos(a), np.sin(a)]) * 3, a, 120 * reach, 2, 1)

    def _bar_dist(self, p):
        return float(np.min(np.hypot(self.path[:, 0] - p[0], self.path[:, 1] - p[1])))

    def _ok(self, p, margin=7, bar=0.0):
        if bar and self._bar_dist(p) < self.width / 2 + bar: return False
        x0, y0, x1, y1 = self.bounds
        if not (x0 + margin < p[0] < x1 - margin and y0 + margin < p[1] < y1 - margin): return False
        for a in self.avoid:
            if a[0] - margin < p[0] < a[2] + margin and a[1] - margin < p[1] < a[3] + margin: return False
        return True

    def _spray(self, start, ang, length, depth, side):
        r = self.r
        step = 2.4
        n = int(length / step)
        turn = side if r.random() < 0.7 else -side
        k0 = r.uniform(0.004, 0.012) * turn
        pts = [np.asarray(start, np.float32)]
        a = ang
        wav = fbm1d(max(n, 4), 20, 2, int(r.integers(1 << 30)))
        for i in range(n):
            t = i / max(n, 1)
            a += (k0 + 0.010 * wav[i] + 0.045 * turn * t ** 4) * step
            q = pts[-1] + step * np.array([np.cos(a), np.sin(a)], np.float32)
            if not self._ok(q, bar=2.0 if i > 3 else 0.0): break
            pts.append(q)
        if len(pts) < 5: return
        pts = np.array(pts)
        self.lines.append(pts)
        m = len(pts)
        # leaves on short stalks along the stem, alternating sides
        for j in range(int(m * step / 42)):
            idx = int(m * r.uniform(0.2, 0.85))
            tg = pts[min(idx + 1, m - 1)] - pts[max(idx - 1, 0)]
            ta = np.arctan2(tg[1], tg[0])
            sd = 1 if j % 2 else -1
            la = ta + sd * r.uniform(0.7, 1.2)
            stalk_end = pts[idx] + 6 * np.array([np.cos(la), np.sin(la)])
            ls = r.uniform(11, 15)
            if self._ok(stalk_end, 9, ls + 3) and self._ok(stalk_end + ls * np.array([np.cos(la), np.sin(la)]), 9, 3) \
                    and self._ok(stalk_end + 0.6 * ls * np.array([np.cos(la + 1.1), np.sin(la + 1.1)]), 9) \
                    and self._ok(stalk_end + 0.6 * ls * np.array([np.cos(la - 1.1), np.sin(la - 1.1)]), 9):
                self.lines.append(np.array([pts[idx], stalk_end]))
                self.leaves.append((stalk_end, la, ls))
        if depth > 0:
            for j in range(int(r.integers(1, 3))):
                idx = int(m * r.uniform(0.3, 0.7))
                tg = pts[min(idx + 1, m - 1)] - pts[max(idx - 1, 0)]
                sd = 1 if (j + depth) % 2 else -1
                a2 = np.arctan2(tg[1], tg[0]) + sd * r.uniform(0.6, 1.0)
                self._spray(pts[idx], a2, length * r.uniform(0.4, 0.62), depth - 1, sd)
        # terminal
        end = pts[-1]
        tg = pts[-1] - pts[-3]
        ea = np.arctan2(tg[1], tg[0])
        u = r.random()
        ls = r.uniform(13, 17)
        if u < 0.42 and self._ok(end + (4 + ls) * np.array([np.cos(ea), np.sin(ea)]), 9, 3) and self._ok(end, 9, ls + 3):
            self.leaves.append((end + 4 * np.array([np.cos(ea), np.sin(ea)]), ea, ls))
        elif u < 0.62:
            fp, fr = end + 5 * np.array([np.cos(ea), np.sin(ea)]), r.uniform(5.5, 7.0)
            if self._ok(fp, fr + 8, fr + 4):
                self.flowers.append((fp, AZURE if r.random() < 0.55 else ROSE, fr))
        else:
            # curl and a gold bezant with three little hairs
            cur = [end]
            a, rad = ea, 5.0
            for i in range(26):
                a += 0.32 * turn
                rad *= 0.94
                cur.append(cur[-1] + rad * 0.32 * np.array([np.cos(a), np.sin(a)]))
            self.lines.append(np.array(cur))
            bp = pts[int(m * 0.6)] + 9 * np.array([np.cos(ea - turn * 1.3), np.sin(ea - turn * 1.3)])
            if self._ok(bp, 8, 8): self.balls.append((bp, r.uniform(3.4, 4.4)))

    @staticmethod
    def leaf_pts(p, a, s):
        u = np.array([(0.0, 0.0), (0.0, -0.18), (0.08, -0.42), (0.22, -0.66), (0.30, -0.40), (0.42, -0.22), (0.70, -0.20),
                      (1.12, 0.0), (0.70, 0.20), (0.42, 0.22), (0.30, 0.40), (0.22, 0.66), (0.08, 0.42), (0.0, 0.18)],
                     np.float32) * s
        c, sn = np.cos(a), np.sin(a)
        return np.stack([p[0] + u[:, 0] * c - u[:, 1] * sn, p[1] + u[:, 0] * sn + u[:, 1] * c], 1)

    def _seg_mask(self, which):
        lines = [(pts, self.width) for k, pts in self.segments if (k == which) and len(pts) > 1]
        return self.il.mask(lines=lines) if lines else None

    def gild(self):
        il = self.il
        m = self._seg_mask('gold')
        if m is not None: il.gild(m, cushion=3.5)
        lm = il.mask([self.leaf_pts(p, a, s) for p, a, s in self.leaves])
        il.gild(lm, cushion=2.2)
        il.gild(il.mask(dots=[(p[0], p[1], rr) for p, rr in self.balls]), cushion=2.0)

    def paint(self):
        il = self.il
        for col, dark in ((AZURE, AZURE_DARK), (ROSE, ROSE_DARK)):
            m = self._seg_mask(col)
            if m is None: continue
            il.paint(m, col, mix=(dark, blur(m, 2) * 0 + smoothstep(0.0, 1.0, il.t_mid)), granular=1.0 if col == AZURE else 0.0)
        # flowers: five petals round a centre
        for col in (AZURE, ROSE):
            dots = []
            for p, c, rr in self.flowers:
                if c != col: continue
                for k in range(5):
                    a = k * 2 * np.pi / 5 + 0.3
                    dots.append((p[0] + rr * 0.75 * np.cos(a), p[1] + rr * 0.75 * np.sin(a), rr * 0.55))
            if dots:
                il.paint(il.mask(dots=dots), col, granular=1.0 if col == AZURE else 0)

    def pen(self):
        il = self.il
        # white tracery on the coloured bar segments: a wave with dots
        waves = []
        for k, pts in self.segments:
            if k == 'gold' or len(pts) < 6: continue
            tg = np.gradient(pts, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
            nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
            s = np.arange(len(pts)) * 2.0
            waves.append(pts[2:-2] + nrm[2:-2] * (self.width * 0.22) * np.sin(s[2:-2] / 5.5)[:, None])
        il.pen(waves, 0.8, 'white', 0.9)
        bar = il.mask(lines=[(self.path, self.width)])
        il.outline(bar, 1.3)
        # bands across the bar where segments meet
        tan = np.gradient(self.path, axis=0); tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6
        bands = []
        for kp in self.knots:
            i = int(np.argmin(np.linalg.norm(self.path - kp, axis=1)))
            nrm = np.array([-tan[i, 1], tan[i, 0]])
            for o in (-1.6, 1.6):
                c = kp + tan[i] * o
                bands.append([c - nrm * self.width * 0.5, c + nrm * self.width * 0.5])
        il.pen(bands, 1.0)
        # hairline tendrils, leaves, flowers, bezants
        il.pen(self.lines, 0.85)
        lm = il.mask([self.leaf_pts(p, a, s) for p, a, s in self.leaves])
        il.outline(lm, 1.0)
        veins = [[p, p + 0.75 * s * np.array([np.cos(a), np.sin(a)])] for p, a, s in self.leaves]
        il.pen(veins, 0.6, opacity=0.8)
        fm = il.mask(dots=[(p[0], p[1], rr * 1.15) for p, c, rr in self.flowers])
        il.outline(fm, 0.8, opacity=0.8)
        cen = il.mask(dots=[(p[0], p[1], 1.4) for p, c, rr in self.flowers])
        sl = _bbox(cen, 2)
        if sl is not None:
            il._ink(cen[sl], np.ones_like(cen[sl]), sl[1].start, sl[0].start, 'white', 0.95)
        bm = il.mask(dots=[(p[0], p[1], rr) for p, rr in self.balls])
        il.outline(bm, 0.9)
        hairs = []
        for p, rr in self.balls:
            for k in range(3):
                a = self.r.uniform(0, 2 * np.pi)
                c0 = p + (rr + 1) * np.array([np.cos(a), np.sin(a)])
                hairs.append([c0, c0 + 4 * np.array([np.cos(a + 0.4), np.sin(a + 0.4)]), c0 + 7 * np.array([np.cos(a - 0.1), np.sin(a - 0.1)])])
        il.pen(hairs, 0.6, opacity=0.85)


class Versal:
    """a two-line penwork initial: a split Lombardic letter in azurite, flourished with red filigree that runs up and
    down the margin"""

    def __init__(self, il, letter, x, y, size, colour, flourish, reach):
        self.il, self.colour, self.flourish, self.reach = il, colour, flourish, reach
        self.x, self.y, self.size = x, y, size
        self.cx, self.cy, self.R = x + size * 0.5, y + size * 0.5, size * 0.5
        self.body, self.counter = _lombard(il, self.cx, self.cy, self.R, letter)
        # the split: a reserved hairline of bare vellum down the thick sides
        a = np.radians(np.linspace(-55, 55, 30))
        R = self.R
        self.split = il.mask(lines=[(np.stack([self.cx + 0.76 * R * np.cos(a), self.cy - 0.76 * R * np.sin(a) * 0.94], 1), 1.6),
                                    (np.stack([self.cx - 0.76 * R * np.cos(a), self.cy - 0.76 * R * np.sin(a) * 0.94], 1), 1.6)])

    def paint(self):
        il = self.il
        il.paint(np.clip(self.body - self.split, 0, 1), self.colour, granular=1.0)

    def pen(self):
        il, R, cx, cy = self.il, self.R, self.cx, self.cy
        r = np.random.default_rng(7)
        kind = 'red' if self.flourish == RED else 'blue'
        paths = []
        # echo lines round the bowl
        for o in (5, 9):
            a = np.linspace(0, 2 * np.pi, 160)
            paths.append(np.stack([cx + (R + o) * np.cos(a), cy + (R + o) * 0.94 * np.sin(a)], 1))
        # infill of the counter: concentric ovals and little circles
        a = np.linspace(0, 2 * np.pi, 120)
        paths.append(np.stack([cx + 0.36 * R * np.cos(a), cy + 0.58 * R * np.sin(a)], 1))
        circles = [np.stack([cx + 0.36 * R * np.cos(t) + 2.0 * np.cos(np.linspace(0, 2 * np.pi, 14)),
                             cy + 0.58 * R * np.sin(t) + 2.0 * np.sin(np.linspace(0, 2 * np.pi, 14))], 1)
                   for t in np.linspace(0, 2 * np.pi, 8, endpoint=False)]
        # tendrils up and down the margin, with feathered barbs and a curl at the end
        up, down = self.reach
        for sgn, L in ((-1, up), (1, down)):
            x0 = cx - R - 16
            ys = np.linspace(cy + sgn * R * 0.4, cy + sgn * (R + L), 80)
            xs = x0 + 2.5 * np.sin((ys - cy) / 14)
            paths.append(np.stack([xs, ys], 1))
            for j, k in enumerate(range(6, 80, 9)):
                bx, by = xs[k], ys[k]
                t = np.linspace(0, 1, 16)
                L = 12 if j % 2 else 8                               # long and short hooks, each ending in a curl
                hx = bx - L * t - 2.2 * np.sin(t * np.pi * 1.6) * t
                hy = by + sgn * (-5 * np.sin(t * np.pi * 0.8) + 3.5 * t ** 3)
                paths.append(np.stack([hx, hy], 1))
            a, rad, cur = -np.pi / 2 * sgn, 7.0, [np.array([xs[-1], ys[-1]])]
            for i in range(30):
                a += 0.3; rad *= 0.95
                cur.append(cur[-1] + rad * 0.3 * np.array([np.cos(a), np.sin(a)]))
            paths.append(np.array(cur))
        il.pen(paths, 0.8, kind, 0.9)
        il.pen(circles, 0.7, kind, 0.9)
        dots = [(cx, cy, 2.0)] + [(cx - R - 24, cy + s * (R + 8 + 14 * k), 1.6) for s in (-1, 1) for k in range(1, 3)]
        m = il.mask(dots=dots)
        sl = _bbox(m, 2)
        il._ink(m[sl], np.ones_like(m[sl]), sl[1].start, sl[0].start, kind, 0.95)


class Astrolabe:
    """an astrolabe drawn with compass and rule. The plate is a real stereographic projection from the south pole:
    tropic of Capricorn at the plate edge, equator, tropic of Cancer, almucantars (circles of equal altitude) for
    latitude `lat`, the horizon; a shell-gold rete (ecliptic ring, star pointers) turned by `rete`; the rule with sight
    vanes at `rule` degrees above the horizon, and its line of sight continued (dotted) to `star`."""

    def __init__(self, il, cx, cy, R, lat=48.0, rete=24.0, rule=40.0, star=None, seed=3):
        self.il, self.cx, self.cy, self.R = il, cx, cy, R
        self.lat, self.rete_rot, self.rule_deg, self.star_xy = lat, rete, rule, star
        self.rp = 0.84 * R                                   # plate = tropic of Capricorn
        eps = np.radians(23.44)
        self.req = self.rp / np.tan((np.pi / 2 + eps) / 2)
        self.rcan = self.req * np.tan((np.pi / 2 - eps) / 2)
        phi = np.radians(lat)
        self.alm = []
        for a in range(0, 90, 10):
            al = np.radians(a)
            yc = cy - self.req * np.cos(phi) / (np.sin(phi) + np.sin(al))
            rr = self.req * np.cos(al) / (np.sin(phi) + np.sin(al))
            self.alm.append((a, yc, rr))
        self.zenith = (cx, cy - self.req * np.cos(phi) / (np.sin(phi) + 1))
        r = np.random.default_rng(seed)
        # rete geometry
        th = np.radians(rete)
        e = (self.rp - self.rcan) / 2
        self.ecl = (cx + e * np.sin(th), cy - e * np.cos(th), (self.rp + self.rcan) / 2)
        self.pointers = []
        for rf, ang in ((0.92, 200), (0.72, 140), (0.55, 250), (0.88, 320), (0.40, 30), (0.80, 75), (0.30, 160), (0.66, 290), (0.95, 110)):
            a = np.radians(ang + rete)
            self.pointers.append((cx + rf * self.rp * np.cos(a), cy - rf * self.rp * np.sin(a), a))

    def _circle(self, cx, cy, r, n=None):
        n = n or max(48, int(r * 1.2))
        t = np.linspace(0, 2 * np.pi, n)
        return np.stack([cx + r * np.cos(t), cy + r * np.sin(t)], 1)

    def _clip(self, pts, r):
        """split a polyline into the runs that lie inside the plate"""
        ins = np.hypot(pts[:, 0] - self.cx, pts[:, 1] - self.cy) <= r
        runs, cur = [], []
        for p, k in zip(pts, ins):
            if k: cur.append(p)
            elif cur:
                if len(cur) > 1: runs.append(np.array(cur))
                cur = []
        if len(cur) > 1: runs.append(np.array(cur))
        return runs

    def _rete_mask(self):
        il, cx, cy, R, rp = self.il, self.cx, self.cy, self.R, self.rp
        ex, ey, er = self.ecl
        m = il.ring(ex, ey, er - 0.06 * R, er)                       # ecliptic ring with its zodiac band
        m = np.maximum(m, il.ring(cx, cy, rp - 0.022 * R, rp))         # outer rim of the rete
        th = np.radians(self.rete_rot)
        lines = []
        u = np.array([np.cos(th), np.sin(th)]); v = np.array([-np.sin(th), np.cos(th)])
        c = np.array([cx, cy])
        lines.append((np.array([c - u * rp, c + u * rp]), 0.017 * R))   # equinoctial bar
        lines.append((np.array([c + v * self.rcan * 0.5, c + v * rp]), 0.017 * R))
        # tracery: two little loops on the lower bar and a trefoil round the hub
        for f in (0.66, 0.84):
            p = c + v * rp * f
            t = np.linspace(0, 2 * np.pi, 40)
            lines.append((np.stack([p[0] + 0.045 * R * np.cos(t), p[1] + 0.045 * R * np.sin(t)], 1), 0.010 * R))
        m = np.maximum(m, il.mask(lines=lines))
        m = np.maximum(m, il.circle(cx, cy, 0.05 * R))
        # star pointers: flame-shaped blades from the framework to each star
        polys = []
        for px, py, a in self.pointers:
            d = np.array([px - cx, py - cy]); L = np.linalg.norm(d); d /= L + 1e-6
            nrm = np.array([-d[1], d[0]])
            base = np.array([px, py]) - d * 0.13 * R
            w = 0.024 * R
            polys.append([(px, py), base + nrm * w, base - d * 0.05 * R, base - nrm * w * 0.6])
        m = np.maximum(m, il.mask(polys))
        m = np.maximum(m, il.mask(dots=[(px, py, 0.012 * R) for px, py, a in self.pointers]))
        return np.clip(m, 0, 1) * il.circle(cx, cy, rp)

    def _throne(self):
        il, cx, cy, R = self.il, self.cx, self.cy, self.R
        top = cy - R
        t = np.linspace(0, 1, 30)
        left = np.stack([cx - 0.30 * R + 0.18 * R * t ** 1.6, top + 0.06 * R - 0.20 * R * np.sin(t * np.pi / 2)], 1)
        lobe = lambda x, y, r: self._circle(x, y, r, 30)
        th = il.mask([np.concatenate([left, [(cx, top - 0.21 * R)], (left * [-1, 1] + [2 * cx, 0])[::-1]])])
        th = np.maximum(th, il.mask([lobe(cx - 0.11 * R, top - 0.10 * R, 0.07 * R), lobe(cx + 0.11 * R, top - 0.10 * R, 0.07 * R),
                                     lobe(cx, top - 0.19 * R, 0.07 * R)]))
        holes = il.circle(cx, top - 0.19 * R, 0.025 * R)
        ring = il.ring(cx, top - 0.36 * R, 0.085 * R, 0.115 * R)
        shackle = il.ring(cx, top - 0.26 * R, 0.035 * R, 0.055 * R)
        return np.clip(th - holes, 0, 1) * (1 - il.circle(cx, cy, R * 0.99)), np.maximum(ring, shackle)

    def _rule(self):
        il, cx, cy, R = self.il, self.cx, self.cy, self.R
        a = np.radians(self.rule_deg)
        u = np.array([np.cos(a), -np.sin(a)]); v = np.array([np.sin(a), np.cos(a)])
        c = np.array([cx, cy])
        L, w = 0.97 * R, 0.022 * R
        bar = il.mask([[c - u * L + v * w * 0.3, c - u * (L - 0.1 * R) + v * w, c + u * (L - 0.1 * R) + v * w, c + u * L + v * w * 0.3,
                        c + u * L - v * w * 0.3, c + u * (L - 0.1 * R) - v * w, c - u * (L - 0.1 * R) - v * w, c - u * L - v * w * 0.3]])
        vanes = []
        holes = []
        for s in (-1, 1):
            p = c + u * s * 0.70 * R
            vanes.append([p - u * 0.018 * R + v * 0.06 * R, p + u * 0.018 * R + v * 0.06 * R, p + u * 0.018 * R - v * 0.06 * R,
                          p - u * 0.018 * R - v * 0.06 * R])
            holes.append((p[0], p[1], 0.009 * R))
        return np.maximum(bar, il.mask(vanes)), il.mask(dots=holes)

    def draw(self):
        """the draftsman's compass work in brown ink"""
        il, cx, cy, R, rp = self.il, self.cx, self.cy, self.R, self.rp
        paths = [self._circle(cx, cy, R), self._circle(cx, cy, 0.88 * R), self._circle(cx, cy, rp),
                 self._circle(cx, cy, self.req), self._circle(cx, cy, self.rcan)]
        il.pen(paths, 1.1, 'diagram', 0.9)
        thin = [[(cx - rp, cy), (cx + rp, cy)], [(cx, cy - rp), (cx, cy + rp)]]
        for a, yc, rr in self.alm:
            for run in self._clip(self._circle(cx, yc, rr, 400), rp):
                (paths if a == 0 else thin).append(run)
        # azimuths: circles through the zenith and nadir, drawn above the horizon only
        phi = np.radians(self.lat)
        yz = cy - self.req * np.cos(phi) / (1 + np.sin(phi))
        yn = cy + self.req * np.cos(phi) / (1 - np.sin(phi))
        hh, ym = (yn - yz) / 2, (yn + yz) / 2
        a0, hy, hr = self.alm[0]
        for A in range(15, 180, 15):
            dx = hh / np.tan(np.radians(A))
            circ = self._circle(cx + dx, ym, np.hypot(dx, hh), 900)
            keep = np.hypot(circ[:, 0] - cx, circ[:, 1] - hy) <= hr
            circ = np.where(keep[:, None], circ, 1e5)
            thin += self._clip(circ, rp)
        il.pen(thin, 0.75, 'diagram', 0.85)
        hor = [run for run in self._clip(self._circle(cx, self.alm[0][1], self.alm[0][2], 600), rp)]
        il.pen(hor, 1.3, 'diagram', 0.95)
        # degree ticks on the limb
        ticks = []
        for d in range(0, 360, 5):
            a = np.radians(d)
            r1 = 0.88 * R + (0.08 if d % 15 == 0 else 0.045) * R
            ticks.append([(cx + 0.88 * R * np.cos(a), cy - 0.88 * R * np.sin(a)), (cx + r1 * np.cos(a), cy - r1 * np.sin(a))])
        il.pen(ticks, 0.8, 'diagram', 0.85)
        th, ring = self._throne()
        il.outline(np.maximum(th, ring), 1.1, 'diagram')
        rete = self._rete_mask()
        il.outline(rete, 0.9, 'diagram', 0.8)

    def gild(self, star=True):
        il, cx, cy, R = self.il, self.cx, self.cy, self.R
        il.shell_gold(il.ring(cx, cy, 0.88 * R, R))
        th, ring = self._throne()
        il.shell_gold(np.maximum(th, ring))
        il.shell_gold(self._rete_mask())
        if star and self.star_xy is not None:
            sx, sy = self.star_xy
            il.gild(il.mask([il.star(sx, sy, 0.13 * R, 8, 0.34, 11)]), cushion=4.5)

    def paint(self):
        """light washes: the sky above the horizon, the earth below"""
        il, cx, cy, rp = self.il, self.cx, self.cy, self.rp
        a0, yc, rr = self.alm[0]
        above = il.circle(cx, yc, rr) * il.circle(cx, cy, rp - 1)
        il.wash(above * (1 - self._rete_mask()), '#7c9ad6', 0.45)
        il.wash(il.circle(cx, cy, rp - 1) * (1 - il.circle(cx, yc, rr)) * (1 - self._rete_mask()), '#c9a46a', 0.25)

    def pen(self, labels=(), xh=13):
        """ink over the gold: ticks, the rule with its sight vanes, the line of sight to the star, labels in red"""
        il, cx, cy, R = self.il, self.cx, self.cy, self.R
        ticks = []
        for d in range(0, 360, 5):
            a = np.radians(d)
            r1 = 0.88 * R + (0.10 if d % 15 == 0 else 0.05) * R
            ticks.append([(cx + 0.885 * R * np.cos(a), cy - 0.885 * R * np.sin(a)), (cx + r1 * np.cos(a), cy - r1 * np.sin(a))])
        il.pen(ticks, 0.8, 'iron', 0.85)
        il.outline(il.ring(cx, cy, 0.88 * R, R), 1.3)
        th, ring = self._throne()
        il.outline(np.maximum(th, ring), 1.2)
        rete = self._rete_mask()
        il.outline(rete, 1.1)
        # zodiac divisions on the ecliptic ring
        ex, ey, er = self.ecl
        zt = []
        for k in range(36):
            a = np.radians(k * 10 + self.rete_rot)
            r0 = er - (0.075 if k % 3 == 0 else 0.03) * R
            zt.append([(ex + r0 * np.cos(a), ey - r0 * np.sin(a)), (ex + er * np.cos(a), ey - er * np.sin(a))])
        il.pen(zt, 0.7, 'iron', 0.8)
        # the rule and its vanes
        bar, holes = self._rule()
        il.shell_gold(bar)
        il.outline(bar, 1.2)
        il.paint(holes, '#2a1d14', texture=0)
        il.outline(il.circle(cx, cy, 0.03 * R), 1.0)
        # line of sight and the angle of altitude
        a = np.radians(self.rule_deg)
        if self.star_xy is not None:
            sx, sy = self.star_xy
            p0 = (cx + 1.0 * R * np.cos(a), cy - 1.0 * R * np.sin(a))
            il.pen([[p0, (sx - 0.15 * R * np.cos(a), sy + 0.15 * R * np.sin(a))]], 1.1, 'red', 0.9, dash=(5, 5))
            il.outline(il.mask([il.star(sx, sy, 0.13 * R, 8, 0.34, 11)]), 1.0)
        il.pen([[(cx + 0.05 * R, cy), (cx + 1.32 * R, cy)]], 1.0, 'red', 0.85, dash=(9, 5))
        arc_r = 1.12 * R
        t = np.linspace(0, a, 30)
        il.pen([np.stack([cx + arc_r * np.cos(t), cy - arc_r * np.sin(t)], 1)], 1.2, 'red', 0.9)
        # labels with leader lines: (text, (x, y) of the label baseline start, (x, y) pointed at)
        leads = []
        for s, (lx, ly), (tx, ty) in labels:
            w = il.text_width(s, xh)
            il.write(s, lx, ly, xh, 'red', load=0.9)
            sx0 = lx + w + 4 if tx > lx + w else lx - 4
            leads.append([(sx0, ly - 0.5 * xh), (tx, ty)])
        il.pen(leads, 0.7, 'red', 0.8)


class Spheres:
    """the order of the planets: the earth (a T-O map) at the centre, the seven planetary spheres, the sphere of the
    fixed stars, a burnished gold frame; planet discs round a spiral, names written round the rings"""

    NAMES = ('luna', 'mercurius', 'uenus', 'sol', 'mars', 'iupiter', 'saturnus')
    COLS = (SILVER, '#8a93a0', '#e8e4c8', 'gold', '#c8452a', '#c9b98e', LEAD)

    def __init__(self, il, cx, cy, R, angles=(196, 222, 248, 274, 300, 326, 352), label_at=(150, 131, 112, 93, 74, 55, 36)):
        self.il, self.cx, self.cy, self.R = il, cx, cy, R
        self.rt = 0.20 * R
        self.rb = np.linspace(0.23 * R, 0.84 * R, 8)               # 7 planetary rings
        self.rf = (0.84 * R, 0.95 * R)                             # fixed stars
        self.angles, self.label_at = angles, label_at
        self.discs = []
        for k, ang in enumerate(angles):
            rm = (self.rb[k] + self.rb[k + 1]) / 2
            a = np.radians(ang)
            self.discs.append((cx + rm * np.cos(a), cy - rm * np.sin(a), (self.rb[1] - self.rb[0]) * 0.52))
        rng = np.random.default_rng(11)
        self.fstars = []
        for a in np.linspace(0, 2 * np.pi, 22, endpoint=False) + rng.normal(0, 0.06, 22):
            if abs(np.degrees(a) % 360 - 90) < 24: continue          # leave room for the name
            rr = rng.uniform(0.865, 0.925) * R
            self.fstars.append((cx + rr * np.cos(a), cy - rr * np.sin(a), rng.uniform(4.6, 6.4)))

    def _c(self, r, n=None):
        n = n or max(60, int(r * 1.3))
        t = np.linspace(0, 2 * np.pi, n)
        return np.stack([self.cx + r * np.cos(t), self.cy + r * np.sin(t)], 1)

    def draw(self):
        il, R = self.il, self.R
        il.pen([self._c(r) for r in list(self.rb) + [self.rt, self.rf[1], R]], 1.0, 'diagram', 0.9)

    def gild(self):
        il, cx, cy, R = self.il, self.cx, self.cy, self.R
        il.gild(il.ring(cx, cy, self.rf[1], R), cushion=3.5)
        x, y, r = self.discs[3]
        il.gild(np.maximum(il.circle(x, y, r * 1.1), il.mask([il.star(x, y, r * 1.9, 12, 0.6)])), cushion=2.2)
        il.gild(il.mask([il.star(x_, y_, r_, 6, 0.45) for x_, y_, r_ in self.fstars]) * il.ring(cx, cy, *self.rf), cushion=1.2)

    def paint(self):
        il, cx, cy, R = self.il, self.cx, self.cy, self.R
        # ring tints, alternating
        for k in range(7):
            if k % 2 == 0:
                il.wash(il.ring(cx, cy, self.rb[k], self.rb[k + 1]), '#d9c49a', 0.45)
        # fixed stars: azurite, painted round the gilded stars
        stars = il.mask([il.star(x_, y_, r_ + 1.2, 6, 0.45) for x_, y_, r_ in self.fstars])
        il.paint(il.ring(cx, cy, *self.rf) * (1 - stars), AZURE, mix=(AZURE_DARK, smoothstep(cy - R, cy + R, il.YY)), granular=1.0)
        # the earth: a T-O map -- ocean round, the T of waters, three parts of the land
        rt = self.rt
        il.paint(il.circle(cx, cy, rt), AZURE_LIGHT, granular=0.6)
        land = il.circle(cx, cy, rt * 0.8)
        il.paint(land * (il.YY < cy), GREEN)
        il.paint(land * (il.YY >= cy) * (il.XX < cx), '#b9944c')
        il.paint(land * (il.YY >= cy) * (il.XX >= cx), '#a7713f')
        t = il.mask(lines=[([(cx - rt * 0.8, cy), (cx + rt * 0.8, cy)], 2.6), ([(cx, cy), (cx, cy + rt * 0.8)], 2.6)])
        il.paint(t * land, AZURE_LIGHT, texture=0.4)
        # planet discs
        for k, ((x, y, r), col) in enumerate(zip(self.discs, self.COLS)):
            if col == 'gold': continue
            m = il.circle(x, y, r)
            if k == 0:            # the moon: a crescent
                m = np.clip(m - il.circle(x + r * 0.45, y - r * 0.2, r * 0.85), 0, 1)
            il.paint(m, col, mix=('#3a3a3a', smoothstep(x - r, x + r * 1.4, il.XX) * 0.35))

    def pen(self, xh=9.0):
        il, cx, cy, R = self.il, self.cx, self.cy, self.R
        il.outline(il.ring(cx, cy, self.rf[1], R), 1.3)
        il.pen([self._c(r) for r in list(self.rb) + [self.rt, self.rf[0]]], 0.9, 'iron', 0.85)
        x, y, r = self.discs[3]
        il.outline(np.maximum(il.circle(x, y, r * 1.1), il.mask([il.star(x, y, r * 1.9, 12, 0.6)])), 0.9)
        for k, (x, y, r) in enumerate(self.discs):
            if k == 3: continue
            m = il.circle(x, y, r)
            if k == 0: m = np.clip(m - il.circle(x + r * 0.45, y - r * 0.2, r * 0.85), 0, 1)
            il.outline(m, 0.9)
        il.outline(il.circle(cx, cy, self.rt), 1.1)
        # names round the rings, alternating red and black
        for k, name in enumerate(self.NAMES):
            rm = (self.rb[k] + self.rb[k + 1]) / 2 - xh * 0.5
            il.arc_text(name, cx, cy, rm, self.label_at[k], xh, 'red' if k % 2 == 0 else 'iron', 0.2)
        il.arc_text('firmamentum', cx, cy, (self.rf[0] + self.rf[1]) / 2 - xh * 0.5 - 0.5, 90, xh * 0.95, 'white', 0.2)
