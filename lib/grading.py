"""grading — 阅卷批改 / Exam Grading: an answer sheet on a green felt desk, marked in red (numpy + Pillow only).

A dark green felt desk under a warm lamp. On it, a beige answer sheet (a few more sheets stacked under it), an
answer-key card held by a black binder clip and a small slip. The sheet is printed: timing marks down the left edge,
corner marks, a heavy title, fields, a ticket number with bubble columns, a score / grader table, numbered sections,
ruled answer lines and a hatched grading column. Then the paper gets written on, and that is what animates:

  papers      `Paper` keeps its own buffers (paper colour with mottle, fibres and a faint cockle; alpha with any
              punched holes) in its own frame. Draw on it in canvas coordinates *as if unrotated*; its resting
              rotation turns everything about its centre. `place(paper, lift, dx, dy, rot)` shows it: lifted it is a
              little larger and casts a wide, soft, offset shadow on the felt; laid down the shadow tightens to a
              contact line. Printing is immediate (multiplied into the paper); white type is `knock`ed out of a
              printed band, so it is the paper itself.
  marks       everything written after printing is a retained `Mark` with `progress` 0..1 (how far it has been
              written), so stages can show it half done. Each mark has a density map (Beer-Lambert: the paper colour
              times exp(-density * absorbance of the ink), so ink over ink and ink over print deepen naturally) and a
              time map (when each pixel was reached). Kinds:
                - red pen strokes: wave underline, hand-drawn ellipse (overshoots its start and grows a little), a
                  bowed leader, a cross, a check, a straight underline, any polyline; the score is digits drawn as
                  pen strokes, circled. Gel ink: a bead of ink where the pen lands, pressure drifting along the line,
                  slight feathering into the fibres, lighter where the tooth of the paper stands up.
                - `note`: an annotation in a bold sans (no handwriting fonts), each character nudged and turned a
                  little, inked with the same red: denser rims, mottle, a faint bleed; revealed char by char.
                - `answer`: the candidate's writing in blue-black, revealed char by char.
                - `stamp`: a vermilion rubber-stamp impression -- double rounded border, heavy label, a check --
                  ragged edges (displaced), clustered pin-hole voids, one end pressed lighter (dry-brush breaks in
                  the thin border there), ink pooled along the rims, a wet bleed just after the press, a slight
                  tilt, and the paper dented round the rubber.
  props       `pen(x, y, lift)`: a red ballpoint seen from above, lying at an angle with its tip on (x, y): metal
              cone and ball, ribbed rubber grip, chrome rings, lacquered barrel with a window highlight, clip. It is
              shaded as a cylinder; its shadow starts at the tip and spreads and softens along the pen (the back end
              is held up). `stamper(impression, height)`: the wooden stamp block with its knob above the paper (or
              pressed on it at height 0, which inks the impression). `card.clip(x, y)`: a black binder clip with
              its wire handles up, on the card's top edge.
  light       one warm lamp, upper left: everything (felt, papers, pen) gets the same gentle falloff, plus a
              vignette and a little grain.

    import sys; sys.path.insert(0, 'lib')
    from grading import Grading
    g = Grading(1920, 1080, seed=4)
    g.desk()
    s = g.sheet(600, 30, 1250, 1100, stack=2)
    s.title('数学单元测验', 664, 112, sub='UNIT TEST · FORM A')
    s.rules(664, 1480, [560, 630])
    a = s.answer('128 ÷ 16 = 6（天）', 690, 620)
    g.place(s, lift=1, dx=-30, dy=-40, rot=-2); g.stage('sheet_up')
    g.place(s); g.stage('sheet_down')
    st = s.stamp(1640, 610, '列式正确')
    g.stamper(st, 0.8); g.stage('hover'); g.stamper(st, 0); g.stage('press'); g.stamper(None)
    w = s.wave(690, 900, 632); r = s.ring(795, 610, 125, 34)
    for p in (0.3, 0.6, 1.0): g.write(w, p); g.stage(f'wave{p}')
    g.pen(1600, 230, lift=0.5)
    g.save('grading.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, spline, noise2d, smoothstep, shift, load_font, fbm1d

INK = '#22262a'        # printed black
GRAY = '#7a7366'       # printed captions
RULE = '#486880'       # blue-grey ruling and bubbles
ANSWER = '#1d2a4c'     # the candidate's blue-black ink
PEN = '#c3121f'        # red pen
STAMP = '#c7382c'      # vermilion stamp pad
NAVY = '#24375a'       # answer-key header band
FELT = '#3b5546'       # green felt desk
PAPERS = {'sheet': '#f7f1e1', 'card': '#eff1eb', 'slip': '#f5eedc', 'white': '#fbfaf5'}
SHADOW = (0.15, 0.14, 0.12)      # shadow tint (multiplies; near neutral so it stays green on felt and warm on paper)

_MA = '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
_FONT_TABLE = {   # (glob, face index); first hit wins -- macOS, Linux, Windows. Override: $INKPAINT_FONT_GRADING_<KIND>
    'heavy': [(_MA + 'Lantinghei.ttc', 2), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2),
              ('/System/Library/Fonts/STHeiti Medium.ttc', 1), ('/usr/share/fonts/**/NotoSansCJK*Black*.tt[cf]', 0),
              ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0)],
    'bold': [(_MA + 'PingFang.ttc', 11), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2),
             ('/System/Library/Fonts/STHeiti Medium.ttc', 1), ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0),
             ('C:/Windows/Fonts/msyhbd.ttc', 0)],
    'medium': [(_MA + 'PingFang.ttc', 7), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
               ('/usr/share/fonts/**/NotoSansCJK*Medium*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSansCJK*Regular*.tt[cf]', 0),
               ('C:/Windows/Fonts/msyh.ttc', 0)],
    'body': [(_MA + 'PingFang.ttc', 3), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
             ('/System/Library/Fonts/STHeiti Light.ttc', 1), ('/usr/share/fonts/**/NotoSansCJK*Regular*.tt[cf]', 0),
             ('C:/Windows/Fonts/msyh.ttc', 0)],
    'light': [(_MA + 'PingFang.ttc', 15), ('/System/Library/Fonts/STHeiti Light.ttc', 1),
              ('/usr/share/fonts/**/NotoSansCJK*Light*.tt[cf]', 0), ('C:/Windows/Fonts/msyhl.ttc', 0)],
    'latin': [('/System/Library/Fonts/Avenir Next.ttc', 2), ('/System/Library/Fonts/HelveticaNeue.ttc', 10),
              ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'latin_heavy': [('/System/Library/Fonts/Avenir Next.ttc', 8), ('/System/Library/Fonts/HelveticaNeue.ttc', 1),
                    ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'digits': [('/System/Library/Fonts/Supplemental/DIN Alternate Bold.ttf', 0), ('/System/Library/Fonts/Avenir Next.ttc', 0),
               ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'mono': [('/System/Library/Fonts/Menlo.ttc', 0), ('/usr/share/fonts/**/DejaVuSansMono.ttf', 0), ('C:/Windows/Fonts/consola.ttf', 0)],
}
_FONTS = {}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _absorb(c):
    """Beer-Lambert absorbance of an ink colour: density 1 over white paper gives exactly this colour"""
    return -np.log(np.clip(_c(c), 0.02, 1.0)).astype(np.float32)


def font(kind, size):
    """PIL font: heavy (titles, stamps), bold (notes, headings), medium, body, light (CJK sans, PingFang /
    Lantinghei on macOS), latin, latin_heavy, digits, mono -- or any core.load_font style name"""
    key = (kind, int(size))
    if key in _FONTS: return _FONTS[key]
    f = None
    env = os.environ.get('INKPAINT_FONT_GRADING_' + kind.upper())
    cands = ([(env, 0)] if env and os.path.exists(env) else []) + _FONT_TABLE.get(kind, [])
    for pat, idx in cands:
        for p in glob.glob(pat, recursive=True):
            try:
                f = ImageFont.truetype(p, int(size), index=idx); break
            except OSError:
                continue
        if f: break
    if f is None:
        f = load_font('cjk_sans' if kind in ('heavy', 'bold', 'medium', 'body', 'light') else
                      ('sans_bold' if kind in ('latin', 'latin_heavy', 'digits') else kind), size)
    _FONTS[key] = f
    return f


def _resample(P, step=1.0):
    P = np.asarray(P, np.float32)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = float(s[-1])
    if L < 1e-3: return P[:1].repeat(2, 0), np.array([0.0, 1.0], np.float32), 1e-3
    t = np.linspace(0, L, max(2, int(L / step) + 1))
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1).astype(np.float32), (t / L).astype(np.float32), L


def _erode(m, r=1):
    """min filter (4-neighbour, r steps): erodes a mask, or spreads the earliest time of a time map"""
    out = m.copy()
    for _ in range(int(r)):
        b = out.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            np.minimum(b, np.roll(np.roll(out, dy, 0), dx, 1), out=b)
        out = b
    return out


def _quad(a, c, b, n=40):
    t = np.linspace(0, 1, n)[:, None]
    a, c, b = (np.asarray(v, np.float32) for v in (a, c, b))
    return ((1 - t) ** 2 * a + 2 * (1 - t) * t * c + t * t * b).astype(np.float32)


def _sample(a, yy, xx):
    """bilinear sample of a 2-D array at float coordinates (clamped)"""
    H, W = a.shape
    xx = np.clip(xx, 0, W - 1.001); yy = np.clip(yy, 0, H - 1.001)
    x0 = xx.astype(np.int32); y0 = yy.astype(np.int32)
    fx = xx - x0; fy = yy - y0
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) +
            a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)


# ---------------------------------------------------------------- handwritten digits for the score (unit box 0.62 x 1, y down)
_DIGITS = {
    '0': [[(0.34, 0.02), (0.1, 0.12), (0.02, 0.5), (0.12, 0.9), (0.34, 1.0), (0.54, 0.88), (0.62, 0.5), (0.54, 0.12), (0.32, 0.0), (0.18, 0.08)]],
    '1': [[(0.14, 0.2), (0.36, 0.0)], [(0.36, 0.0), (0.35, 0.5), (0.34, 1.0)]],
    '2': [[(0.04, 0.24), (0.14, 0.06), (0.34, 0.0), (0.54, 0.1), (0.56, 0.32), (0.4, 0.56), (0.18, 0.8), (0.02, 0.98)], [(0.02, 0.98), (0.32, 0.97), (0.62, 0.95)]],
    '3': [[(0.04, 0.12), (0.26, 0.0), (0.5, 0.06), (0.54, 0.26), (0.38, 0.42), (0.2, 0.47)], [(0.2, 0.47), (0.46, 0.52), (0.6, 0.72), (0.5, 0.94), (0.26, 1.0), (0.02, 0.9)]],
    '4': [[(0.46, 0.0), (0.24, 0.36), (0.02, 0.68)], [(0.02, 0.68), (0.32, 0.67), (0.62, 0.66)], [(0.47, 0.3), (0.46, 0.65), (0.45, 1.0)]],
    '5': [[(0.14, 0.04), (0.11, 0.25), (0.08, 0.46)], [(0.08, 0.46), (0.3, 0.38), (0.52, 0.46), (0.6, 0.7), (0.48, 0.93), (0.24, 0.99), (0.02, 0.88)], [(0.14, 0.04), (0.38, 0.03), (0.6, 0.02)]],
    '6': [[(0.54, 0.04), (0.28, 0.1), (0.1, 0.36), (0.04, 0.68), (0.16, 0.94), (0.38, 1.0), (0.56, 0.86), (0.56, 0.62), (0.38, 0.5), (0.16, 0.56), (0.06, 0.7)]],
    '7': [[(0.02, 0.06), (0.32, 0.04), (0.6, 0.02)], [(0.6, 0.02), (0.48, 0.34), (0.38, 0.66), (0.3, 1.0)]],
    '8': [[(0.52, 0.12), (0.32, 0.0), (0.1, 0.1), (0.12, 0.32), (0.34, 0.48), (0.56, 0.64), (0.54, 0.9), (0.3, 1.0), (0.06, 0.88), (0.08, 0.64), (0.32, 0.48), (0.52, 0.32), (0.54, 0.16), (0.44, 0.04)]],
    '9': [[(0.56, 0.24), (0.42, 0.44), (0.18, 0.46), (0.04, 0.28), (0.14, 0.06), (0.36, 0.0), (0.56, 0.12), (0.58, 0.3)], [(0.58, 0.3), (0.54, 0.64), (0.44, 1.0)]],
}


# ================================================================ marks (retained, with progress)
class Mark:
    """Ink put on a paper after printing. `progress` 0..1 is how far it has been written (1 = done, 0 = not yet).
    D is the density map of a local crop at (oy, ox) in paper-local pixels; T the time map (when each pixel was
    reached, 0..1) or None for marks that appear at once."""
    def __init__(self, paper, K, D, T, oy, ox, path=None, soft=0.01, kind='pen'):
        self.paper, self.K, self.D, self.T, self.oy, self.ox = paper, K, D, T, oy, ox
        self.path = path                    # (pts in paper coordinates, t) for tip(); pts sampled ~1 px
        self.soft = soft
        self.kind = kind
        self.progress = 1.0
        self.shade = None                   # multiplicative shading (stamp dent), applied with the ink
        self.wet = 0.0
        self.wetD = None

    def density(self):
        p = self.progress
        if p <= 0: return None
        D = self.D
        if self.wetD is not None and self.wet > 0: D = D + self.wetD * self.wet
        if p >= 1 or self.T is None: return D
        return D * np.clip((p - self.T) / self.soft + 1.0, 0, 1) * (self.T <= p + self.soft)

    def apply(self, rgb):
        D = self.density()
        if D is None: return
        h, w = D.shape
        sub = rgb[self.oy:self.oy + h, self.ox:self.ox + w]
        if self.shade is not None and self.progress > 0:
            sub *= self.shade[..., None]
        sub *= np.exp(-D[..., None] * self.K)

    def tip(self, p=None):
        """the writing front at progress p (default: current), in paper coordinates"""
        p = self.progress if p is None else p
        if self.path is None: return None
        pts, t = self.path
        i = int(np.clip(np.searchsorted(t, p), 0, len(pts) - 1))
        return float(pts[i, 0]), float(pts[i, 1])


class Group:
    """Several marks written one after another (a cross, a score with its ring). Setting `progress` hands it out
    in proportion to each part's length; `tip()` follows the part being written."""
    def __init__(self, parts, weights=None):
        self.parts = list(parts)
        w = np.array(weights if weights is not None else [max(1.0, m.length) for m in self.parts], np.float64)
        self.edges = np.concatenate([[0], np.cumsum(w / w.sum())])
        self.length = float(sum(m.length for m in self.parts))
        self._p = 1.0

    @property
    def progress(self):
        return self._p

    @progress.setter
    def progress(self, p):
        self._p = p
        for m, a, b in zip(self.parts, self.edges[:-1], self.edges[1:]):
            m.progress = float(np.clip((p - a) / (b - a), 0, 1))

    def tip(self, p=None):
        p = self._p if p is None else p
        for m, a, b in zip(self.parts, self.edges[:-1], self.edges[1:]):
            if p <= b + 1e-9:
                return m.tip(float(np.clip((p - a) / (b - a), 0, 1)))
        return self.parts[-1].tip(1.0)


# ================================================================ paper
class Paper:
    """One sheet or card on the desk. Coordinates are canvas coordinates of the paper as if unrotated; its own
    rotation (`rot`) and pose (`Grading.place`) are applied when composited."""

    def __init__(self, g, x, y, w, h, tint, rot, stack, radius, margin, seed, grain):
        self.g = g
        self.x0, self.y0, self.w, self.h = int(round(x)), int(round(y)), int(round(w)), int(round(h))
        self.rot = float(rot)
        self.M = int(margin)
        self.X0, self.Y0 = self.x0 - self.M, self.y0 - self.M
        self.LW, self.LH = self.w + 2 * self.M, self.h + 2 * self.M
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.tint = _c(tint)
        self.marks = []
        self.state = None
        self._shadow_key = None
        LH, LW, M = self.LH, self.LW, self.M
        rgb = np.zeros((LH, LW, 3), np.float32)
        alpha = np.zeros((LH, LW), np.float32)
        # sheets stacked underneath (offset, a shade darker), then the paper itself
        for k, (ox, oy, tone) in enumerate(stack):
            m = self._rrect_local(M + ox, M + oy, M + ox + self.w, M + oy + self.h, radius)
            col = self.tint * tone
            e = np.clip(m - _erode(m, 1), 0, 1)
            rgb = rgb * (1 - m[..., None]) + (col * (1 - 0.16 * e[..., None])) * m[..., None]
            alpha = np.maximum(alpha, m)
        m = self._rrect_local(M, M, M + self.w, M + self.h, radius)
        mott = noise2d(LH, LW, 110, 4, seed + 1) - 0.5
        cock = noise2d(LH, LW, 420, 2, seed + 2) - 0.5
        fib = blur(self.rng.normal(0, 1, (LH, LW)).astype(np.float32), 0.7)
        fib /= fib.std() + 1e-6
        self.grain = np.clip(0.5 + 0.18 * fib + 0.6 * (noise2d(LH, LW, 3.0, 2, seed + 3) - 0.5), 0, 1).astype(np.float32)
        tex = 1 + grain * (0.045 * mott + 0.010 * fib + 0.028 * cock)
        base = self.tint[None, None, :] * tex[..., None]
        # stray fibres and specks
        im = Image.new('L', (LW, LH), 0); d = ImageDraw.Draw(im)
        for _ in range(int(self.w * self.h / 9000 * grain)):
            x, y = self.rng.uniform(M, M + self.w), self.rng.uniform(M, M + self.h)
            a = self.rng.uniform(0, np.pi); L = self.rng.uniform(4, 16)
            d.line([(x, y), (x + np.cos(a) * L, y + np.sin(a) * L)], fill=int(self.rng.uniform(20, 60)), width=1)
        for _ in range(int(self.w * self.h / 30000 * grain)):
            x, y = self.rng.uniform(M, M + self.w), self.rng.uniform(M, M + self.h)
            d.ellipse((x - 0.8, y - 0.8, x + 0.8, y + 0.8), fill=int(self.rng.uniform(40, 110)))
        sp = blur(np.asarray(im, np.float32) / 255, 0.5)
        base *= (1 - 0.30 * sp[..., None] * np.array([0.8, 0.9, 1.0], np.float32))
        e = np.clip(m - _erode(m, 1), 0, 1)
        base *= (1 - 0.13 * e[..., None])
        self.base = base.astype(np.float32)              # unprinted paper: what knocked-out type shows
        self.rgb = (rgb * (1 - m[..., None]) + base * m[..., None]).astype(np.float32)
        self.alpha = np.maximum(alpha, m).astype(np.float32)
        self.mask = m.astype(np.float32)                  # the top sheet only (where printing can land)

    # ------------------------------------------------------------ coordinates
    def _rrect_local(self, x0, y0, x1, y1, r, ss=2):
        im = Image.new('L', (self.LW * ss, self.LH * ss), 0)
        ImageDraw.Draw(im).rounded_rectangle((x0 * ss, y0 * ss, x1 * ss - 1, y1 * ss - 1), radius=r * ss, fill=255)
        return np.asarray(im.resize((self.LW, self.LH), Image.BOX), np.float32) / 255

    def pose(self):
        """(centre x, centre y, scale, rotation deg) of the paper as currently placed"""
        lift, dx, dy, drot = self.state if self.state else (0.0, 0.0, 0.0, 0.0)
        return self.x0 + self.w / 2 + dx, self.y0 + self.h / 2 + dy, 1 + 0.035 * lift, self.rot + drot

    def to_canvas(self, x, y):
        """paper coordinates -> canvas coordinates under the current pose"""
        cx, cy, s, rot = self.pose()
        th = np.deg2rad(rot); c, si = np.cos(th), np.sin(th)
        u, v = (x - (self.x0 + self.w / 2)) * s, (y - (self.y0 + self.h / 2)) * s
        return cx + c * u + si * v, cy - si * u + c * v

    # ------------------------------------------------------------ low-level printing
    def _blank(self, x0, y0, x1, y1, ss=2):
        """an 'L' scratch image over the paper box (paper coords) -> (img, draw, lx0, ly0, lx1, ly1)"""
        lx0 = max(0, int(np.floor(x0 - self.X0)) - 2); ly0 = max(0, int(np.floor(y0 - self.Y0)) - 2)
        lx1 = min(self.LW, int(np.ceil(x1 - self.X0)) + 3); ly1 = min(self.LH, int(np.ceil(y1 - self.Y0)) + 3)
        if lx1 <= lx0 or ly1 <= ly0: return None
        im = Image.new('L', ((lx1 - lx0) * ss, (ly1 - ly0) * ss), 0)
        return im, ImageDraw.Draw(im), lx0, ly0, lx1, ly1

    def _ink(self, m, ly0, lx0, colour, alpha=1.0, mode='ink'):
        """print a coverage crop at local (ly0, lx0). mode 'ink' multiplies (offset ink), 'knock' restores the bare
        paper (white type out of a band), 'over' paints opaque"""
        h, w = m.shape
        a = (m * alpha * self.mask[ly0:ly0 + h, lx0:lx0 + w])[..., None]
        sub = self.rgb[ly0:ly0 + h, lx0:lx0 + w]
        if mode == 'ink':
            sub *= 1 - a * (1 - _c(colour))
        elif mode == 'knock':
            sub[:] = sub * (1 - a) + self.base[ly0:ly0 + h, lx0:lx0 + w] * a
        else:
            sub[:] = sub * (1 - a) + _c(colour) * a

    def _shape(self, fn, box, colour, alpha=1.0, mode='ink', ss=2):
        r = self._blank(*box, ss=ss)
        if r is None: return
        im, d, lx0, ly0, lx1, ly1 = r
        fn(d, lambda x, y: ((x - self.X0 - lx0) * ss, (y - self.Y0 - ly0) * ss), ss)
        m = np.asarray(im.resize((lx1 - lx0, ly1 - ly0), Image.BOX), np.float32) / 255
        self._ink(m, ly0, lx0, colour, alpha, mode)

    def _text_crop(self, s, x, y, size, kind, anchor, spacing, rot=0.0, jitter=0.0, seed=0):
        """text mask crop in local pixels + per-character x extents (paper coords) for reveal / tips"""
        f = font(kind, size)
        adv = [f.getlength(ch) for ch in s]
        total = sum(adv) + spacing * max(0, len(s) - 1)
        xs = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        asc, desc = f.getmetrics()
        yb = {'s': y, 'm': y + (asc - desc) / 2 * 0.86, 't': y + asc, 'b': y - desc}.get(anchor[1], y)
        pad = int(size * 0.5) + 4
        r = self._blank(xs - pad, yb - asc - pad, xs + total + pad, yb + desc + pad, ss=1)
        if r is None: return None
        im, d, lx0, ly0, lx1, ly1 = r
        rng = np.random.default_rng(seed)
        ext = []
        cx = xs
        for ch, a in zip(s, adv):
            px, py = cx - self.X0 - lx0, yb - self.Y0 - ly0
            if jitter and ch.strip():
                g = Image.new('L', (int(size * 2), int(size * 2)), 0)
                ImageDraw.Draw(g).text((size * 0.5, size * 1.4), ch, font=f, fill=255, anchor='ls')
                g = g.rotate(rng.uniform(-1, 1) * 3.5 * jitter, resample=Image.BICUBIC, center=(size * 0.5 + a / 2, size * 1.0))
                ox_, oy_ = rng.uniform(-1, 1) * 1.6 * jitter, rng.uniform(-1, 1) * 2.2 * jitter
                im.paste(255, (int(round(px - size * 0.5 + ox_)), int(round(py - size * 1.4 + oy_))), g)
            else:
                d.text((px, py), ch, font=f, fill=255, anchor='ls')
            ext.append((cx, cx + a))
            cx += a + spacing
        m = np.asarray(im, np.float32) / 255
        if rot:
            m = np.asarray(Image.fromarray(m, 'F').rotate(rot, resample=Image.BICUBIC, center=(x - self.X0 - lx0, y - self.Y0 - ly0)), np.float32)
        return m, ly0, lx0, ext, yb - asc * 0.78, yb + desc * 0.2

    # ------------------------------------------------------------ printing (immediate)
    def text(self, s, x, y, size, kind='body', colour=INK, anchor='ls', spacing=0.0, alpha=1.0, rot=0.0, mode='ink'):
        """printed type. anchor: [l m r] + [s baseline, m middle, t top, b bottom]; mode 'knock' = white type out of a band"""
        r = self._text_crop(s, x, y, size, kind, anchor, spacing, rot)
        if r is None: return
        m, ly0, lx0 = r[:3]
        self._ink(m, ly0, lx0, colour, alpha, mode)
        return r[3][-1][1] if r[3] else x

    def width(self, s, size, kind='body', spacing=0.0):
        f = font(kind, size)
        return sum(f.getlength(ch) for ch in s) + spacing * max(0, len(s) - 1)

    def rect(self, x0, y0, x1, y1, fill=None, line=None, width=1.5, radius=0, alpha=1.0, mode='ink'):
        def fn(d, P, ss):
            a, b = P(x0, y0), P(x1, y1)
            if fill is not None:
                d.rounded_rectangle((a[0], a[1], b[0] - 1, b[1] - 1), radius=radius * ss, fill=255)
        if fill is not None:
            self._shape(fn, (x0, y0, x1, y1), fill, alpha, mode)
        if line is not None:
            def fl(d, P, ss):
                a, b = P(x0, y0), P(x1, y1)
                d.rounded_rectangle((a[0], a[1], b[0] - 1, b[1] - 1), radius=radius * ss, outline=255, width=max(1, int(round(width * ss))))
            self._shape(fl, (x0 - width, y0 - width, x1 + width, y1 + width), line, alpha)

    def line(self, pts, width=1.2, colour=INK, alpha=1.0, dash=None):
        P = np.asarray(pts, np.float32)
        if dash:
            Q, t, L = _resample(P, 0.5)
            on = ((t * L) % (dash[0] + dash[1])) < dash[0]
            segs, cur = [], []
            for q, o in zip(Q, on):
                if o: cur.append(q)
                elif cur: segs.append(cur); cur = []
            if cur: segs.append(cur)
        else:
            segs = [P]
        box = (P[:, 0].min() - width - 2, P[:, 1].min() - width - 2, P[:, 0].max() + width + 2, P[:, 1].max() + width + 2)

        def fn(d, Pm, ss):
            for sg in segs:
                if len(sg) < 2: continue
                d.line([Pm(x, y) for x, y in sg], fill=255, width=max(1, int(round(width * ss))))
        self._shape(fn, box, colour, alpha)

    def ellipse(self, cx, cy, rx, ry, fill=None, line=None, width=1.0, alpha=1.0):
        if fill is not None:
            self._shape(lambda d, P, ss: d.ellipse((*P(cx - rx, cy - ry), *P(cx + rx, cy + ry)), fill=255),
                        (cx - rx, cy - ry, cx + rx, cy + ry), fill, alpha)
        if line is not None:
            self._shape(lambda d, P, ss: d.ellipse((*P(cx - rx, cy - ry), *P(cx + rx, cy + ry)), outline=255, width=max(1, int(round(width * ss)))),
                        (cx - rx - width, cy - ry - width, cx + rx + width, cy + ry + width), line, alpha)

    def hatch(self, x0, y0, x1, y1, spacing=10.0, angle=45.0, width=2.0, colour=RULE, alpha=0.07):
        def fn(d, P, ss):
            a = np.deg2rad(angle); dx, dy = np.cos(a), -np.sin(a)
            n = int((x1 - x0 + y1 - y0) / spacing) + 4
            for k in range(-n, n):
                ox, oy = x0 + k * spacing / max(1e-3, abs(np.sin(a))), y1
                d.line([P(ox, oy), P(ox + dx * 3000, oy + dy * 3000)], fill=255, width=max(1, int(round(width * ss))))
        r = self._blank(x0, y0, x1, y1)
        if r is None: return
        im, d, lx0, ly0, lx1, ly1 = r
        fn(d, lambda x, y: ((x - self.X0 - lx0) * 2, (y - self.Y0 - ly0) * 2), 2)
        m = np.asarray(im.resize((lx1 - lx0, ly1 - ly0), Image.BOX), np.float32) / 255
        Y, X = np.mgrid[ly0:ly1, lx0:lx1]
        m *= ((X + self.X0 >= x0) & (X + self.X0 < x1) & (Y + self.Y0 >= y0) & (Y + self.Y0 < y1))
        self._ink(m, ly0, lx0, colour, alpha)

    def grid(self, x0, y0, x1, y1, step=14.0, colour=RULE, alpha=0.12, width=0.8):
        xs = np.arange(x0, x1 + 0.1, step); ys = np.arange(y0, y1 + 0.1, step)

        def fn(d, P, ss):
            for x in xs: d.line([P(x, y0), P(x, y1)], fill=255, width=max(1, int(round(width * ss))))
            for y in ys: d.line([P(x0, y), P(x1, y)], fill=255, width=max(1, int(round(width * ss))))
        self._shape(fn, (x0 - 2, y0 - 2, x1 + 2, y1 + 2), colour, alpha)

    def rules(self, x0, x1, ys, colour=RULE, alpha=0.45, width=1.0):
        """ruled answer lines at the given y's"""
        for y in ys:
            self.line([(x0, y), (x1, y)], width, colour, alpha)

    def timing_track(self, x, y0, y1, step=30.0, w=22.0, h=8.0, colour=INK):
        """OMR timing marks: a column of black dashes down the edge"""
        y = y0
        while y + h <= y1:
            self.rect(x, y, x + w, y + h, fill=colour, alpha=0.92)
            y += step

    def corner_mark(self, x, y, s=24.0, colour=INK):
        self.rect(x, y, x + s, y + s, fill=colour)

    def holes(self, x, y0, y1, step=34.0, r=6.5):
        """punched binding holes down the edge: cut through the paper (the felt shows) with a crushed rim"""
        ys = np.arange(y0, y1 + 0.1, step)
        im = Image.new('L', (self.LW * 2, self.LH * 2), 0); d = ImageDraw.Draw(im)
        for y in ys:
            lx, ly = (x - self.X0) * 2, (y - self.Y0) * 2
            d.ellipse((lx - r * 2, ly - r * 2, lx + r * 2, ly + r * 2), fill=255)
        cut = np.asarray(im.resize((self.LW, self.LH), Image.BOX), np.float32) / 255
        rim = np.clip(blur(cut, 1.4) - cut, 0, 1)
        self.rgb *= (1 - 0.35 * rim[..., None])
        self.alpha *= 1 - cut
        self.mask *= 1 - cut

    # ------------------------------------------------------------ answer-sheet furniture
    def title(self, s, x, y, size=52, sub=None, sub_size=15, colour=INK):
        """heavy title with a letter-spaced Latin subtitle under it"""
        self.text(s, x, y, size, 'heavy', colour, spacing=size * 0.04)
        if sub:
            self.text(sub, x + 2, y + sub_size * 2.3, sub_size, 'latin', GRAY, spacing=sub_size * 0.3)

    def field(self, label, value, x, y, x1, size=27, gap=54):
        """a form field: grey caption, bold value, a thin underline"""
        self.text(label, x, y, size * 0.7, 'body', GRAY)
        self.text(value, x + gap, y - 1, size, 'bold', INK)
        self.line([(x + gap - 6, y + 12), (x1, y + 12)], 1.0, INK, 0.55)

    def ticket(self, x, y, digits, box=44, gap=8, label='考号', sub='TICKET NO.'):
        """ticket number: boxed digits and a bubble column under each digit with the right bubble filled"""
        self.text(label, x, y - 12, 19, 'bold', INK)
        if sub: self.text(sub, x + 46, y - 13, 11, 'latin', GRAY, spacing=2.5)
        for i, dg in enumerate(digits):
            bx = x + i * (box + gap)
            self.rect(bx, y, bx + box, y + box - 2, fill='#fffdf6', mode='over')
            self.rect(bx, y, bx + box, y + box - 2, line=INK, width=1.3)
            self.text(dg, bx + box / 2, y + box * 0.72, box * 0.57, 'mono', INK, anchor='ms')
            for k in range(10):
                yy = y + box + 14 + k * 13.6
                if str(k) == dg:
                    self.ellipse(bx + box / 2, yy, 13, 5.3, fill=INK)
                else:
                    self.ellipse(bx + box / 2, yy, 13, 5.3, line=RULE, width=0.9, alpha=0.75)
                    self.text(str(k), bx + box / 2, yy + 3.2, 8.5, 'mono', RULE, anchor='ms', alpha=0.9)

    def score_box(self, x, y, w=350, h=172, split=200, head=36, titles=('得分', '阅卷人'), note='满分 100', lines=()):
        """the score / grader table; returns the centre of the empty score cell"""
        self.rect(x, y, x + w, y + head, fill=INK, alpha=0.07)
        self.rect(x, y, x + w, y + h, line=INK, width=2.0)
        self.line([(x, y + head), (x + w, y + head)], 1.2)
        self.line([(x + split, y), (x + split, y + h)], 1.2)
        self.text(titles[0], x + split / 2, y + head * 0.7, 20, 'bold', INK, anchor='ms', spacing=6)
        self.text(titles[1], x + split + (w - split) / 2, y + head * 0.7, 20, 'bold', INK, anchor='ms', spacing=2)
        if note: self.text(note, x + split - 10, y + head + 24, 15, 'body', GRAY, anchor='rs')
        for k, s in enumerate(lines):
            self.text(s, x + split + (w - split) / 2, y + head + 56 + k * 32, 17, 'body', GRAY, anchor='ms')
        return x + split / 2, y + head + (h - head) / 2 + 4

    def fill_example(self, x, y):
        """the bubble-filling legend: 填涂示例 ● 正确  ✓ ✗ ◐ 错误"""
        self.text('填涂示例', x, y, 14, 'body', GRAY)
        self.ellipse(x + 80, y - 5, 12, 5, fill=INK)
        self.text('正确', x + 98, y, 14, 'body', GRAY)
        for k in range(3):
            cx = x + 150 + k * 34
            self.ellipse(cx, y - 5, 12, 5, line=RULE, width=0.9, alpha=0.8)
            if k == 0: self.line([(cx - 5, y - 5), (cx - 1, y - 2), (cx + 6, y - 9)], 1.3)
            if k == 1:
                self.line([(cx - 5, y - 9), (cx + 5, y - 1)], 1.3); self.line([(cx + 5, y - 9), (cx - 5, y - 1)], 1.3)
            if k == 2: self.ellipse(cx - 4, y - 5, 6, 4, fill=INK)
        self.text('错误', x + 254, y, 14, 'body', GRAY)

    def section(self, x, y, num, title, sub=None, meta=None, x1=None, size=26):
        """a numbered section head: dark square with the numeral knocked out, bold title, grey note"""
        s = size * 1.23
        self.rect(x, y, x + s, y + s, fill=INK)
        self.text(num, x + s / 2, y + s * 0.73, size * 0.77, 'bold', INK, anchor='ms', mode='knock')
        tx = x + s + 12
        end = self.text(title, tx, y + s * 0.78, size, 'bold', INK)
        if sub: self.text(sub, end + 14, y + s * 0.75, size * 0.73, 'body', GRAY)
        if meta and x1: self.text(meta, x1, y + s * 0.72, 16, 'body', GRAY, anchor='rs', spacing=1)

    def question(self, x0, y0, x1, y1, s, size=30, kind='body'):
        """the question in a tinted box with a dark bar on the left"""
        self.rect(x0, y0, x1, y1, fill=INK, alpha=0.05)
        self.rect(x0, y0, x0 + 4, y1, fill=INK)
        self.text(s, x0 + 24, (y0 + y1) / 2 + size * 0.36, size, kind, INK)

    def answer_frame(self, x0, y0, x1, y1, col=None, rows=(), head='阅卷栏', note='考生勿填', grid=14.0, lines=()):
        """the answer box: faint grid and ruled lines on the left, a hatched grading column (x >= col) on the
        right with a header row and dashed row separators; rows = [(caption, y_caption, y_separator or None)]"""
        cx = col if col else x1
        if grid: self.grid(x0, y0, cx, y1, grid)
        for y in lines: self.line([(x0 + 10, y), (cx - 12, y)], 1.0, RULE, 0.42)
        if col:
            self.hatch(col, y0, x1, y1)
            self.rect(col, y0, x1, y0 + 36, fill=INK, alpha=0.06)
            self.text(head, col + 18, y0 + 25, 18, 'bold', INK, spacing=4)
            if note: self.text(note, x1 - 14, y0 + 24, 13, 'body', GRAY, anchor='rs', spacing=1)
            self.line([(col, y0), (col, y1)], 1.5)
            self.line([(col + 4, y0), (col + 4, y1)], 0.6)
            self.line([(col, y0 + 36), (x1, y0 + 36)], 0.9)
            for cap, yc, ysep in rows:
                self.text(cap, col + 18, yc, 16, 'body', GRAY, spacing=1)
                if ysep: self.line([(col + 4, ysep), (x1, ysep)], 0.8, INK, 0.6, dash=(4, 4))
        self.rect(x0, y0, x1, y1, line=INK, width=1.5)

    def band(self, x0, y0, x1, y1, colour=NAVY):
        """a solid printed band (the answer key's header)"""
        self.rect(x0, y0, x1, y1, fill=colour)

    def checkbox(self, x, y, s=26, colour=INK):
        self.rect(x, y, x + s, y + s, line=colour, width=1.6, radius=2)

    def circled(self, n, cx, cy, r=15, size=19, colour=INK):
        """a printed circled number ①"""
        self.ellipse(cx, cy, r, r, line=colour, width=1.6)
        self.text(str(n), cx, cy + size * 0.36, size, 'bold', colour, anchor='ms')

    def clip(self, x, y, w=136.0, handle=74.0):
        """a black binder clip gripping the edge at (x, y) (paper coordinates, y on the edge), both wire handles
        folded up: two silver loops spanning the clip, the back one a little lower and in shadow"""
        lx, ly = x - self.X0, y - self.Y0
        ss = 3
        x0, x1 = max(0, int(lx - w / 2 - 50)), min(self.LW, int(lx + w / 2 + 50))
        y0, y1 = max(0, int(ly - handle - 40)), min(self.LH, int(ly + 70))
        cw, ch = x1 - x0, y1 - y0
        bx, by = lx - x0, ly - y0

        def draw(fn):
            im = Image.new('L', (cw * ss, ch * ss), 0)
            fn(ImageDraw.Draw(im))
            return np.asarray(im.resize((cw, ch), Image.BOX), np.float32) / 255
        top, bot = by - 17, by + 19
        P = lambda pts: [(px * ss, py * ss) for px, py in pts]
        body = draw(lambda d: d.rounded_rectangle(P([(bx - w / 2, top), (bx + w / 2, bot)]), radius=5 * ss, fill=255))
        # glossy black steel: a bright band near the top of the fold, a soft one low down, darker toward the ends
        Y = (np.arange(ch, dtype=np.float32)[:, None] - top) / (bot - top)
        X = (np.arange(cw, dtype=np.float32)[None, :] - bx) / (w / 2)
        sh = 0.045 + 0.30 * np.exp(-((Y - 0.18) / 0.08) ** 2) + 0.07 * np.exp(-((Y - 0.72) / 0.14) ** 2)
        sh = sh * (1 - 0.35 * X ** 4) + 0.02
        body_rgb = sh[..., None] * np.array([0.95, 0.97, 1.0], np.float32)
        # the wire handles: each a loop whose legs enter the clip near its ends
        wires, hil = [], []
        for k, (inset, hgt, dxo) in enumerate(((20, handle, 0.0), (26, handle - 12, -5.0))):
            lb, rb = bx - w / 2 + inset + dxo, bx + w / 2 - inset + dxo
            yt = top - hgt
            pts = spline([(lb, top + 4), (lb - 3, top - hgt * 0.5), (lb + 6, yt + 4), (lb + 18, yt), ((lb + rb) / 2, yt - 1),
                          (rb - 18, yt), (rb - 6, yt + 4), (rb + 3, top - hgt * 0.5), (rb, top + 4)], 10)
            wires.append(draw(lambda d: d.line(P(pts), fill=255, width=int(4.6 * ss), joint='curve')))
            hil.append(draw(lambda d: d.line(P(pts - np.array([1.0, 1.2], np.float32)), fill=255, width=int(1.4 * ss), joint='curve')))
        front, back = wires[0], wires[1] * (1 - wires[0])
        wire_a = np.maximum(front, back)
        wire_rgb = np.where((front > back)[..., None],
                            (0.50 + 0.42 * hil[0])[..., None] * np.array([0.92, 0.93, 0.95], np.float32),
                            (0.34 + 0.30 * hil[1])[..., None] * np.array([0.90, 0.91, 0.93], np.float32))
        wire_a = wire_a * (1 - body)
        # shadows on the paper below (down and to the right; the raised handles throw theirs further)
        sub = self.rgb[y0:y1, x0:x1]
        on = self.mask[y0:y1, x0:x1]
        shad = np.clip(blur(shift(body, 5, 8), 3.5) * 0.62 + blur(shift(np.maximum(front, back), 14, 30), 3.0) * 0.30, 0, 0.8)
        sub *= (1 - shad * on)[..., None]
        a = np.maximum(body, wire_a)
        col = body_rgb * body[..., None] + wire_rgb * wire_a[..., None]
        sub[:] = sub * (1 - a[..., None]) + col
        self.alpha[y0:y1, x0:x1] = np.maximum(self.alpha[y0:y1, x0:x1], a)

    # ------------------------------------------------------------ marks (retained; set .progress to animate)
    def _add(self, m):
        self.marks.append(m)
        return m

    def stroke(self, pts, width=3.2, colour=PEN, pressure=0.16, blob=0.35, feather=0.22, smooth=False, seed=None, density=1.0):
        """a pen stroke along pts (paper coordinates). Gel ink: a bead where the pen lands, pressure drifting along
        the line, feathering into the fibres, lighter where the paper's tooth stands up. Returns a Mark"""
        r = np.random.default_rng(self.rng.integers(1 << 30) if seed is None else seed)
        P = spline(pts, 8) if smooth else np.asarray(pts, np.float32)
        Q, t, L = _resample(P, 1.0)
        n = len(Q)
        press = 1 + pressure * fbm1d(n, 60, 3, int(r.integers(1 << 30)))
        wv = width * (0.88 + 0.12 * press) * (0.75 + 0.25 * np.clip(t * L / 6, 0, 1))
        ss = 3
        pad = width * 3 + 6
        x0, y0 = Q[:, 0].min() - pad, Q[:, 1].min() - pad
        x1, y1 = Q[:, 0].max() + pad, Q[:, 1].max() + pad
        lx0 = max(0, int(np.floor(x0 - self.X0))); ly0 = max(0, int(np.floor(y0 - self.Y0)))
        lx1 = min(self.LW, int(np.ceil(x1 - self.X0))); ly1 = min(self.LH, int(np.ceil(y1 - self.Y0)))
        cw, ch = lx1 - lx0, ly1 - ly0
        cov = Image.new('L', (cw * ss, ch * ss), 0); dc = ImageDraw.Draw(cov)
        tim = Image.new('F', (cw * ss, ch * ss), 9.0); dt = ImageDraw.Draw(tim)
        S = [((q[0] - self.X0 - lx0) * ss, (q[1] - self.Y0 - ly0) * ss) for q in Q]
        for i in range(n - 1, 0, -1):          # backwards: the earliest time wins where the stroke crosses itself
            wpx = wv[i] * ss
            dc.line([S[i - 1], S[i]], fill=255, width=max(1, int(round(wpx))))
            dt.line([S[i - 1], S[i]], fill=float(t[i]), width=max(1, int(round(wpx))) + 2)
            rr = wpx / 2
            dc.ellipse((S[i][0] - rr, S[i][1] - rr, S[i][0] + rr, S[i][1] + rr), fill=255)
            dt.ellipse((S[i][0] - rr - 1, S[i][1] - rr - 1, S[i][0] + rr + 1, S[i][1] + rr + 1), fill=float(t[i]))
        rr = wv[0] * ss / 2
        dc.ellipse((S[0][0] - rr, S[0][1] - rr, S[0][0] + rr, S[0][1] + rr), fill=255)
        dt.ellipse((S[0][0] - rr - 1, S[0][1] - rr - 1, S[0][0] + rr + 1, S[0][1] + rr + 1), fill=0.0)
        c = np.asarray(cov.resize((cw, ch), Image.BOX), np.float32) / 255
        T = np.asarray(tim, np.float32).reshape(ch, ss, cw, ss).min(axis=(1, 3))
        T = np.minimum(T, _erode(T, 3))
        Ty = np.where(T > 2, _erode(T, 6), T)
        D = self._gel(c, Ty, Q, t, wv, press, blob, feather, ly0, lx0, r, density)
        Ty = np.where(Ty > 2, 1.0, Ty)
        m = Mark(self, _absorb(colour), D, Ty.astype(np.float32), ly0, lx0, (Q, t), soft=max(0.004, 2.0 / max(L, 1)))
        m.length = L
        return self._add(m)

    def _gel(self, c, T, Q, t, wv, press, blob, feather, ly0, lx0, r, base=1.0):
        ch, cw = c.shape
        g = self.grain[ly0:ly0 + ch, lx0:lx0 + cw]
        Tc = np.clip(T, 0, 1)
        pn = np.interp(Tc, t, (press - 1) / max(1e-3, float(np.abs(press - 1).max())))
        # the pen slows down in turns and leaves more ink there
        d1 = np.gradient(Q, axis=0)
        ang = np.unwrap(np.arctan2(d1[:, 1], d1[:, 0]))
        curv = np.abs(np.gradient(ang))
        k = max(3, int(len(curv) * 0.02)) | 1
        curv = np.convolve(np.pad(curv, k, mode='edge'), np.ones(k) / k, 'same')[k:-k]
        pool = np.interp(Tc, t, np.clip(curv / 0.12, 0, 1))
        mott = noise2d(ch, cw, 9, 2, int(r.integers(1 << 30)))
        big = noise2d(ch, cw, 34, 2, int(r.integers(1 << 30)))
        D = c * base * (0.74 + 0.20 * pn + 0.22 * (mott - 0.5) + 0.26 * (big - 0.5) + 0.26 * pool) * (1 - 0.20 * smoothstep(0.55, 0.85, g))
        # the bead where the pen lands, a smaller one where it lifts
        Y, X = np.mgrid[0:ch, 0:cw].astype(np.float32)
        for k_, amp in ((0, blob), (len(Q) - 1, blob * 0.35)):
            qx, qy = Q[k_, 0] - self.X0 - lx0, Q[k_, 1] - self.Y0 - ly0
            D += amp * np.exp(-((X - qx) ** 2 + (Y - qy) ** 2) / (2 * (wv[k_] * 0.75) ** 2)) * np.clip(c * 1.5, 0, 1)
        # rims a touch darker, a faint feather into the fibres
        D += 0.18 * np.clip(c - _erode(c, 1), 0, 1)
        if feather:
            fb = blur(c, 1.7) * smoothstep(0.30, 0.75, g + 0.25 * (mott - 0.5))
            D += feather * fb * (1 - c)
        return D.astype(np.float32)

    def wave(self, x0, x1, y, amp=4.2, period=21.0, width=2.6, colour=PEN):
        """a wavy underline from x0 to x1: period and height drift like a hand's, and it wanders downhill a little"""
        r = np.random.default_rng(int(self.rng.integers(1 << 30)))
        n = max(60, int((x1 - x0) / 1.2))
        u = np.linspace(0, 1, n)
        ph = np.cumsum(1 + 0.18 * fbm1d(n, n / 3, 2, int(r.integers(1 << 30)))) / n * (x1 - x0) / period * 2 * np.pi
        a = amp * (1 + 0.22 * fbm1d(n, n / 4, 2, int(r.integers(1 << 30))))
        xs = x0 + (x1 - x0) * u + 1.2 * np.sin(ph)
        ys = y + a * np.sin(ph) + u * 2.0 + 0.8 * fbm1d(n, n / 2, 2, int(r.integers(1 << 30)))
        return self.stroke(np.stack([xs, ys], 1), width, colour, pressure=0.24, blob=0.25)

    def ring(self, cx, cy, rx, ry, tilt=-2.0, a0=-30.0, a1=352.0, grow=0.045, width=3.0, colour=PEN):
        """a hand-drawn ellipse round something: starts at a0, overshoots past its start and grows a little"""
        n = 220
        u = np.linspace(0, 1, n)
        a = np.deg2rad(a0 + (a1 - a0) * u)
        k = 1 + grow * u + 0.012 * np.sin(u * 11)
        ex, ey = rx * k * np.cos(a), ry * k * np.sin(a)
        tl = np.deg2rad(tilt)
        P = np.stack([cx + ex * np.cos(tl) - ey * np.sin(tl), cy + ex * np.sin(tl) + ey * np.cos(tl)], 1)
        return self.stroke(P, width, colour, pressure=0.24)

    def leader(self, p0, p1, bend=44.0, width=2.4, colour=PEN):
        """a bowed leader line from p0 to p1 (a quadratic curve lifted by `bend` px)"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        c = (p0 + p1) / 2 + np.array([30, -bend], np.float32)
        return self.stroke(_quad(p0, c, p1, 60), width, colour, pressure=0.14, blob=0.22, density=0.9)

    def underline(self, x0, x1, y, width=2.6, colour=PEN):
        xs = np.linspace(x0, x1, 30)
        ys = y + 1.4 * np.sin(np.linspace(0, np.pi, 30)) + np.linspace(0, 1.2, 30)
        return self.stroke(np.stack([xs, ys], 1), width, colour, pressure=0.1)

    def cross(self, cx, cy, s=22.0, width=3.6, colour=PEN):
        """a red cross: two quick bowed strokes. Returns a Group"""
        a = self.stroke(_quad((cx - 0.86 * s, cy - 0.95 * s), (cx + 0.1 * s, cy - 0.1 * s), (cx + 0.86 * s, cy + s), 24), width, colour, blob=0.3)
        b = self.stroke(_quad((cx + 0.9 * s, cy - s), (cx - 0.05 * s, cy - 0.05 * s), (cx - 0.95 * s, cy + 0.95 * s), 24), width, colour, blob=0.3)
        return Group([a, b])

    def check(self, cx, cy, s=24.0, width=3.4, colour=PEN):
        """a red check mark: short down-stroke, long flick up"""
        P = np.concatenate([_quad((cx - 0.5 * s, cy + 0.0 * s), (cx - 0.32 * s, cy + 0.16 * s), (cx - 0.14 * s, cy + 0.38 * s), 12),
                            _quad((cx - 0.14 * s, cy + 0.38 * s), (cx + 0.1 * s, cy - 0.1 * s), (cx + 0.6 * s, cy - 0.55 * s), 20)[1:]])
        return self.stroke(P, width, colour, blob=0.3)

    def digits(self, s, x, y, h=80.0, width=4.6, colour=PEN, gap=0.16, slant=0.12):
        """a number written with the pen (each digit from stroke skeletons, slanted, a little irregular); (x, y) is
        the top-left. Returns a Group"""
        r = np.random.default_rng(self.rng.integers(1 << 30))
        parts = []
        cx = x
        for ch in s:
            for st in _DIGITS.get(ch, []):
                P = np.array(st, np.float32)
                P = P + r.normal(0, 0.012, P.shape)
                Px = cx + (P[:, 0] + slant * (1 - P[:, 1])) * h
                Py = y + P[:, 1] * h
                parts.append(self.stroke(np.stack([Px, Py], 1), width, colour, smooth=len(P) > 2, pressure=0.2, blob=0.3))
            cx += (0.62 + gap) * h
        return Group(parts)

    def score(self, s, cx, cy, h=80.0, width=4.6, ring=True, colour=PEN):
        """the score: digits centred on (cx, cy), then a ring round them. Returns a Group (digits, ring)"""
        n = len(s)
        wtot = (0.62 * n + 0.16 * (n - 1) + 0.12) * h
        dg = self.digits(s, cx - wtot / 2, cy - h / 2, h, width, colour)
        parts = list(dg.parts)
        if ring:
            parts.append(self.ring(cx + 2, cy + 1, wtot / 2 + h * 0.30, h * 0.70, tilt=-7, a0=-118, a1=-118 + 376, grow=0.06, width=width * 0.7, colour=colour))
        return Group(parts)

    def note(self, s, x, y, size=32, kind='bold', colour=PEN, anchor='ls', jitter=1.0, seed=None):
        """an annotation in a bold sans inked with the red pen: each character nudged and turned a little, denser
        rims, mottle and a faint bleed. Revealed character by character (top-left to bottom-right inside each)"""
        sd = int(self.rng.integers(1 << 30)) if seed is None else seed
        r = self._text_crop(s, x, y, size, kind, anchor, size * 0.04, jitter=jitter, seed=sd)
        m, ly0, lx0, ext, ytop, ybot = r
        ch, cw = m.shape
        rr = np.random.default_rng(sd)
        g = self.grain[ly0:ly0 + ch, lx0:lx0 + cw]
        mott = noise2d(ch, cw, 6, 2, sd + 1)
        big = noise2d(ch, cw, max(8, size * 0.7), 2, sd + 2)
        D = m * (0.66 + 0.22 * mott + 0.34 * big) * (1 - 0.18 * smoothstep(0.55, 0.85, g))
        D += 0.30 * np.clip(m - _erode(m, 1), 0, 1) * (0.6 + 0.8 * big)
        D += 0.20 * blur(m, 1.6) * smoothstep(0.3, 0.8, g + 0.2 * (mott - 0.5)) * (1 - m)
        X = np.arange(cw, dtype=np.float32)[None, :] + lx0 + self.X0
        Y = np.arange(ch, dtype=np.float32)[:, None] + ly0 + self.Y0
        T = np.full((ch, cw), 1.0, np.float32)
        n = len(ext)
        hh = max(1.0, ybot - ytop)
        tips, tt = [], []
        for i, (a, b) in enumerate(ext):
            lo = a - (size * 0.1 if i == 0 else 0); hi = b if i < n - 1 else b + size * 0.3
            inside = (X >= lo) & (X < hi)
            loc = np.clip(((X - a) + 0.5 * (Y - ytop)) / ((b - a) + 0.5 * hh), 0, 1)
            T = np.where(inside, (i + loc) / n, T)
            for u in np.linspace(0, 1, 12, endpoint=False):
                tips.append((a + (b - a) * u, ytop + hh * (0.5 + 0.42 * np.sin(u * np.pi * 4.5)))); tt.append((i + u) / n)
        T = np.where(X < ext[0][0], 0.0, T)
        tips.append((ext[-1][1], ytop + hh * 0.6)); tt.append(1.0)
        mk = Mark(self, _absorb(colour), D.astype(np.float32), T, ly0, lx0, (np.array(tips, np.float32), np.array(tt, np.float32)), soft=0.6 / max(n, 1) / 4, kind='note')
        mk.length = float(ext[-1][1] - ext[0][0]) * 1.5
        return self._add(mk)

    def answer(self, s, x, y, size=32, kind='body', colour=ANSWER, anchor='ls'):
        """the candidate's writing in blue-black, revealed character by character"""
        r = self._text_crop(s, x, y, size, kind, anchor, 0.0)
        m, ly0, lx0, ext, ytop, ybot = r
        ch, cw = m.shape
        X = np.arange(cw, dtype=np.float32)[None, :] + lx0 + self.X0
        n = len(ext)
        T = np.zeros((ch, cw), np.float32)
        for i, (a, b) in enumerate(ext):
            T = np.where(X >= a - 0.5, (i + np.clip((X - a) / max(1.0, b - a), 0, 1)) / n, T)
        g = self.grain[ly0:ly0 + ch, lx0:lx0 + cw]
        D = m * 0.95 * (1 - 0.08 * smoothstep(0.6, 0.9, g)) + 0.05 * blur(m, 1.0) * (1 - m)
        tips = np.array([((a + b) / 2, (ytop + ybot) / 2) for a, b in ext], np.float32)
        mk = Mark(self, _absorb(colour), D.astype(np.float32), T, ly0, lx0, (tips, (np.arange(n, dtype=np.float32) + 0.5) / n), soft=0.3 / max(n, 1), kind='answer')
        mk.length = float(ext[-1][1] - ext[0][0])
        return self._add(mk)

    def stamp(self, cx, cy, label, w=None, h=64.0, rot=-2.0, size=30, check=True, colour=STAMP, press=(0.64, 1.0), seed=None):
        """a rubber-stamp impression (hidden until pressed: progress 0; `Grading.stamper(mark, 0)` presses it):
        double rounded border, heavy label, a check; ragged, pin-holed, one end lighter, rims pooled, slightly
        turned, the paper dented round the rubber. press = (light end, heavy end) ink pressure."""
        sd = int(self.rng.integers(1 << 30)) if seed is None else seed
        r = np.random.default_rng(sd)
        f = font('heavy', size)
        sp = size * 0.1
        lw = sum(f.getlength(c) for c in label) + sp * (len(label) - 1)
        if w is None: w = lw + (size * 1.0 + 14 if check else 0) + 46
        ss = 3
        pw, ph = int(w + 60), int(h + 60)
        im = Image.new('L', (pw * ss, ph * ss), 0); d = ImageDraw.Draw(im)
        ox, oy = (pw - w) / 2, (ph - h) / 2
        d.rounded_rectangle(((ox + 2.2) * ss, (oy + 2.2) * ss, (ox + w - 2.2) * ss, (oy + h - 2.2) * ss), radius=7 * ss, outline=255, width=int(4.4 * ss))
        d.rounded_rectangle(((ox + 7) * ss, (oy + 7) * ss, (ox + w - 7) * ss, (oy + h - 7) * ss), radius=3.5 * ss, outline=255, width=int(1.6 * ss))
        x_text = pw / 2 - (lw + (size + 14 if check else 0)) / 2
        fb = font('heavy', size * ss)
        xx = x_text
        for c in label:
            d.text((xx * ss, (ph / 2 + size * 0.36) * ss), c, font=fb, fill=255, anchor='ls')
            xx += f.getlength(c) + sp
        if check:
            kx, ky, ks = xx + 14 + size * 0.5, ph / 2, size
            pts = [(kx - 0.5 * ks, ky + 0.02 * ks), (kx - 0.14 * ks, ky + 0.36 * ks), (kx + 0.5 * ks, ky - 0.4 * ks)]
            d.line([(px * ss, py * ss) for px, py in pts], fill=255, width=int(5.6 * ss), joint='curve')
            for px, py in (pts[0], pts[2]):
                d.ellipse(((px - 2.8) * ss, (py - 2.8) * ss, (px + 2.8) * ss, (py + 2.8) * ss), fill=255)
        mk = np.asarray(im.resize((pw, ph), Image.BOX), np.float32) / 255
        # ink spreads a hair, edges go ragged (displaced), then turn it
        mk = np.clip(blur(mk, 0.45) * 1.15, 0, 1)
        dx = (noise2d(ph, pw, 5, 2, sd + 1) - 0.5) * 2.6
        dy = (noise2d(ph, pw, 5, 2, sd + 2) - 0.5) * 2.6
        Yg, Xg = np.mgrid[0:ph, 0:pw].astype(np.float32)
        mk = _sample(mk, Yg + dy, Xg + dx)
        block = np.zeros((ph, pw), np.float32)
        bi = Image.new('L', (pw * ss, ph * ss), 0)
        ImageDraw.Draw(bi).rounded_rectangle(((ox - 4) * ss, (oy - 4) * ss, (ox + w + 4) * ss, (oy + h + 4) * ss), radius=10 * ss, fill=255)
        block = np.asarray(bi.resize((pw, ph), Image.BOX), np.float32) / 255
        # pressure: one end lighter, plus a blotchy field
        a = r.uniform(0, 2 * np.pi)
        ramp = ((Xg - pw / 2) * np.cos(a) + (Yg - ph / 2) * np.sin(a)) / (w / 2) * 0.5 + 0.5
        pr = press[0] + (press[1] - press[0]) * np.clip(ramp, 0, 1) ** 0.8 + 0.30 * (noise2d(ph, pw, 30, 3, sd + 3) - 0.5)
        clump = noise2d(ph, pw, 18, 3, sd + 4)
        speck = r.random((ph, pw)).astype(np.float32)
        void = speck < (0.06 + 0.62 * smoothstep(0.5, 0.85, clump)) * np.clip(1.25 - pr, 0.15, 1)
        fine = blur(void.astype(np.float32), 0.55)
        cov = mk * np.clip(smoothstep(0.34, 0.70, pr + 0.42 * (noise2d(ph, pw, 5, 2, sd + 5) - 0.5)) * 1.1, 0, 1) * (1 - 0.92 * fine)
        D = cov * (0.80 + 0.22 * np.clip(pr, 0, 1.1) + 0.16 * (noise2d(ph, pw, 10, 2, sd + 6) - 0.5)) + 0.22 * np.clip(mk - _erode(mk, 1), 0, 1) * cov
        wet = 0.30 * blur(cov, 1.6) * (1 - cov * 0.5)
        dent_hi = shift(blur(block, 2.0), -1, -1) - blur(block, 2.0)
        dent_lo = blur(block, 2.0) - shift(blur(block, 2.0), 1, 2)
        shade = 1 - 0.05 * np.clip(dent_lo, 0, 1) + 0.035 * np.clip(dent_hi, 0, 1) - 0.012 * block
        def turn(arr, fill):
            return np.asarray(Image.fromarray(arr.astype(np.float32), 'F').rotate(rot, resample=Image.BICUBIC, fillcolor=fill), np.float32)
        D, wet, shade = turn(D, 0.0), turn(wet, 0.0), turn(shade, 1.0)
        lx0, ly0 = int(round(cx - pw / 2 - self.X0)), int(round(cy - ph / 2 - self.Y0))
        g = self.grain[ly0:ly0 + ph, lx0:lx0 + pw]
        D = D * (1 - 0.18 * smoothstep(0.6, 0.9, g))
        m_ = Mark(self, _absorb(colour), D.astype(np.float32), None, ly0, lx0, None, kind='stamp')
        m_.shade = shade.astype(np.float32)
        m_.wetD = wet.astype(np.float32)
        m_.progress = 0.0
        m_.length = 1.0
        m_.geom = dict(cx=cx, cy=cy, w=w, h=h, rot=rot)
        return self._add(m_)


# ================================================================ the scene
class Grading:
    PAPERS = PAPERS

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages = keep_stages              # False: stage() is free
        self.stages_dir = stages_dir                # set: stage() writes each snapshot at once (keeps memory low)
        self.stages = []
        self._n_stages = 0
        self.items = []
        self.bg = np.ones((H, W, 3), np.float32) * hexc(FELT)
        self._pen = None
        self._stamper = None
        self._post = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ desk and light
    def desk(self, colour=FELT, nap=1.0):
        """green felt: soft mottle, fine fuzz, a few pills of lint"""
        H, W = self.H, self.W
        s = self.seed
        mott = noise2d(H, W, 260, 4, s + 11) - 0.5
        mid = noise2d(H, W, 40, 3, s + 12) - 0.5
        fz = blur(self.rng.normal(0, 1, (H, W)).astype(np.float32), 0.8)
        fz /= fz.std() + 1e-6
        tex = 1 + nap * (0.15 * mott + 0.07 * mid + 0.035 * fz)
        col = _c(colour)
        bg = col[None, None, :] * tex[..., None]
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        for _ in range(int(900 * nap)):
            x, y = self.rng.uniform(0, W), self.rng.uniform(0, H)
            a = self.rng.uniform(0, np.pi); L = self.rng.uniform(3, 10)
            d.line([(x, y), (x + np.cos(a) * L, y + np.sin(a) * L)], fill=int(self.rng.uniform(40, 120)), width=1)
        lint = blur(np.asarray(im, np.float32) / 255, 0.6)
        bg = bg * (1 + 0.25 * lint[..., None])
        self.bg = bg.astype(np.float32)

    def _postfx(self):
        if self._post is None:
            H, W = self.H, self.W
            Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
            # one warm lamp upper left: a broad, gentle falloff, then a vignette and a little grain
            dx, dy = X / W - 0.32, Y / H - 0.12
            lamp = 1.07 - 0.20 * np.clip(dx * dx * 1.1 + dy * dy * 0.9, 0, 1.4)
            r = np.hypot((X - W / 2) / W, (Y - H / 2) / H)
            vig = 1 - 0.16 * r ** 2 * 2.0
            grain = 1 + 0.014 * (noise2d(H, W, 1.0, 1, self.seed + 99) - 0.5)
            warm = np.array([1.015, 1.0, 0.975], np.float32)
            self._post = ((lamp * vig * grain)[..., None] * warm).astype(np.float32)
        return self._post

    # ------------------------------------------------------------ papers
    def sheet(self, x, y, w, h, tint=PAPERS['sheet'], rot=0.0, stack=2, radius=3, margin=40, seed=None, grain=1.0):
        """an answer sheet (with `stack` more sheets showing underneath). Returns a Paper"""
        st = [(9, 6, 0.93), (5, 3, 0.965)][-stack:] if stack else []
        return Paper(self, x, y, w, h, tint, rot, st, radius, margin, self._seed() if seed is None else seed, grain)

    def card(self, x, y, w, h, tint=PAPERS['card'], rot=0.0, radius=4, margin=110, seed=None, grain=1.0):
        """a card or slip (margin leaves room for a clip standing above its edge). Returns a Paper"""
        return Paper(self, x, y, w, h, tint, rot, [], radius, margin, self._seed() if seed is None else seed, grain)

    def place(self, paper, lift=0.0, dx=0.0, dy=0.0, rot=0.0):
        """show a paper: laid down (all zero), or lifted `lift` (0..1), held off by dx, dy px and turned rot degrees
        more. The first place() puts it on top of everything placed so far"""
        paper.state = (float(lift), float(dx), float(dy), float(rot))
        if not any(it is paper for it in self.items):
            self.items.append(paper)

    def remove(self, paper):
        self.items = [it for it in self.items if it is not paper]

    # ------------------------------------------------------------ props
    def pen(self, x=None, y=None, lift=0.0, angle=28.0, scale=1.0):
        """the red pen lying at `angle` degrees (tip toward upper left), tip on (x, y) in canvas coordinates;
        lift 0 = writing, 1 = held well above the paper. pen(None) puts it away"""
        self._pen = None if x is None else (float(x), float(y), float(lift), float(angle), float(scale))

    def write(self, mark, progress, lift=0.0, angle=28.0):
        """set a mark's progress and bring the pen tip to its writing front"""
        mark.progress = progress
        tp = mark.tip(progress)
        paper = mark.paper if hasattr(mark, 'paper') else mark.parts[0].paper
        if tp is not None:
            x, y = paper.to_canvas(*tp)
            self.pen(x, y, lift, angle)

    def stamper(self, mark=None, height=0.0):
        """the stamp above its impression at `height` (0..1); height 0 presses it (the impression appears, wet).
        stamper(None) takes it away"""
        if mark is None:
            self._stamper = None; return
        if height <= 1e-3:
            mark.progress = 1.0; mark.wet = 1.0
        self._stamper = (mark, float(height))

    # ------------------------------------------------------------ render
    def _paper_layers(self, p):
        rgb = p.rgb.copy()
        for m in p.marks:
            m.apply(rgb)
        return rgb, p.alpha

    def _warp(self, p, arrs):
        cx, cy, s, rot = p.pose()
        lift, dx, dy, drot = p.state
        LW, LH = p.LW, p.LH
        if s == 1 and rot == 0:
            ox, oy = int(round(p.X0 + dx)), int(round(p.Y0 + dy))
            return (oy, ox), arrs
        th = np.deg2rad(rot); c, si = np.cos(th), np.sin(th)
        corners = np.array([[-LW / 2, -LH / 2], [LW / 2, -LH / 2], [LW / 2, LH / 2], [-LW / 2, LH / 2]]) * s
        Pc = np.stack([cx + corners[:, 0] * c + corners[:, 1] * si, cy - corners[:, 0] * si + corners[:, 1] * c], 1)
        bx0, by0 = int(np.floor(Pc[:, 0].min())) - 2, int(np.floor(Pc[:, 1].min())) - 2
        bx1, by1 = int(np.ceil(Pc[:, 0].max())) + 2, int(np.ceil(Pc[:, 1].max())) + 2
        a, b = c / s, -si / s
        d_, e = si / s, c / s
        cc = LW / 2 + a * (bx0 - cx) + b * (by0 - cy)
        f = LH / 2 + d_ * (bx0 - cx) + e * (by0 - cy)
        out = []
        for arr in arrs:
            chans = [arr[..., k] for k in range(arr.shape[2])] if arr.ndim == 3 else [arr]
            ws = [np.asarray(Image.fromarray(np.ascontiguousarray(ch_, np.float32), 'F').transform(
                (bx1 - bx0, by1 - by0), Image.AFFINE, (a, b, cc, d_, e, f), resample=Image.BILINEAR), np.float32) for ch_ in chans]
            out.append(np.stack(ws, -1) if arr.ndim == 3 else ws[0])
        return (by0, bx0), out

    @staticmethod
    def _paste_box(H, W, oy, ox, h, w):
        y0, x0 = max(0, oy), max(0, ox)
        y1, x1 = min(H, oy + h), min(W, ox + w)
        if y1 <= y0 or x1 <= x0: return None
        return (slice(y0, y1), slice(x0, x1)), (slice(y0 - oy, y1 - oy), slice(x0 - ox, x1 - ox))

    def _shadow(self, I, A, oy, ox, lift):
        """the paper's shadow on whatever is under it: wide and soft while lifted, a contact line once down"""
        h, w = A.shape
        off = (5 + 34 * lift, 8 + 48 * lift)
        sig = 4.0 + 18 * lift
        pad = int(3 * sig + max(off) + 4)
        Ap = np.pad(A, pad)
        far = blur(shift(Ap, off[0], off[1]), sig) * (0.50 - 0.22 * lift)
        near = blur(shift(Ap, 1.5, 2.5), 1.6) * 0.42 * (1 - min(1.0, lift * 1.6))
        S = 1 - (1 - far) * (1 - near)
        hit = self._paste_box(self.H, self.W, oy - pad, ox - pad, h + 2 * pad, w + 2 * pad)
        if hit is None: return
        (cy_, cx_), (ly, lx) = hit
        I[cy_, cx_] *= 1 - S[ly, lx][..., None] * (1 - np.array(SHADOW, np.float32))

    def _render_pen(self, I, x, y, lift, angle, scale):
        H, W = self.H, self.W
        s = scale * (1 + 0.05 * lift)
        L, R = 664.0 * s, 19.0 * s
        th = np.deg2rad(angle)
        ax, ay = np.cos(th), np.sin(th)            # along the pen, tip -> end
        bx_, by_ = -ay, ax                          # across
        # --- shadow: the tip is at height z0, the end is held up (z grows along the pen); light from the upper left
        z0 = 2 + 60 * lift
        k = 0.15
        dvec = np.array([0.50, 0.80], np.float32)
        ex, ey = x + ax * L, y + ay * L
        sx0 = int(min(x, ex) - R - 30); sy0 = int(min(y, ey) - R - 30)
        sx1 = int(max(x, ex) + (z0 + k * L) * dvec[0] + R + 60); sy1 = int(max(y, ey) + (z0 + k * L) * dvec[1] + R + 60)
        sx0, sy0, sx1, sy1 = max(0, sx0), max(0, sy0), min(W, sx1), min(H, sy1)
        if sx1 > sx0 and sy1 > sy0:
            Y, X = np.mgrid[sy0:sy1, sx0:sx1].astype(np.float32)
            px, py = X - x, Y - y
            da = dvec[0] * ax + dvec[1] * ay
            db = dvec[0] * bx_ + dvec[1] * by_
            uq = (px * ax + py * ay - z0 * da) / (1 + k * da)
            vq = px * bx_ + py * by_ - (z0 + k * uq) * db
            rad = np.where(uq < 38 * s, 2.2 * s + (uq / (38 * s)) * 10 * s, np.where(uq < 164 * s, 16 * s, R))
            inside = np.clip(rad - np.abs(vq) + 0.5, 0, 1) * np.clip(uq + 0.5, 0, 1) * np.clip(L - uq + 0.5, 0, 1)
            near_w = np.exp(-np.clip(uq, 0, None) / (140 * s))
            sh = blur(inside, 2.0 + 4 * lift) * (0.46 - 0.12 * lift) * near_w + blur(inside, 9.0 + 8 * lift) * 0.30 * (1 - near_w)
            I[sy0:sy1, sx0:sx1] *= 1 - np.clip(sh, 0, 1)[..., None] * (1 - np.array(SHADOW, np.float32))
        # --- the pen itself, shaded as a cylinder
        bx0 = int(min(x, ex) - R - 4); by0 = int(min(y, ey) - R - 4)
        bx1 = int(max(x, ex) + R + 4); by1 = int(max(y, ey) + R + 4)
        bx0, by0, bx1, by1 = max(0, bx0), max(0, by0), min(W, bx1), min(H, by1)
        if bx1 <= bx0 or by1 <= by0: return
        Y, X = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
        px, py = X - x, Y - y
        u = (px * ax + py * ay) / s
        v = (px * bx_ + py * by_) / s
        r = np.full(u.shape, 19.0, np.float32)
        r = np.where(u < 38, 2.2 + np.clip(u - 2, 0, None) / 36 * 9.8, r)
        r = np.where((u >= 38) & (u < 161), 16.0, r)
        r = np.where(u >= 642, 18.5 * np.sqrt(np.clip(1 - ((u - 642) / 22) ** 2, 0, 1)), r)
        r = np.where((u >= 611) & (u < 642), 18.5, r)
        a = np.clip((r - np.abs(v)) * s + 0.5, 0, 1) * np.clip(u * s + 0.5, 0, 1) * np.clip((664 - u) * s + 0.5, 0, 1)
        if a.max() <= 0: return
        nv = np.clip(v / np.maximum(r, 1e-3), -1, 1)
        nz = np.sqrt(np.clip(1 - nv * nv, 0, 1))
        # light from the upper left, in pen space: its across-component
        Lc = np.array([-0.45, -0.62, 0.64], np.float32); Lc /= np.linalg.norm(Lc)
        lb = Lc[0] * bx_ + Lc[1] * by_
        ndl = np.clip(nv * lb + nz * Lc[2], 0, 1)
        Hh = Lc + np.array([0, 0, 1], np.float32); Hh /= np.linalg.norm(Hh)
        hb = Hh[0] * bx_ + Hh[1] * by_
        ndh = np.clip(nv * hb + nz * Hh[2], 0, 1)
        col = np.zeros(u.shape + (3,), np.float32)
        # chrome: an environment of a bright window band and a dark band
        env = 0.50 + 0.48 * np.exp(-((nv - lb * 0.75) / 0.16) ** 2) - 0.30 * np.exp(-((nv + 0.35) / 0.22) ** 2) - 0.25 * (1 - nz) ** 2
        chrome = np.clip(env, 0.05, 1.0)[..., None] * np.array([0.92, 0.93, 0.95], np.float32)
        lac = np.array([0.74, 0.05, 0.07], np.float32)
        lacq = lac * (0.30 + 0.75 * ndl)[..., None] + (0.55 * ndh ** 60)[..., None] \
            + (0.42 * np.exp(-((nv - lb * 0.62) / 0.07) ** 2))[..., None] * np.array([1.0, 0.92, 0.9], np.float32)
        rub = np.array([0.075, 0.075, 0.085], np.float32) * (0.5 + 0.9 * ndl)[..., None] + (0.10 * ndh ** 10)[..., None]
        ridge = np.abs(((u - 48) % 8) - 4) < 1.1
        rub = np.where(((u >= 46) & (u < 156) & ridge)[..., None], rub * 0.35, rub)
        rub = np.where(((u >= 46) & (u < 156) & (np.abs(((u - 50.2) % 8) - 4) < 0.6))[..., None], rub + 0.05, rub)
        ball = np.array([0.24, 0.24, 0.26], np.float32) * (0.5 + 0.6 * ndl)[..., None]
        col = np.where((u < 3)[..., None], ball, col)
        col = np.where(((u >= 3) & (u < 38))[..., None], chrome * 0.95, col)
        col = np.where(((u >= 38) & (u < 161))[..., None], rub, col)
        col = np.where(((u >= 161) & (u < 171))[..., None], chrome, col)
        col = np.where(((u >= 171) & (u < 603))[..., None], lacq, col)
        col = np.where(((u >= 603) & (u < 611))[..., None], chrome, col)
        col = np.where((u >= 611)[..., None], lacq, col)
        # the clip: a chrome strip lying on top of the barrel, its shadow beside it, a rivet at its root
        clip_m = np.clip((v + 8.5) * s + 0.5, 0, 1) * np.clip((2 - v) * s + 0.5, 0, 1) * np.clip((u - 482) * s + 0.5, 0, 1) * np.clip((656 - u) * s + 0.5, 0, 1)
        clip_sh = np.clip((v - 2) * s + 0.5, 0, 1) * np.clip((6.5 - v) * s + 0.5, 0, 1) * (u > 486) * (u < 654)
        col *= (1 - 0.45 * clip_sh)[..., None]
        cenv = (0.62 + 0.36 * np.exp(-((v + 5.5) / 1.6) ** 2) - 0.25 * np.exp(-((v - 0.8) / 1.2) ** 2))
        col = col * (1 - clip_m[..., None]) + (np.clip(cenv, 0, 1)[..., None] * np.array([0.9, 0.91, 0.93], np.float32)) * clip_m[..., None]
        rv = np.hypot(u - 486, v + 3.2)
        rivet = np.clip((4.6 - rv) * s + 0.5, 0, 1)
        col = col * (1 - rivet[..., None]) + (0.55 + 0.4 * np.clip(-(u - 486 + v + 3.2) / 6, -1, 1))[..., None] * np.array([0.92, 0.92, 0.94], np.float32) * rivet[..., None]
        # a soft dark rim at the silhouette
        rim = 1 - 0.35 * (1 - nz) ** 3
        col *= rim[..., None]
        I[by0:by1, bx0:bx1] = I[by0:by1, bx0:bx1] * (1 - a[..., None]) + col * a[..., None]

    def _render_stamper(self, I, mark, height):
        p = mark.paper
        gm = mark.geom
        cx, cy = p.to_canvas(gm['cx'], gm['cy'])
        rot = gm['rot'] + p.pose()[3]
        s = 1 + 0.10 * height
        bw, bh = (gm['w'] + 22) * s, (gm['h'] + 22) * s
        pad = int(40 + 60 * height)
        size = int(max(bw, bh) + 2 * pad)
        ss = 2
        # shadow of the block on the paper
        th = np.deg2rad(rot)
        def rr_mask(w_, h_, r_, cx_, cy_):
            im = Image.new('L', (size * ss, size * ss), 0)
            ImageDraw.Draw(im).rounded_rectangle(((cx_ - w_ / 2) * ss, (cy_ - h_ / 2) * ss, (cx_ + w_ / 2) * ss, (cy_ + h_ / 2) * ss), radius=r_ * ss, fill=255)
            return np.asarray(im.rotate(np.rad2deg(th), resample=Image.BICUBIC).resize((size, size), Image.BOX), np.float32) / 255
        c0 = size / 2
        blk = rr_mask(bw, bh, 9 * s, c0, c0)
        oy, ox = int(round(cy - c0)), int(round(cx - c0))
        off = (4 + 46 * height, 6 + 64 * height)
        sig = 3 + 16 * height
        SP = int(3 * sig + max(off) + 4)
        Ap = np.pad(blk, SP)
        S = blur(shift(Ap, off[0], off[1]), sig) * (0.55 - 0.25 * height) + blur(shift(Ap, 1, 2), 1.5) * 0.4 * (height < 0.05)
        hit = self._paste_box(self.H, self.W, oy - SP, ox - SP, size + 2 * SP, size + 2 * SP)
        if hit is not None:
            (cy_, cx_), (ly, lx) = hit
            I[cy_, cx_] *= 1 - np.clip(S[ly, lx], 0, 1)[..., None] * (1 - np.array(SHADOW, np.float32))
        # the block: varnished beech, grain along its length, bevelled edges; a turned walnut knob in the middle
        Y, X = np.mgrid[0:size, 0:size].astype(np.float32)
        u = (X - c0) * np.cos(th) - (Y - c0) * np.sin(th)
        v = (X - c0) * np.sin(th) + (Y - c0) * np.cos(th)
        # long grain: fine variation across the block, slow along it, a little warp
        gr = noise2d(220, 14, 2.2, 3, self.seed + 5)
        warp = noise2d(40, 40, 14, 2, self.seed + 6) - 0.5
        vv = (v / bh * 0.5 + 0.5) * 219 + 9 * _sample(warp, (v / bh * 0.5 + 0.5) * 39, (u / bw * 0.5 + 0.5) * 39)
        grain = _sample(gr, vv, (u / bw * 0.5 + 0.5) * 13)
        wood = np.array([0.70, 0.49, 0.29], np.float32) * (0.86 + 0.24 * smoothstep(0.3, 0.8, grain))[..., None]
        bv = blur(blk, 3.0 * s)
        gy, gx = np.gradient(bv)
        lit = np.clip(-(gx * -0.55 + gy * -0.83) * 6.0, -1, 1)
        wood = wood * (1 + 0.45 * lit)[..., None] * (0.86 + 0.14 * np.clip(bv * 1.4, 0, 1))[..., None]
        # a lathe-turned knob: domed, varnished, with turning rings and a darker collar where it meets the block
        rk = min(bh * 0.40, 34 * s)
        rho = np.hypot(u, v) / rk
        knob = np.clip((1 - rho) * rk + 0.5, 0, 1)
        nzk = np.sqrt(np.clip(1 - (rho * 0.92) ** 2, 0, 1))
        Lk = np.array([-0.45, -0.62, 0.64], np.float32); Lk /= np.linalg.norm(Lk)
        nxk, nyk = (X - c0) / rk * 0.92, (Y - c0) / rk * 0.92
        dk = np.clip(nxk * Lk[0] + nyk * Lk[1] + nzk * Lk[2], 0, 1)
        Hk = (Lk + np.array([0, 0, 1], np.float32)); Hk /= np.linalg.norm(Hk)
        sk = np.clip(nxk * Hk[0] + nyk * Hk[1] + nzk * Hk[2], 0, 1) ** 30
        rings = 1 - 0.10 * (np.cos(rho * 9 * np.pi) > 0.6) - 0.22 * np.exp(-((rho - 0.86) / 0.05) ** 2)
        kcol = np.array([0.58, 0.35, 0.18], np.float32) * ((0.40 + 0.75 * dk) * rings)[..., None] + (0.45 * sk)[..., None]
        ksh = blur(shift(knob, 6 * s, 9 * s), 4 * s) * 0.45
        wood *= (1 - ksh)[..., None]
        col = wood * (1 - knob[..., None]) + kcol * knob[..., None]
        hit = self._paste_box(self.H, self.W, oy, ox, size, size)
        if hit is None: return
        (cy_, cx_), (ly, lx) = hit
        a = blk[ly, lx][..., None]
        I[cy_, cx_] = I[cy_, cx_] * (1 - a) + col[ly, lx] * a

    def render(self):
        I = self.bg.copy()
        for p in self.items:
            if p.state is None: continue
            rgb, A = self._paper_layers(p)
            (oy, ox), (rgb_w, A_w) = self._warp(p, [rgb * p.alpha[..., None], A])
            self._shadow(I, A_w, oy, ox, p.state[0])
            h, w = A_w.shape
            hit = self._paste_box(self.H, self.W, oy, ox, h, w)
            if hit is None: continue
            (cy_, cx_), (ly, lx) = hit
            a = A_w[ly, lx][..., None]
            I[cy_, cx_] = I[cy_, cx_] * (1 - a) + rgb_w[ly, lx]
        if self._stamper is not None:
            self._render_stamper(I, *self._stamper)
        if self._pen is not None:
            self._render_pen(I, *self._pen)
        return I

    def composite(self):
        I = self.render() * self._postfx()
        return Image.fromarray((np.clip(I, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        if not self.keep_stages: return
        im = self.composite()
        if self.stages_dir:
            os.makedirs(self.stages_dir, exist_ok=True)
            im.save(f'{self.stages_dir}/{self._n_stages:03d}_{name}.png', compress_level=1)
        else:
            self.stages.append((name, im))
        self._n_stages += 1

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f'{sd}/{i:03d}_{name}.png', compress_level=1)
            img.save(f'{sd}/{self._n_stages:03d}_final.png', compress_level=1)
        return img
