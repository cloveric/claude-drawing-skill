"""stitch — hand embroidery on Aida cloth: cross-stitch, back-stitch, satin stitch, French knots (numpy + Pillow only).

Model:
  cloth   : Aida is woven in square blocks with a hole at every block corner. Stitches can only go
            through the holes, so the picture lives on a grid of cells (`cell` px each).
  thread  : stranded cotton is a round, slightly flattened cord of twisted plies. Every thread is lit as a
            cylinder (bright on the side facing the light, darker at its flanks), shows diagonal twist
            stripes along its length, and casts a small shadow onto the cloth.
  stitches:
    cross   one X per cell: the bottom leg '/', then the top leg '\\' laid over it (a few hand-made
            variants, so no two neighbouring X's are identical);
    back    outlines: short straight stitches from hole to hole (paths snap to the hole grid);
    satin   letters and small solid shapes: parallel floats laid side by side across the shape, with a
            sheen band, raised padding and slightly uneven float ends;
    knot    French knots: tiny wrapped beads (flower centres, eyes, apples).
  Plus `chart()` for classic ASCII charts, `letters()` for a 5x7 cross-stitch alphabet and `label()` for
  a woven label sewn on with running stitch.

    from stitch import Stitch
    s = Stitch(1920, 1080, cell=12, seed=1)
    s.cross(s.cells(s.circle(960, 540, 120)), '#c8423a')        # a filled disc in cross-stitch
    s.back([(800, 700), (1120, 700)], '#2e3f66')                 # a back-stitched line
    s.satin(s.text_mask('love', 960, 300, 90, 'script'), '#e0654a', angle=0.9)
    s.letters('HOME', 60, 10, '#2e3f66', scale=2)                # cross-stitch alphabet on the grid
    s.knot(900, 520, '#f2c14e')
    s.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, shift, load_font, text_mask

FONT5x7 = {
    'A': [' ### ', '#   #', '#   #', '#####', '#   #', '#   #', '#   #'], 'B': ['#### ', '#   #', '#   #', '#### ', '#   #', '#   #', '#### '],
    'C': [' ### ', '#   #', '#    ', '#    ', '#    ', '#   #', ' ### '], 'D': ['#### ', '#   #', '#   #', '#   #', '#   #', '#   #', '#### '],
    'E': ['#####', '#    ', '#    ', '#### ', '#    ', '#    ', '#####'], 'F': ['#####', '#    ', '#    ', '#### ', '#    ', '#    ', '#    '],
    'G': [' ### ', '#   #', '#    ', '# ###', '#   #', '#   #', ' ####'], 'H': ['#   #', '#   #', '#   #', '#####', '#   #', '#   #', '#   #'],
    'I': [' ### ', '  #  ', '  #  ', '  #  ', '  #  ', '  #  ', ' ### '], 'J': ['  ###', '   # ', '   # ', '   # ', '   # ', '#  # ', ' ##  '],
    'K': ['#   #', '#  # ', '# #  ', '##   ', '# #  ', '#  # ', '#   #'], 'L': ['#    ', '#    ', '#    ', '#    ', '#    ', '#    ', '#####'],
    'M': ['#   #', '## ##', '# # #', '# # #', '#   #', '#   #', '#   #'], 'N': ['#   #', '#   #', '##  #', '# # #', '#  ##', '#   #', '#   #'],
    'O': [' ### ', '#   #', '#   #', '#   #', '#   #', '#   #', ' ### '], 'P': ['#### ', '#   #', '#   #', '#### ', '#    ', '#    ', '#    '],
    'Q': [' ### ', '#   #', '#   #', '#   #', '# # #', '#  # ', ' ## #'], 'R': ['#### ', '#   #', '#   #', '#### ', '# #  ', '#  # ', '#   #'],
    'S': [' ####', '#    ', '#    ', ' ### ', '    #', '    #', '#### '], 'T': ['#####', '  #  ', '  #  ', '  #  ', '  #  ', '  #  ', '  #  '],
    'U': ['#   #', '#   #', '#   #', '#   #', '#   #', '#   #', ' ### '], 'V': ['#   #', '#   #', '#   #', '#   #', '#   #', ' # # ', '  #  '],
    'W': ['#   #', '#   #', '#   #', '# # #', '# # #', '# # #', ' # # '], 'X': ['#   #', '#   #', ' # # ', '  #  ', ' # # ', '#   #', '#   #'],
    'Y': ['#   #', '#   #', ' # # ', '  #  ', '  #  ', '  #  ', '  #  '], 'Z': ['#####', '    #', '   # ', '  #  ', ' #   ', '#    ', '#####'],
    '0': [' ### ', '#   #', '#  ##', '# # #', '##  #', '#   #', ' ### '], '1': ['  #  ', ' ##  ', '  #  ', '  #  ', '  #  ', '  #  ', ' ### '],
    '2': [' ### ', '#   #', '    #', '   # ', '  #  ', ' #   ', '#####'], '3': ['#####', '   # ', '  #  ', '   # ', '    #', '#   #', ' ### '],
    '4': ['   # ', '  ## ', ' # # ', '#  # ', '#####', '   # ', '   # '], '5': ['#####', '#    ', '#### ', '    #', '    #', '#   #', ' ### '],
    '6': ['  ## ', ' #   ', '#    ', '#### ', '#   #', '#   #', ' ### '], '7': ['#####', '    #', '   # ', '  #  ', ' #   ', ' #   ', ' #   '],
    '8': [' ### ', '#   #', '#   #', ' ### ', '#   #', '#   #', ' ### '], '9': [' ### ', '#   #', '#   #', ' ####', '    #', '   # ', ' ##  '],
    '.': ['     '] * 5 + [' ##  ', ' ##  '], '-': ['     '] * 3 + [' ### '] + ['     '] * 3, ' ': ['     '] * 7,
    '&': [' ##  ', '#  # ', '# #  ', ' #   ', '# # #', '#  # ', ' ## #'],
}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class Stitch:
    def __init__(self, W=1920, H=1080, cell=12, seed=0, cloth='#efe7d4', light=(-0.5, -0.62, 0.6)):
        self.W, self.H, self.cell = W, H, cell
        self.gw, self.gh = W // cell, H // cell
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.L = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.img = self._aida(_c(cloth))
        self.stages = []
        self._sprites = [self._x_sprite() for _ in range(6)]

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ cloth
    def _aida(self, col):
        c = self.cell
        u, v = (self.XX % c) / c, (self.YY % c) / c
        block = (np.sin(np.pi * u) * np.sin(np.pi * v)) ** 0.35                     # each woven block is slightly domed
        weave = 0.5 + 0.5 * np.cos(2 * np.pi * 3 * u) * np.cos(2 * np.pi * 3 * v)    # 3 x 3 threads interlaced per block
        slub = noise2d(self.H, self.W, 1.6, 2, self._seed())
        img = np.ones((self.H, self.W, 3), np.float32) * col
        img *= (0.91 + 0.065 * block + 0.03 * weave + 0.03 * slub)[..., None]
        du, dv = np.minimum(u, 1 - u) * c, np.minimum(v, 1 - v) * c
        hole = np.exp(-(du ** 2 + dv ** 2) / (2 * (c * 0.085) ** 2))                 # holes at the block corners
        img *= (1 - 0.34 * hole)[..., None]
        img *= (0.98 + 0.04 * noise2d(self.H, self.W, 300, 3, self._seed()))[..., None]
        return img

    # ------------------------------------------------------------ thread lighting
    def _shade(self, across, pdir, along, twist=1.0, pitch=None):
        """lighting of a round thread. across: -1..1 across the thread; pdir: (px, py) unit vector across it"""
        pitch = pitch or self.cell * 0.32
        nz = np.sqrt(np.clip(1 - across ** 2, 0, 1))
        nx, ny = pdir[0] * across, pdir[1] * across
        diff = np.clip(nx * self.L[0] + ny * self.L[1] + nz * self.L[2], 0, 1)
        stripes = np.sin(2 * np.pi * (along + across * pitch * 0.8) / pitch)       # twisted plies
        spec = np.clip(nz, 0, 1) ** 10 * 0.18
        return 0.42 + 0.62 * diff + 0.07 * twist * stripes * nz, spec

    def _paint(self, a, shade, spec, colour, shadow=0.38, off=(1.2, 1.6)):
        col = _c(colour)
        sh = blur(shift(a, off[0], off[1]), 1.1)
        self.img *= (1 - shadow * sh * (1 - a))[..., None]
        lit = col[None, None, :] * np.clip(shade, 0, 2)[..., None]
        lit = lit + (1 - col) * np.clip(shade - 1, 0, 1)[..., None] * 0.35 + spec[..., None]
        self.img = self.img * (1 - a[..., None]) + np.clip(lit, 0, 1) * a[..., None]

    def _x_sprite(self):
        """one hand-made X (supersampled), returns coverage and (shade, spec) in a cell"""
        c, SS = self.cell, 4
        n = c * SS
        yy, xx = (np.mgrid[0:n, 0:n].astype(np.float32) + 0.5) / SS
        legs = []
        for (ax, ay, bx, by) in [(0, c, c, 0), (0, 0, c, c)]:                     # bottom '/', then top '\'
            j = self.rng.normal(0, c * 0.03, 4)
            ins = c * 0.07
            ax_, ay_ = ax + (ins if ax == 0 else -ins) + j[0], ay + (ins if ay == 0 else -ins) + j[1]
            bx_, by_ = bx + (ins if bx == 0 else -ins) + j[2], by + (ins if by == 0 else -ins) + j[3]
            d = np.array([bx_ - ax_, by_ - ay_], np.float32); Lg = float(np.linalg.norm(d)); u = d / Lg
            p = np.array([-u[1], u[0]])
            w = c * 0.4 * self.rng.uniform(0.93, 1.07)
            along = (xx - ax_) * u[0] + (yy - ay_) * u[1]
            perp = (xx - ax_) * p[0] + (yy - ay_) * p[1]
            taper = np.clip(np.minimum(along, Lg - along) / (w * 0.45) + 0.35, 0, 1)   # legs narrow into the holes
            half = w / 2 * taper
            a = np.clip((half - np.abs(perp)) * SS / 1.5, 0, 1) * (along > -0.3) * (along < Lg + 0.3)
            across = np.clip(perp / (half + 1e-3), -1, 1)
            sh, sp = self._shade(across, p, along + self.rng.uniform(0, 5))
            legs.append((a, sh, sp, across))
        (a1, s1, p1, _), (a2, s2, p2, x2) = legs
        A = np.maximum(a1, a2)
        S = np.where(a2 > 0.5, s2, s1)
        edge = (a2 > 0.02) & (a2 < 0.7)
        S = np.where(edge, S * 0.8, S)                                               # the top leg shades the one below
        P = np.where(a2 > 0.5, p2, p1)
        ds = lambda z: z.reshape(c, SS, c, SS).mean((1, 3))
        return ds(A), ds(S), ds(P)

    # ------------------------------------------------------------ grid helpers and masks
    def cells(self, mask, thresh=0.5):
        """pixel mask -> bool cell grid (gh, gw): a cell is stitched when enough of it is covered"""
        c = self.cell
        m = mask[:self.gh * c, :self.gw * c]
        return m.reshape(self.gh, c, self.gw, c).mean((1, 3)) > thresh

    def at(self, gx, gy):
        """pixel centre of cell (gx, gy)"""
        return (gx + 0.5) * self.cell, (gy + 0.5) * self.cell

    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def poly(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=2)

    def rect(self, x0, y0, x1, y1):
        return ((self.XX >= x0) & (self.XX < x1) & (self.YY >= y0) & (self.YY < y1)).astype(np.float32)

    def text_mask(self, s, x, y, size, font='script', anchor='mm', spacing=0.0, rot=0.0):
        return text_mask(self.H, self.W, s, load_font(font, size), (x, y), anchor, spacing, rot)

    # ------------------------------------------------------------ stitches
    def cross(self, cells, colour, shade_var=0.05):
        """cross-stitch every True cell of a (gh, gw) bool grid (use cells(mask) to get one from a pixel mask)"""
        cells = np.asarray(cells, bool)
        if not cells.any(): return
        c = self.cell
        pick = self.rng.integers(0, len(self._sprites), cells.shape)
        a = np.zeros((self.gh * c, self.gw * c), np.float32); s = a.copy(); p = a.copy()
        for k, (A, S, P) in enumerate(self._sprites):
            sel = (cells & (pick == k)).astype(np.float32)
            if not sel.any(): continue
            a += np.kron(sel, A); s += np.kron(sel, S); p += np.kron(sel, P)
        var = np.kron(1 + self.rng.normal(0, shade_var, cells.shape).astype(np.float32), np.ones((c, c), np.float32))
        full = lambda z, fill=0.0: np.pad(z, ((0, self.H - z.shape[0]), (0, self.W - z.shape[1])), constant_values=fill)
        self._paint(full(a), full(s * var, 1.0), full(p), colour)

    def half(self, cells, colour, shade_var=0.05):
        """half stitches (only the '/' leg): lighter, used for sky, shading and soft backgrounds"""
        cells = np.asarray(cells, bool)
        if not cells.any(): return
        c, SS = self.cell, 4
        n = c * SS
        yy, xx = (np.mgrid[0:n, 0:n].astype(np.float32) + 0.5) / SS
        ins = c * 0.07
        ax, ay, bx, by = ins, c - ins, c - ins, ins
        d = np.array([bx - ax, by - ay]); Lg = float(np.linalg.norm(d)); u = d / Lg; pdir = np.array([-u[1], u[0]])
        w = c * 0.4
        along = (xx - ax) * u[0] + (yy - ay) * u[1]; perp = (xx - ax) * pdir[0] + (yy - ay) * pdir[1]
        half = w / 2 * np.clip(np.minimum(along, Lg - along) / (w * 0.45) + 0.35, 0, 1)
        A = np.clip((half - np.abs(perp)) * SS / 1.5, 0, 1) * (along > -0.3) * (along < Lg + 0.3)
        S, P = self._shade(np.clip(perp / (half + 1e-3), -1, 1), pdir, along)
        ds = lambda z: z.reshape(c, SS, c, SS).mean((1, 3))
        A, S, P = ds(A), ds(S), ds(P)
        sel = cells.astype(np.float32)
        var = np.kron(1 + self.rng.normal(0, shade_var, cells.shape).astype(np.float32), np.ones((c, c), np.float32))
        full = lambda z, fill=0.0: np.pad(z, ((0, self.H - z.shape[0]), (0, self.W - z.shape[1])), constant_values=fill)
        self._paint(full(np.kron(sel, A)), full(np.kron(sel, S) * var, 1.0), full(np.kron(sel, P)), colour)

    def _segments(self, segs, width, colour, shadow=0.38):
        """render straight thread segments [(p0, p1), ...] in one pass"""
        a = np.zeros((self.H, self.W), np.float32); S = np.ones((self.H, self.W), np.float32); P = np.zeros((self.H, self.W), np.float32)
        for (p0, p1) in segs:
            p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
            d = p1 - p0; Lg = float(np.linalg.norm(d))
            if Lg < 0.5: continue
            u = d / Lg; pd = np.array([-u[1], u[0]])
            m = width + 3
            x0, x1 = int(max(0, min(p0[0], p1[0]) - m)), int(min(self.W, max(p0[0], p1[0]) + m + 1))
            y0, y1 = int(max(0, min(p0[1], p1[1]) - m)), int(min(self.H, max(p0[1], p1[1]) + m + 1))
            if x1 <= x0 or y1 <= y0: continue
            X, Y = self.XX[y0:y1, x0:x1], self.YY[y0:y1, x0:x1]
            along = (X - p0[0]) * u[0] + (Y - p0[1]) * u[1]; perp = (X - p0[0]) * pd[0] + (Y - p0[1]) * pd[1]
            half = width / 2 * np.clip(np.minimum(along, Lg - along) / (width * 0.5) + 0.45, 0, 1)
            aa = np.clip((half - np.abs(perp)) / 0.8 + 0.5, 0, 1) * (along > -0.5) * (along < Lg + 0.5)
            sh, sp = self._shade(np.clip(perp / (half + 1e-3), -1, 1), pd, along + self.rng.uniform(0, 6), pitch=width * 0.9)
            sel = aa > a[y0:y1, x0:x1]
            S[y0:y1, x0:x1] = np.where(sel, sh, S[y0:y1, x0:x1]); P[y0:y1, x0:x1] = np.where(sel, sp, P[y0:y1, x0:x1])
            a[y0:y1, x0:x1] = np.maximum(a[y0:y1, x0:x1], aa)
        self._paint(a, S, P, colour, shadow)

    def back(self, pts, colour, width=None, snap=True, step=1.0, smooth=True):
        """back-stitch along a path: the path is snapped to the hole grid and sewn as short straight stitches
        (about `step` cells long), exactly as it would be on Aida"""
        c = self.cell
        width = width or c * 0.3
        P = spline(pts, 12) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
        n = max(2, int(cum[-1] / (c * step)) + 1)
        t = np.linspace(0, cum[-1], n)
        Q = np.stack([np.interp(t, cum, P[:, 0]), np.interp(t, cum, P[:, 1])], 1)
        if snap:
            Q = np.round(Q / c) * c
            keep = [0] + [i for i in range(1, len(Q)) if np.any(Q[i] != Q[i - 1])]
            Q = Q[keep]
        segs = [(Q[i], Q[i + 1]) for i in range(len(Q) - 1)]
        self._segments(segs, width, colour)

    def running(self, pts, colour, width=None, dash=1.0, gap=1.0, smooth=True):
        """running stitch (dashed line): quilting lines, label borders, wind"""
        c = self.cell
        width = width or c * 0.28
        P = spline(pts, 12) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
        segs, t = [], 0.0
        while t < cum[-1]:
            t1 = min(cum[-1], t + dash * c)
            segs.append(((np.interp(t, cum, P[:, 0]), np.interp(t, cum, P[:, 1])), (np.interp(t1, cum, P[:, 0]), np.interp(t1, cum, P[:, 1]))))
            t = t1 + gap * c
        self._segments(segs, width, colour, shadow=0.3)

    def satin(self, mask, colour, angle=0.8, period=None, pad=1.0):
        """satin stitch: parallel floats laid side by side across the shape (angle in radians), raised and glossy"""
        period = period or self.cell * 0.3
        m0 = np.clip(mask, 0, 1)
        if m0.max() <= 0: return
        ca, sa = np.cos(angle), np.sin(angle)
        q = -self.XX * sa + self.YY * ca                         # across the floats
        along = self.XX * ca + self.YY * sa
        idx = np.floor(q / period)
        f = q / period - idx
        jit = fbm1d(4096, 3, 2, self._seed())[(idx.astype(np.int64) % 4096)]
        m = smoothstep(0.4, 0.6, blur(m0, 0.7) + jit * 0.16)     # every float ends a little differently
        across = (f - 0.5) * 2
        sh, sp = self._shade(across, (-sa, ca), along, twist=0.6, pitch=period * 3)
        dome = blur(m0, self.cell * 0.4)                          # padded satin: lit on the light side
        gy, gx = np.gradient(dome)
        tilt = np.clip(-(gx * self.L[0] + gy * self.L[1]) * 6, -0.25, 0.25) * pad
        sheen = 0.14 * np.exp(-((np.cos(angle - np.arctan2(self.L[1], self.L[0])) ** 2) * 2))
        self._paint(m, sh * (1 + tilt) + sheen, sp * 1.5, colour, shadow=0.45, off=(1.6, 2.2))

    def satin_text(self, s, x, y, size, colour, font='script', angle=0.9, anchor='mm', spacing=0.0, rot=0.0):
        self.satin(self.text_mask(s, x, y, size, font, anchor, spacing, rot), colour, angle)

    def knot(self, x, y, colour, r=None):
        """French knot: a small bead of wrapped thread"""
        r = r or self.cell * 0.42
        m = int(r + 4)
        x0, x1, y0, y1 = int(max(0, x - m)), int(min(self.W, x + m + 1)), int(max(0, y - m)), int(min(self.H, y + m + 1))
        X, Y = self.XX[y0:y1, x0:x1] - x, self.YY[y0:y1, x0:x1] - y
        d = np.hypot(X, Y) / r
        a = np.zeros((self.H, self.W), np.float32); S = np.ones_like(a); P = np.zeros_like(a)
        a[y0:y1, x0:x1] = np.clip((1 - d) * r / 0.8 + 0.5, 0, 1)
        nz = np.sqrt(np.clip(1 - d ** 2, 0, 1)); nx, ny = X / r, Y / r
        diff = np.clip(nx * self.L[0] + ny * self.L[1] + nz * self.L[2], 0, 1)
        wrap = np.sin(np.arctan2(Y, X) * 3 + d * 7)               # thread wrapped round and round
        S[y0:y1, x0:x1] = 0.45 + 0.65 * diff + 0.1 * wrap * nz
        P[y0:y1, x0:x1] = nz ** 12 * 0.2
        self._paint(a, S, P, colour, shadow=0.45)

    # ------------------------------------------------------------ charts and lettering
    def chart(self, rows, gx, gy, palette, half_keys=()):
        """classic chart: rows of characters placed with the top-left at cell (gx, gy); palette maps char -> colour.
        Characters listed in half_keys are sewn as half stitches."""
        by_key = {}
        for r, row in enumerate(rows):
            for q, ch in enumerate(row):
                if ch in palette:
                    by_key.setdefault(ch, []).append((gy + r, gx + q))
        for ch, lst in by_key.items():
            g = np.zeros((self.gh, self.gw), bool)
            for (r, q) in lst:
                if 0 <= r < self.gh and 0 <= q < self.gw: g[r, q] = True
            (self.half if ch in half_keys else self.cross)(g, palette[ch])

    def letters_grid(self, s, gx, gy, scale=1, spacing=1):
        g = np.zeros((self.gh, self.gw), bool)
        x = gx
        for ch in s.upper():
            glyph = FONT5x7.get(ch, FONT5x7[' '])
            for r, row in enumerate(glyph):
                for q, b in enumerate(row):
                    if b == '#':
                        for dy in range(scale):
                            for dx in range(scale):
                                yy, xx = gy + r * scale + dy, x + q * scale + dx
                                if 0 <= yy < self.gh and 0 <= xx < self.gw: g[yy, xx] = True
            x += (5 + spacing) * scale
        return g

    def letters(self, s, gx, gy, colour, scale=1, spacing=1):
        """cross-stitched capitals from the 5x7 sampler alphabet, top-left at cell (gx, gy)"""
        self.cross(self.letters_grid(s, gx, gy, scale, spacing), colour)

    @staticmethod
    def letters_width(s, scale=1, spacing=1):
        return len(s) * (5 + spacing) * scale - spacing * scale

    def label(self, x0, y0, x1, y1, text, colour='#fbf7ee', ink='#3d3a33', thread='#c8423a', size=30, font='typewriter'):
        """a woven label sewn on with running stitch"""
        lab = np.zeros((self.H, self.W), np.float32)
        im = Image.new('L', (self.W * 2, self.H * 2), 0)
        ImageDraw.Draw(im).rounded_rectangle((x0 * 2, y0 * 2, x1 * 2, y1 * 2), 6, fill=255)
        lab = np.asarray(im.resize((self.W, self.H), Image.BILINEAR), np.float32) / 255
        sh = blur(shift(lab, 3, 4), 4)
        self.img *= (1 - 0.4 * sh * (1 - lab))[..., None]
        twill = 0.96 + 0.04 * (((self.XX + self.YY) // 2) % 2)
        fold = 1 - 0.1 * (1 - smoothstep(0, 7, np.minimum.reduce([self.XX - x0, x1 - self.XX, self.YY - y0, y1 - self.YY])))
        face = _c(colour)[None, None, :] * (twill * fold)[..., None]
        self.img = self.img * (1 - lab[..., None]) + face * lab[..., None]
        t = self.text_mask(text, (x0 + x1) / 2, (y0 + y1) / 2, size, font, 'mm', spacing=size * 0.12)
        t = t * (0.82 + 0.18 * (((self.XX + self.YY) // 2) % 2))       # woven, not printed
        self.img = self.img * (1 - t[..., None]) + _c(ink) * t[..., None]
        ins = 9
        self.running([(x0 + ins, y0 + ins), (x1 - ins, y0 + ins), (x1 - ins, y1 - ins), (x0 + ins, y1 - ins), (x0 + ins, y0 + ins)],
                     thread, width=self.cell * 0.24, dash=0.8, gap=0.55, smooth=False)

    # ------------------------------------------------------------ output
    def composite(self, vignette=0.12):
        r = np.hypot((self.XX - self.W / 2) / self.W, (self.YY - self.H / 2) / self.H)
        img = self.img * (1 - vignette * r ** 2 * 2.2)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite(); img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
