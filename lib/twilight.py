"""twilight — 暮色绘本 / Twilight Storybook: a dreamy dusk picture-book page full of miniature detail (numpy + Pillow only).

The look: a tender, wistful picture-book illustration of the hour when day turns to night. A big pastel dusk sky
(lavender at the top, rose and peach in the middle, warm gold at the horizon) with soft, flat-bottomed cloud bands
and a low pale sun; on one side the sky gives way to a deep night with a field of stars, a Milky Way band with its
dark rift, a crescent moon and a shooting star. Below, rolling hills in soft stacked pastel stripes (patchwork
fields, crop rows, tiny round trees) and in front a meadow made of thousands of tiny wildflowers -- specks near
the crest, then small rosettes, then big daisies, cornflowers, poppies, cosmos and lupins at the bottom edge --
with grass ticks between them. Very small, flat, cute characters. Over it all the language of a scientific plate:
a circular magnified "detail a" inset drawn in fine ink linework with hatching, dimension ticks and labels, and
tiny lowercase handwritten captions in grey. Soft grain, a gentle vignette, a torn paper edge.

Physical model
  dusk sky    A vertical gradient through six stops measured against the horizon row. The stop positions are
              warped by a horizontally stretched low-frequency noise, so the colours lie in soft horizontal layers,
              not a ruler-straight ramp, and a fine mottle (a few percent) gives the airbrushed paper softness.
              Clouds are lens-shaped bands: a lumpy, soft top that fades out and a flatter, sharper bottom, denser
              (darker) toward the bottom, half transparent; thin pale light streaks lie under them. The sun is a pale
              disc with a two-scale glow, painted before the hills so they cut it.
  night       `night_split()` defines a field N (0 dusk .. 1 night) across the canvas from a wandering boundary line
              with a wide, feathered transition. Night paint (gradient, Milky Way, stars, moon) is laid with N as its
              alpha, so stars thin out and fade across the boundary instead of stopping at a line; near the boundary
              the night colour leans indigo, so dusk peach -> mauve -> indigo -> black. Every later "lit" paint
              call (hills, meadow, figures) is shaded by the same field: the colour is pulled toward a desaturated,
              moonlit blue by a linear 3x3 grade (luminance desaturation then a cool tint) weighted by N, so a
              white daisy on the night side becomes a pale moonlit blue and the grass a dark slate. Emissive things
              (stars, fireflies, the lantern, the shooting star) and the plate overlay are painted unlit.
  milky way   An analytic band between two points with a gentle bend and a wandering centre; its density is a
              gaussian across the band times two scales of cloudy noise; a narrower dark rift wanders inside it; a few
              thousand faint stars are sampled with probability proportional to the band density.
  stars       Positions uniform, brightness from a power law (many faint, few bright), a few warm and a few blue.
              Every star is splatted with sub-pixel accuracy: a disc-coverage kernel for big stars, a mass-preserving
              gaussian for sub-pixel ones, accumulated with bincount. The brightest get a little glow; `sparkle()` adds
              the four-point cross with long tapered rays and short diagonals.
  hills       Distant ranges are filled ridges (analytic anti-aliased edge per column) going lighter toward their base
              (mist pooled in the valleys). Striped hills are layered bands that follow the ridge, getting wider toward
              the viewer (perspective); each band is cut into slanted patchwork fields of pastel colours, some fields
              carry fine crop rows parallel to the band, there are thin darker hedge lines between bands and fields and
              a pale rim of light along the crest. `trees()` puts tiny round trees (shadow, trunk, crown, highlight).
  meadow      The ground is a sage-to-olive gradient with mottle and fine flecks, and a lit rim along the crest that
              goes gold -> silver across the night boundary. Plants are sampled by rejection so that the screen
              coverage follows perspective: size grows with depth below the crest (size ~ t^1.9), density ~ coverage /
              (pi size^2), so the crest is thousands of specks and the bottom a few dozen big flowers. The species mix
              drifts across the meadow with low-frequency noise (patches of daisies, a blue drift of cornflowers). By
              size a flower is a speck (one dot), a rosette with an eye, or a full head: daisy (12-16 elongated
              petals, yellow eye), cornflower (toothed wedge florets), poppy (four cupped round petals, dark eye with
              stamens), cosmos (notched petals), marigold (two rings), buttercup, lupin spike (florets shrinking up the
              spike), forget-me-not cluster -- each with a thin stem and, when big, a leaf. Heads are foreshortened
              (squashed vertically) and petals pointing away are painted first. Grass blades are sampled the same way
              (tiny ticks far, long blades near). Everything is collected as polygons, sorted by the y of its base and
              rasterised in one go into a supersampled integer id map (painter's order = id order), coloured through a
              lookup table and box-averaged back, so tens of thousands of anti-aliased shapes cost well under a second.
  figures     Flat, cute picture-book characters built from smooth polygons: `wanderer()` is a small hooded child in a
              felt-textured cloak with a floppy hood tip and pompom, a round cream face, dot eyes with a glint, blush,
              mittens and boots, a warm rim on the sunset side and a thin darker outline; `jar_lantern()` is a glass jar
              of fireflies that glows and lights the grass round it; `kite()` is a four-panel diamond kite with spars,
              bridle and a streaming tail of bows; `kite_string()` sags a little and goes from dark (dusk) to silver
              (night) along its length. `fireflies()`, `butterfly()`, `dragonfly()`, `seeds()` (dandelion parachutes)
              and `birds()` are the small things that reward a close look.
  plate       Fine ink lines are polylines drawn at 3x into a mask with a slight hand wobble and optional taper, then
              box-reduced, so a 0.8 px hairline stays smooth. `hatch()` lays parallel hand lines clipped to a shape
              (cross-hatch by calling twice), `dimension()` draws extension lines, a dimension line with architect's
              ticks and a small label, `ruler()` a little scale, `wash()` a flat watercolour tint with a darker edge.
              `inset()` is the circular magnified view: a paper disc with a faint shadow, whatever the callback draws
              inside it (clipped), a thin double ring, a marker ring on the target and a leader line, and the label.
  captions    Tiny lowercase handwriting from a thin hand font (Noteworthy Light on macOS, or $INKPAINT_FONT_HAND_LIGHT)
              set glyph by glyph: each letter gets its own small rotation, baseline wobble, spacing and pressure, the
              strokes are rendered at 2x and reduced, and a faint pencil texture runs through them.
  finish      `finish()`: a slight softness, bloom around the light sources, fine film / paper grain and a larger soft
              mottle, a gentle vignette leaning plum, and optionally a torn cream paper strip along the bottom edge.

API (canvas px; colours are names in COLOURS or '#rrggbb'; angles in radians unless noted)
  surface    TwilightStorybook(W, H, seed, keep_stages, stages_dir); clipped(mask) / unlit() contexts
  low level  lines(paths, width, colour, alpha, wobble, taper); fill(mask, colour, alpha); ellipse(cx, cy, rx, ry);
             poly(pts); glow(x, y, r, colour, strength); splat(xs, ys, rad, colours, alpha)
  sky        dusk_sky(stops, horizon, mottle); cloud(x0, x1, y, h, colour, alpha); streak(x0, x1, y); sun(x, y, r);
             mist(y0, y1, y2, colour, strength); birds(pts, size); seeds(pts, size)
  night      night_split(edge, soft, ground); night_sky(top, low); milky_way(p0, p1, width, bend, rift, stars);
             stars(n, region, sparkles, dusk); sparkle(x, y, size); moon(x, y, r, phase); shooting_star(p0, p1)
  land       hills(ridge, colour, base, fade, rim); striped_hill(ridge, colours, stripe, grow, fields, rows) -> info;
             trees(pts, size); meadow(crest, size, density, grass, kinds, drifts) -> info
  figures    wanderer(x, y, s, facing, reach) -> hand xy; jar_lantern(x, y, s); kite(cx, cy, size, tilt, tail) -> bridle
             xy; kite_string(p0, p1, sag); fireflies(pts, size, trails); butterfly(x, y, s, colour); dragonfly(x, y, s)
  plate      hatch(shape, angle, spacing, width); dimension(p0, p1, text, offset); ruler(x0, y, x1); wash(pts, colour);
             leader(p0, p1); inset(cx, cy, r, draw, target, label, sub)
  text       caption(x, y, text, size, colour, anchor, rot)
  finish     finish(grain, vignette, bloom, edge); render(); composite(); stage(name); save(path, stages_dir)

    import sys; sys.path.insert(0, 'lib')
    from twilight import TwilightStorybook
    t = TwilightStorybook(2000, 1100, seed=3)
    t.dusk_sky(horizon=700); t.sun(480, 670, 34)
    t.night_split([(1350, 0), (1500, 700)], soft=160)
    t.night_sky(); t.milky_way((1500, -40), (2000, 600)); t.stars(1600)
    t.striped_hill([(0, 740), (1000, 715), (2000, 730)])
    t.meadow([(0, 830), (1250, 745), (2000, 805)])
    hand = t.wanderer(1250, 748, 90)
    t.caption(120, 170, 'the evening waits for us.')
    t.finish(); t.save('twilight.jpg')
"""
import glob
import io
import os
from contextlib import contextmanager
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, load_font


COLOURS = {
    # dusk sky
    'lavender': '#b3afd0', 'lilac': '#c9bcd6', 'rose': '#dcbfca', 'peach': '#e9bba6', 'apricot': '#efc9a8',
    'gold': '#f2d8ae', 'sun': '#fcf2df', 'cloud': '#9c8ba9', 'cloud_low': '#c09798', 'streak': '#f8e8cf',
    # night
    'night': '#121219', 'night_low': '#2d2a3f', 'indigo': '#38346a', 'star': '#f8f5ee', 'moon': '#f5efdc',
    'milk': '#c2bccd',
    # land
    'mauve': '#bea59f', 'mauve_dark': '#a48c8e', 'haze': '#ead2b8', 'rim': '#f6e1b4', 'silver': '#c9cde0',
    'meadow': '#5c6242', 'meadow_far': '#8d8a6a', 'meadow_near': '#4a5134', 'grass': '#3a4329', 'tree': '#55693f',
    'tree_light': '#8da363', 'trunk': '#5a4636',
    'field_sage': '#a8a886', 'field_lav': '#ab9fbd', 'field_wheat': '#cbb594', 'field_green': '#8c946c',
    'field_rose': '#c4a3a0',
    # line, paper, captions
    'ink': '#3d383f', 'pencil': '#6e6670', 'caption': '#75687a', 'paper': '#f4ecdf', 'pale': '#d9d2d4',
    # flowers
    'daisy': '#f8f4ec', 'cornflower': '#5072cc', 'poppy': '#d9442f', 'cosmos': '#e899b4', 'marigold': '#ee9a33',
    'buttercup': '#f2c94b', 'lupine': '#8f77c8', 'forgetmenot': '#86a7e4', 'eye': '#e5b03a', 'stem': '#3f4b2c',
    # figures
    'cloak': '#5f80c2', 'cloak_dark': '#3f5891', 'face': '#f7ecdb', 'cheek': '#ec9690', 'boot': '#3a3335',
    'mitten': '#e9b44c', 'kite': '#e2705c', 'kite_cream': '#f6e6ca', 'spar': '#8b6b4d', 'string': '#5d5360',
    'lantern': '#ffd27a', 'firefly': '#f1f59a', 'glass': '#efe4cf',
}

SPECIES = ('daisy', 'cornflower', 'poppy', 'cosmos', 'marigold', 'buttercup', 'lupine', 'forgetmenot')
MIX = {'daisy': 0.24, 'cornflower': 0.15, 'poppy': 0.09, 'cosmos': 0.13, 'marigold': 0.08, 'buttercup': 0.12,
       'lupine': 0.07, 'forgetmenot': 0.12}
PETALS = {   # per species: list of (colour, weight) for the petals
    'daisy': [('#f8f4ec', 6), ('#f4eee6', 3), ('#efe2ee', 1)],
    'cornflower': [('#5072cc', 4), ('#5d80d9', 3), ('#4561b5', 2), ('#7393de', 1)],
    'poppy': [('#d9442f', 4), ('#e3563a', 3), ('#c9372b', 2), ('#ea6f3f', 1)],
    'cosmos': [('#e899b4', 4), ('#dc7aa0', 2), ('#f2c3d2', 2), ('#f6ebee', 1)],
    'marigold': [('#ee9a33', 4), ('#f1ab3e', 3), ('#e5822a', 2)],
    'buttercup': [('#f2c94b', 4), ('#f5d660', 2), ('#eab73b', 1)],
    'lupine': [('#8f77c8', 4), ('#a48fd6', 2), ('#7a63b6', 2), ('#d394bd', 1)],
    'forgetmenot': [('#86a7e4', 4), ('#9cb8ec', 2), ('#a99ad9', 1)],
}
EYES = {'daisy': '#e5b03a', 'cornflower': '#2c2f5a', 'poppy': '#2a1e22', 'cosmos': '#e3b23d', 'marigold': '#9c4f1d',
        'buttercup': '#d99a22', 'lupine': None, 'forgetmenot': '#f3e27a'}
GRASS = ['#3b4429', '#47512f', '#56613a', '#6c7445', '#8b9156', '#a3a263']

_LUMA = np.array([0.3, 0.59, 0.11], np.float32)


def hexc(c):
    """'#rrggbb', a COLOURS name or an RGB triple -> float32 RGB 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = COLOURS.get(c, c).lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    a, b = hexc(a), hexc(b)
    return (a + (b - a) * t).astype(np.float32)


def _night_matrix(tint=(0.24, 0.27, 0.43), desat=0.6):
    S = (1 - desat) * np.eye(3, dtype=np.float32) + desat * np.ones((3, 1), np.float32) @ _LUMA[None]
    return (np.diag(np.asarray(tint, np.float32)) @ S).astype(np.float32)


def _resample(P, step):
    P = np.asarray(P, np.float32)
    seg = np.hypot(*np.diff(P, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    if s[-1] < 1e-3: return P[:1]
    n = max(2, int(np.ceil(s[-1] / step)) + 1)
    ss = np.linspace(0, s[-1], n)
    return np.stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])], 1).astype(np.float32)


def _ell(cx, cy, rx, ry=None, n=14, rot=0.0):
    ry = rx if ry is None else ry
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = np.cos(t) * rx, np.sin(t) * ry
    c, s = np.cos(rot), np.sin(rot)
    return np.stack([cx + x * c - y * s, cy + x * s + y * c], 1).astype(np.float32)


def _tube(path, w0, w1=None, per=6):
    """outline polygon of a thick path (width w0 -> w1)"""
    P = np.asarray(path, np.float32)
    Q = spline(P, per) if len(P) > 2 else _resample(P, max(1.0, np.hypot(*(P[-1] - P[0])) / 6))
    w1 = w0 if w1 is None else w1
    d = np.gradient(Q, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-6
    nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    hw = np.linspace(w0, w1, len(Q))[:, None] / 2
    return np.vstack([Q + nrm * hw, (Q - nrm * hw)[::-1]]).astype(np.float32)


def _grid_sample(G, u, v):
    """bilinear sample of a small grid G (gh, gw) at u, v in 0..1"""
    gh, gw = G.shape
    x = np.clip(u, 0, 1) * (gw - 1); y = np.clip(v, 0, 1) * (gh - 1)
    x0 = np.minimum(x.astype(int), gw - 2); y0 = np.minimum(y.astype(int), gh - 2)
    fx, fy = x - x0, y - y0
    return (G[y0, x0] * (1 - fx) * (1 - fy) + G[y0, x0 + 1] * fx * (1 - fy) +
            G[y0 + 1, x0] * (1 - fx) * fy + G[y0 + 1, x0 + 1] * fx * fy)


def _pick(r, table, n):
    cols = np.stack([hexc(c) for c, _ in table]); w = np.array([w for _, w in table], np.float32)
    return cols[r.choice(len(table), n, p=w / w.sum())]


class _Polys:
    """collects polygons with colour, alpha and a sort key (painter's order)"""
    def __init__(self):
        self.P, self.c, self.a, self.k = [], [], [], []

    def add(self, pts, colour, alpha=1.0, key=0.0):
        self.P.append(np.asarray(pts, np.float32)); self.c.append(hexc(colour)); self.a.append(alpha); self.k.append(key)

    def group(self, sort=True):
        if not self.P: return None
        idx = np.argsort(np.asarray(self.k), kind='stable') if sort else np.arange(len(self.P))
        return ([self.P[i] for i in idx], np.stack(self.c)[idx], np.asarray(self.a, np.float32)[idx])


class TwilightStorybook:
    COLOURS = COLOURS

    def __init__(self, W=2000, H=1100, seed=0, keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('canvas larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32); self.C[:] = hexc('gold')
        r = np.random.default_rng(seed + 11)
        t = blur(r.random((H, W)).astype(np.float32), 0.6)
        self.TX = ((t - t.mean()) / (t.std() + 1e-6)).astype(np.float32)     # fine tooth inside the paint
        self.N = np.zeros((H, W), np.float32)                                   # 0 dusk .. 1 night (land: x ground)
        self._Nsky = self.N
        self.NM = _night_matrix()
        self.horizon = H * 0.64
        self._clip, self._lit = None, True
        self.fin = None

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== light, clip, composite
    @contextmanager
    def clipped(self, mask):
        """paint only inside a full-canvas mask (the inside of the detail inset)"""
        old = self._clip
        self._clip = mask if old is None else mask * old
        try: yield
        finally: self._clip = old

    @contextmanager
    def unlit(self):
        """paint without the night grade (emissive things, the plate overlay)"""
        old = self._lit; self._lit = False
        try: yield
        finally: self._lit = old

    def _light(self, P, ys, xs):
        """pull colours (or premultiplied colours) toward moonlit blue by the night field"""
        n = self.N[ys, xs]
        if float(n.max()) < 1e-3: return P
        return P + (P @ self.NM.T - P) * n[..., None]

    def _comp(self, A, colour, sl, lit=None):
        lit = self._lit if lit is None else lit
        ys, xs = sl
        if self._clip is not None: A = A * self._clip[ys, xs]
        Cs = self.C[ys, xs]
        if isinstance(colour, np.ndarray) and colour.ndim == 3: col = colour
        else: col = np.broadcast_to(hexc(colour), Cs.shape)
        if lit: col = self._light(col, ys, xs)
        Cs += (col - Cs) * A[..., None]

    def fill(self, mask, colour, alpha=1.0, sl=None, lit=None):
        """flat paint through a float mask (full canvas, or a local mask placed at the region sl)"""
        sl = sl or (slice(None), slice(None))
        A = mask[sl] * alpha if mask.shape[:2] == self.C.shape[:2] and sl != (slice(None), slice(None)) else mask * alpha
        self._comp(A, colour, sl, lit)

    def _paint(self, groups, ss=2, tex=0.03, lit=None):
        """rasterise groups of polygons in order: [(P, colours, alpha), ...]; P is (N, k, 2) or a list of (k, 2)"""
        lit = self._lit if lit is None else lit
        groups = [g for g in groups if g is not None and len(g[0])]
        if not groups: return
        lo = np.array([1e9, 1e9]); hi = np.array([-1e9, -1e9])
        for P, _, _ in groups:
            if isinstance(P, np.ndarray):
                lo = np.minimum(lo, P.reshape(-1, 2).min(0)); hi = np.maximum(hi, P.reshape(-1, 2).max(0))
            else:
                allp = np.concatenate([np.asarray(p, np.float32).reshape(-1, 2) for p in P])
                lo = np.minimum(lo, allp.min(0)); hi = np.maximum(hi, allp.max(0))
        x0, y0 = max(0, int(np.floor(lo[0])) - 1), max(0, int(np.floor(lo[1])) - 1)
        x1, y1 = min(self.W, int(np.ceil(hi[0])) + 2), min(self.H, int(np.ceil(hi[1])) + 2)
        if x1 <= x0 or y1 <= y0: return
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        cols_all, alph_all = [np.zeros((1, 3), np.float32)], [np.zeros(1, np.float32)]
        idx = 1
        off = np.array([x0, y0], np.float32)
        for P, cols, alpha in groups:
            if isinstance(P, np.ndarray): Q = ((P - off) * ss).reshape(len(P), -1).tolist()
            else: Q = [((np.asarray(p, np.float32) - off) * ss).ravel().tolist() for p in P]
            n = len(Q)
            for q in Q:
                if len(q) >= 6: d.polygon(q, fill=idx)
                idx += 1
            cols_all.append(np.broadcast_to(np.asarray(cols, np.float32), (n, 3)))
            alph_all.append(np.broadcast_to(np.asarray(alpha, np.float32), (n,)))
        cols = np.concatenate(cols_all); alph = np.concatenate(alph_all)
        pal = np.empty((idx, 4), np.float32)
        pal[:, :3] = np.clip(cols, 0, 1) * alph[:, None]; pal[:, 3] = alph
        ids = np.asarray(im)
        for r0 in range(0, h, 128):
            r1 = min(h, r0 + 128)
            look = pal[ids[r0 * ss:r1 * ss]].reshape(r1 - r0, ss, w, ss, 4).mean((1, 3))
            A = look[..., 3]; Pm = look[..., :3]
            ys, xs = slice(y0 + r0, y0 + r1), slice(x0, x1)
            if self._clip is not None:
                f = self._clip[ys, xs]; A = A * f; Pm = Pm * f[..., None]
            if tex: Pm = Pm * (1 + tex * self.TX[ys, xs, None])
            if lit: Pm = self._light(Pm, ys, xs)
            self.C[ys, xs] = self.C[ys, xs] * (1 - A[..., None]) + Pm

    def shapes(self, polys, colours, alpha=1.0, ss=3, tex=0.03, lit=None):
        """paint a list of polygons (one colour each, or one for all)"""
        n = len(polys)
        cols = np.broadcast_to(np.asarray(colours if not isinstance(colours, str) else hexc(colours), np.float32), (n, 3))
        self._paint([(list(polys), cols, alpha)], ss, tex, lit)

    def poly(self, pts, ss=2):
        """full-canvas anti-aliased polygon mask"""
        im = Image.new('L', (self.W * ss, self.H * ss), 0)
        ImageDraw.Draw(im).polygon([(float(x) * ss, float(y) * ss) for x, y in pts], fill=255)
        if ss > 1: im = im.resize((self.W, self.H), Image.BOX)
        return np.asarray(im, np.float32) / 255

    def _local(self, polys, ss=3, pad=3):
        """union of polygons -> (local mask, (slice y, slice x)) over their bounding box"""
        allp = np.concatenate([np.asarray(p, np.float32) for p in polys])
        x0 = max(0, int(allp[:, 0].min()) - pad); y0 = max(0, int(allp[:, 1].min()) - pad)
        x1 = min(self.W, int(allp[:, 0].max()) + pad + 1); y1 = min(self.H, int(allp[:, 1].max()) + pad + 1)
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        d = ImageDraw.Draw(im)
        for p in polys:
            q = (np.asarray(p, np.float32) - [x0, y0]) * ss
            d.polygon([tuple(v) for v in q], fill=255)
        m = np.asarray(im.reduce(ss), np.float32) / 255
        return m, (slice(y0, y1), slice(x0, x1))

    def ellipse(self, cx, cy, rx, ry=None):
        """full-canvas anti-aliased ellipse mask"""
        ry = rx if ry is None else ry
        yy = np.arange(self.H, dtype=np.float32)[:, None]; xx = np.arange(self.W, dtype=np.float32)[None, :]
        dd = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        e = 0.8 / max(1.0, min(rx, ry))
        return smoothstep(1 + e, 1 - e, dd).astype(np.float32)

    def _ridge(self, pts):
        """ridge given as control points, a per-column array or a function of x -> y per column"""
        X = np.arange(self.W, dtype=np.float32)
        if callable(pts): return np.asarray(pts(X), np.float32)
        P = np.asarray(pts, np.float32)
        if P.ndim == 1: return P
        Q = spline(P, 24)
        return np.interp(X, Q[:, 0], Q[:, 1]).astype(np.float32)

    # ================================================================== fine lines, glows, splats
    def lines(self, paths, width=1.2, colour='ink', alpha=1.0, wobble=0.0, taper=0.0, ss=3, lit=None, caps=True, seed=None):
        """fine pen lines: polylines drawn at ss x into one mask and box-reduced. width per call or per path;
        wobble = px of slow hand wander; taper = fraction of the length that thins at each end"""
        r = self._r(seed)
        P = []
        for p in paths:
            p = np.asarray(p, np.float32)
            if len(p) < 2: continue
            if wobble or taper:
                p = _resample(p, 2.0)
            if wobble and len(p) > 3:
                dd = np.gradient(p, axis=0); dd /= np.linalg.norm(dd, axis=1, keepdims=True) + 1e-6
                nrm = np.stack([-dd[:, 1], dd[:, 0]], 1)
                off = fbm1d(len(p), max(4.0, len(p) / 2.5), 3, int(r.integers(1 << 30))) * wobble
                p = p + nrm * off[:, None]
            P.append(p)
        if not P: return
        widths = np.broadcast_to(np.asarray(width, np.float32), (len(P),))
        allp = np.concatenate(P); pad = float(widths.max()) * 2 + 3
        x0, y0 = max(0, int(allp[:, 0].min() - pad)), max(0, int(allp[:, 1].min() - pad))
        x1, y1 = min(self.W, int(allp[:, 0].max() + pad) + 1), min(self.H, int(allp[:, 1].max() + pad) + 1)
        if x1 <= x0 or y1 <= y0: return
        im = Image.new('L', ((x1 - x0) * ss, (y1 - y0) * ss), 0)
        d = ImageDraw.Draw(im)
        for p, w in zip(P, widths):
            q = (p - [x0, y0]) * ss
            wp = float(w) * ss
            if taper:
                n = len(q); t = np.linspace(0, 1, n)
                prof = 0.18 + 0.82 * np.clip(np.minimum(t, 1 - t) / taper, 0, 1) ** 0.8
                for i in range(n - 1):
                    wi = max(1, int(round(wp * 0.5 * (prof[i] + prof[i + 1]))))
                    d.line([tuple(q[i]), tuple(q[i + 1])], fill=255, width=wi)
                    if wi >= 3:
                        rr = wi / 2; d.ellipse([q[i + 1][0] - rr, q[i + 1][1] - rr, q[i + 1][0] + rr, q[i + 1][1] + rr], fill=255)
            else:
                wi = max(1, int(round(wp)))
                d.line(q.ravel().tolist(), fill=255, width=wi, joint='curve')
                if caps and wi >= 3:
                    rr = wi / 2
                    for e in (q[0], q[-1]): d.ellipse([e[0] - rr, e[1] - rr, e[0] + rr, e[1] + rr], fill=255)
        m = np.asarray(im.reduce(ss), np.float32) / 255 * alpha
        self._comp(m, colour, (slice(y0, y1), slice(x0, x1)), lit)

    def glow(self, x, y, r, colour='lantern', strength=0.5, squash=1.0):
        """emissive soft light (screen blend, never graded)"""
        R = int(r * 2.6) + 2
        x0, x1 = max(0, int(x) - R), min(self.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(self.H, int(y) + R + 1)
        if x1 <= x0 or y1 <= y0: return
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]; xx = np.arange(x0, x1, dtype=np.float32)[None]
        g = strength * np.exp(-(((xx - x) / r) ** 2 + ((yy - y) / (r * squash)) ** 2))
        if self._clip is not None: g = g * self._clip[y0:y1, x0:x1]
        Cs = self.C[y0:y1, x0:x1]
        Cs[:] = 1 - (1 - Cs) * (1 - hexc(colour) * g[..., None])

    def splat(self, xs, ys, rad, colours, alpha=1.0, lit=False):
        """sub-pixel dots (stars, specks, firefly cores): disc coverage for r >= 1, mass-preserving gaussian below"""
        xs = np.asarray(xs, np.float32); ys = np.asarray(ys, np.float32); n = len(xs)
        if n == 0: return
        rad = np.broadcast_to(np.asarray(rad, np.float32), (n,))
        cols = np.broadcast_to(np.asarray(colours if not isinstance(colours, str) else hexc(colours), np.float32), (n, 3))
        al = np.broadcast_to(np.asarray(alpha, np.float32), (n,))
        R = int(np.ceil(float(rad.max()) * 1.6 + 1.5))
        bx0, bx1 = max(0, int(xs.min()) - R - 1), min(self.W, int(xs.max()) + R + 2)
        by0, by1 = max(0, int(ys.min()) - R - 1), min(self.H, int(ys.max()) + R + 2)
        if bx1 <= bx0 or by1 <= by0: return
        bw, bh = bx1 - bx0, by1 - by0
        ix = np.floor(xs).astype(np.int64); iy = np.floor(ys).astype(np.int64)
        fx, fy = xs - ix, ys - iy
        sig = np.maximum(0.42, rad * 0.62)
        mass = np.pi * rad * rad
        LI, KK, CI = [], [], []
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                d = np.sqrt((dx + 0.5 - fx) ** 2 + (dy + 0.5 - fy) ** 2)
                disc = np.clip(rad + 0.5 - d, 0, 1)
                gau = np.minimum(1.0, mass * np.exp(-d * d / (2 * sig * sig)) / (2 * np.pi * sig * sig))
                k = np.where(rad >= 1.0, disc, gau) * al
                X = ix + dx; Y = iy + dy
                ok = (k > 0.003) & (X >= bx0) & (X < bx1) & (Y >= by0) & (Y < by1)
                if not ok.any(): continue
                LI.append((Y[ok] - by0) * bw + (X[ok] - bx0)); KK.append(k[ok]); CI.append(np.nonzero(ok)[0])
        if not LI: return
        li = np.concatenate(LI); kk = np.concatenate(KK); ci = np.concatenate(CI)
        A = np.bincount(li, kk, bw * bh).reshape(bh, bw).astype(np.float32)
        P = np.stack([np.bincount(li, kk * cols[ci, c], bw * bh).reshape(bh, bw) for c in range(3)], -1).astype(np.float32)
        sc = np.where(A > 1, 1 / np.maximum(A, 1e-6), 1.0)
        A = A * sc; P = P * sc[..., None]
        ys_, xs_ = slice(by0, by1), slice(bx0, bx1)
        if self._clip is not None: A = A * self._clip[ys_, xs_]; P = P * self._clip[ys_, xs_, None]
        if lit: P = self._light(P, ys_, xs_)
        Cs = self.C[ys_, xs_]
        Cs[:] = Cs * (1 - A[..., None]) + P

    # ================================================================== dusk sky
    def dusk_sky(self, stops=None, horizon=None, mottle=1.0, seed=None):
        """the big pastel gradient: lavender -> lilac -> rose -> peach -> apricot -> gold at the horizon"""
        r = self._r(seed)
        H, W = self.H, self.W
        hz = self.horizon if horizon is None else float(horizon)
        self.horizon = hz
        stops = stops or [(0.0, 'lavender'), (0.24, 'lilac'), (0.45, 'rose'), (0.65, 'peach'), (0.84, 'apricot'), (1.0, 'gold')]
        pos = np.array([s[0] for s in stops], np.float32); cols = np.stack([hexc(s[1]) for s in stops])
        # horizontally stretched noise: the colours lie in soft layers
        k = 5
        n1 = np.asarray(Image.fromarray(noise2d(H, W // k, 120, 3, int(r.integers(1 << 30)))).resize((W, H), Image.BICUBIC))
        n2 = noise2d(H, W, 260, 2, int(r.integers(1 << 30)))
        yy = np.arange(H, dtype=np.float32)[:, None] / hz
        t = np.clip(yy + (n1 - 0.5) * 0.07 * mottle + (n2 - 0.5) * 0.05 * mottle, 0, 1)
        out = np.stack([np.interp(t, pos, cols[:, c]) for c in range(3)], -1).astype(np.float32)
        m = noise2d(H, W, 46, 4, int(r.integers(1 << 30)))
        out *= (1 + 0.022 * mottle * (m - 0.5) * 2)[..., None]
        self.C[:] = out

    def cloud(self, x0, x1, y, h, colour='cloud', alpha=0.7, light='lilac', soft=4.0, lumps=5, seed=None):
        """a soft lens-shaped cloud: a flat lens plus a few rounded lumps on top (taller in the middle), the outline
        blurred soft, the bottom kept flatter and a little crisper; lighter at the top, denser at the bottom"""
        r = self._r(seed)
        w = float(x1 - x0)
        pad = int(3 * soft) + 4
        bx0, bx1 = max(0, int(x0) - pad), min(self.W, int(x1) + pad)
        by0, by1 = max(0, int(y - h * 1.3) - pad), min(self.H, int(y + h * 0.4) + pad)
        if bx1 <= bx0 or by1 <= by0: return
        X = np.arange(bx0, bx1, dtype=np.float32)[None]; Y = np.arange(by0, by1, dtype=np.float32)[:, None]
        m = (((X - (x0 + w / 2)) / (w / 2)) ** 2 + ((Y - y) / (h * 0.32)) ** 2 < 1).astype(np.float32)
        for _ in range(lumps):
            c = r.uniform(0.15, 0.85); env = np.sin(np.pi * c) ** 0.7
            rx = w * r.uniform(0.09, 0.2); ry = h * env * r.uniform(0.7, 1.1)
            cxl = x0 + c * w
            m = np.maximum(m, (((X - cxl) / rx) ** 2 + ((Y - (y - ry * 0.25)) / ry) ** 2 < 1).astype(np.float32))
        u = np.clip((X - x0) / w, 0, 1)
        yb = y + h * 0.16 * np.clip(np.sin(np.pi * u), 0, 1) ** 0.6
        ms = blur(m, soft) * smoothstep(yb + 1.4, yb - 1.4, Y)
        top = np.where(m.any(1))[0]
        ytop = by0 + (top.min() if len(top) else 0)
        k = np.clip((Y - ytop) / max(1.0, (y + h * 0.16) - ytop), 0, 1)
        col = mix(colour, light, 0.22)[None, None] * (1 - k[..., None] ** 0.7) + hexc(colour)[None, None] * k[..., None] ** 0.7
        nz = noise2d(by1 - by0, bx1 - bx0, 20, 3, int(r.integers(1 << 30)))
        self._comp(ms * alpha * (0.88 + 0.24 * (nz - 0.5)), col.astype(np.float32), (slice(by0, by1), slice(bx0, bx1)))

    def streak(self, x0, x1, y, colour='streak', width=1.8, alpha=0.7, seed=None):
        """a thin pale line of light lying in the sky (tapered both ends)"""
        r = self._r(seed)
        xs = np.linspace(x0, x1, 12)
        ys = y + fbm1d(12, 6, 2, int(r.integers(1 << 30))) * 0.8
        self.lines([np.stack([xs, ys], 1)], width, colour, alpha, taper=0.3)

    def sun(self, x, y, r, colour='sun', halo=1.0):
        """a low pale sun: wide warm glow, close glow, soft-edged disc (paint before the hills that cut it)"""
        self.glow(x, y, r * 8, 'gold', 0.32 * halo, squash=0.5)
        self.glow(x, y, r * 2.6, '#fff1dc', 0.4 * halo)
        m = self.ellipse(x, y, r)
        yy = np.arange(self.H, dtype=np.float32)[:, None]
        col = np.broadcast_to(hexc(colour), (self.H, self.W, 3)) * (1 + 0.025 * np.clip((y - yy) / r, -1, 1))[..., None]
        self._comp(m * 0.96, col.astype(np.float32), (slice(None), slice(None)), lit=False)

    def mist(self, y0, y1, y2=None, colour='haze', strength=0.3, seed=None):
        """a soft horizontal veil: rises from y0, strongest at y1, gone by y2"""
        r = self._r(seed)
        y2 = y1 + (y1 - y0) if y2 is None else y2
        yy = np.arange(self.H, dtype=np.float32)[:, None]
        a = smoothstep(y0, y1, yy) * smoothstep(y2, y1, yy)
        lo, hi = max(0, int(y0)), min(self.H, int(y2) + 1)
        n = noise2d(hi - lo, self.W, 140, 3, int(r.integers(1 << 30)))
        A = (a[lo:hi] * strength * (0.75 + 0.5 * n)).astype(np.float32)
        self._comp(A, colour, (slice(lo, hi), slice(None)))

    def birds(self, pts, size=7.0, colour='#6d6172', alpha=0.75, seed=None):
        """tiny far birds: two little arcs each"""
        r = self._r(seed)
        paths = []
        for x, y in pts:
            s = size * r.uniform(0.7, 1.25); f = r.uniform(-0.25, 0.35)
            paths.append(np.array([(x - s, y - s * (0.15 + f)), (x - s * 0.45, y - s * 0.38), (x, y)]))
            paths.append(np.array([(x, y), (x + s * 0.45, y - s * 0.36), (x + s * 0.95, y - s * (0.2 + f))]))
        self.lines([spline(p, 6) for p in paths], 1.0, colour, alpha)

    def seeds(self, pts, size=9.0, colour='#5f5763', alpha=0.7, seed=None):
        """floating dandelion parachutes: a seed, a thin beak and a little fan of hairs"""
        r = self._r(seed)
        paths = []; dots = []
        for x, y in pts:
            s = size * r.uniform(0.75, 1.2); a = r.uniform(-0.6, 0.6)
            ux, uy = np.sin(a), -np.cos(a)                       # up the beak
            top = (x + ux * s, y + uy * s)
            paths.append(np.array([(x, y), top]))
            for k in range(9):
                b = a + np.deg2rad(-75 + 150 * k / 8) + r.normal(0, 0.05)
                L = s * r.uniform(0.55, 0.8)
                paths.append(np.array([top, (top[0] + np.sin(b) * L, top[1] - np.cos(b) * L)]))
            dots.append((x - ux * 1.2, y - uy * 1.2))
        self.lines(paths, 0.65, colour, alpha)
        d = np.array(dots)
        self.splat(d[:, 0], d[:, 1], 1.0, hexc(colour), alpha, lit=True)

    # ================================================================== night
    def night_split(self, edge, soft=160.0, ground=0.9, wander=40.0, feather=0.25, seed=None):
        """the boundary between dusk and night: edge is a top -> bottom polyline [(x, y), ...] and night lies to its
        right. N = 0 dusk .. 1 night across a feathered band of +-soft px; below the horizon the land is shaded by
        N * ground. Call after dusk_sky() (it uses the horizon)."""
        r = self._r(seed)
        H, W = self.H, self.W
        E = np.asarray(edge, np.float32)
        ys = np.arange(H, dtype=np.float32)
        ex = np.interp(ys, E[:, 1], E[:, 0]) + fbm1d(H, 260, 3, int(r.integers(1 << 30))) * wander
        n2 = noise2d(H, W, 170, 3, int(r.integers(1 << 30)))
        d = np.arange(W, dtype=np.float32)[None] - ex[:, None] + (n2 - 0.5) * soft * feather
        N = smoothstep(-soft, soft, d)
        g = 1 - (1 - ground) * smoothstep(self.horizon - 30, self.horizon + 30, ys)[:, None]
        self.N = (N * g).astype(np.float32)
        self._Nsky = N.astype(np.float32)

    def night_sky(self, top='night', low='night_low', indigo='indigo', mottle=1.0, richness=0.5, seed=None):
        """the night gradient laid with the night field as alpha; it leans indigo near the boundary, and the
        transition band is re-saturated (richness) so dusk -> night passes through mauve and violet, not grey"""
        r = self._r(seed)
        H, W = self.H, self.W
        N = self._Nsky
        yy = np.arange(H, dtype=np.float32)[:, None, None]
        t = np.clip(yy / self.horizon, 0, 1) ** 1.7
        col = hexc(top) * (1 - t) + hexc(low) * t
        col = col + (hexc(indigo) - col) * (0.8 * (1 - N) ** 0.9)[..., None]
        m = noise2d(H, W, 120, 4, int(r.integers(1 << 30)))
        col = col * (1 + 0.08 * mottle * (m - 0.5))[..., None]
        with self.unlit():
            self._comp(N, col.astype(np.float32), (slice(None), slice(None)))
        if richness:
            hz = int(min(H, self.horizon + 40))
            w = (4 * N[:hz] * (1 - N[:hz]))[..., None]
            Cs = self.C[:hz]
            lum = (Cs @ _LUMA)[..., None]
            Cs[:] = np.clip(lum + (Cs - lum) * (1 + richness * w), 0, 1)

    def milky_way(self, p0, p1, width=150.0, bend=50.0, rift=0.8, stars=3500, colour='milk', alpha=0.45, seed=None):
        """a cloudy luminous band from p0 to p1 with a dark rift and a dense dust of faint stars"""
        r = self._r(seed)
        H, W = self.H, self.W
        p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
        L = float(np.linalg.norm(p1 - p0)); u = (p1 - p0) / L; nv = np.array([-u[1], u[0]], np.float32)
        hz = int(min(H, self.horizon + 10))
        yy = np.arange(hz, dtype=np.float32)[:, None]; xx = np.arange(W, dtype=np.float32)[None]
        s = (xx - p0[0]) * u[0] + (yy - p0[1]) * u[1]
        dd = (xx - p0[0]) * nv[0] + (yy - p0[1]) * nv[1]
        sn = np.clip(s / L, -0.2, 1.2)
        k = 256; grid = np.linspace(-0.2, 1.2, k)
        wander = np.interp(sn, grid, fbm1d(k, 40, 3, int(r.integers(1 << 30)))) * width * 0.35
        wid = width * (0.8 + 0.3 * np.interp(sn, grid, fbm1d(k, 30, 2, int(r.integers(1 << 30)))))
        c = bend * np.sin(np.pi * np.clip(sn, 0, 1)) + wander
        x = dd - c
        core = np.exp(-(x / wid) ** 2 * 1.6)
        inner = np.exp(-(x / (wid * 0.42)) ** 2 * 1.6)
        n1 = noise2d(hz, W, 70, 4, int(r.integers(1 << 30))); n2 = noise2d(hz, W, 16, 3, int(r.integers(1 << 30)))
        cloud = np.clip(0.15 + 1.0 * n1 + 0.45 * n2 - 0.45, 0, 1.2)
        ends = smoothstep(-0.15, 0.1, sn) * smoothstep(1.15, 0.9, sn)
        dens = ((0.7 * core + 0.55 * inner) * cloud * ends).astype(np.float32)
        lane_c = width * 0.08 * np.sin(sn * 7.0) + np.interp(sn, grid, fbm1d(k, 20, 3, int(r.integers(1 << 30)))) * width * 0.1
        lw = width * 0.075 * (0.55 + 0.9 * n1)
        lane = np.exp(-((x - lane_c) / lw) ** 2) * (0.8 * inner + 0.3 * core) * ends * rift * (0.55 + 0.6 * n2)
        N = self._Nsky[:hz]
        sl = (slice(0, hz), slice(None))
        with self.unlit():
            self._comp(np.clip(dens * alpha, 0, 1) * N, colour, sl)
            self._comp(np.clip(lane, 0, 0.92) * N * 0.9, '#0b0a10', sl)
        # the dust of faint stars inside the band
        M = stars * 6
        px = r.uniform(0, W, M); py = r.uniform(0, hz, M)
        dv = dens[py.astype(int), px.astype(int)] * N[py.astype(int), px.astype(int)]
        ok = r.random(M) < dv * 1.6
        px, py = px[ok][:stars], py[ok][:stars]
        b = r.uniform(0.25, 0.85, len(px)) ** 1.5
        self.splat(px, py, r.uniform(0.3, 0.7, len(px)), hexc('star'), b, lit=False)

    def stars(self, n=1600, region=None, sparkles=6, dusk=0.0, size=(0.35, 1.45), sparkle_size=(7, 13), seed=None):
        """a star field (power-law brightness, some warm, some blue) that thins out across the night boundary"""
        r = self._r(seed)
        x0, y0, x1, y1 = region or (0, 0, self.W, self.horizon)
        xs = r.uniform(x0, x1, n).astype(np.float32); ys = r.uniform(y0, y1, n).astype(np.float32)
        Nv = self._Nsky[np.clip(ys.astype(int), 0, self.H - 1), np.clip(xs.astype(int), 0, self.W - 1)]
        vis = np.maximum(Nv, dusk)
        keep = r.random(n) < vis ** 1.4
        b = np.clip(r.pareto(2.4, n) * 0.33 + 0.12, 0.08, 1.8)
        rad = size[0] + (size[1] - size[0]) * np.clip(b / 1.6, 0, 1) ** 0.8
        al = np.clip(0.3 + 0.62 * b, 0, 1) * vis ** 0.6 * (0.45 + 0.55 * smoothstep(self.horizon, self.horizon - 160, ys))
        cols = np.tile(hexc('star'), (n, 1))
        k = r.random(n)
        cols[k < 0.1] = hexc('#ffdcb3'); cols[(k >= 0.1) & (k < 0.2)] = hexc('#d2ddff')
        self.splat(xs[keep], ys[keep], rad[keep], cols[keep], al[keep], lit=False)
        with self.unlit():
            bright = np.where(keep & (b > 1.0))[0]
            for i in bright:
                self.glow(xs[i], ys[i], 3.0 + 2.0 * b[i], cols[i], 0.10 * al[i])
            cand = np.where(keep & (Nv > 0.8) & (ys < y1 - 180))[0]
            if sparkles and len(cand):
                pick = cand[np.argsort(-b[cand])[:max(sparkles * 3, sparkles)]]
                pick = r.choice(pick, min(sparkles, len(pick)), replace=False)
                for i in pick:
                    self.sparkle(xs[i], ys[i], r.uniform(*sparkle_size), alpha=0.85 * Nv[i])

    def sparkle(self, x, y, size=12.0, colour='star', alpha=0.9):
        """four-point star: long tapered cross, short faint diagonals, a bright core and a little glow"""
        with self.unlit():
            self.glow(x, y, size * 0.32, colour, 0.35 * alpha)
            self.lines([[(x - size, y), (x + size, y)], [(x, y - size * 1.1), (x, y + size * 1.1)]], 1.25, colour, alpha, taper=0.5)
            d = size * 0.34
            self.lines([[(x - d, y - d), (x + d, y + d)], [(x - d, y + d), (x + d, y - d)]], 0.7, colour, alpha * 0.55, taper=0.5)
            self.splat([x], [y], [1.3], hexc(colour), alpha, lit=False)

    def moon(self, x, y, r, phase=0.3, tilt=-0.6, colour='moon', earthshine=0.22, glow=1.0):
        """a crescent: a lit disc minus an offset dark disc, faint earthshine on the rest, a soft glow"""
        R = int(r * 1.5) + 3
        x0, x1 = max(0, int(x) - R), min(self.W, int(x) + R + 1)
        y0, y1 = max(0, int(y) - R), min(self.H, int(y) + R + 1)
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]; xx = np.arange(x0, x1, dtype=np.float32)[None]
        disc = smoothstep(r + 0.7, r - 0.7, np.hypot(xx - x, yy - y))
        off = r * 2 * (1 - phase)
        sx, sy = x + np.cos(tilt) * off * 0.62, y + np.sin(tilt) * off * 0.62
        shadow = smoothstep(r * 0.98 + 0.7, r * 0.98 - 0.7, np.hypot(xx - sx, yy - sy))
        lit = disc * (1 - shadow)
        sl = (slice(y0, y1), slice(x0, x1))
        with self.unlit():
            self.glow(x, y, r * 3.2, colour, 0.16 * glow)
            self._comp(disc * earthshine, '#4a4a58', sl)
            rr = np.random.default_rng(self.seed + 41)
            mott = 1 - 0.07 * noise2d(y1 - y0, x1 - x0, max(3, r / 3), 2, int(rr.integers(1 << 30)))
            col = hexc(colour)[None, None] * mott[..., None]
            self._comp(lit * 0.97, col.astype(np.float32), sl)

    def shooting_star(self, p0, p1, width=1.5, colour='star', alpha=0.95):
        """a thin streak that brightens toward its head (p1)"""
        p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
        k = 26
        with self.unlit():
            for i in range(k):
                a, b = i / k, (i + 1) / k
                self.lines([[p0 + (p1 - p0) * a, p0 + (p1 - p0) * b]], width * (0.35 + 0.65 * b), colour, alpha * b ** 1.6, caps=False)
            self.glow(p1[0], p1[1], 4.5, colour, 0.45 * alpha)
            self.splat([p1[0]], [p1[1]], [1.4], hexc(colour), alpha, lit=False)

    # ================================================================== land
    def hills(self, ridge, colour='mauve', base=None, haze='haze', fade=0.35, rim=None, rim_alpha=0.45, texture=0.03, seed=None):
        """a distant range: filled ridge, lighter toward its misty base, faint texture, optional lit rim"""
        r = self._r(seed)
        ry = self._ridge(ridge)
        y0 = max(0, int(ry.min()) - 2); y1 = self.H if base is None else min(self.H, int(base))
        Y = np.arange(y0, y1, dtype=np.float32)[:, None]
        D = Y - ry[None]
        A = smoothstep(-0.8, 0.8, D)
        depth = np.clip(D / max(1.0, (y1 - ry.min()) * 0.8), 0, 1)[..., None]
        col = hexc(colour) * (1 - fade * depth) + hexc(haze) * fade * depth
        n = noise2d(y1 - y0, self.W, 50, 3, int(r.integers(1 << 30)))
        col = col * (1 + texture * (n - 0.5) * 2)[..., None]
        self._comp(A, col.astype(np.float32), (slice(y0, y1), slice(None)))
        if rim:
            self._comp(np.exp(-((D - 1.2) / 1.0) ** 2) * rim_alpha, rim, (slice(y0, y1), slice(None)))
        return ry

    def striped_hill(self, ridge, colours=('field_sage', 'field_lav', 'field_wheat', 'field_green', 'field_rose'), base=None,
                     stripe=(9.0, 20.0), grow=2.2, fields=(150, 470), slant=0.7, rows=0.45, hedge=0.35, rim='rim',
                     rim_alpha=0.6, texture=0.035, haze='haze', fade=0.25, seed=None):
        """rolling hill in soft stacked pastel stripes: bands follow the ridge and widen toward the viewer, each band
        cut into slanted patchwork fields, some with fine crop rows; hedge lines; a pale rim along the crest.
        Returns {'ridge': per-column y, 'bounds': stripe boundaries below the ridge (px)}"""
        r = self._r(seed)
        W = self.W
        ry = self._ridge(ridge)
        y0 = max(0, int(ry.min()) - 2); y1 = self.H if base is None else min(self.H, int(base))
        hgt = y1 - y0
        X = np.arange(W, dtype=np.float32)[None]
        Y = np.arange(y0, y1, dtype=np.float32)[:, None]
        D = Y - ry[None]
        Dw = D + (noise2d(hgt, W, 180, 2, int(r.integers(1 << 30))) - 0.5) * 7 * np.clip(D / 30, 0, 1)
        b = [0.0]
        while b[-1] < hgt + 60:
            b.append(b[-1] + r.uniform(*stripe) * (1 + grow * b[-1] / max(1, hgt)))
        b = np.array(b, np.float32); ns = len(b) - 1
        k = np.clip(np.searchsorted(b, Dw) - 1, 0, ns - 1)
        loc = Dw - b[k]
        nf = int(W / fields[0]) + 6
        cuts = np.cumsum(r.uniform(*fields, (ns, nf)), 1) - r.uniform(0, fields[1], (ns, 1))
        slants = r.uniform(-slant, slant, ns)
        fidx = np.zeros(k.shape, np.int64); dcut = np.full(k.shape, 99.0, np.float32)
        for i in range(ns):
            m = k == i
            if not m.any(): continue
            xe = (X + loc * slants[i])[m]
            j = np.clip(np.searchsorted(cuts[i], xe), 1, nf - 1)
            fidx[m] = j
            dcut[m] = np.minimum(xe - cuts[i][j - 1], cuts[i][j] - xe)
        pal = np.stack([hexc(c) for c in colours])
        lut = pal[r.integers(0, len(colours), (ns, nf))] * r.uniform(0.94, 1.05, (ns, nf, 1))
        col = lut[k, fidx].astype(np.float32)
        rowflag = r.random((ns, nf)) < rows; sp = r.uniform(2.6, 4.0, (ns, nf))
        rl = (np.mod(loc, sp[k, fidx]) < 0.95) & rowflag[k, fidx] & (loc > 1.5)
        col = col * (1 - 0.07 * rl)[..., None]
        hd = (np.exp(-(loc / 0.75) ** 2) + np.exp(-(dcut / 0.7) ** 2) * 0.8) * hedge * np.clip(D / 4, 0, 1)
        col = col * (1 - 0.35 * np.clip(hd, 0, 1))[..., None]
        depth = np.clip(D / max(1.0, hgt * 0.9), 0, 1)
        col = col + (hexc(haze) - col) * (fade * (1 - depth) ** 2)[..., None]
        n = noise2d(hgt, W, 30, 3, int(r.integers(1 << 30)))
        col = col * (1 + texture * (n - 0.5) * 2 + 0.012 * self.TX[y0:y1])[..., None]
        sl = (slice(y0, y1), slice(None))
        self._comp(smoothstep(-0.8, 0.8, D), col.astype(np.float32), sl)
        if rim: self._comp(np.exp(-((D - 1.3) / 1.1) ** 2) * rim_alpha, rim, sl)
        return {'ridge': ry, 'bounds': b}

    def trees(self, pts, size=7.0, colour='tree', light='tree_light', trunk='trunk', shadow=0.22, ss=3, seed=None):
        """tiny round picture-book trees: a soft shadow, a trunk, a round crown and a lit top-left"""
        r = self._r(seed)
        G = _Polys()
        for x, y in sorted(pts, key=lambda p: p[1]):
            s = size * r.uniform(0.75, 1.3)
            G.add(_ell(x + s * 0.55, y + s * 0.05, s * 0.95, s * 0.22, 12), '#2f2b2c', shadow, y)
            G.add(np.array([(x - s * 0.09, y), (x + s * 0.09, y), (x + s * 0.06, y - s), (x - s * 0.06, y - s)]), trunk, 1, y + 0.01)
            c = hexc(colour) * r.uniform(0.85, 1.12)
            G.add(_ell(x + r.normal(0, 0.06) * s, y - s * 1.2, s * 0.82, s * 0.78, 14), c, 1, y + 0.02)
            G.add(_ell(x - s * 0.24, y - s * 1.42, s * 0.42, s * 0.34, 12), mix(light, c, 0.25), 0.85, y + 0.03)
        self._paint([G.group()], ss)

    # ================================================================== the meadow
    def meadow(self, crest, bottom=None, colour='meadow', far_colour='meadow_far', near_colour='meadow_near',
               size=(1.0, 30.0), power=2.0, density=1.0, grass=1.0, kinds=None, drifts=0.8, haze=0.5, rim='rim', rim_alpha=0.6,
               ss=3, seed=None):
        """the wildflower meadow below a crest line: ground, lit rim, thousands of flowers and grass blades in
        perspective (specks at the crest, big heads at the bottom). kinds = {species: weight} (see MIX).
        Returns {'crest': per-column y, 'y0': top row, 'y1': bottom row}"""
        r = self._r(seed)
        W, H = self.W, self.H
        cy = self._ridge(crest)
        y0 = max(0, int(np.floor(cy.min())) - 2); y1 = H if bottom is None else int(bottom)
        hgt = y1 - y0
        Y = np.arange(y0, y1, dtype=np.float32)[:, None]
        D = Y - cy[None]
        span = np.maximum(y1 - cy, 1.0)[None]
        t = np.clip(D / span, 0, 1)
        # ---- ground
        cf, cm, cn = hexc(far_colour), hexc(colour), hexc(near_colour)
        tt = t[..., None]
        base = np.where(tt < 0.3, cf + (cm - cf) * (tt / 0.3) ** 0.8, cm + (cn - cm) * np.clip((tt - 0.3) / 0.7, 0, 1))
        n1 = noise2d(hgt, W, 40, 3, int(r.integers(1 << 30)))
        base = base * (1 + 0.07 * (n1 - 0.5) + 0.03 * self.TX[y0:y1])[..., None]
        sl = (slice(y0, y1), slice(None))
        self._comp(smoothstep(-0.8, 0.8, D), base.astype(np.float32), sl)
        # flecks in the ground (darker and lighter specks)
        nfk = int(W * hgt * 0.02 * density)
        fx = r.uniform(0, W, nfk); fy = r.uniform(y0, y1, nfk)
        okf = fy > cy[fx.astype(int)] + 1
        fx, fy = fx[okf], fy[okf]
        tv = np.clip((fy - cy[fx.astype(int)]) / (y1 - cy[fx.astype(int)]), 0, 1)
        fc = np.where(r.random(len(fx))[:, None] < 0.6, hexc('#3d4529'), hexc('#7d8350'))
        self.splat(fx, fy, 0.5 + 1.4 * tv, fc, 0.5, lit=True)
        # ---- plants: rejection sampling so that coverage follows perspective
        s0, s1 = size
        sc_of = lambda tv: s0 + (s1 - s0) * tv ** power
        cov = lambda tv: (0.24 + 0.32 * tv) * density
        dmax = cov(0.0) / (np.pi * s0 * s0)
        M = int(W * hgt * dmax * 1.05)
        px = r.uniform(0, W, M).astype(np.float32); py = r.uniform(y0, y1, M).astype(np.float32)
        cyx = cy[px.astype(int)]
        tv = np.clip((py - cyx) / (y1 - cyx), 0, 1); sc = sc_of(tv)
        ok = (py > cyx + 0.8) & (r.random(M) < cov(tv) / (np.pi * sc * sc) / dmax)
        px, py, tv, sc = px[ok], py[ok], tv[ok], sc[ok]
        sc = sc * r.uniform(0.7, 1.3, len(sc))
        # species with drifting patches
        kinds = kinds or MIX
        names = [k for k in SPECIES if kinds.get(k, 0) > 0]
        wts = np.array([kinds[k] for k in names], np.float32)
        u = px / W; v = (py - y0) / max(1, hgt)
        P = np.stack([wts[i] * np.exp(drifts * 2.2 * (_grid_sample(r.random((5, 9)), u, v) - 0.5)) for i in range(len(names))], 1)
        P /= P.sum(1, keepdims=True)
        sp = (P.cumsum(1) < r.random(len(px))[:, None]).sum(1)
        sp = np.minimum(sp, len(names) - 1)
        G = _Polys()
        stemc = np.stack([hexc('stem'), hexc('#4f5b35'), hexc('#5d6a3d')])
        self._mhaze = (cf, float(haze))
        for i in range(len(px)):
            self._plant(G, names[sp[i]], float(px[i]), float(py[i]), float(sc[i]), float(tv[i]), r, stemc)
        # grass blades, sampled the same way
        g0 = 0.9
        gl = lambda tv: g0 + (s1 * 2.1 - g0) * tv ** power
        gw = lambda tv: 0.5 + 1.3 * tv ** power
        gden = lambda tv: 0.2 * grass / (gl(tv) * np.maximum(gw(tv), 0.55))
        gmax = float(gden(0.0))
        Mg = int(W * hgt * gmax)
        gx = r.uniform(0, W, Mg).astype(np.float32); gy = r.uniform(y0, y1, Mg).astype(np.float32)
        cyg = cy[gx.astype(int)]
        tg = np.clip((gy - cyg) / (y1 - cyg), 0, 1)
        okg = (gy > cyg + 0.6) & (r.random(Mg) < gden(tg) / gmax)
        gx, gy, tg = gx[okg], gy[okg], tg[okg]
        L = gl(tg) * r.uniform(0.6, 1.4, len(gx)); Wd = np.maximum(0.45, gw(tg) * r.uniform(0.7, 1.3, len(gx)))
        lean = r.normal(0, 0.28, len(gx)); bend = r.normal(0, 0.18, len(gx))
        gpal = np.stack([hexc(c) for c in GRASS])
        gi = np.clip((r.random(len(gx)) * 0.85 + 0.15 * (1 - tg)) * len(GRASS), 0, len(GRASS) - 1).astype(int)
        gcol = gpal[gi] * (1 + 0.15 * (1 - tg))[:, None]
        for i in range(len(gx)):
            x, y, l, w, ln, bd = float(gx[i]), float(gy[i]), float(L[i]), float(Wd[i]), float(lean[i]), float(bend[i])
            tip = (x + ln * l, y - l)
            mid = (x + ln * l * 0.45 + bd * l * 0.3, y - l * 0.5)
            G.add([(x - w / 2, y), (mid[0] - w * 0.3, mid[1]), tip, (mid[0] + w * 0.3, mid[1]), (x + w / 2, y)],
                  gcol[i], 0.92, y + 0.001)
        self._paint([G.group()], ss, tex=0.03)
        # the lit rim along the crest: gold on the dusk side, silver under the night
        rimA = np.exp(-((D - 1.0) / 1.15) ** 2) * rim_alpha
        if rim:
            Nl = self._Nsky[y0:y1]
            rc = hexc(rim)[None, None] * (1 - Nl[..., None]) + hexc('silver')[None, None] * Nl[..., None]
            with self.unlit():
                self._comp(rimA * (1 - 0.45 * Nl), rc.astype(np.float32), sl)
        return {'crest': cy, 'y0': y0, 'y1': y1}

    def _plant(self, G, kind, x, y, s, tv, r, stemc):
        """one wildflower into the polygon list G (stem, leaf, head), keyed by the y of its base"""
        cols = PETALS[kind]
        base = _pick(r, cols, 1)[0] * r.uniform(0.92, 1.05)
        hc, ha = self._mhaze
        hz = ha * (1 - tv) ** 2.5                                      # far flowers sink into the hazy ground colour
        base = base * (1 - hz) + hc * hz
        if s < 1.9:                                                    # a speck
            G.add(_ell(x, y, s, s * 0.8, 7, r.uniform(0, 3)), base, 0.88, y)
            return
        stem_len = s * r.uniform(2.6, 4.2) * (1.35 if kind in ('poppy', 'cosmos') else 1.0)
        lean = r.normal(0, 0.18) * stem_len
        key = y + stem_len
        sw = max(0.5, s * 0.085)
        sc_ = stemc[r.integers(0, 3)]
        stem = np.array([(x - sw / 2, y), (x + sw / 2, y), (x + lean + sw * 0.7, y + stem_len), (x + lean - sw * 0.7, y + stem_len)])
        G.add(stem, sc_, 0.95, key - 0.01)
        if s > 7 and r.random() < 0.8:                                   # a leaf on the stem
            ly = y + stem_len * r.uniform(0.45, 0.8); lx = x + lean * (ly - y) / stem_len
            side = r.choice([-1, 1]); L = s * r.uniform(1.2, 2.0); a = side * r.uniform(0.5, 1.0) - np.pi / 2
            G.add(self._leaf(lx, ly, L, L * 0.22, a), sc_ * 1.08, 0.95, key - 0.009)
        sq = r.uniform(0.62, 0.92)
        rot = r.uniform(0, 2 * np.pi)
        if s < 4.2 or kind == 'forgetmenot':
            if kind == 'lupine':
                for j in range(5):
                    rr = s * (0.42 - 0.06 * j)
                    G.add(_ell(x + (j % 2 - 0.5) * s * 0.25, y - j * s * 0.45, rr, rr * 0.85, 7), base * (1 + 0.04 * j), 1, key)
                return
            if kind == 'forgetmenot':
                for j in range(r.integers(3, 6) if s > 3 else 2):
                    ox, oy = r.normal(0, s * 0.45), r.normal(0, s * 0.3)
                    self._rosette(G, x + ox, y + oy, s * 0.42, 5, base * r.uniform(0.95, 1.05), sq, r.uniform(0, 6), key, EYES[kind] if s > 3 else None)
                return
            npet = {'daisy': 8, 'cornflower': 7, 'poppy': 4, 'cosmos': 8, 'marigold': 10, 'buttercup': 5}[kind]
            self._rosette(G, x, y, s, npet, base, sq, rot, key, EYES[kind] if s > 2.6 else None)
            return
        self._head(G, kind, x, y, s, base, sq, rot, key, r)

    def _rosette(self, G, x, y, s, n, colour, sq, rot, key, eye):
        th = np.linspace(0, 2 * np.pi, n * 4, endpoint=False)
        rad = s * (0.62 + 0.38 * np.abs(np.cos(th * n / 2)))
        pts = np.stack([x + np.cos(th + rot) * rad, y + np.sin(th + rot) * rad * sq], 1)
        G.add(pts, colour, 1, key)
        if eye: G.add(_ell(x, y, s * 0.3, s * 0.3 * sq, 8), eye, 1, key)

    @staticmethod
    def _leaf(x, y, L, w, a):
        T = np.array([(0, 0), (0.25, -0.42), (0.6, -0.48), (1, 0), (0.6, 0.42), (0.25, 0.36)], np.float32)
        c, s = np.cos(a), np.sin(a)
        return np.stack([x + T[:, 0] * L * c - T[:, 1] * w * 2 * s, y + T[:, 0] * L * s + T[:, 1] * w * 2 * c], 1)

    def _petals(self, G, T, x, y, n, length, width, rot, sq, cols, key, start=0.0, jit=0.08, r=None):
        """n petals of template T (pointing +x from the origin), squashed by sq; back petals first"""
        th = rot + 2 * np.pi * np.arange(n) / n + (r.normal(0, jit, n) if r is not None else 0)
        order = np.argsort(np.sin(th))
        for i in order:
            c, s = np.cos(th[i]), np.sin(th[i])
            lx = start + T[:, 0] * length; ly = T[:, 1] * width
            G.add(np.stack([x + lx * c - ly * s, y + (lx * s + ly * c) * sq], 1), cols[i], 1, key)

    def _head(self, G, kind, x, y, s, base, sq, rot, key, r):
        cols = lambda n, v=0.05: _pick(r, PETALS[kind], n) * r.uniform(1 - v, 1 + v, (n, 1))
        if kind == 'daisy':
            n = int(r.integers(12, 17))
            T = np.array([(0, 0), (0.15, -0.5), (0.6, -0.55), (0.95, -0.3), (1, 0), (0.95, 0.3), (0.6, 0.55), (0.15, 0.5)], np.float32)
            pc = np.clip(base[None] * r.uniform(0.9, 1.02, (n, 1)), 0, 1)
            self._petals(G, T, x, y, n, s * 0.82, s * 0.2, rot, sq, pc, key, start=s * 0.18, r=r)
            G.add(_ell(x, y, s * 0.3, s * 0.3 * sq, 12), EYES['daisy'], 1, key)
            G.add(_ell(x + s * 0.06, y + s * 0.06 * sq, s * 0.17, s * 0.17 * sq, 10), '#c98f22', 1, key)
        elif kind == 'cornflower':
            n = int(r.integers(8, 11))
            T = np.array([(0, -0.1), (0.7, -0.36), (1.0, -0.5), (0.9, -0.24), (1.02, -0.08), (0.88, 0.06), (1.0, 0.22),
                          (0.9, 0.34), (1.0, 0.5), (0.7, 0.38), (0, 0.1)], np.float32)
            self._petals(G, T, x, y, n, s * 0.95, s * 0.42, rot, sq, cols(n), key, start=s * 0.05, r=r)
            G.add(_ell(x, y, s * 0.2, s * 0.2 * sq, 8), EYES['cornflower'], 1, key)
        elif kind == 'poppy':
            n = 4
            T = np.stack([0.5 + 0.5 * np.cos(np.linspace(0, 2 * np.pi, 14, endpoint=False)),
                          0.55 * np.sin(np.linspace(0, 2 * np.pi, 14, endpoint=False))], 1).astype(np.float32)
            th = rot + np.arange(n) * np.pi / 2
            cs = cols(n, 0.06)
            sqp = sq * 0.85
            for i in np.argsort(np.sin(th)):
                c, s_ = np.cos(th[i]), np.sin(th[i])
                lx = T[:, 0] * s * 1.0; ly = T[:, 1] * s * 1.0
                shade = 0.82 if np.sin(th[i]) < 0 else 1.0
                G.add(np.stack([x + lx * c - ly * s_, y + (lx * s_ + ly * c) * sqp - s * 0.1], 1), cs[i] * shade, 1, key)
            G.add(_ell(x, y - s * 0.1, s * 0.24, s * 0.22 * sqp, 10), EYES['poppy'], 1, key)
            for j in range(8):
                a = j * np.pi / 4 + rot
                G.add(_ell(x + np.cos(a) * s * 0.3, y - s * 0.1 + np.sin(a) * s * 0.3 * sqp, s * 0.05 + 0.3, s * 0.05 + 0.3, 6), '#241a1e', 1, key)
        elif kind == 'cosmos':
            n = 8
            T = np.array([(0, -0.12), (0.45, -0.46), (0.92, -0.52), (1.0, -0.28), (0.84, 0.0), (1.0, 0.28), (0.92, 0.52),
                          (0.45, 0.46), (0, 0.12)], np.float32)
            self._petals(G, T, x, y, n, s * 0.9, s * 0.36, rot, sq, np.clip(base[None] * r.uniform(0.93, 1.04, (n, 1)), 0, 1), key, start=s * 0.08, r=r)
            G.add(_ell(x, y, s * 0.2, s * 0.2 * sq, 10), EYES['cosmos'], 1, key)
        elif kind == 'marigold':
            T = np.stack([0.5 + 0.5 * np.cos(np.linspace(0, 2 * np.pi, 10, endpoint=False)),
                          0.5 * np.sin(np.linspace(0, 2 * np.pi, 10, endpoint=False))], 1).astype(np.float32)
            n1, n2 = 16, 11
            self._petals(G, T, x, y, n1, s * 0.9, s * 0.34, rot, sq, cols(n1), key, start=s * 0.1, r=r)
            self._petals(G, T, x, y, n2, s * 0.6, s * 0.3, rot + 0.3, sq, cols(n2) * 0.9, key, start=s * 0.05, r=r)
            G.add(_ell(x, y, s * 0.18, s * 0.18 * sq, 8), EYES['marigold'], 1, key)
        elif kind == 'buttercup':
            T = np.stack([0.5 + 0.5 * np.cos(np.linspace(0, 2 * np.pi, 12, endpoint=False)),
                          0.52 * np.sin(np.linspace(0, 2 * np.pi, 12, endpoint=False))], 1).astype(np.float32)
            self._petals(G, T, x, y, 5, s * 0.85, s * 0.78, rot, sq, cols(5, 0.04), key, start=s * 0.05, r=r)
            G.add(_ell(x, y, s * 0.2, s * 0.2 * sq, 8), EYES['buttercup'], 1, key)
        elif kind == 'lupine':
            n = int(r.integers(10, 16)); hgt = s * r.uniform(2.6, 3.6)
            bend = r.normal(0, 0.12) * hgt
            for j in range(n):
                f = j / (n - 1)
                cx_ = x + bend * f * f + (1 if j % 2 else -1) * s * 0.2 * (1 - 0.6 * f)
                cy_ = y - f * hgt
                rr = s * (0.36 - 0.22 * f)
                col = np.clip(base * (0.88 + 0.22 * f), 0, 1)
                G.add(_ell(cx_, cy_, rr, rr * 0.8, 9, r.uniform(0, 3)), col, 1, key)
                if f < 0.75: G.add(_ell(cx_ - rr * 0.25, cy_ - rr * 0.3, rr * 0.4, rr * 0.3, 6), np.clip(col * 1.18, 0, 1), 0.9, key)

    def grass_heads(self, x0, x1, base, n=30, height=(30, 70), colour='#5b4a45', head='#7a6250', lean=0.15, width=0.9, seed=None):
        """tall wild-grass stems with small seed heads, rising from a ground line (base: y or f(x)), e.g. along a crest
        against the sky"""
        r = self._r(seed)
        xs = r.uniform(x0, x1, n)
        ys = base(xs) if callable(base) else np.full(n, float(base))
        paths, heads, hcols = [], [], []
        for x, y in zip(xs, ys):
            hgt = r.uniform(*height); ln = r.normal(lean, 0.12)
            P = spline(np.array([(x, y + 2), (x + ln * hgt * 0.35, y - hgt * 0.5), (x + ln * hgt, y - hgt)]), 8)
            paths.append(P)
            tip = P[-1]; d = P[-1] - P[-4]; a = np.arctan2(d[1], d[0])
            for k in range(int(r.integers(4, 8))):
                f = k * r.uniform(2.2, 3.0)
                cxk = tip[0] - np.cos(a) * f; cyk = tip[1] - np.sin(a) * f
                side = 1 if k % 2 else -1
                heads.append(_ell(cxk + np.cos(a + side * 0.5) * 1.2, cyk + np.sin(a + side * 0.5) * 1.2, 2.2 - 0.12 * k, 1.1, 8, a + side * 0.45))
                hcols.append(hexc(head) * r.uniform(0.85, 1.1))
        self.lines(paths, width, colour, 0.85)
        if heads: self.shapes(heads, np.stack(hcols), 0.95)

    # ================================================================== small living things
    def fireflies(self, pts, size=1.0, colour='firefly', trails=0, faint=0.3, seed=None):
        """glowing fireflies (unlit): a warm halo, a bright core; a few leave a dotted trail of their path"""
        r = self._r(seed)
        pts = np.asarray(pts, np.float32)
        n = len(pts)
        with self.unlit():
            core_r = r.uniform(0.8, 1.7, n) * size
            st = np.where(r.random(n) < faint, r.uniform(0.08, 0.16, n), r.uniform(0.2, 0.42, n))
            for i in range(n):
                self.glow(pts[i, 0], pts[i, 1], r.uniform(5, 12) * size, colour, st[i])
            self.splat(pts[:, 0], pts[:, 1], core_r, hexc('#fffbe0'), np.clip(st * 2.6, 0.4, 1.0), lit=False)
            for i in range(min(trails, n)):
                a = r.uniform(0, 2 * np.pi); L = r.uniform(40, 90) * size
                ctrl = [(pts[i, 0] - np.cos(a) * L * k + np.sin(a) * L * 0.3 * np.sin(k * 3), pts[i, 1] - np.sin(a) * L * k + np.cos(a) * L * 0.3 * np.sin(k * 3)) for k in np.linspace(0, 1, 5)]
                Q = _resample(spline(np.array(ctrl), 8), 6.0)[1:]
                al = np.linspace(0.55, 0.05, len(Q))
                self.splat(Q[:, 0], Q[:, 1], 0.7 * size, hexc(colour), al, lit=False)

    def butterfly(self, x, y, s=8.0, colour='#e99a3d', tip='#3a2c2a', angle=0.0, open_=1.0, seed=None):
        """a small flat butterfly: fore and hind wings, dark tips, a thin body"""
        r = self._r(seed)
        G = _Polys()
        c, sn = np.cos(angle), np.sin(angle)
        R = lambda P: np.stack([x + P[:, 0] * c - P[:, 1] * sn, y + P[:, 0] * sn + P[:, 1] * c], 1)
        col = hexc(colour)
        for side in (-1, 1):
            fw = np.array([(0, 0), (side * 0.9, -1.0), (side * 1.25, -0.75), (side * 1.05, -0.1)], np.float32) * s * np.array([open_, 1])
            hw = np.array([(0, 0.05), (side * 0.95, 0.15), (side * 0.85, 0.75), (side * 0.25, 0.7)], np.float32) * s * np.array([open_, 1])
            G.add(R(spline(np.vstack([hw, hw[:1]]), 4)), col * 0.9, 1)
            G.add(R(spline(np.vstack([fw, fw[:1]]), 4)), col, 1)
            G.add(R(_ell(side * 1.0 * s * open_, -0.78 * s, 0.22 * s, 0.17 * s, 8)), tip, 1)
        G.add(R(_ell(0, 0.1 * s, 0.1 * s, 0.6 * s, 8)), '#2c2426', 1)
        self._paint([G.group(sort=False)], 3)
        self.lines([R(np.array([(0, -0.5 * s), (-0.3 * s, -1.2 * s)])), R(np.array([(0, -0.5 * s), (0.3 * s, -1.2 * s)]))], 0.5, '#2c2426', 0.8)

    def dragonfly(self, x, y, s=14.0, angle=0.0, colour='#5d8f9a', seed=None):
        """a dragonfly: a slim body, four long glassy wings with a fine edge"""
        c, sn = np.cos(angle), np.sin(angle)
        R = lambda P: np.stack([x + P[:, 0] * c - P[:, 1] * sn, y + P[:, 0] * sn + P[:, 1] * c], 1)
        wings = []
        for side in (-1, 1):
            for off, L in ((-0.1, 1.0), (0.12, 0.9)):
                wings.append(R(_ell(side * L * 0.5 * s, off * s, L * 0.5 * s, 0.12 * s, 14, side * 0.12)))
        self.shapes(wings, '#f1eef4', 0.45)
        self.lines([np.vstack([w, w[:1]]) for w in wings], 0.5, '#4f4a55', 0.55)
        self.shapes([R(_ell(0, 0.55 * s, 0.05 * s + 0.4, 0.62 * s, 8)), R(_ell(0, -0.12 * s, 0.11 * s, 0.14 * s, 8))], colour, 1)

    # ================================================================== characters and props
    def wanderer(self, x, y, s=90.0, facing=1, reach=(0.7, -0.7), colour='cloak', dark='cloak_dark', face='face',
                 mitten='mitten', warm='#f7bf8c', warm_side=-1, seed=None):
        """a small hooded wanderer sitting on the ground (x, y = bottom centre, s = height): felt cloak with a
        floppy hood tip and pompom, round face, dot eyes, blush, one mitten raised toward `reach`. Returns the
        mitten position (to tie a kite string to)."""
        r = self._r(seed)
        f = float(facing)
        P = lambda pts: np.stack([x + np.asarray(pts, np.float32)[:, 0] * s * f, y + np.asarray(pts, np.float32)[:, 1] * s], 1)
        body = spline(np.array([(-0.47, 0.0), (-0.44, -0.2), (-0.37, -0.46), (-0.3, -0.66), (-0.2, -0.8), (-0.04, -0.88),
                                (0.13, -0.86), (0.26, -0.76), (0.34, -0.57), (0.41, -0.32), (0.47, -0.1), (0.49, 0.0),
                                (0.3, 0.03), (0.0, 0.04), (-0.3, 0.03), (-0.47, 0.0)]), 8)
        tip = spline(np.array([(-0.06, -0.86), (-0.22, -0.9), (-0.38, -0.86), (-0.5, -0.75), (-0.55, -0.66),
                               (-0.47, -0.69), (-0.36, -0.76), (-0.22, -0.78), (-0.14, -0.74)]), 6)
        rim_ = _ell(0.08, -0.55, 0.245, 0.225, 30)
        face_ = _ell(0.085, -0.545, 0.2, 0.185, 30)
        # shadow on the grass, boots
        self.shapes([P(_ell(0.1, 0.03, 0.62, 0.1, 20))], '#26222a', 0.28)
        self.shapes([P(_ell(-0.14, 0.0, 0.12, 0.065, 14)), P(_ell(0.24, 0.01, 0.12, 0.065, 14))], 'boot', 1, ss=4)
        # cloak: flat, then felt texture, soft shading, warm rim on the sunset side
        self.shapes([P(tip), P(body)], [hexc(colour) * 0.93, hexc(colour)], 1, ss=4)
        m, sl = self._local([P(body), P(tip)], ss=4)
        h_, w_ = m.shape
        yy = np.linspace(0, 1, h_, dtype=np.float32)[:, None]; xx = np.linspace(0, 1, w_, dtype=np.float32)[None]
        shade = np.clip(0.55 * yy + 0.45 * (xx if f > 0 else 1 - xx) - 0.45, 0, 1)
        self.fill(m * shade * 0.7, dark, sl=sl)
        tex = blur(r.random((h_, w_)).astype(np.float32), 0.7)
        tex = (tex - tex.mean()) / (tex.std() + 1e-6)
        self.fill(m * np.clip(tex - 0.9, 0, 1) * 0.35, dark, sl=sl)
        self.fill(m * np.clip(-tex - 1.1, 0, 1) * 0.25, '#9fb4e0', sl=sl)
        self.lines([P(body)[:-3], P(tip)], max(0.8, s * 0.012), '#2e3a5e', 0.45, wobble=0.25)
        if warm_side:
            edge = np.clip(m - np.roll(m, int(-3 * warm_side), axis=1), 0, 1)
            edge = blur(edge, 1.4) * m * (1 - 0.8 * np.linspace(0, 1, h_)[:, None])
            self.fill(np.clip(edge * 1.2, 0, 0.6), warm, sl=sl)
        # pompom
        pp = P(np.array([(-0.55, -0.66)]))[0]
        self.shapes([_ell(pp[0], pp[1], s * 0.065, s * 0.06, 14)], '#f1e6d6', 1, ss=4)
        # hood rim and face
        self.shapes([P(rim_)], dark, 1, ss=4)
        self.shapes([P(face_)], face, 1, ss=4)
        fm, fsl = self._local([P(face_)], ss=4)
        fy = np.linspace(0, 1, fm.shape[0], dtype=np.float32)[:, None]
        self.fill(fm * np.clip(0.9 - fy * 3, 0, 1) * 0.25, '#7f6a6a', sl=fsl)            # hood shadow on the brow
        # eyes, glints, blush
        e1, e2 = P(np.array([(0.03, -0.555)]))[0], P(np.array([(0.15, -0.555)]))[0]
        er = max(1.4, s * 0.026)
        self.shapes([_ell(e1[0], e1[1], er, er * 1.15, 10), _ell(e2[0], e2[1], er, er * 1.15, 10)], '#2a2226', 1, ss=4)
        self.splat([e1[0] - er * 0.3, e2[0] - er * 0.3], [e1[1] - er * 0.4, e2[1] - er * 0.4], max(0.45, er * 0.32), hexc('#ffffff'), 0.9, lit=True)
        c1, c2 = P(np.array([(-0.03, -0.5)]))[0], P(np.array([(0.21, -0.5)]))[0]
        self.shapes([_ell(c1[0], c1[1], s * 0.045, s * 0.026, 10), _ell(c2[0], c2[1], s * 0.045, s * 0.026, 10)], 'cheek', 0.6, ss=4)
        mo = P(np.array([(0.075, -0.49), (0.09, -0.482), (0.105, -0.49)]))
        self.lines([spline(mo, 4)], max(0.7, s * 0.009), '#5a3d3d', 0.8)
        # arm and mitten toward reach
        rv = np.asarray(reach, np.float32); rv = rv / (np.linalg.norm(rv) + 1e-6)
        sh = np.array([0.2, -0.36], np.float32)
        hand = sh + np.array([rv[0], rv[1]]) * 0.36
        mid = (sh + hand) / 2 + np.array([0.03, 0.03])
        arm = _tube(P(np.array([sh, mid, hand])), s * 0.12, s * 0.1)
        self.shapes([arm], hexc(colour) * 0.8, 1, ss=4)
        self.lines([np.vstack([arm, arm[:1]])], max(0.7, s * 0.01), '#2e3a5e', 0.4)
        hp = P(np.array([hand]))[0]
        self.shapes([_ell(hp[0], hp[1], s * 0.068, s * 0.062, 14)], mitten, 1, ss=4)
        return (float(hp[0]), float(hp[1]))

    def jar_lantern(self, x, y, s=34.0, light='lantern', strength=1.0, flies=4, seed=None):
        """a glass jar of fireflies on the grass (x, y = bottom centre, s = height): glass, lid, wire handle, a warm
        glow inside and a pool of light on the ground"""
        r = self._r(seed)
        w = s * 0.62
        body = spline(np.array([(-0.5, -0.06), (-0.52, -0.5), (-0.46, -0.78), (-0.36, -0.84), (0.36, -0.84), (0.46, -0.78),
                                (0.52, -0.5), (0.5, -0.06), (0.42, 0.0), (-0.42, 0.0), (-0.5, -0.06)]) * [w, s] + [x, y], 6)
        with self.unlit():
            self.glow(x, y - s * 0.1, s * 4.2, light, 0.26 * strength, squash=0.45)       # pool of light on the grass
            self.glow(x, y - s * 0.4, s * 1.8, light, 0.3 * strength)
        self.shapes([_ell(x + s * 0.12, y + 1, s * 0.45, s * 0.07, 16)], '#26222a', 0.25)
        self.shapes([body], 'glass', 0.35)
        with self.unlit():
            self.shapes([_ell(x, y - s * 0.4, w * 0.4, s * 0.32, 20)], '#ffe7a6', 0.85)
            self.glow(x, y - s * 0.42, s * 0.75, light, 0.7 * strength)
            fx = x + r.normal(0, w * 0.18, flies); fy = y - s * 0.42 + r.normal(0, s * 0.14, flies)
            self.splat(fx, fy, 1.1, hexc('#fffef0'), 1.0)
            self.lines([np.vstack([body, body[:1]])], 1.0, '#fbf1da', 0.75)
            self.lines([[(x - w * 0.36, y - s * 0.66), (x - w * 0.38, y - s * 0.2)]], 1.4, '#ffffff', 0.55, taper=0.4)
        lid = np.array([(-0.4, -0.84), (0.4, -0.84), (0.42, -0.98), (-0.42, -0.98)]) * [w, s] + [x, y]
        self.shapes([lid], '#6b6066', 1, ss=4)
        self.lines([[(x - w * 0.4, y - s * 0.9), (x + w * 0.4, y - s * 0.9)]], 0.7, '#9a8e92', 0.8)
        th = np.linspace(np.pi, 2 * np.pi, 20)
        handle = np.stack([x + np.cos(th) * w * 0.42, y - s * 0.95 + np.sin(th) * s * 0.42], 1)
        self.lines([handle], 1.1, '#5b5157', 0.9)

    def kite(self, cx, cy, size=120.0, tilt=0.25, colours=('kite_cream', 'kite'), tail=None, bows=('kite', 'kite_cream', 'lupine'),
             seed=None):
        """a four-panel diamond kite (cx, cy = where the spars cross) with spars, a fine outline, a bridle and a
        streaming tail of bows. tail = list of (dx, dy) control offsets from the bottom point (default: streaming
        down and to the right). Returns the bridle knot (to tie the string to)."""
        r = self._r(seed)
        h = size
        c, s_ = np.cos(tilt), np.sin(tilt)
        R = lambda P: np.stack([cx + np.asarray(P, np.float32)[:, 0] * c - np.asarray(P, np.float32)[:, 1] * s_,
                                cy + np.asarray(P, np.float32)[:, 0] * s_ + np.asarray(P, np.float32)[:, 1] * c], 1)
        top, right, bottom, left, o = (0, -0.36 * h), (0.31 * h, 0.0), (0, 0.66 * h), (-0.31 * h, 0.0), (0, 0)
        tri = [R([o, left, top]), R([o, top, right]), R([o, right, bottom]), R([o, bottom, left])]
        cA, cB = hexc(colours[0]), hexc(colours[1])
        cols = [cA * 1.02, cB, cA * 0.9, cB * 0.84]
        self.shapes(tri, np.clip(np.stack(cols), 0, 1), 1, ss=4, tex=0.04)
        # a faint paper texture: a few fibres and the crease where the paper folds over the spar
        self.lines([R([(left[0] * 0.92, 0), (right[0] * 0.92, 0)]), R([(0, top[1] * 0.9), (0, bottom[1] * 0.94)])], max(1.2, h * 0.016), 'spar', 0.85)
        outline = R([top, right, bottom, left, top])
        self.lines([outline], max(0.8, h * 0.009), '#5a3f3a', 0.7, wobble=0.2)
        hem = R(np.array([top, right, bottom, left, top], np.float32) * 0.9)
        self.lines([hem], 0.6, '#8d4f45', 0.35)
        # bridle: from the top and the low spar point to the knot in front
        knot = R([(-0.16 * h, 0.2 * h)])[0]
        self.lines([[R([(0, -0.25 * h)])[0], knot], [R([(0, 0.42 * h)])[0], knot]], 0.7, '#4c4246', 0.75)
        # tail
        b = R([bottom])[0]
        tail = tail or [(0, 0), (0.12, 0.35), (0.02, 0.7), (0.2, 1.05), (0.12, 1.4), (0.32, 1.75)]
        T = spline(np.asarray(tail, np.float32) * h + b, 10)
        self.lines([T], max(0.8, h * 0.008), '#4c4246', 0.8, wobble=0.5)
        Ts = _resample(T, h * 0.26)[1:]
        bow_polys, bow_cols = [], []
        for i, p in enumerate(Ts):
            dvec = T[min(len(T) - 1, np.argmin(np.linalg.norm(T - p, axis=1)) + 2)] - p
            ang = np.arctan2(dvec[1], dvec[0]) + np.pi / 2
            bs = h * 0.07 * r.uniform(0.85, 1.15)
            ca, sa = np.cos(ang), np.sin(ang)
            for side in (-1, 1):
                pts = np.array([(0, 0), (side * bs, -bs * 0.55), (side * bs * 1.05, bs * 0.55)], np.float32)
                bow_polys.append(np.stack([p[0] + pts[:, 0] * ca - pts[:, 1] * sa, p[1] + pts[:, 0] * sa + pts[:, 1] * ca], 1))
                bow_cols.append(hexc(bows[i % len(bows)]) * (0.9 if side < 0 else 1.0))
        if bow_polys: self.shapes(bow_polys, np.stack(bow_cols), 1, ss=4)
        return (float(knot[0]), float(knot[1]))

    def nightline(self, path, width=0.9, dusk='string', night='#d8d6e2', alpha=0.85, pieces=16):
        """a fine line whose ink follows the sky behind it: dark against dusk, silver against night"""
        Q = _resample(np.asarray(path, np.float32), 2.0)
        k = max(1, min(pieces, len(Q) // 3))
        cut = np.linspace(0, len(Q) - 1, k + 1).astype(int)
        with self.unlit():
            for a, b in zip(cut[:-1], cut[1:]):
                seg = Q[a:b + 1]
                xy = seg[len(seg) // 2]
                n = float(self._Nsky[int(np.clip(xy[1], 0, self.H - 1)), int(np.clip(xy[0], 0, self.W - 1))])
                self.lines([seg], width, mix(dusk, night, min(1.0, n * 1.3)), alpha, caps=False)

    def kite_string(self, p0, p1, sag=40.0, width=0.9, dusk='string', night='#d8d6e2', alpha=0.85):
        """the flying line from the hand to the bridle: a slight sag; dark against dusk, silver against night"""
        p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
        m = (p0 + p1) / 2 + np.array([0, sag], np.float32)
        t = np.linspace(0, 1, 160)[:, None]
        Q = (1 - t) ** 2 * p0 + 2 * (1 - t) * t * m + t ** 2 * p1
        self.nightline(Q, width, dusk, night, alpha)

    # ================================================================== plate: hatching, dimensions, inset
    def leader(self, p0, p1, colour='ink', width=0.8, alpha=0.8, lit=False):
        self.lines([[p0, p1]], width, colour, alpha, lit=lit)

    def wash(self, pts, colour, alpha=0.55, edge=0.35, lit=False, seed=None):
        """a flat watercolour tint inside a polygon, a little darker at its edge, faintly mottled"""
        r = self._r(seed)
        m, sl = self._local([pts], ss=3)
        e = np.clip(m - blur(m, 2.5), 0, 1) * 2
        n = noise2d(m.shape[0], m.shape[1], 14, 2, int(r.integers(1 << 30)))
        self._comp(m * alpha * (0.85 + edge * e + 0.15 * (n - 0.5)), colour, sl, lit)

    def hatch(self, shape, angle=45.0, spacing=5.0, width=0.8, colour='ink', alpha=0.75, jitter=0.6, lit=False, seed=None):
        """parallel hand lines clipped to a shape (polygon points or a full-canvas mask); angle in degrees.
        Call twice with different angles to cross-hatch."""
        r = self._r(seed)
        if isinstance(shape, np.ndarray) and shape.shape == (self.H, self.W):
            ys_, xs_ = np.where(shape > 0.5)
            if not len(ys_): return
            m, oy, ox = shape, 0, 0
            bx0, bx1, by0, by1 = xs_.min(), xs_.max() + 1, ys_.min(), ys_.max() + 1
        else:
            m, sl = self._local([shape], ss=2)
            oy, ox = sl[0].start, sl[1].start
            bx0, by0, bx1, by1 = ox, oy, ox + m.shape[1], oy + m.shape[0]
        a = np.deg2rad(angle); u = np.array([np.cos(a), np.sin(a)]); nv = np.array([-u[1], u[0]])
        corners = np.array([(bx0, by0), (bx1, by0), (bx0, by1), (bx1, by1)], np.float32)
        on = corners @ nv; ou = corners @ u
        paths = []
        k = on.min() + r.uniform(0, spacing)
        while k < on.max():
            o = k + r.normal(0, jitter * 0.3)
            ts = np.arange(ou.min(), ou.max(), 1.0)
            P = ts[:, None] * u + o * nv
            ix = np.clip(P[:, 0].astype(int) - ox, 0, m.shape[1] - 1); iy = np.clip(P[:, 1].astype(int) - oy, 0, m.shape[0] - 1)
            inb = (P[:, 0] >= bx0) & (P[:, 0] < bx1) & (P[:, 1] >= by0) & (P[:, 1] < by1)
            ins = inb & (m[iy, ix] > 0.5)
            dif = np.diff(np.concatenate([[0], ins.astype(int), [0]]))
            for s0, s1 in zip(np.where(dif == 1)[0], np.where(dif == -1)[0]):
                if s1 - s0 < 2: continue
                e0 = s0 + r.uniform(0, 1.2) ; e1 = s1 - 1 - r.uniform(0, 1.2)
                paths.append(np.array([P[0] + u * (e0 + r.normal(0, 0.3)), P[0] + u * (e1 + r.normal(0, 0.3))]))
            k += spacing * r.uniform(0.85, 1.15)
        if paths: self.lines(paths, width, colour, alpha, lit=lit)

    def dimension(self, p0, p1, text=None, offset=16.0, tick=5.0, colour='ink', width=0.8, size=15, alpha=0.85, lit=False,
                  across=False, lead=26.0):
        """a drafting dimension: extension lines, the dimension line with architect's ticks, a small label.
        across=True measures across a member that runs out of view (a spar, a stem): the line crosses it from p0 to
        p1 with ticks on both flanks and is carried out `lead` px beyond p0 to the label (e.g. 'ø 6')."""
        p0 = np.asarray(p0, np.float32); p1 = np.asarray(p1, np.float32)
        u = (p1 - p0) / (np.linalg.norm(p1 - p0) + 1e-6); nv = np.array([-u[1], u[0]], np.float32)
        if across:
            tv = (u + nv) * tick * 0.5
            self.lines([[p0 - u * lead, p1 + u * 6], [p0 - tv, p0 + tv], [p1 - tv, p1 + tv]], width, colour, alpha, lit=lit)
            if text:
                e = p0 - u * (lead + 3)
                self.caption(float(e[0]), float(e[1] + size * 0.32), text, size, colour, alpha, anchor='r' if u[0] >= 0 else 'l',
                             jitter=0.5, lit=lit)
            return
        q0, q1 = p0 + nv * offset, p1 + nv * offset
        paths = [[p0 + nv * 3, q0 + nv * 4], [p1 + nv * 3, q1 + nv * 4], [q0 - u * 3, q1 + u * 3]]
        tv = (u + nv) * tick * 0.5
        paths += [[q0 - tv, q0 + tv], [q1 - tv, q1 + tv]]
        self.lines(paths, width, colour, alpha, lit=lit)
        if text:
            ang = np.degrees(np.arctan2(u[1], u[0]))
            if ang > 90: ang -= 180
            if ang < -90: ang += 180
            th = np.deg2rad(-ang)                                       # caption rotation (ccw)
            up = np.array([-np.sin(th), -np.cos(th)], np.float32)       # where the letters stand up to
            away = nv * (1.0 if offset >= 0 else -1.0)                   # the side away from the object
            centre = (q0 + q1) / 2 + away * (3 + size * 0.42)
            base = centre - up * size * 0.3
            self.caption(float(base[0]), float(base[1]), text, size, colour, alpha, anchor='m', rot=-ang, jitter=0.5, lit=lit)

    def ruler(self, x0, y, x1, h=12.0, step=4.0, colour='ink', fill='#ebe3d6', labels=None, size=11, lit=False):
        """a little scale bar: a light strip, mm ticks, long ticks every five, optional numbers"""
        box = np.array([(x0, y), (x1, y), (x1, y + h), (x0, y + h)], np.float32)
        self.shapes([box], fill, 0.9, lit=lit)
        self.lines([np.vstack([box, box[:1]])], 0.8, colour, 0.85, lit=lit)
        paths = []
        n = int((x1 - x0) / step)
        for i in range(n + 1):
            x = x0 + i * step
            L = h * (0.62 if i % 10 == 0 else 0.45 if i % 5 == 0 else 0.28)
            paths.append([(x, y), (x, y + L)])
        self.lines(paths, 0.6, colour, 0.8, lit=lit)
        if labels:
            for i, lab in labels:
                self.caption(x0 + i * step, y + h + size * 1.2, lab, size, colour, 0.85, anchor='m', jitter=0.4, lit=lit)

    def inset(self, cx, cy, r, draw=None, target=None, label='detail a', sub='not to scale', paper='paper', ring='ink',
              label_colour='caption', size=26, marker=13.0, leader_colour=None, seed=None):
        """the circular magnified view: a paper disc with a faint shadow, `draw(t, cx, cy, r)` clipped inside it, a
        thin double ring, a marker ring on the target with a leader line, and a small handwritten label below"""
        rr = self._r(seed)
        with self.unlit():
            disc = self.ellipse(cx, cy, r)
            sh = blur(np.roll(np.roll(disc, 5, 0), 3, 1), 9)
            self.fill(np.clip(sh - disc, 0, 1) * 0.22, '#2a2032')
            self.fill(disc, paper)
            box = (slice(max(0, int(cy - r - 2)), min(self.H, int(cy + r + 3))), slice(max(0, int(cx - r - 2)), min(self.W, int(cx + r + 3))))
            n = noise2d(box[0].stop - box[0].start, box[1].stop - box[1].start, 9, 3, int(rr.integers(1 << 30)))
            self._comp(disc[box] * (n - 0.5) * 0.12, '#b9a68f', box)
            if draw:
                with self.clipped(disc):
                    draw(self, cx, cy, r)
            th = np.linspace(0, 2 * np.pi, 240)
            circ = lambda R: np.stack([cx + np.cos(th) * R, cy + np.sin(th) * R], 1)
            self.lines([circ(r)], 2.0, ring, 0.9)
            self.lines([circ(r - 5)], 0.7, ring, 0.55)
            if target is not None:
                tx, ty = target
                v = np.array([cx - tx, cy - ty], np.float32); d = float(np.linalg.norm(v)); v /= d + 1e-6
                mk = np.stack([tx + np.cos(th) * marker, ty + np.sin(th) * marker], 1)
                lead = np.array([(tx + v[0] * marker, ty + v[1] * marker), (cx - v[0] * (r + 1), cy - v[1] * (r + 1))], np.float32)
                if leader_colour:
                    self.lines([mk], 0.9, leader_colour, 0.85); self.lines([lead], 0.8, leader_colour, 0.8)
                else:
                    self.nightline(mk, 0.9, ring, 'pale', 0.85, pieces=12); self.nightline(lead, 0.8, ring, 'pale', 0.8)
            if label: self.caption(cx, cy + r + size * 1.5, label, size, label_colour, 0.92, anchor='m')
            if sub: self.caption(cx + size * 0.4, cy + r + size * 2.45, sub, size * 0.66, label_colour, 0.8, anchor='m')

    # ================================================================== handwriting
    _FONT_CACHE = {}

    @staticmethod
    def _hand_font(size):
        key = int(size)
        if key in TwilightStorybook._FONT_CACHE: return TwilightStorybook._FONT_CACHE[key]
        f = None
        env = os.environ.get('INKPAINT_FONT_HAND_LIGHT')
        cands = ([(env, 0)] if env else []) + [('/System/Library/Fonts/Noteworthy.ttc', 0),
                                                ('/System/Library/Fonts/Supplemental/Noteworthy.ttc', 0),
                                                ('/usr/share/fonts/**/*Caveat*Regular*.ttf', 0),
                                                ('/usr/share/fonts/**/*Kalam*Light*.ttf', 0),
                                                ('C:/Windows/Fonts/segoepr.ttf', 0)]
        for pat, idx in cands:
            hits = glob.glob(pat, recursive=True) if pat else []
            if hits:
                try:
                    f = ImageFont.truetype(hits[0], key, index=idx); break
                except OSError:
                    pass
        f = f or load_font('hand', key)
        TwilightStorybook._FONT_CACHE[key] = f
        return f

    def caption(self, x, y, text, size=30, colour='caption', alpha=0.88, anchor='l', jitter=1.0, tracking=0.05, rot=0.0,
                lit=False, seed=None):
        """tiny lowercase handwriting: thin hand font set glyph by glyph (own tilt, baseline wobble, spacing and
        pressure per letter), rendered at 2x, faint pencil texture. (x, y) is the baseline; anchor l / m / r;
        rot in degrees counter-clockwise."""
        r = self._r(seed)
        ss = 2
        S = size * ss
        F = self._hand_font(S)
        adv = [F.getlength(ch) + tracking * S + r.normal(0, 0.02 * S * jitter) for ch in text]
        total = float(sum(adv))
        pad = int(S)
        w = int(total + 2 * pad); h = int(S * 2.4)
        by = int(S * 1.5)
        arr = np.zeros((h, w), np.float32)
        cx = float(pad)
        for ch, a in zip(text, adv):
            if ch.strip():
                gw = int(a + S)
                g = Image.new('L', (gw, h), 0)
                ImageDraw.Draw(g).text((S * 0.5, by + r.normal(0, 0.03 * S * jitter)), ch, font=F, fill=255, anchor='ls')
                ang = r.normal(0, 2.2 * jitter)
                if abs(ang) > 0.05: g = g.rotate(ang, resample=Image.BICUBIC, center=(S * 0.5 + a / 2, by))
                ga = np.asarray(g, np.float32) / 255 * r.uniform(0.78, 1.0)
                xo = int(round(cx - S * 0.5))
                a0, a1 = max(0, xo), min(w, xo + gw)
                arr[:, a0:a1] = np.maximum(arr[:, a0:a1], ga[:, a0 - xo:a1 - xo])
            cx += a
        im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
        ax = {'l': 0.0, 'm': 0.5, 'r': 1.0}[anchor]
        if rot: im = im.rotate(rot, resample=Image.BICUBIC, center=(pad + total * ax, by))
        m = np.asarray(im.reduce(ss), np.float32) / 255
        hh, ww = m.shape
        tx = blur(r.random((hh, ww)).astype(np.float32), 0.6)
        m = m * (0.82 + 0.3 * (tx - 0.5))
        X0 = int(round(x - (pad + total * ax) / ss)); Y0 = int(round(y - by / ss))
        x0, y0 = max(0, X0), max(0, Y0); x1, y1 = min(self.W, X0 + ww), min(self.H, Y0 + hh)
        if x1 <= x0 or y1 <= y0: return
        self._comp(m[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] * alpha, colour, (slice(y0, y1), slice(x0, x1)), lit)

    # ================================================================== finish and output
    def finish(self, grain=1.0, vignette=1.0, bloom=1.0, soft=1.0, edge=0.0, paper='paper'):
        """slight softness, bloom round the lights, grain and paper mottle, a gentle plum vignette and optionally
        a torn paper strip `edge` px tall along the bottom (applied in render)"""
        self.fin = dict(grain=grain, vignette=vignette, bloom=bloom, soft=soft, edge=edge, paper=paper)

    def render(self):
        out = self.C.copy()
        f = self.fin
        if f:
            H, W = self.H, self.W
            if f['soft']:
                sb = np.stack([blur(out[..., i], 0.75) for i in range(3)], -1)
                out = out * (1 - 0.28 * f['soft']) + sb * 0.28 * f['soft']
            if f['bloom']:
                lum = out @ _LUMA
                g = blur(np.clip(lum - 0.74, 0, 1), 14) * 1.3 + blur(np.clip(lum - 0.6, 0, 1), 5) * 0.5
                out = 1 - (1 - out) * (1 - f['bloom'] * g[..., None] * hexc('#fff1d6'))
            if f['grain']:
                if not hasattr(self, '_grain'):
                    r = np.random.default_rng(self.seed + 7)
                    g = r.normal(0, 1, (H, W)).astype(np.float32)
                    g = 0.65 * g + 0.35 * blur(g, 1.0) * 2.0
                    mot = noise2d(H, W, 22, 3, self.seed + 8) - 0.5
                    self._grain = (0.016 * g + 0.03 * mot).astype(np.float32)
                lum = out @ _LUMA
                out = out * (1 + f['grain'] * self._grain * (0.6 + 0.6 * (1 - lum)))[..., None]
            if f['vignette']:
                yy = (np.arange(H, dtype=np.float32)[:, None] / H - 0.5) / 0.62
                xx = (np.arange(W, dtype=np.float32)[None] / W - 0.5) / 0.62
                v = smoothstep(0.35, 1.45, xx * xx + yy * yy) * 0.2 * f['vignette']
                out = out * (1 - v[..., None] * (1 - 0.35 * hexc('#5a3a5c')))
            if f['edge']:
                r = np.random.default_rng(self.seed + 9)
                e = f['edge'] + fbm1d(W, 40, 4, self.seed + 10) * 3.0 + fbm1d(W, 6, 2, self.seed + 12) * 0.9
                yy = np.arange(H, dtype=np.float32)[:, None]
                m = smoothstep(H - e[None] - 0.8, H - e[None] + 0.8, yy)
                pc = hexc(f['paper']) * (1 + 0.025 * (noise2d(H, W, 6, 2, self.seed + 13) - 0.5))[..., None]
                sh = smoothstep(H - e[None] - 5, H - e[None], yy) * (1 - m) * 0.25
                out = out * (1 - sh[..., None])
                out = out * (1 - m[..., None]) + pc * m[..., None]
        return np.clip(out, 0, 1)

    def composite(self):
        return Image.fromarray((self.render() * 255 + 0.5).astype(np.uint8))

    def stage(self, name):
        if not self.keep_stages: return
        im = self.composite()
        if self.stages_dir:
            os.makedirs(self.stages_dir, exist_ok=True)
            im.save(f'{self.stages_dir}/{self._n_stages:02d}_{name}.png', compress_level=1)
        else:
            b = io.BytesIO(); im.save(b, 'PNG', compress_level=1)
            self.stages.append((name, b.getvalue()))
        self._n_stages += 1

    def save(self, path, stages_dir=None, quality=88):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, b) in enumerate(self.stages):
                with open(f'{sd}/{i:02d}_{name}.png', 'wb') as f: f.write(b)
            img.save(f'{sd}/{self._n_stages:02d}_final.png', compress_level=1)
        return img
