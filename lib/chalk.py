"""chalk — a classroom chalkboard: green slate, chalk lettering and diagrams, eraser swipes and the ghosts of old
lessons, a wooden frame and a chalk ledge with sticks of chalk and a felt eraser (numpy + Pillow only).

Model: the board is seen straight on under the classroom lights (from above, a little to the left).
  slate    matt green board paint: an uneven, cloudy tone (years of washing and wiping), a darker fall-off toward
           the frame, a very fine paint grain, and a per-pixel "tooth" field -- the microscopic peaks and pits of
           the paint that chalk catches on. The same tooth is used by every mark, so crossing strokes share grain.
  chalk    a stick of soft calcium carbonate. A mark is a deposit, not a paint fill: where the stick touches, chalk
           is scraped off onto the tooth peaks. Pressure decides how deep into the tooth it reaches, so a light
           stroke skips the pits and comes out broken and grainy, a heavy one is nearly solid but still keeps a
           few pits. The worn tip's contact patch is rounded, so a stroke is densest down its centre and ragged at
           its edges. Along a stroke the hand's pressure drifts, the stick lands with a slightly heavier dab and
           lifts off with a taper. Loose powder makes a faint halo round every mark, and some of it falls: a few
           specks always drift below fresh writing.
  side     the stick laid on its side and dragged broadside (shading, fills): a wide band whose long edges are the
           stick's two ends, very light pressure (only the highest tooth takes chalk) and long streaks in the
           direction of motion, because the stick's surface touches unevenly along its length. Overlapping
           passes build up, so a shaded area is streaky, never flat.
  letters  a font mask (CJK / Latin sans, never a handwriting font) written the way a teacher writes on a board:
           each character a little rotated, lifted or dropped, a touch bigger or smaller, pressed harder or softer,
           the line drifting slightly off level. The mask is then warped by a pixel or so (broken edges), given a
           patchy pressure field and pushed through the same tooth deposit as the strokes.
  drawing  freehand lines with a slow bow, ruler lines (straight, pressure still uneven), boxes whose sides
           overshoot the corners, loops that run past a full turn and drift so they never close, arrows whose two
           head flicks meet (and pile up chalk) at the tip, underlines, hatching, pressed dots, dashed lines drawn
           dash by dash, and wave squiggles for light.
  eraser   a felt block pushed along a path: it lifts most of the chalk in its footprint, drags the rest along the
           motion (a smear), leaves a thin film of dust combed into streaks by the felt, and a slightly heavier line
           of dust at the two ends of the felt. `erased()` turns anything drawn inside it into the ghost of an old
           lesson: wiped, not washed.
  dust     specks of settled powder everywhere, thicker toward the bottom where it falls, and a haze just above
           the ledge.
  frame    mitred wooden rails (grain along each rail, a rounded outer edge, a bevel down to the board) casting a
           shadow onto the board, and a chalk ledge: a dusty tray floor and a rounded front lip, holding sticks of
           chalk (matt cylinders, one end worn to a slant) and a felt eraser (wooden back, layered felt caked with
           chalk), each with its own shadow.
Layers: slate -> chalk (premultiplied colour + alpha, so the eraser can take chalk away again) -> things in front
of the board (frame, ledge, props, the shadows they cast) -> room light and vignette.
Lettering uses sans / sans_bold / cjk_sans (a glyph missing in one falls back to the other), never handwriting fonts.
Angles and rotations are degrees counter-clockwise, like PIL.

    from chalk import Chalkboard, WHITE, YELLOW, PINK, BLUE
    cb = Chalkboard(1920, 1080, seed=1)
    cb.slate()
    with cb.erased(keep=0.15):                         # an old lesson, wiped off
        cb.text('v = λ f', 1300, 300, 60)
    cb.swipe([(80, 400), (900, 380), (1800, 420)], width=130)
    cb.dust()
    cb.frame()
    cb.chalk_stick(300, cb.tray_y, 90, WHITE); cb.eraser(1650, cb.tray_y + 7)
    cb.text('为什么天空是蓝的？', 110, 160, 88)
    cb.underline(110, 900, 186, YELLOW)
    cb.loop(600, 500, 160, 60, YELLOW)                 # a loop that doesn't quite close
    cb.arrow([(300, 700), (500, 660), (700, 700)])
    cb.save('out.png')
"""
import numpy as np
from contextlib import contextmanager
from PIL import Image, ImageDraw, ImageChops
from core import blur, fbm1d, spline, noise2d, smoothstep, shift, load_font

WHITE, YELLOW, PINK, BLUE = '#f4f2e9', '#f4e18c', '#f4b5c4', '#acd4ef'
RED, ORANGE, GREEN, VIOLET = '#f4a19b', '#f6c58f', '#bfe2ab', '#cdb9ec'
DUST = '#e1e8e1'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- small helpers (kept inside this module)
_FONTS, _HAS = {}, {}


def _font(style, size):
    k = (style, int(round(size)))
    if k not in _FONTS:
        _FONTS[k] = load_font(style, max(4, int(round(size))))
    return _FONTS[k]


def _is_cjk(ch):
    o = ord(ch)
    return 0x2E80 <= o <= 0x9FFF or 0xF900 <= o <= 0xFAFF or 0xFF00 <= o <= 0xFFEF or 0x3000 <= o <= 0x303F


def _has(style, ch):
    """does the font for `style` have a real glyph for ch (not the .notdef box)?"""
    k = (style, ch)
    if k not in _HAS:
        f = _font(style, 48)
        a, b = f.getmask(ch), f.getmask('\ue000')
        _HAS[k] = ch.isspace() or not (a.size == b.size and bytes(a) == bytes(b))
    return _HAS[k]


def _pick(ch, style):
    """font style for one character: CJK uses the CJK sans; a glyph missing in one font falls back to the other"""
    first = 'cjk_sans' if (_is_cjk(ch) or style in ('cjk', 'cjk_sans')) else style
    if _has(first, ch): return first
    other = 'sans_bold' if first == 'cjk_sans' else 'cjk_sans'
    return other if _has(other, ch) else first


def _resample(P, step):
    P = np.asarray(P, np.float32)
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(s[-1] / step) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


def _bilinear(a, x, y):
    h, w = a.shape
    x = np.clip(x, 0, w - 1.001); y = np.clip(y, 0, h - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32)
    fx, fy = x - x0, y - y0
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy)
            + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)


def _dirblur(a, angle, length, taps=11):
    """average of shifted copies along a direction (degrees ccw): the smear of a wiped mark"""
    if length < 1: return a.copy()
    t = np.deg2rad(angle)
    out = np.zeros_like(a)
    for k in np.linspace(-length / 2, length / 2, taps):
        out += shift(a, k * np.cos(t), -k * np.sin(t))
    return out / taps


def _sdf_rrect(u, v, hw, hh, r):
    qx, qy = np.abs(u) - (hw - r), np.abs(v) - (hh - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


class Chalkboard:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.3, -0.8, 0.52)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        L = np.asarray(light, np.float32)
        self.L = L / np.linalg.norm(L)
        self.paint = np.zeros((H, W, 3), np.float32) + hexc('#2b4538')
        self.ca = np.zeros((H, W), np.float32)              # chalk: alpha
        self.cc = np.zeros((H, W, 3), np.float32)           # chalk: colour, premultiplied
        self.ta = np.zeros((H, W), np.float32)              # in front of the board: alpha
        self.tc = np.zeros((H, W, 3), np.float32)           # in front of the board: colour, premultiplied
        self.dims = (22, 20, 58)                              # frame: side rails, top rail, ledge (px)
        self.area = (22, 20, W - 22, H - 58)                  # the writing area inside the frame
        self.tray_y = H - 58 + int(58 * 0.4) - 3
        g = blur(self.rng.random((H, W)).astype(np.float32), 0.55)     # paint tooth: ~1 px peaks and pits ...
        m = noise2d(H, W, 3.2, 2, self._seed())                         # ... a little clumpy
        z = (0.85 * (g - g.mean()) / (g.std() + 1e-6) + 0.4 * (m - m.mean()) / (m.std() + 1e-6)) / np.hypot(0.85, 0.4)
        self.tooth = (0.5 + 0.5 * np.tanh(0.95 * z)).astype(np.float32)  # roughly uniform in 0..1
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ low-level compositing
    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _lay(self, sl, a, colour):
        """chalk onto the board (premultiplied over): it covers the slate, and more chalk covers chalk"""
        a = np.clip(a, 0, 1)
        col = colour if (isinstance(colour, np.ndarray) and colour.ndim == 3) else _c(colour)
        self.cc[sl] = self.cc[sl] * (1 - a[..., None]) + col * a[..., None]
        self.ca[sl] = self.ca[sl] + a * (1 - self.ca[sl])

    def _front(self, sl, a, colour):
        """something in front of the board (frame, ledge, props, their shadows); colour may be (h, w, 3)"""
        a = np.clip(a, 0, 1)
        col = colour if (isinstance(colour, np.ndarray) and colour.ndim == 3) else _c(colour)
        self.tc[sl] = self.tc[sl] * (1 - a[..., None]) + col * a[..., None]
        self.ta[sl] = self.ta[sl] + a * (1 - self.ta[sl])

    def _shadow(self, sl, mask, dx, dy, soft, strength, tint='#070a08'):
        sh = shift(mask, dx, dy)
        if soft > 0: sh = blur(sh, soft)
        self._front(sl, sh * strength, tint)

    def _specks(self, x, y, alpha, colour=DUST, size=0.55):
        """scattered grains of chalk powder"""
        x, y, alpha = np.asarray(x), np.asarray(y), np.asarray(alpha, np.float32)
        ok = (x >= 1) & (y >= 1) & (x < self.W - 1) & (y < self.H - 1)
        if not ok.any(): return
        x, y, alpha = x[ok], y[ok], alpha[ok]
        sl = self._box(x.min() - 6, y.min() - 6, x.max() + 7, y.max() + 7)
        m = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), np.float32)
        np.add.at(m, (np.round(y).astype(int) - sl[0].start, np.round(x).astype(int) - sl[1].start), alpha)
        m = blur(m, size) * (1.0 / (2 * np.pi * size * size)) * 0.9
        self._lay(sl, np.clip(m, 0, 0.9), colour)

    # ------------------------------------------------------------ the chalk deposit
    def _deposit(self, v, sl, grain=1.0, halo=0.15, powder=0.0):
        """contact map v (coverage x pressure, 0..1) -> chalk alpha. The tooth decides where chalk sticks:
        low contact only reaches the highest peaks (broken, grainy), high contact fills all but the deepest pits."""
        t = 0.5 + (self.tooth[sl] - 0.5) * grain
        v = np.clip(v, 0, 1)
        thr = 0.98 - 0.86 * v                                           # full pressure still leaves ~15 % pits
        a = smoothstep(thr - 0.12, thr + 0.12, t) * (0.5 + 0.5 * v) * smoothstep(0.03, 0.18, v)
        if powder:
            a = a + powder * v * (1 - a)
        if halo:                                                        # loose powder round the mark, some falling
            h = blur(a, 1.8) * halo + blur(shift(a, 0, 3), 4.5) * halo * 0.45
            a = 1 - (1 - a) * (1 - np.clip(h, 0, 1))
        return a

    def _fall(self, a, sl, colour, amount):
        """a few grains drop off fresh chalk and stick to the board below it"""
        if amount <= 0: return
        ys, xs = np.nonzero(a > 0.45)
        n = int(len(xs) * 0.0035 * amount)
        if n == 0: return
        r = self.rng
        i = r.integers(0, len(xs), n)
        self._specks(xs[i] + sl[1].start + r.normal(0, 1.3, n), ys[i] + sl[0].start + 1 + r.exponential(10, n),
                     r.uniform(0.1, 0.42, n), colour)

    # ------------------------------------------------------------ stroke rasteriser
    def _raster(self, strokes, pad=16, ss=3):
        """strokes: [(P (n,2), width (n,), value (n,) 0..1)] -> (mask, slices), drawn at ss x then box-filtered"""
        allp = np.concatenate([s[0] for s in strokes])
        p = max(float(s[1].max()) for s in strokes) / 2 + pad
        sl = self._box(allp[:, 0].min() - p, allp[:, 1].min() - p, allp[:, 0].max() + p, allp[:, 1].max() + p)
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
                d.ellipse([Q[0, 0] - r, Q[0, 1] - r, Q[0, 0] + r, Q[0, 1] + r], fill=int(255 * np.clip(v[0], 0, 1)))
                continue
            for i in range(0, n - 1, 2):
                j = min(n - 1, i + 2)
                ww = float(w[i:j + 1].mean()) * ss
                vv = int(round(255 * float(np.clip(v[i:j + 1].mean(), 0, 1))))
                r = ww / 2
                d.ellipse([Q[i, 0] - r, Q[i, 1] - r, Q[i, 0] + r, Q[i, 1] + r], fill=vv)
                d.line([(float(q[0]), float(q[1])) for q in Q[i:j + 1]], fill=vv, width=max(1, int(round(ww))))
            r = w[-1] * ss / 2
            d.ellipse([Q[-1, 0] - r, Q[-1, 1] - r, Q[-1, 0] + r, Q[-1, 1] + r], fill=int(255 * np.clip(v[-1], 0, 1)))
        return np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255, sl

    def _prep(self, pts, width, pressure, jitter, smooth=True, step=1.2):
        """resample a hand stroke, add the hand's slow wobble and a pressure profile -> (P, widths, pressures)"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 10)
        P = _resample(P, step)
        n = len(P)
        if n < 2: return P, np.array([width], np.float32), np.array([pressure], np.float32)
        tg = np.gradient(P, axis=0)
        tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
        s = self._seed()
        P = P + nrm * (fbm1d(n, max(4, 150 / step), 3, s) * jitter + fbm1d(n, max(2, 10 / step), 2, s + 1) * jitter * 0.15)[:, None]
        L = n * step
        d = np.linspace(0, L, n)
        land = 1 + 0.16 * np.exp(-(d / 4.0) ** 2)                         # the stick lands with a heavier dab
        lift = 0.35 + 0.65 * smoothstep(0, min(18.0, L * 0.35), L - d)    # ... and lifts off with a taper
        flow = 1 + 0.2 * fbm1d(n, max(4, 110 / step), 2, s + 2) + 0.07 * fbm1d(n, max(2, 7 / step), 1, s + 3)
        press = np.clip(pressure * land * lift * flow, 0.02, 1).astype(np.float32)
        w = (width * (0.78 + 0.22 * press / max(pressure, 1e-3))).astype(np.float32)
        return P, w, press

    # ------------------------------------------------------------ tip strokes
    def strokes(self, paths, colour=WHITE, width=4.0, pressure=0.85, jitter=0.7, smooth=True, grain=1.0, halo=0.15,
                fall=1.0, strength=0.96):
        """many chalk strokes in one pass (a list of point lists); where they cross they don't pile up"""
        prepared = [self._prep(p, width, pressure, jitter, smooth) for p in paths if len(p) >= 1]
        prepared = [p for p in prepared if len(p[0])]
        if not prepared: return
        m, sl = self._raster(prepared)
        if sl is None: return
        v = np.clip(blur(m, max(0.6, 0.26 * width)) * 1.22, 0, 1)       # the worn tip's rounded contact patch
        a = self._deposit(v, sl, grain, halo) * strength
        self._lay(sl, a, colour)
        self._fall(a, sl, colour, fall)

    def stroke(self, pts, colour=WHITE, width=4.0, pressure=0.85, jitter=0.7, smooth=True, **kw):
        """one freehand chalk stroke through pts (Catmull-Rom smoothed unless smooth=False)"""
        self.strokes([pts], colour, width, pressure, jitter, smooth, **kw)

    def line(self, x0, y0, x1, y1, colour=WHITE, width=4.0, pressure=0.85, bow=None, jitter=0.6, overshoot=3.0,
             ruler=False, **kw):
        """a freehand straight line (a slow bow, ends over/under-shooting) or, ruler=True, one drawn along a ruler"""
        r = self.rng
        p0, p1 = np.array([x0, y0], np.float32), np.array([x1, y1], np.float32)
        d = p1 - p0; L = float(np.linalg.norm(d)) + 1e-6; u = d / L
        a = p0 - u * r.uniform(-overshoot * 0.4, overshoot)
        b = p1 + u * r.uniform(-overshoot * 0.4, overshoot)
        if ruler:
            self.stroke([a, b], colour, width, pressure, 0.15, smooth=False, **kw)
        else:
            bow = r.uniform(-1, 1) * L * 0.006 if bow is None else bow
            mid = (a + b) / 2 + np.array([-u[1], u[0]]) * bow
            self.stroke([a, mid, b], colour, width, pressure, jitter, smooth=True, **kw)

    def rule(self, x0, y0, x1, y1, colour=WHITE, width=4.0, pressure=0.85, **kw):
        """a line drawn against the board ruler: dead straight, pressure still uneven"""
        self.line(x0, y0, x1, y1, colour, width, pressure, ruler=True, **kw)

    def box(self, x0, y0, x1, y1, colour=WHITE, width=3.6, pressure=0.85, overshoot=8.0, gap=None, jitter=0.5, **kw):
        """four separate strokes whose ends run past the corners; gap=(xa, xb) leaves the top side open for a label"""
        r = self.rng
        j = lambda: r.uniform(-1.4, 1.4)
        ov = lambda: r.uniform(1.5, overshoot)
        ya, yb = y0 + j(), y0 + j()
        top = [(x0 - ov(), ya, x1 + ov(), yb)]
        if gap:
            top = [(x0 - ov(), ya, gap[0], ya + (yb - ya) * 0.3), (gap[1], ya + (yb - ya) * 0.7, x1 + ov(), yb)]
        sides = top + [(x1 + j(), y0 - ov(), x1 + j(), y1 + ov()), (x1 + ov(), y1 + j(), x0 - ov(), y1 + j()),
                       (x0 + j(), y1 + ov(), x0 + j(), y0 - ov())]
        for (a, b, c, d) in sides:
            self.line(a, b, c, d, colour, width * r.uniform(0.9, 1.08), pressure * r.uniform(0.9, 1.05), jitter=jitter,
                      overshoot=0.5, **kw)

    def underline(self, x0, x1, y, colour=YELLOW, width=5.0, pressure=0.9, double=False, sag=2.5, **kw):
        r = self.rng
        self.stroke([(x0, y + r.uniform(-1, 1)), ((x0 + x1) / 2, y + sag), (x1, y - r.uniform(0.5, 3))], colour, width,
                    pressure, 0.6, **kw)
        if double:
            self.stroke([(x0 + 26, y + 15), ((x0 + x1) / 2, y + 15 + sag), (x1 - 70, y + 13)], colour, width * 0.62,
                        pressure * 0.9, 0.6, **kw)

    def loop(self, cx, cy, rx, ry, colour=YELLOW, width=4.4, pressure=0.88, rot=0.0, turns=1.13, a0=None, drift=0.08, **kw):
        """a hand-drawn loop around something: a bit more than one turn, drifting outward so it never closes"""
        r = self.rng
        N = int(max(90, 2 * np.pi * max(rx, ry) * turns / 3))
        t = np.linspace(0, 1, N)
        a0 = r.uniform(150, 215) if a0 is None else a0
        ang = np.deg2rad(a0) + t * 2 * np.pi * turns
        k = 1 + fbm1d(N, 30, 2, self._seed()) * 0.018 + (t - 0.5) * drift
        x, y = rx * k * np.cos(ang), ry * (k + (t - 0.5) * drift * 0.5) * np.sin(ang)
        q = np.deg2rad(-rot)
        P = np.stack([cx + x * np.cos(q) - y * np.sin(q), cy + x * np.sin(q) + y * np.cos(q)], 1)
        self.stroke(P, colour, width, pressure, 0.5, smooth=False, **kw)

    def circle(self, cx, cy, r, colour=WHITE, width=4.0, pressure=0.85, **kw):
        """a freehand circle: the ends just meet and overlap a little"""
        self.loop(cx, cy, r, r * self.rng.uniform(0.97, 1.02), colour, width, pressure, rot=0, turns=1.04, drift=0.025, **kw)

    def dot(self, x, y, r=3.5, colour=WHITE, pressure=1.0):
        """a dot pressed in with a little twist of the stick"""
        n = 14
        a = np.linspace(0, 3 * np.pi, n); rr = np.linspace(r * 0.45, 0.2, n)
        self.stroke(np.stack([x + rr * np.cos(a), y + rr * np.sin(a)], 1), colour, r * 1.5, pressure, 0.1, smooth=False, fall=0.3)

    def arrow(self, pts, colour=WHITE, width=4.0, pressure=0.85, head=18, spread=27, smooth=True, **kw):
        """a stroke through pts ending in two head flicks that meet (and pile up chalk) at the tip"""
        P = np.asarray(pts, np.float32)
        P = spline(P, 12) if (smooth and len(P) > 2) else _resample(P, 2.0)
        self.stroke(P, colour, width, pressure, 0.45, smooth=False, **kw)
        self._head(P, colour, width, pressure, head, spread, **kw)

    def _head(self, P, colour, width, pressure, head, spread, **kw):
        tip = P[-1]
        d = np.hypot(*(P - tip).T)
        k = int(np.argmax(d > head * 0.8)) if (d > head * 0.8).any() else 0
        a = np.arctan2(tip[1] - P[k][1], tip[0] - P[k][0])
        r = self.rng
        wings = []
        for side in (1, -1):
            b = a + np.pi + side * np.deg2rad(spread * r.uniform(0.9, 1.1))
            wings.append([tip + np.array([np.cos(b), np.sin(b)]) * head * r.uniform(0.9, 1.08), tip + (tip - P[k]) / (d[k] + 1e-6) * 1.5])
        self.strokes(wings, colour, width * 0.95, pressure, 0.2, smooth=False, **kw)

    def wave(self, p0, p1, wavelength=40, amplitude=10, colour=BLUE, width=3.6, pressure=0.85, head=15, **kw):
        """light as a squiggle from p0 to p1: a sine along the line, easing in, settling onto the axis at the arrow tip"""
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
        d = p1 - p0; L = float(np.linalg.norm(d)); u = d / L; nrm = np.array([-u[1], u[0]], np.float32)
        s = np.arange(0, L, 1.0)
        env = smoothstep(0, wavelength * 0.5, s) * smoothstep(head * 0.6, head * 0.6 + wavelength * 0.6, L - s)
        ph = self.rng.uniform(0, 0.2)
        P = p0 + u * s[:, None] + nrm * (amplitude * env * np.sin(2 * np.pi * (s / wavelength + ph)))[:, None]
        P = np.vstack([P, p1])
        self.stroke(P, colour, width, pressure, 0.3, smooth=False, **kw)
        if head: self._head(P, colour, width, pressure, head, 28, **kw)

    def propto(self, x, y, size, colour=WHITE, width=None, pressure=0.9):
        """the proportional sign written by hand (a font's bold ∝ thickens into ∞): one stroke, the left loop of a
        lemniscate with both tails running on to the right. (x, y) = left end on the baseline, size = letter size"""
        a = size * 0.46
        t = np.linspace(np.pi / 2 - 0.55, 3 * np.pi / 2 + 0.55, 90)
        den = 1 + np.sin(t) ** 2
        px, py = np.cos(t) / den, np.sin(t) * np.cos(t) / den           # the left lobe, crossing at the origin
        P = np.stack([x + a * 1.05 + px * a * 1.05, y - size * 0.32 + py * a * 1.3], 1)
        self.stroke(P[::-1], colour, width or max(3.0, size * 0.075), pressure, 0.3, smooth=False)
        return a * 2.1

    def dashed(self, pts, colour=WHITE, dash=18, gap=13, width=3.4, pressure=0.8, smooth=True, **kw):
        """a dashed line drawn dash by dash (every dash lands and lifts on its own)"""
        P = np.asarray(pts, np.float32)
        P = spline(P, 12) if (smooth and len(P) > 2) else P
        P = _resample(P, 1.0)
        r = self.rng
        out, i = [], int(r.uniform(0, gap))
        while i < len(P) - 3:
            ln = int(dash * r.uniform(0.8, 1.2))
            out.append(P[i:min(len(P), i + ln)])
            i += ln + int(gap * r.uniform(0.8, 1.25))
        self.strokes([o for o in out if len(o) > 2], colour, width, pressure, 0.2, smooth=False, **kw)

    def hatch(self, mask, colour=WHITE, angle=45, spacing=9, width=2.6, pressure=0.7, jitter=0.4, overshoot=3, **kw):
        """tip hatching inside a mask: parallel strokes, each slightly bowed, ends over/under-shooting"""
        ys, xs = np.nonzero(mask > 0.5)
        if len(xs) == 0: return
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), -np.sin(a)], np.float32)
        nv = np.array([np.sin(a), np.cos(a)], np.float32)
        cx, cy = xs.mean(), ys.mean()
        corners = np.array([[xs.min(), ys.min()], [xs.max(), ys.min()], [xs.min(), ys.max()], [xs.max(), ys.max()]], np.float32) - [cx, cy]
        on, od = corners @ nv, corners @ d
        r = self.rng
        paths = []
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
                t1 = ts[s1 - 1] + r.uniform(-overshoot * 0.8, overshoot * 1.2)
                p0 = np.array([cx, cy]) + nv * o + d * t0
                p1 = np.array([cx, cy]) + nv * o + d * t1
                mid = (p0 + p1) / 2 + nv * r.uniform(-1, 1) * (t1 - t0) * 0.015
                paths.append([p0, mid, p1])
            o += spacing * r.uniform(0.85, 1.15)
        self.strokes(paths, colour, width, pressure, jitter, smooth=True, **kw)

    # ------------------------------------------------------------ side of the stick
    def side(self, p0, p1, colour=WHITE, stick=36, pressure=0.45, clip=None, grain=1.0, strength=0.92, halo=0.06):
        """the stick laid on its side and dragged broadside from p0 to p1: a band `stick` px wide with streaks along
        the motion (the stick touches unevenly along its length); `clip` is a full-canvas mask it is confined to"""
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
        d = p1 - p0; L = float(np.linalg.norm(d)) + 1e-6; tx, ty = d / L
        pad = stick / 2 + 10
        sl = self._box(min(p0[0], p1[0]) - pad, min(p0[1], p1[1]) - pad, max(p0[0], p1[0]) + pad, max(p0[1], p1[1]) + pad)
        if sl is None: return
        X, Y = self.XX[sl] - p0[0], self.YY[sl] - p0[1]
        u = X * tx + Y * ty
        v = -X * ty + Y * tx
        s = self._seed()
        nv = int(stick + 24); vi = np.clip(v + stick / 2 + 12, 0, nv - 1)
        nu = int(L + 48); ui = np.clip(u + 24, 0, nu - 1)
        prof = np.interp(vi, np.arange(nv), 0.66 + 0.22 * fbm1d(nv, 2.5, 2, s) + 0.2 * fbm1d(nv, 11, 2, s + 1))
        e0 = np.interp(ui, np.arange(nu), fbm1d(nu, 40, 2, s + 2) * 2.2)
        e1 = np.interp(ui, np.arange(nu), fbm1d(nu, 40, 2, s + 3) * 2.2)
        band = smoothstep(-stick / 2 - 1.5, -stick / 2 + 2.0, v + e0) * smoothstep(-stick / 2 - 1.5, -stick / 2 + 2.0, -v + e1)
        rag = np.interp(vi, np.arange(nv), fbm1d(nv, 4, 2, s + 4) * 5)
        ends = smoothstep(-2, 5, u - rag) * smoothstep(-2, 6, L - u + rag)
        press = pressure * (1 + 0.28 * np.interp(ui, np.arange(nu), fbm1d(nu, 90, 2, s + 5)))
        vc = band * ends * prof * press
        if clip is not None: vc = vc * clip[sl]
        a = self._deposit(vc, sl, grain, halo, powder=0.22) * strength
        self._lay(sl, a, colour)

    def shade(self, mask, colour=WHITE, angle=0.0, stick=36, pressure=0.42, overlap=0.3, overshoot=6, ragged=1.0,
              strength=0.92, weight=None):
        """fill a mask with the side of the stick: parallel broadside passes (angle = direction of motion, degrees
        ccw) that overlap and build up; the fill stops a little short of / runs a little past the outline.
        weight: optional full-canvas 0..1 map of how hard the hand presses (e.g. a gradient)"""
        ys, xs = np.nonzero(mask > 0.5)
        if len(xs) == 0: return
        s = self._seed()
        bm = blur(mask.astype(np.float32), 2.0)
        clip = smoothstep(0.3, 0.7, bm + ragged * 0.35 * (noise2d(self.H, self.W, 9, 2, s) - 0.5)) if ragged else mask
        if weight is not None: clip = clip * weight
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), -np.sin(a)], np.float32)
        nv = np.array([np.sin(a), np.cos(a)], np.float32)
        cx, cy = xs.mean(), ys.mean()
        on = (xs - cx) * nv[0] + (ys - cy) * nv[1]
        od = (xs - cx) * d[0] + (ys - cy) * d[1]
        r = self.rng
        o = on.min() + stick * 0.3
        while o < on.max() + stick * 0.2:
            sel = np.abs(on - o) < stick / 2
            if sel.any():
                t0, t1 = od[sel].min() - overshoot, od[sel].max() + overshoot
                c = np.array([cx, cy]) + nv * o
                self.side(c + d * t0, c + d * t1, colour, stick * r.uniform(0.9, 1.1), pressure * r.uniform(0.85, 1.15),
                          clip, strength=strength)
            o += stick * (1 - overlap) * r.uniform(0.85, 1.1)

    # ------------------------------------------------------------ lettering
    def _tmask(self, s, x, y, size, style='sans_bold', anchor='ls', spacing=0.0, rot=0.0, weight=0.0, hand=1.0, ss=2):
        """lettering -> (mask, slices). Characters are placed one by one like handwriting: each gets its own small
        rotation, baseline shift, scale and pressure (the mask value); the line drifts slightly off level."""
        r = self.rng
        chars = [(ch, _pick(ch, style)) for ch in s]
        advs = [_font(st, size).getlength(ch) + spacing for ch, st in chars]
        total = sum(advs) - (spacing if chars else 0)
        if any(_is_cjk(ch) for ch, _ in chars):
            capH = -_font('cjk_sans', size).getbbox('中', anchor='ls')[1]
        else:
            capH = -_font(_pick('H', style), size).getbbox('H', anchor='ls')[1]
        desc = size * 0.22
        dyb = {'s': 0, 'm': capH / 2, 'a': capH, 't': capH, 'd': -desc, 'b': -desc}.get(anchor[1], 0)
        xs0 = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        m = size * 0.6 + weight + 8
        corners = np.array([[xs0 - m, y + dyb - capH - m], [xs0 + total + m, y + dyb - capH - m],
                            [xs0 - m, y + dyb + desc + m], [xs0 + total + m, y + dyb + desc + m]], np.float32)
        if rot:
            q = np.deg2rad(rot)
            dx, dy = corners[:, 0] - x, corners[:, 1] - y
            rc = np.stack([x + dx * np.cos(q) + dy * np.sin(q), y - dx * np.sin(q) + dy * np.cos(q)], 1)
            corners = np.vstack([corners, rc])
        ox, oy = int(np.floor(corners[:, 0].min())), int(np.floor(corners[:, 1].min()))
        bw, bh = int(np.ceil(corners[:, 0].max())) - ox + 1, int(np.ceil(corners[:, 1].max())) - oy + 1
        sl = self._box(ox, oy, ox + bw, oy + bh)
        if sl is None: return None, None
        im = Image.new('L', (bw * ss, bh * ss), 0)
        cx = (xs0 - ox) * ss
        by = (y + dyb - oy) * ss
        slope = r.normal(0, 0.006) * hand
        for (ch, st), adv in zip(chars, advs):
            if not ch.isspace():
                sc = 1 + r.normal(0, 0.03) * hand
                f = _font(st, size * ss * sc)
                fill = int(255 * np.clip(r.normal(0.93, 0.045 * hand + 0.01), 0.72, 1.0))
                wc = weight + (size * 0.028 * float(np.clip((size - 10) / 30, 0.3, 1)) if st == 'cjk_sans' else 0)
                # ^ the CJK sans is lighter than Latin bold; boost it, but less when small (dense characters clog up)
                gs = int(size * ss * sc * 1.8 + wc * ss * 2 + 8)
                g = Image.new('L', (gs, gs), 0)
                gx, gy = gs * 0.2, gs * 0.75
                ImageDraw.Draw(g).text((gx, gy), ch, font=f, fill=fill, anchor='ls', stroke_width=int(round(wc * ss)), stroke_fill=fill)
                rc = r.normal(0, 1.3) * hand
                if abs(rc) > 0.05:
                    g = g.rotate(rc, resample=Image.BICUBIC, center=(gx + adv * ss * sc / 2, gy - capH * ss * sc / 2))
                jx = r.normal(0, 0.012 * size) * hand * ss
                jy = r.normal(0, 0.02 * size) * hand * ss + slope * (cx - (xs0 - ox) * ss)
                px, py = int(round(cx + jx - gx)), int(round(by + jy - gy))
                box = (px, py, px + gs, py + gs)
                im.paste(ImageChops.lighter(im.crop(box), g), box)
            cx += adv * ss
        if rot:
            im = im.rotate(rot, resample=Image.BICUBIC, center=((x - ox) * ss, (y - oy) * ss))
        a = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        ys0, xs1 = sl[0].start - oy, sl[1].start - ox
        return a[ys0:ys0 + (sl[0].stop - sl[0].start), xs1:xs1 + (sl[1].stop - sl[1].start)], sl

    def text_width(self, s, size, font='sans_bold', spacing=0.0):
        return sum(_font(_pick(ch, font), size).getlength(ch) + spacing for ch in s) - (spacing if s else 0)

    def text(self, s, x, y, size, colour=WHITE, font='sans_bold', anchor='ls', pressure=0.93, weight=0.0, rot=0.0,
             spacing=0.0, hand=1.0, grain=None, halo=0.14, fall=0.6, strength=0.97):
        """chalk lettering. anchor: first letter l/m/r, second s (baseline), m (middle of the capitals), t (top).
        hand: how much every character wanders (0 = typeset). grain: how much the tooth breaks the letters
        (default: less for small text, so it stays legible)."""
        m, sl = self._tmask(s, x, y, size, font, anchor, spacing, rot, weight, hand)
        if sl is None: return
        h, w = m.shape
        s0 = self._seed()
        m = self._warp(m, 0.2 + size * 0.0095, max(4.0, size * 0.1), s0)          # broken edges (gentler when small)
        prs = 0.84 + 0.3 * noise2d(h, w, max(6.0, size * 0.55), 2, s0 + 1)         # patchy pressure
        v = np.clip(m * 1.06, 0, 1) * pressure * prs
        g = float(np.clip(0.3 + size / 95, 0.52, 1.0)) if grain is None else grain
        if size < 40: v = np.clip(v * (1.12 - size * 0.003), 0, 1)                   # small writing is pressed firmer
        a = self._deposit(v, sl, g, halo) * strength
        self._lay(sl, a, colour)
        self._fall(a, sl, colour, fall)

    def _warp(self, m, amp, scale, seed):
        h, w = m.shape
        dx = (noise2d(h, w, scale, 2, seed) - 0.5) * 2 * amp
        dy = (noise2d(h, w, scale, 2, seed + 7) - 0.5) * 2 * amp
        Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
        return _bilinear(m, X + dx, Y + dy)

    # ------------------------------------------------------------ board
    def slate(self, colour='#2c473a', edge='#18271f', worn='#3a5146', mottle=1.0):
        """matt green board paint: darker toward the frame, cloudy where it has been washed and wiped for years"""
        H, W = self.H, self.W
        s = self._seed()
        r = np.hypot((self.XX - 0.48 * W) / (0.66 * W), (self.YY - 0.42 * H) / (0.7 * H))
        t = smoothstep(0.2, 1.2, r)[..., None]
        base = _c(colour) * (1 - t) + _c(edge) * t
        cloud = noise2d(H, W, 480, 4, s)
        mid = noise2d(H, W, 110, 3, s + 1)
        wear = smoothstep(0.52, 0.85, noise2d(H, W, 700, 3, s + 2))[..., None] * 0.35 * mottle
        base = base * (1 - wear) + _c(worn) * wear
        fine = noise2d(H, W, 1.3, 2, s + 3)
        tone = 1 + mottle * (0.11 * (cloud - 0.5) + 0.05 * (mid - 0.5)) + 0.03 * (self.tooth - 0.5) + 0.02 * (fine - 0.5)
        self.paint = base * tone[..., None]

    @contextmanager
    def erased(self, keep=0.15, angle=0.0, smear=34, streaks=1.0):
        """everything drawn inside this block becomes the ghost of an old lesson: wiped with a felt eraser
        (angle = direction of the wiping, degrees ccw), smeared along the wipe, `keep` of it left behind"""
        ca0, cc0 = self.ca, self.cc
        self.ca = np.zeros_like(ca0); self.cc = np.zeros_like(cc0)
        try:
            yield self
        finally:
            a, c = self.ca, self.cc
            self.ca, self.cc = ca0, cc0
            ys, xs = np.nonzero(a > 0.002)
            if len(xs):
                pad = smear + 12
                sl = self._box(xs.min() - pad, ys.min() - pad, xs.max() + pad, ys.max() + pad)
                a, c = a[sl], c[sl]
                sa, sc = _dirblur(a, angle, smear), _dirblur(c, angle, smear)
                h, w = a.shape
                q = np.deg2rad(angle)
                Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
                u = X * np.cos(q) - Y * np.sin(q); v = X * np.sin(q) + Y * np.cos(q)
                s = self._seed()
                vmin = float(v.min()); nvv = int(v.max() - vmin) + 4
                fib = np.interp(v - vmin, np.arange(nvv), (fbm1d(nvv, 2.2, 2, s) + 1) / 2)
                slow = noise2d(h, w, 60, 2, s + 1)
                wipe = keep * np.clip(0.15 + 2.0 * slow ** 1.3 * ((1 - streaks) + streaks * 1.4 * fib ** 1.6), 0, 2.4)
                ga = blur(sa * 0.7 + a * 0.3, 0.7) * wipe
                gc = np.stack([blur(sc[..., k] * 0.7 + c[..., k] * 0.3, 0.7) for k in range(3)], -1) * wipe[..., None]
                self.cc[sl] = self.cc[sl] * (1 - ga[..., None]) + gc
                self.ca[sl] = self.ca[sl] + ga * (1 - self.ca[sl])

    def swipe(self, pts, width=120, strength=0.9, haze=0.05, smear=30, keep=0.12, colour=DUST):
        """a felt eraser pushed along pts: lifts chalk in its footprint (strength), drags `keep` of it along the
        motion, leaves a thin streaky film of dust (haze) and a heavier line of dust at the felt's two ends"""
        P = np.asarray(pts, np.float32)
        P = spline(P, 8) if len(P) > 2 else P
        P = _resample(P, 8.0)
        hw = width / 2
        pad = hw + smear + 10
        sl = self._box(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if sl is None: return
        X, Y = self.XX[sl], self.YY[sl]
        best = np.full(X.shape, 1e12, np.float32); uu = np.zeros_like(X); vv = np.zeros_like(X)
        seg = np.hypot(*np.diff(P, axis=0).T); acc = np.concatenate([[0], np.cumsum(seg)])
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]
            ab = b - a; l2 = float(ab @ ab) + 1e-6
            t = np.clip(((X - a[0]) * ab[0] + (Y - a[1]) * ab[1]) / l2, 0, 1)
            qx, qy = X - (a[0] + t * ab[0]), Y - (a[1] + t * ab[1])
            dd = qx * qx + qy * qy
            k = dd < best
            best = np.where(k, dd, best)
            uu = np.where(k, acc[i] + t * np.sqrt(l2), uu)
            vv = np.where(k, np.sign(ab[0] * qy - ab[1] * qx) * np.sqrt(dd), vv)
        Lp = float(acc[-1])
        s = self._seed()
        nu = int(Lp + 2); nv = int(width + 2 * pad)
        ui = np.clip(uu, 0, nu - 1); vi = np.clip(vv + nv / 2, 0, nv - 1)
        wav = np.interp(ui, np.arange(nu), fbm1d(nu, 60, 2, s) * 4)
        band = smoothstep(hw + 3, hw - 4, np.abs(vv) + wav)                 # round caps where the eraser lands and lifts
        press = 0.78 + 0.22 * np.interp(ui, np.arange(nu), fbm1d(nu, 140, 2, s + 1))
        fib = (np.interp(vi, np.arange(nv), fbm1d(nv, 1.8, 2, s + 2)) + 1) / 2
        fib2 = (np.interp(vi, np.arange(nv), fbm1d(nv, 9, 2, s + 3)) + 1) / 2
        e = np.clip(band * strength * press * (0.82 + 0.18 * fib), 0, 1)
        ang = np.rad2deg(np.arctan2(-(P[-1, 1] - P[0, 1]), P[-1, 0] - P[0, 0]))
        sa = _dirblur(self.ca[sl] * band, ang, smear); sc = _dirblur(self.cc[sl] * band[..., None], ang, smear)
        self.ca[sl] = self.ca[sl] * (1 - e) + sa * e * keep
        self.cc[sl] = self.cc[sl] * (1 - e[..., None]) + sc * (e * keep)[..., None]
        rim = np.exp(-((np.abs(vv) - hw + 3) / 3.0) ** 2) * smoothstep(0, 20, uu) * smoothstep(0, 20, Lp - uu)
        film = haze * press * (band * (0.3 + 0.55 * fib * fib2 + 0.35 * fib2) + 0.45 * rim * (0.4 + 0.6 * fib2))
        self._lay(sl, np.clip(film, 0, 1), colour)

    def smudge(self, cx, cy, w=160, h=60, rot=0.0, strength=0.7, haze=0.06):
        """a short dab of the eraser (a few centimetres of wiping)"""
        q = np.deg2rad(rot)
        d = np.array([np.cos(q), -np.sin(q)]) * w / 2
        self.swipe([(cx - d[0], cy - d[1]), (cx + d[0], cy + d[1])], h, strength, haze, smear=w * 0.25)

    def dust(self, amount=1.0, specks=4200, haze=0.2):
        """settled chalk powder: specks everywhere, thicker toward the bottom; a streaky haze above the ledge"""
        x0, y0, x1, y1 = self.area
        r = self.rng
        n = int(specks * amount)
        ys = y1 - (r.random(n) ** 2.3) * (y1 - y0)
        xs = r.uniform(x0, x1, n)
        self._specks(xs, ys, r.uniform(0.04, 0.26, n) * amount, DUST, 0.55)
        m = n // 6
        self._specks(r.uniform(x0, x1, m), y1 - (r.random(m) ** 3) * 200, r.uniform(0.05, 0.2, m) * amount, DUST, 1.0)
        sl = self._box(x0, y1 - 240, x1, y1)
        if sl is None: return
        Y = self.YY[sl]; hh, ww = Y.shape
        s = self._seed()
        streak = np.asarray(Image.fromarray(r.random((max(2, hh // 3), max(2, ww // 150))).astype(np.float32)).resize((ww, hh), Image.BICUBIC))
        cloud = noise2d(hh, ww, 90, 3, s)
        k = smoothstep(y1 - 240, y1, Y) ** 2.4
        self._lay(sl, np.clip(haze * amount * k * (0.35 + 0.45 * streak + 0.6 * cloud), 0, 1), DUST)

    # ------------------------------------------------------------ frame, ledge and props
    def _wood(self, h, w, colour, dark, seed, vertical=False):
        if vertical: h, w = w, h
        r = np.random.default_rng(seed)
        rs = lambda gh, gw, res=Image.BICUBIC: np.asarray(Image.fromarray(r.random((max(2, gh), max(2, gw))).astype(np.float32)).resize((w, h), res))
        g1 = rs(h // 2, w // 90); g2 = rs(h, w // 24); pores = rs(h, w // 5, Image.BILINEAR)
        fig = noise2d(h, w, 80, 3, seed + 1)
        rings = 0.5 + 0.5 * np.sin((fig * 7 + np.linspace(0, 3, h)[:, None]) * 2 * np.pi)
        grain = np.clip(0.5 * g1 + 0.3 * g2 + 0.2 * rings, 0, 1)
        col = _c(dark) + (_c(colour) - _c(dark)) * (0.35 + 0.8 * grain)[..., None]
        col = col * (1 - 0.3 * smoothstep(0.86, 0.97, pores))[..., None]
        return np.transpose(col, (1, 0, 2)) if vertical else col

    def _lit(self, nx, ny, nz, spec=0.12, shine=30):
        dif = np.clip(nx * self.L[0] + ny * self.L[1] + nz * self.L[2], 0, 1)
        Hh = self.L + np.array([0, 0, 1], np.float32); Hh /= np.linalg.norm(Hh)
        sp = np.clip(nx * Hh[0] + ny * Hh[1] + nz * Hh[2], 0, 1) ** shine * spec
        return dif, sp

    def frame(self, rail=None, top=None, ledge=None, wood='#77502f', dark='#2e1d10'):
        """mitred wooden rails round the board and a chalk ledge along the bottom; sets self.area (the writing area)
        and self.tray_y (where things lying on the ledge rest). Default sizes are known from the start (self.dims),
        so dust() and swipes can be laid down before the frame is drawn."""
        W, H = self.W, self.H
        rail, top, ledge = rail or self.dims[0], top or self.dims[1], ledge or self.dims[2]
        self.dims = (rail, top, ledge)
        BB = H - ledge
        fl = int(ledge * 0.4)
        self.area = (rail, top, W - rail, BB)
        self.tray_y = BB + fl - 3
        s = self._seed()
        full = (slice(0, H), slice(0, W))
        X, Y = self.XX, self.YY
        # shadows of the frame on the board (the rails stand proud of it; the light comes from above)
        dt, dl, dr = Y - top, X - rail, (W - rail) - X
        ins = ((dt > 0) & (dl > 0) & (dr > 0) & (Y < BB)).astype(np.float32)
        sh = (0.5 * np.exp(-np.clip(dt, 0, None) / 6) + 0.2 * np.exp(-np.clip(dt, 0, None) / 30) + 0.34 * np.exp(-np.clip(dl, 0, None) / 5)
              + 0.12 * np.exp(-np.clip(dl, 0, None) / 24) + 0.14 * np.exp(-np.clip(dr, 0, None) / 4) + 0.3 * np.exp(-np.clip(BB - Y, 0, None) / 3))
        self._front(full, np.clip(sh, 0, 0.85) * ins, '#050806')
        # rails: grain along each rail; profile = rounded outer edge, flat face, bevel down to the board
        def profile(sa):
            slope = 1.3 * (1 - smoothstep(0, 0.3, sa)) - 1.0 * smoothstep(0.62, 1.0, sa)    # dh/ds
            n = 1 / np.sqrt(1 + slope ** 2)
            return -slope * n, n
        wt = self._wood(top, W, wood, dark, s + 1)
        sa = (Y[:top] + 0.5) / top
        na, nz = profile(sa)
        dif, sp = self._lit(np.zeros_like(na), na, nz)
        col = wt * (0.32 + 0.95 * dif)[..., None] + sp[..., None]
        mt = ((Y[:top] <= X[:top] * top / rail) & (Y[:top] <= (W - 1 - X[:top]) * top / rail)).astype(np.float32)
        self._front((slice(0, top), slice(0, W)), mt, col)
        for side in (0, 1):
            x0 = 0 if side == 0 else W - rail
            sl = (slice(0, H), slice(x0, x0 + rail))
            wv = self._wood(H, rail, wood, dark, s + 2 + side, vertical=True)
            xx = X[sl] - x0
            sa = (xx + 0.5) / rail if side == 0 else (rail - xx - 0.5) / rail
            na, nz = profile(sa)
            nx = na if side == 0 else -na
            dif, sp = self._lit(nx, np.zeros_like(na), nz)
            col = wv * (0.32 + 0.95 * dif)[..., None] + sp[..., None]
            xl = xx if side == 0 else rail - 1 - xx
            mv = (Y[sl] > xl * top / rail).astype(np.float32)
            self._front(sl, mv, col)
            j = np.exp(-((Y[sl] - xl * top / rail) / 0.8) ** 2) * (Y[sl] < top + 2)    # the mitre joint
            self._front(sl, j * 0.45, '#140c06')
        # the ledge: tray floor (seen from above, dusty) and a rounded front lip
        sl = (slice(BB, H), slice(0, W))
        wl = self._wood(H - BB, W, wood, dark, s + 5)
        yy = Y[sl] - BB
        floor = (yy < fl).astype(np.float32)
        fcol = wl * (0.34 + 0.18 * (yy / fl))[..., None]
        fcol = fcol * (1 - 0.5 * np.exp(-yy / 2.5))[..., None]                            # the gap under the board
        la = yy - fl
        nose = smoothstep(0, 7, la)
        ny = -(1 - nose) * 0.85 + 0.45 * smoothstep(H - BB - fl - 8, H - BB - fl, la)
        nz = np.sqrt(np.clip(1 - ny ** 2, 0, 1))
        dif, sp = self._lit(np.zeros_like(ny), ny, nz, 0.18, 24)
        lcol = wl * (0.3 + 0.85 * dif)[..., None] * (1 - 0.35 * smoothstep(0, H - BB - fl, la))[..., None] + sp[..., None]
        col = np.where(floor[..., None] > 0, fcol, lcol)
        self._front(sl, np.ones_like(yy), col)
        self._front(sl, np.exp(-((la - 0.5) / 1.2) ** 2) * 0.5, '#120a05')                 # floor meets lip
        # chalk dust in the tray: heavier toward the back where it falls from the board
        fsl = (slice(BB, BB + fl), slice(rail // 2, W - rail // 2))
        hh, ww = fl, W - 2 * (rail // 2)
        r = self.rng
        streak = np.asarray(Image.fromarray(r.random((max(2, hh // 2), max(2, ww // 40))).astype(np.float32)).resize((ww, hh), Image.BICUBIC))
        cl = noise2d(hh, ww, 50, 3, s + 6)
        k = 1 - smoothstep(0, fl, self.YY[fsl] - BB) * 0.6
        self._front(fsl, np.clip((0.12 + 0.35 * cl * streak) * k, 0, 0.7), DUST)
        n = int(W * 0.5)
        px = r.uniform(rail, W - rail, n); py = BB + 2 + r.random(n) ** 1.5 * (fl - 4)
        self._front_specks(px, py, r.uniform(0.2, 0.7, n), r.uniform(0.5, 1.6, n))

    def _front_specks(self, x, y, alpha, rad, colour=DUST):
        sl = self._box(x.min() - 4, y.min() - 4, x.max() + 5, y.max() + 5)
        m = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), np.float32)
        for big in (False, True):
            k = rad > 1.0 if big else rad <= 1.0
            mm = np.zeros_like(m)
            np.add.at(mm, (np.round(y[k]).astype(int) - sl[0].start, np.round(x[k]).astype(int) - sl[1].start), alpha[k])
            sz = 1.1 if big else 0.55
            m += blur(mm, sz) / (2 * np.pi * sz * sz) * 0.9
        self._front(sl, np.clip(m, 0, 0.85), colour)

    def chalk_stick(self, x, y, length=86, colour=WHITE, rot=0.0, r=7.5, worn='right'):
        """a stick of chalk lying on the ledge, centred at (x, y - r) so it rests on y: a matt cylinder, one end cut
        square, the other (worn='right'|'left'|None) worn to a slant; fine lengthwise striations; its shadow"""
        cy = y - r
        q = np.deg2rad(rot); ca, sa = np.cos(q), np.sin(q)
        R = length / 2 + r + 12
        sl = self._box(x - R, cy - R * abs(sa) - r - 12, x + R, cy + R * abs(sa) + r + 12)
        X, Y = self.XX[sl] - x, self.YY[sl] - cy
        u = X * ca - Y * sa
        v = X * sa + Y * ca
        hl = length / 2
        d = _sdf_rrect(u, v, hl, r, r * 0.4)
        facet = np.zeros_like(u)
        if worn:
            sg = 1 if worn == 'right' else -1
            cut = (sg * u - hl + 0.55 * (r + v)) / np.hypot(1, 0.55)     # a slanted flat worn into the used end
            d = (d + cut + np.sqrt((d - cut) ** 2 + 2.5 ** 2)) / 2        # smooth intersection: rounded edges
            facet = smoothstep(-4.0, -1.0, cut)                          # the worn flat catches more light
        m = np.clip(0.5 - d, 0, 1)
        self._shadow(sl, m, 2.5, 4.5, 2.4, 0.55)
        self._shadow(sl, m, 0.5, 1.5, 0.8, 0.45)
        nv = np.clip(v / r, -1, 1); nz = np.sqrt(np.clip(1 - nv ** 2, 0, 1))
        dif, _ = self._lit(sa * nv, ca * nv, nz)
        s = self._seed()
        nn = int(2 * r + 6)
        stri = np.interp(np.clip(v + r + 3, 0, nn - 1), np.arange(nn), fbm1d(nn, 1.5, 2, s)) * 0.05
        col = _c(colour) * (0.5 + 0.62 * dif - stri + 0.06 * (self.tooth[sl] - 0.5))[..., None]
        fcol = _c(colour) * (0.98 + 0.08 * (self.tooth[sl] - 0.5))[..., None]
        col = col * (1 - facet[..., None]) + fcol * facet[..., None]
        self._front(sl, m, np.clip(col, 0, 1))

    def eraser(self, x, y, w=196, h=50, wood='#7c5433', felt='#4a4b48'):
        """a felt board eraser standing on the ledge, bottom centre at (x, y): wooden back on top, layered felt below,
        caked with chalk (thickest near the working face), with its shadow on the tray"""
        x0, y0 = x - w / 2, y - h
        sl = self._box(x0 - 30, y0 - 20, x0 + w + 30, y + 16)
        X, Y = self.XX[sl], self.YY[sl]
        u, v = X - x, Y - (y0 + h / 2)
        m = np.clip(0.5 - _sdf_rrect(u, v, w / 2, h / 2, 3.5), 0, 1)
        self._shadow(sl, m, 5, 5, 4, 0.5)
        self._shadow(sl, m, 1, 2, 1.2, 0.5)
        yy = Y - y0
        split = h * 0.46
        # wooden back: rounded top edge, grain along its length
        wt = self._wood(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start, wood, '#3a2414', self._seed())
        ny = -(1 - smoothstep(0, 7, yy)) * 0.9 + 0.5 * smoothstep(split - 5, split, yy)
        nx = -(1 - smoothstep(0, 5, X - x0)) * 0.6 + 0.6 * smoothstep(w - 5, w, X - x0)
        nz = np.sqrt(np.clip(1 - ny ** 2 - nx ** 2, 0.05, 1))
        dif, sp = self._lit(nx, ny, nz, 0.14, 26)
        wd = wt * (0.3 + 0.9 * dif)[..., None] + sp[..., None]
        # felt: stacked layers, chalk caked in horizontal streaks, heavier toward the bottom
        s = self._seed()
        hh, ww = X.shape
        fib = blur(self.rng.random((hh, ww)).astype(np.float32), 0.7)          # matt felt: fine, non-directional
        fib = (fib - fib.mean()) / (fib.std() + 1e-6)
        blot = noise2d(hh, ww, 11, 3, s + 1)
        seams = 1 - 0.22 * (np.exp(-((yy - split - (h - split) * 0.36) / 0.8) ** 2) + np.exp(-((yy - split - (h - split) * 0.7) / 0.8) ** 2))
        caked = smoothstep(0.35, 0.75, blot * 0.8 + 0.45 * smoothstep(split + 2, h, yy))  # chalk worked into the felt
        dust = np.clip(0.12 + 0.62 * caked + 0.05 * fib, 0, 0.82)
        fc = _c(felt) * (1 + 0.1 * fib)[..., None] * seams[..., None] * (1 - 0.3 * smoothstep(h - 5, h, yy))[..., None]
        fc = fc * (1 - dust[..., None]) + _c(DUST) * (0.74 + 0.06 * fib)[..., None] * dust[..., None]
        col = np.where((yy < split)[..., None], wd, fc)
        col = col * (1 - 0.4 * np.exp(-((yy - split) / 1.1) ** 2))[..., None]
        self._front(sl, m, np.clip(col, 0, 1))

    def crumbs(self, x0, x1, n=18, colours=(WHITE, WHITE, YELLOW, PINK, BLUE)):
        """little broken bits of chalk lying in the tray"""
        r = self.rng
        for i in range(n):
            x = r.uniform(x0, x1); rr = r.uniform(1.4, 3.6)
            y = self.tray_y - rr * 0.6 + r.uniform(-4, 2)
            sl = self._box(x - 8, y - 8, x + 9, y + 9)
            X, Y = self.XX[sl] - x, self.YY[sl] - y
            th = np.arctan2(Y, X)
            rad = rr * (1 + 0.14 * np.sin(2 * th + r.uniform(0, 6)) + 0.09 * np.sin(3 * th + r.uniform(0, 6)))
            m = np.clip(rad - np.hypot(X, Y * 1.35) + 0.5, 0, 1)
            self._shadow(sl, m, 1.2, 1.6, 1.0, 0.45)
            lit = np.clip(0.8 - 0.3 * Y / rr - 0.1 * X / rr, 0.45, 1.05)
            self._front(sl, m, np.clip(_c(r.choice(colours)) * lit[..., None], 0, 1))

    # ------------------------------------------------------------ output
    def composite(self, vignette=0.26):
        W, H = self.W, self.H
        lamp = 1 + 0.08 * np.exp(-(((self.XX - 0.34 * W) / (0.6 * W)) ** 2 + ((self.YY - 0.18 * H) / (0.65 * H)) ** 2))
        img = (self.paint * (1 - self.ca[..., None]) + self.cc) * lamp[..., None]
        img = img * (1 - self.ta[..., None]) + self.tc
        r = np.hypot((self.XX - W * 0.5) / W, (self.YY - H * 0.45) / H)
        img = img * (1 - vignette * r ** 2 * 2.2)[..., None]
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
