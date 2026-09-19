# -*- coding: utf-8 -*-
"""
GDSH — trích số liệu từ file Excel "BC KT Tình hình Sử dụng Ngân sách <MM.YYYY>.xlsx".
Bám theo NHÃN (sheet TH) và MÃ DÒNG (sheet Báo cáo DT-CP), không hardcode số dòng.
Trả về dict cho generator. Có guard đối chiếu; sai cấu trúc -> raise (Action fail, KHÔNG xuất số bậy).
"""
import openpyxl

def _num(x):
    return float(x) if isinstance(x, (int, float)) else 0.0

def _rows(ws):
    return list(ws.iter_rows(values_only=True))

def _find_section(rows, marker):
    for i, r in enumerate(rows):
        for c in r[:3]:
            if isinstance(c, str) and marker in c:
                return i
    raise ValueError(f"Không thấy section '{marker}' trong sheet TH")

def _row_by_label(rows, start, end, col_idx, label):
    # nhãn có thể ở cột A(0) hoặc B(1) tùy dòng -> quét cả hai
    for i in range(start, min(end, len(rows))):
        for ci in (0, 1):
            c = rows[i][ci] if len(rows[i]) > ci else None
            if isinstance(c, str) and c.strip().startswith(label):
                return rows[i]
    raise ValueError(f"Không thấy dòng nhãn bắt đầu '{label}'")

def extract(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
    TH = _rows(wb['TH'])
    DC = _rows(wb['Báo cáo DT-CP'])

    # ---------- HEADLINES từ sheet TH ----------
    # Section B (LÃI/LỖ HOẠT ĐỘNG): cột C(2)=KH, H(7)=T08 Cộng, K(10)=Lũy kế 31/08 Cộng
    bB = _find_section(TH, 'LÃI / LỖ HOẠT ĐỘNG')
    bC = _find_section(TH, 'DÒNG TIỀN')
    dt   = _row_by_label(TH, bB, bC, 1, 'Doanh thu')
    cogs = _row_by_label(TH, bB, bC, 1, 'Giá vốn')
    opex = _row_by_label(TH, bB, bC, 1, 'Chi phí vận hành')
    net  = _row_by_label(TH, bB, bC, 1, 'Lỗ/lãi')
    KHc, T08c, LKc = 2, 7, 10           # cột trong section B
    H = dict(
        dt_kh=_num(dt[KHc]),   dt_t08=_num(dt[T08c]),   dt_lk=_num(dt[LKc]),
        cogs_kh=_num(cogs[KHc]),                         cogs_lk=_num(cogs[LKc]),
        opex_kh=_num(opex[KHc]),                         opex_lk=_num(opex[LKc]),
        net_kh_stated=_num(net[KHc]),                    net_lk=_num(net[LKc]),
        plan_t3k_net=_num(net[3]),                       # cột D(3)=NGÂN SÁCH T03-08 (mốc lỗ KH kỳ)
        lk31_07_net=_num(net[4]),                        # cột E(4)=Lũy kế 31/07 (điểm áp chót #5)
    )
    # Section A (ĐẦU TƯ TÀI SẢN) -> CAPEX: TỔNG, cột C(2)=KH, J(9)=Lũy kế 31/08 Cộng
    aA = _find_section(TH, 'ĐẦU TƯ TÀI SẢN')
    capex = _row_by_label(TH, aA, bB, 0, 'TỔNG')
    H['capex_kh']=_num(capex[2]); H['capex_lk']=_num(capex[9])
    # Section C (DÒNG TIỀN) -> Lỗ/lãi dòng tiền: cột C(2)=KH, K(10)=Lũy kế 31/08 Cộng
    cf = _row_by_label(TH, bC, len(TH), 1, 'Lỗ/lãi dòng tiền')
    H['cf_kh']=_num(cf[2]); H['cf_lk']=_num(cf[10])

    # ---------- CHI TIẾT từ Báo cáo DT-CP (cột D(3)=KH năm, O(14)=Lũy kế 31/08 trong NS) ----------
    by_ma = {}
    for r in DC:
        ma = r[0]
        if isinstance(ma, str) and ma.strip():
            by_ma[ma.strip()] = r
    def d(ma):  # KH năm
        return _num(by_ma[ma][3]) if ma in by_ma else 0.0
    def o(ma):  # Lũy kế 31/08 (trong NS)
        return _num(by_ma[ma][14]) if ma in by_ma else 0.0

    # Doanh thu theo sản phẩm (#3) + giá vốn theo sản phẩm (#4)
    PROD = [  # (nhãn, mã doanh thu, mã giá vốn)
        ("Tiếng Anh (HĐ Anh)", "I.A.1", "II.A.1"),
        ("Trại hè",            "I.A.2", "II.A.2"),
        ("Học Văn hóa",        "I.A.3", "II.A.3"),
        ("Robotics",           "I.A.4", "II.A.4"),
        ("Trải nghiệm",        "I.A.5", "II.A.5"),
        ("Thi IELTS",          "I.A.6", "II.A.6"),
        ("Tài liệu",           "I.B.1", "II.A.7"),
    ]
    products = [dict(label=lab, rev_kh=d(mr), rev_lk=o(mr), cogs_kh=d(mc), cogs_lk=o(mc))
                for lab, mr, mc in PROD]

    # Cơ cấu OPEX (#2): dòng có tên + "Khác" = tổng OPEX (TH cộng) − các dòng có tên
    NAMED = [  # (nhãn, list mã dòng cộng lại)
        ("Nhân sự",              ["II.B.1"]),
        ("Khai trương",          ["II.C"]),
        ("Điện nước",            ["II.B.7"]),
        ("Nhà công vụ",          ["II.B.3"]),
        ("Giao tế tiếp khách",   ["II.B.10"]),
        ("KH & PB CCDC",         ["II.B.21", "II.B.22"]),
        ("Marketing",            ["II.B.15"]),
        ("Phí dịch vụ mặt bằng", ["II.B.23"]),
    ]
    opex_named = []
    for lab, mas in NAMED:
        opex_named.append(dict(label=lab, kh=sum(d(m) for m in mas), lk=sum(o(m) for m in mas)))
    khac_kh = H['opex_kh'] - sum(x['kh'] for x in opex_named)
    khac_lk = H['opex_lk'] - sum(x['lk'] for x in opex_named)
    opex_named.append(dict(label="Khác", kh=khac_kh, lk=khac_lk))

    # ---------- GUARD đối chiếu ----------
    problems = []
    # (a) mốc Kế hoạch khớp tờ trình 27/05: DT_KH − COGS_KH − OPEX_KH = −6.285.486.642 (±5đ)
    plan_anchor = H['dt_kh'] - H['cogs_kh'] - H['opex_kh']
    if abs(plan_anchor - (-6_285_486_642)) > 5:
        problems.append(f"PLAN ANCHOR lệch: {plan_anchor:,.0f} (mong đợi −6.285.486.642)")
    # (b) đẳng thức P&L thực (cột K): net_lk = DT_lk − COGS_lk − OPEX_lk (±5đ)
    calc_net = H['dt_lk'] - H['cogs_lk'] - H['opex_lk']
    if abs(calc_net - H['net_lk']) > 5:
        problems.append(f"P&L THỰC lệch: {calc_net:,.0f} vs net_lk {H['net_lk']:,.0f}")
    # (c) Khác không âm bất thường (cho phép hơi lệch do ngoài NS gộp vào)
    if khac_lk < -1_000_000:
        problems.append(f"OPEX 'Khác' thực âm bất thường: {khac_lk:,.0f}")
    if problems:
        raise ValueError("GUARD FAIL — cấu trúc file có thể đã đổi:\n  - " + "\n  - ".join(problems))

    return dict(headline=H, products=products, opex=opex_named)


if __name__ == "__main__":
    import sys, json
    D = extract(sys.argv[1])
    H = D['headline']
    f = lambda x: f"{x:,.0f}"
    print("== HEADLINE (TH sheet, cột Cộng) ==")
    for k in ("dt_kh","dt_lk","dt_t08","cogs_kh","cogs_lk","opex_kh","opex_lk","net_lk","capex_kh","capex_lk","cf_kh","cf_lk","plan_t3k_net","lk31_07_net"):
        print(f"  {k:16} = {f(H[k])}")
    print("== SẢN PHẨM (rev_kh / rev_lk / cogs_kh / cogs_lk) ==")
    for p in D['products']:
        print(f"  {p['label']:20} {f(p['rev_kh']):>15} {f(p['rev_lk']):>13} {f(p['cogs_kh']):>15} {f(p['cogs_lk']):>13}")
    print("== OPEX cơ cấu (kh / lk) ==")
    for x in D['opex']:
        print(f"  {x['label']:22} {f(x['kh']):>15} {f(x['lk']):>13}")
    print("GUARD: OK (không lỗi)")
