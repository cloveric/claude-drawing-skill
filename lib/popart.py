"""popart — a 1960s pop-art silkscreen painting (the Factory method, after Warhol): one photographic image repeated
in a grid, every panel hand-painted in loud flat acrylic and then over-printed with the same black photo-stencil,
which never quite lines up (numpy + Pillow only).

Model (how the real ones were made, and what each step leaves on the canvas):
  canvas     cotton duck primed with white gesso, photographed flat under even light. The plain weave is a height
             field -- warp and weft crossing over and under, slightly irregular spacing, thicker slubs -- and shows in
             the bare gesso, faintly through paint, and in the ink wherever the film breaks.
  grid       the panels are masked out with tape on one canvas: straight edges, but paint creeps under the tape in a
             few feathered spots; the strips between panels stay bare gesso.
  colour     acrylic, painted by hand *before* the black, from a rough tracing of the photo: first each panel's
             background, then loose flat shapes (face, eyes, nose, collar ...). The shapes are simplified, a little
             too big or too small, and drift off the photograph -- every panel differently. A paint area is flat but
             not dead: a few percent of lightness along the brush direction, thin dry drags, a low ridge where the
             brush stopped, and the weave telegraphing through.
  key        one photographic stencil, made from a high-contrast print of a photo. Only the shadow masses survive:
             solid where the photo was dark, a coarse halftone where it was mid-grey (`tone=`), open where it was
             light, with the grainy wandering edge of a photographic threshold and a few dust specks on the film.
             The key is laid down by hand on every panel: each time a different shift and a hair of rotation against
             the paint.
  pull       the squeegee drags black ink through the mesh in one stroke (`pull=` gives its direction). Starved of
             ink, the film breaks: streaks along the stroke, a nick in the blade leaves a thin skipped line, a dry
             patch where ink has clogged the mesh, the weave valleys left bare -- the colour underneath shows through
             the black. Flooded, the shapes swell, narrow gaps fill in and blobs squeeze past the stencil edge. Every
             panel gets its own mix; `ghost=` adds a faint second impression where the screen was set down twice.
Coordinates: pixels on the canvas; inside a panel you draw in *units* (`Panel.at(u, v)`): the unit origin and size
are chosen per panel, x to the right, y down. Rotations (`turn`, `rot`, brush `direction`) are degrees
counter-clockwise on screen; the squeegee `pull` is a travel direction in screen axes (90 = top to bottom).

    from popart import PopSilkscreen, turn, TURQUOISE, LEMON, HOT_PINK
    ps = PopSilkscreen(1920, 1080, seed=5)
    ps.canvas()
    panels = ps.grid(3, 2, gap=12, margin=14, origin=(0.5, 0.53), unit=0.285)
    p = panels[0]
    ps.ground(p, TURQUOISE)                                    # background, up to the tape
    ps.paint(p, p.shape(face_pts), LEMON, drift=(9, -4))       # loose hand-painted shape, off the photo
    solid = p.shape(shadow_pts); tone = p.soft(p.shape(cheek_pts), 0.08)
    ps.key(p, solid, tone=tone, shift=(-7, 5), rot=0.6, density=0.94)   # the black screen, a bit starved
    ps.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep, spline

# ---------------------------------------------------------------- a loud 1960s acrylic palette
GESSO, INK = '#f1ede3', '#141312'
HOT_PINK, PINK, BLUSH = '#ff3d8f', '#ff86bd', '#ffc2d9'
RED, ORANGE, TANGERINE = '#e8202a', '#ff6a13', '#ff9a1f'
LEMON, YELLOW, CREAM = '#ffe53b', '#ffc21a', '#fff1d2'
LIME, GREEN, MINT = '#c4ec2f', '#22c35e', '#7df0b4'
TURQUOISE, SKY, BLUE = '#14b8c4', '#4fb3ff', '#2253e6'
ULTRA, VIOLET, LILAC = '#3a2fd0', '#8a3ff0', '#c9a6ff'
WHITE = '#fbf8f2'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def closed_spline(pts, per=10):
    """closed Catmull-Rom through control points"""
    P = np.asarray(pts, np.float32)
    n = len(P)
    t = np.linspace(0, 1, per, endpoint=False)[:, None]
    t2, t3 = t * t, t * t * t
    out = []
    for i in range(n):
        p0, p1, p2, p3 = P[i - 1], P[i], P[(i + 1) % n], P[(i + 2) % n]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.concatenate(out, 0)


def turn(pts, deg, about=(0.0, 0.0)):
    """rotate points counter-clockwise on screen (y down) by `deg` about `about`"""
    P = np.asarray(pts, np.float32)
    if not deg: return P
    a = np.deg2rad(deg)
    c, s = np.cos(a), np.sin(a)
    d = P - np.asarray(about, np.float32)
    return np.stack([about[0] + c * d[:, 0] + s * d[:, 1], about[1] - s * d[:, 0] + c * d[:, 1]], 1)


def mirror(pts):
    """reflect points about the vertical unit axis (u -> -u), keeping their order"""
    P = np.array(pts, np.float32)
    P[:, 0] *= -1
    return P


def _sample(a, X, Y):
    """bilinear sample of a 2D array at float pixel coords (edge-clamped)"""
    h, w = a.shape
    X = np.clip(X, 0, w - 1.001); Y = np.clip(Y, 0, h - 1.001)
    x0, y0 = X.astype(np.int32), Y.astype(np.int32)
    fx, fy = X - x0, Y - y0
    return ((a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy)
            + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy)


class Panel:
    """one image of the grid. Canvas rect (x0, y0, x1, y1); masks live in a local window padded by `pad` px on
    every side (so paint can creep under the tape and the key can wander); units map to local px through
    `at(u, v)` = origin + (u, v) * scale."""

    def __init__(self, ps, index, x0, y0, x1, y1, pad, origin, unit):
        self.ps, self.index = ps, index
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
        self.w, self.h = x1 - x0, y1 - y0
        self.pad = pad
        self.lx0, self.ly0 = x0 - pad, y0 - pad                           # local window on the canvas
        self.lw, self.lh = self.w + 2 * pad, self.h + 2 * pad
        self.s = unit * self.h                                             # px per unit
        self.ox = pad + origin[0] * self.w
        self.oy = pad + origin[1] * self.h
        yy, xx = np.mgrid[0:self.lh, 0:self.lw].astype(np.float32)
        self.XX, self.YY = xx, yy
        inside = (np.clip(np.minimum(xx - pad, pad + self.w - xx) + 0.5, 0, 1)
                  * np.clip(np.minimum(yy - pad, pad + self.h - yy) + 0.5, 0, 1))
        self.rect = inside.astype(np.float32)                              # the taped rectangle
        self.tape = self.rect                                              # replaced by ground() (with bleed)

    # ------------------------------------------------------------ units
    def at(self, u, v):
        return self.ox + u * self.s, self.oy + v * self.s

    def _px(self, pts):
        P = np.asarray(pts, np.float32)
        return np.stack([self.ox + P[:, 0] * self.s, self.oy + P[:, 1] * self.s], 1)

    def xy(self, u, v):
        """unit -> canvas px"""
        x, y = self.at(u, v)
        return x + self.lx0, y + self.ly0

    def blank(self):
        return np.zeros((self.lh, self.lw), np.float32)

    # ------------------------------------------------------------ rasterising (4x supersampled, bbox-cropped)
    def _raster(self, polys, ellipses=(), ss=4):
        allp = [p for p in polys if len(p) >= 3]
        boxes = [p for p in allp] + [np.array([[x - r, y - r], [x + r, y + r]]) for x, y, r, _ in ellipses]
        if not boxes: return self.blank()
        B = np.concatenate(boxes, 0)
        bx0 = int(max(0, np.floor(B[:, 0].min()) - 2)); by0 = int(max(0, np.floor(B[:, 1].min()) - 2))
        bx1 = int(min(self.lw, np.ceil(B[:, 0].max()) + 3)); by1 = int(min(self.lh, np.ceil(B[:, 1].max()) + 3))
        out = self.blank()
        if bx1 <= bx0 or by1 <= by0: return out
        im = Image.new('L', ((bx1 - bx0) * ss, (by1 - by0) * ss), 0)
        d = ImageDraw.Draw(im)
        for p in allp:
            d.polygon([((x - bx0) * ss, (y - by0) * ss) for x, y in p], fill=255)
        for x, y, r, ry in ellipses:
            d.ellipse(((x - r - bx0) * ss, (y - ry - by0) * ss, (x + r - bx0) * ss, (y + ry - by0) * ss), fill=255)
        out[by0:by1, bx0:bx1] = np.asarray(im.resize((bx1 - bx0, by1 - by0), Image.BOX), np.float32) / 255
        return out

    # ------------------------------------------------------------ masks (local window, 0..1)
    def shape(self, pts, smooth=True, per=10):
        """filled closed outline through unit control points (Catmull-Rom unless smooth=False)"""
        P = closed_spline(pts, per) if smooth else np.asarray(pts, np.float32)
        return self._raster([self._px(P)])

    def ellipse(self, u, v, ru, rv=None, rot=0.0):
        rv = ru if rv is None else rv
        t = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        P = np.stack([u + ru * np.cos(t), v + rv * np.sin(t)], 1)
        return self._raster([self._px(turn(P, rot, (u, v)))])

    def dots(self, spots):
        """many small discs: [(u, v, r), ...]"""
        return self._raster([], [(*self.at(u, v), r * self.s, r * self.s) for u, v, r in spots])

    def stroke(self, pts, w0, w1=None, smooth=True, caps=True, profile=None, per=8):
        """a filled stroke along unit points, width w0 -> w1 (units); `profile(t)` overrides the taper
        (e.g. lambda t: np.sin(np.pi * t) ** 0.6 for a stripe that swells in the middle)"""
        P = spline(pts, per) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        if len(P) < 2: return self.blank()
        P = self._px(P)
        d = np.gradient(P, axis=0)
        n = np.stack([-d[:, 1], d[:, 0]], 1) / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-6)
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        t = seg / (seg[-1] + 1e-6)
        w1 = w0 if w1 is None else w1
        wid = (w0 + (w1 - w0) * t) if profile is None else w0 * profile(t)
        wid = np.clip(np.nan_to_num(wid), 0, None)                         # sin(pi)**0.7 can be nan
        hw = (wid * self.s / 2)[:, None]
        poly = np.concatenate([P + n * hw, (P - n * hw)[::-1]], 0)
        ell = []
        if caps:
            for i in (0, -1):
                r = float(hw[i, 0])
                if r > 0.3: ell.append((P[i, 0], P[i, 1], r, r))
        return self._raster([poly], ell)

    def soft(self, mask, sigma):
        """a soft tone field from a mask (sigma in units) -- feed it to key(tone=) for a halftone fringe"""
        return blur(mask, sigma * self.s)

    def clip(self, mask):
        """keep a mask inside the taped rectangle"""
        return mask * self.tape


class PopSilkscreen:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.55, -0.8)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.img = np.ones((H, W, 3), np.float32) * _c(GESSO)
        self.weave = np.zeros((H, W), np.float32)                          # thread height, about -1 .. 1
        self.thick = np.zeros((H, W), np.float32)                          # paint film, hides the weave
        self.relief = np.zeros((H, W), np.float32)                         # ridges at paint edges
        self.light_dir = np.array(light, np.float32) / (np.linalg.norm(light) + 1e-6)
        self.room = np.ones((H, W), np.float32)
        self.panels = []
        self.stages = []
        self._grain = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _win(self, p):
        """canvas slices and matching local slices for panel p's window (clipped to the canvas)"""
        cx0, cy0 = max(0, p.lx0), max(0, p.ly0)
        cx1, cy1 = min(self.W, p.lx0 + p.lw), min(self.H, p.ly0 + p.lh)
        return ((slice(cy0, cy1), slice(cx0, cx1)),
                (slice(cy0 - p.ly0, cy1 - p.ly0), slice(cx0 - p.lx0, cx1 - p.lx0)))

    # ------------------------------------------------------------ the support
    def canvas(self, gesso=GESSO, thread=3.8, slub=0.18):
        """gessoed cotton duck: plain weave height field (over / under, jittered spacing, slubs), a slightly uneven
        white ground, and the even light of a studio photograph (a soft falloff toward the corners)"""
        H, W, r = self.H, self.W, self.rng
        jx = (noise2d(H, W, 90, 2, self._seed()) - 0.5) * 0.9                # threads wander a little
        jy = (noise2d(H, W, 90, 2, self._seed()) - 0.5) * 0.9
        sl_w = np.asarray(Image.fromarray(r.random((H // 26 + 2, W // 4 + 2)).astype(np.float32))
                          .resize((W, H), Image.BICUBIC)) - 0.5             # slubs: thicker stretches of thread
        sl_h = np.asarray(Image.fromarray(r.random((H // 4 + 2, W // 26 + 2)).astype(np.float32))
                          .resize((W, H), Image.BICUBIC)) - 0.5
        hgt = np.empty((H, W), np.float32)
        xx = np.arange(W, dtype=np.float32)[None, :]
        for a in range(0, H, 180):                                         # in bands: fewer big temporaries
            b = min(H, a + 180)
            yy = np.arange(a, b, dtype=np.float32)[:, None]
            u, v = xx / thread + jx[a:b], yy / thread + jy[a:b]
            iu, iv = np.floor(u), np.floor(v)
            pw, pv = np.cos(np.pi * (u - iu - 0.5)), np.cos(np.pi * (v - iv - 0.5))   # 1 on a thread's crown
            over = ((iu + iv) % 2) == 0
            hgt[a:b] = np.where(over, pw * (0.62 + 0.38 * pv) * (1 + 2 * slub * sl_w[a:b]),
                                pv * (0.62 + 0.38 * pw) * (1 + 2 * slub * sl_h[a:b]))
        del jx, jy, sl_w, sl_h
        hgt = blur(hgt, 0.55)
        self.weave = ((hgt - hgt.mean()) / (hgt.std() + 1e-6)).astype(np.float32)
        del hgt
        base = _c(gesso) * (1 + 0.012 * (noise2d(H, W, 260, 3, self._seed()) - 0.5))[..., None]
        self.img = base.astype(np.float32)
        yy, xx = np.arange(H, dtype=np.float32)[:, None], np.arange(W, dtype=np.float32)[None, :]
        grad = 1 + 0.022 * (0.5 - (xx / W * 0.6 + yy / H * 0.4))
        vig = 1 - 0.05 * (((xx - W * 0.5) / W) ** 2 + ((yy - H * 0.5) / H) ** 2) * 2
        self.room = (grad * vig).astype(np.float32)
        self.thick[:] = 0

    def grid(self, cols, rows, gap=12, margin=14, origin=(0.5, 0.53), unit=0.285, pad=None):
        """divide the canvas into cols x rows taped panels (row by row); returns the list of Panels.
        origin: where unit (0, 0) sits in each panel (fractions of its width / height); unit: px per unit as a
        fraction of the panel height."""
        pad = int(pad if pad is not None else max(gap, 18))
        xs = np.linspace(margin, self.W - margin + gap, cols + 1)
        ys = np.linspace(margin, self.H - margin + gap, rows + 1)
        self.panels = []
        for j in range(rows):
            for i in range(cols):
                x0, x1 = int(round(xs[i])), int(round(xs[i + 1] - gap))
                y0, y1 = int(round(ys[j])), int(round(ys[j + 1] - gap))
                self.panels.append(Panel(self, len(self.panels), x0, y0, x1, y1, pad, origin, unit))
        return self.panels

    # ------------------------------------------------------------ hand-painted acrylic
    def _brush(self, h, w, angle, length=140.0, width=7.0):
        """zero-mean, unit-std streak texture running along `angle` (deg, ccw)"""
        r = self.rng
        L = int(np.hypot(h, w)) + 8
        out = np.zeros((L, L), np.float32)
        for k, (ln, wd) in enumerate([(length, width), (length * 0.5, width * 3.0)]):
            a = r.standard_normal((max(2, int(L / wd)), max(2, int(L / ln)))).astype(np.float32)
            out += np.asarray(Image.fromarray(a).resize((L, L), Image.BICUBIC)) * (1.0 if k == 0 else 0.6)
        im = Image.fromarray(out).rotate(angle, resample=Image.BILINEAR)
        a = np.asarray(im)[(L - h) // 2:(L - h) // 2 + h, (L - w) // 2:(L - w) // 2 + w]
        return ((a - a.mean()) / (a.std() + 1e-6)).astype(np.float32)

    def _wobble(self, p, m, amp, drift, scale=70.0):
        """re-sample a mask through a low-frequency displacement: a hand-painted edge, `drift` px off the photo"""
        if amp <= 0 and not any(drift): return m
        dx = (noise2d(p.lh, p.lw, scale, 2, self._seed()) - 0.5) * 2 * amp
        dy = (noise2d(p.lh, p.lw, scale, 2, self._seed()) - 0.5) * 2 * amp
        return _sample(m, p.XX - drift[0] - dx, p.YY - drift[1] - dy)

    def paint(self, p, mask, colour, direction=None, wobble=3.0, drift=(0.0, 0.0), opacity=0.97, dry=0.15,
              clip=True, streak=0.012):
        """brush one flat acrylic shape onto panel p. mask: local mask (from Panel.shape / ellipse / stroke ...).
        wobble: px of hand wander along the edge; drift: (dx, dy) px the painter's tracing is off the photo;
        direction: brush angle in degrees (random if None); dry: how much the brush drags thin near the edge;
        streak: lightness variation along the strokes"""
        m = self._wobble(p, mask, wobble, drift)
        if clip: m = m * p.tape
        rows, cols = np.flatnonzero(m.max(1) > 0.004), np.flatnonzero(m.max(0) > 0.004)
        if not len(rows): return
        (cs, ls) = self._win(p)
        y0, y1, x0, x1 = rows[0], rows[-1] + 1, cols[0], cols[-1] + 1
        y0, y1 = max(y0, ls[0].start), min(y1, ls[0].stop)
        x0, x1 = max(x0, ls[1].start), min(x1, ls[1].stop)
        if y1 <= y0 or x1 <= x0: return
        mm = m[y0:y1, x0:x1]
        h, w = mm.shape
        ang = float(self.rng.uniform(-30, 30) if direction is None else direction)
        tex = self._brush(h, w, ang)
        # dry drags: where the brush ran thin, mostly within a band along the edge
        band = np.clip((mm - blur(mm, 6.0)) * 3.0, 0, 1)                    # only near the edge of the shape
        drag = smoothstep(1.4, 2.6, -tex) * band * dry
        cov = np.clip(mm * opacity * (1 - drag), 0, 1)[..., None]
        col = _c(colour)[None, None, :] * (1 + streak * tex[..., None] + 0.006 * self.rng.standard_normal())
        gy0, gx0 = p.ly0 + y0, p.lx0 + x0
        sl = (slice(gy0, gy0 + h), slice(gx0, gx0 + w))
        self.img[sl] = self.img[sl] * (1 - cov) + col * cov
        self.thick[sl] = np.maximum(self.thick[sl], mm * (0.75 + 0.15 * tex))
        rim = np.clip(mm - blur(mm, 1.6), 0, 1)                            # paint piles up where the brush stops
        self.relief[sl] += rim * 0.35 + mm * 0.05 * tex

    def ground(self, p, colour, direction=0.0, bleed=1.0, opacity=0.985):
        """paint panel p's background right up to the tape: straight edges with a few feathered spots where the
        paint crept underneath"""
        r = self.rng
        dist_out = np.maximum(np.maximum(p.pad - p.XX, p.XX - (p.pad + p.w)),
                              np.maximum(p.pad - p.YY, p.YY - (p.pad + p.h)))
        n = noise2d(p.lh, p.lw, 7.0, 3, self._seed())
        spots = smoothstep(0.62, 0.9, noise2d(p.lh, p.lw, 46.0, 2, self._seed()))
        reach = bleed * (0.6 + 4.5 * spots * n)
        creep = np.clip(reach - dist_out, 0, 1) * (dist_out > 0)
        tape = np.maximum(p.rect, creep * (0.55 + 0.45 * n))
        p.tape = tape.astype(np.float32)
        self.paint(p, p.tape, colour, direction=direction, wobble=0.0, opacity=opacity, dry=0.0, clip=False)

    # ------------------------------------------------------------ the photo-stencil and the pull
    def _halftone(self, p, tone, cell, angle):
        a = np.deg2rad(angle)
        u = (p.XX * np.cos(a) + p.YY * np.sin(a)) / cell
        v = (-p.XX * np.sin(a) + p.YY * np.cos(a)) / cell
        d = np.hypot(u - np.floor(u) - 0.5, v - np.floor(v) - 0.5) * cell
        t = np.clip(tone, 0, 1)
        rad = cell * np.sqrt(t / np.pi)
        return np.clip(rad - d + 0.5, 0, 1) * (t > 0.02)

    def _film_grain(self, p):
        """the stencil film's grain, the same for every panel of one size (it is the same screen)"""
        key = (p.lh, p.lw)
        if self._grain is None or self._grain[0] != key:
            g = np.random.default_rng(7).random((p.lh, p.lw)).astype(np.float32)
            g = blur(g, 0.7)
            g = (g - g.mean()) / (g.std() + 1e-6)
            c = noise2d(p.lh, p.lw, 9.0, 2, 11)
            c = (c - c.mean()) / (c.std() + 1e-6)
            self._grain = (key, (0.55 * g + 0.45 * c).astype(np.float32))
        return self._grain[1]

    def stencil(self, p, solid, tone=None, cell=7.0, angle=45.0, grain=0.22, specks=18):
        """the photographic key for panel p: solid masses plus a halftone where `tone` is mid-grey, thresholded
        with film grain (a wandering, slightly granular edge) and a few dust specks"""
        st = np.clip(solid, 0, 1)
        if tone is not None:
            st = np.maximum(st, self._halftone(p, tone, cell, angle))
        g = self._film_grain(p)
        e = blur(st, 0.85) + g * grain * 0.5
        st = smoothstep(0.38, 0.62, e)
        if specks:
            r = np.random.default_rng(101)                                 # same specks on every pull
            near = blur(np.clip(solid, 0, 1), 14) > 0.02
            ys, xs = np.nonzero(near[::4, ::4])
            if len(ys):
                pick = r.choice(len(ys), size=min(specks, len(ys)), replace=False)
                spots = [(xs[i] * 4 + r.uniform(0, 4), ys[i] * 4 + r.uniform(0, 4),
                          r.uniform(0.7, 2.2) * (2.2 if r.random() < 0.12 else 1), 0) for i in pick]
                im = Image.new('L', (p.lw * 2, p.lh * 2), 0)
                d = ImageDraw.Draw(im)
                for x, y, rr, _ in spots:
                    d.ellipse(((x - rr) * 2, (y - rr * r.uniform(0.6, 1)) * 2, (x + rr) * 2, (y + rr) * 2), fill=255)
                st = np.maximum(st, np.asarray(im.resize((p.lw, p.lh), Image.BOX), np.float32) / 255)
        return st.astype(np.float32)

    def _place(self, p, st, rot, sh):
        """lay the screen down by hand: rotate `rot` deg about the panel centre, then shift `sh` px"""
        cx, cy = p.pad + p.w / 2, p.pad + p.h / 2
        a = np.deg2rad(rot)
        c, s = np.cos(a), np.sin(a)
        X, Y = p.XX - sh[0] - cx, p.YY - sh[1] - cy                        # inverse map: canvas -> stencil
        return _sample(st, cx + c * X - s * Y, cy + s * X + c * Y) if rot else _sample(st, X + cx, Y + cy)

    def _film(self, p, density, pull, starve, nicks):
        """ink film thickness over the panel window for one stroke of the squeegee"""
        r = self.rng
        h, w = p.lh, p.lw
        vertical = abs(np.sin(np.deg2rad(pull))) > 0.5
        across_n, along_n = (w, h) if vertical else (h, w)
        def streaks(scale_across, scale_along):
            a = r.random((max(2, int(along_n / scale_along)), max(2, int(across_n / scale_across)))).astype(np.float32)
            im = np.asarray(Image.fromarray(a).resize((across_n, along_n), Image.BICUBIC))
            return im if vertical else im.T
        wide, thin = streaks(40, 260) - 0.5, streaks(3.5, 120) - 0.5
        t = np.deg2rad(pull)                                               # 90: top -> bottom, 0: left -> right
        along = p.XX * np.cos(t) + p.YY * np.sin(t)
        along = (along - along.min()) / (along.max() - along.min() + 1e-6)  # 0 where the stroke starts
        blot = noise2d(h, w, 38, 3, self._seed()) - 0.5
        F = density * (1 + 0.16 * wide + 0.10 * thin + 0.14 * blot - 0.10 * smoothstep(0.3, 1.0, along))
        if starve > 0:                                                     # a patch where ink dried in the mesh
            clog = smoothstep(0.55, 0.8, noise2d(h, w, 120, 2, self._seed()))
            F = F - starve * clog * (0.35 + 0.65 * r.random((h, w)).astype(np.float32))
        for _ in range(nicks):                                             # nicks in the blade -> skipped lines
            pos = r.uniform(0.15, 0.85) * across_n
            wid = r.uniform(1.4, 2.8)
            cross = (p.XX if vertical else p.YY) - pos
            depth = r.uniform(0.35, 0.6) * (0.5 + 0.5 * noise2d(h, w, 50, 2, self._seed()))
            F = F - depth * np.exp(-0.5 * (cross / wid) ** 2)
        return F.astype(np.float32)

    def key(self, p, solid, tone=None, ink=INK, shift=(0.0, 0.0), rot=0.0, density=1.0, flood=0.2, starve=0.0,
            pull=90.0, nicks=1, ghost=None, cell=7.0, angle=45.0, grain=0.22, opacity=0.97):
        """pull the black screen through panel p. solid / tone: local masks (see stencil). shift (px), rot (deg):
        how the screen was laid down against the paint. density: ink film (0.92 starved, 1.0 normal, 1.15 heavy -- below
        about 0.9 the key falls apart); flood:
        0..1, ink squeezed past the stencil (swollen shapes, filled-in gaps, blobs); starve: a dry, clogged
        patch; pull: squeegee direction; nicks: skipped lines from a nicked blade; ghost: (dx, dy, strength) a
        faint second impression. Returns the printed coverage (local)."""
        st = self.stencil(p, solid, tone, cell, angle, grain)
        st = self._place(p, st, rot, shift) * p.rect
        F = self._film(p, density, pull, starve, nicks)
        if flood > 0:                                                      # heavy ink: swell, fill in, blobs
            heavy = np.clip((F - 0.95) * 4, 0, 1)
            sw = blur(st, 1.2 + 2.2 * flood)
            thr = 0.5 - 0.32 * flood * (0.4 + 0.6 * heavy)
            blobs = smoothstep(0.7, 0.92, noise2d(p.lh, p.lw, 16, 2, self._seed())) * flood
            st = np.maximum(st, smoothstep(thr - 0.06, thr + 0.06, sw + blobs * 0.35 * (sw > 0.05)) * p.rect)
        rg = np.random.default_rng(self._seed())
        fine = blur(rg.random((p.lh, p.lw)).astype(np.float32), 0.6)
        fine = (fine - fine.mean()) / (fine.std() + 1e-6)                  # pixel-scale speckle, a little clumped
        clump = noise2d(p.lh, p.lw, 5.0, 2, self._seed()) - 0.5
        (cs, ls) = self._win(p)
        wv = self.weave[cs]
        Fl = F[ls] + 0.035 * wv + 0.05 * fine[ls] + 0.22 * clump[ls]      # the weave's valleys get a little less
        cov = smoothstep(0.66, 0.84, Fl)
        a = np.clip(st[ls] * cov * opacity, 0, 1)
        if ghost:
            gdx, gdy, gs = ghost
            g2 = self._place(p, st, 0.0, (gdx, gdy)) * p.rect
            cov2 = smoothstep(0.62, 0.86, F[ls] * 0.82 + 0.05 * wv + 0.08 * fine[ls] + 0.35 * clump[ls])
            a = 1 - (1 - a) * (1 - np.clip(g2[ls] * cov2 * gs, 0, 1))
        col = _c(ink)[None, None, :]
        self.img[cs] = self.img[cs] * (1 - a[..., None]) + col * a[..., None]
        self.thick[cs] = np.maximum(self.thick[cs], a * 0.35)
        self.relief[cs] += a * 0.12
        return a

    # ------------------------------------------------------------ output
    def composite(self, band=180):
        """the painting photographed: paint ridges and the weave catch the light (computed in row bands)"""
        H, W = self.H, self.W
        out = np.empty((H, W, 3), np.uint8)
        lx, ly = self.light_dir
        for a in range(0, H, band):
            b = min(H, a + band)
            a0, b0 = max(0, a - 2), min(H, b + 2)
            rel = np.pad(self.relief[a0:b0], 1, mode='edge')
            n = rel.shape[0] - 2
            rel = sum(rel[i:i + n, j:j + W] for i in range(3) for j in range(3)) / 9      # 3x3 smoothing
            gy, gx = np.gradient(rel)
            sh = (1 - 0.09 * (lx * gx + ly * gy))[a - a0:a - a0 + (b - a)]
            vis = 1 - 0.72 * np.clip(self.thick[a:b], 0, 1)
            sh = sh * (1 + 0.035 * self.weave[a:b] * vis) * self.room[a:b]
            out[a:b] = (np.clip(self.img[a:b] * sh[..., None], 0, 1) * 255 + 0.5).astype(np.uint8)
        return Image.fromarray(out)

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)                 # 4:4:4 keeps the colour edges crisp
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
