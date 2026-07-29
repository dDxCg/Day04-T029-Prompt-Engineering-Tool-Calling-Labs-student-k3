# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 11:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team:T029
- Members: Nguyen Thanh Hoan - 2A202601201
- Do: Prompt_system

- Team:T029
- Members: Do Tuan Kiet - 2A202601335
- Do: tools

- Team:T029
- Members: Đỗ Đức Cường -  2A202601455
- Do: Eval

- Team:T029
- Members: Luong Thanh Trang - 2A202601363
- Do: UI
---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

> 1–2 câu mô tả agent dùng để làm gì.

Ví dụ: "Research agent: tìm tin theo từ khóa / theo tài khoản, đọc URL và tổng hợp thành digest."

**Link dùng thử (truy cập được trong showdown):**

> Dán public URL nếu người khác cần mở từ máy riêng; localhost cũng được nếu demo trực tiếp trên máy trình chiếu. Streamlit được khuyến nghị, nhưng nhóm có thể dùng bất kỳ framework nào.
>
> URL:

## A2. Tool agent có

> Liệt kê các tool agent đang dùng. Mỗi tool 1 dòng: tên + làm được gì.

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
|  |  |  |
|  |  |  |

## A3. Câu hỏi mẫu để thử

> 3–5 câu hỏi/yêu cầu mẫu để team khác tự thử agent ngay.

1.
2.
3.

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
|  |  |  |  |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

Run thật: `python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json`
Provider/model: `openrouter` / `openai/gpt-4o-mini`. Run file: `runs/v3_B_group_openrouter_20260729T114235832771.json`.

Summary: `case_accuracy=0.6` (6/10 PASS), `tool_routing_accuracy=1.0`, `argument_accuracy=0.6`, `multiturn_accuracy=0.6` (3/5 multi-turn PASS), `provider_error_cases=0`, `measured_cases=10/10`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_news_url_vs_lookup | URL báo cụ thể → phải `fetch`, không phải `lookup` | `fetch{url: techcrunch.com/...}` | **PASS** — gọi đúng `fetch` với url khớp 100%. |
| G02_arxiv_search_vs_lookup | Yêu cầu tìm paper arXiv → `papers`, không phải `lookup` | `papers{query:"RLHF"}` | **PASS** — gọi `papers({query:'RLHF', max_results:5, sort_by:'lastUpdatedDate'})`, đúng tool + query. |
| G03_paper_text_max_pages_arg | Trích đúng `max_pages=2` từ "chỉ 2 trang đầu" | `paper_text{arxiv_url: full abs URL, max_pages:2}` | **FAIL** (wrong_arg_value) — model gọi `paper_text({arxiv_url:'2305.14314', max_pages:2})`: `max_pages` đúng, routing đúng, nhưng chuẩn hoá URL thành bare id thay vì giữ nguyên URL đầy đủ → string-match tuyệt đối của eval fail dù tool thực thi vẫn ra đúng bài báo. |
| G04_lookup_max_results_arg | Trích đúng `max_results=3` + `topic=news` + `timeframe=day` | `lookup{max_results:3, topic:news, timeframe:day}` | **PASS** — cả 3 arg khớp chính xác. |
| G05_arxiv_pdf_link_vs_fetch | Link PDF arXiv trực tiếp → `paper_text`, không phải `fetch` | `paper_text{arxiv_url: full pdf URL}` | **FAIL** (arg mismatch, case gắn nhãn wrong_tool) — routing đúng (`paper_text` được gọi, không lẫn `fetch`), nhưng `arxiv_url` lại bị rút gọn thành `'2305.14314'` thay vì URL PDF đầy đủ → cùng lỗi chuẩn hoá URL như G03. |
| M_G06_context_url_to_paper_text | Mang URL arXiv từ turn 1 sang, latest turn xin toàn văn → `paper_text` đúng url, không phải `fetch`/`papers` | `paper_text{arxiv_url: full abs URL}` | **FAIL** — routing đúng (không gọi nhầm `fetch`/`papers`), nhưng lại cùng lỗi rút gọn URL → bare id `'2305.14314'`. |
| M_G07_timeframe_correction | Turn 2 sửa "tuần này" → "hôm nay", phải cập nhật `timeframe=day` | `lookup{topic:news, timeframe:day}` | **PASS** — model cập nhật đúng `timeframe:'day'`, không giữ `week` cũ. |
| M_G08_switch_lookup_to_papers | Turn 2 đổi ý từ tin tức sang paper arXiv → `papers`, không giữ `lookup` | `papers{}` | **PASS** — model chuyển đúng sang `papers({query:'mô hình ngôn ngữ lớn', max_results:5})`. |
| M_G09_meta_capability_question | Câu hỏi meta về khả năng agent → không gọi tool nào | `no_tool:true` | **PASS** — model trả lời thẳng bằng text, không gọi tool. |
| M_G10_sort_by_correction | "mới đăng gần đây nhất" → `sort_by='submittedDate'` | `papers{sort_by:'submittedDate'}` | **FAIL** (wrong_arg_value) — model chọn `sort_by:'lastUpdatedDate'` thay vì `'submittedDate'`, nhầm giữa "ngày cập nhật" và "ngày đăng ban đầu". |

**Ghi chú pattern lỗi:** 3/4 case fail (G03, G05, M_G06) đều do cùng một nguyên nhân — model tự chuẩn hoá `arxiv_url` thành bare id (`2305.14314`) thay vì giữ URL đầy đủ như user cung cấp; `paper_text` tool vẫn chạy đúng ra kết quả (verify trong `tool_results` của run file) nên đây là lỗi format-arg do eval so khớp string tuyệt đối, không phải lỗi routing hay lỗi hiểu request. Case còn lại (M_G10) là lỗi thật về ngữ nghĩa arg (`sort_by`). `tool_routing_accuracy=1.0` xác nhận: agent luôn chọn đúng tool ở cả 10/10 case, toàn bộ điểm mất nằm ở `argument_accuracy`.

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên |  |  |  |
| Optional built-in |  |  |  |
| Bonus: tool mới thứ 4 trở đi |  |  |  |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?
