# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Tạ Văn Tuấn
> **Mã Sinh Viên / Mã Học viên:** 2A202602806  
> **Chủ đề Lựa chọn:** Trợ lý Học vụ & Tra cứu/Đặt lịch tư vấn VinUni

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | Một số yêu cầu cần tra cứu thông tin sinh viên, lấy tên cố vấn rồi mới thực hiện hành động đặt lịch. |
| **2. Tool Interaction** | 5 / 5 | Agent cần gọi MCP Server để truy vấn dữ liệu học vụ và thực hiện đặt lịch. |
| **3. Dynamic Decision** | 4 / 5 | Hành động tiếp theo phụ thuộc vào Observation, ví dụ phải xác định cố vấn trước khi đặt lịch. |
| **4. Long Horizon Goal** | 3 / 5 | Agent phải duy trì mục tiêu qua nhiều bước nhưng workflow chỉ kéo dài khoảng 2–3 action. |
| **TỔNG ĐIỂM AGENTIC FIT** | 16/ 20 | *Nếu tổng điểm > 12/20: Bài toán rất phù hợp triển khai Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "TOOL_EXECUTION",
    "thought": "OpenAI quyết định gọi công cụ 'academic_query' với tham số: {\"student_id\": \"SV2026001\"}",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 854.02,
    "tool_latency_ms": 0.0
  },
  {
    "step": 2,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ).",
    "output": "Đã tra cứu thành công thông tin học vụ của sinh viên **SV2026001**. Dưới đây là kết quả chi tiết:\n\n- **Họ và tên:** Nguyễn Văn An\n- **Lớp:** AI-K4\n- **GPA:** 3.85\n- **Email:** an.nv@vinuni.edu.vn\n- **Tình trạng học tập:** Đang học\n- **Cố vấn học tập:** PGS.TS Nguyễn Văn A\n\nNếu bạn cần hỗ trợ thêm (ví dụ đặt lịch tư vấn với Cố vấn học tập), hãy cho mình biết nhé!",
    "latency_ms": 1983.65
  },
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
