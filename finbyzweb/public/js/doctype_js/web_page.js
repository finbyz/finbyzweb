cur_frm.cscript.onload = function (frm) {
    this.frm.set_query("reference_name", "related_links", function (doc, cdt, cdn) {
        let d = locals[cdt][cdn];
        return {
            query: "finbyzweb.api.related_link_query",
            filters: {
                "reference_doctype": d.reference_doctype
            }
        };
    });
};
frappe.ui.form.on("Web Page", {
    refresh: function (frm) {
        // --------------------------------------------
        // Generate Page Button
        // --------------------------------------------
        frm.add_custom_button(__('Generate Page'), function() {
            generatePage(frm);
        });

        // --------------------------------------------
        // Generate FAQs Button
        // --------------------------------------------
        if (frm.doc.published && !frm.is_new()) {
            frm.add_custom_button(__('Generate FAQs'), function() {
                frappe.confirm(
                    'This will generate FAQs using AI and replace existing FAQs. Continue?',
                    function() {
                        frappe.call({
                            method: 'finbyzweb.faqs_api.generate_faqs',
                            args: {
                                doctype: 'Web Page',
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
            }, __('AI Tools')); // ✅ Grouped under “AI Tools”
        }

        // --------------------------------------------
        // Generate Related Content Button (New)
        // --------------------------------------------
        if (frm.doc.published && !frm.is_new()) {
            frm.add_custom_button(__('Fetch Related Links'), function() {
                frappe.call({
                    method: 'finbyzweb.fetch_related_links.generate_related_content',
                    args: {
                        doctype: 'Web Page',
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

        // --------------------------------------------
        // Update SEO Content Button
        // --------------------------------------------
        frm.add_custom_button(__('Update SEO Content'), function() {
            show_seo_update_dialog(frm);
        }, __('AI Tools')); // ✅ Also grouped under “AI Tools”
    },

    before_load: function (frm) {
        var df = frappe.meta.get_docfield("Related Links", 'title', frm.doc.name);
        frm.refresh_fields();
    }
});

// ================================================
// SEO Update Dialog Function
// ================================================
function show_seo_update_dialog(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Update SEO Content'),
        fields: [
            {
                label: __('Website URL'),
                fieldname: 'url',
                fieldtype: 'Data',
                reqd: 1,
                description: __('Enter the website URL to scrape content from')
            },
            {
                label: __('Instructions'),
                fieldname: 'instructions',
                fieldtype: 'Small Text',
                reqd: 1,
                description: __('Provide specific instructions for SEO optimization')
            }
        ],
        size: 'large',
        primary_action_label: __('Submit'),
        primary_action(values) {
            frappe.show_alert({
                message: __('Processing SEO update...'),
                indicator: 'blue'
            });

            frappe.call({
                method: 'finbyzweb.update_seo_content.update_seo_content',
                args: {
                    docname: frm.doc.name,
                    url: values.url,
                    instructions: values.instructions
                },
                freeze: true,
                freeze_message: __('Updating SEO content with AI...'),
                callback: function(r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __('SEO content updated successfully!'),
                            indicator: 'green'
                        }, 5);
                        frm.reload_doc();
                        d.hide();
                        frappe.msgprint({
                            title: __('Updated SEO Content'),
                            message: `
                                <strong>SEO Title:</strong><br>${r.message.seo_title}<br><br>
                                <strong>SEO Description:</strong><br>${r.message.seo_description}<br><br>
                                <strong>Keywords:</strong><br>${r.message.keywords}
                            `,
                            indicator: 'green'
                        });
                    }
                },
                error: function() {
                    frappe.show_alert({
                        message: __('Failed to update SEO content'),
                        indicator: 'red'
                    }, 5);
                }
            });
        }
    });
    d.show();
}
