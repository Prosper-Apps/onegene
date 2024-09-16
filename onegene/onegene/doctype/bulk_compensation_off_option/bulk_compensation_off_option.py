# Copyright (c) 2024, TEAMPRO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, cint, date_diff, format_date, getdate
from hrms.hr.utils import (
	create_additional_leave_ledger_entry,
	get_holiday_dates_for_employee,
	get_leave_period,
	validate_active_employee,
	validate_dates,
	validate_overlap,
)

class BulkCompensationOffOption(Document):
	pass

	def validate(self):
		print("HI")
		holiday_list = frappe.db.get_value('Company', {'name': self.company}, 'default_holiday_list')
		holiday = frappe.db.sql("""
			SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off 
			FROM `tabHoliday List` 
			LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name 
			WHERE `tabHoliday List`.name = %s AND holiday_date = %s
		""", (holiday_list, self.holiday_date), as_dict=True)
		if not holiday:
			frappe.throw("The above mentioned holiday date is not a holiday")
		if self.compensation_off_date != '':
			holiday = frappe.db.sql("""
			SELECT `tabHoliday`.holiday_date, `tabHoliday`.weekly_off 
			FROM `tabHoliday List` 
			LEFT JOIN `tabHoliday` ON `tabHoliday`.parent = `tabHoliday List`.name 
			WHERE `tabHoliday List`.name = %s AND holiday_date = %s
		""", (holiday_list, self.compensation_off_date), as_dict=True)
			if  holiday:
				frappe.throw("The above mentioned compensation off date is a holiday,choose a another working day")

	@frappe.whitelist()
	def get_employees(self):
		datalist = []
		data = {}
		conditions = ''
		if self.company:
			conditions += "and company = '%s' " % (self.company)
		if self.employee:
			conditions += "and employee = '%s' " % (self.employee)
		if self.employee_category:
			conditions += "and custom_employee_category = '%s' " % (self.employee_category)
		if self.department:
			conditions += "and department = '%s' " % (self.department)
		if self.designation:
			conditions += "and custom_designation = '%s' " % (self.designation)
		employees = frappe.db.sql("""select * from `tabAttendance` where status = 'Present' and docstatus = 1 and custom_compensation_marked = 0 and attendance_date = '%s' %s """ % (self.holiday_date,conditions), as_dict=True)
		for emp in employees:
			data.update({
				'employee':emp['employee'],
				'attendance':emp['name']
			})
			datalist.append(data.copy())
		return datalist
	
	@frappe.whitelist()
	def mark_compoff(self):
		employees_list = frappe.get_all("Employees List", {'parent': self.name}, ['*'])
		for i in employees_list:
			if self.compensation_marked == 0:
				leave_period = get_leave_period(self.holiday_date, self.holiday_date, self.company)
				if leave_period:
					frappe.errprint("helloworld")
					leave_allocation = frappe.db.sql(
						"""
						select *
						from `tabLeave Allocation`
						where employee=%(employee)s and leave_type=%(leave_type)s
							and docstatus=1
							and (from_date between %(from_date)s and %(to_date)s
								or to_date between %(from_date)s and %(to_date)s
								or (from_date < %(from_date)s and to_date > %(to_date)s))
					""",
						{
							"from_date": leave_period[0].from_date,
							"to_date": leave_period[0].to_date,
							"employee": i.employee,
							"leave_type": "Compensatory Off",
						},
						as_dict=1,
					)
					if leave_allocation :
						frappe.errprint('allocated')
						for allocation in leave_allocation:
							new_leave = allocation['new_leaves_allocated'] + 1
							allocation = frappe.get_doc("Leave Allocation",allocation['name'])
							allocation.new_leaves_allocated= new_leave
							allocation.total_leaves_allocated= new_leave
							allocation.save(ignore_permissions=True)
							frappe.db.commit()
					else:
						frappe.errprint('not allocated')
						is_carry_forward = frappe.db.get_value("Leave Type", "Compensatory Off", "is_carry_forward")
						allocation = frappe.get_doc(
							dict(
								doctype="Leave Allocation",
								employee=i.employee,
								leave_type= "Compensatory Off",
								from_date=add_days(self.holiday_date, 1),
								to_date=leave_period[0].to_date,
								carry_forward=cint(is_carry_forward),
								new_leaves_allocated= "1" ,
								total_leaves_allocated= "1" 
							)
						)
						allocation.insert(ignore_permissions=True)
						allocation.submit()
				# if not frappe.db.exists("Leave Application",{'employee':i.employee,'from_date':self.compensation_off_date,'docstatus':('!=',2)}):
				# 	frappe.errprint("helloworld2")
				# 	leave = frappe.new_doc("Leave Application")
				# 	leave.employee = i.employee
				# 	leave.from_date = self.compensation_off_date
				# 	leave.to_date = self.compensation_off_date
				# 	leave.leave_type = "Compensatory Off"
				# 	leave.description = "Compensatory Off - worked on " + self.holiday_date
				# 	leave.status = "Approved"
				# 	leave.workflow_state = "Approved"
				# 	leave.save(ignore_permissions = True)
				# 	leave.submit()
				# 	frappe.db.commit()
				frappe.db.set_value("Attendance",i.attendance,'custom_compensation_marked',1)
		return "OK"	