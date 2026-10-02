"""rubberhose — a frame from a 1930s black-and-white "rubber hose" cartoon, printed on old film (numpy + Pillow only).

Model: one frame of an early-sound-era cartoon, made the way the studios made it, then photographed and aged.
  background  painted once by the background artist on board in grey gouache: flat tonal washes with a dry-brush
              streak, soft airbrushed pools of light and shade, contact shadows under furniture, and outlines in a
              thin dark-grey line -- thinner and greyer than the characters' ink, so the actors sit in front.
              Things the actors pass *behind* (a hill, a window bar, a blanket) are painted as overlays: they are
              stored as clip masks and cut the character cels (`clip=` on every cel method).
  pencil      the animator's rough on paper: thin grey lines drawn twice and a little off, construction circles,
              cross-hairs on the face and a line of action through the body.
  cel         traced in black ink on clear celluloid (an even, heavy line, a few per cent thicker and thinner along
              its length as the pen pressure drifts), then painted on the back in a handful of flat greys -- white,
              light, mid, dark, black. No shading on a cel. Everything is opaque and drawn back to front, so a fill
              knocks out the lines behind it.
  vocabulary  the rubber-hose look: arms and legs are bendy tubes of constant width with no elbows or knees
              (`hose`), white four-fingered gloves with three stitch lines and a flared, rolled cuff (`glove`), big
              oval shoes with a white shine (`shoe`), white eyes with black pie-cut pupils (`pie_eye`), wide open
              grins with a tongue, and props that are alive -- clocks, suns, pillows and slippers get faces, gloves
              and shoes.
  effects     vibration arcs, shake ticks, impact stars, speed lines, snore Zs and bouncing slab-serif lettering
              ("RRRING!") inked and painted like everything else.
  camera      the cel stack shot on black-and-white negative and printed: lens softness (softer in the corners),
              halation round bright paint, a print tone curve (blacks lifted, whites held, a silvery-warm tone),
              grain clumps strongest in the mid-greys, uneven density, vignette, gate weave (the frame sits a few
              pixels off and a hair rotated) and the rounded projector gate with a soft black edge.
  aging       a print after a hundred runs: vertical scratches (white through the emulsion, dark in the base) that
              come and go along their length, white specks (dirt on the negative) and black specks (dirt on the
              print), lint fibres, a hair caught in the gate, faint processing stains, and a little extra
              density at one side (flicker).

    from rubberhose import RubberHose, WHITE, BLACK
    rh = RubberHose(1920, 1080, seed=3)
    rh.wall(720); rh.floor(720)                                  # background, painted on board
    rh.stage('background')
    c = rh.alarm_clock(930, 390, 135, tilt=0.1)                  # pencil rough of a character
    rh.stage('pencil'); rh.ink(); rh.stage('ink'); rh.paint(); rh.stage('paint')
    rh.lettering('RRRING!', [(700, 130), (930, 70), (1170, 120)], 90)
    rh.film(); rh.age()
    rh.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from core import blur, fbm1d, noise2d, smoothstep, load_font

INK = 0.035
WHITE, LIGHT, PALE, MID, DARK, BLACK = 0.96, 0.84, 0.70, 0.55, 0.36, 0.07

_SLAB = [('/System/Library/Fonts/Supplemental/SuperClarendon.ttc', 7),     # Clarendon black: old title cards
         ('/System/Library/Fonts/Supplemental/Rockwell.ttc', 2),
         ('/usr/share/fonts/**/DejaVuSerif-Bold.ttf', 0), ('C:/Windows/Fonts/ROCKB.TTF', 0),
         ('C:/Windows/Fonts/georgiab.ttf', 0)]


def slab_font(size):
    """a heavy slab / Clarendon face for 1930s cartoon lettering (falls back to core.load_font('serif'))"""
    env = os.environ.get('INKPAINT_FONT_SLAB')
    cands = ([(env, 0)] if env else []) + _SLAB
    for pat, idx in cands:
        for f in glob.glob(pat, recursive=True):
            try:
                return ImageFont.truetype(f, int(size), index=idx)
            except OSError:
                pass
    return load_font('serif', size)


def ellipse_pts(cx, cy, rx, ry, rot=0.0, a0=0.0, a1=2 * np.pi, n=None):
    """points on an ellipse (closed loop if a0..a1 is the full turn, else an arc)"""
    if n is None:
        n = int(max(20, min(240, (abs(rx) + abs(ry)) * 0.9 * (a1 - a0) / (2 * np.pi))))
    full = abs(a1 - a0) >= 2 * np.pi - 1e-6
    t = np.linspace(a0, a1, n, endpoint=not full)
    x, y = np.cos(t) * rx, np.sin(t) * ry
    c, s = np.cos(rot), np.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)


def bezier(p0, p1, p2, p3, n=48):
    t = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    p0, p1, p2, p3 = [np.asarray(p, np.float32) for p in (p0, p1, p2, p3)]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3


def hose_path(p0, p1, bend=0.0, bend2=None, out0=None, n=48):
    """a rubber-hose limb from p0 to p1: one smooth C-curve (bend px to the right of travel), or an S-curve when
    bend2 has the other sign. out0 = optional unit direction the limb leaves p0 in (from the body)"""
    p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
    d = p1 - p0; L = float(np.hypot(*d)) + 1e-6
    nrm = np.array([-d[1], d[0]], np.float32) / L
    b2 = bend if bend2 is None else bend2
    c1 = p0 + d / 3 + nrm * bend * 1.33
    if out0 is not None:
        c1 = p0 + np.asarray(out0, np.float32) * L * 0.38 + nrm * bend * 0.6
    c2 = p0 + d * 2 / 3 + nrm * b2 * 1.33
    return bezier(p0, c1, c2, p1, n)


def _resample(P, step, closed=False):
    P = np.asarray(P, np.float32)
    if closed:
        P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    L = float(seg.sum())
    if L < 1e-3:
        return P[:1], np.zeros(1, np.float32), 0.0
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(2, int(np.ceil(L / step)) + 1)
    u = np.linspace(0, L, n)
    return np.stack([np.interp(u, s, P[:, 0]), np.interp(u, s, P[:, 1])], 1), (u / L).astype(np.float32), L


class Frame:
    """local drawing frame: unit `s` px, rotated by `rot` (clockwise on screen, radians), mirrored when flip=-1"""

    def __init__(self, x, y, s=1.0, rot=0.0, flip=1):
        self.o = np.array([x, y], np.float32); self.s = float(s); self.rot = rot; self.f = flip
        self.c, self.sn = np.cos(rot), np.sin(rot)

    def __call__(self, pts):
        P = np.atleast_2d(np.asarray(pts, np.float32)).copy()
        P[:, 0] *= self.f
        x = P[:, 0] * self.c - P[:, 1] * self.sn
        y = P[:, 0] * self.sn + P[:, 1] * self.c
        return np.stack([x, y], 1) * self.s + self.o

    def p(self, x, y):
        return self([(x, y)])[0]

    def ang(self, a):
        """world angle of a local direction"""
        v = self([(np.cos(a), np.sin(a))])[0] - self.o
        return float(np.arctan2(v[1], v[0]))


class RubberHose:
    def __init__(self, W=1920, H=1080, seed=0, ss=2, ink_w=5.5):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.ink_w = ink_w
        H2, W2 = H * ss, W * ss
        self.bg = np.full((H2, W2), 0.78, np.float32)
        blot = noise2d(H2 // 2, W2 // 2, 200, 4, self._seed()) - 0.5
        streak = self.rng.random((H2 // 6 + 1, W2 // 60 + 1)).astype(np.float32) - 0.5
        tex = np.array(Image.fromarray(blot * 0.8).resize((W2, H2), Image.BICUBIC), np.float32)
        tex += np.asarray(Image.fromarray(streak).resize((W2, H2), Image.BICUBIC), np.float32) * 0.9
        self.tex = tex
        self.layout = Image.new('L', (W2, H2), 0)
        self.clips = {}
        self.prims = []
        self.state = 'pencil'
        self.film_opts = None
        self.age_opts = None
        self.stages = []
        self._cache = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================ background (painted on board)
    def _bbox(self, P, pad):
        S = self.ss
        x0 = int(max(0, np.floor(P[:, 0].min() * S - pad))); y0 = int(max(0, np.floor(P[:, 1].min() * S - pad)))
        x1 = int(min(self.W * S, np.ceil(P[:, 0].max() * S + pad))); y1 = int(min(self.H * S, np.ceil(P[:, 1].max() * S + pad)))
        if x1 <= x0 or y1 <= y0:
            return None
        return x0, y0, x1, y1

    def _field(self, value, value2, axis, x0, y0, x1, y1):
        if value2 is None:
            return np.float32(value)
        S = self.ss
        (ax, ay), (bx, by) = axis
        X = (np.arange(x0, x1, dtype=np.float32) + 0.5) / S
        Y = (np.arange(y0, y1, dtype=np.float32) + 0.5) / S
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy + 1e-6
        t = np.clip(((X[None, :] - ax) * dx + (Y[:, None] - ay) * dy) / L2, 0, 1)
        return value + (value2 - value) * t

    def _apply_mask(self, m, bb, value, value2=None, axis=None, tex=1.0):
        x0, y0, x1, y1 = bb
        v = self._field(value, value2, axis, x0, y0, x1, y1) + self.tex[y0:y1, x0:x1] * 0.03 * tex
        sl = self.bg[y0:y1, x0:x1]
        sl += (v - sl) * m

    def wash(self, pts, value, value2=None, axis=None, tex=1.0, line=2.2, dark=0.7, layout=True):
        """a flat (or graded: value -> value2 along axis=((x0, y0), (x1, y1))) gouache wash inside a polygon,
        outlined in the background's thin dark-grey line"""
        P = np.asarray(pts, np.float32); S = self.ss
        bb = self._bbox(P, 4)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        im = Image.new('L', (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(im).polygon([(float(x * S - x0), float(y * S - y0)) for x, y in P], fill=255)
        self._apply_mask(np.asarray(im, np.float32) / 255, bb, value, value2, axis, tex)
        if layout:
            ImageDraw.Draw(self.layout).polygon([(float(x * S), float(y * S)) for x, y in P], fill=0)
        if line:
            self.line(P, line, dark, closed=True, layout=layout)

    def blob(self, circles, value, line=2.2, dark=0.7, tex=1.0, layout=True):
        """a union of circles (clouds, tree crowns, puffs) washed in one value; outline only round the union"""
        C = np.asarray(circles, np.float32); S = self.ss
        P = np.concatenate([C[:, :2] - C[:, 2:3], C[:, :2] + C[:, 2:3]])
        bb = self._bbox(P, 8)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        im = Image.new('L', (x1 - x0, y1 - y0), 0); d = ImageDraw.Draw(im)
        for x, y, r in C:
            d.ellipse([x * S - r * S - x0, y * S - r * S - y0, x * S + r * S - x0, y * S + r * S - y0], fill=255)
        m = np.asarray(im, np.float32) / 255
        self._apply_mask(m, bb, value, tex=tex)
        if line:
            k = int(round(line * S)) | 1
            edge = np.asarray(ImageChops.subtract(im.filter(ImageFilter.MaxFilter(k)), im.filter(ImageFilter.MinFilter(3))),
                              np.float32) / 255
            sl = self.bg[y0:y1, x0:x1]; sl *= 1 - dark * edge
        if layout:
            lay = self.layout.crop((x0, y0, x1, y1))
            lay.paste(0, mask=im)
            e2 = ImageChops.subtract(im.filter(ImageFilter.MaxFilter(3)), im)
            lay.paste(255, mask=e2)
            self.layout.paste(lay, (x0, y0))

    def line(self, pts, width=2.2, dark=0.7, closed=False, layout=True):
        """the background painter's outline: an even, thin, dark-grey line"""
        P = np.asarray(pts, np.float32); S = self.ss
        bb = self._bbox(P, width * S + 4)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        Q = [(float(x * S - x0), float(y * S - y0)) for x, y in P]
        if closed:
            Q = Q + Q[:1]
        im = Image.new('L', (x1 - x0, y1 - y0), 0); d = ImageDraw.Draw(im)
        w = max(1, int(round(width * S)))
        d.line(Q, fill=255, width=w, joint='curve')
        r = w / 2
        for q in (Q[0], Q[-1]):
            d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)
        m = np.asarray(im, np.float32) / 255
        sl = self.bg[y0:y1, x0:x1]; sl *= 1 - dark * m
        if layout:
            ImageDraw.Draw(self.layout).line([(q[0] + x0, q[1] + y0) for q in Q], fill=255, width=max(2, S + 1))

    def airbrush(self, cx, cy, rx, ry, amount, rot=0.0):
        """a soft airbrushed pool: amount > 0 lightens (light from a window), < 0 darkens (contact shadow)"""
        S = self.ss
        P = ellipse_pts(cx, cy, rx * 2.2, ry * 2.2, rot, n=16)
        bb = self._bbox(P, 2)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        X = (np.arange(x0, x1, dtype=np.float32) + 0.5) / S - cx
        Y = (np.arange(y0, y1, dtype=np.float32) + 0.5) / S - cy
        c, s = np.cos(rot), np.sin(rot)
        u = (X[None, :] * c + Y[:, None] * s) / rx; v = (-X[None, :] * s + Y[:, None] * c) / ry
        g = np.exp(-(u * u + v * v) * 1.4)
        sl = self.bg[y0:y1, x0:x1]
        if amount >= 0:
            sl += (1 - sl) * g * amount
        else:
            sl *= 1 + g * amount

    def light(self, pts, amount=0.2, soft=14.0):
        """a soft-edged patch of light (sunbeam on the floor) airbrushed over the background; amount < 0 for a
        soft shade"""
        S = self.ss; P = np.asarray(pts, np.float32)
        bb = self._bbox(P, soft * S * 3)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        im = Image.new('L', (x1 - x0, y1 - y0), 0)
        ImageDraw.Draw(im).polygon([(float(x * S - x0), float(y * S - y0)) for x, y in P], fill=255)
        m = np.asarray(im.filter(ImageFilter.GaussianBlur(soft * S)), np.float32) / 255
        sl = self.bg[y0:y1, x0:x1]
        if amount >= 0:
            sl += (1 - sl) * m * amount
        else:
            sl *= 1 + m * amount

    def pattern(self, pts, draw_fn, dark=0.15):
        """paint a small repeat pattern (wallpaper sprigs, polka dots) inside a polygon: draw_fn(ImageDraw, S)
        draws motifs in canvas px * S on a full-size sheet"""
        S = self.ss; P = np.asarray(pts, np.float32)
        bb = self._bbox(P, 2)
        if bb is None:
            return
        x0, y0, x1, y1 = bb
        im = Image.new('L', (self.W * S, self.H * S), 0)
        draw_fn(ImageDraw.Draw(im), S)
        im = im.crop(bb)
        mk = Image.new('L', im.size, 0)
        ImageDraw.Draw(mk).polygon([(float(x * S - x0), float(y * S - y0)) for x, y in P], fill=255)
        m = np.asarray(im, np.float32) / 255 * np.asarray(mk, np.float32) / 255
        sl = self.bg[y0:y1, x0:x1]; sl *= 1 - dark * m

    # ---------------------------------------------------------------- clip masks (overlays the actors pass behind)
    def clip(self, name, add=None, sub=None, full=False):
        """build a named clip mask for cels: add / sub are lists of polygons; full=True starts from everything"""
        S = self.ss
        if name not in self.clips:
            self.clips[name] = Image.new('L', (self.W * S, self.H * S), 255 if full else 0)
        d = ImageDraw.Draw(self.clips[name])
        for pts in (add or []):
            d.polygon([(float(x * S), float(y * S)) for x, y in pts], fill=255)
        for pts in (sub or []):
            d.polygon([(float(x * S), float(y * S)) for x, y in pts], fill=0)
        return name

    # ---------------------------------------------------------------- the room
    def wall(self, y1, value=0.8, value_top=0.62, stripes=0.022, sprigs=True, base=40):
        """papered wall down to y1: a graded wash (dark at the ceiling), soft vertical stripes, rows of little
        sprigs, and a skirting board"""
        W, S = self.W, self.ss
        self.wash([(0, 0), (W, 0), (W, y1), (0, y1)], value_top, value, ((0, 0), (0, y1 * 0.85)), line=0)
        if stripes:
            X = np.arange(W * S, dtype=np.float32) / S
            band = smoothstep(-0.25, 0.25, np.sin(2 * np.pi * X / 76.0)).astype(np.float32) - 0.5
            self.bg[:int(y1 * S)] += band[None, :] * stripes
        if sprigs:
            rng = np.random.default_rng(self._seed())

            def motif(d, S):
                for j, y in enumerate(np.arange(46, y1 - base, 76)):
                    for x in np.arange(38 * (j % 2), W + 40, 76):
                        x2, y2 = x + rng.normal(0, 1.2), y + rng.normal(0, 1.2)
                        for a in (0, 2.1, 4.2):
                            px, py = x2 + 5 * np.cos(a - 1.57), y2 + 5 * np.sin(a - 1.57)
                            d.ellipse([(px - 3.6) * S, (py - 3.6) * S, (px + 3.6) * S, (py + 3.6) * S], fill=255)
                        d.line([(x2 * S, (y2 + 4) * S), ((x2 - 3) * S, (y2 + 15) * S)], fill=255, width=int(2 * S))
                        d.ellipse([(x2 + 2) * S, (y2 + 9) * S, (x2 + 9) * S, (y2 + 13) * S], fill=255)
            self.pattern([(0, 0), (W, 0), (W, y1 - base), (0, y1 - base)], motif, dark=0.14)
        self.wash([(0, y1 - base), (W, y1 - base), (W, y1), (0, y1)], 0.56, 0.5, ((0, y1 - base), (0, y1)))
        self.line([(0, y1 - base + 8), (W, y1 - base + 8)], 1.6, 0.45)

    def floor(self, y0, value_back=0.44, value_front=0.62, board=104, vp=(960, -1500)):
        """wooden floor from y0 down: planks converging on a far vanishing point, butt joints, faint grain"""
        W, H = self.W, self.H
        rng = np.random.default_rng(self._seed())
        self.wash([(0, y0), (W, y0), (W, H), (0, H)], value_back, value_front, ((0, y0), (0, H)), line=0)
        vx, vy = vp
        seams = []
        for k in range(-30, 60):
            xs = -1500 + k * board
            xb = vx + (xs - vx) * (H + 20 - vy) / (y0 - vy)
            if max(xs, xb) < -50 or min(xs, xb) > W + 50:
                continue
            seams.append(((xs, y0), (xb, H + 20)))
        for a, b in seams:
            self.line([a, b], 1.7, 0.42)
        for (a, b), (c, d) in zip(seams[:-1], seams[1:]):
            for _ in range(rng.integers(1, 3)):
                t = rng.uniform(0.08, 0.95)
                ya = y0 + (H - y0) * t
                xa = a[0] + (b[0] - a[0]) * (ya - y0) / (H + 20 - y0); xc = c[0] + (d[0] - c[0]) * (ya - y0) / (H + 20 - y0)
                self.line([(xa, ya), (xc, ya)], 1.5, 0.35, layout=False)
            for _ in range(2):
                t0 = rng.uniform(0, 0.6); n = 12
                ys = y0 + (H - y0) * np.linspace(t0, min(1, t0 + rng.uniform(0.2, 0.5)), n)
                f = rng.uniform(0.25, 0.75)
                xa = a[0] + (b[0] - a[0]) * (ys - y0) / (H + 20 - y0); xc = c[0] + (d[0] - c[0]) * (ys - y0) / (H + 20 - y0)
                xg = xa + (xc - xa) * f + fbm1d(n, 6, 2, self._seed()) * 4
                self.line(np.stack([xg, ys], 1), 1.0, 0.12, layout=False)
        self.airbrush(W / 2, y0 + 6, W * 0.8, 26, -0.28)

    def window(self, x0, y0, x1, y1, frame=24, bar=14, horizon=None, bars='sash', valley=None, clip='window'):
        """a sash window with a morning landscape outside: graded sky, two clouds, far hill with a tree and grass
        ticks, a near hill (an overlay: anything clipped to `clip` -- the sun -- rises behind it), white painted
        frame, glazing bars and a sill. Returns geometry (glass, panes, hill polygon)"""
        rng = np.random.default_rng(self._seed())
        gx0, gy0, gx1, gy1 = x0 + frame, y0 + frame, x1 - frame, y1 - frame
        hz = horizon if horizon is not None else gy1 - (gy1 - gy0) * 0.16
        self.wash([(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)], 0.66, 0.88, ((0, gy0), (0, hz)), line=0, tex=0.6)
        for cx, cy, s in ((gx0 + (gx1 - gx0) * 0.24, gy0 + 62, 1.0), (gx0 + (gx1 - gx0) * 0.8, gy0 + 120, 0.75)):
            self.blob([(cx - 34 * s, cy + 6 * s, 24 * s), (cx - 6 * s, cy - 12 * s, 32 * s), (cx + 28 * s, cy, 26 * s),
                       (cx + 2 * s, cy + 14 * s, 24 * s)], 0.93, line=2.0, dark=0.55)
        xs = np.linspace(gx0 - 10, gx1 + 10, 60)
        far = hz - 40 + 22 * np.sin((xs - gx0) / (gx1 - gx0) * 3.4 + 0.6) + fbm1d(60, 20, 2, self._seed()) * 4
        far_poly = np.vstack([np.stack([xs, far], 1), [(gx1 + 10, gy1 + 5), (gx0 - 10, gy1 + 5)]])
        self.wash(far_poly, 0.72, 0.66, ((0, hz - 60), (0, gy1)), line=2.0, dark=0.6)
        tx = gx0 + (gx1 - gx0) * 0.2; ty = float(np.interp(tx, xs, far))
        self.wash([(tx - 6, ty + 6), (tx + 6, ty + 6), (tx + 4, ty - 46), (tx - 4, ty - 46)], 0.4, line=1.8, dark=0.6)
        self.blob([(tx - 18, ty - 58, 20), (tx + 2, ty - 74, 24), (tx + 20, ty - 56, 19), (tx, ty - 50, 18)], 0.46,
                  line=2.0, dark=0.6)
        for gx in rng.uniform(gx0 + 20, gx1 - 20, 9):
            gy = float(np.interp(gx, xs, far)) + rng.uniform(14, 40)
            self.line([(gx - 5, gy + 3), (gx, gy - 5), (gx + 5, gy + 3)], 1.4, 0.45, layout=False)
        vx = valley if valley is not None else (gx0 + gx1) / 2
        near = hz + 24 * np.cos((xs - vx) / (gx1 - gx0) * 2 * np.pi * 0.85) + fbm1d(60, 20, 2, self._seed()) * 3
        near_poly = np.vstack([np.stack([xs, near], 1), [(gx1 + 10, gy1 + 5), (gx0 - 10, gy1 + 5)]])
        self.wash(near_poly, 0.6, 0.54, ((0, hz), (0, gy1)), line=2.0, dark=0.6)
        for gx in rng.uniform(gx0 + 20, gx1 - 20, 7):
            gy = float(np.interp(gx, xs, near)) + rng.uniform(12, 30)
            if gy < gy1 - 6:
                self.line([(gx - 5, gy + 3), (gx, gy - 5), (gx + 5, gy + 3)], 1.4, 0.45, layout=False)
        # painted frame and glazing bars
        mx, my = (gx0 + gx1) / 2, (gy0 + (gy1 - gy0) * 0.42 if bars == 'sash' else (gy0 + gy1) / 2)
        fr = [[(x0, y0), (x1, y0), (x1, gy0), (x0, gy0)], [(x0, gy1), (x1, gy1), (x1, y1), (x0, y1)],
              [(x0, gy0), (gx0, gy0), (gx0, gy1), (x0, gy1)], [(gx1, gy0), (x1, gy0), (x1, gy1), (gx1, gy1)]]
        for p in fr:
            self.wash(p, 0.9, line=0)
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 2.2, 0.7, closed=True)
        self.line([(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)], 2.0, 0.7, closed=True)
        rails = [[(gx0, my - bar / 2), (gx1, my - bar / 2), (gx1, my + bar / 2), (gx0, my + bar / 2)]]
        if bars == 'cross':
            rails.append([(mx - bar / 2, gy0), (mx + bar / 2, gy0), (mx + bar / 2, gy1), (mx - bar / 2, gy1)])
        for p in rails:
            self.wash(p, 0.88, line=0)
        for p in rails:
            self.line(p, 1.8, 0.62, closed=True)
        self.wash([(x0 - 26, y1 - 2), (x1 + 26, y1 - 2), (x1 + 26, y1 + 20), (x0 - 26, y1 + 20)], 0.88, 0.8,
                  ((0, y1), (0, y1 + 20)))
        self.airbrush((x0 + x1) / 2, y1 + 30, (x1 - x0) * 0.55, 14, -0.25)
        self.clip(clip, add=[[(gx0, gy0), (gx1, gy0), (gx1, gy1), (gx0, gy1)]], sub=[near_poly] + rails)
        return dict(glass=(gx0, gy0, gx1, gy1), mid=(mx, my), hill=near_poly, horizon=hz)

    def curtain(self, x_rod0, x_rod1, top, bottom, tie_y, side='left', value=0.6, clip='window'):
        """a gathered curtain hanging from a rod, tied back at tie_y, with polka dots and fold lines; it also cuts
        the window clip (the sun goes behind it)"""
        a, b = x_rod0, x_rod1; w = b - a
        if side == 'left':
            tie = (a + w * 0.12, a + w * 0.52); foot = (a - w * 0.06, a + w * 0.95)
        else:
            tie = (a + w * 0.48, a + w * 0.88); foot = (a + w * 0.05, b + w * 0.06)
        n = 24
        t = np.linspace(0, 1, n)
        def side_x(top_x, tie_x, foot_x):
            up = top_x + (tie_x - top_x) * np.sin(t * np.pi / 2)
            dn = tie_x + (foot_x - tie_x) * (1 - np.cos(t * np.pi / 2))
            return up, dn
        lu, ld = side_x(a, tie[0], foot[0]); ru, rd = side_x(b, tie[1], foot[1])
        yu = top + (tie_y - top) * t; yd = tie_y + (bottom - tie_y) * t
        left = np.vstack([np.stack([lu, yu], 1), np.stack([ld, yd], 1)])
        right = np.vstack([np.stack([ru, yu], 1), np.stack([rd, yd], 1)])
        hem = np.stack([np.linspace(left[-1, 0], right[-1, 0], 20),
                        bottom + 6 * np.abs(np.sin(np.linspace(0, 4 * np.pi, 20)))], 1)
        poly = np.vstack([left, hem, right[::-1]])
        self.wash(poly, value + 0.06, value - 0.04, ((0, top), (0, bottom)))
        rng = np.random.default_rng(self._seed())

        def dots(d, S):
            for j, y in enumerate(np.arange(top + 18, bottom, 34)):
                for x in np.arange(a - 40 + 17 * (j % 2), b + 40, 34):
                    r = 5.0
                    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=255)
        self.pattern(poly, dots, dark=-0.35)
        for f in (0.3, 0.55, 0.78):
            fx_u = lu + (ru - lu) * f; fx_d = ld + (rd - ld) * f
            P = np.vstack([np.stack([fx_u, yu], 1)[2:], np.stack([fx_d, yd], 1)[:-3]])
            self.line(P, 1.5, 0.45)
        tx0, tx1 = tie[0] - 6, tie[1] + 6
        self.wash([(tx0, tie_y - 9), (tx1, tie_y - 9), (tx1, tie_y + 9), (tx0, tie_y + 9)], 0.4)
        self.clip(clip, sub=[poly])
        return poly

    def valance(self, x0, x1, y0, y1, scallops=7, value=0.5, clip='window'):
        """a rod and a scalloped pelmet across the top of the window"""
        self.wash([(x0 - 30, y0 - 12), (x1 + 30, y0 - 12), (x1 + 30, y0 - 4), (x0 - 30, y0 - 4)], 0.3)
        for x in (x0 - 34, x1 + 34):
            self.wash(ellipse_pts(x, y0 - 8, 11, 11), 0.34)
        xs = np.linspace(x0, x1, scallops * 12 + 1)
        ys = y1 - 4 + 20 * np.abs(np.sin(np.linspace(0, scallops * np.pi, xs.size)))
        poly = np.vstack([[(x0, y0)], [(x1, y0)], np.stack([xs, ys], 1)[::-1]])
        self.wash(poly, value + 0.04, value - 0.06, ((0, y0), (0, y1 + 16)))
        self.line([(x0 + 4, y0 + 14), (x1 - 4, y0 + 14)], 1.4, 0.4)
        self.line([(x0 + 4, y0 + 22), (x1 - 4, y0 + 22)], 1.4, 0.4)
        self.clip(clip, sub=[poly])

    def nightstand(self, x0, x1, top, bottom, floor_y, value=0.42):
        """a bedside table: lit top, front with a drawer and knob, tapered legs, a contact shadow"""
        self.airbrush((x0 + x1) / 2, floor_y + 2, (x1 - x0) * 0.62, 18, -0.42)
        for lx in (x0 + 16, x1 - 16):
            self.wash([(lx - 12, bottom - 2), (lx + 12, bottom - 2), (lx + 6, floor_y), (lx - 6, floor_y)], value - 0.06)
        self.wash([(x0, top + 20), (x1, top + 20), (x1, bottom), (x0, bottom)], value, value - 0.06,
                  ((0, top), (0, bottom)))
        self.wash([(x0 + 18, top + 40), (x1 - 18, top + 40), (x1 - 18, top + 108), (x0 + 18, top + 108)],
                  value + 0.05)
        self.line([(x0 + 26, top + 48), (x1 - 26, top + 48), (x1 - 26, top + 100), (x0 + 26, top + 100)], 1.2, 0.3,
                  closed=True)
        kx = (x0 + x1) / 2
        self.wash(ellipse_pts(kx, top + 74, 10, 10), 0.82)
        self.wash([(x0 + 12, top - 16), (x1 - 12, top - 16), (x1 + 10, top), (x0 - 10, top)], 0.6, 0.66,
                  ((0, top - 16), (0, top)))
        self.wash([(x0 - 10, top), (x1 + 10, top), (x1 + 10, top + 20), (x0 - 10, top + 20)], value + 0.08)
        self.line([(x0 + 4, top + 128), (x1 - 4, top + 128)], 1.2, 0.25, layout=False)
        return top - 8

    def bed(self, x0, x1, head_top, sheet_y, front_y, floor_y, wood=0.38, clip='bed'):
        """a bed seen from the foot: arched headboard with ball finials, a sheet, a quilted blanket folded back at
        the top and draped over the front, short front posts. The blanket is an overlay: cels clipped to `clip`
        (the pillow) sit behind it"""
        rng = np.random.default_rng(self._seed())
        pw = 44
        self.airbrush((x0 + x1) / 2, floor_y + 4, (x1 - x0) * 0.6, 20, -0.4)
        # headboard
        arch = ellipse_pts((x0 + x1) / 2, head_top + 60, (x1 - x0) / 2 - pw, 60, a0=np.pi, a1=2 * np.pi, n=60)
        hb = np.vstack([[(x0 + pw, sheet_y + 60)], arch, [(x1 - pw, sheet_y + 60)]])
        self.wash(hb, wood + 0.04, wood - 0.04, ((0, head_top), (0, sheet_y)))
        inset = ellipse_pts((x0 + x1) / 2, head_top + 86, (x1 - x0) / 2 - pw - 34, 46, a0=np.pi, a1=2 * np.pi, n=50)
        self.line(np.vstack([[(x0 + pw + 34, sheet_y - 6)], inset, [(x1 - pw - 34, sheet_y - 6)]]), 1.4, 0.35)
        for k in range(1, 6):
            sx = x0 + pw + 34 + (x1 - x0 - 2 * pw - 68) * k / 6
            self.line([(sx, head_top + 60 + 12 * abs(k - 3)), (sx, sheet_y - 8)], 1.2, 0.25, layout=False)
        for px in (x0, x1 - pw):
            self.wash([(px, head_top + 30), (px + pw, head_top + 30), (px + pw, sheet_y + 120), (px, sheet_y + 120)],
                      wood + 0.02, wood - 0.06, ((px, 0), (px + pw, 0)))
            self.wash(ellipse_pts(px + pw / 2, head_top + 18, 22, 22), wood + 0.1)
            self.airbrush(px + pw / 2 - 7, head_top + 11, 7, 6, 0.35)
        # sheet band
        self.wash([(x0 + pw, sheet_y), (x1 - pw, sheet_y), (x1 - pw + 6, sheet_y + 60), (x0 + pw - 6, sheet_y + 60)],
                  0.9, 0.84, ((0, sheet_y), (0, sheet_y + 60)))
        # blanket: folded-back sheet hem, quilt squares, front drape
        top_y = sheet_y + 44
        fold = [(x0 + 4, top_y), (x1 - 4, top_y), (x1, top_y + 30), (x0, top_y + 30)]
        body = [(x0, top_y + 28), (x1, top_y + 28), (x1 + 22, front_y), (x0 - 22, front_y)]
        hem_x = np.linspace(x0 - 22, x1 + 22, 61)
        hem_y = front_y + 52 + 10 * np.abs(np.sin(np.linspace(0, 10 * np.pi, 61)))
        drape = np.vstack([[(x0 - 22, front_y)], [(x1 + 22, front_y)], np.stack([hem_x, hem_y], 1)[::-1]])
        self.wash(body, 0.7, 0.76, ((0, top_y), (0, front_y)))

        def quilt(d, S):
            nx, ny = 6, 4
            for i in range(nx):
                for j in range(ny):
                    if (i + j) % 2:
                        continue
                    t0, t1 = j / ny, (j + 1) / ny
                    y_a, y_b = top_y + 28 + (front_y - top_y - 28) * t0, top_y + 28 + (front_y - top_y - 28) * t1
                    wa = (x1 - x0) + 44 * t0; wb = (x1 - x0) + 44 * t1
                    xa0, xb0 = x0 - 22 * t0, x0 - 22 * t1
                    q = [(xa0 + wa * i / nx, y_a), (xa0 + wa * (i + 1) / nx, y_a),
                         (xb0 + wb * (i + 1) / nx, y_b), (xb0 + wb * i / nx, y_b)]
                    d.polygon([(x * S, y * S) for x, y in q], fill=255)
        self.pattern(body, quilt, dark=0.17)
        for k in range(1, 6):
            self.line([(x0 + (x1 - x0) * k / 6, top_y + 28), (x0 - 22 + (x1 - x0 + 44) * k / 6, front_y)], 1.2, 0.3,
                      layout=False)
        for k in range(1, 4):
            t = k / 4
            self.line([(x0 - 22 * t, top_y + 28 + (front_y - top_y - 28) * t), (x1 + 22 * t, top_y + 28 + (front_y - top_y - 28) * t)],
                      1.2, 0.3, layout=False)
        self.line(body, 2.0, 0.7, closed=True)
        self.wash(drape, 0.6, 0.5, ((0, front_y), (0, front_y + 60)))
        for k in range(1, 10):
            self.line([(x0 - 22 + (x1 - x0 + 44) * k / 10, front_y + 4), (x0 - 22 + (x1 - x0 + 44) * k / 10, front_y + 48)],
                      1.2, 0.25, layout=False)
        self.wash(fold, 0.92, 0.86, ((0, top_y), (0, top_y + 30)))
        # front posts
        for px in (x0 - 40, x1 + 4):
            self.wash([(px, front_y - 30), (px + 36, front_y - 30), (px + 32, floor_y), (px + 4, floor_y)],
                      wood + 0.02, wood - 0.08, ((px, 0), (px + 36, 0)))
            self.wash(ellipse_pts(px + 18, front_y - 42, 19, 19), wood + 0.1)
            self.airbrush(px + 12, front_y - 48, 6, 5, 0.35)
        self.clip(clip, full=True, sub=[body, fold, drape])
        return dict(top=top_y, front=front_y)

    def rug(self, cx, cy, rx, ry, rings=5):
        """an oval braided rug: concentric bands of alternating grey with braid ticks along each band"""
        self.airbrush(cx, cy + ry * 0.2, rx * 1.02, ry * 1.1, -0.22)
        vals = [0.5, 0.7, 0.42, 0.66, 0.78]
        for k in range(rings):
            f = 1 - k / rings
            self.wash(ellipse_pts(cx, cy, rx * f, ry * f), vals[k % len(vals)], line=1.6, dark=0.5)
            n = int(60 * f) + 12
            for a in np.linspace(0, 2 * np.pi, n, endpoint=False):
                fm = f - 0.5 / rings
                px, py = cx + np.cos(a) * rx * fm, cy + np.sin(a) * ry * fm
                tx, ty = -np.sin(a) * rx, np.cos(a) * ry
                tl = np.hypot(tx, ty)
                self.line([(px - tx / tl * 5 - 2, py - ty / tl * 2 - 3), (px + tx / tl * 5 + 2, py + ty / tl * 2 + 3)],
                          1.1, 0.22, layout=False)

    def sampler(self, x0, y0, x1, y1, lines, value=0.9):
        """a framed embroidered motto hung on a nail: dark moulding, light cloth, lettering, a stitched border"""
        cx = (x0 + x1) / 2
        self.line([(x0 + 40, y0 + 4), (cx, y0 - 50), (x1 - 40, y0 + 4)], 1.4, 0.55)
        self.wash(ellipse_pts(cx, y0 - 50, 5, 5), 0.3)
        self.airbrush(cx + 10, y1 + 8, (x1 - x0) * 0.5, 10, -0.25)
        self.wash([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], 0.34, 0.28, ((x0, y0), (x1, y1)))
        b = 18
        self.wash([(x0 + b, y0 + b), (x1 - b, y0 + b), (x1 - b, y1 - b), (x0 + b, y1 - b)], value)
        self.line([(x0 + b + 9, y0 + b + 9), (x1 - b - 9, y0 + b + 9), (x1 - b - 9, y1 - b - 9), (x0 + b + 9, y1 - b - 9)],
                  1.0, 0.35, closed=True, layout=False)
        S = self.ss; n = len(lines)
        x0i, y0i, x1i, y1i = x0 + b + 18, y0 + b + 14, x1 - b - 18, y1 - b - 14
        size = min((y1i - y0i) / n * 0.86, 999)
        im = Image.new('L', (self.W * S, self.H * S), 0); d = ImageDraw.Draw(im)
        for i, s in enumerate(lines):
            f = slab_font(size * S)
            while f.getlength(s) > (x1i - x0i) * S and size > 8:
                size *= 0.94; f = slab_font(size * S)
            d.text((cx * S, (y0i + (y1i - y0i) * (i + 0.5) / n) * S), s, font=f, fill=255, anchor='mm')
        m = np.asarray(im, np.float32) / 255
        self.bg *= 1 - 0.62 * m
        ImageDraw.Draw(self.layout).bitmap((0, 0), ImageChops.subtract(im.filter(ImageFilter.MaxFilter(3)), im), fill=255)

    # ================================================================ cels: primitives
    def _add(self, **p):
        p.setdefault('clip', self._clip)
        p.setdefault('seed', self._seed())
        self.prims.append(p)
        self._cache = None
        return p

    _clip = None

    def using(self, clip):
        """send the following cels to a clip mask (None = no clip). Use as: rh.using('window'); ...; rh.using(None)"""
        self._clip = clip

    def shape(self, pts, fill=WHITE, ow=None, closed=True):
        """a closed inked-and-painted shape. ow = ink width (outside the fill); fill None = line only"""
        return self._add(k='shape', pts=np.asarray(pts, np.float32), fill=fill,
                         ow=self.ink_w if ow is None else ow, closed=closed)

    def union(self, subs, fill=WHITE, ow=None):
        """several pieces painted as one (no ink between them): subs = [('poly', pts) | ('cap', pts, radius)]"""
        return self._add(k='union', subs=subs, fill=fill, ow=self.ink_w if ow is None else ow)

    def stroke(self, pts, width=4.0, taper=(0.0, 0.0), value=INK, effect=False):
        """an inked line: width px, tapering over the first / last fraction of its length"""
        return self._add(k='stroke', pts=np.asarray(pts, np.float32), w=width, taper=taper, value=value, fx=effect)

    def hose(self, pts, width, fill=BLACK, ow=None):
        """a rubber-hose limb along pts: a tube of constant width, no elbow, no knee"""
        return self._add(k='hose', pts=np.asarray(pts, np.float32), w=width, fill=fill,
                         ow=self.ink_w * 0.8 if ow is None else ow)

    def guide(self, pts, closed=False):
        """a construction line that only shows in the pencil rough"""
        return self._add(k='guide', pts=np.asarray(pts, np.float32), closed=closed)

    def shadow(self, cx, cy, rx, ry, amount=0.35):
        """a painted cast shadow (grey, soft-edged) under a character"""
        return self._add(k='shadow', pts=ellipse_pts(cx, cy, rx, ry), a=amount, clip=None)

    def text(self, s, x, y, size, fill=WHITE, ow=None, rot=0.0, font=None, effect=True):
        """one run of inked lettering centred at (x, y), rotated rot degrees (counter-clockwise)"""
        return self._add(k='text', s=s, x=x, y=y, size=size, fill=fill, ow=self.ink_w if ow is None else ow,
                         rot=rot, font=font, fx=effect)

    # ================================================================ cels: the rubber-hose vocabulary
    def glove(self, x, y, angle, size, pose='open', flip=1, ow=None):
        """a white four-fingered cartoon glove. (x, y) = wrist (where the hose goes in), angle = direction the
        fingers point (radians, screen), size ~ palm-to-tip length / 1.6. pose: open | point | fist | palm (stop).
        flip=-1 mirrors it (left / right hand: which side the thumb is on)."""
        ow = self.ink_w * 0.9 if ow is None else ow
        F = Frame(x, y, size, angle + np.pi / 2, flip)          # local: -y = toward the fingertips
        palm_c = (0.0, -0.78)
        subs = [('poly', F(ellipse_pts(*palm_c, 0.5, 0.44)))]
        seps = []
        if pose in ('open', 'palm'):
            spread = [-0.62, -0.2, 0.2, 0.58] if pose == 'open' else [-0.3, -0.1, 0.1, 0.3]
            lens = [0.78, 0.98, 0.94, 0.74]
            prev = None
            for a, L in zip(spread, lens):
                d = np.array([np.sin(a), -np.cos(a)])
                b = np.array(palm_c) + d * 0.2; t = np.array(palm_c) + d * (0.38 + L * 0.62)
                subs.append(('cap', F([b, t]), 0.155 * size))
                if prev is not None and pose == 'palm':
                    m = (prev + t) / 2
                    seps.append(F([m, m + (np.array(palm_c) - m) * 0.35]))
                prev = t
            subs.append(('cap', F([(-0.3, -0.62), (-0.78, -0.98)]), 0.16 * size))
        elif pose == 'point':
            subs.append(('cap', F([(0.04, -0.9), (0.06, -1.82)]), 0.155 * size))
            for k, (bx, by) in enumerate([(0.2, -1.04), (0.32, -0.86), (0.36, -0.66)]):
                subs.append(('cap', F([(bx - 0.08, by), (bx + 0.08, by + 0.04)]), 0.15 * size))
            subs.append(('cap', F([(-0.34, -0.66), (-0.08, -1.02)]), 0.15 * size))
        elif pose == 'fist':
            subs = [('poly', F(ellipse_pts(0.0, -0.78, 0.5, 0.42)))]
            for bx in (-0.3, -0.1, 0.1, 0.3):                   # four curled fingers: a scalloped knuckle edge
                subs.append(('cap', F([(bx, -1.0), (bx, -1.1)]), 0.135 * size))
        self.union(subs, WHITE, ow)
        if pose == 'open':
            for sx in (-0.16, 0.0, 0.16):
                self.stroke(F([(sx, -0.62), (sx * 1.15, -0.92)]), ow * 0.55, (0.3, 0.3))
        elif pose == 'point':
            for k in range(1, 3):
                self.stroke(F([(-0.32 + 0.22 * k, -1.02), (-0.3 + 0.22 * k, -0.9)]), ow * 0.5, (0.3, 0.3))
        elif pose == 'fist':
            for sx in (-0.2, 0.0, 0.2):
                self.stroke(F([(sx, -1.08), (sx, -0.94)]), ow * 0.5, (0.1, 0.5))
            self.union([('cap', F([(-0.46, -0.76), (-0.16, -0.88)]), 0.13 * size)], WHITE, ow * 0.9)
        for s in seps:
            self.stroke(s, ow * 0.5, (0.2, 0.4))
        cuff = np.vstack([[(0.32, -0.36), (-0.32, -0.36)], ellipse_pts(0, 0.06, 0.5, 0.12, a0=np.pi, a1=0, n=20)])
        self.shape(F(cuff), WHITE, ow)
        self.stroke(F(ellipse_pts(0, 0.06, 0.5, 0.12, a0=np.pi, a1=2 * np.pi, n=20)), ow * 0.6)
        for sx in (-0.18, 0.16):
            self.stroke(F([(sx * 1.3, 0.0), (sx, -0.24)]), ow * 0.45, (0.2, 0.5))
        return F

    def shoe(self, x, y, size, facing=1, tilt=0.0, ow=None):
        """a big oval cartoon shoe; (x, y) = the ankle, facing +-1, tilt rotates it (toe up < 0 < toe down)"""
        ow = self.ink_w if ow is None else ow
        F = Frame(x, y, size, tilt * facing, facing)
        toe = ellipse_pts(0.55, 0.3, 0.66, 0.42); heel = ellipse_pts(-0.22, 0.38, 0.4, 0.34)
        sole = np.vstack([ellipse_pts(0.5, 0.62, 0.78, 0.16, a0=0, a1=np.pi, n=30), [(-0.6, 0.68), (-0.6, 0.5)]])
        self.shape(F(sole), DARK, ow)
        self.union([('poly', F(toe)), ('poly', F(heel))], BLACK, ow)
        self.shape(F(ellipse_pts(0.72, 0.12, 0.26, 0.09, rot=-0.25)), WHITE, 0)
        self.shape(F(ellipse_pts(0.36, 0.06, 0.07, 0.05)), WHITE, 0)
        return F

    def pie_eye(self, cx, cy, rx, ry, look=(0.0, 0.0), wedge=-0.9, lid=0.0, face=WHITE, rot=0.0, ow=None):
        """a white oval eye with a black pie-cut pupil (a wedge cut out toward `wedge`, radians). look = (x, y) in
        -1..1 moves the pupil; lid 0..1 closes a top lid painted in the face colour"""
        ow = self.ink_w * 0.75 if ow is None else ow
        self.shape(ellipse_pts(cx, cy, rx, ry, rot), WHITE, ow)
        px = cx + look[0] * rx * 0.36; py = cy + look[1] * ry * 0.3 + ry * 0.1
        prx, pry = rx * 0.6, ry * 0.66
        half = 0.42
        t = np.linspace(wedge + half, wedge + 2 * np.pi - half, 60)
        tip = (px + np.cos(wedge) * prx * 0.12, py + np.sin(wedge) * pry * 0.12)
        arc = np.stack([px + np.cos(t) * prx, py + np.sin(t) * pry], 1)
        # keep the pupil inside the eye white
        ex, ey = (arc[:, 0] - cx) / (rx * 0.94), (arc[:, 1] - cy) / (ry * 0.94)
        r = np.maximum(1.0, np.hypot(ex, ey))
        arc = np.stack([cx + ex / r * rx * 0.94, cy + ey / r * ry * 0.94], 1)
        self.shape(np.vstack([[tip], arc]), BLACK, 0)
        if lid > 0:
            yl = cy - ry + 2 * ry * lid
            a = np.arcsin(np.clip((yl - cy) / ry, -1, 1))
            arc2 = ellipse_pts(cx, cy, rx * 1.02, ry * 1.02, a0=np.pi - a, a1=2 * np.pi + a, n=40)
            self.shape(arc2, face, 0)
            self.stroke(np.stack([np.linspace(arc2[0, 0], arc2[-1, 0], 12), np.full(12, yl)], 1), ow * 1.1)
            self.shape(ellipse_pts(cx, cy, rx, ry, rot), None, ow)

    def grin(self, F, x0, x1, y_top, y_bot, curve=0.06, tongue=MID, ow=None):
        """a wide open laughing mouth in frame F (local coords): smiling upper lip, deep lower jaw, a tongue"""
        ow = self.ink_w * 0.8 if ow is None else ow
        xs = np.linspace(x0, x1, 30)
        u = (xs - x0) / (x1 - x0)
        top = y_top + curve * (1 - (2 * u - 1) ** 2)
        bot = y_top + (y_bot - y_top) * np.sqrt(np.clip(1 - (2 * u - 1) ** 2, 0, 1)) ** 0.9 + curve * 0.3
        mouth = np.vstack([np.stack([xs, top], 1), np.stack([xs, bot], 1)[::-1]])
        self.shape(F(mouth), BLACK, ow)
        if tongue is not None:
            k = (u > 0.22) & (u < 0.82)
            bl = np.stack([xs[k], bot[k] - 0.012], 1)
            tx = np.linspace(xs[k][-1], xs[k][0], 20)
            ty = y_bot - (y_bot - y_top) * 0.4 + 0.035 * np.abs(np.sin(np.linspace(0, 2 * np.pi, 20)))
            self.shape(F(np.vstack([bl, np.stack([tx, ty], 1)])), tongue, 0)
            self.stroke(F([((x0 + x1) / 2 + 0.01, y_bot - (y_bot - y_top) * 0.3), ((x0 + x1) / 2 + 0.02, y_bot - 0.06)]),
                        ow * 0.45, (0.3, 0.3))
        for xe, sgn in ((x0, -1), (x1, 1)):
            c = F([(xe + sgn * 0.02, y_top - 0.06), (xe + sgn * 0.07, y_top + 0.0), (xe + sgn * 0.06, y_top + 0.07)])
            self.stroke(c, ow * 0.8, (0.3, 0.3))
        return mouth

    def star(self, x, y, r, points=5, rot=0.0, fill=WHITE, ow=None):
        """a little impact star"""
        t = np.linspace(0, 2 * np.pi, points * 2, endpoint=False) + rot - np.pi / 2
        rr = np.where(np.arange(points * 2) % 2 == 0, r, r * 0.45)
        return self.shape(np.stack([x + np.cos(t) * rr, y + np.sin(t) * rr], 1), fill,
                          self.ink_w * 0.7 if ow is None else ow)

    # ================================================================ cels: characters
    def alarm_clock(self, cx, cy, r, tilt=0.0, look=(0.6, -0.1), time=(7, 0), arms=(), legs=(), ring=True):
        """a twin-bell alarm clock that has jumped up to ring: black drum body, white dial with a face (pie-cut
        eyes, open grin), hands at `time`, two bells and a striker; rubber-hose arms and legs.
        arms: [dict(at=(x, y) wrist, side=-1|1, pose, angle, bend)], legs: [dict(at=(x, y) ankle, side, facing,
        tilt, bend)]. Returns the body Frame (local unit = r)."""
        F = Frame(cx, cy, r, tilt)
        ow = self.ink_w
        self.guide(F(ellipse_pts(0, 0, 1, 1)), True)
        self.guide(F([(0, -1.25), (0, 1.1)])); self.guide(F([(-1.05, -0.05), (1.05, -0.05)]))
        self.guide(F([(-0.9, 1.5), (-0.2, 0.6), (0.3, -0.6), (0.2, -1.6)]))
        for leg in legs:
            side = leg.get('side', 1)
            hip = F.p(0.36 * side, 0.86)
            path = hose_path(hip, leg['at'], leg.get('bend', 0.0), leg.get('bend2'))
            self.hose(path, r * 0.13)
            self.shoe(leg['at'][0], leg['at'][1], r * leg.get('shoe', 0.5), leg.get('facing', side), leg.get('tilt', 0.0))
        for arm in arms:
            side = arm.get('side', 1)
            sh = F.p(0.96 * side, 0.12)
            path = hose_path(sh, arm['at'], arm.get('bend', 0.0), arm.get('bend2'))
            self.hose(path, r * 0.105)
            d = path[-1] - path[-4]
            ang = arm.get('angle', float(np.arctan2(d[1], d[0])))
            self.glove(arm['at'][0], arm['at'][1], ang, r * arm.get('glove', 0.44), arm.get('pose', 'open'),
                       arm.get('flip', side))
        # bells, posts and striker (behind the drum)
        bells = []
        for side in (-1, 1):
            a = side * 0.66
            bc = F.p(np.sin(a) * 1.1, -np.cos(a) * 1.1)
            post0 = F.p(np.sin(a) * 0.8, -np.cos(a) * 0.8)
            self.hose(np.stack([np.linspace(post0[0], bc[0], 8), np.linspace(post0[1], bc[1], 8)], 1), r * 0.07, DARK,
                      ow * 0.7)
            B = Frame(bc[0], bc[1], r * 0.4, tilt + a)
            dome = np.vstack([[(-1.1, 0.2)], ellipse_pts(0, 0.05, 1.0, 1.05, a0=np.pi, a1=2 * np.pi, n=50), [(1.1, 0.2)],
                              ellipse_pts(0, 0.2, 1.1, 0.16, a0=0, a1=np.pi, n=20)])
            self.shape(B(dome), LIGHT, ow)
            self.shape(B(np.vstack([ellipse_pts(0, 0.2, 1.1, 0.16, a0=0, a1=np.pi, n=20),
                                    ellipse_pts(0, 0.02, 1.02, 0.13, a0=np.pi, a1=0, n=20)])), DARK, ow * 0.6)
            self.shape(B(ellipse_pts(-0.45, -0.5, 0.14, 0.36, rot=0.6)), WHITE, 0)
            self.shape(B(ellipse_pts(0, -1.08, 0.2, 0.16)), DARK, ow * 0.7)
            bells.append((bc, a))
        top = F.p(0, -0.96)
        for k, (a, fill) in enumerate(((-0.42, DARK), (0.42, None))):
            tip = F.p(np.sin(a) * 1.5, -0.96 - np.cos(a) * 0.5)
            if fill is None:
                self.stroke(np.stack([np.linspace(top[0], tip[0], 6), np.linspace(top[1], tip[1], 6)], 1), ow * 0.5)
                self.shape(ellipse_pts(tip[0], tip[1], r * 0.09, r * 0.09), None, ow * 0.5)
            else:
                self.hose(np.stack([np.linspace(top[0], tip[0], 6), np.linspace(top[1], tip[1], 6)], 1), r * 0.04, DARK,
                          ow * 0.6)
                self.shape(ellipse_pts(tip[0], tip[1], r * 0.1, r * 0.1), DARK, ow * 0.7)
        sw = F([(np.sin(a) * 1.62, -0.96 - np.cos(a) * 0.62) for a in np.linspace(-0.5, 0.5, 14)])
        self.stroke(sw, ow * 0.45, (0.4, 0.4))
        # drum, shine, dial
        self.shape(F(ellipse_pts(0, 0, 1, 1)), BLACK, ow)
        self.shape(F(np.vstack([ellipse_pts(0, 0, 0.95, 0.95, a0=3.55, a1=4.35, n=16),
                                ellipse_pts(0, 0, 0.86, 0.86, a0=4.35, a1=3.55, n=16)])), WHITE, 0)
        self.shape(F(ellipse_pts(0.62, 0.62, 0.05, 0.05)), WHITE, 0)
        self.shape(F(ellipse_pts(0, 0, 0.79, 0.79)), WHITE, ow * 0.8)
        for k in range(12):
            if k in (0, 3, 9, 5, 6, 7):
                continue
            a = k / 12 * 2 * np.pi
            self.stroke(F([(np.sin(a) * 0.66, -np.cos(a) * 0.66), (np.sin(a) * 0.73, -np.cos(a) * 0.73)]), ow * 0.6)
        fsz = r * 0.17
        for s, (lx, ly) in (('12', (0, -0.62)), ('3', (0.64, -0.02)), ('9', (-0.64, -0.02))):
            p = F.p(lx, ly)
            self.text(s, p[0], p[1], fsz, INK, 0, rot=-np.degrees(tilt), font=slab_font, effect=False)
        # face: brows, eyes, grin, then the hands on top
        for sgn in (-1, 1):
            ex = 0.27 * sgn
            self.stroke(F([(ex - 0.13, -0.5 - 0.04 * sgn * 0), (ex, -0.58), (ex + 0.13, -0.52)]), ow * 1.1, (0.3, 0.3))
        for sgn in (-1, 1):
            p = F.p(0.27 * sgn, -0.21)
            self.pie_eye(p[0], p[1], r * 0.15, r * 0.22, look=look, rot=tilt)
        self.grin(F, -0.42, 0.44, 0.24, 0.66, curve=0.07)
        hm = (time[0] % 12 + time[1] / 60) / 12 * 2 * np.pi; mm = time[1] / 60 * 2 * np.pi
        for a, L, w in ((mm, 0.5, 0.05), (hm, 0.3, 0.07)):
            d = np.array([np.sin(a), -np.cos(a)]); n = np.array([-d[1], d[0]])
            hand = [n * w, d * L, -n * w, -d * 0.08]
            self.shape(F(hand), BLACK, 0)
        self.shape(F(ellipse_pts(0, 0, 0.065, 0.065)), BLACK, 0)
        self.shape(F(ellipse_pts(-0.015, -0.015, 0.02, 0.02)), WHITE, 0)
        self.bells = bells
        return F

    def sun(self, cx, cy, r, mood='yawn', arms=(), rays=12, ray_style='wavy', clip=None):
        """a cartoon sun with a face (sleepy lids, a yawn) and stretching rubber-hose arms. ray_style 'wavy' =
        inked S-curved rays with a pale corona, 'spiky' = a crown of pointed rays"""
        prev = self._clip
        if clip is not None:
            self._clip = clip
        F = Frame(cx, cy, r)
        ow = self.ink_w * 0.9
        self.guide(F(ellipse_pts(0, 0, 1, 1)), True)
        for arm in arms:
            side = arm.get('side', 1)
            sh = F.p(0.92 * side, 0.05)
            path = hose_path(sh, arm['at'], arm.get('bend', 0.0), arm.get('bend2'))
            self.hose(path, r * 0.12)
            d = path[-1] - path[-4]
            self.glove(arm['at'][0], arm['at'][1], float(np.arctan2(d[1], d[0])), r * 0.42, arm.get('pose', 'fist'),
                       arm.get('flip', side))
        if ray_style == 'spiky':
            t = np.linspace(0, 2 * np.pi, rays * 2 * 12, endpoint=False)
            tri = 1 - np.abs(((t * rays / (2 * np.pi)) % 1) * 2 - 1)
            rr = 1.18 + 0.42 * tri ** 1.7 + 0.03 * np.sin(t * rays * 3)
            rr = np.where((np.arange(t.size) // 24) % 2 == 0, rr, 1.18 + (rr - 1.18) * 0.7)
            self.shape(F(np.stack([np.cos(t) * rr, np.sin(t) * rr], 1)), LIGHT, ow)
        else:
            t = np.linspace(0, 2 * np.pi, rays * 20, endpoint=False)
            rr = 1.1 + 0.11 * np.abs(np.sin(t * rays / 2)) ** 0.6           # a scalloped corona
            self.shape(F(np.stack([np.cos(t) * rr, np.sin(t) * rr], 1)), LIGHT, ow * 0.9)
            for i in range(rays):
                a = (i + 0.5) / rays * 2 * np.pi                            # a short ray in every notch
                L = 0.34 if i % 2 == 0 else 0.22
                rad = np.array([1.3, 1.3 + L])
                pts = np.stack([np.cos(a) * rad, np.sin(a) * rad], 1)
                self.stroke(F(pts), ow * (2.2 if i % 2 == 0 else 1.8), (0.15, 0.3))
        self.shape(F(ellipse_pts(0, 0, 1, 1)), WHITE, ow)
        for sgn in (-1, 1):
            p = F.p(0.33 * sgn, -0.2)
            self.pie_eye(p[0], p[1], r * 0.16, r * 0.2, look=(0.1 * sgn, -0.5), lid=0.5, face=WHITE)
            self.stroke(F([(0.33 * sgn - 0.15, -0.5), (0.33 * sgn, -0.55), (0.33 * sgn + 0.15, -0.48)]), ow, (0.3, 0.3))
        mouth = ellipse_pts(0, 0.36, 0.2, 0.24)
        self.shape(F(mouth), BLACK, ow * 0.8)
        self.shape(F(ellipse_pts(0, 0.48, 0.13, 0.08)), MID, 0)
        for sgn in (-1, 1):
            self.shape(F(ellipse_pts(0.58 * sgn, 0.2, 0.12, 0.07)), PALE, 0)
        self._clip = prev
        return F

    def pillow(self, cx, cy, w, h, tilt=0.0, arm=None, clip=None):
        """a sleeping pillow: pinched corners, closed eyes with lashes, a snoring 'o', a striped night-cap, and
        one rubber-hose arm out of the bedclothes holding up a glove ("five more minutes")"""
        prev = self._clip
        if clip is not None:
            self._clip = clip
        F = Frame(cx, cy, 1.0, tilt)
        ow = self.ink_w
        if arm:
            sh = F.p(-w * 0.44, h * 0.22)
            path = hose_path(sh, arm['at'], arm.get('bend', 0.0), arm.get('bend2'))
            self.hose(path, h * 0.12)
            d = path[-1] - path[-4]
            self.glove(arm['at'][0], arm['at'][1], arm.get('angle', float(np.arctan2(d[1], d[0]))), h * 0.4,
                       arm.get('pose', 'palm'), arm.get('flip', 1))
        t = np.linspace(0, 2 * np.pi, 160, endpoint=False)
        ct, st = np.cos(t), np.sin(t)
        x = np.sign(ct) * np.abs(ct) ** 0.72 * w / 2; y = np.sign(st) * np.abs(st) ** 0.72 * h / 2
        pinch = 1 - 0.13 * (np.cos(4 * t) + 1) / 2 + 0.06 * (1 - np.cos(4 * t)) / 2
        body = np.stack([x * pinch, y * pinch], 1)
        self.guide(F(ellipse_pts(0, 0, w / 2, h / 2)), True)
        self.shape(F(body), WHITE, ow)
        for sx in (-1, 1):
            for sy in (-1, 1):
                self.stroke(F([(sx * w * 0.42, sy * h * 0.36), (sx * w * 0.34, sy * h * 0.26)]), ow * 0.5, (0.2, 0.5))
        for sgn in (-1, 1):
            ex = w * 0.17 * sgn
            arc = ellipse_pts(ex, -h * 0.02, w * 0.075, h * 0.07, a0=0.15, a1=np.pi - 0.15, n=20)
            self.stroke(F(arc), ow * 1.0, (0.15, 0.15))
            for a in (0.7, 1.57, 2.4):
                p0 = (ex + np.cos(a) * w * 0.075, -h * 0.02 + np.sin(a) * h * 0.07)
                self.stroke(F([p0, (p0[0] + np.cos(a) * w * 0.035, p0[1] + np.sin(a) * h * 0.06)]), ow * 0.5)
        self.shape(F(ellipse_pts(w * 0.03, h * 0.22, w * 0.045, h * 0.075)), BLACK, ow * 0.6)
        for sgn in (-1, 1):
            self.shape(F(ellipse_pts(w * 0.3 * sgn, h * 0.15, w * 0.05, h * 0.04)), PALE, 0)
        # night-cap: a floppy striped cone over the right corner
        spine = np.array([(w * 0.33, -h * 0.36), (w * 0.47, -h * 0.82), (w * 0.64, -h * 0.84), (w * 0.72, -h * 0.5),
                          (w * 0.72, -h * 0.22)], np.float32)
        from core import spline
        sp = spline(spine, 10)
        n = len(sp)
        hw = w * (0.19 * (1 - np.linspace(0, 1, n)) ** 0.9 + 0.016)
        tg = np.gradient(sp, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
        L_, R_ = sp + nr * hw[:, None], sp - nr * hw[:, None]
        brim_c = sp[0]
        seg = max(2, n // 7)
        for i in range(0, n - 1, seg):
            j = min(n - 1, i + seg)
            q = np.vstack([L_[i:j + 1], R_[i:j + 1][::-1]])
            self.shape(F(q), DARK if (i // seg) % 2 == 0 else WHITE, 0)
        self.shape(F(np.vstack([L_, R_[::-1]])), None, ow)
        t0 = tg[0]; ext = (L_[0] - R_[0]) * 0.06
        band = np.vstack([L_[0] + ext - t0 * h * 0.06, R_[0] - ext - t0 * h * 0.06,
                          R_[0] - ext + t0 * h * 0.13, L_[0] + ext + t0 * h * 0.13])
        self.shape(F(band), LIGHT, ow * 0.8)
        tip = sp[-1]
        self.shape(F(ellipse_pts(tip[0], tip[1] + h * 0.06, w * 0.05, w * 0.05)), WHITE, ow * 0.8)
        self._clip = prev
        return F

    def slipper(self, x, y, size, facing=1, tilt=0.0, mood='happy'):
        """a fuzzy bedroom slipper that dances: sole, domed upper, pom-pom, pie-cut eyes and a smile"""
        F = Frame(x, y, size, tilt * facing, facing)
        ow = self.ink_w * 0.85
        self.shape(F(ellipse_pts(0.0, 0.08, 0.66, 0.2)), DARK, ow)
        self.shape(F(ellipse_pts(-0.2, 0.03, 0.42, 0.15)), LIGHT, ow * 0.8)
        self.shape(F(ellipse_pts(-0.22, 0.05, 0.32, 0.09)), MID, ow * 0.5)
        toe = np.vstack([ellipse_pts(0.3, 0.1, 0.38, 0.44, a0=np.pi, a1=2 * np.pi, n=40),
                         ellipse_pts(0.3, 0.1, 0.38, 0.1, a0=0, a1=np.pi, n=20)])
        self.shape(F(toe), LIGHT, ow)
        for k in range(8):
            a = np.pi + 0.25 + k * 0.37
            p = (0.3 + np.cos(a) * 0.32, 0.1 + np.sin(a) * 0.36)
            self.stroke(F([p, (p[0] + 0.02, p[1] + 0.05)]), ow * 0.35)
        self.shape(F(ellipse_pts(0.52, -0.3, 0.12, 0.11)), WHITE, ow * 0.8)
        for ex in (0.2, 0.4):
            p = F.p(ex, -0.1)
            self.pie_eye(p[0], p[1], size * 0.065, size * 0.095, look=(0.5, -0.3), ow=ow * 0.6)
        self.stroke(F(ellipse_pts(0.31, 0.04, 0.09, 0.05, a0=0.2, a1=np.pi - 0.2, n=12)), ow * 0.7, (0.2, 0.2))
        return F

    # ================================================================ cels: effects
    def vibration(self, cx, cy, r, a0, a1, n=3, gap=None, width=None):
        """concentric shake arcs (')))') outside a ringing thing, between angles a0..a1"""
        gap = gap or r * 0.28; width = width or self.ink_w * 0.9
        for k in range(n):
            rr = r + gap * (k + 1)
            self.stroke(ellipse_pts(cx, cy, rr, rr, a0=a0 + 0.05 * k, a1=a1 - 0.05 * k, n=24), width, (0.3, 0.3), effect=True)

    def speed_lines(self, pts_list, width=None):
        for P in pts_list:
            self.stroke(P, width or self.ink_w * 0.9, (0.0, 0.7), effect=True)

    def lettering(self, s, path, size, fill=WHITE, ow=None, wobble=10.0, bounce=0.12, spacing=0.9):
        """bouncing slab-serif lettering along a curve (spline through `path`), each letter tilted the other way"""
        from core import spline
        sp = spline(np.asarray(path, np.float32), 30)
        seg = np.hypot(*np.diff(sp, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)])
        f = slab_font(size)
        adv = [f.getlength(ch) * spacing + size * 0.06 for ch in s]
        total = sum(adv); start = (cum[-1] - total) / 2
        pos = start
        for i, ch in enumerate(s):
            u = pos + adv[i] / 2
            x = float(np.interp(u, cum, sp[:, 0])); y = float(np.interp(u, cum, sp[:, 1]))
            j = min(len(sp) - 2, int(np.searchsorted(cum, u)))
            ang = np.degrees(np.arctan2(sp[j + 1, 1] - sp[j, 1], sp[j + 1, 0] - sp[j, 0]))
            rot = -ang + (wobble if i % 2 else -wobble)
            dy = size * bounce * (1 if i % 2 else -1)
            sz = size * (1.0 + 0.08 * ((i % 3) - 1))
            self.text(ch, x, y + dy, sz, fill, ow, rot)
            pos += adv[i]

    def zzz(self, x, y, size, n=3, dx=46, dy=-52):
        for k in range(n):
            self.text('Z', x + dx * k, y + dy * k, size * (1 + 0.32 * k), WHITE, self.ink_w * 0.8, rot=12 - 10 * k)

    # ================================================================ rendering the cels
    def _stamp(self, draws, vals, P, rad, closed=False, wobble=0.0, seed=0):
        S = self.ss
        Q, u, L = _resample(P * S, max(0.7, float(np.min(rad)) * S * 0.22), closed)
        n = len(Q)
        if np.ndim(rad):
            r = np.interp(u, np.linspace(0, 1, len(rad)), rad) * S
        else:
            r = np.full(n, rad * S, np.float32)
        if wobble and n > 2:
            r = r * (1 + wobble * fbm1d(n, max(4.0, n / max(1.0, L / (70.0 * S))), 3, seed))
        for (x, y), rr in zip(Q, r):
            if rr < 0.4:
                continue
            bb = [x - rr, y - rr, x + rr, y + rr]
            for d, v in zip(draws, vals):
                d.ellipse(bb, fill=v)

    def _poly(self, draws, vals, P):
        S = self.ss
        Q = [(float(x * S), float(y * S)) for x, y in P]
        for d, v in zip(draws, vals):
            d.polygon(Q, fill=v)

    def _draw(self, p, imgs, shadow_d):
        """draw one primitive into the (val, alpha, line) cel images"""
        D = [ImageDraw.Draw(im) for im in imgs]
        k = p['k']; inkv = int(INK * 255)
        if k == 'guide':
            return
        if k == 'shadow':
            self._poly([shadow_d], [int(255 * p['a'])], p['pts'])
            return
        if k == 'shape':
            P, fill, ow = p['pts'], p['fill'], p['ow']
            if fill is None:
                self._stamp(D, [inkv, 255, 255], P, ow / 2, closed=p['closed'], wobble=0.1, seed=p['seed'])
                return
            if ow > 0:
                self._poly(D, [inkv, 255, 255], P)
                self._stamp(D, [inkv, 255, 255], P, ow, closed=True, wobble=0.1, seed=p['seed'])
            self._poly(D, [int(fill * 255), 255, 0], P)
            if ow <= 0:
                self._stamp(D[2:], [255], P, 0.9, closed=True)
            return
        if k == 'union':
            fill, ow = p['fill'], p['ow']
            for i, sub in enumerate(p['subs']):
                if sub[0] == 'poly':
                    self._poly(D, [inkv, 255, 255], sub[1])
                    self._stamp(D, [inkv, 255, 255], sub[1], ow, closed=True, wobble=0.1, seed=p['seed'] + i)
                else:
                    self._stamp(D, [inkv, 255, 255], sub[1], sub[2] + ow)
            for sub in p['subs']:
                if sub[0] == 'poly':
                    self._poly(D, [int(fill * 255), 255, 0], sub[1])
                else:
                    self._stamp(D, [int(fill * 255), 255, 0], sub[1], sub[2])
            return
        if k == 'hose':
            P, w, ow = p['pts'], p['w'], p['ow']
            self._stamp(D, [inkv, 255, 255], P, w / 2 + ow, wobble=0.05, seed=p['seed'])
            self._stamp(D, [int(p['fill'] * 255), 255, 0], P, w / 2)
            return
        if k == 'stroke':
            P, w = p['pts'], p['w']
            t0, t1 = p['taper']
            u = np.linspace(0, 1, 64)
            prof = np.ones_like(u)
            if t0 > 0:
                prof = np.minimum(prof, 0.25 + 0.75 * np.clip(u / t0, 0, 1))
            if t1 > 0:
                prof = np.minimum(prof, 0.25 + 0.75 * np.clip((1 - u) / t1, 0, 1))
            self._stamp(D, [int(p['value'] * 255), 255, 255], P, prof * w / 2, wobble=0.08, seed=p['seed'])
            return
        if k == 'text':
            S = self.ss
            fnt = (p['font'] or slab_font)(p['size'] * S)
            sw = int(round(p['ow'] * S))
            pad = sw + int(p['size'] * S * 0.3)
            bx = fnt.getbbox(p['s'], anchor='mm')
            w_, h_ = bx[2] - bx[0] + 2 * pad, bx[3] - bx[1] + 2 * pad
            outer = Image.new('L', (w_, h_), 0); inner = Image.new('L', (w_, h_), 0)
            c = (w_ / 2 - (bx[0] + bx[2]) / 2, h_ / 2 - (bx[1] + bx[3]) / 2)
            ImageDraw.Draw(outer).text(c, p['s'], font=fnt, fill=255, anchor='mm', stroke_width=sw, stroke_fill=255)
            ImageDraw.Draw(inner).text(c, p['s'], font=fnt, fill=255, anchor='mm')
            if p['rot']:
                outer = outer.rotate(p['rot'], Image.BICUBIC, expand=True)
                inner = inner.rotate(p['rot'], Image.BICUBIC, expand=True)
            ox, oy = int(round(p['x'] * S - outer.width / 2)), int(round(p['y'] * S - outer.height / 2))
            val, al, ln = imgs
            val.paste(inkv, (ox, oy), outer); al.paste(255, (ox, oy), outer); ln.paste(255, (ox, oy), outer)
            if sw > 0:
                val.paste(int(p['fill'] * 255), (ox, oy), inner); ln.paste(0, (ox, oy), inner)
            else:
                val.paste(int(p['fill'] * 255), (ox, oy), inner)
            return

    def _render_paint(self):
        key = ('paint', len(self.prims))
        if self._cache and self._cache[0] == key:
            return self._cache[1]
        S = self.ss; size = (self.W * S, self.H * S)
        L = [Image.new('L', size, 0) for _ in range(3)]
        sh = Image.new('L', size, 0); shd = ImageDraw.Draw(sh)
        cur, tmp = None, None

        def flush(tmp, name):
            m = ImageChops.multiply(tmp[1], self.clips[name])
            for a, b in zip(L, tmp):
                a.paste(b, (0, 0), m)

        for p in self.prims:
            c = p.get('clip')
            if p['k'] == 'shadow':
                c = cur
            if c != cur:
                if tmp is not None:
                    flush(tmp, cur)
                tmp = [Image.new('L', size, 0) for _ in range(3)] if c else None
                cur = c
            tgt = tmp if tmp is not None else L
            self._draw(p, tgt, shd)
        if tmp is not None:
            flush(tmp, cur)
        out = (L, sh.filter(ImageFilter.GaussianBlur(2 * S)))
        self._cache = (key, out)
        return out

    def _render_pencil(self):
        S = self.ss; size = (self.W * S, self.H * S)
        pen = Image.new('L', size, 0); d = ImageDraw.Draw(pen)
        rng = np.random.default_rng(12345)

        def outline(P, closed, val, w, j):
            Q = (np.asarray(P, np.float32) + j) * S
            Q = [tuple(map(float, q)) for q in Q]
            if closed:
                Q = Q + Q[:1]
            if len(Q) > 1:
                d.line(Q, fill=val, width=w, joint='curve')

        def fillpoly(P, j):
            Q = [tuple(map(float, q)) for q in (np.asarray(P, np.float32) + j) * S]
            if len(Q) > 2:
                d.polygon(Q, fill=0)

        def hose_sides(P, w):
            P = np.asarray(P, np.float32)
            tg = np.gradient(P, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
            nr = np.stack([-tg[:, 1], tg[:, 0]], 1)
            return P + nr * w / 2, P - nr * w / 2

        for p in self.prims:
            if p.get('fx') or p['k'] in ('shadow', 'text', 'guide'):
                continue
            j0 = rng.normal(0, 1.1, 2).astype(np.float32)
            for ps, (val, w) in enumerate(((235, max(3, int(1.7 * S))), (150, max(2, int(1.1 * S))))):
                j = j0 * (1 if ps == 0 else -0.8) + rng.normal(0, 0.5, 2).astype(np.float32)
                k = p['k']
                if k == 'shape':
                    if p['fill'] is not None and ps == 0:
                        fillpoly(p['pts'], j)
                    outline(p['pts'], p['closed'], val, w, j)
                elif k == 'union':
                    if ps == 0:
                        for sub in p['subs']:
                            if sub[0] == 'poly':
                                fillpoly(sub[1], j)
                    for sub in p['subs']:
                        if sub[0] == 'poly':
                            outline(sub[1], True, val, w, j)
                        else:
                            a, b = hose_sides(sub[1], sub[2] * 2)
                            outline(a, False, val, w, j); outline(b, False, val, w, j)
                            outline(ellipse_pts(*sub[1][-1], sub[2], sub[2]), True, val, w, j)
                elif k == 'hose':
                    a, b = hose_sides(p['pts'], p['w'])
                    outline(a, False, val, w, j); outline(b, False, val, w, j)
                elif k == 'stroke':
                    outline(p['pts'], False, val, w, j)
        for p in self.prims:
            if p['k'] == 'guide':
                outline(p['pts'], p['closed'], 110, max(1, int(1.0 * S)), np.zeros(2, np.float32))
        return pen

    # ================================================================ state changes
    def ink(self):
        """trace the pencil roughs onto cels in black ink (snapshots now show the ink lines only)"""
        self.state = 'ink'

    def paint(self):
        """paint the backs of the cels in flat greys (snapshots now show the finished cels)"""
        self.state = 'paint'

    def film(self, grain=0.07, soft=0.85, halation=0.1, tone='silver', vignette=0.42, weave=(3.0, -2.0, 0.15),
             gate=(22, 16, 70), lift=0.075, white=0.93):
        """photograph the cel set-up onto black-and-white film and print it: lens softness, halation, print tone
        curve, grain, uneven density, vignette, gate weave, rounded projector gate"""
        self.film_opts = dict(grain=grain, soft=soft, halation=halation, tone=tone, vignette=vignette, weave=weave,
                              gate=gate, lift=lift, white=white)

    def age(self, scratches=7, dust=90, specks=60, fibres=4, hair=True, stains=3, flicker=0.05, seed=None):
        """wear the print: scratches, white dust and black specks, lint fibres, a hair in the gate, stains and a
        frame of flicker"""
        self.age_opts = dict(scratches=scratches, dust=dust, specks=specks, fibres=fibres, hair=hair, stains=stains,
                             flicker=flicker, seed=self._seed() if seed is None else seed)

    # ================================================================ compositing, film and aging
    def _down(self, a):
        S = self.ss
        if isinstance(a, Image.Image):
            a = np.asarray(a, np.uint8)
            return a.reshape(self.H, S, self.W, S).mean(axis=(1, 3), dtype=np.float32) / 255
        return a.reshape(self.H, S, self.W, S).mean(axis=(1, 3), dtype=np.float32)

    def _compose(self, view=None):
        if view == 'layout':
            paper = 0.95 + self._down(self.tex) * 0.012
            return paper * (1 - 0.55 * self._down(self.layout))
        v = np.clip(self._down(self.bg), 0, 1)
        if view == 'background':
            return v
        if self.state == 'pencil':
            return v * (1 - 0.8 * self._render_pencil_cached())
        (val, al, ln), sh = self._render_paint()
        if self.state == 'ink':
            l1 = self._down(ln)
            return v * (1 - l1) + INK * l1
        v = v * (1 - 0.9 * self._down(sh))
        a1 = self._down(al)
        pv = self._down(ImageChops.multiply(val, al))
        return v * (1 - a1) + pv

    def _render_pencil_cached(self):
        key = ('pencil', len(self.prims))
        if self._cache and self._cache[0] == key:
            return self._cache[1]
        out = self._down(self._render_pencil())
        self._cache = (key, out)
        return out

    def _film_pass(self, v):
        o = self.film_opts; H, W = self.H, self.W
        rng = np.random.default_rng(777)
        YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
        r2 = ((XX - W / 2) / (W / 2)) ** 2 + ((YY - H / 2) / (H / 2)) ** 2
        # lens: soft overall, softer toward the corners, halation round bright paint
        v = blur(v, o['soft'])
        e = np.clip(r2 * 0.5, 0, 1)
        v = v * (1 - e) + blur(v, 1.8) * e
        v = v + o['halation'] * blur(np.clip(v - 0.78, 0, 1), 6) * 3
        # gate weave: the frame sits a little off and a hair rotated in the gate
        dx, dy, rot = o['weave']
        im = Image.fromarray(v.astype(np.float32), 'F')
        im = im.rotate(rot, Image.BICUBIC, center=(W / 2, H / 2), translate=(dx, dy), fillcolor=0.02)
        v = np.asarray(im, np.float32)
        # print tone curve
        t = np.clip(v, 0, 1)
        t = t ** 1.1
        t = np.clip(0.5 + (t - 0.5) * 1.1, 0, 1)
        t = t * t * (3 - 2 * t) * 0.35 + t * 0.65
        out = o['lift'] + (o['white'] - o['lift']) * t
        # uneven density, grain
        out *= 1 + (noise2d(H // 4, W // 4, 90, 3, 31).repeat(4, 0).repeat(4, 1)[:H, :W] - 0.5) * 0.06
        g = rng.standard_normal((H, W)).astype(np.float32)
        g = blur(g, 0.7) * 2.2 + rng.standard_normal((H, W)).astype(np.float32) * 0.25
        clump = blur(rng.standard_normal((H // 2, W // 2)).astype(np.float32), 1.0).repeat(2, 0).repeat(2, 1)[:H, :W]
        g = g + clump * 1.6
        amp = o['grain'] * (0.45 + 1.6 * np.sqrt(np.clip(out * (1 - out), 0, 0.25)))
        out = out + g * amp * 0.5
        return out, r2, (XX, YY)

    def _age_pass(self, out, XX, YY):
        a = self.age_opts; H, W = self.H, self.W
        rng = np.random.default_rng(a['seed'])
        # stains: faint drying marks with a darker rim
        for _ in range(a['stains']):
            cx, cy = rng.uniform(150, W - 150), rng.uniform(100, H - 100)
            rx, ry = rng.uniform(40, 120), rng.uniform(30, 90)
            d = np.sqrt(((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2)
            ring = np.exp(-((d - 1) / 0.06) ** 2) * 0.025 - (d < 1) * 0.012
            out -= ring * (1 + 0.5 * np.sin(np.arctan2(YY - cy, XX - cx) * 3))
        # scratches: long vertical lines that wander and come and go
        for k in range(a['scratches']):
            x0 = rng.uniform(80, W - 80)
            white = k % 3 != 2
            wid = rng.uniform(0.6, 1.6) if white else rng.uniform(1.0, 2.2)
            xs = x0 + fbm1d(H, 400, 3, int(rng.integers(1 << 30))) * rng.uniform(4, 14) + np.arange(H) * rng.uniform(-0.01, 0.01)
            on = np.clip(fbm1d(H, rng.uniform(150, 600), 3, int(rng.integers(1 << 30))) * 3 + rng.uniform(0.2, 1.2), 0, 1)
            y0 = int(rng.uniform(0, H * 0.5)) if rng.random() < 0.4 else 0
            on[:y0] = 0
            for dxk in range(-3, 4):
                cols = np.clip((xs + dxk).astype(int), 0, W - 1)
                cov = np.clip(1 - np.abs(cols + 0.5 - xs) / wid, 0, 1) * on
                rows = np.arange(H)
                if white:
                    out[rows, cols] += (0.97 - out[rows, cols]) * cov * rng.uniform(0.55, 0.85)
                else:
                    out[rows, cols] *= 1 - cov * 0.45
        # white dust (dirt on the negative) and black specks (dirt on the print), fibres, a hair
        S = 2
        wim = Image.new('L', (W * S, H * S), 0); bim = Image.new('L', (W * S, H * S), 0)
        dw, db = ImageDraw.Draw(wim), ImageDraw.Draw(bim)
        for n, d in ((a['dust'], dw), (a['specks'], db)):
            for _ in range(n):
                x, y = rng.uniform(0, W), rng.uniform(0, H)
                r = rng.uniform(0.5, 1.6) if rng.random() < 0.85 else rng.uniform(2.0, 4.5)
                pts = [((x + np.cos(t) * r * rng.uniform(0.6, 1.3)) * S, (y + np.sin(t) * r * rng.uniform(0.6, 1.3)) * S)
                       for t in np.linspace(0, 2 * np.pi, 7, endpoint=False)]
                d.polygon(pts, fill=int(rng.uniform(150, 255)))
        for k in range(a['fibres'] + (1 if a['hair'] else 0)):
            hair = a['hair'] and k == a['fibres']
            n = 40
            if hair:
                x, y = rng.uniform(W * 0.78, W * 0.92), H - 40
                L = 210
            else:
                x, y = rng.uniform(100, W - 100), rng.uniform(80, H - 80)
                L = rng.uniform(18, 60)
            ang = np.cumsum(rng.normal(0, 0.35, n)) + rng.uniform(0, 2 * np.pi) if not hair else \
                np.cumsum(rng.normal(0, 0.22, n)) - 1.9
            px = x + np.cumsum(np.cos(ang)) * L / n; py = y + np.cumsum(np.sin(ang)) * L / n
            (db if hair else dw).line([(float(a_ * S), float(b_ * S)) for a_, b_ in zip(px, py)],
                                      fill=255 if hair else 200, width=3 if hair else 2, joint='curve')
        wm = np.asarray(wim, np.uint8).reshape(H, S, W, S).mean(axis=(1, 3), dtype=np.float32) / 255
        bm = np.asarray(bim, np.uint8).reshape(H, S, W, S).mean(axis=(1, 3), dtype=np.float32) / 255
        out = out + (0.98 - out) * wm
        out = out * (1 - 0.85 * bm)
        # flicker: this frame came out a touch dense on one side
        out *= 1 - a['flicker'] * np.clip((XX / W - 0.35), 0, 1)
        return out

    def _finish(self, v):
        if self.film_opts is None:
            g = np.clip(v, 0, 1)
            return Image.fromarray((np.stack([g, g, g], -1) * 255 + 0.5).astype(np.uint8))
        o = self.film_opts; H, W = self.H, self.W
        out, r2, (XX, YY) = self._film_pass(v)
        if self.age_opts is not None:
            out = self._age_pass(out, XX, YY)
        out *= 1 - o['vignette'] * np.clip(r2 / 2, 0, 1) ** 1.3
        out = np.clip(out, 0, 1)
        if o['tone'] == 'sepia':
            rgb = np.stack([out ** 0.88, out ** 0.97, out ** 1.18], -1)
        elif o['tone'] == 'neutral':
            rgb = np.stack([out, out, out], -1)
        else:
            rgb = np.stack([out ** 0.95, out ** 0.985, out ** 1.07], -1)
        # rounded projector gate, soft edge, slightly irregular
        gx, gy, rad = o['gate']
        m = Image.new('L', (W * 2, H * 2), 0)
        ImageDraw.Draw(m).rounded_rectangle([gx * 2, gy * 2, (W - gx) * 2, (H - gy) * 2], radius=rad * 2, fill=255)
        m = m.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(2.2))
        gm = np.asarray(m, np.float32)[..., None] / 255
        edge = 0.025 + 0.01 * (noise2d(H // 8, W // 8, 20, 2, 5).repeat(8, 0).repeat(8, 1)[:H, :W, None])
        rgb = rgb * gm + edge * (1 - gm)
        return Image.fromarray((np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8))

    def composite(self, view=None):
        return self._finish(self._compose(view))

    def stage(self, name, view=None):
        """snapshot for the draw-on animation. view='layout' shows only the background layout pencil on paper,
        view='background' the painted background without cels; otherwise the current state (pencil / ink / paint,
        filmed and aged once film() / age() were called)"""
        self.stages.append((name, self.composite(view)))

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
