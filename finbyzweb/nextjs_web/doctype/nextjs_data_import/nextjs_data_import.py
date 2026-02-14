# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json
import traceback

class NextJSDataImport(Document):
	def import_data(self):
		log = []
		log.append("=== IMPORT STARTED ===")
		
		try:
			if not self.import_file:
				raise Exception("Please attach a file to import.")
			
			log.append(f"Import file: {self.import_file}")

			file_doc = frappe.get_doc("File", {"file_url": self.import_file})
			file_extension = file_doc.file_name.split(".")[-1].lower()
			log.append(f"File extension: {file_extension}")

			data = []

			if file_extension == "json":
				log.append("Processing JSON file...")
				content = file_doc.get_content()
				try:
					data = json.loads(content)
					log.append(f"JSON parsed successfully. Records: {len(data)}")
				except Exception as e:
					raise Exception(f"Invalid JSON file: {str(e)}")

			elif file_extension in ["csv", "xlsx", "xls"]:
				from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
				from frappe.utils.csvutils import read_csv_content
				
				log.append(f"Processing {file_extension.upper()} file...")
				
				if file_extension == "csv":
					log.append("Reading CSV file content...")
					fcontent = file_doc.get_content()
					rows = read_csv_content(fcontent)
				else:
					log.append("Reading Excel file...")
					rows = read_xlsx_file_from_attached_file(file_url=file_doc.file_url)

				if not rows:
					raise Exception("Empty file.")
				
				log.append(f"Total rows (including header): {len(rows)}")
				log.append(f"First 5 headers: {rows[0][:5]}")

				# Parse headers and identify child table columns
				headers = rows[0]
				parsed_headers = []
				child_table_map = {}  # {index: (table_name, field_name)}
				
				# These are NOT child tables even though they have parentheses
				non_child_table_patterns = [
					"markdown", "html", "json", "text", "css",
					"main section", "main_section"
				]
				
				for i, h in enumerate(headers):
					if not h:
						parsed_headers.append(f"col_{i}")
						continue
						
					# Check if this is a child table column: "Field Name (Table Name)"
					if "(" in h and h.endswith(")"):
						field_part = h[:h.rfind("(")].strip()
						table_part = h[h.rfind("(")+1:-1].strip()
						
						# Skip non-child-table patterns like "Content (Markdown)", "Content (HTML)"
						if table_part.lower() in non_child_table_patterns:
							# Treat as parent field: "content_markdown", "content_html", etc.
							parsed_headers.append(frappe.scrub(f"{field_part} {table_part}"))
						else:
							field_name = frappe.scrub(field_part)
							table_name = frappe.scrub(table_part)
							
							child_table_map[i] = (table_name, field_name)
							parsed_headers.append(f"{field_name}__{table_name}")
					else:
						parsed_headers.append(frappe.scrub(h))
				
				log.append(f"Total headers parsed: {len(parsed_headers)}")
				log.append(f"All parsed headers: {parsed_headers}")
				if child_table_map:
					log.append(f"Child table columns: {len(child_table_map)} columns")
					for idx, (tname, fname) in child_table_map.items():
						log.append(f"  col {idx}: {fname} -> {tname}")
				
				# Parse rows and group by document (using route or id)
				documents = {}
				doc_order = []  # Track insertion order
				skipped_rows = 0
				last_doc_id = None  # Track for continuation rows
				
				for row_idx, row in enumerate(rows[1:], start=2):
					if not row or not any(row):
						skipped_rows += 1
						continue
					
					parent_data = {}
					child_data = {}
					doc_id = None
					
					for i, value in enumerate(row):
						if i >= len(parsed_headers):
							continue
						
						if i in child_table_map:
							table_name, field_name = child_table_map[i]
							if table_name not in child_data:
								child_data[table_name] = {}
							child_data[table_name][field_name] = value
						else:
							parent_data[parsed_headers[i]] = value
							if parsed_headers[i] in ["route", "id"] and value:
								doc_id = value
					
					# Determine document ID
					if not doc_id:
						doc_id = parent_data.get("route") or parent_data.get("id") or parent_data.get("name") or parent_data.get("title")
					
					# Continuation row: no parent identifier, but has child data
					# This row belongs to the previous document (denormalized CSV format)
					if not doc_id:
						if last_doc_id and child_data:
							doc_id = last_doc_id
						else:
							log.append(f"Warning: Row {row_idx} has no identifier and no child data, skipping.")
							skipped_rows += 1
							continue
					
					# Update last_doc_id tracker
					last_doc_id = doc_id
					
					# Initialize document if not exists
					if doc_id not in documents:
						documents[doc_id] = {
							"parent": parent_data,
							"child_tables": {}
						}
						doc_order.append(doc_id)
					
					# Add child table row if it has any non-empty data
					for table_name, fields in child_data.items():
						has_data = any(v for v in fields.values() if v is not None and str(v).strip())
						if not has_data:
							continue
						
						if table_name not in documents[doc_id]["child_tables"]:
							documents[doc_id]["child_tables"][table_name] = []
						
						documents[doc_id]["child_tables"][table_name].append(fields)
				
				# Convert to list format (preserve insertion order)
				data = []
				for doc_id in doc_order:
					doc_data = documents[doc_id]
					item = doc_data["parent"].copy()
					for table_name, child_rows in doc_data["child_tables"].items():
						item[table_name] = child_rows
					data.append(item)
				
				log.append(f"Unique documents parsed: {len(data)}")
				log.append(f"Skipped rows: {skipped_rows}")
				if data:
					first_doc = data[0]
					log.append(f"First document keys: {list(first_doc.keys())[:10]}")
					# Log child table counts for verification
					for d in data[:3]:
						route = d.get('route', 'unknown')
						child_info = {k: len(v) for k, v in d.items() if isinstance(v, list)}
						if child_info:
							log.append(f"  {route}: child tables = {child_info}")
			else:
				raise Exception(f"Unsupported file format: .{file_extension}. Please upload JSON, CSV, or Excel file.")

			if not isinstance(data, list):
				raise Exception("Data must be a list of records.")
			
			if not data:
				raise Exception("No data found in the file after parsing.")

			# Sort by route length to process parents first
			data.sort(key=lambda x: len(str(x.get("route", "")).split("/")))
			
			log.append(f"\n=== PROCESSING {len(data)} DOCUMENTS ===")
			
			success_count = 0
			error_count = 0
			
			for idx, item in enumerate(data, start=1):
				try:
					route = item.get('route', 'unknown')
					child_info = {k: len(v) for k, v in item.items() if isinstance(v, list)}
					log.append(f"\n[{idx}/{len(data)}] Processing: {route} | id={item.get('id', 'N/A')} | children={child_info}")
					self.process_item(item)
					log.append(f"  ✓ Success")
					success_count += 1
				except Exception as e:
					log.append(f"  ✗ Error: {str(e)}")
					log.append(f"  Traceback: {traceback.format_exc()}")
					error_count += 1

			log.append(f"\n=== IMPORT COMPLETED ===")
			log.append(f"Success: {success_count} | Errors: {error_count} | Total: {len(data)}")
			
		except Exception as e:
			log.append(f"\n!!! FATAL ERROR !!!")
			log.append(f"Error: {str(e)}")
			log.append(f"\nFull traceback:\n{traceback.format_exc()}")
		
		# Return the log — do NOT save here, let the caller handle saving
		return "\n".join(log)


	def process_item(self, item):
		route = item.get("route")
		if not route:
			raise Exception("Route is required")
			
		if not route.startswith("/"):
			route = "/" + route

		# Ensure parent exists
		parent_route = "/".join(route.split("/")[:-1])
		if not parent_route:
			parent_name = None
		else:
			parent_name = self.get_or_create_parent(parent_route)

		# Get the name from CSV ID field
		csv_id = item.get("id")

		# Check if page exists (by name or route)
		page_name = None
		if csv_id:
			page_name = csv_id if frappe.db.exists("NextJS Page", csv_id) else None
		if not page_name:
			page_name = frappe.db.get_value("NextJS Page", {"route": route}, "name")
		
		if page_name:
			if self.import_type == "Update Existing":
				doc = frappe.get_doc("NextJS Page", page_name)
				self.map_fields(doc, item, parent_name)
				doc.save()
				# Fix route after save (autoname may overwrite it)
				frappe.db.set_value("NextJS Page", doc.name, "route", route)
		else:
			doc = frappe.new_doc("NextJS Page")
			doc.route = route
			self.map_fields(doc, item, parent_name)
			# Use set_name to bypass autoname() — preserves both name and route
			if csv_id:
				doc.insert(set_name=csv_id)
			else:
				doc.insert()
				# Fix route after insert — autoname() overwrites route
				frappe.db.set_value("NextJS Page", doc.name, "route", route)

	def prefix_url(self, value):
		if not value:
			return None
		
		# If value is already a full URL, return as is
		if value.startswith("http://") or value.startswith("https://"):
			return value
			
		# Remove leading slash if present to avoid double slash
		value = value.lstrip("/")
			
		return "https://finbyz.tech/" + value

	def get_or_create_parent(self, route):
		"""Recursively ensure parents exist."""
		if not route or route == "/":
			return None
			
		# Check by route
		page_name = frappe.db.get_value("NextJS Page", {"route": route}, "name")
		if page_name:
			return page_name

		# Parent doesn't exist, check ITS parent
		parent_route = "/".join(route.split("/")[:-1])
		parent_of_parent = self.get_or_create_parent(parent_route)
		
		# Create placeholder parent with route-based name to avoid collisions
		# e.g. route "/erpnext/chemical" -> name "erpnext-chemical"
		title = route.split("/")[-1].replace("-", " ").title()
		parent_name = route.strip("/").replace("/", "-").lower()
		
		try:
			new_parent = frappe.new_doc("NextJS Page")
			new_parent.title = title
			new_parent.route = route
			new_parent.is_group = 1
			new_parent.page_type = "Web page"
			new_parent.parent_nextjs_page = parent_of_parent
			new_parent.is_published = 1
			# Use set_name to bypass autoname() — preserves both name and route
			new_parent.insert(set_name=parent_name)
			return new_parent.name
		except frappe.DuplicateEntryError:
			# Already created (name collision)
			frappe.clear_last_message()
			existing = frappe.db.get_value("NextJS Page", {"route": route}, "name")
			if existing:
				return existing
			if frappe.db.exists("NextJS Page", parent_name):
				return parent_name
			return parent_name

	def map_fields(self, doc, item, parent_name):
		# Common fields
		doc.title = item.get("title") or item.get("gallery_title") or doc.title
		doc.parent_nextjs_page = parent_name
		
		# Page Type mapping
		if self.source_doctype:
			if self.source_doctype == "Gallery":
				doc.page_type = "Gallery"
			elif self.source_doctype == "Blog Post":
				doc.page_type = "Blog Post"
			else:
				doc.page_type = "Web page"
		elif item.get("page_type"):
			doc.page_type = item.get("page_type")
		elif item.get("gallery_title"):
			doc.page_type = "Gallery"
		elif item.get("blog_category"):
			doc.page_type = "Blog Post"
		else:
			doc.page_type = "Web page"
			
		# Content Type & Content Mapping
		doc.content_type = item.get("content_type")
		
		# HTML/Page Builder is no longer supported, map to Rich Text
		if doc.content_type in ["HTML", "Page Builder"]:
			doc.content_type = "Rich Text"

		# Infer content type if not present
		if not doc.content_type:
			if item.get("main_section_markdown") or item.get("content_markdown"):
				doc.content_type = "Markdown"
			else:
				doc.content_type = "Rich Text"

		# Map Main Section (Rich Text / HTML source)
		doc.content = item.get("main_section") or item.get("content") or item.get("description") or item.get("main_section_html") or item.get("content_html") or ""
		if item.get("blog_intro"):
			doc.content = item.get("blog_intro") + "\n\n" + doc.content

		# Map Markdown
		doc.content_md = item.get("main_section_markdown") or item.get("content_markdown") or item.get("main_section_md")
			
		# Meta
		doc.meta_title = item.get("meta_title") or item.get("seo_title") or doc.title
		doc.meta_description = item.get("meta_description") or item.get("small_description")
		doc.keywords = item.get("keywords")
		
		# Image
		# Standard Attach Image field accepts string path even if file doesn't exist in File doctype
		img_val = item.get("image") or item.get("image_seo") or item.get("meta_image") or item.get("animated_image") or item.get("svg_image")
		doc.image = self.prefix_url(img_val)
		
		# Dates
		if item.get("published_on"):
			doc.published_on = item.get("published_on")
		
		# Boolean
		if "published" in item:
			doc.is_published = 1 if item.get("published") else 0
		
		# Navigation fields
		if item.get("hide_from_the_navigation") or item.get("hide_from_navigation"):
			doc.hide_from_navigation = 1
		
		if item.get("navigation_description"):
			doc.navigation_title = item.get("navigation_description")
		
		if item.get("navigation_logo"):
			doc.navigation_image = self.prefix_url(item.get("navigation_logo"))
			
		# YouTube / Video
		if item.get("youtube_link") or item.get("video"):
			doc.youtube_link = item.get("youtube_link") or item.get("video")
			
		if item.get("animated_image"):
			doc.animated_image = self.prefix_url(item.get("animated_image"))
		
		# Child Tables
		# Clear existing child tables when updating
		doc.set("faqs", [])
		doc.set("nextjs_related_page", [])
		
		# Map FAQs child table
		if "faqs" in item and isinstance(item["faqs"], list):
			for faq_row in item["faqs"]:
				if faq_row.get("question") or faq_row.get("answer"):
					doc.append("faqs", {
						"question": faq_row.get("question"),
						"answer": faq_row.get("answer"),
					})
		
		# Map Related Links / Gallery Links to NextJS Related Page
		for table_name in ["related_links", "gallery_links"]:
			if table_name in item and isinstance(item[table_name], list):
				for link_row in item[table_name]:
					title = link_row.get("title")
					route = link_row.get("route")
					reference_name = link_row.get("reference_name")
					
					# Try to find the NextJS Page
					page_name = None
					
					# 1. Try reference_name directly as page name
					if reference_name and frappe.db.exists("NextJS Page", reference_name):
						page_name = reference_name
					
					# 2. Try looking up by route (normalize with / prefix)
					if not page_name and route:
						lookup_route = route if route.startswith("/") else "/" + route
						page_name = frappe.db.get_value("NextJS Page", {"route": lookup_route}, "name")
					
					# 3. Fallback: try by title
					if not page_name and title:
						page_name = frappe.db.get_value("NextJS Page", {"title": title}, "name")
					
					if page_name or title:
						doc.append("nextjs_related_page", {
							"page": page_name,
							"title": title,
							"route": route,
							"image": self.prefix_url(link_row.get("image")),
						})

		# De-duplicate child tables (User Request)
		# FAQs
		if doc.faqs:
			unique_faqs = []
			seen_faqs = set()
			for row in doc.faqs:
				key = (row.question.strip() if row.question else None, 
					   row.answer.strip() if row.answer else None)
				if key not in seen_faqs:
					seen_faqs.add(key)
					unique_faqs.append(row)
			doc.faqs = unique_faqs

		# Related Pages
		if doc.nextjs_related_page:
			unique_rp = []
			seen_rp = set()
			for row in doc.nextjs_related_page:
				key = (
					(row.page or "").strip(),
					(row.route or "").strip(),
					(row.title or "").strip()
				)
				if key not in seen_rp:
					seen_rp.add(key)
					unique_rp.append(row)
			doc.nextjs_related_page = unique_rp


@frappe.whitelist()
def start_import(docname):
	doc = frappe.get_doc("NextJS Data Import", docname)
	doc.status = "Processing"
	doc.log = "Starting import...\n"
	doc.save()
	frappe.db.commit()
	
	try:
		import_log = doc.import_data()
		doc.reload()  # Reload to avoid save conflicts
		doc.status = "Completed"
		doc.log = import_log
	except Exception as e:
		doc.reload()
		doc.status = "Failed"
		doc.log = str(e) + "\n\n" + frappe.get_traceback()
	
	doc.save()
	frappe.db.commit()
