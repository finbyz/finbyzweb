import frappe
from frappe import _
import string
import random

@frappe.whitelist()
def send_to_employee_joining_detail(job_offer_id):
	job_offer = frappe.get_doc("Job Offer", job_offer_id)
	N = 32
	res = ''.join(random.choices(string.ascii_uppercase +
									string.digits, k=N))
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