import frappe
from frappe import _
from frappe.utils import now
from frappe.utils import now_datetime, add_to_date
from frappe.core.doctype.communication.email import _make

@frappe.whitelist()
def update_workflow_timestamp(self, method):
    if self.workflow_state and self.workflow_state == 'Waiting for PO Confirmation':
        self.custom_workflow_state_timestamp = now()

@frappe.whitelist()
def check_order_confirmation():
    # Get all Purchase Orders in 'Waiting for PO Confirmation' state
    pos = frappe.get_all("Purchase Order", 
                         filters={"workflow_state": "Waiting for PO Confirmation"},
                         fields=["name", "custom_workflow_state_timestamp", "follow_up_email_sent",
                                 "email_template_to_send_email", "email_account_to_send_email", "contact_email"])
    
    for po in pos:
        attachments = frappe.get_all("File", filters={"attached_to_doctype": "Purchase Order", "attached_to_name": po.name})
        if len(attachments) < 1:
            timestamp = frappe.utils.get_datetime(po.custom_workflow_state_timestamp)
            four_days_later = add_to_date(timestamp, days=4)
            eight_days_later = add_to_date(timestamp, days=8)
            
            if now_datetime() > eight_days_later and po.follow_up_email_sent:
                frappe.db.set_value("Purchase Order", po.name, "workflow_state", "Order Not Confirmed")
            elif now_datetime() > four_days_later and not po.follow_up_email_sent:
                if not po.email_template_to_send_email or not po.email_account_to_send_email or not po.contact_email:
                    continue
                
                doc = frappe.get_doc("Purchase Order", po.name)
                doc_args = doc.as_dict()
                email_template = frappe.get_doc("Email Template", po.email_template_to_send_email)
                message = frappe.render_template(email_template.response_, doc_args)
                subject = frappe.render_template(email_template.subject, doc_args)
                sender_email = frappe.db.get_value("Email Account", po.email_account_to_send_email, "email_id")
                email_send = _make(
                    subject=subject,
                    content=message,
                    recipients=po.contact_email,
                    sender=sender_email,
                    send_email=True,
                    doctype="Purchase Order",
                    name=po.name,
                )
                if email_send["name"]:
                    frappe.db.set_value("Purchase Order", po.name, "follow_up_email_sent", 1)

    frappe.db.commit()