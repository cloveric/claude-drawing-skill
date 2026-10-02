"""silhouette — cut-paper silhouette portraits ("shades", c. 1790): black paper cut with small scissors, pasted on
an ivory card, touched with thin shell gold, glazed in an oval gilt frame and hung on a block-printed wallpaper
(numpy + Pillow only).

Model:
  wallpaper  hand block-printed paper of the 1790s. A distemper ground brushed on by hand (broad mottling and a
             faint horizontal brush drag), then each colour printed from its own wooden block: matte and chalky,
             a little uneven, the colour squeezed into a slightly stronger rim at the edge of every printed shape,
             dry specks where the block took too little colour, small misregistration between the blocks, and the
             tiny pin-dots the printer used to line the block up. Lengths are butted at vertical seams where the
             pattern does not quite match; inside a length the short sheets that made the roll show as faint
             horizontal joins. Daylight from a window at the upper left falls off across the wall.
  mouldings  picture rail and chair rail: painted wooden mouldings lit from the upper left, throwing a soft
             shadow down onto the paper; a brass hook over the picture rail for every frame.
  cord       a twisted silk cord from the hook, splitting into an inverted V that runs behind the frame: a lit
             cylinder with diagonal twist stripes and its own shadow on the wall.
  frame      an oval gilt frame built as a height field from a moulding profile, from the opening outwards:
             sight-edge bead, cove, a row of pearls, a big torus (optionally twisted like a ribbon), a fillet and
             an outer roll. Gold is a mirror: every pixel's normal reflects a room (a soft window at the upper
             left, a dim room, a dark floor), so the gilt reads as the concentric bright and dark rings of a real
             frame. Gold leaf is laid in squares (faint overlaps); on the most exposed crests it is rubbed through
             to the red bole underneath; grime and ambient occlusion sit in the hollows. Contact and soft drop
             shadows on the wall.
  card       ivory card behind the glass: smooth, toned darker toward the edge (two centuries of light), with a
             few foxing spots.
  paper      the silhouette is black paper cut with scissors. The main outline (`shape`) is glued flat and throws
             only a hairline shadow; loose snips (`snip`, `line`, `fringe`: hair, lashes, whiskers, plume barbs,
             ribbon ends, rigging) are cut as separate tapered strips that lift a little and throw a longer
             shadow. `hole` cuts the paper away so the card shows through (an eye, the gap between legs).
             Outlines are resampled into tiny straight facets, one closing of the blades each; the black has a
             faint fibre and sheen, and edges that face the light catch a hairline. Everything is drawn at 4x and
             box-filtered down, so strands a pixel wide survive.
  bronze     thin shell-gold paint brushed over the black (hair strands, lace, folds, sail seams). Every stroke
             tapers, has its own brightness (the metal flakes lie at random) and a little grain; paint only stays
             on the paper.
  ink        captions in iron-gall ink, faded to brown, a little uneven; `pen` for ruled lines and flourishes.
  glass      verre eglomise: a black band with a gold fillet painted on the back of the glass round the opening;
             the rebate of the frame throws a shadow onto the card from the upper left; after `glaze()` the convex
             glass picks up a soft sheen and a crisp reflection of the window.

    from silhouette import Silhouette
    s = Silhouette(1920, 1080, seed=1)
    s.wallpaper(); s.picture_rail(); s.chair_rail(1000)
    f = s.frame(960, 540, 220, 280, width=60, hook=True)            # opening radii; gilt moulding outside them
    c = s.sheet(f, at=(960, 560), scale=0.5)                        # black paper; px = at + 0.5 * design units
    c.shape(profile_pts); c.snip(hair_pts, 6, 0.5); c.hole(eye_pts)
    s.paste(c)                                                       # glue it onto the card
    s.bronze(c, [strand_pts, ...], width=2.5)                        # thin gold over the black
    s.caption(f, 'Miss A. Lark', 960, 780, 34)
    s.glaze()                                                        # glass reflections on every frame
    s.save('out.jpg')
Coordinates are output pixels, y down. Sheet and bronze methods take design units: px = at + scale * (x, y)
(x mirrored when flip=True); widths are in design units too.
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, noise2d, smoothstep, shift, load_font, text_mask


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- fonts: copperplate roundhand and a Georgian italic
_FONTS = {
    'roundhand': [('/System/Library/Fonts/Supplemental/SnellRoundhand.ttc', 0), ('/System/Library/Fonts/Supplemental/Apple Chancery.ttf', 0),
                  ('/usr/share/fonts/**/z003*.[ot]tf', 0), ('C:/Windows/Fonts/segoesc.ttf', 0)],
    'italic': [('/System/Library/Fonts/Supplemental/Baskerville.ttc', 2), ('/System/Library/Fonts/Supplemental/Hoefler Text.ttc', 2),
               ('/System/Library/Fonts/Supplemental/Didot.ttc', 1), ('/usr/share/fonts/**/DejaVuSerif-Italic.ttf', 0),
               ('C:/Windows/Fonts/georgiai.ttf', 0)],
    'caps': [('/System/Library/Fonts/Supplemental/Didot.ttc', 0), ('/System/Library/Fonts/Supplemental/Baskerville.ttc', 0),
             ('/usr/share/fonts/**/DejaVuSerif.ttf', 0), ('C:/Windows/Fonts/georgia.ttf', 0)],
}
_FCACHE = {}


def sil_font(kind, size):
    """PIL font: 'roundhand' (copperplate script), 'italic' (Georgian italic) or 'caps' (Didone roman).
    Override with $INKPAINT_FONT_ROUNDHAND / _ITALIC / _CAPS."""
    key = (kind, int(size))
    if key in _FCACHE: return _FCACHE[key]
    env = os.environ.get('INKPAINT_FONT_' + kind.upper())
    font = None
    for pat, idx in ([(env, 0)] if env else []) + _FONTS.get(kind, []):
        for p in glob.glob(pat, recursive=True):
            try:
                font = ImageFont.truetype(p, max(4, int(size)), index=idx); break
            except OSError:
                pass
        if font: break
    if font is None: font = load_font({'roundhand': 'script', 'italic': 'serif', 'caps': 'serif'}.get(kind, 'serif'), size)
    _FCACHE[key] = font
    return font


def _box3(a, n=1):
    """3 x 3 mean, n times (a cheap small blur for full-canvas float32 arrays)"""
    for _ in range(n):
        p = np.pad(a, 1, mode='edge')
        a = (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] + p[1:-1, :-2] + p[1:-1, 1:-1] + p[1:-1, 2:] + p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:]) / 9
    return a


def _resample(P, step, closed):
    """polyline -> points every `step` along its length"""
    P = np.asarray(P, np.float64)
    if closed: P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    n = max(3, int(s[-1] / max(step, 1e-3)) + 1)
    t = np.linspace(0, s[-1], n, endpoint=not closed)
    return np.stack([np.interp(t, s, P[:, 0]), np.interp(t, s, P[:, 1])], 1)


def _strip(C, w0, w1):
    """outline polygon of a tapered strip along centreline C (N x 2) whose width runs w0 -> w1 (or an array)"""
    C = np.asarray(C, np.float64)
    if len(C) < 2: return None
    d = np.gradient(C, axis=0)
    d /= np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9
    n = np.stack([-d[:, 1], d[:, 0]], 1)
    w = np.asarray(w0, np.float64) if np.ndim(w0) else np.linspace(w0, w1, len(C))
    L = C + n * (w[:, None] / 2); R = C - n * (w[:, None] / 2)
    return np.vstack([L, R[::-1]])


def smooth(pts, per=8, closed=True):
    """Catmull-Rom through control points; closed=True wraps round (outlines), False for open curves"""
    P = np.asarray(pts, np.float64)
    if not closed:
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    else:
        P = np.vstack([P[-1:], P, P[:2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, per, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed: out.append(P[-2])
    return np.array(out)


class Frame:
    """an oval gilt frame on the wall and the card behind its glass (local arrays cover the opening's bbox)"""
    pass


class Sheet:
    """a sheet of black paper over one frame's card; draws at `ss` x supersampling in design units"""

    def __init__(self, sil, frame, at, scale, flip, ss=4, facet=2.2, warp=None):
        self.sil, self.f, self.ss, self.warp = sil, frame, ss, warp
        self.ax, self.ay = at
        self.k, self.flip, self.facet = scale, flip, facet
        size = (frame.w * ss, frame.h * ss)
        self.body = Image.new('L', size, 0)
        self.loose = Image.new('L', size, 0)
        self.db, self.dl = ImageDraw.Draw(self.body), ImageDraw.Draw(self.loose)
        self.mask = None
        self.rng = np.random.default_rng(sil._seed())

    # ---------------------------------------------------------------- coordinates
    def px(self, pts):
        """design units -> canvas pixels"""
        P = np.asarray(pts, np.float64).reshape(-1, 2)
        if self.warp is not None: P = np.asarray(self.warp(P), np.float64).reshape(-1, 2)
        x = -P[:, 0] if self.flip else P[:, 0]
        return np.stack([self.ax + self.k * x, self.ay + self.k * P[:, 1]], 1)

    def _ss(self, pts):
        P = self.px(pts)
        return np.stack([(P[:, 0] - self.f.x0) * self.ss, (P[:, 1] - self.f.y0) * self.ss], 1)

    def _poly(self, draw, P, fill):
        if P is None or len(P) < 3: return
        draw.polygon([(float(x), float(y)) for x, y in P], fill=fill)

    # ---------------------------------------------------------------- cutting
    def shape(self, pts, loose=False):
        """the main outline, glued flat: closed polygon in design units (spline it first). The edge is
        re-cut into tiny straight facets with a hair of jitter, like successive closings of the scissors."""
        P = self._ss(pts)
        step = self.facet * self.ss
        Q = _resample(P, step, closed=True)
        if len(Q) > 6:
            d = np.roll(Q, -1, 0) - np.roll(Q, 1, 0)
            n = np.stack([-d[:, 1], d[:, 0]], 1) / (np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9)
            Q = Q + n * self.rng.normal(0, 0.12 * self.ss, (len(Q), 1))
        self._poly(self.dl if loose else self.db, Q, 255)

    def snip(self, pts, w0, w1=0.0, loose=True):
        """a separately cut tapered strip along a centreline (hair, lash, whisker, ribbon end), width in design
        units from w0 at the start to w1 at the end (or an array of widths)"""
        P = self._ss(pts)
        if len(P) < 2: return
        C = _resample(P, max(1.0, self.ss * 0.75), closed=False)
        k = self.k * self.ss
        w = np.asarray(w0, np.float64) * k if np.ndim(w0) else np.linspace(w0 * k, w1 * k, len(C))
        if np.ndim(w0): w = np.interp(np.linspace(0, 1, len(C)), np.linspace(0, 1, len(w)), w)
        w = np.maximum(w, 0.9)                                        # never thinner than ~1/4 px: it would vanish
        self._poly(self.dl if loose else self.db, _strip(C, w, None), 255)

    def line(self, pts, w, loose=True):
        """a constant-width strip (rigging, a cord, a stem)"""
        P = self._ss(pts)
        C = _resample(P, max(1.0, self.ss * 0.75), closed=False)
        self._poly(self.dl if loose else self.db, _strip(C, max(0.9, w * self.k * self.ss), max(0.9, w * self.k * self.ss)), 255)

    def disc(self, x, y, r, loose=False):
        t = np.linspace(0, 2 * np.pi, 40, endpoint=False)
        self.shape(np.stack([x + r * np.cos(t), y + r * np.sin(t)], 1), loose)

    def hole(self, pts):
        """cut the paper away: the card shows through"""
        P = self._ss(pts)
        self._poly(self.db, P, 0); self._poly(self.dl, P, 0)

    def fringe(self, pts, n, length, angle=40.0, width=3.0, side=(1, -1), bend=0.25, jitter=0.18, tip=0.0, start=0.0):
        """many loose strands along a curve: plume barbs, fur, frizz. `length` is a number or (at start, at end);
        `angle` is the strand angle from the curve's direction in degrees (barbs sweep toward the tip); `side`
        picks which sides get strands (+1 left of travel, -1 right); `bend` curls each strand back toward the
        curve; `start` skips the first fraction of the curve."""
        C = _resample(np.asarray(pts, np.float64), 1.0, closed=False)
        seg = np.hypot(*np.diff(C, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1] + 1e-9
        d = np.gradient(C, axis=0); d /= np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9
        L0, L1 = (length, length) if np.isscalar(length) else length
        r = self.rng
        for sd in side:
            for t in np.linspace(start, 1, n, endpoint=False) + r.uniform(0, (1 - start) / n, n):
                i = min(len(C) - 1, int(np.searchsorted(s, t)))
                L = (L0 + (L1 - L0) * t) * r.uniform(1 - jitter, 1 + jitter)
                a = np.radians(angle * r.uniform(0.85, 1.15)) * sd
                tx, ty = d[i]
                ux, uy = tx * np.cos(a) - ty * np.sin(a), tx * np.sin(a) + ty * np.cos(a)
                nx, ny = -uy * sd, ux * sd                              # bend back toward the curve's direction
                u = np.linspace(0, 1, 9)[:, None]
                P = C[i] + np.stack([ux, uy]) * L * u - np.stack([nx, ny]) * L * bend * u ** 2 * r.uniform(0.6, 1.4)
                self.snip(P, width * r.uniform(0.8, 1.2), tip)

    def scallop(self, pts, r=(8, 12), step=0.8, loose=False, outset=0.4):
        """a frizzed or curly edge: small overlapping discs along a curve (r in design units, step in radii,
        pushed `outset` radii to the left of travel so they bulge out of the shape they trim)"""
        C = _resample(np.asarray(pts, np.float64), 1.0, closed=False)
        d = np.gradient(C, axis=0); d /= np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9
        r0, r1 = (r, r) if np.isscalar(r) else r
        s, i = 0.0, 0
        seg = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
        while s < seg[-1]:
            i = min(len(C) - 1, int(np.searchsorted(seg, s)))
            rr = self.rng.uniform(r0, r1)
            n = np.array([d[i][1], -d[i][0]])
            c = C[i] + n * rr * outset
            self.disc(c[0], c[1], rr, loose)
            s += rr * step * self.rng.uniform(0.8, 1.2)

    def ringlet(self, x, y, length, width=16, turns=5, sway=6, lean=0.0):
        """a corkscrew curl hanging from (x, y): a wavy strip that swells at every turn and tapers to a point;
        returns its centreline (for bronzing)"""
        u = np.linspace(0, 1, 120)
        cx = x + sway * np.sin(2 * np.pi * turns * u) * (1 - 0.3 * u) + lean * length * u ** 2
        cy = y + length * u
        w = width * (0.72 + 0.28 * np.abs(np.cos(np.pi * turns * u))) * (1 - 0.55 * u) * np.clip(u / 0.06, 0.4, 1)
        w[-12:] *= np.linspace(1, 0.15, 12)
        C = np.stack([cx, cy], 1)
        self.snip(C, w, loose=True)
        return C

    def lace(self, pts, depth=7, step=6, holes=True):
        """a cut lace frill along a curve: a picot edge sticking out to the left of travel with a row of
        pierced holes just inside it"""
        C = _resample(np.asarray(pts, np.float64), 0.5, closed=False)
        d = np.gradient(C, axis=0); d /= np.hypot(d[:, 0], d[:, 1])[:, None] + 1e-9
        n = np.stack([d[:, 1], -d[:, 0]], 1)
        seg = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(C, axis=0).T))])
        ph = (seg / step) % 1.0
        out = depth * (0.35 + 0.65 * np.abs(np.sin(np.pi * ph)) ** 0.6)
        edge = C + n * out[:, None]
        inner = C - n * depth * 0.8
        self.shape(np.vstack([edge, inner[::-1]]), loose=True)
        if holes:
            for t in np.arange(step * 0.5, seg[-1], step):
                i = int(np.searchsorted(seg, t)); i = min(i, len(C) - 1)
                c = C[i] + n[i] * depth * 0.05
                tt = np.linspace(0, 2 * np.pi, 10, endpoint=False)
                hr = depth * 0.2
                self.hole(np.stack([c[0] + hr * np.cos(tt), c[1] + hr * np.sin(tt)], 1))

    # ---------------------------------------------------------------- after cutting
    def coverage(self):
        """(body, loose) coverage at 1x in the frame's local box"""
        b = np.asarray(self.body.reduce(self.ss), np.float32) / 255
        l = np.asarray(self.loose.reduce(self.ss), np.float32) / 255
        return b, l


class Silhouette:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.5, -0.65, 0.58)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.L = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.base = np.ones((H, W, 3), np.float32) * 0.8
        self.frames = []
        self.stages = []
        self.rail_y = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================ wall
    def wallpaper(self, ground='#7e96a1', ink='#ece2c8', tint=None, period=172, repeat=208, length=540, light=0.16):
        """block-printed striped wallpaper: a brushed distemper ground, a darker stripe band with a row of printed
        beads between two pinstripes, and a little sprig half-dropped between the bands. Lengths of paper are
        butted every `length` px; each length has its own small misregistration and pattern drop."""
        H, W = self.H, self.W
        g = _c(ground); ink = _c(ink); tint = _c(tint) if tint is not None else g * np.array([0.80, 0.83, 0.86], np.float32)
        r = self.rng
        mott = noise2d(H, W, 260, 4, self._seed()) - 0.5
        drag = np.asarray(Image.fromarray(r.random((H // 3, W // 90)).astype(np.float32)).resize((W, H), Image.BICUBIC), np.float32) - 0.5
        grain = _box3(r.random((H, W), dtype=np.float32)) - 0.5
        img = g[None, None, :] * (1 + 0.06 * mott + 0.025 * drag + 0.02 * grain)[..., None]

        SS = 2
        band = Image.new('L', (W * SS, H * SS), 0); cream = Image.new('L', (W * SS, H * SS), 0)
        seams = list(range(int(r.uniform(-length * 0.6, -length * 0.2)), W + length, length))
        P, V = period, repeat
        for x0 in seams:
            xa, xb = max(0, x0), min(W, x0 + length)
            if xb <= xa: continue
            # every length is its own strip of paper: print it on its own, then butt it against the last one
            bl, cl = Image.new('L', ((xb - xa) * SS, H * SS), 0), Image.new('L', ((xb - xa) * SS, H * SS), 0)
            db, dc = ImageDraw.Draw(bl), ImageDraw.Draw(cl)
            ox = -xa                                                     # canvas x -> this strip's x
            drop = r.uniform(-7, 7)                                      # the pattern match at the seam is off a little
            mis = r.normal(0, 1.1, 2)                                    # cream block vs band block registration
            img[:, xa:xb] *= 1 + r.uniform(-0.02, 0.02)
            for k in range(-1, W // P + 2):
                bx = k * P + P * 0.5
                if bx + P < xa or bx - P > xb: continue
                for j in range(-1, H // V + 2):                          # the block is printed one repeat at a time
                    y0, y1 = j * V + drop, (j + 1) * V + drop
                    wob = r.normal(0, 0.5)
                    db.rectangle([(bx - 15 + wob + ox) * SS, y0 * SS, (bx + 15 + wob + ox) * SS, y1 * SS + 1], fill=255)
                    cx = bx + mis[0] + r.normal(0, 0.3) + ox
                    for xx in (cx - 19.5, cx + 19.5):                    # pinstripes
                        dc.rectangle([(xx - 1.6) * SS, (y0 + mis[1]) * SS, (xx + 1.6) * SS, (y1 + mis[1]) * SS + 1], fill=255)
                    for q in range(8):                                   # beads down the middle of the band
                        yy = y0 + mis[1] + (q + 0.5) * V / 8
                        rr = 3.1 if q % 2 == 0 else 1.9
                        dc.ellipse([(cx - rr) * SS, (yy - rr) * SS, (cx + rr) * SS, (yy + rr) * SS], fill=255)
                    sx = bx + P * 0.5 + mis[0] + ox                      # sprig between bands, half-dropped
                    sy = j * V + drop + (V * 0.5 if k % 2 else 0) + mis[1]
                    self._sprig(dc, sx, sy, SS)
                    dc.ellipse([(sx - 0.9) * SS, (sy - V / 2 - 0.9) * SS, (sx + 0.9) * SS, (sy - V / 2 + 0.9) * SS], fill=255)   # pin dot
            band.paste(bl, (xa * SS, 0)); cream.paste(cl, (xa * SS, 0))
        mb = self._wander(np.asarray(band.reduce(SS), np.float32) / 255, 0.9)
        mc = self._wander(np.asarray(cream.reduce(SS), np.float32) / 255, 0.7)
        img = self._print(img, mb, tint, 0.86)
        img = self._print(img, mc, ink, 0.66)
        # seams: butt joins (a dark hairline and the lit edge of the next length) and the faint sheet joins
        for x0 in seams:
            if 1 <= x0 < W - 1:
                img[:, x0] *= 0.84; img[:, x0 + 1] *= 0.95; img[:, x0 - 1] *= 1.04
            for y in np.arange(r.uniform(150, 450), H, 540):
                y = int(y)
                xa, xb = max(0, x0), min(W, x0 + length)
                if 0 < y < H - 1 and xb > xa:
                    img[y, xa:xb] *= 0.965; img[y - 1, xa:xb] *= 1.02
        # daylight from the upper left
        yy, xx = np.arange(H, dtype=np.float32)[:, None] / H, np.arange(W, dtype=np.float32)[None, :] / W
        lit = 1 + light * (0.55 - 0.75 * xx - 0.45 * yy) - 0.06 * ((xx - 0.45) ** 2 + (yy - 0.4) ** 2)
        age = noise2d(H, W, 400, 3, self._seed())
        img = img * (1 - 0.05 * age[..., None]) + np.array([0.06, 0.045, 0.0], np.float32) * age[..., None]   # yellowed size
        self.base = np.clip(img * lit[..., None], 0, 1)

    def _wander(self, m, amp):
        """the block never comes down perfectly straight: shift every pixel sideways by a slow noise field"""
        H, W = m.shape
        dx = (noise2d(H, W, 70, 3, self._seed()) - 0.5) * 2 * amp
        xs = np.clip(np.arange(W, dtype=np.float32)[None, :] - dx, 0, W - 1.001)
        i0 = xs.astype(np.int32); fr = xs - i0
        rows = np.arange(H)[:, None]
        return m[rows, i0] * (1 - fr) + m[rows, i0 + 1] * fr

    def _sprig(self, d, x, y, SS):
        """a small block-printed sprig: a four-petal flower on a curved stem with two leaves"""
        for a in range(4):
            t = a * np.pi / 2 + np.pi / 4
            px, py = x + np.cos(t) * 4.2, y - 9 + np.sin(t) * 4.2
            d.ellipse([(px - 2.6) * SS, (py - 2.6) * SS, (px + 2.6) * SS, (py + 2.6) * SS], fill=255)
        stem = [(x + 0.8 * np.sin(u * 2.4), y - 4 + u * 16) for u in np.linspace(0, 1, 8)]
        d.line([(a * SS, b * SS) for a, b in stem], fill=255, width=int(1.6 * SS))
        for sgn, yy in ((-1, y + 4), (1, y + 8)):
            leaf = [(x, yy), (x + sgn * 4, yy - 3.5), (x + sgn * 8.5, yy - 2), (x + sgn * 4.5, yy + 1.2)]
            d.polygon([(a * SS, b * SS) for a, b in leaf], fill=255)

    def _print(self, img, m, col, opacity):
        """one block of distemper colour: uneven, dry specks, colour squeezed into a rim at the edges"""
        H, W = m.shape
        dens = 0.86 + 0.14 * noise2d(H, W, 30, 3, self._seed())
        dry = smoothstep(0.60, 0.80, _box3(self.rng.random((H, W), dtype=np.float32))) * 0.55
        rim = np.clip(m - _box3(m, 2), 0, 1) * 1.6
        a = np.clip(m * (dens - dry) * opacity + rim * 0.25 * m, 0, 1)
        return img * (1 - a[..., None]) + col[None, None, :] * a[..., None] * (0.97 + 0.06 * dens[..., None])

    def picture_rail(self, y=0, h=42, colour='#e7dfcd'):
        """painted picture rail along the top of the wall (the frames hang from hooks on it)"""
        self.rail_y = (y, y + h)
        self.base = self._moulding(self.base, y, h, _c(colour), [(0.0, 0.18, 'flat'), (0.18, 0.62, 'torus'), (0.62, 0.74, 'fillet'), (0.74, 1.0, 'cove')])

    def chair_rail(self, y, h=26, colour='#e7dfcd', dado='#d9cfb8'):
        """chair rail at height y with the painted dado below it"""
        H, W = self.H, self.W
        dd = _c(dado)
        y1 = int(y + h)
        if y1 < H:
            dn = (noise2d(H - y1, W, 180, 3, self._seed()) - 0.5) * 0.04
            panel = dd[None, None, :] * (1 + dn[..., None]) * (1 + 0.12 * (0.5 - np.arange(W, dtype=np.float32) / W))[None, :, None]
            self.base[y1:] = panel
        self.base = self._moulding(self.base, y, h, _c(colour), [(0.0, 0.25, 'cove'), (0.25, 0.8, 'torus'), (0.8, 1.0, 'fillet')])

    def _moulding(self, img, y0, h, col, parts):
        H, W = self.H, self.W
        y0i, y1i = int(round(y0)), int(round(y0 + h))
        v = (np.arange(y0i, y1i, dtype=np.float32) + 0.5 - y0) / h
        hh = np.zeros_like(v)
        for a, b, kind in parts:
            m = (v >= a) & (v < b)
            u = (v[m] - a) / (b - a)
            if kind == 'torus': hh[m] = 0.5 + 0.5 * np.sqrt(np.clip(1 - (2 * u - 1) ** 2, 0, 1))
            elif kind == 'cove': hh[m] = 0.25 + 0.25 * (1 - np.sqrt(np.clip(1 - (1 - u) ** 2, 0, 1)))
            elif kind == 'fillet': hh[m] = 0.45
            else: hh[m] = 0.3
        gy = np.gradient(hh * h * 0.6)
        n = np.stack([np.zeros_like(gy), -gy, np.ones_like(gy)], 1); n /= np.linalg.norm(n, axis=1, keepdims=True)
        shade = 0.62 + 0.5 * np.clip(n @ self.L, 0, 1) + 0.04 * hh
        grain = 1 + 0.02 * (noise2d(y1i - y0i, W, 40, 2, self._seed()) - 0.5)
        strip = col[None, None, :] * (shade[:, None, None] * grain[..., None]) * (1 + 0.06 * (0.5 - np.arange(W) / W))[None, :, None]
        img[y0i:y1i] = np.clip(strip, 0, 1)
        m = np.zeros((H, 1), np.float32); m[y0i:y1i] = 1                 # the shadow only depends on y
        sh = blur(np.repeat(shift(m, 0, 7), 4, 1), 5)[:, :1] * (1 - m) * 0.42 + blur(np.repeat(shift(m, 0, 2), 4, 1), 1.2)[:, :1] * (1 - m) * 0.25
        img *= (1 - np.clip(sh, 0, 0.6))[:, :, None]
        return img

    # ================================================================ frame
    def frame(self, cx, cy, rx, ry, width=56, pearls=True, twist=0.0, eglomise=True, card='#efe5cd',
              hook=False, cord='#7a2e2a', spread=34):
        """an oval gilt frame round an opening of radii (rx, ry); returns a Frame. With hook=True it hangs from
        the picture rail on a silk cord whose V meets the frame `spread` degrees either side of the top."""
        f = Frame()
        f.cx, f.cy, f.rx, f.ry, f.width = cx, cy, rx, ry, width
        f.x0, f.y0 = int(np.floor(cx - rx - 2)), int(np.floor(cy - ry - 2))
        f.x1, f.y1 = int(np.ceil(cx + rx + 2)), int(np.ceil(cy + ry + 2))
        f.w, f.h = f.x1 - f.x0, f.y1 - f.y0
        f.glazed = False
        # drop shadows of the whole frame on the wall (computed in a padded box round it)
        pad = width + 70
        bx0, by0 = max(0, int(cx - rx - pad)), max(0, int(cy - ry - pad))
        bx1, by1 = min(self.W, int(cx + rx + pad)), min(self.H, int(cy + ry + pad))
        yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32) + 0.5
        outer = np.clip(width - self._edist(xx - cx, yy - cy, rx, ry) + 0.5, 0, 1)
        sh = 0.42 * blur(shift(outer, 12, 17), 13) + 0.38 * blur(shift(outer, 2, 3), 2.2)
        self.base[by0:by1, bx0:bx1] *= (1 - np.clip(sh, 0, 0.75) * (1 - outer))[..., None]
        del yy, xx, outer, sh
        if hook and self.rail_y is not None:
            self._hang(f, cord, spread)
        self._gild(f, pearls, twist)
        self._card(f, _c(card), eglomise)
        self.frames.append(f)
        return f

    @staticmethod
    def _edist(x, y, rx, ry):
        """approximate signed distance (px) outside the ellipse x^2/rx^2 + y^2/ry^2 = 1"""
        rho = np.sqrt((x / rx) ** 2 + (y / ry) ** 2) + 1e-6
        g = np.sqrt((x / rx ** 2) ** 2 + (y / ry ** 2) ** 2) / rho + 1e-9
        return (rho - 1) / g

    @staticmethod
    def _arclen(theta, a, b):
        """arc length along the ellipse (a cos t, b sin t) at parameter theta, and the perimeter"""
        t = np.linspace(-np.pi, np.pi, 4097)
        sp = np.sqrt((a * np.sin(t)) ** 2 + (b * np.cos(t)) ** 2)
        s = np.concatenate([[0], np.cumsum((sp[1:] + sp[:-1]) / 2 * np.diff(t))])
        return np.interp(theta, t, s), s[-1]

    def _gild(self, f, pearls, twist, band=192, margin=24):
        """render the gilt moulding at 2x in horizontal bands (with overlap for the gradients and blurs),
        so a big frame never holds more than a band's worth of float arrays"""
        w, SS = f.width, 2
        X0c, Y0c = max(0, int(f.cx - f.rx - w - 3)), max(0, int(f.cy - f.ry - w - 3))
        X1c, Y1c = min(self.W, int(f.cx + f.rx + w + 4)), min(self.H, int(f.cy + f.ry + w + 4))
        H2, W2 = (Y1c - Y0c) * SS, (X1c - X0c) * SS
        n_bole = noise2d(H2, W2, 5 * SS, 3, self._seed())
        n_grime = noise2d(H2, W2, 10 * SS, 2, self._seed())
        xs = (np.arange(X0c * SS, X1c * SS, dtype=np.float32) + 0.5) / SS - f.cx
        for r0 in range(0, H2, band):
            r1 = min(H2, r0 + band)
            a0, a1 = max(0, r0 - margin), min(H2, r1 + margin)
            ys = (np.arange(Y0c * SS + a0, Y0c * SS + a1, dtype=np.float32) + 0.5) / SS - f.cy
            rgb, alpha = self._gilt_band(f, xs, ys, pearls, twist, n_bole[a0:a1], n_grime[a0:a1])
            k0, k1 = r0 - a0, r1 - a0
            pre = np.concatenate([rgb[k0:k1] * alpha[k0:k1, :, None], alpha[k0:k1, :, None]], -1)
            pre = pre.reshape((r1 - r0) // SS, SS, W2 // SS, SS, 4).mean(axis=(1, 3))
            a1_ = pre[..., 3:4]
            out = np.clip(pre[..., :3] / np.maximum(a1_, 1e-6), 0, 1)
            ya, yb = Y0c + r0 // SS, Y0c + r1 // SS
            reg = self.base[ya:yb, X0c:X1c]
            self.base[ya:yb, X0c:X1c] = reg * (1 - a1_) + out * a1_

    def _gilt_band(self, f, xs, ys, pearls, twist, n_bole, n_grime):
        """height field of the moulding profile on one band of 2x pixels, then the gold shading"""
        w, SS = f.width, 2
        x, y = np.meshgrid(xs, ys)
        d = self._edist(x, y, f.rx, f.ry)
        t = d / w
        theta = np.arctan2(y / f.ry, x / f.rx)
        h = np.zeros_like(t)
        def seg(a, b): return (t >= a) & (t < b)
        m = t < 0.07; u = (np.clip(t, 0, 0.07) - 0.035) / 0.035
        h = np.where(m, 0.10 + 0.05 * np.sqrt(np.clip(1 - u ** 2, 0, 1)), h)               # sight-edge bead
        m = seg(0.07, 0.25); u = (t - 0.07) / 0.18
        h = np.where(m, 0.10 + 0.16 * u ** 2, h)                                             # cove
        m = seg(0.25, 0.40); h = np.where(m, 0.26, h)                                        # pearl bed
        m = seg(0.40, 0.84); u = (t - 0.62) / 0.22
        tor = 0.26 + 0.30 * np.sqrt(np.clip(1 - u ** 2, 0, 1))                              # big torus
        if twist:                                                                            # ribbon twist
            s_t, P = self._arclen(theta, f.rx + 0.62 * w, f.ry + 0.62 * w)
            n_rib = max(12, int(round(P / (0.30 * w))))
            ph = (s_t / P * n_rib).astype(np.float32) + u * 0.9
            tor = tor - twist * 0.05 * (0.5 - 0.5 * np.cos(2 * np.pi * ph)) * np.sqrt(np.clip(1 - u ** 2, 0, 1))
            del s_t, ph
        h = np.where(m, tor, h); del tor
        m = seg(0.84, 0.90); h = np.where(m, 0.30, h)                                        # fillet
        m = seg(0.90, 1.0); u = (t - 0.90) / 0.10
        h = np.where(m, 0.06 + 0.24 * np.sqrt(np.clip(1 - u ** 2, 0, 1)), h)               # outer roll
        h = (h * w).astype(np.float32)
        del m, u, t
        if pearls:
            db = 0.325 * w; rb = 0.068 * w
            s_b, P = self._arclen(theta, f.rx + db, f.ry + db)
            n = max(24, int(round(P / (2.2 * rb))))
            sp = P / n
            k = np.round(s_b / sp)
            a = (s_b - k * sp).astype(np.float32)
            jit = (1 + 0.05 * np.sin(k * 12.9898) * np.cos(k * 4.1414)).astype(np.float32)
            del s_b, k
            c = d - db
            hb = 0.26 * w + 0.92 * np.sqrt(np.clip((rb * jit) ** 2 - a ** 2 - c ** 2, 0, None))
            h = np.maximum(h, np.where(np.abs(c) < rb * 1.2, hb, 0)).astype(np.float32)
            del a, jit, c, hb
        del theta
        alpha = ((d > -1.2) & (d < w)).astype(np.float32)
        del d
        h = np.where(alpha > 0, h, 0).astype(np.float32)
        # ---- shading: gold mirrors a room lit by one window at the upper left
        gy, gx = np.gradient(h)
        gx *= SS; gy *= SS
        nz = 1 / np.sqrt(1 + gx * gx + gy * gy); nx, ny = -gx * nz, -gy * nz
        del gx, gy
        Lw = self.L
        rl = 2 * nz * nx * Lw[0] + 2 * nz * ny * Lw[1] + (2 * nz * nz - 1) * Lw[2]
        room = 0.16 + 0.30 * np.clip(0.5 - 1.2 * nz * ny, 0, 1) + 0.10 * (2 * nz * nz - 1)
        v = room + 0.50 * np.exp((rl - 1) / 0.35) + 0.85 * np.exp((rl - 1) / 0.03)
        del nx, ny, nz, rl, room
        ao = np.clip((blur(h, 3.0 * SS) - h) / (0.07 * w), 0, 1)
        v = v * (1 - 0.55 * ao)
        # gold leaf laid in squares: faint tone steps and overlap lines
        lx, ly = (x + 1000.3) / 26.0, (y + 1000.7) / 26.0
        cell = np.floor(lx) * 7.13 + np.floor(ly) * 3.71
        v = v * (1 + 0.035 * np.sin(cell * 12.9898)) * (1 - 0.05 * ((np.abs(lx - np.round(lx)) < 0.025) | (np.abs(ly - np.round(ly)) < 0.025)))
        del lx, ly, cell, x, y
        ramp_v = np.array([0.0, 0.30, 0.62, 1.0, 1.5], np.float32)
        ramp_c = np.array([[0.12, 0.07, 0.025], [0.48, 0.31, 0.10], [0.80, 0.60, 0.26], [0.99, 0.86, 0.55], [1.0, 0.97, 0.84]], np.float32)
        col = np.stack([np.interp(v, ramp_v, ramp_c[:, i]).astype(np.float32) for i in range(3)], -1)
        # rubbed through to red bole on the crests; grime in the hollows
        crest = np.clip((h - blur(h, 2.0 * SS)) / (0.02 * w), 0, 1)
        bole = (crest * smoothstep(0.66, 0.80, n_bole) * 0.6)[..., None]
        col = col * (1 - bole) + np.array([0.50, 0.20, 0.10], np.float32) * np.clip(0.4 + 0.8 * v, 0, 1.3)[..., None] * bole
        grime = (ao * smoothstep(0.3, 0.7, n_grime) * 0.45)[..., None]
        col = col * (1 - grime) + np.array([0.16, 0.11, 0.06], np.float32) * grime
        return col, alpha

    def _tube(self, pts, width, col, twist=7.0, shadow=0.32, sh_off=(6, 9), spec=0.35):
        """a round cord / wire along a polyline: lit cylinder, twist stripes, soft shadow on the wall"""
        P = _resample(np.asarray(pts, np.float64), 2.0, closed=False)
        r = width / 2
        x0, y0 = int(max(0, P[:, 0].min() - width - 30)), int(max(0, P[:, 1].min() - width - 30))
        x1, y1 = int(min(self.W, P[:, 0].max() + width + 30)), int(min(self.H, P[:, 1].max() + width + 30))
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
        best = np.full(yy.shape, 1e9, np.float32); along = np.zeros_like(best); acr = np.zeros_like(best)
        px_ = np.zeros_like(best); py_ = np.zeros_like(best)
        s0 = 0.0
        for a, b in zip(P[:-1], P[1:]):
            ab = b - a; L2 = float(ab @ ab) + 1e-9; L = np.sqrt(L2)
            tt = np.clip(((xx - a[0]) * ab[0] + (yy - a[1]) * ab[1]) / L2, 0, 1)
            dx, dy = xx - (a[0] + tt * ab[0]), yy - (a[1] + tt * ab[1])
            dist = np.sqrt(dx * dx + dy * dy)
            upd = dist < best
            sgn = np.sign(ab[0] * dy - ab[1] * dx)
            best = np.where(upd, dist, best); along = np.where(upd, s0 + tt * L, along); acr = np.where(upd, sgn * dist, acr)
            px_ = np.where(upd, -ab[1] / L, px_); py_ = np.where(upd, ab[0] / L, py_)
            s0 += L
        cov = np.clip(r - best + 0.5, 0, 1)
        u = np.clip(acr / r, -1, 1)
        nz = np.sqrt(np.clip(1 - u * u, 0, 1))
        nx, ny = px_ * u, py_ * u
        diff = np.clip(nx * self.L[0] + ny * self.L[1] + nz * self.L[2], 0, 1)
        stripes = np.sin(2 * np.pi * (along + u * r * 1.6) / twist)
        sh = 0.40 + 0.75 * diff + 0.10 * stripes * nz
        spc = spec * np.clip(diff, 0, 1) ** 14
        c = _c(col)
        rgb = np.clip(c[None, None, :] * sh[..., None] + spc[..., None], 0, 1)
        reg = self.base[y0:y1, x0:x1]
        shd = blur(shift(cov, *sh_off), 3.5) * shadow * (1 - cov)
        reg = reg * (1 - shd[..., None])
        self.base[y0:y1, x0:x1] = reg * (1 - cov[..., None]) + rgb * cov[..., None]

    def _hang(self, f, cord, spread):
        top, bot = self.rail_y
        hx = f.cx
        # brass hook over the rail and a ring below it
        self._tube([(hx, top + 3), (hx, bot - 2), (hx + 0.5, bot + 6)], 6, '#b08a3e', twist=1e9, shadow=0.38, sh_off=(3, 4), spec=0.7)
        t = np.linspace(0, 2 * np.pi, 60)
        ring = np.stack([hx + 7.5 * np.sin(t), bot + 13 - 7.5 * np.cos(t)], 1)
        self._tube(ring, 3.2, '#b08a3e', twist=1e9, shadow=0.38, sh_off=(4, 5), spec=0.7)
        a = np.radians(spread)
        ow = f.width * 0.55
        for sgn in (-1, 1):
            ex = f.cx + sgn * (f.rx + ow) * np.sin(a)
            ey = f.cy - (f.ry + ow) * np.cos(a)
            sx, sy = hx + sgn * 3, bot + 20
            pts = [(sx + (ex - sx) * q, sy + (ey - sy) * q + 3 * np.sin(np.pi * q)) for q in np.linspace(0, 1, 16)]
            self._tube(pts, 4.6, cord, twist=6.5)
        # the knot where the two cords leave the ring
        self._tube([(hx - 3, bot + 19), (hx + 3, bot + 19)], 6.5, cord, twist=4)

    def _card(self, f, col, eglomise):
        yy, xx = np.mgrid[f.y0:f.y1, f.x0:f.x1].astype(np.float32) + 0.5
        d = self._edist(xx - f.cx, yy - f.cy, f.rx, f.ry)
        f.inside = np.clip(-d + 0.5, 0, 1)
        H, W = d.shape
        rho = np.clip(1 + d / max(f.rx, f.ry), 0, 1.2)
        tone = 1 - 0.10 * smoothstep(0.55, 1.0, rho) - 0.02 * (noise2d(H, W, 60, 3, self._seed()) - 0.5)
        card = col[None, None, :] * tone[..., None]
        card = card * (1 - np.array([0.0, 0.02, 0.06], np.float32) * smoothstep(0.6, 1.0, rho)[..., None])
        card *= (1 + 0.012 * (noise2d(H, W, 1.8, 2, self._seed()) - 0.5))[..., None]
        r = self.rng
        fox = np.zeros((H, W), np.float32)
        for _ in range(int(r.integers(6, 12))):
            cx, cy = r.uniform(0.1, 0.9) * W, r.uniform(0.1, 0.9) * H
            rr = r.uniform(0.8, 3.2)
            fox += np.exp(-((xx - f.x0 - cx) ** 2 + (yy - f.y0 - cy) ** 2) / (2 * rr * rr)) * r.uniform(0.25, 0.6)
        for _ in range(3):
            cx, cy = r.uniform(0.15, 0.85) * W, r.uniform(0.15, 0.85) * H
            rr = r.uniform(8, 20)
            fox += np.exp(-((xx - f.x0 - cx) ** 2 + (yy - f.y0 - cy) ** 2) / (2 * rr * rr)) * 0.06
        fox = np.clip(fox, 0, 0.7)
        card = card * (1 - fox[..., None]) + np.array([0.62, 0.42, 0.25], np.float32) * col * fox[..., None]
        f.card = card.astype(np.float32)
        f.paper = np.zeros((H, W), np.float32)                       # where black paper is (for bronze)
        # verre eglomise: black band with a gold fillet, painted on the back of the glass
        f.eg_a = np.zeros((H, W), np.float32); f.eg_rgb = np.zeros((H, W, 3), np.float32)
        if eglomise:
            bw = max(10, 0.065 * min(f.rx, f.ry))
            band = np.clip(d + bw + 0.5, 0, 1)
            fil = np.clip(1.1 - np.abs(d + bw - 3.6), 0, 1)
            sheen = 0.03 + 0.03 * np.clip(-(xx - f.cx) / f.rx - (yy - f.cy) / f.ry, 0, 1)
            gold = np.array([0.80, 0.62, 0.30], np.float32) * (0.85 + 0.25 * noise2d(H, W, 12, 2, self._seed()))[..., None]
            f.eg_rgb = np.ones((H, W, 3), np.float32) * sheen[..., None] * np.array([1.0, 0.95, 0.9], np.float32)
            f.eg_rgb = f.eg_rgb * (1 - fil[..., None]) + gold * fil[..., None]
            f.eg_a = np.maximum(band * 0.97, fil)
        # shadow of the frame's rebate on the card (light from the upper left)
        out = 1 - f.inside
        f.lip = 0.38 * blur(shift(out, 5, 7), 4.5) * f.inside + 0.25 * blur(shift(out, 1, 2), 1.2) * f.inside
        # convex glass: soft sheen and a crisp window reflection (shown after glaze())
        u, v = (xx - f.cx) / f.rx, (yy - f.cy) / f.ry
        rr = np.sqrt(u * u + v * v)
        ang = np.degrees(np.arctan2(v, u))
        soft = 0.10 * np.exp(-((u + 0.38) ** 2 + (v + 0.45) ** 2) / (2 * 0.32 ** 2))
        pane = ((rr > 0.70) & (rr < 0.84) & (((ang > -158) & (ang < -134)) | ((ang > -130) & (ang < -112)))).astype(np.float32)
        pane = blur(pane, 1.0) * (0.75 + 0.25 * np.clip((0.84 - rr) / 0.14, 0, 1))
        streak = 0.05 * np.exp(-((u * 0.7 + v * 0.7 + 0.15) ** 2) / (2 * 0.05 ** 2)) * np.clip(1 - rr, 0, 1)
        f.glare = np.clip(1.2 * soft + 0.16 * blur(pane, 1.2) + streak, 0, 0.5)

    # ================================================================ paper, gold, ink
    def sheet(self, f, at, scale=1.0, flip=False, ss=4, warp=None):
        """a fresh sheet of black paper over frame f's card. Design unit (0, 0) lands on canvas pixel `at`.
        warp: optional function (N x 2 design points -> N x 2) applied to everything cut or painted on this sheet,
        to re-proportion a drawing (a bigger head, a shorter body) without retyping its coordinates."""
        return Sheet(self, f, at, scale, flip, ss, warp=warp)

    def paste(self, sh, black='#0f0d0c'):
        """glue a cut sheet onto its card: hairline shadow under the glued body, a longer one under loose snips,
        black with a faint fibre and sheen, a lit hairline on edges facing the light"""
        f = sh.f
        b, l = sh.coverage()
        P = np.clip(np.maximum(b, l), 0, 1)
        H, W = P.shape
        card = f.card
        sh_b = 0.30 * blur(shift(b, 1, 1), 0.8) + 0.06 * blur(shift(b, 3, 4), 3)
        sh_l = 0.42 * blur(shift(l, 2, 3), 1.3)
        card = card * (1 - np.clip(sh_b + sh_l, 0, 0.7) * (1 - P))[..., None]
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        fib = noise2d(H, W, 3.0, 2, self._seed()) - 0.5
        sheen = 0.6 + 0.4 * np.clip(1 - ((xx / W - 0.3) ** 2 + (yy / H - 0.25) ** 2) * 2, 0, 1)
        blk = _c(black)[None, None, :] * (1 + 0.18 * fib[..., None]) * (0.85 + 0.3 * sheen[..., None])
        gy, gx = np.gradient(blur(P, 0.6))
        lit = np.clip(-(gx * self.L[0] + gy * self.L[1]) * 1.6, 0, 1) * 0.16
        blk = blk + lit[..., None]
        f.card = card * (1 - P[..., None]) + blk * P[..., None]
        f.paper = np.maximum(f.paper, P)
        sh.mask = P

    def bronze(self, sh, strokes, width=2.0, tip=0.0, bright=1.0, colour='#c9a058'):
        """thin shell gold painted over the black paper of sheet `sh`. strokes: list of polylines in design units
        (spline them first); each tapers from `width` (design units) to `tip` and gets its own brightness."""
        f = sh.f
        SS = sh.ss
        cov = Image.new('L', (f.w * SS, f.h * SS), 0); val = Image.new('L', (f.w * SS, f.h * SS), 0)
        dc, dv = ImageDraw.Draw(cov), ImageDraw.Draw(val)
        r = self.rng
        for pts in strokes:
            P = sh._ss(pts)
            if len(P) < 2: continue
            C = _resample(P, max(1.0, SS * 0.75), closed=False)
            n = len(C)
            u = np.linspace(0, 1, n)
            wmax = width * sh.k * SS * r.uniform(0.8, 1.15)
            w = wmax * np.clip(np.minimum(u / 0.18, 1), 0.25, 1) * (1 - (1 - tip / max(width, 1e-6)) * smoothstep(0.55, 1.0, u))
            w = np.maximum(w, 0.8)
            poly = _strip(C, w, None)
            b = int(np.clip(255 * 0.62 * bright * r.uniform(0.7, 1.15), 0, 255))
            dc.polygon([tuple(p) for p in poly], fill=255); dv.polygon([tuple(p) for p in poly], fill=b)
        a = np.asarray(cov.reduce(SS), np.float32) / 255
        vv = np.asarray(val.reduce(SS), np.float32) / 255 / np.maximum(a, 1e-3) / 0.62
        H, W = a.shape
        grain = noise2d(H, W, 1.5, 2, self._seed())
        gold = _c(colour)[None, None, :] * (vv * (0.85 + 0.3 * grain))[..., None]
        gold = gold + np.array([0.10, 0.08, 0.04], np.float32) * smoothstep(0.75, 1.0, grain)[..., None] * vv[..., None]
        a = a * f.paper * 0.95
        f.card = f.card * (1 - a[..., None]) + np.clip(gold, 0, 1) * a[..., None]

    def caption(self, f, text, x, y, size, style='roundhand', colour='#2f1f14', alpha=0.92, spacing=0.0):
        """handwritten caption in iron-gall ink on frame f's card, centred on (x, y) baseline"""
        SS = 2
        font = sil_font(style, size * SS)
        m = text_mask(f.h * SS, f.w * SS, text, font, ((x - f.x0) * SS, (y - f.y0) * SS), anchor='ms', spacing=spacing * SS)
        m = m.reshape(f.h, SS, f.w, SS).mean(axis=(1, 3))
        self._ink(f, m, colour, alpha)

    def pen(self, f, pts, width=1.2, colour='#3a2618', alpha=0.8):
        """a pen line in ink on the card (ground line, flourish); canvas pixels"""
        SS = 4
        im = Image.new('L', (f.w * SS, f.h * SS), 0)
        P = np.asarray(pts, np.float64)
        C = _resample(np.stack([(P[:, 0] - f.x0) * SS, (P[:, 1] - f.y0) * SS], 1), SS * 0.75, closed=False)
        u = np.linspace(0, 1, len(C))
        w = width * SS * (0.35 + 0.65 * np.sin(np.pi * u) ** 0.6)
        ImageDraw.Draw(im).polygon([tuple(p) for p in _strip(C, w, None)], fill=255)
        self._ink(f, np.asarray(im.reduce(SS), np.float32) / 255, colour, alpha)

    def _ink(self, f, m, colour, alpha):
        H, W = m.shape
        dens = 0.8 + 0.2 * noise2d(H, W, 6, 2, self._seed())
        a = np.clip(m * dens * alpha, 0, 1) * (1 - f.paper)
        f.card = f.card * (1 - a[..., None]) + _c(colour)[None, None, :] * f.card * 0.25 * a[..., None] + _c(colour)[None, None, :] * 0.75 * a[..., None]

    def glaze(self, frames=None):
        """put the glass in: soft sheen and window reflection on the convex glass"""
        for f in (frames or self.frames): f.glazed = True

    # ================================================================ output
    def composite(self):
        img = self.base.copy()
        for f in self.frames:
            loc = f.card * (1 - f.eg_a[..., None]) + f.eg_rgb * f.eg_a[..., None]
            loc = loc * (1 - f.lip[..., None])
            if f.glazed:
                loc = 1 - (1 - loc) * (1 - f.glare[..., None] * np.array([0.96, 0.98, 1.0], np.float32))
            a = f.inside[..., None]
            ya, yb, xa, xb = max(0, f.y0), min(self.H, f.y1), max(0, f.x0), min(self.W, f.x1)
            sub = (slice(ya - f.y0, yb - f.y0), slice(xa - f.x0, xb - f.x0))
            img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - a[sub]) + loc[sub] * a[sub]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=88, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
