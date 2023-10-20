from __future__ import unicode_literals
import frappe

def execute():
    frappe.db.sql("""update `tabBacklink Register` set `type` = 'Comments' WHERE `type` = 'Quora Comments' """)