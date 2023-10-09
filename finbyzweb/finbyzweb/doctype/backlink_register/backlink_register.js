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
		
	},
	refresh:function(frm)
	{
		frm.set_query("for_page_type", function() {
			return {
			  filters: [
				['name','In', ["Web Page","Blog Post"]]
			  ]
			};
		  });
	},
	live_backlinks:function(frm)
	{
		frm.call({
			method:'finbyzweb.finbyzweb.doctype.backlink_register.backlink_register.live_backlinks_validate',
			args:{
				msg:frm.doc.live_backlinks
			},
			callback:function(r){
				console.log(r)
				if(r.message)
				{
					
					if(r.message.domain_authority)
					{
						frm.set_value('domiain_authority',r.message.domain_authority);
					}
					if(r.message.domain_name)
					{
						frm.set_value('domain',r.message.domain_name);
					}
				}
				else{
					frm.set_value('domiain_authority',"");
					frm.set_value('domain',"");
				}
			}
		});
	}
});
