"""lineart — continuous single-line drawing (one-line art): one unbroken line draws the whole picture, with a
single accent colour and a lot of empty space (numpy + Pillow only).

Model: one pen that never leaves the paper.
  path       the drawing is ONE path. Shapes are built as polylines (ruled corners get a small fillet: a hand
             moving at speed rounds every corner a little), Catmull-Rom splines (organic parts), scalloped
             outlines (canopies, bushes) and loop-the-loops laid along the path (`curl`), then
             `chain()` strings them together in drawing order. Where one shape ends away from where the next
             begins, the pen does not lift: a cubic bridge leaves along the old tangent and arrives along the new
             one. Where a shape has to be reached "from inside" (a window hung off a wall), the pen goes in and
             comes back over the same stretch -- a retrace is invisible in the final picture. The whole path is
             resampled to 1 px steps, so everything downstream works in arc length s (px).
  pressure   width follows the hand, not a ruler: a light touch-down taper at the start and a longer lift-off at
             the end, a slow drift of pressure along the line (+-9 %), the pen slowing down -- and so laying
             more ink -- where the path turns sharply (corners and tight loops get up to ~25 % heavier), and a
             light flick wherever it doubles straight back (a retraced stub ends in a point, not a blunt cap).
             Whole stretches can be drawn with a lighter or heavier hand (`pressure=[(s0, s1, factor)]`): a
             motion path at ~0.6 reads as a trajectory, not as one more object.
  ink        the line is rasterised once into a time map: every sub-pixel stores the arc length at which the pen
             first covered it (dabs stamped from the end backwards, so the earliest pass wins at crossings). Any
             prefix of the drawing -- "the pen has travelled s px" -- is then just `time <= s`, which is what
             makes draw-on stages cheap and exact. Supersampled 4x for clean anti-aliased edges.
  metal      on a dark ground the line is a thin gilded wire: its colour runs from old gold to pale champagne with
             the angle between the line and a light from the upper left (anisotropic sheen) plus a slow drift along
             its length, and it gives off a faint, tight glow (three small blurs, never a neon bloom). On cream
             paper it is a dark ink line with no glow.
  pen tip    while the drawing is unfinished, the last ~120 px of line are still "hot" (brighter, a stronger
             glow) and the head carries a small spark -- the tell-tale of a line being drawn.
  accent     exactly one filled shape in one accent colour (a lit window, a sun, a seal), revealed at the end; on
             a dark ground it glows softly and warms the nearby line.
  type       letter-spaced display serif (Didot / Bodoni / Baskerville, else any serif) and a light Song-style CJK
             face for a quiet caption; centred under the drawing.
Colours: GOLD / GOLD_HI / GOLD_LO for the wire, AMBER (warm light) and VERMILION (seal red) as accents,
NIGHT (deep navy) and CREAM grounds, INK for a dark line on cream. Angles are screen degrees (clockwise, y down).

    from lineart import LineArt, AMBER
    la = LineArt(1920, 1080, seed=1)
    la.backdrop('night')
    P, marks = la.chain([('ground', LineArt.smooth([(200, 700), (600, 705), (900, 700)])),
                         ('box', LineArt.poly([(900, 700), (900, 560), (1100, 560), (1100, 700)], r=5)),
                         ('tail', LineArt.smooth([(1100, 700), (1400, 706), (1700, 700)]))])
    la.line(P, width=3.2)
    la.draw_to(marks['box']); la.stage('box')          # the pen has reached the end of the box
    la.draw_to(None); la.accent(la.rect(960, 600, 1040, 660), AMBER)
    la.text('ONE LINE', 960, 860, 44, font='display', spacing=14)
    la.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font, cjk_font, text_mask

GOLD, GOLD_HI, GOLD_LO = '#dcc28c', '#fbf0d2', '#8f7040'
AMBER, VERMILION = '#ffb257', '#d4553a'
NIGHT, CREAM, INK = '#172540', '#f1e9da', '#2a2b33'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _cumlen(P):
    return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))]).astype(np.float64)


def _is_cjk(s):
    return any(ord(ch) >= 0x2e80 for ch in s)


_DISPLAY = [('/System/Library/Fonts/Supplemental/Didot.ttc', 0), ('/System/Library/Fonts/Supplemental/Bodoni 72.ttc', 0),
            ('/System/Library/Fonts/Supplemental/Baskerville.ttc', 0), ('/usr/share/fonts/**/*Playfair*Regular*.ttf', 0),
            ('/usr/share/fonts/**/DejaVuSerif.ttf', 0), ('C:/Windows/Fonts/bod_r.ttf', 0), ('C:/Windows/Fonts/georgia.ttf', 0)]
_CJK_SERIF = [('/System/Library/Fonts/Supplemental/Songti.ttc', 3), ('/usr/share/fonts/**/NotoSerifCJK*Light*.tt[cf]', 0),
              ('/usr/share/fonts/**/NotoSerifCJK*.tt[cf]', 0), ('C:/Windows/Fonts/simsun.ttc', 0)]


def _find_font(cands, size):
    for pat, idx in cands:
        for f in glob.glob(pat, recursive=True):
            try:
                return ImageFont.truetype(f, int(size), index=idx)
            except OSError:
                continue
    return None


class LineArt:
    def __init__(self, W=1920, H=1080, seed=0, ss=4):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.bg = np.full((H, W, 3), 0.1, np.float32)
        self.dark = True
        self.ink, self.accent_colour = GOLD, AMBER
        self.strokes = []                                   # rasterised lines (time maps) with their pen heads
        self.acc_a = np.zeros((H, W), np.float32)           # accent fill: alpha + colour
        self.acc_c = np.zeros((H, W, 3), np.float32)
        self.acc_glow = np.zeros((H, W, 3), np.float32)     # additive light from the accent (dark grounds)
        self.acc_warm = np.zeros((H, W), np.float32)        # how much the accent light tints the nearby line
        self.txt_a = np.zeros((H, W), np.float32)
        self.txt_c = np.zeros((H, W, 3), np.float32)
        self.marks = {}
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ ground
    def backdrop(self, kind='night', colour=None, edge=None, grain=None):
        """kind 'night': deep navy, lighter in the middle (like a dark velvet card under one soft light), fine
        grain; 'cream': warm paper with faint fibres and mottling. Sets the default ink / accent / glow."""
        H, W = self.H, self.W
        r = np.hypot((self.XX - W * 0.5) / (W * 0.62), (self.YY - H * 0.44) / (H * 0.72))
        t = smoothstep(0.0, 1.25, r)[..., None]
        mott = noise2d(H, W, 260, 3, self._seed()) - 0.5
        if kind == 'night':
            self.dark = True
            c0, c1 = _c(colour or NIGHT), _c(edge or '#060a13')
            img = c0 * (1 - t) + c1 * t
            img *= (1 + 0.05 * mott)[..., None]
            img += (smoothstep(0.55, 0.0, self.YY / H) * 0.012)[..., None] * _c('#8fa6d8')   # faint top light
            g = grain if grain is not None else 0.007
            self.ink, self.accent_colour = GOLD, AMBER
        else:
            self.dark = False
            c0, c1 = _c(colour or CREAM), _c(edge or '#e2d6bf')
            img = c0 * (1 - t * 0.8) + c1 * (t * 0.8)
            img *= (1 + 0.035 * mott)[..., None]
            fib = np.asarray(Image.fromarray(self.rng.random((H // 3, W // 40)).astype(np.float32))
                             .resize((W, H), Image.BILINEAR)) - 0.5
            img *= (1 + 0.012 * fib)[..., None]
            g = grain if grain is not None else 0.012
            self.ink, self.accent_colour = INK, VERMILION
        img *= (1 + g * self.rng.normal(0, 1, (H, W)).astype(np.float32))[..., None]
        self.bg = np.clip(img, 0, 1).astype(np.float32)

    # ------------------------------------------------------------ building the one path
    @staticmethod
    def resample(P, step=1.0):
        P = np.asarray(P, np.float64)
        s = _cumlen(P)
        if s[-1] < 1e-6: return P[:1].astype(np.float32)
        n = max(2, int(np.ceil(s[-1] / step)) + 1)
        ss = np.linspace(0, s[-1], n)
        return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)

    @staticmethod
    def length(P):
        return float(_cumlen(np.asarray(P, np.float64))[-1])

    @staticmethod
    def smooth(pts, per=24):
        """Catmull-Rom spline through control points (organic parts: hills, trails, canopies)"""
        return LineArt.resample(spline(pts, per), 1.0)

    @staticmethod
    def poly(pts, r=5.0, sharp=()):
        """polyline with filleted corners (radius r px, clipped to half of each side). Indices in `sharp` stay
        pointed (paper corners, a nose, a spire)."""
        P = np.asarray(pts, np.float64)
        out = [P[0]]
        for i in range(1, len(P) - 1):
            a, b, c = P[i - 1], P[i], P[i + 1]
            d1, d2 = b - a, c - b
            l1, l2 = np.hypot(*d1), np.hypot(*d2)
            rr = 0.0 if i in sharp else min(r, l1 * 0.5, l2 * 0.5)
            if rr < 0.5 or l1 < 1e-6 or l2 < 1e-6:
                out.append(b); continue
            p1, p2 = b - d1 / l1 * rr, b + d2 / l2 * rr
            t = np.linspace(0, 1, 9)[:, None]
            out.extend(list((1 - t) ** 2 * p1 + 2 * (1 - t) * t * b + t ** 2 * p2))
        out.append(P[-1])
        return LineArt.resample(np.array(out), 1.0)

    @staticmethod
    def arc(cx, cy, rx, ry=None, a0=0.0, a1=360.0, step=1.0):
        """elliptical arc from angle a0 to a1 (screen degrees: 0 = right, 90 = down); a1 < a0 runs anticlockwise"""
        ry = rx if ry is None else ry
        n = max(8, int(abs(np.deg2rad(a1 - a0)) * max(rx, ry) / step) + 1)
        a = np.deg2rad(np.linspace(a0, a1, n))
        return np.stack([cx + rx * np.cos(a), cy + ry * np.sin(a)], 1).astype(np.float32)

    @staticmethod
    def scallop(cx, cy, r, a0, a1, bumps=6, depth=0.12, squash=1.0):
        """a scalloped outline (tree canopy, bush, cloud) from angle a0 to a1: `bumps` round lobes meeting in
        small inward cusps, like a hand drawing a cloud in one go"""
        n = max(60, int(abs(np.deg2rad(a1 - a0)) * r * 1.2))
        u = np.linspace(0, 1, n)
        a = np.deg2rad(a0 + (a1 - a0) * u)
        rr = r * (1 - depth + depth * 1.6 * np.abs(np.sin(np.pi * bumps * u)) ** 0.7)
        return LineArt.resample(np.stack([cx + rr * np.cos(a), cy + rr * np.sin(a) * squash], 1), 1.0)

    @staticmethod
    def place(pts, origin, angle=0.0, scale=1.0):
        """move a shape drawn in local coordinates: rotate by `angle` (screen degrees, clockwise), scale, then
        put its (0, 0) at `origin`"""
        P = np.asarray(pts, np.float64) * scale
        a = np.deg2rad(angle)
        x = P[:, 0] * np.cos(a) - P[:, 1] * np.sin(a)
        y = P[:, 0] * np.sin(a) + P[:, 1] * np.cos(a)
        return np.stack([x + origin[0], y + origin[1]], 1).astype(np.float32)

    @staticmethod
    def curl(P, s, r, span=None, side=1, aspect=1.0):
        """insert a loop-the-loop into path P at arc length s: the pen runs on, swings round a near-circle of
        radius r on `side` (+1 = left of the direction of travel, i.e. 'up' when moving right, -1 = the other
        side) and crosses its own track before carrying on (a prolate cycloid laid along the path).
        aspect > 1 makes the loop rounder along the direction of travel (useful where the path is bending)."""
        P = LineArt.resample(P, 1.0).astype(np.float64)
        sc = _cumlen(P)
        span = 1.1 * r if span is None else span
        n = int(2 * np.pi * r * 1.6) + 8
        u = np.linspace(0, 1, n)
        sb = s + u * span
        bx, by = np.interp(sb, sc, P[:, 0]), np.interp(sb, sc, P[:, 1])
        tx = np.interp(sb + 1.5, sc, P[:, 0]) - np.interp(sb - 1.5, sc, P[:, 0])
        ty = np.interp(sb + 1.5, sc, P[:, 1]) - np.interp(sb - 1.5, sc, P[:, 1])
        tl = np.hypot(tx, ty) + 1e-9; tx, ty = tx / tl, ty / tl
        nx, ny = side * ty, -side * tx
        ph = 2 * np.pi * u
        ox, oy = r * aspect * np.sin(ph), r * (1 - np.cos(ph))
        loop = np.stack([bx + tx * ox + nx * oy, by + ty * ox + ny * oy], 1)
        return LineArt.resample(np.vstack([P[sc < s], loop, P[sc > s + span]]), 1.0)

    @staticmethod
    def retrace(pts):
        """go out along a stretch and come back over it (a hill shoulder, a window sill): the pen never lifts,
        and the doubled stretch is invisible in the finished picture"""
        Q = np.asarray(pts, np.float32)
        return np.vstack([Q, Q[::-1][1:]])

    @staticmethod
    def _bridge(p0, t0, p3, t3, k=0.42):
        d = float(np.hypot(*(p3 - p0)))
        c1, c2 = p0 + t0 * d * k, p3 - t3 * d * k
        t = np.linspace(0, 1, max(4, int(d * 1.5)))[:, None]
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p3

    def chain(self, parts, bridge=0.42):
        """string shapes into ONE continuous path, in drawing order. parts: [(name, pts), ...] (or bare pts).
        Gaps are closed with a tangent-continuous cubic bridge (the pen never lifts). Returns (P, marks):
        P resampled at 1 px, marks[name] = arc length (px) at the end of that part (use it for stages)."""
        def tan(A, end):
            B = A[-min(len(A), 6):] if end else A[:min(len(A), 6)]
            d = B[-1] - B[0]
            n = np.hypot(*d)
            return d / n if n > 1e-6 else np.zeros(2)
        out, ends = [], []
        for i, part in enumerate(parts):
            name, pts = part if isinstance(part, tuple) else (f'part{i}', part)
            Q = np.asarray(pts, np.float64)
            if out:
                p0 = out[-1][-1]
                if np.hypot(*(Q[0] - p0)) > 1.0:
                    prev = np.vstack(out[-3:])
                    out.append(self._bridge(p0, tan(prev, True), Q[0], tan(Q, False), bridge)[1:-1])
            out.append(Q)
            ends.append((name, sum(len(o) for o in out) - 1))
        P = np.vstack(out)
        s = _cumlen(P)
        marks = {name: float(s[idx]) for name, idx in ends}
        self.marks.update(marks)
        return self.resample(P, 1.0), marks

    @staticmethod
    def trim(P, s0=0.0, s1=None):
        """the stretch of path P between arc lengths s0 and s1 (px)"""
        P = np.asarray(P, np.float64)
        s = _cumlen(P)
        s1 = s[-1] if s1 is None else min(s1, s[-1])
        s0 = max(0.0, s0)
        if s1 <= s0: return P[:1].astype(np.float32)
        inner = (s > s0) & (s < s1)
        a = np.array([np.interp(s0, s, P[:, 0]), np.interp(s0, s, P[:, 1])])
        b = np.array([np.interp(s1, s, P[:, 0]), np.interp(s1, s, P[:, 1])])
        return np.vstack([a, P[inner], b]).astype(np.float32)

    @staticmethod
    def locate(P, xy):
        """arc length (px) of the point of P closest to xy -- for placing a curl or a stage by eye"""
        P = np.asarray(P, np.float64)
        i = int(np.argmin(np.hypot(P[:, 0] - xy[0], P[:, 1] - xy[1])))
        return float(_cumlen(P)[i])

    @staticmethod
    def at(P, s):
        """point and heading (screen degrees) at arc length s"""
        P = np.asarray(P, np.float64)
        sc = _cumlen(P)
        x, y = np.interp(s, sc, P[:, 0]), np.interp(s, sc, P[:, 1])
        x2, y2 = np.interp(s + 2, sc, P[:, 0]), np.interp(s + 2, sc, P[:, 1])
        x1, y1 = np.interp(s - 2, sc, P[:, 0]), np.interp(s - 2, sc, P[:, 1])
        return (float(x), float(y)), float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))

    # ------------------------------------------------------------ pressure and ink
    def pressure(self, P, width=3.2, taper=(50, 150), drift=0.09, slow=0.25, flick=36, spans=None, ramp=60):
        """width (px) at every point of P: touch-down / lift-off tapers, slow pressure drift, more ink where the
        pen slows down in sharp turns, and a light flick wherever the pen doubles straight back on itself (the
        tip of a retraced stub comes out tapered, not blunt). spans = [(s0, s1, factor), ...]: the hand eases
        off (factor < 1) or bears down (> 1) between arc lengths s0 and s1, easing in and out over `ramp` px --
        e.g. a lighter line for a motion path than for the objects it connects."""
        P = np.asarray(P, np.float64)
        s = _cumlen(P); L = s[-1]; n = len(P)
        d = np.gradient(P, axis=0)
        th = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
        k = np.abs(np.gradient(th)) / np.maximum(np.gradient(s), 1e-3)
        win = 9
        k = np.convolve(np.pad(k, win, mode='edge'), np.ones(2 * win + 1) / (2 * win + 1), 'same')[win:-win]
        w = np.full(n, width, np.float64)
        for s0, s1, f in (spans or ()):
            w *= 1 + (f - 1) * smoothstep(s0 - ramp / 2, s0 + ramp / 2, s) * (1 - smoothstep(s1 - ramp / 2, s1 + ramp / 2, s))
        w *= 1 + slow * smoothstep(0.01, 0.16, k)
        w *= 1 + drift * fbm1d(n, 320, 3, self._seed())
        if flick:
            h = 8                                                        # samples (P is resampled at 0.5 px)
            a, b = P[h:-h] - P[:-2 * h], P[2 * h:] - P[h:-h]
            cosang = (a * b).sum(1) / (np.hypot(*a.T) * np.hypot(*b.T) + 1e-9)
            idx = np.nonzero(cosang < -0.985)[0] + h
            if len(idx):
                groups = np.split(idx, np.nonzero(np.diff(idx) > 4)[0] + 1)
                for g in groups:
                    sc = s[int(np.round(g.mean()))]
                    w *= 0.22 + 0.78 * smoothstep(0, flick, np.abs(s - sc))
        w *= 0.3 + 0.7 * smoothstep(0, taper[0], s)
        w *= 0.1 + 0.9 * smoothstep(0, taper[1], L - s)
        return w.astype(np.float32), th

    def line(self, P, width=3.2, colour=None, taper=(50, 150), sheen=0.32, glow=1.0, light=225.0, hot=120.0,
             pressure=None):
        """ink the path P as one pressure-sensitive line (fully drawn until draw_to() says otherwise).
        colour: base ink (default: gold on night, INK on cream); sheen: strength of the angle-dependent metallic
        highlight (dark grounds); glow: multiplier on the soft light round the line; light: direction the light
        comes from (screen degrees); hot: length (px) of the still-bright fresh stretch behind the pen tip;
        pressure: [(s0, s1, factor), ...] spans where the hand is lighter or heavier (see pressure())."""
        P = self.resample(P, 0.5)
        s = _cumlen(P).astype(np.float32)
        w, th = self.pressure(P, width, taper, spans=pressure)
        ss = self.ss
        pad = float(w.max()) + 3
        x0, y0 = max(0, int(P[:, 0].min() - pad)), max(0, int(P[:, 1].min() - pad))
        x1, y1 = min(self.W, int(P[:, 0].max() + pad) + 1), min(self.H, int(P[:, 1].max() + pad) + 1)
        tm = Image.new('F', ((x1 - x0) * ss, (y1 - y0) * ss), 1e9)
        dr = ImageDraw.Draw(tm)
        X, Y, R = (P[:, 0] - x0) * ss, (P[:, 1] - y0) * ss, np.maximum(w * 0.5 * ss, 0.7)
        for i in range(len(P) - 1, -1, -1):                 # backwards: the earliest pass wins at crossings
            dr.ellipse((X[i] - R[i], Y[i] - R[i], X[i] + R[i], Y[i] + R[i]), fill=float(s[i]))
        # metallic sheen: a thin wire is brightest where it runs across the light, plus a slow drift
        lt = np.deg2rad(light)
        b = 0.55 + sheen * np.sin(th - lt) ** 2 * 1.4 - sheen * 0.7 + 0.1 * fbm1d(len(P), 900, 3, self._seed())
        self.strokes.append(dict(P=P, s=s, L=float(s[-1]), box=(x0, y0, x1, y1), tmap=np.asarray(tm, np.float32),
                                 bright=np.clip(b, 0, 1).astype(np.float32), colour=colour, glow=glow, hot=hot,
                                 head=float(s[-1])))
        return len(self.strokes) - 1

    def draw_to(self, s=None, stroke=-1):
        """move the pen head of a stroke to arc length s (px) or to a mark name; None = finished"""
        st = self.strokes[stroke]
        if isinstance(s, str): s = self.marks[s]
        st['head'] = st['L'] if s is None else float(np.clip(s, 0, st['L']))

    def _stroke_layer(self, st):
        """coverage, colour and glow weight of one stroke up to its pen head (cropped to its box)"""
        ss = self.ss
        x0, y0, x1, y1 = st['box']
        h, w = y1 - y0, x1 - x0
        head = st['head']
        m = st['tmap'] <= head
        cov = m.reshape(h, ss, w, ss).mean((1, 3))
        tsum = np.where(m, st['tmap'], 0).reshape(h, ss, w, ss).sum((1, 3))
        tt = tsum / np.maximum(cov * ss * ss, 1)
        bright = np.interp(tt, st['s'], st['bright']).astype(np.float32)
        live = head < st['L'] - 0.5
        hot = (np.exp(-np.clip(head - tt, 0, None) / st['hot']) * (cov > 0)).astype(np.float32) if live else None
        return (slice(y0, y1), slice(x0, x1)), cov.astype(np.float32), bright, hot

    # ------------------------------------------------------------ accent, marks, type
    def _ss_mask(self, box, draw, ss=4):
        """anti-aliased mask drawn by draw(ImageDraw, to_ss) at 4x inside box = (x0, y0, x1, y1), pasted on canvas"""
        x0, y0 = max(0, int(np.floor(box[0])) - 2), max(0, int(np.floor(box[1])) - 2)
        x1, y1 = min(self.W, int(np.ceil(box[2])) + 3), min(self.H, int(np.ceil(box[3])) + 3)
        out = np.zeros((self.H, self.W), np.float32)
        if x1 <= x0 or y1 <= y0: return out
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        draw(ImageDraw.Draw(im), lambda x, y: ((x - x0) * ss, (y - y0) * ss))
        out[y0:y1, x0:x1] = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return out

    def rect(self, x0, y0, x1, y1, r=0.0):
        """anti-aliased (rounded) rectangle mask"""
        return self._ss_mask((x0, y0, x1, y1), lambda d, T: d.rounded_rectangle([*T(x0, y0), *T(x1, y1)],
                                                                                 radius=r * 4, fill=255))

    def disc(self, cx, cy, r):
        """anti-aliased disc mask (a sun, a moon, a seal)"""
        return np.clip(r + 0.5 - np.hypot(self.XX - cx, self.YY - cy), 0, 1)

    def accent(self, mask, colour=None, glow=1.0, inner=0.25, warm=0.55):
        """the one point of colour: fill `mask` with the accent colour, lighter toward its middle (`inner`);
        on a dark ground it glows (`glow`) and warms the line around it (`warm`)"""
        col = _c(colour or self.accent_colour)
        m = np.clip(mask, 0, 1).astype(np.float32)
        ys, xs = np.nonzero(m > 0.01)
        if len(xs) == 0: return
        cx, cy = xs.mean(), ys.mean()
        rad = max(xs.max() - xs.min(), ys.max() - ys.min()) * 0.6 + 1
        lift = inner * np.exp(-((self.XX - cx) ** 2 + (self.YY - cy) ** 2) / (2 * rad * rad))
        fill = col[None, None, :] * (1 - inner * 0.6) + (1 - col[None, None, :]) * lift[..., None] * 0.5 + col * lift[..., None] * 0.6
        self.acc_c = self.acc_c * (1 - m[..., None]) + np.clip(fill, 0, 1) * m[..., None]
        self.acc_a = np.maximum(self.acc_a, m)
        if self.dark and glow > 0:
            g = blur(m, 6) * 0.45 + blur(m, 22) * 0.3 + blur(m, 70) * 0.16
            self.acc_glow += g[..., None] * col * glow
            self.acc_warm = np.maximum(self.acc_warm, np.clip(blur(m, 26) * 2.2, 0, 1) * warm)

    def _font(self, s, size, font):
        if font == 'display' and not _is_cjk(s):
            f = _find_font(_DISPLAY, size)
            if f: return f
        if _is_cjk(s):
            f = _find_font(_CJK_SERIF, size)
            if f: return f
            p = cjk_font()
            if p: return ImageFont.truetype(p, int(size))
        return load_font('serif' if font in ('display', 'serif') else font, size)

    def text(self, s, x, y, size, colour=None, font='display', anchor='ms', spacing=0.0, alpha=1.0):
        """quiet lettering: font 'display' (Didot-like serif, CJK falls back to a light Song face), 'serif',
        'sans'; spacing = extra px between letters (letter-spaced caps)"""
        f = self._font(s, size, font)
        m = text_mask(self.H, self.W, s, f, (x, y), anchor, spacing) * alpha
        col = _c(colour or (GOLD if self.dark else INK))
        self.txt_c = self.txt_c * (1 - m[..., None]) + col * m[..., None]
        self.txt_a = np.maximum(self.txt_a, m)

    def text_width(self, s, size, font='display', spacing=0.0):
        f = self._font(s, size, font)
        return sum(f.getlength(ch) + spacing for ch in s) - spacing

    def hairline(self, x0, y0, x1, y1, width=1.2, colour=None, alpha=0.7):
        """a thin typographic rule (beside a caption), not part of the drawing's line"""
        box = (min(x0, x1) - width, min(y0, y1) - width, max(x0, x1) + width, max(y0, y1) + width)
        m = self._ss_mask(box, lambda d, T: d.line([T(x0, y0), T(x1, y1)], fill=255, width=max(1, int(width * 4)))) * alpha
        col = _c(colour or (GOLD if self.dark else INK))
        self.txt_c = self.txt_c * (1 - m[..., None]) + col * m[..., None]
        self.txt_a = np.maximum(self.txt_a, m)

    # ------------------------------------------------------------ output
    def composite(self, tip=True):
        img = self.bg.copy()
        if self.dark:
            img += self.acc_glow * (1 - img)                                      # screen-ish light
        a = self.acc_a[..., None]
        img = img * (1 - a) + self.acc_c * a
        glow = np.zeros((self.H, self.W), np.float32)
        tips = []
        for st in self.strokes:
            if st['head'] <= 0: continue
            sl, cov, bright, hot = self._stroke_layer(st)
            if self.dark:
                lo, mid, hi = _c(GOLD_LO), _c(st['colour'] or self.ink), _c(GOLD_HI)
                b = bright[..., None]
                col = np.where(b < 0.5, lo + (mid - lo) * (b * 2), mid + (hi - mid) * (b * 2 - 1))
                if hot is not None:
                    col = col + (_c(GOLD_HI) * 1.05 - col) * (hot[..., None] * 0.85)
                warm = self.acc_warm[sl][..., None]
                col = col * (1 - warm) + (col * 0.35 + _c(self.accent_colour) * 0.75) * warm
                g = cov * (0.55 + 0.45 * bright) * st['glow']
                if hot is not None: g = g * (1 + 2.2 * hot)
                glow[sl] = np.maximum(glow[sl], g)
            else:
                col = np.broadcast_to(_c(st['colour'] or self.ink), cov.shape + (3,))
            c = cov[..., None]
            img[sl] = img[sl] * (1 - c) + np.clip(col, 0, 1.2) * c
            if st['head'] < st['L'] - 0.5:
                tips.append(self.at(st['P'], st['head'])[0])
        if self.dark and glow.any():
            gl = blur(glow, 1.6) * 0.4 + blur(glow, 6) * 0.22 + blur(glow, 20) * 0.09
            img += gl[..., None] * _c(GOLD) * (1 - img)
        if tip and tips:
            for (tx, ty) in tips:
                d2 = (self.XX - tx) ** 2 + (self.YY - ty) ** 2
                if self.dark:
                    spark = np.exp(-d2 / (2 * 2.6 ** 2)) * 1.0 + np.exp(-d2 / (2 * 9 ** 2)) * 0.5 + np.exp(-d2 / (2 * 30 ** 2)) * 0.16
                    img += spark[..., None] * (_c('#fff6e0') * 1.1 - img).clip(0, None) * 0.95
                else:
                    img *= 1 - (np.exp(-d2 / (2 * 2.0 ** 2)) * 0.6)[..., None] * (1 - _c(self.ink))
        t = self.txt_a[..., None]
        img = img * (1 - t) + self.txt_c * t
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite(tip=False)
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=88, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
