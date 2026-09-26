"""oilpaint — impasto oil painting with directional strokes and lit paint relief (numpy + Pillow only).

Model (in the spirit of Van Gogh):
  1. you describe the scene as a *reference colour field* (numpy RGB) and a *flow field* (stroke angle per pixel);
  2. thousands of short strokes are laid in passes (big underpainting strokes, then smaller detail strokes),
     each oriented by the flow field and coloured from the reference, with a little hue/value jitter;
  3. an ID map remembers which stroke is on top at every pixel, so each pixel knows where it sits inside
     its stroke -> paint thickness (rounded ridge), bristle grooves along the stroke, thicker blobs at the start;
  4. the height map is lit (normals, raking light + small speculars) -> real impasto relief.

    from oilpaint import OilPainting
    o = OilPainting(1920, 1080, seed=1)
    ref = ...  # HxWx3 float colours
    ang = ...  # HxW stroke angles (radians)
    o.layer(ref, ang, length=(40, 80), width=(14, 22))     # underpainting
    o.layer(ref, ang, length=(18, 40), width=(7, 12))      # detail
    o.save('out.png')
"""
import numpy as np
from PIL import Image, ImageDraw
from core import blur, noise2d, smoothstep


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


class OilPainting:
    def __init__(self, W=1920, H=1080, seed=0):
        self.W, self.H = W, H
        self.rng = np.random.default_rng(seed)
        self.YY, self.XX = np.mgrid[0:H, 0:W].astype(np.float32)
        self.ids = np.full((H, W), -1, np.int32)
        self.cx = []; self.cy = []; self.dx = []; self.dy = []; self.hl = []; self.hw = []; self.col = []; self.ph = []; self.thick = []
        self.stages = []
        # canvas weave shows through where paint is thin
        wx = np.sin(self.XX * 1.9) * 0.5 + 0.5; wy = np.sin(self.YY * 1.9) * 0.5 + 0.5
        self.canvas = np.ones((H, W, 3), np.float32) * hexc('#e9dfc9') * (0.9 + 0.1 * (wx * wy))[..., None]

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    def noise(self, scale, octaves=3):
        return noise2d(self.H, self.W, scale, octaves, self._seed())

    # ------------------------------------------------------------ strokes
    def layer(self, ref, angle, length=(30, 70), width=(10, 18), density=1.4, jitter=0.06, value_jitter=0.06, thickness=1.0, mask=None):
        """lay one pass of strokes over the canvas (or only where mask > 0.5)"""
        H, W = self.H, self.W
        area = W * H if mask is None else float((mask > 0.5).sum())
        mean = np.mean(length) * np.mean(width)
        n = int(area / mean * density)
        xs = self.rng.uniform(0, W, n); ys = self.rng.uniform(0, H, n)
        if mask is not None:
            keep = mask[ys.astype(int).clip(0, H - 1), xs.astype(int).clip(0, W - 1)] > 0.5
            xs, ys = xs[keep], ys[keep]
        im = Image.fromarray(self.ids.astype(np.int32))
        d = ImageDraw.Draw(im)
        base = len(self.cx)
        for i in range(len(xs)):
            x, y = xs[i], ys[i]
            ix, iy = int(x), int(y)
            a = angle[iy, ix] + self.rng.normal(0, jitter)
            L = self.rng.uniform(*length) / 2; Wd = self.rng.uniform(*width) / 2
            c = ref[iy, ix] * (1 + self.rng.normal(0, value_jitter)) + self.rng.normal(0, value_jitter * 0.4, 3)
            dx, dy = np.cos(a), np.sin(a)
            # rounded-rectangle outline of the stroke
            pts = []
            for t in np.linspace(-np.pi / 2, np.pi / 2, 6):          # rounded head
                pts.append((x + dx * L + (dx * np.cos(t) * Wd - dy * np.sin(t) * Wd) * 0.9, y + dy * L + (dy * np.cos(t) * Wd + dx * np.sin(t) * Wd) * 0.9))
            for t in np.linspace(np.pi / 2, 3 * np.pi / 2, 6):        # rounded tail
                pts.append((x - dx * L + (dx * np.cos(t) * Wd - dy * np.sin(t) * Wd) * 0.9, y - dy * L + (dy * np.cos(t) * Wd + dx * np.sin(t) * Wd) * 0.9))
            k = base + i
            d.polygon(pts, fill=k)
            self.cx.append(x); self.cy.append(y); self.dx.append(dx); self.dy.append(dy)
            self.hl.append(L); self.hw.append(Wd); self.col.append(np.clip(c, 0, 1)); self.ph.append(self.rng.uniform(0, 6.28))
            self.thick.append(thickness * self.rng.uniform(0.7, 1.15))
        self.ids = np.asarray(im, np.int32)

    def stroke_at(self, x, y, angle, length, width, colour, thickness=1.0):
        """one explicit stroke (signatures, birds, accents)"""
        c = hexc(colour) if isinstance(colour, str) else np.asarray(colour, np.float32)
        ref = np.broadcast_to(c, (self.H, self.W, 3))
        m = np.zeros((self.H, self.W), np.float32); m[int(y), int(x)] = 1
        n0 = len(self.cx)
        im = Image.fromarray(self.ids.astype(np.int32)); d = ImageDraw.Draw(im)
        dx, dy = np.cos(angle), np.sin(angle); L = length / 2; Wd = width / 2
        pts = []
        for t in np.linspace(-np.pi / 2, np.pi / 2, 6):
            pts.append((x + dx * L + (dx * np.cos(t) * Wd - dy * np.sin(t) * Wd) * 0.9, y + dy * L + (dy * np.cos(t) * Wd + dx * np.sin(t) * Wd) * 0.9))
        for t in np.linspace(np.pi / 2, 3 * np.pi / 2, 6):
            pts.append((x - dx * L + (dx * np.cos(t) * Wd - dy * np.sin(t) * Wd) * 0.9, y - dy * L + (dy * np.cos(t) * Wd + dx * np.sin(t) * Wd) * 0.9))
        d.polygon(pts, fill=n0)
        self.ids = np.asarray(im, np.int32)
        self.cx.append(x); self.cy.append(y); self.dx.append(dx); self.dy.append(dy)
        self.hl.append(L); self.hw.append(Wd); self.col.append(c); self.ph.append(self.rng.uniform(0, 6.28)); self.thick.append(thickness)

    # ------------------------------------------------------------ render
    def render(self, light=(-0.55, -0.65, 0.52), relief=2.4, spec=0.1, bristles=7):
        ids = self.ids
        painted = ids >= 0
        k = np.where(painted, ids, 0)
        cx = np.asarray(self.cx, np.float32)[k]; cy = np.asarray(self.cy, np.float32)[k]
        dx = np.asarray(self.dx, np.float32)[k]; dy = np.asarray(self.dy, np.float32)[k]
        hl = np.asarray(self.hl, np.float32)[k]; hw = np.asarray(self.hw, np.float32)[k]
        ph = np.asarray(self.ph, np.float32)[k]; th = np.asarray(self.thick, np.float32)[k]
        col = np.asarray(self.col, np.float32)[k]
        px, py = self.XX - cx, self.YY - cy
        along = (px * dx + py * dy) / (hl + hw)             # -1 tail .. +1 head
        across = (-px * dy + py * dx) / hw                   # -1 .. 1 across the stroke
        ridge = smoothstep(0.0, 0.45, 1 - np.abs(across)) * (1 + 0.18 * np.abs(across) ** 3)   # flat top, paint pushed to the edges
        groove = 1 + 0.12 * np.sin(across * bristles * np.pi + ph) + 0.05 * np.sin(along * 11 + ph * 2)
        start_blob = 1 + 0.35 * np.clip(1 - (along + 1) * 2.5, 0, 1)          # paint piles up where the brush lands
        end_fade = np.clip((1 - along) * 3, 0, 1) * 0.5 + 0.5
        h = ridge * groove * start_blob * end_fade * th * painted
        h = blur(h, 0.8)
        gx = np.gradient(h, axis=1) * relief; gy = np.gradient(h, axis=0) * relief
        nz = 1 / np.sqrt(gx ** 2 + gy ** 2 + 1)
        nx, ny = -gx * nz, -gy * nz
        L = np.asarray(light, np.float32); L = L / np.linalg.norm(L)
        diffuse = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
        hv = L + np.array([0, 0, 1], np.float32); hv /= np.linalg.norm(hv)
        specular = np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1) ** 24
        base = np.where(painted[..., None], col * (1 + 0.05 * (groove - 1))[..., None], self.canvas)
        shade = (0.8 + 0.38 * diffuse)[..., None]
        img = base * shade + spec * specular[..., None] * painted[..., None]
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
