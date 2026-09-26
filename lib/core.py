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
