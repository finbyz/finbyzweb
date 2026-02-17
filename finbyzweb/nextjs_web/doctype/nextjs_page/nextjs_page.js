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

        // ─── Inline "Improve" Button for Text Selection ───
        setup_inline_improve_button(frm);

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

// ─── Inline Improve Button ─────────────────────────────────────────
// Injects CSS + floating button logic for text selection revision
// Works with both Quill (Rich Text) and CodeMirror (Markdown)

(function () {
    // Inject styles once
    if (!document.getElementById('ai-improve-btn-styles')) {
        const style = document.createElement('style');
        style.id = 'ai-improve-btn-styles';
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
            .ai-improve-popup .btn-revise:hover {
                background: linear-gradient(135deg, #6c44a2, #1a4a7a);
            }
            .ai-improve-popup .btn-revise:disabled {
                opacity: 0.5;
                cursor: wait;
            }
            .ai-improve-popup .btn-popup-cancel {
                background: transparent;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 6px 12px;
                color: #888;
                font-size: 12px;
                cursor: pointer;
            }
            .ai-improve-popup .btn-popup-cancel:hover {
                color: #fff;
                border-color: #555;
            }
        `;
        document.head.appendChild(style);
    }
})();

function setup_inline_improve_button(frm) {
    // Clean up previous listeners
    if (frm._improve_cleanup) {
        frm._improve_cleanup();
    }

    // Remove any leftover DOM elements
    $('.ai-improve-btn, .ai-improve-popup').remove();

    const handlers = [];

    // ── Rich Text (Quill) ──
    const content_field = frm.fields_dict.content;
    if (content_field && content_field.$wrapper) {
        const $ql = content_field.$wrapper.find('.ql-editor');
        if ($ql.length) {
            const handler = setup_quill_improve($ql[0], frm);
            if (handler) handlers.push(handler);
        }
    }

    // ── Markdown (CodeMirror) ──
    const md_field = frm.fields_dict.content_md;
    if (md_field && md_field.$wrapper) {
        // CodeMirror may take time to init, so we retry
        const try_md = () => {
            const cm_el = md_field.$wrapper.find('.cm-editor')[0];
            if (cm_el && cm_el.cmView && cm_el.cmView.view) {
                const handler = setup_codemirror_improve(cm_el.cmView.view, frm);
                if (handler) handlers.push(handler);
            }
        };
        try_md();
        // Retry after a short delay in case CodeMirror loads late
        setTimeout(try_md, 1000);
    }

    frm._improve_cleanup = () => {
        handlers.forEach(h => h());
        $('.ai-improve-btn, .ai-improve-popup').remove();
    };
}

function setup_quill_improve(ql_editor, frm) {
    let $btn = null;
    let $popup = null;
    let saved_selection = null;

    const on_mouseup = () => {
        setTimeout(() => {
            const quill = frm.fields_dict.content.quill;
            const sel = quill ? quill.getSelection() : null;

            const win_sel = window.getSelection();
            const text = win_sel ? win_sel.toString().trim() : '';

            console.log("[AI Improve Quill] Selection detected", { hasText: !!text, length: text.length, quillSel: sel });

            if (!text || !ql_editor.contains(win_sel.anchorNode)) {
                hide_all();
                return;
            }

            saved_selection = {
                text: text,
                range: win_sel.getRangeAt(0).cloneRange(),
                quill_sel: sel
            };

            console.log("[AI Improve Quill] Selection saved:", saved_selection.text.substring(0, 50) + "...");
            show_improve_btn(win_sel.getRangeAt(0), ql_editor);
        }, 10);
    };

    const hide_all = () => {
        if ($btn) { $btn.remove(); $btn = null; }
        if ($popup) { $popup.remove(); $popup = null; }
    };

    const show_improve_btn = (range, container) => {
        hide_all();
        const rect = range.getBoundingClientRect();
        const container_rect = container.closest('.frappe-control').getBoundingClientRect();

        $btn = $(`<div class="ai-improve-btn">✨ ${__('Improve')}</div>`);
        $btn.css({
            top: (rect.bottom - container_rect.top + 6) + 'px',
            left: (rect.left - container_rect.left) + 'px'
        });

        $(container).closest('.frappe-control').css('position', 'relative').append($btn);
        console.log("[AI Improve Quill] Button displayed");

        $btn.on('click', (e) => {
            console.log("[AI Improve Quill] ✨ Button CLICKED");
            e.stopPropagation();
            show_improve_popup(container);
        });
    };

    const show_improve_popup = (container) => {
        console.log("[AI Improve Quill] Creating popup");
        if ($btn) { $btn.remove(); $btn = null; }
        if ($popup) { $popup.remove(); $popup = null; }

        const $container = $(container).closest('.frappe-control');

        $popup = $(`
            <div class="ai-improve-popup">
                <div class="popup-header">
                    <span>✨ Improve Selection</span>
                    <span class="popup-close">&times;</span>
                </div>
                <textarea placeholder="${__('e.g. Make it more professional, shorten it, add more detail...')}" required></textarea>
                <div class="popup-actions">
                    <button class="btn-popup-cancel">${__('Cancel')}</button>
                    <button class="btn-revise">${__('Revise')}</button>
                </div>
            </div>
        `);

        if (saved_selection && saved_selection.range) {
            const rect = saved_selection.range.getBoundingClientRect();
            const container_rect = $container[0].getBoundingClientRect();
            $popup.css({
                top: (rect.bottom - container_rect.top + 10) + 'px',
                left: Math.max(0, (rect.left - container_rect.left)) + 'px'
            });
        }

        $container.css('position', 'relative').append($popup);
        $popup.find('textarea').focus();
        console.log("[AI Improve Quill] Popup displayed & focused");

        $popup.find('.popup-close, .btn-popup-cancel').on('click', () => {
            console.log("[AI Improve Quill] Cancel clicked");
            hide_all();
        });

        $popup.find('.btn-revise').on('click', function () {
            const instruction = $popup.find('textarea').val().trim();
            console.log("[AI Improve Quill] Revise clicked", { instruction, length: instruction.length });

            if (!instruction) {
                console.warn("[AI Improve Quill] No instruction provided");
                frappe.show_alert({ message: __('Please enter a revision instruction.'), indicator: 'orange' });
                return;
            }

            const $revise_btn = $(this);
            $revise_btn.prop('disabled', true).text(__('Revising...'));

            console.log("[AI Improve Quill] === API CALL START ===");
            console.log("[AI Improve Quill] Input:", {
                doc_name: frm.doc.name,
                content_chunk: saved_selection.text,
                instruction: instruction
            });

            frappe.call({
                method: 'finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.revise_content_chunk',
                args: {
                    doc_name: frm.doc.name,
                    content_chunk: saved_selection.text,
                    instruction: instruction,
                    is_markdown: false
                },
                callback: function (r) {
                    console.log("[AI Improve Quill] === API SUCCESS ===");
                    console.log("[AI Improve Quill] Response:", r);

                    if (r.message && r.message.revised_content) {
                        console.log("[AI Improve Quill] Revised content:", r.message.revised_content.substring(0, 100));

                        const quill = frm.fields_dict.content.quill;
                        if (quill) {
                            quill.focus();
                            if (saved_selection.quill_sel) {
                                // Direct character-based replacement (highly accurate)
                                quill.deleteText(saved_selection.quill_sel.index, saved_selection.quill_sel.length);
                                quill.clipboard.dangerouslyPasteHTML(saved_selection.quill_sel.index, r.message.revised_content);
                                console.log("[AI Improve Quill] Content replaced via Quill selection");
                            } else {
                                // Fallback: searching in full text
                                const content = quill.getText();
                                const idx = content.indexOf(saved_selection.text);
                                if (idx !== -1) {
                                    quill.deleteText(idx, saved_selection.text.length);
                                    quill.clipboard.dangerouslyPasteHTML(idx, r.message.revised_content);
                                    console.log("[AI Improve Quill] Content replaced via searched text index");
                                } else {
                                    // Extreme fallback: replace current HTML root
                                    const editor_html = quill.root.innerHTML;
                                    const escaped = saved_selection.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                                    const new_html = editor_html.replace(new RegExp(escaped, 'g'), r.message.revised_content);
                                    quill.root.innerHTML = new_html;
                                    console.log("[AI Improve Quill] Content replaced via HTML string substitution");
                                }
                            }

                            // Sync to field and save
                            frm.set_value('content', quill.root.innerHTML);
                            frm.save();
                        }
                    }
                    frappe.show_alert({ message: __('Content revised and saved!'), indicator: 'green' });
                    hide_all();
                },
                error: function (r) {
                    console.error("[AI Improve Quill] === API ERROR ===");
                    console.error("[AI Improve Quill] Error:", r);
                    $revise_btn.prop('disabled', false).text(__('Revise'));
                    frappe.show_alert({ message: __('Failed to revise. Check console.'), indicator: 'red' });
                }
            });
        });

        $popup.find('textarea').on('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                console.log("[AI Improve Quill] Enter key pressed");
                $popup.find('.btn-revise').click();
            }
        });
    };

    ql_editor.addEventListener('mouseup', on_mouseup);

    const doc_click = (e) => {
        if ($btn && !$btn[0].contains(e.target) &&
            $popup && !$popup[0].contains(e.target)) {
            hide_all();
        } else if ($btn && !$btn[0].contains(e.target) && !$popup) {
            hide_all();
        }
    };
    document.addEventListener('mousedown', doc_click);

    return () => {
        ql_editor.removeEventListener('mouseup', on_mouseup);
        document.removeEventListener('mousedown', doc_click);
        hide_all();
    };
}

function setup_codemirror_improve(cm_view, frm) {
    let $btn = null;
    let saved_text = '';
    let saved_range = null;

    const on_mouseup = () => {
        setTimeout(() => {
            const state = cm_view.state;
            const sel = state.selection.main;
            if (sel.empty) {
                hide_btn();
                return;
            }

            saved_text = state.doc.sliceString(sel.from, sel.to).trim();
            if (!saved_text) {
                hide_btn();
                return;
            }

            saved_range = { from: sel.from, to: sel.to };

            // Get position for the button
            const coords = cm_view.coordsAtPos(sel.to);
            if (!coords) return;

            const $container = $(cm_view.dom).closest('.frappe-control');
            const container_rect = $container[0].getBoundingClientRect();

            hide_btn();

            $btn = $(`<div class="ai-improve-btn">✨ ${__('Improve')}</div>`);
            $btn.css({
                top: (coords.bottom - container_rect.top + 6) + 'px',
                left: (coords.left - container_rect.left) + 'px'
            });

            $container.css('position', 'relative').append($btn);

            $btn.on('click', (e) => {
                console.log("AI Improve (CM): Trigger button clicked");
                e.stopPropagation();
                hide_btn();

                frappe.prompt([
                    {
                        label: __('How should I improve this?'),
                        fieldname: 'instruction',
                        fieldtype: 'Small Text',
                        reqd: 1,
                        placeholder: __('e.g. Make it more professional, shorten it, add more detail...')
                    }
                ], (values) => {
                    const $dialog = cur_dialog;
                    $dialog.get_primary_btn().prop('disabled', true).text(__('Revising...'));

                    frappe.call({
                        method: 'finbyzweb.nextjs_web.doctype.nextjs_page.nextjs_page.revise_content_chunk',
                        args: {
                            doc_name: frm.doc.name,
                            content_chunk: saved_text,
                            instruction: values.instruction,
                            is_markdown: true
                        },
                        callback: function (r) {
                            $dialog.hide();
                            if (r.message && r.message.revised_content) {
                                // Precision replacement using original range
                                cm_view.dispatch({
                                    changes: {
                                        from: saved_range.from,
                                        to: saved_range.to,
                                        insert: r.message.revised_content
                                    }
                                });
                                // Sync to field and save
                                frm.set_value('content_md', cm_view.state.doc.toString());
                                frm.save();
                                frappe.show_alert({ message: __('Content revised and saved!'), indicator: 'green' });
                            }
                        },
                        error: function (r) {
                            $dialog.get_primary_btn().prop('disabled', false).text(__('Revise'));
                        }
                    }, __('Improve Selection'), __('Revise'));
                });
            });
        }, 10);
    };

    const hide_btn = () => {
        if ($btn) { $btn.remove(); $btn = null; }
    };

    cm_view.dom.addEventListener('mouseup', on_mouseup);

    const doc_click = (e) => {
        if ($btn && !$btn[0].contains(e.target)) {
            hide_btn();
        }
    };
    document.addEventListener('mousedown', doc_click);

    return () => {
        cm_view.dom.removeEventListener('mouseup', on_mouseup);
        document.removeEventListener('mousedown', doc_click);
        hide_btn();
    };
}
