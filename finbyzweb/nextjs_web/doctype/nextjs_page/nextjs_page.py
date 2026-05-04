# Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from finbyzai.ai.agent.agent_service import AgentService
from frappe import _


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

        if self.title and not self.actual_route:
            self.actual_route = "/" + frappe.scrub(self.title).replace("_", "-")

    def validate(self):
        # Ensure route starts with /
        if self.route and not self.route.startswith("/"):
            self.route = "/" + self.route

        # Ensure actual_route starts with /
        if self.actual_route and not self.actual_route.startswith("/"):
            self.actual_route = "/" + self.actual_route

        if self.is_published and not self.published_on:
            self.published_on = frappe.utils.today()

        self.sync_faq_schema()
        self.sync_breadcrumb_schema()

    def after_insert(self):
        if self.source_code_snippet:
            frappe.db.set_value(
                "Code Snippet",
                self.source_code_snippet,
                {"is_nextjs_page_generated": 1, "nextjs_page": self.name},
            )

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

        site_url = "https://finbyz.tech"
        page_url = site_url + (self.route or "")

        faq_json_ld = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "@id": page_url + "#faq",
            "mainEntityOfPage": page_url,
            "publisher": {
                "@type": "Organization",
                "@id": site_url + "/#organization",
                "name": "FinByz Tech Pvt Ltd",
                "logo": site_url + "/files/FinbyzLogo.png",
            },
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

        site_url = "https://finbyz.tech"
        page_url = site_url + (self.route or "")

        # Build schema JSON
        breadcrumb_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "@id": page_url + "#breadcrumb",
            "publisher": {"@id": site_url + "/#organization"},
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
        site_url = "https://finbyz.tech"

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
    page_url = "https://finbyz.tech" + (doc.route or "")
    result = agent.invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",  # Compatibility for existing prompts
        page_url=page_url,
        user_input=user_input or "Generate optimized SEO metadata.",
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

    return {"success": True, "message": "SEO metadata generated and saved successfully"}


@frappe.whitelist()
def generate_faqs(doc_name, user_input=None):
    """Generate FAQs using AI Agent."""
    doc = frappe.get_doc("NextJS Page", doc_name)
    settings = frappe.get_single("NextJS AI Settings")

    if not settings.faq_generator_agent:
        frappe.throw("Please configure FAQ Generator Agent in NextJS AI Settings")

    agent = AgentService(settings.faq_generator_agent)
    page_url = "https://finbyz.tech" + (doc.route or "")
    result = agent.invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",  # Compatibility for existing prompts
        page_url=page_url,
        user_input=user_input or "Generate relevant FAQs for this page.",
    )

    doc.set("faqs", [])
    for faq in result.faqs:
        doc.append("faqs", {"question": faq.question, "answer": faq.answer})

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
        if row.schema_type == "FAQPage":
            continue
        if row.schema_type == "BreadcrumbList":
            continue

        if row.schema_type and not row.schema_json:
            template_doc = frappe.get_doc("NextJS Schema Type", row.schema_type)
            reference_schema = template_doc.schema or "{}"
            if row.schema_type == "Organization":
                row.schema_json = reference_schema
                continue
            page_url = "https://finbyz.tech" + (doc.route or "")
            result = agent.invoke(
                title=doc.title,
                content=doc.content or "",
                reference_schema=reference_schema,
                page_url=page_url,
                base_url="https://finbyz.tech",
                user_input=user_input
                or "Generate appropriate JSON-LD schema based on the template.",
            )

            if hasattr(result, "schema_json"):
                schema_val = result.schema_json
            elif isinstance(result, dict) and "schema_json" in result:
                schema_val = result["schema_json"]
            else:
                schema_val = str(result)

            # Clean the JSON: Remove script tags and markdown fences
            if schema_val:
                import re

                # Remove <script ...> and </script>
                schema_val = re.sub(r"<script[^>]*>", "", schema_val)
                schema_val = schema_val.replace("</script>", "")

                # Remove markdown code fences
                schema_val = re.sub(r"```json\s*", "", schema_val)
                schema_val = schema_val.replace("```", "")

                row.schema_json = schema_val.strip()
                generated_count += 1

    if generated_count > 0:
        doc.save()
        return {
            "success": True,
            "message": f"Generated {generated_count} schemas successfully",
        }
    else:
        return {"success": False, "message": "No empty schema rows found to generate."}

    return {"success": True, "message": "Schema generated and saved successfully"}


@frappe.whitelist()
def revise_content(doc_name, user_input):
    """Revise content using AI Agent."""
    doc = frappe.get_doc("NextJS Page", doc_name)
    settings = frappe.get_single("NextJS AI Settings")

    if not settings.content_writer_agent:
        frappe.throw("Please configure Content Writer Agent in NextJS AI Settings")

    agent = AgentService(settings.content_writer_agent)
    page_url = "https://finbyz.tech" + (doc.route or "")
    result = agent.invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",  # Compatibility for existing prompts
        meta_title=doc.meta_title or "",
        meta_description=doc.meta_description or "",
        keywords=doc.keywords or "",
        page_type=doc.page_type or "Web page",
        user_input=user_input,
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

    page_url = "https://finbyz.tech" + (doc.route or "")
    result = agent.invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",  # Compatibility for existing prompts
        page_url=page_url,
        user_input=user_input
        or "Please improve these FAQs for better clarity and SEO.",
        faqs_data=faqs_data,
    )

    # Map revised data back to doc
    if result.faqs:
        for i, revised_faq in enumerate(result.faqs):
            if i < len(faqs_to_revise):
                original = faqs_to_revise[i]
                for row in doc.faqs:
                    # Match by original question or idx if provided
                    if row.question == original.get(
                        "question"
                    ) or row.name == original.get("idx"):
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
        user_input=user_input
        or "Generate engaging social media posts to promote this page.",
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

        created_posts.append({"name": new_post.name, "platform": platform})

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
        frappe.log_error(
            title="AI Page Creation Failed", message=frappe.get_traceback()
        )
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
            "keywords": result.keywords,
            "content": result.content,
        }

    new_page = frappe.new_doc("NextJS Page")
    new_page.title = data.get("title")
    new_page.meta_title = data.get("meta_title")
    new_page.meta_description = data.get("meta_description")
    new_page.keywords = data.get("keywords")
    new_page.content_type = "Rich Text"
    new_page.content = data.get("content", "")
    new_page.page_type = "Web page"
    new_page.is_published = 0

    new_page.insert()
    frappe.db.commit()

    return {
        "success": True,
        "message": "Page created successfully",
        "name": new_page.name,
    }


@frappe.whitelist()
def generate_related_links(doc_name, user_input=None):
    """Generate related page links using AI Agent and store them in nextjs_related_page child table."""
    doc = frappe.get_doc("NextJS Page", doc_name)
    settings = frappe.get_single("NextJS AI Settings")

    if not settings.related_links_finder_agent:
        frappe.throw(
            "Please configure Related Links Finder Agent in NextJS AI Settings"
        )

    agent = AgentService(settings.related_links_finder_agent)
    page_url = "https://finbyz.tech" + (doc.route or "")

    result = agent.invoke(
        title=doc.title or "",
        content=doc.content or "",
        meta_title=doc.meta_title or "",
        meta_description=doc.meta_description or "",
        keywords=doc.keywords or "",
        page_url=page_url,
        user_input=user_input or "Find related pages for this page.",
    )

    # Extract list of related links from agent result
    # Supports new format: {"related_links": [{"title": "...", "route": "..."}]}
    # Also supports legacy format: {"routes": ["...", ...]} or {"related_links": ["...", ...]}
    raw_links = []
    if hasattr(result, "related_links"):
        raw_links = result.related_links
    elif hasattr(result, "routes"):
        raw_links = result.routes
    elif isinstance(result, dict):
        raw_links = result.get("related_links") or result.get("routes") or []

    if not raw_links:
        return {
            "success": False,
            "message": "AI agent did not return any related links.",
        }

    # Clear existing related pages and repopulate
    doc.set("nextjs_related_page", [])

    added = 0
    for link in raw_links:
        # Support both structured objects {"title": ..., "route": ...} and plain route strings
        if isinstance(link, str):
            route = link
        elif isinstance(link, dict):
            route = link.get("route") or ""
        else:
            # Pydantic/object with attributes
            route = getattr(link, "route", None) or ""

        if not route:
            continue

        # Normalise route — strip the domain if agent returned a full URL
        if "finbyz.tech" in route:
            from urllib.parse import urlparse

            route = urlparse(route).path

        # Ensure route starts with /
        if not route.startswith("/"):
            route = "/" + route

        # Look up the NextJS Page name by route field
        page_name = frappe.db.get_value("NextJS Page", {"route": route}, "name")
        if page_name:
            doc.append("nextjs_related_page", {"page": page_name})
            added += 1

    if added == 0:
        return {
            "success": False,
            "message": "No matching NextJS Pages found for the suggested routes.",
        }

    doc.save()

    return {
        "success": True,
        "message": f"Found and saved {added} related page(s) successfully.",
    }


@frappe.whitelist()
def generate_nextjs_code(doc_name):
    """Enqueue Next.js code generation to background to avoid timeout."""
    frappe.enqueue(
        "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page._generate_nextjs_code_background",
        doc_name=doc_name,
        now=frappe.flags.in_test,
        queue="long",
    )
    return {
        "success": True,
        "message": "Generation started in the background. You will be notified once complete.",
    }


def _generate_nextjs_code_background(doc_name):
    """Background task for generating and publishing Next.js code."""
    import base64
    import requests
    import json

    try:
        doc = frappe.get_doc("NextJS Page", doc_name)
        settings = frappe.get_single("NextJS AI Settings")

        # Determine which agent to use
        agent_name = None
        if doc.page_type == "Web page":
            agent_name = settings.web_page_agent
        elif doc.page_type == "Blog Post":
            agent_name = settings.blog_post_agent
        elif doc.page_type == "Code Snippet":
            agent_name = settings.code_snippet_agent

        if not agent_name:
            raise Exception(
                f"Please configure {doc.page_type} Agent in NextJS AI Settings"
            )

        agent = AgentService(agent_name)

        # Prepare input data for the agent
        content_text = frappe.utils.strip_html_tags(doc.content or "")
        if doc.content_type == "Markdown":
            content_text = doc.content_md or ""

        ai_input_data = {
            "title": doc.title or "",
            "content": content_text,
            "meta_title": doc.meta_title or "",
            "meta_description": doc.meta_description or "",
            "keywords": doc.keywords or "",
            "page_type": doc.page_type or "Web page",
            "slug": doc.route or frappe.utils.slug(doc.title),
            "publish_date": doc.published_on or frappe.utils.today(),
            "author_name": doc.owner or "Administrator",
            "primary_category": "Business",
            # Add mappings for the Web Page Agent prompt
            "seo_title": doc.meta_title or doc.title,
            "seo_description": doc.meta_description or "",
            "page_description": doc.meta_description or "",
            "heroImage": doc.image or "",
            "existing_component_str": "[]",  # Placeholder for now
        }

        # Pass a query string to avoid 'contents is not specified' error in Gemini
        query = f"Generate Next.js code for the {doc.page_type}: {doc.title}"
        result = agent.invoke(query=query, **ai_input_data)

        # Check if the result has page_code
        page_code = getattr(result, "page_code", None)
        if not page_code and isinstance(result, dict):
            page_code = result.get("page_code")

        if not page_code:
            if isinstance(result, str):
                page_code = result
            else:
                raise Exception("AI Agent did not return page_code")

        # Send to Next.js API
        page_code_base64 = base64.b64encode(page_code.encode("utf-8")).decode("utf-8")
        slug = doc.route or frappe.utils.slug(doc.title)

        # Map page_type to the specific strings expected by the Next.js API
        type_map = {
            "Web page": "webpage",
            "Blog Post": "blog",
            "Code Snippet": "code-snippet",
        }
        page_type_slug = type_map.get(doc.page_type, "webpage")

        # Extract FAQs for the payload
        faqs_data = []
        for faq in doc.get("faqs") or []:
            faqs_data.append({"question": faq.question, "answer": faq.answer})

        payload = {
            "slug": slug,
            "type": page_type_slug,
            "name": doc.name,
            "pageCode": page_code_base64,
            "components": [],
            "seoData": {
                "seo_title": doc.meta_title or doc.title,
                "title": doc.title,
                "description": doc.meta_description or "",
                "small_description": doc.meta_description or "",
                "keywords": doc.keywords or "",
                "image": doc.image or "",
                "content": content_text[:500] if content_text else "",
                "faqs": faqs_data,  # Added FAQs here
            },
        }

        nextjs_api_url = frappe.conf.get("nextjs_api_url") or "https://web.finbyz.com"
        api_endpoint = f"{nextjs_api_url}/api/write-page"

        response = requests.post(
            api_endpoint,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=120,
        )

        if response.status_code == 200:
            doc.is_published = 1
            doc.published_on = frappe.utils.today()
            doc.save()

            frappe.publish_realtime(
                "nextjs_page_generated",
                {
                    "success": True,
                    "message": "Page generated and published successfully!",
                    "docname": doc_name,
                },
                user=frappe.session.user,
            )
        else:
            error_msg = f"API Error: {response.status_code}"
            try:
                error_msg = response.json().get("message", error_msg)
            except:
                pass
            raise Exception(error_msg)

    except Exception as e:
        frappe.log_error(
            title="AI Generate Background Error", message=frappe.get_traceback()
        )
        frappe.publish_realtime(
            "nextjs_page_generated",
            {"success": False, "message": f"Error: {str(e)}", "docname": doc_name},
            user=frappe.session.user,
        )

