"""aurora — 弥散渐变 · 玻璃拟态: frosted-glass UI cards floating over a soft aurora / mesh gradient
(numpy + Pillow only).

Model: a bright screen of light, then real panes of frosted glass held a little above it, then the interface
printed on the glass.
  backdrop   a mesh gradient: a pale base plus a few large coloured light pools (anisotropic gaussians) and
             aurora ribbons (soft bands along a spline). Every pixel is the weighted average of the pools'
             colours, mixed in OKLab so pink into blue passes through lilac instead of grey mud, on a domain-warped
             grid so the pools wander like dye in water instead of sitting as circles. It is computed at 1/4 size
             (it has no detail to lose), upsampled, then given a fine monochrome grain (+ a little chroma), which
             also kills 8-bit banding. `sparkles()` scatters a few tiny motes of light.
  orbs       glossy pastel spheres floating over the backdrop: wrap-diffuse shading through an iridescent colour
             ramp (lit -> mid -> shade), a Fresnel rim that picks up the backdrop's colour, a tight specular spot
             plus a broad sheen, and a soft coloured contact shadow cast down onto the backdrop. They are sharp
             where they are free and melt into colour where a pane of glass passes in front of them -- which is
             what proves the glass is real.
  glass      a slab of frosted acrylic `elevation` px above what is under it. What you see through it is the
             *actual* pixels below (backdrop, orbs, other cards and their text) gaussian-blurred (the frost
             scatters light; sigma ~ blur), saturated a little (backdrop-filter: saturate), then veiled with milky
             white that is thicker toward the light (upper left) and thinner away from it. At the rim the slab is
             bevelled: over the last `bevel` px the view is bent outward (the rim acts as a lens and pulls in what
             lies just outside the pane), each colour channel by a slightly different amount (dispersion: faint
             colour fringes), and the rim gathers a little extra light. A 1 px edge highlight is brightest on the
             edges that face the light, a fainter one on the far edges (light leaving the slab), a hairline of
             darkness just outside separates pale glass from a pale background. The pane casts a large soft
             shadow tinted with the colour of what it falls on, plus a tight contact shadow -- only outside the
             pane, like CSS box-shadow. A static frost grain sits on the glass. Panes stack: a front card blurs the
             cards behind it, text and all.
  interface  drawn with signed-distance shapes (1 px analytic anti-aliasing, so every pill, ring and knob is
             crisp): gradient toggles with a white knob and its drop shadow, sliders, a progress ring with a conic
             gradient, round caps, a soft coloured glow and an end knob, pill bars, sparklines with a fading area
             fill, round checkmarks, small glass chips and pills (glass on glass), squircle app icons, a glossy sun
             behind a glass cloud, etched dividers. Text: SF (Latin, variable weight and optical size) and PingFang
             (CJK) on macOS, split by script run; Noto / YaHei / core fonts elsewhere.
Colour stops (gradients) are mixed in OKLab. Angles for rings are degrees clockwise from 12 o'clock (UI
convention). Everything is drawn in screen pixels; `glass()` returns a Card (x0, y0, x1, y1, w, h, r) to measure
from.

    from aurora import Aurora, INK, WARM, COOL
    a = Aurora(1920, 1080, seed=3)
    a.backdrop(blobs=[(300, 200, 500, 380, '#ffc3a0'), (1600, 300, 520, 420, '#c9b5ff'),
                      (400, 900, 560, 380, '#9fd8ff')],
               ribbons=[([(-100, 800), (900, 520), (2000, 200)], 120, '#ffffff', 0.8)])
    a.orb(1200, 300, 120, ('#ffe0c8', '#ff9cc0', '#8d6bff'))
    c = a.glass(600, 240, 1300, 860, radius=40)            # a frosted card -> Card
    a.text('晨间计划', c.x0 + 48, c.y0 + 100, 52, weight='semibold')
    a.toggle(c.x1 - 128, c.y0 + 160, on=True)
    a.slider(c.x0 + 48, c.x1 - 48, c.y0 + 260, 0.4)
    a.ring(c.x0 + 200, c.y0 + 450, 110, 20, 0.6, COOL)
    a.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, spline, noise2d, smoothstep, shift, load_font

INK = '#1d2250'                                   # deep indigo: text and hairlines on the glass
WARM = ('#ffae6e', '#ff6f93', '#b06cff')          # sunrise: apricot -> pink -> violet
COOL = ('#56d0ff', '#6f8dff', '#9b6bff')          # calm: sky -> periwinkle -> violet
MINT = ('#5fe3b8', '#2fbf9b')
WHITE = '#ffffff'
LIGHT = (-0.42, -0.91)                            # screen direction toward the key light (upper left)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- colour: sRGB <-> OKLab
_M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
                [0.0883024619, 0.2817188376, 0.6299787005]], np.float32)
_M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
                [0.0259040371, 0.7827717662, -0.8086757660]], np.float32)
_M1i, _M2i = np.linalg.inv(_M1).astype(np.float32), np.linalg.inv(_M2).astype(np.float32)


def _lin(c):
    c = np.asarray(c, np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def to_lab(rgb):
    """sRGB (..., 3) in 0..1 -> OKLab"""
    return np.cbrt(_lin(rgb) @ _M1.T) @ _M2.T


def from_lab(lab):
    """OKLab (..., 3) -> sRGB in 0..1"""
    return _srgb((np.asarray(lab, np.float32) @ _M2i.T) ** 3 @ _M1i.T).astype(np.float32)


def ramp(t, stops):
    """colours along a gradient: t (any shape) in 0..1, stops = colours (hex or rgb) -> t.shape + (3,), OKLab mix"""
    L = np.stack([to_lab(_c(s)) for s in stops])
    t = np.clip(np.asarray(t, np.float32), 0, 1) * (len(stops) - 1)
    i = np.minimum(t.astype(int), len(stops) - 2)
    f = (t - i)[..., None]
    return from_lab(L[i] * (1 - f) + L[i + 1] * f)


def mix(a, b, t):
    """one colour between a and b (OKLab), t in 0..1"""
    return ramp(np.float32(t), (a, b))


# ---------------------------------------------------------------- signed distances (negative inside)
def sdf_rrect(u, v, hw, hh, r):
    qx, qy = np.abs(u) - (hw - r), np.abs(v) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sdf_segment(X, Y, a, b):
    ab = np.subtract(b, a, dtype=np.float32); l2 = float(ab @ ab) + 1e-9
    t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / l2, 0, 1)
    return np.hypot(X - (a[0] + t * ab[0]), Y - (a[1] + t * ab[1])), t


def smin(a, b, k):
    """smooth union of two distance fields (k px of fillet)"""
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _cov(d):
    return np.clip(0.5 - d, 0, 1)


def _bilinear(img, x, y):
    H, W = img.shape
    x = np.clip(x, 0, W - 1.001); y = np.clip(y, 0, H - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32)
    fx, fy = x - x0, y - y0
    a, b = img[y0, x0], img[y0, x0 + 1]
    c, d = img[y0 + 1, x0], img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


# ---------------------------------------------------------------- fonts: SF / PingFang on macOS, fallbacks elsewhere
_WEIGHT = {'light': 300, 'regular': 400, 'medium': 510, 'semibold': 600, 'bold': 700}
_CJK_FACES = [  # (glob, {weight: face index})
    ('/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/PingFang.ttc',
     {'light': 15, 'regular': 3, 'medium': 7, 'semibold': 11, 'bold': 11}),
    ('/System/Library/Fonts/Hiragino Sans GB.ttc', {'light': 0, 'regular': 0, 'medium': 2, 'semibold': 2, 'bold': 2}),
    ('/usr/share/fonts/**/NotoSansCJK*-{W}.tt[cf]', None),
    ('C:/Windows/Fonts/msyh{W}.ttc', None),
]
_FONTS = {}


def _find(pat):
    fs = glob.glob(pat, recursive=True)
    return fs[0] if fs else None


def _cjk_font(weight, size):
    env = os.environ.get('INKPAINT_FONT_CJK_SANS')
    if env and os.path.exists(env): return ImageFont.truetype(env, size)
    for pat, faces in _CJK_FACES:
        if faces is None:
            if 'Noto' in pat:
                w = {'light': 'Light', 'regular': 'Regular', 'medium': 'Medium', 'semibold': 'Bold', 'bold': 'Bold'}[weight]
            else:
                w = {'light': 'l', 'regular': '', 'medium': '', 'semibold': 'bd', 'bold': 'bd'}[weight]
            p = _find(pat.replace('{W}', w)) or _find(pat.replace('{W}', 'Regular' if 'Noto' in pat else ''))
            if p:
                try: return ImageFont.truetype(p, size)
                except OSError: pass
            continue
        p = _find(pat)
        if p:
            try: return ImageFont.truetype(p, size, index=faces[weight])
            except OSError: pass
    return load_font('cjk_sans', size)


def _latin_font(weight, size):
    env = os.environ.get('INKPAINT_FONT_SANS')
    if not (env and os.path.exists(env)) and os.path.exists('/System/Library/Fonts/SFNS.ttf'):
        try:
            f = ImageFont.truetype('/System/Library/Fonts/SFNS.ttf', size)
            f.set_variation_by_axes([100, float(np.clip(size * 0.62, 17, 96)), 400, _WEIGHT[weight]])
            return f
        except (OSError, ValueError):
            pass
    if os.path.exists('/System/Library/Fonts/HelveticaNeue.ttc') and not env:
        idx = {'light': 7, 'regular': 0, 'medium': 10, 'semibold': 10, 'bold': 1}[weight]
        return ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', size, index=idx)
    return load_font('sans_bold' if weight in ('semibold', 'bold') else 'sans', size)


def _font(kind, weight, size):
    key = (kind, weight, int(size))
    if key not in _FONTS:
        _FONTS[key] = (_cjk_font if kind == 'cjk' else _latin_font)(weight, int(size))
    return _FONTS[key]


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


class Card:
    """a pane of glass (or any rounded rectangle) in screen pixels"""

    def __init__(self, x0, y0, x1, y1, r):
        self.x0, self.y0, self.x1, self.y1, self.r = x0, y0, x1, y1, r
        self.w, self.h = x1 - x0, y1 - y0
        self.cx, self.cy = (x0 + x1) / 2, (y0 + y1) / 2


class Aurora:
    def __init__(self, W=1920, H=1080, seed=0, light=LIGHT):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        l = np.asarray(light, np.float32); self.L = l / np.linalg.norm(l)
        self.img = np.ones((H, W, 3), np.float32) * 0.96
        g = blur(self.rng.standard_normal((H, W)).astype(np.float32), 0.55)
        self.frost = (g / (g.std() + 1e-6)).astype(np.float32)          # static frost grain for every pane
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ low-level
    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _blend(self, sl, a, col):
        a = np.clip(a, 0, 1)[..., None]
        col = col if isinstance(col, np.ndarray) and col.ndim == 3 else _c(col)
        self.img[sl] = self.img[sl] * (1 - a) + col * a

    def _mul(self, sl, a, col):
        self.img[sl] *= 1 - np.clip(a, 0, 1)[..., None] * (1 - (col if isinstance(col, np.ndarray) else _c(col)))

    def _paint(self, sl, d, fill, alpha=1.0, grad=None, angle=90.0, box=None):
        """fill the shape with signed distance d (over slice sl): a colour, or `grad` stops along `angle`
        (degrees, 90 = top -> bottom, 0 = left -> right) across `box` (x0, y0, x1, y1)"""
        cov = _cov(d) * alpha
        if grad is not None:
            X, Y = self.XX[sl], self.YY[sl]
            bx0, by0, bx1, by1 = box
            a = np.deg2rad(angle); ux, uy = np.cos(a), np.sin(a)
            pc = np.array([[bx0, by0], [bx1, by0], [bx0, by1], [bx1, by1]], np.float32) @ [ux, uy]
            t = ((X * ux + Y * uy) - pc.min()) / (pc.max() - pc.min() + 1e-6)
            self._blend(sl, cov, ramp(t, grad))
        else:
            self._blend(sl, cov, fill)
        return cov

    def _drop(self, sl, cov, dx=0.0, dy=3.0, soft=4.0, strength=0.25, colour='#2a2466'):
        """soft drop shadow of coverage `cov` (cropped to sl), cast down and away from the light"""
        sh = blur(shift(cov, dx, dy), soft) * strength
        self._mul(sl, sh * (1 - cov), colour)

    # ------------------------------------------------------------ backdrop
    def backdrop(self, base='#f7f3fb', blobs=(), ribbons=(), warp=120.0, warp_scale=560.0, base_weight=0.32,
                 grain=0.022, seed=None):
        """the mesh gradient. blobs: [(x, y, rx, ry, colour[, strength])]; ribbons: [(pts, width, colour[, strength])].
        warp: how far (px) the pools wander; grain: film grain amplitude (0.015-0.03)"""
        s = self._seed() if seed is None else seed
        k = 4
        h, w = self.H // k + 1, self.W // k + 1
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32) * k
        if warp:
            X = X + (noise2d(h, w, warp_scale / k, 3, s) - 0.5) * 2 * warp
            Y = Y + (noise2d(h, w, warp_scale / k, 3, s + 1) - 0.5) * 2 * warp
        num = np.zeros((h, w, 3), np.float32) + to_lab(_c(base)) * base_weight
        den = np.full((h, w), base_weight, np.float32)
        for b in blobs:
            x, y, rx, ry, col = b[:5]
            st = b[5] if len(b) > 5 else 1.0
            wt = st * np.exp(-0.5 * (((X - x) / rx) ** 2 + ((Y - y) / ry) ** 2) * 2.2)
            num += wt[..., None] * to_lab(_c(col)); den += wt
        for rb in ribbons:
            pts, width, col = rb[:3]
            st = rb[3] if len(rb) > 3 else 1.0
            P = spline(pts, 24)
            dist = np.full((h, w), 1e9, np.float32)
            for i in range(len(P) - 1):
                dist = np.minimum(dist, sdf_segment(X, Y, P[i], P[i + 1])[0])
            wt = st * np.exp(-0.5 * (dist / width) ** 2 * 2.0)
            num += wt[..., None] * to_lab(_c(col)); den += wt
        rgb = from_lab(num / den[..., None])
        up = np.stack([np.asarray(Image.fromarray(rgb[..., c]).resize((w * k, h * k), Image.BICUBIC))[:self.H, :self.W]
                       for c in range(3)], -1)
        g = blur(self.rng.standard_normal((self.H, self.W)).astype(np.float32), 0.5)
        g /= g.std() + 1e-6
        ch = blur(self.rng.standard_normal((self.H, self.W, 1)).astype(np.float32)[..., 0], 0.8)
        ch = ch / (ch.std() + 1e-6)
        self.img = np.clip(up + grain * g[..., None] + grain * 0.35 * ch[..., None] * np.array([1, -0.4, -0.6], np.float32),
                           0, 1).astype(np.float32)

    def sparkles(self, n=40, box=None, size=(0.8, 2.4), alpha=(0.25, 0.7), seed=None):
        """tiny motes of light drifting in the aurora (soft white dots)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        x0, y0, x1, y1 = box or (0, 0, self.W, self.H)
        for _ in range(n):
            x, y = r.uniform(x0, x1), r.uniform(y0, y1)
            rad = r.uniform(*size); a = r.uniform(*alpha)
            sl = self._box(x - rad * 4, y - rad * 4, x + rad * 4, y + rad * 4)
            if sl is None: continue
            d = np.hypot(self.XX[sl] - x, self.YY[sl] - y)
            self._blend(sl, a * np.exp(-0.5 * (d / rad) ** 2), WHITE)

    # ------------------------------------------------------------ orbs
    def orb(self, cx, cy, r, stops=('#ffe2cc', '#ff9ec4', '#8d6bff'), spec=0.85, shadow=0.3, rim=0.55):
        """a glossy pastel sphere floating over the backdrop: stops run lit -> mid -> shade"""
        # contact shadow on the backdrop, cast down and to the right (away from the light)
        ox, oy = -self.L[0] * r * 0.28, -self.L[1] * r * 0.34
        sl = self._box(cx - r * 1.8 + ox, cy - r * 1.6 + oy, cx + r * 1.8 + ox, cy + r * 2.0 + oy)
        X, Y = self.XX[sl], self.YY[sl]
        dsh = np.hypot((X - cx - ox) / 0.95, (Y - cy - oy) / 0.9) - r
        env = self.img[sl].mean((0, 1))                                  # what the rim reflects
        shade_col = np.clip(env * 0.45 + hexc('#3b2d8a') * 0.3, 0, 1)
        self._mul(sl, blur(_cov(dsh), r * 0.32) * shadow, shade_col)
        sl = self._box(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2)
        X, Y = self.XX[sl], self.YY[sl]
        nx, ny = (X - cx) / r, (Y - cy) / r
        rr = nx * nx + ny * ny
        nz = np.sqrt(np.clip(1 - rr, 0, 1))
        Lv = np.array([self.L[0] * 0.62, self.L[1] * 0.62, 0.78], np.float32); Lv /= np.linalg.norm(Lv)
        ndl = nx * Lv[0] + ny * Lv[1] + nz * Lv[2]
        wrap = np.clip((ndl + 0.45) / 1.45, 0, 1)
        col = ramp(1 - wrap ** 0.9, stops)
        fres = (1 - nz) ** 2.6
        col = col + (np.clip(env * 1.05, 0, 1) - col) * (fres * rim)[..., None]          # rim picks up the backdrop
        Hv = Lv + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        ndh = np.clip(nx * Hv[0] + ny * Hv[1] + nz * Hv[2], 0, 1)
        sp = spec * (ndh ** 70 * 0.9 + ndh ** 9 * 0.16)
        col = col + (1 - col) * sp[..., None]
        d = (np.sqrt(rr) - 1) * r
        self._blend(sl, _cov(d), np.clip(col, 0, 1))

    # ------------------------------------------------------------ glass
    def _glass(self, sl, d, bbox, blur_px=26.0, tint=0.24, sat=1.5, shadow=0.26, elevation=26.0, bevel=14.0,
               rim=1.0, frost=0.012, sheen=0.5, tint_colour=WHITE, disperse=1.0, shade='#3a2f86'):
        X, Y = self.XX[sl], self.YY[sl]
        reg = self.img[sl]
        cov = _cov(d)
        B = np.stack([blur(reg[..., k], blur_px) for k in range(3)], -1) if blur_px > 0 else reg.copy()
        lum = (B @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
        B = np.clip(lum + (B - lum) * sat, 0, 1)
        # the bevelled rim bends the view outward, a little more for blue than red
        gy, gx = np.gradient(d)
        gn = np.hypot(gx, gy) + 1e-6; nx, ny = gx / gn, gy / gn
        t = np.clip(1 + d / bevel, 0, 1) * (d < 1)
        m = bevel * 1.1 * t ** 2
        lx, ly = X - sl[1].start, Y - sl[0].start
        G = np.empty_like(B)
        for k, f in enumerate((1 - 0.3 * disperse, 1.0, 1 + 0.3 * disperse)):
            G[..., k] = _bilinear(B[..., k], lx + nx * m * f, ly + ny * m * f)
        # milky veil, thicker toward the light; a broad sheen; light gathered in the bevel; frost grain
        bx0, by0, bx1, by1 = bbox
        u = np.clip(((X - bx0) / max(bx1 - bx0, 1) + (Y - by0) / max(by1 - by0, 1)) / 2, 0, 1)
        a = np.clip(tint * (1.3 - 0.6 * u), 0, 1)[..., None]
        G = G * (1 - a) + _c(tint_colour) * a
        G = G + (1 - G) * (sheen * 0.16 * smoothstep(0.62, 0.0, u) + 0.12 * rim * t ** 3)[..., None]
        G = G + frost * self.frost[sl][..., None]
        facing = nx * self.L[0] + ny * self.L[1]
        line = np.exp(-(((d + 1.1) / 0.85) ** 2))
        ra = rim * line * (0.28 + 0.62 * np.clip(facing, 0, 1) + 0.3 * np.clip(-facing, 0, 1))
        G = G * (1 - ra[..., None]) + ra[..., None]
        # shadow outside the pane (large, tinted by what it falls on) + tight contact shadow + outer hairline
        if shadow > 0:
            ox, oy = -self.L[0] * elevation * 0.35, elevation * 0.55
            S = blur(shift(cov, ox, oy), elevation * 0.95) * shadow + blur(shift(cov, ox * 0.2, elevation * 0.12),
                                                                            max(1.0, elevation * 0.18)) * shadow * 0.35
            sc = np.clip(B * 0.5 + _c(shade) * 0.35, 0, 1)
            reg = reg * (1 - (S * (1 - cov))[..., None] * (1 - sc))
        hl = np.exp(-(((d - 0.9) / 0.7) ** 2)) * 0.075 * rim
        reg = reg * (1 - hl[..., None] * (1 - hexc(INK)))
        c3 = cov[..., None]
        self.img[sl] = np.clip(reg * (1 - c3) + G * c3, 0, 1)

    def glass(self, x0, y0, x1, y1, radius=36, blur=26.0, tint=0.24, sat=1.5, shadow=0.26, elevation=26.0,
              bevel=14.0, rim=1.0, frost=0.012, sheen=0.5, tint_colour=WHITE, disperse=1.0):
        """a frosted glass card; everything already on the canvas under it is blurred through it -> Card"""
        pad = int(max(3 * blur, 3.2 * elevation) + bevel + 8)
        sl = self._box(x0 - pad, y0 - pad, x1 + pad, y1 + pad)
        X, Y = self.XX[sl], self.YY[sl]
        d = sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, radius)
        self._glass(sl, d, (x0, y0, x1, y1), blur, tint, sat, shadow, elevation, min(bevel, radius), rim, frost,
                    sheen, tint_colour, disperse)
        return Card(x0, y0, x1, y1, radius)

    def pill(self, x0, y0, x1, y1, blur=8.0, tint=0.42, shadow=0.1, elevation=8.0, rim=0.9, **kw):
        """a small glass pill / chip (glass on glass): a fully rounded glass() with a light touch"""
        return self.glass(x0, y0, x1, y1, radius=(y1 - y0) / 2, blur=blur, tint=tint, shadow=shadow,
                          elevation=elevation, bevel=min(8, (y1 - y0) / 3), rim=rim, **kw)

    # ------------------------------------------------------------ shapes
    def rrect(self, x0, y0, x1, y1, r, fill=WHITE, alpha=1.0, grad=None, angle=0.0, shadow=0.0):
        sl = self._box(x0 - 20, y0 - 20, x1 + 20, y1 + 24)
        X, Y = self.XX[sl], self.YY[sl]
        d = sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
        if shadow: self._drop(sl, _cov(d), 0, 3, 5, shadow)
        return self._paint(sl, d, fill, alpha, grad, angle, (x0, y0, x1, y1))

    def circle(self, cx, cy, r, fill=WHITE, alpha=1.0, grad=None, angle=90.0, shadow=0.0, ring=0.0):
        """a disc (or, with ring=w, a circular stroke w px wide)"""
        sl = self._box(cx - r - 16, cy - r - 16, cx + r + 16, cy + r + 20)
        X, Y = self.XX[sl], self.YY[sl]
        d = np.hypot(X - cx, Y - cy) - r
        if ring: d = np.abs(d + ring / 2) - ring / 2
        if shadow: self._drop(sl, _cov(d), 0, max(2, r * 0.12), max(2, r * 0.22), shadow)
        return self._paint(sl, d, fill, alpha, grad, angle, (cx - r, cy - r, cx + r, cy + r))

    def line(self, pts, width=3.0, fill=INK, alpha=1.0, grad=None, angle=0.0, smooth=False):
        """polyline with round caps and joins (spline-smoothed if smooth=True)"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 12)
        pad = width + 4
        sl = self._box(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        X, Y = self.XX[sl], self.YY[sl]
        dist = np.full(X.shape, 1e9, np.float32)
        for i in range(len(P) - 1):
            dist = np.minimum(dist, sdf_segment(X, Y, P[i], P[i + 1])[0])
        return self._paint(sl, dist - width / 2, fill, alpha, grad, angle,
                           (P[:, 0].min(), P[:, 1].min(), P[:, 0].max(), P[:, 1].max()))

    def divider(self, x0, x1, y, alpha=1.0):
        """an etched hairline: a faint dark line with a light line under it"""
        self.rrect(x0, y - 0.6, x1, y + 0.6, 0.6, INK, 0.08 * alpha)
        self.rrect(x0, y + 0.8, x1, y + 2.0, 0.6, WHITE, 0.55 * alpha)

    # ------------------------------------------------------------ text
    def _runs(self, s):
        runs = []
        for ch in s:
            k = _is_cjk(ch)
            if runs and runs[-1][1] == k: runs[-1][0] += ch
            else: runs.append([ch, k])
        return runs

    def _glyphs(self, s, size, weight, spacing):
        """-> [(font, piece, x offset)], total advance"""
        out, x = [], 0.0
        for piece, k in self._runs(s):
            f = _font('cjk' if k else 'latin', weight, size)
            if spacing:
                for ch in piece:
                    out.append((f, ch, x)); x += f.getlength(ch) + spacing
            else:
                out.append((f, piece, x)); x += f.getlength(piece)
        return out, (x - spacing if spacing else x)

    def text_width(self, s, size, weight='regular', spacing=0.0):
        return self._glyphs(s, size, weight, spacing)[1]

    def text(self, s, x, y, size, fill=INK, weight='regular', anchor='ls', alpha=1.0, spacing=0.0, grad=None,
             angle=0.0):
        """text in SF / PingFang (script runs split automatically). anchor: [l m r] + [s baseline, m middle,
        t cap top, b bottom]; spacing: extra px between letters; grad: gradient stops across the text -> advance"""
        size = int(round(size))
        gl, tw = self._glyphs(s, size, weight, spacing)
        x0 = x - tw * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        base = y + {'s': 0.0, 'm': 0.36 * size, 't': 0.74 * size, 'b': -0.24 * size}[anchor[1]]
        bx0, by0 = int(np.floor(x0)) - 4, int(np.floor(base - size * 1.2))
        bw, bh = int(tw) + 10, int(size * 1.6) + 6
        im = Image.new('L', (bw, bh), 0)
        dr = ImageDraw.Draw(im)
        for f, piece, off in gl:
            dr.text((x0 - bx0 + off, base - by0), piece, font=f, fill=255, anchor='ls')
        m = np.asarray(im, np.float32) / 255
        sl = self._box(bx0, by0, bx0 + bw, by0 + bh)
        if sl is None: return tw
        m = m[sl[0].start - by0:sl[0].stop - by0, sl[1].start - bx0:sl[1].stop - bx0]
        if grad is not None:
            X, Y = self.XX[sl], self.YY[sl]
            a = np.deg2rad(angle)
            t = ((X - x0) * np.cos(a) + (Y - (base - size * 0.74)) * np.sin(a)) / max(tw * abs(np.cos(a)) + size * 0.74 * abs(np.sin(a)), 1)
            self._blend(sl, m * alpha, ramp(t, grad))
        else:
            self._blend(sl, m * alpha, fill)
        return tw

    # ------------------------------------------------------------ controls
    def toggle(self, x, y, on=True, w=80, h=46, grad=COOL):
        """an iOS-style switch, top-left at (x, y): gradient track when on, recessed glass when off, white knob"""
        r = h / 2
        sl = self._box(x - 10, y - 10, x + w + 10, y + h + 14)
        X, Y = self.XX[sl], self.YY[sl]
        d = sdf_rrect(X - (x + w / 2), Y - (y + h / 2), w / 2, h / 2, r)
        if on:
            self._paint(sl, d, None, 1.0, grad, 0, (x, y, x + w, y + h))
            inner = np.clip(-d / 3, 0, 1) * np.exp(-np.clip(Y - y, 0, None) / 5) * _cov(d)
            self._mul(sl, inner * 0.18, INK)                             # the track is a groove: top edge in shade
            self._blend(sl, _cov(d) * np.exp(-((Y - (y + h - 3)) / 3) ** 2) * 0.25, WHITE)
        else:
            self._paint(sl, d, WHITE, 0.4)
            self._mul(sl, _cov(d) * 0.08, INK)
            inner = _cov(d) * np.exp(-np.clip(Y - y, 0, None) / 6) * np.clip(-d / 2, 0, 1)
            self._mul(sl, inner * 0.14, INK)
            self._blend(sl, np.exp(-(((d + 0.6) / 0.7) ** 2)) * 0.12, INK)
        kx = x + w - r if on else x + r
        self.knob(kx, y + h / 2, r - 4)

    def knob(self, cx, cy, r, shadow=0.3):
        """a white knob with a soft drop shadow and a faint top-lit gradient"""
        self.circle(cx, cy, r, grad=('#ffffff', '#f1f1f8'), angle=90, shadow=shadow)
        self.circle(cx, cy, r, INK, 0.06, ring=1.0)

    def slider(self, x0, x1, y, value, grad=COOL, h=8, knob=13, glow=0.25):
        """a slider track centred on y with a gradient fill up to `value` and a white knob"""
        xv = x0 + (x1 - x0) * float(np.clip(value, 0, 1))
        self.rrect(x0, y - h / 2, x1, y + h / 2, h / 2, WHITE, 0.5)
        self.rrect(x0, y - h / 2, x1, y + h / 2, h / 2, INK, 0.06)
        if glow:
            sl = self._box(x0 - 30, y - 30, xv + 30, y + 34)
            X, Y = self.XX[sl], self.YY[sl]
            d = sdf_rrect(X - (x0 + xv) / 2, Y - y, (xv - x0) / 2 + h / 2, h / 2, h / 2)
            g = blur(_cov(d), 7) * glow
            self._blend(sl, g, ramp(np.clip((X - x0) / max(xv - x0, 1), 0, 1), grad))
        self.rrect(x0, y - h / 2, xv + h / 2, y + h / 2, h / 2, grad=grad, angle=0)
        self.knob(xv, y, knob)

    def ring(self, cx, cy, r, width, frac, grad=COOL, track=0.55, glow=0.35, knob=True):
        """a progress ring: faint track, conic gradient arc from 12 o'clock clockwise with round caps, a soft
        coloured glow and a white knob at the end"""
        a1 = 360.0 * float(np.clip(frac, 0.002, 0.999))
        pad = width + 40
        sl = self._box(cx - r - pad, cy - r - pad, cx + r + pad, cy + r + pad)
        X, Y = self.XX[sl], self.YY[sl]
        dx, dy = X - cx, Y - cy
        rho = np.hypot(dx, dy)
        th = np.degrees(np.arctan2(dx, -dy)) % 360
        band = np.abs(rho - r) - width / 2
        if track:
            self._paint(sl, band, WHITE, track)
            self._mul(sl, _cov(band) * 0.035, INK)
        e = np.radians(a1)
        c0 = (cx, cy - r); c1 = (cx + r * np.sin(e), cy - r * np.cos(e))
        dcap = np.minimum(np.hypot(X - c0[0], Y - c0[1]), np.hypot(X - c1[0], Y - c1[1])) - width / 2
        d = np.where(th <= a1, band, 1e9)
        d = np.minimum(d, dcap)
        t = np.where(th <= a1, th / a1, np.where(360 - th < th - a1, 0.0, 1.0))
        col = ramp(t, grad)
        if glow:
            g = blur(_cov(d), width * 0.7) * glow
            self._blend(sl, g * (1 - _cov(d)), col)
        self._blend(sl, _cov(d), col)
        hi = _cov(d) * np.exp(-(((rho - (r - width * 0.18)) / (width * 0.22)) ** 2)) * 0.18   # a faint tube highlight
        self._blend(sl, hi, WHITE)
        if knob:
            self.knob(c1[0], c1[1], width * 0.34, shadow=0.25)

    def check(self, cx, cy, r, state='done', grad=WARM, frac=0.5):
        """a round checkmark: done (gradient disc + white tick), now (ring with a small progress arc), todo (ring)"""
        if state == 'done':
            self.circle(cx, cy, r, grad=grad, angle=45, shadow=0.18)
            self.line([(cx - r * 0.42, cy + r * 0.02), (cx - r * 0.1, cy + r * 0.34), (cx + r * 0.45, cy - r * 0.3)],
                      r * 0.2, WHITE)
        elif state == 'now':
            self.circle(cx, cy, r, WHITE, 0.75, shadow=0.12)
            self.ring(cx, cy, r * 0.6, r * 0.26, frac, grad, track=0.0, glow=0.0, knob=False)
        else:
            self.circle(cx, cy, r, WHITE, 0.35)
            self.circle(cx, cy, r, INK, 0.28, ring=2.0)

    def bars(self, x0, y0, x1, y1, values, vmax=None, labels=(), highlight=None, grad=COOL, label_size=19,
             bar=0.5, slots=0.1, fade=()):
        """a pill bar chart in the box (labels sit below y1). highlight: index drawn with the gradient;
        slots: alpha of the empty full-height slot behind each bar; fade: indices left as empty slots"""
        n = len(values); vmax = vmax or max(values)
        step = (x1 - x0) / n; bw = step * bar
        for i, v in enumerate(values):
            cx = x0 + step * (i + 0.5)
            top = y1 - max(bw, (y1 - y0) * v / vmax)
            if slots: self.rrect(cx - bw / 2, y0, cx + bw / 2, y1, bw / 2, WHITE, slots)   # the empty slot
            if i == highlight:
                self.rrect(cx - bw / 2, top, cx + bw / 2, y1, bw / 2, grad=grad, angle=-90, shadow=0.12)
            elif i in fade:
                pass
            else:
                self.rrect(cx - bw / 2, top, cx + bw / 2, y1, bw / 2, WHITE, 0.78, shadow=0.06)
            if i < len(labels):
                self.text(labels[i], cx, y1 + label_size * 1.6, label_size, INK, 'semibold' if i == highlight else 'regular',
                          'ms', alpha=0.85 if i == highlight else 0.5)

    def spark(self, x0, y0, x1, y1, values, grad=WARM, width=3.0, fill=0.32, dots=(), vmin=None, vmax=None):
        """a smooth sparkline across the box with a gradient line and an area fill fading downward -> points"""
        v = np.asarray(values, np.float32)
        lo = v.min() if vmin is None else vmin; hi = v.max() if vmax is None else vmax
        xs = np.linspace(x0, x1, len(v)); ys = y1 - (v - lo) / max(hi - lo, 1e-6) * (y1 - y0)
        P = spline(np.stack([xs, ys], 1), 16)
        if fill:
            sl = self._box(x0, y0 - 4, x1 + 1, y1 + 30)
            X, Y = self.XX[sl], self.YY[sl]
            top = np.interp(X[0], P[:, 0], P[:, 1])[None, :]
            a = np.clip(Y - top + 0.5, 0, 1) * np.clip(1 - (Y - top) / (y1 + 26 - top + 1e-3), 0, 1) ** 1.6 * fill
            a *= smoothstep(x0 - 1, x0 + 22, X) * smoothstep(x1 + 1, x1 - 22, X)          # fade out at both ends
            self._blend(sl, a, ramp((X - x0) / max(x1 - x0, 1), grad))
        self.line(P, width, grad=grad, angle=0)
        pts = list(zip(xs, ys))
        for i in dots:
            self.circle(pts[i][0], pts[i][1], width * 2.2, WHITE, shadow=0.2)
            self.circle(pts[i][0], pts[i][1], width * 1.2, grad=grad)
        return pts

    # ------------------------------------------------------------ icons
    def sun(self, cx, cy, r, stops=('#fff3b8', '#ffc85a', '#ff8a3d'), glow=0.5):
        """a glossy sun: warm halo, shaded orb, specular spot"""
        sl = self._box(cx - r * 3, cy - r * 3, cx + r * 3, cy + r * 3)
        d = np.hypot(self.XX[sl] - cx, self.YY[sl] - cy)
        self._blend(sl, glow * np.exp(-0.5 * (d / (r * 1.25)) ** 2), hexc('#ffd27a'))
        self.orb(cx, cy, r, stops, spec=0.6, shadow=0.0, rim=0.2)

    def cloud(self, cx, cy, w, blur=7.0, tint=0.5, shadow=0.16):
        """a frosted glass cloud (the sun behind it shows through, blurred)"""
        pad = int(w * 0.6 + 3 * blur + 20)
        sl = self._box(cx - pad, cy - pad, cx + pad, cy + pad)
        X, Y = self.XX[sl], self.YY[sl]
        base = sdf_segment(X, Y, (cx - 0.3 * w, cy + 0.12 * w), (cx + 0.3 * w, cy + 0.12 * w))[0] - 0.17 * w
        c1 = np.hypot(X - (cx - 0.1 * w), Y - (cy - 0.04 * w)) - 0.24 * w
        c2 = np.hypot(X - (cx + 0.17 * w), Y - (cy + 0.03 * w)) - 0.17 * w
        d = smin(smin(base, c1, 0.06 * w), c2, 0.06 * w)
        self._glass(sl, d, (cx - 0.47 * w, cy - 0.28 * w, cx + 0.47 * w, cy + 0.29 * w), blur, tint, 1.2, shadow,
                    w * 0.12, w * 0.07, 1.0, 0.01, 0.6, WHITE, 0.6)

    def app_icon(self, x, y, size, grad=WARM, glyph='', glyph_size=None, weight='semibold'):
        """a squircle app icon at (x, y) top-left: gradient, top gloss, drop shadow, white glyph"""
        sl = self._box(x - 12, y - 12, x + size + 12, y + size + 16)
        X, Y = self.XX[sl], self.YY[sl]
        u, v = (X - (x + size / 2)) / (size / 2), (Y - (y + size / 2)) / (size / 2)
        f = (np.abs(u) ** 5 + np.abs(v) ** 5) ** 0.2                        # superellipse
        d = (f - 1) * size / 2 / np.maximum(1, 0.8 + 0.2 * f)
        self._drop(sl, _cov(d), 0, size * 0.06, size * 0.1, 0.25)
        self._paint(sl, d, None, 1.0, grad, 60, (x, y, x + size, y + size))
        gl = _cov(d) * smoothstep(0.2, -0.9, v) * 0.22
        self._blend(sl, gl, WHITE)
        self._blend(sl, np.exp(-(((d + 0.9) / 0.7) ** 2)) * 0.35, WHITE)
        if glyph:
            self.text(glyph, x + size / 2, y + size / 2, glyph_size or size * 0.5, WHITE, weight, 'mm')

    # ------------------------------------------------------------ output
    def composite(self):
        return Image.fromarray((np.clip(self.img, 0, 1) * 255 + 0.5).astype(np.uint8))

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
