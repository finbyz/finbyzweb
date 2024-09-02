# Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

# import frappe
from frappe.website.website_generator import WebsiteGenerator
import frappe


class WebStories(WebsiteGenerator):
    def validate(self):
        self.make_route()
        WebsiteGenerator.validate(self)
        
    def make_route(self):
        """Make website route"""
        if self.route:
            return

        self.route = self.scrub(self.title)
        return self.route

