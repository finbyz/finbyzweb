// Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('NextJS Data Import', {
	refresh: function (frm) {
		if (frm.doc.status === "Processing") {
			frm.disable_save();
		}

		// Listen for realtime updates
		frappe.realtime.on("import_progress", function (data) {
			if (data.message) {
				frappe.show_alert({ message: data.message, indicator: 'blue' });
			}
		});
	},
	submit_action: function (frm) {
		if (frm.doc.status === "Processing") {
			frappe.msgprint("Import is already in progress.");
			return;
		}

		frappe.confirm(
			'Are you sure you want to start the import process?',
			function () {
				frappe.call({
					method: 'finbyzweb.nextjs_web.doctype.nextjs_data_import.nextjs_data_import.start_import',
					args: {
						docname: frm.doc.name
					},
					freeze: true,
					freeze_message: 'Importing Data...',
					callback: function (r) {
						frm.reload_doc();
						if (!r.exc) {
							frappe.show_alert({
								message: 'Import completed successfully!',
								indicator: 'green'
							}, 5);
						}
					},
					error: function (r) {
						frappe.msgprint({
							title: 'Import Failed',
							message: 'An error occurred during import. Check the log for details.',
							indicator: 'red'
						});
						frm.reload_doc();
					}
				});
			}
		);
	}
});
