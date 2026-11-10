"""Refresh finbyz.tech pages right after their ERP content changes.

finbyz.tech (Next.js) caches ERP data for up to 1 h and nginx caches finished pages for 30 min
(finbyz-ops/notes/cdn-and-headless-cache-plan-2026-11-10.md). When a NextJS Page or Job Opening is saved or deleted,
a background job (queued after the commit, so saving is never slowed or blocked):
1. POSTs the page paths to https://finbyz.tech/api/revalidate (accepted only from this server's own address),
   which drops Next.js's cached ERP data for those pages;
2. GETs each page with the header X-Finbyz-Refresh: 1, which nginx honours only from this server: it skips the
   cached copy, renders the page again and stores the new version.
3. purges those URLs from Cloudflare's edge cache, when site_config has "cloudflare_purge_token" (a token limited
   to Zone > Cache Purge on finbyz.tech). Without it Cloudflare's copy expires on its own (edge TTL of the Cache Rule).
Failures are logged and never raised: the 30 min cache refresh is the fallback.
"""

from urllib.parse import quote

import frappe
import requests

SITE = "https://finbyz.tech"
TIMEOUT = 60
CF_ZONE = "cd40717ca03b89a869dc109dda27e7f1"  # finbyz.tech


def _norm(path):
	path = (path or "").strip()
	if not path or "://" in path:
		return None
	if not path.startswith("/"):
		path = "/" + path
	return path.rstrip("/") or "/"


def _paths_for(doc):
	before = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
	paths = set()
	if doc.doctype == "NextJS Page":
		for d in (doc, before):
			if d:
				paths.update({_norm(d.get("route")), _norm(d.get("actual_route"))})
	elif doc.doctype == "Job Opening":
		for d in (doc, before):
			if d and d.get("route"):
				paths.add(_norm("/careers/job-openings/" + d.get("route").strip("/")))
		paths.update({"/careers/job-openings", "/careers"})
	paths.discard(None)
	# the parent hub lists its child pages
	for p in list(paths):
		if p != "/" and p.count("/") > 1:
			paths.add(p.rsplit("/", 1)[0])
	return sorted(paths)


def queue_refresh(doc, method=None):
	"""doc_events hook (on_update / on_trash) for NextJS Page and Job Opening."""
	if frappe.flags.in_import or frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_patch:
		return
	try:
		paths = _paths_for(doc)
		if paths:
			frappe.enqueue(
				"finbyzweb.finbyzweb.doc_events.website_cache.refresh",
				queue="short",
				paths=paths,
				enqueue_after_commit=True,
			)
	except Exception:
		frappe.log_error(title="Website cache refresh not queued", message=frappe.get_traceback())


def refresh(paths):
	"""Background job: drop Next.js data for the paths, then re-render them into the nginx page cache."""
	results = {}
	try:
		r = requests.post(f"{SITE}/api/revalidate", json={"paths": paths}, timeout=TIMEOUT)
		results["revalidate"] = r.status_code
	except Exception as e:
		results["revalidate"] = repr(e)[:120]
	for p in paths:
		try:
			r = requests.get(
				SITE + quote(p),
				headers={"X-Finbyz-Refresh": "1", "User-Agent": "finbyzweb-cache-refresh"},
				timeout=TIMEOUT,
				allow_redirects=False,
			)
			results[p] = r.status_code
		except Exception as e:
			results[p] = repr(e)[:120]
	token = frappe.conf.get("cloudflare_purge_token")
	if token:
		results["cloudflare"] = _cf_purge(token, [SITE + quote(p) for p in paths])
	if results.get("revalidate") != 200 or results.get("cloudflare", True) is not True or any(
		not isinstance(v, int) or v >= 500 for k, v in results.items() if k != "cloudflare"
	):
		frappe.log_error(title="Website cache refresh incomplete", message=frappe.as_json(results))
	return results


def _cf_purge(token, urls):
	"""Purge the given URLs from Cloudflare's cache (max 30 per call). Returns True or an error text."""
	try:
		for i in range(0, len(urls), 30):
			r = requests.post(
				f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE}/purge_cache",
				headers={"Authorization": f"Bearer {token}"},
				json={"files": urls[i : i + 30]},
				timeout=TIMEOUT,
			)
			if not r.ok or not r.json().get("success"):
				return f"{r.status_code} {r.text[:200]}"
		return True
	except Exception as e:
		return repr(e)[:120]
