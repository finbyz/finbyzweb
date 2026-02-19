
import frappe

def list_pages():
    pages = frappe.get_all("NextJS Page", fields=["name", "title", "content_type", "content", "content_md"])
    for page in pages:
        if page.content or page.content_md:
            print(f"Name: {page.name}")
            print(f"Title: {page.title}")
            print(f"Content Type: {page.content_type}")
            print(f"Content (Rich Text) Length: {len(page.content) if page.content else 0}")
            print(f"Content (Markdown) Length: {len(page.content_md) if page.content_md else 0}")
            if page.content:
                print(f"Content Preview: {page.content[:100]}...")
            if page.content_md:
                print(f"Content MD Preview: {page.content_md[:100]}...")
            print("-" * 20)


