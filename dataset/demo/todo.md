# Todo: Chuẩn bị bộ dữ liệu demo

Spec: [specs.md](specs.md) · Plan: [plan.md](plan.md). Đường dẫn tính từ `D:\KLTN\dataset\`. File gốc nằm trong `official\` và chỉ đọc; mọi file mới nằm trong `demo\`.

**Trạng thái (04-10-2026):** Task 1–11 đã xong, `validate_demo.py` báo 0 lỗi. Còn lại: người duyệt (`reviewed=false`) và các bước ngoài plan (ingest, chạy pipeline).

## Phase 1: Nền tảng

- [x] **Task 1: Xác nhận cách ingest và tín hiệu web search** (S)
  - Acceptance: Biết (a) metadata `department_id`/`access_level` truyền vào ingest ở đâu; (b) ngữ nghĩa level 0/5 và `expect_visible` khớp gateway; (c) cách quan sát node web search được kích hoạt; ghi kết quả vào specs.md mục 13.
  - Verify: Đọc code `unisage-agent` và gateway, trích dẫn `file:line`; người dùng xác nhận.
  - Files: `plans/04-10-2026-prepare-demo-dataset/specs.md` (chỉ cập nhật)
  - Dependencies: không

- [x] **Task 2: Dựng `demo_manifest.csv`** (S)
  - Acceptance: 106 dòng khớp `selection.csv`; có `demo_is_public`, `demo_access_level`, `orig_*`; mọi `local_path` tồn tại; `sha256` khớp manifest gốc.
  - Verify: `python demo\scripts\build_demo_manifest.py` rồi đếm theo phòng/level (public 78, L1 10, L2 8, L3 10).
  - Files: `demo/demo_manifest.csv`, `demo/scripts/build_demo_manifest.py`
  - Dependencies: không

- [x] **Task 3: Trích text từng PDF** (S)
  - Acceptance: `demo/question_work_demo/excerpts/<file_id>.txt` cho cả 106 tài liệu; không file rỗng.
  - Verify: đếm file = 106, kích thước tối thiểu > 0, mẫu 5 file đọc đúng tiếng Việt có dấu.
  - Files: `demo/question_work_demo/excerpts/*.txt`, `demo/scripts/build_slots.py`
  - Dependencies: Task 2

### Checkpoint 1
- [x] `demo_manifest.csv` đủ 106 dòng, PDF đều đọc được
- [x] Hash của `manifest.csv`, `questions.jsonl`, `questions_review.csv`, `question_work\` không đổi
- [ ] Review với người dùng trước khi sinh câu hỏi

## Phase 2: Câu hỏi có căn cứ trong tài liệu

- [x] **Task 4: Tái dùng câu cũ hợp lệ** (M)
  - Acceptance: Câu cũ có mọi `expected_doc_ids` trong 106 tài liệu (76 ứng viên: 55 normal, 9 calculation, 12 access) được chuyển sang schema demo với `reused_from`; `doc_is_public`, `doc_access_level`, `persona`, `asker`, `expect_visible` tính lại theo level demo; câu thuộc tài liệu nay private chuyển sang `access_private`.
  - Verify: `validate_demo.py` không lỗi access; đối chiếu ngẫu nhiên 10 câu với bản gốc.
  - Files: `demo/question_work_demo/reused.jsonl`, `demo/scripts/build_questions.py`
  - Dependencies: Task 2

- [x] **Task 5: Sinh `normal_guest` và `calculation` mới** (M)
  - Acceptance: Mỗi phòng có ≥ 2 câu `normal_guest` trên tài liệu public (kể cả câu tái dùng); ≥ 8 câu `calculation` tổng; mỗi câu có `expected_answer` và `evidence` có trong text tài liệu.
  - Verify: `validate_demo.py` (evidence + coverage cho hai case này).
  - Files: `demo/question_work_demo/slots.jsonl`, `demo/question_work_demo/answers/*.jsonl`
  - Dependencies: Task 3, Task 4

- [x] **Task 6: Sinh `access_private` và `access_public_cross`** (M)
  - Acceptance: Mỗi trong 28 tài liệu private có 1 câu hỏi × 5 persona (140 dòng) với `expect_visible` đúng bảng ở specs.md 4.2; mỗi phòng có ≥ 1 câu `access_public_cross`. Persona/asker sinh bằng script.
  - Verify: `validate_demo.py` (quy tắc access, mỗi tài liệu private đủ 5 persona).
  - Files: `demo/question_work_demo/slots.jsonl`, `demo/question_work_demo/answers/*.jsonl`
  - Dependencies: Task 3, Task 4

- [x] **Task 7: Sinh `advisory_single`, `advisory_multi`, `advisory_compare`** (M)
  - Acceptance: ≥ 12 SINGLE, ≥ 12 MULTI, ≥ 4 compare (câu đơn nhiều thực thể vẫn SINGLE). MULTI là câu ghép/phức/nhiều câu có nhiều yêu cầu độc lập; gắn `routing_mode` và số câu hỏi con kỳ vọng.
  - Verify: Duyệt tay toàn bộ 28 câu theo định nghĩa ngữ pháp; `validate_demo.py`.
  - Files: `demo/question_work_demo/slots.jsonl`, `demo/question_work_demo/answers/*.jsonl`
  - Dependencies: Task 5

### Checkpoint 2
- [x] `validate_demo.py` báo 0 lỗi schema/access/evidence cho các case có tài liệu
- [x] Các nhóm `normal_guest`, `access_*`, `advisory_*`, `calculation` đạt mức tối thiểu
- [ ] Review với người dùng

## Phase 3: Câu hỏi không dựa tài liệu

- [x] **Task 8: Sinh `unanswerable`, `off_topic`, `social`** (S)
  - Acceptance: ≥ 10 unanswerable (phân bố nhiều phòng, không có đáp án trong 106 tài liệu), ≥ 8 off_topic, ≥ 6 social (nhiều kiểu chào hỏi, cảm ơn, tạm biệt); `expected_intent` đúng.
  - Verify: `validate_demo.py`; kiểm tay unanswerable không vô tình có đáp án trong excerpts (grep từ khoá).
  - Files: `demo/question_work_demo/answers/*.jsonl`
  - Dependencies: Task 5

- [x] **Task 9: Sinh `web_search`** (XS)
  - Acceptance: ≥ 6 câu về thông tin ngoài kho cần dữ liệu mới của trường, `expect_web_search=true`; không yêu cầu đáp án hay nguồn.
  - Verify: Tín hiệu kích hoạt đã xác nhận ở Task 1; `validate_demo.py`.
  - Files: `demo/question_work_demo/answers/*.jsonl`
  - Dependencies: Task 1

### Checkpoint 3
- [x] Mọi case ở specs.md mục 4.1 đạt mức tối thiểu

## Phase 4: Gộp, kiểm tra, bàn giao

- [x] **Task 10: Gộp và kiểm tra** (S)
  - Acceptance: `questions_demo.jsonl` (id `d0001...`, không trùng) và `questions_demo_review.csv`; `validate_demo.py` 0 lỗi; hash file gốc trước/sau trùng.
  - Verify: `python demo\scripts\build_questions.py; python demo\scripts\validate_demo.py`
  - Files: `demo/questions_demo.jsonl`, `demo/questions_demo_review.csv`, `demo/scripts/validate_demo.py`
  - Dependencies: Task 6, 7, 8, 9

- [x] **Task 11: Báo cáo coverage và bàn giao** (XS)
  - Acceptance: Bảng đếm số câu theo case/phòng/persona; danh sách câu cần người duyệt; `reviewed=false` toàn bộ.
  - Verify: Người dùng đọc và đồng ý.
  - Files: `demo/coverage_report.md`
  - Dependencies: Task 10

### Checkpoint 4 (dừng để duyệt)
- [x] Đạt specs.md mục 11 (trừ mục 6)
- [ ] Người dùng duyệt trước khi ingest 106 tài liệu hoặc chạy pipeline
