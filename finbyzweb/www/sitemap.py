# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import urllib
import frappe
from frappe.utils import get_request_site_address, get_datetime, nowdate
from frappe.website.router import get_pages,get_doctypes_with_web_view
from six import iteritems
from six.moves.urllib.parse import quote, urljoin
from frappe.model.document import get_controller

no_cache = 1
no_sitemap = 1
base_template_path = "www/sitemap.xml"

def get_context(context=None):
	"""generate the sitemap XML"""
	host = frappe.utils.get_host_name_from_request()
	links = []
	robots = frappe.db.get_single_value("Website Settings", 'robots_txt').replace('Disallow: /', '').replace('\r','').split('\n')
	
	for route, page in iteritems(get_pages()):
		flag = route not in robots

		if '/' in route:
			route_1 = route.split('/')[0]
			rb = [d.split('/')[0] for d in robots if '/*' in d]

			flag = route_1 not in rb
		

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

	for route, data in get_public_pages_from_doctypes().items():
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


def get_all_page_context_from_doctypes():
	"""
	Get all doctype generated routes (for sitemap.xml)
	"""
	routes = frappe.cache().get_value("website_generator_routes")
	if not routes:
		routes = get_page_info_from_doctypes()
		frappe.cache().set_value("website_generator_routes", routes)

	return routes


def get_page_info_from_doctypes(path=None):
	"""
	Find a document with matching `route` from all doctypes with `has_web_view`=1
	"""
	routes = {}
	for doctype in get_doctypes_with_web_view():
		filters = {}
		controller = get_controller(doctype)
		meta = frappe.get_meta(doctype)

		condition_field = (
			meta.is_published_field
			or
			# custom doctypes dont have controllers and no website attribute
			(controller.website.condition_field if not meta.custom else None)
		)

		if condition_field:
			filters[condition_field] = 1

		if path:
			filters["route"] = path

		try:
			for r in frappe.get_all(
				doctype, fields=["name", "route", "modified"], filters=filters, limit=1
			):

				routes[r.route] = {"doctype": doctype, "name": r.name, "modified": r.modified}

				# just want one path, return it!
				if path:
					return routes[r.route]
		except Exception as e:
			if not frappe.db.is_missing_column(e):
				raise e

	return routes


def get_public_pages_from_doctypes():
	
	"""Returns pages from doctypes that are publicly accessible"""

	def get_sitemap_routes():
		routes = {}
		doctypes_with_web_view = frappe.get_all(
			"DocType",
			filters={"has_web_view": True, "allow_guest_to_view": True},
			pluck="name",
		)

		for doctype in doctypes_with_web_view:
			controller = get_controller(doctype)
			meta = frappe.get_meta(doctype)
			condition_field = meta.is_published_field or controller.website.condition_field

			if not condition_field:
				continue

			try:
				res = frappe.get_all(
					doctype,
					fields=["route", "name", "modified"],
					filters={condition_field: True},
				)
			except Exception as e:
				if not frappe.db.is_missing_column(e):
					raise e
			for r in res:
				routes[r.route] = {
					"doctype": doctype,
					"name": r.name,
					"modified": r.modified,
				}
		return routes

	return frappe.cache().get_value("sitemap_routes", get_sitemap_routes)