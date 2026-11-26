# Brief: viết tài liệu giả lập cho bộ test phân quyền UniSage

Mục tiêu: tạo tài liệu PDF tiếng Việt (có dấu đầy đủ) về học vụ / NCKH / quy định cho giảng viên & sinh viên
của Trường Đại học Công nghiệp TP. HCM, dùng để test RAG + phân quyền theo phòng ban và cấp độ truy cập.
Danh mục và chủ đề từng tài liệu: `/home/huy/Main/unisage-gateway/dataset/access-control/catalog.json`.

## Yêu cầu nội dung
- Nội dung HOÀN TOÀN GIẢ LẬP, không chép văn bản có thật. Mọi con số, số hiệu văn bản, tên người, mã đề tài,
  mức tiền, ngày tháng phải do bạn tự đặt, cụ thể và đặc thù (ví dụ "Số: 2471/QĐ-ĐHCN", "mã đề tài CNPM-26-07",
  "1.850.000 đồng/người/tháng") để không thể tìm thấy trên web (iuh.edu.vn và các subdomain).
  Tên người: dùng tên Việt giả lập thông thường, không dùng tên người nổi tiếng hay lãnh đạo thật của trường.
- Mỗi tài liệu đủ dài để render ra **ít nhất 6 trang A4** (khoảng 3.000–3.800 từ): có căn cứ, các chương/điều/khoản,
  ít nhất 2 bảng có số liệu, phụ lục nếu cần. Văn phong hành chính Việt Nam. Không lặp đoạn để độn trang.
- Tài liệu private: ghi `confidential` như "TÀI LIỆU NỘI BỘ – CẤP ĐỘ {n} – {tên bộ môn}" (cấp 0: "TÀI LIỆU NỘI BỘ – {tên bộ môn}").
  `issuer` là bộ môn/khoa tương ứng, `parent_org` là "TRƯỜNG ĐẠI HỌC CÔNG NGHIỆP TP. HỒ CHÍ MINH" (hoặc "KHOA ..." khi issuer là bộ môn).
  Tài liệu public: issuer "TRƯỜNG ĐẠI HỌC CÔNG NGHIỆP TP. HỒ CHÍ MINH", parent_org "BỘ CÔNG THƯƠNG", confidential = null.
- Nội dung mỗi tài liệu phải có ít nhất 5 "sự kiện độc nhất" (con số/tên/mốc) chỉ có trong tài liệu đó — sẽ dùng làm câu hỏi test.
  Tài liệu cùng bộ môn không được trùng các sự kiện đó với nhau.

## Định dạng
Viết spec JSON theo docstring của `/home/huy/Main/unisage-gateway/dataset/access-control/tools/render_pdf.py`
vào `/home/huy/Main/unisage-gateway/dataset/access-control/specs/{doc_id}.json`.
- `file_name`: `{doc_id}_{slug-khong-dau}.pdf`.
- `questions`: đúng 3 câu hỏi tự nhiên (như sinh viên/giảng viên hỏi chatbot), mỗi câu trả lời được bằng 1 sự kiện độc nhất;
  `expected_answer` ngắn gọn; `evidence` là câu trích NGUYÊN VĂN có trong tài liệu. Câu hỏi không được nêu mã doc_id.
- Nên sinh spec bằng một script Python nhỏ (đặt trong scratchpad, KHÔNG đặt trong repo) để tránh lỗi escape JSON, hoặc Write JSON trực tiếp.

## Render và kiểm tra
```
PY=/tmp/claude-1000/-home-huy-Main/9fb3dd98-0a20-487b-bca3-2749548c927d/scratchpad/pdfenv/bin/python
D=/home/huy/Main/unisage-gateway/dataset/access-control
$PY $D/tools/render_pdf.py $D/specs/{doc_id}.json --out $D/files
pdfinfo $D/files/<file>.pdf | grep Pages     # phải >= 6
pdftotext $D/files/<file>.pdf - | grep -F "<evidence>"   # mỗi evidence phải tìm thấy (lưu ý ngắt dòng)
```
Nếu < 6 trang thì viết thêm nội dung thật (điều khoản, bảng, phụ lục), không độn.
Không sửa render_pdf.py, catalog.json hay file của tài liệu khác.

## Báo cáo lại (ngắn)
Mỗi doc: file name, số trang, tiêu đề, 3 câu hỏi. Ghi chú nếu có evidence không grep được.
