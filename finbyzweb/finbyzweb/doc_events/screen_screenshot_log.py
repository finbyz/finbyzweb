# Add project as finbyz tech where project is empty in screenshot log
import frappe
def before_validate(self, method):
    if not self.project:
        self.project = "Finbyz.tech"