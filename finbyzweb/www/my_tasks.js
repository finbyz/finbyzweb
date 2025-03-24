// Global state object to manage selections
const state = {
    selected_project: null,
    selected_start_date: null,
    all_expanded: true
};

// Fetch data from the server with filters
async function fetchData() {
    try {
        // Prepare filter parameters
        const filters = {};
        
        // Only add filters that have values
        if (state.selected_project) {
            filters.project = state.selected_project;
        }
        
        if (state.selected_start_date) {
            filters.start_date = state.selected_start_date;
        }
        
        
        // Send filters to server-side function
        const response = await frappe.call({
            method: 'finbyzweb.www.my_tasks.get_data',
            args: {
                filters: filters
            }
        });
        
        
        // If we need to populate project filter, do it here
        if (!state.projects_loaded) {
            populateProjectFilter(response.message);
            state.projects_loaded = true;
        }
        
        // Render the data
        renderTaskTree(response.message);

    } catch (error) {
        console.error('Error fetching data:', error);
        frappe.msgprint({
            title: 'Error',
            indicator: 'red',
            message: `Failed to fetch data: ${error.message || 'Unknown error'}`
        });
    }
}

// Populate project filter dropdown with unique projects
function populateProjectFilter(data) {
    const projectSelect = document.getElementById('project-filter');
    if (!projectSelect) return;
    
    // Clear existing options
    projectSelect.innerHTML = '<option value="">All Projects</option>';
    
    // Get unique projects
    const projects = [...new Set(data
        .filter(item => item.is_project === 1)
        .map(item => ({ id: item.project_id, name: item.task })))];
    
    // Add options
    projects.forEach(project => {
        const option = document.createElement('option');
        option.value = project.id;
        option.textContent = project.name;
        projectSelect.appendChild(option);
    });
}

function renderTaskTree(data) {
    const tableBody = document.querySelector('.task-table tbody');
    tableBody.innerHTML = ''; // Clear existing rows

    if (!data || data.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="9" style="text-align: center;">No tasks found</td>';
        tableBody.appendChild(emptyRow);
        return;
    }

    const taskIdMap = {};
    const projectMap = {};

    // First pass: Build the maps
    data.forEach(item => {
        if (item.is_project === 1) {
            projectMap[item.project_id] = {
                ...item,
                children: []
            };
        } else if (item.task_id) {
            taskIdMap[item.task_id] = {
                ...item,
                children: []
            };
        }
    });

    // Second pass: Build the hierarchy
    data.forEach(item => {
        if (!item.is_project && item.task_id) {
            const task = taskIdMap[item.task_id];

            if (item.parent_task && taskIdMap[item.parent_task]) {
                taskIdMap[item.parent_task].children.push(task);
            } else if (item.project && projectMap[item.project]) {
                projectMap[item.project].children.push(task);
            }
        }
    });

    // Render all projects first
    Object.values(projectMap).forEach(project => {
        renderProjectRow(tableBody, project, 0);
    });

    // Render orphaned tasks (those without a parent or project)
    Object.values(taskIdMap).forEach(task => {
        if ((task.parent_task && taskIdMap[task.parent_task]) ||
            (task.project && projectMap[task.project])) {
            return;
        }

        renderTaskRow(tableBody, task, 0);
    });
    
    // After rendering, attach click handlers explicitly
    attachClickHandlers();
    
    // Set initial expand/collapse state
    updateExpandCollapseState(state.all_expanded);
}

function renderProjectRow(tableBody, project, level) {
    const row = document.createElement('tr');
    row.classList.add('task-row', 'project-row');
    row.dataset.isProject = '1';
    row.dataset.isGroup = '1';
    row.dataset.taskId = project.project_id;
    row.dataset.level = level.toString();

    const hasChildren = project.children && project.children.length > 0;
    let iconClass = hasChildren ? 'fa-chevron-down' : 'fa-circle';
    let iconStyle = hasChildren ? '' : 'font-size: 8px; color: #ccc;';

    const firstCell = document.createElement('td');
    firstCell.className = 'task-name-cell';

    let indentHTML = '';
    for (let i = 0; i < level; i++) {
        indentHTML += `<span class="indent-spacer" style="display: inline-block; width: 20px;"></span>`;
    }

    firstCell.innerHTML = `
        ${indentHTML}
        <span class="icon-container">
            <i class="fa ${iconClass} collapse-icon" style="${iconStyle}" aria-hidden="true"></i>
        </span>
        <span class="task-name">${project.task}</span>
    `;

    row.appendChild(firstCell);

    const cells = [
        project.type || '',
        project.assignee || '',
        project.progress || '',
        project.exp_start_date || '',
        project.exp_end_date || '',
        project.status_show || '',
        project.expected_time || '',
        project.priority || '',
        project.description || ''
    ];

    cells.forEach(cellContent => {
        const cell = document.createElement('td');
        cell.innerHTML = cellContent;
        row.appendChild(cell);
    });

    tableBody.appendChild(row);

    if (hasChildren) {
        project.children.forEach(task => {
            renderTaskRow(tableBody, task, level + 1, project.project_id);
        });
    }
}

function renderTaskRow(tableBody, task, level, parentId) {
    const row = document.createElement('tr');
    row.classList.add('task-row');
    row.dataset.taskId = task.task_id;
    row.dataset.level = level.toString();

    // Set the correct parent ID
    // First check if the task has a parent_task property provided directly from the server
    if (task.parent_task) {
        row.dataset.parent = task.parent_task;
    } 
    // Otherwise, if it was passed a parentId parameter (from a project or a group task), use that
    else if (parentId) {
        row.dataset.parent = parentId;
    }

    const hasChildren = task.children && task.children.length > 0;
    
    if (hasChildren || task.is_group === 1) {
        row.dataset.isGroup = '1';
    }

    let iconClass = (hasChildren || task.is_group === 1) ? 'fa-chevron-down' : 'fa-circle';
    let iconStyle = (hasChildren || task.is_group === 1) ? '' : 'font-size: 8px; color: #ccc;';

    const firstCell = document.createElement('td');
    firstCell.className = 'task-name-cell';

    // Preserve task.indent if available, otherwise use level
    const indentLevel = task.indent !== undefined ? task.indent : level;
    
    let indentHTML = '';
    for (let i = 0; i < indentLevel; i++) {
        indentHTML += `<span class="indent-spacer" style="display: inline-block; width: 20px;"></span>`;
    }

    firstCell.innerHTML = `
        ${indentHTML}
        <span class="icon-container">
            <i class="fa ${iconClass} collapse-icon" style="${iconStyle}" aria-hidden="true"></i>
        </span>
        <span class="task-name">${task.task}</span>
    `;

    row.appendChild(firstCell);

    const cells = [
        task.type || '',
        task.assignee || '',
        task.progress || '',
        task.exp_start_date || '',
        task.exp_end_date || '',
        task.status_show || '',
        task.expected_time || '',
        task.priority || '',
        task.description || ''
    ];

    cells.forEach(cellContent => {
        const cell = document.createElement('td');
        cell.innerHTML = cellContent;
        row.appendChild(cell);
    });

    tableBody.appendChild(row);

    if (hasChildren) {
        task.children.forEach(childTask => {
            renderTaskRow(tableBody, childTask, level + 1, task.task_id);
        });
    }
}

// Improved show/hide functions for child tasks
function showChildTasks(parentId) {
    document.querySelectorAll(`.task-row[data-parent="${parentId}"]`).forEach(row => {
        row.style.display = '';
        
        // Check if this task was expanded before
        const taskId = row.dataset.taskId;
        const icon = row.querySelector('.collapse-icon');
        
        if (icon && icon.classList.contains('fa-chevron-down') && row.dataset.isGroup === '1') {
            showChildTasks(taskId);
        }
    });
}

function hideChildTasks(parentId) {
    document.querySelectorAll(`.task-row[data-parent="${parentId}"]`).forEach(row => {
        row.style.display = 'none';
        
        // Also hide any children of this row
        const taskId = row.dataset.taskId;
        if (taskId) {
            hideChildTasks(taskId);
        }
    });
}

function handleIconClick(iconElement) {
    const row = iconElement.closest('.task-row');
    if (!row) {
        console.error("No parent row found for this icon");
        return;
    }
    
    if (row.dataset.isGroup === '1' || row.dataset.isProject === '1') {
        const taskId = row.dataset.taskId;
        if (!taskId) {
            console.error("No taskId found on this row", row);
            return;
        }
        

        // Debug what we're looking for
        const children = document.querySelectorAll(`.task-row[data-parent="${taskId}"]`);

        // Toggle expand/collapse
        if (iconElement.classList.contains('fa-chevron-down')) {
            // Collapse
            iconElement.classList.remove('fa-chevron-down');
            iconElement.classList.add('fa-chevron-right');
            hideChildTasks(taskId);
        } else {
            // Expand
            iconElement.classList.remove('fa-chevron-right');
            iconElement.classList.add('fa-chevron-down');
            showChildTasks(taskId);
        }
    } else {
        console.log("");
    }
}

// Function to collapse all tasks
function collapseAll() {
    document.querySelectorAll('.task-row[data-is-group="1"], .task-row[data-is-project="1"]').forEach(row => {
        const icon = row.querySelector('.collapse-icon');
        if (icon && icon.classList.contains('fa-chevron-down')) {
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
            const taskId = row.dataset.taskId;
            if (taskId) {
                hideChildTasks(taskId);
            }
        }
    });
    state.all_expanded = false;
    updateCollapseButtonText();
}

// Function to expand all tasks
function expandAll() {
    document.querySelectorAll('.task-row[data-is-group="1"], .task-row[data-is-project="1"]').forEach(row => {
        const icon = row.querySelector('.collapse-icon');
        if (icon && icon.classList.contains('fa-chevron-right')) {
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
            const taskId = row.dataset.taskId;
            if (taskId) {
                showChildTasks(taskId);
            }
        }
    });
    state.all_expanded = true;
    updateCollapseButtonText();
}

// Update expand/collapse state based on all_expanded flag
function updateExpandCollapseState(expand) {
    if (expand) {
        expandAll();
    } else {
        collapseAll();
    }
}

// Update the text of the collapse/expand button
function updateCollapseButtonText() {
    const button = document.getElementById('collapse-expand-btn');
    if (button) {
        button.textContent = state.all_expanded ? 'Collapse All' : 'Show All';
    }
}

// Toggle between collapse all and expand all
function toggleCollapseExpand() {
    if (state.all_expanded) {
        collapseAll();
    } else {
        expandAll();
    }
}

// Function to attach direct click handlers to all icons
function attachClickHandlers() {
    document.querySelectorAll('.collapse-icon').forEach(icon => {
        // Remove any existing event listeners
        const newIcon = icon.cloneNode(true);
        icon.parentNode.replaceChild(newIcon, icon);
        
        // Add new event listener
        newIcon.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent event bubbling
            handleIconClick(this);
        });
    });
    
    // Also add click handlers to icon containers for better click area
    document.querySelectorAll('.icon-container').forEach(container => {
        // Remove any existing event listeners
        const newContainer = container.cloneNode(true);
        container.parentNode.replaceChild(newContainer, container);
        
        // Add new event listener
        newContainer.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent event bubbling
            const icon = this.querySelector('.collapse-icon');
            if (icon) {
                handleIconClick(icon);
            }
        });
    });
    
    // Add click handler for collapse/expand button
    const collapseExpandBtn = document.getElementById('collapse-expand-btn');
    if (collapseExpandBtn) {
        collapseExpandBtn.addEventListener('click', toggleCollapseExpand);
    }
    
    // Add change handlers for filters
    const projectFilter = document.getElementById('project-filter');
    if (projectFilter) {
        projectFilter.addEventListener('change', function() {
            state.selected_project = this.value;
            fetchData(); // Refetch with new filters
        });
    }
    
    const startDateFilter = document.getElementById('start-date-filter');
    if (startDateFilter) {
        startDateFilter.addEventListener('change', function() {
            state.selected_start_date = this.value;
            fetchData(); // Refetch with new filters
        });
    }
}

// Create filter elements with improved styling
function createFilterElements() {
    const filterContainer = document.createElement('div');
    filterContainer.className = 'task-filters';
    filterContainer.innerHTML = `
        <div class="filter-container">
            <div class="filter-group">
                <label for="project-filter">Project</label>
                <select id="project-filter">
                    <option value="">All Projects</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label for="start-date-filter">Expected Start Date</label>
                <input type="date" id="start-date-filter">
            </div>
            
            <div class="filter-actions">
                <button id="collapse-expand-btn" class="btn btn-default">Collapse All</button>
            </div>
        </div>
    `;
    
    // Find a good place to insert filters (before the task table)
    const taskTable = document.querySelector('.task-table');
    if (taskTable) {
        taskTable.parentNode.insertBefore(filterContainer, taskTable);
    }
}

// Initialize the page
function initializePage() {
    // Load Font Awesome if not already loaded
    if (!document.querySelector('link[href*="font-awesome"]')) {
        const fontAwesome = document.createElement('link');
        fontAwesome.rel = 'stylesheet';
        fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css';
        document.head.appendChild(fontAwesome);
    }

    // Add custom styles for the tree view and enhanced filter styling
    const treeStyles = document.createElement('style');
    treeStyles.textContent = `
        /* Task Row Styles */
        .task-row {
            cursor: pointer;
        }

        .task-row[data-is-group="1"] .task-name {
            font-weight: bold;
        }

        .task-row[data-is-project="1"] {
            background-color: #f5f5f5;
        }

        .collapse-icon {
            margin-right: 5px;
            transition: transform 0.2s;
            width: 16px;
            display: inline-block;
            text-align: center;
            vertical-align: middle;
            cursor: pointer;
        }

        .task-name-cell {
            white-space: nowrap;
            padding-left: 5px !important;
        }

        .indent-spacer {
            display: inline-block;
            width: 20px;
        }

        .icon-container {
            display: inline-block;
            width: 16px;
            text-align: center;
            cursor: pointer;
        }

        .task-description-row {
            background-color: #fafafa;
            font-style: italic;
        }
        
        /* Enhanced Filter Styles */
        .filter-container {
            display: flex;
            align-items: flex-end;
            flex-wrap: wrap;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .filter-group {
            margin-right: 20px;
            margin-bottom: 5px;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: #505050;
            font-size: 13px;
        }
        
        .filter-group select,
        .filter-group input[type="date"] {
            padding: 6px 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
            min-width: 180px;
            background-color: white;
            font-size: 14px;
        }
        
        .filter-group select:focus,
        .filter-group input[type="date"]:focus {
            border-color: #8aa2ff;
            outline: none;
            box-shadow: 0 0 0 2px rgba(24, 79, 238, 0.1);
        }
        
        .filter-actions {
            margin-left: auto;
            display: flex;
            align-items: center;
        }
        
        .filter-actions button {
            background-color: #fff;
            border: 1px solid #ddd;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            color: #333;
            font-weight: 500;
            transition: all 0.2s;
        }
        
        .filter-actions button:hover {
            background-color: #f0f0f0;
            border-color: #ccc;
        }
    `;
    document.head.appendChild(treeStyles);

    // Create filter elements
    createFilterElements();

    // Fetch and render data
    fetchData();
}

// Event listener for DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});