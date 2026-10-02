"""graphite — a pencil drawing in graphite on cartridge paper: tone built from hatching and the side of the lead,
blended with a stump, lifted with erasers, fading out to bare construction lines at the edges (numpy + Pillow only).

Model:
  paper     off-white cartridge paper. Its `tooth` is a height field (0 valley .. 1 peak) of small bumps about
            2 px across with a faint felt texture; under raking light the bumps show a little even where nothing
            is drawn. The sheet is lit from the top left, so there is a very soft light falloff across it.
  graphite  a pencil stroke shaves graphite onto the paper. How much sticks is pressure x the grade's softness, and
            it only sticks where the lead actually touches: light pressure grazes the peaks of the tooth (a grainy,
            sparkly grey with white valleys between), heavy pressure and soft leads reach into the valleys and
            fill them. Graphite is a mass field `m`; the visible value is Dmax (1 - exp(-m)), so layers add up but
            never reach black. Graphite is grey, not black: dark passages are a cool slate grey, and hard
            pressure polishes them (`b`), which in raking light gives the slight silvery sheen of graphite.
  grades    4H .. 8B (`GRADES`): mass per stroke, how deep into the tooth the lead reaches, and the line width.
            Hard leads give thin, pale, crisp lines that leave the tooth white; soft leads give broad dark lines.
  hand      `guide` long light construction lines that overshoot (perspective lines to a vanishing point,
            plumb lines), `guide_ellipse` loose two-loop ellipses with their axes; `line` a contour stroke whose
            pressure swells and fades along it (heavier on the shadow side, `lost` gaps where light eats the
            edge), optionally searched for twice before it settles; `hatch` patches of parallel strokes laid by
            the wrist (all bowed the same way, heavy at the start and flicked off at the end, rows sharing
            staggered breaks) and built up in layers: first one direction, then interleaved, then crossed at a
            second and a third angle -- each layer only where the tone asks for it; `contour_hatch` strokes
            that follow the form (around a tyre, along a tube); `shade` the side of a blunt soft lead, broad
            grainy strokes that leave the tooth white.
  stump     `smudge` with a paper stump or a finger: graphite is pushed into the valleys and sideways (local
            blur, optionally dragged in one direction), a little is picked up; grain disappears, tone softens and
            creeps a few px past where it was drawn.
  erasers   `lift` a kneaded eraser dabbed on to pull out soft highlights; `erase` a hard eraser edge cutting
            crisp white lines through tone (spokes catching light, rim highlights); erasing a construction line
            leaves a ghost.
  margins   `focus` sets where the drawing is finished: tone (hatching, shading, smudging) fades out with an
            irregular edge, lines get lighter, so the edges of the sheet are left as bare line drawing.
            `write` pencil handwriting, `value_scale` a strip of grade swatches the artist tried in the margin,
            `fingerprint` a graphite thumbprint, `smear` the grey haze where the side of the hand dragged.
Angles are screen degrees, clockwise (y points down): 0 runs left to right, 60 runs down to the right.

    from graphite import Graphite
    g = Graphite(1920, 1080, seed=3)
    g.paper()
    g.focus(960, 560, 700, 420)                                  # tone only near the middle
    g.guide((100, 800), (1800, 800))                             # a light construction line
    m = g.ellipse(960, 540, 220, 220)
    g.hatch(m, tone=g.radial(900, 480, 260), angle=60, grade='2B')
    g.smudge(m, 0.6, radius=4)
    g.lift(g.ellipse(900, 470, 40, 30, feather=12), 0.8)          # kneaded-eraser highlight
    g.line(g.circle_pts(960, 540, 220), grade='4B', pressure=0.8, closed=True)
    g.save('sphere.jpg')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, load_font, text_mask

#        mass per full-pressure stroke, tooth reach at full pressure, line width (px)
GRADES = {
    '4H': (0.30, 0.40, 0.95),
    '2H': (0.45, 0.48, 1.05),
    'H':  (0.62, 0.54, 1.15),
    'HB': (0.85, 0.62, 1.30),
    '2B': (1.20, 0.70, 1.55),
    '4B': (1.65, 0.80, 1.85),
    '6B': (2.20, 0.90, 2.20),
    '8B': (2.90, 1.00, 2.60),
}
PAPER = '#f1efe9'
GRAPHITE = (0.205, 0.212, 0.235)        # the darkest polished graphite: a cool slate, never black
SHEEN = (0.62, 0.65, 0.71)              # what polished graphite reflects in raking light


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _gblur(a, sigma):
    """small-radius gaussian blur in float32 with a separable kernel (low memory; for the paper tooth)"""
    r = max(1, int(np.ceil(3 * sigma)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1, dtype=np.float32) / sigma) ** 2); k /= k.sum()
    out = a.astype(np.float32)
    for ax in (0, 1):
        p = np.pad(out, [(r, r), (0, 0)] if ax == 0 else [(0, 0), (r, r)], mode='edge')
        acc = np.zeros_like(out)
        n = out.shape[ax]
        for i, w in enumerate(k):
            acc += w * (p[i:i + n] if ax == 0 else p[:, i:i + n])
        out = acc
    return out


def _resample(P, step):
    """polyline -> points every `step` px along its length"""
    P = np.asarray(P, np.float32)
    if len(P) < 2: return P
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(s[-1] / step) + 1)
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1).astype(np.float32)


class Graphite:
    def __init__(self, W=1920, H=1080, seed=0, ss=2):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.m = np.zeros((H, W), np.float32)            # graphite mass
        self.b = np.zeros((H, W), np.float32)            # burnish (polish) of the graphite
        self.tooth = np.full((H, W), 0.5, np.float32)
        self.base = np.ones((H, W, 3), np.float32) * hexc(PAPER)
        self.finish = np.ones((H, W), np.float32)
        self.dmax = 0.9
        self.stages = []

    def _grid(self):
        """broadcastable pixel coordinates (H, 1) and (1, W) -- no full-size index arrays"""
        return (np.arange(self.H, dtype=np.float32)[:, None], np.arange(self.W, dtype=np.float32)[None, :])

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1)) + 1), min(self.H, int(np.ceil(y1)) + 1)
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    def _mask_box(self, M, pad=2, thr=0.01):
        rows = np.nonzero((M > thr).any(1))[0]
        if not len(rows): return None
        cols = np.nonzero((M[rows[0]:rows[-1] + 1] > thr).any(0))[0]
        return self._box(cols[0] - pad, rows[0] - pad, cols[-1] + pad, rows[-1] + pad)

    # ------------------------------------------------------------ paper
    def paper(self, tone=PAPER, tooth=1.6, felt=0.05, mottle=0.012):
        """cartridge paper: tooth height field (bumps ~`tooth` px), faint felt texture, very soft light falloff"""
        H, W = self.H, self.W
        r = np.random.default_rng(self._seed())
        t = _gblur(r.random((H, W), dtype=np.float32), tooth * 0.3)
        t -= t.mean(); t /= (t.std() + 1e-6)
        t2 = _gblur(r.random((H, W), dtype=np.float32), tooth * 1.3)
        t2 -= t2.mean(); t2 /= (t2.std() + 1e-6)
        t *= 0.74; t += 0.26 * t2; del t2
        fe = noise2d(H, W, 14, 2, self._seed()) - 0.5
        t += felt * fe / (fe.std() + 1e-6); del fe
        t /= (t.std() + 1e-6)
        self.tooth = np.clip(0.5 + t * 0.2, 0, 1).astype(np.float32); del t
        base = hexc(tone)
        gy, gx = np.gradient(_gblur(self.tooth, 0.7))
        emboss = (-gx * 0.6 - gy * 0.8) * 0.07                      # raking light from the top left on the bumps
        mot = (noise2d(H, W, 260, 3, self._seed()) - 0.5) * mottle * 2
        YY, XX = self._grid()
        light = 1.0 - 0.035 * ((XX / W) * 0.6 + (YY / H) * 0.8)        # brighter top left
        f = (1 + emboss + mot) * light
        self.base = (base[None, None, :] * f[..., None]).astype(np.float32)

    # ------------------------------------------------------------ masks and tone fields
    def _local(self, P, pad):
        """bounding box of points (+pad) on the canvas -> (slices, x0, y0, w, h), or None"""
        P = np.asarray(P, np.float32).reshape(-1, 2)
        sl = self._box(P[:, 0].min() - pad, P[:, 1].min() - pad, P[:, 0].max() + pad, P[:, 1].max() + pad)
        if sl is None: return None
        return sl, sl[1].start, sl[0].start, sl[1].stop - sl[1].start, sl[0].stop - sl[0].start

    def _paint(self, P_all, pad, feather, draw):
        """rasterise a mask only inside its bounding box (2x supersampled) -> full-size float mask"""
        M = np.zeros((self.H, self.W), np.float32)
        loc = self._local(P_all, pad + 3 * feather + 3)
        if loc is None: return M
        sl, x0, y0, w, h = loc
        im = Image.new('L', (w * 2, h * 2), 0)
        draw(ImageDraw.Draw(im), lambda p: (float(p[0] - x0) * 2, float(p[1] - y0) * 2))
        a = np.asarray(im.resize((w, h), Image.BILINEAR), np.float32) / 255
        M[sl] = blur(a, feather) if feather else a
        return M

    def poly(self, pts, feather=0.7):
        P = np.asarray(pts, np.float32)
        return self._paint(P, 2, feather, lambda d, T: d.polygon([T(p) for p in P], fill=255))

    def ellipse(self, cx, cy, rx, ry=None, rot=0.0, feather=1.0):
        ry = rx if ry is None else ry
        sl = self._box(cx - max(rx, ry) - 4 * feather - 2, cy - max(rx, ry) - 4 * feather - 2, cx + max(rx, ry) + 4 * feather + 2, cy + max(rx, ry) + 4 * feather + 2)
        M = np.zeros((self.H, self.W), np.float32)
        if sl is None: return M
        yy, xx = np.mgrid[sl].astype(np.float32)
        a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
        u, v = (xx - cx) * c + (yy - cy) * s, -(xx - cx) * s + (yy - cy) * c
        d = (np.sqrt((u / rx) ** 2 + (v / ry) ** 2) - 1) * min(rx, ry)
        M[sl] = np.clip(0.5 - d / max(feather, 0.5), 0, 1)
        return M

    def ring(self, cx, cy, r0, r1, ry_scale=1.0, feather=0.8):
        return np.clip(self.ellipse(cx, cy, r1, r1 * ry_scale, feather=feather) - self.ellipse(cx, cy, r0, r0 * ry_scale, feather=feather), 0, 1)

    def band(self, pts, width, feather=0.7, smooth=True):
        """mask of a thick polyline (a tube, a rod, a strap)"""
        P = spline(pts, 10) if (smooth and len(pts) > 2) else np.asarray(pts, np.float32)

        def draw(d, T):
            Q = [T(p) for p in P]
            d.line(Q, fill=255, width=max(1, int(round(width * 2))), joint='curve')
            for q in (Q[0], Q[-1]):
                d.ellipse([q[0] - width, q[1] - width, q[0] + width, q[1] + width], fill=255)
        return self._paint(P, width, feather, draw)

    def lines_mask(self, lines, width=1.5, feather=0.5):
        """mask of many thin polylines at once (spokes, wires, chain)"""
        allp = np.concatenate([np.asarray(P, np.float32) for P in lines])

        def draw(d, T):
            for P in lines:
                d.line([T(p) for p in P], fill=255, width=max(1, int(round(width * 2))), joint='curve')
        return self._paint(allp, width, feather, draw)

    def rect(self, x0, y0, x1, y1, feather=0.6):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], feather)

    def linear(self, p0, p1, gamma=1.0):
        """tone field 0 at p0 rising to 1 at p1 (clamped beyond)"""
        YY, XX = self._grid()
        d = np.array(p1, np.float32) - np.array(p0, np.float32)
        t = ((XX - p0[0]) * d[0] + (YY - p0[1]) * d[1]) / float(d @ d)
        return np.clip(t, 0, 1) ** gamma

    def radial(self, cx, cy, r, gamma=1.0):
        """tone field 0 at (cx, cy) rising to 1 at distance r -- light falling off a rounded form"""
        YY, XX = self._grid()
        return np.clip(np.hypot(XX - cx, YY - cy) / r, 0, 1) ** gamma

    @staticmethod
    def circle_pts(cx, cy, rx, ry=None, a0=0.0, a1=360.0, rot=0.0, n=None):
        """points on an ellipse arc (degrees, clockwise on screen)"""
        ry = rx if ry is None else ry
        n = n or max(8, int(abs(a1 - a0) / 360 * 2 * np.pi * max(rx, ry) / 4))
        t = np.deg2rad(np.linspace(a0, a1, n))
        x, y = rx * np.cos(t), ry * np.sin(t)
        a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
        return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)

    def focus(self, cx, cy, rx, ry, soft=0.38, rough=0.16):
        """where the drawing is finished: 1 inside an irregular oval, falling to 0 past its edge.
        Tone (hatch / shade / smudge) is multiplied by it; lines get lighter outside"""
        YY, XX = self._grid()
        ang = np.arctan2((YY - cy) / ry, (XX - cx) / rx)
        wob = np.interp(ang, np.linspace(-np.pi, np.pi, 181), fbm1d(181, 18, 4, self._seed()) * rough + 1.0)
        rr = np.hypot((XX - cx) / rx, (YY - cy) / ry) / wob
        rr = rr + (noise2d(self.H, self.W, 60, 3, self._seed()) - 0.5) * rough * 0.8
        self.finish = smoothstep(1 + soft, 1 - soft * 0.3, rr).astype(np.float32)
        return self.finish

    # ------------------------------------------------------------ strokes -> graphite
    def _raster(self, strokes):
        """strokes [(P (n,2), width (n,), pressure (n,))] -> (coverage, slices); drawn ss x, box-filtered.
        Lighter strokes are drawn first so a heavier one wins where two cross"""
        strokes = [s for s in strokes if len(s[0])]
        if not strokes: return None, None
        allp = np.concatenate([s[0] for s in strokes])
        pad = max(float(np.max(s[1])) for s in strokes) + 3
        sl = self._box(allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        if sl is None: return None, None
        ss = self.ss
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (bw * ss, bh * ss), 0)
        d = ImageDraw.Draw(im)
        off = np.array([x0, y0], np.float32)
        strokes.sort(key=lambda s: float(np.mean(s[2])))
        for P, w, v in strokes:
            Q = (P - off) * ss
            n = len(Q)
            if n == 1:
                r_ = w[0] * ss / 2
                d.ellipse([Q[0, 0] - r_, Q[0, 1] - r_, Q[0, 0] + r_, Q[0, 1] + r_], fill=int(255 * min(1, v[0])))
                continue
            ww = np.maximum(1, np.round((w[:-1] + w[1:]) * 0.5 * ss)).astype(int).tolist()
            vv = np.round(255 * np.clip((v[:-1] + v[1:]) * 0.5, 0, 1)).astype(int).tolist()
            q = Q.tolist()
            for i in range(n - 1):
                if vv[i] <= 0: continue
                d.line([tuple(q[i]), tuple(q[i + 1])], fill=vv[i], width=ww[i])
        cov = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        return cov, sl

    def _deposit(self, cov, sl, grade, clip=None, polish=1.0, gain=1.0):
        """coverage (pressure x footprint) -> graphite, through the paper tooth. `gain`: a point pressed into a
        line leaves more graphite per px than the same pressure spread over hatching"""
        mass, reach, _ = GRADES[grade]
        mass = mass * gain
        if clip is not None: cov = cov * clip[sl]
        t = self.tooth[sl]
        r = reach * (0.42 + 0.78 * np.sqrt(np.clip(cov, 0, 1)))   # how deep into the tooth the lead gets (by pressure,
                                                                     # so the anti-aliased rim of a line is not all grain)
        resp = smoothstep(1.0 - r - 0.16, 1.0 - r + 0.16, t)
        dm = cov * mass * resp
        self.m[sl] += dm
        self.b[sl] += dm * np.clip(cov, 0, 1) * mass * polish

    def _prep(self, pts, grade, pressure, width=None, taper=(0.12, 0.22), smooth=True, wobble=0.35, step=2.0,
              swell=0.22, fade=None):
        """one hand stroke: smoothed, resampled, wobbled; pressure eases in, swells and lifts off"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 8)
        P = _resample(P, step)
        n = len(P)
        if n < 2: return P, np.full(n, width or GRADES[grade][2], np.float32), np.full(n, pressure, np.float32)
        if wobble:
            tan = np.gradient(P, axis=0); tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6)
            nrm = np.stack([-tan[:, 1], tan[:, 0]], 1)
            P = P + nrm * (fbm1d(n, max(3, n / 3), 3, self._seed()) * wobble)[:, None]
        t = np.linspace(0, 1, n, dtype=np.float32)
        a, b = taper
        prof = np.ones(n, np.float32)
        if a > 0: prof *= 0.25 + 0.75 * smoothstep(0, a, t)
        if b > 0: prof *= 0.08 + 0.92 * (1 - smoothstep(1 - b, 1, t))
        prof *= 1 + swell * fbm1d(n, max(4, n / 2), 2, self._seed())
        v = pressure * prof
        if fade is not None:
            ix = np.clip(P[:, 0].astype(int), 0, self.W - 1); iy = np.clip(P[:, 1].astype(int), 0, self.H - 1)
            v = v * (fade + (1 - fade) * self.finish[iy, ix])
        w = (width or GRADES[grade][2]) * (0.75 + 0.25 * np.clip(prof, 0, 1.2))
        return P, w.astype(np.float32), v.astype(np.float32)

    def strokes(self, lines, grade='HB', pressure=0.6, width=None, taper=(0.12, 0.22), wobble=0.35, clip=None,
                smooth=True, fade=None, polish=1.0, gain=1.6):
        """deposit a batch of free strokes (each a list of points)"""
        S = [self._prep(p, grade, pressure, width, taper, smooth, wobble, fade=fade) for p in lines if len(p) >= 2]
        cov, sl = self._raster(S)
        if sl is not None: self._deposit(cov, sl, grade, clip, polish, gain)

    def line(self, pts, grade='HB', pressure=0.7, width=None, closed=False, searching=0, lost=0.0, weight=None,
             wobble=0.45, smooth=True, taper=(0.06, 0.12), fade=0.35, gain=2.0):
        """a contour line: pressure swells and fades along it; `lost` (0..1) lets light eat parts of the edge;
        `weight` an optional field (0..1, e.g. a shadow-side map) that makes the line heavier where it is high;
        `searching` lighter exploratory strokes laid first, slightly off the final line"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        if smooth and len(P) > 2: P = spline(P, 8)
        P = _resample(P, 2.0)
        for k in range(searching):
            n = len(P)
            i0 = int(self.rng.uniform(0, 0.15) * n); i1 = n - int(self.rng.uniform(0, 0.2) * n)
            tan = np.gradient(P, axis=0); tan /= (np.linalg.norm(tan, axis=1, keepdims=True) + 1e-6)
            off = np.stack([-tan[:, 1], tan[:, 0]], 1) * (fbm1d(n, max(4, n / 4), 3, self._seed()) * 2.6 + self.rng.normal(0, 1.0))[:, None]
            self.strokes([(P + off)[i0:i1]], 'H' if grade not in ('4H', '2H') else '4H', pressure * 0.5, None, (0.15, 0.2), wobble, smooth=False, fade=fade, gain=1.3)
        S = self._prep(P, grade, pressure, width, taper, False, wobble, fade=fade)
        Q, w, v = S
        if lost > 0:
            n = len(Q)
            g = (fbm1d(n, max(6, n / 5), 3, self._seed()) + 1) / 2
            v = v * (0.08 + 0.92 * smoothstep(lost - 0.12, lost + 0.12, g))
        if weight is not None:
            ix = np.clip(Q[:, 0].astype(int), 0, self.W - 1); iy = np.clip(Q[:, 1].astype(int), 0, self.H - 1)
            k = weight[iy, ix]
            v = v * (0.6 + 0.65 * k); w = w * (0.85 + 0.55 * k)
        cov, sl = self._raster([(Q, w, v)])
        if sl is not None: self._deposit(cov, sl, grade, gain=gain)

    def guide(self, p0, p1, grade='2H', pressure=0.35, overshoot=(20, 60), wobble=0.25):
        """a long light construction line that overshoots both ends (perspective line, plumb line, horizon)"""
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
        d = p1 - p0; L = np.linalg.norm(d) + 1e-6; d /= L
        a = p0 - d * self.rng.uniform(*overshoot); b = p1 + d * self.rng.uniform(*overshoot)
        P = _resample(np.array([a, b]), 4.0)
        Q, w, v = self._prep(P, grade, pressure, None, (0.05, 0.08), False, wobble, swell=0.3)
        cov, sl = self._raster([(Q, w, v)])
        if sl is not None: self._deposit(cov, sl, grade, gain=1.3)

    def guide_ellipse(self, cx, cy, rx, ry=None, rot=0.0, loops=2, grade='2H', pressure=0.32, axes=True):
        """an ellipse blocked in the way a hand does it: two or three loose loops, plus its axes"""
        ry = rx if ry is None else ry
        for k in range(loops):
            a0 = self.rng.uniform(0, 360)
            drx, dry = self.rng.normal(0, 0.012) * rx, self.rng.normal(0, 0.012) * ry
            P = self.circle_pts(cx + self.rng.normal(0, 1.2), cy + self.rng.normal(0, 1.2), rx + drx, ry + dry, a0, a0 + self.rng.uniform(330, 400), rot)
            self.strokes([P], grade, pressure, None, (0.08, 0.12), 0.6, smooth=False, gain=1.3)
        if axes:
            a = np.deg2rad(rot); u = np.array([np.cos(a), np.sin(a)]); v = np.array([-np.sin(a), np.cos(a)])
            c = np.array([cx, cy])
            self.guide(c - u * rx * 1.08, c + u * rx * 1.08, grade, pressure * 0.8, (4, 14))
            self.guide(c - v * ry * 1.08, c + v * ry * 1.08, grade, pressure * 0.8, (4, 14))

    # ------------------------------------------------------------ hatching
    def _tone(self, mask, tone, finish):
        M = np.asarray(mask, np.float32)
        T = M * (tone if np.ndim(tone) else np.float32(tone))
        if finish: T = T * self.finish ** 0.6
        return T

    def hatch(self, mask, tone=0.5, angle=60.0, grade='2B', spacing=4.2, length=(36, 80), layers=(0, 0, 58, -38),
              pressure=0.62, width=None, bow=0.05, finish=True, zigzag=0.0, jitter=1.6, edge=0.6):
        """patches of parallel strokes, built up in layers. `tone` (number or field) 0 paper .. 1 darkest; layer k
        of `layers` (angle offsets; a repeated angle interleaves between the earlier lines) is laid only where
        tone > k / len(layers), and its strokes press harder where the tone is darker.
        `zigzag` (0..1): share of strokes laid back-and-forth as one connected scribble."""
        T = self._tone(mask, tone, finish)
        sl = self._mask_box(T, pad=2, thr=0.02)
        if sl is None: return
        y0, x0 = sl[0].start, sl[1].start
        Tb = T[sl]
        h, w = Tb.shape
        n_l = len(layers)
        seen = {}
        cx, cy = x0 + w / 2, y0 + h / 2
        corners = np.array([[x0, y0], [x0 + w, y0], [x0, y0 + h], [x0 + w, y0 + h]], np.float32) - [cx, cy]
        r = self.rng
        for k, off in enumerate(layers):
            lo = k / n_l
            Wk = smoothstep(lo, lo + 1.0 / n_l, Tb)
            if Wk.max() < 0.02: continue
            ang = np.deg2rad(angle + off + r.normal(0, 2.5))
            d = np.array([np.cos(ang), np.sin(ang)], np.float32)
            nv = np.array([-np.sin(ang), np.cos(ang)], np.float32)
            rep = seen.get(off, 0); seen[off] = rep + 1
            phase = (0.5 if rep % 2 else 0.0) * spacing
            on, od = corners @ nv, corners @ d
            Lb = r.uniform(*length)
            ucut = od.min() + r.uniform(0, Lb)
            k0, k1 = int(np.floor((od.min() - ucut) / Lb)) - 1, int(np.ceil((od.max() - ucut) / Lb)) + 1
            sign = 1 if r.random() < 0.5 else -1
            c = np.array([cx, cy], np.float32)
            S = []                                           # (points, row, patch, weight)
            o = on.min() + phase + r.uniform(0, spacing * 0.3)
            row = 0
            drift = r.normal(0, Lb * 0.05, k1 - k0 + 2)          # the seams between patches wander a little
            while o < on.max():
                drift += r.normal(0, Lb * 0.012, len(drift))
                cuts = ucut + Lb * np.arange(k0, k1 + 2) + drift + r.normal(0, Lb * 0.03, len(drift))
                for j in range(len(cuts) - 1):
                    s0, s1 = cuts[j] - r.uniform(-1.5, 3.0), cuts[j + 1] + r.uniform(-1.5, 3.5)
                    if s1 - s0 < 4 or s1 < od.min() or s0 > od.max(): continue
                    wm = 0.0
                    for q in (0.5, 0.2, 0.8):
                        p = c + nv * o + d * (s0 + (s1 - s0) * q)
                        jx, jy = int(p[0]) - x0, int(p[1]) - y0
                        if 0 <= jx < w and 0 <= jy < h: wm = max(wm, Wk[jy, jx])
                    if wm <= r.uniform(0.0, 0.3): continue
                    if finish:                                   # toward the unfinished margin whole strokes drop out
                        p = c + nv * o + d * (s0 + s1) / 2
                        fm = self.finish[int(np.clip(p[1], 0, self.H - 1)), int(np.clip(p[0], 0, self.W - 1))]
                        if fm < r.uniform(0.05, 0.85): continue
                    tt = np.linspace(0, 1, 6, dtype=np.float32)[:, None]
                    bend = sign * bow * (s1 - s0) * r.uniform(0.6, 1.3)
                    base = c + nv * (o + r.normal(0, jitter * 0.25))
                    P = base + d * (s0 + (s1 - s0) * tt) + nv * (4 * tt * (1 - tt) * bend)
                    S.append((P, row, j, 0.55 + 0.45 * wm))
                o += spacing * r.uniform(0.86, 1.14)
                row += 1
            if not S: continue
            if zigzag:
                # neighbouring rows of one patch laid back-and-forth without lifting the pencil
                by = {}
                for P, rw, j, pw in S: by.setdefault(j, []).append((rw, P, pw))
                prepped = []
                for j, lst in by.items():
                    lst.sort(key=lambda e: e[0])
                    chain, last = [], None
                    for rw, P, pw in lst:
                        if chain and rw == last + 1 and r.random() < zigzag and len(chain) < 8:
                            chain.append((P if len(chain) % 2 == 0 else P[::-1], pw))
                        else:
                            if chain: prepped.append(chain)
                            chain = [(P, pw)]
                        last = rw
                    if chain: prepped.append(chain)
                prepped = [self._prep(np.concatenate([q[0] for q in ch]), grade, pressure * float(np.mean([q[1] for q in ch])),
                                      width, (0.04, 0.08), True, 0.3, step=2.0, swell=0.15) for ch in prepped]
            else:
                prepped = [self._prep(P, grade, pressure * pw * r.uniform(0.9, 1.08), width, (0.07, 0.2), False, 0.25, step=3.0, swell=0.1)
                           for P, rw, j, pw in S]
            cov, ssl = self._raster(prepped)
            if ssl is None: continue
            clip = np.zeros((self.H, self.W), np.float32)
            clip[sl] = np.clip(Wk * (1.0 / max(edge, 0.05)), 0, 1)
            self._deposit(cov, ssl, grade, clip)

    def contour_hatch(self, lines, mask=None, tone=1.0, grade='2B', pressure=0.6, width=None, finish=True, taper=(0.15, 0.3), gain=1.3):
        """strokes that follow the form (given as polylines), kept only where mask x tone is, pressing harder
        where the tone is darker"""
        M = np.ones((self.H, self.W), np.float32) if mask is None else mask
        T = self._tone(M, tone, finish)
        S = []
        for p in lines:
            Q, w, v = self._prep(p, grade, pressure, width, taper, False, 0.3, swell=0.15)
            ix = np.clip(Q[:, 0].astype(int), 0, self.W - 1); iy = np.clip(Q[:, 1].astype(int), 0, self.H - 1)
            v = v * (0.35 + 0.65 * np.clip(T[iy, ix] * 1.3, 0, 1)) * (T[iy, ix] > 0.02)
            S.append((Q, w, v))
        cov, sl = self._raster(S)
        if sl is not None: self._deposit(cov, sl, grade, np.clip(T * 3, 0, 1), gain=gain)

    def shade(self, mask, tone=0.5, angle=20.0, grade='4B', width=9.0, spacing=None, length=(120, 260), pressure=0.32,
              finish=True, passes=3):
        """the side of a blunt soft lead: broad, soft-edged strokes at light pressure, laid in overlapping passes
        at slightly different angles. The lead only grazes the tooth peaks, so it leaves an even, grainy grey
        with the white valleys showing -- the base tone before smudging. Darker tone = harder pressure"""
        T = self._tone(mask, tone, finish)
        sl = self._mask_box(T, pad=int(width), thr=0.02)
        if sl is None: return
        spacing = spacing or width * 0.42
        y0, x0 = sl[0].start, sl[1].start
        Tb = T[sl]; h, w = Tb.shape
        cx, cy = x0 + w / 2, y0 + h / 2
        corners = np.array([[x0, y0], [x0 + w, y0], [x0, y0 + h], [x0 + w, y0 + h]], np.float32) - [cx, cy]
        r = self.rng
        clip = np.zeros((self.H, self.W), np.float32); clip[sl] = Tb
        for p in range(passes):
            ang = np.deg2rad(angle + r.normal(0, 4) + (p - (passes - 1) / 2) * 11)
            d = np.array([np.cos(ang), np.sin(ang)], np.float32); nv = np.array([-np.sin(ang), np.cos(ang)], np.float32)
            on, od = corners @ nv, corners @ d
            S = []
            o = on.min() + r.uniform(0, spacing)
            while o < on.max():
                u = od.min() - r.uniform(0, length[1])
                while u < od.max():
                    L = r.uniform(*length)
                    tt = np.linspace(0, 1, 8, dtype=np.float32)[:, None]
                    P = np.array([cx, cy]) + nv * o + d * (u + L * tt) + nv * (4 * tt * (1 - tt) * r.normal(0, L * 0.03))
                    if finish:                                   # toward the unfinished margin whole strokes drop out
                        pm = P[4]
                        fm = self.finish[int(np.clip(pm[1], 0, self.H - 1)), int(np.clip(pm[0], 0, self.W - 1))]
                        if fm < r.uniform(0.02, 0.7):
                            u += L * r.uniform(0.6, 0.85); continue
                    S.append(self._prep(P, grade, pressure * r.uniform(0.88, 1.08), width * r.uniform(0.9, 1.1), (0.12, 0.16), False, 0.6, step=8.0, swell=0.12))
                    u += L * r.uniform(0.6, 0.85)
                o += spacing * r.uniform(0.85, 1.15)
            cov, ssl = self._raster(S)
            if ssl is None: continue
            cov = blur(cov, width * 0.22)                                   # the flat of the lead has soft edges
            self._deposit(cov, ssl, grade, clip, polish=0.3)

    # ------------------------------------------------------------ stump and erasers
    def smudge(self, mask, amount=0.7, radius=4.0, direction=None, length=0.0, pickup=0.06, finish=True, contain=True):
        """blending stump / finger: graphite pushed into the valleys and sideways (blur), optionally dragged
        `length` px toward `direction` (degrees); a little is picked up. contain=True keeps the stump inside the
        mask (graphite from outside is not dragged in and the area does not pale against an untouched neighbour)"""
        M = np.asarray(mask, np.float32) * (self.finish if finish else 1)
        pad = int(radius * 3 + length + 4)
        sl = self._mask_box(M, pad=pad, thr=0.01)
        if sl is None: return
        src = self.m[sl]
        Mw = (np.asarray(mask, np.float32)[sl] > 0.3).astype(np.float32) if contain else None

        def drag(a):
            if direction is None or length <= 0: return a
            ang = np.deg2rad(direction); acc = np.zeros_like(a); n = max(2, int(length / 2))
            for k in range(n):
                t = k / (n - 1) * length
                dx, dy = int(round(np.cos(ang) * t)), int(round(np.sin(ang) * t))
                acc += np.pad(a, ((max(dy, 0), max(-dy, 0)), (max(dx, 0), max(-dx, 0))), mode='edge')[
                    max(-dy, 0):max(-dy, 0) + a.shape[0], max(-dx, 0):max(-dx, 0) + a.shape[1]]
            return acc / n
        if contain:
            sm = blur(drag(src * Mw), radius) / np.maximum(blur(drag(Mw), radius), 1e-3)
        else:
            sm = blur(drag(src), radius)
        Mb = M[sl] * amount
        self.m[sl] = (src + Mb * (sm - src)) * (1 - pickup * M[sl])
        self.b[sl] = blur(self.b[sl], radius * 0.5) * (1 - 0.5 * Mb) + self.b[sl] * 0.5 * Mb

    def lift(self, mask, amount=0.7):
        """kneaded eraser dabbed on: pulls graphite off softly (highlights, glints, the lit side of a form)"""
        M = np.asarray(mask, np.float32)
        sl = self._mask_box(M, pad=1, thr=0.005)
        if sl is None: return
        k = 1 - amount * M[sl]
        self.m[sl] *= k; self.b[sl] *= k

    def erase(self, pts, width=4.0, amount=0.88, smooth=False, soft=0.5):
        """hard eraser edge: a crisp white line through tone; a ghost of what was there stays"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 8)
        P = _resample(P, 2.0)
        v = np.full(len(P), 1.0, np.float32); w = np.full(len(P), width, np.float32)
        cov, sl = self._raster([(P, w, v)])
        if sl is None: return
        if soft: cov = blur(cov, soft)
        k = 1 - amount * cov
        self.m[sl] *= k; self.b[sl] *= k

    # ------------------------------------------------------------ margins and accidents
    def write(self, s, x, y, size=30, grade='HB', pressure=0.75, rot=0.0, font='hand', anchor='la'):
        """pencil handwriting: glyphs as graphite, through the tooth, with a slight wobble of pressure"""
        f = load_font(font, size)
        M = text_mask(self.H, self.W, s, f, (x, y), anchor=anchor, rot=rot)
        sl = self._mask_box(M, pad=2, thr=0.02)
        if sl is None: return
        cov = blur(M[sl], 0.45) * pressure * (0.8 + 0.4 * noise2d(sl[0].stop - sl[0].start, sl[1].stop - sl[1].start, 30, 2, self._seed()))
        self._deposit(cov, sl, grade)

    def value_scale(self, x, y, w=62, h=40, grades=('2H', 'HB', '2B', '4B', '6B', '8B'), gap=8, label_size=20):
        """the strip of swatches an artist scribbles in the margin to try the pencils: one grade per box, labelled"""
        for i, gname in enumerate(grades):
            x0 = x + i * (w + gap)
            m = self.rect(x0, y, x0 + w, y + h, 0.5)
            self.hatch(m, 0.9, angle=self.rng.uniform(48, 62), grade=gname, spacing=2.8, length=(w * 0.9, w * 1.3),
                       layers=(0, 0), pressure=0.95, finish=False, zigzag=0.9, edge=0.3)
            self.write(gname, x0 + w / 2, y + h + 8, label_size, '2B', 0.95, anchor='mt')

    def fingerprint(self, x, y, r=26, rot=20.0, amount=0.16, period=2.6):
        """a graphite thumbprint: whorled ridges inside an oval, strongest in the middle"""
        sl = self._box(x - r * 1.6, y - r * 1.6, x + r * 1.6, y + r * 1.6)
        if sl is None: return
        yy, xx = np.mgrid[sl].astype(np.float32)
        a = np.deg2rad(rot); c, s = np.cos(a), np.sin(a)
        u, v = (xx - x) * c + (yy - y) * s, -(xx - x) * s + (yy - y) * c
        rr = np.hypot(u / 0.72, v)
        wob = (noise2d(yy.shape[0], yy.shape[1], 14, 2, self._seed()) - 0.5) * 6
        ridge = 0.5 + 0.5 * np.sin(2 * np.pi * (rr + wob + 0.12 * u) / period)
        env = np.clip(1 - rr / r, 0, 1) ** 0.7 * (0.6 + 0.4 * noise2d(yy.shape[0], yy.shape[1], 20, 2, self._seed()))
        self.m[sl] += amount * ridge ** 1.5 * env

    def smear(self, pts, width=60.0, amount=0.05):
        """the grey haze where the side of the hand dragged across the sheet"""
        M = self.band(pts, width, feather=width * 0.35)
        sl = self._mask_box(M, pad=1, thr=0.01)
        if sl is None: return
        h, w = M[sl].shape
        self.m[sl] += amount * M[sl] * (0.5 + noise2d(h, w, 40, 3, self._seed()))

    # ------------------------------------------------------------ output
    def composite(self):
        D = self.dmax * (1 - np.exp(-self.m))
        g = np.array(GRAPHITE, np.float32)
        img = self.base * (1 - D[..., None]) + g * D[..., None]
        pol = smoothstep(0.25, 1.6, self.b) * D
        H, W = self.H, self.W
        YY, XX = self._grid()
        glare = 0.6 + 0.4 * (1 - (XX / W * 0.5 + YY / H * 0.5))
        img = img + (np.array(SHEEN, np.float32) - img) * (pol * 0.16 * glare)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
