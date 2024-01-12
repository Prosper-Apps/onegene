from __future__ import print_function
from pickle import TRUE
from time import strptime
from traceback import print_tb
import frappe
from frappe.utils.data import ceil, get_time, get_year_start
# import pandas as pd
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

@frappe.whitelist()
def cron_job1():
	job = frappe.db.exists('Scheduled Job Type', 'mark_att')
	if not job:
		sjt = frappe.new_doc("Scheduled Job Type")  
		sjt.update({
			"method" : 'onegene.mark_attendance.mark_att',
			"frequency" : 'Cron',
			"cron_format" : '*/20 * * * *'
		})
		sjt.save(ignore_permissions=True)

@frappe.whitelist()
def mark_att1():
	# checkins = frappe.db.sql("""update `tabEmployee Checkin` set skip_auto_attendance = 0 """,as_dict=1)
	# print(checkins)
	# checkins = frappe.db.sql("""update `tabEmployee Checkin` set attendance = 0 """,as_dict=1)
	# print(checkins)
	checkins = frappe.db.sql("""update `tabAttendance` set docstatus = 1 where attendance_date between "2023-12-01" and "2023-12-31" and status = "Present" """,as_dict=1)
	print(checkins)

@frappe.whitelist()
def m_mark_wh_ot():
	from_date = '2023-11-01'
	to_date = '2023-11-30'
	mark_wh_ot(from_date,to_date)
	mark_absent(from_date,to_date) 



@frappe.whitelist()
def mark_att():
	from_date = '2023-11-01'
	to_date = '2023-11-30'
	# from_date = add_days(today(),-40)  
	# to_date = today()
	dates = get_dates(from_date,to_date)
	for date in dates:
		from_date = add_days(date,0)
		to_date = date
		checkins = frappe.db.sql(
			"""select * from `tabEmployee Checkin` where date(time) between '%s' and '%s' order by time ASC """%(from_date,to_date),as_dict=1)
		for c in checkins:
			employee = frappe.db.exists('Employee',{'status':'Active','date_of_joining':['<=',from_date],'name':c.employee})
			if employee:  
				print(c.name)
				mark_attendance_from_checkin(c.name,c.employee,c.time,c.log_type)
	# mark_absent(from_date,to_date) 
	# mark_wh_ot(from_date,to_date)                             

def mark_attendance_from_checkin(checkin,employee,time,log_type):
	att_date = time.date()
	att_time = time.time()
	shift = ''
	if log_type == 'IN':
		shift1 = frappe.db.get_value('Shift Type',{'name':'1'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift2 = frappe.db.get_value('Shift Type',{'name':'2'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift3 = frappe.db.get_value('Shift Type',{'name':'3'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift4 = frappe.db.get_value('Shift Type',{'name':'4'},['custom_checkin_start_time','custom_checkin_end_time'])
		shift5 = frappe.db.get_value('Shift Type',{'name':'5'},['custom_checkin_start_time','custom_checkin_end_time'])
		shiftg = frappe.db.get_value('Shift Type',{'name':'G'},['custom_checkin_start_time','custom_checkin_end_time'])
		print("HI")
		print(att_time)
		att_time_seconds = att_time.hour * 3600 + att_time.minute * 60 + att_time.second
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
		att = frappe.db.exists('Attendance',{"employee":employee,'attendance_date':att_date,'docstatus':['!=','2']})   
		checkins = frappe.db.sql(""" select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'IN' and date(time) = '%s' order by time ASC"""%(employee,att_date),as_dict=True)
		if not att and checkins:
			att = frappe.new_doc("Attendance")
			att.employee = employee
			att.attendance_date = att_date
			att.shift = shift
			att.status = 'Absent'
			if len(checkins) > 0:
				att.in_time = checkins[-1].time
			else:
				att.in_time = checkins[0].time
			att.custom_total_working_hours = "00:00:00"
			att.custom_working_hours = "0.0"
			att.custom_extra_hours = "0.0"
			att.custom_total_extra_hours = "00:00:00"
			att.custom_total_overtime_hours = "00:00:00"
			att.custom_overtime_hours = "0.0"
			att.save(ignore_permissions=True)
			frappe.db.commit()
			for c in checkins:
				frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
				frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
			return att  
		else:
			att = frappe.get_doc("Attendance",att)
			print(att.name)
			if att.docstatus == 0:
				att.employee = employee
				att.attendance_date = att_date
				att.shift = shift
				att.status = 'Absent'
				if len(checkins) > 0:
					att.in_time = checkins[-1].time
				else:
					att.in_time = checkins[0].time
				att.custom_total_working_hours = "00:00:00"
				att.custom_working_hours = "0.0"
				att.custom_extra_hours = "0.0"
				att.custom_total_extra_hours = "00:00:00"
				att.custom_total_overtime_hours = "00:00:00"
				att.custom_overtime_hours = "0.0"
				att.save(ignore_permissions=True)
				frappe.db.commit()
				for c in checkins:
					frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				return att 
	if log_type == 'OUT':
		max_out = datetime.strptime('10:30','%H:%M').time()
		if att_time < max_out:
			yesterday = add_days(att_date,-1)
			checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee = '%s' and log_type = 'OUT' and date(time) = '%s' order by time ASC "%(employee,att_date),as_dict=True)
			att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':yesterday})
			if att:
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0:
					if not att.out_time:
						if att.shift == '':
							if len(checkins) > 0:
								att.shift = get_actual_shift(get_time(checkins[-1].time))
								att.out_time = checkins[-1].time
								for c in checkins:
									frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
									frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
							else:
								att.shift = get_actual_shift(get_time(checkins[0].time))
								att.out_time = checkins[0].time
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
						else:
							if len(checkins) > 0:
								att.out_time = checkins[-1].time
								for c in checkins:
									frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
									frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
							else:
								att.out_time = checkins[0].time
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
						att.status = 'Absent'    
						att.save(ignore_permissions=True)
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
					print(checkins[-1])
					att.out_time = checkins[-1].time
					att.shift = get_actual_shift(get_time(checkins[-1].time))
				else:
					att.out_time = checkins[0].time
					att.shift = get_actual_shift(get_time(checkins[0].time))
				att.save(ignore_permissions=True)
				frappe.db.commit()
				for c in checkins:
					frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				return att	
		else:
			checkins = frappe.db.sql("select * from `tabEmployee Checkin` where employee ='%s' and log_type = 'OUT' and date(time) = '%s' order by time ASC"%(employee,att_date),as_dict=True)
			att = frappe.db.exists("Attendance",{'employee':employee,'attendance_date':att_date})
			if att:
				att = frappe.get_doc("Attendance",att)
				if att.docstatus == 0:
					if not att.out_time:
						if att.shift == '':
							if len(checkins) > 0:
								att.shift = get_actual_shift(get_time(checkins[-1].time))
								att.out_time = checkins[-1].time
								for c in checkins:
									frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
									frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
							else:
								att.shift = get_actual_shift(get_time(checkins[0].time))
								att.out_time = checkins[0].time
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
						else:
							if len(checkins) > 0:
								att.out_time = checkins[-1].time
								for c in checkins:
									frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
									frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
							else:
								att.out_time = checkins[0].time
								frappe.db.set_value('Employee Checkin',checkins[0].name,'skip_auto_attendance','1')
								frappe.db.set_value("Employee Checkin",checkins[0].name, "attendance", att.name)
						att.status = 'Absent'    
						att.save(ignore_permissions=True)
						frappe.db.commit()
						return att
					else:
						return att
			else:
				att = frappe.new_doc("Attendance")
				att.employee = employee
				att.attendance_date = att_date
				att.shift = shift
				att.status = 'Absent'
				if len(checkins) > 0:
					att.shift = get_actual_shift(get_time(checkins[-1].time))
					att.out_time = checkins[-1].time
				else:
					att.shift = get_actual_shift(get_time(checkins[0].time))
					att.out_time = checkins[0].time
				att.save(ignore_permissions=True)
				frappe.db.commit()
				for c in checkins:
					frappe.db.set_value('Employee Checkin',c.name,'skip_auto_attendance','1')
					frappe.db.set_value("Employee Checkin",c.name, "attendance", att.name)
				return att  

def get_actual_shift(get_shift_time):
	print(get_shift_time)
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
					att.insert(ignore_permissions=True)
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
				status = "WW"     
			else:
				status = "HH"


def mark_wh_ot(from_date,to_date):
	attendance = frappe.db.get_all('Attendance',{'attendance_date':('between',(from_date,to_date)),'docstatus':('!=','2')},['*'])
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
						extra_hours_float = wh
					else:
						extra_hours_float = 23.99
					days = time_in_standard_format_timedelta.day
					seconds = time_in_standard_format_timedelta.second
					hours, remainder = divmod(seconds, 3600)
					minutes, seconds = divmod(remainder, 60)
					formatted_time = "{:02}:{:02}:{:02}".format(hours, minutes, seconds)
					time_diff = datetime.strptime(str(formatted_time), '%H:%M:%S').time()
					frappe.db.set_value('Attendance',att.name,'custom_extra_hours',extra_hours_float)
					frappe.db.set_value('Attendance',att.name,'custom_total_extra_hours',time_diff)
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

def mark_att_present(from_date, to_date):
	attendance = frappe.db.get_all('Attendance', {'attendance_date': ('between', (from_date, to_date)),'docstatus': 0}, ['*'])
	for att in attendance:
		if att.status == 'Present':
			frappe.db.set_value('Attendance', att.name, 'docstatus', 1)

import datetime as dt
from datetime import datetime, timedelta
def mark_late_early(from_date, to_date):
	attendance = frappe.db.get_all(
		'Attendance', {'attendance_date': ('between', (from_date, to_date))}, ['*'])

	for att in attendance:
		print(att.name)
		if att.shift and att.in_time:
			shift_time = frappe.get_value(
				"Shift Type", {'name': att.shift}, ["start_time"])
			shift_start_time = datetime.strptime(
				str(shift_time), '%H:%M:%S').time()
			start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
			
			if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
				frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
				frappe.db.set_value('Attendance', att.name,
									'custom_late_entry_time', att.in_time - start_time)

		if att.shift and att.out_time:
			shift_time = frappe.get_value(
				"Shift Type", {'name': att.shift}, ["end_time"])
			shift_end_time = datetime.strptime(
				str(shift_time), '%H:%M:%S').time()
			end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
			if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
				frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
				frappe.db.set_value('Attendance', att.name,
									'custom_early_out_time', att.out_time - end_time)



@frappe.whitelist()
def update_checkin_att():
	checkin = frappe.db.sql("""delete from `tabAttendance` where attendance_date between "2023-01-01" and "2023-09-30"   """,as_dict = True)
	print(checkin)
	# print("JHI")
	# checkin = frappe.db.sql("""update `tabEmployee Checkin` set attendance = ''  """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabEmployee Checkin` set skip_auto_attendance = 0  """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set shift = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set in_time = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set out_time = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set docstatus = 0 where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set status = "Absent" where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set late_entry = 0 where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set custom_late_entry_time = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set early_exit = 0 where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set custom_early_out_time = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set custom_total_working_hours = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set working_hours = 0 where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set custom_extra_hours = 0 where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set custom_total_extra_hours = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set custom_total_overtime_hours = NULL where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)
	# checkin = frappe.db.sql("""update `tabAttendance` set custom_overtime_hours = 0 where attendance_date between "2023-12-01" and "2024-01-10" """,as_dict = True)
	# print(checkin)

