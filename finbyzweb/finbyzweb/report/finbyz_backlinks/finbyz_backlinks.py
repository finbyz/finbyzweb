# Copyright (c) 2023, Finbyz Tech Pvt Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart_data(data)
    return columns, data, None, chart

def get_columns(filters):
    columns = [
        {"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 150},
        {"label": _("Live Backlink"), "fieldname": "live_backlinks", "fieldtype": "HTML", "width": 310},
        {"label": _("Domain Authority"), "fieldname": "domiain_authority", "fieldtype": "Int", "width": 180},
        {"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 201},
        {"label": _("Submitted URL"), "fieldname": "submitted_url", "fieldtype": "Data", "width": 310},
    ]
    return columns

def get_data(filters):
    data = frappe.db.sql('''
        SELECT
            backlink_register.date as date,
            backlink_register.live_backlinks as live_backlinks,
            backlink_register.domiain_authority as domiain_authority,
            backlink_register.type as type,
            backlink_register.submitted_url as submitted_url
        FROM `tabBacklink Register` backlink_register
        WHERE date(backlink_register.date) BETWEEN %(from_date)s AND %(to_date)s {conditions}
        ORDER BY backlink_register.date
    ''' .format(conditions=get_conditions(filters)), filters, as_dict=1)

    for entry in data:
        link=entry["live_backlinks"]
        entry["live_backlinks"] = f'<a href="{entry["live_backlinks"]}" target="_blank">{link}</a>'

    return data

def get_conditions(filters):
    conditions = []

    if filters.get("for_page_type"):
        conditions.append(" AND backlink_register.for_page_type=%(for_page_type)s")

    if filters.get("for_page"):
        conditions.append(" AND backlink_register.for_page=%(for_page)s")
        
    if filters.get("type"):
        conditions.append(" AND backlink_register.type=%(type)s")

    return " ".join(conditions) if conditions else ""

def get_chart_data(data):
    chart_data = {}
    for entry in data:
        if entry["date"] not in chart_data.keys():
            chart_data[entry["date"]] = 1
        else:
            chart_data[entry["date"]] += 1
    
    date_list = []
    backlink_list = []

    for k, v in chart_data.items():
        date_list.append(k)
        backlink_list.append(v)

    return {
        "data": {
            "labels": date_list,
            "datasets": [
                {
                    "name": "Live Backlinks",
                    "values": backlink_list,
                    "colors": "#3366FF"
                }
            ]
        },
        "type": "bar",
        "fieldtype": "Int",
    }
