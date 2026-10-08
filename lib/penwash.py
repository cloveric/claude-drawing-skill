"""penwash — 钢笔淡彩 / Pen & Wash: little fineliner-and-watercolour sketch cards on a table (numpy + Pillow only).

A sketcher's habit: a stack of small cold-press watercolour cards, a waterproof fineliner and a water brush. On each
card one goofy character is drawn quickly in ink (big head, round glasses, dot eyes, a red nose, a little body), then
loose washes go on top, and the cards are photographed lying on the table next to the pen and the brush.

  card      Each card is its own sheet with its own buffers, drawn in card units (= canvas px) *as if unrotated*, at
            `ss` x internal resolution, and laid on the table at a position and a small angle when the photo is
            composed. Cold-press paper: a height field of ~1 mm bumps (2-4 px here) on a softer undulation, lit by
            the window light from the upper left, so the tooth reads as tooth and not as noise; a warm white tone
            with faint mottle. The edge is a guillotine cut that is not quite straight (a sub-pixel wobble and fuzz),
            corners square or a little rounded.
  ink       A fineliner lays a near-uniform line (felt tip, pigment ink): every stroke is the drawn path re-sampled
            and pushed sideways by low-frequency hand wobble plus a little tremor, its width drifting +-9 %, a small
            blob where the tip rested before moving, and on some strokes a quick thinning flick at the end. It is
            drawn fast, so closed shapes are not closed: a head is one to three strokes that either stop short (an
            open gap) or run past the join and leave the curve on its tangent (crossing tails); corners of boxes are
            separate strokes that overshoot. Now and then part of a stroke is gone over again 1-2.5 px off (a doubled
            line). The ink is Beer-Lambert density (nearly black at one pass), with the deepest valleys of the tooth
            barely skipped. A part's outline is hidden where a part in front covers it (z order), so a sleeve's line
            stops at the coat and the ears tuck behind the head.
  wash      Watercolour / gouache is laid loosely after the ink (the ink is waterproof): a wash is the *intended*
            region (a part minus whatever is in front of it), then painted the way a quick hand paints it:
              misregistration  the whole wash slips 2-5 px one way, so colour runs over the line on one side and
                               leaves a white paper gap inside the line on the other;
              edge             the edge is re-found on a blurred copy with a threshold that wanders (low-frequency
                               noise in px: spill where negative, pull back where positive, plus patches pulled
                               back from the line), so the edge is crisp but wobbly and follows the paper tooth;
              wet edge         pigment migrates to the rim of a drying puddle: a darker rim just inside the edge;
              granulation      pigment settles into the valleys of the tooth: speckle tied to the paper itself;
              streaks          the flat brush leaves faint parallel streaks along its direction;
              variation        a puddle is never even: low-frequency density mottle;
              dry brush        on request the brush skips the tooth peaks (white specks at a dragged edge);
              bleed            colour dropped into a wash that is still wet spreads softly and stops at the wet
                               edge (cheeks into skin, a warm-to-cool gradient on a face);
              cockle           paper buckles where it got wet: a faint low relief in the photo light.
            Pigments are kept as density too (absorbance = -ln(masstone)), so overlaps darken and mix like paint.
            A background block is a rough flat wash rectangle that does not fill the card: wobbly brushed sides and
            corners, painted around the figure (the figure is reserved with a halo of a few px, so white paper
            shows between figure and block in places). White gouache (`highlight`, `glint`) is opaque and goes on
            last: glints on glasses, a shine on a nose or a loaf.
  photo     The cards lie on a table (`table`: oak planks with growth-ring grain, pores, seams and a satin sheen, or
            linen) under one window light from the upper left. Each card casts a soft offset shadow and a tight
            contact shadow; its cut edge catches the light on the lit side and darkens on the other. Tools are
            shaded cylinders with their own cast shadows: a fineliner (fibre tip, metal sleeve, grey cone, matte
            barrel with its size printed on it, posted glossy cap with a clip) and a water brush (black nylon tip
            stained with paint, ribbed grip, a clear barrel of water that refracts what is under it, with a bubble,
            and its clear cap). Then the camera: light fall-off away from the window, a vignette, a warm white
            balance and fine sensor grain.

API (card units are canvas px on the unturned card; z orders parts, higher is in front):
  surface   table(kind='oak'|'pale'|'walnut'|'linen'); card(cx, cy, w, h, rot, tone, corner) lays a blank card and
            makes it current, use(card) switches
  drawing   part(pts, z, strokes=None, corners=False, smooth=True, reserve=True) a region + its outline;
            limb(pts, w0, w1, z, caps) a sleeve / leg / strap; stroke(pts, z, width, closed, corners, double, over);
            lines(paths); dot(x, y, r); glasses(cx, cy, r, gap, z, temple); brows(paths); tufts(x, y, n, length);
            frame(x0, y0, x1, y1); ground(x0, x1, y); signature(x, y); ink() inks everything pending
  shapes    PenWash.oval(cx, cy, rx, ry, rot, egg, wob), rrect, box(cx, cy, w, h, rot), turn(pts, cx, cy, deg),
            smooth(pts, closed), tube(pts, w0, w1) -> (outline, sides), hand(x, y, angle, size, 'mitten'|'open'|'fist')
  paint     wash(target, colour, strength, shift, slip, warp, gaps, soft, edge, gran, streak, angle, var, dry);
            bleed(target, x, y, r, colour, strength); background_block(x0, y0, x1, y1, colour, rough, corner, halo);
            spatter(colour, n, box, size); highlight(pts, width) and glint(x, y, r) in white gouache. Colours are
            names in PAINTS or '#rrggbb'.
  photo     pen(x, y, angle, length, r); water_brush(x, y, angle, length, r, stain, cap=(x, y, angle));
            stage(name); save(path, stages_dir)

    import sys; sys.path.insert(0, 'lib')
    from penwash import PenWash
    pw = PenWash(1920, 1080, seed=3)
    pw.table('oak')
    pw.card(960, 540, 420, 520, rot=-3)                       # lays a blank card and makes it current
    head = pw.part(PenWash.oval(210, 200, 70, 78), z=10)      # an outline that will be inked
    lens = pw.glasses(196, 205, 24, gap=50, z=12)
    pw.dot(196, 207, 3.8, z=13); pw.dot(246, 205, 3.8, z=13)
    nose = pw.part(PenWash.oval(222, 238, 14, 12), z=13)
    coat = pw.part(PenWash.smooth([(150, 270), (275, 268), (300, 450), (128, 452)], closed=True), z=4)
    pw.ink(); pw.stage('ink')
    pw.wash(head, 'skin'); pw.bleed(head, 175, 245, 18, 'pink'); pw.wash(nose, 'coral'); pw.wash(coat, 'cobalt')
    pw.background_block(60, 90, 330, 380, 'mint'); pw.stage('wash')
    pw.pen(400, 990, 160); pw.save('penwash.jpg')
"""
import io
import os
from types import SimpleNamespace
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font
from core import shift as _move


def hexc(h):
    if not isinstance(h, str): return np.asarray(h, np.float32)
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


# masstone of each paint at strength 1 on white paper (absorbance = -ln(masstone), so strength scales density)
PAINTS = {
    'coral': '#ee4a3b', 'red': '#de3a2e', 'pink': '#f19a92', 'rose': '#ec7f80', 'peach': '#f5bc9c',
    'skin': '#f2c7a2', 'tan': '#e3ad7c', 'ochre': '#e2a656', 'yellow': '#f3cb52', 'brown': '#a8723f',
    'terracotta': '#d0724a', 'teal': '#3ea98b', 'mint': '#a3d5bd', 'sage': '#a7bc9f', 'green': '#5aa064',
    'cobalt': '#3c6ec4', 'sky': '#93b9df', 'bluegrey': '#9db0c3', 'grey': '#94979b', 'warmgrey': '#aaa197',
    'black': '#2c2c30', 'lilac': '#b3a3d3',
}
INK = '#141518'
PAPER = '#f7f4ec'
WOODS = {'oak': ('#cf9f66', '#93633a'), 'pale': ('#dcc29a', '#a98457'), 'walnut': ('#8a5d3b', '#4e321f')}
LINEN = '#cfc6b6'
SHADOW = np.array([0.20, 0.16, 0.13], np.float32)    # shadow tint (warm, multiplies)


def _closed_spline(P, per=6):
    P = np.asarray(P, np.float32)
    n = len(P)
    t = np.linspace(0, 1, per, endpoint=False, dtype=np.float32)[:, None]
    t2, t3 = t * t, t * t * t
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[(i - 1) % n], P[i], P[(i + 1) % n], P[(i + 2) % n]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.concatenate(out).astype(np.float32)


def _resample(P, step, closed=False):
    P = np.asarray(P, np.float32)
    if closed: P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = float(s[-1])
    if L < 1e-6: return P[:1].copy()
    n = max(2, int(np.ceil(L / step)) + 1)
    u = np.linspace(0, L, n)
    Q = np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1).astype(np.float32)
    return Q[:-1] if closed else Q


def _extend(Q, e0, e1):
    """open path: positive e runs past the end on the tangent (overshoot), negative stops short (gap)"""
    Q = np.asarray(Q, np.float32)
    if len(Q) < 4: return Q
    if e1 < 0: Q = Q[:max(3, len(Q) - int(-e1))]
    if e0 < 0: Q = Q[min(len(Q) - 3, int(-e0)):]
    if e1 > 0:
        d = Q[-1] - Q[-min(4, len(Q))]; d /= (np.linalg.norm(d) + 1e-6)
        k = np.arange(1, int(e1) + 1, dtype=np.float32)[:, None]
        Q = np.vstack([Q, Q[-1] + d * k])
    if e0 > 0:
        d = Q[0] - Q[min(3, len(Q) - 1)]; d /= (np.linalg.norm(d) + 1e-6)
        k = np.arange(int(e0), 0, -1, dtype=np.float32)[:, None]
        Q = np.vstack([Q[0] + d * k, Q])
    return Q


def _corners(P, closed, thr=48.0):
    """split a polyline at sharp corners (turning angle > thr degrees)"""
    P = np.asarray(P, np.float32)
    n = len(P)
    idx = []
    rng_ = range(n) if closed else range(1, n - 1)
    for i in rng_:
        a, b, c = P[(i - 1) % n], P[i], P[(i + 1) % n]
        u, v = b - a, c - b
        nu, nv = np.linalg.norm(u), np.linalg.norm(v)
        if nu < 1e-6 or nv < 1e-6: continue
        ang = np.degrees(np.arccos(np.clip((u @ v) / (nu * nv), -1, 1)))
        if ang > thr: idx.append(i)
    if not idx:
        return [np.vstack([P, P[:1]])] if closed else [P]
    segs = []
    if closed:
        for k in range(len(idx)):
            a, b = idx[k], idx[(k + 1) % len(idx)]
            if b <= a: b += n
            segs.append(P[np.arange(a, b + 1) % n])
    else:
        cut = [0] + idx + [n - 1]
        for a, b in zip(cut[:-1], cut[1:]): segs.append(P[a:b + 1])
    return segs


def _inter(a, b):
    """overlap of two (slice_y, slice_x) boxes -> (sub-slices of a, sub-slices of b) or None"""
    y0, y1 = max(a[0].start, b[0].start), min(a[0].stop, b[0].stop)
    x0, x1 = max(a[1].start, b[1].start), min(a[1].stop, b[1].stop)
    if y1 <= y0 or x1 <= x0: return None
    return ((slice(y0 - a[0].start, y1 - a[0].start), slice(x0 - a[1].start, x1 - a[1].start)),
            (slice(y0 - b[0].start, y1 - b[0].start), slice(x0 - b[1].start, x1 - b[1].start)))


def _bilinear(img, fx, fy):
    """sample img (h, w, c) at float pixel coords (pixel centres at integers); outside -> 0"""
    h, w = img.shape[:2]
    x0 = np.floor(fx).astype(np.int32); y0 = np.floor(fy).astype(np.int32)
    ax = (fx - x0).astype(np.float32)[..., None]; ay = (fy - y0).astype(np.float32)[..., None]
    out = np.zeros(fx.shape + (img.shape[2],), np.float32)
    for dy, wy in ((0, 1 - ay), (1, ay)):
        for dx, wx in ((0, 1 - ax), (1, ax)):
            xi, yi = x0 + dx, y0 + dy
            ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
            v = img[np.clip(yi, 0, h - 1), np.clip(xi, 0, w - 1)]
            out += v * (wx * wy) * ok[..., None]
    return out


class PenWash:
    PAINTS = PAINTS

    def __init__(self, W=1920, H=1080, seed=0, ss=2, keep_stages=True, stages_dir=None):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.surface = np.full((H, W, 3), 0.75, np.float32)
        self.cards, self.cur = [], None
        self.tools = []
        self.ld = np.array([0.55, 0.83], np.float32)          # direction the window light travels (to lower right)
        self.ink_abs = -np.log(hexc(INK))
        self.width = 3.3                                      # default fineliner width, canvas px
        YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
        g = (0.55 * XX / W + 0.83 * YY / H) / 1.38
        rr = np.hypot((XX - W * 0.42) / (W * 0.75), (YY - H * 0.40) / (H * 0.78))
        self._light = (1.06 - 0.17 * smoothstep(0.05, 1.05, g) - 0.13 * smoothstep(0.45, 1.25, rr)).astype(np.float32)
        self._grain = np.random.default_rng(seed + 991).normal(0, 1, (H, W)).astype(np.float32)
        self._grain = 0.7 * self._grain + 0.3 * blur(self._grain, 0.8) * 2.2
        self.warm = np.array([1.025, 1.0, 0.95], np.float32)

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================== table
    def table(self, kind='oak', plank=176, seed=None):
        """the surface the cards lie on: 'oak' / 'pale' / 'walnut' planks, or 'linen' cloth"""
        H, W = self.H, self.W
        r = np.random.default_rng(self._seed() if seed is None else seed)
        if kind == 'linen':
            self.surface = self._linen(r); return
        lite, dark = (hexc(c) for c in WOODS[kind])
        YY = np.arange(H, dtype=np.float32)[:, None]

        def streaks(sy, sx, rows):         # noise stretched along the board: sy px across, sx px along
            g = r.random((int(rows / sy) + 3, int(W / sx) + 3)).astype(np.float32)
            return np.asarray(Image.fromarray(g).resize((W, rows), Image.BICUBIC), np.float32)

        def board(rows):
            """one board's colour mix 0..1 (growth rings with cathedral arches, fibres, pores)"""
            fine, mid, broad, pores, warp = (streaks(1.3, 60, rows), streaks(5, 260, rows), streaks(45, 700, rows),
                                             streaks(1.0, 9, rows), streaks(70, 520, rows))
            yy = np.arange(rows, dtype=np.float32)[:, None]
            XX = np.arange(W, dtype=np.float32)[None, :]
            period = r.uniform(6, 12)
            ph = yy + r.uniform(20, 60) * (warp - 0.5) + 9 * (mid - 0.5)
            for _ in range(int(r.integers(1, 3))):          # flat-sawn boards: nested 'cathedral' arches
                xc, wc = r.uniform(-0.1, 1.1) * W, r.uniform(260, 700)
                arch = np.sqrt(np.clip(1 - ((XX - xc) / wc) ** 2, 0, 1)) ** 1.5
                ph = ph - r.uniform(0.6, 1.6) * rows * arch * (0.85 + 0.3 * warp)
            ring = 0.5 + 0.5 * np.cos(2 * np.pi * ph / period)
            late = smoothstep(0.55, 0.97, ring) * (0.55 + 0.45 * mid)
            a = 0.16 + 0.34 * late + 0.22 * (broad - 0.5) + 0.16 * (fine - 0.5)
            a += 0.35 * smoothstep(0.82, 0.95, pores) * (0.4 + 0.6 * late)
            return a + r.normal(0, 0.05), 1 + r.normal(0, 0.045)

        off = r.uniform(0, plank)
        out = np.zeros((H, W, 3), np.float32)
        XX = np.arange(W, dtype=np.float32)[None, :]
        edges = [0] + [int(off + plank * i) for i in range(0, int(H / plank) + 3) if 0 < off + plank * i < H] + [H]
        for y0, y1 in zip(edges[:-1], edges[1:]):
            if y1 <= y0: continue
            rows = y1 - y0
            yy = np.arange(rows, dtype=np.float32)[:, None]
            a, tone = board(rows)
            col = (lite[None, None] * (1 - a[..., None]) + dark[None, None] * a[..., None]) * tone
            if r.random() < 0.8:                              # a butt joint: another board starts here
                xj = r.uniform(0.1, 0.9) * W
                a2, tone2 = board(rows)
                col2 = (lite[None, None] * (1 - a2[..., None]) + dark[None, None] * a2[..., None]) * tone2
                right = (XX > xj)[..., None]
                col = np.where(right, col2, col)
                col *= (1 - 0.5 * np.exp(-((XX - xj) / 1.2) ** 2))[..., None]
                col *= (1 + 0.04 * np.exp(-((XX - xj - 2.5) / 1.5) ** 2))[..., None]
            # plank seams: a dark gap with a lit bevel just below it
            seam = np.exp(-(yy / 1.3) ** 2) + np.exp(-((rows - 1 - yy) / 1.3) ** 2)
            col *= (1 - 0.55 * seam)[..., None]
            col *= (1 + 0.05 * np.exp(-((yy - 3.0) / 1.6) ** 2))[..., None]
            out[y0:y1] = col
        # satin finish: a broad soft reflection of the window
        XX = np.arange(W, dtype=np.float32)[None, :]
        sheen = np.exp(-(((XX - 0.30 * W) / (0.42 * W)) ** 2 + ((YY - 0.12 * H) / (0.55 * H)) ** 2))
        out = out * (1 + 0.06 * sheen[..., None]) + 0.025 * sheen[..., None]
        self.surface = out.astype(np.float32)

    def _linen(self, r):
        H, W = self.H, self.W
        base = hexc(LINEN)
        a = blur(r.random((H, W), dtype=np.float32), 0.6)
        wx = np.asarray(Image.fromarray(r.random((H, W // 3), dtype=np.float32)).resize((W, H), Image.BILINEAR))
        wy = np.asarray(Image.fromarray(r.random((H // 3, W), dtype=np.float32)).resize((W, H), Image.BILINEAR))
        YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
        weave = 0.5 + 0.25 * np.sin(XX * 2.1) * (wy - 0.5) * 2 + 0.25 * np.sin(YY * 2.1) * (wx - 0.5) * 2
        slub = smoothstep(0.75, 0.95, np.asarray(Image.fromarray(r.random((H // 2, W // 40), dtype=np.float32)).resize((W, H), Image.BICUBIC)))
        v = 1 + 0.06 * (weave - 0.5) + 0.03 * (a - 0.5) - 0.05 * slub
        return (base[None, None] * v[..., None]).astype(np.float32)

    # ================================================================== cards
    def card(self, cx, cy, w, h, rot=0.0, tone=PAPER, corner=6.0, tooth=1.0, seed=None):
        """lay a blank cold-press card centred at (cx, cy), w x h canvas px, turned rot degrees (clockwise);
        it becomes the current card. Draw on it in card units (0..w, 0..h) as if it were not turned."""
        ss = self.ss
        Wi, Hi = int(round(w * ss)), int(round(h * ss))
        r = np.random.default_rng(self._seed() if seed is None else seed)
        t1 = blur(r.random((Hi, Wi), dtype=np.float32), 1.0 * ss); t1 = (t1 - t1.mean()) / (t1.std() + 1e-6)
        t2 = blur(r.random((Hi, Wi), dtype=np.float32), 2.4 * ss); t2 = (t2 - t2.mean()) / (t2.std() + 1e-6)
        t = 0.6 * t1 + 0.4 * t2; t /= (t.std() + 1e-6)
        th = np.clip(0.5 + 0.17 * t, 0, 1).astype(np.float32)
        gy, gx = np.gradient(blur(th, 0.5 * ss))
        lit = (0.55 * gx + 0.83 * gy) * ss
        mot = noise2d(Hi, Wi, 90 * ss, 3, int(r.integers(1 << 30))) - 0.5
        base = hexc(tone)[None, None] * (1 + 0.20 * tooth * lit + 0.012 * mot)[..., None]
        # the cut: a rounded rectangle whose sides are not quite straight, with a little fuzz
        u = (np.arange(Wi, dtype=np.float32) + 0.5) / ss - w / 2
        v = (np.arange(Hi, dtype=np.float32) + 0.5) / ss - h / 2
        qx = np.abs(u)[None, :] - (w / 2 - corner); qy = np.abs(v)[:, None] - (h / 2 - corner)
        sdf = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - corner
        sdf += 0.9 * (noise2d(Hi, Wi, 60 * ss, 2, int(r.integers(1 << 30))) - 0.5)
        sdf += 0.35 * (blur(r.random((Hi, Wi), dtype=np.float32), 0.7 * ss) - 0.5) * 4
        alpha = np.clip(0.5 - sdf * ss, 0, 1).astype(np.float32)
        c = SimpleNamespace(cx=cx, cy=cy, w=w, h=h, rot=rot, Wi=Wi, Hi=Hi, base=base.astype(np.float32), tooth=th,
                            alpha=alpha, D=np.zeros((Hi, Wi, 3), np.float32), wet=np.zeros((Hi, Wi), np.float32),
                            cover_a=None, cover_rgb=None, parts=[], strokes=[], shown=True, rng=r)
        self.cards.append(c)
        self.cur = c
        return c

    def use(self, card):
        """make `card` the current card"""
        self.cur = card
        return card

    def _c(self, card):
        return card if card is not None else self.cur

    def _box(self, c, x0, y0, x1, y1):
        """internal-pixel box clipped to the card"""
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(c.Wi, int(np.ceil(x1)) + 1), min(c.Hi, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _poly(self, c, polys, pad=3, sl=None):
        """closed polygons (card units) -> (slice, AA mask crop); 2x supersampled"""
        ss = self.ss
        if sl is None:
            P = np.concatenate([np.asarray(p, np.float32) for p in polys]) * ss
            sl = self._box(c, P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
            if sl is None: return None, None
        x0, y0 = sl[1].start, sl[0].start
        w, h = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (w * 2, h * 2), 0)
        d = ImageDraw.Draw(im)
        for p in polys:
            q = (np.asarray(p, np.float32) * ss - [x0, y0]) * 2
            if len(q) >= 3: d.polygon([tuple(map(float, a)) for a in q], fill=255)
        return sl, np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255

    # ================================================================== geometry helpers (card units)
    @staticmethod
    def smooth(pts, closed=False, per=8):
        """Catmull-Rom through control points"""
        return _closed_spline(pts, per) if closed else spline(pts, per)

    @staticmethod
    def oval(cx, cy, rx, ry=None, rot=0.0, egg=0.0, n=72, wob=0.0, seed=0):
        """closed ellipse; egg > 0 widens the bottom (a jowly head), < 0 the top; wob = relative wobble"""
        ry = rx if ry is None else ry
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        x, y = np.cos(t) * rx, np.sin(t) * ry
        x = x * (1 + egg * np.sin(t))
        if wob:
            k = 1 + wob * fbm1d(n, n / 5, 3, seed)
            x, y = x * k, y * k
        c, s = np.cos(np.radians(rot)), np.sin(np.radians(rot))
        return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)

    @staticmethod
    def turn(pts, cx, cy, deg):
        """rotate points about (cx, cy) by deg (clockwise on screen)"""
        P = np.asarray(pts, np.float32)
        c, s = np.cos(np.radians(deg)), np.sin(np.radians(deg))
        d = P - [cx, cy]
        return np.stack([cx + d[:, 0] * c - d[:, 1] * s, cy + d[:, 0] * s + d[:, 1] * c], 1).astype(np.float32)

    @staticmethod
    def box(cx, cy, w, h, rot=0.0):
        """corners of a w x h rectangle centred on (cx, cy), turned rot degrees"""
        P = np.array([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)], np.float32)
        return PenWash.turn(P, cx, cy, rot)

    @staticmethod
    def rrect(x0, y0, x1, y1, r=6.0, n=5):
        pts = []
        for (cx, cy, a0) in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
            for a in np.linspace(a0, a0 + 90, n):
                pts.append((cx + r * np.cos(np.radians(a)), cy + r * np.sin(np.radians(a))))
        return np.array(pts, np.float32)

    @staticmethod
    def tube(pts, w0, w1=None, per=8):
        """a limb / strap / loaf around a centre line, width w0 -> w1.
        Returns (outline, sides): sides = [left, right, end_cap, start_cap] open paths for inking."""
        w1 = w0 if w1 is None else w1
        C = spline(pts, per) if len(pts) > 2 else _resample(pts, 3.0)
        C = _resample(C, 2.0)
        n = len(C)
        tg = np.gradient(C, axis=0); tg /= (np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6)
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        wd = np.linspace(w0, w1, n)[:, None] / 2
        L, R = C + nr * wd, C - nr * wd
        a1 = np.arctan2(nr[-1, 1], nr[-1, 0])
        cap_e = np.array([C[-1] + wd[-1] * np.array([np.cos(a1 - t), np.sin(a1 - t)]) for t in np.linspace(0, np.pi, 9)], np.float32)
        a0 = np.arctan2(-nr[0, 1], -nr[0, 0])
        cap_s = np.array([C[0] + wd[0] * np.array([np.cos(a0 - t), np.sin(a0 - t)]) for t in np.linspace(0, np.pi, 9)], np.float32)
        outline = np.vstack([L, cap_e[1:-1], R[::-1], cap_s[1:-1]]).astype(np.float32)
        return outline, [L.astype(np.float32), R.astype(np.float32), cap_e, cap_s]

    @staticmethod
    def hand(x, y, angle, size=26.0, kind='mitten', flip=False):
        """a simple cartoon hand at the wrist (x, y), pointing at `angle` degrees.
        kind: 'mitten' (thumb + a paddle), 'open' (four short fingers + thumb), 'fist' (round, holding).
        Returns (outline, detail paths)."""
        if kind == 'open':
            P = [(0, 0.30), (0.42, 0.36)]
            fy = [0.27, 0.09, -0.09, -0.27]
            for i, c in enumerate(fy):
                hw = 0.085
                tip = 0.95 - 0.07 * abs(i - 1.3)
                P += [(0.46, c + hw), (tip - 0.05, c + hw), (tip + 0.02, c + hw * 0.4), (tip + 0.02, c - hw * 0.4),
                      (tip - 0.05, c - hw), (0.52, c - hw)]
            P += [(0.44, -0.36), (0.50, -0.55), (0.42, -0.66), (0.30, -0.60), (0.20, -0.38), (0, -0.30)]
            det = []
        elif kind == 'fist':
            P = [(0, 0.28), (0.25, 0.36), (0.55, 0.36), (0.72, 0.25), (0.75, 0.0), (0.70, -0.24), (0.52, -0.36),
                 (0.38, -0.50), (0.22, -0.48), (0.18, -0.34), (0, -0.28)]
            det = [[(0.55, 0.12), (0.72, 0.12)], [(0.55, -0.08), (0.73, -0.08)]]
        else:
            P = [(0, 0.30), (0.40, 0.38), (0.78, 0.30), (0.95, 0.06), (0.90, -0.20), (0.66, -0.32), (0.50, -0.34),
                 (0.52, -0.55), (0.40, -0.66), (0.26, -0.56), (0.20, -0.36), (0, -0.30)]
            det = []
        a = np.radians(angle); c, s = np.cos(a), np.sin(a)
        sg = -1.0 if flip else 1.0

        def tf(Q):
            Q = np.asarray(Q, np.float32) * size
            Q[:, 1] *= sg
            return np.stack([x + Q[:, 0] * c - Q[:, 1] * s, y + Q[:, 0] * s + Q[:, 1] * c], 1).astype(np.float32)
        outl = _closed_spline(tf(P), 4) if kind != 'open' else tf(P)
        return outl, [tf(d) for d in det]

    # ================================================================== parts and strokes (deferred until ink())
    def part(self, pts, z=0.0, ink=True, strokes=None, corners=False, smooth=True, width=None, reserve=True,
             nseg=None, card=None, name=None):
        """a shape on the current card: its region (for washes and occlusion) and its ink outline.
        strokes: list of open paths to ink instead of the closed outline (tube sides, a hat brim);
        corners: split the outline at corners into overshooting strokes (boxes, bags, envelopes);
        reserve: background blocks are painted around it."""
        c = self._c(card)
        P = np.asarray(pts, np.float32)
        if smooth and not corners and len(P) > 3: P = _closed_spline(P, 5)
        sl, m = self._poly(c, [P])
        p = SimpleNamespace(kind='part', P=P, z=float(z), sl=sl, m=m, name=name, wet=None, reserve=reserve)
        if sl is None: return p
        c.parts.append(p)
        if ink:
            if strokes is None:
                self.stroke(P, z=z, closed=True, smooth=False, corners=corners, width=width, nseg=nseg, card=c)
            else:
                for s_ in strokes:
                    self.stroke(s_, z=z, smooth=False, width=width, card=c)
        return p

    def stroke(self, pts, z=1e9, width=None, closed=False, smooth=True, corners=False, wobble=1.0, over=(0.0, 3.0),
               double=None, flick=0.35, nseg=None, card=None):
        """one fineliner line (inked at the next ink()); z: hidden where parts with a higher z cover it"""
        c = self._c(card)
        s = SimpleNamespace(kind='line', P=np.asarray(pts, np.float32), z=float(z), width=width or self.width,
                            closed=closed, smooth=smooth, corners=corners, wobble=wobble, over=over,
                            double=(0.12 if closed else 0.07) if double is None else double, flick=flick, nseg=nseg,
                            seed=int(c.rng.integers(1 << 30)), done=False)
        c.strokes.append(s)
        return s

    def dot(self, x, y, r=3.8, z=1e9, card=None):
        """a pressed dot (an eye): a small filled blob of ink"""
        c = self._c(card)
        sd = int(c.rng.integers(1 << 30))
        P = PenWash.oval(x, y, r * np.random.default_rng(sd).uniform(0.92, 1.05), r * 1.08, n=24, wob=0.08, seed=sd)
        s = SimpleNamespace(kind='dot', P=P, z=float(z), seed=sd, done=False)
        c.strokes.append(s)
        return s

    def lines(self, paths, z=1e9, width=None, card=None, **kw):
        return [self.stroke(p, z=z, width=width, card=card, **kw) for p in paths]

    def limb(self, pts, w0, w1=None, z=0.0, caps=(False, True), card=None, name=None):
        """a sleeve, leg or strap as a part: tube region; inks both sides and the chosen end caps"""
        outl, (L, R, ce, cs) = PenWash.tube(pts, w0, w1)
        st = [L, R] + ([cs] if caps[0] else []) + ([ce] if caps[1] else [])
        return self.part(outl, z=z, strokes=st, smooth=False, card=card, name=name)

    # ------------------------------------------------------------------ face and figure helpers
    def glasses(self, cx, cy, r, gap=None, z=20.0, ry=None, temple=None, bridge=True, card=None):
        """big round glasses: two lens parts (kept white: washes behind them stop at the rims), a bridge,
        and a temple arm running back to `temple` (x, y) if given. Returns the two lens parts."""
        gap = 2.15 * r if gap is None else gap
        ry = r if ry is None else ry
        a = self.part(PenWash.oval(cx, cy, r, ry, wob=0.03, seed=int(self._c(card).rng.integers(999))), z=z, nseg=1, card=card)
        b = self.part(PenWash.oval(cx + gap, cy - 1, r, ry, wob=0.03, seed=int(self._c(card).rng.integers(999))), z=z, nseg=1, card=card)
        if bridge:
            self.stroke([(cx + r - 1, cy - 2), (cx + gap / 2, cy - 6), (cx + gap - r + 1, cy - 3)], z=z, card=card, double=0)
        if temple is not None:
            self.stroke([(cx - r + 1, cy - 2), ((cx - r + temple[0]) / 2, (cy + temple[1]) / 2 - 2), temple], z=z - 0.5,
                        card=card, double=0)
        return a, b

    def brows(self, pts_list, z=1e9, card=None):
        return [self.stroke(p, z=z, width=self.width * 0.85, card=card, double=0, over=(0, 1)) for p in pts_list]

    def tufts(self, x, y, n=5, length=14.0, spread=60.0, angle=-90.0, z=1e9, card=None, seed=None):
        """a few quick hair strands fanning out from (x, y)"""
        c = self._c(card)
        r = np.random.default_rng(int(c.rng.integers(1 << 30)) if seed is None else seed)
        out = []
        for i in range(n):
            a = np.radians(angle + spread * ((i + 0.5) / n - 0.5) + r.uniform(-6, 6))
            L = length * r.uniform(0.7, 1.15)
            bend = r.uniform(-0.25, 0.25)
            p0 = np.array([x + r.uniform(-3, 3), y + r.uniform(-2, 2)])
            p2 = p0 + L * np.array([np.cos(a), np.sin(a)])
            p1 = (p0 + p2) / 2 + bend * L * np.array([-np.sin(a), np.cos(a)])
            out.append(self.stroke([p0, p1, p2], z=z, width=self.width * 0.85, card=card, double=0, over=(0, 1)))
        return out

    def frame(self, x0, y0, x1, y1, z=-50.0, card=None):
        """an inked border box, each side its own stroke overshooting the corners. Returns its points."""
        P = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], np.float32)
        self.stroke(P, z=z, closed=True, smooth=False, corners=True, card=card, double=0.3, over=(2, 9))
        return P

    def ground(self, x0, x1, y, width=None, z=-10.0, heavy=True, card=None):
        """a ground line: one or two quick heavy strokes"""
        c = self._c(card)
        r = np.random.default_rng(int(c.rng.integers(1 << 30)))
        w = width or self.width * (1.7 if heavy else 1.0)
        xm = x0 + (x1 - x0) * r.uniform(0.45, 0.65)
        self.stroke([(x0, y + r.uniform(-1, 1)), ((x0 + xm) / 2, y + r.uniform(-1.5, 1.5)), (xm + 8, y + r.uniform(-1, 1))],
                    z=z, width=w, card=card, double=0, over=(0, 2))
        self.stroke([(xm - 6, y + r.uniform(0.5, 2.0)), ((xm + x1) / 2, y + r.uniform(-1, 2)), (x1, y + r.uniform(-1, 1.5))],
                    z=z, width=w, card=card, double=0, over=(0, 2))

    def signature(self, x, y, size=9.0, z=1e9, card=None):
        """a tiny spiral mark in a corner, the way a sketcher initials a card"""
        t = np.linspace(0, 3.3 * np.pi, 40)
        rr = size * (1 - t / (4 * np.pi))
        P = np.stack([x + rr * np.cos(t), y + rr * np.sin(t) * 0.9], 1)
        return self.stroke(P, z=z, width=self.width * 0.9, smooth=False, card=card, double=0)

    # ================================================================== ink
    def _paths(self, s):
        """a deferred stroke -> list of (points, widths) as the hand actually drew them"""
        r = np.random.default_rng(s.seed)
        P = np.asarray(s.P, np.float32)
        segs = []
        if s.closed:
            if s.smooth and len(P) > 3: P = _closed_spline(P, 6)
            if s.corners:
                for g in _corners(P, True):
                    g = _resample(g, 1.0)
                    segs.append(_extend(g, r.uniform(*s.over), r.uniform(*s.over)))
            else:
                Q = _resample(P, 1.0, closed=True)
                n = len(Q)
                k = s.nseg or (1 if n < 150 else int(r.choice([1, 2, 2, 3])))
                start = int(r.integers(n))
                cuts = [start + int(n * (i + (r.uniform(-0.1, 0.1) if i else 0)) / k) for i in range(k)]
                for i in range(k):
                    a = cuts[i]
                    b = cuts[i + 1] if i + 1 < k else cuts[0] + n
                    g = Q[np.arange(a, b + 1) % n]
                    e = r.uniform(-1, 1)
                    e0 = r.uniform(-4.0, 5.0) if e < 0.1 else r.uniform(1.0, 7.0)
                    e1 = r.uniform(-6.0, 7.0)
                    segs.append(_extend(g, e0, e1))
        else:
            if s.smooth and len(P) > 2: P = spline(P, 8)
            parts = _corners(P, False) if s.corners else [P]
            for g in parts:
                g = _resample(g, 1.0)
                segs.append(_extend(g, r.uniform(*s.over), r.uniform(*s.over)))
        out = []
        for g in segs:
            if len(g) < 2: continue
            out += self._hand(g, s, r)
        return out

    def _hand(self, g, s, r):
        """wobble, width drift, rest blob, flick; sometimes a second pass a little off"""
        n = len(g)
        tg = np.gradient(g, axis=0); tg /= (np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6)
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        off = fbm1d(n, 55, 3, int(r.integers(1 << 30))) * 1.0 * s.wobble
        off += fbm1d(n, 8, 2, int(r.integers(1 << 30))) * 0.22 * s.wobble
        Q = g + nr * off[:, None]
        tpx = np.arange(n, dtype=np.float32)
        w = s.width * (1 + 0.09 * fbm1d(n, 40, 2, int(r.integers(1 << 30))))
        w *= 1 + 0.22 * np.exp(-tpx / 2.5)
        if r.random() < s.flick and n > 14:
            w *= np.interp(tpx, [n - 9, n - 1], [1.0, 0.5])
        out = [(Q, w)]
        if r.random() < s.double and n > 30:
            a = int(r.uniform(0, 0.4) * n); b = int(min(n, a + r.uniform(0.35, 0.8) * n))
            d = r.uniform(1.1, 2.4) * (1 if r.random() < 0.5 else -1)
            off2 = d * (0.5 + 0.5 * np.sin(np.linspace(0, np.pi, b - a))) + fbm1d(b - a, 30, 2, int(r.integers(1 << 30))) * 0.6
            Q2 = g[a:b] + nr[a:b] * (off[a:b] + off2)[:, None]
            out.append((Q2, w[a:b] * 0.85))
        return out

    def _raster(self, c, paths):
        """paths in card units -> (slice, coverage crop) at internal res, 2x supersampled"""
        ss = self.ss
        allp = np.concatenate([q for q, _ in paths]) * ss
        pad = max(float(np.max(w)) for _, w in paths) * ss + 4
        sl = self._box(c, allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        if sl is None: return None, None
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        S = 2 * ss
        im = Image.new('L', (bw * 2, bh * 2), 0)
        d = ImageDraw.Draw(im)
        o = np.array([x0, y0], np.float32) / ss
        for Q, w in paths:
            q = (Q - o) * S
            ww = np.maximum(1, np.round((w[:-1] + w[1:]) * 0.5 * S)).astype(int) if len(q) > 1 else np.array([max(1, int(w[0] * S))])
            ql = q.tolist()
            i = 0
            n = len(q)
            while i < n - 1:
                j = i + 1
                while j < n - 1 and ww[j] == ww[i] and j - i < 60: j += 1
                d.line([tuple(p) for p in ql[i:j + 1]], fill=255, width=int(ww[i]), joint='curve')
                i = j
            for k in (0, n - 1):
                rr = w[k] * S / 2
                d.ellipse([q[k, 0] - rr, q[k, 1] - rr, q[k, 0] + rr, q[k, 1] + rr], fill=255)
        cov = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        return sl, cov

    def _front(self, c, sl, z):
        """union of the regions of parts in front of depth z, over box sl"""
        F = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), np.float32)
        for q in c.parts:
            if q.z <= z or q.sl is None: continue
            ij = _inter(sl, q.sl)
            if ij is None: continue
            np.maximum(F[ij[0]], q.m[ij[1]], out=F[ij[0]])
        return F

    def ink(self, card=None):
        """ink every pending stroke of the card (outlines, details, dots)"""
        c = self._c(card)
        for s in c.strokes:
            if s.done: continue
            s.done = True
            if s.kind == 'dot':
                sl, cov = self._poly(c, [s.P], pad=4)
            else:
                paths = self._paths(s)
                if not paths: continue
                sl, cov = self._raster(c, paths)
            if sl is None: continue
            th = c.tooth[sl]
            amt = cov * (1 - 0.22 * smoothstep(0.26, 0.10, th))
            amt = blur(amt, 0.3 * self.ss)
            if s.z < 1e8:
                F = self._front(c, sl, s.z)
                if F.any():
                    F = smoothstep(0.55, 0.9, blur(F, 0.6 * self.ss))
                    amt = amt * (1 - F)
            c.D[sl] += amt[..., None] * self.ink_abs

    # ================================================================== washes
    def _region(self, c, target, pad):
        """wash target -> (padded slice, intended region). target: part, list of parts, points, or ('mask', sl, m)"""
        def is_pts(t):            # a polygon given as an array or a list of (x, y) pairs
            if isinstance(t, np.ndarray): return True
            return isinstance(t, (list, tuple)) and len(t) > 2 and all(np.ndim(q) == 1 and len(q) == 2 and
                                                                      not isinstance(q[0], str) for q in t[:3])
        if isinstance(target, tuple) and len(target) == 3 and isinstance(target[0], str): items = [target]
        elif is_pts(target): items = [np.asarray(target, np.float32)]
        elif isinstance(target, (list, tuple)): items = list(target)
        else: items = [target]
        boxes, pieces = [], []
        for t in items:
            if isinstance(t, SimpleNamespace):
                if t.sl is None: continue
                vis = t.m * (1 - self._front(c, t.sl, t.z))
                pieces.append((t.sl, vis)); boxes.append(t.sl)
            elif isinstance(t, tuple) and len(t) == 3 and t[0] == 'mask':
                pieces.append((t[1], t[2])); boxes.append(t[1])
            else:
                sl, m = self._poly(c, [np.asarray(t, np.float32)])
                if sl is None: continue
                pieces.append((sl, m)); boxes.append(sl)
        if not boxes: return None, None
        p = int(pad)
        sl = self._box(c, min(b[1].start for b in boxes) - p, min(b[0].start for b in boxes) - p,
                       max(b[1].stop for b in boxes) + p, max(b[0].stop for b in boxes) + p)
        R = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), np.float32)
        for bsl, m in pieces:
            ij = _inter(sl, bsl)
            if ij is not None: np.maximum(R[ij[0]], m[ij[1]], out=R[ij[0]])
        return sl, R

    def _streaks(self, h, w, angle, along, across, seed):
        D = int(np.ceil(np.hypot(h, w))) + 4
        g = np.random.default_rng(seed).random((max(2, int(D / across)), max(2, int(D / along)))).astype(np.float32)
        im = Image.fromarray(g).resize((D, D), Image.BICUBIC).rotate(-angle, resample=Image.BILINEAR)
        a = np.asarray(im, np.float32)
        y0, x0 = (D - h) // 2, (D - w) // 2
        return a[y0:y0 + h, x0:x0 + w]

    def wash(self, target, colour, strength=1.0, shift=None, slip=(2.0, 4.8), warp=1.6, gaps=2.2, soft=2.2,
             edge=0.35, gran=0.14, streak=0.08, angle=None, var=0.13, dry=0.0, card=None):
        """a loose watercolour wash of `colour` (paint name or '#rrggbb') over a target region.
        shift: (dx, dy) misregistration in px (default: random, |slip| px); warp: px the edge wanders in and out;
        gaps: px the paint pulls back from the line in patches; soft: px of edge rounding; edge: wet-edge rim;
        gran: granulation; streak: brush streaks along `angle` (degrees); var: density mottle; dry: dry-brush specks."""
        c = self._c(card)
        ss = self.ss
        r = np.random.default_rng(int(c.rng.integers(1 << 30)))
        col = hexc(PAINTS.get(colour, colour) if isinstance(colour, str) else colour)
        absorb = -np.log(np.clip(col, 0.02, 1.0))
        pad = (max(slip) + warp + soft * 3 + 6) * ss
        sl, R = self._region(c, target, pad)
        if sl is None: return None
        h, w = R.shape
        req = np.sqrt(R.sum() / np.pi) / ss                       # equivalent radius of the region, px
        f = float(np.clip(req / 16.0, 0.22, 1.0))
        slip, gaps, warp, soft = (slip[0] * f, slip[1] * f), gaps * f, warp * f, max(0.6, soft * f)
        if shift is None:
            a = r.uniform(0, 2 * np.pi); m = r.uniform(*slip)
            shift = (m * np.cos(a), m * np.sin(a))
        if shift[0] or shift[1]:
            R = _move(R, shift[0] * ss, shift[1] * ss)
        sig = max(0.5, soft) * ss
        Rb = blur(R, sig)
        o = warp * 2 * (noise2d(h, w, 26 * ss, 2, int(r.integers(1 << 30))) - 0.5)
        if gaps: o = o + gaps * smoothstep(0.52, 0.78, noise2d(h, w, 20 * ss, 2, int(r.integers(1 << 30))))
        thr = 0.5 + 0.5 * np.tanh(0.8 * o * ss / sig)
        tex = (c.tooth[sl] - 0.5) * 0.10 + (noise2d(h, w, 4 * ss, 1, int(r.integers(1 << 30))) - 0.5) * 0.04
        M = smoothstep(thr - 0.035, thr + 0.035, Rb + tex)
        if not M.any(): return None
        d = strength * (1 + var * 2 * (noise2d(h, w, 40 * ss, 3, int(r.integers(1 << 30))) - 0.5))
        if streak:
            ang = r.uniform(0, 180) if angle is None else angle
            st = self._streaks(h, w, ang, 70 * ss, 3.5 * ss, int(r.integers(1 << 30)))
            d = d * (1 + streak * 2 * (st - 0.5))
        ring = np.clip(M - blur(M, 1.6 * ss), 0, None)
        d = d + edge * 2.0 * ring * strength
        th = c.tooth[sl]
        d = d * (1 + gran * 2.2 * (0.5 - th))
        if dry:
            d = d * (1 - dry * smoothstep(0.6, 0.74, th) * smoothstep(0.35, 0.7, noise2d(h, w, 30 * ss, 2, int(r.integers(1 << 30)))))
        dens = np.clip(M * d, 0, 3.0)
        c.D[sl] += dens[..., None] * absorb
        c.wet[sl] += M * min(1.0, strength)
        if isinstance(target, SimpleNamespace): target.wet = (sl, M)
        return (sl, M)

    def bleed(self, target, x, y, r, colour, strength=0.6, card=None):
        """drop `colour` into a wash that is still wet: soft spread around (x, y), stopped by the wet edge"""
        c = self._c(card)
        ss = self.ss
        col = hexc(PAINTS.get(colour, colour) if isinstance(colour, str) else colour)
        absorb = -np.log(np.clip(col, 0.02, 1.0))
        if isinstance(target, SimpleNamespace) and target.wet is not None:
            sl, M = target.wet
        elif isinstance(target, tuple) and len(target) == 2:
            sl, M = target
        else:
            sl, M = self._region(c, target, 4 * ss)
            if sl is None: return
        h, w = M.shape
        Y = (np.arange(h, dtype=np.float32)[:, None] + sl[0].start + 0.5) / ss
        X = (np.arange(w, dtype=np.float32)[None, :] + sl[1].start + 0.5) / ss
        nz = noise2d(h, w, max(4, r * 0.6) * ss, 2, int(c.rng.integers(1 << 30)))
        dist = np.hypot(X - x, Y - y) / (r * (0.8 + 0.4 * nz))
        g = np.exp(-dist ** 2 * 1.4)
        dens = g * M * strength
        c.D[sl] += dens[..., None] * absorb

    def background_block(self, x0, y0, x1, y1, colour, strength=0.92, rough=5.0, corner=12.0, halo=4.0, angle=None,
                         edge=0.5, streak=0.12, dry=0.2, card=None):
        """a rough flat wash rectangle behind the figure that does not fill the card. Its sides are wobbly brush
        edges; it is painted around every reserving part, leaving a white halo of ~halo px in places."""
        c = self._c(card)
        ss = self.ss
        r = np.random.default_rng(int(c.rng.integers(1 << 30)))
        P = _resample(PenWash.rrect(x0, y0, x1, y1, corner, 7), 2.0, closed=True)
        n = len(P)
        tg = np.gradient(np.vstack([P[-1:], P, P[:1]]), axis=0)[1:-1]
        tg /= (np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6)
        nr = np.stack([tg[:, 1], -tg[:, 0]], 1)
        off = fbm1d(n, 30, 3, int(r.integers(1 << 30))) * rough + fbm1d(n, 6, 2, int(r.integers(1 << 30))) * rough * 0.25
        P = P + nr * off[:, None]
        sl, R = self._poly(c, [P], pad=(rough + 20) * ss)
        if sl is None: return None
        h, w = R.shape
        F = np.zeros_like(R)
        for q in c.parts:
            if not q.reserve or q.sl is None: continue
            ij = _inter(sl, q.sl)
            if ij is not None: np.maximum(F[ij[0]], q.m[ij[1]], out=F[ij[0]])
        if F.any():
            Fb = blur(F, halo * 0.8 * ss)
            t = 0.06 + 0.22 * noise2d(h, w, 30 * ss, 2, int(r.integers(1 << 30)))
            R = R * (1 - smoothstep(t - 0.03, t + 0.03, Fb))
        return self.wash(('mask', sl, R), colour, strength, shift=(0, 0), warp=1.2, gaps=0.0, soft=1.6, edge=edge,
                         gran=0.2, streak=streak, angle=90.0 if angle is None else angle, var=0.12, dry=dry, card=c)

    def spatter(self, colour, n=10, box=None, size=(0.8, 2.8), strength=1.0, card=None):
        """flicked droplets of paint, each with a darker dried rim"""
        c = self._c(card)
        r = np.random.default_rng(int(c.rng.integers(1 << 30)))
        x0, y0, x1, y1 = box or (0, 0, c.w, c.h)
        polys = [PenWash.oval(r.uniform(x0, x1), r.uniform(y0, y1), rr, rr * r.uniform(0.8, 1.15), n=18, wob=0.1, seed=int(r.integers(999)))
                 for rr in r.uniform(*size, n)]
        sl, m = self._poly(c, polys, pad=6)
        if sl is None: return
        self.wash(('mask', sl, m), colour, strength, shift=(0, 0), warp=0.2, gaps=0, soft=0.6, edge=0.7, gran=0.2, streak=0, card=c)

    # ------------------------------------------------------------------ opaque white gouache (last)
    def _cover(self, c, sl, a, colour):
        if c.cover_a is None:
            c.cover_a = np.zeros((c.Hi, c.Wi), np.float32); c.cover_rgb = np.zeros((c.Hi, c.Wi, 3), np.float32)
        col = hexc(colour)
        ca, cr = c.cover_a[sl], c.cover_rgb[sl]
        cr[:] = cr * (1 - a[..., None]) + col * a[..., None]
        ca[:] = 1 - (1 - ca) * (1 - a)

    def highlight(self, pts, width=3.0, alpha=0.9, colour='#fbfaf3', card=None):
        """a stroke of opaque white gouache (glints, a shine on a loaf or a nose)"""
        c = self._c(card)
        s = SimpleNamespace(P=np.asarray(pts, np.float32), closed=False, smooth=True, corners=False, wobble=0.6,
                            over=(0, 1), width=width, double=0, flick=0.8, seed=int(c.rng.integers(1 << 30)))
        sl, cov = self._raster(c, self._paths(s))
        if sl is None: return
        a = cov * alpha * (0.7 + 0.3 * smoothstep(0.3, 0.6, c.tooth[sl]))
        self._cover(c, sl, a, colour)

    def glint(self, x, y, r=2.2, alpha=0.95, colour='#fdfcf6', card=None):
        """a dab of white gouache"""
        c = self._c(card)
        sl, m = self._poly(c, [PenWash.oval(x, y, r, r * 0.9, n=16, wob=0.12, seed=int(c.rng.integers(999)))], pad=4)
        if sl is None: return
        self._cover(c, sl, m * alpha, colour)

    # ================================================================== tools on the table
    def pen(self, x, y, angle, length=430.0, r=10.5, cap=True):
        """a fineliner lying on the table, tip at (x, y), its body running toward `angle` degrees"""
        k = r / 10.5
        segs = [(0, 5 * k, 0.9 * k, 1.2 * k, 'tip'), (5 * k, 18 * k, 1.5 * k, 2.3 * k, 'metal'),
                (18 * k, 46 * k, 2.6 * k, 0.80 * r, 'grey'), (46 * k, 53 * k, 0.92 * r, 0.92 * r, 'gloss'),
                (53 * k, length * 0.70, r * 0.95, r * 0.95, 'matte'),
                (length * 0.70, length * 0.70 + 4 * k, r * 0.98, r * 0.98, 'metal')]
        if cap:
            segs.append((length * 0.70 + 4 * k, length, r * 1.07, r * 1.07, 'gloss'))
        self.tools.append(dict(kind='pen', x=x, y=y, angle=angle, L=length, r=r, segs=segs,
                               clip=(length * 0.77, length * 0.97) if cap else None, label=(70 * k, '0.3', k)))

    def water_brush(self, x, y, angle, length=320.0, r=12.0, stain='teal', cap=None):
        """a water brush lying on the table: nylon tip at (x, y) stained with a little paint, ribbed grip, a clear
        barrel of water with a bubble; cap=(x, y, angle) also lays its clear cap on the table"""
        k = r / 12.0
        segs = [(0, 36 * k, 0.0, 0.55 * r, 'bristle'), (36 * k, 46 * k, 0.6 * r, 0.66 * r, 'white'),
                (46 * k, 112 * k, 0.78 * r, 0.80 * r, 'rib'), (112 * k, 120 * k, 0.86 * r, 0.86 * r, 'white'),
                (120 * k, length, r, r, 'water')]
        self.tools.append(dict(kind='brush', x=x, y=y, angle=angle, L=length, r=r, segs=segs, stain=stain,
                               tipL=36 * k, bubble=(length * 0.80, length * 0.96)))
        if cap is not None:
            cx, cy, ca = cap
            self.tools.append(dict(kind='cap', x=cx, y=cy, angle=ca, L=74.0 * k, r=r * 0.92,
                                   segs=[(0, 74 * k, r * 0.92, r * 0.92, 'clear')]))

    def _profile(self, t):
        """radius and material index along the axis at 0.25 px steps (rounded ends)"""
        L = t['L']
        s = np.arange(0, L + 0.25, 0.25, dtype=np.float32)
        rad = np.zeros_like(s); mat = np.zeros(len(s), np.int32)
        names = []
        for (s0, s1, r0, r1, m) in t['segs']:
            if m not in names: names.append(m)
            k = (s >= s0) & (s <= s1)
            rad[k] = r0 + (r1 - r0) * (s[k] - s0) / max(1e-3, s1 - s0)
            mat[k] = names.index(m)
        if t['kind'] == 'brush':
            tl = t['tipL']
            k = s <= tl
            rad[k] = 0.55 * t['r'] * np.clip(s[k] / tl, 0, 1) ** 0.75 * (1 - 0.15 * np.clip(s[k] / tl, 0, 1) ** 4)
        e = min(5.0, t['r'] * 0.5)
        tail = s > L - e
        rad[tail] *= np.sqrt(np.clip(1 - ((s[tail] - (L - e)) / e) ** 2, 0, 1))
        if t['kind'] == 'cap':
            head = s < 3
            rad[head] *= np.sqrt(np.clip(1 - ((3 - s[head]) / 3) ** 2, 0.3, 1))
        return s, rad, mat, names

    def _lay_tool(self, I, t):
        H, W = self.H, self.W
        a = np.radians(t['angle']); ax, ay = np.cos(a), np.sin(a)
        nx, ny = -ay, ax
        L, R = t['L'], t['r'] * 1.1
        x0, y0 = t['x'], t['y']
        pts = np.array([(x0, y0), (x0 + ax * L, y0 + ay * L)])
        pad = R + 30
        bx0, by0 = int(max(0, pts[:, 0].min() - pad)), int(max(0, pts[:, 1].min() - pad))
        bx1, by1 = int(min(W, pts[:, 0].max() + pad)), int(min(H, pts[:, 1].max() + pad))
        if bx1 <= bx0 or by1 <= by0: return
        YY, XX = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
        px, py = XX + 0.5 - x0, YY + 0.5 - y0
        s = px * ax + py * ay
        tt = px * nx + py * ny
        sp, rad, mat, names = self._profile(t)
        si = np.clip((s / 0.25).astype(np.int32), 0, len(sp) - 1)
        inside_s = (s >= 0) & (s <= L)
        rr = np.where(inside_s, rad[si], 0.0)
        cov = np.clip(rr - np.abs(tt) + 0.5, 0, 1) * inside_s
        # cast shadow on what is below (lifted by its radius, light from the upper left), plus contact shadow
        dx, dy = self.ld * t['r'] * 0.95
        clear = np.isin(mat[si], [names.index(m) for m in names if m in ('water', 'clear')]) if any(m in ('water', 'clear') for m in names) else np.zeros_like(cov, bool)
        dens = np.where(clear, 0.62, 1.0) * cov
        sh = blur(_move(dens, dx, dy), 0.28 * t['r'] + 1.5) * 0.42 + blur(_move(cov * (np.abs(tt) < rr * 0.5), 1, 1.5), 1.6) * 0.30
        if clear.any():
            caus = blur(_move(clear * cov * (np.abs(tt) < rr * 0.22), dx * 1.1, dy * 1.1), 1.4)
            sh = sh - 0.10 * caus
        reg = I[by0:by1, bx0:bx1]
        reg *= (1 - np.clip(sh, -0.3, 0.9)[..., None] * (1 - SHADOW))
        # shading of the cylinder
        u = np.clip(tt / np.maximum(rr, 1e-3), -1, 1)
        nz = np.sqrt(np.clip(1 - u * u, 0, 1))
        Lv = np.array([-0.55, -0.83, 1.15], np.float32); Lv /= np.linalg.norm(Lv)
        Nx, Ny = nx * u, ny * u
        lam = np.clip(Nx * Lv[0] + Ny * Lv[1] + nz * Lv[2], 0, 1)
        Hv = Lv + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        ndh = np.clip(Nx * Hv[0] + Ny * Hv[1] + nz * Hv[2], 0, 1)
        out = np.zeros(cov.shape + (3,), np.float32)
        m_here = mat[si]
        under = reg.copy()
        for k, m in enumerate(names):
            sel = (m_here == k) & (cov > 0)
            if not sel.any(): continue
            uu, lm, sp_, nzz = u[sel], lam[sel], ndh[sel], nz[sel]
            if m in ('matte', 'gloss', 'tip', 'grey', 'white', 'rib', 'bristle'):
                alb, amb, dif, ks, shin = {'matte': (0.075, 0.35, 0.65, 0.16, 9), 'gloss': (0.05, 0.3, 0.7, 0.75, 60),
                                           'tip': (0.06, 0.4, 0.6, 0.2, 10), 'grey': (0.50, 0.35, 0.65, 0.45, 35),
                                           'white': (0.80, 0.45, 0.55, 0.35, 25), 'rib': (0.16, 0.4, 0.6, 0.18, 12),
                                           'bristle': (0.07, 0.45, 0.55, 0.25, 14)}[m]
                cval = alb * (amb + dif * lm)
                if m == 'rib':
                    cval = cval * (0.78 + 0.22 * np.cos(2 * np.pi * s[sel] / (3.2 * t['r'] / 12.0)))
                if m == 'bristle':
                    kk = t['r'] / 12.0
                    cval = cval * (0.8 + 0.4 * (np.sin(tt[sel] * 2.7 / kk + np.sin(s[sel] * 0.07 / kk) * 3) * 0.5 + 0.5))
                col = np.stack([cval] * 3, -1) + (ks * sp_ ** shin)[..., None]
                if m == 'grey': col *= np.array([0.98, 1.0, 1.03], np.float32)
                if m == 'bristle' and t.get('stain'):
                    st = hexc(PAINTS.get(t['stain'], t['stain']))
                    k_ = np.clip(1 - s[sel] / (0.36 * t['tipL']), 0, 1)[..., None] * 0.85
                    col = col * (1 - k_) + (st * (0.35 + 0.5 * lm[..., None])) * k_
            elif m == 'metal':
                env = 0.42 + 0.5 * np.exp(-((uu + 0.42) / 0.22) ** 2) - 0.2 * np.exp(-((uu - 0.35) / 0.3) ** 2)
                col = np.stack([env * 0.98, env, env * 1.03], -1) + (0.5 * sp_ ** 50)[..., None]
            else:   # clear plastic / water: refract what is under it
                kref = 7.0 if m == 'water' else 3.0
                ox = nx * (uu ** 3) * kref; oy = ny * (uu ** 3) * kref
                ys, xs = np.nonzero(sel)
                fx = np.clip(xs - ox, 0, reg.shape[1] - 1); fy = np.clip(ys - oy, 0, reg.shape[0] - 1)
                und = _bilinear(under, fx, fy)
                tint = np.array([0.90, 0.95, 0.98] if m == 'water' else [0.95, 0.97, 0.985], np.float32)
                col = und * tint * (0.80 + 0.14 * nzz)[..., None] + 0.08          # slightly milky plastic
                col = col * (1 - 0.55 * ((1 - nzz) ** 3))[..., None]
                col += (0.55 * np.exp(-((uu + 0.52) / 0.08) ** 2) + 0.16 * np.exp(-((uu - 0.62) / 0.1) ** 2))[..., None]
                if m == 'water' and t.get('bubble'):
                    b0, b1 = t['bubble']
                    sb = s[sel]
                    inb = (sb > b0) & (sb < b1) & (uu > -0.85) & (uu < -0.05)
                    edgeb = np.exp(-((sb - b0) / 1.6) ** 2) * (uu > -0.85) * (uu < -0.05)
                    col = col + (0.10 * inb)[..., None] - (0.18 * edgeb)[..., None]
                if m == 'clear':
                    ring = np.exp(-((s[sel] - 4) / 1.5) ** 2)
                    col = col * (1 - 0.25 * ring)[..., None]
            out[sel] = col
        if t.get('label'):
            s0, txt, kk = t['label']
            self._ax_neg = ax < 0
            self._print_label(out, cov, s / kk, tt / kk, s0 / kk, txt, rr / kk)
        a_ = cov[..., None]
        reg[:] = reg * (1 - a_) + out * a_
        if t.get('clip'):
            c0, c1 = t['clip']
            cw = 2.6 * t['r'] / 10.5
            kk = t['r'] / 10.5
            cc = np.clip(cw - np.abs(tt + 0.5 * kk) + 0.5, 0, 1) * (s > c0) * (s < c1)
            cc *= np.clip((c1 + 2 - s) / 3, 0, 1)
            shc = blur(_move(cc, dx * 0.25, dy * 0.25), 0.8 * kk) * 0.5
            reg *= (1 - shc[..., None] * (1 - SHADOW))
            v = 0.12 + 0.55 * np.exp(-((tt + 1.6 * kk) / kk) ** 2) + 0.1 * np.exp(-((s - c1 + 4 * kk) / (3 * kk)) ** 2)
            reg[:] = reg * (1 - cc[..., None]) + np.stack([v, v, v * 1.02], -1) * cc[..., None]

    def _print_label(self, out, cov, s, tt, s0, txt, rr):
        """small light-grey print on the barrel (the line width), following the cylinder"""
        f = load_font('sans_bold', 22)
        im = Image.new('L', (90, 30), 0)
        ImageDraw.Draw(im).text((2, 2), txt, font=f, fill=255)
        g = np.asarray(im, np.float32) / 255
        flip = getattr(self, '_ax_neg', False)
        u = (s - s0) if not flip else (s0 + 60 - s)
        v = (tt * 1.25 + 14) if not flip else (-tt * 1.25 + 14)
        ok = (u >= 0) & (u < 89) & (v >= 0) & (v < 29) & (cov > 0)
        if not ok.any(): return
        val = g[np.clip(v.astype(int), 0, 29), np.clip(u.astype(int), 0, 89)] * ok
        val = val * np.clip(1 - np.abs(tt / np.maximum(rr, 1e-3)) ** 2, 0, 1)
        out[:] = out * (1 - 0.65 * val[..., None]) + 0.62 * 0.65 * val[..., None]

    # ================================================================== compose the photo
    def _card_rgba(self, c):
        ss = self.ss
        rgb = c.base * np.exp(-c.D)
        if c.wet.any():
            wb = blur(c.wet, 10 * ss)
            gy, gx = np.gradient(wb)
            rgb *= (1 + np.clip((0.55 * gx + 0.83 * gy) * ss * 2.2, -0.035, 0.035))[..., None]
        if c.cover_a is not None:
            a = c.cover_a[..., None]
            rgb = rgb * (1 - a) + c.cover_rgb * a * c.base / hexc(PAPER)
        A = c.alpha[..., None]
        rgba = np.concatenate([rgb * A, A], -1)
        h1, w1 = c.Hi // ss, c.Wi // ss
        rgba = rgba[:h1 * ss, :w1 * ss].reshape(h1, ss, w1, ss, 4).mean((1, 3))
        return rgba

    def _lay_card(self, I, c):
        H, W = self.H, self.W
        rgba = self._card_rgba(c)
        th = np.radians(c.rot); cs, sn = np.cos(th), np.sin(th)
        hw, hh = c.w / 2, c.h / 2
        corners = np.array([[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]])
        P = np.stack([c.cx + corners[:, 0] * cs - corners[:, 1] * sn, c.cy + corners[:, 0] * sn + corners[:, 1] * cs], 1)
        pad = 28
        bx0, by0 = int(max(0, P[:, 0].min() - pad)), int(max(0, P[:, 1].min() - pad))
        bx1, by1 = int(min(W, P[:, 0].max() + pad)), int(min(H, P[:, 1].max() + pad))
        if bx1 <= bx0 or by1 <= by0: return
        YY, XX = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
        dx, dy = XX + 0.5 - c.cx, YY + 0.5 - c.cy
        u = cs * dx + sn * dy + hw
        v = -sn * dx + cs * dy + hh
        smp = _bilinear(rgba, u - 0.5, v - 0.5)
        a = smp[..., 3]
        reg = I[by0:by1, bx0:bx1]
        sh = blur(_move(a, 6, 8), 7.0) * 0.30 + blur(_move(a, 1.2, 1.8), 1.3) * 0.36
        reg *= (1 - np.clip(sh, 0, 0.9)[..., None] * (1 - SHADOW))
        reg[:] = reg * (1 - a[..., None]) + smp[..., :3]
        gy, gx = np.gradient(a)
        facing = -(gx * -self.ld[0] + gy * -self.ld[1])        # outward normal . (toward the light)
        reg *= (1 + 0.10 * np.clip(facing, 0, 1) - 0.16 * np.clip(-facing, 0, 1))[..., None]

    def render(self):
        I = self.surface.copy()
        for c in self.cards:
            if c.shown: self._lay_card(I, c)
        for t in self.tools: self._lay_tool(I, t)
        return I

    def composite(self):
        I = self.render() * self._light[..., None] * self.warm
        I = I + self._grain[..., None] * 0.010
        return Image.fromarray((np.clip(I, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        if not self.keep_stages: return
        im = self.composite()
        if self.stages_dir:
            os.makedirs(self.stages_dir, exist_ok=True)
            im.save(f'{self.stages_dir}/{self._n_stages:02d}_{name}.png', compress_level=1)
        else:
            b = io.BytesIO(); im.save(b, 'PNG', compress_level=1)
            self.stages.append((name, b.getvalue()))
        self._n_stages += 1

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, b) in enumerate(self.stages):
                with open(f'{sd}/{i:02d}_{name}.png', 'wb') as f: f.write(b)
            img.save(f'{sd}/{self._n_stages:02d}_final.png', compress_level=1)
        return img
