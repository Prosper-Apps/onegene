import frappe
from frappe.model.document import Document

class SupportTicket(Document):
	pass

@frappe.whitelist()
def create_issue_from_support_ticket(support_ticket):
    support_ticket_doc = frappe.get_doc("Support Ticket", support_ticket)
    isu = frappe.new_doc("Issue")
    isu.subject = support_ticket_doc.subject
    isu.status = support_ticket_doc.status
    isu.description = support_ticket_doc.description
    isu.resolution_details = support_ticket_doc.resolution_details
    isu.opening_date = support_ticket_doc.opening_date
    isu.opening_time = support_ticket_doc.opening_time
    isu.flags.ignore_mandatory = True
    isu.save(ignore_permissions=True)

    return isu.name

@frappe.whitelist()
def send_mail_to_support_team(subject, message, recipients, sender):
    """
    Send an email to the specified recipients with the given subject and message.
    """
    if not frappe.db.exists("Email Account", {"email_id": sender}):
        frappe.throw(_("Sender email not configured in Email Account"))

    # Add additional content to the message body
    message_body = f"Dear Sir/Madam,<br><br>\
                    Greetings from Wonjin!!<br><br>\
                    Hope this mail finds you well!!<br><br>\
                    {message}<br><br>\
                    Thanks & Regards,<br>\
                    Wonjin Support"

    try:
        frappe.sendmail(
            recipients=recipients,
            sender=sender,
            subject=subject,
            message=message_body,
            now=True
        )
        return "Email sent successfully"
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), 'Email Sending Failed')
        return "Failed to send email"

