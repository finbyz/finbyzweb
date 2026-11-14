"""Keep the website chatbot's knowledge base (Pinecone) in step with finbyz.tech, and let the SEO agents ask it
which existing pages already cover a query.

sync(apply=0)      Read every sitemap URL, extract the main text (no menu / footer), and compare with the last sync.
                   New pages are added, changed pages re-embedded, pages gone from the sitemap removed.
                   apply=0 (default) only reports. Daily cron:
                   bench --site erp.finbyz.tech execute finbyzweb.finbyzweb.kb_sync.sync --kwargs "{'apply': 1}"
overlap(queries)   For each query: the existing pages that match best (vector search, grouped by page). Read-only.

The knowledge base is the one linked in the enabled Chatbot Settings row (today finbyz_tech_knowledge_base).
Vector ids and metadata follow finbyzai's own KB processing ({kb}_links_{row}_{i}), so the chatbot and the KB
form keep working unchanged. State (text hash + chunk count per page): sites/<site>/private/kb_sync_state.json.
"""
import concurrent.futures as cf
import hashlib
import json
import os
import re

import frappe
import requests
from bs4 import BeautifulSoup

SITE = "https://finbyz.tech"
UA = "Mozilla/5.0 (compatible; FinbyzKBSync/1.0; +https://finbyz.tech)"
MIN_SITEMAP_URLS = 200        # fewer means the sitemap is broken: do nothing
MAX_REMOVE_SHARE = 0.15       # refuse to remove more than this share of the KB in one run (force=1 overrides)


def _kb_name():
    kb = frappe.db.get_value("Chatbot Settings", {"enabled": 1, "website_url": ["like", "%finbyz.tech%"]}, "knowledge_base")
    return kb or "finbyz_tech_knowledge_base"


def _path(url):
    p = re.sub(r"^https?://(www\.)?finbyz\.tech", "", (url or "").strip())
    p = p.split("#")[0].split("?")[0].rstrip("/")
    return p or "/"


def _state_file():
    return frappe.get_site_path("private", "kb_sync_state.json")


def _load_state():
    try:
        with open(_state_file()) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state):
    f = _state_file()
    tmp = f + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(state, fh, indent=0, sort_keys=True)
    os.replace(tmp, f)


def sitemap_paths():
    r = requests.get(SITE + "/sitemap.xml", headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    kids = re.findall(r"<loc>([^<]+)</loc>", r.text)
    out = []
    for k in kids:
        t = requests.get(k.strip(), headers={"User-Agent": UA}, timeout=30)
        t.raise_for_status()
        out += [_path(u) for u in re.findall(r"<loc>([^<]+)</loc>", t.text)]
    return list(dict.fromkeys(out))


def page_text(path):
    """-> (status, text) with title, URL and description on top and the main content without menus or footer.
    status is 'ok', 'redirect' (final URL differs) or the HTTP code / error."""
    url = SITE + ("" if path == "/" else path)
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=25, allow_redirects=True)
    except Exception as e:
        return "error %s" % type(e).__name__, ""
    if r.status_code != 200:
        return str(r.status_code), ""
    if _path(r.url) != path:
        return "redirect", ""
    s = BeautifulSoup(r.content, "html.parser")
    title = (s.title.get_text(" ", strip=True) if s.title else "")
    d = s.find("meta", attrs={"name": "description"})
    desc = (d.get("content") or "").strip() if d else ""
    for t in s(["script", "style", "noscript", "header", "nav", "footer", "aside", "svg", "form", "iframe"]):
        t.decompose()
    for t in s.select("#saas-chatbot, [role=dialog]"):
        t.decompose()
    body = " ".join((s.body or s).get_text(" ").split())
    return "ok", "%s\n%s\n%s\n\n%s" % (title, url, desc, body)


def _store_and_index(kb):
    from pinecone import Pinecone
    store = kb.get_vector_store()          # also loads the Pinecone key into the environment
    index = Pinecone(api_key=os.environ.get("PINECONE_API_KEY")).Index(store._sanitize_index_name(kb.name))
    return store, index


def _ids_for(index, source_id):
    ids = []
    for page in index.list(prefix=source_id + "_"):
        ids += list(page)
    return ids


def sync(apply=0, force=0, limit=0, only=None):
    """Compare the sitemap with the knowledge base and (apply=1) bring the KB up to date. Returns a summary dict."""
    apply, force, limit = int(apply or 0), int(force or 0), int(limit or 0)
    kb_name = _kb_name()
    kb = frappe.get_doc("Knowledge Base", kb_name)
    state = _load_state()

    paths = sitemap_paths()
    if len(paths) < MIN_SITEMAP_URLS:
        return {"error": "sitemap has only %d URLs (< %d); nothing done" % (len(paths), MIN_SITEMAP_URLS)}
    if only:
        only = [_path(p) for p in (only if isinstance(only, list) else json.loads(only) if str(only).startswith("[") else [only])]
        paths = [p for p in paths if p in only]
    if limit:
        paths = paths[:limit]

    rows, dupes = {}, []
    for row in kb.links or []:
        if (row.url or "").startswith(SITE):
            p = _path(row.url)
            if p in rows:
                # same page twice (e.g. with and without a trailing slash): keep the row the state knows
                keep = rows[p] if state.get(p, {}).get("row") != row.name else row
                dupes.append(row if keep is rows[p] else rows[p])
                rows[p] = keep
            else:
                rows[p] = row

    with cf.ThreadPoolExecutor(4) as ex:
        fetched = dict(zip(paths, ex.map(page_text, paths)))

    new, changed, same, failed = [], [], [], []
    for p in paths:
        status, text = fetched[p]
        if status != "ok" or len(text) < 200:
            failed.append((p, status))
            continue
        h = hashlib.sha1(text.encode()).hexdigest()
        if p not in rows:
            new.append((p, text, h))
        elif state.get(p, {}).get("hash") != h:
            changed.append((p, text, h))
        else:
            same.append(p)

    removed = [] if (only or limit) else [p for p in rows if p not in set(paths)]
    summary = {"kb": kb_name, "sitemap": len(paths), "in_kb": len(rows), "new": [x[0] for x in new],
               "changed": [x[0] for x in changed], "unchanged": len(same), "removed": removed,
               "duplicates": [d.url for d in dupes], "fetch_failed": failed,
               "applied": bool(apply)}
    if removed and len(removed) > MAX_REMOVE_SHARE * max(1, len(rows)) and not force:
        summary["error"] = "would remove %d of %d pages (> %d %%); nothing done, rerun with force=1 if intended" % (
            len(removed), len(rows), MAX_REMOVE_SHARE * 100)
        return summary
    if not apply:
        return summary

    store, index = _store_and_index(kb)
    splitter = kb.get_text_splitter()

    # new pages get a row first (marked processed: this job embeds them, not the KB's own queue)
    if new:
        for p, _, _ in new:
            kb.append("links", {"url": SITE + ("" if p == "/" else p), "is_processed": 1})
        kb.save(ignore_permissions=True)
        frappe.db.commit()
        rows = {_path(r.url): r for r in kb.links if (r.url or "").startswith(SITE)}

    done, errors = 0, []
    for p, text, h in new + changed:
        row = rows[p]
        source_id = "%s_links_%s" % (kb_name, row.name)
        try:
            chunks = splitter.split_text(text)
            ids = ["%s_%d" % (source_id, i) for i in range(len(chunks))]
            metas = [{"kb": kb_name, "source_id": source_id, "row_name": row.name, "doc_type": "web_url",
                      "chunk_index": i, "url": SITE + ("" if p == "/" else p)} for i in range(len(chunks))]
            store.upsert(texts=chunks, metadatas=metas, ids=ids)
            stale = [i for i in _ids_for(index, source_id) if i not in set(ids)]
            if stale:
                index.delete(ids=stale)
            state[p] = {"hash": h, "chunks": len(chunks), "row": row.name, "synced": str(frappe.utils.today())}
            done += 1
        except Exception as e:
            errors.append((p, str(e)[:200]))

    for p in removed:
        row = rows[p]
        source_id = "%s_links_%s" % (kb_name, row.name)
        try:
            ids = _ids_for(index, source_id)
            if ids:
                index.delete(ids=ids)
            kb.remove(row)
            state.pop(p, None)
        except Exception as e:
            errors.append((p, str(e)[:200]))
    for row in dupes:
        try:
            ids = _ids_for(index, "%s_links_%s" % (kb_name, row.name))
            if ids:
                index.delete(ids=ids)
            kb.remove(row)
        except Exception as e:
            errors.append((row.url, str(e)[:200]))
    if removed or dupes:
        kb.save(ignore_permissions=True)
        frappe.db.commit()

    _save_state(state)
    summary.update(embedded=done, errors=errors)
    if errors:
        frappe.log_error(title="KB sync: some pages failed", message=json.dumps(errors, indent=1)[:5000])
    return summary


def overlap(queries, k=40, top=5):
    """queries: list of strings (or a JSON string). -> {query: [{page, score, chunks}]} best page first. Read-only."""
    if isinstance(queries, str):
        queries = json.loads(queries) if queries.strip().startswith("[") else [queries]
    kb = frappe.get_doc("Knowledge Base", _kb_name())
    store = kb.get_vector_store()
    out = {}
    for q in queries:
        pages = {}
        for r in store.search(q, k=int(k)):
            p = _path(r["metadata"].get("url") or "")
            e = pages.setdefault(p, {"page": p, "score": 0.0, "chunks": 0})
            e["score"] = max(e["score"], round(float(r["score"]), 4))
            e["chunks"] += 1
        out[q] = sorted(pages.values(), key=lambda e: -e["score"])[:int(top)]
    return out
