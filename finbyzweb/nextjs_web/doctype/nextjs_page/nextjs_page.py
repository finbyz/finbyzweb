# Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from finbyzai.ai.agent.agent_service import AgentService


class NextJSPage(Document):

    def autoname(self):
        """Set name as slugified title."""
        if not self.name and self.title:
            self.name = frappe.scrub(self.title).replace("_", "-")
        if not self.name:
            self.name = frappe.generate_hash(length=8)

        # Auto-generating route if empty
        if self.title and not self.route:
            self.route = "/" + frappe.scrub(self.title).replace("_", "-")

    def validate(self):
        # Ensure route starts with /
        if self.route and not self.route.startswith("/"):
            self.route = "/" + self.route

        if self.is_published and not self.published_on:
            self.published_on = frappe.utils.today()

        self.sync_faq_schema()
        self.sync_breadcrumb_schema()

    def sync_faq_schema(self):
        """Synchronize FAQs child table with FAQPage schema."""
        import json

        # Filter out existing FAQPage schema
        schema_table = self.get("nextjs_page_schema") or []
        existing_faq_schema = next(
            (s for s in schema_table if s.schema_type == "FAQPage"), None
        )

        if not self.faqs:
            if existing_faq_schema:
                self.remove(existing_faq_schema)
            return

        faq_items = []
        for faq in self.faqs:
            if faq.question and faq.answer:
                faq_items.append(
                    {
                        "@type": "Question",
                        "name": faq.question,
                        "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
                    }
                )

        if not faq_items:
            if existing_faq_schema:
                self.remove(existing_faq_schema)
            return

        faq_json_ld = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": faq_items,
        }

        if not existing_faq_schema:
            self.append(
                "nextjs_page_schema",
                {
                    "schema_type": "FAQPage",
                    "schema_json": json.dumps(faq_json_ld, indent=2),
                },
            )
        else:
            existing_faq_schema.schema_json = json.dumps(faq_json_ld, indent=2)

    def sync_breadcrumb_schema(self):
        """Auto-generate BreadcrumbList schema from route."""
        import json

        if not self.route:
            return

        # Parse route into breadcrumb items
        breadcrumb_items = self._parse_route_to_breadcrumbs()

        if not breadcrumb_items:
            return

        # Build schema JSON
        breadcrumb_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumb_items,
        }

        # Find existing BreadcrumbList schema
        schema_table = self.get("nextjs_page_schema") or []
        existing_breadcrumb = next(
            (s for s in schema_table if s.schema_type == "BreadcrumbList"), None
        )

        if not existing_breadcrumb:
            self.append(
                "nextjs_page_schema",
                {
                    "schema_type": "BreadcrumbList",
                    "schema_json": json.dumps(breadcrumb_schema, indent=2),
                },
            )
        else:
            existing_breadcrumb.schema_json = json.dumps(breadcrumb_schema, indent=2)

    def _parse_route_to_breadcrumbs(self):
        """Parse route into breadcrumb list items."""
        if not self.route or self.route == "/":
            return []

        # Get site URL from settings
        site_url = frappe.utils.get_url()

        # Start with Home
        items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": site_url}]

        # Split route and build incremental breadcrumbs
        segments = [s for s in self.route.split("/") if s]
        current_path = ""

        for idx, segment in enumerate(segments, start=2):
            current_path += f"/{segment}"
            # Convert slug to title (e.g., "chemical-industry" → "Chemical Industry")
            name = segment.replace("-", " ").replace("_", " ").title()

            items.append(
                {
                    "@type": "ListItem",
                    "position": idx,
                    "name": name,
                    "item": site_url.rstrip("/") + current_path,
                }
            )

        return items


@frappe.whitelist()
def generate_seo(doc_name, user_input=None):
	"""Generate SEO metadata using AI Agent."""
	doc = frappe.get_doc("NextJS Page", doc_name)
	settings = frappe.get_single("NextJS AI Settings")

	if not settings.seo_generator_agent:
		frappe.throw("Please configure SEO Generator Agent in NextJS AI Settings")

	agent = AgentService(settings.seo_generator_agent)
	result = agent.invoke(
		title=doc.title,
		content=doc.content or "",
		short_description="", # Compatibility for existing prompts
		user_input=user_input or "Generate optimized SEO metadata."
	)

	doc.meta_title = result.meta_title
	doc.meta_description = result.meta_description
	doc.keywords = result.keywords
	
	# Update OG/Twitter fields for consistency
	doc.og_title = result.meta_title
	doc.og_description = result.meta_description
	doc.twitter_title = result.meta_title
	doc.twitter_description = result.meta_description
	
	doc.save()

	return {
		"success": True,
		"message": "SEO metadata generated and saved successfully"
	}


@frappe.whitelist()
def generate_faqs(doc_name, user_input=None):
	"""Generate FAQs using AI Agent."""
	doc = frappe.get_doc("NextJS Page", doc_name)
	settings = frappe.get_single("NextJS AI Settings")

	if not settings.faq_generator_agent:
		frappe.throw("Please configure FAQ Generator Agent in NextJS AI Settings")

	agent = AgentService(settings.faq_generator_agent)
	result = agent.invoke(
		title=doc.title,
		content=doc.content or "",
		short_description="", # Compatibility for existing prompts
		user_input=user_input or "Generate relevant FAQs for this page."
	)

	doc.set("faqs", [])
	for faq in result.faqs:
		doc.append("faqs", {
			"question": faq.question,
			"answer": faq.answer
		})

	doc.save()

	return {"success": True, "message": f"Generated and saved {len(result.faqs)} FAQs"}


@frappe.whitelist()
def generate_schema(doc_name, user_input=None):
	"""Generate JSON-LD Schema using AI Agent."""
	doc = frappe.get_doc("NextJS Page", doc_name)
	settings = frappe.get_single("NextJS AI Settings")

	if not settings.schema_builder_agent:
		frappe.throw("Please configure Schema Builder Agent in NextJS AI Settings")

	agent = AgentService(settings.schema_builder_agent)
	
	generated_count = 0
	for row in doc.nextjs_page_schema:
		# If schema_type is selected but schema_json is empty, generate it
		if row.schema_type and not row.schema_json:
			template_doc = frappe.get_doc("NextJS Schema Type", row.schema_type)
			reference_schema = template_doc.schema or "{}"
			
			result = agent.invoke(
				title=doc.title,
				content=doc.content or "",
				reference_schema=reference_schema,
				user_input=user_input or "Generate appropriate JSON-LD schema based on the template."
			)
			
			if hasattr(result, "schema_json"):
				row.schema_json = result.schema_json
				generated_count += 1
			elif isinstance(result, dict) and "schema_json" in result:
				row.schema_json = result["schema_json"]
				generated_count += 1

	if generated_count > 0:
		doc.save()
		return {
			"success": True, 
			"message": f"Generated {generated_count} schemas successfully"
		}
	else:
		return {
			"success": False,
			"message": "No empty schema rows found to generate."
		}

	return {
		"success": True,
		"message": "Schema generated and saved successfully"
	}


@frappe.whitelist()
def revise_content(doc_name, user_input):
	"""Revise content using AI Agent."""
	doc = frappe.get_doc("NextJS Page", doc_name)
	settings = frappe.get_single("NextJS AI Settings")

	if not settings.content_writer_agent:
		frappe.throw("Please configure Content Writer Agent in NextJS AI Settings")

	agent = AgentService(settings.content_writer_agent)
	result = agent.invoke(
		title=doc.title,
		content=doc.content or "",
		short_description="", # Compatibility for existing prompts
		meta_title=doc.meta_title or "",
		meta_description=doc.meta_description or "",
		keywords=doc.keywords or "",
		page_type=doc.page_type or "Web page",
		user_input=user_input
	)

	doc.content = result.content
	doc.save()

	return {"success": True, "message": "Content revised and saved successfully"}


@frappe.whitelist()
def revise_faqs(doc_name, faqs_to_revise, user_input=None):
	"""Revise or regenerate specific FAQs using AI Agent."""
	doc = frappe.get_doc("NextJS Page", doc_name)
	settings = frappe.get_single("NextJS AI Settings")

	agent_name = settings.faq_reviser_agent
	if not agent_name:
		frappe.throw("Please configure FAQ Reviser Agent in NextJS AI Settings")

	agent = AgentService(agent_name)
	
	import json
	if isinstance(faqs_to_revise, str):
		faqs_to_revise = json.loads(faqs_to_revise)
		
	faqs_data = json.dumps(faqs_to_revise, indent=2)
	
	result = agent.invoke(
		title=doc.title,
		content=doc.content or "",
		short_description="", # Compatibility for existing prompts
		user_input=user_input or "Please improve these FAQs for better clarity and SEO.",
		faqs_data=faqs_data
	)

	# Map revised data back to doc
	if result.faqs:
		for i, revised_faq in enumerate(result.faqs):
			if i < len(faqs_to_revise):
				original = faqs_to_revise[i]
				for row in doc.faqs:
					# Match by original question or idx if provided
					if row.question == original.get("question") or row.name == original.get("idx"):
						# Robust access: try .get() for dicts, dot notation/getattr for objects
						if hasattr(revised_faq, "get"):
							row.question = revised_faq.get("question")
							row.answer = revised_faq.get("answer")
						else:
							row.question = getattr(revised_faq, "question", None)
							row.answer = getattr(revised_faq, "answer", None)
						break

	doc.save()

	return {"success": True, "message": "FAQs revised and saved successfully"}


@frappe.whitelist()
def generate_social_post(doc_name, user_input=None, platforms=None, credentials=None):
	"""Generate social media posts using AI Agent and create Social Media Post docs."""
	import json as _json

	doc = frappe.get_doc("NextJS Page", doc_name)
	settings = frappe.get_single("NextJS AI Settings")

	if not settings.social_media_post_agent:
		frappe.throw("Please configure Social Media Post Agent in NextJS AI Settings")

	# Parse platforms
	if isinstance(platforms, str):
		platforms = _json.loads(platforms)

	if not platforms:
		frappe.throw("Please select at least one platform")

	# Parse credentials
	if isinstance(credentials, str):
		credentials = _json.loads(credentials)
	credentials = credentials or {}

	# Platform to credential_type mapping
	platform_credential_map = {
		"LinkedIn": "LinkedIn Integration",
		"X (Twitter)": "Twitter Integration",
	}

	# Build the page URL
	site_url = frappe.utils.get_url()
	page_url = site_url.rstrip("/") + (doc.route or "")

	# Prepare content summary (strip HTML tags for AI)
	content_text = frappe.utils.strip_html_tags(doc.content or "")
	# Truncate content to avoid token limit issues
	if len(content_text) > 2000:
		content_text = content_text[:2000] + "..."

	# Format platforms string
	platforms_str = ", ".join(platforms)

	agent = AgentService(settings.social_media_post_agent)
	result = agent.invoke(
		title=doc.title or "",
		content=content_text,
		meta_title=doc.meta_title or "",
		meta_description=doc.meta_description or "",
		keywords=doc.keywords or "",
		page_url=page_url,
		platforms=platforms_str,
		user_input=user_input or "Generate engaging social media posts to promote this page."
	)

	# Create Social Media Post docs for each platform
	created_posts = []
	for post_data in result.posts:
		platform = getattr(post_data, "platform", None) or post_data.get("platform")
		content = getattr(post_data, "content", None) or post_data.get("content")

		if not platform or not content:
			continue

		new_post = frappe.new_doc("Social Media Post")
		new_post.title = doc.title
		new_post.platform = platform
		new_post.content = content
		new_post.status = "Draft"
		new_post.created_on = frappe.utils.today()

		# Auto-set credential_type based on platform
		new_post.credential_type = platform_credential_map.get(platform)

		# Set credential if user selected one in the dialog
		platform_creds = credentials.get(platform, {})
		if platform_creds.get("credential"):
			new_post.credential_type = platform_creds["credential_type"]
			new_post.credential = platform_creds["credential"]

		new_post.insert()

		created_posts.append({
			"name": new_post.name,
			"platform": platform
		})

	if not created_posts:
		return {"success": False, "message": "AI agent did not generate any posts."}

	frappe.db.commit()


@frappe.whitelist()
def revise_content_chunk(doc_name, content_chunk, instruction, is_markdown=False):
    """Revise a selected chunk of content using AI Agent.

    Sends the full page content as context so the AI can match
    tone/style, but only the selected chunk is revised.
    Returns the revised text — the frontend replaces it in-place.
    """
    logger = frappe.logger("nextjs_page")
    is_markdown = frappe.parse_json(is_markdown)

    logger.info("=" * 50)
    logger.info(f"[AI Improve] revise_content_chunk called. Markdown: {is_markdown}")

    if not content_chunk:
        frappe.throw("Please select some content to revise.")
    if not instruction:
        frappe.throw("Please provide a revision instruction.")

    doc = frappe.get_doc("NextJS Page", doc_name)
    settings = frappe.get_single("NextJS AI Settings")

    if not settings.content_revision_agent:
        frappe.throw("Please configure Content Revision Agent in NextJS AI Settings")

    # Determine format and full context
    content_type = "HTML"
    if doc.content_type == "Markdown":
        full_content = doc.content_md or ""
        content_type = "Markdown"
    else:
        full_content = doc.content or ""
        # If frontend explicitly says it's markdown, respect that (e.g. if content_type is switched)
        if is_markdown:
            content_type = "Markdown"

    agent = AgentService(settings.content_revision_agent)
    result = agent.invoke(
        content_chunk=content_chunk,
        instruction=instruction,
        full_content=full_content,
        content_type=content_type,
    )

    logger.info(f"[AI Improve] AI agent response received, type: {type(result)}")

    # Extract revised content from result
    revised_text = ""

    # Comprehensive logging for debugging
    log_data = {
        "result_type": str(type(result)),
        "result_value_str": str(result),
        "doc_name": doc_name,
        "instruction": instruction,
        "content_chunk_length": len(content_chunk) if content_chunk else 0,
        "dir_result": dir(result),
    }

    # Try to get data as dict for easier logging
    try:
        if hasattr(result, "dict") and callable(result.dict):
            log_data["result_as_dict"] = result.dict()
        elif hasattr(result, "model_dump") and callable(result.model_dump):
            log_data["result_as_model_dump"] = result.model_dump()
    except Exception as e:
        log_data["extraction_log_error"] = str(e)

    # Extraction logic
    if isinstance(result, str) and result.strip():
        revised_text = result
        log_data["extraction_method"] = "result_is_string"
    elif hasattr(result, "revised_content") and getattr(result, "revised_content"):
        revised_text = result.revised_content
        log_data["extraction_method"] = "attribute_extraction"
    elif isinstance(result, dict) and result.get("revised_content"):
        revised_text = result.get("revised_content")
        log_data["extraction_method"] = "dict_key_extraction"
    elif (
        "result_as_dict" in log_data
        and log_data["result_as_dict"]
        and log_data["result_as_dict"].get("revised_content")
    ):
        revised_text = log_data["result_as_dict"].get("revised_content")
        log_data["extraction_method"] = "injected_dict_extraction"
    else:
        # Fallback: Capture anything that looks like content
        revised_text = str(result)
        log_data["extraction_method"] = "fallback_stringification"

    log_data["final_revised_text_preview"] = (
        revised_text[:200] if revised_text else "EMPTY"
    )

    # Log to Error Log for final verification
    frappe.log_error(
        title=f"AI Improve Process: {doc_name}", message=frappe.as_json(log_data)
    )

    return {"revised_content": revised_text.strip() if revised_text else ""}


@frappe.whitelist()
def create_page_from_ai(user_input):
	"""Create a new NextJS Page based on AI generation."""
	settings = frappe.get_single("NextJS AI Settings")

	if not settings.page_creator_agent:
		frappe.throw("Please configure Page Creator Agent in NextJS AI Settings")

	agent = AgentService(settings.page_creator_agent)
	
	try:
		result = agent.invoke(user_input=user_input)
	except Exception as e:
		frappe.log_error(title="AI Page Creation Failed", message=frappe.get_traceback())
		frappe.throw(f"AI Agent failed to generate page data: {str(e)}")

	if not result or not hasattr(result, "title"):
		# Fallback for different return types if needed
		if isinstance(result, dict) and "title" in result:
			data = result
		else:
			frappe.throw("AI Agent returned invalid data format")
	else:
		data = {
			"title": result.title,
			"meta_title": result.meta_title,
			"meta_description": result.meta_description,
			"keywords": result.keywords
		}

	new_page = frappe.new_doc("NextJS Page")
	new_page.title = data.get("title")
	new_page.meta_title = data.get("meta_title")
	new_page.meta_description = data.get("meta_description")
	new_page.keywords = data.get("keywords")
	new_page.page_type = "Web page"
	new_page.is_published = 0
	
	new_page.insert()
	frappe.db.commit()

	return {
		"success": True,
		"message": "Page created successfully",
		"name": new_page.name
	}
