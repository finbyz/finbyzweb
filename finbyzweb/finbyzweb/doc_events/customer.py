import frappe
def before_validate(self, method):
    projects = frappe.get_all("Project", filters={"customer": self.name}, fields=["name"])
    for project in projects:
        for user in self.portal_users:
            if not frappe.db.exists("User Permission", {"user": user.user, "allow": "Project", "for_value": project.name}):
                doc = frappe.new_doc("User Permission")
                doc.user = user.user
                doc.allow = "Project"
                doc.for_value = project.name
                doc.apply_to_all_doctypes = 1
                doc.save(ignore_permissions=True)
                frappe.db.commit()