import frappe
import json

web_content_setting = frappe.get_single("Web Schema Generation Setting")
content_formatter_agent_doc_name = web_content_setting.web_page_content_agent

if not content_formatter_agent_doc_name:
    print("ERROR: Web Page Content Formatter AI Agent not configured in Web Schema Generation Setting.")
    exit()

content_formatter_agent = frappe.get_doc("AI Agent", content_formatter_agent_doc_name)

if not content_formatter_agent:
    print(f"ERROR: AI Agent '{content_formatter_agent_doc_name}' not found.")
    exit()

web_page_name_to_test = "erp-software-development"

try:
    web_page_doc = frappe.get_doc("Web Page", web_page_name_to_test)
    print(f"--- Processing Web Page: {web_page_doc.name} ---")

    if not web_page_doc.main_section_html:
        print(f"WARNING: main_section_html is empty for {web_page_doc.name}. Skipping.")
        exit()

    ai_input_data = {
        "webpage_title": web_page_doc.title,
        "seo_title": web_page_doc.seo_title,
        "seo_description": web_page_doc.small_description,
        "main_section_html": web_page_doc.main_section_html
    }

    print("Invoking AI Agent...")
    result = content_formatter_agent.invoke(**ai_input_data)
    print("AI Agent invoked successfully.")

    generated_sections = result.get("sections")

    if not generated_sections:
        print("ERROR: AI agent did not return structured web page content (missing 'sections' key).")
        print(f"Raw AI Result: {result}")
        exit()

    web_page_content_json = {"sections": generated_sections}

    print("\n--- Generated web_page_content JSON ---")
    print(json.dumps(web_page_content_json, indent=2))

    print(f"\n--- Updating Web Page '{web_page_doc.name}' with generated content ---")
    web_page_doc.web_page_content = json.dumps(web_page_content_json)
    web_page_doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("✅ Web Page updated successfully.")

except frappe.DoesNotExistError:
    print(f"ERROR: Web Page with name '{web_page_name_to_test}' does not exist.")
except Exception as e:
    print(f"AN UNEXPECTED ERROR OCCURRED: {e}")
    frappe.db.rollback()