frappe.ui.form.on('Blog Post', {
    refresh: function(frm) {
        if (frm.doc.published && !frm.is_new()) {
            frm.add_custom_button(__('Generate FAQs'), function() {
                frappe.confirm(
                    'This will generate FAQs using AI and replace existing FAQs. Continue?',
                    function() {
                        frappe.call({
							method: 'finbyzweb.api.generate_faqs',
							args: {
								doctype: 'Blog Post',
								docname: frm.doc.name
							},
							freeze: true,
							freeze_message: __('Generating FAQs...'),
							callback: function(r) {
								if (r.message && r.message.success) {
									frm.reload_doc();
								}
							}
						});
					}
				);
			});
		}
	}
});