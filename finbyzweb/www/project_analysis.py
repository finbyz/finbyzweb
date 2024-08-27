# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import frappe
import frappe.www.list
from frappe import _
from dateutil.parser import parse

no_cache = 1


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

	context.current_user = frappe.get_doc("User", frappe.session.user)
	context.show_sidebar = True
	

# Work Intensity Code Starts
@frappe.whitelist()
def work_intensity(user = None, start_date=None, end_date=None, project=None):
    # if not project:
    #     return []
    condition = ""
    if user:
        condition += "and employee = '{0}' ".format(user)
    if project:
        condition += "and project = '{0}' ".format(project)

    intensity_data = frappe.db.sql(f"""
        SELECT 
            HOUR(time) as hour, 
            DAYNAME(time) as day_of_week,
            SUM(key_strokes) as total_keystrokes, 
            SUM(mouse_clicks) as total_mouse_clicks,
            SUM(mouse_scrolls) as total_mouse_scrolls
        FROM `tabWork Intensity`
        WHERE time >= '{start_date} 00:00:00'      
            AND time <= '{end_date} 23:59:59' 
            AND HOUR(time) BETWEEN 7 AND 23
            {condition}
        GROUP BY hour, day_of_week
    """, as_dict=True)

    # Define the expected days list
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    data = []

    # Fill in the intensity data
    for entry in intensity_data:
        hour = entry['hour']
        keystrokes = entry['total_keystrokes'] or 0
        mouse_clicks = entry['total_mouse_clicks'] or 0
        mouse_scrolls = entry['total_mouse_scrolls'] or 0
        value = keystrokes + mouse_clicks + mouse_scrolls
        # Ensure day_of_week is converted to abbreviated form
        day_of_week = entry['day_of_week'][:3]  # Assuming day_of_week is returned as full name
        data.append([hour, value, day_of_week])

    # Ensure all hours from 7 to 23 are included for each day of the week
    for hour in range(7, 24):
        for day in days:
            if not any(d[0] == hour and d[2] == day for d in data):
                data.append([hour, 0, day])

    # Sort data by day and then hour within each day
    data.sort(key=lambda x: (days.index(x[2]), x[0]))

    return data
# Work Intensity Code Ends
	

# Applications Used Code Starts
@frappe.whitelist()
def application_usage_time(user=None,start_date=None, end_date=None,project=None):
    # if not project:
    #     return []
    condition = ""
    if user:
        condition += "and employee = '{0}' ".format(user)
    if project:
        condition += "and project = '{0}' ".format(project)
    application_name = frappe.db.sql(f"""
        SELECT 
            LEFT(application_name, 25) AS application_name, 
            SUM(duration) AS total_duration
        FROM `tabApplication Usage log`
        WHERE date >= '{start_date}' AND date <= '{end_date}' {condition}
        GROUP BY LEFT(application_name, 25)
        ORDER BY total_duration DESC
        LIMIT 10
    """, as_dict=True)

    data = []
    for app in application_name:
        # Convert total_duration to hours and minutes
        hours = int(app['total_duration'] // 3600)
        minutes = int((app['total_duration'] % 3600) / 60)
        
        # Calculate total value in hours with two decimal places
        value = round(hours + (minutes / 60), 2)
        
        data.append({
            "name": app['application_name'],
            "value": value,
            "hours": hours,
            "minutes": minutes
        })

    return data
# Applications Used Code Ends

# Web Browsing Time code starts
@frappe.whitelist()
def web_browsing_time(user=None,start_date=None,end_date=None, project=None):
    # if not project:
    #     return []
    condition = ""
    if user:
        condition += "and employee = '{0}' ".format(user)
    if project:
        condition += "and project = '{0}' ".format(project)
    domain_data = frappe.db.sql(f"""
        SELECT domain, round(SUM(duration)/3600,2) as total_duration
        FROM `tabApplication Usage log`
        Where date >= '{start_date}' and date <= '{end_date}' and domain != '' and domain is not null {condition}
        GROUP BY domain
        ORDER BY total_duration DESC
        LIMIT 10
    """, as_dict=True)

    data = []

    for app in domain_data:
        data.append({
            "name": app['domain'],
            "value": app['total_duration'],
        })

    
    return data
# Web Browsing Time code ends

# User Activity Images Code Starts
import frappe
from frappe.utils import getdate

# User Activity Images Code Starts
@frappe.whitelist()
def user_activity_images(user=None,start_date=None, end_date=None, project = None, offset=0):
    # if not project:
    #     return []
    data = frappe.get_all("Screen Screenshot Log", filters={"time": ["BETWEEN", [parse(start_date, dayfirst=True), parse(end_date, dayfirst=True)]],"employee":user, "project":project}, order_by="time desc", group_by="time", fields=["screenshot", "time","active_app"])
    for i in data:
        i["time_"] = frappe.format(i["time"], "Datetime")
    return data
# User Activity Images Code Ends
# Conditions to be applied to get data from versions table code starts 
@frappe.whitelist() 
def version_conditions(user,start_date=None, end_date=None):
    if user != "Administrator":
        email = frappe.db.get_value("Employee", user, "company_email")
        condition = f"WHERE modified_by = '{email}' and creation >= '{start_date} 00:00:00' AND creation <= '{end_date} 23:59:59'"
    else:
        condition = f"WHERE creation >= '{start_date} 00:00:00' AND creation <= '{end_date} 23:59:59'"

    return condition
# Conditions to be applied to get data from versions table code ends


@frappe.whitelist()
def fetch_url_data(user=None, start_date=None, end_date=None, project=None):
    # frappe.throw(str(start_date) + " " + str(end_date))
    # if not project:
    #     frappe.throw("Please select a project")
    condition = ""
    app_condition = ""
    if user:
        condition += "AND mcr.employee = '{0}'".format(user)
        app_condition += "AND employee = '{0}'".format(user)
    if project:
        app_condition += "AND project = '{0}'".format(project)

    # Fetch application usage data
    application_time = frappe.db.sql(f"""
        SELECT employee_name AS employee, employee AS employee_id, SUM(duration) AS total_duration
        FROM `tabApplication Usage log`
        WHERE date >= '{start_date}' AND date <= '{end_date}' {app_condition}
        GROUP BY employee_name, employee
    """, as_dict=True)
    # frappe.throw(f"""
    #     SELECT employee_name AS employee, employee AS employee_id, SUM(duration) AS total_duration
    #     FROM `tabApplication Usage log`
    #     WHERE date >= '{start_date}' AND date <= '{end_date}' {app_condition}
    #     GROUP BY employee_name, employee
    # """)
    # frappe.throw(str(application_time))
    # Fetch meeting time data
    meeting_time = frappe.db.sql(f"""
        SELECT mcr.employee AS employee_id, SUM(TIME_TO_SEC(TIMEDIFF(m.meeting_to, m.meeting_from))) AS total_duration
        FROM `tabMeeting` AS m
        JOIN `tabMeeting Company Representative` AS mcr ON mcr.parent = m.name
        WHERE m.meeting_from >= '{start_date} 00:00:00' AND m.meeting_to <= '{end_date} 23:59:59' AND m.docstatus = 1 {condition}
        GROUP BY mcr.employee
    """, as_dict=True)
    
    # Initialize dictionaries to store results
    app_duration = {}
    meet_duration = {}
    
    # Process application usage data
    for row in application_time:
        employee_id = row['employee_id']
        employee_name = row['employee']
        duration = row['total_duration']
        if employee_id in app_duration:
            app_duration[employee_id]['total_duration'] += duration
        else:
            app_duration[employee_id] = {
                'employee': employee_name,
                'total_duration': duration
            }
    
    # Process meeting time data
    for row in meeting_time:
        employee_id = row['employee_id']
        duration = row['total_duration']
        if employee_id in meet_duration:
            meet_duration[employee_id]['total_duration'] += duration
        else:
            meet_duration[employee_id] = {
                'employee': None,  # Placeholder
                'total_duration': duration
            }
    
    # Update meeting durations with employee names from app_duration
    for employee_id in meet_duration:
        if employee_id in app_duration:
            meet_duration[employee_id]['employee'] = app_duration[employee_id]['employee']
    
    # Combine results
    combined_duration = {}
    combined_duration.update(app_duration)
    combined_duration.update(meet_duration)
    
    # Convert combined results to a list of dictionaries
    data = [{'employee': emp_data['employee'], 'employee_id': emp_id, 'total_duration': emp_data['total_duration']}
            for emp_id, emp_data in combined_duration.items() if emp_data['employee'] is not None]
    # frappe.throw(str(data))
    return {"data": data}


@frappe.whitelist()
def get_projects():
    projects = frappe.get_list("Project", fields=["name", "project_name"])
    return projects


# Overall Performance timely Code Starts
@frappe.whitelist()
def overall_performance_timely(employee=None, date=None, hour=None, project=None):
    # if not project:
    #     return {
    #         "labels": [],
    #         "values": []
    #     }
    if not employee:
        return {
            "labels": [],
            "values": []
        }
    applications = frappe.db.sql(f"""
    SELECT 
        application_name AS name, 
        from_time AS application_start, 
        to_time AS application_end, 
        date, 
        LEFT(application_title, 80) AS application_title, 
        LEFT(url, 80) AS url, 
        project, 
        issue, 
        task,
        process_name
    FROM `tabApplication Usage log`
    WHERE date = '{date}' 
      AND employee = '{employee}' 
      AND application_name != '' 
      AND application_name IS NOT NULL 
      AND HOUR(from_time) = {hour}
      AND project = '{project}'
    """, as_dict=True)

    base_data = []
    for app in applications:
        if app.process_name in ["chrome.exe","firefox.exe","msedge.exe","opera.exe","iexplore.exe","brave.exe","safari.exe","vivaldi.exe","chromium.exe","microsoftedge.exe"]:
            base_data.append([
                "Browser",
                app['date'],
                app['application_start'],
                app['application_end'],
                app['application_title'].split(" - ")[0] if app['application_title'] else None,
                app['url'] if app['url'] else None,
                app['project'] if app['project'] else None,
                app['issue'] if app['issue'] else None,
                app['task'] if app['task'] else None,
                app['name']
            ])
        else:
            base_data.append([
                "Application",
                app['date'],
                app['application_start'],
                app['application_end'],
                app['application_title'].split(" - ")[0] if app['application_title'] else None,
                app['url'] if app['url'] else None,
                app['project'] if app['project'] else None,
                app['issue'] if app['issue'] else None,
                app['task'] if app['task'] else None,
                app['name']         
            ])

    base_data = sorted(base_data, key=lambda x: x[2])
    data = list(set([item[1] for item in base_data]))
    # frappe.throw(str(data))
    return{
        "base_dimensions":['Activity', 'Employee', 'Start Time', 'End Time'],
        "dimensions":['Employee', 'Employee Name'],
        "base_data":base_data,
        "data":data
    }
# Overall Performance Timely Code Ends