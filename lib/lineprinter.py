"""lineprinter — ASCII art from a 1970s impact line printer on greenbar continuous paper (numpy + Pillow only).

Model:
  form     : continuous fanfold "greenbar" paper, 14 7/8 x 11 in, printed at 10 characters per inch and 6 lines
             per inch (132 columns, 66 lines a page). Pale green bands 1/2 in tall (exactly 3 print lines) are
             flexo-printed across the form; a tractor strip on each side carries 5/32 in feed holes every 1/2 in and
             is split off by a line of micro-perforations; a cross perforation and a fanfold crease mark each page
             break (11 in deep by default; `page_in=8.5` with a smaller `ppi` puts a whole sheet, tear line to tear
             line, on the desk). Holes look through to the desk, with the paper's own shadow inside them.
  picture  : nothing is painted on the paper. The scene is painted into a hidden *role map* at sub-cell
             resolution (6 x 10 samples per character cell), in painter's order:
               fill(mask, role, tone)   a region: which glyph vocabulary (role) and how much ink it wants (tone);
               stroke(points)           a drawn line (tower struts, outlines, antennae);
               text(s, col, row)        literal characters (headers, log lines, a printer plot).
             Shading helpers give tones the way light would: `sphere_tone` (smoke puffs), `cylinder_tone`
             (a turned body), `billow` (a cloud of puffs that shadow each other and can be lit from below).
  glyphs   : `compose()` decides every cell:
               line cells -> by the stroke's direction measured in real pixels (cells are tall) and where it sits in
                             the cell: | / \\ for steep, _ - . ' for flat and shallow (so curves come out as _.-'),
                             X and + where two strokes cross; a stroke smeared over two cells keeps the stronger one;
               edge cells -> where a silhouette turns, the same rule on the boundary between two regions; 'round'
                             roles use ( ) for upright sides, a flat top edge high in its cell moves up a row as '_';
               fill cells -> the role's ramp, light to dark, chosen by tone with error diffusion inside the role (so
                             % @ # blend into each other instead of forming hard contour bands);
               darkest    -> overstrikes: ramp entries like '#@' are printed on top of each other in extra passes.
  printing : a drum printer: one hammer per column fires through an inked fabric ribbon against a spinning type
             drum. Each impression is the type slug: ragged edge and grain from the ribbon weave and paper tooth;
             a weak impression gets thinner and breaks up instead of turning grey. Drum timing makes each character
             sit a little high or low (same character, same error), every hammer has its own force (a weak hammer
             leaves a pale column down the page), the ribbon fades as the job runs and wears across its width, some
             lines are printed with the ribbon riding low (character tops starve), overstrike passes land a fraction
             of a pixel off, worn slugs print the same nick every time; ink wicks into the paper and the hammer
             leaves a faint emboss.
  after    : someone reads the printout with a ballpoint: `pen`, `ring`, `tick`, `pen_text`.

    from lineprinter import LinePrinter
    lp = LinePrinter(1920, 1080, seed=3)
    lp.form()
    lp.role('smoke', ['', '.', ':', '+', '%', '@', '#', '#@'])
    puffs = [(40, 30, 6), (50, 28, 7), (58, 31, 5)]           # (col, row, radius in columns)
    lp.billow(puffs, 'smoke')
    lp.stroke([(20, 10), (20, 30)])                            # a vertical line -> '|' cells
    lp.text('T+00:03  LIFTOFF', 96, 5, strike=2)                # bold by double strike
    lp.print_rows(0, lp.rows)
    lp.save('out.jpg')
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core import blur, fbm1d, spline, noise2d, smoothstep, polygon_mask, blob_pts, shift, load_font


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _c(c):
    return hexc(c) if isinstance(c, str) else np.asarray(c, np.float32)


def gauss(a, sigma):
    """separable gaussian blur (edge padded), fine for small sigmas on big arrays"""
    if sigma <= 0.05: return a.astype(np.float32)
    r = max(1, int(np.ceil(sigma * 3)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2).astype(np.float32); k /= k.sum()
    out = a.astype(np.float32)
    for ax in (0, 1):
        pad = [(0, 0), (0, 0)]; pad[ax] = (r, r)
        p = np.pad(out, pad, mode='edge')
        n = out.shape[ax]
        acc = np.zeros_like(out)
        for i, w in enumerate(k):
            acc += w * (p[i:i + n] if ax == 0 else p[:, i:i + n])
        out = acc
    return out


_MONO = [('/System/Library/Fonts/Menlo.ttc', 1), ('/usr/share/fonts/**/DejaVuSansMono-Bold.ttf', 0),
         ('/usr/share/fonts/**/LiberationMono-Bold.ttf', 0), ('C:/Windows/Fonts/consolab.ttf', 0),
         ('C:/Windows/Fonts/courbd.ttf', 0), ('/System/Library/Fonts/Supplemental/Courier New Bold.ttf', 0)]


def mono_font(size, weight='regular'):
    """the print-chain face: a monospaced sans (ink spread makes it heavier). $INKPAINT_FONT_LINEPRINTER overrides"""
    import glob
    env = os.environ.get('INKPAINT_FONT_LINEPRINTER')
    if env and os.path.exists(env): return ImageFont.truetype(env, int(size))
    cands = _MONO if weight == 'bold' else [('/System/Library/Fonts/Menlo.ttc', 0), ('/usr/share/fonts/**/DejaVuSansMono.ttf', 0),
                                            ('/usr/share/fonts/**/LiberationMono-Regular.ttf', 0), ('C:/Windows/Fonts/consola.ttf', 0),
                                            ('C:/Windows/Fonts/cour.ttf', 0)] + _MONO
    for pat, idx in cands:
        for f in glob.glob(pat, recursive=True):
            try:
                return ImageFont.truetype(f, int(size), index=idx)
            except OSError:
                pass
    return load_font('typewriter', size)


# how a line or a silhouette edge becomes a character, by its direction and where it sits in the cell
OUTLINES = {
    'straight': dict(v='|', h='-', low='_', dot='.', tick="'", up='/', down='\\', x='X', plus='+', left='|', right='|',
                     top='_'),
    'round': dict(v='|', h='-', low='_', dot='.', tick="'", up='/', down='\\', x='X', plus='+', left='(', right=')',
                  top=None),
}


def _style(st):
    if isinstance(st, dict): return dict(OUTLINES['straight'], **st)
    return OUTLINES[st or 'straight']


INK = '#22222c'                     # black nylon ribbon, slightly blue as it ages


class LinePrinter:
    def __init__(self, W=1920, H=1080, seed=0, cols=132, top=40.0, cpi=10, lpi=6, form_in=14.875, ss=2,
                 ink=INK, sub=(6, 10), weight='bold', ppi=None, page_in=11.0):
        """ppi=None fits the form's width to the picture; a smaller ppi shows the desk on both sides.
        page_in: form depth (11 in = 66 lines; 8.5 in = 51 lines shows a whole page between two tear lines)"""
        self.W, self.H, self.ss = W, H, ss
        self.rng = np.random.default_rng(seed)
        self.ppi = ppi or W / form_in
        self.cw, self.ch = self.ppi / cpi, self.ppi / lpi                   # character cell in px
        self.px0 = (W - form_in * self.ppi) / 2                             # paper edges
        self.px1 = self.px0 + form_in * self.ppi
        self.page_rows = int(round(page_in * lpi))                         # lines from one tear line to the next
        self.cols = cols
        self.xl = (W - cols * self.cw) / 2                                  # left edge of column 0
        self.top = float(top)                                               # page break (row 0 starts here)
        self.rows = int(np.ceil((H - top) / self.ch))
        self.sx, self.sy = sub
        SY, SX = self.rows * self.sy, cols * self.sx
        self.inst = np.zeros((SY, SX), np.int32)        # painter's-order instance id (0 = bare paper)
        self.rmap = np.zeros((SY, SX), np.int16)        # role id
        self.tone = np.zeros((SY, SX), np.float32)      # ink wanted 0..1
        self.line = np.zeros((SY, SX), np.float32)      # stroke coverage
        self.lset = np.zeros((SY, SX), np.int16)        # which glyph set a stroke uses
        self._n = 0
        self.Y, self.X = (np.mgrid[0:SY, 0:SX].astype(np.float32) + 0.5) / np.array([self.sy, self.sx], np.float32)[:, None, None]
        self.roles = {'paper': dict(id=0, ramp=[''], edge=None, outline=_style('straight'), dither=0.0, noise=0.0,
                                    group='paper', inner_max=1.0)}
        self._role_by_id = ['paper']
        self.line_sets = [_style('straight')]
        self.fixed = {}
        self.grid = None
        self.ink_col = _c(ink)
        self.inkbuf = np.zeros((H * ss, W * ss), np.float32)
        self.emb = np.zeros((H * ss, W * ss), np.float32)
        self.pens = {}
        self.stages = []
        self.paper_rgb = None
        self.printed = set()
        self._jobpos = 0
        # ---- the machine: drum timing per character, hammers per column, ribbon, paper feed
        fs = self.ch * 0.86 * ss                                           # cap height ~ 0.105 in
        self.font = mono_font(fs, weight)
        self.base = int(round(4 + self.ch * ss * 0.74))                    # baseline inside a stamp
        self._stamps, self._protos = {}, {}
        self.drum = {}
        r = self.rng
        self.h_force = np.clip(r.normal(1.0, 0.045, cols), 0.86, 1.1)
        for c in r.choice(cols, 2, replace=False): self.h_force[c] = r.uniform(0.66, 0.76)   # weak hammers
        self.h_dx = r.normal(0, 0.22, cols)
        self.h_dy = r.normal(0, 0.18, cols)
        self.feed = r.normal(0, 0.3, self.rows + 4)
        self.skew = np.tan(np.radians(r.uniform(-0.06, 0.06)))
        self.low_rows = set(int(i) for i in np.nonzero(r.random(self.rows) < 0.06)[0])
        self.line_ink = np.clip(r.normal(1.0, 0.035, self.rows + 4), 0.88, 1.08)
        self.wear = 1 - 0.08 * (0.5 + 0.5 * np.sin(np.arange(cols) / cols * 2 * np.pi * 1.3 + r.uniform(0, 6)))
        self.fade = 0.28
        self._weave = self._make_weave()
        self._tooth = None

    def _seed(self):
        return int(self.rng.integers(1 << 30))

    # ================================================================ geometry
    def xy(self, col, row):
        """pixel position (1x) of a point given in cell coordinates (col, row); (c, r) is a cell's top-left"""
        return self.xl + col * self.cw, self.top + row * self.ch

    def centre(self, col, row):
        """pixel centre (1x) of cell (col, row)'s x-height area"""
        return self.xl + (col + 0.5) * self.cw, self.top + (row + 0.55) * self.ch

    # ================================================================ the form
    def form(self, white='#f6f4eb', green='#d2e7cc', desk='#3b3834', band=3, first_green=False, holes=True):
        """continuous greenbar form at ss x: bands every `band` lines from the page break, tractor strips,
        feed holes, micro-perforations, the cross perforation and the fanfold crease at `top`"""
        ss, W, H = self.ss, self.W * self.ss, self.H * self.ss
        y = (np.arange(H, dtype=np.float32) + 0.5) / ss
        x = (np.arange(W, dtype=np.float32) + 0.5) / ss
        strip = self.ppi * 0.5
        L0, L1 = self.px0 + strip, self.px1 - strip                        # the perforations
        p = (y - self.top) / self.ch / band                                # band coordinate
        k = np.floor(p)
        g = ((k.astype(int) % 2) == (0 if first_green else 1)).astype(np.float32)
        fr = p - k                                                          # band edges soft over ~1.5 px
        d_edge = np.minimum(fr, 1 - fr) * self.ch * band
        soft = smoothstep(-0.7, 0.7, d_edge)
        gband = g * soft + (1 - g) * (1 - soft)
        inside = ((x > L0 + 1.5) & (x < L1 - 1.5)).astype(np.float32)
        gmask = gband[:, None] * inside[None, :]
        # flexo green: a little mottled
        mott = noise2d(H // 4, W // 4, 18, 3, self._seed())
        mott = np.asarray(Image.fromarray(mott).resize((W, H), Image.BILINEAR), np.float32)
        wc, gc = _c(white), _c(green)
        dens = gmask * (0.9 + 0.14 * mott)
        del gmask, mott
        img = np.empty((H, W, 3), np.float32)                              # built channel by channel (memory)
        for k_ in range(3):
            img[..., k_] = wc[k_] + (gc[k_] - wc[k_]) * dens
        del dens
        # paper formation (cloudy) and tooth (fine)
        cloud = noise2d(H // 8, W // 8, 40, 4, self._seed())
        cloud = np.asarray(Image.fromarray(cloud).resize((W, H), Image.BILINEAR), np.float32)
        tooth = self.rng.random((H, W), dtype=np.float32)
        tooth = gauss(tooth, 0.7 * ss / 2)
        tooth = (tooth - tooth.mean()) / (tooth.std() + 1e-6)
        self._tooth = np.clip(0.5 + 0.18 * tooth, 0, 1)
        fac = 0.975 + 0.035 * cloud + 0.012 * tooth
        del cloud, tooth
        for k_ in range(3): img[..., k_] *= fac
        del fac
        # short fibres
        f = np.zeros((H, W), np.float32)
        for _ in range(int(W * H / 9000)):
            x0, y0 = self.rng.uniform(0, W), self.rng.uniform(0, H)
            a = self.rng.uniform(0, np.pi); L = self.rng.uniform(4, 16) * ss
            n = int(L)
            xs = (x0 + np.cos(a) * np.arange(n)).astype(int); ys = (y0 + np.sin(a) * np.arange(n) + np.sin(np.arange(n) / 5) * 1.5).astype(int)
            ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
            f[ys[ok], xs[ok]] = self.rng.uniform(0.3, 1)
        f = 1 - 0.05 * gauss(f, 0.6 * ss / 2)
        for k_ in range(3): img[..., k_] *= f
        del f
        # micro-perforations: tiny slits with a torn, lighter lip
        def perf_v(x0):
            xi = int(round(x0 * ss))
            per = 3.4 * ss
            on = ((np.arange(H) % per) < per * 0.62).astype(np.float32)
            on *= (self.rng.random(H) > 0.04)
            for dx, k_ in ((0, 0.16), (-1, 0.06), (1, 0.06)):
                img[:, xi + dx] *= (1 - k_ * on)[:, None]
            img[:, xi + ss + 1] = np.minimum(1, img[:, xi + ss + 1] * (1 + 0.03 * on)[:, None])

        def perf_h(y0):
            yi = int(round(y0 * ss))
            if not (2 <= yi < H - 3): return
            per = 3.4 * ss
            on = ((np.arange(W) % per) < per * 0.62).astype(np.float32)
            on *= (self.rng.random(W) > 0.04)
            for dy, k_ in ((0, 0.3), (-1, 0.12), (1, 0.1), (2, 0.04)):        # slits, torn lip
                img[yi + dy, :] *= (1 - k_ * on)[:, None]
            img[yi - 2, :] *= (1 + 0.04 * on)[:, None]
        if holes:
            perf_v(L0); perf_v(L1)
        # page breaks (cross perforation + fanfold crease: shade on one side, sheen on the other)
        page = self.page_rows * self.ch
        for yb in np.arange(self.top - page * 2, self.H + page, page):
            if -40 < yb < self.H + 40:
                perf_h(yb)
                dy = (y - yb)
                crease = -0.06 * np.exp(-np.maximum(-dy, 0) / 14) * (dy < 0) + 0.03 * np.exp(-np.maximum(dy, 0) / 9) * (dy >= 0)
                crease += -0.04 * np.exp(-(dy / 1.5) ** 2)
                img *= (1 + crease)[:, None, None]
        # feed holes
        if holes:
            dc = _c(desk)
            pitch = self.ppi * 0.5
            rad = self.ppi * 5 / 64
            ys0 = self.top + pitch / 2 - pitch * np.ceil((self.top + pitch) / pitch)
            centres = [(cx, cy) for cx in (self.px0 + strip / 2, self.px1 - strip / 2)
                       for cy in np.arange(ys0, self.H + pitch, pitch)]
            torn = set(self.rng.choice(len(centres), 2, replace=False).tolist())
            R = int((rad + 8) * ss)
            yy, xx = np.mgrid[-R:R + 1, -R:R + 1].astype(np.float32) / ss
            for i, (cx, cy) in enumerate(centres):
                ang = np.arctan2(yy, xx)
                wob = 1 + 0.025 * np.sin(ang * 7 + i) + 0.015 * np.sin(ang * 13 + 2 * i)
                ry = rad * (1.22 if i in torn else 1.0)
                dd = np.sqrt((xx / rad) ** 2 + (np.where(yy > 0, yy / ry, yy / rad)) ** 2) / wob
                hole = smoothstep(1.0 + 0.6 / rad, 1.0 - 0.6 / rad, dd)
                # desk seen through the hole: the hole's rim shadows the upper-left part of it
                lit = smoothstep(1.0 + 0.9 / rad, 1.0 - 1.4 / rad,
                                 np.sqrt(((xx - 2.6) / rad) ** 2 + ((yy - 3.2) / ry) ** 2))
                col = dc[None, None, :] * (0.55 + 0.6 * lit[..., None])
                rim = np.exp(-((dd - 1.0) * rad / 1.1) ** 2) * (dd > 1)
                x0, y0 = int(round(cx * ss)) - R, int(round(cy * ss)) - R
                xa, ya = max(x0, 0), max(y0, 0)
                xb, yb = min(x0 + 2 * R + 1, W), min(y0 + 2 * R + 1, H)
                if xa >= xb or ya >= yb: continue
                sl = (slice(ya, yb), slice(xa, xb))
                ls = (slice(ya - y0, yb - y0), slice(xa - x0, xb - x0))
                reg = img[sl]
                reg *= (1 - 0.07 * rim[ls])[..., None]
                img[sl] = reg * (1 - hole[ls][..., None]) + col[ls] * hole[ls][..., None]
        # the desk beside the form, with the paper's soft shadow (light from the upper left)
        if self.px0 > 0.5:
            pm = smoothstep(self.px0 - 0.6, self.px0 + 0.6, x) * (1 - smoothstep(self.px1 - 0.6, self.px1 + 0.6, x))
            dist = np.maximum(self.px0 - x, x - self.px1)
            sh = 1 - np.where(x > self.px1, 0.55 * np.exp(-np.maximum(dist, 0) / 9),
                              0.3 * np.exp(-np.maximum(dist, 0) / 4))
            grain = noise2d(H // 4, W // 4, 30, 3, self._seed())
            grain = np.asarray(Image.fromarray(grain).resize((W, H), Image.BILINEAR), np.float32)
            dc = _c(desk)
            for k_ in range(3):
                d_ = dc[k_] * (0.9 + 0.16 * grain) * sh[None, :]
                img[..., k_] = img[..., k_] * pm[None, :] + d_ * (1 - pm[None, :])
            del grain
            edge = np.exp(-((x - self.px0) / 0.8) ** 2) + np.exp(-((x - self.px1) / 0.8) ** 2)
            img *= (1 - 0.12 * edge)[None, :, None]
        np.clip(img, 0, 1, out=img)
        self.paper_rgb = img
        return self

    # ================================================================ roles and masks
    def role(self, name, ramp, edge='outer', outline='straight', dither=0.5, noise=0.02, group=None, inner_max=1.0):
        """a glyph vocabulary. ramp: light -> dark list of strings ('' blank, '#@' = '#' overstruck with '@').
        edge: 'outer' outline against other roles, 'all' also between pieces of the same role, None no outline.
        outline: 'straight' (| for upright sides), 'round' (( and ) for upright sides, for puffs and bellies) or a
        dict overriding any of v h low dot tick up down x plus left right top.
        group: roles in the same group (a body and the paint on it) are not outlined against each other.
        inner_max: with edge='all', outlines between pieces only where the upper piece is lighter than this tone
        (lit tops of puffs get a rim; inside the shadows the tone alone carries the form)"""
        if name not in self.roles:
            self.roles[name] = dict(id=len(self._role_by_id)); self._role_by_id.append(name)
        self.roles[name].update(ramp=list(ramp), edge=edge, outline=_style(outline), dither=dither, noise=noise,
                                group=group or name, inner_max=inner_max)
        return name

    def line_set(self, glyphs):
        """register how a stroke becomes characters: a style name / dict, or one character that is forced"""
        st = glyphs if (isinstance(glyphs, str) and len(glyphs) == 1) else _style(glyphs)
        if st in self.line_sets: return self.line_sets.index(st)
        self.line_sets.append(st); return len(self.line_sets) - 1

    def _aa(self, d):
        """signed distance in sub-pixels (positive inside) -> coverage"""
        return np.clip(d + 0.5, 0, 1)

    def ellipse(self, c, r, rx, ry, rot=0.0):
        """mask of an ellipse; c, r centre in cells, rx in columns, ry in rows, rot radians"""
        u, v = self.X - c, self.Y - r
        if rot:
            # rotate in physical space (columns are narrower than rows)
            k = self.ch / self.cw
            uu, vv = u, v * k
            cs, sn = np.cos(rot), np.sin(rot)
            u, v = (uu * cs + vv * sn), (-uu * sn + vv * cs) / k
        d = np.sqrt((u / rx) ** 2 + (v / ry) ** 2)
        return self._aa((1 - d) * min(rx * self.sx, ry * self.sy))

    def circle(self, c, r, radius):
        """round in the printed picture: radius in columns, the row radius is corrected for the cell shape"""
        return self.ellipse(c, r, radius, radius * self.cw / self.ch)

    def poly(self, pts):
        P = [(float(c) * self.sx, float(r) * self.sy) for c, r in pts]
        return polygon_mask(self.rows * self.sy, self.cols * self.sx, P, ss=3)

    def shape(self, pts, per=10):
        """smooth closed outline through control points (cells)"""
        P = np.asarray(pts, np.float32)
        P = np.vstack([P, P[:3]])
        S = spline(P, per)[per:-per * 1]
        return self.poly(S)

    def rect(self, c0, r0, c1, r1):
        return self.poly([(c0, r0), (c1, r0), (c1, r1), (c0, r1)])

    def blob(self, c, r, rx, ry, rough=0.1, seed=None):
        pts = blob_pts(c, r, rx, ry, rough, 120, self._seed() if seed is None else seed)
        return self.poly(pts)

    # ================================================================ tones (light on things)
    def sphere_tone(self, c, r, radius, light=(-0.55, -0.7, 0.45), amb=0.12, soft=0.0):
        """ink wanted on a sphere seen in the picture (0 lit .. 1 dark), radius in columns"""
        L = np.asarray(light, np.float32); L /= np.linalg.norm(L)
        u = (self.X - c) / radius
        v = (self.Y - r) * (self.ch / self.cw) / radius
        q = np.clip(1 - u * u - v * v, 0, 1)
        n = np.stack([u, v, np.sqrt(q)])
        dif = np.clip((n * L[:, None, None]).sum(0), 0, 1)
        if soft: dif = dif * (1 - soft) + soft * (0.5 + 0.5 * (n * L[:, None, None]).sum(0))
        return np.clip(1 - (amb + (1 - amb) * dif), 0, 1)

    def cylinder_tone(self, c0, c1, light=(-0.8, 0.0, 0.6), amb=0.1, spec=0.0):
        """ink wanted across a vertical cylinder between columns c0 and c1"""
        L = np.asarray(light, np.float32); L /= np.linalg.norm(L)
        u = np.clip((self.X - (c0 + c1) / 2) / ((c1 - c0) / 2), -1, 1)
        nz = np.sqrt(np.clip(1 - u * u, 0, 1))
        dif = np.clip(u * L[0] + nz * L[2], 0, 1)
        t = 1 - (amb + (1 - amb) * dif)
        if spec: t -= spec * np.clip(u * L[0] + nz * L[2], 0, 1) ** 24
        return np.clip(t, 0, 1)

    def ramp_tone(self, p0, p1, t0, t1):
        """linear tone from cell point p0 (tone t0) to p1 (tone t1)"""
        d = np.array(p1, np.float32) - np.array(p0, np.float32)
        s = ((self.X - p0[0]) * d[0] + (self.Y - p0[1]) * d[1]) / (d @ d + 1e-6)
        return t0 + (t1 - t0) * np.clip(s, 0, 1)

    # ================================================================ painting the role map
    def fill(self, mask, role, tone=0.5):
        """paint a region into the role map (covers whatever was there, strokes included)"""
        m = mask > 0.5
        if not m.any(): return m
        self._n += 1
        rid = self.roles[role]['id']
        self.inst[m] = self._n
        self.rmap[m] = rid
        self.tone[m] = tone[m] if isinstance(tone, np.ndarray) else tone
        self.line[m] = 0
        return m

    def erase(self, mask):
        """back to bare paper (knock-outs)"""
        m = mask > 0.5
        self._n += 1
        self.inst[m] = self._n; self.rmap[m] = 0; self.tone[m] = 0; self.line[m] = 0
        return m

    def stroke(self, pts, width=1.15, glyphs=None, smooth=False, closed=False):
        """a drawn line in cell coordinates; its cells get characters by direction and position
        (glyphs: None / 'straight' / 'round' / dict, or one character to force, e.g. '=' for a platform)"""
        P = np.asarray(pts, np.float32)
        if closed: P = np.vstack([P, P[:1]])
        if smooth and len(P) > 2: P = spline(P, 12)
        sid = self.line_set(glyphs)
        Pp = P * np.array([self.sx, self.sy], np.float32)
        hw = width / 2
        SY, SX = self.line.shape
        for a, b in zip(Pp[:-1], Pp[1:]):
            x0, x1 = int(max(min(a[0], b[0]) - width - 2, 0)), int(min(max(a[0], b[0]) + width + 3, SX))
            y0, y1 = int(max(min(a[1], b[1]) - width - 2, 0)), int(min(max(a[1], b[1]) + width + 3, SY))
            if x0 >= x1 or y0 >= y1: continue
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32) + 0.5
            d = b - a; L2 = float(d @ d) + 1e-6
            t = np.clip(((xx - a[0]) * d[0] + (yy - a[1]) * d[1]) / L2, 0, 1)
            dist = np.hypot(xx - a[0] - t * d[0], yy - a[1] - t * d[1])
            cov = np.clip(hw + 0.5 - dist, 0, 1)
            sl = self.line[y0:y1, x0:x1]
            np.maximum(sl, cov, out=sl)
            self.lset[y0:y1, x0:x1][cov > 0.3] = sid
        self.grid = None

    def text(self, s, col, row, strike=1, opaque=False):
        """literal characters from (col, row); strike=2 prints each twice (bold by overstrike);
        opaque=True makes spaces blank out the picture under them"""
        for i, ch in enumerate(s):
            if ch == ' ' and not opaque: continue
            cc = col + i
            if 0 <= cc < self.cols and 0 <= row < self.rows:
                self.fixed[(row, cc)] = '' if ch == ' ' else ch * strike
        self.grid = None

    def text_v(self, s, col, row, strike=1):
        """literal characters downwards from (col, row), one per line (lettering painted on an upright body)"""
        for i, ch in enumerate(s):
            if ch != ' ' and 0 <= row + i < self.rows and 0 <= col < self.cols:
                self.fixed[(row + i, col)] = ch * strike
        self.grid = None

    def plot(self, col, row, w, h, xlim, ylim, series, xticks, yticks, ylab_w=5, xfmt='{:g}', yfmt='{:g}'):
        """a printer plot: y axis of 'I' with '+' ticks and labels, x axis of '-' with '+' ticks, points as glyphs.
        series: [(xs, ys, glyph), ...] later series overwrite earlier ones. Returns cell(x, y) -> (col, row)"""
        ax = col + ylab_w + 1                     # axis column
        x0 = ax + 1
        def cell(xv, yv):
            cc = x0 + (xv - xlim[0]) / (xlim[1] - xlim[0]) * (w - 1)
            rr = row + (ylim[1] - yv) / (ylim[1] - ylim[0]) * (h - 1)
            return cc, rr
        for r in range(row, row + h): self.text('I', ax, r)
        for yv in yticks:
            _, rr = cell(xlim[0], yv); rr = int(round(rr))
            self.text('+', ax, rr)
            lab = yfmt.format(yv)
            self.text(lab.rjust(ylab_w), col, rr)
        xr = row + h
        self.text('+' + '-' * w, ax, xr)
        for xv in xticks:
            cc, _ = cell(xv, ylim[0]); cc = int(round(cc))
            self.text('+', cc, xr)
            lab = xfmt.format(xv)
            self.text(lab, cc - len(lab) // 2, xr + 1)
        for xs, ys, g in series:
            for xv, yv in zip(xs, ys):
                cc, rr = cell(xv, yv)
                cc, rr = int(round(cc)), int(round(rr))
                if x0 <= cc < x0 + w and row <= rr < row + h:
                    self.fixed[(rr, cc)] = g
        self.grid = None
        return cell

    def billow(self, puffs, role, light=(-0.55, -0.75, 0.4), amb=0.12, shadow=0.35, glow=None, lift=None):
        """a cloud of round puffs [(col, row, radius), ...] painted back to front. Each puff is lit as a sphere,
        casts a soft contact shadow on the puffs behind it, and `glow=(col, row, radius_cols, strength)` lights the
        cloud from inside (a flame); `lift` is an optional extra tone field added everywhere. Returns the mask."""
        union = np.zeros(self.line.shape, np.float32)
        first = self._n + 1
        L = np.asarray(light, np.float32); L /= np.linalg.norm(L)
        sh = np.zeros_like(union)
        for (c, r, R) in puffs:
            m = self.circle(c, r, R)
            t = self.sphere_tone(c, r, R, light, amb)
            mm = self.fill(m, role, t)
            # this puff shades what is behind it on the side away from the light
            ring = np.clip(self.circle(c - L[0] * R * 0.35, r - L[1] * R * 0.35 * self.cw / self.ch, R * 1.08) - m, 0, 1)
            sh = np.maximum(sh * (1 - m), ring)
            union = np.maximum(union, m)
        own = (self.inst >= first) & (union > 0.5)
        sh = blur(sh, 2.0)
        tone = self.tone.copy()
        tone[own] = np.clip(tone[own] + shadow * sh[own], 0, 1)
        if glow is not None:
            gc, gr, gR, gs = glow
            d2 = ((self.X - gc) / gR) ** 2 + ((self.Y - gr) * self.ch / self.cw / gR) ** 2
            tone[own] = np.clip(tone[own] - gs * np.exp(-d2[own] * 1.5), 0, 1)
        if lift is not None:
            tone[own] = np.clip(tone[own] + lift[own], 0, 1)
        self.tone = tone
        return union

    # ================================================================ choosing the glyphs
    def _stamp(self, ch):
        """the type slug for one character at ss x: (mask float32 Hs x Ws), pad 4 px"""
        if ch in self._stamps: return self._stamps[ch]
        ss = self.ss
        Ws, Hs = int(np.ceil(self.cw * ss)) + 8, int(np.ceil(self.ch * ss)) + 8
        im = Image.new('L', (Ws, Hs), 0)
        ImageDraw.Draw(im).text((Ws / 2, self.base), ch, font=self.font, fill=255, anchor='ms')
        m = np.asarray(im, np.float32) / 255
        if self.rng.random() < 0.3 and m.sum() > 20:               # a worn slug: the same nick every time
            ys, xs = np.nonzero(m > 0.6)
            i = self.rng.integers(len(ys))
            yy, xx = np.mgrid[0:Hs, 0:Ws]
            rr = self.rng.uniform(1.2, 2.2) * ss / 2
            m = m * (1 - 0.8 * np.exp(-((yy - ys[i]) ** 2 + (xx - xs[i]) ** 2) / (2 * rr * rr)))
        self._stamps[ch] = m
        self.drum[ch] = self.rng.normal(0, 0.42)
        return m

    def _proto(self, ch):
        """the character's shape on the role-map grid (sy x sx), blurred, unit length"""
        if ch in self._protos: return self._protos[ch]
        m = self._stamp(ch)
        ss = self.ss
        crop = m[4:4 + int(round(self.ch * ss)), 4:4 + int(round(self.cw * ss))]
        p = np.asarray(Image.fromarray(crop).resize((self.sx, self.sy), Image.BOX), np.float32)
        p = gauss(p, 0.7)
        self._protos[ch] = p
        return p

    def _pick(self, P, st, inside=None):
        """the character for a line pattern P (sy x sx): by its direction (measured in real pixels, cells are
        tall) and where it sits in the cell. Returns (glyph, family) with family in h / diag / v / x"""
        sy, sx = P.shape
        w = P.ravel().astype(np.float64); W = w.sum() + 1e-9
        X = np.tile((np.arange(sx) + 0.5) / sx * self.cw, sy)
        Y = np.repeat((np.arange(sy) + 0.5) / sy * self.ch, sx)
        mx, my = (w * X).sum() / W, (w * Y).sum() / W
        dx, dy = X - mx, Y - my
        Sxx, Syy, Sxy = (w * dx * dx).sum() / W, (w * dy * dy).sum() / W, (w * dx * dy).sum() / W
        th = 0.5 * np.arctan2(2 * Sxy, Sxx - Syy)
        coh = 2 * np.sqrt(((Sxx - Syy) / 2) ** 2 + Sxy ** 2) / (Sxx + Syy + 1e-9)
        a = np.degrees(abs(th))
        cy = my / self.ch
        Xn, Yn = X / self.cw, Y / self.ch                                  # crossing test in cell units
        mxn, myn = (w * Xn).sum() / W, (w * Yn).sum() / W
        a_, b_, c_ = (w * (Xn - mxn) ** 2).sum() / W, (w * (Yn - myn) ** 2).sum() / W, (w * (Xn - mxn) * (Yn - myn)).sum() / W
        cohn = 2 * np.sqrt(((a_ - b_) / 2) ** 2 + c_ ** 2) / (a_ + b_ + 1e-9)
        if min(coh, cohn) < 0.3 and W > 1.45 * sy:                          # two strokes crossing
            pr = {g: self._proto(g).ravel() for g in '/\\|-'}
            pn = w / (np.linalg.norm(w) + 1e-9)
            k = {g: float(pn @ (v / (np.linalg.norm(v) + 1e-9))) for g, v in pr.items()}
            return (st['x'] if k['/'] + k['\\'] > k['|'] + k['-'] else st['plus']), 'x'
        if a < 14:
            return (st['h'] if cy < 0.62 else st['low']), 'h'
        if a < 40:
            return (st['tick'] if cy < 0.33 else st['h'] if cy < 0.6 else st['dot'] if cy < 0.8 else st['low']), 'h'
        if a < 72:
            return (st['up'] if th < 0 else st['down']), 'diag'
        if inside is not None and abs(inside[0]) > 0.05:
            return (st['left'] if inside[0] > 0 else st['right']), 'v'
        return st['v'], 'v'

    @staticmethod
    def _thin(fam, grid, kind):
        """non-maximum suppression: an upright or slanted outline keeps one cell per row, a flat one one per column"""
        drop = []
        for (r, c), (f, iid, e) in fam.items():
            if f in ('v', 'diag'): nb = [(r, c - 1), (r, c + 1)]
            elif f == 'h': nb = [(r - 1, c), (r + 1, c)]
            else: continue
            for q in nb:
                o = fam.get(q)
                if (o and o[0] == f and o[1] == iid and (f != 'diag' or grid[q[0]][q[1]] == grid[r][c])
                        and (o[2] > e or (o[2] == e and q < (r, c)))):
                    drop.append((r, c)); break
        for (r, c) in drop:
            grid[r][c] = ''; kind[r, c] = 0

    def compose(self):
        """decide every cell's characters from the role map; returns the grid (list of rows of strings)"""
        R, C, sy, sx = self.rows, self.cols, self.sy, self.sx
        blk = lambda a: a.reshape(R, sy, C, sx).transpose(0, 2, 1, 3)
        rm = blk(self.rmap)
        nroles = len(self._role_by_id)
        cnt = np.stack([(rm == k).sum((2, 3)) for k in range(nroles)])
        dom = cnt.argmax(0)
        tone_b = blk(self.tone)
        own = (rm == dom[..., None, None])
        ctone = (tone_b * own).sum((2, 3)) / np.maximum(own.sum((2, 3)), 1)
        # strokes
        Lb = blk(self.line)
        lenergy = Lb.sum((2, 3)) / sy
        lsb = blk(self.lset)
        # silhouette edges: boundary sub-pixels on the side of the upper (later) region
        inst, rmap = self.inst, self.rmap
        ids_out = [self.roles[n]['id'] for n in self._role_by_id if self.roles[n]['edge'] in ('outer', 'all')]
        ids_all = [self.roles[n]['id'] for n in self._role_by_id if self.roles[n]['edge'] == 'all']
        mine = np.isin(rmap, ids_out); all_ = np.isin(rmap, ids_all)
        gnames = sorted(set(self.roles[n]['group'] for n in self._role_by_id))
        gid = np.array([gnames.index(self.roles[n]['group']) for n in self._role_by_id], np.int16)
        gmap = gid[rmap]
        imax = np.array([self.roles[n]['inner_max'] for n in self._role_by_id], np.float32)[rmap]
        lit_enough = self.tone < imax
        B = np.zeros(inst.shape, np.float32)
        Bown = np.zeros(inst.shape, np.int16)
        Binst = np.zeros(inst.shape, np.int32)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            o_inst = shift(inst, dx, dy); o_role = shift(rmap, dx, dy); o_g = shift(gmap, dx, dy)
            valid = np.ones(inst.shape, bool)
            if dx == 1: valid[:, 0] = False
            if dx == -1: valid[:, -1] = False
            if dy == 1: valid[0, :] = False
            if dy == -1: valid[-1, :] = False
            diff_role = rmap != o_role
            diff_g = gmap != o_g
            e = (inst > o_inst) & valid & (rmap != 0) & ((mine & diff_g) | (all_ & ~diff_role & lit_enough))
            B[e] = 1; Bown[e] = rmap[e]; Binst[e] = inst[e]
        Bb = blk(B)
        benergy = Bb.sum((2, 3)) / sy
        Bo, Bi, Ib = blk(Bown), blk(Binst), blk(inst)
        grid = [[''] * C for _ in range(R)]
        kind = np.zeros((R, C), np.int8)              # 0 open, 1 fixed, 2 line, 3 edge, 4 fill
        for (r, c) in self.fixed: kind[r, c] = 1
        # ---- line cells; a slanted or upright line that smears over two neighbouring cells keeps the stronger one
        fam = {}
        for (r, c) in np.argwhere((lenergy > 0.5) & (kind == 0)):
            ids, ns = np.unique(lsb[r, c][Lb[r, c] > 0.3], return_counts=True)
            st = self.line_sets[int(ids[ns.argmax()]) if len(ids) else 0]
            if isinstance(st, str):
                grid[r][c] = st; fam[(r, c)] = ('forced', 0, lenergy[r, c])
            else:
                g, f = self._pick(Lb[r, c], st)
                grid[r][c] = g; fam[(r, c)] = (f, 0, lenergy[r, c])
            kind[r, c] = 2
        self._thin(fam, grid, kind)
        # ---- edge cells, top to bottom; a region's flat top edge high in its cell moves up as '_'
        fam = {}
        for (r, c) in np.argwhere((benergy > 0.32) & (kind == 0)):
            if kind[r, c]: continue
            ids, ns = np.unique(Bo[r, c][Bb[r, c] > 0], return_counts=True)
            rid = int(ids[ns.argmax()])
            iid = np.bincount(Bi[r, c][Bb[r, c] > 0].ravel()).argmax()
            P = Bb[r, c] * (Bi[r, c] == iid)
            if P.sum() < 0.3 * sy: continue
            st = self.roles[self._role_by_id[rid]]['outline']
            yy, xx = np.mgrid[0:sy, 0:sx]
            # which side the region lies on: its pixels in this cell and the two beside it
            c0, c1 = max(c - 1, 0), min(c + 2, C)
            inn = (inst[r * sy:(r + 1) * sy, c0 * sx:c1 * sx] == iid)
            xw = np.mgrid[0:sy, 0:(c1 - c0) * sx][1] - (c - c0) * sx
            inside = None
            if inn.sum() > P.sum():
                inside = (((xw * inn).sum() / inn.sum() - (xx * P).sum() / P.sum()) / sx,
                          ((np.mgrid[0:sy, 0:(c1 - c0) * sx][0] * inn).sum() / inn.sum() - (yy * P).sum() / P.sum()) / sy)
            g, f = self._pick(P, st, inside)
            cy = (yy * P).sum() / P.sum() / sy
            flat = f == 'h' and g in (st['h'], st['low'])
            if flat and st['top'] and inside is not None and inside[1] > 0 and cy < 0.42:
                if r > 0 and kind[r - 1, c] == 0 and dom[r - 1, c] != rid:
                    grid[r - 1][c] = st['top']; kind[r - 1, c] = 3
                continue                                                    # this cell is filled normally
            if flat and inside is not None and inside[1] < 0:
                g = st['low'] if cy > 0.45 else st['h']
            grid[r][c] = g; kind[r, c] = 3; fam[(r, c)] = (f, iid, P.sum())
        self._thin(fam, grid, kind)
        # ---- fill cells: ramp with error diffusion inside each role
        err = np.zeros((R, C + 2), np.float32)
        noise = self.rng.normal(0, 1, (R, C)).astype(np.float32)
        for r in range(R):
            for c in range(C):
                if kind[r, c]: continue
                rid = int(dom[r, c])
                if rid == 0 or cnt[rid, r, c] < sy * sx * 0.45: continue
                ro = self.roles[self._role_by_id[rid]]
                ramp = ro['ramp']; n = len(ramp) - 1
                v = ctone[r, c] * n + ro['noise'] * n * noise[r, c] + err[r, c + 1] * ro['dither']
                q = int(np.clip(np.round(v), 0, n))
                e = (v - q) if 0 < v < n else 0.0
                e = float(np.clip(e, -0.6, 0.6))
                if c + 1 < C and dom[r, c + 1] == rid: err[r, c + 2] += e * 7 / 16
                if r + 1 < R:
                    if c > 0 and dom[r + 1, c - 1] == rid: err[r + 1, c] += e * 3 / 16
                    if dom[r + 1, c] == rid: err[r + 1, c + 1] += e * 5 / 16
                    if c + 1 < C and dom[r + 1, c + 1] == rid: err[r + 1, c + 2] += e * 1 / 16
                grid[r][c] = ramp[q]; kind[r, c] = 4
        for (r, c), s_ in self.fixed.items():
            if 0 <= r < R and 0 <= c < C: grid[r][c] = s_
        self.grid = grid
        self.kind = kind
        return grid

    def listing(self, path=None):
        """the page as plain text (first strike of every cell), for a terminal or a .txt"""
        if self.grid is None: self.compose()
        lines = [''.join((s[:1] or ' ') for s in row).rstrip() for row in self.grid]
        txt = '\n'.join(lines) + '\n'
        if path: open(path, 'w').write(txt)
        return txt

    # ================================================================ the printer
    def _make_weave(self):
        """ribbon: a fabric weave whose threads carry uneven ink, plus clumps; a 256 px tile at ss, sampled at a
        random offset for every impression (the ribbon has moved on between strikes)"""
        n = 256
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        p = 2.2 * self.ss                                                   # ~2.2 px thread pitch at 1x
        wv = 0.5 + 0.22 * np.sin(2 * np.pi * (xx + yy) / p) * np.sin(2 * np.pi * (xx - yy) / (p * 1.09))
        clump = self.rng.random((n, n)).astype(np.float32)
        clump = gauss(clump, 0.9 * self.ss / 2)
        clump = (clump - clump.mean()) / (clump.std() + 1e-6)
        wv += 0.16 * clump
        return np.clip(wv, 0, 1).astype(np.float32)

    def _soft(self, ch):
        """the slug's ink footprint: the glyph pushed a little into the paper (spread)"""
        key = ('soft', ch)
        if key not in self._stamps:
            self._stamps[key] = gauss(self._stamp(ch), 0.95 * self.ss / 2)
        return self._stamps[key]

    def _strike(self, ch, r, c, p, dxp, dyp, ribbon):
        m = self._soft(ch)
        ss = self.ss
        Hs, Ws = m.shape
        x = self.xl + c * self.cw + self.h_dx[c] + dxp + self.rng.normal(0, 0.12)
        y = (self.top + r * self.ch + self.feed[r] + self.drum[ch] + self.h_dy[c] + dyp + self.rng.normal(0, 0.15)
             + (c - self.cols / 2) * self.cw * self.skew)
        X0, Y0 = int(round(x * ss)) - 4, int(round(y * ss)) - 4
        xa, ya = max(X0, 0), max(Y0, 0)
        xb, yb = min(X0 + Ws, self.W * ss), min(Y0 + Hs, self.H * ss)
        if xa >= xb or ya >= yb: return
        mm = m[ya - Y0:yb - Y0, xa - X0:xb - X0]
        e = float(np.clip(self.h_force[c] * self.rng.normal(1, 0.06) * ribbon, 0.25, 1.2))
        if r in self.low_rows:                                           # ribbon rode low: tops starve
            e_v = e * (0.55 + 0.45 * smoothstep(0.25, 0.62, (np.arange(Hs) / Hs)))[ya - Y0:yb - Y0, None]
        else:
            e_v = e
        oy, ox = self.rng.integers(0, 256 - Hs), self.rng.integers(0, 256 - Ws)
        wv = self._weave[oy:oy + (yb - ya), ox:ox + (xb - xa)]
        tooth = self._tooth[ya:yb, xa:xb] if self._tooth is not None else 0.5
        tex = 0.55 * wv + 0.45 * tooth - 0.5                                # about -0.2 .. 0.2
        # ink reaches the paper where the slug presses hard enough through the ribbon: strong strikes fill the
        # whole footprint, weak ones break up on the weave and the paper tooth instead of turning grey
        v = mm * (1.05 + 0.25 * e_v) + 1.1 * tex - 0.32 * (1 - e_v)
        cov = smoothstep(0.42, 0.66, v)
        dens = cov * (0.58 + 0.36 * np.minimum(e_v, 1.05)) * (0.9 + 0.9 * tex)
        sl = self.inkbuf[ya:yb, xa:xb]
        sl[...] = 1 - (1 - sl) * (1 - np.clip(dens, 0, 0.97))
        self.emb[ya:yb, xa:xb] += mm * e

    def print_rows(self, r0=0, r1=None):
        """impact-print rows r0..r1-1 (all overstrike passes of each line before the paper advances)"""
        if self.grid is None: self.compose()
        r1 = self.rows if r1 is None else r1
        for r in range(r0, min(r1, self.rows)):
            if r in self.printed: continue
            row = self.grid[r]
            npass = max((len(s) for s in row), default=0)
            self._jobpos += 1
            job = self._jobpos / max(self.rows, 1)
            for p in range(npass):
                dxp = 0.0 if p == 0 else self.rng.normal(0, 0.3)
                dyp = 0.0 if p == 0 else self.rng.normal(0, 0.42)
                for c, s in enumerate(row):
                    if len(s) > p and s[p] != ' ':
                        ribbon = (1 - self.fade * job) * self.wear[c] * self.line_ink[r]
                        self._strike(s[p], r, c, p, dxp, dyp, ribbon)
            self.printed.add(r)

    # ================================================================ ballpoint
    def _pen_layer(self, colour):
        key = tuple(np.round(_c(colour), 4))
        if key not in self.pens:
            self.pens[key] = np.zeros((self.H * self.ss, self.W * self.ss), np.float32)
        return self.pens[key]

    def pen(self, pts, colour='#b8322a', width=1.5, smooth=True, density=0.85, skip=0.1):
        """a ballpoint line through pixel points (1x): starts and ends blot a little, fast parts run pale,
        the ball skips on the paper tooth"""
        P = np.asarray(pts, np.float32)
        if smooth and len(P) > 2: P = spline(P, 10)
        seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
        Ltot = float(seg.sum())
        if Ltot < 1: return
        s = np.concatenate([[0], np.cumsum(seg)])
        n = max(8, int(Ltot / 1.2))
        ss_ = np.linspace(0, Ltot, n)
        px, py = np.interp(ss_, s, P[:, 0]), np.interp(ss_, s, P[:, 1])
        t = ss_ / Ltot
        S = 2 * self.ss                                                   # draw at 2 x the layer, then reduce
        x0, y0 = int(px.min() - 6), int(py.min() - 6)
        x1, y1 = int(px.max() + 7), int(py.max() + 7)
        w, h = (x1 - x0) * S, (y1 - y0) * S
        im = Image.new('L', (w, h), 0)
        d = ImageDraw.Draw(im)
        wob = fbm1d(n, 30, 3, self._seed())
        inten = density * (0.78 + 0.22 * wob) * (1 + 0.25 * np.exp(-t / 0.03) + 0.2 * np.exp(-(1 - t) / 0.03))
        gate = fbm1d(n, 12, 3, self._seed())
        inten = inten * np.where(gate < np.quantile(gate, skip), 0.3, 1.0)
        for i in range(n - 1):
            ww = max(1, int(round(width * S * (0.85 + 0.15 * wob[i]))))
            d.line([((px[i] - x0) * S, (py[i] - y0) * S), ((px[i + 1] - x0) * S, (py[i + 1] - y0) * S)],
                   fill=int(np.clip(inten[i], 0, 1) * 255), width=ww, joint='curve')
        a = np.asarray(im.resize(((x1 - x0) * self.ss, (y1 - y0) * self.ss), Image.BOX), np.float32) / 255
        self._pen_add(a, x0, y0, colour)

    def _pen_add(self, a, x0, y0, colour):
        lay = self._pen_layer(colour)
        X0, Y0 = x0 * self.ss, y0 * self.ss
        Hh, Ww = a.shape
        xa, ya = max(X0, 0), max(Y0, 0)
        xb, yb = min(X0 + Ww, lay.shape[1]), min(Y0 + Hh, lay.shape[0])
        if xa >= xb or ya >= yb: return
        aa = a[ya - Y0:yb - Y0, xa - X0:xb - X0]
        if self._tooth is not None:
            aa = aa * (0.8 + 0.4 * self._tooth[ya:yb, xa:xb])
        sl = lay[ya:yb, xa:xb]
        np.maximum(sl, np.clip(aa, 0, 1), out=sl)

    def ring(self, cx, cy, rx, ry, colour='#b8322a', turns=1.12, width=1.5, tilt=-0.15):
        """the quick loop drawn around something worth noticing: an ellipse that overshoots its start"""
        n = 60
        a0 = self.rng.uniform(-2.6, -2.0)
        t = np.linspace(a0, a0 + 2 * np.pi * turns, n)
        grow = 1 + 0.1 * (t - a0) / (2 * np.pi)
        wob = 1 + 0.04 * fbm1d(n, 20, 3, self._seed())
        x, y = np.cos(t) * rx * grow * wob, np.sin(t) * ry * grow * wob
        cs, sn = np.cos(tilt), np.sin(tilt)
        self.pen(np.stack([cx + x * cs - y * sn, cy + x * sn + y * cs], 1), colour, width)

    def tick(self, x, y, size=14, colour='#b8322a', width=1.5):
        """a check mark whose foot is at (x, y)"""
        j = self.rng.normal(0, 0.06, 4) * size
        pts = [(x - size * 0.45 + j[0], y - size * 0.45), (x - size * 0.12, y - size * 0.1 + j[1]),
               (x + j[2] * 0.3, y), (x + size * 0.32, y - size * 0.6 + j[3]), (x + size * 0.62, y - size * 1.05)]
        self.pen(pts, colour, width, smooth=True)

    def pen_text(self, s, x, y, size=26, colour='#b8322a', rot=4.0, style='hand', anchor='ls'):
        """handwriting with the same ballpoint"""
        f = load_font(style, size * self.ss)
        ox, oy = int(size * 0.6), int(size * 1.5)                         # local origin (1x) of the baseline
        w, h = int(f.getlength(s) / self.ss + size * 1.4), int(size * 2.3)
        im = Image.new('L', (w * self.ss, h * self.ss), 0)
        ImageDraw.Draw(im).text((ox * self.ss, oy * self.ss), s, font=f, fill=230, anchor=anchor)
        im = im.rotate(rot, resample=Image.BICUBIC, center=(ox * self.ss, oy * self.ss))
        a = np.asarray(im, np.float32) / 255
        self._pen_add(a, int(round(x)) - ox, int(round(y)) - oy, colour)

    # ================================================================ output
    def composite(self, emboss=0.05, wick=0.3, band=480):
        """ink (multiplied into the paper like a dye), wicking halo, hammer emboss, ballpoint; in horizontal bands
        to keep memory low; returns a 1x PIL image"""
        if self.paper_rgb is None: self.form()
        H2 = self.H * self.ss
        out8 = np.empty((H2, self.W * self.ss, 3), np.uint8)
        pad = 12
        ink_k = (1 - self.ink_col)[None, None, :]
        for y0 in range(0, H2, band):
            y1 = min(y0 + band, H2)
            a0, a1 = max(y0 - pad, 0), min(y1 + pad, H2)
            A = self.inkbuf[a0:a1]
            Aw = 1 - (1 - A) * (1 - wick * gauss(A, 1.1 * self.ss / 2))
            out = self.paper_rgb[a0:a1] * (1 - Aw[..., None] * ink_k)
            if emboss:
                h = gauss(self.emb[a0:a1], 1.0 * self.ss / 2)
                gy, gx = np.gradient(h)
                out *= np.clip(1 + emboss * (gx * 0.6 + gy * 0.8), 0.9, 1.06)[..., None]
            for key, a in self.pens.items():
                col = np.array(key, np.float32)
                out *= (1 - np.clip(a[a0:a1], 0, 1)[..., None] * (1 - col)[None, None, :])
            out8[y0:y1] = (np.clip(out[y0 - a0:y0 - a0 + (y1 - y0)], 0, 1) * 255 + 0.5).astype(np.uint8)
        im = Image.fromarray(out8)
        if self.ss > 1: im = im.resize((self.W, self.H), Image.LANCZOS)
        return im

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
