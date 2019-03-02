# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.website.website_generator import WebsiteGenerator

class Gallery(WebsiteGenerator):
	def get_context(self, context):
		context.category = frappe.db.get_value("Gallery Category",
			context.doc.gallery_category, ["category"], as_dict=1)

		context.parents = [{"name": _("Home"), "route":"/"},
			{"name": "Gallery", "route": "/gallery"}]
		return context

def get_list_context(context=None):
	list_context = frappe._dict(
		title = _('Gallery'),
		gallery_category = frappe.get_list("Gallery Category", ignore_permissions=True),
		# gallery_sub_category = frappe.get_doc("Gallery Sub Category", ignore_permissions=True),
		# gallery_sub_category = frappe.db.sql("""
			# select name,category, category_name
			# from `tabGallery Sub Category`
		# """),
		scrub = frappe.scrub
	)

	return list_context
