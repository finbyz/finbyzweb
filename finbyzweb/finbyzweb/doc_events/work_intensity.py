import frappe
def before_validate(self, method):
    if not self.project:
        self.project = "Finbyz.tech"

    proxy_setting = frappe.cache().hget("proxy_setting", "Proxy Setting")
    if not proxy_setting:
        proxy_setting = frappe.get_doc("Proxy Setting", "Proxy Setting")
        frappe.cache().hset("proxy_setting", "Proxy Setting", proxy_setting)
    items = proxy_setting.get("items", [])
    for row in items:
        print(f"For Employee: {row.for_employee}, Proxy Employee: {row.proxy_employee}, Project: {row.project}")
        if row.proxy_employee == self.employee and row.project == self.project:
            self.proxy_employee = row.for_employee
        if self.employee == row.for_employee and self.project == row.project:
            self.project == "Finbyz.tech"
    if not self.proxy_employee:
        self.proxy_employee = self.employee