# -*- coding: utf-8 -*-
# GDSH shared render module (chart SVG builders + palette). Auto-extracted from verified generator.
import html

# Apple HIG light palette (2026-09-24) — replaced the warm Playfair palette.
# Names kept; values migrated. ACC/CRIT/WARN are FILLS (bars, dots, lines);
# text never sits in a raw fill — ink() returns the darker *_INK variant that
# clears 4.5:1 on white. MUT is #6C6C70 (not HIG #8E8E93) to keep AA on 12px.
BG="#F2F2F7"; PAPER="#FFFFFF"; SURF="#F2F2F7"; SUNK="#F2F2F7"; INK="#1C1C1E"; INKS="#3C3C43"
MUT="#6C6C70"; RULE="#E5E5EA"; ACC="#007AFF"; ACCBG="#E8F1FE"; CRIT="#FF3B30"; WARN="#FF9500"
ACC_INK="#0060DF"; CRIT_INK="#C4271D"; WARN_INK="#8A5200"
PLAN=ACC   # Kế hoạch = xanh (blue)
ACT=CRIT   # Thực hiện = đỏ
# Categorical fills for the OPEX donut (#2) — not the semantic four, so a slice
# never reads as "plan" or "critical". Light hex, CSS token.
CAT=[("#5856D6","--c1"),("#AF52DE","--c2"),("#30B0C7","--c3"),("#A2845E","--c4"),
     ("#8E8E93","--c5"),("#AEAEB2","--c6"),("#C7C7CC","--c7"),("#D1D1D6","--c8"),("#DCDCE0","--c9")]
def ink(c): return {ACC:ACC_INK, CRIT:CRIT_INK, WARN:WARN_INK}.get(c, c)

# Every colour the SVG builders write as a fill/stroke attribute, and the CSS
# token that repaints it. page_style() turns this into `svg [fill="#…"]` rules,
# so the charts follow dark mode without the builders emitting var() into
# presentation attributes (which WebKit does not resolve).
SVG_TOKENS=[(SUNK,"--sunk"),(INK,"--ink"),(INKS,"--ink-soft"),(MUT,"--muted"),(RULE,"--rule"),
            (ACC,"--accent"),(CRIT,"--critical-fill"),(WARN,"--warning-fill"),
            (ACC_INK,"--accent-ink"),(CRIT_INK,"--critical"),(WARN_INK,"--warning")]+CAT

def esc(s): return html.escape(str(s))
def tr(x): return f"{x/1e6:,.0f}"      # triệu
def bn(x): return f"{x/1e9:.2f}"       # tỷ
def vnd(x):                                # gọn: tỷ (2 số lẻ) / triệu / đồng ; dấu trừ unicode
    ax=abs(x)
    if ax>=1e9: s=f"{x/1e9:.2f} tỷ".replace(".", ",")
    elif ax>=1e6: s=f"{x/1e6:.0f} tr"
    else: s=f"{x:,.0f}".replace(",", ".") + " đ"
    return s.replace("-", "−")

# ---------- existing grouped vertical bars (chart 1) ----------
def grouped_bars(series, cats, colors, unit="tỷ", w=820, h=360, maxv=None):
    pad_l=54; pad_r=16; pad_t=16; pad_b=64
    plot_w=w-pad_l-pad_r; plot_h=h-pad_t-pad_b
    vals=[v for _,arr in series for v in arr]
    mx=(maxv if maxv else max(vals))*1.12
    n=len(cats); groups=len(series); gw=plot_w/n; bw=gw*0.62/groups
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    for i in range(6):
        val=mx/5*i; y=pad_t+plot_h-(val/mx*plot_h)
        s.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="{RULE}"/>')
        s.append(f'<text x="{pad_l-6}" y="{y+3:.1f}" text-anchor="end" font-size="11" fill="{MUT}">{val/1e9:.0f}</text>')
    for ci,cat in enumerate(cats):
        gx=pad_l+ci*gw+gw*0.19
        for si,(lab,arr) in enumerate(series):
            v=arr[ci]; bh=v/mx*plot_h; x=gx+si*bw; y=pad_t+plot_h-bh
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw*0.9:.1f}" height="{bh:.1f}" fill="{colors[si]}"/>')
            s.append(f'<text x="{x+bw*0.45:.1f}" y="{y-4:.1f}" text-anchor="middle" font-size="10.5" fill="{INKS}" style="font-variant-numeric:tabular-nums">{bn(v)}</text>')
        s.append(f'<text x="{pad_l+ci*gw+gw/2:.1f}" y="{h-pad_b+18:.1f}" text-anchor="middle" font-size="12" fill="{INK}">{esc(cat)}</text>')
    lx=pad_l; ly=h-18
    for si,(lab,_) in enumerate(series):
        s.append(f'<rect x="{lx}" y="{ly-9}" width="12" height="12" fill="{colors[si]}"/>')
        s.append(f'<text x="{lx+16}" y="{ly}" font-size="12" fill="{INKS}">{esc(lab)}</text>')
        lx+=len(lab)*7.2+40
    s.append(f'<text x="{w-pad_r}" y="{h-6}" text-anchor="end" font-size="10.5" fill="{MUT}">ĐVT: {unit} VNĐ</text>')
    s.append('</svg>'); return "".join(s)

# ---------- grouped horizontal bars: plan vs actual per row ----------
def ghbars(rows, w=820, unit="triệu", show_pct=True):
    # rows: (label, plan, actual)
    pad_l=176; pad_r=104; pad_t=34; rh=52
    h=pad_t+rh*len(rows)+10
    plot_w=w-pad_l-pad_r
    mx=max(max(p,a) for _,p,a in rows)*1.02
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    # legend
    s.append(f'<rect x="{pad_l}" y="10" width="12" height="12" fill="{PLAN}"/><text x="{pad_l+16}" y="20" font-size="12" fill="{INKS}">Kế hoạch</text>')
    s.append(f'<rect x="{pad_l+110}" y="10" width="12" height="12" fill="{ink(ACT)}"/><text x="{pad_l+126}" y="20" font-size="12" fill="{INKS}">Thực hiện 31/08</text>')
    for i,(lab,p,a) in enumerate(rows):
        y=pad_t+i*rh
        pbw=p/mx*plot_w; abw=a/mx*plot_w
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+2:.1f}" text-anchor="end" font-size="12" fill="{INK}">{esc(lab)}</text>')
        # plan bar (top)
        s.append(f'<rect x="{pad_l}" y="{y+6:.1f}" width="{pbw:.1f}" height="15" fill="{PLAN}"/>')
        s.append(f'<text x="{pad_l+pbw+5:.1f}" y="{y+18:.1f}" font-size="10.5" fill="{INKS}" style="font-variant-numeric:tabular-nums">{tr(p)}</text>')
        # actual bar (bottom)
        s.append(f'<rect x="{pad_l}" y="{y+26:.1f}" width="{max(abw,0.6):.1f}" height="15" fill="{ACT}"/>')
        s.append(f'<text x="{pad_l+max(abw,0.6)+5:.1f}" y="{y+38:.1f}" font-size="10.5" fill="{ink(ACT)}" style="font-variant-numeric:tabular-nums">{tr(a)}</text>')
        if show_pct:
            r=(a/p*100) if p else 0
            s.append(f'<text x="{w-pad_r+92:.1f}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12.5" font-weight="600" fill="{ink(ACT) if r<50 else INKS}" style="font-variant-numeric:tabular-nums">{r:.1f}%</text>')
    s.append(f'<text x="{w-4}" y="{pad_t-16:.1f}" text-anchor="end" font-size="10.5" fill="{MUT}">% đạt</text>')
    s.append(f'<text x="{w-4}" y="{h-4}" text-anchor="end" font-size="10.5" fill="{MUT}">ĐVT: {unit} VNĐ</text>')
    s.append('</svg>'); return "".join(s)

# ---------- structure-mix bars: plan-mix% vs actual-mix% (share of a total) ----------
def mixbars(rows, w=820, cat="chi phí vận hành"):
    # rows: (label, plan_pct, actual_pct[, flag])
    pad_l=176; pad_r=96; pad_t=34; rh=52
    h=pad_t+rh*len(rows)+10
    plot_w=w-pad_l-pad_r
    mx=max(max(r[1],r[2]) for r in rows)*1.06
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    s.append(f'<rect x="{pad_l}" y="10" width="12" height="12" fill="{PLAN}"/><text x="{pad_l+16}" y="20" font-size="12" fill="{INKS}">Cơ cấu Kế hoạch</text>')
    s.append(f'<rect x="{pad_l+140}" y="10" width="12" height="12" fill="{ink(ACT)}"/><text x="{pad_l+156}" y="20" font-size="12" fill="{INKS}">Cơ cấu Thực hiện 31/08</text>')
    s.append(f'<text x="{w-4}" y="20" text-anchor="end" font-size="10.5" fill="{MUT}">Δ điểm %</text>')
    for i,row in enumerate(rows):
        lab,p,a = row[0],row[1],row[2]; flag = row[3] if len(row)>3 else False
        y=pad_t+i*rh
        pbw=p/mx*plot_w; abw=a/mx*plot_w; d=a-p
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+2:.1f}" text-anchor="end" font-size="12" fill="{INK}">{esc(lab)}</text>')
        s.append(f'<rect x="{pad_l}" y="{y+6:.1f}" width="{pbw:.1f}" height="15" fill="{PLAN}"/>')
        s.append(f'<text x="{pad_l+pbw+5:.1f}" y="{y+18:.1f}" font-size="10.5" fill="{INKS}" style="font-variant-numeric:tabular-nums">{p:.1f}%</text>')
        s.append(f'<rect x="{pad_l}" y="{y+26:.1f}" width="{max(abw,0.6):.1f}" height="15" fill="{ACT}"/>')
        s.append(f'<text x="{pad_l+max(abw,0.6)+5:.1f}" y="{y+38:.1f}" font-size="10.5" fill="{ink(ACT)}" style="font-variant-numeric:tabular-nums">{a:.1f}%</text>')
        dcol=ink(CRIT) if flag else INKS
        s.append(f'<text x="{w-6:.1f}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12.5" font-weight="600" fill="{dcol}" style="font-variant-numeric:tabular-nums">{d:+.1f}</text>')
    s.append(f'<text x="{w-6}" y="{h-4}" text-anchor="end" font-size="10.5" fill="{MUT}">% trong TỔNG {cat}</text>')
    s.append('</svg>'); return "".join(s)

# ---------- gross-profit contribution (đồng), plan vs actual, diverging ----------
def gpbars(rows, w=820, LMIN=-0.8, RMAX=2.5):
    # rows: (label, plan_ty, actual_ty)  values in tỷ
    pad_l=176; pad_r=22; pad_t=34; rh=50
    h=pad_t+rh*len(rows)+16
    plot_w=w-pad_l-pad_r; span=RMAX-LMIN
    zero=pad_l+(0-LMIN)/span*plot_w
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    s.append(f'<rect x="{pad_l}" y="10" width="12" height="12" fill="{PLAN}"/><text x="{pad_l+16}" y="20" font-size="12" fill="{INKS}">Kế hoạch (cả năm)</text>')
    s.append(f'<rect x="{pad_l+150}" y="10" width="12" height="12" fill="{ink(ACT)}"/><text x="{pad_l+166}" y="20" font-size="12" fill="{INKS}">Thực hiện (6 tháng)</text>')
    s.append(f'<line x1="{zero:.1f}" y1="{pad_t}" x2="{zero:.1f}" y2="{h-16}" stroke="{RULE}"/>')
    for i,(lab,pl,ac) in enumerate(rows):
        y=pad_t+i*rh
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+2:.1f}" text-anchor="end" font-size="12" fill="{INK}">{esc(lab)}</text>')
        for v,col,off in [(pl,PLAN,6),(ac,ACT,25)]:
            vc=max(LMIN,min(RMAX,v)); x=pad_l+(vc-LMIN)/span*plot_w
            if v>=0:
                s.append(f'<rect x="{zero:.1f}" y="{y+off:.1f}" width="{max(x-zero,0.6):.1f}" height="14" fill="{col}"/>')
                tx=x+5; anc="start"
            else:
                s.append(f'<rect x="{x:.1f}" y="{y+off:.1f}" width="{max(zero-x,0.6):.1f}" height="14" fill="{col}"/>')
                tx=x-5; anc="end"
            s.append(f'<text x="{tx:.1f}" y="{y+off+11:.1f}" text-anchor="{anc}" font-size="10" fill="{ink(col)}" style="font-variant-numeric:tabular-nums">{v:+.2f}</text>')
    s.append(f'<text x="{zero:.1f}" y="{h-2}" text-anchor="middle" font-size="10" fill="{MUT}">0</text>')
    s.append(f'<text x="{w-6}" y="{h-2}" text-anchor="end" font-size="10.5" fill="{MUT}">Đóng góp LN gộp · ĐVT: tỷ VNĐ</text>')
    s.append('</svg>'); return "".join(s)

# ---------- grouped diverging margin: plan vs actual %, clamped ----------
def gmargin(rows, w=820, LMIN=-160, RMAX=80):
    # rows: (label, plan_pct, actual_pct)
    pad_l=176; pad_r=20; pad_t=34; rh=50
    h=pad_t+rh*len(rows)+16
    plot_w=w-pad_l-pad_r; span=RMAX-LMIN
    zero=pad_l+(0-LMIN)/span*plot_w
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    s.append(f'<rect x="{pad_l}" y="10" width="12" height="12" fill="{PLAN}"/><text x="{pad_l+16}" y="20" font-size="12" fill="{INKS}">Biên KH</text>')
    s.append(f'<rect x="{pad_l+90}" y="10" width="12" height="12" fill="{ink(ACT)}"/><text x="{pad_l+106}" y="20" font-size="12" fill="{INKS}">Biên TH 31/08 (kẹp trần −160%)</text>')
    s.append(f'<line x1="{zero:.1f}" y1="{pad_t}" x2="{zero:.1f}" y2="{h-16}" stroke="{RULE}"/>')
    def barx(v):
        vc=max(LMIN,min(RMAX,v))
        x=pad_l+(vc-LMIN)/span*plot_w
        return x,vc
    for i,(lab,pl,ac) in enumerate(rows):
        y=pad_t+i*rh
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+2:.1f}" text-anchor="end" font-size="12" fill="{INK}">{esc(lab)}</text>')
        for j,(v,col,off) in enumerate([(pl,PLAN,6),(ac,ACT,25)]):
            x,vc=barx(v)
            if vc>=0:
                s.append(f'<rect x="{zero:.1f}" y="{y+off:.1f}" width="{x-zero:.1f}" height="14" fill="{col}"/>')
                tx=x+5; anc="start"
            else:
                s.append(f'<rect x="{x:.1f}" y="{y+off:.1f}" width="{zero-x:.1f}" height="14" fill="{col}"/>')
                tx=x-5; anc="end"
            clamp="" if LMIN<v<RMAX else "★"
            s.append(f'<text x="{tx:.1f}" y="{y+off+11:.1f}" text-anchor="{anc}" font-size="10" fill="{ink(col)}" style="font-variant-numeric:tabular-nums">{v:+.0f}%{clamp}</text>')
    s.append(f'<text x="{zero:.1f}" y="{h-2}" text-anchor="middle" font-size="10" fill="{MUT}">0%   (★ = kẹp trần, giá trị thật ghi cạnh)</text>')
    s.append('</svg>'); return "".join(s)

# ---------- two cumulative lines: actual vs plan ----------
def line2(actual, plan, w=980, h=420, unit="tỷ"):
    pad_l=66; pad_r=22; pad_t=44; pad_b=60
    plot_w=w-pad_l-pad_r; plot_h=h-pad_t-pad_b
    mx=max(max(abs(v) for _,v in actual), max(abs(v) for _,v in plan))*1.1
    n=len(actual); step=plot_w/(n-1)
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    for i in range(6):
        val=mx/5*i; y=pad_t+val/mx*plot_h
        s.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="{RULE}"/>')
        s.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" font-size="13" fill="{MUT}" style="font-variant-numeric:tabular-nums">-{val/1e9:.0f}</text>')
    def pts(series): return [(pad_l+i*step, pad_t+abs(v)/mx*plot_h) for i,(_,v) in enumerate(series)]
    pa=pts(actual); pp=pts(plan)
    dp="M"+" L".join(f"{x:.1f},{y:.1f}" for x,y in pp)
    s.append(f'<path d="{dp}" fill="none" stroke="{PLAN}" stroke-width="2.6" stroke-dasharray="7 5"/>')
    da="M"+" L".join(f"{x:.1f},{y:.1f}" for x,y in pa)
    s.append(f'<path d="{da}" fill="none" stroke="{ACT}" stroke-width="3.2"/>')
    for (x,y),(_,v) in zip(pp,plan):
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="{PLAN}"/>')
    for (x,y),(lab,v) in zip(pa,actual):
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{ACT}"/>')
        s.append(f'<text x="{x:.1f}" y="{y+21:.1f}" text-anchor="middle" font-size="14" font-weight="600" fill="{ink(ACT)}" style="font-variant-numeric:tabular-nums">{v/1e9:.2f}</text>')
        s.append(f'<text x="{x:.1f}" y="{h-26:.1f}" text-anchor="middle" font-size="15" fill="{INK}">{esc(lab)}</text>')
    s.append(f'<rect x="{pad_l}" y="12" width="20" height="5" fill="{PLAN}"/><text x="{pad_l+28}" y="21" font-size="14" fill="{INKS}">Kế hoạch (mốc T3–T8, phân bổ đều)</text>')
    s.append(f'<rect x="{pad_l+360}" y="12" width="20" height="5" fill="{ink(ACT)}"/><text x="{pad_l+388}" y="21" font-size="14" fill="{INKS}">Thực hiện</text>')
    s.append(f'<text x="{w-pad_r}" y="{h-6}" text-anchor="end" font-size="12.5" fill="{MUT}">Lỗ P&L lũy kế · ĐVT: {unit} VNĐ</text>')
    s.append('</svg>'); return "".join(s)

# ---------- simple labeled vertical bars (charts 6,7,8) ----------
def vbars(rows, w=760, h=300, unit="", note=""):
    # rows: (label, value, color)
    pad_t=34; pad_b=64; plot_h=h-pad_t-pad_b
    mx=max(v for _,v,_ in rows)*1.16
    n=len(rows); gw=w/n; bw=min(120, gw*0.5)
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    for i,(lab,v,col) in enumerate(rows):
        bh=v/mx*plot_h; x=gw*i+(gw-bw)/2; y=pad_t+plot_h-bh
        disp=(f"{v:,.0f}".replace(",",".") if abs(v-round(v))<1e-9 else f"{v:.2f}".replace(".",","))
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}"/>')
        s.append(f'<text x="{x+bw/2:.1f}" y="{y-8:.1f}" text-anchor="middle" font-size="16" font-weight="600" fill="{ink(col)}" style="font-variant-numeric:tabular-nums">{disp}</text>')
        for k,wd in enumerate(lab.split("|")):
            s.append(f'<text x="{x+bw/2:.1f}" y="{h-pad_b+18+k*15:.1f}" text-anchor="middle" font-size="11.5" fill="{INK}">{esc(wd.strip())}</text>')
    if note: s.append(f'<text x="{w-6}" y="{h-6}" text-anchor="end" font-size="10.5" fill="{MUT}">{esc(note)}</text>')
    s.append('</svg>'); return "".join(s)

def loss_bars(rows, w=820, h=340):
    pad_l=16; pad_r=16; pad_t=40; pad_b=74; plot_w=w-pad_l-pad_r; plot_h=h-pad_t-pad_b
    mx=max(abs(v) for _,v,_ in rows)*1.12
    n=len(rows); gw=plot_w/n; bw=gw*0.5
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    for i,(lab,v,col) in enumerate(rows):
        bh=abs(v)/mx*plot_h; x=pad_l+i*gw+gw*0.25; y=pad_t
        s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="{col}"/>')
        s.append(f'<text x="{x+bw/2:.1f}" y="{y-8:.1f}" text-anchor="middle" font-size="14" font-weight="600" fill="{ink(col)}" style="font-variant-numeric:tabular-nums">{v/1e9:.2f}</text>')
        for k,wd in enumerate(lab.split("|")):
            s.append(f'<text x="{x+bw/2:.1f}" y="{h-pad_b+16+k*14:.1f}" text-anchor="middle" font-size="11" fill="{INK}">{esc(wd.strip())}</text>')
    s.append(f'<text x="{w-pad_r}" y="{h-6}" text-anchor="end" font-size="10.5" fill="{MUT}">Lỗ ròng · ĐVT: tỷ VNĐ</text>')
    s.append('</svg>'); return "".join(s)

# ---------- two side-by-side donuts + right-side legend (share of total), plan vs actual ----------
def two_donuts(cats, totP, totA, w=900, h=344):
    import math
    r=90; ir=55; cy=196; cxL=150; cxR=362; lx=500
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    def draw(cx,idx,title,subtitle,centerpct):
        out=[f'<text x="{cx}" y="40" text-anchor="middle" font-size="13.5" font-weight="600" fill="{INK}">{esc(title)}</text>']
        out.append(f'<text x="{cx}" y="60" text-anchor="middle" font-size="12.5" fill="{MUT}" style="font-variant-numeric:tabular-nums">Tổng OPEX {esc(subtitle)}</text>')
        ang=-90
        for c in cats:
            v=c[idx]
            if v<=0.05: continue
            sweep=v/100*360; a0=math.radians(ang); a1=math.radians(ang+sweep)
            x0=cx+r*math.cos(a0); y0=cy+r*math.sin(a0); x1=cx+r*math.cos(a1); y1=cy+r*math.sin(a1)
            xi0=cx+ir*math.cos(a1); yi0=cy+ir*math.sin(a1); xi1=cx+ir*math.cos(a0); yi1=cy+ir*math.sin(a0)
            large=1 if sweep>180 else 0
            out.append(f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 {large} 1 {x1:.1f},{y1:.1f} L{xi0:.1f},{yi0:.1f} A{ir},{ir} 0 {large} 0 {xi1:.1f},{yi1:.1f} Z" fill="{c[3]}"/>')
            ang+=sweep
        out.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="24" font-weight="600" fill="{INK}" style="font-variant-numeric:tabular-nums">{centerpct}</text>')
        out.append(f'<text x="{cx}" y="{cy+24}" text-anchor="middle" font-size="11" fill="{MUT}">Nhân sự</text>')
        return "".join(out)
    ns=[c for c in cats if c[0]=="Nhân sự"][0]
    s.append(draw(cxL,1,"Kế hoạch",vnd(totP),f"{ns[1]:.1f}%".replace('.',',')))
    s.append(draw(cxR,2,"Thực hiện 31/08",vnd(totA),f"{ns[2]:.1f}%".replace('.',',')))
    ly=76
    for lab,pp,ap,col in cats:
        s.append(f'<rect x="{lx}" y="{ly-11}" width="13" height="13" rx="2" fill="{col}"/>')
        s.append(f'<text x="{lx+21}" y="{ly}" font-size="13.5" fill="{INKS}" style="font-variant-numeric:tabular-nums">{esc(lab)} · {pp:.1f}% → {ap:.1f}%</text>')
        ly+=29
    s.append('</svg>')
    return "".join(s)

# ---------- single-series % bars (chart 3: % đạt) ----------
def pctbars(rows, w=650, maxv=25):
    # rows: (label, pct, color, khvnd_str)   bảng 4 cột: nhãn | thanh | % (căn phải) | KH DT (căn phải)
    pad_l=196; pad_t=22; rh=32
    plot_w=300                       # vùng thanh
    x_pct=pad_l+plot_w+50            # cột % căn phải, ngay sau thanh
    x_kh=w-14                        # cột KH DT căn phải, sát ngay cột %
    h=pad_t+8+rh*len(rows)
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    s.append(f'<text x="{pad_l-8}" y="14" text-anchor="end" font-size="11.5" font-weight="600" fill="{INKS}">Sản phẩm</text>')
    s.append(f'<text x="{(pad_l+x_pct)/2:.0f}" y="14" text-anchor="middle" font-size="11.5" font-weight="600" fill="{INKS}">% thực thu / KH năm</text>')
    s.append(f'<text x="{x_kh}" y="14" text-anchor="end" font-size="11.5" font-weight="600" fill="{INKS}">KH DT</text>')
    for i,(lab,v,col,kh) in enumerate(rows):
        y=pad_t+i*rh; bw=v/maxv*plot_w
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12.5" fill="{INK}">{esc(lab)}</text>')
        s.append(f'<rect x="{pad_l}" y="{y+5:.1f}" width="{plot_w}" height="{rh-12}" fill="{SUNK}"/>')
        s.append(f'<rect x="{pad_l}" y="{y+5:.1f}" width="{max(bw,0.6):.1f}" height="{rh-12}" fill="{col}"/>')
        s.append(f'<text x="{x_pct}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12" fill="{ink(col)}" style="font-variant-numeric:tabular-nums">{v:.1f}%</text>')
        s.append(f'<text x="{x_kh}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12.5" fill="{INKS}" style="font-variant-numeric:tabular-nums">{esc(kh)}</text>')
    s.append('</svg>'); return "".join(s)

# ---------- single-series diverging margin (chart 4: biên gộp kế hoạch) ----------
def divbars(rows, w=820, maxv=80):
    pad_l=190; pad_r=20; pad_t=8; rh=34
    h=pad_t*2+rh*len(rows)+14
    plot_w=w-pad_l-pad_r; zero=pad_l+plot_w/2
    s=[f'<svg viewBox="0 0 {w} {h}" role="img" style="width:100%;height:auto">']
    s.append(f'<line x1="{zero:.1f}" y1="{pad_t}" x2="{zero:.1f}" y2="{h-16:.1f}" stroke="{RULE}"/>')
    for i,(lab,v) in enumerate(rows):
        y=pad_t+i*rh; bw=abs(v)/maxv*(plot_w/2); col=ACC if v>=0 else CRIT
        x=zero if v>=0 else zero-bw
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12.5" fill="{INK}">{esc(lab)}</text>')
        s.append(f'<rect x="{x:.1f}" y="{y+6:.1f}" width="{bw:.1f}" height="{rh-14}" fill="{col}"/>')
        tx=zero+bw+6 if v>=0 else zero-bw-6; anc="start" if v>=0 else "end"
        s.append(f'<text x="{tx:.1f}" y="{y+rh/2+4:.1f}" text-anchor="{anc}" font-size="12" fill="{ink(col)}" style="font-variant-numeric:tabular-nums">{v:+.1f}%</text>')
    s.append(f'<text x="{zero:.1f}" y="{h-2:.1f}" text-anchor="middle" font-size="10.5" fill="{MUT}">Biên gộp kế hoạch 0%</text>')
    s.append('</svg>'); return "".join(s)

# ---------- page stylesheet: base sheet + Apple layer (shared by build_auto.py) ----------
# Lives here, not in build_auto.py, so the <head> can be rebuilt without an Excel
# input. System font stack only — the Playfair/Be Vietnam webfonts were dropped.
_BASE_CSS = """
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);margin:0;line-height:1.55;font-size:15px}
.wrap{max-width:1000px;margin:0 auto;padding:32px 20px 64px}
h1{font-weight:600;font-size:30px;line-height:1.2;letter-spacing:-.021em;margin:0 0 6px}
h2{font-weight:600;font-size:19px;letter-spacing:-.012em;margin:0}
.masthead{border-bottom:2px solid var(--ink);padding-bottom:18px;margin-bottom:8px}
.meta{color:var(--muted);font-size:13px;margin-top:8px}
.verdict{background:var(--accent-bg);border:1px solid var(--accent);border-radius:12px;padding:18px 20px;margin:22px 0}
.verdict .lead{font-size:20px;color:var(--accent-ink);font-weight:600;letter-spacing:-.012em;margin:0 0 6px}
.verdict p{margin:6px 0 0}
.legend-note{font-size:12.5px;color:var(--ink-soft);margin:14px 0 0;padding:9px 13px;background:var(--paper);border:1px solid var(--rule);border-radius:8px}
.sw{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:baseline;margin:0 3px 0 8px}
.kpirow{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}
.kpi{background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:14px 16px}
.kpi.crit{border-left:3px solid var(--critical-fill)} .kpi.warn{border-left:3px solid var(--warning-fill)}
.kv{font-size:26px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}
.kpi.crit .kv{color:var(--critical)} .kpi.warn .kv{color:var(--warning)}
.kl{color:var(--muted);font-size:12.5px;margin-top:4px}
.card{background:var(--paper);border:1px solid var(--rule);border-radius:12px;padding:20px 22px;margin:16px 0}
.chd{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:2px}
.tag{font-size:11px;color:var(--accent-ink);border:1px solid var(--accent);border-radius:20px;padding:2px 10px;white-space:nowrap}
.sub{color:var(--ink-soft);font-size:13.5px;margin:4px 0 14px}
.note{background:var(--surface);border-left:3px solid var(--warning-fill);padding:10px 14px;border-radius:0 8px 8px 0;font-size:13.5px;color:var(--ink-soft);margin-top:14px}
.note.crit{border-left-color:var(--critical-fill)}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:4px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--rule)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}
thead th{background:var(--surface);color:var(--ink-soft);font-weight:600}
.neg{color:var(--critical)}
.q{border:1px solid var(--rule);border-radius:8px;padding:14px 16px 14px 46px;margin:10px 0;position:relative;background:var(--surface);counter-increment:q}
.qbox{counter-reset:q}
.q:before{content:counter(q);position:absolute;left:14px;top:14px;width:22px;height:22px;background:var(--accent);color:#fff;border-radius:50%;text-align:center;line-height:22px;font-size:13px;font-weight:600}
.q .qh{font-weight:600}
.qm{color:var(--muted);font-size:12.5px;display:block;margin-top:4px}
.qm b{color:var(--ink-soft);font-weight:600}
.gate td:first-child{font-weight:600;white-space:nowrap;color:var(--accent-ink)}
.gate td{vertical-align:top}
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.foot{color:var(--muted);font-size:12px;margin-top:28px;border-top:1px solid var(--rule);padding-top:14px}
@media (max-width:720px){.kpirow{grid-template-columns:1fr 1fr}.two{grid-template-columns:1fr}h1{font-size:24px}}
@media print{body{font-size:12px;background:#fff}.wrap{max-width:none;padding:0}.card,.kpi,.verdict,.note,.q,.legend-note{background:#fff!important;break-inside:avoid}.kv{color:var(--ink)!important}:root{--muted:#222;--ink-soft:#222}.tag{color:#222;border-color:#222}svg{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""

# Dark values — SCREEN only; print always gets the light sheet.
_DARK = ("--bg:#000000;--paper:#1C1C1E;--surface:#2C2C2E;--sunk:#2C2C2E;--rule:#38383A;"
         "--ink:#FFFFFF;--ink-soft:#D1D1D6;--muted:#98989F;"
         "--accent:#0A84FF;--accent-ink:#64B5FF;--accent-bg:rgba(10,132,255,.16);"
         "--critical-fill:#FF453A;--critical:#FF6961;--warning-fill:#FF9F0A;--warning:#FFB340;"
         "--c1:#5E5CE6;--c2:#BF5AF2;--c3:#40C8E0;--c4:#AC8E68;--c5:#98989D;--c6:#7C7C80;"
         "--c7:#636366;--c8:#545458;--c9:#48484A;"
         "--shadow-card:none;--shadow-float:0 8px 24px rgba(0,0,0,.5)")

_APPLE_CSS = """
/* ============================================================
   APPLE LAYER — apple-design skill, 2026-09-24 (modelled on Omni-TMDV).
   Additive: sits after the base sheet and only overrides.
   Dark mode is SCREEN-only — print always gets the light sheet.
   ============================================================ */
:root{color-scheme:light dark;
  --shadow-card:0 1px 2px rgba(0,0,0,.04),0 2px 8px rgba(0,0,0,.04);
  --shadow-float:0 1px 3px rgba(0,0,0,.06),0 8px 24px rgba(0,0,0,.06)}
@media screen and (prefers-color-scheme:dark){:root:not([data-theme="light"]){@DARK@}}
@media screen{:root[data-theme="dark"]{@DARK@}}

/* Charts — every SVG fill/stroke the builders write is repainted from its token */
@SVGMAP@

/* Typography — optical sizing; small text gets a hair of positive tracking */
body{font-optical-sizing:auto;text-rendering:optimizeLegibility}
.meta,.kl,.tag,.qm,.foot,.legend-note{letter-spacing:.01em}

/* Materials — cards float; the verdict floats highest */
.card,.kpi,.legend-note{box-shadow:var(--shadow-card)}
.verdict{box-shadow:var(--shadow-float)}

/* Accessibility — increased contrast strengthens hairlines and captions */
@media (prefers-contrast:more){:root{--rule:#8E8E93;--muted:#3C3C43}}
@media (prefers-contrast:more) and (prefers-color-scheme:dark){:root:not([data-theme="light"]){--rule:#8E8E93;--muted:#D1D1D6}}

@media print{.card,.kpi,.legend-note,.verdict{box-shadow:none!important}}
"""

def page_style():
    toks = [("--bg",BG),("--paper",PAPER),("--surface",SURF),("--sunk",SUNK),("--ink",INK),
            ("--ink-soft",INKS),("--muted",MUT),("--rule",RULE),("--accent",ACC),("--accent-ink",ACC_INK),
            ("--accent-bg",ACCBG),("--critical",CRIT_INK),("--critical-fill",CRIT),
            ("--warning",WARN_INK),("--warning-fill",WARN)] + [(t,h) for h,t in CAT]
    root = ":root{" + ";".join(f"{t}:{h}" for t,h in toks) + \
        ';--sans:-apple-system,BlinkMacSystemFont,"San Francisco","Helvetica Neue",Helvetica,Ubuntu,Roboto,"Segoe UI",sans-serif}'
    svgmap = "\n".join(f'svg [fill="{h}"]{{fill:var({t})}} svg [stroke="{h}"]{{stroke:var({t})}}' for h,t in SVG_TOKENS)
    apple = _APPLE_CSS.replace("@DARK@", _DARK).replace("@SVGMAP@", svgmap)
    return f"<style>\n{root}{_BASE_CSS}</style>\n<style id=\"apple-layer\">{apple}</style>"
