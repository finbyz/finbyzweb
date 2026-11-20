from __future__ import unicode_literals

import frappe
import requests
import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit


TURNSTILE_SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_TIMEOUT_SECONDS = 5

def customer_before_save(self, method):
	doc = frappe.get_single("Customer Details")
	doc.ignore_permissions = True

	if self.show_on_website:
		if not frappe.db.exists("Customer Details List", {'customer': self.customer_name}):
			doc.append('customer_details_list', {
					'customer': self.customer_name,
					'image': self.image
				})
			doc.save()

	else:
		if frappe.db.exists("Customer Details List", {'customer': self.customer_name}):
			to_remove = [row for row in doc.get('customer_details_list') if row.customer == self.customer_name]
			[doc.remove(row) for row in to_remove]
			doc.save()

	frappe.db.commit()

@frappe.whitelist(allow_guest=True, methods=["POST"])
def set_form_contact_data(
	lead_name: str = "",
	company_name: str = "",
	mobile_no: str = "",
	title: str = "",
	email: str = "",
	notes: str = "",
):
	_require_contact(email, mobile_no)
	# A failed security check never loses an inquiry: the Lead is saved and marked (see _inquiry_check)
	notes = _inquiry_check(notes)

	# Lead.notes is a CRM Note table in v16; the visitor's text goes into Lead.message
	_save_website_lead(
		lead_name=lead_name,
		company_name=company_name,
		mobile_no=mobile_no,
		email=email,
		source_web_page=title,
		message=notes,
	)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def set_form_data(
	lead_name: str = "",
	company_name: str = "",
	mobile_no: str = "",
	title: str = "",
	email: str = "",
	message: str = "",
	utm_source: str = "",
	utm_medium: str = "",
	utm_campaign: str = "",
	utm_term: str = "",
	utm_content: str = "",
	attribution: str = "",
	ga_client_id: str = "",
):
	_require_contact(email, mobile_no)
	message = _inquiry_check(message)

	query_params = parse_qs(urlsplit(title or "").query)
	utm = {
		fieldname: (value or "").strip() or query_params.get(fieldname, [""])[0].strip()
		for fieldname, value in {
			"utm_source": utm_source,
			"utm_medium": utm_medium,
			"utm_campaign": utm_campaign,
			"utm_term": utm_term,
			"utm_content": utm_content,
		}.items()
	}
	_save_website_lead(
		lead_name=lead_name,
		company_name=company_name,
		mobile_no=mobile_no,
		email=email,
		source_web_page=title,
		message=message,
		utm=utm,
		journey=_parse_attribution(attribution, ga_client_id),
	)


# Lead "Website Journey" fields (custom fields, module Finbyzweb) filled from the website's
# attribution payload (finbyzwebsite src/lib/attribution.ts). Everything is optional: old cached
# pages, the chatbot and other forms simply leave them empty.
_JOURNEY_MAX_BYTES = 20000
_JOURNEY_MAX_PAGES = 25


def _clean_text(value, limit=140):
	if value is None or isinstance(value, (dict, list)):
		return ""
	text = frappe.utils.strip_html_tags(str(value)).replace("\n", " ").replace("\r", " ").strip()
	return text[:limit]


def _clean_int(value, upper=100000):
	try:
		number = int(value)
	except (TypeError, ValueError):
		return None
	return number if 0 <= number <= upper else None


def _epoch_to_site_datetime(value, millis=False):
	try:
		seconds = float(value) / (1000 if millis else 1)
	except (TypeError, ValueError):
		return None
	# accept 2020-01-01 .. now + 1 day (browser clocks drift)
	if not (1577836800 <= seconds <= datetime.now().timestamp() + 86400):
		return None
	return frappe.utils.convert_utc_to_system_timezone(datetime.fromtimestamp(seconds, tz=timezone.utc)).replace(tzinfo=None)


def _parse_attribution(raw, ga_client_id=""):
	"""Map the website attribution JSON to Lead field values. Never raises: a bad payload must not
	lose the inquiry."""
	values = {}
	try:
		if ga_client_id:
			values["ga_client_id"] = _clean_text(ga_client_id, 60)
		if not raw or len(raw) > _JOURNEY_MAX_BYTES:
			return values
		data = json.loads(raw)
		if not isinstance(data, dict):
			return values
		values["tracking_consent"] = _clean_text(data.get("consent"), 20)

		first = data.get("first") if isinstance(data.get("first"), dict) else {}
		last = data.get("last") if isinstance(data.get("last"), dict) else {}
		for prefix, touch in (("first", first), ("last", last)):
			if not touch:
				continue
			values[f"{prefix}_channel"] = _clean_text(touch.get("channel"), 80)
			values[f"{prefix}_source"] = _clean_text(touch.get("source"), 80)
			landing = _clean_text(touch.get("landing"))
			values[f"{prefix}_landing_page"] = landing if landing.startswith("/") else ""
		if first:
			values["first_referrer"] = _clean_text(first.get("referrer"))
			first_on = _epoch_to_site_datetime(first.get("at"), millis=True)
			if first_on:
				values["first_visit_on"] = first_on
				submitted = _epoch_to_site_datetime(data.get("submitted_at"), millis=True) or frappe.utils.now_datetime()
				values["days_to_convert"] = max(0, (submitted - first_on).days)

		visits = _clean_int(data.get("visits"))
		pages = _clean_int(data.get("pages"))
		if visits is not None:
			values["visits_before_lead"] = visits
		if pages is not None:
			values["pages_viewed"] = pages

		lines = []
		journey = data.get("journey") if isinstance(data.get("journey"), list) else []
		for step in journey[-_JOURNEY_MAX_PAGES:]:
			if not isinstance(step, dict):
				continue
			path = _clean_text(step.get("p"), 200)
			if not path.startswith("/"):
				continue
			when = _epoch_to_site_datetime(step.get("t"))
			lines.append(f"{when.strftime('%Y-%m-%d %H:%M') if when else '?'}  {path}")
		if lines:
			values["website_journey"] = "\n".join(lines)
	except ValueError:
		pass  # malformed JSON from a client: ignore, the inquiry still saves
	except Exception:
		frappe.log_error(title="Website lead attribution not parsed", message=frappe.get_traceback())
	return {k: v for k, v in values.items() if v not in (None, "")}


def _journey_summary(journey):
	if not journey or not journey.get("first_channel"):
		return ""
	text = f"Came from: {journey.get('first_channel')} - {journey.get('first_source', '')}"
	if journey.get("first_landing_page"):
		text += f", landed on {journey['first_landing_page']}"
	if journey.get("first_visit_on"):
		text += f" ({frappe.utils.format_datetime(journey['first_visit_on'], 'dd MMM yyyy')})"
	if journey.get("last_source") and journey.get("last_source") != journey.get("first_source"):
		text += f"; latest: {journey.get('last_channel')} - {journey['last_source']}"
	if journey.get("visits_before_lead") or journey.get("pages_viewed"):
		text += f"; {journey.get('visits_before_lead', 0)} visits, {journey.get('pages_viewed', 0)} pages"
	return text


def _save_website_lead(lead_name, company_name, mobile_no, email, source_web_page, message, utm=None, journey=None):
	"""Create a Lead from a website form.

	v16 dropped Lead.source, so website leads are marked with utm_source "Website" unless the
	visitor came with their own UTM source. A visitor who is already a Lead (email must be unique)
	would get a DuplicateEntryError and lose the inquiry; their inquiry is added to the existing
	Lead's timeline instead.
	"""
	utm = dict(utm or {})
	utm["utm_source"] = utm.get("utm_source") or "Website"

	email = (email or "").strip()
	lead_name = (lead_name or "").strip()[:140]
	company_name = (company_name or "").strip()[:140]
	if not (email or (mobile_no or "").strip()):
		frappe.throw("Please enter your email or phone number.")
	existing = email and frappe.db.get_value("Lead", {"email_id": email}, "name")
	if existing and not frappe.db.get_single_value("CRM Settings", "allow_lead_duplication_based_on_emails"):
		lines = [
			"<b>New website inquiry</b>",
			f"Name: {frappe.utils.escape_html(lead_name or '')}",
			f"Organization: {frappe.utils.escape_html(company_name or '')}",
			f"Mobile: {frappe.utils.escape_html(mobile_no or '')}",
			f"Page: {frappe.utils.escape_html(source_web_page or '')}",
		]
		if utm.get("utm_source") != "Website" or any(utm.get(k) for k in ("utm_medium", "utm_campaign")):
			lines.append("UTM: " + frappe.utils.escape_html(", ".join(f"{k}={v}" for k, v in utm.items() if v)))
		summary = _journey_summary(journey)
		if summary:
			lines.append(frappe.utils.escape_html(summary))
		if journey and journey.get("website_journey"):
			lines.append("Pages: " + frappe.utils.escape_html(journey["website_journey"]).replace("\n", "<br>"))
		if message:
			lines.append("Message: " + frappe.utils.escape_html(message))
		lead = frappe.get_doc("Lead", existing)
		lead.add_comment("Comment", "<br>".join(lines), comment_email=email, comment_by=lead_name)
		frappe.db.commit()
		return

	def build(keep_mobile=True, keep_email=True):
		data = frappe.new_doc("Lead")
		data.lead_name = lead_name
		# Lead requires Organization; the quick forms send none for Gmail/Yahoo addresses
		data.company_name = company_name or NO_COMPANY
		data.mobile_no = mobile_no if keep_mobile else None
		data.email_id = email if keep_email else None
		data.source_web_page = source_web_page
		data.message = message
		dropped = [f"Mobile: {mobile_no}" for _ in [1] if not keep_mobile and mobile_no]
		dropped += [f"Email: {email}" for _ in [1] if not keep_email and email]
		if dropped:
			data.message = "\n\n".join(filter(None, [message, "As typed, not valid, check by hand: " + ", ".join(dropped)]))
		_split_unknown_utm(data, utm)
		for fieldname, value in utm.items():
			data.set(fieldname, value)
		for fieldname, value in (journey or {}).items():
			if data.meta.has_field(fieldname):
				data.set(fieldname, value)
		return data

	# An inquiry must never be refused for a badly typed phone or email: save it with those two
	# fields kept in the message instead, so sales can still read and call/write.
	email_ok = not email or bool(frappe.utils.validate_email_address(email))
	attempts = [(True, True), (True, False), (False, True), (False, False)]
	attempts = [a for a in attempts if email_ok or not a[1]]  # a bad email is never retried
	for i, (keep_mobile, keep_email) in enumerate(attempts):
		frappe.db.savepoint("website_lead")
		try:
			build(keep_mobile, keep_email).save(ignore_permissions=True)
			break
		except frappe.ValidationError:
			frappe.db.rollback(save_point="website_lead")
			frappe.clear_messages()
			if i == len(attempts) - 1:
				frappe.log_error(
					"Website inquiry not saved",
					frappe.as_json({"lead_name": lead_name, "company_name": company_name, "mobile_no": mobile_no,
						"email": email, "page": source_web_page, "message": message}) + "\n\n" + frappe.get_traceback(),
				)
				frappe.db.commit()
				raise
	frappe.db.commit()


UTM_LINK_DOCTYPES = {"utm_source": "UTM Source", "utm_medium": "UTM Medium", "utm_campaign": "UTM Campaign"}
UTM_OTHER_FIELD = "utm_other"


def _split_unknown_utm(lead, utm):
	"""Keep only known UTM values in the Lead's Link fields; put the rest in Other UTM Values.

	Lead.utm_source / utm_medium / utm_campaign link to UTM Source / Medium / Campaign records, so
	an unknown value would fail link validation and lose the inquiry. Rather than creating a
	record for every new referrer or campaign, an unknown value leaves the Link empty and is kept
	as text ("utm_source: example.com"). Add a UTM record by hand when a source is worth reporting
	on; later leads with that value then use the Link.
	"""
	other = []
	for fieldname, doctype in UTM_LINK_DOCTYPES.items():
		value = (utm.get(fieldname) or "").strip()
		utm[fieldname] = None
		if not value:
			continue
		df = lead.meta.get_field(fieldname)
		if df and df.fieldtype != "Link":
			utm[fieldname] = value
		elif len(value) <= 140 and frappe.db.exists(doctype, value):
			utm[fieldname] = frappe.db.get_value(doctype, value, "name")
		else:
			other.append(f"{fieldname}: {value}")
	if other:
		text = "\n".join(other)
		if lead.meta.has_field(UTM_OTHER_FIELD):
			lead.set(UTM_OTHER_FIELD, text)
		else:
			lead.message = "\n\n".join(filter(None, [lead.message, "UTM: " + text]))


NO_COMPANY = "Not given"
# Most unverified inquiries per hour, site-wide (website traffic reaches the ERP through one proxy IP,
# so a per-IP limit is not possible). Above it, posts are refused and logged. site_config can change it.
UNVERIFIED_LEADS_PER_HOUR = 20


def _turnstile_result(token: str | None) -> str:
	"""Return "" when the Cloudflare check passed, else a short reason. Never raises."""
	if not token:
		return "no token (" + _clean_text(frappe.form_dict.get("turnstile_fallback") or "not sent", 40) + ")"
	secret = frappe.conf.get("turnstile_secret_key")
	if not secret:
		return "secret key not configured"
	payload = {"secret": secret, "response": token}
	if remote_ip := getattr(frappe.local, "request_ip", None):
		payload["remoteip"] = remote_ip
	try:
		response = requests.post(TURNSTILE_SITEVERIFY_URL, data=payload, timeout=TURNSTILE_TIMEOUT_SECONDS)
		response.raise_for_status()
		verification = response.json()
	except (requests.RequestException, ValueError):
		frappe.logger("finbyzweb").exception("Turnstile verification request failed")
		return "Cloudflare not reachable"
	if isinstance(verification, dict) and verification.get("success"):
		return ""
	codes = verification.get("error-codes", []) if isinstance(verification, dict) else []
	return "rejected: " + (", ".join(map(str, codes)) or "unknown")


def _require_contact(email: str, mobile_no: str) -> None:
	"""Refuse only a post nobody could answer: no valid email and no phone with 6+ digits.

	The website forms check both before sending, so this stops junk (and the daily health probe)
	before it counts against the unverified limit or becomes a Lead.
	"""
	email_ok = bool(email and frappe.utils.validate_email_address((email or "").strip()))
	phone_ok = sum(ch.isdigit() for ch in (mobile_no or "")) >= 6
	if not (email_ok or phone_ok):
		frappe.throw("Please enter a valid email or phone number.")


def _inquiry_check(message: str) -> str:
	"""Security check for website inquiries that never loses a real inquiry.

	A visitor whose browser cannot finish the Cloudflare check (privacy browsers, in-app browsers,
	blocked scripts, slow networks) used to be refused. Now the Lead is saved with a note at the top
	of its message, and only a flood of unverified posts (a bot) is refused.
	"""
	reason = _turnstile_result(frappe.form_dict.get("cf-turnstile-response"))
	if not reason:
		return message or ""
	cap = frappe.utils.cint(frappe.conf.get("website_unverified_leads_per_hour") or UNVERIFIED_LEADS_PER_HOUR)
	key = "finbyzweb:unverified_leads:" + datetime.now(timezone.utc).strftime("%Y%m%d%H")
	count = frappe.cache.incrby(key, 1)
	frappe.cache.expire(key, 7200)
	frappe.logger("finbyzweb").warning("Website inquiry without security check (%s), %s this hour", reason, count)
	if count > cap:
		if count == cap + 1:
			frappe.log_error("Website inquiries: unverified limit reached",
				f"More than {cap} inquiries this hour without a passed security check. Further ones are refused until the hour ends. Last reason: {reason}")
			frappe.db.commit()
		frappe.throw("Too many requests. Please try again later or write to info@finbyz.tech.", frappe.PermissionError)
	note = f"[Security check not completed: {reason}. Saved so the inquiry is not lost; may be spam.]"
	return "\n\n".join(filter(None, [note, message]))


def _verify_turnstile(token: str | None) -> None:
	if not token:
		frappe.throw("Please complete the security check.", frappe.PermissionError)

	secret = frappe.conf.get("turnstile_secret_key")
	if not secret:
		frappe.logger("finbyzweb").error("Turnstile secret key is not configured")
		frappe.throw("Security check is unavailable. Please try again later.", frappe.PermissionError)

	payload = {"secret": secret, "response": token}
	if remote_ip := getattr(frappe.local, "request_ip", None):
		payload["remoteip"] = remote_ip

	try:
		response = requests.post(
			TURNSTILE_SITEVERIFY_URL,
			data=payload,
			timeout=TURNSTILE_TIMEOUT_SECONDS,
		)
		response.raise_for_status()
		verification = response.json()
	except (requests.RequestException, ValueError):
		frappe.logger("finbyzweb").exception("Turnstile verification request failed")
		frappe.throw("Security check is unavailable. Please try again later.", frappe.PermissionError)

	if not isinstance(verification, dict) or not verification.get("success"):
		error_codes = verification.get("error-codes", []) if isinstance(verification, dict) else []
		frappe.logger("finbyzweb").warning("Turnstile verification failed: %s", error_codes)
		frappe.throw("Security check failed. Please try again.", frappe.PermissionError)


@frappe.whitelist(allow_guest=True)
def related_link_query(doctype, txt, searchfield, start, page_len, filters):
	cond = ""
	args = {

	}
	# doctype and searchfield are pasted into the SQL as names, so accept only a real
	# doctype and one of its real columns
	ref_doc = filters.get("reference_doctype")
	if not ref_doc or not frappe.db.exists("DocType", ref_doc):
		frappe.throw(_("Invalid reference doctype"))
	meta = frappe.get_meta(ref_doc)
	if searchfield not in meta.get_valid_columns():
		frappe.throw(_("Invalid search field"))
	if meta.get_field('published'):
		return frappe.db.sql("""select name
				from `tab{ref_doc}` where published = 1 and `{key}` LIKE %(txt)s {cond}
			"""
			.format(ref_doc=filters.get("reference_doctype"), key=searchfield, cond=cond), {
				'txt': '%' + txt + '%',
			})
	else:
		return frappe.db.sql("""select name
				from `tab{ref_doc}` where `{key}` LIKE %(txt)s {cond}
			"""
			.format(ref_doc=filters.get("reference_doctype"), key=searchfield, cond=cond), {
				'txt': '%' + txt + '%',
			})
	
def add_preload_headers(response):
	pass

@frappe.whitelist(allow_guest=True)
def select_category(gallery_category=None,gallery_sub_category=None):
	condition = ""
	values = {}
	if str(gallery_category) != "All":
		condition += "where gallery_category = %(gallery_category)s"
		values["gallery_category"] = gallery_category
	if gallery_sub_category:
		condition += " and gallery_sub_category = %(gallery_sub_category)s"
		values["gallery_sub_category"] = gallery_sub_category
	result = frappe.db.sql(f"""select * from `tabGallery` {condition}""", values or (), as_dict = 1)

	output = ""
	for row in result:
		doc_dict = {'doc' :row}
		output += frappe.render_template("finbyzweb/doctype/gallery/templates/gallery_row.html", doc_dict)
	return output

@frappe.whitelist(allow_guest=True)
def get_sub_category(category=None):
	output = frappe.db.get_all('Gallery Sub Category',filters={'category':category},fields=['name','category'])
	return output


@frappe.whitelist()
def get_employee_joining_detail(token):
	# returns the whole record (bank, ID numbers); the joining form uses
	# employee_joining_detail.get_employee_data instead
	frappe.only_for(("System Manager", "HR Manager"))
	if not frappe.db.exists("Employee Joining Detail", {"token": token}):
		frappe.throw(_("You are not authorized to view this record!"))
		return
	joining_detail = frappe.get_doc("Employee Joining Detail", {"token": token})
	return joining_detail.as_dict()

from frappe import _
@frappe.whitelist(methods=['POST'])
def update_employee_joining_detail(email,data):
	"""
	ENDPOINT: /api/method/finbyzweb.api.update_employee_joining_detail
	"""
	# knowing a personal email was enough to rewrite any field (bank details, token) of a
	# joining record; the joining form uses employee_joining_detail.update_employee_data
	frappe.only_for(("System Manager", "HR Manager"))
	data = frappe.parse_json(data)
	if not frappe.db.exists("Employee Joining Detail", {"personal_email": email}):
		frappe.throw(_("You are not authorized to update this record!"))
		return
	joining_detail = frappe.get_doc("Employee Joining Detail", {"personal_email": email})
	joining_detail.update(data)
	joining_detail.flags.ignore_permissions = True
	joining_detail.save()
	return _("Updated successfully!")
