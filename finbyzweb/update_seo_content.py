import frappe

@frappe.whitelist()
# *** 1. UPDATED: Changed function signature, removed `self`, added `docname` ***
def update_seo_content(docname: str, url: str, instructions: str):
    """
    Update SEO content based on URL and user instructions
    """
    try:
        # *** 2. ADDED: Get the document using the docname passed from the frontend ***
        web_page_doc = frappe.get_doc("Web Page", docname)

        # Step 1: Get existing SEO data from the loaded document
        current_seo_data = {
            "seo_title": web_page_doc.seo_title or "",
            "seo_description": web_page_doc.small_description or "",
            "keywords": web_page_doc.keyword or "",
        }
        
        # Step 2: Hardcoded AI Agent name
        ai_agent_name = "SEO Content Updater Agent"
        
        # Step 3: Get AI Agent document
        try:
            ai_agent_doc = frappe.get_doc("AI Agent", ai_agent_name)
            agent_service = ai_agent_doc.agent_service
        except frappe.DoesNotExistError:
            frappe.throw(f"AI Agent '{ai_agent_name}' not found. Please create it first.")
        
        # Step 4: Prepare input for AI Agent (use `web_page_doc.name`)
        ai_input_data = {
            "url": url,
            "seo_title": current_seo_data["seo_title"],
            "seo_description": current_seo_data["seo_description"],
            "keywords": current_seo_data["keywords"],
            "instructions": instructions,
            "webpage_name": web_page_doc.name
        }
        
        # Step 5: Invoke AI Agent
        result = agent_service.invoke(**ai_input_data)
        
        # Step 6: Parse result
        updated_seo_title = getattr(result, "seo_title", None)
        updated_seo_description = getattr(result, "seo_description", None)
        updated_keywords = getattr(result, "keywords", None)
        
        if not updated_seo_title or not updated_seo_description:
            frappe.throw("AI agent did not return complete SEO content")
        
        # Step 7: Update the loaded document object
        web_page_doc.seo_title = updated_seo_title
        web_page_doc.small_description = updated_seo_description
        web_page_doc.keyword = updated_keywords
        web_page_doc.save(ignore_permissions=True) # Use ignore_permissions if needed
        # No need for reload() here
        
        return {
            "status": "success",
            "seo_title": updated_seo_title,
            "seo_description": updated_seo_description,
            "keywords": updated_keywords,
            "message": "SEO content updated successfully"
        }
        
    except Exception as e:
        frappe.log_error(f"SEO Update Error: {str(e)}")
        frappe.throw(f"Error updating SEO content: {str(e)}")