import frappe
import re


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text


@frappe.whitelist(methods=["POST"])
def generate_nextjs_page(name, instruction):

    if not frappe.db.exists("Code Snippet", name):
        frappe.throw(f"Code Snippet {name} not found")

    doc = frappe.get_doc("Code Snippet", name)

    if not doc.snippet_name:
        frappe.throw("snippet_name is missing in Code Snippet.")

    ai_agent_doc = frappe.get_doc("AI Agent", "NextJs Page Agent")

    ai_input_data = {
        "instruction": instruction,
        "snippet": doc.code_snippet,
        "category": doc.category,
        "language": doc.language,
        "description": doc.seo_description or "",
    }
    result = ai_agent_doc.agent_service.invoke(**ai_input_data)
    if not result:
        frappe.throw("Agent returned no result")

    route = f"/{slugify(result.title)}"

    if frappe.db.exists("NextJS Page", {"route": route}):
        existing = frappe.db.get_value("NextJS Page", {"route": route}, "name")
        return {
            "success": False,
            "message": f"Already exists: {route}",
            "redirect": f"/app/nextjs-page/{existing}",
        }

    return {
        "success": True,
        "message": f"Data generated for: {result.title}",
        "doc_data": {
            "title": result.title,
            "meta_title": result.meta_title,
            "meta_description": result.meta_description,
            "keywords": result.keywords,
            "image": "https://finbyz.tech/images/FinbyzLogo.png",
            "content": result.content,
            "content_type": "Rich Text",
            "route": route,
            "actual_route": route,
            "page_type": "Code Snippet",
            "parent_nextjs_page": "erpnext-wiki",
            "source_code_snippet": name,
        },
    }
