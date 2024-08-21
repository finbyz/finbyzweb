(() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropSymbols = Object.getOwnPropertySymbols;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __propIsEnum = Object.prototype.propertyIsEnumerable;
  var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
  var __spreadValues = (a, b) => {
    for (var prop in b || (b = {}))
      if (__hasOwnProp.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    if (__getOwnPropSymbols)
      for (var prop of __getOwnPropSymbols(b)) {
        if (__propIsEnum.call(b, prop))
          __defNormalProp(a, prop, b[prop]);
      }
    return a;
  };

  // ../finbyzweb/finbyzweb/public/js/frappe/web_form/web_form_list.js
  frappe.provide("frappe.ui");
  frappe.provide("frappe.views");
  frappe.provide("frappe.web_form_list");
  var WebFormList = class {
    constructor(opts) {
      Object.assign(this, opts);
      frappe.web_form_list = this;
      this.wrapper = $(".web-list-table");
      this.make_actions();
      this.make_filters();
    }
    refresh() {
      this.rows = [];
      this.web_list_start = 0;
      this.page_length = 10;
      frappe.run_serially([
        () => this.get_list_view_fields(),
        () => this.get_data(),
        () => this.remove_more(),
        () => this.make_table(),
        () => this.create_more()
      ]);
    }
    remove_more() {
      $(".more").remove();
    }
    make_filters() {
      this.filters = {};
      this.filter_input = [];
      let filter_area = $(".web-list-filters");
      frappe.call("frappe.website.doctype.web_form.web_form.get_web_form_filters", {
        web_form_name: this.web_form_name
      }).then((response) => {
        let fields = response.message;
        fields.length && filter_area.removeClass("hide");
        fields.forEach((field) => {
          if (["Text Editor", "Text", "Small Text"].includes(field.fieldtype)) {
            field.fieldtype = "Data";
          }
          if (["Table", "Signature"].includes(field.fieldtype)) {
            return;
          }
          let input = frappe.ui.form.make_control({
            df: {
              fieldtype: field.fieldtype,
              fieldname: field.fieldname,
              options: field.options,
              input_class: "input-xs",
              only_select: true,
              label: __(field.label, null, field.parent),
              onchange: (event) => {
                this.add_filter(field.fieldname, input.value, field.fieldtype);
                this.refresh();
              }
            },
            parent: filter_area,
            render_input: 1,
            only_input: field.fieldtype == "Check" ? false : true
          });
          $(input.wrapper).addClass("col-md-2").attr("title", __(field.label, null, field.parent)).tooltip({
            delay: { show: 600, hide: 100 },
            trigger: "hover"
          });
          input.$input.attr("placeholder", __(field.label, null, field.parent));
          this.filter_input.push(input);
        });
        this.refresh();
      });
    }
    add_filter(field, value, fieldtype) {
      if (!value) {
        delete this.filters[field];
      } else {
        if (["Data", "Currency", "Float", "Int"].includes(fieldtype)) {
          value = ["like", "%" + value + "%"];
        }
        Object.assign(this.filters, Object.fromEntries([[field, value]]));
      }
    }
    get_list_view_fields() {
      if (this.columns)
        return this.columns;
      if (this.list_columns) {
        this.columns = this.list_columns.map((df) => {
          return {
            label: df.label,
            fieldname: df.fieldname,
            fieldtype: df.fieldtype
          };
        });
      }
    }
    fetch_data() {
      if (this.condition_json && JSON.parse(this.condition_json)) {
        let filter = frappe.utils.get_filter_from_json(this.condition_json, this.doctype);
        filter = frappe.utils.get_filter_as_json(filter);
        this.filters = Object.assign(this.filters, JSON.parse(filter));
      }
      let args = {
        method: "frappe.www.list.get_list_data",
        args: __spreadValues({
          doctype: this.doctype,
          limit_start: this.web_list_start,
          limit: this.page_length,
          web_form_name: this.web_form_name
        }, this.filters)
      };
      if (this.no_change(args)) {
        return Promise.resolve();
      }
      return frappe.call(args);
    }
    no_change(args) {
      if (this.last_args && JSON.stringify(args) === this.last_args) {
        return true;
      }
      this.last_args = JSON.stringify(args);
      setTimeout(() => {
        this.last_args = null;
      }, 3e3);
      return false;
    }
    async get_data() {
      let response = await this.fetch_data();
      if (response) {
        this.data = await response.message;
      }
    }
    more() {
      this.web_list_start += this.page_length;
      this.fetch_data().then((res) => {
        if (res.message.length === 0) {
          frappe.msgprint(__("No more items to display"));
        }
        this.append_rows(res.message);
      });
    }
    make_table() {
      this.table = $(`<table class="table"></table>`);
      this.make_table_head();
      this.make_table_body();
    }
    make_table_head() {
      let $thead = $(`
			<thead>
				<tr>
					<th>
						<input type="checkbox" class="select-all">
					</th>
					<th>${__("Name")}</th>
				</tr>
			</thead>
		`);
      this.check_all = $thead.find("input.select-all");
      this.check_all.on("click", (event) => {
        this.toggle_select_all(event.target.checked);
      });
      this.columns.forEach((col) => {
        let $tr = $thead.find("tr");
        let $th = $(`<th>${__(col.label)}</th>`);
        $th.appendTo($tr);
      });
      $thead.appendTo(this.table);
    }
    make_table_body() {
      if (this.data.length) {
        this.wrapper.empty();
        if (this.table) {
          this.table.find("tbody").remove();
          if (this.check_all.length) {
            this.check_all.prop("checked", false);
          }
        }
        this.append_rows(this.data);
        this.table.appendTo(this.wrapper);
      } else {
        if (this.wrapper.find(".no-result").length)
          return;
        this.wrapper.empty();
        frappe.has_permission(this.doctype, "", "create", () => {
          this.setup_empty_state();
        });
      }
    }
    setup_empty_state() {
      let new_button = `
			<a
				class="btn btn-primary btn-sm btn-new-doc hidden-xs"
				href="${location.pathname.replace("/list", "")}/new">
				${__("Create a new {0}", [__(this.doctype)])}
			</a>
		`;
      let empty_state = $(`
			<div class="no-result text-muted flex justify-center align-center">
				<div class="text-center">
					<div>
						<img
							src="/assets/frappe/images/ui-states/list-empty-state.svg"
							alt="Generic Empty State"
							class="null-state">
					</div>
					<p class="small mb-2">${__("No {0} found", [__(this.doctype)])}</p>
					${new_button}
				</div>
			</div>
		`);
      empty_state.appendTo(this.wrapper);
    }
    append_rows(row_data) {
      let $tbody = this.table.find("tbody");
      if (!$tbody.length) {
        $tbody = $(`<tbody></tbody>`);
        $tbody.appendTo(this.table);
      }
      row_data.forEach((data_item) => {
        let $row_element = $(`<tr id="${data_item.name}"></tr>`);
        let row = new frappe.ui.WebFormListRow({
          row: $row_element,
          doc: data_item,
          columns: this.columns,
          serial_number: data_item.name,
          events: {
            on_edit: () => this.open_form(data_item.name),
            on_select: () => {
              this.toggle_new();
              this.toggle_delete();
            }
          }
        });
        this.rows.push(row);
        $row_element.appendTo($tbody);
      });
    }
    make_actions() {
      const actions = $(".web-list-actions");
      frappe.has_permission(this.doctype, "", "delete", () => {
        this.add_button(
          actions,
          "delete-rows",
          "danger",
          true,
          "Delete",
          () => this.delete_rows()
        );
      });
    }
    add_button(wrapper, name, type, hidden, text, action) {
      if ($(`.${name}`).length)
        return;
      hidden = hidden ? "hide" : "";
      type = type == "danger" ? "danger button-delete" : type;
      let button = $(`
			<button class="${name} btn btn-${type} btn-sm ml-2 ${hidden}">${text}</button>
		`);
      button.on("click", () => action());
      button.appendTo(wrapper);
    }
    create_more() {
      if (this.rows.length >= this.page_length) {
        const footer = $(".web-list-footer");
        this.add_button(footer, "more", "secondary", false, "Load More", () => this.more());
      }
    }
    toggle_select_all(checked) {
      this.rows.forEach((row) => row.toggle_select(checked));
    }
    open_form(name) {
      let path = window.location.pathname;
      if (path.includes("/list")) {
        path = path.replace("/list", "");
      }
      window.location.href = path + "/" + name;
    }
    get_selected() {
      return this.rows.filter((row) => row.is_selected());
    }
    toggle_delete() {
      if (!this.settings.allow_delete)
        return;
      let btn = $(".delete-rows");
      !this.get_selected().length ? btn.addClass("hide") : btn.removeClass("hide");
    }
    toggle_new() {
      if (!this.settings.allow_delete)
        return;
      let btn = $(".button-new");
      this.get_selected().length ? btn.addClass("hide") : btn.removeClass("hide");
    }
    delete_rows() {
      if (!this.settings.allow_delete)
        return;
      frappe.call({
        type: "POST",
        method: "frappe.website.doctype.web_form.web_form.delete_multiple",
        args: {
          web_form_name: this.web_form_name,
          docnames: this.get_selected().map((row) => row.doc.name)
        }
      }).then(() => {
        this.refresh();
        this.toggle_delete();
        this.toggle_new();
      });
    }
  };
  frappe.ui.WebFormListRow = class WebFormListRow {
    constructor({ row, doc, columns, serial_number, events, options }) {
      Object.assign(this, { row, doc, columns, serial_number, events });
      this.make_row();
    }
    make_row() {
      let $cell = $(`<td class="list-col-checkbox"></td>`);
      this.checkbox = $(`<input type="checkbox">`);
      this.checkbox.on("click", (event) => {
        this.toggle_select(event.target.checked);
        event.stopImmediatePropagation();
      });
      this.checkbox.appendTo($cell);
      $cell.appendTo(this.row);
      let serialNo = $(`<td><p class="ellipsis">${__(this.serial_number)}</p></td>`);
      serialNo.appendTo(this.row);
      this.columns.forEach((field) => {
        let formatter = frappe.form.get_formatter(field.fieldtype);
        let value = this.doc[field.fieldname] && __(
          formatter(this.doc[field.fieldname], field, { only_value: 1 }, this.doc)
        ) || "";
        let cell = $(`<td><p class="ellipsis">${value}</p></td>`);
        if (field.fieldname === "status") {
          let pTag = cell.find("p");
          if (value.toLowerCase() === "open" && this.doc["priority"].toLowerCase() === "high") {
            pTag.addClass("badge badge-danger");
          } else if (value.toLowerCase() === "closed") {
            pTag.addClass("badge badge-success");
          } else if (value.toLowerCase() === "on hold") {
            pTag.addClass("badge badge-secondary");
          } else if (value.toLowerCase() === "open") {
            pTag.addClass("badge badge-warning");
          }
        }
        cell.appendTo(this.row);
        if (field.fieldtype === "Text Editor") {
          value = $(value).addClass("ellipsis");
          cell = $("<td></td>").append(value);
        }
        cell.appendTo(this.row);
      });
      this.row.on("click", () => this.events.on_edit());
    }
    toggle_select(checked) {
      this.checkbox.prop("checked", checked);
      this.events.on_select(checked);
    }
    is_selected() {
      return this.checkbox.prop("checked");
    }
  };

  // ../finbyzweb/finbyzweb/public/js/frappe/event_emitter.js
  frappe.provide("frappe.utils");
  var EventEmitterMixin = {
    init() {
      this.jq = jQuery({});
    },
    trigger(evt, data) {
      !this.jq && this.init();
      this.jq.trigger(evt, data);
    },
    once(evt, handler) {
      !this.jq && this.init();
      this.jq.one(evt, (e, data) => handler(data));
    },
    on(evt, handler) {
      !this.jq && this.init();
      this.jq.bind(evt, (e, data) => handler(data));
    },
    off(evt, handler) {
      !this.jq && this.init();
      this.jq.unbind(evt, (e, data) => handler(data));
    }
  };
  frappe.utils.make_event_emitter = function(object) {
    Object.assign(object, EventEmitterMixin);
    return object;
  };
  var event_emitter_default = EventEmitterMixin;

  // ../finbyzweb/finbyzweb/public/js/frappe/web_form/web_form.js
  frappe.provide("frappe.ui");
  frappe.provide("frappe.web_form");
  var WebForm = class extends frappe.ui.FieldGroup {
    constructor(opts) {
      super();
      Object.assign(this, opts);
      frappe.web_form = this;
      frappe.web_form.events = {};
      Object.assign(frappe.web_form.events, event_emitter_default);
      this.current_section = 0;
      this.is_multi_step_form = false;
    }
    prepare(web_form_doc, doc) {
      Object.assign(this, web_form_doc);
      this.fields = web_form_doc.web_form_fields;
      this.doc = doc;
    }
    make() {
      this.parent.empty();
      super.make();
      this.set_page_breaks();
      this.set_field_values();
      if (this.is_new || this.in_edit_mode) {
        this.setup_primary_action();
        this.setup_discard_action();
      }
      this.setup_previous_next_button();
      this.toggle_section();
      frappe.init_client_script && frappe.init_client_script();
      this.setup_listeners();
      frappe.web_form.events.trigger("after_load");
      this.after_load && this.after_load();
    }
    on(fieldname, handler) {
      let field = this.fields_dict[fieldname];
      field.df.change = () => {
        handler(field, field.value);
        this.refresh_dependency();
        this.make_form_dirty();
      };
    }
    setup_listeners() {
      this.fields.forEach((field) => {
        if (!field.change) {
          field.change = () => {
            this.refresh_dependency();
            this.make_form_dirty();
          };
        }
      });
    }
    make_form_dirty() {
      frappe.form_dirty = true;
      $(".indicator-pill.orange").removeClass("hide");
    }
    set_page_breaks() {
      this.page_breaks = $(".page-break");
      if (this.page_breaks.length) {
        this.page_breaks.each((i, page_break) => {
          if (!$(page_break).find("form").length) {
            $(page_break).remove();
          }
        });
      }
      this.page_breaks = $(".page-break");
      this.is_multi_step_form = !!this.page_breaks.length;
    }
    setup_previous_next_button() {
      let me = this;
      if (!me.is_multi_step_form) {
        return;
      }
      this.$next_button = $(`<button class="btn btn-default btn-next btn-sm ml-2">
			${__("Next")}
		</button>`);
      this.$previous_button = $(`<button class="btn btn-default btn-previous btn-sm">
			${__("Previous")}
		</button>`);
      this.$next_button.insertAfter(".web-form-footer .right-area .discard-btn");
      this.in_view_mode && $(".web-form-footer .right-area").append(this.$next_button);
      $(".web-form-footer .left-area").prepend(this.$previous_button);
      this.$previous_button.on("click", () => {
        let is_validated = me.validate_section();
        if (!is_validated)
          return false;
        for (let idx = me.current_section; idx < me.sections.length; idx--) {
          let is_empty = me.is_previous_section_empty(idx);
          me.current_section = me.current_section > 0 ? me.current_section - 1 : me.current_section;
          if (!is_empty) {
            break;
          }
        }
        me.toggle_section();
        return false;
      });
      this.$next_button.on("click", () => {
        let is_validated = me.validate_section();
        if (!is_validated)
          return false;
        for (let idx = me.current_section; idx < me.sections.length; idx++) {
          let is_empty = me.is_next_section_empty(idx);
          me.current_section = me.current_section < me.sections.length ? me.current_section + 1 : me.current_section;
          if (!is_empty) {
            break;
          }
        }
        me.toggle_section();
        return false;
      });
    }
    set_field_values() {
      if (this.doc.name)
        this.set_values(this.doc);
      else
        return;
    }
    set_default_values() {
      let defaults = {};
      for (let df of this.fields) {
        if (df.default) {
          defaults[df.fieldname] = df.default;
        }
      }
      let values = frappe.utils.get_query_params();
      delete values.new;
      Object.assign(defaults, values);
      this.set_values(values);
    }
    setup_primary_action() {
      $(".web-form").on("submit", () => this.save());
    }
    setup_discard_action() {
      $(".web-form-footer .discard-btn").on("click", () => this.discard_form());
    }
    discard_form() {
      let path = window.location.href;
      path = path.substring(0, path.lastIndexOf("/"));
      if (frappe.form_dirty) {
        frappe.warn(
          __("Discard?"),
          __("Are you sure you want to discard the changes?"),
          () => window.location.href = path,
          __("Discard")
        );
      } else {
        window.location.href = path;
      }
      return false;
    }
    validate_section() {
      if (this.allow_incomplete)
        return true;
      let fields = $(`${this.get_page(this.current_section)} .form-control`);
      let errors = [];
      let invalid_values = [];
      for (let field of fields) {
        let fieldname = $(field).attr("data-fieldname");
        if (!fieldname)
          continue;
        field = this.fields_dict[fieldname];
        if (field && field.get_value) {
          let value = field.get_value();
          if (field.df.reqd && is_null(typeof value === "string" ? strip_html(value) : value))
            errors.push(__(field.df.label));
          if (field.df.reqd && field.df.fieldtype === "Text Editor" && is_null(strip_html(cstr(value))))
            errors.push(__(field.df.label));
          if (field.df.invalid)
            invalid_values.push(__(field.df.label));
        }
      }
      let message = "";
      if (invalid_values.length) {
        message += __("Invalid values for fields:", null, "Error message in web form");
        message += "<br><br><ul><li>" + invalid_values.join("<li>") + "</ul>";
      }
      if (errors.length) {
        message += __("Mandatory fields required:", null, "Error message in web form");
        message += "<br><br><ul><li>" + errors.join("<li>") + "</ul>";
      }
      if (invalid_values.length || errors.length) {
        frappe.msgprint({
          title: __("Error", null, "Title of error message in web form"),
          message,
          indicator: "orange"
        });
      }
      return !(errors.length || invalid_values.length);
    }
    toggle_section() {
      if (!this.is_multi_step_form)
        return;
      this.render_progress_dots();
      this.toggle_previous_button();
      this.hide_form_pages();
      this.show_form_page();
      this.toggle_buttons();
    }
    render_progress_dots() {
      if (!this.is_multi_step_form)
        return;
      $(".center-area.paging").empty();
      if (this.in_view_mode) {
        let paging_text = __("Page {0} of {1}", [
          this.current_section + 1,
          this.page_breaks.length + 1
        ]);
        $(".center-area.paging").append(`<div>${paging_text}</div>`);
        return;
      }
      this.$slide_progress = $(`<div class="slides-progress"></div>`).appendTo(
        $(".center-area.paging")
      );
      this.$slide_progress.empty();
      if (this.page_breaks.length < 1)
        return;
      for (let i = 0; i <= this.page_breaks.length; i++) {
        let $dot = $(`<div class="slide-step">
				<div class="slide-step-indicator"></div>
				<div class="slide-step-complete">${frappe.utils.icon("tick", "xs")}</div>
			</div>`).attr({ "data-step-id": i });
        if (i < this.current_section) {
          $dot.addClass("step-success");
        }
        if (i === this.current_section) {
          $dot.addClass("active");
        }
        this.$slide_progress.append($dot);
      }
    }
    toggle_buttons() {
      for (let idx = this.current_section; idx <= this.page_breaks.length; idx++) {
        if (this.is_next_section_empty(idx)) {
          this.show_save_and_hide_next_button();
        } else {
          this.show_next_and_hide_save_button();
          break;
        }
      }
    }
    is_next_section_empty(section) {
      if (section + 1 > this.page_breaks.length + 1)
        return true;
      let _page = $(`${this.get_page(section + 1)}`);
      let visible_controls = _page.find(".frappe-control:not(.hide-control)");
      return !visible_controls.length ? true : false;
    }
    is_previous_section_empty(section) {
      if (section - 1 > this.page_breaks.length + 1)
        return true;
      let _page = $(`${this.get_page(section - 1)}`);
      let visible_controls = _page.find(".frappe-control:not(.hide-control)");
      return !visible_controls.length ? true : false;
    }
    show_save_and_hide_next_button() {
      $(".btn-next").hide();
      $(".submit-btn").show();
    }
    show_next_and_hide_save_button() {
      $(".btn-next").show();
      !this.allow_incomplete && $(".submit-btn").hide();
    }
    toggle_previous_button() {
      this.current_section == 0 ? $(".btn-previous").hide() : $(".btn-previous").show();
    }
    get_page(idx) {
      return idx > 0 ? `.page-break:eq(${idx - 1})` : `.form-page:eq(${idx})`;
    }
    show_form_page() {
      $(this.get_page(this.current_section)).show();
    }
    hide_form_pages() {
      for (let idx = 0; idx <= this.page_breaks.length; idx++) {
        if (idx !== this.current_section) {
          $(this.get_page(idx)).hide();
        }
      }
    }
    save() {
      let is_new = this.is_new;
      let valid = this.validate && this.validate();
      if (!valid && valid !== void 0) {
        frappe.msgprint(
          __("Couldn't save, please check the data you have entered"),
          __("Validation Error")
        );
        return false;
      }
      let doc_values = super.get_values(this.allow_incomplete);
      if (!doc_values)
        return false;
      if (window.saving)
        return false;
      let for_payment = Boolean(this.accept_payment && !this.doc.paid);
      Object.assign(this.doc, doc_values);
      this.doc.doctype = this.doc_type;
      this.doc.web_form_name = this.name;
      window.saving = true;
      frappe.form_dirty = false;
      frappe.call({
        type: "POST",
        method: "frappe.website.doctype.web_form.web_form.accept",
        args: {
          data: this.doc,
          web_form: this.name,
          for_payment
        },
        btn: $("btn-primary"),
        freeze: true,
        callback: (response) => {
          if (!response.exc) {
            this.handle_success(response.message);
            frappe.web_form.events.trigger("after_save");
            this.after_save && this.after_save();
            if (is_new && (response.message.attachment || response.message.file)) {
              frappe.call({
                type: "POST",
                method: "frappe.handler.upload_file",
                args: {
                  file_url: response.message.attachment || response.message.file,
                  doctype: response.message.doctype,
                  docname: response.message.name
                }
              });
            }
          }
        },
        always: function() {
          window.saving = false;
        }
      });
      return false;
    }
    handle_success(data) {
      if (this.accept_payment && !this.doc.paid) {
        window.location.href = data;
      }
      if (!this.is_new) {
        $(".success-title").text(__("Updated"));
        $(".success-message").text(__("Your form has been successfully updated"));
      }
      $(".web-form-container").hide();
      $(".success-page").removeClass("hide");
      if (this.success_url) {
        frappe.utils.setup_timer(5, 0, $(".time"));
        setTimeout(() => {
          window.location.href = this.success_url;
        }, 5e3);
      } else {
        this.render_success_page(data);
      }
    }
    render_success_page(data) {
      if (this.allow_edit && data.name) {
        $(".success-footer").append(`
				<a href="/${this.route}/${data.name}/edit" class="edit-button btn btn-default btn-md">
					${__("Edit your response", null, "Button in web form")}
				</a>
			`);
      }
      if (this.login_required && !this.allow_multiple && !this.show_list && data.name) {
        $(".success-footer").append(`
				<a href="/${this.route}/${data.name}" class="view-button btn btn-default btn-md">
					${__("View your response", null, "Button in web form")}
				</a>
			`);
      }
    }
  };

  // ../finbyzweb/finbyzweb/public/js/frappe/web_form/webform_script.js
  frappe.ready(function() {
    let web_form_doc = frappe.web_form_doc;
    let reference_doc = frappe.reference_doc;
    show_login_prompt();
    web_form_doc.is_list ? show_list() : show_form();
    function show_login_prompt() {
      if (frappe.session.user != "Guest" || !web_form_doc.login_required)
        return;
      const login_required = new frappe.ui.Dialog({
        title: __("Not Permitted"),
        primary_action_label: __("Login"),
        primary_action: () => {
          window.location.replace("/login?redirect-to=" + window.location.pathname);
        }
      });
      login_required.show();
      login_required.set_message(__("You are not permitted to access this page without login."));
    }
    function show_list() {
      new WebFormList({
        doctype: web_form_doc.doc_type,
        web_form_name: web_form_doc.name,
        list_columns: web_form_doc.list_columns,
        condition_json: web_form_doc.condition_json,
        settings: {
          allow_delete: web_form_doc.allow_delete
        }
      });
    }
    function show_form() {
      let web_form = new WebForm({
        parent: $(".web-form-wrapper")
      });
      let doc = reference_doc || {};
      setup_fields(web_form_doc, doc);
      web_form.prepare(web_form_doc, doc);
      web_form.make();
      if (web_form_doc.is_new) {
        web_form.set_default_values();
      }
      $(".file-size").each(function() {
        $(this).text(frappe.form.formatters.FileSize($(this).text()));
      });
    }
    function setup_fields(web_form_doc2, doc_data) {
      web_form_doc2.web_form_fields.forEach((df) => {
        df.is_web_form = true;
        df.read_only = df.read_only || !web_form_doc2.is_new && !web_form_doc2.in_edit_mode;
        if (df.fieldtype === "Table") {
          df.get_data = () => {
            let data = [];
            if (doc_data && doc_data[df.fieldname]) {
              return doc_data[df.fieldname];
            }
            return data;
          };
          $.each(df.fields || [], function(_i, field) {
            if (field.fieldtype === "Link") {
              field.only_select = true;
            }
            field.is_web_form = true;
          });
          if (df.fieldtype === "Attach") {
            df.is_private = true;
          }
          delete df.parent;
          delete df.parentfield;
          delete df.parenttype;
          delete df.doctype;
          return df;
        }
        if (df.fieldtype === "Link") {
          df.only_select = true;
        }
        if (["Attach", "Attach Image"].includes(df.fieldtype)) {
          if (typeof df.options !== "object") {
            df.options = {};
          }
          df.options.disable_file_browser = true;
        }
      });
    }
  });
})();
//# sourceMappingURL=custom_web_form.bundle.5R552RGW.js.map
