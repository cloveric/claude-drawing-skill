"""sunlitgreen -- 夏日光绿 / Sunlit Greenery: bright summer daylight in the anime background-painting / digital
gouache manner -- crisp painted leaf clusters, dappled sunlight, sun-bleached whites with cool shadows, clear water
(numpy + Pillow only).

The look: a high-key summer day, as a background painter for an anime film would paint it. Foliage is built from
many crisp, flat leaf shapes in a few greens -- deep teal-green in the shade, mid green, yellow-lime in the sun, a
pale glint -- with leafy, slightly broken edges and small holes of sky through the canopy. Whites (walls, cushions,
boulders) are sun-bleached: warm cream in the light, cool blue-grey in the shade, often with a thin warm line where
the two meet. Leaf shadows and light patches lie across floors, walls and stones. The sky is a clean saturated blue
with a small cumulus; water is a transparent teal over a pebbled bed with its reflection broken into horizontal
painted strokes. No ink outlines anywhere, hard-edged shapes rather than blur, a faint paper / gouache tooth.

Model
  rasteriser  Everything is a flat polygon of paint. A batch of polygons is drawn by index into a 2x supersampled
              id map (Pillow), the ids look up colour and alpha, and the map is box-averaged back to 1x: crisp,
              anti-aliased edges, painter's order = list order, a few microseconds a leaf, so a picture holds tens
              of thousands of leaves. Edges are subdivided and jittered a little (`_wobble`): painted, not ruled.
  foliage     `canopy()` paints a mass the way a background painter does. Its clumps (cx, cy, rx, ry[, shade])
              are big domes packed with smaller sub-clumps (radius ~ `sub` leaves), each a little dome that catches
              the sun on its lit side; their normals, blended with the big dome's, a little noise, darkening toward
              the bottom and crevice occlusion give a light value, cut into the flat greens at `levels`. Each tone,
              darkest first, is painted as a shape (solid when `fill` is 1 -- a far or middle mass -- or only leaves
              when `fill` is 0 -- a near, leafy tree) whose whole edge is stamped with small leaf clusters pointing
              out of it, so lighter areas lie over darker ones with crisp leafy edges and the silhouette is all
              leaves; `mottle` swaps some leaves one tone up or down (lit and shaded leaves interleave). `airy`
              thins the outer zone of the mass with a coarse noise, so the edge breaks into separate sprays with sky
              between; `holes` punches pale sky chips (the sky colour at that height) inside, with leaves laid back
              over their rims and `twigs` showing in them; `glint` sprinkles pale highlights on the sunniest leaves.
              `spray()` is near foliage: twigs with big single leaves along them and a rosette at the tip, every leaf
              two flat halves split at the midrib (the half toward the sun a tone lighter), sunlit ones with a pale
              midrib and a thin warm edge, laid shaded-first. `grass()` tufts of flat blades, `limb()` trunks and
              branches with a lit stripe and bark grain.
  light       `leaf_shadow()` makes a dappled mask: big shadow masses from a low-frequency field whose edges are
              fringes of leaf clusters pointing outward, loose leaf sprays out in the sun and small sun flecks in the
              shade, squashed for a floor seen in perspective. `shade()` lays a cool shadow over what is painted (a
              blue-grey multiply: cream goes blue-grey, warm stone violet-grey, lime grass teal); `sunlight()` warm
              light (a screen with cream, `tint` for the deeper amber of a late sun); `dapple()` does both on a
              region. Paint a surface in its sunlit colours and lay leaf shadows over it, or in its shade and lay a
              sun patch (a window shape, say) with leaf shadows cut out of it.
  solids      `soft()` puffs any outline into a height field (pillow-like at the edges, `dome` for rounder,
              `facets` random planes for stone), lights it and cuts it into a few flat tones; `levels='q'` puts the
              boundaries at quantiles so every tone shows; `warm` draws a thin warm line on the terminator; `clean`
              dissolves tone islands too small to read as form. `rock()` (a sun-bleached boulder with moss caps; with
              `wet=` it stands in water: a submerged body tinted by the water, its own broken reflection and a
              ripple line), `cushion()` (plump, with painted stripes or checks), `pot()` (cylinder bands), `box()`,
              `panel()`, `face()`, `window()` (white bars with a sunlit face and a cool reveal; returns the glass),
              `curtain()` (sheer, translucent folds), `boards()` (a floor in one-point perspective), `book()`,
              `mug()`, `gradient()` and `strokes()` (visible brush patches inside an area).
  water       `water()` paints a pebbled bed seen through transparent teal (deeper and bluer away from the viewer),
              then the picture above `line` mirrored (`reflect_scale` stretches it), every thin horizontal band
              shifted sideways by its own amount, smeared sideways and flattened to a few paints, and cut by a
              coverage of tapered horizontal strokes -- continuous far away, clustered and sparse near the viewer,
              where the bed shows -- plus a few pale sky glints. Paint everything it mirrors first.
  sky         `sky()` a clean three-stop gradient (remembered, so canopy holes take the sky colour at their height);
              `cloud()` a small cumulus: puffs on a dome with a flat base, the height field merged, three flat tones
              along noise-warped boundaries, a crisp slightly broken edge.
  finish      `finish()` only records the finishing (applied in render, so every stage snapshot matches): bloom on
              the brightest parts, a slight lift toward a pale air colour, a faint paper tooth and fine grain.

API (picture pixel coordinates, y down; colours are PAINTS names, '#rrggbb' or RGB triples; leaf tones a LEAVES
     name -- 'summer' 'gold' 'moss' -- or a list deep -> sunlit; k = min(W, H) / 1000 scales default sizes; light is
     a direction toward the sun: x right, y down, z toward the viewer)
  picture   SunlitGreen(W, H, seed, keep_stages, stages_dir, light); finish(paper, grain, bloom, lift) -- first
  sky       sky(top, mid, bottom, y0, y1, mid_at); sky_at(y); cloud(cx, base, w, h, seed, light, tones, n, levels,
            rough, merge)
  foliage   canopy(clumps, tones, leaf, light, holes, far, sub, levels, noise, bottom_dark, blend, haze,
            edge_leaves, sprinkle, width, shape, hole_size, fill, glint, mottle, twigs, twig_colour, hole_colour,
            airy, seed); spray(stems, leaf, width, tones, rosette, along, droop, bend, light, rim, rim_w, midrib,
            stem, stem_w, far, seed, lit_bias); grass(x0, x1, y, h, n, tones, lean, width, far, curve, seed, ys);
            limb(path, w0, w1, colour, lit, lit_w, alpha, bark, seed)
  light     leaf_shadow(box, cover, leaf, squash, scale, flecks, seed) -> mask; shade(mask, tint, strength, add,
            add_k); sunlight(mask, colour, strength, tint); dapple(region, cover, leaf, squash, scale, flecks,
            mode='shade'|'sun', strength, tint, colour, seed)
  solids    soft(pts, tones, light, bevel, levels, noise, wobble, warm, warm_w, facets, flat, dome, clean, seed,
            clip); rock(cx, cy, rx, ry, tones, facets, rough, flat_base, moss, warm, bevel, wet, seed, light);
            face(pts, colour, alpha, wobble, seed); box(front, top, side, tones); panel(x0, y0, x1, y1, colour,
            lit, shade, bevel); window(x0, y0, x1, y1, cols, rows, frame, bar, colour, lit, shade, depth) -> glass;
            cushion(cx, cy, w, h, tones, round_, tilt, bulge, stripes, light, bevel, seed); curtain(x0, x1, y0,
            y1, folds, tones, alpha, sway, seed); boards(y0, y1, vp, n, x_span, tones, gap, gap_w, seed);
            pot(cx, top, w, h, colour, rim, light); book(cx, cy, w, h, open_, cover, tilt); mug(cx, base, w, h,
            colour, handle, tea); fill(mask, colour, alpha); poly(pts, colour); mask(polys); gradient(mask, c0,
            c1, axis, p0, p1); strokes(mask, n, size, var, angle, spread, aspect, seed)
  water     water(box, line, mask, deep, mid, shallow, reflect, near_reflect, stroke, density, pebbles,
            pebble_size, ripple, sky_glints, reflect_scale, seed) -> mask
  output    render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 92, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from sunlitgreen import SunlitGreen
    g = SunlitGreen(1152, 2048, seed=3); g.finish()
    g.sky(y1=1200); g.cloud(400, 500, 300, 130)
    g.canopy([(700, 400, 260, 200), (900, 600, 220, 180), (560, 640, 200, 150)], leaf=22, fill=0.0, holes=1.0,
             airy=1.0, mottle=0.3)
    m = g.rock(500, 1500, 260, 120, moss=0.3)
    g.dapple(m, cover=0.4, leaf=20)
    g.save('greenery.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, spline, smoothstep, blob_pts

PAINTS = {
    # sky
    'sky_top': '#2a76d4', 'sky': '#4b94e0', 'sky_low': '#9fcbee', 'sky_hole': '#c4def2', 'haze': '#b7d3e4',
    'cloud': '#ffffff', 'cloud_half': '#e8eef8', 'cloud_shade': '#c3d1e6',
    # leaves, deep -> sunlit
    'leaf_deep': '#1d4c47', 'leaf_shade': '#2d6b54', 'leaf_mid': '#55924f', 'leaf_light': '#97c05a',
    'leaf_sun': '#cadf7c', 'leaf_glint': '#f3eb98',
    'bark': '#4a4038', 'bark_light': '#9a8a78',
    # whites (sunlit cream -> cool shade)
    'white_sun': '#fdf7ea', 'white': '#efebe4', 'white_half': '#d9dde4', 'white_shade': '#b4c2d6',
    'white_deep': '#8f9fba',
    # wood, stone, moss
    'wood_sun': '#f0cfa2', 'wood': '#ddb07e', 'wood_shade': '#a68a7c', 'wood_deep': '#7a6670',
    'stone_sun': '#fbf3e6', 'stone': '#f0dcc2', 'stone_half': '#e8c3a0', 'stone_shade': '#a9b1c8',
    'stone_deep': '#7f87a8',
    'warm_edge': '#ec9f6c', 'moss_sun': '#b6d050', 'moss': '#6fa040', 'moss_shade': '#3f7346',
    # water
    'water_deep': '#1a5a58', 'water': '#3a8a80', 'water_shallow': '#9cc2a6', 'pebble': '#a9a676',
    # accents
    'blue_cloth': '#2e5aa8', 'orange_cloth': '#e2733a', 'terracotta': '#cf7a52', 'book_red': '#c8553d',
    'book_teal': '#3e8a8a', 'book_mustard': '#d9a93a', 'paper': '#f4f1ea',
}


# Leaf palettes, deep shade -> sunlit (+ an optional glint): canopy / spray / grass take a name or a list.
LEAVES = {
    'summer': ['leaf_deep', 'leaf_shade', 'leaf_mid', 'leaf_light', 'leaf_sun', 'leaf_glint'],
    'gold': ['#1f4a48', '#30674e', '#5f9148', '#a7bb4a', '#e2cf6a', '#f6eaa0'],       # late-afternoon sun
    'moss': ['moss_shade', 'moss', 'moss_sun', '#d8e88a'],
}


def _leaves(tones, n=None):
    t = LEAVES[tones] if isinstance(tones, str) else (tones or LEAVES['summer'])
    return list(t[:n]) if n else list(t)


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 sRGB 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def mix(a, b, t):
    return hexc(a) * (1 - t) + hexc(b) * t


def _hblur(a, sigma):
    """blur along x only (three box passes)"""
    if sigma <= 0: return a
    w = int(np.sqrt(12 * sigma * sigma / 3 + 1)); w += (w % 2 == 0); rr = w // 2
    out = a.astype(np.float32)
    for _ in range(3):
        c = np.cumsum(np.pad(out, [(0, 0), (rr + 1, rr)], mode='edge'), axis=1, dtype=np.float64)
        out = ((c[:, w:] - c[:, :-w]) / w).astype(np.float32)
    return out


def _rot(pts, ang):
    c, s = np.cos(ang), np.sin(ang)
    return np.stack([pts[..., 0] * c - pts[..., 1] * s, pts[..., 0] * s + pts[..., 1] * c], -1)


def _wobble(pts, amp, r, step=None):
    """subdivide a closed polygon and jitter it a little (a painted, not ruled, edge)"""
    P = np.asarray(pts, np.float32)
    if amp <= 0: return P
    out = []
    n = len(P)
    for i in range(n):
        a, b = P[i], P[(i + 1) % n]
        L = float(np.hypot(*(b - a)))
        k = max(1, int(L / (step or max(amp * 6, 4))))
        t = np.arange(k, dtype=np.float32)[:, None] / k
        out.append(a + (b - a) * t)
    Q = np.concatenate(out)
    d = np.roll(Q, -1, 0) - np.roll(Q, 1, 0)
    nrm = np.stack([-d[:, 1], d[:, 0]], 1) / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-6)
    w = np.convolve(np.concatenate([r.standard_normal(len(Q)), ]), np.ones(3) / 3, 'same')
    return Q + nrm * (w * amp)[:, None]


class SunlitGreen:
    PAINTS = PAINTS

    def __init__(self, W=1152, H=2048, seed=0, keep_stages=True, stages_dir=None, light=(-0.55, -0.7, 0.45)):
        if W * H > 4096 * 4096: raise ValueError('picture larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.k = min(W, H) / 1000
        self.rng = np.random.default_rng(seed)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32)
        self.C[:] = hexc('paper')
        self.light = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.fin = None
        self.sky_stops = None

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    # ================================================================== rasteriser
    def _paint(self, polys, cols, alpha=None, ss=2, target=None, clip=None, mask_only=False):
        """paint polygons in order (later covers earlier). polys: list of (n, 2) arrays in picture px; cols: (N, 3).
        Every polygon's index goes into a supersampled id map (Pillow), the ids look up colour and alpha, and the
        map is box-averaged back to 1x, so edges are crisp but anti-aliased. Returns the coverage over its box."""
        polys = [p for p in polys if len(p) >= 3]
        if not polys: return None
        H, W = self.H, self.W
        allp = np.concatenate(polys)
        x0 = max(int(np.floor(allp[:, 0].min())) - 1, 0); x1 = min(int(np.ceil(allp[:, 0].max())) + 2, W)
        y0 = max(int(np.floor(allp[:, 1].min())) - 1, 0); y1 = min(int(np.ceil(allp[:, 1].max())) + 2, H)
        if x1 <= x0 or y1 <= y0: return None
        w, h = x1 - x0, y1 - y0
        im = Image.new('I', (w * ss, h * ss), 0)
        d = ImageDraw.Draw(im)
        off = np.array([x0, y0], np.float32)
        for i, p in enumerate(polys):
            d.polygon(((p - off) * ss).ravel().tolist(), fill=i + 1)
        ids = np.asarray(im, np.int32)
        N = len(polys)
        if mask_only:
            cov = (ids > 0).astype(np.float32).reshape(h, ss, w, ss).mean((1, 3))
            M = np.zeros((H, W), np.float32); M[y0:y1, x0:x1] = cov
            return M
        tab = np.zeros((N + 1, 4), np.float32)
        tab[1:, :3] = np.asarray(cols, np.float32).reshape(-1, 3)[:N] if len(np.asarray(cols).shape) > 1 \
            else np.asarray(cols, np.float32)[None]
        tab[1:, 3] = 1.0 if alpha is None else np.broadcast_to(np.asarray(alpha, np.float32), (N,))
        tab[:, :3] *= tab[:, 3:4]
        px = tab[ids].reshape(h, ss, w, ss, 4).mean((1, 3))
        A = px[..., 3]
        if clip is not None:
            c = clip[y0:y1, x0:x1]
            A = A * c; px[..., :3] *= c[..., None]
        T = self.C if target is None else target
        T[y0:y1, x0:x1] = T[y0:y1, x0:x1] * (1 - A[..., None]) + px[..., :3]
        return (y0, y1, x0, x1, A)

    def mask(self, polys, ss=2):
        """coverage mask (H, W) of a list of polygons"""
        M = self._paint([np.asarray(p, np.float32) for p in polys], None, ss=ss, mask_only=True)
        return np.zeros((self.H, self.W), np.float32) if M is None else M

    def fill(self, mask, colour, alpha=1.0):
        m = (mask * alpha)[..., None]
        self.C = self.C * (1 - m) + hexc(colour)[None, None] * m

    def poly(self, pts, colour, alpha=1.0, wobble=0.0, seed=None):
        P = np.asarray(pts, np.float32)
        if wobble: P = _wobble(P, wobble * self.k, self._r(seed))
        self._paint([P], hexc(colour)[None], alpha=alpha)

    # ================================================================== shapes
    def _shapes(self, xs, ys, L, Wd, ang, shape, r, jit=0.12):
        """N leaf / chip polygons centred at (xs, ys), length L, width Wd, angle ang (radians, 0 = right)"""
        N = len(xs)
        if N == 0: return np.zeros((0, 3, 2), np.float32)
        L = np.broadcast_to(np.asarray(L, np.float32), (N,)); Wd = np.broadcast_to(np.asarray(Wd, np.float32), (N,))
        if shape == 'leaf':          # pointed tip, rounded base; x along the leaf, centred on its middle
            t = np.linspace(0, 1, 7, dtype=np.float32)
            hw = np.sin(np.pi * t ** 0.72) * (1 - 0.12 * t) * 0.5
            tpl = np.concatenate([np.stack([t, hw], 1), np.stack([t[::-1], -hw[::-1]], 1)[1:-1]]) - [0.5, 0]
            P = np.repeat(tpl[None], N, 0)
        elif shape == 'blade':
            t = np.linspace(0, 1, 5, dtype=np.float32)
            hw = (1 - t) ** 0.9 * 0.5
            tpl = np.concatenate([np.stack([t, hw], 1), np.stack([t[::-1], -hw[::-1]], 1)[1:]])
            P = np.repeat(tpl[None], N, 0)
        else:                        # 'chip' irregular 5-7 gon / 'round'
            K = 7 if shape == 'chip' else 9
            a = np.sort(r.random((N, K)).astype(np.float32), 1) * 2 * np.pi if shape == 'chip' else \
                np.repeat(np.linspace(0, 2 * np.pi, K, endpoint=False, dtype=np.float32)[None], N, 0)
            if shape == 'chip': a = a + np.linspace(0, 2 * np.pi, K, endpoint=False)[None] * 0.6 - a * 0.6
            rad = (0.62 + 0.38 * r.random((N, K))).astype(np.float32) if shape == 'chip' else \
                (0.86 + 0.14 * r.random((N, K))).astype(np.float32) * (1 + 0.12 * np.cos(np.linspace(0, 2 * np.pi, K, endpoint=False)))[None]
            P = np.stack([np.cos(a) * rad * 0.5, np.sin(a) * rad * 0.5], -1)
        P = P * np.stack([L, Wd], 1)[:, None, :]
        if jit: P = P + r.standard_normal(P.shape).astype(np.float32) * jit * Wd[:, None, None] * 0.5
        P = _rot(P, np.asarray(ang, np.float32)[:, None] if np.ndim(ang) else ang)
        return P + np.stack([xs, ys], 1)[:, None, :].astype(np.float32)

    def _clusters(self, cx, cy, n, L, W, ang, spread, shape, r, out=0.55):
        """leaf clusters: n leaves around every centre, radiating near `ang` (+- spread)"""
        m = len(cx)
        if m == 0: return np.zeros((0, 3, 2), np.float32)
        k = r.integers(n[0], n[1] + 1, m)
        idx = np.repeat(np.arange(m), k)
        a = np.asarray(ang, np.float32)[idx] + (r.random(len(idx)) - 0.5) * 2 * spread
        s = (0.75 + 0.5 * r.random(len(idx))).astype(np.float32)
        ln = L * s
        d = ln * (out * (0.5 + 0.7 * r.random(len(idx))))
        xs = cx[idx] + np.cos(a) * d
        ys = cy[idx] + np.sin(a) * d
        if shape == 'mix':
            pick = r.random(len(idx)) < 0.65
            A = self._shapes(xs[pick], ys[pick], ln[pick], ln[pick] * W, a[pick], 'leaf', r)
            B = self._shapes(xs[~pick], ys[~pick], ln[~pick] * 0.78, ln[~pick] * W * 1.25, a[~pick], 'round', r)
            order = np.concatenate([np.nonzero(pick)[0], np.nonzero(~pick)[0]])
            allp = [None] * len(idx)
            for j, p in zip(order, list(A) + list(B)): allp[j] = p
            return allp
        return list(self._shapes(xs, ys, ln, ln * W, a, shape, r))

    # ================================================================== sky
    def sky(self, top='sky_top', mid='sky', bottom='sky_low', y0=0, y1=None, mid_at=0.45):
        """clean saturated summer sky: a smooth vertical gradient (top -> mid -> bottom over y0..y1)"""
        H, W = self.H, self.W
        y1 = H if y1 is None else y1
        stops = [(y0, hexc(top)), (y0 + (y1 - y0) * mid_at, hexc(mid)), (y1, hexc(bottom))]
        self.sky_stops = stops
        ys = np.arange(H, dtype=np.float32)
        col = np.stack([np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops]) for c in range(3)], 1)
        self.C[:] = col[:, None, :]

    def sky_at(self, y):
        if self.sky_stops is None: return np.repeat(hexc('sky_hole')[None], np.size(y), 0)
        st = self.sky_stops
        y = np.atleast_1d(y).astype(np.float32)
        return np.stack([np.interp(y, [s[0] for s in st], [s[1][c] for s in st]) for c in range(3)], 1)

    def cloud(self, cx, base, w, h, seed=None, light=None, tones=('cloud', 'cloud_half', 'cloud_shade'),
              n=30, levels=(0.6, 0.44), rough=0.25, merge=0.05):
        """a small summer cumulus: puffs on a dome with a flat base; their height field is merged (blurred) so the
        puffs melt into one mass, lit by the sun and cut into three flat tones (sunlit white, a pale blue half
        tone, a cool shade underneath) along noise-warped boundaries, with a crisp, slightly broken edge"""
        r = self._r(seed)
        lt = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        u = (r.random(n) * 2 - 1) * 0.92
        xs = cx + u * w / 2
        top = h * np.clip(1 - u * u, 0, 1) ** 0.6
        t = r.random(n)
        rad = h * (0.16 + 0.2 * r.random(n)) * (0.55 + 0.45 * np.clip(1 - np.abs(u), 0, 1))
        ys = base - rad * 0.6 - (top - rad * 0.9).clip(0) * t
        pad = 6
        x0, x1 = int(max(0, (xs - rad).min() - pad)), int(min(self.W, (xs + rad).max() + pad))
        y0, y1 = int(max(0, (ys - rad).min() - pad)), int(min(self.H, base + 2))
        if x1 <= x0 or y1 <= y0: return
        gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        hh, ww = gy.shape
        en = noise2d(hh, ww, max(5, h * 0.06), 3, int(r.integers(1 << 30))) - 0.5
        hgt = np.zeros(gx.shape, np.float32)
        for X, Y, R in zip(xs, ys, rad):
            q = 1 - ((gx - X) / R) ** 2 - ((gy - Y) / R) ** 2 + en * rough
            hgt = np.maximum(hgt, np.sqrt(np.clip(q, 0, 1)) * R)
        cov = (hgt > 0).astype(np.float32) * (gy < base - 1)
        cov = np.maximum(cov, (blur(cov, h * 0.07) > 0.62).astype(np.float32) * (gy < base - 1))   # no pinholes
        cov = smoothstep(0.3, 0.7, blur(cov, 0.6))
        hs = blur(hgt, h * merge)
        gyy, gxx = np.gradient(hs)
        nzv = np.ones_like(hs) * 0.6
        nn = np.sqrt(gxx ** 2 + gyy ** 2 + nzv ** 2)
        lc = np.array([lt[0], lt[1] - 0.25, lt[2] * 0.5]); lc /= np.linalg.norm(lc)
        v = (-gxx * lc[0] - gyy * lc[1] + nzv * lc[2]) / nn
        v = 0.5 + 0.5 * v + (noise2d(hh, ww, max(6, h * 0.1), 3, int(r.integers(1 << 30))) - 0.5) * 0.28
        v -= smoothstep(base - h * 0.7, base, gy) * 0.32
        T = [hexc(c) for c in tones]
        col = np.where((v > levels[0])[..., None], T[0], np.where((v > levels[1])[..., None], T[1], T[2]))
        reg = self.C[y0:y1, x0:x1]
        self.C[y0:y1, x0:x1] = reg * (1 - cov[..., None]) + col * cov[..., None]

    # ================================================================== foliage
    def _subclumps(self, K, sub, r):
        """sub-clumps packed inside the big clumps: (x, y, radius, z of the big dome there)"""
        out = []
        for cx, cy, rx, ry, _ in K:
            n = int(np.pi * rx * ry / (sub * sub) * 1.6) + 3
            a = r.random(n) * 2 * np.pi
            d = np.sqrt(r.random(n)) * 0.92
            xs, ys = cx + np.cos(a) * d * rx, cy + np.sin(a) * d * ry
            rad = sub * (0.7 + 0.6 * r.random(n))
            rad = np.minimum(rad, np.minimum(rx, ry) * 0.6)
            z = np.sqrt(np.clip(1 - d * d, 0, 1)) * min(rx, ry)
            out.append(np.stack([xs, ys, rad, z], 1))
        return np.concatenate(out).astype(np.float32)

    def _field(self, K, S, box, lt, noise, bottom_dark, blend, r, edge):
        """per-pixel coverage, light value and outward direction of a foliage mass inside box"""
        x0, y0, x1, y1 = box
        gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        h, w = gy.shape
        hgt = np.full((h, w), -1e9, np.float32)
        nx = np.zeros((h, w), np.float32); ny = np.zeros((h, w), np.float32)
        bnx = np.zeros((h, w), np.float32); bny = np.zeros((h, w), np.float32)
        bsh = np.zeros((h, w), np.float32)
        en = noise2d(h, w, max(6.0, edge * 2), 2, int(r.integers(1 << 30))) - 0.5
        for (sx, sy, sr, sz) in S:
            i0, i1 = int(max(sy - sr - y0, 0)), int(min(sy + sr - y0 + 1, h))
            j0, j1 = int(max(sx - sr - x0, 0)), int(min(sx + sr - x0 + 1, w))
            if i1 <= i0 or j1 <= j0: continue
            dx = (gx[i0:i1, j0:j1] - sx) / sr; dy = (gy[i0:i1, j0:j1] - sy) / sr
            q = 1 - dx * dx - dy * dy + en[i0:i1, j0:j1] * 0.5
            hz = np.sqrt(np.clip(q, 0, 1)) * sr + sz
            better = (q > 0) & (hz > hgt[i0:i1, j0:j1])
            hgt[i0:i1, j0:j1] = np.where(better, hz, hgt[i0:i1, j0:j1])
            nx[i0:i1, j0:j1] = np.where(better, dx, nx[i0:i1, j0:j1])
            ny[i0:i1, j0:j1] = np.where(better, dy, ny[i0:i1, j0:j1])
        cov = hgt > -1e8
        for cx, cy, rx, ry, shade in K:
            u, v = (gx - cx) / rx, (gy - cy) / ry
            ins = (u * u + v * v < 1.0) & cov
            bnx = np.where(ins, u, bnx); bny = np.where(ins, v, bny); bsh = np.where(ins, shade, bsh)
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
        bz = np.sqrt(np.clip(1 - bnx * bnx - bny * bny, 0, 1))
        Nx, Ny, Nz = nx * blend + bnx * (1 - blend), ny * blend + bny * (1 - blend), nz * blend + bz * (1 - blend) + 0.1
        nn = np.sqrt(Nx * Nx + Ny * Ny + Nz * Nz) + 1e-6
        val = (Nx * lt[0] + Ny * lt[1] + Nz * lt[2]) / nn
        hg = np.where(cov, hgt, 0)
        ao = blur(hg, 6 * self.k) - hg
        top, bot = y0, y1
        val = 0.5 + 0.5 * val
        val += (noise2d(h, w, 40 * self.k, 3, int(r.integers(1 << 30))) - 0.5) * noise
        val -= bottom_dark * (gy - top) / (bot - top + 1) + bsh + np.clip(ao, 0, None) * 0.004 / self.k
        return cov.astype(np.float32), val

    def _tube(self, path, w0, w1=None, per=8):
        """a tapered stroke polygon along a smooth path"""
        P = np.asarray(path, np.float32)
        if len(P) > 2: P = spline(P, per)
        w1 = w0 * 0.4 if w1 is None else w1
        d = np.gradient(P, axis=0)
        nrm = np.stack([-d[:, 1], d[:, 0]], 1) / (np.linalg.norm(d, axis=1, keepdims=True) + 1e-6)
        wd = np.linspace(w0, w1, len(P))[:, None] / 2
        return np.concatenate([P + nrm * wd, (P - nrm * wd)[::-1]]), P, nrm, wd

    def limb(self, path, w0, w1=None, colour='bark', lit='bark_light', lit_w=0.35, alpha=1.0, bark=0.0, seed=None):
        """a trunk or branch: a tapered flat shape with a lit stripe on the sun side; `bark` (0..1) adds short
        darker and lighter marks along the grain"""
        r = self._r(seed)
        poly, P, nrm, wd = self._tube(path, w0, w1)
        self._paint([poly], hexc(colour)[None], alpha=alpha)
        side = 1.0 if (nrm.mean(0) @ self.light[:2]) > 0 else -1.0
        if lit:
            q = _wobble(np.concatenate([P + nrm * wd * side, (P + nrm * wd * side * (1 - 2 * lit_w))[::-1]]),
                        0.8 * self.k, r)
            self._paint([q], hexc(lit)[None], alpha=alpha)
        if bark:
            M = self.mask([poly])
            n = int(len(P) * bark * 6)
            i = r.integers(0, len(P), n)
            u = (r.random(n) * 2 - 1) * 0.85
            d = np.gradient(P, axis=0)[i]
            ang = np.arctan2(d[:, 1], d[:, 0])
            xs, ys = P[i, 0] + nrm[i, 0] * wd[i, 0] * u, P[i, 1] + nrm[i, 1] * wd[i, 0] * u
            ln = wd[i, 0] * (0.8 + 1.6 * r.random(n))
            S = self._shapes(xs, ys, ln, np.maximum(1.6 * self.k, ln * 0.06), ang, 'leaf', r, jit=0.02)
            dark = (u * side < 0.2)
            cols = np.where(dark[:, None], hexc(colour) * 0.84, np.clip(hexc(lit or colour) * 1.04, 0, 1))
            self._paint(list(S), cols, alpha=0.7, clip=M)

    def _twigs(self, K, n, L, col, r, clip=None):
        polys = []
        for _ in range(n):
            i = int(r.integers(len(K)))
            cx, cy, rx, ry = K[i, :4]
            a = r.random() * 2 * np.pi
            p0 = np.array([cx + np.cos(a) * rx * 0.2, cy + np.sin(a) * ry * 0.2])
            b = a + (r.random() - 0.5) * 0.8
            p1 = p0 + np.array([np.cos(b) * rx * 0.55, np.sin(b) * ry * 0.55])
            p2 = p1 + np.array([np.cos(b + 0.4) * rx * 0.35, np.sin(b + 0.4) * ry * 0.35])
            polys.append(self._tube([p0, p1, p2], L * 0.22, L * 0.08)[0])
        if polys:
            self._paint(polys, np.repeat(np.asarray(col)[None], len(polys), 0), clip=clip)

    def canopy(self, clumps, tones=None, leaf=12.0, light=None, holes=0.3, far=0.0, sub=3.5,
               levels=(0.0, 0.38, 0.52, 0.64, 0.78), noise=0.22, bottom_dark=0.22, blend=0.55, haze=None,
               edge_leaves=1.0, sprinkle=0.15, width=0.55, shape='mix', hole_size=1.0, fill=1.0, glint=0.0,
               mottle=0.15, twigs=0, twig_colour='bark', hole_colour=None, airy=0.0, seed=None):
        """a foliage mass painted the way a background painter does it. The clumps (cx, cy, rx, ry[, shade])
        are big domes packed with smaller sub-clumps (radius ~ `sub` leaves), each a little dome of its own that
        catches the sun on its lit side. That light value is cut into a few flat greens (`tones`, deep ->
        sunlit, at `levels`); every tone, from the darkest up, is painted as one flat shape -- shrunk a little
        -- and its whole edge is stamped with leaf clusters that point outward, so each lighter area lies over
        the darker ones with a crisp, leafy edge, and the silhouette against the sky is all leaves. Then small
        sky holes (the sky colour at that height, paled) with a few leaves over their edges."""
        r = self._r(seed)
        K = np.asarray(clumps, np.float32)
        if K.shape[1] == 4: K = np.concatenate([K, np.zeros((len(K), 1), np.float32)], 1)
        lt = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        tones = _leaves(tones, 5) if (tones is None or isinstance(tones, str)) else list(tones)
        hz = hexc(haze or 'haze')
        T = [hexc(t) * (1 - far) + hz * far for t in tones]
        L = leaf * self.k
        S = self._subclumps(K, sub * L, r)
        pad = int(L * 1.5) + 2
        x0 = int(max(0, (S[:, 0] - S[:, 2]).min() - pad)); x1 = int(min(self.W, (S[:, 0] + S[:, 2]).max() + pad))
        y0 = int(max(0, (S[:, 1] - S[:, 2]).min() - pad)); y1 = int(min(self.H, (S[:, 1] + S[:, 2]).max() + pad))
        if x1 <= x0 or y1 <= y0: return
        cov, val = self._field(K, S, (x0, y0, x1, y1), lt, noise, bottom_dark, blend, r, L)
        h, w = cov.shape
        if airy:     # thin the outer zone of the mass into separate sprays with sky between them
            e = blur(cov, L * 3.0 * (0.5 + airy * 0.5))
            N = noise2d(h, w, L * 4.0, 2, int(r.integers(1 << 30)))
            keep = (N + (e - 0.6) * (2.0 / airy)) > 0.45
            cov = cov * keep
        tone = np.digitize(val, levels[1:len(T)]) * (cov > 0)
        reg = self.C[y0:y1, x0:x1]
        for k in range(len(T)):
            R = ((tone >= k) & (cov > 0)).astype(np.float32)
            if R.sum() < 4: continue
            fk = max(fill, 0.7) if k == 0 else fill      # the darkest tone is always a solid base
            er = L * (0.45 if fk >= 0.99 else 0.45 + (1 - fk) * 0.8)
            b = blur(R, er)
            tw = min(0.08, 1.5 / (er * 2.5))
            if fk > 0:
                solid = blur((b > (0.76 if fk >= 0.99 else 0.9)).astype(np.float32), 0.55) * R
                reg[:] = reg * (1 - solid[..., None]) + T[k][None, None] * solid[..., None]
            band = (b > 0.2) & (b < (0.8 if fk >= 0.99 else 0.94)) & (R > 0)
            ys_, xs_ = np.nonzero(band)
            n = int(len(ys_) / (L * L * 0.22) * edge_leaves)
            inner = (b >= (0.8 if fk >= 0.99 else 0.94)) & (R > 0)
            yi, xi = np.nonzero(inner)
            ni = int(len(yi) / (L * L * 0.3) * (1 - fk) * edge_leaves)
            if n + ni <= 0: continue
            pick = r.integers(0, max(len(ys_), 1), n) if len(ys_) else np.zeros(0, int)
            pi_ = r.integers(0, len(yi), ni) if ni > 0 and len(yi) else np.zeros(0, int)
            Y = np.concatenate([ys_[pick], yi[pi_]]) if len(ys_) else yi[pi_]
            X = np.concatenate([xs_[pick], xi[pi_]]) if len(ys_) else xi[pi_]
            n = len(Y)
            if n == 0: continue
            ys, xs = Y.astype(np.float32), X.astype(np.float32)
            gb = np.gradient(b)
            gx = gb[1][Y, X]; gy = gb[0][Y, X]
            ang = np.arctan2(-gy, -gx)
            flat = np.hypot(gx, gy) < 1e-3       # inside: no outward direction, droop down with the light
            ang = np.where(flat, np.pi / 2 + (r.random(n) - 0.5) * 3.0, ang + (r.random(n) - 0.5) * 1.6)
            xs += x0 + np.cos(ang) * L * 0.15 + (r.random(n) - 0.5) * L * 0.3
            ys += y0 + np.sin(ang) * L * 0.15 + (r.random(n) - 0.5) * L * 0.3
            polys = self._clusters(xs, ys, (1, 3), L, width, ang, 0.55, shape, r, out=0.45)
            m = len(polys)
            kk = np.full(m, k)
            if mottle:   # interleave: some leaves one tone darker or lighter than their area
                q = r.random(m)
                kk = np.where(q < mottle * 0.6, k - 1, np.where(q > 1 - mottle * 0.4, k + 1, k))
                kk = np.clip(kk, 0, len(T) - 1)
            cj = np.stack(T)[kk] * (1 + (r.random((m, 1)) - 0.5) * 0.035)
            self._paint(polys, cj)
            reg = self.C[y0:y1, x0:x1]
            if sprinkle and k > 0:      # a few loose leaves of this tone inside the next darker one
                inner = (tone == k - 1) & (cov > 0) & (b > 0.05) & (b < 0.5)
                ys_, xs_ = np.nonzero(inner)
                m = int(len(ys_) / (L * L) * sprinkle)
                if m > 0 and len(ys_):
                    pick = r.integers(0, len(ys_), m)
                    a = r.random(m) * 2 * np.pi
                    P = self._shapes(xs_[pick] + x0 + 0.0, ys_[pick] + y0 + 0.0, L * (0.6 + 0.4 * r.random(m)),
                                     L * width * 0.9, a, 'leaf', r)
                    self._paint(list(P), np.repeat(T[k][None], m, 0))
                    reg = self.C[y0:y1, x0:x1]
        hole_m = np.zeros((h, w), np.float32)
        if holes > 0:
            hn = noise2d(h, w, 7 * L, 2, int(r.integers(1 << 30)))
            ce = blur(cov, L * 1.2)
            edge = (ce > 0.45) & (ce < 0.93)
            okm = (cov > 0) & (tone >= 1) & ((hn > 0.55) | (edge & (hn > 0.35))) & (ce > 0.45)
            ys_, xs_ = np.nonzero(okm)
            n = int(len(ys_) / (L * L * 2.5) * holes)
            if n > 0:
                pick = r.integers(0, len(ys_), n)
                ys, xs = ys_[pick] + y0 + 0.0, xs_[pick] + x0 + 0.0
                if hole_colour is None:
                    cs = self.sky_at(ys) * (1 - far * 0.5) + hz * far * 0.5
                    cs = np.clip(cs * 0.55 + 0.45 * hexc('sky_hole'), 0, 1)
                else:
                    cs = np.repeat(hexc(hole_colour)[None], n, 0)
                sz = L * hole_size * (0.6 + 1.0 * r.random(n) ** 2)
                P = list(self._shapes(xs, ys, sz, sz * 0.8, r.random(n) * np.pi, 'chip', r))
                hm = self.mask(P)
                hole_m = hm[y0:y1, x0:x1]
                self._paint(P, cs)
                if twigs:
                    self._twigs(K, twigs, L, hexc(twig_colour) * (1 - far) + hz * far, r, clip=hm)
                tk = np.repeat(tone[ys_[pick], xs_[pick]], 3)
                a = r.random(n * 3) * 2 * np.pi
                rr = np.repeat(sz, 3) * (0.45 + 0.2 * r.random(n * 3))
                P = self._shapes(np.repeat(xs, 3) + np.cos(a) * rr, np.repeat(ys, 3) + np.sin(a) * rr,
                                 L * (0.7 + 0.4 * r.random(n * 3)), L * width * 0.9, a + np.pi + (r.random(n * 3) - 0.5),
                                 'leaf', r)
                kk = np.clip(tk + (r.random(n * 3) < mottle) * np.where(r.random(n * 3) < 0.5, -1, 1), 0, len(T) - 1)
                self._paint(list(P), np.stack(T)[kk])
        if glint > 0:      # small sun glints on the brightest leaves
            okm = (tone >= len(T) - 1) & (cov > 0)
            ys_, xs_ = np.nonzero(okm)
            n = int(len(ys_) / (L * L * 3) * glint)
            if n > 0:
                pick = r.integers(0, len(ys_), n)
                a = r.random(n) * 2 * np.pi
                sz = L * (0.35 + 0.35 * r.random(n))
                P = self._shapes(xs_[pick] + x0 + 0.0, ys_[pick] + y0 + 0.0, sz, sz * 0.6, a, 'leaf', r)
                self._paint(list(P), np.repeat(hexc('leaf_glint')[None], n, 0))

    # ================================================================== near foliage, grass
    def _leaf_halves(self, x, y, L, Wd, ang, bend, r):
        """the two halves of a pointed leaf (base at (x, y)), split along its midrib, plus the midrib itself"""
        K = 13
        t = np.linspace(0, 1, K, dtype=np.float32)
        hw = np.clip(np.sin(np.pi * t ** 0.68), 0, 1) ** 0.9 * (1 - 0.08 * t) * 0.5 * Wd
        cx = t * L
        cy = bend * L * (t - 0.5) ** 2 * 4 - bend * L
        wob = 1 + 0.035 * r.standard_normal(K)
        up = np.stack([cx, cy - hw * wob], 1)
        mid = np.stack([cx, cy + hw * 0.08 * np.sin(t * np.pi)], 1)
        lo = np.stack([cx, cy + hw * wob[::-1]], 1)
        A = np.concatenate([up, mid[::-1][1:-1]])
        B = np.concatenate([lo, mid[::-1][1:-1]])
        ribw = max(0.5, Wd * 0.028)
        R_ = np.concatenate([mid[:K - 2] + [0, -ribw], (mid[:K - 2] + [0, ribw])[::-1]])
        c, s_ = np.cos(ang), np.sin(ang)
        rot = lambda P: np.stack([P[:, 0] * c - P[:, 1] * s_ + x, P[:, 0] * s_ + P[:, 1] * c + y], 1)
        return rot(A), rot(B), rot(R_), rot(np.concatenate([up, lo[::-1][1:-1]]))

    def spray(self, stems, leaf=40.0, width=0.4, tones=None, rosette=(5, 8), along=0.6, droop=0.35, bend=0.08,
              light=None, rim='warm_edge', rim_w=0.9, midrib=True, stem='bark', stem_w=3.0, far=0.0, seed=None,
              lit_bias=0.0):
        """near foliage: twigs (lists of points, base first) with big single leaves along them and a rosette at the
        tip. Every leaf is two flat halves split at the midrib -- the half turned to the sun one tone lighter --
        sunlit leaves get a pale midrib and a thin warm edge, shaded ones a dark one; leaves are laid from the
        shaded ones (behind) to the sunlit ones (in front)."""
        r = self._r(seed)
        lt = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        tones = _leaves(tones)
        if len(tones) < 6: tones = tones + ['leaf_glint']
        hz = hexc('haze')
        T = np.stack([hexc(t) * (1 - far) + hz * far for t in tones])
        L0 = leaf * self.k
        items = []
        stems_poly = []
        for st in stems:
            P = np.asarray(st, np.float32)
            P = spline(P, 10) if len(P) > 2 else P
            seg = np.hypot(*np.diff(P, axis=0).T); cum = np.concatenate([[0], np.cumsum(seg)])
            stems_poly.append(self._tube(P, stem_w * self.k * 1.6, stem_w * self.k * 0.6)[0])
            tot = cum[-1]
            nodes = np.arange(L0 * 0.5, tot - L0 * 0.3, L0 * along) if along else np.zeros(0)
            side = 1
            for d in nodes:
                i = min(np.searchsorted(cum, d), len(P) - 1)
                tg = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]
                ta = np.arctan2(tg[1], tg[0])
                a = ta + side * (0.55 + 0.5 * r.random()); side = -side
                a = a * (1 - droop) + np.pi / 2 * droop if abs(((a - np.pi / 2 + np.pi) % (2 * np.pi)) - np.pi) < 2.6 else a
                items.append((P[i, 0], P[i, 1], L0 * (0.55 + 0.35 * d / tot) * (0.85 + 0.3 * r.random())
                              * (0.55 + 0.45 * r.random() ** 0.5), a))
            if rosette:
                m = int(r.integers(rosette[0], rosette[1] + 1))
                tg = P[-1] - P[-2]; ta = np.arctan2(tg[1], tg[0])
                for j in range(m):
                    a = ta + (j / max(m - 1, 1) - 0.5) * 2 * (1.2 + 0.5 * r.random()) + (r.random() - 0.5) * 0.3
                    a = a * (1 - droop * 0.5) + np.pi / 2 * droop * 0.5
                    items.append((P[-1, 0], P[-1, 1], L0 * (0.85 + 0.35 * r.random()) * (0.5 + 0.5 * r.random() ** 0.5), a))
        if stems_poly:
            self._paint(stems_poly, np.repeat((hexc(stem) * (1 - far) + hz * far)[None], len(stems_poly), 0))
        if not items: return
        it = np.array(items, np.float32)
        # each leaf's tilt: its normal leans up and along its direction; lit if that faces the sun
        tilt = r.random(len(it)) * 2 - 1
        nx, ny = np.cos(it[:, 3]) * 0.5 + tilt * 0.3, np.sin(it[:, 3]) * 0.3 - 0.6
        nzz = 0.6 + 0.3 * r.random(len(it))
        v = (nx * lt[0] + ny * lt[1] + nzz * lt[2]) / np.sqrt(nx * nx + ny * ny + nzz * nzz)
        v = 0.5 + 0.5 * v + (r.random(len(it)) - 0.5) * 0.5 + lit_bias
        k = np.clip(np.digitize(v, np.quantile(v, [0.18, 0.4, 0.62, 0.84]) if len(v) > 8 else [0.4, 0.52, 0.64, 0.76]), 0, 4)
        order = np.argsort(v + r.random(len(it)) * 0.25)
        polys, cols = [], []
        for i in order:
            x, y, ln, a = it[i]
            A, B, Rb, full = self._leaf_halves(x, y, ln, ln * width, a, bend * (r.random() - 0.3), r)
            # which half faces the sun: the one whose side normal points toward the light in the picture plane
            side_n = np.array([-np.sin(a), np.cos(a)])
            litA = (side_n @ lt[:2]) < 0
            kk = int(k[i])
            hi, lo = min(kk + 1, len(T) - 1), kk
            if rim and kk >= 4:
                c = full.mean(0)
                polys.append(c + (full - c) * (1 + rim_w * self.k / max(ln * width * 0.5, 1)) + self.light[:2] * rim_w * self.k)
                cols.append((hexc(rim) * 0.6 + T[hi] * 0.4) * (1 - far) + hz * far)
            polys += [A, B]
            cols += [T[hi] if litA else T[lo], T[lo] if litA else T[hi]]
            if midrib:
                polys.append(Rb)
                cols.append(T[min(hi + 1, len(T) - 1)] if kk >= 2 else T[max(lo - 1, 0)])
        self._paint(polys, np.stack(cols))

    def grass(self, x0, x1, y, h, n=400, tones=None, lean=0.0, width=5.0, far=0.0, curve=0.25, seed=None, ys=None):
        """tufts of grass blades: narrow curved flat blades, darker ones first, sunlit ones on top"""
        r = self._r(seed)
        tones = _leaves(tones, 5) if (tones is None or isinstance(tones, str)) else list(tones)
        hz = hexc('haze')
        T = np.stack([hexc(t) * (1 - far) + hz * far for t in tones])
        cx = x0 + r.random(n) * (x1 - x0)
        by = (y + (r.random(n) - 0.3) * h * 0.6 * self.k) if ys is None else np.interp(cx, ys[0], ys[1])
        tuft = noise2d(2, max(int(x1 - x0) // 4, 2), 12, 2, int(r.integers(1 << 30)))[0]
        tv = tuft[np.clip(((cx - x0) / 4).astype(int), 0, len(tuft) - 1)]
        ln = h * self.k * (0.25 + 0.95 * r.random(n) * (0.35 + 0.9 * tv))
        a = -np.pi / 2 + lean + (r.random(n) - 0.5) * 1.3
        k = np.clip((r.random(n) * len(T) * (0.6 + 0.6 * ln / ln.max())).astype(int), 0, len(T) - 1)
        order = np.argsort(k + r.random(n) * 1.5)
        polys = []
        for i in order:
            t = np.linspace(0, 1, 6)
            bendv = curve * ln[i] * t ** 2 * np.sign(np.cos(a[i]) + 1e-3)
            px = cx[i] + np.cos(a[i]) * ln[i] * t + bendv
            py = by[i] + np.sin(a[i]) * ln[i] * t
            wd = width * self.k * (1 - t) ** 0.8 * (0.6 + 0.6 * r.random())
            P = np.stack([px, py], 1)
            polys.append(np.concatenate([P + np.stack([wd / 2, 0 * wd], 1), (P - np.stack([wd / 2, 0 * wd], 1))[::-1]]))
        self._paint(polys, T[k[order]])

    # ================================================================== light: dapples, shade, sun
    def leaf_shadow(self, box, cover=0.5, leaf=16.0, squash=1.0, scale=7.0, flecks=0.5, seed=None):
        """a dappled leaf-shadow mask (H, W) in box (x0, y0, x1, y1): big shadow masses from a low-frequency
        field, every edge of them leafy (stamped leaf chips), scattered loose leaf shadows in the sun and small
        sun flecks punched in the shade; `squash` flattens it for a floor seen in perspective"""
        r = self._r(seed)
        x0, y0, x1, y1 = [int(v) for v in box]
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, self.W), min(y1, self.H)
        w, h = x1 - x0, y1 - y0
        L = leaf * self.k
        hh = max(2, int(h / squash))
        D = noise2d(hh, w, scale * L, 3, int(r.integers(1 << 30)))
        D = np.asarray(Image.fromarray(D).resize((w, h), Image.BILINEAR), np.float32)
        t = np.quantile(D, 1 - cover)
        core = blur((D > t).astype(np.float32), 0.6)
        M = np.zeros((self.H, self.W), np.float32)
        M[y0:y1, x0:x1] = core
        gyD, gxD = np.gradient(D)
        polys = []

        def squash_(P, yc):
            P = np.asarray(P, np.float32)
            P[..., 1] = (P[..., 1] - yc) * squash + yc
            return P

        band = (D > t - 0.035) & (D < t + 0.05)
        ys_, xs_ = np.nonzero(band)
        n = int(len(ys_) / (L * L * squash * 0.9))
        if n > 0:        # the edge of every shadow mass is a fringe of leaf clusters pointing out of it
            pick = r.integers(0, len(ys_), n)
            ang = np.arctan2(-gyD[ys_[pick], xs_[pick]], -gxD[ys_[pick], xs_[pick]]) + (r.random(n) - 0.5) * 1.2
            cx, cy = xs_[pick] + x0 + 0.0, ys_[pick] + y0 + 0.0
            P = self._clusters(cx, cy, (2, 4), L * 1.15, 0.42, ang, 0.7, 'leaf', r, out=0.55)
            polys += [squash_(p, p[:, 1].mean()) for p in P]
        loose = (D > t - 0.22) & (D < t - 0.08)
        ys_, xs_ = np.nonzero(loose)
        n = int(len(ys_) / (L * L * squash * 30))
        if n > 0:        # loose sprays of leaf shadows out in the sun
            pick = r.integers(0, len(ys_), n)
            ang = r.random(n) * 2 * np.pi
            P = self._clusters(xs_[pick] + x0 + 0.0, ys_[pick] + y0 + 0.0, (2, 5), L * 1.0, 0.42, ang, 0.9, 'leaf', r,
                               out=0.6)
            polys += [squash_(p, p[:, 1].mean()) for p in P]
        if polys:
            M = np.maximum(M, self.mask(polys))
        if flecks:
            inner = D > t + 0.07
            ys_, xs_ = np.nonzero(inner)
            n = int(len(ys_) / (L * L * squash * 6) * flecks)
            if n > 0:
                pick = r.integers(0, len(ys_), n)
                sz = L * (0.25 + 0.5 * r.random(n) ** 2)
                P = self._shapes(xs_[pick] + x0 + 0.0, ys_[pick] + y0 + 0.0, sz, sz * 0.7, r.random(n) * np.pi, 'round', r)
                P[..., 1] = (P[..., 1] - (ys_[pick] + y0)[:, None]) * squash + (ys_[pick] + y0)[:, None]
                M = M * (1 - self.mask(list(P)))
        return M

    def shade(self, mask, tint=(0.64, 0.72, 0.88), strength=1.0, add='#1a2a5a', add_k=0.04):
        """cool shadow over whatever is painted: multiply by a blue-grey tint (sun-bleached whites go blue-grey,
        warm stone violet-grey, lime grass teal)"""
        m = (np.clip(mask, 0, 1) * strength)[..., None]
        sh = self.C * np.asarray(tint, np.float32)[None, None] + hexc(add)[None, None] * add_k
        self.C = self.C * (1 - m) + sh * m

    def sunlight(self, mask, colour='#fff1cf', strength=0.55, tint=0.0):
        """warm sunlight over whatever is painted: a screen with a warm cream; `tint` (0..1) also multiplies the
        lit result by the colour, for the deeper amber of a late sun"""
        m = (np.clip(mask, 0, 1) * strength)[..., None]
        c = hexc(colour)[None, None]
        lit = 1 - (1 - self.C) * (1 - c * m)
        if tint: lit = lit * (1 - m * tint + c * m * tint)
        self.C = lit

    def dapple(self, region, cover=0.5, leaf=16.0, squash=1.0, scale=7.0, flecks=0.5, mode='shade', strength=1.0,
               tint=(0.64, 0.72, 0.88), colour='#fff1cf', seed=None):
        """dappled light on a painted region (a mask): mode 'shade' lays leaf shadows over a sunlit surface,
        mode 'sun' lays sun patches (leaf-edged, with flecks) over a shaded one. Returns the mask used."""
        ys, xs = np.nonzero(region > 0.01)
        if not len(ys): return None
        box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        M = self.leaf_shadow(box, cover, leaf, squash, scale, flecks, seed) * region
        if mode == 'shade': self.shade(M, tint, strength)
        else: self.sunlight(M, colour, strength)
        return M

    # ================================================================== painted solids
    def soft(self, pts, tones, light=None, bevel=18.0, levels=None, noise=0.1, wobble=0.8, warm=None, warm_w=0.025,
             facets=0, flat=0.0, dome=1.0, clean=0.0, seed=None, clip=None):
        """a solid painted in a few flat tones: the shape's mask is puffed into a height field (pillow-like at its
        edges, optionally cut by `facets` random planes for stone), lit by the sun and cut into the tones
        (dark -> light) along noise-warped boundaries; `warm` paints a thin warm band on the terminator (the
        bounce light at the edge of a sunlit white). Returns the shape's mask."""
        r = self._r(seed)
        lt = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        P = np.asarray(pts, np.float32)
        if wobble: P = _wobble(P, wobble * self.k, r)
        M = self.mask([P])
        if clip is not None: M = M * clip
        ys, xs = np.nonzero(M > 0)
        if not len(ys): return M
        b = int(bevel * self.k * 2.5) + 3
        y0, y1 = max(ys.min() - b, 0), min(ys.max() + b + 1, self.H)
        x0, x1 = max(xs.min() - b, 0), min(xs.max() + b + 1, self.W)
        m = M[y0:y1, x0:x1]
        hgt = blur(m, bevel * self.k) * (1 - flat) + flat * m
        if dome != 1.0: hgt = np.clip(hgt, 0, 1) ** dome
        if facets:
            gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            cx, cy = xs.mean(), ys.mean()
            ext = max(xs.max() - xs.min(), ys.max() - ys.min())
            fh = np.full(m.shape, 9.0, np.float32)
            for _ in range(facets):
                a = r.random() * 2 * np.pi
                d = (r.random() * 0.4 + 0.25) * ext
                pl = 1.2 - ((gx - cx) * np.cos(a) + (gy - cy) * np.sin(a) - d * 0.3) / (ext * 0.6)
                fh = np.minimum(fh, pl)
            hgt = np.minimum(hgt * 1.2, np.clip(fh, 0, None) * 0.9 + hgt * 0.25)
        gyy, gxx = np.gradient(hgt)
        sc = bevel * self.k * 1.6
        nx, ny, nz = -gxx * sc, -gyy * sc, np.ones_like(hgt)
        nn = np.sqrt(nx * nx + ny * ny + nz * nz)
        v = (nx * lt[0] + ny * lt[1] + nz * lt[2]) / nn
        v = 0.5 + 0.5 * v
        if noise: v += (noise2d(y1 - y0, x1 - x0, max(8, bevel * self.k * 1.5), 3, int(r.integers(1 << 30))) - 0.5) * noise * 2
        n = len(tones)
        if isinstance(levels, str):          # 'q': tone boundaries at quantiles of the light inside the shape
            vin = v[m > 0.5]
            levels = list(np.quantile(vin, np.linspace(0.22, 0.8, n - 1))) if len(vin) else None
        levels = levels or list(np.linspace(0.5 + 0.5 * lt[2] - 0.22, 0.5 + 0.5 * lt[2] + 0.16, n - 1))
        idx = np.digitize(v, levels)
        if clean:        # dissolve tone islands smaller than about `clean` px (they read as holes, not as form)
            oh = np.stack([blur((idx == i).astype(np.float32), clean * self.k) for i in range(n)])
            idx = np.where(m > 0.5, oh.argmax(0), idx)
        T = np.stack([hexc(t) for t in tones])
        col = T[np.clip(idx, 0, n - 1)]
        if warm is not None:     # a thin warm line where the shade tone meets the lit ones (bounce light)
            sh = (idx <= 0).astype(np.float32)
            e = (blur(sh, max(0.8, warm_w * 40 * self.k)) - sh)
            wb = (e > 0.12) & (idx >= 1) & (m > 0.5)
            col = np.where(wb[..., None], hexc(warm)[None, None], col)
        reg = self.C[y0:y1, x0:x1]
        self.C[y0:y1, x0:x1] = reg * (1 - m[..., None]) + col * m[..., None]
        return M

    def rock(self, cx, cy, rx, ry, tones=('stone_shade', 'stone_half', 'stone', 'stone_sun'), facets=4,
             rough=0.12, flat_base=0.25, moss=0.0, warm='warm_edge', bevel=None, wet=None, seed=None, light=None):
        """a sun-bleached boulder: an irregular outline (its base flattened), puffed and cut by a few facet
        planes, in four flat tones from cool violet-grey shade to warm cream light, a warm bounce band on the
        terminator, and optional moss on the faces turned up to the sun"""
        r = self._r(seed)
        if wet is not None:      # standing in water: the body continues below, seen through the teal
            Q = blob_pts(cx, cy + ry * 0.5, rx * 1.04, ry * 0.7, rough, 14, int(r.integers(1 << 30)))
            Q[:, 1] = np.maximum(Q[:, 1], cy + ry * (1 - flat_base) - 2)
            self.face(Q, mix('stone_shade', wet, 0.72), wobble=1.0, alpha=0.75)
        P = blob_pts(cx, cy, rx, ry, rough, 11, int(r.integers(1 << 30)), rot=r.random() * 0.6)
        P = _wobble(P, 1.2 * self.k, r, step=max(rx, ry) * 0.12)
        if flat_base: P[:, 1] = np.minimum(P[:, 1], cy + ry * (1 - flat_base))
        lt = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        c0 = 0.5 + 0.5 * lt[2]
        M = self.soft(P, list(tones), light=light, bevel=bevel or max(rx, ry) / self.k * 0.35, facets=facets,
                      warm=warm, seed=int(r.integers(1 << 30)), noise=0.06, wobble=0, clean=max(rx, ry) / self.k * 0.06,
                      levels=[c0 - 0.17, c0 - 0.06, c0 + 0.08])
        if moss:          # moss caps on the faces turned up to the sun: a tiny foliage mass of its own
            ys, xs = np.nonzero(M > 0.5)
            if len(ys):
                top = ys.min()
                k_ = max(2, int(3 + moss * 5))
                cl = []
                for _ in range(k_):
                    mx = cx + (r.random() - 0.5) * rx * 1.3
                    col = xs[np.abs(xs - mx) < 3]
                    if not len(col): continue
                    ty = ys[np.abs(xs - mx) < 3].min()
                    cl.append((mx, ty + ry * 0.08, rx * (0.15 + 0.25 * moss * r.random()), ry * (0.08 + 0.12 * moss)))
                if cl:
                    save = self.C.copy()
                    self.canopy(cl, tones='moss', leaf=5.0, fill=1.0, holes=0,
                                levels=(0.0, 0.45, 0.6, 0.75), sub=2.0, seed=int(r.integers(1 << 30)), noise=0.3,
                                sprinkle=0.1)
                    keep = np.clip(blur(M, 1.0) * 1.6, 0, 1)[..., None]      # hang a little over the edge only
                    self.C = save * (1 - keep) + self.C * keep
        if wet is not None:      # its reflection, broken into sideways-shifted bands, and a bright ripple line
            yb = cy + ry * (1 - flat_base)
            ys_, xs_ = np.nonzero(M > 0.5)
            if len(ys_):
                y0_, x0_, x1_ = int(ys_.min()), int(max(xs_.min() - 20, 0)), int(min(xs_.max() + 20, self.W))
                hh = int(min(yb - y0_, self.H - yb - 1) * 0.8)
                if hh > 4:
                    yy = np.arange(hh)
                    band = (yy / max(3.0, 5 * self.k)).astype(int)
                    sh = (r.standard_normal(band.max() + 1) * 5 * self.k).astype(int)[band]
                    src_y = np.clip((yb - 1 - yy * 1.1).astype(int), 0, self.H - 1)
                    xs = np.arange(x0_, x1_)
                    sx_ = np.clip(xs[None, :] + sh[:, None], 0, self.W - 1)
                    patch = self.C[src_y[:, None], sx_]
                    am = M[src_y[:, None], sx_] * (1 - yy / hh)[:, None] ** 0.7
                    dst = slice(int(yb) + 1, int(yb) + 1 + hh)
                    reg = self.C[dst, x0_:x1_]
                    if reg.shape[0] == hh:
                        a_ = (am * 0.55 * (1 - M[dst, x0_:x1_]))[..., None]
                        col = patch * 0.6 + hexc(wet)[None, None] * 0.4
                        self.C[dst, x0_:x1_] = reg * (1 - a_) + col * a_
            xs_ = np.nonzero(M[int(min(yb - 2, self.H - 1))] > 0.5)[0]
            if len(xs_):
                xa, xb = xs_.min() - rx * 0.12, xs_.max() + rx * 0.12
                n = int(6 + rx / 20)
                sx = xa + r.random(n) * (xb - xa)
                P = self._strokes_h(sx, np.full(n, yb + 2 * self.k) + r.random(n) * 4 * self.k,
                                    rx * (0.15 + 0.3 * r.random(n)), np.full(n, 3.2 * self.k), r)
                self._paint(P, np.repeat(np.clip(mix(wet, '#ffffff', 0.75), 0, 1)[None], n, 0), alpha=0.85)
        return M

    def face(self, pts, colour, alpha=1.0, wobble=0.6, seed=None):
        """a flat painted plane (a wall, a table top, the riser of a step); returns its mask"""
        P = np.asarray(pts, np.float32)
        if wobble: P = _wobble(P, wobble * self.k, self._r(seed))
        self._paint([P], hexc(colour)[None], alpha=alpha)
        return self.mask([P])

    def gradient(self, mask, c0, c1, axis=0, p0=None, p1=None):
        """paint a mask with a smooth gradient between two colours along y (axis 0) or x (axis 1)"""
        ys, xs = np.nonzero(mask > 0)
        if not len(ys): return
        if axis == 0:
            a, b = (ys.min() if p0 is None else p0), (ys.max() if p1 is None else p1)
            t = np.clip((np.arange(self.H, dtype=np.float32) - a) / max(b - a, 1), 0, 1)[:, None, None]
        else:
            a, b = (xs.min() if p0 is None else p0), (xs.max() if p1 is None else p1)
            t = np.clip((np.arange(self.W, dtype=np.float32) - a) / max(b - a, 1), 0, 1)[None, :, None]
        col = hexc(c0)[None, None] * (1 - t) + hexc(c1)[None, None] * t
        m = mask[..., None]
        self.C = self.C * (1 - m) + col * m

    def strokes(self, mask, n=200, size=30.0, var=0.05, angle=0.0, spread=0.4, aspect=0.35, seed=None):
        """visible brush marks inside a painted area: flat, irregular, slightly lighter or darker patches with
        hard edges, laid along `angle` (degrees)"""
        r = self._r(seed)
        ys, xs = np.nonzero(mask > 0.5)
        if not len(ys): return
        pick = r.integers(0, len(ys), n)
        sz = size * self.k * (0.5 + r.random(n))
        a = np.deg2rad(angle) + (r.random(n) - 0.5) * spread
        P = self._shapes(xs[pick] + 0.0, ys[pick] + 0.0, sz, sz * aspect, a, 'chip', r)
        light = r.random(n) < 0.55
        cols = np.where(light[:, None], hexc('#ffffff')[None], hexc('#203060')[None])
        al = np.where(light, var * 1.4, var)
        self._paint(list(P), cols, alpha=al, clip=mask)

    def window(self, x0, y0, x1, y1, cols=2, rows=1, frame=14.0, bar=9.0, colour='white', lit='white_sun',
               shade='white_shade', depth=8.0, wobble=0.5, seed=None):
        """a painted window frame (white): the outer frame and the mullions/transoms as flat bars, each with a
        sunlit face and a cool shaded reveal on the side away from the sun. Returns the glass mask; paint the
        view outside first, then the wall around it, then call this."""
        r = self._r(seed)
        f, b, dp = frame * self.k, bar * self.k, depth * self.k
        bars = [(x0, y0, x1, y0 + f), (x0, y1 - f, x1, y1), (x0, y0, x0 + f, y1), (x1 - f, y0, x1, y1)]
        for i in range(1, cols):
            xm = x0 + (x1 - x0) * i / cols
            bars.append((xm - b / 2, y0, xm + b / 2, y1))
        rws = [j / rows for j in range(1, rows)] if isinstance(rows, int) else list(rows)
        for fr_ in rws:
            ym = y0 + (y1 - y0) * fr_
            bars.append((x0, ym - b / 2, x1, ym + b / 2))
        glass = np.zeros((self.H, self.W), np.float32)
        glass[int(y0 + f):int(y1 - f), int(x0 + f):int(x1 - f)] = 1
        sx = 1 if self.light[0] < 0 else -1          # the reveal shows on the side away from the sun
        for (a0, b0, a1, b1) in bars:
            rect = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
            self.face(rect, colour, wobble=wobble, seed=int(r.integers(1 << 30)))
            # shaded side faces (depth of the bar)
            if a1 - a0 < b1 - b0:     # vertical bar: reveal on the right (or left)
                xr = a1 if sx > 0 else a0
                self.face([(xr, b0), (xr + sx * dp, b0 + dp), (xr + sx * dp, b1), (xr, b1)], shade, wobble=0.3)
            else:                     # horizontal bar: underside
                self.face([(a0, b1), (a1, b1), (a1 + sx * dp * 0.5, b1 + dp), (a0 + sx * dp * 0.5, b1 + dp)], shade,
                          wobble=0.3)
            # a sunlit edge on the top / sun side
            self.face([(a0, b0), (a1, b0), (a1, b0 + max(1.5, (b1 - b0) * 0.12)), (a0, b0 + max(1.5, (b1 - b0) * 0.12))],
                      lit, wobble=0)
        g = glass.copy()
        for (a0, b0, a1, b1) in bars:
            g[int(max(b0 - dp, 0)):int(b1 + dp), int(max(a0 - dp, 0)):int(a1 + dp)] = 0
        return g

    # ================================================================== furniture
    def box(self, front, top=None, side=None, tones=('white', 'white_sun', 'white_half'), wobble=0.6, seed=None):
        """a block seen from the front: its front, top and side quads in flat tones (front, top, side).
        Returns the masks (front, top, side)."""
        r = self._r(seed)
        out = []
        for q, c in ((side, tones[2]), (top, tones[1]), (front, tones[0])):
            out.append(self.face(q, c, wobble=wobble, seed=int(r.integers(1 << 30))) if q is not None else None)
        return out[2], out[1], out[0]

    def panel(self, x0, y0, x1, y1, colour='white_half', lit='white_sun', shade='white_shade', bevel=6.0):
        """a recessed panel (cupboard door, wainscot): a flat field with a shaded bevel on the sun side's top and
        side and a lit bevel opposite"""
        b = bevel * self.k
        sx = self.light[0] < 0
        self.face([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], colour, wobble=0.3)
        self.face([(x0, y0), (x1, y0), (x1 - b, y0 + b), (x0 + b, y0 + b)], shade, wobble=0.2)
        self.face([(x0, y1), (x1, y1), (x1 - b, y1 - b), (x0 + b, y1 - b)], lit, wobble=0.2)
        xa, xb = (x0, x0 + b) if sx else (x1, x1 - b)
        xc, xd = (x1, x1 - b) if sx else (x0, x0 + b)
        self.face([(xa, y0), (xb, y0 + b), (xb, y1 - b), (xa, y1)], shade, wobble=0.2)
        self.face([(xc, y0), (xd, y0 + b), (xd, y1 - b), (xc, y1)], lit, wobble=0.2)

    def cushion(self, cx, cy, w, h, tones=('white_shade', 'white_half', 'white', 'white_sun'), round_=0.4, tilt=0.0,
                bulge=0.08, stripes=None, light=None, bevel=None, seed=None):
        """a plump cushion: a rounded, slightly bulging outline, puffed and shaded in flat tones; `stripes` =
        (colour, n, width 0..1, angle in degrees) lays painted stripes / checks that take the same shading"""
        r = self._r(seed)
        t = np.linspace(0, 2 * np.pi, 64, endpoint=False)
        ex = 2 / max(round_, 0.05)
        ct, st = np.cos(t), np.sin(t)
        x = np.sign(ct) * np.abs(ct) ** (2 / ex) * w / 2
        y = np.sign(st) * np.abs(st) ** (2 / ex) * h / 2
        # corners pulled out a little: plump cushions have ears
        ear = 1 + bulge * np.abs(np.sin(2 * t)) ** 4
        P = np.stack([x * ear, y * ear], 1)
        P = _rot(P, np.deg2rad(tilt)) + [cx, cy]
        bev = bevel or min(w, h) / self.k * 0.3
        M = self.soft(P, list(tones), light=light, bevel=bev, noise=0.05, wobble=0.6, dome=0.6, levels='q',
                      seed=int(r.integers(1 << 30)))
        if stripes:
            colour, n, wd, ang = stripes[:4]
            ys, xs = np.nonzero(M > 0)
            gy, gx = np.mgrid[0:self.H, 0:self.W]
            a_ = np.deg2rad(ang)
            u = ((gx - cx) * np.cos(a_) + (gy - cy) * np.sin(a_)) / max(w, h) * n
            band = (np.abs(((u + 0.5) % 1) - 0.5) < wd / 2).astype(np.float32)
            if len(stripes) > 4:
                u2 = ((gx - cx) * -np.sin(a_) + (gy - cy) * np.cos(a_)) / max(w, h) * n
                band = np.maximum(band, (np.abs(((u2 + 0.5) % 1) - 0.5) < wd / 2).astype(np.float32))
            band = blur(band, 0.5) * M
            val = self.C.mean(-1)
            ref = val[M > 0.5].max() if (M > 0.5).any() else 1
            shadef = np.clip(val / max(ref, 1e-3), 0.4, 1.05)[..., None]
            col = hexc(colour)[None, None] * (0.35 + 0.65 * shadef) + hexc('#1a2a5a')[None, None] * 0.03
            self.C = self.C * (1 - band[..., None]) + col * band[..., None]
        return M

    def curtain(self, x0, x1, y0, y1, folds=5, tones=('white_shade', 'white_half', 'white', 'white_sun'), alpha=0.9,
                sway=0.06, seed=None):
        """a sheer white curtain: vertical folds as flat tone stripes (each fold lit on its sun side, shaded on
        the other), a wavy hem, painted slightly translucent so the light behind glows through"""
        r = self._r(seed)
        T = [hexc(t) for t in tones]
        fw = (x1 - x0) / folds
        polys, cols = [], []
        sx = 1 if self.light[0] < 0 else -1
        for i in range(folds):
            a = x0 + i * fw
            sw = (r.random() - 0.5) * sway * (y1 - y0)
            top = [(a, y0), (a + fw, y0)]
            bot = [(a + fw + sw, y1 + (r.random() - 0.5) * 10 * self.k), (a + sw, y1 + (r.random() - 0.5) * 10 * self.k)]
            polys.append(np.array(top + bot, np.float32)); cols.append(T[2])
            # the fold: a shaded half-stripe and a lit one
            m0 = a + fw * (0.45 + 0.2 * r.random())
            polys.append(np.array([(m0, y0), (a + fw, y0), (a + fw + sw, y1), (m0 + sw, y1)], np.float32))
            cols.append(T[0] if sx > 0 else T[3])
            polys.append(np.array([(m0 - fw * 0.12, y0), (m0, y0), (m0 + sw, y1), (m0 + sw - fw * 0.12, y1)], np.float32))
            cols.append(T[1])
            polys.append(np.array([(a, y0), (a + fw * 0.18, y0), (a + fw * 0.18 + sw, y1), (a + sw, y1)], np.float32))
            cols.append(T[3] if sx > 0 else T[0])
        self._paint([_wobble(p, 0.8 * self.k, r) for p in polys], np.stack(cols), alpha=alpha)
        # a hem shadow and a rod
        self.face([(x0 - 6 * self.k, y0 - 8 * self.k), (x1 + 6 * self.k, y0 - 8 * self.k), (x1 + 6 * self.k, y0 + 4 * self.k),
                   (x0 - 6 * self.k, y0 + 4 * self.k)], 'white_half', wobble=0.3)

    def boards(self, y0, y1, vp, n=14, x_span=None, tones=('wood_shade', 'wood', 'wood_sun'), gap='wood_deep',
               gap_w=1.6, seed=None):
        """a wooden floor in one-point perspective: boards radiating from the vanishing point vp = (x, y) between
        y0 (far) and y1 (near), each with its own flat tone and a thin dark gap, a few end joints"""
        r = self._r(seed)
        x_span = x_span or (-0.6 * self.W, 1.6 * self.W)
        T = [hexc(t) for t in tones]
        vx, vy = vp
        xs = np.linspace(x_span[0], x_span[1], n + 1)
        polys, cols = [], []
        f0 = (y0 - vy) / (y1 - vy)
        for i in range(n):
            a, b = xs[i], xs[i + 1]
            pa0 = (vx + (a - vx) * f0, y0); pb0 = (vx + (b - vx) * f0, y0)
            polys.append(np.array([pa0, pb0, (b, y1), (a, y1)], np.float32))
            cols.append(T[int(r.integers(0, len(T)))] * (1 + (r.random() - 0.5) * 0.05))
        self._paint(polys, np.stack(cols))
        lines = []
        for i in range(n + 1):
            a = xs[i]
            p0 = np.array([vx + (a - vx) * f0, y0]); p1 = np.array([a, y1])
            d = p1 - p0; nn = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6) * gap_w * self.k / 2
            lines.append(np.array([p0 - nn * 0.4, p0 + nn * 0.4, p1 + nn, p1 - nn], np.float32))
            for _ in range(int(r.integers(0, 3))):            # end joints across the board
                t = r.random() ** 0.7
                yj = y0 + (y1 - y0) * t
                fj = (yj - vy) / (y1 - vy)
                if i < n:
                    xa, xb = vx + (xs[i] - vx) * fj, vx + (xs[i + 1] - vx) * fj
                    hw = gap_w * self.k * 0.5 * (0.4 + t)
                    lines.append(np.array([(xa, yj - hw), (xb, yj - hw), (xb, yj + hw), (xa, yj + hw)], np.float32))
        self._paint(lines, np.repeat(hexc(gap)[None], len(lines), 0), alpha=0.55)

    def pot(self, cx, top, w, h, colour='terracotta', rim=0.16, light=None, seed=None):
        """a plant pot: a tapered body and a rim band, shaded as a cylinder in flat vertical bands (sunlit side,
        body, turning edge, cool shade side)"""
        lt = self.light if light is None else np.asarray(light, np.float32) / np.linalg.norm(light)
        c = hexc(colour)
        tones = np.stack([c * np.array([0.7, 0.75, 0.88]), c * 0.9, c, np.clip(c * 1.06 + 0.04, 0, 1)])
        body = [(cx - w / 2, top + h * rim), (cx + w / 2, top + h * rim), (cx + w * 0.38, top + h), (cx - w * 0.38, top + h)]
        rm = [(cx - w * 0.54, top), (cx + w * 0.54, top), (cx + w * 0.52, top + h * rim), (cx - w * 0.52, top + h * rim)]
        M = np.maximum(self.mask([np.asarray(body, np.float32)]), self.mask([np.asarray(rm, np.float32)]))
        gx = np.arange(self.W, dtype=np.float32)[None, :]
        u = np.clip((gx - cx) / (w / 2), -1, 1)
        v = u * -np.sign(lt[0]) * 0.8 + 0.2
        idx = np.digitize(v, [-0.55, -0.05, 0.45])
        col = tones[np.broadcast_to(idx, (self.H, self.W))]
        self.C = self.C * (1 - M[..., None]) + col * M[..., None]
        band = self.mask([np.array([(cx - w * 0.52, top + h * rim), (cx + w * 0.52, top + h * rim),
                                    (cx + w * 0.5, top + h * rim + 5 * self.k), (cx - w * 0.5, top + h * rim + 5 * self.k)],
                                   np.float32)])
        self.fill(band, tones[0] * 0.95, 0.6)
        return M

    def book(self, cx, cy, w, h, open_=True, cover='book_teal', tilt=0.0, seed=None):
        """a book lying on a surface seen from above-front: open (two pale pages bowed at the gutter, faint text
        lines) or closed (a coloured cover and a page edge)"""
        r = self._r(seed)
        def tr(P):
            return _rot(np.asarray(P, np.float32), np.deg2rad(tilt)) + [cx, cy]
        if open_:
            self.face(tr([(-w / 2 - 3, -h / 2 + 4), (w / 2 + 3, -h / 2 + 4), (w / 2 + 3, h / 2 + 5), (-w / 2 - 3, h / 2 + 5)]), cover)
            for sgn, tone in ((-1, 'white_sun'), (1, 'white')):
                xs = np.linspace(0, 1, 10)
                bow = np.sin(xs * np.pi / 2) * h * 0.06
                topp = [(sgn * w / 2 * xx, -h / 2 + h * 0.08 * (1 - xx) - bw) for xx, bw in zip(xs, bow)][::-1]
                botp = [(sgn * w / 2 * xx, h / 2 - bw * 0.5) for xx, bw in zip(xs, bow)]
                self.face(tr(topp + botp), tone, wobble=0.3)
                for j in range(6):
                    yy = -h * 0.3 + j * h * 0.11
                    xa, xb = sgn * w * 0.08, sgn * w * (0.42 - 0.06 * (j == 5))
                    self.face(tr([(min(xa, xb), yy), (max(xa, xb), yy), (max(xa, xb), yy + 1.4 * self.k),
                                  (min(xa, xb), yy + 1.4 * self.k)]), '#b9bcc8', alpha=0.7, wobble=0)
            self.face(tr([(-1.2, -h / 2 + 2), (1.2, -h / 2 + 2), (1.2, h / 2), (-1.2, h / 2)]), 'white_shade', wobble=0)
        else:
            self.face(tr([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]), cover)
            self.face(tr([(-w / 2, h / 2), (w / 2, h / 2), (w / 2, h / 2 + h * 0.12), (-w / 2, h / 2 + h * 0.12)]), 'white')
            self.face(tr([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, -h / 2 + h * 0.1), (-w / 2, -h / 2 + h * 0.1)]),
                      np.clip(hexc(cover) * 1.15 + 0.05, 0, 1))

    def mug(self, cx, base, w, h, colour='white', handle=True, tea='#b06a36', light=None, seed=None):
        """a mug or cup: an elliptical mouth showing the drink, a body shaded in flat tones, a handle"""
        c = hexc(colour)
        tones = [c * np.array([0.7, 0.75, 0.88]), c * 0.93, c, np.clip(c * 1.03 + 0.03, 0, 1)]
        ey = w * 0.18
        if handle:
            sx = 1 if self.light[0] < 0 else -1
            hx = cx + sx * w * 0.5
            self.face([(hx - 2, base - h * 0.75), (hx + sx * w * 0.28, base - h * 0.72), (hx + sx * w * 0.3, base - h * 0.3),
                       (hx - 2, base - h * 0.25), (hx - 2, base - h * 0.38), (hx + sx * w * 0.16, base - h * 0.42),
                       (hx + sx * w * 0.15, base - h * 0.6), (hx - 2, base - h * 0.62)], tones[1], wobble=0.3)
        t = np.linspace(0, np.pi, 16)
        bot = np.stack([cx + np.cos(t) * w / 2, base + np.sin(t) * ey - ey * 0.4], 1)
        body = np.concatenate([[[cx - w / 2, base - h]], [[cx + w / 2, base - h]], bot])
        self.soft(body, tones, light=light, bevel=w / self.k * 0.3, noise=0.02, seed=seed)
        tt = np.linspace(0, 2 * np.pi, 32)
        self.face(np.stack([cx + np.cos(tt) * w / 2, base - h + np.sin(tt) * ey], 1), tones[3], wobble=0)
        self.face(np.stack([cx + np.cos(tt) * w * 0.42, base - h + ey * 0.12 + np.sin(tt) * ey * 0.78], 1), tea, wobble=0)

    # ================================================================== water
    def water(self, box, line, mask=None, deep='water_deep', mid='water', shallow='water_shallow', reflect=0.85,
              near_reflect=0.25, stroke=(90.0, 6.0), density=1.4, pebbles=120, pebble_size=26.0, ripple=6.0,
              sky_glints=0.4, reflect_scale=1.0, seed=None):
        """still, clear water in box (x0, y0, x1, y1) mirroring what is painted above `line`: a pebbled bed seen
        through a transparent teal (deeper and bluer away from the viewer), then the reflection broken into
        horizontal painted strokes -- each a flat colour sampled from the mirrored picture -- that cover more
        toward the far edge (Fresnel) and leave the near water clear, and a few pale sky glints"""
        r = self._r(seed)
        x0, y0, x1, y1 = [int(v) for v in box]
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, self.W), min(y1, self.H)
        w, h = x1 - x0, y1 - y0
        M = np.zeros((self.H, self.W), np.float32); M[y0:y1, x0:x1] = 1
        if mask is not None: M *= mask
        src = self.C.copy()
        gy = np.arange(y0, y1, dtype=np.float32)
        tdep = ((gy - y0) / max(h - 1, 1))[:, None]          # 0 far .. 1 near
        # the bed: teal-olive ground with pebbles
        bed = np.zeros((h, w, 3), np.float32)
        bed[:] = (hexc(shallow) * 0.3 + hexc('pebble') * 0.35 + hexc(mid) * 0.35)[None, None]
        save = self.C
        self.C = np.zeros_like(save); self.C[y0:y1, x0:x1] = bed
        if pebbles:
            n = int(pebbles)
            px = x0 + r.random(n) * w
            py = y0 + (r.random(n) ** 0.6) * h
            sc = (0.4 + 0.8 * (py - y0) / h)
            sz = pebble_size * self.k * sc * (0.6 + 0.8 * r.random(n))
            pc = np.stack([hexc(c) for c in ('#a19a52', '#7f9a50', '#bba062', '#6f8a5c', '#c8b27a', '#5f7a58', '#9aa86a')])
            ci = r.integers(0, len(pc), n)
            P = self._shapes(px, py, sz, sz * (0.5 + 0.2 * r.random(n)), (r.random(n) - 0.5) * 0.5, 'round', r)
            self._paint(list(P), pc[ci])
            P2 = self._shapes(px - sz * 0.12, py - sz * 0.1, sz * 0.62, sz * 0.32, (r.random(n) - 0.5) * 0.5, 'round', r)
            self._paint(list(P2), np.clip(pc[ci] * 1.12 + 0.04, 0, 1))
        bed = self.C[y0:y1, x0:x1].copy()
        self.C = save
        # transparent teal: deep far away, clear near
        tint = hexc(deep)[None, None] * (1 - tdep[..., None]) + hexc(mid)[None, None] * tdep[..., None]
        clear = (0.12 + 0.66 * tdep ** 1.1)[..., None]
        body = bed * clear + tint * (1 - clear)
        reg = self.C[y0:y1, x0:x1]
        m = M[y0:y1, x0:x1][..., None]
        self.C[y0:y1, x0:x1] = reg * (1 - m) + body * m
        # the reflection: the picture mirrored about `line`, every thin horizontal band shifted sideways by its
        # own amount (so colour edges break into horizontal fingers), then cut by a coverage of horizontal
        # strokes -- dense far away, thin near the viewer -- so the clear water shows between them
        Lr, Hr = stroke[0] * self.k, stroke[1] * self.k
        t1 = (gy - y0) / max(h - 1, 1)
        persp = 0.45 + 0.9 * t1
        hb = np.maximum(2.5, Hr * persp * (0.6 + 0.8 * r.random(h)))
        edges = np.cumsum(hb)
        band = np.searchsorted(edges, np.arange(h))
        nb = int(band.max()) + 1
        bdx = (r.standard_normal(nb) * ripple * self.k).astype(np.float32)
        bdy = (r.standard_normal(nb) * ripple * 0.35 * self.k).astype(np.float32)
        wav = (noise2d(nb, w, 40 * self.k, 2, int(r.integers(1 << 30))) - 0.5) * ripple * 2.2 * self.k
        X = np.arange(x0, x1, dtype=np.float32)[None, :] + bdx[band][:, None] * persp[:, None] + wav[band] * persp[:, None]
        Y = line - (gy[:, None] - line) * reflect_scale + bdy[band][:, None]
        Xi = np.clip(X, 0, self.W - 1).astype(int); Yi = np.clip(Y, 0, self.H - 1).astype(int)
        refl = src[Yi, Xi]
        # a painter simplifies a reflection: smear it sideways, then flatten it to a few paints
        sm = np.stack([_hblur(refl[..., c], 9 * self.k) for c in range(3)], -1)
        sm = np.stack([blur(sm[..., c], 1.2 * self.k) for c in range(3)], -1)
        q = Image.fromarray((np.clip(sm, 0, 1) * 255).astype(np.uint8)).quantize(14, method=Image.Quantize.MEDIANCUT,
                                                                                 dither=Image.Dither.NONE)
        refl = np.asarray(q.convert('RGB'), np.float32) / 255
        tint_s = (hexc(deep)[None, None] * (1 - tdep[..., None]) + hexc(mid)[None, None] * tdep[..., None])
        refl = refl * 0.8 + tint_s * 0.2
        n = int(w * h / (Lr * Hr) * density)
        sy = y0 + r.random(n) * h
        tt = (sy - y0) / max(h, 1)
        sx = x0 + r.random(n) * w
        pp = 0.45 + 0.9 * tt
        fr = reflect * (1 - tt) + near_reflect * tt
        cl = noise2d(max(h // 4, 2), max(w // 4, 2), 30 * self.k, 3, int(r.integers(1 << 30)))
        clv = cl[np.clip(((sy - y0) / 4).astype(int), 0, cl.shape[0] - 1), np.clip(((sx - x0) / 4).astype(int), 0, cl.shape[1] - 1)]
        keep = r.random(n) < np.clip(fr * 1.1 * (0.3 + 1.4 * clv), 0, 1)
        P = self._strokes_h(sx[keep], sy[keep], Lr * pp[keep] * (0.4 + 1.6 * r.random(keep.sum()) ** 2),
                            Hr * pp[keep] * (0.7 + 1.2 * r.random(keep.sum())), r)
        cov = self.mask(P)[y0:y1, x0:x1]
        far_fill = smoothstep(0.45, 0.05, tdep) * reflect        # the far water is a continuous mirror
        cov = np.maximum(cov, far_fill)
        a_ = (cov * (0.8 + 0.2 * (1 - tdep)))[..., None] * m
        reg = self.C[y0:y1, x0:x1]
        self.C[y0:y1, x0:x1] = reg * (1 - a_) + refl * a_
        if sky_glints:
            g = int(n * 0.05 * sky_glints)
            gy_ = y0 + r.random(g) ** 1.5 * h
            gx_ = x0 + r.random(g) * w
            tt = (gy_ - y0) / h
            gc = np.clip(self.sky_at(np.clip(line - (gy_ - line) * reflect_scale, 0, self.H - 1)) * 0.6 + 0.4, 0, 1)
            P = self._strokes_h(gx_, gy_, Lr * (0.2 + 0.5 * r.random(g)) * (0.5 + tt), Hr * 0.5 * (0.5 + tt), r)
            self._paint(list(P), gc, alpha=0.9, clip=M)
        return M

    def _strokes_h(self, xs, ys, ln, ht, r):
        """horizontal painted dashes with tapered, slightly ragged ends"""
        n = len(xs)
        K = 8
        t = np.linspace(0, 1, K, dtype=np.float32)
        prof = np.clip(np.sin(np.pi * t), 0, 1) ** 0.45
        P = np.zeros((n, 2 * K, 2), np.float32)
        jt = 1 + 0.25 * r.standard_normal((n, K)).astype(np.float32)
        jb = 1 + 0.25 * r.standard_normal((n, K)).astype(np.float32)
        P[:, :K, 0] = (t[None] - 0.5) * ln[:, None]
        P[:, :K, 1] = -prof[None] * jt * ht[:, None] * 0.5
        P[:, K:, 0] = (t[::-1][None] - 0.5) * ln[:, None]
        P[:, K:, 1] = prof[::-1][None] * jb[:, ::-1] * ht[:, None] * 0.5
        sk = (r.random(n) - 0.5) * 0.06
        P[..., 1] += P[..., 0] * sk[:, None]
        P[..., 0] += xs[:, None]; P[..., 1] += ys[:, None]
        return list(P)

    # ================================================================== output
    def finish(self, paper=1.0, grain=1.0, bloom=0.25, lift=0.03):
        self.fin = dict(paper=paper, grain=grain, bloom=bloom, lift=lift)
        return self

    def render(self):
        out = np.clip(self.C, 0, 1).copy()
        f = self.fin
        if not f: return out
        H, W = self.H, self.W
        if f['bloom']:
            sm = Image.fromarray((out * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
            sm = np.asarray(sm, np.float32) / 255
            br = sm * smoothstep(0.78, 1.0, sm.mean(-1))[..., None]
            for c in range(3): br[..., c] = blur(br[..., c], 8 * self.k)
            up = np.asarray(Image.fromarray((np.clip(br, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                            np.float32) / 255
            out = 1 - (1 - out) * (1 - up * f['bloom'])
        if f['lift']:
            out = out * (1 - f['lift']) + hexc('#dfeaf2')[None, None] * f['lift']
        r = np.random.default_rng(self.seed * 31 + 7)
        if f['paper']:
            g = noise2d(H // 2, W // 2, 3, 2, int(r.integers(1 << 30)))
            g = np.asarray(Image.fromarray(g).resize((W, H), Image.BILINEAR), np.float32) - 0.5
            s = blur(r.standard_normal((H, W)).astype(np.float32), 0.6)
            out *= (1 + (g * 0.035 + s * 0.012) * f['paper'])[..., None]
        if f['grain']:
            out += (r.standard_normal((H, W)).astype(np.float32) * 0.006 * f['grain'])[..., None]
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

    def save(self, path, stages_dir=None, quality=92):
        img = self.composite()
        if str(path).lower().endswith(('.jpg', '.jpeg')): img.save(path, quality=quality, subsampling=0)
        else: img.save(path)
        sd = stages_dir or self.stages_dir
        if sd and self.keep_stages:
            os.makedirs(sd, exist_ok=True)
            for i, (name, b) in enumerate(self.stages):
                with open(f'{sd}/{i:02d}_{name}.png', 'wb') as fh: fh.write(b)
            img.save(f'{sd}/{self._n_stages:02d}_final.png', compress_level=1)
        return img
