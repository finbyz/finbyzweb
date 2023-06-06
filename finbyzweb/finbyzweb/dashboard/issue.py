from __future__ import unicode_literals
from frappe import _

# def get_data(data):
#     # data['internal_links'] = {
#     #     'Timesheet': ['Time Sheets', 'issue_ref_no']
#     #     }
#     data['transactions'] += [
#         {
#             'label': _('Feedback Form'),
#             'items': ['Feedback Form']
#         },
# 	]
#     return data
 

def get_data(data):
    data['non_standard_fieldnames']={
        'Feedback Form': 'document_name'
    }
    data['transactions']+= [
        {	
            'label': _('Feedback Form'),
            'items': ['Feedback Form']
        }
    ]
    return data 
	