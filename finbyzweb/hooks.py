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

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/finbyzweb/css/finbyzweb.css"
# app_include_js = "/assets/finbyzweb/js/finbyzweb.js"

web_include_css = [
	"https://cdnjs.cloudflare.com/ajax/libs/owl-carousel/1.3.3/owl.carousel.min.css"
]
web_include_js = [
	"https://cdnjs.cloudflare.com/ajax/libs/gsap/2.0.2/TweenMax.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/gsap/2.0.2/TimelineMax.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/owl-carousel/1.3.3/owl.carousel.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/ScrollMagic/2.0.6/ScrollMagic.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/ScrollMagic/2.0.6/plugins/animation.gsap.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/ScrollMagic/2.0.6/plugins/debug.addIndicators.min.js",
	"https://cdnjs.cloudflare.com/ajax/libs/scrollify/1.0.19/jquery.scrollify.min.js",
	"js/splittext.min.js",
	"js/finbyz.js",
]

# include js, css files in header of web template
# web_include_css = "/assets/finbyzweb/css/finbyzweb.css"
# web_include_js = "/assets/finbyzweb/js/finbyzweb.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

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