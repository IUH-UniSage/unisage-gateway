# Spec: Bộ dữ liệu demo để test pipeline UniSage

Ngày: 04-10-2026 · Trạng thái: dữ liệu đã dựng và qua kiểm tra, chờ duyệt · Plan: [plan.md](plan.md) · Tasks: [todo.md](todo.md)

## 1. Objective

Dựng một **bộ test end-to-end nhỏ, kiểm soát được** cho UniSage Gateway:

- ~106 tài liệu chọn từ một số phòng ban (nhỏ hơn nhiều so với kho 1.929 PDF).
- Một bộ câu hỏi **mới, tách biệt hoàn toàn** với bộ 297 câu cũ. Số lượng không giới hạn, chỉ cần **bao phủ hết các case** ở mục 4.
- Mục đích: chạy pipeline, phát hiện và sửa lỗi. Bộ này giữ sẵn `expected_answer` và `evidence` để sau này đưa vào RAGAS, nhưng **phase này chưa chấm RAGAS**.

Người dùng: tác giả KLTN. Thành công: mọi case có kết quả kỳ vọng đối chiếu được và pipeline chạy hết bộ để ra pass/fail theo từng luồng.

## 2. Những gì đã chốt

| # | Quyết định |
|---|---|
| 1 | Mục tiêu bộ câu hỏi: test pipeline, sửa lỗi; làm cơ sở chấm RAGAS về sau (chưa làm ở phase này). |
| 2 | Số câu hỏi không có trần; điều kiện dừng là bao phủ hết các case. |
| 3 | Chọn **tài liệu trước theo phòng ban**, rồi **sinh câu hỏi mới** cho chúng. Câu cũ chỉ được tái dùng khi tài liệu tương ứng nằm trong bộ demo. |
| 4 | Phòng ban: PHONG_DAO_TAO, PHONG_TC_KT, PHONG_KHAO_THI_DBCL, TT_NGOAI_NGU, cộng toàn bộ thư mục tuyển sinh. **Bỏ PHONG_CTSV.** Bù thêm phòng ban khác cho đủ ~100 tài liệu. |
| 5 | Tối đa 10 tài liệu mỗi phòng (không tính 5 tài liệu tuyển sinh). Cho phép vượt 100 tổng. |
| 6 | Không có OCR: chỉ lấy tài liệu `quality = ok`, bỏ scan, `garbled_ocr`, `no_diacritics`, `broken_encoding`. |
| 7 | PHONG_TC_KT: để public hoàn toàn. |
| 8 | Phần lớn là public (để test vãng lai). Một số tài liệu **giả định private ở L1–L3, phân bố đều**. Level giả chỉ nằm trong file của bộ demo, **không sửa `manifest.csv` gốc**. |
| 9 | Web search: chỉ kiểm tra **node web search có được kích hoạt**; không cần đúng kết quả hay đúng nguồn web. |
| 10 | SINGLE/MULTI phân loại theo **cấu trúc ngữ pháp của tin nhắn** (câu đơn một yêu cầu = SINGLE; câu ghép, câu phức hoặc nhiều câu = MULTI), **không** theo số thực thể được nhắc. |
| 11 | Mô hình access dùng lại 5 persona của bộ cũ (mục 4.2). |

## 3. Assumptions (sửa ngay nếu sai)

1. `department_id` và `access_level` của tài liệu demo được truyền vào pipeline qua metadata lúc ingest. Cách upload (API gateway hay script ingest) sẽ xác nhận ở Task 1 của plan.
2. Ngữ nghĩa level: số càng lớn càng hạn chế. Người hỏi thấy tài liệu khi `asker.access_level >= doc.access_level` trong cùng phòng ban, hoặc có wildcard `*`. Đúng với dữ liệu persona của bộ cũ, cần xác nhận lại với gateway.
3. Tài liệu public thấy được với mọi người hỏi, kể cả `guest` (`department_access = []`).
4. Câu hỏi do LLM sinh từ trích đoạn tài liệu, `reviewed=false` cho đến khi người duyệt.
5. Intent hợp lệ hiện có: `academic_advisory`, `academic_calculation`, `off_topic`, `social_chat`. Chưa biết giá trị intent/cờ cho web search; xem Open Questions.

## 4. Case matrix (phải bao phủ hết)

### 4.1 Các nhóm case (kết quả thực tế ở [coverage_report.md](coverage_report.md))

| Mã case | Mô tả | Kỳ vọng kiểm tra | Tối thiểu |
|---|---|---|---|
| `normal_guest` | Hỏi đáp thường trên tài liệu public, người hỏi `guest` | Đúng intent, trả lời có căn cứ, trích dẫn đúng tài liệu | 2 câu mỗi phòng (24+) |
| `access_private` | Mỗi tài liệu private × 5 persona | `expect_visible` đúng theo bảng 4.2; thấy thì trả lời, không thấy thì không lộ nội dung | 1 câu mỗi tài liệu private × 5 persona |
| `access_public_cross` | Tài liệu public, hỏi từ phòng ban khác | Luôn thấy được | 1 câu mỗi phòng |
| `advisory_single` | Câu đơn, đúng một yêu cầu | `routing_mode = SINGLE` | 12 |
| `advisory_multi` | Câu ghép/phức/nhiều câu, nhiều yêu cầu độc lập | `routing_mode = MULTI`, tách đúng số câu hỏi con | 12 |
| `advisory_compare` | Câu đơn nhưng so sánh nhiều thực thể | Vẫn là `SINGLE` (tách theo thực thể ở tầng dưới) | 4 |
| `calculation` | Cần tính từ số liệu trong tài liệu | `academic_calculation`, kết quả đúng | 8 |
| `unanswerable` | Không có đáp án trong kho | Từ chối đúng cách, không bịa, gợi ý liên hệ | 10 |
| `off_topic` | Ngoài phạm vi trường | `off_topic`, từ chối lịch sự | 8 |
| `social` | Chào hỏi xã giao | `social_chat`, đáp thân thiện | 6 |
| `web_search` | Cần thông tin ngoài kho, có yếu tố mới/thời sự | **Node web search được kích hoạt** (không kiểm tra nội dung) | 6 |

Các mức "tối thiểu" là sàn chứ không phải trần; thêm câu tuỳ ý miễn không bỏ sót nhóm nào.

### 4.2 Persona và `expect_visible` (dùng lại nguyên mô hình bộ cũ)

| Persona | `asker.department_access` | Với tài liệu private của phòng X, level L |
|---|---|---|
| `guest` | `[]` | không thấy |
| `same_department_exact_level` | `[{X, L}]` | thấy |
| `same_department_one_level_below` | `[{X, L-1}]` (L1 thì dùng 0) | không thấy |
| `other_department_max_level` | `[{phòng khác, 5}]` | không thấy |
| `wildcard_max_level` | `[{"*", 5}]` | thấy |

## 5. Bộ tài liệu (tóm tắt, chi tiết ở plan.md phụ lục)

106 tài liệu / 12 phòng ban / 1.071 trang. Gán level giả: **public 78, L1 10, L2 8, L3 10**.

| Phòng ban | Tài liệu | Public | L1 | L2 | L3 | Ghi chú |
|---|---|---|---|---|---|---|
| PHONG_DAO_TAO | 15 | 12 | 1 | 1 | 1 | 10 chung + 5 tuyển sinh (5 này luôn public) |
| PHONG_KHAO_THI_DBCL | 10 | 7 | 1 | 1 | 1 | |
| PHONG_TC_KT | 1 | 1 | – | – | – | chỉ có 1 tài liệu `ok`; public |
| TT_NGOAI_NGU | 7 | 5 | 1 | – | 1 | chỉ có 7 tài liệu đủ điều kiện |
| KHOA_CNTT | 10 | 7 | 1 | 1 | 1 | bù thêm |
| VIEN_TAI_CHINH_KE_TOAN | 10 | 7 | 1 | 1 | 1 | bù thêm |
| PHONG_QLKH_HTQT | 10 | 7 | 1 | 1 | 1 | bù thêm |
| KHOA_NGOAI_NGU | 10 | 7 | 1 | 1 | 1 | bù thêm |
| KHOA_QTKD | 10 | 7 | 1 | 1 | 1 | bù thêm |
| PHONG_TO_CHUC_HANH_CHINH | 8 | 8 | – | – | – | bù thêm; public |
| TT_QUAN_TRI_HE_THONG | 10 | 7 | 1 | 1 | 1 | bù thêm |
| BAN_QUAN_LY_KTX | 5 | 3 | 1 | – | 1 | bù thêm; chỉ có 5 tài liệu `ok` |

### Quy tắc chọn (có thể tái lập)

- Điều kiện: `quality = ok`, file tồn tại, `pages <= 60`, `text_chars >= 1000`. Riêng thư mục tuyển sinh lấy **cả 5 tài liệu `ok`**, không áp `text_chars`/`pages`.
- Ưu tiên tài liệu đã được bộ câu cũ tham chiếu (để tái dùng câu hỏi), sau đó theo `sha256` tăng dần.
- Gán private: chọn trong số tài liệu ít được tham chiếu nhất của phòng, theo `sha256`. Phòng đủ 10 tài liệu thì 3 private (L1, L2, L3); phòng 5–9 tài liệu thì 2 private (L1, L3). PHONG_TC_KT, PHONG_TO_CHUC_HANH_CHINH và 5 tài liệu tuyển sinh luôn public.
- Thư mục tuyển sinh có 13 tài liệu: 5 tài liệu `ok` được ingest, 8 tài liệu scan bị bỏ vì không có OCR.

## 6. Commands

Dùng PowerShell (Windows). Các script nằm trong `D:\KLTN\dataset\demo\scripts\`.

```powershell
# Python của unisage-agent có sẵn pymupdf (không cài thêm thư viện)
$py = "D:\KLTN\Main\unisage-agent\.venv\Scripts\python.exe"
cd D:\KLTN\dataset\demo\scripts

& $py build_demo_manifest.py   # selection.csv -> demo_manifest.csv (kiểm tra file + sha256)
& $py build_excerpts.py        # trích text -> question_work_demo\excerpts\
python reuse_old.py            # câu cũ tái dùng -> question_work_demo\reused_base.jsonl
python build_questions.py      # gộp câu tái dùng + câu viết tay -> questions_demo.jsonl
python validate_demo.py        # schema, expect_visible, evidence, coverage, file gốc không đổi
```

Lệnh ingest và chạy pipeline là bước sau (xem mục 14).

## 7. Project structure

Mọi thứ mới nằm trong `demo/`. Các file/thư mục gốc **chỉ đọc**.

```
D:\KLTN\dataset\
├─ official\                    (CHÍNH THỨC - chỉ đọc, không sửa)
│   ├─ manifest.csv, questions.jsonl, questions_review.csv, sources.csv, ...
│   ├─ question_work\
│   └─ files\, scanned_pdf\     (PDF; `local_path` trong manifest tính từ official\)
└─ demo\                        (MỚI - tách biệt hoàn toàn)
    ├─ specs.md, plan.md, todo.md
    ├─ selection.csv            (106 tài liệu + level demo)
    ├─ official_hash_before.txt (hash các file gốc nhỏ trước khi làm)
    ├─ demo_manifest.csv        (106 dòng, có demo_is_public / demo_access_level)
    ├─ questions_demo.jsonl     (câu hỏi demo, id d0001...)
    ├─ questions_demo_review.csv
    ├─ question_work_demo\      (slots.jsonl, excerpts\, answers\, review_notes.json)
    └─ scripts\
```

`local_path` trong `selection.csv` và `demo_manifest.csv` giữ nguyên dạng tương đối `files/...` hoặc `scanned_pdf/...`, tính từ `official\`.

## 8. Schema câu hỏi (`questions_demo.jsonl`)

Giữ các trường của `questions.jsonl` cũ: `id, slot_id, category, question, expected_answer, evidence, evidence_found, expected_doc_ids, expected_intent, department_id, doc_is_public, doc_access_level, persona, asker, expect_visible, reviewed, generator`. Thêm:

- `case`: mã case ở 4.1.
- `routing_mode`: `SINGLE` / `MULTI` / rỗng (chỉ áp cho nhóm advisory).
- `expect_web_search`: `true` chỉ với case `web_search`.
- `reused_from`: id câu cũ nếu tái dùng, rỗng nếu sinh mới.
- `demo_batch`: `2026-10-04`.

`id` dùng tiền tố `d` (ví dụ `d0001`) để không nhầm với `q0001` của bộ cũ. `doc_is_public` và `doc_access_level` lấy từ **level demo**, không phải level gốc.

### Quy tắc tái dùng câu cũ

- Chỉ tái dùng khi **mọi** `expected_doc_ids` nằm trong 106 tài liệu demo (hiện có 76 ứng viên: 55 normal, 9 calculation, 12 access).
- Sao chép `question`, `expected_answer`, `evidence`; ghi `reused_from`.
- Tính lại `doc_is_public`, `doc_access_level`, `persona`, `asker`, `expect_visible` theo level demo. Câu cũ ở tài liệu nay là private thì chuyển thành case `access_private` với đủ 5 persona.
- Câu `access` cũ chỉ giữ nguyên nếu level demo của tài liệu trùng level cũ; nếu không thì sinh lại.

## 9. Testing strategy

Vì đây là dữ liệu, "test" là các kiểm tra tự động của script:

- **Schema:** mọi dòng đủ trường bắt buộc, `category`/`case`/`persona` thuộc tập hợp hợp lệ.
- **Toàn vẹn:** mọi `expected_doc_ids` có trong `demo_manifest.csv`; mọi `local_path` tồn tại; không `id` trùng.
- **Quy tắc access:** `expect_visible` khớp bảng 4.2 tính từ `asker` và level demo.
- **Coverage:** mỗi case đạt mức tối thiểu ở 4.1; mỗi tài liệu private có đủ 5 persona; mỗi phòng có ít nhất 1 câu `normal_guest`.
- **Evidence:** với câu có `evidence_found=true`, đoạn `evidence` phải xuất hiện trong text của tài liệu (so khớp sau khi chuẩn hoá khoảng trắng).
- **Tách biệt:** kiểm tra không file nào dưới `question_work\` và các file gốc bị đổi (so sánh hash trước/sau).

## 10. Boundaries

- **Always:** đọc file gốc ở chế độ chỉ đọc; ghi mọi thứ mới vào `demo/`; giữ cột `orig_*` để biết level gốc; chạy `validate_demo.py` trước khi coi là xong; commit message ngắn, không nêu task/phase/tên file.
- **Ask first:** sửa `manifest.csv` gốc; thêm tài liệu ngoài 12 phòng đã chốt; thêm thư viện Python mới; ingest vào hệ thống thật (tác động ra ngoài); đổi định nghĩa SINGLE/MULTI.
- **Never:** sửa hoặc xoá bất kỳ file/thư mục đã tạo trước đó (`questions.jsonl`, `questions_review.csv`, `question_work\`...); hardcode nội dung theo từng tài liệu cụ thể trong code ingestion/parsing; đưa thư mục `dataset\` lên repo công khai; thêm trailer co-author của AI vào commit.

## 11. Success criteria

1. `demo\demo_manifest.csv` có đúng 106 dòng, khớp `selection.csv`, mọi PDF tồn tại.
2. `questions_demo.jsonl` bao phủ đủ **mọi case** ở 4.1, đạt mức tối thiểu; `validate_demo.py` báo 0 lỗi.
3. Mỗi tài liệu private có 5 dòng persona với `expect_visible` đúng; mỗi level L1, L2, L3 có ít nhất 8 tài liệu được kiểm tra.
4. Các file/thư mục gốc không đổi (hash trước/sau trùng).
5. Câu tái dùng đều có `reused_from` hợp lệ và level/persona đã tính lại.
6. Pipeline chạy hết bộ và cho ra bảng pass/fail theo từng case (thực hiện ở bước chạy test, ngoài phạm vi dựng dữ liệu).

## 12. Out of scope

Chấm RAGAS ở phase này; OCR tài liệu scan; tài liệu CTSV; kiểm tra độ đúng của câu trả lời web search; sửa manifest gốc; sinh câu hỏi cho 1.800+ tài liệu còn lại.

## 13. Open Questions

1. **Người duyệt:** ai duyệt `reviewed` và duyệt theo mẫu hay toàn bộ?
2. **Cấu hình web search khi chạy test:** `CHAT_WEB_SEARCH_ENABLED` và `TAVILY_API_KEY` có bật không? Quyết định kỳ vọng của `unanswerable` (mục 14).

## 14. Kết quả Task 1 (đã xác nhận bằng code `unisage-agent`)

- **Ingest:** luồng wizard qua gateway: `POST /ingestion/preview`, `/ingestion/chunking`, `/ingestion/embedding`. `EmbeddingRequest` mang `document_id`, `object_key` (MinIO), `department_id`, `access_level`, `is_public` (`app/api/v1/ingestion.py:149`). Người gọi chỉ được ingest với `access_level` không vượt level họ được cấp trong phòng đó (`ingestion.py:250`). Cần MinIO, Celery, Qdrant và `document_id` từ backend nên ingest tách khỏi việc dựng dữ liệu (ngoài phạm vi plan này).
- **Quyền thấy chunk:** chunk thấy được nếu `is_public`, hoặc người hỏi có mục `department_access` cùng phòng (hoặc `*`) với `access_level` >= level của chunk (`app/rag/vectorstore/qdrant_store.py:89`). Khớp bảng persona ở 4.2; level 0 và 5 hợp lệ. `guest` có `department_access = []` nên chỉ thấy tài liệu public.
- **Web search:** `WebSearchNode` chạy khi rerank không còn chunk nào cho một sub-query và `CHAT_WEB_SEARCH_ENABLED` bật (`app/graph/streaming_graph.py:343`). Tín hiệu kích hoạt đo được: node `09b_WebSearchNode` trong trace. Cờ `used_web_search` chỉ true khi có kết quả web, và thiếu `TAVILY_API_KEY` thì node chạy nhưng không có kết quả (cảnh báo `NOT_CONFIGURED`). Không có kết quả web và không có chunk thì đi `11_TicketFallbackNode` (`used_ticket_fallback`).
- **Hệ quả cho case:**
  - `web_search`: kiểm tra node `09b_WebSearchNode` có trong trace, không kiểm tra kết quả.
  - Mọi câu mà không còn chunk nào (cả `unanswerable` lẫn `access_private` với `expect_visible=false`) cũng đi qua web search trước khi vào ticket fallback. Vì vậy kỳ vọng của hai nhóm này là "không dùng nội dung tài liệu cấm/không có", và hệ thống đi `09b_WebSearchNode` rồi (có kết quả web thì trả lời từ web, không thì `used_ticket_fallback`). Không kiểm tra riêng ticket fallback trừ khi tắt web search.
  - Câu `web_search` nên là câu về trường nhưng không có trong 106 tài liệu (tin mới, thông báo gần đây), khác `unanswerable` ở ý định thiết kế: `unanswerable` kiểm tra không bịa, `web_search` kiểm tra node được kích hoạt.
