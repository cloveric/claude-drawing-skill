"""crayon — a child's wax-crayon drawing on rough paper (numpy + Pillow only).

Model:
  paper   : cheap rough drawing paper. Its tooth is a height field of 2-16 px bumps, histogram-equalised so a
            threshold maps straight to a coverage fraction. Bare paper shows the tooth faintly under a raking light.
  crayon  : a fat stick of pigmented wax. Its worn tip is not a point but a flat facet with ridges, so a stroke
            is a bundle of parallel sub-lines (K = width / 3) of uneven strength: white streaks run along every
            stroke. Wax only rubs off onto the *peaks* of the tooth: a pixel gets wax where
                tooth + 0.35 * wax_already_there  >  1 - contact * pressure
            so a light stroke leaves a speckle of white pits, a hard one fills the valleys, and every later layer
            catches more easily on the wax of the earlier ones (build-up). The crayon rides from bump to bump in
            the direction it is dragged, so the bare pits are drawn out into short streaks along the stroke
            (the tooth is averaged along the stroke angle before the threshold). `burnish` presses the wax down
            into the pits: the specks close up and the surface turns waxy and shiny.
  colour  : wax is semi-opaque. New colour = lerp(under, colour * under^0.6, coverage): on white paper it is the
            crayon colour, over yellow a blue turns green, over a black outline everything stays dark, and the
            same colour twice gets deeper and more saturated.
  the hand: a child colours in by scribbling back and forth. The arm only reaches so far, so a big area is filled
            patch by patch, each patch with its own stroke angle; strokes bow like a wrist arc, turn in sharp V's
            at the outline and overshoot it (or stop short), leave triangle-shaped gaps between passes, and the
            turns are darker because two passes overlap there. Smaller things get circle scribbles (`loops`),
            bands get strokes along their length (`follow`), outlines are one wobbly line whose end runs past
            its start (`line(closed=True)`), and letters are thin glyphs re-drawn with a fat round crayon,
            each character tilted, resized and coloured differently (`write`).
  finish  : wax has thickness: it is lit with the paper as one height field (raking light from the top left,
            a faint waxy sheen where it is thick); crayon crumbs sit on top; real crayons can lie on the sheet.

    from crayon import Crayon
    c = Crayon(1920, 1080, seed=3)
    c.paper()
    sun = c.circle(300, 240, 120)
    c.line(sun, c.C['orange'], closed=True)                     # the outline first
    c.loops(c.mask(sun), c.C['yellow'])                         # then colour it in with circles
    c.scribble(c.mask(c.rect(0, 0, 1920, 330)), c.C['sky'], angle=4, avoid=c.drawn(), halo=14)  # colour round the sun
    c.write('MY DAY', 900, 120, 110, [c.C['red'], c.C['blue']])
    c.stick(1600, 980, -20, c.C['red'])                          # a real crayon lying on the paper
    c.save('out.jpg')
"""
import os
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, noise2d, smoothstep, polygon_mask, blob_pts, shift, height_normals, cjk_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# a 24-stick school crayon box (generic names, no brand)
COLOURS = {
    'red': '#d8302c', 'scarlet': '#ec4a32', 'orange': '#f5821f', 'apricot': '#f9b98a', 'peach': '#f6c7a1',
    'yellow': '#fcd22e', 'lemon': '#f3e75a', 'yellowgreen': '#9ccc3c', 'green': '#2f9e48', 'darkgreen': '#1f6f3a',
    'sky': '#5fb1ea', 'blue': '#2a63c9', 'navy': '#253b8a', 'violet': '#7550b0', 'purple': '#9b3f9a',
    'pink': '#f27aa8', 'magenta': '#df3f8b', 'brown': '#8a5230', 'tan': '#d29a5c', 'black': '#2a2826',
    'grey': '#8c8c8c', 'white': '#fbfaf5', 'turquoise': '#2fb7b0', 'carmine': '#b3222f',
}

_THIN_CJK = [('/System/Library/Fonts/STHeiti Light.ttc', 0), ('/System/Library/Fonts/Hiragino Sans GB.ttc', 0),
             ('/usr/share/fonts/**/NotoSansCJK*Light*.tt[cf]', 0), ('/usr/share/fonts/**/NotoSansCJK*DemiLight*.tt[cf]', 0),
             ('/usr/share/fonts/**/NotoSansCJK*Regular*.tt[cf]', 0), ('C:/Windows/Fonts/msyhl.ttc', 0),
             ('C:/Windows/Fonts/msyh.ttc', 0)]


def _thin_font(size):
    """a light-weight sans (CJK + Latin) whose strokes are thin enough to serve as the centre line of a letter.
    $INKPAINT_FONT_CRAYON overrides."""
    env = os.environ.get('INKPAINT_FONT_CRAYON')
    cands = [(env, 0)] if env and os.path.exists(env) else []
    for pat, idx in _THIN_CJK:
        fs = glob.glob(pat, recursive=True)
        if fs: cands.append((fs[0], idx))
    p = cjk_font()
    if p: cands.append((p, 0))
    for path, idx in cands:
        try:
            return ImageFont.truetype(path, int(size), index=idx)
        except OSError:
            continue
    return ImageFont.load_default(int(size))


def _thin(b):
    """Zhang-Suen thinning: a boolean glyph -> its one-pixel centre line"""
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
            if step == 0:
                c1, c2 = p2 * p4 * p6, p4 * p6 * p8
            else:
                c1, c2 = p2 * p4 * p8, p2 * p6 * p8
            m = (I == 1) & (B >= 2) & (B <= 6) & (A == 1) & (c1 == 0) & (c2 == 0)
            if m.any():
                I[m] = 0; changed = True
    return I.astype(bool)


class Crayon:
    C = COLOURS

    def __init__(self, W=1920, H=1080, seed=0, paper='#f7f3e9'):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.tone = _c(paper)
        self.img = np.ones((H, W, 3), np.float32) * self.tone
        self.wax = np.zeros((H, W), np.float32)
        self.tooth = np.full((H, W), 0.5, np.float32)
        self.relief = np.zeros((H, W), np.float32)
        self.over = []                    # things lying on the paper (crayons), drawn at composite time
        self.crumb = np.zeros((H, W), np.float32)
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def noise(self, scale, octaves=3, seed=None):
        return noise2d(self.H, self.W, scale, octaves, seed if seed is not None else self._seed())

    # ------------------------------------------------------------ paper
    def paper(self, tone=None, grain=1.0, fibres=0.6, scan=0.035):
        """rough drawing paper: a coarse tooth (2-16 px bumps), a few pulp fibres and a faint uneven scan light"""
        if tone is not None: self.tone = _c(tone)
        H, W = self.H, self.W
        t = 0.62 * self.noise(1.7, 2) + 0.28 * self.noise(3.8, 2) + 0.10 * self.noise(14, 2)
        if fibres:
            im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
            for _ in range(int(2600 * fibres)):
                x, y = self.rng.uniform(0, W), self.rng.uniform(0, H)
                a = self.rng.uniform(0, np.pi); L = self.rng.uniform(5, 18)
                bend = self.rng.normal(0, 2.5)
                d.line([(x, y), (x + np.cos(a) * L / 2 - np.sin(a) * bend, y + np.sin(a) * L / 2 + np.cos(a) * bend),
                        (x + np.cos(a) * L, y + np.sin(a) * L)], fill=int(self.rng.uniform(60, 160)), width=1)
            t = t + 0.25 * blur(np.asarray(im, np.float32) / 255, 0.6)
        self.relief = blur(t, 0.7)
        # equalise: tooth is uniform on [0, 1], so 1 - threshold = the fraction of paper the wax reaches
        hist, edges = np.histogram(t, 1024)
        cdf = np.cumsum(hist).astype(np.float32); cdf /= cdf[-1]
        self.tooth = np.interp(t, edges[1:], cdf).astype(np.float32) * grain + 0.5 * (1 - grain)
        light = 1 - scan * (0.6 * self.noise(500, 2) + 0.4 * ((self.XX / W - 0.35) ** 2 + (self.YY / H - 0.3) ** 2))
        self.img = np.ones((H, W, 3), np.float32) * self.tone * light[..., None]
        self.img *= (1 - 0.03 * (self.tooth[..., None] - 0.5))

    # ------------------------------------------------------------ shapes (a child's hand: nothing is quite round or square)
    def wobble(self, pts, amp=3.0, closed=True, step=6.0, scale=14):
        """resample a polyline every `step` px and push it sideways by a slow fractal wobble of `amp` px"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        seg = np.hypot(*np.diff(P, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        n = max(8, int(s[-1] / step))
        ss = np.linspace(0, s[-1], n, endpoint=not closed)
        x, y = np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])
        tx, ty = np.gradient(x), np.gradient(y)
        tl = np.hypot(tx, ty) + 1e-6
        w = fbm1d(n, scale, 3, self._seed()) * amp
        if closed:                                   # make the wobble wrap so the shape stays closed
            k = max(3, n // 8)
            w[-k:] = w[-k:] * np.linspace(1, 0, k) + w[0] * np.linspace(0, 1, k)
        return np.stack([x - ty / tl * w, y + tx / tl * w], 1)

    def circle(self, cx, cy, rx, ry=None, rot=0.0, lumpy=0.04, amp=2.0):
        """a hand-drawn circle / ellipse outline (points)"""
        ry = rx if ry is None else ry
        n = max(40, int((rx + ry) * 0.5))
        return self.wobble(blob_pts(cx, cy, rx, ry, rough=lumpy, n=n, seed=self._seed(), rot=rot), amp)

    def rect(self, x0, y0, x1, y1, skew=4.0, amp=1.8):
        """a hand-drawn box: corners a little off, sides a little bent"""
        j = lambda: self.rng.normal(0, skew)
        pts = [(x0 + j(), y0 + j()), (x1 + j(), y0 + j()), (x1 + j(), y1 + j()), (x0 + j(), y1 + j())]
        return self.poly(pts, amp=amp)

    def poly(self, pts, amp=1.8):
        return self.wobble(pts, amp, closed=True)

    def mask(self, pts, ss=1):
        return polygon_mask(self.H, self.W, pts, ss=ss)

    def drawn(self, thresh=0.12):
        """mask of everything already on the paper -- pass it as `avoid` to colour round it"""
        return (self.wax > thresh).astype(np.float32)

    # ------------------------------------------------------------ the crayon itself
    def _tip(self, width, worn=0.35):
        """the worn crayon facet: K parallel sub-lines (offset, line width, strength)"""
        K = max(2, int(round(width / 3.0)))
        offs = (np.arange(K) + 0.5) / K - 0.5
        offs = offs * width + self.rng.normal(0, width * 0.04, K)
        lw = max(2, int(round(width / K * 1.55)))
        prof = 1 - 0.28 * (2 * np.abs(offs) / max(width, 1)) ** 2
        st = prof * self.rng.uniform(1 - worn, 1.0, K)
        st[self.rng.random(K) < 0.22] *= 0.4                  # a ridge that hardly touches -> white streak
        return offs, lw, st

    def _render(self, passes, nref=None):
        """passes: list of (pts (n,2), pressure, group, tip). Sub-lines are drawn as polylines on one L image per group,
        brightest last (so each group is the max of its strokes); groups then add up like layers of wax."""
        groups = {}
        boxes = []
        for pts, p, g, tip in passes:
            pts = np.asarray(pts, np.float32)
            if len(pts) < 2: continue
            offs, lw, st = tip
            if nref is not None:
                nx = np.full(len(pts), nref[0], np.float32); ny = np.full(len(pts), nref[1], np.float32)
            else:
                tx, ty = np.gradient(pts[:, 0]), np.gradient(pts[:, 1])
                tl = np.hypot(tx, ty) + 1e-6
                nx, ny = -ty / tl, tx / tl
            for o, s in zip(offs, st):
                q = np.stack([pts[:, 0] + nx * o, pts[:, 1] + ny * o], 1)
                v = int(np.clip(255 * p * s, 0, 255))
                if v < 6: continue
                groups.setdefault(g, []).append((v, lw, q))
            boxes.append((pts.min(0), pts.max(0), max(abs(offs).max(), 1) + lw))
        if not groups: return None, None
        lo = np.min([b[0] - b[2] for b in boxes], 0); hi = np.max([b[1] + b[2] for b in boxes], 0)
        x0, y0 = max(0, int(lo[0]) - 4), max(0, int(lo[1]) - 4)
        x1, y1 = min(self.W, int(hi[0]) + 5), min(self.H, int(hi[1]) + 5)
        if x1 <= x0 or y1 <= y0: return None, None
        keep = np.ones((y1 - y0, x1 - x0), np.float32)
        for g, items in groups.items():
            im = Image.new('L', (x1 - x0, y1 - y0), 0); d = ImageDraw.Draw(im)
            items.sort(key=lambda it: it[0])
            for v, lw, q in items:
                d.line([(float(a) - x0, float(b) - y0) for a, b in q], fill=v, width=lw, joint='curve')
            keep *= 1 - np.asarray(im, np.float32) / 255
        return 1 - keep, (x0, y0, x1, y1)

    def _drag(self, sl, angle, reach=6):
        """the tooth as the crayon feels it when dragged along `angle`: it rides from peak to peak, so the bare pits
        are drawn out into short streaks along the stroke (directional average of the tooth, re-equalised)"""
        t = self.tooth[sl]
        if angle is None: return t
        ca, sa = np.cos(np.radians(angle)), np.sin(np.radians(angle))
        P = reach + 2
        tp = np.pad(t, P, mode='edge')
        h, w = t.shape
        acc = np.zeros_like(t)
        ks = np.linspace(-reach, reach, 2 * reach + 1)
        for k in ks:
            dx, dy = k * ca, k * sa
            ix, iy = int(np.floor(dx)), int(np.floor(dy)); fx, fy = dx - ix, dy - iy
            a = tp[P + iy:P + iy + h, P + ix:P + ix + w]; b = tp[P + iy:P + iy + h, P + ix + 1:P + ix + 1 + w]
            c = tp[P + iy + 1:P + iy + 1 + h, P + ix:P + ix + w]; d = tp[P + iy + 1:P + iy + 1 + h, P + ix + 1:P + ix + 1 + w]
            acc += a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy
        acc /= len(ks)
        acc = 0.35 * t + 0.65 * acc
        hist, edges = np.histogram(acc, 256)
        cdf = np.cumsum(hist).astype(np.float32); cdf /= max(cdf[-1], 1)
        return np.interp(acc, edges[1:], cdf).astype(np.float32)

    def deposit(self, cover, box, colour, opacity=0.92, soft=0.6, angle=None):
        """rub wax of `colour` onto the paper where the contact field `cover` (crop at `box`) reaches the tooth;
        angle (deg): the stroke direction, which drags the bare pits out into streaks"""
        x0, y0, x1, y1 = box
        C = blur(cover, soft) if soft else cover
        sl = (slice(y0, y1), slice(x0, x1))
        surf = self._drag(sl, angle) + 0.35 * np.clip(self.wax[sl], 0, 1.4)
        dep = smoothstep(-0.09, 0.09, surf - (1 - C)) * smoothstep(0.03, 0.14, C)
        a = (dep * opacity)[..., None]
        under = self.img[sl]
        mix = _c(colour) * np.clip(under, 0, 1) ** 0.6
        self.img[sl] = under + (mix - under) * a
        self.wax[sl] += dep * (0.35 + 0.65 * C)

    def _pass(self, a, b, bow=0.0, jit=1.2, n=None):
        """one stroke from a to b, bowed sideways (a wrist arc) with a little hand tremor"""
        a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
        L = float(np.hypot(*(b - a)))
        n = n or max(4, int(L / 22))
        t = np.linspace(0, 1, n)[:, None]
        d = (b - a) / (L + 1e-6); nrm = np.array([-d[1], d[0]], np.float32)
        off = 4 * t * (1 - t) * bow + (fbm1d(n, max(3, n / 2), 2, self._seed())[:, None] * jit if n > 3 else 0)
        return a + (b - a) * t + nrm * off

    # ------------------------------------------------------------ colouring in
    def scribble(self, mask, colour, angle=20, width=20, density=0.7, pressure=0.8, reach=260, mess=0.5,
                 angle_jitter=9, avoid=None, halo=12, fade=None, opacity=0.92, bow=0.035):
        """colour a region in by scribbling back and forth.
        angle: stroke direction in degrees (0 = left-right, 90 = up-down); width: crayon contact width (px);
        density 0..1: how close the passes are (low = triangle gaps between them); pressure 0..1: how far the wax
        reaches into the tooth; reach: arm length -- big areas are coloured patch by patch, each patch at its own
        angle (None = one patch); mess 0..1: how far the turns overshoot the outline (or stop short of it);
        avoid / halo: a mask to colour around, leaving a white margin of `halo` px (clouds, letters, a sun);
        fade=(y_full, y_none): pressure dies away downwards and the passes give out (a sky the child got bored of)"""
        Mfull = (np.asarray(mask) > 0.5)
        M = Mfull.copy()
        keep = None
        if avoid is not None:
            keep = np.clip(np.asarray(avoid, np.float32), 0, 1)
            M &= ~(blur(keep, max(1.0, halo * 0.5)) > 0.08) if halo else ~(keep > 0.5)
        ys, xs = np.nonzero(M)
        if len(xs) < 20: return
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        a0 = np.radians(angle)
        U0 = np.array([np.cos(a0), np.sin(a0)], np.float32); V0 = np.array([-U0[1], U0[0]], np.float32)
        corners = np.array([[x0, y0], [x1, y0], [x0, y1], [x1, y1]], np.float32)
        cu, cv = corners @ U0, corners @ V0
        s = width * (2.3 - 1.6 * density)
        if reach is None:
            nu, nv = 1, 1; Lu, Lv = cu.max() - cu.min() + 4 * width, cv.max() - cv.min() + 4 * width
        else:
            Lu, Lv = reach, reach * 1.3
            nu = max(1, int(np.ceil((cu.max() - cu.min()) / Lu))); nv = max(1, int(np.ceil((cv.max() - cv.min()) / Lv)))
            Lu, Lv = (cu.max() - cu.min()) / nu, (cv.max() - cv.min()) / nv
        tip = self._tip(width)
        passes = []
        order = [(i, j) for i in range(nu) for j in range(nv)]
        for k, (i, j) in enumerate(order):
            uc = cu.min() + (i + 0.5) * Lu + self.rng.normal(0, Lu * 0.06)
            vc = cv.min() + (j + 0.5) * Lv + self.rng.normal(0, Lv * 0.06)
            c = U0 * uc + V0 * vc
            ap = a0 + np.radians(self.rng.normal(0, angle_jitter)) if (nu * nv > 1) else a0 + np.radians(self.rng.normal(0, angle_jitter * 0.3))
            U = np.array([np.cos(ap), np.sin(ap)], np.float32); V = np.array([-U[1], U[0]], np.float32)
            hu = Lu * (0.62 if nu > 1 else 0.6) + (width if nu == 1 else 0)
            hv = Lv * (0.6 if nv > 1 else 0.6) + (width if nv == 1 else 0)
            us = np.arange(-hu, hu, 2.0, dtype=np.float32)
            rows = np.arange(-hv + s * 0.25, hv, s / 2, dtype=np.float32)
            chains, active = [], []
            for r, v in enumerate(rows):
                px = c[0] + us * U[0] + v * V[0]; py = c[1] + us * U[1] + v * V[1]
                ix, iy = np.round(px).astype(int), np.round(py).astype(int)
                ok = (ix >= 0) & (iy >= 0) & (ix < self.W) & (iy < self.H)
                ins = np.zeros(len(us), bool); ins[ok] = M[iy[ok], ix[ok]]
                if not ins.any():
                    active = []; continue
                full = np.zeros(len(us), bool); full[ok] = Mfull[iy[ok], ix[ok]]
                dd = np.diff(np.concatenate([[0], ins.astype(np.int8), [0]]))
                st, en = np.nonzero(dd == 1)[0], np.nonzero(dd == -1)[0] - 1
                # run end kinds: 1 = the outline, 2 = something to colour round (careful), 0 = the arm's reach
                kind = lambda i: 0 if (i < 0 or i >= len(us)) else (2 if full[i] else 1)
                minrun = max(2, int(0.35 * width))         # (samples are 2 px) no gaps narrower than 0.7 x width
                runs = [(us[a], us[b], kind(a - 1), kind(b + 1)) for a, b in zip(st, en) if b - a >= minrun]
                new_active = []
                for run in runs:
                    hit = None
                    for ch in active:
                        la, lb = ch[-1][1], ch[-1][2]
                        if min(lb, run[1]) - max(la, run[0]) > 0.3 * min(lb - la, run[1] - run[0]) and ch not in new_active:
                            hit = ch; break
                    if hit is None:
                        hit = []; chains.append(hit)
                    hit.append((v, run[0], run[1], run[2], run[3]))
                    new_active.append(hit)
                active = new_active
            for ch in chains:
                if len(ch) < 2 and (ch[0][2] - ch[0][1]) < width: continue
                side = self.rng.integers(2)
                turns = []
                for r, (v, ua, ub, ea, eb) in enumerate(ch):
                    left = (r + side) % 2 == 0
                    edge = ea if left else eb
                    u = ua if left else ub
                    if edge == 1:                                # a real outline: overshoot it or stop short
                        o = float(np.clip(self.rng.normal(mess * 7 - 2.5, 2.5 + mess * 5), -9, 26)) - width * 0.32
                    elif edge == 2:                              # colouring round something: careful, stop short
                        o = float(np.clip(self.rng.normal(0, 2.0), -5, 4)) - width * 0.45
                    else:                                        # the edge of the arm's reach
                        o = self.rng.normal(0, 7)
                    u = u - o if left else u + o
                    turns.append(c + U * u + V * v)
                pb = bow * self.rng.choice([-1, 1]) * Lu
                prs = pressure * (0.84 + 0.36 * fbm1d(max(len(turns), 4), 5, 2, self._seed()))
                for q in range(len(turns) - 1):
                    A, B = turns[q], turns[q + 1]
                    pp = prs[q]
                    if fade is not None:
                        my = (A[1] + B[1]) / 2
                        f = float(np.clip((fade[1] - my) / (fade[1] - fade[0]), 0, 1))
                        if self.rng.random() > f ** 0.6 + 0.05: continue
                        pp *= 0.45 + 0.55 * f
                    passes.append((self._pass(A, B, bow=pb), pp, (k % 2) * 2 + q % 2, tip))
        cover, box = self._render(passes)
        if cover is None: return
        if keep is not None:                             # the things coloured round stay (mostly) clean
            bx0, by0, bx1, by1 = box
            cover = cover * (1 - 0.9 * blur(keep[by0:by1, bx0:bx1], 1.5))
        self.deposit(cover, box, colour, opacity, angle=angle)

    def loops(self, mask, colour, r=16, width=12, density=0.7, pressure=0.8, mess=0.4, avoid=None, halo=10, opacity=0.92):
        """colour a region in with a coiled circle scribble ('eeeee'), the way children fill tree tops, suns and
        bushes; the coil wanders back and forth across the shape; loops near the edge spill over it a little"""
        M = (np.asarray(mask) > 0.5)
        if avoid is not None:
            M &= ~(blur(np.asarray(avoid, np.float32), max(1.0, halo * 0.5)) > 0.08)
        inner = blur(M.astype(np.float32), r * (0.55 - 0.35 * mess)) > 0.5
        if inner.sum() < 30: inner = M
        ys, xs = np.nonzero(inner)
        if len(xs) < 5: return
        s = r * (2.4 - 1.5 * density)
        a = self.rng.uniform(-0.4, 0.4)
        U = np.array([np.cos(a), np.sin(a)], np.float32); V = np.array([-U[1], U[0]], np.float32)
        pts = np.stack([xs, ys], 1).astype(np.float32)
        pu, pv = pts @ U, pts @ V
        tip = self._tip(width)
        passes, k = [], 0
        for r_i, v in enumerate(np.arange(pv.min(), pv.max() + 1, s)):
            sel = np.abs(pv - v) < s * 0.5
            if not sel.any(): continue
            ua, ub = pu[sel].min(), pu[sel].max()
            if (r_i % 2): ua, ub = ub, ua
            L = abs(ub - ua)
            nl = max(1, int(L / (r * 0.75)))
            t = np.linspace(0, 1, nl * 18 + 1)
            ph = t * nl * 2 * np.pi * (1 if r_i % 2 == 0 else -1) + self.rng.uniform(0, 6.3)
            rr = r * (0.85 + 0.3 * fbm1d(len(t), 30, 2, self._seed()))
            cu_ = ua + (ub - ua) * t
            cx = cu_ * U[0] + v * V[0] + rr * np.cos(ph); cy = cu_ * U[1] + v * V[1] + rr * 0.85 * np.sin(ph)
            q = np.stack([cx, cy], 1)
            for j in range(nl):                      # one group per loop, so the overlaps add up
                seg = q[j * 18:(j + 1) * 18 + 1]
                passes.append((seg, pressure * self.rng.uniform(0.85, 1.08), k % 3, tip)); k += 1
        cover, box = self._render(passes)
        if cover is not None: self.deposit(cover, box, colour, opacity)

    def follow(self, pts, colour, width=26, passes=3, crayon=14, pressure=0.85, back=True, opacity=0.92, spread=1.0):
        """fill a band along a path with strokes that follow it (rainbow arcs, roads, a kite tail, smoke):
        `passes` strokes side by side across `width`, each starting and stopping a bit early or late"""
        P = np.asarray(pts, np.float32)
        tx, ty = np.gradient(P[:, 0]), np.gradient(P[:, 1]); tl = np.hypot(tx, ty) + 1e-6
        nx, ny = -ty / tl, tx / tl
        tip = self._tip(crayon)
        out = []
        n = len(P)
        for k in range(passes):
            o = ((k + 0.5) / passes - 0.5) * (width - crayon * 0.6) * spread + self.rng.normal(0, 1.5)
            a, b = int(self.rng.integers(0, max(1, n // 25) + 1)), n - int(self.rng.integers(0, max(1, n // 25) + 1))
            q = P[a:b] + np.stack([nx[a:b], ny[a:b]], 1) * (o + fbm1d(b - a, 20, 2, self._seed())[:, None] * 1.6)
            if back and k % 2: q = q[::-1]
            out.append((q, pressure * self.rng.uniform(0.88, 1.06), k % 2, tip))
        cover, box = self._render(out)
        if cover is not None: self.deposit(cover, box, colour, opacity)

    # ------------------------------------------------------------ lines
    def line(self, pts, colour, width=9, pressure=0.9, closed=False, overlap=0.07, wobble=1.2, opacity=0.95, lift=True,
             avoid=None):
        """one crayon line: pressure swells and fades along it (lands heavy, lifts light). closed=True draws a shape
        the way a child does: round once, then the end runs on past the start and misses it by a few px.
        avoid: a mask the line stops at (a hill line that goes behind the people instead of through their faces)"""
        P = np.asarray(pts, np.float32)
        if closed:
            seg = np.hypot(*np.diff(np.vstack([P, P[:1]]), axis=0).T)
            k = max(2, int(len(P) * overlap * self.rng.uniform(0.6, 1.4)))
            drift = np.linspace(0, 1, k)[:, None] * self.rng.normal(0, 4.0, 2)[None]
            P = np.vstack([P, P[:1], P[1:k + 1] + drift[:len(P[1:k + 1])]])
        if wobble:
            P = self.wobble(P, wobble, closed=False, step=5, scale=10)
        n = len(P)
        if n < 2: return
        prs = pressure * (0.86 + 0.28 * fbm1d(n, max(4, n / 4), 2, self._seed()))
        if lift:
            t = np.linspace(0, 1, n)
            prs = prs * np.clip(0.75 + 0.25 * np.minimum(t / 0.06, 1), 0, 1.1) * np.clip(1 - 0.35 * smoothstep(0.86, 1, t), 0, 1)
        tip = self._tip(width, worn=0.25)
        out = []
        step = 8
        for i in range(0, n - 1, step):
            out.append((P[i:i + step + 1], float(prs[i]), 0, tip))
        cover, box = self._render(out)
        if cover is None: return
        if avoid is not None:
            x0, y0, x1, y1 = box
            cover = cover * (1 - np.clip(np.asarray(avoid, np.float32)[y0:y1, x0:x1], 0, 1))
        self.deposit(cover, box, colour, opacity, soft=0.5)

    def stroke_mask(self, pts, width, closed=False):
        """a mask of a polyline drawn `width` px wide (to keep fills off arms, legs, stems and strings)"""
        im = Image.new('L', (self.W, self.H), 0)
        P = [tuple(map(float, q)) for q in np.asarray(pts, np.float32)]
        if closed: P = P + P[:1]
        ImageDraw.Draw(im).line(P, fill=255, width=int(width), joint='curve')
        return np.asarray(im, np.float32) / 255

    def grow(self, mask, px):
        """dilate a mask by about `px` pixels"""
        return (blur(np.asarray(mask, np.float32), max(0.8, px * 0.5)) > 0.08).astype(np.float32)

    def lines(self, paths, colour, **kw):
        for p in paths: self.line(p, colour, **kw)

    def dab(self, x, y, r, colour, pressure=1.0, turns=None):
        """a pressed-in dot (eyes, buttons, seeds): a tight spiral ground into the paper"""
        turns = turns or max(1.5, r / 4)
        t = np.linspace(0, 1, int(turns * 24))
        ang = t * turns * 2 * np.pi + self.rng.uniform(0, 6.3)
        rr = r * (0.25 + 0.6 * t)
        pts = np.stack([x + rr * np.cos(ang), y + rr * 0.9 * np.sin(ang)], 1)
        tip = self._tip(max(4, r * 0.8), worn=0.15)
        cover, box = self._render([(pts, pressure, 0, tip), (pts[::-1], pressure * 0.9, 1, tip)])
        if cover is not None: self.deposit(cover, box, colour, 0.96, soft=0.5)

    def burnish(self, mask, strength=0.8):
        """press hard and rub: the wax already there is pushed down into the pits of the tooth, the white specks close
        up, the colour goes deep and the surface turns waxy and shiny (heavy sunglasses, a ball, a roof)"""
        m = np.clip(np.asarray(mask, np.float32), 0, 1)
        ys, xs = np.nonzero(m > 0.01)
        if len(xs) == 0: return
        x0, x1, y0, y1 = max(0, xs.min() - 12), min(self.W, xs.max() + 13), max(0, ys.min() - 12), min(self.H, ys.max() + 13)
        sl = (slice(y0, y1), slice(x0, x1))
        mm = m[sl]
        w = np.clip(self.wax[sl], 0, 1)
        avg = np.stack([blur(self.img[sl][..., k] * w, 3) for k in range(3)], -1) / (blur(w, 3)[..., None] + 1e-4)
        fill = (mm * strength * smoothstep(0.05, 0.3, blur(w, 3)))[..., None]
        self.img[sl] = self.img[sl] * (1 - fill) + np.clip(avg * 0.96, 0, 1) * fill
        self.wax[sl] += mm * strength * 0.8

    # ------------------------------------------------------------ writing
    def write(self, s, x, y, size, colours, width=None, pressure=0.95, tilt=9, jumble=0.12, spacing=0.92, anchor='m'):
        """write like a six-year-old: each character re-drawn with a fat round crayon over the centre line of a thin
        glyph, every one tilted (+-tilt deg), resized and lifted off the baseline (jumble), in its own colour.
        colours: one colour or a list cycled per character; anchor 'l' / 'm' / 'r' on x; y is the middle of the line"""
        if isinstance(colours, str) or (hasattr(colours, 'shape') and np.asarray(colours).ndim == 1):
            colours = [colours]
        width = width or max(5, size * 0.068)
        chars = list(s)
        sizes = [size * (1 + self.rng.normal(0, jumble)) for ch in chars]
        adv = [_thin_font(sz).getlength(ch) * spacing + width * 0.6 for ch, sz in zip(chars, sizes)]
        tot = sum(adv)
        cx = x - tot * {'l': 0, 'm': 0.5, 'r': 1}[anchor]
        for i, (ch, sz) in enumerate(zip(chars, sizes)):
            if ch.strip():
                self._glyph(ch, cx + adv[i] / 2, y + self.rng.normal(0, size * jumble * 0.6), sz,
                            colours[i % len(colours)], width, pressure, self.rng.normal(0, tilt))
            cx += adv[i]

    def _glyph(self, ch, cx, cy, size, colour, width, pressure, rot):
        font = _thin_font(size)
        pad = int(size * 0.5 + width * 2)
        S = int(size) + 2 * pad
        im = Image.new('L', (S, S), 0)
        ImageDraw.Draw(im).text((S / 2, S / 2), ch, font=font, fill=255, anchor='mm')
        im = im.rotate(rot, resample=Image.BICUBIC)
        g = np.asarray(im, np.float32) / 255
        # warp the glyph with a slow hand wobble
        n1, n2 = noise2d(S, S, size * 0.55, 2, self._seed()), noise2d(S, S, size * 0.55, 2, self._seed())
        amp = size * 0.045
        yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
        sx = np.clip(xx + (n1 - 0.5) * 2 * amp, 0, S - 1.001); sy = np.clip(yy + (n2 - 0.5) * 2 * amp, 0, S - 1.001)
        ix, iy = sx.astype(int), sy.astype(int); fx, fy = sx - ix, sy - iy
        g = (g[iy, ix] * (1 - fx) * (1 - fy) + g[iy, ix + 1] * fx * (1 - fy) + g[iy + 1, ix] * (1 - fx) * fy + g[iy + 1, ix + 1] * fx * fy)
        core = _thin((g > 0.4)).astype(np.float32)
        # fat round crayon over the centre line: dilate with a disc
        r = width / 2
        out = core.copy()
        R = int(np.ceil(r))
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                if dx * dx + dy * dy <= r * r and (dx or dy):
                    np.maximum(out, shift(core, dx, dy), out=out)
        out = blur(out, 0.8)
        # streaks along a random stroke direction + pressure patches
        a = self.rng.uniform(0, np.pi)
        proj = (xx * np.cos(a) + yy * np.sin(a)) - (xx * np.cos(a) + yy * np.sin(a)).min()
        st = fbm1d(int(proj.max()) + 2, 4, 2, self._seed())
        streak = 0.84 + 0.16 * st[proj.astype(int)]
        cov = out * streak * (0.8 + 0.25 * noise2d(S, S, 18, 2, self._seed())) * pressure
        x0, y0 = int(cx) - S // 2, int(cy) - S // 2
        X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(self.W, x0 + S), min(self.H, y0 + S)
        if X1 <= X0 or Y1 <= Y0: return
        self.deposit(cov[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0], (X0, Y0, X1, Y1), colour, 0.95, soft=0)

    # ------------------------------------------------------------ the table top: crumbs and crayons
    def crumbs(self, x0, y0, x1, y1, colours, n=40, size=(2, 6)):
        """flakes of wax rubbed off the crayon, lying on the paper (they catch the light and cast a shadow)"""
        if isinstance(colours, str): colours = [colours]
        for _ in range(n):
            cx, cy = self.rng.uniform(x0, x1), self.rng.uniform(y0, y1)
            r = self.rng.uniform(*size)
            m = self.mask(blob_pts(cx, cy, r, r * self.rng.uniform(0.5, 1.0), rough=0.3, n=12, seed=self._seed(),
                                   rot=self.rng.uniform(0, 6.3)), ss=2)
            col = _c(colours[int(self.rng.integers(len(colours)))])
            self.img = self.img * (1 - m[..., None]) + col * m[..., None] * (0.92 + 0.08 * self.tooth[..., None])
            self.crumb = np.maximum(self.crumb, m * r * 0.5)

    def stick(self, x, y, angle, colour, length=360, radius=22, wrapper=True, wrap=(0.16, 0.86), tip='worn',
              band=None, peel=0.0, label=True):
        """a real crayon lying on the paper, centred on (x, y), pointing along `angle` (deg, tip end).
        tip: 'worn' (a cone ground flat on one side), 'new' (a sharp cone) or 'broken' (a jagged snapped end);
        wrapper: paper sleeve between wrap=(t0, t1) of the length; band: wrapper print colour; peel: 0..1 of the
        sleeve torn off from the tip end; label: print the sleeve (rules, wavy bands, a line of pseudo-lettering,
        no brand). A real crayon (~8 mm) on an A4 sheet 1920 px wide would be radius ~26 px; 22 keeps it from crowding
        the drawing. Rendered with its own shading (matte wax, satin sheen, paper sleeve) and a soft shadow at
        composite time."""
        self.over.append(dict(x=x, y=y, a=np.radians(angle), col=_c(colour), L=length, r=radius, wrapper=wrapper,
                              wrap=wrap, tip=tip, band=_c(band) if band is not None else None, peel=peel,
                              label=label, seed=self._seed()))

    def _draw_stick(self, img, s, light):
        H, W = self.H, self.W
        ca, sa = np.cos(s['a']), np.sin(s['a'])
        L, R = s['L'], s['r']
        pad = int(L / 2 + R * 3 + 30)
        x0, y0 = max(0, int(s['x'] - pad)), max(0, int(s['y'] - pad))
        x1, y1 = min(W, int(s['x'] + pad)), min(H, int(s['y'] + pad))
        if x1 <= x0 or y1 <= y0: return img
        XX, YY = self.XX[y0:y1, x0:x1] - s['x'], self.YY[y0:y1, x0:x1] - s['y']
        al = XX * ca + YY * sa                       # px along the stick, tip end positive
        t = al / L + 0.5                             # 0 = butt end .. 1 = tip end
        d = -XX * sa + YY * ca                       # px across the stick
        # radius along the stick: a cone at the tip, worn flat on one side, or a snapped end
        rad = np.full(t.shape, float(R), np.float32)
        cone = 0.15                                 # the last 15 % of the stick is the tip
        if s['tip'] in ('new', 'worn'):
            k = np.clip((t - (1 - cone)) / cone, 0, 1)
            rad = R * (1 - k * (0.9 if s['tip'] == 'new' else 0.62))
        end = np.ones_like(t, bool)
        if s['tip'] == 'broken':
            jag = fbm1d(64, 5, 3, s['seed'])
            idx = np.clip(((d / R + 1) * 0.5 * 63).astype(int), 0, 63)
            end = t < 1 - 0.03 * (1.2 + jag[idx])
        butt = np.sqrt(np.clip(1 - (d / R) ** 2, 0, 1)) * 2.5      # the butt end is slightly domed
        inside = (np.abs(d) < rad) & (al > -L / 2 - butt) & (t < 1.0) & end
        m = blur(inside.astype(np.float32), 0.7)
        sl = (slice(y0, y1), slice(x0, x1))
        sh = blur(shift(m, 7, 10), 6) * 0.45 + blur(shift(m, 2, 3), 1.5) * 0.25      # soft shadow + contact shadow
        img[sl] *= (1 - np.clip(sh, 0, 0.6)[..., None])
        u = np.clip(d / np.maximum(rad, 1e-3), -1, 1)
        nz = np.sqrt(np.clip(1 - u * u, 0, 1))
        N = np.stack([-sa * u, ca * u, nz], -1)
        if s['tip'] == 'worn':                       # the flat wear facet near the tip, facing up and forward
            f = (t > 1 - cone * 0.9) & (u > -0.2)
            N[f] = np.array([0.35 * ca, 0.35 * sa, 0.94]) / np.linalg.norm([0.35, 0.94])
        Ld = np.asarray(light, np.float32); Ld /= np.linalg.norm(Ld)
        diff = np.clip(N @ Ld, 0, 1)
        Hh = Ld + np.array([0, 0, 1], np.float32); Hh /= np.linalg.norm(Hh)
        spec = np.clip(N @ Hh, 0, 1) ** 12
        out = s['col'] * (0.45 + 0.62 * diff[..., None]) + 0.13 * spec[..., None]      # matte wax, satin sheen
        rng = np.random.default_rng(s['seed'])
        if s['wrapper']:
            w0, w1 = s['wrap']
            peel_to = w1 - (w1 - w0) * s['peel']
            ragged = 0.015 * fbm1d(64, 8, 3, s['seed'] + 1)[np.clip(((u + 1) * 31.5).astype(int), 0, 63)]
            onw = (t > w0) & (t < peel_to + ragged) & inside
            tt = (t - w0) / (w1 - w0)
            base = s['band'] if s['band'] is not None else np.clip(s['col'] * 0.9, 0, 1)
            ink = np.clip(s['col'] * 0.25, 0, 1)
            wc = np.ones(t.shape + (3,), np.float32) * base
            if s['label']:
                rules = np.zeros(t.shape, bool)
                for r0 in (0.05, 0.085, 0.915, 0.95):
                    rules |= np.abs(tt - r0) < 0.008
                wave = (np.abs(((tt * 22 + 0.18 * np.sin(u * 3.0)) % 1.0) - 0.5) < 0.07) & (((tt > 0.13) & (tt < 0.25)) | ((tt > 0.75) & (tt < 0.87)))
                lab = (tt > 0.29) & (tt < 0.71)
                wc = np.where(lab[..., None], np.clip(base * 0.35 + 0.66, 0, 1), wc)
                # one line of pseudo-lettering along the label (no real words)
                ls = tt * (w1 - w0) * L
                word = fbm1d(int((w1 - w0) * L) + 4, 30, 2, s['seed'] + 3)
                inword = word[np.clip(ls.astype(int), 0, len(word) - 1)] > -0.25
                glyph = ((ls / 6.5) % 1.0) < 0.62
                txt = lab & (tt > 0.34) & (tt < 0.66) & (np.abs(u - 0.05) < 0.2) & inword & glyph
                wc = np.where((rules | wave | txt)[..., None], ink, wc)
            wrap_col = wc * (0.5 + 0.56 * diff[..., None]) + 0.03 * spec[..., None]
            out = np.where(onw[..., None], wrap_col, out)
            # torn edge of the sleeve: a thin light lip, and scrape marks on the bare wax beyond it
            lip = onw & ~shift(onw.astype(np.float32), int(round(-ca * 2)), int(round(-sa * 2))).astype(bool)
            out = np.where(lip[..., None], np.clip(out * 0.8 + 0.25, 0, 1), out)
        if s['tip'] == 'broken':                     # the snapped face is rough and a bit lighter
            face = inside & ~(t < 1 - 0.03 * 3.4)
            out = np.where(face[..., None], np.clip(out * (1.04 + 0.1 * rng.random(t.shape))[..., None], 0, 1), out)
        scr = 0.05 * fbm1d(256, 3, 2, s['seed'] + 2)[np.clip(((u + 1) * 127.5).astype(int), 0, 255)]
        out = np.clip(out * (1 + scr[..., None]), 0, 1)
        img[sl] = img[sl] * (1 - m[..., None]) + out * m[..., None]
        return img

    # ------------------------------------------------------------ output
    def composite(self, light=(-0.55, -0.62, 0.56)):
        """light the paper and the wax as one height field (a raking light from the top left), add the wax sheen,
        then lay the crumbs and the crayons on top"""
        h = self.relief * 0.65 + blur(np.clip(self.wax, 0, 1.6), 1.6) * 0.55 + self.crumb
        n = height_normals(h)
        Ld = np.asarray(light, np.float32); Ld /= np.linalg.norm(Ld)
        diff = n @ Ld
        shade = 1 + 0.55 * (diff - Ld[2])
        Hh = Ld + np.array([0, 0, 1], np.float32); Hh /= np.linalg.norm(Hh)
        spec = np.clip(n @ Hh, 0, 1) ** 40 * smoothstep(0.6, 1.4, self.wax) * 0.10
        img = self.img * shade[..., None] + spec[..., None]
        if self.crumb.any():                          # crumbs cast a small shadow
            cs = blur(shift((self.crumb > 0).astype(np.float32), 2, 3), 1.5) * (self.crumb <= 0)
            img = img * (1 - 0.35 * cs[..., None])
        for s in self.over:
            img = self._draw_stick(img, s, light)
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        """snapshot for the draw-on animation"""
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
