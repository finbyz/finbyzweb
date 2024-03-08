async function lead_creation() {
    frappe.msgprint("sent");
    frappe.call({
        method: "finbyzweb.api.set_form_data",
        args: {
            'lead_name': $('#lead_name').val(),
            'company_name': $('#company_name').val(),
            'mobile_no': $('#mobile_no').val(),
            'title': window.location.href,
            'email': $('#email').val()
        },
        callback: function (r) {
            $('#lead_name').val('');
            $('#company_name').val('');
            $('#mobile_no').val('');
            $('#email').val('');
        }
    });
};

var form = $('#inquiry-ad'),
    submit = form.find('[name="submit"]');

form.on('submit', async function (e) {
    await lead_creation();
    window.location.href = "/thank-you-for-inquiry";
    // let label = $('.inquiry-label');
    // label.removeClass('show');
    e.preventDefault();
});
function submitLead() {
    // Get form data
    var name = document.getElementById('name').value;
    var email = document.getElementById('email').value;

    // Check if email already exists
    frappe.call({
        method: 'finbyzweb.finbyzweb.',
        args: { email: email },
        callback: function(response) {
            if (response.message) {
                alert('Lead with this email already exists!');
            } else {
                // Lead doesn't exist, submit the form
                frappe.call({
                    method: 'your_custom_method_to_create_lead',
                    args: { name: name, email: email },
                    callback: function(response) {
                        alert('Lead created successfully!');
                        // Additional actions after successful submission
                    }
                });
            }
        }
    });
}
