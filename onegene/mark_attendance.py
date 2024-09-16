# from _future_ import print_function
from pickle import TRUE
from time import strptime
from traceback import print_tb
import frappe
from frappe.utils.data import ceil, get_time, get_year_start
import json
import datetime
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from datetime import datetime
from calendar import monthrange
from frappe import _, msgprint
from frappe.utils import flt
from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
import requests
from datetime import date, timedelta,time
from datetime import datetime, timedelta
from frappe.utils import get_url_to_form
import math
import dateutil.relativedelta
from frappe.utils.background_jobs import enqueue
import datetime as dt
from datetime import datetime, timedelta

@frappe.whitelist()
def cron_job1():
	job = frappe.db.exists('Scheduled Job Type', 'mark_att_multidate')
	if not job:
		sjt = frappe.new_doc("Scheduled Job Type")  
		sjt.update({
			"method" : 'onegene.mark_attendance.mark_att_multidate',
			"frequency" : 'Cron',
			"cron_format" : '0 2 * * * *'
		})
		sjt.save(ignore_permissions=True)

@frappe.whitelist()
def enqueue_mark_att_month():
	enqueue(mark_att_month, queue='default', timeout=6000)

@frappe.whitelist()
def mark_att_month():
	from_date = '2024-08-01'
	to_date = '2024-08-06'
	# from_date = datetime.strptime(from_date, "%d-%m-%Y").date()
	# to_date = datetime.strptime(to_date, "%d-%m-%Y").date()
	# from_date = get_first_day(from_date)
	# to_date = get_last_day(to_date)
	# checkins = frappe.db.sql("""select count(*) as count from `tabEmployee Checkin` where date(time) between '%s' and '%s' and device_id != "Canteen" order by time ASC  """%(from_date,to_date),as_dict=1)
	# print(checkins)
	checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and device_id != "Canteen"  order by time ASC """%(from_date,to_date),as_dict=1)
	for c in checkins:
		print(c.name)
		employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
		if employee:
			print(c.employee)  
			mark_attendance_from_checkin(c.employee,c.time,c.log_type)
	mark_wh_ot(from_date,to_date)   
	submit_present_att(from_date,to_date) 
	mark_late_early(from_date,to_date)
	# mark_absent(from_date,to_date) 


@frappe.whitelist()
def mark_att_multidate():
	from_date = add_days(today(),-3)
	to_date = today()
	checkins = frappe.db.sql("""select count(*) as count from `tabEmployee Checkin` where date(time) between '%s' and '%s' and device_id != "Canteen" order by time ASC  """%(from_date,to_date),as_dict=1)
	print(checkins)
	checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and device_id != "Canteen"  order by time ASC """%(from_date,to_date),as_dict=1)
	for c in checkins:
		print(c.name)
		employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
		if employee:  
			mark_attendance_from_checkin(c.employee,c.time,c.log_type)
	mark_wh_ot(from_date,to_date)   
	submit_present_att(from_date,to_date) 
	mark_late_early(from_date,to_date)
	mark_absent(from_date,to_date) 

	
@frappe.whitelist()
def mark_att():
	from_date = add_days(today(),-1)
	to_date = add_days(today(),0)
	checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and device_id != "Canteen" order by time ASC """%(from_date,to_date),as_dict=1)
	for c in checkins:
		print(c.name)
		employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
		if employee:
			print(c.employee)  
			mark_attendance_from_checkin(c.employee,c.time,c.log_type)
	mark_wh_ot(from_date,to_date)   
	submit_present_att(from_date,to_date) 
	mark_late_early(from_date,to_date)
	mark_absent(from_date,to_date) 


@frappe.whitelist()
def mark_att_without_employee(date):
	# from_date = add_days(date,-1)
	# to_date = add_days(date,0)
	from_date = to_date = date
	checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' and device_id != "Canteen" order by time ASC """%(from_date,to_date),as_dict=1)
	for c in checkins:
		print(c.name)
		employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
		if employee:  
			mark_attendance_from_checkin(c.employee,c.time,c.log_type)
	mark_absent(from_date,to_date) 
	mark_wh_ot(from_date,to_date)   
	submit_present_att(from_date,to_date) 
	mark_late_early(from_date,to_date) 
	# check_ot(from_date,to_date)


@frappe.whitelist()
def mark_att_from_frontend(date,employee):
	enqueue(mark_att_from_frontend_with_employee, queue='default', timeout=6000,
					date=date,employee= employee)
	
@frappe.whitelist()
def mark_att_from_frontend_with_employee(date,employee):
	# from_date =  add_days(date,-1)
	# to_date = add_days(date,0)
	from_date = to_date = date
	
	checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where date(time)= '%s' and employee = '%s' and device_id != "Canteen" order by time ASC """%(from_date,employee),as_dict=1)
	for c in checkins:
		frappe.errprint(c)
		employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
		if employee:  
			frappe.errprint(c.name)
			mark_attendance_from_checkin_new(c.employee,c.time,c.log_type)
	mark_absent_with_employee(employee,from_date,to_date) 
	mark_wh_ot_with_employee(employee,from_date,to_date)   
	submit_present_att_with_employee(employee,from_date,to_date) 
	mark_late_early_with_employee(employee,from_date,to_date)   
	# check_ot_with_employee(employee,from_date,to_date)

def mark_attendance_from_checkin(employee,time,log_type):
	att_date = time.date()
	att_time = time.time()
	if log_type == 'IN':
		# attendance_name = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':1,'status':"On Leave"})
		# if attendance_name:
		# 	attendance = frappe.get_doc("Attendance", attendance_name)
		# 	attendance.flags.ignore_permissions = True
		# 	leave = frappe.get_doc("Leave Application", attendance.leave_application)
		# 	attendance.flags.ignore_permissions = True
		# 	if leave.half_day == 0:
		# 		attendance.cancel()
		# 		leave.cancel()
		att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
		checkins = frappe.db.sql(""" select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and device_id != "Canteen" order by time ASC"""%(employee,att_date),as_dict=True)
		if not att:
			print("HI")
			att = frappe.new_doc("Attendance")
			att.employee = employee
			att.attendance_date = att_date
			att.status = 'Absent'
			att.in_time = checkins[0].time
			att.shift = get_actual_shift_start(employee ,get_time(checkins[0].time))
			att.custom_total_working_hours = "00:00:00"
			att.custom_working_hours = "0.0"
			att.custom_extra_hours = "0.0"
			att.custom_total_extra_hours = "00:00:00"
			att.custom_total_overtime_hours = "00:00:00"
			att.custom_overtime_hours = "0.0"
			att.custom_early_out_time = "00:00:00"
			att.custom_late_entry_time = "00:00:00"
			att.custom_from_time = "00:00:00"
			att.custom_to_time = "00:00:00"
			att.save(ignore_permissions=True)
			frappe.db.commit()
			for c in checkins:
				frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
				frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
		else:
			if frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':0}):
				print("Hi")
				att = frappe.get_doc("Attendance",att)
				print("attcreated")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				att.in_time = checkins[0].time
				att.shift = get_actual_shift_start(employee ,get_time(checkins[0].time))
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				print("attcreated2")
				att.save(ignore_permissions=True)
				frappe.db.commit()
				for c in checkins:
					frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
	if log_type == 'OUT':
		print("Helloooo")
		today_att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date,'docstatus':('!=',2)})
		if today_att:
			today_att = frappe.get_doc("Attendance",today_att)
			if today_att.in_time:
				in_time = today_att.in_time.time()
				checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,in_time),as_dict=True)
				today_out = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) > '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,in_time),as_dict=True)
			else:
				max_out_checkin = datetime.strptime('12:30:00','%H:%M:%S').time()
				checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,max_out_checkin),as_dict=True)
				today_out = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) > '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,max_out_checkin),as_dict=True)
		else:
			max_out_checkin = datetime.strptime('12:30:00','%H:%M:%S').time()
			today_out=''
			# today_out = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) > '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,in_time),as_dict=True)
			checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,max_out_checkin),as_dict=True)
		if checkins and not today_out:
			yesterday = add_days(att_date,-1)
			att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':yesterday,'docstatus':('!=',2)})
			if att:
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0 or att.docstatus == 1:
					if att.shift == '':
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
							frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					else:
						if len(checkins) > 0:
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
							frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = yesterday
				att.status = 'Absent'
				if len(checkins) > 0:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)			
					for c in checkins:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
					frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att	
		if today_out and not checkins:
			checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' and device_id != "Canteen" order by time ASC"""%(employee,att_date),as_dict=True)
			# attendance_name = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':1,'status':"On Leave"})
			# if attendance_name :
			# 	attendance = frappe.get_doc("Attendance", attendance_name)
			# 	attendance.flags.ignore_permissions = True
			# 	leave = frappe.get_doc("Leave Application", attendance.leave_application)
			# 	attendance.flags.ignore_permissions = True
			# 	if leave.half_day == 0:
			# 		attendance.cancel()
			# 		leave.cancel()
			att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date,'docstatus':('!=',2)})
			if att:
				print("Hello")
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0  or att.docstatus == 1:
					if not att.out_time and att.shift=='':
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
							frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					else:
						if len(checkins) > 0:
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
							frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				if len(checkins) > 0:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)			
					for c in checkins:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
					frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att
		if checkins and today_out:
			frappe.errprint("Both condition Passed")
			yesterday = add_days(att_date, -1)
			prev_att = frappe.db.exists("Attendance", {'employee': employee, 'attendance_date': yesterday, 'docstatus': ('!=', 2)})
			if prev_att:
				frappe.errprint("Previous day attendance")
				prev_att = frappe.get_doc("Attendance", prev_att)
				if prev_att.docstatus == 0 or prev_att.docstatus == 1:
					if prev_att.shift=='':
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(checkins[-1].employee,get_time(today_out[-1].time)))
							frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", prev_att.name)
						else:
							if checkins:
								frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(checkins[0].employee,get_time(today_out[0].time)))
								frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[0].time)
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", prev_att.name)
					else:
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(checkins[-1].employee,get_time(today_out[-1].time)))
							frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", prev_att.name)
						else:
							if checkins:
								frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(checkins[0].employee,get_time(today_out[0].time)))
								frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[0].time)
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", prev_att.name)

			att = frappe.db.exists("Attendance", {'employee': employee, 'attendance_date': att_date, 'docstatus': ('!=', 2)})
			if att:
				frappe.errprint("current day attendance")
				att = frappe.get_doc("Attendance", att)
				if att.docstatus == 0 or att.docstatus == 1:
					if att.shift=='':
						if len(today_out) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(today_out[-1].employee,get_time(today_out[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[-1].time)
							for c in today_out:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(today_out[0].employee,get_time(today_out[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[0].time)
							frappe.db.set_value('Employee Checkin',today_out[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",today_out[0].name, "attendance", att.name)
					else:
						if len(today_out) > 0:
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[-1].time)
							for c in today_out:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[0].time)
							frappe.db.set_value('Employee Checkin',today_out[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",today_out[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				frappe.errprint("No Attendance")
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				if len(today_out) > 0:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(today_out[-1].employee,get_time(today_out[-1].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",today_out[-1].time)			
					for c in today_out:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(today_out[0].employee,get_time(today_out[0].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",today_out[0].time)
					frappe.db.set_value('Employee Checkin',today_out[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",today_out[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att
		else:
			yesterday = add_days(att_date,1)
			next_att = frappe.db.get_value("Attendance",{'employee':employee,'attendance_date':yesterday,'docstatus':('!=',2)},['in_time'])
			next_checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,yesterday,next_att),as_dict=True)
			att = frappe.db.exists("Attendance", {'employee': employee, 'attendance_date': att_date, 'docstatus': ('!=', 2)})
			if att:
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0 or att.docstatus == 1:
					if att.shift == '':
						if len(next_checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(next_checkins[-1].employee,get_time(next_checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[-1].time)
							for c in next_checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[0].employee,get_time(next_checkins[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[0].time)
							frappe.db.set_value('Employee Checkin',next_checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",next_checkins[0].name, "attendance", att.name)
					else:
						if len(next_checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(next_checkins[-1].employee,get_time(next_checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[-1].time)
							for c in next_checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[0].employee,get_time(next_checkins[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[0].time)
							frappe.db.set_value('Employee Checkin',next_checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",next_checkins[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				if next_checkins:
					if len(next_checkins) > 0:
						frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[-1].employee,get_time(next_checkins[-1].time)))
						frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[-1].time)			
						for c in next_checkins:
							frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
					else:
						frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[0].employee,get_time(next_checkins[0].time)))
						frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[0].time)
						frappe.db.set_value('Employee Checkin',next_checkins[0].name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",next_checkins[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att

				  

def get_actual_shift_start(employee,get_shift_time):
	if frappe.db.exists("Employee",{'name':employee,'shift':"Single"}):
		shift = frappe.get_value("Employee",{'name':employee,'shift':"Single"},['default_shift'])
	else:
		shift1 = frappe.db.get_value('Shift Type',{'name':'1'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift4 = frappe.db.get_value('Shift Type',{'name':'4'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift5 = frappe.db.get_value('Shift Type',{'name':'5'},['custom_checkin_start_time','custom_checkin_end_time'])
		shiftg = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkin_start_time','custom_checkin_end_time'])
		att_time_seconds = get_shift_time.hour * 3600 + get_shift_time.minute * 60 + get_shift_time.second
		shift = ''
		
		if shift1[0].total_seconds() < att_time_seconds < shift1[1].total_seconds():
			shift = '1'
		elif shift2[0].total_seconds() < att_time_seconds < shift2[1].total_seconds():
			shift = '2'
		elif shift3[0].total_seconds() < att_time_seconds < shift3[1].total_seconds():
			shift ='3'
		elif shiftg[0].total_seconds() < att_time_seconds < shiftg[1].total_seconds():
			shift ='G'
		elif shift4[0].total_seconds() < att_time_seconds < shift4[1].total_seconds():
			shift ='4'
		elif shift5[0].total_seconds() < att_time_seconds < shift5[1].total_seconds():
			shift ='5'
			
	return shift

def get_actual_shift(employee,get_shift_time):
	if frappe.db.exists("Employee",{'name':employee,'shift':"Single"}):
		shift = frappe.get_value("Employee",{'name':employee,'shift':"Single"},['default_shift'])
	else:
		shift1 = frappe.db.get_value('Shift Type',{'name':'1'},['custom_checkout_start_time','custom_checkout_end_time'])
		shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkout_start_time','custom_checkout_end_time'])
		shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkout_start_time','custom_checkout_end_time'])
		shift4 = frappe.db.get_value('Shift Type',{'name':'4'},['custom_checkout_start_time','custom_checkout_end_time'])
		shift5 = frappe.db.get_value('Shift Type',{'name':'5'},['custom_checkout_start_time','custom_checkout_end_time'])
		shiftg = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkout_start_time','custom_checkout_end_time'])
		att_time_seconds = get_shift_time.hour * 3600 + get_shift_time.minute * 60 + get_shift_time.second
		shift = ''

		if shift1[0].total_seconds() < att_time_seconds < shift1[1].total_seconds():
			shift = '1'
		if shift2[0].total_seconds() < att_time_seconds < shift2[1].total_seconds():
			shift = '2'
		if shift3[0].total_seconds() < att_time_seconds < shift3[1].total_seconds():
			shift ='3'
		if shiftg[0].total_seconds() < att_time_seconds < shiftg[1].total_seconds():
			shift ='G'
		if shift4[0].total_seconds() < att_time_seconds < shift4[1].total_seconds():
			shift ='4'
		if shift5[0].total_seconds() < att_time_seconds < shift5[1].total_seconds():
			shift ='5'
	return shift

@frappe.whitelist()    
def mark_absent(from_date,to_date):
	dates = get_dates(from_date,to_date)
	for date in dates:
		employee = frappe.db.get_all('Employee',{'status':'Active','date_of_joining':['<=',date]},['*'])
		for emp in employee:
			hh = check_holiday(date,emp.name)
			if not hh:
				if not frappe.db.exists('Attendance',{'attendance_date':date,'employee':emp.name,'docstatus':('!=','2')}):
					att = frappe.new_doc('Attendance')
					att.employee = emp.name
					att.status = 'Absent'
					att.attendance_date = date
					att.custom_total_working_hours = "00:00:00"
					att.custom_working_hours = "0.0"
					att.custom_extra_hours = "0.0"
					att.custom_total_extra_hours = "00:00:00"
					att.custom_total_overtime_hours = "00:00:00"
					att.custom_overtime_hours = "0.0"
					att.custom_early_out_time = "00:00:00"
					att.custom_late_entry_time = "00:00:00"
					att.save(ignore_permissions=True)
					frappe.db.commit()   

def get_dates(from_date,to_date):
	no_of_days = date_diff(add_days(to_date, 1), from_date)
	dates = [add_days(from_date, i) for i in range(0, no_of_days)]
	return dates

def check_holiday(date,emp):
	holiday_list = frappe.db.get_value('Employee',{'name':emp},'holiday_list')
	holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off from `tabHoliday List`
	left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
	doj= frappe.db.get_value("Employee",{'name':emp},"date_of_joining")
	status = ''
	if holiday :
		if doj < holiday[0].holiday_date:
			if holiday[0].weekly_off == 1:
				return "WW"     
			else:
				return "HH"
		
def mark_wh_ot(from_date,to_date):
	attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2'),'status':("!=","On Leave")},['*'],order_by = 'attendance_date')
	for att in attendance:
		print(att.name)
		if att.shift and att.in_time and att.out_time :
			if att.in_time and att.out_time:
				in_time = att.in_time
				out_time = att.out_time
			if isinstance(in_time, str):
				in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
			if isinstance(out_time, str):
				out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
			wh = time_diff_in_hours(out_time,in_time)
			print(in_time)
			print(out_time)
			print(wh)
			if wh > 0 :
				if wh < 24.0:
					print(att.name)
					print("atttttt")
					time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
					frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
					frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
				else:
					wh = 24.0
					frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
					frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
				if wh < 4:
					frappe.db.set_value('Attendance',att.name,'status','Absent')
				elif wh >= 4 and wh < 8:
					custom_permission_hours = float(att.custom_permission_hours) if att.custom_permission_hours else 0.0
					if att.custom_permission_hours!='':
						tot_hours=att.working_hours+custom_permission_hours
						if tot_hours >= 8:
							frappe.db.set_value('Attendance',att.name,'status','Present')
						else:
							frappe.db.set_value('Attendance',att.name,'status','Half Day')
					else:
						frappe.db.set_value('Attendance',att.name,'status','Half Day')
				elif wh >= 8:
					frappe.db.set_value('Attendance',att.name,'status','Present')  
				shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
				shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
				shift_tot = time_diff_in_hours(shift_et,shift_st)
				time_in_standard_format_timedelta = time_diff_in_timedelta(shift_et,out_time)
				ot_hours = time(0,0,0)
				hh = check_holiday(att.attendance_date,att.employee)
				if not hh:
					if wh > shift_tot:
						shift_start_time = datetime.strptime(str(shift_et),'%H:%M:%S').time()
						if att.shift in ['1','2','G'] :
							if wh < 15 :
								shift_date = att.attendance_date
							else:
								shift_date = add_days(att.attendance_date,+1)  
						else:
							shift_date = add_days(att.attendance_date,+1)  
						ot_date_str = datetime.strptime(str(shift_date),'%Y-%m-%d').date()
						shift_start_datetime = datetime.combine(ot_date_str,shift_start_time)
						if shift_start_datetime < out_time :
							extra_hours = out_time - shift_start_datetime
							days = 1
						else:
							extra_hours = "00:00:00"
							days = 0
						if days == 1 :
							duration = datetime.strptime(str(extra_hours), "%H:%M:%S")
							total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
							rounded_number = round(total_seconds, 3)
							time_diff = datetime.strptime(str(extra_hours), '%H:%M:%S').time()
							frappe.db.set_value('Attendance',att.name,'custom_extra_hours',rounded_number)
							frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',extra_hours)
							if att.custom_employee_category not in ['Staff','Sub Staff']:
								if time_diff.hour >= 2:
									ot_request=frappe.db.get_all("OT Request",{'ot_requested_date':att.attendance_date,'department':att.department,'workflow_state':'Approved',"ot_updated":0},['name'])
									if ot_request:
										for i in ot_request:
											if frappe.db.exists("OT Request Child",{'employee_code':att.employee,'parent':i.name}):
												employee_ot_requested_hours=frappe.db.get_value("OT Request Child",{'employee_code':att.employee,'parent':i.name},['requested_ot_hours'])
												print(employee_ot_requested_hours)
												if time_diff.hour >= int(employee_ot_requested_hours):
													ot_hours = time(int(employee_ot_requested_hours),0,0)
												else:
													ot_hours = time(time_diff.hour,0,0)			
							ftr = [3600,60,1]
							hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
							ot_hr = round(hr/3600,1)
							frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',ot_hours)
							frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hr)
							# if time_diff.hour >= 1 :
							# 	if time_diff.minute <= 29:
							# 		ot_hours = time(time_diff.hour,0,0)
							# 	else:
							# 		ot_hours = time(time_diff.hour,30,0)
							# elif time_diff.hour == 0 :
							# 	if time_diff.minute <= 29:
							# 		ot_hours = time(0,0,0)
							# 	else:
							# 		ot_hours = time(time_diff.hour,30,0)
							# ftr = [3600,60,1]
							# hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
							# ot_hr = round(hr/3600,1)
							# frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',ot_hours)
							# frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hr)
						else:
							frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
							frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
							frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
							frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")
					else:
						frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
						frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
						frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
						frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")
				else:
					if wh < 24.0:
						time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
						frappe.db.set_value('Attendance', att.name, 'custom_total_extra_hours', str(time_in_standard_format))
						frappe.db.set_value('Attendance', att.name, 'custom_extra_hours', wh)
						duration = datetime.strptime(str(time_in_standard_format), "%H:%M:%S")
						total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
						rounded_number = round(total_seconds, 3)
						time_diff = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
						frappe.db.set_value('Attendance',att.name,'custom_extra_hours',rounded_number)
						frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',time_in_standard_format)
					else:
						wh = 24.0
						frappe.db.set_value('Attendance', att.name, 'custom_total_extra_hours',"23:59:59")
						frappe.db.set_value('Attendance', att.name, 'custom_extra_hours',wh)
						duration = datetime.strptime(str("23:59:59"), "%H:%M:%S")
						total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
						rounded_number = round(total_seconds, 3)
						time_diff = datetime.strptime(str("23:59:59"), '%H:%M:%S').time()
						frappe.db.set_value('Attendance',att.name,'custom_extra_hours',rounded_number)
						frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"23:59:59")
					if time_diff.hour >= 1 :
						if time_diff.minute <= 29:
							ot_hours = time(time_diff.hour,0,0)
						else:
							ot_hours = time(time_diff.hour,30,0)
					elif time_diff.hour == 0 :
						if time_diff.minute <= 29:
							ot_hours = time(0,0,0)
						else:
							ot_hours = time(time_diff.hour,30,0)
					ftr = [3600,60,1]
					hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
					ot_hr = round(hr/3600,1)
					frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',ot_hours)
					frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hr)
			else:
				frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
				frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
				frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
				frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
				frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
				frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")
		else:
			frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
			frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
			frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
			frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
			frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
			frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")

def time_diff_in_timedelta(time1, time2):
	return time2 - time1

def submit_present_att(from_date,to_date):
	attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':0},['*'])
	for att in attendance:
		if att.attendance_date == getdate(today()) and att.status == 'Present' and att.early_exit == 0:
			frappe.db.set_value('Attendance', att.name, 'docstatus', 1)
		elif att.attendance_date > getdate(today()) and att.status == 'Present':
			frappe.db.set_value('Attendance', att.name, 'docstatus', 1)
		

def mark_late_early(from_date, to_date):
	attendance = frappe.db.get_all('Attendance', {'attendance_date': ('between', (from_date, to_date)),'status':("!=","On Leave")}, ['*'],order_by = 'attendance_date')
	for att in attendance:
		hh = check_holiday(att.attendance_date, att.employee)
		if not hh:
			if att.status not in ['On Leave', 'Work From Home']:
				if att.shift and att.in_time:
					shift_time_start = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time"])
					shift_start_time = datetime.strptime(str(shift_time_start), '%H:%M:%S').time()
					start_time = dt.datetime.combine(att.attendance_date, shift_start_time)
					start_time += dt.timedelta(minutes=5)
					late_time = dt.datetime.combine(att.attendance_date, shift_start_time)
					late_time += dt.timedelta(minutes=120)                   
					# if att.in_time > late_time:
					#     frappe.db.set_value('Attendance', att.name, 'status', "Half Day")
					if att.in_time >start_time:
						frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
						frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time -start_time )
					else:
						frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
						frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")

				if att.shift and att.out_time:
					shift_time_end = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
					shift_end_time = datetime.strptime(str(shift_time_end), '%H:%M:%S').time()
					end_time = dt.datetime.combine(att.attendance_date, shift_end_time)

					if att.out_time < end_time:
						frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
						frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
					else:
						frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
						frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
			else:
				frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
				frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
				frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
				frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
		else:
			frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
			frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
			frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
			frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")

def check_ot(from_date, to_date):
	attendance = frappe.db.get_all('Attendance', {'attendance_date': ('between', (from_date, to_date))}, ['*'],order_by = 'attendance_date')
	for att in attendance:
		if att.custom_overtime_hours > 0 :
			if frappe.db.exists("OT Planning List",{'employee':att.employee,'ot_date':att.attendance_date,'docstatus':1}):
				ot_hours = frappe.get_value("OT Planning List",{'employee':att.employee,'ot_date':att.attendance_date,'docstatus':1})
				if att.custom_overtime_hours > ot_hours :
					total_seconds = int(ot_hours * 3600)
					hours = total_seconds // 3600
					minutes = (total_seconds % 3600) // 60
					seconds = total_seconds % 60
					frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',f"{hours:02}:{minutes:02}:{seconds:02}")
					frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hours)
				
@frappe.whitelist()    
def mark_absent_with_employee(employee,from_date,to_date):
	dates = get_dates(from_date,to_date)
	for date in dates:
		hh = check_holiday(date,employee)
		if not hh:
			if not frappe.db.exists('Attendance',{'attendance_date':date,'employee':employee,'docstatus':('!=','2')}):
				att = frappe.new_doc('Attendance')
			else:
				att = frappe.get_doc('Attendance',{'attendance_date':date,'employee':employee,'docstatus':('!=','2')})
			att.employee = employee
			att.status = 'Absent'
			att.attendance_date = date
			att.custom_total_working_hours = "00:00:00"
			att.custom_working_hours = "0.0"
			att.custom_extra_hours = "0.0"
			att.custom_total_extra_hours = "00:00:00"
			att.custom_total_overtime_hours = "00:00:00"
			att.custom_overtime_hours = "0.0"
			att.custom_early_out_time = "00:00:00"
			att.custom_late_entry_time = "00:00:00"
			att.save(ignore_permissions=True)
			frappe.db.commit()

def mark_wh_ot_with_employee(employee,from_date,to_date):
	attendance = frappe.db.get_all('Attendance',{'attendance_date':from_date,'docstatus':('!=','2'),'employee':employee,'status':("!=","On Leave")},['*'],order_by = 'attendance_date')
	for att in attendance:
		frappe.errprint(att.name)
		frappe.errprint("wh check")
		if att.in_time and att.out_time and att.shift:
			frappe.errprint("wh calculation")
			if att.in_time and att.out_time:
				in_time = att.in_time
				out_time = att.out_time
			if isinstance(in_time, str):
				in_time = datetime.strptime(in_time, '%Y-%m-%d %H:%M:%S')
			if isinstance(out_time, str):
				out_time = datetime.strptime(out_time, '%Y-%m-%d %H:%M:%S')
			wh = time_diff_in_hours(out_time,in_time)
			frappe.errprint(in_time)
			frappe.errprint(out_time)
			if wh > 0 :
				if wh < 24.0:
					time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
					frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours', str(time_in_standard_format))
					frappe.db.set_value('Attendance', att.name, 'working_hours', wh)
				else:
					wh = 24.0
					frappe.db.set_value('Attendance', att.name, 'custom_total_working_hours',"23:59:59")
					frappe.db.set_value('Attendance', att.name, 'working_hours',wh)
				if wh < 4:
					frappe.db.set_value('Attendance',att.name,'status','Absent')
				elif wh >= 4 and wh < 8:
					custom_permission_hours = float(att.custom_permission_hours) if att.custom_permission_hours else 0.0
					if att.custom_permission_hours!='':
						tot_hours=att.working_hours+custom_permission_hours
						if tot_hours >= 8:
							frappe.db.set_value('Attendance',att.name,'status','Present')
						else:
							frappe.db.set_value('Attendance',att.name,'status','Half Day')
					else:
						frappe.db.set_value('Attendance',att.name,'status','Half Day')
				elif wh >= 8:
					frappe.db.set_value('Attendance',att.name,'status','Present')  
				shift_st = frappe.get_value("Shift Type",{'name':att.shift},['start_time'])
				shift_et = frappe.get_value("Shift Type",{'name':att.shift},['end_time'])
				shift_tot = time_diff_in_hours(shift_et,shift_st)
				frappe.errprint(out_time)
				time_in_standard_format_timedelta = time_diff_in_timedelta(shift_et,out_time)
				ot_hours = time(0,0,0)
				hh = check_holiday(att.attendance_date,att.employee)
				if not hh:
					if wh > shift_tot:
						shift_start_time = datetime.strptime(str(shift_et),'%H:%M:%S').time()
						if att.shift in ['1','2','G'] :
							if wh < 15 :
								shift_date = att.attendance_date
							else:
								shift_date = add_days(att.attendance_date,+1)  
						else:
							shift_date = add_days(att.attendance_date,+1)  
						ot_date_str = datetime.strptime(str(shift_date),'%Y-%m-%d').date()
						shift_start_datetime = datetime.combine(ot_date_str,shift_start_time)
						if shift_start_datetime < out_time :
							extra_hours = out_time - shift_start_datetime
							days = 1
						else:
							extra_hours = "00:00:00"
							days = 0
						if days == 1 :
							duration = datetime.strptime(str(extra_hours), "%H:%M:%S")
							total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
							rounded_number = round(total_seconds, 3)
							time_diff = datetime.strptime(str(extra_hours), '%H:%M:%S').time()
							frappe.db.set_value('Attendance',att.name,'custom_extra_hours',rounded_number)
							frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',extra_hours)
							if att.custom_employee_category not in ['Staff','Sub Staff']:
								if time_diff.hour >= 2:
									ot_request=frappe.db.get_all("OT Request",{'ot_requested_date':att.attendance_date,'department':att.department,'workflow_state':'Approved',"ot_updated":0},['name'])
									if ot_request:
										for i in ot_request:
											if frappe.db.exists("OT Request Child",{'employee_code':att.employee,'parent':i.name}):
												employee_ot_requested_hours=frappe.db.get_value("OT Request Child",{'employee_code':att.employee,'parent':i.name},['requested_ot_hours'])
												print(employee_ot_requested_hours)
												if time_diff.hour >= int(employee_ot_requested_hours):
													ot_hours = time(int(employee_ot_requested_hours),0,0)
												else:
													ot_hours = time(time_diff.hour,0,0)			
							ftr = [3600,60,1]
							hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
							ot_hr = round(hr/3600,1)
							frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',ot_hours)
							frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hr)
							# if time_diff.hour >= 1 :
							# 	if time_diff.minute <= 29:
							# 		ot_hours = time(time_diff.hour,0,0)
							# 	else:
							# 		ot_hours = time(time_diff.hour,30,0)
							# elif time_diff.hour == 0 :
							# 	if time_diff.minute <= 29:
							# 		ot_hours = time(0,0,0)
							# 	else:
							# 		ot_hours = time(time_diff.hour,30,0)
							# ftr = [3600,60,1]
							# hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
							# ot_hr = round(hr/3600,1)
							# frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',ot_hours)
							# frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hr)
						else:
							frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
							frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
							frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
							frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")
					else:
						frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
						frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
						frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
						frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")
				else:
					# time_in_standard_format = time_diff_in_timedelta(out_time,in_time)
					# duration = datetime.strptime(str(time_in_standard_format), "%H:%M:%S")
					# total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
					# rounded_number = round(total_seconds, 3)
					# time_diff = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
					# frappe.db.set_value('Attendance',att.name,'custom_extra_hours',rounded_number)
					# frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',time_in_standard_format)
					if wh < 24.0:
						time_in_standard_format = time_diff_in_timedelta(in_time,out_time)
						duration = datetime.strptime(str(time_in_standard_format), "%H:%M:%S")
						total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
						rounded_number = round(total_seconds, 3)
						time_diff = datetime.strptime(str(time_in_standard_format), '%H:%M:%S').time()
						frappe.db.set_value('Attendance',att.name,'custom_extra_hours',rounded_number)
						frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',time_in_standard_format)
					else:
						wh = 24.0
						duration = datetime.strptime(str("23:59:59"), "%H:%M:%S")
						total_seconds = (duration.hour * 3600 + duration.minute * 60 + duration.second)/3600
						rounded_number = round(total_seconds, 3)
						time_diff = datetime.strptime(str("23:59:59"), '%H:%M:%S').time()
						frappe.db.set_value('Attendance',att.name,'custom_extra_hours',rounded_number)
						frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"23:59:59")
					if time_diff.hour >= 1 :
						if time_diff.minute <= 29:
							ot_hours = time(time_diff.hour,0,0)
						else:
							ot_hours = time(time_diff.hour,30,0)
					elif time_diff.hour == 0 :
						if time_diff.minute <= 29:
							ot_hours = time(0,0,0)
						else:
							ot_hours = time(time_diff.hour,30,0)
					ftr = [3600,60,1]
					hr = sum([a*b for a,b in zip(ftr, map(int,str(ot_hours).split(':')))])
					ot_hr = round(hr/3600,1)
					frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',ot_hours)
					frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hr)
			else:
				frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
				frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
				frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
				frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
				frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
				frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")
		else:
			frappe.db.set_value('Attendance',att.name,'custom_total_working_hours',"00:00:00")
			frappe.db.set_value('Attendance',att.name,'working_hours',"0.0")
			frappe.db.set_value('Attendance',att.name,'custom_extra_hours',"0.0")
			frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',"00:00:00")
			frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',"00:00:00")
			frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',"0.0")

def submit_present_att_with_employee(employee,from_date,to_date):
	attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':0,'employee':employee},['*'],order_by = 'attendance_date')
	for att in attendance:
		if att.attendance_date == getdate(today()) and att.status == 'Present' and att.early_exit == 0:
			frappe.db.set_value('Attendance', att.name, 'docstatus', 1)
		elif att.attendance_date > getdate(today()) and att.status == 'Present':
			frappe.db.set_value('Attendance', att.name, 'docstatus', 1)

def mark_late_early_with_employee(employee,from_date,to_date):
	attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'employee':employee,'status':("!=","On Leave")},['*'],order_by = 'attendance_date')
	for att in attendance:
		hh = check_holiday(att.attendance_date, att.employee)
		if not hh:
			if att.status not in ['On Leave', 'Work From Home']:
				if att.shift and att.in_time:
					shift_time_start = frappe.get_value("Shift Type", {'name': att.shift}, ["start_time"])
					shift_start_time = datetime.strptime(str(shift_time_start), '%H:%M:%S').time()
					start_time = dt.datetime.combine(att.attendance_date, shift_start_time)
					start_time += dt.timedelta(minutes=5)
					late_time = dt.datetime.combine(att.attendance_date, shift_start_time)
					late_time += dt.timedelta(minutes=120)                   
					# if att.in_time > late_time:
					#     frappe.db.set_value('Attendance', att.name, 'status', "Half Day")
					#     frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
					#     frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time -start_time )
					if att.in_time >start_time:
						frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
						frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time -start_time )
					else:
						frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
						frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")

				if att.shift and att.out_time:
					shift_time_end = frappe.get_value("Shift Type", {'name': att.shift}, ["end_time"])
					shift_end_time = datetime.strptime(str(shift_time_end), '%H:%M:%S').time()
					end_time = dt.datetime.combine(att.attendance_date, shift_end_time)

					if att.out_time < end_time:
						frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
						frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', end_time - att.out_time)
					else:
						frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
						frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
			else:
				frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
				frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
				frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
				frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")
		else:
			frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
			frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
			frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
			frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', "00:00:00")

def check_ot_with_employee(employee,from_date,to_date):
	attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'employee':employee,'status':("!=","On Leave")},['*'],order_by = 'attendance_date')
	for att in attendance:
		if att.custom_overtime_hours > 0 :
			if frappe.db.exists("OT Planning List",{'employee':att.employee,'ot_date':att.attendance_date,'docstatus':1}):
				ot_hours = frappe.get_value("OT Planning List",{'employee':att.employee,'ot_date':att.attendance_date,'docstatus':1})
				if att.custom_overtime_hours > ot_hours :
					total_seconds = int(ot_hours * 3600)
					hours = total_seconds // 3600
					minutes = (total_seconds % 3600) // 60
					seconds = total_seconds % 60
					frappe.db.set_value('Attendance',att.name,'custom_total_overtime_hours',f"{hours:02}:{minutes:02}:{seconds:02}")
					frappe.db.set_value('Attendance',att.name,'custom_overtime_hours',ot_hours)

@frappe.whitelist()
def get_urc_to_ec(date,employee):
	if employee == '':
		urc = frappe.db.sql("""select * from `tabUnregistered Employee Checkin` where date(time) = '%s' """%(date),as_dict=True)
	else:
		urc = frappe.db.sql("""select * from `tabUnregistered Employee Checkin` where date(time) = '%s' and employee = '%s' """%(date,employee),as_dict=True)
	for uc in urc:
		employee = uc.employee
		time = uc.time
		dev = uc.location__device_id
		typ = uc.log_type
		nam = uc.name
		if frappe.db.exists('Employee',{'name':employee}):
			if not frappe.db.exists('Employee Checkin',{'employee':employee,"time":time}):
				frappe.errprint(employee)
				ec = frappe.new_doc('Employee Checkin')
				ec.employee = employee
				ec.time = time
				ec.device_id = dev
				ec.log_type = typ
				ec.save(ignore_permissions=True)
				frappe.db.commit()
				frappe.errprint("Created")
				attendance = frappe.db.sql(""" delete from `tabUnregistered Employee Checkin` where name = '%s' """%(nam))      
	return "OK"

def mark_attendance_from_checkin_new(employee,time,log_type):
	att_date = time.date()
	att_time = time.time()
	if log_type == 'IN':
		print("In time fetched")
		# attendance_name = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':1,'status':"On Leave"})
		# if attendance_name:
		# 	attendance = frappe.get_doc("Attendance", attendance_name)
		# 	attendance.flags.ignore_permissions = True
		# 	leave = frappe.get_doc("Leave Application", attendance.leave_application)
		# 	attendance.flags.ignore_permissions = True
		# 	if leave.half_day == 0:
		# 		attendance.cancel()
		# 		leave.cancel()
		att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
		checkins = frappe.db.sql(""" select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' and device_id != "Canteen" order by time ASC"""%(employee,att_date),as_dict=True)
		if not att:
			print("HI")
			att = frappe.new_doc("Attendance")
			att.employee = employee
			att.attendance_date = att_date
			att.status = 'Absent'
			att.in_time = checkins[0].time
			att.shift = get_actual_shift_start(employee ,get_time(checkins[0].time))
			att.custom_total_working_hours = "00:00:00"
			att.custom_working_hours = "0.0"
			att.custom_extra_hours = "0.0"
			att.custom_total_extra_hours = "00:00:00"
			att.custom_total_overtime_hours = "00:00:00"
			att.custom_overtime_hours = "0.0"
			att.custom_early_out_time = "00:00:00"
			att.custom_late_entry_time = "00:00:00"
			att.custom_from_time = "00:00:00"
			att.custom_to_time = "00:00:00"
			att.save(ignore_permissions=True)
			frappe.db.commit()
			for c in checkins:
				frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
				frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
		else:
			if frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':0}):
				print("Hi")
				att = frappe.get_doc("Attendance",att)
				print("attcreated")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				att.in_time = checkins[0].time
				att.shift = get_actual_shift_start(employee ,get_time(checkins[0].time))
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				print("attcreated2")
				att.save(ignore_permissions=True)
				frappe.db.commit()
				for c in checkins:
					frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
	if log_type == 'OUT':
		frappe.errprint("Helloooo")
		today_att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date,'docstatus':('!=',2)})
		if today_att:
			today_att = frappe.get_doc("Attendance",today_att)
			if today_att.in_time:
				frappe.errprint("Checkin in Att")
				checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,today_att.in_time),as_dict=True)
				today_out=frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) > '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,today_att.in_time),as_dict=True)
				# frappe.errprint(today_out)
				for t in today_out:
					frappe.errprint(t.name)
			else:
				max_out_checkin = datetime.strptime('12:30:00','%H:%M:%S').time()
				today_out = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) > '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,max_out_checkin),as_dict=True)
				checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,max_out_checkin),as_dict=True)
		else:
			today_out=''
			max_out_checkin = datetime.strptime('12:30:00','%H:%M:%S').time()
			checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,att_date,max_out_checkin),as_dict=True)
		if checkins and not today_out:
			frappe.errprint("shift details")
			yesterday = add_days(att_date,-1)
			att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':yesterday,'docstatus':('!=',2)})
			if att:
				frappe.errprint("shift details2")
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0 or att.docstatus == 1:
					frappe.errprint("shift details3")
					frappe.errprint(att.attendance_date)
					if not att.shift:
						frappe.errprint("shift details1")
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							frappe.errprint(get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
							frappe.db.commit()	
						else:
							if checkins:
								frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
								frappe.errprint(get_actual_shift(checkins[0].employee,get_time(checkins[-1].time)))
								frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
								frappe.db.commit()
					else:
						if len(checkins) > 0:
							frappe.errprint("Checkin present 1")
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.errprint("Checkin present 2")
								frappe.errprint(c.name)
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							if checkins:
								frappe.errprint("Checkin present")
								frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				if len(checkins) > 0:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)			
					for c in checkins:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
					frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att	
		if today_out and not checkins:
			frappe.errprint("today_out and not checkins")
			checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' and device_id != "Canteen" order by time ASC"""%(employee,att_date),as_dict=True)
			att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date,'docstatus':('!=',2)})
			if att:
				frappe.errprint("Hello 1")
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0  or att.docstatus == 1:
					if att.shift=='':
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
							frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					else:
						if len(checkins) > 0:
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
							frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				if len(checkins) > 0:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[-1].employee,get_time(checkins[-1].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[-1].time)			
					for c in checkins:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(checkins[0].employee,get_time(checkins[0].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",checkins[0].time)
					frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att
		if checkins and today_out:
			frappe.errprint("Both condition Passed")
			yesterday = add_days(att_date, -1)
			prev_att = frappe.db.exists("Attendance", {'employee': employee, 'attendance_date': yesterday, 'docstatus': ('!=', 2)})
			if prev_att:
				frappe.errprint("Previous day attendance")
				prev_att = frappe.get_doc("Attendance", prev_att)
				if prev_att.docstatus == 0 or prev_att.docstatus == 1:
					if prev_att.shift=='':
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(today_out[-1].employee,get_time(today_out[-1].time)))
							frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", prev_att.name)
						else:
							if checkins:
								frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(today_out[0].employee,get_time(today_out[0].time)))
								frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[0].time)
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", prev_att.name)
					else:
						if len(checkins) > 0:
							frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(today_out[-1].employee,get_time(today_out[-1].time)))
							frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[-1].time)
							for c in checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", prev_att.name)
						else:
							if checkins:
								frappe.db.set_value('Attendance',prev_att.name, 'shift',get_actual_shift(today_out[0].employee,get_time(today_out[0].time)))
								frappe.db.set_value("Attendance",prev_att.name, "out_time",checkins[0].time)
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", prev_att.name)



			att = frappe.db.exists("Attendance", {'employee': employee, 'attendance_date': att_date, 'docstatus': ('!=', 2)})
			if att:
				frappe.errprint("current day attendance")
				att = frappe.get_doc("Attendance", att)
				if att.docstatus == 0 or att.docstatus == 1:
					if att.shift=='':
						if len(today_out) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(today_out[-1].employee,get_time(today_out[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[-1].time)
							for c in today_out:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(today_out[0].employee,get_time(today_out[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[0].time)
							frappe.db.set_value('Employee Checkin',today_out[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",today_out[0].name, "attendance", att.name)
					else:
						if len(today_out) > 0:
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[-1].time)
							for c in today_out:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value("Attendance",att.name, "out_time",today_out[0].time)
							frappe.db.set_value('Employee Checkin',today_out[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",today_out[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				frappe.errprint("No Attendance")
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.status = 'Absent'
				if len(today_out) > 0:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(today_out[-1].employee,get_time(today_out[-1].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",today_out[-1].time)			
					for c in today_out:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(today_out[0].employee,get_time(today_out[0].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",today_out[0].time)
					frappe.db.set_value('Employee Checkin',today_out[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",today_out[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att
		else:
			frappe.errprint("Last else")
			yesterday = add_days(att_date,1)
			next_att = frappe.db.get_value("Attendance",{'employee':employee,'attendance_date':yesterday,'docstatus':('!=',2)},['in_time'])
			next_checkins = frappe.db.sql("""select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' and TIME(time) < '%s' and device_id != "Canteen" order by time ASC """%(employee,yesterday,next_att),as_dict=True)
			att = frappe.db.exists("Attendance", {'employee': employee, 'attendance_date': att_date, 'docstatus': ('!=', 2)})
			if att:
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0 or att.docstatus == 1:
					if att.shift == '':
						if len(next_checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(next_checkins[-1].employee,get_time(next_checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[-1].time)
							for c in next_checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[0].employee,get_time(next_checkins[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[0].time)
							frappe.db.set_value('Employee Checkin',next_checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",next_checkins[0].name, "attendance", att.name)
					else:
						if len(next_checkins) > 0:
							frappe.db.set_value('Attendance',att.name, 'shift',get_actual_shift(next_checkins[-1].employee,get_time(next_checkins[-1].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[-1].time)
							for c in next_checkins:
								frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
						else:
							frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[0].employee,get_time(next_checkins[0].time)))
							frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[0].time)
							frappe.db.set_value('Employee Checkin',next_checkins[0].name,'skip_auto_attendance','1')
							frappe.db.set_value("Employee Checkin",next_checkins[0].name, "attendance", att.name)
					frappe.db.commit()
					return att
				else:
					return att
			else:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = yesterday
				att.status = 'Absent'
				if len(next_checkins) > 0:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[-1].employee,get_time(next_checkins[-1].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[-1].time)			
					for c in next_checkins:
						frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
						frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				else:
					frappe.db.set_value('Attendance',att.name,'shift',get_actual_shift(next_checkins[0].employee,get_time(next_checkins[0].time)))
					frappe.db.set_value("Attendance",att.name, "out_time",next_checkins[0].time)
					frappe.db.set_value('Employee Checkin',next_checkins[0].name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",next_checkins[0].name, "attendance", att.name)
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.custom_early_out_time = "00:00:00"
				att.custom_late_entry_time = "00:00:00"
				att.custom_from_time = "00:00:00"
				att.custom_to_time = "00:00:00"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				return att
		

					

			