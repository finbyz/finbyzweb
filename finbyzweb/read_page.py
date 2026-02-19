
import frappe

def read_page(name):
    page = frappe.get_doc("NextJS Page", name)
    print(f"Name: {page.name}")
    print(f"Content Type: {page.content_type}")
    print("--- Content (Rich Text) ---")
    print(page.content)
    print("--- Content (Markdown) ---")
    print(page.content_md)
