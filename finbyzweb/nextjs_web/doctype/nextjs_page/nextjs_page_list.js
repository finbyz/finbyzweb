frappe.listview_settings['NextJS Page'] = {
    add_fields: ["is_published", "page_type"],
    onload: function (listview) {
        listview.page.add_inner_button(__("Draft Content with AI"), function () {
            let d = new frappe.ui.Dialog({
                title: __('Draft Content'),
                fields: [
                    {
                        label: __('What is this page about?'),
                        fieldname: 'user_input',
                        fieldtype: 'Small Text',
                        reqd: 1,
                        description: __('Explain the topic or content of the new page briefly.')
                    }
                ],
                primary_action_label: __('Generate & Create'),
                primary_action(values) {
                    d.hide();
                    frappe.call({
                        method: 'finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.create_page_from_ai',
                        args: {
                            user_input: values.user_input
                        },
                        freeze: true,
                        freeze_message: __('AI is generating your page...'),
                        callback: function (r) {
                            if (!r.message) return
                            frappe.new_doc("NextJS Page", r.message)
                        }
                    });
                }
            });
            d.show();
        });
    }
};
