// Copyright (c) 2023, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Finbyz Backlinks"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"for_page_type",
			"label": __("For Page Type"),
			"fieldtype": "Link",
			"options": "DocType",
			get_query: () => {
				var list_doc = frappe.query_report.get_filter_value('for_page_type');
				return {
					filters: {
						'name':["in",["Web Page","Blog Post"]],
					}
				};
			}
		},
		{
			"fieldname":"for_page",
			"label": __("For Page"),
			"fieldtype": "Dynamic Link",
			"options": "for_page_type",
		},
		{
			"fieldname":"type",
			"label": __("type"),
			"fieldtype": "Select",
			"width": "80",
			"options": ["","Social Bookmarking","PPT Sharing","Blog Submission","Image Sharing","Comments","Classified Ads","Profile Creation","Local Listing","Blog Bookmarking"] 
		},
	],
};
