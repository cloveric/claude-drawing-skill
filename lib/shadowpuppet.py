"""shadowpuppet — 皮影戏 / Shadow Puppetry: dyed-leather puppets pressed to a lamp-lit screen (numpy + Pillow only).

A shadow-play stage seen from the audience. Behind a cloth screen an oil lamp burns; in front of it stands a carved
wooden proscenium with a lacquered name plaque and red paper lanterns. Everything seen on the screen is lamp light
that came through it:

  screen      the lamp's light through the cloth: palest and brightest round the hot spot behind the middle, deeper
              amber toward the rim, with thread slubs, a faint fold or two and a vignette. `lamp(level, radius,
              flicker)` dims it, shrinks it to a small glow (the lamp being lit) or makes it flicker.
  leather     a puppet piece is scraped, oiled donkey hide: translucent and dyed with transparent colour. A `Leather`
              keeps coverage and an optical density per channel, so what reaches the eye is the lamp light times
              exp(-density): vermilion, teal, ochre and green glow, black dye is nearly opaque, and where two pieces
              overlap the densities add and it darkens, as with the real thing. Pieces are cut (`fill`), dyed in
              fields (`dye`), inked along every cut edge (`edge`, `contour`) and punched with the hollow patterns of
              the craft (`pattern`: dots, rings, plum blossoms, coins, fish scales, cloud heads, lattice, ice
              cracks, stripes; `carve` cuts a line). The hide's thickness varies, so no dye is flat.
  puppets     a `Puppet` is a tree of pieces joined by thread knots, each with a pivot and an angle, so a pose is a
              dict of joint angles (degrees counter-clockwise as seen with the figure facing right; a hanging limb
              at +90 points forward). `figure()` builds the classic figure: a profile head with a hollow-carved
              face (one long eye, a long brow) or a solid face with the features cut out, a helmet with pheasant
              plumes or a crown with pompoms, a cloud collar, robe, sleeves with cuffs, hands, trousers and
              thick-soled boots. Control rods are tied to the collar and the hands and run down past the screen.
  distance    every puppet has a distance from the screen `d` (0 = pressed flat). Lifted off the cloth its image
              grows a little and blurs, and because the lamp has two wicks it splits into two offset shadows: the
              soft double edge of a figure that is not quite pressed. Pieces can lift on their own (`away`). Rods
              slant back toward the puppeteers, so they are sharp where they are tied on and soft lower down.
  props       the same leather: `gate()` (a pailou archway with a lattice net and a round eye), `ball()`,
              `border()` (the ornamental floor band the puppets stand on), `nameplate()` (a small hanging plaque).
  front       `proscenium()`: a dark lacquered lintel with carved key-fret panels and a red plaque with gilt
              characters, an openwork valance and corner brackets the screen glows through, pillars and a sill, all
              lit by the light the screen spills onto them. `lantern()` hangs red paper lanterns lit from inside,
              with tassels and a warm halo. Both have poses for the draw-on (the lintel drops in, lanterns swing).

    import sys; sys.path.insert(0, 'lib')
    from shadowpuppet import ShadowPuppet
    sp = ShadowPuppet(1920, 1080, seed=3)
    sp.screen(); sp.proscenium('蹴鞠')
    sp.lantern(200); sp.lantern(1720)
    sp.place(sp.border())
    hero = sp.figure(robe='red', headdress='plume')
    hero.rod('torso', (4, -136)); hero.rod('hand_f', (0, 16), lean=-60)
    hero.pose(arm_f=150, fore_f=40, thigh_f=70, shin_f=-80)
    sp.place(hero, x=700, y=640); hero.ground(932)
    sp.save('puppet.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, spline, noise2d, smoothstep

# ---------------------------------------------------------------- palette
SCREEN = (1.00, 0.75, 0.37)       # lamp light through the cloth at the hot spot
SCREEN_EDGE = (1.00, 0.44, 0.13)  # ... toward the rim
HIDE = (0.97, 0.87, 0.68)         # scraped, oiled donkey hide (transmittance of undyed leather)
DYES = {                          # transmittance of the dye alone (multiplied with the hide)
    'plain': (1.0, 1.0, 1.0),
    'red': (1.0, 0.20, 0.10),     # vermilion
    'crimson': (0.86, 0.10, 0.12),
    'teal': (0.10, 0.64, 0.78),
    'green': (0.40, 0.78, 0.22),
    'ochre': (1.0, 0.72, 0.22),
    'yellow': (1.0, 0.92, 0.40),
    'blue': (0.22, 0.42, 0.95),
    'brown': (0.62, 0.34, 0.16),
    'pink': (1.0, 0.66, 0.56),
    'black': (0.10, 0.08, 0.065),
}
WOOD = (0.17, 0.075, 0.045)       # dark lacquered wood
LACQUER = (0.52, 0.045, 0.03)     # plaque red
GOLD = (0.95, 0.72, 0.32)
SPILL = (1.0, 0.58, 0.26)         # light the screen throws onto the frame
ROD = (0.86, 0.88, 0.90)          # absorbance of a control rod
LAMPS = (((0.44, 0.60), 0.66), ((0.60, 0.54), 0.34))   # two wicks: foot point on the screen (fraction of W, H), share

_MA = '/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/'
_FONT_TABLE = {   # (glob, face index); first hit wins -- macOS, Linux, Windows. Override: $INKPAINT_FONT_SHADOWPUPPET_<KIND>
    'plaque': [(_MA + 'WeibeiSC-Bold.otf', 0), (_MA + 'Libian.ttc', 0), (_MA + 'Kaiti.ttc', 0),
               ('/System/Library/Fonts/Supplemental/Songti.ttc', 1), ('/System/Library/Fonts/STHeiti Medium.ttc', 0),
               ('/usr/share/fonts/**/NotoSerifCJK*Black*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSerifCJK*Bold*.tt[cf]', 0),
               ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/STXINWEI.TTF', 0),
               ('C:/Windows/Fonts/simkai.ttf', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0)],
}
_FONT_TABLE['label'] = _FONT_TABLE['plaque']
_font_cache = {}


def font_path(kind='plaque'):
    """(path, index) of the CJK font for `kind` ('plaque' / 'label'), or None"""
    if kind in _font_cache: return _font_cache[kind]
    env = os.environ.get('INKPAINT_FONT_SHADOWPUPPET_' + kind.upper())
    hit = (env, 0) if env and os.path.exists(env) else None
    if hit is None:
        for pat, idx in _FONT_TABLE[kind]:
            fs = sorted(glob.glob(pat, recursive=True))
            if fs: hit = (fs[0], idx); break
    if hit is None:
        from core import cjk_font
        p = cjk_font(); hit = (p, 0) if p else None
    _font_cache[kind] = hit
    return hit


def _font(kind, size):
    hit = font_path(kind)
    if hit:
        try: return ImageFont.truetype(hit[0], int(round(size)), index=hit[1])
        except OSError: pass
    return ImageFont.load_default(int(round(size)))


def _rgb(c):
    return np.array(DYES[c] if isinstance(c, str) else c, np.float32)


def _dens(dye):
    """optical density (per channel) of hide dyed with `dye`"""
    return (-np.log(np.clip(np.array(HIDE, np.float32) * _rgb(dye), 1e-3, 1.0))).astype(np.float32)


def _loop(pts, per=6):
    """closed Catmull-Rom loop through pts"""
    P = np.asarray(pts, np.float32); n = len(P); out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out, np.float32)


def _grow(m, r):
    """dilate a float mask by r px (alternating square / cross steps, so roughly round)"""
    out = m.astype(np.float32)
    for i in range(int(round(r))):
        p = np.pad(out, 1, mode='edge')
        if i % 2 == 0:
            a = np.maximum(np.maximum(p[1:-1, :-2], p[1:-1, 2:]), out)
            q = np.pad(a, ((1, 1), (0, 0)), mode='edge')
            out = np.maximum(np.maximum(q[:-2], q[2:]), a)
        else:
            out = np.maximum.reduce([out, p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]])
    return out


def _shrink(m, r):
    return 1 - _grow(1 - m, r)


def _hash(i, j, seed):
    return np.mod(np.sin(i * 127.1 + j * 311.7 + seed * 74.7) * 43758.5453, 1.0)


def _hex(u, v, S):
    """offset to the nearest centre of a hexagonal lattice with spacing S"""
    rh = S * 0.8660254
    j0 = np.floor(v / rh)
    best = bu = bv = None
    for dj in (0, 1):
        jj = j0 + dj
        off = np.mod(jj, 2) * S / 2
        i = np.round((u - off) / S)
        du, dv = u - (i * S + off), v - jj * rh
        d2 = du * du + dv * dv
        if best is None: best, bu, bv = d2, du, dv
        else:
            m = d2 < best
            best = np.where(m, d2, best); bu = np.where(m, du, bu); bv = np.where(m, dv, bv)
    return bu, bv


def _scales(u, v, S, bar):
    """fish-scale armour: rows of overlapping discs, the upper row on top; sd > 0 inside a hole"""
    R, rh = 0.5 * S, 0.36 * S
    j0 = np.floor(v / rh)
    ds = []
    for dj in (-1, 0, 1, 2):
        jj = j0 + dj
        off = np.mod(jj, 2) * S / 2
        i = np.round((u - off) / S)
        ds.append(np.hypot(u - (i * S + off), v - jj * rh))
    ds = np.stack(ds)
    inside = ds < R
    own = np.argmax(inside, 0)
    d_own = np.take_along_axis(ds, own[None], 0)[0]
    rows = np.arange(len(ds))[:, None, None]
    cover = np.where(rows < own[None], ds - R, 1e9).min(0)
    sd = np.minimum(R - d_own, cover) - bar / 2
    return np.where(inside.any(0), sd, -1.0)


def _cloud(u, v, S):
    """ruyi cloud heads: three lobes with a leather curl in each"""
    du, dv = _hex(u, v, S)
    sd = -1e9
    for x, y, r in ((-0.17, 0.05, 0.12), (0.0, -0.05, 0.16), (0.17, 0.05, 0.12)):
        sd = np.maximum(sd, r * S - np.hypot(du - x * S, dv - y * S))
    sd = np.minimum(sd, 0.13 * S - dv)
    curl = 1e9
    for x, y, r in ((-0.15, 0.07, 0.04), (0.0, -0.02, 0.055), (0.15, 0.07, 0.04)):
        curl = np.minimum(curl, np.hypot(du - x * S, dv - y * S) - r * S)
    return np.minimum(sd, curl)


def _ice(u, v, S, bar, seed):
    """ice-crack lattice (jittered Voronoi cells)"""
    ci, cj = np.floor(u / S), np.floor(v / S)
    F1 = np.full(u.shape, 1e9, np.float32); F2 = F1.copy()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            i, j = ci + di, cj + dj
            px = (i + 0.15 + 0.7 * _hash(i, j, seed)) * S
            py = (j + 0.15 + 0.7 * _hash(i, j, seed + 17)) * S
            d = np.hypot(u - px, v - py)
            F2 = np.where(d < F1, F1, np.minimum(F2, d)); F1 = np.minimum(F1, d)
    return (F2 - F1) / 2 - bar / 2


def meander(x0, x1, y0, y1, unit=None, gap=0.0):
    """key-fret (回纹) polylines filling the strip [x0, x1] x [y0, y1]: one hook per unit plus a baseline"""
    h = y1 - y0; u = unit or h
    n = max(1, int((x1 - x0) // u))
    xs = x0 + ((x1 - x0) - n * u) / 2
    key = [(0.0, 1.0), (0.0, 0.0), (0.84, 0.0), (0.84, 0.70), (0.30, 0.70), (0.30, 0.34), (0.58, 0.34)]
    out = []
    for i in range(n):
        a = xs + i * u + gap
        out.append([(a + px * (u - 2 * gap), y0 + py * h) for px, py in key])
    out.append([(xs, y1), (xs + n * u, y1)])
    return out


# ================================================================ one piece of leather
_PAD = 6


class Leather:
    """One piece of carved, dyed leather in its own frame. Coordinates are design units (multiplied by `scale` to
    pixels); the pivot of the piece is the origin. Rasterised `ss` times finer and box-filtered at the end."""

    def __init__(self, x0, y0, x1, y1, scale=1.0, ss=3, seed=0):
        k = float(scale)
        self.k, self.ss, self.seed = k, int(ss), int(seed)
        self.x0 = int(np.floor(x0 * k)) - _PAD
        self.y0 = int(np.floor(y0 * k)) - _PAD
        self.w = int(np.ceil(x1 * k)) + _PAD - self.x0
        self.h = int(np.ceil(y1 * k)) + _PAD - self.y0
        H, W = self.h * self.ss, self.w * self.ss
        self.A = np.zeros((H, W), np.float32)        # coverage
        self.D = np.zeros((H, W, 3), np.float32)     # optical density where covered
        self._grid = None

    # ---------------------------------------------------------- geometry
    def _px(self, pts):
        P = np.asarray(pts, np.float64).reshape(-1, 2)
        return [((x * self.k - self.x0) * self.ss - 0.5, (y * self.k - self.y0) * self.ss - 0.5) for x, y in P]

    def grid(self):
        """design-unit coordinates (X, Y) of every fine pixel centre"""
        if self._grid is None:
            H, W = self.A.shape
            xs = (((np.arange(W) + 0.5) / self.ss + self.x0) / self.k).astype(np.float32)
            ys = (((np.arange(H) + 0.5) / self.ss + self.y0) / self.k).astype(np.float32)
            self._grid = np.meshgrid(xs, ys)
        return self._grid

    def _aa(self, sd):
        return np.clip(0.5 + sd * self.k * self.ss, 0, 1).astype(np.float32)

    def px(self, d):
        """design units -> fine pixels"""
        return d * self.k * self.ss

    def poly(self, pts):
        H, W = self.A.shape
        im = Image.new('L', (W, H), 0)
        ImageDraw.Draw(im).polygon(self._px(pts), fill=255)
        return np.asarray(im, np.float32) / 255

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        ry = rx if ry is None else ry
        X, Y = self.grid()
        t = np.deg2rad(rot); c, s = np.cos(t), np.sin(t)
        u = (X - cx) * c + (Y - cy) * s; v = -(X - cx) * s + (Y - cy) * c
        return self._aa((1 - np.sqrt((u / rx) ** 2 + (v / ry) ** 2)) * min(rx, ry))

    def ring(self, cx, cy, r0, r1):
        X, Y = self.grid()
        d = np.hypot(X - cx, Y - cy)
        return self._aa(np.minimum(r1 - d, d - r0))

    def below(self, y):
        return self._aa(self.grid()[1] - y)

    def above(self, y):
        return self._aa(y - self.grid()[1])

    def right_of(self, x):
        return self._aa(self.grid()[0] - x)

    def left_of(self, x):
        return self._aa(x - self.grid()[0])

    def stroke(self, pts, width):
        """a round-capped polyline mask"""
        H, W = self.A.shape
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        P = self._px(pts); wpx = max(1, int(round(self.px(width))))
        if len(P) > 1: d.line(P, fill=255, width=wpx, joint='curve')
        r = wpx / 2
        for (x, y) in (P[0], P[-1]): d.ellipse([x - r, y - r, x + r, y + r], fill=255)
        return np.asarray(im, np.float32) / 255

    @staticmethod
    def ribbon(pts, w0, w1=None):
        """outline polygon of a band along pts whose width runs from w0 to w1"""
        P = np.asarray(pts, np.float32)
        w = np.linspace(w0, w0 if w1 is None else w1, len(P)).astype(np.float32)
        d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        return np.vstack([P + nrm * w[:, None] / 2, (P - nrm * w[:, None] / 2)[::-1]])

    def text(self, s, x, y, size, kind='label', vertical=False, spacing=1.06):
        H, W = self.A.shape
        im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
        f = _font(kind, self.px(size))
        if vertical:
            n = len(s)
            for i, ch in enumerate(s):
                d.text(self._px([(x, y + (i - (n - 1) / 2) * size * spacing)])[0], ch, font=f, fill=255, anchor='mm')
        else:
            d.text(self._px([(x, y)])[0], s, font=f, fill=255, anchor='mm')
        return np.asarray(im, np.float32) / 255

    def mask(self, shape):
        if isinstance(shape, np.ndarray) and shape.shape == self.A.shape: return shape.astype(np.float32)
        return self.poly(shape)

    def inset(self, shape, width):
        return _shrink(self.mask(shape), self.px(width))

    def grow(self, shape, width):
        return _grow(self.mask(shape), self.px(width))

    # ---------------------------------------------------------- cutting and dyeing
    def fill(self, shape, dye='plain'):
        """add leather (a cut piece or a strip glued on) dyed `dye`; returns the mask"""
        m = self.mask(shape)
        self.D += m[..., None] * (_dens(dye) - self.D)
        self.A = np.maximum(self.A, m)
        return m

    def dye(self, shape, dye):
        """recolour the leather already there"""
        m = self.mask(shape) * np.clip(self.A * 3, 0, 1)
        self.D += m[..., None] * (_dens(dye) - self.D)
        return m

    def edge(self, width=2.0, dye='black', region=None):
        """ink the cut edge of the piece (or of `region` within it)"""
        R = self.A if region is None else self.mask(region) * self.A
        band = np.clip(R - _shrink(R, self.px(width)), 0, 1)
        self.D += band[..., None] * (_dens(dye) - self.D)
        return band

    contour = lambda self, region, width=1.4, dye='black': self.edge(width, dye, region)

    def punch(self, shape, rim=0.8, dye='black'):
        """cut a hole; the cut edge round it is inked `rim` wide"""
        m = self.mask(shape)
        if rim > 0:
            ring = np.clip(_grow(m, self.px(rim)) - m, 0, 1) * self.A
            self.D += ring[..., None] * (_dens(dye) - self.D)
        self.A = self.A * (1 - m)
        return m

    def line(self, pts, width=1.6, dye='black'):
        """a strip of leather (an inked line that is part of the piece)"""
        return self.fill(self.stroke(pts, width), dye)

    def carve(self, pts, width=1.4, rim=0.0):
        """cut a thin line through"""
        return self.punch(self.stroke(pts, width), rim)

    def holes(self, kind, size, angle=0.0, origin=(0.0, 0.0), seed=0, **kw):
        """the hole mask of a hollow pattern over the whole piece (see `pattern`)"""
        X, Y = self.grid()
        t = np.deg2rad(angle); c, s = np.cos(t), np.sin(t)
        x, y = X - origin[0], Y - origin[1]
        u, v = x * c + y * s, -x * s + y * c
        S = float(size)
        if kind == 'dots':
            du, dv = _hex(u, v, S); sd = kw.get('r', 0.27) * S - np.hypot(du, dv)
        elif kind == 'rings':
            du, dv = _hex(u, v, S); d = np.hypot(du, dv)
            sd = np.minimum(kw.get('r', 0.34) * S - d, d - kw.get('pin', 0.13) * S)
        elif kind == 'flower':
            du, dv = _hex(u, v, S); n = kw.get('petals', 5)
            rp, rr = kw.get('r', 0.12) * S, kw.get('ring', 0.21) * S
            sd = -1e9
            for i in range(n):
                a = 2 * np.pi * i / n - np.pi / 2
                sd = np.maximum(sd, rp - np.hypot(du - rr * np.cos(a), dv - rr * np.sin(a)))
        elif kind == 'coins':
            du, dv = _hex(u, v, S); d = np.hypot(du, dv)
            sd = np.minimum(kw.get('r', 0.36) * S - d, np.maximum(np.abs(du), np.abs(dv)) - kw.get('square', 0.11) * S)
        elif kind == 'scales':
            sd = _scales(u, v, S, kw.get('bar', 0.12) * S)
        elif kind == 'cloud':
            sd = _cloud(u, v, S)
        elif kind == 'lattice':
            b = kw.get('bar', 0.2) * S
            fu = np.abs(np.mod(u, S) - S / 2); fv = np.abs(np.mod(v, S) - S / 2)
            sd = np.minimum(S / 2 - b / 2 - fu, S / 2 - b / 2 - fv)
        elif kind == 'stripes':
            b = kw.get('bar', 0.45) * S
            sd = S / 2 - b / 2 - np.abs(np.mod(u, S) - S / 2)
        elif kind == 'ice':
            sd = _ice(u, v, S, kw.get('bar', 0.13) * S, seed)
        else:
            raise ValueError(kind)
        return self._aa(sd)

    def pattern(self, region, kind, size, angle=0.0, margin=3.0, rim=0.7, origin=(0.0, 0.0), seed=0, **kw):
        """punch a hollow pattern inside `region`, keeping `margin` of solid leather along its border.
        kinds: dots, rings, flower (plum blossoms), coins, scales (fish-scale armour), cloud (ruyi heads),
        lattice, stripes, ice (ice-crack lattice)"""
        R = self.mask(region) * (self.A > 0.5)
        h = self.holes(kind, size, angle, origin, seed, **kw) * _shrink(R, self.px(margin))
        return self.punch(h, rim)

    def finish(self, mottle=0.24, blotch=0.16, fibre=0.07):
        """-> K (h, w, 3): the fraction of light each channel loses through the piece. The hide is scraped by hand,
        so its thickness (and so every dye's depth) varies: `mottle` at ~30 px, `blotch` at ~90 px, `fibre` fine"""
        H, W = self.A.shape
        n = noise2d(H, W, 30 * self.ss, 3, self.seed + 3)
        b = noise2d(H, W, 90 * self.ss, 2, self.seed + 5)
        f = noise2d(H, W, 3 * self.ss, 2, self.seed + 4)
        th = (1 + mottle * (2 * n - 1) + blotch * (2 * b - 1)) * (1 + fibre * (2 * f - 1))
        K = self.A[..., None] * (1 - np.exp(-self.D * th[..., None]))
        ss = self.ss
        return K.reshape(self.h, ss, self.w, ss, 3).mean((1, 3)).astype(np.float32)


# ================================================================ a jointed puppet
def _R(a):
    t = np.deg2rad(a); c, s = np.cos(t), np.sin(t)
    return np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])


def _T(x, y):
    return np.array([[1.0, 0.0, x], [0.0, 1.0, y], [0.0, 0.0, 1.0]])


class Puppet:
    """A tree of leather pieces. `pose(**angles)` sets joint angles in degrees, counter-clockwise as seen with the
    puppet facing right (a hanging limb at +90 points forward, a head at +10 looks up); `flip=True` faces it left.
    x, y place the root pivot on the canvas; d is the distance from the screen (0 = pressed flat, 1 = far)."""

    def __init__(self, sp, name='puppet', scale=1.0):
        self.sp, self.name, self.k = sp, name, float(scale)
        self.parts, self.order, self.angles = {}, [], {}
        self.x = self.y = 0.0
        self.rot, self.flip, self.d, self.alpha = 0.0, False, 0.0, 1.0
        self.away, self.rods, self.soles = {}, [], {}
        self.shown = False

    def add(self, name, leather, parent=None, joint=(0, 0), knot=True):
        K = leather.finish() if isinstance(leather, Leather) else leather
        img = Image.fromarray((np.clip(K, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')
        self.parts[name] = dict(img=img, x0=leather.x0, y0=leather.y0, parent=parent,
                                joint=(joint[0] * self.k, joint[1] * self.k), knot=knot and parent is not None)
        self.order.append(name)
        self.angles.setdefault(name, 0.0)
        return self

    def pose(self, **angles):
        for n, a in angles.items():
            if n not in self.parts: raise KeyError(f'{self.name} has no part {n!r}')
            self.angles[n] = float(a)
        return self

    def set(self, x=None, y=None, rot=None, d=None, flip=None, alpha=None, **angles):
        if x is not None: self.x = float(x)
        if y is not None: self.y = float(y)
        if rot is not None: self.rot = float(rot)
        if d is not None: self.d = float(d)
        if flip is not None: self.flip = bool(flip)
        if alpha is not None: self.alpha = float(alpha)
        return self.pose(**angles)

    def state(self):
        return dict(x=self.x, y=self.y, rot=self.rot, d=self.d, alpha=self.alpha, angles=dict(self.angles))

    def load(self, st):
        self.set(x=st['x'], y=st['y'], rot=st['rot'], d=st['d'], alpha=st['alpha'], **st['angles'])
        return self

    @staticmethod
    def tween(a, b, t):
        """a state between two `state()`s"""
        lerp = lambda p, q: p + (q - p) * t
        return dict(x=lerp(a['x'], b['x']), y=lerp(a['y'], b['y']), rot=lerp(a['rot'], b['rot']), d=lerp(a['d'], b['d']),
                    alpha=lerp(a['alpha'], b['alpha']), angles={n: lerp(a['angles'][n], b['angles'][n]) for n in a['angles']})

    def matrices(self):
        F = np.diag([-1.0 if self.flip else 1.0, 1.0, 1.0])
        M = {}
        for n in self.order:
            p = self.parts[n]
            if p['parent'] is None:
                M[n] = _T(self.x, self.y) @ F @ _R(self.rot + self.angles[n])
            else:
                M[n] = M[p['parent']] @ _T(*p['joint']) @ _R(self.angles[n])
        return M

    def point(self, part, pt=(0, 0), M=None):
        """canvas position of a point given in the part's design units"""
        M = (M or self.matrices())[part]
        v = M @ np.array([pt[0] * self.k, pt[1] * self.k, 1.0])
        return float(v[0]), float(v[1])

    def rod(self, part, pt=(0, 0), lean=0.0, width=3.2):
        """a control rod tied to `part` at `pt`, running down past the bottom of the screen, `lean` px sideways"""
        self.rods.append(dict(part=part, pt=pt, lean=float(lean), width=float(width)))
        return self

    def ground(self, y_floor, parts=None):
        """move the puppet up or down so the lowest sole of `parts` (default: all feet) rests on y_floor"""
        M = self.matrices()
        lows = [self.point(n, q, M)[1] for n in (parts or list(self.soles)) for q in self.soles[n]]
        if lows: self.y += y_floor - max(lows)
        return self


# ================================================================ hanging lantern
class Lantern:
    def __init__(self, sp, x, top, r=56, drop=70, tassel=True, lit=1.0, swing=0.0, seed=0):
        self.sp, self.x, self.top, self.r, self.drop = sp, float(x), float(top), float(r), float(drop)
        self.tassel, self.lit, self.swing, self.seed = tassel, float(lit), float(swing), seed
        self.shown = True
        self._cache = {}

    def set(self, lit=None, swing=None, shown=None):
        if lit is not None: self.lit = float(lit)
        if swing is not None: self.swing = float(swing)
        if shown is not None: self.shown = bool(shown)
        return self

    def _draw(self, lit):
        key = round(lit, 2)
        if key in self._cache: return self._cache[key]
        r, drop = self.r, self.drop
        ry, cap = 0.84 * r, 0.16 * r
        cy = drop + cap + ry
        tas = 1.75 * r if self.tassel else 0.0
        Hl = int(cy + ry + cap + 0.3 * r + tas + 10); Wl = int(2 * r + 30)
        hx = Wl / 2
        Y, X = np.mgrid[0:Hl, 0:Wl].astype(np.float32) + 0.5
        rgb = np.zeros((Hl, Wl, 3), np.float32); A = np.zeros((Hl, Wl), np.float32)

        def over(m, col):
            nonlocal rgb, A
            m = np.clip(m, 0, 1)
            rgb = rgb * (1 - m[..., None]) + np.asarray(col, np.float32) * m[..., None]
            A = np.maximum(A, m)

        def lines(segs, width):
            im = Image.new('L', (Wl * 2, Hl * 2), 0); d = ImageDraw.Draw(im)
            for seg in segs: d.line([(x * 2, y * 2) for x, y in seg], fill=255, width=max(1, int(round(width * 2))))
            return np.asarray(im, np.float32).reshape(Hl, 2, Wl, 2).mean((1, 3)) / 255

        # string
        over(lines([[(hx, 0), (hx, drop + 2)]], 2.2), (0.09, 0.05, 0.035))
        # body: paper over bamboo ribs, lit from inside
        u, v = (X - hx) / r, (Y - cy) / ry
        q = np.sqrt(u * u + v * v)
        body = np.clip((1 - q) * min(r, ry) + 0.5, 0, 1)
        sv = np.sqrt(np.clip(1 - v * v, 1e-4, 1))
        rib = np.zeros_like(q)
        for kk in range(11):
            ph = (kk + 0.5) * np.pi / 11 - np.pi / 2
            rib = np.maximum(rib, np.clip(1.25 - np.abs(X - (hx + r * sv * np.sin(ph))), 0, 1))
        paper = 1 + 0.05 * (noise2d(Hl, Wl, 6, 2, self.seed) - 0.5)
        gather = smoothstep(0.62, 0.98, np.abs(v))
        if lit > 0:
            core = np.exp(-((X - hx) ** 2 + (Y - (cy + 0.22 * ry)) ** 2) / (2 * (0.42 * r) ** 2))
            b = (0.42 + 0.62 * np.clip(1 - q * q, 0, 1) ** 0.7 + 0.55 * core) * paper * (1 - 0.35 * gather)
            deep, mid, hot = np.array([0.46, 0.035, 0.03]), np.array([0.93, 0.16, 0.06]), np.array([1.0, 0.66, 0.26])
            t1 = np.clip(b / 0.85, 0, 1)[..., None]; t2 = np.clip((b - 0.85) / 0.55, 0, 1)[..., None]
            col_lit = deep + (mid - deep) * t1 + (hot - mid) * t2
        else:
            col_lit = 0
        n_z = np.sqrt(np.clip(1 - q * q, 0, 1))
        dif = np.clip(0.55 * n_z - 0.35 * u * 0.6 - 0.45 * v * 0.6, 0, 1)
        col_off = np.array([0.30, 0.045, 0.035]) * (0.35 + 0.75 * dif)[..., None] * paper[..., None]
        col = col_off * (1 - lit) + col_lit * lit
        col = col * (1 - 0.55 * rib[..., None] * (0.6 + 0.4 * lit))
        over(body, col)
        # caps: black lacquer with a gilt band
        for y0 in (drop, cy + ry - 0.04 * r):
            cm = ((np.abs(X - hx) < 0.46 * r) & (Y >= y0) & (Y < y0 + cap)).astype(np.float32)
            capc = np.array([0.07, 0.04, 0.03]) + 0.05 * lit
            over(cm, capc)
            gm = ((np.abs(X - hx) < 0.46 * r) & (np.abs(Y - (y0 + cap * 0.5)) < 1.2)).astype(np.float32)
            over(gm, np.array(GOLD) * (0.55 + 0.35 * lit))
        # tassel: a gilt knot and a red silk fringe
        if self.tassel:
            ky = cy + ry + cap + 0.12 * r
            over(np.clip(0.11 * r - np.hypot(X - hx, Y - ky) + 0.5, 0, 1), np.array(GOLD) * (0.6 + 0.3 * lit))
            rng = np.random.default_rng(self.seed + 5)
            segs = []
            for i in range(28):
                s0 = rng.uniform(-0.12, 0.12) * r
                s1 = s0 * 2.4 + rng.uniform(-0.08, 0.08) * r
                L = tas * rng.uniform(0.82, 1.0)
                segs.append([(hx + s0, ky + 0.06 * r), (hx + (s0 + s1) / 2, ky + 0.5 * L), (hx + s1, ky + L)])
            fm = lines(segs, 1.3)
            tcol = np.array([0.50, 0.04, 0.035])[None, None, :] * (1 + 0.9 * lit * np.clip(1 - (Y - ky) / tas, 0, 1))[..., None]
            over(fm, tcol)
            band = ((np.abs(X - hx) < 0.17 * r) & (np.abs(Y - (ky + 0.22 * r)) < 0.05 * r)).astype(np.float32)
            over(band, np.array(GOLD) * (0.55 + 0.3 * lit))
        out = (rgb, A, (hx, cy))
        self._cache[key] = out
        return out


# ================================================================ the stage
class ShadowPuppet:
    DYES = DYES

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages = keep_stages              # False: stage() is free
        self.stages_dir = stages_dir                # set: stage() writes each snapshot at once (keeps memory low)
        self.stages, self._n_stages = [], 0
        self.box = (0, 0, W, H)                     # the screen opening
        self.hot = (0.5 * W, 0.56 * H)
        self.lamps = [((fx * W, fy * H), w) for (fx, fy), w in LAMPS]
        self.lamp_state = dict(level=1.0, radius=1.0, flicker=0.0)
        self.items, self.lanterns = [], []
        self._scr = None
        self._L = None
        self._prosc = None
        self._frame = None
        self.frame_pose = dict(dy=0.0, alpha=1.0)
        self._post = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ screen and lamp
    def screen(self, colour=SCREEN, edge=SCREEN_EDGE, hot=None, weave=1.0, folds=2):
        """the cloth screen lit from behind; hot = the point the lamp is behind (default just below the middle)"""
        if hot is not None: self.hot = (float(hot[0]), float(hot[1]))
        self._scr = dict(colour=np.array(colour, np.float32), edge=np.array(edge, np.float32), weave=weave, folds=folds)
        self._Lbase = None; self._L = None
        return self

    def lamp(self, level=1.0, radius=1.0, flicker=0.0):
        """lamp brightness 0..1, how far the glow has spread (0.15 = a small glow just lit, 1 = full) and a flicker
        (a small +- brightness change)"""
        st = dict(level=float(level), radius=float(radius), flicker=float(flicker))
        if st != self.lamp_state: self._L = None
        self.lamp_state = st
        return self

    def _screen_base(self):
        if self._Lbase is None:
            if self._scr is None: self.screen()
            H, W = self.H, self.W
            x0, y0, x1, y1 = self.box
            Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
            hx, hy = self.hot
            r2 = ((X - hx) / (0.47 * W)) ** 2 + ((Y - hy) / (0.64 * H)) ** 2
            rng = np.random.default_rng(self.seed + 7)
            sc = self._scr
            sx = np.asarray(Image.fromarray(rng.normal(0, 1, (H, max(2, W // 9))).astype(np.float32)).resize((W, H), Image.BILINEAR))
            sy = np.asarray(Image.fromarray(rng.normal(0, 1, (max(2, H // 9), W)).astype(np.float32)).resize((W, H), Image.BILINEAR))
            tex = 1 + sc['weave'] * (0.010 * sx + 0.010 * sy) + 0.05 * (noise2d(H, W, 300, 3, self.seed + 8) - 0.5)
            for i in range(sc['folds']):
                fx = x0 + (x1 - x0) * rng.uniform(0.18, 0.82)
                wob = fx + 6 * np.sin(Y / 140 + i)
                tex -= 0.022 * np.exp(-((X - wob) / 3.5) ** 2)
                tex += 0.010 * np.exp(-((X - wob - 6) / 5.0) ** 2)
            ins = (np.clip(X - x0 + 0.5, 0, 1) * np.clip(x1 - X + 0.5, 0, 1) * np.clip(Y - y0 + 0.5, 0, 1) * np.clip(y1 - Y + 0.5, 0, 1))
            self._Lbase = dict(r2=r2, tex=(tex * ins).astype(np.float32), X=X, Y=Y)
        return self._Lbase

    def _emission(self):
        if self._L is None:
            B = self._screen_base(); sc = self._scr; st = self.lamp_state
            rad = max(0.05, st['radius'])
            r2 = B['r2']
            if st['flicker']:
                hx, hy = self.hot
                dx, dy = 14 * st['flicker'], -8 * st['flicker']
                r2 = ((B['X'] - hx - dx) / (0.47 * self.W)) ** 2 + ((B['Y'] - hy - dy) / (0.64 * self.H)) ** 2
            fall = np.exp(-r2 / rad ** 2)
            b = st['level'] * (1 + 0.6 * st['flicker']) * (0.10 * min(1.0, rad) ** 3 + 0.95 * fall)
            t = (fall ** 0.65)[..., None]
            col = sc['edge'] + (sc['colour'] - sc['edge']) * t
            self._L = (col * (b * B['tex'])[..., None]).astype(np.float32)
        return self._L

    # ------------------------------------------------------------ leather, puppets and props
    def leather(self, x0, y0, x1, y1, scale=1.0, ss=3, seed=None):
        return Leather(x0, y0, x1, y1, scale, ss, self._seed() if seed is None else seed)

    def puppet(self, name='puppet', scale=1.0):
        return Puppet(self, name, scale)

    def prop(self, leather, name='prop'):
        """a one-piece prop (its pivot is the leather's origin)"""
        p = Puppet(self, name, leather.k)
        p.add(name, leather)
        return p

    def place(self, p, x=None, y=None, **kw):
        """put a puppet or prop on the screen (or update it); the first place() decides nothing about order:
        light through stacked leather multiplies, so any order looks the same"""
        p.set(x=x, y=y, **kw)
        p.shown = True
        if not any(it is p for it in self.items): self.items.append(p)
        return p

    def hide(self, p):
        p.shown = False

    def figure(self, **kw):
        """a jointed figure; see _figure() for the options"""
        return _figure(self, **kw)

    def ball(self, r=22, dye='ochre', scale=1.0, seed=None):
        """the leather ball (鞠): stitched panels cut as petals round a ring"""
        L = self.leather(-r - 2, -r - 2, r + 2, r + 2, scale, seed=seed)
        m = L.fill(L.ellipse(0, 0, r), dye)
        core = L.dye(L.ellipse(0, 0, 0.36 * r), 'red')
        for i in range(6):     # six stitched panels: a seam from the core to the rim, a lens-shaped cut in each panel
            a = 2 * np.pi * i / 6
            L.dye(L.stroke([(np.cos(a) * 0.36 * r, np.sin(a) * 0.36 * r), (np.cos(a) * r, np.sin(a) * r)], max(1.6, 0.09 * r)), 'black')
            b = a + np.pi / 6
            L.punch(L.ellipse(np.cos(b) * 0.66 * r, np.sin(b) * 0.66 * r, 0.20 * r, 0.085 * r, rot=-np.degrees(b)), 0.8)
        L.punch(L.ellipse(0, 0, 0.12 * r), 0.8)
        L.contour(core, max(1.2, 0.06 * r))
        L.edge(max(1.8, 0.08 * r))
        return self.prop(L, 'ball')

    def gate(self, w=280, h=560, net_h=250, eye=(0, -400), eye_r=44, post='red', beam='teal', roof='black',
             net='ochre', trim='red', scale=1.0, seed=None):
        """a pailou archway as a goal (球门): posts, a beam, a tiled roof with upturned eaves and ridge curls, and a
        lattice net (窗棂) with a round eye (风流眼). Pivot: the middle of the floor line."""
        hw = w / 2
        L = self.leather(-hw - 80, -h - 120, hw + 80, 4, scale, ss=2, seed=seed)
        # posts with stepped plinths
        for s in (-1, 1):
            x = s * hw
            pm = L.fill([(x - 12, -h + 4), (x + 12, -h + 4), (x + 12, 0), (x - 12, 0)], post)
            L.pattern(pm * L.below(-h + 40) * L.above(-50), 'coins', 25, angle=90, r=0.31, square=0.1, margin=3.5, origin=(x, 0))
            L.fill([(x - 18, -44), (x + 18, -44), (x + 21, -32), (x - 21, -32)], net)
            L.fill([(x - 24, -32), (x + 24, -32), (x + 28, 0), (x - 28, 0)], net)
        # the net: a lattice panel between the posts with a ringed eye
        ny0, ny1 = -h + 34, -h + 34 + net_h
        nm = L.fill([(-hw + 10, ny0), (hw - 10, ny0), (hw - 10, ny1), (-hw + 10, ny1)], net)
        ex, ey = eye
        holes = L.holes('lattice', 27, 45, origin=(ex, ey), bar=0.2) * L.inset(nm, 7) * (1 - L.ellipse(ex, ey, eye_r + 14))
        L.punch(holes, 0.8)
        L.fill(L.ring(ex, ey, eye_r - 1, eye_r + 12), trim)
        L.pattern(L.ring(ex, ey, eye_r + 1, eye_r + 11), 'dots', 7.5, r=0.22, margin=1.5, origin=(ex, ey))
        L.punch(L.ellipse(ex, ey, eye_r), 0)
        L.contour(nm, 2.4)
        # fringe of scallops under the net
        sc = 0
        for i in range(int((w - 20) // 24)):
            cx = -hw + 22 + i * 24
            sc = np.maximum(sc, L.ellipse(cx, ny1 + 2, 11, 13) * L.below(ny1 - 1))
        L.fill(sc, trim); L.pattern(sc, 'dots', 9, r=0.18, margin=2.5)
        # beam
        bm = L.fill([(-hw - 40, -h - 4), (hw + 40, -h - 4), (hw + 34, -h + 30), (-hw - 34, -h + 30)], beam)
        L.pattern(bm, 'coins', 26, r=0.37, square=0.1, margin=4, origin=(0, -h + 13))
        for s in (-1, 1):   # brackets under the beam
            L.fill(_loop([(s * (hw - 12), -h + 30), (s * (hw - 44), -h + 30), (s * (hw - 30), -h + 40), (s * (hw - 14), -h + 56)], 4), net)
        # tiled roof with upturned eaves
        e = hw + 64
        roof_pts = np.vstack([spline([(-e - 6, -h - 34), (-e + 18, -h - 12), (-hw, -h - 6), (hw, -h - 6), (e - 18, -h - 12), (e + 6, -h - 34)], 8),
                              spline([(e + 6, -h - 34), (e - 20, -h - 30), (hw - 16, -h - 70), (-hw + 16, -h - 70), (-e + 20, -h - 30), (-e - 6, -h - 34)], 8)])
        rm = L.fill(roof_pts, roof)
        L.pattern(rm * L.below(-h - 66) * L.above(-h - 12), 'stripes', 13, bar=0.5, margin=4)
        L.fill([(-hw + 10, -h - 82), (hw - 10, -h - 82), (hw - 6, -h - 66), (-hw + 6, -h - 66)], roof)
        for s in (-1, 1):   # ridge curls
            curl = spline([(s * (hw - 14), -h - 74), (s * (hw + 4), -h - 92), (s * (hw - 6), -h - 112), (s * (hw - 26), -h - 108), (s * (hw - 24), -h - 96)], 8)
            L.fill(L.ribbon(curl, 13, 6), roof)
            L.punch(L.ellipse(s * (hw - 7), -h - 99, 4.2), 0.6)
        jm = L.fill(L.ellipse(0, -h - 96, 13, 13), trim)
        L.fill(_loop([(0, -h - 132), (8, -h - 112), (0, -h - 104), (-8, -h - 112)], 5), net)
        L.pattern(jm, 'flower', 30, petals=5, r=0.1, ring=0.19, margin=1.5, origin=(0, -h - 96))
        L.edge(2.2)
        return self.prop(L, 'gate')

    def border(self, y0=None, y1=None, x0=None, x1=None, dye='teal', trim='red', unit=None, seed=None):
        """the ornamental floor band along the bottom of the screen: a dotted strip, a key-fret band, a dark rail.
        Built in canvas coordinates (place it at x=0, y=0; move x to slide it in)"""
        bx0, by0, bx1, by1 = self.box
        x0 = bx0 - 4 if x0 is None else x0; x1 = bx1 + 4 if x1 is None else x1
        y1 = by1 + 2 if y1 is None else y1; y0 = y1 - 70 if y0 is None else y0
        L = self.leather(x0, y0, x1, y1, 1.0, ss=2, seed=seed)
        h = y1 - y0
        top = L.fill([(x0, y0), (x1, y0), (x1, y0 + 0.2 * h), (x0, y0 + 0.2 * h)], trim)
        L.pattern(top, 'dots', 10, r=0.2, margin=3, origin=(0, y0 + 0.1 * h))
        mid = L.fill([(x0, y0 + 0.2 * h), (x1, y0 + 0.2 * h), (x1, y1 - 0.14 * h), (x0, y1 - 0.14 * h)], dye)
        L.fill([(x0, y1 - 0.14 * h), (x1, y1 - 0.14 * h), (x1, y1), (x0, y1)], 'black')
        my0, my1 = y0 + 0.2 * h + 7, y1 - 0.14 * h - 7
        for path in meander(x0 + 10, x1 - 10, my0, my1, unit or (my1 - my0) * 1.2):
            L.carve(path, 3.6)
        L.contour(top, 1.5); L.contour(mid, 1.5)
        L.edge(1.6)
        return self.prop(L, 'border')

    def nameplate(self, text, dye='red', size=30, string=60, seed=None):
        """a small vertical plaque on a thread: dark characters on pale hide in a dyed frame. Pivot: the top of the
        thread"""
        n = len(text); w = size + 22; h = n * size * 1.08 + 30
        L = self.leather(-w / 2 - 6, -2, w / 2 + 6, string + h + 26, 1.0, seed=seed)
        L.line([(0, 0), (0, string + 4)], 1.6)
        L.fill(_loop([(-9, string + 2), (0, string - 8), (9, string + 2), (0, string + 8)], 4), 'ochre')
        fr = L.fill([(-w / 2, string + 6), (w / 2, string + 6), (w / 2, string + 6 + h), (-w / 2, string + 6 + h)], dye)
        pane = L.dye([(-w / 2 + 7, string + 13), (w / 2 - 7, string + 13), (w / 2 - 7, string - 1 + h), (-w / 2 + 7, string - 1 + h)], 'plain')
        L.pattern(fr * (1 - L.grow(pane, 1)), 'dots', 7, r=0.2, margin=1.6)
        L.fill(L.text(text, 0, string + 6 + h / 2, size, 'label', vertical=True), 'black')
        L.contour(pane, 1.2)
        tip = string + 6 + h
        L.fill(_loop([(-8, tip), (8, tip), (0, tip + 18)], 4), 'ochre')
        L.edge(1.5)
        return self.prop(L, 'nameplate')

    # ------------------------------------------------------------ the front: proscenium and lanterns
    def proscenium(self, plaque='蹴鞠', top=150, valance=54, side=64, sill=80, bracket=170, plaque_w=420):
        """the carved frame: lintel with key-fret panels and the plaque, an openwork valance and corner brackets,
        pillars and a sill. Sets the screen opening to the space inside it"""
        self.box = (side, top, self.W - side, self.H - sill)
        self._prosc = dict(plaque=plaque, top=top, valance=valance, side=side, sill=sill, bracket=bracket, plaque_w=plaque_w)
        self._Lbase = self._L = self._frame = None
        return self

    def frame(self, dy=0.0, alpha=1.0):
        """pose of the lintel group (lintel, plaque, valance, brackets) for the draw-on: dy < 0 lifts it out of view"""
        self.frame_pose = dict(dy=float(dy), alpha=float(alpha))
        return self

    def lantern(self, x, top=None, r=56, drop=70, tassel=True, lit=1.0, swing=0.0):
        """a red paper lantern hanging from the lintel at x (top: where its string is tied)"""
        top = (self._prosc['top'] if self._prosc else 0) if top is None else top
        ln = Lantern(self, x, top, r, drop, tassel, lit, swing, self._seed())
        self.lanterns.append(ln)
        return ln

    def _build_frame(self):
        P = self._prosc; H, W = self.H, self.W
        top, val, side, sill, br, pw = P['top'], P['valance'], P['side'], P['sill'], P['bracket'], P['plaque_w']
        cx = W / 2
        rng = np.random.default_rng(self.seed + 31)
        Y, X = np.mgrid[0:H, 0:W].astype(np.float32)

        def canvas():
            im = Image.new('L', (W, H), 0); return im, ImageDraw.Draw(im)

        def arr(im):
            return np.asarray(im, np.float32) / 255

        Ht = np.zeros((H, W), np.float32)     # relief height, px
        gild = np.zeros((H, W), np.float32)
        red = np.zeros((H, W), np.float32)
        At = np.zeros((H, W), np.float32)     # lintel group
        Ab = np.zeros((H, W), np.float32)     # pillars and sill
        vert = np.zeros((H, W), np.float32)   # grain runs vertically here
        # pillars (drawn first; the lintel and sill sit over them)
        for a, b in ((0, side), (W - side, W)):
            uu = (np.arange(a, b, dtype=np.float32) + 0.5 - (a + b) / 2) / ((b - a) / 2)
            Ab[:, a:b] = 1; vert[:, a:b] = 1
            Ht[:, a:b] = 3 + 10 * np.sqrt(np.clip(1 - uu * uu, 0, 1))[None, :]
            inner = b - 3 if a == 0 else a + 1
            gild[top + val:H - sill, inner:inner + 2] = 0.7
        # sill
        Ab[H - sill:] = 1; vert[H - sill:] = 0
        yy = Y[H - sill:]
        Ht[H - sill:] = 2 + 5 * np.sqrt(np.clip(1 - ((yy - (H - sill + 8)) / 7) ** 2, 0, 1))
        gild[H - sill + 15:H - sill + 17] = 1
        im, d = canvas()
        for path in meander(side + 30, W - side - 30, H - sill + 28, H - 14, 46):
            d.line([(x, y) for x, y in path], fill=255, width=5)
        Ht += 3 * blur(arr(im), 0.9)
        # lintel
        At[:top] = 1
        yy = Y[:top]
        Ht[:top] = 2 + 4 * smoothstep(16, 8, yy) + 5 * np.sqrt(np.clip(1 - ((yy - (top - 12)) / 8) ** 2, 0, 1))
        gild[17:19] = 1; gild[top - 3:top - 1] = 1
        im, d = canvas()
        panels = [(side + 22, cx - pw / 2 - 34), (cx + pw / 2 + 34, W - side - 22)]
        for a, b in panels: d.rectangle([a, 30, b, top - 30], fill=255)
        panel = arr(im)
        lip = np.clip(_grow(panel, 4) - panel, 0, 1)
        Ht += -4 * blur(panel, 1.0) + 2.5 * blur(lip, 0.8)
        im, d = canvas()
        for a, b in panels:
            for path in meander(a + 6, b - 6, 40, top - 40, (top - 80) * 1.15):
                d.line([(x, y) for x, y in path], fill=255, width=6)
        Ht += 4.5 * blur(arr(im) * panel, 0.9)
        # plaque: a raised board with a gilt fillet, a red lacquer field and gilt characters
        bx0, bx1, by0, by1 = cx - pw / 2, cx + pw / 2, 12, top - 8
        im, d = canvas(); d.rounded_rectangle([bx0, by0, bx1, by1], radius=12, fill=255); board = arr(im)
        im, d = canvas(); d.rounded_rectangle([bx0 + 17, by0 + 15, bx1 - 17, by1 - 15], radius=5, fill=255); field = arr(im)
        Ht = Ht * (1 - board) + board * (4 + 7 * blur(board, 3.0))
        im, d = canvas(); d.rounded_rectangle([bx0 + 7, by0 + 6, bx1 - 7, by1 - 6], radius=9, outline=255, width=2)
        d.rounded_rectangle([bx0 + 24, by0 + 22, bx1 - 24, by1 - 22], radius=3, outline=255, width=2)
        gild = np.maximum(gild, arr(im))
        red = field.copy()
        fsize = (by1 - by0 - 30) * 0.80
        im, d = canvas()
        f = _font('plaque', fsize)
        plaque = P['plaque']
        n = len(plaque)
        step = min(fsize * 1.32, (pw - 90) / max(1, n))
        for i, ch in enumerate(plaque):
            d.text((cx + (i - (n - 1) / 2) * step, (by0 + by1) / 2 + 2), ch, font=f, fill=255, anchor='mm')
        glyph = arr(im) * field
        gild = np.maximum(gild, glyph)
        Ht += 3.5 * blur(glyph, 1.1)
        gshadow = np.roll(np.roll(blur(glyph, 2.0), 3, 0), 2, 1) * field * (1 - glyph)
        # valance: openwork key-fret between two rails
        im, d = canvas()
        d.rectangle([side, top, W - side, top + 7], fill=255)
        d.rectangle([side, top + val - 9, W - side, top + val], fill=255)
        for path in meander(side + 4, W - side - 4, top + 13, top + val - 15, (val - 26) * 1.25, gap=1.5):
            d.line([(x, y) for x, y in path], fill=255, width=6)
        for x in range(side, W - side, 8):     # pearls along the bottom rail
            d.ellipse([x + 1, top + val - 1, x + 6, top + val + 4], fill=255)
        vm = arr(im)
        # corner brackets: a carved quarter plate pierced with scrolls
        im, d = canvas()
        bh = br * 0.78
        for s in (1, -1):
            x0 = side if s == 1 else W - side
            pts = [(x0 + s * br * np.cos(t), top + val + bh * np.sin(t)) for t in np.linspace(0, np.pi / 2, 48)]
            d.polygon([(x0, top + val)] + pts, fill=255)
        plate = arr(im)
        im, d = canvas()
        for s in (1, -1):
            x0 = side if s == 1 else W - side
            inner = [(x0 + s * (br - 13) * np.cos(t), top + val + (bh - 12) * np.sin(t)) for t in np.linspace(0.06, np.pi / 2 - 0.06, 40)]
            d.polygon([(x0 + s * 11, top + val + 9)] + inner, fill=255)
        hole = arr(im)
        im, d = canvas()
        for s in (1, -1):
            x0 = side if s == 1 else W - side
            for (u0, v0, rr, turns) in ((0.36, 0.40, 0.20, 1.6), (0.70, 0.17, 0.12, 1.4), (0.15, 0.78, 0.10, 1.3)):
                c0x, c0y = x0 + s * br * u0, top + val + bh * v0
                ts = np.linspace(0, turns * 2 * np.pi, 70)
                rs = rr * br * (1 - ts / (turns * 2 * np.pi) * 0.75)
                d.line([(c0x + s * r_ * np.cos(t), c0y - r_ * 0.85 * np.sin(t)) for r_, t in zip(rs, ts)], fill=255, width=9, joint='curve')
            d.line([(x0 + s * br * 0.08, top + val + bh * 0.08), (x0 + s * br * 0.30, top + val + bh * 0.28)], fill=255, width=8)
        bm = np.clip(plate * (1 - hole) + arr(im) * hole, 0, 1)
        inside = ((X >= side) & (X < W - side)).astype(np.float32)
        cm = np.maximum(vm, bm) * inside
        At = np.maximum(At, cm)
        Ht = Ht * (1 - cm) + cm * (2 + 3.5 * blur(cm, 1.2))
        del X, plate, hole, vm, bm, cm, inside, panel, lip, board, field
        # ---- shade, band by band (the frame is only a top band, two pillars and a sill; this keeps memory low)
        l1 = np.array([-0.38, -0.50, 0.78]); l1 /= np.linalg.norm(l1)
        l2 = np.array([0.0, 0.62, 0.78]); l2 /= np.linalg.norm(l2)
        hv = l1 + np.array([0, 0, 1.0]); hv /= np.linalg.norm(hv)
        gh = np.asarray(Image.fromarray(rng.normal(0, 1, (H, W // 50)).astype(np.float32)).resize((W, H), Image.BICUBIC))
        gv = np.asarray(Image.fromarray(rng.normal(0, 1, (H // 50, W)).astype(np.float32)).resize((W, H), Image.BICUBIC))
        fine = noise2d(H, W, 6, 2, self.seed + 32) - 0.5
        gnoise = noise2d(H, W, 3, 2, self.seed + 33) - 0.5
        # light the screen spills onto the frame: a tight rim on edges next to it and a broad warm wash
        B = self._screen_base()
        scr = B['tex'] * (np.exp(-B['r2']) * 0.95 + 0.10) * (1 - np.maximum(At, Ab))
        near = blur(scr, 2.2)
        h2, w2 = H // 2, W // 2
        far = np.asarray(Image.fromarray(blur(scr[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2).mean((1, 3)), 15.0)).resize((W, H), Image.BILINEAR))
        del scr
        rgb_full = np.zeros((H, W, 3), np.float32); spill_full = np.zeros((H, W, 3), np.float32)
        Rt = int(top + val + bh + 16)
        bands = [(0, Rt, 0, W), (Rt, H - sill - 4, 0, side + 2), (Rt, H - sill - 4, W - side - 2, W), (H - sill - 4, H, 0, W)]
        for r0, r1, c0, c1 in bands:
            sl = (slice(r0, r1), slice(c0, c1))
            Hb = Ht[sl]
            gy, gx = np.gradient(blur(Hb, 0.8))
            nz = 1 / np.sqrt(gx * gx + gy * gy + 1)
            nx, ny = -gx * nz, -gy * nz
            d1 = np.clip(nx * l1[0] + ny * l1[1] + nz * l1[2], 0, 1)
            d2 = np.clip(nx * l2[0] + ny * l2[1] + nz * l2[2], 0, 1)
            spec = (np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1) ** 40)[..., None]
            vb = vert[sl]
            grain = (gh[sl] * (1 - vb) + gv[sl] * vb) * 0.5 + 0.25 * fine[sl]
            ao = 1 - 0.55 * np.clip((blur(Hb, 5) - Hb) / 3, 0, 1)
            wood = np.array(WOOD, np.float32) * (0.82 + 0.36 * np.clip(grain, -1, 1))[..., None]
            rgb = wood * ((0.30 + 0.62 * d1 + 0.22 * d2) * ao)[..., None] + 0.10 * spec
            rd = red[sl][..., None]
            if rd.any():
                lac = np.array(LACQUER, np.float32) * ((0.8 + 0.35 * smoothstep(by1, by0, Y[sl])) * (0.55 + 0.6 * d1))[..., None]
                lac = lac * (1 - 0.65 * gshadow[sl][..., None]) + 0.22 * spec
                rgb = rgb * (1 - rd) + lac * rd
            gd = gild[sl][..., None]
            gold = np.array(GOLD, np.float32) * (0.38 + 0.80 * d1 + 0.25 * d2)[..., None] + 0.55 * spec * np.array([1, 0.9, 0.7], np.float32)
            gold *= (0.92 + 0.12 * gnoise[sl])[..., None]
            rgb_full[sl] = rgb * (1 - gd) + gold * gd
            spill_full[sl] = ((1.1 * near[sl] + 0.40 * far[sl]) * (0.55 + 0.6 * d2) * (1 - 0.5 * gild[sl]))[..., None] * np.array(SPILL, np.float32)
        layers = {}
        for name, Am in (('base', Ab), ('top', At)):
            ys = np.nonzero(Am.max(1) > 0)[0]
            r0, r1 = int(ys.min()), int(ys.max()) + 1
            layers[name] = dict(r0=r0, r1=r1, A=Am[r0:r1].copy(), rgb=rgb_full[r0:r1].copy(), spill=spill_full[r0:r1].copy())
        self._frame = layers

    def _front(self, I):
        if self._prosc is not None:
            if self._frame is None: self._build_frame()
            st = self.lamp_state
            lvl = st['level'] * min(1.0, st['radius']) ** 2 * (1 + 0.6 * st['flicker'])
            for name in ('base', 'top'):
                Ly = self._frame[name]
                r0, r1 = Ly['r0'], Ly['r1']
                A, rgb = Ly['A'], Ly['rgb'] + Ly['spill'] * lvl
                if name == 'top':
                    fp = self.frame_pose
                    if fp['alpha'] <= 0: continue
                    dy = int(round(fp['dy']))
                    r0, r1 = r0 + dy, r1 + dy
                    A = A * fp['alpha']
                    if r1 <= 0: continue
                    if r0 < 0: A, rgb, r0 = A[-r0:], rgb[-r0:], 0
                    if r1 > self.H: A, rgb, r1 = A[:self.H - r0], rgb[:self.H - r0], self.H
                a = A[..., None]
                I[r0:r1] = I[r0:r1] * (1 - a) + rgb * a
        for ln in self.lanterns:
            if ln.shown: self._draw_lantern(I, ln)
        return I

    def _draw_lantern(self, I, ln):
        rgb, A, (hx, cy) = ln._draw(ln.lit)
        h, w = A.shape
        dy = self.frame_pose['dy'] if self._prosc else 0.0
        ox, oy = ln.x - hx, ln.top + dy
        if ln.swing:
            ch = [Image.fromarray(np.ascontiguousarray(c), 'F').rotate(ln.swing, Image.BICUBIC, center=(hx, 0))
                  for c in (rgb[..., 0], rgb[..., 1], rgb[..., 2], A)]
            rgb = np.stack([np.asarray(c) for c in ch[:3]], -1); A = np.clip(np.asarray(ch[3]), 0, 1)
        x0, y0 = int(round(ox)), int(round(oy))
        ya, yb = max(0, y0), min(self.H, y0 + h); xa, xb = max(0, x0), min(self.W, x0 + w)
        if ya >= yb or xa >= xb: return
        a = A[ya - y0:yb - y0, xa - x0:xb - x0, None]
        I[ya:yb, xa:xb] = I[ya:yb, xa:xb] * (1 - a) + rgb[ya - y0:yb - y0, xa - x0:xb - x0] * a
        if ln.lit > 0:     # warm halo in the air round it
            t = np.deg2rad(ln.swing)
            bx, by = ln.x + np.sin(t) * cy, oy + np.cos(t) * cy
            sg = 1.7 * ln.r; R = int(3 * sg)
            ya, yb = max(0, int(by - R)), min(self.H, int(by + R)); xa, xb = max(0, int(bx - R)), min(self.W, int(bx + R))
            if ya < yb and xa < xb:
                yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
                g = np.exp(-((xx - bx) ** 2 + (yy - by) ** 2) / (2 * sg * sg)) * 0.30 * ln.lit
                I[ya:yb, xa:xb] += g[..., None] * np.array([1.0, 0.34, 0.10], np.float32)

    # ------------------------------------------------------------ render
    def _lampmat(self, li, d):
        if li is None or d <= 0: return np.eye(3)
        (fx, fy), _ = self.lamps[li]
        m = 1 + 0.30 * d
        return np.array([[m, 0, fx * (1 - m)], [0, m, fy * (1 - m)], [0, 0, 1.0]])

    @staticmethod
    def _sigma(d):
        return 0.0 if d <= 0 else 0.5 + 16.0 * d

    def _warp(self, part, M):
        img, x0, y0 = part['img'], part['x0'], part['y0']
        w, h = img.size
        C = np.array([[x0, y0, 1], [x0 + w, y0, 1], [x0 + w, y0 + h, 1], [x0, y0 + h, 1]], np.float64)
        Pc = C @ M.T
        bx0, by0 = int(np.floor(Pc[:, 0].min())) - 1, int(np.floor(Pc[:, 1].min())) - 1
        bx1, by1 = int(np.ceil(Pc[:, 0].max())) + 1, int(np.ceil(Pc[:, 1].max())) + 1
        if bx1 <= 0 or by1 <= 0 or bx0 >= self.W or by0 >= self.H: return None
        Li = np.linalg.inv(M[:2, :2]); t = M[:2, 2]
        a, b = Li[0]; d_, e = Li[1]
        c = a * (bx0 - t[0]) + b * (by0 - t[1]) - x0
        f = d_ * (bx0 - t[0]) + e * (by0 - t[1]) - y0
        out = img.transform((bx1 - bx0, by1 - by0), Image.AFFINE, (a, b, c, d_, e, f), resample=Image.BILINEAR)
        return by0, bx0, np.asarray(out, np.float32) / 255

    def _render_item(self, p, S):
        Mw = p.matrices()
        groups = {}
        for n in p.order:
            groups.setdefault(round(min(1.0, max(0.0, p.d + p.away.get(n, 0.0))), 2), []).append(n)
        for de, names in groups.items():
            sig = self._sigma(de)
            for li in ((0, 1) if de > 0 else (None,)):
                Lm = self._lampmat(li, de)
                pieces = []
                for n in names:
                    r = self._warp(p.parts[n], Lm @ Mw[n])
                    if r is not None: pieces.append(r)
                if not pieces: continue
                pad = int(3 * sig) + 3
                y0 = min(r[0] for r in pieces) - pad; x0 = min(r[1] for r in pieces) - pad
                y1 = max(r[0] + r[2].shape[0] for r in pieces) + pad; x1 = max(r[1] + r[2].shape[1] for r in pieces) + pad
                buf = np.ones((y1 - y0, x1 - x0, 3), np.float32)
                for (oy, ox, arr) in pieces:
                    buf[oy - y0:oy - y0 + arr.shape[0], ox - x0:ox - x0 + arr.shape[1]] *= 1 - arr * p.alpha
                # thread knots at the joints
                kr = 3.8 * p.k * (Lm[0, 0])
                for n in names:
                    if not p.parts[n]['knot']: continue
                    v = Lm @ Mw[n] @ np.array([0, 0, 1.0])
                    cxk, cyk = v[0] - x0, v[1] - y0
                    ya, yb = int(cyk - kr - 4), int(cyk + kr + 5); xa, xb = int(cxk - kr - 4), int(cxk + kr + 5)
                    if ya < 0 or xa < 0 or yb > buf.shape[0] or xb > buf.shape[1]: continue
                    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32) + 0.5
                    dd = np.hypot(xx - cxk, yy - cyk)
                    knot = np.clip(kr - dd + 0.5, 0, 1) * 0.86 + np.clip(1.0 - np.abs(dd - kr - 1.4), 0, 1) * 0.25
                    buf[ya:yb, xa:xb] *= 1 - (knot * p.alpha)[..., None]
                if sig > 0:
                    K = 1 - buf
                    buf = 1 - np.stack([blur(K[..., c], sig) for c in range(3)], -1)
                for T in ((S[0], S[1]) if li is None else (S[li],)):
                    self._mul(T, buf, y0, x0)
        # control rods: tied on at the puppet's distance, slanting back toward the puppeteers
        for rd in p.rods:
            A = p.point(rd['part'], rd['pt'], Mw)
            d0 = min(1.0, p.d + p.away.get(rd['part'], 0.0)); d1 = min(1.0, d0 + 0.15)
            B = (A[0] + rd['lean'], self.box[3] + 70)
            for li in (0, 1):
                a = self._lampmat(li, d0) @ np.array([A[0], A[1], 1.0]); b = self._lampmat(li, d1) @ np.array([B[0], B[1], 1.0])
                self._rod(S[li], a, b, max(0.6, self._sigma(d0)), self._sigma(d1), rd['width'] * p.k, p.alpha)

    def _mul(self, T, buf, y0, x0):
        h, w = buf.shape[:2]
        ya, yb = max(0, y0), min(self.H, y0 + h); xa, xb = max(0, x0), min(self.W, x0 + w)
        if ya < yb and xa < xb:
            T[ya:yb, xa:xb] *= buf[ya - y0:yb - y0, xa - x0:xb - x0]

    def _rod(self, T, a, b, s0, s1, width, alpha):
        pad = int(3 * max(s0, s1)) + 4
        x0, x1 = int(min(a[0], b[0])) - pad, int(max(a[0], b[0])) + pad + 1
        y0, y1 = int(min(a[1], b[1])) - pad, int(max(a[1], b[1])) + pad + 1
        w, h = x1 - x0, y1 - y0
        im = Image.new('L', (w * 2, h * 2), 0)
        dr = ImageDraw.Draw(im)
        wpx = max(1, int(round(width * 2)))
        dr.line([((a[0] - x0) * 2, (a[1] - y0) * 2), ((b[0] - x0) * 2, (b[1] - y0) * 2)], fill=255, width=wpx)
        r = wpx * 0.9
        dr.ellipse([(a[0] - x0) * 2 - r, (a[1] - y0) * 2 - r, (a[0] - x0) * 2 + r, (a[1] - y0) * 2 + r], fill=255)
        m = np.asarray(im, np.float32).reshape(h, 2, w, 2).mean((1, 3)) / 255
        m0, m1 = blur(m, s0), blur(m, s1)
        t = np.clip((np.arange(h, dtype=np.float32) + y0 - a[1]) / max(1.0, b[1] - a[1]), 0, 1)[:, None] ** 0.8
        mm = (m0 * (1 - t) + m1 * t * (1 + 0.4 * t))
        self._mul(T, 1 - alpha * mm[..., None] * np.array(ROD, np.float32), y0, x0)

    def _bloom(self, E):
        H, W = self.H, self.W
        h2, w2 = H // 2, W // 2
        Eh = E[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 3).mean((1, 3))
        out = E.copy()
        for sg, amt in ((14, 0.15), (3, 0.06)):
            b = np.stack([blur(Eh[..., c], sg) for c in range(3)], -1)
            up = np.stack([np.asarray(Image.fromarray(b[..., c]).resize((w2 * 2, h2 * 2), Image.BILINEAR)) for c in range(3)], -1)
            out[:h2 * 2, :w2 * 2] += amt * up
        return out

    def _postfx(self):
        if self._post is None:
            H, W = self.H, self.W
            Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
            r = np.hypot((X - W / 2) / W, (Y - H / 2) / H)
            vig = 1 - 0.30 * r ** 2 * 2.0
            grain = 1 + 0.018 * (noise2d(H, W, 1.0, 1, self.seed + 99) - 0.5)
            self._post = (vig * grain).astype(np.float32)
        return self._post

    def render(self):
        H, W = self.H, self.W
        L = self._emission()
        S = [np.ones((H, W, 3), np.float32), np.ones((H, W, 3), np.float32)]
        for p in self.items:
            if p.shown and p.alpha > 0: self._render_item(p, S)
        w1, w2 = self.lamps[0][1], self.lamps[1][1]
        E = L * (w1 * S[0] + w2 * S[1])
        del S
        E = self._bloom(E)
        k = 1.5
        I = (1 - np.exp(-k * E)) / (1 - np.exp(-k))      # soft shoulder: the hot spot glows instead of clipping
        I = self._front(I)
        return I * self._postfx()[..., None]

    def composite(self):
        return Image.fromarray((np.clip(self.render(), 0, 1) * 255 + 0.5).astype(np.uint8))

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


# ================================================================ the figure
def _figure(sp, robe='red', trim='black', accent='ochre', trousers='teal', face='hollow', skin='plain', facedye=None,
            headdress='plume', plume='ochre', pom='red', pattern='cloud', hands=('open', 'open'), scale=1.0, seed=None,
            name='figure'):
    """A jointed shadow-puppet figure facing right (flip it to face left). Parts and joints:
        pelvis (root, pivot at the hips) -- torso (waist) -- head (neck), arm_f / arm_b (shoulders) -- fore_f /
        fore_b (elbows) -- hand_f / hand_b (wrists); thigh_f / thigh_b (hips) -- shin_f / shin_b (knees).
    _f is the near limb, _b the far one. robe / trim / accent / trousers / skin are dye names; face 'hollow' (阳刻:
    the face cut away, a fine profile line, one long eye, a long brow) or 'solid' (阴刻: the face left as dyed leather,
    `facedye`, with the features cut out); headdress 'plume' (helmet + two pheasant plumes), 'crown' (crown with
    pompoms and a tassel) or 'bun' (hair knot and a ribbon); pattern: the hollow pattern of the robe; hands: ('open' |
    'fist') for the near and far hand. At scale 1 the figure stands about 520 px from sole to helmet."""
    k = float(scale)
    rng = np.random.default_rng(sp._seed() if seed is None else seed)
    sd = lambda: int(rng.integers(1 << 30))
    P = Puppet(sp, name, k)
    LW = 2.4
    other = 'teal' if robe not in ('teal', 'green', 'blue') else 'red'

    # ---- pelvis: tunic skirt with belt and buckle (root; pivot = hips)
    L = Leather(-66, -46, 52, 108, k, seed=sd())
    sk = L.fill(_loop([(-36, -34), (-40, 4), (-50, 56), (-58, 96), (-30, 104), (-6, 99), (20, 104), (46, 96), (42, 48), (35, 4), (31, -34)], 6), robe)
    hem = L.dye(sk * L.below(84), trim)
    L.pattern(sk * L.above(80) * L.below(-16), pattern, 26, margin=5, origin=(0, 30))
    L.pattern(hem, 'dots', 10, r=0.24, margin=3, origin=(0, 94))
    belt = L.fill([(-44, -41), (35, -41), (36, -18), (-45, -18)], accent)
    L.pattern(belt, 'stripes', 7, bar=0.5, margin=3.2)
    L.carve([(-7, 103), (-6, 46)], 2.0)
    L.edge(LW); L.contour(hem, 1.6); L.contour(belt, 1.6)
    bk = L.fill(L.ellipse(28, -29.5, 8, 7.5), other)
    L.contour(bk, 1.5); L.punch(L.ellipse(28, -29.5, 2.4), 0)
    P.add('pelvis', L)

    def thigh():
        L = Leather(-26, -20, 26, 112, k, seed=sd())
        m = L.fill(_loop([(0, -17), (17, -11), (21, 26), (18, 70), (15, 106), (-15, 106), (-19, 70), (-21, 26), (-17, -11)], 6), trousers)
        L.pattern(m * L.below(12) * L.above(92) * L.left_of(-4), 'dots', 11, angle=90, r=0.22, margin=3, origin=(-11, 30))
        L.edge(LW)
        return L

    def shin():
        L = Leather(-26, -18, 64, 122, k, seed=sd())
        out = np.vstack([spline([(0, -15), (14, -9), (14, 36), (13, 84), (24, 92), (38, 96), (48, 97), (53, 92)], 5),
                         spline([(53, 92), (51, 106), (43, 116), (-18, 116), (-18, 103), (-15, 90), (-14, 36), (-15, -9), (0, -15)], 5)])
        m = L.fill(out, trousers)
        boot = L.dye(m * L.below(36), 'black')
        sole = L.dye(m * L.below(103), 'plain')
        L.pattern(m * L.above(33), 'lattice', 12, angle=45, bar=0.26, margin=3.5)
        L.pattern(boot * L.above(98) * L.below(42), 'cloud', 21, margin=3.5, origin=(0, 66))
        L.pattern(sole, 'dots', 8, r=0.2, margin=2.6, origin=(0, 110))
        L.edge(LW); L.contour(sole, 1.8)
        L.line([(-14, 37), (14, 37)], 2.4, accent)
        return L

    P.add('thigh_b', thigh(), 'pelvis', (-8, 0))
    P.add('shin_b', shin(), 'thigh_b', (0, 100))

    # ---- torso: robe, cloud collar, breastplate mirror, scale armour, sash (pivot = waist)
    L = Leather(-52, -162, 58, 10, k, seed=sd())
    tm = L.fill(_loop([(30, 4), (36, -34), (46, -84), (45, -112), (36, -130), (18, -142), (-8, -144), (-30, -136), (-42, -118), (-42, -66), (-35, 4)], 6), robe)
    cm = L.fill(_loop([(-34, -128), (-22, -146), (18, -146), (40, -128), (47, -108), (35, -97), (23, -110), (10, -94), (-4, -107), (-18, -95), (-32, -105)], 6), accent)
    sash = L.dye(tm * L.below(-20), trim)
    mirror = L.fill(L.ellipse(14, -70, 17), other)
    L.pattern(tm * (1 - L.grow(cm, 1.5)) * (1 - L.grow(mirror, 2)) * L.above(-24), 'scales', 17, margin=4.5, origin=(0, -96))
    L.pattern(cm, 'cloud', 17, margin=3.2, origin=(4, -116))
    L.pattern(mirror, 'flower', 40, petals=6, r=0.085, ring=0.2, margin=2, origin=(14, -70))
    L.punch(L.ellipse(14, -70, 3), 0)
    L.pattern(sash, 'dots', 8, r=0.22, margin=2.8, origin=(0, -8))
    L.fill(L.ellipse(3, -142, 15, 6, rot=-6), trim)
    L.edge(LW); L.contour(cm, 1.7); L.contour(sash, 1.6); L.contour(mirror, 1.8)
    L.dye(L.ring(14, -70, 11.5, 13.3), 'black')
    P.add('torso', L, 'pelvis', (-2, -30))

    def arm(near):
        L = Leather(-26, -26, 26, 94, k, seed=sd())
        m = L.fill(_loop([(0, -20), (15, -15), (19, 4), (18, 40), (15, 88), (-15, 88), (-18, 40), (-19, 4), (-15, -15)], 6), robe)
        L.pattern(m * L.below(16 if near else -4) * L.above(80), pattern, 22, margin=4, origin=(0, 50))
        if near:     # the shoulder guard only on the near arm (two would pile up over the collar)
            md = L.fill(L.ellipse(0, -1, 14.5, 13.5), accent)
            L.pattern(md, 'flower', 28, petals=5, r=0.11, ring=0.2, margin=1.5, origin=(0, -1))
            L.contour(md, 1.6)
        L.edge(LW)
        return L

    def fore():
        L = Leather(-24, -16, 24, 82, k, seed=sd())
        m = L.fill(_loop([(0, -13), (13, -9), (14, 28), (15, 52), (18, 78), (-18, 78), (-15, 52), (-14, 28), (-13, -9)], 6), robe)
        cuff = L.dye(m * L.below(54), trim)
        L.pattern(m * L.above(50) * L.below(4), 'dots', 14, r=0.2, margin=4, origin=(0, 26), angle=90)
        L.pattern(cuff, 'dots', 7.5, r=0.22, margin=2.6, origin=(0, 66))
        L.edge(LW); L.contour(cuff, 1.4)
        L.line([(-16, 54), (16, 54)], 2.2, accent)
        return L

    def hand(kind):
        L = Leather(-18, -8, 28, 54, k * 1.1, seed=sd())
        if kind == 'fist':
            L.fill(_loop([(-10, -2), (9, -2), (13, 10), (14, 26), (6, 33), (-8, 32), (-12, 18)], 5), skin)
            L.edge(1.7)
            for y in (13, 20, 27): L.carve([(3, y), (12, y - 1)], 1.1)
            L.carve([(-4, 8), (6, 14)], 1.1)
        else:
            L.fill(_loop([(-9, -2), (9, -2), (11, 13), (9, 25), (-9, 25), (-11, 12)], 5), skin)
            for i, x in enumerate((-7.2, -2.4, 2.4, 7.2)):
                L.fill(L.ribbon(spline([(x, 20), (x * 1.12, 33), (x * 1.18 + 1.0, 45 - abs(i - 1.6) * 3.2)], 6), 4.6, 3.6), skin)
            L.fill(L.ribbon(spline([(7, 7), (15, 17), (20, 28)], 6), 5.4, 3.8), skin)
            L.edge(1.6)
            for x in (-4.8, 0.0, 4.8): L.carve([(x * 1.1, 27), (x * 1.16, 36)], 0.9)
        return L

    def head():
        L = Leather(-170, -240, 66, 12, k * 1.15, seed=sd())
        L.fill([(-10, 10), (-11, -24), (7, -24), (9, 10)], skin)
        front = spline([(4, -19), (11, -24.5), (17, -28.5), (18, -33), (15.8, -35.2), (19.2, -37.8), (18.4, -40.8), (21.6, -43.4),
                        (25.2, -45.4), (21, -50), (18.6, -55.5), (17.4, -60), (15.6, -67), (11, -74)], 5)
        back = spline([(11, -74), (3, -74), (-1, -64), (-3.5, -50), (-4, -36), (0, -24), (4, -19)], 5)
        fm = L.fill(np.vstack([front, back]), skin if face == 'hollow' else (facedye or skin))
        hair = np.vstack([spline([(11, -74), (4, -81), (-8, -86), (-20, -82), (-27, -68), (-28, -52), (-23, -38), (-14, -27), (-9, -22)], 5),
                          spline([(-9, -22), (-2, -26), (-4, -36), (-3.5, -50), (-1, -64), (3, -74), (11, -74)], 5)])
        hm = L.fill(hair, 'black')
        L.carve(spline([(-22, -46), (-17, -60), (-8, -70)], 6), 1.0)
        L.carve(spline([(-18, -36), (-13, -50), (-5, -60)], 6), 1.0)
        ear = L.fill(L.ellipse(-6, -45, 4.8, 7.5, rot=10), skin)
        L.contour(ear, 1.2); L.carve(spline([(-6, -50), (-8, -45), (-5, -41)], 5), 0.9)
        brow = L.ribbon(spline([(3, -58.6), (9, -61.6), (17.4, -60.2)], 8), 3.0, 1.2)
        eye_up = spline([(4, -53.6), (9.5, -55.8), (15.8, -53.6)], 8)
        eye_lo = spline([(6.5, -52.6), (11, -51.4), (15.8, -53.4)], 8)
        tail = L.ribbon(spline([(5, -53.8), (2, -55.2), (-0.5, -57.2)], 6), 1.6, 0.6)
        if face == 'hollow':
            L.edge(2.0, region=fm)
            L.punch(L.inset(fm, 2.1) * (1 - L.grow(hm, 0.5)) * (1 - L.grow(ear, 1.2)), 0)
            L.fill(brow, 'black'); L.line(eye_up, 1.5); L.line(eye_lo, 1.0); L.fill(tail, 'black')
            L.fill(L.ellipse(12.0, -53.5, 1.9, 2.1), 'black')
            L.line(spline([(18.6, -42.0), (20.4, -44.2), (22.6, -43.8)], 5), 1.1)
            L.line([(15.8, -35.3), (12.6, -35.0)], 1.1)
        else:
            L.edge(2.0, region=fm)
            L.punch(brow, 0); L.punch(tail, 0)
            L.punch(L.poly(np.vstack([eye_up, eye_lo[::-1]])) * (1 - L.ellipse(12.0, -53.5, 1.9, 2.1)), 0)
            L.carve(spline([(18.4, -42.2), (20.4, -44.2), (22.2, -43.8)], 5), 1.0)
            L.carve([(15.6, -35.3), (12.4, -35.0)], 1.1)
        if headdress == 'plume':
            helm = np.vstack([spline([(13, -73), (14, -86), (10, -98), (0, -106), (-14, -104), (-25, -94), (-29, -78), (-28, -68)], 6),
                              spline([(-28, -68), (-10, -75), (13, -73)], 6)])
            hl = L.fill(helm, robe)
            L.pattern(hl * L.above(-80), 'scales', 11, margin=2.6, origin=(0, -100))
            band = L.fill(L.ribbon(spline([(-30, -69), (-10, -75.5), (15, -74)], 8), 9, 8), accent)
            L.pattern(band, 'dots', 6.2, r=0.22, margin=1.8, origin=(0, -72))
            fl = L.fill(_loop([(5, -98), (16, -107), (20, -121), (15, -137), (11, -124), (3, -110)], 6), accent)
            L.punch(L.ellipse(13, -114, 2.6, 4.5, rot=-25), 0.6)
            for (px, py, pr) in ((16, -138, 7.5), (-25, -97, 6.5)):
                pm = L.fill(L.ellipse(px, py, pr), pom)
                L.pattern(pm, 'dots', pr * 0.9, r=0.2, margin=1.4, origin=(px, py))
            plumes = [spline([(-7, -103), (-18, -146), (-44, -176), (-84, -192), (-126, -190), (-158, -176)], 10),
                      spline([(0, -105), (-6, -154), (-28, -194), (-66, -216), (-110, -220), (-146, -208)], 10)]
            for pl in plumes:
                pm = L.fill(L.ribbon(pl, 9.5, 2.6), plume)
                seg = np.cumsum(np.r_[0, np.linalg.norm(np.diff(pl, axis=0), axis=1)])
                for s0 in np.arange(14, seg[-1] - 6, 11.5):
                    i = np.searchsorted(seg, s0); i = min(max(i, 1), len(pl) - 2)
                    dvec = pl[i + 1] - pl[i - 1]; dvec = dvec / (np.linalg.norm(dvec) + 1e-6)
                    nrm = np.array([-dvec[1], dvec[0]])
                    wv = 9.5 + (2.6 - 9.5) * s0 / seg[-1]
                    L.dye(L.stroke([pl[i] - nrm * wv, pl[i] + nrm * wv], 3.4) * pm, 'black')
                L.edge(1.2, region=pm)
            L.edge(1.6, region=hl); L.contour(band, 1.3); L.contour(fl, 1.3)
        elif headdress == 'crown':
            cr = np.vstack([spline([(14, -73), (16, -90), (6, -104), (-6, -108), (-20, -102), (-28, -86), (-28, -68)], 6),
                            spline([(-28, -68), (-10, -75), (14, -73)], 6)])
            crm = L.fill(cr, accent)
            L.pattern(crm * L.above(-80), 'coins', 12, margin=2.4, origin=(0, -95))
            for (x, y, s) in ((10, -104, 1.0), (-4, -112, 1.25), (-19, -106, 1.0)):
                fl = L.fill(_loop([(x - 6 * s, y + 4), (x + 6 * s, y + 4), (x + 4 * s, y - 10 * s), (x, y - 22 * s), (x - 4 * s, y - 10 * s)], 5), accent)
                L.contour(fl, 1.2)
                pm = L.fill(L.ellipse(x, y - 22 * s - 5, 5.5 * s), pom)
                L.contour(pm, 1.1)
            band = L.fill(L.ribbon(spline([(-30, -69), (-10, -75.5), (16, -74)], 8), 8, 7), robe)
            L.pattern(band, 'dots', 6, r=0.22, margin=1.7, origin=(0, -72))
            L.line(spline([(-26, -70), (-32, -52), (-30, -32)], 6), 1.4)
            tm_ = L.fill(L.ellipse(-30, -28, 4.8), pom); L.contour(tm_, 1.1)
            L.edge(1.6, region=crm); L.contour(band, 1.3)
        elif headdress == 'bun':
            L.fill(L.ellipse(-10, -88, 13, 10, rot=-15), 'black')
            L.carve(spline([(-18, -86), (-10, -94), (0, -90)], 6), 1.0)
            rb = L.fill(L.ribbon(spline([(-14, -80), (-32, -70), (-44, -48), (-52, -26)], 8), 6, 3), accent)
            L.pattern(rb, 'dots', 5, r=0.2, margin=1.3)
            L.contour(rb, 1.1)
        L.edge(1.4, region=1 - fm)
        return L

    P.add('arm_b', arm(False), 'torso', (-16, -122))
    P.add('fore_b', fore(), 'arm_b', (0, 82))
    P.add('hand_b', hand(hands[1]), 'fore_b', (0, 76))
    P.add('head', head(), 'torso', (3, -135), knot=False)
    P.add('thigh_f', thigh(), 'pelvis', (4, 2))
    P.add('shin_f', shin(), 'thigh_f', (0, 100))
    P.add('arm_f', arm(True), 'torso', (4, -118))
    P.add('fore_f', fore(), 'arm_f', (0, 82))
    P.add('hand_f', hand(hands[0]), 'fore_f', (0, 76))
    P.soles = {'shin_f': [(-18, 116), (43, 116)], 'shin_b': [(-18, 116), (43, 116)]}
    return P
