
import frappe

def check_content(name='whats-new-erpnext-v16-complete-feature-guide'):
    doc = frappe.get_doc('NextJS Page', name)
    print(f"NAME: {doc.name}")
    print(f"CONTENT TYPE: {doc.content_type}")
    print("-" * 20)
    print("CONTENT (Rich Text):")
    print(doc.content)
    print("-" * 20)
    print("CONTENT MD (Markdown):")
    print(doc.content_md)
    print("-" * 20)

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else 'whats-new-erpnext-v16-complete-feature-guide'
    # This part depends on how it's called. 
    # If via bench execute, it won't run __main__.
