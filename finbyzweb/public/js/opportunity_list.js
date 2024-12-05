frappe.listview_settings['Opportunity'] = {
    get_indicator: function(doc) {
        try {
            console.log("get_indicator triggered for", doc.name, "with status", doc.status);

            if (!doc.status) {
                console.warn("No status available for", doc.name);
                return [__("No Status"), "gray", "status,=,No Status"];
            }

            // Your existing status checks remain the same
            switch(doc.status) {
                case "Open":
                    return [__("Open"), "red", "status,=,Open"];
                case "Quotation":
                    return [__("Quotation"), "yellow", "status,=,Quotation"];
                case "Lost":
                    return [__("Lost"), "blue", "status,=,Lost"];
                case "Replied":
                    return [__("Replied"), "pink", "status,=,Replied"];
                case "Closed":
                    return [__("Closed"), "green", "status,=,Closed"];
                case "Converted":
                    return [__("Converted"), "green", "status,=,Converted"];
                default:
                    console.warn("Unhandled status:", doc.status);
                    return [__(doc.status), "gray", "status,!=,Closed"];
            }
        } catch (error) {
            console.error("Error in get_indicator:", error);
            return [__("Error"), "red", ""];
        }
    }
};