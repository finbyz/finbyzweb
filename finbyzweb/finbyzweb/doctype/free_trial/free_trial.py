# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import string
import random

class FreeTrial(Document):
	def validate(self):
		self.random_promo_code()
		
	def random_promo_code(self): 
		N = 5
		res = ''.join(random.choices(string.ascii_uppercase +
									string.digits, k=N))
		self.promo_code = res
			

			