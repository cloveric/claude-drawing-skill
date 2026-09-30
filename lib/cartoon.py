"""cartoon — a drawing from a hand-drawn cartoon animation (逐帧手绘 / frame by frame): brush-pen ink that boils
from frame to frame, flat colour with one or two hard cel-shadow tones, cream paper, crayon and screentone accents,
and small everyday things with faces (numpy + Pillow only).

Model: one drawing of a hand-drawn animation, made the way an animator makes it, on one sheet of cream paper.
  paper     warm cream drawing paper: a bumpy "tooth" (cold-press grain lit from the upper left, so every colour
            laid on the sheet still shows the grain), slow mottling and a few fibres. Crayon and pencil only catch
            the tops of the tooth; ink and flat colour cover it but keep its light and shade.
  rough     the animator's blue col-erase pencil. Every ink line is first sketched loosely in blue: one or two
            passes that drift off the final line, overshoot the ends and run past the start of closed shapes. The
            rough stays on the sheet under the colour, faint, the way it does on real animation drawings.
  ink       a brush pen: a line lands thin, swells, and lifts off to a point; pressure drifts along it and the
            hand wobbles slowly; closed shapes are one stroke whose two tapered ends overlap where the pen came
            back round, and they are heavier on the side away from the light (bottom right), so shapes read solid.
            Edges pick up a little of the paper tooth, so a line is never vector-clean.
  colour    flat gouache / marker fills painted slightly off the lines: every fill is shifted a few pixels and its
            edge wanders, so here it spills over a line and there it leaves a sliver of paper -- hand-coloured,
            a little mis-registered. Big fills also drift slowly in density.
  cel shade one or two hard-edged shadow tones inside a shape: the shape minus itself nudged toward the light
            (a crescent on the far side), plus white glints (tapered strokes of opaque white paint).
  accents   crayon (wax that only takes on the tooth tops, streaked along the scribble direction, with a ragged
            edge), screentone (a rotated halftone dot grid), ink hatching for contact shadows.
  things    faces (happy ^ ^ eyes and an open grin with a tongue, surprised, sleepy, smiling, blush), rubber-hose
            arms with round white gloves, 4-point sparkles, speed lines, steam wisps, scalloped puffs, starbursts,
            crumbs, emphasis ticks; display lettering (chunky rounded letters, each a little tilted and bounced,
            with an extruded shadow, a white rim light and a thick ink outline), hand-lettered notes, arrows,
            numbered badges, and blue-pencil notes in the corner of the sheet.
  boil      a hand-drawn animation is traced again for every frame, so its lines never sit still ("boiling
            line"). Every snapshot re-traces the ink through a fresh smooth displacement field of a pixel or two;
            the colour and the pencil stay where they are on the sheet, so line and colour slide against each
            other a little from frame to frame.
  occlusion things are opaque: a fill knocks out the ink and colour of whatever was drawn before it inside its
            outline (hidden lines removed), so draw back to front. Effects ('fx') and lettering ('type') are
            overlays drawn last; their knock-outs apply only when those groups are shown, so staged snapshots
            never show holes.
Groups: every mark lands in a named group chosen by its kind -- 'rough' (pencil), 'ink' (lines), 'flat' (fills),
'shade' (cel shadows, glints, blush), 'texture' (crayon, screentone, hatching), 'fx' (effects), 'type' (lettering,
notes, arrows). Methods take kind=...; `with c.group(ink='ink_bg'):` sends one kind to another group, `with
c.group('fx'):` sends everything. stage(name, show=[groups]) snapshots only those groups, so a finished drawing can
be replayed the way it was made: rough -> ink -> flat colour -> shadows -> texture -> effects -> lettering.
Lettering: chunky CJK rounded (Yuanti on macOS, Noto Sans CJK Bold on Linux, YaHei Bold on Windows) and a comic
Latin face (Chalkboard SE / Marker Felt / Comic Sans, else a rounded bold). Angles are degrees counter-clockwise.

    from cartoon import Cartoon, YELLOW, RED, WHITE
    c = Cartoon(1920, 1080, seed=3)                       # draw back to front: every fill hides what is behind it
    c.arm((1150, 640), (1300, 540), bend=0.35)            # limbs first, so the body hides the shoulder
    body = Cartoon.rrect_pts(700, 500, 1200, 850, (90, 90, 30, 30))
    c.shape(body, '#83cbbd', shade=('#57a89d', 30, 10))    # fill + cel shadow + brush outline
    c.face(950, 680, 120, 'happy')
    c.sparkle(1350, 420, 30)
    c.burst(1500, 260, 150, 110, RED)
    c.letter('POP!', 1500, 290, 90, YELLOW, anchor='m')
    c.stage('ink', show=['rough', 'ink'])
    c.save('out.png')
"""
import glob
import numpy as np
from contextlib import contextmanager
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, shift, polygon_mask, latin_font

PAPER, INK, PENCIL, WHITE = '#f0e7d5', '#231c18', '#6c9be0', '#fffbf1'
RED, YELLOW, PINK, ORANGE = '#e04a3a', '#f8cd48', '#f39486', '#f58a3c'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def darker(colour, k=0.78):
    """a cel-shadow tone of `colour`: darker and nudged a little toward violet, never grey"""
    c = _c(colour) * k
    return np.clip(c * np.array([0.98, 0.95, 1.04], np.float32) + np.array([0.01, 0, 0.02], np.float32), 0, 1)


def _resample(P, step, closed=False):
    P = np.asarray(P, np.float32)
    if closed: P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(s[-1] / step) + 1)
    ss = np.linspace(0, s[-1], n, endpoint=not closed)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


def _closed_spline(pts, per=12):
    """periodic Catmull-Rom through control points (closed smooth curve)"""
    P = np.asarray(pts, np.float32)
    n = len(P)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out, np.float32)


def _normals(P):
    T = np.gradient(P, axis=0)
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-6
    return T, np.stack([-T[:, 1], T[:, 0]], 1)


def _dilate(m, r):
    """grow a mask by about r px (alternating plus / square steps ~ an octagon)"""
    out = m
    for i in range(int(round(r))):
        o = out.copy()
        nb = ((1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (1, -1), (-1, 1), (-1, -1)) if i % 2 else ())
        for dx, dy in nb:
            np.maximum(o, shift(out, dx, dy), out=o)
        out = o
    return out


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


# ---------------------------------------------------------------- fonts (looked up on the system, never bundled)
_FONT_CANDIDATES = {
    'cjk_round': [('/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/Yuanti.ttc', 2),
                  ('/Library/Fonts/Yuanti.ttc', 2), ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0),
                  ('/usr/share/fonts/**/NotoSansSC*Bold*.[ot]tf', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0)],
    'comic': [('/System/Library/Fonts/Supplemental/ChalkboardSE.ttc', 2), ('/System/Library/Fonts/MarkerFelt.ttc', 1),
              ('/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf', 0), ('/usr/share/fonts/**/ComicNeue*Bold*.[ot]tf', 0),
              ('/usr/share/fonts/**/ComicRelief*.ttf', 0), ('C:/Windows/Fonts/comicbd.ttf', 0)],
}
_FALLBACK = {'comic': ('rounded', 'sans_bold'), 'cjk_round': ('cjk_sans', 'cjk')}
_PATHS, _FONTS, _HAS = {}, {}, {}


def _font_path(style):
    if style in _PATHS: return _PATHS[style]
    hit = None
    for pat, idx in _FONT_CANDIDATES.get(style, []):
        for p in glob.glob(pat, recursive=True):
            try:
                ImageFont.truetype(p, 20, index=idx); hit = (p, idx); break
            except OSError:
                pass
        if hit: break
    if hit is None:
        for st in _FALLBACK.get(style, (style,)):
            h = latin_font(st)
            if h: hit = h; break
    _PATHS[style] = hit
    return hit


def _font(style, size):
    key = (style, int(size))
    if key not in _FONTS:
        hit = _font_path(style)
        try:
            _FONTS[key] = ImageFont.truetype(hit[0], int(size), index=hit[1]) if hit else ImageFont.load_default(int(size))
        except OSError:
            _FONTS[key] = ImageFont.load_default(int(size))
    return _FONTS[key]


def _has(style, ch):
    """does the font for `style` have a real glyph for ch (not the .notdef box)?"""
    key = (style, ch)
    if key not in _HAS:
        f = _font(style, 40)
        try:
            a, b = f.getmask(ch), f.getmask('\U000F0000')
            _HAS[key] = a.size != b.size or bytes(a) != bytes(b)
        except Exception:
            _HAS[key] = False
    return _HAS[key]


def _pick(ch, style):
    if style is None: style = 'cjk_round' if _is_cjk(ch) else 'comic'
    if _has(style, ch): return style
    for alt in ('cjk_round', 'comic', 'cjk_sans'):
        if alt != style and _has(alt, ch): return alt
    return style


class Mask:
    """a mask cropped to its bounding box: sl = (row slice, col slice), a = values"""

    def __init__(self, sl, a):
        self.sl, self.a = sl, a


class Cartoon:
    ORDER = ('rough', 'ink', 'flat', 'shade', 'texture', 'fx', 'type')
    OVERLAY = ('fx', 'type')

    def __init__(self, W=1920, H=1080, seed=0, boil=1.8, slop=3.5, rough=True, light=(-0.55, -0.83)):
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.boil, self.slop, self.auto_rough = boil, slop, rough
        l = np.asarray(light, np.float32)
        self.light = l / np.linalg.norm(l)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.random.default_rng(seed + 991)
        g = blur(r.random((H, W)).astype(np.float32), 0.7)                 # fine grain ...
        m = noise2d(H, W, 4.5, 3, seed + 3)                                  # ... in cold-press bumps
        g = (g - g.mean()) / (g.std() + 1e-6)
        m = (m - m.mean()) / (m.std() + 1e-6)
        self.tooth = np.clip(0.5 + (0.45 * g + 0.75 * m) / 3.4, 0, 1).astype(np.float32)
        gy, gx = np.gradient(blur(0.35 * g + m, 1.0))
        s = -(gx * self.light[0] + gy * self.light[1])
        self._bump = np.clip(s / (s.std() + 1e-6), -3, 3).astype(np.float32)
        self._mott = (noise2d(H, W, 380, 3, seed + 5) - 0.5).astype(np.float32)
        self._var = noise2d(H, W, 90, 3, seed + 7)                           # slow density drift of fills
        self._wob = noise2d(H, W, 15, 2, seed + 11)                          # wandering fill edges
        self.paint, self.ink, self.pencil, self.cover = {}, {}, {}, {}
        self.created = []
        self._all, self._map = None, {}
        self.stages = []
        self.paper()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ groups and buffers
    @contextmanager
    def group(self, name=None, **kinds):
        """with c.group('fx'): every mark goes to group 'fx'; with c.group(ink='ink_bg'): only ink lines move"""
        old = (self._all, dict(self._map))
        if name: self._all = name
        self._map.update(kinds)
        try:
            yield
        finally:
            self._all, self._map = old

    def _g(self, kind):
        return self._all or self._map.get(kind, kind)

    def _prio(self, g):
        return self.ORDER.index(g) if g in self.ORDER else self.ORDER.index('texture') + 0.5

    def _new(self, g):
        if g not in self.created: self.created.append(g)

    def _pbuf(self, g):
        if g not in self.paint:
            self._new(g)
            self.paint[g] = [np.zeros((self.H, self.W, 3), np.float32), np.zeros((self.H, self.W), np.float32)]
        return self.paint[g]

    def _ibuf(self, g):
        if g not in self.ink:
            self._new(g); self.ink[g] = np.zeros((self.H, self.W), np.float32)
        return self.ink[g]

    def _rbuf(self, g):
        if g not in self.pencil:
            self._new(g); self.pencil[g] = np.zeros((self.H, self.W), np.float32)
        return self.pencil[g]

    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _region(self, shape, pad=4):
        """points (n, 2), a full-size mask or a Mask -> (slices, cropped mask)"""
        if isinstance(shape, Mask):
            y0, x0 = shape.sl[0].start, shape.sl[1].start
            h, w = shape.a.shape
            sl = self._box(x0 - pad, y0 - pad, x0 + w + pad, y0 + h + pad)
            out = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), np.float32)
            oy, ox = y0 - sl[0].start, x0 - sl[1].start
            out[oy:oy + h, ox:ox + w] = shape.a
            return sl, out
        a = np.asarray(shape, np.float32)
        if a.ndim == 2 and a.shape == (self.H, self.W):
            rows = np.flatnonzero(a.max(1) > 1e-3); cols = np.flatnonzero(a.max(0) > 1e-3)
            if not len(rows): return None, None
            sl = self._box(cols[0] - pad, rows[0] - pad, cols[-1] + 1 + pad, rows[-1] + 1 + pad)
            return sl, a[sl].copy()
        sl = self._box(a[:, 0].min() - pad, a[:, 1].min() - pad, a[:, 0].max() + pad + 1, a[:, 1].max() + pad + 1)
        if sl is None: return None, None
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        return sl, polygon_mask(h, w, a - np.array([sl[1].start, sl[0].start], np.float32), ss=2)

    def _crop(self, shape, sl):
        """any mask-like `shape` sampled on the slices sl"""
        if shape is None: return 1.0
        if isinstance(shape, Mask):
            full = np.zeros((self.H, self.W), np.float32); full[shape.sl] = shape.a
            return full[sl]
        a = np.asarray(shape, np.float32)
        if a.ndim == 2 and a.shape == (self.H, self.W): return a[sl]
        return self.mask(a)[sl]

    def mask(self, pts, ss=2):
        """filled polygon -> full-size float mask (combine masks with numpy, then pass them to any method)"""
        return polygon_mask(self.H, self.W, pts, ss)

    def _knock(self, g, sl, occ_paint, occ_ink):
        """an opaque thing: whatever was drawn before it inside its outline disappears. Overlay groups (fx, type)
        knock their own group now and everything else only when they are shown (see composite)."""
        if g in self.OVERLAY:
            cp, ci = self.cover.setdefault(g, [np.zeros((self.H, self.W), np.float32), np.zeros((self.H, self.W), np.float32)])
            cp[sl] = np.maximum(cp[sl], occ_paint); ci[sl] = np.maximum(ci[sl], occ_ink)
            targets = [g]
        else:
            targets = list(self.created)
        for t in targets:
            if t in self.paint:
                pc, pa = self.paint[t]
                pc[sl] *= (1 - occ_paint)[..., None]; pa[sl] *= 1 - occ_paint
            if t in self.ink:
                self.ink[t][sl] *= 1 - occ_ink

    def _put(self, g, sl, a, colour):
        """paint (premultiplied over); colour may be (3,) or (h, w, 3)"""
        pc, pa = self._pbuf(g)
        a = np.clip(a, 0, 1)
        col = colour if (isinstance(colour, np.ndarray) and colour.ndim == 3) else _c(colour)
        pc[sl] = pc[sl] * (1 - a[..., None]) + col * a[..., None]
        pa[sl] = pa[sl] * (1 - a) + a

    def _inkon(self, g, sl, a):
        """ink: edges pick up a little paper tooth, overlapping ink does not get darker"""
        e = 4 * a * (1 - a)
        a = np.clip(a + e * (self.tooth[sl] - 0.5) * 0.9, 0, 1)
        ia = self._ibuf(g)
        ia[sl] = 1 - (1 - ia[sl]) * (1 - a)

    # ------------------------------------------------------------ geometry helpers
    @staticmethod
    def place(pts, cx, cy, scale=1.0, rot=0.0):
        """local points (x right, y down) -> scaled, rotated counter-clockwise by rot degrees, moved to (cx, cy)"""
        P = np.asarray(pts, np.float32) * scale
        t = np.deg2rad(rot)
        c, s = np.cos(t), np.sin(t)
        return np.stack([cx + P[:, 0] * c + P[:, 1] * s, cy - P[:, 0] * s + P[:, 1] * c], 1)

    @staticmethod
    def ellipse_pts(cx, cy, rx, ry, rot=0.0, a0=0.0, a1=360.0, n=None):
        """ellipse (or an arc from a0 to a1 degrees, clockwise on screen from +x) as points"""
        full = abs(a1 - a0) >= 360
        n = n or max(24, int(abs(a1 - a0) / 360 * 2 * np.pi * max(rx, ry) / 5))
        t = np.deg2rad(np.linspace(a0, a1, n, endpoint=not full))
        return Cartoon.place(np.stack([np.cos(t) * rx, np.sin(t) * ry], 1), cx, cy, 1, rot)

    @staticmethod
    def rrect_pts(x0, y0, x1, y1, r=20, step=10):
        """rounded rectangle; r is one radius or (top-left, top-right, bottom-right, bottom-left)"""
        tl, tr, br, bl = (r,) * 4 if np.isscalar(r) else r
        out = []

        def edge(p, q):
            n = max(2, int(np.hypot(q[0] - p[0], q[1] - p[1]) / step))
            for t in np.linspace(0, 1, n, endpoint=False): out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))

        def arc(cx, cy, rr, a0):
            if rr <= 0: out.append((cx, cy)); return
            for a in np.deg2rad(np.linspace(a0, a0 + 90, max(4, int(rr / 4)), endpoint=False)):
                out.append((cx + np.cos(a) * rr, cy + np.sin(a) * rr))

        edge((x0 + tl, y0), (x1 - tr, y0)); arc(x1 - tr, y0 + tr, tr, -90)
        edge((x1, y0 + tr), (x1, y1 - br)); arc(x1 - br, y1 - br, br, 0)
        edge((x1 - br, y1), (x0 + bl, y1)); arc(x0 + bl, y1 - bl, bl, 90)
        edge((x0, y1 - bl), (x0, y0 + tl)); arc(x0 + tl, y0 + tl, tl, 180)
        return np.array(out, np.float32)

    @staticmethod
    def densify(pts, step=8, closed=True):
        """straight-edged polygon -> many points along its edges (keeps the corners sharp)"""
        P = np.asarray(pts, np.float32)
        Q = np.vstack([P, P[:1]]) if closed else P
        out = []
        for a, b in zip(Q[:-1], Q[1:]):
            n = max(1, int(np.hypot(*(b - a)) / step))
            for t in np.arange(n) / n: out.append(a + (b - a) * t)
        if not closed: out.append(Q[-1])
        return np.array(out, np.float32)

    # ------------------------------------------------------------ paper
    def paper(self, colour=PAPER, grain=1.0, mottle=1.0, fibres=260):
        """cream drawing paper; the grain (lit tooth) shows through everything painted on it"""
        H, W = self.H, self.W
        base = _c(colour)
        col = base[None, None, :] * (1 + 0.055 * mottle * self._mott)[..., None]
        col = col + np.array([0.004, 0.0, -0.006], np.float32) * self._mott[..., None] * 4
        r = np.random.default_rng(self.seed + 17)
        im = Image.new('L', (W, H), 0)
        d = ImageDraw.Draw(im)
        for _ in range(fibres):
            x, y = r.uniform(0, W), r.uniform(0, H)
            a, L = r.uniform(0, np.pi), r.uniform(8, 34)
            bend = r.uniform(-0.5, 0.5)
            pts = [(x + np.cos(a + bend * t) * L * t, y + np.sin(a + bend * t) * L * t) for t in np.linspace(0, 1, 6)]
            d.line(pts, fill=int(r.uniform(90, 200)), width=1)
        fib = blur(np.asarray(im, np.float32) / 255, 0.45)
        self.paperc = (col * (1 - 0.07 * fib[..., None])).astype(np.float32)
        self.grain = (1 + grain * (0.026 * self._bump + 0.016 * (self.tooth - 0.5))).astype(np.float32)

    # ------------------------------------------------------------ the brush pen
    def _dense(self, pts, smooth=True, closed=False, step=1.4):
        """control points -> an evenly spaced centreline (Catmull-Rom through few points, as-is for many)"""
        P = np.asarray(pts, np.float32)
        if smooth and 3 <= len(P) < 60:
            P = _closed_spline(P, 10) if closed else spline(P, per=10)
        P = _resample(P, step, closed)
        return P if len(P) >= 2 else np.vstack([P, P + 0.5])

    def _profile(self, P, width, taper=(10, 22), jitter=1.0, press=0.14, step=1.4):
        """hand wobble (slow sideways drift) and the pressure / width profile along a dense centreline"""
        n = len(P)
        _, N = _normals(P)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        L = s[-1]
        if jitter:
            P = P + N * (fbm1d(n, max(4, 150 / step), 3, self._seed()) * jitter * 1.6)[:, None]
        w = width * (1 + press * fbm1d(n, max(4, 80 / step), 3, self._seed()))
        if taper:
            w = w * (0.22 + 0.78 * smoothstep(0, max(taper[0], 1e-3), s)) * (0.1 + 0.9 * smoothstep(0, max(taper[1], 1e-3), L - s))
        return P.astype(np.float32), w.astype(np.float32)

    def _prep(self, pts, width, taper=(10, 22), smooth=True, jitter=1.0, press=0.14):
        return self._profile(self._dense(pts, smooth), width, taper, jitter, press)

    def _raster(self, P, w, ss=3):
        """variable-width centreline -> (slices, alpha): quads between offset points + round joins, drawn at ss x"""
        r = float(w.max()) / 2 + 3
        sl = self._box(P[:, 0].min() - r, P[:, 1].min() - r, P[:, 0].max() + r + 1, P[:, 1].max() + r + 1)
        if sl is None: return None, None
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (bw * ss, bh * ss), 0)
        d = ImageDraw.Draw(im)
        Q = (P - np.array([x0, y0], np.float32)) * ss
        R = np.maximum(w * ss / 2, 0.6)
        T, N = _normals(Q)
        A = (Q + N * R[:, None]).tolist(); B = (Q - N * R[:, None]).tolist()
        for i in range(len(Q) - 1):
            d.polygon(A[i] + A[i + 1] + B[i + 1] + B[i], fill=255)
        seg = np.diff(Q, axis=0)
        seg /= np.linalg.norm(seg, axis=1, keepdims=True) + 1e-6
        turn = np.concatenate([[1.0], np.sum(seg[1:] * seg[:-1], 1), [1.0]])
        idx = set(np.flatnonzero(turn < 0.96).tolist()) | set(range(0, len(Q), 3)) | {0, len(Q) - 1}
        Ql, Rl = Q.tolist(), R.tolist()
        for i in idx:
            (x, y), rr = Ql[i], Rl[i]
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=255)
        return sl, np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255

    def _pencil_pass(self, P, closed=False, drift=3.2, width=1.7, alpha=0.6, passes=None, kind='rough'):
        """loose blue col-erase pencil along a line: drifts off it, overshoots the ends, runs past closed starts"""
        buf = self._rbuf(self._g(kind))
        r = self.rng
        for _ in range(passes or int(r.integers(1, 3))):
            Q = _resample(P, 2.5)
            if len(Q) < 2: continue
            T, N = _normals(Q)
            n = len(Q)
            off = fbm1d(n, max(4, 90), 3, self._seed()) * drift + r.normal(0, 1.0)
            Q = Q + N * off[:, None] + r.normal(0, 1.4, 2).astype(np.float32)
            if closed:
                k = max(2, int(n * r.uniform(0.04, 0.1)))
                Q = np.vstack([Q, Q[1:k] + r.normal(0, 1.5, 2).astype(np.float32)])
            else:
                e0, e1 = r.uniform(3, 15), r.uniform(3, 15)
                Q = np.vstack([Q[:1] - T[:1] * e0, Q, Q[-1:] + T[-1:] * e1])
            wv = np.full(len(Q), width, np.float32) * (0.8 + 0.4 * r.random())
            sl, a = self._raster(Q, wv, ss=2)
            if sl is None: continue
            a = a * alpha * smoothstep(0.2, 0.7, self.tooth[sl] + 0.22)
            buf[sl] = 1 - (1 - buf[sl]) * (1 - a)

    def sketch(self, pts, closed=False, width=1.7, alpha=0.6, smooth=True, passes=1):
        """construction lines in blue pencil only (guides, centre lines, ellipses): they never get inked"""
        P = np.asarray(pts, np.float32)
        if smooth and 3 <= len(P) < 60: P = _closed_spline(P, 10) if closed else spline(P, per=10)
        self._pencil_pass(P, closed, drift=2.0, width=width, alpha=alpha, passes=passes)

    def line(self, pts, width=6.0, taper=(10, 22), smooth=True, jitter=1.0, press=0.14, kind='ink', rough=True):
        """an open brush-pen line: lands thin, swells, lifts off to a point"""
        P, w = self._prep(pts, width, taper, smooth, jitter, press)
        if rough and self.auto_rough: self._pencil_pass(P)
        sl, a = self._raster(P, w)
        if sl is not None: self._inkon(self._g(kind), sl, a)
        return P

    def lines(self, paths, width=6.0, **kw):
        for p in paths: self.line(p, width, **kw)

    def outline(self, pts, width=7.0, weight=0.35, overlap=0.05, gaps=0, jitter=1.0, press=0.12, taper=(18, 26),
                smooth=None, start=None, kind='ink', rough=True):
        """a closed shape inked in one stroke: the two tapered ends overlap where the pen came back round;
        heavier on the side away from the light. gaps=n leaves n small breaks (open-ended hand inking)."""
        P = np.asarray(pts, np.float32)
        smooth = len(P) < 60 if smooth is None else smooth
        C = self._dense(P, smooth, closed=True)
        n = len(C)
        _, Nl = _normals(np.vstack([C[-1:], C, C[:1]]))
        Nl = Nl[1:-1]
        sign = 1.0 if np.mean(np.sum(Nl * (C - C.mean(0)), 1)) > 0 else -1.0
        out = Nl * sign
        i0 = int(self.rng.integers(n)) if start is None else int(start) % n
        idx = (i0 + np.arange(int(n * (1 + overlap)))) % n
        Pp, O = C[idx], out[idx]
        if rough and self.auto_rough: self._pencil_pass(C, closed=True)
        cuts = [(0, len(Pp))]
        if gaps:
            pos = np.sort(self.rng.uniform(0.15, 0.85, gaps)) * len(Pp)
            cuts, a = [], 0
            for p in pos:
                g = int(self.rng.uniform(5, 12) / 1.4)
                cuts.append((a, int(p))); a = int(p) + g
            cuts.append((a, len(Pp)))
        for a, b in cuts:
            if b - a < 4: continue
            Pr, w = self._profile(Pp[a:b], width, taper, jitter, press)
            w = w * (1 + weight * np.clip(O[a:b] @ (-self.light), -1, 1))
            sl, al = self._raster(Pr, w)
            if sl is not None: self._inkon(self._g(kind), sl, al)
        return C

    def ink_fill(self, shape, kind='ink'):
        """a solid ink area (slots, soles, a very dark pupil that needs no glint)"""
        sl, M = self._region(shape, 2)
        if sl is not None: self._inkon(self._g(kind), sl, M)

    def dot(self, x, y, r=3.0, kind='ink'):
        sl, a = self._raster(np.array([[x - 0.3, y], [x + 0.3, y]], np.float32), np.array([2 * r, 2 * r], np.float32))
        if sl is not None: self._inkon(self._g(kind), sl, a)

    # ------------------------------------------------------------ colour
    def fill(self, shape, colour, slop=None, wander=1.0, drift=0.05, knock=True, kind='flat'):
        """flat colour, painted a little off the lines (shifted by `slop` px, wandering edge); knocks out what is
        behind. Returns the painted area as a Mask (use it as clip= for shade)."""
        slop = self.slop if slop is None else slop
        sl, M = self._region(shape, int(slop + 8))
        if sl is None: return None
        F = M
        if slop:
            a = self.rng.uniform(0, 2 * np.pi)
            F = shift(M, np.cos(a) * slop, np.sin(a) * slop)
        if wander:
            F = smoothstep(0.3, 0.7, blur(F, 1.2) + (self._wob[sl] - 0.5) * 0.5 * wander)
        col = _c(colour)[None, None, :] * (1 + drift * (self._var[sl] - 0.5) * 2)[..., None]
        g = self._g(kind)
        if knock: self._knock(g, sl, np.maximum(M, F), M)
        self._put(g, sl, F, col)
        return Mask(sl, F)

    def shade(self, shape, colour, offset=(12, 12), clip=None, wander=0.6, kind='shade'):
        """a hard cel shadow: the shape minus itself nudged toward the light (offset px away from the light),
        or with offset=None the shape itself; clipped to `clip` (e.g. the Mask returned by fill)"""
        pad = int(max(abs(offset[0]), abs(offset[1])) + 6) if offset else 6
        sl, M = self._region(shape, pad)
        if sl is None: return None
        S = M * (1 - shift(M, -offset[0], -offset[1])) if offset else M
        S = S * self._crop(clip, sl)
        if wander:
            S = smoothstep(0.35, 0.65, blur(S, 0.8) + (self._wob[sl] - 0.5) * 0.3 * wander) * (S > 0.02)
        self._put(self._g(kind), sl, S, colour)
        return Mask(sl, S)

    def glint(self, pts, width=7.0, colour=WHITE, taper=(8, 14), smooth=True, kind='shade'):
        """a white highlight: a tapered stroke of opaque paint"""
        P, w = self._prep(pts, width, taper, smooth, 0.3, 0.1)
        sl, a = self._raster(P, w)
        if sl is not None: self._put(self._g(kind), sl, a, colour)

    def shape(self, pts, colour, shade=None, shade2=None, width=7.0, weight=0.35, slop=None, gaps=0, kind=('flat', 'ink')):
        """fill + up to two cel shadows (colour, dx, dy) + brush outline, in that order"""
        F = self.fill(pts, colour, slop, kind=kind[0])
        for sh in (shade, shade2):
            if sh: self.shade(pts, sh[0], (sh[1], sh[2]), clip=F)
        self.outline(pts, width, weight, gaps=gaps, kind=kind[1])
        return F

    def _streaks(self, sl, angle, spacing=2.6):
        xx, yy = self.XX[sl], self.YY[sl]
        a = np.deg2rad(angle)
        along = xx * np.cos(a) - yy * np.sin(a)
        k = (xx * np.sin(a) + yy * np.cos(a)) / spacing
        k0 = np.floor(k.min())
        n = int(k.max() - k0) + 3
        r1, r2 = self.rng.random(n), self.rng.random(n)
        j = k - k0
        s = np.interp(j, np.arange(n), r1)
        mod = 0.5 + 0.5 * np.sin(along / (18 + 30 * np.interp(j, np.arange(n), r2)) + np.interp(j, np.arange(n), r2) * 40)
        return (0.62 * s + 0.38 * mod).astype(np.float32)

    def crayon(self, shape, colour, pressure=0.6, angle=35, soft=5, edge=1.0, alpha=0.95, clip=None, kind='texture'):
        """wax crayon: only the tops of the tooth take colour, streaked along the scribble direction, ragged
        edge. pressure may be a full-size array (a gradient)."""
        sl, M = self._region(shape, int(soft * 3 + 6))
        if sl is None: return
        E = smoothstep(0.25, 0.75, blur(M, soft) + (self._wob[sl] - 0.5) * 0.7 * edge)
        tex = 0.55 * self.tooth[sl] + 0.45 * self._streaks(sl, angle)
        p = pressure[sl] if isinstance(pressure, np.ndarray) else pressure
        thr = 1 - np.asarray(p, np.float32)
        a = E * smoothstep(thr - 0.13, thr + 0.13, tex) * alpha * self._crop(clip, sl)
        self._put(self._g(kind), sl, a, colour)

    def blush(self, cx, cy, rx=16, ry=9, colour=PINK, rot=0.0, kind='shade'):
        self.crayon(self.ellipse_pts(cx, cy, rx, ry, rot), colour, pressure=0.72, angle=40 + rot, soft=2.5, edge=0.4, kind=kind)

    def tone(self, shape, colour=INK, cell=9.0, angle=45, amount=0.22, alpha=1.0, clip=None, kind='texture'):
        """screentone: a rotated grid of dots; amount (0..1 ink coverage) may be a full-size array"""
        sl, M = self._region(shape, 2)
        if sl is None: return
        xx, yy = self.XX[sl], self.YY[sl]
        a = np.deg2rad(angle)
        u = (xx * np.cos(a) - yy * np.sin(a)) / cell
        v = (xx * np.sin(a) + yy * np.cos(a)) / cell
        d = np.hypot(u - np.round(u), v - np.round(v)) * cell
        amt = amount[sl] if isinstance(amount, np.ndarray) else amount
        rad = cell * np.sqrt(np.clip(amt, 0, 1) / np.pi)
        dots = np.clip(rad - d + 0.5, 0, 1) * M * self._crop(clip, sl) * alpha
        self._put(self._g(kind), sl, dots, colour)

    def hatch(self, shape, angle=-55, spacing=11, width=2.8, jitter=0.5, trim=5, kind='texture'):
        """ink hatching clipped to a mask: parallel short strokes with uneven, tapered ends (contact shadows)"""
        sl, M = self._region(shape, 4)
        if sl is None: return
        y0, x0 = sl[0].start, sl[1].start
        h, w = M.shape
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), -np.sin(a)], np.float32)
        p = np.array([-d[1], d[0]], np.float32)
        corners = np.array([[0, 0], [w, 0], [0, h], [w, h]], np.float32)
        pr, dr = corners @ p, corners @ d
        ts = np.arange(dr.min(), dr.max(), 1.5, dtype=np.float32)
        for o in np.arange(pr.min() + spacing * 0.5, pr.max(), spacing):
            o = o + self.rng.uniform(-0.12, 0.12) * spacing
            pts = o * p + ts[:, None] * d
            ix, iy = np.round(pts[:, 0]).astype(int), np.round(pts[:, 1]).astype(int)
            ok = (ix >= 0) & (iy >= 0) & (ix < w) & (iy < h)
            inside = np.zeros(len(ts), bool)
            inside[ok] = M[iy[ok], ix[ok]] > 0.5
            edges = np.flatnonzero(np.diff(np.concatenate([[0], inside.astype(np.int8), [0]])))
            for s0, s1 in zip(edges[::2], edges[1::2]):
                s0 = s0 + int(self.rng.uniform(0, trim) / 1.5); s1 = s1 - int(self.rng.uniform(0, trim) / 1.5)
                if s1 - s0 < 4: continue
                seg = pts[s0:s1] + np.array([x0, y0], np.float32)
                self.line(seg, width, taper=(3, 6), smooth=False, jitter=jitter, kind=kind, rough=False)

    # ------------------------------------------------------------ faces and limbs
    def face(self, cx, cy, size=100, mood='happy', rot=0.0, blush=True, width=None, kind=('flat', 'ink')):
        """a face on anything. size ~ the face width in px. moods: happy (^ ^ and an open grin with a tongue),
        wow (round eyes, little o mouth), sleepy (closed eyes, small smile), smile (dot eyes, smile), wink"""
        u = size / 100.0
        lw = width or max(3.0, 5.4 * u)
        X = lambda pts: self.place(pts, cx, cy, u, rot)
        ex, ey = 34, -8

        def dot_eye(sx):
            e = X(self.ellipse_pts(sx * ex, ey, 7.5, 10.5))
            self.fill(e, INK, slop=0.6, wander=0.2, kind=kind[0])
            self.outline(e, lw * 0.5, 0, kind=kind[1], rough=False)
            gl = X(self.ellipse_pts(sx * ex - 2.2, ey - 4.2, 2.6, 3.2))
            self.fill(gl, WHITE, slop=0, wander=0, knock=False, kind='shade')

        if mood in ('happy', 'grin', 'wink'):
            for sx in (-1, 1):
                if mood == 'wink' and sx == 1:
                    dot_eye(sx); continue
                self.line(X([(sx * ex - 12, ey + 6), (sx * ex, ey - 7), (sx * ex + 12, ey + 6)]), lw, (5, 6), kind=kind[1])
            top = [(-24, 14), (-10, 17), (10, 17), (24, 14)]
            bot = [(22, 18), (12, 38), (0, 43), (-12, 38), (-22, 18)]
            mouth = X(_closed_spline(top + bot, 8))
            F = self.fill(mouth, '#6b2723', slop=1.5, kind=kind[0])
            tongue = X(self.ellipse_pts(1, 40, 15, 10))
            self.fill(self.mask(tongue) * self._full(F), '#ef6b5d', slop=0, wander=0.3, knock=False, kind='shade')
            self.outline(mouth, lw * 0.9, 0.2, overlap=0.03, kind=kind[1])
        elif mood == 'wow':
            for sx in (-1, 1): dot_eye(sx)
            o = X(self.ellipse_pts(0, 27, 9, 11))
            self.fill(o, '#6b2723', slop=1, kind=kind[0])
            self.outline(o, lw * 0.85, 0.2, kind=kind[1])
        elif mood == 'sleepy':
            for sx in (-1, 1):
                self.line(X([(sx * ex - 12, ey - 2), (sx * ex, ey + 6), (sx * ex + 12, ey - 2)]), lw * 0.9, (5, 6), kind=kind[1])
                self.line(X([(sx * ex + sx * 12, ey - 1), (sx * ex + sx * 17, ey - 5)]), lw * 0.55, (2, 4), kind=kind[1])
            self.line(X([(-8, 22), (0, 27), (8, 22)]), lw * 0.8, (4, 5), kind=kind[1])
        else:   # smile
            for sx in (-1, 1): dot_eye(sx)
            self.line(X([(-17, 17), (0, 29), (17, 17)]), lw, (5, 6), kind=kind[1])
        if blush:
            for sx in (-1, 1):
                p = X([(sx * (ex + 11), ey + 23)])[0]
                self.blush(p[0], p[1], 15 * u, 8.5 * u, rot=rot)

    def _full(self, m):
        full = np.zeros((self.H, self.W), np.float32)
        if m is not None: full[m.sl] = m.a
        return full

    def arm(self, p0, p1, bend=0.25, width=5.5, hand=22, glove=WHITE, thumb=1, kind=('flat', 'ink')):
        """a rubber-hose arm: one even ink line from the shoulder p0, and a round white mitten at p1 (thumb on
        side thumb=+1 / -1 of the arm direction, a cuff line, two finger creases)"""
        from core import curve
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        L = float(np.hypot(*(p1 - p0)))
        self.line(curve(p0, p1, bend * L, n=16), width, taper=(3, 3), press=0.05, kind=kind[1])
        d = (p1 - p0) / (L + 1e-6)
        ang = np.degrees(np.arctan2(-d[1], d[0]))
        hx, hy = p1 + d * hand * 0.35
        at = lambda pts: self.place(pts, hx, hy, hand, ang)
        th = at(self.ellipse_pts(0.05, -0.78 * thumb, 0.42, 0.34, 25 * thumb))     # thumb lobe, behind the palm
        self.fill(th, glove, slop=1, kind=kind[0])
        self.outline(th, width * 0.75, 0.2, kind=kind[1])
        palm = at(self.ellipse_pts(0.1, 0.05, 1.0, 0.86))
        F = self.fill(palm, glove, slop=1.5, kind=kind[0])
        self.shade(palm, '#dcd9e2', (-hand * 0.0 + 4, 5), clip=F)
        self.outline(palm, width * 0.8, 0.3, kind=kind[1])
        self.line(at([(-0.72, -0.62), (-0.95, 0.0), (-0.72, 0.62)]), width * 0.55, (3, 4), kind=kind[1])
        for v in (0.12, 0.42):
            self.line(at([(0.55, v * thumb), (0.98, v * thumb * 0.9)]), width * 0.45, (2, 4), smooth=False, kind=kind[1])

    # ------------------------------------------------------------ effects (overlay group 'fx' unless fx=False)
    def _k(self, fx, base):
        return 'fx' if fx else base

    def sparkle(self, x, y, r=24, colour=YELLOW, rot=8, width=None, fx=True):
        """a 4-point sparkle (astroid with concave sides), filled and outlined"""
        t = np.linspace(0, 2 * np.pi, 160, endpoint=False)
        c, s = np.cos(t), np.sin(t)
        e = 3.1
        pts = self.place(np.stack([np.sign(c) * np.abs(c) ** e * 0.9, np.sign(s) * np.abs(s) ** e * 1.2], 1), x, y, r, rot)
        self.fill(pts, colour, slop=r * 0.08, kind=self._k(fx, 'flat'))
        self.outline(pts, width or max(2.4, r * 0.11), 0.2, smooth=False, overlap=0.03, kind=self._k(fx, 'ink'))

    def speed_lines(self, p0, p1, angle=90, n=6, length=(60, 140), width=4.5, fx=True):
        """motion lines: n strokes starting along the segment p0-p1, heading `angle` (ccw, 90 = up)"""
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), -np.sin(a)], np.float32)
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        for t in (np.arange(n) + self.rng.uniform(0.2, 0.8, n)) / n:
            q = p0 + (p1 - p0) * t + d * self.rng.uniform(0, 18)
            L = self.rng.uniform(*length)
            self.line([q, q + d * L * 0.5, q + d * L], width * self.rng.uniform(0.75, 1.15), (L * 0.3, L * 0.45),
                      smooth=False, jitter=0.6, kind=self._k(fx, 'ink'))

    def steam(self, x, y, h=120, amp=14, width=4.5, turns=1.3, fx=True):
        """a steam wisp rising from (x, y): an S-curve that widens as it rises, tapered both ends"""
        t = np.linspace(0, 1, 24)
        ph = self.rng.uniform(0, 2 * np.pi)
        pts = np.stack([x + amp * (0.4 + t) * np.sin(2 * np.pi * turns * t + ph), y - h * t], 1)
        self.line(pts, width, (h * 0.25, h * 0.35), kind=self._k(fx, 'ink'))

    def puff(self, cx, cy, r, colour=WHITE, bumps=6, width=5.0, curl=True, shadow='#dcdbe3', rot=0.0, squash=0.85, fx=True):
        """a scalloped cloud / smoke puff with an inner curl line and a cel shadow"""
        th = np.linspace(0, 2 * np.pi, 260, endpoint=False)
        amp = self.rng.uniform(0.8, 1.2, bumps)
        k = (th + np.deg2rad(rot)) / (2 * np.pi) * bumps
        rr = r * (0.8 + 0.2 * np.abs(np.sin(np.pi * k)) ** 0.7 * amp[np.floor(k).astype(int) % bumps])
        pts = np.stack([cx + rr * np.cos(th), cy + rr * np.sin(th) * squash], 1)
        F = self.fill(pts, colour, slop=r * 0.04, kind=self._k(fx, 'flat'))
        if shadow: self.shade(pts, shadow, (r * 0.16, r * 0.2), clip=F, kind=self._k(fx, 'shade'))
        self.outline(pts, width, 0.3, smooth=False, kind=self._k(fx, 'ink'))
        if curl:
            a0 = self.rng.uniform(15, 45)
            arc = self.ellipse_pts(cx, cy, r * 0.55, r * 0.55 * squash, 0, a0, a0 + 70)
            self.line(arc, width * 0.7, (6, 10), kind=self._k(fx, 'ink'))
        return pts

    def burst(self, cx, cy, rx, ry, colour=RED, spikes=14, depth=0.3, rot=0.0, width=7.0, shade=None, fx=True):
        """a comic starburst with uneven spikes; returns its outline points"""
        n = 2 * spikes
        th = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.deg2rad(rot) + self.rng.uniform(-0.08, 0.08, n)
        rr = np.where(np.arange(n) % 2 == 0, self.rng.uniform(0.9, 1.1, n), (1 - depth) * self.rng.uniform(0.94, 1.04, n))
        pts = self.densify(np.stack([cx + rx * rr * np.cos(th), cy + ry * rr * np.sin(th)], 1), 7)
        F = self.fill(pts, colour, kind=self._k(fx, 'flat'))
        if shade: self.shade(pts, shade, (rx * 0.06, ry * 0.08), clip=F, kind=self._k(fx, 'shade'))
        self.outline(pts, width, 0.3, smooth=False, overlap=0.03, kind=self._k(fx, 'ink'))
        return pts

    def crumbs(self, cx, cy, n=8, spread=(150, 80), size=(5, 10), colour='#c9803c', width=2.6, avoid=None, fx=True):
        """little flying bits: irregular chunks, each outlined; avoid = a full-size mask they must not land on"""
        placed, tries = 0, 0
        while placed < n and tries < n * 40:
            tries += 1
            a = self.rng.uniform(0, 2 * np.pi); rr = np.sqrt(self.rng.uniform(0.15, 1))
            x, y = cx + np.cos(a) * spread[0] * rr, cy + np.sin(a) * spread[1] * rr
            if avoid is not None and (not (0 <= x < self.W and 0 <= y < self.H) or avoid[int(y), int(x)] > 0.1): continue
            placed += 1
            s = self.rng.uniform(*size)
            k = int(self.rng.integers(4, 6))
            th = np.sort(self.rng.uniform(0, 2 * np.pi, k))
            pts = np.stack([x + np.cos(th) * s * self.rng.uniform(0.6, 1.2, k), y + np.sin(th) * s * self.rng.uniform(0.6, 1.2, k)], 1)
            pts = self.densify(pts, 3)
            self.fill(pts, colour, slop=1, kind=self._k(fx, 'flat'))
            self.outline(pts, width, 0, smooth=False, rough=False, kind=self._k(fx, 'ink'))

    def pop_lines(self, cx, cy, r0, r1, angles, width=5.0, fx=True):
        """emphasis ticks radiating from a point (surprise, a sudden sound)"""
        for a in angles:
            t = np.deg2rad(a)
            d = np.array([np.cos(t), -np.sin(t)])
            self.line([(cx + d[0] * r0, cy + d[1] * r0), (cx + d[0] * r1, cy + d[1] * r1)], width, (4, 8), smooth=False,
                      jitter=0.3, kind=self._k(fx, 'ink'))

    # ------------------------------------------------------------ lettering (overlay group 'type')
    def _word(self, s, size, font=None, tilt=3.0, bounce=0.04, spacing=0.0, scale=0.04):
        """hand-set word mask: every glyph a little tilted, bounced and resized. -> (mask, pad, baseline, width)"""
        r = np.random.default_rng(self._seed())
        items = []
        for ch in s:
            sz = size * (1 + r.uniform(-scale, scale))
            f = _font(_pick(ch, font), sz)
            adv = (size * 0.3 if not ch.strip() else f.getlength(ch)) + spacing
            items.append((ch, f, sz, adv))
        total = sum(it[3] for it in items) - spacing
        pad = int(size * 0.55) + 12
        Wc, Hc = int(total + 2 * pad), int(size * 1.55 + 2 * pad)
        base = pad + size * 1.08
        canvas = np.zeros((Hc, Wc), np.float32)
        x = float(pad)
        for ch, f, sz, adv in items:
            if ch.strip():
                cw, chh = int(adv + sz * 1.2), int(sz * 2.2)
                im = Image.new('L', (cw, chh), 0)
                ox, oy = sz * 0.6, sz * 1.45
                ImageDraw.Draw(im).text((ox, oy), ch, font=f, fill=255, anchor='ls')
                im = im.rotate(r.uniform(-tilt, tilt), Image.BICUBIC, center=(ox + adv / 2, oy - sz * 0.36))
                a = np.asarray(im, np.float32) / 255
                px, py = int(round(x - ox)), int(round(base + r.uniform(-bounce, bounce) * size - oy))
                ya, xa = max(0, py), max(0, px)
                yb, xb = min(Hc, py + chh), min(Wc, px + cw)
                if yb > ya and xb > xa:
                    np.maximum(canvas[ya:yb, xa:xb], a[ya - py:yb - py, xa - px:xb - px], out=canvas[ya:yb, xa:xb])
            x += adv
        return canvas, pad, base, total

    def _place_word(self, canvas, pad, base, total, x, y, anchor, rot):
        if rot:
            ax = pad + total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor]
            canvas = np.asarray(Image.fromarray(canvas).rotate(rot, Image.BICUBIC, center=(ax, base)), np.float32)
        x0 = int(round(x - pad - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor]))
        y0 = int(round(y - base))
        h, w = canvas.shape
        sl = self._box(x0, y0, x0 + w, y0 + h)
        if sl is None: return None, None
        return sl, canvas[sl[0].start - y0:sl[0].stop - y0, sl[1].start - x0:sl[1].stop - x0]

    def text_width(self, s, size, font=None, spacing=0.0):
        return sum((size * 0.3 if not ch.strip() else _font(_pick(ch, font), size).getlength(ch)) + spacing for ch in s) - spacing

    def letter(self, s, x, y, size, fill=YELLOW, depth=(5, 7), depth_colour=RED, outline=None, font=None, anchor='l',
               rot=0.0, tilt=4.0, bounce=0.05, spacing=0.0, highlight=True, kind='type'):
        """display lettering: chunky letters, each a little tilted and bounced, an extruded shadow in
        depth_colour, a white rim light on the upper-left edges and a thick ink outline round it all.
        (x, y) is the baseline point at `anchor` ('l', 'm', 'r')."""
        canvas, pad, base, total = self._word(s, size, font, tilt, bounce, spacing)
        sl, M = self._place_word(canvas, pad, base, total, x, y, anchor, rot)
        if sl is None: return
        ow = outline or max(3.0, size * 0.065)
        E = np.zeros_like(M)
        if depth:
            k = int(max(abs(depth[0]), abs(depth[1]))) + 1
            for i in range(1, k + 1): np.maximum(E, shift(M, depth[0] * i / k, depth[1] * i / k), out=E)
        U = np.maximum(M, E)
        ring = np.clip(_dilate(U, ow) - U, 0, 1)
        inner = np.clip(_dilate(M, max(2, ow * 0.45)) - M, 0, 1) * E
        occ = _dilate(U, ow)
        g = self._g(kind)
        self._knock(g, sl, occ, occ)
        if depth: self._put(g, sl, E, depth_colour)
        col = _c(fill)[None, None, :] * (1 + 0.05 * (self._var[sl] - 0.5) * 2)[..., None]
        self._put(g, sl, M, col)
        if highlight:
            hl = np.clip(M - shift(M, 2, 3), 0, 1) * smoothstep(0.35, 0.6, self._wob[sl])
            self._put(g, sl, hl * 0.95, WHITE)
        self._inkon(g, sl, np.maximum(ring, inner))

    def note(self, s, x, y, size, colour=INK, font=None, anchor='l', rot=0.0, tilt=3.0, bounce=0.04, spacing=0.0,
             bold=0, kind='type'):
        """hand-lettered text in ink (or paint, if colour is not INK); (x, y) = baseline point at anchor"""
        canvas, pad, base, total = self._word(s, size, font, tilt, bounce, spacing)
        if bold: canvas = _dilate(canvas, bold)
        sl, M = self._place_word(canvas, pad, base, total, x, y, anchor, rot)
        if sl is None: return total
        if isinstance(colour, str) and colour.lower() == INK:
            self._inkon(self._g(kind), sl, M)
        else:
            self._put(self._g(kind), sl, M, colour)
        return total

    def pencil_note(self, s, x, y, size=26, anchor='l', rot=0.0, colour=PENCIL, alpha=0.8):
        """blue-pencil writing on the sheet (drawing numbers, timing notes): grainy, shown with the rough"""
        canvas, pad, base, total = self._word(s, size, 'comic', 2.0, 0.03, 1.0)
        sl, M = self._place_word(canvas, pad, base, total, x, y, anchor, rot)
        if sl is None: return
        a = M * alpha * smoothstep(0.2, 0.62, self.tooth[sl] + 0.2)
        self._put(self._g('rough'), sl, a, colour)

    def arrow(self, pts, width=4.5, head=22, spread=30, smooth=True, kind='type'):
        """a hand-drawn arrow: a tapered line and two flicks meeting at the tip"""
        P = self.line(pts, width, taper=(8, 3), smooth=smooth, kind=kind)
        tip = P[-1]
        back = P[max(0, len(P) - 12)]
        a = np.arctan2(back[1] - tip[1], back[0] - tip[0])
        for sgn in (-1, 1):
            b = a + sgn * np.deg2rad(spread)
            self.line([(tip[0] + np.cos(b) * head, tip[1] + np.sin(b) * head), tuple(tip)], width, (4, 2), smooth=False,
                      jitter=0.3, kind=kind)

    def badge(self, x, y, r, label, colour=YELLOW, size=None, width=4.5, kind='type'):
        """a numbered round badge: filled disc, outline, the label in ink"""
        e = self.ellipse_pts(x, y, r, r)
        self.fill(e, colour, slop=2, kind=kind)
        self.outline(e, width, 0.3, kind=kind)
        self.note(label, x, y + (size or r * 1.1) * 0.36, size or r * 1.1, anchor='m', tilt=0, bounce=0, kind=kind)

    # ------------------------------------------------------------ output
    def _field(self, k, amp):
        r = np.random.default_rng(self.seed * 7919 + k * 104729 + 1)

        def smooth(cell):
            gh, gw = self.H // cell + 3, self.W // cell + 3
            a = Image.fromarray(r.random((gh, gw)).astype(np.float32)).resize((gw * cell, gh * cell), Image.BICUBIC)
            return (np.asarray(a, np.float32)[:self.H, :self.W] - 0.5) * 2

        return [amp * (0.8 * smooth(44) + 0.45 * smooth(150)) for _ in range(2)]            # (dx, dy)

    def _warp(self, arrs, fx, fy):
        x = np.clip(self.XX + fx, 0, self.W - 1.001); y = np.clip(self.YY + fy, 0, self.H - 1.001)
        x0, y0 = x.astype(np.int32), y.astype(np.int32)
        wx, wy = x - x0, y - y0
        out = []
        for a in arrs:
            X, Y = (wx[..., None], wy[..., None]) if a.ndim == 3 else (wx, wy)
            out.append((a[y0, x0] * (1 - X) + a[y0, x0 + 1] * X) * (1 - Y) + (a[y0 + 1, x0] * (1 - X) + a[y0 + 1, x0 + 1] * X) * Y)
        return out

    def composite(self, show=None, rough=None, boil=0):
        """show: groups to include (None = all); rough: pencil strength (default 0.3); boil: which retrace"""
        H, W = self.H, self.W
        vis = lambda g: show is None or g in show
        covers = [(self._prio(g), cv) for g, cv in self.cover.items() if vis(g)]

        def knocked(g, arr, which):
            for pg, cv in covers:
                if self._prio(g) < pg:
                    k = 1 - cv[which]
                    arr = arr * (k[..., None] if arr.ndim == 3 else k)
            return arr

        PC = np.zeros((H, W, 3), np.float32); PA = np.zeros((H, W), np.float32)
        for g in sorted(self.paint, key=lambda g: (self._prio(g), self.created.index(g))):
            if not vis(g): continue
            pc, pa = knocked(g, self.paint[g][0], 0), knocked(g, self.paint[g][1], 0)
            PC = PC * (1 - pa[..., None]) + pc; PA = PA * (1 - pa) + pa
        IA = np.zeros((H, W), np.float32)
        for g, ia in self.ink.items():
            if vis(g): IA = 1 - (1 - IA) * (1 - knocked(g, ia, 1))
        R = np.zeros((H, W), np.float32)
        for g, rb in self.pencil.items():
            if vis(g): R = 1 - (1 - R) * (1 - rb)
        R = R * (0.3 if rough is None else rough)
        if self.boil:                                                   # the ink is re-traced, colour and pencil stay
            fx, fy = self._field(boil, self.boil)
            IA, = self._warp([IA], fx, fy)
        out = self.paperc * (1 - R[..., None] * (1 - _c(PENCIL)))
        out = out * (1 - PA[..., None]) + PC
        out = out * (1 + (self.grain - 1) * (1 - 0.55 * PA))[..., None]      # paint fills the tooth a little
        out = out * (1 - IA[..., None]) + _c(INK) * IA[..., None]
        return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))

    def stage(self, name, show=None, rough=None):
        """snapshot for the draw-on animation; each one is a fresh retrace (the lines boil)"""
        self.stages.append((name, self.composite(show, rough, boil=len(self.stages) + 1)))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality)
        else: img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
