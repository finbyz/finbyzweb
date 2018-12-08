# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe, erpnext
from frappe import _
from frappe.utils import cint, flt, cstr
import json
import sys

# Overrided Modules
from erpnext.stock.stock_ledger import get_previous_sle, get_valuation_rate
from erpnext.stock.utils import get_avg_purchase_rate, get_valuation_method, get_fifo_rate
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry

__version__ = '0.0.1'


frappe.db.set_value("Test", "TEST-0001", 'sys_path', '\n'.join(sys.path))
'''
	Overrided for following .py files
	utils.py, stock_entry.py, 
'''
@frappe.whitelist()
def get_incoming_rate(args):
	"""Get Incoming Rate based on valuation method"""
	if isinstance(args, basestring):
		args = json.loads(args)

	in_rate = 0

	frappe.msgprint("__init__")

	if (args.get("serial_no") or "").strip():
		in_rate = get_avg_purchase_rate(args.get("serial_no"))
	else:
		valuation_method = get_valuation_method(args.get("item_code"))
		previous_sle = get_previous_sle(args)
		if valuation_method == 'FIFO':
			if previous_sle:
				previous_stock_queue = json.loads(previous_sle.get('stock_queue', '[]') or '[]')
				in_rate = get_fifo_rate(previous_stock_queue, args.get("qty") or 0) if previous_stock_queue else 0
		elif valuation_method == 'Moving Average':
			in_rate = previous_sle.get('valuation_rate') or 0

	if not in_rate:
		voucher_no = args.get('voucher_no') or args.get('name')
		in_rate = get_valuation_rate(args.get('item_code'), args.get('warehouse'),
			args.get('voucher_type'), voucher_no, args.get('allow_zero_valuation'),
			currency=erpnext.get_company_currency(args.get('company')), company=args.get('company'))

	return in_rate

# stock_entry.py
def get_args_for_incoming_rate(self, item):
	return frappe._dict({
		"item_code": item.item_code,
		"warehouse": item.s_warehouse or item.t_warehouse,
		"posting_date": self.posting_date,
		"posting_time": self.posting_time,
		"qty": item.s_warehouse and -1*flt(item.transfer_qty) or flt(item.transfer_qty),
		"serial_no": item.serial_no,
		"voucher_type": self.doctype,
		"voucher_no": item.name,
		"company": self.company,
		"allow_zero_valuation": item.allow_zero_valuation_rate,
		"batch_no": item.batch_no,
	})


utils = sys.modules['erpnext.stock.utils']
utils.get_incoming_rate = get_incoming_rate

stock_entry = sys.modules['erpnext.stock.doctype.stock_entry.stock_entry']
stock_entry.StockEntry.get_args_for_incoming_rate = get_args_for_incoming_rate
stock_entry.get_incoming_rate = get_incoming_rate
