import WebFormList from './web_form_list.js';

export default class FinByzWebFormList extends WebFormList {
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
}

frappe.ui.WebFormListRow = class FinByzWebFormListRow extends WebFormListRow {
	constructor({ row, doc, columns, serial_number, events, options }) {
		Object.assign(this, { row, doc, columns, serial_number, events });
		this.make_row();
	}

	make_row() {
		// console.log(this.doc);
		// Add Checkboxes
		let $cell = $(`<td class="list-col-checkbox"></td>`);

		this.checkbox = $(`<input type="checkbox">`);
		this.checkbox.on("click", (event) => {
			this.toggle_select(event.target.checked);
			event.stopImmediatePropagation();
		});
		this.checkbox.appendTo($cell);
		$cell.appendTo(this.row);

		// Add Serial Number
		let serialNo = $(`<td><p class="ellipsis">${__(this.serial_number)}</p></td>`);
		serialNo.appendTo(this.row);

		this.columns.forEach((field) => {
			let formatter = frappe.form.get_formatter(field.fieldtype);
			let value =
				(this.doc[field.fieldname] &&
					__(
						formatter(this.doc[field.fieldname], field, { only_value: 1 }, this.doc)
					)) ||
				"";
			let cell = $(`<td><p class="ellipsis">${value}</p></td>`);

			// Color coding for status field
			

			if (field.fieldtype === "Text Editor") {
				value = $(value).addClass("ellipsis");
				cell = $("<td></td>").append(value);
			}
			cell.appendTo(this.row);
			if (field.fieldname === "status") {
				
				if (value.toLowerCase() === "open") {
					cell.css("color", "green");
				} else if (value.toLowerCase() === "close") {
					cell.css("color", "red");
				} else if (value.toLowerCase() === "hold") {
					cell.css("color", "orange");
				}
			}
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
