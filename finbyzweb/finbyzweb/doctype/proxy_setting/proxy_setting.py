# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProxySetting(Document):
    def validate(self):
        existing_keys = frappe.cache().get_keys("proxy_setting_*")
        
        current_combinations = set()
        
        for item in self.items:
            if item.for_employee and (not item.proxy_employee or not item.project):
                frappe.throw("Enter value in all child table fields.")
            
            cache_key = f"proxy_setting_{item.proxy_employee}_{item.project}"
            cache_value = f"{item.for_employee} {item.proxy_employee} {item.project}"
            frappe.cache().set_value(cache_key, cache_value)
            current_combinations.add(cache_key)
        
        for key in existing_keys:
            if key not in current_combinations:
                frappe.cache().delete_key(key)

def update_proxy_setting_cache():
    """
    Background job to update and maintain proxy setting cache
    """
    try:
        # Directly fetch the single Proxy Setting document
        doc = frappe.get_single("Proxy Setting")
        
        # Reload the document to get the latest data
        doc.reload()
        
        # Run the validation method to update cache
        doc.validate()
        
        frappe.logger().info("Proxy Setting cache update completed successfully")
    except Exception as e:
        # Log any errors that occur during cache update
        frappe.logger().error(f"Error updating Proxy Setting cache: {str(e)}")

@frappe.whitelist()
def clear_proxy_settings():
    try:
        doc = frappe.get_single("Proxy Setting")
        doc.set('items', [])
        doc.save(ignore_permissions=True)
        
        cache_keys = frappe.cache().get_keys("proxy_setting_*")
        for key in cache_keys:
            frappe.cache().delete_key(key)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Clear Proxy Settings Error")
