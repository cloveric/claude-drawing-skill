"""cyanotype — sun print / photogram in Prussian blue (numpy + Pillow only).

Model (how a real cyanotype is made):
  1. rag paper is brushed with iron-salt emulsion -> the coated area has ragged, streaky brushed edges
     and uneven thickness (it only turns blue where it was coated);
  2. objects are laid on it under glass and the sheet is put in the sun. Each object *blocks* part of the UV:
     transmission multiplies, T = product(1 - opacity_i * mask_i). Thin leaves let a little light through
     (a pale blue body with whiter veins); things that don't lie flat (fluff, curled stems) are lifted off the
     paper and cast a soft penumbra instead of a sharp edge; light also scatters a little under every edge;
  3. exposure E = coat x T x (uneven sunlight) is developed in water: Prussian-blue density D = 1 - exp(-k E),
     mapped through paper-white -> pale cyan -> deep Prussian blue; the paper tooth shows through the blue.
White handwriting can be printed in (written on a transparency, `label`), and pencil notes added on the
paper margin afterwards (`pencil`).

    from cyanotype import Cyanotype
    cy = Cyanotype(1920, 1080, seed=1)
    cy.coat(90, 70, 1830, 1010)                                  # brushed emulsion area
    cy.place(cy.shapes([leaf1, leaf2]), opacity=0.9)             # leaves pressed flat
    cy.place(cy.lines([vein1, vein2], 2), opacity=1.0)           # veins block fully -> whiter
    cy.place(cy.lines(fluff, 1.2), opacity=0.35, lift=3)         # fluff lifted off the paper -> soft
    cy.label('Ginkgo biloba', 1500, 960, 44)
    cy.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts, load_font, text_mask


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


class Cyanotype:
    RAMP = [(0.0, '#f3f0e6'), (0.18, '#c9d9e6'), (0.42, '#7ea5cc'), (0.68, '#2e64a1'), (0.86, '#174a86'), (1.0, '#0f3466')]

    def __init__(self, W=1920, H=1080, seed=0, paper='#f4f1e7', ramp=None, strength=3.0):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.paper_col = _c(paper)
        self.ramp = ramp or self.RAMP
        self.k = strength
        self.trans = np.ones((H, W), np.float32)             # how much UV reaches the paper
        self.coat_m = None
        s = int(self.rng.integers(1 << 30))
        self.tooth = noise2d(H, W, 1.8, 2, s) * 0.6 + noise2d(H, W, 6, 2, s + 1) * 0.4
        self.sun = 0.9 + 0.14 * noise2d(H, W, 380, 3, s + 2)  # uneven sunlight / glass / coating thickness
        self.labels = []
        self.notes = []
        self.stages = []

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ------------------------------------------------------------ the brushed emulsion
    def coat(self, x0, y0, x1, y1, ragged=1.0, strokes=None, splatter=14):
        """brush the emulsion onto a rectangle with overlapping horizontal brush strokes (~140 px wide):
        every stroke starts and stops at its own place, its ends thin into dry-brush bristle streaks,
        the top and bottom edges are the gently wavy sides of the first and last strokes"""
        H, W = self.H, self.W
        X, Y = self.XX, self.YY
        n = strokes or max(3, int(round((y1 - y0) / 130)))
        pitch = (y1 - y0) / n
        cov = np.zeros((H, W), np.float32)
        for k in range(n):
            s = self._seed()
            top = y0 + k * pitch - (0 if k == 0 else pitch * 0.18)
            bot = y0 + (k + 1) * pitch + (0 if k == n - 1 else pitch * 0.18)
            wav_t = fbm1d(W, 160, 3, s) * 10 * ragged + fbm1d(W, 6, 2, s + 1) * 1.2 * ragged
            wav_b = fbm1d(W, 160, 3, s + 2) * 10 * ragged + fbm1d(W, 6, 2, s + 3) * 1.2 * ragged
            band = smoothstep(-1.5, 1.5, Y - (top + wav_t)[None, :]) * smoothstep(-1.5, 1.5, (bot + wav_b)[None, :] - Y)
            xs = x0 + self.rng.normal(0, 22) * ragged; xe = x1 + self.rng.normal(0, 22) * ragged
            hair = np.interp(Y[:, 0], np.arange(H), fbm1d(H, 2.5, 3, s + 4))              # per-hair variation, ~1 px
            clump = np.interp(Y[:, 0], np.arange(H), fbm1d(H, 16, 3, s + 5))              # hairs clump in groups
            reach = (0.35 * hair + 0.65 * clump)[:, None] * 0.5 + 0.5                       # 0..1: how far each hair drags on
            dry = 80 * ragged
            end_s = xs - dry * reach; end_e = xe + dry * reach
            sharp = smoothstep(-1.2, 1.2, X - end_s) * smoothstep(-1.2, 1.2, end_e - X)    # every hair stops crisply
            inner = smoothstep(0, dry * 1.2, np.minimum(X - end_s, end_e - X))            # 0 at the ragged end .. 1 inside
            streaks = np.asarray(Image.fromarray(self.rng.random((H // 2, W // 14)).astype(np.float32)).resize((W, H), Image.BILINEAR))
            keep = smoothstep(0.42, 0.5, streaks * 0.8 + inner * 0.55 + 0.1)             # dry brush breaks up near the ends
            thick = 0.94 + 0.06 * (np.interp(Y[:, 0], np.arange(H), fbm1d(H, 9, 3, s + 6))[:, None])
            cov = np.maximum(cov, band * sharp * keep * (0.82 + 0.18 * inner) * thick)
        for _ in range(splatter):                              # a few drops flicked off the brush
            side = int(self.rng.integers(4))
            if side < 2:
                x = self.rng.uniform(x0, x1); y = (y0 - self.rng.uniform(8, 40)) if side == 0 else (y1 + self.rng.uniform(8, 40))
            else:
                y = self.rng.uniform(y0, y1); x = (x0 - self.rng.uniform(70, 130)) if side == 2 else (x1 + self.rng.uniform(70, 130))
            r = self.rng.uniform(1.2, 4.5)
            cov = np.maximum(cov, np.clip(r - np.hypot(X - x, (Y - y) * self.rng.uniform(0.8, 1.3)) + 0.5, 0, 1) * 0.9)
        self.coat_m = np.clip(cov, 0, 1).astype(np.float32)

    # ------------------------------------------------------------ masks
    def shapes(self, polys, ss=2):
        """many closed outlines -> one mask, drawn in a single pass (fast for hundreds of leaflets)"""
        im = Image.new('L', (self.W * ss, self.H * ss), 0); d = ImageDraw.Draw(im)
        for pts in polys:
            d.polygon([(float(x) * ss, float(y) * ss) for x, y in pts], fill=255)
        if ss > 1: im = im.resize((self.W, self.H), Image.BILINEAR)
        return np.asarray(im, np.float32) / 255

    def lines(self, polylines, width, ss=2, taper=False):
        """many open polylines (stems, veins, filaments) -> one mask; taper=True thins each line toward its end"""
        im = Image.new('L', (self.W * ss, self.H * ss), 0); d = ImageDraw.Draw(im)
        for pts in polylines:
            P = [(float(x) * ss, float(y) * ss) for x, y in pts]
            if not taper or len(P) < 3:
                d.line(P, fill=255, width=max(1, int(round(width * ss))), joint='curve')
            else:
                n = len(P) - 1
                for i in range(n):
                    w = width * (1 - 0.75 * i / n)
                    d.line([P[i], P[i + 1]], fill=255, width=max(1, int(round(w * ss))))
                    r = w * ss / 2
                    d.ellipse((P[i + 1][0] - r, P[i + 1][1] - r, P[i + 1][0] + r, P[i + 1][1] + r), fill=255)
        if ss > 1: im = im.resize((self.W, self.H), Image.BILINEAR)
        return np.asarray(im, np.float32) / 255

    def poly(self, pts):
        return polygon_mask(self.H, self.W, pts, ss=2)

    def circle(self, cx, cy, r):
        return np.clip(r - np.hypot(self.XX - cx, self.YY - cy) + 0.5, 0, 1)

    @staticmethod
    def leaf_pts(x, y, angle, length, width, tip=0.55, n=28, serrate=0.0, blunt=0.0):
        """a simple leaf/leaflet outline from its base (x, y) pointing along `angle`.
        tip < 0.5 fattens toward the tip; blunt 0..1 rounds the tip off (oblong fern pinnules);
        serrate > 0 adds small teeth"""
        t = np.linspace(0, 1, n)
        pointed = np.sin(np.pi * t ** tip) * (1 - 0.15 * t)
        oval = np.sqrt(np.clip(1 - (2 * t - 1) ** 2, 0, 1))
        half = width / 2 * ((1 - blunt) * pointed + blunt * oval)
        if serrate:
            half = half * (1 + serrate * (np.arange(n) % 2) * np.sin(np.pi * t))
        c, s = np.cos(angle), np.sin(angle)
        up = [(x + c * length * ti - s * hi, y + s * length * ti + c * hi) for ti, hi in zip(t, half)]
        dn = [(x + c * length * ti + s * hi, y + s * length * ti - c * hi) for ti, hi in zip(t[::-1], half[::-1])]
        return np.array(up + dn, np.float32)

    # ------------------------------------------------------------ laying things on the paper
    def place(self, mask, opacity=1.0, lift=0.0, texture=0.0):
        """lay an object on the paper. opacity: how much UV it stops (thin leaf ~0.85, card 1.0, fluff ~0.3);
        lift: px it stands off the paper (0 pressed flat under glass -> sharp; 2-8 -> soft penumbra);
        texture: internal unevenness of a translucent object (leaf tissue)"""
        m = blur(mask, lift) if lift > 0 else mask
        m = blur(m, 0.6)                                      # even pressed edges are not razor sharp
        op = opacity
        if texture:
            op = opacity * (1 - texture * noise2d(self.H, self.W, 14, 3, self._seed()))
        self.trans *= (1 - np.clip(m * op, 0, 1))

    def line(self, pts, width, opacity=1.0, lift=0.0, taper=False):
        self.place(self.lines([pts], width, taper=taper), opacity, lift)

    def label(self, s, x, y, size=44, font='hand', anchor='la', rot=0.0, opacity=0.96):
        """white handwriting printed with the plants (ink on a transparency laid on the paper)"""
        self.labels.append((s, x, y, size, font, anchor, rot, opacity))

    def pencil(self, s, x, y, size=30, font='hand', anchor='la', rot=0.0, colour='#6b6f78'):
        """graphite note written on the paper margin after the print was washed"""
        self.notes.append((s, x, y, size, font, anchor, rot, colour))

    # ------------------------------------------------------------ develop
    def _colour(self, D):
        xs = [p for p, _ in self.ramp]
        cols = np.stack([_c(c) for _, c in self.ramp])
        out = np.empty(D.shape + (3,), np.float32)
        for ch in range(3):
            out[..., ch] = np.interp(D, xs, cols[:, ch])
        return out

    def develop(self):
        trans = self.trans.copy()
        for (s, x, y, size, font, anchor, rot, op) in self.labels:
            m = text_mask(self.H, self.W, s, load_font(font, size), (x, y), anchor, rot=rot)
            trans *= 1 - blur(m, 0.7) * op
        blocked = 1 - trans
        halo = blur(blocked, 5) * 0.22 + blur(blocked, 16) * 0.08       # light scattering under the edges
        t_eff = np.clip(trans * (1 - halo), 0, 1)
        coat = self.coat_m if self.coat_m is not None else np.ones((self.H, self.W), np.float32)
        E = coat * t_eff * self.sun
        D = (1 - np.exp(-self.k * E)) / (1 - np.exp(-self.k))
        D = np.clip(D * (1 - 0.07 * (self.tooth - 0.5)) - 0.02 * (self.tooth > 0.8), 0, 1)
        img = self._colour(D)
        paper = self.paper_col * (0.975 + 0.04 * self.tooth)[..., None]
        img = img * (paper / _c(self.ramp[0][1]))                     # paper fibre shows through the whole sheet
        stain = coat * (1 - D) * 0.06                                   # washed-out emulsion leaves a faint blue cast in the whites
        img = img * (1 - stain[..., None]) + _c('#9fbfd8') * stain[..., None]
        return img

    def composite(self):
        img = self.develop()
        for (s, x, y, size, font, anchor, rot, colour) in self.notes:
            m = text_mask(self.H, self.W, s, load_font(font, size), (x, y), anchor, rot=rot)
            m = m * (0.6 + 0.4 * self.tooth)                           # graphite catches on the tooth
            img = img * (1 - m[..., None] * (1 - _c(colour)))
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
