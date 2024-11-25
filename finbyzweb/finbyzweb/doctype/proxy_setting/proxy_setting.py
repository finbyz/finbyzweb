# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProxySetting(Document):
	def validate(self):
		for item in self.items:
			if item.for_employee and (not item.proxy_employee or not item.project):
				frappe.throw("Enter value in all child table fields.")
