"""xray — an X-ray transmission picture (baggage scanner / radiograph): every object is built as real material
measured along the beam, the beam goes through it by Beer-Lambert, and the result is seen through a line-scan
detector and a display (numpy + Pillow only).

Nothing is painted as a picture of an object. The picture is built in four passes, the way the real thing works:

  1. material   every object adds its *path length along the beam* times its attenuation to two maps, one per
                beam energy (a dual-energy scanner: A_lo at ~60 keV, A_hi at ~120 keV):
                    A_E += mu_E(material) * density * length
                All lengths are canvas px, including depths along the beam; `px_cm` sets the physical scale, so
                1 cm of steel is ~9.5 at low energy and 1 cm of plastic ~0.2 (MATERIALS, approximate values from
                mass attenuation tables). There is no draw order: overlapping things simply add, as on a real film.
                Shapes are 3D bodies, not flat fills:
                  slab     a solid with rounded edges over a closed outline (key, coin, circuit board, plaster bone);
                  shell    a hollow body with a wall (suitcase, hairdryer housing, camera body). Near its outline
                           the beam runs along the side wall, so the path through material is long there: X-ray
                           outlines glow for a physical reason and the middle stays faint;
                  rod      a round wire or rod along a path (chord 2*sqrt(r^2 - d^2)); with `wall` it is a tube
                           (bright edges, darker core). A path may carry depth z per point: where a wire dives along
                           the beam (the turning points of a spring) the chord is longer, so coils show bright
                           turning points and the zig-zag of their near and far halves;
                  coil, zipper, screw, cable, ball, disc (seen face-on: coin with a raised rim, washer, lens whose
                           glass is thickest in the middle, a barrel ring seen end-on is all wall), fabric (folded
                           layers whose turned-over edges read as soft rims, knit / twill / plain weave, creases).
  2. detector   transmission I_E = exp(-A_E). Compton scatter adds a low-frequency haze of the surrounding flux
                (dense objects lose edge contrast and the air around them lifts a little); focal-spot blur; the
                line-scan detector (one column of pixels, the belt drags the bag past it) has its own gain per row,
                so the picture carries faint horizontal streaks and a seam every 64 rows (one detector module);
                quantum (Poisson) noise grows where few photons get through, so metal is grainy and the densest
                parts are photon-starved. Measured A'_E = -ln(I').
  3. display    'film' (radiograph look): dense = bright. Log compression of a mix of both energies, unsharp edge
                enhancement (a bright rim on the inside of every edge, a dark undershoot just outside), phosphor
                glow around bright parts, a blue-steel LUT. 'material' (security pseudo-colour): Zeff from the
                ratio A'_lo / A'_hi -> organic orange, inorganic green, metal blue, opaque black, white where the
                beam went through nothing; the thicker, the deeper the colour.
  4. OSD        crisp monospace overlay at output resolution: status bar, numbered flag boxes, insets of any
                region in either display, a material legend, an attenuation scale whose ticks are computed through
                the same display curve, and text whose readings ({tag.z}, {tag.ml}, {tag.cm2}) are measured from
                that stage's detector image, background-subtracted around the tagged object -- so the numbers
                always agree with the picture.

Stages are cheap: `stage(name)` keeps a float16 copy of both maps and the OSD so far; `save()` runs the detector
and the display for every stage with the same noise, so snapshots differ only where something was added.

    from xray import XRay
    x = XRay(1920, 1080, px_cm=17, seed=1)
    x.belt(120, 980)
    case = x.rrect(700, 550, 1190, 714, 90)
    x.shell(case, 'organic', depth=425, wall=5, edge=70, density=1.2)        # 25 cm deep polycarbonate case
    x.rod(x.path([(300, 300), (600, 360)]), 'steel', 4, wall=0.7)            # a thin steel tube
    x.coil((320, 420), (560, 420), 22, 9, 'steel', 1.2)                      # a spring
    x.slab(x.ellipse(800, 600, 60, 40), 'plaster', 30, tag='rock')
    x.flag(730, 550, 870, 650, 1, 'BONE-LIKE  Zeff {rock.z:.1f}')
    x.save('out.jpg')

Coordinates are canvas px, y down; angles in degrees, clockwise on screen.
"""
import os
import string
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from core import fbm1d, spline, noise2d, smoothstep, load_font


def blur(a, sigma):
    """same 3-box gaussian as core.blur, but slices views instead of np.take copies (half the transient memory
    on full-frame passes)"""
    if sigma <= 0:
        return np.array(a, np.float32)
    out = np.asarray(a, np.float32)
    w = int(np.sqrt(12 * sigma * sigma / 3 + 1))
    w += (w % 2 == 0)
    r = w // 2
    for _ in range(3):
        for ax in (0, 1):
            pad = [(0, 0), (0, 0)]
            pad[ax] = (r + 1, r)
            c = np.cumsum(np.pad(out, pad, mode='edge'), axis=ax, dtype=np.float64)
            d = (c[w:] - c[:-w]) if ax == 0 else (c[:, w:] - c[:, :-w])
            del c
            d /= w
            out = d.astype(np.float32)
            del d
    return out

# linear attenuation coefficients (1/cm) at nominal density, (~60 keV, ~120 keV). Rounded from mass attenuation
# tables x density; good enough that steel, plaster and plastic separate the way they do on a real scanner.
MATERIALS = {
    'organic': (0.200, 0.158),     # plastics, fibre, wood, food, paper (rho ~1)
    'water': (0.206, 0.162),
    'rubber': (0.235, 0.180),
    'pvc': (0.350, 0.215),         # chlorine pushes it toward 'inorganic'
    'pcb': (0.420, 0.265),         # glass-epoxy board
    'magnesium': (0.420, 0.265),
    'mica': (0.620, 0.355),
    'glass': (0.670, 0.380),
    'aluminium': (0.750, 0.420),
    'bone': (0.600, 0.320),
    'plaster': (0.690, 0.360),     # gypsum casting plaster: bone-like
    'ferrite': (4.50, 1.05),
    'zinc': (11.0, 2.30),          # die-cast zinc alloy (zip sliders, padlocks)
    'steel': (9.50, 2.30),
    'brass': (12.6, 2.75),
    'copper': (14.2, 3.00),
    'tin': (30.0, 6.0),            # solder
    'lead': (57.0, 44.0),
}

# A_lo / A_hi ratio -> effective atomic number (calibrated on the table above)
_R_K = np.array([1.10, 1.25, 1.31, 1.56, 1.79, 1.92, 2.60, 4.13, 4.75], np.float32)
_Z_K = np.array([5.0, 7.0, 7.6, 11.0, 13.0, 14.5, 18.5, 26.0, 29.5], np.float32)

FILM = [(0.00, '#03070d'), (0.05, '#071420'), (0.16, '#123049'), (0.32, '#2a5d80'), (0.50, '#5d9cc2'),
        (0.68, '#a6d4ec'), (0.84, '#def3fd'), (1.00, '#ffffff')]
RAMPS = {   # security pseudo-colour: thin -> thick for each material class
    'organic': [(0, '#ffffff'), (0.10, '#fdebcf'), (0.35, '#f5b25e'), (0.65, '#cf7419'), (1.0, '#5a2a05')],
    'inorganic': [(0, '#ffffff'), (0.10, '#e6f3d2'), (0.35, '#9fd07a'), (0.65, '#4b9638'), (1.0, '#123d10')],
    'metal': [(0, '#ffffff'), (0.10, '#dce8fa'), (0.35, '#86b0ec'), (0.65, '#3460c4'), (1.0, '#0b1a55')],
}
CYAN, AMBER, GREEN, RED, INK = '#bfe6fa', '#ffb347', '#79e3a0', '#ff6f59', '#06101a'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _rgb8(h):
    return tuple(int(c * 255 + 0.5) for c in hexc(h))


def lut(stops, n=1024):
    xs = np.array([s for s, _ in stops], np.float32)
    cs = np.stack([hexc(c) for _, c in stops])
    t = np.linspace(0, 1, n, dtype=np.float32)
    return np.stack([np.interp(t, xs, cs[:, k]) for k in range(3)], 1).astype(np.float32)


def _mono(size, bold=False):
    cands = [('/System/Library/Fonts/Menlo.ttc', 1 if bold else 0), ('/System/Library/Fonts/SFNSMono.ttf', 0),
             ('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf' if bold else
              '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 0),
             ('C:/Windows/Fonts/consolab.ttf' if bold else 'C:/Windows/Fonts/consola.ttf', 0)]
    env = os.environ.get('INKPAINT_FONT_MONO')
    if env: cands.insert(0, (env, 0))
    for p, i in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, int(size), index=i)
            except OSError:
                pass
    return load_font('typewriter', size)


class _Reading:
    """what the scanner measures for one tagged object (background-subtracted)"""
    def __init__(self, z=0.0, ml=0.0, cm2=0.0, a=0.0):
        self.z, self.ml, self.cm2, self.a = z, ml, cm2, a


class XRay:
    def __init__(self, W=1920, H=1080, px_cm=17.0, seed=0):
        self.W, self.H, self.px = W, H, float(px_cm)
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.Alo = np.zeros((H, W), np.float32)
        self.Ahi = np.zeros((H, W), np.float32)
        self.tags, self.osd, self.stages = {}, [], []
        self._noise, self._calib = None, None
        self.scan()
        self.film()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ outlines and paths (canvas px)
    @staticmethod
    def _place(P, cx, cy, rot):
        a = np.radians(rot)
        c, s = np.cos(a), np.sin(a)
        P = np.asarray(P, np.float32)
        return np.stack([cx + P[:, 0] * c - P[:, 1] * s, cy + P[:, 0] * s + P[:, 1] * c], 1).astype(np.float32)

    @classmethod
    def rrect(cls, cx, cy, w, h, r=0.0, rot=0.0, n=10):
        """rounded-rectangle outline"""
        r = float(min(max(r, 0), w / 2, h / 2))
        pts = []
        for sx, sy, a0 in [(1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)]:
            ox, oy = sx * (w / 2 - r), sy * (h / 2 - r)
            for a in (np.linspace(a0, a0 + 90, n) if r > 0.5 else [a0 + 45]):
                if r > 0.5:
                    pts.append((ox + r * np.cos(np.radians(a)), oy + r * np.sin(np.radians(a))))
                else:
                    pts.append((sx * w / 2, sy * h / 2))
        return cls._place(pts, cx, cy, rot)

    @classmethod
    def ellipse(cls, cx, cy, rx, ry, rot=0.0, n=96):
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        return cls._place(np.stack([np.cos(t) * rx, np.sin(t) * ry], 1), cx, cy, rot)

    @classmethod
    def poly(cls, pts, cx=0.0, cy=0.0, rot=0.0, scale=1.0):
        """a local outline (list of points) scaled, rotated and moved onto the canvas"""
        return cls._place(np.asarray(pts, np.float32) * scale, cx, cy, rot)

    @staticmethod
    def path(ctrl, per=12):
        """smooth path through control points (Catmull-Rom); points may carry a 3rd value (depth z)"""
        ctrl = np.asarray(ctrl, np.float32)
        if len(ctrl) < 3:
            return ctrl
        return spline(ctrl, per)

    @staticmethod
    def closed(ctrl, per=10):
        """smooth closed outline through control points"""
        c = np.asarray(ctrl, np.float32)
        P = spline(np.vstack([c[-1:], c, c[:2]]), per)
        return P[per:per * (len(c) + 1)]

    @staticmethod
    def offset(P, d):
        """path shifted sideways by d px (positive = to the right of the direction of travel, y down)"""
        P = np.asarray(P, np.float32)
        g = np.gradient(P[:, :2], axis=0)
        g /= np.linalg.norm(g, axis=1, keepdims=True) + 1e-6
        out = P.copy()
        out[:, 0] -= g[:, 1] * d
        out[:, 1] += g[:, 0] * d
        return out

    # ------------------------------------------------------------ geometry kernels
    def _box(self, pts, pad):
        x0 = int(max(0, np.floor(pts[:, 0].min() - pad)))
        y0 = int(max(0, np.floor(pts[:, 1].min() - pad)))
        x1 = int(min(self.W, np.ceil(pts[:, 0].max() + pad) + 1))
        y1 = int(min(self.H, np.ceil(pts[:, 1].max() + pad) + 1))
        return None if x1 <= x0 or y1 <= y0 else (x0, y0, x1, y1)

    def _sdf(self, loops, band):
        """signed distance (px, + inside) to a shape of closed loops (first the outline, then holes; even-odd),
        exact within `band` of an edge, clamped to +-band further away. Returns (x0, y0, D) or None."""
        loops = [np.asarray(L, np.float32)[:, :2] for L in loops]
        b = self._box(np.vstack(loops), 3)
        if b is None:
            return None
        x0, y0, x1, y1 = b
        im = Image.new('L', (x1 - x0, y1 - y0), 0)
        d = ImageDraw.Draw(im)
        for i, L in enumerate(loops):
            d.polygon([(float(x - x0), float(y - y0)) for x, y in L], fill=255 if i == 0 else 0)
        m = np.asarray(im, np.float32) / 255
        bm = blur(np.pad(m, 4), max(1.0, band / 2.4))[4:-4, 4:-4]
        near = (bm > 0.0015) & (bm < 0.9985)
        D = np.where(m > 0.5, band, -band).astype(np.float32)
        ys, xs = np.nonzero(near)
        if len(xs):
            px = (xs + x0).astype(np.float32)
            py = (ys + y0).astype(np.float32)
            d2 = np.full(px.shape, np.inf, np.float32)
            cross = np.zeros(px.shape, np.int32)
            for L in loops:
                A, B = L, np.roll(L, -1, 0)
                for k in range(0, len(A), 16):
                    a, bb = A[k:k + 16], B[k:k + 16]
                    dx, dy = bb[:, 0] - a[:, 0], bb[:, 1] - a[:, 1]
                    l2 = dx * dx + dy * dy + 1e-9
                    for c0 in range(0, len(px), 65536):
                        qx = px[c0:c0 + 65536, None] - a[None, :, 0]
                        qy = py[c0:c0 + 65536, None] - a[None, :, 1]
                        t = np.clip((qx * dx + qy * dy) / l2, 0, 1)
                        ex, ey = qx - t * dx, qy - t * dy
                        np.minimum(d2[c0:c0 + 65536], (ex * ex + ey * ey).min(1), out=d2[c0:c0 + 65536])
                        up = (a[None, :, 1] > py[c0:c0 + 65536, None]) != (bb[None, :, 1] > py[c0:c0 + 65536, None])
                        xi = a[None, :, 0] + qy * dx / np.where(np.abs(dy) < 1e-9, 1e-9, dy)
                        cross[c0:c0 + 65536] += (up & (px[c0:c0 + 65536, None] < xi)).sum(1)
            D[ys, xs] = np.minimum(np.sqrt(d2), band) * np.where(cross % 2 == 1, 1, -1)
        return x0, y0, D

    def _nearest(self, P, px, py):
        """distance from points to the polyline P, plus arc length and segment index of the nearest point"""
        if len(P) == 1:
            P = np.vstack([P, P + 1e-3])
        A, B = P[:-1], P[1:]
        dx, dy = B[:, 0] - A[:, 0], B[:, 1] - A[:, 1]
        ln = np.sqrt(dx * dx + dy * dy)
        s0 = np.concatenate([[0], np.cumsum(ln)]).astype(np.float32)
        l2 = dx * dx + dy * dy + 1e-9
        d2 = np.full(px.shape, np.inf, np.float32)
        sb = np.zeros(px.shape, np.float32)
        ib = np.zeros(px.shape, np.int32)
        for k in range(0, len(A), 16):
            a = A[k:k + 16]
            for c0 in range(0, len(px), 65536):
                sl = slice(c0, c0 + 65536)
                qx = px[sl, None] - a[None, :, 0]
                qy = py[sl, None] - a[None, :, 1]
                t = np.clip((qx * dx[None, k:k + 16] + qy * dy[None, k:k + 16]) / l2[None, k:k + 16], 0, 1)
                ex, ey = qx - t * dx[None, k:k + 16], qy - t * dy[None, k:k + 16]
                e2 = ex * ex + ey * ey
                j = e2.argmin(1)
                m = e2[np.arange(len(j)), j]
                better = m < d2[sl]
                d2[sl] = np.where(better, m, d2[sl])
                sb[sl] = np.where(better, s0[k + j] + t[np.arange(len(j)), j] * ln[k + j], sb[sl])
                ib[sl] = np.where(better, k + j, ib[sl])
        return np.sqrt(d2), sb, ib, s0

    @staticmethod
    def _ext(x, h, rc):
        """extent along the beam of a slab of height h with edges rounded at radius rc, at x px inside its outline"""
        rc = float(min(max(rc, 0.0), h / 2))
        if h <= 0:
            return np.zeros_like(x)
        if rc < 0.05:
            return np.where(x > 0, h, 0).astype(np.float32)
        xc = np.clip(x, 0, rc)
        e = h - 2 * (rc - np.sqrt(np.clip(rc * rc - (rc - xc) ** 2, 0, None)))
        return np.where(x > 0, e, 0).astype(np.float32)

    @staticmethod
    def _aa(D, fn):
        return (fn(D - 0.33) + fn(D) + fn(D + 0.33)) / 3

    def _add(self, x0, y0, t, material, density=1.0, tag=None):
        lo, hi = MATERIALS[material] if isinstance(material, str) else material
        k = density / self.px
        h, w = t.shape
        self.Alo[y0:y0 + h, x0:x0 + w] += t * (lo * k)
        self.Ahi[y0:y0 + h, x0:x0 + w] += t * (hi * k)
        if tag:
            self.tags.setdefault(tag, []).append((x0, y0, t > 0.3))

    # ------------------------------------------------------------ bodies
    def slab(self, outline, material, depth, edge=None, holes=(), density=1.0, tag=None, texture=None):
        """solid `depth` px thick along the beam over a closed outline; edges rounded at radius `edge`
        (default depth/2: a pebble / round bar edge; 0: a sawn edge). holes: outlines cut right through."""
        edge = depth / 2 if edge is None else edge
        r = self._sdf([outline, *holes], band=edge + 2)
        if r is None:
            return
        x0, y0, D = r
        t = self._aa(D, lambda d: self._ext(d, depth, edge))
        if texture is not None:
            t *= texture(x0, y0, t.shape)
        self._add(x0, y0, t, material, density, tag)

    def shell(self, outline, material, depth, wall, edge=None, density=1.0, tag=None, holes=()):
        """hollow body (case, housing): walls `wall` px thick, `depth` px deep along the beam, rounded edges.
        Seen through, the outline is where the beam runs along the wall -> a bright rim, a faint inside."""
        edge = depth / 2 if edge is None else edge
        r = self._sdf([outline, *holes], band=edge + wall + 2)
        if r is None:
            return
        x0, y0, D = r
        fn = lambda d: self._ext(d, depth, edge) - self._ext(d - wall, depth - 2 * wall, edge - wall)
        self._add(x0, y0, self._aa(D, fn), material, density, tag)

    def rod(self, P, material, r, wall=None, density=1.0, tag=None, ribs=None, flat=None):
        """round wire / rod along a path P ((N,2), or (N,3) with depth z in px); r: radius, scalar or per point.
        wall: tube wall thickness (hollow). ribs=(amount, period px): thread / coiled-coil / twisted-strand ripple.
        flat: a flat strip of that thickness instead of a round section (umbrella rib, key blade seen edge-on);
        may be a function of arc length s (px from the first point)."""
        P = np.asarray(P, np.float32)
        z = P[:, 2] if P.shape[1] > 2 else None
        P2 = np.ascontiguousarray(P[:, :2])
        rr = np.broadcast_to(np.asarray(r, np.float32), (len(P2),)).astype(np.float32)
        b = self._box(P2, rr.max() + 3)
        if b is None:
            return
        x0, y0, x1, y1 = b
        im = Image.new('L', (x1 - x0, y1 - y0), 0)
        dr = ImageDraw.Draw(im)
        q = [(float(x - x0), float(y - y0)) for x, y in P2]
        wd = int(np.ceil(2 * rr.max() + 4))
        if len(q) > 1:
            dr.line(q, fill=255, width=wd, joint='curve')
        for x, y in (q[0], q[-1]):
            dr.ellipse([x - wd / 2, y - wd / 2, x + wd / 2, y + wd / 2], fill=255)
        ys, xs = np.nonzero(np.asarray(im))
        if not len(xs):
            return
        d, s, idx, s0 = self._nearest(P2, (xs + x0).astype(np.float32), (ys + y0).astype(np.float32))
        R = np.interp(s, s0, rr)
        if flat is not None:
            fl = flat(s) if callable(flat) else float(flat)
            chord = lambda dd, RR: np.where(np.abs(dd) < RR, fl, 0.0)
        else:
            chord = lambda dd, RR: 2 * np.sqrt(np.clip(RR * RR - dd * dd, 0, None))
        t = (chord(d - 0.33, R) + chord(d, R) + chord(d + 0.33, R)) / 3
        if wall is not None:
            Ri = np.maximum(R - wall, 0)
            t -= (chord(d - 0.33, Ri) + chord(d, Ri) + chord(d + 0.33, Ri)) / 3
        if z is not None:
            seg2 = np.linalg.norm(np.diff(P2, axis=0), axis=1) + 1e-6
            seg3 = np.sqrt(seg2 ** 2 + np.diff(z) ** 2)
            k = np.clip(seg3 / seg2, 1, 7) if len(seg2) else np.ones(1)
            t *= k[np.clip(idx, 0, len(k) - 1)]
        if ribs is not None:
            t *= 1 + ribs[0] * np.cos(2 * np.pi * s / ribs[1])
        tt = np.zeros((y1 - y0, x1 - x0), np.float32)
        tt[ys, xs] = np.maximum(t, 0)
        self._add(x0, y0, tt, material, density, tag)

    def edgeon(self, p0, p1, thick, material, hole=0.0, **kw):
        """a disc or ring seen edge-on (fan, grille, filter, washer on its side): a strip p0 -> p1 `thick` px wide
        whose depth along the beam is the disc's chord at each point"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        R = float(np.linalg.norm(p1 - p0)) / 2

        def f(s):
            out = 2 * np.sqrt(np.clip(R * R - (s - R) ** 2, 0, None))
            if hole:
                out = out - 2 * np.sqrt(np.clip(hole * hole - (s - R) ** 2, 0, None))
            return out
        self.rod(np.stack([p0, p1]), material, thick / 2, flat=f, **kw)

    def tube(self, P, material, r, wall, **kw):
        self.rod(P, material, r, wall=wall, **kw)

    def coil(self, p0, p1, R, turns, material, r_wire, phase=0.0, per=28, density=1.0, tag=None, ribs=None):
        """helical spring / heating coil wound round the axis p0 -> p1 with radius R, seen from the side"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        n = int(turns * per) + 1
        th = np.radians(phase) + np.linspace(0, 2 * np.pi * turns, n)
        u = np.linspace(0, 1, n)[:, None]
        e = (p1 - p0) / (np.linalg.norm(p1 - p0) + 1e-6)
        nrm = np.array([-e[1], e[0]], np.float32)
        P = p0 + (p1 - p0) * u + nrm * (R * np.sin(th))[:, None]
        self.rod(np.column_stack([P, R * np.cos(th)]), material, r_wire, density=density, tag=tag, ribs=ribs)

    def ball(self, cx, cy, r, material, density=1.0, tag=None):
        """a sphere (bearing ball, bead)"""
        self.disc(cx, cy, r, material, 0, dome=2 * r, sphere=True, density=density, tag=tag)

    def disc(self, cx, cy, r, material, depth, hole=0.0, rim=None, dome=0.0, sphere=False, density=1.0, tag=None):
        """round thing seen face-on: coin (rim=(width, extra depth)), washer / ring seen end-on (hole), lens
        (dome > 0: that much thicker in the middle; < 0: concave)"""
        b = self._box(np.array([[cx - r, cy - r], [cx + r, cy + r]], np.float32), 2)
        if b is None:
            return
        x0, y0, x1, y1 = b
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        rr = np.hypot(xx - cx, yy - cy)
        cov = np.clip(r - rr + 0.5, 0, 1)
        if hole:
            cov *= np.clip(rr - hole + 0.5, 0, 1)
        if sphere:
            t = 2 * np.sqrt(np.clip(r * r - rr * rr, 0, None)) + cov * 0
        else:
            u = np.clip(rr / max(r, 1e-3), 0, 1)
            t = depth + dome * (1 - u * u)
            if rim is not None:
                t = t + rim[1] * smoothstep(r - rim[0] - 1.2, r - rim[0], rr)
            t = np.maximum(t, 0) * cov
        self._add(x0, y0, t.astype(np.float32), material, density, tag)

    def zipper(self, P, material='brass', tooth=(8.0, 5.0), pitch=None, depth=4.0, tape=12.0, tag=None):
        """zip: interlocking teeth alternating either side of the path on a woven tape"""
        P = np.asarray(P, np.float32)[:, :2]
        self.rod(P, 'organic', tape / 2, flat=1.6, density=0.8)
        pitch = pitch or tooth[1] * 0.95
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        for i, s in enumerate(np.arange(pitch / 2, L[-1], pitch)):
            x, y = np.interp(s, L, P[:, 0]), np.interp(s, L, P[:, 1])
            j = min(np.searchsorted(L, s), len(P) - 1)
            g = P[j] - P[max(j - 1, 0)]
            ang = np.degrees(np.arctan2(g[1], g[0]))
            side = 1 if i % 2 else -1
            nx, ny = -np.sin(np.radians(ang)), np.cos(np.radians(ang))
            ox = side * tooth[0] * 0.18
            self.slab(self.rrect(x + nx * ox, y + ny * ox, tooth[1] * 0.82, tooth[0], 1.6, rot=ang), material,
                      depth, edge=1.2, tag=tag)

    def screw(self, p0, p1, r, material='steel', head=None, pitch=None, tag=None):
        """machine screw seen from the side: threaded shank p0 -> p1 and a head at p0 (head=(width, height))"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        self.rod(np.stack([p0, p1]), material, r, ribs=(0.16, pitch or r * 0.9), tag=tag)
        if head:
            e = (p1 - p0) / (np.linalg.norm(p1 - p0) + 1e-6)
            ang = np.degrees(np.arctan2(e[1], e[0]))
            c = p0 - e * head[1] / 2
            self.slab(self.rrect(c[0], c[1], head[1], head[0], head[1] * 0.4, rot=ang), material, head[0] * 0.9,
                      edge=head[0] * 0.3, tag=tag)

    def cable(self, P, r=6.0, cores=2, core_r=1.3, jacket='pvc', core='copper', tag=None):
        """mains / USB cable: insulation jacket with stranded copper cores side by side"""
        P = np.asarray(P, np.float32)
        self.rod(P, jacket, r, tag=tag)
        for k in range(cores):
            off = (k - (cores - 1) / 2) * r * 0.95
            self.rod(self.offset(P, off), core, core_r, ribs=(0.22, 3.2), tag=tag)

    # ------------------------------------------------------------ textiles and the belt
    def weave(self, kind='plain', scale=6.0, angle=0.0, amount=0.25, seed=None):
        """texture multiplier for slab(texture=...): 'plain', 'twill' (denim), 'knit' (chevron columns)"""
        sd = self._seed() if seed is None else seed

        def tex(x0, y0, shape):
            h, w = shape
            yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w].astype(np.float32)
            a = np.radians(angle)
            u = (xx * np.cos(a) + yy * np.sin(a)) / scale
            v = (-xx * np.sin(a) + yy * np.cos(a)) / scale
            if kind == 'twill':
                p = np.cos(2 * np.pi * (u + v * 0.5))
            elif kind == 'knit':
                p = np.cos(2 * np.pi * (u + 0.7 * np.abs((v / 1.3) % 1 - 0.5))) * (0.7 + 0.3 * np.cos(2 * np.pi * v / 1.3))
            else:
                p = np.cos(2 * np.pi * u) * np.cos(2 * np.pi * v)
            slub = noise2d(h, w, max(30, 9 * scale), 3, sd) * 2 - 1
            return (1 + amount * p + amount * 0.8 * slub).astype(np.float32)
        return tex

    def fabric(self, outline, depth, layers=6, sheet=2.0, density=0.5, weave='plain', scale=6.0, angle=0.0,
               creases=(), material='organic', tag=None):
        """folded garment: `layers` sheets `sheet` px thick, stacked `depth` px high. Where the cloth turns over
        at a fold the beam runs along it, so fold edges read as soft brighter rims; creases add a ridge."""
        wall = layers * sheet / 2
        tex = self.weave(weave, scale, angle) if weave else None
        r = self._sdf([outline], band=depth / 2 + wall + 2)
        if r is None:
            return
        x0, y0, D = r
        fn = lambda d: self._ext(d, depth, depth / 2) - self._ext(d - wall, depth - 2 * wall, depth / 2 - wall)
        t = self._aa(D, fn)
        if tex is not None:
            t *= tex(x0, y0, t.shape)
        self._add(x0, y0, t, material, density, tag)
        for c in creases:
            self.rod(c, material, 3.0, density=density * 1.6)

    def belt(self, y0, y1, material='rubber', depth=8.0, cords=True, guides=True, lacing=None):
        """the conveyor belt (rubber with lengthwise cords), steel side guides, an optional steel-hook splice"""
        h = y1 - y0
        t = np.full((h, self.W), depth, np.float32)
        if cords:
            yy = np.arange(h, dtype=np.float32)[:, None]
            t *= 1 + 0.06 * np.cos(2 * np.pi * yy / 7.0) + 0.04 * (noise2d(h, self.W, 200, 3, self._seed()) - 0.5)
        self._add(0, int(y0), t, material)
        lo, hi = MATERIALS[material]
        self._calib = (int(y0), (t * (lo / self.px)).astype(np.float32), (t * (hi / self.px)).astype(np.float32))
        if guides:
            for yg, sgn in ((y0 - 14, -1), (y1 + 14, 1)):
                self.rod(np.array([[-10, yg], [self.W + 10, yg]], np.float32), 'steel', 7, wall=1.2)
                self.rod(np.array([[-10, yg + sgn * 10], [self.W + 10, yg + sgn * 10]], np.float32), 'steel', 3,
                         flat=24)
                for xb in np.arange(60, self.W, 240):
                    self.disc(xb, yg + sgn * 20, 6, 'steel', 14, hole=2.5)
        if lacing is not None:
            for yk in np.arange(y0 + 6, y1 - 4, 11.0):
                v = np.array([[lacing - 7, yk - 3], [lacing + 1, yk + 1], [lacing - 7, yk + 5]], np.float32)
                self.rod(v, 'steel', 1.3)
                self.rod(v * [-1, 1] + [2 * lacing + 6, 0], 'steel', 1.3)
            self.rod(np.array([[lacing + 3, y0], [lacing + 3, y1]], np.float32), 'steel', 1.6)

    # ------------------------------------------------------------ detector and display settings
    def scan(self, kv=140, ma=0.8, flux=(1700.0, 5000.0), scatter=0.07, scatter_px=55.0, focal=0.6,
             streak=0.004, module=64):
        """detector: photons per pixel at each energy (noise), scatter fraction and reach, focal-spot blur,
        per-row gain spread of the line-scan detector and its module size"""
        self.det = dict(kv=kv, ma=ma, flux=flux, scatter=scatter, scatter_px=scatter_px, focal=focal,
                        streak=streak, module=module)
        self._noise = None

    def film(self, a0=0.30, amax=8.5, mix=0.35, edge=(0.9, 0.3), glow=0.5, vignette=0.22, stops=FILM):
        """radiograph display: log curve (a0: knee, amax: full white), energy mix, edge enhancement (fine,
        broad), phosphor glow, vignette, LUT"""
        self.disp = dict(a0=a0, amax=amax, mix=mix, edge=edge, glow=glow, vignette=vignette)
        self._lut = lut(stops)

    def _fixed_noise(self):
        if self._noise is None:
            r = np.random.default_rng(self.seed * 7919 + 13)
            H, W, m = self.H, self.W, self.det['module']
            g = 1 + self.det['streak'] * r.standard_normal(H).astype(np.float32)
            mod = np.repeat(1 + self.det['streak'] * 1.6 * r.standard_normal(H // m + 1).astype(np.float32), m)[:H]
            col = 1 + self.det['streak'] * 0.5 * fbm1d(W, 40, 3, int(r.integers(1 << 30)))
            self._noise = (r.standard_normal((H, W), dtype=np.float32), r.standard_normal((H, W), dtype=np.float32),
                           (g * mod).astype(np.float32), col.astype(np.float32))
        return self._noise

    def detect(self, Alo=None, Ahi=None):
        """attenuation maps -> what the detector measures (A'_lo, A'_hi)"""
        Alo = self.Alo if Alo is None else Alo
        Ahi = self.Ahi if Ahi is None else Ahi
        nlo, nhi, grow, gcol = self._fixed_noise()
        dt = self.det
        out = []
        for A, N0, nz in ((Alo, dt['flux'][0], nlo), (Ahi, dt['flux'][1], nhi)):
            I = np.exp(-A.astype(np.float32))
            if dt['focal']:
                I = blur(I, dt['focal'])
            if dt['scatter']:                                   # low-frequency haze: work at 1/4 resolution
                I *= 1 - dt['scatter']
                I += dt['scatter'] / (1 - dt['scatter']) * self._lowpass(I, dt['scatter_px'])
            I *= grow[:, None]
            I *= gcol[None, :]
            I += nz * np.sqrt(np.maximum(I, 0) / N0)
            np.maximum(I, 0.6 / N0, out=I)
            np.log(I, out=I)
            I *= -1
            out.append(np.maximum(I, -0.05, out=I))
        return out

    @staticmethod
    def _lowpass(I, sigma, f=4):
        h, w = I.shape
        hh, ww = max(1, h // f), max(1, w // f)
        small = I[:hh * f, :ww * f].reshape(hh, f, ww, f).mean((1, 3))
        small = blur(small, sigma / f)
        return np.asarray(Image.fromarray(small.astype(np.float32)).resize((w, h), Image.BILINEAR), np.float32)

    def _v(self, A):
        dp = self.disp
        return np.log1p(np.maximum(A, 0) / dp['a0']) / np.log1p(dp['amax'] / dp['a0'])

    def show_film(self, Lo, Hi, vignette=True):
        """film display: dense = bright, edge-enhanced, glowing, blue-steel LUT -> float RGB"""
        dp = self.disp
        v = self._v(dp['mix'] * Lo + (1 - dp['mix']) * Hi).astype(np.float32)
        e1, e2 = dp['edge']
        v = v + e1 * (v - blur(v, 1.4)) + e2 * (v - blur(v, 7))
        if dp['glow']:
            v = v + dp['glow'] * blur(np.clip(v - 0.32, 0, None), 9) + dp['glow'] * 0.35 * blur(np.clip(v - 0.5, 0, None), 28)
        if vignette and dp['vignette']:
            h, w = v.shape
            yy = ((np.arange(h, dtype=np.float32) - h / 2) / (h * 0.62)) ** 2
            xx = ((np.arange(w, dtype=np.float32) - w / 2) / (w * 0.62)) ** 2
            r2 = yy[:, None] + xx[None, :]
            v = v * (1 - dp['vignette'] * np.clip(r2, 0, 1.6) * 0.55) + 0.012 * (1 - np.clip(r2, 0, 1))
        idx = np.clip(v * (len(self._lut) - 1), 0, len(self._lut) - 1).astype(np.int32)
        return self._lut[idx]

    @staticmethod
    def zeff(Lo, Hi):
        R = Lo / np.maximum(Hi, 1e-4)
        Z = np.interp(R, _R_K, _Z_K).astype(np.float32)
        return Z

    def show_material(self, Lo, Hi, k=0.6):
        """security pseudo-colour: hue from Zeff (orange organic, green inorganic, blue metal), depth from how
        much was absorbed, black where nothing got through, white where nothing was"""
        bl, bh = blur(Lo, 0.8), blur(Hi, 0.8)
        Z = self.zeff(bl, bh)
        thin = smoothstep(0.01, 0.07, bh)
        Z = Z * thin + 7.0 * (1 - thin)
        w_org = 1 - smoothstep(9.0, 10.8, Z)
        w_met = smoothstep(17.0, 20.5, Z)
        w_ino = np.clip(1 - w_org - w_met, 0, 1)
        t = 1 - np.exp(-np.maximum(bh, 0) * k)
        idx = np.clip(t * 1023, 0, 1023).astype(np.int32)
        rgb = sum(w[..., None] * lut(RAMPS[c])[idx] for c, w in (('organic', w_org), ('inorganic', w_ino),
                                                                 ('metal', w_met)))
        opaque = smoothstep(4.0, 6.0, bh)[..., None]
        return rgb * (1 - opaque) + hexc('#0c0d10') * opaque

    def _measure(self, tag, Lo, Hi, nparts=None):
        parts = self.tags.get(tag, [])[:nparts]
        if not parts:
            return _Reading()
        x0 = max(0, min(p[0] for p in parts) - 30)
        y0 = max(0, min(p[1] for p in parts) - 30)
        x1 = min(self.W, max(p[0] + p[2].shape[1] for p in parts) + 30)
        y1 = min(self.H, max(p[1] + p[2].shape[0] for p in parts) + 30)
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        for px, py, mk in parts:
            sl = m[py - y0:py - y0 + mk.shape[0], px - x0:px - x0 + mk.shape[1]]
            np.maximum(sl, mk, out=sl)
        inner = m > 0.5
        near = blur(m, 5) > 0.01
        ring = (blur(m, 16) > 0.01) & ~near
        lo, hi = Lo[y0:y1, x0:x1], Hi[y0:y1, x0:x1]
        if ring.sum() < 10 or inner.sum() < 5:
            return _Reading()
        olo = lo[inner] - np.median(lo[ring])
        ohi = hi[inner] - np.median(hi[ring])
        sh = max(float(ohi.sum()), 1e-3)
        ok = ohi > 0.04
        R = float(np.median(olo[ok] / ohi[ok])) if ok.sum() > 20 else float(olo.sum()) / sh
        z = float(np.interp(R, _R_K, _Z_K))
        ml = sh / MATERIALS['water'][1] / self.px ** 2
        return _Reading(z, ml, inner.sum() / self.px ** 2, float(np.median(ohi)))

    # ------------------------------------------------------------ OSD
    def text(self, s, x, y, size=22, colour=CYAN, anchor='la', bold=False, box=None):
        """overlay text; {tag.z} / {tag.ml} / {tag.cm2} are filled with readings of that tag"""
        self.osd.append(('text', s, x, y, size, colour, anchor, bold, box))

    def status(self, left, right=(), y=0, h=58, size=21):
        """top bar: lines of text left and right"""
        self.osd.append(('bar', 0, y, self.W, y + h))
        for i, s in enumerate(left):
            self.text(s, 26, y + 8 + i * 25, size, CYAN if i == 0 else '#8fb9cf', bold=(i == 0))
        for i, s in enumerate(right):
            self.text(s, self.W - 26, y + 8 + i * 25, size, CYAN if i == 0 else '#8fb9cf', 'ra', bold=(i == 0))

    def footer(self, left=(), right=(), h=52, size=19):
        self.osd.append(('bar', 0, self.H - h, self.W, self.H))
        x = 26
        for s, col in left:
            self.text(s, x, self.H - h / 2, size, col, 'lm', box=col if col in (AMBER, GREEN, RED) else None)
            x += _mono(size).getlength(s) + 34
        x = self.W - 26
        for s, col in reversed(list(right)):
            self.text(s, x, self.H - h / 2, size, col, 'rm', box=col if col in (AMBER, GREEN, RED) else None)
            x -= _mono(size).getlength(s) + 30

    def panel(self, x0, y0, x1, y1, title=None, alpha=0.86):
        self.osd.append(('panel', x0, y0, x1, y1, title, alpha))

    def flag(self, x0, y0, x1, y1, n, label, note=None, colour=AMBER, side='top'):
        """numbered alert box: corner brackets, a filled number tag and a label (readings allowed in label/note)"""
        self.osd.append(('flag', x0, y0, x1, y1, n, label, note, colour, side))

    def inset(self, src, dst, mode='material', title=None, frame=CYAN):
        """show region src=(x0, y0, x1, y1) of the scan in dst=(x0, y0, x1, y1) as 'film' or 'material'"""
        self.osd.append(('inset', tuple(src), tuple(dst), mode, title, frame))

    def legend(self, x, y, w, size=17):
        """material classes of the pseudo-colour display"""
        self.osd.append(('legend', x, y, w, size))

    def scale(self, x0, y0, x1, y1, marks, size=16, title=None):
        """attenuation bar in the film display; marks: (label, material, thickness px) placed by the display curve"""
        self.osd.append(('scale', x0, y0, x1, y1, marks, size, title))

    def line(self, pts, colour=CYAN, width=2, dash=None):
        self.osd.append(('line', [tuple(map(float, p)) for p in pts], colour, width, dash))

    def _fmt(self, s, R):
        if '{' not in s:
            return s

        class _Tags(dict):
            def __missing__(self, k):
                return _Reading()
        return string.Formatter().vformat(s, (), _Tags(R))

    @staticmethod
    def _dash(d, pts, col, width, dash):
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            if not dash:
                d.line([(xa, ya), (xb, yb)], fill=col, width=width)
                continue
            L = float(np.hypot(xb - xa, yb - ya))
            for s in np.arange(0, L, dash * 2):
                e = min(L, s + dash)
                d.line([(xa + (xb - xa) * s / L, ya + (yb - ya) * s / L), (xa + (xb - xa) * e / L, ya + (yb - ya) * e / L)],
                       fill=col, width=width)

    def _draw_osd(self, base, items, Lo, Hi, R):
        W, H = self.W, self.H
        bg = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        fg = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        db, df = ImageDraw.Draw(bg), ImageDraw.Draw(fg)
        pastes = []
        for it in items:
            k = it[0]
            if k == 'bar':
                _, x0, y0, x1, y1 = it
                db.rectangle([x0, y0, x1, y1], fill=(3, 9, 15, 205))
                yl = y1 if y0 == 0 else y0
                df.line([(x0, yl), (x1, yl)], fill=_rgb8('#2f5d78') + (255,), width=1)
            elif k == 'panel':
                _, x0, y0, x1, y1, title, alpha = it
                db.rectangle([x0, y0, x1, y1], fill=(3, 9, 15, int(255 * alpha)))
                df.rectangle([x0, y0, x1, y1], outline=_rgb8('#3c7193') + (255,), width=1)
                if title:
                    f = _mono(17, True)
                    df.text((x0 + 14, y0 + 10), title, font=f, fill=_rgb8(CYAN) + (255,))
                    df.line([(x0 + 14, y0 + 36), (x1 - 14, y0 + 36)], fill=_rgb8('#2f5d78') + (255,), width=1)
            elif k == 'text':
                _, s, x, y, size, col, anchor, bold, box = it
                s = self._fmt(s, R)
                f = _mono(size, bold)
                if box:
                    l, t, r, b = df.textbbox((x, y), s, font=f, anchor=anchor)
                    df.rectangle([l - 7, t - 5, r + 7, b + 5], fill=_rgb8(box) + (255,))
                    df.text((x, y), s, font=f, fill=_rgb8(INK) + (255,), anchor=anchor)
                else:
                    df.text((x, y), s, font=f, fill=_rgb8(col) + (255,), anchor=anchor)
            elif k == 'line':
                _, pts, col, width, dash = it
                self._dash(df, pts, _rgb8(col) + (255,), width, dash)
            elif k == 'flag':
                _, x0, y0, x1, y1, n, label, note, col, side = it
                c = _rgb8(col) + (255,)
                L = int(min(30, (x1 - x0) / 4, (y1 - y0) / 4))
                for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
                    df.line([(cx, cy + sy * L), (cx, cy), (cx + sx * L, cy)], fill=c, width=3)
                self._dash(df, [(x0 + L + 6, y0), (x1 - L - 6, y0)], c, 1, 6)
                self._dash(df, [(x0 + L + 6, y1), (x1 - L - 6, y1)], c, 1, 6)
                f, fb = _mono(19), _mono(20, True)
                ty = y0 - 34 if side == 'top' else y1 + 8
                df.rectangle([x0, ty, x0 + 30, ty + 28], fill=c)
                df.text((x0 + 15, ty + 14), str(n), font=fb, fill=_rgb8(INK) + (255,), anchor='mm')
                lab = self._fmt(label, R)
                nt = self._fmt(note, R) if note else ''
                wtxt = fb.getlength(lab) + (22 + f.getlength(nt) if nt else 0)
                db.rectangle([x0 + 31, ty, x0 + 52 + wtxt, ty + 28], fill=(3, 9, 15, 215))     # backing plate
                df.text((x0 + 40, ty + 14), lab, font=fb, fill=c, anchor='lm')
                if nt:
                    df.text((x0 + 40 + fb.getlength(lab) + 22, ty + 14), nt, font=f,
                            fill=_rgb8('#ffd9a0') + (255,), anchor='lm')
            elif k == 'inset':
                _, (sx0, sy0, sx1, sy1), (dx0, dy0, dx1, dy1), mode, title, frame = it
                lo, hi = Lo[sy0:sy1, sx0:sx1], Hi[sy0:sy1, sx0:sx1]
                if mode == 'material' and self._calib is not None:      # belt is part of the air calibration
                    cy0, clo, chi = self._calib
                    lo, hi = lo.copy(), hi.copy()
                    a, b = max(sy0, cy0), min(sy1, cy0 + clo.shape[0])
                    if b > a:
                        lo[a - sy0:b - sy0] -= clo[a - cy0:b - cy0, sx0:sx1]
                        hi[a - sy0:b - sy0] -= chi[a - cy0:b - cy0, sx0:sx1]
                rgb = self.show_material(lo, hi) if mode == 'material' else self.show_film(lo, hi, vignette=False)
                im = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
                pastes.append((im.resize((dx1 - dx0, dy1 - dy0), Image.LANCZOS), (dx0, dy0)))
                df.rectangle([dx0 - 1, dy0 - 1, dx1, dy1], outline=_rgb8(frame) + (255,), width=2)
                if title:
                    df.text((dx0, dy0 - 8), title, font=_mono(16, True), fill=_rgb8(frame) + (255,), anchor='ld')
            elif k == 'legend':
                _, x, y, w, size = it
                f = _mono(size)
                items_ = [('ORGANIC', lut(RAMPS['organic'])[440]), ('INORGANIC', lut(RAMPS['inorganic'])[440]),
                          ('METAL', lut(RAMPS['metal'])[440]), ('OPAQUE', hexc('#0c0d10'))]
                tw = sum(30 + f.getlength(nm) for nm, _ in items_)
                gap = max(10.0, (w - tw) / (len(items_) - 1))
                xx = x
                for nm, cc in items_:
                    df.rectangle([xx, y, xx + 20, y + 20], fill=tuple(int(v * 255) for v in cc) + (255,),
                                 outline=_rgb8('#7fa9c2') + (255,))
                    df.text((xx + 28, y + 10), nm, font=f, fill=_rgb8('#a9cfe3') + (255,), anchor='lm')
                    xx += 28 + f.getlength(nm) + gap
            elif k == 'scale':
                _, x0, y0, x1, y1, marks, size, title = it
                n = int(x1 - x0)
                v = np.linspace(0, 1, n, dtype=np.float32)
                strip = self._lut[np.clip((v * (len(self._lut) - 1)).astype(int), 0, len(self._lut) - 1)]
                im = Image.fromarray((np.repeat(strip[None], int(y1 - y0), 0) * 255).astype(np.uint8))
                pastes.append((im, (int(x0), int(y0))))
                df.rectangle([x0 - 1, y0 - 1, x1, y1], outline=_rgb8('#7fa9c2') + (255,))
                f = _mono(size)
                dp = self.disp
                for i, (lab, mat, th) in enumerate(marks):
                    lo, hi = MATERIALS[mat]
                    A = (dp['mix'] * lo + (1 - dp['mix']) * hi) * th / self.px
                    xv = x0 + float(np.clip(self._v(np.float32(A)), 0, 1)) * (x1 - x0)
                    up = i % 2 == 0
                    df.line([(xv, y0 - (7 if up else 0)), (xv, y1 + (0 if up else 7))], fill=_rgb8(CYAN) + (255,), width=2)
                    df.text((xv, y0 - 9 if up else y1 + 9), lab, font=f, fill=_rgb8('#a9cfe3') + (255,),
                            anchor='md' if up else 'ma')
                if title:
                    df.text((x0, y0 - 34), title, font=_mono(size, True), fill=_rgb8(CYAN) + (255,), anchor='ld')
        out = Image.alpha_composite(base.convert('RGBA'), bg)
        for im, xy in pastes:
            out.paste(im, xy)
        fa = np.asarray(fg)
        a = fa[..., 3:].astype(np.float32) / 255
        pm = fa[..., :3] * a                                            # premultiplied: monitor glow round the OSD
        g = np.asarray(Image.fromarray((pm + 0.5).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3.5)), np.float32)
        o = np.asarray(out.convert('RGB'), np.float32)
        o *= 1 - a
        o += pm + 0.45 * g * (1 - a)
        return Image.fromarray(np.clip(o + 0.5, 0, 255).astype(np.uint8))

    # ------------------------------------------------------------ output
    def composite(self, Alo=None, Ahi=None, n_osd=None, tagparts=None):
        Lo, Hi = self.detect(Alo, Ahi)
        rgb = self.show_film(Lo, Hi)
        base = Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))
        items = self.osd if n_osd is None else self.osd[:n_osd]
        tp = tagparts if tagparts is not None else {k: len(v) for k, v in self.tags.items()}
        need = set()
        for it in items:
            for s in it[1:]:
                if isinstance(s, str) and '{' in s:
                    need |= {f.split('.')[0] for _, f, _, _ in string.Formatter().parse(s) if f}
        R = {t: self._measure(t, Lo, Hi, tp.get(t, 0)) for t in need if tp.get(t, 0)}
        self.readings = R
        return self._draw_osd(base, items, Lo, Hi, R)

    def stage(self, name):
        self.stages.append((name, self.Alo.astype(np.float16), self.Ahi.astype(np.float16), len(self.osd),
                            {k: len(v) for k, v in self.tags.items()}))

    def save(self, path, stages_dir=None):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=88, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, lo, hi, n, tp) in enumerate(self.stages):
                self.composite(lo.astype(np.float32), hi.astype(np.float32), n, tp).save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
