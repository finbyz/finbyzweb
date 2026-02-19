import frappe
import re

def execute():
    pages = frappe.get_all("NextJS Page", fields=["name", "content_type", "content", "content_md"])
    for page in pages:
        doc = frappe.get_doc("NextJS Page", page.name)
        if fix_record(doc):
            doc.save()

def fix_record(doc):
    text = doc.content or doc.content_md
    if not text:
        return False
    
    detected_format = detect_format(text)
    changed = False

    # Case 1: Content looks like Markdown, but type is Rich Text and data is in Rich Text field
    if detected_format == "Markdown" and doc.content_type == "Rich Text" and doc.content and not doc.content_md:
        doc.content_type = "Markdown"
        doc.content_md = doc.content
        doc.content = ""
        changed = True
    # Case 2: Content looks like HTML, but type is Markdown and data is in Markdown field
    elif detected_format == "Rich Text" and doc.content_type == "Markdown" and doc.content_md and not doc.content:
        doc.content_type = "Rich Text"
        doc.content = doc.content_md
        doc.content_md = ""
        changed = True
    # Case 3: Type is Markdown, but data is in Rich Text field (type matches detected format or is neutral)
    elif doc.content_type == "Markdown" and doc.content and not doc.content_md:
        doc.content_md = doc.content
        doc.content = ""
        changed = True
    # Case 4: Type is Rich Text, but data is in Markdown field
    elif doc.content_type == "Rich Text" and doc.content_md and not doc.content:
        doc.content = doc.content_md
        doc.content_md = ""
        changed = True

    return changed

def detect_format(text):
    if not text:
        return None
    # Check for common HTML tags
    html_tags = re.compile(r'<p>|<div>|<strong>|<em>|<ul>|<li>|<br>', re.IGNORECASE)
    if html_tags.search(text):
        return "Rich Text"
    # Check for common Markdown syntax
    markdown_syntax = re.compile(r'^#\s|^##\s|^###\s|\*\*|\[.*\]\(.*\)', re.MULTILINE)
    if markdown_syntax.search(text):
        return "Markdown"
    return "Unknown"
