"""linocut — a black-and-white linoleum-block print with one spot-colour block (numpy + Pillow only).

Model:
  block   : a sheet of linoleum glued to a board. Rolled up with ink, the uncut block prints one solid black
            rectangle; everything white in the print is lino the carver *removed*. So the picture is made by
            subtraction: every block is a relief map (uint8, `ss`x the canvas) where 255 = surface that takes
            ink and 0 = cut away. The key block starts solid; a spot-colour block starts cleared and only the
            shapes that should print in colour are left standing. A rim around the key block is never cut, so the
            print has the slightly wobbly black frame of a hand-cut block.
  tools   : every cut is a tapered polygon with a crumbly edge (lino tears a little):
    'v'     V-gouge / liner: starts at a point as the tool dips in, widens with depth, thins out as it is
            lifted -- leaf- and comma-shaped marks (sky streaks, hatching, needles, outlines);
    'u'     U-gouge / scoop: a round head where it bites, a ragged tail where the chip breaks off (snowflakes,
            snow on branches, clearing);
    'knife' constant-width cut with clean ends (window frames, planks);
    'brush' width runs linearly from `width` to `end` (branches, smoke, things you *leave* standing).
            Every tool can also *leave* (cut=False): a line of standing lino in a cleared area prints black.
          Clearing a big area with a wide gouge never leaves a perfectly flat floor: low ridges and islands
          ("chatter") catch a little ink and print as faint broken marks along the gouging direction.
          Shading is never grey: it is the density and width of cuts (white lines in black) or of ridges left
          standing (black lines in white).
  print   : each block is inked with a brayer (an ink film that varies, with faint stop-lines across) and
            burnished by hand with a baren (circular pressure swirls). Ink only reaches the paper where film x
            pressure beats the paper's tooth, so big blacks are "salty": pin-holes where the paper fibres stay
            bare, more of them where the pressure was low, and the swirls of the baren show through. Ink is
            squeezed to the edges of every shape, so edges stay solid even where the middle is salty.
            Overprint: the colour block is printed first, slightly out of register (`offset`), and the key block
            on top -- colour under black disappears, colour that misses a carved window leaves a cream sliver.
            The paper is pressed into the block, so carved (white) areas and the margin stand slightly proud
            and catch the light (a faint emboss around every shape and the plate edge).
  finish  : pencil in the bottom margin (edition number, title, signature) in graphite that only catches
            the top of the paper's tooth, and an optional blind chop (an un-inked embossed seal).

    from linocut import Linocut
    L = Linocut(1920, 1080, block=(100, 56, 1820, 918), seed=3)
    sky = [(100, 56), (1820, 56), (1820, 500), (100, 520)]
    field = [(100, 520), (1820, 500), (1820, 918), (100, 918)]
    L.flow(sky, lambda x, y: 172, n=300, length=(60, 300), width=(2, 6))     # wind streaks cut into the black
    L.moon(1500, 200, 70)
    L.clear(L.poly(field), chatter=0.5)                                        # the snow field cut away
    L.hatch(field, angle=0, spacing=14, width=3, cut=False,                    # drift ridges left standing
            bend=lambda x, y: 12 * np.sin(x / 150 + y / 40), density=lambda x, y: 0.4)
    lamp = L.colour_block('#e8a33a', offset=(4, -3))                          # one spot colour, out of register
    L.cottage(800, 600, 180, 110, 100, side=160, side_windows=[(40, 36, 32, 38)], chimney=(0.5, 20, 40), lit=lamp)
    L.speckle(None, n=1200)                                                    # falling snow
    L.sign('7/30', 'Title', 'Signature 2026'); L.chop(1800, 1010)
    L.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, curve, noise2d, smoothstep, polygon_mask, shift, load_font, text_mask


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _resample(pts, step):
    P = np.asarray(pts, np.float32)
    if len(P) < 2: return P, 0.0
    d = np.linalg.norm(np.diff(P, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(d)])
    L = float(s[-1])
    if L < 1e-3: return P[:1], 0.0
    n = max(2, int(L / step) + 1)
    u = np.linspace(0, L, n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1).astype(np.float32), L


def _soft(m):
    """tiny separable [1 2 1] blur (sub-2px softening; core.blur is a no-op below sigma ~1.2)"""
    p = np.pad(m, 1, mode='edge')
    m = (p[:, :-2] + 2 * p[:, 1:-1] + p[:, 2:]) / 4
    return (m[:-2] + 2 * m[1:-1] + m[2:]) / 4


class Block:
    """one carved block: relief map `a` (uint8, ss x canvas; 255 = uncut surface that takes ink)"""

    def __init__(self, name, colour, shape, offset=(0, 0), seed=0):
        self.name, self.colour, self.offset, self.seed = name, colour, offset, seed
        self.a = np.zeros(shape, np.uint8)


class Linocut:
    def __init__(self, W=1920, H=1080, block=(100, 56, 1820, 918), seed=0, paper='#eee7d4', ink='#1c1a19',
                 ss=2, rim=7):
        self.W, self.H, self.ss = W, H, ss
        self.box = tuple(int(v) for v in block)
        self.rng = np.random.default_rng(seed)
        self.paper_c = _c(paper)
        self.stages = []
        self.chatter = np.zeros((H, W), np.float32)        # faint ink caught by ridges left in cleared areas
        self.pencil = np.zeros((H, W), np.float32)
        self.relief = np.zeros((H, W), np.float32)          # blind emboss (chop)
        self._make_paper()
        self._make_block(rim)
        self.key = Block('key', _c(ink), (H * ss, W * ss), seed=self._seed())
        self.key.a[:] = self._outer
        self.blocks = [self.key]

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ paper and block
    def _make_paper(self):
        H, W, r = self.H, self.W, self.rng
        g = r.random((H, W)).astype(np.float32)
        g = 0.55 * _soft(_soft(g)) + 0.45 * noise2d(H, W, 5, 3, self._seed())
        lo, hi = np.percentile(g[::7, ::7], (2, 98))
        self.grain = np.clip((g - lo) / (hi - lo), 0, 1)                     # paper tooth, 1 = fibre tops
        tone = noise2d(H, W, 420, 3, self._seed())
        fib = Image.new('L', (W, H), 0); d = ImageDraw.Draw(fib)
        for _ in range(2600):                                                 # short wandering fibres
            x, y = r.uniform(0, W), r.uniform(0, H)
            a = r.uniform(0, np.pi); L = r.uniform(6, 26)
            pts = curve((x, y), (x + np.cos(a) * L, y + np.sin(a) * L), r.uniform(-4, 4), 6)
            d.line([tuple(p) for p in pts], fill=int(r.uniform(40, 120)), width=1)
        fib = np.asarray(fib, np.float32) / 255
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        vig = ((xx / W - 0.5) ** 2 + (yy / H - 0.5) ** 2)
        base = self.paper_c[None, None, :] * (0.985 + 0.03 * tone[..., None] - 0.05 * vig[..., None])
        base = base * (1 - 0.035 * fib[..., None]) * (0.985 + 0.03 * self.grain[..., None])
        self.paper = base.astype(np.float32)
        n = r.random((H, W)).astype(np.float32)
        self.crumble = _soft(_soft(n))                                        # edge tear noise
        self.crumble = (self.crumble - self.crumble.mean()) / (self.crumble.std() + 1e-6)

    def _make_block(self, rim):
        """outer edge of the lino (sawn, slightly wavy, rounded corners) and the inner edge of the uncut rim"""
        S, (x0, y0, x1, y1) = self.ss, self.box

        def edge(inset, amp, seed):
            pts = []
            sides = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
            for k, (a, b) in enumerate(sides):
                a, b = np.array(a, np.float32), np.array(b, np.float32)
                L = np.linalg.norm(b - a); n = int(L / 6) + 2
                t = np.linspace(0, 1, n)[:-1]
                dvec = (b - a) / L; nrm = np.array([-dvec[1], dvec[0]])      # points inward (clockwise sides)
                w = fbm1d(n, 40, 4, seed + k)[:-1] * amp
                for ti, wi in zip(t, w):
                    p = a + (b - a) * ti
                    pts.append(p + nrm * (inset + wi))
            return [(float(px) * S, float(py) * S) for px, py in pts]

        im = Image.new('L', (self.W * S, self.H * S), 0)
        ImageDraw.Draw(im).polygon(edge(0.0, 0.8, self._seed()), fill=255)
        self._outer = np.asarray(im).copy()
        im = Image.new('L', (self.W * S, self.H * S), 0)
        ImageDraw.Draw(im).polygon(edge(rim, 2.2, self._seed()), fill=255)
        self._inside = np.asarray(im).copy()                                 # cuttable area

    def colour_block(self, colour, offset=(3, -2), mottle=0.25):
        """a second block for one spot colour; `colour` is how the ink looks printed on this paper.
        It starts cleared: `leave()` the shapes that should print. offset = misregistration in px; mottle = how
        much a light ink shows the paper's tooth and the uneven film (0 = flat)."""
        ink = np.clip(_c(colour) / self.paper_c.mean(), 0, 1)
        b = Block('colour', ink, self.key.a.shape, offset, self._seed())
        b.mottle = mottle
        self.blocks.insert(len(self.blocks) - 1, b)                           # printed before the key block
        return b

    # ------------------------------------------------------------ masks
    def poly(self, pts, smooth=False):
        """1x float mask of a polygon (smooth=True runs a Catmull-Rom spline through the points first)"""
        P = spline(list(pts) + [pts[0]], 8) if smooth else pts
        return polygon_mask(self.H, self.W, P, ss=2)

    def disc(self, cx, cy, r):
        yy, xx = np.ogrid[0:self.H, 0:self.W]
        return np.clip(r + 0.5 - np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2), 0, 1).astype(np.float32)

    def rect(self, x0, y0, x1, y1):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def _bbox(self, region, pad=2):
        if region is None:
            x0, y0, x1, y1 = self.box
        elif isinstance(region, np.ndarray) and region.shape == (self.H, self.W):
            ys, xs = np.nonzero(region > 0.01)
            if len(xs) == 0: return None
            x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        else:
            P = np.asarray(region, np.float32)
            x0, y0 = P.min(0); x1, y1 = P.max(0)
        x0 = int(max(0, np.floor(x0) - pad)); y0 = int(max(0, np.floor(y0) - pad))
        x1 = int(min(self.W, np.ceil(x1) + pad)); y1 = int(min(self.H, np.ceil(y1) + pad))
        if x1 <= x0 or y1 <= y0: return None
        return x0, y0, x1, y1

    def _region(self, region, box):
        """uint8 crop (ss) of a region over `box`: None = whole block, polygon points, or a 1x float mask"""
        S, (x0, y0, x1, y1) = self.ss, box
        if region is None:
            return self._inside[y0 * S:y1 * S, x0 * S:x1 * S]
        if isinstance(region, np.ndarray) and region.shape == (self.H, self.W):
            c = Image.fromarray((np.clip(region[y0:y1, x0:x1], 0, 1) * 255).astype(np.uint8))
            return np.asarray(c.resize(((x1 - x0) * S, (y1 - y0) * S), Image.BILINEAR))
        im = Image.new('L', ((x1 - x0) * S, (y1 - y0) * S), 0)
        P = (np.asarray(region, np.float32) - (x0, y0)) * S
        ImageDraw.Draw(im).polygon([tuple(p) for p in P], fill=255)
        return np.asarray(im)

    def _apply(self, t, box, cut, on, region=None):
        blk = on or self.key
        S, (x0, y0, x1, y1) = self.ss, box
        sl = (slice(y0 * S, y1 * S), slice(x0 * S, x1 * S))
        if region is not None: t = np.minimum(t, self._region(region, box))
        t = np.minimum(t, self._inside[sl])
        a = blk.a[sl]
        if cut: np.minimum(a, 255 - t, out=a)
        else: np.maximum(a, t, out=a)

    def _draw(self, polys, cut, on=None, region=None):
        polys = [p for p in polys if p is not None and len(p) >= 3]
        if not polys: return
        allp = np.concatenate(polys)
        box = self._bbox(allp, 3)
        if region is not None and box is not None:
            rb = self._bbox(region, 2)
            if rb is None: return
            box = (max(box[0], rb[0]), max(box[1], rb[1]), min(box[2], rb[2]), min(box[3], rb[3]))
            if box[2] <= box[0] or box[3] <= box[1]: return
        if box is None: return
        S, (x0, y0, x1, y1) = self.ss, box
        im = Image.new('L', ((x1 - x0) * S, (y1 - y0) * S), 0); d = ImageDraw.Draw(im)
        for p in polys:
            q = (p - (x0, y0)) * S
            d.polygon([tuple(v) for v in q], fill=255)
        self._apply(np.asarray(im), box, cut, on, region)

    # ------------------------------------------------------------ one cut
    def stroke(self, pts, width, tool='v', taper=None, end=None, jitter=0.12, smooth=False):
        """polygon (canvas px) of one gouge mark along `pts`; see the module docstring for the tools"""
        r = self.rng
        P = spline(pts, 10) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        P, L = _resample(P, max(0.7, min(2.5, width * 0.35)))
        n = len(P)
        if n < 2: return None
        t = np.linspace(0, 1, n, dtype=np.float32); s = t * L
        if tool == 'v':
            ta, tb = taper if taper else (r.uniform(0.12, 0.42), r.uniform(0.08, 0.3))
            w = width * np.clip(t / max(ta, 1e-3), 0, 1) ** 0.7 * np.clip((1 - t) / max(tb, 1e-3), 0, 1) ** 0.55
        elif tool == 'u':
            rad = width / 2
            head = np.sqrt(np.clip(1 - np.clip(1 - s / max(rad, 1e-3), 0, 1) ** 2, 0, 1))
            tb = taper[1] if taper else r.uniform(0.12, 0.4)
            w = width * head * np.clip((1 - t) / max(tb, 1e-3), 0, 1) ** 0.7
        elif tool == 'brush':
            e = width * 0.2 if end is None else end
            w = width + (e - width) * t
            cap = min(0.5, 0.8 * width / max(L, 1))
            w = w * np.clip(t / max(cap, 1e-3), 0, 1) ** 0.35
        else:                                                                 # knife
            e = min(0.5, 1.0 / max(L, 1))
            w = width * np.clip(np.minimum(t, 1 - t) / e, 0, 1) ** 0.4
        tg = np.gradient(P, axis=0); tg /= (np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6)
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        k = int(r.integers(1 << 30))
        jl = fbm1d(n, max(3, n / 5), 3, k) * jitter * width
        jr = fbm1d(n, max(3, n / 5), 3, k + 1) * jitter * width
        fade = np.clip(w / max(width, 1e-3) * 3, 0, 1)
        hl = np.maximum(w / 2 + jl * fade, 0); hr = np.maximum(w / 2 + jr * fade, 0)
        return np.concatenate([P + nr * hl[:, None], (P - nr * hr[:, None])[::-1]])

    def gouge(self, pts, width, tool='v', cut=True, on=None, taper=None, end=None, smooth=True, jitter=0.12,
              region=None):
        """one cut (or, cut=False, one line of lino left standing) along `pts`"""
        self._draw([self.stroke(pts, width, tool, taper, end, jitter, smooth)], cut, on, region)

    def jab(self, x, y, size, angle=200, cut=True, on=None):
        """a single short poke of the U-gouge (snowflakes, stipple)"""
        a = np.radians(angle + self.rng.uniform(-25, 25)); L = size * self.rng.uniform(1.0, 1.9)
        self._draw([self.stroke([(x, y), (x + np.cos(a) * L, y + np.sin(a) * L)], size, 'u')], cut, on)

    # ------------------------------------------------------------ many cuts
    def leave(self, shape, on=None):
        """keep a shape standing (prints solid): polygon points or a 1x mask"""
        box = self._bbox(shape)
        if box: self._apply(self._region(shape, box), box, False, on)

    def clear(self, shape, on=None, chatter=0.35, angle=0.0):
        """cut a whole area away with a wide gouge; chatter = how many low ridges and islands survive to
        catch a little ink (gouging direction `angle`, more of them near the edges of the area)"""
        box = self._bbox(shape)
        if not box: return
        t = self._region(shape, box)
        self._apply(t, box, True, on)
        if not chatter or (on is not None and on is not self.key): return
        r, (x0, y0, x1, y1) = self.rng, box
        S = self.ss
        m = np.asarray(Image.fromarray(t).resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        near = np.clip((1 - blur(m, 9)) * 2.2, 0, 1) * m                       # close to the edge of the area
        prob = (0.25 + 0.75 * near) * (m > 0.95)
        n = int(prob.sum() * chatter / 420)
        if n <= 0: return
        flat = prob.ravel() / prob.sum()
        idx = r.choice(flat.size, size=n, p=flat)
        ys, xs = np.divmod(idx, x1 - x0)
        im = Image.new('L', (x1 - x0, y1 - y0), 0); d = ImageDraw.Draw(im)
        for x, y in zip(xs, ys):
            a = np.radians(angle + r.normal(0, 14)); L = r.uniform(6, 30)
            if r.random() < 0.15:                                             # an island the gouge skipped
                rx, ry = r.uniform(1, 3.5), r.uniform(1, 2.5)
                d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=int(r.uniform(90, 200)))
                continue
            nrm = np.array([-np.sin(a), np.cos(a)])
            for q in range(int(r.choice([1, 1, 2, 3]))):                      # neighbouring passes of the gouge
                o = nrm * q * r.uniform(3, 6); Lq = L * r.uniform(0.5, 1.0)
                pts = curve((x + o[0], y + o[1]), (x + o[0] + np.cos(a) * Lq, y + o[1] + np.sin(a) * Lq), r.uniform(-1, 1), 5)
                d.line([tuple(p) for p in pts], fill=int(r.uniform(60, 170)), width=int(r.choice([1, 2, 2])))
        c = np.asarray(im, np.float32) / 255 * m
        sl = self.chatter[y0:y1, x0:x1]
        np.maximum(sl, c, out=sl)

    def hatch(self, region, angle=0.0, spacing=8, width=3, dash=(30, 120), gap=(4, 30), tool='v', cut=True,
              on=None, density=None, bend=None, jitter=0.12, wobble=0.0, box=None):
        """rows of parallel gouge strokes across `region` at `angle` degrees.
        density(x, y) -> 0..1: chance a stroke survives (its width scales with it too) -- this is how a
        linocut shades. bend(x, y) -> px pushed across the row (curved hatching: drifts, contours, folds)."""
        r = self.rng
        box = box or self._bbox(region)
        if not box: return
        x0, y0, x1, y1 = box
        th = np.radians(angle); dv = np.array([np.cos(th), np.sin(th)], np.float32)
        nv = np.array([-dv[1], dv[0]], np.float32)
        c = np.array([(x0 + x1) / 2, (y0 + y1) / 2], np.float32)
        R = 0.5 * np.hypot(x1 - x0, y1 - y0) + 4
        polys = []
        for v in np.arange(-R, R, spacing):
            v = v + r.uniform(-0.2, 0.2) * spacing
            u = -R - r.uniform(0, dash[1])
            while u < R:
                Ld = r.uniform(*dash)
                us = np.linspace(u, u + Ld, max(3, int(Ld / 5)))
                base = c + dv * us[:, None] + nv * v
                off = np.zeros(len(us), np.float32)
                if bend is not None: off = off + bend(base[:, 0], base[:, 1])
                if wobble: off = off + fbm1d(len(us), max(3, len(us) / 3), 2, int(r.integers(1 << 30))) * wobble
                pts = base + nv * off[:, None]
                mx, my = pts[len(pts) // 2]
                if x0 - 40 <= mx <= x1 + 40 and y0 - 40 <= my <= y1 + 40:
                    dn = float(np.clip(density(mx, my), 0, 1)) if density else 1.0
                    if r.random() < dn:
                        polys.append(self.stroke(pts, width * (0.55 + 0.45 * dn), tool, jitter=jitter))
                u += Ld + r.uniform(*gap)
        self._draw(polys, cut, on, region)

    def flow(self, region, field, n=200, length=(40, 200), width=(2, 5), tool='v', cut=True, on=None, step=3.0,
             density=None, seeds=None, jitter=0.12, taper=None):
        """strokes that follow a direction field: field(x, y) -> angle in degrees (wind, smoke, fur, water)"""
        r = self.rng
        box = self._bbox(region)
        if not box: return
        x0, y0, x1, y1 = box
        polys = []
        for i in range(n if seeds is None else len(seeds)):
            if seeds is not None:
                x, y = seeds[i]
            else:
                for _ in range(30):
                    x, y = r.uniform(x0, x1), r.uniform(y0, y1)
                    if density is None or r.random() < density(x, y): break
                else:
                    continue
            L = r.uniform(*length); pts = [(x, y)]
            for _ in range(max(2, int(L / step))):
                a = np.radians(field(x, y)); x += np.cos(a) * step; y += np.sin(a) * step
                pts.append((x, y))
            polys.append(self.stroke(pts, r.uniform(*width), tool, taper=taper, jitter=jitter))
        self._draw(polys, cut, on, region)

    def speckle(self, region=None, n=500, size=(2, 6), angle=200, stars=0.015, on_ink=True):
        """falling snow / stipple: U-gouge pokes, a few six-point flakes made of three crossing V nicks.
        on_ink: only bother where the block still has surface (a poke in a cleared area prints nothing)"""
        r, S = self.rng, self.ss
        box = self._bbox(region)
        if not box: return
        x0, y0, x1, y1 = box
        polys = []
        for _ in range(n):
            for _ in range(20):
                x, y = r.uniform(x0, x1), r.uniform(y0, y1)
                if not on_ink or self.key.a[int(y * S), int(x * S)] > 128: break
            else:
                continue
            if r.random() < stars:
                s = r.uniform(size[1] * 1.3, size[1] * 2.4); a0 = r.uniform(0, 60)
                for k in range(3):
                    a = np.radians(a0 + 60 * k)
                    polys.append(self.stroke([(x - np.cos(a) * s, y - np.sin(a) * s), (x + np.cos(a) * s, y + np.sin(a) * s)],
                                             s * 0.32, 'v', taper=(0.45, 0.45), jitter=0.05))
            else:
                sz = r.uniform(*size); a = np.radians(angle + r.uniform(-25, 25)); L = sz * r.uniform(0.9, 1.8)
                polys.append(self.stroke([(x, y), (x + np.cos(a) * L, y + np.sin(a) * L)], sz, 'u'))
        self._draw(polys, True, None, region)

    def rings(self, cx, cy, radii, width=3.0, arc=(0.5, 1.8), gap=(0.06, 0.35), tool='v', cut=True, on=None,
              squash=1.0):
        """broken concentric cuts (a halo of rings round a moon or a lamp, ripples, growth rings)"""
        r = self.rng
        polys = []
        for R in radii:
            a = r.uniform(0, 2 * np.pi); end = a + 2 * np.pi
            while a < end:
                da = min(r.uniform(*arc), end - a)
                if da > 0.08:
                    t = np.linspace(a, a + da, max(4, int(R * da / 4)))
                    rr = R * (1 + 0.012 * fbm1d(len(t), 8, 2, int(r.integers(1 << 30))))
                    polys.append(self.stroke(np.stack([cx + np.cos(t) * rr, cy + np.sin(t) * rr * squash], 1),
                                             width * r.uniform(0.7, 1.15), tool))
                a += da + r.uniform(*gap)
        self._draw(polys, cut, on)

    def outline(self, shape, width=3.0, on=None, cut=True):
        """cut a thin white contour round a shape so a black thing still reads against a black ground
        (the classic linocut halo); then leave() or draw the shape itself. cut=False leaves a black contour
        instead (a white thing crossing a white ground)"""
        box = self._bbox(shape, int(width) + 4)
        if not box: return
        S = self.ss
        t = self._region(shape, box).astype(np.float32) / 255
        dil = blur(t, max(0.8, width * S * 0.55)) > 0.04
        ring = (dil & (t < 0.5)).astype(np.uint8) * 255
        self._apply(ring, box, cut, on)

    def mask_of(self, polys):
        """1x float mask of a list of stroke polygons (to outline or clip a group of strokes)"""
        im = Image.new('L', (self.W * 2, self.H * 2), 0); d = ImageDraw.Draw(im)
        for p in polys:
            if p is not None and len(p) >= 3: d.polygon([tuple(v * 2) for v in p], fill=255)
        return np.asarray(im.resize((self.W, self.H), Image.BOX), np.float32) / 255

    # ------------------------------------------------------------ things
    def moon(self, cx, cy, r, rings=(1.45, 1.8, 2.2, 2.65), shade=True):
        """a carved-out moon: the disc cleared, a crescent of curved ridges left on the shadow side, a few
        maria, broken rings cut round it"""
        self.clear(self.disc(cx, cy, r), chatter=0.25, angle=-30)
        if shade:
            k = 0
            for f in np.linspace(1.02, 1.4, 5):
                t = np.linspace(-0.4, 2.0, 60)
                ox, oy = cx - r * 0.42, cy - r * 0.36
                P = np.stack([ox + np.cos(t) * r * f, oy + np.sin(t) * r * f], 1)
                self.gouge(P, 2.2 + 2.0 * k / 4, 'v', cut=False, smooth=False, region=self.disc(cx, cy, r - 1.5))
                k += 1
        self.rings(cx, cy, [r * f for f in rings], width=3.0, arc=(0.35, 1.2), gap=(0.15, 0.6))

    def pine(self, x, y, h, w=None, tiers=None, snow=0.8, halo=2.5, nicks=0.5, region=None):
        """a snow-loaded spruce left standing: stacked drooping tiers, white snow bands cut along the top of
        each tier, V nicks for needles on the lit side, an optional white halo against a black ground"""
        r = self.rng
        w = w or h * 0.46
        k = tiers or max(3, int(h / 24))
        polys, edges = [], []
        for i in range(k):
            yt = y - h + h * 0.86 * i / k
            yb = y - h + h * 0.86 * (i + 1.55) / k
            hw = w / 2 * (0.22 + 0.78 * (i + 1) / k) * r.uniform(0.9, 1.08)
            tips = int(np.clip(hw / 9, 2, 7))
            low = []
            for j in range(tips + 1):
                fx = -1 + 2 * j / tips
                ty = yb + r.uniform(-0.12, 0.08) * (yb - yt) - abs(fx) * 0.12 * (yb - yt)
                low.append((x + fx * hw, ty))
                if j < tips:
                    low.append((x + (fx + 1 / tips) * hw * 0.98, ty - r.uniform(0.18, 0.32) * (yb - yt)))
            P = [(x, yt)] + [(x + hw * 0.55, yt + (yb - yt) * 0.55)] + low[::-1] + [(x - hw * 0.55, yt + (yb - yt) * 0.55)]
            polys.append(np.array(P, np.float32)); edges.append((low, yb - yt))
        polys.append(np.array([(x - w * 0.05, y - h * 0.15), (x + w * 0.05, y - h * 0.15), (x + w * 0.06, y), (x - w * 0.06, y)], np.float32))
        m = self.mask_of(polys)
        if region is not None: m = m * (region if isinstance(region, np.ndarray) else self.poly(region))
        if halo: self.outline(m, halo)
        self.leave(m)
        if snow:
            cuts = []
            for i in range(1, k):
                low, th = edges[i - 1]
                band = np.array(low, np.float32)
                band = band[np.argsort(band[:, 0])]
                for j in range(len(band) - 1):
                    if r.random() > snow: continue
                    a, b = band[j], band[j + 1]
                    mid = (a + b) / 2 + (0, th * r.uniform(0.18, 0.3))
                    cuts.append(self.stroke([a + (0, th * 0.16), mid, b + (0, th * 0.16)], th * r.uniform(0.16, 0.26), 'u',
                                            smooth=True))
            sm = self.mask_of(cuts) * m
            self._apply_mask(sm, True)
        if nicks:
            cuts = []
            for i in range(k):
                yt = y - h + h * 0.86 * i / k; yb = y - h + h * 0.86 * (i + 1.55) / k
                for _ in range(int(nicks * 5)):
                    fy = r.uniform(0.45, 0.85); yy = yt + (yb - yt) * fy
                    hw = w / 2 * (0.22 + 0.78 * (i + 1) / k) * fy
                    xx = x + r.uniform(0.15, 0.85) * hw
                    cuts.append(self.stroke([(xx, yy), (xx + hw * 0.3, yy + (yb - yt) * 0.18)], r.uniform(1.6, 2.6), 'v'))
            self._apply_mask(self.mask_of(cuts) * m, True)

    def _apply_mask(self, m, cut, on=None):
        box = self._bbox(m)
        if box: self._apply(self._region(m, box), box, cut, on)

    def bare_tree(self, x, y, h, lean=0.0, spread=1.0, width=None, depth=6, halo=3.0, snow=True, seed=None):
        """a leafless tree left standing as tapered branches; a halo where it crosses black, snow cut along
        the top of the thicker branches. Returns the 1x mask of the tree."""
        r = np.random.default_rng(seed if seed is not None else self._seed())
        width = width or h * 0.05
        segs = []

        def grow(p, ang, L, wd, d):
            if d > depth or wd < 0.9 or L < 6: return
            bend = r.uniform(-0.18, 0.18) * L
            q = (p[0] + np.cos(ang) * L, p[1] + np.sin(ang) * L)
            pts = curve(p, q, bend, 14, wig=L * 0.03, seed=int(r.integers(1 << 30)))
            tip = d >= depth or wd * 0.62 < 0.9
            segs.append((pts, wd, 0.5 if tip else wd * 0.62))
            nb = 2 if d < 2 else int(r.choice([2, 2, 3])) if d < 4 else int(r.choice([1, 2, 2]))
            for j in range(nb):
                da = (j - (nb - 1) / 2) * r.uniform(0.45, 0.8) * spread + r.normal(0, 0.12)
                if d == 0 and nb == 2: da *= 1.25
                grow(q, ang + da - 0.12 * np.sign(np.cos(ang + da)) * (d > 1), L * r.uniform(0.62, 0.8), wd * 0.62, d + 1)

        grow((x, y), -np.pi / 2 + lean, h * 0.36, width, 0)
        polys = [self.stroke(pts, w0, 'brush', end=w1, jitter=0.06) for pts, w0, w1 in segs]
        rootw = width * 1.05                                                 # flare into the ground
        polys.append(np.array([(x - rootw, y + 4), (x - width * 0.45, y - h * 0.08), (x + width * 0.45, y - h * 0.08), (x + rootw, y + 4)], np.float32))
        m = self.mask_of(polys)
        if halo: self.outline(m, halo)
        self.leave(m)
        if snow:
            cuts = []
            for pts, w0, w1 in segs:
                if w0 < 4: continue
                P = np.asarray(pts)
                dx, dy = P[-1] - P[0]
                if abs(dy) > abs(dx) * 1.6: continue                            # snow sits on the flatter limbs
                lift = np.array([0, -w0 * 0.28], np.float32)
                cuts.append(self.stroke(P[2:-2] + lift, w0 * 0.34, 'u', taper=(0, 0.35)))
            self._apply_mask(self.mask_of(cuts) * m, True)
        return m

    def cottage(self, x, base, fw, wall, roof, side=0.0, rise=0.1, windows=(), side_windows=(), door=None,
                chimney=None, lit=None, planks=8.0, snow=14.0, icicles=True, attic=False):
        """a snowy cottage, gable end to the viewer: black front with vertical boards cut in, a side wall
        receding to the right with horizontal boards, roofs heavy with snow (cleared white) and a few drift
        ridges, icicles cut under the eave. windows: (u, v, w, h) in px from the front's bottom-left corner;
        side_windows: (u, v, w, h) along the side wall. door: (u, w, h, open). lit: a colour block -> lit
        windows print in it. Returns a dict of geometry (apex, chimney top, door rect, window rects)."""
        r = self.rng
        k = -rise
        ax, ay = x + fw / 2, base - wall - roof
        eL, eR = (x, base - wall), (x + fw, base - wall)
        dv = np.array([side, side * k], np.float32)
        front = [(x, base), (x, base - wall), (ax, ay), (x + fw, base - wall), (x + fw, base)]
        sidew = [(x + fw, base), (x + fw + side, base + side * k), (x + fw + side, base - wall + side * k), (x + fw, base - wall)]
        roofp = [(ax, ay), (ax + dv[0], ay + dv[1]), (eR[0] + dv[0] + 6, eR[1] + dv[1] + 4), (eR[0] + 6, eR[1] + 4)]
        self.outline(self.poly(front), 2.5)
        self.leave(front)
        if side > 0:
            self.leave(sidew)
            # boards on the side wall: horizontal knife cuts, broken
            for i in range(1, int(wall / planks)):
                yy = base - wall + i * planks
                p0 = np.array([x + fw + 3, yy]); p1 = np.array([x + fw + side - 3, yy + side * k])
                f0 = r.uniform(0, 0.25); f1 = r.uniform(0.6, 1.0)
                self.gouge([p0 + (p1 - p0) * f0, p0 + (p1 - p0) * f1], r.uniform(1.4, 2.2), 'v', smooth=False,
                           region=sidew)
        # vertical boards on the front
        for xx in np.arange(x + 8, x + fw - 4, planks * 1.25):
            top = base - wall + 4 if abs(xx - ax) > fw * 0.3 else ay + roof * 0.35 + abs(xx - ax) * roof / (fw / 2) * 0.6
            yb = base - r.uniform(2, 10); yt = top + r.uniform(4, 30)
            self.gouge([(xx, yt), (xx + r.uniform(-1, 1), yb)], r.uniform(1.3, 2.0), 'v', smooth=False, region=front)
        geo = {'apex': (ax, ay), 'windows': [], 'door': None}
        # roof snow: side plane cleared, thick snow lip along the front gable edges
        if side > 0:
            lip = [(ax, ay - snow * 0.8), (ax + dv[0], ay + dv[1] - snow * 0.8)]
            bulge = []
            n = 9
            for i in range(n + 1):
                f = i / n
                p = np.array(eR) + dv * f
                bulge.append((p[0] + 6, p[1] + 5 + snow * 0.25 * np.sin(np.pi * f * 3 + r.uniform(0, 1)) ** 2))
            snowp = lip + bulge[::-1]
            self.clear(self.poly(snowp, smooth=False), chatter=0.2, angle=np.degrees(np.arctan2(eR[1] - ay, eR[0] - ax)))
            # drift ridges on the roof running down the slope, sparse
            slope = np.degrees(np.arctan2(eR[1] - ay, eR[0] - ax))
            self.hatch(snowp, angle=slope, spacing=9, width=2.2, dash=(18, 60), gap=(20, 70), cut=False,
                       density=lambda xx, yy: 0.45)
            self.gouge([(eR[0] + 4, eR[1] + 7), (eR[0] + dv[0] + 6, eR[1] + dv[1] + 7)], 3.0, 'knife', cut=False,
                       smooth=False)
        lipL = [(x - 10, base - wall + 4), (ax, ay - snow), (ax + 3, ay + snow * 0.7), (x + 2, base - wall + snow * 0.6)]
        self.clear(self.poly(lipL), chatter=0.0)
        lipR = [(ax - 3, ay - snow), (x + fw + 10, base - wall + 2), (x + fw - 2, base - wall + snow * 0.6), (ax, ay + snow * 0.7)]
        self.clear(self.poly(lipR), chatter=0.0)
        # eave line left standing under the snow lips
        self.gouge([(x - 6, base - wall + snow * 0.62 + 1), (ax, ay + snow * 0.78)], 2.4, 'knife', cut=False, smooth=False)
        self.gouge([(ax, ay + snow * 0.78), (x + fw + 6, base - wall + snow * 0.62 + 1)], 2.4, 'knife', cut=False, smooth=False)
        if icicles and side > 0:
            for i in range(int(side / 9)):
                f = (i + r.uniform(0.2, 0.8)) / (side / 9)
                p = np.array(eR) + dv * f + (6, 10)
                L = r.uniform(5, 18)
                self.gouge([p, p + (r.uniform(-1, 1), L)], r.uniform(2.2, 3.6), 'v', taper=(0.05, 0.9), smooth=False)
        if attic:
            self.clear(self.disc(ax, ay + roof * 0.55, roof * 0.12), chatter=0)
            self.leave([(ax - 1.3, ay + roof * 0.43), (ax + 1.3, ay + roof * 0.43), (ax + 1.3, ay + roof * 0.67), (ax - 1.3, ay + roof * 0.67)])
        for (u, v, ww, wh) in windows:
            geo['windows'].append(self._window(x + u, base - v - wh, ww, wh, lit))
        for (u, v, ww, wh) in side_windows:
            x0 = x + fw + u; y0 = base - v - wh + u * k
            geo['windows'].append(self._window(x0, y0, ww, wh, lit, skew=k))
        if door:
            u, dw, dh, op = door
            d0, d1 = x + u, x + u + dw
            rect = [(d0, base - dh), (d1, base - dh), (d1, base + 1), (d0, base + 1)]
            if op:
                self.clear(self.poly(rect), chatter=0)
                if lit is not None: self.leave(self.poly([(d0 - 1, base - dh - 1), (d1 + 1, base - dh - 1), (d1 + 1, base + 2), (d0 - 1, base + 2)]), on=lit)
                self.leave([(d0, base - dh), (d0 + dw * 0.3, base - dh + 6), (d0 + dw * 0.3, base + 3), (d0, base + 1)])   # door leaf swung in
                self.gouge([(d0 + dw * 0.12, base - dh * 0.55), (d0 + dw * 0.2, base - dh * 0.53)], 2.2, 'knife', smooth=False)
            else:
                self.gouge([(d0, base - dh), (d1, base - dh)], 2, 'knife', smooth=False)
                self.gouge([(d0, base - dh), (d0, base)], 2, 'knife', smooth=False)
                self.gouge([(d1, base - dh), (d1, base)], 2, 'knife', smooth=False)
            geo['door'] = (d0, base - dh, d1, base)
        if chimney:
            u, cw, ch = chimney
            cx0 = ax + dv[0] * u
            cy = ay + dv[1] * u + (eR[1] - ay) * 0.3
            cp = [(cx0, cy - ch), (cx0 + cw, cy - ch), (cx0 + cw, cy + 12), (cx0, cy + 12)]
            self.outline(self.poly(cp), 2.5)
            self.leave(cp)
            self.clear(self.poly([(cx0 - 4, cy - ch + 2), (cx0 + cw / 2, cy - ch - 8), (cx0 + cw + 4, cy - ch + 2), (cx0 + cw + 3, cy - ch + 6), (cx0 - 3, cy - ch + 6)]), chatter=0)
            for yy in (cy - ch + 16, cy - ch + 30):
                xa = cx0 + r.uniform(2, cw * 0.4)
                self.gouge([(xa, yy), (xa + cw * 0.45, yy + r.uniform(-1, 1))], 1.5, 'v', smooth=False)
            geo['chimney'] = (cx0 + cw / 2, cy - ch - 6)
        return geo

    def _window(self, x0, y0, w, h, lit, skew=0.0):
        quad = [(x0, y0), (x0 + w, y0 + w * skew), (x0 + w, y0 + h + w * skew), (x0, y0 + h)]
        if lit is not None:
            self.clear(self.poly(quad), chatter=0)
            self.leave(self.poly([(x0 - 0.5, y0 - 0.5), (x0 + w + 0.5, y0 + w * skew - 0.5), (x0 + w + 0.5, y0 + h + w * skew + 0.5), (x0 - 0.5, y0 + h + 0.5)]), on=lit)
        else:
            self.clear(self.poly(quad), chatter=0)
            for f in (0.3, 0.55, 0.8):                                         # a dark window: ridges left
                self.gouge([(x0, y0 + h * f), (x0 + w, y0 + h * f + w * skew)], 2.0, 'knife', cut=False, smooth=False)
        cx = x0 + w / 2
        self.gouge([(cx, y0 + w / 2 * skew), (cx, y0 + h + w / 2 * skew)], max(2.2, w * 0.1), 'knife', cut=False, smooth=False)
        self.gouge([(x0, y0 + h * 0.45), (x0 + w, y0 + h * 0.45 + w * skew)], max(2.2, w * 0.1), 'knife', cut=False, smooth=False)
        # snow on the sill
        self.gouge([(x0 - 3, y0 + h + 3), (x0 + w + 3, y0 + h + 3 + w * skew)], 4.0, 'u', taper=(0, 0.2), smooth=False)
        return quad

    def smoke(self, x, y, rise=160, drift=-220, width=10, edge=2.2):
        """chimney smoke cut out of the sky as a chain of billows that rise, lean with the wind and grow; each
        billow keeps a curl of black ridge on its shadow side; where it crosses something white a thin black
        edge is left standing so it still reads"""
        r = self.rng
        j = lambda k: r.normal(0, 0.09) * rise                                # no two plumes alike
        ctrl = [(x, y), (x + drift * 0.04 + j(0) * 0.3, y - rise * 0.35), (x + drift * 0.25 + j(1), y - rise * 0.72 + j(1) * 0.5),
                (x + drift * 0.6 + j(2), y - rise * 0.92 + j(2)), (x + drift, y - rise + j(3))]
        P, L = _resample(spline(ctrl, 12), 1.0)
        polys, curls = [], []
        rad = []                                                              # billows grow; spaced to overlap
        while sum(rad) * 0.8 < L and len(rad) < 60:
            f = min(1.0, sum(rad) * 0.8 / max(L, 1))
            rad.append(width * (0.5 + 1.25 * f) * r.uniform(0.85, 1.15))
        pos = np.cumsum([0.0] + [q * 0.8 for q in rad[:-1]])
        pos = pos * (L - rad[-1] * 0.5) / max(pos[-1], 1)
        for rr, sp in zip(rad, pos):
            c = P[min(len(P) - 1, int(sp))] + r.uniform(-0.12, 0.12, 2) * rr
            polys.append(np.array(_blob(c[0], c[1], rr, r, 22), np.float32))
            t = np.linspace(-0.2, 1.5, 14) + r.uniform(-0.2, 0.2)               # curl on the lower right of the billow
            curls.append((np.stack([c[0] + np.cos(t) * rr * 0.62, c[1] + np.sin(t) * rr * 0.62], 1), max(1.6, rr * 0.13)))
        m = self.mask_of(polys)
        self.outline(m, edge, cut=False)                                      # black edge where it crosses white
        self._apply_mask(m, True)
        for pts, w in curls[3::3]:
            self.gouge(pts, w, 'v', cut=False, smooth=False, region=m)

    def footprints(self, path, step=24, size=7.0, side=5.0, start=0.0, stop=1.0, paws=False):
        """boot prints (or paw prints) left standing as small dark ovals in a cleared snow field"""
        r = self.rng
        P, L = _resample(spline(path, 12), 1.0)
        tg = np.gradient(P, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        polys = []
        s = start * L; i = 0
        while s < stop * L:
            j = int(s); p, d = P[j], tg[j]; nrm = np.array([-d[1], d[0]])
            sd = side if i % 2 else -side
            c = p + nrm * sd
            sz = size * r.uniform(0.85, 1.1)
            if paws:
                for q in range(2):
                    cc = c + d * q * sz * 1.4 + nrm * (q - 0.5) * sz * 0.8
                    polys.append(np.array(_blob(cc[0], cc[1], sz * 0.5, r), np.float32))
            else:
                a = c - d * sz; b = c + d * sz
                polys.append(self.stroke([a, b], sz * 0.95, 'u', taper=(0, 0.3), jitter=0.15))
            s += step * r.uniform(0.9, 1.1); i += 1
        self._draw(polys, False)

    # ------------------------------------------------------------ printing
    def _print_fields(self, blk):
        """brayer film and baren pressure for one pull of one block (fixed per block)"""
        if hasattr(blk, 'film'): return
        H, W = self.H, self.W
        r = np.random.default_rng(blk.seed)
        film = 1 + 0.07 * (noise2d(H, W, 260, 3, int(r.integers(1 << 30))) - 0.5) * 2
        yy = np.arange(H, dtype=np.float32)[:, None]
        for _ in range(4):                                                    # brayer stop-lines across the block
            y0 = r.uniform(self.box[1], self.box[3]); wd = r.uniform(2, 6)
            band = np.exp(-((yy - y0) / wd) ** 2) * r.uniform(0.06, 0.12)
            fade = 0.5 + 0.5 * noise2d(1, W, 300, 2, int(r.integers(1 << 30)))[0][None, :]
            film = film - band * fade
        # baren: many small circular passes, summed at quarter resolution
        h4, w4 = H // 4, W // 4
        acc = np.zeros((h4, w4), np.float32)
        x0, y0, x1, y1 = [v / 4 for v in self.box]
        for _ in range(900):
            cx, cy, rad = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(5, 16)
            t = np.linspace(0, 2 * np.pi * r.uniform(0.6, 1.0), 40) + r.uniform(0, 6.3)
            xs = np.clip((cx + np.cos(t) * rad).astype(int), 0, w4 - 1); ys = np.clip((cy + np.sin(t) * rad).astype(int), 0, h4 - 1)
            np.add.at(acc, (ys, xs), 1.0)
        acc = blur(acc, 1.6); acc = acc / (acc.mean() + 1e-6)
        acc = np.asarray(Image.fromarray(acc).resize((W, H), Image.BILINEAR))
        patch = noise2d(H, W, 380, 2, int(r.integers(1 << 30)))
        press = 1 + 0.07 * np.clip(acc - 1, -1.5, 1.5) - 0.26 * smoothstep(0.55, 0.92, patch)
        blk.film, blk.press = film.astype(np.float32), press.astype(np.float32)

    def _coverage(self, blk):
        self._print_fields(blk)
        m = np.asarray(Image.fromarray(blk.a).resize((self.W, self.H), Image.BOX), np.float32) / 255
        m = smoothstep(0.22, 0.78, _soft(m) + self.crumble * 0.09)
        if blk.offset != (0, 0): m = shift(m, *blk.offset)
        contact = blk.film * blk.press
        if blk.offset != (0, 0): contact = shift(contact, *blk.offset) + (contact == 0)
        t = smoothstep(0.45, 0.72, contact * 0.70 + self.grain * 0.36)
        edge = np.clip(m - blur(m, 1.6), 0, 1)                                # ink squeezed to the edges
        cov = m * np.maximum(t, smoothstep(0.02, 0.3, edge))
        if blk is self.key:
            cov = np.maximum(cov, self.chatter * (1 - m) * t * 0.8)
        else:                                                                 # a light ink shows every unevenness
            mot = getattr(blk, 'mottle', 0.0)
            cov = cov * (1 - mot + mot * smoothstep(0.75, 1.15, contact * 0.6 + self.grain * 0.5))
        return np.clip(cov, 0, 1), m

    def pull(self, blocks=None):
        """print the blocks (default: all) onto the paper and return a PIL image"""
        img = self.paper.copy()
        blocks = self.blocks if blocks is None else blocks
        mk = None
        for blk in blocks:
            if blk is not self.key and not blk.a.any(): continue
            cov, m = self._coverage(blk)
            ink = blk.colour[None, None, :]
            img *= 1 - cov[..., None] * (1 - ink)
            if blk is self.key: mk = m
        # emboss: paper pressed onto the inked surface; carved areas and the margin stand proud
        h = (1 - (mk if mk is not None else 0)) * 1.0 + self.relief
        if mk is not None or self.relief.any():
            h = blur(np.asarray(h, np.float32) * np.ones((self.H, self.W), np.float32), 1.3)
            gy, gx = np.gradient(h)
            sh = np.clip(-(gx * -0.6 + gy * -0.7) * 0.3, -0.035, 0.035)
            img *= (1 + sh)[..., None]
        if self.pencil.any():
            a = self.pencil[..., None]
            img = img * (1 - a) + np.array([0.33, 0.32, 0.31], np.float32) * a
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def sign(self, edition='7/30', title='Untitled', name='', y=None, size=30, gap=8):
        """pencil in the margin under the print: edition left, title centred, signature right"""
        x0, _, x1, y1 = self.box
        y = y or y1 + 48
        hand = _pencil_font(size)
        script = _script_font(int(size * 1.25))
        m = text_mask(self.H, self.W, edition, hand, (x0 + gap, y), 'ls')
        m = np.maximum(m, text_mask(self.H, self.W, title, hand, ((x0 + x1) / 2, y), 'ms'))
        if name: m = np.maximum(m, text_mask(self.H, self.W, name, script, (x1 - gap, y + 2), 'rs'))
        g = 0.42 + 0.58 * self.grain
        self.pencil = np.maximum(self.pencil, m * g * 0.78)

    def chop(self, x, y, size=34, seed=None):
        """a blind chop: the printer's seal pressed into the margin without ink"""
        r = np.random.default_rng(seed if seed is not None else self._seed())
        sq = self.rect(x - size / 2, y - size / 2, x + size / 2, y + size / 2)
        inner = np.zeros_like(sq)
        for _ in range(5):                                                    # a few glyph-ish bars
            if r.random() < 0.5:
                yy = y + r.uniform(-0.3, 0.3) * size; a = r.uniform(-0.32, -0.05) * size; b = r.uniform(0.05, 0.32) * size
                inner = np.maximum(inner, self.rect(x + a, yy - 1.6, x + b, yy + 1.6))
            else:
                xx = x + r.uniform(-0.3, 0.3) * size; a = r.uniform(-0.32, -0.05) * size; b = r.uniform(0.05, 0.32) * size
                inner = np.maximum(inner, self.rect(xx - 1.6, y + a, xx + 1.6, y + b))
        border = sq - self.rect(x - size / 2 + 3, y - size / 2 + 3, x + size / 2 - 3, y + size / 2 - 3)
        self.relief = np.maximum(self.relief, np.clip(border + inner, 0, 1) * 0.9)

    # ------------------------------------------------------------ output
    def stage(self, name, blocks=None):
        """snapshot for the draw-on animation (blocks=[] -> blank paper)"""
        self.stages.append((name, self.pull(blocks)))

    def save(self, path, stages_dir=None, quality=88):
        img = self.pull()
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


def _blob(cx, cy, r, rng, n=18):
    n = int(n)
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    rr = r * (1 + 0.18 * (rng.random(n) - 0.5))
    return [(cx + np.cos(a) * q, cy + np.sin(a) * q) for a, q in zip(t, rr)]


def _pencil_font(size):
    """a light handwriting face for pencil (Noteworthy on macOS), else core's 'hand' style"""
    from PIL import ImageFont
    for p, i in (('/System/Library/Fonts/Noteworthy.ttc', 0), ('/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf', 0)):
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size, index=i)
            except OSError: pass
    return load_font('hand', size)


def _script_font(size):
    return load_font('script', size)
