# Bộ test phân quyền (public / private theo cấp độ)

Mục tiêu: kiểm tra chatbot chỉ trả lời từ tài liệu mà người hỏi được phép xem.

Toàn bộ nội dung được **giả lập**: số hiệu văn bản, con số và tên người đều tự đặt.
Đã tìm thử một số chuỗi đặc thù với `site:iuh.edu.vn` (3186/QĐ-ĐHCN, 10.380.000, H5.0214, 27% tín chỉ trực tuyến) và không có kết quả trùng.

## Thành phần

| File | Nội dung |
|---|---|
| `catalog.json` | 20 tài liệu: phòng ban, `is_public`, `min_access_level`, chủ đề |
| `files/*.pdf` | 20 PDF tiếng Việt, mỗi file 7–9 trang |
| `specs/*.json` | Nguồn của từng PDF, gồm cả 3 câu hỏi kèm đáp án và evidence nguyên văn |
| `questions.jsonl` | 60 câu hỏi (3 câu mỗi tài liệu) |
| `accounts.csv` | 12 tài khoản test và GUEST |
| `cases.csv` | 780 case (13 tài khoản × 60 câu): 438 ANSWER / 342 DENY |
| `tools/` | `render_pdf.py`, `seed_accounts.py`, `build_cases.py` |

## Ma trận

| | L0 | L1 | L2 | L3 | L4 | L5 |
|---|---|---|---|---|---|---|
| BM_CONG_NGHE_PHAN_MEM | A0 | A1 | A2 | A3 | A4 | A5 |
| BM_KE_TOAN | B0 | B1 | B2 | B3 | B4 | B5 |

- **Tài liệu public P1–P8** (học vụ cấp trường): mọi người đều xem được, kể cả khách.
- **Tài liệu private:** chỉ xem được khi phòng ban trùng chính xác và cấp độ của tài khoản lớn hơn hoặc bằng `min_access_level` của tài liệu. Quy tắc này giống `unisage-agent/app/rag/vectorstore/qdrant_store.py`.
- **Tài khoản:** `TST-CNPM-L0..L5` và `TST-KT-L0..L5`, mật khẩu đặt trong `.env` của gateway (`TEST_ACCOUNT_PASSWORD`, không commit), role USER. Mỗi tài khoản chỉ thuộc một bộ môn (là phòng ban lá).

Ví dụ: `TST-KT-L3` được trả lời P1–P8 và B0–B3. Tài khoản này phải bị từ chối với B4, B5 và toàn bộ A*.

## Chạy lại

```bash
python3 tools/seed_accounts.py            # tạo tài khoản qua gateway (bỏ qua nếu đã tồn tại)
python3 tools/build_cases.py              # sinh lại questions.jsonl / accounts.csv / cases.csv
<venv có reportlab>/bin/python tools/render_pdf.py specs/*.json --out files
```

Khi upload tài liệu lên hệ thống, đặt phòng ban và cấp độ theo `catalog.json`:
- P1–P8: `is_public=true`, danh mục HOC_VU.
- A*/B*: `is_public=false`, phòng ban là bộ môn tương ứng, `min_access_level` lấy theo catalog.
