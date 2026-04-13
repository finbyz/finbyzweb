from frappe import _
import frappe
from frappe.model.document import Document
import json
import string
import random
from uuid import uuid4


class EmployeeJoiningDetail(Document):

	def validate(self):

		first_name = self.first_name or ""
		middle_name = self.middle_name or ""
		last_name = self.last_name or ""

		employee_name = " ".join([first_name, middle_name, last_name]).strip()

		self.employee_name = employee_name
	
	def before_insert(self):
		self.random_token()
		self.generate_url()

	def random_token(self): 
		N = 32
		res = uuid4()
		self.token = str(res)
	
	def generate_url(self):
		self.url = f"https://erp.finbyz.tech/employee-joining-details?token={self.token}"


	@frappe.whitelist()
	def create_employee(self, employee_joining_detail_id, employee_name):
		joining_detail = frappe.get_doc("Employee Joining Detail", employee_joining_detail_id)

		new_employee = frappe.get_doc({
			"doctype": "Employee",
			"employee_name": employee_name,  
			"first_name": joining_detail.first_name,
			"middle_name": joining_detail.middle_name,
			"last_name": joining_detail.last_name,
			"date_of_birth": joining_detail.date_of_birth,
			"personal_email": joining_detail.personal_email,
			"gender": joining_detail.gender,
			"date_of_joining": joining_detail.date_of_joining,
			"bank_name": joining_detail.bank_name,
			"bank_ac_no": joining_detail.bank_ac_no,
			"ifsc_code": joining_detail.ifsc_code,
			"pan_number": joining_detail.pan_number,
			"cell_number": joining_detail.cell_number,
			"current_address": joining_detail.current_address,
			"salary_mode": joining_detail.salary_mode,
			"marital_status": joining_detail.marital_status,
			"blood_group": joining_detail.blood_group,
			"department": joining_detail.department,
			"designation": joining_detail.designation,
			"company_email": joining_detail.company_email,
			"salutation": joining_detail.salutation,
			"employment_type": joining_detail.employment_type,
		})
		if joining_detail.is_intern:
			new_employee.naming_series = "INT/"

		new_employee.insert() 
		frappe.db.commit()
		
		employee_link = frappe.utils.get_url_to_form("Employee", new_employee.name)
		return _("Employee record created successfully. <a href='{0}' target='_blank'>{1}</a>").format(employee_link, new_employee.first_name)

	@frappe.whitelist()
	def send_email(self, email):
		subject = "Employee Joining Confirmation"
		message = f"""
			<p>Dear {self.employee_name},</p>
			<p>Welcome to Finbyz Tech Pvt. Ltd!</p>
			<p>We are thrilled to have you on board and look forward to working together.</p>
			<p>As part of our onboarding process, we kindly request you to submit the following documents to complete the necessary formalities. Please ensure that all requested information is accurate and up-to-date:</p>
			<p>Your joining details have been verified. Kindly fill in the further details using the following link:</p>
			<p><a href="{self.url}">Fill Further Details</a></p>
			<p>If you have any questions or need assistance during the onboarding process, please do not hesitate to reach out to us at <a href="mailto:info@finbyz.tech">info@finbyz.tech</a>.</p>
			<p>Best Regards,</p>
			<p>Finbyz Tech Pvt. Ltd.</p>
		"""

		frappe.sendmail(
				recipients=email,
				subject=subject,
				message=message,
			)
		return _("Email sent successfully!")

@frappe.whitelist(allow_guest=True)
def get_employee_joining_detail_fields():
	meta = frappe.get_meta("Employee Joining Detail")
	fields = meta.fields
	return fields

from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def update_employee_data():
	"""
	Updates the Employee Joining Detail document based on the token provided in the URL.
	Handles both dynamic field updates and file uploads.
	"""
	data = frappe.local.form_dict  # Retrieve data from the request
	token = data.get("token")

	if not token:
		frappe.throw("Token is required.")

	# Fetch the document using the token
	try:
		doc = frappe.get_doc("Employee Joining Detail", {"token": token, "status": "Pending"})
	except Exception as e:
		frappe.throw("Document not found for the given token.")

	# Dynamically update fields based on the provided data
	for field, value in data.items():
		if hasattr(doc, field):  # Check if the field exists in the document
			setattr(doc, field, value)

	# Handle file uploads (attachments)
	if frappe.request.files:
		for fieldname, file in frappe.request.files.items():
			if file.filename:
				# raise Exception(str(fieldname) + str(file.filename))
				# Save the file and link it to the document
				file_doc = save_file(file.filename, file.stream.read(), doc.doctype, doc.name, decode=False, is_private=0)
				if hasattr(doc, fieldname):  # Check if the field exists in the document
					setattr(doc, fieldname, file_doc.file_url)  # Save the file URL to the document field

	try:
		# Save changes while ignoring permissions
		doc.save(ignore_permissions=True)
		doc.generate_url()
		doc.save(ignore_permissions=True)
		frappe.db.commit()  # Commit the transaction
		return {"message": "Document updated successfully."}
	except Exception as e:
		frappe.log_error(message=str(e), title="Error Updating Document")
		frappe.throw(f"Failed to update Employee Data: {str(e)}")

@frappe.whitelist(allow_guest=True)
def get_employee_data(token):
	try:
		# Find the document using the token
		doc = frappe.get_doc("Employee Joining Detail", {"token": token})
		
		# Return the required data if document is found
		return {
			"name": doc.name,
			"first_name": doc.first_name,
			"last_name": doc.last_name,
			"personal_email": getattr(doc, 'personal_email', None),
			"token": doc.token,
			"applicant_type":doc.applicant_type
		}
	except frappe.DoesNotExistError:
		# Handle the case where no document is found for the given token
		frappe.throw("Document not found for the given token.")
