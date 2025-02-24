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
    if not project:
        frappe.throw(_("Please select a project"))

    portal_users = frappe.db.sql(f"""select pu.user from `tabProject` as p join `tabPortal User` as pu on p.customer = pu.parent where p.name = '{project}'""", as_dict=1)
    if frappe.session.user not in [user['user'] for user in portal_users]:
        raise frappe.PermissionError
    else:
        work_intensity_data = work_intensity(user, start_date, end_date, project)
        application_usage_data = application_usage_time(user, start_date, end_date, project)
        web_browsing_data = web_browsing_time(user, start_date, end_date, project)
        url_data = fetch_url_data(user, start_date, end_date, project)
        task_list = get_project_status_data(user, start_date, end_date, project)
        return {
            "work_intensity": work_intensity_data,
            "application_usage": application_usage_data,
            "web_browsing": web_browsing_data,
            "url_data": url_data,
            "task_list": task_list
        }
    

def work_intensity(user=None, start_date=None, end_date=None, project=None):
    if not project:
        return []
    condition = ""
    if user:
        condition += "and proxy_employee = '{0}' ".format(user)
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
        WHERE project = '{project}'
            {condition}
            and time >= '{start_date} 00:00:00'      
            AND time <= '{end_date} 23:59:59' 
            AND HOUR(time) BETWEEN 7 AND 23
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
    if project:
        condition += "and project = '{0}' ".format(project)
    if user:
        condition += "and proxy_employee = '{0}' ".format(user)
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
    if project:
        condition += "and project = '{0}' ".format(project)
    if user:
        condition += "and proxy_employee = '{0}' ".format(user)
    domain_data = frappe.db.sql(f"""
        SELECT domain, round(SUM(duration)/3600,2) as total_duration
        FROM `tabApplication Usage log`
        Where date >= '{start_date}' and date <= '{end_date}' {condition} and domain != '' and domain is not null 
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
    # parsed_datetime = datetime.strptime(start_date, '%d/%m/%Y, %I:%M:%S %p')
    # start_date = parsed_datetime.strftime('%Y-%m-%d  %H:%M:%S')
    # parsed_datetime_ = datetime.strptime(end_date, '%d/%m/%Y, %I:%M:%S %p')
    # end_date = parsed_datetime_.strftime('%Y-%m-%d  %H:%M:%S')
    if not project:
        return []
    portal_users = frappe.db.sql(f"""select pu.user from `tabProject` as p join `tabPortal User` as pu on p.customer = pu.parent where p.name = '{project}'""", as_dict=1)
    if frappe.session.user not in [user['user'] for user in portal_users]:
        raise frappe.PermissionError
    else:
        data = frappe.get_all("Screen Screenshot Log", filters={ "project":project, "proxy_employee":user,"time": ["BETWEEN", [start_date, end_date]]}, order_by="time desc", group_by="time", fields=["screenshot", "time","active_app"])
        for i in data:
            i["time_"] = frappe.format(i["time"], "Datetime")
        return data
# User Activity Images Code Ends

@frappe.whitelist()
def last_screenshot_time(user=None, start_date=None, end_date=None, project=None):
    # parsed_start_date = datetime.strptime(start_date, '%d/%m/%Y, %I:%M:%S %p')
    # start_date = parsed_start_date.strftime('%Y-%m-%d %H:%M:%S')
    # parsed_end_date = datetime.strptime(end_date, '%d/%m/%Y, %I:%M:%S %p')
    # end_date = parsed_end_date.strftime('%Y-%m-%d %H:%M:%S')
    
    if not project:
        return None
    
    portal_users = frappe.db.sql(f"""select pu.user from `tabProject` as p join `tabPortal User` as pu on p.customer = pu.parent where p.name = '{project}'""", as_dict=1)
    if frappe.session.user not in [user['user'] for user in portal_users]:
        raise frappe.PermissionError
    else:
        last_screenshot = frappe.db.sql("""
            SELECT time 
            FROM `tabScreen Screenshot Log` 
            WHERE project = %s AND proxy_employee = %s AND time BETWEEN %s AND %s
            ORDER BY time DESC 
            LIMIT 1
        """, (project, user, start_date, end_date), as_dict=1)
        return last_screenshot[0]['time'] if last_screenshot else None


def fetch_url_data(user=None, start_date=None, end_date=None, project=None):
    if not project:
        return []
        
    # Get customer once and cache it
    customer = frappe.db.get_value("Project", project, "customer")
    
    # Build base conditions using list for better performance
    base_conditions = []
    if user:
        base_conditions.append(f"a.proxy_employee = '{user}'")
    if project:
        base_conditions.append(f"a.project = '{project}'")
    
    # Join conditions efficiently
    app_condition = " AND ".join(base_conditions) if base_conditions else ""
    app_condition = f"AND {app_condition}" if app_condition else ""

    # Optimize application query with proper date indexing
    application_intervals = frappe.db.sql(f"""
        SELECT 
            e.employee_name AS employee, 
            a.proxy_employee AS employee_id,
            a.from_time as start_time,
            a.to_time as end_time
        FROM `tabApplication Usage log` a
        JOIN `tabEmployee` e ON e.name = a.proxy_employee
        WHERE a.date BETWEEN '{start_date}' AND '{end_date}'
        {app_condition}
    """, as_dict=True)

    # Optimize meeting query
    meeting_intervals = frappe.db.sql(f"""
        SELECT 
            mcr.employee AS employee_id,
            e.employee_name AS employee,
            m.meeting_from as start_time,
            m.meeting_to as end_time
        FROM `tabMeeting` m
        JOIN `tabMeeting Company Representative` mcr ON mcr.parent = m.name
        JOIN `tabEmployee` e ON e.name = mcr.employee
        WHERE m.meeting_from >= '{start_date} 00:00:00'
        AND m.meeting_to <= '{end_date} 23:59:59'
        AND m.docstatus = 1 
        AND m.project = '{project}'
        {f"AND mcr.employee = '{user}'" if user else ""}
    """, as_dict=True)

    # Optimize calls query - Now always fetch calls data
    calls_query = f"""
        SELECT 
            employee AS employee_id,
            employee_name AS employee,
            call_datetime as start_time,
            ADDTIME(call_datetime, SEC_TO_TIME(duration)) as end_time
        FROM `tabEmployee Fincall`
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        AND link_name = '{customer}'
        AND calltype NOT IN ('Missed', 'Rejected')
    """
    
    if user:
        calls_query += f" AND employee = '{user}'"
    
    calls_intervals = frappe.db.sql(calls_query, as_dict=True)

    # Process data using dictionary for O(1) lookups
    employee_data = {}
    
    # Optimize datetime conversion
    datetime_cache = {}
    def cached_datetime(time_str):
        if time_str not in datetime_cache:
            datetime_cache[time_str] = frappe.utils.get_datetime(time_str)
        return datetime_cache[time_str]

    def get_duration(start_time, end_time):
        if isinstance(start_time, str):
            start_time = cached_datetime(start_time)
        if isinstance(end_time, str):
            end_time = cached_datetime(end_time)
        return (end_time - start_time).total_seconds()

    # Initialize employee_data dictionary with all employees from all sources
    for interval_list in [application_intervals, meeting_intervals, calls_intervals]:
        for interval in interval_list:
            emp_id = interval['employee_id']
            if emp_id not in employee_data:
                employee_data[emp_id] = {
                    'employee': interval['employee'],
                    'intervals': [],
                    'durations': {
                        'app': 0,
                        'meeting': 0,
                        'call': 0
                    }
                }

    # Process intervals in a single pass
    for interval_type, intervals in [
        ('app', application_intervals),
        ('meeting', meeting_intervals),
        ('call', calls_intervals)
    ]:
        for interval in intervals:
            emp_id = interval['employee_id']
            # Calculate duration once
            duration = get_duration(interval['start_time'], interval['end_time'])
            employee_data[emp_id]['durations'][interval_type] += duration
            employee_data[emp_id]['intervals'].append(interval)

    # Process final results
    result_data = []
    for emp_id, emp_data in employee_data.items():
        intervals = emp_data['intervals']
        
        # Sort and merge intervals only once per employee
        sorted_intervals = sorted(intervals, 
                                key=lambda x: cached_datetime(x['start_time']))
        
        total_duration = 0
        current_end = None
        
        for interval in sorted_intervals:
            start_time = cached_datetime(interval['start_time'])
            end_time = cached_datetime(interval['end_time'])
            
            if current_end is None or start_time > current_end:
                total_duration += (end_time - start_time).total_seconds()
            else:
                if end_time > current_end:
                    total_duration += (end_time - current_end).total_seconds()
            
            current_end = max(end_time, current_end) if current_end else end_time

        result_data.append({
            'employee': emp_data['employee'],
            'employee_id': emp_id,
            'total_duration': round(total_duration, 2),
            'application_duration': round(emp_data['durations']['app'], 2),
            'meeting_duration': round(emp_data['durations']['meeting'], 2),
            'call_duration': round(emp_data['durations']['call'], 2)
        })

    return {
        "data": sorted(result_data, key=lambda x: x['total_duration'], reverse=True)
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
    
    portal_users = frappe.db.sql(f"""select pu.user from `tabProject` as p join `tabPortal User` as pu on p.customer = pu.parent where p.name = '{project}'""", as_dict=1)
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
        AND project = '{project}'
        AND proxy_employee = '{employee}' 
        AND application_name != '' 
        AND application_name IS NOT NULL 
        AND HOUR(from_time) = {hour}
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


def get_project_status_data(user=None, start_date=None, end_date=None, project=None):
    if not project:
        return []
    
    conditions = []
    query_params = {}

    if project:
        conditions.append("t.project = %(project)s")
        query_params['project'] = project

    # Base condition for task statuses
    status_condition = """
        (
            (t.status NOT IN ('Completed', 'Cancelled', 'In-Progress', 'Pending Review') AND (t.exp_start_date IS NOT NULL))
            OR (t.status = 'In-Progress' AND (t.exp_start_date IS NOT NULL))
            OR (t.status = 'Pending Review' AND (t.exp_start_date IS NOT NULL))
            OR (t.status = 'Completed' AND (t.completed_on IS NOT NULL))
        )
    """
    conditions.append(status_condition)

    # Date range conditions
    if start_date and end_date:
        conditions.append("""
            (
                (t.status != 'Completed') OR
                (t.status = 'Completed' AND t.completed_on BETWEEN %(start_date)s AND %(end_date)s)
            )
        """)
        query_params['start_date'] = start_date
        query_params['end_date'] = end_date
    elif start_date:
        conditions.append("""
            (
                (t.status != 'Completed') OR
                (t.status = 'Completed' AND t.completed_on >= %(start_date)s)
            )
        """)
        query_params['start_date'] = start_date
    elif end_date:
        conditions.append("""
            (
                (t.status != 'Completed') OR
                ((t.status = 'Completed' AND t.completed_on <= %(end_date)s) OR 
                 (t.status = 'Completed' AND t.completed_on >= %(end_date)s))
            )
        """)
        query_params['end_date'] = end_date

    query = """
    SELECT 
        t.name,
        t.subject,
        CASE 
            WHEN t.status NOT IN ('Completed', 'Cancelled', 'In-Progress', 'Pending Review') THEN 'Open'
            ELSE t.status
        END as status,
        t.exp_start_date,
        t.exp_end_date,
        t.completed_on,
        t.task_owner,
        u.full_name
    FROM 
        `tabTask` as t
    JOIN 
        `tabUser` as u on u.name = t.assignee
    WHERE 
        {conditions}
    ORDER BY 
        t.status, t.completed_on DESC, t.exp_start_date DESC
    """.format(conditions=' AND '.join(conditions))

    tasks = frappe.db.sql(query, query_params, as_dict=True)

    # Group tasks by status
    grouped_tasks = {
        'Open': [],
        'In-Progress': [],
        'Pending Review': [],
        'Completed': []
    }

    # Distribute tasks to appropriate groups
    for task in tasks:
        status = task['status']
        if status in grouped_tasks:
            grouped_tasks[status].append(task)

    return grouped_tasks

@frappe.whitelist()
def get_project_details(project_name):
    """
    Fetch project details for a given project name using a query.
    """
    try:
        project_data = frappe.db.sql("""
            SELECT show_task 
            FROM `tabProject` 
            WHERE name = %s
        """, (project_name,), as_dict=True) 
        return {
            "show_task": project_data[0]["show_task"],
            "statuses": ["Open", "In-Progress", "Pending Review", "Completed"]
        }
    except Exception as e:
        frappe.throw(str(e))
