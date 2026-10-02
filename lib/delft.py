"""delft — a wall of Delftware: hand-painted cobalt tiles in tin glaze, with a tile picture (tableau)
set among single tiles (numpy + Pillow only).

Model — the way a Dutch tile wall of about 1650–1800 was made, step by step:
  biscuit   every tile is a square of buff earthenware (about 13 cm, so `tile` px on the wall) dipped in a
            tin glaze: opaque white, a little cool or a little creamy from batch to batch; the glaze runs thin
            and round over the edges.
  pounce    the design comes from a pricked paper pattern (the spons): charcoal dust tapped through the holes
            leaves dotted outlines on the raw glaze. `trek()` records those dots; they burn off in the kiln.
  trek      the outline painter follows the dots with a long fine brush: fluent lines of nearly even width,
            a small bead where the brush lands, a taper where it lifts, a slow hand wobble.
  wash      a second hand floods areas with diluted cobalt. Raw glaze is powdery and drinks the water at
            once, so a wash cannot be blended: it shows the bands of the brush, bristle streaks, a darker rim
            where the water dried last, overlaps that darken, and it never sits exactly inside the outline.
            A blue ground painted round a shape leaves that shape white (`reserve` / `holes=`).
  occlusion one transparent pigment, so the painter leaves out what is hidden: draw front to back and call
            `occlude()` with the silhouette of whatever stands in front; later strokes skip it.
  raw/fired unfired pigment is dull grey-black on a matte chalky glaze; in the kiln the glaze melts and turns
            glossy, cobalt develops into blue (pale where thin, deep violet-blue where thick, Beer–Lambert
            absorption per channel) and sinks into the glaze with a soft bleed.
  tile by tile  each tile is painted and fired on its own, so in a tableau the lines step a pixel or two at
            every joint, and every tile has its own white and its own strength of blue.
  wall      tiles set in lime mortar on a grid that is never quite straight; every tile a little warped and
            tilted, so a window reflects as broken, bent pieces and the rounded edges catch the light.
  age       crazing (a fine crack network with dirt in it), pinholes and iron specks, chipped corners that
            show the buff body, nail holes near the corners from the trimming template, a cracked tile.

    from delft import DelftTile
    t = DelftTile(1920, 1080, tile=128, joint=3.6, origin=(0, -36), seed=7)
    R = t.tableau(2, 1, 13, 8)                       # tiles i 2..12, k 1..7 carry one continuous picture
    t.layer('picture')                               # front to back: draw, then occlude() what stands in front
    t.tulip(400, 900, 50, lean=0.3)                  # Delft vocabulary: windmill, sailboat, house, tree, bushes,
    t.windmill(455, 560, 232, sails=0.42)            #   tulip, cloud, birds, water, reflection, grass, smoke
    t.cloud(1000, 215, 430, 120)
    t.trek(points, 2.0); t.wash(polygon, tone=0.2, angle=0.0); t.hatch(polygon, angle=1.2, spacing=4)
    t.layer('frame'); t.border(R)                    # painted frame with a reserved white vine
    t.layer('single'); t.field(corners='spin')       # every other tile: corner quarters + medallion + motif
    t.stage('outline', hide=('wash', 'single'))      # replay the workshop: hide layers or kinds
    t.fire(); t.set_wall(); t.age(); t.light(window=(1752, 318, 150, 200))
    t.save('out.jpg')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, shift, load_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


COBALT_K = np.array([2.3, 1.95, 0.95], np.float32)   # fired cobalt in tin glaze: absorbs red/green, passes blue
RAW_K = np.array([1.62, 1.68, 1.66], np.float32)      # unfired pigment: dull grey-black
GLAZE_COOL, GLAZE_WARM, RAW_GLAZE = '#f1f2ed', '#f4ecdb', '#e6e0d5'
MORTAR, BED, BODY = '#d2ccbe', '#5d564e', '#caa086'


def _resample(P, step):
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = float(s[-1])
    n = max(2, int(L / step) + 1)
    u = np.linspace(0, L, n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1).astype(np.float32), L


def _normals(P):
    tg = np.gradient(P, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
    return np.stack([-tg[:, 1], tg[:, 0]], 1)


def arc(cx, cy, rx, ry, a0, a1, n=24, rot=0.0):
    """points on an elliptical arc, angles in radians (y down: 0 = right, pi/2 = down)"""
    t = np.linspace(a0, a1, n)
    x, y = np.cos(t) * rx, np.sin(t) * ry
    c, s = np.cos(rot), np.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1)


def ellipse_pts(cx, cy, rx, ry, rot=0.0, n=48):
    return arc(cx, cy, rx, ry, 0, 2 * np.pi, n + 1, rot)[:-1]


def _lerp(p, q, t):
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


class DelftTile:
    def __init__(self, W=1920, H=1080, seed=0, tile=128, joint=3.6, origin=(0, 0), ss=3,
                 glaze=(GLAZE_COOL, GLAZE_WARM), mortar=MORTAR, light=(-0.5, -0.6, 0.63)):
        self.W, self.H, self.p, self.joint, self.ss = W, H, float(tile), float(joint), ss
        self.ox, self.oy = float(origin[0]), float(origin[1])
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.Lv = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.glaze_cols = (_c(glaze[0]), _c(glaze[1]))
        self.mortar = _c(mortar)
        self.layers, self.order, self.cur = {}, [], None
        self.P = np.zeros((H, W), np.float32)               # pounce dots (charcoal)
        self.occ = np.zeros((H, W), np.float32)             # reserved (already painted in front)
        self.tabs = []
        self.fired = self.grouted = False
        self.aged = None
        self.window = None
        self.stages = []
        self._fine = noise2d(H, W, 5, 2, self._seed())
        self._grid()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ the grid of tiles
    def _grid(self):
        p, r = self.p, self.rng
        self.i0 = int(np.floor(-self.ox / p)) - 1
        self.k0 = int(np.floor(-self.oy / p)) - 1
        ni = int(np.ceil((self.W - self.ox) / p)) - self.i0 + 2
        nk = int(np.ceil((self.H - self.oy) / p)) - self.k0 + 2
        sh = (nk, ni)
        self.jx = np.clip(r.normal(0, 0.55, sh), -1.3, 1.3).astype(np.float32)   # set a little off the grid
        self.jy = np.clip(r.normal(0, 0.55, sh), -1.3, 1.3).astype(np.float32)
        self.sz = np.clip(r.normal(0, 0.45, sh), -0.9, 0.9).astype(np.float32)   # hand-trimmed size
        self.warm = r.beta(2.0, 3.2, sh).astype(np.float32)                       # glaze batch: cool .. creamy
        self.bright = r.normal(1.0, 0.011, sh).astype(np.float32)
        self.strength = np.clip(r.normal(1.0, 0.075, sh), 0.85, 1.16).astype(np.float32)  # kiln position
        self.pdx = np.clip(np.round(r.normal(0, 1.05, sh)), -2, 2).astype(np.int32)       # painted on its own
        self.pdy = np.clip(np.round(r.normal(0, 1.05, sh)), -2, 2).astype(np.int32)
        self.tx = r.normal(0, 0.0048, sh).astype(np.float32)                      # set slightly tilted
        self.ty = r.normal(0, 0.0048, sh).astype(np.float32)
        self.warp = r.normal(0.25, 0.3, sh).astype(np.float32)                    # px; + = cushioned
        self.craze = r.beta(1.0, 2.6, sh).astype(np.float32)
        ci = np.floor((self.XX - self.ox) / p).astype(np.int32) - self.i0
        ck = np.floor((self.YY - self.oy) / p).astype(np.int32) - self.k0
        self.ci, self.ck = ci, ck
        cx = self.ox + (ci + self.i0) * p + p / 2 + self.jx[ck, ci]
        cy = self.oy + (ck + self.k0) * p + p / 2 + self.jy[ck, ci]
        lx, ly = self.XX - cx, self.YY - cy
        hs = (p - self.joint) / 2 + self.sz[ck, ci]
        rc = 2.4
        qx, qy = np.abs(lx) - (hs - rc), np.abs(ly) - (hs - rc)
        sdf = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rc
        edge = noise2d(self.H, self.W, 9, 2, self._seed())
        sdf = sdf + (edge - 0.5) * 1.1                                                # hand-cut, wavy edge
        self.sdf = sdf.astype(np.float32)
        self.inside = np.clip(0.5 - sdf, 0, 1).astype(np.float32)
        self.lx, self.ly, self.hs = lx, ly, hs
        # glaze surface (px): rounded edge + cushion + tilt + orange peel
        bev, bh = 3.4, 1.3
        e = np.clip(-sdf / bev, 0, 1)
        h = bh * np.sqrt(1 - (1 - e) ** 2)
        u, v = lx / hs, ly / hs
        wav = noise2d(self.H, self.W, 46, 2, self._seed()) - 0.5                    # glaze runs a little uneven
        body = self.warp[ck, ci] * (1 - 0.5 * (u * u + v * v)) + self.tx[ck, ci] * lx + self.ty[ck, ci] * ly + 0.3 * wav
        self.h = (h + body * smoothstep(0, 1, e)).astype(np.float32)
        Yi = np.clip(self.YY.astype(np.int32) - self.pdy[ck, ci], 0, self.H - 1)
        Xi = np.clip(self.XX.astype(np.int32) - self.pdx[ck, ci], 0, self.W - 1)
        self.Yi, self.Xi = Yi, Xi
        self.is_tab = np.zeros(sh, bool)

    def rect(self, i, k):
        """nominal glazed face of tile (i, k): (x0, y0, x1, y1)"""
        p, j = self.p, self.joint / 2
        x0, y0 = self.ox + i * p, self.oy + k * p
        return x0 + j, y0 + j, x0 + p - j, y0 + p - j

    def centre(self, i, k):
        x0, y0, x1, y1 = self.rect(i, k)
        return (x0 + x1) / 2, (y0 + y1) / 2

    def visible(self):
        """every tile index (i, k) that shows on the canvas"""
        p = self.p
        out = []
        for k in range(int(np.floor(-self.oy / p)), int(np.ceil((self.H - self.oy) / p))):
            for i in range(int(np.floor(-self.ox / p)), int(np.ceil((self.W - self.ox) / p))):
                out.append((i, k))
        return out

    def tableau(self, i0, k0, i1, k1):
        """tiles i0 <= i < i1, k0 <= k < k1 carry one continuous picture; returns its outer rect in px"""
        self.tabs.append((i0, k0, i1, k1))
        self.is_tab[k0 - self.k0:k1 - self.k0, i0 - self.i0:i1 - self.i0] = True
        return (self.ox + i0 * self.p, self.oy + k0 * self.p, self.ox + i1 * self.p, self.oy + k1 * self.p)

    def in_tableau(self, i, k):
        return any(a <= i < c and b <= k < d for a, b, c, d in self.tabs)

    # ------------------------------------------------------------ paint layers
    def layer(self, name):
        """draw into a named pigment layer; every layer keeps its outlines ('trek') and washes ('wash') apart,
        so stages can replay the painting order (hide 'sky', 'wash', 'sky.wash', ...)"""
        for kind in ('trek', 'wash'):
            if (name, kind) not in self.layers:
                self.layers[(name, kind)] = np.zeros((self.H, self.W), np.float32)
                self.order.append((name, kind))
        self.cur = name

    def occlude(self, shape, grow=1.0):
        """reserve a silhouette: later strokes and washes leave it unpainted (draw front to back)"""
        x0, y0, m = self._mask_local(shape, pad=3)
        if m is None: return
        if grow: m = np.clip(blur(m, grow) * 2.2, 0, 1)
        sl = self.occ[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
        np.maximum(sl, m[:sl.shape[0], :sl.shape[1]], out=sl)

    def clear_occlusion(self):
        self.occ[:] = 0

    def _add(self, x0, y0, arr, mode):
        if self.cur is None: self.layer('paint')
        h, w = arr.shape
        xa, ya, xb, yb = max(0, x0), max(0, y0), min(self.W, x0 + w), min(self.H, y0 + h)
        if xa >= xb or ya >= yb: return
        sub = arr[ya - y0:yb - y0, xa - x0:xb - x0] * (1 - self.occ[ya:yb, xa:xb])
        L = self.layers[(self.cur, 'trek' if mode == 'trek' else 'wash')][ya:yb, xa:xb]
        if mode == 'trek':
            L += sub * (1 - 0.6 * np.clip(L, 0, 1))      # crossing lines darken a little, not double
        else:
            L += sub

    def _mask_local(self, shape, pad=4, holes=None):
        """polygon / list of polygons / full-size mask -> (x0, y0, local AA mask)"""
        if isinstance(shape, np.ndarray) and shape.ndim == 2 and shape.shape == (self.H, self.W):
            ys, xs = np.nonzero(shape > 0.01)
            if len(xs) == 0: return 0, 0, None
            x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
            x1, y1 = min(self.W, xs.max() + pad + 1), min(self.H, ys.max() + pad + 1)
            m = shape[y0:y1, x0:x1].astype(np.float32)
            if holes is not None:
                _, _, hm = self._poly_raster(holes, x0, y0, x1, y1)
                m = m * (1 - hm)
            return x0, y0, m
        polys = [np.asarray(shape, np.float32)] if np.asarray(shape[0]).ndim == 1 else [np.asarray(q, np.float32) for q in shape]
        allp = np.vstack(polys)
        x0 = int(max(0, np.floor(allp[:, 0].min()) - pad)); y0 = int(max(0, np.floor(allp[:, 1].min()) - pad))
        x1 = int(min(self.W, np.ceil(allp[:, 0].max()) + pad + 1)); y1 = int(min(self.H, np.ceil(allp[:, 1].max()) + pad + 1))
        if x1 - x0 < 2 or y1 - y0 < 2: return 0, 0, None
        _, _, m = self._poly_raster(polys, x0, y0, x1, y1)
        if holes is not None:
            _, _, hm = self._poly_raster(holes, x0, y0, x1, y1)
            m = m * (1 - hm)
        return x0, y0, m

    def _poly_raster(self, polys, x0, y0, x1, y1, ss=2):
        if len(polys) and np.asarray(polys[0]).ndim == 1: polys = [polys]
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        d = ImageDraw.Draw(im)
        for q in polys:
            q = np.asarray(q, np.float32)
            if len(q) >= 3:
                d.polygon([((x - x0) * ss, (y - y0) * ss) for x, y in q], fill=255)
        a = np.asarray(im, np.float32).reshape(y1 - y0, ss, x1 - x0, ss).mean(axis=(1, 3)) / 255
        return x0, y0, a

    # ------------------------------------------------------------ brushes
    def _pounce(self, P):
        Q, L = _resample(P, 3.3)
        Q = Q + self.rng.normal(0, 0.35, Q.shape)
        v = self.rng.uniform(0.45, 0.95, len(Q)).astype(np.float32)
        ix, iy = np.floor(Q[:, 0]).astype(int), np.floor(Q[:, 1]).astype(int)
        fx, fy = Q[:, 0] - ix, Q[:, 1] - iy
        for dx, dy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
            xx, yy = ix + dx, iy + dy
            ok = (xx >= 0) & (yy >= 0) & (xx < self.W) & (yy < self.H)
            np.add.at(self.P, (yy[ok], xx[ok]), (v * wgt)[ok])

    def _raster(self, P, w, d):
        ss = self.ss
        pad = float(w.max()) + 3
        x0 = int(np.floor(P[:, 0].min() - pad)); y0 = int(np.floor(P[:, 1].min() - pad))
        x1 = int(np.ceil(P[:, 0].max() + pad)); y1 = int(np.ceil(P[:, 1].max() + pad))
        x0, y0 = max(x0, -8), max(y0, -8)
        x1, y1 = min(x1, self.W + 8), min(y1, self.H + 8)
        if x1 - x0 < 1 or y1 - y0 < 1: return x0, y0, np.zeros((1, 1), np.float32)
        im = Image.new('F', ((x1 - x0) * ss, (y1 - y0) * ss), 0.0)
        dr = ImageDraw.Draw(im)
        Q = (P - np.array([x0, y0], np.float32)) * ss
        nr = _normals(Q)
        hw = w * ss / 2
        Lp, Rp = Q + nr * hw[:, None], Q - nr * hw[:, None]
        n, step = len(Q), 5
        for a in range(0, n - 1, step):
            b = min(n - 1, a + step)
            poly = [tuple(q) for q in Lp[a:b + 1]] + [tuple(q) for q in Rp[a:b + 1][::-1]]
            dr.polygon(poly, fill=float(d[a:b + 1].mean()))
        for a in list(range(0, n, step)) + [n - 1]:
            r = hw[a]
            if r > 0.3:
                dr.ellipse([Q[a, 0] - r, Q[a, 1] - r, Q[a, 0] + r, Q[a, 1] + r], fill=float(d[a]))
        arr = np.asarray(im, np.float32).reshape(y1 - y0, ss, x1 - x0, ss).mean(axis=(1, 3))
        return x0, y0, arr

    def trek(self, pts, width=2.2, dens=1.0, taper=(0.1, 0.3), wobble=0.75, smooth=True, pounce=True, bead=0.22, step=1.2):
        """an outline stroke with the fine trek brush (width px, dens = pigment load, ~1 for outlines)"""
        P = np.asarray(pts, np.float32)
        if len(P) < 2: return
        if smooth and len(P) >= 3: P = spline(P, per=8)
        P, L = _resample(P, step)
        if L < 0.6: return
        n = len(P)
        t = np.linspace(0, 1, n, dtype=np.float32)
        if pounce: self._pounce(P)
        sd = self._seed()
        if wobble:
            P = P + _normals(P) * (fbm1d(n, max(4.0, 46 / step), 3, sd) * wobble * min(1.0, L / 40 + 0.35))[:, None]
        tg = np.gradient(P, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        w = width * (0.84 + 0.16 * fbm1d(n, max(3.0, 28 / step), 2, sd + 1)) * (1 + 0.16 * tg[:, 1])   # heavier on the downstroke
        a, b = max(taper[0], 1e-3), max(taper[1], 1e-3)
        w = w * np.clip(np.minimum(0.62 + 0.38 * t / a, 0.2 + 0.8 * (1 - t) / b), 0.2, 1)
        d = dens * (1.07 - 0.14 * t) * (0.93 + 0.07 * fbm1d(n, max(3.0, 20 / step), 2, sd + 2))
        if bead:
            nb = max(2, int(min(n, 4 + n * 0.03)))
            w[:nb] *= 1 + bead; d[:nb] *= 1.08
        x0, y0, arr = self._raster(P, w.astype(np.float32), d.astype(np.float32))
        self._add(x0, y0, arr, 'trek')

    def line(self, p0, p1, width=2.0, dens=1.0, bend=0.0, **kw):
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        if bend:
            m = (p0 + p1) / 2; d = p1 - p0
            m = m + np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6) * bend
            self.trek([p0, m, p1], width, dens, **kw)
        else:
            self.trek([p0, p1], width, dens, smooth=False, **kw)

    def closed(self, pts, width=2.0, dens=1.0, **kw):
        P = np.asarray(pts, np.float32)
        self.trek(np.vstack([P, P[:1]]), width, dens, **kw)

    def dot(self, x, y, r=1.6, dens=1.0):
        self._add(*self._raster(np.array([[x, y], [x + 0.01, y]], np.float32), np.array([2 * r, 2 * r], np.float32),
                                np.array([dens, dens], np.float32)), 'trek')

    def wash(self, shape, tone=0.2, angle=0.0, pool=0.55, ragged=0.3, slip=1.2, band=11.0, streak=0.35,
             grad=None, holes=None, soft=0.7):
        """a flat wash of diluted cobalt (tone ~0.1 pale .. 0.5 dark) over a polygon / polygons / mask.
        angle: brush direction (radians); grad=((x0, y0), (x1, y1), f0, f1) ramps the tone along a line;
        holes: polygons kept white (reserve)."""
        x0, y0, m = self._mask_local(shape, pad=6, holes=holes)
        if m is None: return
        h, w = m.shape
        if soft: m = blur(m, soft)
        if ragged:
            n = self._fine[y0:y0 + h, x0:x0 + w]
            m = smoothstep(0.3, 0.7, m + (n - 0.5) * ragged)
        if slip:
            m = shift(m, self.rng.uniform(-slip, slip), self.rng.uniform(-slip, slip))
        rim = np.clip(m - blur(m, 3.2), 0, 1) * 2.4
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        ca, sa = np.cos(angle), np.sin(angle)
        acr = -xx * sa + yy * ca
        alg = xx * ca + yy * sa
        r = self.rng
        tb = r.random(64).astype(np.float32); tf = r.random(256).astype(np.float32); tl = r.random(64).astype(np.float32)
        bands = np.interp((acr / band + r.uniform(0, 8)) % 63, np.arange(64), tb)
        fine = np.interp((acr / 1.6 + r.uniform(0, 30)) % 255, np.arange(256), tf)
        along = np.interp((alg / 70 + r.uniform(0, 8)) % 63, np.arange(64), tl)
        S = 0.6 * bands + 0.4 * fine * (0.4 + 0.6 * along)
        d = tone * m * (1 - streak * 0.5 + streak * S) * (1 + pool * rim)
        if grad is not None:
            (gx0, gy0), (gx1, gy1), f0, f1 = grad
            vx, vy = gx1 - gx0, gy1 - gy0
            tt = np.clip(((xx + x0 - gx0) * vx + (yy + y0 - gy0) * vy) / (vx * vx + vy * vy + 1e-6), 0, 1)
            d = d * (f0 + (f1 - f0) * tt)
        self._add(x0, y0, d.astype(np.float32), 'wash')

    def hatch(self, shape, angle=0.0, spacing=5.0, width=1.1, dens=0.8, jitter=0.5, shorten=1.5, holes=None, wave=0.0):
        """parallel freehand lines clipped to a shape (shading, sails, thatch, ground)"""
        x0, y0, m = self._mask_local(shape, pad=2, holes=holes)
        if m is None: return
        if self.occ is not None:
            m = m * (1 - self.occ[y0:y0 + m.shape[0], x0:x0 + m.shape[1]])
        h, w = m.shape
        ca, sa = np.cos(angle), np.sin(angle)
        cx, cy = w / 2, h / 2
        R = np.hypot(w, h) / 2 + 2
        tt = np.arange(-R, R, 1.0, dtype=np.float32)
        off = -R + self.rng.uniform(0, spacing)
        while off < R:
            o = off + self.rng.normal(0, jitter)
            px = cx + ca * tt - sa * o; py = cy + sa * tt + ca * o
            ok = (px >= 0) & (py >= 0) & (px < w - 1) & (py < h - 1)
            ins = np.zeros(len(tt), bool)
            ins[ok] = m[py[ok].astype(int), px[ok].astype(int)] > 0.5
            dif = np.diff(np.concatenate([[0], ins.astype(np.int8), [0]]))
            for a, b in zip(np.nonzero(dif == 1)[0], np.nonzero(dif == -1)[0]):
                a2 = a + self.rng.uniform(0, shorten); b2 = b - 1 - self.rng.uniform(0, shorten)
                if b2 - a2 < 2.5: continue
                s = np.linspace(a2, b2, max(2, int((b2 - a2) / 6) + 2))
                sx = np.interp(s, np.arange(len(tt)), px) + x0; sy = np.interp(s, np.arange(len(tt)), py) + y0
                if wave:
                    ph = self.rng.uniform(0, 6.3)
                    k = np.sin(s * 0.25 + ph) * wave
                    sx, sy = sx - sa * k, sy + ca * k
                self.trek(np.stack([sx, sy], 1), width, dens, taper=(0.15, 0.3), wobble=0.35, pounce=False, bead=0.1)
            off += spacing

    def letters(self, s, x, y, size, font='serif', dens=1.0, anchor='mm', spacing=0.0):
        """painted capitals (font outline, softened and wobbled like a brush)"""
        f = load_font(font, size)
        pad = int(size * 0.6)
        tw = int(f.getlength(s) + spacing * len(s)) + 2 * pad
        th = int(size * 1.6) + 2 * pad
        im = Image.new('L', (tw * 2, th * 2), 0)
        d = ImageDraw.Draw(im)
        f2 = load_font(font, size * 2)
        cx = tw; cy = th
        adv = [f2.getlength(ch) + spacing * 2 for ch in s]
        xx = cx - (sum(adv) - spacing * 2) / 2
        for ch, a in zip(s, adv):
            d.text((xx, cy), ch, font=f2, fill=255, anchor='l' + anchor[1]); xx += a
        m = np.asarray(im, np.float32).reshape(th, 2, tw, 2).mean(axis=(1, 3)) / 255
        m = blur(m, 0.5)
        x0, y0 = int(x - tw / 2), int(y - th / 2)
        n = self._fine[max(0, y0):max(0, y0) + th, max(0, x0):max(0, x0) + tw]
        if n.shape == m.shape: m = smoothstep(0.28, 0.72, m + (n - 0.5) * 0.25)
        self._add(x0, y0, (m * dens * (0.95 + 0.1 * (n if n.shape == m.shape else 0.5))).astype(np.float32), 'trek')

    # ------------------------------------------------------------ the Delft vocabulary
    def cloud(self, cx, cy, w, h, lean=0.3, tone=0.14, width=1.8, seed=None):
        """a scalloped cumulus: a dome of bumps (one stroke per bump, cusps between), a flat wavy base,
        a few inner bumps, a pale wash that darkens toward the base. lean > 0: wind from the left
        (the dome sits left of centre, the right end trails off in smaller bumps)."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        base = cy + h * 0.5
        xl, xr = cx - w / 2, cx + w / 2
        n = max(4, int(w / (h * 0.36)))
        u = np.linspace(0, 1, n)
        u = np.clip(u + r.normal(0, 0.15 / n, n), 0, 1)
        peak = 0.5 - lean * 0.22
        env = np.where(u < peak, np.sin(np.pi / 2 * u / peak), np.cos(np.pi / 2 * (u - peak) / (1 - peak))) ** 0.7
        rad = h * (0.2 + 0.26 * env) * r.uniform(0.85, 1.15, n)
        bx = xl + rad[0] * 0.7 + u * (w - rad[0] * 0.7 - rad[-1] * 0.7)
        by = base - h * 0.95 * env + rad * 0.95
        by = np.minimum(by, base - rad * 0.25)
        xx = np.linspace(xl - 2, xr + 2, 360)
        top = np.full_like(xx, base); owner = np.full(len(xx), -1)
        for j in range(n):
            dy = np.sqrt(np.clip(rad[j] ** 2 - (xx - bx[j]) ** 2, 0, None))
            yv = np.where(dy > 0, by[j] - dy, 1e9)
            better = yv < top
            top[better] = yv[better]; owner[better] = j
        ok = top < base - 0.5
        xx, top, owner = xx[ok], top[ok], owner[ok]
        for j in range(n):
            idx = np.nonzero(owner == j)[0]
            if len(idx) < 3: continue
            seg = np.stack([xx[idx], top[idx]], 1)
            self.trek(seg[::2], width, 0.95, taper=(0.06, 0.3))
        k = np.linspace(0, 1, 30)
        bl = np.stack([xx[0] + 4 + (xx[-1] - xx[0] - 8) * k, base + np.sin(k * 9 + r.uniform(0, 6)) * h * 0.03], 1)
        cut = sorted(r.choice(np.arange(6, 24), 2, replace=False))
        for a_, b_ in ((0, cut[0]), (cut[0] + 2, cut[1]), (cut[1] + 2, 30)):
            if b_ - a_ > 2: self.trek(bl[a_:b_], width * 0.75, 0.7, taper=(0.25, 0.35))
        for j in r.choice(np.arange(1, n - 1), size=max(1, (n - 2) // 2), replace=False):
            rr = rad[j] * 0.62
            self.trek(arc(bx[j] + r.normal(0, rr * 0.2), by[j] + rad[j] * 0.5, rr, rr * 0.75, np.pi * 1.08, np.pi * 1.72, 10),
                      width * 0.65, 0.65, taper=(0.15, 0.5), pounce=False)
        poly = np.vstack([np.stack([xx, top], 1)[::3], [[xx[-1], base], [xx[0], base]]])
        mid = base - h * 0.45
        low = np.stack([xx, np.maximum(top, mid + np.sin(xx * 0.035) * h * 0.07)], 1)[::3]
        lower = np.vstack([low, [[xx[-1], base], [xx[0], base]]])
        self.wash(poly, tone * 0.3, angle=0.0, pool=0.35, slip=1.2)
        self.wash(lower, tone * 0.8, angle=0.0, pool=0.45, slip=1.2, ragged=0.5, grad=((cx, mid), (cx, base), 0.3, 1.0))
        for kk in range(3):
            yv = base - 3 - kk * 4.5
            x0_ = xx[0] + w * (0.1 + 0.07 * kk) + r.normal(0, 6)
            x1_ = xx[-1] - w * (0.12 + 0.09 * kk) + r.normal(0, 6)
            self.trek([(x0_, yv), ((x0_ + x1_) / 2, yv - 1.0), (x1_, yv - 0.5)], 0.9, 0.55 - 0.1 * kk, pounce=False, taper=(0.3, 0.4))
        return poly

    def birds(self, pts, size=9.0, width=1.5, tilt=0.15):
        for (x, y) in pts:
            s = size * self.rng.uniform(0.7, 1.15)
            a = tilt + self.rng.normal(0, 0.12)
            c, sn = np.cos(a), np.sin(a)
            L = [(-s, -s * 0.15), (-s * 0.45, -s * 0.5), (0, 0)]
            R = [(0, 0), (s * 0.5, -s * 0.55), (s * 1.05, -s * 0.2)]
            for side in (L, R):
                P = [(x + px * c - py * sn, y + px * sn + py * c) for px, py in side]
                self.trek(P, width, 0.95, taper=(0.1, 0.5), pounce=False)

    def water(self, x0, x1, y0, y1, density=1.0, width=1.5, dens=0.8, far=3.5, near=11.0, avoid=None, waves=0.7):
        """ripples: short wavy dashes, finer and closer together toward the far bank"""
        r = self.rng
        y = y0 + 2
        while y < y1:
            f = (y - y0) / max(1, y1 - y0)
            gap = far + (near - far) * f ** 1.2
            x = x0 + r.uniform(0, 40)
            while x < x1:
                L = r.uniform(10, 26) + f * r.uniform(10, 50)
                if r.random() < 0.62 * density:
                    xs = np.linspace(x, min(x1, x + L), 6)
                    amp = waves * (1 + 2 * f) * r.uniform(0.5, 1.3)
                    ys = y + np.sin(np.linspace(0, np.pi * r.uniform(1.5, 3), 6) + r.uniform(0, 6)) * amp
                    if avoid is None or not np.any(avoid[np.clip(ys.astype(int), 0, self.H - 1), np.clip(xs.astype(int), 0, self.W - 1)] > 0.3):
                        self.trek(np.stack([xs, ys], 1), width * (0.6 + 0.6 * f), dens * r.uniform(0.75, 1.05),
                                  taper=(0.25, 0.4), pounce=False, bead=0.1)
                x += L + r.uniform(8, 30) * (1.4 - f)
            y += gap * r.uniform(0.8, 1.2)

    def reflection(self, x, y, w, depth, step=5.0, width=1.4, dens=0.8):
        """a broken reflection under something standing at the water: stacked short dashes"""
        r = self.rng
        k = 0
        yy = y + 3
        while yy < y + depth:
            f = (yy - y) / depth
            ww = w * (1 - 0.5 * f) * r.uniform(0.6, 1.0)
            xc = x + r.normal(0, 3) + (k % 2) * 3
            self.trek([(xc - ww / 2, yy), (xc + ww / 2, yy + r.normal(0, 0.6))], width, dens * (1 - 0.55 * f),
                      smooth=False, taper=(0.3, 0.3), pounce=False)
            yy += step * (1 + f); k += 1

    def grass(self, x0, x1, y, n=20, h=10.0, lean=0.3, width=1.2, dens=0.85, yspread=0.0):
        r = self.rng
        for _ in range(n):
            x = r.uniform(x0, x1); yb = y + r.uniform(-yspread, yspread) if np.isscalar(y) else np.interp(x, *y)
            if not np.isscalar(y): yb += r.uniform(-yspread, yspread)
            hh = h * r.uniform(0.6, 1.3)
            for k in range(r.integers(2, 5)):
                a = -np.pi / 2 + lean + (k - 1.5) * 0.35 + r.normal(0, 0.12)
                tip = (x + np.cos(a) * hh + lean * hh * 0.4, yb + np.sin(a) * hh)
                mid = (x + np.cos(a) * hh * 0.5, yb + np.sin(a) * hh * 0.55)
                self.trek([(x + k - 1.5, yb), mid, tip], width, dens, taper=(0.05, 0.7), pounce=False, bead=0.05)

    def tulip(self, x, y, h=60.0, lean=0.0, width=1.6, tone=0.22, leaves=2, wash=True):
        """a tulip on its stem (y = ground); lean > 0 bends it to the right"""
        r = self.rng
        top = (x + lean * h * 0.55, y - h)
        stem = [(x, y), (x + lean * h * 0.08, y - h * 0.45), (top[0] - lean * h * 0.08, top[1] + h * 0.2), top]
        s = h * 0.17
        ang = np.arctan2(*(np.array(top) - np.array(stem[2]))[::-1]) + np.pi / 2
        c, sn = np.cos(ang), np.sin(ang)
        def T(px, py): return (top[0] + px * c - py * sn, top[1] + px * sn + py * c)
        cup = [T(-s * 0.95, -s * 0.2), T(-s * 1.05, -s * 1.3), T(-s * 0.45, -s * 0.95), T(0, -s * 1.65),
               T(s * 0.45, -s * 0.95), T(s * 1.05, -s * 1.3), T(s * 0.95, -s * 0.2), T(0, s * 0.35)]
        outline = [cup[7], cup[0], cup[1], cup[2], cup[3], cup[4], cup[5], cup[6], cup[7]]
        self.trek([cup[0], T(-s * 1.05, -s * 0.8), cup[1]], width, taper=(0.1, 0.4))
        self.trek([cup[1], T(-s * 0.55, -s * 0.85), T(-s * 0.1, -s * 0.3)], width * 0.8, 0.8, taper=(0.1, 0.5))
        self.trek([cup[0], T(-s * 0.4, s * 0.3), cup[7], T(s * 0.4, s * 0.3), cup[6]], width)
        self.trek([cup[6], T(s * 1.05, -s * 0.8), cup[5]], width, taper=(0.1, 0.4))
        self.trek([cup[5], T(s * 0.55, -s * 0.85), T(s * 0.1, -s * 0.3)], width * 0.8, 0.8, taper=(0.1, 0.5))
        self.trek([T(-s * 0.5, -s * 0.6), T(-s * 0.2, -s * 1.3), cup[3], T(s * 0.2, -s * 1.3), T(s * 0.5, -s * 0.6)], width * 0.9)
        if wash:
            self.wash([cup[0], cup[1], cup[2], cup[3], cup[4], cup[5], cup[6], T(0, s * 0.35)], tone, angle=ang - np.pi / 2,
                      pool=0.7, slip=0.8, band=5)
            self.wash([T(s * 0.15, -s * 1.2), cup[4], cup[5], cup[6], T(0, s * 0.35)], tone * 0.8, angle=ang, slip=0.6, band=4)
        self.occlude(outline, grow=0.6)
        self.trek(stem, width * 0.95, 0.95, taper=(0.05, 0.1))
        for k in range(leaves):
            side = -1 if k % 2 == 0 else 1
            yb = y - h * (0.05 + 0.18 * k)
            L = h * r.uniform(0.45, 0.6)
            tipx = x + side * L * 0.42 + lean * L * 0.6
            tipy = yb - L
            mid1 = (x + side * L * 0.32 + lean * L * 0.15, yb - L * 0.45)
            self.trek([(x + side, yb), mid1, (tipx, tipy)], width * 0.9, taper=(0.05, 0.6))
            mid2 = (x + side * L * 0.12 + lean * L * 0.3, yb - L * 0.55)
            self.trek([(x + side, yb + 2), mid2, (tipx, tipy)], width * 0.8, 0.85, taper=(0.05, 0.6))
            if wash:
                self.wash([(x + side, yb), mid1, (tipx, tipy), mid2], tone * 0.8, angle=-np.pi / 2, slip=0.7, band=4, pool=0.6)
        return outline

    def _scallops(self, C, clumps, n=220):
        """outer envelope of a union of circles seen from centre C: points, owner index per point"""
        th = np.linspace(-np.pi, np.pi, n, endpoint=False)
        ux, uy = np.cos(th), np.sin(th)
        best = np.zeros(n); own = np.full(n, -1)
        for j, (px, py, rad) in enumerate(clumps):
            dx, dy = px - C[0], py - C[1]
            b = ux * dx + uy * dy
            disc = b * b - (dx * dx + dy * dy - rad * rad)
            tt = np.where(disc >= 0, b + np.sqrt(np.clip(disc, 0, None)), 0)
            better = tt > best
            best[better] = tt[better]; own[better] = j
        return np.stack([C[0] + ux * best, C[1] + uy * best], 1), own, th

    def tree(self, x, y, h=150.0, w=None, lean=0.15, width=1.8, tone=0.2, clumps=7, trunk=None, seed=None):
        """a rounded Dutch tree: a crown of leaf clumps (outer scallops outlined, cusps between), leaf dabs
        crowding on the shade side, a wash dark toward lower right, trunk and forked branches below.
        lean > 0 = wind from the left. Returns the crown polygon."""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        w = w or h * 0.7
        tw = trunk or max(4.0, h * 0.06)
        C = (x + lean * h * 0.3, y - h * 0.6)
        rx, ry = w * 0.5, h * 0.33
        cl = [(C[0], C[1], min(rx, ry) * 0.62)]
        for j in range(clumps - 1):
            a = -np.pi + (j + r.uniform(0.2, 0.8)) * 2 * np.pi / (clumps - 1)
            rr = r.uniform(0.3, 0.42) * min(rx, ry) * 1.5
            px = C[0] + np.cos(a) * (rx - rr * 0.8) + lean * rr * 0.3 * (np.cos(a) > 0)
            py = C[1] + np.sin(a) * (ry - rr * 0.7)
            cl.append((px, py, rr))
        P, own, th = self._scallops(C, cl)
        # outline: one stroke per run of the same clump (lighter along the underside)
        runs, start = [], 0
        for k in range(1, len(own) + 1):
            if k == len(own) or own[k] != own[start]:
                runs.append((start, k)); start = k
        for a0, a1 in runs:
            if a1 - a0 < 3: continue
            seg = P[a0:a1 + 1] if a1 < len(P) else np.vstack([P[a0:a1], P[:1]])
            under = np.mean(np.sin(th[a0:min(a1, len(th) - 1)])) > 0.55
            self.trek(seg[::2] if len(seg) > 7 else seg, width * (0.7 if under else 1.0), 0.65 if under else 0.95, taper=(0.08, 0.3))
        # nested scallop rows inside the crown, on the shade side (light from the upper left)
        for sc in (0.7, 0.42):
            cl2 = [(C[0] + (px - C[0]) * sc + rx * 0.06, C[1] + (py - C[1]) * sc + ry * 0.08, rr * sc) for (px, py, rr) in cl]
            P2, own2, th2 = self._scallops(C, cl2, 160)
            start = 0
            for k in range(1, len(own2) + 1):
                if k == len(own2) or own2[k] != own2[start]:
                    a0, a1 = start, k
                    start = k
                    if a1 - a0 < 4: continue
                    mid = th2[(a0 + a1 - 1) // 2]
                    if not (-0.5 < mid < 2.4) and r.random() < 0.8: continue
                    seg = P2[a0:a1]
                    self.trek(seg[::2] if len(seg) > 7 else seg, width * 0.6, 0.75, taper=(0.15, 0.45), pounce=False)
        # leaf dabs, mostly on the shade side
        for _ in range(int(w * h / 600)):
            a = r.uniform(0, 2 * np.pi); d = np.sqrt(r.uniform(0.05, 0.85))
            ux, uy = C[0] + np.cos(a) * d * rx * 0.85, C[1] + np.sin(a) * d * ry * 0.85
            lit = -(np.cos(a) * 0.6 + np.sin(a) * 0.8) * d
            if lit > 0.15 and r.random() < 0.75: continue
            cc = r.uniform(2.2, 4.2) * (w / 110) ** 0.5
            sa = r.uniform(-0.6, 0.6)
            self.trek(arc(ux, uy, cc, cc * 0.7, 0.3 + sa, 2.7 + sa, 5), width * 0.55, 0.7, taper=(0.1, 0.6), pounce=False)
        poly = P[::2]
        self.wash(poly, tone, angle=0.7, pool=0.6, slip=1.0, band=7, grad=((C[0] - rx, C[1] - ry), (C[0] + rx * 0.6, C[1] + ry), 0.35, 1.4))
        sh = [(px + rx * 0.12, py + ry * 0.14, rr * 0.8) for (px, py, rr) in cl]       # second wash: the shade side
        P3, _, _ = self._scallops((C[0] + rx * 0.12, C[1] + ry * 0.14), sh, 120)
        self.wash(P3, tone * 0.6, angle=0.7, slip=0.8, pool=0.7, band=6, ragged=0.5,
                  grad=((C[0] - rx * 0.5, C[1] - ry * 0.6), (C[0] + rx * 0.5, C[1] + ry * 0.7), 0.0, 1.2))
        self.occlude(poly, grow=1.0)
        # trunk and forked branches, behind the crown
        bend = lean * h * 0.22
        yc = C[1] + ry * 0.4
        self.trek([(x - tw / 2, y), (x - tw * 0.45 + bend * 0.5, y - h * 0.22), (x - tw * 0.3 + bend, yc)], width)
        self.trek([(x + tw / 2, y), (x + tw * 0.5 + bend * 0.5, y - h * 0.22), (x + tw * 0.3 + bend, yc)], width)
        self.hatch([(x - tw / 2, y), (x + tw / 2, y), (x + tw * 0.3 + bend, yc), (x - tw * 0.3 + bend, yc)],
                   angle=-np.pi / 2 + 0.1, spacing=max(2.0, tw / 2.5), width=0.8, dens=0.65)
        for k, side in enumerate((-1, 1, -1)):
            yb = y - h * (0.3 + 0.06 * k)
            xb = x + bend * (0.4 + 0.1 * k)
            self.trek([(xb, yb), (xb + side * w * 0.12 + bend * 0.3, yb - h * 0.1), (xb + side * w * 0.2 + bend * 0.4, yb - h * 0.2)],
                      width * 0.75, 0.9, taper=(0.05, 0.6))
        return poly

    def bushes(self, x0, x1, y, h=14.0, width=1.0, tone=0.14, gap=(), seed=None):
        """a distant row of trees and hedges: little scalloped humps on the horizon with a pale wash"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        x = x0
        while x < x1:
            n = int(r.integers(2, 5))
            cl = []
            for j in range(n):
                rr = h * r.uniform(0.35, 0.6)
                cl.append((x + j * h * 0.55, y - rr * r.uniform(0.6, 1.3), rr))
            xe = x + n * h * 0.55
            if not any(a <= x <= b or a <= xe <= b for a, b in gap):
                C = (x + (n - 1) * h * 0.27, y)
                P, own, th = self._scallops(C, cl, 120)
                top = P[np.sin(th) < -0.02]
                top = top[np.argsort(top[:, 0])]
                if len(top) > 3:
                    self.trek(top[::2], width, 0.8, taper=(0.1, 0.3), pounce=False)
                    self.wash(np.vstack([top, [[top[-1, 0], y], [top[0, 0], y]]]), tone, angle=0.0, slip=0.6, pool=0.4)
                    if r.random() < 0.4:
                        self.trek([(C[0], y), (C[0], y - h * 0.3)], width * 0.8, 0.7, smooth=False, pounce=False)
            x = xe + h * r.uniform(0.6, 3.0)

    def windmill(self, x, base, h, sails=0.35, squash=0.62, cloth=(0, 2), width=2.2, tone=0.16, gallery=True, door=True):
        """a smock mill with a stage: base = ground y, h = hub height above ground.
        sails = angle of the first arm (radians); squash < 1 turns the sail cross toward the left (3/4 view);
        cloth = which arms carry canvas. Returns the silhouette polygon."""
        r = self.rng
        bw, tw = h * 0.25, h * 0.125
        yb, yt = base - h * 0.17, base - h * 0.86
        hub = (x - h * 0.07, base - h * 0.95)
        R = h * 0.8
        # --- sails first (they are in front)
        cloth_polys = []
        for k in range(4):
            a = sails + k * np.pi / 2
            d = np.array([np.cos(a) * squash, np.sin(a)])
            pr = np.array([-np.sin(a) * squash, np.cos(a)])
            def S(s, o): return (hub[0] + d[0] * s + pr[0] * o, hub[1] + d[1] * s + pr[1] * o)
            s0, s1, ww = R * 0.17, R, R * 0.19
            frame = [S(s0, 2), S(s1, 2), S(s1, ww), S(s0 + R * 0.05, ww)]
            if k in cloth:
                cl = [S(s0 + R * 0.02, 2.5), S(s1 - R * 0.03, 2.5), S(s1 - R * 0.05, ww * 0.96), S(s0 + R * 0.08, ww * 0.94)]
                cloth_polys.append(cl)
                self.wash(cl, 0.22, angle=a, pool=0.5, slip=0.8, band=6)
                self.hatch(cl, angle=a, spacing=4.2, width=0.9, dens=0.7)
            self.trek([S(R * 0.06, 0), S(s1 + R * 0.04, 0)], width * 1.15, taper=(0.02, 0.15))
            self.trek([S(R * 0.06, -3.2), S(s1 + R * 0.02, -2.2)], width * 0.6, 0.8, taper=(0.05, 0.3))
            self.trek([frame[1], frame[2]], width * 0.8)
            self.trek([frame[2], frame[3]], width * 0.9)
            for j in range(1, 10):
                s = s0 + (s1 - s0) * j / 10
                self.trek([S(s, 1), S(s, ww * (0.95 if s > s0 + R * 0.05 else 0.6))], width * 0.55, 0.85, smooth=False, taper=(0.1, 0.2), pounce=False)
            self.trek([S(s0 + R * 0.04, ww * 0.5), S(s1, ww * 0.5)], width * 0.5, 0.75, taper=(0.1, 0.2), pounce=False)
            self.occlude([S(R * 0.05, -4), S(s1 + R * 0.04, -4), S(s1 + R * 0.04, 3.5), S(R * 0.05, 3.5)], grow=0.5)
            self.occlude([frame[1], frame[2], (frame[2][0] + 0.1, frame[2][1] + 0.1)], grow=1.6)
            self.occlude([frame[2], frame[3], (frame[3][0] + 0.1, frame[3][1])], grow=1.6)
        for cl in cloth_polys: self.occlude(cl, grow=0.8)
        # hub and cap
        self.trek(ellipse_pts(hub[0], hub[1], 5.5, 6.5), width, 1.05)
        self.wash(ellipse_pts(hub[0], hub[1], 5, 6), 0.5, pool=0.2, slip=0)
        self.occlude(ellipse_pts(hub[0], hub[1], 7, 8))
        cap = [(x - tw * 1.25, yt + 2), (x - tw * 1.1, yt - h * 0.07), (x - tw * 0.5, yt - h * 0.135), (x + tw * 0.3, yt - h * 0.145),
               (x + tw * 0.95, yt - h * 0.09), (x + tw * 1.2, yt + 2)]
        self.trek(cap, width, taper=(0.05, 0.1))
        self.trek([cap[0], (x, yt + 4), cap[-1]], width * 0.9)
        self.wash(cap + [(x, yt + 4)], tone * 1.6, angle=0.3, pool=0.6, grad=((x - tw, yt - h * 0.1), (x + tw, yt), 0.7, 1.3))
        self.hatch(cap + [(x, yt + 4)], angle=0.9, spacing=4.5, width=0.8, dens=0.6)
        # gallery (stage) in front of the smock
        sil = [(x - bw * 1.04, base), (x - bw * 1.04, yb), (x - tw, yt), (x + tw, yt), (x + bw * 1.04, yb), (x + bw * 1.04, base)]
        if gallery:
            yg = base - h * 0.36
            gw = h * 0.43
            half = lambda yy: tw + (bw - tw) * (yy - yt) / (yb - yt)
            self.trek([(x - gw, yg), (x + gw, yg)], width, smooth=False)
            self.trek([(x - gw, yg + 3.5), (x + gw, yg + 3.5)], width * 0.7, 0.85, smooth=False, pounce=False)
            yr = yg - h * 0.075
            self.trek([(x - gw, yr), (x - half(yr) - 1, yr)], width * 0.7, smooth=False)
            self.trek([(x + half(yr) + 1, yr), (x + gw, yr)], width * 0.7, smooth=False)
            for j in range(9):
                f = j / 8
                px = x - gw + 2 * gw * f
                if abs(px - x) < half(yr) - 2: continue
                self.trek([(px, yr), (px, yg)], width * 0.55, 0.9, smooth=False, pounce=False, bead=0)
            for sgn in (-1, 1):
                self.trek([(x + sgn * gw * 0.85, yg + 3), (x + sgn * half(yg + 40) * 0.98, yg + h * 0.17)], width * 0.75, smooth=False)
                self.trek([(x + sgn * gw * 0.45, yg + 3), (x + sgn * half(yg + 30) * 0.98, yg + h * 0.1)], width * 0.6, 0.9, smooth=False)
            self.wash([(x - gw, yg - 1), (x + gw, yg - 1), (x + gw, yg + 4.5), (x - gw, yg + 4.5)], 0.35, slip=0.5, pool=0.2)
            self.occlude([(x - gw - 1, yg - 1.5), (x + gw + 1, yg - 1.5), (x + gw + 1, yg + 5), (x - gw - 1, yg + 5)], grow=0.5)
            self.occlude([(x - gw, yr - 1), (x + gw, yr - 1), (x + gw, yr + 1.2), (x - gw, yr + 1.2)], grow=0.3)
        # door and windows
        if door:
            dw = bw * 0.32
            dp = [(x - dw, base), (x - dw, base - h * 0.1), (x - dw * 0.6, base - h * 0.125), (x, base - h * 0.132),
                  (x + dw * 0.6, base - h * 0.125), (x + dw, base - h * 0.1), (x + dw, base)]
            self.trek(dp, width * 0.85)
            self.wash(dp, 0.42, angle=np.pi / 2, slip=0.6)
            self.occlude(dp)
        for (fy, fx) in ((0.55, -0.15), (0.7, 0.18), (0.25, 0.42)):
            yy = base - h * fy
            hw = tw + (bw - tw) * (yy - yt) / (yb - yt)
            wx = x + fx * hw
            q = [(wx - 4.5, yy - 6), (wx + 4.5, yy - 6), (wx + 4.5, yy + 6), (wx - 4.5, yy + 6)]
            self.closed(q, width * 0.7, smooth=False)
            self.wash(q, 0.5, slip=0.4, pool=0.1)
            self.occlude(q)
        # smock body: sides, thatch lines (denser on the shade side), brick base
        self.trek([(x - bw, yb), (x - (bw + tw) / 2 - 2, (yb + yt) / 2), (x - tw, yt)], width)
        self.trek([(x + bw, yb), (x + (bw + tw) / 2 + 2, (yb + yt) / 2), (x + tw, yt)], width)
        for f in np.linspace(-0.85, 0.85, 13):
            if f < -0.2 and r.random() < 0.55: continue
            p0 = (x + f * bw, yb - 2); p1 = (x + f * tw, yt + 3)
            self.trek([p0, _lerp(p0, p1, 0.5), p1], width * (0.45 + 0.25 * (f > 0.2)), 0.75 + 0.2 * (f > 0.2), taper=(0.1, 0.4), pounce=False)
        for f in (0.33, 0.66):
            yy = yb + (yt - yb) * f
            hw = tw + (bw - tw) * (yy - yt) / (yb - yt)
            self.line((x - hw, yy), (x + hw, yy + 1), width * 0.5, 0.6, bend=2, pounce=False)
        smock = [(x - bw, yb), (x - tw, yt), (x + tw, yt), (x + bw, yb)]
        self.wash(smock, tone, angle=-np.pi / 2, pool=0.5, grad=((x - bw, yb), (x + bw, yb), 0.6, 1.6))
        self.trek([(x - bw * 1.04, base), (x - bw * 1.04, yb), (x + bw * 1.04, yb), (x + bw * 1.04, base)], width, smooth=False, taper=(0.03, 0.05))
        base_q = [(x - bw * 1.04, base), (x - bw * 1.04, yb), (x + bw * 1.04, yb), (x + bw * 1.04, base)]
        self.wash(base_q, tone * 1.5, angle=0.0, pool=0.5, grad=((x - bw, base), (x + bw, base), 0.7, 1.4))
        for j in range(5):
            yy = base - (j + 0.5) * (base - yb) / 5
            for k in range(4):
                xx = x - bw + (k + 0.5 * (j % 2)) * bw * 0.5 + r.uniform(-2, 2)
                if xx > x + bw - 6: continue
                self.trek([(xx, yy), (xx + bw * 0.3, yy)], 0.9, 0.7, smooth=False, pounce=False, taper=(0.2, 0.3))
        self.occlude(sil + [(x + bw, base)])
        self.occlude(cap)
        return sil

    def house(self, x0, x1, base, wall, gable='step', gable_h=None, floors=3, cols=None, door=0.5, chimney=None,
              hoist=True, width=1.9, tone=0.1, shade=None, vane=None, smoke=None):
        """a canal house: facade x0..x1 from `base` up `wall` px, then a gable ('step', 'bell', 'neck', 'spout').
        chimney = x of a chimney on the roof behind; smoke = (dx, dy) drift of its smoke; vane = draw a cockerel
        weathervane on the top pointing into the wind (-1 = wind from the left). Returns the silhouette."""
        r = self.rng
        W = x1 - x0
        gh = gable_h or W * 0.75
        top = base - wall
        cx = (x0 + x1) / 2
        if gable == 'step':
            n = 3 if W < 110 else 4
            sw = W * 0.38 / n; sh = gh / (n + 0.6)
            L = [(x0, base), (x0, top)]
            xx, yy = x0, top
            for j in range(n):
                L += [(xx, yy - sh), (xx + sw, yy - sh)]; xx += sw; yy -= sh
            L += [(xx, yy - sh * 0.6)]
            Rr = [(x1 - (pt[0] - x0), pt[1]) for pt in L[::-1]]
            sil = L + Rr[1:]
        elif gable == 'bell':
            sil = [(x0, base), (x0, top), (x0 + W * 0.04, top - gh * 0.35), (x0 + W * 0.2, top - gh * 0.62), (x0 + W * 0.25, top - gh * 0.9),
                   (cx - W * 0.18, top - gh * 0.98), (cx, top - gh * 1.12), (cx + W * 0.18, top - gh * 0.98), (x1 - W * 0.25, top - gh * 0.9),
                   (x1 - W * 0.2, top - gh * 0.62), (x1 - W * 0.04, top - gh * 0.35), (x1, top), (x1, base)]
        elif gable == 'neck':
            nw = W * 0.24
            sil = [(x0, base), (x0, top), (x0 + W * 0.08, top - gh * 0.08), (x0 + W * 0.14, top - gh * 0.38), (cx - nw, top - gh * 0.42),
                   (cx - nw, top - gh * 0.95), (cx, top - gh * 1.12), (cx + nw, top - gh * 0.95), (cx + nw, top - gh * 0.42),
                   (x1 - W * 0.14, top - gh * 0.38), (x1 - W * 0.08, top - gh * 0.08), (x1, top), (x1, base)]
        else:   # spout: plain pointed gable
            sil = [(x0, base), (x0, top), (cx - W * 0.12, top - gh * 0.9), (cx, top - gh), (cx + W * 0.12, top - gh * 0.9), (x1, top), (x1, base)]
        peak = min(sil, key=lambda q: q[1])
        # weathervane / smoke first (in front of the sky)
        if vane:
            vx, vy = peak[0], peak[1]
            self.trek([(vx, vy), (vx, vy - 30)], 1.3, smooth=False)
            d = -1 if vane < 0 else 1
            arrow = [(vx + d * 15, vy - 22), (vx - d * 13, vy - 22)]
            self.trek(arrow, 1.2, smooth=False)
            self.trek([(vx + d * 15, vy - 22), (vx + d * 10, vy - 25)], 1.1, smooth=False)
            self.trek([(vx + d * 15, vy - 22), (vx + d * 10, vy - 19)], 1.1, smooth=False)
            ck = [(vx - d * 2, vy - 26), (vx + d * 4, vy - 33), (vx + d * 7, vy - 31), (vx + d * 5, vy - 27), (vx + d * 1, vy - 25),
                  (vx - d * 6, vy - 29), (vx - d * 9, vy - 36), (vx - d * 9, vy - 27), (vx - d * 3, vy - 24)]
            self.closed(ck, 1.1)
            self.wash(ck, 0.6, pool=0.2, slip=0)
            self.dot(vx, vy - 30.5, 1.6)
        # outline
        self.trek(sil[1:-1], width, taper=(0.02, 0.05), smooth=False)
        self.trek([sil[0], sil[1]], width, smooth=False); self.trek([sil[-2], sil[-1]], width, smooth=False)
        self.trek([(x0 - 2, base), (x1 + 2, base)], width * 0.9, smooth=False)
        if gable == 'step':
            self.trek([(x0 + 1, top + 4), (x1 - 1, top + 4)], width * 0.6, 0.85, smooth=False, pounce=False)
        # windows
        cols = cols or (2 if W < 100 else 3)
        fh = (wall - 8) / floors
        win = []
        for fl in range(floors):
            yy0 = base - fh * (fl + 1) + fh * 0.22
            yy1 = base - fh * fl - fh * 0.18
            for c in range(cols):
                if fl == 0 and door is not None and abs((c + 0.5) / cols - door) < 0.5 / cols: continue
                wx0 = x0 + W * (c + 0.22) / cols; wx1 = x0 + W * (c + 0.78) / cols
                q = [(wx0, yy0), (wx1, yy0), (wx1, yy1), (wx0, yy1)]
                win.append(q)
        gy0 = top - gh * 0.55; gy1 = top - gh * 0.12
        if gh > 40:
            win.append([(cx - W * 0.1, gy0), (cx + W * 0.1, gy0), (cx + W * 0.1, gy1), (cx - W * 0.1, gy1)])
        for q in win:
            self.closed(q, width * 0.7, smooth=False, bead=0.1)
            mx, my = (q[0][0] + q[1][0]) / 2, (q[0][1] + q[2][1]) / 2
            self.trek([(mx, q[0][1]), (mx, q[2][1])], width * 0.5, 0.9, smooth=False, pounce=False)
            self.trek([(q[0][0], my - 1), (q[1][0], my - 1)], width * 0.5, 0.9, smooth=False, pounce=False)
            self.wash(q, 0.36, angle=np.pi / 2, slip=0.6, pool=0.4, holes=[[(mx - 1, my), (q[1][0] - 2, my), (q[1][0] - 2, q[2][1] - 2), (mx - 1, q[2][1] - 2)]])
            self.occlude(q, grow=0.4)
        if door is not None:
            dx = x0 + W * door
            dwid = W * 0.13
            dq = [(dx - dwid, base), (dx - dwid, base - fh * 0.75), (dx, base - fh * 0.85), (dx + dwid, base - fh * 0.75), (dx + dwid, base)]
            self.trek(dq, width * 0.8)
            self.wash(dq, 0.45, angle=np.pi / 2, slip=0.6)
            self.occlude(dq)
            self.trek([(dx - dwid - 4, base - 1), (dx + dwid + 4, base - 1)], width * 0.7, smooth=False, pounce=False)
        if hoist:
            hy = peak[1] + gh * 0.28 if gable != 'neck' else top - gh * 0.78
            self.trek([(cx, hy), (cx, hy - 5), (cx + 9, hy - 5)], 1.4, smooth=False)
            self.trek([(cx + 9, hy - 5), (cx + 9, hy + 3)], 0.9, 0.8, smooth=False, pounce=False)
        # brick: scattered short courses, more on the shade side
        for _ in range(int(W * wall / 380)):
            bx = r.uniform(x0 + 4, x1 - 12); by = r.uniform(top + 4, base - 4)
            if shade == 'right' and bx < cx and r.random() < 0.5: continue
            self.trek([(bx, by), (bx + r.uniform(6, 12), by)], 0.85, 0.6, smooth=False, pounce=False, taper=(0.3, 0.3))
        self.wash(sil, tone, angle=np.pi / 2, pool=0.55, slip=1.0)
        if shade == 'right':
            self.hatch([(x1 - W * 0.18, base), (x1 - W * 0.18, top), (x1, top), (x1, base)], angle=np.pi / 2, spacing=3.6, width=0.8, dens=0.6)
        if chimney is not None:
            chy = peak[1] + gh * 0.25
            q = [(chimney - 5, chy + 14), (chimney - 5, chy - 10), (chimney + 5, chy - 10), (chimney + 5, chy + 14)]
            self.closed(q[:4], 1.4, smooth=False)
            self.wash(q, 0.3, slip=0.4)
            if smoke:
                self.smoke(chimney, chy - 12, *smoke)
        self.occlude(sil)
        return sil

    def sailboat(self, x, water, length, facing=1, mast=None, belly=0.35, width=2.0, tone=0.2,
                 cargo=6, skipper=True, pennant=1, leeboard=True):
        """a Dutch sailing barge (tjalk): round bluff hull, leeboard, gaff mainsail and jib, pennant.
        x = stern, facing = +1 sails to the right. Returns the hull polygon (occlude water with it)."""
        r = self.rng
        f = facing
        L = length
        H0 = L * 0.15
        mast = mast or L * 1.05
        def P(u, v): return (x + f * u, water - v)
        hull_top = [P(-L * 0.02, H0 * 1.15), P(L * 0.12, H0 * 0.98), P(L * 0.5, H0 * 0.88), P(L * 0.86, H0 * 1.02), P(L * 1.0, H0 * 1.35)]
        hull_bot = [P(L * 1.0, H0 * 1.35), P(L * 0.99, H0 * 0.6), P(L * 0.93, 0), P(L * 0.5, -H0 * 0.05), P(L * 0.08, 0), P(-L * 0.02, H0 * 0.5),
                    P(-L * 0.02, H0 * 1.15)]
        hull = hull_top + hull_bot[1:]
        mx = L * 0.58
        mtop = P(mx, H0 + mast)
        mfoot = P(mx, H0 * 0.9)
        # pennant streaming downwind
        if pennant:
            k = np.linspace(0, 1, 12)
            pp = np.stack([mtop[0] + pennant * k * L * 0.22, mtop[1] + 2 + np.sin(k * 7) * 3 * k], 1)
            self.trek(pp, 1.6, taper=(0.02, 0.7))
            self.trek(pp + [0, 3.5], 1.1, 0.8, taper=(0.02, 0.7), pounce=False)
        # mainsail (gaff): luff on the mast, foot on the boom, gaff up to the peak; bellied leech
        boom_y = H0 * 1.55
        luff0, luff1 = P(mx, boom_y), P(mx, H0 + mast * 0.8)
        clew = P(mx - L * 0.56, boom_y + L * 0.02)
        peak = P(mx - L * 0.3, H0 + mast * 1.08)
        b = belly * L * 0.12
        leech = [peak, (peak[0] - f * b * 0.4, (peak[1] * 2 + clew[1]) / 3), (clew[0] - f * b * 0.5, (peak[1] + 2 * clew[1]) / 3), clew]
        sail = [luff0, luff1] + leech + [clew]
        foot = [clew, ((clew[0] + luff0[0]) / 2, luff0[1] + b * 0.4), luff0]
        # jib
        jtop = P(mx, H0 + mast * 0.8)
        jtack = P(L * 0.99, H0 * 1.4)
        jclew = P(mx + L * 0.12, H0 * 1.9)
        jib = [jtop, (jtop[0] + f * (b * 0.5 + 6), (jtop[1] + jtack[1]) / 2), jtack, jclew]
        # skipper at the tiller (in front of the sail foot)
        if skipper:
            sx, sy = P(L * 0.06, H0 * 1.0)
            self._skipper(sx, sy, L * 0.16, f)
        self.trek([P(-L * 0.02, H0 * 1.2), P(-L * 0.1, H0 * 1.6)], width * 0.9, smooth=False)  # tiller
        # sails
        self.trek([luff1, peak], width * 1.1, smooth=False)                           # gaff
        self.trek(leech, width)
        self.trek(foot, width * 0.9)
        self.trek([clew, P(mx + L * 0.02, boom_y - 1)], width * 1.1, smooth=False)    # boom
        self.wash(sail, tone * 0.7, angle=-np.pi / 2 + 0.2 * f, pool=0.6, slip=1.0,
                  grad=(luff1, clew, 0.6, 1.25))
        for j in range(1, 7):
            u = j / 7
            a0 = _lerp(luff0, luff1, u)
            a1 = _lerp(clew, peak, u)
            m = ((a0[0] + a1[0]) / 2 - f * b * 0.55 * np.sin(np.pi * u) * 0.7, (a0[1] + a1[1]) / 2 + 4)
            self.trek([a0, m, a1], 0.9, 0.55, taper=(0.2, 0.3), pounce=False)
        self.trek(jib + [jtop], width * 0.9)
        self.wash(jib, tone * 0.6, angle=0.3 * f, slip=0.8, pool=0.6)
        self.occlude(sail, grow=1.0); self.occlude(jib, grow=1.0)
        # mast and rigging
        self.trek([mfoot, (mtop[0], mtop[1] - 4)], width * 1.2, smooth=False, taper=(0.02, 0.1))
        self.trek([mtop, P(L * 1.04, H0 * 1.4)], 0.9, 0.8, smooth=False, pounce=False)
        self.trek([mtop, P(-L * 0.01, H0 * 1.15)], 0.9, 0.8, smooth=False, pounce=False)
        self.occlude([(mfoot[0] - 2.5, mfoot[1]), (mfoot[0] + 2.5, mfoot[1]), (mtop[0] + 2.5, mtop[1]), (mtop[0] - 2.5, mtop[1])])
        # cargo: sacks on deck
        for j in range(cargo):
            u = 0.2 + 0.07 * j + (0.12 if 0.2 + 0.07 * j > 0.5 else 0)
            if u > 0.88: break
            gx, gy = P(L * u, H0 * 0.92)
            sw_, sh_ = L * 0.032, L * 0.05
            sk = [(gx - sw_, gy), (gx - sw_ * 1.05, gy - sh_ * 0.55), (gx - sw_ * 0.6, gy - sh_ * 0.95), (gx - sw_ * 0.15, gy - sh_ * 1.12),
                  (gx + sw_ * 0.2, gy - sh_ * 1.0), (gx + sw_ * 0.7, gy - sh_ * 0.9), (gx + sw_ * 1.05, gy - sh_ * 0.5), (gx + sw_, gy)]
            self.trek(sk, 1.3, 0.95, taper=(0.05, 0.1))
            self.trek([(gx - sw_ * 0.45, gy - sh_ * 0.95), (gx - sw_ * 0.1, gy - sh_ * 0.82), (gx + sw_ * 0.35, gy - sh_ * 0.92)], 0.9, 0.8, pounce=False)
            self.wash(sk, 0.1, slip=0.5, pool=0.6)
            self.occlude(sk)
        if leeboard:
            lc = P(L * 0.66, H0 * 0.9)
            lb = [(lc[0] - f * L * 0.022, lc[1] - 3), (lc[0] + f * L * 0.022, lc[1] - 3), (lc[0] + f * L * 0.075, lc[1] + H0 * 0.9),
                  (lc[0] + f * L * 0.03, lc[1] + H0 * 0.98), (lc[0] - f * L * 0.03, lc[1] + H0 * 0.98), (lc[0] - f * L * 0.075, lc[1] + H0 * 0.9)]
            self.trek(lb + [lb[0]], width * 0.9)
            self.wash(lb, 0.16, slip=0.5, pool=0.7, angle=np.pi / 2)
            self.dot(lc[0], lc[1] + 2, 1.8)
            for j in (-0.55, 0.0, 0.55):                                    # planks fanning out
                self.trek([(lc[0] + f * L * 0.012 * j, lc[1] + 4), (lc[0] + f * L * 0.07 * j, lc[1] + H0 * 0.92)], 0.8, 0.7, smooth=False, pounce=False)
            self.occlude(lb)
        # hull
        self.trek(hull_top, width * 1.1, taper=(0.02, 0.05))
        self.trek(hull_bot, width, taper=(0.02, 0.05))
        self.trek([P(-L * 0.01, H0 * 0.75), P(L * 0.5, H0 * 0.45), P(L * 0.97, H0 * 0.85)], width * 0.7, 0.9, pounce=False)
        self.wash(hull, tone * 2.0, angle=0.0, pool=0.5, holes=[[P(0, H0 * 0.98), P(L * 0.5, H0 * 0.8), P(L * 0.95, H0 * 1.12), P(L * 0.95, H0 * 0.92), P(L * 0.5, H0 * 0.55), P(0, H0 * 0.78)]])
        self.hatch(hull_bot, angle=0.0, spacing=3.4, width=0.8, dens=0.7)
        self.occlude(hull)
        return hull

    def _skipper(self, x, y, h, f=1):
        """a small figure standing at the tiller (feet hidden by the bulwark)"""
        hy = y - h
        self.trek(ellipse_pts(x, hy, h * 0.11, h * 0.12, 0, 16), 1.4)
        hat = [(x - h * 0.2, hy - h * 0.05), (x + h * 0.2, hy - h * 0.07)]
        self.trek(hat, 1.6, smooth=False)
        self.trek([(x - h * 0.1, hy - h * 0.06), (x - h * 0.07, hy - h * 0.2), (x + h * 0.08, hy - h * 0.2), (x + h * 0.1, hy - h * 0.07)], 1.4)
        body = [(x - h * 0.16, y), (x - h * 0.13, hy + h * 0.2), (x + h * 0.13, hy + h * 0.2), (x + h * 0.18, y)]
        self.trek(body, 1.5)
        self.wash(body, 0.35, slip=0.5)
        self.trek([(x + f * h * 0.1, hy + h * 0.3), (x - f * h * 0.15, hy + h * 0.5), (x - f * h * 0.32, hy + h * 0.55)], 1.3)
        self.occlude(body + [(x, hy - h * 0.25)])

    def smoke(self, x, y, dx, dy, puffs=7, width=1.3):
        """smoke from a chimney blown downwind: a chain of growing curls that fade"""
        for k in range(puffs):
            f = k / max(1, puffs - 1)
            px = x + dx * f + np.sin(f * 7) * 3
            py = y + dy * f - 4 * f
            rr = 2.5 + 6 * f
            a0 = np.pi * (0.75 + 0.2 * np.sin(k))
            self.trek(arc(px, py, rr * 1.25, rr, a0, a0 + np.pi * 1.35, 10), width * (1 - 0.4 * f), 0.9 - 0.45 * f,
                      taper=(0.1, 0.5), pounce=False)

    # ------------------------------------------------------------ single tiles: corners, medallion, small motifs
    def corner(self, x, y, sx, sy, style='spin', size=24.0, width=1.5):
        """a quarter ornament in the tile corner at (x, y); (sx, sy) = ±1 points into the tile.
        Four tiles meeting at a joint build the whole ornament between them."""
        d = np.array([sx, sy], np.float32) / np.sqrt(2)
        q = np.array([-d[1], d[0]])
        def P(a, b): return (x + d[0] * a + q[0] * b, y + d[1] * a + q[1] * b)
        s = size
        if style == 'spin':                      # 'spider': a leaf on the diagonal, curling tendrils, dots
            leaf = [P(s * 0.12, 0), P(s * 0.4, s * 0.16), P(s * 0.78, 0), P(s * 0.4, -s * 0.16)]
            self.trek(leaf + [leaf[0]], width)
            self.wash(leaf, 0.42, slip=0.3, pool=0.3, ragged=0.15)
            self.trek([P(s * 0.78, 0), P(s * 0.92, 0)], width * 0.7, pounce=False)
            for sg in (-1, 1):
                self.trek([P(s * 0.08, sg * s * 0.08), P(s * 0.2, sg * s * 0.42), P(s * 0.42, sg * s * 0.5), P(s * 0.5, sg * s * 0.36),
                           P(s * 0.4, sg * s * 0.3)], width * 0.85, taper=(0.1, 0.5))
                self.dot(*P(s * 0.66, sg * s * 0.28), r=width * 0.75)
            self.trek(arc(x, y, s * 0.2, s * 0.2, np.arctan2(d[1], d[0]) - 0.8, np.arctan2(d[1], d[0]) + 0.8, 8), width * 0.8)
        elif style == 'lelie':                   # a quarter fleur-de-lis
            self.trek([P(s * 0.05, 0), P(s * 0.85, 0)], width)
            for sg in (-1, 1):
                self.trek([P(s * 0.3, 0), P(s * 0.35, sg * s * 0.3), P(s * 0.6, sg * s * 0.38), P(s * 0.62, sg * s * 0.18)], width * 0.85)
            self.wash([P(s * 0.5, -s * 0.1), P(s * 0.85, 0), P(s * 0.5, s * 0.1)], 0.45, slip=0.2)
        else:                                    # 'dot': a plain quarter circle with a dot
            self.trek(arc(x, y, s * 0.35, s * 0.35, np.arctan2(d[1], d[0]) - 0.8, np.arctan2(d[1], d[0]) + 0.8, 10), width)
            self.dot(*P(s * 0.55, 0), r=width)

    def medallion(self, i, k, r=None, width=1.4, tendrils=True):
        cx, cy = self.centre(i, k)
        hs = (self.p - self.joint) / 2
        r = r or hs * 0.72
        self.trek(ellipse_pts(cx, cy, r, r, self.rng.uniform(0, 6), 64), width, 0.95, taper=(0.02, 0.02))
        self.trek(ellipse_pts(cx, cy, r - 3.6, r - 3.6, self.rng.uniform(0, 6), 64), width * 0.7, 0.8, taper=(0.02, 0.02), pounce=False)
        if tendrils:
            for a in (np.pi / 4, 3 * np.pi / 4, 5 * np.pi / 4, 7 * np.pi / 4):
                bx, by = cx + np.cos(a) * r, cy + np.sin(a) * r
                ox, oy = np.cos(a), np.sin(a)
                self.trek([(bx, by), (bx + ox * 6 - oy * 4, by + oy * 6 + ox * 4), (bx + ox * 9, by + oy * 9)], width * 0.8, 0.9, taper=(0.05, 0.5))
        return cx, cy, r

    def vignette(self, i, k, kind, mirror=False, scale=1.0, width=1.35):
        """a small motif in the centre of a single tile: 'tulip', 'ship', 'mill', 'boat', 'fish', 'bird', 'house', 'pot'"""
        cx, cy = self.centre(i, k)
        s = (self.p - self.joint) / 2 * 0.62 * scale
        m = -1 if mirror else 1
        r = self.rng
        def P(u, v): return (cx + m * u * s, cy + v * s)
        w = width
        if kind == 'tulip':
            self.tulip(cx, cy + s * 0.75, s * 1.35, lean=m * 0.1, width=w, tone=0.22, leaves=2)
            self.trek([P(-0.6, 0.78), P(0, 0.68), P(0.6, 0.8)], w * 0.9, pounce=False)
            self.grass(cx - s * 0.6, cx + s * 0.6, cy + s * 0.78, n=3, h=s * 0.18, width=w * 0.7)
        elif kind == 'pot':
            pot = [P(-0.38, 0.25), P(0.38, 0.25), P(0.28, 0.85), P(-0.28, 0.85)]
            self.trek(pot + [pot[0]], w, smooth=False)
            self.trek([P(-0.42, 0.25), P(0.42, 0.25)], w * 1.4, smooth=False)
            self.wash(pot, 0.3, slip=0.5)
            self.occlude(pot)
            for j, (u, hh, ln) in enumerate(((-0.35, 0.95, -0.25), (0.0, 1.15, 0.0), (0.35, 0.9, 0.25))):
                self.tulip(cx + m * u * s * 0.4, cy + s * 0.25, s * hh, lean=m * ln, width=w * 0.85, tone=0.22, leaves=1 if j != 1 else 2)
        elif kind == 'ship':
            hull = [P(-0.75, 0.25), P(0.75, 0.2), P(0.6, 0.45), P(-0.55, 0.45)]
            self.trek(hull + [hull[0]], w)
            self.wash(hull, 0.35, slip=0.5)
            self.occlude(hull)
            for u, hgt in ((-0.4, 0.85), (0.05, 1.05), (0.45, 0.8)):
                for j in range(2):
                    y0 = 0.15 - hgt * (0.25 + 0.38 * j); y1 = y0 + hgt * 0.32
                    sq = [P(u - 0.17, y0), P(u + 0.17, y0), P(u + 0.2, y1), P(u - 0.2, y1)]
                    self.trek([sq[0], sq[1], (sq[2][0] + m * 2, (sq[1][1] + sq[2][1]) / 2), sq[2], sq[3], (sq[3][0] + m * 2, (sq[0][1] + sq[3][1]) / 2), sq[0]], w * 0.8)
                    self.wash(sq, 0.12, slip=0.4)
                    self.occlude(sq)
                self.trek([P(u, 0.25), P(u, 0.15 - hgt)], w * 0.9, smooth=False)
                self.trek([P(u, 0.15 - hgt), P(u + 0.14, 0.18 - hgt)], w * 0.8, smooth=False, pounce=False)
            self.water(cx - s * 0.85, cx + s * 0.85, cy + s * 0.5, cy + s * 0.75, width=w * 0.8, far=4, near=6)
        elif kind == 'boat':
            hull = [P(-0.55, 0.3), P(0.6, 0.25), P(0.45, 0.48), P(-0.45, 0.48)]
            sail = [P(-0.05, 0.2), P(-0.05, -0.75), P(-0.55, -0.62), P(-0.5, 0.18)]
            self.trek(sail + [sail[0]], w); self.wash(sail, 0.14, slip=0.4); self.occlude(sail)
            self.trek([P(0.0, 0.25), P(0.0, -0.85)], w, smooth=False)
            self.trek([P(0.0, -0.75), P(0.55, 0.22)], w * 0.7, smooth=False, pounce=False)
            self.trek(hull + [hull[0]], w); self.wash(hull, 0.35, slip=0.4); self.occlude(hull)
            self.water(cx - s * 0.8, cx + s * 0.8, cy + s * 0.5, cy + s * 0.75, width=w * 0.8, far=4, near=6)
        elif kind == 'fish':
            body = ellipse_pts(cx, cy, s * 0.55, s * 0.24, m * -0.35, 30)
            self.closed(body, w)
            tail = [P(0.48, -0.15), P(0.85, -0.45), P(0.78, -0.05), P(0.9, 0.2)]
            self.trek(tail + [P(0.48, -0.15)], w)
            self.wash(body, 0.2, slip=0.4, grad=((cx, cy - s * 0.3), (cx, cy + s * 0.3), 1.4, 0.4))
            self.dot(*P(-0.33, 0.08), r=w * 0.9)
            self.trek([P(-0.2, -0.08), P(-0.15, 0.08), P(-0.22, 0.2)], w * 0.7, pounce=False)
            self.water(cx - s * 0.8, cx + s * 0.8, cy + s * 0.45, cy + s * 0.75, width=w * 0.8, far=4, near=6)
        elif kind == 'bird':
            self.trek([P(-0.8, 0.35), P(-0.1, 0.25), P(0.7, 0.4)], w * 1.1)
            for u in (-0.55, 0.45):
                self.trek(arc(*P(u, 0.32), s * 0.12, s * 0.08, 3.6, 5.6, 6), w * 0.7, pounce=False)
            body = [P(-0.35, 0.05), P(-0.15, -0.3), P(0.2, -0.32), P(0.38, -0.1), P(0.2, 0.15), P(-0.1, 0.2)]
            self.closed(body, w)
            self.wash(body, 0.18, slip=0.4)
            self.trek([P(0.2, -0.32), P(0.32, -0.55), P(0.45, -0.5), P(0.43, -0.3)], w)
            self.trek([P(0.45, -0.48), P(0.6, -0.45)], w, smooth=False)
            self.dot(*P(0.37, -0.45), r=w * 0.7)
            self.trek([P(-0.35, 0.05), P(-0.7, -0.05), P(-0.62, 0.12)], w * 0.9)
            self.trek([P(-0.05, -0.15), P(0.2, -0.05), P(0.05, 0.1)], w * 0.7, pounce=False)
            self.trek([P(0.0, 0.2), P(0.0, 0.3)], w * 0.7, smooth=False); self.trek([P(0.1, 0.18), P(0.12, 0.29)], w * 0.7, smooth=False)
        elif kind == 'house':
            self.house(cx + m * s * 0.05 - s * 0.35, cx + m * s * 0.05 + s * 0.35, cy + s * 0.55, s * 0.55, gable='step',
                       gable_h=s * 0.5, floors=2, cols=2, door=0.5, width=w, hoist=False, tone=0.08)
            self.tree(cx - m * s * 0.62, cy + s * 0.58, s * 1.0, w=s * 0.6, lean=0, width=w * 0.8, tone=0.18, clumps=3)
            self.trek([P(-0.85, 0.6), P(0.85, 0.56)], w * 0.9, pounce=False)
        elif kind == 'mill':
            self.windmill(cx + m * s * 0.1, cy + s * 0.6, s * 1.0, sails=r.uniform(0, 1.5), squash=0.85, width=w, tone=0.12,
                          gallery=False, door=True)
            self.trek([P(-0.85, 0.62), P(0.85, 0.58)], w * 0.9, pounce=False)
            self.grass(cx - s * 0.8, cx + s * 0.8, cy + s * 0.62, n=3, h=s * 0.15, width=w * 0.7)
            self.birds([P(-0.6, -0.55)], size=s * 0.12, width=w * 0.9)
        self.clear_occlusion()

    def field(self, tiles=None, corners='spin', size=None, medallion=True, motifs=('tulip', 'ship', 'mill', 'boat', 'fish', 'bird', 'house', 'pot'),
              width=1.4, skip=()):
        """paint every tile outside the tableaux as a single tile: corner quarters, a medallion and a small motif"""
        tiles = tiles if tiles is not None else [t for t in self.visible() if not self.in_tableau(*t) and t not in skip]
        size = size or self.p * 0.24
        r = self.rng
        chosen = {}
        for (i, k) in tiles:
            x0, y0, x1, y1 = self.rect(i, k)
            for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
                self.corner(cx - sx * self.joint / 2, cy - sy * self.joint / 2, sx, sy, corners, size, width)
            if medallion: self.medallion(i, k, width=width)
            near = {chosen.get((i - 1, k)), chosen.get((i, k - 1)), chosen.get((i - 1, k - 1)), chosen.get((i + 1, k - 1))}
            kinds = [m for m in motifs if m not in near] or list(motifs)
            kind = kinds[int(r.integers(len(kinds)))]
            chosen[(i, k)] = kind
            self.vignette(i, k, kind, mirror=bool(r.random() < 0.5), width=width)

    def border(self, rect, band=34.0, inset=9.0, width=2.6, tone=0.42, leaf=26.0, reserve=None):
        """a painted frame round a tableau: outer and inner rules, a blue band with a white (reserved) vine
        of leaves and berries, rosettes in the corners. reserve = extra polygons kept white (a cartouche)."""
        X0, Y0, X1, Y1 = rect
        a0 = (X0 + inset, Y0 + inset, X1 - inset, Y1 - inset)
        a1 = (a0[0] + band, a0[1] + band, a0[2] - band, a0[3] - band)
        holes = list(reserve or [])
        r = self.rng
        mid = band / 2
        sides = [((a0[0] + band, a0[1] + mid), (a0[2] - band, a0[1] + mid)), ((a0[2] - mid, a0[1] + band), (a0[2] - mid, a0[3] - band)),
                 ((a0[2] - band, a0[3] - mid), (a0[0] + band, a0[3] - mid)), ((a0[0] + mid, a0[3] - band), (a0[0] + mid, a0[1] + band))]
        leaves = []
        for (p0, p1) in sides:
            L = np.hypot(p1[0] - p0[0], p1[1] - p0[1])
            ux, uy = (p1[0] - p0[0]) / L, (p1[1] - p0[1]) / L
            nx, ny = -uy, ux
            n = int(L / leaf)
            t = np.linspace(0, L, n * 8 + 1)
            amp = band * 0.16
            vine = np.stack([p0[0] + ux * t + nx * np.sin(t / leaf * np.pi) * amp, p0[1] + uy * t + ny * np.sin(t / leaf * np.pi) * amp], 1)
            leaves.append(('vine', vine))
            for j in range(n):
                tc = (j + 0.5) * leaf
                side = 1 if j % 2 == 0 else -1
                bx, by = p0[0] + ux * tc + nx * side * amp, p0[1] + uy * tc + ny * side * amp
                ang = np.arctan2(uy, ux) + side * 0.9
                ca, sa = np.cos(ang), np.sin(ang)
                ll = band * 0.36
                lf = [(bx, by), (bx + ca * ll * 0.5 - sa * ll * 0.22, by + sa * ll * 0.5 + ca * ll * 0.22), (bx + ca * ll, by + sa * ll),
                      (bx + ca * ll * 0.5 + sa * ll * 0.22, by + sa * ll * 0.5 - ca * ll * 0.22)]
                leaves.append(('leaf', lf))
                bx2, by2 = p0[0] + ux * (tc + leaf * 0.5) - nx * side * amp * 1.6, p0[1] + uy * (tc + leaf * 0.5) - ny * side * amp * 1.6
                if j < n - 1: leaves.append(('berry', (bx2, by2)))
        vine_polys = []
        for kind, g in leaves:
            if kind == 'vine':
                P = np.asarray(g); nr = _normals(P)
                vine_polys.append(np.vstack([P + nr * 2.4, (P - nr * 2.4)[::-1]]))
            elif kind == 'leaf':
                vine_polys.append(g)
            else:
                vine_polys.append(ellipse_pts(g[0], g[1], 3.4, 3.4, 0, 12))
        rosettes = []
        for (cx, cy) in ((a0[0] + mid, a0[1] + mid), (a0[2] - mid, a0[1] + mid), (a0[2] - mid, a0[3] - mid), (a0[0] + mid, a0[3] - mid)):
            ro = []
            for j in range(8):
                a = j * np.pi / 4
                ro.append(ellipse_pts(cx + np.cos(a) * band * 0.22, cy + np.sin(a) * band * 0.22, band * 0.15, band * 0.08, a, 12))
            rosettes.append((cx, cy, ro))
            vine_polys += ro
        outer = [(a0[0], a0[1]), (a0[2], a0[1]), (a0[2], a0[3]), (a0[0], a0[3])]
        inner = [(a1[0], a1[1]), (a1[2], a1[1]), (a1[2], a1[3]), (a1[0], a1[3])]
        ring_mask = np.zeros((self.H, self.W), np.float32)
        _, _, mo = self._poly_raster([outer], 0, 0, self.W, self.H, ss=1)
        _, _, mi = self._poly_raster([inner], 0, 0, self.W, self.H, ss=1)
        ring_mask = np.clip(mo - mi, 0, 1)
        self.wash(ring_mask, tone, angle=0.0, pool=0.5, slip=0.5, holes=vine_polys + holes, ragged=0.2, band=9)
        for kind, g in leaves:
            if kind == 'leaf':
                self.trek(list(g) + [g[0]], 1.2, 0.9, pounce=True, bead=0.1)
                self.trek([g[0], g[2]], 0.8, 0.7, smooth=False, pounce=False)
        for (cx, cy, ro) in rosettes:
            self.dot(cx, cy, 2.6)
        self.trek(outer + [outer[0]], width, smooth=False, taper=(0.01, 0.01))
        self.trek(inner + [inner[0]], width * 0.8, smooth=False, taper=(0.01, 0.01))
        o2 = [(a0[0] - 4.5, a0[1] - 4.5), (a0[2] + 4.5, a0[1] - 4.5), (a0[2] + 4.5, a0[3] + 4.5), (a0[0] - 4.5, a0[3] + 4.5)]
        self.trek(o2 + [o2[0]], width * 0.5, 0.85, smooth=False, taper=(0.01, 0.01), pounce=False)
        return a1

    # ------------------------------------------------------------ kiln, wall, age, light
    def fire(self):
        """kiln: glaze melts glossy, pigment turns cobalt blue and bleeds a little, pounce dust burns off"""
        self.fired = True

    def set_wall(self):
        """set the tiles in lime mortar (joints filled, recessed)"""
        self.grouted = True

    def age(self, craze=1.0, chips=10, specks=1.0, nails=0.5, cracks=(), dirt=1.0, seed=None):
        """crazing, pinholes, iron specks, chipped edges/corners showing the buff body, template nail holes,
        cracked tiles (cracks = list of polylines in px)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        H, W = self.H, self.W
        # crazing: warped Voronoi edges, per-tile amount
        c = 21.0
        wx = (noise2d(H, W, 40, 2, int(r.integers(1 << 30))) - 0.5) * 14
        wy = (noise2d(H, W, 40, 2, int(r.integers(1 << 30))) - 0.5) * 14
        X, Y = self.XX + wx, self.YY + wy
        gx, gy = int(W / c) + 3, int(H / c) + 3
        jit = r.random((gy, gx, 2)).astype(np.float32)
        bx, by = np.floor(X / c).astype(np.int32), np.floor(Y / c).astype(np.int32)
        d1 = np.full((H, W), 1e9, np.float32); d2 = np.full((H, W), 1e9, np.float32)
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                cxi = np.clip(bx + ox, 0, gx - 1); cyi = np.clip(by + oy, 0, gy - 1)
                jx_ = jit[cyi, cxi, 0]; jy_ = jit[cyi, cxi, 1]
                d = np.hypot(X - (cxi + jx_) * c, Y - (cyi + jy_) * c)
                lo = d < d1
                d2 = np.where(lo, d1, np.minimum(d2, d))
                d1 = np.where(lo, d, d1)
        edge = smoothstep(1.1, 0.0, d2 - d1)
        broken = noise2d(H, W, 30, 2, int(r.integers(1 << 30)))
        amt = self.craze[self.ck, self.ci] * craze
        cr = edge * smoothstep(0.35, 0.65, broken + amt * 0.5 - 0.25) * (0.35 + 0.65 * amt)
        # specks & pinholes
        sp = np.zeros((H, W), np.float32); pin = np.zeros((H, W), np.float32)
        n = int(W * H / 2600 * specks)
        for arr, cnt, rad in ((sp, n, (0.3, 0.9)), (pin, n // 2, (0.4, 0.8))):
            xs = r.uniform(0, W, cnt); ys = r.uniform(0, H, cnt); rs = r.uniform(*rad, cnt)
            for x, y, rr in zip(xs, ys, rs):
                x0, y0 = int(x) - 3, int(y) - 3
                if x0 < 0 or y0 < 0 or x0 + 7 > W or y0 + 7 > H: continue
                yy, xx = np.mgrid[y0:y0 + 7, x0:x0 + 7]
                arr[y0:y0 + 7, x0:x0 + 7] = np.maximum(arr[y0:y0 + 7, x0:x0 + 7], np.clip(rr + 0.5 - np.hypot(xx - x, yy - y), 0, 1))
        # chips: bites out of the glaze at edges and corners
        chip = np.zeros((H, W), np.float32)
        vis = self.visible()
        for _ in range(chips):
            i, k = vis[int(r.integers(len(vis)))]
            x0, y0, x1, y1 = self.rect(i, k)
            if r.random() < 0.6:
                cx, cy = (x0, x1)[int(r.integers(2))], (y0, y1)[int(r.integers(2))]
            else:
                if r.random() < 0.5: cx, cy = r.uniform(x0 + 15, x1 - 15), (y0, y1)[int(r.integers(2))]
                else: cx, cy = (x0, x1)[int(r.integers(2))], r.uniform(y0 + 15, y1 - 15)
            rr = r.uniform(5.0, 11.0)
            xs0, ys0 = int(cx - rr * 2), int(cy - rr * 2)
            xs1, ys1 = int(cx + rr * 2) + 1, int(cy + rr * 2) + 1
            xs0, ys0, xs1, ys1 = max(0, xs0), max(0, ys0), min(W, xs1), min(H, ys1)
            if xs1 <= xs0 or ys1 <= ys0: continue
            yy, xx = np.mgrid[ys0:ys1, xs0:xs1].astype(np.float32)
            ang = np.arctan2(yy - cy, xx - cx)
            rad = rr * (1 + 0.3 * np.sin(ang * 3 + r.uniform(0, 6)) + 0.15 * np.sin(ang * 7 + r.uniform(0, 6)))
            v = np.clip(rad - np.hypot(xx - cx, yy - cy), 0, 1)
            chip[ys0:ys1, xs0:xs1] = np.maximum(chip[ys0:ys1, xs0:xs1], v)
        chip *= self.inside
        # nail holes from the trimming template, about 5 px in from two or four corners
        nail = np.zeros((H, W), np.float32)
        for (i, k) in vis:
            if r.random() > nails: continue
            x0, y0, x1, y1 = self.rect(i, k)
            for (cx, cy) in ((x0 + 5, y0 + 5), (x1 - 5, y0 + 5), (x0 + 5, y1 - 5), (x1 - 5, y1 - 5)):
                if r.random() < 0.35: continue
                cx += r.normal(0, 0.8); cy += r.normal(0, 0.8)
                xa, ya = int(cx) - 3, int(cy) - 3
                if xa < 0 or ya < 0 or xa + 7 > W or ya + 7 > H: continue
                yy, xx = np.mgrid[ya:ya + 7, xa:xa + 7]
                nail[ya:ya + 7, xa:xa + 7] = np.maximum(nail[ya:ya + 7, xa:xa + 7], np.clip(1.6 - np.hypot(xx - cx, yy - cy), 0, 1))
        # cracks
        crack = np.zeros((H, W), np.float32)
        for pl in cracks:                                    # a crack runs through one tile and stops at the joint
            im = Image.new('L', (W * 2, H * 2), 0); dr = ImageDraw.Draw(im)
            P, _ = _resample(spline(np.asarray(pl, np.float32), 6), 2.0)
            P = P + _normals(P) * (fbm1d(len(P), 8, 3, int(r.integers(1 << 30))) * 2.2)[:, None]
            dr.line([(x * 2, y * 2) for x, y in P], fill=255, width=2)
            m = np.asarray(im, np.float32).reshape(H, 2, W, 2).mean(axis=(1, 3)) / 255
            x0, y0 = int(np.clip(pl[len(pl) // 2][0], 0, W - 1)), int(np.clip(pl[len(pl) // 2][1], 0, H - 1))
            same = (self.ci == self.ci[y0, x0]) & (self.ck == self.ck[y0, x0])
            crack = np.maximum(crack, m * same * self.inside)
        grime = noise2d(H, W, 90, 3, int(r.integers(1 << 30)))
        self.aged = dict(craze=cr.astype(np.float32), speck=sp, pin=pin, chip=chip, nail=nail, crack=crack, grime=grime, dirt=dirt)

    def light(self, window=(420, 290, 110, 150), strength=0.5, panes=(2, 3), soft=8.0, F=2300.0):
        """a window behind the viewer reflected in the glaze: window = (x, y, w, h) where the reflection would sit
        on a perfectly flat wall; tilted, cushioned tiles break it into bent pieces that jump at every joint.
        The reflection is blended over the glaze (screen), so the painting stays visible through it;
        strength ~0.5 = the brightest pane lifts a dark line about half way to white."""
        self.window = dict(rect=window, strength=strength, panes=panes, soft=soft, F=F)

    # ------------------------------------------------------------ rendering
    def _glaze_rgb(self):
        c0, c1 = self.glaze_cols
        wm = self.warm[self.ck, self.ci][..., None]
        g = c0 * (1 - wm) + c1 * wm
        g = g * self.bright[self.ck, self.ci][..., None]
        mott = noise2d(self.H, self.W, 26, 3, 11)
        g = g * (0.985 + 0.03 * mott)[..., None]
        e = np.clip(-self.sdf / 10, 0, 1)                  # glaze thinner over the rounded edge: a hint of body
        g = g * (1 - 0.035 * (1 - e))[..., None] + _c(BODY) * (0.035 * (1 - e))[..., None]
        return g.astype(np.float32)

    def composite(self, hide=()):
        hide = set(hide)
        none = '*' in hide
        H, W = self.H, self.W
        D = np.zeros((H, W), np.float32)
        if not none:
            for (nm, kind) in self.order:
                if nm in hide or kind in hide or f'{nm}.{kind}' in hide: continue
                D += self.layers[(nm, kind)]
        D = D[self.Yi, self.Xi]
        hy, hx = np.gradient(self.h)
        nz = 1 / np.sqrt(1 + hx * hx + hy * hy)
        ndl = (-hx * self.Lv[0] - hy * self.Lv[1] + self.Lv[2]) * nz
        shade = np.clip(1 + 1.1 * (ndl - self.Lv[2]), 0.55, 1.25)
        if self.fired:
            D = D * self.strength[self.ck, self.ci]
            gran = noise2d(H, W, 1.6, 1, 44)                 # undissolved cobalt grains speckle the washes
            D = D * (1 + 0.32 * (gran - 0.5) * smoothstep(0.03, 0.25, D) * (1 - smoothstep(0.5, 0.9, D)))
            D = 0.5 * blur(D, 0.55) + 0.33 * blur(D, 1.25) + 0.17 * blur(D, 3.2)
            G = self._glaze_rgb()
            col = G * np.exp(-COBALT_K[None, None, :] * D[..., None])
        else:
            G = _c(RAW_GLAZE) * (0.97 + 0.05 * noise2d(H, W, 3, 2, 5))[..., None] * self.bright[self.ck, self.ci][..., None]
            col = G * np.exp(-RAW_K[None, None, :] * D[..., None])
            if not none and 'pounce' not in hide:
                Pn = np.clip(blur(self.P[self.Yi, self.Xi], 0.45) * 1.4, 0, 1)
                col = col * (1 - 0.75 * Pn)[..., None]
        col = col * shade[..., None]
        ins = self.inside[..., None]
        if self.grouted:
            sand = noise2d(H, W, 2.5, 2, 21)
            mort = self.mortar * (0.9 + 0.12 * sand)[..., None]
            sh = np.clip(blur(shift(self.inside, 1.6, 1.8), 1.2) - self.inside, 0, 1)
            ao = np.clip(blur(self.inside, 2.5), 0, 1)
            J = mort * (1 - 0.45 * sh - 0.22 * ao)[..., None]
        else:
            sh = np.clip(blur(shift(self.inside, 2.5, 3.0), 1.8) - self.inside, 0, 1)
            J = _c(BED) * (1 - 0.5 * sh)[..., None] * (0.9 + 0.15 * noise2d(H, W, 3, 2, 22))[..., None]
        img = col * ins + J * (1 - ins)
        spec_ok = self.inside.copy()
        if self.aged:
            a = self.aged
            dirt = a['dirt']
            img = img * (1 - (0.13 * a['craze'] * dirt)[..., None] * np.array([1.0, 1.03, 1.12], np.float32))
            img = img * (1 - 0.45 * a['speck'])[..., None] + (a['speck'] * 0.45)[..., None] * np.array([0.36, 0.27, 0.2], np.float32)
            pin = a['pin']
            img = img * (1 - 0.45 * pin)[..., None]
            nail = a['nail'] * self.inside
            img = img * (1 - 0.55 * nail)[..., None]
            chip = a['chip']
            if chip.any():
                body = _c(BODY) * (0.8 + 0.2 * noise2d(H, W, 1.5, 2, 33) + 0.08 * noise2d(H, W, 6, 2, 34))[..., None]
                lip = np.clip(chip - shift(chip, 1.5, 1.8), 0, 1)          # inside edge toward the light: shadowed by the glaze lip
                rim = np.clip(chip - shift(chip, -1.2, -1.4), 0, 1)          # far wall of the bite faces the light
                img = img * (1 - chip[..., None]) + body * chip[..., None]
                img = img * (1 - 0.38 * lip)[..., None] + 0.1 * rim[..., None]
                spec_ok = spec_ok * (1 - chip)
            if a['crack'].any():
                ck = a['crack']
                img = img * (1 - 0.5 * ck)[..., None]
                img = img + 0.05 * np.clip(shift(ck, -1, -1) - ck, 0, 1)[..., None]
            if self.grouted:
                gr = a['grime']
                img = img * (1 - dirt * 0.18 * (1 - ins) * gr[..., None])
                img = img * (1 - dirt * 0.03 * gr)[..., None]
        if self.window and self.fired:
            wv = self.window
            F = wv['F']
            cx, cy = W / 2, H / 2
            vx, vy, vz = cx - self.XX, cy - self.YY, np.full((H, W), F, np.float32)
            vl = np.sqrt(vx * vx + vy * vy + vz * vz); vx /= vl; vy /= vl; vz /= vl
            nx, ny = -hx * nz, -hy * nz
            dn = nx * vx + ny * vy + nz * vz
            rx, ry, rz = 2 * dn * nx - vx, 2 * dn * ny - vy, 2 * dn * nz - vz
            t = F / np.maximum(rz, 1e-3)
            px, py = self.XX + rx * t, self.YY + ry * t
            x, y, w, h = wv['rect']
            hx0, hy0 = 2 * x - cx, 2 * y - cy
            Wx, Wy = 2 * w, 2 * h
            s = wv['soft']
            u = (px - (hx0 - Wx / 2)); v = (py - (hy0 - Wy / 2))
            inside_w = smoothstep(-s, s, u) * smoothstep(-s, s, Wx - u) * smoothstep(-s, s, v) * smoothstep(-s, s, Wy - v)
            bars = np.ones_like(u)
            nxp, nyp = wv['panes']
            for j in range(1, nxp):
                bars *= smoothstep(Wx * 0.05, Wx * 0.05 + s, np.abs(u - Wx * j / nxp))
            for j in range(1, nyp):
                bars *= smoothstep(Wy * 0.03, Wy * 0.03 + s, np.abs(v - Wy * j / nyp))
            fr = Wx * 0.06
            bars *= smoothstep(fr, fr + s, u) * smoothstep(fr, fr + s, Wx - u) * smoothstep(fr, fr + s, v) * smoothstep(fr, fr + s, Wy - v)
            sky = 0.78 + 0.22 * np.clip(1 - v / Wy, 0, 1)
            spec = inside_w * bars * sky * wv['strength']
            room = 0.035 * smoothstep(-400, 400, -(px - hx0)) * (1 - inside_w)
            fres = 1 + 2.5 * (1 - dn) ** 3
            sp = np.clip((spec + room) * fres, 0, 0.85) * spec_ok
            img = img + (np.array([0.985, 0.995, 1.0], np.float32) - img) * sp[..., None]     # screen over the glaze
        # room light: brighter toward the window side, soft vignette
        gx = (self.XX / W - 0.25); gy = (self.YY / H - 0.3)
        illum = 1.03 - 0.07 * np.clip(np.hypot(gx * 1.2, gy), 0, 1.2) - 0.08 * ((self.XX / W - 0.5) ** 2 + (self.YY / H - 0.5) ** 2)
        img = img * illum[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name, hide=()):
        """snapshot for the drawing animation; hide = layer names (or 'pounce', or '*' for bare tiles)"""
        self.stages.append((name, self.composite(hide)))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img

