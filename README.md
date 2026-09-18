# Proposal Scorer AI

> **Dự án:** Proposal Scorer AI — SiviHack 2026 (Track 1: Proposal Scorer - FPT Software Europe)  
> **Nhóm thực hiện:** Team 11 - mosAIC  

Hệ thống hỗ trợ phân tích Yêu cầu Mời thầu (RFP) và đánh giá Hồ sơ Đề xuất Nhà thầu (Vendor Proposal) sử dụng **Google Gemini API**, kết hợp trích xuất tiêu chí ưu tiên 1–5, chấm điểm 7 chiều chất lượng theo Appendix A và hỗ trợ sinh đề xuất chỉnh sửa.

---

## 📑 Mục Lục
1. [Sản Phẩm Là Gì?](#1-sản-phẩm-là-gì)
2. [Hướng Dẫn Cài Đặt & Chạy Demo](#2-hướng-dẫn-cài-đặt--chạy-demo)
3. [Công Nghệ Sử Dụng](#3-công-nghệ-sử-dụng)
4. [Dataset, API, Thư Viện & Template Đã Sử Dụng](#4-dataset-api-thư-viện--template-đã-sử-dụng)
5. [Giới Hạn Hiện Tại Của Sản Phẩm](#5-giới-hạn-hiện-tại-của-sản-phẩm)

---

## 1. Sản Phẩm Là Gì?

### Mục tiêu
Khi đánh giá hồ sơ thầu, người thẩm định thường mất nhiều thời gian đọc đối chiếu thủ công giữa bản yêu cầu của khách hàng (RFP) và hồ sơ chào thầu của các nhà thầu. Quá trình này dễ dẫn đến việc bỏ sót các yêu cầu bắt buộc hoặc đánh giá thiếu nhất quán.

**Proposal Scorer AI** là công cụ web giúp tự động hóa một phần quá trình này:
- Trích xuất các tiêu chí từ tài liệu RFP và phân loại theo mức độ quan trọng (1–5).
- Đánh giá độc lập chất lượng hồ sơ đề xuất theo 7 chiều (Rubric Appendix A của FPT Software).
- Đối chiếu mức độ đáp ứng từng tiêu chí RFP của đề xuất kèm trích dẫn văn bản đối chứng.
- Đề xuất câu chữ khắc phục cho các tiêu chí còn thiếu hoặc chưa rõ ràng và cho phép xuất bản thảo chỉnh sửa.

---

### Quy Trình Hoạt Động (5 Bước)

Hệ thống hoạt động theo quy trình 5 bước trên giao diện web:

1. **Bước 1: Nạp RFP (Customer RFP)**
   - Người dùng tải lên file RFP (`.pdf`, `.md`, `.txt`, `.xlsx`, `.csv`) hoặc dán trực tiếp nội dung văn bản vào ô nhập.
   - Có sẵn nút chọn nhanh tài liệu mẫu (`rfp_nordframe.md`).
2. **Bước 2: Xem & Tùy Biến Tiêu Chí (Criteria 1–5)**
   - AI bóc tách danh sách các yêu cầu và xếp hạng mức độ ưu tiên từ 1 (Nice-to-Have) đến 5 (Must-Have).
   - Người dùng có thể kéo thanh trượt (slider) để thay đổi mức độ quan trọng, thêm/xóa tiêu chí, và bấm nút **Adapt Descriptions** để AI viết lại diễn giải phù hợp với trọng số mới.
3. **Bước 3: Nạp Hồ Sơ Đề Xuất (Vendor Proposal)**
   - Tải lên file đề xuất (hỗ trợ PDF tài liệu hoặc PDF xuất từ PowerPoint) hoặc dán trực tiếp văn bản.
   - 4 bộ đề xuất mẫu (`Weak`, `Medium`, `Strong`, `Overpromise`) để kiểm thử nhanh.
   - Người dùng có thể giữ nguyên tiêu chí từ Bước 2 để quay lại thử nghiệm với nhiều đề xuất khác nhau.
4. **Bước 4: Đánh Giá Hồ Sơ & Phân Tích Lỗ Hổng**
   - **Bảng điểm 7 Rubric (Appendix A):** Chấm điểm 1–5 cho 7 khía cạnh (Thấu hiểu bài toán, Phạm vi bàn giao, Giá, Tiến độ, Độ đầy đủ, Văn phong thuyết phục, Tính minh bạch rủi ro).
   - **Ma trận tuân thủ tiêu chí (Compliance Scorecard):** Đánh giá từng yêu cầu theo 4 trạng thái (*Addressed, Partial, Missing, Contradicted*) kèm tính điểm trung bình có trọng số.
   - **Trích dẫn nguồn:** Cho phép bấm xem đoạn văn bản trích dẫn từ đề xuất để kiểm chứng kết quả đánh giá.
5. **Bước 5: Xuất Đề Xuất Đã Chỉnh Sửa**
   - Người dùng chọn các mục gợi ý sửa đổi cần áp dụng.
   - AI tạo bản thảo đề xuất mới đã bổ sung các điều khoản còn thiếu.

---

## 2. Hướng Dẫn Cài Đặt & Chạy Demo

### Yêu Cầu Môi Trường
- Docker & Docker Compose (khuyến nghị), **hoặc** Python 3.10+ nếu chạy trực tiếp.
- Khóa Google Gemini API Key.

### Cấu Hình Biến Môi Trường (`.env`)
Sao chép file `.env.example` thành `.env` và điền API key:
```bash
cp .env.example .env
```
Mở file `.env` và cập nhật:
```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8001

# Model tiers (tùy chọn)
LITE_MODEL=gemini-3.5-flash-lite
MEDIUM_MODEL=gemini-3.6-flash
STRONG_MODEL=gemini-3.8-flash
```

---

### Cách 1: Chạy Bằng Docker Compose (Production - Khuyên Dùng)

Sử dụng file [docker-compose.yaml](file:///home/linhphan/SiviCamp/team11-mosAIC-track1/docker-compose.yaml) (đóng gói mã nguồn trực tiếp vào container, ổn định, không dùng live-reload):

```bash
# Khởi chạy hệ thống
docker compose up -d --build

# Xem logs
docker compose logs -f

# Dừng hệ thống
docker compose down
```

Sau khi khởi chạy:
- **Giao diện Web:** [http://localhost:3000](http://localhost:3000)
- **API Swagger Docs:** [http://localhost:8001/docs](http://localhost:8001/docs)
- **Health Check:** [http://localhost:8001/api/health](http://localhost:8001/api/health)

---

### Cách 2: Chạy Bằng Docker Compose (Development - Live-Reload)

Dành cho lập trình viên cần chỉnh sửa code liên tục (sử dụng bind-mount và uvicorn reload):

```bash
# Khởi chạy chế độ dev
docker compose -f docker-compose.dev.yaml up -d --build

# Dừng chế độ dev
docker compose -f docker-compose.dev.yaml down
```

---

### Cách 3: Chạy Trực Tiếp Bằng Python (Không Dùng Docker)

```bash
# 1. Tạo môi trường ảo và cài đặt dependencies
python3 -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# 2. Khởi động Backend server
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
Mở trình duyệt truy cập: [http://localhost:8001](http://localhost:8001)

---

### Kịch Bản Chạy Demo Nhanh

1. **Sử dụng "Load Sample RFP":**
   - Tại Bước 1, bấm nút **`📄 Load Sample RFP (NordFrame Logistics)`** để nạp nhanh tài liệu RFP mẫu của NordFrame mà không cần tải file thủ công.
   - Sau đó bấm chuyển bước để hệ thống tự động bóc tách tiêu chí sang Bước 2.
2. **Thử nghiệm 4 hồ sơ thầu mẫu tại Bước 3:**
   - `proposal_1_weak` (BrightPath): Đề xuất thiếu nhiều tiêu chí quan trọng (vi phạm cơ sở dữ liệu, không có SLA).
   - `proposal_2_medium` (Clarion): Đề xuất ở mức trung bình, đáp ứng một phần yêu cầu.
   - `proposal_3_strong` (Apex): Đề xuất đầy đủ, bám sát các yêu cầu kỹ thuật và chi phí.
   - `proposal_4_overpromise` (Vantix): Đề xuất cam kết tiến độ ngắn bất thường (4 tuần), AI cảnh báo rủi ro về tính khả thi.

---

## 3. Công Nghệ Sử Dụng

- **AI / LLM:** Google Gemini API qua thư viện chính thức `google-genai>=2.0.0`.
  - Hỗ trợ cấu hình phân tầng model theo tác vụ: model nhẹ cho trích xuất nhanh và model mạnh hơn cho đối chiếu ngữ nghĩa, chấm điểm rubric và sinh văn bản.
- **Backend:**
  - **FastAPI**: Xây dựng REST API bất đồng bộ.
  - **Uvicorn**: ASGI web server.
  - **Pydantic v2**: Định nghĩa và kiểm tra cấu trúc dữ liệu JSON.
  - **PyMuPDF (`fitz`)**: Bóc tách nội dung file PDF, nhận diện slide ngang và trích xuất bảng biểu.
  - **Pandas & OpenPyXL**: Đọc và xử lý file dữ liệu bảng (`.xlsx`, `.csv`).
- **Frontend:**
  - **React 18**: Quản lý trạng thái và hiển thị giao diện người dùng.
  - **Tailwind CSS**: Định dạng giao diện theo phong cách tối giản (dark theme).
  - **Babel Standalone**: Biên dịch JSX ngay trên trình duyệt, không cần bước build Node.js phức tạp.
- **Web Server & Reverse Proxy:** Nginx Alpine điều hướng các yêu cầu `/api/` về Backend.

---

## 4. Dataset, API, Thư Viện & Template Đã Sử Dụng

### Dataset & Dữ Liệu Mẫu (Trong thư mục `data/`)
- `data/rfp/rfp_nordframe.md`: Đề bài RFP mẫu của công ty Nordframe (yêu cầu nâng cấp hệ thống kho vận, tích hợp PostgreSQL, cam kết SLA).
- `data/response/`: 4 bản đề xuất nhà thầu mẫu với mức độ tuân thủ khác nhau (`response_1_weak.md`, `response_2_medium.md`, `response_3_strong.md`, `response_4_overpromise.md`).

### Thư Viện Backend (`backend/requirements.txt`)
```text
google-genai>=2.0.0      # SDK chính thức của Google cho Gemini API
pydantic>=2.6.0          # Xác thực kiểu dữ liệu và schema
python-dotenv>=1.0.0     # Đọc cấu hình từ file .env
tabulate>=0.9.0          # Định dạng bảng văn bản khi chạy script CLI
fastapi>=0.110.0         # Framework xây dựng API
uvicorn>=0.28.0          # Web server chạy ứng dụng FastAPI
python-multipart>=0.0.9  # Hỗ trợ nhận file tải lên qua form
pymupdf>=1.24.0          # Đọc và bóc tách text/bảng từ file PDF
pandas>=2.2.0            # Đọc và xử lý bảng tính
openpyxl>=3.1.0          # Hỗ trợ file Excel .xlsx
```

### Các API Endpoints Chính
| Method | Endpoint | Chức Năng |
|:---:|---|---|
| `GET` | `/api/health` | Kiểm tra trạng thái hoạt động của Backend |
| `GET` | `/api/presets/{key}` | Lấy nội dung của 4 đề xuất mẫu |
| `GET` | `/api/sample` | Lấy dữ liệu đánh giá mẫu cho tính năng Instant Demo |
| `POST` | `/api/extract-criteria` | Trích xuất tiêu chí từ RFP (file hoặc text) |
| `POST` | `/api/criteria/adapt-descriptions` | AI viết lại mô tả tiêu chí khi thay đổi trọng số |
| `POST` | `/api/feedback` | Đánh giá đề xuất thầu đối chiếu tiêu chí và chấm 7 Rubric |
| `POST` | `/api/evaluate` | Đánh giá trọn gói 2 giai đoạn từ 2 file/text đầu vào |

### Template Đánh Giá
- **7 Tiêu Chí Rubric (Appendix A - FPT Software):**
  1. *Problem Understanding* (Thấu hiểu bài toán)
  2. *Scope & Deliverables Clarity* (Độ rõ ràng về phạm vi & bàn giao)
  3. *Pricing Clarity* (Độ minh bạch về giá)
  4. *Timeline Clarity* (Độ rõ ràng về tiến độ)
  5. *Completeness vs. RFP Requirements* (Độ đầy đủ so với yêu cầu)
  6. *Tone & Persuasiveness* (Văn phong và sức thuyết phục)
  7. *Risk / Assumptions Transparency* (Minh bạch rủi ro & giả định)
- **Thang Điểm Tiêu Chí (1–5 Marks):** Phân loại mức độ ưu tiên từ 1 (Nice-to-Have) đến 5 (Must-Have).

---

## 5. Giới Hạn Hiện Tại Của Sản Phẩm

Để đánh giá đúng năng lực thực tế của công cụ, nhóm ghi nhận một số giới hạn kỹ thuật hiện tại:

1. **Chưa có OCR cho PDF ảnh scan thuần:**
   - Thư viện `PyMuPDF` xử lý tốt các file PDF có lớp văn bản số (digital PDF, Word/PowerPoint xuất sang PDF).
   - Nếu file PDF là ảnh chụp scan không có text layer, hệ thống hiện chưa tự động bóc tách được và cần bổ sung thêm module OCR (như Tesseract OCR hoặc Gemini Vision).
2. **Xử lý tài liệu rất dài (>100 trang):**
   - Khi tài liệu quá dài, việc gửi toàn bộ nội dung trong một lần gọi API có thể làm chậm thời gian phản hồi hoặc chạm ngưỡng ngữ cảnh hiệu quả. Hướng giải quyết tiếp theo là chia nhỏ tài liệu (chunking) kết hợp tìm kiếm ngữ nghĩa (RAG).
3. **Lưu trữ phiên làm việc (Session-based):**
   - Dữ liệu hiện tại được xử lý theo từng phiên làm việc của người dùng trên trình duyệt và dọn dẹp file tạm sau khi xử lý xong, chưa tích hợp cơ sở dữ liệu để lưu lại lịch sử chấm thầu của từng tài khoản.
4. **Phụ thuộc vào chất lượng sinh của LLM:**
   - Kết quả chấm điểm và gợi ý sửa đổi phụ thuộc vào chất lượng phản hồi từ mô hình Gemini. Dù đã có schema ràng buộc và thuật toán tính điểm nội bộ, người thẩm định vẫn đóng vai trò quyết định cuối cùng trong việc xét duyệt hồ sơ.

---

## 👥 Thông Tin Dự Án

- **Nhóm:** Team 11 - mosAIC (SiviCamp 2026)