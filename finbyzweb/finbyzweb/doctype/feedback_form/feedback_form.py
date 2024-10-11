# Copyright (c) 2023, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class FeedbackForm(Document):
	def before_validate(self):
		if self.document == "Issue":
			issue_name = self.document_name  
   
			frappe.db.set_value('Issue', issue_name, {
				'rating': self.rating,     
				'feedback': self.feedback  
			})
