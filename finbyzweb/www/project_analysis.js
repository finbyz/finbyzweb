// Global state object to manage selections
const state = {
    selected_project: null,
    selected_start_date: null,
    selected_end_date: null,
    selected_employee: null
};

function updateUrlParams(from_date, to_date, project, employee) {
    const url = new URL(window.location);
    const params = new URLSearchParams(url.search);
    if (from_date) params.set('from_date', from_date);
    if (to_date) params.set('to_date', to_date);
    if (project) params.set('project', project);
    if (employee) params.set('employee', employee);

    url.search = params.toString();
    window.history.replaceState({}, '', url);
}

function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
        from_date: params.get('from_date'),
        to_date: params.get('to_date'),
        project: params.get('project'),
        employee: params.get('employee')
    };
}

function formatDateToYYYYMMDD(date) {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

async function populateProjectOptions() {
    const projectSelect = document.getElementById('projectSelect');
    projectSelect.innerHTML = '';
    
    try {
        const projects = await frappe.xcall("finbyzweb.www.project_analysis.get_projects");
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a project';
        projectSelect.appendChild(defaultOption);

        // Add project options
        projects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.name;
            option.textContent = project.project_name;
            projectSelect.appendChild(option);
        });

        // Get project from URL params
        const { project: projectFromUrl } = getUrlParams();

        if (projectFromUrl) {
            state.selected_project = projectFromUrl;
        } else if (!state.selected_project && projects.length > 0) {
            state.selected_project = projects[0].name;
        }

        // Set the selected project in the dropdown
        if (state.selected_project) {
            projectSelect.value = state.selected_project;
        }

        return state.selected_project;
    } catch (error) {
        console.error("Error fetching projects:", error);
        return null;
    }
}

function updateDates(fromDate, toDate) {
    state.selected_start_date = formatDateToYYYYMMDD(fromDate);
    state.selected_end_date = formatDateToYYYYMMDD(toDate);
    updateUrlParams(
        state.selected_start_date, 
        state.selected_end_date, 
        state.selected_project,
        state.selected_employee
    );
}

async function initial_requirements() {
    // Get URL parameters
    const { from_date, to_date, project, employee } = getUrlParams();

    // Set dates
    if (from_date && to_date) {
        state.selected_start_date = from_date;
        state.selected_end_date = to_date;
    } else {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 1);
        
        state.selected_end_date = formatDateToYYYYMMDD(endDate);
        state.selected_start_date = formatDateToYYYYMMDD(startDate);
    }

    // Set project and employee from URL if available
    if (project) {
        state.selected_project = project;
    }
    if (employee) {
        state.selected_employee = employee;
    }

    // Wait for project options to be populated
    await populateProjectOptions();

    // Initialize date inputs with current state values
    const fromDateInput = document.getElementById('fromDate');
    const toDateInput = document.getElementById('toDate');
    if (fromDateInput) fromDateInput.value = state.selected_start_date;
    if (toDateInput) toDateInput.value = state.selected_end_date;

    // Update URL and fetch data
    updateUrlParams(
        state.selected_start_date, 
        state.selected_end_date, 
        state.selected_project,
        state.selected_employee
    );
    
    await updateDataBasedOnSelection(
        state.selected_start_date, 
        state.selected_end_date, 
        state.selected_project, 
        state.selected_employee
    );

    // Call render_images if employee is present in URL
    if (state.selected_employee) {
        render_images(
            state.selected_start_date,
            state.selected_end_date,
            state.selected_project,
            state.selected_employee
        );
    }
}

function updateDataBasedOnSelection(selected_start_date, selected_end_date, selected_project, selected_employee) {
    // Ensure we have valid dates before making the call
    if (!selected_start_date || !selected_end_date) {
        console.error('Invalid dates:', { selected_start_date, selected_end_date });
        return Promise.reject(new Error('Invalid dates'));
    }

    return frappe.xcall("finbyzweb.www.project_analysis.get_data", {
        user: selected_employee,
        start_date: selected_start_date,
        end_date: selected_end_date,
        project: selected_project
    }).then((response) => {
        work_intensity(response.work_intensity);
        application_usage_time(response.application_usage);
        web_browsing_time(response.web_browsing);
        fetch_url_data(response.url_data, selected_start_date, selected_end_date, selected_project, selected_employee);
    }).catch(error => {
        console.error('Error updating data:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the application
    initial_requirements().catch(console.error);

    // Employee select change handler
    document.getElementById('employeeSelect')?.addEventListener('change', function(event) {
        state.selected_employee = event.target.value;
        updateUrlParams(
            state.selected_start_date,
            state.selected_end_date,
            state.selected_project,
            state.selected_employee
        );
        updateDataBasedOnSelection(
            state.selected_start_date,
            state.selected_end_date,
            state.selected_project,
            state.selected_employee
        );
        // Add render_images call when employee is selected
        if (state.selected_employee) {
            render_images(
                state.selected_start_date,
                state.selected_end_date,
                state.selected_project,
                state.selected_employee
            );
        }
    });

    // Project select change handler
    document.getElementById('projectSelect').addEventListener('change', function(event) {
        state.selected_project = event.target.value;
        updateUrlParams(
            state.selected_start_date,
            state.selected_end_date,
            state.selected_project,
            state.selected_employee
        );
    });

    // Save project button handler
    document.getElementById('saveProjectBtn').addEventListener('click', function() {
        state.selected_project = document.getElementById('projectSelect').value;
        updateUrlParams(
            state.selected_start_date,
            state.selected_end_date,
            state.selected_project,
            state.selected_employee
        );
        updateDataBasedOnSelection(
            state.selected_start_date,
            state.selected_end_date,
            state.selected_project,
            state.selected_employee
        );
        bootstrap.Modal.getInstance(document.getElementById('projectModal')).hide();
    });

    // Save timespan button handler
    document.getElementById('saveTimespanBtn').addEventListener('click', function() {
        const fromDate = document.getElementById('fromDate').value;
        const toDate = document.getElementById('toDate').value;
        updateDates(fromDate, toDate);
        updateDataBasedOnSelection(
            state.selected_start_date,
            state.selected_end_date,
            state.selected_project,
            state.selected_employee
        );
        bootstrap.Modal.getInstance(document.getElementById('timespanModal')).hide();
    });
});

// URL DATA Code
function fetch_url_data(r, selected_start_date, selected_end_date, selected_project, selected_employee) {
    if (r.data) {
        url_data(r.data, selected_start_date, selected_end_date, selected_project, selected_employee);
        $(document).ready(function () {
            $('#logCountModalTrigger').click(function () {
                $('#logCountModal').modal('show');
            });
        });
    }
}

function url_data(data, selected_start_date, selected_end_date, selected_project, selected_employee) {
    function getBaseURL() {
        return window.location.origin + '/app/';
    }

    let employee_data;
    let start_date_ = selected_start_date;
    let end_date_ = selected_end_date;
    if (selected_employee != null) {
        employee_data = selected_employee;
    }
    
    var total_duration = 0;
    const baseUrl = getBaseURL();
    const container = $("#url-data");
    container.empty();
    let wholedata = `
    <div class="row mt-3">
        <div class="col-md-12">
            <div class="custom-card">
                <h4 class="custom-title p-3" style="font-size: 14px !important;" align="center">All Resources</h4>
                <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr align="center">
                            <th>Resources</th>
                            <th>Total Time</th>
                        </tr>
                    </thead>
                    <tbody>`;

    data.forEach(app => {
        wholedata += `
            <tr align="center">
                <td style="color:#00A6E0 !important;"><b><a href="#" style="text-decoration:none !important;color:#00A6E0 !important;" class="url-link" data-url="${app.employee_id}" data-employee="${app.employee_id}">${app.employee}</a></b></td>
                <td style="color:#FF4001;">${convertSecondsToTime_(app.total_duration)} H</td>
            </tr>`;
        total_duration += app.total_duration;
    });

    wholedata += `
            <tr align="center">
                <td><b><a href="#" style="text-decoration:none !important;" class="url-link" data-url="null" data-employee="null">Total</a></b></td>
                <td><b>${convertSecondsToTime_(total_duration)} H</b></td>
            </tr>`;

    wholedata += `
                    </tbody>
                </table>
            </div>
        </div>
    </div>`;
    container.append(wholedata);

    $(document).ready(function () {
        $(document).on('click', '.url-link', function (e) {
            e.preventDefault();
            let clickedLink = $(this);
            let selectedEmployee = e.target.getAttribute('data-employee');

            if (selectedEmployee === "null") {
                selectedEmployee = employee_data;
            }

            // Update selected employee and call required functions
            state.selected_employee = selectedEmployee;

            // Update URL with selected employee, start date, and end date
            const newUrl = new URL(window.location);
            const params = new URLSearchParams(newUrl.search);
            params.set('employee', selectedEmployee);
            newUrl.search = params.toString();
            window.history.replaceState({}, '', newUrl);

            // Call functions to refresh data
            initial_requirements();
            frappe.xcall("finbyzweb.www.project_analysis.get_data", {
                user: selectedEmployee,
                start_date: selected_start_date,
                end_date: selected_end_date,
                project: selected_project
            }).then((response) => {
                work_intensity(response.work_intensity);
                application_usage_time(response.application_usage);
                web_browsing_time(response.web_browsing);
            });
            
            // Call render_images when employee link is clicked
            if (selectedEmployee) {
                render_images(
                    selected_start_date,
                    selected_end_date,
                    selected_project,
                    selectedEmployee
                );
            }
        });
    });
}
function work_intensity(response) {
		if (response.length === 0) {
			return;
		}

		const hours = Array.from({ length: 17 }, (_, index) => `${index + 7}:00`);
		const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
		const data = [];

		response.forEach(entry => {
			const hour = entry[0];
			const value = entry[1];
			const dayOfWeek = entry[2];
			const xIndex = hour - 7;
			const yIndex = days.indexOf(dayOfWeek);

			if (yIndex !== -1) {
				data.push([xIndex, yIndex, value || 0]);
			}
		});

		const values = data.map(item => item[2]);
		const minValue = Math.min(...values);
		const maxValue = Math.max(...values);

		const heatMapDom = document.querySelector('.work-intensity');
		const heatMapChart = echarts.init(heatMapDom, null, { renderer: 'svg' });

		const option = {
			tooltip: {
				position: 'top',
				formatter: function (params) {
					const day = days[params.value[1]];
					const hour = hours[params.value[0]];
					return `${day} ${hour}: ${params.value[2]}`;
				}
			},
			grid: {
				height: '50%',
				top: '10%'
			},
			xAxis: {
				type: 'category',
				data: hours,
				splitArea: {
					show: true
				}
			},
			yAxis: {
				type: 'category',
				data: days,
				splitArea: {
					show: true
				}
			},
			visualMap: {
				min: minValue,
				max: maxValue,
				orient: 'horizontal',
				left: 'center',
				bottom: '15%',
				color: ['rgb(0,100,200)', 'rgb(230,250,255)']
			},
			series: [{
				name: 'Intensity Count',
				type: 'heatmap',
				data: data,
				label: {
					show: false
				},
				emphasis: {
					itemStyle: {
						shadowBlur: 10,
						shadowColor: 'rgba(0, 0, 0, 0.5)'
					}
				},
				itemStyle: {
					borderWidth: 2,
					borderColor: '#ffffff'
				}
			}]
		};

		heatMapChart.setOption(option);

		// Store the chart instance globally
		window.myChart = heatMapChart;

		// Add resize listener
		window.addEventListener('resize', function () {
			if (window.myChart) {
				window.myChart.resize();
			}
		});
}

function application_usage_time(r) {
			if (r.length === 0) {
				return;
			}

			const chartDom = document.getElementById('application-usage-time');
			if (!chartDom) {
				console.error('Chart container not found.');
				return;
			}

			const myChart = echarts.init(chartDom, null, { renderer: 'svg' });

			const getCurrentThemeLabelColor = () => {
				
				return {
					labelColor: '#FFFFFF', // Default to black
					backgroundColor: 'rgba(0,0,0,0)' // Default to transparent
				};
			};

			const themeColors = getCurrentThemeLabelColor();

			const option = {
                tooltip: {
                    trigger: 'item',
                    formatter: function(params) {
                        const hours = params.data.hours;
                        const minutes = params.data.minutes;
                        const formattedHours = hours.toString().padStart(2, '0');
                        const formattedMinutes = minutes.toString().padStart(2, '0');
                        return `${params.name} : ${formattedHours}:${formattedMinutes}`;
                    },
                    show: false
                },
                legend: {
                    top: '10%', // Adjusted for better spacing
                    left: 'center'
                },
                series: [
                    {
                        name: 'Access From',
                        type: 'pie',
                        radius: ['30%', '60%'], // Adjusted to make the pie chart smaller
                        center: ['50%', '50%'],
                        avoidLabelOverlap: false,
                        itemStyle: {
                            borderRadius: 10,
                            borderColor: '#fff',
                            borderWidth: 2
                        },
                        label: {
                            show: false,
                            position: 'center'
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: 16, // Reduced font size
                                fontWeight: 'bold',
                                formatter: function(params) {
                                    const hours = params.data.hours;
                                    const minutes = params.data.minutes;
                                    const formattedHours = hours.toString().padStart(2, '0');
                                    const formattedMinutes = minutes.toString().padStart(2, '0');
                                    return `${params.name}\n${formattedHours}:${formattedMinutes} Hours`;
                                },
                                center: ['50%', '50%']
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: r
                    }
                ],
                color: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                    '#FF9966', '#66CCCC', '#6699FF', '#FF6666', '#FFCC66'
                ]
            };
            
            
			
			myChart.resize();
			myChart.setOption(option);
			myChart.resize();
			window.addEventListener('resize', function () {
				myChart.resize();
			});
}
// Application Used Chart Code Ends

// Web Browsing Time Chart Code Starts
function web_browsing_time(r) {
            if (r.length === 0) return;

            const chartDom = document.getElementById('web-browsing-time');
            if (!chartDom) {
                console.error('Chart container not found.');
                return;
            }

            // Destroy existing chart instance if it exists
            let myChart = echarts.getInstanceByDom(chartDom);
            if (!myChart) {
                myChart = echarts.init(chartDom, null, { renderer: 'svg' });
            }

            const option = {
                tooltip: {
                    trigger: 'item',
                    formatter: params => {
                        let totalHours = params.value;
                        let hours = Math.floor(totalHours);
                        let minutes = Math.round((totalHours - hours) * 60);
                        return `${params.name} : ${hours}:${minutes < 10 ? '0' + minutes : minutes} Hours`;
                    }
                },
                legend: {
                    orient: 'horizontal',
                    left: 10
                },
                series: [{
                    name: 'Access From',
                    type: 'pie',
                    radius: '75%',
                    top: '20%',
                    center: ['50%', '50%'],
                    label: {
                        show: false
                    },
                    labelLine: {
                        show: false
                    },
                    data: r,
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }],
                color: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9966', '#66CCCC', '#6699FF', '#FF6666', '#FFCC66'],
                textStyle: {
                    color: '#FFFFFF'
                },
                backgroundColor: 'rgba(0,0,0,0)'
            };

            myChart.setOption(option);
            myChart.resize(); 
            window.addEventListener('resize', function () {
                myChart.resize();
            });
}
function render_images(selected_start_date, selected_end_date, selected_project, selected_employee) {

    let startDatetime = new Date(selected_start_date + "T00:00:00");
    let endDatetime = new Date(selected_end_date + "T23:59:59");
    let data = selected_employee

    let lastPrintedDate = null;
    let lastPrintedHour = null;
    let renderedTimeSlots = new Set();

    const imageContainer = $(".recent-activity-list");
    imageContainer.empty();

    // Remove any existing scroll event listeners
    $(window).off('scroll');

    const debounce = (func, delay) => {
        let debounceTimer;
        return function () {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => func.apply(this, arguments), delay);
        };
    };

    function formatDate(date) {
        return date.toISOString().split('T')[0];
    }

    function formatDatetime(date) {
        return date.getFullYear() + '-' +
            String(date.getMonth() + 1).padStart(2, '0') + '-' +
            String(date.getDate()).padStart(2, '0') + ' ' +
            String(date.getHours()).padStart(2, '0') + ':' +
            String(date.getMinutes()).padStart(2, '0') + ':' +
            String(date.getSeconds()).padStart(2, '0');
    }

    function loadImages(user = null, start_time, end_time, selected_project) {
        const self = this;
        return frappe.xcall("finbyzweb.www.project_analysis.user_activity_images", {
            user: user,
            start_date: start_time,
            end_date: end_time,
            project: selected_project
        }).then((imagedata) => {
            // console.log("imagedata", imagedata);
            let flag = imagedata.length > 0 ? 1 : 0;
            
            let slotImages = {};
            imagedata.forEach((image) => {
                const imageDateTime = new Date(image.time);
                const hour = imageDateTime.getHours();
                const date = imageDateTime.toDateString();
                const slot = Math.floor(imageDateTime.getMinutes() / 5);
                self.formattedDate_ = formatDate(imageDateTime);
                if (!slotImages[date]) {
                    slotImages[date] = {};
                }
                if (!slotImages[date][hour]) {
                    slotImages[date][hour] = new Array(12).fill(null);
                }
                slotImages[date][hour][slot] = image;
            });

            Object.keys(slotImages).reverse().forEach(date => {
                Object.keys(slotImages[date]).reverse().forEach(hour => {
                    const timeSlotKey = `${date}-${hour}`;
                    if (!renderedTimeSlots.has(timeSlotKey)) {
                        renderedTimeSlots.add(timeSlotKey);
                        
                        if (lastPrintedDate !== date || lastPrintedHour !== hour) {
                            const hourHeader = `<div class="col-md-1"><h5><b>${date} ${hour}:00</b></h5></div><br><div class="col-md-11">
                                <div class="overall-performance-timely" id="performance-chart-${self.formattedDate_}-${hour}" style="min-height: 50px; max-height: 50px;">
                                    <!-- Overall Performance Chart Container -->
                                </div>
                                </div>`;
                            imageContainer.append(hourHeader);
                            lastPrintedDate = date;
                            lastPrintedHour = hour;
                            self.overall_performance_timely(user, self.formattedDate_, hour, selected_project);
                        }

                        for (let slot = 11; slot >= 0; slot--) {
                            const image = slotImages[date][hour][slot];
                            const slotTime = new Date(date);
                            slotTime.setHours(hour);
                            slotTime.setMinutes(slot * 5);
                            const slotTimeString = slotTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

                            if (image) {
								// console.log("image", image);
                                const imgElement = `
                                    <div class="col-md-3">
                                        <div style="display: flex; justify-content: center; align-items: center; height: 160px;">
                                            <img src="${image.screenshot}" title="${image.time_}" data-active-app="${image.active_app}" alt="User Activity Image" style="max-width: 100%; max-height: 100%; object-fit: contain;" class="clickable-image">
                                        </div>
                                        <p style="text-align: center;"><b>${slotTimeString}</b></p>
                                    </div>`;
                                imageContainer.append(imgElement);
                            } else {
                                const gapMessage = `
                                    <div class="col-md-3">
                                        <div style="width: 100%; height: 160px; background-color: #dddddd; display: flex; justify-content: center; align-items: center;">
                                            <span style="font-weight: bold;">Not Active</span>
                                        </div>
                                        <p style="text-align: center;"><b>${slotTimeString}</b></p>
                                    </div>`;
                                imageContainer.append(gapMessage);
                            }
                        }
                    }
                });
            });

            function setImageHeight() {
                const windowHeight = window.innerHeight;
                const imageHeight = windowHeight * 0.2;
                const images = document.querySelectorAll('.clickable-image');
                images.forEach(img => {
                    img.style.height = `${imageHeight}px`;
                });
            }
            setImageHeight();
            window.addEventListener('resize', setImageHeight);

            $('.clickable-image').off('click').on('click', function () {
				// console.log("clickable-image");
                const imgSrc = $(this).attr('src');
                const activeApp = $(this).data('active-app');
                showImageDialog(imgSrc, activeApp);
            });

            return flag;
        });
    }

	function showImageDialog(imgSrc, activeApp) {
		// console.log("imgSrc", imgSrc);
		// console.log("activeApp", activeApp);
	
		// Create modal HTML
		const modalHTML = `
			<div id="imageModal" class="modal" style="display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.9);">
				<div class="modal-content" style="margin: 2% auto; padding: 20px; width: 90%; max-width: 1200px; height: 90%; background-color: #fff; position: relative; display: flex; flex-direction: column;">
					<span class="close" style="color: #aaa; position: absolute; top: 10px; right: 25px; font-size: 35px; font-weight: bold; cursor: pointer;">&times;</span>
					<h5 style="margin-top: 0; margin-bottom: 5px;">${activeApp || 'Unknown App'}</h5>
					<div style="flex-grow: 1; display: flex; justify-content: center; align-items: center; overflow: hidden;">
						<img id="zoomedImg" src="${imgSrc}" style="max-width: 100%; max-height: 100%; object-fit: contain;">
					</div>
				</div>
			</div>
		`;
	
		// Append modal to body
		$('body').append(modalHTML);
	
		// Get modal element
		const modal = document.getElementById('imageModal');
	
		// Get the <span> element that closes the modal
		const span = modal.querySelector('.close');
	
		// Show the modal
		modal.style.display = "block";
	
		// When the user clicks on <span> (x), close the modal
		span.onclick = function() {
			modal.style.display = "none";
			modal.remove(); // Remove the modal from DOM after closing
		}
	
		// When the user clicks anywhere outside of the modal, close it
		window.onclick = function(event) {
			if (event.target == modal) {
				modal.style.display = "none";
				modal.remove(); // Remove the modal from DOM after closing
			}
		}
	}

    let currentDatetime = new Date(endDatetime);
    let end_time = new Date(currentDatetime);
    end_time.setMinutes(0, 0, 0);
    let start_time = new Date(end_time);
    start_time.setHours(start_time.getHours() - 1);

    let formattedStartTime = formatDatetime(start_time);
    let formattedEndTime = formatDatetime(end_time);

    function fetchImages() {
        if (start_time < startDatetime) {
            return;
        }
        loadImages(data, formattedStartTime, formattedEndTime, selected_project).then(function (flag) {
            if (flag === 0 && start_time > startDatetime) {
                end_time = new Date(start_time);
                start_time = new Date(end_time);
                start_time.setHours(start_time.getHours() - 1);
                formattedStartTime = formatDatetime(start_time);
                formattedEndTime = formatDatetime(end_time);
                fetchImages();
            }
        });
    }

    fetchImages();

    if (currentDatetime > startDatetime) {
        const handleScroll = debounce(function () {
            const windowHeight = $(window).height();
            const documentHeight = $(document).height();
            const scrollTop = $(window).scrollTop();
            const scrollPercentage = (scrollTop / (documentHeight - windowHeight)) * 100;

            if (scrollPercentage >= 50) {
                end_time = new Date(start_time);
                start_time = new Date(end_time);
                start_time.setHours(start_time.getHours() - 1);
                formattedStartTime = formatDatetime(start_time);
                formattedEndTime = formatDatetime(end_time);
                fetchImages();
            }
        }, 100);

        $(window).on('scroll', handleScroll);
    }
}



function convertSecondsToTime_(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;
    return `${hours}:${formattedMinutes}`;
}
// Overall Performance Timely Chart Code Starts
function overall_performance_timely(user,date, hour, selected_project) {
	let overallPerformanceDom = document.querySelector(`#performance-chart-${date}-${hour}`);
	if (!overallPerformanceDom) {
		console.error('Chart container not found:', `#performance-chart-${date}-${hour}`);
	}
	let overallPerformance = echarts.init(overallPerformanceDom, null, { renderer: 'svg' });
	window.addEventListener('resize', overallPerformance.resize);
	// console.log("selected_employee", user);	
	frappe.xcall("finbyzweb.www.project_analysis.overall_performance_timely", {
		employee: user,
		date: date,
		hour: hour,
		project: selected_project
	}).then((r) => {
		if (r.base_data.length === 0) {
			// Handle no data scenario if needed
		} else {
			var _rawData = {
				flight: {
					dimensions: r.base_dimensions,
					data: r.base_data
				},
				parkingApron: {
					dimensions: r.dimensions,
					data: r.data
				}
			};

			var priorityOrder = {
				'Inactive': 0,
				'Application': 1,
					'Browser': 2,
					'Idle': 3,
					'Internal Meeting': 4,
					'External Meeting': 5,
					'	Call': 6
			};

			function makeOption() {
				function convertDateTime(dateTimeString) {
					const date = new Date(dateTimeString);
					return `${date.getFullYear()}-${padZero(date.getMonth() + 1)}-${padZero(date.getDate())} ${padZero(date.getHours())}:${padZero(date.getMinutes())}:${padZero(date.getSeconds())}`;
				}

				function padZero(num) {
					return num < 10 ? `0${num}` : num;
				}
				// Function to get the start of the hour for a given date
				function getStartOfHour(date) {
				return new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), 0, 0, 0);
				}

				// Function to get the end of the hour for a given date
				function getEndOfHour(date) {
				return new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), 59, 59, 999);
				}

				// Define the inactive periods array
				var inactivePeriods = [];

				// Define a map to track the last end time of each employee
				var employeeLastEndTime = {};

				// Sort the flight data by date and then by priority
				_rawData.flight.data.sort((a, b) => new Date(a[2]).getTime() - new Date(b[2]).getTime());
				_rawData.flight.data.sort((a, b) => priorityOrder[a[0]] - priorityOrder[b[0]]);

				// Iterate over each activity in the flight data
				for (var i = 0; i < _rawData.flight.data.length; i++) {
				var activity = _rawData.flight.data[i];
				var employeeName = activity[1];
				var startTime = new Date(activity[2]);
				var endTime = new Date(activity[3]); // Assuming end time is at index 3

				// Initialize employee's last end time if not already set
				if (!employeeLastEndTime[employeeName]) {
        employeeLastEndTime[employeeName] = getStartOfHour(startTime);
				}

    // Calculate inactive period if there is a gap between the last activity and the current start time
    if (startTime > employeeLastEndTime[employeeName]) {
						var inactiveStart = employeeLastEndTime[employeeName];
        var inactiveEnd = startTime;
        
        // If the inactive period crosses an hour boundary, split it
        while (getEndOfHour(inactiveStart) < inactiveEnd && getEndOfHour(inactiveStart) < startTime) {
            var hourEnd = getEndOfHour(inactiveStart);
            inactivePeriods.push([
                'Inactive',
                employeeName,
                convertDateTime(inactiveStart.toISOString()),
                convertDateTime(hourEnd.toISOString())
            ]);
            inactiveStart = new Date(hourEnd.getTime() + 1); // Start of next hour
				}

        // Add the remaining inactive period if it exists and is within the same hour
        if (inactiveStart < inactiveEnd && inactiveStart.getHours() === inactiveEnd.getHours()) {
            inactivePeriods.push([
                'Inactive',
                employeeName,
                convertDateTime(inactiveStart.toISOString()),
                convertDateTime(inactiveEnd.toISOString())
            ]);
					}
				}

    // Update the last end time to the end of the current activity
    employeeLastEndTime[employeeName] = endTime;
				}

				// Handle inactive periods at the end of the day for each employee
				for (const employee in employeeLastEndTime) {
				var lastEnd = employeeLastEndTime[employee];
    var endOfHour = getEndOfHour(lastEnd);

    // Only add an inactive period if it's within the same hour and there's actually a gap
    if (lastEnd < endOfHour && 
        lastEnd.getHours() === endOfHour.getHours() && 
        lastEnd.getTime() !== endOfHour.getTime()) {
        
        // Ensure we're not creating a full 59-minute inactive period
        if (endOfHour.getTime() - lastEnd.getTime() < 3540000) { // 59 minutes in milliseconds
            inactivePeriods.push([
                'Inactive',
                employee,
                convertDateTime(lastEnd.toISOString()),
                convertDateTime(endOfHour.toISOString())
            ]);
        }
				}
				}

				// Combine flight data with inactive periods
				_rawData.flight.data = _rawData.flight.data.concat(inactivePeriods);

				// Sort combined data by date and priority
				_rawData.flight.data.sort((a, b) => new Date(a[2]).getTime() - new Date(b[2]).getTime());
				_rawData.flight.data.sort((a, b) => priorityOrder[a[0]] - priorityOrder[b[0]]);

				// Format the date for each entry
				_rawData.flight.data = _rawData.flight.data.map(item => {
				let date = new Date(item[2]);
				let formattedDate = `${padZero(date.getDate())}-${padZero(date.getMonth() + 1)}-${date.getFullYear()}`;
				return [item[0], formattedDate, ...item.slice(2)];
				});
				var uniqueDates = [...new Set(_rawData.flight.data.map(item => item[1]))];

				function setFixedDate(timestamp) {
					var date = new Date(timestamp);
					date.setFullYear(2000, 0, 1);
					return date.getTime();
				}
				var startTimeList = _rawData.flight.data.map(item => setFixedDate(new Date(item[2]).getTime()));
				var endTimeList = _rawData.flight.data.map(item => setFixedDate(new Date(item[3]).getTime()));
				var minStartTime = Math.min(...startTimeList);
				var maxEndTime = Math.max(...endTimeList);

				var fixedStartTime = new Date(minStartTime);
				var fixedEndTime = new Date(maxEndTime);

				let startHour = new Date(fixedStartTime);
				startHour.setMinutes(0);
				startHour.setSeconds(0);
				let endHour = new Date(fixedStartTime);
				endHour.setHours(endHour.getHours() + 1);
				endHour.setMinutes(0);
				endHour.setSeconds(0);
				function formatTimeToHHMM(date) {
					return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
				}
				
				return {
					backgroundColor: 'transparent',

					tooltip: {
						formatter: function(params) {
							var activityType = params.data[0];
							var date = params.data[1];
							var startTime_ = new Date(params.data[2]);
							var endTime_ = new Date(params.data[3]);
								// console.log(startTime_, endTime_);
							var startTimeString = formatTimeToHHMM(startTime_);
							var endTimeString = formatTimeToHHMM(endTime_);

							var durationMs = endTime_ - startTime_;
							var durationSeconds = Math.floor(durationMs / 1000);
							var hours = Math.floor(durationSeconds / 3600);
							var minutes = Math.floor((durationSeconds % 3600) / 60);
							var seconds = durationSeconds % 60;

							var durationString = "";
							if (hours > 0) durationString += hours + "h ";
							if (minutes > 0) durationString += minutes + "m ";
							if (seconds > 0 || durationString === "") durationString += seconds + "s";

								var tooltipContent = ``;

								if (activityType === "Application" || activityType === "Browser") {
									tooltipContent += `
								<div class="custom-tooltip">
									<table style="border-collapse: collapse; width: 100%; font-size: 14px;">
										<tr>
											<td style="padding: 0px 10px; text-align: left; font-weight: bold;">${startTimeString}</td>
													<td style="padding: 0px 10px; font-weight: bold;">${params.data[9]}</td>
											<td style="padding: 0px 10px; text-align: right; font-weight: bold;">${durationString}</td>
										</tr>
							`;
								}
								if (activityType === "Call") {
									tooltipContent += `
										<div class="custom-tooltip">
											<table style="border-collapse: collapse; width: 100%; font-size: 14px;">
												<tr>
													<td style="padding: 0px 10px; text-align: left; font-weight: bold;">${startTimeString}</td>
													<td style="padding: 0px 10px; font-weight: bold;">Call</td>
													<td style="padding: 0px 10px; text-align: right; font-weight: bold;">${durationString}</td>
												</tr>
									`;
								}
								if (activityType === "Idle"){
									tooltipContent += `
										<div class="custom-tooltip">
											<table style="border-collapse: collapse; width: 100%; font-size: 14px;">
												<tr>
													<td style="padding: 0px 10px; text-align: left; font-weight: bold;">${startTimeString}</td>
													<td style="padding: 0px 10px; font-weight: bold;">Idle</td>
													<td style="padding: 0px 10px; text-align: right; font-weight: bold;">${durationString}</td>
												</tr>
									`;
								}
								if (activityType === "Inactive"){
									tooltipContent += `
										<div class="custom-tooltip">
											<table style="border-collapse: collapse; width: 100%; font-size: 14px;">
												<tr>
													<td style="padding: 0px 10px; text-align: left; font-weight: bold;">${startTimeString}</td>
													<td style="padding: 0px 10px; font-weight: bold;">Inactive</td>
													<td style="padding: 0px 10px; text-align: right; font-weight: bold;">${durationString}</td>
												</tr>
									`;
								}
								if (activityType === "Internal Meeting" || activityType === "External Meeting") {
									tooltipContent += `
										<div class="custom-tooltip">
											<table style="border-collapse: collapse; width: 100%; font-size: 14px;">
												<tr>
													<td style="padding: 0px 10px; text-align: left; font-weight: bold;">${startTimeString}</td>
													<td style="padding: 0px 10px; font-weight: bold;">Meeting</td>
													<td style="padding: 0px 10px; text-align: right; font-weight: bold;">${durationString}</td>
												</tr>
									`;
								}
								if (activityType === "Application" || activityType === "Browser") {
									if (params.data[4]) {
										tooltipContent += `
											<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[4]}</td>
											</tr>`;
									}
									if (params.data[5]) {
										tooltipContent += `
											<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[5]}</td>
											</tr>`;
									}
									if (params.data[6]) {
										tooltipContent += `
											<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[6]}</td>
										</tr>`;
								}
								if (params.data[7] && params.data[8]) {
									tooltipContent += `
										<tr>
											<td style="padding: 0px 10px; text-align: left;">${params.data[7]}</td>
												<td></td>
											<td style="padding: 0px 10px; text-align: left;">${params.data[8]}</td>
										</tr>`;
								}
								}
								if (activityType === "Call") {
									// console.log("params",params);
									if (params.data[4]) {
								tooltipContent += `
									<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[4]}</td>
											</tr>`;
									}
									if (params.data[6] && params.data[7]) {
										tooltipContent += `
											<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[6]} - ${params.data[7]}</td>
											</tr>`;
									}
								} 
								if (activityType === "Internal Meeting" || activityType === "External Meeting") {
									if (params.data[7] && params.data[8]) {
										tooltipContent += `
											<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[8]} - ${params.data[7]}</td>
											</tr>`;
									}
									if (params.data[4]) {
										tooltipContent += `
											<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[4]}</td>
											</tr>`;
									}
									if (params.data[5]) {
										tooltipContent += `
											<tr>
												<td colspan="3" style="padding: 0px 10px; text-align: left;">${params.data[5]}</td>
									</tr>`;
									}
								}
								else {
									
							}

							tooltipContent += `
									</table>
								</div>`;
							
							return tooltipContent;
						},
						confine: true,  // Ensures the tooltip stays within the chart container
						textStyle: {
							fontSize: 15,
						},
						padding: [10, 15],
					},
					animation: false,
					toolbox: {
						left: 20,
						top: 0,
						itemSize: 20 
					},
					grid: {
						show: false,
						top: 20,
						bottom: 5,
						left: 120,
						right: 20,
						backgroundColor: 'transparent',
						borderWidth: 0
					},
					xAxis: {
						type: 'time',
						position: 'top',
						min: startHour,
						max: endHour,
						splitLine: {
							lineStyle: {
								color: ['#E9EDFF']
							}
						},
						axisLine: { show: false },
						axisTick: {
							lineStyle: {
								color: '#929ABA'
							}
						},
						axisLabel: {
							show: true,
							formatter: function (value) {
								let date = new Date(value);
								return `${date.getHours()}:${padZero(date.getMinutes())}`;
							}
						}
					},
					yAxis: {
						type: 'category',
						axisTick: { show: false },
						splitLine: { show: false },
						axisLine: { show: false },
						axisLabel: { 
							show: false
						},
						data: uniqueDates,
					},
					series: [
						{
							id: 'flightData',
							type: 'custom',
							renderItem: function (params, api) {
								var dateIndex = api.value(1);
								var xValue = new Date(api.value(2));
								var xEndValue = new Date(api.value(3));
								xValue.setFullYear(2000, 0, 1);
								xEndValue.setFullYear(2000, 0, 1);

								var yValue = api.coord([0, dateIndex])[1];
								var activityType = api.value(0);

								var color;
								if (activityType === 'Application') {
									color = '#4BC0C0';
								} else if (activityType === 'Inactive') {
									color = '#E9EAEC';
								} else if (activityType === 'Browser') {
									color = '#2c5278';
									} else if (activityType === 'Call') {
										color = '#FFCC66';
									} else if (activityType === 'Internal Meeting') {
										color = '#9966FF';
									} else if (activityType == 'External Meeting') {
										color = '#6699FF';
								} else {
									color = '#4BC0C0';
								}

								var barHeight = Math.min(20, api.size([0, 1])[1] * 0.8);

								var item = {
									type: 'rect',
									shape: {
										x: api.coord([xValue, yValue])[0],
										y: yValue - barHeight / 2,
										width: api.size([xEndValue - xValue, 0])[0],
										height: barHeight,
									},
									style: api.style({
										fill: color,
										stroke: 'rgba(0,0,0,0.2)'
									})
								};

								return item;
							},
							dimensions: _rawData.flight.dimensions,
							encode: {
								x: [2, 3],
								y: 1,
							},
							data: _rawData.flight.data
						}
					]
				};
			}

			overallPerformance.setOption(makeOption());

			function updateChart() {
				let legends = overallPerformance.getOption().legend[0].selected;
				legends = Object.keys(legends).filter(legend => legends[legend]);
				var filteredData = _rawData.flight.data.filter(item => {
					var activityType = item[0];
					return legends.includes(activityType);
				});

				overallPerformance.setOption({
					series: [{
						id: 'flightData',
						data: filteredData
					}]
				});
			}

			$('#overallChartLegends li').each(function() {
				let li = $(this);
				$(li).attr('selected', 'true');
			});

			function updateLegend() {
				let overallChartLegends = $('#overallChartLegends li');
				let legends = {};

				overallChartLegends.each(function() {
					let li = $(this);
					legends[li.attr('data-value')] = li.attr('selected') ? true : false;
				});

				overallPerformance.setOption({
					legend: {
						selected: legends
					}
				});
			}

			let overallChartLegends = document.querySelectorAll('#overallChartLegends li');
			$.each(overallChartLegends, function(index, li) {
				$(li).on('click', function() {
					if ($(li).attr('selected')) {
						$(li).removeAttr('selected');
					} else {
						$(li).attr('selected', 'true');
					}
					updateLegend();
					updateChart();
				});
			});
		}
	});
}
// Overall Performance Timely Chart Code Ends

// render_images();