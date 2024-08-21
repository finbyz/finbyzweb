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