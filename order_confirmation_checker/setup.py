import frappe

def after_install():
    add_workflow_action()

def after_uninstall():
    remove_workflow_action()

def add_workflow_action():
    try:
        workflow_doc = frappe.get_doc("Workflow", "Purchase Order Approval")
        workflow_doc.append("states", {
            "state": "Order Not Confirmed",
            "doc_status": "1",
            "allow_edit": "Purchase Manager"
        })
        workflow_doc.append("transitions", {
            "state": "Order Not Confirmed",
            "action": "Confirm PO",
            "next_state": "Expect Delivery",
            "allowed": "Purchase Manager",
            "allow_self_approval": 1,
            "dont_send_notification_workflow": 1
        })
        workflow_doc.save(ignore_permissions=True)
    except Exception as e:
        raise e

def remove_workflow_action():
    state_list = frappe.get_list("Workflow Document State", {"state": "Order Not Confirmed"}, ["name"])
    transition_list = frappe.get_list("Workflow Transition", {"state": "Order Not Confirmed"}, ["name"])
    for state in state_list:
        frappe.delete_doc("Workflow Document State", state.get("name"))
    for transition in transition_list:
        frappe.delete_doc("Workflow Transition", transition.get("name"))