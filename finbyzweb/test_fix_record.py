import frappe
import re

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

def test_fix_record(name=None, commit=False):
    if not name:
        # Search for a candidate if name is not provided
        candidates = frappe.get_all("NextJS Page", filters={"content_type": "Markdown", "content_md": ""}, fields=["name"])
        if not candidates:
            print("No candidates found with filters {'content_type': 'Markdown', 'content_md': ''}")
            # Try a broader search
            all_pages = frappe.get_all("NextJS Page", limit=5, fields=["name", "content_type"])
            print(f"Sample of all Pages: {all_pages}")
            return
        name = candidates[0].name
        print(f"No name provided, selected candidate: {name}")

    print(f"Fetching record with name: '{name}'")
    try:
        doc = frappe.get_doc("NextJS Page", name)
    except frappe.DoesNotExistError:
        print(f"Error: Record '{name}' not found.")
        # Try to find record with similar name
        similar = frappe.db.sql(f"select name from `tabNextJS Page` where name like '%{name}%'", as_dict=1)
        print(f"Similar records: {similar}")
        return


    print(f"Processing Record: {doc.name}")
    print(f"Current Content Type: {doc.content_type}")
    print(f"Content (Rich Text) Length: {len(doc.content) if doc.content else 0}")
    print(f"Content (Markdown) Length: {len(doc.content_md) if doc.content_md else 0}")

    original_content = doc.content
    original_content_md = doc.content_md
    original_type = doc.content_type

    detected_format = detect_format(doc.content or doc.content_md)
    print(f"Detected Format from Content: {detected_format}")

    changed = False
    # Logic to fix
    
    # Priority 1: If detected format contradicts content_type and the field it's in
    if detected_format == "Markdown" and doc.content_type == "Rich Text" and doc.content and not doc.content_md:
        print("Detected Case: Content looks like Markdown, but type is Rich Text and data is in Rich Text field. Switching Type and moving data.")
        doc.content_type = "Markdown"
        doc.content_md = doc.content
        doc.content = ""
        changed = True
    elif detected_format == "Rich Text" and doc.content_type == "Markdown" and doc.content_md and not doc.content:
        print("Detected Case: Content looks like HTML, but type is Markdown and data is in Markdown field. Switching Type and moving data.")
        doc.content_type = "Rich Text"
        doc.content = doc.content_md
        doc.content_md = ""
        changed = True
    
    # Priority 2: Mismatch between type and field (already handled in previous version)
    elif doc.content_type == "Markdown" and doc.content and not doc.content_md:
        print("Detected Case: Type is Markdown, but data is in Rich Text field. Moving data.")
        doc.content_md = doc.content
        doc.content = ""
        changed = True
    elif doc.content_type == "Rich Text" and doc.content_md and not doc.content:
        print("Detected Case: Type is Rich Text, but data is in Markdown field. Moving data.")
        doc.content = doc.content_md
        doc.content_md = ""
        changed = True
        
    # Case 3: Both have data - this might need manual intervention or smarter detection
    elif doc.content and doc.content_md:
        print("Warning: Both fields have data. Skipping for now as it's ambiguous.")
        return
    # Case 4: Neither has data but maybe the type should be checked?
    elif not doc.content and not doc.content_md:
        print("No data in either field. Nothing to do.")
        return
    else:
        print("Current state seems consistent with content_type and detected format.")

    if changed:
        print("-" * 20)
        print("PROPOSED CHANGES:")
        print(f"Content Type: {original_type} -> {doc.content_type}")
        print(f"Content (Rich Text) Length: {len(original_content) if original_content else 0} -> {len(doc.content) if doc.content else 0}")
        print(f"Content (Markdown) Length: {len(original_content_md) if original_content_md else 0} -> {len(doc.content_md) if doc.content_md else 0}")

        if commit:
            print("Saving changes...")
            doc.save()
            frappe.db.commit()
            print("Done.")
        else:
            print("Snapshot only. Run with commit=True to save.")
    
    return changed

def fix_all_records(commit=False):
    print(f"Starting fix for all NextJS Page records. Commit: {commit}")
    all_pages = frappe.get_all("NextJS Page", fields=["name"])
    total = len(all_pages)
    fixed = 0
    
    for i, p in enumerate(all_pages):
        print(f"[{i+1}/{total}] Processing {p.name}...")
        if test_fix_record(p.name, commit):
            fixed += 1
        print("-" * 10)
    
    print(f"Execution complete. Total records processed: {total}. Records fixed: {fixed}.")

if __name__ == "__main__":
    import sys
    # Usage: 
    # Single record dry run: python test_fix_record.py "name"
    # Single record commit: python test_fix_record.py "name" True
    # All records dry run: python test_fix_record.py ALL
    # All records commit: python test_fix_record.py ALL True
    
    target = sys.argv[1] if len(sys.argv) > 1 else None
    commit = sys.argv[2].lower() == 'true' if len(sys.argv) > 2 else False
    
    if target == "ALL":
        fix_all_records(commit)
    else:
        test_fix_record(target, commit)


