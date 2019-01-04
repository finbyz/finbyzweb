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
	host = get_request_site_address()
	links = []
	robots = frappe.db.get_single_value("Website Settings", 'robots_txt').replace('Disallow: /', '').split('\n')

	for route, page in iteritems(get_pages()):
		flag = route not in robots

		if '/' in route:
			route_1 = route.split('/')[0]
			rb = [d.split('/')[0] for d in robots if '/*' in d]

			flag = route_1 not in rb

		if not page.no_sitemap and flag:
			links.append({
				"loc": urljoin(host, quote(page.name.encode("utf-8"))),
				"lastmod": nowdate()
			})

	for route, data in iteritems(get_all_page_context_from_doctypes()):
		flag = route not in robots

		if '/' in route:
			route_1 = route.split('/')[0]
			rb = [d.split('/')[0] for d in robots if '/*' in d]

			flag = route_1 not in rb

		if flag:
			links.append({
				"loc": urljoin(host, quote((route or "").encode("utf-8"))),
				"lastmod": get_datetime(data.get("modified")).strftime("%Y-%m-%d")
			})

	return {"links":links}
