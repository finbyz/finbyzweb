import frappe
import json

@frappe.whitelist()
def generate_related_content(doctype, docname):
    """
    Generate related links and gallery links for Web Page, Blog Post, or Gallery.
    """
    # Validate doctype
    if doctype not in ['Web Page', 'Blog Post', 'Gallery']:
        frappe.throw(f"Doctype '{doctype}' is not supported")
    
    # Fetch AI Agent
    ai_agent_name = "Related Content Matcher"
    if not frappe.db.exists("AI Agent", ai_agent_name):
        frappe.throw(f"AI Agent '{ai_agent_name}' does not exist")
    
    ai_agent_doc = frappe.get_doc("AI Agent", ai_agent_name)
    agent_service = ai_agent_doc.agent_service
    
    if not agent_service:
        frappe.throw(f"AI Agent has no configured service")
    
    # Fetch current document
    doc = frappe.get_doc(doctype, docname)
    
    if not doc.published:
        frappe.throw(f"{doctype} '{docname}' is not published")
    
    # Extract current document metadata
    current_data = extract_document_metadata(doc, doctype)
    
    # Fetch candidates
    candidates_blog_web = fetch_blog_and_web_candidates(doctype, docname)
    candidates_gallery = fetch_gallery_candidates(doctype, docname)
    
    if not candidates_blog_web and not candidates_gallery:
        frappe.msgprint("No published candidates found", indicator="orange")
        return {"success": False, "message": "No candidates available"}
    
    # Format for AI
    formatted_blog_web = format_candidates_for_prompt(candidates_blog_web)
    formatted_gallery = format_gallery_candidates_for_prompt(candidates_gallery)
    
    # Prepare input data
    input_data = {
        "current_doctype": doctype,
        "current_docname": docname,
        "current_title": current_data['title'],
        "current_seo_title": current_data['seo_title'],
        "current_keywords": current_data['keywords'],
        "current_description": current_data['description'],
        "candidates_blog_web": formatted_blog_web,
        "candidates_gallery": formatted_gallery
    }
    
    # Log input
    frappe.log_error(
        title=f"AI Input - {doctype} - {docname}",
        message=json.dumps(input_data, indent=2)
    )
    
    # Invoke AI Agent
    try:
        result = agent_service.invoke(**input_data)
    except Exception as e:
        frappe.log_error(
            title=f"AI Error - {doctype} - {docname}",
            message=str(e)
        )
        frappe.throw(f"AI Agent failed: {str(e)}")
    
    # Log raw output
    frappe.log_error(
        title=f"AI Output - {doctype} - {docname}",
        message=json.dumps(result, indent=2, default=str)
    )
    
    # Process output
    try:
        # Get output
        if isinstance(result, dict) and 'output' in result:
            output_data = result['output']
        else:
            output_data = result
        
        # Convert to dict if needed
        if isinstance(output_data, str):
            parsed_output = json.loads(output_data)
        elif isinstance(output_data, dict):
            parsed_output = output_data
        elif hasattr(output_data, 'dict'):
            parsed_output = output_data.dict()
        elif hasattr(output_data, 'model_dump'):
            parsed_output = output_data.model_dump()
        elif hasattr(output_data, '__dict__'):
            parsed_output = vars(output_data)
        else:
            frappe.throw(f"Cannot process output type: {type(output_data)}")
        
    except Exception as e:
        frappe.log_error(
            title=f"AI Parse Error - {doctype} - {docname}",
            message=f"Error: {str(e)}\nRaw Result: {str(result)}"
        )
        frappe.throw(f"Failed to parse output: {str(e)}")
    
    # Clear existing
    doc.related_links = []
    doc.gallery_links = []
    
    # Add related links
    for link in parsed_output.get('related_links', []):
        ref_doctype = link.get('reference_doctype')
        ref_name = link.get('reference_name')
        
        if ref_doctype and ref_name and frappe.db.exists(ref_doctype, ref_name):
            doc.append("related_links", {
                "reference_doctype": ref_doctype,
                "reference_name": ref_name
            })
    
    # Add gallery links
    for gallery in parsed_output.get('gallery_links', []):
        gallery_name = gallery.get('gallery')
        
        if gallery_name and frappe.db.exists('Gallery', gallery_name):
            doc.append("gallery_links", {
                "gallery": gallery_name
            })
    
    # Save
    doc.save()
    
    related_count = len(doc.related_links)
    gallery_count = len(doc.gallery_links)
    
    frappe.msgprint(
        msg=f"Generated {related_count} related links and {gallery_count} galleries",
        title="Success",
        indicator="green"
    )
    
    return {
        "success": True,
        "related_links_count": related_count,
        "gallery_links_count": gallery_count
    }


def extract_document_metadata(doc, doctype):
    metadata = {
        'title': '',
        'seo_title': '',
        'keywords': '',
        'description': ''
    }
    
    if doctype == 'Blog Post':
        metadata['title'] = doc.get('title') or doc.get('blog_title') or ""
        metadata['seo_title'] = doc.get('meta_title') or doc.get('title') or ""
        metadata['keywords'] = doc.get('meta_keywords') or ""
        metadata['description'] = doc.get('meta_description') or doc.get('blog_intro') or ""
    elif doctype == 'Web Page':
        metadata['title'] = doc.get('title') or ""
        metadata['seo_title'] = doc.get('seo_title') or doc.get('title') or ""
        metadata['keywords'] = doc.get('keyword') or ""
        metadata['description'] = doc.get('small_description') or ""
    elif doctype == 'Gallery':
        metadata['title'] = doc.get('gallery_title') or doc.get('title') or ""
        metadata['seo_title'] = doc.get('seo_title') or ""
        metadata['keywords'] = doc.get('keywords') or ""
        metadata['description'] = ""
    
    return metadata


def fetch_blog_and_web_candidates(current_doctype, current_docname):
    candidates = []
    
    # Blog Posts
    blog_fields = ['name']
    blog_meta = frappe.get_meta('Blog Post')
    for field in ['title', 'blog_title', 'meta_title', 'meta_keywords', 'meta_description', 'blog_intro']:
        if blog_meta.has_field(field):
            blog_fields.append(field)
    
    try:
        blog_posts = frappe.get_all('Blog Post', filters={'published': 1}, fields=blog_fields)
        for post in blog_posts:
            if current_doctype == 'Blog Post' and post.name == current_docname:
                continue
            candidates.append({
                'doctype': 'Blog Post',
                'name': post.name,
                'title': post.get('title') or post.get('blog_title') or "",
                'seo_title': post.get('meta_title') or "",
                'keywords': post.get('meta_keywords') or "",
                'description': post.get('meta_description') or post.get('blog_intro') or ""
            })
    except:
        pass
    
    # Web Pages
    web_fields = ['name']
    web_meta = frappe.get_meta('Web Page')
    for field in ['title', 'seo_title', 'keyword', 'small_description']:
        if web_meta.has_field(field):
            web_fields.append(field)
    
    try:
        web_pages = frappe.get_all('Web Page', filters={'published': 1}, fields=web_fields)
        for page in web_pages:
            if current_doctype == 'Web Page' and page.name == current_docname:
                continue
            candidates.append({
                'doctype': 'Web Page',
                'name': page.name,
                'title': page.get('title') or "",
                'seo_title': page.get('seo_title') or "",
                'keywords': page.get('keyword') or "",
                'description': page.get('small_description') or ""
            })
    except:
        pass
    
    return candidates


def fetch_gallery_candidates(current_doctype, current_docname):
    candidates = []
    gallery_fields = ['name']
    gallery_meta = frappe.get_meta('Gallery')
    
    for field in ['title', 'gallery_title', 'seo_title', 'keywords']:
        if gallery_meta.has_field(field):
            gallery_fields.append(field)
    
    try:
        galleries = frappe.get_all('Gallery', filters={'published': 1}, fields=gallery_fields)
        for gallery in galleries:
            if current_doctype == 'Gallery' and gallery.name == current_docname:
                continue
            candidates.append({
                'name': gallery.name,
                'title': gallery.get('gallery_title') or gallery.get('title') or "",
                'seo_title': gallery.get('seo_title') or "",
                'keywords': gallery.get('keywords') or ""
            })
    except:
        pass
    
    return candidates


def format_candidates_for_prompt(candidates):
    if not candidates:
        return "No candidates available."
    
    formatted = []
    for idx, c in enumerate(candidates, 1):
        desc = c.get('description', '')[:150]
        formatted.append(
            f"{idx}. [{c['doctype']}] {c['name']}\n"
            f"   Title: {c.get('title', 'N/A')}\n"
            f"   Keywords: {c.get('keywords', 'N/A')}\n"
            f"   Description: {desc or 'N/A'}"
        )
    return "\n\n".join(formatted)


def format_gallery_candidates_for_prompt(candidates):
    if not candidates:
        return "No galleries available."
    
    formatted = []
    for idx, c in enumerate(candidates, 1):
        formatted.append(
            f"{idx}. [Gallery] {c['name']}\n"
            f"   Title: {c.get('title', 'N/A')}\n"
            f"   Keywords: {c.get('keywords', 'N/A')}"
        )
    return "\n\n".join(formatted)