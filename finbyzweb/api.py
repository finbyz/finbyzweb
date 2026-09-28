from __future__ import unicode_literals

import frappe
import requests


TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_TIMEOUT_SECONDS = 5

@frappe.whitelist()
def customer_before_save(self, method):
	doc = frappe.get_single("Customer Details")
	doc.ignore_permissions = True

	if self.show_on_website:
		if not frappe.db.exists("Customer Details List", {'customer': self.customer_name}):
			doc.append('customer_details_list', {
					'customer': self.customer_name,
					'image': self.image
				})
			doc.save()

	else:
		if frappe.db.exists("Customer Details List", {'customer': self.customer_name}):
			to_remove = [row for row in doc.get('customer_details_list') if row.customer == self.customer_name]
			[doc.remove(row) for row in to_remove]
			doc.save()

	frappe.db.commit()

@frappe.whitelist(allow_guest=True, methods=["POST"])
def set_form_contact_data(
	lead_name: str,
	company_name: str,
	mobile_no: str,
	title: str,
	email: str,
	notes: str,
):
	_verify_turnstile(frappe.form_dict.get("cf-turnstile-response"))

	data = frappe.new_doc("Lead")
	data.lead_name = lead_name
	data.company_name = company_name
	data.mobile_no = mobile_no
	data.source = 'Website'
	data.notes = title
	data.email_id = email
	data.notes = notes
	data.save(ignore_permissions=True)
	
	frappe.db.commit()
	
@frappe.whitelist(allow_guest=True, methods=["POST"])
def set_form_data(
	lead_name: str,
	company_name: str,
	mobile_no: str,
	title: str,
	email: str,
	message: str = "",
):
	_verify_turnstile(frappe.form_dict.get("cf-turnstile-response"))

	data = frappe.new_doc("Lead")
	data.lead_name = lead_name
	data.company_name = company_name
	data.mobile_no = mobile_no
	data.source = 'Website'
	data.source_web_page = title
	data.email_id = email
	data.message = message
	data.save(ignore_permissions=True)
	
	frappe.db.commit()


def _verify_turnstile(token: str | None) -> None:
	if not token:
		frappe.throw("Please complete the security check.", frappe.PermissionError)

	secret = frappe.conf.get("turnstile_secret_key")
	if not secret:
		frappe.logger("finbyzweb").error("Turnstile secret key is not configured")
		frappe.throw("Security check is unavailable. Please try again later.", frappe.PermissionError)

	payload = {"secret": secret, "response": token}
	if remote_ip := getattr(frappe.local, "request_ip", None):
		payload["remoteip"] = remote_ip

	try:
		response = requests.post(
			TURNSTILE_SITEVERIFY_URL,
			data=payload,
			timeout=TURNSTILE_TIMEOUT_SECONDS,
		)
		response.raise_for_status()
		verification = response.json()
	except (requests.RequestException, ValueError):
		frappe.logger("finbyzweb").exception("Turnstile verification request failed")
		frappe.throw("Security check is unavailable. Please try again later.", frappe.PermissionError)

	if not isinstance(verification, dict) or not verification.get("success"):
		error_codes = verification.get("error-codes", []) if isinstance(verification, dict) else []
		frappe.logger("finbyzweb").warning("Turnstile verification failed: %s", error_codes)
		frappe.throw("Security check failed. Please try again.", frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def related_link_query(doctype, txt, searchfield, start, page_len, filters):
	cond = ""
	args = {

	}
	meta = frappe.get_meta(filters.get("reference_doctype"))
	if meta.get_field('published'):
		return frappe.db.sql("""select name
				from `tab{ref_doc}` where published = 1 and `{key}` LIKE %(txt)s {cond}
			"""
			.format(ref_doc=filters.get("reference_doctype"), key=searchfield, cond=cond), {
				'txt': '%' + txt + '%',
			})
	else:
		return frappe.db.sql("""select name
				from `tab{ref_doc}` where `{key}` LIKE %(txt)s {cond}
			"""
			.format(ref_doc=filters.get("reference_doctype"), key=searchfield, cond=cond), {
				'txt': '%' + txt + '%',
			})
	
def add_preload_headers(response):
	pass

@frappe.whitelist(allow_guest=True)
def select_category(gallery_category=None,gallery_sub_category=None):
	condition = ""
	if str(gallery_category) != "All":
		condition += f"where gallery_category ='{gallery_category}'"
	if gallery_sub_category:
		condition += f"and gallery_sub_category ='{gallery_sub_category}'"
	result = frappe.db.sql(f"""select * from `tabGallery` {condition}""", as_dict = 1)

	output = ""
	for row in result:
		doc_dict = {'doc' :row}
		output += frappe.render_template("finbyzweb/doctype/gallery/templates/gallery_row.html", doc_dict)
	return output

@frappe.whitelist(allow_guest=True)
def get_sub_category(category=None):
	output = frappe.db.get_all('Gallery Sub Category',filters={'category':category},fields=['name','category'])
	return output


@frappe.whitelist(allow_guest=True)
def get_employee_joining_detail(token):
	if not frappe.db.exists("Employee Joining Detail", {"token": token}):
		frappe.throw(_("You are not authorized to view this record!"))
		return
	joining_detail = frappe.get_doc("Employee Joining Detail", {"token": token})
	return joining_detail.as_dict()

from frappe import _
@frappe.whitelist(allow_guest=True,methods=['POST'])
def update_employee_joining_detail(email,data):
	"""
	ENDPOINT: /api/method/finbyzweb.api.update_employee_joining_detail
	"""
	data = frappe.parse_json(data)
	if not frappe.db.exists("Employee Joining Detail", {"personal_email": email}):
		frappe.throw(_("You are not authorized to update this record!"))
		return
	joining_detail = frappe.get_doc("Employee Joining Detail", {"personal_email": email})
	joining_detail.update(data)
	joining_detail.flags.ignore_permissions = True
	joining_detail.save()
	return _("Updated successfully!")