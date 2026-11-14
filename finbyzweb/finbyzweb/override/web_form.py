from  frappe.website.doctype.web_form.web_form import WebForm as _WebForm,get_in_list_view_fields,get_link_options
import frappe
from frappe import _
from frappe.utils import strip_html
from frappe.core.api.file import get_max_file_size


class WebForm(_WebForm):
	def get_comment_list(self,doctype, name):
		comments = frappe.get_all(
			"Comment",
			fields=["name", "creation", "owner", "comment_email", "comment_by", "content"],
			filters=dict(
				reference_doctype=doctype,
				reference_name=name,
				comment_type="Comment",
			),
			or_filters=[["owner", "=", frappe.session.user], ["published", "=", 1]],
		)

		return sorted((comments), key=lambda comment: comment["creation"], reverse=True)
