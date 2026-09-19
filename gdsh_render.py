# -*- coding: utf-8 -*-
# GDSH shared render module (chart SVG builders + palette). Auto-extracted from verified generator.
import html

PAPER="#FFFFFF"; SURF="#FAFAF8"; SUNK="#F3F3EF"; INK="#1C1C1A"; INKS="#44443F"
MUT="#6B6B64"; RULE="#E4E4DF"; ACC="#0F6E52"; ACCBG="#EAF3EF"; CRIT="#B02418"; WARN="#9A6B00"
PLAN=ACC   # Kế hoạch = xanh
ACT=CRIT   # Thực hiện = đỏ

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
    s.append(f'<rect x="{pad_l+110}" y="10" width="12" height="12" fill="{ACT}"/><text x="{pad_l+126}" y="20" font-size="12" fill="{INKS}">Thực hiện 31/08</text>')
    for i,(lab,p,a) in enumerate(rows):
        y=pad_t+i*rh
        pbw=p/mx*plot_w; abw=a/mx*plot_w
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+2:.1f}" text-anchor="end" font-size="12" fill="{INK}">{esc(lab)}</text>')
        # plan bar (top)
        s.append(f'<rect x="{pad_l}" y="{y+6:.1f}" width="{pbw:.1f}" height="15" fill="{PLAN}"/>')
        s.append(f'<text x="{pad_l+pbw+5:.1f}" y="{y+18:.1f}" font-size="10.5" fill="{INKS}" style="font-variant-numeric:tabular-nums">{tr(p)}</text>')
        # actual bar (bottom)
        s.append(f'<rect x="{pad_l}" y="{y+26:.1f}" width="{max(abw,0.6):.1f}" height="15" fill="{ACT}"/>')
        s.append(f'<text x="{pad_l+max(abw,0.6)+5:.1f}" y="{y+38:.1f}" font-size="10.5" fill="{ACT}" style="font-variant-numeric:tabular-nums">{tr(a)}</text>')
        if show_pct:
            r=(a/p*100) if p else 0
            s.append(f'<text x="{w-pad_r+92:.1f}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12.5" font-weight="600" fill="{ACT if r<50 else INKS}" style="font-variant-numeric:tabular-nums">{r:.1f}%</text>')
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
    s.append(f'<rect x="{pad_l+140}" y="10" width="12" height="12" fill="{ACT}"/><text x="{pad_l+156}" y="20" font-size="12" fill="{INKS}">Cơ cấu Thực hiện 31/08</text>')
    s.append(f'<text x="{w-4}" y="20" text-anchor="end" font-size="10.5" fill="{MUT}">Δ điểm %</text>')
    for i,row in enumerate(rows):
        lab,p,a = row[0],row[1],row[2]; flag = row[3] if len(row)>3 else False
        y=pad_t+i*rh
        pbw=p/mx*plot_w; abw=a/mx*plot_w; d=a-p
        s.append(f'<text x="{pad_l-8}" y="{y+rh/2+2:.1f}" text-anchor="end" font-size="12" fill="{INK}">{esc(lab)}</text>')
        s.append(f'<rect x="{pad_l}" y="{y+6:.1f}" width="{pbw:.1f}" height="15" fill="{PLAN}"/>')
        s.append(f'<text x="{pad_l+pbw+5:.1f}" y="{y+18:.1f}" font-size="10.5" fill="{INKS}" style="font-variant-numeric:tabular-nums">{p:.1f}%</text>')
        s.append(f'<rect x="{pad_l}" y="{y+26:.1f}" width="{max(abw,0.6):.1f}" height="15" fill="{ACT}"/>')
        s.append(f'<text x="{pad_l+max(abw,0.6)+5:.1f}" y="{y+38:.1f}" font-size="10.5" fill="{ACT}" style="font-variant-numeric:tabular-nums">{a:.1f}%</text>')
        dcol=CRIT if flag else INKS
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
    s.append(f'<rect x="{pad_l+150}" y="10" width="12" height="12" fill="{ACT}"/><text x="{pad_l+166}" y="20" font-size="12" fill="{INKS}">Thực hiện (6 tháng)</text>')
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
            s.append(f'<text x="{tx:.1f}" y="{y+off+11:.1f}" text-anchor="{anc}" font-size="10" fill="{col}" style="font-variant-numeric:tabular-nums">{v:+.2f}</text>')
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
    s.append(f'<rect x="{pad_l+90}" y="10" width="12" height="12" fill="{ACT}"/><text x="{pad_l+106}" y="20" font-size="12" fill="{INKS}">Biên TH 31/08 (kẹp trần −160%)</text>')
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
            s.append(f'<text x="{tx:.1f}" y="{y+off+11:.1f}" text-anchor="{anc}" font-size="10" fill="{col}" style="font-variant-numeric:tabular-nums">{v:+.0f}%{clamp}</text>')
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
        s.append(f'<text x="{x:.1f}" y="{y+21:.1f}" text-anchor="middle" font-size="14" font-weight="600" fill="{ACT}" style="font-variant-numeric:tabular-nums">{v/1e9:.2f}</text>')
        s.append(f'<text x="{x:.1f}" y="{h-26:.1f}" text-anchor="middle" font-size="15" fill="{INK}">{esc(lab)}</text>')
    s.append(f'<rect x="{pad_l}" y="12" width="20" height="5" fill="{PLAN}"/><text x="{pad_l+28}" y="21" font-size="14" fill="{INKS}">Kế hoạch (mốc T3–T8, phân bổ đều)</text>')
    s.append(f'<rect x="{pad_l+360}" y="12" width="20" height="5" fill="{ACT}"/><text x="{pad_l+388}" y="21" font-size="14" fill="{INKS}">Thực hiện</text>')
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
        s.append(f'<text x="{x+bw/2:.1f}" y="{y-8:.1f}" text-anchor="middle" font-size="16" font-weight="600" fill="{col}" style="font-variant-numeric:tabular-nums">{disp}</text>')
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
        s.append(f'<text x="{x+bw/2:.1f}" y="{y-8:.1f}" text-anchor="middle" font-size="14" font-weight="600" fill="{col}" style="font-variant-numeric:tabular-nums">{v/1e9:.2f}</text>')
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
        s.append(f'<text x="{x_pct}" y="{y+rh/2+4:.1f}" text-anchor="end" font-size="12" fill="{col}" style="font-variant-numeric:tabular-nums">{v:.1f}%</text>')
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
        s.append(f'<text x="{tx:.1f}" y="{y+rh/2+4:.1f}" text-anchor="{anc}" font-size="12" fill="{col}" style="font-variant-numeric:tabular-nums">{v:+.1f}%</text>')
    s.append(f'<text x="{zero:.1f}" y="{h-2:.1f}" text-anchor="middle" font-size="10.5" fill="{MUT}">Biên gộp kế hoạch 0%</text>')
    s.append('</svg>'); return "".join(s)
