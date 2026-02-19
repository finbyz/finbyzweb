from __future__ import unicode_literals
import time
import frappe

@frappe.whitelist()
def customer_before_save(self, method):
	doc = frappe.get_single("Customer Details")
	doc.ignore_permissions = True

	if self.show_on_website:
		if not frappe.db.exists("Customer Details List", {'customer': self.customer_name}):
			doc.append('customer_details_list', {
					'customer': self.customer_name,
					'image': self.image
				})
			doc.save()

	else:
		if frappe.db.exists("Customer Details List", {'customer': self.customer_name}):
			to_remove = [row for row in doc.get('customer_details_list') if row.customer == self.customer_name]
			[doc.remove(row) for row in to_remove]
			doc.save()

	frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def get_customer_details():
    """
    API to fetch all customer names and their images
    from the 'Customer Details' doctype's child table 'customer_details_list'.
    Returns only `customer` and `image` fields.
    """
    try:
        # Get singleton document
        doc = frappe.get_single("Customer Details")

        if not doc or not doc.get("customer_details_list"):
            return {
                "success": True,
                "data": [],
                "message": "No customer details found."
            }

        # Prepare simplified data
        customer_list = []
        for row in doc.customer_details_list:
            customer_list.append({
                "customer": row.customer,
                "image": row.image
            })

        return {
            "success": True,
            "data": customer_list
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_customer_details API Error")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True,methods='POST')
def set_form_contact_data(lead_name, company_name, mobile_no, title, email,notes):
	# frappe.log_error('data',f'{lead_name, company_name, mobile_no, title, email,notes}')
	data = frappe.new_doc("Lead")
	data.lead_name = lead_name
	data.company_name = company_name
	data.mobile_no = mobile_no
	data.source = 'Website'
	data.source_web_page = title
	data.email_id = email
	data.message = notes
	data.set_user_and_timestamp


	
@frappe.whitelist(allow_guest=True)
def set_form_data(lead_name, company_name, mobile_no, title, email):

    data = frappe.new_doc("Lead")
    data.lead_name = lead_name
    data.company_name = company_name
    data.mobile_no = mobile_no
    data.source = 'Website'
    data.source_web_page = title
    data.email_id = email
    data.save(ignore_permissions=True)

    frappe.db.commit()

@frappe.whitelist(allow_guest=True)
def related_link_query(doctype, txt, searchfield, start, page_len, filters):
	cond = ""
	args = {

	}
	meta = frappe.get_meta(filters.get("reference_doctype"))
	if meta.get_field('published'):
		return frappe.db.sql("""select name
				from `tab{ref_doc}` where published = 1 and `{key}` LIKE %(txt)s {cond}
			"""
			.format(ref_doc=filters.get("reference_doctype"), key=searchfield, cond=cond), {
				'txt': '%' + txt + '%',
			})
	else:
		return frappe.db.sql("""select name
				from `tab{ref_doc}` where `{key}` LIKE %(txt)s {cond}
			"""
			.format(ref_doc=filters.get("reference_doctype"), key=searchfield, cond=cond), {
				'txt': '%' + txt + '%',
			})
	
def add_preload_headers(response):
	pass

@frappe.whitelist(allow_guest=True)
def select_category(gallery_category=None,gallery_sub_category=None):
	condition = ""
	if str(gallery_category) != "All":
		condition += f"where gallery_category ='{gallery_category}'"
	if gallery_sub_category:
		condition += f"and gallery_sub_category ='{gallery_sub_category}'"
	result = frappe.db.sql(f"""select * from `tabGallery` {condition}""", as_dict = 1)

	output = ""
	for row in result:
		doc_dict = {'doc' :row}
		output += frappe.render_template("finbyzweb/doctype/gallery/templates/gallery_row.html", doc_dict)
	return output

@frappe.whitelist(allow_guest=True)
def get_sub_category(category=None):
	output = frappe.db.get_all('Gallery Sub Category',filters={'category':category},fields=['name','category'])
	return output


@frappe.whitelist(allow_guest=True)
def get_employee_joining_detail(token):
	if not frappe.db.exists("Employee Joining Detail", {"token": token}):
		frappe.throw(_("You are not authorized to view this record!"))
		return
	joining_detail = frappe.get_doc("Employee Joining Detail", {"token": token})
	return joining_detail.as_dict()

from frappe import _
@frappe.whitelist(allow_guest=True,methods=['POST'])
def update_employee_joining_detail(email,data):
	"""
	ENDPOINT: /api/method/finbyzweb.api.update_employee_joining_detail
	"""
	data = frappe.parse_json(data)
	if not frappe.db.exists("Employee Joining Detail", {"personal_email": email}):
		frappe.throw(_("You are not authorized to update this record!"))
		return
	joining_detail = frappe.get_doc("Employee Joining Detail", {"personal_email": email})
	joining_detail.update(data)
	joining_detail.flags.ignore_permissions = True
	joining_detail.save()
	return _("Updated successfully!")

@frappe.whitelist()
def generate_page(content):
    """
    Call external API to generate page and return the response
    """
    try:
        # Validate content
        if not content or not content.strip():
            frappe.throw("Content cannot be empty")
        
        # Primary endpoint(s). Can be overridden via site_config.json:
        #   "web_page_generator_url": "https://example.com/api/generate-page"
        # or as a list of endpoints
        default_url = "https://web.finbyz.tech/api/generate-page"
        config_url = frappe.conf.get("web_page_generator_url")
        urls = []
        if isinstance(config_url, (list, tuple)):
            urls = [str(u).strip().rstrip('/') for u in config_url if str(u).strip()]
        elif isinstance(config_url, str) and config_url.strip():
            urls = [config_url.strip().rstrip('/')]
        else:
            urls = [default_url.rstrip('/')]
        
        # If the incoming content is a JSON string, try to send it as JSON first
        parsed_json = None
        try:
            parsed_json = json.loads(content)
        except Exception:
            parsed_json = None

        # Try different approaches
        approaches = []

        # Approach 0: Send parsed JSON directly (preferred)
        if isinstance(parsed_json, dict):
            approaches.append({
                'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
                'data': parsed_json,
                'send_as_json': True
            })
        elif isinstance(parsed_json, list):
            # If we only received an array of sections, wrap it
            approaches.append({
                'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
                'data': {'sections': parsed_json},
                'send_as_json': True
            })

        # Approach 1: JSON with content field (string)
        approaches.append({
            'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
            'data': {'content': content},
            'send_as_json': True
        })
        # Approach 2: JSON with data field (string)
        approaches.append({
            'headers': {'Content-Type': 'application/json', 'Accept': 'application/json'},
            'data': {'data': content},
            'send_as_json': True
        })
        # Approach 3: Form data
        approaches.append({
            'headers': {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'},
            'data': f'content={content}',
            'send_as_json': False
        })
        # Approach 4: Plain text
        approaches.append({
            'headers': {'Content-Type': 'text/plain', 'Accept': 'application/json'},
            'data': content,
            'send_as_json': False
        })
        
        import requests

        # Keep track of what we attempted to send for debugging
        attempts_log = []
        # Keep track of responses received for debugging
        responses_log = []

        errors = []
        for endpoint in urls:
            for i, approach in enumerate(approaches, 1):
                try:
                    # Prepare a safe preview of the payload
                    try:
                        if approach.get('send_as_json') and not isinstance(approach['data'], str):
                            payload_preview = json.dumps(approach['data'])
                        else:
                            payload_preview = str(approach['data'])
                    except Exception:
                        payload_preview = '<unserializable payload>'

                    # Persist the attempted payload for later inspection
                    attempt_entry = {
                        'endpoint': endpoint,
                        'approach': i,
                        'headers': approach.get('headers'),
                        'send_as_json': bool(approach.get('send_as_json')),
                        'data': approach.get('data')
                    }
                    attempts_log.append(attempt_entry)
                    try:
                        frappe.cache().set_value('last_generate_page_attempts', json.dumps(attempts_log, ensure_ascii=False))
                    except Exception:
                        # Best-effort cache write; continue regardless
                        pass

                    frappe.logger().info(f"Trying {endpoint} with approach {i}: {approach['headers']} | Payload preview: {payload_preview[:1000]}")

                    if approach.get('send_as_json'):
                        response = requests.post(endpoint, json=approach['data'], headers=approach['headers'], timeout=30)
                    else:
                        response = requests.post(endpoint, data=approach['data'], headers=approach['headers'], timeout=30)

                    frappe.logger().info(f"{endpoint} - Approach {i} - Status: {response.status_code}")
                    frappe.logger().info(f"{endpoint} - Approach {i} - Response: {response.text[:500]}")  # First 500 chars

                    # Record response details for later inspection
                    try:
                        response_headers = {k: v for k, v in response.headers.items()}
                    except Exception:
                        response_headers = {}
                    parsed_response_json = None
                    try:
                        parsed_response_json = response.json()
                    except Exception:
                        parsed_response_json = None
                    response_entry = {
                        'endpoint': endpoint,
                        'approach': i,
                        'status': response.status_code,
                        'headers': response_headers,
                        'text': (response.text or '')[:10000],
                        'json': parsed_response_json
                    }
                    responses_log.append(response_entry)
                    try:
                        frappe.cache().set_value('last_generate_page_responses', json.dumps(responses_log, ensure_ascii=False))
                    except Exception:
                        pass

                    if response.status_code == 200:
                        try:
                            result = response.json()
                            frappe.logger().info(f"{endpoint} - Approach {i} succeeded!")
                            return result
                        except:
                            frappe.logger().info(f"{endpoint} - Approach {i} succeeded but response is not JSON: {response.text}")
                            return {'success': True, 'message': 'Page generated', 'data': {'pageUrl': response.text}}

                    elif response.status_code == 400:
                        frappe.logger().error(f"{endpoint} - Approach {i} failed with 400: {response.text}")
                        errors.append({'url': endpoint, 'approach': i, 'status': 400, 'body': response.text[:300]})
                        continue
                    else:
                        frappe.logger().error(f"{endpoint} - Approach {i} failed with status {response.status_code}: {response.text}")
                        errors.append({'url': endpoint, 'approach': i, 'status': response.status_code, 'body': response.text[:300]})
                        continue

                except Exception as e:
                    frappe.logger().error(f"{endpoint} - Approach {i} exception: {str(e)}")
                    errors.append({'url': endpoint, 'approach': i, 'exception': str(e)})
                    # Save exception to responses log as well
                    try:
                        responses_log.append({
                            'endpoint': endpoint,
                            'approach': i,
                            'exception': str(e)
                        })
                        frappe.cache().set_value('last_generate_page_responses', json.dumps(responses_log, ensure_ascii=False))
                    except Exception:
                        pass
                    continue
        
        # If we get here, none worked
        detail_lines = []
        for err in errors[:4]:
            if 'exception' in err:
                detail_lines.append(f"{err.get('url')}: approach {err['approach']} exception - {err['exception']}")
            else:
                detail_lines.append(f"{err.get('url')}: approach {err['approach']} status {err['status']} - {err['body']}")
        detail_msg = "\n".join(detail_lines) or "No details captured."
        raise frappe.ValidationError(f"All API request approaches failed. Details:\n{detail_msg}")
        
    except Exception as e:
        frappe.log_error(f"Page Generation Error: {str(e)}", "Page Generation Error")
        frappe.throw(f"Failed to generate page: {str(e)}")  


@frappe.whitelist()
def get_last_generate_page_attempts():
	"""
	Return the last payload attempts made by `generate_page`.
	Useful for debugging what data was sent to the external API.
	"""
	data = frappe.cache().get_value('last_generate_page_attempts')
	try:
		return json.loads(data) if data else []
	except Exception:
		return []


@frappe.whitelist()
def get_last_generate_page_responses():
	"""
	Return the last responses captured by `generate_page`.
	Provides status, headers, response text (truncated), and parsed JSON if available.
	"""
	data = frappe.cache().get_value('last_generate_page_responses')
	try:
		return json.loads(data) if data else []
	except Exception:
		return []

# @frappe.whitelist(allow_guest=True)
# def set_form_job_applicant(applicant_name, email, cover_letter=None, resume_attachment=None, job_title=None, mobile_no=None):
#     job_applicant = frappe.new_doc("Job Applicant")
#     job_applicant.applicant_name = applicant_name
#     job_applicant.email_id = email
#     job_applicant.cover_letter = cover_letter
#     job_applicant.job_title = job_title
#     job_applicant.phone_number = mobile_no

#     if resume_attachment:
#         job_applicant.resume_attachment = resume_attachment  # pass File URL or attachment ID

#     job_applicant.source = "Website"
#     job_applicant.save(ignore_permissions=True)

#     frappe.db.commit()

#     return job_applicant.name
import frappe
import json

import frappe, json
from frappe.utils.file_manager import save_file

@frappe.whitelist(allow_guest=True)
def set_form_job_applicant(data):
    try:
        doc_data = json.loads(data) if isinstance(data, str) else data
    except Exception:
        frappe.throw("Invalid data format. Expecting JSON.")

    # Create Job Applicant
    job_applicant = frappe.new_doc("Job Applicant")
    job_applicant.applicant_name = doc_data.get("applicant_name")
    job_applicant.email_id = doc_data.get("email_id")
    job_applicant.phone_number = doc_data.get("mobile")
    job_applicant.job_title = doc_data.get("job_title")
    job_applicant.gender = doc_data.get("gender")
    job_applicant.current_location = doc_data.get("location")
    job_applicant.applicant_type = doc_data.get("applicant_type")
    job_applicant.linkedin_link = doc_data.get("linkedin_link")
    job_applicant.additional_info = doc_data.get("additional_info")
    job_applicant.highest_qualification = doc_data.get("qualification")
    # Add experienced applicant fields (only if provided)
    if doc_data.get("current_ctc"):
        job_applicant.current_ctc = doc_data.get("current_ctc")
    if doc_data.get("expected_ctc"):
        job_applicant.expected_ctc = doc_data.get("expected_ctc")
    if doc_data.get("current_employer_"):
        job_applicant.current_employer_ = doc_data.get("current_employer_")
    if doc_data.get("total_experience"):
        job_applicant.total_experience = doc_data.get("total_experience")
    job_applicant.insert(ignore_permissions=True)

    if "resume" in frappe.request.files:
        _file = frappe.request.files["resume"]
        file_doc = save_file(
            _file.filename,
            _file.stream.read(),  
            "Job Applicant",
            job_applicant.name,
            is_private=1
        )
        job_applicant.resume_attachment = file_doc.file_url
        job_applicant.save(ignore_permissions=True)

    frappe.db.commit()

    return {"status": "success", "job_applicant": job_applicant.name}


# @frappe.whitelist(allow_guest=True)  #
# def get_applicant_types():
#     meta = frappe.get_meta("Job Applicant")
#     field = next((f for f in meta.fields if f.fieldname == "applicant_type"), None)
#     if field and field.options:
#         types = field.options.split("\n")
#         return {"message": types}  # <- Important
#     return {"message": []}  #


@frappe.whitelist(allow_guest=True)
def get_applicant_types():
    # ensure the meta includes custom fields
    frappe.clear_cache(doctype="Job Applicant")

    meta = frappe.get_meta("Job Applicant", cached=False)
    field = next((f for f in meta.fields if f.fieldname == "applicant_type"), None)

    if field and field.options:
        options = [opt.strip() for opt in field.options.split("\n") if opt.strip()]
        return {"message": options}

    return {"message": []}


@frappe.whitelist(allow_guest=True)
def get_gender():
   
    try:
        gender = frappe.get_all(
            "Gender",
            fields=["name"]
        )
        return {"success": True, "data": gender}
    except Exception as e:
        return {"success": False, "message": str(e)}



@frappe.whitelist(allow_guest=True)
def get_all_job_openings():
    """
    Fetch all published Job Openings
    """
    try:
        job_openings = frappe.get_all(
            "Job Opening",
            filters={"status": "Open"},  
            fields=["name", "designation"]
            
        )
        return {"success": True, "data": job_openings}
    except Exception as e:
        return {"success": False, "message": str(e)}
    
    
@frappe.whitelist(allow_guest=True)
def create_lead(lead_name, company_name, mobile_no, email_id, lead_type):
    """
    Custom POST API to create a Lead from webform submission
    """
    try:
        doc = frappe.get_doc({
            "doctype": "Lead",
            "lead_name": lead_name,
            "company_name": company_name,
            "mobile_no": mobile_no,
            "email_id": email_id,
            "type": "Client" if lead_type == "End User" else lead_type,  
            "source": "Frappeverse2025" 
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return {
            "status": "success",
            "message": _(f"Thank you {doc.lead_name}, your form has been created successfully!"),
            "lead_id": doc.name
        }
    except frappe.DuplicateEntryError as e:
    # Email already exists
        return {
            "status": "error",
            "message": "This email is already registered. Please use another email address."
        }
    except Exception as e:
        frappe.throw(_("Error while creating Lead: {0}").format(str(e)))
        
        
# ==================== FAQ GENERATOR ====================

import json
import re

@frappe.whitelist()
def generate_faqs(doctype, docname):
	"""
	Generate FAQs for a single Web Page or Blog Post.
	This function is called from the button in the form.
	"""
	ai_agent_name = "FAQs Agent"
	if not frappe.db.exists("AI Agent", ai_agent_name):
		frappe.throw(f"AI Agent '{ai_agent_name}' does not exist.")

	ai_agent_doc = frappe.get_doc("AI Agent", ai_agent_name)
	agent_service = ai_agent_doc.agent_service
	if not agent_service:
		frappe.throw(f"AI Agent '{ai_agent_name}' has no configured service.")

	# Fetch the document
	doc = frappe.get_doc(doctype, docname)
	if not doc.published:
		frappe.throw(f"{doctype} '{docname}' is not published.")

	# Build full URL
	doc_route = doc.route or ""
	full_url = f"https://finbyz.tech/{doc_route}"

	result = agent_service.invoke(url=full_url)
	if not result:
		frappe.throw("AI agent returned an empty result.")
	doc.faqs = []

	for faq in result.faqs:
		question = faq.question
		answer = faq.answer
		if question and answer:
			doc.append("faqs", {"question": question, "answer": answer})

	if not doc.faqs:
		frappe.throw("No valid FAQs were generated by the AI.")

	doc.save()

	faq_count = len(doc.faqs)
	
	frappe.msgprint(
		msg=f"Successfully generated {faq_count} FAQs for '{doc.title}'",
		title="FAQ Generation Complete", 
		indicator="green"
	)
	
	return {
		"success": True,
		"message": "FAQ generation completed",
		"doctype": doctype,
		"docname": doc.name,
		"title": doc.title,
		"faq_count": faq_count
	}

def generate_faqs_bulk(doctype, docnames):		
	results = {
		"success": [],
		"failed": [],
		"skipped": []
	}
	
	for docname in docnames:
		try:				
			if not frappe.db.exists(doctype, docname):
				results["skipped"].append({
					"docname": docname,
					"reason": "Document not found"
				})
				continue
			
			result = generate_faqs(doctype, docname)
			
			if result.get("success"):
				results["success"].append({
					"docname": docname,
					"title": result.get("title"),
					"faq_count": result.get("faq_count")
				})
			else:
				results["failed"].append({
					"docname": docname,
					"error": result.get("message")
				})
		except Exception as e:
			error_msg = str(e)
			frappe.logger().error(f"[FAQ Bulk] Error processing {docname}: {error_msg}")
			results["failed"].append({
				"docname": docname,
				"error": error_msg
			})
		time.sleep(60)
			
	return results


@frappe.whitelist()
def create_faqs_for_documents(doctype, docnames):
	"""
	Generate FAQs for multiple Web Pages or Blog Posts.
	
	Args:
		doctype (str): "Web Page" or "Blog Post"
		docnames (str or list): JSON string or list of document names
	"""
	if doctype not in ['Web Page','Blog','Gallery']:
		frappe.throw(f"{doctype} not allowed to generate faqs")
  
	if isinstance(docnames, str):
		docnames = frappe.parse_json(docnames)
	
	if not isinstance(docnames, list):
		frappe.throw("docnames must be a list of document names")
	
	if not docnames:
		frappe.throw("No documents provided for bulk generation")
	
	job = frappe.enqueue(generate_faqs_bulk,queue='long',job_name=f'faqs generation for {doctype}')
	return {
		"sucess": True,
		'job_id': job.id
	}

@frappe.whitelist()
def generate_faqs_for_all_published(doctype):
	"""
	Generate FAQs for ALL published Web Pages or Blog Posts that don't have FAQs.
	"""
	try:
		# Get all published documents without FAQs
		docs = frappe.get_all(
			doctype,
			filters={"published": 1},
			fields=["name", "title"]
		)
		
		if not docs:
			frappe.msgprint(f"No published {doctype} found", indicator="blue")
			return {"success": True, "message": f"No published {doctype} found"}
		
		# Filter documents that don't have FAQs
		docs_without_faqs = []
		for doc_info in docs:
			doc = frappe.get_doc(doctype, doc_info.name)
			if not doc.get("faqs") or len(doc.get("faqs")) == 0:
				docs_without_faqs.append(doc_info.name)
		
		if not docs_without_faqs:
			frappe.msgprint(f"All published {doctype} already have FAQs", indicator="blue")
			return {"success": True, "message": f"All published {doctype} already have FAQs"}
		
		
		# Use bulk generation
		return generate_faqs_bulk(doctype, docs_without_faqs)
		
	except Exception as e:
		error_msg = str(e)
		frappe.logger().error(f"[FAQ All Published] Error: {error_msg}", exc_info=True)
		frappe.msgprint(f"Error: {error_msg}", title="Generation Error", indicator="red")
		return {"success": False, "error": error_msg}
