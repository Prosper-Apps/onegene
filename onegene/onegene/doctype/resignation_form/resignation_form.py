# Copyright (c) 2024, TEAMPRO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ResignationForm(Document):
	pass

	def on_submit(self):
		if self.workflow_state == 'Approved':
			frappe.db.set_value('Employee', self.employee,'resignation_letter_date', self.posting_date)
			frappe.db.set_value('Employee', self.employee,'relieving_date', self.hod_relieving_date)
			frappe.db.set_value('Employee', self.employee,'held_on', self.exit_interview_held_on)
			frappe.db.set_value('Employee', self.employee,'reason_for_leaving', self.reason)
			frappe.db.set_value('Employee', self.employee,'feedback', self.feedback)
			frappe.db.set_value('Employee', self.employee,'new_workplace', self.new_workplace)

	def on_cancel(self):
		emp = frappe.get_doc("Employee",self.employee)
		emp.resignation_letter_date = ''
		emp.relieving_date = ''
		emp.reason_for_leaving = ''
		emp.exit_interview_held_on = ''
		emp.feedback = ''
		emp.new_workplace = ''
		emp.save(ignore_permissions = True)
		frappe.db.sql("""update `tabFull and Final Statement` set docstatus = 2 where custom_resignation_form = '%s' """%(self.name),as_dict = True)
		

	def amend_to_submit(self):
		pass


@frappe.whitelist()
def update_employee(doc,method):
	if doc.workflow_state == 'Approved' and doc.custom_type == "Termination":
		employee = frappe.get_doc('Employee', {'name':doc.employee},['name'])
		frappe.db.set_value('Employee', employee,'status', "Left")
		frappe.db.set_value('Employee', employee,'resignation_letter_date', doc.custom_termination_date)
		frappe.db.set_value('Employee', employee,'relieving_date', doc.custom_termination_date)
		frappe.db.set_value('Employee', employee,'held_on', doc.custom_termination_date)
		frappe.db.set_value('Employee', employee,'reason_for_leaving', doc.custom_termination_reason)

@frappe.whitelist()
def revert_employee(doc,method):
	if doc.workflow_state == 'Approved' and doc.custom_type == "Termination":
		employee = frappe.get_doc('Employee', {'name':doc.employee},['name'])
		frappe.db.set_value('Employee', employee,'status', "Active")
		frappe.db.set_value('Employee', employee,'resignation_letter_date', " ")
		frappe.db.set_value('Employee', employee,'relieving_date',  " ")
		frappe.db.set_value('Employee', employee,'held_on',  " ")
		frappe.db.set_value('Employee', employee,'reason_for_leaving',  " ")
		



