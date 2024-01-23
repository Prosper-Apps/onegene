import frappe
import requests
from datetime import date
import erpnext
from frappe.model.naming import parse_naming_series
import re
import json
from frappe import throw,_
from frappe.utils import flt
from frappe.utils import (
	add_days,
	ceil,
	cint,
	comma_and,
	flt,
	 formatdate,
	get_link_to_form,
	getdate,
	now_datetime,
	datetime,get_first_day,get_last_day,
	nowdate,
	today,
)

@frappe.whitelist()
def return_sales_order_qty(item,posting_date):
	item_list = json.loads(item)
	sample = []
	for it in item_list:
		sale = frappe.get_doc('Sales Order',it['sales_order'])
		for i in sale.custom_schedule_table:
			if i.item_code == it['item_code']:
				from datetime import datetime
				current_date = datetime.strptime(str(posting_date), '%Y-%m-%d').date()
				date_datetime = datetime.strptime(str(i.schedule_date), '%Y-%m-%d').date()
				if date_datetime.month == current_date.month and date_datetime.year == current_date.year:                
					sample.append(frappe._dict({'name':i.name,'item_code':it['item_code'],'qty':i.pending_qty}))
	return sample

@frappe.whitelist()
def update_order_schedule_table(doc,method):
	for i in doc.items:
		sale = frappe.get_doc("Sales Order",i.against_sales_order)
		for k in sale.custom_schedule_table:
			if k.name == i.custom_against_order_schedule:
				qty = k.delivery_qty + i.qty
				pending_qty = k.pending_qty - i.qty
				del_amount = qty * i.rate
				pen_amount = pending_qty * i.rate
				frappe.db.set_value("Sales Order Schedule",i.custom_against_order_schedule,'delivery_qty',qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'delivered_qty',qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'delivered_amount',del_amount)

				frappe.db.set_value("Sales Order Schedule",i.custom_against_order_schedule,'pending_qty',pending_qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'pending_qty',pending_qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'pending_amount',pen_amount)

@frappe.whitelist()
def revert_order_schedule_table(doc,method):
	for i in doc.items:
		sale = frappe.get_doc("Sales Order",i.against_sales_order)
		for k in sale.custom_schedule_table:
			if k.name == i.custom_against_order_schedule:
				qty = k.delivery_qty - i.qty
				pending_qty = k.pending_qty + i.qty
				del_amount = qty * i.rate
				pen_amount = pending_qty * i.rate
				frappe.db.set_value("Sales Order Schedule",i.custom_against_order_schedule,'delivery_qty',qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'delivered_qty',qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'delivered_amount',del_amount)

				frappe.db.set_value("Sales Order Schedule",i.custom_against_order_schedule,'pending_qty',pending_qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'pending_qty',pending_qty)
				frappe.db.set_value("Order Schedule",{"child_name":i.custom_against_order_schedule},'pending_amount',pen_amount)
				

@frappe.whitelist()
def open_qty_so(doc,method):
	so = frappe.get_doc("Sales Order",doc.sales_order_number)
	if so.customer_order_type == "Open":
		order = frappe.get_all("Order Schedule",{"sales_order_number":doc.sales_order_number,"customer_code":doc.customer_code,"item_code":doc.item_code},["*"])
		existing_order_schedules = {row.order_schedule for row in so.custom_schedule_table}
		for i in order:
			order_schedule_name = i.name
			if order_schedule_name not in existing_order_schedules:
				so.append("custom_schedule_table", {
						"item_code": i.item_code,
						"schedule_date": i.schedule_date,
						"schedule_qty": i.qty,
						"order_schedule":order_schedule_name,
						"pending_qty":i.pending_qty
					})
		so.save()
		
	
@frappe.whitelist()
def update_child_item(doc,method):
	if doc.customer_order_type == "Open":
		if doc.custom_schedule_table:
			for i in doc.custom_schedule_table:
				order = frappe.get_doc("Order Schedule",i.order_schedule)
				frappe.db.set_value("Order Schedule",i.order_schedule,"child_name",i.name)


@frappe.whitelist()
def update_order_sch_qty(doc,method):
	sale = frappe.get_doc("Sales Order",doc.sales_order_number)
	for i in sale.custom_schedule_table:
		if i.order_schedule == doc.name:
			qty = doc.qty
			frappe.db.set_value("Sales Order Schedule",i.name,'schedule_qty',qty)
			frappe.db.set_value("Sales Order Schedule",i.name,'pending_qty',qty)

			
	# for k in sale.custom_schedule_table:
	#     if k.order_schedule == doc.name:
	#         qty = doc.qty
	
@frappe.whitelist()
def supplier_mpd(item):
	supplier = frappe.get_doc("Item",item)
	data = ''
	data1 = ''
	i = 0
	if supplier.supplier_items:
		data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f" colspan = 10><center>Supplier Details</center></th></tr>'
		data += '''
			<tr><td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan =1><b>Supplier Code</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan =1><b>Supplier Name</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Supplier Part No</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Lead Time in days</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Expected Date</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Price</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Currency</b></td>
			</td></tr>'''
		
		for i in supplier.supplier_items:
			supplier_name = frappe.db.get_value("Supplier",{"name":i.supplier},["supplier_name"])
			exp_date = add_days(nowdate(), i.custom_lead_time_in_days)
			data += '''<tr>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td></tr>'''%(i.supplier,supplier_name,i.supplier_part_no,i.custom_lead_time_in_days,formatdate(exp_date),i.custom_price,i.custom_currency)
		data += '</table>'	
	else:
		i += 1
		data1 += '<table class="table table-bordered"><tr><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f;width:100%" ><center>Supplier Details Not Available</center></th></tr>'
		data1 += '</table>'
		data += data1
	# if i > 0:
	return data


@frappe.whitelist()
def mat_req_item(item):
	supplier = frappe.get_doc("Item",item)
	data = ''
	data1 = ''
	i = 0
	if supplier.supplier_items:
		data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f" colspan = 10><center>Supplier Details</center></th></tr>'
		data += '''
			<tr><td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan =1><b>Supplier Code</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan =1><b>Supplier Name</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Supplier Part No</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Lead Time in days</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Expected Date</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Price</b></td>
			<td style="padding:1px;border: 1px solid black;color:white;background-color:#909e8a" colspan=1><b>Currency</b></td>
			</td></tr>'''
		
		for i in supplier.supplier_items:
			supplier_name = frappe.db.get_value("Supplier",{"name":i.supplier},["supplier_name"])
			exp_date = add_days(nowdate(), i.custom_lead_time_in_days)
			data += '''<tr>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
				<td style="padding:1px;border: 1px solid black" colspan=1>%s</td></tr>'''%(i.supplier,supplier_name,i.supplier_part_no,i.custom_lead_time_in_days,formatdate(exp_date),i.custom_price,i.custom_currency)
		data += '</table>'	
	else:
		i += 1
		data1 += '<table class="table table-bordered"><tr><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f;width:100%" ><center>Supplier Details Not Available</center></th></tr>'
		data1 += '</table>'
		data += data1
	# if i > 0:
	return data

@frappe.whitelist()
def set_naming(employee_category, designation,department,contractor,contractor_shortcode):
	if employee_category != "Contractor":
		if frappe.db.exists("Employee", {'employee_category': employee_category, 'designation': designation}):
			if department != 'Driver - WAIP':
				query = frappe.db.sql("""
					SELECT name 
					FROM `tabEmployee` 
					WHERE employee_category = %s AND designation = %s AND department != 'Driver - WAIP'
					ORDER BY name DESC
				""", (employee_category, designation), as_dict=True)
			elif department == 'Driver - WAIP':
				query= frappe.db.sql("""
					SELECT name 
					FROM `tabEmployee` 
					WHERE employee_category = %s AND designation = %s 
					ORDER BY name DESC
				""", (employee_category, designation), as_dict=True)
			if query:
				input_string = query[0]['name']
				match = re.search(r'(\d+)$', input_string)
			if match:
				number = match.group(1)
				leng = int(number) + 1
				str_len = str(leng)
				lengt = len(str_len)
				ty = str(lengt)
				if ty == "4":
					if employee_category=='Apprentice' and designation=='Apprentice':
						code = 'AN' + str(leng)
					if employee_category == 'Staff' or 'SUB STAFF':
						code = 'S' + str(leng)
					if employee_category == 'Operators' and designation == 'Operator':
						code = 'H' + '00' + str(leng)
					if employee_category == 'Apprentice' and designation == 'Apprentice' and department == 'Driver - WAIP':
						code = 'DR' + str(leng)
					if employee_category == 'Staff' and designation == 'General Manager':
						code = 'KR' + str(leng)
					if employee_category == 'Operators' and designation == 'Driver':
						code = 'DR'  + str(leng)
				elif ty == "3":
					if employee_category == 'Staff' :
						code = 'S' + '0' + str(leng)
					if employee_category == 'SUB STAFF':
						code = 'S' + '0' + str(leng)
					if employee_category == 'Staff' and designation == 'General Manager':
						code = 'KR' + str(leng)
					if employee_category == 'Operators' and designation == 'Driver':
						code = 'DR' + '0' + str(leng)
				elif ty == "2":
					if employee_category == 'Staff' and designation == 'General Manager':
						code = 'KR'   + '00' + str(leng)
					if employee_category == 'Operators' and designation == 'Driver':
						code = 'DR'  + '00' + str(leng)
					if employee_category == 'Operators' and designation == 'Driver':
						code = 'DR'  + '0' + str(leng) 
				elif ty == "1":
					if employee_category == 'Operators' and designation == 'Operator':
						code = 'H' + '000' + str(leng)
					if employee_category == 'Staff' and  employee_category == 'SUB STAFF':
						code = 'S' + '000' + str(leng)
					if employee_category == 'Staff' and designation == 'General Manager':
						code = 'KR'   + '00' + str(leng)
					if employee_category == 'DIRECTOR':
						if designation == 'SMD':
							code =  "SMD" + '0' + str(leng)
						if designation == "CMD":
							code =  "CMD" + '0' + str(leng)
						if designation == "BMD":
							code =  "BMD" + '0' + str(leng)
				else:
					code = str(leng) 
		else:
			code =  "0001"
	else:
		if frappe.db.exists("Employee", {'employee_category': employee_category , 'contractor' : contractor}):
			query = frappe.db.sql("""
				SELECT name 
				FROM `tabEmployee` 
				WHERE employee_category = %s
				AND contractor = %s
				ORDER BY name DESC
			""", (employee_category,contractor), as_dict=True)
			if query:
				input_string = query[0]['name']
				match = re.search(r'(\d+)$', input_string)
				if match:
					number = match.group(1)
					leng = int(number) + 1
					str_len = str(leng)
					lengt = len(str_len)
					ty = str(lengt)
					if ty == "4":
						code == contractor_shortcode + str(leng)
					elif ty == "3":
						code == contractor_shortcode + "0" + str(leng)
					elif ty == "2":
						code == contractor_shortcode + "00" + str(leng)
					elif ty == "1":
						code == contractor_shortcode + "000" + str(leng)
		else:
			code == contractor_shortcode + "0001"

		return code

# @frappe.whitelist()
# def set_naming(employee_category, designation,department,contractor,contractor_shortcode):
#     if employee_category not in ["Contractor","Director"]:
#         if frappe.db.exists("Employee", {'employee_category': employee_category}):
#             if department != 'Driver - WAIP':
#                 query = frappe.db.sql("""
#                     SELECT name 
#                     FROM `tabEmployee` 
#                     WHERE employee_category = %s AND department != 'Driver - WAIP'
#                     ORDER BY name DESC
#                 """, (employee_category, designation), as_dict=True)
#             elif department == 'Driver - WAIP':
#                 query= frappe.db.sql("""
#                     SELECT name 
#                     FROM `tabEmployee` 
#                     WHERE employee_category = %s AND department == 'Driver - WAIP'
#                     ORDER BY name DESC
#             """, (employee_category, designation), as_dict=True)
#             if query:
#                 input_string = query[0]['name']
#                 match = re.search(r'(\d+)$', input_string)
#             if match:
#                 number = match.group(1)
#                 leng = int(number) + 1
#                 str_len = str(leng)
#                 lengt = len(str_len)
#                 ty = str(lengt)
#                 if ty == "4":
#                     if employee_category=='Apprentice' and designation=='Apprentice':
#                         code = 'AN' + str(leng)
#                     if employee_category == 'Apprentice' and designation == 'Apprentice' and department == 'Driver - WAIP':
#                         code = 'DR' + str(leng)
#                     if employee_category == 'Staff' or 'SUB STAFF':
#                         if designation != 'General Manager':
#                             code = 'S' + str(leng)
#                         elif designation == 'General Manager':
#                             code = 'KR' + str(leng)
#                     if employee_category == 'Operators' and designation == 'Operator':
#                         code = 'H'  + str(leng)
#                     if employee_category == 'Operators' and designation == 'Driver':
#                         code = 'DR'  + str(leng)
#                 elif ty == "3":
#                     if employee_category=='Apprentice' and designation=='Apprentice':
#                         code = 'AN' + "0" + str(leng)
#                     if employee_category == 'Apprentice' and designation == 'Apprentice' and department == 'Driver - WAIP':
#                         code = 'DR' + "0" + str(leng)
#                     if employee_category == 'Staff' or 'SUB STAFF':
#                         if designation != 'General Manager':
#                             code = 'S' + "0" + str(leng)
#                         elif designation == 'General Manager':
#                             code = 'KR' + "0" + str(leng)
#                     if employee_category == 'Operators' and designation == 'Operator':
#                         code = 'H'  + "0" + str(leng)
#                     if employee_category == 'Operators' and designation == 'Driver':
#                         code = 'DR'  + "0" + str(leng)
#                 elif ty == "2":
#                     if employee_category=='Apprentice' and designation=='Apprentice':
#                         code = 'AN' + "00" + str(leng)
#                     if employee_category == 'Apprentice' and designation == 'Apprentice' and department == 'Driver - WAIP':
#                         code = 'DR' + "00" + str(leng)
#                     if employee_category == 'Staff' or 'SUB STAFF':
#                         if designation != 'General Manager':
#                             code = 'S' + "00" + str(leng)
#                         elif designation == 'General Manager':
#                             code = 'KR' + "00" + str(leng)
#                     if employee_category == 'Operators' and designation == 'Operator':
#                         code = 'H'  + "00" + str(leng)
#                     if employee_category == 'Operators' and designation == 'Driver':
#                         code = 'DR'  + "00" + str(leng)
#                 elif ty == "1":
#                     if employee_category=='Apprentice' and designation=='Apprentice':
#                         code = 'AN' + "000" + str(leng)
#                     if employee_category == 'Apprentice' and designation == 'Apprentice' and department == 'Driver - WAIP':
#                         code = 'DR' + "000" + str(leng)
#                     if employee_category == 'Staff' or 'SUB STAFF':
#                         if designation != 'General Manager':
#                             code = 'S' + "000" + str(leng)
#                         elif designation == 'General Manager':
#                             code = 'KR' + "000" + str(leng)
#                     if employee_category == 'Operators' and designation == 'Operator':
#                         code = 'H'  + "000" + str(leng)
#                     if employee_category == 'Operators' and designation == 'Driver':
#                         code = 'DR'  + "000" + str(leng)
#         else:
#             if employee_category=='Apprentice' and designation=='Apprentice':
#                 code = 'AN' + "000" + str(leng)
#             if employee_category == 'Apprentice' and designation == 'Apprentice' and department == 'Driver - WAIP':
#                 code = 'DR' + "000" + str(leng)
#             if employee_category == 'Staff' or 'SUB STAFF':
#                 if designation != 'General Manager':
#                     code = 'S' + "000" + str(leng)
#                 elif designation == 'General Manager':
#                     code = 'KR' + "000" + str(leng)
#             if employee_category == 'Operators' and designation == 'Operator':
#                 code = 'H'  + "000" + str(leng)
#             if employee_category == 'Operators' and designation == 'Driver':
#                 code = 'DR'  + "000" + str(leng)
#     return code

