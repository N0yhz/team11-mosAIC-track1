# 📋 Danh Sách Hạng Mục Dự Án (TODO & Backlog)
**Dự án:** Proposal Scorer AI — SiviHack 2026 (Sponsor: FPT Software Europe)  
**Nhóm:** Team 11 - mosAIC Track 1  
**Trạng thái cập nhật:** 2026-09-18

Tài liệu này ghi nhận các hạng mục công việc được bảo lưu, tạm hoãn hoặc lên kế hoạch cho các giai đoạn tiếp theo theo thỏa thuận phát triển.

---

## ✅ Vấn đề 1: Bảng Chấm 7 Tiêu Chí Rubric (Appendix A) — [TRẠNG THÁI: HOÀN THÀNH]
> **Trạng thái:** Đã hoàn thành! Đã bóc tách core function từ branch `dev/atl` vào `backend/support_library/rubric_evaluator/`, chạy độc lập và hiển thị bảng điểm 7 chiều phía trên phần so sánh RFP vs Proposal.

### Bối cảnh & Yêu cầu từ Đề bài FPT Software:
Theo **Appendix A (Additional Scoring Criteria)** trong tài liệu đề bài, ngoài việc bóc tách các yêu cầu chức năng cụ thể của RFP, hệ thống cần chấm điểm tổng thể đề xuất (thang điểm 1–5) kèm nhận xét ngắn cho 7 chiều chất lượng hồ sơ thầu:
1. **Problem Understanding** (Thấu hiểu bài toán)
2. **Scope & Deliverables Clarity** (Độ rõ ràng phạm vi & bàn giao)
3. **Pricing Clarity** (Độ minh bạch về giá)
4. **Timeline Clarity** (Độ rõ ràng về tiến độ)
5. **Completeness vs. RFP Requirements** (Độ đầy đủ so với RFP)
6. **Tone & Persuasiveness** (Văn phong & Sức thuyết phục)
7. **Risk / Assumptions Transparency** (Minh bạch rủi ro & giả định)

### Đã triển khai:
- [x] Tạo module độc lập `backend/support_library/rubric_evaluator/` chứa:
  - `models.py`: `Criterion`, `CriterionScore`, `ScoringResult` với các thuộc tính tính toán tự động (`total_score`, `max_total_score`, `average_score`, `percentage`).
  - `criteria.py`: 7 tiêu chí chuẩn hóa theo Appendix A của FPT Software.
  - `scorer.py`: function `evaluate_rubric_score(proposal_text, rfp_text, proposal_name)` tích hợp Google GenAI SDK (`gemini-2.5-flash`), kèm fallback heuristic an toàn khi quota hoặc mạng gặp sự cố.
- [x] Tách riêng rẽ hoàn toàn:
  - `evaluate_response_stage`: chuyên trách ma trận so sánh RFP vs Proposal, trích dẫn nguồn (citations) và đề xuất sửa lỗi (issues & fixes).
  - `evaluate_rubric_score`: chuyên trách chấm 7 chiều chất lượng độc lập của Proposal.
- [x] Backend `POST /api/feedback` và `POST /api/evaluate` gọi song song cả 2 function và trả về `rubric_evaluation` cùng với `response_feedback`.
- [x] Frontend hiển thị bảng điểm **7-Dimension Proposal Quality Rubric Assessment** ở **ngay phía trên** bảng so sánh Criteria Compliance Scorecard trong Step 4:
  - Tổng điểm và điểm trung bình (thang điểm 5.0), xếp hạng chất lượng Tier A+/A/B/C.
  - Tóm tắt đánh giá tổng quan của giám khảo (Evaluator Synthesis Commentary).
  - 7 thẻ tiêu chí trực quan với thanh tiến trình màu sắc, điểm số và nhận xét bằng chứng cụ thể.

---

## ✅ Vấn đề 5: Hỗ Trợ Dán Văn Bản Trực Tiếp (Paste Input) — [TRẠNG THÁI: HOÀN THÀNH]
> **Trạng thái:** Đã hoàn thành! Đã hỗ trợ chuyển đổi linh hoạt giữa Upload File và Paste Text trực tiếp cho cả RFP (Step 1) và Proposal (Step 3).

### Yêu cầu từ Đề bài:
- Ban giám khảo có thể mang dữ liệu kiểm thử mới (*unseen validation data*) đến buổi chấm thi và muốn **paste trực tiếp đoạn text RFP hoặc Proposal** từ clipboard vào trình duyệt thay vì phải tạo file trên máy.

### Đã triển khai:
- [x] Thêm nút chuyển đổi tab trực quan: [📁 Upload File] | [📝 Paste Text] ở cả Step 1 (RFP) và Step 3 (Proposal).
- [x] Tích hợp khung soạn thảo / dán văn bản kích thước rộng, hỗ trợ đếm ký tự, số từ và nút Clear text nhanh.
- [x] Backend hỗ trợ tiếp nhận cả raw text/markdown thông qua các trường form 
fp_text và 
esponse_text tại các endpoint /api/extract-criteria, /api/feedback, và /api/evaluate.
- [x] Tự động đồng bộ với tính năng xuất bản thảo đề xuất hoàn thiện (Revised Proposal) tại Step 5.

---

## ✅ Vấn đề 6: Xử Lý File PDF & PowerPoint PDF (Bonus Criterion) — [TRẠNG THÁI: HOÀN THÀNH]
> **Trạng thái:** Đã hoàn thành và tích hợp trực tiếp vào module `support_library.extractors` và pipeline đánh giá backend.

### Yêu cầu từ Đề bài:
- **Bonus Criterion:** Đánh giá cao các đội có khả năng xử lý tài liệu thực tế dài và phức tạp hơn, chẳng hạn như hồ sơ RFP dạng file PDF hoặc Proposal xuất từ PowerPoint sang PDF.

### Đã triển khai:
- [x] Đã cấu trúc module `support_library/extractors/` sử dụng `PyMuPDF` (`pymupdf`), `pandas`, `openpyxl` tối ưu tốc độ và trích xuất bảng biểu.
- [x] Tự động nhận diện slide thuyết trình PowerPoint PDF (khổ 16:9 / landscape) và gắn nhãn `Slide X` thay vì `Page X`.
- [x] Tích hợp thuật toán chống trùng lặp văn bản khi có bảng (`_bbox_overlaps_table`) và chuẩn hoá ký tự (ligatures, bullets, de-hyphenation).
- [x] Tích hợp tự động vào `backend/pipeline.py` (`_convert_to_markdown_placeholder`) và các API endpoint tại `backend/main.py`: tự động nhận dạng định dạng file cho cả RFP lẫn Vendor Proposal.
- [x] Cập nhật Frontend Step 1 và Step 3 hỗ trợ kéo thả / chọn file `.pdf` với giao diện thông báo định dạng trực quan.

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
