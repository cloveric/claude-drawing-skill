"""notebook — a lab notebook lying on a desk: graph paper, graphite pencil, highlighter, red pen, sticky notes,
label-maker tape and die-cut stickers (numpy + Pillow only).

Model: every mark is made the way the real tool makes it, on real paper.
  desk       graphite blue-grey board, soft light from the upper left, fine grain, vignette;
  notebook   hard back cover, divider tabs that peek out between the pages, a stack of pages whose edges step
             down, the top page (cream graph paper: fine cyan grid, stronger every 5 squares, a header rule, a red
             double margin line, punched holes), a dog-eared corner showing the page beneath, and a wire-o binding
             (twin wire loops lit as metal tubes, casting shadows onto the page);
  paper      a per-pixel "tooth" field: graphite catches only the tops of the tooth, so light pencil is grainy
             and broken while heavy pencil fills in; liquid inks (highlighter, felt pen) ignore most of it;
  pencil     strokes are resampled, get a slow hand wobble plus a little shake, and a pressure profile (light
             touch-down, uneven middle, lift-off taper); pressure sets both width and how deep the graphite
             gets into the tooth. Ruled lines use less wobble; hatching is many short strokes clipped to a mask
             with over/under-shoot at the ends;
  highlighter a chisel-nib swipe blended with multiply: ragged long edges, a slanted start, ink pooling where the
             nib lands and stops, lengthwise streaks from the felt, a streaky tail, darker wherever passes overlap;
  red pen    felt-tip ink (multiply, slightly soaked into the paper): loops that run past a full turn and drift so
             they never close, underlines, arrows with two-stroke heads; overlaps get darker;
  paper bits sticky notes (flat adhesive strip, the rest curls up: soft corner shadows), die-cut vinyl stickers
             (white cut margin, gloss, thin shadow), label-maker tape (dark embossed tape, stress-whitened raised
             letters, scissor-cut ends), a coffee-ring stain;
  props      a hexagonal pencil lying on the desk: lit facets, a scalloped paint edge where it was sharpened, a
             wood cone with grain and a shiny graphite point, cast shadow.
Lettering uses sans / sans_bold / typewriter (CJK falls back to the CJK sans), never handwriting fonts.
Rotations are in degrees, counter-clockwise (like PIL).

    from notebook import Notebook
    nb = Notebook(1920, 1080, seed=1)
    nb.desk()
    nb.notebook(112, 100, 1796, 1018)
    nb.text('Trial log', 310, 330, 80, font='sans_bold')
    nb.rule(310, 520, 1040, 520)                         # a ruled pencil line
    nb.highlight(316, 1010, 736, 46)                     # a highlighter swipe
    nb.pen_loop(663, 737, 380, 40)                       # a red-pen loop that doesn't quite close
    f = nb.sticky(1370, 850, 380, 220, rot=1.8)          # a mint sticky note; f.pt(lx, ly) -> canvas point
    nb.text('600 um', *f.pt(28, 90), 32, rot=f.rot)
    nb.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, shift, load_font

INK, SOFT, LEAD = '#25303d', '#5b697a', '#3a4758'
RED, HI, MINT, MINTD = '#d1382d', '#f7e92b', '#abe4d0', '#1b8466'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _resample(P, step):
    P = np.asarray(P, np.float32)
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(s[-1] / step) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


def _is_cjk(ch):
    return ord(ch) >= 0x2e80


def _periodic(th, k=8, seed=0, falloff=1.2):
    """smooth random function of an angle (no seam at +-pi), roughly in [-1, 1]"""
    r = np.random.default_rng(seed)
    out = np.zeros_like(th)
    tot = 0
    for i in range(1, k + 1):
        a = 1 / i ** falloff
        out += a * np.sin(i * th + r.uniform(0, 2 * np.pi))
        tot += a
    return out / tot * 1.6


class Frame:
    """a rotated rectangle on the page (sticky note, sticker, tape). pt(lx, ly) maps a point measured from the
    rectangle's top-left corner (in its own rotated axes) to canvas coordinates; rot is the text rotation to use."""

    def __init__(self, cx, cy, w, h, rot):
        self.cx, self.cy, self.w, self.h, self.rot = cx, cy, w, h, rot

    def pt(self, lx, ly):
        u, v = lx - self.w / 2, ly - self.h / 2
        t = np.deg2rad(self.rot)
        return (self.cx + u * np.cos(t) + v * np.sin(t), self.cy - u * np.sin(t) + v * np.cos(t))


class Notebook:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.45, -0.6, 0.66)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.L = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.img = np.ones((H, W, 3), np.float32) * 0.4
        g = blur(self.rng.random((H, W)).astype(np.float32), 0.6)       # paper tooth: ~1-2 px grain ...
        m = noise2d(H, W, 4.0, 2, self._seed())                           # ... in slightly clumpy patches
        fib = np.asarray(Image.fromarray(self.rng.random((H // 2, W // 14)).astype(np.float32)).resize((W, H), Image.BILINEAR))
        t = 0.62 * (g - g.mean()) / (g.std() + 1e-6) + 0.3 * (m - m.mean()) / (m.std() + 1e-6) + 0.2 * (fib - 0.5) / 0.29
        self.tooth = np.clip(0.5 + t / 3.4, 0, 1).astype(np.float32)
        self.page = None
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ low-level compositing
    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _mul(self, sl, a, colour):
        """transparent media (graphite, ink, highlighter): multiply, so overlaps get darker"""
        self.img[sl] *= 1 - np.clip(a, 0, 1)[..., None] * (1 - _c(colour))

    def _over(self, sl, a, colour):
        """opaque media (stickers, white letters): normal blend; colour may be an (h, w, 3) array"""
        a = np.clip(a, 0, 1)[..., None]
        col = colour if isinstance(colour, np.ndarray) and colour.ndim == 3 else _c(colour)
        self.img[sl] = self.img[sl] * (1 - a) + col * a

    def _shadow(self, sl, mask, dist, soft, strength, tint='#0e1620'):
        """soft shadow of `mask` (already cropped to sl) cast away from the light"""
        d = -self.L[:2] / (np.linalg.norm(self.L[:2]) + 1e-6)
        sh = blur(shift(mask, d[0] * dist, d[1] * dist), soft) if soft > 0 else shift(mask, d[0] * dist, d[1] * dist)
        self._mul(sl, sh * strength, tint)

    def _rbox(self, cx, cy, hw, hh, rot, pad):
        """bounding slices for a rotated rectangle and the local (u, v) coords of every pixel in it"""
        R = np.hypot(hw, hh) + pad
        sl = self._box(cx - R, cy - R, cx + R, cy + R)
        if sl is None: return None, None, None
        t = np.deg2rad(rot)
        dx, dy = self.XX[sl] - cx, self.YY[sl] - cy
        return sl, dx * np.cos(t) - dy * np.sin(t), dx * np.sin(t) + dy * np.cos(t)

    @staticmethod
    def _sdf_rrect(u, v, hw, hh, r):
        qx, qy = np.abs(u) - (hw - r), np.abs(v) - (hh - r)
        return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r

    # ------------------------------------------------------------ stroke rasteriser (pencil, pen)
    def _raster(self, strokes, ss=3):
        """strokes: [(P (n,2), width (n,), value (n,) 0..1)] -> (mask, slices); drawn at ss x then box-filtered"""
        allp = np.concatenate([s[0] for s in strokes])
        pad = max(float(s[1].max()) for s in strokes) + 3
        sl = self._box(allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        if sl is None: return None, None
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (bw * ss, bh * ss), 0)
        d = ImageDraw.Draw(im)
        for P, w, v in strokes:
            Q = (P - np.array([x0, y0], np.float32)) * ss
            n = len(Q)
            if n == 1:
                r = w[0] * ss / 2
                d.ellipse([Q[0, 0] - r, Q[0, 1] - r, Q[0, 0] + r, Q[0, 1] + r], fill=int(255 * v[0]))
                continue
            for i in range(0, n - 1, 3):
                j = min(n - 1, i + 3)
                ww = float(w[i:j + 1].mean()) * ss
                vv = int(round(255 * float(np.clip(v[i:j + 1].mean(), 0, 1))))
                r = ww / 2
                d.ellipse([Q[i, 0] - r, Q[i, 1] - r, Q[i, 0] + r, Q[i, 1] + r], fill=vv)
                d.line([(float(q[0]), float(q[1])) for q in Q[i:j + 1]], fill=vv, width=max(1, int(round(ww))))
            r = w[-1] * ss / 2
            d.ellipse([Q[-1, 0] - r, Q[-1, 1] - r, Q[-1, 0] + r, Q[-1, 1] + r], fill=int(255 * np.clip(v[-1], 0, 1)))
        m = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        return m, sl

    def _prep(self, pts, width, pressure, jitter, smooth=True, taper=(14, 24), step=1.5):
        """resample a hand stroke, add wobble + shake and a pressure profile -> (P, widths, pressures)"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 10)
        P = _resample(P, step)
        n = len(P)
        if n < 2: return P, np.array([width], np.float32), np.array([pressure], np.float32)
        tg = np.gradient(P, axis=0)
        tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
        s = self._seed()
        wob = fbm1d(n, max(4, 110 / step), 3, s) * jitter + fbm1d(n, max(2, 9 / step), 2, s + 1) * jitter * 0.22
        P = P + nrm * wob[:, None]
        L = n * step
        t = np.linspace(0, 1, n)
        env = 0.4 + 0.6 * smoothstep(0, min(0.3, taper[0] / L), t) * smoothstep(0, min(0.35, taper[1] / L), 1 - t)
        flow = 1 + 0.16 * fbm1d(n, max(4, 70 / step), 2, s + 2)
        press = np.clip(pressure * env * flow, 0.02, 1).astype(np.float32)
        w = (width * (0.72 + 0.28 * press / max(pressure, 1e-3))).astype(np.float32)
        return P, w, press

    def _graphite(self, m, sl, colour=LEAD, strength=0.9):
        """graphite deposit: light pressure only catches the tops of the paper tooth, heavy pressure fills in;
        even a heavy line keeps some grain (the valleys stay paler)"""
        t = self.tooth[sl]
        thr = 1.0 - 1.3 * m
        dep = smoothstep(thr - 0.2, thr + 0.2, t)
        a = smoothstep(0.0, 0.1, m) * (0.22 + 0.78 * np.clip(m, 0, 1)) * (0.38 + 0.62 * dep) * (0.86 + 0.14 * t) * strength
        self._mul(sl, a, colour)

    # ------------------------------------------------------------ pencil
    def pencils(self, strokes, width=2.4, pressure=0.7, jitter=0.8, colour=LEAD, smooth=True, strength=0.88):
        """many graphite strokes in one pass (a list of point lists); overlapping strokes of one call don't stack"""
        prepared = [self._prep(p, width, pressure, jitter, smooth) for p in strokes if len(p) >= 1]
        prepared = [p for p in prepared if len(p[0])]
        if not prepared: return
        m, sl = self._raster(prepared)
        if sl is not None: self._graphite(m, sl, colour, strength)

    def pencil(self, pts, width=2.4, pressure=0.7, jitter=0.8, colour=LEAD, smooth=True, strength=0.88):
        """one freehand graphite stroke through `pts` (Catmull-Rom smoothed unless smooth=False)"""
        self.pencils([pts], width, pressure, jitter, colour, smooth, strength)

    def rule(self, x0, y0, x1, y1, width=2.0, pressure=0.6, colour=LEAD, overshoot=4):
        """a line ruled with a straight-edge: straight, tiny wobble, uneven pressure, ends not exactly on target"""
        r = self.rng
        d = np.array([x1 - x0, y1 - y0], np.float32); d /= np.linalg.norm(d) + 1e-6
        a = np.array([x0, y0], np.float32) - d * r.uniform(-overshoot * 0.5, overshoot)
        b = np.array([x1, y1], np.float32) + d * r.uniform(-overshoot * 0.5, overshoot)
        self.pencil([a, b], width, pressure, 0.3, colour, smooth=False)

    def hatch(self, mask, angle=45, spacing=7, pressure=0.5, width=1.5, jitter=0.4, colour=LEAD, overshoot=3):
        """pencil hatching inside a mask: parallel short strokes, each slightly bowed, ends over/under-shooting"""
        ys, xs = np.nonzero(mask > 0.5)
        if len(xs) == 0: return
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), -np.sin(a)], np.float32)
        nv = np.array([np.sin(a), np.cos(a)], np.float32)
        cx, cy = xs.mean(), ys.mean()
        corners = np.array([[xs.min(), ys.min()], [xs.max(), ys.min()], [xs.min(), ys.max()], [xs.max(), ys.max()]], np.float32) - [cx, cy]
        on, od = corners @ nv, corners @ d
        r = self.rng
        strokes = []
        o = on.min()
        while o < on.max():
            ts = np.arange(od.min() - 2, od.max() + 2, 1.0)
            px = cx + nv[0] * o + d[0] * ts; py = cy + nv[1] * o + d[1] * ts
            ix, iy = np.round(px).astype(int), np.round(py).astype(int)
            ok = (ix >= 0) & (iy >= 0) & (ix < self.W) & (iy < self.H)
            inside = np.zeros(len(ts), bool)
            inside[ok] = mask[iy[ok], ix[ok]] > 0.5
            edges = np.diff(np.concatenate([[0], inside.astype(int), [0]]))
            for s0, s1 in zip(np.nonzero(edges == 1)[0], np.nonzero(edges == -1)[0]):
                if s1 - s0 < 4: continue
                t0 = ts[s0] - r.uniform(-overshoot * 0.6, overshoot)
                t1 = ts[s1 - 1] + r.uniform(-overshoot * 0.8, overshoot * 1.3)
                p0 = np.array([cx, cy]) + nv * o + d * t0
                p1 = np.array([cx, cy]) + nv * o + d * t1
                mid = (p0 + p1) / 2 + nv * r.uniform(-1, 1) * (t1 - t0) * 0.012
                strokes.append([p0, mid, p1])
            o += spacing * r.uniform(0.85, 1.15)
        self.pencils(strokes, width, pressure, jitter, colour, smooth=True)

    def checkbox(self, x, y, size=24, checked=True, pressure=0.7, check_colour=LEAD):
        """a pencil box (four ruled sides that overshoot at the corners) and an optional tick"""
        s = size
        for p0, p1 in [((x, y), (x + s, y)), ((x + s, y), (x + s, y + s)), ((x + s, y + s), (x, y + s)), ((x, y + s), (x, y))]:
            self.rule(p0[0], p0[1], p1[0], p1[1], 1.9, pressure * 0.85, overshoot=2.5)
        if checked:
            self.pencil([(x + s * 0.18, y + s * 0.5), (x + s * 0.42, y + s * 0.8), (x + s * 1.05, y - s * 0.3)], 2.8, 0.95, 0.5,
                        check_colour, strength=0.95)

    def arrowhead(self, tip, direction_deg, size=14, width=2.2, pressure=0.75, colour=LEAD):
        """two short pencil flicks forming an arrow head at `tip` pointing along direction_deg (screen, clockwise from +x)"""
        a = np.deg2rad(direction_deg)
        for side in (1, -1):
            b = a + side * np.deg2rad(152)
            self.pencil([(tip[0] + np.cos(b) * size, tip[1] + np.sin(b) * size), tip], width, pressure, 0.3, colour, smooth=False)

    def axes(self, x0, y0, x1, y1, xlim, ylim, xticks, yticks, xlabels=None, ylabels=None, size=18, colour=LEAD,
             label_colour=SOFT, font='typewriter', tick=9):
        """pencil-ruled chart axes (origin at bottom-left x0, y1) with ticks and typed labels -> to_px(xv, yv)"""
        def to_px(xv, yv):
            return (x0 + (xv - xlim[0]) / (xlim[1] - xlim[0]) * (x1 - x0), y1 - (yv - ylim[0]) / (ylim[1] - ylim[0]) * (y1 - y0))
        self.rule(x0 - 6, y1, x1 + 22, y1, 2.3, 0.8, colour, overshoot=2)
        self.rule(x0, y1 + 6, x0, y0 - 22, 2.3, 0.8, colour, overshoot=2)
        self.arrowhead((x1 + 24, y1), 0, 13, colour=colour)
        self.arrowhead((x0, y0 - 24), -90, 13, colour=colour)
        tk = []
        for i, xv in enumerate(xticks):
            px, _ = to_px(xv, ylim[0])
            tk.append([(px, y1 - tick * 0.4), (px, y1 + tick)])
            if xlabels: self.text(xlabels[i], px, y1 + tick + size * 1.35, size, label_colour, font, 'ms', medium='typed')
        for i, yv in enumerate(yticks):
            _, py = to_px(xlim[0], yv)
            tk.append([(x0 - tick, py), (x0 + tick * 0.4, py)])
            if ylabels: self.text(ylabels[i], x0 - tick - 10, py, size, label_colour, font, 'rm', medium='typed')
        self.pencils(tk, 2.0, 0.7, 0.2, colour, smooth=False)
        return to_px

    # ------------------------------------------------------------ highlighter
    def highlight(self, x0, x1, y, h=40, colour=HI, tilt=-3, alpha=0.8, slant=0.35):
        """a fluorescent chisel-nib swipe from x0 to x1 (centre line y; the end sits `tilt` px lower/higher),
        multiplied onto the page: ragged edges, pooled ink where the nib lands and stops, felt streaks,
        a streaky tail; overlapping swipes get darker."""
        L = float(np.hypot(x1 - x0, tilt)); ang = np.arctan2(tilt, x1 - x0)
        pad = h + abs(tilt) + 24
        sl = self._box(min(x0, x1) - 24, y - pad, max(x0, x1) + 24, y + pad)
        if sl is None: return
        X, Y = self.XX[sl] - x0, self.YY[sl] - y
        u = X * np.cos(ang) + Y * np.sin(ang)
        v = -X * np.sin(ang) + Y * np.cos(ang)
        s = self._seed()
        nU = int(L + 60); nV = int(h * 2 + 20)
        ui = np.clip(u + 30, 0, nU - 1); vi = np.clip(v + h + 10, 0, nV - 1)
        top = np.interp(ui, np.arange(nU), fbm1d(nU, 45, 3, s) * 2.4 + fbm1d(nU, 6, 2, s + 1) * 0.7)
        bot = np.interp(ui, np.arange(nU), fbm1d(nU, 45, 3, s + 2) * 2.4 + fbm1d(nU, 6, 2, s + 3) * 0.7)
        vt, vb = -h / 2 + top, h / 2 + bot
        us = (v / h) * h * slant                                        # chisel start: a slanted edge
        ragged = np.interp(vi, np.arange(nV), fbm1d(nV, 5, 2, s + 4))
        ue = L + (v / h) * h * slant * 0.6 + ragged * 7
        sm = lambda q: np.clip(q / 1.4 + 0.5, 0, 1)
        cov = sm(v - vt) * sm(vb - v) * sm(u - us) * sm(ue - u)
        streak = np.interp(vi, np.arange(nV), fbm1d(nV, 3, 2, s + 5))
        flow = np.interp(ui, np.arange(nU), fbm1d(nU, 120, 2, s + 6))
        dens = (0.9 + 0.09 * streak) * (1 + 0.04 * flow)
        dens *= 1 + 0.28 * np.exp(-((u - us - 5) / 7) ** 2) + 0.16 * np.exp(-((u - ue + 6) / 6) ** 2)
        dens *= 1 + 0.12 * (np.exp(-((v - vt) / 2.2) ** 2) + np.exp(-((vb - v) / 2.2) ** 2))
        tail = smoothstep(ue - 46, ue - 4, u)                           # the nib runs dry: rows drop out near the end
        keep = np.interp(vi, np.arange(nV), (fbm1d(nV, 2.5, 2, s + 7) + 1) / 2)
        cov *= 1 - tail * (1 - smoothstep(tail * 0.8 - 0.12, tail * 0.8 + 0.12, keep)) * 0.85
        a = cov * dens * alpha * (0.97 + 0.03 * self.tooth[sl])
        self._mul(sl, a, colour)

    # ------------------------------------------------------------ red pen
    def pen(self, pts, width=4.0, colour=RED, alpha=0.9, jitter=0.7, smooth=True):
        """a felt-tip stroke: even, slightly soaked-in ink, a blob where the pen touched down"""
        P, w, press = self._prep(pts, width, 1.0, jitter, smooth, taper=(6, 10))
        w = width * (0.86 + 0.14 * press)
        w[:4] *= 1.12
        m, sl = self._raster([(P, w.astype(np.float32), np.ones(len(P), np.float32))])
        if sl is None: return
        m = blur(m, 0.5)
        self._mul(sl, m * alpha * (0.93 + 0.07 * self.tooth[sl]), colour)

    def pen_loop(self, cx, cy, rx, ry, rot=-1.5, turns=1.12, a0=196, width=4.2, colour=RED):
        """a hand-drawn red loop: a bit more than one turn, drifting outward so the ends pass each other"""
        N = 160
        t = np.linspace(0, 1, N)
        a = np.deg2rad(a0 + t * 360 * turns)
        s = self._seed()
        k = 1 + fbm1d(N, 30, 2, s) * 0.02 + (t - 0.5) * 0.07
        x, y = rx * k * np.cos(a), ry * (k + (t - 0.5) * 0.05) * np.sin(a)
        r = np.deg2rad(-rot)
        P = np.stack([cx + x * np.cos(r) - y * np.sin(r), cy + x * np.sin(r) + y * np.cos(r)], 1)
        cut = int(N * 0.56)
        self.pen(P[:cut + 1], width, colour, jitter=0.6, smooth=False)   # two strokes: the overlap stacks darker
        self.pen(P[cut:], width * 0.95, colour, jitter=0.6, smooth=False)

    def pen_arrow(self, pts, width=4.0, head=20, colour=RED):
        """a curved red arrow through control points, with a two-stroke head at the last point"""
        P = spline(np.asarray(pts, np.float32), 12)
        self.pen(P, width, colour, smooth=False)
        d = P[-1] - P[-4]
        a = np.arctan2(d[1], d[0])
        for side in (1, -1):
            b = a + side * np.deg2rad(150)
            self.pen([P[-1] + np.array([np.cos(b), np.sin(b)]) * head, P[-1]], width * 0.95, colour, jitter=0.3, smooth=False)

    def pen_underline(self, x0, x1, y, width=4.0, colour=RED, double=False, sag=2.0):
        r = self.rng
        self.pen([(x0, y + r.uniform(-1, 1)), ((x0 + x1) / 2, y + sag), (x1, y - r.uniform(0, 3))], width, colour)
        if double:
            self.pen([(x0 + 14, y + 13), ((x0 + x1) / 2, y + 13 + sag), (x1 - 24, y + 11)], width * 0.75, colour)

    # ------------------------------------------------------------ lettering
    def _font(self, style, size, s):
        if style in ('sans', 'sans_bold', 'typewriter', 'condensed', 'rounded') and any(_is_cjk(ch) for ch in s):
            return load_font('cjk_sans', size)
        return load_font(style, size)

    def _runs(self, s, style):
        """split into runs of CJK / non-CJK so Latin keeps its own font next to Chinese"""
        runs = []
        for ch in s:
            k = _is_cjk(ch)
            if runs and runs[-1][1] == k: runs[-1][0] += ch
            else: runs.append([ch, k])
        return [(t, 'cjk_sans' if k else style) for t, k in runs]

    def _tmask(self, s, x, y, size, style='sans_bold', anchor='ls', spacing=0.0, rot=0.0, weight=0, typed=False, ss=2):
        """text -> (mask, slices); mixed CJK/Latin, faux-bold `weight` (px), letter `spacing`, rotation about (x, y).
        typed=True: every character gets its own ink density and a small baseline wobble (typewriter / label printer)"""
        runs = self._runs(s, style) if style not in ('cjk', 'cjk_sans') else [(s, style)]
        fonts = {st: load_font(st, size * ss) for _, st in runs}
        items = []                                                      # (char or run, font, advance)
        for t, st in runs:
            f = fonts[st]
            if typed or spacing:
                for ch in t: items.append((ch, f, f.getlength(ch) + spacing * ss))
            else:
                items.append((t, f, f.getlength(t)))
        total = sum(a for _, _, a in items) - (spacing * ss if (typed or spacing) else 0)
        latin = [st for _, st in runs if st not in ('cjk', 'cjk_sans')]
        f0 = fonts[latin[0]] if latin else fonts[runs[0][1]]
        capH = -f0.getbbox('H', anchor='ls')[1]
        desc = f0.getbbox('g', anchor='ls')[3]
        dyb = {'s': 0, 'm': capH / 2, 'a': capH * 1.12, 't': capH * 1.12, 'd': -desc, 'b': -desc}.get(anchor[1], 0)
        R = int(np.hypot(total / ss, size * 1.4) + weight + 8)
        ox, oy = int(np.floor(x)) - R, int(np.floor(y)) - R              # local image origin (may be off-canvas)
        sl = self._box(ox, oy, ox + 2 * R, oy + 2 * R)
        if sl is None: return None, None
        im = Image.new('L', (2 * R * ss, 2 * R * ss), 0)
        d = ImageDraw.Draw(im)
        cx = (x - ox) * ss - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        by = (y - oy) * ss + dyb
        r = self.rng
        for t, f, adv in items:
            if typed:
                fill = int(255 * r.uniform(0.82, 1.0)); jy = r.normal(0, 0.45) * ss; jx = r.normal(0, 0.25) * ss
            else:
                fill, jy, jx = 255, 0, 0
            d.text((cx + jx, by + jy), t, font=f, fill=fill, anchor='ls', stroke_width=int(round(weight * ss)), stroke_fill=fill)
            cx += adv
        if rot:
            im = im.rotate(rot, resample=Image.BICUBIC, center=((x - ox) * ss, (y - oy) * ss))
        im = im.resize((2 * R, 2 * R), Image.BOX)
        m = np.asarray(im, np.float32) / 255
        ys0, xs0 = sl[0].start - oy, sl[1].start - ox
        m = m[ys0:ys0 + (sl[0].stop - sl[0].start), xs0:xs0 + (sl[1].stop - sl[1].start)]
        return m, sl

    def text_width(self, s, size, font='sans_bold', spacing=0.0):
        w = 0.0
        for t, st in self._runs(s, font):
            f = load_font(st, size)
            w += sum(f.getlength(ch) + spacing for ch in t) if spacing else f.getlength(t)
        return w - (spacing if spacing else 0)

    def text(self, s, x, y, size, colour=INK, font='sans_bold', anchor='ls', rot=0.0, spacing=0.0, weight=0,
             medium='ink', alpha=0.95):
        """lettering on the page. medium: 'ink' (fine-liner, multiply), 'print' (pre-printed form text),
        'typed' (typewriter / label printer: uneven strikes), 'pencil' (graphite grain), 'opaque' (white on stickers)"""
        m, sl = self._tmask(s, x, y, size, font, anchor, spacing, rot, weight, typed=(medium == 'typed'))
        if sl is None: return
        if medium == 'pencil':
            self._graphite(m * alpha, sl, colour, 0.92)
        elif medium == 'opaque':
            self._over(sl, m * alpha, colour)
        elif medium == 'typed':
            m = blur(m, 0.35)
            self._mul(sl, m * alpha * (0.84 + 0.16 * self.tooth[sl]), colour)
        elif medium == 'print':
            self._mul(sl, m * alpha * (0.95 + 0.05 * self.tooth[sl]), colour)
        else:
            m = np.maximum(m, blur(m, 0.6) * 0.9)
            self._mul(sl, m * alpha * (0.9 + 0.1 * self.tooth[sl]), colour)

    # ------------------------------------------------------------ desk and notebook
    def desk(self, colour='#56616c', light='#77838e', dark='#3a434d'):
        """graphite blue-grey desk: light pooled at the upper left, fine grain, faint board fibres"""
        r = np.hypot((self.XX - 0.28 * self.W) / (0.95 * self.W), (self.YY - 0.16 * self.H) / (0.85 * self.H))
        t1 = smoothstep(0.0, 0.55, r)[..., None]; t2 = smoothstep(0.5, 1.15, r)[..., None]
        base = _c(light) * (1 - t1) + _c(colour) * t1
        base = base * (1 - t2) + _c(dark) * t2
        grain = noise2d(self.H, self.W, 1.6, 2, self._seed())
        fib = np.asarray(Image.fromarray(self.rng.random((self.H // 3, self.W // 90)).astype(np.float32)).resize((self.W, self.H), Image.BICUBIC))
        mott = noise2d(self.H, self.W, 260, 3, self._seed())
        self.img = base * (1 + 0.05 * (grain - 0.5) + 0.03 * (fib - 0.5) + 0.05 * (mott - 0.5))[..., None]

    def _grid(self, sl, gx0, gy0, grid, major):
        X, Y = self.XX[sl] - gx0, self.YY[sl] - gy0
        def lines(c, g, w):
            d = np.abs(((c + g / 2) % g) - g / 2)
            return np.clip(w / 2 - d + 0.5, 0, 1)
        minor = np.maximum(lines(X, grid, 1.0), lines(Y, grid, 1.0))
        maj = np.maximum(lines(X, grid * major, 1.5), lines(Y, grid * major, 1.5))
        return minor, maj

    def notebook(self, x0, y0, x1, y1, tabs=((MINT, 250), ('#efe596', 372), ('#e9a79f', 494)), stack=5, ear=58,
                 margin=150, header=48, grid=24, major=5, cover='#2c3846', paper='#f8f8f4', grid_colour='#3f8fb8',
                 margin_colour='#d6483e', holes=True):
        """a top-bound wire-o notebook lying on the desk; the top page spans (x0, y0)-(x1, y1)"""
        self.page = (x0, y0, x1, y1)
        self.page_margin = x0 + margin
        self.page_header = y0 + header
        s = self._seed()
        # hard back cover + its shadow on the desk
        sl, u, v = self._rbox((x0 + x1) / 2 + 1, (y0 + y1) / 2 + 10, (x1 - x0) / 2 + 17, (y1 - y0) / 2 + 12, 0, 120)
        cm = np.clip(0.5 - self._sdf_rrect(u, v, (x1 - x0) / 2 + 17, (y1 - y0) / 2 + 12, 14), 0, 1)
        self._shadow(sl, cm, 44, 40, 0.5)
        self._shadow(sl, cm, 12, 10, 0.35)
        g = np.clip((u / (x1 - x0) + v / (y1 - y0)) + 0.5, 0, 1)[..., None]
        cc = _c('#3b4858') * (1 - g) + _c(cover) * g
        cc = cc * (1 + 0.035 * (self.tooth[sl] - 0.5))[..., None]
        rim = np.clip(cm - shift(cm, 2, 2), 0, 1)
        self._over(sl, cm, cc)
        self.img[sl] += (rim * 0.12)[..., None]
        # divider tabs, peeking out on the right between the pages
        for i, (tc, ty) in enumerate(tabs or []):
            tsl, tu, tv = self._rbox(x1 + 6, ty + 52, 44, 52, 0, 20)
            tm = np.clip(0.5 - self._sdf_rrect(tu, tv, 44, 52, 11), 0, 1) * (tu > -40)
            self._shadow(tsl, tm, 4, 3, 0.35)
            shade = 1 - 0.08 * smoothstep(-44, 0, -tu) + 0.1 * np.exp(-((tu - 14) / 14) ** 2) - 0.06 * smoothstep(30, 44, tu)
            tcol = _c(tc)[None, None, :] * (shade * (0.97 + 0.04 * self.tooth[tsl]))[..., None]
            self._over(tsl, tm, tcol)
        # the stack of pages under the top one: each edge steps down a little
        for i in range(stack, 0, -1):
            dx, dy = i * 0.7, i * 3.0
            psl, pu, pv = self._rbox((x0 + x1) / 2 + dx, (y0 + y1) / 2 + dy, (x1 - x0) / 2, (y1 - y0) / 2, 0, 6)
            pm = np.clip(0.5 - self._sdf_rrect(pu, pv, (x1 - x0) / 2, (y1 - y0) / 2, 5), 0, 1)
            self._shadow(psl, pm, 1.2, 1.0, 0.3)
            shade = (0.955 - 0.018 * i) * (0.985 + 0.02 * self.tooth[psl])
            col = _c(paper)[None, None, :] * shade[..., None]
            if i == 1:                                                   # the page right under shows in the dog-ear
                mi, ma = self._grid(psl, x0 + dx, y0 + header + dy, grid, major)
                col = col * (1 - (np.maximum(mi * 0.2, ma * 0.36))[..., None] * (1 - _c(grid_colour)))
            self._over(psl, pm, col)
        # the top page
        psl = self._box(x0 - 2, y0 - 2, x1 + 2, y1 + 2)
        X, Y = self.XX[psl], self.YY[psl]
        pm = np.clip(0.5 - self._sdf_rrect(X - (x0 + x1) / 2, Y - (y0 + y1) / 2, (x1 - x0) / 2, (y1 - y0) / 2, 5), 0, 1)
        cut = ((X - (x1 - ear)) + (Y - (y1 - ear)) - ear) / np.sqrt(2)          # > 0 beyond the fold line
        pm = pm * np.clip(0.5 - cut, 0, 1)
        self._shadow(psl, pm, 1.5, 1.2, 0.25)
        glow = 0.045 * np.exp(-(((X - x0 - 0.22 * (x1 - x0)) / (0.75 * (x1 - x0))) ** 2 + ((Y - y0 - 0.1 * (y1 - y0)) / (0.7 * (y1 - y0))) ** 2))
        fall = 0.06 * np.clip(((X - x0) / (x1 - x0) * 0.35 + (Y - y0) / (y1 - y0) * 0.65 - 0.4) / 0.6, 0, 1)
        edge = np.minimum.reduce([X - x0, x1 - X, Y - y0, y1 - Y])
        inset = 0.06 * (1 - smoothstep(0, 34, edge))
        curl = 0.035 * np.exp(-np.clip(Y - y0, 0, None) / 22)
        light = 1 + glow - fall - inset - curl + 0.03 * (self.tooth[psl] - 0.5)
        col = _c(paper)[None, None, :] * light[..., None]
        mi, ma = self._grid(psl, x0, y0 + header, grid, major)
        ga = np.maximum(mi * 0.2, ma * 0.36) * (Y > y0 + header + 0.5) * (0.8 + 0.2 * self.tooth[psl])
        col = col * (1 - ga[..., None] * (1 - _c(grid_colour)))
        hl = np.clip(1.1 - np.abs(Y - (y0 + header)) + 0.5, 0, 1) * 0.42
        col = col * (1 - hl[..., None] * (1 - _c(grid_colour)))
        mx = x0 + margin
        mg = (np.clip(1.2 - np.abs(X - mx) + 0.5, 0, 1) * 0.62 + np.clip(0.5 - np.abs(X - mx - 6) + 0.5, 0, 1) * 0.35) * (Y > y0 + header)
        col = col * (1 - (mg * (0.85 + 0.15 * self.tooth[psl]))[..., None] * (1 - _c(margin_colour)))
        self._over(psl, pm, col)
        # punched holes (the dark cover shows through)
        self.holes = []
        if holes:
            n = int((x1 - x0 - 76) / 39.6) + 1
            xs = x0 + 38 + np.arange(n) * (x1 - x0 - 76) / (n - 1)
            for hx in xs:
                hsl, hu, hv = self._rbox(hx, y0 + 21.5, 7, 9.5, 0, 3)
                hm = np.clip(0.5 - self._sdf_rrect(hu, hv, 7, 9.5, 5), 0, 1)
                hc = _c('#232c36')[None, None, :] * (0.75 + 0.35 * smoothstep(-9.5, 4, hv))[..., None]
                self._over(hsl, hm, hc)
                self.holes.append(hx)
        # dog-ear: the corner folded back over the page (its back shows a faint mirror of the grid)
        fsl = self._box(x1 - ear - 6, y1 - ear - 6, x1 + 6, y1 + 6)
        X, Y = self.XX[fsl], self.YY[fsl]
        du, dv = X - (x1 - ear), Y - (y1 - ear)
        fm = np.clip(0.5 - (du + dv - ear) / np.sqrt(2), 0, 1) * np.clip(du + 0.5, 0, 1) * np.clip(dv + 0.5, 0, 1)
        dist_fold = (ear - du - dv) / np.sqrt(2)
        under = np.clip(0.5 + (du + dv - ear) / np.sqrt(2), 0, 1) * np.clip(x1 - X, 0, 1) * np.clip(y1 - Y, 0, 1)
        self._mul(fsl, under * 0.35 * np.exp(-np.clip(-dist_fold, 0, None) / 10), '#0e1620')
        self._shadow(fsl, fm, 2.5, 2.2, 0.28)
        ft = np.clip(dist_fold / (ear / np.sqrt(2)), 0, 1)
        fcol = _c('#f4f4ef')[None, None, :] * (1.02 - 0.09 * ft + 0.05 * np.exp(-(dist_fold / 5) ** 2))[..., None]
        mi, ma = self._grid(fsl, x1 + 3, y1 + 3, grid, major)
        fcol = fcol * (1 - (np.maximum(mi, ma) * 0.05)[..., None])
        self._over(fsl, fm, fcol)

    def binding(self, colour='#b9c2cb', r=2.2):
        """wire-o twin loops through every punched hole, lit as metal tubes, with shadows on the page"""
        if not self.page: return
        x0, y0, x1, y1 = self.page
        paths = []
        for hx in self.holes:
            for o in (-3.4, 3.4):
                p0 = np.array([hx + o, y0 + 25]); p3 = np.array([hx + o * 0.15, y0 - 28])
                c1 = np.array([hx + o, y0 - 6]); c2 = np.array([hx + o * 0.7, y0 - 22])
                t = np.linspace(0, 1, 26)[:, None]
                paths.append(((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * c1 + 3 * (1 - t) * t * t * c2 + t ** 3 * p3)
        sl = self._box(x0 - 20, y0 - 40, x1 + 20, y0 + 40)
        sh = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), np.float32)
        im = Image.new('L', (sh.shape[1] * 2, sh.shape[0] * 2), 0); d = ImageDraw.Draw(im)
        for P in paths:
            Q = (P - [sl[1].start, sl[0].start]) * 2
            d.line([tuple(q) for q in Q], fill=255, width=int(r * 2 * 2 + 2))
        sh = np.asarray(im.resize((sh.shape[1], sh.shape[0]), Image.BOX), np.float32) / 255
        self._shadow(sl, sh, 8, 2.8, 0.5)
        for P in paths:
            self._tube(P, r, colour, deep=(y0 + 12, y0 + 30))

    def _tube(self, P, r, colour, spec=0.9, shine=36, deep=None):
        """a round metal wire along polyline P, shaded from its cross-section normals"""
        P = np.asarray(P, np.float32)
        sl = self._box(P[:, 0].min() - r - 2, P[:, 1].min() - r - 2, P[:, 0].max() + r + 2, P[:, 1].max() + r + 2)
        if sl is None: return
        X, Y = self.XX[sl], self.YY[sl]
        best = np.full(X.shape, 1e9, np.float32); vx = np.zeros_like(X); vy = np.zeros_like(X); tt = np.zeros_like(X)
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]
            ab = b - a; l2 = float(ab @ ab) + 1e-6
            t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / l2, 0, 1)
            qx, qy = X - (a[0] + t * ab[0]), Y - (a[1] + t * ab[1])
            dd = qx * qx + qy * qy
            k = dd < best
            best = np.where(k, dd, best); vx = np.where(k, qx, vx); vy = np.where(k, qy, vy); tt = np.where(k, (i + t) / (len(P) - 1), tt)
        dist = np.sqrt(best)
        cov = np.clip(r - dist + 0.5, 0, 1)
        nx, ny = np.clip(vx / r, -1, 1), np.clip(vy / r, -1, 1)
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        dif = np.clip(nx * self.L[0] + ny * self.L[1] + nz * self.L[2], 0, 1)
        Hh = self.L + np.array([0, 0, 1], np.float32); Hh /= np.linalg.norm(Hh)
        sp = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** shine
        col = _c(colour)[None, None, :] * (0.28 + 0.8 * dif)[..., None] + (sp * spec)[..., None]
        col = col * (0.75 + 0.25 * nz)[..., None]
        if deep is not None:                                             # inside the hole the wire is in shadow
            yy = Y
            col = col * (1 - 0.55 * smoothstep(deep[0], deep[1], yy))[..., None]
        col = col * (1 - 0.35 * smoothstep(0.85, 1.0, tt))[..., None]     # turning down behind the page edge
        self._over(sl, cov, np.clip(col, 0, 1))

    # ------------------------------------------------------------ paper bits
    def sticky(self, cx, cy, w, h, rot=0.0, colour=MINT, curl=1.0):
        """a sticky note: the adhesive strip lies flat, the rest curls up, so the shadow grows toward the bottom
        corners. Returns a Frame to write on."""
        sl, u, v = self._rbox(cx, cy, w / 2, h / 2, rot, 40)
        if sl is None: return Frame(cx, cy, w, h, rot)
        m = np.clip(0.5 - self._sdf_rrect(u, v, w / 2, h / 2, 1.5), 0, 1)
        vn = (v + h / 2) / h
        lift = smoothstep(0.22, 1.0, vn) ** 1.6 * (0.55 + 0.45 * (np.abs(u) / (w / 2)) ** 2) * curl
        self._shadow(sl, m, 1.6, 1.4, 0.3)
        self._shadow(sl, m * lift, 9 * curl + 2, 8, 0.42)
        col = _c(colour)
        shade = 1 + 0.035 * (1 - smoothstep(0, 0.22, vn)) - 0.07 * smoothstep(0.35, 1.0, vn) + 0.04 * np.clip(1 - (u / w + vn) * 1.4, 0, 1)
        shade = shade + 0.025 * (self.tooth[sl] - 0.5) + 0.05 * np.exp(-((v - h / 2 + 1.5) / 1.4) ** 2)
        self._over(sl, m, col[None, None, :] * shade[..., None])
        return Frame(cx, cy, w, h, rot)

    def sticker(self, cx, cy, w, h, rot=0.0, colour=RED, radius=None, border=7, lines=(), shape='rrect'):
        """a die-cut vinyl sticker: printed face, white cut margin, gloss, thin shadow.
        lines: [(text, lx, ly, size, font, colour, anchor)] in the sticker's own frame (from its top-left)."""
        hw, hh = w / 2 + border, h / 2 + border
        sl, u, v = self._rbox(cx, cy, hw, hh, rot, 30)
        if sl is None: return Frame(cx, cy, w, h, rot)
        if shape == 'circle':
            d_in = np.hypot(u, v) - w / 2
        else:
            rr = min(w, h) / 2 if radius is None else radius
            d_in = self._sdf_rrect(u, v, w / 2, h / 2, rr)
        outer = np.clip(0.5 - (d_in - border), 0, 1)
        inner = np.clip(0.5 - d_in, 0, 1)
        self._shadow(sl, outer, 1.5, 1.3, 0.35)
        self._shadow(sl, outer, 7, 8, 0.22)
        vinyl = _c('#fdfdfb')[None, None, :] * (0.97 + 0.03 * self.tooth[sl])[..., None]
        self._over(sl, outer, vinyl)
        face = _c(colour)[None, None, :] * (1 + 0.02 * (self.tooth[sl] - 0.5))[..., None]
        self._over(sl, inner, face)
        f = Frame(cx, cy, w, h, rot)
        for ln in lines:
            s, lx, ly, size, font, col = ln[:6]
            anchor = ln[6] if len(ln) > 6 else 'ms'
            px, py = f.pt(lx, ly)
            self.text(s, px, py, size, col, font, anchor, rot=rot, medium='opaque', alpha=1.0)
        gl = np.clip(1 - ((u + hw) / (2 * hw) * 0.6 + (v + hh) / (2 * hh)) * 1.1, 0, 1) ** 1.5 * 0.3
        rim = np.clip(outer - np.clip(0.5 - (d_in - border + 1.6), 0, 1), 0, 1)
        side = np.clip(-(u * self.L[0] + v * self.L[1]) / (np.hypot(u, v) + 1e-3), -1, 1)
        self.img[sl] = np.clip(self.img[sl] + (outer * gl)[..., None] - (rim * 0.12 * (1 - side))[..., None], 0, 1)
        return f

    def label_tape(self, s, x, y, size=24, rot=-0.8, colour='#27313c', letters='#e8edf1', anchor='l', spacing=None):
        """label-maker tape: dark embossed plastic, scissor-cut ends, stress-whitened raised letters.
        (x, y): left end (anchor 'l') or centre (anchor 'm') of the tape's centre line. Returns a Frame."""
        sp = size * 0.22 if spacing is None else spacing
        tw = self.text_width(s, size, 'sans_bold', sp)
        w, h = tw + size * 1.6, size * 1.75
        t = np.deg2rad(rot)
        cx = x + (w / 2 * np.cos(t) if anchor == 'l' else 0)
        cy = y - (w / 2 * np.sin(t) if anchor == 'l' else 0)
        sl, u, v = self._rbox(cx, cy, w / 2, h / 2, rot, 16)
        if sl is None: return Frame(cx, cy, w, h, rot)
        skew = self.rng.uniform(-0.12, 0.12)                             # scissor cut: ends not quite square
        m = np.clip(0.5 - self._sdf_rrect(u + v * skew * np.sign(u), v, w / 2, h / 2, 2.5), 0, 1)
        self._shadow(sl, m, 2.2, 2.2, 0.4)
        vn = (v + h / 2) / h
        grad = 1.2 - 0.3 * vn + 0.25 * np.exp(-((vn - 0.2) / 0.1) ** 2) - 0.12 * np.exp(-((vn - 0.97) / 0.05) ** 2)
        ridges = 1 + 0.03 * np.sin(v * 3.1) + 0.05 * (self.tooth[sl] - 0.5)
        self._over(sl, m, _c(colour)[None, None, :] * (grad * ridges)[..., None])
        tm, tsl = self._tmask(s, cx, cy, size, 'sans_bold', 'mm', sp, rot, 0)
        if tsl is not None:
            hmap = blur(tm, 1.0) * 3.0
            gy, gx = np.gradient(hmap)
            lit = np.clip(1 - 0.9 * (gx * self.L[0] + gy * self.L[1]), 0.45, 1.5)
            stress = 0.84 + 0.16 * noise2d(tm.shape[0], tm.shape[1], 3, 2, self._seed())
            col = _c(letters)[None, None, :] * (stress * lit)[..., None]
            self._over(tsl, np.clip(tm * 1.05, 0, 1), np.clip(col, 0, 1))
            self._mul(tsl, np.clip(shift(blur(tm, 0.8), 1, 1) - tm, 0, 1) * 0.5, '#000000')
        return Frame(cx, cy, w, h, rot)

    def stain(self, cx, cy, r, colour='#8a5a2b', strength=0.2, gaps=0.35):
        """a coffee-ring stain: a faint fill with the darker tide line at the rim (partly broken)"""
        sl = self._box(cx - r - 12, cy - r - 12, cx + r + 12, cy + r + 12)
        if sl is None: return
        dx, dy = self.XX[sl] - cx, self.YY[sl] - cy
        th = np.arctan2(dy, dx); d = np.hypot(dx, dy)
        s = self._seed()
        rr = r * (1 + 0.035 * _periodic(th, 10, s) + 0.02 * np.cos(th - 0.8))
        inside = np.clip(rr - d + 0.5, 0, 1)
        rim = np.exp(-((d - rr + 1.0) / 1.15) ** 2) * 1.3 + 0.28 * np.exp(-((d - rr + 4.5) / 3.0) ** 2) * inside
        keep = (0.12 + 0.88 * smoothstep(gaps - 0.15, gaps + 0.15, 0.5 + 0.5 * _periodic(th, 6, s + 1, 0.8))) * (0.75 + 0.25 * np.cos(th - 0.8))
        tide = 0.14 * np.exp(-((d - rr * 0.84) / 1.2) ** 2) * np.clip(0.7 * _periodic(th, 5, s + 2), 0, 1)
        fill = inside * 0.08 * (0.6 + 0.4 * noise2d(d.shape[0], d.shape[1], 30, 2, s + 3))
        self._mul(sl, strength * (rim * keep + tide + fill), colour)

    # ------------------------------------------------------------ desk props
    def pencil_prop(self, x, y, angle=90, length=1100, width=34, body='#56677a', wood='#e2c298', lead='#2a3038',
                    label=None, label_colour='#d9c78c', end='eraser', eraser='#d39a90', ferrule='#c8c2b2'):
        """a hexagonal pencil lying on the desk, point at (x, y), body running along `angle`
        (screen degrees, clockwise from +x); end='eraser' adds a crimped ferrule and a rubber, 'plain' a cut end"""
        a = np.deg2rad(angle); ca, sa = np.cos(a), np.sin(a)
        Rh = width / 2; cone = Rh * 5.4
        ex, ey = x + ca * length, y + sa * length
        sl = self._box(min(x, ex) - Rh - 40, min(y, ey) - Rh - 40, max(x, ex) + Rh + 40, max(y, ey) + Rh + 40)
        if sl is None: return
        X, Y = self.XX[sl] - x, self.YY[sl] - y
        u = X * ca + Y * sa; v = -X * sa + Y * ca
        rad = np.where(u < cone, Rh * np.clip(u / cone, 0, 1), Rh)
        if end == 'eraser':
            fl, el, rE = width * 1.25, width * 0.85, Rh * 0.55
            uf0, ue0 = length - el - fl, length - el
            cap = Rh * 0.88 * np.sqrt(np.clip(1 - ((u - (length - rE)) / rE) ** 2, 0, 1))
            rad = np.where(u >= ue0, np.where(u > length - rE, cap, Rh * 0.88), np.where(u >= uf0, Rh * 0.96, rad))
        m = np.clip(rad - np.abs(v) + 0.5, 0, 1) * np.clip(u + 0.5, 0, 1) * np.clip(length - u + 0.5, 0, 1)
        self._shadow(sl, m, Rh * 0.9 + 5, 6, 0.5)
        self._shadow(sl, m, 2, 2, 0.35)
        Lu = self.L[0] * ca + self.L[1] * sa; Lv = -self.L[0] * sa + self.L[1] * ca; Lz = self.L[2]
        Hh = np.array([Lu, Lv, Lz + 1]); Hh /= np.linalg.norm(Hh)
        # painted hexagonal body: three facets seen from above
        side = np.where(v < -Rh / 2, -1, np.where(v > Rh / 2, 1, 0))
        nv = side * 0.866; nz = np.where(side == 0, 1.0, 0.5)
        dif = np.clip(nv * Lv + nz * Lz, 0, 1)
        sp = np.clip(nv * Hh[1] + nz * Hh[2], 0, 1) ** 50
        paint = _c(body)[None, None, :] * (0.42 + 0.72 * dif)[..., None] + (sp * 0.28)[..., None]
        ridge = np.exp(-((np.abs(v) - Rh / 2) / 0.8) ** 2) * 0.12
        paint = paint + ridge[..., None]
        streak = np.interp(np.clip(u, 0, length), np.linspace(0, length, 400), fbm1d(400, 30, 2, self._seed()))
        paint = paint * (1 + 0.02 * streak)[..., None]
        # scalloped paint edge where the sharpener cut into each facet
        sface = np.where(side == 0, v, (np.abs(v) - 0.75 * Rh) / 0.5)
        u_paint = cone * np.sqrt(0.75 + (sface / Rh) ** 2)
        # sharpened cone (round): wood, then the graphite point
        rc = np.maximum(Rh * np.clip(u / cone, 1e-3, 1), 1e-3)
        cnv = np.clip(v / rc, -1, 1); cnz = np.sqrt(np.clip(1 - cnv ** 2, 0, 1))
        k = Rh / cone
        cn = np.stack([-k * cnz, cnv, cnz], -1); cn /= np.linalg.norm(cn, axis=-1, keepdims=True)
        cdif = np.clip(cn[..., 0] * Lu + cn[..., 1] * Lv + cn[..., 2] * Lz, 0, 1)
        csp = np.clip(cn[..., 0] * Hh[0] + cn[..., 1] * Hh[1] + cn[..., 2] * Hh[2], 0, 1)
        grain = 0.5 + 0.5 * np.sin(cnv * 7 + 1.5 * noise2d(u.shape[0], u.shape[1], 18, 2, self._seed()) * 3 + u * 0.02)
        woodc = _c(wood)[None, None, :] * (0.55 + 0.6 * cdif - 0.08 * grain)[..., None]
        leadc = _c(lead)[None, None, :] * (0.6 + 0.6 * cdif)[..., None] + (csp ** 30 * 0.55)[..., None]
        tip = u < cone * 0.24
        col = np.where((u < u_paint)[..., None], np.where(tip[..., None], leadc, woodc), paint)
        edge = np.clip(1 - np.abs(u - u_paint) / 1.2, 0, 1) * (u > cone * 0.5)
        col = col * (1 - 0.25 * edge)[..., None]
        if end == 'eraser':                                              # round parts: crimped metal ferrule, rubber
            rr = np.maximum(rad, 1e-3)
            rnv = np.clip(v / rr, -1, 1); rnz = np.sqrt(np.clip(1 - rnv ** 2, 0, 1))
            rnu = np.where(u > length - rE, np.clip((u - (length - rE)) / rE, 0, 1), 0)
            rn = np.stack([rnu, rnv, rnz], -1); rn /= np.linalg.norm(rn, axis=-1, keepdims=True)
            rdif = np.clip(rn[..., 0] * Lu + rn[..., 1] * Lv + rn[..., 2] * Lz, 0, 1)
            rsp = np.clip(rn[..., 0] * Hh[0] + rn[..., 1] * Hh[1] + rn[..., 2] * Hh[2], 0, 1)
            crimp = np.cos(2 * np.pi * (u - uf0) / 6.0) * ((u - uf0 < fl * 0.3) | (u - uf0 > fl * 0.7))
            fcol = _c(ferrule)[None, None, :] * (0.4 + 0.7 * rdif - 0.12 * crimp)[..., None] + (rsp ** 40 * 0.7)[..., None]
            ecol = _c(eraser)[None, None, :] * (0.5 + 0.6 * rdif + 0.03 * (self.tooth[sl] - 0.5))[..., None]
            col = np.where((u >= ue0)[..., None], ecol, np.where((u >= uf0)[..., None], fcol, col))
        self._over(sl, m, np.clip(col, 0, 1))
        if label:
            lx, ly = x + ca * (cone + 150), y + sa * (cone + 150)
            self.text(label, lx, ly, width * 0.42, label_colour, 'sans_bold', 'lm', rot=-angle, spacing=2, medium='opaque', alpha=0.85)

    # ------------------------------------------------------------ output
    def composite(self, vignette=0.2):
        r = np.hypot((self.XX - self.W * 0.45) / self.W, (self.YY - self.H * 0.42) / self.H)
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
