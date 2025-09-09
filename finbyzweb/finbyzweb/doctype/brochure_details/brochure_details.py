# Copyright (c) 2025, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

# finbyzweb.finbyzweb.doctype.brochure_details.brochure_details.create_brochure
import frappe
from frappe.model.document import Document


class BrochureDetails(Document):
	pass


     
@frappe.whitelist(allow_guest=True)
def create_brochure(name, email_id, mobile_no, company_name):
    existing = frappe.db.exists("Brochure Details", {"email": email_id})
    if existing:
        return {"status": "exists", "Brochure Details": existing}

    doc = frappe.get_doc({
        "doctype": "Brochure Details",
        "name1": name,
        "email": email_id,
        "mobile": mobile_no,
        "organization": company_name,
        
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success", "Brochure Details": doc.name}

