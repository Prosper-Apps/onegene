from __future__ import unicode_literals
import frappe
from frappe.utils import today,flt,cint, getdate, get_datetime
from datetime import timedelta,datetime
from frappe.utils import (
    add_days,
    ceil,
    cint,
    comma_and,
    flt,
    get_link_to_form,
    getdate,
    now_datetime,
    datetime,get_first_day,get_last_day,
    nowdate,
    today,
)

no_cache = 1

def get_context(context):
	context.bday_data = birthday_list()

@frappe.whitelist()
@frappe.whitelist()
def birthday_list():
    from datetime import datetime
    today_date = datetime.now().date()
    
    employees = frappe.get_all("Employee", {"status": "Active"}, ["*"])
    data = []
    has_birthday = False
    
    for employee in employees:
        emp_dob = employee.date_of_birth
        if emp_dob and emp_dob.month == today_date.month and emp_dob.day == today_date.day:
            image = frappe.db.get_value("File", {"attached_to_name": employee.name, "attached_to_doctype": 'Employee'}, ["file_url"])
            has_birthday = True
            row = {
                "ID": employee.name,
                "Name": employee.employee_name,
                "Employee Category": employee.employee_category,
                "Department": employee.department,
                "Designation": employee.designation
            }
            if image:
                row["Default Image URL"] = 'https://erp.onegeneindia.in/' + image
            else:
                image2 = frappe.db.get_value("File", {"name": '63881d8e44'}, ["file_url"])
                row["Default Image URL"] = 'https://erp.onegeneindia.in/' + image2
            
            data.append(row)
    
    if has_birthday:
        return data
    else:
        return "No Birthdays Today"
