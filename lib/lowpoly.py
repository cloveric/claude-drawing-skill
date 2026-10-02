"""lowpoly — a late-90s polygon game frame, drawn by a tiny software rasterizer (numpy + Pillow only).

What makes a frame from a 1999 console / PC game look like one, and how this module does each part:
  framebuffer   everything is drawn into a small framebuffer (default 384 x 216, the 16:9 cousin of 320 x 240)
                and blown up with nearest-neighbour scaling (x5 -> 1920 x 1080): every pixel stays a hard
                square and every polygon edge is a staircase. There is no anti-aliasing anywhere.
  geometry      meshes of a few dozen to a few thousand triangles. Vertices go world -> camera -> screen through
                a pinhole camera; screen positions are snapped to whole pixels (no sub-pixel precision), so
                thin polygons jag and shimmer.
  hidden faces  back-face culling, then the painter's algorithm: every triangle of the scene goes into one list
                sorted by mean depth (the console "ordering table") and is drawn far to near; decals carry a depth
                bias so they land on what they lie on. `zbuffer=True` adds a per-pixel depth test (the N64 way).
  near plane    triangles that cross the near plane are clipped (Sutherland-Hodgman) instead of dropped, so the
                ground under the camera has no holes.
  shading       flat shading: one colour per triangle from its face normal: a hemisphere ambient (sky above,
                warm bounce below) + one sun + an optional per-face Blinn glint, so gold, water and glass flash
                facet by facet like cut stones instead of shining smoothly.
  textures      tiny procedural textures (32-64 texels) sampled nearest-neighbour, interpolated *affinely* across
                each triangle (no perspective correction): rock strata bend on big polygons near the camera
                exactly as they did on the original hardware. Texture alpha is a hard cut-out (crossed-quad trees).
  fog           a per-vertex depth cue: each vertex gets a fog amount from its depth, interpolated across the
                triangle (Gouraud), so the far clip plane dissolves into the horizon colour of the sky.
  blending      the four semi-transparency modes of the era: 'half' (B/2 + F/2), 'add' (B + F), 'sub' (B - F),
                'quarter' (B + F/4): propeller discs, blob shadows, glows and lens flares.
  colour        the finished frame is crushed to 15-bit colour (5 bits per channel) through the 4 x 4 ordered
                dither matrix, so every gradient (sky, fog, lens flare) gets the tell-tale cross-hatch.
  HUD           a bitmap font stamped in framebuffer pixels: chunky italic digits with a banded colour ramp, a 1 px
                black outline and a drop shadow; icons, a stepped speed bar, a translucent minimap.

World: X right, Y up, Z forward (into the picture), units are metres. Angles in degrees.

    from lowpoly import LowPoly
    g = LowPoly(1920, 1080, scale=5, seed=1)
    path = g.path([(0, -40), (0, 60), (25, 160), (40, 260)])
    plane = g.along(path, 50, u=-1, y=12)
    g.camera(eye=g.along(path, 40, u=3, y=15), target=plane, fov=52)
    g.aim(plane, at=(0.35, 0.68))                 # compose: the plane on the lower-left third
    g.sky('#33509e', '#c4bedd'); g.sun(screen=(0.4, 0.1)); g.light(lift=26)
    g.canyon(path, height=0.75); g.river(path); g.fog(55, 250)
    g.ring(g.along(path, 70, y=13), g.heading(path, 70))
    g.aircraft(plane, g.heading(path, 50), roll=30)
    g.flare()
    g.counter('HOOPS', '04/09', 8, 6, icon='ring')
    g.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image
from core import noise2d, fbm1d, spline

# the 4x4 ordered-dither offsets of the PlayStation GPU (in 8-bit steps, added before truncating to 5 bits)
DITHER = np.array([[-4, 0, -3, 1], [2, -2, 3, -1], [-3, 1, -4, 0], [3, -1, 2, -2]], np.float32)

GOLD, WHITE, BLACK = '#ffaa1a', '#f4f1e8', '#000000'
HUD_YELLOW, HUD_ORANGE, HUD_RED, HUD_GREEN, HUD_CYAN = '#ffe85a', '#ff8a1c', '#e8401c', '#7ee05a', '#7fe6ff'

FONT = {  # 5 x 7 bitmap glyphs for the HUD
    'A': [' ### ', '#   #', '#   #', '#####', '#   #', '#   #', '#   #'], 'B': ['#### ', '#   #', '#   #', '#### ', '#   #', '#   #', '#### '],
    'C': [' ### ', '#   #', '#    ', '#    ', '#    ', '#   #', ' ### '], 'D': ['#### ', '#   #', '#   #', '#   #', '#   #', '#   #', '#### '],
    'E': ['#####', '#    ', '#    ', '#### ', '#    ', '#    ', '#####'], 'F': ['#####', '#    ', '#    ', '#### ', '#    ', '#    ', '#    '],
    'G': [' ### ', '#   #', '#    ', '# ###', '#   #', '#   #', ' ####'], 'H': ['#   #', '#   #', '#   #', '#####', '#   #', '#   #', '#   #'],
    'I': ['#####', '  #  ', '  #  ', '  #  ', '  #  ', '  #  ', '#####'], 'J': ['  ###', '   # ', '   # ', '   # ', '   # ', '#  # ', ' ##  '],
    'K': ['#   #', '#  # ', '# #  ', '##   ', '# #  ', '#  # ', '#   #'], 'L': ['#    ', '#    ', '#    ', '#    ', '#    ', '#    ', '#####'],
    'M': ['#   #', '## ##', '# # #', '# # #', '#   #', '#   #', '#   #'], 'N': ['#   #', '#   #', '##  #', '# # #', '#  ##', '#   #', '#   #'],
    'O': [' ### ', '#   #', '#   #', '#   #', '#   #', '#   #', ' ### '], 'P': ['#### ', '#   #', '#   #', '#### ', '#    ', '#    ', '#    '],
    'Q': [' ### ', '#   #', '#   #', '#   #', '# # #', '#  # ', ' ## #'], 'R': ['#### ', '#   #', '#   #', '#### ', '# #  ', '#  # ', '#   #'],
    'S': [' ####', '#    ', '#    ', ' ### ', '    #', '    #', '#### '], 'T': ['#####', '  #  ', '  #  ', '  #  ', '  #  ', '  #  ', '  #  '],
    'U': ['#   #', '#   #', '#   #', '#   #', '#   #', '#   #', ' ### '], 'V': ['#   #', '#   #', '#   #', '#   #', '#   #', ' # # ', '  #  '],
    'W': ['#   #', '#   #', '#   #', '# # #', '# # #', '## ##', '#   #'], 'X': ['#   #', '#   #', ' # # ', '  #  ', ' # # ', '#   #', '#   #'],
    'Y': ['#   #', '#   #', ' # # ', '  #  ', '  #  ', '  #  ', '  #  '], 'Z': ['#####', '    #', '   # ', '  #  ', ' #   ', '#    ', '#####'],
    '0': [' ### ', '#   #', '#   #', '#   #', '#   #', '#   #', ' ### '], '1': ['  #  ', ' ##  ', '# #  ', '  #  ', '  #  ', '  #  ', '#####'],
    '2': [' ### ', '#   #', '    #', '  ## ', ' #   ', '#    ', '#####'], '3': ['#####', '   # ', '  #  ', '   # ', '    #', '#   #', ' ### '],
    '4': ['   # ', '  ## ', ' # # ', '#  # ', '#####', '   # ', '   # '], '5': ['#####', '#    ', '#### ', '    #', '    #', '#   #', ' ### '],
    '6': ['  ## ', ' #   ', '#    ', '#### ', '#   #', '#   #', ' ### '], '7': ['#####', '    #', '   # ', '  #  ', ' #   ', ' #   ', ' #   '],
    '8': [' ### ', '#   #', '#   #', ' ### ', '#   #', '#   #', ' ### '], '9': [' ### ', '#   #', '#   #', ' ####', '    #', '   # ', ' ##  '],
    ' ': ['   '] * 7, '.': [' ', ' ', ' ', ' ', ' ', '#', '#'], ':': [' ', '#', '#', ' ', '#', '#', ' '],
    "'": ['#', '#', ' ', ' ', ' ', ' ', ' '], '"': ['#  #', '#  #', '    ', '    ', '    ', '    ', '    '],
    '/': ['    #', '    #', '   # ', '  #  ', ' #   ', '#    ', '#    '], '-': ['    ', '    ', '    ', '####', '    ', '    ', '    '],
    '+': ['     ', '  #  ', '  #  ', '#####', '  #  ', '  #  ', '     '], '!': ['#', '#', '#', '#', '#', ' ', '#'],
    '>': ['#   ', ' #  ', '  # ', '   #', '  # ', ' #  ', '#   '], '<': ['   #', '  # ', ' #  ', '#   ', ' #  ', '  # ', '   #'],
    'x': ['     ', '     ', '#   #', ' # # ', '  #  ', ' # # ', '#   #'], '%': ['##  #', '##  #', '   # ', '  #  ', ' #   ', '#  ##', '#  ##'],
    '#': [' # # ', '#####', ' # # ', ' # # ', ' # # ', '#####', ' # # '],
}
BLEND = {'opaque': 0, 'half': 1, 'add': 2, 'sub': 3, 'quarter': 4}


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-9)


def _q5(c):
    """snap a colour to the 15-bit grid (5 bits per channel), as the hardware stores it"""
    v = np.clip(np.floor(np.asarray(c, np.float32) * 31 + 0.5), 0, 31)
    return (v * 8 + v // 4) / 255


def _basis(fwd, roll=0.0, pitch=0.0):
    """orthonormal (right, up, fwd) for a heading, then pitch (nose up +) and roll (right wing down +)"""
    f = _unit(fwd)
    r = _unit(np.cross([0, 1, 0], f))
    u = np.cross(f, r)
    p, q = np.radians(pitch), np.radians(roll)
    f, u = f * np.cos(p) + u * np.sin(p), u * np.cos(p) - f * np.sin(p)
    r, u = r * np.cos(q) - u * np.sin(q), u * np.cos(q) + r * np.sin(q)
    return np.stack([r, u, f]).astype(np.float32)


class Path:
    """a centreline on the ground, sampled every metre of arc length (x, z); `at(s)` -> point, tangent, right"""
    def __init__(self, pts):
        P = spline(np.asarray(pts, np.float32), per=32)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        self.length = float(s[-1])
        self.s = np.arange(0, self.length, 1.0, dtype=np.float32)
        self.x = np.interp(self.s, s, P[:, 0]).astype(np.float32)
        self.z = np.interp(self.s, s, P[:, 1]).astype(np.float32)
        tx, tz = np.gradient(self.x), np.gradient(self.z)
        tl = np.hypot(tx, tz) + 1e-9
        self.tx, self.tz = tx / tl, tz / tl

    def at(self, s):
        s = np.clip(np.asarray(s, np.float32), 0, self.s[-1])
        x, z = np.interp(s, self.s, self.x), np.interp(s, self.s, self.z)
        tx, tz = np.interp(s, self.s, self.tx), np.interp(s, self.s, self.tz)
        tl = np.hypot(tx, tz) + 1e-9
        tx, tz = tx / tl, tz / tl
        return x, z, tx, tz, tz, -tx          # point, tangent, right-hand normal


class LowPoly:
    def __init__(self, W=1920, H=1080, scale=5, seed=0, record=True, zbuffer=False, near=0.6, far=260.0,
                 bits=5, dither=True):
        self.W, self.H, self.scale = W, H, scale
        self.w, self.h = W // scale, H // scale
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.record, self.zbuffer, self.near, self.far = record, zbuffer, near, far
        self.bits, self.dither = bits, dither
        self.meshes, self.post, self.hud = [], [], []
        self.textures = {}
        self.stages = []
        self.camera((0, 2, -10), (0, 2, 0))
        self.sky('#3a58a8', '#c2bcdc')
        self.L = self.L_shade = _unit([-0.45, 0.35, 0.8])
        self.sun_col, self.sky_amb, self.gnd_amb = _c('#ffe2b0') * 1.05, _c('#6f7fb0') * 0.95, _c('#7a5040') * 0.8
        self.fog_on, self.fog_col, self.fog_near, self.fog_far = False, self.horizon, 60.0, far

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ camera, sky, sun, fog
    def camera(self, eye, target=None, fov=52.0, roll=0.0, yaw=0.0, pitch=0.0):
        """pinhole camera at `eye` looking at `target` (or along yaw / pitch in degrees: yaw 0 looks along +Z,
        + turns right; pitch + looks up); `fov` is the vertical field of view; roll tilts the horizon (+ clockwise)"""
        self.eye = np.asarray(eye, np.float32)
        if target is None:
            y, p = np.radians(yaw), np.radians(pitch)
            target = self.eye + np.array([np.sin(y) * np.cos(p), np.sin(p), np.cos(y) * np.cos(p)], np.float32)
        d = np.asarray(target, np.float32) - self.eye
        self.yaw = float(np.degrees(np.arctan2(d[0], d[2])))
        self.pitch = float(np.degrees(np.arctan2(d[1], np.hypot(d[0], d[2]))))
        self.roll = roll
        B = _basis(d)
        q = np.radians(-roll)
        r, u = B[0] * np.cos(q) - B[1] * np.sin(q), B[1] * np.cos(q) + B[0] * np.sin(q)
        self.R = np.stack([r, u, B[2]]).astype(np.float32)
        self.fov = fov
        self.f = (self.h / 2) / np.tan(np.radians(fov) / 2)
        self.cx, self.cy = self.w / 2, self.h / 2
        self.tanx, self.tany = (self.w / 2) / self.f, (self.h / 2) / self.f
        self._skybuf = None

    def aim(self, point, at=(0.5, 0.5)):
        """turn the camera (keeping eye, fov and roll) so that world `point` lands at screen fraction `at`:
        the way to compose a shot ("plane on the lower-left third")"""
        yaw, pitch = self.yaw, self.pitch
        for _ in range(40):
            self.camera(self.eye, None, self.fov, self.roll, yaw, pitch)
            x, y, z = self.project(point)
            dx, dy = x - at[0] * self.w, y - at[1] * self.h
            if abs(dx) < 0.05 and abs(dy) < 0.05: break
            yaw += np.degrees(np.arctan(dx / self.f)); pitch -= np.degrees(np.arctan(dy / self.f))
        return self

    def project(self, p):
        """world point -> (sx, sy, depth) in framebuffer pixels"""
        c = (np.asarray(p, np.float32) - self.eye) @ self.R.T
        z = max(float(c[2]), 1e-3)
        return self.cx + self.f * c[0] / z, self.cy - self.f * c[1] / z, float(c[2])

    def ray(self, sx, sy):
        """world direction through framebuffer pixel (sx, sy)"""
        d = np.array([(sx - self.cx) / self.f, -(sy - self.cy) / self.f, 1.0], np.float32)
        return _unit(d @ self.R)

    def sky(self, zenith='#3a58a8', horizon='#c2bcdc', below=None, glow='#fff0c8', bands=None):
        """sky gradient by elevation (zenith -> horizon), a warm glow around the sun; below the horizon = horizon"""
        self.zenith, self.horizon = _c(zenith), _c(horizon)
        self.below = _c(below) if below is not None else self.horizon
        self.glow_col = _c(glow)
        self.bands = bands
        self._skybuf = None

    def sun(self, direction=None, screen=None, colour='#ffe2b0', strength=1.05, disc=1.7):
        """set the sun: a world direction toward it, or a framebuffer position as fractions (fx, fy) of the frame.
        It lights every face, and is drawn in the sky with a glow (call after camera())"""
        if screen is not None:
            direction = self.ray(screen[0] * self.w, screen[1] * self.h)
        self.L = _unit(direction)
        self.L_shade = self.L
        self.sun_col = _c(colour) * strength
        self.sun_disc = disc
        self._skybuf = None

    def light(self, direction=None, lift=0.0):
        """the shading light, if it should differ from the sun in the sky (games of the era set them separately):
        a world direction, or the sun's direction raised by `lift` degrees"""
        d = _unit(direction) if direction is not None else self.L
        if lift:
            h = np.hypot(d[0], d[2]); el = np.arctan2(d[1], h) + np.radians(lift)
            d = np.array([d[0] / h * np.cos(el), np.sin(el), d[2] / h * np.cos(el)], np.float32)
        self.L_shade = _unit(d)

    def ambient(self, sky='#6f7fb0', ground='#7a5040', strength=(0.95, 0.8)):
        self.sky_amb, self.gnd_amb = _c(sky) * strength[0], _c(ground) * strength[1]

    def fog(self, near=60.0, far=None, colour=None):
        """per-vertex depth fog from `near` (clear) to `far` (all fog); colour defaults to the sky's horizon"""
        self.fog_on, self.fog_near = True, float(near)
        self.fog_far = float(far if far is not None else self.far)
        self.fog_col = _c(colour) if colour is not None else self.horizon

    def _sky(self):
        if self._skybuf is not None: return self._skybuf
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32) + 0.5
        d = np.stack([(xx - self.cx) / self.f, -(yy - self.cy) / self.f, np.ones_like(xx)], -1) @ self.R
        d /= np.linalg.norm(d, axis=-1, keepdims=True)
        el = np.arcsin(np.clip(d[..., 1], -1, 1))
        t = np.clip(el / np.radians(38), 0, 1) ** 0.75
        img = self.horizon * (1 - t[..., None]) + self.zenith * t[..., None]
        img = np.where((el < 0)[..., None], self.below, img)
        if self.bands:                                   # thin streak clouds lit from below
            n = noise2d(self.h, self.w, 40, 3, self.seed + 5)
            for e0, thick, col, a in self.bands:
                k = np.exp(-((np.degrees(el) - e0) / thick) ** 2) * np.clip((n - 0.35) * 2.2, 0, 1) * a
                img = img * (1 - k[..., None]) + _c(col) * k[..., None]
        cs = np.clip((d * self.L).sum(-1), -1, 1)
        ang = np.degrees(np.arccos(cs))
        g = np.exp(-ang / 9.0) * 0.55 + np.exp(-ang / 30.0) * 0.25
        img = img + (self.glow_col - img) * np.clip(g, 0, 1)[..., None]
        disc = getattr(self, 'sun_disc', 1.7)
        core = (ang < disc).astype(np.float32)
        ring = ((ang >= disc) & (ang < disc * 1.6)).astype(np.float32)
        img = img * (1 - core[..., None]) + np.array([1.0, 0.99, 0.93]) * core[..., None]
        img = img * (1 - 0.6 * ring[..., None]) + np.array([1.0, 0.93, 0.7]) * 0.6 * ring[..., None]
        self._skybuf = np.clip(img, 0, 1).astype(np.float32)
        return self._skybuf

    # ------------------------------------------------------------ textures
    def texture(self, name):
        """tiny procedural textures, RGBA float: strata, ledge, sand, water, rock, juniper, spark, flare"""
        if name in self.textures: return self.textures[name]
        r = np.random.default_rng(self.seed * 31 + sum(map(ord, name)))
        if name == 'strata':                       # canyon wall: horizontal bands, ledges, desert-varnish streaks
            th, tw = 64, 32
            pal = ['#7c3421', '#a8482a', '#c4643a', '#d98a52', '#e6b27a', '#b9573a', '#8e4436', '#efcf98', '#c87a4c', '#9a3d27']
            rows = np.zeros((th, 3), np.float32)
            y, k = 0, 0
            while y < th:
                t = int(r.integers(2, 8)); col = hexc(pal[(k * 3 + int(r.integers(0, 3))) % len(pal)])
                rows[y:y + t] = col; y += t; k += 1
            tex = np.repeat(rows[:, None, :], tw, 1)
            tex *= (0.9 + 0.2 * r.random((th, tw)))[..., None]
            edges = np.abs(np.diff(rows.sum(1), prepend=rows[0].sum())) > 0.25
            tex[edges] *= 0.72                                         # ledge shadows at band boundaries
            for _ in range(7):                                         # dark varnish streaks running down
                x0, y0, L = int(r.integers(0, tw)), int(r.integers(0, th)), int(r.integers(8, 26))
                for i in range(L):
                    yy = (y0 + i) % th
                    a = 0.45 * (1 - i / L)
                    for dx in (0, 1):
                        tex[yy, (x0 + dx) % tw] *= (1 - a * (0.6 if dx else 1))
            alpha = np.ones((th, tw, 1), np.float32)
        elif name == 'ledge':                      # flat tops: dusty ochre with sage scrub
            th = tw = 32
            base = hexc('#c99a62') * (0.88 + 0.22 * r.random((th, tw)))[..., None]
            n = noise2d(th, tw, 6, 2, int(r.integers(1 << 30)))
            scrub = (r.random((th, tw)) < 0.12) | (n > 0.78)
            tex = np.where(scrub[..., None], hexc('#7d8a52') * (0.75 + 0.3 * r.random((th, tw)))[..., None], base)
            pebble = r.random((th, tw)) < 0.05
            tex = np.where(pebble[..., None], hexc('#ead2a4'), tex)
            alpha = np.ones((th, tw, 1), np.float32)
        elif name == 'sand':
            th = tw = 32
            tex = hexc('#d8b48a') * (0.86 + 0.24 * r.random((th, tw)))[..., None]
            tex = np.where((r.random((th, tw)) < 0.07)[..., None], hexc('#8f7a66'), tex)
            alpha = np.ones((th, tw, 1), np.float32)
        elif name == 'water':                      # teal with lighter ripple dashes running downstream
            th = tw = 32
            tex = np.repeat((hexc('#2a6f7c') * (0.92 + 0.12 * r.random((th, 1))))[:, None, :], tw, 1)
            for _ in range(16):
                y, x, L = int(r.integers(0, th)), int(r.integers(0, tw)), int(r.integers(3, 8))
                for i in range(L):
                    tex[(y + i // 3) % th, (x + i) % tw] = hexc('#5fa6a8') if i % 4 else hexc('#9ed2c8')
            tex *= (0.95 + 0.1 * r.random((th, tw)))[..., None]
            alpha = np.ones((th, tw, 1), np.float32)
        elif name == 'rock':
            th = tw = 16
            tex = hexc('#8a7468') * (0.8 + 0.35 * r.random((th, tw)))[..., None]
            alpha = np.ones((th, tw, 1), np.float32)
        elif name == 'juniper':                    # a cut-out tree for crossed quads (u across, v up)
            th, tw = 48, 32
            yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32)
            v = 1 - (yy + 0.5) / th; u = (xx + 0.5) / tw - 0.5
            trunk = (np.abs(u + 0.02 * np.sin(v * 9)) < 0.05) & (v < 0.32)
            crown = np.zeros((th, tw), bool)
            for _ in range(9):
                cy, cx = r.uniform(0.32, 0.9), r.uniform(-0.18, 0.18)
                ry = r.uniform(0.09, 0.16); rx = ry * (1.4 - (cy - 0.3)) * 1.25
                crown |= ((u - cx) / rx) ** 2 + ((v - cy) / ry) ** 2 < 1
            crown &= r.random((th, tw)) > 0.06
            lit = 0.75 + 0.5 * np.clip(-u * 2 + (v - 0.5), -0.5, 0.6)
            tex = np.where(crown[..., None], hexc('#5c7e40') * (lit * (0.85 + 0.3 * r.random((th, tw))))[..., None],
                           hexc('#5a3c2a') * np.ones((th, tw, 1)))
            alpha = (crown | trunk)[..., None].astype(np.float32)
        elif name == 'spark':                      # four-point star for additive sprites
            th = tw = 16
            yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32) - 7.5
            a = np.clip(1.2 - (np.abs(xx) * np.abs(yy)) ** 0.5 / 1.6 - np.hypot(xx, yy) / 9, 0, 1)
            tex = np.ones((th, tw, 3), np.float32); alpha = a[..., None]
        else:
            raise ValueError(name)
        T = np.concatenate([np.clip(tex, 0, 1), alpha], -1).astype(np.float32)
        self.textures[name] = T
        return T

    # ------------------------------------------------------------ meshes
    def mesh(self, V, F, colour, uv=None, tex=None, lit=True, spec=0.0, shine=16.0, blend='opaque', alpha=0.5,
             two_sided=False, fog=True, bias=0.0, cutout=False, glow=0.0, name=''):
        """add triangles. V (n, 3) world vertices; F (m, 3) indices; colour one colour or (m, 3) per face;
        uv (m, 3, 2) per face corner; tex a texture name; blend 'opaque'|'half'|'add'|'sub'|'quarter'; glow lifts the
        face toward full-bright (pickups). Front faces wind so that their normal points toward the viewer side."""
        V = np.asarray(V, np.float32); F = np.asarray(F, np.int32)
        P = V[F]
        m = len(F)
        col = np.asarray(colour if not isinstance(colour, str) else hexc(colour), np.float32)
        col = np.broadcast_to(col, (m, 3)).astype(np.float32)
        N = _unit(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]))
        if uv is None: uv = np.zeros((m, 3, 2), np.float32)
        uv = np.asarray(uv, np.float32)
        flat = col.copy()
        if tex is not None:                          # untextured preview: the texel under the face centre
            T = self.texture(tex)
            c = uv.mean(1)
            iu = (np.floor(c[:, 0] * T.shape[1]).astype(int)) % T.shape[1]
            iv = (np.floor(c[:, 1] * T.shape[0]).astype(int)) % T.shape[0]
            flat = col * T[iv, iu, :3]
        self.meshes.append(dict(P=P, N=N, col=col, flat=flat, uv=uv, tex=tex, lit=lit, spec=spec, shine=shine,
                                blend=BLEND[blend], alpha=alpha, two=two_sided, fog=fog, bias=bias, cutout=cutout,
                                glow=glow, name=name))
        return self.meshes[-1]

    @staticmethod
    def _orient(V, F, inside):
        """flip faces whose normal points toward `inside` (a point, or (m, 3) points one per face)"""
        V = np.asarray(V, np.float32); F = np.array(F, np.int32)
        P = V[F]
        n = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
        bad = ((P.mean(1) - np.asarray(inside, np.float32)) * n).sum(-1) < 0
        F[bad] = F[bad][:, [0, 2, 1]]
        return F

    # ------------------------------------------------------------ places along a path
    def path(self, pts):
        """a centreline through (x, z) control points (Catmull-Rom), sampled by arc length"""
        return Path(pts)

    def along(self, path, s, u=0.0, y=0.0):
        """world point `s` metres along the path, `u` metres to its right, `y` metres up"""
        x, z, tx, tz, nx, nz = path.at(s)
        return np.array([x + nx * u, y, z + nz * u], np.float32)

    def heading(self, path, s):
        x, z, tx, tz, nx, nz = path.at(s)
        return np.array([tx, 0.0, tz], np.float32)

    # ------------------------------------------------------------ terrain
    CANYON = [  # half cross-section from the centre outward: (u metres, y metres, material of the face beyond)
        (0.0, -1.2, 'sand'), (6.0, -1.2, 'sand'), (7.4, 0.5, 'sand'), (10.5, 1.4, 'sand'), (13.0, 4.5, 'rock'),
        (13.6, 15.0, 'ledge'), (18.0, 15.8, 'rock'), (18.8, 26.0, 'ledge'), (22.5, 26.8, 'rock'), (23.4, 37.0, 'ledge'),
        (34.0, 38.0, 'ledge'), (60.0, 39.5, 'ledge'), (110.0, 41.0, 'ledge')]
    MATERIALS = {'sand': ('sand', '#ffffff', 'top'), 'rock': ('strata', '#ffffff', 'wall'),
                 'ledge': ('ledge', '#ffffff', 'top')}

    def canyon(self, path, s0=0.0, s1=None, step=7.0, profile=None, width=0.14, wobble=0.9, height=1.0,
               strata=40.0, buried=-0.2, seed=None):
        """a canyon lofted along `path`: every `step` metres a cross-section (river bed, sand banks, talus, stepped
        cliffs with ledges, rim, plateau) is laid across the path; its width breathes along the way (`width`), every
        vertex is nudged (`wobble`) so no two facets match; walls take the strata texture by height (`strata`
        metres per repeat), flat parts a top-down sand / scrub texture"""
        prof = profile or self.CANYON
        s1 = path.s[-1] if s1 is None else s1
        n = int((s1 - s0) / step) + 1
        ss = np.linspace(s0, s1, n).astype(np.float32)
        r = np.random.default_rng(self._seed() if seed is None else seed)
        breathe = {side: 1 + width * fbm1d(n, 6, 3, int(r.integers(1 << 30))) for side in (-1, 1)}
        K = len(prof)
        cols = [(-1, k) for k in range(K - 1, 0, -1)] + [(0, 0)] + [(1, k) for k in range(1, K)]
        nc = len(cols)
        V = np.zeros((n, nc, 3), np.float32)
        A = np.zeros((n, nc), np.float32)                 # arc length of every vertex (texture u on walls)
        x, z, tx, tz, nx, nz = path.at(ss)
        for j, (side, k) in enumerate(cols):
            u, y, _ = prof[k]
            b = breathe[side if side else 1]
            uu = side * u * (b if u > 7 else 1.0)
            big = 1.0 if u >= 11 else 0.4
            ju = r.normal(0, wobble, n) * big * (k > 0)
            jy = r.normal(0, wobble, n) * big * (k > 0)
            js = r.normal(0, step * 0.12, n) * (k > 0)
            js[0] = js[-1] = 0
            V[:, j, 0] = x + nx * (uu + ju) + tx * js
            V[:, j, 1] = y * (height if y > 2 else 1.0) + jy
            V[:, j, 2] = z + nz * (uu + ju) + tz * js
            A[:, j] = ss + js
        idx = np.arange(n * nc).reshape(n, nc)
        F, mats, inside = [], [], []
        for i in range(n - 1):
            for j in range(nc - 1):
                a, b, c, d = idx[i, j], idx[i, j + 1], idx[i + 1, j], idx[i + 1, j + 1]
                side = cols[j][0] if cols[j][0] < 0 else cols[j + 1][0]
                mat = prof[min(cols[j][1], cols[j + 1][1])][2]      # material of the face beyond the inner point
                F += [(a, c, b), (b, c, d)] if (i + j) % 2 else [(a, c, d), (a, d, b)]
                mats += [mat, mat]
                # the rock side of every face: deep below the plateau on its own side of the canyon
                ox, oz = (x[i] + x[i + 1]) / 2 + nx[i] * side * 300, (z[i] + z[i + 1]) / 2 + nz[i] * side * 300
                inside += [[ox, -80.0, oz]] * 2
        Vf = V.reshape(-1, 3)
        F = self._orient(Vf, F, np.array(inside, np.float32))
        mats = np.array(mats)
        if buried is not None:                       # faces wholly under the water are never seen: leave them out
            keep = Vf[F][:, :, 1].max(1) > buried
            F, mats = F[keep], mats[keep]
        self._terrain(Vf[F], mats, strata, along=A.reshape(-1)[F])

    def _terrain(self, P, mats, strata=40.0, along=None):
        """texture terrain faces by material: walls get strata by height (u along the wall), flat parts top-down"""
        if along is None:
            along = P[..., 0] * 0.6 + P[..., 2] * 0.8
        for mat in np.unique(mats):
            sel = mats == mat
            tex, tint, mapping = self.MATERIALS[mat]
            Q = P[sel]
            if mapping == 'wall':
                uv = np.stack([along[sel] / 22.0, -Q[..., 1] / strata], -1)
            else:
                uv = np.stack([Q[..., 0] / 15.0, Q[..., 2] / 15.0], -1)
            V = Q.reshape(-1, 3)
            self.mesh(V, np.arange(len(V)).reshape(-1, 3), tint, uv=uv, tex=tex, name='terrain')

    def river(self, path, s0=0.0, s1=None, step=7.0, half=7.0, level=0.0, ripple=0.12, colour='#ffffff', spec=0.35):
        """the water surface between the banks: a strip of slightly uneven facets (each catches the sun on its own),
        textured with ripples running downstream"""
        s1 = path.s[-1] if s1 is None else s1
        n = int((s1 - s0) / step) + 1
        ss = np.linspace(s0, s1, n).astype(np.float32)
        x, z, tx, tz, nx, nz = path.at(ss)
        us = np.array([-half, -half * 0.35, half * 0.35, half], np.float32)
        r = np.random.default_rng(self._seed())
        nc = len(us)
        V = np.zeros((n, nc, 3), np.float32); UV = np.zeros((n, nc, 2), np.float32)
        for j, u in enumerate(us):
            V[:, j, 0] = x + nx * u; V[:, j, 2] = z + nz * u
            V[:, j, 1] = level + r.normal(0, ripple, n) * (0.4 if j in (0, nc - 1) else 1)
            UV[:, j, 0] = u / 9.0; UV[:, j, 1] = -ss / 9.0
        idx = np.arange(n * nc).reshape(n, nc)
        F = []
        for i in range(n - 1):
            for j in range(nc - 1):
                a, b, c, d = idx[i, j], idx[i, j + 1], idx[i + 1, j], idx[i + 1, j + 1]
                F += [(a, c, b), (b, c, d)] if (i + j) % 2 else [(a, c, d), (a, d, b)]
        Vf = V.reshape(-1, 3)
        F = self._orient(Vf, F, Vf.mean(0) - np.array([0, 50, 0]))
        return self.mesh(Vf, F, colour, uv=UV.reshape(-1, 2)[F], tex='water', spec=spec, shine=30, bias=-2.0,
                         name='water')

    def _prism(self, ring_lo, ring_hi, top=True, bottom=False):
        """side wall (+ caps) between two closed rings of equal length -> V, F (outward)"""
        n = len(ring_lo)
        V = np.vstack([ring_lo, ring_hi]).astype(np.float32)
        F = []
        for i in range(n):
            j = (i + 1) % n
            F += [(i, j, n + i), (j, n + j, n + i)]
        c_lo, c_hi = ring_lo.mean(0), ring_hi.mean(0)
        if top:
            V = np.vstack([V, c_hi]); k = len(V) - 1
            F += [(n + i, n + (i + 1) % n, k) for i in range(n)]
        if bottom:
            V = np.vstack([V, c_lo]); k = len(V) - 1
            F += [(i, (i + 1) % n, k) for i in range(n)]
        F = self._orient(V, np.array(F), (c_lo + c_hi) / 2)
        return V, F

    def mesa(self, x, z, radius, height, base=0.0, sides=7, taper=0.82, cap=0.06, strata=40.0, seed=None):
        """a flat-topped butte: an irregular prism with strata walls, a scrub-covered cap rock and a talus skirt"""
        r = np.random.default_rng(self._seed() if seed is None else seed)
        a = np.sort(r.uniform(0, 2 * np.pi, sides)) + r.uniform(0, 1)
        rr = radius * r.uniform(0.75, 1.2, sides)
        lo = np.stack([x + np.cos(a) * rr * 1.25, np.full(sides, base), z + np.sin(a) * rr * 1.25], 1)
        mid = np.stack([x + np.cos(a) * rr, np.full(sides, base + height * 0.18), z + np.sin(a) * rr], 1)
        hi = np.stack([x + np.cos(a) * rr * taper, base + height + r.normal(0, height * cap, sides), z + np.sin(a) * rr * taper], 1)
        V1, F1 = self._prism(lo, mid, top=False)
        V2, F2 = self._prism(mid, hi, top=False)
        Pm = np.concatenate([V1[F1], V2[F2]])
        ang = np.arctan2(Pm[..., 2] - z, Pm[..., 0] - x)
        ang = np.where(ang - ang[:, :1] > np.pi, ang - 2 * np.pi, np.where(ang - ang[:, :1] < -np.pi, ang + 2 * np.pi, ang))
        self._terrain(Pm, np.array(['rock'] * len(Pm)), strata, along=ang * radius)
        Vt = np.vstack([hi, hi.mean(0) + [0, height * 0.02, 0]])
        Ft = self._orient(Vt, [(i, (i + 1) % sides, sides) for i in range(sides)], hi.mean(0) - [0, 5, 0])
        self._terrain(Vt[Ft], np.array(['ledge'] * sides), strata)

    def arch(self, path, s, span=46.0, rise=16.0, base=24.0, thick=4.5, depth=6.0, segs=11, strata=40.0):
        """a natural stone arch thrown across the canyon at `s`: an irregular rock section swept along a half
        ellipse whose feet sink into the walls at height `base`; thicker at the feet"""
        x, z, tx, tz, nx, nz = path.at(s)
        P0 = np.array([x, 0, z], np.float32)
        t3, n3 = np.array([tx, 0, tz], np.float32), np.array([nx, 0, nz], np.float32)
        r = np.random.default_rng(self._seed())
        sec = 7
        rings = []
        for i in range(segs + 1):
            th = np.pi * i / segs
            c = P0 + n3 * (-np.cos(th) * span / 2) + np.array([0, base + np.sin(th) * rise, 0])
            out = _unit(n3 * -np.cos(th) * 0.6 + np.array([0, np.sin(th), 0]) + 1e-3)   # away from the arch's axis
            k = 1 + 0.9 * (1 - np.sin(th)) ** 2
            a = np.linspace(0, 2 * np.pi, sec, endpoint=False) + 0.3
            pts = [c + t3 * np.cos(aa) * depth / 2 * k * r.uniform(0.8, 1.15) +
                   out * np.sin(aa) * thick / 2 * k * r.uniform(0.8, 1.15) for aa in a]
            rings.append(np.array(pts, np.float32))
        V = np.vstack(rings)
        F = []
        for i in range(segs):
            for j in range(sec):
                a_, b_ = i * sec + j, i * sec + (j + 1) % sec
                c_, d_ = a_ + sec, b_ + sec
                F += [(a_, b_, c_), (b_, d_, c_)]
        F = np.array(F)
        cen = np.repeat(np.array([rg.mean(0) for rg in rings[:-1]]) * 0.5 + np.array([rg.mean(0) for rg in rings[1:]]) * 0.5, sec * 2, 0)
        F = self._orient(V, F, cen)
        P = V[F]
        mats = np.where(_unit(np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]))[:, 1] > 0.75, 'ledge', 'rock')
        self._terrain(P, mats, strata)

    def boulder(self, x, y, z, r=1.0, colour='#ffffff', squash=0.7):
        """a jittered octahedron-sphere rock (half sunk into what it sits on)"""
        rr = np.random.default_rng(self._seed())
        ph = np.array([0.0, 0.55, 1.15, 1.75, np.pi])
        V, F = [], []
        ring_n = 6
        V.append([0, 1, 0])
        for p in ph[1:-1]:
            for k in range(ring_n):
                a = 2 * np.pi * k / ring_n + p
                V.append([np.sin(p) * np.cos(a), np.cos(p), np.sin(p) * np.sin(a)])
        V.append([0, -1, 0])
        V = np.array(V, np.float32) * rr.uniform(0.8, 1.15, (len(V), 1))
        V *= np.array([r, r * squash, r * rr.uniform(0.8, 1.2)])
        V += [x, y, z]
        nr = len(ph) - 2
        for k in range(ring_n):
            F.append((0, 1 + k, 1 + (k + 1) % ring_n))
        for i in range(nr - 1):
            for k in range(ring_n):
                a, b = 1 + i * ring_n + k, 1 + i * ring_n + (k + 1) % ring_n
                F += [(a, a + ring_n, b), (b, a + ring_n, b + ring_n)]
        last = len(V) - 1
        for k in range(ring_n):
            F.append((last, 1 + (nr - 1) * ring_n + (k + 1) % ring_n, 1 + (nr - 1) * ring_n + k))
        F = self._orient(V, F, [x, y, z])
        P = V[F]
        uv = np.stack([P[..., 0] / 3 + P[..., 1] / 5, P[..., 2] / 3], -1)
        return self.mesh(V, F, colour, uv=uv, tex='rock', name='rock')

    def tree(self, x, y, z, height=4.0, colour='#ffffff'):
        """a juniper as two crossed textured quads with a hard alpha cut-out (the classic billboard tree)"""
        rr = np.random.default_rng(self._seed())
        a0 = rr.uniform(0, np.pi)
        w = height * 0.7
        for a in (a0, a0 + np.pi / 2):
            d = np.array([np.cos(a), 0, np.sin(a)], np.float32) * w / 2
            b = np.array([x, y, z], np.float32)
            V = np.array([b - d, b + d, b + d + [0, height, 0], b - d + [0, height, 0]], np.float32)
            F = np.array([(0, 1, 2), (0, 2, 3)])
            uv = np.array([[(0, 1), (1, 1), (1, 0)], [(0, 1), (1, 0), (0, 0)]], np.float32) * 0.999
            self.mesh(V, F, colour, uv=uv, tex='juniper', two_sided=True, cutout=True, glow=0.3, name='tree')

    # ------------------------------------------------------------ objects
    def torus(self, centre, axis, radius, tube, segs=14, sides=6, spin=0.0):
        """faceted torus around `axis` -> (V, F) outward"""
        a = _unit(axis)
        e1 = _unit(np.cross(a, [0, 1, 0]) if abs(a[1]) < 0.9 else np.cross(a, [1, 0, 0]))
        e2 = np.cross(a, e1)
        V, C = [], []
        for i in range(segs):
            t = 2 * np.pi * i / segs + np.radians(spin)
            d = e1 * np.cos(t) + e2 * np.sin(t)
            c = np.asarray(centre, np.float32) + d * radius
            for k in range(sides):
                p = 2 * np.pi * k / sides + np.pi / sides
                V.append(c + (d * np.cos(p) + a * np.sin(p)) * tube)
        V = np.array(V, np.float32)
        F, inside = [], []
        for i in range(segs):
            for k in range(sides):
                p0 = i * sides + k; p1 = i * sides + (k + 1) % sides
                q0 = ((i + 1) % segs) * sides + k; q1 = ((i + 1) % segs) * sides + (k + 1) % sides
                F += [(p0, q0, p1), (p1, q0, q1)]
                t = 2 * np.pi * (i + 0.5) / segs + np.radians(spin)
                c = np.asarray(centre) + (e1 * np.cos(t) + e2 * np.sin(t)) * radius
                inside += [c, c]
        return V, self._orient(V, F, np.array(inside, np.float32))

    def ring(self, centre, facing, radius=3.4, tube=0.6, colour=GOLD, segs=12, sides=5, glow=0.28, spin=8.0, shine=4.0,
             spec=2.0):
        """a gold hoop to fly through: a faceted torus facing along `facing`; every facet flashes on its own"""
        V, F = self.torus(centre, facing, radius, tube, segs, sides, spin)
        return self.mesh(V, F, colour, spec=spec, shine=shine, glow=glow, name="ring")

    def aircraft(self, pos, heading, roll=0.0, pitch=0.0, size=1.0, body=WHITE, trim='#1fa39c', canopy='#1d2c4c',
                 spinner='#f0742a', prop=True):
        """a small low-wing stunt plane of ~230 triangles: octagonal fuselage, tapered wings with dihedral, tail,
        bubble canopy, spinner, plus a half-transparent propeller disc with a brighter tip circle and two smeared
        blades; `roll` + banks to the right"""
        B = _basis(heading, roll, pitch)
        O = np.asarray(pos, np.float32)
        place = lambda v: O + (np.asarray(v, np.float32) * size) @ B
        parts = []                                      # (V local, F, colour per face, spec)
        # fuselage: octagonal sections (z, half-width, half-height, y)
        st = [(-2.1, 0.06, 0.09, 0.2), (-1.45, 0.17, 0.2, 0.1), (-0.55, 0.33, 0.36, 0.02), (0.4, 0.4, 0.42, 0.0),
              (1.0, 0.38, 0.38, -0.02), (1.38, 0.29, 0.29, -0.03)]
        ang = (np.arange(8) + 0.5) * np.pi / 4
        rings = [np.stack([np.cos(ang) * hw, y + np.sin(ang) * hh, np.full(8, z)], 1) for z, hw, hh, y in st]
        V = np.vstack(rings); F = []
        for i in range(len(st) - 1):
            for k in range(8):
                a, b = i * 8 + k, i * 8 + (k + 1) % 8
                F += [(a, b, a + 8), (b, b + 8, a + 8)]
        V = np.vstack([V, [0, st[0][3], st[0][0] - 0.05], [0, st[-1][3], st[-1][0]]])
        t0, t1 = len(V) - 2, len(V) - 1
        F += [(k, (k + 1) % 8, t0) for k in range(8)]
        F += [((len(st) - 1) * 8 + k, (len(st) - 1) * 8 + (k + 1) % 8, t1) for k in range(8)]
        F = self._orient(V, F, [0, 0, 0])
        zc = V[F][:, :, 2].mean(1)
        yc = V[F][:, :, 1].mean(1)
        cf = np.where((zc > 0.75)[:, None], hexc(trim), hexc(body))
        cf = np.where(((zc > -1.2) & (zc < -0.85))[:, None], hexc(trim), cf)
        cf = np.where(((zc > 0.75) & (yc > 0.25))[:, None], hexc('#22323a'), cf)          # anti-glare panel
        parts.append((V, F, cf, 0.25))

        def wing(x0, x1, z0r, z1r, z0t, z1t, y0, y1, tr, tt, tip_col, split=0.72):
            """half-wing from x0 (root) to x1 (tip): diamond section (trailing edge, top, leading edge, bottom);
            the outer segment is painted tip_col"""
            secs = []
            for f in (0.0, split, 1.0):
                x = x0 + (x1 - x0) * f
                za, zb = z0r + (z0t - z0r) * f, z1r + (z1t - z1r) * f
                y = y0 + (y1 - y0) * f
                t = tr + (tt - tr) * f
                secs.append([(x, y, zb), (x, y + t / 2, za + (zb - za) * 0.3), (x, y, za), (x, y - t / 2, za + (zb - za) * 0.3)])
            S = np.array(secs, np.float32)
            V = S.reshape(-1, 3)
            F, C, I = [], [], []
            for i in range(2):
                mid = (S[i].mean(0) + S[i + 1].mean(0)) / 2
                for k in range(4):
                    a, b = i * 4 + k, i * 4 + (k + 1) % 4
                    F += [(a, b, a + 4), (b, b + 4, a + 4)]
                    C += [tip_col if i == 1 else body] * 2
                    I += [mid, mid]
            F += [(8, 9, 10), (8, 10, 11), (0, 1, 2), (0, 2, 3)]
            C += [tip_col] * 2 + [body] * 2
            I += [(S[1].mean(0) + S[2].mean(0)) / 2] * 2 + [(S[0].mean(0) + S[1].mean(0)) / 2] * 2
            F = self._orient(V, F, np.array(I, np.float32))
            return V, F, np.array([hexc(c) for c in C]), 0.3

        for sgn in (1, -1):
            for (V, F, C, sp) in [wing(0.25, 2.25, 0.85, -0.25, 0.62, 0.12, -0.22, 0.02, 0.16, 0.07, trim),
                                  wing(0.1, 0.95, -1.4, -2.05, -1.6, -2.0, 0.12, 0.16, 0.08, 0.05, trim, split=0.6)]:
                V = V * [sgn, 1, 1]
                if sgn < 0: F = F[:, [0, 2, 1]]
                parts.append((V, F, C, sp))
        # fin
        fin = [[(0, 0.2, -2.12), (0.05, 0.2, -1.7), (0, 0.2, -1.3), (-0.05, 0.2, -1.7)],
               [(0, 0.98, -2.12), (0.03, 0.98, -1.95), (0, 0.98, -1.8), (-0.03, 0.98, -1.95)]]
        V = np.array(fin, np.float32).reshape(-1, 3)
        Vf, Ff = self._prism(V[:4], V[4:], top=True)
        parts.append((Vf, Ff, np.tile(hexc(trim), (len(Ff), 1)), 0.3))
        # canopy: half-octagon bubble
        cs = [(-0.35, 0.12, 0.05), (-0.05, 0.27, 0.2), (0.35, 0.29, 0.24), (0.62, 0.22, 0.12), (0.78, 0.1, 0.0)]
        ca = np.linspace(0, np.pi, 5)
        rings = [np.stack([np.cos(ca) * hw, 0.36 + np.sin(ca) * hh, np.full(5, z)], 1) for z, hw, hh in cs]
        V = np.vstack(rings); F = []
        for i in range(len(cs) - 1):
            for k in range(4):
                a, b = i * 5 + k, i * 5 + k + 1
                F += [(a, b, a + 5), (b, b + 5, a + 5)]
        F = self._orient(V, F, [0, 0.3, 0.2])
        parts.append((V, F, np.tile(hexc(canopy), (len(F), 1)), 1.4))
        # spinner
        sa = np.arange(6) * np.pi / 3
        base = np.stack([np.cos(sa) * 0.17, -0.03 + np.sin(sa) * 0.17, np.full(6, 1.38)], 1)
        V = np.vstack([base, [0, -0.03, 1.78]])
        F = self._orient(V, [(k, (k + 1) % 6, 6) for k in range(6)], [0, -0.03, 1.45])
        parts.append((V, F, np.tile(hexc(spinner), (len(F), 1)), 0.6))
        for V, F, C, sp in parts:
            self.mesh(place(V), F, C, spec=sp, shine=12, name='plane')
        if prop:                                         # the blur of a spinning propeller: a half-transparent disc
            pa = np.arange(14) * 2 * np.pi / 14
            rim = np.stack([np.cos(pa) * 1.0, -0.03 + np.sin(pa) * 1.0, np.full(14, 1.5)], 1)
            V = np.vstack([rim, [0, -0.03, 1.5]])
            F = [(k, (k + 1) % 14, 14) for k in range(14)]
            self.mesh(place(V), F, '#ece8dc', blend='half', alpha=0.36, two_sided=True, lit=False, name='prop')
            ra = np.arange(14) * 2 * np.pi / 14                # the tip circle, a little brighter
            outer = np.stack([np.cos(ra) * 1.0, -0.03 + np.sin(ra) * 1.0, np.full(14, 1.49)], 1)
            inner = np.stack([np.cos(ra) * 0.88, -0.03 + np.sin(ra) * 0.88, np.full(14, 1.49)], 1)
            V = np.vstack([outer, inner])
            F = [f for k in range(14) for f in ((k, (k + 1) % 14, 14 + k), ((k + 1) % 14, 14 + (k + 1) % 14, 14 + k))]
            self.mesh(place(V), F, '#ffffff', blend='half', alpha=0.3, two_sided=True, lit=False, name='prop')
            for a in (0.5, 0.5 + np.pi):                     # two smeared blades, a little darker
                d = np.array([np.cos(a), np.sin(a), 0]); e = np.array([-np.sin(a), np.cos(a), 0])
                c0 = np.array([0, -0.03, 1.51])
                V = np.array([c0 + e * 0.07, c0 + d * 0.98 + e * 0.17, c0 + d * 0.98 - e * 0.05, c0 - e * 0.04])
                self.mesh(place(V), [(0, 1, 2), (0, 2, 3)], '#3a3630', blend='half', alpha=0.4, two_sided=True,
                          lit=False, name='prop')
        return B

    def shadow(self, x, z, y, radius=1.6, stretch=1.0, heading=(0, 0, 1), strength=0.2, sides=10):
        """the blob shadow of the era: a dark polygon laid on the ground straight below an object ('sub' blend,
        drawn after the surface it lies on)"""
        h = _unit(heading); s = np.cross([0, 1, 0], h)
        a = np.arange(sides) * 2 * np.pi / sides
        rim = np.array([x, y, z]) + np.outer(np.cos(a) * radius, s) + np.outer(np.sin(a) * radius * stretch, h)
        V = np.vstack([rim, [x, y, z]])
        F = [(k, (k + 1) % sides, sides) for k in range(sides)]
        return self.mesh(V, F, np.full(3, strength), blend='sub', lit=False, two_sided=True, bias=-6.0, name='shadow')

    def sparkle(self, p, size=1.2, colour='#ffffff', strength=1.0):
        """an additive four-point star sprite facing the camera"""
        r, u = self.R[0] * size / 2, self.R[1] * size / 2
        p = np.asarray(p, np.float32)
        V = np.array([p - r - u, p + r - u, p + r + u, p - r + u])
        uv = np.array([[(0, 1), (1, 1), (1, 0)], [(0, 1), (1, 0), (0, 0)]], np.float32) * 0.999
        return self.mesh(V, [(0, 1, 2), (0, 2, 3)], _c(colour) * strength, uv=uv, tex='spark', blend='add',
                         lit=False, two_sided=True, bias=-3.0, name='fx')

    def flare(self, strength=1.0, elements=None):
        """a lens flare in screen space from the sun through the centre of the frame (only if the sun is not
        hidden behind geometry): hexagons, rings and discs in 'add' mode"""
        els = elements or [(0.0, 12, 'disc', '#fff4d0', 0.35), (0.16, 4, 'hex', '#ffd890', 0.3),
                           (0.3, 2, 'disc', '#ffffff', 0.45), (0.44, 2, 'disc', '#a8f0b0', 0.4),
                           (0.62, 3, 'disc', '#a8c8ff', 0.4), (0.8, 5, 'hex', '#e8b0ff', 0.2),
                           (1.15, 15, 'hex', '#a0d0ff', 0.07), (1.15, 15, 'hexring', '#c8e0ff', 0.2)]
        self.post.append(('flare', strength, els))

    # ------------------------------------------------------------ rendering
    def _gather(self, textures):
        """all meshes as one triangle list. With textures off, surfaces show their flat preview colour (the texel
        under each face centre); additive sprites keep their texture, they are light, not surface"""
        M = self.meshes
        cat = lambda k: np.concatenate([m[k] for m in M])
        per = lambda k, dt=np.float32: np.concatenate([np.full(len(m['P']), m[k], dt) for m in M])
        names = sorted({m['tex'] for m in M if m['tex'] is not None})
        use = [m['tex'] is not None and (textures or m['blend'] == BLEND['add']) for m in M]
        tid = np.concatenate([np.full(len(m['P']), names.index(m['tex']) if u else -1, np.int32) for m, u in zip(M, use)])
        col = np.concatenate([m['col'] if (u or m['tex'] is None) else m['flat'] for m, u in zip(M, use)])
        return dict(P=cat('P'), N=cat('N'), col=col, uv=cat('uv'), tid=tid, texs=[self.textures[t] for t in names],
                    lit=per('lit', bool), spec=per('spec'), shine=per('shine'), blend=per('blend', np.int32),
                    alpha=per('alpha'), two=per('two', bool), fog=per('fog', bool), bias=per('bias'),
                    cut=per('cutout', bool), glow=per('glow'))

    def _render(self, wire=False, fog=True, textures=True):
        fb = self._sky().copy()
        self.cov = np.zeros((self.h, self.w), bool)
        if not self.meshes: return fb
        G = self._gather(textures)
        E, R = self.eye, self.R
        P, N = G['P'], G['N']
        cen = P.mean(1)
        front = ((E - cen) * N).sum(-1) > 0
        keep = front | G['two']
        N = np.where(front[:, None], N, -N)
        Pc = (P - E) @ R.T
        z = Pc[..., 2]
        keep &= ~(z < self.near).all(1) & ~(z > self.far).all(1)
        for ax, t in ((0, self.tanx), (1, self.tany)):
            keep &= ~((Pc[..., ax] - Pc[..., 2] * t * 1.02) > 0).all(1)
            keep &= ~((Pc[..., ax] + Pc[..., 2] * t * 1.02) < 0).all(1)
        idx = np.nonzero(keep)[0]
        # ---- flat shading (one colour per face)
        n = N[idx]
        V = _unit(E - cen[idx])
        Ls = self.L_shade
        diff = np.clip(n @ Ls, 0, 1)
        hemi = (0.5 + 0.5 * n[:, 1])[:, None]
        amb = self.gnd_amb * (1 - hemi) + self.sky_amb * hemi
        shade = amb + self.sun_col * diff[:, None]
        H = _unit(V + Ls)
        spec = G['spec'][idx, None] * np.clip((n * H).sum(-1), 0, 1)[:, None] ** G['shine'][idx, None] * self.sun_col
        glow = G['glow'][idx, None]
        shade = shade * (1 - glow) + glow * 1.0
        lit = G['lit'][idx, None]
        mul = np.where(lit, G['col'][idx] * shade, G['col'][idx]).astype(np.float32)
        add = np.where(lit, spec, 0).astype(np.float32)
        # ---- per-vertex fog, near-plane clipping
        Pc = Pc[idx]; uv = G['uv'][idx]
        tri_P, tri_uv, src = [Pc], [uv], [np.arange(len(idx))]
        cross = (Pc[..., 2] < self.near).any(1)
        good = ~cross
        tri_P[0], tri_uv[0], src[0] = Pc[good], uv[good], src[0][good]
        extra_P, extra_uv, extra_src = [], [], []
        for k in np.nonzero(cross)[0]:
            poly = list(zip(Pc[k], uv[k]))
            out = []
            for i in range(3):
                (a, ua), (b, ub) = poly[i], poly[(i + 1) % 3]
                ina, inb = a[2] >= self.near, b[2] >= self.near
                if ina: out.append((a, ua))
                if ina != inb:
                    t = (self.near - a[2]) / (b[2] - a[2])
                    out.append((a + (b - a) * t, ua + (ub - ua) * t))
            for i in range(1, len(out) - 1):
                extra_P.append([out[0][0], out[i][0], out[i + 1][0]])
                extra_uv.append([out[0][1], out[i][1], out[i + 1][1]])
                extra_src.append(k)
        if extra_P:
            tri_P.append(np.array(extra_P, np.float32)); tri_uv.append(np.array(extra_uv, np.float32))
            src.append(np.array(extra_src))
        Pc = np.concatenate(tri_P); uv = np.concatenate(tri_uv); src = np.concatenate(src)
        gi = idx[src]
        zc = Pc[..., 2]
        if fog and self.fog_on:
            fv = np.clip((np.linalg.norm(Pc, axis=-1) - self.fog_near) / (self.fog_far - self.fog_near), 0, 1)
            fv = fv * G['fog'][gi, None]
        else:
            fv = np.zeros_like(zc)
        sx = np.round(self.cx + self.f * Pc[..., 0] / zc).clip(-30000, 30000).astype(np.int32)
        sy = np.round(self.cy - self.f * Pc[..., 1] / zc).clip(-30000, 30000).astype(np.int32)
        key = zc.mean(1) + G['bias'][gi]
        order = np.argsort(-key, kind='stable')
        zb = np.full((self.h, self.w), np.inf, np.float32) if self.zbuffer else None
        fogc = self.fog_col.astype(np.float32)
        texs = G['texs']; tid = G['tid'][gi]; blend = G['blend'][gi]; alpha = G['alpha'][gi]; cut = G['cut'][gi]
        mul = mul[src]; add = add[src]
        Wf, Hf = self.w, self.h
        wire_fill, wire_line = hexc('#0b1424'), hexc('#9dfcd0')
        for k in order:
            X = sx[k]; Y = sy[k]
            ax, bx, cx = int(X[0]), int(X[1]), int(X[2]); ay, by, cy = int(Y[0]), int(Y[1]), int(Y[2])
            area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            if area == 0: continue
            vi = [0, 1, 2]
            if area < 0:
                bx, cx, by, cy = cx, bx, cy, by; vi = [0, 2, 1]; area = -area
            x0, x1 = max(min(ax, bx, cx), 0), min(max(ax, bx, cx), Wf)
            y0, y1 = max(min(ay, by, cy), 0), min(max(ay, by, cy), Hf)
            if x0 >= x1 or y0 >= y1: continue
            px = np.arange(x0, x1, dtype=np.int64)[None, :] * 2 + 1
            py = np.arange(y0, y1, dtype=np.int64)[:, None] * 2 + 1

            def edge(Ax, Ay, Bx, By):
                e = (2 * Bx - 2 * Ax) * (py - 2 * Ay) - (2 * By - 2 * Ay) * (px - 2 * Ax)
                dx, dy = Bx - Ax, By - Ay
                return e, (dy < 0) or (dy == 0 and dx > 0)
            ea, ta = edge(bx, by, cx, cy)
            eb, tb = edge(cx, cy, ax, ay)
            ec, tc = edge(ax, ay, bx, by)
            ins = ((ea > 0) | ((ea == 0) & ta)) & ((eb > 0) | ((eb == 0) & tb)) & ((ec > 0) | ((ec == 0) & tc))
            yy, xx = np.nonzero(ins)
            if len(yy) == 0: continue
            A2 = float(4 * area)
            wa, wb, wc = ea[yy, xx] / A2, eb[yy, xx] / A2, ec[yy, xx] / A2
            Yp, Xp = yy + y0, xx + x0
            f3 = fv[k][vi]
            fpx = wa * f3[0] + wb * f3[1] + wc * f3[2]
            if zb is not None:
                z3 = zc[k][vi]
                zpx = wa * z3[0] + wb * z3[1] + wc * z3[2]
                ok = zpx < zb[Yp, Xp]
                if not ok.any(): continue
                Yp, Xp, wa, wb, wc, fpx, zpx = Yp[ok], Xp[ok], wa[ok], wb[ok], wc[ok], fpx[ok], zpx[ok]
            bm = blend[k]
            if wire:
                if bm != 0: continue
                fb[Yp, Xp] = wire_fill * (1 - fpx[:, None]) + fogc * fpx[:, None] * 0.25
                for (p, q) in ((0, 1), (1, 2), (2, 0)):
                    P0 = (int(X[p]), int(Y[p])); P1 = (int(X[q]), int(Y[q]))
                    m = max(abs(P1[0] - P0[0]), abs(P1[1] - P0[1])) + 1
                    if m > 4000: continue
                    lx = np.round(np.linspace(P0[0], P1[0], m)).astype(int)
                    ly = np.round(np.linspace(P0[1], P1[1], m)).astype(int)
                    okl = (lx >= 0) & (lx < Wf) & (ly >= 0) & (ly < Hf)
                    ff = (fv[k][p] + fv[k][q]) / 2
                    fb[ly[okl], lx[okl]] = wire_line * (1 - ff) + wire_fill * ff
                self.cov[Yp, Xp] = True
                continue
            t = tid[k]
            src_c = np.broadcast_to(mul[k], (len(Yp), 3))
            a_px = None
            if t >= 0:
                T = texs[t]
                u3 = uv[k][vi]
                upx = wa * u3[0, 0] + wb * u3[1, 0] + wc * u3[2, 0]
                vpx = wa * u3[0, 1] + wb * u3[1, 1] + wc * u3[2, 1]
                iu = np.floor(upx * T.shape[1]).astype(np.int64) % T.shape[1]
                iv = np.floor(vpx * T.shape[0]).astype(np.int64) % T.shape[0]
                texel = T[iv, iu]
                if cut[k]:
                    ok = texel[:, 3] > 0.5
                    Yp, Xp, fpx, texel = Yp[ok], Xp[ok], fpx[ok], texel[ok]
                    if not len(Yp): continue
                    if zb is not None: zpx = zpx[ok]
                src_c = texel[:, :3] * mul[k]
                a_px = texel[:, 3]
            src_c = src_c + add[k]
            fp = fpx[:, None]
            if bm == 0:
                fb[Yp, Xp] = src_c * (1 - fp) + fogc * fp
                self.cov[Yp, Xp] = True
                if zb is not None: zb[Yp, Xp] = zpx
            elif bm == 1:
                a = alpha[k] * (a_px[:, None] if a_px is not None else 1)
                fb[Yp, Xp] = fb[Yp, Xp] * (1 - a) + (src_c * (1 - fp) + fogc * fp) * a
            elif bm == 2 or bm == 4:
                a = (a_px[:, None] if a_px is not None else 1) * (1 if bm == 2 else 0.25)
                fb[Yp, Xp] = fb[Yp, Xp] + src_c * (1 - fp) * a
            elif bm == 3:
                fb[Yp, Xp] = fb[Yp, Xp] - src_c * (1 - fp)
        return np.clip(fb, 0, 1)

    def _post(self, fb, fx=True):
        for op in self.post:
            if op[0] == 'flare' and fx:
                fb = self._flare(fb, op[1], op[2])
        return fb

    def _flare(self, fb, strength, els):
        d = (self.L @ self.R.T)
        if d[2] <= 0.05: return fb
        sx, sy = self.cx + self.f * d[0] / d[2], self.cy - self.f * d[1] / d[2]
        if not (0 <= sx < self.w and 0 <= sy < self.h): return fb
        if self.cov[int(sy), int(sx)]: return fb
        yy, xx = np.mgrid[0:self.h, 0:self.w].astype(np.float32) + 0.5
        cxs, cys = self.cx, self.cy
        for t, rad, kind, col, a in els:
            px, py = sx + (cxs - sx) * t * 2, sy + (cys - sy) * t * 2
            dx, dy = xx - px, yy - py
            if kind in ('hex', 'hexring'):
                ang = np.arctan2(dy, dx)
                rr = np.hypot(dx, dy) * np.cos((ang % (np.pi / 3)) - np.pi / 6) / np.cos(np.pi / 6)
                if kind == 'hex':
                    m = (rr < rad).astype(np.float32) * (0.6 + 0.4 * (rr / rad))
                else:
                    m = ((rr < rad) & (rr >= rad - 1.2)).astype(np.float32)
            elif kind == 'ring':
                rr = np.hypot(dx, dy)
                m = ((rr < rad) & (rr > rad * 0.78)).astype(np.float32)
            else:
                rr = np.hypot(dx, dy)
                m = np.clip(1 - rr / rad, 0, 1) ** 1.5
            fb = fb + hexc(col) * (m * a * strength)[..., None]
        return np.clip(fb, 0, 1)

    def _crush(self, fb):
        """15-bit colour through the 4x4 ordered dither: 8-bit value + offset, then truncate to 5 bits"""
        v = fb * 255
        if self.dither:
            D = np.tile(DITHER, (self.h // 4 + 1, self.w // 4 + 1))[:self.h, :self.w]
            v = v + D[..., None]
        step = 256 >> self.bits
        q = np.clip(np.floor(v / step), 0, (1 << self.bits) - 1)
        q = q * step + q // (1 << (self.bits - 3)) if self.bits == 5 else q * step
        return (q / 255).astype(np.float32)

    def composite(self, wire=False, fog=True, textures=True, fx=True, hud=True):
        fb = self._render(wire=wire, fog=fog, textures=textures)
        fb = self._post(fb, fx=fx and not wire)
        q = self._crush(fb)
        if hud:
            for op in self.hud: op(q)
        img = Image.fromarray((np.clip(q, 0, 1) * 255 + 0.5).astype(np.uint8))
        return img.resize((self.W, self.H), Image.NEAREST)

    # ------------------------------------------------------------ HUD (framebuffer pixels)
    def _glyphs(self, s, scale=1, bold=True, italic=0, spacing=1):
        cols = []
        for ch in s:
            g = FONT.get(ch, FONT.get(ch.upper(), FONT[' ']))
            a = np.array([[c == '#' for c in row] for row in g], bool)
            if bold:
                a = np.concatenate([a, np.zeros((7, 1), bool)], 1)
                a[:, 1:] |= a[:, :-1].copy()
            cols += [a, np.zeros((7, spacing), bool)]
        m = np.concatenate(cols[:-1], 1) if cols else np.zeros((7, 1), bool)
        m = np.kron(m, np.ones((scale, scale), bool))
        if italic:
            h = m.shape[0]
            out = np.zeros((h, m.shape[1] + italic), bool)
            for r in range(h):
                o = int(round(italic * (h - 1 - r) / max(h - 1, 1)))
                out[r, o:o + m.shape[1]] = m[r]
            m = out
        return m

    def text_width(self, s, scale=1, bold=True, italic=0, spacing=1):
        return self._glyphs(s, scale, bold, italic, spacing).shape[1]

    def _stamp(self, q, m, x, y, fill, outline=BLACK, shadow=True):
        H, W = m.shape
        pad = 2
        M = np.zeros((H + 2 * pad, W + 2 * pad), bool)
        M[pad:pad + H, pad:pad + W] = m
        O = M.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                O |= np.roll(np.roll(M, dy, 0), dx, 1)
        S = np.roll(np.roll(O, 1, 0), 1, 1) & ~O
        x0, y0 = int(x) - pad, int(y) - pad
        ys, xs = np.nonzero(S | O)
        Y, X = ys + y0, xs + x0
        ok = (Y >= 0) & (Y < self.h) & (X >= 0) & (X < self.w)
        if shadow:
            sel = S[ys, xs] & ok
            q[Y[sel], X[sel]] = q[Y[sel], X[sel]] * 0.35
        if outline is not None:
            sel = O[ys, xs] & ~M[ys, xs] & ok
            q[Y[sel], X[sel]] = _q5(_c(outline))
        ys, xs = np.nonzero(M)
        Y, X = ys + y0, xs + x0
        ok = (Y >= 0) & (Y < self.h) & (X >= 0) & (X < self.w)
        if isinstance(fill, (tuple, list)) and not isinstance(fill[0], (int, float)):
            cols = [_c(c) for c in fill]
            t = (ys - pad) / max(H - 1, 1)
            seg = np.clip(t * (len(cols) - 1), 0, len(cols) - 1 - 1e-6)
            i0 = seg.astype(int); fr = (seg - i0)[:, None]
            col = np.array(cols)[i0] * (1 - fr) + np.array(cols)[i0 + 1] * fr
        else:
            col = np.broadcast_to(_c(fill), (len(ys), 3))
        q[Y[ok], X[ok]] = _q5(col[ok])

    def text(self, s, x, y, scale=1, fill=WHITE, outline=BLACK, shadow=True, italic=0, anchor='l', bold=True, spacing=1):
        """bitmap HUD text at framebuffer pixel (x, y) = top-left (anchor 'l'), top-right ('r') or top-centre ('m').
        fill is a colour or a list of colours for a top-to-bottom ramp"""
        def op(q):
            m = self._glyphs(s, scale, bold, italic, spacing)
            xx = x - (m.shape[1] if anchor == 'r' else m.shape[1] // 2 if anchor == 'm' else 0)
            self._stamp(q, m, xx, y, fill, outline, shadow)
        self.hud.append(op)

    def icon(self, kind, x, y, size=1):
        """HUD icons: 'ring' (a little gold hoop), 'plane' (top view), 'clock'"""
        pics = {
            'ring': ['  ####  ', ' #....# ', '#.    .#', '#.    .#', '#.    .#', '#.    .#', ' #....# ', '  ####  '],
            'plane': ['    #    ', '    #    ', '   ###   ', '#########', ' ####### ', '    #    ', '   ###   ', '    #    '],
            'clock': ['  ####  ', ' #....# ', '#...#..#', '#...#..#', '#...##.#', '#......#', ' #....# ', '  ####  '],
        }
        cmap = {'ring': {'#': '#ffcc33', '.': '#b06a10'}, 'plane': {'#': '#f4f1e8'},
                'clock': {'#': '#f4f1e8', '.': '#5a6a8a'}}[kind]
        rows = pics[kind]

        def op(q):
            for ch, col in cmap.items():
                m = np.array([[c == ch for c in row] for row in rows], bool)
                m = np.kron(m, np.ones((size, size), bool))
                self._stamp(q, m, x, y, col, outline=BLACK if ch == '#' else None, shadow=ch == '#')
        self.hud.append(op)

    def counter(self, label, value, x, y, icon=None, anchor='l', label_fill=HUD_CYAN, fill=(HUD_YELLOW, HUD_ORANGE, '#d0501a'),
                scale=2, italic=3):
        """a labelled HUD counter: small label over big italic ramp digits, optional icon on the left"""
        if icon:
            self.icon(icon, x, y + 4, size=2)
            x += 20
        if anchor == 'r':
            self.text(label, x, y, 1, label_fill, anchor='r')
            self.text(value, x, y + 10, scale, list(fill), italic=italic, anchor='r')
        else:
            self.text(label, x, y, 1, label_fill)
            self.text(value, x, y + 10, scale, list(fill), italic=italic)

    def panel(self, x0, y0, x1, y1, colour='#101c3a', alpha=0.55, border='#a8c8ff'):
        """a translucent HUD box with a 1 px light frame and dark corners cut"""
        def op(q):
            q[y0:y1, x0:x1] = q[y0:y1, x0:x1] * (1 - alpha) + _c(colour) * alpha
            if border is not None:
                b = _q5(_c(border))
                q[y0, x0 + 1:x1 - 1] = b; q[y1 - 1, x0 + 1:x1 - 1] = b
                q[y0 + 1:y1 - 1, x0] = b; q[y0 + 1:y1 - 1, x1 - 1] = b
            q[...] = self._snap(q)
        self.hud.append(op)

    @staticmethod
    def _snap(q):
        v = np.clip(np.floor(q * 31 + 0.5), 0, 31)
        return ((v * 8 + v // 4) / 255).astype(np.float32)

    def gauge(self, x, y, value, segments=12, label='SPD', unit='KM/H', number=None, colours=(HUD_GREEN, HUD_YELLOW, HUD_RED)):
        """a stepped speed bar: segments grow taller left to right, lit up to `value` (0..1), green -> yellow -> red"""
        def op(q):
            cols = [_c(c) for c in colours]
            lit = int(round(value * segments))
            for i in range(segments):
                h = 4 + i // 2
                sx = x + i * 4
                t = i / max(segments - 1, 1) * (len(cols) - 1)
                i0 = min(int(t), len(cols) - 2); fr = t - i0
                c = cols[i0] * (1 - fr) + cols[i0 + 1] * fr
                if i >= lit: c = np.array([0.18, 0.2, 0.26])
                q[y + 10 - h - 1:y + 11, sx - 1:sx + 4] = 0
                q[y + 10 - h:y + 10, sx:sx + 3] = _q5(c)
        self.hud.append(op)
        if label: self.text(label, x, y - 9, 1, HUD_CYAN)
        if number is not None:
            self.text(number, x + segments * 4 + 6, y - 6, 2, [HUD_YELLOW, HUD_ORANGE, '#d0501a'], italic=3)
            self.text(unit, x + segments * 4 + 6 + self.text_width(number, 2, italic=3) + 4, y + 2, 1, HUD_CYAN)

    def minimap(self, x0, y0, x1, y1, path, s0, s1, rings, done, plane, heading, finish=None, title=None,
                band='#c98a52', river='#5fb8c8'):
        """a translucent top-down course map, turned so the plane heads up: canyon band, river, hoops (passed dim,
        next bright and boxed, later orange), finish flag, the plane as an arrow"""
        self.panel(x0, y0, x1, y1)
        def op(q):
            h = _unit(np.array([heading[0], heading[2]], np.float32))
            ss = np.arange(s0, s1, 1.0)
            x, z, *_ = path.at(ss)
            pts = np.stack([x, z], 1)
            rot = np.array([[h[1], -h[0]], [h[0], h[1]]], np.float32)       # world xz -> map (right, forward)
            org = np.array([plane[0], plane[2]], np.float32)
            Q = (pts - org) @ rot.T
            lo, hi = Q.min(0), Q.max(0)
            m = 6
            sc = min((x1 - x0 - 2 * m) / max(hi[0] - lo[0], 1), (y1 - y0 - 2 * m - (8 if title else 0)) / max(hi[1] - lo[1], 1))
            mid = (lo + hi) / 2
            cxm, cym = (x0 + x1) / 2, (y0 + y1) / 2 + (4 if title else 0)
            tomap = lambda P: np.stack([cxm + (P[..., 0] - mid[0]) * sc, cym - (P[..., 1] - mid[1]) * sc], -1)
            M = tomap(Q)

            def dots(P, r, col):
                for px, py in P:
                    xi, yi = int(round(px)), int(round(py))
                    q[max(yi - r, y0 + 1):min(yi + r + 1, y1 - 1), max(xi - r, x0 + 1):min(xi + r + 1, x1 - 1)] = _q5(_c(col))
            dots(M[::1], 2, band)
            dots(M[::1], 0, river)
            for i, rp in enumerate(rings):
                R2 = tomap((np.array([[rp[0], rp[2]]], np.float32) - org) @ rot.T)
                if i < done: dots(R2, 1, '#6a6a7a')
                elif i == done:
                    xi, yi = int(round(R2[0, 0])), int(round(R2[0, 1]))
                    q[yi - 3:yi + 4, xi - 3:xi + 4] = _q5(_c('#000000'))
                    q[yi - 2:yi + 3, xi - 2:xi + 3] = _q5(_c(HUD_YELLOW))
                    q[yi - 1:yi + 2, xi - 1:xi + 2] = _q5(_c('#000000'))
                else: dots(R2, 1, HUD_ORANGE)
            if finish is not None:
                F2 = tomap((np.array([[finish[0], finish[2]]], np.float32) - org) @ rot.T)[0]
                xi, yi = int(round(F2[0])), int(round(F2[1]))
                for j in range(-3, 3):
                    for i in range(-3, 3):
                        q[yi + j, xi + i] = _q5(_c('#ffffff' if (i + j) % 2 else '#000000'))
            P2 = tomap(np.zeros((1, 2), np.float32))[0]
            xi, yi = int(round(P2[0])), int(round(P2[1]))
            arrow = ['  #  ', '  #  ', ' ### ', ' ### ', '#####', '## ##']
            for j, row in enumerate(arrow):
                for i, c in enumerate(row):
                    if c == '#': q[yi - 3 + j, xi - 2 + i] = _q5(_c('#ffffff'))
        self.hud.append(op)
        if title: self.text(title, (x0 + x1) // 2, y0 + 3, 1, HUD_CYAN, anchor='m', shadow=False)

    # ------------------------------------------------------------ output
    def stage(self, name, wire=False, fog=True, textures=True, fx=True, hud=True):
        """snapshot for the draw-on GIF; wire=True draws hidden-line wireframe, fog/textures can be held back"""
        if self.record:
            self.stages.append((name, self.composite(wire=wire, fog=fog, textures=textures, fx=fx, hud=hud)))

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
