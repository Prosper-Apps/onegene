# Copyright (c) 2022, teampro and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from email import message
import re
from frappe import _
import frappe
from frappe.model.document import Document
from datetime import date, timedelta, datetime,time
from frappe.utils import (getdate, cint, add_months, date_diff, add_days,

	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime,today, format_date)
import pandas as pd
import math
from frappe.utils import add_months, cint, flt, getdate, time_diff_in_hours
import datetime as dt
from datetime import datetime, timedelta

class AttendanceRegularize(Document):

	def on_submit(self):
		if self.corrected_shift or self.corrected_in or self.corrected_out :
			att = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':self.attendance_date})
			frappe.db.set_value('Attendance', att, 'shift', self.corrected_shift)
			frappe.db.set_value('Attendance', att, 'in_time', self.corrected_in)
			frappe.db.set_value('Attendance', att, 'out_time', self.corrected_out)
			attendance = frappe.db.get_all('Attendance',{'name':att},['*'])
			for att in attendance:
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
						elif wh >= 4 and wh < 6:
							frappe.db.set_value('Attendance',att.name,'status','Half Day')
						elif wh >= 6:
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
				hh = check_holiday(att.attendance_date,att.employee)
				if not hh:
					if att.shift and att.in_time:
						shift_time = frappe.get_value(
							"Shift Type", {'name': att.shift}, ["start_time"])
						shift_start_time = datetime.strptime(
							str(shift_time), '%H:%M:%S').time()
						start_time = dt.datetime.combine(att.attendance_date,shift_start_time)
						
						if att.in_time > datetime.combine(att.attendance_date, shift_start_time):
							frappe.db.set_value('Attendance', att.name, 'late_entry', 1)
							frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', att.in_time - start_time)
						else:
							frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
							frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
					if att.shift and att.out_time:
						shift_time = frappe.get_value(
							"Shift Type", {'name': att.shift}, ["end_time"])
						shift_end_time = datetime.strptime(
							str(shift_time), '%H:%M:%S').time()
						end_time = dt.datetime.combine(att.attendance_date,shift_end_time)
						if att.out_time < datetime.combine(att.attendance_date, shift_end_time):
							frappe.db.set_value('Attendance', att.name, 'early_exit', 1)
							frappe.db.set_value('Attendance', att.name, 'custom_early_out_time', att.out_time - end_time)
						else:
							frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
							frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',"00:00:00")
				else:
					frappe.db.set_value('Attendance', att.name, 'late_entry', 0)
					frappe.db.set_value('Attendance', att.name, 'custom_late_entry_time', "00:00:00")
					frappe.db.set_value('Attendance', att.name, 'early_exit', 0)
					frappe.db.set_value('Attendance', att.name, 'custom_early_out_time',  "00:00:00")
			frappe.db.set_value('Attendance', att.name, 'custom_regularize_marked', 1)
			frappe.db.set_value('Attendance', att.name, 'custom_attendance_regularize',self.name)
	

				
	def on_cancel(self):
		att = frappe.db.exists('Attendance',{'employee':self.employee,'attendance_date':self.attendance_date})
		if att:
			att_reg = frappe.db.get_value('Attendance',{'name':att},['custom_attendance_regularize'])
			if att_reg == self.name:
				frappe.db.set_value('Attendance', att, 'custom_total_working_hours',"00:00:00")
				frappe.db.set_value('Attendance', att, 'working_hours',"0.0")
				frappe.db.set_value('Attendance', att, 'custom_extra_hours',"0.0")
				frappe.db.set_value('Attendance', att, 'custom_total_extra_hours',"00:00:00")
				frappe.db.set_value('Attendance', att, 'custom_total_overtime_hours',"00:00:00")
				frappe.db.set_value('Attendance', att, 'custom_overtime_hours',"0.0")
				frappe.db.set_value('Attendance', att, 'shift', '')
				frappe.db.set_value('Attendance', att, 'in_time',"00:00:00")
				frappe.db.set_value('Attendance', att, 'out_time',"00:00:00")
				frappe.db.set_value('Attendance', att, 'custom_attendance_regularize', '')
				frappe.db.set_value('Attendance', att, 'late_entry', 0)
				frappe.db.set_value('Attendance', att, 'custom_late_entry_time', "00:00:00")
				frappe.db.set_value('Attendance', att, 'early_exit', 0)
				frappe.db.set_value('Attendance', att, 'custom_early_out_time',  "00:00:00")

@frappe.whitelist()
def get_assigned_shift_details(emp,att_date):
	datalist = []
	data = {}
	shift_type = frappe.get_value("Employee",{'name':emp},['shift'])
	if shift_type == "Multiple":
		if frappe.db.exists('Shift Assignment',{'start_date':att_date,'employee':emp,'docstatus': 1}):
			assigned_shift = frappe.db.get_value('Shift Assignment',{'start_date':att_date,'employee':emp,'docstatus': 1},['shift_type'])
		else:
			assigned_shift = ' '
	else:
		assigned_shift = frappe.get_value("Employee",{'name':emp},['default_shift'])
	if assigned_shift != ' ':
		shift_in_time = frappe.db.get_value('Shift Type',{'name':assigned_shift},['start_time'])
		shift_out_time = frappe.db.get_value('Shift Type',{'name':assigned_shift},['end_time'])
	else:
		shift_in_time = ' '
		shift_out_time = ' '
	if frappe.db.exists('Attendance',{'employee':emp,'attendance_date':att_date}):
		if frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date},['in_time']):
			first_in_time = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date},['in_time'])
		else:
			first_in_time = ' ' 
		if frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date},['out_time']):
			last_out_time = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date},['out_time'])  
		else:
			last_out_time = ' '
		if frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date},['shift']):
			attendance_shift = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date},['shift'])   
		else:
			attendance_shift = ' '
		attendance_marked = frappe.db.get_value('Attendance',{'employee':emp,'attendance_date':att_date},['name'])
		data.update({
			'assigned_shift':assigned_shift or ' ',
			'shift_in_time':shift_in_time or '00:00:00',
			'shift_out_time':shift_out_time or '00:00:00',
			'attendance_shift':attendance_shift or ' ',
			'first_in_time':first_in_time,
			'last_out_time':last_out_time,
			'attendance_marked':attendance_marked 
		})
		datalist.append(data.copy())
		return datalist	 
	else:
		frappe.throw(_("Attendance not Marked"))

@frappe.whitelist()
def time_diff_in_timedelta(time1, time2):
		return time2 - time1

@frappe.whitelist()
def check_holiday(date,emp):
	holiday_list = frappe.db.get_value('Employee',{'name':emp},'holiday_list')
	holiday = frappe.db.sql("""select `tabHoliday`.holiday_date,`tabHoliday`.weekly_off from `tabHoliday List`
	left join `tabHoliday` on `tabHoliday`.parent = `tabHoliday List`.name where `tabHoliday List`.name = '%s' and holiday_date = '%s' """%(holiday_list,date),as_dict=True)
	doj= frappe.db.get_value("Employee",{'name':emp},"date_of_joining")
	if holiday :
		if doj < holiday[0].holiday_date:
			if holiday[0].weekly_off == 1:
				return "WW"     
			else:
				return "HH"



	



