"""clay — stop-motion plasticine relief, photographed under a soft studio light (numpy + Pillow only).

Model: the picture is a board of plasticine seen from the front. Two maps are built piece by piece:
  height  h(x, y)  in pixels -- every piece is pressed on top of whatever is already there
                   (by default it drapes over the surface below, like real clay pressed on clay)
  albedo  c(x, y)  the clay colour, slightly uneven, with streaks where two colours were kneaded
Pieces are what hands make: flattened pads (any outline, round or pillowy edges), balls, rolled
snakes along a path, puffy letters, finger-smeared slabs, tool grooves and poked holes. Every surface
carries small lumps and the odd fingerprint whorl.
The render lights the height field like a photo of a set: wrap-diffuse warm key + cool fill, a soft
waxy sheen, cast shadows marched through the height field, ambient occlusion in the creases (clay
shadows stay saturated, not grey), then a little lens vignette and film grain.

    from clay import Clay
    c = Clay(1920, 1080, seed=1)
    c.backdrop('#bfe0ea')
    c.pad(c.circle(960, 540, 200), '#f4c542', height=18)        # a pressed disc
    c.ball(900, 500, 16, '#2f3b63')                              # an eye
    c.snake([(860, 600), (960, 640), (1060, 600)], 8, '#2f3b63') # a rolled smile
    c.groove([(700, 700), (1200, 700)], 4, 3)                    # a tool line
    c.text('HELLO', 960, 200, 120, '#ee7453')                    # puffy letters
    c.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import (blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts, load_font, text_mask,
                  height_normals, height_shadow, ambient_occlusion)


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class Clay:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.5, -0.62, 0.6), backdrop='#d9dccb'):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.light = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.h = np.zeros((H, W), np.float32)
        self.alb = np.ones((H, W, 3), np.float32) * _c(backdrop)
        self.gloss = np.full((H, W), 1.0, np.float32)
        s = int(self.rng.integers(1 << 30))
        self.fine = noise2d(H, W, 2.4, 2, s) - 0.5              # pores and tiny crumbs
        self.lump = noise2d(H, W, 60, 3, s + 1) - 0.5            # hand-pressed unevenness
        self.tint = noise2d(H, W, 45, 3, s + 2) - 0.5            # colour not perfectly kneaded
        self.prints = self._fingerprints(int(W * H / 40000))
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ texture fields
    def _fingerprints(self, n):
        """sparse fingerprint whorls: concentric elliptical ridges in small fading patches"""
        f = np.zeros((self.H, self.W), np.float32)
        for _ in range(n):
            cx, cy = self.rng.uniform(0, self.W), self.rng.uniform(0, self.H)
            R = self.rng.uniform(22, 42); per = self.rng.uniform(4.2, 5.6)
            a = self.rng.uniform(0, np.pi); sq = self.rng.uniform(0.55, 0.8)
            x0, x1 = int(max(0, cx - R * 2)), int(min(self.W, cx + R * 2))
            y0, y1 = int(max(0, cy - R * 2)), int(min(self.H, cy + R * 2))
            if x1 <= x0 or y1 <= y0: continue
            X, Y = self.XX[y0:y1, x0:x1] - cx, self.YY[y0:y1, x0:x1] - cy
            u, v = X * np.cos(a) + Y * np.sin(a), (-X * np.sin(a) + Y * np.cos(a)) / sq
            r = np.hypot(u, v)
            ridge = np.sin(2 * np.pi * r / per + 0.35 * np.sin(3 * np.arctan2(v, u)))
            f[y0:y1, x0:x1] += ridge * np.exp(-(r / R) ** 2 * 1.6) * self.rng.uniform(0.5, 1.0)
        return f

    def _box(self, mask, margin=0):
        ys, xs = np.nonzero(mask > 0.002)
        if len(xs) == 0: return None
        return (slice(max(0, ys.min() - margin), min(self.H, ys.max() + margin + 1)),
                slice(max(0, xs.min() - margin), min(self.W, xs.max() + margin + 1)))

    def _roll(self, a, sl):
        """a random window of a precomputed field, the same size as box `sl` (no two pieces share a pattern).
        The window stays inside the field: wrapping non-tileable noise would leave straight seams."""
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        oy = int(self.rng.integers(0, self.H - h + 1)); ox = int(self.rng.integers(0, self.W - w + 1))
        return a[oy:oy + h, ox:ox + w]

    # ------------------------------------------------------------ masks
    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        X, Y = self.XX - cx, self.YY - cy
        c, s = np.cos(rot), np.sin(rot)
        d = np.hypot((X * c + Y * s) / rx, (-X * s + Y * c) / ry)
        return np.clip((1 - d) * min(rx, ry) + 0.5, 0, 1)

    def poly(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=2)

    def blob(self, cx, cy, rx, ry, rough=0.06, rot=0.0):
        return self.poly(blob_pts(cx, cy, rx, ry, rough=rough, n=120, seed=self._seed(), rot=rot))

    def rrect(self, x0, y0, x1, y1, r):
        im = Image.new('L', (self.W * 2, self.H * 2), 0)
        ImageDraw.Draw(im).rounded_rectangle((x0 * 2, y0 * 2, x1 * 2, y1 * 2), r * 2, fill=255)
        return np.asarray(im.resize((self.W, self.H), Image.BILINEAR), np.float32) / 255

    def gradient(self, top, bottom, y0=0, y1=None):
        """a vertical colour field (H, W, 3) to feed smear() or pad(colour=...)"""
        y1 = self.H if y1 is None else y1
        t = np.clip((self.YY - y0) / max(1, y1 - y0), 0, 1)[..., None]
        return _c(top) * (1 - t) + _c(bottom) * t

    # ------------------------------------------------------------ pressing a piece
    def _press(self, sl, hp, cover, colour, texture=1.0, gloss=1.0, marble=None):
        """composite one piece inside box `sl`: hp = its absolute height, cover = where it exists (0..1)"""
        cur = self.h[sl]
        tex = (self._roll(self.fine, sl) * 0.5 + self._roll(self.lump, sl) * 1.6 + self._roll(self.prints, sl) * 0.24) * texture
        hp = hp + tex * np.clip(cover * 3, 0, 1)
        k = np.clip((hp - cur) / 1.0 + 0.5, 0, 1) * cover
        if np.ndim(colour) == 3:
            col = colour[sl]
        else:
            col = np.broadcast_to(_c(colour), cur.shape + (3,))
        col = col * (1 + 0.07 * self._roll(self.tint, sl))[..., None]
        if marble is not None:                                  # half-kneaded second colour in streaks
            mc, amt = marble
            ang = self.rng.uniform(0, np.pi)
            u = (-self.XX[sl] * np.sin(ang) + self.YY[sl] * np.cos(ang)) + 40 * self._roll(self.lump, sl)
            span = int(u.max() - u.min()) + 4
            st = np.interp(u - u.min(), np.arange(span), fbm1d(span, 26, 3, self._seed()))
            m = smoothstep(0.5 - amt, 0.62 - amt * 0.6, st * 0.5 + 0.5)[..., None]
            col = col * (1 - m) + _c(mc) * m
        self.alb[sl] = self.alb[sl] * (1 - k[..., None]) + col * k[..., None]
        self.h[sl] = cur * (1 - k) + np.maximum(cur, hp) * k
        self.gloss[sl] = self.gloss[sl] * (1 - k) + gloss * k
        return k

    def _base(self, sl, base):
        return blur(self.h[sl], 3) if base is None else np.float32(base)

    def pad(self, mask, colour, height=14, round=5, base=None, texture=1.0, gloss=1.0, marble=None):
        """a piece pressed flat to any outline. round: edge radius in px (small = crisp slab, large = pillow/dome).
        colour may be a hex / RGB or an (H, W, 3) field (e.g. from gradient()). base=None drapes it over what is below."""
        sl = self._box(mask, int(round * 3 + 4))
        if sl is None: return None
        b = blur(mask[sl], max(0.8, round))
        p = np.clip((b - 0.5) * 2.1, 0, 1)
        prof = np.sqrt(1 - (1 - p) ** 2)                        # a quarter-circle fillet into a flat top
        hp = self._base(sl, base) + prof * height
        cover = smoothstep(0.42, 0.56, b)
        return self._press(sl, hp, cover, colour, texture, gloss, marble)

    def ball(self, cx, cy, r, colour, squash=0.85, base=None, texture=0.6, gloss=1.0):
        """a rolled ball (eyes, berries, rivets, pebbles)"""
        m = 3
        sl = (slice(max(0, int(cy - r - m)), min(self.H, int(cy + r + m + 1))), slice(max(0, int(cx - r - m)), min(self.W, int(cx + r + m + 1))))
        if sl[0].stop <= sl[0].start or sl[1].stop <= sl[1].start: return
        d2 = (self.XX[sl] - cx) ** 2 + (self.YY[sl] - cy) ** 2
        prof = np.sqrt(np.clip(r * r - d2, 0, None)) * squash
        cover = np.clip(r - np.sqrt(d2) + 0.5, 0, 1)
        self._press(sl, self._base(sl, base) + prof, cover, colour, texture, gloss)

    def snake(self, pts, r, colour, taper=(1.0, 1.0), squash=0.8, base=None, smooth=True, texture=0.6, gloss=1.0):
        """a rolled coil of clay along a path (lines, rims, stems, waves, smiles); taper = radius factor at (start, end)"""
        P = spline(pts, 10) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        rmax = r * max(taper)
        x0, x1 = int(max(0, P[:, 0].min() - rmax - 3)), int(min(self.W, P[:, 0].max() + rmax + 4))
        y0, y1 = int(max(0, P[:, 1].min() - rmax - 3)), int(min(self.H, P[:, 1].max() + rmax + 4))
        if x1 <= x0 or y1 <= y0: return
        sl = (slice(y0, y1), slice(x0, x1))
        X, Y = self.XX[sl], self.YY[sl]
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)]); L = cum[-1] + 1e-6
        best = np.full(X.shape, 1e9, np.float32); tpar = np.zeros(X.shape, np.float32)
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]; d = b - a; l2 = float(d @ d) + 1e-9
            t = np.clip(((X - a[0]) * d[0] + (Y - a[1]) * d[1]) / l2, 0, 1)
            dist = np.hypot(X - a[0] - t * d[0], Y - a[1] - t * d[1])
            sel = dist < best
            best = np.where(sel, dist, best); tpar = np.where(sel, (cum[i] + t * seg[i]) / L, tpar)
        rr = r * (taper[0] + (taper[1] - taper[0]) * tpar)
        prof = np.sqrt(np.clip(rr * rr - best * best, 0, None)) * squash
        cover = np.clip(rr - best + 0.5, 0, 1)
        self._press(sl, self._base(sl, base) + prof, cover, colour, texture, gloss)

    def text(self, s, x, y, size, colour, height=None, font='rounded', anchor='mm', spacing=0.0, round=None, base=None):
        """puffy clay letters (any font style from core.load_font: rounded, sans_bold, cjk_sans, ...)"""
        m = text_mask(self.H, self.W, s, load_font(font, size), (x, y), anchor, spacing)
        return self.pad(m, colour, height if height is not None else size * 0.12, round if round is not None else size * 0.05, base, texture=0.5)

    def smear(self, mask, colour, strokes=220, length=(90, 190), width=(40, 70), angle=0.0, spread=0.5, height=6, drag=0.85):
        """a slab spread with fingertips: short curved finger strokes drag colour along and leave soft ridges.
        colour: a hex / RGB or an (H, W, 3) field -- the strokes smudge neighbouring colours into each other."""
        base_col = colour if np.ndim(colour) == 3 else np.broadcast_to(_c(colour), (self.H, self.W, 3))
        k = self.pad(mask, base_col, height, 3)
        if k is None: return
        field = self.alb.copy()
        ys, xs = np.nonzero(mask > 0.5)
        if len(xs) == 0: return
        for _ in range(strokes):
            i = int(self.rng.integers(len(xs))); sx, sy = float(xs[i]), float(ys[i])
            a = angle + self.rng.normal(0, spread); L = self.rng.uniform(*length); w = self.rng.uniform(*width)
            bend = self.rng.normal(0, 0.35)
            ex, ey = sx + np.cos(a) * L, sy + np.sin(a) * L
            mx, my = (sx + ex) / 2 - np.sin(a) * bend * L * 0.3, (sy + ey) / 2 + np.cos(a) * bend * L * 0.3
            P = spline([(sx, sy), (mx, my), (ex, ey)], 8)
            x0, x1 = int(max(0, P[:, 0].min() - w)), int(min(self.W, P[:, 0].max() + w + 1))
            y0, y1 = int(max(0, P[:, 1].min() - w)), int(min(self.H, P[:, 1].max() + w + 1))
            if x1 - x0 < 3 or y1 - y0 < 3: continue
            sl = (slice(y0, y1), slice(x0, x1))
            X, Y = self.XX[sl], self.YY[sl]
            best = np.full(X.shape, 1e9, np.float32); tp = np.zeros(X.shape, np.float32)
            seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
            for j in range(len(P) - 1):
                a0, b0 = P[j], P[j + 1]; d = b0 - a0; l2 = float(d @ d) + 1e-9
                t = np.clip(((X - a0[0]) * d[0] + (Y - a0[1]) * d[1]) / l2, 0, 1)
                dist = np.hypot(X - a0[0] - t * d[0], Y - a0[1] - t * d[1])
                sel = dist < best; best = np.where(sel, dist, best); tp = np.where(sel, (cum[j] + t * seg[j]) / (cum[-1] + 1e-6), tp)
            u = best / (w / 2)                                   # 0 centre .. 1 edge of the fingertip
            tp = np.clip(tp, 0, 1)
            env = smoothstep(1.9, 1.1, u) * smoothstep(0.0, 0.15, tp) * mask[sl]
            if env.max() <= 0: continue
            src = field[min(self.H - 1, int(sy)), min(self.W - 1, int(sx))]           # colour picked up where the finger lands
            a_col = smoothstep(1.05, 0.45, u) * mask[sl] * drag * (1 - tp) ** 1.2
            self.alb[sl] = self.alb[sl] * (1 - a_col[..., None]) + src * a_col[..., None]
            # a shallow scoop under the fingertip, soft ridges of pushed clay along both sides and at the end
            prof = -0.7 * (1 - smoothstep(0.0, 1.1, u)) + 0.8 * np.exp(-((u - 1.05) / 0.38) ** 2)
            prof = prof * (1 - 0.4 * tp) + 0.9 * np.exp(-((tp - 0.97) / 0.07) ** 2) * (1 - smoothstep(0.3, 1.1, u))
            self.h[sl] = self.h[sl] + prof * env * height * 0.32

    def groove(self, pts, width, depth, smooth=True):
        """a line pressed in with a modelling tool (a trough with slightly raised lips)"""
        P = spline(pts, 10) if smooth and len(pts) > 2 else np.asarray(pts, np.float32)
        w = width
        x0, x1 = int(max(0, P[:, 0].min() - w * 2 - 2)), int(min(self.W, P[:, 0].max() + w * 2 + 3))
        y0, y1 = int(max(0, P[:, 1].min() - w * 2 - 2)), int(min(self.H, P[:, 1].max() + w * 2 + 3))
        if x1 <= x0 or y1 <= y0: return
        sl = (slice(y0, y1), slice(x0, x1))
        X, Y = self.XX[sl], self.YY[sl]
        best = np.full(X.shape, 1e9, np.float32)
        for i in range(len(P) - 1):
            a, b = P[i], P[i + 1]; d = b - a; l2 = float(d @ d) + 1e-9
            t = np.clip(((X - a[0]) * d[0] + (Y - a[1]) * d[1]) / l2, 0, 1)
            best = np.minimum(best, np.hypot(X - a[0] - t * d[0], Y - a[1] - t * d[1]))
        u = best / (w / 2)
        trough = np.sqrt(np.clip(1 - u * u, 0, 1))
        lip = np.exp(-((u - 1.25) / 0.3) ** 2) * 0.25
        self.h[sl] -= depth * (trough - lip)

    def poke(self, cx, cy, r, depth):
        """a hole pushed in with a tool tip (portholes, nostrils, texture dots)"""
        m = int(r * 1.8 + 2)
        sl = (slice(max(0, int(cy - m)), min(self.H, int(cy + m + 1))), slice(max(0, int(cx - m)), min(self.W, int(cx + m + 1))))
        d = np.hypot(self.XX[sl] - cx, self.YY[sl] - cy) / r
        self.h[sl] -= depth * (np.sqrt(np.clip(1 - d * d, 0, 1)) - 0.22 * np.exp(-((d - 1.2) / 0.25) ** 2))

    def backdrop(self, colour, texture=1.0, lumps=3.0):
        """the board itself: a flat slab of one colour (or an (H, W, 3) field) with gentle hand-made unevenness"""
        self.alb = (np.broadcast_to(_c(colour), (self.H, self.W, 3)) if np.ndim(colour) < 3 else colour.copy()).astype(np.float32)
        self.alb = self.alb * (1 + 0.05 * self.tint)[..., None]
        self.h = (self.lump * lumps + self.fine * 0.35 + self.prints * 0.2) * texture

    # ------------------------------------------------------------ light and output
    def render(self, key=('#fff4e2', 1.0), fill=('#c9dcff', 0.28), ambient=0.34, sheen=0.16, shadow=0.62, ao=0.55,
               reach=180, grain=0.018, vignette=0.16):
        h = self.h
        n = height_normals(h)
        L = self.light
        wrap = 0.3
        diff = np.clip((n @ L + wrap) / (1 + wrap), 0, 1)
        Lf = np.array([-L[0], -L[1] * 0.3, 0.7], np.float32); Lf /= np.linalg.norm(Lf)
        fil = np.clip(n @ Lf, 0, 1)
        sh = blur(height_shadow(h, tuple(L), reach=reach, step=2.0, soft=2.5), 2.2)
        occ = ambient_occlusion(h)
        kc, ki = _c(key[0]), key[1]; fc, fi = _c(fill[0]), fill[1]
        direct = (diff * (1 - shadow * sh))[..., None] * kc * ki
        amb = (ambient * (1 - ao * occ))[..., None] * np.array([0.93, 0.97, 1.05], np.float32)
        light = direct + amb + (fil * fi * (1 - 0.5 * occ))[..., None] * fc
        alb = self.alb
        deep = np.clip(1 - light.mean(-1, keepdims=True), 0, 1) * 0.35     # clay shadows stay saturated (a little subsurface)
        sat = np.clip(alb + (alb - alb.mean(-1, keepdims=True)) * deep, 0, 1)
        img = sat * light
        Hv = L + np.array([0, 0, 1], np.float32); Hv /= np.linalg.norm(Hv)
        spec = np.clip(n @ Hv, 0, 1) ** 24 * sheen * self.gloss * (1 - 0.8 * sh)
        img = img + spec[..., None] * kc
        r = np.hypot((self.XX - self.W / 2) / self.W, (self.YY - self.H / 2) / self.H)
        img = img * (1 - vignette * r ** 2 * 2.2)[..., None]
        if grain:
            img = img + (np.random.default_rng(7).normal(0, grain, (self.H, self.W, 1))).astype(np.float32)
        return np.clip(img, 0, 1)

    def composite(self):
        return Image.fromarray((self.render() * 255).astype(np.uint8))

    def stage(self, name):
        self.stages.append((name, self.composite()))

    def save(self, path, stages_dir=None):
        img = self.composite(); img.save(path)
        if stages_dir:
            import os
            os.makedirs(stages_dir, exist_ok=True)
            for i, (name, im) in enumerate(self.stages):
                im.save(f"{stages_dir}/{i:02d}_{name}.png")
            img.save(f"{stages_dir}/{len(self.stages):02d}_final.png")
        return img
