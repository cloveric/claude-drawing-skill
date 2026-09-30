"""Example (aurora glassmorphism): 晨间计划 · Morning Plan — one weekday morning at 08:26, told by a stack of
frosted-glass widgets over a sunrise-coloured aurora: the plan card (3 of 5 done, the deep-work block running now),
a focus ring counting down that block, today's weather (a glossy sun behind a glass cloud), the focus settings
(do-not-disturb on, rain noise at 40 %), the last seven days of focus time, and a reminder pill for the 9:00
stand-up. Warm gradients belong to the morning plan, cool ones to focus. No image model.
python3 aurora_morning.py [out.jpg] [--stages DIR]
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from aurora import Aurora, INK, WARM, COOL, MINT, WHITE

out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'aurora_morning.jpg'
stages = sys.argv[sys.argv.index('--stages') + 1] if '--stages' in sys.argv else None

a = Aurora(1920, 1080, seed=5)

# ---- the aurora: a sunrise wash, warm at the top, cool below, one pale ribbon of light across it
a.backdrop(base='#f6f2fb',
           blobs=[(260, 150, 560, 380, '#ffb28c', 1.0),      # apricot
                  (980, 40, 640, 300, '#ffe29a', 0.9),       # butter (the sun is up)
                  (1700, 220, 520, 440, '#bba2ff', 1.0),     # lilac
                  (880, 640, 520, 400, '#ff9cc9', 0.8),      # pink
                  (200, 930, 600, 400, '#86cbff', 1.0),      # sky
                  (1640, 960, 620, 380, '#8feccd', 0.9),     # mint
                  (1330, 600, 420, 320, '#a7bfff', 0.7)],    # periwinkle
           ribbons=[([(-120, 560), (420, 520), (1000, 600), (1500, 600), (2040, 470)], 70, '#fff8f0', 1.4),
                    ([(-100, 1080), (600, 1020), (1300, 1010), (2040, 1000)], 60, '#c6b2ff', 1.0),
                    ([(900, -40), (1320, 60), (1700, 40), (2040, -20)], 60, '#ffd0e4', 0.9)],
           grain=0.019)
a.sparkles(46)
a.stage('aurora')

a.orb(596, 150, 104, ('#fff0dc', '#ffa2b8', '#8e6bff'))
a.orb(1700, 628, 100, ('#e3f7ff', '#6cc0ff', '#6a55ff'))
a.orb(1175, 1000, 58, ('#f4fff9', '#8fe8c8', '#4f9dff'))
a.stage('orbs')

# ---- weather (behind the plan card)
w = a.glass(130, 110, 590, 500, radius=38)
a.text('今天 · 晴', w.x0 + 40, w.y0 + 62, 24, INK, 'medium', alpha=0.62)
a.text('21°', w.x0 + 34, w.y0 + 176, 104, INK, 'light', spacing=-3)
a.sun(w.x0 + 286, w.y0 + 100, 46)
a.cloud(w.x0 + 318, w.y0 + 146, 128)
a.text('微风 · 最高 26° 最低 15°', w.x0 + 40, w.y0 + 226, 21, INK, 'regular', alpha=0.6)
pts = a.spark(w.x0 + 58, w.y0 + 272, w.x0 + 330, w.y0 + 318, [21, 22, 24, 25, 26], WARM, 3, fill=0.16, dots=(0,))
for i, (x, y) in enumerate(pts):
    a.text('现在' if i == 0 else f'{8 + i}时', x, w.y0 + 364, 18, INK, 'semibold' if i == 0 else 'regular', 'ms',
           alpha=0.85 if i == 0 else 0.5)
a.stage('weather')

# ---- focus settings (behind the plan card)
c = a.glass(130, 560, 590, 970, radius=38)
a.text('专注设置', c.x0 + 40, c.y0 + 64, 28, INK, 'semibold')
a.text('FOCUS', c.x0 + 40, c.y0 + 96, 15, INK, 'semibold', alpha=0.4, spacing=3)
a.text('勿扰模式', c.x0 + 40, c.y0 + 160, 24, INK, 'medium')
a.text('只有闹钟会响', c.x0 + 40, c.y0 + 190, 18, INK, alpha=0.5)
a.toggle(c.x0 + 270, c.y0 + 142, on=True)
a.divider(c.x0 + 40, c.x0 + 350, c.y0 + 226)
a.text('自动回复', c.x0 + 40, c.y0 + 272, 24, INK, 'medium')
a.toggle(c.x0 + 270, c.y0 + 246, on=False)
a.text('白噪音 · 雨声', c.x0 + 40, c.y0 + 334, 22, INK, 'medium', alpha=0.85)
a.text('40%', c.x0 + 350, c.y0 + 334, 20, INK, 'medium', 'rs', alpha=0.55)
a.slider(c.x0 + 44, c.x0 + 346, c.y0 + 368, 0.4)
a.stage('settings')

# ---- the plan: the card this morning is about
p = a.glass(520, 200, 1190, 990, radius=44, blur=30, elevation=34, shadow=0.3)
X0, X1 = p.x0 + 56, p.x1 - 56
a.stage('plan_glass')
a.text('MORNING PLAN', X0, p.y0 + 66, 16, INK, 'semibold', alpha=0.45, spacing=3.5)
a.text('周三', X1, p.y0 + 66, 20, INK, 'medium', 'rs', alpha=0.5)
a.text('晨间计划', X0, p.y0 + 134, 56, INK, 'semibold')
a.text('7:00 – 9:30 · 已完成 3 / 5', X0, p.y0 + 176, 22, INK, alpha=0.6)
a.rrect(X0, p.y0 + 204, X1, p.y0 + 216, 6, WHITE, 0.5)
a.rrect(X0, p.y0 + 204, X0 + (X1 - X0) * 0.6, p.y0 + 216, 6, grad=WARM)
a.text('60%', X1, p.y0 + 176, 22, INK, 'semibold', 'rs', alpha=0.75)

rows = [('07:00', '起床，喝一杯温水', '', 'done'),
        ('07:15', '拉伸', '10 分钟', 'done'),
        ('07:30', '早餐 · 燕麦和水果', '', 'done'),
        ('08:00', '深度工作 · 写方案', '', 'now'),
        ('09:00', '团队站会', '15 分钟', 'todo')]
y = p.y0 + 286
cx = X0 + 20
for i, (t, title, note, st) in enumerate(rows):
    if i < len(rows) - 1:                                     # the thread between the checks
        a.line([(cx, y + 26), (cx, y + 84 - 26)], 3, WHITE, 0.8 if st == 'done' else 0.5)
    if st == 'now':
        a.pill(X0 - 16, y - 38, X1 + 16, y + 38, blur=6, tint=0.5, shadow=0.14)
        a.check(cx, y, 20, 'now', COOL, frac=0.59)
        a.text(t, X0 + 58, y, 21, INK, 'semibold', 'lm', alpha=0.8)
        a.text(title, X0 + 146, y, 27, INK, 'semibold', 'lm')
        a.rrect(X1 - 128, y - 20, X1, y + 20, 20, grad=COOL, angle=0, shadow=0.15)
        a.text('进行中', X1 - 64, y, 19, WHITE, 'semibold', 'mm')
    else:
        a.check(cx, y, 20, st, WARM)
        al = 1.0 if st == 'done' else 0.9
        a.text(t, X0 + 58, y, 21, INK, 'medium', 'lm', alpha=0.5)
        a.text(title, X0 + 146, y, 27, INK, 'medium', 'lm', alpha=0.62 if st == 'done' else 0.92)
        if note: a.text(note, X1, y, 20, INK, 'regular', 'rm', alpha=0.45)
    y += 84
a.pill(X0, p.y1 - 96, X0 + 170, p.y1 - 50, tint=0.5)
a.text('＋ 添加事项', X0 + 85, p.y1 - 73, 19, INK, 'medium', 'mm', alpha=0.8)
a.pill(X0 + 186, p.y1 - 96, X0 + 356, p.y1 - 50, tint=0.5)
a.text('明早照旧', X0 + 271, p.y1 - 73, 19, INK, 'medium', 'mm', alpha=0.8)
a.stage('plan')

# ---- focus ring: the deep-work block, 18:24 left of 45 minutes
f = a.glass(1150, 96, 1570, 576, radius=40, elevation=30, shadow=0.3)
a.text('专注中', f.x0 + 40, f.y0 + 62, 26, INK, 'semibold')
a.text('45 分钟', f.x1 - 40, f.y0 + 62, 20, INK, 'medium', 'rs', alpha=0.5)
a.ring(f.cx, f.y0 + 238, 118, 20, 26.6 / 45, COOL)
a.text('18:24', f.cx, f.y0 + 250, 58, INK, 'semibold', 'ms', spacing=-1)
a.text('深度工作 · 写方案', f.cx, f.y0 + 290, 19, INK, 'regular', 'ms', alpha=0.55)
a.pill(f.x0 + 40, f.y1 - 92, f.cx - 10, f.y1 - 40, tint=0.5)
a.text('暂停', (f.x0 + 40 + f.cx - 10) / 2, f.y1 - 66, 20, INK, 'medium', 'mm', alpha=0.8)
a.rrect(f.cx + 10, f.y1 - 92, f.x1 - 40, f.y1 - 40, 26, grad=COOL, angle=0, shadow=0.18)
a.text('休息 5 分钟', (f.cx + 10 + f.x1 - 40) / 2, f.y1 - 66, 20, WHITE, 'semibold', 'mm')
a.stage('focus')

# ---- the last seven days of focus time
k = a.glass(1230, 636, 1810, 976, radius=38, blur=20)
a.text('近 7 天专注', k.x0 + 40, k.y0 + 60, 24, INK, 'semibold')
a.text('15.2', k.x0 + 40, k.y0 + 132, 60, INK, 'semibold', spacing=-1)
wv = a.text_width('15.2', 60, 'semibold', -1)
a.text('小时', k.x0 + 48 + wv, k.y0 + 132, 22, INK, 'medium', alpha=0.55)
a.rrect(k.x0 + 40, k.y0 + 156, k.x0 + 150, k.y0 + 190, 17, grad=MINT, angle=0)
a.text('↑ 18%', k.x0 + 95, k.y0 + 173, 18, WHITE, 'semibold', 'mm')
a.bars(k.x0 + 244, k.y0 + 66, k.x1 - 30, k.y1 - 74, [2.8, 3.1, 1.2, 0.6, 3.6, 2.5, 1.4], 4.0,
       ['24', '25', '26', '27', '28', '29', '今天'], highlight=6, label_size=18)
a.text('较上周', k.x0 + 162, k.y0 + 173, 18, INK, 'regular', 'lm', alpha=0.5)
a.stage('week')

# ---- the reminder pill at the top
n = a.pill(660, 56, 1100, 146, blur=14, tint=0.4, shadow=0.22, elevation=18)
a.app_icon(n.x0 + 22, n.y0 + 17, 56, WARM, '9', 30)
a.text('9:00 团队站会', n.x0 + 94, n.y0 + 40, 22, INK, 'semibold', 'lm')
a.text('还有 34 分钟 · 会议室 B', n.x0 + 94, n.y0 + 66, 17, INK, 'regular', 'lm', alpha=0.55)
a.text('现在', n.x1 - 30, n.y0 + 40, 16, INK, 'regular', 'rm', alpha=0.45)

a.save(out, stages)
