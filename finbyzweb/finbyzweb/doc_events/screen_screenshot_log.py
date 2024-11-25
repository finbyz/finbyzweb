# Add project as finbyz tech where project is empty in screenshot log
import frappe
def before_validate(self, method):
    if not self.project:
        self.project = "Finbyz.tech"

    employee = self.employee
    project = self.project

    cache_key = f"proxy_setting_{employee}_{project}"
    cached_value = frappe.cache().get_value(cache_key)
    
    if cached_value:
        for_employee, proxy_employee, project_value = cached_value.split()
        if proxy_employee == self.employee and project_value == self.project:
            self.proxy_employee = for_employee
        if self.employee == for_employee and self.project == project_value:
            self.project = "Finbyz.tech"
    
    if not self.proxy_employee:
        self.proxy_employee = self.employee
    