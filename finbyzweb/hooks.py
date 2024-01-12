# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "finbyzweb"
app_title = "Finbyzweb"
app_publisher = "Finbyz Tech Pvt Ltd"
app_description = "App for Website"
app_icon = "octicon octicon-search"
app_color = "#30AFE2"
app_email = "info@finbyz.com"
app_license = "GPL 3.0"

# override bcz getting 404 error in thirt party files
from frappe.website import utils
from finbyzweb.api import add_preload_headers as my_add_preload_headers
utils.add_preload_headers = my_add_preload_headers

# app_include_js = [
# 	"assets/js/summernote.min.js",
# 	"assets/js/comment_desk.min.js",
# 	"assets/js/editor.min.js",
# 	"assets/js/timeline.min.js"
# ]

app_include_css = [
	"assets/css/summernote.min.css"
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/finbyzweb/css/finbyzweb.css"
# app_include_js = "/assets/finbyzweb/js/finbyzweb.js"

web_include_css = [
	"https://stackpath.bootstrapcdn.com/bootstrap/4.2.1/css/bootstrap.min.css",
	"https://cdnjs.cloudflare.com/ajax/libs/OwlCarousel2/2.3.4/assets/owl.carousel.min.css"
]
# web_include_js = [
	# "assets/finbyzweb/js/finbyz.js",
# ]

# include js, css files in header of web template
web_include_css = "/assets/finbyzweb/css/finbyzweb.css"
# web_include_js = "/assets/finbyzweb/js/finbyzweb.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

override_doctype_class = {
	"Website Theme": "finbyzweb.website_theme_override.CustomWebsiteTheme"
}



doctype_js = {
	"Web Page": "public/js/doctype_js/web_page.js"
}


# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "finbyzweb.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "finbyzweb.install.before_install"
# after_install = "finbyzweb.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "finbyzweb.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"finbyzweb.tasks.all"
# 	],
# 	"daily": [
# 		"finbyzweb.tasks.daily"
# 	],
# 	"hourly": [
# 		"finbyzweb.tasks.hourly"
# 	],
# 	"weekly": [
# 		"finbyzweb.tasks.weekly"
# 	]
# 	"monthly": [
# 		"finbyzweb.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "finbyzweb.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "finbyzweb.event.get_events"
# }

doc_events = {
	"Customer": {
		"before_save": "finbyzweb.api.customer_before_save"
	}
}

override_doctype_dashboards = {
	"Issue":"finbyzweb.finbyzweb.dashboard.issue.get_data",
}