"""panel — vintage industrial-design fronts: radios, hi-fi, instruments (numpy + Pillow only).

Model: a product front is built like the real thing, part by part, and every part is lit by one key light
from the upper left:
  materials  teak veneer (warped growth rings + pores + satin varnish), brushed aluminium (brushing streaks
             + a broad anisotropic highlight), moulded plastic, painted metal, woven grille cloth (with lurex
             threads), perforated metal;
  relief     raised plates, bevelled edges and recessed wells are small height fields: edges facing the light
             catch a highlight, the far edges fall into shadow, raised parts cast soft drop shadows;
  controls   machined knobs (lathe rings, radial sheen, knurled skirt, indicator), piano-key buttons, bat-handle
             toggle switches, jewel lamps with glow, a green "magic eye" tuning tube, a moving-coil meter,
             slotted screws;
  print      silkscreened legends (letter-spaced sans), arc and linear scales, a backlit dial behind glass
             with a needle and a reflection streak, a chrome script badge.

    from panel import Panel
    p = Panel(1920, 1080, seed=1)
    p.background('#b9c7bd')
    body = p.rrect(100, 120, 1820, 950, 40)
    p.surface(body, 'wood', '#8a5230', height=10, shadow=0.5)
    p.knob(1200, 740, 70, angle=-40)
    p.scale_arc(1200, 740, 84, 100, -135, 135, 11, labels=['0', '5', '10'])
    p.text('VOLUME', 1200, 850, 22, spacing=6, anchor='mm')
    p.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, shift, load_font, text_mask, height_normals


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class Panel:
    def __init__(self, W=1920, H=1080, seed=0, light=(-0.5, -0.62, 0.6)):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.L = np.asarray(light, np.float32) / np.linalg.norm(light)
        self.img = np.ones((H, W, 3), np.float32) * 0.8
        self.fine = noise2d(H, W, 1.3, 2, int(self.rng.integers(1 << 30)))
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def _box(self, mask, margin=0):
        ys, xs = np.nonzero(mask > 0.002)
        if len(xs) == 0: return None
        return (slice(max(0, ys.min() - margin), min(self.H, ys.max() + margin + 1)),
                slice(max(0, xs.min() - margin), min(self.W, xs.max() + margin + 1)))

    # ------------------------------------------------------------ masks
    def rrect(self, x0, y0, x1, y1, r):
        im = Image.new('L', (self.W * 2, self.H * 2), 0)
        ImageDraw.Draw(im).rounded_rectangle((x0 * 2, y0 * 2, x1 * 2, y1 * 2), r * 2, fill=255)
        return np.asarray(im.resize((self.W, self.H), Image.BILINEAR), np.float32) / 255

    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    def ring(self, cx, cy, r, width):
        return np.clip(width / 2 - np.abs(np.hypot(self.XX - cx, self.YY - cy) - r) + 0.5, 0, 1)

    def poly(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=2)

    def line_mask(self, pts, width):
        im = Image.new('L', (self.W * 2, self.H * 2), 0)
        ImageDraw.Draw(im).line([(float(x) * 2, float(y) * 2) for x, y in pts], fill=255, width=max(1, int(round(width * 2))), joint='curve')
        return np.asarray(im.resize((self.W, self.H), Image.BILINEAR), np.float32) / 255

    # ------------------------------------------------------------ materials (generated inside a box)
    def material(self, kind, colour, sl, **kw):
        H, W = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        X, Y = self.XX[sl], self.YY[sl]
        col = _c(colour)
        base = np.ones((H, W, 3), np.float32) * col
        s = self._seed()
        if kind == 'plastic':                                       # moulded: faint orange-peel, gentle gradient
            t = 1.0 + 0.012 * (noise2d(H, W, 2.0, 2, s) - 0.5) + 0.03 * (noise2d(H, W, 260, 2, s + 1) - 0.5)
            return base * t[..., None]
        if kind == 'painted':
            t = 1.0 + 0.02 * (noise2d(H, W, 1.5, 2, s) - 0.5) + 0.04 * (noise2d(H, W, 180, 3, s + 1) - 0.5)
            return base * t[..., None]
        if kind == 'brushed':                                       # aluminium brushed along x (or radially)
            rows = np.interp(Y[:, 0], np.arange(self.H), fbm1d(self.H, 1.5, 3, s))[:, None]
            streak = 0.6 * rows + 0.4 * (np.asarray(Image.fromarray(self.rng.random((H, max(2, W // 40))).astype(np.float32)).resize((W, H), Image.BILINEAR)) - 0.5)
            band = kw.get('band', 0.5)
            u = (X - X.min()) / max(1, W)
            aniso = 0.9 + 0.14 * np.exp(-((u - band) / 0.28) ** 2) - 0.05 * u
            return base * (aniso + 0.045 * streak)[..., None]
        if kind == 'wood':                                          # teak veneer: warped growth rings, rays, pores
            dark = _c(kw.get('dark', '#5c3118')); light = _c(kw.get('light', '#b07442'))
            warp = noise2d(H, W, 220, 3, s) * 60 + noise2d(H, W, 40, 2, s + 1) * 8
            v = (Y + warp) * kw.get('ring_scale', 0.12) + 3 * np.sin(X / 380 + noise2d(H, W, 500, 2, s + 2) * 3)
            rings = 0.5 + 0.5 * np.sin(v + 1.5 * np.sin(v * 0.37))
            rings = rings ** 1.8
            fig = noise2d(H, W, 90, 3, s + 3)
            t = np.clip(0.55 * rings + 0.35 * fig + 0.1 * self.fine[sl], 0, 1)
            c = col * (1 - t[..., None] * 0.55) + dark * (t[..., None] * 0.55)
            c = c * (1 - 0.25 * (1 - rings)[..., None]) + light * (0.25 * (1 - rings))[..., None]
            pores = np.asarray(Image.fromarray(self.rng.random((H, max(2, W // 9))).astype(np.float32)).resize((W, H), Image.BILINEAR))
            c *= (1 - 0.18 * smoothstep(0.82, 0.95, pores))[..., None]
            return c
        if kind == 'fabric':                                        # woven grille cloth with metallic lurex threads
            p = kw.get('pitch', 4.0)
            wx = 0.5 + 0.5 * np.cos(2 * np.pi * X / p); wy = 0.5 + 0.5 * np.cos(2 * np.pi * Y / p)
            over = ((np.floor(X / p) + np.floor(Y / p)) % 2)
            weave = np.where(over > 0, wx * 0.6 + 0.4, wy * 0.6 + 0.4)
            slub = noise2d(H, W, 3, 2, s)
            c = base * (0.78 + 0.22 * weave + 0.06 * (slub - 0.5))[..., None]
            lur = kw.get('lurex')
            if lur:                                                 # a metallic weft floating over 3 warps, then under 1
                every = kw.get('lurex_every', 7)
                ty = (Y / p) % 1
                rowline = (np.floor(Y / p) % every == 0) & (np.floor(X / p) % 4 != 0)
                cyl = 0.7 + 0.45 * np.sin(np.pi * ty)
                shine = 0.9 + 0.18 * np.cos(2 * np.pi * X / 97 + 1.3) + 0.08 * (slub - 0.5)
                c = np.where(rowline[..., None], _c(lur) * (cyl * shine)[..., None], c)
            return c
        if kind == 'glass':
            return base
        raise ValueError(kind)

    # ------------------------------------------------------------ relief and compositing
    def _relief(self, mask, height, soft):
        """lighting multiplier for a mask raised (height > 0) or sunk (height < 0) with rounded edges"""
        h = blur(mask, soft) * height
        n = height_normals(h)
        return 1 + 1.6 * (n @ self.L - self.L[2])

    def drop_shadow(self, mask, dist=8, soft=8, strength=0.45, colour='#1c1712'):
        d = np.array([-self.L[0], -self.L[1]]); d /= np.linalg.norm(d)
        sh = blur(shift(mask, d[0] * dist, d[1] * dist), soft)
        self.img = self.img * (1 - (strength * sh * (1 - mask))[..., None] * (1 - _c(colour)))

    def surface(self, mask, kind='plastic', colour='#e7e3da', height=4, soft=None, shadow=0.0, shadow_dist=None, **kw):
        """lay a part of some material: raised (height > 0, bevelled toward the light) or sunk (height < 0)"""
        sl = self._box(mask, 4)
        if sl is None: return
        soft = soft if soft is not None else max(1.0, abs(height) * 0.7)
        if shadow:
            self.drop_shadow(mask, shadow_dist if shadow_dist is not None else abs(height) * 1.4 + 2, abs(height) * 1.2 + 3, shadow)
        m = mask[sl]
        fill = self.material(kind, colour, sl, **kw)
        rel = self._relief(m, height, soft) if height else 1.0
        fill = fill * np.clip(rel, 0.3, 1.8)[..., None] if height else fill
        self.img[sl] = self.img[sl] * (1 - m[..., None]) + np.clip(fill, 0, 1) * m[..., None]

    def recess(self, mask, kind='painted', colour='#2b2a27', depth=10, **kw):
        """a sunken well: the floor is shaded by the wall on the light side, the far rim catches light"""
        sl = self._box(mask, int(depth * 2 + 6))
        if sl is None: return
        m = mask[sl]
        fill = self.material(kind, colour, sl, **kw)
        d = np.array([-self.L[0], -self.L[1]]); d /= np.linalg.norm(d)
        inner = m * blur(shift(1 - m, d[0] * depth, d[1] * depth), depth * 0.8)
        fill = fill * (1 - 0.6 * inner)[..., None]
        rim = self._relief(m, -depth * 0.6, 2.0)
        self.img[sl] = self.img[sl] * (1 - m[..., None]) + np.clip(fill, 0, 1) * m[..., None]
        edge = np.clip(blur(m, 1.5) - m, 0, 1) + np.clip(m - blur(m, 1.5), 0, 1)
        self.img[sl] = self.img[sl] * np.clip(1 + (rim - 1) * np.clip(edge * 3, 0, 1), 0.5, 1.6)[..., None]

    def paint(self, mask, colour, alpha=1.0):
        """flat colour on top (print, inlay), no relief"""
        a = np.clip(mask * alpha, 0, 1)[..., None]
        self.img = self.img * (1 - a) + _c(colour) * a

    def glow(self, x, y, r, colour, strength=0.6):
        g = np.exp(-((self.XX - x) ** 2 + (self.YY - y) ** 2) / (2 * r * r)) * strength
        self.img = 1 - (1 - self.img) * (1 - g[..., None] * _c(colour))

    # ------------------------------------------------------------ print
    def text(self, s, x, y, size, colour='#2b2a27', font='sans_bold', anchor='mm', spacing=0.0, rot=0.0, alpha=0.95):
        """silkscreened legend"""
        m = text_mask(self.H, self.W, s, load_font(font, size), (x, y), anchor, spacing, rot)
        self.paint(m * (0.92 + 0.08 * self.fine), colour, alpha)

    def scale_arc(self, cx, cy, r0, r1, a0=-135, a1=135, n=11, major=5, colour='#2b2a27', labels=None, label_r=None,
                  size=18, font='sans_bold', width=2.0):
        """printed arc scale; angles in degrees clockwise from 12 o'clock"""
        segs = []
        for i in range(n):
            a = np.deg2rad(a0 + (a1 - a0) * i / (n - 1))
            big = (i % major == 0) if major else True
            ri = r0 if big else r0 + (r1 - r0) * 0.45
            segs.append(((cx + np.sin(a) * ri, cy - np.cos(a) * ri), (cx + np.sin(a) * r1, cy - np.cos(a) * r1), width * (1.4 if big else 0.9)))
        m = np.zeros((self.H, self.W), np.float32)
        for p0, p1, w in segs:
            m = np.maximum(m, self.line_mask([p0, p1], w))
        self.paint(m, colour)
        if labels:
            lr = label_r or r1 + size * 1.1
            for i, lab in enumerate(labels):
                a = np.deg2rad(a0 + (a1 - a0) * i / max(1, len(labels) - 1))
                self.text(lab, cx + np.sin(a) * lr, cy - np.cos(a) * lr, size, colour, font)

    def scale_linear(self, x0, x1, y, n, major=5, length=18, colour='#2b2a27', labels=None, size=20, font='sans_bold', up=True, width=2.0, label_gap=14):
        m = np.zeros((self.H, self.W), np.float32)
        for i in range(n):
            x = x0 + (x1 - x0) * i / (n - 1)
            big = (i % major == 0) if major else True
            L = length if big else length * 0.55
            m = np.maximum(m, self.line_mask([(x, y), (x, y - L if up else y + L)], width * (1.3 if big else 0.9)))
        self.paint(m, colour)
        if labels:
            for i, lab in enumerate(labels):
                if lab is None: continue
                x = x0 + (x1 - x0) * i / max(1, len(labels) - 1)
                self.text(lab, x, y - length - label_gap if up else y + length + label_gap, size, colour, font)

    # ------------------------------------------------------------ controls
    def knob(self, cx, cy, r, angle=0.0, face='#d4d4cf', skirt='#26241f', indicator='#d8452b', knurl=48, skirt_w=None):
        """machined aluminium knob on a dark knurled skirt; angle in degrees clockwise from 12 o'clock"""
        sw = skirt_w if skirt_w is not None else r * 0.22
        R = r + sw
        self.drop_shadow(self.circle(cx, cy, R), dist=r * 0.22, soft=r * 0.2, strength=0.55)
        sk = self.circle(cx, cy, R)
        th = np.arctan2(self.YY - cy, self.XX - cx)
        rr = np.hypot(self.XX - cx, self.YY - cy)
        ridges = 0.5 + 0.5 * np.cos(th * knurl)
        side = 0.55 + 0.45 * np.clip(-(np.cos(th) * self.L[0] + np.sin(th) * self.L[1]), -1, 1)
        skc = _c(skirt)[None, None, :] * (0.7 + 0.6 * side * (0.6 + 0.4 * ridges))[..., None]
        self.img = self.img * (1 - sk[..., None]) + np.clip(skc, 0, 1) * sk[..., None]
        fm = self.circle(cx, cy, r)
        lathe = np.interp(rr, np.arange(0, R + 4, 0.5), fbm1d(int((R + 4) * 2), 2.5, 4, self._seed()))
        sheen = 0.5 + 0.5 * np.cos(2 * (th - np.arctan2(self.L[1], self.L[0])))
        c = _c(face)[None, None, :] * (0.78 + 0.06 * lathe + 0.2 * sheen + 0.02 * (self.fine - 0.5))[..., None]
        chamfer = self.ring(cx, cy, r - 2.5, 5)
        lit = np.clip(-((self.XX - cx) * self.L[0] + (self.YY - cy) * self.L[1]) / (r * 1.1) + 0.5, 0, 1)
        c = c * (1 - chamfer[..., None]) + (c * (0.55 + 0.9 * lit[..., None])) * chamfer[..., None]
        self.img = self.img * (1 - fm[..., None]) + np.clip(c, 0, 1) * fm[..., None]
        a = np.deg2rad(angle)
        p0 = (cx + np.sin(a) * r * 0.25, cy - np.cos(a) * r * 0.25); p1 = (cx + np.sin(a) * r * 0.86, cy - np.cos(a) * r * 0.86)
        ind = self.line_mask([p0, p1], max(3, r * 0.09))
        self.paint(ind * fm, indicator)
        self.paint(self.circle(cx, cy, r * 0.09) * 0.5, '#8a8984')

    def button(self, x0, y0, x1, y1, colour='#efe9dc', pressed=False, label=None, label_colour='#2b2a27', size=18):
        """piano-key push button; a pressed key sits lower and darker"""
        m = self.rrect(x0, y0, x1, y1, 5)
        h = 3 if pressed else 9
        self.surface(m, 'plastic', colour, height=h, soft=3, shadow=0.35 if not pressed else 0.15, shadow_dist=h * 0.8)
        if pressed:
            self.paint(m, '#000000', 0.08)
        top = self.rrect(x0 + 3, y0 + 3, x1 - 3, y0 + (y1 - y0) * 0.35, 3)
        self.paint(top, '#ffffff', 0.08 if pressed else 0.16)
        if label:
            self.text(label, (x0 + x1) / 2, y0 + (y1 - y0) * 0.64, size, label_colour, 'sans_bold', spacing=1.5)

    def toggle(self, x, y, up=True, length=64, colour='#dcdcd8'):
        """bat-handle toggle switch: a chrome hex nut and a tapered lever"""
        nut = self.poly([(x + np.cos(a) * 26, y + np.sin(a) * 26) for a in np.linspace(0, 2 * np.pi, 6, endpoint=False) + np.pi / 6])
        self.surface(nut, 'brushed', '#c9c9c4', height=6, soft=2, shadow=0.4)
        self.surface(self.circle(x, y, 13), 'brushed', '#b8b8b2', height=5, soft=2)
        d = -1 if up else 1
        tip = (x + 6, y + d * length)
        lever = self.poly([(x - 7, y), (x + 7, y), (tip[0] + 5, tip[1]), (tip[0] - 5, tip[1])])
        self.drop_shadow(lever, dist=10, soft=5, strength=0.45)
        u = np.clip((self.XX - (x - 7 + (tip[0] - x) * np.clip((self.YY - y) / (d * length), 0, 1))) / 14, 0, 1)
        cyl = 0.55 + 0.6 * np.exp(-((u - 0.3) / 0.18) ** 2) + 0.1 * u
        self.img = self.img * (1 - lever[..., None]) + np.clip(_c(colour) * cyl[..., None], 0, 1) * lever[..., None]
        ball = self.circle(tip[0], tip[1], 8.5)
        self.surface(ball, 'brushed', colour, height=7, soft=4)

    def lamp(self, x, y, r, colour='#ffb347', on=True, bezel='#c9c9c4'):
        """jewel pilot lamp in a chrome bezel, glowing when on"""
        self.surface(self.circle(x, y, r + r * 0.45), 'brushed', bezel, height=5, soft=2, shadow=0.35)
        lens = self.circle(x, y, r)
        rr = np.hypot(self.XX - x, self.YY - y) / r
        facets = 0.5 + 0.5 * np.cos(np.arctan2(self.YY - y, self.XX - x) * 8)
        col = _c(colour)
        if on:
            c = col[None, None, :] * (1.15 - 0.5 * rr[..., None] + 0.12 * facets[..., None]) + (1 - col) * np.clip(0.8 - rr, 0, 1)[..., None]
        else:
            c = col[None, None, :] * (0.45 - 0.2 * rr[..., None] + 0.08 * facets[..., None])
        self.img = self.img * (1 - lens[..., None]) + np.clip(c, 0, 1) * lens[..., None]
        self.paint(self.circle(x - r * 0.35, y - r * 0.38, r * 0.22), '#ffffff', 0.7)
        if on:
            self.glow(x, y, r * 2.4, colour, 0.45)

    def magic_eye(self, x, y, r, tuned=0.7):
        """green 'magic eye' tuning tube: glowing fluorescent petals around a dark cap, the shadow wedge
        closes as the station is tuned in"""
        self.surface(self.circle(x, y, r * 1.35), 'brushed', '#c9c9c4', height=5, soft=2, shadow=0.35)
        win = self.circle(x, y, r)
        self.paint(win, '#0b1a10')
        th = np.arctan2(self.XX - x, -(self.YY - y))                          # 0 at 12 o'clock, clockwise
        rr = np.hypot(self.XX - x, self.YY - y) / r
        gap = np.deg2rad(8 + 70 * (1 - tuned))
        shadow_wedge = (np.abs(th) < gap)
        petals = (rr > 0.28) * (rr < 0.95) * (~shadow_wedge)
        fl = np.clip(1.1 - rr * 0.7, 0, 1) * (0.85 + 0.15 * np.cos(th * 24))
        self.paint(win * petals * fl, '#6cff8a', 0.95)
        self.glow(x, y, r * 1.2, '#57e07a', 0.25)
        self.paint(self.circle(x, y, r * 0.3), '#1c1f1c')
        self.paint(self.circle(x - r * 0.3, y - r * 0.4, r * 0.18) * win, '#ffffff', 0.25)

    def meter(self, x0, y0, x1, y1, value=0.6, face='#f2e6c9', label='VU'):
        """moving-coil meter behind glass: printed arc scale, red zone, black needle"""
        m = self.rrect(x0, y0, x1, y1, 8)
        self.recess(m, 'plastic', face, depth=8)
        cx, cy = (x0 + x1) / 2, y1 - (y1 - y0) * 0.12
        R = (y1 - y0) * 0.72
        self.scale_arc(cx, cy, R * 0.86, R * 0.96, -50, 50, 21, 5, '#2b2a27', width=1.6)
        red = self.ring(cx, cy, R * 0.99, 5) * (np.arctan2(self.XX - cx, -(self.YY - cy)) > np.deg2rad(22))
        self.paint(red * m, '#c8332a')
        self.text(label, cx, cy - R * 0.45, (y1 - y0) * 0.14, '#2b2a27', 'sans_bold')
        a = np.deg2rad(-50 + 100 * value)
        self.paint(self.line_mask([(cx, cy), (cx + np.sin(a) * R * 0.98, cy - np.cos(a) * R * 0.98)], 2.4) * m, '#161514')
        self.glass(m)

    def glass(self, mask, streak=0.12):
        """a sheet of glass over a window: diagonal reflection streaks and a faint top shadow"""
        d = (self.XX * 0.55 + self.YY) / 60
        refl = np.clip(np.sin(d * 0.8) - 0.55, 0, 1) * 2.2 + np.clip(np.sin(d * 0.8 + 1.4) - 0.9, 0, 1) * 4
        self.img = self.img + (mask * refl * streak)[..., None] * np.array([1, 1, 1], np.float32)
        self.img = np.clip(self.img, 0, 1)

    def screw(self, x, y, r=9, slot=None):
        self.surface(self.circle(x, y, r), 'brushed', '#bdbdb7', height=4, soft=r * 0.5, shadow=0.35, shadow_dist=3)
        a = slot if slot is not None else self.rng.uniform(0, np.pi)
        sl = self.line_mask([(x - np.cos(a) * r * 0.8, y - np.sin(a) * r * 0.8), (x + np.cos(a) * r * 0.8, y + np.sin(a) * r * 0.8)], max(1.6, r * 0.22))
        self.paint(sl * self.circle(x, y, r), '#4d4b46', 0.85)

    def grille(self, mask, pitch=22, r=6, colour='#34322e', stagger=True):
        """perforated metal: a grid of drilled holes (each with a dark hole and a light lower lip)"""
        sl = self._box(mask)
        if sl is None: return
        X, Y = self.XX[sl], self.YY[sl]
        row = np.round(Y / (pitch * (0.866 if stagger else 1)))
        yc = row * pitch * (0.866 if stagger else 1)
        off = (row % 2) * pitch / 2 if stagger else 0
        xc = np.round((X - off) / pitch) * pitch + off
        d = np.hypot(X - xc, Y - yc)
        hole = np.clip(r - d + 0.5, 0, 1) * mask[sl]
        lip = np.clip(r - np.hypot(X - xc + 1.2, Y - yc + 1.6) + 0.5, 0, 1)
        m = self.img[sl]
        m = m * (1 - hole[..., None] * (1 - _c(colour)) * 0.95)
        m = m + (np.clip(hole - lip, 0, 1) * 0.35)[..., None]
        self.img[sl] = np.clip(m, 0, 1)

    def badge(self, s, x, y, size, font='script', colour='#d9d6cc', anchor='mm'):
        """chrome script badge: raised polished letters with a bevel and a small shadow"""
        m = text_mask(self.H, self.W, s, load_font(font, size), (x, y), anchor)
        sl = self._box(m, 12)
        if sl is None: return
        self.drop_shadow(m, dist=4, soft=3, strength=0.5)
        mm = m[sl]
        rel = self._relief(mm, 5, 1.6)
        grad = 0.75 + 0.35 * np.cos((self.YY[sl] - y) / size * 5.5)
        c = _c(colour)[None, None, :] * (grad * np.clip(rel, 0.4, 1.9))[..., None]
        self.img[sl] = self.img[sl] * (1 - mm[..., None]) + np.clip(c, 0, 1) * mm[..., None]

    # ------------------------------------------------------------ output
    def background(self, colour, kind='painted', **kw):
        sl = (slice(0, self.H), slice(0, self.W))
        self.img = self.material(kind, colour, sl, **kw)

    def composite(self, vignette=0.14):
        r = np.hypot((self.XX - self.W / 2) / self.W, (self.YY - self.H / 2) / self.H)
        img = self.img * (1 - vignette * r ** 2 * 2.2)[..., None]
        return Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))

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
