// Copyright (c) 2026, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SITE_URL = "https://finbyz.tech";
const AI_METHOD_PREFIX = "finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.";

// ---------------------------------------------------------------------------
// Core helper: save-if-dirty → freeze → call → unfreeze
// ---------------------------------------------------------------------------

/**
 * Run an AI frappe.call, auto-saving first if the form is dirty.
 *
 * @param {object} frm        - Frappe form instance
 * @param {string} method     - Python method name (full dotted path)
 * @param {object} args       - Extra args (doc_name is added automatically)
 * @param {string} freeze_msg - Message shown while frozen
 * @param {function} on_success - Called with r.message on success
 * @param {function} [on_error]  - Optional, called on network/server error
 */
function run_ai(frm, method, args, freeze_msg, on_success, on_error) {
    const execute = () => {
        frappe.dom.freeze(__(freeze_msg));
        frappe.call({
            method,
            args: { doc_name: frm.doc.name, ...args },
            callback(r) {
                frappe.dom.unfreeze();
                if (r.message && r.message.success) {
                    on_success(r.message);
                } else {
                    frappe.show_alert({
                        message: (r.message && r.message.message) || __("Action failed."),
                        indicator: "orange"
                    });
                }
            },
            error() {
                frappe.dom.unfreeze();
                frappe.show_alert({ message: __("Server error. Check the Error Log."), indicator: "red" });
                on_error && on_error();
            }
        });
    };
    if (frm.is_dirty()) frm.save().then(execute); else execute();
}

// ---------------------------------------------------------------------------
// Main form events
// ---------------------------------------------------------------------------

frappe.ui.form.on("NextJS Page", {

    parent_nextjs_page(frm) {
        // Guard: circular reference
        if (frm.doc.parent_nextjs_page === frm.doc.name) {
            frappe.msgprint(__("A page cannot be its own parent."));
            frm.set_value("parent_nextjs_page", null);
            return;
        }

        const current_slug = (frm.doc.route || "")
            .replace(/^\/+|\/+$/g, "")
            .split("/")
            .pop();

        if (!current_slug) {
            frappe.msgprint(__("Please set a route or page name before assigning a parent."));
            frm.set_value("parent_nextjs_page", null);
            return;
        }

        if (!frm.doc.parent_nextjs_page) {
            // Parent removed → revert to bare slug
            frm.set_value("route", `/${current_slug}`);
            frm.set_value("actual_route", `/${current_slug}`);
            return;
        }

        frappe.db
            .get_value("NextJS Page", frm.doc.parent_nextjs_page, "route")
            .then(r => {
                const parent_route = r.message && r.message.route;
                if (!parent_route) {
                    frappe.msgprint(__("Could not fetch parent route. Please check the parent page."));
                    frm.set_value("parent_nextjs_page", null);
                    return;
                }

                const new_route = `/${parent_route.replace(/^\/+|\/+$/g, "")}/${current_slug}`;
                const old_route = frm.doc.route || "/";

                const apply = () => {
                    frm.set_value("route", new_route);
                    frm.set_value("actual_route", new_route);
                };

                if (frm.is_new()) {
                    apply();
                } else {
                    frappe.confirm(
                        __(`Are you sure you want to change the parent?<br><br>
                            <b>Current Route:</b> ${old_route}<br>
                            <b>New Route:</b> ${new_route}<br><br>
                            This will update the page route.`),
                        apply,
                        () => frm.set_value("parent_nextjs_page", null)
                    );
                }
            })
            .catch(() => {
                frappe.msgprint(__("Error fetching parent route. Please try again."));
                frm.set_value("parent_nextjs_page", null);
            });
    },

    title(frm) {
        if (frm.doc.title && (!frm.doc.route || frm.doc.route === "/")) {
            const slug = frappe.scrub(frm.doc.title).replace(/_/g, "-");
            frm.set_value("route", "/" + slug);
            frm.set_value("actual_route", "/" + slug);
        }
    },

    refresh(frm) {
        // ── Web link ──────────────────────────────────────────────────────────
        if (frm.doc.route && frm.doc.is_published) {
            const route = frm.doc.route.replace(/^\/+/, "");
            frm.add_web_link(`${SITE_URL}/${route}`, __("See on Website"));
        }

        if (frm.is_new()) return;

        // ── AI Action buttons ─────────────────────────────────────────────────
        add_ai_buttons(frm);

        // ── FAQs grid: bulk regenerate ────────────────────────────────────────
        frm.fields_dict.faqs.grid.add_custom_button(__("Regenerate Selected"), () => {
            const selected = frm.fields_dict.faqs.grid.get_selected();
            if (!selected.length) {
                frappe.msgprint(__("Please select at least one FAQ to regenerate."));
                return;
            }

            const faqs_to_revise = selected.map(idx => {
                const row = frm.doc.faqs.find(f => f.name === idx);
                return { question: row.question, answer: row.answer, idx };
            });

            frappe.prompt(
                [{
                    label: __("Instruction (Optional)"),
                    fieldname: "user_input",
                    fieldtype: "Small Text",
                    description: __("Example: Make it more concise, or use simpler language.")
                }],
                values => run_ai(
                    frm,
                    AI_METHOD_PREFIX + "revise_faqs",
                    { faqs_to_revise, user_input: values.user_input },
                    "Regenerating FAQs...",
                    msg => { frm.reload_doc(); frappe.show_alert({ message: msg.message, indicator: "green" }); }
                ),
                __("AI Regeneration"),
                __("Regenerate")
            );
        });

        // ── Realtime listener ─────────────────────────────────────────────────
        frappe.realtime.off("nextjs_page_generated");
        frappe.realtime.on("nextjs_page_generated", data => {
            if (data.docname !== frm.doc.name) return;
            if (data.success) {
                frm.reload_doc();
                frappe.msgprint({ title: __("Page Published"), message: `✅ ${data.message}`, indicator: "green" });
            } else {
                frappe.msgprint({ title: __("Generation Failed"), message: data.message || __("Unknown error. Check Error Log."), indicator: "red" });
            }
        });

        // ── Inline Improve button ─────────────────────────────────────────────
        setup_inline_improve_button(frm);
    }
});

// ---------------------------------------------------------------------------
// AI Action buttons
// ---------------------------------------------------------------------------

function add_ai_buttons(frm) {
    const GROUP = __("AI Actions");

    // Helper: prompt → run_ai → reload
    const prompt_and_run = (prompt_title, prompt_label, btn_label, method, freeze_msg, extra_args = {}) => {
        frappe.prompt(
            [{
                label: __(prompt_label),
                fieldname: "user_input",
                fieldtype: "Small Text",
                description: __("Optional — leave blank for default behaviour.")
            }],
            values => run_ai(
                frm,
                AI_METHOD_PREFIX + method,
                { user_input: values.user_input, ...extra_args },
                freeze_msg,
                msg => { frm.reload_doc(); frappe.show_alert({ message: msg.message, indicator: "green" }); }
            ),
            __(prompt_title),
            __(btn_label)
        );
    };

    frm.add_custom_button(__("Revise Content"), () =>
        prompt_and_run("Interactive Revision", "Revision Instruction", "Revise",
            "revise_content", "Revising content..."),
        GROUP);

    frm.add_custom_button(__("Generate SEO"), () =>
        prompt_and_run("AI SEO Generation", "SEO Intent / Context", "Generate",
            "generate_seo", "Generating SEO..."),
        GROUP);

    frm.add_custom_button(__("Generate FAQs"), () =>
        prompt_and_run("AI FAQ Generation", "FAQ Intent / Context", "Generate",
            "generate_faqs", "Generating FAQs..."),
        GROUP);

    frm.add_custom_button(__("Build Schema"), () =>
        prompt_and_run("AI Schema Builder", "Schema Instructions", "Build",
            "generate_schema", "Building schema..."),
        GROUP);

    frm.add_custom_button(__("Find Related Links"), () =>
        prompt_and_run("AI Related Links", "Instructions (Optional)", "Find",
            "generate_related_links", "Finding related links..."),
        GROUP);

    frm.add_custom_button(__("Create Social Media Post"), () =>
        show_social_post_dialog(frm), GROUP);

    frm.add_custom_button(__("Generate Page"), () =>
        show_generate_page_dialog(frm), GROUP);
}

// ---------------------------------------------------------------------------
// Social Media Post dialog
// ---------------------------------------------------------------------------

function show_social_post_dialog(frm) {
    const d = new frappe.ui.Dialog({
        title: __("Create Social Media Post"),
        fields: [
            {
                label: __("Instructions (Optional)"),
                fieldname: "user_input",
                fieldtype: "Small Text",
                description: __("E.g. Focus on benefits, use a casual tone, highlight the offer...")
            },
            { fieldtype: "Section Break", label: __("Select Platform(s)") },
            { label: __("LinkedIn"), fieldname: "linkedin", fieldtype: "Check", default: 1 },
            {
                label: __("LinkedIn Credential"),
                fieldname: "linkedin_credential",
                fieldtype: "Link",
                options: "LinkedIn Integration",
                description: __("Optional — select a LinkedIn account"),
                depends_on: "linkedin"
            },
            { fieldtype: "Column Break" },
            { label: __("X (Twitter)"), fieldname: "twitter", fieldtype: "Check", default: 1 },
            {
                label: __("Twitter Credential"),
                fieldname: "twitter_credential",
                fieldtype: "Link",
                options: "Twitter Integration",
                description: __("Optional — select a Twitter account"),
                depends_on: "twitter"
            }
        ],
        size: "small",
        primary_action_label: __("Generate"),
        primary_action(values) {
            const platforms = [];
            const credentials = {};

            if (values.linkedin) {
                platforms.push("LinkedIn");
                if (values.linkedin_credential) {
                    credentials["LinkedIn"] = { credential_type: "LinkedIn Integration", credential: values.linkedin_credential };
                }
            }
            if (values.twitter) {
                platforms.push("X (Twitter)");
                if (values.twitter_credential) {
                    credentials["X (Twitter)"] = { credential_type: "Twitter Integration", credential: values.twitter_credential };
                }
            }

            if (!platforms.length) {
                frappe.msgprint(__("Please select at least one platform."));
                return;
            }

            d.hide();
            run_ai(
                frm,
                AI_METHOD_PREFIX + "generate_social_post",
                { user_input: values.user_input, platforms: JSON.stringify(platforms), credentials: JSON.stringify(credentials) },
                "Generating social media posts...",
                msg => {
                    const links = (msg.posts || [])
                        .map(p => `<a href="/app/social-media-post/${p.name}">${p.platform}: ${p.name}</a>`)
                        .join("<br>");
                    frappe.msgprint({ title: __("Social Media Posts Created"), message: `${msg.message}<br><br>${links}`, indicator: "green" });
                }
            );
        }
    });
    d.show();
}

// ---------------------------------------------------------------------------
// Generate Page dialog
// ---------------------------------------------------------------------------

function show_generate_page_dialog(frm) {
    if (!frm.doc.page_type) {
        frappe.msgprint({
            title: __("Page Type Required"),
            message: __("Please set the <b>Page Type</b> field before generating a page."),
            indicator: "orange"
        });
        return;
    }

    frappe.confirm(
        __(`Generate and publish a Next.js page for this <b>${frm.doc.page_type}</b>?<br><br>
            The AI agent from <b>NextJS AI Settings</b> will generate the code
            and push it to <b>web.finbyz.com</b>.`),
        () => {
            const execute = () => frappe.call({
                method: AI_METHOD_PREFIX + "generate_nextjs_code",
                args: { doc_name: frm.doc.name },
                callback(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: __("⏳ Generation started in background. You'll be notified when done."),
                            indicator: "blue"
                        }, 7);
                    } else {
                        frappe.msgprint({
                            title: __("Generation Failed"),
                            message: (r.message && r.message.message) || __("Unknown error. Check Error Log."),
                            indicator: "red"
                        });
                    }
                },
                error() {
                    frappe.show_alert({ message: __("Server error. Check Error Log."), indicator: "red" });
                }
            });
            if (frm.is_dirty()) frm.save().then(execute); else execute();
        }
    );
}

// ---------------------------------------------------------------------------
// FAQ row: per-row AI Revise button
// ---------------------------------------------------------------------------

frappe.ui.form.on("FAQs", {
    form_render(frm, cdt, cdn) {
        if (frm.doc.doctype !== "NextJS Page") return;

        setTimeout(() => {
            const row = frm.fields_dict.faqs.grid.grid_rows_by_docname[cdn];
            if (!row || !row.grid_form) return;

            const $wrapper = row.grid_form.fields_dict.answer.$wrapper;
            if (!$wrapper || $wrapper.find(".btn-revise-faq").length) return;

            const $btn = $(`
                <button class="btn btn-xs btn-primary btn-revise-faq" style="margin-top:10px;">
                    <i class="fa fa-magic"></i> ${__("Revise with AI")}
                </button>
            `);
            $wrapper.append($btn);

            $btn.on("click", () => {
                frappe.prompt(
                    [{
                        label: __("Revision Instruction"),
                        fieldname: "user_input",
                        fieldtype: "Small Text",
                        description: __("Example: Make it more professional, or add more detail.")
                    }],
                    values => run_ai(
                        frm,
                        AI_METHOD_PREFIX + "revise_faqs",
                        {
                            faqs_to_revise: [{
                                question: frappe.model.get_value(cdt, cdn, "question"),
                                answer: frappe.model.get_value(cdt, cdn, "answer"),
                                idx: cdn
                            }],
                            user_input: values.user_input
                        },
                        "Revising FAQ...",
                        msg => { frm.reload_doc(); frappe.show_alert({ message: msg.message, indicator: "green" }); }
                    ),
                    __("AI FAQ Revision"),
                    __("Revise")
                );
            });
        }, 200);
    }
});

// ---------------------------------------------------------------------------
// Inline Improve button — shared styles
// ---------------------------------------------------------------------------

function inject_improve_styles() {
    if (document.getElementById("ai-improve-btn-styles")) return;

    const style = document.createElement("style");
    style.id = "ai-improve-btn-styles";
    style.textContent = `
        .ai-improve-btn {
            position: absolute;
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border: 1px solid #0f3460;
            border-radius: 6px;
            padding: 5px 12px;
            color: #e0e0e0;
            font-size: 12px;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(0,0,0,0.35);
            z-index: 1050;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: all 0.15s ease;
            white-space: nowrap;
        }
        .ai-improve-btn:hover {
            background: linear-gradient(135deg, #16213e, #1a1a2e);
            border-color: #533483;
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(83,52,131,0.3);
            color: #fff;
        }
        .ai-improve-popup {
            position: absolute;
            background: #1a1a2e;
            border: 1px solid #0f3460;
            border-radius: 10px;
            padding: 14px;
            width: 320px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            z-index: 1051;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .ai-improve-popup .popup-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #888;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .ai-improve-popup .popup-close {
            cursor: pointer;
            font-size: 16px;
            line-height: 1;
            color: #888;
        }
        .ai-improve-popup .popup-close:hover { color: #fff; }
        .ai-improve-popup textarea {
            background: #16213e;
            border: 1px solid #0f3460;
            border-radius: 6px;
            padding: 8px 10px;
            color: #e0e0e0;
            font-size: 13px;
            width: 100%;
            min-height: 60px;
            resize: vertical;
            font-family: inherit;
        }
        .ai-improve-popup textarea:focus {
            outline: none;
            border-color: #533483;
            background: #1a1a2e;
        }
        .ai-improve-popup textarea::placeholder { color: #555; }
        .ai-improve-popup .popup-actions {
            display: flex;
            justify-content: flex-end;
            gap: 8px;
        }
        .ai-improve-popup .btn-revise {
            background: linear-gradient(135deg, #533483, #0f3460);
            border: none;
            border-radius: 6px;
            padding: 6px 18px;
            color: #fff;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .ai-improve-popup .btn-revise:hover { background: linear-gradient(135deg, #6c44a2, #1a4a7a); }
        .ai-improve-popup .btn-revise:disabled { opacity: 0.5; cursor: wait; }
        .ai-improve-popup .btn-popup-cancel {
            background: transparent;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 6px 12px;
            color: #888;
            font-size: 12px;
            cursor: pointer;
        }
        .ai-improve-popup .btn-popup-cancel:hover { color: #fff; border-color: #555; }
    `;
    document.head.appendChild(style);
}

// ---------------------------------------------------------------------------
// Inline Improve button — orchestrator
// ---------------------------------------------------------------------------

function setup_inline_improve_button(frm) {
    inject_improve_styles();

    // Tear down previous listeners before re-registering
    if (frm._improve_cleanup) frm._improve_cleanup();
    $(".ai-improve-btn, .ai-improve-popup").remove();

    const cleanups = [];

    // Rich Text (Quill)
    const content_field = frm.fields_dict.content;
    if (content_field && content_field.$wrapper) {
        const $ql = content_field.$wrapper.find(".ql-editor");
        if ($ql.length) cleanups.push(setup_quill_improve($ql[0], frm));
    }

    // Markdown (CodeMirror) — wait up to 1.5 s for CM to initialise, but only register once
    const md_field = frm.fields_dict.content_md;
    if (md_field && md_field.$wrapper) {
        let cm_registered = false;
        const try_register_cm = () => {
            if (cm_registered) return;
            const cm_el = md_field.$wrapper.find(".cm-editor")[0];
            if (cm_el && cm_el.cmView && cm_el.cmView.view) {
                cm_registered = true;
                cleanups.push(setup_codemirror_improve(cm_el.cmView.view, frm));
            }
        };
        try_register_cm();
        if (!cm_registered) setTimeout(try_register_cm, 1000);
    }

    frm._improve_cleanup = () => {
        cleanups.forEach(fn => fn && fn());
        $(".ai-improve-btn, .ai-improve-popup").remove();
    };
}

// ---------------------------------------------------------------------------
// Shared popup builder used by both Quill and CodeMirror
// ---------------------------------------------------------------------------

/**
 * Render the floating improvement popup anchored to `anchor_rect` inside
 * `$container`. Calls `on_submit(instruction)` when the user clicks Revise.
 * Returns a `hide` function.
 */
function create_improve_popup($container, anchor_rect, on_submit) {
    const container_rect = $container[0].getBoundingClientRect();

    const $popup = $(`
        <div class="ai-improve-popup">
            <div class="popup-header">
                <span>✨ ${__("Improve Selection")}</span>
                <span class="popup-close">&times;</span>
            </div>
            <textarea placeholder="${__("e.g. Make it more professional, shorten it, add more detail...")}"></textarea>
            <div class="popup-actions">
                <button class="btn-popup-cancel">${__("Cancel")}</button>
                <button class="btn-revise">${__("Revise")}</button>
            </div>
        </div>
    `);

    $popup.css({
        top: (anchor_rect.bottom - container_rect.top + 10) + "px",
        left: Math.max(0, anchor_rect.left - container_rect.left) + "px"
    });

    $container.css("position", "relative").append($popup);
    $popup.find("textarea").focus();

    const hide = () => $popup.remove();

    $popup.find(".popup-close, .btn-popup-cancel").on("click", hide);

    const handle_submit = () => {
        const instruction = $popup.find("textarea").val().trim();
        if (!instruction) {
            frappe.show_alert({ message: __("Please enter a revision instruction."), indicator: "orange" });
            return;
        }
        const $btn = $popup.find(".btn-revise");
        $btn.prop("disabled", true).text(__("Revising..."));

        on_submit(instruction, () => {
            // on success
            hide();
            frappe.show_alert({ message: __("Content revised and saved!"), indicator: "green" });
        }, () => {
            // on error
            $btn.prop("disabled", false).text(__("Revise"));
            frappe.show_alert({ message: __("Failed to revise. Check Error Log."), indicator: "red" });
        });
    };

    $popup.find(".btn-revise").on("click", handle_submit);
    $popup.find("textarea").on("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handle_submit(); }
    });

    return hide;
}

// ---------------------------------------------------------------------------
// Quill (Rich Text) handler
// ---------------------------------------------------------------------------

function setup_quill_improve(ql_editor, frm) {
    let hide_popup = null;
    let $btn = null;
    let saved = null;   // { text, quill_sel, range }

    const hide_all = () => {
        if ($btn) { $btn.remove(); $btn = null; }
        if (hide_popup) { hide_popup(); hide_popup = null; }
    };

    const on_mouseup = () => {
        setTimeout(() => {
            const quill = frm.fields_dict.content.quill;
            const quill_sel = quill ? quill.getSelection() : null;
            const win_sel = window.getSelection();
            const text = win_sel ? win_sel.toString().trim() : "";

            if (!text || !ql_editor.contains(win_sel.anchorNode)) {
                hide_all();
                return;
            }

            saved = { text, quill_sel, range: win_sel.getRangeAt(0).cloneRange() };

            const rect = saved.range.getBoundingClientRect();
            const $control = $(ql_editor).closest(".frappe-control");
            const control_rect = $control[0].getBoundingClientRect();

            hide_all();
            $btn = $(`<div class="ai-improve-btn">✨ ${__("Improve")}</div>`);
            $btn.css({
                top: (rect.bottom - control_rect.top + 6) + "px",
                left: (rect.left - control_rect.left) + "px"
            });
            $control.css("position", "relative").append($btn);

            $btn.on("click", e => {
                e.stopPropagation();
                if ($btn) { $btn.remove(); $btn = null; }

                hide_popup = create_improve_popup(
                    $control,
                    saved.range.getBoundingClientRect(),
                    (instruction, on_success, on_error) => {
                        frappe.call({
                            method: AI_METHOD_PREFIX + "revise_content_chunk",
                            args: {
                                doc_name: frm.doc.name,
                                content_chunk: saved.text,
                                instruction,
                                is_markdown: false
                            },
                            callback(r) {
                                const revised = r.message && r.message.revised_content;
                                if (!revised) { on_error(); return; }

                                const quill = frm.fields_dict.content.quill;
                                if (quill) {
                                    quill.focus();
                                    if (saved.quill_sel) {
                                        quill.deleteText(saved.quill_sel.index, saved.quill_sel.length);
                                        quill.clipboard.dangerouslyPasteHTML(saved.quill_sel.index, revised);
                                    } else {
                                        const idx = quill.getText().indexOf(saved.text);
                                        if (idx !== -1) {
                                            quill.deleteText(idx, saved.text.length);
                                            quill.clipboard.dangerouslyPasteHTML(idx, revised);
                                        } else {
                                            const escaped = saved.text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
                                            quill.root.innerHTML = quill.root.innerHTML
                                                .replace(new RegExp(escaped, "g"), revised);
                                        }
                                    }
                                    frm.set_value("content", quill.root.innerHTML);
                                    frm.save();
                                }
                                on_success();
                            },
                            error: on_error
                        });
                    }
                );
            });
        }, 10);
    };

    const on_doc_mousedown = e => {
        if (($btn && $btn[0].contains(e.target))) return;
        if ($(e.target).closest(".ai-improve-popup").length) return;
        hide_all();
    };

    ql_editor.addEventListener("mouseup", on_mouseup);
    document.addEventListener("mousedown", on_doc_mousedown);

    return () => {
        ql_editor.removeEventListener("mouseup", on_mouseup);
        document.removeEventListener("mousedown", on_doc_mousedown);
        hide_all();
    };
}

// ---------------------------------------------------------------------------
// CodeMirror (Markdown) handler
// ---------------------------------------------------------------------------

function setup_codemirror_improve(cm_view, frm) {
    let hide_popup = null;
    let $btn = null;
    let saved = null;   // { text, from, to }

    const hide_all = () => {
        if ($btn) { $btn.remove(); $btn = null; }
        if (hide_popup) { hide_popup(); hide_popup = null; }
    };

    const on_mouseup = () => {
        setTimeout(() => {
            const sel = cm_view.state.selection.main;
            if (sel.empty) { hide_all(); return; }

            const text = cm_view.state.doc.sliceString(sel.from, sel.to).trim();
            if (!text) { hide_all(); return; }

            saved = { text, from: sel.from, to: sel.to };
            const coords = cm_view.coordsAtPos(sel.to);
            if (!coords) return;

            const $control = $(cm_view.dom).closest(".frappe-control");
            const control_rect = $control[0].getBoundingClientRect();

            hide_all();
            $btn = $(`<div class="ai-improve-btn">✨ ${__("Improve")}</div>`);
            $btn.css({
                top: (coords.bottom - control_rect.top + 6) + "px",
                left: (coords.left - control_rect.left) + "px"
            });
            $control.css("position", "relative").append($btn);

            $btn.on("click", e => {
                e.stopPropagation();
                if ($btn) { $btn.remove(); $btn = null; }

                const anchor_rect = { bottom: coords.bottom, left: coords.left };
                hide_popup = create_improve_popup(
                    $control,
                    anchor_rect,
                    (instruction, on_success, on_error) => {
                        frappe.call({
                            method: AI_METHOD_PREFIX + "revise_content_chunk",
                            args: {
                                doc_name: frm.doc.name,
                                content_chunk: saved.text,
                                instruction,
                                is_markdown: true
                            },
                            callback(r) {
                                const revised = r.message && r.message.revised_content;
                                if (!revised) { on_error(); return; }

                                cm_view.dispatch({
                                    changes: { from: saved.from, to: saved.to, insert: revised }
                                });
                                frm.set_value("content_md", cm_view.state.doc.toString());
                                frm.save();
                                on_success();
                            },
                            error: on_error
                        });
                    }
                );
            });
        }, 10);
    };

    const on_doc_mousedown = e => {
        if ($btn && $btn[0].contains(e.target)) return;
        if ($(e.target).closest(".ai-improve-popup").length) return;
        hide_all();
    };

    cm_view.dom.addEventListener("mouseup", on_mouseup);
    document.addEventListener("mousedown", on_doc_mousedown);

    return () => {
        cm_view.dom.removeEventListener("mouseup", on_mouseup);
        document.removeEventListener("mousedown", on_doc_mousedown);
        hide_all();
    };
}

