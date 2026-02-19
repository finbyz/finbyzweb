def set_lead_type(doc, method):
    """
    If Lead is created from the Lead Webform and 'End User' is selected,
    then set type = 'Client'
    """
    
    
    if doc.type == "End User":
        doc.type = "Client"