frappe.listview_settings['Backlink Register'] = {

	onload: function(listview) {
		if (listview.page.fields_dict.for_page_type) {
			listview.page.fields_dict.for_page_type.get_query = function() {
				return {
					"filters": {
						"name": ["in",["Web Page","Blog Post"]],
					}
				};
			};
		}
	}
};