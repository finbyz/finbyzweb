// Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Employee Joining Detail", {
    refresh: function(frm) {
        if (frm.doc.status !== "Verified") {
            frm.add_custom_button(__("Verify"), function() {
                frm.set_value("status", "Verified");
                frm.save();
            });
        }
        
        frm.add_custom_button(__("Make Employee"), function() {
            const employeeName = [frm.doc.first_name, frm.doc.middle_name, frm.doc.last_name]
                .filter(name => !!name)  
                .join(" ");  

            frappe.call({
                doc: frm.doc,
                method: "create_employee",
                args: {
                    employee_joining_detail_id: frm.doc.name,
                    employee_name: employeeName  
                },
                callback: function(response) {
                    frappe.msgprint(response.message);
                },
                error: function(err) {
                    frappe.msgprint(__("An error occurred while creating the Employee record."));
                    console.error(err);
                }
            });
        });
        frm.add_custom_button(__("Send Email"), function() {
            if (frm.doc.personal_email) {
                console.log("Sending email to:", frm.doc.personal_email);
                
                frappe.call({
                    doc: frm.doc,
                    method: "send_email",
                    args: {
                        email: frm.doc.personal_email  
                    },
                    callback: function(response) {
                        frappe.msgprint(response.message);
                    },
                    error: function(err) {
                        console.error("Error sending email:", err); 
                        frappe.msgprint(__("An error occurred while sending the email."));
                    }
                });
            } else {
                frappe.msgprint(__("Please provide a personal email address to send the email."));
            }
        });
    },
    
    first_name: function(frm) {
        update_employee_name(frm);
    },
    middle_name: function(frm) {
        update_employee_name(frm);
    },
    last_name: function(frm) {
        update_employee_name(frm);
    },
    validate: function(frm) {
        update_employee_name(frm);  
    }
});

function update_employee_name(frm) {
    const firstName = frm.doc.first_name || "";
    const middleName = frm.doc.middle_name || "";
    const lastName = frm.doc.last_name || "";

    frm.set_value("employee_name", [firstName, middleName, lastName].filter(name => name).join(" "));
}
