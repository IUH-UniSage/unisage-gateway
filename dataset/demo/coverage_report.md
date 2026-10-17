# Báo cáo coverage bộ demo

Ngày: 04-10-2026 · Tổng: **276** dòng câu hỏi · `reviewed=false` toàn bộ · 114 dòng có `reused_from` (tái dùng câu cũ) · 88/106 tài liệu được tham chiếu.

## Theo case

| Case | Số dòng |
|---|---|
| access_private | 140 |
| normal_guest | 54 |
| advisory_multi | 14 |
| access_public_cross | 12 |
| advisory_single | 12 |
| calculation | 10 |
| unanswerable | 10 |
| off_topic | 8 |
| social | 6 |
| web_search | 6 |
| advisory_compare | 4 |

## access_private theo persona (140 dòng = 28 tài liệu private × 5 persona)

| Persona | expect_visible | Số dòng |
|---|---|---|
| guest | False | 28 |
| other_department_max_level | False | 28 |
| same_department_exact_level | True | 28 |
| same_department_one_level_below | False | 28 |
| wildcard_max_level | True | 28 |

Số tài liệu private được kiểm tra theo level: L1: 10, L2: 8, L3: 10

## Theo phòng ban

| Phòng ban | Tổng | access_private | access_public_cross | advisory_compare | advisory_multi | advisory_single | calculation | normal_guest | off_topic | social | unanswerable | web_search |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (không gắn phòng) | 14 |  |  |  |  |  |  |  | 8 | 6 |  |  |
| BAN_QUAN_LY_KTX | 15 | 10 | 1 |  | 1 |  |  | 2 |  |  | 1 |  |
| KHOA_CNTT | 25 | 15 | 1 |  | 1 |  | 1 | 6 |  |  | 1 |  |
| KHOA_NGOAI_NGU | 26 | 15 | 1 |  | 2 | 3 |  | 5 |  |  |  |  |
| KHOA_QTKD | 30 | 15 | 1 | 2 | 1 | 2 | 6 | 3 |  |  |  |  |
| PHONG_DAO_TAO | 31 | 15 | 1 |  | 2 | 3 | 1 | 6 |  |  | 1 | 2 |
| PHONG_KHAO_THI_DBCL | 29 | 15 | 1 |  | 1 | 3 |  | 7 |  |  | 1 | 1 |
| PHONG_QLKH_HTQT | 26 | 15 | 1 |  |  | 1 | 1 | 6 |  |  | 1 | 1 |
| PHONG_TC_KT | 4 |  | 1 |  |  |  |  | 2 |  |  | 1 |  |
| PHONG_TO_CHUC_HANH_CHINH | 7 |  | 1 |  | 1 |  |  | 3 |  |  | 1 | 1 |
| TT_NGOAI_NGU | 17 | 10 | 1 |  | 1 |  |  | 3 |  |  | 1 | 1 |
| TT_QUAN_TRI_HE_THONG | 25 | 15 | 1 | 1 | 2 |  |  | 5 |  |  | 1 |  |
| VIEN_TAI_CHINH_KE_TOAN | 27 | 15 | 1 | 1 | 2 |  | 1 | 6 |  |  | 1 |  |

## Câu cần người duyệt

Toàn bộ `reviewed=false`. Nên ưu tiên duyệt: `advisory_multi`, `advisory_compare` (đúng định nghĩa SINGLE/MULTI), `unanswerable` (không vô tình có đáp án trong kho), `web_search` (chỉ cần kích hoạt node).
