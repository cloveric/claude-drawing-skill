"""stainedglass — a Gothic stained-glass window seen from inside a stone church, lit by daylight from behind
(numpy + Pillow only).

How a real window is made, and how this module copies it step by step:
  cartoon  the glazier draws the design full size and divides it into pieces. A piece is one colour of glass,
           and glass cannot be cut into thin strips or deep inward curves, so big areas (sky, ground, a crown of
           leaves) are split into many irregular pieces. `glass(mask, colour, cell=...)` registers one area of
           colour; with `cell` it is cut into a jittered Voronoi mosaic (optionally in polar coordinates around a
           point, so the pieces radiate from a sun). Later areas are cut out of earlier ones, so work back to
           front like a painter. Slivers too small to cut are merged into a neighbour of the same colour.
           `cut(pts)` adds an extra cut line (a lead) through a piece, e.g. to split a trunk.
  glass    pot-metal glass is coloured all the way through, and every piece comes from a different part of a
           hand-blown sheet: its own shade, its own thickness (thicker = darker and more saturated, because the
           transmission is colour ** thickness), parallel reams / streaks running one way per piece, and seeds
           (small air bubbles drawn out along the streaks). Flashed ruby carries its colour in a thin layer on
           clear glass, so it streaks strongly from pink to deep red.
  paint    grisaille is a brown-black vitreous paint fired onto the glass. Paint is never coloured: all the colour
           is in the glass. `trace()` lays opaque brush lines (features, veins, feathers, twigs too thin to cut);
           `matt()` / `shade()` lay a semi-opaque stippled wash that models volume; `scratch()` lifts paint off
           again with a stick so highlights and patterns shine through; `diaper()` is a background pattern
           scratched out of (or painted on) a light matt; `stain()` is silver stain, which turns white glass lemon
           to amber and blue glass green; `inscribe()` paints or scratches lettering.
  lead     H-section lead came runs along every boundary between pieces, so the lead falls exactly on the Voronoi
           bisectors and on the colour edges; a wider came frames the rim of each light; the joints are soldered
           (slightly wider, lighter tin blobs). `crack()` adds a broken piece mended with a thin strap lead.
  iron     `saddle_bar()` crosses a light on the inside, tied to the leads with copper wire.
  stone    `wall()` is coursed ashlar; `lancet()` cuts a pointed-arch opening with a splayed reveal (radial
           voussoir joints round the arch), a sloping sill and an optional hood mould; `string_course()` is a
           moulded band below the sills.
  light    seen from inside, the glass is the light source. `daylight()` turns on the room: the wall stays dim
           and takes a wash of coloured spill light, the reveals glow near the glass, the sloping sill catches a
           soft upside-down projection of the lowest glass, and bright glass halates over the dark leads (blue
           spreads most). `weather()` adds grime along the leads and corrosion pits on some pieces.

    from stainedglass import StainedGlass
    g = StainedGlass(1920, 1080, seed=1)
    g.wall()
    L = g.lancet(960, 80, 940, 360)                       # a pointed-arch light; L.pt(lx, ly) = local -> image
    g.glass(L.inner(0), '#1f4fa8', cell=46)               # blue sky cut into a Voronoi mosaic
    g.glass(g.circle(*L.pt(0, 300), 60), '#f2c230')       # a yellow sun, one piece
    g.trace(L.P([(-40, 500), (0, 470), (40, 500)]), 4)    # a grisaille line
    g.lead(); g.saddle_bar(L, 520); g.daylight()
    g.save('window.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, shift, load_font, text_mask

NANG = 8                                          # streak directions available to the glass pieces
PAINT_T = np.array([0.030, 0.022, 0.016], np.float32)   # transmission of fully opaque fired grisaille (brown-black)
STAIN = '#f0b43a'                                 # silver stain at full strength on white glass

# medieval pot-metal glass, as it looks with daylight behind it
RUBY, BLUE, DEEP_BLUE, SKY = '#b3182c', '#2456b0', '#173c8f', '#5d8fd0'
GREEN, LEAF, SPRING, OLIVE = '#2f8a3c', '#4fa83f', '#9ccd52', '#7c8a2a'
GOLD, AMBER, ORANGE, MURREY = '#f2c230', '#e0922a', '#d0601e', '#7a2c5c'
WHITE, PALE, BROWN, FLESH = '#eeeadb', '#d7e2ea', '#6e4526', '#e9c9a8'

_FONT_FILES = {
    'lombardic': ['/System/Library/Fonts/Supplemental/Luminari.ttf', '/System/Library/Fonts/Supplemental/Herculanum.ttf',
                  '/usr/share/fonts/**/*Uncial*.[ot]tf', '/usr/share/fonts/**/*Unifraktur*.[ot]tf',
                  'C:/Windows/Fonts/OLDENGL.TTF'],
    'roman': ['/System/Library/Fonts/Supplemental/Trajan*.[ot]tf', '/System/Library/Fonts/Optima.ttc',
              '/System/Library/Fonts/Supplemental/Baskerville.ttc', '/usr/share/fonts/**/DejaVuSerif.ttf',
              'C:/Windows/Fonts/georgia.ttf'],
}


def glass_font(style, size):
    """PIL font: 'lombardic' (Luminari / Herculanum / an uncial) or 'roman'; $INKPAINT_FONT_LOMBARDIC overrides;
    falls back to core.load_font('serif')"""
    env = os.environ.get('INKPAINT_FONT_' + style.upper())
    cands = ([env] if env else []) + _FONT_FILES.get(style, [])
    for pat in cands:
        for f in glob.glob(pat, recursive=True):
            try:
                return ImageFont.truetype(f, int(size))
            except OSError:
                pass
    return load_font('serif', size)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def lin(c):
    """'#rrggbb' or sRGB triple -> linear light"""
    c = hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)
    return np.clip(c, 0, 1) ** 2.2


def _hash(i, j, seed):
    h = (i.astype(np.int64) * 73856093) ^ (j.astype(np.int64) * 19349663) ^ np.int64(seed * 83492791)
    h &= 0xFFFFFFFF
    h = ((h ^ (h >> 16)) * 0x45d9f3b) & 0xFFFFFFFF
    h = ((h ^ (h >> 16)) * 0x45d9f3b) & 0xFFFFFFFF
    return h ^ (h >> 16)


class Light:
    """one pointed-arch light (glass opening). Local coordinates: origin at the apex, x right, y down.
    sdf(): signed distance inside the glass edge (px, positive inside); inner(b) / band(b0, b1) are AA masks."""

    def __init__(self, g, cx, top, bottom, width, arch, splay, sill):
        self.g, self.cx, self.top, self.bottom = g, float(cx), float(top), float(bottom)
        self.a = width / 2.0
        self.R = max(arch * width, self.a)                      # arch=1: equilateral (each arc centred on the far springing)
        self.h = float(np.sqrt(self.R ** 2 - (self.R - self.a) ** 2))
        self.ys = self.top + self.h                             # springing line
        self.splay, self.sill = splay, sill
        self.width, self.height = width, bottom - top
        self._sdf = None

    def pt(self, lx, ly):
        return (self.cx + lx, self.top + ly)

    def P(self, pts):
        p = np.asarray(pts, np.float32).copy()
        p[:, 0] += self.cx; p[:, 1] += self.top
        return p

    def sdf_at(self, X, Y):
        dx = np.abs(X - self.cx)
        rect = np.minimum(self.a - dx, self.bottom - Y)
        cl = self.cx - self.a + self.R                          # centre of the arc that bounds the left side
        cr = self.cx + self.a - self.R
        arch = np.minimum(self.R - np.hypot(X - cl, Y - self.ys), self.R - np.hypot(X - cr, Y - self.ys))
        arch = np.minimum(arch, self.bottom - Y)
        return np.where(Y >= self.ys, rect, arch).astype(np.float32)

    def sdf(self):
        if self._sdf is None:
            self._sdf = self.sdf_at(self.g.XX, self.g.YY)
        return self._sdf

    def inner(self, b=0.0):
        """mask of the glass shrunk by b px (b=0: the whole light)"""
        return np.clip(self.sdf() - b + 0.5, 0, 1)

    def band(self, b0, b1):
        """mask of the strip b0 < sdf < b1 (a border band running round the light)"""
        s = self.sdf()
        return np.clip(s - b0 + 0.5, 0, 1) * np.clip(b1 - s + 0.5, 0, 1)

    def outline(self, b=0.0, step=20.0):
        """points (N x 2, image coords) round the outline shrunk by b, every ~step px: bottom, right side,
        right arc, left arc, left side"""
        a, R = self.a - b, self.R - b
        yb, ys, cx = self.bottom - b, self.ys, self.cx
        cr, cl = self.cx + self.a - self.R, self.cx - self.a + self.R
        segs = []
        n = max(2, int(2 * a / step)); segs.append(np.stack([np.linspace(cx - a, cx + a, n), np.full(n, yb)], 1))
        n = max(2, int((yb - ys) / step)); segs.append(np.stack([np.full(n, cx + a), np.linspace(yb, ys, n)], 1))
        th1 = -np.arccos(np.clip((cx - cr) / R, -1, 1))
        n = max(2, int(abs(th1) * R / step)); t = np.linspace(0, th1, n)
        segs.append(np.stack([cr + R * np.cos(t), ys + R * np.sin(t)], 1))
        th2 = -np.pi + np.arccos(np.clip((cl - cx) / R, -1, 1))
        t = np.linspace(th2, -np.pi, n)
        segs.append(np.stack([cl + R * np.cos(t), ys + R * np.sin(t)], 1))
        n = max(2, int((yb - ys) / step)); segs.append(np.stack([np.full(n, cx - a), np.linspace(ys, yb, n)], 1))
        P = np.vstack([sg[1:] if i else sg for i, sg in enumerate(segs)])
        keep = np.r_[True, np.hypot(*np.diff(P, axis=0).T) > 1e-3]
        return P[keep].astype(np.float32)

    def half(self, ly, b=0.0):
        """half-width of the outline shrunk by b at local y"""
        y = self.top + ly
        if y >= self.ys: return self.a - b
        dy = self.ys - y
        R = self.R - b
        return max(0.0, float(np.sqrt(max(R * R - dy * dy, 0))) - (self.R - self.a))


class StainedGlass:
    def __init__(self, W=1920, H=1080, seed=0, record=True, ambient=0.05):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.record = record
        self.ambient = ambient
        z = lambda: np.zeros((H, W), np.float32)
        # stone
        self.alb = np.ones((H, W, 3), np.float32) * lin('#8a8073')
        self.relief = np.ones((H, W), np.float32)
        self.kind = np.zeros((H, W), np.uint8)                  # 0 wall face, 1 reveal, 2 sill, 3 moulding
        self.reveal = z()
        self.stone_tex = z()
        self.win = z()
        self.lights = []
        # glass
        self.label = np.full((H, W), -1, np.int32)
        self.p_col, self.p_thick, self.p_ang, self.p_streak, self.p_region, self.p_off = [], [], [], [], [], []
        self.regions = []
        self.cuts = np.zeros((H, W), bool)
        self.mends = np.zeros((H, W), bool)
        self.crack_a = z()
        # paint
        self.trace_a, self.matt_a, self.scratch_a, self.stain_a = z(), z(), z(), z()
        self.grain = noise2d(H, W, 1.4, 2, self._seed()) - 0.5
        # seeds for fields made lazily at render time: fixed now, so stage snapshots never shift the random sequence
        self._lazy = [int(v) for v in self.rng.integers(1 << 30, size=6)]
        # lead, iron, light
        self.lead_a = None; self.lead_rgb = None; self.lead_d = None
        self.bar_a = z(); self.bar_rgb = np.zeros((H, W, 3), np.float32)
        self.weather_T = None
        self.lit = None
        self.stages = []
        self._T = None
        self._sky = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================== masks (full frame, anti-aliased)
    def _local(self, cx, cy, r):
        b = (slice(max(0, int(cy - r - 2)), min(self.H, int(cy + r + 3))), slice(max(0, int(cx - r - 2)), min(self.W, int(cx + r + 3))))
        return b, self.XX[b], self.YY[b]

    def circle(self, cx, cy, r):
        out = np.zeros((self.H, self.W), np.float32)
        b, X, Y = self._local(cx, cy, r)
        out[b] = np.clip(r - np.hypot(X - cx, Y - cy) + 0.5, 0, 1)
        return out

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        out = np.zeros((self.H, self.W), np.float32)
        b, X, Y = self._local(cx, cy, max(rx, ry))
        c, s = np.cos(rot), np.sin(rot)
        u = (X - cx) * c + (Y - cy) * s
        v = -(X - cx) * s + (Y - cy) * c
        d = np.hypot(u / rx, v / ry)
        out[b] = np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1)
        return out

    def poly(self, pts):
        """filled polygon -> full-frame AA mask (rasterised only inside its bounding box)"""
        P = np.asarray(pts, np.float32)
        x0, y0 = max(0, int(P[:, 0].min()) - 2), max(0, int(P[:, 1].min()) - 2)
        x1, y1 = min(self.W, int(P[:, 0].max()) + 3), min(self.H, int(P[:, 1].max()) + 3)
        out = np.zeros((self.H, self.W), np.float32)
        if x1 > x0 and y1 > y0:
            out[y0:y1, x0:x1] = polygon_mask(y1 - y0, x1 - x0, P - [x0, y0], ss=2)
        return out

    def blob(self, cx, cy, rx, ry, rough=0.1, seed=None, rot=0.0):
        from core import blob_pts
        return self.poly(blob_pts(cx, cy, rx, ry, rough, 90, self._seed() if seed is None else seed, rot))

    def branch(self, pts, w0, w1, smooth=True):
        """tapered thick polyline mask (boughs, stems): width w0 at the start to w1 at the end"""
        P = spline(pts, 10) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        w = np.linspace(w0, w1, len(P))
        y0, x0, m = self._stroke_mask(P, w)
        out = np.zeros((self.H, self.W), np.float32)
        self._paste_max(out, y0, x0, m)
        return out

    # ------------------------------------------------------------------ variable-width polyline rasteriser
    def _stroke_mask(self, P, widths, ss=3):
        P = np.asarray(P, np.float32); widths = np.asarray(widths, np.float32)
        pad = float(widths.max()) / 2 + 3
        x0, y0 = int(np.floor(P[:, 0].min() - pad)), int(np.floor(P[:, 1].min() - pad))
        x1, y1 = int(np.ceil(P[:, 0].max() + pad)), int(np.ceil(P[:, 1].max() + pad))
        w, h = max(1, x1 - x0), max(1, y1 - y0)
        im = Image.new('L', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        Q = (P - [x0, y0]) * ss
        for i in range(len(Q)):
            r = widths[i] * ss / 2
            d.ellipse([Q[i, 0] - r, Q[i, 1] - r, Q[i, 0] + r, Q[i, 1] + r], fill=255)
            if i + 1 < len(Q):
                p, q = Q[i], Q[i + 1]
                t = q - p; n = np.hypot(*t)
                if n < 1e-6: continue
                nx, ny = -t[1] / n, t[0] / n
                r2 = widths[i + 1] * ss / 2
                d.polygon([(p[0] + nx * r, p[1] + ny * r), (q[0] + nx * r2, q[1] + ny * r2),
                           (q[0] - nx * r2, q[1] - ny * r2), (p[0] - nx * r, p[1] - ny * r)], fill=255)
        m = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        return y0, x0, m

    def _paste_max(self, dst, y0, x0, m, scale=1.0):
        h, w = m.shape
        ya, xa = max(0, y0), max(0, x0)
        yb, xb = min(self.H, y0 + h), min(self.W, x0 + w)
        if ya >= yb or xa >= xb: return
        sub = m[ya - y0:yb - y0, xa - x0:xb - x0] * scale
        np.maximum(dst[ya:yb, xa:xb], sub, out=dst[ya:yb, xa:xb])

    def _crop(self, a, y0, x0, h, w):
        out = np.zeros((h, w), a.dtype)
        ya, xa, yb, xb = max(0, y0), max(0, x0), min(self.H, y0 + h), min(self.W, x0 + w)
        if ya < yb and xa < xb:
            out[ya - y0:yb - y0, xa - x0:xb - x0] = a[ya:yb, xa:xb]
        return out

    @staticmethod
    def _taper(n, taper):
        t = np.linspace(0, 1, n)
        a, b = max(taper[0], 1e-3), max(taper[1], 1e-3)
        return np.clip(np.minimum(t / a, (1 - t) / b), 0, 1) ** 0.6 * 0.75 + 0.25

    # ================================================================== stone
    def wall(self, colour='#8f8576', mortar='#6f675d', course=(60, 82), block=(110, 240)):
        """coursed ashlar: blocks of slightly different stone, tooled faces, worn arrises, recessed mortar joints"""
        H, W = self.H, self.W
        r = self.rng
        base, mcol = lin(colour), lin(mortar)
        mott = noise2d(H, W, 60, 4, self._seed())
        fine = noise2d(H, W, 3, 2, self._seed())
        self.stone_tex = (0.65 * mott + 0.35 * fine).astype(np.float32)
        alb = np.empty((H, W, 3), np.float32)
        dmin = np.full((H, W), 99, np.float32)
        tool = np.zeros((H, W), np.float32)
        top_edge = np.zeros((H, W), np.float32)
        y = -int(r.integers(10, 40))
        while y < H:
            ch = int(r.integers(*course))
            ya, yb = max(0, y), min(H, y + ch)
            if yb > ya:
                xs = [-int(r.integers(0, block[1]))]
                while xs[-1] < W:
                    xs.append(xs[-1] + int(r.integers(*block)))
                xs = np.array(xs, np.float32)
                X = self.XX[ya:yb]; Y = self.YY[ya:yb]
                k = np.clip(np.searchsorted(xs, X[0], side='right') - 1, 0, len(xs) - 2)
                left, right = xs[k], xs[k + 1]
                dx = np.minimum(X - left[None, :], right[None, :] - X)
                dy = np.minimum(Y - y, y + ch - Y)
                dmin[ya:yb] = np.minimum(dx, dy)
                top_edge[ya:yb] = (Y - y) / ch
                tint = np.stack([np.exp(r.normal(0, 0.10, len(xs))) * np.array([1 + r.normal(0, 0.03), 1, 1 + r.normal(0, 0.04)])[c]
                                 for c in range(3)], 1).astype(np.float32)
                alb[ya:yb] = base * tint[k][None, :, :]
                ang = r.uniform(0.5, 1.1, len(xs))[k]                     # every block tooled at its own angle
                ph = (X * np.cos(ang)[None, :] + Y * np.sin(ang)[None, :])
                tool[ya:yb] = np.sin(ph * 2 * np.pi / 5.5 + 3 * mott[ya:yb]) * 0.5 + 0.5
            y += ch
        wear = (noise2d(H, W, 9, 3, self._seed()) - 0.5) * 3.5            # chipped arrises
        joint = smoothstep(2.6, 1.0, dmin + wear * 0.5)
        arris = smoothstep(7, 1.5, dmin + wear)
        self.alb = alb * (0.80 + 0.32 * self.stone_tex)[..., None]
        self.alb = self.alb * (1 - joint[..., None]) + mcol * (0.8 + 0.4 * fine)[..., None] * joint[..., None]
        pits = (noise2d(H, W, 2.2, 1, self._seed()) > 0.84).astype(np.float32) * (1 - joint)
        self.relief = (1 - 0.05 * tool * (1 - joint) - 0.18 * pits - 0.22 * joint
                       - 0.10 * arris * (top_edge > 0.5) + 0.06 * arris * (top_edge <= 0.5)).astype(np.float32)
        self.kind[:] = 0

    def lancet(self, cx, top, bottom, width, arch=1.0, splay=30, sill=44, hood=16, voussoir=8.5):
        """cut a pointed-arch light into the wall: glass opening, splayed reveal (radial voussoir joints round the
        arch, coursed joints down the sides), a sloping sill below and a roll hood mould over the arch.
        arch=1 is equilateral; >1 is a sharper lancet. Returns a Light."""
        L = Light(self, cx, top, bottom, width, arch, splay, sill)
        self.lights.append(L)
        m_ = splay + (hood or 0) + 6
        y0, y1 = max(0, int(top - m_ * 1.3 - 6)), min(self.H, int(bottom + sill + 3))
        x0, x1 = max(0, int(cx - L.a - m_)), min(self.W, int(cx + L.a + m_ + 1))
        sl = (slice(y0, y1), slice(x0, x1))                                   # everything happens inside this box
        X, Y = self.XX[sl], self.YY[sl]
        s = L.sdf()[sl]
        win, rvl, kind, alb, relief = self.win[sl], self.reveal[sl], self.kind[sl], self.alb[sl], self.relief[sl]
        tex = self.stone_tex[sl]
        np.maximum(win, np.clip(s + 0.5, 0, 1), out=win)
        dx = np.abs(X - L.cx)
        below = Y > L.bottom
        depth = np.clip((Y - L.bottom) / sill, 0, 1)
        side_low = below & (Y <= L.bottom + sill) & (dx <= L.a + splay) & (dx > L.a + splay * depth)
        sill_m = below & (Y <= L.bottom + sill) & (dx <= L.a + splay * depth)
        rev = (s < 0) & (s >= -splay) & ~below
        reveal = rev | side_low
        # reveal position 0 (wall edge) .. 1 (glass edge)
        rvl[rev] = (1 + s / splay)[rev]
        rvl[side_low] = (1 - (dx - L.a) / splay)[side_low]
        rvl[sill_m] = (1 - depth)[sill_m]
        kind[reveal] = 1
        kind[sill_m] = 2
        # joints on the reveal: radial voussoirs round the arch, coursed below the springing
        cl, cr = L.cx - L.a + L.R, L.cx + L.a - L.R
        Cx = np.where(X < L.cx, cl, cr)
        phi = np.arctan2(Y - L.ys, X - Cx)
        rr = np.hypot(X - Cx, Y - L.ys)
        step = np.deg2rad(voussoir)
        jd_arch = np.abs((phi / step) - np.round(phi / step)) * step * rr
        jd_arch = np.minimum(jd_arch, np.abs(X - L.cx))                    # joint at the apex
        course = 56.0
        jd_side = np.abs(((Y - L.ys) / course) - np.round((Y - L.ys) / course)) * course
        jd = np.where(Y < L.ys, jd_arch, jd_side)
        jd = np.where(sill_m, np.abs(((X - L.cx) / 70) - np.round((X - L.cx) / 70)) * 70 / (0.6 + depth), jd)
        joint = smoothstep(1.8, 0.6, jd)
        stone = lin('#9a9081') * (0.80 + 0.34 * tex)[..., None]
        surf = stone * (1 - joint[..., None]) + lin('#746b60') * joint[..., None]
        m2 = reveal | sill_m
        alb[m2] = surf[m2]
        edge = smoothstep(3.0, 0.0, np.abs(s + splay)) * rev                  # arris where reveal meets the wall face
        rel = 1 - 0.2 * joint + 0.18 * edge
        rel = np.where(sill_m, rel * (1 - 0.15 * smoothstep(0.85, 1.0, depth)), rel)
        relief[m2] = rel[m2]
        # hood mould: a roll moulding following the arch, ending in square label stops
        if hood:
            t = (-(s + splay)) / hood                                          # 0 inner .. 1 outer
            stop = (Y > L.ys + 18) & (Y < L.ys + 18 + hood * 1.2)
            hm = (t >= 0) & (t <= 1) & (Y < L.ys + 18)
            st = stop & (dx >= L.a + splay - 2) & (dx <= L.a + splay + hood + 4)
            prof = np.clip(np.sin(np.clip(t, 0, 1) * np.pi), 0, 1) ** 0.7  # a roll: lit crown, darker flanks
            shade = 0.55 + 0.6 * prof - 0.18 * np.clip(t, 0, 1)
            hs = hm | st
            alb[hs] = (lin('#a49a8a') * (0.82 + 0.3 * tex)[..., None])[hs]
            relief[hm] = shade[hm]
            relief[st] = (0.95 - 0.25 * ((Y - L.ys - 18) / (hood * 1.2)))[st]
            kind[hs] = 3
        self._T = None
        return L

    def string_course(self, y, h=24, colour='#a1978a'):
        """a moulded horizontal band across the wall: lit top, shadowed undercut"""
        m = (self.YY >= y) & (self.YY < y + h)
        t = (self.YY - y) / h
        shade = np.where(t < 0.35, 1.15 - 0.2 * t, np.where(t < 0.8, 0.9 - 0.3 * (t - 0.35), 0.45))
        self.alb = np.where(m[..., None], lin(colour) * (0.82 + 0.3 * self.stone_tex)[..., None], self.alb)
        self.relief = np.where(m, shade, self.relief).astype(np.float32)
        self.relief[int(y + h):int(y + h + 6)] *= np.linspace(0.6, 1, 6)[:, None]   # shadow under the band
        self.kind[m] = 3

    # ================================================================== glass
    def _voronoi(self, X, Y, cell, seed, jitter, around, spokes, aspect, angle):
        if around is not None:
            dx, dy = X - around[0], Y - around[1]
            r = np.hypot(dx, dy)
            n = int(spokes or max(6, round(2 * np.pi * float(np.median(r)) / cell)))
            U = r / cell
            V = (np.arctan2(dy, dx) + np.pi) / (2 * np.pi) * n
            period = n
        else:
            c, s = np.cos(angle), np.sin(angle)
            U = (X * c + Y * s) / (cell * aspect)
            V = (-X * s + Y * c) / (cell / aspect)
            period = None
        iu, iv = np.floor(U).astype(np.int64), np.floor(V).astype(np.int64)
        best = np.full(U.shape, np.inf, np.float32)
        bid = np.zeros(U.shape, np.int64)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                ci, cj = iu + di, iv + dj
                cw = np.mod(cj, period) if period else cj
                h = _hash(ci, cw, seed)
                su = ci + 0.5 + jitter * ((h & 0xFFFF) / 65535.0 - 0.5)
                sv = cj + 0.5 + jitter * (((h >> 16) & 0xFFFF) / 65535.0 - 0.5)
                d = ((U - su) ** 2 + (V - sv) ** 2).astype(np.float32)
                upd = d < best
                best = np.where(upd, d, best)
                bid = np.where(upd, ci * 1000003 + cw, bid)
        return bid

    def glass(self, mask, colour, cell=None, streak=0.5, seeds=1.0, thick=1.0, vary=1.0, flashed=False,
              around=None, spokes=None, aspect=1.0, angle=0.0, jitter=0.9, streak_dir=None, sites=None):
        """lay one area of pot-metal glass of `colour` (its look with daylight behind it).
        cell: cut it into a Voronoi mosaic of about this piece size (None = one piece);
        around=(x, y): cut in polar coordinates round a point (pieces radiate; `spokes` sets how many);
        aspect/angle: stretch the pieces along a direction; streak: strength of the reams; seeds: bubbles;
        thick: thickness (darker, more saturated); vary: piece-to-piece shade variation; flashed: ruby-style
        streaky flash layer; streak_dir: fix the ream direction (radians) instead of a random one per piece;
        sites: explicit cut points (N x 2) -- each piece is the area nearest one site (borders: sites along the band).
        colour may be a list: Voronoi pieces pick from it at random, site pieces cycle through it.
        Later glass is cut out of earlier glass. Returns the region id."""
        m = (np.asarray(mask) > 0.5) & (self.win > 0.02)
        if not m.any(): return None
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        sub = m[y0:y1, x0:x1]
        if sites is not None:
            S = np.asarray(sites, np.float32)
            py, px = np.nonzero(sub)
            px = px.astype(np.float32) + x0; py = py.astype(np.float32) + y0
            inv = np.zeros(len(px), np.int64); best = np.full(len(px), np.inf, np.float32)
            for i, (sx, sy) in enumerate(S):
                d = (px - sx) ** 2 + (py - sy) ** 2
                u = d < best; best[u] = d[u]; inv[u] = i
            n = len(S)
        elif cell:
            bid = self._voronoi(self.XX[y0:y1, x0:x1], self.YY[y0:y1, x0:x1], cell, self._seed(), jitter,
                                around, spokes, aspect, angle)
            _, inv = np.unique(bid[sub], return_inverse=True)
            n = int(inv.max()) + 1
        else:
            inv = np.zeros(int(sub.sum()), np.int64); n = 1
        base = len(self.p_col)
        lab = self.label[y0:y1, x0:x1]
        lab[sub] = base + inv.reshape(-1).astype(np.int32)
        rid = len(self.regions)
        cols = [lin(c) for c in colour] if isinstance(colour, (list, tuple)) and isinstance(colour[0], str) else [lin(colour)]
        col = cols[0]
        r = self.rng
        for i in range(n):
            ci = cols[i % len(cols)] if sites is not None else cols[int(r.integers(0, len(cols)))]
            v = np.exp(r.normal(0, 0.11 * vary))
            c = np.clip(ci * v * np.exp(r.normal(0, 0.05 * vary, 3)), 1e-4, 1)
            self.p_col.append(c)
            self.p_thick.append(thick * r.uniform(0.8, 1.3))
            if streak_dir is None:
                self.p_ang.append(int(r.integers(0, NANG)))
            else:
                self.p_ang.append(int(round((streak_dir % np.pi) / np.pi * NANG)) % NANG)
            self.p_streak.append(streak * r.uniform(0.5, 1.5) * (2.2 if flashed else 1.0))
            self.p_region.append(rid)
            self.p_off.append(float(r.uniform(0, 4000)))                    # each piece cut from elsewhere in the sheet
        self.regions.append(dict(colour=col, seeds=seeds, flashed=flashed))
        self._T = None
        return rid

    def cut(self, pts, smooth=False):
        """an extra cut line (lead) through glass, e.g. to divide a trunk or a long border strip"""
        P = spline(pts, 8) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        im = Image.new('1', (self.W, self.H), 0)
        ImageDraw.Draw(im).line([tuple(map(float, p)) for p in P], fill=1, width=1)
        self.cuts |= np.asarray(im, bool) & (self.win > 0.5)

    def crack(self, pts, mend=True):
        """a crack running through glass; mend=True covers it with a thin strap lead, as restorers did"""
        P = np.asarray(pts, np.float32)
        n = max(8, int(np.hypot(*(P[-1] - P[0])) / 6))
        t = np.linspace(0, 1, n)
        Q = np.stack([np.interp(t, np.linspace(0, 1, len(P)), P[:, 0]), np.interp(t, np.linspace(0, 1, len(P)), P[:, 1])], 1)
        Q[1:-1] += self.rng.normal(0, 1.6, (n - 2, 2))
        y0, x0, m = self._stroke_mask(Q, np.full(n, 1.2))
        self._paste_max(self.crack_a, y0, x0, m)
        if mend:
            im = Image.new('1', (self.W, self.H), 0)
            ImageDraw.Draw(im).line([tuple(map(float, p)) for p in Q], fill=1, width=1)
            self.mends |= np.asarray(im, bool)

    def _tidy(self):
        """merge slivers (too small or too thin to cut) into the neighbour of the same glass they share most edge with"""
        for _ in range(3):
            lab = self.label
            n = len(self.p_col)
            if n == 0: return
            reg = np.array(self.p_region + [-1], np.int64)
            area = np.bincount(lab[lab >= 0], minlength=n)
            a = np.concatenate([lab[:, :-1].ravel(), lab[:-1, :].ravel()])
            b = np.concatenate([lab[:, 1:].ravel(), lab[1:, :].ravel()])
            d = a != b
            a, b = a[d], b[d]
            per = np.bincount(a[a >= 0], minlength=n) + np.bincount(b[b >= 0], minlength=n)
            small = (area > 0) & ((area < 170) | (area < per * 2.6))
            if not small.any(): return
            src = np.concatenate([a, b]); dst = np.concatenate([b, a])
            ok = (src >= 0) & (dst >= 0)
            src, dst = src[ok], dst[ok]
            ok = small[src] & ~small[dst] & (reg[src] == reg[dst])
            src, dst = src[ok], dst[ok]
            if len(src) == 0: return
            key, cnt = np.unique(src * n + dst, return_counts=True)
            s_, d_ = key // n, key % n
            order = np.lexsort((-cnt, s_))
            s_, d_ = s_[order], d_[order]
            first = np.r_[True, s_[1:] != s_[:-1]]
            mp = np.arange(n + 1, dtype=np.int32); mp[-1] = -1
            mp[s_[first]] = d_[first]
            self.label = np.where(lab >= 0, mp[lab], -1).astype(np.int32)
        self._T = None

    def _glass_T(self):
        """per-pixel transmission of the bare glass (linear RGB), cached"""
        if self._T is not None: return self._T
        H, W = self.H, self.W
        lab = self.label
        m = lab >= 0
        T = np.zeros((H, W, 3), np.float32)
        if not m.any():
            self._T = T; return T
        idx = lab[m]
        if not hasattr(self, '_thick_n'):
            self._thick_n = (noise2d(H, W, 80, 3, self._lazy[0]) * 2 - 1).astype(np.float32)
            self._warp = (noise2d(H, W, 240, 3, self._lazy[1]) - 0.5).astype(np.float32)
            self._sheen = (noise2d(H, W, 30, 3, self._lazy[2]) * 2 - 1).astype(np.float32)
        pang = np.array(self.p_ang, np.int64)
        ang = np.full((H, W), -1, np.int64); ang[m] = pang[idx]
        off = np.zeros((H, W), np.float32); off[m] = np.array(self.p_off, np.float32)[idx]
        st = np.zeros((H, W), np.float32)
        nd = int(np.hypot(W, H)) + 4600
        for k in range(NANG):
            sel = ang == k
            if not sel.any(): continue
            a = np.pi * k / NANG
            ys_, xs_ = np.nonzero(sel)
            dd = xs_ * np.cos(a) + ys_ * np.sin(a) + self._warp[sel] * 40 + H + 200 + off[sel]
            tab = 0.7 * fbm1d(nd, 4, 4, 1000 + k) + 0.3 * fbm1d(nd, 30, 3, 2000 + k)
            st[sel] = np.interp(dd, np.arange(nd), tab)
        st = st / (np.abs(st[m]).max() + 1e-6)
        pc = np.array(self.p_col, np.float32)[idx]
        n_p = len(self.p_col)
        ys_m, xs_m = np.nonzero(m)
        cnt = np.bincount(idx, minlength=n_p) + 1e-6
        cxp = np.bincount(idx, xs_m, n_p) / cnt; cyp = np.bincount(idx, ys_m, n_p) / cnt
        ga = np.random.default_rng(77).uniform(0, 2 * np.pi, n_p)
        grad = ((xs_m - cxp[idx]) * np.cos(ga[idx]) + (ys_m - cyp[idx]) * np.sin(ga[idx])) / 45.0
        th = np.array(self.p_thick, np.float32)[idx] * (1 + 0.18 * self._thick_n[m]) * np.clip(1 + 0.22 * grad, 0.6, 1.5)
        amp = np.array(self.p_streak, np.float32)[idx]
        th = th * np.clip(1 + 0.55 * amp * st[m], 0.2, 3)
        Tm = pc ** th[:, None]
        Tm *= (1 + 0.05 * self._sheen[m])[:, None]
        T[m] = Tm
        T *= (1 + self._bubbles(ang))[..., None]
        self._T = np.clip(T, 0, 1.2).astype(np.float32)
        return self._T

    def _bubbles(self, ang):
        """seeds: tiny air bubbles drawn out along the reams -- a bright core in a dark refracting rim"""
        H, W = self.H, self.W
        out = np.zeros((H, W), np.float32)
        lab = self.label
        ys, xs = np.nonzero(lab >= 0)
        if len(ys) == 0: return out
        r = np.random.default_rng(self._lazy[3])
        n = len(ys) // 520
        pick = r.integers(0, len(ys), n)
        seeds = np.array([g['seeds'] for g in self.regions], np.float32)
        reg = np.array(self.p_region, np.int64)
        R = 7
        ky, kx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
        for i in pick:
            y, x = int(ys[i]), int(xs[i])
            if r.random() > seeds[reg[lab[y, x]]] * 0.6: continue
            if y < R or x < R or y >= H - R or x >= W - R: continue
            a = np.pi * ang[y, x] / NANG
            Lb, wb = r.uniform(1.2, 5.5) * (1.6 if r.random() < 0.15 else 1), r.uniform(0.9, 2.0)
            u = kx * np.cos(a) + ky * np.sin(a)
            v = -kx * np.sin(a) + ky * np.cos(a)
            e = np.sqrt((u / max(Lb, wb)) ** 2 + (v / wb) ** 2)
            k = 0.55 * np.exp(-e * e * 3) - 0.45 * np.exp(-((e - 1.05) ** 2) / 0.06)
            out[y - R:y + R + 1, x - R:x + R + 1] += k * r.uniform(0.5, 1.0)
        return out

    # ================================================================== grisaille paint and silver stain
    def trace(self, pts, width=3.5, taper=(0.2, 0.3), opacity=0.97, smooth=True, wobble=0.5, clip=None):
        """an opaque grisaille trace line laid with a long-haired brush: swells and tapers, slightly ragged edge.
        clip: optional full-frame mask the line is confined to (e.g. only over the sky, not over foliage)"""
        P = spline(pts, 8) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        if len(P) < 2: return
        if wobble:
            seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
            L = float(seg.sum())
            if L > 30 and len(P) > 3:
                t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-6
                P = P + np.stack([-t[:, 1], t[:, 0]], 1) * fbm1d(len(P), 12, 2, self._seed())[:, None] * wobble
        w = width * self._taper(len(P), taper) * (1 + 0.12 * fbm1d(len(P), 10, 2, self._seed()))
        y0, x0, m = self._stroke_mask(P, w)
        g = self._crop(self.grain, y0, x0, *m.shape)
        m = np.clip(m * (1 + 0.5 * g) * 1.1, 0, 1)                           # paint load: slightly ragged, uneven
        if clip is not None:
            m = m * self._crop(np.asarray(clip, np.float32), y0, x0, *m.shape)
        self._paste_max(self.trace_a, y0, x0, m, opacity)

    def traces(self, strokes, width=3.5, **kw):
        for p in strokes:
            self.trace(p, width, **kw)

    def _box(self, mask, pad):
        """bounding box (slices) of the non-zero part of a full-frame mask, padded; None if empty"""
        rows, cols = np.nonzero(mask.any(1))[0], np.nonzero(mask.any(0))[0]
        if len(rows) == 0: return None
        p = int(pad)
        return (slice(max(0, rows[0] - p), min(self.H, rows[-1] + p + 1)),
                slice(max(0, cols[0] - p), min(self.W, cols[-1] + p + 1)))

    def matt(self, mask, strength=0.5, soft=4.0, stipple=0.6):
        """a semi-opaque wash of paint, badgered smooth and stippled (fine mottled texture)"""
        mask = np.asarray(mask, np.float32)
        b = self._box(mask > 1e-3, 3 * soft + 3)
        if b is None: return
        m = blur(mask[b], soft) if soft else mask[b]
        st = np.clip(1 + stipple * self.grain[b] * 2.2, 0, 2)
        a = np.clip(strength * m * st, 0, 1)
        self.matt_a[b] = 1 - (1 - self.matt_a[b]) * (1 - a)

    def shade(self, mask, offset=(10, 10), strength=0.55, soft=5.0, clip=None):
        """model volume with matt on the side away from the light: the shape minus itself moved toward the light"""
        m = np.asarray(mask, np.float32)
        b = self._box(m > 1e-3, 3 * soft + max(abs(offset[0]), abs(offset[1])) + 3)
        if b is None: return
        mb = m[b]
        cres = np.clip(mb - shift(mb, -offset[0], -offset[1]), 0, 1)
        cres = blur(cres, soft) * mb
        if clip is not None: cres = cres * np.asarray(clip, np.float32)[b]
        st = np.clip(1 + 0.6 * self.grain[b] * 2.2, 0, 2)
        a = np.clip(strength * cres * st, 0, 1)
        self.matt_a[b] = 1 - (1 - self.matt_a[b]) * (1 - a)

    def scratch(self, pts, width=2.0, smooth=True):
        """scrape paint back off with a stick (sticklighting): highlights, hair, veins, patterns"""
        P = spline(pts, 8) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        if len(P) < 2: P = np.vstack([P, P + 0.01])
        w = width * self._taper(len(P), (0.15, 0.15))
        y0, x0, m = self._stroke_mask(P, w)
        self._paste_max(self.scratch_a, y0, x0, m)

    def scratch_mask(self, mask):
        np.maximum(self.scratch_a, np.asarray(mask, np.float32), out=self.scratch_a)

    def stain(self, mask, strength=1.0):
        """silver stain: fired yellow on white glass (lemon at low strength, amber at high); on blue it makes green"""
        np.maximum(self.stain_a, np.clip(np.asarray(mask, np.float32) * strength, 0, 1.6), out=self.stain_a)

    def diaper(self, mask, spacing=28, motif='cross', size=5.0, paint=0.3, scratched=True, jitter=0.0,
               width=1.8, rot=0.0):
        """a background pattern: a light matt over `mask` with a lattice of small motifs scratched out of it
        (scratched=False paints the motifs dark instead). motif: cross, dot, ring, flake (six-armed), quatrefoil;
        jitter > 0 scatters them (falling snow)"""
        m = np.asarray(mask, np.float32)
        ys, xs = np.nonzero(m > 0.5)
        if len(ys) == 0: return
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        if paint: self.matt(m, paint, soft=1.5)
        r = self.rng
        strokes = []
        for j, gy in enumerate(np.arange(y0, y1 + spacing, spacing * 0.866)):
            for gx in np.arange(x0 + (spacing / 2 if j % 2 else 0), x1 + spacing, spacing):
                x, y = gx + r.normal(0, jitter * spacing * 0.3), gy + r.normal(0, jitter * spacing * 0.3)
                xi, yi = int(x), int(y)
                if not (0 <= xi < self.W and 0 <= yi < self.H) or m[yi, xi] < 0.9: continue
                s = size * (r.uniform(0.6, 1.2) if jitter else 1)
                a0 = rot + (r.uniform(0, np.pi) if jitter else 0)
                if motif == 'cross':
                    for a in (a0, a0 + np.pi / 2):
                        strokes.append(np.array([[x - s * np.cos(a), y - s * np.sin(a)], [x + s * np.cos(a), y + s * np.sin(a)]]))
                elif motif == 'flake':
                    for k in range(3):
                        a = a0 + k * np.pi / 3
                        strokes.append(np.array([[x - s * np.cos(a), y - s * np.sin(a)], [x + s * np.cos(a), y + s * np.sin(a)]]))
                elif motif in ('dot', 'ring'):
                    t = np.linspace(0, 2 * np.pi, 14)
                    rr = s * (0.35 if motif == 'dot' else 1)
                    strokes.append(np.stack([x + rr * np.cos(t), y + rr * np.sin(t)], 1))
                elif motif == 'quatrefoil':
                    for k in range(4):
                        a = a0 + k * np.pi / 2
                        cx, cy = x + s * 0.55 * np.cos(a), y + s * 0.55 * np.sin(a)
                        t = np.linspace(0, 2 * np.pi, 12)
                        strokes.append(np.stack([cx + s * 0.4 * np.cos(t), cy + s * 0.4 * np.sin(t)], 1))
        tgt = self.scratch_a if scratched else self.trace_a
        for P in strokes:
            wv = np.full(len(P), width if motif != 'dot' else size * 0.7)
            y0_, x0_, mm = self._stroke_mask(P, wv)
            self._paste_max(tgt, y0_, x0_, mm, 1.0 if scratched else 0.9)

    def inscribe(self, s, x, y, size, font='lombardic', anchor='mm', spacing=0.0, scratched=False, stroke=0):
        """lettering: painted dark (default) or scratched out of a matt so it shines (scratched=True)"""
        f = glass_font(font, size)
        m = text_mask(self.H, self.W, s, f, (x, y), anchor, spacing)
        if stroke:
            m = np.clip(blur(m, stroke) * 2.2, 0, 1)
        if scratched:
            np.maximum(self.scratch_a, m, out=self.scratch_a)
        else:
            np.maximum(self.trace_a, np.clip(m * (1.05 + 0.4 * self.grain), 0, 1) * 0.96, out=self.trace_a)

    # ================================================================== lead, iron, weather, light
    def _boundary_dist(self, B, R):
        """distance (px) from every pixel to the nearest True pixel of B, up to R (disk of offsets)"""
        ys, xs = np.nonzero(B)
        d = np.full((self.H, self.W), np.inf, np.float32)
        if len(ys) == 0: return d
        y0, y1 = max(0, ys.min() - R - 1), min(self.H, ys.max() + R + 2)
        x0, x1 = max(0, xs.min() - R - 1), min(self.W, xs.max() + R + 2)
        b = B[y0:y1, x0:x1]
        dd = np.full(b.shape, np.inf, np.float32)
        offs = sorted(((ox, oy) for oy in range(-R, R + 1) for ox in range(-R, R + 1) if ox * ox + oy * oy <= R * R),
                      key=lambda o: o[0] ** 2 + o[1] ** 2)
        for ox, oy in offs:
            sb = shift(b, ox, oy)
            new = sb & np.isinf(dd)
            dd[new] = np.hypot(ox, oy)
        d[y0:y1, x0:x1] = dd
        return d

    def lead(self, width=6.0, rim=10.0, solder=True, mend=3.2):
        """lead the window up: H-section came on every piece boundary, cut line and the rim of each light;
        soldered joints; thin strap leads over mended cracks"""
        self._tidy()
        lab = self.label
        H, W = self.H, self.W
        B = np.zeros((H, W), bool)
        dh = lab[:, 1:] != lab[:, :-1]
        dv = lab[1:, :] != lab[:-1, :]
        B[:, 1:] |= dh; B[:, :-1] |= dh
        B[1:, :] |= dv; B[:-1, :] |= dv
        B &= (lab >= 0) | np.roll(lab >= 0, 1, 0) | np.roll(lab >= 0, 1, 1)
        rimzone = np.zeros((H, W), np.float32)
        for L in self.lights:
            rimzone = np.maximum(rimzone, smoothstep(rim + 3, rim - 1, L.sdf()) * (L.sdf() > -2))
        B &= rimzone < 0.5                                                   # the rim came covers the edge itself
        B |= self.cuts
        hw = width / 2
        d = self._boundary_dist(B, int(hw + 4)) + 0.5
        # solder joints where three or more pieces meet
        if solder:
            a, b, c, e = lab[:-1, :-1], lab[:-1, 1:], lab[1:, :-1], lab[1:, 1:]
            cnt = 1 + (b != a) + ((c != a) & (c != b)) + ((e != a) & (e != b) & (e != c))
            J = np.zeros((H, W), np.float32); J[:-1, :-1] = (cnt >= 3)
            J *= (lab >= 0)
            sol = smoothstep(0.015, 0.09, blur(J, 2.6))
            sol *= (0.75 + 0.5 * (noise2d(H, W, 6, 2, self._seed())))
        else:
            sol = np.zeros((H, W), np.float32)
        de = d - 2.4 * sol
        cov_in = smoothstep(hw + 0.75, hw - 0.75, de)
        h_in = np.sqrt(np.clip(1 - (np.clip(de, 0, None) / (hw + 0.6)) ** 2, 0, 1)) * cov_in
        # rim came
        cov_rim = np.zeros((H, W), np.float32); h_rim = np.zeros((H, W), np.float32)
        for L in self.lights:
            s = L.sdf()
            cr = smoothstep(rim + 0.75, rim - 0.75, s) * (s > -3)
            t = np.clip(s / rim, 0, 1)
            hr = np.sqrt(np.clip(1 - ((t - 0.45) / 0.62) ** 2, 0, 1)) * cr
            cov_rim = np.maximum(cov_rim, cr); h_rim = np.maximum(h_rim, hr)
        # strap leads over mended cracks
        cov_m = np.zeros((H, W), np.float32); h_m = np.zeros((H, W), np.float32)
        if self.mends.any():
            dm = self._boundary_dist(self.mends, int(mend / 2 + 3)) + 0.5
            cov_m = smoothstep(mend / 2 + 0.7, mend / 2 - 0.7, dm)
            h_m = np.sqrt(np.clip(1 - (dm / (mend / 2 + 0.5)) ** 2, 0, 1)) * cov_m * 0.7
        cov = np.maximum(np.maximum(cov_in, cov_rim), cov_m) * (self.win > 0.02)
        hgt = np.maximum(np.maximum(h_in, h_rim), h_m) * (hw * 0.9) + sol * 1.6
        hgt = blur(hgt, 0.7)
        gy, gx = np.gradient(hgt)
        n = np.stack([-gx, -gy, np.ones_like(gx)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        Ld = np.array([-0.35, -0.6, 0.72], np.float32); Ld /= np.linalg.norm(Ld)
        diff = np.clip(n @ Ld, 0, 1)
        hv = Ld + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
        spec = np.clip(n @ hv, 0, 1) ** 30
        pat = noise2d(H, W, 14, 3, self._seed())                             # dull white patina (lead carbonate)
        alb = lin('#2c2d31') * (0.8 + 0.5 * pat)[..., None]
        alb = alb * (1 - sol[..., None]) + lin('#6d6f72') * sol[..., None]   # tin solder is lighter
        rgb = alb * (0.28 + 0.9 * diff)[..., None] + (0.035 + 0.06 * sol)[..., None] * spec[..., None]
        self.lead_a = cov.astype(np.float32)
        self.lead_rgb = rgb.astype(np.float32) * 0.55
        self.lead_d = np.minimum(de, np.where(cov_rim > 0, 0, 99)).astype(np.float32)
        for L in self.lights:
            self.lead_d = np.minimum(self.lead_d, np.clip(L.sdf() - rim, 0, None) + hw)
        self._T = None

    def saddle_bar(self, light, y, width=9.0, ties=True):
        """a wrought-iron saddle bar across the light on the inside, ends let into the reveal, wired to the leads"""
        L = light
        x0, x1 = L.cx - L.a - L.splay * 0.55, L.cx + L.a + L.splay * 0.55
        b = (slice(max(0, int(y - width / 2 - 6)), min(self.H, int(y + width / 2 + 7))),
             slice(max(0, int(x0) - 1), min(self.W, int(x1) + 2)))
        Y, X = self.YY[b], self.XX[b]
        t = (Y - (y - width / 2)) / width
        m = np.clip(np.minimum(Y - (y - width / 2), (y + width / 2) - Y) + 0.5, 0, 1) * \
            np.clip(np.minimum(X - x0, x1 - X) + 0.5, 0, 1)
        prof = np.clip(t, 0, 1)
        shade = 0.35 + 0.9 * np.exp(-((prof - 0.22) / 0.16) ** 2) - 0.25 * smoothstep(0.6, 1, prof)
        rust = noise2d(Y.shape[0], Y.shape[1], 8, 3, self._seed())
        col = lin('#2b2622') * (0.7 + 0.6 * rust)[..., None] * shade[..., None] + lin('#5a3a26') * 0.05 * rust[..., None]
        if ties and self.lead_a is not None:
            row_a = self.lead_a[int(y - width / 2 - 5)]
            row_b = self.lead_a[int(y + width / 2 + 5)]
            xs = np.nonzero((row_a > 0.7) & (row_b > 0.7) & (self.XX[0] > L.cx - L.a + 14) & (self.XX[0] < L.cx + L.a - 14))[0]
            runs = np.split(xs, np.nonzero(np.diff(xs) > 1)[0] + 1) if len(xs) else []
            centres = [int(r_.mean()) for r_ in runs if len(r_)]
            for x in centres[::max(1, len(centres) // 4)][:5]:                # a few ties, not one per lead
                tie = np.clip((1 - np.hypot((X - x) / 1.7, (Y - y) / (width / 2 + 2.6))) * 1.7 + 0.5, 0, 1)
                m = np.maximum(m, tie)
                col = np.where((tie > 0.05)[..., None], lin('#5a3a22') * (0.7 + 0.5 * rust)[..., None], col)
        self.bar_rgb[b] = np.where((m > 0)[..., None], col * 0.6, self.bar_rgb[b])
        self.bar_a[b] = np.maximum(self.bar_a[b], m)

    def weather(self, grime=0.5, pits=0.5):
        """age: grime along the leads and toward the bottom of each light; corrosion pits on some pieces"""
        H, W = self.H, self.W
        n = noise2d(H, W, 70, 4, self._seed())
        near = smoothstep(16, 3, self.lead_d) if self.lead_d is not None else 0
        low = np.zeros((H, W), np.float32)
        for L in self.lights:
            low = np.maximum(low, smoothstep(L.top + L.height * 0.4, L.bottom, self.YY) * (L.sdf() > 0))
        g = grime * np.clip(0.25 * n + 0.45 * near * n + 0.35 * low * n, 0, 1)
        Tm = 1 - g[..., None] * (1 - lin('#d8c6a2'))[None, None, :] * 1.3
        # pits: on a few pieces the outside skin has corroded into little dark craters with pale halos
        out = np.ones((H, W), np.float32)
        lab = self.label
        n_p = len(self.p_col)
        if pits and n_p:
            r = np.random.default_rng(self._seed())
            level = np.where(r.random(n_p) < 0.22, r.uniform(0.4, 1.0, n_p), r.uniform(0, 0.12, n_p)) * pits
            ys, xs = np.nonzero(lab >= 0)
            pick = r.integers(0, len(ys), len(ys) // 260)
            R = 4
            ky, kx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
            for i in pick:
                y, x = int(ys[i]), int(xs[i])
                if r.random() > level[lab[y, x]] or y < R or x < R or y >= H - R or x >= W - R: continue
                rr = r.uniform(0.6, 1.9)
                e = np.hypot(kx, ky) / rr
                k = 1 - 0.55 * np.exp(-e * e * 1.5) + 0.12 * np.exp(-((e - 1.6) ** 2) / 0.3)
                out[y - R:y + R + 1, x - R:x + R + 1] *= k
        self.weather_T = (Tm * out[..., None]).astype(np.float32)

    def daylight(self, strength=1.0, spill=1.0, halation=1.0, sky=('#ffffff', '#e4e9f0')):
        """turn the room on: sky light behind the glass, coloured spill on the stone, glow on the reveals, a soft
        projection of the glass on the sill, halation over the leads"""
        self.lit = dict(strength=strength, spill=spill, halation=halation)
        self._sky = sky

    # ================================================================== compositing
    def _backlight(self):
        H, W = self.H, self.W
        top, bot = self._sky or ('#ffffff', '#e4e9f0')
        if not hasattr(self, '_cloud'):
            self._cloud = noise2d(H, W, 340, 3, self._lazy[4])
        t = (self.YY / H)[..., None]
        B = lin(top) * (1 - t) + lin(bot) * t
        k = (self.lit or {}).get('strength', 1.0)
        return B * (0.86 + 0.24 * self._cloud)[..., None] * k

    def _cartoon(self):
        """the glazier's cutline drawing: paper with the cut lines in charcoal"""
        lab = self.label
        Bd = np.zeros(lab.shape, np.float32)
        Bd[:, 1:] += lab[:, 1:] != lab[:, :-1]
        Bd[1:, :] += lab[1:, :] != lab[:-1, :]
        Bd = np.clip(blur(np.clip(Bd, 0, 1) + self.cuts, 0.7) * 1.6, 0, 1)
        paper = lin('#e6dcc6') * (0.92 + 0.08 * self.grain[..., None] * 2)
        return paper * (1 - 0.8 * Bd[..., None])

    def composite(self, cartoon=False):
        H, W = self.H, self.W
        win = self.win[..., None]
        if cartoon:
            Eg = self._cartoon() * 0.75
            light = Eg * 0.5
        else:
            Eg = self._glass_T().copy()
            Eg[self.label < 0] = (0.92, 0.95, 1.0)                           # still empty: plain daylight
            P = 1 - (1 - self.trace_a * (1 - self.scratch_a)) * (1 - self.matt_a * (1 - self.scratch_a))
            Eg *= (1 - P)[..., None] + P[..., None] * PAINT_T
            del P
            if self.stain_a.any():
                S = np.clip(self.stain_a, 0, 1.6)[..., None]
                Eg *= (1 - np.minimum(S, 1)) + np.minimum(S, 1) * lin(STAIN) ** np.maximum(S, 1)
                del S
            if self.crack_a.any():
                Eg *= (1 - 0.6 * self.crack_a)[..., None]
            if self.lead_d is not None:                                      # glass just under the came is shaded
                Eg *= (1 - 0.22 * smoothstep(4.5, 0, self.lead_d - 2.5))[..., None]
            if self.weather_T is not None:
                Eg *= self.weather_T
            Eg *= self._backlight()
            light = Eg.copy()
        ba = self.bar_a[..., None]
        if self.lead_a is not None:
            la = self.lead_a[..., None]
            light *= 1 - la
            Eg *= 1 - la
            Eg += self.lead_rgb * la
        light *= (1 - ba) * win
        # stone lighting: ambient, a wide wash of the window's colours, glowing reveals, the sill's projection.
        # Until daylight() the room is lit by a fixed neutral spill, so the stone stays identical between stages.
        q = 4
        small = light[::q, ::q] if self.lit else self.win[::q, ::q, None] * np.array([0.42, 0.44, 0.48], np.float32)
        up = lambda a: np.stack([np.asarray(Image.fromarray(np.ascontiguousarray(a[..., c], np.float32)).resize((W, H), Image.BILINEAR))
                                 for c in range(a.shape[-1])], -1)
        wm = blur(self.win[::q, ::q], 40 / q)[..., None] + 1e-3
        near = np.stack([blur(small[..., c], 40 / q) for c in range(3)], -1)
        far = np.stack([blur(small[..., c], 150 / q) for c in range(3)], -1)
        k = (self.lit or {}).get('spill', 0.75)
        illum = up(k * (0.55 * far + 0.25 * near))
        illum += (self.ambient * (0.75 + 0.35 * (1 - self.YY / H)))[..., None]
        avg = up(near / wm)                                                   # average colour of the nearby glass
        del near, far
        rv = self.reveal
        f = np.where(self.kind == 1, k * (0.08 + 0.42 * rv ** 1.6), 0) + np.where(self.kind == 2, k * 0.05 * bool(self.lit), 0)
        illum += avg * f[..., None]
        del avg, f
        if self.lit:
            self._sill_light(light, illum, k)
        img = self.alb * illum
        del illum
        img *= (self.relief * (1 - self.win))[..., None]
        img += Eg * win
        del Eg
        img *= 1 - ba
        img += self.bar_rgb * ba
        if self.lit and self.lit.get('halation', 0):
            h = self.lit['halation']
            sm = up(np.stack([blur(small[..., c], 24 / q) for c in range(3)], -1))
            for c in range(3):
                bl = 0.16 * blur(light[..., c], 1.6) + 0.12 * blur(light[..., c], 6) + 0.09 * sm[..., c]
                if c == 2: bl *= 1.3                                         # blue halates most
                la = self.lead_a if self.lead_a is not None else 0
                img[..., c] += h * bl * (1 - self.win * (0.74 - 0.08 * la) - 0.4 * self.bar_a)
            del sm
        del light
        # vignette, tone, grain
        vx = (self.XX / W - 0.5) * 1.6; vy = (self.YY / H - 0.48) * 1.5
        img *= (1 - 0.42 * smoothstep(0.35, 1.25, np.hypot(vx, vy)))[..., None]
        hi = img > 0.75
        img[hi] = 0.75 + 0.25 * (1 - np.exp(-(img[hi] - 0.75) / 0.25))
        np.clip(img, 0, 1, out=img)
        img **= 1 / 2.2
        img += (self.grain * 0.018 * (1 - self.win * 0.6))[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def _sill_light(self, light, illum, k):
        """light falling through the lowest glass lands on the sloping sill as a soft, upside-down projection"""
        H, W = self.H, self.W
        for L in self.lights:
            src_h = int(L.height * 0.32)
            yb = int(L.bottom)
            x0, x1 = max(0, int(L.cx - L.a - L.splay - 2)), min(W, int(L.cx + L.a + L.splay + 2))
            src = light[yb - src_h:yb, x0:x1]
            src = np.stack([blur(src[..., c], 9) for c in range(3)], -1)
            sh = int(L.sill)
            xs = np.arange(x1 - x0, dtype=np.float32)
            c = (x1 - x0) / 2
            for j in range(sh):
                y = yb + 1 + j
                if y >= H: break
                d = j / sh
                row = src[int(src_h - 1 - d * (src_h - 1))]
                xsrc = c + (xs - c) / (1 + 0.18 * d)
                rr = np.stack([np.interp(xsrc, xs, row[:, kk]) for kk in range(3)], -1) * (1.7 - 0.9 * d)
                on = self.kind[y, x0:x1] == 2
                illum[y, x0:x1][on] += k * rr[on]

    def stage(self, name, cartoon=False):
        if self.record:
            self.stages.append((name, self.composite(cartoon)))

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
