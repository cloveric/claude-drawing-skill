"""perler — fuse beads (Perler / Hama / Artkal): little plastic tubes pushed one by one onto a pegboard to make a
pixel picture, then ironed so they melt together into one piece. Photographed from just above a craft table
(numpy + Pillow only).

Model: the table top is a *height field* (every object is solid geometry measured in output pixels) seen by a
camera that looks almost straight down but leans back a little, so the side of anything tall shows as a sliver
under its top. Nothing is painted as a picture of a bead; every bead is a tube and the light does the rest.
  camera     oblique projection: a point (x, y, z) lands on screen at (x, y - tilt * z). Each screen pixel walks
             its column of the height field from the front and takes the first surface it hits, so near beads hide
             far ones, the gap between two beads shows a sliver of the far bead's side wall, and holes show their
             inside walls (a reverse running minimum + one searchsorted per column; no draw order involved).
  bead       a short tube: outer radius 0.47 pitch, hole radius 0.235, height 0.88, with rounded top edges. On a
             pegboard the peg stands inside the hole, so looking down the hole you see the peg tip in the dark,
             tinted by light that came through the bead wall. Each bead sits a little off-centre on its peg, is a
             hair taller or shorter, and has its own shade of the colour (dye lots are never identical).
  plastics   opaque (glossy, translucent enough that shadows are coloured), pearl (iridescent sheen), clear (you
             see the board through it; edges refract dark), glow (milky pale green).
  pegboard   a translucent plastic plate (square, circle or hexagon outline; the pegs always stand on a square
             lattice) with a peg at every lattice point inside it; the table shows through it faintly. Empty pegs
             stay visible wherever no bead has been placed yet.
  ironing    `melt` 0..1 per bead: the tube slumps (lower), spreads (wider), its hole closes from the rim, the
             edges roll over and neighbours flow together (a smooth union of their outlines that grows with
             melt), so the dark gaps shrink to little diamonds and then close, and the joined top turns into a
             flat, pillowy, waxy sheet with the grain of the ironing paper pressed into it. `iron(board, 0.4)` is
             the classic half-melt (holes still open, beads stuck together); 0.8 is a flat, smooth piece.
  paper      pattern charts, ironing paper and tape are thin sheets. Ironing paper drapes over the beads (a max
             filter + blur of what is under it), is translucent, and can be peeled back with a curled edge.
  light      one big soft box up and to the left: a local point light (so a flat piece gets a sheen that drifts
             across it), a directional march through the height field for soft cast shadows, and the box itself
             seen in reflection -- every surface whose mirror direction points into it shows a bright patch, which
             on a glossy tube is a crisp arc on the upper-left shoulder of the rim and on the far lip of the hole,
             and on melted (rougher) plastic spreads into a broad waxy sheen. Sky light with ambient occlusion from
             the height field, a little Fresnel on edges, coloured light through translucent plastic in the shade;
             shaded in linear light with a soft highlight shoulder, rendered at `ss` x supersampling.
  props      a sorting tray with a heap of beads in every compartment, spilled beads standing on end or lying on
             their side, tweezers held above the board with a bead in their tips (drawn as a lifted layer that
             casts its own shadow), masking tape labels.

    from perler import Perler
    p = Perler(1920, 1080, seed=1, pitch=22)
    p.desk('#d8c3a0')
    b = p.pegboard(960, 540, 29, colour='clear')                                # 29 x 29 square board
    p.place(b, ['.RR.', 'RRRR', '.RR.'], {'R': 'red'}, at=(10, 10))             # beads from a text pattern
    p.stage('placed')
    p.iron(b, 0.7)                                                              # fuse them
    p.lift_off(b)                                                               # piece off the board
    p.save('out.jpg')
Coordinates are output pixels, y down; angles in degrees, counter-clockwise; heights in output pixels.
"""
import copy
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep, load_font, height_shadow, ambient_occlusion

# ---------------------------------------------------------------- colours
BEADS = {
    'red': '#d3272f', 'dark_red': '#8c1726', 'pink': '#f6a0ae', 'yellow': '#f7c62b', 'orange': '#f27a24',
    'green': '#3a9d48', 'dark_green': '#1c6334', 'light_green': '#9ccc54', 'sky': '#7cc3e8', 'blue': '#2f63b5',
    'purple': '#8759b8', 'brown': '#7b4a2c', 'tan': '#d9a86c', 'cream': '#f2e3bd', 'white': '#f5f4f0',
    'grey': '#a3a6ab', 'black': '#26242b', 'pearl': '#efe9e3', 'clear': '#e4edf0', 'glow': '#e0f1c6',
}
_KIND = {'pearl': 1, 'clear': 2, 'glow': 3}           # every other colour is opaque plastic
DESK, PLASTIC, BOARD, PAPER, METAL, PEARL, CLEAR = range(7)

BEAD_R, BEAD_RH, BEAD_H, BEAD_C = 0.47, 0.235, 0.88, 0.10      # outer radius, hole radius, height, edge round (x pitch)
PEG_R, PEG_H, PLATE_T = 0.17, 0.50, 0.34                        # peg radius, peg height, plate thickness (x pitch)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    if isinstance(c, str): return hexc(BEADS.get(c, c))
    return np.asarray(c, np.float32)


def _lin(c):
    return np.power(np.clip(c, 0, 1), 2.2).astype(np.float32)


def _shoulder(e, h, c, aa):
    """height of a flat-topped wall at distance e inside its edge: a vertical side, top corner rounded with radius c"""
    c = np.maximum(c, 1e-3)
    ec = np.clip(e, 0, c)
    top = h - c + np.sqrt(np.maximum(c * c - (c - ec) ** 2, 0))
    return np.maximum(top, 0) * np.clip(e / aa + 0.5, 0, 1)


def _smin(a, b, k):
    """polynomial smooth minimum: outlines closer than k flow into each other"""
    k = np.maximum(k, 1e-4)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def _maxf(a, r):
    """box max filter (radius r px) via shifted maxima"""
    r = int(r)
    if r < 1: return a
    o = a.copy()
    for d in range(1, r + 1):
        o[:, d:] = np.maximum(o[:, d:], a[:, :-d]); o[:, :-d] = np.maximum(o[:, :-d], a[:, d:])
    a = o; o = a.copy()
    for d in range(1, r + 1):
        o[d:] = np.maximum(o[d:], a[:-d]); o[:-d] = np.maximum(o[:-d], a[d:])
    return o


def _blur3(a, sigma):
    """core.blur on each channel of an (h, w, 3) array"""
    return np.stack([blur(a[..., i], sigma) for i in range(a.shape[-1])], -1)


def _font(style, size):
    return load_font(style, max(6, int(round(size))))


# ---------------------------------------------------------------- the canvas that objects are rasterised into
class _Canvas:
    """height field + material maps at `S` x supersampling. z is in output px; x, y indices are internal px."""

    def __init__(self, W, H, S, tilt, zmax):
        self.S, self.k = S, tilt
        self.W, self.H = W * S, H * S
        self.Hm = self.H + int(np.ceil(tilt * zmax * S)) + 4 * S       # world rows below the frame still show up
        Hm, Wm = self.Hm, self.W
        self.z = np.zeros((Hm, Wm), np.float32)
        self.alb = np.zeros((Hm, Wm, 3), np.float32)                     # linear albedo
        self.spec = np.zeros((Hm, Wm), np.float32)
        self.rough = np.ones((Hm, Wm), np.float32)
        self.trans = np.zeros((Hm, Wm), np.float32)                      # how much light the stuff lets through
        self.mat = np.zeros((Hm, Wm), np.uint8)
        self.over = []                                                   # lifted layers (tweezers)

    def win(self, x0, y0, x1, y1):
        """window in output px -> (slices, X, Y) with X, Y the pixel centres in output px"""
        S = self.S
        a0, a1 = max(0, int(np.floor(x0 * S))), min(self.W, int(np.ceil(x1 * S)))
        b0, b1 = max(0, int(np.floor(y0 * S))), min(self.Hm, int(np.ceil(y1 * S)))
        if a1 <= a0 or b1 <= b0: return None
        X = ((np.arange(a0, a1, dtype=np.float32) + 0.5) / S)[None, :]
        Y = ((np.arange(b0, b1, dtype=np.float32) + 0.5) / S)[:, None]
        return (slice(b0, b1), slice(a0, a1)), X, Y

    def put(self, sl, znew, alb, spec, rough, mat, trans=0.0):
        """lay a surface down wherever it rises above what is already there (soft over ~0.7 internal px)"""
        zo = self.z[sl]
        a = np.clip((znew - zo) * self.S / 0.7, 0, 1)
        self.z[sl] = np.maximum(zo, znew)
        a3 = a[..., None]
        self.alb[sl] = self.alb[sl] * (1 - a3) + np.asarray(alb, np.float32) * a3
        self.spec[sl] = self.spec[sl] * (1 - a) + spec * a
        self.rough[sl] = self.rough[sl] * (1 - a) + rough * a
        self.trans[sl] = self.trans[sl] * (1 - a) + trans * a
        self.mat[sl] = np.where(a > 0.5, mat, self.mat[sl]).astype(np.uint8)
        return a

    def paste(self, im, cx, cy, angle):
        """rotate an RGBA image about its centre and place it at (cx, cy) output px -> (slices, rgba array) or None"""
        if angle: im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
        w, h = im.size
        x0, y0 = int(round(cx * self.S - w / 2)), int(round(cy * self.S - h / 2))
        a0, b0 = max(0, x0), max(0, y0)
        a1, b1 = min(self.W, x0 + w), min(self.Hm, y0 + h)
        if a1 <= a0 or b1 <= b0: return None
        arr = np.asarray(im, np.float32)[b0 - y0:b1 - y0, a0 - x0:a1 - x0] / 255
        return (slice(b0, b1), slice(a0, a1)), arr


# ---------------------------------------------------------------- beads on a lattice (the heart of the style)
def _lattice(cv, sl, u, v, p, occ, col, kind, melt, jit, base):
    """beads whose centres sit on integer (u, v); melt fuses neighbours. Writes into the canvas window `sl`."""
    R_, C_ = occ.shape
    S = cv.S
    aa = 1.0 / S
    i0, j0 = np.floor(u).astype(np.int32), np.floor(v).astype(np.int32)
    occf, meltf = occ.ravel(), melt.ravel()
    SD, RR, ID = [], [], []
    for a in (0, 1):
        for b in (0, 1):
            ci, rj = i0 + a, j0 + b
            ok = (ci >= 0) & (ci < C_) & (rj >= 0) & (rj < R_)
            idx = np.clip(rj, 0, R_ - 1) * C_ + np.clip(ci, 0, C_ - 1)
            ok &= occf[idx]
            m = meltf[idx]
            r = np.hypot(u - ci - jit[..., 0].ravel()[idx], v - rj - jit[..., 1].ravel()[idx]) * p
            sd = np.where(ok, r - BEAD_R * p * (1 + 0.22 * m), 1e4)
            SD.append(sd.astype(np.float32)); RR.append(r.astype(np.float32)); ID.append(np.where(ok, idx, -1))
    SD, RR, ID = np.stack(SD), np.stack(RR), np.stack(ID)
    if not (ID >= 0).any(): return
    own = np.argmin(SD, 0)[None]
    sd1 = np.take_along_axis(SD, own, 0)[0]
    r_own = np.take_along_axis(RR, own, 0)[0]
    i_own = np.take_along_axis(ID, own, 0)[0]
    have = i_own >= 0
    io = np.maximum(i_own, 0)
    m = meltf[io] * have
    mm = np.max(np.where(ID >= 0, meltf[np.maximum(ID, 0)], 0), 0)
    kk = (0.012 + 0.55 * mm) * p                                          # outlines flow together as they melt
    order = np.argsort(SD, 0)
    Ss = np.take_along_axis(SD, order, 0)
    sdu = Ss[0]
    for q in (1, 2, 3): sdu = _smin(sdu, Ss[q], kk)
    sdu = np.where(have, sdu, 1e4)
    rh = BEAD_RH * p * (1 - 0.74 * m)
    hb = BEAD_H * p * (1 - 0.40 * m) * (1 + jit[..., 2].ravel()[io])
    e_in = r_own - rh
    e = np.minimum(-sdu, e_in)
    c_out = BEAD_C * p * (1 + 0.6 * m)                                     # the piece's outer edge rolls over
    c_in = BEAD_C * p * (1 + 1.3 * m)                                      # molten plastic slumps into the hole
    prof = np.minimum(_shoulder(-sdu, hb, c_out, aa), _shoulder(e_in, hb, c_in, aa))
    if mm.max() > 0:
        # melted top: each bead slumps into a low pillow around its closing hole; seams stay as faint grooves;
        # the grain of the ironing paper is pressed into the plastic
        pil = 1 - 0.05 * m * np.clip(r_own / (0.55 * p), 0, 1.4) ** 2
        seam = np.exp(-((Ss[1] - Ss[0]) / (0.05 * p)) ** 2) * (Ss[1] < 0.2 * p)
        groove = 0.06 * BEAD_H * p * seam * np.clip(1 - m / 0.7, 0, 1) ** 2 * (m > 0)
        hh, ww = prof.shape
        grain = (noise2d(hh, ww, 2.2 * S, 2, int(p * 1000) % 9973) - 0.5) * 0.08 + \
                (noise2d(hh, ww, 30 * S, 3, 77) - 0.5) * 0.7
        prof = np.where(prof > 0, prof * pil - groove + grain * m * (prof > 0.5 * hb), prof)
    # colours: soft blend across seams, per-bead dye-lot shade
    wq = np.exp(-np.clip(SD - sd1[None], 0, 30) / (0.6 / S)) * (ID >= 0)
    colf = col.reshape(-1, 3)
    albb = (wq[..., None] * colf[np.maximum(ID, 0)]).sum(0) / np.maximum(wq.sum(0), 1e-6)[..., None]
    kd = kind.ravel()[io]
    under = cv.alb[sl].copy()
    # looking down a hole: the peg / table in there is lit through the coloured wall
    hole_w = (np.clip(-e_in * S, 0, 1) * have * (r_own < BEAD_R * p))[..., None]
    cv.alb[sl] = under * (1 - hole_w) + under * (0.22 + 0.78 * albb) * 0.8 * hole_w
    alb = albb.copy()
    clear = (kd == 2)[..., None]
    if clear.any():
        wall = BEAD_R * p - BEAD_RH * p
        rim = np.exp(-(np.clip(e, 0, None) / (0.18 * wall)) ** 2)[..., None]
        alb = np.where(clear, (0.35 * albb + 0.65 * under * 1.08) * (1 - 0.45 * rim), alb)
    glow = (kd == 3)[..., None]
    if glow.any(): alb = np.where(glow, 0.8 * albb + 0.2 * under, alb)
    mat = np.select([kd == 1, kd == 2], [PEARL, CLEAR], PLASTIC).astype(np.uint8)
    spec = np.select([kd == 1, kd == 2], [0.45, 0.85], 0.55) * (1 - 0.25 * m)
    rough = np.select([kd == 1, kd == 2], [0.30, 0.06], 0.16) + 0.30 * m
    trans = np.select([kd == 2, kd == 3], [0.0, 0.9], 0.55)
    cv.put(sl, np.where(prof > 0, base + prof, -1e3), alb, spec, rough, mat, trans)


def _stamp_bead(cv, x, y, col, pose, ang, tilt, p, sink=0.3, base=None, layer=None, floor=None, cap=1.3):
    """one loose bead: standing on end (a ring, maybe tipped) or lying on its side. Lands on whatever is under it."""
    tgt = layer if layer is not None else cv
    w = cv.win(x - p, y - p, x + p, y + p) if layer is None else layer.win(x - p, y - p, x + p, y + p)
    if w is None: return
    sl, X, Y = w
    S = cv.S
    aa = 1.0 / S
    zo = tgt.z[sl]
    if base is None:
        rr = np.hypot(X - x, Y - y)
        near = rr < BEAD_R * p * 0.9
        base = (zo[near].max() if near.any() else 0.0) - sink * BEAD_R * p
        base = max(base, float(zo[near].min()) if near.any() else 0.0)
        if floor is not None: base = min(base, floor + cap * BEAD_H * p * 0.62)
    ca, sa = np.cos(np.radians(ang)), np.sin(np.radians(ang))
    dx, dy = X - x, Y - y
    t = dx * ca - dy * sa                      # along the tilt / lying axis (screen, ccw angle)
    s = dx * sa + dy * ca
    c = _c(col)
    R = BEAD_R * p
    if pose == 'side':
        L = BEAD_H * p
        et = L / 2 - np.abs(t)
        ce = 0.16 * p
        fe = np.sqrt(np.clip(1 - (1 - np.clip(et / ce, 0, 1)) ** 2, 0, 1))
        top = np.sqrt(np.maximum(R * R - s * s, 0))
        cov = np.clip((R - np.abs(s)) / aa + 0.5, 0, 1) * np.clip(et / aa + 0.5, 0, 1)
        prof = (R * 0.9 + top) * fe * cov
        # a tube lying down shows its hole at the ends as a dark ring on the end face
        endh = np.clip(1 - np.hypot(s / (BEAD_RH * p), (np.abs(t) - L / 2 + 0.02 * p) / (0.13 * p)), 0, 1)
        shade = 1 - 0.55 * np.clip(endh * 3, 0, 1)
        alb = _lin(c)[None, None] * shade[..., None]
    else:
        ct = np.cos(tilt)
        r = np.hypot(t / ct, s)
        e = np.minimum(R - r, r - BEAD_RH * p)
        prof = _shoulder(e, BEAD_H * p * ct, BEAD_C * p, aa)
        prof = np.where(prof > 0, prof + t * np.sin(tilt) * 0.9, 0)
        alb = np.broadcast_to(_lin(c)[None, None], prof.shape + (3,)).copy()
        inh = ((r < BEAD_RH * p) & (r < R))[..., None]
        tgt.alb[sl] = np.where(inh, tgt.alb[sl] * (0.22 + 0.78 * _lin(c)) * 0.75, tgt.alb[sl])
    kd = _KIND.get(col, 0) if isinstance(col, str) else 0
    if kd == 2 and pose != 'side':
        rim = np.exp(-(np.clip(np.minimum(R - r, r - BEAD_RH * p), 0, None) / (0.05 * p)) ** 2)[..., None]
        alb = (0.22 * alb + 0.78 * tgt.alb[sl] * 1.05) * (1 - 0.5 * rim)
    elif kd == 2: alb = 0.3 * alb + 0.7 * tgt.alb[sl] * 1.08
    mat = {1: PEARL, 2: CLEAR}.get(kd, PLASTIC)
    spec = {1: 0.45, 2: 0.85}.get(kd, 0.55)
    rough = {1: 0.3, 2: 0.06}.get(kd, 0.16)
    zn = np.where(prof > 0, base + prof, -1e3)
    if layer is not None:
        layer.put(sl, zn, alb, spec, rough, mat, thick=np.where(prof > 0, prof + 2, 0))
    else:
        cv.put(sl, zn, alb, spec, rough, mat, 0.9 if kd == 3 else (0.0 if kd == 2 else 0.55))


# ---------------------------------------------------------------- scene objects
class _Desk:
    def __init__(self, colour, kind, seed):
        self.c, self.kind, self.seed = _c(colour), kind, seed

    def raster(self, cv):
        Hm, Wm, S = cv.Hm, cv.W, cv.S
        base = _lin(self.c)
        if self.kind == 'wood':
            lo = noise2d(Hm, max(16, Wm // 14), 40 * S, 4, self.seed)
            lo = np.asarray(Image.fromarray(lo).resize((Wm, Hm), Image.BICUBIC), np.float32)
            y = np.arange(Hm, dtype=np.float32)[:, None] / S
            ring = 0.5 + 0.5 * np.sin(2 * np.pi * (y / 11.0 + 5.5 * lo))
            fine = noise2d(Hm, max(16, Wm // 40), 3 * S, 2, self.seed + 1)
            fine = np.asarray(Image.fromarray(fine).resize((Wm, Hm), Image.BILINEAR), np.float32)
            blot = noise2d(Hm, Wm, 220 * S, 3, self.seed + 2)
            v = 1 - 0.07 * ring ** 3 - 0.05 * (fine - 0.5) - 0.07 * (blot - 0.5)
            cv.alb[:] = base[None, None] * v[..., None]
            cv.alb[..., 0] *= 1 + 0.04 * ring ** 3
            cv.spec[:], cv.rough[:] = 0.06, 0.55
        else:                                                           # a plain craft mat
            n = noise2d(Hm, Wm, 3 * S, 2, self.seed) - 0.5
            blot = noise2d(Hm, Wm, 260 * S, 3, self.seed + 2) - 0.5
            cv.alb[:] = base[None, None] * (1 + 0.035 * n + 0.05 * blot)[..., None]
            cv.spec[:], cv.rough[:] = 0.03, 0.8
        cv.z[:] = 0
        cv.mat[:] = DESK


class _Sheet:
    """any thin flat thing drawn with PIL: a chart, a card, a strip of tape, ironing paper"""

    def __init__(self, draw, cx, cy, angle, thick=0.9, translucency=0.0, drape=0.0, spec=0.03, rough=0.85,
                 cut=None, curl=0.0, bump=0.0, seed=0):
        self.draw, self.cx, self.cy, self.angle = draw, cx, cy, angle
        self.thick, self.tr, self.drape, self.spec, self.rough = thick, translucency, drape, spec, rough
        self.cut, self.curl, self.bump, self.seed = cut, curl, bump, seed
        self.data = {}
        self.hidden = False

    def raster(self, cv):
        if self.hidden: return
        code = self.draw.__code__
        im = self.draw(cv.S, data=self.data) if 'data' in code.co_varnames[:code.co_argcount] else self.draw(cv.S)
        got = cv.paste(im, self.cx, self.cy, self.angle)
        if got is None: return
        sl, arr = got
        a = arr[..., 3]
        if self.cut is not None:                                   # peeled back: only the part past a line stays
            (px, py), (nx, ny) = self.cut
            yy, xx = np.mgrid[sl[0], sl[1]].astype(np.float32) / cv.S
            d = (xx - px) * nx + (yy - py) * ny                    # > 0 keeps
            a = a * np.clip(d * cv.S + 0.5, 0, 1)
        zo = cv.z[sl]
        if self.drape:
            r = int(self.drape * cv.S)
            base = blur(_maxf(zo, r), 0.8 * r)
        else:
            base = zo
        lift = 0
        if self.cut is not None and self.curl:
            lift = self.curl * np.exp(-np.clip(d, 0, None) / 9.0) * (d > -1)
        if self.bump:                                             # heat-wrinkled: a low, soft cockle
            hh, ww = a.shape
            lift = lift + self.bump * (noise2d(hh, ww, 32 * cv.S, 3, self.seed % 9973) - 0.5) * 2 + self.bump
        rgb = _lin(arr[..., :3])
        if self.tr: rgb = rgb * (1 - self.tr) + cv.alb[sl] * self.tr * 1.05
        cv.put(sl, np.where(a > 0.02, base + (self.thick + lift) * a, -1), rgb, self.spec, self.rough, PAPER,
               0.25 if self.tr else 0.0)


class Board:
    """a pegboard and the beads on it. Returned by Perler.pegboard(); cells are (row, col)."""

    def __init__(self, cx, cy, cols, rows, shape, colour, angle, pitch, translucency, seed):
        self.cx, self.cy, self.cols, self.rows = cx, cy, cols, rows
        self.shape, self.colour, self.angle, self.pitch, self.tr = shape, _c(colour), angle, pitch, translucency
        r = np.random.default_rng(seed)
        self.seed = seed
        self.occ = np.zeros((rows, cols), bool)
        self.col = np.zeros((rows, cols, 3), np.float32)
        self.kind = np.zeros((rows, cols), np.int32)
        self.melt = np.zeros((rows, cols), np.float32)
        self.jit = np.stack([r.normal(0, 0.022, (rows, cols)), r.normal(0, 0.022, (rows, cols)),
                             r.normal(0, 0.018, (rows, cols))], -1).astype(np.float32)
        self.shade = r.normal(0, 1, (rows, cols, 2)).astype(np.float32)
        self.plate = True
        vv, uu = np.mgrid[0:rows, 0:cols].astype(np.float32)
        cu, cr = (cols - 1) / 2, (rows - 1) / 2
        if shape == 'circle':
            self.pegs = np.hypot(uu - cu, vv - cr) <= min(cols, rows) / 2 - 0.3
        elif shape == 'hexagon':                                        # flat-topped hexagon
            q, w = np.abs(uu - cu), np.abs(vv - cr)
            self.pegs = np.maximum(w, q * 0.866 + w * 0.5) <= (min(cols, rows) / 2 - 0.3) * 0.866
        else:
            self.pegs = np.ones((rows, cols), bool)

    def xy(self, row, col):
        """output-px position of the peg at (row, col) (its foot on the board)"""
        a = np.radians(self.angle)
        lx, ly = (col - (self.cols - 1) / 2) * self.pitch, (row - (self.rows - 1) / 2) * self.pitch
        return (self.cx + lx * np.cos(a) + ly * np.sin(a), self.cy - lx * np.sin(a) + ly * np.cos(a))

    def top(self):
        return PLATE_T * self.pitch if self.plate else 0.0

    def raster(self, cv):
        p, S = self.pitch, cv.S
        a = np.radians(self.angle)
        ca, sa = np.cos(a), np.sin(a)
        margin = 0.42 * p
        half = 0.5 * np.hypot(self.cols, self.rows) * p + margin + 4
        w = cv.win(self.cx - half, self.cy - half, self.cx + half, self.cy + half)
        if w is None: return
        sl, X, Y = w
        dx, dy = X - self.cx, Y - self.cy
        lx, ly = dx * ca - dy * sa, dx * sa + dy * ca                  # board-local px
        u = lx / p + (self.cols - 1) / 2
        v = ly / p + (self.rows - 1) / 2
        zo = cv.z[sl]
        base = float(np.median(zo))
        aa = 1.0 / S
        if self.plate:
            hx, hy = self.cols * p / 2 + margin, self.rows * p / 2 + margin
            if self.shape == 'circle':
                sd = np.hypot(lx, ly) - (min(self.cols, self.rows) / 2 * p + margin * 0.6)
            elif self.shape == 'hexagon':
                rr = min(self.cols, self.rows) / 2 * p + margin * 0.6
                q, w_ = np.abs(lx), np.abs(ly)
                sd = np.maximum(w_, q * 0.866 + w_ * 0.5) - rr * 0.866
            else:
                rc = 0.9 * p
                qx, qy = np.abs(lx) - hx + rc, np.abs(ly) - hy + rc
                sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rc
            tb = PLATE_T * p
            plate = _shoulder(-sd, tb, 0.45 * tb, aa)
            iu, iv = np.rint(u).astype(np.int32), np.rint(v).astype(np.int32)
            ok = (iu >= 0) & (iu < self.cols) & (iv >= 0) & (iv < self.rows)
            ok &= self.pegs[np.clip(iv, 0, self.rows - 1), np.clip(iu, 0, self.cols - 1)]
            rp = np.hypot(u - iu, v - iv) * p
            peg = _shoulder(PEG_R * p - rp, PEG_H * p, 0.8 * PEG_R * p, aa) * ok * (plate > 0.9 * tb)
            under = _blur3(cv.alb[sl], 3 * S)
            bc = _lin(self.colour)[None, None]
            n = noise2d(zo.shape[0], zo.shape[1], 5 * S, 2, self.seed % 9973)[..., None]
            alb = bc * (1 - self.tr) + under * self.tr * 1.15
            alb = alb * (0.985 + 0.03 * n)
            alb = np.where((peg > 0.3)[..., None], alb * 0.9 + bc * 0.12, alb)
            cv.put(sl, np.where(plate > 0, base + plate + peg, -1), alb, 0.30, 0.30, BOARD, 0.6)
            zb = base + tb
        else:
            zb = np.maximum(blur(zo, 2 * S), zo)                        # off the board: sits on the table
        if self.occ.any():
            _lattice(cv, sl, u, v, p, self.occ, _lin(self.col), self.kind, self.melt, self.jit, zb)


class _Tray:
    def __init__(self, cx, cy, cols, rows, cell, angle, colour, seed):
        self.cx, self.cy, self.cols, self.rows, self.cell = cx, cy, cols, rows, cell
        self.angle, self.colour, self.seed = angle, _c(colour), seed
        self.wall, self.h = 0.12 * cell, 0.26 * cell

    def local_to_xy(self, lx, ly):
        a = np.radians(self.angle)
        return self.cx + lx * np.cos(a) + ly * np.sin(a), self.cy - lx * np.sin(a) + ly * np.cos(a)

    def raster(self, cv):
        S, a = cv.S, np.radians(self.angle)
        W2, H2 = self.cols * self.cell / 2 + self.wall, self.rows * self.cell / 2 + self.wall
        half = np.hypot(W2, H2) + 6
        w = cv.win(self.cx - half, self.cy - half, self.cx + half, self.cy + half)
        if w is None: return
        sl, X, Y = w
        dx, dy = X - self.cx, Y - self.cy
        lx, ly = dx * np.cos(a) - dy * np.sin(a), dx * np.sin(a) + dy * np.cos(a)
        rc = 0.18 * self.cell
        qx, qy = np.abs(lx) - W2 + rc, np.abs(ly) - H2 + rc
        sd = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rc
        aa = 1.0 / S
        e_out = np.minimum(-sd, self.wall + sd)
        e = e_out
        for i in range(1, self.cols):
            e = np.maximum(e, np.minimum(self.wall / 2 - np.abs(lx - (-W2 + self.wall + i * self.cell)), -sd))
        for j in range(1, self.rows):
            e = np.maximum(e, np.minimum(self.wall / 2 - np.abs(ly - (-H2 + self.wall + j * self.cell)), -sd))
        walls = _shoulder(e, self.h, 0.4 * self.wall, aa)
        floor = _shoulder(-sd, 1.6, 0.8, aa)
        zo = cv.z[sl]
        under = _blur3(cv.alb[sl], 3 * S)
        bc = _lin(self.colour)[None, None]
        wallish = (walls > 0.5)[..., None]
        alb = np.where(wallish, bc * 0.8 + under * 0.25, bc * 0.45 + under * 0.62)
        cv.put(sl, np.where(np.maximum(walls, floor) > 0, zo + np.maximum(walls, floor), -1), alb, 0.35, 0.25,
               BOARD, 0.7)


class _Beads:
    """a set of loose beads (a spill, a heap in a tray compartment, one bead) rastered in order, so they stack;
    floor: the surface they were poured onto (heaps stay low: at most `cap` bead layers)"""

    def __init__(self, items, pitch, floor=None, cap=1.3):
        self.items, self.p, self.floor, self.cap = items, pitch, floor, cap

    def raster(self, cv):
        for (x, y, col, pose, ang, tilt) in self.items:
            _stamp_bead(cv, x, y, col, pose, ang, tilt, self.p, floor=self.floor, cap=self.cap)


class _Layer:
    """something held in the air: its own little height field, drawn after the scene with its own cast shadow"""

    def __init__(self, cv, x0, y0, x1, y1):
        self.cv = cv
        w = cv.win(x0, y0, x1, y1)
        self.sl, self.X, self.Y = w
        h, ww = self.Y.shape[0], self.X.shape[1]
        self.z = np.full((h, ww), -1e3, np.float32)
        self.alb = np.zeros((h, ww, 3), np.float32)
        self.spec = np.zeros((h, ww), np.float32)
        self.rough = np.ones((h, ww), np.float32)
        self.mat = np.zeros((h, ww), np.uint8)
        self.thick = np.zeros((h, ww), np.float32)

    def win(self, x0, y0, x1, y1):
        S = self.cv.S
        b0, a0 = self.sl[0].start, self.sl[1].start
        c0, c1 = max(0, int(np.floor(x0 * S)) - a0), min(self.z.shape[1], int(np.ceil(x1 * S)) - a0)
        r0, r1 = max(0, int(np.floor(y0 * S)) - b0), min(self.z.shape[0], int(np.ceil(y1 * S)) - b0)
        if c1 <= c0 or r1 <= r0: return None
        return (slice(r0, r1), slice(c0, c1)), self.X[:, c0:c1], self.Y[r0:r1]

    def put(self, sl, znew, alb, spec, rough, mat, thick):
        up = znew > self.z[sl]
        self.z[sl] = np.where(up, znew, self.z[sl])
        self.alb[sl] = np.where(up[..., None], alb, self.alb[sl])
        self.spec[sl] = np.where(up, spec, self.spec[sl])
        self.rough[sl] = np.where(up, rough, self.rough[sl])
        self.mat[sl] = np.where(up, mat, self.mat[sl])
        self.thick[sl] = np.where(up, thick, self.thick[sl])


class _Tweezers:
    def __init__(self, tip, angle, length, lift, rise, holding, grip, open_w, pitch, seed):
        self.tip, self.angle, self.L, self.lift, self.rise = tip, angle, length, lift, rise
        self.holding, self.grip, self.open, self.p, self.seed = holding, grip, open_w, pitch, seed

    def raster(self, cv):
        S, p = cv.S, self.p
        a = np.radians(self.angle)
        ux, uy = np.cos(a), -np.sin(a)                                   # from the tip toward the hinge
        tx, ty = self.tip
        ex, ey = tx + ux * self.L, ty + uy * self.L
        pad = 30
        ly = _Layer(cv, min(tx, ex) - pad, min(ty, ey) - pad, max(tx, ex) + pad, max(ty, ey) + pad)
        X, Y = ly.X, ly.Y
        dx, dy = X - tx, Y - ty
        t = dx * ux + dy * uy                                            # along, 0 at the tip
        s = -dx * uy + dy * ux                                           # across
        L = self.L
        tt = np.clip(t / L, 0, 1)
        gap = self.open                                                   # tip opening (centre to centre)
        wleg = 1.5 + 3.4 * tt ** 0.7                                     # half width of each leg
        sc = (gap / 2) * (1 - tt) + wleg * 0.97 * tt                    # legs meet at the hinge
        zplane = self.lift + self.rise * t
        best = np.full(t.shape, -1.0, np.float32)
        for sign in (-1, 1):
            d = np.abs(s - sign * sc)
            e = wleg - d
            best = np.maximum(best, e)
        inside = (t > -0.5) & (t < L)
        et = np.minimum(t + 0.5, L - t)
        e = np.minimum(best, et)
        grip0, grip1 = 0.42 * L, 0.78 * L
        gr = (t > grip0) & (t < grip1)
        th = np.where(gr, 3.6, 2.6)
        aa = 1.0 / S
        prof = _shoulder(e, th, np.where(gr, 1.6, 0.9), aa) * inside
        # stainless: brushed along the leg; a rubber grip sleeve in the middle with ribs
        streak = noise2d(prof.shape[0], prof.shape[1], 2.0 * S, 2, self.seed % 9973)
        streak = 0.5 + 0.5 * np.sin(2 * np.pi * (s / 2.3 + 3 * streak))          # brushed along the leg
        metal = np.array([0.46, 0.47, 0.50], np.float32)[None, None] * (0.72 + 0.45 * streak[..., None])
        ribs = 0.5 + 0.5 * np.cos(2 * np.pi * t / 5.0)
        gc = _lin(_c(self.grip))[None, None] * (0.85 + 0.2 * ribs[..., None])
        alb = np.where(gr[..., None], gc, metal)
        mat = np.where(gr, PLASTIC, METAL).astype(np.uint8)
        spec = np.where(gr, 0.25, 0.9)
        rough = np.where(gr, 0.45, 0.12)
        ly.put((slice(None), slice(None)), np.where(prof > 0.05, zplane + prof, -1e3), alb, spec, rough, mat,
               np.where(prof > 0, prof + 0.5, 0))
        if self.holding:
            bx, by = tx + ux * 0.25 * p, ty + uy * 0.25 * p
            _stamp_bead(cv, bx, by, self.holding, 'stand', self.angle, 0.12, p,
                        base=self.lift - BEAD_H * p * 0.45, layer=ly)
        cv.over.append(ly)


# ---------------------------------------------------------------- the painter
class Perler:
    def __init__(self, W=1920, H=1080, seed=0, pitch=22.0, tilt=0.32, ss=2, light=(-350.0, -520.0, 2300.0)):
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.pitch, self.tilt, self.ss = float(pitch), float(tilt), int(ss)
        self.light = np.array(light, np.float32)
        self.objs, self.stages = [], []
        self.zmax = 3.4 * pitch
        self.stage_ss = 1

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ---- surfaces
    def desk(self, colour='#dcc5a0', kind='wood'):
        """the table top: 'wood' (pale oak, long grain) or 'mat' (a plain craft mat)"""
        o = _Desk(colour, kind, self._seed()); self.objs.append(o); return o

    def sheet(self, draw, cx, cy, angle=0.0, **kw):
        """a thin flat thing: draw(S) (or draw(S, data), data = the returned object's .data dict) returns an RGBA PIL
        image at S x scale. kw: thick, translucency, drape (px: rests on what is under it), cut, curl, bump"""
        o = _Sheet(draw, cx, cy, angle, **kw); self.objs.append(o); return o

    def pegboard(self, cx, cy, cols, rows=None, shape='square', colour='clear', angle=0.0, translucency=None):
        """a pegboard; colour 'clear' is frosted clear plastic (the table shows through), or any colour"""
        colour_ = {'clear': '#e9eef0', 'white': '#f2f1ee'}.get(colour, colour)
        tr = translucency if translucency is not None else (0.62 if colour == 'clear' else 0.18)
        b = Board(cx, cy, cols, rows or cols, shape, colour_, angle, self.pitch, tr, self._seed())
        self.objs.append(b); return b

    def place(self, board, rows, key, at=(0, 0), only=None, keep=None):
        """put beads on `board` from a text pattern: rows of characters, key maps a character to a bead colour
        name (BEADS) or '#rrggbb'. only: the characters to place now (placing colour by colour); keep(r, c) -> bool
        filters cells (e.g. only the part done so far). Returns the number of beads placed."""
        n = 0
        for i, line in enumerate(rows):
            for j, ch in enumerate(line):
                if ch not in key or (only is not None and ch not in only): continue
                rr, cc = at[0] + i, at[1] + j
                if not (0 <= rr < board.rows and 0 <= cc < board.cols) or not board.pegs[rr, cc]: continue
                if keep is not None and not keep(rr, cc): continue
                name = key[ch]
                c = _c(name)
                sh = board.shade[rr, cc]
                c = np.clip(c * (1 + 0.035 * sh[0]) + 0.012 * sh[1], 0, 1)          # dye-lot variation
                board.occ[rr, cc] = True
                board.col[rr, cc] = c
                board.kind[rr, cc] = _KIND.get(name, 0) if isinstance(name, str) else 0
                n += 1
        return n

    def iron(self, board, melt=0.7, where=None):
        """iron the beads on `board`: melt 0.35-0.5 is the half-melt (holes open, beads stuck together), 0.8 is
        flat and smooth. where(r, c) -> bool irons only part (the rest stays as it was)."""
        for rr in range(board.rows):
            for cc in range(board.cols):
                if board.occ[rr, cc] and (where is None or where(rr, cc)):
                    board.melt[rr, cc] = melt

    def lift_off(self, board):
        """take the ironed piece off its pegboard: the plate and pegs go, the piece lies on the table"""
        board.plate = False

    def tray(self, cx, cy, colours, cell=100.0, angle=0.0, colour='#eef2f3', fill=20):
        """a sorting tray with a compartment per colour (colours: list of rows), each holding a heap of beads"""
        rows, cols = len(colours), max(len(r) for r in colours)
        t = _Tray(cx, cy, cols, rows, cell, angle, colour, self._seed())
        self.objs.append(t)
        r = np.random.default_rng(self._seed())
        items = []
        W2, H2 = cols * cell / 2 + t.wall, rows * cell / 2 + t.wall
        for j, row in enumerate(colours):
            for i, name in enumerate(row):
                if not name: continue
                x0 = -W2 + t.wall * 1.5 + i * cell; y0 = -H2 + t.wall * 1.5 + j * cell
                inner = cell - t.wall * 2 - BEAD_R * self.pitch * 2
                cx0, cy0 = x0 + BEAD_R * self.pitch + inner / 2, y0 + BEAD_R * self.pitch + inner / 2
                g = int(np.ceil(np.sqrt(fill)))
                cells = [(a_, b_) for a_ in range(g) for b_ in range(g)]
                r.shuffle(cells)
                for q in range(fill):
                    a_, b_ = cells[q % len(cells)]
                    lx = cx0 - inner / 2 + (a_ + 0.5 + r.normal(0, 0.28)) * inner / g
                    lyy = cy0 - inner / 2 + (b_ + 0.5 + r.normal(0, 0.28)) * inner / g
                    lx, lyy = np.clip(lx, cx0 - inner / 2, cx0 + inner / 2), np.clip(lyy, cy0 - inner / 2, cy0 + inner / 2)
                    x, y = t.local_to_xy(lx, lyy)
                    pose = 'side' if r.random() < 0.55 else 'stand'
                    items.append((x, y, name, pose, r.uniform(0, 180), r.uniform(0, 0.55)))
        o = _Beads(items, self.pitch, floor=1.6, cap=1.0); self.objs.append(o)
        return t

    def spill(self, cx, cy, colours, n=20, spread=60.0, standing=0.35, weights=None, seed=None):
        """loose beads scattered on whatever is there (standing on end or lying on their side)"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        items = []
        for q in range(n):
            ang = r.random() * 2 * np.pi
            rad = spread * np.sqrt(r.random()) * (1 + 0.4 * r.normal(0, 0.3))
            name = colours[r.choice(len(colours), p=weights)]
            items.append((cx + np.cos(ang) * rad * 1.25, cy + np.sin(ang) * rad * 0.9, name,
                          'stand' if r.random() < standing else 'side', r.uniform(0, 180), r.uniform(0, 0.35)))
        o = _Beads(items, self.pitch, floor=0.0, cap=0.9); self.objs.append(o); return o

    def bead(self, x, y, colour, pose='stand', angle=0.0, tilt=0.0):
        """one loose bead at (x, y)"""
        o = _Beads([(x, y, colour, pose, angle, tilt)], self.pitch); self.objs.append(o); return o

    def tweezers(self, tip, angle, length=300.0, lift=26.0, rise=0.09, holding=None, grip='#e8775f', open_w=None):
        """bead tweezers held above the table: tip (x, y), pointing from the hinge toward the tip is angle+180.
        holding: a bead colour pinched in the tips. lift: height of the tips; rise: how fast the legs climb."""
        ow = open_w if open_w is not None else (2 * BEAD_R * self.pitch + 3.4 if holding else 3.0)
        o = _Tweezers(tip, angle, length, lift, rise, holding, grip, ow, self.pitch, self._seed())
        self.objs.append(o); return o

    def ironing_paper(self, cx, cy, w, h, angle=0.0, cut=None, curl=6.0, colour='#f4f1ea', wrinkle=0.0):
        """a sheet of ironing paper laid over the beads (drapes over them, translucent, fine grain).
        cut=((x, y), (nx, ny)): peeled back -- only the part where (P - point) . n > 0 stays, its edge curled;
        wrinkle: px of heat cockle (a used sheet)"""
        seed = self._seed()

        def draw(S, w=w, h=h):
            W_, H_ = int(w * S), int(h * S)
            n = noise2d(H_, W_, 1.6 * S, 2, seed % 9973)
            cl = noise2d(H_, W_, 40 * S, 3, (seed + 1) % 9973)
            c = hexc(colour)
            rgb = c[None, None] * (0.97 + 0.03 * n[..., None] + 0.035 * (cl[..., None] - 0.5))
            a = np.ones((H_, W_), np.float32)
            im = np.dstack([rgb, a]) * 255
            return Image.fromarray(im.clip(0, 255).astype(np.uint8), 'RGBA')
        o = _Sheet(draw, cx, cy, angle, thick=0.8, translucency=0.42, drape=0.5 * self.pitch, spec=0.12,
                   rough=0.45, cut=cut, curl=curl, bump=wrinkle, seed=seed)
        self.objs.append(o); return o

    def tape(self, text, cx, cy, width=None, angle=0.0, colour='#f1e6c8', ink='#3a3a3a', size=26, font='cjk_sans',
             sub=None, sub_font='hand', badge=None, badge_colour='#d3272f'):
        """a strip of masking tape with a handwritten / printed label; badge='1' adds a round step number"""
        seed = self._seed()

        def draw(S):
            f = _font(font, size * S)
            f2 = _font(sub_font, size * 0.62 * S) if sub else None
            tw = f.getlength(text) + (f2.getlength(sub) + size * 0.5 * S if sub else 0)
            bw = size * 1.25 * S if badge else 0
            W_ = int(width * S) if width else int(tw + bw + size * 1.6 * S)
            H_ = int(size * 1.75 * S)
            r = np.random.default_rng(seed)
            im = Image.new('RGBA', (W_, H_), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            zz = int(4 * S)
            left = [(zz * r.random(), H_ * k / 8) for k in range(9)]
            right = [(W_ - zz * r.random(), H_ * (8 - k) / 8) for k in range(9)]
            c = tuple(int(v * 255) for v in hexc(colour))
            d.polygon(left + right, fill=c + (235,))
            x = size * 0.8 * S
            if badge:
                cy_ = H_ / 2
                rr = size * 0.52 * S
                bc = tuple(int(v * 255) for v in hexc(badge_colour))
                d.ellipse([x - 0.1 * S, cy_ - rr, x + 2 * rr, cy_ + rr], fill=bc + (255,))
                d.text((x + rr, cy_ + 0.5 * S), badge, font=_font('sans_bold', size * 0.72 * S), fill=(255, 255, 255, 255),
                       anchor='mm')
                x += 2 * rr + size * 0.35 * S
            ic = tuple(int(v * 255) for v in hexc(ink))
            d.text((x, H_ / 2 + 1 * S), text, font=f, fill=ic + (255,), anchor='lm')
            if sub:
                d.text((x + f.getlength(text) + size * 0.45 * S, H_ / 2 + 2 * S), sub, font=f2, fill=ic + (215,),
                       anchor='lm')
            n = noise2d(H_, W_, 2 * S, 2, seed % 9973)
            arr = np.asarray(im, np.float32)
            arr[..., :3] *= (0.96 + 0.06 * n)[..., None]
            return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
        o = _Sheet(draw, cx, cy, angle, thick=0.5, translucency=0.12, spec=0.05, rough=0.7)
        self.objs.append(o); return o

    def chart(self, rows, key, cx, cy, cell=16.0, angle=0.0, title='', subtitle='', number='', names=None,
              done=(), note=None):
        """a printed pattern chart on graph paper: the design as coloured cells with a symbol each, row / column
        numbers, heavier lines every 5 cells, and a legend (bead icon, symbol, name, count). done: characters
        already placed get a pencil tick in the legend."""
        seed = self._seed()
        nr, nc = len(rows), max(len(r) for r in rows)
        counts = {ch: sum(line.count(ch) for line in rows) for ch in key}

        order = [ch for ch in key if counts[ch]]
        names = names or {}

        def draw(S, data):
            cs = cell * S
            left, top = 2.2 * cs, 5.4 * cs
            ncol_leg = 3
            nleg = (len(order) + ncol_leg - 1) // ncol_leg
            W_ = int(left + (nc + 1.4) * cs)
            H_ = int(top + (nr + 1.2) * cs + nleg * 1.9 * cs + 1.2 * cs)
            im = Image.new('RGBA', (W_, H_), (250, 248, 242, 255))
            d = ImageDraw.Draw(im)
            # graph paper everywhere (faint), on the same module as the pattern
            gx0, gy0 = left % cs, top % cs
            for i in range(int(W_ / cs) + 2):
                x = gx0 + i * cs
                d.line([(x, 0), (x, H_)], fill=(196, 220, 232, 255), width=max(1, int(0.5 * S)))
            for j in range(int(H_ / cs) + 2):
                y = gy0 + j * cs
                d.line([(0, y), (W_, y)], fill=(196, 220, 232, 255), width=max(1, int(0.5 * S)))
            # pattern cells
            fs = _font('sans_bold', cs * 0.52)
            for i, line in enumerate(rows):
                for j, ch in enumerate(line):
                    if ch not in key: continue
                    c = _c(key[ch])
                    pc = 0.88 * c + 0.12
                    x0, y0 = left + j * cs, top + i * cs
                    d.rectangle([x0, y0, x0 + cs, y0 + cs], fill=tuple(int(v * 255) for v in pc) + (255,))
                    lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
                    tc = (255, 255, 255, 235) if lum < 0.55 else (40, 40, 48, 220)
                    d.text((x0 + cs / 2, y0 + cs / 2 + 0.3 * S), ch, font=fs,
                           fill=tc, anchor='mm')
            # chart grid over the pattern area
            for i in range(nc + 1):
                x = left + i * cs
                heavy = i % 5 == 0 or i == nc
                d.line([(x, top), (x, top + nr * cs)], fill=(70, 72, 80, 255) if heavy else (150, 152, 160, 255),
                       width=max(1, int((1.3 if heavy else 0.6) * S)))
            for j in range(nr + 1):
                y = top + j * cs
                heavy = j % 5 == 0 or j == nr
                d.line([(left, y), (left + nc * cs, y)], fill=(70, 72, 80, 255) if heavy else (150, 152, 160, 255),
                       width=max(1, int((1.3 if heavy else 0.6) * S)))
            fn = _font('sans', cs * 0.5)
            for i in range(nc):
                if (i + 1) % 5 == 0 or i == 0:
                    d.text((left + (i + 0.5) * cs, top - 0.35 * cs), str(i + 1), font=fn, fill=(90, 92, 100, 255),
                           anchor='ms')
            for j in range(nr):
                if (j + 1) % 5 == 0 or j == 0:
                    d.text((left - 0.35 * cs, top + (j + 0.5) * cs), str(j + 1), font=fn, fill=(90, 92, 100, 255),
                           anchor='rm')
            # centre arrows (as on printed charts)
            for (ax, ay, dx_, dy_) in [(left + nc / 2 * cs, top - 0.05 * cs, 0, -1), (left - 0.05 * cs, top + nr / 2 * cs, -1, 0)]:
                sz = 0.32 * cs
                if dy_:
                    d.polygon([(ax, ay), (ax - sz, ay - 1.3 * sz), (ax + sz, ay - 1.3 * sz)], fill=(211, 60, 60, 255))
                else:
                    d.polygon([(ax, ay), (ax - 1.3 * sz, ay - sz), (ax - 1.3 * sz, ay + sz)], fill=(211, 60, 60, 255))
            # header
            if number:
                d.text((left, 1.0 * cs), number, font=_font('sans_bold', cs * 0.62), fill=(211, 60, 60, 255), anchor='ls')
            if title:
                d.text((left, 2.75 * cs), title, font=_font('cjk_sans', cs * 1.45), fill=(40, 40, 48, 255), anchor='ls')
            if subtitle:
                d.text((left, 3.9 * cs), subtitle, font=_font('sans', cs * 0.62), fill=(95, 97, 106, 255), anchor='ls')
            # legend
            ly0 = top + (nr + 1.3) * cs
            colw = (nc * cs) / ncol_leg
            fl = _font('cjk_sans', cs * 0.72)
            fc = _font('sans', cs * 0.62)
            rg = np.random.default_rng(seed)
            for q, ch in enumerate(order):
                gx_, gy_ = left + (q % ncol_leg) * colw, ly0 + (q // ncol_leg) * 1.9 * cs
                c = _c(key[ch]); ci = tuple(int(v * 255) for v in c) + (255,)
                rr = 0.52 * cs
                cxx, cyy = gx_ + rr, gy_ + 0.75 * cs
                d.ellipse([cxx - rr, cyy - rr, cxx + rr, cyy + rr], fill=ci, outline=(90, 90, 96, 255),
                          width=max(1, int(0.6 * S)))
                d.ellipse([cxx - rr * 0.45, cyy - rr * 0.45, cxx + rr * 0.45, cyy + rr * 0.45], fill=(250, 248, 242, 255))
                d.text((gx_ + 2.5 * rr, cyy), ch, font=_font('sans_bold', cs * 0.66),
                       fill=(50, 50, 58, 255), anchor='lm')
                d.text((gx_ + 2.5 * rr + 0.9 * cs, cyy), names.get(ch, key[ch]), font=fl, fill=(50, 50, 58, 255), anchor='lm')
                d.text((gx_ + colw - 0.6 * cs, cyy), f'x{counts[ch]}', font=fc, fill=(110, 112, 120, 255), anchor='rm')
                if ch in data['done']:                                    # pencil tick: already on the board
                    px_, py_ = cxx + 0.1 * cs, cyy + 0.05 * cs
                    pts = [(px_ - 0.35 * cs, py_ - 0.05 * cs), (px_ - 0.1 * cs + rg.normal(0, 0.3) * S, py_ + 0.35 * cs),
                           (px_ + 0.45 * cs, py_ - 0.55 * cs + rg.normal(0, 0.3) * S)]
                    d.line(pts, fill=(70, 70, 78, 235), width=max(1, int(1.9 * S)), joint='curve')
            if note:
                d.text((left, H_ - 0.55 * cs), note, font=_font('hand', cs * 0.7), fill=(88, 88, 96, 220), anchor='ls')
            n = noise2d(H_, W_, 2.2 * S, 2, seed % 9973)
            arr = np.asarray(im, np.float32)
            arr[..., :3] *= (0.975 + 0.035 * n)[..., None]
            return Image.fromarray(arr.clip(0, 255).astype(np.uint8), 'RGBA')
        o = _Sheet(draw, cx, cy, angle, thick=0.9, spec=0.03, rough=0.85)
        o.data['done'] = o.done = set(done)                             # chart.done.update('RD') ticks colours off
        o.counts = counts
        self.objs.append(o); return o

    def on_top(self, *objs):
        """move things to the top of the pile (drawn last), e.g. labels after a sheet slid under them"""
        for o in objs:
            if o in self.objs: self.objs.remove(o); self.objs.append(o)

    def remove(self, obj):
        """take something off the table (e.g. the ironing paper once it has been peeled)"""
        if obj in self.objs: self.objs.remove(obj)

    # ---- rendering
    def _raster(self, S):
        cv = _Canvas(self.W, self.H, S, self.tilt, self.zmax)
        for o in self.objs: o.raster(cv)
        return cv

    def _march(self, f, s0, s1):
        """f: (rows, cols) screen row of every world row (y - tilt z), +big where empty. For screen rows s0..s1-1
        return the index of the nearest world row whose surface covers that pixel (-1 if none)."""
        Hm, Wm = f.shape
        f = np.minimum(f, s1 + 8.0)                                     # empty rows: past every query
        m = np.minimum.accumulate(f[::-1], axis=0)[::-1]
        lo = float(m.min())
        out = np.empty((s1 - s0, Wm), np.int32)
        BIG = (s1 + 8.0 - lo) + 64.0                                    # > the value range of one column
        q0 = np.arange(s0, s1, dtype=np.float64) - lo
        for c0 in range(0, Wm, 384):
            c1 = min(Wm, c0 + 384); n = c1 - c0
            off = (np.arange(n, dtype=np.float64) * BIG)[:, None]
            flat = (m[:, c0:c1].T.astype(np.float64) - lo + off).ravel()
            q = (q0[None, :] + off).ravel()
            idx = np.searchsorted(flat, q, side='right').reshape(n, -1) - (np.arange(n) * Hm)[:, None] - 1
            out[:, c0:c1] = idx.T
        return out

    def _light(self, N, P, alb, spec, rough, mat, trans, sh, ao):
        """shade (…, 3) normals at world points P (output px) -> linear RGB"""
        V = np.array([0, self.tilt, 1], np.float32); V /= np.linalg.norm(V)
        L = self.light[None, None] - P
        L /= np.linalg.norm(L, axis=-1, keepdims=True)
        ndl = np.clip((N * L).sum(-1), 0, 1)
        vis = 1 - 0.82 * sh
        amb = (0.40 + 0.26 * N[..., 2] + 0.16 * np.clip(N[..., 1], 0, 1)) * (1 - 0.82 * ao)
        dif = 0.92 * ndl * vis
        Hh = L + V[None, None]; Hh /= np.linalg.norm(Hh, axis=-1, keepdims=True)
        ndh = np.clip((N * Hh).sum(-1), 0, 1)
        shin = 10 + 420 * (1 - rough) ** 3
        spk = spec * ndh ** shin * (0.15 + 1.2 * (1 - rough) ** 2) * vis
        ndv = np.clip((N * V).sum(-1), 0, 1)
        R = 2 * ndv[..., None] * N - V
        # the key is a big soft box: every surface whose mirror direction points into it shows it as a bright
        # patch -- a crisp arc on the upper-left shoulder of each bead's rim and on the far lip of its hole;
        # rougher (melted) plastic spreads it into a broad waxy sheen that drifts across a flat piece
        rl = np.clip((R * L).sum(-1), -1, 1)
        a_in = np.radians(8.0)
        a_out = a_in + np.radians(5.0 + 62.0 * rough)
        win = smoothstep(np.cos(a_out), np.cos(a_in), rl)
        F = 0.04 + 0.96 * (1 - ndv) ** 5
        env = spec * (0.05 + 0.08 * F + 1.35 * win * (1 - 0.55 * rough)) * (1 - 0.6 * ao) * vis ** 0.5
        a = alb
        key = np.array([1.03, 1.0, 0.95], np.float32)
        sky = np.array([0.95, 0.99, 1.05], np.float32)
        col = a * (amb[..., None] * sky + dif[..., None] * key)
        # translucent plastic: light that went through comes out coloured in the shade
        col += a * np.sqrt(a) * (trans * 0.30 * (1 - ndl * vis) * (1 - 0.6 * ao))[..., None]
        white = (spk + env)[..., None] * key
        pearl = mat == PEARL
        if pearl.any():
            ph = ndv * 5.0 + N[..., 0] * 2.0
            irid = 0.5 + 0.5 * np.cos(2 * np.pi * (ph[..., None] + np.array([0.0, 0.33, 0.67], np.float32)))
            col = np.where(pearl[..., None], col + (0.16 * (1 - ndv) + 0.05)[..., None] * (0.55 + 0.6 * irid) * (1 - ao[..., None]), col)
        metal = mat == METAL
        if metal.any():
            wm = win
            mc = a * (0.34 * amb[..., None] + 0.30 * dif[..., None]) + a * (0.12 + 0.9 * wm[..., None])
            col = np.where(metal[..., None], mc, col)
            white = np.where(metal[..., None], white * 0.3, white)
        return col + white

    def _render(self, S):
        cv = self._raster(S)
        k = self.tilt
        z = cv.z
        Hm, Wm = z.shape
        Hs = cv.H
        # shadows and occlusion on the world grid (heights in internal px)
        zi = z * S
        Lc = self.light - np.array([self.W / 2, self.H / 2, 0], np.float32)
        Ld = Lc / np.linalg.norm(Lc)
        sh = height_shadow(zi, light=tuple(Ld), reach=int(self.zmax * 1.4 * S), step=max(1.0, 0.75 * S), soft=2.4 * S)
        ao = ambient_occlusion(zi, radii=(2 * S, 6 * S, 16 * S), depth=(5.0 * S, 12.0 * S, 26.0 * S))
        ao = np.clip(ao * 1.0, 0, 1)
        for ly in cv.over:                                              # things held in the air cast soft shadows
            osh = np.zeros_like(z)
            valid = ly.z > -100
            if not valid.any(): continue
            b0, a0 = ly.sl[0].start, ly.sl[1].start
            ys, xs = np.nonzero(valid)
            dz = ly.z[ys, xs] - z[b0 + ys, a0 + xs]
            ox = np.rint((xs + a0) + dz * (-Ld[0] / Ld[2]) * S).astype(int)
            oy = np.rint((ys + b0) + dz * (-Ld[1] / Ld[2]) * S).astype(int)
            ok = (ox >= 0) & (ox < Wm) & (oy >= 0) & (oy < Hm)
            osh[oy[ok], ox[ok]] = 1
            osh = blur(_maxf(osh, int(S)), 2.2 * S)
            sh = np.maximum(sh, np.clip(osh * 1.5, 0, 1) * 0.92)
        gy, gx = np.gradient(z)
        gx *= S; gy *= S
        zb = blur(z, 2.2 * S)
        gyb, gxb = np.gradient(zb)
        y_idx = np.arange(Hm, dtype=np.float32)[:, None]
        f = y_idx - k * zi
        Y = self._march(f, 0, Hs)
        cols = np.arange(Wm)[None, :]
        Yc = np.clip(Y, 0, Hm - 2)
        srow = np.arange(Hs, dtype=np.float32)[:, None]
        fY = f[Yc, cols]
        wall = fY < srow - 1.5                                            # > 1.5 rows past its surface point: a wall
        zY = zi[Yc, cols]                                                 # (a gentle slope toward the camera
        zN = zi[np.minimum(Yc + 1, Hm - 1), cols]                        #  stretches a row over ~1.1 rows)                        # the foot of a wall: lowest of the next
        for d in range(2, 2 * S + 2):                                     # few rows (edges are anti-aliased steps)
            zN = np.minimum(zN, zi[np.minimum(Yc + d, Hm - 1), cols])
        zw = np.clip((Yc + 0.5 - srow) / k, zN, zY)
        # normals: tops from the height gradient, walls horizontal and facing the camera
        nt = np.stack([-gx[Yc, cols], -gy[Yc, cols], np.ones_like(zY)], -1)
        wall |= (1.0 / np.linalg.norm(nt, axis=-1)) < 0.3                  # steep anti-aliasing ramps shade as wall
        nw = np.stack([-gxb[Yc, cols], np.maximum(-gyb[Yc, cols], 0.0), np.zeros_like(zY)], -1)
        nwl = np.linalg.norm(nw, axis=-1, keepdims=True)
        nw = np.where(nwl > 1e-4, nw / np.maximum(nwl, 1e-6), np.array([0, 1, 0], np.float32))
        nw[..., 1] = np.maximum(nw[..., 1], 0.25)
        N = np.where(wall[..., None], nw, nt)
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        zT = zY.copy()                                                    # the real top of a wall (not the ramp row)
        for d in range(1, 2 * S + 1):
            zT = np.maximum(zT, zi[np.maximum(Yc - d, 0), cols])
        tw = np.clip((zw - zN) / np.maximum(zT - zN, 1e-3), 0, 1)
        # walls read light from smooth maps, sampled at their foot and just inside their top edge: the edge row
        # itself is an anti-aliased staircase and would streak the wall
        aoB, shB = blur(ao, 2.0 * S), blur(sh, 1.5 * S)
        foot, head = np.minimum(Yc + 2 * S, Hm - 1), np.maximum(Yc - 2 * S, 0)
        aoY = ao[Yc, cols]
        aop = np.where(wall, np.clip(0.42 * (1 - tw) ** 1.5 + 0.8 * aoB[foot, cols] * (1 - tw) + 0.05, 0, 1), aoY)
        shp = np.where(wall, shB[foot, cols] * (1 - tw) + shB[head, cols] * tw, sh[Yc, cols])
        zz = np.where(wall, zw, zY) / S
        P = np.stack([np.broadcast_to((cols + 0.5) / S, zY.shape), (Yc + 0.5) / S, zz], -1).astype(np.float32)
        col = self._light(N, P, cv.alb[Yc, cols], cv.spec[Yc, cols], cv.rough[Yc, cols], cv.mat[Yc, cols],
                          cv.trans[Yc, cols], shp, aop)
        # lifted layers on top
        for ly in cv.over:
            col = self._composite_layer(col, ly, cv)
        # room light falls off a little away from the window (upper left)
        yy, xx = np.mgrid[0:Hs, 0:Wm].astype(np.float32)
        xx /= Wm; yy /= Hs
        fall = 1.06 - 0.10 * (0.6 * xx + 0.4 * yy) - 0.10 * ((xx - 0.5) ** 2 + (yy - 0.5) ** 2)
        col *= fall[..., None]
        col = np.maximum(col, 0)
        col = np.where(col < 0.8, col, 0.8 + 0.2 * (1 - np.exp(-(col - 0.8) / 0.2)))   # soft shoulder: whites keep form
        img = np.power(np.clip(col, 0, 1), 1 / 2.2)
        g = np.random.default_rng(self.seed + 7).normal(0, 0.006, img.shape[:2]).astype(np.float32)
        img = np.clip(img + g[..., None], 0, 1)
        im = Image.fromarray((img * 255 + 0.5).astype(np.uint8))
        if S > 1: im = im.resize((self.W, self.H), Image.LANCZOS)
        return im

    def _composite_layer(self, col, ly, cv):
        S, k = cv.S, self.tilt
        b0, a0 = ly.sl[0].start, ly.sl[1].start
        zi = ly.z * S
        valid = ly.z > -100
        h, w = zi.shape
        top = int(np.floor(b0 - k * zi[valid].max())) - 2 if valid.any() else b0
        s0, s1 = max(0, top), min(cv.H, b0 + h)
        if s1 <= s0: return col
        yw = (b0 + np.arange(h, dtype=np.float32))[:, None]
        f = np.where(valid, yw - k * zi, 1e6)
        Y = self._march(f, s0, s1)
        have = Y >= 0
        Yc = np.clip(Y, 0, h - 2)
        cols = np.arange(w)[None, :]
        srow = np.arange(s0, s1, dtype=np.float32)[:, None]
        fY = f[Yc, cols]
        wall = fY < srow - 1.0
        zY = zi[Yc, cols]
        zw = (b0 + Yc + 0.5 - srow) / k
        bottom = zY - ly.thick[Yc, cols] * S
        vis = have & valid[Yc, cols] & (~wall | (zw >= bottom))
        gy, gx = np.gradient(np.where(valid, ly.z, np.nan))
        gx = np.nan_to_num(gx) * S; gy = np.nan_to_num(gy) * S
        nt = np.stack([-gx[Yc, cols], -gy[Yc, cols], np.ones(Yc.shape, np.float32)], -1)
        nw = np.stack([np.zeros(Yc.shape, np.float32), np.ones(Yc.shape, np.float32), np.zeros(Yc.shape, np.float32)], -1)
        N = np.where(wall[..., None], nw, nt)
        N /= np.linalg.norm(N, axis=-1, keepdims=True)
        zz = np.where(wall, zw, zY) / S
        P = np.stack([np.broadcast_to((a0 + cols + 0.5) / S, Yc.shape), (b0 + Yc + 0.5) / S, zz], -1).astype(np.float32)
        z0 = np.zeros(Yc.shape, np.float32)
        lc = self._light(N, P, ly.alb[Yc, cols], ly.spec[Yc, cols], ly.rough[Yc, cols], ly.mat[Yc, cols], z0 + 0.4,
                         z0, z0 + np.where(wall, 0.35, 0.0))
        a = vis.astype(np.float32)[..., None]
        seg = col[s0:s1, a0:a0 + w]
        col[s0:s1, a0:a0 + w] = seg * (1 - a) + lc * a
        return col

    def stage(self, name):
        """snapshot for the draw-on animation: the table as it is now (a copy of every object). Rendered only when
        save() is given a stages_dir, at stage_ss (1x by default, quick)."""
        self.stages.append((name, copy.deepcopy(self.objs)))

    def save(self, path, stages_dir=None, quality=88):
        img = self._render(self.ss)
        if path.lower().endswith(('.jpg', '.jpeg')):
            img.save(path, quality=quality, subsampling=0)
        else:
            img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            now = self.objs
            for i, (name, objs) in enumerate(self.stages):
                self.objs = objs
                self._render(self.stage_ss).save(f"{stages_dir}/{i:02d}_{name}.png")
            self.objs = now
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
