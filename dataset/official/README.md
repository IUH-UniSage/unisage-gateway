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
    data_files: questions.jsonl
    default: true
  - config_name: questions_review
    data_files: questions_review.csv
  - config_name: manifest
    data_files: manifest.csv
  - config_name: sources
    data_files: sources.csv
  - config_name: discovered
    data_files: discovered.csv
---

# UniSage IUH Dataset

Bộ dữ liệu phục vụ xây dựng và đánh giá hệ thống hỏi đáp RAG (UniSage Gateway) cho Trường Đại học Công nghiệp TP.HCM (IUH).
Gồm tài liệu PDF crawl từ các website của trường và bộ câu hỏi đánh giá kèm đáp án, bằng chứng trích dẫn.

## Cấu trúc

| Đường dẫn | Mô tả |
|---|---|
| `questions.jsonl` | 557 câu hỏi đánh giá (bộ gốc + bộ demo) kèm đáp án kỳ vọng, đoạn bằng chứng và tài liệu nguồn |
| `questions_review.csv` | Cùng bộ câu hỏi ở dạng bảng để người duyệt kiểm tra |
| `manifest.csv` | 1.929 tài liệu PDF đã tải: đơn vị, URL nguồn, quyền truy cập, chất lượng text, sha256, `local_path` |
| `files/<đơn-vị>/` | PDF có text layer (1,1 GB) |
| `scanned_pdf/<đơn-vị>/` | PDF dạng ảnh scan, cần OCR (2,4 GB) |
| `sources.csv` | 42 trang nguồn đã crawl và thống kê |
| `discovered.csv` | 2.300 link PDF phát hiện được khi crawl |
| `download_errors.csv` | 371 link tải lỗi và nguyên nhân |
| `question_work/` | File trung gian khi sinh câu hỏi (slots, excerpts, answers) |

## Bộ câu hỏi (`questions.jsonl`)

Gộp từ bộ gốc (`q*`, 221 câu còn lại) và bộ demo (`d*`, 336 câu) ngày 10-10-2026. 76 câu gốc mà bộ demo
đã dùng lại được bỏ để không trùng. Cột `source_set` cho biết câu thuộc bộ nào.

Ngày 10-10-2026 thêm 60 câu `d0277`–`d0336` cho bộ demo: 30 câu `normal` cho 18 tài liệu demo trước đó
chưa có câu hỏi, 30 câu `calculation` (có `expected_numbers`, 11 câu tính ngược). Các câu này có thêm
`question_user`: cùng câu hỏi nhưng viết như người dùng gõ trong khung chat (ngắn, không nêu tên tài liệu,
một phần không dấu/viết tắt). 3 câu có `review_note` cần duyệt.

Ngày 11-10-2026 thêm `question_user` cho mọi câu có đáp án (`normal`, `calculation`, `access`; 457 dòng
của cả bộ gốc và bộ demo): cùng nhu cầu thông tin và cùng đáp án, nhưng viết như người dùng thật gõ.
Dùng để đo khoảng cách giữa câu "chính xác" (`question`) và câu người dùng (`question_user`).

Phân bố theo `category`:

| category | Số câu | Ý nghĩa |
|---|---|---|
| `access` | 188 | Kiểm tra phân quyền: tài liệu không công khai, `expect_visible` cho biết người hỏi có được thấy hay không |
| `normal` | 210 | Câu hỏi thông thường, có đáp án trong tài liệu (gồm câu một ý, nhiều ý, so sánh) |
| `unanswerable` | 50 | Không có đáp án trong kho tài liệu, hệ thống nên từ chối |
| `calculation` | 59 | Cần tính toán từ số liệu trong tài liệu |
| `off_topic` | 26 | Ngoài phạm vi trường |
| `social` | 18 | Chào hỏi, giao tiếp xã giao |
| `web_search` | 6 | Cần tìm thêm trên web |

Các trường chính: `id`, `source_set`, `category`, `case`, `question`, `expected_answer`, `evidence`,
`evidence_found`, `expected_doc_ids` (khớp với `file_id` trong `manifest.csv`), `expected_intent`,
`routing_mode`, `sub_question_count`, `expect_web_search`, `department_id`, `doc_is_public`,
`doc_access_level`, `persona`, `asker`, `expect_visible`, `reused_from`, `reviewed`, `generator`; câu mới từ
10-10-2026 có thêm `question_user`, `expected_numbers` (câu `calculation`) và `review_note` (nếu cần duyệt).

> Câu hỏi được sinh tự động bằng LLM; `reviewed=false` nghĩa là chưa được người kiểm duyệt.

## Manifest tài liệu (`manifest.csv`)

Cột `quality` phân loại chất lượng text trích xuất: `ok` (1.111), `scanned` (631), `garbled_ocr` (167),
`no_diacritics` (14), `broken_encoding` (6). Cột `selected` đánh dấu 1.085 tài liệu được chọn để ingest.
Dùng `local_path` để tìm file PDF tương ứng trong repo.

46 tài liệu của bộ demo được gán lại nhãn quyền để có đủ case phân quyền (`label_source=demo`); câu hỏi
`access` dựa trên nhãn này, nên phải ingest lại theo `manifest.csv` hiện tại.

## Sử dụng

```python
from datasets import load_dataset

questions = load_dataset("hgjyhm/unisage-iuh-dataset", "questions", split="train")
manifest = load_dataset("hgjyhm/unisage-iuh-dataset", "manifest", split="train")
```

Tải PDF:

```bash
hf download hgjyhm/unisage-iuh-dataset --type dataset --include "files/*" --local-dir ./iuh
```

## Nguồn và giấy phép

Tài liệu gốc thuộc bản quyền của Trường Đại học Công nghiệp TP.HCM và các đơn vị trực thuộc, được thu thập từ
các website công khai `*.iuh.edu.vn`. Bộ dữ liệu chỉ dùng cho mục đích nghiên cứu, đánh giá nội bộ.
Một số tài liệu có `is_public=false` trong manifest, cần cân nhắc trước khi công khai repo.
