# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class EmployeeFeedback(Document):
	@frappe.whitelist()
	def before_validate(self):
		self.set_employee_name()

	def set_employee_name(self):
		self.employee_code = frappe.db.get_value("Employee", {"user_id": self.user}, "name")
		self.employee_name = frappe.db.get_value("Employee", {"user_id": self.user}, "employee_name")

