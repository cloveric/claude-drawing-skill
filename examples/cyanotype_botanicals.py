"""Example (cyanotype): Sun Print Botanicals / 蓝晒植物 — a photogram in the spirit of Anna Atkins:
a fern frond, a sprig of ginkgo leaves and a dandelion clock laid on brushed Prussian-blue emulsion.
Thin leaves let a little light through (pale body, whiter veins), dandelion fluff stands off the paper
(soft penumbra), white handwriting printed in, a pencil note on the margin. No image model.
python3 cyanotype_botanicals.py [out.png] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
import numpy as np
from cyanotype import Cyanotype
from core import spline, fbm1d

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'cyanotype_botanicals.png'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

cy = Cyanotype(1920, 1080, seed=1842)
rng = cy.rng
W, H = cy.W, cy.H
cy.coat(96, 64, 1826, 1000)
cy.stage('coated')


def along(P, s):
    """point and unit tangent at arc-length fraction s of polyline P"""
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
    d = s * cum[-1]; i = min(len(seg) - 1, int(np.searchsorted(cum, d) - 1)); i = max(i, 0)
    t = (d - cum[i]) / (seg[i] + 1e-6)
    p = P[i] + (P[i + 1] - P[i]) * t
    u = (P[i + 1] - P[i]) / (seg[i] + 1e-6)
    return p, u


# ---- fern frond: rachis, alternating pinnae, each pinna a midrib with blunt pinnules
def fern(base, ctrl, tip, lmax, n_pairs, seed):
    """a pinnate frond: alternating pinnae, each one continuous blade with a scalloped (lobed) margin"""
    r = np.random.default_rng(seed)
    rachis = spline([base, ctrl, tip], 30)
    blades, ribs = [], []
    for k in range(n_pairs * 2):
        s = 0.07 + 0.9 * (k / (n_pairs * 2)) ** 0.92
        side = 1 if k % 2 == 0 else -1
        p, u = along(rachis, s)
        nrm = np.array([-u[1], u[0]]) * side
        L = lmax * np.sin(np.pi * (0.14 + 0.86 * s)) ** 0.7 * (1.1 - s * 0.35) * r.uniform(0.94, 1.04)
        out_dir = nrm * 0.9 + u * 0.42; out_dir /= np.linalg.norm(out_dir)
        bend = u * L * 0.16
        rib = spline([p, p + out_dir * L * 0.5 + bend * 0.3, p + out_dir * L + bend], 12)
        n = 60
        t = np.linspace(0, 1, n)
        seg = np.linalg.norm(np.diff(rib, axis=0), axis=1); cum = np.concatenate([[0], np.cumsum(seg)])
        pts = np.stack([np.interp(t * cum[-1], cum, rib[:, 0]), np.interp(t * cum[-1], cum, rib[:, 1])], 1)
        tg = np.gradient(pts, axis=0); tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6
        nm = np.stack([-tg[:, 1], tg[:, 0]], 1)
        lobes = max(3, L / 15)
        wmax = min(30, 7 + L * 0.13)
        half = wmax * (0.62 + 0.38 * np.sin(np.pi * np.clip(t * 1.15, 0, 1)) ** 0.5) * np.sqrt(np.clip(1 - t, 0, 1) + 0.02)
        scallop = 0.7 + 0.3 * np.abs(np.sin(np.pi * lobes * t)) ** 0.6
        left = pts + nm * (half * scallop)[:, None]
        right = pts - nm * (half * np.roll(scallop, 1))[:, None]
        blades.append(np.vstack([left, right[::-1]]))
        ribs.append(rib)
        for j in range(int(lobes)):                             # a faint vein into every lobe
            tj = (j + 0.5) / lobes
            i = min(n - 1, int(tj * (n - 1)))
            for sd in (1, -1):
                ribs.append([tuple(pts[i]), tuple(pts[i] + (nm[i] * sd * 0.85 + tg[i] * 0.5) * half[i] * 0.8)])
    return rachis, blades, ribs


rachis, leaflets, ribs = fern((300, 1060), (440, 560), (800, 140), 215, 19, 3)
cy.place(cy.shapes(leaflets), opacity=0.88, texture=0.16)
cy.place(cy.lines(ribs, 1.6), opacity=0.5)
cy.line(rachis, 6.5, opacity=1.0, taper=True)
r2, l2, rb2 = fern((60, 960), (150, 700), (290, 470), 95, 12, 8)                     # a young frond behind it
cy.place(cy.shapes(l2), opacity=0.86, texture=0.18, lift=1.0)
cy.place(cy.lines(rb2, 1.3), opacity=0.45, lift=1.0)
cy.line(r2, 4, opacity=1.0, taper=True)
cy.stage('fern')


# ---- ginkgo sprig: fan-shaped bilobed leaves with fine radiating veins on long petioles
def ginkgo(px, py, ang, R, span=2.3, notch=0.22, seed=0):
    r = np.random.default_rng(seed)
    th = np.linspace(-span / 2, span / 2, 90)
    wav = 1 + 0.035 * fbm1d(90, 8, 3, seed)
    rad = R * (1 - notch * np.exp(-(th / 0.07) ** 2)) * (0.9 + 0.1 * np.cos(th * 1.3)) * wav
    edge = [(px + np.cos(ang + t) * rr, py + np.sin(ang + t) * rr) for t, rr in zip(th, rad)]
    blade = [(px, py)] + [(px + np.cos(ang + th[0]) * R * 0.25, py + np.sin(ang + th[0]) * R * 0.25)] + edge + \
            [(px + np.cos(ang + th[-1]) * R * 0.25, py + np.sin(ang + th[-1]) * R * 0.25)]
    veins = []
    for t in np.linspace(-span / 2 + 0.06, span / 2 - 0.06, 34):
        rr = R * (1 - notch * np.exp(-(t / 0.07) ** 2)) * (0.9 + 0.1 * np.cos(t * 1.3)) * 0.97
        mid = 0.35 * t
        veins.append(spline([(px, py), (px + np.cos(ang + mid) * rr * 0.3, py + np.sin(ang + mid) * rr * 0.3), (px + np.cos(ang + t) * rr, py + np.sin(ang + t) * rr)], 6))
    return blade, veins


GX, GY = 1120, 1060
blades, veins, stems = [], [], []
for (ang, plen, R, bend) in [(-2.05, 300, 128, 40), (-1.55, 360, 142, -20), (-1.02, 270, 120, -46), (-2.55, 170, 96, 30)]:
    tipx, tipy = GX + np.cos(ang) * plen, GY + np.sin(ang) * plen
    mid = ((GX + tipx) / 2 + bend, (GY + tipy) / 2)
    stems.append(spline([(GX, GY), mid, (tipx, tipy)], 12))
    b, v = ginkgo(tipx, tipy, ang, R, seed=int(R))
    blades.append(b); veins += v
cy.place(cy.shapes(blades), opacity=0.82, texture=0.12)
cy.place(cy.lines(veins, 1.3), opacity=0.55)
cy.place(cy.lines(stems, 4.2, taper=True), opacity=1.0)
cy.stage('ginkgo')

# ---- dandelion clock: seeds on a sphere, each a beak with an umbrella of filaments; fluff is lifted -> soft
DX, DY, DR = 1590, 330, 172
beaks, fluff = [], []
for i in range(340):
    v = rng.normal(size=3); v /= np.linalg.norm(v)
    proj = np.array([v[0], v[1]]); pl = np.linalg.norm(proj) + 1e-6
    u = proj / pl
    b0 = np.array([DX, DY]) + u * 10 * pl
    b1 = np.array([DX, DY]) + u * DR * 0.6 * pl
    beaks.append([tuple(b0), tuple(b1)])
    for f in range(14):
        a = np.arctan2(u[1], u[0]) + (f / 13 - 0.5) * 2.0
        L = DR * 0.42 * rng.uniform(0.8, 1.05) * (0.55 + 0.45 * pl)
        fluff.append([tuple(b1), tuple(b1 + np.array([np.cos(a), np.sin(a)]) * L)])
cy.place(cy.lines(fluff, 1.2), opacity=0.3, lift=1.1)
cy.place(cy.lines(beaks, 1.3), opacity=0.6, lift=0.8)
cy.place(cy.circle(DX, DY, 9), opacity=0.95, lift=1.0)
stem = spline([(DX, DY + 8), (DX - 20, DY + 240), (DX - 120, DY + 490), (DX - 250, H + 20)], 16)
cy.line(stem, 7, opacity=1.0, lift=1.0)


def seed(x, y, ang, s=1.0):
    """one loose seed drifting away: achene, long beak, pappus umbrella"""
    u = np.array([np.cos(ang), np.sin(ang)])
    a0 = np.array([x, y]); a1 = a0 + u * 20 * s; b1 = a1 + u * 64 * s
    cy.place(cy.shapes([Cyanotype.leaf_pts(a0[0], a0[1], ang, 22 * s, 5 * s, tip=0.5, n=10)]), opacity=0.95)
    cy.line([tuple(a1), tuple(b1)], 1.4, opacity=0.75, lift=0.5)
    fl = []
    for f in range(18):
        a = ang + (f / 17 - 0.5) * 2.3
        fl.append([tuple(b1), tuple(b1 + np.array([np.cos(a), np.sin(a)]) * 46 * s)])
    cy.place(cy.lines(fl, 1.2), opacity=0.6, lift=0.8)


for (x, y, a, s) in [(1300, 230, -2.25, 1.0), (1180, 140, -2.55, 0.9), (1110, 330, -2.05, 0.8), (980, 210, -2.8, 0.85), (1270, 400, -2.35, 0.72)]:
    seed(x, y, a, s)
cy.stage('dandelion')

# ---- white handwriting printed in, and a pencil note on the margin
cy.label('Fern, Ginkgo', 1792, 866, 52, anchor='rs', rot=2)
cy.label('& Dandelion', 1792, 924, 52, anchor='rs', rot=2)
cy.label('sun print · 14 min', 1790, 972, 32, anchor='rs', rot=2, opacity=0.85)
cy.pencil('No. 7 — June, bright sun', 104, 1046, 30, anchor='ls', rot=0.6)

cy.save(out, stages_dir=stages)
print('saved', out)
