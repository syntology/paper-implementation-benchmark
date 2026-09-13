#!/usr/bin/env python3
"""
The search-engine arm's toolkit for the graph-vs-search benchmark (see
PREREGISTRATION.md): Semantic Scholar paper search, arXiv search/abstract,
GitHub code search + file fetch, and a generic page fetcher. This is the
domain-realistic version of "a bot with a search engine" for ML
implementation work -- the same sources a Claude-with-web-search agent
lands on for these tasks, minus a browser.

No secrets ever enter tool RESULTS (keys ride only in request headers),
so transcripts are safe to commit.
"""
import base64
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

REPO = Path(os.environ.get("BENCH_REPO_ROOT",
                           Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent / "vendor"))

import api_gateway  # noqa: E402  (the ONE way out to any external service)
import arxiv_client  # noqa: E402  (arXiv's vocabulary over that gateway)

FETCH_CAP = 18000          # chars of extracted text per fetch
TIMEOUT = 25


def _http_json(url, headers=None, timeout=TIMEOUT):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


class _TextExtract(HTMLParser):
    _SKIP = {"script", "style", "noscript", "svg", "head"}

    def __init__(self):
        super().__init__()
        self.chunks, self._skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip and data.strip():
            self.chunks.append(data.strip())


def search_semantic_scholar(query: str, limit: int = 8) -> dict:
    """Paper search over Semantic Scholar."""
    limit = max(1, min(int(limit), 20))
    # Through api_gateway (2026-09-10), which holds S2's clock, its key and
    # the retries. A benchmark arm is the LAST caller that should be trusted
    # with its own throttle: this one had a private 2s ladder and read the key
    # itself, so a search-arm run competed with the ingest lane for the same
    # quota without either knowing about the other.
    try:
        r = api_gateway.s2_get("/paper/search",
                               {"query": query, "limit": limit,
                                "fields": "title,abstract,year,externalIds,citationCount"},
                               timeout=TIMEOUT, max_attempts=3)
        data = r.json() if r.status_code == 200 else {}
    except api_gateway.Unanswered as e:
        return {"error": f"semantic scholar search unanswered: {e}"}
    except Exception as e:
        return {"error": f"semantic scholar search failed: {e}"}
    out = []
    for p in data.get("data", []) or []:
        ext = p.get("externalIds") or {}
        out.append({"title": p.get("title"), "year": p.get("year"),
                    "arxiv_id": ext.get("ArXiv"),
                    "citations": p.get("citationCount"),
                    "abstract": (p.get("abstract") or "")[:600]})
    return {"query": query, "results": out}


def search_arxiv(query: str, limit: int = 8) -> dict:
    """arXiv keyword search (titles + summaries).

    Through arxiv_client like every other arXiv call in the project: this is
    an agent-driven tool, so its request rate is set by whatever the model
    under test decides to do, and a benchmark arm is exactly the caller that
    should not be trusted with its own throttle. It used to carry the UA
    "syntology-benchmark" and no pacing at all."""
    limit = max(1, min(int(limit), 20))
    try:
        r = arxiv_client.get({"search_query": f"all:{query}", "max_results": limit},
                             timeout=TIMEOUT)
        if r.status_code != 200:
            return {"error": f"arxiv search failed: HTTP {r.status_code}"}
        xml = r.text
    except Exception as e:
        return {"error": f"arxiv search failed: {type(e).__name__}: {e}"}
    entries = []
    for m in re.finditer(r"<entry>(.*?)</entry>", xml, re.S):
        e = m.group(1)
        def _tag(t):
            mm = re.search(rf"<{t}[^>]*>(.*?)</{t}>", e, re.S)
            return re.sub(r"\s+", " ", mm.group(1)).strip() if mm else None
        eid = _tag("id") or ""
        aid = eid.rsplit("/abs/", 1)[-1] if "/abs/" in eid else eid
        entries.append({"arxiv_id": re.sub(r"v\d+$", "", aid),
                        "title": _tag("title"),
                        "summary": (_tag("summary") or "")[:600]})
    return {"query": query, "results": entries}


def get_arxiv_abstract(arxiv_id: str) -> dict:
    """Title + full abstract for one arXiv id.

    Was TWO arXiv requests: a `search_arxiv(f"id:{arxiv_id}")` whose result
    was bound to `r` and then never read, immediately shadowed by the real
    id_list fetch. Every abstract lookup cost double, against the service
    that has since blocked us. One request now."""
    try:
        resp = arxiv_client.get({"id_list": arxiv_id, "max_results": 1},
                                timeout=TIMEOUT)
        if resp.status_code != 200:
            return {"error": f"arxiv abstract fetch failed: HTTP {resp.status_code}"}
        xml = resp.text
        title = re.search(r"<entry>.*?<title[^>]*>(.*?)</title>", xml, re.S)
        summ = re.search(r"<summary[^>]*>(.*?)</summary>", xml, re.S)
        if not summ:
            return {"error": f"no arXiv record for '{arxiv_id}'"}
        return {"arxiv_id": arxiv_id,
                "title": re.sub(r"\s+", " ", title.group(1)).strip() if title else None,
                "abstract": re.sub(r"\s+", " ", summ.group(1)).strip(),
                "html_url": f"https://arxiv.org/abs/{arxiv_id}",
                # ar5iv named by its canonical host (2026-09-09): ar5iv.org is
                # a redirect onto ar5iv.labs.arxiv.org, i.e. arXiv's servers,
                # and only the arxiv.org form is recognisable to fetch_url's
                # host check BEFORE the request is made. Pointing the model at
                # the redirect would have spent arXiv's budget outside it.
                "hint": "fetch_url can read https://arxiv.org/abs/<id> or the "
                        "ar5iv full-text rendering at "
                        "https://ar5iv.labs.arxiv.org/html/<id>"}
    except Exception as e:
        return {"error": f"arxiv abstract fetch failed: {type(e).__name__}: {e}"}


def github_search_code(query: str, limit: int = 8) -> dict:
    """GitHub code search. Supports qualifiers like `repo:owner/name`,
    `filename:...`, `language:python`."""
    limit = max(1, min(int(limit), 15))
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return {"error": "GITHUB_TOKEN not configured"}
    url = ("https://api.github.com/search/code?"
           + urllib.parse.urlencode({"q": query, "per_page": limit}))
    try:
        data = _http_json(url, {"Authorization": f"Bearer {tok}",
                                "Accept": "application/vnd.github.text-match+json"})
    except Exception as e:
        return {"error": f"github code search failed: {e}"}
    out = []
    for it in data.get("items", []) or []:
        matches = [tm.get("fragment", "")[:300]
                   for tm in it.get("text_matches", [])][:2]
        out.append({"repo": it.get("repository", {}).get("full_name"),
                    "path": it.get("path"), "fragments": matches})
    return {"query": query, "total_count": data.get("total_count"), "results": out}


def github_fetch_file(repo: str, path: str, ref: str = None) -> dict:
    """Fetch one file from a GitHub repo (owner/name, path)."""
    tok = os.environ.get("GITHUB_TOKEN")
    if not tok:
        return {"error": "GITHUB_TOKEN not configured"}
    url = f"https://api.github.com/repos/{repo}/contents/{urllib.parse.quote(path)}"
    if ref:
        url += "?" + urllib.parse.urlencode({"ref": ref})
    try:
        data = _http_json(url, {"Authorization": f"Bearer {tok}"})
    except Exception as e:
        return {"error": f"github fetch failed: {e}"}
    if isinstance(data, list):
        return {"repo": repo, "path": path, "directory": True,
                "entries": [{"name": d.get("name"), "type": d.get("type")}
                            for d in data][:60]}
    try:
        text = base64.b64decode(data.get("content", "")).decode("utf-8", "replace")
    except Exception:
        return {"error": "file is not decodable text"}
    truncated = len(text) > FETCH_CAP
    return {"repo": repo, "path": path, "truncated": truncated,
            "content": text[:FETCH_CAP]}


def fetch_url(url: str, start: int = 0) -> dict:
    """Fetch a web page and return extracted text (use start to page
    through long documents).

    An arXiv URL goes through arxiv_client, on the same clock and the same
    single connection as `search_arxiv` and `get_arxiv_abstract` above
    (2026-09-09). This is the sharpest version of the "one hostname over"
    hole: the tool takes ANY url, `get_arxiv_abstract`'s own `hint` field
    tells the model to point it at arxiv.org, the request rate is whatever the
    model under test decides, and it sent a spoofed `Mozilla/5.0` with no
    pacing at all. A benchmark arm is the last caller that should be trusted
    with its own throttle, and the tool's URL is not knowable from the source
    -- so the decision is made here, at runtime, by the same host rule the
    client refuses on."""
    if not re.match(r"^https?://", url):
        return {"error": "only http(s) URLs"}
    try:
        if arxiv_client.is_arxiv_url(url):
            r = arxiv_client.get_url(url, timeout=TIMEOUT)
            ctype = r.headers.get("Content-Type", "")
            raw = r.content[:2_500_000]
        elif api_gateway.known_host(url):
            # A host we have a declared policy for -- S2, dblp, PMLR, CVF and
            # the rest -- is paced on that policy even when the MODEL chose the
            # URL. This is the sharpest version of the "one hostname over"
            # hole and the reason known_host exists.
            r = api_gateway.get(url, timeout=TIMEOUT)
            ctype = r.headers.get("Content-Type", "")
            raw = r.content[:2_500_000]
        else:
            # An undeclared host, chosen by the model under test. It gets our
            # honest identifier and NOT the `Mozilla/5.0 syntology-benchmark`
            # this line used to send: spoofing is what ARXIV_BLOCK_2026-09-09.md
            # refuses to do, and a benchmark is not an exemption. It is still
            # unpaced, which is the open edge of this tool -- an arbitrary URL
            # has no policy to obey.
            req = urllib.request.Request(url, headers={"User-Agent": api_gateway.UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                ctype = r.headers.get("Content-Type", "")
                raw = r.read(2_500_000)
    except Exception as e:
        return {"error": f"fetch failed: {e}"}
    if "html" in ctype:
        p = _TextExtract()
        try:
            p.feed(raw.decode("utf-8", "replace"))
        except Exception:
            pass
        text = "\n".join(p.chunks)
    else:
        text = raw.decode("utf-8", "replace")
    start = max(0, int(start))
    seg = text[start:start + FETCH_CAP]
    return {"url": url, "start": start, "total_chars": len(text),
            "truncated": start + FETCH_CAP < len(text), "content": seg}


TOOLS = {
    "search_semantic_scholar": search_semantic_scholar,
    "search_arxiv": search_arxiv,
    "get_arxiv_abstract": get_arxiv_abstract,
    "github_search_code": github_search_code,
    "github_fetch_file": github_fetch_file,
    "fetch_url": fetch_url,
}


if __name__ == "__main__":
    print(json.dumps(search_arxiv("quantile regression loss", 2), indent=1)[:500])
    print(json.dumps(github_search_code("quantile_loss language:python", 2), indent=1)[:500])
