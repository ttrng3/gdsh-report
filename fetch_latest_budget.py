# -*- coding: utf-8 -*-
# Tải file BC ngân sách MỚI NHẤT từ Google Drive bằng SERVICE ACCOUNT (chỉ đọc).
#   Yêu cầu: GOOGLE_APPLICATION_CREDENTIALS trỏ tới file JSON key của service account.
#   Tùy chọn: GDSH_FOLDER_ID = ID thư mục chứa file (nếu có -> chỉ tìm trong thư mục đó).
# Xuất: budget.xlsx (cạnh script) + in "PERIOD=MM/YYYY" ra stdout (Action đọc để đặt env).
import os, re, sys, io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
KEY = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "sa.json")
FOLDER = os.environ.get("GDSH_FOLDER_ID", "").strip()

def main():
    creds = service_account.Credentials.from_service_account_file(
        KEY, scopes=["https://www.googleapis.com/auth/drive.readonly"])
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)

    q = ("name contains 'Ngân sách' and mimeType='%s' and trashed=false" % XLSX_MIME)
    if FOLDER:
        q += " and '%s' in parents" % FOLDER
    res = svc.files().list(q=q, orderBy="modifiedTime desc", pageSize=50,
                           fields="files(id,name,modifiedTime)",
                           supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = [f for f in res.get("files", []) if not f["name"].startswith("~$")]
    if not files:
        sys.exit("FETCH FAIL: không thấy file 'Ngân sách *.xlsx' service account đọc được "
                 "(kiểm tra đã share thư mục cho email service account chưa; GDSH_FOLDER_ID nếu dùng).")

    # chọn file có kỳ MM.YYYY lớn nhất trong tên; nếu không parse được thì theo modifiedTime
    def period_key(name):
        m = re.search(r'(\d{2})[.\-_](\d{4})', name)
        return (int(m.group(2)), int(m.group(1))) if m else (0, 0)
    files.sort(key=lambda f: (period_key(f["name"]), f["modifiedTime"]), reverse=True)
    top = files[0]
    m = re.search(r'(\d{2})[.\-_](\d{4})', top["name"])
    period = f"{m.group(1)}/{m.group(2)}" if m else ""

    req = svc.files().get_media(fileId=top["id"], supportsAllDrives=True)
    buf = io.FileIO(os.path.join(os.path.dirname(os.path.abspath(__file__)), "budget.xlsx"), "wb")
    dl = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
    buf.close()
    sys.stderr.write(f"Đã tải: {top['name']} (kỳ {period})\n")
    print(f"PERIOD={period}")

if __name__ == "__main__":
    main()
