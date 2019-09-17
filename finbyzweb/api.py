from __future__ import unicode_literals
import frappe

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

@frappe.whitelist(allow_guest=True)
def set_form_data(lead_name, company_name, mobile_no, title, email):
	data = frappe.new_doc("Lead")
	data.lead_name = lead_name
	data.company_name = company_name
	data.mobile_no = mobile_no
	data.source = 'Website'
	data.notes = title
	data.email_id = email
	data.save(ignore_permissions=True)
	
	frappe.db.commit()