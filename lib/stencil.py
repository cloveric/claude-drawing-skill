"""stencil — spray-paint stencil graffiti on a board-marked concrete wall (numpy + Pillow only).

Model: a real wall, real stencils cut from card, and a spray can whose paint is a cloud of droplets.
  wall       board-marked cast concrete, built as an albedo map plus a height map lit by one low sun from the upper
             left. The formwork was a row of sawn planks, so the wall is banded: each plank-high band has its own
             tone and a fraction of a pixel of step, the sawn wood grain is pressed into the surface (wavy grain
             lines flowing round the odd knot), board ends make short vertical joints, and cement paste that
             squeezed between the boards left a thin broken fin along every seam. Form-tie holes are cone-shaped
             recesses on a regular grid, some still with the rusted rod end, some plugged with paler mortar. Air
             bubbles left bug holes (small pits). Weather does the rest: rain streaks hanging from the ties and the
             seams, rust stains under some ties, a damp splash zone above the pavement with a tide line and a white
             efflorescence crust, a hairline crack, dust.
  history    the wall was painted before: `buff()` is a council roller patch of not-quite-matching grey laid on in
             vertical passes (stepped top and bottom edges, dry streaky ends, darker laps) over an old tag whose
             ghost still shows through; `freehand(..., wash=)` is an old tag half taken off by a pressure washer.
  stencil    `card()` is a sheet of card; you cut openings in it (shapes, letters) and paint goes only through the
             openings. Any piece of card that the cuts surround completely (the middle of an O, the gap between an
             arm and a body, the spaces between the spokes of a reel) would fall out, so it must be held by
             bridges: thin strips of uncut card that show up in the paint as hairlines of bare wall.
             `bridges()` finds those islands and cuts the shortest bridges automatically; `text()` bridges every
             counter top and bottom like a stencil typeface. A picture in several tones is several cards, sprayed
             light to dark; each card goes on a few pixels off, so the lighter layer peeks out along one side.
  spray      the can moves across the card in overlapping sweeps; each sweep deposits a soft cone of paint, so the
             paint film is the sum of gaussian strokes along the path (heavier where the can slowed or lingered).
             Through the openings the film reaches the wall: where the card lay flat (near the tape) the edge is
             knife-crisp, where it lifted the paint creeps under it as a soft fringe; a fine mist drifts further
             (the overspray halo) and the sweeps that overshoot the card leave a faint straight-edged ghost of the
             sheet itself. Coverage comes from droplets: a thick film is solid, a thin one is a scatter of dots, so
             every soft edge is speckled rather than blurred. Paint is opaque or not by pigment (black hides in one
             coat, white needs more), it does not reach the bottom of pits, it lies on the relief (the wood grain
             and the seams show through it) and it has a satin sheen. Where the film is too thick at the lower
             edge of an opening, paint runs: a drip with a neck, a thin tail and a bead at the end, raised and
             glossy.
  freehand   `freehand()` is the can without a stencil (a skinny cap): a soft line whose width and weight follow the
             hand's speed, a little spatter, a spit of paint where the nozzle started, drips where it paused.
Coordinates are pixels on the wall; a card can carry its own design origin and scale (`card(..., origin, scale)`)
so a figure can be written once in its own units. Angles are degrees counter-clockwise.

    from stencil import Stencil, shade_side, BLACK, WHITE, RED
    s = Stencil(1920, 1080, seed=7)
    s.wall(ground=1000); s.pavement()
    c = s.card(1250, 500, 1650, 1000, origin=(1450, 994))           # the sheet, and where design (0, 0) sits
    body = np.maximum(c.capsule((0, -60), (0, -300), 60, 45), c.ellipse((0, -360), 40))
    c.cut(body); c.keep(c.text('HI', 0, -170, 90, anchor='ms', bridge=0))   # knocked-out letters: loose card
    c.bridges()                                                       # ... so hold every island with bridges
    s.spray(c, BLACK, drips=1.0)
    s.stage('figure', card=c)                                         # snapshot with the card still taped up
    s.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, noise2d, smoothstep, shift, latin_font, spline, fbm1d, height_normals, height_shadow

CONCRETE = '#a9a398'
BLACK, WHITE, GREY, RED = '#161616', '#ece8de', '#7b7c79', '#cf2a1f'
HIDE = {BLACK: 3.4, GREY: 2.8, RED: 2.4, WHITE: 2.0}          # hiding power per unit of film
GLOSS = {BLACK: 0.55, GREY: 0.35, RED: 0.4, WHITE: 0.25}      # satin sheen on the relief


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _aniso(h, w, sx, sy, octaves, seed):
    """value noise in [0, 1] stretched sx by sy px (wood grain, streaks)"""
    r = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = max(2, int(h / sy * 2 ** o) + 2), max(2, int(w / sx * 2 ** o) + 2)
        g = Image.fromarray(r.random((gh, gw)).astype(np.float32))
        out += amp * np.asarray(g.resize((w, h), Image.BICUBIC), np.float32)
        tot += amp; amp *= 0.5
    out /= tot
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def _disc_splat(arr, x, y, r, val, mode='min'):
    """stamp a soft disc (radius r) into arr at (x, y): mode min/max/add; val scales the profile"""
    H, W = arr.shape
    R = int(np.ceil(r + 2))
    x0, x1, y0, y1 = int(x) - R, int(x) + R + 1, int(y) - R, int(y) + R + 1
    if x1 <= 0 or y1 <= 0 or x0 >= W or y0 >= H: return
    xa, ya = max(x0, 0), max(y0, 0)
    xb, yb = min(x1, W), min(y1, H)
    yy, xx = np.mgrid[ya:yb, xa:xb].astype(np.float32)
    d = np.hypot(xx - x, yy - y)
    prof = np.clip(r + 0.5 - d, 0, 1) if r < 1.5 else np.clip(1 - (d / (r + 0.5)) ** 2, 0, 1)
    sl = arr[ya:yb, xa:xb]
    if mode == 'min': np.minimum(sl, val * prof, out=sl)
    elif mode == 'max': np.maximum(sl, val * prof, out=sl)
    else: sl += val * prof


def _geo_fill(seed, allowed, iters=4000):
    """geodesic flood: grow `seed` inside `allowed` (both bool) until it stops changing"""
    cur = seed & allowed
    for i in range(iters):
        nxt = cur.copy()
        nxt[1:] |= cur[:-1]; nxt[:-1] |= cur[1:]
        nxt[:, 1:] |= cur[:, :-1]; nxt[:, :-1] |= cur[:, 1:]
        nxt &= allowed
        if i % 8 == 7 and np.array_equal(nxt, cur): break
        cur = nxt
    return cur


def shade_side(mask, light=(-1.0, -1.0), depth=20.0, soft=2.0, wobble=0.0, seed=0):
    """posterised form shadow for a stencil plate: the part of `mask` whose far side (away from `light`) lies
    within `depth` px -- a crescent along the shadow side, like the dark plate of a two-tone stencil.
    wobble (0..1) varies the depth along the edge so the shadow reads cut by hand, not offset by machine."""
    lx, ly = light
    l = np.hypot(lx, ly) + 1e-6
    m = blur(mask, soft) if soft else mask

    def far(d):
        return shift(m, lx / l * d, ly / l * d)               # = mask one step of d further away from the light

    if wobble:
        h, w = mask.shape
        n = noise2d(h, w, max(10.0, depth * 2.0), 2, seed)
        f = far(depth * (1 - wobble)) * (1 - n) + far(depth * (1 + wobble)) * n
    else:
        f = far(depth)
    return np.clip(mask * (1 - smoothstep(0.35, 0.65, f)), 0, 1).astype(np.float32)


# ====================================================================== the stencil sheet
class Card:
    """a sheet of card with openings cut in it. Shapes are made in design units (origin + scale), return local
    masks (h, w) in [0, 1] that can be combined with numpy, and are cut with `cut()`."""

    def __init__(self, st, x0, y0, x1, y1, origin=None, scale=1.0, tape=None, material='manila', seed=0):
        self.st = st
        self.x0, self.y0 = int(np.floor(x0)), int(np.floor(y0))
        self.x1, self.y1 = int(np.ceil(x1)), int(np.ceil(y1))
        self.w, self.h = self.x1 - self.x0, self.y1 - self.y0
        self.ox, self.oy = origin if origin is not None else (self.x0, self.y0)
        self.k = float(scale)
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.open = np.zeros((self.h, self.w), np.float32)
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32)
        self.YY, self.XX = yy, xx
        # the sheet itself: a knife-cut rectangle with slightly wandering edges and one clipped corner
        e = 0.9 * fbm1d(self.w, 120, 3, seed + 1)
        f = 0.9 * fbm1d(self.h, 120, 3, seed + 2)
        inside = ((yy > 1.5 + e[None, :]) & (yy < self.h - 2.5 + e[None, :] * 0.7) &
                  (xx > 1.5 + f[:, None]) & (xx < self.w - 2.5 - f[:, None] * 0.7))
        cc = self.rng.uniform(10, 26)
        inside &= (xx + yy > cc)
        self.sheet = blur(inside.astype(np.float32), 0.6)
        if tape is None:                                       # masking tape at three corners and one edge
            tape = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 0.55)]
        self.tape = [(tx * self.w, ty * self.h) for tx, ty in tape]
        self.material = material

    # ------------------------------------------------------------ design units -> local px
    def P(self, pts):
        p = np.asarray(pts, np.float32).reshape(-1, 2)
        return np.stack([self.ox - self.x0 + p[:, 0] * self.k, self.oy - self.y0 + p[:, 1] * self.k], 1)

    def _poly_mask(self, pts, ss=4):
        im = Image.new('L', (self.w * ss, self.h * ss), 0)
        ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in pts], fill=255)
        im = im.reduce(ss)
        return np.asarray(im, np.float32) / 255

    # ------------------------------------------------------------ shapes (do not cut yet)
    def poly(self, pts, smooth=False, per=10, facet=0.0):
        """closed outline. smooth: Catmull-Rom through the points. facet: px of knife jitter (cut as short straight
        segments, the way a blade follows a curve)"""
        P = self.P(pts)
        if smooth:
            Q = np.vstack([P, P[:2]])
            P = spline(Q, per)[: len(P) * per]
        if facet:
            seg = np.linalg.norm(np.diff(np.vstack([P, P[:1]]), axis=0), axis=1)
            L = np.concatenate([[0], np.cumsum(seg)])
            n = max(8, int(L[-1] / 7))
            s = np.linspace(0, L[-1], n, endpoint=False)
            Pc = np.vstack([P, P[:1]])
            P = np.stack([np.interp(s, L, Pc[:, 0]), np.interp(s, L, Pc[:, 1])], 1)
            P = P + self.rng.normal(0, facet, P.shape)
        return self._poly_mask(P)

    def capsule(self, p0, p1, r0, r1=None):
        """a limb: segment p0-p1 with radius r0 -> r1 (round ends)"""
        r1 = r0 if r1 is None else r1
        a, b = self.P([p0])[0], self.P([p1])[0]
        r0, r1 = r0 * self.k, r1 * self.k
        X, Y = self.XX, self.YY
        d = b - a
        L2 = float(d @ d) + 1e-6
        t = np.clip(((X - a[0]) * d[0] + (Y - a[1]) * d[1]) / L2, 0, 1)
        dist = np.hypot(X - a[0] - t * d[0], Y - a[1] - t * d[1])
        r = r0 + (r1 - r0) * t
        return np.clip(r - dist + 0.5, 0, 1).astype(np.float32)

    def ellipse(self, c, rx, ry=None, rot=0.0):
        ry = rx if ry is None else ry
        cx, cy = self.P([c])[0]
        rx, ry = rx * self.k, ry * self.k
        a = np.radians(rot)
        dx, dy = self.XX - cx, self.YY - cy
        u = dx * np.cos(a) - dy * np.sin(a)
        v = dx * np.sin(a) + dy * np.cos(a)
        q = np.hypot(u / rx, v / ry)
        return np.clip((1 - q) * min(rx, ry) + 0.5, 0, 1).astype(np.float32)

    def ring(self, c, r_out, r_in):
        return np.clip(self.ellipse(c, r_out) - self.ellipse(c, r_in), 0, 1)

    def stroke(self, pts, w0, w1=None, smooth=True, per=8):
        """a tapered band along a path (scarf tail, tail string, a spar): width w0 -> w1"""
        w1 = w0 if w1 is None else w1
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, per)
        out = np.zeros((self.h, self.w), np.float32)
        n = len(P)
        for i in range(n - 1):
            t0, t1 = i / max(n - 1, 1), (i + 1) / max(n - 1, 1)
            np.maximum(out, self.capsule(P[i], P[i + 1], (w0 + (w1 - w0) * t0) / 2, (w0 + (w1 - w0) * t1) / 2), out=out)
        return out

    def text(self, s, x, y, size, font='stencil', anchor='ls', spacing=0.0, bridge=3.5, rot=0.0):
        """stencil lettering: the counters of every letter are held by bridges at the top and bottom (or the
        shortest side, for awkward shapes). x, y, size in design units."""
        f = stencil_font(font, size * self.k)
        (px, py), = self.P([(x, y)])
        im = Image.new('L', (self.w, self.h), 0)
        d = ImageDraw.Draw(im)
        if spacing:
            adv = [f.getlength(ch) + spacing * self.k for ch in s]
            tot = sum(adv) - spacing * self.k
            cx = px - tot * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
            for ch, a in zip(s, adv):
                d.text((cx, py), ch, font=f, fill=255, anchor='l' + anchor[1]); cx += a
        else:
            d.text((px, py), s, font=f, fill=255, anchor=anchor)
        if rot: im = im.rotate(rot, resample=Image.BICUBIC, center=(px, py))
        m = np.asarray(im, np.float32) / 255
        if bridge:
            m = self._bridge_mask(m, bridge * self.k, prefer='v')
        return m

    # ------------------------------------------------------------ cutting
    def cut(self, mask):
        np.maximum(self.open, np.clip(mask, 0, 1), out=self.open)
        return self

    def keep(self, mask):
        """leave card here (a deliberate bridge or a detail that stays unpainted)"""
        self.open *= 1 - np.clip(mask, 0, 1)
        return self

    def bridge(self, p0, p1, width=3.5):
        """a hand-placed bridge from p0 to p1 (design units)"""
        return self.keep(self.capsule(p0, p1, width / 2))

    def bridges(self, width=3.5, min_area=12, two_over=1600, prefer=None):
        """find every island of card the cuts have isolated and hold each with the shortest bridge (two bridges,
        on roughly opposite sides, for big islands)"""
        self.open = self._bridge_mask(self.open, width * self.k, min_area, two_over * self.k ** 2, prefer)
        return self

    def islands(self):
        """number of loose pieces of card left (0 means the stencil holds together)"""
        card = self.open < 0.5
        outer = np.zeros_like(card); outer[0, :] = outer[-1, :] = outer[:, 0] = outer[:, -1] = True
        return int(((card & ~_geo_fill(outer, card)).sum()))

    def _bridge_mask(self, m, width, min_area=12, two_over=1600, prefer=None):
        for _round in range(4):
            card = m < 0.5
            h, w = card.shape
            outer = np.zeros_like(card); outer[0, :] = outer[-1, :] = outer[:, 0] = outer[:, -1] = True
            reached = _geo_fill(outer, card)
            isl = card & ~reached
            if not isl.any(): break
            todo = isl.copy()
            cuts = []
            while todo.any():
                ys, xs = np.nonzero(todo)
                seed = np.zeros_like(todo); seed[ys[0], xs[0]] = True
                comp = _geo_fill(seed, todo)
                todo &= ~comp
                area = int(comp.sum())
                if area < min_area:
                    m = np.where(comp, 1.0, m).astype(np.float32)      # a crumb: it just falls out
                    continue
                cy, cx = np.nonzero(comp)
                mx, my = cx.mean(), cy.mean()
                k = np.argmin((cx - mx) ** 2 + (cy - my) ** 2)
                sx, sy = float(cx[k]), float(cy[k])
                cands = []
                angs = np.radians(np.arange(0, 360, 7.5))
                for a in angs:
                    dx, dy = np.cos(a), np.sin(a)
                    x, y, t = sx, sy, 0.0
                    start = None; ok = False
                    while True:
                        t += 0.75
                        x, y = sx + dx * t, sy + dy * t
                        ix, iy = int(round(x)), int(round(y))
                        if ix < 0 or iy < 0 or ix >= w or iy >= h: break
                        if comp[iy, ix]:
                            start = None; continue
                        if start is None: start = (x, y, t)
                        if card[iy, ix] and not comp[iy, ix]:
                            ok = reached[iy, ix] or isl[iy, ix]
                            end = (x, y)
                            break
                    if ok and start is not None:
                        L = t - start[2]
                        if prefer == 'v': L *= 1.0 + 1.6 * abs(dx)          # stencil type: vertical bridges
                        if prefer == 'h': L *= 1.0 + 1.6 * abs(dy)
                        cands.append((L, a, start[:2], end, reached[iy, ix]))
                if not cands: continue
                cands.sort(key=lambda c: (not c[4], c[0]))
                best = cands[0]
                cuts.append(best)
                if area > two_over or prefer == 'v':
                    opp = [c for c in cands if abs(((c[1] - best[1] + np.pi) % (2 * np.pi)) - np.pi) > np.radians(120)]
                    if opp: cuts.append(opp[0])
            for L, a, (x0, y0), (x1, y1), _ in cuts:
                dx, dy = np.cos(a), np.sin(a)
                p0 = (x0 - dx * 1.5, y0 - dy * 1.5); p1 = (x1 + dx * 1.5, y1 + dy * 1.5)
                d = np.array(p1) - np.array(p0)
                L2 = float(d @ d) + 1e-6
                tt = np.clip(((self.XX - p0[0]) * d[0] + (self.YY - p0[1]) * d[1]) / L2, 0, 1)
                dist = np.hypot(self.XX - p0[0] - tt * d[0], self.YY - p0[1] - tt * d[1])
                m = m * (1 - np.clip(width / 2 - dist + 0.5, 0, 1))
        return m.astype(np.float32)


def stencil_font(style, size):
    """heavy display faces for stencil lettering: stencil (DIN Condensed Bold / Impact), slab (Rockwell Bold),
    block (Futura Bold / Arial Black). Override with $INKPAINT_FONT_STENCIL etc."""
    env = os.environ.get('INKPAINT_FONT_' + style.upper())
    cands = {'stencil': [('/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf', 0),
                         ('/System/Library/Fonts/Supplemental/Impact.ttf', 0)],
             'slab': [('/System/Library/Fonts/Supplemental/Rockwell.ttc', 1)],
             'block': [('/System/Library/Fonts/Supplemental/Arial Black.ttf', 0),
                       ('/System/Library/Fonts/Supplemental/Futura.ttc', 2)]}.get(style, [])
    if env and os.path.exists(env): cands = [(env, 0)] + cands
    for p, i in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, int(round(size)), index=i)
            except OSError:
                pass
    hit = latin_font('condensed') or latin_font('sans_bold')
    return ImageFont.truetype(hit[0], int(round(size)), index=hit[1]) if hit else ImageFont.load_default(int(size))


# ====================================================================== the wall and the can
class Stencil:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.58, -0.62, 0.53)):
        self.W, self.H = W, H
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        l = np.array(light, np.float32); self.light = l / np.linalg.norm(l)
        self.alb = np.ones((H, W, 3), np.float32) * _c(CONCRETE)
        self.hgt = np.zeros((H, W), np.float32)
        self.gloss = np.zeros((H, W), np.float32)
        self.pit = np.zeros((H, W), np.float32)          # how deep a pit is: paint does not reach its bottom
        self.ground_y = H
        self.gmask = np.zeros((H, W), np.float32)        # 1 = pavement (lit from above, not part of the wall)
        self.stages = []
        g = self.rng.random((H, W)).astype(np.float32)
        c = blur(g, 0.9)
        u = 0.55 * (g - 0.5) / 0.2887 + 0.45 * (c - c.mean()) / (c.std() + 1e-6)
        order = np.argsort(u, axis=None)
        U = np.empty(H * W, np.float32); U[order] = (np.arange(H * W, dtype=np.float32) + 0.5) / (H * W)
        self.U = U.reshape(H, W)                         # droplet thresholds (uniform, slightly clumped)
        del g, c, u, order, U

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ the wall
    def wall(self, colour=CONCRETE, planks=(86, 118), ties=(380, None), ground=1000, damp=110, crack=True):
        """board-marked concrete: plank bands, wood grain imprint, board joints, paste fins, tie holes, bug
        holes, aggregate, weather. ties: (horizontal spacing, list of rows or None for every third seam)"""
        H, W, r = self.H, self.W, self.rng
        self.ground_y = ground
        base = _c(colour)
        Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
        hgt = np.zeros((H, W), np.float32)
        tone = np.ones((H, W), np.float32)
        # --- planks
        seams = []
        y = -r.uniform(0, planks[0])
        while y < ground:
            seams.append(y); y += r.uniform(*planks)
        seams.append(y)
        warp = (_aniso(H, W, 260, 26, 3, self._seed()) - 0.5)
        fine = (_aniso(H, W, 90, 2.2, 2, self._seed()) - 0.5)
        gshow = noise2d(H, W, 150, 3, self._seed())
        for i in range(len(seams) - 1):
            a, b = seams[i], seams[i + 1]
            ya, yb = max(0, int(np.floor(a))), min(H, int(np.ceil(b)) + 1)
            if yb <= ya: continue
            sl = slice(ya, yb)
            yy, xx = Y[sl], X[sl]
            inband = ((yy >= a) & (yy < b)).astype(np.float32)
            # boards of random length inside the band
            ends = [0.0]
            while ends[-1] < W: ends.append(ends[-1] + r.uniform(380, 1250))
            ends[0] = -r.uniform(0, 600)
            seg = np.searchsorted(np.array(ends[1:]), xx[0], side='right')
            nseg = len(ends)
            ph = r.uniform(0, 50, nseg + 1)[seg][None, :]
            per = r.uniform(4.2, 7.5, nseg + 1)[seg][None, :]
            amp = r.uniform(5, 14, nseg + 1)[seg][None, :]
            tn = r.normal(0, 0.035, nseg + 1)[seg][None, :]
            st = r.normal(0, 0.28, nseg + 1)[seg][None, :]
            disp = warp[sl] * amp * 2 + (yy - a) * r.uniform(-0.02, 0.02)
            # knots: grain flows round them
            knot = np.zeros_like(yy)
            for _ in range(r.integers(0, 3)):
                kx, ky = r.uniform(0, W), r.uniform(a + 15, b - 15)
                rx, ry = r.uniform(18, 40), r.uniform(7, 14)
                q = ((xx - kx) / rx) ** 2 + ((yy - ky) / ry) ** 2
                disp = disp + np.sign(yy - ky) * 9 * np.exp(-q * 0.8)
                knot = np.maximum(knot, np.exp(-q * 3.0))
            g = np.sin(2 * np.pi * (yy - a + disp + ph) / per)
            show = smoothstep(0.3, 0.8, gshow[sl])                       # grain pressed in here, smooth there
            grain = (0.11 * smoothstep(0.1, 0.9, g) * show + 0.07 * fine[sl] * 2)
            hgt[sl] += inband * (grain + st - 0.35 * knot)
            tone[sl] *= 1 + inband * (tn - 0.05 * knot - 0.025 * smoothstep(0.5, 1.0, g) * show)
            # board ends: a hairline joint with a little lip
            for ex in ends[1:-1]:
                if ex < 0 or ex > W: continue
                wob = ex + 0.8 * fbm1d(yb - ya, 40, 2, self._seed())[:, None]
                dj = np.abs(xx - wob)
                hgt[sl] -= inband * 0.3 * np.exp(-(dj / 0.9) ** 2)
                tone[sl] *= 1 - inband * 0.03 * np.exp(-(dj / 1.4) ** 2)
        # paste fins along every seam (broken here and there) and a slight tone step
        for sy in seams[1:-1]:
            ya, yb = max(0, int(sy) - 6), min(H, int(sy) + 7)
            if yb <= ya: continue
            sl = slice(ya, yb)
            wob = sy + 0.9 * fbm1d(W, 160, 3, self._seed())[None, :]
            d = Y[sl] - wob
            gate = smoothstep(0.25, 0.55, noise2d(1, W, 40, 2, self._seed())[0])[None, :]
            th = 1.2 + 1.4 * noise2d(1, W, 18, 2, self._seed())[0][None, :]
            hgt[sl] += gate * 1.15 * np.exp(-(d / th) ** 2) - (1 - gate) * 0.5 * np.exp(-(d / 1.0) ** 2)
            tone[sl] *= 1 - 0.06 * np.exp(-(d / 1.6) ** 2) * (1 - gate) + 0.03 * gate * np.exp(-(d / th) ** 2)
        # --- aggregate and cement tone
        cloud = noise2d(H, W, 260, 4, self._seed())
        tone *= 1 + 0.085 * (cloud - 0.5)
        mott = noise2d(H, W, 38, 3, self._seed())
        tone *= 1 + 0.07 * (mott - 0.5) - 0.05 * smoothstep(0.62, 0.8, mott)
        lait = smoothstep(0.68, 0.9, noise2d(H, W, 90, 3, self._seed()))
        tone *= 1 + 0.06 * lait
        sand = self.rng.random((H, W)).astype(np.float32)
        tone *= 1 + 0.045 * (sand - 0.5)
        hgt += 0.18 * (sand - 0.5) + 0.25 * (blur(sand, 1.2) - 0.5)
        specks = sand > 0.996
        tone[specks] *= 0.8
        tone[(sand < 0.003)] *= 1.12
        # --- bug holes (air pits), more of them near the top of each lift of planks
        pit = np.zeros((H, W), np.float32)
        pitd = np.zeros((H, W), np.float32)
        n = int(W * ground / 1800)
        cl = noise2d(H // 8 + 1, W // 8 + 1, 18, 2, self._seed())
        for _ in range(n):
            x, y = r.uniform(0, W), r.uniform(0, ground - 4)
            if cl[int(y) // 8, int(x) // 8] < r.uniform(0.25, 0.95): continue
            rad = r.choice([0.7, 1.0, 1.4, 2.0, 2.8], p=[0.32, 0.3, 0.2, 0.12, 0.06])
            _disc_splat(pitd, x, y, rad, 1.0, 'max')
        hgt -= 2.6 * pitd
        pit = np.maximum(pit, pitd)
        tone *= 1 - 0.25 * pitd
        # --- form-tie holes
        sx = ties[0]
        rows = ties[1]
        if rows is None:
            cent = [(seams[i] + seams[i + 1]) / 2 for i in range(len(seams) - 1)]
            rows = [cy for j, cy in enumerate(cent) if j % 3 == 1 and 30 < cy < ground - 60]
        self.tie_holes = []
        rust = np.zeros((H, W), np.float32)
        x_off = r.uniform(0.3, 0.7) * sx
        for ri, cy in enumerate(rows):
            xs = np.arange(x_off - sx * 2, W + sx, sx)
            for cx in xs:
                cx2, cy2 = cx + r.normal(0, 1.5), cy + r.normal(0, 1.0)
                if cx2 < -20 or cx2 > W + 20: continue
                kind = r.choice(['rod', 'plug', 'open'], p=[0.5, 0.3, 0.2])
                self.tie_holes.append((cx2, cy2, kind))
                R = 12.5
                ya, yb = max(0, int(cy2 - R - 3)), min(H, int(cy2 + R + 4))
                xa, xb = max(0, int(cx2 - R - 3)), min(W, int(cx2 + R + 4))
                if yb <= ya or xb <= xa: continue
                yy, xx = Y[ya:yb, xa:xb], X[ya:yb, xa:xb]
                d = np.hypot(xx - cx2, yy - cy2)
                cone = np.clip(1 - d / R, 0, 1)
                lip = np.exp(-((d - R) / 1.4) ** 2) * 0.5
                depth = 7.0 if kind != 'plug' else 2.2
                hgt[ya:yb, xa:xb] += -depth * np.clip(cone * 1.6, 0, 1) ** 0.8 + lip
                pit[ya:yb, xa:xb] = np.maximum(pit[ya:yb, xa:xb], np.clip(cone * 1.4, 0, 1) * (0.8 if kind != 'plug' else 0.2))
                core = np.clip(4.6 - d, 0, 1)
                if kind == 'rod':
                    tone[ya:yb, xa:xb] *= 1 - 0.5 * core - 0.12 * cone
                    rust[ya:yb, xa:xb] = np.maximum(rust[ya:yb, xa:xb], core * 0.9)
                elif kind == 'plug':
                    tone[ya:yb, xa:xb] *= 1 + 0.06 * np.clip(9.5 - d, 0, 1) - 0.08 * np.exp(-((d - 9.5) / 1.2) ** 2)
                else:
                    tone[ya:yb, xa:xb] *= 1 - 0.35 * np.clip(7 - d, 0, 1) - 0.1 * cone
        # --- weather: rain streaks from ties and seams, rust stains, the damp splash zone
        streak = np.zeros((H, W), np.float32)
        for cx, cy, kind in self.tie_holes:
            if r.random() < 0.75:
                L = r.uniform(70, 330); wd = r.uniform(5, 15)
                self._streak(streak, cx + r.normal(0, 2), cy + 6, L, wd, r.uniform(0.5, 1.0))
            if kind == 'rod' and r.random() < 0.7:
                self._streak(rust, cx + r.normal(0, 1), cy + 3, r.uniform(40, 190), r.uniform(2.5, 5.5), r.uniform(0.5, 0.9))
        for _ in range(int(W / 70)):
            cx, cy = r.uniform(0, W), r.choice(seams[1:-1])
            self._streak(streak, cx, cy + 2, r.uniform(40, 260), r.uniform(10, 40), r.uniform(0.25, 0.7))
        for _ in range(5):                                       # long runs from the coping above the frame
            self._streak(streak, r.uniform(0, W), 0, r.uniform(0.35, 0.8) * ground, r.uniform(25, 70), r.uniform(0.3, 0.6))
        streak = np.clip(streak, 0, 1.3)
        rust = np.clip(rust, 0, 1)
        dirt = 1 - 0.26 * streak[..., None] * np.array([1.0, 0.98, 0.93], np.float32)
        rust_c = np.array([0.62, 0.36, 0.2], np.float32)
        # damp splash zone above the pavement: a wavy tide line, algae, efflorescence crust
        tide = ground - damp + 26 * (fbm1d(W, 300, 4, self._seed()) )[None, :] + 10 * fbm1d(W, 40, 2, self._seed())[None, :]
        zone = smoothstep(-6, 18, Y - tide)
        deep = smoothstep(0, ground - (ground - damp * 0.4), Y - (ground - damp * 0.4)) * (Y <= ground)
        alg = noise2d(H, W, 22, 4, self._seed())
        damp_m = (zone * (0.55 + 0.45 * deep) * (0.8 + 0.4 * noise2d(H, W, 50, 3, self._seed())))[..., None]
        crust = noise2d(H, W, 7, 3, self._seed())
        efflo = np.exp(-((Y - tide + 2) / 4.0) ** 2) * smoothstep(0.45, 0.8, crust) * 0.5 * smoothstep(0.3, 0.6, alg)
        efflo += zone * smoothstep(0.78, 0.92, noise2d(H // 2 + 1, W // 2 + 1, 6, 2, self._seed())[
            (np.arange(H) // 2)[:, None], (np.arange(W) // 2)[None, :]]) * 0.25
        # --- assemble
        alb = base[None, None, :] * tone[..., None] * dirt
        alb = alb * (1 - rust[..., None] * 0.55) + rust[..., None] * 0.55 * rust_c * alb.mean(-1, keepdims=True) * 1.6
        green = np.array([0.80, 0.86, 0.74], np.float32)
        alb = alb * (1 - damp_m * 0.30) * (1 - damp_m * smoothstep(0.6, 0.85, alg)[..., None] * deep[..., None] * (1 - green))
        alb = alb + (np.array([0.93, 0.92, 0.88], np.float32) - alb) * np.clip(efflo, 0, 0.8)[..., None]
        # dust: the whole wall a little lighter and flatter toward the top, dirtier toward the ground
        alb *= (1.02 - 0.06 * smoothstep(0, ground, Y))[..., None]
        if crack: self._crack(hgt, alb, self.tie_holes)
        self.alb = alb.astype(np.float32)
        self.hgt = hgt.astype(np.float32)
        self.pit = np.clip(pit, 0, 1).astype(np.float32)

    def _streak(self, arr, x, y, L, wd, s):
        """a soft vertical run of grime starting at (x, y), widening and fading as it goes down"""
        H, W = arr.shape
        ya, yb = max(0, int(y)), min(H, int(y + L))
        xa, xb = max(0, int(x - wd * 2.5 - 6)), min(W, int(x + wd * 2.5 + 7))
        if yb <= ya or xb <= xa: return
        yy = np.arange(ya, yb, dtype=np.float32)[:, None]
        xx = np.arange(xa, xb, dtype=np.float32)[None, :]
        t = (yy - y) / L
        wob = 3 * fbm1d(yb - ya, 60, 3, int(x * 7 + y) % 99991)[:, None]
        width = wd * (0.45 + 0.8 * np.sqrt(np.clip(t, 0, 1)))
        prof = np.exp(-((xx - x - wob) / width) ** 2)
        fade = np.clip(t * 12, 0, 1) * (1 - t) ** 1.4
        tex = 0.7 + 0.3 * np.cos(xx * 1.7 + wob * 2.1) * np.cos(yy * 0.05)
        arr[ya:yb, xa:xb] += s * prof * fade * tex

    def _crack(self, hgt, alb, ties):
        """a hairline crack wandering down from one tie hole"""
        r = self.rng
        if not ties: return
        cx, cy, _ = ties[int(r.integers(len(ties)))]
        for branch in range(2):
            x, y = cx + r.normal(0, 3), cy + 10
            a = np.radians(r.uniform(60, 110) if branch == 0 else r.uniform(20, 60))
            pts = [(x, y)]
            for i in range(int(r.uniform(40, 80) if branch == 0 else r.uniform(15, 30))):
                a += r.normal(0, 0.35)
                a = np.clip(a, np.radians(15), np.radians(165))
                step = r.uniform(2, 5)
                x += np.cos(a) * step; y += np.sin(a) * step
                pts.append((x, y))
            for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
                for t in np.linspace(0, 1, 6):
                    _disc_splat(hgt, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 0.6, -0.5, 'add')
            im = Image.new('L', (self.W, self.H), 0)
            ImageDraw.Draw(im).line(pts, fill=255, width=1)
            m = np.asarray(im, np.float32) / 255
            m = np.clip(m * 0.5 + blur(m, 1.4) * 0.5, 0, 1)
            alb *= (1 - 0.32 * m)[..., None]
            cx, cy = pts[len(pts) // 3]

    def pavement(self, colour='#6f6c68', joint=True):
        """the strip of pavement under the wall: asphalt seen at a glance, lit from above, with dust and grit
        along the foot of the wall"""
        H, W, r = self.H, self.W, self.rng
        g0 = self.ground_y
        if g0 >= H: return
        h = H - g0
        Y, X = np.mgrid[0:h, 0:W].astype(np.float32)
        t = Y / max(h - 1, 1)
        base = _c(colour)
        grit = self.rng.random((h, W)).astype(np.float32)
        agg = _aniso(h, W, 7, 3, 2, self._seed())
        tone = 1 + 0.16 * (agg - 0.5) + 0.10 * (grit - 0.5)
        tone *= 1 + 0.08 * (noise2d(h, W, 140, 3, self._seed()) - 0.5)
        g2 = blur(grit, 0.7)
        g2 = (g2 - g2.mean()) / (g2.std() + 1e-6)
        tone *= 1 + 0.07 * np.clip(g2, -2.5, 2.5)                    # aggregate: pale stones in dark binder
        tone[grit > 0.97] *= 1.22
        tone[grit < 0.04] *= 0.8
        alb = base[None, None, :] * tone[..., None] * (0.9 + 0.12 * t)[..., None]
        # tar-sealed cracks, flattened chewing gum, an oil stain: the life of a pavement
        tar = Image.new('L', (W, h), 0)
        dd = ImageDraw.Draw(tar)
        for _ in range(3):
            x = r.uniform(0, W); y = r.uniform(h * 0.3, h)
            pts = [(x, y)]
            for _ in range(14):
                x += r.uniform(15, 40); y += r.normal(0, 4) * 0.6
                pts.append((x, min(max(y, 6), h - 1)))
            dd.line(pts, fill=255, width=int(r.integers(7, 12)), joint='curve')
        tm = blur(np.asarray(tar, np.float32) / 255, 1.5) * (0.7 + 0.3 * noise2d(h, W, 20, 2, self._seed()))
        alb = alb * (1 - 0.32 * tm[..., None])
        for _ in range(int(W / 70)):
            gx, gy = r.uniform(0, W), r.uniform(8, h - 3)
            rr = r.uniform(2.0, 4.2)
            gum = np.zeros((h, W), np.float32)
            _disc_splat(gum, gx, gy, rr, 1.0, 'max')
            gum = np.clip(gum * 2.5, 0, 1)
            alb = alb * (1 - 0.6 * gum[..., None]) + 0.6 * gum[..., None] * np.array([0.27, 0.27, 0.28], np.float32)
        oil = smoothstep(0.62, 0.8, noise2d(h, W, 60, 3, self._seed())) * smoothstep(0.5, 0.8, noise2d(h, W, 300, 2, self._seed()))
        alb = alb * (1 - 0.25 * oil[..., None])
        # a band of dust and grit swept against the wall
        dust = np.exp(-Y / 10.0) * (0.6 + 0.4 * noise2d(h, W, 30, 2, self._seed()))
        alb = alb * (1 - 0.35 * dust[..., None]) + 0.35 * dust[..., None] * np.array([0.62, 0.58, 0.52], np.float32)
        # a dark crack line where the wall meets the ground
        alb[:3] *= np.array([0.45, 0.55, 0.75], np.float32)[:, None, None]
        self.alb[g0:] = alb
        self.hgt[g0:] = 0.0
        self.gmask[g0:] = 1.0
        self.pit[g0:] = 0.0
        self._weeds()

    def _weeds(self):
        """a few tufts of grass in the joint at the foot of the wall"""
        r = self.rng
        im = Image.new('L', (self.W * 2, (self.H - self.ground_y + 80) * 2), 0)
        d = ImageDraw.Draw(im)
        gy = 80
        for _ in range(int(r.integers(3, 6))):
            cx = r.uniform(40, self.W - 40)
            for _ in range(int(r.integers(6, 16))):
                a = np.radians(r.uniform(-150, -30))
                L = r.uniform(12, 46)
                bend = r.normal(0, 0.4)
                pts = []
                for s in np.linspace(0, 1, 7):
                    aa = a + bend * s * s
                    pts.append(((cx + np.cos(aa) * L * s) * 2, (gy + 4 + np.sin(aa) * L * s) * 2))
                for i in range(len(pts) - 1):
                    wdt = int(max(1, (1 - i / 6) * 4))
                    d.line([pts[i], pts[i + 1]], fill=255, width=wdt)
        m = np.asarray(im.reduce(2), np.float32) / 255
        y0 = self.ground_y - 80
        y0c = max(0, y0)
        m = m[y0c - y0:]
        h = m.shape[0]
        sl = slice(y0c, y0c + h)
        col = np.array([0.33, 0.40, 0.2], np.float32)
        self.alb[sl] = self.alb[sl] * (1 - m[..., None]) + col * (0.8 + 0.4 * self.U[sl, :, None] * 0.5) * m[..., None]
        self.hgt[sl] += m * 2.0

    # ------------------------------------------------------------ painting helpers
    def _deposit(self, sl, film, colour, wash=None, mist_tint=0.22, roll=None):
        """turn a paint film (local array) into droplets on the wall"""
        col = _c(colour)
        hide = HIDE.get(colour, 2.4) if isinstance(colour, str) else 2.4
        m = 1 - np.exp(-hide * np.clip(film, 0, None))
        if roll is None: roll = (int(self.rng.integers(self.H)), int(self.rng.integers(self.W)))
        U = np.roll(self.U, roll, (0, 1))[sl]
        dots = smoothstep(-0.03, 0.03, m - U)
        cov = np.clip(dots * (1 - mist_tint) + m * mist_tint, 0, 1)
        cov *= 1 - 0.78 * self.pit[sl] * (1 - smoothstep(1.6, 3.2, film))      # paint misses the bottom of pits
        if wash is not None: cov *= wash
        cov = cov * (1 - self.gmask[sl])
        a = cov[..., None]
        self.alb[sl] = self.alb[sl] * (1 - a) + col * a
        gl = GLOSS.get(colour, 0.35) if isinstance(colour, str) else 0.35
        self.gloss[sl] = self.gloss[sl] * (1 - cov) + gl * cov
        return cov

    def _drip(self, x, y, length, width, colour, seed):
        """one run of paint: a neck where it leaves the edge, a thinning tail, a bead at the end"""
        r = np.random.default_rng(seed)
        ss = 4
        L = float(length)
        pad = int(width * 3 + 6)
        x0, y0 = int(x) - pad, int(y) - 2
        w, h = 2 * pad + 1, int(L + width * 4 + 8)
        if x0 < 0 or x0 + w > self.W or y0 >= self.ground_y - 2: return
        h = min(h, self.ground_y - y0 - 1)
        if h < 4: return
        im = Image.new('L', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        n = int(L * 2) + 2
        t = np.linspace(0, 1, n)
        wob = fbm1d(n, max(4, n / 3), 3, seed) * min(2.2, 0.35 + L / 90) + np.cumsum(r.normal(0, 0.02, n))
        for i in range(n):
            tt = t[i]
            rad = width * (1.0 + 0.9 * np.exp(-tt * L / 4.0)) * (1 - 0.38 * tt) / 2
            cx, cy = x - x0 + wob[i], y - y0 + tt * L
            d.ellipse([(cx - rad) * ss, (cy - rad) * ss, (cx + rad) * ss, (cy + rad) * ss], fill=255)
        rb = width * r.uniform(0.62, 0.85)
        cx, cy = x - x0 + wob[-1], y - y0 + L
        d.ellipse([(cx - rb) * ss, (cy - rb * 1.25) * ss, (cx + rb) * ss, (cy + rb * 1.15) * ss], fill=255)
        m = np.asarray(im.reduce(ss), np.float32) / 255
        sl = (slice(y0, y0 + h), slice(x0, x0 + w))
        a = m[:self.H - y0]
        col = _c(colour)
        self.alb[sl] = self.alb[sl] * (1 - a[..., None]) + col * a[..., None]
        self.gloss[sl] = np.maximum(self.gloss[sl], a * 0.85)
        self.hgt[sl] += blur(a, 1.0) * (0.45 + 0.25 * width / 3)

    def _drips(self, film, open_m, sl, colour, amount, length, wet, seed):
        """paint runs from the lower edges of the openings where the film is too thick"""
        if amount <= 0: return
        r = np.random.default_rng(seed)
        y0, x0 = sl[0].start, sl[1].start
        below = shift(open_m, 0, -3)                         # value 3 px further down
        clear = np.maximum(shift(open_m, 0, -7), shift(open_m, 0, -12))
        edge = (open_m > 0.5) & (below < 0.3) & (clear < 0.3)      # a real lower edge, not just a bridge
        ex = film - wet
        cand = edge & (ex > 0)
        ys, xs = np.nonzero(cand)
        if not len(ys): return
        w = ex[ys, xs]
        nmax = int(round(amount * min(26, 2 + w.sum() / 40)))
        p = w / w.sum()
        taken = []
        for i in r.choice(len(ys), size=min(nmax * 3, len(ys)), replace=False, p=p):
            if len(taken) >= nmax: break
            X, Y = xs[i] + x0, ys[i] + y0
            if any(abs(X - a) < 9 and abs(Y - b) < 40 for a, b in taken): continue
            taken.append((X, Y))
            e = float(ex[ys[i], xs[i]])
            L = np.clip((18 + 120 * e * r.uniform(0.4, 1.4)) * length, 10, 300)
            wd = np.clip(1.5 + 0.9 * np.sqrt(e) + r.normal(0, 0.25), 1.3, 3.6)
            self._drip(X + 0.5, Y, L, wd, colour, int(r.integers(1 << 30)))

    def _lift(self, card, dx, dy):
        """how far the card stands off the wall (0 flat at the tape .. 1 curled), local to the card"""
        h, w = card.h, card.w
        d = np.full((h, w), 1e9, np.float32)
        for tx, ty in card.tape:
            d = np.minimum(d, np.hypot(card.XX - tx, card.YY - ty))
        diag = np.hypot(w, h)
        L = np.clip(d / (0.7 * diag), 0, 1) ** 1.5
        curl = smoothstep(0.55, 0.85, noise2d(h, w, 120, 2, card.seed + 11))     # here and there the card bows out
        return np.clip(0.15 + 0.35 * L + 0.5 * curl, 0, 1).astype(np.float32)

    def _sweeps(self, h, w, box, cone, angle, rng, overshoot=1.2, linger=3):
        """the path of the can: overlapping parallel sweeps over `box`, dwell weights splatted into an array"""
        x0, y0, x1, y1 = box
        a = np.radians(angle)
        ux, uy = np.cos(a), -np.sin(a)
        vx, vy = -uy, ux
        corners = np.array([[x0, y0], [x1, y0], [x0, y1], [x1, y1]], np.float32)
        u = corners @ np.array([ux, uy]); v = corners @ np.array([vx, vy])
        sp = cone * 0.95
        D = np.zeros((h, w), np.float32)
        pts, wts = [], []
        for vi, vv in enumerate(np.arange(v.min() - cone * 0.4, v.max() + cone * 0.6, sp)):
            ua, ub = u.min() - cone * overshoot, u.max() + cone * overshoot
            n = int((ub - ua) / 1.5) + 2
            uu = np.linspace(ua, ub, n)
            speed = 1 + 0.35 * fbm1d(n, max(6, n / 3), 3, int(rng.integers(1 << 30)))
            tt = (uu - ua) / (ub - ua)
            speed *= 0.55 + 0.45 * smoothstep(0.0, 0.08, np.minimum(tt, 1 - tt))     # slows at the reversals
            off = vv + rng.normal(0, cone * 0.12) + np.linspace(0, rng.normal(0, cone * 0.25), n)
            px = uu * ux + off * vx; py = uu * uy + off * vy
            pts.append(np.stack([px, py], 1)); wts.append(1.5 / speed)
        P = np.concatenate(pts); Wt = np.concatenate(wts)
        for _ in range(linger):                           # the hand stops to fill a corner
            k = rng.integers(len(P))
            P = np.vstack([P, P[k] + rng.normal(0, cone * 0.2, (40, 2))]); Wt = np.concatenate([Wt, np.full(40, 1.1)])
        ix, iy = np.floor(P[:, 0]).astype(int), np.floor(P[:, 1]).astype(int)
        fx, fy = P[:, 0] - ix, P[:, 1] - iy
        for ddx, ddy, ww in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            jx, jy = ix + ddx, iy + ddy
            ok = (jx >= 0) & (jy >= 0) & (jx < w) & (jy < h)
            np.add.at(D, (jy[ok], jx[ok]), (Wt * ww)[ok])
        return blur(D, cone)

    # ------------------------------------------------------------ public painting tools
    def card(self, x0, y0, x1, y1, origin=None, scale=1.0, tape=None, material='manila'):
        """a sheet of card covering x0..x1, y0..y1 (wall px). Openings are cut with its shape methods."""
        return Card(self, x0, y0, x1, y1, origin, scale, tape, material, self._seed())

    def spray(self, card, colour, coats=1.8, cone=24, angle=8, misreg=2.2, at=(0, 0), rot=0.0, lift=1.0, mist=1.0,
              drips=1.0, drip_len=1.0, wet=2.4, linger=3, ghost=1.0):
        """spray through `card`: overlapping sweeps (cone = spray radius px), the paint lands through the
        openings with a crisp core, an under-spray fringe where the card lifted, an overspray halo, a ghost of
        the sheet where sweeps overshot it, and drips where the film is too heavy. at: move the card (reuse it
        somewhere else); rot: turn it (degrees, about its origin); misreg: random placement error (px) for
        multi-layer work."""
        r = self.rng
        dx = at[0] + r.normal(0, misreg); dy = at[1] + r.normal(0, misreg)
        idx, idy = int(np.floor(dx)), int(np.floor(dy))
        fx, fy = dx - idx, dy - idy
        pad = int(2.5 * cone + 30)                               # paint also lands round the outside of the card
        opn, sht = card.open, card.sheet
        if rot:
            cx, cy = card.ox - card.x0, card.oy - card.y0
            opn = np.asarray(Image.fromarray(opn).rotate(rot, Image.BILINEAR, center=(cx, cy)), np.float32)
            sht = np.asarray(Image.fromarray(sht).rotate(rot, Image.BILINEAR, center=(cx, cy)), np.float32)
        op = np.pad(opn, pad)
        op = ((1 - fx) * (1 - fy) * op + fx * (1 - fy) * shift(op, 1, 0) + (1 - fx) * fy * shift(op, 0, 1)
              + fx * fy * shift(op, 1, 1))
        sheet = np.pad(sht, pad)
        Lf = np.pad(self._lift(card, dx, dy), pad, mode='edge') * lift
        X0, Y0 = card.x0 + idx - pad, card.y0 + idy - pad
        xa, ya = max(0, X0), max(0, Y0)
        xb, yb = min(self.W, X0 + card.w + 2 * pad), min(self.ground_y, Y0 + card.h + 2 * pad)
        if xb <= xa or yb <= ya: return None
        lsl = (slice(ya - Y0, yb - Y0), slice(xa - X0, xb - X0))
        sl = (slice(ya, yb), slice(xa, xb))
        op, sheet, L = op[lsl], sheet[lsl], Lf[lsl]
        h, w = op.shape
        ys, xs = np.nonzero(op > 0.3)
        if not len(ys): return None
        box = (xs.min(), ys.min(), xs.max(), ys.max())
        D = self._sweeps(h, w, box, cone, angle + r.normal(0, 4), r, linger=linger)
        Dm = np.median(D[op > 0.5]) if (op > 0.5).any() else D.max()
        D = D / (Dm + 1e-6) * coats
        # paint through the openings: crisp core, under-spray fringe where lifted, halo of drifting mist
        s1, s2 = blur(op, 0.5), blur(op, 1.8)
        soft = s1 * (1 - L) + s2 * L
        open_eff = np.maximum(op, soft * (0.2 + 0.5 * L))
        halo = (blur(op, 7) * 0.022 + blur(op, 24) * 0.012) * mist * (0.5 + L)
        film = D * np.clip(open_eff + halo, 0, 1.2) * sheet
        film += D * (1 - sheet) * 0.0035 * ghost                 # sweeps that ran past the edge of the card
        self._deposit(sl, film, colour)
        if drips > 0:
            self._drips(film, op, sl, colour, drips, drip_len, wet, self._seed())
        card.last = dict(sl=sl, lsl=lsl, D=D, colour=colour, offset=(idx, idy), L=L, pad=pad, op=op, sheet=sheet)
        return card

    def freehand(self, pts, colour, width=4.0, coats=2.0, smooth=True, per=10, speed=None, spits=4, drips=0.6,
                 mist=1.0, wash=None, wet=2.5, drip_len=1.0):
        """the can without a stencil (a skinny cap): a soft line along pts whose weight follows the hand's speed.
        speed: optional per-control-point speed factors (slow = heavier). wash: 0..1 how much a pressure washer
        took off afterwards."""
        r = self.rng
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, per)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        Ls = np.concatenate([[0], np.cumsum(seg)])
        n = int(Ls[-1] / 0.8) + 2
        s = np.linspace(0, Ls[-1], n)
        x = np.interp(s, Ls, P[:, 0]); y = np.interp(s, Ls, P[:, 1])
        if speed is not None:
            sp = np.interp(s / Ls[-1], np.linspace(0, 1, len(speed)), speed)
        else:
            sp = np.ones(n)
        sp = sp * (1 + 0.25 * fbm1d(n, max(8, n / 6), 3, self._seed()))
        tt = s / max(Ls[-1], 1)
        sp = sp * (0.45 + 0.55 * smoothstep(0, 0.04, tt))          # starting slow: the heavy blob at the start
        pad = int(width * 6 + 40)
        xa, xb = max(0, int(x.min()) - pad), min(self.W, int(x.max()) + pad)
        ya, yb = max(0, int(y.min()) - pad), min(self.ground_y, int(y.max()) + pad)
        if xb <= xa or yb <= ya: return
        h, w = yb - ya, xb - xa
        D = np.zeros((h, w), np.float32)
        ix = np.clip(np.round(x - xa).astype(int), 0, w - 1); iy = np.clip(np.round(y - ya).astype(int), 0, h - 1)
        np.add.at(D, (iy, ix), 0.8 / sp)
        sig = width / 2.6
        core = blur(D, sig) * (sig * 2.5066)                       # = 1 along a steady line
        film = core * coats + blur(D, sig * 5) * (sig * 12.5) * 0.06 * mist * coats
        sl = (slice(ya, yb), slice(xa, xb))
        wm = None
        if wash is not None and wash > 0:
            st = _aniso(h, w, 24, 260, 3, self._seed())
            wm = np.clip(1 - wash * smoothstep(0.25, 0.75, st + 0.3 * (self.rng.random((h, w)) - 0.5)), 0, 1)
        self._deposit(sl, film, colour, wash=wm)
        # cap spits: a few fat droplets near the line
        for _ in range(int(spits)):
            k = int(r.integers(n))
            if wm is not None: break
            rr = r.uniform(1.0, 2.6) * width / 4
            ox, oy = r.normal(0, width * 2.2, 2)
            buf = np.zeros((h, w), np.float32)
            _disc_splat(buf, x[k] - xa + ox, y[k] - ya + oy, rr, 1.0, 'max')
            self._deposit(sl, buf * 4, colour)
        # drips where the hand paused
        if drips > 0 and wm is None:
            heavy = np.argsort(sp)[: max(1, n // 40)]
            cnt = 0
            for k in heavy:
                if r.random() > drips * 0.5 or cnt > 3 * drips: continue
                cnt += 1
                self._drip(x[k], y[k] + width * 0.4, r.uniform(25, 110) * drip_len, width * r.uniform(0.45, 0.7),
                           colour, self._seed())

    def buff(self, x0, y0, x1, y1, colour='#8f8e8a', roller=64, ragged=26):
        """a council roller patch over old graffiti: not-quite-matching grey laid on in vertical roller passes.
        Each pass starts and stops at its own height, so the top and bottom edges are stepped; the ends of a pass
        go dry and streaky; neighbouring passes overlap in slightly darker laps; the nap leaves a fine stipple.
        Whatever was there before still ghosts through the thin places."""
        r = self.rng
        xa, xb = max(0, int(x0) - 20), min(self.W, int(x1) + 20)
        ya, yb = max(0, int(y0) - ragged - 30), min(self.ground_y, int(y1) + ragged + 30)
        h, w = yb - ya, xb - xa
        yy = np.arange(h, dtype=np.float32)[:, None] + ya
        xx = np.arange(w, dtype=np.float32)[None, :] + xa
        streak = _aniso(h, w, 2.5, 50, 3, self._seed())
        nap = noise2d(h, w, 3, 2, self._seed())
        cover = np.zeros((h, w), np.float32)
        laps = np.zeros((h, w), np.float32)
        x = float(x0)
        while x < x1 - roller * 0.3:
            wd = roller * r.uniform(0.92, 1.05)
            top = y0 + r.uniform(-ragged, ragged * 0.6); bot = y1 + r.uniform(-ragged * 0.6, ragged)
            sx = x + r.normal(0, 3)
            tilt = r.normal(0, 0.012)
            cx = sx + (yy - y0) * tilt
            across = np.clip(np.minimum(xx - cx, cx + wd - xx) + 0.5, 0, 1)
            dry = 14.0                                                  # the ends of a pass run dry
            along = smoothstep(0, 1, (np.minimum(yy - top, bot - yy) + streak * dry) / dry)
            p = across * along
            laps += p
            cover = np.maximum(cover, p)
            x += wd * r.uniform(0.82, 0.92)                              # passes overlap a little
        laps = np.clip(laps - 1, 0, 1)
        cover = np.clip(cover * (0.82 + 0.12 * nap) + 0.06 * laps, 0, 1)
        sl = (slice(ya, yb), slice(xa, xb))
        col = _c(colour) * (1 + 0.03 * (noise2d(h, w, 90, 3, self._seed()) - 0.5))[..., None] * (1 - 0.05 * laps[..., None])
        self.alb[sl] = self.alb[sl] * (1 - cover[..., None]) + col * cover[..., None]
        self.gloss[sl] *= 1 - cover * 0.8
        self.pit[sl] *= 1 - 0.6 * cover                       # roller paint fills the small pits

    # ------------------------------------------------------------ the card on the wall (for snapshots)
    def _card_overlay(self, img, card):
        """the stencil still taped up: the card (its own colour, caked with this and older overspray), masking
        tape, and the shadow the lifted card throws on the wall and into its openings"""
        if not hasattr(card, 'last'): return img
        lt = card.last
        sl, lsl = lt['sl'], lt['lsl']
        idx, idy = lt['offset']
        op, sheet = lt['op'], lt['sheet']
        solid = np.clip(sheet - op, 0, 1)
        h, w = solid.shape
        base = _c('#d9c69a') if card.material == 'manila' else _c('#b9b4aa')
        fib = noise2d(h, w, 3, 2, card.seed + 5)
        old = smoothstep(0.55, 0.85, noise2d(h, w, 70, 3, card.seed + 6)) * 0.55
        cardc = base[None, None, :] * (0.94 + 0.08 * fib[..., None])
        cardc = cardc * (1 - old[..., None]) + _c('#2b2b2b') * old[..., None] * 0.9 + cardc * old[..., None] * 0.1
        paint = 0.82 * (1 - np.exp(-0.55 * lt['D'])) * (0.85 + 0.3 * fib)      # dusty: the card shows through
        cardc = cardc * (1 - paint[..., None]) + _c(lt['colour']) * paint[..., None]
        # the cut edges: the card's thickness catches the light on the lit side of every opening
        bs = blur(solid, 0.8)
        lit = np.clip(bs - shift(bs, -2, -2), 0, 1)
        dark = np.clip(bs - shift(bs, 2, 2), 0, 1)
        cardc = cardc + (0.42 * lit)[..., None] - (0.25 * dark * cardc.mean(-1))[..., None]
        out = img[sl].copy()
        sh = np.clip(shift(solid, 4, 5) - solid, 0, 1)
        sh = blur(sh, 2.5) * 0.45 * (1 - solid)
        out *= (1 - sh)[..., None]
        out = out * (1 - solid[..., None]) + cardc * solid[..., None]
        img = img.copy(); img[sl] = out
        # masking tape across the corners
        for tx, ty in card.tape:
            gx, gy = card.x0 + idx + tx, card.y0 + idy + ty
            a = np.radians(self.rng.uniform(-35, 35) + (45 if (tx in (0, card.w)) and (ty in (0, card.h)) else 0))
            Lt, Wt = 70, 26
            corners = [(-Lt / 2, -Wt / 2), (Lt / 2, -Wt / 2), (Lt / 2, Wt / 2), (-Lt / 2, Wt / 2)]
            pts = [(gx + u * np.cos(a) - v * np.sin(a), gy + u * np.sin(a) + v * np.cos(a)) for u, v in corners]
            im = Image.new('L', (self.W, self.H), 0)
            ImageDraw.Draw(im).polygon(pts, fill=255)
            m = blur(np.asarray(im, np.float32) / 255, 0.7)
            ys, xs = np.nonzero(m > 0.01)
            if not len(ys): continue
            ts = (slice(ys.min(), ys.max() + 1), slice(xs.min(), xs.max() + 1))
            mt = m[ts][..., None]
            tc = _c('#e4d6ad') * (0.95 + 0.05 * self.U[ts][..., None])
            img[ts] = img[ts] * (1 - 0.88 * mt) + tc * 0.88 * mt
        return img

    # ------------------------------------------------------------ output
    def composite(self):
        n = height_normals(self.hgt)
        l = self.light
        ndl = n[..., 0] * l[0] + n[..., 1] * l[1] + n[..., 2] * l[2]
        rel = ndl / l[2]
        shade = 1 + 0.9 * (rel - 1)
        sh = height_shadow(self.hgt, tuple(l), reach=26, step=1.5, soft=1.2)
        shade *= 1 - 0.38 * sh
        cav = np.clip((blur(self.hgt, 3) - self.hgt) / 4.0, 0, 1)
        shade *= 1 - 0.35 * cav
        sheen = self.gloss * np.clip(rel - 1, 0, 1) * 0.9 + self.gloss * 0.015
        g = self.gmask
        shade = shade * (1 - g) + g * 1.08
        img = self.alb * shade[..., None] + sheen[..., None]
        H, W = self.H, self.W
        Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
        day = 1.05 - 0.10 * (X / W * 0.6 + Y / H * 0.4)
        vig = 1 - 0.16 * (((X - W / 2) / (W / 2)) ** 2 + ((Y - H / 2) / (H / 2)) ** 2) ** 1.5 * 0.5
        img = img * (day * vig)[..., None]
        img = img * np.array([1.0, 0.995, 0.975], np.float32)          # afternoon sun, a hair warm
        return np.clip(img, 0, 1).astype(np.float32)

    def _to_image(self, img):
        grain = (self.U - 0.5) * 0.018
        return Image.fromarray((np.clip(img + grain[..., None], 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name, card=None):
        img = self.composite()
        if card is not None: img = self._card_overlay(img, card)
        self.stages.append((name, self._to_image(img)))

    def save(self, path, stages_dir=None, quality=88):
        img = self._to_image(self.composite())
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
