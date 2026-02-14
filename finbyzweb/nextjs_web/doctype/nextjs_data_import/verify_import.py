import frappe
from frappe.utils import get_site_path
import os

def execute():
    try:
        # Cleanup
        frappe.db.delete("NextJS Page", {"route": "/verify-csv"})
        frappe.db.delete("NextJS Data Import", {"status": ["!=", "Completed"]}) # delete old/pending
        
        # Create Dummy CSV
        csv_content = "title,route,page_type,content\nVerify CSV,/verify-csv,Web page,Verified Content"
        fname = "verify_import.csv"
        fpath = get_site_path("public", "files", fname)
        
        with open(fpath, "w") as f:
            f.write(csv_content)
            
        # Create File Doc
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": fname,
            "is_private": 0,
            "content": csv_content
        }).insert(ignore_permissions=True)

        print(f"File created: {file_doc.file_url}")

        # Create Import Doc
        import_doc = frappe.get_doc({
            "doctype": "NextJS Data Import",
            "import_file": file_doc.file_url,
            "import_type": "Insert New"
        }).insert(ignore_permissions=True)

        print(f"Import Doc created: {import_doc.name}")

        # Run Import
        import_doc.import_data()
        
        if frappe.db.exists("NextJS Page", {"route": "/verify-csv"}):
            page = frappe.get_doc("NextJS Page", {"route": "/verify-csv"})
            if page.title == "Verify CSV" and page.page_type == "Web page" and page.content == "Verified Content":
                print("SUCCESS: CSV Import Verified")
            else:
                print(f"FAILURE: Page data mismatch. Title: {page.title}, Type: {page.page_type}, Content: {page.content}")
        else:
            import_doc.reload()
            print(f"FAILURE: Page not found. Import Status: {import_doc.status}")
            print(f"Import Log:\n{import_doc.log}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
