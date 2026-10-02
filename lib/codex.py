"""codex — a Renaissance engineer's notebook page in the manner of Leonardo's codices: iron-gall ink from a quill
on laid rag paper, left-handed hatching, red chalk, stylus and compass construction, exploded machine parts and
mirror writing (numpy + Pillow only).

Model:
  sheet     laid rag paper on a museum mount. The ground is a warm buff with fibre mottling, the faint wire marks
            of the paper mould (fine horizontal laid lines, wavy vertical chain lines every ~170 px), and a
            `tooth` field that red chalk catches on. Time is baked into the sheet: browned and slightly ragged
            edges, one lost corner, large soft clouds where the sizing yellowed unevenly, rust-coloured foxing
            specks (crisp cores, small clusters), a water stain whose tide line is darker than its inside, an
            optional old vertical fold (bright on one lip, dark on the other, grimy along the crease), handling
            grime near the lower corners, and writing from the back of the leaf showing through -- reversed, so
            it reads left to right (`show_through`).
  ink       iron-gall ink is a density field `ink`. A quill stroke is a polyline smoothed, resampled to ~1.3 px
            and wobbled by the hand; its width follows the broad nib (wider where the line runs across the nib's
            edge, cut at ~35 deg), a heavier touch-down and a tapering lift-off. The pen carries a load: every px
            drawn uses ink, so strokes grow paler until the pen is re-dipped, and a fresh dip can pool a small
            dark bead where the next stroke starts. Composite is a multiply: thin ink is warm amber-brown, thick
            ink dark umber, overlaps darken (crossings in hatching), a faint halo bleeds into the fibres, and the
            paper's fibre texture breaks the ink up a little.
  hatching  Leonardo was left-handed, so his parallel hatching runs '\\' (top left to bottom right) almost
            everywhere, whatever the form. Tone is density: a shade field (0 lit .. 1 dark) is cut into levels;
            the first level is spaced hatching, the next interleaves between those lines, the darkest adds a
            second direction (cross-hatching). A hand hatches in bands -- a row of parallel strokes of about one
            length, then the next row -- so long runs are cut where staggered band edges fall, never chained
            stroke after stroke (that reads as wavy fur). Strokes are all bowed the same way (a pivoting wrist),
            start a little heavier and over- or undershoot the contour by a pixel or two. `between()` gives the
            0..1 field across a panel from one rib to the next, the usual way to make a membrane billow.
  chalk     red chalk (sanguine) deposits only where it touches the paper tooth: light pressure grazes the tops
            of the grain, heavy pressure fills the valleys; `rub` smears it into a soft tone.
  stylus    construction lines pressed with a stylus or a compass leg have no colour: they are a height field
            lit by raking light (the wall facing the light is bright, the other dark); compass centres leave
            prick holes. `lead` is a faint grey leadpoint underdrawing with searching lines.
  writing   mirror writing in a chancery cursive (Apple Chancery / URW Chancery, else any script face), flipped:
            every line starts at the right margin and is ragged on the left; letters jitter in size and
            baseline, the baseline drifts, the pen fades and is re-dipped mid-line. `prose()` makes
            pseudo-Italian; letters such as a, b, c label points of the drawings.
  solids    machine parts (spur gears, lantern pinions, crown wheels, cranks, axles, beams, pulleys) are small
            meshes drawn by a pen renderer: an orthographic camera, a z-buffer, every face shaded by how far it
            turns from the light, each surface group hatched with that tone, the ink of whatever is behind the
            solid erased (a draughtsman simply does not draw hidden lines), and only feature edges -- silhouette,
            creases sharper than ~30 deg, open borders -- chained into long quill strokes; hidden parts of an
            edge are dropped by depth test. Exploded views are the same parts slid apart along a dot-dash axis.
  objects   things Leonardo drew again and again: `cane` (a rod as two converging pen lines with cord lashings,
            returns its outline for masking), `feather` (curved rachis, narrow leading vane, broad trailing vane,
            rounded tip; `overlapped=True` draws only what shows in a fanned wing), `bird` (a little bird seen from
            behind at any phase of the wing-beat: bent wrist, spread primaries, body and tail).
  accidents ink blots with a darker tide rim and satellite drops, spatter, struck-out sketches, contours searched
            two or three times before the final line (pentimenti).
Angles are screen degrees, clockwise (y points down): 55 is the left-hander's '\\', -40 is '/'.

    from codex import Codex, Camera, gear, merge
    c = Codex(1920, 1080, seed=3)
    c.sheet()
    c.compass(960, 540, 200)                                   # blind compass circle + prick hole
    c.quill(Codex.arc(960, 540, 200, 0, 360), width=2.2)       # inked over
    c.hatch(c.disc_mask(960, 540, 200), shade=c.radial_shade(960, 540, 200))
    cam = Camera(1400, 700, azim=-30, elev=35)
    c.solid(gear(80, 16, 12, 30), cam)
    c.write(c.prose(40), x=700, y=200, width=420, size=21)     # mirror-written paragraph
    c.save('page.jpg')
"""
import os
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts, shift, load_font

INK_DARK = np.array([0.19, 0.105, 0.045], np.float32)     # thick iron-gall ink, aged to umber
INK_LIGHT = np.array([0.60, 0.40, 0.18], np.float32)     # thin ink, warm amber-brown
INK_HALO = np.array([0.80, 0.64, 0.42], np.float32)      # what migrates into the fibres
SANGUINE = '#a9482c'
LEADPOINT = '#6a6762'
PAPER = '#e9d7ae'
MOUNT = '#6b5f52'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _resample(P, step):
    P = np.asarray(P, np.float32)
    if len(P) < 2: return P
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(np.ceil(s[-1] / step)) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


# ------------------------------------------------------------------------------------------- pseudo-Italian
_SYL = ['la', 'le', 'li', 'lo', 'ra', 're', 'ri', 'ro', 'ta', 'te', 'ti', 'to', 'na', 'ne', 'ni', 'no', 'ma', 'me',
        'mo', 'pa', 'pe', 'po', 'sa', 'se', 'so', 'ca', 'che', 'chi', 'co', 'da', 'de', 'di', 'do', 'va', 've', 'vo',
        'gli', 'gna', 'gno', 'zza', 'zzo', 'qua', 'que', 'stra', 'ssi', 'tte', 'lla', 'nte', 'nto', 'rri', 'ppo', 'ffe']
_SMALL = ['e', 'la', 'il', 'che', 'di', 'del', 'della', 'per', 'con', 'non', 'se', 'al', 'nel', 'quando', 'come',
          'piu', 'sua', 'suo', 'essa', 'tal', 'ogni', 'cosi', 'ma', 'o', 'a', 'in', 'da', 'lo', 'le']
_TERMS = ['ala', 'penna', 'moto', 'vento', 'aria', 'peso', 'leva', 'rota', 'corda', 'polo', 'perno', 'forza',
          'canna', 'tela', 'nodo', 'braccio', 'volo', 'batte', 'sotto', 'sopra']


# ------------------------------------------------------------------------------------------- solids
class Camera:
    """orthographic camera. World: x right, y forward (away), z up. azim turns the object about z, elev tilts the
    view down from above; `scale` px per unit; (cx, cy) is where the world origin lands on the page."""

    def __init__(self, cx, cy, scale=1.0, azim=-30.0, elev=30.0):
        self.cx, self.cy, self.s = cx, cy, scale
        a, e = np.deg2rad(azim), np.deg2rad(elev)
        Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]], np.float32)
        right = np.array([1, 0, 0], np.float32)
        toward = np.array([0, -np.cos(e), np.sin(e)], np.float32)      # from the scene to the eye
        up = np.array([0, np.sin(e), np.cos(e)], np.float32)
        self.B = np.stack([right, toward, up]) @ Rz                     # rows: right, toward, up in world coords

    def cam(self, P):
        return np.asarray(P, np.float32) @ self.B.T                      # (right, toward, up)

    def project(self, P):
        C = self.cam(P)
        xy = np.stack([self.cx + C[:, 0] * self.s, self.cy - C[:, 2] * self.s], 1)
        return xy.astype(np.float32), (-C[:, 1] * self.s).astype(np.float32)   # depth: larger is farther


class Mesh:
    """vertices (N, 3), faces (lists of vertex indices, counter-clockwise seen from outside) and a surface group
    name per face (each group is hatched as one surface)"""

    def __init__(self, V=None, F=None, G=None):
        self.V = np.zeros((0, 3), np.float32) if V is None else np.asarray(V, np.float32)
        self.F = [] if F is None else [list(f) for f in F]
        self.G = [] if G is None else list(G)

    def place(self, origin=(0, 0, 0), axis=(0, 0, 1), spin=0.0):
        """local z -> `axis`, then move to `origin`; spin turns the part about its own axis first (degrees)"""
        z = np.asarray(axis, np.float32); z /= np.linalg.norm(z)
        ref = np.array([0, 0, 1], np.float32) if abs(z[2]) < 0.9 else np.array([1, 0, 0], np.float32)
        x = np.cross(ref, z); x /= np.linalg.norm(x); y = np.cross(z, x)
        sp = np.deg2rad(spin)
        Vl = self.V.copy()
        Vl[:, 0], Vl[:, 1] = self.V[:, 0] * np.cos(sp) - self.V[:, 1] * np.sin(sp), self.V[:, 0] * np.sin(sp) + self.V[:, 1] * np.cos(sp)
        V = Vl[:, :1] * x + Vl[:, 1:2] * y + Vl[:, 2:3] * z + np.asarray(origin, np.float32)
        return Mesh(V, self.F, self.G)

    def named(self, prefix):
        return Mesh(self.V, self.F, [prefix + '.' + g for g in self.G])


def merge(*meshes):
    V, F, G, off = [], [], [], 0
    for m in meshes:
        V.append(m.V); F += [[i + off for i in f] for f in m.F]; G += m.G; off += len(m.V)
    return Mesh(np.concatenate(V) if V else None, F, G)


def extrude(outline, h, cap='cap', side='side', z0=0.0):
    """prism: a counter-clockwise 2D outline from z0 to z0 + h"""
    P = np.asarray(outline, np.float32)
    M = len(P)
    V = np.concatenate([np.c_[P, np.full(M, z0)], np.c_[P, np.full(M, z0 + h)]]).astype(np.float32)
    F = [list(range(M - 1, -1, -1)), list(range(M, 2 * M))]
    G = [cap + '_bottom', cap]
    for i in range(M):
        j = (i + 1) % M
        F.append([i, j, M + j, M + i]); G.append(side)
    return Mesh(V, F, G)


def circle_outline(r, n=48):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([np.cos(t) * r, np.sin(t) * r], 1)


def cylinder(r, h, n=40, cap='cap', side='side', z0=0.0):
    return extrude(circle_outline(r, n), h, cap, side, z0)


def box(sx, sy, sz):
    """a beam centred on the origin"""
    m = extrude([(-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)], sz, 'end', 'face', -sz / 2)
    for i, f in enumerate(m.F[2:]):                         # name the four long faces separately: crisp creases
        m.G[2 + i] = 'face%d' % i
    return m


def gear(r, teeth, depth, h, hub=None):
    """spur gear of radius r (tip), `teeth` trapezoid teeth `depth` deep, thickness h; optional hub boss"""
    pts = []
    for k in range(teeth):
        a0 = 2 * np.pi * k / teeth
        da = 2 * np.pi / teeth
        for f, rr in [(0.0, r - depth), (0.18, r - depth), (0.30, r), (0.62, r), (0.74, r - depth)]:
            pts.append((np.cos(a0 + f * da) * rr, np.sin(a0 + f * da) * rr))
    m = extrude(pts, h, 'face', 'teeth')
    if hub:
        m = merge(m, cylinder(hub[0], hub[1], 28, 'hub_face', 'hub', h))
    return m


def lantern(r, h, staves=8, stave_r=None, disc_h=None):
    """lantern pinion: two thin discs joined by round staves (the pins the crown wheel's teeth push)"""
    stave_r = stave_r or r * 0.09
    disc_h = disc_h or r * 0.16
    parts = [cylinder(r, disc_h, 44, 'disc_low', 'rim_low'), cylinder(r, disc_h, 44, 'disc', 'rim', h - disc_h)]
    for k in range(staves):
        a = 2 * np.pi * k / staves
        s = cylinder(stave_r, h - 2 * disc_h, 10, 'stave_end', 'stave', disc_h)
        s.V[:, 0] += np.cos(a) * r * 0.74; s.V[:, 1] += np.sin(a) * r * 0.74
        parts.append(s)
    return merge(*parts)


def crown(r, h, teeth=16, tooth_h=None, tooth_w=None):
    """crown wheel: a disc with square pegs standing up round its rim (meshes with a lantern pinion at 90 deg)"""
    tooth_h = tooth_h or r * 0.22
    tooth_w = tooth_w or r * 0.11
    parts = [cylinder(r, h, 64, 'face', 'rim')]
    for k in range(teeth):
        a = 2 * np.pi * k / teeth
        t = box(tooth_w, tooth_w, tooth_h)
        t.V[:, 2] += h + tooth_h / 2
        ca, sa = np.cos(a), np.sin(a)
        x, y = t.V[:, 0].copy(), t.V[:, 1].copy()
        t.V[:, 0] = (x + r - tooth_w * 0.75) * ca - y * sa
        t.V[:, 1] = (x + r - tooth_w * 0.75) * sa + y * ca
        t.G = ['peg_top' if g == 'end' else ('peg_bottom' if g == 'end_bottom' else 'peg') for g in t.G]
        parts.append(t)
    return merge(*parts)


def crank(arm, r_axle, handle_len, handle_r, throw_w=None):
    """bent crank: a flat iron arm along +x from the axle end (z=0), a round wooden handle standing at its tip"""
    throw_w = throw_w or r_axle * 1.6
    a = box(arm + throw_w, throw_w, throw_w * 0.6)
    a.V[:, 0] += arm / 2
    a.G = ['arm_' + g for g in a.G]
    boss = cylinder(r_axle * 1.9, throw_w * 1.1, 20, 'boss_end', 'boss', -throw_w * 1.1)     # socket for the shaft
    hnd = cylinder(handle_r, handle_len, 18, 'handle_end', 'handle', throw_w * 0.3)
    hnd.V[:, 0] += arm
    return merge(a, boss, hnd)


def pulley(r, h, groove=0.25):
    """grooved sheave: two flanges with a narrower waist (the cord runs in the groove)"""
    q = h / 4
    return merge(cylinder(r, q, 36, 'flange_low', 'rim_low'), cylinder(r * (1 - groove), 2 * q, 36, 'waist_cap', 'groove', q),
                 cylinder(r, q, 36, 'flange', 'rim', 3 * q))


# ------------------------------------------------------------------------------------------- the page
class Codex:
    def __init__(self, W=1920, H=1080, seed=0, ss=3, nib=35.0):
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.nib = np.deg2rad(nib)
        self.ink = np.zeros((H, W), np.float32)
        self.chalk = np.zeros((H, W), np.float32)
        self.lead = np.zeros((H, W), np.float32)
        self.groove = np.zeros((H, W), np.float32)
        self.load = 1.0
        self.use = 1.0 / 2600.0               # load used per px of 2 px line
        self.fresh = False
        self.base = None
        self.mask = np.ones((H, W), np.float32)
        self.tooth = None
        self._fonts = {}
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _box(self, x0, y0, x1, y1):
        x0, y0 = max(0, int(np.floor(x0))), max(0, int(np.floor(y0)))
        x1, y1 = min(self.W, int(np.ceil(x1))), min(self.H, int(np.ceil(y1)))
        if x1 <= x0 or y1 <= y0: return None
        return (slice(y0, y1), slice(x0, x1))

    # ------------------------------------------------------------ paper
    def sheet(self, tone=PAPER, mount=MOUNT, margin=(30, 26), laid=5.6, chain=172, lost_corner='br', fold=None,
              stains=None, foxing=1.0, edges=1.0, age=1.0):
        """the leaf on its mount. stains: [(cx, cy, r)] water stains; fold: x of an old vertical fold"""
        W, H, r = self.W, self.H, self.rng
        YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
        mx, my = margin
        # ragged sheet outline
        e = lambda n, sc, s: fbm1d(n, sc, 4, s) * 3.0 * edges
        top = my + e(W, 90, self._seed()); bot = H - my + e(W, 90, self._seed())
        lef = mx + e(H, 90, self._seed()); rig = W - mx + e(H, 90, self._seed())
        inside = (YY >= top[None, :]) & (YY <= bot[None, :]) & (XX >= lef[:, None]) & (XX <= rig[:, None])
        m = inside.astype(np.float32)
        for _ in range(int(7 * edges)):                         # small chips out of the edges
            side = r.integers(4)
            if side == 0: cx, cy = r.uniform(mx, W - mx), my
            elif side == 1: cx, cy = r.uniform(mx, W - mx), H - my
            elif side == 2: cx, cy = mx, r.uniform(my, H - my)
            else: cx, cy = W - mx, r.uniform(my, H - my)
            m *= 1 - polygon_mask(H, W, blob_pts(cx, cy, r.uniform(4, 11), r.uniform(3, 7), 0.4, 24, self._seed(), r.uniform(0, 3)))
        if lost_corner:
            cx = W - mx if 'r' in lost_corner else mx
            cy = H - my if 'b' in lost_corner else my
            sx, sy = (-1 if 'r' in lost_corner else 1), (-1 if 'b' in lost_corner else 1)
            n = 30
            t = np.linspace(0, 1, n)
            tear = np.stack([cx + sx * (1 - t) * 74, cy + sy * t * 52], 1) + fbm1d(n, 8, 3, self._seed())[:, None] * 6
            poly = np.vstack([[cx + sx * 90, cy - sy * 20], tear, [cx - sx * 20, cy + sy * 70], [cx - sx * 20, cy - sy * 20]])
            m *= 1 - polygon_mask(H, W, poly, 2)
        m = blur(m, 0.7)
        self.mask = m
        # paper body
        col = _c(tone)
        mott = noise2d(H, W, 260, 4, self._seed()) - 0.5
        cloud = noise2d(H, W, 60, 3, self._seed()) - 0.5
        g = r.random((H, W)).astype(np.float32)
        fib = blur(g, 0.6) - 0.5
        streak = np.asarray(Image.fromarray(r.random((H // 3, W // 22)).astype(np.float32)).resize((W, H), Image.BILINEAR)) - 0.5
        self.fib = np.clip(0.5 + 2.2 * fib + 0.8 * streak, 0, 1).astype(np.float32)
        self.tooth = np.clip(0.5 + 2.6 * fib + 0.9 * cloud + 0.4 * streak, 0, 1).astype(np.float32)
        laidl = np.cos(2 * np.pi * (YY + 1.4 * fbm1d(W, 300, 3, self._seed())[None, :]) / laid)
        laidl *= 0.5 + 0.5 * noise2d(H, W, 120, 2, self._seed())
        ch = np.zeros((H, W), np.float32)
        x = mx + r.uniform(30, 90)
        while x < W - mx:
            wav = x + 3 * fbm1d(H, 200, 3, self._seed())
            d = XX - wav[:, None]
            ch += np.exp(-d ** 2 / 3.0) - 0.45 * np.exp(-d ** 2 / 40.0)
            x += chain * r.uniform(0.96, 1.04)
        lum = 1 + 0.045 * mott + 0.02 * cloud + 0.016 * fib + 0.008 * streak + 0.006 * laidl + 0.012 * ch
        paper = col[None, None, :] * lum[..., None]
        # age: large soft brownish clouds where the sizing has yellowed unevenly
        ag = smoothstep(0.5, 0.86, noise2d(H, W, 210, 4, self._seed())) * (0.55 + 0.45 * noise2d(H, W, 46, 3, self._seed()))
        a_ = (0.115 * ag * age)[..., None]
        paper = paper * (1 - a_ * (1 - np.array([0.74, 0.56, 0.36], np.float32)))
        # browning toward the edges (oxidised), with a warmer, darker band right at the edge
        dist = blur(m, 34)
        brown = np.clip(1 - dist * 1.35, 0, 1) ** 1.3 * (0.7 + 0.6 * noise2d(H, W, 90, 3, self._seed()))
        rim = np.clip(1 - blur(m, 5) * 1.25, 0, 1) * m
        tan = np.array([0.66, 0.47, 0.27], np.float32)
        k = np.clip(0.55 * brown + 0.5 * rim, 0, 0.9)[..., None]
        paper = paper * (1 - k) + paper * tan * 1.05 * k
        # foxing: rust specks in loose clusters
        spots = np.zeros((H, W), np.float32)
        for _ in range(int(26 * foxing)):
            cx, cy = r.uniform(mx, W - mx), r.uniform(my, H - my)
            for _ in range(int(r.integers(2, 14))):
                sx, sy = cx + r.normal(0, 22), cy + r.normal(0, 16)
                rad = r.uniform(0.5, 2.4) if r.random() < 0.88 else r.uniform(3, 6)
                ext = rad * 7 + 3
                sl = self._box(sx - ext, sy - ext, sx + ext + 1, sy + ext + 1)
                if sl is None: continue
                d2 = (XX[sl] - sx) ** 2 + (YY[sl] - sy) ** 2
                core_ = np.clip((rad - np.sqrt(d2)) / 1.2 + 0.5, 0, 1) * r.uniform(0.35, 0.9)
                spots[sl] += core_ * (0.8 + 0.4 * self.rng.random(d2.shape)) + 0.07 * np.exp(-d2 / (2 * (rad * 1.9) ** 2))
        rust = np.array([0.56, 0.33, 0.16], np.float32)
        sp = blur(np.clip(spots, 0, 1), 0.6)[..., None] * 0.5
        paper = paper * (1 - sp) + paper * rust * sp
        # water stains: slightly darker inside, a crisp darker tide line at the edge where the water stopped
        for (cx, cy, rad) in (stains or []):
            st = polygon_mask(H, W, blob_pts(cx, cy, rad, rad * r.uniform(0.6, 0.85), 0.22, 160, self._seed(), r.uniform(0, 3)), 2)
            st = blur(st, 1.0)
            tide = np.clip(np.clip(st - blur(st, 6), 0, 1) * 2.2 + np.clip(st - blur(st, 2.0), 0, 1) * 1.2, 0, 1)
            tide *= 0.6 + 0.8 * noise2d(H, W, 40, 2, self._seed())
            a = (0.05 * blur(st, 14) + 0.16 * tide)[..., None]
            paper = paper * (1 - a * (1 - np.array([0.74, 0.56, 0.34], np.float32)))
        # an old fold: one lip catches the light, the other is in shadow, grime in the crease
        if fold is not None:
            fx = fold + 2.0 * fbm1d(H, 260, 3, self._seed())
            d = XX - fx[:, None]
            crease = 0.05 * np.exp(-(d + 2.2) ** 2 / 5.0) - 0.07 * np.exp(-(d - 1.6) ** 2 / 4.0) - 0.035 * np.exp(-d ** 2 / 70.0)
            paper *= (1 + crease * (0.7 + 0.6 * noise2d(H, W, 50, 2, self._seed())))[..., None]
        # handling grime near the lower corners (where the leaf was turned)
        for gx, gy in [(W - mx - 150, H - my - 130), (mx + 120, H - my - 100)]:
            gr = np.exp(-(((XX - gx) / 210) ** 2 + ((YY - gy) / 150) ** 2)) * (0.5 + noise2d(H, W, 40, 3, self._seed()))
            paper *= (1 - 0.06 * gr)[..., None]
        # the mount (card) and the sheet's shadow on it
        mc = _c(mount)
        card = mc[None, None, :] * (1 + 0.04 * (noise2d(H, W, 30, 3, self._seed()) - 0.5) + 0.02 * fib)[..., None]
        sh = blur(shift(m, 3, 5), 7) * 0.45
        card *= (1 - sh)[..., None]
        self.base = (card * (1 - m[..., None]) + paper * m[..., None]).astype(np.float32)
        return self

    def show_through(self, x, y, width, lines=8, size=20, strength=0.06):
        """writing on the back of the leaf, seen through it: reversed (so it reads left to right), soft, faint"""
        save, self.ink = self.ink, np.zeros_like(self.ink)
        load = self.load
        self.write(self.prose(lines * 9), x, y, width=width, size=size, mirror=False, max_lines=lines)
        ghost = blur(self.ink, 1.6) * strength
        self.ink, self.load = save, load
        self.base *= (1 - np.clip(ghost, 0, 0.3)[..., None] * (1 - INK_LIGHT * 0.9))

    # ------------------------------------------------------------ stroke engine
    def _prep(self, pts, width, ink, smooth=True, jitter=0.5, taper=(6, 18), step=1.3, nib=True, load=True):
        """resample a hand stroke, wobble it, give it nib width, pressure and an ink load -> (P, widths, values)"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 8)
        P = _resample(P, step)
        n = len(P)
        if n < 2:
            return P, np.array([width], np.float32), np.array([ink], np.float32)
        tg = np.gradient(P, axis=0)
        tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
        s = self._seed()
        if jitter:
            wob = fbm1d(n, max(4, 120 / step), 3, s) * jitter + fbm1d(n, max(2, 8 / step), 2, s + 1) * jitter * 0.18
            P = P + nrm * wob[:, None]
        sa = np.arange(n, dtype=np.float32) * step
        L = sa[-1]
        nibf = (0.66 + 0.42 * np.abs(np.sin(np.arctan2(tg[:, 1], tg[:, 0]) - self.nib))) if nib else 1.0
        env = smoothstep(0, max(1.0, min(taper[0], L * 0.3)), sa) * smoothstep(0, max(1.0, min(taper[1], L * 0.4)), L - sa)
        press = (0.42 + 0.58 * env) * (1 + 0.10 * fbm1d(n, max(4, 60 / step), 2, s + 2))
        w = (width * nibf * press).astype(np.float32)
        v = np.full(n, ink, np.float32)
        if load:
            v0 = self.load
            used = sa * self.use * max(width, 0.8) / 2.0
            v = ink * np.clip(v0 - used, 0.42, 1.0) * (0.92 + 0.1 * env)
            if self.fresh:                                  # just dipped: a small pool where the nib lands
                v = v * (1 + 0.45 * np.exp(-sa / 4.0)); w = w * (1 + 0.35 * np.exp(-sa / 3.0))
                self.fresh = False
            self.load = v0 - float(used[-1])
            if self.load < 0.58:
                self.load = self.rng.uniform(0.95, 1.05); self.fresh = self.rng.random() < 0.35
        return P, w, v.astype(np.float32)

    def _raster(self, strokes, ss=None):
        """strokes [(P, w, v)] -> (coverage, slices); drawn at ss x and box-filtered. Strokes of one call overwrite
        each other (no double density where a stroke meets itself); separate calls add up."""
        ss = ss or self.ss
        strokes = [s for s in strokes if len(s[0])]
        if not strokes: return None, None
        allp = np.concatenate([s[0] for s in strokes])
        pad = max(float(s[1].max()) for s in strokes) + 3
        sl = self._box(allp[:, 0].min() - pad, allp[:, 1].min() - pad, allp[:, 0].max() + pad, allp[:, 1].max() + pad)
        if sl is None: return None, None
        x0, y0 = sl[1].start, sl[0].start
        bw, bh = sl[1].stop - x0, sl[0].stop - y0
        im = Image.new('L', (bw * ss, bh * ss), 0)
        d = ImageDraw.Draw(im)
        off = np.array([x0, y0], np.float32)
        for P, w, v in strokes:
            Q = (P - off) * ss
            n = len(Q)
            if n == 1:
                r_ = w[0] * ss / 2
                d.ellipse([Q[0, 0] - r_, Q[0, 1] - r_, Q[0, 0] + r_, Q[0, 1] + r_], fill=int(255 * min(1, v[0])))
                continue
            for i in range(0, n - 1, 2):
                j = min(n - 1, i + 2)
                ww = float(w[i:j + 1].mean()) * ss
                vv = int(round(255 * float(np.clip(v[i:j + 1].mean(), 0, 1))))
                r_ = ww / 2
                d.ellipse([Q[i, 0] - r_, Q[i, 1] - r_, Q[i, 0] + r_, Q[i, 1] + r_], fill=vv)
                d.line([(float(q[0]), float(q[1])) for q in Q[i:j + 1]], fill=vv, width=max(1, int(round(ww))))
            r_ = w[-1] * ss / 2
            d.ellipse([Q[-1, 0] - r_, Q[-1, 1] - r_, Q[-1, 0] + r_, Q[-1, 1] + r_], fill=int(255 * np.clip(v[-1], 0, 1)))
        m = np.asarray(im.resize((bw, bh), Image.BOX), np.float32) / 255
        return m, sl

    def _deposit(self, strokes, medium='ink', strength=1.0):
        m, sl = self._raster(strokes)
        if sl is None: return
        if medium == 'ink':
            self.ink[sl] += m * strength
        elif medium == 'chalk':
            t = self.tooth[sl]
            thr = 1.0 - 1.35 * m
            dep = smoothstep(thr - 0.2, thr + 0.2, t)
            a = np.clip(m * 1.5, 0, 1) * (0.25 + 0.75 * dep) * strength
            self.chalk[sl] = 1 - (1 - self.chalk[sl]) * (1 - a)
        elif medium == 'lead':
            self.lead[sl] = np.maximum(self.lead[sl], m * strength)
        elif medium == 'stylus':
            self.groove[sl] = np.maximum(self.groove[sl], m * strength)

    # ------------------------------------------------------------ the quill
    def quill(self, pts, width=2.2, ink=1.0, smooth=True, jitter=0.5, taper=(6, 18)):
        """one pen stroke through pts"""
        self._deposit([self._prep(pts, width, ink, smooth, jitter, taper)])

    def quills(self, strokes, width=2.2, ink=1.0, smooth=True, jitter=0.5, taper=(6, 18)):
        """many pen strokes in one pass (they do not double up where they touch)"""
        self._deposit([self._prep(p, width, ink, smooth, jitter, taper) for p in strokes if len(p) > 1])

    def contour(self, pts, width=2.3, ink=1.0, searching=2, spread=2.2, smooth=True, closed=False):
        """a contour found the way Leonardo found it: `searching` light, slightly-off passes, then the line"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:2]])
        for k in range(searching):
            off = self.rng.normal(0, spread, 2)
            Q = P + off * np.linspace(0.4, 1.0, len(P))[:, None]
            Q = Q + fbm1d(len(P), max(3, len(P) / 3), 2, self._seed())[:, None] * spread * 0.8
            self.quill(Q, width * 0.55, ink * 0.42, smooth, 0.7)
        self.quill(P, width, ink, smooth)

    def ruled(self, p0, p1, width=1.7, ink=0.9, overshoot=4.0, medium='ink'):
        """a line drawn along a straight-edge: straight, ends not exactly on target"""
        p0, p1 = np.asarray(p0, np.float32), np.asarray(p1, np.float32)
        d = p1 - p0; d /= np.linalg.norm(d) + 1e-6
        a = p0 - d * self.rng.uniform(-overshoot * 0.5, overshoot)
        b = p1 + d * self.rng.uniform(-overshoot * 0.5, overshoot)
        self._deposit([self._prep([a, b], width, ink, False, 0.15, (3, 6), load=(medium == 'ink'))], medium)

    def dotted(self, pts, dash=7.0, gap=6.0, width=1.5, ink=0.8, dot_dash=False, smooth=True):
        """dashed (or dot-dash, for an axis) pen line along pts"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 8)
        P = _resample(P, 1.0)
        n = len(P)
        strokes, i, k = [], 0, 0
        while i < n - 1:
            ln = dash if (not dot_dash or k % 2 == 0) else 1.5
            j = min(n - 1, i + max(1, int(ln * self.rng.uniform(0.8, 1.2))))
            strokes.append(P[i:j + 1] if j > i else P[i:i + 1])
            i = j + int(gap * self.rng.uniform(0.8, 1.25)); k += 1
        self._deposit([self._prep(s, width, ink, False, 0.2, (1.5, 2.5)) for s in strokes])

    def arrow(self, pts, width=1.8, ink=0.95, head=11.0, smooth=True):
        """a pen arrow along pts (head at the last point)"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 10)
        self.quill(P, width, ink, False)
        d = P[-1] - P[-4 if len(P) > 4 else 0]; d /= np.linalg.norm(d) + 1e-6
        for sgn in (1, -1):
            a = np.deg2rad(150 * sgn)
            v = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)])
            self.quill([P[-1], P[-1] + v * head * 0.55, P[-1] + v * head], width * 0.9, ink, True, 0.2, (2, 6))

    # ------------------------------------------------------------ hatching
    def hatch(self, mask, shade=1.0, angle=55.0, spacing=5.2, levels=(0.2, 0.48), cross=0.76, cross_angle=-38.0,
              width=1.1, ink=0.72, length=(22, 46), bow=0.035, over=1.6, jitter=0.1, noise=0.08, origin=(0, 0),
              medium='ink'):
        """parallel hatching inside `mask` (0..1); shade (array like mask, or a number) 0 lit .. 1 dark.
        Lines at `angle` (55 = the left-hander's '\\'); each entry of `levels` interleaves another set of lines
        where shade exceeds it; above `cross` a second set at `cross_angle` crosses them.
        A hand hatches in bands: a row of parallel strokes of about one length, then the next row, so long
        runs are cut where the band edges fall (staggered a little from line to line, small gaps/overlaps)."""
        M = np.asarray(mask, np.float32)
        ys, xs = np.nonzero(M > 0.5)
        if len(xs) < 4: return
        S = np.broadcast_to(np.asarray(shade, np.float32), M.shape) if np.ndim(shade) == 0 else np.asarray(shade, np.float32)
        by0, by1, bx0, bx1 = max(0, ys.min() - 2), min(M.shape[0], ys.max() + 3), max(0, xs.min() - 2), min(M.shape[1], xs.max() + 3)
        M, S = M[by0:by1, bx0:bx1], S[by0:by1, bx0:bx1]
        ox, oy = origin[0] + bx0, origin[1] + by0
        xs, ys = xs - bx0, ys - by0
        h, w = M.shape
        N = noise2d(h, w, 22, 2, self._seed()) - 0.5 if h > 2 and w > 2 else np.zeros_like(M)
        cx, cy = xs.mean(), ys.mean()
        corners = np.array([[xs.min(), ys.min()], [xs.max(), ys.min()], [xs.min(), ys.max()], [xs.max(), ys.max()]], np.float32) - [cx, cy]
        r = self.rng
        layers = [(angle, lev, k / max(1, len(levels)), spacing) for k, lev in enumerate(levels)]
        if cross is not None: layers.append((cross_angle, cross, 0.0, spacing * 1.05))
        for ang, lev, phase, sp in layers:
            a = np.deg2rad(ang)
            d = np.array([np.cos(a), np.sin(a)], np.float32)
            nv = np.array([-np.sin(a), np.cos(a)], np.float32)
            on, od = corners @ nv, corners @ d
            ts = np.arange(od.min() - 3, od.max() + 3, 1.0, dtype=np.float32)
            Lb = r.uniform(*length)
            cut0 = od.min() - 3 + r.uniform(0, Lb)
            wph = r.uniform(0, 2 * np.pi)
            strokes = []
            o = on.min() + phase * sp
            while o < on.max():
                px = cx + nv[0] * o + d[0] * ts; py = cy + nv[1] * o + d[1] * ts
                ix, iy = np.round(px).astype(int), np.round(py).astype(int)
                ok = (ix >= 0) & (iy >= 0) & (ix < w) & (iy < h)
                inside = np.zeros(len(ts), bool)
                ii, jj = iy[ok], ix[ok]
                inside[ok] = (M[ii, jj] > 0.5) & (S[ii, jj] + noise * 2 * N[ii, jj] > lev)
                edges = np.diff(np.concatenate([[0], inside.astype(np.int8), [0]]))
                cb = cut0 + 0.2 * Lb * np.sin(o / 19.0 + wph) + r.normal(0, 1.2)
                for s0, s1 in zip(np.nonzero(edges == 1)[0], np.nonzero(edges == -1)[0]):
                    if s1 - s0 < 3: continue
                    t0 = ts[s0] - r.uniform(-over * 0.6, over)
                    t1 = ts[s1 - 1] + r.uniform(-over * 0.8, over)
                    k0 = int(np.ceil((t0 - cb) / Lb))
                    cuts = [cb + Lb * k for k in range(k0, k0 + int((t1 - t0) / Lb) + 2) if t0 + Lb * 0.4 < cb + Lb * k < t1 - Lb * 0.4]
                    knots = [t0] + cuts + [t1]
                    for i in range(len(knots) - 1):
                        p_ = knots[i] + (r.uniform(0.3, 1.8) if i > 0 else 0)
                        e_ = knots[i + 1] - (r.uniform(-0.6, 1.2) if i < len(knots) - 2 else 0)
                        if e_ - p_ < 2.5: continue
                        p0 = np.array([cx, cy]) + nv * o + d * p_
                        p1 = np.array([cx, cy]) + nv * o + d * e_
                        mid = (p0 + p1) / 2 + nv * (e_ - p_) * bow * r.uniform(0.7, 1.3)
                        strokes.append(np.array([p0, mid, p1], np.float32) + [ox, oy])
                o += sp * r.uniform(0.88, 1.12)
            if not strokes: continue
            if medium == 'ink':
                self._deposit([self._prep(s, width, ink, True, jitter, (3, 7)) for s in strokes])
            else:
                self._deposit([self._prep(s, width, ink, True, jitter, (4, 8), nib=False, load=False) for s in strokes], medium)

    # ------------------------------------------------------------ red chalk, leadpoint, stylus
    def sanguine(self, pts, width=3.4, pressure=0.7, smooth=True, jitter=0.6):
        """one red-chalk stroke (pressure decides how deep into the grain it goes)"""
        self._deposit([self._prep(pts, width, pressure, smooth, jitter, (8, 16), nib=False, load=False)], 'chalk')

    def sanguines(self, strokes, width=3.4, pressure=0.7, smooth=True, jitter=0.6):
        self._deposit([self._prep(p, width, pressure, smooth, jitter, (8, 16), nib=False, load=False) for p in strokes if len(p) > 1], 'chalk')

    def rub(self, mask, amount=0.25, soften=4.0, origin=(0, 0)):
        """a finger rubbed over the chalk: a soft tone inside mask, the chalk lines blurred into it"""
        M = np.asarray(mask, np.float32)
        h, w = M.shape
        sl = self._box(origin[0], origin[1], origin[0] + w, origin[1] + h)
        if sl is None: return
        M = M[:sl[0].stop - sl[0].start, :sl[1].stop - sl[1].start]
        sm = blur(self.chalk[sl], soften)
        tone = blur(M, soften) * amount * (0.7 + 0.6 * self.tooth[sl])
        self.chalk[sl] = np.clip(np.maximum(self.chalk[sl] * (1 - 0.35 * M) + sm * 0.35 * M, tone), 0, 1)

    def leadpoint(self, pts, width=1.1, strength=0.5, smooth=True, jitter=0.8):
        """faint grey underdrawing (searching lines under the ink)"""
        self._deposit([self._prep(pts, width, strength, smooth, jitter, (6, 10), nib=False, load=False)], 'lead')

    def incise(self, pts, depth=1.0, width=1.5, smooth=True):
        """a blind line pressed with a stylus: no colour, only a groove that catches the raking light"""
        self._deposit([self._prep(pts, width, depth, smooth, 0.15, (4, 6), nib=False, load=False)], 'stylus')

    def prick(self, x, y, r=1.6):
        """the hole a compass point leaves at a centre"""
        sl = self._box(x - 6, y - 6, x + 7, y + 7)
        if sl is None: return
        yy, xx = np.mgrid[sl[0], sl[1]].astype(np.float32)
        d2 = (xx - x) ** 2 + (yy - y) ** 2
        self.groove[sl] = np.maximum(self.groove[sl], 2.6 * np.exp(-d2 / (2 * r * r)))
        self.ink[sl] += 0.5 * np.exp(-d2 / (2 * (r * 0.6) ** 2))

    def compass(self, cx, cy, r, a0=0.0, a1=360.0, depth=0.9, prick=True):
        """a circle (or arc) scored with the compass, centre pricked"""
        self.incise(self.arc(cx, cy, r, a0, a1), depth, 1.4, smooth=False)
        if prick: self.prick(cx, cy)

    # ------------------------------------------------------------ shapes and shade fields
    @staticmethod
    def arc(cx, cy, rx, a0=0.0, a1=360.0, ry=None, rot=0.0, step=None):
        """points on an (elliptic) arc, screen degrees (clockwise from +x)"""
        ry = rx if ry is None else ry
        n = max(8, int(abs(a1 - a0) / 360 * 2 * np.pi * max(rx, ry) / (step or 3.0)))
        t = np.deg2rad(np.linspace(a0, a1, n))
        x, y = np.cos(t) * rx, np.sin(t) * ry
        c, s = np.cos(np.deg2rad(rot)), np.sin(np.deg2rad(rot))
        return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)

    def _grid(self):
        if not hasattr(self, '_yx'):
            self._yx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
        return self._yx[0], self._yx[1]

    def poly_mask(self, pts, ss=2):
        return polygon_mask(self.H, self.W, pts, ss)

    def disc_mask(self, cx, cy, r):
        sl = self._box(cx - r - 2, cy - r - 2, cx + r + 3, cy + r + 3)
        m = np.zeros((self.H, self.W), np.float32)
        yy, xx = np.mgrid[sl[0], sl[1]].astype(np.float32)
        m[sl] = np.clip(r + 0.5 - np.hypot(xx - cx, yy - cy), 0, 1)
        return m

    def radial_shade(self, cx, cy, r, light=(-0.55, -0.6)):
        """shade of a sphere/disc lit from `light` (screen direction): 0 lit .. 1 dark"""
        YY, XX = self._grid()
        ux, uy = (XX - cx) / r, (YY - cy) / r
        l = np.asarray(light, np.float32) / np.linalg.norm(light)
        return np.clip(0.42 + 0.5 * (ux * -l[0] + uy * -l[1]) + 0.22 * (ux * ux + uy * uy), 0, 1)

    def between(self, a0, a1, b0, b1):
        """0 on the line a0-a1 .. 1 on the line b0-b1 (e.g. across a membrane panel from one rib to the next)"""
        YY, XX = self._grid()

        def dist(p, q):
            p, q = np.asarray(p, np.float32), np.asarray(q, np.float32)
            d = q - p; d /= np.linalg.norm(d) + 1e-6
            return np.abs((XX - p[0]) * d[1] - (YY - p[1]) * d[0])
        da, db = dist(a0, a1), dist(b0, b1)
        return da / (da + db + 1e-6)

    # ------------------------------------------------------------ objects Leonardo drew again and again
    def cane(self, p0, p1, w0=6.0, w1=3.0, bend=0.0, lashings=(), width=1.7, ink=1.0, cap=True):
        """a cane / wooden rod seen from the side: two converging pen lines (w0 at p0, w1 at p1), optional
        bend (px, sideways), cord lashings at fractions along it. Returns its outline (for masking hatching)."""
        from core import curve
        C = curve(p0, p1, bend, 40)
        tg = np.gradient(C, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nv = np.stack([-tg[:, 1], tg[:, 0]], 1)
        t = np.linspace(0, 1, len(C))[:, None]
        hw = (w0 + (w1 - w0) * t) / 2
        A, B = C + nv * hw, C - nv * hw
        self.quills([A, B], width, ink, True, 0.35, (5, 12))
        if cap:
            self.quill(self.arc(C[0, 0], C[0, 1], w0 / 2, 0, 360, step=1.0)[::-1], width * 0.8, ink * 0.9, False, 0.2, (2, 3))
        for f in lashings:
            i = int(np.clip(f, 0, 1) * (len(C) - 1))
            for k in range(3):
                q = C[min(len(C) - 1, i + k * 2)] + tg[i] * k * 0.5
                h_ = hw[i, 0] + 1.6
                self.quill([q + nv[i] * h_ - tg[i] * 1.5, q - nv[i] * h_ + tg[i] * 1.5], width * 0.7, ink * 0.9, False, 0.1, (1, 2))
        return np.vstack([A, B[::-1]])

    def feather(self, base, angle, length, width, medium='chalk', curl=0.06, lead=0.42, pressure=0.75, rachis=True,
                line=None, side=1, overlapped=False):
        """a flight feather: curved rachis, narrow leading vane, broad trailing vane, rounded tip.
        medium 'chalk' (red chalk) or 'ink'; side=+1/-1 puts the broad vane on the left/right of the rachis (as seen
        walking from base to tip); overlapped=True draws only what shows in a fanned wing (the broad vane's edge,
        the tip and the end of the narrow vane). Returns (outline polygon, rachis, edge of the broad vane)."""
        from core import curve
        a = np.deg2rad(angle)
        tip = (base[0] + np.cos(a) * length, base[1] + np.sin(a) * length)
        C = curve(base, tip, length * curl, 48)
        tg = np.gradient(C, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nv = np.stack([-tg[:, 1], tg[:, 0]], 1) * side
        t = np.linspace(0, 1, len(C))
        rise = np.clip(t / 0.2, 0, 1) ** 0.55                       # widens quickly from the bare quill
        tipr = np.where(t > 0.7, np.sqrt(np.clip(1 - ((t - 0.7) / 0.3) ** 2, 0, 1)), 1.0)   # rounded end
        prof = width * rise * tipr * (1 - 0.18 * t)
        trail = C + nv * prof[:, None]
        lead_ = C - nv * (prof * lead)[:, None]
        poly = np.vstack([trail, lead_[::-1]])
        if overlapped:
            outline = [np.vstack([trail[int(len(C) * 0.18):], lead_[::-1][:int(len(C) * 0.4)]])]
        else:
            outline = [trail[3:], lead_[3:]]
        if medium == 'chalk':
            lw = line or 2.4
            self.sanguines(outline, lw, pressure, True, 0.5)
            if rachis: self.sanguine(C[:-4], lw * 0.8, pressure * 0.8, True, 0.3)
        else:
            lw = line or 1.5
            self.quills(outline, lw, 0.9, True, 0.35)
            if rachis: self.quill(C[:-4], lw * 0.75, 0.75, True, 0.25)
        return poly, C, trail

    def bird(self, x, y, size=24.0, phase=0.0, ink=0.85, width=1.6):
        """one of Leonardo's little birds seen from behind, a few quick strokes: phase 0 wings level, pi/2 fully
        up, -pi/2 fully down; the wing bends at the wrist and its tip trails behind the beat"""
        up = np.sin(phase)
        lag = np.cos(phase)
        s_ = size
        strokes = []
        for sgn in (-1, 1):
            root = (x + sgn * s_ * 0.07, y - s_ * 0.02)
            wrist = (x + sgn * s_ * 0.48, y - up * s_ * 0.42 - lag * s_ * 0.10)
            tip = (x + sgn * s_ * 1.0, y - up * s_ * 0.66 + lag * s_ * 0.08 * (1 if up >= 0 else -1))
            strokes.append([root, wrist, tip])
            fk = (tip[0] - sgn * s_ * 0.16, tip[1] + s_ * 0.12)              # primaries spread at the tip
            strokes.append([fk, (tip[0] - sgn * s_ * 0.05, tip[1] + s_ * 0.05), tip])
        self.quills(strokes, width, ink, True, 0.15, (2, 5))
        self.quill([(x, y - s_ * 0.14), (x + s_ * 0.01, y + s_ * 0.06), (x, y + s_ * 0.24)], width * 2.0, ink, True, 0.05, (3, 4))
        self.quills([[(x, y + s_ * 0.2), (x - s_ * 0.1, y + s_ * 0.36)], [(x, y + s_ * 0.2), (x + s_ * 0.1, y + s_ * 0.36)],
                     [(x, y + s_ * 0.2), (x, y + s_ * 0.38)]], width * 0.8, ink * 0.9, False, 0.05, (1, 2))

    # ------------------------------------------------------------ writing
    def _hand(self, size):
        size = int(round(size))
        if size in self._fonts: return self._fonts[size]
        env = os.environ.get('INKPAINT_FONT_CHANCERY')
        cands = ([(env, 0)] if env else []) + [('/System/Library/Fonts/Supplemental/Apple Chancery.ttf', 0),
                                               ('/usr/share/fonts/**/z003*.[ot]tf', 0), ('/usr/share/fonts/**/URWChancery*.[ot]tf', 0),
                                               ('C:/Windows/Fonts/segoesc.ttf', 0), ('/System/Library/Fonts/Supplemental/SnellRoundhand.ttc', 0)]
        f = None
        for pat, idx in cands:
            hits = glob.glob(pat, recursive=True) if pat else []
            if hits:
                try:
                    f = ImageFont.truetype(hits[0], size, index=idx); break
                except OSError:
                    pass
        if f is None: f = load_font('script', size)
        self._fonts[size] = f
        return f

    def prose(self, n=30, terms=0.18, capital=True):
        """n pseudo-Italian words: real little words, invented ones, a few engineering terms"""
        r = self.rng
        out = []
        for i in range(n):
            u = r.random()
            if u < 0.34: w = _SMALL[r.integers(len(_SMALL))]
            elif u < 0.34 + terms: w = _TERMS[r.integers(len(_TERMS))]
            else: w = ''.join(_SYL[r.integers(len(_SYL))] for _ in range(int(r.integers(2, 4))))
            out.append(w)
        if capital and out: out[0] = out[0][:1].upper() + out[0][1:]
        return ' '.join(out)

    def _line_mask(self, s, size):
        """one handwritten line (left to right) -> (mask, baseline y in mask)"""
        r = self.rng
        f = self._hand(size)
        est = int(f.getlength(s) * 1.12 + size * 2)
        h = int(size * 2.4)
        base = int(size * 1.5)
        im = Image.new('L', (est, h), 0)
        d = ImageDraw.Draw(im)
        x = size * 0.5
        drift = fbm1d(max(len(s), 2), 9, 2, self._seed()) * size * 0.07
        slope = r.normal(0, 0.006)
        for i, ch in enumerate(s):
            fs = self._hand(size * r.uniform(0.93, 1.07)) if ch != ' ' else f
            y = base + drift[i] + slope * x + r.normal(0, 0.35)
            d.text((x, y), ch, font=fs, fill=255, anchor='ls')
            x += fs.getlength(ch) * r.uniform(0.96, 1.05) + (r.uniform(0.0, 2.2) if ch == ' ' else 0)
        x = int(min(est, x + size * 0.3))
        return np.asarray(im, np.float32)[:, :x] / 255, base, x

    def write(self, text, x, y, width=420, size=20, leading=1.32, mirror=True, ink=0.9, max_lines=None, indent=None):
        """a block of handwriting. mirror=True: Leonardo's right-to-left mirror writing, x is the RIGHT margin
        where every line starts (lines end ragged on the left); mirror=False: normal, x is the left margin.
        `indent(i)` may return extra px to keep line i clear of a drawing. Returns the y below the block."""
        words = text.split() if isinstance(text, str) else None
        lines = []
        if words is not None:
            f = self._hand(size)
            cur = ''
            k = 0
            while words:
                lim = width - (indent(len(lines)) if indent else 0)
                t = (cur + ' ' + words[0]).strip()
                if f.getlength(t) * 1.03 <= lim or not cur:
                    cur = t; words.pop(0)
                else:
                    lines.append(cur); cur = ''
                    if max_lines and len(lines) >= max_lines: break
            if cur and not (max_lines and len(lines) >= max_lines): lines.append(cur)
        else:
            lines = list(text)
        yy = y
        for i, s in enumerate(lines):
            m, base, wl = self._line_mask(s, size)
            # the pen's load along the line (in writing order), re-dipped when it runs low
            n = m.shape[1]
            prof = np.empty(n, np.float32)
            for j in range(n):
                prof[j] = self.load
                self.load -= self.use * 0.55
                if self.load < 0.6: self.load = self.rng.uniform(0.95, 1.05)
            dens = m * (ink * (0.55 + 0.45 * np.clip(prof, 0, 1)))[None, :]
            ind = indent(i) if indent else 0
            if mirror:
                dens = dens[:, ::-1]
                x0 = int(round(x - ind - n + self.rng.normal(0, 1.5)))
            else:
                x0 = int(round(x + ind + self.rng.normal(0, 1.5)))
            y0 = int(round(yy - base))
            sl = self._box(x0, y0, x0 + n, y0 + dens.shape[0])
            if sl is not None:
                dy, dx = sl[0].start - y0, sl[1].start - x0
                self.ink[sl] += dens[dy:dy + sl[0].stop - sl[0].start, dx:dx + sl[1].stop - sl[1].start]
            yy += size * leading
        return yy

    def label(self, s, x, y, size=22, ink=0.95, mirror=True):
        """a short label (a point letter, a number) centred on x, baseline y"""
        m, base, n = self._line_mask(s, size)
        dens = m * ink * (0.85 + 0.15 * self.load)
        if mirror: dens = dens[:, ::-1]
        x0, y0 = int(round(x - n / 2)), int(round(y - base))
        sl = self._box(x0, y0, x0 + n, y0 + dens.shape[0])
        if sl is not None:
            dy, dx = sl[0].start - y0, sl[1].start - x0
            self.ink[sl] += dens[dy:dy + sl[0].stop - sl[0].start, dx:dx + sl[1].stop - sl[1].start]

    # ------------------------------------------------------------ accidents
    def blot(self, x, y, r=6.0, ink=1.4, drops=5):
        """an ink drop: irregular, a darker tide rim where it dried, a few satellite drops"""
        sl = self._box(x - r * 4 - 4, y - r * 4 - 4, x + r * 4 + 5, y + r * 4 + 5)
        if sl is None: return
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        ox, oy = sl[1].start, sl[0].start
        pts = blob_pts(x - ox, y - oy, r, r * self.rng.uniform(0.7, 1.0), 0.22, 60, self._seed(), self.rng.uniform(0, 3))
        m = polygon_mask(h, w, pts, 3)
        for _ in range(drops):
            a, d = self.rng.uniform(0, 2 * np.pi), r * self.rng.uniform(1.3, 3.4)
            rr = self.rng.uniform(0.5, max(0.8, r * 0.22))
            m = np.maximum(m, polygon_mask(h, w, blob_pts(x - ox + np.cos(a) * d, y - oy + np.sin(a) * d, rr, rr, 0.2, 14, self._seed()), 3))
        rim = np.clip(m - blur(m, max(0.8, r * 0.16)), 0, 1)
        self.ink[sl] += (blur(m, 0.5) * 0.85 + rim * 1.1) * ink

    def spatter(self, x, y, n=12, spread=30.0, ink=1.0):
        r = self.rng
        for _ in range(n):
            px, py = x + r.normal(0, spread), y + r.normal(0, spread * 0.7)
            rr = r.uniform(0.5, 1.6)
            sl = self._box(px - 4, py - 4, px + 5, py + 5)
            if sl is None: continue
            yy, xx = np.mgrid[sl[0], sl[1]].astype(np.float32)
            self.ink[sl] += ink * np.clip(rr + 0.5 - np.hypot(xx - px, yy - py), 0, 1)

    def strike(self, x0, y0, x1, y1, n=5, width=2.0, ink=1.0):
        """strike a rejected sketch out: a few fast diagonal strokes across it, then a cross"""
        r = self.rng
        strokes = []
        for k in range(n):
            t = (k + 0.5) / n
            a = (x0 + (x1 - x0) * (t - 0.35), y0 - 4)
            b = (x0 + (x1 - x0) * (t + 0.35), y1 + 4)
            mid = ((a[0] + b[0]) / 2 + r.normal(0, 3), (a[1] + b[1]) / 2)
            strokes.append([a, mid, b])
        strokes.append([(x0, y0), ((x0 + x1) / 2 + 3, (y0 + y1) / 2 - 2), (x1, y1)])
        strokes.append([(x1, y0), ((x0 + x1) / 2 - 2, (y0 + y1) / 2 + 3), (x0, y1)])
        for s in strokes: self.quill(s, width, ink, True, 0.6, (3, 12))

    # ------------------------------------------------------------ machine parts (pen renderer)
    def solid(self, mesh, cam, width=2.1, ink=1.0, crease=30.0, light=(-0.55, 0.45, 0.70), hatch=None, erase=True,
              hatch_groups=None, edge_ink=None):
        """draw a mesh the way a draughtsman would: hidden lines dropped, feature edges inked, faces hatched by tone.
        hatch: dict of hatch() keyword overrides (applies to every group); hatch_groups: {group prefix: dict}
        for per-surface overrides (angle, levels, ...; None to leave a surface white)."""
        V = mesh.V
        S2, Z = cam.project(V)
        F = mesh.F
        nf = len(F)
        Lc = np.asarray(light, np.float32); Lc /= np.linalg.norm(Lc)
        # face normals (Newell) in camera space: (right, toward, up)
        Nw = np.zeros((nf, 3), np.float32)
        for i, f in enumerate(F):
            P = V[f]; Q = np.roll(P, -1, 0)
            Nw[i] = [np.sum((P[:, 1] - Q[:, 1]) * (P[:, 2] + Q[:, 2])), np.sum((P[:, 2] - Q[:, 2]) * (P[:, 0] + Q[:, 0])),
                     np.sum((P[:, 0] - Q[:, 0]) * (P[:, 1] + Q[:, 1]))]
        Nw /= np.linalg.norm(Nw, axis=1, keepdims=True) + 1e-9
        Nc = cam.cam(Nw)
        front = Nc[:, 1] > 1e-3
        lam = np.clip(Nc @ Lc, 0, 1)
        shade_f = np.clip(1.0 - lam * 1.12, 0, 1) ** 0.9
        pad = 8
        sl = self._box(S2[:, 0].min() - pad, S2[:, 1].min() - pad, S2[:, 0].max() + pad, S2[:, 1].max() + pad)
        if sl is None: return
        x0, y0 = sl[1].start, sl[0].start
        h, w = sl[0].stop - y0, sl[1].stop - x0
        zb = np.full((h, w), np.inf, np.float32)
        fid = np.full((h, w), -1, np.int32)
        cov = Image.new('L', (w * 2, h * 2), 0)
        dc = ImageDraw.Draw(cov)
        for i in np.nonzero(front)[0]:
            P2 = S2[F[i]] - [x0, y0]
            bx0, by0 = max(0, int(P2[:, 0].min()) - 1), max(0, int(P2[:, 1].min()) - 1)
            bx1, by1 = min(w, int(P2[:, 0].max()) + 2), min(h, int(P2[:, 1].max()) + 2)
            if bx1 <= bx0 or by1 <= by0: continue
            im = Image.new('L', (bx1 - bx0, by1 - by0), 0)
            ImageDraw.Draw(im).polygon([(float(p[0] - bx0 - 0.5), float(p[1] - by0 - 0.5)) for p in P2], fill=1, outline=1)
            m = np.asarray(im, bool)
            dc.polygon([(float(p[0] * 2), float(p[1] * 2)) for p in P2], fill=255)
            if not m.any(): continue
            A = np.c_[P2, np.ones(len(P2))]
            coef, *_ = np.linalg.lstsq(A, Z[F[i]], rcond=None)
            yy, xx = np.mgrid[by0:by1, bx0:bx1].astype(np.float32)
            dep = coef[0] * xx + coef[1] * yy + coef[2]
            sub_z = zb[by0:by1, bx0:bx1]; sub_f = fid[by0:by1, bx0:bx1]
            upd = m & (dep < sub_z)
            sub_z[upd] = dep[upd]; sub_f[upd] = i
        sil = np.asarray(cov.resize((w, h), Image.BOX), np.float32) / 255
        if erase:
            self.ink[sl] *= 1 - sil
            self.lead[sl] *= 1 - sil
        # hatch each surface group with its own tone field (smoothed inside the group)
        groups = {}
        for i, g in enumerate(mesh.G): groups.setdefault(g, []).append(i)
        base_h = dict(angle=55.0, spacing=4.6, levels=(0.22, 0.5), cross=0.76, width=1.05, ink=0.7, length=(10, 40))
        if hatch: base_h.update(hatch)
        for g, idx in groups.items():
            kw = dict(base_h)
            skip = False
            if hatch_groups:
                for pre, o in hatch_groups.items():
                    if g.startswith(pre) or g.split('.')[-1].startswith(pre):
                        if o is None: skip = True
                        else: kw.update(o)
            if skip: continue
            reg = np.isin(fid, idx)
            if reg.sum() < 12: continue
            sh = np.zeros((h, w), np.float32)
            lut = np.zeros(nf + 1, np.float32); lut[:nf] = shade_f
            sh[reg] = lut[fid[reg]]
            regf = reg.astype(np.float32)
            num = blur(sh * regf, 2.0); den = blur(regf, 2.0) + 1e-4
            shs = np.where(reg, num / den, 0)
            self.hatch(regf, shs, origin=(x0, y0), **kw)
        # feature edges
        emap = {}
        for i, f in enumerate(F):
            for k in range(len(f)):
                a, b = f[k], f[(k + 1) % len(f)]
                emap.setdefault((min(a, b), max(a, b)), []).append(i)
        cosc = np.cos(np.deg2rad(crease))
        draw = {}
        for (a, b), own in emap.items():
            vis = [o for o in own if front[o]]
            if not vis: continue
            if len(own) == 1: kind = 1.0
            elif len(vis) < len(own): kind = 1.0                       # silhouette
            elif float(np.dot(Nw[own[0]], Nw[own[1]])) < cosc: kind = 0.72   # crease
            else: continue
            draw[(a, b)] = kind
        # chain edges into long polylines (degree-2 vertices of the same kind are joined)
        adj = {}
        for (a, b), k in draw.items():
            adj.setdefault(a, []).append((b, k)); adj.setdefault(b, []).append((a, k))
        used = set()
        chains = []
        for (a, b), k in draw.items():
            if (a, b) in used: continue
            used.add((a, b))
            path = [a, b]
            for end in (1, 0):
                while True:
                    v = path[-1] if end else path[0]
                    prev = path[-2] if end else path[1]
                    nxt = [(u, kk) for u, kk in adj[v] if (min(u, v), max(u, v)) not in used and kk == k]
                    if len(adj[v]) != 2 or not nxt: break
                    u = nxt[0][0]
                    used.add((min(u, v), max(u, v)))
                    if end: path.append(u)
                    else: path.insert(0, u)
                    if u == path[0 if end else -1]: break
            chains.append((path, k))
        zmax = zb.copy()
        zmax[~np.isfinite(zmax)] = 1e9
        zmax = np.maximum.reduce([shift(zmax, dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)])
        tol = 1.5
        strokes_hi, strokes_lo = [], []
        for path, k in chains:
            P = S2[path]; Zp = Z[path]
            seg = np.hypot(*np.diff(P, axis=0).T)
            sacc = np.concatenate([[0], np.cumsum(seg)])
            if sacc[-1] < 1.5: continue
            n = int(sacc[-1]) + 2
            t = np.linspace(0, sacc[-1], n)
            px = np.interp(t, sacc, P[:, 0]); py = np.interp(t, sacc, P[:, 1]); pz = np.interp(t, sacc, Zp)
            ix = np.clip(np.round(px - x0).astype(int), 0, w - 1); iy = np.clip(np.round(py - y0).astype(int), 0, h - 1)
            vis = pz <= zmax[iy, ix] + tol
            e = np.diff(np.concatenate([[0], vis.astype(np.int8), [0]]))
            for s0, s1 in zip(np.nonzero(e == 1)[0], np.nonzero(e == -1)[0]):
                if s1 - s0 < 3: continue
                run = np.stack([px[s0:s1], py[s0:s1]], 1)
                # long runs are drawn as several pen strokes, as a hand would
                L = s1 - s0
                cut = [0]
                while cut[-1] < L - 1:
                    cut.append(min(L - 1, cut[-1] + int(self.rng.uniform(90, 220))))
                for c0, c1 in zip(cut[:-1], cut[1:]):
                    (strokes_hi if k >= 1 else strokes_lo).append(run[max(0, c0 - 2):c1 + 1])
        ei = ink if edge_ink is None else edge_ink
        self._deposit([self._prep(s, width, ei, False, 0.35, (4, 8)) for s in strokes_hi])
        self._deposit([self._prep(s, width * 0.72, ei * 0.85, False, 0.35, (4, 8)) for s in strokes_lo])

    # ------------------------------------------------------------ output
    def composite(self):
        img = self.base.copy()
        m = self.mask
        if self.groove.any():                                   # raking light on the stylus grooves
            g = blur(self.groove, 0.7)
            gy, gx = np.gradient(g)
            lit = (gx * -0.6 + gy * -0.7)
            img *= (1 + np.clip(lit * 0.55, -0.12, 0.12) * m - 0.03 * np.clip(g, 0, 1) * m)[..., None]
        if self.lead.any():
            a = np.clip(self.lead * 0.5, 0, 0.55) * m
            img *= 1 - a[..., None] * (1 - _c(LEADPOINT))
        if self.chalk.any():
            a = np.clip(self.chalk, 0, 1) * 0.9 * m
            img *= 1 - a[..., None] * (1 - _c(SANGUINE))
        D = self.ink * (0.8 + 0.4 * self.fib) * m
        halo = np.clip(blur(D, 1.8), 0, 1.5)
        img *= 1 - (0.11 * halo)[..., None] * (1 - INK_HALO)
        a = 1 - np.exp(-1.75 * D)
        k = smoothstep(0.25, 0.97, a)[..., None]
        col = INK_LIGHT * (1 - k) + INK_DARK * k
        img *= 1 - a[..., None] * (1 - col)
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
