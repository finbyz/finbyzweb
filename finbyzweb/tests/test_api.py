from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import frappe
import requests

from finbyzweb.api import (
	TURNSTILE_SITEVERIFY_URL,
	TURNSTILE_TIMEOUT_SECONDS,
	_verify_turnstile,
	set_form_contact_data,
)


class TestTurnstileVerification(TestCase):
	def setUp(self):
		self.local_patcher = patch(
			"finbyzweb.api.frappe.local",
			SimpleNamespace(
				flags=SimpleNamespace(in_test=False),
				request=None,
				request_ip="203.0.113.10",
			),
		)
		self.logger_patcher = patch("finbyzweb.api.frappe.logger", return_value=Mock())
		self.throw_patcher = patch("finbyzweb.api.frappe.throw", side_effect=self._raise_frappe_error)
		self.local_patcher.start()
		self.logger_patcher.start()
		self.throw_patcher.start()

	def tearDown(self):
		self.throw_patcher.stop()
		self.logger_patcher.stop()
		self.local_patcher.stop()

	@staticmethod
	def _raise_frappe_error(message, exception):
		raise exception(message)

	def test_missing_token_is_rejected_without_request(self):
		with patch("finbyzweb.api.requests.post") as post:
			with self.assertRaises(frappe.PermissionError):
				_verify_turnstile(None)

		post.assert_not_called()

	def test_valid_token_is_verified_with_cloudflare(self):
		response = Mock()
		response.json.return_value = {"success": True}

		with patch("finbyzweb.api.frappe.conf", {"turnstile_secret_key": "test-secret"}):
			with patch("finbyzweb.api.requests.post", return_value=response) as post:
				_verify_turnstile("valid-token")

		post.assert_called_once_with(
			TURNSTILE_SITEVERIFY_URL,
			data={
				"secret": "test-secret",
				"response": "valid-token",
				"remoteip": "203.0.113.10",
			},
			timeout=TURNSTILE_TIMEOUT_SECONDS,
		)
		response.raise_for_status.assert_called_once_with()

	def test_missing_secret_is_rejected_without_request(self):
		with patch("finbyzweb.api.frappe.conf", {}):
			with patch("finbyzweb.api.requests.post") as post:
				with self.assertRaises(frappe.PermissionError):
					_verify_turnstile("unverified-token")

		post.assert_not_called()

	def test_invalid_token_is_rejected(self):
		response = Mock()
		response.json.return_value = {
			"success": False,
			"error-codes": ["timeout-or-duplicate"],
		}

		with patch("finbyzweb.api.frappe.conf", {"turnstile_secret_key": "test-secret"}):
			with patch("finbyzweb.api.requests.post", return_value=response):
				with self.assertRaises(frappe.PermissionError):
					_verify_turnstile("stale-token")

	def test_provider_failure_is_rejected(self):
		with patch("finbyzweb.api.frappe.conf", {"turnstile_secret_key": "test-secret"}):
			with patch(
				"finbyzweb.api.requests.post",
				side_effect=requests.ConnectionError("provider unavailable"),
			):
				with self.assertRaises(frappe.PermissionError):
					_verify_turnstile("unverified-token")

	def test_contact_form_verifies_token_before_creating_lead(self):
		with patch("finbyzweb.api.frappe.form_dict", {"cf-turnstile-response": "contact-token"}):
			with patch("finbyzweb.api._verify_turnstile") as verify:
				with patch("finbyzweb.api.frappe.new_doc", return_value=Mock()) as new_doc, patch("finbyzweb.api.frappe.db", Mock()):
					set_form_contact_data(
						lead_name="Test Lead",
						company_name="Test Company",
						mobile_no="+911234567890",
						title="Contact",
						email="lead@example.com",
						notes="Please contact me",
					)

		verify.assert_called_once_with("contact-token")
		new_doc.assert_called_once_with("Lead")
