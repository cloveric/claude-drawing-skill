"""constructivism -- a Soviet constructivist poster of the 1920s, printed in two inks (numpy + Pillow only).

A red disc, a black diagonal, a wedge, slabs of heavy condensed Cyrillic, and photographs cut out with scissors and
screened into a coarse 45-degree halftone: the photomontage poster as it came off a two-colour press onto cheap,
cream paper, and as it looks a century later.

Model: the poster is one sheet and two printing plates.
  plates     everything red is on the red plate, everything black (solids, type, every halftone dot of every
             photograph) is on the black plate. A plate is a coverage map 0..1. Drawing is "ink this mask on that
             plate" or "knock this mask out of these plates" (the paper shows). The plates are only put on paper
             in composite(), each with its own registration error -- one small shift plus a hair of rotation for the
             whole plate -- so all red moves together against all black: wherever the designer made red and black
             meet, a sliver of bare paper opens on one side and a dark overprint on the other.
  inks       printing ink is a transparent filter, so the ink colours multiply with the paper and with each other:
             black over red prints a deep warm black, red over the paper picks up the paper's yellow. The ink film
             is never quite even: big soft blotches of more and less ink, a fine mottle, a few voids where a fibre
             or a speck of dust kept the plate from touching, an edge that is ragged at the scale of the paper's
             fibres, and a slightly heavier squeeze of ink along the edge of every solid (letterpress halo).
  photo      a "photograph" is really rendered: `Photo` is a tiny z-buffer rasteriser for triangle meshes (cylinders,
             lathes, swept tubes, boxes, hyperboloid lattices) in a perspective camera, shaded like a studio or
             outdoor photo (key + fill + sky light, Blinn highlights, an environment for metal, haze with distance,
             a slightly soft lens and film grain), giving a grey-tone image and a silhouette.
  montage    the photomontage step: a photo is scaled, rotated and placed on the poster, then -- like the whole
             paste-up being re-photographed for the plate -- screened in poster space into an AM halftone on the
             black plate: round dots on a 45-degree screen that grow, touch in a chequerboard at 50 % and leave only
             white holes in the shadows, with dot gain and fibre-ragged dot edges. `cut=` cuts the print out along
             its silhouette with a margin (scissors: a slightly wandering offset path), and the cut piece covers
             whatever was printed under it, so it shows as a pale paper outline with the faint highlight dots of
             the photographic backdrop; without `cut` the photo is retouched out of its background and the dots
             print straight over the red.
  type       heavy condensed grotesque (Helvetica Neue Condensed Black, else Impact / DejaVu Sans Condensed Bold)
             for the slabs, a squarer condensed face (DIN Condensed, else Arial Narrow / PT Sans Narrow) for labels,
             Futura Bold for small geometric captions; any font missing a Cyrillic glyph is skipped for the next.
             Big lettering can be given a hand-drawn `wobble` (a sub-pixel low-frequency warp of the outline).
  paper      cheap uncoated poster paper: cream, cloudy pulp, short fibres and dark flecks, a little cockle,
             yellowing and greying toward the edges.
  age        a hundred years later: the folds it was posted in (a lit ridge and a dark valley, a band of grime,
             the ink cracked off in a broken line along the crease), foxing, a faint water-stain tide line,
             rubbed corners, drawing-pin holes.
Coordinates are pixels, y down. Angles are degrees counter-clockwise from 3 o'clock; `rot` of text and photos is
counter-clockwise too (so a line of type rising to the right has a positive rot).

    from constructivism import Constructivism, Photo
    c = Constructivism(1920, 1080, seed=3)
    c.paper()
    c.ink(c.circle(420, 260, 200), 'red')
    c.ink(c.wedge((420, 260), -25, 8, 1700), 'red')
    c.waves(420, 260, 180, 1500, 64, 14, -36, -14, plates=('black',))
    c.ink(c.bar(560, 1000, 1920, 560, 96), 'black', knock=c.text_mask('СЛУШАЙТЕ', 760, 935, 70, anchor='lm', rot=18))
    p = Photo(600, 900, eye=(-40, -60, 2), target=(0, 0, 40), fov=60)
    steel = p.material(albedo=0.12)
    p.hyperboloid(0, 25, 20, 15, 16, 67.5, steel, member=0.5); p.hyperboloid(25, 50, 15, 11, 12, 90, steel, member=0.4)
    c.montage(p, 420, 620, cell=5.5)                                # retouched, printed over the red
    c.montage(other_photo, 1500, 600, rot=10, cut=13, close=16)     # cut out with scissors, covers what is under
    c.text('РАДИО', 1860, 330, 330, 'black', anchor='rs')
    c.age(folds=(1, 1))
    c.save('out.jpg')
"""
import glob
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, noise2d, smoothstep, fbm1d

RED, BLACK = '#c9302a', '#1d1b1a'
PAPER, AGED = '#ebe0c6', '#d6c08f'
PLATES = ('red', 'black')


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


# ---------------------------------------------------------------- fonts (kept inside this module)
_CHAINS = {
    'grotesk': [('/System/Library/Fonts/HelveticaNeue.ttc', ('Condensed Black',)),
                ('/System/Library/Fonts/Supplemental/Impact.ttf', None),
                ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', None),
                ('C:/Windows/Fonts/impact.ttf', None)],
    'din': [('/System/Library/Fonts/Supplemental/DIN Condensed Bold.ttf', None),
            ('/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf', None),
            ('/System/Library/Fonts/PTSans.ttc', ('Narrow', 'Bold')),
            ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', None),
            ('C:/Windows/Fonts/ARIALNB.TTF', None)],
    'narrow': [('/System/Library/Fonts/HelveticaNeue.ttc', ('Condensed Bold',)),
               ('/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf', None),
               ('/usr/share/fonts/**/DejaVuSansCondensed-Bold.ttf', None),
               ('C:/Windows/Fonts/ARIALNB.TTF', None)],
    'futura': [('/System/Library/Fonts/Supplemental/Futura.ttc', ('Bold',)),
               ('/System/Library/Fonts/Avenir Next.ttc', ('Bold',)),
               ('/usr/share/fonts/**/DejaVuSans-Bold.ttf', None),
               ('C:/Windows/Fonts/arialbd.ttf', None)],
}
_FACES, _FONTS, _HAS = {}, {}, {}


def _faces(style):
    """all usable (path, index) faces for a style, best first; $INKPAINT_FONT_<STYLE> goes in front"""
    if style in _FACES: return _FACES[style]
    out = []
    env = os.environ.get('INKPAINT_FONT_' + style.upper())
    if env and os.path.exists(env): out.append((env, 0))
    for pat, want in _CHAINS.get(style, _CHAINS['grotesk']):
        for path in glob.glob(pat, recursive=True)[:1]:
            if want is None:
                out.append((path, 0)); continue
            for i in range(40):
                try:
                    f = ImageFont.truetype(path, 20, index=i)
                except (OSError, ValueError):
                    break
                name = ' '.join(f.getname())
                if all(w in name for w in want) and 'Italic' not in name and 'Oblique' not in name:
                    out.append((path, i)); break
    _FACES[style] = out
    return out


def _font_of(face, size):
    k = (face, int(round(size)))
    if k not in _FONTS:
        _FONTS[k] = ImageFont.truetype(face[0], max(4, int(round(size))), index=face[1])
    return _FONTS[k]


def _has(face, ch):
    k = (face, ch)
    if k not in _HAS:
        f = _font_of(face, 48)
        a, b = f.getmask(ch), f.getmask('\U0010fffd')
        _HAS[k] = ch.isspace() or (a.getbbox() is not None and not (a.size == b.size and bytes(a) == bytes(b)))
    return _HAS[k]


def font(style, size, s=''):
    """PIL font for `style` ('grotesk', 'din', 'narrow', 'futura') whose face has every glyph of `s`"""
    faces = _faces(style) or _faces('grotesk')
    for face in faces:
        if all(_has(face, ch) for ch in s):
            return _font_of(face, size)
    if faces: return _font_of(faces[0], size)
    from core import load_font
    return load_font('sans_bold', size)


# ---------------------------------------------------------------- small helpers
def _rotate(a, deg, center=None, expand=False):
    im = Image.fromarray(a.astype(np.float32), 'F')
    return np.asarray(im.rotate(deg, resample=Image.BILINEAR, center=center, expand=expand), np.float32)


def _warp(a, dx, dy):
    """sample a at (x + dx, y + dy), bilinear, clamped"""
    h, w = a.shape
    Y, X = np.mgrid[0:h, 0:w].astype(np.float32)
    x = np.clip(X + dx, 0, w - 1.001); y = np.clip(Y + dy, 0, h - 1.001)
    x0, y0 = x.astype(np.int32), y.astype(np.int32)
    fx, fy = x - x0, y - y0
    return ((a[y0, x0] * (1 - fx) + a[y0, x0 + 1] * fx) * (1 - fy)
            + (a[y0 + 1, x0] * (1 - fx) + a[y0 + 1, x0 + 1] * fx) * fy)


def _dilate(m, r):
    """dilate a 0..1 mask by a disc of radius r px (max over shifted copies, done in 2-px steps)"""
    out = m.copy()
    offs = [(dx, dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx * dx + dy * dy <= 5]
    steps, rest = int(r // 2), r - 2 * int(r // 2)
    for _ in range(steps):
        p = np.pad(out, 2)
        h, w = out.shape
        out = np.max([p[2 + dy:2 + dy + h, 2 + dx:2 + dx + w] for dx, dy in offs], axis=0)
    if rest > 0.3:
        p = np.pad(out, 1)
        h, w = out.shape
        out = np.max([p[1 + dy:1 + dy + h, 1 + dx:1 + dx + w] for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if dx * dx + dy * dy <= 1], axis=0)
    return out


def _fill_holes(m):
    """binary mask -> the same with every enclosed hole filled (flood the outside from a padded corner)"""
    im = Image.fromarray(np.pad((m > 0.5).astype(np.uint8) * 255, 1)).copy()      # copy: floodfill needs a writable image
    ImageDraw.floodfill(im, (0, 0), 128)
    return (np.asarray(im)[1:-1, 1:-1] != 128).astype(np.float32)


def halftone(dark, X, Y, cell=7.0, angle=45.0, rough=None, gain=0.55, soften=0.3):
    """AM halftone: darkness 0..1 -> ink coverage 0..1, evaluated at poster coordinates X, Y (so every photo on the
    sheet shares one screen). Round dots that grow with darkness, touch in a chequerboard at 50 % and leave white
    holes in the shadows. rough: a fibre-noise field that roughens the dot edges; gain: dot gain blur (px)."""
    d = blur(dark, cell * soften) if soften else dark
    a = np.deg2rad(angle)
    u = (X * np.cos(a) + Y * np.sin(a)) / cell
    v = (-X * np.sin(a) + Y * np.cos(a)) / cell
    su, sv = np.sin(2 * np.pi * u), np.sin(2 * np.pi * v)
    spot = 0.5 - 0.25 * (np.cos(2 * np.pi * u) + np.cos(2 * np.pi * v))
    grad = (np.pi / (2 * cell)) * np.sqrt(su * su + sv * sv) + 0.04
    if rough is not None:
        spot = spot + rough
    ink = np.clip((d - spot) / grad + 0.5, 0, 1) * smoothstep(0.0, 0.035, d)
    ink = np.maximum(ink, smoothstep(0.94, 1.0, d))
    if gain:
        ink = np.clip(blur(ink, gain) * 1.1, 0, 1)
    return ink.astype(np.float32)


# ---------------------------------------------------------------- the photograph
class Photo:
    """A tiny perspective z-buffer rasteriser that 'photographs' simple meshes in grey tones.
    World units are metres, Z is up. Build with cylinder / lathe / sweep / box / hyperboloid, then render()
    (once: rendering frees the buffers and caches the result)."""

    def __init__(self, w, h, eye, target, up=(0, 0, 1), fov=40.0, ss=2, seed=0, key=(-0.55, -0.65, 0.55),
                 fill=(0.75, -0.25, 0.15), key_k=1.0, fill_k=0.3, amb=0.32, exposure=1.0, haze=0.0,
                 haze_tone=0.9, grain=0.025, lens=0.6, shift=(0.0, 0.0)):
        """shift: lens shift (fraction of the frame) -- moves the picture without tilting the camera"""
        self.w, self.h, self.ss = w, h, ss
        self.E = np.array(eye, np.float64)
        f = np.array(target, np.float64) - self.E; f /= np.linalg.norm(f)
        r = np.cross(f, np.array(up, np.float64)); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.R = np.stack([r, u, f])
        self.focal = 0.5 * w / np.tan(np.deg2rad(fov) / 2)
        self.cx, self.cy = w / 2 + shift[0] * w, h / 2 + shift[1] * h
        H, W = h * ss, w * ss
        self.z = np.full((H, W), np.inf, np.float32)
        self.n = np.zeros((H, W, 3), np.float32)
        self.pos = np.zeros((H, W, 3), np.float32)
        self.mat = np.full((H, W), -1, np.int16)
        self.mats = []
        self.rng = np.random.default_rng(seed)
        self.key = np.array(key, np.float32) / np.linalg.norm(key)
        self.fill = np.array(fill, np.float32) / np.linalg.norm(fill)
        self.key_k, self.fill_k, self.amb, self.exposure = key_k, fill_k, amb, exposure
        self.haze, self.haze_tone, self.grain, self.lens = haze, haze_tone, grain, lens
        self._out = None

    def material(self, albedo=0.5, gloss=0.15, shine=20.0, metal=0.0, tex=None, interior=0.3, haze=True):
        """returns a material id. tex(pos (k,3), normal (k,3)) -> albedo multiplier (k,) for procedural texture.
        interior: how dark the inside (back faces) of an open shape looks"""
        self.mats.append(dict(albedo=albedo, gloss=gloss, shine=shine, metal=metal, tex=tex, interior=interior,
                              haze=haze))
        return len(self.mats) - 1

    def project(self, P):
        """world points (n, 3) -> screen x, y (output pixels) and depth"""
        p = (np.asarray(P, np.float64) - self.E) @ self.R.T
        z = p[:, 2]
        return self.cx + self.focal * p[:, 0] / z, self.cy - self.focal * p[:, 1] / z, z

    # ------------------------------------------------------------ rasteriser
    def mesh(self, V, N, F, mid):
        """triangles F (m, 3) over vertices V (n, 3) with vertex normals N (n, 3)"""
        if self.z is None:
            raise RuntimeError('this Photo has already been rendered; build a new one to add more objects')
        V = np.asarray(V, np.float64); N = np.asarray(N, np.float32); F = np.asarray(F, np.int64)
        sx, sy, z = self.project(V)
        ss = self.ss
        sx, sy = sx * ss, sy * ss
        H, W = self.z.shape
        for tri in F:
            i, j, k = tri
            z0, z1, z2 = z[i], z[j], z[k]
            if min(z0, z1, z2) < 0.05: continue
            x0, x1, x2 = sx[i], sx[j], sx[k]
            y0, y1, y2 = sy[i], sy[j], sy[k]
            area = (x1 - x0) * (y2 - y0) - (x2 - x0) * (y1 - y0)
            if abs(area) < 1e-7: continue
            bx0 = max(int(np.floor(min(x0, x1, x2))), 0); bx1 = min(int(np.ceil(max(x0, x1, x2))) + 1, W)
            by0 = max(int(np.floor(min(y0, y1, y2))), 0); by1 = min(int(np.ceil(max(y0, y1, y2))) + 1, H)
            if bx1 <= bx0 or by1 <= by0: continue
            py, px = np.mgrid[by0:by1, bx0:bx1].astype(np.float64)
            px += 0.5; py += 0.5
            w0 = ((x1 - px) * (y2 - py) - (x2 - px) * (y1 - py)) / area
            w1 = ((x2 - px) * (y0 - py) - (x0 - px) * (y2 - py)) / area
            w2 = 1 - w0 - w1
            ins = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
            if not ins.any(): continue
            zz = (w0 * z0 + w1 * z1 + w2 * z2).astype(np.float32)
            sub = self.z[by0:by1, bx0:bx1]
            upd = ins & (zz < sub)
            if not upd.any(): continue
            sub[upd] = zz[upd]
            a, b, c = w0[upd][:, None], w1[upd][:, None], w2[upd][:, None]
            self.n[by0:by1, bx0:bx1][upd] = a * N[i] + b * N[j] + c * N[k]
            self.pos[by0:by1, bx0:bx1][upd] = a * V[i] + b * V[j] + c * V[k]
            self.mat[by0:by1, bx0:bx1][upd] = mid

    @staticmethod
    def _frame(axis):
        a = np.asarray(axis, np.float64); a = a / np.linalg.norm(a)
        t = np.array([0, 0, 1.0]) if abs(a[2]) < 0.9 else np.array([1.0, 0, 0])
        u = np.cross(a, t); u /= np.linalg.norm(u)
        return a, u, np.cross(a, u)

    def _surface(self, rings, normals, mid, closed=True):
        """grid of vertex rings (k, s, 3) -> triangles"""
        k, s = rings.shape[:2]
        V = rings.reshape(-1, 3); N = normals.reshape(-1, 3)
        F = []
        cols = s if closed else s - 1
        for a in range(k - 1):
            for b in range(cols):
                b2 = (b + 1) % s
                p, q, r_, t = a * s + b, a * s + b2, (a + 1) * s + b2, (a + 1) * s + b
                F.append((p, q, r_)); F.append((p, r_, t))
        self.mesh(V, N, F, mid)

    def lathe(self, base, axis, profile, mid, sides=32, cap=True):
        """surface of revolution: profile = [(t, r), ...] along `axis` from `base` (metres)"""
        a, u, v = self._frame(axis)
        prof = np.asarray(profile, np.float64)
        th = np.linspace(0, 2 * np.pi, sides, endpoint=False)
        ring = np.cos(th)[:, None] * u + np.sin(th)[:, None] * v                         # (s, 3) radial dirs
        t, r = prof[:, 0], prof[:, 1]
        dt, dr = np.gradient(t), np.gradient(r)
        P = np.asarray(base, np.float64) + t[:, None, None] * a + r[:, None, None] * ring[None]
        nrm = ring[None] * dt[:, None, None] - a * dr[:, None, None]
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True) + 1e-12
        self._surface(P, nrm, mid)
        if cap and r[-1] > 1e-4:                                                          # flat end cap
            c = np.asarray(base) + t[-1] * a
            V = np.vstack([c[None], P[-1]]); N = np.tile(a, (sides + 1, 1))
            self.mesh(V, N, [(0, 1 + i, 1 + (i + 1) % sides) for i in range(sides)], mid)
        if cap and r[0] > 1e-4:
            c = np.asarray(base) + t[0] * a
            V = np.vstack([c[None], P[0]]); N = np.tile(-a, (sides + 1, 1))
            self.mesh(V, N, [(0, 1 + i, 1 + (i + 1) % sides) for i in range(sides)], mid)

    def cylinder(self, p0, p1, r, mid, sides=8, segs=1, r1=None, cap=False):
        """a straight tube (steel member, rod, wire) from p0 to p1; r1 tapers it"""
        p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
        L = np.linalg.norm(p1 - p0)
        if L < 1e-9: return
        r1 = r if r1 is None else r1
        t = np.linspace(0, L, segs + 1)
        self.lathe(p0, p1 - p0, np.stack([t, r + (r1 - r) * t / L], 1), mid, sides, cap)

    def sweep(self, path, radii, mid, sides=20):
        """a tube of varying radius along a 3-D path (gooseneck, horn, cable); parallel-transport frames"""
        P = np.asarray(path, np.float64); rad = np.asarray(radii, np.float64)
        T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)
        _, u, _ = self._frame(T[0])
        us = [u]
        for i in range(1, len(P)):
            u = us[-1] - T[i] * np.dot(us[-1], T[i]); u /= np.linalg.norm(u)
            us.append(u)
        U = np.array(us); Vv = np.cross(T, U)
        th = np.linspace(0, 2 * np.pi, sides, endpoint=False)
        ring = np.cos(th)[None, :, None] * U[:, None] + np.sin(th)[None, :, None] * Vv[:, None]
        s = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
        drds = np.gradient(rad, s)
        pts = P[:, None] + rad[:, None, None] * ring
        nrm = ring - drds[:, None, None] * T[:, None]
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        self._surface(pts, nrm, mid)

    def box(self, lo, hi, mid):
        """axis-aligned box from corner lo to corner hi (flat-shaded faces)"""
        x0, y0, z0 = lo; x1, y1, z1 = hi
        faces = [((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (0, -1, 0)),
                 ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (0, 1, 0)),
                 ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (-1, 0, 0)),
                 ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (1, 0, 0)),
                 ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1), (0, 0, 1)),
                 ((x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0), (0, 0, -1))]
        for a, b, c, d, n in faces:
            self.mesh([a, b, c, d], [n] * 4, [(0, 1, 2), (0, 2, 3)], mid)

    def hyperboloid(self, z0, z1, r0, r1, n, twist, mid, member=0.25, rings=4, ring_member=None, phase=0.0, sides=6,
                    segs=4):
        """one section of a ruled-surface lattice (a hyperboloid tower section): n straight members leaning one
        way and n the other, from a ring of radius r0 at height z0 to a ring of radius r1 at z1, each joining
        angle th to th +- twist (degrees); plus `rings` horizontal hoops that follow the waist."""
        tw = np.deg2rad(twist)
        th = np.deg2rad(phase) + np.linspace(0, 2 * np.pi, n, endpoint=False)
        for sgn in (1, -1):
            for t in th:
                p0 = (r0 * np.cos(t), r0 * np.sin(t), z0)
                p1 = (r1 * np.cos(t + sgn * tw), r1 * np.sin(t + sgn * tw), z1)
                self.cylinder(p0, p1, member, mid, sides, segs)
        rm = ring_member or member * 0.8
        for k in range(rings + 1):
            f = k / rings
            a0 = np.array([r0, 0.0]); a1 = np.array([r1 * np.cos(tw), r1 * np.sin(tw)])
            rr = np.linalg.norm(a0 * (1 - f) + a1 * f)                                   # waist radius here
            zz = z0 + (z1 - z0) * f
            m = max(24, n * 2)
            ang = np.linspace(0, 2 * np.pi, m + 1)
            for a, b in zip(ang[:-1], ang[1:]):
                self.cylinder((rr * np.cos(a), rr * np.sin(a), zz), (rr * np.cos(b), rr * np.sin(b), zz), rm, mid, 5)

    # ------------------------------------------------------------ shading
    def render(self, backdrop=None):
        """-> (tone, alpha), both (h, w) float32. tone 1 = paper white, 0 = full black.
        backdrop: None (transparent) or a tone (float) / (h, w) array behind the objects"""
        if self._out is not None: return self._out
        ss = self.ss
        hit = self.mat >= 0
        idx = np.flatnonzero(hit)                                       # shade only the covered pixels
        mat = self.mat.reshape(-1)[idx]
        pos = self.pos.reshape(-1, 3)[idx]
        n = self.n.reshape(-1, 3)[idx]
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        V = self.E[None, :].astype(np.float32) - pos
        dist = np.linalg.norm(V, axis=-1)
        V /= dist[:, None] + 1e-9
        ndv = (n * V).sum(-1)
        back = ndv < 0
        n[back] *= -1
        ndv = np.abs(ndv)
        k = len(idx)
        alb = np.zeros(k, np.float32); gloss = np.zeros_like(alb); shine = np.ones_like(alb)
        metal = np.zeros_like(alb); inter = np.ones_like(alb); hz = np.zeros_like(alb)
        for mid, m in enumerate(self.mats):
            sel = mat == mid
            if not sel.any(): continue
            a = np.full(int(sel.sum()), m['albedo'], np.float32)
            if m['tex'] is not None:
                a = a * np.asarray(m['tex'](pos[sel], n[sel]), np.float32)
            alb[sel] = a; gloss[sel] = m['gloss']; shine[sel] = m['shine']; metal[sel] = m['metal']
            inter[sel & back] = m['interior']; hz[sel] = 1.0 if m['haze'] else 0.0
        L1, L2 = self.key, self.fill
        d1 = np.clip(n @ L1, 0, 1); d2 = np.clip(n @ L2, 0, 1)
        hemi = 0.55 + 0.45 * n[:, 2]
        H1 = L1[None] + V; H1 /= np.linalg.norm(H1, axis=-1, keepdims=True) + 1e-9
        spec = np.clip((n * H1).sum(-1), 0, 1) ** shine
        Rz = 2 * ndv * n[:, 2] - V[:, 2]                                                 # reflected ray, z part
        env = 0.12 + 0.88 * smoothstep(-0.15, 0.55, Rz)                                  # bright sky, dark ground
        fres = 0.04 + 0.5 * (1 - ndv) ** 4
        diff = alb * (self.key_k * d1 + self.fill_k * d2 + self.amb * hemi)
        col = diff * (1 - metal) + metal * alb * (0.25 + 0.95 * env) + gloss * (1.4 * spec + fres * env)
        col = col * inter
        if self.haze:
            kh = 1 - np.exp(-dist / self.haze)
            col = col * (1 - kh * hz) + self.haze_tone * kh * hz
        t = 1 - np.exp(-col * 2.2 * self.exposure)                                       # soft film shoulder
        tone = np.zeros(self.z.size, np.float32)
        tone[idx] = np.clip(t / (1 - np.exp(-2.2 * self.exposure)), 0, 1)
        tone = tone.reshape(self.z.shape)
        # downsample with coverage
        cov = hit.astype(np.float32)
        h, w = self.h, self.w
        cs = cov.reshape(h, ss, w, ss).mean((1, 3))
        ts = (tone * cov).reshape(h, ss, w, ss).mean((1, 3)) / np.maximum(cs, 1e-6)
        if self.lens:
            wsum = blur(cs, self.lens)
            ts = blur(ts * cs, self.lens) / np.maximum(wsum, 1e-6)
            cs = np.clip(wsum * 1.0, 0, 1)
        if self.grain:
            g = blur(self.rng.random((h, w)).astype(np.float32), 0.8)
            ts = ts + self.grain * (g - g.mean()) / (g.std() + 1e-6)
        ts = np.clip(ts, 0, 1)
        if backdrop is not None:
            ts = ts * cs + np.asarray(backdrop, np.float32) * (1 - cs)
        self._out = (ts.astype(np.float32), cs.astype(np.float32))
        self.z = self.n = self.pos = self.mat = None                    # the negative is developed: free the buffers
        return self._out


# ---------------------------------------------------------------- the poster
class Constructivism:
    def __init__(self, W=1920, H=1080, seed=0, misreg=2.4, red=RED, black=BLACK):
        """misreg: typical registration error between the two plates, px"""
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.cov = {p: np.zeros((H, W), np.float32) for p in PLATES}
        self.inks = {'red': _c(red), 'black': _c(black)}
        self.paper_rgb = np.ones((H, W, 3), np.float32) * _c(PAPER)
        self.light = np.ones((H, W), np.float32)
        self.fibre = np.ones((H, W), np.float32)
        self.tooth = np.zeros((H, W), np.float32)
        self.stages = []
        self.aged = None
        r = self.rng
        self.reg = {}
        for p in PLATES:                                                    # each plate's registration error
            a = r.uniform(0, 2 * np.pi)
            mag = misreg * r.uniform(0.6, 1.0) * (1.0 if p == 'red' else 0.35)
            self.reg[p] = (np.cos(a) * mag, np.sin(a) * mag, r.normal(0, 0.02))      # dx, dy, degrees
        self._ink_fields()

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _ink_fields(self):
        H, W, r = self.H, self.W, self.rng
        self.film = {}
        for p in PLATES:
            blot = noise2d(H, W, 260, 3, self._seed())
            mott = noise2d(H, W, 22, 2, self._seed())
            fine = blur(r.random((H, W)).astype(np.float32), 0.7)
            fine = (fine - fine.mean()) / (fine.std() + 1e-6)
            # voids: dust and fibres that kept the plate off the paper
            vim = Image.new('L', (W, H), 0)
            d = ImageDraw.Draw(vim)
            for _ in range(int(W * H / 5200)):
                x, y = r.uniform(0, W), r.uniform(0, H)
                if r.random() < 0.7:
                    rr = r.uniform(0.4, 1.3)
                    d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=int(r.uniform(90, 255)))
                else:
                    a, L = r.uniform(0, np.pi), r.uniform(3, 11)
                    d.line((x, y, x + np.cos(a) * L, y + np.sin(a) * L), fill=int(r.uniform(80, 200)), width=1)
            voids = blur(np.asarray(vim, np.float32) / 255, 0.45)
            film = 1.0 - 0.07 * (blot - 0.5) - 0.05 * (mott - 0.5) - 0.018 * fine
            self.film[p] = dict(film=film.astype(np.float32), voids=voids.astype(np.float32),
                                edge=(blur(r.random((H, W)).astype(np.float32), 0.9) - 0.5).astype(np.float32))

    # ------------------------------------------------------------ the sheet
    def paper(self, colour=PAPER, aged=AGED, yellow=1.0):
        """cheap cream poster paper: cloudy pulp, fibres, dark flecks, a little cockle, yellowing at the edges"""
        H, W, r = self.H, self.W, self.rng
        base = _c(colour)
        cloud = noise2d(H, W, 300, 4, self._seed())
        t = smoothstep(0.3, 0.95, cloud)[..., None] * 0.18
        img = base * (1 - t) + _c(aged) * t
        # yellowing / greying toward the edges (light and air got at the margins, the middle was folded inside)
        ex = np.minimum(self.XX, W - 1 - self.XX) / W
        ey = np.minimum(self.YY, H - 1 - self.YY) / H
        e = np.minimum(ex * 1.7, ey * 1.0)
        wob = noise2d(H, W, 160, 3, self._seed())
        edge = (1 - smoothstep(0.0, 0.16 + 0.08 * wob, e)) * yellow
        img = img * (1 - 0.45 * edge[..., None]) + _c(aged) * 0.92 * 0.45 * edge[..., None]
        img = img * (1 - 0.05 * edge[..., None] * (1 - wob[..., None]))
        img = img * (1 + 0.014 * (noise2d(H, W, 50, 3, self._seed()) - 0.5))[..., None]
        # fibres
        fim = Image.new('L', (W, H), 128)
        d = ImageDraw.Draw(fim)
        for _ in range(int(W * H / 650)):
            x, y = r.uniform(0, W), r.uniform(0, H)
            a, L = r.uniform(0, np.pi), r.uniform(4, 20)
            bend = r.normal(0, 0.3)
            pts = [(x + np.cos(a + bend * s) * L * s, y + np.sin(a + bend * s) * L * s) for s in np.linspace(-0.5, 0.5, 5)]
            d.line(pts, fill=int(128 + r.choice([-1, 1]) * r.uniform(8, 26)), width=1)
        fib = blur((np.asarray(fim, np.float32) - 128) / 128, 0.55)
        fine = blur(r.random((H, W)).astype(np.float32), 0.6)
        self.tooth = ((fine - fine.mean()) / (fine.std() + 1e-6)).astype(np.float32)
        self.fibre = (1 + 0.045 * fib + 0.008 * self.tooth).astype(np.float32)
        # flecks in the pulp
        fl = Image.new('L', (W * 2, H * 2), 0)
        d = ImageDraw.Draw(fl)
        for _ in range(int(W * H / 5000)):
            x, y = r.uniform(0, W * 2), r.uniform(0, H * 2)
            rr = r.uniform(0.6, 2.2) * (3 if r.random() < 0.03 else 1)
            d.ellipse((x - rr, y - rr * r.uniform(0.4, 1), x + rr, y + rr * r.uniform(0.4, 1)), fill=int(r.uniform(60, 190)))
        fl = np.asarray(fl.resize((W, H), Image.BOX), np.float32) / 255
        img = img * (1 - fl[..., None] * (1 - _c('#5d4b36')))
        self.paper_rgb = img.astype(np.float32)
        cockle = noise2d(H, W, 480, 2, self._seed()) - 0.5
        grad = 1 + 0.025 * (0.5 - (self.XX / W * 0.6 + self.YY / H * 0.4))
        self.light = (grad + 0.02 * cockle).astype(np.float32)

    # ------------------------------------------------------------ masks (full canvas, anti-aliased, 0..1)
    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def ring(self, cx, cy, r, width):
        return np.clip(width / 2 - np.abs(np.hypot(self.XX - cx, self.YY - cy) - r) + 0.5, 0, 1)

    def _between(self, cx, cy, a0, a1):
        """0..1: inside the angular sector a0 -> a1 (ccw degrees, span <= 180) seen from (cx, cy)"""
        dx, dy = self.XX - cx, -(self.YY - cy)
        t0, t1 = np.deg2rad(a0), np.deg2rad(a1)
        h0 = np.cos(t0) * dy - np.sin(t0) * dx                    # left of ray a0
        h1 = -np.cos(t1) * dy + np.sin(t1) * dx                   # right of ray a1
        return np.clip(np.minimum(h0, h1) + 0.5, 0, 1)

    def arc(self, cx, cy, r, a0, a1, width):
        """a band of radius r from angle a0 to a1 (ccw), square-cut along the radii"""
        return np.minimum(self.ring(cx, cy, r, width), self._between(cx, cy, a0, a1))

    def sector(self, cx, cy, r, a0, a1):
        return np.minimum(self.circle(cx, cy, r), self._between(cx, cy, a0, a1))

    def poly(self, pts, ss=4):
        P = np.asarray(pts, np.float64)
        x0, y0 = int(np.floor(P[:, 0].min())) - 2, int(np.floor(P[:, 1].min())) - 2
        x1, y1 = int(np.ceil(P[:, 0].max())) + 2, int(np.ceil(P[:, 1].max())) + 2
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - x0) * ss, (y - y0) * ss) for x, y in P], fill=255)
        a = np.asarray(im.resize((x1 - x0, y1 - y0), Image.BOX), np.float32) / 255
        return self._place(a, x0, y0)

    def _place(self, a, x0, y0):
        out = np.zeros((self.H, self.W), np.float32)
        h, w = a.shape
        ys, xs = max(0, y0), max(0, x0)
        ye, xe = min(self.H, y0 + h), min(self.W, x0 + w)
        if ye > ys and xe > xs:
            out[ys:ye, xs:xe] = a[ys - y0:ye - y0, xs - x0:xe - x0]
        return out

    def rect(self, x0, y0, x1, y1, rot=0.0):
        """rectangle; rot (ccw degrees) turns it about its centre"""
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        t = np.deg2rad(rot)
        c, s = np.cos(t), np.sin(t)
        return self.poly([(cx + u * c + v * s, cy - u * s + v * c) for u, v in
                          [(x0 - cx, y0 - cy), (x1 - cx, y0 - cy), (x1 - cx, y1 - cy), (x0 - cx, y1 - cy)]])

    def bar(self, x0, y0, x1, y1, width, cap='butt'):
        """a straight bar from (x0, y0) to (x1, y1) -- a diagonal slab, or a rule when thin"""
        dx, dy = x1 - x0, y1 - y0
        L = float(np.hypot(dx, dy)) + 1e-6
        ux, uy = dx / L, dy / L
        u = (self.XX - x0) * ux + (self.YY - y0) * uy
        v = -(self.XX - x0) * uy + (self.YY - y0) * ux
        ext = width / 2 if cap == 'square' else 0
        return np.clip(np.minimum(width / 2 - np.abs(v), np.minimum(u + ext, L + ext - u)) + 0.5, 0, 1)

    def wedge(self, apex, angle, half, length):
        """a sharp triangle (the 'wedge') from `apex` pointing along `angle` (ccw degrees), opening by +-half"""
        ax, ay = apex
        pts = [(ax, ay)]
        for a in (angle - half, angle + half):
            t = np.deg2rad(a)
            pts.append((ax + np.cos(t) * length, ay - np.sin(t) * length))
        return self.poly(pts)

    def along(self, p, angle, d, side=0.0):
        """the point `d` px from p along `angle` (ccw degrees) and `side` px to its left"""
        t = np.deg2rad(angle)
        return p[0] + np.cos(t) * d - np.sin(t) * side, p[1] - np.sin(t) * d - np.cos(t) * side

    # ------------------------------------------------------------ type
    def text_mask(self, s, x, y, size, font_style='grotesk', anchor='ls', spacing=0.0, rot=0.0, wobble=0.0,
                  scale_x=1.0, ss=2):
        """lettering -> full-canvas mask. anchor as in Pillow ('ls' left-baseline, 'mm' centre, 'rs', 'lt' ...).
        spacing: extra px per letter. rot: ccw degrees about (x, y). wobble: hand-drawn warp of the outline, px.
        scale_x: squeeze (<1) or stretch the letters horizontally."""
        f = font(font_style, size * ss, s)
        adv = [f.getlength(ch) + spacing * ss for ch in s]
        total = sum(adv) - (spacing * ss if s else 0)
        asc, desc = f.getmetrics()
        pad = int(size * 0.4 + 8) * ss
        bw, bh = int(total + 2 * pad), int(asc + desc + 2 * pad)
        im = Image.new('L', (bw, bh), 0)
        d = ImageDraw.Draw(im)
        base = pad + asc
        if spacing:
            cx = pad
            for ch, a in zip(s, adv):
                d.text((cx, base), ch, font=f, fill=255, anchor='ls')
                cx += a
        else:
            d.text((pad, base), s, font=f, fill=255, anchor='ls')
        bb = f.getbbox('H', anchor='ls')
        capH = -bb[1]
        ax = pad + total * {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor[0]]
        ay = base - {'s': 0, 'm': capH / 2, 't': capH, 'a': capH, 'b': -desc, 'd': -desc}[anchor[1]]
        if scale_x != 1.0:
            nw = max(1, int(round(bw * scale_x)))
            im = im.resize((nw, bh), Image.LANCZOS)
            ax *= scale_x
        a = np.asarray(im.resize((im.width // ss, im.height // ss), Image.BOX), np.float32) / 255
        ax, ay = ax / ss, ay / ss
        if wobble:
            h, w = a.shape
            g = np.random.default_rng(self._seed())
            dx = (noise2d(h, w, max(6.0, size * 0.35), 2, int(g.integers(1 << 30))) - 0.5) * 2 * wobble
            dy = (noise2d(h, w, max(6.0, size * 0.35), 2, int(g.integers(1 << 30))) - 0.5) * 2 * wobble
            a = _warp(a, dx, dy)
        if rot:
            h, w = a.shape
            R = int(np.hypot(h, w)) + 4
            big = np.zeros((2 * R, 2 * R), np.float32)
            ox, oy = int(round(R - ax)), int(round(R - ay))
            big[oy:oy + h, ox:ox + w] = a
            big = _rotate(big, rot, center=(R, R))
            return self._place(big, int(round(x)) - R, int(round(y)) - R)
        return self._place(a, int(round(x - ax)), int(round(y - ay)))

    def text_width(self, s, size, font_style='grotesk', spacing=0.0):
        f = font(font_style, size, s)
        return sum(f.getlength(ch) + spacing for ch in s) - (spacing if s else 0)

    def text(self, s, x, y, size, plate='black', font_style='grotesk', anchor='ls', spacing=0.0, rot=0.0,
             wobble=0.0, scale_x=1.0, knock=None):
        """print lettering on a plate (and optionally knock the same letters out of other plates)"""
        m = self.text_mask(s, x, y, size, font_style, anchor, spacing, rot, wobble, scale_x)
        self.ink(m, plate)
        if knock:
            self.knock(m, knock)
        return m

    # ------------------------------------------------------------ inking
    def ink(self, mask, plate='black', knock=None, density=1.0):
        """ink a mask on a plate. knock: a mask cut out of this same solid (type reversed out of a bar)"""
        m = np.clip(mask if knock is None else mask - knock, 0, 1) * density
        c = self.cov[plate]
        np.maximum(c, m, out=c)

    def knock(self, mask, plates=PLATES):
        """knock a mask out of plates: nothing is printed there (the paper shows)"""
        for p in ((plates,) if isinstance(plates, str) else plates):
            self.cov[p] *= (1 - np.clip(mask, 0, 1))

    def tint(self, mask, plate='black', level=0.3, cell=7.0, angle=45.0):
        """a flat halftone tint (a screen of dots at one percentage) inside mask"""
        rows, cols = np.flatnonzero(mask.max(1) > 0.002), np.flatnonzero(mask.max(0) > 0.002)
        if not len(rows): return
        sl = (slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1))
        rough = self._rough(sl)
        ht = halftone(np.full(mask[sl].shape, level, np.float32), self.XX[sl], self.YY[sl], cell, angle, rough,
                      soften=0)
        sub = self.cov[plate][sl]
        np.maximum(sub, ht * mask[sl], out=sub)

    def _rough(self, sl):
        return 0.07 * self.film['black']['edge'][sl] / 0.12

    def waves(self, cx, cy, r0, r1, step, width, a0, a1, plates=('black', 'red'), grow=0.0):
        """concentric wave fronts radiating from (cx, cy) inside the angles a0 -> a1, cycling through `plates`.
        grow: change of width per 100 px of radius, as a fraction (+ fatten, - thin out as they spread)"""
        k = 0
        r = r0
        while r <= r1:
            w = max(2.0, width * (1 + grow * (r - r0) / 100))
            self.ink(self.arc(cx, cy, r, a0, a1, w), plates[k % len(plates)])
            r += step; k += 1

    # ------------------------------------------------------------ photomontage
    def montage(self, photo, cx, cy, rot=0.0, scale=1.0, plate='black', cut=None, backdrop=0.94, cell=7.0,
                angle=45.0, contrast=1.0, gamma=1.0, gain=0.55, cut_wander=0.35, close=0, soften=0.3):
        """paste a photograph (a Photo or (tone, alpha)) centred at (cx, cy), turned rot degrees ccw and scaled,
        then screen it into the halftone on `plate`. cut: scissor margin in px (the cut piece covers what is
        under it); None: retouched out of its background and overprinted. backdrop: tone of the photo's own
        background inside the cut. close: px of closing applied to the silhouette before cutting (bridges the
        gaps of a lattice so the scissors go round the outside). soften: blur before screening, in cells (lower keeps
        thin members and narrow gaps open, higher gives rounder, calmer dots)."""
        tone, alpha = photo.render() if hasattr(photo, 'render') else photo
        tone = np.clip(0.5 + (tone - 0.5) * contrast, 0, 1) ** gamma
        dark = alpha * (1 - tone)
        h, w = tone.shape
        if scale != 1.0:
            nw, nh = int(round(w * scale)), int(round(h * scale))
            dark = np.asarray(Image.fromarray(dark, 'F').resize((nw, nh), Image.BILINEAR), np.float32)
            alpha = np.asarray(Image.fromarray(alpha, 'F').resize((nw, nh), Image.BILINEAR), np.float32)
            h, w = nh, nw
        pad = int((cut or 0) + 30)
        dark = np.pad(dark, pad); alpha = np.pad(alpha, pad)
        if rot:
            dark = _rotate(dark, rot, expand=True); alpha = _rotate(alpha, rot, expand=True)
        h, w = dark.shape
        x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
        D = self._place(dark, x0, y0); A = self._place(alpha, x0, y0)
        ys, xs = max(0, y0), max(0, x0)
        ye, xe = min(self.H, y0 + h), min(self.W, x0 + w)
        sl = (slice(ys, ye), slice(xs, xe))
        piece = None
        if cut:
            a = A[sl]
            if close:
                a = 1 - _dilate(1 - _dilate((a > 0.3).astype(np.float32), close), close)
                a = np.maximum(a, A[sl])
            m = _fill_holes(_dilate((a > 0.25).astype(np.float32), cut))   # scissors go round, never in
            n = noise2d(m.shape[0], m.shape[1], 90, 3, self._seed()) - 0.5
            m = blur(m, 2.2 + cut * 0.12)
            m = smoothstep(0.42 + cut_wander * n * 0.5, 0.58 + cut_wander * n * 0.5, m)
            piece = np.zeros((self.H, self.W), np.float32)
            piece[sl] = np.maximum(m, A[sl])
            D[sl] = D[sl] + (1 - A[sl]) * (1 - backdrop) * piece[sl]
            self.knock(piece)
        ht = halftone(D[sl], self.XX[sl], self.YY[sl], cell, angle, self._rough(sl), gain, soften)
        if piece is not None:
            ht *= piece[sl]
        sub = self.cov[plate][sl]
        np.maximum(sub, ht, out=sub)
        return piece if piece is not None else A

    # ------------------------------------------------------------ a century later
    def age(self, folds=(1, 1), foxing=1.0, stain=True, pins=True, crack=1.0, grime=1.0):
        """folds: (vertical, horizontal) fold lines -- the sheet folded into equal panels; ink cracks off along
        them. foxing: brown spots. stain: a faint water tide line. pins: drawing-pin holes in the corners."""
        H, W, r = self.H, self.W, self.rng
        light = np.ones((H, W), np.float32); dirt = np.zeros((H, W), np.float32)
        crackm = np.zeros((H, W), np.float32); wear = np.zeros((H, W), np.float32)
        lines = [('v', W * (i + 1) / (folds[0] + 1)) for i in range(folds[0])]
        lines += [('h', H * (i + 1) / (folds[1] + 1)) for i in range(folds[1])]
        for kind, pos in lines:
            n = W if kind == 'h' else H
            wav = fbm1d(n, 300, 4, self._seed()) * 2.0 + pos
            coord = self.XX if kind == 'v' else self.YY
            along = self.YY if kind == 'v' else self.XX
            off = wav[along.astype(np.int32)]
            d = coord - off
            sgn = r.choice([-1, 1])
            light *= 1 + sgn * 0.035 * np.exp(-(d - 1.6) ** 2 / 3.0) - sgn * 0.045 * np.exp(-(d + 1.6) ** 2 / 3.0)
            light *= 1 - 0.035 * np.exp(-d ** 2 / 0.8)
            dirt = np.maximum(dirt, np.exp(-d ** 2 / (2 * 9.0 ** 2)) * (0.5 + 0.5 * noise2d(H, W, 40, 2, self._seed())))
            gate = smoothstep(0.22, 0.6, noise2d(H, W, 16, 2, self._seed()))
            jit = blur(r.random((H, W)).astype(np.float32), 0.6)
            crackm = np.maximum(crackm, np.clip(1.6 - np.abs(d) / 1.2, 0, 1) * gate * smoothstep(0.3, 0.55, jit) * crack)
            rough = noise2d(H, W, 6, 2, self._seed())
            wear = np.maximum(wear, np.exp(-d ** 2 / (2 * 3.2 ** 2)) * (0.35 + 0.65 * rough) * crack)
        # foxing
        fox = np.zeros((H, W), np.float32)
        for _ in range(int(40 * foxing)):
            x, y = r.uniform(0, W), r.uniform(0, H)
            rad = r.lognormal(1.2, 0.6)
            fox = np.maximum(fox, np.exp(-((self.XX - x) ** 2 + (self.YY - y) ** 2) / (2 * rad ** 2)) * r.uniform(0.25, 0.8))
        # tide line of an old water stain (lower-right corner area)
        tide = np.zeros((H, W), np.float32)
        if stain:
            sx, sy, sr = W * r.uniform(0.86, 0.95), H * r.uniform(0.84, 0.95), r.uniform(150, 230)
            ang = np.arctan2(self.YY - sy, self.XX - sx)
            rr = np.hypot(self.XX - sx, self.YY - sy) / sr
            wob = 1 + 0.12 * np.sin(3 * ang + 1) + 0.07 * np.sin(7 * ang + 2)
            q = rr / wob
            tide = np.exp(-(q - 1) ** 2 / (2 * 0.012 ** 2)) * 0.6 + smoothstep(1.0, 0.2, q) * 0.12
        # rubbed corners
        cx = np.minimum(self.XX, W - 1 - self.XX); cy = np.minimum(self.YY, H - 1 - self.YY)
        rub = np.exp(-(cx ** 2 + cy ** 2) / (2 * 55.0 ** 2)) * noise2d(H, W, 12, 2, self._seed())
        holes = np.zeros((H, W), np.float32); halo = np.zeros((H, W), np.float32)
        if pins:
            for (px, py) in [(22, 22), (W - 24, 20), (21, H - 23), (W - 22, H - 21)]:
                px += r.uniform(-5, 5); py += r.uniform(-5, 5)
                d = np.hypot(self.XX - px, self.YY - py)
                holes = np.maximum(holes, np.clip(2.6 - d, 0, 1))
                halo = np.maximum(halo, np.exp(-d ** 2 / (2 * 6.0 ** 2)) * (0.6 + 0.4 * np.cos(np.arctan2(self.YY - py, self.XX - px) - r.uniform(0, 6.3))))
        self.aged = dict(light=light, dirt=dirt * 0.06 * grime, crack=crackm, wear=wear, fox=fox, tide=tide,
                         rub=rub, holes=holes, halo=halo)

    # ------------------------------------------------------------ output
    def _plate(self, p):
        dx, dy, rot = self.reg[p]
        c = self.cov[p]
        if dx or dy or rot:
            P = 8                                          # the sheet was trimmed after printing: no bare edge
            im = Image.fromarray(np.pad(c, P, mode='edge'), 'F')
            t = np.deg2rad(rot)
            cs, sn = np.cos(t), np.sin(t)
            cx, cy = self.W / 2, self.H / 2
            # output -> input: rotate by -rot about the centre, then subtract the shift
            a, b = cs, -sn
            d_, e = sn, cs
            c0 = cx - a * (cx + dx) - b * (cy + dy) + P
            f0 = cy - d_ * (cx + dx) - e * (cy + dy) + P
            c = np.asarray(im.transform((self.W, self.H), Image.AFFINE, (a, b, c0, d_, e, f0), resample=Image.BILINEAR),
                           np.float32)
        F = self.film[p]
        # ragged edge at the scale of the fibres, a heavier squeeze of ink at the edge of solids
        e = c + F['edge'] * 0.55 * (c * (1 - c) * 4)
        e = smoothstep(0.2, 0.8, e)
        rim = np.clip(e - blur(e, 2.0), 0, 1)
        dens = e * np.clip(F['film'] + 0.06 * rim, 0, 1.08) * (1 - 0.85 * F['voids'])
        return np.clip(dens, 0, 1)

    def composite(self):
        img = self.paper_rgb.copy()
        ag = self.aged
        if ag is not None:
            img *= (1 - ag['fox'][..., None] * 0.2 * (1 - _c('#a77a45')))
            img *= (1 - ag['tide'][..., None] * 0.12 * (1 - _c('#9c7a4c')))
        for p in PLATES:
            dns = self._plate(p)
            if ag is not None:
                dns = dns * (1 - ag['crack']) * (1 - 0.22 * ag['wear']) * (1 - 0.25 * ag['rub'])
            ink = self.inks[p]
            filt = np.clip(ink / np.array([0.93, 0.89, 0.80], np.float32), 0, 1)       # ink as a filter
            img = img * (1 - dns[..., None] + dns[..., None] * filt)
        L = self.light * self.fibre
        if ag is not None:
            L = L * ag['light']
            img = img * (1 - ag['dirt'][..., None]) * (1 - 0.3 * ag['halo'][..., None] * (1 - _c('#8a5a2b')))
            img = img * (1 - ag['holes'][..., None]) + ag['holes'][..., None] * _c('#2a2118')
            img = img * (1 - 0.06 * ag['rub'][..., None]) + 0.06 * ag['rub'][..., None] * _c('#e6dcc4')
        img = img * L[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

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
