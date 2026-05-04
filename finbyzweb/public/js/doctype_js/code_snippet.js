frappe.ui.form.on('Code Snippet', {
    refresh: function (frm) {
        if (!frm.doc.is_nextjs_page_generated) {
            frm.add_custom_button(__('NextJS Page'), function () {

                if (!frm.doc.snippet_name) {
                    frappe.msgprint({
                        title: 'Missing Field',
                        message: 'snippet_name is required to generate NextJS Page.',
                        indicator: 'red'
                    });
                    return;
                }
                let dialog = new frappe.ui.Dialog({
                    title: "Generate NextJS Page",
                    fields: [
                        {
                            fieldname: "instruction",
                            fieldtype: "Small Text",
                            label: "Instruction",
                            default: "",
                            reqd: 0,
                        },
                    ],
                    primary_action_label: "Generate",
                    primary_action: function () {
                        frappe.call({
                            method: 'finbyzweb.nextjs_page_api.generate_nextjs_page',
                            args: { name: frm.doc.name, instruction: dialog.fields_dict.instruction.get_value() },
                            freeze: true,
                            freeze_message: 'Generating NextJS Page...',
                            callback: function (r) {
                                dialog.hide();
                                if (r && r.message) {
                                    if (r.message.success) {
                                        let data = r.message.doc_data;
                                        frappe.new_doc('NextJS Page', {
                                            title: data.title,
                                            route: data.route,
                                            actual_route: data.actual_route,
                                            meta_title: data.meta_title,
                                            meta_description: data.meta_description,
                                            keywords: data.keywords,
                                            image: data.image,
                                            content: data.content,
                                            content_type: data.content_type,
                                            page_type: data.page_type,
                                            parent_nextjs_page: data.parent_nextjs_page,
                                            source_code_snippet: frm.doc.name
                                        });

                                    } else {
                                        frappe.msgprint({
                                            title: 'Info',
                                            message: r.message.message,
                                            indicator: 'orange'
                                        });
                                        if (r.message.redirect) {
                                            window.location.href = r.message.redirect;
                                        }
                                    }
                                }
                            }
                        });
                    }
                });
                dialog.show();
            }, __('Create'));
        }

        if (frm.doc.published) {
            frm.add_custom_button(__('View Published Page'), async function () {
                let resp = await frappe.db.get_value('NextJS Page', frm.doc.nextjs_page, 'actual_route');
                let route_url = 'https://finbyz.tech/' + resp.message.actual_route;
                window.open(route_url, '_blank');
            });
        }
    }
});