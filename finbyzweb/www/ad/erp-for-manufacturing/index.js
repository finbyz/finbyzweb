async function lead_creation() {
    frappe.msgprint("sent");
    frappe.call({
        method: "finbyzweb.api.set_form_data",
        args: {
            'lead_name': $('#lead_name').val(),
            'company_name': $('#company_name').val(),
            'mobile_no': $('#mobile_no').val(),
            'title': document.title + '</br>' + window.location.href,
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
