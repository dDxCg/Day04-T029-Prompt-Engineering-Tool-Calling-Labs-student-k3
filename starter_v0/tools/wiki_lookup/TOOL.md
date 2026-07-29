---
name: wiki_lookup
track: team_new
kind: live_api
provider: Wikipedia (no key required)
requires_env: []
inputs: [query, lang]
outputs: [items]
side_effect: false
---
# wiki_lookup

Trả về đoạn tóm tắt (summary) từ Wikipedia cho một chủ đề/thực thể cụ thể
(người, tổ chức, khái niệm, sự kiện lịch sử). Dùng khi người dùng cần một lời
giải thích/định nghĩa/tiểu sử nền tảng, KHÔNG cần tin tức mới nhất — khác với
`lookup` (tìm kiếm web/tin tức thời sự qua Tavily) và khác với `fetch` (đọc
một URL cụ thể đã biết trước).

Không cần API key. Gọi trực tiếp Wikipedia search API rồi REST summary API.
