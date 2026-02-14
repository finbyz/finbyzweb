// Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("NextJS Page", {
    title: function (frm) {
        if (frm.doc.title) {
            let slug = frappe.scrub(frm.doc.title).replace(/_/g, "-");
            // If route is empty, always set it.
            if (!frm.doc.route || frm.doc.route === "/") {
                frm.set_value("route", "/" + slug);
            }
        }
    },
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Revise Content"), () => {
                frappe.prompt([
                    {
                        label: __("Revision Instruction"),
                        fieldname: "user_input",
                        fieldtype: "Small Text",
                        reqd: 1,
                        description: __("Example: Make it more professional, or focus on benefits.")
                    }
                ], (values) => {
                    frappe.dom.freeze(__("Revising content..."));
                    const run_ai = () => {
                        frappe.call({
                            method: "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.revise_content",
                            args: { doc_name: frm.doc.name, user_input: values.user_input },
                            callback: function (r) {
                                frappe.dom.unfreeze();
                                if (r.message && r.message.success) {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: r.message.message, indicator: "green" });
                                }
                            },
                            error: () => frappe.dom.unfreeze()
                        });
                    };
                    if (frm.is_dirty()) frm.save().then(run_ai); else run_ai();
                }, __("Interactive Revision"), __("Revise"));
            }, __("AI Actions"));

            frm.add_custom_button(__("Generate SEO"), () => {
                frappe.prompt([
                    {
                        label: __("SEO Intent / context"),
                        fieldname: "user_input",
                        fieldtype: "Small Text",
                        description: __("Optional context for SEO generation")
                    }
                ], (values) => {
                    frappe.dom.freeze(__("Generating SEO..."));
                    const run_ai = () => {
                        frappe.call({
                            method: "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.generate_seo",
                            args: { doc_name: frm.doc.name, user_input: values.user_input },
                            callback: function (r) {
                                frappe.dom.unfreeze();
                                if (r.message && r.message.success) {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: r.message.message, indicator: "green" });
                                }
                            },
                            error: () => frappe.dom.unfreeze()
                        });
                    };
                    if (frm.is_dirty()) frm.save().then(run_ai); else run_ai();
                }, __("AI SEO Generation"), __("Generate"));
            }, __("AI Actions"));

            frm.add_custom_button(__("Generate FAQs"), () => {
                frappe.prompt([
                    {
                        label: __("FAQ Intent / Context"),
                        fieldname: "user_input",
                        fieldtype: "Small Text",
                        description: __("Optional context for FAQ generation")
                    }
                ], (values) => {
                    frappe.dom.freeze(__("Generating FAQs..."));
                    const run_ai = () => {
                        frappe.call({
                            method: "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.generate_faqs",
                            args: { doc_name: frm.doc.name, user_input: values.user_input },
                            callback: function (r) {
                                frappe.dom.unfreeze();
                                if (r.message && r.message.success) {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: r.message.message, indicator: "green" });
                                }
                            },
                            error: () => frappe.dom.unfreeze()
                        });
                    };
                    if (frm.is_dirty()) frm.save().then(run_ai); else run_ai();
                }, __("AI FAQ Generation"), __("Generate"));
            }, __("AI Actions"));

            frm.add_custom_button(__("Build Schema"), () => {
                frappe.prompt([
                    {
                        label: __("Schema Instructions"),
                        fieldname: "user_input",
                        fieldtype: "Small Text",
                        description: __("Optional instructions for schema generation")
                    }
                ], (values) => {
                    frappe.dom.freeze(__("Building schema..."));
                    const run_ai = () => {
                        frappe.call({
                            method: "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.generate_schema",
                            args: { doc_name: frm.doc.name, user_input: values.user_input },
                            callback: function (r) {
                                frappe.dom.unfreeze();
                                if (r.message && r.message.success) {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: r.message.message, indicator: "green" });
                                }
                            },
                            error: () => frappe.dom.unfreeze()
                        });
                    };
                    if (frm.is_dirty()) frm.save().then(run_ai); else run_ai();
                }, __("AI Schema Builder"), __("Build"));
            }, __("AI Actions"));

            frm.add_custom_button(__("Create Social Media Post"), () => {
                let d = new frappe.ui.Dialog({
                    title: __("Create Social Media Post"),
                    fields: [
                        {
                            label: __("Instructions (Optional)"),
                            fieldname: "user_input",
                            fieldtype: "Small Text",
                            description: __("E.g. Focus on benefits, use a casual tone, highlight the offer...")
                        },
                        {
                            fieldtype: "Section Break",
                            label: __("Select Platform(s)")
                        },
                        {
                            label: __("LinkedIn"),
                            fieldname: "linkedin",
                            fieldtype: "Check",
                            default: 1,
                            change: function () {
                                d.fields_dict.linkedin_credential.df.hidden = !d.get_value("linkedin");
                                d.fields_dict.linkedin_credential.refresh();
                            }
                        },
                        {
                            label: __("LinkedIn Credential"),
                            fieldname: "linkedin_credential",
                            fieldtype: "Link",
                            options: "LinkedIn Integration",
                            description: __("Optional — select a LinkedIn account"),
                            hidden: 0
                        },
                        {
                            fieldtype: "Column Break"
                        },
                        {
                            label: __("X (Twitter)"),
                            fieldname: "twitter",
                            fieldtype: "Check",
                            default: 1,
                            change: function () {
                                d.fields_dict.twitter_credential.df.hidden = !d.get_value("twitter");
                                d.fields_dict.twitter_credential.refresh();
                            }
                        },
                        {
                            label: __("Twitter Credential"),
                            fieldname: "twitter_credential",
                            fieldtype: "Link",
                            options: "Twitter Integration",
                            description: __("Optional — select a Twitter account"),
                            hidden: 0
                        }
                    ],
                    size: "small",
                    primary_action_label: __("Generate"),
                    primary_action: function (values) {
                        let platforms = [];
                        let credentials = {};
                        if (values.linkedin) {
                            platforms.push("LinkedIn");
                            if (values.linkedin_credential) {
                                credentials["LinkedIn"] = {
                                    credential_type: "LinkedIn Integration",
                                    credential: values.linkedin_credential
                                };
                            }
                        }
                        if (values.twitter) {
                            platforms.push("X (Twitter)");
                            if (values.twitter_credential) {
                                credentials["X (Twitter)"] = {
                                    credential_type: "Twitter Integration",
                                    credential: values.twitter_credential
                                };
                            }
                        }

                        if (platforms.length === 0) {
                            frappe.msgprint(__("Please select at least one platform."));
                            return;
                        }

                        d.hide();
                        frappe.dom.freeze(__("Generating social media posts..."));

                        const run_ai = () => {
                            frappe.call({
                                method: "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.generate_social_post",
                                args: {
                                    doc_name: frm.doc.name,
                                    user_input: values.user_input,
                                    platforms: JSON.stringify(platforms),
                                    credentials: JSON.stringify(credentials)
                                },
                                callback: function (r) {
                                    frappe.dom.unfreeze();
                                    if (r.message && r.message.success) {
                                        let links = (r.message.posts || []).map(p =>
                                            `<a href="/app/social-media-post/${p.name}">${p.platform}: ${p.name}</a>`
                                        ).join("<br>");

                                        frappe.msgprint({
                                            title: __("Social Media Posts Created"),
                                            message: r.message.message + "<br><br>" + links,
                                            indicator: "green"
                                        });
                                    } else {
                                        frappe.msgprint({
                                            title: __("Error"),
                                            message: (r.message && r.message.message) || __("Failed to generate posts"),
                                            indicator: "red"
                                        });
                                    }
                                },
                                error: () => frappe.dom.unfreeze()
                            });
                        };

                        if (frm.is_dirty()) frm.save().then(run_ai); else run_ai();
                    }
                });
                d.show();
            }, __("AI Actions"));
        }

        // Add bulk regeneration button to FAQs grid
        frm.fields_dict.faqs.grid.add_custom_button(__("Regenerate Selected"), () => {
            const selected = frm.fields_dict.faqs.grid.get_selected();
            if (selected.length === 0) {
                frappe.msgprint(__("Please select at least one FAQ to regenerate."));
                return;
            }

            const faqs_to_revise = selected.map(idx => {
                const row = frm.doc.faqs.find(f => f.name === idx);
                return { question: row.question, answer: row.answer, idx: idx };
            });

            frappe.prompt([
                {
                    label: __("Instruction (Optional)"),
                    fieldname: "user_input",
                    fieldtype: "Small Text",
                    description: __("Example: Make it more concise, or use simpler language.")
                }
            ], (values) => {
                frappe.dom.freeze(__("Regenerating FAQs..."));
                const run_ai = () => {
                    frappe.call({
                        method: "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.revise_faqs",
                        args: {
                            doc_name: frm.doc.name,
                            faqs_to_revise: faqs_to_revise,
                            user_input: values.user_input
                        },
                        callback: (r) => {
                            frappe.dom.unfreeze();
                            if (r.message && r.message.success) {
                                frm.reload_doc();
                                frappe.show_alert({ message: r.message.message, indicator: "green" });
                            }
                        },
                        error: () => frappe.dom.unfreeze()
                    });
                };
                if (frm.is_dirty()) frm.save().then(run_ai); else run_ai();
            }, __("AI Regeneration"), __("Regenerate"));
        });
    }
});

frappe.ui.form.on("FAQs", {
    form_render: function (frm, cdt, cdn) {
        if (frm.doc.doctype !== "NextJS Page") return;

        console.log("AI FAQ: Injecting button into row dialog", cdn);

        const inject = () => {
            const grid = frm.fields_dict.faqs.grid;
            const row = grid.grid_rows_by_docname[cdn];

            if (!row || !row.grid_form) return;

            const $wrapper = row.grid_form.fields_dict.answer.$wrapper;
            if (!$wrapper) return;

            // Avoid duplicate button
            if ($wrapper.find(".btn-revise-faq").length) return;

            const btn = $(`<button class="btn btn-xs btn-primary btn-revise-faq" style="margin-top: 10px;">
                <i class="fa fa-magic"></i> ${__("Revise with AI")}
            </button>`);

            $wrapper.append(btn);

            btn.on("click", function () {
                frappe.prompt([
                    {
                        label: __("Revision Instruction"),
                        fieldname: "user_input",
                        fieldtype: "Small Text",
                        description: __("Example: Make it more professional, or add more detail.")
                    }
                ], (values) => {
                    frappe.dom.freeze(__("Revising FAQ..."));

                    const run_ai = () => {
                        frappe.call({
                            method: "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.revise_faqs",
                            args: {
                                doc_name: frm.doc.name,
                                faqs_to_revise: [{
                                    question: frappe.model.get_value(cdt, cdn, "question"),
                                    answer: frappe.model.get_value(cdt, cdn, "answer"),
                                    idx: cdn
                                }],
                                user_input: values.user_input
                            },
                            callback: (r) => {
                                frappe.dom.unfreeze();
                                if (r.message && r.message.success) {
                                    frm.reload_doc();
                                    frappe.show_alert({ message: r.message.message, indicator: "green" });
                                }
                            },
                            error: () => frappe.dom.unfreeze()
                        });
                    };

                    if (frm.is_dirty()) {
                        frm.save().then(run_ai);
                    } else {
                        run_ai();
                    }
                }, __("AI FAQ Revision"), __("Revise"));
            });
        };

        // Use setTimeout to ensure the grid form is fully rendered
        setTimeout(inject, 200);
    }
});
