---
language:
  - vi
pretty_name: UniSage IUH Dataset
task_categories:
  - question-answering
tags:
  - rag
  - evaluation
  - vietnamese
  - university
size_categories:
  - 1K<n<10K
configs:
  - config_name: questions
    data_files: official/questions.jsonl
    default: true
  - config_name: questions_review
    data_files: official/questions_review.csv
  - config_name: manifest
    data_files: official/manifest.csv
  - config_name: sources
    data_files: official/sources.csv
  - config_name: discovered
    data_files: official/discovered.csv
  - config_name: access_control_questions
    data_files: access-control/questions.jsonl
  - config_name: access_control_cases
    data_files: access-control/cases.csv
  - config_name: access_control_manifest
    data_files: access-control/manifest.csv
---

# UniSage IUH Dataset

Bộ dữ liệu phục vụ xây dựng và đánh giá hệ thống hỏi đáp RAG (UniSage Gateway) cho Trường Đại học Công nghiệp TP.HCM (IUH).
Gồm tài liệu PDF crawl từ các website của trường, tài liệu giả lập để test phân quyền, và các bộ câu hỏi đánh giá kèm đáp án, bằng chứng trích dẫn.

Repo có hai phần tách biệt:

| Thư mục | Nội dung |
|---|---|
| `official/` | Bộ dữ liệu chính thức: 1.875 PDF crawl từ web trường (1.031 tài liệu được chọn để ingest) và 565 câu hỏi. |
| `access-control/` | Bộ test phân quyền: 20 PDF giả lập (8 public về học vụ, 12 private của 2 bộ môn × cấp 0–5), 60 câu hỏi, 780 case tài khoản × câu hỏi. |

Bộ demo cũ (`demo/`) đã được gộp vào `official/` từ 10-10-2026 và bị xoá khỏi repo ngày 23-11-2026.

## `official/`

| Đường dẫn | Mô tả |
|---|---|
| `official/questions.jsonl` | 565 câu hỏi đánh giá kèm đáp án kỳ vọng, đoạn bằng chứng và tài liệu nguồn |
| `official/questions_review.csv` | Cùng bộ câu hỏi ở dạng bảng để người duyệt kiểm tra |
| `official/manifest.csv` | 1.875 tài liệu PDF đã tải: đơn vị, URL nguồn, quyền truy cập, chất lượng text, sha256, `local_path`, `document_id`, `title` |
| `official/files/<đơn-vị>/` | 1.057 PDF có text layer (≈ 0,9 GB), đặt tên theo tiêu đề tài liệu |
| `official/scanned_pdf/<đơn-vị>/` | PDF dạng ảnh scan, cần OCR (2,4 GB), đặt tên theo `file_id` |
| `official/departments.json` | Mã phòng ban → UUID trong backend lúc ingest |
| `official/sources.csv` | 42 trang nguồn đã crawl và thống kê |
| `official/discovered.csv` | 2.300 link PDF phát hiện được khi crawl |
| `official/download_errors.csv` | Link tải lỗi và nguyên nhân |
| `official/question_work/` | File trung gian khi sinh câu hỏi (slots, excerpts, answers) |

`local_path` trong `manifest.csv` tính từ thư mục `official/` (ví dụ `files/phong-dao-tao/<tiêu đề>.pdf`).

### Bộ câu hỏi (`questions.jsonl`)

| category | Số câu | Ý nghĩa |
|---|---|---|
| `normal` | 197 | Câu hỏi thông thường, có đáp án trong tài liệu |
| `access` | 172 | Kiểm tra phân quyền: tài liệu không công khai, `expect_visible` cho biết người hỏi có được thấy hay không |
| `unanswerable` | 70 | Không có đáp án trong kho tài liệu, hệ thống nên từ chối |
| `calculation` | 58 | Cần tính toán từ số liệu trong tài liệu |
| `off_topic` | 26 | Ngoài phạm vi trường |
| `web_search` | 24 | Cần tìm thêm trên web của trường |
| `social` | 18 | Chào hỏi, giao tiếp xã giao |

Các trường chính: `id`, `category`, `question`, `expected_answer`, `evidence`, `evidence_found`,
`expected_doc_ids` (khớp với `file_id` trong `manifest.csv`), `expected_intent`, `department_id`,
`doc_is_public`, `doc_access_level`, `persona`, `asker`, `expect_visible`, `reviewed`, `generator`.

> Câu hỏi được sinh tự động bằng LLM; `reviewed=false` nghĩa là chưa được người kiểm duyệt.

Câu `calculation` có thêm `expected_calculation` - đường tính kỳ vọng của agent: `formula:<formula_id>`
(công thức registry Python: `admission_score_2026`, `transcript_score_3hk`, `weighted_score`, `date_span`,
`time_span`...), `arithmetic` (số học thuần trên số nêu trong câu hỏi, code tính) hoặc `advisory` (số liệu phải lấy
từ văn bản: trích dẫn, có thể kèm khối tính do code thực hiện; model không được tự tính). Eval chấm `pass` khi đúng
đường và số kỳ vọng xuất hiện; `arithmetic` chấp nhận cả câu trả lời tư vấn có số đúng, và `a|b` chấp nhận một trong
hai đường.

### Manifest tài liệu (`manifest.csv`)

Cột `quality`: `ok` (1.057), `scanned` (631), `garbled_ocr` (167), `no_diacritics` (14), `broken_encoding` (6).
Cột `selected` đánh dấu 1.031 tài liệu được chọn để ingest (05-11-2026: bỏ 43 tài liệu nạp lại không xong vì hết quota và 27 câu hỏi dựa trên chúng).

## `access-control/`

Bộ test phân quyền theo phòng ban và cấp truy cập. **Toàn bộ nội dung là giả lập** (số hiệu văn bản, con số, tên
người tự đặt), không có trên website của trường, để chắc chắn chatbot chỉ trả lời được khi đọc đúng tài liệu.

| Đường dẫn | Mô tả |
|---|---|
| `access-control/catalog.json` | 20 tài liệu: đơn vị, `is_public`, `min_access_level`, chủ đề |
| `access-control/files/` | 20 PDF tiếng Việt (7–9 trang mỗi file) |
| `access-control/specs/` | Nguồn JSON của từng PDF (nội dung + 3 câu hỏi, đáp án, bằng chứng nguyên văn) |
| `access-control/questions.jsonl` | 60 câu hỏi (3 câu / tài liệu) |
| `access-control/user_questions.json` | Cách hỏi kiểu người dùng (viết tắt, không dấu) cho từng câu |
| `access-control/accounts.csv` | 12 tài khoản test + khách |
| `access-control/cases.csv` | 780 case (13 tài khoản × 60 câu): 438 `ANSWER`, 342 `DENY` |
| `access-control/manifest.csv` | Manifest theo định dạng của `official/` để ingest bằng `evals.dataset.ingest` |
| `access-control/Bo_cau_hoi_phan_quyen.xlsx` | Bộ câu hỏi dạng bảng (cùng cột với sheet "Official - Đầy đủ") dùng khi báo cáo |
| `access-control/tools/` | Script render PDF, tạo tài khoản, sinh case / manifest / Excel, ingest có retry |

| Đơn vị | Cấp 0 | Cấp 1 | Cấp 2 | Cấp 3 | Cấp 4 | Cấp 5 |
|---|---|---|---|---|---|---|
| BM_CONG_NGHE_PHAN_MEM | A0 | A1 | A2 | A3 | A4 | A5 |
| BM_KE_TOAN | B0 | B1 | B2 | B3 | B4 | B5 |

P1–P8 là văn bản học vụ công khai, ai cũng xem được. Tài liệu private chỉ trả lời cho tài khoản cùng đơn vị
(khớp chính xác) có cấp truy cập ≥ `min_access_level`. Tài khoản test: `TST-CNPM-L0..L5`, `TST-KT-L0..L5`
(chỉ tồn tại trên môi trường eval nội bộ).

## Sử dụng

```python
from datasets import load_dataset

questions = load_dataset("unisage/unisage-iuh-dataset", "questions", split="train")
manifest = load_dataset("unisage/unisage-iuh-dataset", "manifest", split="train")
access_cases = load_dataset("unisage/unisage-iuh-dataset", "access_control_cases", split="train")
```

Tải PDF:

```bash
hf download unisage/unisage-iuh-dataset --repo-type dataset --include "official/files/**" --local-dir ./iuh
hf download unisage/unisage-iuh-dataset --repo-type dataset --include "access-control/**" --local-dir ./iuh
```

## Nguồn và giấy phép

Tài liệu trong `official/` thuộc bản quyền của Trường Đại học Công nghiệp TP.HCM và các đơn vị trực thuộc, được thu
thập từ các website công khai `*.iuh.edu.vn`. Tài liệu trong `access-control/` do nhóm dự án tự soạn để test.
Bộ dữ liệu chỉ dùng cho mục đích nghiên cứu, đánh giá nội bộ.
Một số tài liệu có `is_public=false` trong manifest, cần cân nhắc trước khi công khai repo.
