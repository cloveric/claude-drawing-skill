"""vhs — a home-video frame: a 1970s living room shot on a consumer camcorder and played back off VHS tape
(numpy + Pillow only).

This is not a 'retro filter' laid over a picture (that is what synthwave does with its neon scene): the picture is
made the way a real home-video frame was made, in three passes, and every artefact comes out of one of them.

  1. the room      surfaces are painted as albedo (what colour the thing is) into one buffer and self-lit things
                   (lamp shade, candle flames, dusk sky in the window, glints) into an emission buffer. At render time
                   the albedo is multiplied by the lighting of the room -- a dim warm ambient, a few point lights with
                   a soft 1/(1+d^2) fall-off (`light`) and painted light patches (`glow`: the scallops a drum shade
                   throws on the wall, the pool a candle throws on the table). Things right in front of the lens are
                   painted on a defocus layer (`layer(defocus=)`), because the camcorder focused on the cake, not on
                   the child's head between it and the cake.
  2. the camera    an 80s CCD camcorder held by hand: a slight roll and zoom (`tilt`), the white balance left on
                   'outdoor' under tungsten bulbs (the room goes orange, the window goes blue), auto-exposure that
                   lets the flames and the lamp shade clip, a soft knee, bloom, CCD vertical smear -- a faint vertical
                   streak through the whole frame wherever a point is far over-exposed --, a short lag tail behind the
                   highlights (the camera was still panning), lens softness, vignetting and gain noise that is worst
                   in the dark corners. The camera's character generator mixes its OSD into the signal right here
                   (REC, battery, tape counter, date stamp, zoom bar in a chunky dot-matrix font with a black edge),
                   so the OSD goes onto the tape with the picture and smears with it.
  3. the tape      the frame is box-sampled to 480 lines x `samples` and split into luma Y and chroma I/Q (NTSC YIQ).
                   VHS records luma at ~3 MHz (~240 TV lines) and chroma 'colour-under' at ~0.6 MHz, so
                     luma    is low-passed along each line, then the playback 'sharpness' circuit adds edge
                             enhancement: a bright halo on one side of every dark edge and a dark one on the other;
                     chroma  is smeared over ~6x the luma width, averaged over two lines (comb filter) and delayed a
                             few samples to the right -- saturated reds bleed out of their outlines to the right;
                   playback then adds streaky luma noise, horizontal chroma noise streaks, line-by-line timebase
                   jitter, 'flagging' (the top lines bend sideways), a tracking-error band (displaced lines, white
                   noise streaks, ragged edges), head-switching noise in the last lines, dropouts (short white
                   flecks), a lifted black level and slightly lower saturation; the 480-line frame is scaled back up.

Stages: `stage(name)` keeps a full render of what is there so far: room stages render clean, `camera()`,
`record()`, `wear()` switch on their pass for every later stage, OSD items show from the stage they are added.

Canvas coordinates are output pixels; colours are '#rrggbb' or 0..1 RGB triples.

    from vhs import VHSCamcorder
    v = VHSCamcorder(1920, 1080, seed=3)
    v.ambient('#ffd7a8', 0.35)
    v.wallpaper(v.rect(0, 0, 1920, 760), tile=120)
    v.shag(v.rect(0, 760, 1920, 1080), '#c9962e')
    v.floor_lamp(1500, 760, 300)                         # brings its own light
    tips = v.cake(960, 700, 110, 33, 68, [(270, '#f2b51e', 'lit'), (90, '#2f6fc8', 1.0)])
    for x, y in tips: v.light(x, y, 280, '#ffa048', 0.3)
    v.stage('room')
    v.camera(tilt=-1.4)                                  # default white balance: 'outdoor' under tungsten
    v.record(); v.wear(tracking=(0.94, 0.04))
    v.rec(150, 100); v.datestamp('7:42 PM', 'JUN.16.1984', 150, 864)
    v.save('out.jpg')
"""
import os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font, shift

f32 = np.float32


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], f32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, f32)


def _blur_axis(a, sigma, axis):
    """gaussian-ish blur along one axis only (three box passes via cumulative sums)"""
    if sigma <= 0.05: return a.astype(f32, copy=True)
    if a.ndim == 3 and axis < 2 and a.shape[0] * a.shape[1] > 500000:   # big colour images: one channel at a time
        return np.stack([_blur_axis(a[..., k], sigma, axis) for k in range(a.shape[2])], -1)
    out = a.astype(f32)
    w = int(np.sqrt(12 * sigma * sigma / 3 + 1)); w += (w % 2 == 0)
    if w < 2:
        k = np.exp(-0.5 * (np.arange(-2, 3) / sigma) ** 2); k /= k.sum()
        pad = [(0, 0)] * out.ndim; pad[axis] = (2, 2)
        p = np.pad(out, pad, mode='edge'); n = out.shape[axis]
        return sum(k[i] * np.take(p, np.arange(i, i + n), axis=axis) for i in range(5)).astype(f32)
    r = w // 2
    for _ in range(3):
        pad = [(0, 0)] * out.ndim; pad[axis] = (r + 1, r)
        c = np.cumsum(np.pad(out, pad, mode='edge'), axis=axis, dtype=np.float64)
        n = c.shape[axis]
        out = ((np.take(c, np.arange(w, n), axis=axis) - np.take(c, np.arange(0, n - w), axis=axis)) / w).astype(f32)
    return out


def _gb(a, sigma):
    """gaussian-ish blur over the first two axes of a 2D or (H, W, C) array"""
    return _blur_axis(_blur_axis(a, sigma, 0), sigma, 1)


def _rowshift(a, off, fill=0.0):
    """shift every row of a (L, S[, C]) by off[row] samples (positive = right), linear interpolation, blank = fill"""
    L, S = a.shape[:2]
    xs = np.arange(S, dtype=f32)[None, :] - off[:, None].astype(f32)
    x0 = np.floor(xs); fr = xs - x0; x0 = x0.astype(np.int32)
    ok = (xs >= 0) & (xs <= S - 1)
    a0 = np.clip(x0, 0, S - 1); a1 = np.clip(x0 + 1, 0, S - 1)
    rows = np.arange(L)[:, None]
    if a.ndim == 3:
        out = a[rows, a0] * (1 - fr)[..., None] + a[rows, a1] * fr[..., None]
        return np.where(ok[..., None], out, f32(fill)).astype(f32)
    out = a[rows, a0] * (1 - fr) + a[rows, a1] * fr
    return np.where(ok, out, f32(fill)).astype(f32)


def _resize(a, w, h, method=Image.BICUBIC):
    """resize an (H, W) or (H, W, C) float array"""
    if a.ndim == 2:
        return np.asarray(Image.fromarray(a.astype(f32), 'F').resize((w, h), method), f32)
    return np.stack([_resize(a[..., i], w, h, method) for i in range(a.shape[2])], -1)


# ------------------------------------------------------------------ the character generator's dot-matrix font
_GLYPHS = {
    'A': '01110 10001 10001 11111 10001 10001 10001', 'B': '11110 10001 10001 11110 10001 10001 11110',
    'C': '01110 10001 10000 10000 10000 10001 01110', 'D': '11110 10001 10001 10001 10001 10001 11110',
    'E': '11111 10000 10000 11110 10000 10000 11111', 'F': '11111 10000 10000 11110 10000 10000 10000',
    'G': '01110 10001 10000 10111 10001 10001 01111', 'H': '10001 10001 10001 11111 10001 10001 10001',
    'I': '01110 00100 00100 00100 00100 00100 01110', 'J': '00111 00010 00010 00010 00010 10010 01100',
    'K': '10001 10010 10100 11000 10100 10010 10001', 'L': '10000 10000 10000 10000 10000 10000 11111',
    'M': '1000001 1100011 1010101 1001001 1000001 1000001 1000001', 'N': '10001 10001 11001 10101 10011 10001 10001',
    'O': '01110 10001 10001 10001 10001 10001 01110', 'P': '11110 10001 10001 11110 10000 10000 10000',
    'Q': '01110 10001 10001 10001 10101 10010 01101', 'R': '11110 10001 10001 11110 10100 10010 10001',
    'S': '01111 10000 10000 01110 00001 00001 11110', 'T': '11111 00100 00100 00100 00100 00100 00100',
    'U': '10001 10001 10001 10001 10001 10001 01110', 'V': '10001 10001 10001 10001 10001 01010 00100',
    'W': '1000001 1000001 1000001 1001001 1001001 1010101 0100010', 'X': '10001 10001 01010 00100 01010 10001 10001',
    'Y': '10001 10001 01010 00100 00100 00100 00100', 'Z': '11111 00001 00010 00100 01000 10000 11111',
    '0': '01110 10001 10001 10001 10001 10001 01110', '1': '00100 01100 00100 00100 00100 00100 01110',
    '2': '01110 10001 00001 00010 00100 01000 11111', '3': '11111 00010 00100 00010 00001 10001 01110',
    '4': '00010 00110 01010 10010 11111 00010 00010', '5': '11111 10000 11110 00001 00001 10001 01110',
    '6': '00110 01000 10000 11110 10001 10001 01110', '7': '11111 00001 00010 00100 01000 01000 01000',
    '8': '01110 10001 10001 01110 10001 10001 01110', '9': '01110 10001 10001 01111 00001 00010 01100',
    ':': '00000 01100 01100 00000 01100 01100 00000', '.': '00000 00000 00000 00000 00000 01100 01100',
    '-': '00000 00000 00000 11111 00000 00000 00000', '/': '00001 00010 00010 00100 01000 01000 10000',
    ' ': '00000 00000 00000 00000 00000 00000 00000', '>': '10000 11000 11100 11110 11100 11000 10000',
}


def _glyph_bitmap(s, bold=True):
    """string -> (7, n) 0/1 dot array; bold doubles every dot to the right like a camcorder character generator"""
    cols = []
    for ch in s.upper():
        g = np.array([[int(b) for b in row] for row in _GLYPHS.get(ch, _GLYPHS[' ']).split()], np.uint8)
        if bold: g = np.concatenate([g, np.zeros((7, 1), np.uint8)], 1); g[:, 1:] |= g[:, :-1]
        cols += [g, np.zeros((7, 1), np.uint8)]
    return np.concatenate(cols, 1) if cols else np.zeros((7, 1), np.uint8)


class VHSCamcorder:
    def __init__(self, W=1920, H=1080, seed=0, lines=480, samples=760, ss=2, keep_stages=True):
        self.W, self.H, self.ss = W, H, ss
        self.keep_stages = keep_stages              # False: stage() is free (no snapshot renders)
        self.lines, self.samples = lines, samples
        self.seed0 = seed
        self.rng = np.random.default_rng(seed)
        self.alb = np.zeros((H, W, 3), f32)       # surface colour
        self.em = np.zeros((H, W, 3), f32)        # self-lit
        self.patch = np.zeros((H, W, 3), f32)     # painted light patches (add to the lighting)
        self.amb = (_c('#ffffff'), 1.0)
        self.lights = []
        self.cam = None; self.rec_ = None; self.wear_ = None
        self.osd = []
        self.stages = []
        self._layer = None
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(f32)

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================ masks (full frame, drawn only inside the bbox)
    def _mask(self, bbox, draw):
        x0, y0, x1, y1 = bbox
        x0, y0 = max(int(np.floor(x0)) - 2, 0), max(int(np.floor(y0)) - 2, 0)
        x1, y1 = min(int(np.ceil(x1)) + 2, self.W), min(int(np.ceil(y1)) + 2, self.H)
        m = np.zeros((self.H, self.W), f32)
        if x1 <= x0 or y1 <= y0: return m
        ss = self.ss
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        T = lambda pts: [((float(x) - x0) * ss, (float(y) - y0) * ss) for x, y in pts]
        draw(ImageDraw.Draw(im), T, ss)
        m[y0:y1, x0:x1] = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), f32) / 255
        return m

    def poly(self, pts):
        P = np.asarray(pts, f32)
        return self._mask((P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()),
                          lambda d, T, ss: d.polygon(T(P), fill=255))

    def shape(self, pts, per=10):
        """closed smooth outline through control points"""
        P = np.asarray(pts, f32)
        return self.poly(spline(np.vstack([P, P[:1]]), per))

    def rect(self, x0, y0, x1, y1, r=0):
        if r <= 0: return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
        return self._mask((x0, y0, x1, y1), lambda d, T, ss: d.rounded_rectangle(
            [T([(x0, y0)])[0], T([(x1, y1)])[0]], radius=r * ss, fill=255))

    def ellipse(self, cx, cy, rx, ry, rot=0.0, n=120):
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        c, s = np.cos(np.radians(rot)), np.sin(np.radians(rot))
        x, y = np.cos(t) * rx, np.sin(t) * ry
        return self.poly(np.stack([cx + x * c - y * s, cy + x * s + y * c], 1))

    def line(self, pts, width):
        P = np.asarray(pts, f32); r = width / 2
        def dr(d, T, ss):
            Q = T(P)
            d.line(Q, fill=255, width=max(1, int(round(width * ss))), joint='curve')
            for q in (Q[0], Q[-1]): d.ellipse([q[0] - r * ss, q[1] - r * ss, q[0] + r * ss, q[1] + r * ss], fill=255)
        return self._mask((P[:, 0].min() - r, P[:, 1].min() - r, P[:, 0].max() + r, P[:, 1].max() + r), dr)

    def text(self, s, x, y, size, style='sans_bold', anchor='mm', rot=0.0):
        font = load_font(style, size * self.ss)
        def dr(d, T, ss):
            q = T([(x, y)])[0]
            if not rot:
                d.text(q, s, font=font, fill=255, anchor=anchor); return
            tmp = Image.new('L', d.im.size, 0)
            ImageDraw.Draw(tmp).text(q, s, font=font, fill=255, anchor=anchor)
            d.bitmap((0, 0), tmp.rotate(rot, resample=Image.BICUBIC, center=q), fill=255)
        R = size * (len(s) * 0.7 + 1.5)
        return self._mask((x - R, y - R, x + R, y + R), dr)

    # ================================================================ fields (colour gradients) and painting
    def lin(self, p0, c0, p1, c1, ease=None):
        """linear colour gradient from p0 (colour c0) to p1 (colour c1)"""
        d = np.array(p1, f32) - np.array(p0, f32)
        t = np.clip(((self.XX - p0[0]) * d[0] + (self.YY - p0[1]) * d[1]) / (d @ d + 1e-6), 0, 1)
        if ease: t = t ** ease
        return _c(c0) + (_c(c1) - _c(c0)) * t[..., None]

    def rad(self, cx, cy, rx, ry, c0, c1, power=1.0):
        t = np.clip(np.hypot((self.XX - cx) / rx, (self.YY - cy) / ry), 0, 1) ** power
        return _c(c0) + (_c(c1) - _c(c0)) * t[..., None]

    @staticmethod
    def _bbox(m):
        r = np.flatnonzero(m.any(1)); c = np.flatnonzero(m.any(0))
        if not len(r): return None
        return slice(r[0], r[-1] + 1), slice(c[0], c[-1] + 1)

    def paint(self, mask, colour, alpha=1.0, form=0.0, form_r=24.0, light=(-0.55, -0.83)):
        """lay a colour (or colour field) over the surfaces. form > 0 rounds the shape: darker towards its outline,
        lighter on the side facing `light` (a direction in the picture plane)"""
        bb = self._bbox(mask)
        if bb is None: return
        ys, xs = bb
        m = mask[ys, xs] * alpha
        col = colour if isinstance(colour, np.ndarray) and colour.ndim == 3 else np.broadcast_to(_c(colour), (1, 1, 3))
        col = col[ys, xs] if col.shape[0] == self.H and col.shape[1] == self.W else np.broadcast_to(col, m.shape + (3,))
        if form:
            pad = int(form_r * 3)
            Y0, Y1 = max(ys.start - pad, 0), min(ys.stop + pad, self.H)
            X0, X1 = max(xs.start - pad, 0), min(xs.stop + pad, self.W)
            s = blur(mask[Y0:Y1, X0:X1], form_r)
            gy, gx = np.gradient(s)
            lx, ly = light
            sh = 1 + form * (np.clip(-(gx * lx + gy * ly) * form_r * 2.2, -1, 1) * 0.6 - (1 - np.clip(s * 2 - 0.2, 0, 1)) * 0.9)
            sh = sh[ys.start - Y0:ys.stop - Y0, xs.start - X0:xs.stop - X0]
            col = col * sh[..., None]
        if self._layer is not None:
            la, lc = self._layer
            lc[ys, xs] += (col - lc[ys, xs]) * m[..., None]
            la[ys, xs] += (1 - la[ys, xs]) * m
            return
        self.alb[ys, xs] += (col - self.alb[ys, xs]) * m[..., None]
        self.em[ys, xs] *= (1 - m[..., None])
        self.patch[ys, xs] *= (1 - m[..., None] * 0.6)

    def emit(self, mask, colour, level=1.0):
        """self-lit: adds light that the room lighting does not touch (flames, lamp shade, sky)"""
        bb = self._bbox(mask)
        if bb is None: return
        ys, xs = bb
        col = colour[ys, xs] if isinstance(colour, np.ndarray) and colour.ndim == 3 else _c(colour)
        self.em[ys, xs] += mask[ys, xs, None] * col * level

    def glow(self, mask, colour, level=0.5):
        """a painted patch of light falling on surfaces (multiplies their colour, unlike emit)"""
        bb = self._bbox(mask)
        if bb is None: return
        ys, xs = bb
        col = colour[ys, xs] if isinstance(colour, np.ndarray) and colour.ndim == 3 else _c(colour)
        self.patch[ys, xs] += mask[ys, xs, None] * col * level

    def shadow(self, mask, strength=0.4, soft=8.0, dx=0.0, dy=0.0):
        """darken the surfaces under a (shifted, blurred) mask: contact and cast shadows"""
        bb = self._bbox(mask)
        if bb is None: return
        ys, xs = bb
        pad = int(soft * 3 + abs(dx) + abs(dy) + 4)
        Y0, Y1 = max(ys.start - pad, 0), min(ys.stop + pad, self.H)
        X0, X1 = max(xs.start - pad, 0), min(xs.stop + pad, self.W)
        s = blur(shift(mask[Y0:Y1, X0:X1], dx, dy), soft) * strength
        tgt = self._layer[1] if self._layer is not None else self.alb
        tgt[Y0:Y1, X0:X1] *= (1 - np.clip(s, 0, 0.95))[..., None]

    def rim(self, mask, toward, colour, level=0.6, width=6.0):
        """edge light on the side of a shape that faces a light source at `toward` (x, y)"""
        cx, cy = toward
        bb = self._bbox(mask)
        if bb is None: return
        ys, xs = bb
        my = (self.YY[ys, xs] * mask[ys, xs]).sum() / (mask[ys, xs].sum() + 1e-6)
        mx = (self.XX[ys, xs] * mask[ys, xs]).sum() / (mask[ys, xs].sum() + 1e-6)
        d = np.array([cx - mx, cy - my], f32); d /= np.linalg.norm(d) + 1e-6
        edge = np.clip(mask - shift(mask, d[0] * width, d[1] * width), 0, 1)
        edge = blur(edge, width * 0.35) * mask
        target = self._layer[1] if self._layer is not None else None
        if target is not None:
            target += edge[..., None] * _c(colour) * level
        else:
            self.em += edge[..., None] * _c(colour) * level

    @contextmanager
    def layer(self, defocus=4.0):
        """paint near objects on their own layer and blur it: out of the camcorder's focus"""
        self._layer = (np.zeros((self.H, self.W), f32), np.zeros((self.H, self.W, 3), f32))
        try:
            yield self
        finally:
            la, lc = self._layer
            self._layer = None
            a = blur(la, defocus); c = _gb(lc * la[..., None], defocus)
            self.alb = self.alb * (1 - a[..., None]) + c
            self.em *= (1 - a[..., None]); self.patch *= (1 - a[..., None] * 0.6)

    # ================================================================ lighting
    def ambient(self, colour='#ffffff', level=0.4):
        self.amb = (_c(colour), level)

    def light(self, x, y, radius, colour='#ffd9a0', power=1.0):
        """a point light with a soft 1 / (1 + (d / radius)^2) fall-off"""
        self.lights.append((x, y, radius, _c(colour), power))

    def _lit(self):
        L = np.broadcast_to(self.amb[0] * self.amb[1], (self.H, self.W, 3)).astype(f32).copy()
        for x, y, r, col, p in self.lights:
            d2 = ((self.XX - x) ** 2 + (self.YY - y) ** 2) / (r * r)
            L += (p / (1 + d2))[..., None] * col
        L += self.patch
        return self.alb * L + self.em

    # ================================================================ the 70s room
    def wallpaper(self, mask, tile=120, base='#e9d8ad', ring='#d4702a', core='#6e3a1c', leaf='#8d8b34',
                  dot='#e0a42c', seam=3, x0=0.0, y0=0.0, contrast=0.8):
        """a 1970s repeat: big orange rings with brown centres staggered with avocado discs, small gold dots;
        printed on paper strips: a faint seam (and a slight drop mismatch) every `seam` tiles"""
        S = 3; T = int(tile * S)
        im = Image.new('RGB', (T, T), tuple(int(v * 255) for v in _c(base)))
        d = ImageDraw.Draw(im)
        col = lambda h: tuple(int(v * 255) for v in (_c(base) + (_c(h) - _c(base)) * contrast))
        def disc(cx, cy, r, c): d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
        for cx, cy in ((0, 0), (T, 0), (0, T), (T, T)):
            disc(cx, cy, 0.24 * T, col(leaf)); disc(cx, cy, 0.135 * T, col(base)); disc(cx, cy, 0.07 * T, col(leaf))
        c = T / 2
        disc(c, c, 0.33 * T, col(ring)); disc(c, c, 0.245 * T, col(base)); disc(c, c, 0.175 * T, col(ring))
        disc(c, c, 0.105 * T, col(core)); disc(c, c, 0.035 * T, col(base))
        for cx, cy in ((c, 0), (0, c), (T, c), (c, T)):
            disc(cx, cy, 0.05 * T, col(dot))
        t = np.asarray(im.resize((tile, tile), Image.LANCZOS), f32) / 255
        ny, nx = self.H // tile + 3, self.W // tile + 3
        big = np.tile(t, (ny, nx, 1))
        ox, oy = int(x0) % tile, int(y0) % tile
        pap = big[tile - oy:tile - oy + self.H, tile - ox:tile - ox + self.W]
        # strip seams and a small drop mismatch
        strip = int(tile * seam)
        k = ((self.XX - x0) // strip).astype(np.int32)
        pap = np.where((k % 2 == 1)[..., None], np.roll(pap, 3, axis=0), pap)
        sx = np.abs(((self.XX - x0) % strip))
        seamline = np.exp(-(np.minimum(sx, strip - sx) ** 2) / 1.2)
        pap = pap * (1 - 0.12 * seamline[..., None])
        pap = pap * (0.97 + 0.06 * noise2d(self.H, self.W, 180, 3, self._seed()))[..., None]
        self.paint(mask, pap)

    def paneling(self, mask, grooves, base='#6b4226', dark='#2a170c', grain=0.22):
        """dark walnut wall panels: vertical grain, boards a shade apart, V-grooves at the x positions given"""
        H, W = self.H, self.W
        g = noise2d(H // 8 + 2, W, 3, 3, self._seed())[:H // 8 + 2]
        g = np.asarray(Image.fromarray(g).resize((W, H), Image.BICUBIC), f32)
        tone = np.ones((H, W), f32)
        xs = sorted(grooves)
        for i in range(len(xs) + 1):
            a = xs[i - 1] if i else -1e9; b = xs[i] if i < len(xs) else 1e9
            tone[(self.XX >= a) & (self.XX < b)] = 0.86 + 0.24 * self.rng.random()
        col = _c(base) * (tone * (1 - grain + grain * 2 * g))[..., None]
        self.paint(mask, col)
        for x in xs:
            w = max(1.5, 4.0 * min(1.0, (300 - x) / 200 + 0.4))
            self.paint(mask * self.rect(x - w / 2, 0, x + w / 2, H), dark, 0.85)
            self.paint(mask * self.rect(x + w / 2, 0, x + w / 2 + 2, H), _c(base) * 1.35, 0.5)

    def ceiling(self, mask, colour='#e8dcc4'):
        """popcorn ceiling: off-white with a fine stipple"""
        n = noise2d(self.H, self.W, 6, 2, self._seed())
        self.paint(mask, _c(colour) * (0.9 + 0.12 * n)[..., None])

    def shag(self, mask, colour='#c48f2c', y_far=None, y_near=None):
        """shag carpet: mottled pile with tufts that get bigger towards the camera"""
        H, W = self.H, self.W
        lo = noise2d(H, W, 140, 3, self._seed())
        hi = noise2d(H, W, 5, 2, self._seed())
        mid = noise2d(H, W, 22, 2, self._seed())
        tuft = noise2d(H, W, 2.2, 1, self._seed())
        v = 0.74 + 0.24 * lo + 0.3 * (mid - 0.5) + 0.3 * (hi - 0.5) + 0.22 * (tuft - 0.5)
        self.paint(mask, _c(colour) * v[..., None])

    def curtain(self, x0, x1, y0, y1, colour='#c8561e', motif='#f0b44a', folds=5, gather=0.0, seed=None):
        """lined drapes: sinusoidal folds shaded across, a loose flower motif that follows the folds"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        w = x1 - x0
        hem = fbm1d(64, 10, 2, int(r.integers(1 << 30))) * 6
        pts = [(x0, y0), (x1, y0)] + [(x1 - w * i / 63, y1 + hem[i]) for i in range(64)]
        m = self.poly(pts)
        u = (self.XX - x0) / max(w, 1)
        ph = u * folds * 2 * np.pi + 0.6 * np.sin(self.YY / 90 + r.random() * 6)
        fold = 0.5 + 0.5 * np.cos(ph)
        col = _c(colour) * (0.62 + 0.5 * fold)[..., None]
        self.paint(m, col)
        # flower motif: five-petal daisies on a staggered grid, squeezed in the fold shadows
        step = w / 2.2
        petals, centres = [], []
        for j in range(int((y1 - y0) / step) + 2):
            for i in range(4):
                cx = x0 + (i + 0.5 * (j % 2)) * step * 0.95 + r.normal(0, 4)
                cy = y0 + 40 + j * step * 0.9 + r.normal(0, 4)
                if not (x0 + 8 < cx < x1 - 8 and cy < y1 - 20): continue
                rr = step * 0.2
                for a in np.linspace(0, 2 * np.pi, 5, endpoint=False) + r.uniform(0, 1):
                    t = np.linspace(0, 2 * np.pi, 24, endpoint=False)
                    ex, ey = np.cos(t) * rr * 0.75, np.sin(t) * rr * 0.5
                    petals.append(np.stack([cx + np.cos(a) * rr + ex * np.cos(a) - ey * np.sin(a),
                                            cy + np.sin(a) * rr + ex * np.sin(a) + ey * np.cos(a)], 1))
                t = np.linspace(0, 2 * np.pi, 20, endpoint=False)
                centres.append(np.stack([cx + np.cos(t) * rr * 0.45, cy + np.sin(t) * rr * 0.45], 1))
        bb = (x0, y0, x1, y1 + 10)
        pm = self._mask(bb, lambda d, T, ss: [d.polygon(T(q), fill=255) for q in petals])
        cm = self._mask(bb, lambda d, T, ss: [d.polygon(T(q), fill=255) for q in centres])
        self.paint(pm * m, _c(motif) * (0.62 + 0.5 * fold)[..., None], 0.85)
        self.paint(cm * m, _c('#6b2e12') * (0.62 + 0.5 * fold)[..., None], 0.9)
        self.shadow(m, 0.25, 10, 8, 4)
        return m

    def window(self, x0, y0, x1, y1, sky=('#1d2e63', '#3d5fa0', '#c98a6a'), frame='#efe6d2', bars=(1, 1)):
        """a sash window at dusk: emissive sky gradient, a neighbour's roof and a tree as silhouettes, one lit
        window across the street, white-painted frame and glazing bars"""
        glass = self.rect(x0, y0, x1, y1)
        h = y1 - y0
        skyc = self.lin((0, y0), sky[0], (0, y0 + h * 0.62), sky[1])
        lowc = self.lin((0, y0 + h * 0.62), sky[1], (0, y1), sky[2])
        skyf = np.where((self.YY < y0 + h * 0.62)[..., None], skyc, lowc)
        self.paint(glass, '#000000')
        self.emit(glass, skyf, 0.8)
        r = self.rng
        # silhouettes: a roof line with a chimney, a round tree
        roof_y = y0 + h * 0.66
        roof = self.poly([(x0, y1), (x0, roof_y + 20), (x0 + (x1 - x0) * 0.35, roof_y - 30),
                          (x0 + (x1 - x0) * 0.72, roof_y + 15), (x1, roof_y + 10), (x1, y1)]) * glass
        tree = np.clip(sum(self.ellipse(x1 - (x1 - x0) * 0.18 + r.normal(0, 18), y0 + h * 0.5 + r.normal(0, 22),
                                        r.uniform(28, 48), r.uniform(30, 50)) for _ in range(7)), 0, 1) * glass
        self.paint(np.clip(roof + tree, 0, 1), '#000000')
        self.em *= (1 - np.clip(roof + tree, 0, 1)[..., None] * 0.92)
        lw = self.rect(x0 + (x1 - x0) * 0.22, roof_y + 34, x0 + (x1 - x0) * 0.30, roof_y + 64) * glass
        self.emit(lw, '#ffc86a', 0.9)
        # frame and bars
        fw = 16
        fr = np.clip(self.rect(x0 - fw, y0 - fw, x1 + fw, y1 + fw) - glass, 0, 1)
        nx, ny = bars
        for i in range(1, nx + 1):
            x = x0 + (x1 - x0) * i / (nx + 1); fr = np.maximum(fr, self.rect(x - 5, y0, x + 5, y1))
        for j in range(1, ny + 1):
            y = y0 + (y1 - y0) * j / (ny + 1); fr = np.maximum(fr, self.rect(x0, y - 6, x1, y + 6))
        self.paint(fr, frame, form=0.25, form_r=4)
        sill = self.rect(x0 - fw - 14, y1 + fw - 2, x1 + fw + 14, y1 + fw + 14, r=3)
        self.paint(sill, frame, form=0.3, form_r=5)
        self.shadow(sill, 0.35, 6, 0, 8)
        return glass

    def rod(self, x0, x1, y, colour='#b98a3e'):
        m = self.rect(x0, y - 6, x1, y + 6, r=6)
        self.paint(m, colour, form=0.6, form_r=4)
        for x in (x0, x1):
            self.paint(self.ellipse(x, y, 14, 14), colour, form=0.6, form_r=6)

    def console_tv(self, x0, y0, x1, y1, top=12, wood='#6a3f1f', screen_frac=0.62, legs=46, glow=None):
        """a 70s console colour TV: walnut cabinet on splayed legs, curved dark screen in a chrome bezel with a
        reflection, speaker grille and two knobs on the right; `glow` (x, y) puts a warm reflection on the glass"""
        r = self.rng
        yb = y1 - legs
        cab = self.rect(x0, y0, x1, yb, r=6)
        g = noise2d(self.H, self.W // 6 + 2, 2.5, 3, self._seed())
        g = np.asarray(Image.fromarray(g[:, :self.W // 6 + 2]).resize((self.W, self.H), Image.BICUBIC), f32)
        self.paint(cab, _c(wood) * (0.85 + 0.3 * g)[..., None], form=0.25, form_r=8)
        topm = self.poly([(x0 + 4, y0), (x1 - 4, y0), (x1 - 14, y0 - top), (x0 + 14, y0 - top)])
        self.paint(topm, _c(wood) * 1.25)
        for lx, sk in ((x0 + 30, -10), (x1 - 30, 10)):
            self.paint(self.poly([(lx - 7, yb), (lx + 7, yb), (lx + sk + 3, y1), (lx + sk - 3, y1)]), '#2b170a')
        self.shadow(self.rect(x0, yb, x1, y1 + 6), 0.45, 10, 0, 4)
        # screen
        sw = (x1 - x0) * screen_frac
        sx0, sy0, sx1, sy1 = x0 + 22, y0 + 22, x0 + sw, yb - 26
        bez = self.rect(sx0 - 8, sy0 - 8, sx1 + 8, sy1 + 8, r=26)
        self.paint(bez, '#b9b4a8', form=0.5, form_r=5)
        scr = self.rect(sx0, sy0, sx1, sy1, r=30)
        cx, cy = (sx0 + sx1) / 2, (sy0 + sy1) / 2
        self.paint(scr, self.rad(cx - 20, cy - 20, (sx1 - sx0) * 0.7, (sy1 - sy0) * 0.75, '#4a524c', '#161a18'))
        hl = self.shape([(sx0 + 20, sy0 + 30), (sx0 + (sx1 - sx0) * 0.45, sy0 + 14), (sx0 + (sx1 - sx0) * 0.5, sy0 + 26),
                         (sx0 + 24, sy0 + (sy1 - sy0) * 0.4)]) * scr
        self.emit(blur(hl, 4), '#dfe8e0', 0.12)
        refl = self.rect(sx0 + (sx1 - sx0) * 0.08, sy0 + (sy1 - sy0) * 0.12, sx0 + (sx1 - sx0) * 0.3, sy0 + (sy1 - sy0) * 0.5, r=8) * scr
        self.emit(blur(refl, 6), '#7f97d8', 0.1)
        if glow is not None:
            gx, gy = glow
            self.emit(self.ellipse(gx, gy, 26, 16) * scr, '#ffb060', 0.35)
            self.emit(blur(self.ellipse(gx, gy, 60, 38) * scr, 10), '#ff9040', 0.12)
        # speaker grille + knobs
        gx0, gx1 = sx1 + 26, x1 - 20
        grille = self.rect(gx0, y0 + 110, gx1, yb - 26, r=4)
        stripes = 0.75 + 0.25 * (np.sin(self.XX * 1.3) > 0)
        self.paint(grille, _c('#3b2a1c') * stripes[..., None])
        for k, ky in enumerate((y0 + 42, y0 + 84)):
            kx = (gx0 + gx1) / 2
            self.paint(self.ellipse(kx, ky, 17, 17), '#cfc8b8', form=0.7, form_r=6)
            self.paint(self.rect(kx - 2, ky - 15, kx + 2, ky - 2), '#2b2420')
        self.paint(self.rect(gx0, y0 + 102, gx1, y0 + 106), '#d9cfb8', 0.8)
        return scr

    def rabbit_ears(self, x, y, spread=(-70, 60), height=160, colour='#d8d4cc'):
        base = self.ellipse(x, y - 8, 30, 12)
        self.paint(base, '#2a2420', form=0.6, form_r=5)
        for i, dx in enumerate(spread):
            tip = (x + dx * height / 140, y - height * (1 - 0.06 * i))
            self.paint(self.line([(x, y - 14), tip], 3), colour)
            self.paint(self.ellipse(tip[0], tip[1], 4, 4), colour)

    def floor_lamp(self, x, y_floor, y_shade, shade_w=130, shade_h=92, pole='#b58a3a', shade='#f3dfb0', power=1.0):
        """a floor lamp with a drum shade: brass pole, weighted base, the shade glows and throws a scallop of light
        up and down the wall"""
        self.paint(self.line([(x, y_shade + shade_h), (x, y_floor - 6)], 6), pole, form=0.5, form_r=3)
        self.paint(self.ellipse(x, y_floor - 4, 46, 11), '#4a3a22', form=0.5, form_r=5)
        self.shadow(self.ellipse(x, y_floor, 60, 12), 0.5, 7)
        # light scallops on the wall above and below the shade
        up = self.poly([(x - shade_w * 0.4, y_shade), (x + shade_w * 0.4, y_shade), (x + shade_w * 1.6, y_shade - 420),
                        (x - shade_w * 1.6, y_shade - 420)])
        up = blur(up * smoothstep(y_shade - 430, y_shade - 10, self.YY), 26)
        dn = self.poly([(x - shade_w * 0.5, y_shade + shade_h), (x + shade_w * 0.5, y_shade + shade_h),
                        (x + shade_w * 1.5, y_floor), (x - shade_w * 1.5, y_floor)])
        dn = blur(dn * smoothstep(y_floor + 40, y_shade + shade_h, self.YY), 30)
        self.glow(up, '#ffcf8a', 0.38 * power)
        self.glow(dn, '#ffcf8a', 0.2 * power)
        sm = self.poly([(x - shade_w / 2 + 12, y_shade), (x + shade_w / 2 - 12, y_shade),
                        (x + shade_w / 2, y_shade + shade_h), (x - shade_w / 2, y_shade + shade_h)])
        lum = self.lin((0, y_shade), '#ffe9bf', (0, y_shade + shade_h), '#fff6dc')
        seams = 1 - 0.08 * (np.abs(((self.XX - x) / (shade_w / 5)) % 1 - 0.5) < 0.04)
        self.paint(sm, _c(shade) * 0.45 * seams[..., None])
        self.emit(sm, lum * seams[..., None] * self.lin((x - shade_w / 2, 0), '#d8b890', (x + shade_w / 2, 0), '#ffffff'), 1.25 * power)
        self.emit(blur(sm, 20), '#ffc070', 0.25 * power)
        for yy in (y_shade, y_shade + shade_h - 7):                     # brass trim bands
            k = (yy - y_shade) / shade_h
            ww = shade_w / 2 - 12 + 12 * k
            self.paint(self.rect(x - ww - 1, yy, x + ww + 1, yy + 7), '#7a4e22')
        self.paint(self.line([(x, y_shade - 18), (x, y_shade)], 4), pole)
        self.paint(self.ellipse(x, y_shade - 20, 6, 6), pole, form=0.5, form_r=3)
        self.emit(self.rect(x - shade_w / 2, y_shade + shade_h - 5, x + shade_w / 2, y_shade + shade_h), '#ffffff', 0.5 * power)
        self.light(x, y_shade + shade_h * 0.5, 520, '#ffc98a', 0.45 * power)
        return sm

    def sofa(self, x0, x1, y_back, y_seat, y_front, y_floor, colour='#a8481f', cushions=3, arm=70):
        """a velour three-seater seen from the front: rolled arms, tufted back cushions, seat cushions with front
        faces, a dark skirt; returns the seat line y for things sitting on it"""
        c = _c(colour)
        body = self.rect(x0, y_back + 30, x1, y_floor - 8, r=18)
        self.paint(body, c * 0.72)
        w = (x1 - x0 - 2 * arm) / cushions
        for i in range(cushions):
            a = x0 + arm + i * w
            back = self.rect(a + 3, y_back + 8 * (i % 2), a + w - 3, y_seat + 12, r=26)
            self.paint(back, c, form=0.55, form_r=18)
            for bx in (a + w * 0.33, a + w * 0.66):
                for by in (y_back + 50, y_back + 100):
                    if by < y_seat - 10:
                        self.paint(self.ellipse(bx, by, 5, 4), c * 0.5)
                        self.shadow(self.ellipse(bx, by, 9, 7), 0.25, 4)
            seat = self.rect(a + 2, y_seat, a + w - 2, y_front, r=14)
            self.paint(seat, c * 1.06, form=0.45, form_r=14)
            self.paint(self.rect(a + 6, y_seat + 6, a + w - 6, y_seat + 18, r=6), c * 1.18, 0.6)
        for ax in (x0, x1 - arm):
            armm = self.rect(ax, y_back + 70, ax + arm, y_front + 6, r=30)
            self.paint(armm, c * 0.98, form=0.6, form_r=16)
        skirt = self.rect(x0 + 6, y_front, x1 - 6, y_floor - 8)
        self.paint(skirt, c * 0.55)
        self.shadow(self.rect(x0, y_floor - 12, x1, y_floor + 4), 0.6, 9, 0, 3)
        return y_seat

    def balloon(self, x, y, r, colour, string_to=None, sag=30, rot=0.0):
        """a latex balloon: egg-shaped body, tied knot, soft shading, a window-shaped specular glint, string"""
        c = _c(colour)
        if string_to is not None:
            p0 = np.array([x + np.sin(np.radians(rot)) * r * 1.2, y + r * 1.25]); p1 = np.array(string_to, f32)
            mid = (p0 + p1) / 2 + np.array([sag, 0])
            self.paint(self.line(spline([p0, mid, p1], 12), 1.6), '#d9d2c4', 0.8)
        body = self.ellipse(x, y, r, r * 1.16, rot=rot)
        sh = self.rad(x - r * 0.35, y - r * 0.45, r * 1.5, r * 1.6, c * 1.25, c * 0.45, 1.3)
        self.paint(body, sh)
        self.shadow(body, 0.25, 14, 16, 22)
        kx, ky = x + np.sin(np.radians(rot)) * r * 1.16, y + np.cos(np.radians(rot)) * r * 1.16
        self.paint(self.poly([(kx - 7, ky + 9), (kx + 7, ky + 9), (kx, ky - 3)]), c * 0.7)
        g = self.ellipse(x - r * 0.38, y - r * 0.48, r * 0.16, r * 0.24, rot=30)
        self.emit(blur(g, 2), '#ffffff', 0.55)

    def streamer(self, p0, p1, sag, colour, width=16, twists=9, hang=0.0):
        """a twisted crepe-paper streamer hung between two points: the band narrows and flips at every half-turn"""
        P = spline([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + sag), p1], 40)
        n = len(P)
        tan = np.gradient(P, axis=0); tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
        ph = np.linspace(0, twists * np.pi, n)
        hw = width / 2 * (0.15 + 0.85 * np.abs(np.cos(ph)))
        c = _c(colour)
        quads, faces = [], []
        for i in range(n - 1):
            quads.append([P[i] + nrm[i] * hw[i], P[i + 1] + nrm[i + 1] * hw[i + 1], P[i + 1] - nrm[i + 1] * hw[i + 1],
                          P[i] - nrm[i] * hw[i]])
            faces.append(0.72 + 0.4 * (np.cos(ph[i]) > 0) * np.abs(np.cos(ph[i])))
        bb = (P[:, 0].min() - width, P[:, 1].min() - width, P[:, 0].max() + width, P[:, 1].max() + width)
        cov = self._mask(bb, lambda d, T, ss: [d.polygon(T(q), fill=255) for q in quads])
        val = self._mask(bb, lambda d, T, ss: [d.polygon(T(q), fill=int(255 * f / 1.2)) for q, f in zip(quads, faces)])
        self.paint(cov, c * (val / (cov + 1e-4) * 1.2)[..., None])
        self.shadow(self.line(P, width * 0.6), 0.18, 8, 6, 12)

    def pennants(self, p0, p1, sag, letters, colours, size=96, letter='#fff6e0', dark_letter='#4a2412', seed=None):
        """a string of paper pennants with one hand-cut letter each, hanging along a sagging cord; the cord
        casts a soft shadow on the wall"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        n = len(letters)
        P = spline([p0, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2 + sag), p1], 60)
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        L = s[-1]
        cord = self.line(P, 2.2)
        self.shadow(cord, 0.25, 4, 5, 9)
        self.paint(cord, '#efe8d8')
        slot = L / n
        k = 0
        for i, ch in enumerate(letters):
            if ch == ' ': continue
            sa, sb = (i + 0.08) * slot, (i + 0.92) * slot
            a = np.array([np.interp(sa, s, P[:, 0]), np.interp(sa, s, P[:, 1])])
            b = np.array([np.interp(sb, s, P[:, 0]), np.interp(sb, s, P[:, 1])])
            mid = (a + b) / 2
            d = b - a; ang = np.arctan2(d[1], d[0]) + r.normal(0, 0.05)
            dn = np.array([-np.sin(ang), np.cos(ang)])
            tip = mid + dn * size + np.array([r.normal(0, 4), 0])
            tri = self.poly([a, b, tip])
            col = _c(colours[k % len(colours)]); k += 1
            self.shadow(tri, 0.3, 7, 7, 12)
            self.paint(tri, self.lin(tuple(mid), col * 1.08, tuple(tip), col * 0.82), form=0.15, form_r=6)
            cpos = mid + dn * size * 0.36
            tm = self.text(ch, cpos[0], cpos[1], size * 0.42, 'rounded', rot=-np.degrees(ang) + r.normal(0, 4))
            lum = col @ np.array([0.299, 0.587, 0.114], f32)
            self.paint(tm * tri, dark_letter if lum > 0.55 else letter)

    def coffee_table(self, quad, thick=16, wood='#7b4a24', legs=None, gloss=None):
        """a teak coffee table top seen from above-front: quad = [back-left, back-right, front-right, front-left];
        grain runs left-right, a soft sheen where the lamp reflects (gloss = (x, y))"""
        bl, br, fr, fl = [np.array(p, f32) for p in quad]
        top = self.poly([bl, br, fr, fl])
        g = noise2d(self.H // 10 + 2, self.W, 4, 3, self._seed())[:self.H // 10 + 2]
        g = np.asarray(Image.fromarray(g).resize((self.W, self.H), Image.BICUBIC), f32)
        g2 = noise2d(self.H, self.W, 60, 2, self._seed())
        col = _c(wood) * (0.8 + 0.28 * g + 0.12 * g2)[..., None]
        col = col * self.lin((0, bl[1]), '#d0d0d0', (0, fl[1]), '#ffffff')
        self.paint(top, col)
        if gloss is not None:
            self.glow(blur(self.ellipse(gloss[0], gloss[1], 260, 34) * top, 24), '#ffd9a8', 0.7)
        edge = self.poly([fl, fr, fr + [0, thick], fl + [0, thick]])
        self.paint(edge, _c(wood) * 0.55)
        if legs:
            for lx, ly0, ly1 in legs:
                self.paint(self.poly([(lx - 9, ly0), (lx + 9, ly0), (lx + 5, ly1), (lx - 5, ly1)]), _c(wood) * 0.5)
        return top

    def cake(self, cx, cy, rx, ry, h, candles, frosting='#fbf1e2', piping='#f08aa6', sprinkles=None, plate='#e6e2dc',
             lean=(1.0, -0.2), seed=None):
        """a round frosted cake on a plate: cylinder side shaded around, top ellipse, piped rosettes on the top and
        bottom rims, sprinkles, candles in a ring. candles: [(angle deg, colour, state)], state 'lit' = burning
        (the flame bends along `lean`), a number 0..1 = just blown out, trailing that much smoke (0 = cold).
        Returns the flame centres (put a `light` on each)."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        fc = _c(frosting)
        plt = self.ellipse(cx, cy + h + 4, rx * 1.28, ry * 1.3)
        self.shadow(plt, 0.5, 10, 0, 8)
        self.paint(plt, self.lin((cx - rx, 0), _c(plate) * 0.8, (cx + rx, 0), _c(plate)))
        self.emit(blur(self.ellipse(cx - rx * 0.6, cy + h + 4 + ry * 0.75, rx * 0.35, 4) * plt, 2), '#ffffff', 0.25)
        side = np.clip(self.rect(cx - rx, cy, cx + rx, cy + h) + self.ellipse(cx, cy + h, rx, ry), 0, 1)
        u = np.clip((self.XX - cx) / rx, -1, 1)
        shade = 0.55 + 0.45 * np.sqrt(np.clip(1 - u ** 2, 0, 1)) * (1 - 0.25 * u)
        self.paint(side, fc * shade[..., None])
        topm = self.ellipse(cx, cy, rx, ry)
        self.paint(topm, self.lin((cx - rx, cy - ry), fc * 1.05, (cx + rx, cy + ry), fc * 0.9))
        # piped rosettes: bottom rim (front half), top rim (all round, back ones first)
        def rosette(x, y, s):
            m = self.ellipse(x, y, s, s * 0.8)
            self.paint(m, _c(piping), form=0.7, form_r=max(2, s * 0.6))
        for a in np.linspace(0.08, np.pi - 0.08, 15):
            rosette(cx + np.cos(a) * rx, cy + h + np.sin(a) * ry, rx * 0.075)
        for a in sorted(np.linspace(0, 2 * np.pi, 22, endpoint=False), key=lambda a: np.sin(a)):
            rosette(cx + np.cos(a) * rx * 0.97, cy + np.sin(a) * ry * 0.97 - 2, rx * 0.06)
        if sprinkles:
            for _ in range(46):
                a, rr = r.uniform(0, 2 * np.pi), np.sqrt(r.uniform(0, 0.7))
                sx, sy = cx + np.cos(a) * rx * rr, cy + np.sin(a) * ry * rr
                ang = r.uniform(0, 180)
                self.paint(self.ellipse(sx, sy, 5, 1.8, rot=ang, n=16), sprinkles[r.integers(len(sprinkles))])
        tips = []
        order = sorted(candles, key=lambda c: np.sin(np.radians(c[0])))
        for ang, ccol, state in order:
            a = np.radians(ang)
            bx, by = cx + np.cos(a) * rx * 0.6, cy + np.sin(a) * ry * 0.6
            ch = h * 0.62
            body = self.rect(bx - 4.5, by - ch, bx + 4.5, by)
            stripe = (np.sin((self.XX - bx) * 0.9 + (self.YY - by) * 0.55) > 0)
            self.paint(body, np.where(stripe[..., None], _c(ccol), _c('#fff4e4')) * self.lin((bx - 5, 0), '#c8c8c8', (bx + 5, 0), '#ffffff'))
            self.paint(self.ellipse(bx, by - ch, 4.5, 1.8), '#fff4e4')
            self.paint(self.line([(bx, by - ch), (bx + 0.5, by - ch - 7)], 1.6), '#1c1410')
            wick = (bx + 0.5, by - ch - 7)
            if state == 'lit' or state is True:
                lx, ly = lean
                fl = 30
                tip = (wick[0] + lx * fl * 0.55, wick[1] - fl + abs(ly) * 4)
                mid = (wick[0] + lx * fl * 0.2, wick[1] - fl * 0.45)
                outer = self.shape([(wick[0] - 5, wick[1] + 1), (mid[0] - 7, mid[1]), tip, (mid[0] + 7, mid[1] + 3),
                                    (wick[0] + 5, wick[1] + 1)], per=8)
                inner = self.shape([(wick[0] - 2.5, wick[1] - 1), (mid[0] - 3, mid[1] + 2),
                                    (wick[0] + lx * fl * 0.42, wick[1] - fl * 0.72), (mid[0] + 3, mid[1] + 4),
                                    (wick[0] + 2.5, wick[1] - 1)], per=8)
                self.emit(blur(outer, 1.2), '#ff9a3a', 1.6)
                self.emit(blur(inner, 1.0), '#fff2c0', 3.2)
                self.emit(blur(self.ellipse(wick[0], wick[1] + 1, 4, 3), 1), '#5a7cff', 0.6)
                tips.append(((wick[0] + tip[0]) / 2, (wick[1] + tip[1]) / 2))
            elif state:
                self.smoke(wick[0], wick[1], 170 * state, drift=lean[0] * 46, seed=int(r.integers(1 << 30)))
                self.emit(self.ellipse(wick[0], wick[1], 1.6, 1.6), '#ff6a20', 0.9)
        return tips

    def smoke(self, x, y, height, drift=30.0, width=2.8, opacity=0.62, seed=None):
        """a thin wisp from a just-blown-out wick: a hair-thin ribbon that rises, drifts, starts to curl, widens and
        thins out (grey, not lit -- it must not read as another flame)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        n = 48
        t = np.linspace(0, 1, n)
        ph = r.uniform(0, 6.3)
        wob = fbm1d(n, 9, 3, int(r.integers(1 << 30))) * 20 * t ** 1.2 + np.sin(t * 9 + ph) * 9 * t ** 1.5
        pts = np.stack([x + drift * t ** 1.3 + wob, y - height * t], 1)
        x0, y0 = pts.min(0) - 20; x1, y1 = pts.max(0) + 20
        op = opacity * smoothstep(0.0, 0.12, t) * (1 - t) ** 1.3
        def dr(d, T, ss):
            Q = T(pts)
            for i in range(n - 1):
                d.line([Q[i], Q[i + 1]], fill=int(255 * op[i]), width=max(1, int(width * (0.6 + 2.6 * t[i]) * ss)))
        m = self._mask((x0, y0, x1, y1), dr)
        self.paint(blur(m, 1.3), '#cfc9c2')

    def present(self, x, y, w, h, d, paper='#c8302a', stripe='#f4e6c8', ribbon='#f2c230'):
        """a wrapped box seen slightly from above and the left: front face, lid, right side; diagonal stripes,
        ribbon crossing over, a looped bow"""
        p = _c(paper); s = _c(stripe)
        front = self.rect(x, y, x + w, y + h)
        top = self.poly([(x, y), (x + w, y), (x + w + d * 0.6, y - d * 0.55), (x + d * 0.6, y - d * 0.55)])
        side = self.poly([(x + w, y), (x + w + d * 0.6, y - d * 0.55), (x + w + d * 0.6, y + h - d * 0.55), (x + w, y + h)])
        st = (((self.XX + self.YY) / 22) % 1) < 0.42
        for m, k in ((front, 0.95), (top, 1.12), (side, 0.66)):
            self.paint(m, np.where(st[..., None], s, p) * k)
        self.shadow(np.clip(front + side, 0, 1), 0.5, 9, 10, 8)
        rb = _c(ribbon)
        self.paint(self.rect(x + w * 0.45, y, x + w * 0.55, y + h) * front, rb * 0.95)
        self.paint(self.poly([(x + w * 0.45, y), (x + w * 0.55, y), (x + w * 0.55 + d * 0.6, y - d * 0.55),
                              (x + w * 0.45 + d * 0.6, y - d * 0.55)]) * top, rb * 1.1)
        self.paint(self.poly([(x + w * 0.3 + d * 0.33, y - d * 0.33), (x + w * 0.3 + d * 0.22, y - d * 0.2),
                              (x + w + d * 0.6, y - d * 0.3), (x + w + d * 0.6, y - d * 0.4)]) * top, rb * 1.05)
        bx, by = x + w * 0.5 + d * 0.3, y - d * 0.3
        for sgn in (-1, 1):
            loop = self.ellipse(bx + sgn * 20, by - 12, 22, 13, rot=-sgn * 25)
            self.paint(loop, rb, form=0.6, form_r=6)
            self.paint(self.ellipse(bx + sgn * 21, by - 12, 9, 4, rot=-sgn * 25), rb * 0.55)
        self.paint(self.ellipse(bx, by - 6, 9, 8), rb * 0.9, form=0.6, form_r=4)

    def cup(self, x, y, w, h, colour='#d23a2e', stripe='#f6efe0', stripes=6):
        """a striped paper party cup, slightly tapered, with a dark inside at the rim"""
        m = self.poly([(x - w / 2, y - h), (x + w / 2, y - h), (x + w * 0.38, y), (x - w * 0.38, y)])
        u = (self.XX - x) / (w / 2)
        st = (np.sin((u * 1.25 + 1) * stripes * np.pi / 2) > 0)
        col = np.where(st[..., None], _c(colour), _c(stripe)) * (0.6 + 0.45 * np.sqrt(np.clip(1 - u ** 2, 0, 1)))[..., None]
        self.shadow(m, 0.4, 6, 8, 6)
        self.paint(m, col)
        self.paint(self.ellipse(x, y - h, w / 2, w * 0.14), '#f6efe0')
        self.paint(self.ellipse(x, y - h + 1, w / 2 - 3, w * 0.11), '#3a2216')

    def plates(self, x, y, rx, ry, n=4, colour='#fbf6ea', rim='#e8a23a'):
        for i in range(n):
            yy = y - i * 3
            self.paint(self.ellipse(x, yy, rx, ry), _c(colour) * (0.86 + 0.04 * i))
        self.paint(self.ellipse(x, y - (n - 1) * 3, rx * 0.93, ry * 0.9) - self.ellipse(x, y - (n - 1) * 3, rx * 0.8, ry * 0.76), rim)
        self.shadow(self.ellipse(x, y + 4, rx, ry), 0.4, 7, 6, 4)

    def blower(self, x, y, length=90, colour='#2f6fc8', curl=3.0, seed=None):
        """a party blower lying on the table: mouthpiece and a curled paper tube"""
        t = np.linspace(0, 1, 50)
        rr = 18 * (1 - t * 0.55)
        a = t * curl * np.pi
        pts = np.stack([x + length * 0.45 + rr * np.sin(a) + t * 30, y - rr * (1 - np.cos(a)) * 0.6], 1)
        self.paint(self.line([(x, y), (x + length * 0.45, y)], 9), colour, form=0.4, form_r=3)
        self.paint(self.line(pts, 8), colour, form=0.4, form_r=3)
        self.paint(self.line([(x - 18, y), (x, y)], 7), '#f0e0b0')

    def confetti(self, region, n=60, colours=('#e04848', '#f2c230', '#3a8ad8', '#5cb85c', '#f08ab0'), size=4.0):
        x0, y0, x1, y1 = region
        r = self.rng
        for _ in range(n):
            x, y = r.uniform(x0, x1), r.uniform(y0, y1)
            self.paint(self.ellipse(x, y, size, size * 0.6, rot=r.uniform(0, 180), n=12), colours[r.integers(len(colours))])

    def teddy(self, cx, cy, s, fur='#9a6a3a', muzzle='#d9b48a', hat=('#3a8ad8', '#f2c230')):
        """a plush bear sitting up (a toy: button eyes are fine), wearing a little party hat"""
        f = _c(fur)
        body = self.ellipse(cx, cy + s * 0.9, s * 0.72, s * 0.8)
        self.shadow(body, 0.4, 12, 10, 14)
        self.paint(body, f, form=0.6, form_r=s * 0.3)
        self.paint(self.ellipse(cx, cy + s * 1.0, s * 0.42, s * 0.48), _c(muzzle) * 0.95, form=0.4, form_r=s * 0.2)
        for sx in (-1, 1):
            self.paint(self.ellipse(cx + sx * s * 0.62, cy + s * 0.75, s * 0.2, s * 0.42, rot=sx * 25), f * 0.92,
                       form=0.6, form_r=s * 0.12)
            self.paint(self.ellipse(cx + sx * s * 0.45, cy + s * 1.62, s * 0.3, s * 0.22), f, form=0.6, form_r=s * 0.12)
            self.paint(self.ellipse(cx + sx * s * 0.47, cy + s * 1.66, s * 0.17, s * 0.13), _c(muzzle))
            self.paint(self.ellipse(cx + sx * s * 0.52, cy - s * 0.42, s * 0.2, s * 0.2), f, form=0.6, form_r=s * 0.1)
            self.paint(self.ellipse(cx + sx * s * 0.52, cy - s * 0.42, s * 0.1, s * 0.1), _c(muzzle) * 0.9)
        head = self.ellipse(cx, cy, s * 0.55, s * 0.5)
        self.paint(head, f, form=0.6, form_r=s * 0.25)
        self.paint(self.ellipse(cx, cy + s * 0.16, s * 0.22, s * 0.16), _c(muzzle), form=0.4, form_r=s * 0.1)
        self.paint(self.ellipse(cx, cy + s * 0.08, s * 0.08, s * 0.06), '#24160c')
        for sx in (-1, 1):
            self.paint(self.ellipse(cx + sx * s * 0.2, cy - s * 0.06, s * 0.055, s * 0.055), '#140c08')
        ha, hb = hat
        cone = self.poly([(cx - s * 0.26, cy - s * 0.4), (cx + s * 0.22, cy - s * 0.44), (cx + s * 0.1, cy - s * 1.05)])
        st = ((self.XX * 0.6 - self.YY) / 14 % 1) < 0.5
        self.paint(cone, np.where(st[..., None], _c(ha), _c(hb)), form=0.3, form_r=6)
        self.paint(self.ellipse(cx + s * 0.1, cy - s * 1.06, s * 0.09, s * 0.09), '#f4eee0', form=0.5, form_r=3)

    def child_back(self, hx, hy, s, hair='#3e2414', shirt='#2f8a84', collar='#e9dcc0', skin='#c88e66',
                   hat=('#e23d5a', '#ffd23a'), pom='#f2efe6', lean=24.0, glow_from=None, seed=None):
        """a small child seen from behind, leaning towards the cake: sloping shoulders in a ringer tee, the back of a
        round head of hair with a crown whorl, both ears, a striped cone party hat tipped towards the cake with its
        elastic; rim-lit on the side that faces the candles (`glow_from`). Paint it on a defocus layer."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        yb = self.H + 80
        sc = _c(shirt)
        for sx in (-1, 1):                                      # upper arms hang to the elbows; forearms go forward
            arm = self.poly(spline([(hx + sx * 0.95 * s, hy + 1.25 * s), (hx + sx * 1.45 * s, hy + 1.35 * s),
                                    (hx + sx * 1.72 * s, hy + 1.9 * s), (hx + sx * 1.8 * s, hy + 2.55 * s),
                                    (hx + sx * 1.62 * s, hy + 2.95 * s), (hx + sx * 1.3 * s, hy + 2.75 * s),
                                    (hx + sx * 1.12 * s, hy + 2.1 * s), (hx + sx * 0.95 * s, hy + 1.25 * s)], 8))
            self.paint(arm, sc * 0.92, form=0.6, form_r=s * 0.22, light=(0.7, -0.7))
        body = [(hx - 1.25 * s, yb), (hx - 1.22 * s, hy + 2.4 * s), (hx - 1.3 * s, hy + 1.6 * s), (hx - 1.05 * s, hy + 1.22 * s),
                (hx - 0.42 * s, hy + 1.02 * s), (hx + 0.42 * s, hy + 1.0 * s), (hx + 1.08 * s, hy + 1.18 * s),
                (hx + 1.34 * s, hy + 1.58 * s), (hx + 1.26 * s, hy + 2.4 * s), (hx + 1.3 * s, yb)]
        torso = self.poly(spline(body, 10))
        self.paint(torso, sc, form=0.5, form_r=s * 0.4, light=(0.7, -0.7))
        for sx in (-1, 1):                                      # shoulder blades
            self.paint(blur(self.line(spline([(hx + sx * 0.35 * s, hy + 1.55 * s), (hx + sx * 0.62 * s, hy + 2.05 * s),
                                              (hx + sx * 0.5 * s, hy + 2.45 * s)], 8), s * 0.05), s * 0.08), sc * 0.7, 0.6)
        neck = self.rect(hx - 0.3 * s, hy + 0.55 * s, hx + 0.3 * s, hy + 1.12 * s, r=s * 0.12)
        self.paint(neck, skin, form=0.5, form_r=s * 0.12)
        ring = np.clip(self.ellipse(hx, hy + 1.07 * s, 0.5 * s, 0.13 * s) - self.ellipse(hx, hy + 1.0 * s, 0.37 * s, 0.09 * s), 0, 1)
        self.paint(ring * torso, collar)
        for sx in (-1, 1):
            ear = self.ellipse(hx + sx * 0.95 * s, hy + 0.14 * s, 0.2 * s, 0.28 * s, rot=-sx * 14)
            self.paint(ear, skin, form=0.6, form_r=s * 0.08)
            self.paint(self.ellipse(hx + sx * 0.99 * s, hy + 0.14 * s, 0.08 * s, 0.16 * s, rot=-sx * 14), _c(skin) * 0.72)
        head = self.ellipse(hx, hy, 0.9 * s, 1.0 * s)
        hc = _c(hair)
        self.paint(head, hc, form=0.65, form_r=s * 0.4, light=(0.6, -0.8))
        # strands spiralling out of the crown whorl, then a ragged nape
        wx, wy = hx + 0.12 * s, hy - 0.42 * s
        dark, light = [], []
        for k in range(70):
            a0 = r.uniform(0, 2 * np.pi); L = r.uniform(0.5, 1.15) * s
            t = np.linspace(0, 1, 12)
            ang = a0 + 0.9 * t
            pts = np.stack([wx + np.cos(ang) * L * t, wy + np.sin(ang) * L * t * 1.1], 1)
            (dark if k % 3 else light).append(pts)
        for lst, col, k in ((dark, hc * 0.5, 0.9), (light, hc * 2.1, 0.7)):
            m = self._mask((hx - s, hy - s, hx + s, hy + s), lambda d, T, ss, lst=lst: [d.line(T(q), fill=255, width=max(1, int(s * 0.035 * ss))) for q in lst])
            self.paint(m * head, col, k)
        for k in range(9):
            tx = hx - 0.62 * s + k * 0.155 * s + r.normal(0, 0.02 * s)
            tuft = self.poly([(tx - 0.1 * s, hy + 0.66 * s), (tx + 0.1 * s, hy + 0.66 * s), (tx + 0.02 * s, hy + (0.93 + 0.06 * r.random()) * s)])
            self.paint(tuft, hc * 0.95)
        # cone hat tipped towards the cake
        a = np.radians(lean)
        ax_ = np.array([np.sin(a), -np.cos(a)]); px_ = np.array([-ax_[1], ax_[0]])
        tb = np.array([hx + 0.2 * s, hy - 0.72 * s]); hw, hl = 0.6 * s, 1.75 * s
        tip = tb + ax_ * hl
        rim = [tb - px_ * hw + ax_ * 0.0, tb - px_ * hw * 0.5 - ax_ * 0.12 * s, tb - ax_ * 0.16 * s,
               tb + px_ * hw * 0.5 - ax_ * 0.12 * s, tb + px_ * hw]
        cone = self.poly(list(spline(rim, 6)) + [tip])
        u = ((self.XX - tb[0]) * px_[0] + (self.YY - tb[1]) * px_[1]) / hw
        v = ((self.XX - tb[0]) * ax_[0] + (self.YY - tb[1]) * ax_[1]) / hl
        st = ((v * 4.5 + u * 0.55) % 1) < 0.5
        conec = np.where(st[..., None], _c(hat[0]), _c(hat[1])) * (0.62 + 0.42 * np.sqrt(np.clip(1 - u ** 2, 0, 1)) + 0.1 * u)[..., None]
        self.shadow(cone, 0.35, s * 0.08, -s * 0.05, s * 0.1)
        self.paint(cone, conec)
        fr = []
        for k in range(16):
            ang = k / 16 * 2 * np.pi
            fr.append([tuple(tip), tuple(tip + np.array([np.cos(ang), np.sin(ang)]) * s * r.uniform(0.18, 0.28))])
        pm = self._mask((tip[0] - s * 0.4, tip[1] - s * 0.4, tip[0] + s * 0.4, tip[1] + s * 0.4),
                        lambda d, T, ss: [d.line(T(q), fill=255, width=max(1, int(s * 0.07 * ss))) for q in fr])
        self.paint(np.clip(pm + self.ellipse(tip[0], tip[1], s * 0.12, s * 0.12), 0, 1), pom, form=0.4, form_r=s * 0.06)
        for sx in (-1, 1):
            el = spline([tuple(tb + sx * px_ * hw * 0.92), (hx + sx * 0.88 * s, hy - 0.1 * s), (hx + sx * 0.72 * s, hy + 0.62 * s)], 10)
            self.paint(self.line(el, max(1.5, s * 0.025)), '#ece6da', 0.9)
        if glow_from is not None:
            for m in (head, cone, torso, arm):
                self.rim(m, glow_from, '#ffb070', 0.9, width=s * 0.11)
        return head

    # ================================================================ camera, tape, OSD switches
    def camera(self, tilt=-1.4, zoom=1.0, white_balance=(1.08, 0.94, 0.70), exposure=1.0, knee=0.72,
               bloom=0.5, smear=0.22, lag=(-26, 0, 0.35), soft=1.2, vignette=0.26, gain_noise=0.035, seed=None):
        """switch on the camcorder for every later stage.
        tilt: hand-held roll (deg); white_balance: RGB gains (outdoor setting under tungsten = orange);
        knee: where highlights start to roll off; bloom: glow around clipped points; smear: CCD vertical smear
        strength; lag: (dx, dy, strength) comet tail behind highlights; gain_noise: noise in the shadows."""
        self.cam = dict(tilt=tilt, zoom=zoom, wb=np.asarray(white_balance, f32), exposure=exposure, knee=knee,
                        bloom=bloom, smear=smear, lag=lag, soft=soft, vignette=vignette, gain_noise=gain_noise,
                        seed=self._seed() if seed is None else seed)

    def record(self, luma=1.1, chroma=7.0, chroma_v=1.0, delay=4.5, sharpen=1.1, sharp_r=2.6, saturation=0.9):
        """put it on tape: luma low-pass (sigma in samples), chroma low-pass + vertical comb + delay to the right,
        playback edge enhancement (white / dark halos), lower saturation"""
        self.rec_ = dict(luma=luma, chroma=chroma, chroma_v=chroma_v, delay=delay, sharpen=sharpen, sharp_r=sharp_r,
                         saturation=saturation)

    def wear(self, noise=0.03, chroma_noise=0.05, jitter=0.45, flagging=7.0, tracking=(0.84, 0.045), head_switch=7,
             dropouts=24, black=0.06, lines=0.035, seed=None):
        """playback faults: tracking = (centre as a fraction of the height, band height fraction) or None;
        head_switch = number of ruined lines at the bottom; flagging = sideways bend of the top lines (samples)"""
        self.wear_ = dict(noise=noise, chroma_noise=chroma_noise, jitter=jitter, flagging=flagging, tracking=tracking,
                          head_switch=head_switch, dropouts=dropouts, black=black, lines=lines,
                          seed=self._seed() if seed is None else seed)

    # ---- OSD items (character generator)
    def osd_text(self, s, x, y, px=7, colour='#f4f4ee', anchor='l'):
        self.osd.append(('text', s, x, y, px, _c(colour), anchor))

    def rec(self, x, y, px=7):
        """red dot + REC"""
        self.osd.append(('rec', x, y, px))

    def battery(self, x, y, px=7, level=2, of=4):
        self.osd.append(('battery', x, y, px, level, of))

    def counter(self, s, x, y, px=7, anchor='r'):
        self.osd_text(s, x, y, px, anchor=anchor)

    def datestamp(self, time_s, date_s, x, y, px=7, anchor='l'):
        """the burned-in date stamp: time over date"""
        self.osd_text(time_s, x, y, px, anchor=anchor)
        self.osd_text(date_s, x, y + px * 10, px, anchor=anchor)

    def zoom_bar(self, x, y, pos=0.7, px=7, width=300):
        """W [=====|----] T while zooming"""
        self.osd.append(('zoom', x, y, px, pos, width))

    def _osd_layer(self, n):
        """(alpha, colour) of the first n OSD items: dot-matrix glyphs with a black edge"""
        H, W = self.H, self.W
        fg = np.zeros((H, W), f32); fgc = np.zeros((H, W, 3), f32)
        def put(bits, x, y, px, col, anchor='l'):
            dw, dh = px * 0.8, px
            hh, ww = bits.shape
            tw = ww * dw
            if anchor == 'r': x = x - tw
            elif anchor == 'm': x = x - tw / 2
            im = Image.new('L', (int(tw + 2), int(hh * dh + 2)), 0)
            d = ImageDraw.Draw(im)
            for j, i in zip(*np.nonzero(bits)):
                d.rectangle([i * dw, j * dh, (i + 1) * dw - 0.5, (j + 1) * dh - 0.5], fill=255)
            m = np.asarray(im, f32) / 255
            self._put_mask(fg, fgc, m, x, y, col)
        for it in self.osd[:n]:
            kind = it[0]
            if kind == 'text':
                _, s, x, y, px, col, anchor = it
                put(_glyph_bitmap(s), x, y, px, col, anchor)
            elif kind == 'rec':
                _, x, y, px = it
                r = px * 2.6
                m = self.ellipse(x + r, y + px * 3.5, r, r)
                fg[:] = np.maximum(fg, m); fgc += (hexc('#ff2a1e') - fgc) * m[..., None]
                put(_glyph_bitmap('REC'), x + r * 2 + px * 2, y, px, hexc('#f4f4ee'))
            elif kind == 'battery':
                _, x, y, px, level, of = it
                cols = 3 * of + 3
                b = np.zeros((7, cols), np.uint8)
                b[0, :cols - 2] = 1; b[6, :cols - 2] = 1; b[:, 0] = 1; b[:, cols - 3] = 1; b[2:5, cols - 2:] = 1
                for k in range(level): b[2:5, 2 + 3 * k:4 + 3 * k] = 1
                put(b, x, y, px, hexc('#f4f4ee'))
            elif kind == 'zoom':
                _, x, y, px, pos, width = it
                n = max(12, int(width / (px * 0.8)))
                bar = np.zeros((7, n), np.uint8)
                bar[1, :] = 1; bar[5, :] = 1; bar[1:6, 0] = 1; bar[1:6, -1] = 1
                k = int(round(pos * (n - 1)))
                bar[2:5, :k] = 1
                bar[0:7, max(k - 1, 0):k + 1] = 1
                wdots = _glyph_bitmap('W ')
                put(np.concatenate([wdots, bar, np.zeros((7, 2), np.uint8), _glyph_bitmap('T')], 1), x, y, px, hexc('#f4f4ee'))
        # black edge: dilate the glyphs a few px
        e = fg.copy()
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2), (3, 2), (2, 3)):
            e = np.maximum(e, shift(fg, dx, dy))
        edge = np.clip(e, 0, 1)
        return fg, fgc, edge

    def _put_mask(self, fg, fgc, m, x, y, col):
        h, w = m.shape
        x0, y0 = int(round(x)), int(round(y))
        xa, ya = max(x0, 0), max(y0, 0)
        xb, yb = min(x0 + w, self.W), min(y0 + h, self.H)
        if xb <= xa or yb <= ya: return
        sub = m[ya - y0:yb - y0, xa - x0:xb - x0]
        fg[ya:yb, xa:xb] = np.maximum(fg[ya:yb, xa:xb], sub)
        fgc[ya:yb, xa:xb] += (col - fgc[ya:yb, xa:xb]) * sub[..., None]

    # ================================================================ render passes
    def _camera(self, img):
        c = self.cam
        H, W = self.H, self.W
        r = np.random.default_rng(c['seed'])
        th = np.radians(c['tilt'])
        s = (np.cos(abs(th)) + (W / H) * np.sin(abs(th))) * c['zoom']
        # hand-held roll + zoom about the centre (inverse affine for PIL)
        ca, sa = np.cos(th) / s, np.sin(th) / s
        cx, cy = W / 2, H / 2
        A = (ca, -sa, cx - ca * cx + sa * cy, sa, ca, cy - sa * cx - ca * cy)
        img = np.stack([np.asarray(Image.fromarray(img[..., k], 'F').transform((W, H), Image.AFFINE, A, Image.BILINEAR), f32)
                        for k in range(3)], -1)
        img *= c['wb'] * c['exposure']
        lum = img.max(-1)
        if c['lag'] and c['lag'][2] > 0:
            dx, dy, k = c['lag']
            hi = img * (np.clip(lum - 1.2, 0, None) / (lum + 1e-6))[..., None]
            tail = np.zeros_like(img)
            for i in range(1, 9):
                tail = np.maximum(tail, shift(hi, dx * i / 8, dy * i / 8) * (1 - i / 9))
            img += _gb(tail, 2.0) * k
        if c['bloom'] > 0:
            hot = img * (np.clip(lum - 1.0, 0, None) / (lum + 1e-6))[..., None]
            h4 = _resize(hot, W // 4, H // 4, Image.BOX)              # wide radii at quarter resolution
            wide = _resize(_gb(h4, 22 / 4) * 0.35 + _gb(h4, 70 / 4) * 0.25, W, H, Image.BILINEAR)
            img += (_gb(hot, 6) * 0.5 + wide) * c['bloom']
        if c['smear'] > 0:
            hot = np.clip(img - 2.2, 0, None)                      # only point sources far over full-well
            col = _blur_axis(hot.sum(0) / H * 30.0, 0.8, 0)         # the charge spilled while the column is read out
            prof = 0.55 + 0.45 * np.exp(-((self.YY[:, :1] - (np.argmax(hot.max(-1), 0)[None, :])) / 260.0) ** 2)
            img += col[None, :, :] * prof[..., None] * c['smear']
        if c['soft'] > 0:
            img = _gb(img, c['soft'])
        rr = ((self.XX - cx) / cx) ** 2 + ((self.YY - cy) / cy) ** 2
        img *= (1 - c['vignette'] * np.clip(rr / 2, 0, 1) ** 1.3)[..., None]
        # gain noise, worse in the dark, a little blotchy
        lum = img.mean(-1)
        n = blur(r.normal(0, 1, (H, W)).astype(f32), 1.0) * 1.8
        nc = _gb(r.normal(0, 1, (H, W, 2)).astype(f32), 2.0) * 2.0
        amt = c['gain_noise'] * (0.35 + 0.65 * np.clip(1 - lum * 1.6, 0, 1))
        img += (n * amt)[..., None]
        img[..., 0] += nc[..., 0] * amt * 0.6; img[..., 2] += nc[..., 1] * amt * 0.6
        return self._knee(img, c['knee'])

    @staticmethod
    def _knee(x, k):
        x = np.clip(x, 0, None)
        y = np.where(x < k, x, k + (1 - k) * (1 - np.exp(-(x - k) / (1 - k))))
        return np.clip(y, 0, 1).astype(f32)

    def _tape(self, img):
        L, S = self.lines, self.samples
        rc, wr = self.rec_, self.wear_
        a = _resize(img, S, L, Image.BOX)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        Y = 0.299 * R + 0.587 * G + 0.114 * B
        I = 0.596 * R - 0.274 * G - 0.322 * B
        Q = 0.211 * R - 0.523 * G + 0.312 * B
        # luma: band-limited, then the playback sharpness circuit
        Y = _blur_axis(Y, rc['luma'], 1)
        if rc['sharpen']:
            Y = Y + rc['sharpen'] * (Y - _blur_axis(Y, rc['sharp_r'], 1))
        # chroma: colour-under bandwidth, comb filter over neighbouring lines, delay to the right
        C = np.stack([I, Q], -1)
        C = _blur_axis(C, rc['chroma'], 1)
        if rc['chroma_v']: C = _blur_axis(C, rc['chroma_v'], 0)
        C = _rowshift(C, np.full(L, rc['delay'], f32), 0.0)
        C *= rc['saturation']
        if wr:
            r = np.random.default_rng(wr['seed'])
            # streaky luma noise and horizontal chroma noise
            n = _blur_axis(r.normal(0, 1, (L, S)).astype(f32), 1.1, 1) * 1.6
            Y = Y + n * wr['noise'] * (0.6 + 0.8 * np.clip(1 - Y, 0, 1))
            cn = _blur_axis(r.normal(0, 1, (L, S, 2)).astype(f32), 9.0, 1) * 4.0
            C = C + cn * wr['chroma_noise']
            # timebase jitter + flagging at the top
            off = fbm1d(L, 40, 4, int(r.integers(1 << 30))) * wr['jitter'] * 2 + r.normal(0, wr['jitter'] * 0.35, L)
            top = np.arange(L, dtype=f32)
            off += wr['flagging'] * np.exp(-top / 7.0)
            # tracking band
            band = np.zeros(L, f32)
            if wr['tracking']:
                yc, bh = wr['tracking'][0] * L, wr['tracking'][1] * L
                band = np.exp(-((top - yc) / (bh * 0.5)) ** 4).astype(f32)
                off += band * r.normal(0, 1, L) * 9 + band * 6
            # head switching: the last lines slide to the right and tear
            hs = wr['head_switch']
            if hs:
                k = np.clip((top - (L - hs)) / hs, 0, 1)
                off += k ** 1.5 * (18 + r.normal(0, 5, L) * k)
            YC = _rowshift(np.concatenate([Y[..., None], C], -1), off.astype(f32), 0.0)
            Y, C = YC[..., 0], YC[..., 1:]
            # noise inside the tracking band: white streaks, grey hash, ragged
            if wr['tracking']:
                for j in np.flatnonzero(band > 0.05):
                    b = band[j]
                    hsh = _blur_axis(r.normal(0, 1, S).astype(f32)[None, :], 0.8, 1)[0]
                    Y[j] = Y[j] * (1 - 0.45 * b) + 0.45 * b * (0.45 + 0.3 * hsh)
                    for _ in range(int(r.poisson(4.0 * b))):
                        x0 = int(r.integers(0, S)); ln = int(r.integers(6, 70))
                        Y[j, x0:x0 + ln] = np.maximum(Y[j, x0:x0 + ln], r.uniform(0.75, 1.05))
                        if j + 1 < L and r.random() < 0.5:
                            Y[j + 1, x0:x0 + ln] = np.maximum(Y[j + 1, x0:x0 + ln], r.uniform(0.5, 0.8))
                    C[j] *= (1 - 0.6 * b)
            if hs:
                for j in range(L - hs, L):
                    Y[j] = Y[j] * 0.8 + 0.2 * (0.45 + 0.3 * r.normal(0, 1, S).astype(f32))
            # dropouts: short white flecks (with a dark tail)
            for _ in range(int(wr['dropouts'])):
                j = int(r.integers(4, L - 4)); x0 = int(r.integers(0, S - 4)); ln = int(np.clip(r.exponential(9) + 1, 1, 60))
                Y[j, x0:x0 + ln] = r.uniform(0.85, 1.1)
                Y[j, x0 + ln:x0 + ln + 6] *= 0.6
                C[j, x0:x0 + ln] *= 0.2
            # blanking at the left edge (follows the jitter) and a lifted black level
            ledge = np.clip(off, 0, None) + 3 + r.normal(0, 0.6, L)
            Y = np.where(np.arange(S)[None, :] < ledge[:, None], 0.0, Y)
            Y = wr['black'] + Y * (1 - wr['black'] * 0.8)
        Y = Y.astype(f32)
        Ii, Qi = C[..., 0], C[..., 1]
        R = Y + 0.956 * Ii + 0.621 * Qi
        G = Y - 0.272 * Ii - 0.647 * Qi
        B = Y - 1.106 * Ii + 1.703 * Qi
        out = np.clip(np.stack([R, G, B], -1), 0, 1.1)
        up = _resize(out, self.W, self.H, Image.BICUBIC)
        if wr and wr['lines']:
            yy = self.YY[:, :1] * L / self.H
            up *= (1 - wr['lines'] * (0.5 + 0.5 * np.cos(2 * np.pi * yy)))[..., None]
        return np.clip(up, 0, 1)

    def composite(self, n_osd=None):
        img = self._lit()
        if self.cam is not None:
            img = self._camera(img)
        else:
            img = self._knee(img, 0.8)
        n = len(self.osd) if n_osd is None else n_osd
        if n:
            fg, fgc, edge = self._osd_layer(n)
            img = img * (1 - edge * 0.85)[..., None]
            img = img * (1 - fg[..., None]) + fgc * fg[..., None]
        if self.rec_ is not None:
            img = self._tape(img)
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')

    def stage(self, name):
        if self.keep_stages:
            self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f'{stages_dir}/{i:02d}_{name}.png')
            img.save(f'{stages_dir}/{len(self.stages):02d}_final.png')
        return img
