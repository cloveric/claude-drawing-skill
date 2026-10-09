"""bluebook — 蓝调绘本 / Blue Picture Book: a soft-blue, limited-palette modern picture-book page (numpy + Pillow only).

The look of a contemporary children's picture book drawn by hand and printed: a mostly blue world (powder blue,
cornflower, a deep teal-blue) on white paper, a loose black ink line that is scratchy, broken and dry, flat-ish
colour laid with dry crayon / pastel / gouache so the tooth of the paper shows through, chalky white marks over the
blue, speckle and spatter, a few small accents (coral, a flesh-pink cheek, a touch of mustard) and charming round
characters. Nothing here is a filter on flat shapes: every mark is laid by a modelled tool on a modelled paper, in
the order an illustrator works (colour blocks, ink line, dark scribbled masses, accents, chalk, weather, print).

Physical model
  paper       Cartridge / pastel paper. Its tooth is a height field (1 px grain, 2-5 px bumps and a softer 9 px
              undulation) histogram-equalised to a uniform 0..1, so "the tool reaches the tooth where tooth >
              1 - contact" turns a contact pressure straight into a coverage fraction. A dry tool dragged across
              the sheet rides from peak to peak, so the bare pits it skips are drawn out into short streaks along
              the stroke: the tooth is pre-averaged along 8 directions (`TD`) and every mark reads the version that
              matches its own direction. The bare paper is a warm white with a faint tooth.
  ink line    A brush / ink-pencil line. The drawn path is re-sampled and pushed sideways by a slow hand wobble and
              a small tremor. Pressure lands fast and lifts slower (taper), and swells and thins along the way
              (thick-thin). The tip is a bundle of hairs that carry different loads, so across the line there are
              lanes; the load runs out along the stroke (`dry`), and where contact x load falls below the tooth the
              ink breaks into dry white streaks that run along the stroke. The edge of the line wanders with the
              tooth, so it is never vector-clean. Closed shapes are not closed: `outline()` draws a contour as one
              to three strokes that stop short or run past the join on their tangent, and now and then goes over
              part of a stroke again a couple of px off (a sketchy double line). Every pixel of a mark knows
              its arc length and its offset across the mark (segment indices are rasterised by Pillow, then
              projected exactly), so taper, swell, lanes and drying are per pixel.
  scribble    Dark masses (bush shadows, trunks, boots, hair shadow) are quick back-and-forth scribbles: zigzag
              polylines inside the mask along one direction, sharp V turns that over- or under-shoot the outline,
              a wrist-sized patch at a time, the same dry ink model, so white tooth and gaps between passes stay
              in the black. `hatch()` lays separate quick parallel flicks; `blades()` draws tapered leaf / grass
              blades.
  colour      Dry media (crayon, pastel, dry gouache) laid AFTER a rough idea of the shape, not inside the line:
              the region slips 1.5-3.5 px one way (misregistration), its edge is re-found on a blurred copy with a
              threshold that wanders, contact pressure is mottled at low frequency, the area is laid in parallel
              stroke lanes of slightly different pressure, and near the edge the pressure falls so the border
              breaks up dry. Coverage comes from the directional tooth, so white specks of paper show through and
              streak along the stroke. Wax / pastel is semi-opaque: new = lerp(under, colour * under^0.55,
              coverage) -- over white it is the colour, over the ink it stays dark, a second blue over a blue goes
              deeper. `block()` is the big background colour field: a rough-sided block that does not reach the
              edge of the page, whose borders are brushed along their own direction and dragged dry.
  chalk       White pastel / chalk / white gouache is opaque and dry: it is laid only on the tooth peaks, with
              long streaks, over the blue (clouds, fur on the silhouette, ripples, highlights, snow-like specks).
  spatter     Flicked paint: drops with a power-law size distribution, slightly elongated, with satellite
              droplets (`spatter()`); `speckle()` is finer dust; `rain()` is short dry strokes; `splash()` is the
              little crown where a drop hits; `ripples()` are broken rings on a puddle.
  characters  Round-headed picture-book people and animals: `head()` an open contour with optional ears,
              `eyes()` ink dots with a white glint, `smile()`, `blush()` a stippled cheek of pink dots, `freckles()`,
              `fluff()` scribbly fur -- the silhouette drawn as short scalloped ink tufts, or white chalk tufts that
              cross the edge into the background, plus little curls inside.
  print       The page is reproduced in a book (`printed()`): a slight print softness, blacks that lift to a deep
              ink, a fine paper speck, an optional centre gutter (the fold of a spread: a soft shadow, a fine crease
              and a hairline of light), and tiny page numbers (`folio()`).

API (canvas px; angles in degrees, 0 = to the right, 90 = down; colours are names in COLOURS or '#rrggbb')
  paper     BlueBook(W, H, seed, keep_stages, stages_dir); paper(tone, tooth, drag)
  shapes    ellipse(cx, cy, rx, ry, rot), poly(pts, smooth), blob(cx, cy, rx, ry, rough, seed, rot), band(path, w0, w1),
            cloud(cx, cy, w, h, bumps, seed), rect(x0, y0, x1, y1, rough, corner, seed) -> canvas-size float masks
  colour    block(mask | box, colour, ...); fill(mask, colour, pressure, angle, slip, loose, edge, dry_edge, medium,
            avoid, halo, passes, clip); crayon(paths, colour, width, pressure)
  ink       ink(path, width, dry, taper, wobble, ...); outline(pts, width, closed, open_, overshoot, twice);
            scribble(mask, width, spacing, angle, reach, dry); hatch(mask, angle, spacing, length, width);
            blades(x0, x1, y, n, height, lean, width); dot(x, y, r)
  white     chalk(mask | paths, width, pressure, angle); ripples(cx, cy, rx, ry, rings, medium)
  weather   rain(region, n, angle, length, colour, medium, avoid); splash(x, y, size, colour, medium);
            spatter(region, colour, n, size, medium); speckle(region, colour, n, size)
  figures   head(cx, cy, rx, ry, ears); eyes(pts, r, look); smile(x, y, w, depth); blush(cx, cy, r); freckles(cx, cy, n);
            fluff(mask, medium, every, length, curls, avoid); flower(x, y, r, colour)
  finish    printed(amount, gutter); folio(x, y, text, size); render(); composite(); stage(name); save(path, stages_dir)

    import sys; sys.path.insert(0, 'lib')
    from bluebook import BlueBook
    b = BlueBook(1920, 1080, seed=4)
    b.paper()
    bear = b.ellipse(1200, 620, 220, 240)
    b.block((60, 50, 1860, 900), 'powder', avoid=bear)             # the blue field, painted round the bear
    b.stage('blue')
    b.fluff(bear, 'ink')                                           # scalloped fur line
    b.eyes([(1150, 560), (1250, 556)], r=7)
    b.blush(1120, 610, 22); b.blush(1290, 604, 22)
    b.fluff(bear, 'chalk')                                         # white tufts across the edge
    b.rain((60, 50, 1860, 900), n=400, avoid=bear)
    b.printed(gutter=960); b.save('bluebook.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, noise2d, smoothstep, spline, polygon_mask, blob_pts, load_font, text_mask
from core import shift as _shift


COLOURS = {
    'paper': '#fbfaf5', 'chalk': '#fbfbf6', 'ink': '#17181e',
    'mist': '#d6e4f1', 'powder': '#b9d2ea', 'cornflower': '#8fb3dc', 'blue': '#5b8fcb', 'cobalt': '#3e6fb0',
    'deep': '#2f5c91', 'teal': '#2b5d72', 'navy': '#1d3450', 'slate': '#6f8fae',
    'coral': '#e8574a', 'tomato': '#d9483c', 'cheek': '#ee7f78', 'flesh': '#f7dfd3', 'freckle': '#9a5446',
    'mustard': '#e7b34c', 'butter': '#f2d488',
}
INK = COLOURS['ink']
NB = 8                                   # directions of the dragged tooth


def hexc(c):
    """'#rrggbb', a COLOURS name or an RGB triple -> float32 RGB 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = COLOURS.get(c, c).lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _closed_spline(P, per=8):
    P = np.asarray(P, np.float32)
    n = len(P)
    ext = np.vstack([P[-1:], P, P[:2]])
    out = []
    for i in range(1, n + 1):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(out[0])
    return np.array(out, np.float32)


def _resample(P, step):
    P = np.asarray(P, np.float32)
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(np.ceil(s[-1] / step)) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


def _equalise(t, bins=1024):
    hist, edges = np.histogram(t, bins)
    cdf = np.cumsum(hist).astype(np.float32); cdf /= cdf[-1]
    return np.interp(t, edges[1:], cdf).astype(np.float32)


class BlueBook:
    COLOURS = COLOURS

    def __init__(self, W=1920, H=1080, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32)
        self.C[:] = hexc('paper')
        self.K = np.zeros((H, W), np.float32)                # ink already on the page
        self.T = None
        self.TD = None
        self.print_amt, self.gutter_x = 0.0, None

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== paper
    def paper(self, tone='paper', tooth=1.0, drag=7):
        """cartridge paper: an equalised tooth (grain, bumps, undulation) and its 8 dragged versions"""
        H, W = self.H, self.W
        r = np.random.default_rng(self.seed + 101)
        z = lambda a: (a - a.mean()) / (a.std() + 1e-6)
        g1 = blur(r.random((H, W)).astype(np.float32), 0.7)
        g2 = noise2d(H, W, 2.6, 2, self.seed + 102)
        g3 = noise2d(H, W, 9.0, 2, self.seed + 103)
        T = _equalise(0.52 * z(g1) + 0.36 * z(g2) + 0.22 * z(g3))
        T = T * tooth + 0.5 * (1 - tooth)
        self.T = T
        TD = np.empty((NB, H, W), np.float32)
        ks = np.arange(-drag, drag + 1)
        wk = 1.0 - np.abs(ks) / (drag + 1.0)
        for b in range(NB):
            a = np.pi * b / NB
            acc = np.zeros((H, W), np.float32)
            for k, w in zip(ks, wk):
                acc += w * np.roll(T, (int(round(k * np.sin(a))), int(round(k * np.cos(a)))), axis=(0, 1))
            TD[b] = _equalise(0.32 * T + 0.68 * acc / wk.sum())
        self.TD = TD
        mot = noise2d(H, W, 260, 2, self.seed + 104) - 0.5
        self.C[:] = hexc(tone) * (1 - 0.012 * (T[..., None] - 0.5) + 0.008 * mot[..., None])

    def _need(self):
        if self.T is None: self.paper()

    def _bin(self, ang_rad):
        return (np.round((np.mod(ang_rad, np.pi)) / np.pi * NB).astype(np.int32)) % NB

    def _tooth_region(self, sl, angle):
        """dragged tooth for a region: angle (deg) a number or a canvas-size field"""
        if np.ndim(angle) == 0:
            return self.TD[int(self._bin(np.deg2rad(angle)))][sl]
        bins = self._bin(np.deg2rad(angle[sl]))
        sub = self.TD[:, sl[0], sl[1]]
        return np.take_along_axis(sub, bins[None], 0)[0]

    # ================================================================== shapes (canvas-size masks)
    def _grid(self, sl):
        ys = np.arange(sl[0].start, sl[0].stop, dtype=np.float32)[:, None]
        xs = np.arange(sl[1].start, sl[1].stop, dtype=np.float32)[None, :]
        return xs, ys

    def _clip_box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0):
        ry = rx if ry is None else ry
        R = max(rx, ry) + 3
        out = np.zeros((self.H, self.W), np.float32)
        sl = self._clip_box(cx - R, cy - R, cx + R + 1, cy + R + 1)
        if sl is None: return out
        X, Y = self._grid(sl)
        X, Y = X - cx, Y - cy
        if rot:
            a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
            X, Y = X * c + Y * s, -X * s + Y * c
        d = np.sqrt((X / rx) ** 2 + (Y / ry) ** 2)
        e = 1.0 / max(2.0, min(rx, ry))
        out[sl] = smoothstep(1 + e, 1 - e, d)
        return out

    def poly(self, pts, smooth=True, per=8):
        pts = np.asarray(pts, np.float32)
        if smooth and len(pts) > 2: pts = _closed_spline(pts, per)
        return polygon_mask(self.H, self.W, pts, ss=2)

    def blob(self, cx, cy, rx, ry=None, rough=0.08, seed=0, rot=0.0):
        return self.poly(blob_pts(cx, cy, rx, rx if ry is None else ry, rough, 120, seed, np.deg2rad(rot)), smooth=False)

    @staticmethod
    def tube(path, w0, w1=None, per=8):
        """outline polygon of a thick path (width w0 -> w1), rounded ends"""
        Q = spline(np.asarray(path, np.float32), per) if len(path) > 2 else np.asarray(path, np.float32)
        w1 = w0 if w1 is None else w1
        d = np.gradient(Q, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-d[:, 1], d[:, 0]], 1)
        hw = np.linspace(w0, w1, len(Q))[:, None] / 2
        L, R = Q + nrm * hw, Q - nrm * hw
        a0 = np.arctan2(nrm[0, 1], nrm[0, 0]); a1 = np.arctan2(nrm[-1, 1], nrm[-1, 0])
        cap1 = [Q[-1] + hw[-1] * np.array([np.cos(a1 - t), np.sin(a1 - t)]) for t in np.linspace(0, np.pi, 9)[1:-1]]
        cap0 = [Q[0] + hw[0] * np.array([np.cos(a0 + np.pi - t), np.sin(a0 + np.pi - t)]) for t in np.linspace(0, np.pi, 9)[1:-1]]
        return np.vstack([L, np.array(cap1).reshape(-1, 2), R[::-1], np.array(cap0).reshape(-1, 2)]).astype(np.float32)

    def band(self, path, w0, w1=None):
        return self.poly(self.tube(path, w0, w1), smooth=False)

    def cloud(self, cx, cy, w, h, bumps=5, seed=0):
        """a cumulus outline: a flat-ish bottom and a row of rounded bumps on top"""
        r = np.random.default_rng(seed)
        m = self.ellipse(cx, cy + h * 0.18, w * 0.5, h * 0.32)
        xs = np.linspace(cx - w * 0.36, cx + w * 0.36, bumps)
        for i, x in enumerate(xs):
            k = 1 - abs(i - (bumps - 1) / 2) / ((bumps - 1) / 2 + 1e-6)
            rr = h * (0.26 + 0.24 * k) * r.uniform(0.85, 1.15)
            m = np.maximum(m, self.ellipse(x, cy + h * 0.12 - rr * 0.55, rr, rr * 0.92))
        return m

    def rect(self, x0, y0, x1, y1, rough=8.0, corner=24.0, seed=0):
        """a hand-cut / brushed rectangle: wobbly sides, softly rounded corners"""
        r = np.random.default_rng(seed)
        pts = []
        sides = [((x0 + corner, y0), (x1 - corner, y0)), ((x1, y0 + corner), (x1, y1 - corner)),
                 ((x1 - corner, y1), (x0 + corner, y1)), ((x0, y1 - corner), (x0, y0 + corner))]
        for (a, b) in sides:
            a, b = np.array(a, np.float32), np.array(b, np.float32)
            L = float(np.hypot(*(b - a)))
            n = max(8, int(L / 6))
            t = np.linspace(0, 1, n)[:, None]
            d = (b - a) / max(L, 1e-3); nrm = np.array([d[1], -d[0]], np.float32)       # outward
            off = fbm1d(n, max(4, n / 7), 4, int(r.integers(1 << 30)))[:, None] * rough
            pts.append(a + (b - a) * t + nrm * off)
        return polygon_mask(self.H, self.W, _closed_spline(np.vstack(pts)[::3], 6), ss=2)

    def _bbox(self, m, pad=0, thr=0.004):
        rows = np.flatnonzero(m.max(1) > thr)
        if not len(rows): return None
        cols = np.flatnonzero(m.max(0) > thr)
        pad = int(np.ceil(pad))
        return (slice(max(0, rows[0] - pad), min(self.H, rows[-1] + 1 + pad)),
                slice(max(0, cols[0] - pad), min(self.W, cols[-1] + 1 + pad)))

    # ================================================================== laying media
    def _lay(self, idx, dep, colour, medium, over_ink=0.1):
        """put pigment on the page at idx (a region slice or (ys, xs)) with coverage dep. Ink is remembered in K;
        colour laid later barely takes on it (over_ink), so the line stays on top as in the printed book."""
        if medium == 'ink':
            self.K[idx] = 1 - (1 - self.K[idx]) * (1 - dep)
        elif over_ink < 1:
            dep = dep * (1 - (1 - over_ink) * self.K[idx])
        C = self.C[idx]
        col = hexc(colour) if np.ndim(colour) <= 1 else colour
        if medium == 'crayon':
            tgt = col * np.clip(C, 0, 1) ** 0.55                    # semi-opaque wax / pastel
        else:
            tgt = col if np.ndim(col) > 1 else np.broadcast_to(col, C.shape)   # ink, chalk, gouache: cover
        self.C[idx] = C + (tgt - C) * dep[..., None]

    def _hand(self, path, wobble=1.0, smooth=True, closed=False, r=None, step=2.0):
        """the drawn path: smoothed, re-sampled every `step` px, pushed sideways by hand wobble and tremor"""
        r = r if r is not None else self._r()
        P = np.asarray(path, np.float32).reshape(-1, 2)
        if len(P) < 2: return P
        if smooth and len(P) > 2:
            P = _closed_spline(P) if closed else spline(P, 8)
        elif closed:
            P = np.vstack([P, P[:1]])
        Q = _resample(P, step)
        n = len(Q)
        if wobble and n > 3:
            d = np.gradient(Q, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
            nrm = np.stack([-d[:, 1], d[:, 0]], 1)
            w = fbm1d(n, 30, 3, int(r.integers(1 << 30))) * 1.4 * wobble \
                + fbm1d(n, 3.5, 2, int(r.integers(1 << 30))) * 0.32 * wobble
            Q = Q + nrm * w[:, None]
        return Q

    def _footprint(self, Q, reach):
        """pixels within `reach` of polyline Q, with the index of the segment they belong to (Pillow rasterises
        the segment ids into an int image; round caps at both ends)"""
        x0 = max(0, int(np.floor(Q[:, 0].min() - reach - 2))); x1 = min(self.W, int(np.ceil(Q[:, 0].max() + reach + 3)))
        y0 = max(0, int(np.floor(Q[:, 1].min() - reach - 2))); y1 = min(self.H, int(np.ceil(Q[:, 1].max() + reach + 3)))
        if x1 <= x0 or y1 <= y0: return None
        im = Image.new('I', (x1 - x0, y1 - y0), 0)
        d = ImageDraw.Draw(im)
        q = (Q - [x0 - 0.5, y0 - 0.5]).tolist()
        wpx = max(1, int(np.ceil(2 * reach + 1)))
        n = len(q)
        rr = reach + 0.5
        d.ellipse([q[0][0] - rr, q[0][1] - rr, q[0][0] + rr, q[0][1] + rr], fill=1)
        for k in range(n - 1):
            d.line([tuple(q[k]), tuple(q[k + 1])], fill=k + 1, width=wpx)
        d.ellipse([q[-1][0] - rr, q[-1][1] - rr, q[-1][0] + rr, q[-1][1] + rr], fill=n - 1)
        a = np.asarray(im, np.int32)
        yy, xx = np.nonzero(a)
        if not len(yy): return None
        return yy + y0, xx + x0, a[yy, xx] - 1

    def _mark(self, path, width, colour, medium='ink', pressure=1.0, dry=0.2, taper=(0.12, 0.3), wobble=1.0,
              smooth=True, closed=False, streak=0.45, rough=1.0, alpha=0.97, swell=0.18, clip=None, seed=None,
              Q=None, over_ink=0.1):
        """one mark of a dry tool along a path: thick-thin, tapered, bristle lanes, drying out, toothy edge"""
        self._need()
        r = self._r(seed)
        if Q is None: Q = self._hand(path, wobble, smooth, closed, r)
        if len(Q) < 2: return
        seg = Q[1:] - Q[:-1]
        sL = np.hypot(seg[:, 0], seg[:, 1]) + 1e-6
        cum = np.concatenate([[0], np.cumsum(sL)])
        L = float(cum[-1])
        if L < 1.0: return
        reach = width * 0.5 * (1 + abs(swell)) + 1.5 + rough * 0.6
        fp = self._footprint(Q, reach)
        if fp is None: return
        ys, xs, k = fp
        k = np.clip(k, 0, len(seg) - 1)
        dx, dy = seg[k, 0] / sL[k], seg[k, 1] / sL[k]
        rx, ry = xs - Q[k, 0], ys - Q[k, 1]
        u = np.clip(rx * dx + ry * dy, 0, sL[k])
        px, py = rx - u * dx, ry - u * dy
        dist = np.hypot(px, py)
        side = np.sign(-rx * dy + ry * dx)
        s01 = (cum[k] + u) / L
        prof = np.clip(np.minimum(s01 / max(taper[0], 1e-3), (1 - s01) / max(taper[1], 1e-3)), 0, 1) ** 0.6
        nn = max(4, int(L / 7))
        sw = np.interp(s01, np.linspace(0, 1, nn), fbm1d(nn, max(2.0, nn / 3), 2, int(r.integers(1 << 30))))
        hw = 0.5 * width * (0.2 + 0.8 * prof) * (1 + swell * sw)
        Td = self.TD[self._bin(np.arctan2(dy, dx)), ys, xs]
        e = dist - hw - rough * 0.9 * (Td - 0.5) * min(1.0, width / 3.0)
        body = smoothstep(0.7, -0.7, e)
        nbr = max(3, int(width / 1.6))
        tn = np.clip(side * dist / (hw + 1e-3), -1, 1)
        B = np.interp(tn, np.linspace(-1, 1, nbr), r.uniform(0.4, 1.0, nbr))
        load = 1.0 - dry * 1.35 * s01 ** 1.25 * r.uniform(0.8, 1.2)
        c = pressure * (0.55 + 0.45 * prof) * load * (1 - streak * (1 - B)) * (1 - 0.3 * streak * smoothstep(0.55, 1.0, np.abs(tn)))
        dep = body * smoothstep(-0.1, 0.1, Td - (1 - 1.12 * c)) * alpha
        if clip is not None: dep = dep * clip[ys, xs]
        keep = dep > 0.003
        if not keep.any(): return
        self._lay((ys[keep], xs[keep]), dep[keep], colour, medium, over_ink)

    # ================================================================== colour
    def fill(self, mask, colour, pressure=0.9, angle=None, slip=None, loose=3.0, edge=8.0, dry_edge=0.55,
             mottle=0.1, lanes=24.0, lane_var=0.08, passes=1, medium='crayon', alpha=1.0, avoid=None, halo=3.0,
             clip=None, tint=0.05, streak=0.45, over_ink=0.1, seed=None):
        """colour an area in dry media, loose against the line. Returns the region actually coloured.
        pressure: contact (0..1 = coverage fraction on the tooth; 0.95 leaves fine specks of paper); mottle /
        lanes / lane_var: how much the pigment density varies (blotches, parallel passes); streak: how much the
        bare specks are drawn out along the stroke; angle: stroke direction (deg, or a canvas-size
        field); slip: misregistration (dx, dy), None = random 1.5-3.5 px, 0 = none; loose: edge wander px;
        edge / dry_edge: width and strength of the dry-out at the border; lanes: stroke width of the parallel passes;
        medium: 'crayon' (semi-opaque) | 'gouache' | 'chalk' (opaque); avoid / halo: a mask to colour round"""
        self._need()
        r = self._r(seed)
        if slip is None:
            a = r.uniform(0, 2 * np.pi); mg = r.uniform(1.5, 3.5)
            slip = (np.cos(a) * mg, np.sin(a) * mg)
        elif np.ndim(slip) == 0:
            slip = (0.0, 0.0)
        pad = loose * 3 + edge + 8 + abs(slip[0]) + abs(slip[1])
        sl = self._bbox(mask, pad)
        if sl is None: return np.zeros((self.H, self.W), np.float32)
        m = mask[sl].astype(np.float32)
        if slip[0] or slip[1]: m = _shift(m, slip[0], slip[1])
        if avoid is not None:
            av = avoid[sl]
            if halo: av = smoothstep(0.08, 0.4, blur(av, halo * 0.6))
            m = m * (1 - av)
        h, w = m.shape
        if loose:
            mb = blur(m, max(0.8, loose * 0.5))
            wob = noise2d(h, w, max(14.0, loose * 9), 2, int(r.integers(1 << 30))) - 0.5
            R = smoothstep(0.40, 0.60, mb + wob * 0.55)
        else:
            R = m
        Pc = pressure + 0.04 * (noise2d(h, w, 40, 2, int(r.integers(1 << 30))) - 0.5)
        if dry_edge and edge:
            ed = blur(R, edge * 0.5)
            Pc = Pc * ((1 - dry_edge) + dry_edge * smoothstep(0.5, 0.92, ed))
        dens = 1 - mottle * 2 * np.abs(noise2d(h, w, 110, 3, int(r.integers(1 << 30))) - 0.5)
        ang = r.uniform(-40, 40) if angle is None else angle
        a0 = np.deg2rad(ang if np.ndim(ang) == 0 else float(np.median(ang[sl])))
        if lanes:
            X, Y = self._grid(sl)
            v = -X * np.sin(a0) + Y * np.cos(a0) + 7 * (noise2d(h, w, 70, 2, int(r.integers(1 << 30))) - 0.5) * 2
            v = v - v.min()
            nl = int(v.max() / lanes) + 3
            dens = dens * np.interp(v / lanes, np.arange(nl), 1 - lane_var * np.abs(r.normal(0, 1, nl)))
        Td = self._tooth_region(sl, ang)
        Tf = Td * streak + self.T[sl] * (1 - streak)
        dep = R * smoothstep(-0.06, 0.06, Tf - (1 - Pc))
        for i in range(1, passes):
            Td2 = self._tooth_region(sl, (ang if np.ndim(ang) == 0 else float(np.degrees(a0))) + r.choice([-1, 1]) * r.uniform(45, 75))
            d2 = R * smoothstep(-0.06, 0.06, Td2 - (1 - Pc * 0.85))
            dep = 1 - (1 - dep) * (1 - d2)
        dep = dep * np.clip(dens, 0, 1)
        dep = dep * alpha
        if clip is not None: dep = dep * clip[sl]
        col = hexc(colour)
        if tint:
            nt = noise2d(h, w, 60, 2, int(r.integers(1 << 30)))[..., None] - 0.5
            col = np.clip(col * (1 + tint * 2 * nt), 0, 1)
        else:
            col = np.broadcast_to(col, (h, w, 3))
        self._lay(sl, dep, col, medium, over_ink)
        out = np.zeros((self.H, self.W), np.float32)
        out[sl] = R
        return out

    def block(self, box, colour='powder', rough=9.0, corner=28.0, pressure=0.96, angle=-12.0, edge=16.0,
              dry_edge=0.7, streaks=90, avoid=None, halo=3.0, seed=None, **kw):
        """the big background colour field: a rough-sided block on white (box = (x0, y0, x1, y1) or a mask);
        its borders are brushed along their own direction and drag out dry"""
        r = self._r(seed)
        mask = self.rect(*box, rough=rough, corner=corner, seed=int(r.integers(1 << 30))) if np.ndim(box) == 1 else box
        mb = blur(mask, 16)
        gy, gx = np.gradient(mb)
        mag = np.hypot(gx, gy)
        along = np.degrees(np.arctan2(gx, -gy))                        # direction of the border
        wgt = smoothstep(0.004, 0.02, mag)
        field = np.where(wgt > 0.5, along, angle).astype(np.float32)
        R = self.fill(mask, colour, pressure, angle=field, slip=0, loose=rough * 0.45, edge=edge, dry_edge=dry_edge,
                      lanes=46, avoid=avoid, halo=halo, seed=int(r.integers(1 << 30)), **kw)
        # dry strokes dragged along the border, some running a little off the block (kept near the border)
        ys, xs = np.nonzero((mag > 0.012) & (mask > 0.15) & (mask < 0.85))
        near = smoothstep(0.02, 0.12, blur(mask, 6))
        if streaks and len(ys):
            for i in r.choice(len(ys), min(streaks, len(ys)), replace=False):
                x, y = float(xs[i]), float(ys[i])
                a = np.deg2rad(along[ys[i], xs[i]])
                nx, ny = -gx[ys[i], xs[i]] / (mag[ys[i], xs[i]] + 1e-6), -gy[ys[i], xs[i]] / (mag[ys[i], xs[i]] + 1e-6)
                off = r.uniform(-9, 3)
                Lh = r.uniform(25, 110)
                c0 = (x + nx * off, y + ny * off)
                p0 = (c0[0] - np.cos(a) * Lh, c0[1] - np.sin(a) * Lh)
                p1 = (c0[0] + np.cos(a) * Lh, c0[1] + np.sin(a) * Lh)
                if avoid is not None:
                    if avoid[int(np.clip(c0[1], 0, self.H - 1)), int(np.clip(c0[0], 0, self.W - 1))] > 0.3: continue
                self._mark([p0, c0, p1], r.uniform(8, 20), colour, 'crayon', pressure=r.uniform(0.7, 0.9),
                           dry=r.uniform(0.3, 0.7), taper=(0.2, 0.4), wobble=1.5, streak=0.7, rough=2.0, alpha=0.95,
                           clip=near if avoid is None else near * (1 - avoid))
        return R

    def crayon(self, paths, colour, width=8.0, pressure=0.8, dry=0.35, taper=(0.15, 0.35), wobble=1.0, streak=0.6,
               alpha=0.95, medium='crayon', clip=None, seed=None):
        """coloured dry strokes along paths (hair, blades, wet streaks, reflections)"""
        r = self._r(seed)
        for p in paths:
            self._mark(p, width * r.uniform(0.85, 1.15), colour, medium, pressure, dry * r.uniform(0.7, 1.3), taper,
                       wobble, streak=streak, rough=1.6, alpha=alpha, clip=clip, seed=int(r.integers(1 << 30)))

    # ================================================================== ink
    def ink(self, path, width=4.0, colour=INK, dry=0.2, taper=(0.12, 0.32), wobble=1.0, smooth=True, pressure=1.0,
            streak=0.45, rough=1.0, alpha=0.97, swell=0.18, overshoot=0.0, clip=None, seed=None):
        """one brush / ink-pencil stroke along a path"""
        r = self._r(seed)
        Q = self._hand(path, wobble, smooth, False, r)
        if overshoot and len(Q) > 2:
            d = Q[-1] - Q[-3]; d /= np.linalg.norm(d) + 1e-6
            Q = np.vstack([Q, Q[-1] + d * overshoot * 0.5, Q[-1] + d * overshoot])
        self._mark(None, width, colour, 'ink', pressure, dry, taper, wobble, streak=streak, rough=rough, alpha=alpha,
                   swell=swell, clip=clip, seed=int(r.integers(1 << 30)), Q=Q)

    def outline(self, pts, width=4.0, closed=True, open_=0.45, overshoot=(4, 12), strokes=(1, 3), colour=INK,
                dry=0.2, wobble=1.0, smooth=True, taper=(0.1, 0.3), alpha=0.97, twice=0.35, clip=None, seed=None):
        """a quick contour: closed shapes are drawn as 1-3 strokes that stop short (a gap) or run past the
        join and leave the curve on its tangent; open_ = chance of a gap; twice = chance that part of a stroke
        is gone over again a little off the first line (a sketchy double line)"""
        r = self._r(seed)
        P = np.asarray(pts, np.float32)
        if not closed:
            self.ink(P, width, colour, dry, taper, wobble, smooth, alpha=alpha, clip=clip, seed=int(r.integers(1 << 30)))
            return
        P = _closed_spline(P, 6) if smooth else np.vstack([P, P[:1]])
        P = _resample(P, 2.0)
        seg = np.hypot(*np.diff(P, axis=0).T)
        s = np.concatenate([[0], np.cumsum(seg)])
        Lp = float(s[-1])
        ns = int(r.integers(strokes[0], strokes[1] + 1))
        start = r.uniform(0, Lp)
        cuts = np.sort(r.uniform(0.2, 0.8, ns - 1)) * Lp if ns > 1 else np.array([])
        bounds = np.concatenate([[0], cuts, [Lp]]) + start

        def at(u):
            u = np.mod(u, Lp)
            return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1)
        for i in range(ns):
            a, b = bounds[i], bounds[i + 1]
            gap = r.random() < open_
            if gap: b -= r.uniform(5, 14)
            else: b += r.uniform(*overshoot) * 0.3
            a -= 0 if i == 0 else r.uniform(2, 6)
            Q = at(np.arange(a, b, 2.0))
            if len(Q) < 3: continue
            if not gap:
                d = Q[-1] - Q[-3]; d /= np.linalg.norm(d) + 1e-6
                e = r.uniform(*overshoot)
                Q = np.vstack([Q, Q[-1] + d * e * 0.5, Q[-1] + d * e])
            self.ink(Q, width, colour, dry, taper, wobble, smooth=False, alpha=alpha, clip=clip, seed=int(r.integers(1 << 30)))
            if r.random() < twice and len(Q) > 12:
                n = len(Q); a_ = int(r.uniform(0, 0.5) * n); b_ = min(n, a_ + int(r.uniform(0.25, 0.5) * n))
                d = np.gradient(Q[a_:b_], axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
                off = r.uniform(1.5, 3.2) * r.choice([-1, 1])
                Q2 = Q[a_:b_] + np.stack([-d[:, 1], d[:, 0]], 1) * off * np.sin(np.linspace(0, np.pi, b_ - a_))[:, None] ** 0.5
                self.ink(Q2, width * 0.6, colour, dry + 0.2, (0.3, 0.4), wobble, smooth=False, alpha=alpha * 0.9, clip=clip,
                         seed=int(r.integers(1 << 30)))

    def _runs(self, mask, angle, spacing, step=3.0, r=None):
        """rows across `angle`, each with the [u0, u1] runs where the row lies in the mask"""
        sl = self._bbox(mask, 2)
        if sl is None: return [], None
        a = np.deg2rad(angle)
        dv, nv = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
        cx, cy = (sl[1].start + sl[1].stop) / 2, (sl[0].start + sl[0].stop) / 2
        R = 0.5 * np.hypot(sl[1].stop - sl[1].start, sl[0].stop - sl[0].start) + 4
        vs = np.arange(-R, R, spacing) + r.uniform(0, spacing)
        vs = vs + r.normal(0, spacing * 0.18, len(vs))
        us = np.arange(-R, R, step)
        X = cx + dv[0] * us[None, :] + nv[0] * vs[:, None]
        Y = cy + dv[1] * us[None, :] + nv[1] * vs[:, None]
        ok = (X >= 0) & (X < self.W) & (Y >= 0) & (Y < self.H)
        ins = np.zeros(X.shape, bool)
        ins[ok] = mask[Y[ok].astype(int), X[ok].astype(int)] > 0.5
        rows = []
        for i in range(len(vs)):
            d = np.diff(np.concatenate([[0], ins[i].astype(np.int8), [0]]))
            st, en = np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1
            rows.append([[us[a_], us[b_], False] for a_, b_ in zip(st, en) if b_ > a_])
        return rows, (cx, cy, dv, nv, vs)

    def scribble(self, mask, width=5.0, spacing=4.5, angle=80.0, reach=900.0, overshoot=7.0, dry=0.45,
                 colour=INK, medium='ink', alpha=0.95, wobble=0.6, piece=260.0, clip=None, seed=None):
        """a dark mass scribbled back and forth: zigzag passes along `angle`, sharp turns past (or short of)
        the outline, one wrist-sized patch at a time"""
        r = self._r(seed)
        rows, geo = self._runs(mask, angle, spacing, r=r)
        if geo is None: return
        cx, cy, dv, nv, vs = geo
        # cut long runs into wrist-sized pieces
        for row in rows:
            out = []
            for a, b, _ in row:
                while b - a > piece * 1.3:
                    m = a + piece * r.uniform(0.6, 1.0)
                    out.append([a, m, False]); a = m - r.uniform(4, 12)
                out.append([a, b, False])
            row[:] = out

        def xy(u, v):
            return (cx + dv[0] * u + nv[0] * v, cy + dv[1] * u + nv[1] * v)
        for i in range(len(rows)):
            for run in rows[i]:
                if run[2]: continue
                pts, total, row, cur, fwd = [], 0.0, i, run, bool(r.random() < 0.5)
                while cur is not None and total < reach:
                    cur[2] = True
                    a = cur[0] - r.uniform(-0.4, 1.0) * overshoot
                    b = cur[1] + r.uniform(-0.4, 1.0) * overshoot
                    v = vs[row]
                    pts += [xy(a, v), xy(b, v)] if fwd else [xy(b, v), xy(a, v)]
                    total += b - a
                    nxt, best = None, 0.0
                    if row + 1 < len(rows):
                        for cand in rows[row + 1]:
                            if cand[2]: continue
                            ov = min(cand[1], cur[1]) - max(cand[0], cur[0])
                            if ov > best: nxt, best = cand, ov
                    if nxt is None or best < 6: break
                    row += 1; fwd = not fwd; cur = nxt
                if len(pts) >= 2:
                    self._mark(None, width * r.uniform(0.85, 1.15), colour, medium, 1.0, dry * r.uniform(0.7, 1.3),
                               (0.04, 0.12), wobble, streak=0.6, rough=1.3, alpha=alpha, swell=0.25, clip=clip,
                               Q=self._hand(np.array(pts, np.float32), wobble, False, False, r))

    def hatch(self, mask, angle=70.0, spacing=8.0, length=(18, 40), width=2.2, colour=INK, medium='ink', dry=0.35,
              bend=0.1, jitter=0.35, density=1.0, alpha=0.95, pressure=1.0, seed=None):
        """quick parallel flicks inside a mask (shading, rain-darkened cloth, fur shadow)"""
        r = self._r(seed)
        sl = self._bbox(mask, 2)
        if sl is None: return
        a = np.deg2rad(angle)
        dv, nv = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
        cx, cy = (sl[1].start + sl[1].stop) / 2, (sl[0].start + sl[0].stop) / 2
        R = 0.5 * np.hypot(sl[1].stop - sl[1].start, sl[0].stop - sl[0].start) + 4
        Lm = float(np.mean(length))
        for v in np.arange(-R, R, spacing):
            for u in np.arange(-R, R, Lm * 0.9) + r.uniform(0, Lm):
                if r.random() > density: continue
                uu = u + r.normal(0, Lm * jitter); vv = v + r.normal(0, spacing * jitter)
                x, y = cx + dv[0] * uu + nv[0] * vv, cy + dv[1] * uu + nv[1] * vv
                if not (0 <= x < self.W and 0 <= y < self.H) or mask[int(y), int(x)] < 0.5: continue
                L = r.uniform(*length); aa = a + r.normal(0, 0.06)
                d = np.array([np.cos(aa), np.sin(aa)]); nrm = np.array([-d[1], d[0]])
                b = r.uniform(-bend, bend) * L
                p = [(x - d[0] * L / 2, y - d[1] * L / 2), (x + nrm[0] * b, y + nrm[1] * b), (x + d[0] * L / 2, y + d[1] * L / 2)]
                self._mark(p, width * r.uniform(0.8, 1.2), colour, medium, pressure, dry, (0.08, 0.45), 0.5,
                           streak=0.5, rough=1.2, alpha=alpha, seed=int(r.integers(1 << 30)))

    def blades(self, x0, x1, y, n=20, height=(30, 90), lean=0.0, width=4.0, colour=INK, medium='ink', dry=0.3,
               curl=0.25, alpha=0.95, clip=None, seed=None):
        """tapered leaf / grass blades growing up from a base line y (or a function of x)"""
        r = self._r(seed)
        for _ in range(n):
            x = r.uniform(x0, x1)
            yb = y(x) if callable(y) else y
            h = r.uniform(*height)
            a = np.deg2rad(-90 + lean + r.normal(0, 16))
            c = r.normal(0, curl)
            p0 = np.array([x, yb + r.uniform(0, 6)])
            d = np.array([np.cos(a), np.sin(a)]); nrm = np.array([-d[1], d[0]])
            pts = [p0, p0 + d * h * 0.5 + nrm * c * h * 0.3, p0 + d * h + nrm * c * h * 0.8]
            self._mark(pts, width * r.uniform(0.7, 1.25), colour, medium, 1.0, dry, (0.04, 0.85), 0.7, streak=0.4,
                       rough=1.0, alpha=alpha, swell=0.1, clip=clip, seed=int(r.integers(1 << 30)))

    # ================================================================== dots, spatter, speckle
    def _dots(self, xs, ys, rs, colour, medium='ink', alpha=0.95, elong=None, angle=None, rough=0.0, tooth=0.35,
              ss=3, over_ink=0.1, seed=None):
        """many small dots at once (rendered at ss x, then laid through the tooth)"""
        xs, ys, rs = (np.asarray(v, np.float32).ravel() for v in (xs, ys, rs))
        if not len(xs): return
        r = self._r(seed)
        pad = float(rs.max() * (1 + (0 if elong is None else np.max(elong))) + 3)
        sl = self._clip_box(xs.min() - pad, ys.min() - pad, xs.max() + pad + 1, ys.max() + pad + 1)
        if sl is None: return
        x0, y0 = sl[1].start, sl[0].start
        h, w = sl[0].stop - y0, sl[1].stop - x0
        im = Image.new('L', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        el = np.ones(len(xs)) if elong is None else np.asarray(elong, np.float32) * np.ones(len(xs))
        an = r.uniform(0, np.pi, len(xs)) if angle is None else np.deg2rad(np.asarray(angle, np.float32)) * np.ones(len(xs))
        for x, y, rr, e, a in zip(xs, ys, rs, el, an):
            cx, cy = (x - x0) * ss, (y - y0) * ss
            m = max(10, int(rr * ss * 2.2))
            t = np.linspace(0, 2 * np.pi, m, endpoint=False)
            rad = rr * ss * (1 + rough * 0.5 * fbm1d(m, max(2.0, m / 5), 2, int(r.integers(1 << 30))) if rough else 1)
            px, py = np.cos(t) * rad * e, np.sin(t) * rad
            c, s_ = np.cos(a), np.sin(a)
            d.polygon(list(zip((cx + px * c - py * s_).tolist(), (cy + px * s_ + py * c).tolist())), fill=255)
        cov = np.asarray(im.resize((w, h), Image.BOX), np.float32) / 255
        if tooth:
            cov = cov * smoothstep(-0.2, 0.25, self.T[sl] - 0.5 + (1 - tooth) + cov * 0.6 - 0.35)
        self._lay(sl, cov * alpha, colour, medium, over_ink)

    def dot(self, x, y, r=4.0, ry=None, colour=INK, medium='ink', alpha=0.97, rough=0.18, seed=None):
        """a solid little ink dot (an eye, a nose, a button) with an irregular edge"""
        ry = r if ry is None else ry
        self._dots([x], [y], [ry], colour, medium, alpha, elong=[r / ry], angle=[0.0], rough=rough, tooth=0.15, seed=seed)

    def _region_points(self, region, n, r, avoid=None):
        if np.ndim(region) == 1:
            x0, y0, x1, y1 = region
            xs, ys = r.uniform(x0, x1, n * 2), r.uniform(y0, y1, n * 2)
        else:
            yy, xx = np.nonzero(region > 0.5)
            if not len(yy): return np.zeros(0), np.zeros(0)
            i = r.integers(0, len(yy), n * 2)
            xs, ys = xx[i] + r.random(n * 2), yy[i] + r.random(n * 2)
        if avoid is not None:
            ok = avoid[np.clip(ys.astype(int), 0, self.H - 1), np.clip(xs.astype(int), 0, self.W - 1)] < 0.5
            xs, ys = xs[ok], ys[ok]
        return xs[:n], ys[:n]

    def spatter(self, region, colour=INK, n=60, size=(0.7, 4.5), alpha=0.92, satellites=0.6, medium=None,
                avoid=None, seed=None):
        """flicked paint: power-law drop sizes, slightly elongated, with satellite droplets"""
        r = self._r(seed)
        medium = medium or ('ink' if hexc(colour).mean() < 0.3 else 'chalk')
        xs, ys = self._region_points(region, n, r, avoid)
        if not len(xs): return
        rs = size[0] + (size[1] - size[0]) * r.random(len(xs)) ** 3.2
        an = r.uniform(0, 180, len(xs))
        X, Y, R_, E, A = [xs], [ys], [rs], [r.uniform(1.0, 1.6, len(xs))], [an]
        k = r.random(len(xs)) < satellites
        if k.any():
            m = int(k.sum())
            dd = rs[k] * r.uniform(1.8, 4.0, m)
            X.append(xs[k] + np.cos(np.deg2rad(an[k])) * dd); Y.append(ys[k] + np.sin(np.deg2rad(an[k])) * dd)
            R_.append(np.maximum(0.45, rs[k] * r.uniform(0.2, 0.45, m))); E.append(np.ones(m)); A.append(an[k])
        self._dots(np.concatenate(X), np.concatenate(Y), np.concatenate(R_), colour, medium, alpha,
                   np.concatenate(E), np.concatenate(A), rough=0.2, tooth=0.25, seed=int(r.integers(1 << 30)))

    def speckle(self, region, colour='chalk', n=400, size=(0.45, 1.3), alpha=0.85, medium=None, avoid=None, seed=None):
        """fine dust / sparkle specks"""
        r = self._r(seed)
        medium = medium or ('ink' if hexc(colour).mean() < 0.3 else ('chalk' if hexc(colour).mean() > 0.85 else 'crayon'))
        xs, ys = self._region_points(region, n, r, avoid)
        if not len(xs): return
        rs = size[0] + (size[1] - size[0]) * r.random(len(xs)) ** 2
        self._dots(xs, ys, rs, colour, medium, alpha, r.uniform(1.0, 1.8, len(xs)), None, rough=0.3, tooth=0.4,
                   seed=int(r.integers(1 << 30)))

    # ================================================================== chalk, weather
    def chalk(self, target, width=10.0, pressure=0.62, angle=None, dry=0.45, colour='chalk', alpha=0.95, taper=(0.2, 0.4),
              wobble=1.2, over_ink=0.5, seed=None, **fill_kw):
        """opaque white chalk / pastel / white gouache over the colour: a mask is coloured in, paths are stroked"""
        r = self._r(seed)
        if isinstance(target, np.ndarray) and target.ndim == 2 and target.shape == (self.H, self.W):
            kw = dict(slip=0, loose=3.0, edge=10.0, dry_edge=0.7, mottle=0.2, lanes=16.0, lane_var=0.2, streak=0.85,
                      over_ink=over_ink)
            kw.update(fill_kw)
            return self.fill(target, colour, pressure, angle, medium='chalk', alpha=alpha, tint=0,
                             seed=int(r.integers(1 << 30)), **kw)
        for p in target:
            self._mark(p, width * r.uniform(0.8, 1.2), colour, 'chalk', pressure * r.uniform(0.85, 1.1),
                       dry * r.uniform(0.7, 1.3), taper, wobble, streak=0.7, rough=2.0, alpha=alpha,
                       seed=int(r.integers(1 << 30)), over_ink=over_ink)

    def rain(self, region, n=400, angle=100.0, length=(12, 30), width=(1.5, 2.8), colour='deep', medium=None,
             dry=0.5, pressure=0.95, alpha=0.9, avoid=None, seed=None):
        """rain as short dry strokes"""
        r = self._r(seed)
        medium = medium or ('chalk' if hexc(colour).mean() > 0.85 else 'crayon')
        xs, ys = self._region_points(region, n, r, avoid)
        for x, y in zip(xs, ys):
            L = r.uniform(*length); a = np.deg2rad(angle + r.normal(0, 3))
            d = np.array([np.cos(a), np.sin(a)])
            self._mark([(x - d[0] * L / 2, y - d[1] * L / 2), (x + d[0] * L / 2, y + d[1] * L / 2)],
                       r.uniform(*width), colour, medium, pressure, dry, (0.05, 0.6), 0.3, smooth=False,
                       streak=0.5, rough=1.2, alpha=alpha, swell=0.1, seed=int(r.integers(1 << 30)))

    def splash(self, x, y, size=10.0, colour='chalk', medium=None, n=5, width=2.0, up=-90.0, seed=None):
        """the little crown where a drop hits: a fan of short ticks and a couple of droplets"""
        r = self._r(seed)
        medium = medium or ('chalk' if hexc(colour).mean() > 0.85 else ('ink' if hexc(colour).mean() < 0.3 else 'crayon'))
        for a in np.linspace(up - 70, up + 70, n) + r.normal(0, 8, n):
            d = np.array([np.cos(np.deg2rad(a)), np.sin(np.deg2rad(a))])
            s0, s1 = size * r.uniform(0.25, 0.45), size * r.uniform(0.7, 1.1)
            self._mark([(x + d[0] * s0, y + d[1] * s0), (x + d[0] * s1, y + d[1] * s1)], width * r.uniform(0.7, 1.2),
                       colour, medium, 1.0, 0.2, (0.1, 0.6), 0.2, smooth=False, streak=0.3, alpha=0.95,
                       seed=int(r.integers(1 << 30)))
        k = int(r.integers(1, 3))
        aa = np.deg2rad(up + r.uniform(-50, 50, k))
        self._dots(x + np.cos(aa) * size * 1.4, y + np.sin(aa) * size * 1.4, r.uniform(0.8, 1.5, k) * width * 0.6,
                   colour, medium, 0.95, tooth=0.2)

    def ripples(self, cx, cy, rx, ry, rings=2, colour='chalk', medium=None, width=2.4, gap=0.55, seed=None):
        """broken concentric rings on a puddle"""
        r = self._r(seed)
        medium = medium or ('chalk' if hexc(colour).mean() > 0.85 else ('ink' if hexc(colour).mean() < 0.3 else 'crayon'))
        for k in range(rings):
            s = 1 + k * gap
            n_arc = int(r.integers(2, 4))
            starts = np.sort(r.uniform(0, 2 * np.pi, n_arc))
            for a0 in starts:
                span = r.uniform(0.6, 1.5)
                t = np.linspace(a0, a0 + span, 14)
                pts = np.stack([cx + np.cos(t) * rx * s, cy + np.sin(t) * ry * s], 1)
                self._mark(pts, width * (1 - 0.15 * k), colour, medium, 0.9, 0.3, (0.25, 0.4), 0.6, streak=0.5,
                           rough=1.4, alpha=0.95 - 0.15 * k, seed=int(r.integers(1 << 30)))

    # ================================================================== characters
    def head(self, cx, cy, rx, ry=None, width=4.6, rot=0.0, ears=(), lumpy=0.025, colour=INK, open_=0.6, seed=None):
        """a big round head as an open ink contour; ears = [(x, y, r)] drawn only where they stick out.
        Returns the head mask (ears included)."""
        r = self._r(seed)
        ry = rx if ry is None else ry
        pts = blob_pts(cx, cy, rx, ry, lumpy, 120, int(r.integers(1 << 30)), np.deg2rad(rot))
        self.outline(pts, width, open_=open_, strokes=(1, 2), colour=colour, seed=int(r.integers(1 << 30)))
        m = self.ellipse(cx, cy, rx, ry, rot)
        for ex, ey, er in ears:
            t = np.linspace(0, 2 * np.pi, 90, endpoint=False)
            E = np.stack([ex + np.cos(t) * er, ey + np.sin(t) * er], 1)
            X, Y = E[:, 0] - cx, E[:, 1] - cy
            a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
            X, Y = X * c + Y * s, -X * s + Y * c
            out = (X / rx) ** 2 + (Y / ry) ** 2 > 0.98
            if out.any():
                i0 = int(np.argmin(out)) if not out.all() else 0
                E2, o2 = np.roll(E, -i0, 0), np.roll(out, -i0)
                idx = np.flatnonzero(o2)
                arc = E2[idx[0]:idx[-1] + 1]
                if len(arc) > 2:
                    self.ink(arc, width * 0.9, colour, 0.2, (0.1, 0.25), smooth=False, seed=int(r.integers(1 << 30)))
            m = np.maximum(m, self.ellipse(ex, ey, er))
        return m

    def eyes(self, pts, r=6.0, look=(0.0, 0.0), glint=0.36, ry=1.12, colour=INK, seed=None):
        """dot eyes with a white glint"""
        rr = self._r(seed)
        for (x, y) in pts:
            x2, y2 = x + look[0] * r * 0.3, y + look[1] * r * 0.3
            self.dot(x2, y2, r, r * ry, colour, seed=int(rr.integers(1 << 30)))
            if glint:
                self._dots([x2 - r * 0.32], [y2 - r * 0.38], [max(0.9, r * glint)], 'chalk', 'chalk', 0.97, tooth=0.05,
                           over_ink=1.0)

    def smile(self, x, y, w=14.0, depth=5.0, width=2.6, tilt=0.0, colour=INK, seed=None):
        a = np.deg2rad(tilt); c, s = np.cos(a), np.sin(a)
        P = np.array([(-w / 2, 0), (-w / 4, depth * 0.8), (0, depth), (w / 4, depth * 0.8), (w / 2, -depth * 0.1)], np.float32)
        P = np.stack([x + P[:, 0] * c - P[:, 1] * s, y + P[:, 0] * s + P[:, 1] * c], 1)
        self.ink(P, width, colour, 0.1, (0.2, 0.35), wobble=0.4, seed=seed)

    def blush(self, cx, cy, r=18.0, colour='cheek', density=1.0, ry=None, soft=0.18, seed=None):
        """a stippled cheek: separate little pink dots over a faint crayon disc"""
        rr = self._r(seed)
        ry = r * 0.82 if ry is None else ry
        if soft:
            self.fill(self.ellipse(cx, cy, r * 0.95, ry * 0.95), colour, pressure=soft, slip=0, loose=2.0, edge=4,
                      dry_edge=0.6, lanes=0, mottle=0.3, seed=int(rr.integers(1 << 30)))
        n = int(r * ry * 0.55 * density)
        a = rr.uniform(0, 2 * np.pi, n); d = np.sqrt(rr.random(n)) ** 0.8
        xs, ys = cx + np.cos(a) * d * r, cy + np.sin(a) * d * ry
        keep = rr.random(n) < 1.15 - d ** 2
        k = int(keep.sum())
        self._dots(xs[keep], ys[keep], rr.uniform(0.8, 1.9, k) * max(1.0, r / 22), colour, 'gouache', 0.92,
                   rr.uniform(1, 1.4, k), rough=0.3, tooth=0.25)

    def freckles(self, cx, cy, n=4, spread=9.0, r=1.2, colour='freckle', seed=None):
        rr = self._r(seed)
        self._dots(cx + rr.normal(0, spread * 0.5, n), cy + rr.normal(0, spread * 0.3, n), rr.uniform(0.7, 1.15, n) * r,
                   colour, 'crayon', 0.9, rough=0.2, tooth=0.1)

    def _edge_points(self, mask, every, r, avoid=None, inset=0.0):
        """points on the silhouette of a mask, about `every` px apart, with outward normals"""
        sl = self._bbox(mask, 6)
        if sl is None: return []
        mb = blur(mask[sl], 1.6)
        gy, gx = np.gradient(mb)
        band = (mb > 0.3) & (mb < 0.7)
        yy, xx = np.nonzero(band)
        if not len(yy): return []
        cell = (yy // every) * 100000 + (xx // every)
        order = r.permutation(len(yy))
        _, first = np.unique(cell[order], return_index=True)
        pick = order[first]
        out = []
        for i in pick:
            y, x = yy[i], xx[i]
            g = np.hypot(gx[y, x], gy[y, x]) + 1e-6
            nx, ny = -gx[y, x] / g, -gy[y, x] / g
            X, Y = x + sl[1].start + r.uniform(-every / 3, every / 3) * -ny, y + sl[0].start + r.uniform(-every / 3, every / 3) * nx
            if avoid is not None and avoid[int(np.clip(Y, 0, self.H - 1)), int(np.clip(X, 0, self.W - 1))] > 0.5: continue
            out.append((X - nx * inset, Y - ny * inset, nx, ny))
        return out

    def fluff(self, mask, medium='ink', every=None, length=(16, 30), width=None, curl=0.5, colour=None, avoid=None,
              curls=0, alpha=None, reach=(0.6, 0.45), gaps=0.12, seed=None):
        """scribbly fur. medium='ink': the silhouette as short scalloped tufts (a line that is all little
        bumps, never closed); medium='chalk': white tufts that start inside and cross the edge into the background;
        curls = little c-shaped marks inside (in `colour`)."""
        r = self._r(seed)
        ink_ = medium == 'ink'
        colour = colour or (INK if ink_ else 'chalk')
        width = width or (3.2 if ink_ else 5.0)
        alpha = alpha or (0.96 if ink_ else 0.92)
        every = every or (0.62 * float(np.mean(length)) if ink_ else 0.5 * float(np.mean(length)))
        for (x, y, nx, ny) in self._edge_points(mask, every, r, avoid):
            tx, ty = -ny, nx
            L = r.uniform(*length)
            if ink_:
                if r.random() < gaps: continue
                sgn = r.choice([-1, 1])
                bulge = L * curl * r.uniform(0.35, 1.0)
                sink = L * r.uniform(0.04, 0.16)
                p0 = (x - tx * L / 2 * sgn - nx * sink, y - ty * L / 2 * sgn - ny * sink)
                pm = (x + nx * bulge * 0.6, y + ny * bulge * 0.6)
                p1 = (x + tx * L / 2 * sgn - nx * sink * 0.5, y + ty * L / 2 * sgn - ny * sink * 0.5)
                self._mark([p0, pm, p1], width * r.uniform(0.75, 1.25), colour, 'ink', 1.0, 0.12, (0.18, 0.4), 0.4,
                           streak=0.35, rough=1.0, alpha=alpha, swell=0.25, seed=int(r.integers(1 << 30)))
            else:
                a = r.normal(0, 0.45)
                dx, dy = nx * np.cos(a) - ny * np.sin(a), nx * np.sin(a) + ny * np.cos(a)
                b = r.normal(0, 0.25) * L
                p0 = (x - dx * L * reach[0], y - dy * L * reach[0])
                p1 = (x + dx * L * reach[1] + tx * b, y + dy * L * reach[1] + ty * b)
                self._mark([p0, ((p0[0] + p1[0]) / 2 + tx * b * 0.4, (p0[1] + p1[1]) / 2 + ty * b * 0.4), p1],
                           width * r.uniform(0.7, 1.3), colour, 'chalk', r.uniform(0.7, 0.95), 0.4, (0.15, 0.6), 0.5,
                           streak=0.6, rough=1.8, alpha=alpha, seed=int(r.integers(1 << 30)))
        if curls:
            yy, xx = np.nonzero(mask > 0.9)
            if len(yy):
                for i in r.integers(0, len(yy), curls):
                    x, y = xx[i], yy[i]
                    rr_ = r.uniform(4, 8); a0 = r.uniform(0, 2 * np.pi)
                    t = np.linspace(a0, a0 + r.uniform(2.6, 4.2), 9)
                    pts = np.stack([x + np.cos(t) * rr_, y + np.sin(t) * rr_ * 0.8], 1)
                    self._mark(pts, (width or 2.4) * 0.7, colour if colour else 'slate', 'ink' if ink_ else 'crayon',
                               0.9, 0.3, (0.2, 0.5), 0.4, streak=0.4, alpha=0.85, seed=int(r.integers(1 << 30)))

    def flower(self, x, y, r=7.0, colour='coral', petals=5, centre=INK, seed=None):
        """a tiny flower: crayon petals and an ink centre"""
        rr = self._r(seed)
        a0 = rr.uniform(0, 2 * np.pi)
        a = a0 + np.arange(petals) * 2 * np.pi / petals + rr.normal(0, 0.15, petals)
        self._dots(x + np.cos(a) * r * 0.62, y + np.sin(a) * r * 0.62, rr.uniform(0.5, 0.62, petals) * r, colour,
                   'gouache', 0.95, rr.uniform(1.1, 1.4, petals), np.degrees(a), rough=0.25, tooth=0.45)
        self._dots([x], [y], [max(1.0, r * 0.22)], centre, 'ink' if hexc(centre).mean() < 0.3 else 'crayon', 0.95, tooth=0.1)

    # ================================================================== finish
    def printed(self, amount=1.0, gutter=None):
        """reproduce the page in a book: print softness, lifted blacks, paper speck; gutter = x of the fold"""
        self.print_amt = float(amount)
        self.gutter_x = gutter

    def folio(self, x, y, text, size=20, colour=INK, anchor='mm'):
        """a tiny page number"""
        self._need()
        f = load_font('serif', size)
        m = text_mask(self.H, self.W, str(text), f, (x, y), anchor=anchor)
        sl = self._bbox(m, 2)
        if sl is None: return
        dep = m[sl] * smoothstep(0.05, 0.35, self.T[sl] + m[sl] * 0.5 - 0.2) * 0.9
        self._lay(sl, dep, colour, 'ink')

    def render(self):
        out = self.C.copy()
        p = self.print_amt
        if p:
            soft = np.stack([blur(out[..., i], 0.7) for i in range(3)], -1)
            out = out * (1 - 0.3 * p) + soft * 0.3 * p
            c0 = 0.07 * p * hexc('#262833')                                   # blacks lift to a deep ink, white stays white
            out = c0 + out * (1 - c0)
            if not hasattr(self, '_speck'):
                r = np.random.default_rng(self.seed + 7)
                sp = r.normal(0, 1, (self.H, self.W)).astype(np.float32)
                self._speck = 0.6 * sp + 0.4 * blur(sp, 1.1) * 2.2
            out = out * (1 + 0.009 * p * self._speck[..., None])
            if self.gutter_x is not None:
                X = np.arange(self.W, dtype=np.float32) - self.gutter_x
                sh = 0.075 * np.exp(-(X / 9) ** 2) + 0.045 * np.exp(-(X / 60) ** 2) + 0.02 * np.exp(-((X + 2) / 1.2) ** 2)
                hi = 0.025 * np.exp(-((X - 4) / 1.5) ** 2)
                out = out * (1 - p * sh)[None, :, None] + p * hi[None, :, None]
        return np.clip(out, 0, 1)

    def composite(self):
        return Image.fromarray((self.render() * 255 + 0.5).astype(np.uint8))

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
