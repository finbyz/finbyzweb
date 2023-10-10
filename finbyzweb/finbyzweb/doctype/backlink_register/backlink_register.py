# Copyright (c) 2023, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import get_doc, new_doc

class BacklinkRegister(Document):
	def validate(self):
		self.generating_domain()
		self.live_backlinks_validate()

	def generating_domain(self):
			live_backlinks=self.live_backlinks.split('/')
			exists = frappe.db.exists("Domain Authority", {"domain_name":live_backlinks[0]+"//"+live_backlinks[2]}) 
			if not exists:
					doctype = "Domain Authority"
					new_entry = new_doc(doctype)
					new_entry.domain_authority = self.domiain_authority
					live_backlinks=self.live_backlinks.split('/')
					new_entry.domain_name = live_backlinks[0]+"//"+live_backlinks[2]
					new_entry.insert()
					self.domain=live_backlinks[0]+"//"+live_backlinks[2]
	def live_backlinks_validate(self):
			live_backlinks=self.live_backlinks.split('/')
			domain=live_backlinks[0]+"//"+live_backlinks[2]
			if domain:
				self.domiain_authority = frappe.db.get_value("Domain Authority",domain,'domain_authority') if frappe.db.get_value("Domain Authority",domain,'domain_authority') else None
				self.domain = frappe.db.get_value("Domain Authority",domain,'domain_name') if frappe.db.get_value("Domain Authority",domain,'domain_name') else None
              
@frappe.whitelist()
def live_backlinks_validate(msg):
		try:
			live_backlinks=msg.split('/')
			domain=live_backlinks[0]+"//"+live_backlinks[2]
			exists = frappe.db.exists("Domain Authority", {"domain_name": domain})
			if  exists:
				db_data=frappe.get_doc('Domain Authority', domain)
				return db_data
			else:
				db_data={}
		except Exception as e:
			frappe.throw(str(e))


