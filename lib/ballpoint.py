"""ballpoint — doodling on a sheet of copy paper with ballpoint pens (blue, red, black) and a few coloured pencils:
pen line art, pencil hatching inside it, margin doodles, handwritten notes (numpy + Pillow only).

Model:
  paper     grey-beige copy paper. A fine `tooth` height field (smoother than drawing paper), sparse fibres and
            a faint mottle; the sheet is not flat: low cockles and optional fold creases (a sharp valley with the
            two sides tilted differently) shade it under a soft light from the top left, and it is photographed,
            so the light falls off a little toward the corners. Nothing shows through from the back.
  ink       ballpoint ink is a thick oil paste that a rolling ball lays down. A line is ~2.3 px wide and almost
            solid; its colour is an optical density (Beer-Lambert), so a line drawn twice, a crossing or a gloop
            gets darker and more saturated (blue goes to a deep blue-violet), never flat black. How a stroke goes:
              start   the ball is dry for the first few px: thin, pale and grainy (ink only on the tooth peaks);
              body    pressure drifts +-12 %; the width follows it a little; hand tremor and, on long straight
                      lines, a slight bow;
              skips   here and there the ball stops feeding for 2-9 px: a pale gap, but the groove is still there;
              gloops  excess paste builds up on the ball and is dropped as a dark blob where the pen stops, at
                      sharp turns, sometimes where it starts and every few hundred px on long lines;
              end     a quick flick as the pen lifts (`hook`): the line curls back 90-160 degrees over 3-7 px;
              twice   a line gone over again lands 0.6-1.6 px off the first one for part of its length.
  grooves   every stroke presses a groove into the paper (deeper with pressure, a little for pencil too). The
            height field is lit from the top left: the upper-left wall of a groove darkens, the lower-right wall
            catches light. `emboss` / `write(blind=True)` press grooves with no ink -- the ghost of writing done on
            the sheet that lay on top.
  pencil    coloured pencil is wax pigment that only sticks to the tooth it touches: light pressure grazes the
            peaks (grainy, pale), hard pressure fills the valleys. It is laid as quick parallel hatching (`pencil`),
            one patch at a time, strokes a little bowed, heavier in the middle than at the ends, running past the
            outline (`overshoot`) and changing direction from patch to patch; big areas light, small ones heavy.
            Layers multiply. `pen_hatch` is the same in ink: back-and-forth zigzag shading with gloops at the turns.
  writing   the centre lines of a thin handwriting font (Zhang-Suen skeleton traced into pen paths, cached per
            character) are re-drawn as pen strokes: each letter re-sized, tilted and lifted off a wandering
            baseline, slanted, with pressure, start fade, gloops and hooks of its own. `strike` scribbles a word out.
  doodles   `face` (inked eyes with a highlight, mouth, pencil blush), `eye`, `dot`, `dashes`, `arrow`, `ring`
            (a loose red-pen circle that overshoots), and point helpers `circle_pts`, `star_pts`, `cloud_pts`,
            `spiral_pts`, `heart_pts`.

    import sys; sys.path.insert(0, 'lib')
    from ballpoint import Ballpoint
    b = Ballpoint(1920, 1080, seed=4)
    b.paper()
    m = b.ellipse(960, 540, 160, 120)
    b.line(b.circle_pts(960, 540, 160, 120), 'blue', closed=True, twice=0.6)
    b.pencil(m, 'yellow', angle=60, pressure=0.45)
    b.face(960, 540, 90)
    b.write('hello there', 820, 760, 44, 'red')
    b.save('doodle.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from core import blur, fbm1d, spline, noise2d, smoothstep, latin_font

# single-pass reflectance of a ballpoint line on white paper (its optical density is -ln of this)
PENS = {
    'blue': (0.20, 0.235, 0.62),
    'red': (0.80, 0.19, 0.21),
    'black': (0.215, 0.20, 0.205),
}
# what heavily pressed coloured pencil looks like (light pressure gives a paler, grainier version)
PENCILS = {
    'leaf': '#4f9a3e', 'green': '#6fb04c', 'lime': '#a5cc4e', 'mint': '#8ccfa6', 'teal': '#3f9e9a',
    'sky': '#79b2e4', 'blue': '#3c6cc4', 'violet': '#8566c4', 'lilac': '#b49ddf', 'pink': '#ef86a6',
    'rose': '#e2557a', 'red': '#d6403a', 'orange': '#f0862e', 'peach': '#f5b088', 'yellow': '#f5cf34',
    'ochre': '#d39d3a', 'brown': '#97603a', 'tan': '#d8b07c', 'grey': '#9b9a98', 'cream': '#efdcae',
}
PAPER = '#e6e1d4'
SHEEN = (0.42, 0.36, 0.50)          # what heavily worked ballpoint ink reflects (a dull violet-bronze)
LIGHT = (-0.6, -0.8)                # toward the light, in the image plane: top left

_THIN_HAND = [('/System/Library/Fonts/Noteworthy.ttc', 0), ('/System/Library/Fonts/Supplemental/ChalkboardSE.ttc', 0),
              ('/System/Library/Fonts/MarkerFelt.ttc', 0), ('/usr/share/fonts/**/*Kalam*Light*.ttf', 0),
              ('/usr/share/fonts/**/*Caveat*.ttf', 0), ('C:/Windows/Fonts/segoepr.ttf', 0), ('C:/Windows/Fonts/comic.ttf', 0)]
_THIN_CJK = [('/System/Library/Fonts/STHeiti Light.ttc', 1), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
             ('/usr/share/fonts/**/NotoSansCJK*Light*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSansCJK*Regular*.tt[cf]', 0),
             ('C:/Windows/Fonts/msyhl.ttc', 0), ('C:/Windows/Fonts/msyh.ttc', 0)]
_GS = 160                            # glyphs are skeletonised at this size
_FONTS = {}
_GLYPHS = {}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _font(kind):
    """thin handwriting font for 'latin' or 'cjk' ($INKPAINT_FONT_BALLPOINT / _BALLPOINT_CJK override)"""
    if kind in _FONTS: return _FONTS[kind]
    env = os.environ.get('INKPAINT_FONT_BALLPOINT' + ('_CJK' if kind == 'cjk' else ''))
    cands = [(env, 0)] if env and os.path.exists(env) else []
    for pat, idx in (_THIN_CJK if kind == 'cjk' else _THIN_HAND):
        fs = glob.glob(pat, recursive=True)
        if fs: cands.append((fs[0], idx))
    hit = latin_font('cjk' if kind == 'cjk' else 'hand')
    if hit: cands.append(hit)
    f = None
    for path, idx in cands:
        try:
            f = ImageFont.truetype(path, _GS, index=idx); break
        except OSError:
            continue
    _FONTS[kind] = f or ImageFont.load_default(_GS)
    return _FONTS[kind]


def _thin(b):
    """Zhang-Suen thinning: boolean glyph -> one-pixel centre line"""
    I = b.astype(np.uint8).copy()
    changed = True
    while changed:
        changed = False
        for step in range(2):
            P = np.pad(I, 1)
            p2, p3, p4, p5 = P[:-2, 1:-1], P[:-2, 2:], P[1:-1, 2:], P[2:, 2:]
            p6, p7, p8, p9 = P[2:, 1:-1], P[2:, :-2], P[1:-1, :-2], P[:-2, :-2]
            nb = [p2, p3, p4, p5, p6, p7, p8, p9, p2]
            B = sum(x.astype(np.int32) for x in nb[:8])
            A = sum(((nb[i] == 0) & (nb[i + 1] == 1)).astype(np.int32) for i in range(8))
            c1, c2 = (p2 * p4 * p6, p4 * p6 * p8) if step == 0 else (p2 * p4 * p8, p2 * p6 * p8)
            m = (I == 1) & (B >= 2) & (B <= 6) & (A == 1) & (c1 == 0) & (c2 == 0)
            if m.any():
                I[m] = 0; changed = True
    # staircase corners: a pixel whose only two neighbours are an orthogonal pair (N+E ...) is redundant
    for _ in range(2):
        P = np.pad(I, 1)
        n, s, e, w = P[:-2, 1:-1], P[2:, 1:-1], P[1:-1, 2:], P[1:-1, :-2]
        tot = sum(x.astype(np.int32) for x in (n, s, e, w, P[:-2, 2:], P[2:, 2:], P[2:, :-2], P[:-2, :-2]))
        corner = (I == 1) & (tot == 2) & (((n & e) | (e & s) | (s & w) | (w & n)) == 1)
        ys, xs = np.nonzero(corner)
        for y, x in zip(ys[::2], xs[::2]):        # every other one: never remove two touching pixels at once
            I[y, x] = 0
    return I.astype(bool)


_NB = [(-1, 0), (0, 1), (1, 0), (0, -1), (-1, 1), (1, 1), (1, -1), (-1, -1)]


def _trace(sk):
    """skeleton pixels -> list of pixel paths (endpoints first, then branches from junctions, then loops)"""
    pix = set(zip(*[a.tolist() for a in np.nonzero(sk)]))
    nbrs = lambda p: [(p[0] + dy, p[1] + dx) for dy, dx in _NB if (p[0] + dy, p[1] + dx) in pix]
    seen, paths = set(), []

    def walk(start):
        path, cur, d = [start], start, None
        seen.add(start)
        while True:
            cand = [q for q in nbrs(cur) if q not in seen]
            if not cand: break
            if d is None:
                q = min(cand, key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
            else:
                q = max(cand, key=lambda q: ((q[0] - cur[0]) * d[0] + (q[1] - cur[1]) * d[1]) / np.hypot(q[0] - cur[0], q[1] - cur[1]))
            nd = np.array([q[0] - cur[0], q[1] - cur[1]], np.float32); nd /= np.linalg.norm(nd)
            d = nd if d is None else 0.55 * d + 0.45 * nd
            d = d / (np.linalg.norm(d) + 1e-9)
            seen.add(q); path.append(q); cur = q
        return path

    for e in sorted([p for p in pix if len(nbrs(p)) == 1], key=lambda p: (p[1] + p[0] * 0.4)):
        if e not in seen: paths.append(walk(e))
    while True:
        rest = [p for p in pix if p not in seen]
        if not rest: break
        touching = [p for p in rest if any(q in seen for q in nbrs(p))]
        s = min(touching or rest)
        path = walk(s)
        anchor = [q for q in nbrs(s) if q in seen and q not in path]
        if anchor: path = [anchor[0]] + path
        if len(path) > 3:
            close = [q for q in nbrs(path[-1]) if q in seen and q != path[-2]]
            if close: path.append(close[0])
        paths.append(path)
    return paths


def _components(sk):
    """label 8-connected components of a small boolean image -> list of pixel-coordinate arrays"""
    pix = set(zip(*[a.tolist() for a in np.nonzero(sk)]))
    comps = []
    while pix:
        st = [pix.pop()]; comp = list(st)
        while st:
            p = st.pop()
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (p[0] + dy, p[1] + dx)
                    if q in pix:
                        pix.remove(q); st.append(q); comp.append(q)
        comps.append(np.array(comp))
    return comps


def _smooth(P, k=2, it=2):
    P = np.asarray(P, np.float32)
    if len(P) < 5: return P
    for _ in range(it):
        Q = P.copy()
        for i in range(1, len(P) - 1):
            a, b = max(0, i - k), min(len(P), i + k + 1)
            Q[i] = P[a:b].mean(0)
        P = Q
    return P


def _resample(P, step):
    P = np.asarray(P, np.float32)
    if len(P) < 2: return P
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(s[-1] / step) + 1)
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1).astype(np.float32)


def _closed_spline(P, per=8):
    P = np.asarray(P, np.float32)
    n = len(P)
    E = np.vstack([P[-1:], P, P[:2]])
    out = []
    for i in range(1, n + 1):
        p0, p1, p2, p3 = E[i - 1], E[i], E[i + 1], E[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[0])
    return np.array(out, np.float32)


def _glyph(ch):
    """(paths, dots, advance) of one character, normalised to size 1, baseline at y = 0, origin at x = 0"""
    if ch in _GLYPHS: return _GLYPHS[ch]
    kind = 'cjk' if ord(ch) >= 0x2E80 else 'latin'
    f = _font(kind)
    adv = f.getlength(ch) / _GS
    if not ch.strip():
        _GLYPHS[ch] = ([], [], adv); return _GLYPHS[ch]
    S = int(_GS * 1.9); ox, oy = int(_GS * 0.4), int(_GS * 1.3)
    im = Image.new('L', (S, S), 0)
    ImageDraw.Draw(im).text((ox, oy), ch, font=f, fill=255, anchor='ls')
    g = np.asarray(im) > 110
    if kind == 'cjk':
        g = np.asarray(im.filter(ImageFilter.MaxFilter(3))) > 110
    sk = _thin(g)
    paths, dots = [], []
    for comp in _components(sk):
        h, w = np.ptp(comp[:, 0]), np.ptp(comp[:, 1])
        if max(h, w) < 0.11 * _GS:
            c = comp.mean(0); dots.append(((c[1] - ox) / _GS, (c[0] - oy) / _GS))
            continue
        sub = np.zeros_like(sk); sub[comp[:, 0], comp[:, 1]] = True
        for p in _trace(sub):
            P = np.array([(x, y) for y, x in p], np.float32)
            L = np.hypot(*np.diff(P, axis=0).T).sum() if len(P) > 1 else 0
            if L < 0.07 * _GS: continue
            P = _resample(_smooth(P), 3.0)
            paths.append(np.stack([(P[:, 0] - ox) / _GS, (P[:, 1] - oy) / _GS], 1))
    _GLYPHS[ch] = (paths, dots, adv)
    return _GLYPHS[ch]


class Ballpoint:
    PENS = PENS
    PENCILS = PENCILS

    def __init__(self, W=1920, H=1080, seed=0, ss=2, pen_width=2.5):
        self.W, self.H, self.ss = W, H, ss
        self.pen_w = pen_width
        self.rng = np.random.default_rng(seed)
        self.D = np.zeros((H, W, 3), np.float32)          # optical density: ink + pencil
        self.I = np.zeros((H, W), np.float32)             # amount of ink (for the sheen of heavy ink)
        self.G = np.zeros((H, W), np.float32)             # grooves pressed by pen and pencil (px, negative)
        self.tooth = np.full((H, W), 0.5, np.float32)
        self.base = np.ones((H, W, 3), np.float32) * hexc(PAPER)
        self.relief_shade = np.ones((H, W), np.float32)   # cockles and folds, already lit
        self.light = np.ones((H, W), np.float32)
        self.stages = []

    # ------------------------------------------------------------ small helpers
    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _grid(self):
        return (np.arange(self.H, dtype=np.float32)[:, None], np.arange(self.W, dtype=np.float32)[None, :])

    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1)) + 1), min(self.H, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _mask_box(self, M, pad=2, thr=0.02):
        rows = np.nonzero((M > thr).any(1))[0]
        if not len(rows): return None
        cols = np.nonzero((M[rows[0]:rows[-1] + 1] > thr).any(0))[0]
        return self._box(cols[0] - pad, rows[0] - pad, cols[-1] + pad, rows[-1] + pad)

    # ------------------------------------------------------------ paper
    def paper(self, tone=PAPER, tooth=0.75, fibres=260, mottle=0.014, cockle=1.0, folds=(), vignette=0.09):
        """copy paper: fine tooth, sparse fibres, mottle, cockles and fold creases lit from the top left,
        the soft light fall-off of a photographed sheet. folds: [((x0, y0), (x1, y1)), ...] crease lines"""
        H, W = self.H, self.W
        r = np.random.default_rng(self._seed())
        t = blur(r.random((H, W), dtype=np.float32), tooth)
        t -= t.mean(); t /= (t.std() + 1e-6)
        t2 = blur(r.random((H, W), dtype=np.float32), tooth * 2.6)
        t2 -= t2.mean(); t2 /= (t2.std() + 1e-6)
        t = 0.72 * t + 0.28 * t2; del t2
        t /= (t.std() + 1e-6)
        self.tooth = np.clip(0.5 + t * 0.19, 0, 1).astype(np.float32); del t
        base = hexc(tone)
        mot = (noise2d(H, W, 220, 3, self._seed()) - 0.5) * mottle * 2
        mot += (noise2d(H, W, 30, 2, self._seed()) - 0.5) * mottle * 0.6
        f = 1 + mot
        gy, gx = np.gradient(blur(self.tooth, 0.5))
        f += (gx * 0.6 + gy * 0.8) * 0.035                          # the tooth itself, barely, in raking light
        self.base = (base[None, None, :] * f[..., None]).astype(np.float32)
        # fibres: short faint curls, a few darker, most lighter than the sheet
        if fibres:
            im = Image.new('L', (W, H), 128); d = ImageDraw.Draw(im)
            for _ in range(int(fibres)):
                x, y = r.uniform(0, W), r.uniform(0, H)
                a = r.uniform(0, np.pi); L = r.uniform(6, 22); c = r.uniform(-1, 1) * 0.08
                pts = []
                for k in range(6):
                    a += c; x += np.cos(a) * L / 6; y += np.sin(a) * L / 6; pts.append((x, y))
                d.line(pts, fill=int(128 + (r.choice([-1, 1], p=[0.35, 0.65])) * r.uniform(10, 26)), width=1)
            fib = blur((np.asarray(im, np.float32) - 128) / 128, 0.6) * 0.09
            self.base *= (1 + fib)[..., None]
        # relief: low cockles + folds, lit from the top left
        YY, XX = self._grid()
        rel = (noise2d(H, W, 420, 3, self._seed()) - 0.5) * 14 * cockle
        for (p0, p1) in folds:
            p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
            dv = p1 - p0; dv /= np.linalg.norm(dv)
            dist = (XX - p0[0]) * dv[1] - (YY - p0[1]) * dv[0]
            dist = dist + fbm1d(W + H, 160, 3, self._seed())[np.clip(((XX + YY) * 0 + XX * abs(dv[0]) + YY * abs(dv[1])).astype(int), 0, W + H - 1)] * 2.5
            rel = rel - 0.1 * np.exp(-(dist / 3.0) ** 2) + 0.024 * np.abs(dist) * np.exp(-np.abs(dist) / 320)
        gy, gx = np.gradient(rel.astype(np.float32))
        self.relief_shade = (1 + np.clip((gx * 0.6 + gy * 0.8) * 0.55, -0.07, 0.07)).astype(np.float32)
        del rel, gx, gy
        rr = np.hypot((XX - W * 0.46) / (W * 0.62), (YY - H * 0.42) / (H * 0.68))
        self.light = (1.0 - vignette * smoothstep(0.35, 1.25, rr) - 0.02 * (XX / W) - 0.015 * (YY / H)).astype(np.float32)

    # ------------------------------------------------------------ masks
    def _paint(self, P_all, pad, feather, draw):
        M = np.zeros((self.H, self.W), np.float32)
        P = np.asarray(P_all, np.float32).reshape(-1, 2)
        sl = self._box(P[:, 0].min() - pad - 3 * feather - 2, P[:, 1].min() - pad - 3 * feather - 2,
                       P[:, 0].max() + pad + 3 * feather + 2, P[:, 1].max() + pad + 3 * feather + 2)
        if sl is None: return M
        x0, y0 = sl[1].start, sl[0].start
        w, h = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (w * 2, h * 2), 0)
        draw(ImageDraw.Draw(im), lambda p: (float(p[0] - x0) * 2, float(p[1] - y0) * 2))
        a = np.asarray(im.resize((w, h), Image.BILINEAR), np.float32) / 255
        M[sl] = blur(a, feather) if feather else a
        return M

    def poly(self, pts, feather=0.6):
        """filled polygon mask (0..1)"""
        P = np.asarray(pts, np.float32)
        return self._paint(P, 2, feather, lambda d, T: d.polygon([T(p) for p in P], fill=255))

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0, feather=0.6):
        ry = rx if ry is None else ry
        return self.poly(self.circle_pts(cx, cy, rx, ry, rot=rot, n=max(24, int((rx + ry) * 0.6))), feather)

    def band(self, pts, width, feather=0.6, smooth=True):
        """mask of a thick polyline"""
        P = spline(pts, 10) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32)

        def draw(d, T):
            Q = [T(p) for p in P]
            d.line(Q, fill=255, width=max(1, int(round(width * 2))), joint='curve')
            for q in (Q[0], Q[-1]):
                d.ellipse([q[0] - width, q[1] - width, q[0] + width, q[1] + width], fill=255)
        return self._paint(P, width, feather, draw)

    def tube(self, pts, w0, w1, feather=0.6):
        """mask of a tapering body along a path: width w0 at the first point to w1 at the last (snake, tail)"""
        P = _resample(spline(pts, 10) if len(pts) > 2 else pts, 3.0)
        L, R = self.tube_sides(P, w0, w1)
        return self.poly(np.vstack([L, R[::-1]]), feather)

    @staticmethod
    def tube_sides(pts, w0, w1, smooth=True):
        """left and right outlines of a tapering body (for drawing its two edges with the pen)"""
        P = _resample(spline(pts, 10) if (smooth and len(pts) > 2) else pts, 3.0)
        tan = np.gradient(P, axis=0); tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6)
        nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
        t = np.linspace(0, 1, len(P))[:, None]
        hw = (w0 + (w1 - w0) * t) / 2
        return P + nrm * hw, P - nrm * hw

    # ------------------------------------------------------------ point helpers
    @staticmethod
    def resample(pts, step=3.0):
        """a polyline re-spaced to one point every `step` px"""
        return _resample(pts, step)

    @staticmethod
    def circle_pts(cx, cy, rx, ry=None, a0=0.0, a1=360.0, rot=0.0, n=None):
        """points on an ellipse arc (degrees, clockwise on screen)"""
        ry = rx if ry is None else ry
        n = n or max(10, int(abs(a1 - a0) / 360 * 2 * np.pi * max(rx, ry) / 3))
        t = np.deg2rad(np.linspace(a0, a1, n))
        x, y = rx * np.cos(t), ry * np.sin(t)
        a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
        return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)

    @staticmethod
    def star_pts(cx, cy, r, inner=0.45, n=5, rot=-90.0):
        a = np.deg2rad(rot) + np.arange(2 * n) * np.pi / n
        rr = np.where(np.arange(2 * n) % 2 == 0, r, r * inner)
        P = np.stack([cx + rr * np.cos(a), cy + rr * np.sin(a)], 1)
        return np.vstack([P, P[:1]]).astype(np.float32)

    @staticmethod
    def cloud_pts(cx, cy, w, h, bumps=7, seed=0, flat=True):
        """scalloped cloud outline: arcs bulging out of an ellipse; a flatter bottom if `flat`"""
        r = np.random.default_rng(seed)
        ang = np.sort(np.linspace(0, 2 * np.pi, bumps, endpoint=False) + r.normal(0, 0.12, bumps))
        pts = []
        for i in range(bumps):
            a0, a1 = ang[i], ang[(i + 1) % bumps] + (2 * np.pi if i == bumps - 1 else 0)
            for t in np.linspace(0, 1, 9, endpoint=False):
                a = a0 + (a1 - a0) * t
                bulge = np.sin(np.pi * t) * (0.20 + 0.06 * r.random() if t == 0 else 0.22)
                ry = h / 2 * (0.62 if (flat and np.sin(a) > 0.2) else 1.0)
                k = 1 + bulge * (0.35 if (flat and np.sin(a) > 0.35) else 1.0)
                pts.append((cx + np.cos(a) * w / 2 * k, cy + np.sin(a) * ry * k))
        pts.append(pts[0])
        return np.array(pts, np.float32)

    @staticmethod
    def spiral_pts(cx, cy, r, turns=2.5, a0=0.0, inward=True, n=None):
        n = n or int(turns * 2 * np.pi * r / 4) + 8
        t = np.linspace(0, 1, n)
        rad = r * (1 - t) if inward else r * t
        a = np.deg2rad(a0) + t * turns * 2 * np.pi
        return np.stack([cx + rad * np.cos(a), cy + rad * np.sin(a)], 1).astype(np.float32)

    @staticmethod
    def heart_pts(cx, cy, s, rot=0.0):
        t = np.linspace(0, 2 * np.pi, 60)
        x = 16 * np.sin(t) ** 3; y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
        a = np.deg2rad(rot); c, sn = np.cos(a), np.sin(a)
        x, y = x * s / 32, y * s / 32
        return np.stack([cx + x * c - y * sn, cy + x * sn + y * c], 1).astype(np.float32)

    # ------------------------------------------------------------ the pen: one stroke
    def _prep(self, pts, pressure, width, closed, smooth, wobble, bow, hook, gloop, skip, start, step=1.5,
              overlap=None):
        r = self.rng
        P = np.asarray(pts, np.float32)
        if len(P) == 0: return None
        if closed and smooth and len(P) > 3:
            if np.hypot(*(P[0] - P[-1])) < 1e-3: P = P[:-1]
            P = _closed_spline(P, 8)
        elif closed:
            P = np.vstack([P, P[:1]])
        elif smooth and len(P) > 2:
            P = spline(P, 8)
        P = _resample(P, step)
        if closed and len(P) > 8:                      # the pen does not close exactly: overshoot or fall short
            ov = r.uniform(-3, 9) if overlap is None else overlap
            k = int(abs(ov) / step)
            if ov > 0 and k: P = np.vstack([P, P[1:k + 1]])
            elif k: P = P[:-k]
        n = len(P)
        if n < 2:
            return dict(Q=P, w=np.full(1, width * 1.15, np.float32), v=np.full(1, pressure * 1.3, np.float32),
                        p=np.full(1, pressure, np.float32), gl=[(P[0, 0], P[0, 1], width * 0.75, 0.0, 0.8)], skip=False)
        L = (n - 1) * step
        tan = np.gradient(P, axis=0); tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6)
        nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
        t = np.linspace(0, 1, n, dtype=np.float32)
        off = np.zeros(n, np.float32)
        if wobble:
            off += fbm1d(n, max(3, 55 / step), 3, self._seed()) * wobble
            off += fbm1d(n, max(2, 9 / step), 2, self._seed()) * wobble * 0.18
        if bow:
            off += 4 * t * (1 - t) * bow * L * (1 if r.random() < 0.5 else -1)
        P = P + nrm * off[:, None]
        # pressure: drift, dry start, ease at the end
        v = pressure * (1 + 0.12 * fbm1d(n, max(4, 80 / step), 2, self._seed()))
        if start:
            s0 = r.uniform(3, 10)
            v *= 0.32 + 0.68 * smoothstep(0, s0, t * L)
        v *= 0.8 + 0.2 * (1 - smoothstep(L - 3, L, t * L))
        p = v.copy()
        gl = []
        # gloops: where the pen stops, sharp turns, sometimes the start, now and then along long lines
        k = 3
        if n > 2 * k + 2:
            a1 = P[k:-k] - P[:-2 * k]; a2 = P[2 * k:] - P[k:-k]
            cosang = (a1 * a2).sum(1) / (np.linalg.norm(a1, axis=1) * np.linalg.norm(a2, axis=1) + 1e-6)
            turn = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
            for i in range(1, len(turn) - 1):
                if turn[i] > 55 and turn[i] >= turn[i - 1] and turn[i] >= turn[i + 1] and r.random() < gloop * 0.8:
                    j = i + k
                    gl.append((P[j, 0], P[j, 1], width * r.uniform(0.62, 0.95), np.arctan2(tan[j, 1], tan[j, 0]), r.uniform(0.6, 1.2)))
        if r.random() < gloop * 0.62:
            gl.append((P[-1, 0], P[-1, 1], width * r.uniform(0.62, 1.0), np.arctan2(tan[-1, 1], tan[-1, 0]), r.uniform(0.7, 1.4)))
        if r.random() < gloop * 0.3:
            gl.append((P[0, 0], P[0, 1], width * r.uniform(0.55, 0.85), np.arctan2(tan[0, 1], tan[0, 0]), r.uniform(0.5, 1.0)))
        s_ = r.uniform(150, 450)
        while s_ < L - 20:
            if r.random() < gloop * 0.35:
                j = int(s_ / step)
                gl.append((P[j, 0], P[j, 1], width * r.uniform(0.55, 0.8), np.arctan2(tan[j, 1], tan[j, 0]), r.uniform(0.5, 1.0)))
            s_ += r.uniform(150, 450)
        # skips: the ball stops feeding for a few px; the groove stays
        has_skip = False
        if skip and L > 25:
            m = r.poisson(L / 320 * skip * (1.5 - min(pressure, 1.0)))
            for _ in range(m):
                c0 = r.uniform(8, L - 8); ln = r.uniform(2, 9)
                g = 1 - smoothstep(ln / 2, ln / 2 + 1.5, np.abs(t * L - c0))
                v = v * (1 - g * r.uniform(0.65, 0.95)); has_skip = True
        # hook: the flick as the pen lifts
        if hook and r.random() < hook and n > 6:
            d = P[-1] - P[-4]; d /= (np.linalg.norm(d) + 1e-6)
            nr = np.array([-d[1], d[0]], np.float32)
            sgn = 1.0 if nr[1] < 0 else -1.0                 # curl toward the top of the page, mostly
            if r.random() < 0.25: sgn = -sgn
            hl = r.uniform(3, 7) * width / 2.3; turn = np.deg2rad(r.uniform(90, 160)) * sgn
            m = 6; pts_h = []; q = P[-1].copy(); ang = np.arctan2(d[1], d[0])
            for i in range(m):
                ang += turn / m
                q = q + np.array([np.cos(ang), np.sin(ang)], np.float32) * hl / m
                pts_h.append(q.copy())
            H_ = np.array(pts_h, np.float32)
            P = np.vstack([P, H_])
            fall = np.linspace(0.85, 0.3, m, dtype=np.float32) * v[-1]
            v = np.concatenate([v, fall]); p = np.concatenate([p, fall])
        w = width * (0.8 + 0.24 * np.clip(v / max(pressure, 1e-3), 0, 1.25))
        return dict(Q=P.astype(np.float32), w=w.astype(np.float32), v=v.astype(np.float32), p=p.astype(np.float32),
                    gl=gl, skip=has_skip)

    def _raster(self, strokes, key='v'):
        """prepared strokes -> (coverage, groove coverage or None, slices); ss x supersampled, box-filtered"""
        strokes = [s for s in strokes if s is not None and len(s['Q'])]
        if not strokes: return None, None, None
        allp = np.concatenate([s['Q'] for s in strokes])
        pad = max(float(np.max(s['w'])) for s in strokes) * 2 + 4
        sl = self._box(allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        if sl is None: return None, None, None
        ss = self.ss
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        need_g = any(s['skip'] for s in strokes)
        ims = [Image.new('L', (bw * ss, bh * ss), 0)] + ([Image.new('L', (bw * ss, bh * ss), 0)] if need_g else [])
        dr = [ImageDraw.Draw(im) for im in ims]
        off = np.array([x0, y0], np.float32)
        for s in strokes:
            Q = (s['Q'] - off) * ss
            for di, vals in zip(dr, [s['v'], s['p']][:len(dr)]):
                n = len(Q)
                if n == 1:
                    r_ = s['w'][0] * ss / 2
                    di.ellipse([Q[0, 0] - r_, Q[0, 1] - r_, Q[0, 0] + r_, Q[0, 1] + r_], fill=int(255 * min(1, vals[0])))
                    continue
                ww = np.maximum(1, np.round((s['w'][:-1] + s['w'][1:]) * 0.5 * ss)).astype(int)
                vv = np.round(np.clip((vals[:-1] + vals[1:]) * 0.5, 0, 1) * 40).astype(int)       # 40 levels
                q = Q.tolist()
                i = 0
                while i < n - 1:                                  # runs of equal width and value: one call each
                    j = i + 1
                    while j < n - 1 and ww[j] == ww[i] and vv[j] == vv[i] and j - i < 40: j += 1
                    if vv[i] > 0:
                        di.line([tuple(c) for c in q[i:j + 1]], fill=int(vv[i] * 255 / 40), width=int(ww[i]), joint='curve')
                    i = j
        cov = np.asarray(ims[0].resize((bw, bh), Image.BOX), np.float32) / 255
        gro = np.asarray(ims[1].resize((bw, bh), Image.BOX), np.float32) / 255 if need_g else None
        return cov, gro, sl

    def _gloops(self, strokes, sl):
        """the blobs: soft-edged teardrops of extra ink, in the box `sl`"""
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        out = None
        for s in strokes:
            if s is None: continue
            for (x, y, rad, ang, k) in s['gl']:
                x_, y_ = x - sl[1].start, y - sl[0].start
                R = int(rad * 2.2 + 3)
                X0, Y0 = int(x_) - R, int(y_) - R
                xs0, ys0 = max(0, X0), max(0, Y0); xs1, ys1 = min(w, X0 + 2 * R + 1), min(h, Y0 + 2 * R + 1)
                if xs1 <= xs0 or ys1 <= ys0: continue
                if out is None: out = np.zeros((h, w), np.float32)
                yy, xx = np.mgrid[ys0:ys1, xs0:xs1].astype(np.float32)
                c, sn = np.cos(ang), np.sin(ang)
                u = (xx - x_) * c + (yy - y_) * sn - rad * 0.25; v_ = -(xx - x_) * sn + (yy - y_) * c
                d = np.sqrt((u / 1.3) ** 2 + v_ ** 2) - rad
                out[ys0:ys1, xs0:xs1] += np.clip(0.5 - d / 0.9, 0, 1) * k
        return out

    def _ink(self, strokes, pen, clip=None, groove=1.0):
        cov, gro, sl = self._raster(strokes)
        if sl is None: return
        gl = self._gloops(strokes, sl)
        if gro is None: gro = cov.copy()
        if gl is not None:
            gro = np.maximum(gro, np.clip(gl, 0, 1))
        if clip is not None:
            cov = cov * clip[sl]; gro = gro * clip[sl]
            if gl is not None: gl = gl * clip[sl]
        if pen is not None:
            t = self.tooth[sl]
            reach = 0.48 + 0.6 * np.sqrt(np.clip(cov, 0, 1))
            resp = smoothstep(1.0 - reach - 0.2, 1.0 - reach + 0.2, t)
            amt = cov * (0.22 + 0.78 * resp)
            if gl is not None: amt = amt + gl * (0.75 + 0.25 * resp)
            dens = -np.log(np.array(PENS[pen] if isinstance(pen, str) else pen, np.float32))
            self.D[sl] += amt[..., None] * dens
            self.I[sl] += amt
        if groove:
            self.G[sl] -= blur(gro, 0.55) * 0.9 * groove

    def line(self, pts, pen='blue', pressure=0.82, width=None, closed=False, smooth=True, wobble=0.55, bow=0.0,
             hook=0.3, gloop=0.5, skip=0.6, twice=0.0, start=True, clip=None, groove=1.0):
        """one ballpoint stroke through `pts`. pen: 'blue' 'red' 'black' (or an RGB reflectance), None = blind
        groove only. bow: sideways bow as a fraction of length (freehand straight lines ~0.003-0.006).
        hook / gloop: chances of a lift-off flick and of ink blobs; skip: how often the ball skips;
        twice: chance (0..1) the line is gone over again, slightly off, for part of its length"""
        width = width or self.pen_w
        s = self._prep(pts, pressure, width, closed, smooth, wobble, bow, hook, gloop, skip, start)
        if s is None: return
        self._ink([s], pen, clip, groove)
        if twice and self.rng.random() < twice and len(s['Q']) > 8:
            Q = s['Q']; n = len(Q)
            i0 = int(self.rng.uniform(0, 0.25) * n); i1 = n - int(self.rng.uniform(0, 0.3) * n)
            if i1 - i0 > 4:
                tan = np.gradient(Q, axis=0); tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6)
                nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
                off = (self.rng.uniform(0.6, 1.6) * (1 if self.rng.random() < 0.5 else -1)
                       + fbm1d(n, max(4, n / 4), 2, self._seed()) * 0.7)
                s2 = self._prep((Q + nrm * off[:, None])[i0:i1], pressure * 0.85, width, False, False, wobble * 0.5, 0,
                                hook * 0.5, gloop * 0.5, skip, True)
                self._ink([s2], pen, clip, groove)

    def lines(self, paths, pen='blue', pressure=0.8, width=None, smooth=True, wobble=0.5, hook=0.25, gloop=0.4,
              skip=0.5, clip=None, closed=False, groove=1.0):
        """many short strokes in one go (they share one raster: crossings do not add up)"""
        width = width or self.pen_w
        S = [self._prep(p, pressure, width, closed, smooth, wobble, 0.0, hook, gloop, skip, True) for p in paths if len(p)]
        self._ink(S, pen, clip, groove)

    def emboss(self, pts, pressure=0.8, width=None, smooth=True):
        """a groove with no ink: what writing on the sheet above leaves behind (shows only in raking light)"""
        self.line(pts, None, pressure, width, smooth=smooth, hook=0.2, gloop=0.0, skip=0.0)

    # ------------------------------------------------------------ marks made of strokes
    def dot(self, x, y, r=3.0, pen='blue', pressure=0.95):
        """a pressed dot: a tiny circling of the pen, ink pooled in the middle"""
        if r <= 2.0:
            s = self._prep([(x, y)], pressure, self.pen_w * r / 1.3, False, False, 0, 0, 0, 1, 0, False)
            self._ink([s], pen); return
        P = self.spiral_pts(x, y, max(0.5, r - self.pen_w * 0.45), turns=max(1.2, r / 1.6), a0=self.rng.uniform(0, 360))
        s = self._prep(P, pressure, self.pen_w, False, False, 0.15, 0, 0, 0, 0, False)
        s['gl'].append((x, y, r * 0.7, 0.0, 0.6))
        self._ink([s], pen)

    def eye(self, cx, cy, rx, ry=None, pen='black', look=(0.0, 0.0), shine=0.32, pressure=0.95):
        """an inked oval eye: the pen circles inward until it is solid, leaving a round highlight"""
        ry = ry or rx
        hx, hy = cx - rx * 0.32 + look[0] * rx * 0.2, cy - ry * 0.34 + look[1] * ry * 0.2
        hr = min(rx, ry) * shine
        clip = None
        if shine:
            clip = 1 - self.ellipse(hx, hy, hr, hr, feather=0.5)
        turns = max(rx, ry) / (self.pen_w * 0.62)
        t = np.linspace(0, 1, int(turns * 2 * np.pi * max(rx, ry) / 2.5) + 8)
        a = t * turns * 2 * np.pi + self.rng.uniform(0, 6.28)
        k = np.clip(1 - t, 0, 1)
        P = np.stack([cx + (rx - self.pen_w * 0.45) * k * np.cos(a), cy + (ry - self.pen_w * 0.45) * k * np.sin(a)], 1)
        s = self._prep(P, pressure, self.pen_w * 1.05, False, False, 0.1, 0, 0, 0.3, 0.2, False)
        self._ink([s], pen, clip)
        self.line(self.circle_pts(cx, cy, rx, ry), pen, pressure, closed=True, hook=0, gloop=0.4, skip=0.2, clip=clip)

    def face(self, cx, cy, size, mood='smile', pen='black', blush='pink', look=(0.0, 0.0), rot=0.0):
        """a doodle face: inked eyes, mouth, pencil blush. mood: smile, grin, oh, dizzy, sleep, worry"""
        a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
        T = lambda x, y: (cx + x * c - y * s, cy + x * s + y * c)
        e = size * 0.11; gap = size * 0.2
        for sx in (-1, 1):
            ex, ey = T(sx * gap, -size * 0.04)
            if mood == 'dizzy':
                self.line(self.spiral_pts(ex, ey, e * 1.15, turns=2.3, a0=self.rng.uniform(0, 360)), pen, 0.8, smooth=False,
                          hook=0.2, gloop=0.4, skip=0.1)
            elif mood == 'sleep':
                self.line([T(sx * gap - e, -size * 0.04), T(sx * gap, size * 0.02), T(sx * gap + e, -size * 0.04)], pen, 0.8,
                          hook=0.3, gloop=0.3)
            else:
                self.eye(ex, ey, e * 0.92, e * 1.12, pen, look)
        if mood in ('smile', 'grin', 'sleep'):
            mw = size * (0.1 if mood != 'grin' else 0.15)
            self.line([T(-mw, size * 0.1), T(0, size * 0.1 + mw * (0.8 if mood != 'grin' else 0.9)), T(mw, size * 0.1)], pen,
                      0.8, hook=0.15, gloop=0.3)
        elif mood == 'oh':
            mx, my = T(0, size * 0.15)
            self.line(self.circle_pts(mx, my, size * 0.05, size * 0.065), pen, 0.85, closed=True, hook=0)
        elif mood == 'dizzy':
            mx, my = T(0, size * 0.16)
            self.line(self.circle_pts(mx, my, size * 0.06, size * 0.075), pen, 0.85, closed=True, hook=0)
        elif mood == 'worry':
            self.line([T(-size * 0.09, size * 0.16), T(-size * 0.03, size * 0.12), T(size * 0.03, size * 0.16), T(size * 0.09, size * 0.12)],
                      pen, 0.8, hook=0.1)
        if blush:
            for sx in (-1, 1):
                bx, by = T(sx * gap * 1.55, size * 0.09)
                self.pencil(self.ellipse(bx, by, size * 0.08, size * 0.045, rot=rot), blush, angle=self.rng.uniform(40, 70),
                            pressure=0.7, spacing=2.6, overshoot=1.5, length=(8, 14))

    def dashes(self, pts, pen='red', dash=11.0, gap=8.0, pressure=0.85, smooth=True, clip=None):
        """a dashed line along a path: each dash its own little stroke; returns the resampled path"""
        P = _resample(spline(pts, 10) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32), 1.0)
        L = len(P); out = []; i = int(self.rng.uniform(0, gap))
        while i < L - 2:
            dl = int(dash * self.rng.uniform(0.8, 1.2))
            out.append(P[i:min(L, i + dl)])
            i += dl + int(gap * self.rng.uniform(0.8, 1.25))
        self.lines([q for q in out if len(q) > 1], pen, pressure, smooth=False, hook=0.05, gloop=0.35, skip=0.1, wobble=0.25,
                   clip=clip)
        return P

    def arrow(self, tip, direction, size=16.0, pen='red', pressure=0.85, spread=28.0):
        """an arrowhead: two quick strokes back from the tip (direction: the way the arrow points)"""
        d = np.array(direction, np.float32); d /= (np.linalg.norm(d) + 1e-6)
        tip = np.array(tip, np.float32)
        for sg in (-1, 1):
            a = np.deg2rad(spread + self.rng.normal(0, 4)) * sg
            c, s = np.cos(a), np.sin(a)
            back = -np.array([d[0] * c - d[1] * s, d[0] * s + d[1] * c])
            self.line([tip + back * size * self.rng.uniform(0.9, 1.1), tip], pen, pressure, smooth=False, hook=0.0, gloop=0.6)

    def ring(self, cx, cy, rx, ry=None, pen='red', pressure=0.85, turns=1.12, rot=0.0):
        """a quick loose circle around something: overshoots its start and drifts outward"""
        ry = ry or rx
        a0 = self.rng.uniform(-150, -60)
        t = np.linspace(0, 1, 120)
        a = np.deg2rad(a0 + t * 360 * turns)
        k = 1 + 0.07 * t + 0.03 * np.sin(t * 7 + self.rng.uniform(0, 6))
        P = np.stack([rx * k * np.cos(a), ry * k * np.sin(a)], 1)
        ra = np.deg2rad(rot); c, s = np.cos(ra), np.sin(ra)
        P = np.stack([cx + P[:, 0] * c - P[:, 1] * s, cy + P[:, 0] * s + P[:, 1] * c], 1)
        self.line(P, pen, pressure, smooth=False, wobble=0.9, hook=0.5, gloop=0.6, skip=0.3)

    # ------------------------------------------------------------ hatching: coloured pencil and pen
    def _hatch_paths(self, mask, angle, spacing, length, overshoot, jitter, bow):
        sl = self._mask_box(mask, pad=2, thr=0.3)
        if sl is None: return []
        r = self.rng
        M = mask[sl]
        y0, x0 = sl[0].start, sl[1].start
        h, w = M.shape
        a = np.deg2rad(angle)
        d = np.array([np.cos(a), np.sin(a)], np.float32); nv = np.array([-d[1], d[0]], np.float32)
        c = np.array([x0 + w / 2, y0 + h / 2], np.float32)
        R = np.hypot(w, h) / 2 + 4
        out = []
        o = -R + r.uniform(0, spacing)
        ts = np.arange(-R, R, 1.5, dtype=np.float32)
        Lp = r.uniform(*length)
        cut0 = r.uniform(0, Lp)
        while o < R:
            base = c + nv * o
            X = base[0] + d[0] * ts; Y = base[1] + d[1] * ts
            ix = np.clip((X - x0).astype(int), 0, w - 1); iy = np.clip((Y - y0).astype(int), 0, h - 1)
            ins = (M[iy, ix] > 0.5) & (X >= x0) & (X < x0 + w) & (Y >= y0) & (Y < y0 + h)
            if ins.any():
                e = np.diff(np.concatenate([[0], ins.astype(np.int8), [0]]))
                st, en = np.nonzero(e == 1)[0], np.nonzero(e == -1)[0] - 1
                for s0, s1 in zip(st, en):
                    u0, u1 = ts[s0] - r.uniform(-1.5, overshoot), ts[s1] + r.uniform(-1.5, overshoot)
                    # break long runs into wrist-length strokes, seams staggered from row to row
                    k0 = np.floor((u0 - cut0) / Lp); seams = cut0 + Lp * np.arange(k0 + 1, np.ceil((u1 - cut0) / Lp))
                    seams = seams + r.normal(0, Lp * 0.06, len(seams))
                    bounds = [u0] + [sm for sm in seams if u0 + 6 < sm < u1 - 6] + [u1]
                    for b0, b1 in zip(bounds[:-1], bounds[1:]):
                        b0 -= r.uniform(0, 2.5); b1 += r.uniform(0, 2.5)
                        if b1 - b0 < 3: continue
                        tt = np.linspace(0, 1, max(3, int((b1 - b0) / 6)), dtype=np.float32)[:, None]
                        bend = bow * (b1 - b0) * r.uniform(0.5, 1.3)
                        oo = o + r.normal(0, jitter * 0.3)
                        P = c + nv * oo + d * (b0 + (b1 - b0) * tt) + nv * (4 * tt * (1 - tt) * bend)
                        out.append(P)
            o += spacing * r.uniform(0.82, 1.18)
        return out

    def pencil(self, mask, colour, angle=60.0, pressure=0.45, spacing=4.2, length=(40, 90), overshoot=5.0, width=2.9,
               jitter=1.0, bow=0.04, cross=None, clip=None, groove=0.25):
        """coloured-pencil hatching inside `mask`: parallel quick strokes, heavier mid-stroke than at the ends,
        overshooting the outline a little. colour: a PENCILS name or '#rrggbb'. cross: a second angle laid
        over the first (darker, interleaved)"""
        col = hexc(PENCILS.get(colour, colour)) if isinstance(colour, str) else np.asarray(colour, np.float32)
        for ang in [angle] + ([cross] if cross is not None else []):
            paths = self._hatch_paths(mask, ang + self.rng.normal(0, 2.0), spacing, length, overshoot, jitter, bow)
            if not paths: continue
            self._wax(paths, col, pressure, width, clip, groove)

    def pencil_line(self, pts, colour, pressure=0.6, width=3.0, smooth=True, wobble=0.6, clip=None):
        """a single coloured-pencil line (grass blades, rays, a rainbow band)"""
        col = hexc(PENCILS.get(colour, colour)) if isinstance(colour, str) else np.asarray(colour, np.float32)
        P = spline(pts, 8) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32)
        self._wax([P], col, pressure, width, clip, 0.25, wobble)

    def _wax(self, paths, col, pressure, width, clip, groove, wobble=0.35):
        r = self.rng
        allp = np.concatenate(paths)
        pad = width * 2 + 4
        sl = self._box(allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        if sl is None: return
        ss = self.ss
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (bw * ss, bh * ss), 0); d = ImageDraw.Draw(im)
        off = np.array([x0, y0], np.float32)
        for P in paths:
            P = _resample(P, 3.0)
            n = len(P)
            if n < 2: continue
            if wobble:
                tan = np.gradient(P, axis=0); tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6)
                P = P + np.stack([-tan[:, 1], tan[:, 0]], 1) * (fbm1d(n, max(3, n / 3), 2, self._seed()) * wobble)[:, None]
            Q = ((P - off) * ss).tolist()
            pr = pressure * r.uniform(0.8, 1.15)
            wd = max(1, int(round(width * ss * r.uniform(0.85, 1.15))))
            k = max(1, n // 5)
            parts = [(0, k + 1, 0.55), (k, n - k, 1.0), (n - k - 1, n, 0.45)] if n > 4 else [(0, n, 0.85)]
            for a_, b_, f in parts:
                seg = Q[a_:b_]
                if len(seg) >= 2:
                    d.line([tuple(q) for q in seg], fill=int(255 * min(1, pr * f)), width=wd, joint='curve')
        cov = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        if clip is not None: cov = cov * clip[sl]
        t = self.tooth[sl]
        reach = 0.16 + 0.62 * np.sqrt(np.clip(cov, 0, 1))
        resp = smoothstep(1.0 - reach - 0.11, 1.0 - reach + 0.11, t)
        amt = cov * (0.1 + 0.9 * resp) * 0.95
        self.D[sl] += amt[..., None] * (-np.log(np.clip(col, 0.02, 1)))
        if groove: self.G[sl] -= blur(cov, 0.6) * 0.3 * groove

    def pen_hatch(self, mask, pen='blue', angle=50.0, spacing=3.2, pressure=0.7, length=(30, 60), overshoot=3.0,
                  zigzag=0.85, cross=None, clip=None):
        """ballpoint shading: parallel strokes laid back and forth without lifting the pen (`zigzag` share),
        gloops at the turns; cross: a second pass at another angle"""
        for ang in [angle] + ([cross] if cross is not None else []):
            paths = self._hatch_paths(mask, ang + self.rng.normal(0, 2.0), spacing, length, overshoot, 1.0, 0.03)
            if not paths: continue
            chains = []
            if zigzag:
                cur = None
                for P in paths:
                    if cur is not None and self.rng.random() < zigzag and len(cur) < 9 and \
                            np.hypot(*(cur[-1][-1] - P[-1])) < spacing * 3.5 + 6:
                        cur.append(P[::-1] if len(cur) % 2 else P)
                    else:
                        if cur: chains.append(np.vstack(cur))
                        cur = [P]
                if cur: chains.append(np.vstack(cur))
            else:
                chains = paths
            S = [self._prep(P, pressure * self.rng.uniform(0.85, 1.1), self.pen_w * 0.95, False, False, 0.3, 0, 0.1, 0.35, 0.3, True)
                 for P in chains if len(P) > 1]
            self._ink(S, pen, clip)

    # ------------------------------------------------------------ handwriting
    def write(self, s, x, y, size=34.0, pen='blue', pressure=0.8, slant=7.0, spacing=1.04, jitter=1.0, anchor='l',
              rot=0.0, width=None, blind=False, hook=0.3, gloop=0.4):
        """handwrite `s` with its baseline at y. anchor 'l' / 'm' / 'r' on x; rot: the whole line tilted (deg,
        clockwise); blind: grooves only (writing that came through from the sheet on top). Returns the
        (x0, y0, x1, y1) box of what was written"""
        r = self.rng
        width = width or self.pen_w
        G = [_glyph(ch) for ch in s]
        scs = size * (1 + r.normal(0, 0.05 * jitter, len(s)))           # each letter its own size ...
        advs = np.array([g[2] * sc * spacing * (1 + r.normal(0, 0.02 * jitter)) for g, sc in zip(G, scs)], np.float32)
        tot = float(advs.sum())
        xs = x - tot * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor] + np.concatenate([[0], np.cumsum(advs)[:-1]])
        drift = fbm1d(max(4, len(s) + 2), 3, 2, self._seed()) * size * 0.045 * jitter
        ra = np.deg2rad(rot); cr, sr = np.cos(ra), np.sin(ra)
        sh = np.tan(np.deg2rad(slant))
        strokes, boxes = [], []
        for i, (ch, (paths, dots, _)) in enumerate(zip(s, G)):
            if not paths and not dots: continue
            sc = scs[i]                                                     # ... and its advance to match
            a = np.deg2rad(r.normal(0, 2.5 * jitter)); ca, sa = np.cos(a), np.sin(a)
            dy = drift[i] + r.normal(0, size * 0.012 * jitter)

            def T(P, xi=xs[i], sc=sc, ca=ca, sa=sa, dy=dy):
                P = np.asarray(P, np.float32) * sc
                px, py = P[:, 0] - P[:, 1] * sh, P[:, 1]
                px, py = px * ca - py * sa, px * sa + py * ca
                gx, gy = xi + px, y + py + dy
                return np.stack([x + (gx - x) * cr - (gy - y) * sr, y + (gx - x) * sr + (gy - y) * cr], 1)
            for P in paths:
                Q = T(P)
                strokes.append(self._prep(Q, pressure * r.uniform(0.88, 1.08), width, False, False, 0.25 * jitter, 0,
                                          hook if P is paths[-1] else hook * 0.4, gloop, 0.25, True))
                boxes.append(Q)
            for (dx_, dy_) in dots:
                Q = T([(dx_, dy_)])[0]
                strokes.append(self._prep([Q, Q + r.normal(0, 0.6, 2)], pressure * 1.1, width * 1.2, False, False, 0, 0, 0,
                                          1.0, 0, False))
                boxes.append(Q[None])
        if not strokes: return (x, y, x, y)
        self._ink(strokes, None if blind else pen, groove=0.55 if blind else 1.0)
        B = np.concatenate(boxes)
        return (float(B[:, 0].min()), float(B[:, 1].min()), float(B[:, 0].max()), float(B[:, 1].max()))

    def strike(self, box, pen='blue', pressure=0.85, passes=3):
        """scribble a word out: the pen goes back and forth through its middle a few times"""
        x0, y0, x1, y1 = box
        h = y1 - y0; ym = y0 + h * 0.55
        pts = []
        for k in range(passes + 1):
            xx = (x0 - 4 + self.rng.uniform(-3, 3)) if k % 2 == 0 else (x1 + 4 + self.rng.uniform(-3, 3))
            pts.append((xx, ym + self.rng.normal(0, h * 0.09) + (k - passes / 2) * h * 0.06))
        P = []
        for a, b in zip(pts[:-1], pts[1:]):
            P.extend(_resample(np.array([a, b], np.float32), 3.0)[:-1].tolist())
        P.append(pts[-1])
        self.line(np.array(P, np.float32), pen, pressure, smooth=False, wobble=1.0, hook=0.3, gloop=0.8, skip=0.2)

    def underline(self, x0, x1, y, pen='red', pressure=0.85, wavy=False, twice=0.5):
        if wavy:
            xs = np.linspace(x0, x1, int((x1 - x0) / 3) + 2)
            P = np.stack([xs, y + np.sin((xs - x0) / 9.0) * 3.2], 1)
            self.line(P, pen, pressure, smooth=False, hook=0.4, wobble=0.5)
        else:
            self.line([(x0, y), (x1, y + self.rng.normal(0, 2))], pen, pressure, bow=0.006, hook=0.5, twice=twice)

    # ------------------------------------------------------------ output
    def composite(self):
        gy, gx = np.gradient(blur(self.G, 0.55))
        shade = 1 + np.clip((gx * 0.6 + gy * 0.8) * 0.13, -0.1, 0.1)
        del gx, gy
        img = self.base * np.exp(-self.D)
        heavy = smoothstep(1.4, 3.2, self.I)
        img += (np.array(SHEEN, np.float32) - img) * (heavy * 0.14)[..., None]
        img *= (shade * self.relief_shade * self.light)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
