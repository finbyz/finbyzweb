import frappe
from frappe import _
from datetime import datetime, timedelta
from frappe.utils import getdate, get_first_day, get_last_day, add_days


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    columns = []
    
    # Date column if showing daily data
    if filters.get("show_daily_data"):
        columns.append({
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        })
    
    # Employee column if showing employee data
    if filters.get("show_employee"):
        columns.append({
            "fieldname": "employee_name",
            "label": _("Employee"),
            "fieldtype": "Data",
            "width": 150
        })
    
    columns.extend([
        {
            "fieldname": "project",
            "label": _("Project"),
            "fieldtype": "Link",
            "options": "Project",
            "width": 150
        },
        {
            "fieldname": "total_hours",
            "label": _("Total Hours"),
            "fieldtype": "Float",
            "width": 100
        }
    ])
    
    # Add additional columns for detailed breakdown if needed
    if filters.get("show_details"):
        columns.extend([
            {
                "fieldname": "application_hours",
                "label": _("Application Hours"),
                "fieldtype": "Float",
                "width": 100
            },
            {
                "fieldname": "meeting_hours",
                "label": _("Meeting Hours"),
                "fieldtype": "Float",
                "width": 100
            },
            {
                "fieldname": "call_hours",
                "label": _("Call Hours"),
                "fieldtype": "Float",
                "width": 100
            }
        ])
    
    return columns


def get_data(filters):
    # Build date conditions
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    project = filters.get("project")
    employee = filters.get("employee")
    
    # Helper function to calculate duration in seconds
    def get_duration(start_time, end_time):
        if isinstance(start_time, str):
            start_time = frappe.utils.get_datetime(start_time)
        if isinstance(end_time, str):
            end_time = frappe.utils.get_datetime(end_time)
        return (end_time - start_time).total_seconds()

    # Helper function to merge overlapping intervals
    def merge_intervals(intervals):
        if not intervals:
            return []
            
        # Sort intervals by start time
        sorted_intervals = sorted(intervals, key=lambda x: frappe.utils.get_datetime(x['start_time']))
        merged = []
        current = sorted_intervals[0].copy()
        
        for interval in sorted_intervals[1:]:
            current_end = frappe.utils.get_datetime(current['end_time'])
            next_start = frappe.utils.get_datetime(interval['start_time'])
            
            if next_start <= current_end:  # Overlapping intervals
                # Take the later end time
                current['end_time'] = max(
                    current['end_time'],
                    interval['end_time'],
                    key=lambda x: frappe.utils.get_datetime(x)
                )
            else:
                merged.append(current)
                current = interval.copy()
                
        merged.append(current)
        return merged

    # Helper function to get the date from datetime
    def get_date_from_datetime(dt_str):
        if isinstance(dt_str, str):
            dt = frappe.utils.get_datetime(dt_str)
        else:
            dt = dt_str
        return dt.date()

    # Build internal project condition
    internal_project_condition = ""
    if filters.get("is_internal_project"):
        internal_project_condition = f" AND c.is_internal_customer= 1"
    else:
        internal_project_condition = f" AND c.is_internal_customer= 0"

    # Build conditions
    app_condition = ""
    meeting_condition = ""
    call_condition = ""
    
    if project:
        app_condition += f" AND a.project = '{project}'"
        meeting_condition += f" AND m.project = '{project}'"
    
    if employee:
        app_condition += f" AND a.employee = '{employee}'"
        meeting_condition += f" AND mcr.employee = '{employee}'"
        call_condition += f" AND employee = '{employee}'"
        
    if filters.get("resource_based_project"):
        app_condition += " AND p.resource_based_project = 1"
    else:
        app_condition += " AND p.resource_based_project = 0"
        
    if filters.get("hourly_based_project"):
        app_condition += " AND p.based_on_hourly_package = 1"
    else:
        app_condition += " AND p.based_on_hourly_package = 0"

    # Add internal project condition to app and meeting queries
    if internal_project_condition:
        app_condition += f""" AND EXISTS (
            SELECT 1 FROM `tabProject` p_inner
            JOIN `tabCustomer` c ON c.name = p_inner.customer
            WHERE p_inner.name = a.project {internal_project_condition}
        )"""
        
        meeting_condition += f""" AND EXISTS (
            SELECT 1 FROM `tabProject` p_inner
            JOIN `tabCustomer` c ON c.name = p_inner.customer
            WHERE p_inner.name = m.project {internal_project_condition}
        )"""

    # Application intervals query
    application_intervals = frappe.db.sql(f"""
        SELECT 
            e.employee_name AS employee_name, 
            a.employee AS employee_id,
            a.project,
            a.from_time as start_time,
            a.to_time as end_time,
            DATE(a.from_time) as date,
            'application' as activity_type
        FROM `tabApplication Usage log` as a
        JOIN `tabEmployee` as e ON e.name = a.employee
        JOIN `tabProject` as p ON p.name = a.project
        WHERE a.date >= '{from_date}' 
        AND a.date <= '{to_date}'
        {app_condition}
    """, as_dict=True)

    # Meeting intervals query
    meeting_intervals = frappe.db.sql(f"""
        SELECT 
            mcr.employee AS employee_id,
            e.employee_name AS employee_name,
            m.project,
            m.meeting_from as start_time,
            m.meeting_to as end_time,
            DATE(m.meeting_from) as date,
            'meeting' as activity_type
        FROM `tabMeeting` AS m
        JOIN `tabMeeting Company Representative` AS mcr ON mcr.parent = m.name
        LEFT JOIN `tabEmployee` e ON e.name = mcr.employee
        WHERE m.meeting_from >= '{from_date} 00:00:00' 
        AND m.meeting_to <= '{to_date} 23:59:59' 
        AND m.docstatus = 1
        {meeting_condition}
    """, as_dict=True)

    # Get customer from project for call filtering
    customer = None
    if project:
        customer_result = frappe.db.sql(f"""SELECT customer FROM `tabProject` WHERE name = '{project}'""", as_dict=True)
        if customer_result and customer_result[0]['customer']:
            customer = customer_result[0]['customer']
    
    # Add customer filter to call condition if available
    call_condition_final = call_condition
    if customer:
        call_condition_final += f" AND link_name = '{customer}'"
    
    # Add internal customer condition to calls
    if internal_project_condition:
        call_condition_final += f""" AND EXISTS (
            SELECT 1 FROM `tabCustomer` c
            WHERE c.name = link_name {internal_project_condition}
        )"""
        
    # Calls intervals query - always fetch call data
    calls_intervals = frappe.db.sql(f"""
        SELECT 
            employee AS employee_id,
            employee_name,
            Null as project,
            call_datetime as start_time,
            ADDTIME(call_datetime, SEC_TO_TIME(duration)) as end_time,
            date,
            'call' as activity_type
        FROM `tabEmployee Fincall` 
        WHERE date >= '{from_date}'
        AND date <= '{to_date}'
        AND (calltype != 'Missed' AND calltype != 'Rejected')
        AND link_to = 'Customer'
        {call_condition_final}
    """, as_dict=True)
    
    # Map project to calls based on customer
    for call in calls_intervals:
        if not call.get('project') and call.get('link_name'):
            # Get projects for this customer
            projects = frappe.db.sql("""
                SELECT name FROM `tabProject` 
                WHERE customer = %s
            """, call.get('link_name'), as_dict=True)
            
            if projects:
                # Just use the first project for this customer
                call['project'] = projects[0]['name']

    # Process data based on whether to show employee details, by day, or just by project
    if filters.get("show_daily_data"):
        if filters.get("show_employee"):
            # Group by date, employee, and project
            result_data = process_by_date_employee_project(
                application_intervals, 
                meeting_intervals, 
                calls_intervals, 
                get_duration, 
                merge_intervals,
                from_date,
                to_date
            )
        else:
            # Group by date and project only
            result_data = process_by_date_project(
                application_intervals, 
                meeting_intervals, 
                calls_intervals, 
                get_duration, 
                merge_intervals,
                from_date,
                to_date
            )
    else:
        if filters.get("show_employee"):
            # Original employee-project grouping
            result_data = process_by_employee_and_project(
                application_intervals, 
                meeting_intervals, 
                calls_intervals, 
                get_duration, 
                merge_intervals
            )
        else:
            # Project-only grouping
            result_data = process_by_project_only(
                application_intervals, 
                meeting_intervals, 
                calls_intervals, 
                get_duration, 
                merge_intervals
            )
    
    return result_data


def process_by_employee_and_project(application_intervals, meeting_intervals, calls_intervals, 
                                   get_duration, merge_intervals):
    """Process data grouped by both employee and project"""
    employee_project_data = {}
    
    # Process each record's data
    for intervals, activity_type in [
        (application_intervals, 'app_intervals'), 
        (meeting_intervals, 'meeting_intervals'), 
        (calls_intervals, 'call_intervals')
    ]:
        for interval in intervals:
            emp_id = interval['employee_id']
            project = interval.get('project')
            
            if not project:
                continue
                
            key = (emp_id, project)
            
            if key not in employee_project_data:
                employee_project_data[key] = {
                    'employee_name': interval['employee_name'],
                    'project': project,
                    'all_intervals': [],
                    'app_intervals': [],
                    'meeting_intervals': [],
                    'call_intervals': []
                }
            
            # Store intervals by type
            employee_project_data[key][activity_type].append(interval)
            # Also store in the combined list
            employee_project_data[key]['all_intervals'].append(interval)

    # Process the intervals for each employee-project combination
    result_data = []
    for key, data in employee_project_data.items():
        if not data['all_intervals']:
            continue

        # Merge overlapping intervals for total time calculation
        merged_all_intervals = merge_intervals(data['all_intervals'])
        total_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                            for interval in merged_all_intervals)
        
        # Merge overlapping intervals for each activity type separately
        merged_app_intervals = merge_intervals(data['app_intervals'])
        merged_meeting_intervals = merge_intervals(data['meeting_intervals'])
        merged_call_intervals = merge_intervals(data['call_intervals'])
        
        # Calculate individual activity durations (after merging)
        app_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                          for interval in merged_app_intervals)
        meeting_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                              for interval in merged_meeting_intervals)
        call_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                           for interval in merged_call_intervals)

        # Convert seconds to hours
        total_hours = round(total_duration / 3600, 2)
        application_hours = round(app_duration / 3600, 2)
        meeting_hours = round(meeting_duration / 3600, 2)
        call_hours = round(call_duration / 3600, 2)
        
        # Ensure activity hours don't exceed total hours due to rounding
        sum_activity_hours = application_hours + meeting_hours + call_hours
        if sum_activity_hours > total_hours:
            # Apply proportional adjustment
            if sum_activity_hours > 0:
                factor = total_hours / sum_activity_hours
                application_hours = round(application_hours * factor, 2)
                meeting_hours = round(meeting_hours * factor, 2)
                call_hours = round(call_hours * factor, 2)

        result_data.append({
            'employee_name': data['employee_name'],
            'employee_id': key[0],
            'project': data['project'],
            'total_hours': total_hours,
            'application_hours': application_hours,
            'meeting_hours': meeting_hours,
            'call_hours': call_hours
        })

    # Sort by total hours in descending order
    result_data = sorted(result_data, key=lambda x: x['total_hours'], reverse=True)
    return result_data


def process_by_project_only(application_intervals, meeting_intervals, calls_intervals, 
                           get_duration, merge_intervals):
    """Process data grouped by project only - calculates hours per employee first"""
    # First, use the employee-and-project function to get per-employee data
    employee_project_results = process_by_employee_and_project(
        application_intervals, meeting_intervals, calls_intervals, 
        get_duration, merge_intervals
    )
    
    # Then aggregate by project
    project_totals = {}
    for result in employee_project_results:
        project = result['project']
        
        if project not in project_totals:
            project_totals[project] = {
                'project': project,
                'total_hours': 0,
                'application_hours': 0,
                'meeting_hours': 0,
                'call_hours': 0
            }
        
        # Sum up the hours
        project_totals[project]['total_hours'] += result['total_hours']
        project_totals[project]['application_hours'] += result['application_hours']
        project_totals[project]['meeting_hours'] += result['meeting_hours']
        project_totals[project]['call_hours'] += result['call_hours']
    
    # Convert to list and round the values
    result_data = []
    for project, data in project_totals.items():
        result_data.append({
            'project': data['project'],
            'total_hours': round(data['total_hours'], 2),
            'application_hours': round(data['application_hours'], 2),
            'meeting_hours': round(data['meeting_hours'], 2),
            'call_hours': round(data['call_hours'], 2)
        })
    
    # Sort by total hours in descending order
    result_data = sorted(result_data, key=lambda x: x['total_hours'], reverse=True)
    return result_data

def process_by_date_employee_project(application_intervals, meeting_intervals, calls_intervals, 
                                    get_duration, merge_intervals, from_date, to_date):
    """Process data grouped by date, employee, and project"""
    date_employee_project_data = {}
    
    # Process each record's data
    for intervals, activity_type in [
        (application_intervals, 'app_intervals'), 
        (meeting_intervals, 'meeting_intervals'), 
        (calls_intervals, 'call_intervals')
    ]:
        for interval in intervals:
            emp_id = interval['employee_id']
            project = interval.get('project')
            date_str = interval.get('date')
            
            if not project or not date_str:
                continue
            
            # Convert date to string format if it's a datetime object
            if not isinstance(date_str, str):
                date_str = date_str.strftime('%Y-%m-%d')
                
            key = (date_str, emp_id, project)
            
            if key not in date_employee_project_data:
                date_employee_project_data[key] = {
                    'date': date_str,
                    'employee_name': interval['employee_name'],
                    'employee_id': emp_id,
                    'project': project,
                    'all_intervals': [],
                    'app_intervals': [],
                    'meeting_intervals': [],
                    'call_intervals': []
                }
            
            # Store intervals by type
            date_employee_project_data[key][activity_type].append(interval)
            # Also store in the combined list
            date_employee_project_data[key]['all_intervals'].append(interval)

    # Process the intervals for each date-employee-project combination
    result_data = []
    for key, data in date_employee_project_data.items():
        if not data['all_intervals']:
            continue

        # Merge overlapping intervals for total time calculation
        merged_all_intervals = merge_intervals(data['all_intervals'])
        total_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                            for interval in merged_all_intervals)
        
        # Merge overlapping intervals for each activity type separately
        merged_app_intervals = merge_intervals(data['app_intervals'])
        merged_meeting_intervals = merge_intervals(data['meeting_intervals'])
        merged_call_intervals = merge_intervals(data['call_intervals'])
        
        # Calculate individual activity durations (after merging)
        app_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                          for interval in merged_app_intervals)
        meeting_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                              for interval in merged_meeting_intervals)
        call_duration = sum(get_duration(interval['start_time'], interval['end_time']) 
                           for interval in merged_call_intervals)

        # Convert seconds to hours
        total_hours = round(total_duration / 3600, 2)
        application_hours = round(app_duration / 3600, 2)
        meeting_hours = round(meeting_duration / 3600, 2)
        call_hours = round(call_duration / 3600, 2)
        
        # Ensure activity hours don't exceed total hours due to rounding
        sum_activity_hours = application_hours + meeting_hours + call_hours
        if sum_activity_hours > total_hours:
            # Apply proportional adjustment
            if sum_activity_hours > 0:
                factor = total_hours / sum_activity_hours
                application_hours = round(application_hours * factor, 2)
                meeting_hours = round(meeting_hours * factor, 2)
                call_hours = round(call_hours * factor, 2)

        result_data.append({
            'date': data['date'],
            'employee_name': data['employee_name'],
            'employee_id': data['employee_id'],
            'project': data['project'],
            'total_hours': total_hours,
            'application_hours': application_hours,
            'meeting_hours': meeting_hours,
            'call_hours': call_hours
        })

    # Sort first by date, then by total hours descending
    result_data = sorted(result_data, key=lambda x: (x['date'], -x['total_hours']))
    return result_data

def process_by_date_project(application_intervals, meeting_intervals, calls_intervals, 
                           get_duration, merge_intervals, from_date, to_date):
    """Process data grouped by date and project - calculates by employee first"""
    # First, use date-employee-project function to get per-employee data
    date_employee_project_results = process_by_date_employee_project(
        application_intervals, meeting_intervals, calls_intervals, 
        get_duration, merge_intervals, from_date, to_date
    )
    
    # Then aggregate by date and project
    date_project_totals = {}
    for result in date_employee_project_results:
        date = result['date']
        project = result['project']
        key = (date, project)
        
        if key not in date_project_totals:
            date_project_totals[key] = {
                'date': date,
                'project': project,
                'total_hours': 0,
                'application_hours': 0,
                'meeting_hours': 0,
                'call_hours': 0
            }
        
        # Sum up the hours
        date_project_totals[key]['total_hours'] += result['total_hours']
        date_project_totals[key]['application_hours'] += result['application_hours']
        date_project_totals[key]['meeting_hours'] += result['meeting_hours']
        date_project_totals[key]['call_hours'] += result['call_hours']
    
    # Convert to list and round the values
    result_data = []
    for key, data in date_project_totals.items():
        result_data.append({
            'date': data['date'],
            'project': data['project'],
            'total_hours': round(data['total_hours'], 2),
            'application_hours': round(data['application_hours'], 2),
            'meeting_hours': round(data['meeting_hours'], 2),
            'call_hours': round(data['call_hours'], 2)
        })
    
    # Sort first by date, then by total hours descending
    result_data = sorted(result_data, key=lambda x: (x['date'], -x['total_hours']))
    return result_data