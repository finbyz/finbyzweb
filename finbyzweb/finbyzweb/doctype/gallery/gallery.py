# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.website.website_generator import WebsiteGenerator

class Gallery(WebsiteGenerator):
	def get_context(self, context):
		context.category = frappe.db.get_value("Gallery Category",
			context.doc.gallery_category, ["category"], as_dict=1)

		context.parents = [{"name": _("Home"), "route":"/"},
			{"name": "Gallery", "route": "/gallery"}]
		return context
		
	def make_route(self):
		'''Returns the default route. If `route` is specified in DocType it will be
		route/title'''
		from_title = self.scrubbed_title()
		return from_title
	
	@frappe.whitelist()
	def expand_gallery_description(self):
		"""
		Expands and optimizes the gallery description content using AI agent
		"""
		try:
			# Hardcoded AI Agent name
			ai_agent_name = "Gallery Content Generator"
			
			# Get the AI agent document
			ai_agent_doc = frappe.get_doc("AI Agent", ai_agent_name)
			
			if not ai_agent_doc:
				frappe.throw(f"AI Agent '{ai_agent_name}' not found")
			
			# Get the AI service from the agent
			ai_service = ai_agent_doc.agent_service
			
			if not ai_service:
				frappe.throw(f"AI Agent '{ai_agent_name}' has no configured service")
			
			# Prepare AI input data
			ai_input_data = {
				"existing_description": self.description or "",
				"title": self.title or "Gallery Item",
			}
			
			frappe.logger().info(f"Calling AI Agent '{ai_agent_name}' with inputs: {list(ai_input_data.keys())}")
			
			# Invoke the AI service
			result = ai_service.invoke(**ai_input_data)
   
  			# Log the raw output for debugging
			frappe.log_error(
				title=f"AI Raw Output - {self.name}",
				message=str(result)
			)
			
			# Parse AI output
			expanded_content = self._parse_ai_result(result)
			
			# Extract the HTML content
			html_content = self._extract_html_content(expanded_content)
			
			if not html_content:
				frappe.throw("AI Agent returned empty content")
			
			# Update the description field with expanded HTML content
			self.description = html_content
			
			# Save the document
			self.save()
			self.reload()
			
			frappe.msgprint("Description has been successfully expanded and optimized", indicator="green")
			
			return {
				"status": "success",
				"message": "Description content has been successfully expanded and optimized",
				"updated_description": self.description
			}
			
		except Exception as e:
			frappe.log_error(
				title="Gallery AI Expansion Error",
				message=f"AI Agent: {ai_agent_name}\n\nError: {str(e)}"
			)
			frappe.throw(f"Error expanding gallery description: {str(e)}")
	
	def _parse_ai_result(self, result):
		"""Parse AI Agent result into usable format"""
		if isinstance(result, str):
			try:
				return json.loads(result)
			except:
				return result
		elif hasattr(result, 'model_dump'):
			return result.model_dump()
		elif hasattr(result, 'dict'):
			return result.dict()
		elif isinstance(result, dict):
			return result
		else:
			return str(result)
	
	def _extract_html_content(self, parsed_result):
		"""Extract HTML content from AI result"""
		# If it's already a string (likely HTML), return it
		if isinstance(parsed_result, str):
			return parsed_result.strip()
		
		# If it's a dict, look for common content keys
		if isinstance(parsed_result, dict):
			# Try different possible keys
			for key in ['content', 'html', 'html_content', 'expanded_content', 'description']:
				if key in parsed_result:
					return str(parsed_result[key]).strip()
			
			# If no specific key found, try to get the first non-empty value
			for value in parsed_result.values():
				if value and isinstance(value, str) and len(value) > 50:
					return value.strip()
		
		# Last resort: convert to string
		return str(parsed_result).strip()

	@frappe.whitelist()
	def expand_gallery_description_with_instruction(self, custom_instruction):
		"""
		Expands gallery description with custom user instruction
		Approach with user-provided custom instruction
		"""
		try:
			# Hardcoded AI Agent name
			ai_agent_name = "Gallery Content Generator"
			
			# Get the AI agent
			ai_agent = frappe.get_doc("AI Agent", ai_agent_name)
			
			if not ai_agent:
				frappe.throw(f"AI Agent '{ai_agent_name}' not found")
			
			if not custom_instruction:
				frappe.throw("Custom instruction is required")
			
			# Prepare AI input data with custom instruction
			ai_input_data = {
				"existing_description": self.description or "",
				"title": self.title or "Gallery Item",
				"custom_instruction": custom_instruction
			}
			
			# Invoke the AI agent
			result = ai_agent.invoke(**ai_input_data)
   
			# Log the raw output for debugging
			frappe.log_error(
				title=f"AI Raw Output - {self.name}",
				message=str(result)
			)
			
			# Update the description field with expanded content
			self.description = result.content
			
			# Save the document
			self.save()
			self.reload()
			
			return {
				"status": "success",
				"message": "Description content has been successfully expanded with custom instructions"
			}
			
		except Exception as e:
			frappe.log_error(f"Error expanding gallery description with instruction: {str(e)}")
			return {
				"status": "error",
				"message": str(e)
			}
			
def get_list_context(context=None):
	list_context = frappe._dict(
		title = _('Gallery'),
		gallery_category = frappe.get_list("Gallery Category", ignore_permissions=True),
		# gallery_sub_category = frappe.get_doc("Gallery Sub Category", ignore_permissions=True),
		# gallery_sub_category = frappe.db.sql("""
			# select name,category, category_name
			# from `tabGallery Sub Category`
		# """),
		no_breadcrumbs = True,
		scrub = frappe.scrub
	)

	return list_context