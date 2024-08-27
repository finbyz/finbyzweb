let selectedProject = null;

function updateUrlParams(from_date, to_date, project) {
    const url = new URL(window.location);
    const params = new URLSearchParams(url.search);

    if (from_date) params.set('from_date', from_date);
    if (to_date) params.set('to_date', to_date);
    if (project) params.set('project', project);

    url.search = params.toString();
    window.history.replaceState({}, '', url);
}

function initial_requirements() {
    // Function to get URL parameters
    function getUrlParams() {
        const params = new URLSearchParams(window.location.search);
        return {
            from_date: params.get('from_date'),
            to_date: params.get('to_date'),
            project: params.get('project')
        };
    }

    // Retrieve URL parameters
    const { from_date, to_date, project } = getUrlParams();
    if (from_date && to_date) {
        this.selected_start_date = from_date;
        this.selected_end_date = to_date;
    } else {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(endDate.getDate() - 30);
        
        this.selected_end_date = formatDateToYYYYMMDD(endDate);
        this.selected_start_date = formatDateToYYYYMMDD(startDate);

        updateUrlParams(this.selected_start_date, this.selected_end_date, this.selected_project);
    }

    if (project && !this.selected_project) {
        this.selected_project = project;
    }

    populateProjectOptions();
    updateDataBasedOnSelection(this.selected_start_date, this.selected_end_date, this.selected_project, this.selected_employee);
}

function updateDataBasedOnSelection(selected_start_date, selected_end_date, selected_project, selected_employee) {
	console.log("hii")
    work_intensity(selected_start_date, selected_end_date, selected_project, selected_employee);
    application_usage_time(selected_start_date, selected_end_date, selected_project, selected_employee);
    web_browsing_time(selected_start_date, selected_end_date, selected_project, selected_employee);
    fetch_url_data(selected_start_date, selected_end_date, selected_project, selected_employee);
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

function populateProjectOptions() {
    const projectSelect = document.getElementById('projectSelect');
    projectSelect.innerHTML = '';
    
    frappe.xcall("finbyzweb.www.project_analysis.get_projects")
        .then(projects => {
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a project';
            projectSelect.appendChild(defaultOption);

            projects.forEach(project => {
                const option = document.createElement('option');
                option.value = project.name;
                option.textContent = project.project_name;
                projectSelect.appendChild(option);
            });

            // Check URL for project
            const urlParams = new URLSearchParams(window.location.search);
            const projectFromUrl = urlParams.get('project');

            if (projectFromUrl) {
                this.selected_project = projectFromUrl;
            } else if (!this.selected_project && projects.length > 0) {
                this.selected_project = projects[0].name;
            }

            // Set the selected project in the dropdown
            if (this.selected_project) {
                projectSelect.value = this.selected_project;
                updateUrlParams(this.selected_start_date, this.selected_end_date, this.selected_project);
            }
            
            // console.log("selected_project", this.selected_project);
        })
        .catch(error => {
            console.error("Error fetching projects:", error);
        });
}

function updateDates(fromDate, toDate) {
    this.selected_start_date = formatDateToYYYYMMDD(fromDate);
    this.selected_end_date = formatDateToYYYYMMDD(toDate);
    updateUrlParams(this.selected_start_date, this.selected_end_date, this.selected_project);
}

document.addEventListener('DOMContentLoaded', function() {
    initial_requirements.call(this);

    document.getElementById('projectSelect').addEventListener('change', function () {
        this.selected_project = this.value;
        // console.log("Selected project:", this.selected_project);
        updateUrlParams(this.selected_start_date, this.selected_end_date, this.selected_project);
        // updateDataBasedOnSelection.call(this);
    }.bind(this));

    document.getElementById('saveProjectBtn').addEventListener('click', function() {
        // console.log("Saving project:", document.getElementById('projectSelect').value);
        this.selected_project = document.getElementById('projectSelect').value;
        updateUrlParams(this.selected_start_date, this.selected_end_date, this.selected_project);
        updateDataBasedOnSelection(this.selected_start_date, this.selected_end_date, this.selected_project, this.selected_employee);
        bootstrap.Modal.getInstance(document.getElementById('projectModal')).hide();
    }.bind(this));

    document.getElementById('saveTimespanBtn').addEventListener('click', function() {
        const fromDate = document.getElementById('fromDate').value;
        const toDate = document.getElementById('toDate').value;
        updateDates.call(this, fromDate, toDate);
        updateDataBasedOnSelection(this.selected_start_date, this.selected_end_date, this.selected_project, this.selected_employee);
        bootstrap.Modal.getInstance(document.getElementById('timespanModal')).hide();
    }.bind(this));
});
function work_intensity(selected_start_date, selected_end_date, selected_project, selected_employee) {
	frappe.xcall("finbyzweb.www.project_analysis.work_intensity", {
        user: selected_employee,
		start_date: selected_start_date,
		end_date: selected_end_date,
        project: selected_project
	}).then((response) => {
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
	}).catch((error) => {
		console.error("Error fetching data:", error);
	});
}

function application_usage_time(selected_start_date, selected_end_date, selected_project, selected_employee) {
	frappe
		.xcall("finbyzweb.www.project_analysis.application_usage_time", {
            user: selected_employee,
			start_date: selected_start_date,
			end_date: selected_end_date,
            project: selected_project
		})
		.then((r) => {
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
		})
		.catch(error => {
			console.error("Error fetching chart data:", error);
		});
}
// Application Used Chart Code Ends

// Web Browsing Time Chart Code Starts
function web_browsing_time(selected_start_date, selected_end_date, selected_project, selected_employee) {
    frappe
        .xcall("finbyzweb.www.project_analysis.web_browsing_time", {
            user: selected_employee,
            start_date: selected_start_date,
            end_date: selected_end_date,
            project: selected_project
        })
        .then(r => {
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
            myChart.resize(); // Ensure it fits the container initially

            // Ensure `selected_start_date` and `selected_end_date` are accessible or passed as arguments
            // Re-add resize listener to ensure chart resizes with window
            window.addEventListener('resize', function () {
                myChart.resize();
            });
        })
        .catch(error => {
            console.error("Error fetching chart data:", error);
        });
}
function render_images(selected_start_date, selected_end_date, selected_project, selected_employee) {
    let startDatetime = new Date(selected_start_date + "T00:00:00");
    let endDatetime = new Date(selected_end_date + "T23:59:59");
    let data = selected_employee ? selected_employee : user_id;

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
            console.log("imagedata", imagedata);
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
                const imgSrc = $(this).attr('src');
                const activeApp = $(this).data('active-app');
                showImageDialog(imgSrc, activeApp);
            });

            return flag;
        });
    }

    function showImageDialog(imgSrc, activeApp) {
        let dialog = new frappe.ui.Dialog({
            title: activeApp || 'Unknown App',
            fields: [
                {
                    fieldtype: 'HTML',
                    label: '',
                    fieldname: 'image_content',
                    options: `
                        <div class="frappe-card custom-card">
                            <div class="modal-body">
                                <img id="zoomedImg" src="${imgSrc}" class="img-fluid" style="width: 100%; height: auto; object-fit: contain;">
                            </div>
                        </div>`
                }
            ],
            size: 'extra-large',
            primary_action_label: 'Close',
            primary_action: function () {
                dialog.hide();
            }
        });

        dialog.show();
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
// URL DATA Code Starts
function fetch_url_data(start_date, end_date, project, employee) {
	// console.log("start_date", this.selected_start_date);
	// console.log("end_date", this.selected_end_date);
	// console.log("employee", this.selected_employee);
	// console.log("project mmm", this.selected_project);
    frappe.call({
        method: "finbyzweb.www.project_analysis.fetch_url_data",
        args: {
            start_date: start_date,
            end_date: end_date,
            project: project,
            employee: employee
        },
        callback: (r) => {
            if (r.message) {
                url_data(r.message);
                $(document).ready(function () {
                    $('#logCountModalTrigger').click(function () {
                        $('#logCountModal').modal('show');
                    });
                });
            }
        }
    });
}
function url_data(data) {
    function getBaseURL() {
        return window.location.origin + '/app/';
    }

    let employee_data;
    let start_date_ = this.selected_start_date;
    let end_date_ = this.selected_end_date;
    if (this.selected_employee != null) {
        employee_data = this.selected_employee;
    } else {
        employee_data = this.user_id;
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

    data.data.forEach(app => {
        wholedata += `
            <tr align="center">
                <td style="color:#00A6E0 !important;"><b><a href="#" style="text-decoration:none !important;color:#00A6E0 !important;" class="url-link" data-url="${app.employee_id}" data-employee="${app.employee_id}">${app.employee}</a></b></td>
                <td style="color:#FF4001;">${this.convertSecondsToTime_(app.total_duration)} H</td>
            </tr>`;
        total_duration += app.total_duration;
    });

    wholedata += `
            <tr align="center">
                <td><b><a href="#" style="text-decoration:none !important;" class="url-link" data-url="null" data-employee="null">Total</a></b></td>
                <td><b>${this.convertSecondsToTime_(total_duration)} H</b></td>
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
            this.selected_employee = selectedEmployee;

            // Update URL with selected employee, start date, and end date
            const newUrl = new URL(window.location);
            const params = new URLSearchParams(newUrl.search);
            params.set('employee', this.selected_employee);
            params.set('from_date', this.selected_start_date);
            params.set('to_date', this.selected_end_date);
            newUrl.search = params.toString();
            window.history.replaceState({}, '', newUrl);

            // Call functions to refresh data
            initial_requirements.call(this);
            work_intensity(this.selected_start_date, this.selected_end_date, this.selected_project, this.selected_employee);
            application_usage_time(this.selected_start_date, this.selected_end_date, this.selected_project, this.selected_employee);
            web_browsing_time(this.selected_start_date, this.selected_end_date, this.selected_project, this.selected_employee);
            render_images(this.selected_start_date, this.selected_end_date, this.selected_project, this.selected_employee);
        }.bind(this));
    });
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
			};

			function makeOption() {
				function convertDateTime(dateTimeString) {
					const date = new Date(dateTimeString);
					return `${date.getFullYear()}-${padZero(date.getMonth() + 1)}-${padZero(date.getDate())} ${padZero(date.getHours())}:${padZero(date.getMinutes())}:${padZero(date.getSeconds())}`;
				}

				function padZero(num) {
					return num < 10 ? `0${num}` : num;
				}

				// Define the inactive periods array
				var inactivePeriods = [];
				// Define a map to track the end time of the last activity for each employee
				var employeeLastEndTime = {};
				// Sort the flight data by date and then by priority
				_rawData.flight.data.sort((a, b) => new Date(a[2]).getTime() - new Date(b[2]).getTime());
				_rawData.flight.data.sort((a, b) => priorityOrder[a[0]] - priorityOrder[b[0]]);
				// Iterate over each activity in the flight data
				for (var i = 0; i < _rawData.flight.data.length; i++) {
				var activity = _rawData.flight.data[i];
				var employeeName = activity[1];
				var startTime = new Date(activity[2]).getTime();
				var endTime = new Date(activity[3]).getTime(); // Assuming end time is at index 3
				// Initialize employee's last end time if not already set
				if (!employeeLastEndTime[employeeName]) {
					employeeLastEndTime[employeeName] = startTime; // Set to the start time of the first activity
				}
				// Calculate inactive period if there is a gap between the last activity and the current start time
				if (startTime > employeeLastEndTime[employeeName]) {
					var lastEndTime = employeeLastEndTime[employeeName];
					var startTimeString = convertDateTime(new Date(lastEndTime).toISOString());
					var endTimeString = convertDateTime(new Date(startTime).toISOString());       
					inactivePeriods.push(['Inactive', employeeName, startTimeString, endTimeString]);
				}
				// Update the last end time to the end time of the current activity
				employeeLastEndTime[employeeName] = endTime;
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

				var hourStart = getStartOfHour(startTime);
				var hourEnd = getEndOfHour(startTime);

				// Initialize employee's last end time if not already set
				if (!employeeLastEndTime[employeeName]) {
					employeeLastEndTime[employeeName] = hourStart;
				}

				// Calculate inactive periods for the previous hour if there's a gap
				if (employeeLastEndTime[employeeName] < hourStart) {
					if (employeeLastEndTime[employeeName] < hourEnd) {
						var inactiveStart = employeeLastEndTime[employeeName];
						var inactiveEnd = Math.min(hourEnd, startTime);
						if (inactiveStart < inactiveEnd) {
							var startTimeString = convertDateTime(new Date(inactiveStart).toISOString());
							var endTimeString = convertDateTime(new Date(inactiveEnd).toISOString());
							inactivePeriods.push(['Inactive', employeeName, startTimeString, endTimeString]);
						}
					}
					// Update last end time to the end of the current activity
					employeeLastEndTime[employeeName] = Math.max(employeeLastEndTime[employeeName], endTime);
				} else {
					// Update last end time to the end of the current activity
					employeeLastEndTime[employeeName] = Math.max(employeeLastEndTime[employeeName], endTime);
				}
				}

				// Handle inactive periods after the last activity of each employee for the day
				for (const employee in employeeLastEndTime) {
				var lastEnd = employeeLastEndTime[employee];
				var nextHourStart = getStartOfHour(new Date(lastEnd)).getTime() + 3600000; // Start of next hour
				var endOfDay = new Date(lastEnd).setHours(23, 59, 59, 999);

				if (nextHourStart < endOfDay) {
					var startTimeString = convertDateTime(new Date(lastEnd).toISOString());
					var endTimeString = convertDateTime(new Date(nextHourStart).toISOString());
					inactivePeriods.push(['Inactive', employee, startTimeString, endTimeString]);
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

				var hourStart = getStartOfHour(startTime);
				var hourEnd = getEndOfHour(startTime);

				// Initialize employee's last end time if not already set
				if (!employeeLastEndTime[employeeName]) {
					// Initialize to the start of the day or the first hour boundary
					employeeLastEndTime[employeeName] = hourStart;
				}

				// Handle inactive period from the end of the last activity to the start of the current activity
				if (employeeLastEndTime[employeeName] < startTime) {
					var inactiveStart = employeeLastEndTime[employeeName];
					var inactiveEnd = startTime;
					if (inactiveStart < inactiveEnd) {
						var startTimeString = convertDateTime(new Date(inactiveStart).toISOString());
						var endTimeString = convertDateTime(new Date(inactiveEnd).toISOString());
						inactivePeriods.push(['Inactive', employeeName, startTimeString, endTimeString]);
					}
				}

				// Update last end time to the end of the current activity
				employeeLastEndTime[employeeName] = Math.max(employeeLastEndTime[employeeName], endTime);

				// Move the last end time to the end of the hour if needed
				if (endTime > hourEnd) {
					employeeLastEndTime[employeeName] = hourEnd;
				}
				}

				// Handle inactive periods at the end of the day for each employee
				for (const employee in employeeLastEndTime) {
				var lastEnd = employeeLastEndTime[employee];
				var endOfDay = new Date(lastEnd).setHours(23, 59, 59, 999);

				// Add inactive periods from the end of the last recorded activity until the end of the day
				if (lastEnd < endOfDay) {
					var startTimeString = convertDateTime(new Date(lastEnd).toISOString());
					var endTimeString = convertDateTime(new Date(endOfDay).toISOString());
					inactivePeriods.push(['Inactive', employee, startTimeString, endTimeString]);
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

							var tooltipContent = `
								<div class="custom-tooltip">
									<table style="border-collapse: collapse; width: 100%; font-size: 14px;">
										<tr>
											<td style="padding: 0px 10px; text-align: left; font-weight: bold;">${startTimeString}</td>
											<td style="padding: 0px 10px; text-align: right; font-weight: bold;">${durationString}</td>
										</tr>
							`;

							if (activityType === "Application" || activityType === "Browser") {
								if (params.data[4]) {
									tooltipContent += `
										<tr>
											<td colspan="2" style="padding: 0px 10px; text-align: left;">${params.data[4]}</td>
										</tr>`;
								}
								if (activityType) {
									tooltipContent += `
										<tr>
											<td colspan="2" style="padding: 0px 10px; text-align: left;">${params.data[9]}</td>
										</tr>`;
								}
								if (params.data[5]) {
									tooltipContent += `
										<tr>
											<td colspan="2" style="padding: 0px 10px; text-align: left;">${params.data[5]}</td>
										</tr>`;
								}
								if (params.data[6]) {
									tooltipContent += `
										<tr>
											<td colspan="2" style="padding: 0px 10px; text-align: left;">${params.data[6]}</td>
										</tr>`;
								}
								if (params.data[7] && params.data[8]) {
									tooltipContent += `
										<tr>
											<td style="padding: 0px 10px; text-align: left;">${params.data[7]}</td>
											<td style="padding: 0px 10px; text-align: left;">${params.data[8]}</td>
										</tr>`;
								}
							} else {
								tooltipContent += `
									<tr>
										<td colspan="2" style="padding: 0px 10px; text-align: left;">${activityType}</td>
									</tr>`;
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