// // Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
// // For license information, please see license.txt

frappe.ui.form.on('Gallery', {
	refresh: function(frm) {
		// --- AI Description Expander ---
		if (!frm.is_new()) {
			frm.add_custom_button(__('Expand Description with AI'), function() {
				expand_gallery_description(frm);
			}, __('AI Actions'));
		}

		// --- Generate FAQs Button ---
		if (!frm.is_new()) {
			frm.add_custom_button(__('Generate FAQs'), function() {
				frappe.confirm(
					'This will generate FAQs using AI. Do you want to continue?',
					function() {
						frappe.call({
							method: 'finbyzweb.api.generate_faqs',
							args: {
								doctype: 'Gallery',
								docname: frm.doc.name
							},
							freeze: true,
							freeze_message: __('Generating FAQs for this gallery...'),
							callback: function(r) {
								if (r.message && r.message.success) {
									frm.reload_doc();
								}
							}
						});
					}
				);
			}, __('AI Actions'));
		}

		// --- Generate Related Content Button ---
		if (!frm.is_new()) {
			frm.add_custom_button(__('Fetch Related Links'), function() {
				frappe.confirm(
					'This will generate related content using AI. Do you want to continue?',
					function() {
						frappe.call({
							method: 'finbyzweb.fetch_related_links.generate_related_content',
							args: {
								doctype: 'Gallery', // ✅ Corrected for Gallery
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
					}
				);
			}, __('AI Actions'));
		}
	}
});

/**
 * Function to expand the gallery description using AI.
 * @param {object} frm - The current form object.
 */
function expand_gallery_description(frm) {
	frappe.confirm(
		__('This will use AI to expand and optimize the gallery description. Continue?'),
		function() {
			frappe.show_alert({
				message: __('Expanding description with AI...'),
				indicator: 'blue'
			}, 3);

			frm.disable_save();

			frappe.call({
				method: 'expand_gallery_description',
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
						frm.reload_doc();
					} else if (r.message && r.message.status === 'error') {
						frappe.msgprint({
							title: __('Error'),
							message: r.message.message,
							indicator: 'red'
						});
					}
				},
				error: function() {
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
			frappe.show_alert({
				message: __('Action cancelled'),
				indicator: 'orange'
			}, 2);
		}
	);
}
