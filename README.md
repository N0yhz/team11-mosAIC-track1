# RFP Evaluator AI • Level 2 Intelligence Platform

Hệ thống phân tích Yêu cầu Mời thầu (RFP) và đánh giá Hồ sơ Đề xuất Nhà thầu (Vendor Response) sử dụng **Google Gemini API**, cấu trúc điểm ưu tiên 1–5 (Criteria 1–5 Marks) và giao diện trực quan hóa dạng slide tương tác.

---

## 🏗️ Cấu Trúc Dự Án (Repository Architecture)

Dự án được phân tách rõ ràng thành hai phần độc lập: **Backend** (FastAPI / Gemini Pipeline) và **Frontend** (React / Tailwind UI), cùng thư mục tài liệu **Data**:

```
team11-mosAIC-track1/
├── backend/                          # Backend API & AI Pipeline Engine
│   ├── support_library/              # Module bóc tách tiêu chí & chấm điểm response
│   │   ├── criterias_extractor/      # Gemini RFP requirements extractor (1–5 scale)
│   │   └── lvl2_feedback_response/   # Feedback & proposal correction engine
│   ├── pipeline.py                   # Level 2 Pipeline orchestrator
│   ├── main.py                       # FastAPI REST API & route handlers
│   ├── requirements.txt              # Backend dependencies
│   └── Dockerfile                    # Container backend (Python 3.11-slim)
│
├── frontend/                         # Frontend UI
│   ├── index.html                    # React + Tailwind UI (Slide 5 marks & Scorecard)
│   ├── nginx.conf                    # Cấu hình Nginx reverse proxy dev
│   └── Dockerfile                    # Container frontend (Nginx alpine)
│
├── data/                             # Dữ liệu & tài liệu mẫu
│   ├── rfp/                          # Customer RFP documents (.md)
│   ├── response/                     # Vendor proposals (weak, medium, strong...)
│   ├── sample_data/                  # Benchmark requirements
│   └── samples/                      # Kết quả phân tích mẫu (JSON & MD)
│
├── docker-compose.dev.yaml           # Docker Compose môi trường phát triển (Bind Mounts)
├── .env                              # Biến môi trường & Google Gemini API Key
├── .env.example                      # File mẫu biến môi trường
├── .gitignore                        # Cấu hình bỏ qua git
└── README.md                         # Tài liệu hướng dẫn sử dụng
```

---

## 🎯 Thang Điểm Tiêu Chí RFP (1 - 5 Marks)

Mỗi tiêu chí trích xuất từ RFP được AI phân loại theo 5 mức độ:

| Điểm | Mức Độ | Ý Nghĩa Nghiệp Vụ |
|:---:|:---|:---|
| **5** | **Must-Have** | Bắt buộc phải có (Deal-breaker). Thiếu tiêu chí này sẽ bị loại ngay từ vòng hồ sơ. |
| **4** | **High Priority** | Rất quan trọng cho vận hành, ảnh hưởng lớn đến quyết định chọn thầu. |
| **3** | **Medium Priority** | Yêu cầu tiêu chuẩn cần đáp ứng trong phạm vi hợp đồng. |
| **2** | **Low Priority** | Tiện ích phụ hoặc tính năng giai đoạn sau, mức độ ưu tiên thấp. |
| **1** | **Nice to Have** | Tính năng mở rộng tùy chọn, điểm cộng gia tăng nếu ngân sách cho phép. |

---

## 🐳 Khởi Chạy Bằng Docker Compose (Development Mode)

Chế độ phát triển sử dụng **Host Bind Mounts**:
* Thay đổi file Python trong `./backend/` ➡️ `uvicorn --reload` tự động tải lại ngay trong container mà **không cần restart container**.
* Thay đổi HTML/CSS/JS trong `./frontend/` ➡️ F5 trình duyệt là thấy ngay phiên bản mới nhất mà **không cần build lại image**.

### 1. Cấu hình biến môi trường
Tạo file `.env` từ `.env.example` và điền Gemini API Key:
```bash
cp .env.example .env
# Chỉnh sửa .env:
# GEMINI_API_KEY=AIzaSy...
```

### 2. Khởi chạy hệ thống
```bash
docker compose -f docker-compose.dev.yaml up -d --build
```

### 3. Truy cập ứng dụng
* **Frontend Web UI**: [http://localhost:3000](http://localhost:3000) (Nginx reverse-proxy sang Backend)
* **Backend API / Swagger Docs**: [http://localhost:8001/docs](http://localhost:8001/docs)
* **Health Check**: [http://localhost:8001/api/health](http://localhost:8001/api/health)

### 4. Xem logs realtime
```bash
# Xem toàn bộ logs
docker compose -f docker-compose.dev.yaml logs -f

# Hoặc chỉ xem logs backend
docker compose -f docker-compose.dev.yaml logs -f backend
```

### 5. Dừng hệ thống
```bash
docker compose -f docker-compose.dev.yaml down
```

---

## 💻 Chạy Trực Tiếp Bằng Python (Không Dùng Docker)

Nếu không sử dụng Docker, bạn có thể chạy trực tiếp bằng virtualenv:

### 1. Cài đặt dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 2. Chạy Backend API Server
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```
Truy cập giao diện tại: [http://localhost:8001](http://localhost:8001)

### 3. Chạy Pipeline qua dòng lệnh (CLI)
```bash
python3 backend/pipeline.py data/rfp/rfp_nordframe.md data/response/response_2_medium.md
```
Kết quả được lưu tại file `lvl2_pipeline_output_response_2_medium.json`.

---


---

## 🤖 Cấu Hình Phân Tầng AI Models (Model Tiers in `.env`)

Hệ thống hỗ trợ 3 tầng model chuyên biệt hóa theo đặc thù từng tác vụ (Task-to-Model Mapping):

```env
# ===============================================
# Google Gemini API Configuration & Model Tiers
# ===============================================
GEMINI_API_KEY=your_gemini_api_key_here

# 1. LITE MODEL: Tốc độ tối đa, chi phí thấp, context lớn
LITE_MODEL=gemini-3.5-flash-lite

# 2. MEDIUM MODEL: Cân bằng tốc độ và khả năng bóc tách cấu trúc JSON
MEDIUM_MODEL=gemini-3.6-flash

# 3. STRONG MODEL: Suy luận sâu, đánh giá chéo tài liệu, viết lại đề xuất
STRONG_MODEL=gemini-3.8-flash
```

### 📋 Bảng Phân Công Nhiệm Vụ & Model Sử Dụng (Task & Model Matrix)

| Tác Vụ (Task) | Phân Tầng | Model Gemini Mặc Định | Lý Do Kỹ Thuật (Rationale) |
|---|---|---|---|
| **Tiền xử lý văn bản & Metadata Extraction** | **LITE** | `gemini-3.5-flash-lite` | Tác vụ đơn giản (trích xuất tiêu đề, ngày tháng, định dạng), cần độ trễ thấp và tối ưu chi phí token. |
| **Bóc tách Tiêu chí RFP & Chấm điểm 1–5** (Stage 1) | **MEDIUM** | `gemini-3.6-flash` | Cần hiểu ngữ nghĩa RFP ("must", "shall", "optional") và xuất schema JSON chuẩn xác. Cung cấp tốc độ phản hồi nhanh khi người dùng upload RFP. |
| **Đánh giá Tuân thủ & Lập Scorecard Đề xuất** (Stage 2A) | **STRONG** | `gemini-3.8-flash` | Đòi hỏi đối chiếu logic đa tài liệu (RFP vs Response), bóc trần các tuyên bố tiếp thị chung chung, phát hiện lỗ hổng và deal-breaker. |
| **Chiến lược Sửa đổi & Viết lại Đề xuất** (Stage 2B) | **STRONG** | `gemini-3.8-flash` (hoặc `gemini-3.1-pro`) | Sinh văn bản dài, chuyên nghiệp (Executive Summary, Technical Architecture), đề xuất lộ trình khắc phục các điểm chưa đạt. |
| **Tái tính toán Điểm Số Tương Tác** (UI Sliders) | **Code** | *Thuật toán nội bộ (Không tốn token)* | Tính toán tức thì trên Frontend/Backend khi người dùng kéo thanh điểm ưu tiên 1–5. |

---
## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/api/health` | Kiểm tra trạng thái hoạt động của Backend |
| `GET` | `/api/sample` | Trả về kết quả đánh giá mẫu tức thì (cho demo UI) |
| `GET` | `/api/sample/criteria` | Trả về danh sách tiêu chí mẫu (cho demo Stage 1) |
| `POST` | `/api/extract-criteria` | **Stage 1**: Upload RFP, trích xuất danh sách tiêu chí và xếp hạng 1–5 marks |
| `POST` | `/api/feedback` | **Stage 2**: Gửi tiêu chí đã tùy biến cùng đề xuất nhà thầu để AI chấm điểm và sửa đổi |
| `POST` | `/api/evaluate` | **Unified Pipeline**: Upload cả 2 file, chạy trọn gói 2 giai đoạn |
