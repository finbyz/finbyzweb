# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# See license.txt

import frappe
import json
from frappe.tests.utils import FrappeTestCase
from finbyzweb.nextjs_web.doctype.nextjs_data_import.nextjs_data_import import NextJSDataImport

class TestNextJSDataImport(FrappeTestCase):
	def setUp(self):
		# Clear existing pages to avoid conflicts
		frappe.db.delete("NextJS Page")
		frappe.db.delete("NextJS Data Import")

	def test_import_hierarchy(self):
		# Create a dummy file
		data = [
			{
				"title": "Deep Page",
				"route": "/services/api/deep",
				"page_type": "Web page",
				"content": "Deep content"
			},
			{
				"title": "Services",
				"route": "/services",
				"page_type": "Web page"
			}
			# Note: /services/api is missing, should be created automatically
		]
		
		content = json.dumps(data)
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": "test_import.json",
			"content": content,
			"is_private": 1
		}).insert()

		# Create Import Doc
		import_doc = frappe.get_doc({
			"doctype": "NextJS Data Import",
			"import_file": file_doc.file_url,
			"import_type": "Insert New"
		}).insert()

		# Run Import
		import_doc.import_data()

		# Verify
		self.assertTrue(frappe.db.exists("NextJS Page", {"route": "/services"}))
		self.assertTrue(frappe.db.exists("NextJS Page", {"route": "/services/api"}), "Placeholder /services/api should exist")
		self.assertTrue(frappe.db.exists("NextJS Page", {"route": "/services/api/deep"}))

		# Check Hierarchy
		services = frappe.get_doc("NextJS Page", {"route": "/services"})
		api = frappe.get_doc("NextJS Page", {"route": "/services/api"})
		deep = frappe.get_doc("NextJS Page", {"route": "/services/api/deep"})

		self.assertEqual(api.parent_nextjs_page, services.name)
		self.assertEqual(deep.parent_nextjs_page, api.name)
		
		# Check content
		self.assertEqual(deep.content, "Deep content")
		self.assertEqual(api.title, "Api") # Title Case generated

	def test_blog_import(self):
		data = [{
			"title": "My Blog",
			"route": "/blog/my-blog",
			"blog_category": "Tech",
			"blog_intro": "Intro",
			"content": "Body"
		}]
		
		content = json.dumps(data)
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": "test_blog.json",
			"content": content,
			"is_private": 1
		}).insert()

		import_doc = frappe.get_doc({
			"doctype": "NextJS Data Import",
			"import_file": file_doc.file_url
		}).insert()
		
		import_doc.import_data()
		
		blog = frappe.get_doc("NextJS Page", {"route": "/blog/my-blog"})
		self.assertEqual(blog.page_type, "Blog Post")
		self.assertIn("Intro", blog.content)
		self.assertIn("Body", blog.content)
		
		# Parent /blog should hold it
		self.assertTrue(frappe.db.exists("NextJS Page", {"route": "/blog"}))

	def test_csv_import(self):
		csv_content = "title,route,page_type,content\nCSV Page,/csv-page,Web page,Content from CSV"
		
		file_doc = frappe.get_doc({
			"doctype": "File",
			"file_name": "test_import.csv",
			"content": csv_content,
			"is_private": 1
		}).insert()

		import_doc = frappe.get_doc({
			"doctype": "NextJS Data Import",
			"import_file": file_doc.file_url,
			"import_type": "Insert New"
		}).insert()
		
		import_doc.import_data()
		
		page = frappe.get_doc("NextJS Page", {"route": "/csv-page"})
		self.assertEqual(page.title, "CSV Page")
		self.assertEqual(page.page_type, "Web page")
		self.assertEqual(page.content, "Content from CSV")
