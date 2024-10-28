# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: MIT. See LICENSE

import frappe
import frappe.www.list
from frappe import _
from dateutil.parser import parse
from dateutil.parser import parse
from frappe.utils import format_datetime

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)
    context.show_sidebar = True

@frappe.whitelist()
def get_data(user=None, start_date=None, end_date=None, project=None):
    # frappe.throw(str(user) + " " + str(start_date) + " " + str(end_date) + " " + str(project))
    if not project:
        frappe.throw(_("Please select a project"))

    portal_users = frappe.db.sql(f"""select pu.user from `tabProject` as p join `tabPortal User` as pu on p.customer = pu.parent where p.status = 'Open' and p.name = '{project}'""", as_dict=1)
    if frappe.session.user not in [user['user'] for user in portal_users]:
        raise frappe.PermissionError
    else:
        work_intensity_data = work_intensity(user, start_date, end_date, project)
        application_usage_data = application_usage_time(user, start_date, end_date, project)
        web_browsing_data = web_browsing_time(user, start_date, end_date, project)
        url_data = fetch_url_data(user, start_date, end_date, project)
        return {
            "work_intensity": work_intensity_data,
            "application_usage": application_usage_data,
            "web_browsing": web_browsing_data,
            "url_data": url_data
        }
    

def work_intensity(user=None, start_date=None, end_date=None, project=None):
    if not project:
        return []
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


# Application Usage Time Code Starts
def application_usage_time(user=None, start_date=None, end_date=None, project=None):
    if not project:
        return []
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
# Application Usage Time Code Ends

# Web Browsing Time Code Starts
def web_browsing_time(user=None, start_date=None, end_date=None, project=None):
    if not project:
        return []
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
# Web Browsing Time Code Ends

# User Activity Images Code Starts
@frappe.whitelist()
def user_activity_images(user=None, start_date=None, end_date=None, project=None, offset=0):
    # frappe.throw(str(user) + " " + str(start_date) + " " + str(end_date) + " " + str(project))
    if not project:
        return []
    portal_users = frappe.db.sql(f"""select pu.user from `tabProject` as p join `tabPortal User` as pu on p.customer = pu.parent where p.status = 'Open' and p.name = '{project}'""", as_dict=1)
    if frappe.session.user not in [user['user'] for user in portal_users]:
        raise frappe.PermissionError
    else:
        data = frappe.get_all("Screen Screenshot Log", filters={"time": ["BETWEEN", [parse(start_date, dayfirst=True), parse(end_date, dayfirst=True)]],"employee":user, "project":project}, order_by="time desc", group_by="time", fields=["screenshot", "time","active_app"])
        for i in data:
            i["time_"] = frappe.format(i["time"], "Datetime")
        return data
# User Activity Images Code Ends
def fetch_url_data(user=None, start_date=None, end_date=None, project=None):
    if not project:
        return []
    customer = frappe.db.get_value("Project", project, "customer")
    # Initialize conditions for SQL queries
    condition = ""
    app_condition = ""
    if user:
        condition += "AND mcr.employee = '{0}'".format(user)
        app_condition += "AND employee = '{0}'".format(user)
    if project:
        app_condition += "AND project = '{0}'".format(project)

    # Fetch application usage data
    application_time = frappe.db.sql(f"""
        SELECT 
            employee_name AS employee, 
            employee AS employee_id, 
            SUM(duration) AS total_duration
        FROM `tabApplication Usage log`
        WHERE date >= '{start_date}' 
        AND date <= '{end_date}' 
        {app_condition}
        GROUP BY employee_name, employee
    """, as_dict=True)

    # Fetch meeting time data
    meeting_time = frappe.db.sql(f"""
        SELECT 
            mcr.employee AS employee_id,
            e.employee_name AS employee,
            SUM(TIME_TO_SEC(TIMEDIFF(m.meeting_to, m.meeting_from))) AS total_duration
        FROM `tabMeeting` AS m
        JOIN `tabMeeting Company Representative` AS mcr ON mcr.parent = m.name
        LEFT JOIN `tabEmployee` e ON e.name = mcr.employee
        WHERE m.meeting_from >= '{start_date} 00:00:00' 
        AND m.meeting_to <= '{end_date} 23:59:59' 
        AND m.docstatus = 1 
        {condition} 
        AND m.project = '{project}'
        GROUP BY mcr.employee, e.employee_name
    """, as_dict=True)

    # Fetch calls data
    calls_time = frappe.db.sql(f"""
        SELECT 
            employee AS employee_id,
            employee_name AS employee,
            SUM(duration) AS total_duration
        FROM `tabEmployee Fincall` 
        WHERE date >= '{start_date}'
        AND date <= '{end_date}'
        AND link_name = '{customer}'
        AND employee = '{user}'
        GROUP BY employee, employee_name
    """, as_dict=True)
    
    # Process application usage data
    app_duration = {}
    for row in application_time:
        employee_id = row['employee_id']
        app_duration[employee_id] = {
            'employee': row['employee'],
            'total_duration': float(row['total_duration']),
            'app_duration': float(row['total_duration']),
            'meeting_duration': 0,
            'call_duration': 0
        }

    # Process meeting time data
    for row in meeting_time:
        employee_id = row['employee_id']
        meeting_duration = float(row['total_duration'])
        
        if employee_id in app_duration:
            app_duration[employee_id]['meeting_duration'] = meeting_duration
            app_duration[employee_id]['total_duration'] += meeting_duration
        else:
            app_duration[employee_id] = {
                'employee': row['employee'],
                'total_duration': meeting_duration,
                'app_duration': 0,
                'meeting_duration': meeting_duration,
                'call_duration': 0
            }

    # Process calls data
    for row in calls_time:
        employee_id = row['employee_id']
        call_duration = float(row['total_duration'])
        
        if employee_id in app_duration:
            app_duration[employee_id]['call_duration'] = call_duration
            app_duration[employee_id]['total_duration'] += call_duration
        else:
            app_duration[employee_id] = {
                'employee': row['employee'],
                'total_duration': call_duration,
                'app_duration': 0,
                'meeting_duration': 0,
                'call_duration': call_duration
            }

    # Convert combined results to a list of dictionaries
    data = []
    for emp_id, emp_data in app_duration.items():
        if emp_data['employee']:  # Only include if we have employee name
            data.append({
                'employee': emp_data['employee'],
                'employee_id': emp_id,
                'total_duration': round(emp_data['total_duration'], 2),
                'application_duration': round(emp_data['app_duration'], 2),
                'meeting_duration': round(emp_data['meeting_duration'], 2),
                'call_duration': round(emp_data['call_duration'], 2)
            })

    # Sort data by total duration in descending order
    data = sorted(data, key=lambda x: x['total_duration'], reverse=True)
    # frappe.throw(str(data))
    return {
        "data": data
    }

@frappe.whitelist()
def get_projects():
    current_user = frappe.session.user
    projects = frappe.db.sql(f"""
        SELECT DISTINCT p.name as name, p.project_name 
        from `tabProject` as p 
        join `tabPortal User` as pu on p.customer = pu.parent 
        where pu.user = '{current_user}'
        order by  p.resource_based_project DESC""",as_dict=1)
    return projects
from datetime import datetime, timedelta

@frappe.whitelist()
def overall_performance_timely(employee=None, date=None, hour=None, project=None):
    if not project:
        return {
            "labels": [],
            "values": []
        }
    
    portal_users = frappe.db.sql(f"""select pu.user from `tabProject` as p join `tabPortal User` as pu on p.customer = pu.parent where p.status = 'Open' and p.name = '{project}'""", as_dict=1)
    customer = frappe.db.get_value("Project", project, "customer")
    
    if frappe.session.user not in [user['user'] for user in portal_users]:
        raise frappe.PermissionError
    
    if not employee:
        return {
            "labels": [],
            "values": []
        }

    def split_activity(activity_type, date_val, start, end, *args):
        try:
            # Convert strings to datetime objects if they aren't already
            if isinstance(start, str):
                start_time = datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
            else:
                start_time = start

            if isinstance(end, str):
                end_time = datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
            else:
                end_time = end

            # Create hour boundaries
            hour_start = datetime.combine(start_time.date(), datetime.min.time().replace(hour=int(hour)))
            hour_end = hour_start + timedelta(hours=1)

            # Adjust start and end times to fit within the hour
            if start_time < hour_start:
                start_time = hour_start
            if end_time > hour_end:
                end_time = hour_end

            # Only return if there's actually time spent in this hour
            if start_time < end_time:
                return [
                    activity_type,
                    start_time.date(),
                    start_time,
                    end_time
                ] + list(args)
            return None
        except Exception as e:
            frappe.log_error(f"Error in split_activity: {str(e)}")
            return None

    base_data = []
    
    # Fetch applications
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

    # Fetch calls
    calls = frappe.db.sql(f"""
        SELECT 
            name AS parent, 
            call_datetime AS call_start,
            ADDTIME(call_datetime, SEC_TO_TIME(duration)) AS call_end,
            employee, date, 
            COALESCE(contact, client, customer_no) as caller,
            calltype, link_to, link_name
        FROM `tabEmployee Fincall`
        WHERE date = '{date}' 
        AND employee = '{employee}' 
        AND (
            (HOUR(call_datetime) = {hour}) OR
            (HOUR(call_datetime) < {hour} AND HOUR(ADDTIME(call_datetime, SEC_TO_TIME(duration))) >= {hour})
        )
        AND link_name = '{customer}'
        ORDER BY date
    """, as_dict=True)

    # Process applications
    for app in applications:
        is_browser = app.process_name in [
            "chrome.exe", "firefox.exe", "msedge.exe", "opera.exe",
            "iexplore.exe", "brave.exe", "safari.exe", "vivaldi.exe",
            "chromium.exe", "microsoftedge.exe"
        ]
        
        activity_data = split_activity(
            "Browser" if is_browser else "Application",
            app.get('date'),
            app.get('application_start'),
            app.get('application_end'),
            app.get('application_title', '').split(" - ")[0] if app.get('application_title') else None,
            app.get('url'),
            app.get('project'),
            app.get('issue'),
            app.get('task'),
            app.get('name')
        )
        
        if activity_data:
            base_data.append(activity_data)

    # Process calls
    for call in calls:
        activity_data = split_activity(
            "Call",
            call.get('date'),
            call.get('call_start'),
            call.get('call_end'),
            call.get('caller'),
            call.get('calltype'),
            call.get('link_to'),
            call.get('link_name')
        )
        
        if activity_data:
            base_data.append(activity_data)

    # Sort by start time
    base_data = sorted(base_data, key=lambda x: x[2] if x else datetime.max)
    
    # Get unique dates
    data = list(set(str(item[1]) for item in base_data if item))

    return {
        "base_dimensions": ['Activity', 'Date', 'Start Time', 'End Time'],
        "dimensions": ['Employee', 'Employee Name'],
        "base_data": base_data,
        "data": data
    } 
    