# Copyright (c) 2024, TEAMPRO and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import timedelta



class PayrollProcess(Document):
	pass

@frappe.whitelist()
def attendance_calc(from_date,to_date):
	# from_date='2023-01-01'
	# to_date='2023-01-30'

	employees = frappe.get_all("Employee",{"status":"Active"},["*"])
	for emp in employees:
		late_list = 0
		attendance=frappe.get_all('Attendance',{'employee':emp.employee,'attendance_date':['between',(from_date,to_date)],'docstatus':('!=', 2)},['*'])
		for att in attendance:
			start_time = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time"])
			time= start_time + timedelta(minutes=5)
			in_time = att.in_time.time()
			if in_time > start_time:
				late_list += 1			
				if late_list > 0:
					allowed_late = 2
					actual_late = late_list - allowed_late 
					if actual_late >= 0:
						at = actual_late
					else:
						at = 0
					if at >= 3:
						if at <= 5 :
							late = 0.5
                        elif at <=8:
                            late = 1
                        elif at <= 11 :
                            late = 1.5
                        elif at <= 14 :
                            late = 2
                        elif at <= 17 :
                            late = 2.5
                        elif at <= 20 :
                            late = 3
                        elif at <= 23 :
                            late = 3.5
                        elif at <= 26 :
                            late = 41
                        elif at <= 29 :
                            late = 4.5
                    else:
                        late = 0
					if late > 0 :
						if frappe.db.exists('Late Penalty',{'employee':emp.name,'from_date':from_date,'to_date':to_date}):
							lp = frappe.get_doc('Late Penalty',{'emp_name':emp.name,'from_date':from_date,'to_date':to_date})
							lp.employee == emp.name
							lp.employee_name = emp.employee_name
							lp.designation == emp.designation
							lp.department = emp.department
							lp.company=emp.company
							lp.employee_category= emp.employee_category
							lp.from_date =from_date
							lp.to_date =to_date
							lp.late_days =late_list
							lp.total_actual_lates=actual_late
							lp.deduction_days=late
						else:
							lp = frappe.new_doc('Late Penalty')
							lp.employee == emp.name
							lp.employee_name = emp.employee_name
							lp.designation == emp.designation
							lp.department = emp.department
							lp.company=emp.company
							lp.employee_category= emp.employee_category
							lp.from_date =from_date
							lp.to_date =to_date
							lp.late_days =late_list
							lp.total_actual_lates=actual_late
							lp.deduction_days=late
						lp.save()                       
						frappe.db.commit()    


                        total=0
						k=0

						leave_ledger_entries = frappe.get_all("Leave Ledger Entry",filters={'employee': emp.name, 'leave_type':'Earned Leave','to_date': ['>=', to_date]},fields=["*"], order_by="name Asc, creation Asc",limit_page_length=1 )
						if leave_ledger_entries
							latest_leave_entry = leave_ledger_entries[0]
							leave = frappe.get_all("Leave Ledger Entry",filters={'employee': emp.name,'leave_type':'Earned Leave','leaves':['<', latest_leave_entry.leaves] 'to_date': ['<=', to_date]},["*"])
							if leave:
								for i in leave:
									r=latest_leave_entry.leaves - i.leaves
									k += r
									total += k
							vr=latest_leave_entry.leaves - total
							if vr > 0:			
								adsl = frappe.new_doc("Leave Ledger Entry")
								adsl.employee = emp.name
								adsl.employee_name = emp.employee_name
								adsl.leave_type = 'Earned Leave'
								adsl.from_date =from_date
								adsl.to_date =to_date
								adsl.transaction_type ='Leave Allocation'
								adsl.company='WONJIN AUTOPARTS INDIA PVT.LTD.'
								adsl.leaves=vr- late
							else:
								adsl = frappe.new_doc("Leave Ledger Entry")
								adsl.employee = emp.name
								adsl.employee_name = emp.employee_name
								adsl.leave_type = 'Leave Without Pay'
								adsl.from_date =from_date
								adsl.to_date =to_date
								adsl.transaction_type ='Leave Allocation'
								adsl.company='WONJIN AUTOPARTS INDIA PVT.LTD.'          
								adsl.leaves=late
						else:
							adsl = frappe.new_doc("Leave Ledger Entry")
							adsl.employee = emp.name
							adsl.employee_name = emp.employee_name
							adsl.leave_type = 'Leave Without Pay'
							adsl.from_date =from_date
							adsl.to_date =to_date
							adsl.transaction_type ='Leave Allocation'
							adsl.company='WONJIN AUTOPARTS INDIA PVT.LTD.'          
							adsl.leaves=late
						adsl.save()                       
						frappe.db.commit()                          
					return 'ok'


					















