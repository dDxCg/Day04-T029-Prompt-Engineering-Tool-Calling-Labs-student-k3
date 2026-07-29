# UI Spec — Research Agent Tool Eval (Day04)

Spec bàn giao để code `starter_v0/app.py`. Viết cho người sẽ code lại từ đây, không cần hỏi thêm.

---

## Bối cảnh

**Giả định** (suy ra từ `README.md`, sửa lại nếu team quyết khác):

- **Ai dùng:** ba nhóm, xếp theo mức độ ưu tiên khi có xung đột thiết kế.
  1. **Người test lạ trong buổi showdown** — team khác hoặc giảng viên, mở link `trycloudflare.com` trên máy mình, không đọc hướng dẫn, có ~3 phút, và họ tới để *thử đánh gãy agent*.
  2. **Team đang demo** — cần chiếu lên máy chiếu và chỉ vào bằng chứng cụ thể.
  3. **Team đang debug routing** — cần xem args thật, tool result thật, hash artifact.
- **Trạng thái khi tới:** vội và hoài nghi. Họ không tin agent chọn đúng tool cho tới khi nhìn thấy args.
- **Một việc phải trơn:** gõ (hoặc bấm) **một** câu → thấy ngay agent gọi tool nào, args gì, kết quả gì, ở version nào — **không phải mở file JSON**.
- **Vào từ đâu:** URL public (Cloudflare tunnel) hoặc `streamlit run app.py`. **Đi ra đâu:** tải transcript JSON, hoặc mở tab so sánh version.

**Định vị sản phẩm — quyết định quan trọng nhất của bản thiết kế này:**

> Đây **không phải chatbot**. Đây là **trình xem bằng chứng có kèm ô chat**. Chat chỉ là cách sinh ra bằng chứng.

Hệ quả: trace tool không phải tính năng phụ giấu trong expander cuối trang — nó là nội dung chính, ngang hàng với câu trả lời. Một chatbot đẹp mà không nhìn được `args` thì trượt yêu cầu "bằng chứng tối thiểu trên UI" của lab.

---

## User flow

### Luồng chính (single-turn)

```
Mở app
  → thấy version đang chạy + 4 câu gợi ý bấm được
  → bấm 1 câu (hoặc tự gõ)
  → step list chạy dần: gọi model → chạy tool 1 → chạy tool 2 → tổng hợp
  → câu trả lời + khối Trace (thu gọn 1 dòng, bấm mở ra)
  → hành động: 👍/👎 · Chạy lại · So với v0 · Tải transcript
```

### Nhánh phải thiết kế (không phải "nice to have")

| Nhánh                                       | Xảy ra khi                                                    | UI làm gì                                                                                                                                                                                                                                                                               |
| -------------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Agent hỏi lại**                    | `status == "waiting_for_user"` (tool trả `awaiting_user`) | Hiện câu hỏi như bong bóng agent + badge`⏸ Đang chờ bạn trả lời`. Ô nhập đổi placeholder thành "Trả lời câu hỏi trên…". Nếu `response_type=yes_no` → hiện luôn 2 nút **Có** / **Không**; nếu `choice` → hiện các nút từ `options`. |
| **Hành động nhạy cảm** (`send`) | Model gọi`send`                                             | **Chặn trước khi chạy.** Hiện thẻ xác nhận với nội dung sẽ gửi nguyên văn + đích đến. Chỉ chạy tool khi người dùng bấm nút. Xem [Thẻ xác nhận](#4-thẻ-xác-nhận-hành-động-nhạy-cảm).                                                              |
| **Tool lỗi**                          | `result` có key `error`                                   | Bước đó đánh dấu`✗`, mở sẵn (không thu gọn), hiện `error` + `message` bằng ngôn ngữ người dùng. Loop vẫn chạy tiếp — nói rõ "agent vẫn tiếp tục với các kết quả còn lại".                                                                         |
| **Provider lỗi**                      | exception khi gọi API                                         | Không đổ stack trace. Xem[Trạng thái lỗi](#trạng-thái-lỗi).                                                                                                                                                                                                                       |
| **Hết vòng**                         | `status == "max_tool_rounds"`                                | Badge`⚠ Dừng sau 4 vòng tool` + gợi ý tăng `Max rounds` ở sidebar hoặc hỏi lại cụ thể hơn.                                                                                                                                                                               |
| **Thiếu API key**                     | preflight fail lúc khởi động                               | Chặn ngay màn hình đầu, không để người dùng gõ rồi mới báo lỗi.                                                                                                                                                                                                           |
| **Ngoài phạm vi**                    | người dùng hỏi chuyện không liên quan                   | Agent trả lời không dùng tool → Trace hiện`Không gọi tool nào` (đây là kết quả **đúng**, không phải lỗi — phải nói rõ, vì `unnecessary_tool` là một `failure_type` trong eval).                                                                     |

Bước bị loại bỏ có chủ đích: **không có màn hình đăng nhập, không có bước chọn cấu hình trước khi chat**. Người test lạ phải gõ được câu đầu tiên trong vòng 10 giây kể từ lúc mở link. Mọi cấu hình nằm ở sidebar với default chạy được ngay.

---

## Ba phương án bố cục

**A. Một trang, trace inline dưới mỗi câu trả lời.**
Đơn giản nhất, hợp quy ước chat. Đổi lại: không so sánh được version cạnh nhau — mà lab yêu cầu "cùng một scenario chạy qua nhiều version để thấy cải thiện".

**B. Hai cột: chat trái, pane trace cố định bên phải.**
Trace luôn nhìn thấy, hợp người debug. Đổi lại: Streamlit không có sticky pane thật, cột phải sẽ trôi theo trang; trên máy chiếu 2 cột làm chữ nhỏ đi một nửa.

**C. Tabs: 💬 Chat · ⚖️ So sánh version · 📊 Eval runs. Trace inline trong tab Chat.** ← **chọn phương án này**

Vì: tab Chat giữ nguyên ưu điểm của A (một luồng đọc, chữ to, chiếu được); tab So sánh giải đúng yêu cầu bắt buộc của lab mà A không giải được; tab Eval biến `runs/*.json` thành thứ chiếu được thay vì phải mở terminal. Ba tab cũng khớp đúng ba nhóm người dùng ở trên — và tab đầu tiên phục vụ nhóm ưu tiên số 1.

---

## Khung màn hình

### Tab 1 — 💬 Chat (mặc định)

Trạng thái rỗng (lần đầu mở):

```text
┌─ SIDEBAR ────────┬──────────────────────────────────────────────────────┐
│                  │  Research Agent          v3+p1a2b3c4 · openrouter    │
│ ⚙ Cấu hình       │ ─────────────────────────────────────────────────────│
│                  │                                                      │
│ Version          │   Agent tra cứu và tổng hợp tin tức AI.              │
│ ( ) v0  (•) v3   │   Nó tự chọn tool, chạy thật, rồi hiện lại            │
│                  │   toàn bộ trace để bạn kiểm.                         │
│ Provider         │                                                      │
│ [ openrouter  ▾] │   Gợi ý:                                       │
│                  │   ┌───────────────────────────────────────────┐      │
│ Model            │   │ Tổng hợp tin AI tuần này                  │      │
│ [ auto        ▾] │   ├───────────────────────────────────────────┤      │
│                  │   │ 5 bài mới nhất của @OpenAI                │      │
│ Max tool rounds  │   ├───────────────────────────────────────────┤      │
│ [────●───]  4    │   │ Gửi digest tuần này lên Telegram          │      │
│                  │   ├───────────────────────────────────────────┤      │
│ History window   │   │ Chính sách trích nguồn nội bộ nói gì?     │      │
│ [──●─────]  5    │   └───────────────────────────────────────────┘      │
│                  │                                                      │
│ ─────────────    │   Không trả lời được: câu hỏi này ngoài phạm vi           │
│ 📄 Transcript    │   research, và dữ liệu realtime nằm ngoài            │
│ v3_openrouter_   │   6 tool đang có.                                    │
│ 20260729T104233  │                                                      │
│ 0 lượt           │                                                      │
│ [⬇ Tải JSON]     │  ┌────────────────────────────────────────┐ ┌──────┐│
│ [🗑 Hội thoại mới]│  │ Nhập câu hỏi…                          │ │ Gửi  ││
│                  │  └────────────────────────────────────────┘ └──────┘│
└──────────────────┴──────────────────────────────────────────────────────┘
```

Sau một lượt (trace thu gọn — mặc định):

```text
│  ┌──────────────────────────────────────────────────────────┐
│  │ 👤  Tổng hợp tin AI tuần này                             │
│  └──────────────────────────────────────────────────────────┘
│
│  ▸ Trace · 2 vòng · 3 tool · 4,1s                  ✓ đã xong
│
│  🤖  **Tin AI tuần này**
│      1. OpenAI công bố… [1]
│      2. Google DeepMind… [2]
│      …
│      ─────────────────────────────────────────────
│      👍  👎   ⟳ Chạy lại   📋 Copy   ⚖ So với v0
```

Trace mở ra:

```text
│  ▾ Trace · 2 vòng · 3 tool · 4,1s                  ✓ đã xong
│  ┌─ Vòng 1 ────────────────────────────────────────────────┐
│  │ ✓ lookup                                          1,4s  │
│  │     query        "tin tức AI tuần này"                  │
│  │     topic        news                                   │
│  │     timeframe    week                                   │
│  │     max_results  5                                      │
│  │     → 5 kết quả  ▸ xem JSON                             │
│  │                                                          │
│  │ ✓ social_search                                   1,2s  │
│  │     query        "AI news"                              │
│  │     search_type  Latest                                 │
│  │     → 5 bài  ▸ xem JSON                                 │
│  ├─ Vòng 2 ────────────────────────────────────────────────┤
│  │ ✓ format                                          0,1s  │
│  │     template     sections                               │
│  │     headline     "Tin AI tuần này"                      │
│  │     items        [8 mục]  ▸ xem JSON                    │
│  └──────────────────────────────────────────────────────────┘
│    artifact_version  v3+p1a2b3c4d5e6+t9f8e7d6c5b4
│    prompt_hash 1a2b3c4d5e6f…   tools_hash 9f8e7d6c5b4a…
```

**Quy tắc trình bày args** — đây là chỗ dễ làm ẩu nhất:

- Args hiện dạng **bảng key–value từng dòng**, không phải một dòng JSON dài. Người chấm cần đọc lướt thấy `topic=news` chứ không muốn parse `{"query":"…","topic":"news",…}` bằng mắt.
- Giá trị string dài > 80 ký tự: cắt còn 80 + `…`, bấm để mở đầy đủ.
- Array/object lồng nhau: hiện `[8 mục]` / `{4 khoá}` + link `▸ xem JSON`.
- **Tool result không bao giờ đổ nguyên ra dòng chảy chính.** Hiện một dòng tóm tắt (`→ 5 kết quả`), JSON đầy đủ nằm sau một cú bấm nữa. Một `paper_text` trả 8.000 ký tự sẽ phá vỡ toàn bộ bố cục nếu đổ thẳng.

### Tab 2 — ⚖️ So sánh version

```text
│ Scenario  [ Tổng hợp tin AI tuần này            ▾]
│ Nguồn     (•) Transcript đã lưu   ( ) Chạy lại trực tiếp (tốn quota)
│
│ ┌── v0+p3f2a9c1 ──────────────┬── v3+p1a2b3c4 ──────────────┐
│ │ ✗ Sai tool                  │ ✓ Đúng tool                 │
│ │                             │                             │
│ │ ✓ social_search      1,1s   │ ✓ lookup             1,4s   │
│ │   query  "tin AI"           │   query  "tin tức AI tuần"  │
│ │   search_type  Latest       │   topic  news               │
│ │                             │   timeframe  week           │
│ │                             │                             │
│ │ — không gọi format          │ ✓ format             0,1s   │
│ │                             │   template  sections        │
│ ├─────────────────────────────┼─────────────────────────────┤
│ │ Câu trả lời  ▸ mở           │ Câu trả lời  ▸ mở           │
│ └─────────────────────────────┴─────────────────────────────┘
│
│ 💡 Thay đổi giữa hai version: v1 thêm luật "yêu cầu tin tức →
│    lookup(topic=news, timeframe=week)" vào system_prompt.md.
│    Nguồn: artifacts/version_log.csv
```

**Quyết định thiết kế:** mặc định là **replay từ transcript đã lưu**, không phải chạy lại live. Lý do: mạng hội trường và quota API là hai thứ hay chết nhất lúc demo, và so sánh version là phần *chắc chắn* phải chiếu được. Chạy live vẫn có, nhưng là lựa chọn thứ hai và ghi rõ "tốn quota".

Trên màn hình < 900px, hai cột xếp chồng dọc: v0 trước, v3 sau, mỗi khối có nhãn version rõ ràng.

### Tab 3 — 📊 Eval runs

```text
│ Thư mục runs/  ·  7 file  ·  mới nhất 29/07 10:42
│
│ version  suite   case_acc  routing  args   multiturn  lỗi provider
│ v0       base      0,45     0,55    0,62     0,30      0
│ v1       base      0,64     0,73    0,70     0,50      0
│ v2       base      0,73  ⚠  0,82    0,75     0,60      2  ← xem chú thích
│ v3       base      0,91     0,95    0,88     0,80      0
│ v3       group     0,80     0,90    0,85     0,80      0
│
│ ⚠ v2/base có 2 provider_error_cases → 4 metric của dòng này chưa
│   dùng được để report. Chạy lại rồi mới trích vào REPORT.md.
│
│ Lỗi thường gặp nhất (v3/base):  wrong_arg_value 2 · missing_tool_call 1
│ [ Chọn một case fail để xem trace ▾ ]
```

Cột `lỗi provider` và dòng cảnh báo là bắt buộc, không phải trang trí: `README.md` quy định metric chỉ có giá trị khi `provider_error_cases == 0` và `measured_cases == total_cases`. Cho UI hiện số 0,73 mà không kèm cảnh báo là mời người ta chép nhầm vào report.

---

## Thành phần

### 1. Thanh header version

- **Vai trò:** trả lời câu "tôi đang nhìn version nào" mà không cần cuộn. Đây là câu hỏi đầu tiên của bất kỳ ai chấm bài này.
- **Dữ liệu:** `artifact_version` (string, bắt buộc), `provider` (string), `model` (string).
- Hiện rút gọn `v3+p1a2b3c4`; hover/bấm hiện đủ `artifact_version`, `prompt_hash`, `tools_hash`.
- **Đổi version ở sidebar → phải đổi header ngay** và hiện toast `Đã chuyển sang v0. Hội thoại hiện tại giữ nguyên; lượt tiếp theo chạy bằng v0.` Trộn lẫn hai version trong một transcript mà không báo là cách chắc chắn tạo ra kết luận sai.

### 2. Câu gợi ý (chip)

- **Vai trò:** giải bài toán ô chat trống, đồng thời dạy ngầm phạm vi agent.
- 4 chip, mỗi chip là câu **thật sự chạy tốt**, và cả 4 phủ 4 loại hành vi khác nhau: research thường · lấy timeline · **hành động nhạy cảm** (để người test tự phát hiện boundary xác nhận) · tra policy nội bộ.
- Bấm chip = gửi luôn, không phải điền vào ô nhập rồi bắt bấm Gửi lần nữa.
- Ẩn toàn bộ khối chip sau lượt đầu tiên.

### 3. Khối Trace

| Trạng thái               | Thể hiện                                                                                                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Rỗng**            | Không render gì. Lượt chưa chạy thì không có trace.                                                                                                                    |
| **Đang chạy**      | `st.status` mở sẵn, các bước hiện dần: `⟳ Đang gọi model…` → `⟳ lookup(topic=news)…` → `✓ lookup · 1,4s`. Đây là phần chống "hộp đen 15 giây". |
| **Có dữ liệu**    | Thu gọn về một dòng:`▸ Trace · 2 vòng · 3 tool · 4,1s ✓`. Bấm mở chi tiết.                                                                                       |
| **Có tool lỗi**    | Thu gọn thành`▸ Trace · 2 vòng · 3 tool · 1 lỗi ⚠` và **mở sẵn** ở bước lỗi.                                                                            |
| **Không gọi tool** | `▸ Trace · Không gọi tool nào · trả lời trực tiếp ✓` — nói rõ đây có thể là hành vi đúng.                                                               |
| **Provider lỗi**    | Trace hiện các bước đã chạy được rồi dừng ở`✗ Gọi model thất bại`.                                                                                           |

- **Bàn phím:** header trace là `<button>`/`<summary>` thật — Tab tới được, Enter/Space mở.
- Ký hiệu trạng thái luôn là **icon + chữ**, không bao giờ chỉ dựa vào màu.

### 4. Thẻ xác nhận hành động nhạy cảm

Đây là lớp chặn cuối, không phải UX cho đẹp. Áp dụng cho `send` (và mọi action tool team viết thêm).

```text
│ ┌──────────────────────────────────────────────────────┐
│ │ ⏸  Agent muốn gửi tin nhắn ra ngoài                  │
│ │                                                       │
│ │ Tool   send                                          │
│ │ Đích   Telegram channel @ai_daily_vn                 │
│ │ Nội dung sẽ được gửi:                                │
│ │ ┌───────────────────────────────────────────────┐    │
│ │ │ **Tin AI tuần này**                           │    │
│ │ │ 1. OpenAI công bố…                            │    │
│ │ │ 2. Google DeepMind…                           │    │
│ │ └───────────────────────────────────────────────┘    │
│ │                                                       │
│ │ [ Gửi lên Telegram ]        [ Không gửi ]            │
│ └──────────────────────────────────────────────────────┘
```

- Nút mô tả **hậu quả**, không phải "OK"/"Huỷ".
- Nội dung hiện **nguyên văn** thứ sắp gửi — không tóm tắt. Người dùng phải kiểm được đúng cái sẽ ra ngoài.
- Nút chính không được là nút mặc định của Enter. Người ta đang gõ chat, Enter là phản xạ.
- Bấm **Không gửi** → tool không chạy, trace ghi `⏭ send · người dùng từ chối`, agent nhận kết quả này và đi tiếp.

### 5. Ô nhập

- Enter gửi, Shift+Enter xuống dòng. Không đổi quy ước này.
- Nút Gửi luôn hiện, mờ đi khi ô rỗng (không ẩn hẳn).
- Khi đang chạy: ô nhập khoá, nút Gửi đổi thành **Dừng**.
- Khi `status == waiting_for_user`: placeholder đổi thành `Trả lời câu hỏi của agent…`, và nếu là `yes_no`/`choice` thì hiện thêm nút bấm nhanh.

### Trạng thái lỗi

Viết bằng ngôn ngữ người dùng, luôn đủ ba phần: **chuyện gì · ở đâu · giờ làm gì**.

| Tình huống                  | Thông báo                                                                                                                                                                 |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Thiếu API key                | `Chưa có API key cho openrouter. Mở starter_v0/.env và điền OPENROUTER_API_KEY, rồi tải lại trang.`                                                              |
| Provider timeout / mất mạng | `Không gọi được openrouter (hết thời gian chờ). Kiểm tra mạng rồi bấm Chạy lại. Hội thoại và transcript vẫn được giữ.` + nút **Chạy lại**. |
| Hết quota                    | `Tài khoản openrouter đã hết quota. Đổi provider ở sidebar, hoặc mở tab So sánh version để xem lại các lượt đã chạy.`                                 |
| Tool lỗi mạng               | `Tool lookup không lấy được kết quả (lỗi mạng). Agent vẫn tiếp tục với các tool còn lại.`                                                                 |
| Hết vòng tool               | `Agent dừng sau 4 vòng tool mà chưa chốt được câu trả lời. Thử hỏi cụ thể hơn, hoặc tăng Max tool rounds ở sidebar.`                                   |
| Thiếu Telegram credentials   | `Chưa cấu hình Telegram nên không gửi thật được. Bước xác nhận vẫn chạy để bạn kiểm boundary.`                                                        |

Không bao giờ hiện `Error 502`, `KeyError`, hay stack trace trong dòng chảy chính. Chi tiết kỹ thuật để trong expander `▸ Chi tiết kỹ thuật` cho người debug.

---

## Token

Streamlit không cho tuỳ biến sâu. Chốt token ở `.streamlit/config.toml` + **một** khối CSS nhỏ, đừng dựng design system mới lên trên.

```toml
# starter_v0/.streamlit/config.toml
[theme]
base = "light"
primaryColor = "#2563EB"          # Xanh nhấn — CHỈ dùng cho hành động chính
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F4F6F8"   # nền sidebar, nền khối trace
textColor = "#111827"
font = "sans serif"
```

| Vai trò     | Hex         | Dùng ở đâu                    | Tương phản trên nền   |
| ------------ | ----------- | --------------------------------- | -------------------------- |
| Chữ chính  | `#111827` | nội dung, tiêu đề             | 16,1:1 trên`#FFFFFF` ✓ |
| Chữ phụ    | `#4B5563` | tên args, thời gian bước      | 7,6:1 ✓                   |
| Viền        | `#E5E7EB` | khung trace, đường chia        | —                         |
| Nhấn        | `#2563EB` | nút Gửi, tab đang chọn        | 5,2:1 ✓                   |
| Thành công | `#15803D` | `✓` bước xong                | 5,0:1 ✓                   |
| Cảnh báo   | `#B45309` | `⚠` hết vòng, provider_error | 4,8:1 ✓                   |
| Lỗi         | `#B91C1C` | `✗` tool lỗi, case fail       | 6,5:1 ✓                   |

Không dùng `#9CA3AF` cho chữ trên nền trắng (2,5:1 — trượt). Đây là màu xám mặc định hay bị dùng cho caption.

- **Chữ:** font hệ thống. Thang `13 · 15 · 17 · 20 · 26`. **Chữ nội dung 17px, không phải 16px** — bản này sẽ được chiếu lên máy chiếu và hàng ghế cuối phải đọc được. Args và metadata trong trace dùng mono 15px.
- **Khoảng cách:** `4 · 8 · 12 · 16 · 24 · 32`. Không có số lẻ ngoài thang.
- **Bo góc:** 6px (chip, nút) · 12px (thẻ trace, thẻ xác nhận). **Đổ bóng:** chỉ dùng `0 1px 2px rgba(0,0,0,.06)` cho thẻ xác nhận; các khối khác dùng viền.

**Dark mode:** Streamlit tự đảo theo hệ thống. Nếu team đặt `base = "dark"`, dùng nền `#1A1A1A` (không dùng đen tuyệt đối) và giảm bão hoà màu nhấn xuống `#60A5FA`. Kiểm lại toàn bộ 7 màu trên nền tối trước khi chốt — bảng tương phản ở trên chỉ tính cho nền sáng.

---

## Responsive

| Khoảng     | Xử lý                                                                                                                                             |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| < 640px     | Một cột. Sidebar thu vào nút hamburger (mặc định của Streamlit). Tab So sánh: hai version xếp chồng dọc. Bảng eval → danh sách thẻ. |
| 640–1024px | Sidebar hiện được. So sánh version vẫn xếp dọc (hai cột ở đây làm args bị xuống dòng nát).                                         |
| > 1024px    | Bố cục đầy đủ. Giới hạn bề rộng vùng chat ~800px — màn 27" không có nghĩa là dòng chữ dài hết màn.                            |

Bảng eval và khối JSON cuộn ngang **trong hộp riêng**. Trang không bao giờ cuộn ngang.

---

## Tiếp cận

- [X] Tương phản ≥ 4.5:1 — đã kiểm cả 7 màu ở bảng trên.
- [X] Vùng bấm ≥ 44×44px — chip gợi ý và nút xác nhận có padding dọc ≥ 12px.
- [X] Không dùng riêng màu để truyền thông tin — mọi trạng thái đều là **icon + chữ** (`✓ đã xong`, `✗ lỗi`, `⚠ hết vòng`), đọc được trên ảnh in đen trắng và với người mù màu.
- [X] Bàn phím — Tab theo thứ tự đọc; Enter gửi; Space/Enter mở trace; Esc đóng thẻ xác nhận (= "Không gửi").
- [X] Nút chỉ có icon (👍/👎/📋/⟳) phải có `aria-label` hoặc `help=` của Streamlit.
- [X] Đọc được ở mức phóng to 200%.

---

## Ghi chú kỹ thuật cho người code

Ba điểm dưới đây ảnh hưởng trực tiếp tới UX, phát hiện lúc đọc code hiện có:

1. **Không stream token được.** `Provider.complete()` ở [providers/base.py:21](starter_v0/providers/base.py#L21) trả về nguyên câu trả lời một lần, không có API stream. Vì vậy thiết kế này **stream các bước, không stream chữ** — step list chạy dần chính là thứ thay thế hiệu ứng gõ chữ. Đừng giả lập hiệu ứng gõ chữ trên text đã có đủ: nó làm người dùng chờ lâu hơn mà không thêm thông tin nào.
2. **`run_model_tool_loop` chỉ trả kết quả khi đã xong cả loop** ([chat.py:80](starter_v0/chat.py#L80)). Muốn step list chạy dần thì cần thêm **một tham số optional** `on_event: Callable | None = None` và gọi nó ở ba chỗ: trước khi gọi provider, sau khi có `tool_calls`, sau mỗi `execute_tool_call`. Optional nên `chat.py` và `run_eval.py` không đổi hành vi. **Không viết agent loop thứ hai trong `app.py`** — README yêu cầu tái sử dụng hàm này, và hai loop sẽ trôi lệch nhau ngay vòng tối ưu đầu tiên.
3. **Boundary xác nhận cần chặn *trước* khi tool chạy.** Hiện tại `execute_tool_call` chạy thẳng. Cách gọn nhất là dùng chính `on_event` ở trên: trả về `False` từ callback để bỏ qua call đó, rồi đưa `{"error": "user_declined"}` vào tool result. Đừng dựa vào việc model tự truyền `confirmed=true` — model là thứ đang được kiểm, không phải thứ để tin.

Ngoài ra: mọi state (`messages`, `transcript`, `version`, `pending_confirmation`) phải nằm trong `st.session_state`, và transcript ghi ra file **sau mỗi lượt** — không đợi lúc đóng app.

---

## Ngoài phạm vi (cố ý không làm)

- **Đăng nhập / phân quyền.** Link tunnel là tạm thời, dùng trong buổi demo. Đổi lại: **không hiện API key, `.env`, hay bất kỳ secret nào trên UI**, kể cả trong expander "chi tiết kỹ thuật".
- **Sửa lại câu hỏi cũ và chạy lại từ đó.** Có ích, nhưng "Chạy lại" đã phủ 90% nhu cầu với 10% công sức.
- **Chỉ số `[1]` bấm ra popover có trích đoạn nguyên văn.** Đúng chuẩn cho RAG, nhưng `format` hiện trả markdown phẳng nên phải đổi tool. Bản này chỉ hiện link nguồn trong câu trả lời; nguồn thật để kiểm nằm ở tool result trong trace.
- **Lưu lịch sử nhiều phiên.** Một phiên = một transcript, tải về được. Ai cần lịch sử thì mở thư mục `transcripts/`.
- **Mobile-first.** Có chạy được trên điện thoại, nhưng đối tượng chính ngồi trước máy chiếu và laptop.

```

```
