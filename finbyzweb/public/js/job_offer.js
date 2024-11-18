frappe.ui.form.on("Job Offer", {
    refresh: function(frm) {
        if (frm.doc.status === "Accepted") {
            frm.add_custom_button(__("Send to Employee Joining Detail"), function() {
                frappe.call({
                    method: "finbyzweb.finbyzweb.doc_events.job_offer.send_to_employee_joining_detail",
                    args: {
                        job_offer_id: frm.doc.name
                    },
                    callback: function(response) {
                        if (response.message) {
                            frappe.msgprint(__("Employee Joining Detail created successfully."));
                        } else {
                            frappe.msgprint(__("Failed to create Employee Joining Detail."));
                        }
                    },
                    error: function(err) {
                        frappe.msgprint(__("An error occurred while sending data."));
                        console.error(err);
                    }
                });
            });
        }
    }
});
