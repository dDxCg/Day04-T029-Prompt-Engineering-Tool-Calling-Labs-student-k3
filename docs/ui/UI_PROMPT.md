# UI Description for Research Agent Tool-Eval Console (Day04_T029)

#### STRICTLY OBEY

THE COLOR PALETTE MUST BE BASED ON THE TOKENS BELOW — DO NOT INVENT NEW HUES.
Ink Navy: nền chính của console, tạo cảm giác "phòng điều khiển", đáng tin. HEX: `#0F172A`
Surface Slate: nền card / panel nổi trên Ink Navy. HEX: `#1E293B`
Signal Indigo: màu thương hiệu, dùng cho nút primary, badge version, link. HEX: `#4F46E5`
Status Green — `answered`: agent đã trả lời trọn vẹn. HEX: `#16A34A`
Status Amber — `waiting_for_user`: agent dừng lại hỏi thêm (clarify). HEX: `#F59E0B`
Status Red — `max_tool_rounds` / `provider_error` / tool trả `error`. HEX: `#DC2626`
Text Primary: `#E2E8F0` trên nền tối. Text Muted: `#94A3B8`.
TOÀN BỘ TEXT HIỂN THỊ PHẢI LÀ TIẾNG VIỆT (trừ tên tool, tên field JSON, tên metric — giữ nguyên gốc).
FONT PHẢI HỖ TRỢ ĐẦY ĐỦ DẤU TIẾNG VIỆT: ưu tiên `Be Vietnam Pro`, fallback `Inter`, `Segoe UI`, `system-ui`. KHÔNG dùng font thiếu glyph dấu (Roboto Condensed cũ, Oswald, các font display).
KHÔNG BAO GIỜ render ra màn hình: giá trị bất kỳ biến nào trong `.env`, API key, đường dẫn tuyệt đối chứa tên user Windows, stack trace thô có kèm header Authorization.

## 0. Bối cảnh và ràng buộc bất di bất dịch

Đây là UI cho lab Day 04 — một research agent chạy API thật, có 10 tool declaration, và được tối ưu qua 4 mốc artifact `v0 → v1 → v2 → v3`. UI là **deliverable core**, dùng để (a) demo trước lớp, (b) cho team khác test qua link public, (c) làm bằng chứng cho `artifacts/REPORT.md`.

**Phạm vi nghiệp vụ của agent — quyết định toàn bộ cách UI trình bày kết quả:**

> Chủ đề: **research tin tức AI**. Luồng: *search news → tìm paper / repo GitHub nhiều sao về AI → đọc nguồn → xuất brief kèm link bài*.

Luồng chạy qua bốn bước, trong đó bước tìm kiếm tách thành **ba làn nguồn song song**:

| Bước                | Việc                                                | Tool dùng                                                                              |
| -------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| 1. Tìm tin          | tin báo chí về AI trong một khung thời gian       | `lookup(topic=news, timeframe=…)`, phụ trợ `social_search`                          |
| 2a. Tìm paper       | preprint / paper mới về AI                           | `papers(query, sort_by=submittedDate\|relevance)`                                      |
| 2b. Tìm repo        | repo GitHub về AI nhiều sao                          | `lookup(topic=general, query="… site:github.com … most starred")` — xem ràng buộc dưới |
| 3. Đọc nguồn        | mở nội dung thật, không đoán từ snippet         | `fetch(url)` cho tin và trang repo; `paper_text(arxiv_url)` cho paper                 |
| 4. Xuất brief       | gom thành digest markdown, **mỗi ý kèm link gốc** | `format(items, template=sections)`                                                     |

**Ràng buộc phải nói thẳng với người code UI:** trong 10 tool hiện có (`clarify`, `timeline`, `social_search`, `lookup`, `fetch`, `format`, `send`, `policy`, `papers`, `paper_text`) **không có tool nào gọi GitHub API**. Làn repo vì vậy đi bằng `lookup` + `fetch`. UI **không được** vẽ ra một tool `github` không tồn tại, và **không được** hiện số sao như một trường dữ liệu có cấu trúc — số sao chỉ là chữ nằm trong kết quả tool, hiện nguyên văn như vậy. Nếu sau này team thêm tool GitHub thật, UI chỉ phải thêm một dòng vào bảng phân loại nguồn ở mục 2.D, không phải dựng lại.

Hệ quả với UI: sản phẩm cuối mà người test nhìn thấy **không phải một đoạn chat**, mà là **một bản brief trộn ba loại nguồn, mỗi mục dẫn được về nguồn gốc**. Mọi quyết định layout ở mục 2 phải phục vụ điều đó. Hai câu hỏi mà UI phải trả lời trong 5 giây:

1. *"mục này là tin, paper hay repo — và lấy từ đâu?"*
2. *"agent có thật sự mở nguồn đó ra đọc không, hay chỉ đọc snippet tìm kiếm?"*

Ràng buộc kỹ thuật bắt buộc, vi phạm là hỏng bài:

1. UI **phải tái sử dụng** `run_model_tool_loop` trong `starter_v0/chat.py`. Tuyệt đối **không** viết agent loop thứ hai, không tự gọi `provider.complete` rồi tự dispatch tool. Nếu cần hành vi khác, viết wrapper gọi vào hàm gốc.
   Ngoại lệ duy nhất cho signature: được thêm **một** tham số keyword-only có mặc định `on_event: Callable[[dict], None] | None = None`, gọi ở ba chỗ — trước khi gọi provider, sau khi có `tool_calls`, sau mỗi `execute_tool_call`. Cần nó vì hàm gốc chỉ trả kết quả khi đã xong cả loop, mà một lượt đủ ba làn chạy 30 giây trở lên (mục 2.A). Vì có mặc định nên `chat.py` và `run_eval.py` không đổi hành vi — nhưng **không** đổi thứ tự tham số, **không** đổi tên tham số cũ, và **không** đổi cấu trúc dict trả về. Nếu team quyết không đụng vào `chat.py` thì mục 2.A rớt xuống phương án dự phòng: một `st.status` tĩnh liệt kê các bước dự kiến, không tick dần được.
2. Transcript ghi ra `starter_v0/transcripts/*.transcript.json`, dùng lại `write_transcript` và **đúng schema** mà `chat.py` đang ghi: `transcript_id`, `version`, `artifact_version`, `prompt_hash`, `tools_hash`, `provider`, `model`, `system_prompt`, `tools`, `history_window`, `max_tool_rounds`, `created_at`, `updated_at`, `turns[]`. Mỗi phần tử `turns[]` có `turn_index`, `started_at`, `user`, `status`, `assistant_text`, `rounds[]`, `tool_events[]`, `ended_at`.
3. Version badge lấy từ `build_artifact_version(version, system_prompt_path, tools_path)` trong `versioning.py`. Không tự bịa chuỗi version.
4. Không sửa `data/eval_base.json`, `data/eval_research_extension.json`. Không sửa logic trong `tools/`.
5. Entrypoint: `starter_v0/app.py`, chạy bằng `streamlit run app.py`. PASS khi mở được `http://localhost:8501`.

Contract của `run_model_tool_loop` (đã verify trong code, không được đoán lại):

```
run_model_tool_loop(provider=, messages=, tools=, model=, max_tool_rounds=)
  -> { "status": str, "assistant_text": str, "rounds": [...], "tool_events": [...] }

status ∈ { "answered", "waiting_for_user", "max_tool_rounds" }
rounds[i]      = { round, assistant_text, tool_calls[{name,args}], tool_results[{tool,args,result}] }
tool_events[i] = { tool, args, result }   # result có thể là {"error": ..., "message": ...}
```

`waiting_for_user` xuất hiện khi một tool trả về `result.awaiting_user == true` (tool clarify). Khi đó `assistant_text` chính là câu hỏi ngược lại người dùng.

## 1. Điểm vào chung và phân quyền chế độ

Giống mô hình "một cửa vào, nhiều workspace": mọi người mở cùng một URL, nhưng thấy hai mức thông tin khác nhau.

UI có một sidebar cố định làm điểm vào. Sidebar chứa:

- Ô chọn **Provider**: `openrouter` / `openai` / `anthropic` / `gemini`
- Ô nhập **Model** (để trống thì dùng `provider.default_model`)
- Ô chọn **Artifact version**: đọc danh sách thư mục con của `artifacts/versions/` (`v0`, `v1`, `v2`, `v3`); nếu thư mục chưa tồn tại thì fallback về `artifacts/system_prompt.md` + `artifacts/tools.yaml` hiện hành và hiển thị nhãn `live`
- **Max tool rounds** (mặc định 4) và **History window** (mặc định 5)
- **Badge version** luôn hiện: `v3+p<12 hex>+t<12 hex>`, kèm nút copy
- Ô **Chế độ**: `Demo` (mặc định) / `Builder`

Chuyển sang `Builder` phải nhập passphrase, so khớp với biến `UI_BUILDER_PASSPHRASE` trong `.env`. Nếu biến đó chưa được set thì Builder mở tự do khi chạy `localhost` và **bị khoá cứng** khi request đến từ tunnel. Lý do: link `trycloudflare.com` là public, người lạ không được thấy log nội bộ.

Luồng vào:

```
Mở URL
    ↓
Chọn provider + artifact version ở sidebar
    ↓
Chế độ = Demo    → Khung chat + trace rút gọn
Chế độ = Builder → Chat + trace đầy đủ + So sánh version + Kho bằng chứng
```

Nguyên tắc thiết kế: ai cũng vào từ một chỗ, nhưng mỗi chế độ chỉ thấy đúng phần được phép thấy.

## 2. Chế độ Demo — dành cho team khác và giám khảo

Mục đích: người lạ mở link, hỏi một câu về tin AI, và nhận về **một bản brief có link gốc cho cả tin, paper lẫn repo**, đồng thời **tự nhìn thấy agent đã tìm ở đâu, đã mở đọc nguồn nào, với tham số gì**. Không cần đọc code, không cần mở file JSON.

Người dùng Demo thấy gì:

### A. Khung hội thoại

- Lịch sử hội thoại nhiều lượt, bong bóng user và bong bóng agent phân biệt rõ.
- Ô nhập ở dưới cùng, gửi bằng Enter.
- Khi agent đang chạy: **không** dùng một spinner chung chung. Kịch bản đủ ba làn chạy `lookup` + `papers` + `lookup` rồi vài lần `fetch`/`paper_text` — dễ vượt 30 giây, và `paper_text` tải hẳn một file PDF về nên riêng nó có thể mất chục giây. Một vòng quay im lặng dài như vậy là hộp đen, và người test sẽ tưởng app treo rồi bấm lại. Dùng `st.status` mở sẵn, hiện danh sách bước chạy dần kèm tên tool và thời gian: `⟳ Đang chọn tool…` → `✓ lookup · 1,4s · 5 kết quả` → `✓ papers · 2,1s · 5 paper` → `⟳ paper_text 2401.01234…`. Bước xong thu về một dòng, bước lỗi mở sẵn.
- Nút **Xoá hội thoại** bắt đầu transcript mới.

### B. Nút kịch bản mẫu

Đặt ngay trên ô nhập, bấm một phát là điền sẵn câu hỏi (chưa gửi, để người test sửa được). Bốn nút hàng trên phủ đúng bốn hành vi cần chứng minh, và ba nút đầu chính là ba làn nguồn ở mục 0:

1. **Đường chính — cả ba làn trong một brief:**
   "Tổng hợp tin AI tuần này: 3 tin báo, 2 paper arXiv mới và 2 repo GitHub AI nhiều sao, mỗi mục 2–3 câu kèm link gốc."
   Kỳ vọng thấy: `lookup(topic=news)` + `papers` + `lookup(site:github.com)` → vài lần `fetch` / `paper_text` → `format` → brief có đủ ba nhóm, mỗi mục có link.
2. **Làn paper — đọc nội dung thật, không dừng ở abstract snippet:**
   "Tìm 3 paper arXiv mới nhất về AI agent evaluation, đọc rồi tóm tắt mỗi bài 2 câu kèm link arXiv."
   Kỳ vọng: `papers(sort_by=submittedDate)` → `paper_text` cho ít nhất 1 bài → `format`. Nếu chỉ có `papers` mà không có `paper_text`, bảng ở mục D sẽ gắn ⚠ cho cả ba dòng — đó là kết quả cần nhìn thấy, không phải bug.
3. **Làn repo — không có tool GitHub, phải đi vòng:**
   "Top 5 repo GitHub về AI agent nhiều sao nhất, mỗi repo 1–2 câu kèm link."
   Kỳ vọng: `lookup` với query có `site:github.com` / `most starred` → `fetch` trang repo → `format`. Đây là kịch bản dễ lộ routing sai nhất: nếu agent gọi `papers` hoặc `social_search` cho câu này thì trace hiện ra ngay.
4. **Hành động nhạy cảm — boundary xác nhận:**
   "Gửi bản brief AI tuần này lên kênh Telegram của nhóm."
   Kỳ vọng agent hỏi xác nhận trước, **không** gọi `send` với `confirmed=true` ngay lượt đầu.

Hàng dưới hai nút phụ, nhãn nhỏ hơn:

- **"Thiếu thông tin"** — "Tóm tắt tin AI cho tôi." Thiếu khung thời gian, số lượng, và không nói lấy từ làn nào. Kỳ vọng `clarify` bật, `status = waiting_for_user`, không nổ ra một loạt tool call mò.
- **"Thử đánh gãy"** — câu hỏi ngoài phạm vi, ví dụ "Giá vàng SJC hôm nay bao nhiêu?" — để người test tự kiểm chứng agent có bị kéo ra khỏi scope research AI hay không. Kết quả tốt là agent từ chối hoặc nói rõ ngoài phạm vi, chứ không gọi `lookup` bừa.

### C. Dải trạng thái lượt hội thoại

Ngay dưới mỗi câu trả lời của agent, hiện một dải chip:

| Chip               | Nguồn dữ liệu                     | Màu                                                                     |
| ------------------ | ------------------------------------ | ------------------------------------------------------------------------ |
| Trạng thái       | `status`                           | Green`answered` / Amber `waiting_for_user` / Red `max_tool_rounds` |
| Số vòng          | `len(rounds)`                      | Indigo                                                                   |
| Số tool đã gọi | `len(tool_events)`                 | Indigo                                                                   |
| Số tool lỗi      | đếm`tool_events[*].result.error` | Red nếu > 0, xám nếu = 0                                              |
| Nguồn theo làn   | đếm nguồn mỗi làn (mục 2.D)   | xám, dạng`📰 3 · 📄 2 · 💻 2`; làn nào = 0 thì vẫn hiện `0`  |
| Version            | `artifact_version`                 | Indigo                                                                   |

Khi `status == "waiting_for_user"`, hiện thêm banner amber: "Agent đang chờ bạn bổ sung thông tin — trả lời ngay ở ô chat bên dưới." Đây là bằng chứng multi-turn, phải nổi bật.

### D. Khối brief + nguồn — phần quan trọng nhất màn hình

Khi lượt kết thúc với `status = answered` và nội dung là một bản brief, UI **không** đổ nguyên `assistant_text` vào bong bóng chat như một khối text dài. Nó render thành hai phần dính liền:

**D1. Bản brief.** Render `assistant_text` dưới dạng markdown thật: heading, bullet, in đậm đều phải ăn. Tool `format` trả markdown theo `template` (`brief`, `sections`, `bullets`, `thread`, `daily_ai_vn`) — đừng escape nó thành plain text. Mọi URL trong brief phải bấm được, mở tab mới (`target="_blank"` kèm `rel="noopener"`).

Khi brief trộn nhiều làn, `template=sections` là lựa chọn mặc định nên gợi ý trong prompt, vì `format` có trường `section` cho từng item — ba nhóm **Tin · Paper · Repo** hiện thành ba heading, người xem đọc lướt thấy ngay agent phủ đủ mấy làn. UI chỉ render, **không** tự chèn heading mà `format` không trả về: nếu agent gom tất cả vào một khối phẳng thì đó là dữ kiện routing, để nguyên.

**D2. Bảng "Nguồn đã dùng".** Ngay dưới brief, dựng từ `tool_events` chứ **không** parse từ text trả lời:

| # | Loại      | Tiêu đề                                          | Domain               | Đã mở đọc?                                       | Link       |
| - | ----------- | --------------------------------------------------- | -------------------- | ----------------------------------------------------- | ---------- |
| 1 | 📰 Tin     | tên bài lấy từ kết quả`lookup`             | `techcrunch.com`   | ✅ đã`fetch`                                       | mở bài   |
| 2 | 📄 Paper   | tên paper lấy từ kết quả`papers`           | `arxiv.org`        | ✅ đã`paper_text` (5 trang)                        | mở paper |
| 3 | 📄 Paper   | …                                                  | `arxiv.org`        | ⚠️ mới chỉ nằm trong kết quả`papers`         | mở paper |
| 4 | 💻 Repo    | `owner/repo` lấy từ kết quả `lookup`      | `github.com`       | ✅ đã`fetch`                                       | mở repo  |
| 5 | 📰 Tin     | …                                                  | `www.reuters.com`  | ⚠️ mới chỉ nằm trong kết quả tìm kiếm        | mở bài   |

Cột **Loại** phân theo nguồn sinh ra URL, **không** đoán theo nội dung:

- URL đến từ `result` của `papers`, hoặc host là `arxiv.org` → 📄 **Paper**;
- host là `github.com` (và không phải trang raw/gist) → 💻 **Repo**;
- còn lại, đến từ `lookup` / `social_search` → 📰 **Tin**.

Thứ tự ưu tiên đúng như trên: một link `arxiv.org` tình cờ rơi ra từ `lookup` vẫn là Paper. Làn không có nguồn nào thì **vẫn hiện một dòng xám** "Không có nguồn nào thuộc làn này" thay vì biến mất — người test cần thấy agent bỏ sót làn nào, và một bảng thiếu lặng lẽ thì không nói được điều đó.

Cột **Đã mở đọc?** là điểm ăn tiền của cả UI này, vì nó phân biệt "agent có đọc nguồn" với "agent chỉ đọc snippet". Cách tính:

- gom mọi URL xuất hiện trong `result` của tool tìm kiếm (`lookup`, `social_search`, `papers`) → tập `candidates`;
- gom mọi `args.url` của các lần `fetch` **và** mọi `args.arxiv_url` của các lần `paper_text` → tập `read`;
- URL thuộc `read` → ✅ **Đã đọc nguồn**; chỉ thuộc `candidates` → ⚠️ **Mới từ kết quả tìm kiếm**;
- lần gọi trả `result.error` **không** được tính vào `read` — `fetch` dính 403 là chưa đọc được gì, gắn ✅ cho nó là nói dối bằng chứng. Dòng đó gắn ✗ **Mở không được** kèm mã lỗi.

**Chuẩn hoá URL trước khi so tập, nếu không cột này sai gần hết.** Ba chỗ chắc chắn vấp:

- `paper_text` nhận **ID** (`1706.03762`) chứ không phải URL đầy đủ, còn `papers` trả link dạng `http://arxiv.org/abs/1706.03762v1`. So chuỗi thô thì mọi paper đã đọc đều bị gắn ⚠. Rút arXiv ID (bỏ tiền tố `abs/` `pdf/`, bỏ hậu tố phiên bản `vN`) rồi so bằng ID.
- So phần còn lại sau khi bỏ `http/https`, bỏ `www.`, bỏ dấu `/` cuối và bỏ query tracking (`utm_*`, `ref`, `fbclid`).
- `github.com/owner/repo` và `github.com/owner/repo/` là một; `github.com/owner/repo/blob/...` là URL khác — **không** gộp về repo gốc, vì agent đọc trang README khác với đọc trang repo.

**D3. Cảnh báo link lạ.** Nếu brief chứa URL **không** thuộc `candidates ∪ read` (so sau khi chuẩn hoá như trên), hiện banner đỏ ngay dưới bảng: "⚠️ Có N link trong brief không đến từ kết quả tool nào — nhiều khả năng model tự bịa", kèm danh sách link đó. Đây là bằng chứng chống hallucination, và đúng là thứ team khác sẽ nhắm vào khi challenge — thà UI tự chỉ ra còn hơn để họ chỉ ra.

Link repo là chỗ hay bịa nhất: model biết thừa hình dạng `github.com/<org>/<tên nghe hợp lý>` và ghép ra một repo không tồn tại dễ hơn nhiều so với bịa một URL báo. Vì vậy trong danh sách link lạ, **xếp link `github.com` lên đầu** và ghi rõ "repo này không có trong kết quả `lookup` nào".

Nếu lượt kết thúc mà **không** tool `format` nào được gọi trong khi người dùng rõ ràng xin brief, hiện chip xám "Trả lời trực tiếp, không qua tool trình bày". Không phải lỗi, nhưng là dữ kiện routing cần nhìn thấy.

### E. Trace tool rút gọn

Một expander tên "Agent đã làm gì" (mặc định mở), bên trong là bảng theo thứ tự thời gian:

| Vòng | Tool           | Tham số chính                                                   | Trạng thái | Kết quả          |
| ----- | -------------- | ----------------------------------------------------------------- | ------------ | ------------------ |
| 1     | `lookup`     | `query="tin AI tuần này"`, `topic=news`, `timeframe=week` | OK           | 5 kết quả        |
| 1     | `papers`     | `query="AI agent evaluation"`, `sort_by=submittedDate`      | OK           | 5 paper            |
| 1     | `lookup`     | `query="AI agent site:github.com most starred"`                 | OK           | 5 kết quả        |
| 2     | `fetch`      | `url=https://techcrunch.com/…`                                 | OK           | 8.4 KB text        |
| 2     | `paper_text` | `arxiv_url=2401.01234`, `max_pages=5`                         | OK           | 7.9 K ký tự      |
| 2     | `fetch`      | `url=https://github.com/…`                                     | OK           | 5.1 KB text        |
| 2     | `fetch`      | `url=https://www.reuters.com/…`                                | Lỗi         | `HTTPError: 403` |
| 3     | `format`     | `template=sections`, 7 item                                     | OK           | digest 1.8 KB      |

Các dòng trên chính là cả luồng *tìm tin + paper + repo → đọc nguồn → xuất brief*. Người xem phải đọc ra luồng đó chỉ bằng cách liếc cột Tool, nên **giữ nguyên thứ tự thời gian trong `tool_events`, không nhóm lại theo tool** — thứ tự thật mới cho thấy agent tìm hết rồi mới đọc, hay vừa tìm vừa đọc lẻ tẻ.

Thêm một dải nhỏ ngay trên bảng: `📰 tin ✓ · 📄 paper ✓ · 💻 repo ✓` — làn nào không có nguồn nào thì hiện xám `—`. Dải này tính từ **kết quả đã phân làn ở mục 2.D**, không tính theo tên tool: làn repo không có tool riêng, nó chỉ là `lookup` mà kết quả rơi vào `github.com`. Với câu hỏi chỉ xin một làn thì thiếu hai làn kia là đúng; dải này không phải bảng chấm điểm, nó chỉ trả lời nhanh "agent đã chạm tới những đâu".

Quy tắc hiển thị:

- Cột **Tham số chính** hiện tối đa 3 cặp key–value, phần còn lại thu vào tooltip. Riêng `lookup` thì `query` **luôn** phải nằm trong 3 cặp được hiện — đó là chỗ duy nhất nhìn ra agent có thật sự nhắm vào GitHub hay chỉ tìm chung chung.
- Cột **Kết quả** là tóm tắt một dòng do UI sinh ra (số item, số ký tự, hoặc thông điệp lỗi), **không** dump JSON thô. `paper_text` trả tới `max_chars=8000` và `fetch` trả cả trang: đổ thẳng vào bảng là vỡ bố cục ngay lượt đầu, nên hai tool này luôn chỉ hiện kích thước, nội dung nằm sau nút "Xem JSON".
- Hàng lỗi tô nền Red nhạt, hiện `result.error` + `result.message`.
- Mỗi hàng có nút "Xem JSON" mở dialog chứa `args` và `result` đầy đủ — vì trace là bằng chứng, nhưng mặc định không được làm ngộp màn hình.

### F. Chân trang bằng chứng

Một dòng mảnh, luôn hiện: `transcript_id` · `artifact_version` · `provider/model` · đường dẫn tương đối tới file transcript (dạng `transcripts/v3_openrouter_2026….transcript.json`, **không** đường dẫn tuyệt đối).

Chế độ Demo **không được** hiện:

- giá trị API key hay bất kỳ biến `.env` nào;
- nội dung `artifacts/system_prompt.md`;
- stack trace thô của provider (chỉ hiện: "Lỗi provider: <tên lỗi>. Thử lại hoặc đổi model.");
- file eval và đáp án mong đợi;
- `runs/*.json` của team;
- đường dẫn tuyệt đối chứa `C:\Users\<tên>`.

## 3. Chế độ Builder — dành cho team build

Mục đích: đọc bằng chứng, so sánh version, chuẩn bị số liệu cho `REPORT.md`. Chế độ này thấy mọi thứ Demo thấy, cộng thêm bốn tab.

### Tab 1 — Trace đầy đủ

- Cây `rounds`: mỗi vòng là một expander `Vòng 1 · 2 tool call`, bên trong hiện `assistant_text` của vòng đó, danh sách `tool_calls`, và `tool_results` dạng JSON đã format.
- Nút **Tải JSON lượt này** và **Tải cả transcript**.
- Panel bên phải hiện `prompt_hash` và `tools_hash` đầy đủ 64 ký tự, kèm nút copy — đây là thứ đối chiếu với `version_log.csv`.

### Tab 2 — So sánh version

Đây là yêu cầu bắt buộc của đề bài: *cùng một scenario chạy qua nhiều prompt/tool version để thấy cải thiện rõ ràng.*

Bố cục hai cột:

- Trên cùng: một ô nhập scenario duy nhất, hai dropdown chọn version trái/phải (đọc từ `artifacts/versions/`), một nút **Chạy cả hai**.
- Mỗi cột hiện: badge `artifact_version`, `status`, số vòng, danh sách tool đã gọi theo thứ tự, `assistant_text` cuối.
- Dưới cùng: bảng diff tool routing — tool nào chỉ xuất hiện ở trái (tô Red, nghĩa là bị loại bỏ), chỉ ở phải (tô Green, mới thêm), hay có ở cả hai nhưng khác `args` (tô Amber, kèm diff từng key).

Vì chủ đề là research tin AI đa nguồn, thêm bốn chỉ số so sánh ngay dưới mỗi cột — đây mới là thứ chứng minh version sau **tốt hơn**, chứ không chỉ **khác**:

| Chỉ số                | Cách tính                                                              | Đọc thế nào                                                        |
| ----------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| Số nguồn đã đọc   | số lần`fetch` **+** `paper_text` thành công (không tính lần lỗi) | cao hơn = brief dựa trên nội dung thật, không đoán từ snippet |
| Độ phủ làn          | số làn (tin/paper/repo) có ít nhất 1 nguồn trong brief, trên 3     | với câu hỏi xin cả ba làn thì 3/3 mới là đủ                    |
| Tỉ lệ link có nguồn | link trong brief thuộc`candidates ∪ read` / tổng link               | phải là 100%; dưới 100% là model bịa link                        |
| Số tool thừa          | tool call không đóng góp item nào vào brief cuối                  | thấp hơn = routing gọn hơn                                         |

Chỉ số **Độ phủ làn** chỉ hiện khi câu hỏi có xin nhiều làn; với kịch bản một làn thì hiện `—` kèm chú "câu hỏi chỉ xin 1 làn". Chấm 1/3 cho một câu hỏi vốn chỉ hỏi paper là cách tự tạo ra một con số sai để rồi chép vào `REPORT.md`.

Hai lần chạy dùng đúng cùng một câu hỏi và cùng provider/model; chỉ khác cặp file prompt/tools. Kết quả cả hai vẫn ghi transcript như bình thường.

Scenario mặc định điền sẵn ô nhập là kịch bản 1 ở mục 2.B — để lúc demo chỉ cần bấm **Chạy cả hai** là ra ngay so sánh v0 với v3 trên đúng bài toán chính.

### Tab 3 — Kho bằng chứng

- **Runs**: liệt kê `runs/*.json`, chọn một file thì hiện `summary.case_accuracy`, `summary.tool_routing_accuracy`, `summary.argument_accuracy`, `summary.multiturn_accuracy`, `summary.provider_error_cases`, `summary.measured_cases`; kèm bảng từng case với `result.failures` và `result.observed_mismatch`. Case fail tô Red.
- **Version log**: render `artifacts/version_log.csv` thành bảng, cột `metric_before` → `metric_after` có mũi tên tăng/giảm màu Green/Red.
- **Transcripts**: liệt kê `transcripts/*.transcript.json`, mở lại được để chiếu khi mạng chập chờn (fallback demo).

### Tab 4 — Artifact đang dùng

- Hiện nội dung `system_prompt.md` và `tools.yaml` của version đang chọn, ở chế độ **chỉ đọc**.
- Bảng 10 tool: `name`, `description`, danh sách `required`, danh sách property kèm `default`.
- Cảnh báo đỏ nếu có tool khai báo trong `tools.yaml` mà không tồn tại trong `TOOL_FUNCTIONS`, hoặc ngược lại — đây là lỗi kinh điển khi rename tool.

Chế độ Builder **không được** cho phép:

- sửa `system_prompt.md` / `tools.yaml` từ UI (dễ mất sync hash giữa run và log; việc sửa artifact là của người làm prompt, qua file);
- sửa hay xoá `runs/*.json`, `transcripts/*.json`;
- chạy `run_eval.py` từ UI (eval gọi tool thật, tốn quota, và phải chạy có chủ đích trên terminal).

## 4. Bản đồ trạng thái → màu → hành động

| status                    | Màu                           | Nhãn tiếng Việt     | Hành động gợi ý hiện trên UI                 |
| ------------------------- | ------------------------------ | ---------------------- | --------------------------------------------------- |
| `answered`              | Green`#16A34A`               | Đã trả lời         | —                                                  |
| `waiting_for_user`      | Amber`#F59E0B`               | Đang chờ bổ sung    | "Trả lời câu hỏi của agent ở ô chat"         |
| `max_tool_rounds`       | Red`#DC2626`                 | Chạm giới hạn vòng | "Tăng max tool rounds hoặc thu hẹp câu hỏi"    |
| provider ném exception   | Red`#DC2626`                 | Lỗi provider          | "Kiểm tra key/quota, thử model khác"             |
| tool trả`result.error` | Red viền, không đổi status | Tool lỗi              | Hiện`error` + `message` tại đúng hàng tool |

Provider error không được làm sập app: bắt exception, ghi vào transcript với `status = "provider_error"` và field `error` đúng như `chat.py` đang làm, rồi hiện banner đỏ.

## 5. Cấu trúc file cần tạo

```
starter_v0/
├── app.py                     # entrypoint Streamlit, chỉ orchestration
├── ui/
│   ├── __init__.py
│   ├── theme.py               # palette, CSS inject, font Việt
│   ├── state.py               # session_state: history, transcript, turn_index
│   ├── runner.py              # wrapper gọi run_model_tool_loop + ghi transcript
│   ├── sources.py             # chuẩn hoá URL, phân làn tin/paper/repo, tính candidates ∪ read
│   ├── components.py          # chip trạng thái, bảng trace, badge version
│   └── evidence.py            # đọc runs/, version_log.csv, transcripts/
└── artifacts/
    └── versions/
        ├── v0/{system_prompt.md, tools.yaml}
        ├── v1/{system_prompt.md, tools.yaml}
        ├── v2/{system_prompt.md, tools.yaml}
        └── v3/{system_prompt.md, tools.yaml}
```

`app.py` không được chứa business logic dài; nó ráp các module trong `ui/`.

`ui/sources.py` tách riêng vì nó là phần **duy nhất** có logic đủ rắc rối để sai âm thầm: chuẩn hoá URL, rút arXiv ID, phân làn, đối chiếu `candidates`/`read`. Tách ra thì test tay được bằng vài URL mẫu mà không cần chạy cả app — và cả mục 2.D lẫn chỉ số ở Tab 2 đều gọi vào đúng một chỗ, không dựng hai cách tính lệch nhau.

Thư mục `artifacts/versions/` là **hợp đồng với người làm prompt**: mỗi lần bump version, họ copy cặp file hiện hành vào đó. UI chỉ đọc, không tự ghi. Nếu thư mục trống, UI vẫn phải chạy được ở chế độ `live`.

## 6. Hành vi kỹ thuật bắt buộc

- Provider khởi tạo qua `make_provider(...)` và cache bằng `st.cache_resource` theo `(provider_name, model)`.
- `load_tool_declarations` + `to_openai_tools` gọi lại mỗi lần đổi version; **không** cache theo đường dẫn mà không tính hash file.
- `messages` dựng đúng như `chat.py`: `[{"role":"system", ...}, *trim_history(history, history_window), {"role":"user", ...}]`. Import `trim_history` từ `chat.py`, không copy lại.
- Gọi model là blocking; **không** dùng thread hay asyncio. Tiến trình hiện bằng `st.status` cập nhật từ `on_event` (mục 0, ràng buộc 1) — vẫn chạy trên đúng một luồng, chỉ là vẽ ra màn hình khi từng bước xong. Không có `on_event` thì `st.spinner` là mức tối thiểu.
- Transcript ghi lại **sau mỗi lượt**, không đợi đóng app — mất điện giữa demo vẫn còn bằng chứng.
- `run_model_tool_loop` có `print()` ra stdout; kệ nó, không sửa.
- App phải chạy được ngay cả khi chưa có key: hiện banner "Chưa cấu hình provider key" thay vì crash lúc import.

## 7. Tiêu chí nghiệm thu

UI được coi là PASS khi tất cả các mục sau đúng:

1. `streamlit run app.py` mở được `http://localhost:8501`, không lỗi đỏ trên màn hình.
2. Gõ kịch bản 1 (tin + paper + repo) → nhận brief markdown render đúng, bảng **Nguồn đã dùng** có ít nhất 5 hàng phủ **cả ba làn** 📰/📄/💻, ít nhất 1 hàng gắn ✅ Đã đọc nguồn, và trace hiện đủ chuỗi `lookup` + `papers` → `fetch` / `paper_text` → `format` với `args` đọc được.
   2b. Mọi link trong brief đều truy được về một `tool_events` — không có banner đỏ "link không đến từ kết quả tool nào". Nếu có, đó là phát hiện cần ghi vào `REPORT.md`, không phải bug của UI.
   2c. Gõ kịch bản 2 (paper) → có ít nhất một lần `paper_text`, và hàng arXiv tương ứng gắn ✅ chứ không phải ⚠. Đây là phép thử trực tiếp cho phần chuẩn hoá arXiv ID ở mục 2.D — sai chỗ đó thì mọi paper đã đọc đều bị gắn nhầm ⚠.
   2d. Gõ kịch bản 3 (repo) → trace hiện `lookup` với `query` nhìn thấy được là có nhắm GitHub, và bảng nguồn có ít nhất 2 hàng 💻 Repo.
3. Gõ một câu hỏi thiếu thông tin → `status = waiting_for_user`, banner amber hiện, trả lời tiếp ở lượt sau thì agent dùng được thông tin vừa bổ sung.
4. Một câu hỏi có hành động nhạy cảm → thấy agent hỏi xác nhận trước khi gọi tool gửi.
5. Sau 3 lượt, `transcripts/*.transcript.json` tồn tại, mở bằng `json.load` không lỗi, có đủ 3 phần tử trong `turns`.
6. Tab So sánh version chạy cùng một scenario ở hai version và hiện diff tool routing.
7. Badge `artifact_version` trên UI khớp chính xác chuỗi trong file transcript vừa ghi.
8. Bật `cloudflared tunnel --url http://localhost:8501`, mở link trên thiết bị khác: vào được, ở chế độ Demo, và không nhìn thấy bất cứ thứ gì trong danh mục cấm ở mục 2.

## 8. Ngoài phạm vi

Không làm trong lượt này: đăng nhập nhiều tài khoản, database, đa ngôn ngữ, dark/light toggle (chỉ làm dark theo palette trên), streaming token, biểu đồ metric ngoài những bảng đã nêu, hay bất kỳ thay đổi nào trong `tools/`, `providers/`, `run_eval.py`.

Nói riêng cho làn repo, ba thứ **cố ý không làm**:

- **Không viết tool `github` mới.** Thêm tool là đổi `tools.yaml` + `TOOL_FUNCTIONS` + hai file eval, tức là đổi bài toán đang được chấm chứ không phải làm UI. Làn repo đi bằng `lookup` + `fetch` như mục 0 đã chốt.
- **Không gọi thẳng GitHub API từ UI.** UI chỉ được đọc `tool_events`; tự đi lấy số sao là dựng một nguồn dữ liệu thứ hai mà transcript không ghi lại — bằng chứng và màn hình sẽ nói hai chuyện khác nhau.
- **Không parse số sao, ngôn ngữ, ngày commit thành trường có cấu trúc** để sắp xếp hay lọc. Kết quả `lookup`/`fetch` là text tự do, parse ra là đoán; đoán sai trên đúng cái màn hình dựng ra để chống đoán thì hỏng cả luận điểm.
