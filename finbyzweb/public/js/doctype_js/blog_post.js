frappe.ui.form.on('Blog Post', {
    refresh: function(frm) {
        if (frm.doc.published && !frm.is_new()) {

            // --------------------------------------------
            // Generate FAQs Button
            // --------------------------------------------
            frm.add_custom_button(__('Generate FAQs'), function() {
                frappe.confirm(
                    'This will generate FAQs using AI and replace existing FAQs. Continue?',
                    function() {
                        frappe.call({
                            method: 'finbyzweb.faqs_api.generate_faqs',
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
            }, __('AI Tools')); // ✅ Grouped under "AI Tools"

            // --------------------------------------------
            // Generate Related Content Button
            // --------------------------------------------
            frm.add_custom_button(__('Fetch Related Links'), function() {
                frappe.call({
                    method: 'finbyzweb.fetch_related_links.generate_related_content',
                    args: {
                        doctype: 'Blog Post', // ✅ Changed from Web Page to Blog Post
                        docname: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __('Generating related links...'),
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Related links generated successfully!'),
                                indicator: 'green'
                            }, 5);
                            frm.reload_doc();
                        }
                    }
                });
            }, __('AI Tools')); // ✅ Same group as FAQs
        }
    }
});
