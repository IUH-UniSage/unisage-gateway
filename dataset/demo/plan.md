# Implementation Plan: Chuẩn bị bộ dữ liệu demo

Spec: [specs.md](specs.md) · Tasks: [todo.md](todo.md) · Ngày: 04-10-2026

## Overview

Dựng bộ demo gồm 106 tài liệu (12 phòng ban) và bộ câu hỏi mới phủ hết các case, tất cả nằm trong `D:\KLTN\dataset\demo\`, tách biệt hoàn toàn với `questions.jsonl`, `questions_review.csv` và `question_work\` đã tạo trước đó. Plan này chỉ dựng **dữ liệu**; ingest vào hệ thống thật và chạy pipeline là bước sau, cần duyệt riêng.

## Architecture Decisions

- **Tách biệt bằng thư mục `demo/`.** Mọi file mới ghi vào đây; file gốc chỉ đọc và được kiểm hash trước/sau.
- **Level giả nằm trong `demo_manifest.csv`**, giữ cột `orig_is_public` và `orig_access_level` để truy nguyên, không đụng `manifest.csv` gốc.
- **Chọn tài liệu xác định (deterministic)** theo quy tắc ở specs.md mục 5, kết quả chốt trong `selection.csv`, nên chạy lại ra cùng kết quả.
- **Câu hỏi sinh từ trích đoạn tài liệu** (`excerpts/`) rồi LLM sinh slot, đáp án và evidence, giống quy trình của bộ cũ nhưng workspace riêng `question_work_demo/`.
- **Tái dùng câu cũ có tính lại** `doc_is_public`, `doc_access_level`, `persona`, `asker`, `expect_visible` theo level demo.
- **Persona access sinh bằng script** từ (phòng, level) thay vì để LLM tự viết, để `expect_visible` luôn đúng.
- **Không hardcode theo từng tài liệu** trong script; script đọc quy tắc từ dữ liệu.

## Dependency graph

```
selection.csv ─► demo_manifest.csv ─► excerpts (trích text từng PDF)
                                         │
              câu cũ tái dùng ◄──────────┤
                                         ▼
                                  slots.jsonl ─► answers/ ─► questions_demo.jsonl
                                                                  │
persona/asker (script) ──────────────────────────────────────────►│
                                                                  ▼
                                                  validate_demo.py (schema + coverage + access)
                                                                  │
                                                                  ▼
                                                    review (reviewed=false → người duyệt)
```

## Task list (tóm tắt, chi tiết trong todo.md)

### Phase 1: Nền tảng
- Task 1: Xác nhận cách ingest và tín hiệu web search (đọc code, không viết code).
- Task 2: Dựng `demo_manifest.csv` + kiểm tra toàn vẹn 106 tài liệu.
- Task 3: Trích text từng PDF vào `question_work_demo/excerpts/`.

**Checkpoint 1:** `demo_manifest.csv` đủ 106 dòng, PDF đều đọc được, file gốc không đổi.

### Phase 2: Câu hỏi có căn cứ trong tài liệu
- Task 4: Tái dùng câu cũ hợp lệ (76 ứng viên) với level/persona tính lại.
- Task 5: Sinh `normal_guest` và `calculation` mới cho phòng chưa đủ.
- Task 6: Sinh `access_private` (28 tài liệu × 5 persona) và `access_public_cross`.
- Task 7: Sinh `advisory_single`, `advisory_multi`, `advisory_compare`.

**Checkpoint 2:** `validate_demo.py` báo 0 lỗi schema/access; các nhóm case 1–7 đạt mức tối thiểu.

### Phase 3: Câu hỏi không dựa tài liệu
- Task 8: Sinh `unanswerable`, `off_topic`, `social`.
- Task 9: Sinh `web_search` (chỉ cần kích hoạt node).

**Checkpoint 3:** Mọi case ở specs.md mục 4.1 đạt mức tối thiểu.

### Phase 4: Gộp, kiểm tra, bàn giao
- Task 10: Gộp thành `questions_demo.jsonl` + `questions_demo_review.csv`, chạy `validate_demo.py`, kiểm hash file gốc.
- Task 11: Báo cáo coverage và bàn giao để duyệt (`reviewed=false`).

**Checkpoint 4:** Toàn bộ success criteria ở specs.md mục 11 (trừ mục 6) đạt. Dừng để người duyệt trước khi ingest hoặc chạy pipeline.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Ngữ nghĩa level/`expect_visible` khác gateway hiện tại | Cao: `expect_visible` sai cả bộ access | Task 1 đối chiếu với code gateway trước khi sinh câu |
| Tài liệu có text ít hoặc bảng biểu nên khó sinh câu hỏi tốt | Trung bình | Ngưỡng `text_chars >= 1000`; slot nào thiếu evidence thì loại và bù từ tài liệu khác cùng phòng |
| PHONG_TC_KT chỉ có 1 tài liệu, TT_NGOAI_NGU 7 | Thấp | Chấp nhận; phủ phòng thiếu bằng câu `access_public_cross` từ phòng khác |
| Level giả khiến câu cũ không còn đúng ngữ cảnh | Trung bình | Quy tắc tái dùng ở specs.md mục 8; câu cũ ở tài liệu nay private được chuyển thành access và tính lại persona |
| Câu LLM sinh sai hoặc evidence không có trong tài liệu | Cao với RAGAS sau này | `validate_demo.py` kiểm evidence có trong text; `reviewed=false` cho tới khi người duyệt |
| Phân biệt SINGLE/MULTI sai | Trung bình | Dùng đúng định nghĩa ngữ pháp; thêm nhóm `advisory_compare` (câu đơn nhiều thực thể) để bắt lỗi nhầm |
| Vô tình sửa file gốc | Cao | Chỉ đọc file gốc; kiểm hash trước/sau ở Task 10 |

## Open Questions

Xem specs.md mục 13 (cách ingest, tín hiệu web search, ngữ nghĩa level 0/5, người duyệt).

---

## Phụ lục A: Danh sách tài liệu dùng cho demo

Nguồn: [selection.csv](selection.csv). `Lv` là level demo (`P` = public). `Q cũ` là số câu trong `questions.jsonl` đang tham chiếu tài liệu này (để tái dùng). Đường dẫn tính từ `D:\KLTN\dataset\`.

### PHONG_DAO_TAO (15 tài liệu: 12 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 20e1750624a1 | cfdf42e8-ee06-40d0-92e1-c32b8e7a04ab_M2.GH_DON DE NGHI MO TAI KHOAN SV (đã HTCTDT).pdf | 1 | P | general | 0 | files/phong-dao-tao/20e1750624a1.pdf |
| 2 | 232dacb7a8f1 | b6eab491-befa-4d08-a43b-72795a2cb29b_Don De Nghi Chuyen Diem (1).pdf | 2 | P | general | 0 | files/phong-dao-tao/232dacb7a8f1.pdf |
| 3 | 25a891093637 | IUH_ThuGioiThieu_2026.pdf | 1 | P | tuyen-sinh | 0 | files/tuyen-sinh/25a891093637.pdf |
| 4 | 26257f701710 | 8da952c4-c1e9-4365-85ac-e9e289452a68_DOn-phuc-khao.pdf | 1 | P | general | 1 | files/phong-dao-tao/26257f701710.pdf |
| 5 | 6398d268c1d5 | IUH_PhieuDangKyXetTuyenHB_2024_New.pdf | 2 | P | tuyen-sinh | 0 | files/tuyen-sinh/6398d268c1d5.pdf |
| 6 | 6c65d0162904 | 227fc761-b451-4fbe-8889-83a726bd49dd_03. Don DN xet cap HB TS (DT02).pdf | 1 | P | general | 1 | files/phong-dao-tao/6c65d0162904.pdf |
| 7 | 7659659b655c | IUH_PhieuDangKyXetTuyenUTX_2024_New.pdf | 2 | P | tuyen-sinh | 1 | files/tuyen-sinh/7659659b655c.pdf |
| 8 | 7e735808112b | 40cf1399-3d6a-4938-a7f9-fd58545a48ef_20. Don xin thi bo sung hoc phan.pdf | 1 | P | general | 1 | files/phong-dao-tao/7e735808112b.pdf |
| 9 | ad22132fee71 | 50679da0-79ab-43c2-86d6-e8227a6d765f_14_Don-de-nghi-xet-HB.TS_.pdf | 1 | P | general | 1 | files/phong-dao-tao/ad22132fee71.pdf |
| 10 | bc0962c377a7 | cong-thuc-xet-tuyen-iuh-2026.pdf | 1 | P | tuyen-sinh | 0 | files/tuyen-sinh/bc0962c377a7.pdf |
| 11 | edf5150a21c7 | HDSD_Thisinh_DKXT_T72025_IUH.pdf | 24 | P | tuyen-sinh | 1 | files/tuyen-sinh/edf5150a21c7.pdf |
| 12 | f9b339fb8896 | 52f4a8c3-8b70-4c51-b69b-608c07601b67_04. Giay Xac Nhan GV cac Truong lien ket_moi.pdf | 1 | P | general | 1 | files/phong-dao-tao/f9b339fb8896.pdf |
| 13 | 0f6e6dc782f2 | c0cfda33-c2b1-4940-865c-6812b4610b6e_4-DonXinChuyenNganh.pdf | 1 | L1 | general | 0 | files/phong-dao-tao/0f6e6dc782f2.pdf |
| 14 | 15a73a51c2ab | 152ffa6e-1ac2-439c-816a-75febd546433_4Tam-ngung-hoc_bao-luu.pdf | 2 | L2 | general | 0 | files/phong-dao-tao/15a73a51c2ab.pdf |
| 15 | 1d5c111c3eba | 34c41776-581a-4a23-9da7-24426b29cf76_0. Quy trình chỉnh sửa điểm, bổ sung điểm, xóa cột điểm.pdf | 3 | L3 | general | 0 | files/phong-dao-tao/1d5c111c3eba.pdf |

### PHONG_KHAO_THI_DBCL (10 tài liệu: 7 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 5a0063f8805c | thong_ke_tinh_hinh_phuc_khao_HK-I_20-21.pdf | 1 | P | general | 1 | files/phong-khao-thi-va-dam-bao-chat-luong/5a0063f8805c.pdf |
| 2 | 7565b29b32c6 | phuc-khao-HK3-2024-2025-dang-web.pdf | 1 | P | general | 1 | files/phong-khao-thi-va-dam-bao-chat-luong/7565b29b32c6.pdf |
| 3 | 813aff8bcfc8 | bao_cao_tinh-hinh-phuc-khao-HK3-2018-2019.pdf | 1 | P | general | 1 | files/phong-khao-thi-va-dam-bao-chat-luong/813aff8bcfc8.pdf |
| 4 | a13bafb44b2c | 06b_-PHU-LUC-CV-2085.pdf | 57 | P | general | 1 | files/phong-khao-thi-va-dam-bao-chat-luong/a13bafb44b2c.pdf |
| 5 | ba29b6723bb5 | Anti-terrorism-work-of-Industrial-University-of-Ho-Chi-Minh-City-in-2025.pdf | 11 | P | general | 1 | files/phong-khao-thi-va-dam-bao-chat-luong/ba29b6723bb5.pdf |
| 6 | d4755fc087e1 | IUH-Strategic-Quality-Enhancement-Plan-2026–2031.pdf | 14 | P | general | 1 | files/phong-khao-thi-va-dam-bao-chat-luong/d4755fc087e1.pdf |
| 7 | db73f5b955c6 | bao_cao_tinh-hinh-phuc-khao-HK1-2019-2020.pdf | 1 | P | general | 1 | files/phong-khao-thi-va-dam-bao-chat-luong/db73f5b955c6.pdf |
| 8 | 006f3af54506 | 3.-Decision-Internal-expenditure-regulations-2025.pdf | 37 | L1 | general | 0 | files/phong-khao-thi-va-dam-bao-chat-luong/006f3af54506.pdf |
| 9 | 0adc6f0ad4c9 | bao_cao_tinh-hinh-phuc-khao-HK2-2019-2020.pdf | 1 | L2 | general | 0 | files/phong-khao-thi-va-dam-bao-chat-luong/0adc6f0ad4c9.pdf |
| 10 | 0ae0376b3a09 | Appendix_1b_Guide_to_writing_learning_outcomes.pdf | 30 | L3 | general | 0 | files/phong-khao-thi-va-dam-bao-chat-luong/0ae0376b3a09.pdf |

### PHONG_TC_KT (1 tài liệu: 1 public, 0 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | faba80179b4e | HDSD Thanh toan va in hoa don HP.pdf | 7 | P | general | 1 | files/phong-tai-chinh-ke-toan/faba80179b4e.pdf |

### TT_NGOAI_NGU (7 tài liệu: 5 public, 2 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 46821b388123 | Ngay12-3-2022_Ca1.pdf | 9 | P | general | 1 | files/trung-tam-ngoai-ngu-tin-hoc/46821b388123.pdf |
| 2 | 6ffb3d82eb82 | KQ_PKngay24,25,26-3 va 4,5,6,7,8,12-4-2022.pdf | 2 | P | general | 0 | files/trung-tam-ngoai-ngu-tin-hoc/6ffb3d82eb82.pdf |
| 3 | 93b5b0734296 | Ngay12-3-2022_Ca2 (1).pdf | 9 | P | general | 0 | files/trung-tam-ngoai-ngu-tin-hoc/93b5b0734296.pdf |
| 4 | c02ede6611c8 | 03_ BanCamKetNopCCTH_NgoaiTruong.pdf | 1 | P | general | 1 | files/trung-tam-ngoai-ngu-tin-hoc/c02ede6611c8.pdf |
| 5 | fc9f1aebf447 | KQ_PK_Ngay14den23-03-2022.pdf | 2 | P | general | 1 | files/trung-tam-ngoai-ngu-tin-hoc/fc9f1aebf447.pdf |
| 6 | 3af8c7a6adb8 | 02_ HoSo&QuyTrinh_HauKiemCCNgoai_01_11_2025 (4).pdf | 1 | L1 | general | 0 | files/trung-tam-ngoai-ngu-tin-hoc/3af8c7a6adb8.pdf |
| 7 | 5d9e93b143e7 | KQ_PhucKhao_Ngay24den28-02 va 01den05-3.pdf | 1 | L3 | general | 0 | files/trung-tam-ngoai-ngu-tin-hoc/5d9e93b143e7.pdf |

### KHOA_CNTT (10 tài liệu: 7 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 37cdb8604e17 | HoidongPoster_HK2.pdf | 1 | P | general | 1 | files/khoa-cong-nghe-thong-tin/37cdb8604e17.pdf |
| 2 | 37f9d88f8634 | KetQua_Pretest_Thang12_2024_CS 2.pdf | 1 | P | general | 1 | files/khoa-cong-nghe-thong-tin/37f9d88f8634.pdf |
| 3 | 4e1222ceff00 | Diểm Pretest HK2_2023_2024 pdf.pdf | 1 | P | general | 1 | files/khoa-cong-nghe-thong-tin/4e1222ceff00.pdf |
| 4 | 9a0b06450fb2 | PB KLTNHK22025.pdf | 1 | P | general | 1 | files/khoa-cong-nghe-thong-tin/9a0b06450fb2.pdf |
| 5 | a127a708a486 | JOB DESCRIPTION_SAP Fresher LOGISTIC.pdf | 2 | P | general | 1 | files/khoa-cong-nghe-thong-tin/a127a708a486.pdf |
| 6 | ecedf7299d79 | BT NHAP MON LT C_2015.pdf | 46 | P | general | 1 | files/khoa-cong-nghe-thong-tin/ecedf7299d79.pdf |
| 7 | f22eeb395678 | CTDT nganh Cong nghe Thong tin_K16.pdf | 5 | P | general | 1 | files/khoa-cong-nghe-thong-tin/f22eeb395678.pdf |
| 8 | 00522b067eaa | Ke hoach Pretest dot thang 7_2026(1).pdf | 1 | L1 | general | 0 | files/khoa-cong-nghe-thong-tin/00522b067eaa.pdf |
| 9 | 036645574654 | BaiTapThucHanhCSDL_Chi_(2015).pdf | 26 | L2 | general | 0 | files/khoa-cong-nghe-thong-tin/036645574654.pdf |
| 10 | 1f196efd97e6 | GCS tour 29_03_2017.pdf | 1 | L3 | general | 1 | files/khoa-cong-nghe-thong-tin/1f196efd97e6.pdf |

### VIEN_TAI_CHINH_KE_TOAN (10 tài liệu: 7 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 25999d44b549 | handbook for student-compressed.pdf | 50 | P | general | 4 | files/vien-tai-chinh-ke-toan/25999d44b549.pdf |
| 2 | 3833d01f616f | Chuong trinh khung-TCDN 2020.pdf | 6 | P | general | 1 | files/vien-tai-chinh-ke-toan/3833d01f616f.pdf |
| 3 | 4989ba2da31b | Ban mo ta CTDT 2020_KIEM TOAN.pdf | 59 | P | general | 1 | files/vien-tai-chinh-ke-toan/4989ba2da31b.pdf |
| 4 | 766bf6452c4d | Chuẩn dầu ra CTDT 2020_TCNH.pdf | 3 | P | general | 1 | files/vien-tai-chinh-ke-toan/766bf6452c4d.pdf |
| 5 | 783cef8626fc | COMPARISONS ELOs 2016 TIENG VIET 25-06-2019(2).pdf | 2 | P | general | 1 | files/vien-tai-chinh-ke-toan/783cef8626fc.pdf |
| 6 | c9cc421ea93a | CTDT 2020_KIEM TOAN.pdf | 11 | P | general | 1 | files/vien-tai-chinh-ke-toan/c9cc421ea93a.pdf |
| 7 | eeafc0706f82 | CTDT KT - 2022.pdf | 4 | P | general | 1 | files/vien-tai-chinh-ke-toan/eeafc0706f82.pdf |
| 8 | 1dbdf35075c6 | RUBRICS-Intership2.pdf | 7 | L1 | general | 1 | files/vien-tai-chinh-ke-toan/1dbdf35075c6.pdf |
| 9 | 277cab361c0a | Ban mo ta CTDT cao hoc 2022.pdf | 55 | L2 | general | 1 | files/vien-tai-chinh-ke-toan/277cab361c0a.pdf |
| 10 | 2e108eb62a4a | Ban mo ta CTDT cao hoc 2016.pdf | 30 | L3 | general | 1 | files/vien-tai-chinh-ke-toan/2e108eb62a4a.pdf |

### PHONG_QLKH_HTQT (10 tài liệu: 7 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 1c87e1bb4334 | Thong-bao-nhan-ho-so_hoc-bong-khcn-du-hoc-cua-vingroup_2020-21-2021-22_vf.pdf | 11 | P | general | 1 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/1c87e1bb4334.pdf |
| 2 | 277ad32ab34a | 10_Mau_1_Dang_Huu_Phuc.pdf | 17 | P | general | 0 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/277ad32ab34a.pdf |
| 3 | 2a28a6168eaf | Huớng dẫn Dang ky tổ chức hộ thảo.pdf | 9 | P | general | 1 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/2a28a6168eaf.pdf |
| 4 | 5fcc64d76f74 | 01_Mau_1_Huynh_Trung_Hieu.pdf | 21 | P | general | 1 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/5fcc64d76f74.pdf |
| 5 | 6e7ab86be4ee | 09_Mau_1_Tran_Thanh_Ngoc.pdf | 17 | P | general | 1 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/6e7ab86be4ee.pdf |
| 6 | 7f3adf63b7f6 | The IUH Exchange Student Handbook provide11111.pdf | 20 | P | general | 1 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/7f3adf63b7f6.pdf |
| 7 | b541e0cd4d71 | HUỚNG DẪN DANG KY DỀ TAI NCKH CẤP TRUỜNG IUH - 2026.pdf | 3 | P | general | 4 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/b541e0cd4d71.pdf |
| 8 | 002b0f2d3165 | 2020 HEAT Graduate Program_Attachment2(Final)_Korean Council for University Education.pdf | 46 | L1 | general | 0 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/002b0f2d3165.pdf |
| 9 | 018e82f3519f | 05_Mau_1_nguyen_Phuc_Hung.pdf | 13 | L2 | general | 0 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/018e82f3519f.pdf |
| 10 | 0903ff94e89b | Huớng dẫn thanh toan bai bao ISIScopus.pdf | 10 | L3 | general | 0 | files/phong-quan-ly-khoa-hoc-va-hop-tac-quoc-te/0903ff94e89b.pdf |

### KHOA_NGOAI_NGU (10 tài liệu: 7 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 18e24bbb5a5a | ilovepdf_merged(7).pdf | 10 | P | general | 0 | files/khoa-ngoai-ngu/18e24bbb5a5a.pdf |
| 2 | 1e96fe119370 | ilovepdf_merged.pdf | 7 | P | general | 0 | files/khoa-ngoai-ngu/1e96fe119370.pdf |
| 3 | 83a97513ac19 | 19_12 DANH SACH SV THI BỔ SUNG HK1.pdf | 2 | P | general | 1 | files/khoa-ngoai-ngu/83a97513ac19.pdf |
| 4 | 8565e9cc9fca | 16_ 2111443- interpretation 1 25-6-2019 checked.pdf | 4 | P | general | 1 | files/khoa-ngoai-ngu/8565e9cc9fca.pdf |
| 5 | acbfa996ca3d | PS 2024 version.pdf | 38 | P | general | 1 | files/khoa-ngoai-ngu/acbfa996ca3d.pdf |
| 6 | cbaf33bff641 | 4_ THONG BAO MUA SACH- DH CONG NGHIEP TP HCM -4_2025- new.pdf | 2 | P | general | 1 | files/khoa-ngoai-ngu/cbaf33bff641.pdf |
| 7 | fa48effe7ca7 | THONG TIN CHỨNG CHỈ NGOẠI NGỮ MIỄN TIẾNG ANH DẦU VAO (Responses)(2).pdf | 22 | P | general | 1 | files/khoa-ngoai-ngu/fa48effe7ca7.pdf |
| 8 | 04e829a52e44 | DS THI BỔ SUNG new.pdf | 13 | L1 | general | 0 | files/khoa-ngoai-ngu/04e829a52e44.pdf |
| 9 | 08ad47a6d5e1 | ilovepdf_merged.pdf | 2 | L2 | general | 0 | files/khoa-ngoai-ngu/08ad47a6d5e1.pdf |
| 10 | 15e4977edeac | DS THI BỔ SUNG MON TIẾNG ANH 1 VA TIẾNG ANH 2.pdf | 1 | L3 | general | 0 | files/khoa-ngoai-ngu/15e4977edeac.pdf |

### KHOA_QTKD (10 tài liệu: 7 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 1a789e8bf51a | CHUONG-TRINH-KHUNG-THS-QTKD-2022.pdf | 1 | P | general | 1 | files/khoa-quan-tri-kinh-doanh/1a789e8bf51a.pdf |
| 2 | 2e379acc6ddd | Quy-che-tuyen-sinh-va-dao-tao-Tien-si-2023.pdf | 39 | P | general | 1 | files/khoa-quan-tri-kinh-doanh/2e379acc6ddd.pdf |
| 3 | 3199cf8d42ec | Khung-chuong-trinh-SCM.pdf | 3 | P | general | 1 | files/khoa-quan-tri-kinh-doanh/3199cf8d42ec.pdf |
| 4 | 387672d6ea88 | Khung-chuong-trinh-NNL.pdf | 3 | P | general | 1 | files/khoa-quan-tri-kinh-doanh/387672d6ea88.pdf |
| 5 | 3b393125812f | PL2.pdf | 1 | P | general | 1 | files/khoa-quan-tri-kinh-doanh/3b393125812f.pdf |
| 6 | 5770bc1a0d75 | Quy-che-tien-si-IUH-2017-Final2-1.pdf | 28 | P | general | 1 | files/khoa-quan-tri-kinh-doanh/5770bc1a0d75.pdf |
| 7 | 5a4d341128ee | 4_-Don-xin-huy-bot-hoc-phan-vua-dang-ky.pdf | 1 | P | general | 1 | files/khoa-quan-tri-kinh-doanh/5a4d341128ee.pdf |
| 8 | 00237112e863 | Khung-chuong-trinh-QTKD.pdf | 3 | L1 | general | 1 | files/khoa-quan-tri-kinh-doanh/00237112e863.pdf |
| 9 | 1101a31ce7cd | PL1-1.pdf | 6 | L2 | general | 1 | files/khoa-quan-tri-kinh-doanh/1101a31ce7cd.pdf |
| 10 | 148a0aa71759 | ts1.pdf | 1 | L3 | general | 1 | files/khoa-quan-tri-kinh-doanh/148a0aa71759.pdf |

### PHONG_TO_CHUC_HANH_CHINH (8 tài liệu: 8 public, 0 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 24075ba242e7 | _So 29 - Web.pdf | 6 | P | general | 1 | files/truong-trang-chinh/24075ba242e7.pdf |
| 2 | 2434418d90b3 | Tap chi KHCN - So 24.pdf | 6 | P | general | 1 | files/truong-trang-chinh/2434418d90b3.pdf |
| 3 | 50bdc3a9c2d0 | TapchiKHCN-Vol23.pdf | 5 | P | general | 1 | files/truong-trang-chinh/50bdc3a9c2d0.pdf |
| 4 | 55df0dd76d43 | 02_Huong_dan_dang_ky_noi_tru_nam_hoc_2026_2027.pdf | 5 | P | general | 0 | files/truong-trang-chinh/55df0dd76d43.pdf |
| 5 | 812f9912e3d4 | _Tap chi KHCN - So 26 - Bia.pdf | 6 | P | general | 0 | files/truong-trang-chinh/812f9912e3d4.pdf |
| 6 | a0c6aad0af8b | _So 27 - Web.pdf | 6 | P | general | 0 | files/truong-trang-chinh/a0c6aad0af8b.pdf |
| 7 | a566d0b4acf8 | QuyTrinhNhapHocTongThe (1).pdf | 1 | P | general | 0 | files/truong-trang-chinh/a566d0b4acf8.pdf |
| 8 | b1398d48dcab | Tap chi KHCN - So 25.pdf | 6 | P | general | 0 | files/truong-trang-chinh/b1398d48dcab.pdf |

### TT_QUAN_TRI_HE_THONG (10 tài liệu: 7 public, 3 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | 258192435053 | huongdanK22thitructuyentienganhdauvao.pdf | 9 | P | general | 1 | files/trung-tam-quan-tri-he-thong/258192435053.pdf |
| 2 | 3c2ab4abf26b | HD_SVK20_ThisathachTA.pdf | 11 | P | general | 1 | files/trung-tam-quan-tri-he-thong/3c2ab4abf26b.pdf |
| 3 | 4dc06358f8e3 | HuongDanTruyCapWiFiIUH21062026.pdf | 7 | P | general | 0 | files/trung-tam-quan-tri-he-thong/4dc06358f8e3.pdf |
| 4 | 6418d1537459 | Huong_dan_ky_so_LLKH_SMIA_V1_1.pdf | 8 | P | general | 1 | files/trung-tam-quan-tri-he-thong/6418d1537459.pdf |
| 5 | 755c97444da3 | GV_HuongDanGiangVienSuDungMSTeams.pdf | 19 | P | general | 0 | files/trung-tam-quan-tri-he-thong/755c97444da3.pdf |
| 6 | aa032621247c | SV_MotSoLoiThuongGapKhiThiTrucTuyen091121.pdf | 3 | P | general | 1 | files/trung-tam-quan-tri-he-thong/aa032621247c.pdf |
| 7 | e961218a2ada | GV_Huongdangiangvienkhoiphucmatkhaucongthongtin020323.pdf | 13 | P | general | 4 | files/trung-tam-quan-tri-he-thong/e961218a2ada.pdf |
| 8 | 15bdfd65eb05 | huongdancongcunenpdfcuctot.pdf | 5 | L1 | general | 0 | files/trung-tam-quan-tri-he-thong/15bdfd65eb05.pdf |
| 9 | 22d536ff4472 | SV_Huongdansinhvienkhoiphucmatkhaucongthongtin020323.pdf | 11 | L2 | general | 0 | files/trung-tam-quan-tri-he-thong/22d536ff4472.pdf |
| 10 | 3f362d7f351f | HD_Dang_ky_di_nuớc_ngoai_V1_1.pdf | 15 | L3 | general | 0 | files/trung-tam-quan-tri-he-thong/3f362d7f351f.pdf |

### BAN_QUAN_LY_KTX (5 tài liệu: 3 public, 2 private)

| # | file_id | Tên file | Trang | Lv | Nhóm | Q cũ | local_path |
|---|---|---|---|---|---|---|---|
| 1 | c07f3426071e | HuongDanquytrinhdkktxonline _ Tan sinh vien 2025.pdf | 5 | P | general | 1 | files/phong-quan-ly-ky-tuc-xa/c07f3426071e.pdf |
| 2 | d3f9989a0017 | Cẩm nang PCCC.pdf | 7 | P | general | 0 | files/phong-quan-ly-ky-tuc-xa/d3f9989a0017.pdf |
| 3 | fa654409799b | Huớng dẫn dang ky nội tru nam học 2026-2027 (Danh cho sinh vien khoa mới nhập học).pdf | 6 | P | general | 1 | files/phong-quan-ly-ky-tuc-xa/fa654409799b.pdf |
| 4 | 0684ac95615f | Tuyen truyền về việc lừa dảo quan mạng.pdf | 10 | L1 | general | 0 | files/phong-quan-ly-ky-tuc-xa/0684ac95615f.pdf |
| 5 | d356f35e33b8 | HuongDanquytrinhdkktxonline.pdf | 5 | L3 | general | 0 | files/phong-quan-ly-ky-tuc-xa/d356f35e33b8.pdf |

