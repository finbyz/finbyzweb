// Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gallery', {
	refresh: function(frm) {
		// --- AI Description Expander ---
		if (!frm.is_new()) {
			// This button will be placed in the "AI Actions" dropdown menu.
			frm.add_custom_button(__('Expand Description with AI'), function() {
				expand_gallery_description(frm);
			}, __('AI Actions'));
		}

		// --- "Generate FAQs" button ---
		// MODIFIED: This button will now appear as long as the document is saved,
		// regardless of its 'published' status.
		if (!frm.is_new()) {
			frm.add_custom_button(__('Generate FAQs'), function() {
				// Ask for confirmation before proceeding
				frappe.confirm(
					'This will generate FAQs using AI. Do you want to continue?',
					function() {
						// Call the backend Python function
						frappe.call({
							method: 'finbyzweb.api.generate_faqs', // Path to your Python function
							args: {
								doctype: 'Gallery',         // Pass 'Gallery' as the doctype
								docname: frm.doc.name       // Pass the current document's name
							},
							freeze: true,
							freeze_message: __('Generating FAQs for this gallery...'),
							callback: function(r) {
								// If the call is successful, reload the form to show the new FAQs
								if (r.message && r.message.success) {
									frm.reload_doc();
								}
								// Note: The Python script will show an error if the doc is not published.
							}
						});
					}
				);
			});
		}
	}
});

/**
 * Function to expand the gallery description using an AI call.
 * This remains unchanged from your original script.
 * @param {object} frm - The current form object.
 */
function expand_gallery_description(frm) {
	// Show confirmation dialog
	frappe.confirm(
		__('This will use AI to expand and optimize the gallery description. Continue?'),
		function() {
			// User confirmed
			frappe.show_alert({
				message: __('Expanding description with AI...'),
				indicator: 'blue'
			}, 3);

			// Disable the form while processing
			frm.disable_save();

			// Call the server method
			frappe.call({
				method: 'expand_gallery_description', // Assumes this is a whitelisted Python method
				doc: frm.doc,
				freeze: true,
				freeze_message: __('AI is generating content...'),
				callback: function(r) {
					frm.enable_save();

					if (r.message && r.message.status === 'success') {
						frappe.show_alert({
							message: r.message.message,
							indicator: 'green'
						}, 5);

						// Refresh the form to show updated description
						frm.reload_doc();
					} else if (r.message && r.message.status === 'error') {
						frappe.msgprint({
							title: __('Error'),
							message: r.message.message,
							indicator: 'red'
						});
					}
				},
				error: function(r) {
					frm.enable_save();
					frappe.msgprint({
						title: __('Error'),
						message: __('Failed to expand description. Please check the error log.'),
						indicator: 'red'
					});
				}
			});
		},
		function() {
			// User cancelled
			frappe.show_alert({
				message: __('Action cancelled'),
				indicator: 'orange'
			}, 2);
		}
	);
}