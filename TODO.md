# 📋 Danh Sách Hạng Mục Dự Án (TODO & Backlog)
**Dự án:** Proposal Scorer AI — SiviHack 2026 (Sponsor: FPT Software Europe)  
**Nhóm:** Team 11 - mosAIC Track 1  
**Trạng thái cập nhật:** 2026-09-18

Tài liệu này ghi nhận các hạng mục công việc được bảo lưu, tạm hoãn hoặc lên kế hoạch cho các giai đoạn tiếp theo theo thỏa thuận phát triển.

---

## 📌 Vấn đề 1: Bảng Chấm 7 Tiêu Chí Rubric (Appendix A) — [TRẠNG THÁI: PASS / DEFERRED]
> **Trạng thái:** Tạm thời đánh dấu **PASS** trong hệ thống hiện tại và sẽ được hoàn thiện ở Phase tiếp theo.

### Bối cảnh & Yêu cầu từ Đề bài FPT Software:
Theo **Appendix A (Additional Scoring Criteria)** trong tài liệu đề bài, ngoài việc bóc tách các yêu cầu chức năng cụ thể của RFP, hệ thống cần chấm điểm tổng thể đề xuất (thang điểm 1–5 hoặc traffic-light) kèm nhận xét ngắn cho 7 chiều chất lượng hồ sơ thầu:
1. **Problem Understanding** (Thấu hiểu bài toán): Đề xuất có phản ánh đúng vấn đề và mục tiêu thực tế của khách hàng từ RFP không, hay chỉ là một bài chào hàng chung chung?
2. **Scope & Deliverables Clarity** (Độ rõ ràng phạm vi & bàn giao): Các hạng mục bàn giao có cụ thể, không mập mờ không? Đã rõ ràng cái gì bao gồm và cái gì KHÔNG bao gồm chưa?
3. **Pricing Clarity** (Độ minh bạch về giá): Giá cả có được nêu rõ, bóc tách hạng mục dễ hiểu không (thay vì mơ hồ hoặc 'báo giá sau')?
4. **Timeline Clarity** (Độ rõ ràng về tiến độ): Các mốc thời gian có cụ thể với ngày tháng/tuần rõ ràng không (thay vì 'trong thời gian sớm nhất')?
5. **Completeness vs. RFP Requirements** (Độ đầy đủ so với RFP): Đề xuất có giải quyết được mọi yêu cầu mà RFP đã nêu rõ không?
6. **Tone & Persuasiveness** (Văn phong & Sức thuyết phục): Văn bản có tự tin, hướng đến khách hàng và chuyên nghiệp không (tránh văn mẫu sáo rỗng)?
7. **Risk / Assumptions Transparency** (Minh bạch rủi ro & giả định): Các giả định, phụ thuộc kỹ thuật hoặc rủi ro có được nêu rõ thay vì giấu đi không?

### Kế hoạch Triển khai trong tương lai:
- [ ] Thêm schema cấu trúc `rubric_scoring` vào prompt của `lvl2_feedback_response.py`.
- [ ] Tính toán điểm Rubric Score trung bình (ví dụ: Overall Rubric: 3.8 / 5.0).
- [ ] Thiết kế bảng Rubric Scorecard trực quan trên giao diện Frontend với thanh tiến trình màu và nhận xét tương ứng từng tiêu chí.

---

## 📌 Vấn đề 5: Hỗ Trợ Dán Văn Bản Trực Tiếp (Paste Input) — [TRẠNG THÁI: BACKLOG]
> **Trạng thái:** Tạm hoãn. Hiện tại hệ thống hỗ trợ upload file (.md, .txt) và tải dữ liệu 4 kịch bản Preset thực tế.

### Yêu cầu từ Đề bài:
- Ban giám khảo có thể mang dữ liệu kiểm thử mới (*unseen validation data*) đến buổi chấm thi và muốn **paste trực tiếp đoạn text RFP hoặc Proposal** từ clipboard vào trình duyệt thay vì phải tạo file trên máy.

### Kế hoạch Triển khai:
- [ ] Thêm tab chuyển đổi: [📁 Upload File] | [📝 Paste Markdown/Text] ở cả Stage 1 (RFP) và Stage 2 (Proposal).
- [ ] Backend hỗ trợ tiếp nhận cả raw_text qua multipart form hoặc JSON body.

---

## 📌 Vấn đề 6: Xử Lý File PDF & PowerPoint PDF (Bonus Criterion) — [TRẠNG THÁI: BACKLOG]
> **Trạng thái:** Tạm hoãn. Hiện tại hệ thống xử lý định dạng Markdown (.md) và Plaintext (.txt).

### Yêu cầu từ Đề bài:
- **Bonus Criterion:** Đánh giá cao các đội có khả năng xử lý tài liệu thực tế dài và phức tạp hơn, chẳng hạn như hồ sơ RFP dạng file PDF hoặc Proposal xuất từ PowerPoint sang PDF.

### Kế hoạch Triển khai:
- [ ] Cài đặt thư viện đọc PDF nhẹ như `pypdf` hoặc `pdfplumber` vào `backend/requirements.txt`.
- [ ] Tận dụng khả năng xử lý multimodal nguyên bản của Google Gemini API (`types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf')`) để phân tích trực tiếp PDF mà không làm mất cấu trúc bảng biểu.
- [ ] Thay thế hàm NotImplementedError trong `backend/pipeline.py` bằng pipeline trích xuất nội dung PDF.

---

## ✅ Vấn đề 7: Nhóm 4 Kịch Bản Preset (Weak, Medium, Strong, Overpromise) — [TRẠNG THÁI: HOÀN THÀNH]
> **Trạng thái:** Đã hoàn thành và tích hợp trực tiếp vào Step 1 cùng cơ chế Session Hygiene.

### Đã triển khai:
- [x] Backend endpoint `GET /api/presets/{preset_key}` (`weak`, `medium`, `strong`, `overpromise`): tải tài liệu thô thực tế từ `data/sample_data/rfp_nordframe.md` và `data/response/response_*.md`.
- [x] Frontend giao diện 4 nút Preset màu sắc tương ứng:
  - 🔴 `proposal_1_weak (BrightPath)`: Bỏ qua hoàn toàn PostgreSQL, không có SLA -> Đánh giá: Non-Compliant, Grade F / Reject.
  - 🟡 `proposal_2_medium (Clarion)`: Baseline benchmark, tuân thủ một phần.
  - 🟢 `proposal_3_strong (Apex)`: Tuân thủ kỹ thuật toàn diện, điểm cao.
  - ⚠️ `proposal_4_overpromise (Vantix)`: Rủi ro cam kết quá đà, vi phạm các mốc khả thi.
- [x] Tích hợp Session Reset: Mỗi khi chọn preset hoặc bấm "Reset & Start Over", hệ thống gọi `POST /api/session/reset` xóa sạch mọi dữ liệu đánh giá cũ, đảm bảo phân tích mới 100% không tái sử dụng dữ liệu rác.
