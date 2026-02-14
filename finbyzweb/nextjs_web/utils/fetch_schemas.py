import frappe
import requests
import json
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

BASE_URL = "https://finbyz.tech"

# Headers mimicking Googlebot for best extraction results
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# Principal schema types we want to store and map
INTEREST_TYPES = [
    "WebPage", "FAQPage", "BreadcrumbList", "ProfessionalService", 
    "Organization", "LocalBusiness", "Service"
]

@frappe.whitelist()
def sync_all_pages_background(batch_size=10):
    """
    Triggers the automated sync process for all pages in the background.
    """
    batch_size = int(batch_size)
    frappe.enqueue(
        'finbyzweb.nextjs_web.utils.fetch_schemas.sync_schemas_for_pages',
        queue='long',
        timeout=3600,
        batch_size=batch_size,
        start_offset=0
    )
    return {"status": "queued", "message": "Background sync job started."}

@frappe.whitelist()
def test_single_page(route="/erpnext/services/website-development-on-erpnext"):
    """
    Test and verify sync for a single page.
    Maps data to fields and updates the child table.
    """
    try:
        # Find page
        page_docname = frappe.get_value("NextJS Page", {"route": route}, "name")
        if not page_docname:
            # Try by name/slug
            page_docname = frappe.get_value("NextJS Page", route, "name")
            
        if not page_docname:
            return {"status": "error", "message": f"Page not found: {route}"}
            
        doc = frappe.get_doc("NextJS Page", page_docname)
        full_route = doc.route if doc.route.startswith("/") else "/" + doc.route
        full_url = urljoin(BASE_URL, full_route)
        
        frappe.logger().info(f"Syncing {full_url}")
        schemas = fetch_page_schemas(full_url)
        
        if not schemas:
            return {"status": "warning", "message": "No schemas extracted."}
            
        # Map to fields and save
        sync_result = process_and_save_doc(doc, schemas)
        frappe.db.commit()
        
        return {
            "status": "success",
            "page": doc.name,
            "schemas_found": len(schemas),
            "types": [s.get("@type") for s in schemas],
            "details": sync_result
        }
        
    except Exception as e:
        frappe.logger().error(f"Sync test failed: {str(e)}")
        return {"status": "error", "message": str(e), "traceback": frappe.get_traceback()}

@frappe.whitelist()
def sync_schemas_for_pages(batch_size=10, start_offset=0):
    """
    Background worker for batch processing.
    """
    pages = frappe.get_all("NextJS Page", fields=["name"], limit_start=start_offset, limit_page_length=batch_size)
    
    if not pages:
        return
        
    for p in pages:
        try:
            doc = frappe.get_doc("NextJS Page", p.name)
            if not doc.route: continue
            
            full_url = urljoin(BASE_URL, doc.route)
            schemas = fetch_page_schemas(full_url)
            if schemas:
                process_and_save_doc(doc, schemas)
                frappe.db.commit()
        except: continue
        
    # Chain next batch
    total = frappe.db.count("NextJS Page")
    next_offset = start_offset + batch_size
    if next_offset < total:
        frappe.enqueue(
            'finbyzweb.nextjs_web.utils.fetch_schemas.sync_schemas_for_pages',
            queue='long', batch_size=batch_size, start_offset=next_offset
        )

@frappe.whitelist()
def force_sync_all():
    """
    Forcefully sync all pages regardless of their last update time.
    """
    pages = frappe.get_all("NextJS Page", fields=["name", "route"])
    count = 0
    for p in pages:
        try:
            doc = frappe.get_doc("NextJS Page", p.name)
            if not doc.route: continue
            
            full_url = urljoin(BASE_URL, doc.route)
            schemas = fetch_page_schemas(full_url)
            if schemas:
                process_and_save_doc(doc, schemas)
                frappe.db.commit()
                count += 1
        except Exception as e:
            frappe.logger().error(f"Force sync failed for {p.name}: {str(e)}")
            
    return {"status": "success", "synced_count": count}

@frappe.whitelist()
def sync_missing_pages():
    """
    Sync all pages that currently have no schemas in the child table.
    """
    missing = frappe.db.sql("""
        SELECT name, route FROM `tabNextJS Page` 
        WHERE name NOT IN (SELECT DISTINCT parent FROM `tabNextJS Page Schema`)
    """, as_dict=1)
    
    count = 0
    for p in missing:
        try:
            doc = frappe.get_doc("NextJS Page", p.name)
            if not doc.route: continue
            
            full_url = urljoin(BASE_URL, doc.route)
            schemas = fetch_page_schemas(full_url)
            if schemas:
                process_and_save_doc(doc, schemas)
                frappe.db.commit()
                count += 1
        except: continue
        
    return {"status": "success", "synced_count": count}

@frappe.whitelist()
def sync_pages_by_list(pages):
    """
    Sync a specific list of pages (either names or routes).
    Example: ["website-development", "/crm"]
    """
    if isinstance(pages, str):
        pages = json.loads(pages)
        
    count = 0
    results = []
    
    for p_id in pages:
        try:
            # Try finding by name first
            docname = frappe.db.get_value("NextJS Page", p_id, "name")
            if not docname:
                # Try finding by route
                docname = frappe.db.get_value("NextJS Page", {"route": p_id}, "name")
                
            if not docname:
                results.append({"id": p_id, "status": "not_found"})
                continue
                
            doc = frappe.get_doc("NextJS Page", docname)
            if not doc.route:
                results.append({"id": p_id, "status": "no_route"})
                continue
                
            full_url = urljoin(BASE_URL, doc.route)
            schemas = fetch_page_schemas(full_url)
            
            if schemas:
                stats = process_and_save_doc(doc, schemas)
                frappe.db.commit()
                results.append({"id": p_id, "status": "synced", "stats": stats})
                count += 1
            else:
                results.append({"id": p_id, "status": "no_schemas"})
        except Exception as e:
            results.append({"id": p_id, "status": "error", "message": str(e)})
            
    return {"synced_count": count, "details": results}

def fetch_page_schemas(url):
    """
    Extracts all JSON-LD schemas using standard parsing and robust regex for hydration scripts.
    """
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        html = res.text
        
        raw_schemas = []
        
        # 1. BS4 standard
        soup = BeautifulSoup(html, 'html.parser')
        for s in soup.find_all('script', type='application/ld+json'):
            if s.string:
                try:
                    data = json.loads(s.string.strip())
                    flatten_and_collect(data, raw_schemas)
                except: pass
                
        # 2. Next.js Hydration Script Robust Regex
        # Handles escaped strings in self.__next_f.push
        clean_html = html.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
        for match in re.finditer(r'\"@context\"\s*:\s*\"https?://schema\.org\"', clean_html):
            start = clean_html.rfind('{', 0, match.start())
            if start != -1:
                # Incremental brace matching
                for end in range(match.start() + 10, min(match.start() + 20000, len(clean_html))):
                    if clean_html[end] == '}':
                        try:
                            data = json.loads(clean_html[start:end+1])
                            if isinstance(data, dict):
                                flatten_and_collect(data, raw_schemas)
                                break
                        except: continue
                        
        # Deduplicate
        unique = []
        seen = set()
        for s in raw_schemas:
            # We filter for main entities only
            stype = s.get("@type")
            if not stype: continue
            
            # Key by type and content hash to find true unique items
            content_key = hash(json.dumps(s, sort_keys=True))
            if content_key not in seen:
                seen.add(content_key)
                unique.append(s)
                
        return unique
    except:
        return []

def flatten_and_collect(data, collection):
    """
    Recursively find all schema objects in a graph or nested structure.
    """
    if isinstance(data, list):
        for item in data: flatten_and_collect(item, collection)
    elif isinstance(data, dict):
        stype = data.get("@type")
        if stype:
            # Handle list of types
            types = stype if isinstance(stype, list) else [stype]
            if any(t in INTEREST_TYPES for t in types) or "@context" in data:
                collection.append(data)
                
        # Dig deeper
        for k, v in data.items():
            if isinstance(v, (dict, list)): flatten_and_collect(v, collection)

def process_and_save_doc(doc, schemas):
    """
    Maps extracted data to the document fields and child tables.
    """
    has_changes = False
    stats = {"faqs": 0, "schemas": 0, "seo": False}
    
    # 1. Update Core Metadata from WebPage schema if possible
    webpage = next((s for s in schemas if s.get("@type") == "WebPage"), None)
    if webpage:
        if webpage.get("name") and not doc.meta_title:
            doc.meta_title = webpage.get("name")
            has_changes = True
        if webpage.get("description") and not doc.meta_description:
            doc.meta_description = webpage.get("description")
            has_changes = True
        stats["seo"] = True
            
    # 2. Update FAQs Table
    faq_page = next((s for s in schemas if s.get("@type") == "FAQPage"), None)
    if faq_page and faq_page.get("mainEntity"):
        # Clear existing and re-populate to keep in sync with Web
        doc.set("faqs", [])
        for item in faq_page["mainEntity"]:
            q = item.get("name")
            a = item.get("acceptedAnswer", {}).get("text")
            if q and a:
                doc.append("faqs", {"question": q, "answer": a})
                stats["faqs"] += 1
        has_changes = True
                
    # 3. Update Schemas Child Table
    # We only keep the 100% required ones in the table to avoid clutter
    # Google likes: FAQPage, BreadcrumbList, ProfessionalService/Organization
    required_in_table = ["WebPage", "FAQPage", "BreadcrumbList", "ProfessionalService", "Organization", "LocalBusiness"]
    
    # Filter schemas to only these
    target_schemas = [s for s in schemas if s.get("@type") in required_in_table]
    
    # Sync keeping unique types
    doc.set("nextjs_page_schema", [])
    for s_data in target_schemas:
        s_type = s_data.get("@type")
        # Ensure schema type exists in system
        if not frappe.db.exists("NextJS Schema Type", s_type):
            frappe.get_doc({
                "doctype": "NextJS Schema Type", "name": s_type, 
                "schema": json.dumps(s_data, indent=2)
            }).insert(ignore_permissions=True)
            
        doc.append("nextjs_page_schema", {
            "schema_type": s_type,
            "schema_json": json.dumps(s_data, indent=2)
        })
        stats["schemas"] += 1
    has_changes = True
    
    if has_changes:
        doc.save(ignore_permissions=True)
        
    return stats

@frappe.whitelist()
def get_sync_status():
    """
    Get sync statistics and recent activity.
    """
    total = frappe.db.count("NextJS Page")
    with_schemas = frappe.db.sql("SELECT COUNT(DISTINCT parent) FROM `tabNextJS Page Schema`")[0][0]
    
    # Get pages updated in the last hour
    recent_updates = frappe.get_all(
        "NextJS Page",
        fields=["name", "route", "modified"],
        filters={"modified": [">", frappe.utils.add_to_date(None, minutes=-60)]},
        order_by="modified desc",
        limit=50
    )
    
    return {
        "total_pages": total,
        "synced_pages": with_schemas,
        "unsynced_pages": total - with_schemas,
        "coverage": f"{int(with_schemas/total*100) if total else 0}%",
        "recent_updates_count": len(recent_updates),
        "recent_updates": recent_updates,
        "timestamp": datetime.now().isoformat()
    }