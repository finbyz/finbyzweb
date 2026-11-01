import frappe
from frappe import _
import secrets
import string

@frappe.whitelist()
def send_to_employee_joining_detail(job_offer_id):
	job_offer = frappe.get_doc("Job Offer", job_offer_id)
	job_offer.check_permission("read")
	N = 32
	# the token alone grants access to the joiner's form, so use a cryptographically secure generator
	res = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(N))
	joining_detail = frappe.get_doc({
		"doctype": "Employee Joining Detail",
		"first_name": job_offer.applicant_name,  
		"personal_email": job_offer.job_applicant,
		"job_offer":job_offer.name,
		"job_applicant":job_offer.job_applicant,
		"token":res,
		"url":f"https://finbyz.tech/employee-joining-details?token={res}"
	})

	joining_detail.insert()
	frappe.db.commit()
	frappe.msgprint(_("Employee Joining Detail created successfully."))
	return True