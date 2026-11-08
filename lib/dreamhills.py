"""dreamhills — 柔光草丘 / Dreamy Hills: minimalist dreamy-hills wallpapers -- giant soft hills furred with grass, a
luminous surreal colour field on every swell, a deep clean sky, and one tiny walker (numpy + Pillow only).

The look: a tall (1:2) phone wallpaper. Huge rolling hills fill the lower half, every one of them covered in a
velvety fur made of tens of thousands of fine grass strokes that run along the slope; the colour of a hill is a soft
luminous field -- light catching the crests, pastel rim bands where the swells turn away, cool shadowed troughs where
one hill sinks behind the next -- often in surreal colours (lilac and peach, saffron, burnt orange at night). Above,
a clean, slightly graded deep sky takes a big share of the frame, with a sculpted cumulus built from soft puffs, or
stars, a milky way and a comet at night. A dense band of grass blades and a few wildflowers along the bottom, a fine
film grain over everything, and somewhere on a ridge a person a few pixels tall, walking -- the only sense of scale.

Model
  ridges      A hill is its silhouette: a smooth Catmull-Rom ridge through a few control points, sampled per column
              (`Ridge.y`, its slope `Ridge.dy`). Hills are painted back to front; each one is told which ridges lie
              in front of it, so it knows where it disappears (it is not painted, and grows no grass, below them)
              and where its trough is.
  light       Every pixel of a hill gets a pseudo surface normal: on the ridge it is the silhouette's outward normal
              (in the picture plane); going down the face it turns toward the viewer (1 - exp(-d / foot), d = px
              below the ridge) while keeping the side the swell faces (from the ridge slope smoothed over the face,
              so a dome's left half faces left all the way down). `swell` bends it with a noise height field laid
              out in (x, d) -- its contours run parallel to the ridge and become the soft bands of light and shade
              that follow each hill. Two lights: a key (`key_dir`, a 3-vector: x right, y up, z toward the viewer;
              negative z is back light) with a wrapped diffuse term, and a sky fill that grows as the normal turns
              up; a crest rim along the ridge on the key side; trough occlusion above every nearer ridge, which
              takes the key away first (ao squared) and the fill less, so troughs cool as well as darken. The light
              goes through 1 - exp(-E * expo) to a value, and the colour is a palette's `warm` ramp at that value,
              mixed toward its `cool` ramp by the share of the sky fill (a smoothstep, sharp for the night) -- that
              pair of ramps is the luminous, surreal colour field: lilac / peach, saffron / pink, ember / navy.
  fur         The hill is laid down as a smooth base field (a shade darker than the grass, its top edge eroded a
              little below the ridge) and then covered with tens of thousands of fine, tapered, slightly bent
              strokes. Each stroke's direction is the local flow: the silhouette normal on the crest (so the fringe
              stands out against the sky), turning to the up-vector further down, plus wind and a slow swirl --
              grass combed over the swell. Each stroke is lit with its own normal (the surface normal jittered by
              the palette's `jitter`, so blades on one patch fleck warm and cool), the root with the key half
              blocked (darker, cooler), the tip leaning into the key. Strokes are splatted, not drawn: sample points
              along every blade (and across it when it is wider than a pixel), bilinear weights, `np.bincount` into
              coverage and colour sums; blades are sorted by root (jittered by about a blade, or the chunks would
              stripe) and composited in chunks from the back of the hill to the front, so lower blades lie over
              higher ones.
  sky         `sky()` a smooth multi-stop vertical gradient mixed in linear light, wandering a little, with an
              optional sun glow; `cloud()` a cumulus: puffs sit on the front of a dome whose height wanders into
              one or more rounded heads (big puffs low, smaller higher), and small puffs bubble out of its upper
              part (only where they touch the mass); each pixel takes the highest sphere, the height field is
              smoothed a touch and its slope clamped, so puffs melt together and an overlap reads soft, not as a
              crease; lit with a wrapped key, crevice occlusion and a cooler lower part; coverage is the union of
              every puff's own soft disc, the bottom is cut flat. `stars()` power-law brightness, a few with
              four-point spikes; `milky_way()` a bent band of cloudy glow with a brighter core, a dark rift and star
              dust; `comet()` a bright spiked head and a widening tail of fine grainy streaks.
  extras      `trees()` small soft trees on a far ridge, hazed like it; `foreground()` the dense band of tall
              blades at the bottom, dark at the root and backlit at the tip (the taller, the brighter), with
              five-petal wildflowers on the tallest stems, a touch out of focus; `walker()` a tiny person drawn at 8x
              and boxed down (head, hair, shirt, trousers in stride, swinging arms), rim-lit on the key side, with a
              soft shadow, a few blades over the feet and, optionally, a glowing lantern.
  finish      `finish()` only records the finishing (applied in render, so every stage snapshot matches): a slight
              softening, bloom of the brightest parts, a fine luminance-weighted film grain with a little chroma
              (it also dithers the sky, so the gradient never bands).

API (picture pixel coordinates, y down; angles in degrees, 0 = right, 90 = down; colours are PAINTS names,
     '#rrggbb' or RGB triples; k = min(W, H) / 1000 scales default sizes)
  picture   DreamHills(W, H, seed, palette, keep_stages, stages_dir); palette: 'meadow' 'lilac' 'saffron' 'ember'
            or a dict like PALETTES' (sky stops, key_dir, warm / cool ramps, rim, haze, cloud colours, foreground,
            flowers, walker, weights); finish(grain, bloom, soft, chroma) -- before the first mark
  sky       sky(stops, sun_xy, glow, glow_r, glow_strength, wander); cloud(cx, base, w, h, seed, n, detail, light,
            lit, shade, warm, warm_k, alpha, wisp, flat, towers); stars(n, y0, y1, x0, x1, size, bright, spikes,
            colour, fade, seed); sparkle(x, y, size, colour, strength, angle); milky_way(p0, p1, width, bend,
            strength, colour, warm, rift, stars, seed); comet(x, y, angle, length, width, colour, head, strength,
            spread, seed)
  hills     ridge(pts) -> Ridge (.y, .dy, .at(x), .slope(x)); hill(ridge, front, foot, blade, density, warm, cool,
            haze, swell, swell_scale, rim, rim_w, trough, trough_w, wind, flow, lean, seed, jitter, tip, root,
            base_dark, fur)
  extras    trees(ridge, xs, h, colour, light, haze, kind, seed) ('round' / 'tall'); foreground(top, bottom,
            density, blade, colour, tip, flowers, flower_colours, flower_size, wind, blur_px, seed, curve);
            walker(x, y, h, facing, shirt, trousers, skin, hair, stride, rim, shadow, grass, bag, lamp, lamp_glow)
  output    render(); composite(); stage(name); save(path, stages_dir) -- save('x.jpg') quality 92, 4:4:4 chroma

    import sys; sys.path.insert(0, 'lib')
    from dreamhills import DreamHills
    g = DreamHills(1200, 2400, seed=3, palette='lilac'); g.finish()
    g.sky()
    far, near = g.ridge([(-50, 1300), (500, 1180), (1250, 1260)]), g.ridge([(-50, 1700), (700, 1520), (1250, 1600)])
    g.hill(far, front=[near], blade=7, haze=0.3)
    g.hill(near, blade=12)
    g.walker(640, near.at(640), 30)
    g.save('hills.jpg')
"""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, spline, smoothstep

PAINTS = {
    # skies
    'navy': '#081a44', 'night': '#0f2b6e', 'midnight': '#132f7c', 'cobalt': '#1f5fbf', 'azure': '#3a86d8',
    'sky': '#5fa2e6', 'sky_pale': '#a7cdf2', 'cornflower': '#7eb0f2', 'lavender': '#b9b2f0', 'lilac': '#a99cf0',
    'mist': '#dad6f4', 'peach_sky': '#f6c6b4', 'apricot_sky': '#f8b88c', 'rose_sky': '#eab0c4',
    # grounds
    'grass': '#7cc243', 'grass_deep': '#2f7a2c', 'moss': '#4f8f2e', 'cream': '#f4ead8', 'peach': '#f4ad86',
    'apricot': '#f79a5c', 'saffron': '#ffc21c', 'marigold': '#ffad1a', 'ember': '#e0782c', 'rust': '#b4501c',
    'violet': '#5e4fb4', 'indigo': '#1b1f5a', 'plum': '#6a3f86',
    # lights
    'white': '#ffffff', 'warm_white': '#fff4e2', 'gold': '#ffd27a', 'pink_light': '#ffd9ee',
    'ice': '#d4e4ff',
    # figures and flowers
    'shirt_blue': '#2a55d8', 'shirt_red': '#d8452e', 'shirt_white': '#eef0f4', 'shirt_yellow': '#f2b928',
    'trousers': '#1d1f2a', 'skin': '#e9b08c', 'hair': '#2a1d16',
    'cornflower_blue': '#3a5cff', 'flower_white': '#f6f4ff', 'flower_coral': '#ff8a72', 'flower_yellow': '#ffd84a',
}

# A palette is the light of one scene. The ground is coloured from two ramps, dark -> light: `warm` where the key
# light (`key_dir`: x right, y up, z toward the viewer; negative z is back light) does the lighting, `cool` where the
# sky fill does (surfaces turned up and away from the key) -- the surreal colour field comes from these two ramps.
# Also: the sky stops (position 0 top .. 1 bottom of the picture), the crest rim colour, the haze, the clouds, the
# foreground grass (dark root, lit tip), the flowers and the walker's shirt; ks / kf / ka weight key, fill and
# ambient, kr the rim, expo the tone curve, kc the strength of the cool ramp.
PALETTES = {
    'meadow': dict(sky=[(0.0, '#1a56ae'), (0.45, '#3a82d2'), (0.62, '#8cbcea')],
                   key_dir=(0.55, 0.62, 0.45),
                   warm=['#0c3418', '#2a7020', '#62aa2c', '#9ed43e', '#d8f070', '#f6ffc0'],
                   cool=['#0a3022', '#1e6440', '#46925c', '#86c08c', '#c4e6c4', '#eefaf0'],
                   rim='#f2ffb0', haze='#a8cff0', cloud='#ffffff', cloud_shade='#9fb2d8',
                   fg='#123a1c', fg_tip='#9ed44a', flowers=['flower_white', 'flower_yellow'], walker='shirt_red',
                   ks=1.15, kf=0.55, ka=0.08, kr=0.5, expo=0.8, kc=0.55, jitter=0.14),
    'lilac': dict(sky=[(0.0, '#2c6cc8'), (0.32, '#5a96e2'), (0.5, '#a9b9f2'), (0.6, '#f2c8c6')],
                  key_dir=(0.72, 0.38, 0.30),
                  warm=['#463a9e', '#a070b8', '#ea8e7c', '#fbaa80', '#fed0a8', '#fff2e2'],
                  cool=['#3a3ca4', '#7276dc', '#9ea0f4', '#c0baf8', '#e0d6fc', '#f8f2ff'],
                  rim='#fff0d6', haze='#d6cdf6', cloud='#fff8f2', cloud_shade='#b4ace6',
                  fg='#3a3896', fg_tip='#f4b08a', flowers=['flower_white', 'cornflower_blue'], walker='shirt_blue',
                  ks=1.2, kf=0.75, ka=0.06, kr=0.85, expo=0.62, kc=0.85, jitter=0.24),
    'saffron': dict(sky=[(0.0, '#5a9cf0'), (0.45, '#84b6f6'), (0.6, '#b4d0f8')],
                    key_dir=(0.72, 0.6, 0.22),
                    warm=['#a8380a', '#d86a12', '#f8a018', '#ffc824', '#ffe46a', '#fff6c8'],
                    cool=['#b44a1c', '#e2844a', '#f4ae8c', '#f6cce0', '#f8e0f6', '#fff4ff'],
                    rim='#fce4ff', haze='#f6e6c8', cloud='#ffffff', cloud_shade='#aebce6',
                    fg='#1a2c10', fg_tip='#e8a020', flowers=['cornflower_blue', 'cornflower_blue', 'flower_white'],
                    walker='shirt_blue', ks=1.5, kf=0.55, ka=0.08, kr=0.8, expo=0.8, kc=0.7, jitter=0.16, wrap=0.2,
                    kt=(0.35, 0.75)),
    'ember': dict(sky=[(0.0, '#05103a'), (0.4, '#0c2868'), (0.62, '#1a428c')],
                  key_dir=(-0.85, 0.38, -0.05),
                  warm=['#0a0c26', '#3a1a2a', '#8a3416', '#d8661e', '#ffa042', '#ffdc96'],
                  cool=['#080c2a', '#122a66', '#2a52a8', '#5e86d8', '#a8c4f4', '#e4eeff'],
                  rim='#d4e2ff', haze='#1a3a7e', cloud='#c4d0ee', cloud_shade='#36498a',
                  fg='#070c26', fg_tip='#ff9450', flowers=['cornflower_blue', 'flower_white'], walker='shirt_white',
                  ks=2.2, kf=0.45, ka=0.02, kr=0.8, expo=0.6, kc=0.95, wrap=0.12, kt=(0.42, 0.62), jitter=0.07),
}


def hexc(c):
    """'#rrggbb', a PAINTS name or an RGB triple -> float32 sRGB in 0..1"""
    if not isinstance(c, str): return np.asarray(c, np.float32)
    h = PAINTS.get(c, c).lstrip('#')[:6]
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def lin(c):
    """sRGB (0..1, array or colour) -> linear light"""
    c = hexc(c) if isinstance(c, str) or not isinstance(c, np.ndarray) else c
    c = np.clip(c, 0, None)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def srgb(c):
    """linear light -> sRGB (0..1)"""
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055).astype(np.float32)


def _norm(v):
    v = np.asarray(v, np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


class Ridge:
    """a hill silhouette sampled per column: y[x] (picture px, y down) and its slope dy[x]"""

    def __init__(self, y):
        self.y = y.astype(np.float32)
        self.dy = np.gradient(self.y).astype(np.float32)

    def at(self, x):
        return float(np.interp(x, np.arange(len(self.y)), self.y))

    def slope(self, x):
        return float(np.interp(x, np.arange(len(self.y)), self.dy))


class DreamHills:
    PAINTS = PAINTS
    PALETTES = PALETTES

    def __init__(self, W=1200, H=2400, seed=0, palette='lilac', keep_stages=True, stages_dir=None):
        if W * H > 4096 * 4096: raise ValueError('picture larger than 4096 x 4096')
        self.W, self.H, self.seed = W, H, seed
        self.k = min(W, H) / 1000
        self.rng = np.random.default_rng(seed)
        self.P = dict(PALETTES[palette]) if isinstance(palette, str) else dict(palette)
        self.keep_stages, self.stages_dir = keep_stages, stages_dir
        self.stages, self._n_stages = [], 0
        self.C = np.empty((H, W, 3), np.float32)              # the picture, sRGB 0..1; starts as a blank
        self.C[:] = hexc('#efece6')                           # warm-grey canvas (the first draw-on frame)
        self.fin = None
        self.sun_xy = None

    def _r(self, seed=None):
        return np.random.default_rng(int(self.rng.integers(1 << 30)) if seed is None else seed)

    def _pal(self, key, override=None):
        return lin(override if override is not None else self.P[key])

    # ================================================================== sky
    def sky(self, stops=None, sun_xy=None, glow='#fff1dc', glow_r=0.35, glow_strength=0.35, wander=0.02):
        """the sky: a smooth multi-stop vertical gradient (stops: [(pos 0..1 of H, colour)]) mixed in linear light,
        a faint low-frequency wander so it is not a ruler-straight ramp, and an optional sun glow at sun_xy"""
        H, W = self.H, self.W
        stops = stops or self.P['sky']
        pos = np.array([p for p, _ in stops], np.float32) * H
        cols = np.stack([lin(c) for _, c in stops])
        r = self._r()
        yy = np.arange(H, dtype=np.float32)[:, None] + np.zeros((1, W), np.float32)
        if wander:
            yy = yy + (noise2d(H // 8 + 2, W // 8 + 2, 60, 2, int(r.integers(1 << 30))) - 0.5)[
                np.minimum(np.arange(H) // 8, H // 8 + 1)][:, np.minimum(np.arange(W) // 8, W // 8 + 1)] * wander * H
        out = np.empty((H, W, 3), np.float32)
        for c in range(3):
            out[..., c] = np.interp(yy, pos, cols[:, c])
        if sun_xy is not None:
            self.sun_xy = sun_xy
            sx, sy = sun_xy
            gy, gx = np.ogrid[:H, :W]
            d = np.sqrt((gx - sx) ** 2 + ((gy - sy) * 1.15) ** 2) / (glow_r * max(W, H))
            g = np.exp(-d * d) * glow_strength + np.exp(-d * 6) * glow_strength * 0.6
            out += lin(glow)[None, None] * g[..., None].astype(np.float32)
        self.C = srgb(out)
        del out, yy

    # ================================================================== hills
    def ridge(self, pts, per=40):
        """a smooth hill silhouette through control points [(x, y), ...] (x increasing; extend past both edges)"""
        P = np.asarray(pts, np.float32)
        S = spline(P, per)
        order = np.argsort(S[:, 0], kind='stable')
        xs, ys = S[order, 0], S[order, 1]
        return Ridge(np.interp(np.arange(self.W, dtype=np.float32), xs, ys))

    def _ramp(self, ramp, v):
        """sample a dark -> light colour ramp (list of colours) at v in 0..1, in linear light"""
        cols = np.stack([lin(c) for c in ramp])
        xs = np.linspace(0, 1, len(cols))
        out = np.empty(v.shape + (3,), np.float32)
        for c in range(3): out[..., c] = np.interp(v, xs, cols[:, c])
        return out

    def _shade(self, n, d, ao, P, rim_w, rim_k, haze, key_occ=1.0, fill_occ=1.0):
        """light a set of normals (..., 3) in camera space; returns linear RGB (..., 3).
        The light is a value (wrapped key diffuse + sky fill + ambient, times occlusion, plus the crest rim, through
        1 - exp(-E * expo)) and a temperature (the share of the sky fill in it); the colour is the warm ramp at that
        value, mixed toward the cool ramp by the temperature. key_occ / fill_occ scale the two lights separately
        (deep in the fur the key is blocked first, so the roots of the blades go cool and dark, the tips warm)."""
        kd = _norm(P['key_dir'])
        wrap = P.get('wrap', 0.3)
        dif = np.clip((n @ kd + wrap) / (1 + wrap), 0, 1)
        skyl = np.clip(0.5 + 0.5 * n[..., 1], 0, 1)
        # the trough is shaded by the hill in front of it: the key goes first (ao squared), the sky fill less, so
        # the trough above every nearer ridge cools as well as darkens
        ek = dif * P['ks'] * key_occ * ao * ao
        ef = skyl * P['kf'] * fill_occ * ao
        E = ek + ef + P['ka'] * ao
        rimv = 0.0
        if rim_k:
            # crest rim: a band along the ridge on the side that faces the key, brightest where the surface turns away
            side = np.clip(n[..., 0] * kd[0] + n[..., 1] * max(kd[1], 0.0) * 0.6, 0, 1)
            graz = np.clip(1 - np.abs(n[..., 2]), 0, 1) ** 1.5
            rimv = np.exp(-d / rim_w) * (0.35 + 0.65 * side) * (0.5 + 0.5 * graz) * rim_k * P['kr']
            E = E + rimv
        v = 1 - np.exp(-E * P['expo'])
        lo_, hi_ = P.get('kt', (0.25, 0.85))
        t = smoothstep(lo_, hi_, ef / (ek + ef + 1e-4)) * P['kc']
        C = self._ramp(P['warm'], v)
        C += (self._ramp(P['cool'], v) - C) * t[..., None]
        if rim_k:
            C += (self._pal('rim') - C) * np.clip(rimv * 0.45, 0, 0.6)[..., None]
        if haze is not None:
            h = haze if np.ndim(haze) == 0 else haze[..., None]
            C = C * (1 - h) + self._pal('haze') * h
        return C.astype(np.float32)

    def hill(self, ridge, front=(), foot=260, blade=10, density=1.0, warm=None, cool=None, haze=0.0, swell=0.55,
             swell_scale=(320, 90), rim=1.0, rim_w=None, trough=0.45, trough_w=None, wind=12.0, flow=18.0,
             lean=0.7, seed=None, jitter=None, tip=1.1, root=0.72, base_dark=0.86, fur=True):
        """paint one hill: its luminous colour field, then the grass fur over it.
        ridge: Ridge; front: the ridges painted later in front of it (for visibility and the trough);
        foot: px over which the surface turns from the ridge toward the viewer; blade: stroke length in px;
        density: blades per unit area (1 = about 2.5x coverage); haze 0..1; swell: strength of the contour
        bands, swell_scale: (along, down) px; rim / rim_w: crest glow and its depth in px; trough / trough_w: shading
        above a nearer ridge; wind: degrees the fur leans (+ = to the right); flow: degrees of slow swirl;
        lean: how far the crest fringe follows the silhouette normal (0 = straight up); jitter: per-blade normal
        jitter (the warm / cool fleck; default from the palette); tip / root: brightness at the tip / root of every blade."""
        H, W = self.H, self.W
        r = self._r(seed)
        P = dict(self.P)
        if warm is not None: P['warm'] = warm
        if cool is not None: P['cool'] = cool
        rim_w = rim_w or 0.22 * foot
        jitter = P.get('jitter', 0.2) if jitter is None else jitter
        trough_w = trough_w or 0.35 * foot
        ry = ridge.y
        vis = np.full(W, H + 4 * blade, np.float32)
        for f in front: vis = np.minimum(vis, f.y)
        y0 = int(max(0, np.floor(ry.min() - 2.5 * blade)))
        y1 = int(min(H, np.ceil(min(H, vis.max() + 3 * blade))))
        if y1 <= y0: return None
        Hc = y1 - y0
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]
        d = yy - ry[None, :]                                          # px below the ridge
        dist_front = vis[None, :] - yy                                # px above the nearest front ridge
        # ---- normals: silhouette normal on the crest turning toward the viewer down the face
        sl = ridge.dy
        ns = np.stack([sl, np.ones_like(sl)], -1) / np.sqrt(sl * sl + 1)[:, None]       # (x, up), outward
        f = 1 - np.exp(-np.clip(d, 0, None) / foot)
        phi = f * 1.32
        # the side a swell faces persists down its face (a dome's left half faces left all the way down), taken
        # from the ridge slope smoothed over the face, so small wiggles of the ridge do not streak down the hill
        ssm = blur(np.repeat(sl[None, :], 3, 0), 0.45 * foot)[1]
        lat = ssm / np.sqrt(ssm * ssm + 1)
        n = np.empty((Hc, W, 3), np.float32)
        n[..., 0] = ns[None, :, 0] * np.cos(phi) * (1 - f) + lat[None, :] * f * 0.85
        n[..., 1] = ns[None, :, 1] * np.cos(phi)
        n[..., 2] = np.sin(phi)
        # ---- swells: a height field laid out along the ridge (contours parallel to it)
        if swell:
            sa, sd = swell_scale
            dmax = int(np.ceil(np.clip(d, 0, None).max())) + 4
            gh, gw = max(3, int(dmax / sd) + 3), max(3, int(W / sa) + 3)
            g = Image.fromarray(r.random((gh, gw)).astype(np.float32))
            S = np.asarray(g.resize((W, dmax + 2), Image.BICUBIC), np.float32)
            g2 = Image.fromarray(r.random((gh * 2 + 1, gw * 2 + 1)).astype(np.float32))
            S = S + 0.25 * np.asarray(g2.resize((W, dmax + 2), Image.BICUBIC), np.float32)
            dc = np.clip(d, 0, dmax)
            di = dc.astype(np.int32); fr = dc - di                 # linear in d, or every integer step of the
            ax = np.arange(W)[None, :]                             # ridge would streak down the hill
            Sx = S[di, ax] * (1 - fr) + S[np.minimum(di + 1, dmax + 1), ax] * fr
            gy, gx = np.gradient(Sx)
            amp = swell * sd * 1.6 * np.clip(f, 0.25, 1)
            n[..., 0] -= gx * amp
            n[..., 1] += gy * amp
            n /= np.linalg.norm(n, axis=-1, keepdims=True)
            del S, Sx, gy, gx, di
        ao = 1 - trough * np.exp(-np.clip(dist_front, 0, None) / trough_w)
        ao = ao * (1 - 0.18 * smoothstep(0.6, 1.0, f))
        ao = ao.astype(np.float32)
        hz = np.float32(haze)
        field = self._shade(n, np.clip(d, 0, None), ao, P, rim_w, rim, hz)          # linear
        # ---- base: a shade darker than the grass; its top edge sits a little below the ridge
        a = smoothstep(0.15 * blade, 0.9 * blade, d)[..., None]
        base = srgb(field * base_dark)
        Cc = self.C[y0:y1]
        Cc += (base - Cc) * a
        del base, a
        if fur:
            self._fur(ridge, ns, vis, y0, y1, n, ao, P, r, blade, density, wind, flow, lean, jitter, tip, root,
                      rim, rim_w, hz)
        return dict(y0=y0, y1=y1)

    def _fur(self, ridge, ns, vis, y0, y1, n, ao, P, r, blade, density, wind, flow, lean, jitter, tip, root,
             rim, rim_w, hz):
        H, W = self.H, self.W
        ry = ridge.y
        top = ry - 0.15 * blade
        bot = np.minimum(vis + 1.0 * blade, H + blade)
        hgt = np.clip(bot - top, 0, None)
        area = float(hgt.sum())
        Lm = blade
        n_strokes = int(density * 2.5 * area / max(1.0, 0.45 * Lm * max(1.0, 0.11 * Lm)))
        if n_strokes <= 0: return
        # extra roots along the crest so its fringe is dense
        n_crest = int(n_strokes * 0.12)
        p = hgt / hgt.sum()
        xs = r.choice(W, n_strokes, p=p).astype(np.float32) + r.random(n_strokes).astype(np.float32) - 0.5
        xi = np.clip(xs.round().astype(np.int32), 0, W - 1)
        ys = top[xi] + r.random(n_strokes).astype(np.float32) * hgt[xi]
        xc = r.random(n_crest).astype(np.float32) * (W - 1)
        xci = xc.round().astype(np.int32)
        yc = top[xci] + r.random(n_crest).astype(np.float32) ** 1.5 * 1.6 * blade
        xs = np.concatenate([xs, xc]); ys = np.concatenate([ys, yc]); xi = np.concatenate([xi, xci])
        N = len(xs)
        yi = np.clip(ys.round().astype(np.int32) - y0, 0, y1 - y0 - 1)
        dd = np.clip(ys - ry[xi], 0, None)
        # perspective within the hill: blades a little longer lower down the face
        L = blade * (0.62 + 0.76 * r.random(N).astype(np.float32)) * (1 + 0.35 * np.tanh(dd / (8 * blade)))
        # ---- direction: silhouette normal on the crest -> up further down, + wind + a slow swirl
        fdir = 1 - np.exp(-dd / (2.5 * blade))
        nx = ns[xi, 0] * lean * (1 - fdir)
        ny = ns[xi, 1] * lean * (1 - fdir) + (1 - lean * (1 - fdir))
        ang = np.degrees(np.arctan2(-ny, nx))                     # picture angle (y down)
        sw = noise2d(max(4, (y1 - y0) // 16), max(4, W // 16), 14, 2, int(r.integers(1 << 30)))
        swv = (sw[np.clip(yi // 16, 0, sw.shape[0] - 1), np.clip(xi // 16, 0, sw.shape[1] - 1)] - 0.5) * 2
        ang = ang + wind + flow * swv + r.normal(0, 7, N).astype(np.float32)
        th = np.radians(ang)
        DX, DY = np.cos(th).astype(np.float32), np.sin(th).astype(np.float32)
        BEND = (L * (0.08 + 0.18 * r.random(N)) * np.sign(wind + 1e-3)).astype(np.float32)
        W0 = np.clip(L * 0.11, 0.85, None) * (0.8 + 0.4 * r.random(N)).astype(np.float32)
        # ---- colour: each blade lit with its own (jittered) normal
        nb = n[yi, xi] + r.normal(0, jitter, (N, 3)).astype(np.float32)
        nb /= np.linalg.norm(nb, axis=-1, keepdims=True)
        aob = ao[yi, xi]
        v = (0.92 + 0.16 * r.random(N)).astype(np.float32)
        cr = self._shade(nb, dd, aob * v, P, rim_w, rim * 0.4, hz, key_occ=root * 0.8, fill_occ=root)
        CR = srgb(cr)
        ntip = nb + 0.1 * _norm(P['key_dir'])[None, :]          # the tips lean into the light a little
        ntip /= np.linalg.norm(ntip, axis=-1, keepdims=True)
        ct = self._shade(ntip, dd * 0.7, np.minimum(1, aob + 0.1) * v, P, rim_w, rim, hz, key_occ=tip,
                         fill_occ=1.0)
        CT = srgb(ct)
        self._splat_sorted(xs, ys, DX, DY, L, BEND, W0, CR, CT)

    # ================================================================== clouds and the night sky
    def _screen(self, y0, x0, add):
        """screen a linear-light patch (h, w, 3) onto the picture at (y0, x0), clipped to the picture"""
        h, w = add.shape[:2]
        ya, xa = max(0, y0), max(0, x0)
        yb, xb = min(self.H, y0 + h), min(self.W, x0 + w)
        if yb <= ya or xb <= xa: return
        a = add[ya - y0:yb - y0, xa - x0:xb - x0]
        Cc = self.C[ya:yb, xa:xb]
        Cl = lin(Cc)
        Cc[:] = srgb(1 - (1 - Cl) * (1 - np.clip(a, 0, 1)))

    def _over(self, y0, x0, col, a):
        """lay sRGB colour (h, w, 3) with alpha (h, w) over the picture at (y0, x0), clipped"""
        h, w = a.shape
        ya, xa = max(0, y0), max(0, x0)
        yb, xb = min(self.H, y0 + h), min(self.W, x0 + w)
        if yb <= ya or xb <= xa: return
        aa = a[ya - y0:yb - y0, xa - x0:xb - x0, None]
        cc = col[ya - y0:yb - y0, xa - x0:xb - x0]
        Cc = self.C[ya:yb, xa:xb]
        Cc += (cc - Cc) * aa

    def cloud(self, cx, base, w, h, seed=None, n=70, detail=160, light=(0.55, 0.75, 0.35), lit=None, shade=None,
              warm=None, warm_k=0.35, alpha=1.0, wisp=0.35, flat=1.0, towers=2):
        """a cumulus of soft puffs. The mass is a dome (w wide, h tall above `base`, its height wandering along x so
        it grows `towers` rounded heads); puffs sit on the front of the dome with their centres a little inside it
        (big ones low, smaller ones higher), and a second scale of small puffs bubbles on the upper part
        (cauliflower). Every pixel takes the highest sphere; the height field is smoothed a touch so the puffs
        melt together, its normal is lit (wrapped key + sky fill), crevices darken, the lower part cools into
        `shade`; the silhouette goes soft (and a little wispy), the bottom is cut flat.
        light: key direction (x right, y up, z toward viewer); warm: a tint for the lit side (dawn)."""
        r = self._r(seed)
        k = self.k
        lit = lin(lit or self.P['cloud']); shade = lin(shade or self.P['cloud_shade'])
        D = 0.32 * w
        tw = np.zeros(64, np.float32)
        xs_t = np.linspace(-1, 1, 64)
        for _ in range(towers):
            c = r.uniform(-0.45, 0.45); s_ = r.uniform(0.18, 0.32)
            tw += r.uniform(0.25, 0.45) * np.exp(-((xs_t - c) / s_) ** 2)
        hfun = lambda u: h * (0.62 + np.interp(u, xs_t, tw)) / (0.62 + tw.max())

        def surf(u, v):
            z = D * np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
            x = cx + u * 0.5 * w
            y = base - v * hfun(u)
            nn_ = np.stack([u / (0.5 * w), v / np.maximum(hfun(u), 1), z / (D * D) + 1e-6], -1)
            nn_ /= np.linalg.norm(nn_, axis=-1, keepdims=True)
            return x, y, z, nn_

        def sample(m, vmin, vmax):
            u = r.uniform(-1, 1, m * 3); v = r.uniform(vmin, vmax, m * 3)
            ok = u * u + v * v <= 1
            return u[ok][:m], v[ok][:m]

        P = []
        # the body: a row of overlapping puffs along the bottom, so even a long, low cloud is one solid mass
        m = int(np.ceil(w / (0.32 * h))) + 1
        for ub in np.linspace(-0.82, 0.82, m):
            rb = 0.42 * hfun(ub) * (1 - ub * ub) ** 0.35 * r.uniform(0.85, 1.1)
            P.append([cx + ub * 0.5 * w + r.normal(0, 0.02 * w), base - 0.5 * rb, rb, 0.0])
        u, v = sample(n, 0.0, 1.0)
        x, y, z, nn_ = surf(u, v)
        rr = h * r.uniform(0.13, 0.24, len(u)) * (1.15 - 0.45 * v)
        for i in range(len(u)):
            c = np.array([x[i], y[i], z[i]]) - nn_[i] * 0.55 * rr[i] * np.array([1, -1, 1])
            P.append([c[0], c[1], rr[i], c[2]])
        big = np.array(P, np.float32)
        u, v = sample(detail, 0.25, 1.0)
        x, y, z, nn_ = surf(u, v)
        rr = h * r.uniform(0.045, 0.1, len(u))
        for i in range(len(u)):
            c = np.array([x[i], y[i], z[i]]) - nn_[i] * 0.2 * rr[i] * np.array([1, -1, 1])
            # only where it bubbles out of the mass, never as a ball floating free of it
            gap = np.hypot(big[:, 0] - c[0], big[:, 1] - c[1]) - big[:, 2]
            if gap.min() > 0.2 * rr[i]: continue
            P.append([c[0], c[1], rr[i], c[2]])
        P = np.array(P, np.float32)
        x0 = int(np.floor((P[:, 0] - P[:, 2]).min())) - 6; x1 = int(np.ceil((P[:, 0] + P[:, 2]).max())) + 6
        y0 = int(np.floor((P[:, 1] - P[:, 2]).min())) - 6; y1 = int(np.ceil(base + 0.08 * h)) + 6
        Hh, Ww = y1 - y0, x1 - x0
        Z = np.full((Hh, Ww), -1e9, np.float32)
        NX = np.zeros((Hh, Ww), np.float32); NY = np.zeros_like(NX); NZ = np.zeros_like(NX); AL = np.zeros_like(NX)
        for (px, py, pr, pz) in P:
            a0, a1 = int(max(0, py - pr - y0)), int(min(Hh, py + pr - y0 + 1))
            b0, b1 = int(max(0, px - pr - x0)), int(min(Ww, px + pr - x0 + 1))
            if a1 <= a0 or b1 <= b0: continue
            gy, gx = np.mgrid[a0:a1, b0:b1].astype(np.float32)
            dx, dy = gx + x0 - px, gy + y0 - py
            q = pr * pr - dx * dx - dy * dy
            ins = q > 0
            z = pz + np.sqrt(np.clip(q, 0, None))
            sub = Z[a0:a1, b0:b1]
            up = ins & (z > sub)
            sub[up] = z[up]
            NX[a0:a1, b0:b1][up] = (dx / pr)[up]
            NY[a0:a1, b0:b1][up] = (-dy / pr)[up]
            NZ[a0:a1, b0:b1][up] = (np.sqrt(np.clip(q, 0, None)) / pr)[up]
            # coverage is the union of every puff's own soft disc (not the front puff's), so a puff passing in
            # front of another never lets the sky through along its edge
            np.maximum(AL[a0:a1, b0:b1], np.sqrt(np.clip(q, 0, None)) / pr, out=AL[a0:a1, b0:b1])
        cov = Z > -1e8
        gy = np.arange(y0, y1, dtype=np.float32)[:, None]
        L = _norm(light)
        # normals from the height field smoothed a little, so neighbouring puffs melt into each other instead of
        # showing every sphere's rim; crevices from the difference to a wider blur
        Zc = np.where(cov, Z, 0).astype(np.float32)
        Hs = blur(Zc, 0.014 * h + 1.5)
        gyy, gxx = np.gradient(Hs)
        # where one puff passes in front of another the height steps; clamp the slope so the step reads as a soft
        # overlap, not a dark crease
        gm = np.hypot(gxx, gyy); sc = np.minimum(1, 2.2 / (gm + 1e-6))
        gxx *= sc; gyy *= sc
        nn = np.stack([-gxx, gyy, np.ones_like(gxx)], -1)
        nn /= np.linalg.norm(nn, axis=-1, keepdims=True)
        dif = np.clip((nn @ L + 0.15) / 1.15, 0, 1)
        occ = np.clip((blur(Zc, 0.07 * h) - Zc) / (0.12 * h), 0, 1) * cov
        hgt = np.clip((base - gy) / h, 0, 1)
        v = np.clip(0.1 + 1.05 * dif * (0.5 + 0.5 * hgt ** 0.5) - 0.35 * occ, 0, 1)
        v = blur(v, 0.8 * k)
        col = shade[None, None] + (lit - shade)[None, None] * v[..., None]
        if warm is not None:
            col += (lin(warm) - col) * (warm_k * smoothstep(0.35, 0.9, dif) * (0.4 + 0.6 * hgt))[..., None]
        # alpha: soft at the silhouette (the sphere turning away), eroded a little by noise (wisps), flat bottom
        nz = blur(AL, 1.0 * k)
        en = noise2d(Hh, Ww, 7 * k, 3, int(r.integers(1 << 30)))
        a = smoothstep(0.0, 0.42, nz - wisp * 0.25 * (en - 0.5))
        bn = noise2d(Hh, Ww, 0.25 * w, 2, int(r.integers(1 << 30)))
        a *= smoothstep(base + 0.02 * h * flat, base - 0.04 * h * flat, gy + (bn - 0.5) * 0.06 * h)
        a = np.clip(a * alpha, 0, 1)
        self._over(y0, x0, srgb(col), a)

    def stars(self, n, y0=0, y1=None, x0=0, x1=None, size=1.0, bright=0.35, spikes=4, colour='#f4f0ff',
              fade=None, seed=None):
        """stars: uniform positions, power-law brightness (most faint, a few bright), a few warm or blue, splatted
        with sub-pixel accuracy; the `spikes` brightest get four thin diffraction spikes. fade: (y_a, y_b) the
        stars thin out from y_a to y_b (toward the horizon)."""
        r = self._r(seed)
        y1 = self.H if y1 is None else y1; x1 = self.W if x1 is None else x1
        xs = r.uniform(x0, x1, n).astype(np.float32); ys = r.uniform(y0, y1, n).astype(np.float32)
        b = (r.pareto(2.2, n) + 1).astype(np.float32) ** 1.2 * 0.5 * bright
        if fade is not None:
            b *= 1 - smoothstep(fade[0], fade[1], ys)
        tint = np.array([lin('#ffd9b0'), lin(colour), lin(colour), lin('#c8d8ff')])[r.integers(0, 4, n)]
        self._point_lights(xs, ys, b, tint, 0.55 * self.k * size)
        if spikes:
            for i in np.argsort(-b)[:spikes]:
                self.sparkle(xs[i], ys[i], 14 * self.k * size * (0.7 + 0.6 * r.random()), colour)

    def _point_lights(self, xs, ys, b, tint, sig):
        """add gaussian points (brightness b, linear tint) to the picture in linear light"""
        H, W = self.H, self.W
        acc = np.zeros((H * W, 3), np.float64)
        rad = int(np.ceil(3 * sig)) + 1
        for oy in range(-rad, rad + 1):
            for ox in range(-rad, rad + 1):
                ix = np.floor(xs).astype(np.int32) + ox; iy = np.floor(ys).astype(np.int32) + oy
                d2 = (ix + 0.5 - xs) ** 2 + (iy + 0.5 - ys) ** 2
                wv = np.exp(-d2 / (2 * sig * sig)) / (2 * np.pi * sig * sig) * b
                ok = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
                idx = iy[ok] * W + ix[ok]
                for c in range(3):
                    acc[:, c] += np.bincount(idx, (wv * tint[:, c])[ok], H * W)
        add = acc.reshape(H, W, 3).astype(np.float32)
        del acc
        rows = np.nonzero(add.max((1, 2)) > 1e-5)[0]
        if not len(rows): return
        ya, yb = rows[0], rows[-1] + 1
        self._screen(ya, 0, add[ya:yb])

    def sparkle(self, x, y, size, colour='#f4f0ff', strength=1.0, angle=0.0):
        """a bright point with a glow and four thin spikes"""
        s = int(size * 1.2) + 4
        gy, gx = np.mgrid[-s:s + 1, -s:s + 1].astype(np.float32)
        dx, dy = gx - (x - np.floor(x)) + 0.5, gy - (y - np.floor(y)) + 0.5
        th = np.radians(angle)
        u, v = dx * np.cos(th) + dy * np.sin(th), -dx * np.sin(th) + dy * np.cos(th)
        rr = np.hypot(dx, dy)
        sp = (np.exp(-np.abs(v) / 0.45) * np.exp(-np.abs(u) / (0.35 * size)) +
              np.exp(-np.abs(u) / 0.45) * np.exp(-np.abs(v) / (0.35 * size))) * 0.9
        core = np.exp(-rr * rr / (2 * (0.9 * self.k) ** 2)) * 1.6 + np.exp(-rr / (0.22 * size)) * 0.5
        add = (sp + core)[..., None] * lin(colour)[None, None] * strength
        self._screen(int(np.floor(y)) - s, int(np.floor(x)) - s, add)

    def milky_way(self, p0, p1, width, bend=0.0, strength=0.5, colour='#c9cff5', warm='#f2c8d8', rift=0.6,
                  stars=6000, seed=None):
        """a soft band of glow from p0 to p1 (bowed sideways by `bend` px), its density a gaussian across the band
        times two scales of cloudy noise, a darker rift along its middle, and faint star dust sampled from it"""
        r = self._r(seed)
        H, W = self.H, self.W
        p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
        d = p1 - p0; Lh = float(np.linalg.norm(d)); t_ = d / Lh; nrm = np.array([-t_[1], t_[0]])
        ys = np.arange(H, dtype=np.float32)[:, None]; xs = np.arange(W, dtype=np.float32)[None, :]
        u = ((xs - p0[0]) * t_[0] + (ys - p0[1]) * t_[1]) / Lh
        v = (xs - p0[0]) * nrm[0] + (ys - p0[1]) * nrm[1] - bend * 4 * np.clip(u, 0, 1) * (1 - np.clip(u, 0, 1))
        n1 = noise2d(H, W, 0.35 * width, 4, int(r.integers(1 << 30)))
        n2 = noise2d(H, W, 0.12 * width, 3, int(r.integers(1 << 30)))
        wv = width * (0.8 + 0.4 * n1)
        den = np.exp(-(v / wv) ** 2) * (0.55 + 0.6 * n1 * (0.7 + 0.5 * n2)) * smoothstep(-0.1, 0.12, u) * \
            smoothstep(1.1, 0.88, u)
        den += 0.5 * np.exp(-(v / (0.3 * wv)) ** 2) * smoothstep(-0.1, 0.2, u) * smoothstep(1.1, 0.8, u) * n1
        den *= 1 - rift * np.exp(-((v + 0.12 * width * (n2 - 0.5) * 2) / (0.22 * width)) ** 2) * (0.5 + 0.7 * n2)
        den = np.clip(den, 0, None).astype(np.float32)
        tint = lin(colour)[None, None] * (1 - n2[..., None] * 0.5) + lin(warm)[None, None] * n2[..., None] * 0.5
        self._screen(0, 0, den[..., None] * tint * strength * 0.35)
        if stars:
            cand_x = r.uniform(0, W, stars * 4).astype(np.float32); cand_y = r.uniform(0, H, stars * 4).astype(np.float32)
            pd = den[np.clip(cand_y.astype(int), 0, H - 1), np.clip(cand_x.astype(int), 0, W - 1)]
            keep = r.random(len(pd)) < pd / (pd.max() + 1e-6)
            xs_, ys_ = cand_x[keep][:stars], cand_y[keep][:stars]
            b = (r.pareto(3.0, len(xs_)) + 1).astype(np.float32) * 0.28 * strength
            tint2 = np.repeat(lin(colour)[None], len(xs_), 0)
            self._point_lights(xs_, ys_, b, tint2, 0.5 * self.k)
        del den, n1, n2, u, v

    def comet(self, x, y, angle, length, width=None, colour='#dfe6ff', head='#fffaf0', strength=1.0, spread=0.12,
              seed=None):
        """a comet: a bright spiked head at (x, y) and a tail running away at `angle` (degrees, 0 = right,
        90 = down) for `length` px -- a cone that widens (spread), fades, and is made of fine grainy streaks"""
        r = self._r(seed)
        k = self.k
        width = width or 5 * k
        th = np.radians(angle); t_ = np.array([np.cos(th), np.sin(th)]); nrm = np.array([-t_[1], t_[0]])
        ends = np.array([[x, y], [x + t_[0] * length, y + t_[1] * length]])
        pad = width + spread * length + 10
        x0, x1 = int(ends[:, 0].min() - pad), int(ends[:, 0].max() + pad)
        y0, y1 = int(ends[:, 1].min() - pad), int(ends[:, 1].max() + pad)
        gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        u = (gx - x) * t_[0] + (gy - y) * t_[1]
        v = (gx - x) * nrm[0] + (gy - y) * nrm[1]
        uu = np.clip(u / length, 0, 1)
        wv = width + spread * np.clip(u, 0, None)
        # fine streaks: a 1-D noise across the tail, stretched along it
        sn = noise2d(64, 512, 6, 3, int(r.integers(1 << 30)))
        si = np.clip(((v / (wv + 1e-3)) * 0.5 + 0.5) * 511, 0, 511).astype(np.int32)
        ui = np.clip(uu * 63, 0, 63).astype(np.int32)
        streak = 0.55 + 0.9 * sn[ui, si]
        grain = 0.75 + 0.5 * r.random(u.shape).astype(np.float32)
        I = np.exp(-(v / wv) ** 2) * (1 - uu) ** 1.6 * (u > 0) * streak * grain
        I *= smoothstep(-2, 0.05 * length, u)
        add = I[..., None] * lin(colour)[None, None] * 0.55 * strength
        self._screen(y0, x0, add)
        self.sparkle(x, y, 26 * k, head, strength=1.2 * strength, angle=r.uniform(0, 45))

    # ================================================================== extras
    def trees(self, ridge, xs, h, colour=None, light=None, haze=0.3, kind='round', seed=None):
        """small soft trees standing on a (far) ridge at the given x positions, h px tall: a crown of soft fur
        (round or tall), lit on the key side, a thin trunk; hazed like the hill they stand on"""
        r = self._r(seed)
        P = self.P
        kd = _norm(P['key_dir'])
        dark = lin(colour or P['cool'][1]); lt = lin(light or P['warm'][3])
        hz = lin(P['haze'])
        for x in xs:
            hh = h * r.uniform(0.75, 1.2)
            yb = ridge.at(x) + 0.08 * hh
            cw = hh * (0.42 if kind == 'round' else 0.24) * r.uniform(0.85, 1.15)
            ch = hh * (0.62 if kind == 'round' else 0.82)
            cy = yb - hh + ch * 0.5
            s = int(max(cw, ch) + 6)
            x0, y0 = int(x - s), int(cy - s)
            gy, gx = np.mgrid[y0:y0 + 2 * s, x0:x0 + 2 * s].astype(np.float32)
            dx, dy = (gx - x) / (0.5 * cw), (gy - cy) / (0.5 * ch)
            rr = np.sqrt(dx * dx + dy * dy)
            en = noise2d(2 * s, 2 * s, max(1.5, 0.12 * cw), 3, int(r.integers(1 << 30)))
            crown = smoothstep(1.05, 0.85, rr + (en - 0.5) * 0.45)
            trunk = (np.abs(gx - x) < max(0.7, 0.05 * hh)) & (gy > cy) & (gy < yb)
            a = np.clip(crown + trunk * 0.9, 0, 1)
            sh = np.clip(0.5 + 0.5 * (dx * kd[0] - dy * kd[1]) * 0.9 + (en - 0.5) * 0.5, 0, 1)
            col = dark[None, None] + (lt - dark)[None, None] * (sh ** 1.4 * 0.8)[..., None]
            col = col * (1 - haze) + hz * haze
            self._over(y0, x0, srgb(col), a)

    def foreground(self, top, bottom=None, density=1.0, blade=None, colour=None, tip=None, flowers=90,
                   flower_colours=None, flower_size=None, wind=10.0, blur_px=0.7, seed=None, curve=0.25):
        """the dense band of tall grass along the bottom of the picture: blades rooted below `bottom` whose tips
        reach up to about `top` (a y or a per-column array), dark at the root and backlit at the tip, with
        wildflowers on some of the stems; softened by blur_px (out of focus)"""
        H, W, k = self.H, self.W, self.k
        r = self._r(seed)
        P = self.P
        bottom = H if bottom is None else bottom
        topv = np.full(W, top, np.float32) if np.ndim(top) == 0 else np.asarray(top, np.float32)
        span = bottom - topv
        blade = blade or float(np.median(span))
        n = int(density * 2.6 * W * float(span.mean()) / max(1.0, 0.45 * 0.6 * blade * 4.2 * k))
        xs = r.uniform(-20, W + 20, n).astype(np.float32)
        xi = np.clip(xs.astype(int), 0, W - 1)
        sp = span[xi]
        ys = bottom + r.uniform(-0.05, 0.25, n).astype(np.float32) * sp
        Lb = (sp + (ys - bottom)) * (0.35 + 0.75 * r.random(n).astype(np.float32) ** 0.7)
        ang = -90 + wind + r.normal(0, 9, n)
        th = np.radians(ang).astype(np.float32)
        DX, DY = np.cos(th), np.sin(th)
        BEND = (Lb * curve * r.normal(0.5, 0.6, n) * np.sign(wind + 1e-3)).astype(np.float32)
        W0 = (r.uniform(2.6, 6.0, n) * k).astype(np.float32)
        dark = lin(colour or P['fg']); ltc = lin(tip or P['fg_tip'])
        v = r.random(n).astype(np.float32)[:, None]
        CR = srgb(dark[None] * (0.45 + 0.5 * v))
        # backlit tips: the taller the blade (the closer its tip to the lit band above), the more it glows
        reach = np.clip(Lb / np.maximum(sp, 1), 0, 1).astype(np.float32)[:, None]
        tipmix = np.clip(0.08 + 0.7 * reach ** 2.5 * (0.4 + 0.7 * r.random(n).astype(np.float32)[:, None]), 0, 0.9)
        CT = srgb(dark[None] * (1.1 + 0.3 * v) * (1 - tipmix) + ltc[None] * tipmix)
        target = np.zeros((H, W, 3), np.float32) + self.C       # paint on a copy, so the band can be softened
        alpha_acc = np.zeros((H, W), np.float32)
        self._splat_sorted(xs, ys, DX, DY, Lb, BEND, W0, CR, CT, target=target, chunk=6000, gain=1.6,
                           alpha_out=alpha_acc, tpow=2.2)
        # wildflowers at the tips of some stems
        if flowers:
            fc = flower_colours or P['flowers']
            fs = flower_size or 13 * k
            # flowers on the taller stems (they stand in the light at the top of the band), a few lower down
            pw = (reach[:, 0] ** 3 + 0.04); pw /= pw.sum()
            pick = r.choice(n, min(flowers, n), replace=False, p=pw)
            fx = xs[pick] + DX[pick] * Lb[pick] + (-DY[pick]) * BEND[pick]
            fy = ys[pick] + DY[pick] * Lb[pick] + DX[pick] * BEND[pick]
            depth = np.clip((fy - topv[np.clip(fx.astype(int), 0, W - 1)]) / np.maximum(span[np.clip(fx.astype(int), 0, W - 1)], 1), 0, 1)
            sz = fs * (0.6 + 0.9 * depth) * r.uniform(0.75, 1.25, len(pick))
            self._flowers(fx, fy, sz, [fc[int(i)] for i in r.integers(0, len(fc), len(pick))], r, target, alpha_acc)
        if blur_px:
            a = np.clip(alpha_acc, 0, 1)
            rows = np.nonzero(a.max(1) > 0)[0]
            if len(rows):
                ya = max(0, rows[0] - 8)
                for c in range(3):
                    target[ya:, :, c] = blur(target[ya:, :, c], blur_px * k)
        self.C[:] = target
        del target, alpha_acc

    def _flowers(self, fx, fy, sz, cols, r, target, alpha_acc):
        """five-petal wildflowers: each petal a short stroke from its rounded tip into the centre"""
        X0, Y0, DX, DY, L, BEND, W0, CR, CT = ([] for _ in range(9))
        for x, y, s, c in zip(fx, fy, sz, cols):
            base = lin(c)
            rot = r.uniform(0, 72)
            tilt = r.uniform(0.45, 1.0)                     # seen a little from the side
            for j in range(5):
                a = np.radians(rot + 72 * j)
                ex, ey = np.cos(a) * s * 0.5, np.sin(a) * s * 0.5 * tilt
                X0.append(x + ex); Y0.append(y + ey)
                ll = float(np.hypot(ex, ey)) + 0.3
                DX.append(-ex / ll); DY.append(-ey / ll); L.append(ll); BEND.append(0.0)
                W0.append(max(1.0, 0.55 * s * (0.7 + 0.3 * tilt)))
                sh = r.uniform(0.85, 1.15)
                CR.append(srgb(np.clip(base * sh * 1.25, 0, 1))); CT.append(srgb(base * sh * 0.8))
        f = lambda a: np.asarray(a, np.float32)
        self._splat_sorted(f(X0), f(Y0), f(DX), f(DY), f(L), f(BEND), f(W0), f(CR), f(CT), target=target,
                           chunk=4000, gain=1.5, alpha_out=alpha_acc)
        # small warm centres: one short dab each
        m = len(fx)
        cx_ = np.asarray(fx, np.float32); cy_ = np.asarray(fy, np.float32)
        ss = np.asarray(sz, np.float32)
        cc = np.repeat(hexc('#ffd868')[None], m, 0)
        self._splat_sorted(cx_ - 0.08 * ss, cy_, np.ones(m, np.float32), np.zeros(m, np.float32), 0.16 * ss,
                           np.zeros(m, np.float32), np.clip(0.22 * ss, 1, None), cc, cc, target=target, gain=1.4)

    def walker(self, x, y, h, facing=1, shirt=None, trousers='trousers', skin='skin', hair='hair', stride=0.9,
               rim=None, shadow=0.35, grass=None, bag=None, lamp=None, lamp_glow=1.0):
        """a tiny person walking, feet at (x, y), h px tall: drawn at 8x with smooth shapes (head, hair, shirt,
        trousers in stride, swinging arms) and boxed down; rim-lit on the key side; a soft shadow on the grass;
        `grass` (a colour) lays a few blades over the feet so the figure stands in the fur; `lamp` (a colour) hangs
        a small lantern from the near hand that glows and warms the grass around it"""
        S = 8
        P = self.P
        shirt = shirt or P['walker']
        pad = int(h * 0.6) + 4
        w2 = int(h * 1.2) + 2 * pad
        x0, y0 = int(np.floor(x)) - w2 // 2, int(np.floor(y - h)) - pad
        hh2 = int(h) + 2 * pad
        ox, oy = (x - x0) * S, (y - y0) * S
        U = h * S
        f = facing

        def poly(pts):
            im = Image.new('L', (w2 * S, hh2 * S), 0)
            ImageDraw.Draw(im).polygon([(ox + px * U * f, oy - py * U) for px, py in pts], fill=255)
            return im

        def limb(p0, p1, w0, w1):
            p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
            d = p1 - p0; n_ = np.array([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
            pts = [p0 + n_ * w0 / 2, p1 + n_ * w1 / 2, p1 - n_ * w1 / 2, p0 - n_ * w0 / 2]
            im = poly([tuple(p) for p in pts])
            dr = ImageDraw.Draw(im)
            for p, ww in ((p0, w0), (p1, w1)):
                cx_, cy_ = ox + p[0] * U * f, oy - p[1] * U
                rr = ww / 2 * U
                dr.ellipse([cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr], fill=255)
            return im

        def ell(cx_, cy_, rx, ry):
            im = Image.new('L', (w2 * S, hh2 * S), 0)
            X, Y = ox + cx_ * U * f, oy - cy_ * U
            ImageDraw.Draw(im).ellipse([X - rx * U, Y - ry * U, X + rx * U, Y + ry * U], fill=255)
            return im

        st = stride
        hip = (0.0, 0.50)
        legs_far = limb(hip, (-0.13 * st, 0.03), 0.105, 0.075)
        legs_near = limb(hip, (0.15 * st, 0.02), 0.11, 0.08)
        feet = [limb((-0.13 * st, 0.03), (-0.13 * st + 0.07, 0.02), 0.06, 0.05),
                limb((0.15 * st, 0.02), (0.15 * st + 0.08, 0.015), 0.06, 0.05)]
        torso = poly([(-0.11, 0.48), (0.11, 0.48), (0.125, 0.80), (0.07, 0.84), (-0.07, 0.84), (-0.125, 0.80)])
        arm_far = limb((-0.06, 0.80), (-0.12 * st - 0.02, 0.55), 0.06, 0.05)
        arm_near = limb((0.05, 0.80), (0.12 * st + 0.05, 0.54), 0.065, 0.05)
        neck = limb((0.0, 0.82), (0.01, 0.87), 0.05, 0.05)
        head = ell(0.015, 0.925, 0.072, 0.08)
        hairm = ell(0.0, 0.95, 0.075, 0.062)
        bagm = poly([(-0.17, 0.56), (-0.09, 0.56), (-0.09, 0.78), (-0.17, 0.76)]) if bag else None
        down = lambda im: np.asarray(im.resize((w2, hh2), Image.BOX), np.float32) / 255
        parts = [(legs_far, trousers, 0.8), (feet[0], '#24201e', 0.8), (arm_far, shirt, 0.8)]
        if bagm is not None: parts.append((bagm, bag, 1.0))
        parts += [(legs_near, trousers, 1.0), (feet[1], '#24201e', 1.0), (torso, shirt, 1.0),
                  (arm_near, shirt, 1.05), (neck, skin, 0.9), (head, skin, 1.0), (hairm, hair, 1.0)]
        col = np.zeros((hh2, w2, 3), np.float32); A = np.zeros((hh2, w2), np.float32)
        for im, c, sh in parts:
            a = down(im)
            cc = np.clip(lin(c) * sh, 0, 1)
            col += (cc[None, None] - col) * a[..., None]
            A = A + (1 - A) * a
        # rim light on the key side, a cool fill on the other
        kd = _norm(P['key_dir'])
        sx = int(np.sign(kd[0]) or 1)
        edge = np.clip(A - np.roll(A, sx, axis=1), 0, 1)
        rimc = lin(rim or P['warm'][4])
        col += (rimc[None, None] - col) * (edge * 0.75)[..., None]
        col *= 0.8 + 0.2 * np.linspace(1, 0.6, hh2, dtype=np.float32)[:, None, None]
        # shadow on the grass, away from the key
        if shadow:
            gy, gx = np.mgrid[0:hh2, 0:w2].astype(np.float32)
            cxs = x - x0 - sx * 0.45 * h; cys = y - y0 + 0.02 * h
            sha = np.exp(-(((gx - cxs) / (0.5 * h)) ** 2 + ((gy - cys) / (0.045 * h + 0.8)) ** 2)) * shadow
            Cc = self.C[y0:y0 + hh2, x0:x0 + w2]
            Cc *= 1 - (sha[:Cc.shape[0], :Cc.shape[1], None] * (1 - lin(P['cool'][1]) * 0.6))
        self._over(y0, x0, srgb(col), A)
        if grass:
            r = self._r()
            m = int(10 + h * 0.5)
            gxs = (x + r.uniform(-0.25, 0.25, m) * h).astype(np.float32)
            gys = (y + r.uniform(-0.01, 0.06, m) * h).astype(np.float32)
            Lg = (h * r.uniform(0.06, 0.16, m)).astype(np.float32)
            th = np.radians(-90 + r.normal(10, 12, m)).astype(np.float32)
            gc = np.asarray(grass if not isinstance(grass, str) else hexc(grass), np.float32)
            CR = np.repeat(gc[None] * 0.8, m, 0).astype(np.float32); CT = np.repeat(np.clip(gc[None] * 1.15, 0, 1), m, 0).astype(np.float32)
            self._splat_sorted(gxs, gys, np.cos(th), np.sin(th), Lg, np.zeros(m, np.float32),
                               np.full(m, 0.9, np.float32), CR, CT)
        if lamp:
            hx = x + (0.12 * st + 0.07) * h * f
            hy = y - 0.47 * h
            R = int(1.6 * h)
            gy, gx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32)
            d = np.hypot(gx, gy * 1.1)
            glow = (np.exp(-d / (0.22 * h)) * 0.55 + np.exp(-d / (0.7 * h)) * 0.22) * lamp_glow
            glow *= smoothstep(R, 0.55 * R, d)
            self._screen(int(hy) - R, int(hx) - R, glow[..., None] * lin(lamp)[None, None])
            self.sparkle(hx, hy, 0.35 * h, '#fff2d0', strength=0.9 * lamp_glow, angle=0)

    # ================================================================== stroke splatting
    def _splat_sorted(self, X0, Y0, DX, DY, L, BEND, W0, CR, CT, chunk=14000, step=0.6, gain=1.15, blur_px=0.0,
                      target=None, alpha_out=None, tpow=0.9):
        """lay tapered, bent strokes from the back (small root y) to the front, in chunks"""
        r = self._r()
        # sort by root, jittered by about a blade length, so the chunks are not straight rows (they would stripe)
        order = np.argsort(Y0 + (r.random(len(Y0)).astype(np.float32) - 0.5) * 2.4 * L, kind='stable')
        for s in range(0, len(order), chunk):
            idx = order[s:s + chunk]
            self._splat(X0[idx], Y0[idx], DX[idx], DY[idx], L[idx], BEND[idx], W0[idx], CR[idx], CT[idx],
                        step, gain, blur_px, target, alpha_out, tpow)

    def _splat(self, X0, Y0, DX, DY, L, BEND, W0, CR, CT, step=0.6, gain=1.15, blur_px=0.0, target=None,
               alpha_out=None, tpow=0.9):
        H, W = self.H, self.W
        C = self.C if target is None else target
        ext = float(L.max()) + float(np.abs(BEND).max()) + float(W0.max()) + 3
        ya = int(max(0, np.floor(Y0.min() - ext))); yb = int(min(H, np.ceil(Y0.max() + ext)))
        if yb <= ya: return
        Hc = yb - ya
        A = np.zeros(Hc * W, np.float64); R = np.zeros(Hc * W, np.float64)
        G = np.zeros(Hc * W, np.float64); B = np.zeros(Hc * W, np.float64)
        K = np.clip(np.ceil(L / step).astype(np.int32) + 1, 2, 400)
        # bucket by sample count (rounded up to a coarse ladder) so every bucket is one dense array op
        ladder = np.array([3, 4, 6, 8, 11, 15, 20, 27, 36, 48, 64, 85, 112, 150, 200, 270, 400])
        kb = ladder[np.searchsorted(ladder, K)]
        for kk in np.unique(kb):
            sel = np.nonzero(kb == kk)[0]
            m = int(np.ceil(W0[sel].max()))
            for s0 in range(0, len(sel), max(1, 3_000_000 // (kk * m))):
                ii = sel[s0:s0 + max(1, 3_000_000 // (kk * m))]
                s = np.linspace(0, 1, kk, dtype=np.float32)[None, :]
                Li, Bi = L[ii][:, None], BEND[ii][:, None]
                dx, dy = DX[ii][:, None], DY[ii][:, None]
                px, py = -dy, dx
                X = X0[ii][:, None] + dx * Li * s + px * Bi * s * s
                Y = Y0[ii][:, None] + dy * Li * s + py * Bi * s * s
                w = W0[ii][:, None] * (1 - s) ** 0.8 * (0.55 + 0.45 * np.minimum(1, s * 6))
                seg = (Li / (kk - 1)).astype(np.float32)
                cr, ct = CR[ii][:, None, :], CT[ii][:, None, :]
                tt = (s ** tpow)[..., None]
                col = cr + (ct - cr) * tt
                mm = max(1, int(np.ceil(W0[ii].max())))
                for j in range(mm):
                    if mm == 1:
                        Xj, Yj, wt = X, Y, np.minimum(w, 1.0) * seg
                    else:
                        o = (j + 0.5) / mm - 0.5
                        Xj, Yj = X + px * o * w, Y + py * o * w
                        wt = np.minimum(w / mm, 1.0) * seg
                    self._bilinear(Xj, Yj, wt, col, ya, Hc, A, R, G, B)
        A = A.reshape(Hc, W).astype(np.float32)
        Cs = np.stack([R.reshape(Hc, W), G.reshape(Hc, W), B.reshape(Hc, W)], -1).astype(np.float32)
        del R, G, B
        if blur_px:
            A = blur(A, blur_px)
            for c in range(3): Cs[..., c] = blur(Cs[..., c], blur_px)
        a = np.clip(A * gain, 0, 1)
        col = Cs / np.maximum(A, 1e-6)[..., None]
        Cc = C[ya:yb]
        Cc += (col - Cc) * a[..., None]
        if alpha_out is not None:
            ao_ = alpha_out[ya:yb]
            ao_ += (1 - ao_) * a

    def _bilinear(self, X, Y, wt, col, ya, Hc, A, R, G, B):
        W = self.W
        X = X.ravel(); Y = Y.ravel() - ya
        wt = np.broadcast_to(wt, (wt.shape[0], col.shape[1])).ravel() if wt.ndim == 2 else wt.ravel()
        ix = np.floor(X).astype(np.int32); iy = np.floor(Y).astype(np.int32)
        fx = (X - ix).astype(np.float32); fy = (Y - iy).astype(np.float32)
        c = col.reshape(-1, 3)
        for oy, ox, ww in ((0, 0, (1 - fx) * (1 - fy)), (0, 1, fx * (1 - fy)), (1, 0, (1 - fx) * fy), (1, 1, fx * fy)):
            jx, jy = ix + ox, iy + oy
            ok = (jx >= 0) & (jx < W) & (jy >= 0) & (jy < Hc)
            if not ok.any(): continue
            id_ = (jy[ok] * W + jx[ok])
            wv = (ww * wt)[ok]
            n = A.shape[0]
            A += np.bincount(id_, wv, n)
            cc = c[ok]
            R += np.bincount(id_, wv * cc[:, 0], n)
            G += np.bincount(id_, wv * cc[:, 1], n)
            B += np.bincount(id_, wv * cc[:, 2], n)

    # ================================================================== output
    def finish(self, grain=1.0, bloom=0.3, soft=0.3, chroma=0.25):
        """record the finishing (applied in render, so every stage snapshot matches; call before the first mark)"""
        self.fin = dict(grain=grain, bloom=bloom, soft=soft, chroma=chroma)
        return self

    def render(self):
        """the finished picture (the buffer is untouched)"""
        out = np.clip(self.C, 0, 1).copy()
        f = self.fin
        if not f: return out
        H, W = self.H, self.W
        if f['soft']:
            s = f['soft']
            for c in range(3): out[..., c] = out[..., c] * (1 - s) + blur(out[..., c], 0.8 * self.k) * s
        if f['bloom']:
            sm = Image.fromarray((out * 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
            sm = np.asarray(sm, np.float32) / 255
            lum = sm.mean(-1)
            br = sm * smoothstep(0.72, 0.98, lum)[..., None]
            for c in range(3): br[..., c] = blur(br[..., c], 6 * self.k)
            up = np.asarray(Image.fromarray((np.clip(br, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR),
                            np.float32) / 255
            out = 1 - (1 - out) * (1 - up * f['bloom'])
        if f['grain']:
            r = np.random.default_rng(self.seed * 31 + 7)
            g = r.standard_normal((H, W)).astype(np.float32)
            g = 0.7 * g + 0.6 * blur(g, 0.7) * 1.6
            lum = out.mean(-1)
            amp = 0.017 * f['grain'] * (0.45 + 1.1 * lum * (1 - lum) * 4 * 0.5)
            out += (g * amp)[..., None]
            if f['chroma']:
                for c in range(3):
                    out[..., c] += r.standard_normal((H, W)).astype(np.float32) * 0.008 * f['chroma'] * f['grain']
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
