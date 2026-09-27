"""core — shared helpers for every style (numpy + Pillow only)."""
import glob
import os
import numpy as np
from PIL import Image


def blur(a, sigma):
    """fast gaussian approximation: 3 separable box blurs via cumulative sums (numpy only)"""
    if sigma <= 0: return a.copy()
    out = a.astype(np.float32)
    w = int(np.sqrt(12 * sigma * sigma / 3 + 1))
    w += (w % 2 == 0)
    r = w // 2
    for _ in range(3):
        for ax in (0, 1):
            pad = [(0, 0), (0, 0)]; pad[ax] = (r + 1, r)
            c = np.cumsum(np.pad(out, pad, mode='edge'), axis=ax, dtype=np.float64)
            hi = np.take(c, np.arange(w, c.shape[ax]), axis=ax)
            lo = np.take(c, np.arange(0, c.shape[ax] - w), axis=ax)
            out = ((hi - lo) / w).astype(np.float32)
    return out


def fbm1d(n, scale, octaves=5, seed=0):
    """1D fractal noise in [-1, 1] (ridgelines, wobble)"""
    r = np.random.default_rng(seed)
    x = np.arange(n, dtype=np.float32)
    out = np.zeros(n, np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        k = max(2, int(n / scale * 2 ** o) + 2)
        out += amp * np.interp(x, np.linspace(0, n - 1, k), r.random(k).astype(np.float32) * 2 - 1)
        tot += amp; amp *= 0.5
    return out / tot


def curve(p0, p1, bend, n=24, wig=0.0, seed=0):
    """curve from p0 to p1 bowing sideways by `bend` px, optional wiggle"""
    p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
    t = np.linspace(0, 1, n)[:, None]
    d = p1 - p0; nrm = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
    off = (4 * t * (1 - t)) * bend
    if wig: off = off + fbm1d(n, 6, 2, seed)[:, None] * wig
    return p0 + d * t + nrm * off


def spline(pts, per=14):
    """Catmull-Rom through control points — always use this instead of straight zig-zags"""
    P = np.asarray(pts, np.float32)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out, np.float32)



def noise2d(h, w, scale, octaves=4, seed=0):
    """2D value noise in [0, 1] (bicubic-upsampled random grids, fractal sum)"""
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp = 1.0; tot = 0.0
    for o in range(octaves):
        gh, gw = max(2, int(h / scale * 2 ** o) + 2), max(2, int(w / scale * 2 ** o) + 2)
        g = Image.fromarray(r.random((gh, gw)).astype(np.float32))
        out += amp * np.asarray(g.resize((w, h), Image.BICUBIC), np.float32)
        tot += amp; amp *= 0.5
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def polygon_mask(h, w, pts, ss=1):
    """filled polygon -> float mask (optionally supersampled for smooth edges)"""
    from PIL import ImageDraw
    im = Image.new('L', (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in pts], fill=255)
    if ss > 1: im = im.resize((w, h), Image.BILINEAR)
    return np.asarray(im, np.float32) / 255


def blob_pts(cx, cy, rx, ry, rough=0.08, n=90, seed=0, rot=0.0):
    """closed organic outline around (cx, cy): ellipse with fractal radius wobble"""
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    wob = 1 + rough * fbm1d(n, n / 6, 4, seed)
    x, y = np.cos(t) * rx * wob, np.sin(t) * ry * wob
    c, s = np.cos(rot), np.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)


def cjk_font():
    """a brush-like CJK font: $INKPAINT_FONT, else Kaiti/Songti (macOS), Noto CJK (Linux), KaiTi/SimSun (Windows)"""
    env = os.environ.get('INKPAINT_FONT')
    if env and os.path.exists(env): return env
    pats = ['/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData/Kaiti.ttc',
            '/System/Library/Fonts/Supplemental/Songti.ttc', '/System/Library/Fonts/STHeiti Medium.ttc',
            '/usr/share/fonts/**/NotoSerifCJK*.tt[cf]', '/usr/share/fonts/**/NotoSansCJK*.tt[cf]',
            'C:/Windows/Fonts/simkai.ttf', 'C:/Windows/Fonts/simsun.ttc']
    for pat in pats:
        fs = glob.glob(pat, recursive=True)
        if fs: return fs[0]
    return None


def bristle_stroke(buf, pts, width, ink, dry=0.35, taper=(0.25, 0.35), jitter=0.6, seed=0):
    """bristle brush along polyline `pts` into density buffer `buf` (in place).
    width px; ink = peak opacity 0..1; dry = flying-white (0 wet .. 0.8 very dry); taper = (start, end)."""
    H, W = buf.shape
    r = np.random.default_rng(seed)
    pts = np.asarray(pts, np.float32)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    L = float(seg.sum())
    if L < 2: return
    s = np.concatenate([[0], np.cumsum(seg)])
    nb = max(3, int(width * 1.3))
    br = max(0.6, width / nb * 1.7)                      # bristles overlap -> no stripes
    step = max(0.5, min(width * 0.22, br * 0.7))         # dab spacing relative to bristle -> no beads
    n = int(L / step) + 2
    ss = np.linspace(0, L, n)
    px = np.interp(ss, s, pts[:, 0]); py = np.interp(ss, s, pts[:, 1])
    tx = np.gradient(px); ty = np.gradient(py)
    tl = np.hypot(tx, ty) + 1e-6; tx /= tl; ty /= tl
    nx, ny = -ty, tx
    t = ss / L
    press = 0.35 + 0.65 * np.clip(np.minimum(t / max(taper[0], 1e-3), (1 - t) / max(taper[1], 1e-3)), 0, 1) ** 0.6
    offs = np.linspace(-0.5, 0.5, nb) + r.normal(0, 0.04, nb)
    load0 = r.uniform(0.75, 1.0, nb)
    wob = fbm1d(n, 40, 3, int(r.integers(1 << 30))) * jitter * width * 0.5
    rad = int(br * 2 + 2)
    ky, kx = np.mgrid[-rad:rad + 1, -rad:rad + 1].astype(np.float32)
    for b in range(nb):
        load = load0[b] * (1 - dry * t ** 1.2 * r.uniform(0.6, 1.4))
        gate = fbm1d(n, 25, 3, int(r.integers(1 << 30)))
        alive = (load * (0.75 + 0.5 * gate)) > (dry * 0.9)
        for i in range(n):
            if not alive[i]: continue
            w = width * press[i]
            cx = px[i] + nx[i] * (offs[b] * w + wob[i]); cy = py[i] + ny[i] * (offs[b] * w + wob[i])
            ix, iy = int(cx), int(cy)
            if ix < rad or iy < rad or ix >= W - rad - 1 or iy >= H - rad - 1: continue
            k = np.exp(-((kx - (cx - ix)) ** 2 + (ky - (cy - iy)) ** 2) / (2 * (br * press[i]) ** 2 + 1e-3))
            sl = buf[iy - rad:iy + rad + 1, ix - rad:ix + rad + 1]
            np.copyto(sl, 1 - (1 - sl) * (1 - k * ink * load[i] * 0.55))


# ---------------------------------------------------------------- helpers shared by clay / cyanotype / stitch / panel
def shift(a, dx, dy):
    """zero-padded shift, no wrap-around: out[y, x] = a[y - dy, x - dx]"""
    dx, dy = int(round(dx)), int(round(dy))
    H, W = a.shape[:2]
    out = np.zeros_like(a)
    if abs(dx) >= W or abs(dy) >= H: return out
    out[max(dy, 0):H + min(dy, 0), max(dx, 0):W + min(dx, 0)] = a[max(-dy, 0):H + min(-dy, 0), max(-dx, 0):W + min(-dx, 0)]
    return out


_FONT_CANDIDATES = {   # (glob pattern, face index); first hit wins -- macOS, Linux, Windows
    'sans': [('/System/Library/Fonts/HelveticaNeue.ttc', 0), ('/System/Library/Fonts/Helvetica.ttc', 0),
             ('/usr/share/fonts/**/DejaVuSans.ttf', 0), ('/usr/share/fonts/**/LiberationSans-Regular.ttf', 0), ('C:/Windows/Fonts/arial.ttf', 0)],
    'sans_bold': [('/System/Library/Fonts/HelveticaNeue.ttc', 1), ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 0),
                  ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('/usr/share/fonts/**/LiberationSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'rounded': [('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf', 0), ('/usr/share/fonts/**/Nunito*Black*.ttf', 0),
                ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/ARLRDBD.TTF', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'geometric': [('/System/Library/Fonts/Supplemental/Futura.ttc', 0), ('/System/Library/Fonts/Avenir Next.ttc', 5),
                  ('/usr/share/fonts/**/URWGothic-Book.*', 0), ('/usr/share/fonts/**/DejaVuSans.ttf', 0), ('C:/Windows/Fonts/GOTHIC.TTF', 0), ('C:/Windows/Fonts/arial.ttf', 0)],
    'condensed': [('/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf', 0), ('/System/Library/Fonts/HelveticaNeue.ttc', 4),
                  ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', 0), ('C:/Windows/Fonts/ARIALNB.TTF', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)],
    'serif': [('/System/Library/Fonts/Supplemental/Georgia.ttf', 0), ('/System/Library/Fonts/Times.ttc', 0),
              ('/usr/share/fonts/**/DejaVuSerif.ttf', 0), ('C:/Windows/Fonts/georgia.ttf', 0)],
    'typewriter': [('/System/Library/Fonts/Supplemental/AmericanTypewriter.ttc', 0), ('/System/Library/Fonts/Supplemental/Courier New.ttf', 0),
                   ('/usr/share/fonts/**/DejaVuSansMono.ttf', 0), ('C:/Windows/Fonts/cour.ttf', 0)],
    'hand': [('/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf', 0), ('/System/Library/Fonts/Noteworthy.ttc', 0),
             ('/usr/share/fonts/**/*Kalam*Regular*.ttf', 0), ('/usr/share/fonts/**/*Caveat*.ttf', 0), ('C:/Windows/Fonts/segoepr.ttf', 0), ('C:/Windows/Fonts/comic.ttf', 0)],
    'script': [('/System/Library/Fonts/Supplemental/SnellRoundhand.ttc', 1), ('/System/Library/Fonts/Supplemental/Apple Chancery.ttf', 0),
               ('/usr/share/fonts/**/z003*.[ot]tf', 0), ('C:/Windows/Fonts/segoesc.ttf', 0), ('C:/Windows/Fonts/Gabriola.ttf', 0)],
    'cjk_sans': [('/System/Library/Fonts/STHeiti Medium.ttc', 0), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 2),
                 ('/usr/share/fonts/**/NotoSansCJK*Bold*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSansCJK*.tt[cf]', 0), ('C:/Windows/Fonts/msyhbd.ttc', 0), ('C:/Windows/Fonts/msyh.ttc', 0)],
}


def latin_font(style='sans'):
    """(path, face_index) of a system font for `style`, or None.
    styles: sans, sans_bold, rounded, geometric, condensed, serif, typewriter, hand, script, cjk_sans, cjk.
    Override any style with $INKPAINT_FONT_<STYLE>, e.g. INKPAINT_FONT_HAND=/path/to/font.ttf"""
    env = os.environ.get('INKPAINT_FONT_' + style.upper())
    if env and os.path.exists(env): return env, 0
    if style == 'cjk':
        p = cjk_font()
        return (p, 0) if p else None
    for pat, idx in _FONT_CANDIDATES.get(style, []):
        fs = glob.glob(pat, recursive=True)
        if fs: return fs[0], idx
    return None


def load_font(style, size):
    """PIL font for `style` at `size` px; falls back to the sans font, then the CJK font, then Pillow's default"""
    from PIL import ImageFont
    for st in (style, 'sans', 'cjk'):
        hit = latin_font(st)
        if hit:
            try:
                return ImageFont.truetype(hit[0], int(size), index=hit[1])
            except OSError:
                pass
    return ImageFont.load_default(size)


def text_mask(h, w, s, font, xy, anchor='la', spacing=0.0, rot=0.0):
    """text -> anti-aliased float mask (h, w) in 0..1.
    font: a PIL font (see load_font); anchor as in Pillow ('la', 'mm', 'rs', ...);
    spacing: extra px between letters (letter-spaced legends); rot: degrees counter-clockwise about xy"""
    from PIL import ImageDraw
    im = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(im)
    x, y = float(xy[0]), float(xy[1])
    if not spacing:
        d.text((x, y), s, font=font, fill=255, anchor=anchor)
    else:
        adv = [font.getlength(ch) + spacing for ch in s]
        total = sum(adv) - spacing
        x0 = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        for ch, a in zip(s, adv):
            d.text((x0, y), ch, font=font, fill=255, anchor='l' + anchor[1])
            x0 += a
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, center=(x, y))
    return np.asarray(im, np.float32) / 255


def height_normals(hmap):
    """unit surface normals (H, W, 3) of a height field measured in pixels"""
    gy, gx = np.gradient(hmap.astype(np.float32))
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def height_shadow(hmap, light=(-0.45, -0.62, 0.64), reach=160, step=2.0, soft=3.0):
    """cast shadow of a height field onto itself: 0 lit .. 1 in shadow.
    March from every pixel toward the light; if the terrain rises above the light ray, the pixel is shadowed."""
    lx, ly, lz = light
    l = float(np.hypot(lx, ly)) + 1e-6
    dx, dy, slope = lx / l, ly / l, lz / l                 # slope: how fast the ray climbs per px
    occ = np.full(hmap.shape, -1e9, np.float32)
    t = step
    while t <= reach:
        s = shift(hmap, -dx * t, -dy * t) - t * slope
        np.maximum(occ, s, out=occ)
        t += step
    return smoothstep(0.0, soft, occ - hmap)


def ambient_occlusion(hmap, radii=(4, 12, 32), depth=(6.0, 14.0, 30.0)):
    """crevices and the feet of raised shapes get less sky light: 0 open .. 1 occluded"""
    ao = np.zeros(hmap.shape, np.float32)
    for r, k in zip(radii, depth):
        ao += np.clip((blur(hmap, r) - hmap) / k, 0, 1)
    return np.clip(ao / len(radii), 0, 1)
