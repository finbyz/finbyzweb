# Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import base64
import json
import re
import unicodedata
from urllib.parse import urlparse

import frappe
import requests
from frappe.model.document import Document

from finbyzai.ai.agent.agent_service import AgentService

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SITE_URL = "https://finbyz.tech"
NEXTJS_API_DEFAULT = "https://web.finbyz.com"

# Maps NextJS Page.page_type → NextJS AI Settings agent field name
PAGE_TYPE_AGENT_MAP = {
    "Web page": "web_page_agent",
    "Blog Post": "blog_post_agent",
    "Code Snippet": "code_snippet_agent",
}

# Maps NextJS Page.page_type → API slug for the Next.js write-page endpoint
PAGE_TYPE_SLUG_MAP = {
    "Web page": "webpage",
    "Blog Post": "blog",
    "Code Snippet": "code-snippet",
}

# Maps social platform name → credential type label
PLATFORM_CREDENTIAL_MAP = {
    "LinkedIn": "LinkedIn Integration",
    "X (Twitter)": "Twitter Integration",
}

# Schema types managed internally; must never be AI-generated
INTERNAL_SCHEMA_TYPES = {"FAQPage", "BreadcrumbList"}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def slugify(title: str) -> str:
    """Convert a title string into a URL-safe slug (no leading slash)."""
    title = (
        unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    )
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", "-", title)
    return title.strip("-")


def _page_url(route: str) -> str:
    """Return the full page URL for a given route."""
    return SITE_URL + (route or "")


def _get_agent(settings_field: str) -> AgentService:
    """
    Load NextJS AI Settings and return an initialised AgentService.
    Raises a user-facing error if the agent field is not configured.
    """
    settings = frappe.get_single("NextJS AI Settings")
    agent_name = getattr(settings, settings_field, None)
    if not agent_name:
        label = settings_field.replace("_", " ").title()
        frappe.throw(f"Please configure {label} in NextJS AI Settings")
    return AgentService(agent_name)


def _getval(obj, key):
    """Safely get a value from either a dict or an object with attributes."""
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


def _clean_schema_json(raw: str) -> str:
    """Strip script tags and Markdown code fences from an AI-generated schema string."""
    raw = re.sub(r"<script[^>]*>", "", raw)
    raw = raw.replace("</script>", "")
    raw = re.sub(r"```json\s*", "", raw).replace("```", "")
    return raw.strip()


def _truncate(text: str, limit: int = 2000) -> str:
    return text[:limit] + "..." if len(text) > limit else text


# ---------------------------------------------------------------------------
# Document class
# ---------------------------------------------------------------------------


class NextJSPage(Document):

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------
    def on_trash(self):
        if self.source_code_snippet:
            frappe.db.set_value("Code Snippet", self.source_code_snippet, "is_nextjs_page_generated", 0 )
            frappe.db.set_value("Code Snippet", self.source_code_snippet, "nextjs_page", None )
            self.source_code_snippet = None
        
    def autoname(self):
        """Derive document name and auto-populate route fields from title."""
        if not self.name and self.title:
            self.name = frappe.scrub(self.title).replace("_", "-")
        if not self.name:
            self.name = frappe.generate_hash(length=8)

        if self.title and not self.route:
            self.route = "/" + slugify(self.title)

        if self.title and not self.actual_route:
            self.actual_route = "/" + slugify(self.title)

    def validate(self):
        # Ensure routes always start with /
        for field in ("route", "actual_route"):
            value = self.get(field)
            if value and not value.startswith("/"):
                self.set(field, "/" + value)

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

    # ------------------------------------------------------------------
    # Schema synchronisation
    # ------------------------------------------------------------------

    def sync_faq_schema(self):
        """Keep the FAQPage JSON-LD schema in sync with the faqs child table."""
        existing = self._find_schema("FAQPage")

        faq_items = [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in (self.faqs or [])
            if faq.question and faq.answer
        ]

        if not faq_items:
            if existing:
                self.remove(existing)
            return

        page_url = _page_url(self.route)
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "@id": page_url + "#faq",
            "mainEntityOfPage": page_url,
            "publisher": {
                "@type": "Organization",
                "@id": SITE_URL + "/#organization",
                "name": "FinByz Tech Pvt Ltd",
                "logo": SITE_URL + "/files/FinbyzLogo.png",
            },
            "mainEntity": faq_items,
        }
        self._upsert_schema("FAQPage", schema, existing)

    def sync_breadcrumb_schema(self):
        """Auto-generate a BreadcrumbList JSON-LD schema from the page route."""
        if not self.route:
            return

        items = self._build_breadcrumb_items()
        if not items:
            return

        page_url = _page_url(self.route)
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "@id": page_url + "#breadcrumb",
            "publisher": {"@id": SITE_URL + "/#organization"},
            "itemListElement": items,
        }
        self._upsert_schema(
            "BreadcrumbList", schema, self._find_schema("BreadcrumbList")
        )

    def _find_schema(self, schema_type: str):
        """Return the first schema row matching schema_type, or None."""
        return next(
            (
                s
                for s in (self.get("nextjs_page_schema") or [])
                if s.schema_type == schema_type
            ),
            None,
        )

    def _upsert_schema(self, schema_type: str, schema_dict: dict, existing=None):
        """Insert or update a schema row with the serialised schema_dict."""
        serialised = json.dumps(schema_dict, indent=2)
        if existing:
            existing.schema_json = serialised
        else:
            self.append(
                "nextjs_page_schema",
                {
                    "schema_type": schema_type,
                    "schema_json": serialised,
                },
            )

    def _build_breadcrumb_items(self) -> list:
        """Parse self.route into an ordered list of ListItem breadcrumb dicts."""
        if not self.route or self.route == "/":
            return []

        items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE_URL}]
        current_path = ""

        for position, segment in enumerate(
            (s for s in self.route.split("/") if s), start=2
        ):
            current_path += f"/{segment}"
            items.append(
                {
                    "@type": "ListItem",
                    "position": position,
                    "name": segment.replace("-", " ").replace("_", " ").title(),
                    "item": SITE_URL.rstrip("/") + current_path,
                }
            )

        return items


# ---------------------------------------------------------------------------
# Whitelisted API functions
# ---------------------------------------------------------------------------


@frappe.whitelist()
def generate_seo(doc_name, user_input=None):
    """Generate and save SEO metadata using the configured AI Agent."""
    doc = frappe.get_doc("NextJS Page", doc_name)
    result = _get_agent("seo_generator_agent").invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",
        page_url=_page_url(doc.route),
        user_input=user_input or "Generate optimized SEO metadata.",
    )

    doc.meta_title = _getval(result, "meta_title")
    doc.meta_description = _getval(result, "meta_description")
    doc.keywords = _getval(result, "keywords")

    # Mirror to OG / Twitter fields for consistency
    doc.og_title = doc.meta_title
    doc.og_description = doc.meta_description
    doc.twitter_title = doc.meta_title
    doc.twitter_description = doc.meta_description

    doc.save()
    return {"success": True, "message": "SEO metadata generated and saved successfully"}


@frappe.whitelist()
def generate_faqs(doc_name, user_input=None):
    """Generate and save FAQs using the configured AI Agent."""
    doc = frappe.get_doc("NextJS Page", doc_name)
    result = _get_agent("faq_generator_agent").invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",
        page_url=_page_url(doc.route),
        user_input=user_input or "Generate relevant FAQs for this page.",
    )

    doc.set("faqs", [])
    for faq in result.faqs:
        doc.append(
            "faqs",
            {
                "question": _getval(faq, "question"),
                "answer": _getval(faq, "answer"),
            },
        )

    doc.save()
    return {"success": True, "message": f"Generated and saved {len(result.faqs)} FAQs"}


@frappe.whitelist()
def generate_schema(doc_name, user_input=None):
    """
    Generate JSON-LD schema for any schema rows that have a schema_type
    selected but an empty schema_json.

    FAQPage and BreadcrumbList rows are always skipped — they are managed
    automatically via sync_faq_schema() and sync_breadcrumb_schema().
    """
    doc = frappe.get_doc("NextJS Page", doc_name)
    agent = _get_agent("schema_builder_agent")
    generated_count = 0
    schema_types = [schema_row.schema_type for schema_row in doc.nextjs_page_schema]
    for row in doc.nextjs_page_schema:
        if (
            not row.schema_type
            or row.schema_json
            or row.schema_type in INTERNAL_SCHEMA_TYPES
        ):
            continue

        template = frappe.get_doc("NextJS Schema Type", row.schema_type)
        reference_schema = template.schema or "{}"

        # Organization schema is copied verbatim from the template
        if row.schema_type == "Organization":
            row.schema_json = reference_schema
            generated_count += 1
            continue

        # result = agent.invoke(
        #     title=doc.title,
        #     content=doc.content or "",
        #     reference_schema=reference_schema,
        #     page_url=_page_url(doc.route),
        #     base_url=SITE_URL,
        #     user_input=user_input
        #     or "Generate appropriate JSON-LD schema based on the template.",
        # )
        result = agent.invoke(
            schema_type=row.schema_type,
            has_breadcrumb=True if "BreadcrumbList" in schema_types else False,
            has_faq=True if "FAQPage" in schema_types else False,
            title=doc.title,
            content=doc.content or "",
            page_url=_page_url(doc.route),
            base_url=SITE_URL,
            user_input=user_input
            or "Generate appropriate JSON-LD schema based on the template.",
        )

        raw = _getval(result, "schema_json") or str(result)
        row.schema_json = _clean_schema_json(raw)
        generated_count += 1

    if not generated_count:
        return {"success": False, "message": "No empty schema rows found to generate."}

    doc.save()
    return {
        "success": True,
        "message": f"Generated {generated_count} schema(s) successfully",
    }


@frappe.whitelist()
def revise_content(doc_name, user_input):
    """Rewrite the full page content using the Content Writer Agent."""
    doc = frappe.get_doc("NextJS Page", doc_name)
    settings = frappe.get_single("NextJS AI Settings")
    agent_name = settings.content_writer_agent
    agent = _get_agent(agent_name)
    result = agent.invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",
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
    """Revise specific FAQs in-place using the FAQ Reviser Agent."""
    doc = frappe.get_doc("NextJS Page", doc_name)

    if isinstance(faqs_to_revise, str):
        faqs_to_revise = json.loads(faqs_to_revise)

    result = _get_agent("faq_reviser_agent").invoke(
        title=doc.title,
        content=doc.content or "",
        short_description="",
        page_url=_page_url(doc.route),
        user_input=user_input
        or "Please improve these FAQs for better clarity and SEO.",
        faqs_data=json.dumps(faqs_to_revise, indent=2),
    )

    if not result.faqs:
        return {
            "success": False,
            "message": "AI agent did not return any revised FAQs.",
        }

    for i, revised in enumerate(result.faqs):
        if i >= len(faqs_to_revise):
            break
        original = faqs_to_revise[i]
        for row in doc.faqs:
            if row.question == original.get("question") or row.name == original.get(
                "idx"
            ):
                row.question = _getval(revised, "question")
                row.answer = _getval(revised, "answer")
                break

    doc.save()
    return {"success": True, "message": "FAQs revised and saved successfully"}


@frappe.whitelist()
def revise_content_chunk(doc_name, content_chunk, instruction, is_markdown=False):
    """
    Revise a selected chunk of content using the Content Improvement Agent.

    Full page content is sent as context so the AI can match tone and style,
    but only the selected chunk is rewritten. The caller replaces the chunk
    in the editor using the returned revised_content value.
    """
    if not content_chunk:
        frappe.throw("Please select some content to revise.")
    if not instruction:
        frappe.throw("Please provide a revision instruction.")

    is_markdown = frappe.parse_json(is_markdown)
    doc = frappe.get_doc("NextJS Page", doc_name)

    if doc.content_type == "Markdown" or is_markdown:
        full_content = doc.content_md or ""
        content_type = "Markdown"
    else:
        full_content = doc.content or ""
        content_type = "HTML"

    result = _get_agent("content_revision_agent").invoke(
        content_chunk=content_chunk,
        instruction=instruction,
        full_content=full_content,
        content_type=content_type,
    )

    # Prefer structured field; fall back to raw string representation
    revised_text = _getval(result, "revised_content") or (
        result if isinstance(result, str) else str(result)
    )

    return {"revised_content": revised_text.strip() if revised_text else ""}


@frappe.whitelist()
def generate_social_post(doc_name, user_input=None, platforms=None, credentials=None):
    """
    Generate social media posts with AI and create a Social Media Post doc
    for each requested platform.
    """
    doc = frappe.get_doc("NextJS Page", doc_name)

    if isinstance(platforms, str):
        platforms = json.loads(platforms)
    if not platforms:
        frappe.throw("Please select at least one platform")

    if isinstance(credentials, str):
        credentials = json.loads(credentials)
    credentials = credentials or {}

    content_text = _truncate(frappe.utils.strip_html_tags(doc.content or ""))

    result = _get_agent("social_media_post_agent").invoke(
        title=doc.title or "",
        content=content_text,
        meta_title=doc.meta_title or "",
        meta_description=doc.meta_description or "",
        keywords=doc.keywords or "",
        page_url=_page_url(doc.route),
        platforms=", ".join(platforms),
        user_input=user_input
        or "Generate engaging social media posts to promote this page.",
    )

    created_posts = []
    for post_data in result.posts:
        platform = _getval(post_data, "platform")
        content = _getval(post_data, "content")
        if not platform or not content:
            continue

        new_post = frappe.new_doc("Social Media Post")
        new_post.title = doc.title
        new_post.platform = platform
        new_post.content = content
        new_post.status = "Draft"
        new_post.created_on = frappe.utils.today()
        new_post.credential_type = PLATFORM_CREDENTIAL_MAP.get(platform)

        platform_creds = credentials.get(platform, {})
        if platform_creds.get("credential"):
            new_post.credential_type = platform_creds.get("credential_type")
            new_post.credential = platform_creds["credential"]

        new_post.insert()
        created_posts.append({"name": new_post.name, "platform": platform})

    if not created_posts:
        return {"success": False, "message": "AI agent did not generate any posts."}

    frappe.db.commit()
    return {
        "success": True,
        "message": f"Created {len(created_posts)} social media post(s) successfully.",
        "posts": created_posts,
    }


@frappe.whitelist()
def create_page_from_ai(user_input):
    """
    Create a new NextJS Page from an AI-generated outline.

    Uses the web_page_agent. If a dedicated page-creator agent is needed,
    add a `page_creator_agent` Link field to the NextJS AI Settings DocType
    and change the _get_agent() call below accordingly.
    """
    try:
        result = _get_agent("content_writer_agent").invoke(user_input=user_input)
    except Exception:
        frappe.log_error(
            title="AI Page Creation Failed", message=frappe.get_traceback()
        )
        frappe.throw(
            "AI Agent failed to generate page data. Check the error log for details."
        )

    title = _getval(result, "title")
    if not title:
        frappe.throw("AI Agent returned invalid data — missing required 'title' field.")

    new_page = frappe.new_doc("NextJS Page")
    new_page.title = title
    new_page.meta_title = _getval(result, "meta_title")
    new_page.meta_description = _getval(result, "meta_description")
    new_page.keywords = _getval(result, "keywords")
    new_page.content_type = "Rich Text"
    new_page.content = _getval(result, "content") or ""
    new_page.page_type = "Web page"
    new_page.is_published = 0
    new_page.route = "/" + slugify(title)
    new_page.actual_route = "/" + slugify(title)

    return new_page


@frappe.whitelist()
def generate_related_links(doc_name, user_input=None):
    """
    Use AI to find related NextJS Pages and populate the nextjs_related_page
    child table.
    """
    doc = frappe.get_doc("NextJS Page", doc_name)
    result = _get_agent("related_links_finder_agent").invoke(
        title=doc.title or "",
        content=doc.content or "",
        meta_title=doc.meta_title or "",
        meta_description=doc.meta_description or "",
        keywords=doc.keywords or "",
        page_url=_page_url(doc.route),
        user_input=user_input or "Find related pages for this page.",
    )

    raw_links = _getval(result, "related_links") or _getval(result, "routes") or []
    if not raw_links:
        return {
            "success": False,
            "message": "AI agent did not return any related links.",
        }

    doc.set("nextjs_related_page", [])
    added = 0

    for link in raw_links:
        route = link if isinstance(link, str) else (_getval(link, "route") or "")
        if not route:
            continue

        # Strip domain if agent returned an absolute URL
        if "finbyz.tech" in route:
            route = urlparse(route).path

        if not route.startswith("/"):
            route = "/" + route

        page_name = frappe.db.get_value("NextJS Page", {"route": route}, "name")
        if page_name:
            doc.append("nextjs_related_page", {"page": page_name})
            added += 1

    if not added:
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
    """Enqueue Next.js code generation as a background job to avoid request timeouts."""
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
    """
    Background task: generate Next.js page code with AI and push it to the
    Next.js write-page API. Publishes a realtime event on completion or failure.
    """
    try:
        doc = frappe.get_doc("NextJS Page", doc_name)
        settings = frappe.get_single("NextJS AI Settings")

        agent_field = PAGE_TYPE_AGENT_MAP.get(doc.page_type)
        agent_name = agent_field and getattr(settings, agent_field, None)
        if not agent_name:
            raise ValueError(
                f"Please configure a {doc.page_type} Agent in NextJS AI Settings"
            )

        agent = AgentService(agent_name)

        content_text = (
            doc.content_md or ""
            if doc.content_type == "Markdown"
            else frappe.utils.strip_html_tags(doc.content or "")
        )

        result = agent.invoke(
            query=f"Generate Next.js code for the {doc.page_type}: {doc.title}",
            title=doc.title or "",
            content=content_text,
            meta_title=doc.meta_title or "",
            meta_description=doc.meta_description or "",
            keywords=doc.keywords or "",
            page_type=doc.page_type or "Web page",
            slug=doc.route or ("/" + slugify(doc.title)),
            publish_date=doc.published_on or frappe.utils.today(),
            author_name=doc.owner or "Administrator",
            primary_category="Business",
            seo_title=doc.meta_title or doc.title,
            seo_description=doc.meta_description or "",
            page_description=doc.meta_description or "",
            heroImage=doc.image or "",
            existing_component_str="[]",
        )

        page_code = _getval(result, "page_code") or (
            result if isinstance(result, str) else None
        )
        if not page_code:
            raise ValueError("AI Agent did not return page_code")

        slug = doc.route or ("/" + slugify(doc.title))
        faqs_data = [
            {"question": faq.question, "answer": faq.answer}
            for faq in (doc.get("faqs") or [])
        ]

        payload = {
            "slug": slug,
            "type": PAGE_TYPE_SLUG_MAP.get(doc.page_type, "webpage"),
            "name": doc.name,
            "pageCode": base64.b64encode(page_code.encode("utf-8")).decode("utf-8"),
            "components": [],
            "seoData": {
                "seo_title": doc.meta_title or doc.title,
                "title": doc.title,
                "description": doc.meta_description or "",
                "small_description": doc.meta_description or "",
                "keywords": doc.keywords or "",
                "image": doc.image or "",
                "content": content_text[:500],
                "faqs": faqs_data,
            },
        }

        api_url = (
            frappe.conf.get("nextjs_api_url") or NEXTJS_API_DEFAULT
        ) + "/api/write-page"
        response = requests.post(
            api_url,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=120,
        )

        if response.status_code != 200:
            try:
                error_msg = response.json().get("message") or response.text
            except Exception:
                error_msg = response.text
            raise RuntimeError(f"API Error {response.status_code}: {error_msg}")

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

    except Exception:
        frappe.log_error(
            title="NextJS Code Generation Failed", message=frappe.get_traceback()
        )
        frappe.publish_realtime(
            "nextjs_page_generated",
            {
                "success": False,
                "message": "Generation failed. Check the error log for details.",
                "docname": doc_name,
            },
            user=frappe.session.user,
        )
