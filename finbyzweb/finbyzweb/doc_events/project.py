import frappe

def after_insert(self, method):
    if self.customer:
        customer = frappe.get_doc("Customer", self.customer)
        for user in customer.portal_users:
            # Skip if user permission already exists
            if frappe.db.exists("User Permission", 
                {"user": user.user, "allow": "Project", "for_value": self.name}):
                continue
                
            # Check if user is system user
            user_doc = frappe.get_doc("User", user.user)
            if user_doc.user_type == "System User":
                continue
                
            # Create permission for non-system users
            doc = frappe.new_doc("User Permission")
            doc.user = user.user
            doc.allow = "Project"
            doc.for_value = self.name
            doc.apply_to_all_doctypes = 1
            doc.insert(ignore_permissions=True)