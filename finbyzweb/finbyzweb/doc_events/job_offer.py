import frappe
from frappe import _

@frappe.whitelist()
def send_to_employee_joining_detail(job_offer_id):
    job_offer = frappe.get_doc("Job Offer", job_offer_id)

    joining_detail = frappe.get_doc({
        "doctype": "Employee Joining Detail",
        "first_name": job_offer.applicant_name,  
        "personal_email": job_offer.job_applicant,
        # "date_of_joining": job_offer.date_of_joining,  
    })

    joining_detail.insert()
    frappe.db.commit()
    frappe.msgprint(_("Employee Joining Detail created successfully."))
    return True