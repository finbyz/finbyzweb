# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class UpdateProxyEmployee(Document):
    def validate(self):
        if not self.project or self.project == "":
            self.project = None
        
        if not self.from_date or not self.to_date:
            frappe.throw("Please select valid from and to times")
        

        from_date = self.from_date
        to_date = self.to_date

        application_usage_log = frappe.qb.DocType("Application Usage log")
        screen_screenshot_log = frappe.qb.DocType("Screen Screenshot Log")
        
        # Update Application Usage log
        update_app_usage = (
            frappe.qb.update(application_usage_log)
            .set(application_usage_log.proxy_employee, self.proxy_employee)
            .where(application_usage_log.date >= from_date)
            .where(application_usage_log.date <= to_date)
            .where(application_usage_log.employee == self.employee)
            .where(application_usage_log.project == self.project)
            .where(application_usage_log.date.between(from_date, to_date))
        )

        # Update Screen Screenshot Log
        update_screen_log = (
            frappe.qb.update(screen_screenshot_log)
            .set(screen_screenshot_log.proxy_employee, self.proxy_employee)
            .where(screen_screenshot_log.employee == self.employee)
            .where(screen_screenshot_log.project == self.project)
            .where(screen_screenshot_log.time.between(from_date + " 00:00:00", to_date + " 23:59:59"))
        )

        # Run the updates
        update_app_usage.run()
        update_screen_log.run()

        self.employee = None
        self.project = None
        self.from_date = None
        self.to_date = None
        self.employee_name = None
        self.proxy_employee = None
        
        frappe.msgprint("Proxy Employee updated successfully")
        # Optionally, you can commit if your changes require it
        # frappe.db.commit()  # Uncomment if necessary