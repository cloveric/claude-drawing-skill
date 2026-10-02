"""artdeco — a 1930s Art Deco / Streamline travel poster: airbrush and frisket on illustration board, printed by
offset lithography (numpy + Pillow only).

Model: the poster artist never draws a line. Every shape is a *frisket* -- a sheet of masking film cut with a knife
and laid on the board -- and the colour is sprayed over it with an airbrush, so each shape has a perfectly crisp
edge and an inside that is one smooth gradient. Form comes only from light and dark: a tower is a flat cut-out
whose face is sprayed darker on one side and lighter on the other, a cylinder gets a hot highlight streak along
one shoulder and a band of reflected light under its belly, a sky is one long fade.
  spray      `spray(mask, colour, density)` is one pass of the airbrush over a frisket. Density 0..1 per pixel is
             how much paint lands. Airbrush paint arrives as a fog of tiny droplets, so wherever the coat is thin
             (the tail of a fade) it is speckled -- the stipple is a fixed per-board noise multiplied by d(1 - d),
             zero where the coat is solid or absent. Gradients are built from passes: `fade()` (linear, between two
             points, through colour stops) and `glow()` (radial).
  sky        `sky()` fades top to bottom; `burst()` is the Deco sunburst: alternating light and dark wedges
             around a centre, sprayed through a fan-shaped frisket, strongest near the centre and fading outward,
             with a soft radial glow; `moon()` a disc with an off-centre radial fade (a sphere) and a halo;
             `searchlight()` a long wedge of light whose density falls along its length.
  city       `tower(x, base, tiers)` is a stepped skyscraper in elevation: each set-back tier is its own frisket,
             sprayed as a slightly cylindrical face (dark on the shadow side, bright on the lit side) with vertical
             fluting, a rim of light along each ledge, rows of lit and dark windows (`windows`) or lit slit strips
             (`slits`); `spire`, `crown` (stepped fan of arches) and `clock(...)` sit on top. `far=` pushes a tower
             into the haze: lighter, bluer, flatter.
  water      `water(horizon)` sprays the river and then mirrors whatever is already above the horizon into it,
             broken into horizontal ripple dashes that get longer and sparser toward the viewer.
  machines   `camera()` + `express()` render a streamlined train on an arched viaduct from a little 3D scene
             (signed distance fields, sphere-traced in numpy, rows above the train skipped, only edge pixels
             supersampled). The renderer does not light it like a photograph: each material has a poster ramp
             (shadow -> mid -> light colour) indexed by a half-Lambert term, plus an airbrushed highlight streak,
             moon rim light and a band of reflected light underneath -- the way an illustrator models a
             cylinder. The result comes back as layers so it can be laid in like the artist does: `frisket(r)`
             (flat base colours), `model(r)` (form sprays), `lights(r)` (lit windows, headlamp, beam, bloom and
             their reflections in the river).
  type       `lettering(s, ...)` sets a geometric Deco display alphabet built here from rectangles, diagonals and
             elliptical bowls: thick stems and down-strokes, hairline cross-strokes, a high waist; filled with a
             sprayed metallic fade and an optional cast block shadow. `caption()` is wide-tracked geometric sans
             (Futura, else the system sans). `border()` is a double gold rule with stepped corners.
  print      `finish()` lays the lithographic print over everything: paper tone and tooth, a whisper of grain, a
             faint warm cast, very slight edge vignette.
Coordinates are pixels, y down; angles are degrees counter-clockwise from 3 o'clock. World units of the 3D scene
are metres (y up).

    from artdeco import ArtDeco
    a = ArtDeco(1920, 1080, seed=3)
    a.sky([(0, '#0a1530'), (1, '#3f8f8a')], bottom=690)
    a.burst(1250, 430, rays=44)
    a.moon(1250, 430, 110)
    a.tower(1500, 690, [(160, 220), (120, 120), (70, 80)], spire=120)
    a.water(690)
    a.camera(f=1500, cx=960, horizon=690, height=12.5)
    r = a.express(nose=(-7.4, 21), vp_x=1450)
    a.frisket(r); a.model(r); a.lights(r)
    a.lettering('NIGHT EXPRESS', 110, 300, 150)
    a.finish(); a.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep, load_font, polygon_mask

NAVY, MIDNIGHT, TEAL, JADE = '#0e1d3a', '#08112a', '#2f6f78', '#5fa39a'
GOLD, BRASS, IVORY, CREAM = '#d9ac55', '#a9772f', '#f6ead0', '#efdcb2'
MAROON, CRIMSON, WARM = '#5a1424', '#a82a33', '#ffd585'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def ramp(t, stops):
    """t (any shape) through colour stops [(pos, colour), ...] -> (..., 3)"""
    t = np.asarray(t, np.float32)
    pos = np.array([p for p, _ in stops], np.float32)
    col = np.stack([_c(c) for _, c in stops])
    out = np.empty(t.shape + (3,), np.float32)
    for k in range(3):
        out[..., k] = np.interp(t, pos, col[:, k])
    return out


# ---------------------------------------------------------------- the Deco display alphabet
# unit glyphs: cap height 1, y up from the baseline. Thick stems and down-strokes (T), hairline cross-strokes (t),
# a high waist for E F H B P R. Each glyph = (advance width, [polygons]).
_T, _t, _WAIST = 0.2, 0.055, 0.6


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _diag(xb, xt, w, yb=0.0, yt=1.0):
    """slanted stroke of horizontal thickness w; left edge at xb (bottom) and xt (top)"""
    return [(xb, yb), (xb + w, yb), (xt + w, yt), (xt, yt)]


def _ring(cx, cy, rx, ry, a0=0, a1=360, tl=_T, tr=_T, tb=_t, tt=_t, n=96):
    """elliptical bowl between angles a0..a1 (degrees ccw); side thicknesses left/right/bottom/top"""
    a = np.radians(np.linspace(a0, a1, n))
    icx, icy = cx + (tl - tr) / 2, cy + (tb - tt) / 2
    irx, iry = rx - (tl + tr) / 2, ry - (tb + tt) / 2
    outer = [(cx + rx * np.cos(t), cy + ry * np.sin(t)) for t in a]
    inner = [(icx + irx * np.cos(t), icy + iry * np.sin(t)) for t in a[::-1]]
    if a1 - a0 >= 360:
        return [outer, inner]                       # drawn as outer filled, inner cut (see _glyph_mask)
    return [outer + inner]


def _bowl_right(xs, xc, yb, yt, rx, tx=_T):
    """D/P/B bowl: arms from the stem at x=xs out to xc, then a half ring bulging right"""
    cy, ry = (yb + yt) / 2, (yt - yb) / 2
    return [_rect(xs - 0.01, yt - _t, xc + 0.005, yt), _rect(xs - 0.01, yb, xc + 0.005, yb + _t)] + \
        _ring(xc, cy, rx, ry, -90, 90, tl=tx, tr=tx, tb=_t, tt=_t)


def _glyph(ch):
    T, t, W = _T, _t, _WAIST
    if ch == 'A':
        wd, ax = 0.9, 0.45
        right = _diag(wd - T * 1.15, ax - T / 2, T * 1.15)
        left = _diag(0.0, ax - T / 2, t * 1.25)
        yb, yt = 0.27, 0.27 + t
        xl = lambda y: t * 1.25 + (ax - T / 2) * y
        xr = lambda y: (wd - T * 1.15) + (ax - T / 2 - (wd - T * 1.15)) * y
        bar = [(xl(yb) - 0.01, yb), (xr(yb) + 0.01, yb), (xr(yt) + 0.01, yt), (xl(yt) - 0.01, yt)]
        return wd, [right, left, bar]
    if ch == 'B':
        return 0.7, [_rect(0, 0, T, 1)] + _bowl_right(T, 0.37, W - t / 2, 1.0, 0.26, T * 0.85) + \
            _bowl_right(T, 0.40, 0.0, W + t / 2, 0.30)
    if ch == 'C':
        return 0.84, _ring(0.42, 0.5, 0.42, 0.5, 42, 318)
    if ch == 'D':
        return 0.78, [_rect(0, 0, T, 1)] + _bowl_right(T, 0.32, 0, 1, 0.46)
    if ch == 'E':
        return 0.6, [_rect(0, 0, T, 1), _rect(T - 0.01, 1 - t, 0.6, 1), _rect(T - 0.01, W - t / 2, 0.5, W + t / 2),
                     _rect(T - 0.01, 0, 0.6, t)]
    if ch == 'F':
        return 0.58, [_rect(0, 0, T, 1), _rect(T - 0.01, 1 - t, 0.58, 1), _rect(T - 0.01, W - t / 2, 0.48, W + t / 2)]
    if ch == 'G':
        return 0.86, _ring(0.43, 0.5, 0.43, 0.5, 42, 360) + [_rect(0.47, 0.5 - t, 0.86, 0.5),
                                                             _rect(0.86 - T, 0.12, 0.86, 0.5)]
    if ch == 'H':
        return 0.78, [_rect(0, 0, T, 1), _rect(0.78 - T, 0, 0.78, 1), _rect(T - 0.01, W - t / 2, 0.79 - T, W + t / 2)]
    if ch == 'I':
        return T, [_rect(0, 0, T, 1)]
    if ch == 'J':
        return 0.56, [_rect(0.56 - T, 0.28, 0.56, 1)] + _ring(0.28, 0.28, 0.28, 0.28, 180, 360, tl=t * 1.4, tr=T)
    if ch == 'K':
        return 0.78, [_rect(0, 0, T, 1), _diag(T - 0.03, 0.78 - t * 1.4, t * 1.4, 0.36, 1.0),
                      _diag(0.78 - T * 1.1, T - 0.04, T * 1.1, 0.0, 0.62)]
    if ch == 'L':
        return 0.58, [_rect(0, 0, T, 1), _rect(T - 0.01, 0, 0.58, t)]
    if ch == 'M':
        wd = 1.02
        return wd, [_rect(0, 0, t * 1.4, 1), _diag(wd / 2 - T * 0.55, 0.0, T * 1.1),
                    _diag(wd / 2 - t * 0.7, wd - T - t * 0.4, t * 1.4), _rect(wd - T, 0, wd, 1)]
    if ch == 'N':
        wd = 0.8
        return wd, [_rect(0, 0, t * 1.4, 1), _diag(wd - T * 1.1, 0.0, T * 1.1), _rect(wd - t * 1.4, 0, wd, 1)]
    if ch == 'O':
        return 0.94, _ring(0.47, 0.5, 0.47, 0.5)
    if ch == 'P':
        return 0.66, [_rect(0, 0, T, 1)] + _bowl_right(T, 0.37, W - t / 2 - 0.03, 1.0, 0.29, T * 0.95)
    if ch == 'Q':
        return 0.96, _ring(0.47, 0.5, 0.47, 0.5) + [_diag(0.80, 0.52, T * 0.8, -0.08, 0.3)]
    if ch == 'R':
        return 0.74, [_rect(0, 0, T, 1)] + _bowl_right(T, 0.35, W - t / 2 - 0.03, 1.0, 0.29, T * 0.95) + \
            [_diag(0.74 - T * 1.1, 0.25, T * 1.1, 0.0, W - 0.02)]
    if ch == 'S':
        wd = 0.68
        return wd, _ring(wd / 2, 0.75 - t / 4, wd / 2 - 0.02, 0.25 + t / 4, 25, 270, tl=T * 0.95, tr=t * 1.4) + \
            _ring(wd / 2, 0.25 + t / 4, wd / 2, 0.25 + t / 4, -155, 90, tl=t * 1.4, tr=T)
    if ch == 'T':
        return 0.72, [_rect(0, 1 - t * 1.5, 0.72, 1), _rect(0.36 - T / 2, 0, 0.36 + T / 2, 1)]
    if ch == 'U':
        return 0.78, [_rect(0, 0.32, T, 1), _rect(0.78 - t * 1.4, 0.32, 0.78, 1)] + \
            _ring(0.39, 0.32, 0.39, 0.32, 180, 360, tl=T, tr=t * 1.4)
    if ch == 'V':
        wd = 0.86
        return wd, [_diag(wd / 2 - T * 0.55, 0.0, T * 1.1), _diag(wd / 2 - t * 0.7, wd - t * 1.4, t * 1.4)]
    if ch == 'W':
        wd = 1.26
        return wd, [_diag(0.3 - T * 0.5, 0.0, T * 1.0), _diag(0.3 - t * 0.7, 0.63 - t * 0.7, t * 1.4),
                    _diag(0.96 - T * 0.5, 0.63 - T * 0.5, T * 1.0), _diag(0.96 - t * 0.7, wd - t * 1.4, t * 1.4)]
    if ch == 'X':
        wd = 0.82
        return wd, [_diag(wd - T * 1.1, 0.0, T * 1.1), _diag(0.0, wd - t * 1.4, t * 1.4)]
    if ch == 'Y':
        wd = 0.82
        return wd, [_diag(wd / 2 - T / 2, 0.0, T, 0.46, 1.0), _diag(wd / 2 - t * 0.7, wd - t * 1.4, t * 1.4, 0.46, 1.0),
                    _rect(wd / 2 - T / 2, 0, wd / 2 + T / 2, 0.47)]
    if ch == 'Z':
        wd = 0.72
        return wd, [_rect(0, 1 - t, wd, 1), _rect(0, 0, wd, t), _diag(0.0, wd - T * 1.1, T * 1.1, t * 0.5, 1 - t * 0.5)]
    if ch == '-':
        return 0.42, [_rect(0.04, 0.46, 0.38, 0.46 + t * 1.2)]
    if ch in '·.':
        return 0.3, [[(0.15, 0.4), (0.25, 0.5), (0.15, 0.6), (0.05, 0.5)]] if ch == '·' else [_rect(0.05, 0, 0.05 + T * 0.8, T * 0.8)]
    if ch == ' ':
        return 0.42, []
    return None


# ---------------------------------------------------------------- signed distance helpers for the 3D scene
def _rbox2(x, y, bx, by, r):
    qx = np.abs(x) - bx + r
    qy = np.abs(y) - by + r
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def _ext(d2, du):
    """combine a 2D section distance with a distance along the extrusion axis"""
    return np.hypot(np.maximum(d2, 0), np.maximum(du, 0)) + np.minimum(np.maximum(d2, du), 0)


class _Render:
    """layers of an `express()` render, all full-canvas: alpha, base, shaded, emissive, depth"""
    pass


class ArtDeco:
    def __init__(self, W=1920, H=1080, seed=0, grain=1.0):
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.img = np.zeros((H, W, 3), np.float32)
        self.speck = self.rng.standard_normal((H, W)).astype(np.float32) * grain   # the airbrush's droplet fog
        self.stages = []
        self.yy, self.xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.cam = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ airbrush
    def spray(self, mask, colour, density=1.0, grain=1.0, blend='paint'):
        """one pass of the airbrush through a frisket: mask * density = paint coverage per pixel.
        colour may be one colour or a (H, W, 3) field. Thin coats are speckled (droplets)."""
        d = np.clip(np.asarray(mask, np.float32) * density, 0, 1)
        if grain:
            d = np.clip(d + self.speck * (0.2 * grain) * d * (1 - d), 0, 1)
        col = _c(colour) if isinstance(colour, str) or np.ndim(colour) == 1 else colour
        if blend == 'screen':
            self.img = 1 - (1 - self.img) * (1 - d[..., None] * col)
        elif blend == 'add':
            self.img = np.minimum(self.img + d[..., None] * col, 1.5)
        else:
            self.img = self.img * (1 - d[..., None]) + col * d[..., None]

    def fade(self, mask, stops, p0, p1, grain=1.0):
        """linear gradient through colour stops from point p0 (pos 0) to p1 (pos 1), sprayed over mask"""
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L2 = dx * dx + dy * dy + 1e-6
        t = ((self.xx - p0[0]) * dx + (self.yy - p0[1]) * dy) / L2
        t = np.clip(t + self.speck * 0.006 * grain, 0, 1)
        self.spray(mask, ramp(t, stops), grain=grain)

    def glow(self, cx, cy, r, colour, strength=1.0, power=2.0, mask=1.0, blend='screen'):
        """radial airbrush glow: soft disc of light falling off to zero at radius r"""
        d = np.hypot(self.xx - cx, self.yy - cy) / r
        a = np.clip(1 - d, 0, 1) ** power * strength
        self.spray(a * mask, colour, grain=0.6, blend=blend)

    def rect(self, x0, y0, x1, y1):
        """anti-aliased rectangle frisket (fractional edges)"""
        cx = np.clip(np.minimum(self.xx + 1 - x0, x1 - self.xx), 0, 1)
        cy = np.clip(np.minimum(self.yy + 1 - y0, y1 - self.yy), 0, 1)
        return (cx * cy).astype(np.float32)

    def poly(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=4)

    def disc(self, cx, cy, r):
        return np.clip(r - np.hypot(self.xx + 0.5 - cx, self.yy + 0.5 - cy) + 0.5, 0, 1).astype(np.float32)

    # ------------------------------------------------------------ sky
    def sky(self, stops, top=0, bottom=None):
        """the long airbrushed fade of the night sky, top -> bottom"""
        bottom = self.H if bottom is None else bottom
        self.fade(1.0, stops, (0, top), (0, bottom))

    def burst(self, cx, cy, rays=44, contrast=0.16, reach=1500, colour='#bfe3d6', dark='#06102a', glow=0.5,
              phase=0.0, taper=0.35, bottom=None):
        """Deco sunburst: alternating light and dark wedges around (cx, cy). The light wedges are sprayed through
        a fan-shaped frisket and are a little wider near the centre (taper), contrast falls off with distance.
        bottom: row where the frisket stops (the horizon)."""
        dx, dy = self.xx - cx, self.yy - cy
        r = np.hypot(dx, dy) + 1e-3
        th = np.arctan2(dy, dx) + np.radians(phase)
        n = rays / 2
        s = np.sin(n * th)
        w = n / r * 1.2                                  # d(sin)/dpx -> 1 px anti-aliasing at any radius
        bias = taper * np.exp(-r / (reach * 0.25))       # light wedges widen toward the centre
        on = np.clip(0.5 + (s + bias) / (2 * w), 0, 1)
        fall = np.exp(-r / reach) * smoothstep(0, 60, r)
        clip = 1.0 if bottom is None else np.clip(bottom - self.yy, 0, 1)
        self.spray(on * fall * contrast * 2.2 * clip, colour, grain=0.45, blend='screen')
        self.spray((1 - on) * fall * contrast * 1.4 * clip, dark, grain=0.45)
        if glow:
            self.glow(cx, cy, reach * 0.55, colour, strength=glow * 0.55, power=2.2, mask=clip)

    def moon(self, cx, cy, r, stops=((0, '#fff8e2'), (0.55, '#f3dfa6'), (1, '#c99b4f')), halo='#f6e6b0',
             halo_r=2.6, halo_strength=0.55, light=(-0.35, -0.4)):
        """a full moon: disc frisket, radial fade off-centre toward the light (reads as a sphere), soft halo,
        and two or three faint airbrushed maria"""
        self.glow(cx, cy, r * halo_r, halo, strength=halo_strength, power=2.4)
        m = self.disc(cx, cy, r)
        lx, ly = cx + light[0] * r, cy + light[1] * r
        t = np.clip(np.hypot(self.xx - lx, self.yy - ly) / (r * 1.6), 0, 1)
        limb = smoothstep(0.75, 1.0, np.hypot(self.xx - cx, self.yy - cy) / r)
        self.spray(m, ramp(np.clip(t * 0.85 + limb * 0.25, 0, 1), stops), grain=0.6)
        rr = np.random.default_rng(self._seed())
        for k in range(5):                                               # maria: soft, low-contrast sprays
            a, d = rr.uniform(0, 2 * np.pi), rr.uniform(0.1, 0.55) * r
            mx, my, mr = cx + np.cos(a) * d, cy + np.sin(a) * d, rr.uniform(0.2, 0.36) * r
            blob = np.clip(1 - np.hypot(self.xx - mx, (self.yy - my) * 1.25) / mr, 0, 1)
            self.spray(m * smoothstep(0, 1, blob) * 0.13, '#c49a5a', grain=0.25)

    def searchlight(self, x, y, angle, length, spread=2.2, colour='#d9f0e4', strength=0.32):
        """a searchlight beam: wedge from (x, y) at `angle`, half-angle `spread`, fading along its length"""
        a = np.radians(angle)
        ux, uy = np.cos(a), -np.sin(a)
        dx, dy = self.xx - x, self.yy - y
        along = dx * ux + dy * uy
        across = np.abs(-dx * uy + dy * ux)
        half = np.tan(np.radians(spread)) * np.maximum(along, 0) + 2.5
        edge = np.clip(half - across + 0.5, 0, 1) * (along > 0)
        core = np.clip(1 - across / (half + 1e-3), 0, 1) ** 0.6
        fall = np.clip(1 - along / length, 0, 1) ** 1.3
        self.spray(edge * (0.55 + 0.45 * core) * fall * strength, colour, grain=1.2, blend='screen')

    # ------------------------------------------------------------ city
    def tower(self, x, base, tiers, body=('#0b1a33', '#183554', '#2f5c78'), rim='#e2be6a', light=1,
              flutes=0, windows=0.0, slits=0, win=WARM, far=0.0, haze='#4f8f8c', spire=0, spire_w=None,
              ledge=3.0, seed=None, mast=0, top_windows=True):
        """a stepped skyscraper in elevation. tiers = [(width, height), ...] bottom -> top, centred on x.
        Each tier is a frisket sprayed as a slightly round face (shadow side -> lit side, `light` = +1 lit from the
        right), with `flutes` vertical pilasters, a rim of light on each ledge, lit windows (`windows` = share
        of windows lit) or `slits` continuous lit strips. far 0..1 mixes everything toward the haze colour.
        Returns the top centre (x, y) of the top tier."""
        rr = np.random.default_rng(self._seed() if seed is None else seed)
        hz = _c(haze)
        cols = [(1 - far) * _c(c) + far * hz for c in body]
        rimc = (1 - far * 0.8) * _c(rim) + far * 0.8 * hz
        winc = (1 - far * 0.6) * _c(win) + far * 0.6 * hz
        y = float(base)
        for i, (w, h) in enumerate(tiers):
            x0, x1, y0, y1 = x - w / 2, x + w / 2, y - h, y
            m = self.rect(x0, y0, x1, y1)
            u = np.clip((self.xx - x0) / max(w, 1), 0, 1)
            if light < 0: u = 1 - u
            sh = 0.12 + 0.88 * u ** 1.4                                   # round face: dark side -> lit side
            if flutes:
                fu = (u * flutes) % 1.0
                sh = sh * (0.84 + 0.16 * np.clip(fu * 1.6, 0, 1)) + 0.05 * smoothstep(0.75, 1.0, fu)
            sh = sh * (0.9 + 0.1 * np.clip((self.yy - y0) / max(h, 1), 0, 1))  # city glow from below
            st = [(0, cols[0]), (0.55, cols[1]), (1, cols[2])]
            self.spray(m, ramp(np.clip(sh, 0, 1), st), grain=0.8)
            # windows
            lit_here = top_windows or i < len(tiers) - 1
            if windows > 0 and w > 18 and lit_here:
                cw = max(6.0, w / max(3, int(w / 13)))
                rh = cw * 1.25
                nx, ny = int(w / cw), int((h - rh * 0.6) / rh)
                ox = x0 + (w - nx * cw) / 2
                lit = np.zeros((self.H, self.W), np.float32)
                for jx in range(nx):
                    for jy in range(ny):
                        if rr.random() > windows: continue
                        wx0 = ox + jx * cw + cw * 0.3
                        wy0 = y0 + rh * 0.5 + jy * rh
                        a = rr.uniform(0.55, 1.0)
                        lit += self.rect(wx0, wy0, wx0 + cw * 0.42, wy0 + rh * 0.42) * a
                self.spray(np.clip(lit, 0, 1) * m, winc, grain=0.5)
            if slits and w > 18 and lit_here:
                for k in range(slits):
                    sx = x0 + w * (k + 0.5) / slits
                    sm = self.rect(sx - 1.6, y0 + h * 0.08, sx + 1.6, y1 - h * 0.06)
                    gy = np.clip((self.yy - y0) / max(h, 1), 0, 1)
                    self.spray(sm * (0.35 + 0.65 * gy) * rr.uniform(0.6, 1.0), winc, grain=0.6)
            # ledge catching the light (top surface of the set-back)
            if ledge:
                lm = self.rect(x0, y0, x1, y0 + ledge) * (0.45 + 0.55 * u)
                self.spray(lm * (1 - far * 0.6), rimc, grain=0.6)
            y = y0
        top = (x, y)
        if spire:
            sw = spire_w or tiers[-1][0] * 0.28
            m = self.poly([(x - sw / 2, y + 1), (x + sw / 2, y + 1), (x, y - spire)])
            u = np.clip((self.xx - (x - sw / 2)) / sw, 0, 1)
            if light < 0: u = 1 - u
            st = [(0, cols[0]), (0.5, cols[2]), (1, rimc)]
            self.spray(m, ramp(u ** 1.2, st), grain=0.8)
            top = (x, y - spire)
        if mast:
            self.spray(self.rect(x - 1.2, top[1] - mast, x + 1.2, top[1] + 2), cols[2], grain=0)
            self.glow(x, top[1] - mast, 9, '#ff5a4a', strength=0.9, power=1.5)
            self.spray(self.disc(x, top[1] - mast, 2.2), '#ff8a70', grain=0)
        return top

    def crown(self, x, y, w, steps=3, body=('#0b1a33', '#183554', '#2f5c78'), rim='#e2be6a', win=WARM, light=1,
              far=0.0, haze='#4f8f8c'):
        """stepped fan crown: `steps` nested half-discs rising from y, each with radial lit slits (sunburst
        windows) and a rim of light. Returns the apex y."""
        hz = _c(haze)
        cols = [(1 - far) * _c(c) + far * hz for c in body]
        rimc = (1 - far * 0.8) * _c(rim) + far * 0.8 * hz
        r0 = w / 2
        for k in range(steps):
            r = r0 * (1 - k / (steps + 0.6))
            cy = y - k * r0 * 0.34
            m = self.disc(x, cy, r) * (self.yy <= cy)
            u = np.clip((self.xx - (x - r)) / (2 * r), 0, 1)
            if light < 0: u = 1 - u
            self.spray(m, ramp(0.15 + 0.85 * u ** 1.3, [(0, cols[0]), (0.55, cols[1]), (1, cols[2])]), grain=0.8)
            ring = np.clip(r - np.hypot(self.xx - x, self.yy - cy), 0, 1) * np.clip(np.hypot(self.xx - x, self.yy - cy) - (r - 3.0), 0, 1)
            self.spray(ring * (self.yy <= cy) * (0.4 + 0.6 * u), rimc, grain=0.5)
            th = np.arctan2(-(self.yy - cy), self.xx - x)
            n = 9 + 2 * k
            sl = np.clip(0.5 + (np.cos(th * n * 2) - 0.72) * r / 6, 0, 1)
            rad = np.hypot(self.xx - x, self.yy - cy)
            band = ((rad > r * 0.55) & (rad < r * 0.86)).astype(np.float32)
            self.spray(m * sl * band * (1 - far * 0.5) * 0.9, (1 - far * 0.5) * _c(win) + far * 0.5 * hz, grain=0.6)
        return y - (steps - 1) * r0 * 0.34 - r0 * (1 - (steps - 1) / (steps + 0.6))

    def clock(self, cx, cy, r, hour, minute, face='#f3e2b3', hands='#1a1f2e', rim=GOLD):
        """a tower clock: gilt rim, ivory face sprayed as a shallow dome, twelve bar markers, two hands"""
        self.glow(cx, cy, r * 2.2, '#f6deb0', strength=0.35, power=2)
        self.spray(self.disc(cx, cy, r + max(2, r * 0.12)), rim, grain=0.4)
        t = np.clip(np.hypot(self.xx - cx + r * 0.3, self.yy - cy + r * 0.3) / (r * 1.8), 0, 1)
        self.spray(self.disc(cx, cy, r), ramp(t, [(0, '#fffaf0'), (1, '#d9c08a')]), grain=0.4)
        hc = _c(hands)
        for k in range(12):
            a = np.radians(90 - k * 30)
            p0 = (cx + np.cos(a) * r * 0.72, cy - np.sin(a) * r * 0.72)
            p1 = (cx + np.cos(a) * r * 0.9, cy - np.sin(a) * r * 0.9)
            self.spray(self._bar(p0, p1, r * (0.09 if k % 3 == 0 else 0.05)), hc, grain=0)
        am = np.radians(90 - minute * 6)
        ah = np.radians(90 - (hour % 12 + minute / 60) * 30)
        self.spray(self._bar((cx, cy), (cx + np.cos(ah) * r * 0.5, cy - np.sin(ah) * r * 0.5), r * 0.1), hc, grain=0)
        self.spray(self._bar((cx, cy), (cx + np.cos(am) * r * 0.8, cy - np.sin(am) * r * 0.8), r * 0.065), hc, grain=0)
        self.spray(self.disc(cx, cy, r * 0.09), rim, grain=0)

    def _bar(self, p0, p1, w):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = np.hypot(dx, dy) + 1e-6
        nx, ny = -dy / L * w / 2, dx / L * w / 2
        return self.poly([(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)])

    # ------------------------------------------------------------ river
    def water(self, horizon, stops=((0, '#1d4a5a'), (1, '#060d22')), reflect=0.6, dash=(70, 2.2), seed=None):
        """the river: sprayed fade from the horizon down, then the scene above the horizon mirrored into it,
        broken into horizontal ripple dashes (longer and sparser toward the viewer)"""
        H, W = self.H, self.W
        h = int(horizon)
        rows = np.arange(h, H)
        rho = (rows - h).astype(np.float32)
        src = np.clip(h - 1 - rho * 1.0, 0, h - 1).astype(int)
        mir = self.img[src]                                              # (rows, W, 3)
        rr = np.random.default_rng(self._seed() if seed is None else seed)
        # horizontal ripple displacement per row, growing toward the viewer
        amp = 1.5 + rho * 0.035
        off = (np.sin(rho * 0.9 + rr.uniform(0, 6)) * 0.6 + rr.standard_normal(len(rows)) * 0.7) * amp
        xs = np.clip((np.arange(W)[None, :] + off[:, None]).astype(int), 0, W - 1)
        mir = np.take_along_axis(mir, xs[..., None].repeat(3, 2), axis=1)
        # ripple dashes: elongated noise, threshold rising toward the viewer
        brk = self._ripples(len(rows), W, 0.42)
        wt = np.clip(1 - rho / (H - h) * 0.5, 0, 1)[:, None]
        base = ramp((rho / max(1, H - h))[:, None].repeat(W, 1), stops)
        lum = mir @ np.float32([0.3, 0.55, 0.15])
        boost = 0.45 + 1.3 * smoothstep(0.35, 0.85, lum)
        out = base + (mir - base * 0.6) * (reflect * brk * wt * boost)[..., None] * 0.9
        mask = np.zeros((H, W), np.float32)
        mask[h:] = 1
        full = self.img.copy()
        full[h:] = out
        self.spray(mask, full, grain=0.7)
        self.horizon = h

    def _ripples(self, n_rows, W, level):
        """0..1 mask of horizontal ripple dashes for n_rows of river below the horizon: thin and dense at the
        horizon, longer, thicker and sparser toward the viewer"""
        rho = np.arange(n_rows, dtype=np.float32)
        # rows grow with perspective: index the noise by a compressed depth coordinate
        depth = np.sqrt(rho + 4.0) * 9.0
        nr = int(depth[-1]) + 2
        z = noise2d(nr, W // 90 + 2, 2.5, 2, self._seed())
        z = np.asarray(Image.fromarray(z).resize((W, nr), Image.BICUBIC), np.float32)
        lo = np.floor(depth).astype(int); fr = (depth - lo)[:, None]
        zz = z[lo] * (1 - fr) + z[np.minimum(lo + 1, nr - 1)] * fr
        thr = level + 0.12 * (rho / max(1, n_rows))[:, None]
        return smoothstep(thr - 0.04, thr + 0.04, zz).astype(np.float32)

    # ------------------------------------------------------------ 3D: camera and the streamliner on its viaduct
    def camera(self, f=1500.0, cx=None, horizon=None, height=12.5):
        """pin-hole camera at (0, height, 0) looking along +Z, level (the horizon is the row `horizon`)"""
        self.cam = dict(f=float(f), cx=float(self.W / 2 if cx is None else cx),
                        cy=float(self.H / 2 if horizon is None else horizon), h=float(height))

    def project(self, X, Y, Z):
        c = self.cam
        return c['cx'] + c['f'] * X / Z, c['cy'] - c['f'] * (Y - c['h']) / Z

    def express(self, nose=(-7.4, 21.0), vp_x=1450, deck=10.0, cars=9, loco=19.0, car=23.0, gap=1.1,
                nose_len=3.6, rake=2.2, light=(-0.55, 0.62, -0.56), moon=None, top=None, edge_ss=3, max_steps=150):
        """render the streamlined train on an arched viaduct over the river. nose = (X, Z) of the locomotive's
        nose tip on the rails (deck height `deck` above the water); the track runs away toward the vanishing
        point at column vp_x on the horizon. Returns a _Render with alpha/base/shade/emit layers."""
        c = self.cam
        f, cx, cy = c['f'], c['cx'], c['cy']
        d = np.array([(vp_x - cx) / f, 0, 1], np.float32)
        d /= np.linalg.norm(d)
        s = np.array([d[2], 0, -d[0]], np.float32)                     # lateral axis, toward the camera side
        N = np.array([nose[0], deck, nose[1]], np.float32)
        P = dict(d=d, s=s, N=N, deck=deck, cars=cars, loco=loco, car=car, gap=gap, Ln=nose_len,
                 bw=1.55, yb=0.75, yt=2.6, ycut=0.45, yk=1.32, rake=rake)
        P['end'] = loco + gap + cars * (car + gap)
        self._P = P
        P['tip'] = -nose_len * 4                                         # provisional, for the livery mapping

        def surface_a(h):
            # where the nose surface crosses height h on the centre line
            lo, hi = -nose_len * 4 - 10, rake + 1.0
            for _ in range(48):
                mid = (lo + hi) / 2
                dd = self._sd_train(np.float32([mid]), np.float32([0.0]), np.float32([h]))[0][0]
                lo, hi = (mid, hi) if dd > 0 else (lo, mid)
            return hi
        P['tip'] = surface_a(1.6)
        # headlamp: on the nose surface at height 2.35 on the centre line, set just inside it
        P['lamp'] = np.float32([surface_a(2.35) + 0.2, 0.0, 2.35])
        L = np.array(light, np.float32); L /= np.linalg.norm(L)
        if moon is None:
            M = np.array([0.35, 0.45, 0.82], np.float32)
        else:
            M = np.array([(moon[0] - cx) / f, -(moon[1] - cy) / f, 1], np.float32)
        M /= np.linalg.norm(M)
        P['L'], P['M'] = L, M
        # which rows can contain geometry: everything from just above the locomotive roof down
        y_top = int(max(0, (top if top is not None else self.project(N[0], deck + 4.6, N[2])[1] - 30)))
        H, W = self.H, self.W
        ys, xs = np.mgrid[y_top:H, 0:W]
        xs = xs.ravel().astype(np.float32) + 0.5
        ys = ys.ravel().astype(np.float32) + 0.5
        col, alpha, emit, depth, mat = self._shade_px(xs, ys, max_steps)
        # supersample only where the 1x result has an edge
        hh = H - y_top
        colg = col.reshape(hh, W, 3)
        ag = alpha.reshape(hh, W)
        lum = colg @ np.float32([0.3, 0.5, 0.2]) * ag + emit.reshape(hh, W, 3).sum(-1) * 0.3
        e = np.zeros((hh, W), bool)
        gx = np.abs(np.diff(lum, axis=1)) > 0.035
        gy = np.abs(np.diff(lum, axis=0)) > 0.035
        e[:, 1:] |= gx; e[:, :-1] |= gx; e[1:] |= gy; e[:-1] |= gy
        ax = np.abs(np.diff(ag, axis=1)) > 0.01
        ay = np.abs(np.diff(ag, axis=0)) > 0.01
        e[:, 1:] |= ax; e[:, :-1] |= ax; e[1:] |= ay; e[:-1] |= ay
        ei = np.flatnonzero(e.ravel())
        if edge_ss > 1 and ei.size:
            k = edge_ss
            offs = [((i + 0.5) / k - 0.5, (j + 0.5) / k - 0.5) for i in range(k) for j in range(k)]
            acc_c = np.zeros((ei.size, 3), np.float32); acc_a = np.zeros(ei.size, np.float32)
            acc_e = np.zeros((ei.size, 3), np.float32)
            for ox, oy in offs:
                c2, a2, e2, _, _ = self._shade_px(xs[ei] + ox, ys[ei] + oy, max_steps)
                acc_c += c2 * a2[:, None]; acc_a += a2; acc_e += e2
            n = len(offs)
            alpha[ei] = acc_a / n
            col[ei] = acc_c / np.maximum(acc_a, 1e-4)[:, None]
            emit[ei] = acc_e / n
        R = _Render()
        R.y_top = y_top

        def full(a, ch_=None):
            if ch_:
                out = np.zeros((H, W, ch_), np.float32); out[y_top:] = a.reshape(hh, W, ch_)
            else:
                out = np.zeros((H, W), np.float32); out[y_top:] = a.reshape(hh, W)
            return out
        R.alpha = full(alpha)
        R.shade = full(col, 3)
        R.emit = full(emit, 3)
        R.depth = full(np.where(mat > 0, depth, 1e9).astype(np.float32))
        R.mat = full(mat.astype(np.float32))
        R.base = self._base_colours(R.mat)
        R.under = None
        return R

    # ---- the scene as signed distances (local frame: a = metres behind the nose, v = lateral, y = above rails)
    def _local(self, x, y, z):
        P = self._P
        qx, qz = x - P['N'][0], z - P['N'][2]
        a = qx * P['d'][0] + qz * P['d'][2]
        v = qx * P['s'][0] + qz * P['s'][2]
        return a, v, y - P['deck']

    def _sd_train(self, a, v, y):
        """distance to the train + texture coordinates. The body is a flat *core* in the vertical plane v = 0
        -- in the (a, y) plane a strip yb..yt running back from a raked front edge -- dilated by R = half the body
        width and cut flat at the bottom: straight sides, a round roof, a raked prow. In front of the core's
        front edge the a axis is stretched by nose_len / R, which turns the round prow into a long bullet nose
        (stretching only under-estimates distance, so the sphere tracer stays safe). Livery coordinate ys: on
        the nose the heights are squeezed toward yk, so the stripes converge on the prow."""
        P = self._P
        Ln, R, yb, yt, ycut, yk, rake = P['Ln'], P['bw'], P['yb'], P['yt'], P['ycut'], P['yk'], P['rake']
        m = rake / (yt - yb)
        a1 = rake
        yc_ = np.clip(y, yb, yt)
        front = m * (yc_ - yb)
        e = a - front
        a_s = front + np.where(e < 0, e * (R / Ln), e)
        # distance in the (a, y) plane to the core: bottom ray, top ray, raked front edge
        d_bot = np.where(a_s >= 0, np.abs(y - yb), np.hypot(a_s, y - yb))
        d_top = np.where(a_s >= a1, np.abs(y - yt), np.hypot(a_s - a1, y - yt))
        L2 = a1 * a1 + (yt - yb) ** 2
        tt = np.clip((a_s * a1 + (y - yb) * (yt - yb)) / L2, 0, 1)
        d_fr = np.hypot(a_s - tt * a1, y - yb - tt * (yt - yb))
        inside = (y >= yb) & (y <= yt) & (a_s >= front)
        dC = np.where(inside, 0.0, np.minimum(np.minimum(d_bot, d_top), d_fr))
        d_loco = np.maximum(np.sqrt(v * v + dC * dC) - R, np.maximum(ycut - y, a - P['loco']))
        dy = y - yc_
        sec = np.sqrt(v * v + dy * dy) - R
        a0 = a - P['loco'] - P['gap']
        k = np.clip(np.round((a0 - P['car'] / 2) / (P['car'] + P['gap'])), 0, P['cars'] - 1)
        w = a0 - k * (P['car'] + P['gap'])
        du = np.abs(w - P['car'] / 2) - P['car'] / 2
        d_car = np.maximum(_ext(sec + 0.18, du + 0.18) - 0.18, ycut - y)
        dyd = y - np.clip(y, yb + 0.1, yt - 0.1)
        d_dia = np.maximum(np.sqrt(v * v + dyd * dyd) - R * 0.9,
                           np.maximum(ycut + 0.05 - y, np.maximum(P['loco'] - 0.5 - a, a - P['end'])))
        d = np.minimum(np.minimum(d_loco, d_car), d_dia)
        an = np.clip((a1 + 1.0 - a) / (a1 + 1.0 - P['tip']), 0, 1)        # 0 behind the nose .. 1 at the tip
        sc = np.sqrt(np.clip(1 - an ** 2, 0.0025, 1))
        ys = yk + (y - yk) / sc
        return d, v, ys, k, w

    def _sd_viaduct(self, a, v, y):
        P = self._P
        dk = P['deck']
        deck = _rbox2(v, y + 0.7, 3.95, 0.55, 0.05)                    # slab y -1.25 .. -0.15
        par = _rbox2(np.abs(v) - 3.62, y - 0.03, 0.3, 0.23, 0.04)       # low parapets
        wall_v = np.abs(v) - 3.3
        wall_y = np.maximum(y + 1.2, -dk - 1 - y)                       # from below the water up to under the deck
        wall = np.maximum(wall_v, wall_y)
        Pp, R = 15.0, 5.3
        am = np.mod(a, Pp) - Pp / 2
        yac = -2.7 - R
        circ = np.hypot(am, y - yac) - R
        qx, qy = np.abs(am) - R, y - yac
        rect = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0)
        hole = np.minimum(circ, rect)
        wall = np.maximum(wall, -hole)
        ap = np.mod(a + Pp / 2, Pp) - Pp / 2                            # pilasters between the arches + plinths
        p1 = np.maximum(np.maximum(np.abs(ap) - 1.25, np.abs(v) - 3.62), np.maximum(y + 1.25, -dk - 1 - y))
        p2 = np.maximum(np.maximum(np.abs(ap) - 1.75, np.abs(v) - 3.85), np.maximum(y + dk - 1.6, -dk - 1 - y))
        pier = np.minimum(p1, p2)
        rails = _rbox2(np.abs(v) - 0.72, y + 0.08, 0.05, 0.08, 0.0)
        via = np.minimum(np.minimum(deck, par), np.minimum(wall, pier))
        return via, rails

    def _sd_lamp(self, a, v, y):
        lp = self._P['lamp']
        return np.sqrt((a - lp[0]) ** 2 + (v - lp[1]) ** 2 + (y - lp[2]) ** 2) - 0.3

    def _sdf(self, x, y, z):
        a, v, yl = self._local(x, y, z)
        dt = self._sd_train(a, v, yl)[0]
        dv, drl = self._sd_viaduct(a, v, yl)
        return np.minimum(np.minimum(dt, self._sd_lamp(a, v, yl)), np.minimum(dv, drl))

    def _shade_px(self, px, py, max_steps):
        c = self.cam
        f, cx, cy, ch = c['f'], c['cx'], c['cy'], c['h']
        dx = (px - cx) / f; dy = -(py - cy) / f; dz = np.ones_like(px)
        nl = np.sqrt(dx * dx + dy * dy + 1)
        dx /= nl; dy /= nl; dz /= nl
        # rays stop at the water plane (y = 0) or far away
        tw = np.where(dy < -1e-5, ch / np.maximum(-dy, 1e-5), 3000.0).astype(np.float32)
        tmax = np.minimum(tw, 2500.0)
        n = px.size
        t = np.full(n, 0.3, np.float32)
        hit = np.zeros(n, bool)
        alive = np.arange(n)
        pix = 1.0 / f
        for _ in range(max_steps):
            if alive.size == 0: break
            ta = t[alive]
            d = self._sdf(dx[alive] * ta, ch + dy[alive] * ta, dz[alive] * ta)
            h = d < ta * pix * 0.35 + 1e-4
            hit[alive[h]] = True
            tn = ta + d * 0.82
            t[alive] = tn
            keep = (~h) & (tn < tmax[alive])
            alive = alive[keep]
        col = np.zeros((n, 3), np.float32)
        emit = np.zeros((n, 3), np.float32)
        alpha = hit.astype(np.float32)
        mat = np.zeros(n, np.int8)
        hi = np.flatnonzero(hit)
        if hi.size:
            th = t[hi]
            X, Y, Z = dx[hi] * th, ch + dy[hi] * th, dz[hi] * th
            V = -np.stack([dx[hi], dy[hi], dz[hi]], 1)
            cc, ee, mm = self._surface(X, Y, Z, V, th)
            col[hi] = cc; emit[hi] = ee; mat[hi] = mm
        return col, alpha, emit, t, mat

    def _normal(self, X, Y, Z, th):
        e = np.maximum(0.004, th * 0.0006).astype(np.float32)
        k = ((1, -1, -1), (-1, -1, 1), (-1, 1, -1), (1, 1, 1))
        n = np.zeros((X.size, 3), np.float32)
        for kx, ky, kz in k:
            dd = self._sdf(X + kx * e, Y + ky * e, Z + kz * e)
            n[:, 0] += kx * dd; n[:, 1] += ky * dd; n[:, 2] += kz * dd
        return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)

    def _surface(self, X, Y, Z, V, th):
        P = self._P
        n = self._normal(X, Y, Z, th)
        a, v, y = self._local(X, Y, Z)
        dt, vs, ys, kcar, wcar = self._sd_train(a, v, y)
        dv, drl = self._sd_viaduct(a, v, y)
        dl = self._sd_lamp(a, v, y)
        ds = np.stack([dt, dl, dv, drl], 1)
        which = np.argmin(ds, 1)                       # 0 train, 1 lamp, 2 viaduct, 3 rails
        L, M = P['L'], P['M']
        ndl = n @ L
        ndm = n @ M
        ndv = np.clip(np.sum(n * V, 1), 0, 1)
        k = 0.5 + 0.5 * ndl                            # half-Lambert: the airbrush modelling term
        Hh = L[None, :] + V
        Hh /= np.linalg.norm(Hh, axis=1, keepdims=True)
        spec = smoothstep(0.90, 0.985, np.sum(n * Hh, 1))
        rim = (1 - ndv) ** 2.2 * np.clip(ndm + 0.25, 0, 1)
        bounce = np.clip(-n[:, 1], 0, 1)
        col = np.zeros((X.size, 3), np.float32)
        emit = np.zeros((X.size, 3), np.float32)
        mat = np.zeros(X.size, np.int8)
        # ---- train
        it = which == 0
        if it.any():
            ktr = k[it]; yy = ys[it]; aa = a[it]
            side = np.abs(n[it] @ P['s']) > 0.55
            t = np.clip(0.08 + 0.92 * ktr ** 1.25, 0, 1)
            body = ramp(t, [(0, '#16070d'), (0.35, '#4a101d'), (0.62, '#8b2030'), (0.84, '#c4473f'), (1, '#f1a172')])
            skirt = ramp(t, [(0, '#07090f'), (0.5, '#1d2232'), (0.85, '#4b5368'), (1, '#8a93a6')])
            gold = ramp(t, [(0, '#2a1a08'), (0.4, '#7b5519'), (0.7, '#cf9f45'), (0.9, '#f3d58b'), (1, '#fff3cf')])
            cream = ramp(t, [(0, '#3a2a1c'), (0.35, '#8c6f4c'), (0.62, '#d8bf93'), (0.84, '#f3e3c0'), (1, '#fff8e8')])
            cc = body.copy()
            is_skirt = yy < 1.0
            cc[is_skirt] = skirt[is_skirt]
            cap = aa < P['tip'] * 0.86 + P['rake'] * 0.14                # nose cap: plain enamel, stripes end before it
            band = (yy > 1.95) & (yy < 3.15) & ~cap
            cc[band] = cream[band]
            stripe = (((yy > 1.7) & (yy < 1.84)) | ((yy > 3.26) & (yy < 3.36)) | ((yy > 1.12) & (yy < 1.2))) & ~cap
            cc[stripe] = gold[stripe]
            m = np.full(it.sum(), 1, np.int8)
            m[is_skirt] = 4; m[band] = 8; m[stripe] = 5
            # car windows (sleeping cars: some blinds drawn) and the cab glass
            kk = kcar[it]; ww = wcar[it]
            on_car = (aa > P['loco'] + P['gap']) & (aa < P['end'])
            wpos = (ww - 1.6) / 2.05
            wi = np.floor(wpos)
            wf = wpos - wi
            in_win = on_car & side & (ww > 1.6) & (ww < P['car'] - 1.6) & (wf > 0.16) & (wf < 0.84) & (yy > 2.05) & (yy < 3.05)
            hsh = np.mod(np.sin(kk * 12.9898 + wi * 78.233) * 43758.5453, 1.0)
            blind = 2.05 + np.where(hsh < 0.3, 0.55, np.where(hsh < 0.45, 0.9, 1.0)) * 1.0
            dark = hsh > 0.86
            lit = in_win & ~dark
            glass = ramp(t, [(0, '#05070d'), (0.6, '#14203a'), (1, '#3a5578')])
            cc[in_win] = glass[in_win]
            ev = np.zeros((it.sum(), 3), np.float32)
            gy = np.clip((yy - 2.05) / 1.0, 0, 1)
            warm = ramp(gy, [(0, '#fff0b8'), (1, '#f7b553')])
            blinded = lit & (yy > blind)
            ev[lit] = warm[lit] * 1.05
            ev[blinded] = _c('#d9802f') * 0.62
            m[in_win] = 6
            # cab: a rounded side window in the cream band just behind the nose, glass reflecting the sky
            cu = (aa - 1.55) / 1.05; cv = (yy - 2.6) / 0.36
            cab = side & (np.abs(cu) ** 3 + np.abs(cv) ** 3 < 1)
            sky = ramp(np.clip(0.5 - cv * 0.5, 0, 1), [(0, '#08101e'), (0.55, '#1c3d50'), (1, '#6aa9a2')])
            cc[cab] = sky[cab]
            ev[cab] = _c('#ffcf7a') * 0.08
            m[cab] = 6
            # lamp bezel (chrome ring round the headlamp)
            lp = P['lamp']
            rl = np.sqrt((aa - lp[0]) ** 2 + (v[it] - lp[1]) ** 2 + (y[it] - lp[2]) ** 2)
            bez = rl < 0.47
            chrome = ramp(t, [(0, '#1a1d26'), (0.5, '#6f7787'), (0.85, '#d9dde3'), (1, '#ffffff')])
            cc[bez] = chrome[bez]
            ny = n[it, 1]
            streak = np.exp(-((ny - 0.62) / 0.09) ** 2) * 0.55 + np.exp(-((ny + 0.42) / 0.07) ** 2) * 0.12
            cc = cc + streak[:, None] * np.where(m[:, None] == 8, _c('#fff3dc') * 0.35, _c('#ffb08a') * 0.6) * (1 - is_skirt[:, None] * 0.6)
            sp = spec[it][:, None]
            spcol = np.where(m[:, None] == 5, _c('#fff6dc'), _c('#ffd9b8'))
            cc = cc + sp * spcol * np.where(m[:, None] == 6, 0.7, 0.55)
            cc = cc + rim[it][:, None] * _c('#8fd0c8') * 0.55
            cc = cc + bounce[it][:, None] * _c('#2b6a74') * 0.22
            col[it] = cc; emit[it] = ev; mat[it] = m
        il = which == 1
        if il.any():
            col[il] = _c('#fffbe8')
            emit[il] = _c('#fff4cf') * 0.85
            mat[il] = 7
        # the headlamp lights the deck and rails ahead of the train (a cone along -a, tipped slightly down)
        lp = P['lamp']
        qa, qv, qy = a - lp[0], v - lp[1], y - lp[2]
        ql = np.sqrt(qa * qa + qv * qv + qy * qy) + 1e-4
        ax_ = np.float32([-0.995, 0.0, -0.1]); ax_ /= np.linalg.norm(ax_)
        cosang = (qa * ax_[0] + qv * ax_[1] + qy * ax_[2]) / ql
        nl_a, nl_v = n @ P['d'], n @ P['s']
        lam = np.clip(-(nl_a * qa + nl_v * qv + n[:, 1] * qy) / ql, 0, 1)
        spill = smoothstep(np.cos(np.radians(15)), np.cos(np.radians(4)), cosang) * np.clip(lam * 5, 0, 1) * \
            np.clip(1 - ql / 70, 0, 1) ** 1.2
        iv = which == 2
        if iv.any():
            t = np.clip(0.06 + 0.94 * k[iv] ** 1.1, 0, 1)
            cc = ramp(t, [(0, '#050b18'), (0.45, '#11243a'), (0.75, '#24465c'), (1, '#4f7d86')])
            up = np.clip(n[iv, 1], 0, 1)
            cc = cc + up[:, None] * _c('#2c5560') * 0.25 + rim[iv][:, None] * _c('#6fb8b0') * 0.35
            cc = cc + spill[iv][:, None] * _c('#d9b06a') * 0.55
            col[iv] = cc; mat[iv] = 2
        ir = which == 3
        if ir.any():
            col[ir] = ramp(np.clip(k[ir] + spec[ir], 0, 1), [(0, '#0b0e16'), (0.6, '#5a6274'), (1, '#e9eef2')])
            col[ir] += spill[ir][:, None] * _c('#ffe2a8') * 1.1
            mat[ir] = 3
        # air between us and far objects: fade toward the glow of the city at the horizon
        fog = (1 - np.exp(-th / 260.0)) ** 1.2
        fogc = _c('#3f7d82')
        col = col * (1 - fog[:, None] * 0.85) + fogc * fog[:, None] * 0.85
        emit = emit * (1 - fog[:, None] * 0.45)
        return col, emit, mat

    def _base_colours(self, mat):
        """flat base coat per material (what the first spray through each frisket looks like)"""
        out = np.zeros(mat.shape + (3,), np.float32)
        for m, cc in ((1, '#7a1c2b'), (2, '#1c3449'), (3, '#4a5262'), (4, '#2a2f3d'), (5, '#b88a3c'),
                      (6, '#141d30'), (7, '#e8dcc0'), (8, '#cdb58a')):
            out[mat == m] = _c(cc)
        return out

    def frisket(self, R):
        """first pass: every machine shape cut and sprayed flat in its base colour"""
        R.under = self.img.copy()
        self.img = R.under * (1 - R.alpha[..., None]) + R.base * R.alpha[..., None]

    def model(self, R):
        """second pass: form shading (ramps, highlight streaks, rim and reflected light)"""
        if R.under is None: R.under = self.img.copy()
        sh = R.shade.copy()
        sh = np.clip(sh + self.speck[..., None] * 0.006, 0, 1.2)
        self.img = R.under * (1 - R.alpha[..., None]) + sh * R.alpha[..., None]

    def lights(self, R, beam=True, beam_len=900, bloom=1.0, reflect=True):
        """third pass: lit windows and headlamp, headlamp beam, bloom, the lights' reflections in the river"""
        e = R.emit
        lum = e.max(-1)
        self.img = self.img * (1 - np.clip(lum, 0, 1)[..., None]) + e
        P = self._P
        lp = P['lamp']
        # lamp in world coordinates
        wpos = P['N'] + P['d'] * lp[0] + P['s'] * lp[1] + np.array([0, lp[2], 0], np.float32)
        lx, ly = self.project(*wpos)
        if beam:
            tip = wpos - P['d'] * min(60.0, 0.6 * wpos[2] / P['d'][2])
            bx, by = self.project(*tip)
            ang = np.degrees(np.arctan2(-(by - ly), bx - lx))
            self.searchlight(lx, ly, ang, beam_len, spread=8.5, colour='#fff1c8', strength=0.42)
            self.searchlight(lx, ly, ang, beam_len * 0.7, spread=3.6, colour='#fff6dc', strength=0.4)
        if bloom:
            g = blur(lum, 3) * 0.6 + blur(lum, 14) * 0.5 + blur(lum, 40) * 0.35
            self.spray(np.clip(g * bloom, 0, 1), '#ffd58a', grain=0.4, blend='screen')
            self.glow(lx, ly, 80, '#fff3d0', strength=0.45, power=2.6)
            self.glow(lx, ly, 10, '#ffffff', strength=0.8, power=1.4)
            # four-point glint on the lamp
            for ang in (0, 90):
                aa = np.radians(ang)
                ux, uy = np.cos(aa), np.sin(aa)
                dx, dy = self.xx - lx, self.yy - ly
                al = np.abs(dx * ux + dy * uy); ac = np.abs(-dx * uy + dy * ux)
                self.spray(np.clip(1 - al / 110, 0, 1) ** 2 * np.clip(1 - ac / 1.6, 0, 1), '#fff6e0', grain=0, blend='screen')
        if reflect and hasattr(self, 'horizon'):
            # the lit windows mirrored in the river: mirror each emissive hit point under the water plane
            c = self.cam
            ys_, xs_ = np.nonzero(lum > 0.25)
            if ys_.size:
                dx = (xs_ + 0.5 - c['cx']) / c['f']; dy = -(ys_ + 0.5 - c['cy']) / c['f']
                t = R.depth[ys_, xs_]
                nl = np.sqrt(dx * dx + dy * dy + 1)
                X, Y, Z = dx / nl * t, c['h'] + dy / nl * t, t / nl
                mx, my = self.project(X, -Y, Z)
                ok = (mx >= 0) & (mx < self.W) & (my >= self.horizon) & (my < self.H)
                mxi, myi = mx[ok].astype(int), my[ok].astype(int)
                dist = np.sqrt(X[ok] ** 2 + (Y[ok] + c['h']) ** 2 + Z[ok] ** 2)
                vis = R.depth[myi, mxi] > dist * 0.98
                buf = np.zeros((self.H, self.W, 3), np.float32)
                np.add.at(buf, (myi[vis], mxi[vis]), e[ys_[ok][vis], xs_[ok][vis]] * 0.5)
                # stretch down into ripple streaks and break into dashes
                k = 46
                h0 = self.horizon
                acc = buf[h0:].copy()
                b = buf[h0:]
                for j in range(1, k):
                    acc[j:] += b[:-j] * (1 - j / k) ** 1.5
                acc = np.stack([blur(acc[..., q], 1.6) for q in range(3)], -1)
                dash = self._ripples(self.H - h0, self.W, 0.5)
                self.img[h0:] = self.img[h0:] + acc * dash[..., None] * (1 - R.alpha[h0:, :, None]) * 0.9

    # ------------------------------------------------------------ type
    def _glyph_mask(self, s, cap, track=0.12, ss=4):
        """render a string in the Deco display alphabet -> (mask array, width px, ascent px)"""
        gl = []
        x = 0.0
        for ch in s.upper():
            g = _glyph(ch)
            if g is None:
                g = _glyph(' ')
            gl.append((x, g))
            x += g[0] + track
        width = x - track
        pad = 0.12
        Wm = int((width + 2 * pad) * cap * ss) + 4
        Hm = int((1 + 2 * pad) * cap * ss) + 4
        im = Image.new('L', (Wm, Hm), 0)
        dr = ImageDraw.Draw(im)
        S = cap * ss
        for x0, (wd, polys) in gl:
            k = 0
            while k < len(polys):
                p = polys[k]
                pts = [((x0 + pad + px) * S, (1 + pad - py) * S) for px, py in p]
                # a closed full ring arrives as [outer, inner]: fill outer, cut inner
                if k + 1 < len(polys) and len(p) == 96 and len(polys[k + 1]) == 96 and \
                        abs(p[0][0] - p[-1][0]) < 1e-6 and abs(p[0][1] - p[-1][1]) < 1e-6:
                    dr.polygon(pts, fill=255)
                    q = polys[k + 1]
                    dr.polygon([((x0 + pad + px) * S, (1 + pad - py) * S) for px, py in q], fill=0)
                    k += 2
                    continue
                dr.polygon(pts, fill=255)
                k += 1
        im = im.resize((Wm // ss, Hm // ss), Image.LANCZOS)
        return np.asarray(im, np.float32) / 255, width * cap, pad * cap

    def deco_width(self, s, cap, track=0.12):
        x = 0.0
        for ch in s.upper():
            g = _glyph(ch) or _glyph(' ')
            x += g[0] + track
        return (x - track) * cap

    def lettering(self, s, x, base, cap, fill=((0, '#fff7e4'), (0.5, '#f2d79a'), (0.52, '#c9963f'), (1, '#f0cf87')),
                  track=0.12, shadow=(5, 5), shadow_colour='#050a1c', anchor='l'):
        """Deco display letters: thick down-strokes, hairline cross-strokes, high waist. `fill` is sprayed top to
        bottom through the letter friskets (default: a gilt fade with a hard horizon at the middle, the way
        sign painters faked metal), `shadow` a cast block shadow (dx, dy) in a dark ink."""
        m, wpx, pad = self._glyph_mask(s, cap, track)
        if anchor == 'm': x = x - wpx / 2
        elif anchor == 'r': x = x - wpx
        ox, oy = int(round(x - pad)), int(round(base - cap - pad))
        full = np.zeros((self.H, self.W), np.float32)
        h, w = m.shape
        y0, x0 = max(0, oy), max(0, ox)
        y1, x1 = min(self.H, oy + h), min(self.W, ox + w)
        full[y0:y1, x0:x1] = m[y0 - oy:y1 - oy, x0 - ox:x1 - ox]
        if shadow:
            sh = np.zeros_like(full)
            n = int(max(abs(shadow[0]), abs(shadow[1])))
            for j in range(1, n + 1):
                dx, dy = int(round(shadow[0] * j / n)), int(round(shadow[1] * j / n))
                sh = np.maximum(sh, np.roll(np.roll(full, dy, 0), dx, 1))
            self.spray(sh * (1 - full), shadow_colour, density=0.9, grain=0.6)
        self.fade(full, list(fill), (0, base - cap), (0, base))
        return wpx

    def caption(self, s, x, y, size, colour=IVORY, track=0.32, anchor='ls', font='geometric', alpha=1.0):
        """wide-tracked geometric sans (Futura / system sans) for the small print"""
        f = load_font(font, size)
        im = Image.new('L', (self.W, self.H), 0)
        d = ImageDraw.Draw(im)
        adv = [f.getlength(ch) + track * size for ch in s]
        total = sum(adv) - track * size
        x0 = x - total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        for ch, a in zip(s, adv):
            d.text((x0, y), ch, font=f, fill=255, anchor='l' + anchor[1])
            x0 += a
        m = np.asarray(im, np.float32) / 255
        self.spray(m * alpha, colour, grain=0.3)
        return total

    def rule(self, x0, x1, y, width=2.0, colour=GOLD):
        self.spray(self.rect(x0, y - width / 2, x1, y + width / 2), colour, grain=0.3)

    def border(self, inset=26, gap=9, width=2.2, colour=GOLD, step=34):
        """double gilt rule round the sheet with stepped (ziggurat) corners"""
        W, H = self.W, self.H
        m = np.zeros((H, W), np.float32)
        for k, ins in enumerate((inset, inset + gap)):
            st = step - k * gap * 0.0
            x0, y0, x1, y1 = ins, ins, W - ins, H - ins
            pts = [(x0 + st, y0), (x1 - st, y0), (x1 - st, y0 + st * 0.5), (x1 - st * 0.5, y0 + st * 0.5),
                   (x1 - st * 0.5, y0 + st), (x1, y0 + st), (x1, y1 - st), (x1 - st * 0.5, y1 - st),
                   (x1 - st * 0.5, y1 - st * 0.5), (x1 - st, y1 - st * 0.5), (x1 - st, y1), (x0 + st, y1),
                   (x0 + st, y1 - st * 0.5), (x0 + st * 0.5, y1 - st * 0.5), (x0 + st * 0.5, y1 - st), (x0, y1 - st),
                   (x0, y0 + st), (x0 + st * 0.5, y0 + st), (x0 + st * 0.5, y0 + st * 0.5), (x0 + st, y0 + st * 0.5)]
            im = Image.new('L', (W * 2, H * 2), 0)
            ImageDraw.Draw(im).line([(px * 2, py * 2) for px, py in pts + [pts[0]]], fill=255,
                                    width=int(round(width * 2)), joint='curve')
            m = np.maximum(m, np.asarray(im.resize((W, H), Image.LANCZOS), np.float32) / 255)
        self.fade(m, [(0, '#f3d892'), (0.5, colour), (1, '#9c6e2c')], (0, 0), (W, H), grain=0.3)

    # ------------------------------------------------------------ print
    def finish(self, paper='#efe4cc', tooth=0.035, warm=0.04, vignette=0.12):
        """lithographic print: paper tooth, a whisper of grain, warm cast, soft vignette"""
        H, W = self.H, self.W
        n = noise2d(H, W, 3, 2, self._seed()) - 0.5
        fib = noise2d(H, W // 6 + 1, 2, 2, self._seed())
        fib = np.asarray(Image.fromarray(fib).resize((W, H), Image.BICUBIC), np.float32) - 0.5
        g = 1 + tooth * (n * 0.8 + fib * 0.4)
        img = self.img * g[..., None]
        img = img * (1 - warm) + warm * _c(paper) * (0.35 + 0.65 * img)
        r = np.hypot((self.xx - W / 2) / (W / 2), (self.yy - H / 2) / (H / 2))
        img = img * (1 - vignette * smoothstep(0.65, 1.45, r))[..., None]
        self.img = img

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def composite(self):
        return Image.fromarray((np.clip(self.img, 0, 1) * 255 + 0.5).astype(np.uint8))

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
