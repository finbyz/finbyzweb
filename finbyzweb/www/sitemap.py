# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import urllib
import frappe
from frappe.utils import get_request_site_address, get_datetime, nowdate
from frappe.website.router import get_pages, get_all_page_context_from_doctypes
from six import iteritems
from six.moves.urllib.parse import quote, urljoin

no_cache = 1
no_sitemap = 1
base_template_path = "templates/www/sitemap.xml"

def get_context(context):
	"""generate the sitemap XML"""
	host = frappe.utils.get_host_name_from_request()
	links = []
	robots = frappe.db.get_single_value("Website Settings", 'robots_txt').replace('Disallow: /', '').replace('\r','').split('\n')

	for route, page in iteritems(get_pages()):
		print(route)
		flag = route not in robots

		if '/' in route:
			route_1 = route.split('/')[0]
			rb = [d.split('/')[0] for d in robots if '/*' in d]

			flag = route_1 not in rb
		
		print(flag)

		if flag:
			priority = 0.4
			if page.route in ("about","contact","services"):
				priority = 0.9
			elif page.route == "clients":
				priority = 0.6
			else:
				priority = 0.4

			links.append({
				"loc": urljoin(host, quote(page.name.encode("utf-8"))),
				"lastmod": nowdate(),
				"priority": priority
			})

	for route, data in iteritems(get_all_page_context_from_doctypes()):
		flag = route not in robots

		if '/' in route:
			route_1 = route.split('/')[0]
			rb = [d.split('/')[0] for d in robots if '/*' in d]

			flag = route_1 not in rb

		if flag:
			priority = 0.5
			if data.get("doctype") == "Web Page":
				priority = 0.9
			elif data.get("doctype") == "Gallery":
				priority = 0.6
			elif data.get("doctype") == "Job Opening":
				priority = 0.7
			elif data.get("doctype") == "Blog Post":
				priority = 0.8
			else:
				priority = 0.5
			
			links.append({
				"loc": urljoin(host, quote((route or "").encode("utf-8"))),
				"lastmod": get_datetime(data.get("modified")).strftime("%Y-%m-%d"),
				"priority": priority
			})

	return {"links":links}
