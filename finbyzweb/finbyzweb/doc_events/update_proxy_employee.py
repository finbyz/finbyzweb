import frappe

# Proxy employees are set within minutes of a record arriving, so only recent rows can still
# need one; filtering on creation lets the creation index replace a scan of the whole table.
RECENT_DAYS = 3


def update_proxy_employee():
    doctype_list = ["Application Usage log", "Screen Screenshot Log", "Work Intensity"]
    
    for doctype in doctype_list:
        # Get all distinct employee-project combinations that need updates
        combinations = frappe.db.sql(f"""
            SELECT DISTINCT employee, project 
            FROM `tab{doctype}`
            WHERE creation >= NOW() - INTERVAL %s DAY
                AND (proxy_employee IS NULL OR proxy_employee = '')
        """, (RECENT_DAYS,), as_dict=True)
        
        # Process each combination individually
        for combo in combinations:
            employee = combo['employee']
            project = combo['project']
            
            # Get the cache value
            cache_key = f"proxy_setting_{employee}_{project}"
            cached_value = frappe.cache().get_value(cache_key)
            if cached_value:
                parts = cached_value.split()
                if len(parts) >= 3:
                    for_employee = parts[0]
                    proxy_employee = parts[1]
                    project_value = ' '.join(parts[2:])
                    
                    # Update records where employee = proxy_employee and project = project_value
                    frappe.db.sql(f"""
                        UPDATE `tab{doctype}`
                        SET proxy_employee = %s
                        WHERE employee = %s AND project = %s
                        AND creation >= NOW() - INTERVAL %s DAY
                        AND (proxy_employee IS NULL OR proxy_employee = '')
                    """, (proxy_employee, for_employee, project_value, RECENT_DAYS))
        
        # For any remaining records, set proxy_employee = employee
        frappe.db.sql(f"""
            UPDATE `tab{doctype}`
            SET proxy_employee = employee
            WHERE creation >= NOW() - INTERVAL %s DAY
                AND (proxy_employee IS NULL OR proxy_employee = '')
        """, (RECENT_DAYS,))
        