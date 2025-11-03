// cur_frm.fields_dict.related_links.grid.get_field("reference_doctype").get_query = function (doc) {
//     return {
//         filters: {
//             "has_web_view": 1,
//         }
//     }
// };

cur_frm.cscript.onload = function (frm) {
    this.frm.set_query("reference_name", "related_links", function (doc,cdt,cdn) {
        let d = locals[cdt][cdn];
        return {
            query:"finbyzweb.api.related_link_query",
            filters: {
                "reference_doctype": d.reference_doctype
            }
        }
    });
}

// cur_frm.fields_dict.related_links.grid.get_field("reference_name").get_query = function (doc, cdt, cdn) {
//     let d = locals[cdt][cdn]
//     console.log(d.fields_dict.company))
//     if (frappe.meta.get_docfield(d.reference_doctype, 'published')) {
//         return {
//             filters: {
//                 "published": 1,
//             }
//         }
//     }
// };
frappe.ui.form.on("Web Page", {
    refresh: function (frm) {
        // Add a custom button to generate the web page
        frm.add_custom_button(__('Generate Page'), function() {
            generatePage(frm);
        });

        // Add a custom button to generate FAQs if the document is published and not new
        if (frm.doc.published && !frm.is_new()) {
            frm.add_custom_button(__('Generate FAQs'), function() {
                frappe.confirm(
                    'This will generate FAQs using AI and replace existing FAQs. Continue?',
                    function() {
                        frappe.call({
                            method: 'finbyzweb.api.generate_faqs',
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
            });
        }
    },

    before_load: function (frm) {
        var df = frappe.meta.get_docfield("Related Links", 'title',frm.doc.name);
       // console.log(df)
        frm.refresh_fields();
    }
});