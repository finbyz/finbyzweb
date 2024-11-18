	
	// frappe.web_form.validate = () => {
	// 	const ifscValue = frappe.web_form.get_value("ifsc_code");
	// 	const panValue = frappe.web_form.get_value("pan_number");
	
	// 	// IFSC Code Validation
	// 	const ifscPattern = /^[A-Z]{4}0[A-Z0-9]{6}$/;
	// 	if (!ifscPattern.test(ifscValue)) {
	// 		frappe.msgprint("Please enter a valid IFSC code. It should start with 4 uppercase letters followed by '0' and 6 alphanumeric characters.");
	// 		return false; 
	// 	}
	
	// 	// PAN Number Validation
	// 	const panPattern = /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/;
	// 	if (!panPattern.test(panValue)) {
	// 		frappe.msgprint("Please enter a valid PAN number. It should have 5 uppercase letters, followed by 4 digits, and ending with 1 uppercase letter.");
	// 		return false; 
	// 	}
	
	// 	return true; 
	// },  
