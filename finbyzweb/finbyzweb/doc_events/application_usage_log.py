import frappe
def before_validate(self, method):
    employee = self.employee
    project = self.project

    cache_key = f"proxy_setting_{employee}_{project}"
    cached_value = frappe.cache().get_value(cache_key)
    
    if cached_value:
        parts = cached_value.split()
        for_employee = parts[0]
        proxy_employee = parts[1]
        project_value = ' '.join(parts[2:])
        if proxy_employee == self.employee and project_value == self.project:
            self.proxy_employee = for_employee
        if self.employee == for_employee and self.project == project_value:
            self.project = "Finbyz.tech"
    
    if not self.proxy_employee:
        self.proxy_employee = self.employee