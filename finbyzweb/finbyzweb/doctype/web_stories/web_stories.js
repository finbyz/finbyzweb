// Copyright (c) 2024, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Web Stories", {
	refresh(frm) {

	},
});


frappe.ui.form.on("Detail Web Stories", {
    image: async function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let imageUrl = row.image;

        if (imageUrl) {
            let img = new Image();
            img.src = imageUrl;
            await img.decode();
            frappe.model.set_value(cdt, cdn, "height", flt(img.height));
            frm.refresh_fields("details_web_stories");
            
        }
    }
});
