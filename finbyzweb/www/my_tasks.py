from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr, getdate

def get_context(context):
    if frappe.session.user == "Guest":
        frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

    context.current_user = frappe.get_doc("User", frappe.session.user)
    context.show_sidebar = True

def execute(filters=None):
    data = get_data(filters)
    return data

@frappe.whitelist()
def get_data(filters=None):
    if isinstance(filters, str):
        try:
            # Try to parse if it's a JSON string
            import json
            filters = json.loads(filters)
        except:
            # If parsing fails, create an empty dict
            filters = {}
    # Get projects the user has permission to access
    projects = get_projects(filters)
    tasks = get_tasks(projects, filters)
    
    if not tasks and not projects:
        return []
    
    return prepare_data(projects, tasks)

def get_projects(filters=None):
    # Prepare filter conditions
    filter_conditions = {"name": ["in", frappe.get_all("Project", pluck="name")]}
    
    # Apply additional filters if provided
    if filters:
        # If specific project is requested
        if filters.get("project"):
            filter_conditions["name"] = filters.get("project")
    
    # Get projects the user has permission to access
    return frappe.get_list("Project", 
        fields=["name", "project_name as subject", "status", "priority", 
                "expected_start_date", "expected_end_date", "percent_complete"],
        filters=filter_conditions,
        order_by="name"
    )

def prepare_data(projects, tasks):
    data = []
    project_task_map = {}
    parent_children_map = {}
    
    # Build parent-child relationships map
    for task in tasks:
        project_task_map.setdefault(task.project, []).append(task)
        
        # Handle both direct parent-child and orphaned tasks
        if task.parent_task:
            parent_children_map.setdefault(task.parent_task, []).append(task)
        else:
            # For tasks without parent_task, map them directly under their project
            parent_children_map.setdefault(task.project, []).append(task)

    # First pass - determine which tasks have children
    task_has_children = {}
    for task in tasks:
        # A task has children if it appears as a key in parent_children_map
        task_has_children[task.name] = task.name in parent_children_map
    
    for project in projects:
        project_tasks = project_task_map.get(project.name, [])
        project_progress = calculate_project_progress(project.name)
        project_progress_display = create_progress_display(project_progress)
        
        if project_tasks:
            # Add project header
            project_data = frappe._dict({
                "project_id": project.name,
                "task": cstr(project.subject),
                "progress": project_progress_display,
                "status_show": create_status_display(project.status),
                "status": project.status,
                "expected_time": "",
                "priority": project.priority,
                "description": "",
                "assignee": "",
                "type": "",
                "indent": 0,
                "exp_start_date": project.expected_start_date,
                "exp_end_date": project.expected_end_date,
                "is_group": 1,  # Projects are always groups
                "is_project": 1
            })
            data.append(project_data)
            
            # Process all tasks for this project
            for task in project_tasks:
                # Only process tasks that don't have a parent or whose parent isn't in our task list
                if not task.parent_task or task.parent_task not in {t.name for t in tasks}:
                    add_task_to_data(data, task, parent_children_map, task_has_children, 1, show_progress=True)

    return data

def get_tasks(projects, filters=None):
    project_names = [project.name for project in projects]
    
    # Prepare base filters
    task_filters = {'project': ['in', project_names]}
    
    # Apply additional filters if provided
    if filters:
        # Date range filters for tasks
        if filters.get("start_date"):
            task_filters['exp_start_date'] = ['=', getdate(filters.get("start_date"))]

        task_filters['status'] = ['!=', 'Cancelled']
    # Get all tasks for the projects the user has permission to access
    return frappe.get_all('Task', 
        filters=task_filters,
        fields=['name', 'subject', 'parent_task', 'project', 'status', 'assignee', 
                'priority', 'description', 'exp_start_date', 'exp_end_date', 
                'completed_on', 'expected_time', 'type'],
        order_by='project, parent_task, name'
    )

# The rest of the functions remain unchanged
def add_task_to_data(data, task, parent_children_map, task_has_children, level, show_progress=False):
    # Add the current task
    task_progress = calculate_task_progress(task.name) if show_progress else None
    task_name = '  ' * level + str(task.subject)
    progress_display = create_progress_display(task_progress) if show_progress else ""
    status_display = create_status_display(task.status)
    
    # Set is_group based on whether the task has children
    is_group = 1 if task_has_children.get(task.name, False) else 0

    data.append(frappe._dict({
        "task": task_name,
        "type": task.type,
        "progress": progress_display,
        "assignee": task.assignee,
        "exp_start_date": task.exp_start_date,
        "exp_end_date": task.exp_end_date,
        "status": task.status,
        "status_show": status_display,
        "expected_time": task.expected_time,
        "priority": task.priority,
        "description": task.description,
        "indent": level,
        "is_group": is_group,  # Dynamically set based on children
        "is_project": 0,
        "project": task.project,
        "task_id": task.name,
        "parent_task": task.parent_task,  # Add the parent_task field explicitly
        "completed_on": task.completed_on
    }))

    # Process children if any exist
    children = parent_children_map.get(task.name, [])
    if children:
        # Sort children by name to maintain consistent order
        children.sort(key=lambda x: x.name)
        for child in children:
            add_task_to_data(data, child, parent_children_map, task_has_children, level + 1, show_progress)

def get_progress_color(progress):
    """
    Get the appropriate color based on the progress percentage
    
    Args:
        progress (int): Progress percentage (0-100)
    
    Returns:
        dict: Color styling for the progress indicator
    """
    if progress is None or progress == 0:
        return {
            'color': '#6b7280',  # Neutral gray
            'background-color': '#f3f4f6'
        }
    
    # If progress is less than 100, return orange/red tones
    if progress < 100:
        return {
            'color': '#c53030',  # Dark red
            'background-color': '#fff5f5'  # Light red background
        }
    # If progress is exactly 100, return green
    elif progress == 100:
        return {
            'color': '#286840',  # Dark green
            'background-color': '#eaf5ee'  # Light green background
        }

def get_status_styles(status):
    """Return color mapping for different statuses"""
    colors = {
        "Unplanned": ("#FFF0F0", "#FF0000"),  # Light red bg, red text
        "Overdue": ("#FFF0F0", "#FF4500"),    # Light red bg, orange-red text
        "In-Progress": ("#FFFFF0", "#997A00"), # Light yellow bg, darker yellow text
        "Open": ("#F8F0FF", "#800080"),        # Light purple bg, purple text
        "Pending Review": ("#FFF8F0", "#FFA500"),
        "Working": ("#FFF8F0", "#FFA500"),
        "Completed": ("#F0FFF0", "#008000"),
        "Cancelled": ("#F0F0F0", "#808080"),
        "Change Pending": ("#F0F8FF", "#4169E1"),
        "Scheduled": ("#F0F8FF", "#0000FF"),
        "Planned": ("#FFF0F8", "#FF69B4"),
        "Template": ("#F0F8FF", "#0000FF")
    }
    return colors.get(status, ("#F0F0F0", "#808080"))

def create_status_display(status):
    """
    Create HTML display for status similar to progress_display
    Returns formatted HTML string with appropriate styling
    """
    if not status:
        return ""
    
    bg_color, text_color = get_status_styles(status)
    
    html = f'''
        <div style="
            display: inline-block;
            padding: 2px 8px;
            border-radius: 10px;
            background-color: {bg_color};
            color: {text_color};
            font-size: 12px;
            font-weight: 500;
            white-space: nowrap;
        ">
            {status}
        </div>
    '''
    return html
          
def create_progress_display(progress):
    """
    Create a styled progress display with color
    
    Args:     
        progress (int or None): Progress percentage
    
    Returns:
        str: HTML-formatted progress display with color styling
    """
    if progress is None:
        return ""
    
    # Get color styling
    progress_colors = get_progress_color(progress)
    
    # Create inline style
    progress_style = (
        f"color:{progress_colors['color']};"
        f"background-color:{progress_colors['background-color']};"
        "border-radius:20px;padding:2px 4px;"
    )
    
    # Return styled progress
    return f"<span style='{progress_style}'>{progress}%</span>"
       
def calculate_project_progress(project_name):
    """
    Calculate project progress based on all tasks within the project
    
    Args:
        project_name (str): Name of the project
    
    Returns:
        int: Overall project progress percentage
    """
    # Get all tasks in the project
    project_tasks = frappe.get_all('Task', 
        filters={'project': project_name},
        fields=['name', 'status']
    )
    
    # If no tasks, return None
    if not project_tasks:
        return None
    
    # Count total and completed tasks
    total_tasks = len(project_tasks)
    completed_tasks = sum(1 for task in project_tasks if task.status == 'Completed')
    
    # Calculate and return progress percentage
    return round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
     
def calculate_task_progress(task_name):
    """
    Calculate task progress based on child tasks' completion
    
    Args:
        task_name (str): Name of the task to calculate progress for
    
    Returns:
        int or None: Percentage of completed child tasks, or None if no children
    """
    # Get all child tasks
    child_tasks = frappe.get_all('Task', 
        filters={'parent_task': task_name},
        fields=['name', 'status']
    )
    
    # If no child tasks, return None
    if not child_tasks:
        return None
    
    # Count total and completed child tasks
    total_tasks = len(child_tasks)
    completed_tasks = sum(1 for task in child_tasks if task.status == 'Completed')
    
    # Calculate and return progress percentage
    return round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0