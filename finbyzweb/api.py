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
def set_form_contact_data(lead_name, company_name, mobile_no, title, email,notes):
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
	
@frappe.whitelist(allow_guest=True)
def set_form_data(lead_name, company_name, mobile_no, title, email):
	data = frappe.new_doc("Lead")
	data.lead_name = lead_name
	data.company_name = company_name
	data.mobile_no = mobile_no
	data.source = 'Website'
	data.message = title
	data.email_id = email
	data.save(ignore_permissions=True)
	
	frappe.db.commit()

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