import frappe

def update_proxy_employee():
    doctype_list = ["Application Usage log", "Screen Screenshot Log", "Work Intensity"]
    
    for doctype in doctype_list:
        # Get all distinct employee-project combinations that need updates
        combinations = frappe.db.sql(f"""
            SELECT DISTINCT employee, project 
            FROM `tab{doctype}`
            WHERE proxy_employee IS NULL OR proxy_employee = ''
        """, as_dict=True)
        
        # Process each combination individually
        for combo in combinations:
            employee = combo['employee']
            project = combo['project']
            
            # Get the cache value
            cache_key = f"proxy_setting_{employee}_{project}"
            print(cache_key)
            cached_value = frappe.cache().get_value(cache_key)
            print("meghwin"+str(cached_value))
            if cached_value:
                print(cached_value)
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
                        AND (proxy_employee IS NULL OR proxy_employee = '')
                    """, (proxy_employee, for_employee, project_value))
        
        # For any remaining records, set proxy_employee = employee
        frappe.db.sql(f"""
            UPDATE `tab{doctype}`
            SET proxy_employee = employee
            WHERE (proxy_employee IS NULL OR proxy_employee = '')
        """)
        