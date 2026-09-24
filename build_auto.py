# -*- coding: utf-8 -*-
# ============================================================================
# GDSH Dashboard — AUTONOMOUS generator (chạy trong GitHub Actions).
#   Đọc thẳng file Excel ngân sách -> tính lại -> xuất index.html.
#   Lớp SỐ LIỆU (chart #1–#7, KPI, bảng P&L, số trong note) = tự động từ Excel.
#   Lớp PHÁN QUYẾT (verdict, đề xuất phê duyệt, #8 kịch bản, Stage-Gate, 5 câu hỏi)
#     = judgment/judgment.html, do người rà soát sửa tay mỗi kỳ. Script chỉ ĐỌC
#     file đó (và điền các số {placeholder} từ kỳ hiện tại), KHÔNG tự viết lại.
#   Guard đối chiếu nằm trong gdsh_extract.extract(): sai cấu trúc -> raise -> Action fail.
# Chạy:  GDSH_XLSX=<file.xlsx> GDSH_PERIOD=08/2026 python3 build_auto.py
#
# Test / parity hooks (the workflow sets none of these):
#   GDSH_EXTRACT_JSON  extract()-shaped JSON to use instead of an Excel file
#   GDSH_OUT_DIR       write index.html, history.json, data/ here instead of the repo
#   GDSH_TODAY         dd/mm/yyyy to stamp as the build date
#   GDSH_JUDGMENT      judgment file to read (default judgment/judgment.html)
# ============================================================================
import io, os, re, json, glob, datetime
from gdsh_render import *          # palette, page_style, esc, vnd, tr, bn, grouped_bars, two_donuts, pctbars, marginbars, line2, vbars, loss_bars

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.environ.get("GDSH_OUT_DIR") or HERE
TODAY = os.environ.get("GDSH_TODAY") or datetime.date.today().strftime('%d/%m/%Y')

# ---------- lớp phán quyết (judgment layer) ----------
JUDGMENT_PATH = os.environ.get("GDSH_JUDGMENT") or os.path.join(HERE, "judgment", "judgment.html")
_JBLOCKS = ("review_asof", "verdict", "scenarios", "scenario_sub", "stage_gate", "questions")
def load_judgment(path):
    # Blocks start at a line `<!--@name-->` and run to the next; text before the
    # first marker (the instructions comment) is ignored.
    txt = io.open(path, encoding="utf-8").read()
    parts = re.split(r'^<!--@(\w+)-->[ \t]*\n', txt, flags=re.M)
    J = {parts[i]: parts[i+1].strip("\n") for i in range(1, len(parts), 2)}
    missing = [b for b in _JBLOCKS if b not in J]
    if missing:
        raise ValueError(f"{path}: thiếu block {missing}")
    return J
J = load_judgment(JUDGMENT_PATH)
REVIEW_ASOF = J["review_asof"].strip()   # ngày người rà soát duyệt lớp phán quyết gần nhất

# ---------- formatters hiển thị (dấu phẩy thập phân VN) ----------
def d1(x):  return f"{x:.1f}".replace(".", ",")            # 71.5 -> "71,5"
def d0(x):  return f"{x:.0f}"
def pctv(x):return d1(x) + "%"                             # -> "71,5%"
def sgn1(x):return (f"{x:+.1f}".replace(".", ",").replace("-", "−")) + "%"   # -> "+74,8%" / "−22,7%"
def sgn0(x):return (f"{x:+.0f}".replace("-", "−")) + "%"                       # -> "−195%"
def mult(x):return d1(x) + "×"
def dong(x):return f"{abs(x):,.0f}".replace(",", ".")      # đủ số đồng, không dấu: 7.977.640.000
def neg_dong(x): return f"({dong(x)})"                     # số âm trong ngoặc
def mns(x): return str(x).replace("-", "−")          # -200 -> "−200"
def ty2(x): return f"{x/1e9:.2f} tỷ".replace(".", ",").replace("-", "−")   # luôn theo tỷ: -0.541e9 -> "−0,54 tỷ"
def thou(x):return f"{x:,.0f}".replace(",", ".")           # 1945 -> "1.945"

# ---------- nạp dữ liệu ----------
xlsx = os.environ.get("GDSH_XLSX")
_fixture = os.environ.get("GDSH_EXTRACT_JSON")
if _fixture:
    D = json.load(open(_fixture, encoding="utf-8"))
else:
    from gdsh_extract import extract
    if not xlsx:
        cands = sorted(glob.glob(os.path.join(HERE, "*Ngân sách*.xlsx")) + glob.glob("*Ngân sách*.xlsx") + glob.glob("budget_sample.xlsx"))
        xlsx = cands[-1] if cands else "budget_sample.xlsx"
    D = extract(xlsx)
H, PRODUCTS, OPEX = D["headline"], D["products"], D["opex"]

PERIOD = os.environ.get("GDSH_PERIOD")
if not PERIOD:
    m = re.search(r'(\d{2})[.\-_](\d{4})', os.path.basename(xlsx or ""))
    PERIOD = f"{m.group(1)}/{m.group(2)}" if m else "08/2026"
_mm = int(PERIOD.split("/")[0]); _tN = f"T{_mm}"; _tPrev = f"T{_mm-1}"
_endday = (datetime.date(int(PERIOD.split('/')[1]), _mm, 1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
ASOF = _endday.strftime("%d/%m/%Y")     # ví dụ 31/08/2026
_left = max(12 - _mm, 1)                # số tháng còn lại trong năm

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
surge_need= (dt_kh-dt_lk)/_left
surge_x   = surge_need/dt_t08
dt_pct    = dt_lk/dt_kh*100
cf_pct    = H['cf_lk']/H['cf_kh']*100

# ---------- #1 bốn khối ----------
c1 = grouped_bars(
    [("Kế hoạch cả năm / Budget",[dt_kh,cogs_kh,opex_kh,H["capex_kh"]]),
     (f"Thực hiện {ASOF} / Actual",[dt_lk,cogs_lk,opex_lk,H["capex_lk"]])],
    ["Doanh thu|Revenue","Giá vốn|COGS","Chi phí VH|OPEX","CAPEX|CAPEX"], [PLAN,ACT])

# ---------- #2 cơ cấu OPEX ----------
# Categorical fills from gdsh_render.CAT — never the semantic four.
_C=[h for h,_ in CAT]
_COL2={"Nhân sự":_C[0],"Marketing":_C[1],"KH & PB CCDC":_C[2],
       "Khai trương":_C[3],"Nhà công vụ":_C[4],"Phí dịch vụ mặt bằng":_C[5],
       "Điện nước":_C[6],"Giao tế tiếp khách":_C[7],"Khác":_C[8]}
_cats2=sorted([(x["label"], x["kh"]/opex_kh*100, x["lk"]/opex_lk*100, _COL2.get(x["label"],_C[8])) for x in OPEX], key=lambda c:-c[1])
c2=two_donuts(_cats2, opex_kh, opex_lk)
def _op(lbl):  return next(x for x in OPEX if x["label"]==lbl)
_ns,_mkt,_khpb,_ktr,_mb = _op("Nhân sự"),_op("Marketing"),_op("KH & PB CCDC"),_op("Khai trương"),_op("Phí dịch vụ mặt bằng")

# ---------- #3 % đạt theo sản phẩm ----------
_rev = sorted(PRODUCTS, key=lambda p:-(p["rev_lk"]/p["rev_kh"] if p["rev_kh"] else 0))
c3 = pctbars([(p["label"], (p["rev_lk"]/p["rev_kh"]*100 if p["rev_kh"] else 0),
               (ACC if p["rev_kh"] and p["rev_lk"]/p["rev_kh"]*100>=5 else CRIT), vnd(p["rev_kh"])) for p in _rev])
_ex = _rev[:2]   # hai ví dụ đầu bảng cho note

# ---------- #4 biên gộp: hai panel cạnh nhau, KH (trái) và TH (phải) ----------
def mkh(p): return (p["rev_kh"]-p["cogs_kh"])/p["rev_kh"]*100 if p["rev_kh"] else 0
def mth(p): return (p["rev_lk"]-p["cogs_lk"])/p["rev_lk"]*100 if p["rev_lk"] else None
M4_KH = (-40, 80)      # trục panel KH (%): ngoài khoảng -> kẹp, đánh dấu ★
M4_TH = (-200, 20)     # trục panel TH (%)
_pm = sorted(PRODUCTS, key=lambda p:-mkh(p))
_n_rev = sum(1 for p in PRODUCTS if p["rev_lk"]>0)
c4 = ('<div class="two">'
      + marginbars([(p["label"], mkh(p)) for p in _pm], "Biên KH / Budget margin", *M4_KH, pos=PLAN, neg=CRIT)
      + marginbars([(p["label"], mth(p)) for p in _pm], "Biên TH / Actual margin", *M4_TH, pos=ACT, neg=ACT)
      + '</div>')
def _P(name): return next(p for p in PRODUCTS if p["label"].startswith(name))
_rob,_th,_ta = _P("Robotics"),_P("Trại hè"),_P("Tiếng Anh")

# ---------- #5 lỗ P&L lũy kế (history.json giữ chuỗi tháng) ----------
HIST_PATH=os.path.join(OUT_DIR,"history.json")
try:
    hist=json.load(open(HIST_PATH if os.path.exists(HIST_PATH) else os.path.join(HERE,"history.json"),encoding="utf-8"))
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
c6=vbars([(f"Run-rate {_tN}|Thực hiện · Actual", round(dt_t08/1e6), ACT),
          (f"Cần T{_mm+1}–T12|đạt KH · to hit budget", round(surge_need/1e6), PLAN)],
         note=f"ĐVT: triệu/tháng · gap {mult(surge_x)}")

# ---------- #7 hòa vốn ----------
c7=vbars([(f"Thực thu {ASOF[:5]}|Actual", round(dt_lk/1e9,2), ACT),
          ("Kế hoạch năm|Budget", round(dt_kh/1e9,2), PLAN),
          ("Hòa vốn|Breakeven", round(breakeven/1e9,2), WARN)], note="ĐVT: tỷ VNĐ")

# ---------- #8 kịch bản CẢ NĂM (JUDGMENT — judgment/judgment.html, block `scenarios`) ----------
_SCN_COL={"blue":PLAN,"red":ACT,"orange":WARN}
def _scenario(line):
    lab,val,col=[x.strip() for x in line.split(";")]
    return (lab, int(net_kh) if val.lower()=="plan" else int(val), _SCN_COL[col.lower()])
c8=loss_bars([_scenario(l) for l in J["scenarios"].splitlines() if l.strip()])

# ---------- số cho lớp phán quyết: {placeholder} trong judgment/judgment.html ----------
_summer = _P("Trại hè")
PLACEHOLDERS = dict(
    dt_pct=pctv(dt_pct), cf_lk=vnd(H['cf_lk']), cf_lk_abs=bn(abs(H['cf_lk'])).replace(".", ","),
    cf_pct=d0(cf_pct), months=_mm-2, surge_x=mult(surge_x), surge_need_tr=thou(surge_need/1e6),
    t08_tr=d0(dt_t08/1e6), tN=_tN, mm=_mm, be_mult=mult(be_mult), capex_lk=vnd(H['capex_lk']),
    net_kh_1=d1(net_kh/1e9).replace("-", "−"),
    summer_share=d0(_summer["rev_lk"]/dt_lk*100),
    en_gp_kh=ty2(_ta["rev_kh"]-_ta["cogs_kh"]), en_cogs_kh=vnd(_ta["cogs_kh"]), en_rev_kh=vnd(_ta["rev_kh"]),
    payroll_pct=d0(_ns["lk"]/_ns["kh"]*100),
    ns_kh_share=pctv(_ns["kh"]/opex_kh*100), ns_lk_share=pctv(_ns["lk"]/opex_lk*100),
    payroll_rev_pct=d0(_ns["kh"]/dt_kh*100), rev_per_wage=d1(dt_lk/_ns["lk"]*100),
)
def jblock(name): return J[name].format_map(PLACEHOLDERS)

# ---------- KPI ----------
def kpi(v,l,cls=""): return f'<div class="kpi {cls}"><div class="kv">{v}</div><div class="kl">{esc(l)}</div></div>'
kpis=(kpi(pctv(dt_pct),"DT / kế hoạch năm · Revenue vs budget","crit")
     +kpi(vnd(net_lk),f"Lỗ P&L lũy kế · Cumulative P&L loss ({ASOF[:5]})","crit")
     +kpi(vnd(H["cf_lk"]),f"Đốt tiền mặt · Cash burn ({d0(cf_pct)}% NS)","crit")
     +kpi(mult(surge_x),"Cú hích Q4 cần có · Q4 surge needed","warn")
     +kpi(mult(be_mult),"Bội số DT để hòa vốn · Breakeven multiple","warn")
     +kpi(sgn1(mkh(_ta)),"Biên gộp Tiếng Anh (KH) · English gross margin","crit"))

def card(title, sub, body, tag=None):
    tagh=f'<span class="tag">{esc(tag)}</span>' if tag else ''
    subh=f'<p class="sub">{esc(sub)}</p>' if sub else ''
    return f'<section class="card"><div class="chd"><h2>{esc(title)}</h2>{tagh}</div>{subh}{body}</section>'

PER = PERIOD.replace("/", ".")     # "08.2026" cho tiêu đề

HTML=f"""<!DOCTYPE html>
<html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Thẩm định Giáo dục Sông Hồng</title>
{page_style()}</head>
<body><div class="wrap">

<div class="masthead">
<h1>Thẩm định đầu tư — Giáo dục Sông Hồng ECO</h1>
<div class="meta"><b>Investment review — Song Hong Education</b> · trong hệ sinh thái Eco Central Park (Vinh) · Báo cáo cho HĐQT / Ban TGĐ · Board / ExCo brief · số liệu lũy kế {ASOF} (kỳ {PER})<br>
Nguồn / Source: Tờ trình KHKD 27/05/2026 + Báo cáo sử dụng ngân sách {PER}. Số liệu tính lại tự động bằng code từ file nguồn (cập nhật {TODAY}) · figures auto-recomputed from source by code; phán quyết &amp; kịch bản rà soát thủ công gần nhất / judgment layer last reviewed {REVIEW_ASOF}.</div>
</div>

<div class="verdict">
{jblock("verdict")}
</div>

<div class="legend-note"><b>Quy ước màu / Colour key (mọi biểu đồ · all charts):</b> <span class="sw" style="background:var(--accent)"></span> xanh = <b>Kế hoạch / Budget</b>, <span class="sw" style="background:var(--critical-fill)"></span> đỏ = <b>Thực hiện lũy kế / Actual to {ASOF}</b>. Ngân sách và thực chi/thực thu đặt cạnh nhau (hai biểu đồ riêng) để đối chiếu trực tiếp · budget and actual shown as separate side-by-side charts.</div>

<div class="kpirow">{kpis}</div>

{card("1 · Kế hoạch vs Thực hiện — 4 khối lớn / Budget vs Actual — the big four",f"Cột xanh = Kế hoạch cả năm, cột đỏ = Thực hiện lũy kế {ASOF}, đặt cạnh nhau theo từng khối · green = full-year budget, red = actual to date.",c1+f'<div class="note crit"><b>Đọc / Read:</b> doanh thu thực mới <b>{pctv(dt_pct)}</b> kế hoạch năm, nhưng chi phí vận hành đã tiêu <b>{pctv(opex_lk/opex_kh*100)}</b> và CAPEX <b>{pctv(H["capex_lk"]/H["capex_kh"]*100)}</b>. Nền chi phí nạp gần đủ trước khi doanh thu kịp lên — cột đỏ (thực) lùn hẳn so cột xanh (kế hoạch) ở Doanh thu, nhưng gần bằng ở Chi phí VH. <i>Cost base almost fully loaded ({pctv(opex_lk/opex_kh*100)} of OPEX budget spent) while revenue is only {pctv(dt_pct)} of plan.</i></div>',tag="Budget vs Actual")}

{card("2 · Cơ cấu chi phí vận hành: Kế hoạch vs Thực hiện / OPEX mix: Budget vs Actual",f"Hai vòng tròn cạnh nhau — cơ cấu NGÂN SÁCH (Kế hoạch) và cơ cấu THỰC CHI (Thực hiện {ASOF}). Tổng OPEX ghi ngay dưới mỗi vòng: Kế hoạch {vnd(opex_kh)} · Thực hiện {vnd(opex_lk)} ({pctv(opex_lk/opex_kh*100)} ngân sách). Mỗi lát = tỷ trọng dòng đó trong tổng của cột; chú giải bên phải đọc dòng-theo-dòng: KH% → TH%.",c2+f'<div class="note crit"><b>Trôi cơ cấu:</b> lát nhân sự phình từ {pctv(_ns["kh"]/opex_kh*100)} lên <b>{pctv(_ns["lk"]/opex_lk*100)}</b> tổng chi trong khi marketing gần biến mất ({pctv(_mkt["kh"]/opex_kh*100)} → <b>{pctv(_mkt["lk"]/opex_lk*100)}</b>) và KH&amp;PB {pctv(_khpb["kh"]/opex_kh*100)} → {pctv(_khpb["lk"]/opex_lk*100)}. Thực chi bị khóa vào lương nhiều hơn cả kế hoạch vốn đã nặng lương, và bỏ đói kênh tạo cầu. Khai trương chiếm {pctv(_ktr["lk"]/opex_lk*100)} (chi một lần, dồn đầu kỳ).</div><div class="note"><b>Tín hiệu kiểm soát (tiến độ ngân sách):</b> marketing mới giải ngân {pctv(_mkt["lk"]/_mkt["kh"]*100)} ngân sách năm; phí dịch vụ mặt bằng {pctv(_mb["lk"]/_mb["kh"]*100 if _mb["kh"] else 0)} — chi phí cố định còn tiềm ẩn, chưa phát sinh; khai trương đã dùng {pctv(_ktr["lk"]/_ktr["kh"]*100 if _ktr["kh"] else 0)}.</div>',tag="Cơ cấu phân bổ")}

{card("3 · Tỷ lệ hoàn thành doanh thu theo sản phẩm / Revenue completion by product",f"% doanh thu thực thu lũy kế {ASOF} so với kế hoạch cả năm của từng sản phẩm. Cột KH DT bên phải là doanh thu kế hoạch năm của mỗi sản phẩm — mẫu số của tỷ lệ %.",c3+f'<div class="note"><b>Cách tính:</b> % đạt = doanh thu thực thu lũy kế ÷ doanh thu kế hoạch cả năm của sản phẩm (cột phải). VD {_ex[0]["label"]} {vnd(_ex[0]["rev_lk"])} ÷ {vnd(_ex[0]["rev_kh"])} = <b>{pctv(_ex[0]["rev_lk"]/_ex[0]["rev_kh"]*100)}</b>; {_ex[1]["label"]} {vnd(_ex[1]["rev_lk"])} ÷ {vnd(_ex[1]["rev_kh"])} = <b>{pctv(_ex[1]["rev_lk"]/_ex[1]["rev_kh"]*100)}</b>. Tổng DT KH năm = {vnd(dt_kh)}; thực thu {vnd(dt_lk)} = <b>{pctv(dt_pct)}</b>.</div><div class="note crit"><b>Đọc:</b> mọi dòng dưới 20% ngân sách của chính nó; hai động cơ định kỳ Robotics ({pctv(_rob["rev_lk"]/_rob["rev_kh"]*100)}) và Văn hóa ({pctv(_P("Học Văn")["rev_lk"]/_P("Học Văn")["rev_kh"]*100)}) gần như chưa chạy; nguồn thu ít ỏi lại dồn vào Trại hè (một lần) và Trải nghiệm (giá thấp). Tổng thực thu = {pctv(dt_pct)} kế hoạch năm.</div>',tag="% đạt kế hoạch")}

{card("4 · Biên lợi nhuận gộp theo sản phẩm / Gross margin by product",f"Hai biểu đồ cạnh nhau: trái = biên gộp KẾ HOẠCH (thiết kế cả năm), phải = biên gộp THỰC lũy kế {ASOF}. {_n_rev}/{len(PRODUCTS)} sản phẩm đã phát sinh doanh thu; sản phẩm chưa phát sinh ghi 'chưa phát sinh / n/a'. · Left = budget (design) margin, right = actual margin.",c4+f'<div class="note"><b>Cách tính:</b> biên gộp = (doanh thu − giá vốn) ÷ doanh thu. Cột KH lấy số thiết kế cả năm; cột TH lấy thực thu/thực chi lũy kế {ASOF}. VD Robotics KH <b>{sgn1(mkh(_rob))}</b> nhưng TH <b>{sgn0(mth(_rob))}</b>; Trại hè KH <b>{sgn1(mkh(_th))}</b> vs TH <b>{sgn0(mth(_th))}</b>; Tiếng Anh KH <b>{sgn1(mkh(_ta))}</b> vs TH <b>{sgn0(mth(_ta))}</b>.</div><div class="note crit"><b>Đọc:</b> mọi biên THỰC đều âm sâu — kể cả Robotics vốn là cỗ máy lợi nhuận theo thiết kế ({sgn1(mkh(_rob))}). Nguyên nhân: giá vốn/nhượng quyền/vận hành dồn trước trong khi doanh thu chưa lên, nên mỗi đồng bán ra đang lỗ trực tiếp. Đây là bài toán THỜI ĐIỂM (chưa đủ quy mô) chồng lên bài toán CẤU TRÚC (Tiếng Anh HĐ Anh lỗ gộp cả theo thiết kế). <i>Timing problem (sub-scale) on top of a structural one (English is loss-making even by design).</i> ★ = kẹp trần để đọc được (Biên TH kẹp {mns(M4_TH[0])}%, Biên KH kẹp {mns(M4_KH[0])}%), giá trị thật ghi cạnh.</div>',tag="Budget vs Actual")}

{card("5 · Lỗ P&L lũy kế: Kế hoạch vs Thực hiện / Cumulative P&L loss",f"Lỗ thực {vnd(net_lk)} so mốc ngân sách {vnd(E)} — đọc cùng doanh thu và chi phí đều dưới kế hoạch. Đường đỏ (thực) so đường xanh đứt (kế hoạch phân bổ đều) từng tháng.",c5)}

<div class="two">
{card("6 · Run-rate doanh thu / Revenue run-rate: needed vs actual",f"Doanh thu/tháng cần cho các tháng cuối năm để đạt kế hoạch, so với doanh thu thực {_tN}.",c6+f'<div class="note crit"><b>{mult(surge_x)} so với con số nào:</b> {_tN} chỉ thu <b>{d0(dt_t08/1e6)} triệu</b> (run-rate hiện tại, từ cột tháng đó của file ngân sách). Để đạt kế hoạch doanh thu năm, phần còn lại phải thu (chia đều) <b>{d0(surge_need/1e6)} triệu/tháng</b>. Chia ra: {d0(surge_need/1e6)} ÷ {d0(dt_t08/1e6)} = <b>{mult(surge_x)}</b> — phải nhân doanh thu tháng lên gần {d0(surge_x)} lần, ngay và giữ suốt. Chưa có hợp đồng/đăng ký nào làm bằng cho cú nhảy này.</div>',tag=mult(surge_x))}
{card("7 · Điểm hòa vốn / Breakeven: Actual vs Budget vs Breakeven","Ba mốc doanh thu: thực thu, kế hoạch năm, và mức phải đạt để hòa vốn (không còn lỗ).",c7+f'<div class="note crit"><b>{mult(be_mult)} so với con số nào:</b> điểm hòa vốn = tổng OPEX {vnd(opex_kh)} ÷ biên đóng góp {pctv(cm*100)} ≈ <b>{vnd(breakeven)}</b>. So kế hoạch doanh thu năm {vnd(dt_kh)} → <b>{mult(be_mult)}</b>; so thực thu {vnd(dt_lk)} → <b>{d0(be_mult_a)}×</b>. Nghĩa là ngay cả khi đạt 100% kế hoạch, đơn vị VẪN lỗ — muốn hết lỗ phải có doanh thu gấp {d1(be_mult)} lần chính kế hoạch. Biên đóng góp {pctv(cm*100)} = biên gộp kế hoạch ({vnd(gp_kh)} ÷ {vnd(dt_kh)}); giả định toàn bộ OPEX là chi phí cố định.</div>',tag="Cấu trúc")}
</div>

{card("8 · Stress test lỗ CẢ NĂM 2026 / Full-year 2026 loss stress test",jblock("scenario_sub"),c8+f'<div class="note"><b>Ghi chú kỳ:</b> lỗ thực lũy kế ({vnd(net_lk)}) KHÔNG đặt cạnh đây để tránh so lệch kỳ (lũy kế vs cả năm) — nó nằm ở biểu đồ #5. Kịch bản là lớp phán quyết, rà soát thủ công gần nhất {REVIEW_ASOF}.</div>')}

{card("Bảng P&L chuẩn hóa / Standardized P&L — Kế hoạch vs Thực hiện", "Số đầy đủ theo đồng (VND); (số trong ngoặc) = âm. Full figures in đồng (VND); (parentheses) = negative.", f'''
<div style="overflow-x:auto"><table><thead><tr><th>Chỉ tiêu / Metric</th><th class="n">Kế hoạch 2026 / Budget</th><th class="n">TH đến {ASOF} / Actual</th><th class="n">% đạt / of budget</th></tr></thead><tbody>
<tr><td>Doanh thu / Revenue</td><td class="n">{dong(dt_kh)}</td><td class="n">{dong(dt_lk)}</td><td class="n neg">{pctv(dt_pct)}</td></tr>
<tr><td>Giá vốn / COGS</td><td class="n">{dong(cogs_kh)}</td><td class="n">{dong(cogs_lk)}</td><td class="n">{pctv(cogs_lk/cogs_kh*100)}</td></tr>
<tr><td>Lợi nhuận gộp / Gross profit</td><td class="n">{dong(gp_kh)}</td><td class="n neg">{neg_dong(gp_lk)}</td><td class="n neg">biên âm / negative</td></tr>
<tr><td>Chi phí vận hành / OPEX</td><td class="n">{dong(opex_kh)}</td><td class="n">{dong(opex_lk)}</td><td class="n">{pctv(opex_lk/opex_kh*100)}</td></tr>
<tr><td>EBITDA</td><td class="n neg">{neg_dong(ebitda_kh)}</td><td class="n neg">{neg_dong(ebitda_lk)}</td><td class="n">–</td></tr>
<tr><td><b>Lợi nhuận ròng / Net profit</b></td><td class="n neg">{neg_dong(net_kh)}</td><td class="n neg">{neg_dong(net_lk)}</td><td class="n">–</td></tr>
<tr><td>Dòng tiền thuần / Net cash flow</td><td class="n neg">{neg_dong(H['cf_kh'])}</td><td class="n neg">{neg_dong(H['cf_lk'])}</td><td class="n">{d0(cf_pct)}% NS</td></tr>
<tr><td>CAPEX giải ngân / CAPEX</td><td class="n">{dong(H['capex_kh'])}</td><td class="n">{dong(H['capex_lk'])}</td><td class="n">{pctv(H['capex_lk']/H['capex_kh']*100)}</td></tr>
</tbody></table></div>
<div class="note crit"><b>Đọc nhanh / Bottom line:</b> đơn vị đã tiêu {d0(cf_pct)}% ngân sách tiền mặt và {d0(_ns['lk']/_ns['kh']*100)}% quỹ lương cả năm, nhưng mới thu {pctv(dt_pct)} doanh thu. Lỗ gộp âm nghĩa là bán một đồng đang lỗ trực tiếp, trước cả lương và mặt bằng. <i>Spent {d0(cf_pct)}% of the cash budget and {d0(_ns['lk']/_ns['kh']*100)}% of the annual payroll for {pctv(dt_pct)} of revenue; negative gross margin means each đồng sold loses money before payroll or rent.</i></div>
''')}

{card("Phán quyết & Cổng kiểm soát 90 ngày / Verdict & 90-day Stage-Gate", None, f'''
{jblock("stage_gate")}
<p style="color:var(--muted);font-size:12px;margin:12px 0 0">Lớp phán quyết (verdict, kịch bản #8, cổng, câu hỏi) rà soát thủ công gần nhất {REVIEW_ASOF} — số liệu biểu đồ ở trên tự cập nhật theo kỳ ngân sách mới.</p>
''')}

{card("5 câu hỏi 'xoáy' cho buổi bảo vệ kế hoạch / 5 hard questions for the plan defense", "Lớp người duyệt — bộ câu hỏi để ép quản lý ra bằng chứng, không phải lời hứa. Reviewer layer: forces evidence, not promises.", chr(10)+jblock("questions"))}

<div class="foot">Báo cáo phân tích nội bộ · số liệu kỳ {PER} (lũy kế {ASOF}) · sinh tự động {TODAY}. Con số tài chính tính lại bằng code từ file ngân sách nguồn, có guard đối chiếu mốc Kế hoạch (tờ trình 27/05) và đẳng thức P&L. #2 cơ cấu OPEX (dòng có tên từ Báo cáo DT-CP, "Khác" = tổng OPEX − các dòng đã nêu); #3 % thực thu/KH năm; #4 biên gộp KH vs TH (kẹp trần −160%); #8 kịch bản cả năm là lớp phán quyết (rà soát thủ công). Không phải tư vấn pháp lý/thuế.</div>

</div></body></html>"""

_OUT=os.path.join(OUT_DIR,"index.html")
with io.open(_OUT,"w",encoding="utf-8") as f:
    f.write(HTML)

# Machine-readable clock beside the page. index.html carries the period only in
# prose, which a watchdog cannot parse; this sidecar is what tells the freshness
# check whether a new budget period was actually published, as opposed to the
# job merely having run. Written on every build.
_META = {
    "generatedUtc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "asof": ASOF,
    "period": PERIOD,
    "reviewAsOf": REVIEW_ASOF,
    "pages": "https://ttrng3.github.io/gdsh-report/",
    "repo": "https://github.com/ttrng3/gdsh-report",
}
os.makedirs(os.path.join(OUT_DIR, "data"), exist_ok=True)
with io.open(os.path.join(OUT_DIR, "data", "index.json"), "w", encoding="utf-8") as f:
    json.dump(_META, f, ensure_ascii=False, indent=1)

print("written", len(HTML), "chars ·", "kỳ", PER, "· lũy kế", ASOF, "· phán quyết rà soát", REVIEW_ASOF)
