// Copyright (c) 2023, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Backlink Register', {
	for_page:function(frm)
	{
		var selected_doctype=frm.doc.for_page_type;
		var selected_entry=frm.doc.for_page;
		frappe.db.get_value(selected_doctype,selected_entry , "route",function(r)
		{
			if(r.route)
			{
				frm.set_value("submitted_url",`https://finbyz.tech/${r.route}`)
			}
		})
		
	}
});
