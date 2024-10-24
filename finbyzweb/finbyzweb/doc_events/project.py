import frappe
def before_validate(self, method):
    if self.customer:
        customer = frappe.get_doc("Customer", self.customer)
        for user in customer.portal_users:
            if not frappe.db.exists("User Permission", {"user": user.user, "allow": "Project", "for_value": self.name}):
                doc = frappe.new_doc("User Permission")
                doc.user = user.user
                doc.allow = "Project"
                doc.for_value = self.name
                doc.apply_to_all_doctypes = 1
                doc.save(ignore_permissions=True)
                frappe.db.commit()