# GDSH Dashboard — 100% Autonomy (GitHub Actions + Drive service account)

Pipeline chạy **hoàn toàn trong repo**, không cần Mac, không cần Cowork:
mỗi tháng GitHub Actions đọc file ngân sách mới nhất từ Google Drive (service account **chỉ đọc**),
tính lại bằng `build_auto.py` (có guard đối chiếu), rồi commit `index.html` → GitHub Pages tự build.

- Số liệu (chart #1–#7, KPI, bảng P&L, số trong note) **tự cập nhật** từ Excel.
- Phán quyết / kịch bản #8 / Stage-Gate / 5 câu hỏi = **lớp người duyệt**, chỉ đổi khi Ty rà soát (sửa `REVIEW_ASOF` trong `build_auto.py`). Script không tự viết lại phán quyết.

## Các file
| File | Vai trò |
|---|---|
| `.github/workflows/publish.yml` | Lịch chạy (17 hằng tháng) + nút chạy tay |
| `fetch_latest_budget.py` | Tải file ngân sách mới nhất từ Drive (service account) |
| `build_auto.py` | Sinh `index.html` từ Excel (+ cập nhật `history.json`) |
| `gdsh_extract.py` | Trích số theo Mã dòng + **guard đối chiếu** |
| `gdsh_render.py` | Hàm vẽ biểu đồ SVG + bảng màu (Ty Standard) |
| `history.json` | Chuỗi lỗ P&L lũy kế từng tháng cho chart #5 |
| `requirements.txt` | Thư viện Python |

## SETUP MỘT LẦN (Ty làm — ~10 phút)

### 1. Tạo service account chỉ-đọc trên Google Cloud
1. Vào https://console.cloud.google.com → tạo (hoặc chọn) một Project.
2. **APIs & Services → Library** → tìm **Google Drive API** → **Enable**.
3. **APIs & Services → Credentials → Create credentials → Service account**.
   - Đặt tên (vd `gdsh-reader`), Create → Done (không cần cấp role nào).
4. Mở service account vừa tạo → tab **Keys → Add key → Create new key → JSON** → tải file JSON về.
   - Mở file JSON, copy dòng `"client_email": "gdsh-reader@...iam.gserviceaccount.com"` — đây là **email service account**.

### 2. Share thư mục ngân sách cho service account (chỉ Viewer)
- Trên Google Drive, mở thư mục **`01 Eco Central Park - ECP/ECP - Eco Sông Hồng`** (thư mục chứa file `...BC KT Tình hình Sử dụng Ngân sách MM.YYYY.xlsx`).
- Share → dán **email service account** ở trên → quyền **Viewer** → Send.
- (Không share cả Drive; chỉ đúng thư mục này.)

### 3. Nạp key vào GitHub (secret)
- Repo `ttrng3/gdsh-report` → **Settings → Secrets and variables → Actions → New repository secret**:
  - Name: `GDRIVE_SA_KEY` — Value: **dán TOÀN BỘ nội dung file JSON key**.
- (Tùy chọn, khuyến nghị) thêm secret `GDSH_FOLDER_ID` = ID thư mục ngân sách
  (lấy từ URL thư mục Drive: `drive.google.com/drive/folders/<ID>`) — để pipeline chỉ tìm trong đúng thư mục đó.

### 4. Bật GitHub Pages (nếu chưa)
- **Settings → Pages → Source: Deploy from a branch → Branch: `main` / root**. (Trang: https://ttrng3.github.io/gdsh-report/)

### 5. Chạy thử
- Tab **Actions → GDSH monthly publish → Run workflow**. Xong → xem `index.html` được commit và trang Pages cập nhật.
- Nếu file ngân sách đổi cấu trúc, guard trong `gdsh_extract.py` sẽ **làm job đỏ (fail)** kèm lý do, KHÔNG xuất số sai.

## Vận hành hằng tháng
Không phải làm gì. Kế toán bỏ file ngân sách tháng mới vào thư mục Drive như thường; ngày 17 pipeline tự chạy.
Muốn chạy ngay: Actions → Run workflow.

## Khi muốn đổi phán quyết / kịch bản / câu hỏi
Sửa phần literal trong `build_auto.py` (khối `c8` và các block `Stage-Gate` / `5 câu hỏi`) + cập nhật `REVIEW_ASOF`, commit. Đó là lớp người-duyệt, cố ý tách khỏi phần tự động.

## Bảo mật (ghi cho KSNB)
- Service account **chỉ đọc**, chỉ thấy **đúng một thư mục** được share; không đụng được phần còn lại của Drive.
- Key nằm trong **GitHub encrypted secret** của repo Ty kiểm soát; không in ra log; chỉ Ty (owner) thêm được workflow.
- Chỉ file dashboard (vốn đã public trên Pages) là công khai. Số liệu ngân sách gốc không rời repo/secret.
