frappe.ready(function() {
	frappe.web_form.set_df_property("assigned_to", "reqd", 0);
    frappe.web_form.set_df_property("project", "reqd", 0);
});

frappe.web_form.after_load = () => {
    frappe.web_form.doc.time_involvement_table.forEach(d => {
        d.user_name = d.full_name;
    });

    frappe.web_form.refresh();
}
