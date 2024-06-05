import frappe
from frappe.www.list import get_list
from frappe.utils.user import is_website_user


def get_issue_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by=None):

	user = frappe.session.user
	contact = frappe.db.get_value("Contact", {"user": user}, "name")
	customer = None

	if contact:
		contact_doc = frappe.get_doc("Contact", contact)
		customer = contact_doc.get_link_for("Customer")

	ignore_permissions = False
	if is_website_user():
		if not filters:
			filters = {}
		
		customer_list = frappe.db.get_all("Portal User", filters={"user": user}, pluck="parent")
		filters["customer"] = ['IN', customer_list]

		ignore_permissions = True

	return get_list(
		doctype, txt, filters, limit_start, limit_page_length, ignore_permissions=ignore_permissions
	)

