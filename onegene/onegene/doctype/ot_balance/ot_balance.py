# Copyright (c) 2024, TEAMPRO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today,get_first_day, get_last_day, add_days


class OTBalance(Document):
	pass

@frappe.whitelist()
def update_ot_hrs():
	date=add_days(today(),-1)
	# date="2024-06-30"
	month_start=get_first_day(today())
	month_end=get_last_day(today())
	attendance=frappe.get_all("Attendance",{'attendance_date':date,'docstatus':('!=',2),'custom_employee_category':('not in', ['Staff','Sub Staff']),'custom_overtime_hours':('>=',2),"custom_ot_balance_updated":0},['*'])
	for att in attendance:
		print(att.name)
		# if att.custom_employee_category not in ['Staff','Sub Staff'] and att.custom_overtime_hours>=2:
		if not frappe.db.exists("OT Balance",{'employee':att.employee,'from_date':month_start,'to_date':month_end}):
			otb=frappe.new_doc("OT Balance")
			otb.employee=att.employee
			otb.from_date=month_start
			otb.to_date=month_end
			otb.total_ot_hours = att.custom_overtime_hours
			draft=frappe.db.count("Leave Application",{'employee':att.employee,'from_date':('between',[month_start,month_end]),'to_date':('between',[month_start,month_end]),'workflow_state':'Draft','docstatus':('!=',2),'custom_select_leave_type':'Comp-off from OT'})
			approved=frappe.db.count("Leave Application",{'employee':att.employee,'from_date':('between',[month_start,month_end]),'to_date':('between',[month_start,month_end]),'workflow_state':'Approved','docstatus':('!=',2),'custom_select_leave_type':'Comp-off from OT'})
			otb.comp_off_pending_for_approval = draft * 8
			otb.comp_off_used = approved * 8
			otb.ot_balance = otb.total_ot_hours - ((draft * 8)+(approved * 8))
			otb.save(ignore_permissions=True)
		else:
			otb=frappe.get_doc("OT Balance",{'employee':att.employee,'from_date':month_start,'to_date':month_end})
			otb.total_ot_hours += att.custom_overtime_hours
			draft=frappe.db.count("Leave Application",{'employee':att.employee,'from_date':('between',[month_start,month_end]),'to_date':('between',[month_start,month_end]),'workflow_state':'Draft','docstatus':('!=',2),'custom_select_leave_type':'Comp-off from OT'})
			approved=frappe.db.count("Leave Application",{'employee':att.employee,'from_date':('between',[month_start,month_end]),'to_date':('between',[month_start,month_end]),'workflow_state':'Approved','docstatus':('!=',2),'custom_select_leave_type':'Comp-off from OT'})
			otb.comp_off_pending_for_approval = draft * 8
			otb.comp_off_used = approved * 8
			otb.ot_balance = otb.total_ot_hours - ((draft * 8)+(approved * 8))
			otb.save(ignore_permissions=True)
		

@frappe.whitelist()
def cron_for_ot_balance():
	job = frappe.db.exists('Scheduled Job Type', 'update_ot_hrs')
	if not job:
		sjt = frappe.new_doc("Scheduled Job Type")  
		sjt.update({
			"method" : 'onegene.onegene.doctype.ot_balance.ot_balance.update_ot_hrs',
			"frequency" : 'Cron',
			"cron_format" : '00 08 * * *'
		})
		sjt.save(ignore_permissions=True)