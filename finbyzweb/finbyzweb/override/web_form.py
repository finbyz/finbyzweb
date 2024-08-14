from  frappe.website.doctype.web_form.web_form import WebForm as WebForm,get_in_list_view_fields,get_link_options
import frappe
from frappe import _
from frappe.utils import strip_html
from frappe.core.api.file import get_max_file_size


class WebForm(WebForm):
	def load_form_data(self, context):
		context.parents = []
		if self.show_list:
			context.parents.append(
				{
					"label": _(self.title),
					"route": f"{self.route}/list",
				}
			)

		context.parents = self.get_parents(context)

		if self.breadcrumbs:
			context.parents = frappe.safe_eval(self.breadcrumbs, {"_": _})

		if self.show_list and frappe.form_dict.is_new:
			context.title = _("New {0}").format(context.title)

		context.has_header = (frappe.form_dict.name or frappe.form_dict.is_new) and (
			frappe.session.user != "Guest" or not self.login_required
		)

		if context.success_message:
			context.success_message = frappe.db.escape(context.success_message.replace("\n", "<br>")).strip(
				"'"
			)

		if not context.max_attachment_size:
			context.max_attachment_size = get_max_file_size() / 1024 / 1024

		# For Table fields, server-side processing for meta
		for field in context.web_form_doc.web_form_fields:
			if field.fieldtype == "Table":
				field.fields = get_in_list_view_fields(field.options)

			if field.fieldtype == "Link":
				field.fieldtype = "Autocomplete"
				field.options = get_link_options(
					self.name, field.options, field.allow_read_on_all_link_options
				)

		context.reference_doc = {}

		# load reference doc
		if frappe.form_dict.name:
			context.doc_name = frappe.form_dict.name
			context.reference_doc = frappe.get_doc(self.doc_type, context.doc_name)
			context.web_form_title = context.title
			context.title = (
				strip_html(context.reference_doc.get(context.reference_doc.meta.get_title_field()))
				or context.doc_name
			)
			context.reference_doc.add_seen()
			context.reference_doctype = context.reference_doc.doctype
			context.reference_name = context.reference_doc.name

			if self.show_attachments:
				context.attachments = frappe.get_all(
					"File",
					filters={
						"attached_to_name": context.reference_name,
						"attached_to_doctype": context.reference_doctype,
						"is_private": 0,
					},
					fields=["file_name", "file_url", "file_size"],
				)

			if self.allow_comments:
				context.comment_list = self.get_comment_list(
					context.reference_doc.doctype, context.reference_doc.name
				)

			context.reference_doc = context.reference_doc.as_dict(no_nulls=True)
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
