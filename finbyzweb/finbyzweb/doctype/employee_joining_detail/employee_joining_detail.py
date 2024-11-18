from frappe import _
import frappe
from frappe.model.document import Document

class EmployeeJoiningDetail(Document):

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
        })

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
            <p><a href="https://website.finbyz.com/employee-joining-detail?email={email}">Fill Further Details</a></p>
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