#!/usr/bin/env python3
"""Build review/index.html: the two versions of the GDSH report (Bản A, Bản B) as two tabs.

Sources are the HTML exports of the two tabs of the working doc, kept in review/src/.
Style is copied from brief/index.html so the two pages read as one site.
Run: python3 tools/build_review.py
"""
import re, html, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "review" / "src"
brief = (ROOT / "brief" / "index.html").read_text(encoding="utf-8")
css = re.search(r"<style>(.*?)</style>", brief, re.S).group(1)

EXTRA_CSS = """
.tabs{display:flex;gap:6px;background:var(--page);border:1px solid var(--line);border-radius:10px;padding:4px;margin-top:16px;width:max-content;max-width:100%;overflow-x:auto}
.tabs button{font:inherit;font-size:.88rem;font-weight:600;color:var(--ink2);background:transparent;border:0;border-radius:7px;padding:8px 14px;cursor:pointer;white-space:nowrap;min-height:40px}
.tabs button[aria-selected="true"]{background:var(--card);color:var(--ink);box-shadow:0 1px 2px rgba(0,0,0,.08)}
.tabs button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.panel[hidden]{display:none}
.panel{display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}.panel>*{min-width:0}
.card h2{font-size:1.12rem;margin:0 0 10px}
.card h3{color:var(--ink);font-size:.98rem;margin:18px 0 6px}
.card h4{color:var(--ink);font-size:.9rem;margin:14px 0 6px}
.card table{margin:0;min-width:560px}
.card td p,.card li p{margin:0}
.card ul,.card ol{margin:0 0 12px}
figure{margin:8px 0 12px}figcaption{font-size:.78rem;color:var(--ink3);margin-top:4px}
.chart svg{width:100%;height:auto;display:block}
.srcnote{font-size:.8rem;color:var(--ink3)}
@media print{.tabs{display:none}.panel[hidden]{display:grid}}
"""

def chart_svg():
    rows = [("T9/26",2.20,2.20,2.20),("T10",0.46,0.42,1.42),("T11",-0.71,-0.56,0.44),("T12",-1.57,-0.36,0.64),
            ("T1/27",-2.42,-0.76,0.24),("T2",-3.26,-0.94,1.56),("T3",-4.95,-2.11,0.39),("T4",-5.78,-2.44,0.06),
            ("T5",-6.60,-2.60,1.20),("T6",-7.42,-2.79,1.01),("T7",-8.22,-2.98,0.82),("T8/27",-9.02,-3.27,0.53)]
    lo, hi, y0 = -10, 4, 80
    x = lambda i: 72 + i * 548 / (len(rows) - 1)
    y = lambda v: y0 + (hi - v) / (hi - lo) * 224
    f = lambda v: f"{v:.2f}".replace(".", ",").replace("-", "−")
    series = [(1, "A. Giữ nguyên", "var(--red)"), (2, "B. Không cấp vốn", "var(--amber)"), (3, "B. Có cấp vốn", "var(--green)")]
    o = ['<svg viewBox="0 0 760 380" role="img" aria-label="Tái cấu trúc kèm 3 đợt vốn giữ tiền trên 0 suốt 12 tháng" font-size="12" font-family="inherit">',
         '<text x="24" y="30" font-size="16" font-weight="600" fill="var(--ink)">Tái cấu trúc kèm 3 đợt vốn giữ tiền trên 0 suốt 12 tháng</text>',
         '<text x="24" y="52" fill="var(--ink3)">Tiền cuối tháng (tỷ đồng), ước tính mô hình</text>']
    for t in range(-10, 5, 2):
        if t != 0:
            o.append(f'<line x1="72" x2="620" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="var(--line)"/>')
        o.append(f'<text x="62" y="{y(t)+4:.1f}" text-anchor="end" fill="var(--ink3)">{str(t).replace("-","−")}</text>')
    o.append(f'<line x1="72" x2="620" y1="{y(0):.1f}" y2="{y(0):.1f}" stroke="var(--ink3)" stroke-dasharray="4 4"/>')
    o.append(f'<text x="{x(9):.1f}" y="{y(0)+16:.1f}" text-anchor="middle" fill="var(--ink3)">Mức 0: hết tiền</text>')
    for i, r in enumerate(rows):
        o.append(f'<text x="{x(i):.1f}" y="326" text-anchor="middle" fill="var(--ink3)">{r[0]}</text>')
    o.append('<text x="346" y="352" text-anchor="middle" fill="var(--ink3)">Tháng, T9/2026–T8/2027</text>')
    end = x(len(rows) - 1) + 12
    for k, name, col in series:
        pts = " ".join(f"{x(i):.1f},{y(r[k]):.1f}" for i, r in enumerate(rows))
        o.append(f'<polyline fill="none" stroke="{col}" stroke-width="2.5" stroke-linejoin="round" points="{pts}"/>')
        for i, r in enumerate(rows):
            o.append(f'<circle cx="{x(i):.1f}" cy="{y(r[k]):.1f}" r="3.5" fill="{col}"><title>{name}, {r[0]}: {f(r[k])} tỷ</title></circle>')
        last = rows[-1][k]
        o.append(f'<text x="{end:.1f}" y="{y(last)-2:.1f}" font-weight="600" fill="var(--ink)">{name}</text>')
        o.append(f'<text x="{end:.1f}" y="{y(last)+14:.1f}" fill="var(--ink3)">{f(last)}</text>')
    o.append("</svg>")
    return "".join(o)

def prep(src, prefix):
    s = src
    s = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", s, flags=re.S)                       # doc/tab title
    s = re.sub(r"^<p><time[^>]*>.*?</p>\s*", "", s, flags=re.S)                    # byline chips
    s = re.sub(r'<a data-atom="ref" data-ref="file/[^"]+">([^<]*)</a>',
               lambda m: '<a href="#ban-b" data-tab="b">' + m.group(1) + "</a>", s)
    s = re.sub(r'<figure data-embed="[^"]+">(.*?)</figure>',
               lambda m: '<figure class="chart">' + chart_svg() + m.group(1) + "</figure>", s, flags=re.S)
    s = re.sub(r'id="([^"]+)"', lambda m: f'id="{prefix}-{m.group(1)}"', s)
    s = re.sub(r"<table>", '<div class="tw"><table>', s)
    s = s.replace("</table>", "</table></div>")
    # one card per h2 section; anything before the first h2 is the tab's lead
    parts = re.split(r"(?=<h2 )", s)
    out = []
    for p in parts:
        if p.strip():
            out.append('<section class="card">' + p + "</section>")
    return "\n".join(out)

A = prep((SRC / "A.html").read_text(encoding="utf-8"), "a")
B = prep((SRC / "B.html").read_text(encoding="utf-8"), "b")

page = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex">
<title>GDSH BLĐ Report</title>
<style>{css}{EXTRA_CSS}</style>
</head>
<body>
<div class="wrap">
<section class="card">
  <div class="meta">Kính gửi HĐQT, Chủ tịch và BLĐ · Người lập: Ty Truong, Thường trực KSNB &amp; QTRR · 26/09/2026 · Số liệu đến 31/08, công nợ đến 21/09</div>
  <h1>Báo cáo GDSH gửi BLĐ</h1>
  <p><strong>Bản B</strong> là bản gửi BLĐ: bức tranh tổng thể ở trang đầu, độ tin cậy của từng số liệu ghi bằng chữ, mỗi vấn đề có một giải pháp tương ứng. <strong>Bản A</strong> giữ lại để đối chiếu, theo đúng cấu trúc file Ngọc tổng hợp (mục lục I–IV + Phụ lục). Bản tóm lược: <a href="../brief/">GDSH Board Brief</a>.</p>
  <div class="tabs" role="tablist" aria-label="Chọn bản">
    <button role="tab" id="t-b" aria-controls="panel-b" aria-selected="true" data-tab="b">Bản B · Gửi BLĐ</button>
    <button role="tab" id="t-a" aria-controls="panel-a" aria-selected="false" data-tab="a">Bản A · Đối chiếu (theo file của Ngọc)</button>
  </div>
</section>
<div class="panel" id="panel-b" role="tabpanel" aria-labelledby="t-b">
{B}
</div>
<div class="panel" id="panel-a" role="tabpanel" aria-labelledby="t-a" hidden>
{A}
</div>
<div class="foot">Báo cáo nội bộ · noindex</div>
</div>
<script>
(function(){{
  var tabs=document.querySelectorAll('.tabs button'), panels={{a:document.getElementById('panel-a'),b:document.getElementById('panel-b')}};
  function show(k,push){{
    tabs.forEach(function(t){{t.setAttribute('aria-selected',t.dataset.tab===k?'true':'false')}});
    panels.a.hidden=k!=='a'; panels.b.hidden=k!=='b';
    try{{localStorage.setItem('gdsh-review-tab2',k)}}catch(e){{}}
    if(push)history.replaceState(null,'','#ban-'+k);
  }}
  document.addEventListener('click',function(e){{
    var el=e.target.closest('[data-tab]'); if(!el)return;
    e.preventDefault(); show(el.dataset.tab,true); window.scrollTo(0,0);
  }});
  var h=location.hash.replace('#ban-',''), k=(h==='a'||h==='b')?h:null;
  if(!k){{try{{k=localStorage.getItem('gdsh-review-tab2')}}catch(e){{}}}}
  show(k==='a'?'a':'b',false);
}})();
</script>
</body>
</html>
"""
(ROOT / "review" / "index.html").write_text(page, encoding="utf-8")
print("wrote review/index.html", len(page))
