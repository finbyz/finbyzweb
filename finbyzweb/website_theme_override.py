from os.path import abspath
from os.path import exists as path_exists
from os.path import join as join_path
from os.path import splitext
from typing import Optional

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_path
from frappe.website.doctype.website_theme.website_theme import WebsiteTheme, get_scss

class CustomWebsiteTheme(WebsiteTheme):
	def generate_bootstrap_theme(self):
		from subprocess import PIPE, Popen

		self.theme_scss = frappe.render_template(
			"frappe/website/doctype/website_theme/website_theme_template.scss", self.as_dict()
		)

		# create theme file in site public files folder
		folder_path = abspath(frappe.utils.get_files_path("website_theme", is_private=False))
		# create folder if not exist
		frappe.create_folder(folder_path)

		if self.custom:
			self.delete_old_theme_files(folder_path)


		#FinByz Changes to remove suffix
		# add a random suffix
		# suffix = frappe.generate_hash(length=8) if self.custom else "style"

		file_name = frappe.scrub(self.name) + ".css"
		output_path = join_path(folder_path, file_name)

		self.theme_scss = content = get_scss(self)
		content = content.replace("\n", "\\n")
		command = ["/home/finbyz/.nvm/versions/node/v14.21.2/bin/node", "generate_bootstrap_theme.js", output_path, content]

		process = Popen(command, cwd=frappe.get_app_path("frappe", ".."), stdout=PIPE, stderr=PIPE)

		stderr = process.communicate()[1]

		if stderr:
			stderr = frappe.safe_decode(stderr)
			stderr = stderr.replace("\n", "<br>")
			frappe.throw(f'<div style="font-family: monospace;">{stderr}</div>')
		else:
			self.theme_url = "/files/website_theme/" + file_name

		frappe.msgprint(_("Compiled Successfully"), alert=True)


