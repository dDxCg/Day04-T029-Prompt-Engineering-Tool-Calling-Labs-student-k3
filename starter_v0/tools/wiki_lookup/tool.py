from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err


USER_AGENT = "AI20k-Day04-Research-Agent/1.0 (educational lab)"


def wiki_lookup(query: str = "", lang: str = "en") -> dict[str, Any]:
    try:
        if not query:
            raise ValueError("query is required")
        search_response = requests.get(
            f"https://{lang}.wikipedia.org/w/api.php",
            params={"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        search_response.raise_for_status()
        hits = search_response.json().get("query", {}).get("search", [])
        if not hits:
            return {"tool": "wiki_lookup", "query": query, "lang": lang, "items": []}

        title = hits[0]["title"]
        summary_response = requests.get(
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        summary_response.raise_for_status()
        data = summary_response.json()
        items = [{
            "title": data.get("title"),
            "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
            "source": "wikipedia.org",
            "summary": data.get("extract"),
        }]
        return {"tool": "wiki_lookup", "query": query, "lang": lang, "items": items}
    except Exception as exc:
        return err("wiki_lookup", exc)
