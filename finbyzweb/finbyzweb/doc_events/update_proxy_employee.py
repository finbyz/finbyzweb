import frappe

def update_proxy_employee():
    doctype_list = ["Application Usage log", "Screen Screenshot Log", "Work Intensity"]
    
    for doctype in doctype_list:
        query = f"""
            SELECT name, employee, project FROM `tab{doctype}`
            WHERE proxy_employee IS NULL OR proxy_employee = ''
        """
        logs = frappe.db.sql(query, as_dict=True)
        
        for log in logs:
            employee = log["employee"]
            project = log["project"]

            cache_key = f"proxy_setting_{employee}_{project}"
            frappe.log_error(f"Checking cache with key: {cache_key}")

            cached_value = frappe.cache().get_value(cache_key)
            
            if cached_value:
                frappe.log_error(f"Cache found for {cache_key}: {cached_value}")
                
                parts = cached_value.split()
                if len(parts) < 3:
                    frappe.log_error(f"Invalid cache format for key {cache_key}: {cached_value}")
                    continue
                
                for_employee = parts[0]
                proxy_employee = parts[1]
                project_value = ' '.join(parts[2:])

                if proxy_employee == employee and project_value == project:
                    frappe.db.sql(f"""
                        UPDATE `tab{doctype}`
                        SET proxy_employee = %s
                        WHERE name = %s
                    """, (for_employee, log["name"]))

                if employee == for_employee and project == project_value:
                    frappe.db.sql(f"""
                        UPDATE `tab{doctype}`
                        SET project = 'Finbyz.tech'
                        WHERE name = %s
                    """, (log["name"]))

            if not frappe.db.get_value(doctype, log["name"], "proxy_employee"):
                frappe.db.sql(f"""
                    UPDATE `tab{doctype}`
                    SET proxy_employee = %s
                    WHERE name = %s
                """, (employee, log["name"]))