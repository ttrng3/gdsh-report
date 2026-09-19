# -*- coding: utf-8 -*-
# ============================================================================
# GDSH Dashboard — AUTONOMOUS generator (chạy trong GitHub Actions).
#   Đọc thẳng file Excel ngân sách -> tính lại -> xuất index.html.
#   Lớp SỐ LIỆU (chart #1–#7, KPI, bảng P&L, số trong note) = tự động từ Excel.
#   Lớp PHÁN QUYẾT (verdict, #8 kịch bản, Stage-Gate, 5 câu hỏi) = do người rà soát,
#     giữ nguyên như bản người duyệt gần nhất (REVIEW_ASOF), script KHÔNG tự viết lại.
#   Guard đối chiếu nằm trong gdsh_extract.extract(): sai cấu trúc -> raise -> Action fail.
# Chạy:  GDSH_XLSX=<file.xlsx> GDSH_PERIOD=08/2026 python3 build_auto.py
# ============================================================================
import io, os, re, json, glob, datetime
from gdsh_render import *          # palette, esc, vnd, tr, bn, grouped_bars, two_donuts, pctbars, gmargin, line2, vbars, loss_bars
from gdsh_extract import extract

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = datetime.date.today().strftime('%d/%m/%Y')
REVIEW_ASOF = "18/09/2026"        # kỳ người rà soát phán quyết/kịch bản gần nhất (cập nhật khi Ty duyệt lại)

# ---------- formatters hiển thị (dấu phẩy thập phân VN) ----------
def d1(x):  return f"{x:.1f}".replace(".", ",")            # 71.5 -> "71,5"
def d0(x):  return f"{x:.0f}"
def pctv(x):return d1(x) + "%"                             # -> "71,5%"
def sgn1(x):return (f"{x:+.1f}".replace(".", ",").replace("-", "−")) + "%"   # -> "+74,8%" / "−22,7%"
def sgn0(x):return (f"{x:+.0f}".replace("-", "−")) + "%"                       # -> "−195%"
def mult(x):return d1(x) + "×"

# ---------- nạp dữ liệu ----------
xlsx = os.environ.get("GDSH_XLSX")
if not xlsx:
    cands = sorted(glob.glob(os.path.join(HERE, "*Ngân sách*.xlsx")) + glob.glob("*Ngân sách*.xlsx") + glob.glob("budget_sample.xlsx"))
    xlsx = cands[-1] if cands else "budget_sample.xlsx"
D = extract(xlsx)
H, PRODUCTS, OPEX = D["headline"], D["products"], D["opex"]

PERIOD = os.environ.get("GDSH_PERIOD")
if not PERIOD:
    m = re.search(r'(\d{2})[.\-_](\d{4})', os.path.basename(xlsx))
    PERIOD = f"{m.group(1)}/{m.group(2)}" if m else "08/2026"
_mm = int(PERIOD.split("/")[0]); _tN = f"T{_mm}"; _tPrev = f"T{_mm-1}"
_endday = (datetime.date(int(PERIOD.split('/')[1]), _mm, 1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
ASOF = _endday.strftime("%d/%m/%Y")     # ví dụ 31/08/2026

# ---------- shortcut ----------
dt_kh,dt_lk,dt_t08 = H["dt_kh"],H["dt_lk"],H["dt_t08"]
cogs_kh,cogs_lk    = H["cogs_kh"],H["cogs_lk"]
opex_kh,opex_lk    = H["opex_kh"],H["opex_lk"]
net_lk             = H["net_lk"]; net_kh = dt_kh - cogs_kh - opex_kh
gp_kh, gp_lk       = dt_kh-cogs_kh, dt_lk-cogs_lk
da = next((x for x in OPEX if x["label"]=="KH & PB CCDC"), {"kh":0,"lk":0})   # khấu hao + phân bổ CCDC
ebitda_kh, ebitda_lk = net_kh + da["kh"], net_lk + da["lk"]
cm = gp_kh/dt_kh
breakeven = opex_kh/cm
be_mult   = breakeven/dt_kh
be_mult_a = breakeven/dt_lk
surge_need= (dt_kh-dt_lk)/4
surge_x   = surge_need/dt_t08

# ---------- #1 bốn khối ----------
c1 = grouped_bars(
    [("Kế hoạch cả năm",[dt_kh,cogs_kh,opex_kh,H["capex_kh"]]),
     (f"Thực hiện đến {ASOF}",[dt_lk,cogs_lk,opex_lk,H["capex_lk"]])],
    ["Doanh thu","Giá vốn","Chi phí VH","CAPEX"], [PLAN,ACT])

# ---------- #2 cơ cấu OPEX ----------
_COL2={"Nhân sự":"#0F6E52","Marketing":"#9A6B00","KH & PB CCDC":"#7BA895",
       "Khai trương":"#C6864F","Nhà công vụ":"#8F9B8A","Phí dịch vụ mặt bằng":"#B5876A",
       "Điện nước":"#9AA0A6","Giao tế tiếp khách":"#C9C7BE","Khác":"#D8D5CB"}
_cats2=sorted([(x["label"], x["kh"]/opex_kh*100, x["lk"]/opex_lk*100, _COL2.get(x["label"],"#D8D5CB")) for x in OPEX], key=lambda c:-c[1])
c2=two_donuts(_cats2, opex_kh, opex_lk)
def _op(lbl):  return next(x for x in OPEX if x["label"]==lbl)
_ns,_mkt,_khpb,_ktr,_mb = _op("Nhân sự"),_op("Marketing"),_op("KH & PB CCDC"),_op("Khai trương"),_op("Phí dịch vụ mặt bằng")

# ---------- #3 % đạt theo sản phẩm ----------
_rev = sorted(PRODUCTS, key=lambda p:-(p["rev_lk"]/p["rev_kh"] if p["rev_kh"] else 0))
c3 = pctbars([(p["label"], (p["rev_lk"]/p["rev_kh"]*100 if p["rev_kh"] else 0),
               (ACC if p["rev_kh"] and p["rev_lk"]/p["rev_kh"]*100>=5 else CRIT), vnd(p["rev_kh"])) for p in _rev])
_ex = _rev[:2]   # hai ví dụ đầu bảng cho note

# ---------- #4 biên gộp KH vs TH (chỉ SP đã phát sinh doanh thu) ----------
def mkh(p): return (p["rev_kh"]-p["cogs_kh"])/p["rev_kh"]*100 if p["rev_kh"] else 0
def mth(p): return (p["rev_lk"]-p["cogs_lk"])/p["rev_lk"]*100 if p["rev_lk"] else None
_pm = sorted([p for p in PRODUCTS if p["rev_lk"]>0], key=lambda p:-mkh(p))
c4 = gmargin([(p["label"], mkh(p), mth(p)) for p in _pm])
def _P(name): return next(p for p in PRODUCTS if p["label"].startswith(name))
_rob,_th,_ta = _P("Robotics"),_P("Trại hè"),_P("Tiếng Anh")

# ---------- #5 lỗ P&L lũy kế (history.json giữ chuỗi tháng) ----------
HIST_PATH=os.path.join(HERE,"history.json")
try:
    hist=json.load(open(HIST_PATH,encoding="utf-8"))
except Exception:
    hist={}
hist.setdefault("pnl_cum",{})
# seed các tháng lịch sử nếu file trống (giá trị đã kiểm chứng tới 08/2026)
for k,v in {"T3":-434948164,"T4":-956038009,"T5":-1582632204,"T6":-2630990305}.items():
    hist["pnl_cum"].setdefault(k,v)
hist["pnl_cum"][_tPrev]=int(H["lk31_07_net"])
hist["pnl_cum"][_tN]=int(net_lk)
json.dump(hist,open(HIST_PATH,"w",encoding="utf-8"),ensure_ascii=False,indent=1)
_months=[f"T{n}" for n in range(3,_mm+1)]
act_cum=[(m,hist["pnl_cum"][m]) for m in _months if m in hist["pnl_cum"]]
E=H["plan_t3k_net"]; n=len(act_cum)
plan_cum=[(act_cum[i][0], E*(i+1)/n) for i in range(n)]
c5=line2(act_cum, plan_cum)

# ---------- #6 run-rate ----------
c6=vbars([(f"Run-rate {_tN}|(Thực hiện)", round(dt_t08/1e6), ACT),
          (f"Cần {('T'+str(_mm+1))}–T12|(đạt KH năm)", round(surge_need/1e6), PLAN)],
         note=f"ĐVT: triệu/tháng (làm tròn) · chênh {mult(surge_x)}")

# ---------- #7 hòa vốn ----------
c7=vbars([(f"DT thực {ASOF[:5]}", round(dt_lk/1e9,2), ACT),
          ("DT kế hoạch năm", round(dt_kh/1e9,2), PLAN),
          ("DT hòa vốn", round(breakeven/1e9,2), WARN)], note="ĐVT: tỷ VNĐ")

# ---------- #8 kịch bản CẢ NĂM (JUDGMENT — giữ như bản người duyệt REVIEW_ASOF) ----------
c8=loss_bars([
    ("Lạc quan | (đúng KH)", int(net_kh), PLAN),
    ("Cơ sở | (giữ chi phí)", -8_418_236_732, ACT),
    ("Cắt OPEX 20% | (Cơ sở)", -6_627_951_881, WARN),
    ("Xấu | (Q4 ~10%, giữ CP)", -8_684_830_494, ACT)])

# ---------- KPI ----------
def kpi(v,l,cls=""): return f'<div class="kpi {cls}"><div class="kv">{v}</div><div class="kl">{esc(l)}</div></div>'
kpis=(kpi(pctv(dt_lk/dt_kh*100),"Doanh thu / kế hoạch năm","crit")
     +kpi(vnd(net_lk),f"Lỗ P&L lũy kế {ASOF[:5]}","crit")
     +kpi(vnd(H["cf_lk"]),f"Đốt tiền mặt ({d0(H['cf_lk']/H['cf_kh']*100)}% NS)","crit")
     +kpi(mult(surge_x),"Cú hích Q4 cần có","warn")
     +kpi(mult(be_mult),"DT cần để hòa vốn","warn")
     +kpi(sgn1(mkh(_ta)),"Biên gộp Tiếng Anh","crit"))

def card(title, sub, body, tag=None):
    tagh=f'<span class="tag">{esc(tag)}</span>' if tag else ''
    subh=f'<p class="sub">{esc(sub)}</p>' if sub else ''
    return f'<section class="card"><div class="chd"><h2>{esc(title)}</h2>{tagh}</div>{subh}{body}</section>'

PER = PERIOD.replace("/", ".")     # "08.2026" cho tiêu đề

HTML=f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thẩm định Giáo dục Sông Hồng</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Be+Vietnam+Pro:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{{--paper:{PAPER};--surface:{SURF};--sunk:{SUNK};--ink:{INK};--ink-soft:{INKS};--muted:{MUT};--rule:{RULE};--accent:{ACC};--accent-bg:{ACCBG};--critical:{CRIT};--warning:{WARN}}}
*{{box-sizing:border-box}}
body{{background:#FFFFFF;color:var(--ink);font-family:'Be Vietnam Pro',system-ui,sans-serif;margin:0;line-height:1.55;font-size:15px}}
.wrap{{max-width:1000px;margin:0 auto;padding:32px 20px 64px}}
h1{{font-family:'Playfair Display',serif;font-weight:700;font-size:30px;line-height:1.2;margin:0 0 6px}}
h2{{font-family:'Playfair Display',serif;font-weight:600;font-size:19px;margin:0}}
.masthead{{border-bottom:2px solid var(--ink);padding-bottom:18px;margin-bottom:8px}}
.meta{{color:var(--muted);font-size:13px;margin-top:8px}}
.verdict{{background:var(--accent-bg);border:1px solid var(--accent);border-radius:8px;padding:18px 20px;margin:22px 0}}
.verdict .lead{{font-family:'Playfair Display',serif;font-size:20px;color:var(--accent);font-weight:600;margin:0 0 6px}}
.verdict p{{margin:6px 0 0}}
.legend-note{{font-size:12.5px;color:var(--ink-soft);margin:14px 0 0;padding:9px 13px;background:var(--surface);border:1px solid var(--rule);border-radius:6px}}
.sw{{display:inline-block;width:11px;height:11px;border-radius:2px;vertical-align:baseline;margin:0 3px 0 8px}}
.kpirow{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}}
.kpi{{background:var(--surface);border:1px solid var(--rule);border-radius:8px;padding:14px 16px}}
.kpi.crit{{border-left:3px solid var(--critical)}} .kpi.warn{{border-left:3px solid var(--warning)}}
.kv{{font-size:26px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.1}}
.kpi.crit .kv{{color:var(--critical)}} .kpi.warn .kv{{color:var(--warning)}}
.kl{{color:var(--muted);font-size:12.5px;margin-top:4px}}
.card{{background:var(--paper);border:1px solid var(--rule);border-radius:8px;padding:20px 22px;margin:16px 0}}
.chd{{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:2px}}
.tag{{font-size:11px;color:var(--accent);border:1px solid var(--accent);border-radius:20px;padding:2px 10px;white-space:nowrap}}
.sub{{color:var(--ink-soft);font-size:13.5px;margin:4px 0 14px}}
.note{{background:var(--surface);border-left:3px solid var(--warning);padding:10px 14px;border-radius:0 6px 6px 0;font-size:13.5px;color:var(--ink-soft);margin-top:14px}}
.note.crit{{border-left-color:var(--critical)}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:4px}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--rule)}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
thead th{{background:var(--surface);color:var(--ink-soft);font-weight:600}}
.neg{{color:var(--critical)}}
.q{{border:1px solid var(--rule);border-radius:8px;padding:14px 16px 14px 46px;margin:10px 0;position:relative;background:var(--surface);counter-increment:q}}
.qbox{{counter-reset:q}}
.q:before{{content:counter(q);position:absolute;left:14px;top:14px;width:22px;height:22px;background:var(--accent);color:#fff;border-radius:50%;text-align:center;line-height:22px;font-size:13px;font-weight:600}}
.q .qh{{font-weight:600}}
.qm{{color:var(--muted);font-size:12.5px;display:block;margin-top:4px}}
.qm b{{color:var(--ink-soft);font-weight:600}}
.gate td:first-child{{font-weight:600;white-space:nowrap;color:var(--accent)}}
.gate td{{vertical-align:top}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.foot{{color:var(--muted);font-size:12px;margin-top:28px;border-top:1px solid var(--rule);padding-top:14px}}
@media (max-width:720px){{.kpirow{{grid-template-columns:1fr 1fr}}.two{{grid-template-columns:1fr}}h1{{font-size:24px}}}}
@media print{{body{{font-size:12px}}.wrap{{max-width:none;padding:0}}.card,.kpi,.verdict,.note,.q,.legend-note{{background:#fff!important;break-inside:avoid}}.kv{{color:var(--ink)!important}}:root{{--muted:#222;--ink-soft:#222}}.tag{{color:#222;border-color:#222}}}}
</style></head>
<body><div class="wrap">

<div class="masthead">
<h1>Thẩm định đầu tư — Giáo dục Sông Hồng ECO</h1>
<div class="meta">Trong hệ sinh thái Eco Central Park (Vinh) · Báo cáo cho HĐQT / Ban TGĐ · Số liệu lũy kế {ASOF} (kỳ {PER})<br>
Nguồn: Tờ trình KHKD 27/05/2026 + Báo cáo sử dụng ngân sách {PER}. Số liệu tính lại tự động bằng code từ file nguồn (cập nhật {TODAY}); phán quyết &amp; kịch bản rà soát thủ công gần nhất {REVIEW_ASOF}.</div>
</div>

<div class="verdict">
<p class="lead">Phán quyết: KHÔNG mở rộng — CHỈ duy trì có điều kiện &amp; tái cấu trúc</p>
<p>Đơn vị chưa chứng minh cầu ở quy mô nền: doanh thu = <b>{pctv(dt_lk/dt_kh*100)} kế hoạch năm</b>, lỗ gộp âm, đốt <b>{vnd(H['cf_lk'])}</b> tiền mặt sau {_mm-2} tháng. Toàn bộ kế hoạch đặt cược vào cú hích cuối năm gấp <b>{mult(surge_x)}</b> run-rate hiện tại. Cơ chế đúng là <b>rót vốn theo cổng kiểm soát 90 ngày</b>, không phê duyệt trọn gói.</p>
</div>

<div class="legend-note"><b>Quy ước màu (mọi biểu đồ):</b> <span class="sw" style="background:{PLAN}"></span> xanh = <b>Kế hoạch</b>, <span class="sw" style="background:{ACT}"></span> đỏ = <b>Thực hiện lũy kế {ASOF}</b>. Mọi biểu đồ đặt cạnh nhau ngân sách vs thực chi/thực thu để đối chiếu trực tiếp.</div>

<div class="kpirow">{kpis}</div>

{card("1 · Kế hoạch vs Thực hiện — 4 khối lớn","Doanh thu gần chạm sàn trong khi chi phí vận hành đã nạp gần đủ.",c1)}

{card("2 · Cơ cấu chi phí vận hành: Kế hoạch vs Thực hiện",f"Hai vòng tròn cạnh nhau — cơ cấu NGÂN SÁCH (Kế hoạch) và cơ cấu THỰC CHI (Thực hiện {ASOF}). Tổng OPEX ghi ngay dưới mỗi vòng: Kế hoạch {vnd(opex_kh)} · Thực hiện {vnd(opex_lk)} ({pctv(opex_lk/opex_kh*100)} ngân sách). Mỗi lát = tỷ trọng dòng đó trong tổng của cột; chú giải bên phải đọc dòng-theo-dòng: KH% → TH%.",c2+f'<div class="note crit"><b>Trôi cơ cấu:</b> lát nhân sự phình từ {pctv(_ns["kh"]/opex_kh*100)} lên <b>{pctv(_ns["lk"]/opex_lk*100)}</b> tổng chi trong khi marketing gần biến mất ({pctv(_mkt["kh"]/opex_kh*100)} → <b>{pctv(_mkt["lk"]/opex_lk*100)}</b>) và KH&amp;PB {pctv(_khpb["kh"]/opex_kh*100)} → {pctv(_khpb["lk"]/opex_lk*100)}. Thực chi bị khóa vào lương nhiều hơn cả kế hoạch vốn đã nặng lương, và bỏ đói kênh tạo cầu. Khai trương chiếm {pctv(_ktr["lk"]/opex_lk*100)} (chi một lần, dồn đầu kỳ).</div><div class="note"><b>Tín hiệu kiểm soát (tiến độ ngân sách):</b> marketing mới giải ngân {pctv(_mkt["lk"]/_mkt["kh"]*100)} ngân sách năm; phí dịch vụ mặt bằng {pctv(_mb["lk"]/_mb["kh"]*100 if _mb["kh"] else 0)} — chi phí cố định còn tiềm ẩn, chưa phát sinh; khai trương đã dùng {pctv(_ktr["lk"]/_ktr["kh"]*100 if _ktr["kh"] else 0)}.</div>',tag="Cơ cấu phân bổ")}

{card("3 · Tỷ lệ hoàn thành doanh thu theo sản phẩm",f"% doanh thu thực thu lũy kế {ASOF} so với kế hoạch cả năm của từng sản phẩm. Cột KH DT bên phải là doanh thu kế hoạch năm của mỗi sản phẩm — mẫu số của tỷ lệ %.",c3+f'<div class="note"><b>Cách tính:</b> % đạt = doanh thu thực thu lũy kế ÷ doanh thu kế hoạch cả năm của sản phẩm (cột phải). VD {_ex[0]["label"]} {vnd(_ex[0]["rev_lk"])} ÷ {vnd(_ex[0]["rev_kh"])} = <b>{pctv(_ex[0]["rev_lk"]/_ex[0]["rev_kh"]*100)}</b>; {_ex[1]["label"]} {vnd(_ex[1]["rev_lk"])} ÷ {vnd(_ex[1]["rev_kh"])} = <b>{pctv(_ex[1]["rev_lk"]/_ex[1]["rev_kh"]*100)}</b>. Tổng DT KH năm = {vnd(dt_kh)}; thực thu {vnd(dt_lk)} = <b>{pctv(dt_lk/dt_kh*100)}</b>.</div><div class="note crit"><b>Đọc:</b> mọi dòng dưới 20% ngân sách của chính nó; hai động cơ định kỳ Robotics ({pctv(_rob["rev_lk"]/_rob["rev_kh"]*100)}) và Văn hóa ({pctv(_P("Học Văn")["rev_lk"]/_P("Học Văn")["rev_kh"]*100)}) gần như chưa chạy; nguồn thu ít ỏi lại dồn vào Trại hè (một lần) và Trải nghiệm (giá thấp). Tổng thực thu = {pctv(dt_lk/dt_kh*100)} kế hoạch năm.</div>',tag="% đạt kế hoạch")}

{card("4 · Biên lợi nhuận gộp theo sản phẩm: Kế hoạch vs Thực hiện",f"Hai thanh mỗi sản phẩm đặt cạnh nhau: biên gộp KẾ HOẠCH (thiết kế, xanh) và biên gộp THỰC lũy kế {ASOF} (đỏ). Chỉ {len(_pm)} sản phẩm đã phát sinh doanh thu — sản phẩm chưa phát sinh không có biên thực.",c4+f'<div class="note"><b>Cách tính:</b> biên gộp = (doanh thu − giá vốn) ÷ doanh thu. Cột KH lấy số thiết kế cả năm; cột TH lấy thực thu/thực chi lũy kế {ASOF}. VD Robotics KH <b>{sgn1(mkh(_rob))}</b> nhưng TH <b>{sgn0(mth(_rob))}</b>; Trại hè KH <b>{sgn1(mkh(_th))}</b> vs TH <b>{sgn0(mth(_th))}</b>; Tiếng Anh KH <b>{sgn1(mkh(_ta))}</b> vs TH <b>{sgn0(mth(_ta))}</b>.</div><div class="note crit"><b>Đọc:</b> mọi biên THỰC đều âm sâu — kể cả Robotics vốn là cỗ máy lợi nhuận theo thiết kế ({sgn1(mkh(_rob))}). Nguyên nhân: giá vốn/nhượng quyền/vận hành dồn trước trong khi doanh thu chưa lên, nên mỗi đồng bán ra đang lỗ trực tiếp. Đây là bài toán THỜI ĐIỂM (chưa đủ quy mô) chồng lên bài toán CẤU TRÚC (Tiếng Anh HĐ Anh lỗ gộp cả theo thiết kế). ★ = kẹp trần −160% để đọc được, giá trị thật ghi cạnh.</div>',tag="Budget vs Actual")}

{card("5 · Lỗ P&L lũy kế: Kế hoạch vs Thực hiện",f"Lỗ thực {vnd(net_lk)} so mốc ngân sách {vnd(E)} — đọc cùng doanh thu và chi phí đều dưới kế hoạch. Đường đỏ (thực) so đường xanh đứt (kế hoạch phân bổ đều) từng tháng.",c5)}

<div class="two">
{card("6 · Run-rate doanh thu: Cần (KH) vs Thực (TH)",f"Doanh thu/tháng cần cho các tháng cuối năm để đạt kế hoạch, so với doanh thu thực {_tN}.",c6+f'<div class="note crit"><b>{mult(surge_x)} so với con số nào:</b> {_tN} chỉ thu <b>{d0(dt_t08/1e6)} triệu</b> (run-rate hiện tại, từ cột tháng đó của file ngân sách). Để đạt kế hoạch doanh thu năm, phần còn lại phải thu (chia đều) <b>{d0(surge_need/1e6)} triệu/tháng</b>. Chia ra: {d0(surge_need/1e6)} ÷ {d0(dt_t08/1e6)} = <b>{mult(surge_x)}</b> — phải nhân doanh thu tháng lên gần {d0(surge_x)} lần, ngay và giữ suốt. Chưa có hợp đồng/đăng ký nào làm bằng cho cú nhảy này.</div>',tag=mult(surge_x))}
{card("7 · Điểm hòa vốn: Thực vs Kế hoạch vs Hòa vốn","Ba mốc doanh thu: thực thu, kế hoạch năm, và mức phải đạt để hòa vốn (không còn lỗ).",c7+f'<div class="note crit"><b>{mult(be_mult)} so với con số nào:</b> điểm hòa vốn = tổng OPEX {vnd(opex_kh)} ÷ biên đóng góp {pctv(cm*100)} ≈ <b>{vnd(breakeven)}</b>. So kế hoạch doanh thu năm {vnd(dt_kh)} → <b>{mult(be_mult)}</b>; so thực thu {vnd(dt_lk)} → <b>{d0(be_mult_a)}×</b>. Nghĩa là ngay cả khi đạt 100% kế hoạch, đơn vị VẪN lỗ — muốn hết lỗ phải có doanh thu gấp {d1(be_mult)} lần chính kế hoạch. Biên đóng góp {pctv(cm*100)} = biên gộp kế hoạch ({vnd(gp_kh)} ÷ {vnd(dt_kh)}); giả định toàn bộ OPEX là chi phí cố định.</div>',tag="Cấu trúc")}
</div>

{card("8 · Stress test lỗ CẢ NĂM 2026: Kế hoạch vs Kịch bản","Bốn kịch bản trên cùng một cơ sở 12 tháng: Kế hoạch (Lạc quan, xanh) so với các kịch bản theo quỹ đạo thực. Giữ chi phí lỗ nặng hơn kế hoạch; chỉ cắt giảm mới kéo về vùng đã duyệt.",c8+f'<div class="note"><b>Ghi chú kỳ:</b> lỗ thực lũy kế ({vnd(net_lk)}) KHÔNG đặt cạnh đây để tránh so lệch kỳ (lũy kế vs cả năm) — nó nằm ở biểu đồ #5. Kịch bản là lớp phán quyết, rà soát thủ công gần nhất {REVIEW_ASOF}.</div>')}

{card("Bảng P&L chuẩn hóa — Kế hoạch vs Thực hiện", None, f'''
<table><thead><tr><th>Chỉ tiêu</th><th class="n">Kế hoạch 2026</th><th class="n">TH đến {ASOF}</th><th class="n">% đạt</th></tr></thead><tbody>
<tr><td>Doanh thu</td><td class="n">{vnd(dt_kh)}</td><td class="n">{vnd(dt_lk)}</td><td class="n neg">{pctv(dt_lk/dt_kh*100)}</td></tr>
<tr><td>Giá vốn (COGS)</td><td class="n">{vnd(cogs_kh)}</td><td class="n">{vnd(cogs_lk)}</td><td class="n">{pctv(cogs_lk/cogs_kh*100)}</td></tr>
<tr><td>Lợi nhuận gộp</td><td class="n">{vnd(gp_kh)}</td><td class="n neg">({vnd(abs(gp_lk))})</td><td class="n neg">biên âm</td></tr>
<tr><td>Chi phí vận hành</td><td class="n">{vnd(opex_kh)}</td><td class="n">{vnd(opex_lk)}</td><td class="n">{pctv(opex_lk/opex_kh*100)}</td></tr>
<tr><td>EBITDA</td><td class="n neg">({vnd(abs(ebitda_kh))})</td><td class="n neg">({vnd(abs(ebitda_lk))})</td><td class="n">–</td></tr>
<tr><td><b>Lợi nhuận ròng</b></td><td class="n neg">({vnd(abs(net_kh))})</td><td class="n neg">({vnd(abs(net_lk))})</td><td class="n">–</td></tr>
<tr><td>Dòng tiền thuần</td><td class="n neg">({vnd(abs(H['cf_kh']))})</td><td class="n neg">({vnd(abs(H['cf_lk']))})</td><td class="n">{d0(H['cf_lk']/H['cf_kh']*100)}% NS</td></tr>
<tr><td>CAPEX giải ngân</td><td class="n">{vnd(H['capex_kh'])}</td><td class="n">{vnd(H['capex_lk'])}</td><td class="n">{pctv(H['capex_lk']/H['capex_kh']*100)}</td></tr>
</tbody></table>
<div class="note crit"><b>Đọc nhanh:</b> đơn vị đã tiêu {d0(H['cf_lk']/H['cf_kh']*100)}% ngân sách tiền mặt và {d0(_ns['lk']/_ns['kh']*100)}% quỹ lương cả năm, nhưng mới thu {pctv(dt_lk/dt_kh*100)} doanh thu. Lỗ gộp âm nghĩa là bán một đồng đang lỗ trực tiếp, trước cả lương và mặt bằng.</div>
''')}

{card("Phán quyết & Cơ chế Cổng kiểm soát (Stage-Gate 90 ngày)", None, f'''
<p style="margin-top:0"><b>KHÔNG mở rộng.</b> Phê duyệt một giai đoạn <b>duy trì – tái cấu trúc 90 ngày</b>, vốn giải ngân theo <b>TRANCHE</b> gắn với ba cổng kiểm soát. Không giải ngân trọn gói; mỗi cổng là điều kiện bắt buộc để mở tranche kế; trượt cổng kích hoạt phương án thu hẹp. Không đóng cửa (CAPEX {vnd(H['capex_lk'])} là chi phí chìm, Robotics đã chứng minh biên, và tiện ích giáo dục hỗ trợ giá trị BĐS) — nhưng cũng không nuôi một mô hình chưa chứng minh cầu.</p>
<div style="overflow-x:auto"><table class="gate"><thead><tr><th>Cổng</th><th>Mục tiêu</th><th>Điều kiện KPI bắt buộc (đo được)</th><th>Mở khóa / Hệ quả</th></tr></thead><tbody>
<tr><td>G1<br>0–30 ngày</td><td>Tái cấu trúc nền chi phí</td><td>• Biên chế điều chỉnh theo số lớp thực, cam kết bằng văn bản kéo lỗ kịch bản Cơ sở cả năm về vùng đã duyệt (≤ mốc kế hoạch)<br>• Phương án Tiếng Anh HĐ Anh đã trình (tái đàm phán phí / định giá lại / thu hẹp) kèm ngưỡng học viên hòa vốn gộp</td><td>Đạt → mở <b>tranche 2</b>. Trượt → dừng, không rót thêm</td></tr>
<tr><td>G2<br>30–60 ngày</td><td>Chứng minh cầu thật</td><td>• Ngân sách tạo cầu nâng từ mức giải ngân hiện tại lên mức chốt; báo cáo phễu hàng tuần<br>• Số học viên khóa học TRẢ PHÍ (không tính lượt trải nghiệm) ≥ ngưỡng đầu năm học BLĐ chốt<br>• Run-rate DT tháng ≥ 3–4× tháng gần nhất, có hợp đồng/đăng ký làm bằng</td><td>Đạt → mở <b>tranche 3</b>. Trượt → thu hẹp</td></tr>
<tr><td>G3<br>60–90 ngày</td><td>Chứng minh mô hình</td><td>• Biên gộp toàn đơn vị <b>DƯƠNG</b><br>• Lỗ P&L quy năm về vùng kế hoạch<br>• Công suất lấp đầy khung giờ vàng đạt ngưỡng</td><td>Đạt cả 3 → xét <b>MỞ RỘNG</b> trên dữ liệu thật. Trượt → <b>DỪNG LỖ</b>, thu về lõi Robotics/STEM</td></tr>
</tbody></table></div>
<p style="color:var(--muted);font-size:12px;margin:12px 0 0">Lớp phán quyết (verdict, kịch bản #8, cổng, câu hỏi) rà soát thủ công gần nhất {REVIEW_ASOF} — số liệu biểu đồ ở trên tự cập nhật theo kỳ ngân sách mới.</p>
''')}

<div class="foot">Báo cáo phân tích nội bộ · số liệu kỳ {PER} (lũy kế {ASOF}) · sinh tự động {TODAY}. Con số tài chính tính lại bằng code từ file ngân sách nguồn, có guard đối chiếu mốc Kế hoạch (tờ trình 27/05) và đẳng thức P&L. #2 cơ cấu OPEX (dòng có tên từ Báo cáo DT-CP, "Khác" = tổng OPEX − các dòng đã nêu); #3 % thực thu/KH năm; #4 biên gộp KH vs TH (kẹp trần −160%); #8 kịch bản cả năm là lớp phán quyết (rà soát thủ công). Không phải tư vấn pháp lý/thuế.</div>

</div></body></html>"""

_OUT=os.path.join(HERE,"index.html")
with io.open(_OUT,"w",encoding="utf-8") as f:
    f.write(HTML)
print("written", len(HTML), "chars ·", "kỳ", PER, "· lũy kế", ASOF)
