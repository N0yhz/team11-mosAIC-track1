"""
Chương trình trích xuất và xếp hạng yêu cầu khách hàng từ file Markdown (.md)
sử dụng Google GenAI SDK (google-genai) và Pydantic Structured Outputs.

Thang điểm xếp hạng:
- 1: Nice to have (Tùy chọn / Có thì tốt hơn)
- 2: Low priority (Ưu tiên thấp)
- 3: Medium priority (Ưu tiên trung bình)
- 4: High priority (Ưu tiên cao)
- 5: Must have (Bắt buộc phải có)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Tải biến môi trường từ .env
load_dotenv()

# =====================================================================
# 1. Định nghĩa cấu trúc dữ liệu đầu ra với Pydantic (Structured Output)
# =====================================================================
class RequirementItem(BaseModel):
    id: str = Field(
        description="Mã định danh yêu cầu, ví dụ REQ-01, REQ-02..."
    )
    title: str = Field(
        description="Tiêu đề ngắn gọn tóm tắt yêu cầu"
    )
    description: str = Field(
        description="Mô tả chi tiết nội dung yêu cầu của khách hàng"
    )
    category: str = Field(
        description="Phân loại chức năng/module (ví dụ: 'Xác thực & Tài khoản', 'Thanh toán', 'Bảo mật', 'Vận chuyển', v.v.)"
    )
    priority_score: int = Field(
        description="Điểm xếp hạng độ quan trọng từ 1 đến 5 (1: Nice to have, 5: Must have)",
        ge=1,
        le=5
    )
    priority_level: str = Field(
        description="Nhãn mức độ ưu tiên tương ứng ('1 - Nice to have', '2 - Low priority', '3 - Medium priority', '4 - High priority', '5 - Must have')"
    )
    rationale: str = Field(
        description="Lý do chi tiết giải thích tại sao chấm mức ưu tiên này dựa trên mức độ quan trọng nghiệp vụ hoặc rủi ro"
    )


class RequirementAnalysisResult(BaseModel):
    project_title: str = Field(
        description="Tên hoặc chủ đề tổng quan của dự án theo tài liệu yêu cầu của khách hàng"
    )
    summary: str = Field(
        description="Tóm tắt tổng quan về bối cảnh và mục tiêu cốt lõi của khách hàng"
    )
    requirements: List[RequirementItem] = Field(
        description="Danh sách toàn bộ các yêu cầu đã được trích xuất và xếp hạng từ 1 đến 5"
    )


# =====================================================================
# 2. Hàm chính: Trích xuất và xếp hạng yêu cầu từ file .md
# =====================================================================
def extract_and_rank_requirements(
    file_path: str,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> RequirementAnalysisResult:
    """
    Đọc file markdown (.md) chứa yêu cầu của khách hàng, gọi Google GenAI 
    để phân tích, bóc tách và xếp hạng từng yêu cầu theo thang điểm 1-5.

    :param file_path: Đường dẫn tới file .md chứa yêu cầu.
    :param model_name: Tên model Gemini muốn dùng (mặc định lấy từ biến GEMINI_MODEL hoặc 'gemini-3.5-flash-lite').
    :param api_key: Gemini API Key (mặc định lấy từ biến GEMINI_API_KEY trong .env).
    :return: Đối tượng RequirementAnalysisResult chứa danh sách yêu cầu đã xếp hạng.
    """
    # 1. Kiểm tra file đầu vào
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
    if not path.is_file():
        raise ValueError(f"Đường dẫn '{file_path}' không phải là tập tin hợp lệ.")
    if path.suffix.lower() != ".md":
        print(f"[Lưu ý] File '{file_path}' không có phần mở rộng là .md, vẫn tiếp tục đọc nội dung...")

    with open(path, "r", encoding="utf-8") as f:
        markdown_content = f.read().strip()

    if not markdown_content:
        raise ValueError(f"File '{file_path}' rỗng, vui lòng cung cấp nội dung yêu cầu.")

    # 2. Xác định API Key
    effective_api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not effective_api_key or effective_api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Chưa cấu hình GEMINI_API_KEY! "
            "Vui lòng tạo hoặc sửa file .env và điền API Key: GEMINI_API_KEY=AIzaSy..."
        )

    # 3. Khởi tạo Google GenAI Client
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=effective_api_key)

    # 4. Xác định Model
    primary_model = model_name or os.environ.get("GEMINI_MODEL") or "gemini-3.5-flash-lite"
    fallback_models = [m for m in ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"] if m != primary_model]
    models_to_try = [primary_model] + fallback_models

    # 5. Xây dựng Prompt cho AI
    prompt = f"""
Bạn là một chuyên gia cao cấp về Phân tích Nghiệp vụ phần mềm (Senior Business Analyst & Requirements Engineer).
Nhiệm vụ của bạn là đọc kỹ tài liệu yêu cầu của khách hàng dưới đây, bóc tách TOÀN BỘ các yêu cầu cụ thể (cả chức năng và phi chức năng), sau đó phân loại và xếp hạng từng yêu cầu theo thang điểm từ 1 đến 5:

### THANG ĐIỂM XẾP HẠNG (1 - 5):
- **5 - Must have (Bắt buộc phải có)**: Yêu cầu cốt lõi nhất. Nếu thiếu thì hệ thống KHÔNG THỂ hoạt động được, vi phạm pháp luật/bảo mật nghiêm trọng, hoặc không đáp ứng mục tiêu kinh doanh tối thiểu của khách hàng.
- **4 - High priority (Rất quan trọng)**: Mang lại giá trị vận hành cao, cực kỳ quan trọng đối với trải nghiệm khách hàng, nhưng có thể chấp nhận giải pháp thay thế tạm thời trong giai đoạn đầu nếu cần.
- **3 - Medium priority (Quan trọng vừa phải)**: Tính năng tiêu chuẩn cần có để hệ thống hoàn thiện, nâng cao sự tiện lợi nhưng không làm gián đoạn luồng nghiệp vụ chính.
- **2 - Low priority (Ưu tiên thấp)**: Tính năng phụ trợ, cải tiến nhỏ, tần suất dùng thấp, có thể lùi sang các giai đoạn sau.
- **1 - Nice to have (Tùy chọn / Có thì tốt hơn)**: Tính năng 'xa xỉ', trang trí UI/UX nâng cao, ý tưởng thêm vào nếu còn thời gian/ngân sách, hoàn toàn không ảnh hưởng vận hành nếu bỏ qua.

### TÀI LIỆU YÊU CẦU CỦA KHÁCH HÀNG:
---
{markdown_content}
---

Hãy trích xuất danh sách đầy đủ, gán mã REQ-01, REQ-02..., xếp hạng chính xác theo thang điểm 1-5 và nêu lý do (rationale) rõ ràng, thuyết phục.
"""

    # 6. Gửi yêu cầu với Structured Output
    last_error = None
    for target_model in models_to_try:
        try:
            print(f"[AI] Đang phân tích yêu cầu bằng model: {target_model}...")
            response = client.models.generate_content(
                model=target_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RequirementAnalysisResult,
                    temperature=0.1,
                ),
            )
            return response.parsed
        except Exception as e:
            last_error = e
            print(f"[Cảnh báo] Model {target_model} bận hoặc gặp lỗi ({str(e)[:80]}). Thử model khác...")
            continue

    raise RuntimeError(f"Không thể hoàn thành phân tích sau khi thử các model: {last_error}")


# =====================================================================
# 3. Tiện ích: Hiển thị kết quả ra Terminal
# =====================================================================
def display_results_terminal(result: RequirementAnalysisResult):
    """In kết quả phân tích dạng bảng màu sắc trực quan ra terminal."""
    try:
        from tabulate import tabulate
        has_tabulate = True
    except ImportError:
        has_tabulate = False

    print("\n" + "=" * 85)
    print(f"  DỰ ÁN: {result.project_title}")
    print("=" * 85)
    print(f"  Tóm tắt: {result.summary}")
    print("-" * 85)

    # Sắp xếp theo thứ tự ưu tiên giảm dần (từ 5 xuống 1)
    sorted_reqs = sorted(result.requirements, key=lambda x: x.priority_score, reverse=True)

    # ANSI Colors
    C_RED = "\033[91m"
    C_YELLOW = "\033[93m"
    C_BLUE = "\033[94m"
    C_CYAN = "\033[96m"
    C_GREEN = "\033[92m"
    C_RESET = "\033[0m"
    C_BOLD = "\033[1m"

    color_map = {
        5: C_RED,
        4: C_YELLOW,
        3: C_BLUE,
        2: C_CYAN,
        1: C_GREEN
    }

    table_data = []
    for r in sorted_reqs:
        c = color_map.get(r.priority_score, C_RESET)
        formatted_priority = f"{c}{C_BOLD}[{r.priority_score}/5] {r.priority_level}{C_RESET}"
        table_data.append([
            r.id,
            r.title,
            r.category,
            formatted_priority,
            r.rationale
        ])

    if has_tabulate:
        headers = ["Mã", "Yêu cầu", "Phân loại", "Mức độ ưu tiên", "Lý do xếp hạng"]
        print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[8, 22, 16, 22, 35]))
    else:
        for r in sorted_reqs:
            print(f"[{r.id}] ({r.category}) - {r.title}")
            print(f"   Ưu tiên: [{r.priority_score}/5] {r.priority_level}")
            print(f"   Mô tả: {r.description}")
            print(f"   Lý do: {r.rationale}")
            print("-" * 60)

    # Thống kê nhanh
    counts = {i: 0 for i in range(1, 6)}
    for r in result.requirements:
        counts[r.priority_score] = counts.get(r.priority_score, 0) + 1

    print("\n  THỐNG KÊ MỨC ĐỘ ƯU TIÊN:")
    print(f"   - {C_RED}[Điểm 5] Must have (Bắt buộc):{C_RESET}       {counts[5]} yêu cầu")
    print(f"   - {C_YELLOW}[Điểm 4] High priority (Rất quan trọng):{C_RESET} {counts[4]} yêu cầu")
    print(f"   - {C_BLUE}[Điểm 3] Medium priority (Trung bình):{C_RESET}   {counts[3]} yêu cầu")
    print(f"   - {C_CYAN}[Điểm 2] Low priority (Ưu tiên thấp):{C_RESET}    {counts[2]} yêu cầu")
    print(f"   - {C_GREEN}[Điểm 1] Nice to have (Tùy chọn):{C_RESET}       {counts[1]} yêu cầu")
    print(f"   ==> TỔNG CỘNG: {len(result.requirements)} yêu cầu\n")


# =====================================================================
# 4. Tiện ích: Xuất kết quả ra Markdown và JSON
# =====================================================================
def export_to_markdown(result: RequirementAnalysisResult, output_path: str):
    """Xuất báo cáo kết quả ra file Markdown đẹp mắt."""
    sorted_reqs = sorted(result.requirements, key=lambda x: x.priority_score, reverse=True)

    lines = [
        f"# Báo Cáo Phân Tích & Xếp Hạng Yêu Cầu Khách Hàng: {result.project_title}",
        f"\n> **Tóm tắt dự án:** {result.summary}\n",
        "## Bảng Tổng Hợp Yêu Cầu (Xếp hạng từ 1 đến 5)",
        "- **5**: Must have (Bắt buộc phải có)",
        "- **4**: High priority (Rất quan trọng)",
        "- **3**: Medium priority (Quan trọng vừa phải)",
        "- **2**: Low priority (Ưu tiên thấp)",
        "- **1**: Nice to have (Tùy chọn / Có thì tốt hơn)\n",
        "| Mã | Yêu Cầu | Phân Loại | Mức Ưu Tiên | Điểm | Lý Do Xếp Hạng |",
        "|:---|:---|:---|:---|:---:|:---|"
    ]

    for r in sorted_reqs:
        lines.append(f"| **{r.id}** | {r.title} | {r.category} | `{r.priority_level}` | **{r.priority_score}/5** | {r.rationale} |")

    lines.append("\n## Chi Tiết Từng Yêu Cầu\n")
    for r in sorted_reqs:
        lines.append(f"### [{r.id}] {r.title}")
        lines.append(f"- **Phân loại:** {r.category}")
        lines.append(f"- **Mức độ ưu tiên:** **{r.priority_score}/5** ({r.priority_level})")
        lines.append(f"- **Mô tả yêu cầu:** {r.description}")
        lines.append(f"- **Lý do đánh giá:** {r.rationale}\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[Xuất file] Đã lưu báo cáo Markdown vào: {output_path}")


def export_to_json(result: RequirementAnalysisResult, output_path: str):
    """Lưu kết quả phân tích dưới định dạng JSON."""
    with open(output_path, "w", encoding="utf-8") as jf:
        jf.write(result.model_dump_json(indent=2))
    print(f"[Xuất file] Đã lưu kết quả JSON vào: {output_path}")


# =====================================================================
# 5. CLI Entrypoint
# =====================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Trích xuất và xếp hạng yêu cầu khách hàng từ file Markdown (.md) bằng Google GenAI."
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default="sample_customer_requirements.md",
        help="Đường dẫn tới file markdown chứa yêu cầu của khách hàng (mặc định: sample_customer_requirements.md)"
    )
    parser.add_argument(
        "--output-md",
        "-o",
        default="requirements_report.md",
        help="Đường dẫn xuất file báo cáo Markdown (mặc định: requirements_report.md)"
    )
    parser.add_argument(
        "--output-json",
        "-j",
        help="Đường dẫn xuất file JSON kết quả (tùy chọn)"
    )

    args = parser.parse_args()

    print("=" * 85)
    print("  GOOGLE GENAI - TRÍCH XUẤT VÀ XẾP HẠNG YÊU CẦU KHÁCH HÀNG (1-5)")
    print("=" * 85)
    print(f"File đầu vào: {args.input_file}")

    try:
        # Gọi hàm chính
        analysis_result = extract_and_rank_requirements(args.input_file)

        # In kết quả ra terminal
        display_results_terminal(analysis_result)

        # Xuất file Markdown
        if args.output_md:
            export_to_markdown(analysis_result, args.output_md)

        # Xuất file JSON nếu có tùy chọn
        if args.output_json:
            export_to_json(analysis_result, args.output_json)

    except Exception as exc:
        print(f"\n[LỖI]: {exc}", file=sys.stderr)
        sys.exit(1)
