"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider):
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot phản hồi:\n{response}")


def run_react_agent(
    user_query: str,
    provider,
    mcp_server: MCPAcademicServer
) -> list:
    """
    Thực thi ReAct Loop thực sự:
    Thought -> Action -> Observation -> Thought -> ...

    Agent có thể gọi nhiều Tool liên tiếp trước khi đưa ra Final Answer.

    Trả về danh sách Waterfall Trace Logs.
    """

    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    step = 0
    trace_logs = []
    tools_list = mcp_server.list_tools()

    # Lưu lịch sử các Action/Observation để đưa lại cho LLM ở vòng sau
    execution_history = []

    # Prompt ban đầu
    working_prompt = user_query

    while step < MAX_ITERATIONS:
        step += 1
        step_start_time = time.time()

        print(
            f"\n--- 🔄 Vòng lặp ReAct Loop "
            f"(Step {step}/{MAX_ITERATIONS}) ---"
        )

        # ==========================================================
        # 1. GỌI LLM
        # ==========================================================
        llm_response = provider.generate_with_tools(
            working_prompt,
            tools_list,
            system_prompt=REACT_AGENT_SYSTEM_PROMPT
        )

        latency_ms = round(
            (time.time() - step_start_time) * 1000,
            2
        )

        thought = llm_response.get(
            "thought",
            "Đang phân tích bước xử lý tiếp theo..."
        )

        print(f"🧠 [Thought]: {thought}")

        response_type = llm_response.get("type")

        # ==========================================================
        # 2. LLM TRẢ VỀ FINAL ANSWER
        # ==========================================================
        if response_type == "text":
            final_content = llm_response.get(
                "content",
                "Không có nội dung phản hồi."
            )

            print(f"🏁 [Final Answer]: {final_content}")

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })

            break

        # ==========================================================
        # 3. LLM MUỐN GỌI TOOL
        # ==========================================================
        elif response_type == "tool_call":

            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})

            print(
                f"🛠️ [Action Proposed]: "
                f"{tool_name}({arguments})"
            )

            # ------------------------------------------------------
            # Kiểm tra Tool Call hợp lệ
            # ------------------------------------------------------
            if not tool_name:
                error_message = "LLM không cung cấp tên Tool."

                print(f"⚠️ {error_message}")

                trace_logs.append({
                    "step": step,
                    "query": user_query,
                    "action_type": "ERROR",
                    "thought": thought,
                    "output": error_message,
                    "latency_ms": latency_ms
                })

                break

            # ------------------------------------------------------
            # Chống việc Agent gọi lại chính xác Tool đã chạy
            # ------------------------------------------------------
            duplicate_call = any(
                item["tool_name"] == tool_name
                and item["arguments"] == arguments
                for item in execution_history
            )

            if duplicate_call:
                print(
                    "⚠️ [DUPLICATE TOOL CALL]: "
                    "Agent đang cố gọi lại Tool với cùng tham số."
                )

                working_prompt = f"""
Yêu cầu ban đầu của người dùng:

{user_query}

Các thao tác đã thực hiện:
{json.dumps(execution_history, ensure_ascii=False, indent=2)}

Bạn đang định gọi lại chính xác một công cụ đã thực hiện trước đó.

KHÔNG được lặp lại Tool Call cũ.

Hãy xem lại các Observation đã có.

Nếu nhiệm vụ đã hoàn thành:
- Trả lời người dùng bằng văn bản.

Nếu vẫn còn bước khác chưa hoàn thành:
- Gọi công cụ tiếp theo phù hợp.

Ví dụ:
Nếu đã academic_query và đã biết advisor,
nhưng người dùng còn yêu cầu đặt lịch,
hãy gọi schedule_appointment.
"""

                continue

            # ======================================================
            # 4. THỰC THI TOOL QUA MCP SERVER
            # ======================================================
            tool_start_time = time.time()

            try:
                mcp_result = mcp_server.call_tool(
                    tool_name,
                    arguments
                )

                tool_latency_ms = round(
                    (time.time() - tool_start_time) * 1000,
                    2
                )

                obs_data = mcp_result.get("result", {})

            except Exception as e:
                tool_latency_ms = round(
                    (time.time() - tool_start_time) * 1000,
                    2
                )

                obs_data = {
                    "status": "MCP_ERROR",
                    "error": str(e)
                }

            obs_str = json.dumps(
                obs_data,
                ensure_ascii=False
            )

            print(
                f"👁️ [Observation từ MCP Server]: "
                f"{obs_str}"
            )

            # ======================================================
            # 5. GHI WATERFALL TRACE
            # ======================================================
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "thought": thought,
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms,
                "tool_latency_ms": tool_latency_ms
            })

            # Lưu lịch sử để Agent biết những gì đã làm
            execution_history.append({
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data
            })

            # ======================================================
            # 6. TẠO CONTEXT CHO VÒNG REACT TIẾP THEO
            # ======================================================

            working_prompt = f"""
YÊU CẦU BAN ĐẦU CỦA NGƯỜI DÙNG:
{user_query}

LỊCH SỬ CÁC ACTION / OBSERVATION ĐÃ THỰC HIỆN:
{json.dumps(execution_history, ensure_ascii=False, indent=2)}

Bạn đang ở trong một ReAct Loop.

Hãy xem xét yêu cầu ban đầu và các Observation đã có.

QUY TẮC:
1. Không gọi lại một Tool với cùng tham số nếu Tool đó đã chạy thành công.
2. Nếu yêu cầu của người dùng còn hành động chưa hoàn thành,
   hãy gọi Tool tiếp theo.
3. Nếu đã có đủ dữ liệu và tất cả yêu cầu đã hoàn thành,
   hãy trả lời người dùng bằng văn bản.
4. Không được tự bịa dữ liệu ngoài Observation.
5. Nếu Observation có status NOT_FOUND,
   hãy thông báo chính xác rằng không tìm thấy dữ liệu.
6. Nếu vừa tra cứu được tên cố vấn và yêu cầu ban đầu còn yêu cầu đặt lịch,
   hãy sử dụng tên cố vấn từ Observation để gọi schedule_appointment.

Hãy quyết định bước tiếp theo.
"""

            # QUAN TRỌNG:
            # Không break ở đây.
            # Loop tiếp tục để LLM quyết định Action tiếp theo.

        # ==========================================================
        # 7. RESPONSE TYPE KHÔNG HỢP LỆ
        # ==========================================================
        else:
            error_message = (
                f"LLM trả về response type không hợp lệ: "
                f"{response_type}"
            )

            print(f"⚠️ [AGENT ERROR]: {error_message}")

            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "ERROR",
                "thought": thought,
                "output": error_message,
                "latency_ms": latency_ms
            })

            break

    # ==============================================================
    # 8. MAX ITERATIONS
    # ==============================================================
    else:
        final_message = (
            f"Agent đã đạt giới hạn {MAX_ITERATIONS} bước "
            "nhưng chưa hoàn tất được yêu cầu."
        )

        print(f"⚠️ [MAX ITERATIONS]: {final_message}")

        trace_logs.append({
            "step": step + 1,
            "query": user_query,
            "action_type": "MAX_ITERATIONS_REACHED",
            "thought": "Dừng để tránh vòng lặp vô hạn.",
            "output": final_message,
            "latency_ms": 0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")
    
    if "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp với ReAct Agent:")
        print("💡 Gợi ý câu hỏi thử nghiệm:")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên SV2026001'")
        print("   - Đặt lịch hẹn: 'Đặt lịch hẹn tư vấn cho SV2026001 vào 14:00 ngày 15/09/2026'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break
                logs = run_react_agent(user_input, provider, mcp_server)
                save_waterfall_trace(logs)
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Đã thoát phiên tương tác.")
                break
    elif "--all" in sys.argv:
        print("🚀 [TEST SUITE MODE] Kiểm tra 5 Test Cases:")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                logs = run_react_agent(tc["question"], provider, mcp_server)
                all_traces.extend(logs)
                completed_count += 1
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:   python src/app.py --interactive")
        print("  2. Chạy toàn bộ Test Cases:    python src/app.py --all\n")
        
        sample_query = tests[1]["question"]
        print(f"--- 🏁 DEMO CHẠY THỬ 1 TEST CASE MẪU (TC02: Tra cứu học vụ) ---")
        logs = run_react_agent(sample_query, provider, mcp_server)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
