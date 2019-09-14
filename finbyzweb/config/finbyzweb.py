from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Customer"),
			"items": [
				{
					"type": "doctype",
					"name": "Customer Details",
				},
			]
		},
		{
			"label": _("Documents"),
			"items": [
				{
					"type": "doctype",
					"name": "Gallery",
				},

			]
		},
		{
			"label": _("Web Site"),
			"items": [
				{
					"type": "doctype",
					"name": "Web Page",
				},
				{
					"type": "doctype",
					"name": "Web Form",
				},
				{
					"type": "doctype",
					"name": "About Us Settings",
				},
				{
					"type": "doctype",
					"name": "Contact Us Settings",
				},
				{
					"type": "doctype",
					"name": "Website Settings",
				},
			]
		}
	]