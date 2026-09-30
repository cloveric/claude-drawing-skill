"""soft3d — soft pastel 3D renders: a sea of small candy balls, puffy extruded letters and rounded solids, lit
like a product shot in a photo studio (numpy + Pillow only).

Model: a real (small) 3D renderer, not a 2D imitation. A pinhole camera looks into a scene measured in world units
(X right, Y up, Z away from the camera); every pixel is a ray.
  geometry  analytic wherever possible, so edges stay clean and ten thousand objects stay cheap:
            ball field   thousands of spheres on a square grid resting on a floor, each a little different in size,
                         position and colour. A ray walks the grid cell by cell (a DDA) and tests only the one ball
                         in each cell, so the whole sea costs about as much as a handful of balls.
            loose balls  any size, anywhere (on top of the sea, riding on a letter, the dot of an i): exact
                         ray-sphere tests through a depth buffer. drop() lets a ball fall until it touches
                         something and roll down into the nearest hollow.
            heroes       signed distance fields, ray-marched only inside their own bounding boxes: puffy letters
                         (font glyph -> exact 2D distance transform -> extruded, edges rounded right through, then
                         inflated like a balloon), rounded boxes, capsules, rounded cylinders, tori; each with its
                         own position and rotation.
            part()       heroes rising through the sea push it aside: balls they overlap are gone, the balls around
                         them are heaped into a soft mound that hugs their feet.
            The whole scene can also be asked "how far is the nearest surface from here?" (a distance field built
            from the same grid, a hash of the loose balls and the heroes) -- that is what the light uses.
  light     a photo studio, not a sun:
            sky      a big gradient dome (backdrop colour above, a bounce of the floor colour below) lights every
                     surface by its normal, dimmed by ambient occlusion sampled in the distance field (the dark
                     crevices between balls, the foot of a letter). The occlusion is coloured: shaded pastel
                     material turns deeper and more saturated instead of grey, the way light scatters inside it.
            key      a large area light: wrap-around diffuse (light bleeds a saturated tint across the terminator:
                     the subsurface look), soft shadows marched through the distance field whose penumbra widens
                     with distance from the occluder, tinted the same way.
            rim      a back light that outlines silhouettes.
            gloss    every light is also a softbox seen in reflections: glossy candy mirrors a crisp rounded
                     panel, satin balls a broad soft sheen; Fresnel makes grazing edges reflective, and the sky
                     gradient and the floor colour show up in the lower half of every reflection.
  lens      aerial haze toward the horizon, then a thin-lens depth of field: a circle of confusion from depth,
            gathered in layers so a sharp subject never smears into the blurred background behind it.
  film      a gentle tone curve (pastel highlights roll off instead of clipping), bloom, vignette, fine grain.
Stages: stage() is a real re-render, at preview size, of what exists so far -- grey clay (no sky yet) -> materials
under the sky -> key and rim light -> film, the way a 3D scene is built up. Set lens() early (with the camera) and
every stage already has the depth of field: softer previews, and a drawing GIF that compresses much better.
Angles are degrees. Light azimuth is measured from the camera: 0 = from behind the camera, -90 = from the left,
+90 = from the right, 180 = from behind the subject. Hero yaw > 0 turns its front toward the left, pitch > 0 leans
it back, roll > 0 leans it left (counter-clockwise on screen, like PIL).

    from soft3d import Soft3D
    s = Soft3D(1920, 1080, seed=1, eye=(0, 2.1, -6.2), target=(0, 0.6, 0.4), fov=29)
    s.floor('#b9e6d4')
    s.ball_field(-12, 12, -5, 40, r=0.1, colours=['#c4ecdc', '#b8e5d2'])
    word = s.text('hey', at=(0, -0.2, 0.4), size=2.2, colour='#ff6a88')
    s.part(heap=0.09)
    s.drop(0.3, 1.0, 0.1, '#ffd35c')                  # a loose ball falls and rolls into a hollow
    s.sky('#cfc6f4', '#fbe4dc')
    s.key(azimuth=-40, elevation=48)
    s.rim(azimuth=160)
    s.lens(focus=word)
    s.film()
    s.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, smoothstep, load_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _lin(c):
    """sRGB-ish colour -> linear light (all lighting is done in linear light)"""
    return np.power(_c(c), 2.2).astype(np.float32)


def _unit(v):
    v = np.asarray(v, np.float32)
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + 1e-12)


def _rot(yaw=0.0, pitch=0.0, roll=0.0):
    """local -> world rotation (degrees): roll about Z, then pitch about X, then yaw about Y"""
    a, b, c = np.radians([yaw, pitch, roll])
    Ry = np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(b), -np.sin(b)], [0, np.sin(b), np.cos(b)]])
    Rz = np.array([[np.cos(c), -np.sin(c), 0], [np.sin(c), np.cos(c), 0], [0, 0, 1]])
    return (Ry @ Rx @ Rz).astype(np.float32)


def _edt(mask, R):
    """distance (px) from every pixel to the nearest True pixel of `mask`: exact up to R px, capped at R.
    Rows first (nearest set pixel on the same row, by running max / min of indices), then columns within +-R."""
    H, W = mask.shape
    idx = np.arange(W, dtype=np.float32)[None, :]
    left = np.maximum.accumulate(np.where(mask, idx, -1e6), axis=1)
    right = np.minimum.accumulate(np.where(mask, idx, 1e6)[:, ::-1], axis=1)[:, ::-1]
    g = np.minimum(np.minimum(idx - left, right - idx), R + 1).astype(np.float32)
    g2 = g * g
    D = g2.copy()
    for k in range(1, int(R) + 1):
        kk = np.float32(k * k)
        np.minimum(D[k:], g2[:-k] + kk, out=D[k:])
        np.minimum(D[:-k], g2[k:] + kk, out=D[:-k])
    return np.minimum(np.sqrt(D), R)


def _bilinear(a, x, y):
    H, W = a.shape
    x = np.clip(x, 0, W - 1.001); y = np.clip(y, 0, H - 1.001)
    x0 = x.astype(np.int32); y0 = y.astype(np.int32)
    fx = x - x0; fy = y - y0
    f = a.ravel(); i = y0 * W + x0
    return (f[i] * (1 - fx) + f[i + 1] * fx) * (1 - fy) + (f[i + W] * (1 - fx) + f[i + W + 1] * fx) * fy


def _blur_big(a, sigma):
    """gaussian-ish blur of a 2D float array; large radii are done on a downsampled copy"""
    if sigma < 0.3: return a
    k = 1
    while sigma / k > 7 and min(a.shape) / (k * 2) > 32: k *= 2
    if k == 1: return blur(a, sigma)
    H, W = a.shape
    small = np.asarray(Image.fromarray(a.astype(np.float32), 'F').resize((W // k, H // k), Image.BOX))
    small = blur(small, sigma / k)
    return np.asarray(Image.fromarray(small, 'F').resize((W, H), Image.BILINEAR))


def _blur3(img, sigma):
    return np.stack([_blur_big(img[..., i], sigma) for i in range(img.shape[-1])], -1)


# material presets: rough = reflection blur, spec = how much the surface mirrors, sss = how far light wraps and
# how saturated its shade gets, sheen = soft glow along silhouettes
MATERIALS = {
    'satin': dict(rough=0.42, spec=0.55, sss=0.6, sheen=0.22),
    'candy': dict(rough=0.07, spec=1.0, sss=0.8, sheen=0.10),
    'jelly': dict(rough=0.14, spec=0.9, sss=1.0, sheen=0.25),
    'matte': dict(rough=0.8, spec=0.18, sss=0.35, sheen=0.3),
    'pearl': dict(rough=0.25, spec=0.8, sss=0.5, sheen=0.4),
}


class Soft3D:
    def __init__(self, W=1920, H=1080, seed=0, eye=(0, 2.0, -6.0), target=(0, 0.5, 0), fov=30.0, floor=0.0,
                 preview=0.5, record=True):
        """fov: vertical field of view in degrees. preview: scale of the stage() renders. record=False makes
        stage() a no-op (no preview renders)."""
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.floor_y = float(floor)
        self.preview, self.record = preview, record
        self.camera(eye, target, fov)
        self.mats, self._matkey = [], {}
        self.floor_mat = self._mat('#d8d8d8', 'matte')
        self.field = None
        self.bc = np.zeros((0, 3), np.float32); self.br = np.zeros(0, np.float32); self.bm = np.zeros(0, np.int32)
        self.heroes = []
        self.env = None; self.lights = []; self.panels = []
        self.lens_cfg = None; self.film_cfg = None
        self.version = 0; self._cache = {}; self._hash = None
        self.stages = []

    # ------------------------------------------------------------------ camera
    def camera(self, eye, target, fov=30.0):
        self.eye = np.asarray(eye, np.float32); self.target = np.asarray(target, np.float32)
        self.fwd = _unit(self.target - self.eye)
        self.right = _unit(np.cross([0, 1, 0], self.fwd))
        self.up = np.cross(self.fwd, self.right).astype(np.float32)
        self.fov = float(fov)
        self._cache = {}

    def _focal(self, h):
        return (h / 2) / np.tan(np.radians(self.fov) / 2)

    def project(self, X, Y, Z, scale=1.0):
        """world point -> (x, y) pixel position and camera depth"""
        w, h = self.W * scale, self.H * scale; f = self._focal(h)
        rel = np.asarray([X, Y, Z], np.float32) - self.eye
        zc = float(rel @ self.fwd)
        return w / 2 + f * float(rel @ self.right) / zc, h / 2 - f * float(rel @ self.up) / zc, zc

    # ------------------------------------------------------------------ materials
    def _mat(self, colour, kind='satin', **kw):
        key = (tuple(np.round(_c(colour), 4)), kind, tuple(sorted(kw.items())))
        if key in self._matkey: return self._matkey[key]
        p = dict(MATERIALS[kind]); p.update(kw)
        alb = _lin(colour)
        tint = alb ** 0.9 / (alb ** 0.9).max()                 # the material's own saturated hue, peak 1
        tint = np.clip(tint * 1.0, 0.05, 1)
        self.mats.append(dict(alb=alb, tint=tint.astype(np.float32), **p))
        self._matkey[key] = len(self.mats) - 1
        self._mtab = None
        return len(self.mats) - 1

    def _mat_table(self):
        if getattr(self, '_mtab', None) is None:
            self._mtab = {k: np.array([m[k] for m in self.mats], np.float32)
                          for k in ('alb', 'tint', 'rough', 'spec', 'sss', 'sheen')}
        return self._mtab

    def _touch(self):
        self.version += 1; self._hash = None

    # ------------------------------------------------------------------ geometry: floor and the ball field
    def floor(self, colour='#d0d0d0', mat='matte'):
        """the ground plane at y = floor (seen only in the gaps between balls and beyond the field)"""
        self.floor_mat = self._mat(colour, mat); self._touch()

    def ball_field(self, x0, x1, z0, z1, r=0.1, gap=0.015, colours=('#c4ecdc',), weights=None, mat='satin',
                   size_var=0.05, jitter=0.5, lift_var=0.0):
        """a sea of balls on a square grid resting on the floor. gap: space between neighbours; size_var: relative
        radius spread; jitter: 0..1 of the free room each ball may wander in its cell; lift_var: random height."""
        s = 2 * r + gap
        NI, NJ = int((x1 - x0) / s), int((z1 - z0) / s)
        n = NI * NJ
        rng = self.rng
        rad = r * (1 + size_var * rng.uniform(-1, 1, n))
        rad = np.minimum(rad, s / 2 - 1e-3).astype(np.float32)
        room = s / 2 - rad
        ii, jj = np.meshgrid(np.arange(NI), np.arange(NJ), indexing='ij')
        cx = x0 + (ii.ravel() + 0.5) * s + rng.uniform(-1, 1, n) * room * jitter
        cz = z0 + (jj.ravel() + 0.5) * s + rng.uniform(-1, 1, n) * room * jitter
        cy = self.floor_y + rad + np.abs(rng.normal(0, 1, n)) * lift_var
        wts = np.ones(len(colours)) if weights is None else np.asarray(weights, float)
        pick = rng.choice(len(colours), n, p=wts / wts.sum())
        mids = np.array([self._mat(col, mat) for col in colours], np.int32)
        self.field = dict(s=np.float32(s), x0=np.float32(x0), z0=np.float32(z0), NI=NI, NJ=NJ, r0=r,
                          C=np.stack([cx, cy, cz], 1).astype(np.float32), r=rad, m=mids[pick])
        self._field_bounds()
        self._touch()
        return self.field

    def _field_bounds(self):
        F = self.field; ok = F['r'] > 0
        F['ylo'] = np.float32(self.floor_y - 1e-3)
        F['yhi'] = np.float32((F['C'][ok, 1] + F['r'][ok]).max() + 1e-3)

    def tint_balls(self, x, z, radius, colours, chance=1.0, mat='satin'):
        """recolour field balls within `radius` of (x, z) (a few scattered accents, a coloured patch...)"""
        F = self.field
        d = np.hypot(F['C'][:, 0] - x, F['C'][:, 2] - z)
        sel = np.nonzero((d < radius) & (self.rng.random(len(d)) < chance))[0]
        mids = np.array([self._mat(c, mat) for c in colours], np.int32)
        F['m'][sel] = mids[self.rng.integers(0, len(mids), len(sel))]
        self._touch()

    def part(self, heap=0.05, reach=0.5, pile=1.0, pile_top=None, clear=1.02, seed=None):
        """the heroes push up through the sea. Balls they overlap are shoved aside and pile up around their feet:
        each settles into the nearest free hollow (between four balls of the sea, or on top of the pile), layer on
        layer, and is kept only where it would really rest (three contacts, the floor, or leaning on a hero).
        pile: how many balls pile up, as a multiple of the ones pushed aside; pile_top: the highest a piled ball's
        centre may sit above the floor (keep the heap low so it doesn't hide the bottoms of letters). The sea
        around them swells by `heap`, fading over `reach`, without ever touching a hero."""
        F = self.field; s = float(F['s']); NJ, NI = F['NJ'], F['NI']
        C, r = F['C'], F['r']
        rng = np.random.default_rng(seed) if seed is not None else self.rng
        alive = r > 0
        d = self._heroes_d(C)
        gone = np.nonzero(alive & (d < r * clear))[0]
        gone_m = F['m'][gone].copy()
        r[gone] = 0
        alive[gone] = False
        lift = (heap * np.exp(-(np.maximum(d - r, 0) / reach) ** 2)).astype(np.float32)
        lift[~alive] = 0
        for _ in range(6):                                   # never push a ball into a hero
            P = C.copy(); P[:, 1] += lift
            bad = alive & (lift > 1e-4) & (self._heroes_d(P) < r * clear)
            if not bad.any(): break
            lift[bad] *= 0.5
        C[:, 1] += lift
        self._field_bounds()
        n = int(len(gone) * pile)
        if n:
            r0 = float(F['r0'])
            near = np.nonzero(alive & (d < 5 * s) | np.isin(np.arange(len(r)), gone))[0]
            ci, cj = near // NJ, near % NJ
            cand = np.concatenate([np.stack([ci + a, cj + b], 1) for a in (0, 1) for b in (0, 1)]).astype(np.float32)
            cand = np.unique(cand, axis=0)
            corners = np.stack([F['x0'] + cand[:, 0] * s, F['z0'] + cand[:, 1] * s], 1)
            centres = np.stack([F['x0'] + (ci + 0.5) * s, F['z0'] + (cj + 0.5) * s], 1)
            xz = np.concatenate([corners, centres])
            hd = self._heroes_d(np.stack([xz[:, 0], np.full(len(xz), 2.3 * r0), xz[:, 1]], 1).astype(np.float32))
            order = np.argsort(hd + rng.uniform(0, 0.6 * s, len(hd)) + (np.arange(len(xz)) >= len(corners)) * 0.5 * s)
            pc, pr = [], []
            for q in order:
                if len(pc) >= n: break
                x, z = xz[q]
                if hd[q] > 6 * s: continue
                rb = r0 * (1 + 0.04 * rng.uniform(-1, 1))
                i, j = int((x - F['x0']) // s), int((z - F['z0']) // s)
                cells = [(i + a) * NJ + (j + b) for a in (-1, 0, 1) for b in (-1, 0, 1)
                         if 0 <= i + a < NI and 0 <= j + b < NJ]
                sc, sr = C[cells], r[cells]
                if pc:
                    A = np.asarray(pc, np.float32); B = np.asarray(pr, np.float32)
                    close = np.hypot(A[:, 0] - x, A[:, 2] - z) < 2.5 * r0
                    sc = np.vstack([sc, A[close]]); sr = np.concatenate([sr, B[close]])
                rho = np.hypot(sc[:, 0] - x, sc[:, 2] - z)
                ok = (sr > 0) & (rho < rb + sr)
                ys = sc[ok, 1] + np.sqrt((rb + sr[ok]) ** 2 - rho[ok] ** 2)
                y = max(self.floor_y + rb, ys.max() if len(ys) else -1e9)
                if pile_top is not None and y > self.floor_y + pile_top: continue
                contacts = int((ys > y - 0.025).sum())
                dh = float(self._heroes_d(np.float32([[x, y, z]]))[0])
                if dh < rb * 1.01: continue
                if contacts >= 3 or y <= self.floor_y + rb + 1e-4 or (dh < rb + 0.02 and contacts >= 2):
                    pc.append((x + rng.normal(0, 0.003), y + 1e-3, z + rng.normal(0, 0.003))); pr.append(rb)
            if pc:
                cols = gone_m[rng.integers(0, len(gone_m), len(pc))]
                self.bc = np.vstack([self.bc, np.asarray(pc, np.float32)])
                self.br = np.concatenate([self.br, np.asarray(pr, np.float32)])
                self.bm = np.concatenate([self.bm, cols.astype(np.int32)])
        self._touch()
        return len(gone)

    # ------------------------------------------------------------------ geometry: loose balls
    def ball(self, x, y, z, r, colour, mat='satin'):
        """a loose ball exactly where you say"""
        self.bc = np.vstack([self.bc, np.float32([[x, y, z]])])
        self.br = np.append(self.br, np.float32(r)); self.bm = np.append(self.bm, np.int32(self._mat(colour, mat)))
        self._touch()
        return len(self.br) - 1

    def drop(self, x, z, r, colour, mat='satin', roll=24, y=None):
        """drop a ball straight down at (x, z) until it touches the scene, then let it roll `roll` small steps
        downhill into a hollow (roll=0: it stays balanced where it landed). Returns its centre."""
        top = self._scene_top() + r + 0.5 if y is None else y
        p = np.float32([x, top, z])

        def settle(p):
            for _ in range(400):
                d = float(self._sdf(p[None])[0]) - r
                if d < 2e-4: break
                p[1] -= max(d, 2e-4)
            return p
        p = settle(p)
        for _ in range(roll):
            n = self._grad(p[None])[0]
            h = np.hypot(n[0], n[2])
            if h < 0.03: break
            p[0] += n[0] / h * r * 0.18 * min(1, h * 3); p[2] += n[2] / h * r * 0.18 * min(1, h * 3)
            p[1] += r * 0.3
            p = settle(p)
        self.ball(float(p[0]), float(p[1]) + 2e-4, float(p[2]), r, colour, mat)
        return p

    # ------------------------------------------------------------------ geometry: heroes (signed distance fields)
    def _hero(self, kind, R, t, lo, hi, mat, **kw):
        h = dict(kind=kind, R=np.asarray(R, np.float32), t=np.asarray(t, np.float32),
                 lo=np.asarray(lo, np.float32), hi=np.asarray(hi, np.float32), mat=mat, near=1e9, **kw)
        self.heroes.append(h); self._touch()
        return len(self.heroes) - 1

    def rbox(self, centre, size, radius=0.05, colour='#ffb3c7', mat='candy', yaw=0, pitch=0, roll=0):
        """rounded box; size = full (w, h, d)"""
        b = np.asarray(size, np.float32) / 2
        return self._hero('rbox', _rot(yaw, pitch, roll), centre, -b, b, self._mat(colour, mat), b=b, rr=radius)

    def capsule(self, centre, length, radius, colour='#ffb3c7', mat='candy', yaw=0, pitch=0, roll=0):
        """a pill standing along its local Y axis"""
        hl = length / 2
        e = np.float32([radius, hl + radius, radius])
        return self._hero('capsule', _rot(yaw, pitch, roll), centre, -e, e, self._mat(colour, mat), hl=hl, rad=radius)

    def cylinder(self, centre, radius, height, round=0.04, colour='#ffb3c7', mat='candy', yaw=0, pitch=0, roll=0):
        """rounded cylinder (a puck, a pedestal) along local Y"""
        e = np.float32([radius, height / 2, radius])
        return self._hero('rcyl', _rot(yaw, pitch, roll), centre, -e, e, self._mat(colour, mat),
                          ra=radius, hh=height / 2, rr=round)

    def torus(self, centre, R, r, colour='#ffb3c7', mat='candy', yaw=0, pitch=0, roll=0):
        """a ring lying in the local XZ plane (pitch=90 stands it up)"""
        e = np.float32([R + r, r, R + r])
        return self._hero('torus', _rot(yaw, pitch, roll), centre, -e, e, self._mat(colour, mat), Rt=R, rt=r)

    def _glyph(self, ch, px, style, reach, undot):
        font = load_font(style, px)
        x0, y0, x1, y1 = font.getbbox(ch, anchor='ls')
        m = int(reach) + 8
        ox, oy = m - x0, m - y0
        im = Image.new('L', (x1 - x0 + 2 * m, y1 - y0 + 2 * m), 0)
        ImageDraw.Draw(im).text((ox, oy), ch, font=font, fill=255, anchor='ls')
        a = np.asarray(im, np.float32) / 255
        dot = None
        if undot:                                            # cut the tittle off an i / j: it becomes a ball
            rows = np.nonzero(a.max(1) > 0.5)[0]
            gaps = np.nonzero(np.diff(rows) > 1)[0]
            if len(gaps):
                cut = rows[gaps[0]] + 1
                top = a[:cut].copy(); a = a.copy(); a[:cut] = 0
                ys, xs = np.nonzero(top > 0.5)
                dot = ((xs.mean() - ox), (oy - ys.mean()), np.sqrt(len(xs) / np.pi))
        inside = a >= 0.5
        sd = np.where(inside, -(_edt(~inside, reach) - 0.5), _edt(inside, reach) - 0.5)
        sd = blur(sd.astype(np.float32), 2.0)
        ys, xs = np.nonzero(inside)
        ink = (xs.min() - ox, oy - ys.max(), xs.max() - ox, oy - ys.min())   # px, y up
        return sd, ox, oy, font.getlength(ch), ink, dot, float(-sd.min())

    def text(self, s, at=(0, 0, 0), size=2.0, depth=0.4, colour='#ff6f91', mat='candy', yaw=0.0, pitch=0.0,
             spacing=0.0, round=None, inflate=0.02, style='rounded', bob=None, roll=None, turn=None,
             dot=None, dot_mat='satin', px=360):
        """puffy extruded letters standing on their baseline. at = centre of the word's baseline; size = em height
        (world units); depth = thickness; round = edge radius (default: most of the stroke half-width, so the
        letters are fully rounded like balloons); inflate = how much fatter than the font they are blown up.
        Per-letter lists: bob (raise / sink), roll (lean, degrees), turn (extra yaw). dot = a colour turns the
        dots of i and j into balls of that colour. Returns {'heroes': [...], 'dots': [...], 'centre': xyz}."""
        n = len(s)
        bob = bob or [0] * n; roll = roll or [0] * n; turn = turn or [0] * n
        k = size / px                                        # world units per glyph pixel
        reach = int(0.22 * px)
        glyphs = [self._glyph(ch, px, style, reach, dot is not None and ch in 'ij') for ch in s]
        adv = [g[3] * k + spacing for g in glyphs]
        width = sum(adv) - spacing
        Rw = _rot(yaw, pitch, 0)
        at = np.asarray(at, np.float32)
        out = dict(heroes=[], dots=[])
        pen = -width / 2
        for i, (ch, g) in enumerate(zip(s, glyphs)):
            sd, ox, oy, _, ink, dt, depth_px = g
            if ch.isspace(): pen += adv[i]; continue
            half_w = depth_px * k                            # half the stroke width, world units
            rr = min(0.92 * half_w + inflate, depth / 2 - 1e-3) if round is None else round
            hz = depth / 2
            Rl = _rot(turn[i], 0, roll[i])
            R = Rw @ Rl
            cg = np.float32([(ink[0] + ink[2]) / 2 * k, 0, 0])            # pivot: bottom centre of the ink
            pivot = np.float32([pen + cg[0], bob[i], 0])
            t = at + Rw @ pivot - R @ cg
            pad = inflate + 0.01
            lo = np.float32([ink[0] * k - pad, ink[1] * k - pad, -hz - 0.01])
            hi = np.float32([ink[2] * k + pad, ink[3] * k + pad, hz + 0.01])
            mid = self._mat(colour, mat)
            out['heroes'].append(self._hero('glyph', R, t, lo, hi, mid, sd=sd, ox=np.float32(ox), oy=np.float32(oy),
                                            k=np.float32(k), inv=np.float32(1 / k), rr=np.float32(rr),
                                            hz=np.float32(hz), inflate=np.float32(inflate)))
            self.heroes[-1]['near'] = (reach - 2) * k - pad
            if dt is not None:
                dxl, dyl, drp = dt
                rad = max(drp * k + inflate, half_w + inflate) * 1.08
                c = R @ np.float32([dxl * k, dyl * k + rad * 0.25, 0]) + t
                out['dots'].append(self.ball(float(c[0]), float(c[1]), float(c[2]), rad, dot, dot_mat))
            pen += adv[i]
        lo, hi = self.hero_bounds(out['heroes'])
        out['centre'] = (lo + hi) / 2
        return out

    def hero_bounds(self, ids):
        """world-space bounding box (lo, hi) of some heroes"""
        pts = []
        for i in ids:
            h = self.heroes[i]
            for cx in (0, 1):
                for cy in (0, 1):
                    for cz in (0, 1):
                        c = np.where([cx, cy, cz], h['hi'], h['lo'])
                        pts.append(h['R'] @ c + h['t'])
        pts = np.array(pts)
        return pts.min(0), pts.max(0)

    def _local_d(self, h, p):
        k = h['kind']
        if k == 'glyph':
            u = p[:, 0] * h['inv'] + h['ox']; v = h['oy'] - p[:, 1] * h['inv']
            d2 = _bilinear(h['sd'], u, v) * h['k'] - h['inflate']
            rr = h['rr']
            qx = d2 + rr; qz = np.abs(p[:, 2]) - h['hz'] + rr
            return np.minimum(np.maximum(qx, qz), 0) + np.hypot(np.maximum(qx, 0), np.maximum(qz, 0)) - rr
        if k == 'rbox':
            q = np.abs(p) - h['b'] + h['rr']
            return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0) - h['rr']
        if k == 'capsule':
            y = np.clip(p[:, 1], -h['hl'], h['hl'])
            return np.sqrt(p[:, 0] ** 2 + (p[:, 1] - y) ** 2 + p[:, 2] ** 2) - h['rad']
        if k == 'rcyl':
            qx = np.hypot(p[:, 0], p[:, 2]) - h['ra'] + h['rr']; qy = np.abs(p[:, 1]) - h['hh'] + h['rr']
            return np.minimum(np.maximum(qx, qy), 0) + np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) - h['rr']
        if k == 'torus':
            q = np.hypot(p[:, 0], p[:, 2]) - h['Rt']
            return np.hypot(q, p[:, 1]) - h['rt']
        raise ValueError(k)

    def _hero_d(self, h, P):
        """exact distance within `near` of the hero's box (glyphs: inside their distance grid), the box distance
        (a lower bound) farther out -- light queries (AO, shadows, drop) need the exact value close by"""
        pl = (P - h['t']) @ h['R']
        c = (h['lo'] + h['hi']) / 2; e = (h['hi'] - h['lo']) / 2
        q = np.abs(pl - c) - e
        d = np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)
        sel = np.nonzero(d < h['near'])[0]
        if len(sel): d[sel] = self._local_d(h, pl[sel])
        return d

    def _heroes_d(self, P):
        d = np.full(len(P), 1e9, np.float32)
        for h in self.heroes:
            np.minimum(d, self._hero_d(h, P), out=d)
        return d

    # ------------------------------------------------------------------ the distance field of the whole scene
    def _field_d(self, P):
        """distance to the sea: the 3 x 3 cells around P. Every ball stays inside its own cell, so any ball not
        looked at is at least one cell width away -- the result is capped there (still a lower bound)"""
        F = self.field; s = F['s']; NJ = F['NJ']
        i0 = np.clip(np.floor((P[:, 0] - F['x0']) / s).astype(np.int32), 1, F['NI'] - 2)
        j0 = np.clip(np.floor((P[:, 2] - F['z0']) / s).astype(np.int32), 1, NJ - 2)
        base = i0 * NJ + j0
        d = np.full(len(P), s, np.float32)
        for off in (-NJ - 1, -NJ, -NJ + 1, -1, 0, 1, NJ - 1, NJ, NJ + 1):
            cell = base + off
            r = F['r'][cell]
            dd = np.linalg.norm(P - F['C'][cell], axis=1) - r
            np.minimum(d, np.where(r > 0, dd, s), out=d)
        return np.maximum(d, P[:, 1] - F['yhi'])

    def _build_hash(self):
        """loose balls -> a grid of lists: a query only looks at the balls registered in its own cell. A ball is
        registered in every cell within `margin` of its footprint, so anything not listed is at least `margin` away
        (the returned distance is capped there, still a lower bound)."""
        n = len(self.br)
        if n == 0: self._hash = False; return
        G = max(0.2, float(self.br.max()) * 2.2); mg = G * 0.5
        rmax = float(self.br.max())
        lo = self.bc[:, [0, 2]].min(0) - rmax - G; hi = self.bc[:, [0, 2]].max(0) + rmax + G
        ni, nj = int(np.ceil((hi[0] - lo[0]) / G)) + 1, int(np.ceil((hi[1] - lo[1]) / G)) + 1
        lists = {}
        for b in range(n):
            x, z, r = self.bc[b, 0], self.bc[b, 2], self.br[b]
            for a in range(int((x - r - mg - lo[0]) // G), int((x + r + mg - lo[0]) // G) + 1):
                for c in range(int((z - r - mg - lo[1]) // G), int((z + r + mg - lo[1]) // G) + 1):
                    lists.setdefault(a * nj + c, []).append(b)
        K = max(len(l) for l in lists.values())
        tab = np.full((ni * nj, K), -1, np.int32)
        for i, l in lists.items(): tab[i, :len(l)] = l
        self._hash = dict(G=np.float32(G), mg=np.float32(mg), lo=lo.astype(np.float32), ni=ni, nj=nj, tab=tab)

    def _balls_d(self, P):
        if self._hash is None: self._build_hash()
        hs = self._hash
        if not hs: return np.full(len(P), 1e9, np.float32)
        G = hs['G']
        a = np.floor((P[:, 0] - hs['lo'][0]) / G).astype(np.int32); c = np.floor((P[:, 2] - hs['lo'][1]) / G).astype(np.int32)
        inside = (a >= 0) & (a < hs['ni']) & (c >= 0) & (c < hs['nj'])
        d = np.full(len(P), hs['mg'], np.float32)
        sel = np.nonzero(inside)[0]
        if not len(sel): return d
        ids = hs['tab'][a[sel] * hs['nj'] + c[sel]]
        sub = d[sel]
        for k in range(ids.shape[1]):
            ok = np.nonzero(ids[:, k] >= 0)[0]
            if not len(ok): break
            b = ids[ok, k]
            dd = np.linalg.norm(P[sel[ok]] - self.bc[b], axis=1) - self.br[b]
            sub[ok] = np.minimum(sub[ok], dd)
        d[sel] = sub
        return d

    def _sdf(self, P):
        d = P[:, 1] - self.floor_y
        if self.field is not None: np.minimum(d, self._field_d(P), out=d)
        if len(self.br): np.minimum(d, self._balls_d(P), out=d)
        if self.heroes: np.minimum(d, self._heroes_d(P), out=d)
        return d

    def _grad(self, P, e=1e-3):
        n = np.zeros_like(P)
        for k in ((1, -1, -1), (-1, -1, 1), (-1, 1, -1), (1, 1, 1)):
            kv = np.float32(k)
            n += kv * self._sdf(P + kv * e)[:, None]
        return _unit(n)

    def _scene_top(self):
        top = self.floor_y
        if self.field is not None: top = max(top, float(self.field['yhi']))
        if len(self.br): top = max(top, float((self.bc[:, 1] + self.br).max()))
        if self.heroes: top = max(top, float(self.hero_bounds(range(len(self.heroes)))[1][1]))
        return top

    # ------------------------------------------------------------------ primary rays
    def _rays(self, w, h):
        f = self._focal(h)
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        D = (self.fwd[None, None] + ((xs + 0.5 - w / 2) / f)[..., None] * self.right
             - ((ys + 0.5 - h / 2) / f)[..., None] * self.up)
        return _unit(D.reshape(-1, 3)), f

    def _rect(self, pts, w, h, f, pad=3):
        rel = pts - self.eye
        zc = rel @ self.fwd
        if (zc < 0.05).any(): return 0, 0, w, h
        x = w / 2 + f * (rel @ self.right) / zc; y = h / 2 - f * (rel @ self.up) / zc
        x0, x1 = int(max(0, x.min() - pad)), int(min(w, x.max() + pad + 1))
        y0, y1 = int(max(0, y.min() - pad)), int(min(h, y.max() + pad + 1))
        return (x0, y0, x1, y1) if x1 > x0 and y1 > y0 else None

    def _hit_heroes(self, D, T, kind, oid, w, h, f):
        O = self.eye
        for hi_, hr in enumerate(self.heroes):
            corners = np.array([hr['R'] @ np.where([a, b, c], hr['hi'], hr['lo']) + hr['t']
                                for a in (0, 1) for b in (0, 1) for c in (0, 1)], np.float32)
            rc = self._rect(corners, w, h, f)
            if rc is None: continue
            x0, y0, x1, y1 = rc
            ids = (np.arange(y0, y1)[:, None] * w + np.arange(x0, x1)[None, :]).ravel()
            Dl = D[ids] @ hr['R']; Ol = (O - hr['t']) @ hr['R']
            with np.errstate(divide='ignore', invalid='ignore'):
                inv = 1 / Dl
                ta = (hr['lo'] - Ol) * inv; tb = (hr['hi'] - Ol) * inv
            tin = np.fmax(np.nanmax(np.fmin(ta, tb), 1), 0); tout = np.nanmin(np.fmax(ta, tb), 1)
            ok = (tin < tout) & (tin < T[ids])
            ids, Dl, t, tout = ids[ok], Dl[ok], tin[ok], tout[ok]
            pixf = 0.4 / f
            for _ in range(160):
                if not len(ids): break
                d = self._local_d(hr, Ol + Dl * t[:, None])
                hit = d < pixf * t
                if hit.any():
                    g = ids[hit]; better = t[hit] < T[g]
                    g = g[better]; T[g] = t[hit][better]; kind[g] = 4; oid[g] = hi_
                t = t + d
                keep = ~hit & (t < tout) & (t < T[ids])
                ids, Dl, t, tout = ids[keep], Dl[keep], t[keep], tout[keep]

    def _hit_balls(self, D, T, kind, oid, w, h, f):
        O = self.eye
        for b in range(len(self.br)):
            c, r = self.bc[b], float(self.br[b])
            rel = c - O; zc = float(rel @ self.fwd)
            if zc < r + 0.05: continue
            sx = w / 2 + f * float(rel @ self.right) / zc; sy = h / 2 - f * float(rel @ self.up) / zc
            rp = f * r / np.sqrt(max(zc * zc - r * r, 1e-6)) * 1.15 + 3
            x0, x1 = int(max(0, sx - rp)), int(min(w, sx + rp + 1)); y0, y1 = int(max(0, sy - rp)), int(min(h, sy + rp + 1))
            if x1 <= x0 or y1 <= y0: continue
            ids = (np.arange(y0, y1)[:, None] * w + np.arange(x0, x1)[None, :]).ravel()
            oc = O - c
            bq = D[ids] @ oc; disc = bq * bq - (oc @ oc - r * r)
            th = -bq - np.sqrt(np.maximum(disc, 0))
            upd = (disc > 0) & (th > 0) & (th < T[ids])
            g = ids[upd]; T[g] = th[upd]; kind[g] = 3; oid[g] = b

    def _hit_field(self, D, T, kind, oid):
        F = self.field; O = self.eye
        s = F['s']; x0, z0, NI, NJ = F['x0'], F['z0'], F['NI'], F['NJ']
        with np.errstate(divide='ignore', invalid='ignore'):
            inv = 1 / D
            lo = np.float32([x0, F['ylo'], z0]); hi = np.float32([x0 + NI * s, F['yhi'], z0 + NJ * s])
            ta = (lo - O) * inv; tb = (hi - O) * inv
        tmin = np.fmax(np.nanmax(np.fmin(ta, tb), 1), 0); tmax = np.fmin(np.nanmin(np.fmax(ta, tb), 1), T)
        ids = np.nonzero(tmin < tmax)[0]
        d = D[ids]; t1 = tmax[ids]
        p = O + d * (tmin[ids] + 1e-5)[:, None]
        i = np.clip(np.floor((p[:, 0] - x0) / s), 0, NI - 1).astype(np.int32)
        j = np.clip(np.floor((p[:, 2] - z0) / s), 0, NJ - 1).astype(np.int32)
        sx = np.where(d[:, 0] > 0, 1, -1).astype(np.int32); sz = np.where(d[:, 2] > 0, 1, -1).astype(np.int32)
        with np.errstate(divide='ignore', invalid='ignore'):
            tdx = np.abs(s / d[:, 0]); tdz = np.abs(s / d[:, 2])
            tmx = np.where(d[:, 0] != 0, (x0 + (i + (sx > 0)) * s - O[0]) / d[:, 0], np.inf)
            tmz = np.where(d[:, 2] != 0, (z0 + (j + (sz > 0)) * s - O[2]) / d[:, 2], np.inf)
        C, Rr = F['C'], F['r']
        while len(ids):
            cell = i * NJ + j
            r = Rr[cell]; oc = O - C[cell]
            bq = (oc * d).sum(1); disc = bq * bq - ((oc * oc).sum(1) - r * r)
            hit = (r > 0) & (disc > 0)
            th = -bq - np.sqrt(np.where(hit, disc, 0))
            hit &= (th > 0) & (th < t1)
            if hit.any():
                g = ids[hit]; T[g] = th[hit]; kind[g] = 2; oid[g] = cell[hit]
            ax = tmx < tmz
            tn = np.where(ax, tmx, tmz)
            i = i + np.where(ax, sx, 0); j = j + np.where(ax, 0, sz)
            tmx = np.where(ax, tmx + tdx, tmx); tmz = np.where(ax, tmz, tmz + tdz)
            keep = ~hit & (tn < t1) & (i >= 0) & (i < NI) & (j >= 0) & (j < NJ)
            ids, d, t1, i, j, sx, sz, tdx, tdz, tmx, tmz = (a[keep] for a in (ids, d, t1, i, j, sx, sz, tdx, tdz, tmx, tmz))

    def _trace(self, scale):
        key = (scale, self.version)
        if key in self._cache: return self._cache[key]
        self._cache = {k: v for k, v in self._cache.items() if k[1] == self.version}
        w, h = int(round(self.W * scale)), int(round(self.H * scale))
        D, f = self._rays(w, h)
        n = len(D)
        T = np.full(n, np.inf, np.float32); kind = np.zeros(n, np.int8); oid = np.full(n, -1, np.int32)
        if self.heroes: self._hit_heroes(D, T, kind, oid, w, h, f)
        if len(self.br): self._hit_balls(D, T, kind, oid, w, h, f)
        if self.field is not None: self._hit_field(D, T, kind, oid)
        with np.errstate(divide='ignore'):
            tf = np.where(D[:, 1] < 0, (self.floor_y - self.eye[1]) / D[:, 1], np.inf)
        fl = tf < T
        T[fl] = tf[fl]; kind[fl] = 1
        hit = np.nonzero(kind > 0)[0]
        P = self.eye + D[hit] * T[hit, None]
        Nn = np.zeros_like(P); mat = np.zeros(len(hit), np.int32)
        kh = kind[hit]; oh = oid[hit]
        m = kh == 1
        Nn[m] = (0, 1, 0); mat[m] = self.floor_mat
        m = kh == 2
        if m.any():
            cell = oh[m]; Nn[m] = (P[m] - self.field['C'][cell]) / self.field['r'][cell][:, None]
            mat[m] = self.field['m'][cell]
        m = kh == 3
        if m.any():
            b = oh[m]; Nn[m] = (P[m] - self.bc[b]) / self.br[b][:, None]; mat[m] = self.bm[b]
        for hi_, hr in enumerate(self.heroes):
            m = np.nonzero((kh == 4) & (oh == hi_))[0]
            if not len(m): continue
            pl = (P[m] - hr['t']) @ hr['R']
            e = float(hr.get('k', 0.001)) * 2.5 if hr['kind'] == 'glyph' else 1e-3
            g = np.zeros_like(pl)
            for kv in ((1, -1, -1), (-1, -1, 1), (-1, 1, -1), (1, 1, 1)):
                kv = np.float32(kv); g += kv * self._local_d(hr, pl + kv * e)[:, None]
            Nn[m] = _unit(g) @ hr['R'].T
            mat[m] = hr['mat']
        Nn = _unit(Nn)
        Z = np.full(n, 1e6, np.float32); Z[hit] = T[hit] * (D[hit] @ self.fwd)
        tr = dict(w=w, h=h, f=f, D=D, T=T, Z=Z, kind=kind, hit=hit, P=P, N=Nn, mat=mat, shadows={})
        tr['ao'] = self._ao(P, Nn)
        self._cache[key] = tr
        return tr

    # ------------------------------------------------------------------ light transport helpers
    def _ao(self, P, N, radius=0.3):
        """ambient occlusion: how much of the distance field crowds in along the normal (1 open .. 0 buried)"""
        hs = radius * np.array([0.05, 0.13, 0.25, 0.42, 0.66, 1.0], np.float32)
        occ = np.zeros(len(P), np.float32); tot = 0.0; w = 1.0
        base = P + N * 2e-3
        for hgt in hs:
            d = self._sdf(base + N * hgt)
            occ += np.clip(hgt - d, 0, None) * w; tot += hgt * w; w *= 0.72
        return np.clip(1 - 1.25 * occ / tot, 0, 1)

    def _shadow(self, P, N, L, k):
        """soft shadow toward a light of direction L: march the distance field, keep the closest near-miss"""
        n = len(P); res = np.ones(n, np.float32)
        top = self._scene_top() + 1e-3
        ndl = N @ L
        ids = np.nonzero(ndl > -0.35)[0]
        res[ndl <= -0.35] = 0
        o = P[ids] + N[ids] * 3e-3
        t = np.full(len(ids), 4e-3, np.float32)
        for _ in range(64):
            if not len(ids): break
            p = o + L * t[:, None]
            hd = self._sdf(p)
            res[ids] = np.minimum(res[ids], k * hd / t)
            t = t + np.clip(hd, 0.006, 0.3)
            keep = (res[ids] > 0.002) & (p[:, 1] < top)
            ids, o, t = ids[keep], o[keep], t[keep]
        return smoothstep(0, 1, np.clip(res, 0, 1))

    # ------------------------------------------------------------------ lights, sky, lens, film
    def _dir(self, azimuth, elevation):
        fh = _unit([self.fwd[0], 0, self.fwd[2]]); rh = _unit(np.cross([0, 1, 0], fh))
        a, e = np.radians(azimuth), np.radians(elevation)
        return _unit(-fh * np.cos(a) * np.cos(e) + rh * np.sin(a) * np.cos(e) + np.float32([0, 1, 0]) * np.sin(e))

    def sky(self, top='#cfc6f4', horizon='#fbe4dc', ground=None, strength=1.0, haze=45.0, haze_start=6.0,
            haze_colour=None):
        """the studio dome: backdrop gradient (what the camera sees behind everything), ambient light from above
        and a floor bounce from below (ground defaults to the floor colour). haze: distance over which far things
        fade into haze_colour (default: the horizon colour), starting haze_start from the camera."""
        g = self.mats[self.floor_mat]['alb'] ** (1 / 2.2) if ground is None else _c(ground)
        self.env = dict(top=_lin(top), hor=_lin(horizon), ground=np.power(g, 2.2).astype(np.float32) * 0.8,
                        k=strength, haze=haze, haze0=haze_start,
                        hazec=_lin(horizon if haze_colour is None else haze_colour))

    def key(self, azimuth=-40, elevation=48, colour='#fff3e8', strength=2.4, size=11, shadow=True):
        """the main soft area light (size = angular radius in degrees: bigger = softer shadows, broader gloss)"""
        L = self._dir(azimuth, elevation)
        self.lights.append(dict(L=L, col=_lin(colour), k=strength, size=size, shadow=shadow))
        self._panel(L, size * 1.25, size, strength, len(self.lights) - 1)

    def rim(self, azimuth=160, elevation=26, colour='#ffd9e6', strength=1.3, size=14, shadow=False):
        """a back light: bright outlines along the far side of every silhouette"""
        L = self._dir(azimuth, elevation)
        self.lights.append(dict(L=L, col=_lin(colour), k=strength, size=size, shadow=shadow, rim=True))
        self._panel(L, size, size * 0.6, strength * 0.6, len(self.lights) - 1)

    def softbox(self, azimuth, elevation, width=20, height=12, strength=1.0):
        """a panel that only shows in reflections (adds a studio highlight without changing the lighting)"""
        self._panel(self._dir(azimuth, elevation), width / 2, height / 2, strength, None)

    def _panel(self, L, hw, hh, strength, light):
        a1 = _unit(np.cross([0, 1, 0], L)); a2 = _unit(np.cross(L, a1))
        hw, hh = np.radians(hw), np.radians(hh)
        self.panels.append(dict(c=L, a1=a1, a2=a2, hw=hw, hh=hh, rad=strength / (4 * hw * hh) * 1.6, light=light))

    def lens(self, focus=None, aperture=0.006, max_blur=0.018):
        """depth of field. focus: a world point, a hero list (text() result) or None (the heroes' centre);
        aperture: blur radius of infinity as a fraction of the image width"""
        if isinstance(focus, dict): focus = focus['centre']
        if focus is None:
            focus = np.mean(self.hero_bounds(range(len(self.heroes))), 0) if self.heroes else self.target
        zf = float((np.asarray(focus, np.float32) - self.eye) @ self.fwd)
        self.lens_cfg = dict(zf=zf, a=aperture, mx=max_blur)

    def film(self, bloom=0.22, vignette=0.22, grain=0.012, exposure=1.0):
        self.film_cfg = dict(bloom=bloom, vignette=vignette, grain=grain, exposure=exposure)

    # ------------------------------------------------------------------ shading
    def _backdrop(self, D):
        if self.env is None:
            t = smoothstep(-0.05, 0.5, D[:, 1])[:, None]
            return np.float32([0.62, 0.62, 0.64]) * (1 - t) + np.float32([0.5, 0.5, 0.53]) * t
        e = self.env
        t = smoothstep(-0.01, 0.3, D[:, 1])[:, None] ** 0.8
        return (e['hor'] * (1 - t) + e['top'] * t) * e['k'] * 1.12

    def _env(self, R, rough, shadows):
        e = self.env
        up = R[:, 1:2]
        sky = e['hor'] + (e['top'] - e['hor']) * np.clip(up, 0, 1) ** 0.6
        gnd = e['hor'] + (e['ground'] - e['hor']) * np.clip(-up * 3, 0, 1) ** 0.5
        col = np.where(up > 0, sky, gnd) * e['k']
        for p in self.panels:
            cz = R @ p['c']
            u = np.arctan2(R @ p['a1'], np.maximum(cz, 1e-4)); v = np.arctan2(R @ p['a2'], np.maximum(cz, 1e-4))
            sp = rough * 0.9 + 0.01
            hw, hh = p['hw'] + sp, p['hh'] + sp
            rr = np.minimum(hw, hh) * 0.45
            qx = np.abs(u) - hw + rr; qy = np.abs(v) - hh + rr
            dist = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - rr
            soft = 0.015 + sp * 0.7
            I = p['rad'] * (p['hw'] * p['hh']) / (hw * hh) * smoothstep(soft, -soft, dist) * (cz > 0)
            if p['light'] is not None and p['light'] in shadows:
                I = I * (0.15 + 0.85 * shadows[p['light']])
            col = col + I[:, None] * self.lights[p['light']]['col'] if p['light'] is not None else col + I[:, None]
        return col

    def _shade(self, tr):
        D, hit = tr['D'], tr['hit']
        out = np.zeros((len(D), 3), np.float32)
        miss = tr['kind'] == 0
        out[miss] = self._backdrop(D[miss])
        P, N, ao = tr['P'], tr['N'], tr['ao']
        V = -D[hit]
        ndv = np.clip((N * V).sum(1), 0, 1)
        if self.env is None:                                 # clay render: grey clay under a white dome
            dome = 0.55 + 0.35 * np.clip(N[:, 1], 0, 1)
            out[hit] = (0.62 * dome * ao ** 1.2)[:, None]
            return out
        mt = self._mat_table(); m = tr['mat']
        alb, tint, rough, spec, sss, sheen = (mt[k][m] for k in ('alb', 'tint', 'rough', 'spec', 'sss', 'sheen'))
        e = self.env
        sat = (1 - tint) * sss[:, None]                      # 0 on the dominant channel: shade stays saturated
        ao_rgb = (0.1 + 0.9 * ao[:, None]) ** (1 + 1.6 * sat)
        up = N[:, 1:2]
        E = np.where(up > 0, e['hor'] + (e['top'] - e['hor']) * up, e['hor'] + (e['ground'] - e['hor']) * (-up))
        col = alb * E * ao_rgb * e['k']
        shadows = {}
        for li, L in enumerate(self.lights):
            if L['shadow']:
                sk = ('sh', li, tuple(np.round(L['L'], 4)), L['size'])
                if sk not in tr['shadows']:
                    tr['shadows'][sk] = self._shadow(P, N, L['L'], 1 / np.tan(np.radians(L['size'])))
                sh = tr['shadows'][sk]
            else:
                sh = np.clip(0.35 + 0.65 * ao, 0, 1)
            shadows[li] = sh
            ndl = N @ L['L']
            lam = np.clip(ndl, 0, 1); wr = 0.5 * sss
            wrp = np.clip((ndl + wr) / (1 + wr), 0, 1)
            diff = lam[:, None] + (wrp - lam)[:, None] * tint
            # shade is filled a little by light scattered inside the soft material: saturated, never grey
            sh_rgb = sh[:, None] ** (1 + 1.2 * sat) + 0.4 * sss[:, None] * tint * (1 - sh)[:, None]
            k = L['k'] * (0.55 if L.get('rim') else 1.0)
            col += alb * diff * sh_rgb * L['col'] * k * (0.6 + 0.4 * ao)[:, None]
            if L.get('rim'):                                 # the back light also grazes along silhouettes
                edge = (1 - ndv) ** 1.8 * np.clip(ndl + 0.4, 0, 1)
                col += (alb * 0.5 + 0.5 * tint * alb.max(1, keepdims=True)) * (edge * sh * L['k'] * 1.1)[:, None] * L['col']
        R = D[hit] - 2 * (D[hit] * N).sum(1, keepdims=True) * N
        f0 = 0.045
        F = f0 + (1 - f0) * (1 - ndv) ** 5
        spec_occ = np.clip(ao * 1.25, 0, 1) ** 1.5
        refl = self._env(R, rough, shadows)
        col += refl * (F * spec * spec_occ)[:, None]
        col += alb * tint * (sheen * (1 - ndv) ** 3 * ao)[:, None] * E * e['k']
        out[hit] = col
        if e['haze']:
            fog = 1 - np.exp(-np.maximum(tr['T'][hit] - e['haze0'], 0) / e['haze'])
            out[hit] = out[hit] * (1 - fog[:, None]) + (e['hazec'] * e['k'] * 1.12) * fog[:, None]
        return out

    def _dof(self, img, tr):
        h, w = tr['h'], tr['w']
        L = self.lens_cfg
        Z = tr['Z'].reshape(h, w)
        coc = np.minimum(L['a'] * w * np.abs(1 - L['zf'] / Z), L['mx'] * w)
        levels = np.array([0, 1.0, 2.2, 3.8, 6.0, 9.0, 13.0, 18.5, 26.0, 36.0]) * w / 1920
        levels = levels[levels <= coc.max() * 1.05 + 1e-3]
        if len(levels) < 2: return img
        out = np.zeros_like(img); wsum = np.zeros((h, w), np.float32)
        pos = np.interp(coc, levels, np.arange(len(levels)))
        for k, rad in enumerate(levels):
            wk = np.clip(1 - np.abs(pos - k), 0, 1)
            if wk.max() < 1e-4: continue
            if k == 0:
                layer = img
            else:
                src = smoothstep(0.35 * rad, 0.8 * rad, coc)
                num = _blur3(img * src[..., None], rad * 0.6)
                den = _blur_big(src, rad * 0.6)
                layer = np.where(den[..., None] > 1e-3, num / np.maximum(den, 1e-3)[..., None], img)
            out += layer * wk[..., None]; wsum += wk
        return out / np.maximum(wsum, 1e-6)[..., None]

    def _film(self, img, final):
        c = self.film_cfg
        exp = c['exposure'] if c else 1.0
        img = img * exp
        if c and c['bloom']:
            lum = img.mean(-1, keepdims=True)
            hi = img * np.clip(lum - 0.75, 0, None) / np.maximum(lum, 1e-3)
            w = img.shape[1]
            img = img + (_blur3(hi, w * 0.006) * 0.6 + _blur3(hi, w * 0.022) * 0.6) * c['bloom']
        a = 0.72                                             # tone curve: linear below `a`, soft shoulder above
        img = np.where(img < a, img, a + (1 - a) * (1 - np.exp(-(img - a) / (1 - a))))
        img = np.clip(img, 0, 1) ** (1 / 2.2)
        if c:
            h, w = img.shape[:2]
            ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
            r2 = ((xs - w / 2) / (w / 2)) ** 2 * 0.7 + ((ys - h / 2) / (h / 2)) ** 2 * 0.9
            img = img * (1 - c['vignette'] * 0.5 * r2)[..., None]
            if c['grain'] and final:
                g = np.random.default_rng(7).normal(0, 1, (h, w)).astype(np.float32)
                g = g * 0.8 + blur(g, 0.8) * 0.9
                img = img + (g * c['grain'])[..., None]
        return np.clip(img, 0, 1)

    def render(self, scale=1.0, final=True):
        tr = self._trace(scale)
        img = self._shade(tr).reshape(tr['h'], tr['w'], 3)
        if self.lens_cfg: img = self._dof(img, tr)
        img = self._film(img, final)
        return Image.fromarray((img * 255 + 0.5).astype(np.uint8))

    # ------------------------------------------------------------------ output
    def stage(self, name, ss=1.5):
        """snapshot of the scene so far: a real render at `preview` size (supersampled `ss` times)"""
        if not self.record: return
        w, h = int(round(self.W * self.preview)), int(round(self.H * self.preview))
        im = self.render(self.preview * ss, final=False)
        self.stages.append((name, im.resize((w, h), Image.LANCZOS) if im.size != (w, h) else im))

    def save(self, path, stages_dir=None, quality=88, ss=1.5):
        """final render, supersampled `ss` times per axis and downsampled (clean silhouettes)"""
        img = self.render(ss)
        if img.size != (self.W, self.H): img = img.resize((self.W, self.H), Image.LANCZOS)
        if path.lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality)
        else: img.save(path)
        if stages_dir:
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
