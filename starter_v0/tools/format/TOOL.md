---
name: format
track: core
kind: local_formatter
requires_env: []
inputs: [items, template, headline]
outputs: [markdown, item_count]
side_effect: false
---
# format

Formats already-collected items (from `lookup`, `timeline`, `social_search`,
`fetch`, `wiki_lookup`, ...) into a markdown digest. It does not fetch or
search for data itself — always call a research tool first, then pass its
`items` into `format`.

## `items` (array of objects)

Each item may include:

- `title`: item title/headline.
- `url`: source link.
- `source`: display name for the source; falls back to the domain of `url`.
- `summary`: body text used for the bullet line (falls back to `title`), truncated to 280 chars.
- `section`: group label used by the `sections` and `daily_ai_vn` templates (defaults to "Tổng hợp" / "Tin chính").

## `template` (enum)

- `brief`: first 5 items as flat bullets, with an optional bold `headline`.
- `bullets`: all items as flat bullets, no grouping or heading.
- `sections` (default): items grouped under `## <section>` headings, with an optional `# <headline>` title.
- `thread`: numbered `1/ 2/ 3/ ...` bullets, e.g. for a tweet-thread style output.
- `daily_ai_vn`: items grouped under bold `**<section>**` headings under a bold headline (defaults to "Tin tức hôm nay").

## `headline` (string, optional)

Title shown above the digest; behavior depends on `template` (see above).
