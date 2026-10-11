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
  - config_name: demo_questions
    data_files: demo/questions_demo.jsonl
  - config_name: demo_manifest
    data_files: demo/demo_manifest.csv
---

# UniSage IUH Dataset

Bộ dữ liệu phục vụ xây dựng và đánh giá hệ thống hỏi đáp RAG (UniSage Gateway) cho Trường Đại học Công nghiệp TP.HCM (IUH).
Gồm tài liệu PDF crawl từ các website của trường và các bộ câu hỏi đánh giá kèm đáp án, bằng chứng trích dẫn.

Repo có hai phần tách biệt:

| Thư mục | Nội dung |
|---|---|
| `official/` | Bộ dữ liệu chính thức: toàn bộ 1.929 PDF và bộ 557 câu hỏi (gộp bộ gốc với bộ demo ngày 10-10-2026). |
| `demo/` | Bộ demo nhỏ để test pipeline: 106 tài liệu chọn từ 12 phòng ban và 276 câu hỏi phủ các luồng xử lý. |

## `official/`

| Đường dẫn | Mô tả |
|---|---|
| `official/questions.jsonl` | 557 câu hỏi đánh giá (gộp bộ gốc và bộ demo) kèm đáp án kỳ vọng, đoạn bằng chứng và tài liệu nguồn |
| `official/questions_review.csv` | Cùng bộ câu hỏi ở dạng bảng để người duyệt kiểm tra |
| `official/manifest.csv` | 1.929 tài liệu PDF đã tải: đơn vị, URL nguồn, quyền truy cập, chất lượng text, sha256, `local_path` |
| `official/files/<đơn-vị>/` | PDF có text layer (1,1 GB) |
| `official/scanned_pdf/<đơn-vị>/` | PDF dạng ảnh scan, cần OCR (2,4 GB) |
| `official/sources.csv` | 42 trang nguồn đã crawl và thống kê |
| `official/discovered.csv` | 2.300 link PDF phát hiện được khi crawl |
| `official/download_errors.csv` | 371 link tải lỗi và nguyên nhân |
| `official/question_work/` | File trung gian khi sinh câu hỏi (slots, excerpts, answers) |

`local_path` trong `manifest.csv` tính từ thư mục `official/` (ví dụ `files/phong-dao-tao/xxxx.pdf`).

### Bộ câu hỏi (`questions.jsonl`)

| category | Số câu | Ý nghĩa |
|---|---|---|
| `normal` | 210 | Câu hỏi thông thường, có đáp án trong tài liệu |
| `access` | 188 | Kiểm tra phân quyền: tài liệu không công khai, `expect_visible` cho biết người hỏi có được thấy hay không |
| `unanswerable` | 50 | Không có đáp án trong kho tài liệu, hệ thống nên từ chối |
| `calculation` | 59 | Cần tính toán từ số liệu trong tài liệu |
| `off_topic` | 26 | Ngoài phạm vi trường |
| `social` | 18 | Chào hỏi, giao tiếp xã giao |

Các trường chính: `id`, `category`, `question`, `expected_answer`, `evidence`, `evidence_found`,
`expected_doc_ids` (khớp với `file_id` trong `manifest.csv`), `expected_intent`, `department_id`,
`doc_is_public`, `doc_access_level`, `persona`, `asker`, `expect_visible`, `reviewed`, `generator`.

> Câu hỏi được sinh tự động bằng LLM; `reviewed=false` nghĩa là chưa được người kiểm duyệt.

### Manifest tài liệu (`manifest.csv`)

Cột `quality`: `ok` (1.111), `scanned` (631), `garbled_ocr` (167), `no_diacritics` (14), `broken_encoding` (6).
Cột `selected` đánh dấu 1.085 tài liệu được chọn để ingest.

## `demo/`

Bộ demo để test pipeline, sửa lỗi và làm nền cho việc chấm RAGAS về sau. Tách biệt hoàn toàn với `official/`.

| Đường dẫn | Mô tả |
|---|---|
| `demo/demo_manifest.csv` | 106 tài liệu demo (trỏ tới PDF trong `official/` qua `local_path`), có `demo_is_public` / `demo_access_level` và cột `orig_*` giữ giá trị gốc |
| `demo/questions_demo.jsonl` | 276 câu hỏi (id `d0001...`), cùng schema với `questions.jsonl` cộng `case`, `routing_mode`, `expect_web_search`, `reused_from` |
| `demo/questions_demo_review.csv` | Cùng bộ câu hỏi dạng bảng |
| `demo/question_work_demo/` | File trung gian (excerpts của 106 tài liệu, câu tái dùng, câu viết tay) |
| `demo/specs.md`, `demo/plan.md`, `demo/todo.md` | Đặc tả, kế hoạch và danh sách task |
| `demo/coverage_report.md` | Thống kê coverage theo case, persona, phòng ban |
| `demo/scripts/` | Script dựng manifest, trích text, gộp câu hỏi và kiểm tra |

**Level private trong demo là level giả định**, gán để test phân quyền (public 78, L1 10, L2 8, L3 10); level gốc ở các cột `orig_*`.
Các case: `normal_guest`, `access_private` (mỗi tài liệu private × 5 persona), `access_public_cross`, `advisory_single`,
`advisory_multi`, `advisory_compare`, `calculation`, `unanswerable`, `off_topic`, `social`, `web_search`.
Toàn bộ câu hỏi demo là `reviewed=false`.

## Sử dụng

```python
from datasets import load_dataset

questions = load_dataset("unisage/unisage-iuh-dataset", "questions", split="train")
manifest = load_dataset("unisage/unisage-iuh-dataset", "manifest", split="train")
demo_questions = load_dataset("unisage/unisage-iuh-dataset", "demo_questions", split="train")
```

Tải PDF:

```bash
hf download unisage/unisage-iuh-dataset --repo-type dataset --include "official/files/*" --local-dir ./iuh
```

## Nguồn và giấy phép

Tài liệu gốc thuộc bản quyền của Trường Đại học Công nghiệp TP.HCM và các đơn vị trực thuộc, được thu thập từ
các website công khai `*.iuh.edu.vn`. Bộ dữ liệu chỉ dùng cho mục đích nghiên cứu, đánh giá nội bộ.
Một số tài liệu có `is_public=false` trong manifest, cần cân nhắc trước khi công khai repo.
