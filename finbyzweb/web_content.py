import frappe

def generate_missing_webpage_content():
    # Get one Web Page where web_page_content is not set or empty
    web_page_doc = frappe.get_all(
        "Web Page",
        filters={"web_page_content": ["=", ""]},
        fields=["name"],
        limit=1
    )
  
    if not web_page_doc:
        return

    web_page_name = web_page_doc[0].name

    # Get AI agent settings
    web_content_setting = frappe.get_single("Web Schema Generation Setting")
    content_formatter_agent_doc_name = web_content_setting.web_page_content_agent

    ai_agent = frappe.get_doc("AI Agent", content_formatter_agent_doc_name)
    web_page = frappe.get_doc("Web Page", web_page_name)

    # Prepare input for AI
    ai_input_data = {
        "webpage_title": web_page.title,
        "seo_title": web_page.seo_title,
        "seo_description": web_page.small_description,
        "main_section_html": web_page.main_section_html,
    }

    # Invoke AI Agent
    result = ai_agent.invoke(**ai_input_data)

    # Save result to the web page
    web_page.web_page_content = result.json()
    web_page.save()

    frappe.db.commit()
    frappe.logger().info(f"✅ Web Page Content generated for: {web_page_name}")


import frappe
import json

@frappe.whitelist()
def generate_nextjs_page(web_page_name: str):
    """
    Generate a Next.js page using AI Agent linked in Web Content Settings
    and update Web Page.context_script
    """

    try:
        # Step 1: Fetch Web Page record
        web_page = frappe.get_doc("Web Page", web_page_name)

        # Step 2: Get linked AI Agent from Web Content Settings
        web_content_settings = frappe.get_single("Web Content Settings")
        ai_agent_name = web_content_settings.ai_agent

        if not ai_agent_name:
            frappe.throw("No AI Agent is linked in Web Content Settings")

        ai_agent_doc = frappe.get_doc("AI Agent", ai_agent_name)
        ai_service = ai_agent_doc.agent_service

        if not ai_service:
            frappe.throw(f"AI Agent '{ai_agent_name}' has no configured service")

        # Step 3: Define existing components JSON
        components_json = {
            "components": [
    {
      "name": "PricingCards",
      "path": "@/components/ui/ComponentShowcase2",
      "import": "{ PricingCards }",
      "props": {}
    },
    {
      "name": "ContactForm",
      "path": "@/components/ui/ComponentShowcase2",
      "import": "{ ContactForm }",
      "props": {}
    },
    {
      "name": "Benefits",
      "path": "@/components/sections/benefits",
      "import": "default",
      "props": {
        "data?": {
          "component_type?": "Card",
          "title?": "string",
          "subtitle?": "string",
          "benefits?": [
            {
              "number": "number",
              "suffix": "string",
              "label": "string",
              "header": "string",
              "description": "string",
              "icon": "string",
              "palette": { "iconBg": "string", "iconColor": "string" }
            }
          ],
          "ctaButton?": { "text?": "string", "action?": "string" }
        }
      }
    },
    {
      "name": "BusinessSlider",
      "path": "@/components/sections/business-slider",
      "import": "default",
      "props": { "data?": "Record<string, any>" }
    },
    {
      "name": "ClientLogos",
      "path": "@/components/sections/client-logos",
      "import": "default",
      "props": {
        "data?": {
          "component_type?": "Carousal",
          "title?": "string",
          "subtitle?": "string",
          "clients?": "any[]",
          "carousel?": { "autoPlay?": "boolean", "interval?": "number", "showArrows?": "boolean", "showIndicators?": "boolean" }
        }
      }
    },
    {
      "name": "Comment",
      "path": "@/components/sections/comment",
      "import": "default",
      "props": { "data?": { "text?": "string", "symbol?": "string" } }
    },
    {
      "name": "ContactFormSection",
      "path": "@/components/sections/contact-form",
      "import": "default",
      "props": { "title?": "string", "subtitle?": "string", "submitLabel?": "string", "toEmail?": "string" }
    },
    {
      "name": "ContactInfo",
      "path": "@/components/sections/contact-info",
      "import": "default",
      "props": {
        "data?": {
          "title?": "string",
          "subtitle?": "string",
          "contactMethods?": "Array< { icon: string; title?: string; method?: string; value: string; description: string } >",
          "form?": { "title": "string", "nameLabel": "string", "namePlaceholder": "string", "emailLabel": "string", "emailPlaceholder": "string", "messageLabel": "string", "messagePlaceholder": "string", "submitText": "string" },
          "contactStats?": "Array< { metric: string; label: string; description: string; icon: string; iconColor: string; iconBg: string } >",
          "officeLocations?": "Array< { city: string; address: string; phone: string; email: string; hours: string; timezone: string; icon: string; iconColor: string; iconBg: string } >",
          "cta?": { "title": "string", "description": "string", "primaryButton": "string", "secondaryButton": "string" }
        }
      }
    },
    {
      "name": "ContactWithMap",
      "path": "@/components/sections/contact-with-map",
      "import": "default",
      "props": {
        "data?": {
          "component_type": "Text",
          "title?": "string",
          "subtitle?": "string",
          "items?": "Array< { label: string; value: string; href?: string; icon?: string } >",
          "addressTitle?": "string",
          "addressLines?": "string[]",
          "mapEmbedUrl?": "string"
        }
      }
    },
    {
      "name": "ContentIllustrationLeft",
      "path": "@/components/sections/content-illustration-left",
      "import": "default",
      "props": { "data?": { "component_type?": "Text", "title": "string", "paragraphs": "string[]", "imageSrc": "string", "imageAlt?": "string" } }
    },
    {
      "name": "ContentIllustrationRight",
      "path": "@/components/sections/content-illustration-right",
      "import": "default",
      "props": { "data?": { "component_type?": "Text", "title": "string", "paragraphs": "string[]", "imageSrc": "string", "imageAlt?": "string" } }
    },
    {
      "name": "DynamicHero",
      "path": "@/components/sections/dynamic-hero",
      "import": "default",
      "props": {
        "tagline?": "string",
        "headline?": "string",
        "highlightWords?": "string[]",
        "description?": "string",
        "primaryButton?": { "text": "string" },
        "secondaryButton?": { "text": "string" },
        "heroImage?": { "alt": "string", "src?": "string", "videoSrc?": "string", "poster?": "string" },
        "features?": "Array< { icon: ReactComponent; title: string; description: string } >",
        "backgroundColor?": "string",
        "accentColor?": "'orange'|'blue'|'green'"
      }
    },
    {
      "name": "CTA",
      "path": "@/components/sections/cta",
      "import": "default",
      "props": {
        "data?": {
          "component_type?": "Text",
          "subheading?": { "text?": "string", "icon?": "string" },
          "title?": "string",
          "description?": "string",
          "primaryButton?": { "text?": "string", "icon?": "string", "action?": "string" },
          "secondaryButton?": { "text?": "string", "icon?": "string", "action?": "string" },
          "trustIndicator?": { "text?": "string", "icon?": "string" }
        }
      }
    },
    {
      "name": "Differentiators",
      "path": "@/components/sections/differentiators",
      "import": "default",
      "props": {
        "data?": {
          "component_type?": "FOQ",
          "title?": "string",
          "subtitle?": "string",
          "differentiators?": "Array< { icon: string; title: string; description: string; iconColor: string; iconBg: string } >",
          "quote?": { "text?": "string", "highlight?": "string", "author?": "string" }
        }
      }
    },
    {
      "name": "ERPIntroText",
      "path": "@/components/sections/erp-intro-text",
      "import": "default",
      "props": { "data?": { "component_type?": "Text", "title": "string", "paragraphs": "string[]", "highlightLink?": { "text": "string", "href": "string" } } }
    },
    {
      "name": "ForwardContractingText",
      "path": "@/components/sections/forward-contracting-text",
      "import": "default",
      "props": { "data?": { "component_type?": "Text", "title?": "string", "paragraphs": "string[]" } }
    },
    {
      "name": "GlobalPresence",
      "path": "@/components/sections/global-presence",
      "import": "default",
      "props": {
        "data?": {
          "title?": "string",
          "subtitle?": "string",
          "locations?": "Array< { city: string; country: string; timezone: string; icon: string; color: string } >",
          "globalStats?": "Array< { metric: string; value: string; description: string; icon: string; iconColor: string; iconBg: string } >",
          "globalOffices?": "Array< { city: string; country: string; region: string; address: string; phone: string; email: string; team: string; timezone: string; services: string[]; icon: string; iconColor: string; iconBg: string } >",
          "globalCoverage?": { "regions": "Array< { name: string; cities: string[] } >" }
        }
      }
    },
    {
      "name": "HeroSimple",
      "path": "@/components/sections/hero_section_without_button",
      "import": "default",
      "props": { "data?": "Record<string, any>" }
    },
    {
      "name": "Hero",
      "path": "@/components/sections/hero",
      "import": "default",
      "props": { "data?": "Record<string, any>" }
    },
    {
      "name": "JobDetailSection",
      "path": "@/components/sections/job-detail",
      "import": "default",
      "props": { "id?": "string", "className?": "string", "data?": { "title?": "string", "jobDescription?": "string[]", "keySkills?": "string[]", "image?": { "src": "string", "alt": "string", "width?": "number", "height?": "number" }, "cta?": { "primary?": { "label": "string", "href?": "string" }, "secondary?": { "label": "string", "href?": "string" } } } }
    },
    {
      "name": "Points",
      "path": "@/components/sections/points",
      "import": "default",
      "props": { "data?": { "component_type?": "Text", "title?": "string", "points": "string[]" } }
    },
    {
      "name": "ProcessWorkflow",
      "path": "@/components/sections/process-workflow",
      "import": "default",
      "props": { "data?": { "component_type?": "Timeline", "title?": "string", "subtitle?": "string", "processSteps?": "Array< { step: string; title: string; description: string; icon: string; details: string[]; duration: string; iconColor: string; iconBg: string } >", "stats?": { "steps": "string", "weeks": "string", "transparency": "string", "support": "string" } } }
    },
    {
      "name": "ResourceCenter",
      "path": "@/components/sections/resource-center",
      "import": "default",
      "props": { "data?": { "title?": "string", "subtitle?": "string", "resourceCategories?": "Array< { category: string; count: number; description: string; icon: string; iconColor: string; iconBg: string } >", "resources?": "Array< { title: string; type: string; category: string; description: string; duration: string; downloads: number; rating: number; icon: string; iconColor: string; iconBg: string } >", "upcomingEvents?": "Array< { title: string; date: string; time: string; type: string; attendees: number; description: string; icon: string; iconColor: string; iconBg: string } >", "resourceStats?": { "resources": "string", "downloads": "string", "rating": "string", "learners": "string" } } }
    },
    {
      "name": "ResponsiveCardGrid",
      "path": "@/components/sections/responsive-card-grid",
      "import": "default",
      "props": { "data?": { "title?": "string", "subtitle?": "string", "cards": "Array< { id: string|number; title: string; description: string; image?: string; imageAlt?: string; className?: string; icon?: string; iconColor?: string; iconBg?: string } >", "layout?": "'standard'|'compact'", "showImage?": "boolean", "imageHeight?": "number", "imageWidth?": "number", "cardClassName?": "string", "variant?": "'standard'|'iconCard'", "debug?": "boolean" }, "className?": "string" }
    },
    {
      "name": "SecurityCompliance",
      "path": "@/components/sections/security-compliance",
      "import": "default",
      "props": { "data?": { "title?": "string", "subtitle?": "string", "securityStats": "Array< { metric: string; label: string; description: string; icon?: string; iconColor?: string; iconBg?: string } >" }, "className?": "string" }
    },
    {
      "name": "StatsShowcase",
      "path": "@/components/sections/stats-showcase",
      "import": "default",
      "props": { "data?": "Record<string, any>" }
    },
    {
      "name": "TeamExpertise",
      "path": "@/components/sections/team-expertise",
      "import": "default",
      "props": { "data?": "Record<string, any>" }
    },
    {
      "name": "TechnologyStack",
      "path": "@/components/sections/technology-stack",
      "import": "default",
      "props": { "data?": "Record<string, any>" }
    },
    {
      "name": "Testimonials",
      "path": "@/components/sections/testimonials",
      "import": "default",
      "props": { "data?": "Record<string, any>" }
    },
    {
      "name": "TextSection",
      "path": "@/components/sections/text",
      "import": "default",
      "props": { "data?": { "component_type?": "Text", "title?": "string", "paragraphs": "string[]" } }
    },
    {
      "name": "Video",
      "path": "@/components/sections/video",
      "import": "default",
      "props": { "data?": { "component_type?": "Video", "title?": "string", "url?": "string", "videoId?": "string" } }
    },
    {
      "name": "YouTubeEmbed",
      "path": "@/components/sections/YouTubeEmbed",
      "import": "default",
      "props": { "url": "string", "title?": "string", "className?": "string", "aspectRatio?": "'16:9'|'4:3'|'1:1'|'21:9'" }
    },
    {
      "name": "AlternativeTimeline",
      "path": "@/components/ui/AlternativeTimeline",
      "import": "default",
      "props": {}
    },
    {
      "name": "Card",
      "path": "@/components/ui/card",
      "import": "{ Card }",
      "props": "React.ComponentProps<'div'>"
    },
    {
      "name": "CardHeader",
      "path": "@/components/ui/card",
      "import": "{ CardHeader }",
      "props": "React.ComponentProps<'div'>"
    },
    {
      "name": "CardContent",
      "path": "@/components/ui/card",
      "import": "{ CardContent }",
      "props": "React.ComponentProps<'div'>"
    },
    {
      "name": "CardFooter",
      "path": "@/components/ui/card",
      "import": "{ CardFooter }",
      "props": "React.ComponentProps<'div'>"
    },
    {
      "name": "CardTitle",
      "path": "@/components/ui/card",
      "import": "{ CardTitle }",
      "props": "React.ComponentProps<'div'>"
    },
    {
      "name": "CardDescription",
      "path": "@/components/ui/card",
      "import": "{ CardDescription }",
      "props": "React.ComponentProps<'div'>"
    },
    {
      "name": "CardAction",
      "path": "@/components/ui/card",
      "import": "{ CardAction }",
      "props": "React.ComponentProps<'div'>"
    },
    {
      "name": "CompanyHistoryTimeline",
      "path": "@/components/ui/CompanyHistoryTimeline",
      "import": "default",
      "props": { "data?": { "title?": "string", "subtitle?": "string", "events?": "Array< { date: string; title: string; location: string; description: string; icon: any; position: 'left'|'right'; illustration?: ReactNode; buttonText?: string; buttonLink?: string } >" } }
    },
    {
      "name": "ComponentRenderer",
      "path": "@/components/ui/ComponentRenderer",
      "import": "{ ComponentRenderer }",
      "props": { "componentData": { "component": "string", "data": "any" } }
    },
    {
      "name": "PageRenderer",
      "path": "@/components/ui/ComponentRenderer",
      "import": "{ PageRenderer }",
      "props": { "components": "Array< { component: string; data: any } >" }
    },
    {
      "name": "TimelineSection",
      "path": "@/components/ui/ComponentShowcase3",
      "import": "{ TimelineSection }",
      "props": { "timelineItems?": "Array< { year: string; title: string; description: string; icon: any } >", "title?": "string", "subtitle?": "string" }
    },
    {
      "name": "FullScreenTimeline",
      "path": "@/components/ui/ComponentShowcase3",
      "import": "{ FullScreenTimeline }",
      "props": { "timelineItems?": "Array< { year: string; title: string; description: string; icon: any } >", "title?": "string", "subtitle?": "string" }
    },
    {
      "name": "TeamSection",
      "path": "@/components/ui/ComponentShowcase3",
      "import": "{ TeamSection }",
      "props": {}
    },
    {
      "name": "BlogGrid",
      "path": "@/components/ui/ComponentShowcase3",
      "import": "{ BlogGrid }",
      "props": {}
    },
    {
      "name": "FAQSection",
      "path": "@/components/ui/ComponentShowcase3",
      "import": "{ FAQSection }",
      "props": {}
    },
    {
      "name": "TimelineCarousel",
      "path": "@/components/ui/ComponentShowcase3",
      "import": "{ TimelineCarousel }",
      "props": { "timelineItems?": "Array< { year: string; title: string; description: string; icon: any } >", "title?": "string", "subtitle?": "string", "onFinish?": "() => void" }
    },
    {
      "name": "ERPModules",
      "path": "@/components/ui/ERPModules",
      "import": "default",
      "props": { "data?": { "companyName?": "string", "companyDescription?": "string", "yearsOfExperience?": "number", "statistics?": "Array< { number: string; label: string } >", "services?": "Array< { id: string; title: string; description: string; icon: ReactNode } >" } }
    },
    {
      "name": "FileUpload",
      "path": "@/components/ui/FileUpload",
      "import": "default",
      "props": { "data?": { "title?": "string", "subtitle?": "string", "maxFiles?": "number", "maxFileSize?": "number", "acceptedTypes?": "string[]", "uploadButtonText?": "string", "dragText?": "string" } }
    },
    {
      "name": "InquiryForm",
      "path": "@/components/ui/InquiryForm",
      "import": "default",
      "props": { "data?": "any", "className?": "string" }
    },
    {
      "name": "TimelineComponent",
      "path": "@/components/ui/TimelineComponent",
      "import": "default",
      "props": {}
    },
    {
      "name": "ToggleGroup",
      "path": "@/components/ui/toggle-group",
      "import": "{ ToggleGroup }",
      "props": "Radix ToggleGroup.Root props"
    },
    {
      "name": "ToggleGroupItem",
      "path": "@/components/ui/toggle-group",
      "import": "{ ToggleGroupItem }",
      "props": "Radix ToggleGroup.Item props"
    },
    {
      "name": "YearFilterTimeline",
      "path": "@/components/ui/YearFilterTimeline",
      "import": "default",
      "props": {}
    },
    {
      "name": "VerticalTimeline",
      "path": "@/components/ui/VerticalTimeline",
      "import": "default",
      "props": {}
    },
    {
      "name": "VisualTimeline",
      "path": "@/components/ui/VisualTimeline",
      "import": "default",
      "props": {}
    }
  ]
        }

        # Get hero image
        hero_image = web_page.get("image") or ""
        
        # Validate if image exists
        if not hero_image:
            frappe.msgprint("Warning: No hero image found. Using placeholder.", indicator="orange")
            hero_image = "/api/fb/n/files/placeholder.jpg"


        # Step 5: Prepare AI input data
        ai_input_data = {
            "seo_title": web_page.seo_title,
            "small_description": web_page.small_description,  
            "main_section_md": web_page.main_section_md,      
            "image": hero_image,
            "existing_component_str": json.dumps(components_json, ensure_ascii=False)
        }

        # Log input
        frappe.log_error(
            title="AI Agent Input Data",
            message=f"Web Page: {web_page_name}\n\nInput Data:\n{frappe.as_json(ai_input_data, indent=2)}"
        )

        # Step 6: Invoke AI Agent
        result = None
        try:
            result = ai_service.invoke(**ai_input_data)

            frappe.log_error(
                title="AI Agent Raw Output",
                message=f"Result Type: {type(result)}\nResult Length: {len(str(result)) if result else 0}"
            )

        except Exception as e:
            frappe.log_error(
                title="AI Agent Invocation Failed",
                message=f"Error: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
            )
            frappe.throw(f"AI Agent invocation failed: {str(e)}")

        # Step 7: Extract content based on result type
        generated_content = None

        try:
            # Check if result is already a string (JSON)
            if isinstance(result, str):
                frappe.log_error(
                    title="AI Agent Result is String",
                    message="Parsing JSON string directly"
                )
                generated_content = json.loads(result)

            # Check if result has model_dump (Pydantic v2)
            elif hasattr(result, 'model_dump'):
                frappe.log_error(
                    title="AI Agent Using model_dump()",
                    message="Extracting via Pydantic model_dump()"
                )
                generated_content = result.model_dump()

            # Check if result has dict (Pydantic v1)
            elif hasattr(result, 'dict'):
                frappe.log_error(
                    title="AI Agent Using dict()",
                    message="Extracting via Pydantic dict()"
                )
                generated_content = result.dict()

            # Check if result is already a dict
            elif isinstance(result, dict):
                frappe.log_error(
                    title="AI Agent Result is Dict",
                    message="Using result directly"
                )
                generated_content = result

            else:
                frappe.log_error(
                    title="AI Agent Unknown Format",
                    message=f"Result Type: {type(result)}\nAttempting to convert to string and parse"
                )
                # Try converting to string and parsing
                generated_content = json.loads(str(result))

            frappe.log_error(
                title="AI Agent Content Extracted Successfully",
                message=f"Content Type: {type(generated_content)}\nKeys: {list(generated_content.keys()) if isinstance(generated_content, dict) else 'Not a dict'}"
            )

        except json.JSONDecodeError as e:
            frappe.log_error(
                title="AI Agent JSON Parse Error",
                message=f"Error: {str(e)}\nResult Type: {type(result)}\nResult Preview:\n{str(result)[:1000]}"
            )
            frappe.throw(f"Failed to parse AI Agent JSON output: {str(e)}")

        except Exception as e:
            frappe.log_error(
                title="AI Agent Content Extraction Failed",
                message=f"Error: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
            )
            frappe.throw(f"Failed to extract AI Agent content: {str(e)}")

        # Step 8: Validate content
        if not generated_content or generated_content == {}:
            frappe.throw(
                f"AI Agent '{ai_agent_name}' returned empty response. "
                "Please check the AI Agent configuration and prompts."
            )

        # Step 9: Extract page code
        try:
            if 'page' not in generated_content:
                frappe.log_error(
                    title="AI Agent Missing 'page' Key",
                    message=f"Available keys: {list(generated_content.keys())}\n\nFull output (first 2000 chars):\n{frappe.as_json(generated_content, indent=2)[:2000]}"
                )
                frappe.throw("AI output missing required 'page' key")

            page_data = generated_content.get("page", {})
            page_code = page_data.get("code", "")

            if not page_code:
                frappe.log_error(
                    title="AI Agent Empty Page Code",
                    message=f"Page data: {frappe.as_json(page_data, indent=2)}"
                )
                frappe.throw("AI Agent returned empty page code")

            components_count = len(generated_content.get("components", []))
            component_names = [c.get("name", "Unknown") for c in generated_content.get("components", [])]

            # Log success with details
            frappe.log_error(
                title="AI Agent Page Generation Success",
                message=f"Web Page: {web_page_name}\n"
                        f"Components Generated: {components_count}\n"
                        f"Page Code Length: {len(page_code):,} characters\n\n"
                        f"Component Names:\n" +
                        "\n".join([f"  - {name}" for name in component_names]) +
                        f"\n\nPage Code Preview (first 500 chars):\n{page_code[:500]}..."
            )

        except Exception as e:
            if "AI" in str(e):
                raise
            frappe.log_error(
                title="AI Output Processing Error",
                message=f"Error: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
            )
            frappe.throw(f"Failed to process AI output: {str(e)}")

        # Step 10: Store generated code in the Web Page
        
        if isinstance(page_code, str):
            # Decode escaped newlines to actual ones
            page_code = page_code.replace("\\n", "\n").replace("\\t", "\t")
            
        web_page.context_script = page_code
        web_page.save(ignore_permissions=True)
        frappe.db.commit()

        # Success message
        frappe.msgprint(
            f"✅ <strong>Next.js page generated successfully!</strong><br><br>",
            title="AI Page Generation Complete",
            indicator="green"
        )

        return {
            "status": "success",
            "message": "Next.js page generated successfully!",
            "page_code_length": len(page_code),
            "components_count": components_count,
            "components": component_names
        }

    except Exception as e:
        frappe.log_error(
            title="AI Page Generation Failed",
            message=f"Web Page: {web_page_name}\nError: {str(e)}\n\nTraceback: {frappe.get_traceback()}"
        )
        frappe.throw(f"Failed to generate page: {str(e)}")