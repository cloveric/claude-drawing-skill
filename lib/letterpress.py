"""letterpress — a two-colour letterpress poster of the 1890s playbill kind: wood-type lines set to full measure,
a woodcut picture split into a red tint block and a black key block, both printed a hair out of register on
cheap toned stock that has since been folded, tacked to a wall and left to foxing (numpy + Pillow only).

Model: a sheet goes through the press once per ink. Everything that will print in one ink is first locked up on
that ink's forme (`plates[ink]`), then `press(ink)` prints the forme in one impression.
  stock      cheap machine-finished paper, already toned: a cloudy cream with warmer patches, short fibres, dark
             flecks in the pulp and a per-pixel "tooth" (the hills and pits that decide where ink takes).
  forme      one per ink. A forme carries wood type, metal type, brass rules, ornaments and the woodcut block for
             that colour. On press the sheet lands a little differently for every pass, so each forme prints with
             its own small shift and a hair of rotation (`register`): red and black never sit exactly on each
             other -- the red tint creeps out from under the black key on one side and leaves a sliver of paper on
             the other. A forme can be locked in named parts (`with lp.layer('key'):`) and proofed part by part
             (`press(ink, only=['key'])`), which is how the drawing stages show key lines before hatching.
  wood type  every letter is its own block of end-grain maple. A line is set to the full measure, the way a
             jobbing printer filled a poster: the face is condensed or extended (a different font of wood type)
             and letter-spaced until the line is flush on both sides. Each block inks a little differently: wood
             grain prints as faint streaks, the block is never exactly type-high so one end prints lighter, old
             blocks have nicked edges, dents (pale soft spots) and now and then a split along the grain. Shaded
             letters (`shade=`) carry a drop shade on the other forme; inline letters (`inline=`) have a white line
             cut down the middle of the stroke.
  ink        a stiff, nearly opaque oil ink rolled on thin. On big solids the roller starves: the film goes
             mottled and the deepest pits of the tooth stay bare (a "salty" print), while the edge of every
             solid squeezes a little extra ink into a darker rim. Dust on the forme leaves round dropouts.
             Black over red prints darker still.
  impression the forme bites into the soft sheet: printed areas sit in a shallow dent that catches the light
             along one edge (very low, it is thin stock).
  woodcut    drawn the way a cutter leaves wood standing: a key line around every shape that thickens on the side
             away from the light, swelling parallel hatching whose line width follows a tone (`hatch`), solid
             blacks, carved highlights (`clear`), stipple, and a red tint block (`tint`) cut separately and loosely
             from the key, so its edges wander off the black lines.
  afterlife  the bill was folded in thirds to post (`fold`: a crease with cracked ink, dirt and a light/shade
             roll), a date strip printed on its own little press was pasted on (`strip(..., draw=fn)`: whiter slip,
             glue stain round it), it was tacked up (`tack`: torn hole, rust halo), browned from the edges
             (`tone_edges`), foxed (`foxing`), water-stained (`stain`) and nicked (`nicks`).
Coordinates are pixels, y down. Angles are degrees counter-clockwise (0 = 3 o'clock) unless noted. Shapes are
full-sheet float masks (`shape`, `poly`, `tube`, `ellipse`, `rect`) that can be added, multiplied and subtracted.

    from letterpress import Letterpress, RED, BLACK
    lp = Letterpress(1920, 1080, seed=7)
    lp.paper()
    lp.type_line('CIRCUS', 90, 840, 360, 190, face='clarendon', ink=RED, shade=(9, 7, BLACK, 4))
    body = lp.shape([(1200, 600), (1500, 560), (1600, 700), (1300, 760)])
    lp.tint(body)                                  # red block
    lp.clear(body); lp.key(body); lp.hatch(body, angle=30)
    lp.press(RED); lp.press(BLACK)
    lp.fold('v', 640); lp.tone_edges(); lp.foxing()
    lp.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core import blur, noise2d, smoothstep, shift, spline, latin_font, fbm1d

RED, BLACK = '#c0392b', '#1d1a17'
PAPER, AGED, RUST, WALL = '#ecdfbd', '#c9a66b', '#8a4a22', '#3a2f26'
OPACITY = {RED: 0.82, BLACK: 0.95}
LIGHT = (-0.55, -0.83)                       # where the light comes from (screen direction, unit-ish)
SS = 2                                       # supersampling for type and shapes


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- faces of type (kept inside this module)
_S = '/System/Library/Fonts/Supplemental/'
_FACES = {   # (glob, index); first hit wins -- macOS, then Linux / Windows look-alikes; generic core style last
    'clarendon': [(_S + 'SuperClarendon.ttc', 7), (_S + 'Rockwell.ttc', 2), ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0),
                  ('C:/Windows/Fonts/ROCKEB.TTF', 0), ('C:/Windows/Fonts/georgiab.ttf', 0)],
    'antique': [(_S + 'Rockwell.ttc', 2), (_S + 'SuperClarendon.ttc', 5), ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0),
                ('C:/Windows/Fonts/ROCKB.TTF', 0), ('C:/Windows/Fonts/georgiab.ttf', 0)],
    'gothic': [(_S + 'Impact.ttf', 0), (_S + 'DIN Condensed Bold.ttf', 0), ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', 0),
               ('C:/Windows/Fonts/impact.ttf', 0)],
    'fatface': [(_S + 'Bodoni 72.ttc', 2), (_S + 'Didot.ttc', 2), ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0),
                ('C:/Windows/Fonts/BOD_B.TTF', 0), ('C:/Windows/Fonts/georgiab.ttf', 0)],
    'roman': [(_S + 'Hoefler Text.ttc', 0), (_S + 'PTSerif.ttc', 0), (_S + 'Times New Roman.ttf', 0),
              ('/usr/share/fonts/**/DejaVuSerif.ttf', 0), ('C:/Windows/Fonts/times.ttf', 0)],
    'roman_bold': [(_S + 'Hoefler Text.ttc', 1), (_S + 'PTSerif.ttc', 3), (_S + 'Times New Roman Bold.ttf', 0),
                   ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0), ('C:/Windows/Fonts/timesbd.ttf', 0)],
    'italic': [(_S + 'Hoefler Text.ttc', 2), (_S + 'PTSerif.ttc', 1), (_S + 'Times New Roman Italic.ttf', 0),
               ('/usr/share/fonts/**/DejaVuSerif-Italic.ttf', 0), ('C:/Windows/Fonts/timesi.ttf', 0)],
    'cjk': [(_S + 'Songti.ttc', 0), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
            ('/usr/share/fonts/**/NotoSerifCJK*Black*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSerifCJK*Bold*.tt[cf]', 0),
            ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('C:/Windows/Fonts/simsun.ttc', 0)],
    'cjk_book': [(_S + 'Songti.ttc', 6), ('/System/Library/Fonts/STHeiti Medium.ttc', 1),
                 ('/usr/share/fonts/**/NotoSerifCJK*Regular*.tt[cf]', 0), ('C:/Windows/Fonts/simsun.ttc', 0)],
    'ornament': [(_S + 'Bodoni Ornaments.ttf', 0)],
}
_GENERIC = {'clarendon': 'serif', 'antique': 'serif', 'gothic': 'condensed', 'fatface': 'serif', 'roman': 'serif',
            'roman_bold': 'serif', 'italic': 'serif', 'cjk': 'cjk', 'cjk_book': 'cjk', 'ornament': 'sans'}
_HITS, _FONTS, _CAP = {}, {}, {}


def _face(face):
    if face in _HITS: return _HITS[face]
    env = os.environ.get('INKPAINT_FONT_' + face.upper())
    hit = (env, 0) if env and os.path.exists(env) else None
    for pat, idx in ([] if hit else _FACES.get(face, [])):
        fs = glob.glob(pat, recursive=True)
        if fs:
            hit = (fs[0], idx); break
    if hit is None and face != 'ornament':
        hit = latin_font(_GENERIC.get(face, 'sans')) or latin_font('sans')
    _HITS[face] = hit
    return hit


def font(face, size):
    """PIL font for a face of type: clarendon, antique, gothic, fatface, roman, roman_bold, italic, cjk, cjk_book"""
    k = (face, int(round(size)))
    if k not in _FONTS:
        hit = _face(face)
        size = max(4, int(round(size)))
        _FONTS[k] = ImageFont.truetype(hit[0], size, index=hit[1]) if hit else ImageFont.load_default(size)
    return _FONTS[k]


def cap_ratio(face):
    """cap height / font size for a face (the height of H, or of 国 for Chinese)"""
    if face not in _CAP:
        f = font(face, 200)
        ch = '国' if face.startswith('cjk') else 'H'
        b = f.getbbox(ch, anchor='ls')
        _CAP[face] = max(0.3, -b[1] / 200)
    return _CAP[face]


# ---------------------------------------------------------------- small array helpers
def _paste(dst, a, x, y):
    """paste array a into dst with its top-left at (x, y), clipped"""
    h, w = a.shape[:2]
    H, W = dst.shape[:2]
    ys, xs, ye, xe = max(0, y), max(0, x), min(H, y + h), min(W, x + w)
    if ye > ys and xe > xs:
        dst[ys:ye, xs:xe] = a[ys - y:ye - y, xs - x:xe - x]


def _box3(a):
    p = np.pad(a, 1, mode='edge')
    h, w = a.shape
    return sum(p[i:i + h, j:j + w] for i in range(3) for j in range(3)) / 9


def _erode(a, r):
    if r <= 0: return a
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MinFilter(2 * int(r) + 1)), np.float32) / 255


def _dilate(a, r):
    if r <= 0: return a
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * int(r) + 1)), np.float32) / 255


def _phi_table():
    z = np.linspace(0, 4.5, 400)
    # Abramowitz & Stegun 7.1.26 erf
    x = z / np.sqrt(2)
    t = 1 / (1 + 0.3275911 * x)
    erf = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-x * x)
    return 0.5 * (1 + erf), z


_PHI, _Z = _phi_table()


def _inner_dist(mask, sigma):
    """approximate distance (px) from each inside pixel to the shape's edge, valid up to ~3 sigma"""
    b = blur(mask, sigma)
    return (np.interp(np.clip(b, 0.5, 0.99999), _PHI, _Z) * sigma).astype(np.float32)


def _closed_spline(pts, per=10):
    P = np.asarray(pts, np.float32)
    n = len(P)
    ext = np.vstack([P[-1:], P, P[:2]])
    out = []
    for i in range(1, n + 1):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out, np.float32)


def _hash(i, seed):
    """per-integer pseudo-random in [-1, 1] (for per-line jitter of hatching)"""
    x = (np.asarray(i, np.int64) * 374761393 + seed * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x & 0xFFFF) / 32767.5 - 1).astype(np.float32)


class Letterpress:
    def __init__(self, W=1920, H=1080, seed=0, misreg=3.2):
        """misreg: typical registration error between the formes, px (one pass of the sheet per ink)"""
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.misreg = misreg
        self.salt = 1.0                                                     # how much bare tooth shows in solids
        self.paper_col = _c(PAPER)
        self.img = np.ones((H, W, 3), np.float32) * self.paper_col
        self.stock = self.img.copy()                                        # bare paper, for ink that cracks off
        self.fibre = np.ones((H, W), np.float32)
        self.light = np.ones((H, W), np.float32)
        self.impress = np.zeros((H, W), np.float32)
        self.tooth = np.full((H, W), 0.5, np.float32)
        self.plates = {}
        self._layer = 'main'
        self.stages = []
        self.wob = (noise2d(H // 4, W // 4, 18, 3, self._seed()) - 0.5)          # hand wobble of cut lines
        self.wob = np.asarray(Image.fromarray(self.wob).resize((W, H), Image.BICUBIC), np.float32)

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ the stock
    def paper(self, colour=PAPER, warm=AGED, tone=0.5):
        """cheap toned poster stock: cloudy cream with warmer patches, fibres, flecks, tooth, a sheet that is not
        quite flat. tone: how far it has already yellowed (0 fresh .. 1 brown)"""
        H, W, r = self.H, self.W, self.rng
        self.paper_col = _c(colour)
        cloud = noise2d(H, W, 300, 4, self._seed())
        t = (smoothstep(0.3, 0.95, cloud) * (0.18 + 0.25 * tone))[..., None]
        base = self.paper_col * (1 - t) + _c(warm) * t
        base = base * (1 + 0.02 * (noise2d(H, W, 40, 3, self._seed()) - 0.5))[..., None]
        self.img = base.astype(np.float32)
        fim = Image.new('L', (W, H), 128)
        d = ImageDraw.Draw(fim)
        for _ in range(int(W * H / 520)):
            x, y = r.uniform(0, W), r.uniform(0, H)
            a, L = r.uniform(0, np.pi), r.uniform(4, 22)
            bend = r.normal(0, 0.3)
            pts = [(x + np.cos(a + bend * s) * L * s, y + np.sin(a + bend * s) * L * s) for s in np.linspace(-0.5, 0.5, 5)]
            d.line(pts, fill=int(128 + r.choice([-1, 1], p=[0.6, 0.4]) * r.uniform(10, 34)), width=1)
        fib = blur((np.asarray(fim, np.float32) - 128) / 128, 0.55)
        fine = blur(r.random((H, W)).astype(np.float32), 0.6)
        fine = (fine - fine.mean()) / (fine.std() + 1e-6)
        self.fibre = (1 + 0.06 * fib + 0.008 * fine).astype(np.float32)
        fl = Image.new('L', (W * 2, H * 2), 0)
        d = ImageDraw.Draw(fl)
        for _ in range(int(W * H / 5000)):
            x, y = r.uniform(0, W * 2), r.uniform(0, H * 2)
            rr = r.uniform(0.6, 2.4) * (3 if r.random() < 0.05 else 1)
            d.ellipse((x - rr, y - rr * r.uniform(0.4, 1), x + rr, y + rr * r.uniform(0.4, 1)), fill=int(r.uniform(60, 190)))
        fl = np.asarray(fl.resize((W, H), Image.BOX), np.float32) / 255
        self.img *= (1 - fl[..., None] * (1 - _c('#5e4630')))
        g = r.random((H, W)).astype(np.float32)
        c = noise2d(H, W, 5.0, 2, self._seed())
        tt = 0.85 * (g - 0.5) / 0.29 + 0.6 * (c - c.mean()) / (c.std() + 1e-6)
        self.tooth = np.clip(0.5 + tt / 4.0, 0, 1).astype(np.float32)          # 1 = the deepest pits
        cockle = noise2d(H, W, 420, 2, self._seed()) - 0.5
        grad = 1 + 0.03 * (0.5 - (self.XX / W * 0.6 + self.YY / H * 0.4))
        self.light = (grad + 0.03 * cockle).astype(np.float32)
        self.stock = self.img.copy()

    # ------------------------------------------------------------ formes
    def _plate(self, ink):
        if ink in self.plates: return self.plates[ink]
        r = self.rng
        n = len(self.plates)
        a = r.uniform(0, 2 * np.pi)
        mag = 0.0 if n == 0 and ink == BLACK else self.misreg * r.uniform(0.7, 1.0)
        P = dict(layers={}, film=np.ones((self.H, self.W), np.float32),
                 off=(float(np.cos(a) * mag), float(np.sin(a) * mag)), rot=float(r.normal(0, 0.05)),
                 seed=self._seed())
        self.plates[ink] = P
        return P

    def register(self, ink, dx, dy, rot=0.0):
        """set a forme's registration error by hand: shift (px) and rotation (degrees ccw)"""
        P = self._plate(ink)
        P['off'], P['rot'] = (float(dx), float(dy)), float(rot)

    def layer(self, name):
        """with lp.layer('hatch'): ... -- what is locked inside goes into a named part of each forme, so a stage
        can press the key lines before the hatching (press(ink, only=[...])). clear() cuts through every part."""
        lp = self

        class _L:
            def __enter__(s):
                s.prev = lp._layer
                lp._layer = name

            def __exit__(s, *a):
                lp._layer = s.prev
        return _L()

    def _mask(self, ink, name=None):
        P = self._plate(ink)
        name = name or self._layer
        if name not in P['layers']:
            P['layers'][name] = np.zeros((self.H, self.W), np.float32)
        return P['layers'][name]

    def lock(self, mask, ink=BLACK, film=None):
        """lock any mask into a forme (it prints at the next press of that ink); film scales the ink locally"""
        P = self._plate(ink)
        M = self._mask(ink)
        np.maximum(M, mask, out=M)
        if film is not None:
            sel = mask > 0.02
            P['film'][sel] = np.minimum(P['film'][sel], film[sel] if np.ndim(film) else film)

    def clear(self, mask, ink=BLACK, keep=0.0):
        """cut away: whatever is on the forme under `mask` no longer prints (woodcut highlights, overlaps)"""
        P = self._plate(ink)
        for M in P['layers'].values():
            M *= 1 - np.clip(mask, 0, 1) * (1 - keep)

    def _affine(self, a, P):
        dx, dy = P['off']
        t = np.deg2rad(P['rot'])
        c, s = np.cos(t), np.sin(t)
        cx, cy = self.W / 2, self.H / 2
        # output (x, y) samples input at R^-1 (x - c - d) + c
        A, B = c, -s
        D, E = s, c
        C = cx - A * (cx + dx) - B * (cy + dy)
        F = cy - D * (cx + dx) - E * (cy + dy)
        im = Image.fromarray(a.astype(np.float32), 'F')
        return np.asarray(im.transform((self.W, self.H), Image.AFFINE, (A, B, C, D, E, F), resample=Image.BILINEAR),
                          np.float32)

    def press(self, ink, density=1.0, only=None):
        """one impression: print everything locked on the `ink` forme since its last press, then clear the forme.
        only=[layer names] prints just those parts of the forme (and keeps the rest locked).
        Stiff oil ink: ragged edge at the scale of the paper tooth, a squeezed darker rim, starved mottled solids
        with bare pits (salt), dust dropouts; nearly opaque, multiplies a little with what is under it."""
        P = self._plate(ink)
        names = [k for k in P['layers'] if only is None or k in only]
        if not names: return
        m = np.maximum.reduce([P['layers'][k] for k in names]) if len(names) > 1 else P['layers'][names[0]]
        rows, cols = np.flatnonzero(m.max(1) > 0.002), np.flatnonzero(m.max(0) > 0.002)
        if not len(rows): return
        r = np.random.default_rng(P['seed'] + 17 * len(self.stages))
        mm = np.clip(self._affine(m, P), 0, 1)
        film = self._affine(P['film'] - 1, P) + 1 if P['film'].min() < 1 else 1.0
        pad = int(self.misreg * 2 + 14)
        y0, y1 = max(0, rows[0] - pad), min(self.H, rows[-1] + pad + 1)
        x0, x1 = max(0, cols[0] - pad), min(self.W, cols[-1] + pad + 1)
        sl = (slice(y0, y1), slice(x0, x1))
        mm = mm[sl]
        h, w = mm.shape
        if not np.isscalar(film): film = film[sl]
        fine = blur(r.random((h, w)).astype(np.float32), 0.9)
        fine = np.clip(0.5 + (fine - fine.mean()) / (fine.std() + 1e-6) * 0.2, 0, 1)
        mott = noise2d(h, w, 26, 3, int(r.integers(1 << 30)))                 # the roller's mottle ...
        roller = noise2d(h, w, 380, 2, int(r.integers(1 << 30)))              # ... and its uneven charge
        # dust on the forme: round dropouts
        dim = Image.new('L', (w * 2, h * 2), 0)
        d = ImageDraw.Draw(dim)
        for _ in range(int(w * h / 9000 * density)):
            x, y, rr = r.uniform(0, w * 2), r.uniform(0, h * 2), r.uniform(0.9, 3.4) * (2.4 if r.random() < 0.06 else 1)
            d.ellipse((x - rr, y - rr * r.uniform(0.6, 1), x + rr, y + rr), fill=int(r.uniform(150, 255)))
        dust = np.asarray(dim.resize((w, h), Image.BOX), np.float32) / 255
        del dim
        col = _c(ink)[None, None, :]
        mul = np.clip(col / self.paper_col, 0, 1.2)
        op = OPACITY.get(ink, 0.85)
        B, M = 240, 24                                                         # row bands keep the memory down
        for b0 in range(0, h, B):
            b1 = min(h, b0 + B)
            a0, a1 = max(0, b0 - M), min(h, b1 + M)
            k0, k1 = b0 - a0, b1 - a0
            mmb = mm[a0:a1]
            mb = _box3(mmb)
            e = mb + (fine[a0:a1] - 0.5) * 0.28 + 0.04                         # ink squeezes a hair past the edge
            rag = smoothstep(0.32, 0.68, e) * np.clip(mb * 3, 0, 1)
            thick = smoothstep(0.5, 0.85, blur(mmb, 2.0))                      # hairlines keep their own edge
            m2 = mmb * (1 - thick) + rag * thick
            # the roller: big solids starve, mottle, show salt; the edge of a solid squeezes a darker rim
            interior = smoothstep(0.86, 0.995, blur(mmb, 5.0))
            mo = mott[a0:a1]
            thin = 0.10 * interior * (mo - 0.35) + 0.07 * (roller[a0:a1] - 0.5)
            salt = (smoothstep(0.975, 1.03, self.tooth[y0 + a0:y0 + a1, x0:x1] + interior * 0.07 * mo * mo)
                    * (0.35 + 0.65 * interior) * self.salt)
            rim = np.clip(m2 - blur(m2, 1.6), 0, 1)
            fb = film if np.isscalar(film) else np.clip(film[a0:a1], 0, 1)
            cov = m2 * fb * density * (1 - thin) * (1 - salt) * (1 - dust[a0:a1] * 0.95)
            cov = np.clip(cov * (1 + 0.12 * rim), 0, 1)[k0:k1, :, None]
            rows_ = slice(y0 + b0, y0 + b1)
            cur = self.img[rows_, x0:x1]
            T = cur * (1 - cov + cov * mul)                                     # the transparent part multiplies
            O = cur * (1 - cov) + cov * col                                     # the pigment part covers
            self.img[rows_, x0:x1] = T * (1 - op) + O * op
            np.maximum(self.impress[rows_, x0:x1], m2[k0:k1], out=self.impress[rows_, x0:x1])
        for k in names:
            del P['layers'][k]
        if not P['layers']:
            P['film'][:] = 1

    # ------------------------------------------------------------ wood type
    def type_line(self, s, x0, x1, base, cap, face='clarendon', ink=BLACK, align='justify', stretch=None,
                  track=0.0, shade=None, inline=None, wear=0.35, grain=0.5, limits=(0.62, 1.7)):
        """set one line of wood type with its baseline at `base` and capitals `cap` px tall.
        align='justify' fills x0..x1 exactly: the face is condensed / extended (within `limits`) and the rest is
        letter-spacing. stretch fixes the width factor; track adds px between letters.
        shade=(dx, dy, ink, gap): a drop shade on another forme, offset (dx, dy), with a gap of white.
        inline=(inset, width): a white line cut down the middle of each stroke.
        wear: nicks, dents and splits of old blocks (0..1). grain: how much the wood grain prints.
        Returns dict(x0, x1, top, base, boxes=[(x0, y0, x1, y1) per letter])."""
        size = cap / cap_ratio(face)
        f = font(face, size * SS)
        chars = list(s)
        n = len(chars)
        adv = [f.getlength(ch) / SS for ch in chars]
        ink_l = [(f.getbbox(ch, anchor='ls') if not ch.isspace() else (0, 0, f.getlength(ch), 0)) for ch in chars]
        lb = ink_l[0][0] / SS
        rb = adv[-1] - ink_l[-1][2] / SS
        nat = sum(adv) - lb - rb
        meas = x1 - x0
        if align == 'justify':
            k = stretch or float(np.clip((meas - track * (n - 1)) / max(nat, 1), *limits))
            gap = (meas - nat * k) / max(n - 1, 1)
            pen = x0 - lb * k
        else:
            k = stretch or 1.0
            gap = track
            total = nat * k + gap * (n - 1)
            start = {'left': x0, 'center': (x0 + x1 - total) / 2, 'right': x1 - total}[align]
            pen = start - lb * k
        r = self.rng
        P = self._plate(ink)
        pad = int(cap * 0.3 + 6)
        top = int(base - cap * 1.35) - pad
        hl = int(cap * 1.75) + 2 * pad
        lx0 = int(pen) - pad
        lw = int(sum(adv) * k + gap * n + 2 * pad + 8)
        G = np.zeros((hl, lw), np.float32)
        FILM = np.ones((hl, lw), np.float32)
        INL = np.zeros((hl, lw), np.float32)
        boxes = []
        for i, ch in enumerate(chars):
            if ch.isspace():
                pen += adv[i] * k + gap
                continue
            bb = ink_l[i]
            gw = int(np.ceil((bb[2] - bb[0]) + 8 * SS))
            gh = int(np.ceil((bb[3] - bb[1]) + 8 * SS))
            im = Image.new('L', (gw, gh), 0)
            ImageDraw.Draw(im).text((4 * SS - bb[0], 4 * SS - bb[1]), ch, font=f, fill=255, anchor='ls')
            tw, th = max(1, int(round(gw * k / SS))), max(1, int(round(gh / SS)))
            g = np.asarray(im.resize((tw, th), Image.LANCZOS), np.float32) / 255
            g = np.clip(g, 0, 1)
            # where the glyph lands: its ink box starts at pen + bb[0]/SS*k
            gx = pen + (bb[0] / SS - 4) * k
            jit = r.normal(0, 0.35 + cap * 0.004)
            gy = base + bb[1] / SS - 4 + jit
            ix, iy = int(round(gx)) - lx0, int(round(gy)) - top
            g, film, inl = self._block(g, cap, wear, grain, inline, r)
            ys, xs = max(0, iy), max(0, ix)
            ye, xe = min(hl, iy + th), min(lw, ix + tw)
            if ye > ys and xe > xs:
                sub = (slice(ys, ye), slice(xs, xe))
                gg = g[ys - iy:ye - iy, xs - ix:xe - ix]
                np.maximum(G[sub], gg, out=G[sub])
                FILM[sub] = np.where(gg > 0.02, np.minimum(FILM[sub], film[ys - iy:ye - iy, xs - ix:xe - ix]), FILM[sub])
                if inl is not None:
                    np.maximum(INL[sub], inl[ys - iy:ye - iy, xs - ix:xe - ix], out=INL[sub])
            boxes.append((lx0 + ix, top + iy, lx0 + ix + tw, top + iy + th))
            pen += adv[i] * k + gap
        Gp = np.clip(G - INL, 0, 1)
        full = self._place(Gp, lx0, top)
        fullf = self._place(FILM, lx0, top, fill=1.0)
        self.lock(full, ink, fullf)
        if shade:
            dx, dy, sink, sgap = shade
            steps = int(max(abs(dx), abs(dy)))
            S = np.zeros_like(G)
            for t in range(1, steps + 1):
                np.maximum(S, shift(G, dx * t / steps, dy * t / steps), out=S)
            S = np.clip(S - _dilate(G, sgap), 0, 1)
            self.lock(self._place(S, lx0, top), sink)
        return dict(x0=x0, x1=x1, top=base - cap, base=base, boxes=boxes, stretch=k)

    def _block(self, g, cap, wear, grain, inline, r):
        """one piece of wood type: grain streaks, an end that prints light, dents, nicks, a rare split"""
        h, w = g.shape
        film = np.full((h, w), r.uniform(0.9, 1.0), np.float32)
        if grain > 0 and h > 8 and w > 8:
            gh, gw = max(2, h // 3), max(2, int(w / max(20, cap * 0.9)) + 2)
            st = np.asarray(Image.fromarray(r.random((gh, gw)).astype(np.float32)).resize((w, h), Image.BICUBIC), np.float32)
            fine = np.asarray(Image.fromarray(r.random((max(2, h // 2), max(2, w // 30) + 2)).astype(np.float32))
                              .resize((w, h), Image.BICUBIC), np.float32)
            streak = smoothstep(0.55, 0.85, st) * 0.6 + smoothstep(0.6, 0.9, fine) * 0.4
            film *= 1 - grain * 0.16 * streak
        a = r.uniform(0, 2 * np.pi)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        ramp = ((xx - w / 2) * np.cos(a) + (yy - h / 2) * np.sin(a)) / (max(w, h) / 2 + 1)
        film *= 1 - r.uniform(0.0, 0.10) * np.clip(ramp, 0, 1)                  # not quite type-high at one end
        if wear > 0 and cap > 40:
            for _ in range(r.poisson(wear * 2.2)):                               # dents: soft pale spots
                cx, cy, rr = r.uniform(0, w), r.uniform(0, h), r.uniform(0.03, 0.09) * cap
                film *= 1 - r.uniform(0.15, 0.35) * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * rr * rr))
        inl = None
        if inline:
            inset, width = inline
            e1 = _erode(g, inset)
            e2 = _erode(g, inset + width)
            inl = np.clip(e1 - e2, 0, 1)
        if wear > 0:
            edge = (g > 0.5) & (_erode(g, 1) < 0.5)
            ey, ex = np.nonzero(edge)
            if len(ey):
                n = r.poisson(wear * (2 + len(ey) / 220))
                im = Image.fromarray((g * 255).astype(np.uint8))
                d = ImageDraw.Draw(im)
                for _ in range(n):
                    j = int(r.integers(len(ey)))
                    rr = r.uniform(0.8, 1.6 + cap * 0.012)
                    d.ellipse((ex[j] - rr, ey[j] - rr * r.uniform(0.6, 1), ex[j] + rr, ey[j] + rr), fill=0)
                if cap > 60 and r.random() < wear * 0.22:                        # a split along the grain
                    y = r.uniform(h * 0.2, h * 0.8)
                    pts = [(x, y + r.normal(0, 0.8) + (x - w / 2) * r.normal(0, 0.03)) for x in np.linspace(0, w, 7)]
                    d.line(pts, fill=0, width=max(1, int(round(cap * 0.012))))
                g = np.asarray(im, np.float32) / 255
        return g, film, inl

    def type_width(self, s, cap, face='clarendon', stretch=1.0, track=0.0):
        """natural width of a line of wood type (ink edges, no justification)"""
        f = font(face, cap / cap_ratio(face) * SS)
        b0 = f.getbbox(s[0], anchor='ls')[0] / SS
        rb = f.getlength(s[-1]) / SS - f.getbbox(s[-1], anchor='ls')[2] / SS
        return (f.getlength(s) / SS - b0 - rb) * stretch + track * (len(s) - 1)

    # ------------------------------------------------------------ metal type, rules, ornaments
    def text_mask(self, s, x, y, size, face='roman', anchor='ls', spacing=0.0, rot=0.0, stretch=1.0):
        """small metal type -> full-canvas mask. anchor as in Pillow (l/m/r + a/t/m/s/b); size is the font size"""
        f = font(face, size * SS)
        adv = [f.getlength(ch) + spacing * SS for ch in s]
        total = (sum(adv) - spacing * SS) / SS * stretch
        asc, desc = f.getmetrics()
        W2 = int(total * SS / stretch + size * SS * 1.2 + 8)
        H2 = int((asc + desc) * 1.4 + 8)
        im = Image.new('L', (W2, H2), 0)
        d = ImageDraw.Draw(im)
        ox, oy = int(size * SS * 0.6), int(asc * 1.2)
        cx = ox
        for ch, a in zip(s, adv):
            d.text((cx, oy), ch, font=f, fill=255, anchor='ls')
            cx += a
        tw = max(1, int(round(W2 / SS * stretch)))
        a = np.asarray(im.resize((tw, max(1, H2 // SS)), Image.LANCZOS), np.float32) / 255
        capH = -f.getbbox('H', anchor='ls')[1] / SS
        dy = {'s': 0, 'a': -asc / SS, 't': capH, 'm': capH / 2, 'b': -desc / SS, 'd': -desc / SS}[anchor[1]]
        px = x - total * {'l': 0, 'm': 0.5, 'r': 1}[anchor[0]] - ox / SS * stretch
        py = y + dy - oy / SS
        if rot:
            R = int(np.hypot(*a.shape) + abs(px - x) + abs(py - y)) + 4
            ox, oy = int(round(x)) - R, int(round(y)) - R
            big = np.zeros((2 * R, 2 * R), np.float32)
            _paste(big, a, int(round(px)) - ox, int(round(py)) - oy)
            bim = Image.fromarray(big, 'F').rotate(rot, resample=Image.BICUBIC, center=(x - ox, y - oy))
            return self._place(np.clip(np.asarray(bim, np.float32), 0, 1), ox, oy)
        return self._place(a, int(round(px)), int(round(py)))

    def text(self, s, x, y, size, face='roman', ink=BLACK, anchor='ls', spacing=0.0, rot=0.0, stretch=1.0):
        """set a line of small metal type (cleaner than wood type) and lock it on the forme; returns its width"""
        m = self.text_mask(s, x, y, size, face, anchor, spacing, rot, stretch)
        self.lock(m, ink)
        return self.text_width(s, size, face, spacing) * stretch

    def text_width(self, s, size, face='roman', spacing=0.0):
        f = font(face, size * SS)
        return (sum(f.getlength(ch) for ch in s) / SS + spacing * (len(s) - 1))

    def rule(self, x0, x1, y, kind='single', ink=BLACK, weight=3.0, joints=260):
        """brass rule from x0 to x1 at y. kind: single | double | thick_thin | thin_thick | dotted.
        Long rules are made of several pieces of brass: tiny gaps and 1 px steps at the joints."""
        r = self.rng
        parts = {'single': [(0, weight)], 'double': [(-weight * 1.1, weight * 0.6), (weight * 1.1, weight * 0.6)],
                 'thick_thin': [(-weight * 0.9, weight * 1.5), (weight * 1.35, weight * 0.45)],
                 'thin_thick': [(-weight * 1.35, weight * 0.45), (weight * 0.9, weight * 1.5)]}
        m = np.zeros((self.H, self.W), np.float32)
        if kind == 'dotted':
            n = int((x1 - x0) / (weight * 3.2))
            for xx in np.linspace(x0, x1, n):
                m = np.maximum(m, self._disc(xx, y, weight * 0.62))
            self.lock(m, ink)
            return m
        cuts = [x0]
        while cuts[-1] + joints < x1 - joints * 0.4:
            cuts.append(cuts[-1] + joints * r.uniform(0.8, 1.2))
        cuts.append(x1)
        for (a, b) in zip(cuts[:-1], cuts[1:]):
            step = r.choice([-0.6, 0, 0, 0.6])
            for off, wdt in parts[kind]:
                yy = y + off + step
                g = 0.8 if b < x1 else 0
                m = np.maximum(m, np.clip(np.minimum(self.XX - a, b - g - self.XX) + 0.5, 0, 1)
                               * np.clip(wdt / 2 - np.abs(self.YY - yy) + 0.5, 0, 1))
        self.lock(m, ink)
        return m

    def leaders(self, x0, x1, y, size=4.0, gap=14.0, ink=BLACK):
        """a row of leader dots between a name and its detail"""
        n = max(1, int((x1 - x0) / gap))
        m = np.zeros((self.H, self.W), np.float32)
        for xx in np.linspace(x0, x1, n + 1):
            m = np.maximum(m, self._disc(xx, y, size / 2))
        self.lock(m, ink)

    def star(self, cx, cy, r, ink=RED, points=5, inner=0.4, rot=90.0):
        """a printer's star (metal ornament)"""
        t = np.deg2rad(rot) + np.arange(points * 2) * np.pi / points
        rr = np.where(np.arange(points * 2) % 2 == 0, r, r * inner)
        pts = np.stack([cx + np.cos(t) * rr, cy - np.sin(t) * rr], 1)
        m = self.poly(pts)
        self.lock(m, ink)
        return m

    def ornament(self, ch, cx, cy, size, ink=BLACK, rot=0.0):
        """a printer's flower from the ornament font (Bodoni Ornaments on macOS); a star where it is missing"""
        if _face('ornament') is None:
            return self.star(cx, cy, size * 0.4, ink)
        m = self.text_mask(ch, cx, cy, size, 'ornament', anchor='mm', rot=rot)
        self.lock(m, ink)
        return m

    def border(self, x0, y0, x1, y1, ink=BLACK, weight=4.0, corners=True):
        """a thick-and-thin rule box with square corner pieces, the frame of a bill"""
        for (yy, flip) in [(y0, False), (y1, True)]:
            self.rule(x0, x1, yy, 'thin_thick' if flip else 'thick_thin', ink, weight)
        m = np.zeros((self.H, self.W), np.float32)
        for xx, flip in [(x0, False), (x1, True)]:
            o1, o2 = (-weight * 0.9, weight * 1.35) if not flip else (weight * 0.9, -weight * 1.35)
            for off, wdt in [(o1, weight * 1.5), (o2, weight * 0.45)]:
                m = np.maximum(m, np.clip(wdt / 2 - np.abs(self.XX - (xx + off)) + 0.5, 0, 1)
                               * np.clip(np.minimum(self.YY - y0, y1 - self.YY) + 0.5, 0, 1))
        self.lock(m, ink)
        if corners:
            s = weight * 4.2
            for (cx, cy) in [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]:
                sq = self.rect(cx - s, cy - s, cx + s, cy + s)
                self.clear(sq, ink)
                self.lock(np.clip(sq - self.rect(cx - s + weight, cy - s + weight, cx + s - weight, cy + s - weight), 0, 1)
                          + self._disc(cx, cy, s * 0.42), ink)

    # ------------------------------------------------------------ shapes (full-canvas masks, 0..1)
    def _place(self, a, x0, y0, fill=0.0):
        out = np.full((self.H, self.W), fill, np.float32)
        h, w = a.shape
        ys, xs = max(0, y0), max(0, x0)
        ye, xe = min(self.H, y0 + h), min(self.W, x0 + w)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = a[ys - y0:ye - y0, xs - x0:xe - x0]
        return out

    def _disc(self, cx, cy, r):
        x0, y0 = int(cx - r - 2), int(cy - r - 2)
        n = int(2 * r + 5)
        yy, xx = np.mgrid[y0:y0 + n, x0:x0 + n].astype(np.float32)
        return self._place(np.clip(r - np.hypot(xx - cx, yy - cy) + 0.5, 0, 1), x0, y0)

    def poly(self, pts, ss=3):
        """filled polygon mask (supersampled)"""
        P = np.asarray(pts, np.float64)
        x0, y0 = int(np.floor(P[:, 0].min())) - 2, int(np.floor(P[:, 1].min())) - 2
        x1, y1 = int(np.ceil(P[:, 0].max())) + 2, int(np.ceil(P[:, 1].max())) + 2
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P], fill=255)
        a = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return self._place(a, x0, y0)

    def shape(self, pts, per=10):
        """closed smooth shape through control points (Catmull-Rom) -> mask"""
        return self.poly(_closed_spline(pts, per))

    def rect(self, x0, y0, x1, y1):
        return (np.clip(np.minimum(self.XX - x0, x1 - self.XX) + 0.5, 0, 1)
                * np.clip(np.minimum(self.YY - y0, y1 - self.YY) + 0.5, 0, 1))

    def ellipse(self, cx, cy, rx, ry, rot=0.0, a0=0.0, a1=360.0, n=120):
        """ellipse (or a pie slice from a0 to a1, degrees ccw) as a mask"""
        t = np.deg2rad(np.linspace(a0, a1, n))
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        x, y = np.cos(t) * rx, -np.sin(t) * ry
        pts = np.stack([cx + x * c + y * s, cy - x * s + y * c], 1)
        if a1 - a0 < 360: pts = np.vstack([[cx, cy], pts])
        return self.poly(pts)

    @staticmethod
    def outline_pts(path, widths, cap=True):
        """polygon around a centre-line `path` (N x 2) with per-point widths (N,) -- limbs, trunks, ropes"""
        P = np.asarray(path, np.float32)
        wd = np.asarray(widths, np.float32)
        d = np.gradient(P, axis=0)
        d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        L = P + nrm * wd[:, None] / 2
        R = P - nrm * wd[:, None] / 2
        pts = [L]
        if cap:
            a0 = np.arctan2(nrm[-1, 1], nrm[-1, 0])
            t = np.linspace(0, -np.pi, 9)[1:-1] + a0
            pts.append(P[-1] + np.stack([np.cos(t), np.sin(t)], 1) * wd[-1] / 2)
        pts.append(R[::-1])
        if cap:
            a0 = np.arctan2(-nrm[0, 1], -nrm[0, 0])
            t = np.linspace(0, -np.pi, 9)[1:-1] + a0
            pts.append(P[0] + np.stack([np.cos(t), np.sin(t)], 1) * wd[0] / 2)
        return np.vstack(pts)

    def tube(self, pts, w0=8.0, w1=None, per=12, widths=None):
        """a tapered tube along a smooth path (legs, trunk, tail, rope): width w0 at the start, w1 at the end"""
        path = spline(pts, per) if len(pts) > 2 else np.linspace(pts[0], pts[1], per * 2).astype(np.float32)
        if widths is None:
            widths = np.linspace(w0, w0 if w1 is None else w1, len(path))
        else:
            widths = np.interp(np.linspace(0, 1, len(path)), np.linspace(0, 1, len(widths)), widths)
        return self.poly(self.outline_pts(path, widths))

    # ------------------------------------------------------------ the woodcut
    def ramp(self, p0, p1):
        """a linear tone field: 0 at point p0, 1 at point p1 (and beyond), for darkening one side of a form"""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        t = ((self.XX - p0[0]) * dx + (self.YY - p0[1]) * dy) / (dx * dx + dy * dy + 1e-6)
        return np.clip(t, 0, 1).astype(np.float32)

    def cast(self, mask, dx, dy, onto, soft=2.0):
        """the shadow `mask` casts on `onto` when the light comes from the opposite of (dx, dy)"""
        return np.clip(blur(shift(mask, dx, dy), soft) - mask, 0, 1) * onto

    def form_tone(self, mask, soft=None, light=LIGHT, ambient=0.12, lift=1.0):
        """tone 0 (lit) .. 1 (dark) of a rounded volume filling `mask`: a blurred mask as a pillow height map,
        lit from `light`. soft: how round (px, default ~ a sixth of the shape's size)"""
        rows, cols = np.flatnonzero(mask.max(1) > 0.01), np.flatnonzero(mask.max(0) > 0.01)
        if not len(rows): return np.zeros_like(mask)
        if soft is None:
            soft = max(4.0, min(rows[-1] - rows[0], cols[-1] - cols[0]) / 6)
        pad = int(soft * 3)
        y0, y1 = max(0, rows[0] - pad), min(self.H, rows[-1] + pad + 1)
        x0, x1 = max(0, cols[0] - pad), min(self.W, cols[-1] + pad + 1)
        m = mask[y0:y1, x0:x1]
        h = blur(m, soft) * soft * 2.2 * lift
        gy, gx = np.gradient(h)
        L = np.array([light[0], light[1], 0.75], np.float32)
        L /= np.linalg.norm(L)
        nz = 1.0
        nl = (-gx * L[0] - gy * L[1] + nz * L[2]) / np.sqrt(gx * gx + gy * gy + nz * nz)
        t = np.clip(1 - (nl - ambient) / (1 - ambient), 0, 1) * m
        out = np.zeros_like(mask)
        out[y0:y1, x0:x1] = t
        return out

    def key(self, mask, width=3.5, heavy=7.5, light=LIGHT, ink=BLACK):
        """the key line: a cut outline just inside the shape, thicker on the side turned from the light"""
        sig = max(width, heavy) * 0.75
        rows, cols = np.flatnonzero(mask.max(1) > 0.01), np.flatnonzero(mask.max(0) > 0.01)
        if not len(rows): return mask * 0
        pad = int(sig * 4 + 4)
        y0, y1 = max(0, rows[0] - pad), min(self.H, rows[-1] + pad + 1)
        x0, x1 = max(0, cols[0] - pad), min(self.W, cols[-1] + pad + 1)
        m = mask[y0:y1, x0:x1]
        d = _inner_dist(m, sig)
        b = blur(m, 2.5)
        gy, gx = np.gradient(b)
        gl = np.sqrt(gx * gx + gy * gy) + 1e-6
        L = np.array(light, np.float32) / np.hypot(*light)
        facing = (-gx * L[0] - gy * L[1]) / gl                       # +1 the edge faces the light
        shadow = smoothstep(-0.2, 0.9, -facing)
        w = width + (heavy - width) * shadow
        w = w * (1 + 0.18 * self.wob[y0:y1, x0:x1] * 4)
        line = np.clip(w - d + 0.5, 0, 1) * m
        out = self._place(line, x0, y0)
        self.lock(out, ink)
        return out

    def hatch(self, mask, angle=0.0, spacing=9.0, tone=None, centre=None, aspect=1.0, lo=0.12, gain=1.0,
              wobble=1.0, ink=BLACK, solid=0.92):
        """swelling parallel hatching cut into `mask`. The lines run at `angle` (degrees ccw), or as arcs around
        `centre` (cross-contour lines on a round body; aspect squashes them). Each line's width follows `tone`
        (0..1, default form_tone(mask)): thin where it is light, fattening into solid black above `solid`,
        and petering out below `lo`, so every line ends in a hand-cut taper."""
        if tone is None: tone = self.form_tone(mask)
        rows, cols = np.flatnonzero(mask.max(1) > 0.01), np.flatnonzero(mask.max(0) > 0.01)
        if not len(rows): return mask * 0
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        X, Y = self.XX[y0:y1, x0:x1], self.YY[y0:y1, x0:x1]
        if centre is None:
            t = np.deg2rad(angle)
            v = X * np.sin(t) + Y * np.cos(t)
        else:
            v = np.sqrt((X - centre[0]) ** 2 + ((Y - centre[1]) * aspect) ** 2)
        v = v + self.wob[y0:y1, x0:x1] * spacing * 1.3 * wobble
        i = np.floor(v / spacing + 0.5)
        dist = np.abs(v - i * spacing)
        j = _hash(i.astype(np.int64), self.seed)
        tt = tone[y0:y1, x0:x1] * gain + 0.07 * j
        hw = spacing * 0.5 * np.clip((tt - lo) / max(solid - lo, 1e-3), 0, 1.05) ** 0.85
        line = np.clip(hw - dist + 0.5, 0, 1) * (hw > 0.35) * mask[y0:y1, x0:x1]
        out = self._place(line.astype(np.float32), x0, y0)
        self.lock(out, ink)
        return out

    def line(self, pts, width=3.0, taper=(0.25, 0.25), ink=BLACK, per=12):
        """a cut line along a smooth path: swells to `width`, tapers at both ends (wrinkles, folds, ropes)"""
        path = spline(pts, per) if len(pts) > 2 else np.linspace(pts[0], pts[1], per * 2).astype(np.float32)
        n = len(path)
        t = np.linspace(0, 1, n)
        prof = np.clip(np.minimum(t / max(taper[0], 1e-3), (1 - t) / max(taper[1], 1e-3)), 0, 1) ** 0.7
        w = np.maximum(width * (0.15 + 0.85 * prof), 0.6)
        m = self.poly(self.outline_pts(path, w, cap=False))
        self.lock(m, ink)
        return m

    def solid(self, mask, ink=BLACK):
        """leave the wood standing: a solid black (or red) area"""
        self.lock(np.clip(mask, 0, 1), ink)
        return mask

    def stipple(self, mask, density=0.004, size=(0.8, 2.2), ink=BLACK, tone=None):
        """dots picked out with a point (sawdust, sand, texture); density = dots per px of mask"""
        r = self.rng
        rows, cols = np.flatnonzero(mask.max(1) > 0.01), np.flatnonzero(mask.max(0) > 0.01)
        if not len(rows): return
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        h, w = y1 - y0, x1 - x0
        n = int(mask[y0:y1, x0:x1].sum() * density)
        im = Image.new('L', (w * 2, h * 2), 0)
        d = ImageDraw.Draw(im)
        for _ in range(n):
            x, y = r.uniform(0, w), r.uniform(0, h)
            p = mask[y0 + int(y), x0 + int(x)] * (1 if tone is None else tone[y0 + int(y), x0 + int(x)])
            if r.random() > p: continue
            rr = r.uniform(*size)
            d.ellipse(((x - rr) * 2, (y - rr * r.uniform(0.6, 1)) * 2, (x + rr) * 2, (y + rr) * 2), fill=255)
        a = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        self.lock(self._place(a, x0, y0), ink)

    def tint(self, mask, ink=RED, loose=2.2, grow=1.0):
        """the colour block, cut separately and a little loosely: its edge wanders off the key by ~`loose` px
        and it is cut a hair fat (`grow` px) so it runs under the black lines"""
        rows, cols = np.flatnonzero(mask.max(1) > 0.01), np.flatnonzero(mask.max(0) > 0.01)
        if not len(rows): return
        pad = int(loose * 3 + grow + 6)
        y0, y1 = max(0, rows[0] - pad), min(self.H, rows[-1] + pad + 1)
        x0, x1 = max(0, cols[0] - pad), min(self.W, cols[-1] + pad + 1)
        m = mask[y0:y1, x0:x1]
        h, w = m.shape
        dxn = noise2d(h, w, 60, 2, self._seed()) - 0.5
        dyn = noise2d(h, w, 60, 2, self._seed()) - 0.5
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        sx = np.clip(xx + dxn * loose * 4, 0, w - 1).astype(np.int32)
        sy = np.clip(yy + dyn * loose * 4, 0, h - 1).astype(np.int32)
        mw = m[sy, sx]
        if grow >= 1:
            mw = _dilate(mw, int(round(grow)))
        mw = blur(mw, 0.6)
        self.lock(self._place(np.clip(mw, 0, 1), x0, y0), ink)

    # ------------------------------------------------------------ after printing: the life of the bill
    def fold(self, axis, pos, depth=1.0, crack=0.8):
        """a crease from folding the bill: axis 'v' (vertical line at x=pos) or 'h' (horizontal at y=pos).
        The ink cracks off along the crease, dirt settles in it, and the two faces roll the light differently."""
        r = self.rng
        d = (self.XX - pos) if axis == 'v' else (self.YY - pos)
        along = self.YY if axis == 'v' else self.XX
        n = self.H if axis == 'v' else self.W
        wig = np.interp(along, np.arange(n), fbm1d(n, 120, 3, self._seed()) * 1.6)
        d = d + wig
        sgn = r.choice([-1, 1])
        self.light *= (1 + depth * 0.05 * sgn * np.tanh(d / 3.0) * np.exp(-np.abs(d) / 55.0)
                       - depth * 0.05 * np.exp(-(d / 2.2) ** 2))
        # ink cracked off the ridge
        nz = noise2d(self.H, self.W, 7, 2, self._seed())
        band = np.exp(-(d / 1.6) ** 2) * smoothstep(0.42, 0.62, nz) * crack
        printed = np.clip(self.impress, 0, 1)
        loss = (band * printed)[..., None]
        self.img = self.img * (1 - loss * 0.85) + self.stock * loss * 0.85
        dirt = np.exp(-(d / 1.3) ** 2) * (0.5 + 0.5 * nz) * 0.16 * depth
        self.img *= (1 - dirt[..., None] * (1 - _c('#6b5236')))

    def tone_edges(self, amount=1.0, width=70.0, colour='#a87c45'):
        """paper browns from the edges in (light and air), and a little everywhere in uneven patches"""
        e = np.minimum(np.minimum(self.XX, self.W - 1 - self.XX), np.minimum(self.YY, self.H - 1 - self.YY))
        nz = noise2d(self.H, self.W, 90, 3, self._seed())
        e = e + (nz - 0.5) * width * 0.9
        t = np.clip(np.exp(-np.maximum(e, 0) / width) * 0.55 + smoothstep(0.55, 0.95, noise2d(self.H, self.W, 260, 3, self._seed())) * 0.16, 0, 1)
        t = (t * amount)[..., None]
        self.img = self.img * (1 - t * (1 - _c(colour) / np.maximum(self.paper_col, 1e-3) * 0.95))
        self.stock = self.stock * (1 - t * (1 - _c(colour) / np.maximum(self.paper_col, 1e-3) * 0.95))

    def foxing(self, n=160, colour='#9a6436', clusters=6):
        """foxing: rust-brown spots in the paper, in loose clusters, the larger ones with a darker tide-line ring"""
        r = self.rng
        W, H = self.W, self.H
        im = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(im)
        cs = [(r.uniform(0, W), r.uniform(0, H), r.uniform(60, 240)) for _ in range(clusters)]
        for k in range(n):
            if r.random() < 0.7:
                cx, cy, s = cs[int(r.integers(len(cs)))]
                x, y = cx + r.normal(0, s), cy + r.normal(0, s * 0.7)
            else:
                x, y = r.uniform(0, W), r.uniform(0, H)
            rr = r.uniform(0.8, 3.0) * (r.uniform(2, 4.5) if r.random() < 0.12 else 1)
            a = int(r.uniform(50, 150))
            d.ellipse((x - rr, y - rr * r.uniform(0.6, 1), x + rr, y + rr), fill=a)
            if rr > 4:
                d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=min(255, a + 60), width=1)
        f = blur(np.asarray(im, np.float32) / 255, 0.9)[..., None]
        self.img = self.img * (1 - f * (1 - _c(colour)))

    def stain(self, cx, cy, rx, ry, strength=0.10, colour='#a07a48'):
        """a water stain: a faint browned patch with a darker, wandering tide line"""
        t = np.linspace(0, 2 * np.pi, 140, endpoint=False)
        wob = 1 + 0.18 * fbm1d(140, 25, 4, self._seed())
        pts = np.stack([cx + np.cos(t) * rx * wob, cy + np.sin(t) * ry * wob], 1)
        m = blur(self.poly(pts), 6)
        ring = np.clip(m * (1 - m) * 4, 0, 1) ** 2
        a = (m * 0.35 + ring * 0.9)[..., None] * strength
        self.img = self.img * (1 - a * (1 - _c(colour)))

    def tack(self, x, y, r=4.0):
        """a tack hole: the bill was nailed up -- a torn hole showing the wall, rust bled into the paper"""
        g = self.rng
        halo = self._disc(x, y, r * 4.5)
        halo = blur(halo, r * 1.6) * (0.6 + 0.4 * noise2d(self.H, self.W, 12, 2, self._seed()))
        self.img *= (1 - (halo * 0.5)[..., None] * (1 - _c(RUST)))
        pts = [(x + np.cos(a) * r * g.uniform(0.6, 1.3), y + np.sin(a) * r * g.uniform(0.6, 1.3))
               for a in np.linspace(0, 2 * np.pi, 9, endpoint=False)]
        hole = self.poly(pts)
        for _ in range(3):                                                         # little radial tears
            a = g.uniform(0, 2 * np.pi)
            L = g.uniform(1.2, 2.6) * r
            hole = np.maximum(hole, self.poly(self.outline_pts(np.array([[x, y], [x + np.cos(a) * L, y + np.sin(a) * L]]),
                                                               np.array([1.6, 0.4]), cap=False)))
        lip = np.clip(_dilate(hole, 2) - hole, 0, 1) * 0.35
        self.img = self.img * (1 - lip[..., None] * 0.5)
        self.img = self.img * (1 - hole[..., None]) + _c(WALL) * hole[..., None]

    def nicks(self, n=8, size=(4, 14)):
        """small bites out of the sheet's edges (the wall shows through)"""
        g = self.rng
        m = np.zeros((self.H, self.W), np.float32)
        for _ in range(n):
            side = g.integers(4)
            s = g.uniform(*size)
            if side == 0: x, y = g.uniform(0, self.W), 0
            elif side == 1: x, y = g.uniform(0, self.W), self.H
            elif side == 2: x, y = 0, g.uniform(0, self.H)
            else: x, y = self.W, g.uniform(0, self.H)
            pts = [(x + np.cos(a) * s * g.uniform(0.5, 1.2), y + np.sin(a) * s * g.uniform(0.4, 1.0))
                   for a in np.linspace(0, 2 * np.pi, 11, endpoint=False)]
            m = np.maximum(m, self.poly(pts))
        lip = np.clip(_dilate(m, 2) - m, 0, 1) * 0.25
        self.img *= (1 - lip[..., None])
        self.img = self.img * (1 - m[..., None]) + _c(WALL) * m[..., None]

    def strip(self, x0, y0, x1, y1, rot=0.0, colour='#efe3c6', draw=None, ink=BLACK, misreg=(1.5, -1.0)):
        """paste a date strip over the bill: a separate slip of whiter stock printed on its own forme.
        draw(s) gets the strip as a small Letterpress (origin at the strip's top-left + 20 px margin, so the strip
        spans 20..20+w, 20..20+h) to set type on; it is pressed, rotated by `rot` and pasted. The glue darkens
        the bill around the strip, and the damp slip dries with a few wrinkles."""
        r = self.rng
        w, h = int(x1 - x0), int(y1 - y0)
        sub = Letterpress(w + 40, h + 40, seed=self._seed(), misreg=0)
        sub.paper(colour, warm='#e2cfa2', tone=0.25)
        sub.register(ink, *misreg)
        if draw is not None:
            draw(sub)
        for k in list(sub.plates):
            sub.press(k)
        sheet = sub.img * (sub.fibre * sub.light)[..., None]
        mask = np.zeros((h + 40, w + 40), np.float32)
        mask[20:20 + h, 20:20 + w] = 1
        # paper edge: slightly ragged guillotine cut
        mask = np.clip(_box3(mask) + (np.asarray(Image.fromarray(r.random((h + 40, w + 40)).astype(np.float32)), np.float32) - 0.5) * 0.15, 0, 1)
        wr = noise2d(h + 40, w + 40, 30, 2, self._seed())
        sheet = sheet * (1 + 0.035 * (wr - 0.5))[..., None]
        rgba = np.dstack([np.clip(sheet, 0, 1), mask])
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ims = [Image.fromarray(rgba[..., k].astype(np.float32), 'F').rotate(rot, resample=Image.BICUBIC, expand=True)
               for k in range(4)]
        arr = np.stack([np.asarray(i, np.float32) for i in ims], -1)
        hh, ww = arr.shape[:2]
        px, py = int(round(cx - ww / 2)), int(round(cy - hh / 2))
        a = self._place(arr[..., 3], px, py)
        glue = np.clip(_dilate(a, 3) * 1.0 - a, 0, 1)
        glue = blur(glue, 2.0) * 0.6
        self.img *= (1 - (glue * 0.35)[..., None] * (1 - _c('#8a6a3c')))
        sh = np.clip(shift(blur(a, 1.4), 1, 2) - a, 0, 1) * 0.25
        self.img *= (1 - sh[..., None])
        for k in range(3):
            ch = self._place(arr[..., k], px, py)
            self.img[..., k] = self.img[..., k] * (1 - a) + ch * a
        self.impress *= (1 - a)
        self.stock = self.stock * (1 - a[..., None]) + self.img * a[..., None]
        return a

    # ------------------------------------------------------------ output
    def composite(self):
        imp = blur(self.impress, 1.2)
        gy, gx = np.gradient(imp)
        relief = 1 + 0.10 * (gx * LIGHT[0] + gy * LIGHT[1])                      # the dent's far wall catches the light
        img = self.img * (self.fibre * self.light * relief)[..., None]
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
