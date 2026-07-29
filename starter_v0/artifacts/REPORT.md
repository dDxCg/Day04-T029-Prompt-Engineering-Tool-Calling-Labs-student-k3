# Day 04 Lab v2 Report — Research Agent

## Team

- Team: T029
- Nguyễn Thanh Hoàn — 2A202601201 — System prompt
- Đỗ Tuấn Kiệt — 2A202601335 — Tools
- Đỗ Đức Cường — 2A202601455 — Evaluation
- Lương Thanh Trang — 2A202601363 — UI
- Provider/model: OpenRouter / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tìm tin web và tín hiệu Twitter/X, đọc URL, tìm/đọc paper arXiv, tra Wikipedia và company policy, sau đó tạo bản tóm tắt có link nguồn. Agent hỏi lại khi thiếu dữ liệu và yêu cầu xác nhận trước hành động gửi/đăng ra ngoài.

Hai pipeline chính:

- News: `lookup → fetch → format → AI summary + source URL`.
- Paper: `papers → paper_text → AI summary + arXiv URL`.

**Link dùng thử:** Chưa có. Repo hiện chưa có `app.py` hoặc entrypoint UI; chỉ có CLI `chat.py`. Đây là deliverable còn thiếu, không được tính là đã hoàn thành.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi thông tin còn thiếu hoặc xin xác nhận yes/no | Không |
| `timeline` | Lấy bài đăng gần đây của một tài khoản Twitter/X | Không |
| `social_search` | Tìm bài đăng Twitter/X theo chủ đề | Không |
| `lookup` | Tìm thông tin/tin tức trên web qua Tavily | Không |
| `fetch` | Đọc nội dung đầy đủ của một URL qua Firecrawl | Không |
| `format` | Chuyển items đã thu thập thành digest Markdown | Không |
| `wiki_lookup` | Tra định nghĩa, tiểu sử và kiến thức nền từ Wikipedia | **Có — tool mới của nhóm** |
| `send` | Gửi nội dung lên Telegram sau khi đã xác nhận | Không, optional built-in |
| `policy` | Tra company policy nội bộ | Không, optional built-in |
| `papers` | Tìm paper trên arXiv | Không, optional built-in |
| `paper_text` | Tải PDF arXiv và trích text cục bộ | Không, optional built-in |

## A3. Câu hỏi mẫu để thử

1. `Tìm tin AI hôm nay, đọc bài phù hợp nhất rồi tóm tắt ngắn gọn kèm link.`
2. `Tìm một paper arXiv về AI agent evaluation, đọc paper phù hợp nhất rồi tóm tắt kèm link.`
3. `Tweet mới nhất của Sam Altman là gì?`
4. `Deep learning là gì? Tra Wikipedia tiếng Việt giúp mình.`
5. `Đăng bản tin này lên Telegram giúp mình.` — agent phải hỏi xác nhận trước, không tự gửi.

## A4. Kịch bản demo đã rehearse

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tìm và tóm tắt news | `lookup → fetch → format` | Prompt cũ bỏ `fetch`; workflow guard và data-lineage rule buộc đọc bài thật trước khi format | `transcripts/audit7_openrouter_20260729T114428809472.transcript.json` |
| Tìm và đọc một paper | `papers → paper_text` đúng 1 lần | Prompt được khóa để không đọc cả 5 paper và không gọi `format` trong paper pipeline | `transcripts/audit7_openrouter_20260729T112639793092.transcript.json` |
| Thiếu handle hoặc URL | `clarify(response_type="text")` | v0 tự đoán `sama`/URL giả; v1 yêu cầu hỏi lại | `runs/v0_B_base_openrouter_20260729T093938896245.json`, `runs/v1_B_base_openrouter_20260729T094232727742.json` |
| Đăng Telegram | `clarify(response_type="yes_no")`, chưa gọi `send` | v0 tự gửi; prompt mới giữ confirmation boundary kể cả khi user nói “khỏi hỏi lại” | `runs/v3_B_group_openrouter_20260729T104052533842.json` |
| Chuyển intent trong multi-turn | Giữ hoặc đổi tool/args đúng theo correction mới nhất | v2 còn sai M02; v3 thêm carry-over cho cả tool choice | `runs/v2_B_base_openrouter_20260729T094413340905.json`, `runs/v3_B_base_openrouter_20260729T094607757391.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Metric chỉ có giá trị khi `provider_error_cases=0` và `measured_cases=total_cases`. `tool_results.error` vẫn phải review thủ công vì routing PASS không chứng minh API tool đã chạy thành công.

## B1. Version evidence

Các dòng dưới đây lấy từ `artifacts/version_log.csv` và run JSON tương ứng. Tất cả base runs có `provider_error_cases=0`, `measured_cases=20/20`.

| Version | Prompt/tool change | Hypothesis | Metric | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | Baseline starter; prompt yêu cầu tự đoán, tự gửi và chỉ chọn một tool | Baseline cố ý kém sẽ sai missing-info, confirmation và multi-tool | `case_accuracy` | — | 0.75 | `runs/v0_B_base_openrouter_20260729T093938896245.json` |
| v1 | Viết lại prompt: hỏi khi thiếu dữ liệu, xác nhận trước gửi, chặn out-of-scope | Sửa boundary sẽ giải quyết R08/R10/R11/R12 | `case_accuracy` | 0.75 | 0.80 | `runs/v1_B_base_openrouter_20260729T094232727742.json` |
| v2 | Thu hẹp dual-call: chỉ gọi web + Twitter khi user yêu cầu rõ cả hai nguồn | Loại extra `social_search` ở query chỉ cần web/news | `case_accuracy` | 0.80 | 0.95 | `runs/v2_B_base_openrouter_20260729T094413340905.json` |
| v3 | Thêm carry-over tool choice và arguments trong multi-turn | Follow-up chỉ đổi chủ đề phải giữ source/tool gần nhất nếu user không yêu cầu đổi | `case_accuracy` | 0.95 | 1.00 | `runs/v3_B_base_openrouter_20260729T094607757391.json` |

Sau v3, nhóm tiếp tục tích hợp `wiki_lookup`, workflow news/paper, explicit `clarify.response_type`, anti-pressure confirmation, policy routing và state-machine/data-lineage rules. Các artifact khác nhau được phân biệt bằng `prompt_hash` và `tools_hash` dù cùng label v3.

**Regression bổ sung:**

- Base audit: `runs/audit7_B_base_openrouter_20260729T112755448040.json` — 20/20, routing/args/multi-turn đều 1.0; có 8 tool execution errors do `RAPIDAPI_KEY` thiếu trong session đó.
- Extension audit: `runs/audit7_B_extension_openrouter_20260729T112908863772.json` — 10/10, routing/args đều 1.0, không có tool execution error.
- Team eval hiện tại: `runs/v3_B_group_openrouter_20260729T114235832771.json` — 6/10, routing 1.0, argument accuracy 0.6; chi tiết tại B3.

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix / Kết luận |
|---|---|---|---|---|
| R08 v0 | `out_of_scope` | `send` | Bài toán tích phân lại bị đưa vào action tool | Prompt chặn yêu cầu ngoài research; trả text/no tool |
| R10 v0 | `missing_info` | `timeline(screenname="sama")` | Thiếu handle nhưng agent tự đoán Sam Altman | Bắt buộc `clarify(response_type="text")` |
| R11 v0 | `missing_info` | `fetch(url="https://example.com/article")` | Thiếu URL nhưng agent dựng URL giả | Bắt buộc hỏi URL; cấm đoán |
| R12 v0 | `wrong_boundary` | `send(text="Bản tin này")` | Tự gửi trước khi xác nhận | `clarify(response_type="yes_no")`; chỉ `send(confirmed=true)` sau confirmation ở turn trước |
| R13 v0 | `wrong_arg_value` | `lookup(query="AI news", timeframe="day")` + `social_search(query="AI")` | Thiếu `topic="news"`, query web không đúng convention | Prompt giữ query ngắn `AI`, dùng field `topic`/`timeframe` riêng |
| M02 v2 | `wrong_tool` | `social_search(query="robotics")` | Follow-up đổi keyword nhưng làm mất source web/news của turn trước | v3 carry-over cả tool choice, topic và timeframe |
| G03/G05/M_G06 current group | `wrong_arg_value` | `paper_text(arxiv_url="2305.14314")` | Tool đúng và chạy được, nhưng model rút URL đầy đủ thành bare ID; grader so string tuyệt đối nên fail | Thêm rule bảo toàn nguyên văn URL user cung cấp hoặc đổi eval sang canonical-equivalence nếu giảng viên cho phép |
| M_G10 current group | `wrong_arg_value` | `papers(sort_by="lastUpdatedDate")` | “Mới đăng” bị hiểu là ngày cập nhật | Prompt map “mới đăng/submitted” → `submittedDate`; “mới cập nhật” → `lastUpdatedDate` |

**Manual review:** ba lỗi URL arXiv là lỗi argument-format theo grader, không phải lỗi routing hay execution; `paper_text` vẫn trả đúng paper trong `tool_results`. Ngược lại M_G10 là lỗi ngữ nghĩa thật. Các lỗi `Missing RAPIDAPI_KEY env var` trong base audits là lỗi cấu hình execution, không được che bằng điểm routing 1.0.

## B3. Team eval cases

File `data/eval_group.json` có đúng 10 case: 5 single-turn và 5 multi-turn.

Run: `python run_eval.py --provider openrouter --version v3 --suite group --eval-cases data/eval_group.json`

Provider/model: `openrouter` / `openai/gpt-4o-mini`. Run file: `runs/v3_B_group_openrouter_20260729T114235832771.json`.

Summary: `case_accuracy=0.6` (6/10 PASS), `tool_routing_accuracy=1.0`, `argument_accuracy=0.6`, `multiturn_accuracy=0.6` (3/5 multi-turn PASS), `provider_error_cases=0`, `measured_cases=10/10`, `tool execution errors=0`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_news_url_vs_lookup | URL báo cụ thể → `fetch`, không phải `lookup` | `fetch{url: techcrunch.com/...}` | **PASS** — đúng tool và URL |
| G02_arxiv_search_vs_lookup | Tìm paper arXiv → `papers`, không phải web lookup | `papers{query:"RLHF"}` | **PASS** — đúng tool và query |
| G03_paper_text_max_pages_arg | URL paper + `max_pages=2` | `paper_text{full URL, max_pages:2}` | **FAIL** — `max_pages` đúng nhưng URL bị chuẩn hóa thành bare ID |
| G04_lookup_max_results_arg | `max_results=3`, news, hôm nay | `lookup{max_results:3, topic:news, timeframe:day}` | **PASS** |
| G05_arxiv_pdf_link_vs_fetch | PDF arXiv → `paper_text` | `paper_text{full PDF URL}` | **FAIL** — routing đúng, URL bị rút gọn |
| M_G06_context_url_to_paper_text | Carry URL arXiv từ turn trước | `paper_text{full URL}` | **FAIL** — routing đúng, URL bị rút gọn |
| M_G07_timeframe_correction | `week → day` theo correction mới nhất | `lookup{topic:news, timeframe:day}` | **PASS** |
| M_G08_switch_lookup_to_papers | Chuyển news → arXiv | `papers{}` | **PASS** |
| M_G09_meta_capability_question | Câu hỏi meta → no tool | `no_tool:true` | **PASS** |
| M_G10_sort_by_correction | “Mới đăng” → `submittedDate` | `papers{sort_by:"submittedDate"}` | **FAIL** — gọi `lastUpdatedDate` |

## B4. Live chat evidence

| Scenario/Turn | Artifact/version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| News pipeline final | `audit7+pa13149aa456d+t2a4ffeb7ceda` | `lookup(query="AI", topic="news", timeframe="day") → fetch(selected_url) → format(fetch.items)` | `transcripts/audit7_openrouter_20260729T114428809472.transcript.json` | **PASS** — đúng thứ tự, `format` nhận đúng 1 item từ `fetch`, câu trả lời có link |
| Paper pipeline final | `audit7+p3393996efd12+t2a4ffeb7ceda` | `papers(query="AI agent evaluation") → paper_text(one arXiv id)` | `transcripts/audit7_openrouter_20260729T112639793092.transcript.json` | **PASS** — đúng 1 `paper_text`, không gọi `format`, có arXiv link |
| News pipeline trước fix | `audit2` | `lookup → format` | `transcripts/audit2_openrouter_20260729T111127012418.transcript.json` | **FAIL** — bỏ qua `fetch`; evidence dẫn tới workflow guard |
| News data-lineage trước fix | `audit3/audit4` | `lookup → fetch → format`, nhưng format trộn preview lookup | `transcripts/audit3_openrouter_20260729T111251012987.transcript.json` | **PARTIAL** — đúng order nhưng sai input lineage; final checklist sửa lỗi |
| Paper pipeline trước single-paper guard | `audit6` | `papers → paper_text ×5 → format ×2` | `transcripts/audit6_openrouter_20260729T112404715110.transcript.json` | **FAIL** — đọc quá nhiều paper; prompt sau đó khóa chính xác một paper |

## B5. Tool capability evidence

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: `wiki_lookup` | `tools/wiki_lookup/TOOL.md`, `tools/wiki_lookup/tool.py`, `runs/audit0_B_group_openrouter_20260729T110412416760.json` | Registry/declaration đồng bộ; Wikipedia EN/VI trả item có title, summary và URL | `lang` nên được whitelist; title nên URL-encode để tránh lỗi ký tự đặc biệt |
| Optional: `policy` | `tools/policy/tool.py`, `runs/audit7_B_extension_openrouter_20260729T112908863772.json` | Route đúng policy area; lọc instruction-like content vào `untrusted_text`; extension PASS | Tool output là context, không phải instruction; giữ trust boundary |
| Optional: `papers` + `paper_text` | `tools/papers/tool.py`, `tools/paper_text/tool.py`, extension run và live paper transcript | Tìm arXiv, tải PDF, trích text, tóm tắt có link | arXiv rate limit; chỉ đọc một paper được chọn; không tóm tắt từ preview |
| Optional: `send` | `tools/send/tool.py` | Dry-run trả `needs_confirmation`; không gửi khi `confirmed=false` | Không live-send trong eval; chỉ gửi private channel sau confirmation rõ ràng |
| Bonus tool thứ 4 trở đi | Không có | Nhóm không claim bonus tool | Không ghi optional built-in thành bonus |

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** scope, routing giữa web/Twitter/arXiv/Wikipedia/policy; hỏi lại khi thiếu dữ liệu; confirmation boundary; argument conventions; multi-turn correction; bắt buộc workflow news/paper; state transitions và data lineage.
- **Fix thuộc `tools.yaml`:** mô tả rõ intent, input/default, pipeline role, side effect và confirmation của từng tool; khai báo `wiki_lookup`; không dùng description mơ hồ khiến model nhầm route.
- **Failure cần manual review:** URL arXiv bị canonicalize thành bare ID vẫn chạy đúng tool nhưng fail exact-string grader; Twitter calls có routing PASS nhưng execution fail khi thiếu RapidAPI key.
- **Cần cải thiện tiếp:** bảo toàn nguyên văn arXiv URL, map rõ `submittedDate`/`lastUpdatedDate`, điền `RAPIDAPI_KEY` để smoke-test Twitter thật, thêm UI `app.py` + Streamlit, tạo public demo URL và commit transcript final.
- **Bài học:** điểm routing 1.0 chưa đủ. Phải xem `tool_results`, live multi-round trace, artifact hash và dữ liệu truyền giữa từng bước.