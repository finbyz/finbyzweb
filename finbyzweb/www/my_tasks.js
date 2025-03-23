// Global state object to manage selections
const state = {
    selected_project: null,
    selected_start_date: null,
    selected_end_date: null,
    selected_employee: null
};

// Fetch data from the server
async function fetchData() {
    try {
        const response = await frappe.xcall('finbyzweb.www.my_tasks.get_data');
        console.log(response)
        renderTaskTree(response);

    } catch (error) {
        console.error('Error fetching data:', error);
        frappe.msgprint({
            title: 'Error',
            indicator: 'red',
            message: `Failed to fetch data: ${error.message || 'Unknown error'}`
        });
    }
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
        console.log(`Set parent of ${task.task_id} to explicit parent_task: ${task.parent_task}`);
    } 
    // Otherwise, if it was passed a parentId parameter (from a project or a group task), use that
    else if (parentId) {
        row.dataset.parent = parentId;
        console.log(`Set parent of ${task.task_id} to parentId parameter: ${parentId}`);
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
    console.log("Showing children of:", parentId);
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
    console.log("Hiding children of:", parentId);
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
        
        console.log("Toggling task:", taskId);
        console.log("Row data:", row.dataset);

        // Debug what we're looking for
        const children = document.querySelectorAll(`.task-row[data-parent="${taskId}"]`);
        console.log(`Found ${children.length} children rows with parent="${taskId}"`);
        if (children.length > 0) {
            console.log("Child rows:", children);
        } else {
            console.warn("No children found for this parent!");
        }

        // Toggle expand/collapse
        if (iconElement.classList.contains('fa-chevron-down')) {
            // Collapse
            console.log("Collapsing - changing icon and hiding children");
            iconElement.classList.remove('fa-chevron-down');
            iconElement.classList.add('fa-chevron-right');
            hideChildTasks(taskId);
        } else {
            // Expand
            console.log("Expanding - changing icon and showing children");
            iconElement.classList.remove('fa-chevron-right');
            iconElement.classList.add('fa-chevron-down');
            showChildTasks(taskId);
        }
    } else {
        console.log("This row is not a group or project row", row);
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

    // Add custom styles for the tree view
    const treeStyles = document.createElement('style');
    treeStyles.textContent = `
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
    `;
    document.head.appendChild(treeStyles);

    fetchData();
}

// Event listener for DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    console.log("Initializing task tree...");
    initializePage();
});