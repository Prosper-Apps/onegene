import frappe
from frappe.utils import add_days
from frappe.utils.csvutils import UnicodeWriter
from frappe.utils.file_manager import get_file
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from six import BytesIO
from datetime import date, timedelta, datetime,time

class ReportsDashboard(Document):
	pass

@frappe.whitelist()
def download():
	filename = 'Manpower_Plan_vs_Actual_Report.xlsx'
	xlsx_content = build_xlsx_content()
	frappe.response['filename'] = filename
	frappe.response['filecontent'] = xlsx_content
	frappe.response['type'] = 'binary'

def make_xlsx(data, sheet_name=None, wb=None, column_widths=None):
	args = frappe.local.form_dict
	if wb is None:
		wb = openpyxl.Workbook()
	ws = wb.create_sheet(sheet_name, 0)

	header_date = title(args)
	ws.append(header_date)

	header_date = title1(args)
	ws.append(header_date)

	header_date = title2(args)
	ws.append(header_date)

	header_date = title3(args)
	ws.append(header_date)

	data_rows = title4(args)
	for row in data_rows:
		ws.append(row)

	header_date = title5(args)
	ws.append(header_date)

	data_rows = title6(args)
	for row in data_rows:
		ws.append(row)

	ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column= 17)
	ws.merge_cells(start_row=4, start_column=1, end_row=4, end_column= 17)
	ws.merge_cells(start_row=2, start_column=1, end_row=3, end_column= 1)
	ws.merge_cells(start_row=2, start_column=2, end_row=3, end_column= 2)
	ws.merge_cells(start_row=2, start_column=3, end_row=3, end_column= 3)
	ws.merge_cells(start_row=2, start_column=4, end_row=3, end_column= 4)
	ws.merge_cells(start_row=2, start_column=5, end_row=3, end_column= 5)
	ws.merge_cells(start_row=2, start_column=17, end_row=3, end_column= 17)
	ws.merge_cells(start_row=2, start_column=6, end_row=2, end_column=9 )
	ws.merge_cells(start_row=2, start_column=10, end_row=2, end_column= 13)
	ws.merge_cells(start_row=2, start_column=14, end_row=2, end_column=16)
	ws.merge_cells(start_row=4+len(title4(args))+1, start_column=1, end_row=4+len(title4(args))+1, end_column=17)
	ws.merge_cells(start_row=4+len(title4(args)), start_column=1, end_row=4+len(title4(args)), end_column=3)
	ws.merge_cells(start_row=4+len(title4(args))-1, start_column=1, end_row=4+len(title4(args))-1, end_column=3)
	ws.merge_cells(start_row=(len(title4(args))+ len(title6(args)) + 2), start_column=1, end_row=(len(title4(args))+ len(title6(args)) + 2), end_column=3)
	ws.merge_cells(start_row=(len(title4(args))+ len(title6(args)) + 5), start_column=1, end_row=(len(title4(args))+ len(title6(args)) + 5), end_column=3)
	ws.merge_cells(start_row=(len(title4(args))+ len(title6(args)) + 4), start_column=1, end_row=(len(title4(args))+ len(title6(args)) + 4), end_column=3)
	ws.merge_cells(start_row=(len(title4(args))+ len(title6(args)) + 3), start_column=1, end_row=(len(title4(args))+ len(title6(args)) + 3), end_column=3)
	align_center = Alignment(horizontal='center',vertical='center')
	border = Border(
		left=Side(border_style='thin'),
		right=Side(border_style='thin'),
		top=Side(border_style='thin'),
		bottom=Side(border_style='thin'))
	for rows in ws.iter_rows(min_row=1, max_row=4, min_col=1, max_col=17):
		for cell in rows:
			cell.font = Font(bold=True)
			cell.alignment = align_center
	for rows in ws.iter_rows(min_row=4+len(title4(args))-1, max_row=4+len(title4(args))+1, min_col=1, max_col=17):
		for cell in rows:
			cell.font = Font(bold=True)
			cell.alignment = align_center
	for rows in ws.iter_rows(min_row=(len(title4(args))+ len(title6(args)) + 2), max_row=(len(title4(args))+ len(title6(args)) + 5), min_col=1, max_col=17):
		for cell in rows:
			cell.font = Font(bold=True)
			cell.alignment = align_center
	for rows in ws.iter_rows(min_row=5, max_row=(len(title4(args))+ len(title6(args)) + 5), min_col=3, max_col=17):
		for cell in rows:
			cell.alignment = align_center
	for rows in ws.iter_rows(min_row=1, max_row=(len(title4(args))+ len(title6(args)) + 5), min_col=1, max_col=17):
		for cell in rows:
			cell.border = border
	ws.freeze_panes = 'D4'
	ws.column_dimensions['B'].width = 25
	ws.column_dimensions['C'].width = 20
	ws.column_dimensions['D'].width = 20
	ws.column_dimensions['E'].width = 20
	ws.column_dimensions['Q'].width = 20
	xlsx_file = BytesIO()
	wb.save(xlsx_file)
	return xlsx_file.getvalue()

def build_xlsx_content():
	return make_xlsx(None, "Sheet1")

@frappe.whitelist()
def title(args):
	month = datetime.strptime(str(args.date),'%Y-%m-%d')
	mon = str(month.strftime('%B') +' '+ str(month.strftime('%Y')))
	data = ["Manpower Plan vs Actual Report for " + str(month.day) + " " + mon]
	return data

@frappe.whitelist()
def title1(args):
	data = ["S NO" ,"Particulars","Department","Business Plan","Actual Plan","Man Days(A)","","","","Overtime(B)","","","","New/Free (C)" ,"","","Total(A+B+C)"]
	return data

@frappe.whitelist()
def title2(args):
	data = ["","","","","","Com","App","Cont","Total","Com","App","Cont","Total","New","Free","Total",""]
	return data

@frappe.whitelist()
def title3(args):
	data = ["Direct Employees"]
	return data

@frappe.whitelist()
def title4(args):
	data = []
	row = []
	departments = frappe.get_all('Department', {'parent_department': 'Manufacturing - WAIP'}, order_by='name ASC')
	tbp = 0
	tacp = 0
	i = 1
	for dept in departments:
		row = [i]
		bp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['business_plan']) or 0
		acp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['plan']) or 0
		row += [dept.name,'Production',bp or 0,acp or 0]
		tbp += bp
		tacp += int(acp)
		data.append(row)
		i += 1
	row1 = ["Sub Total"," "," ",tbp,tacp," "," "," "," "," "," "," "," "," "," "," "," "]
	row2 = ["Percentage"," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "]
	data.append(row1)
	data.append(row2)
	return data 

@frappe.whitelist()
def title5(args):
	data = ["Indirect Employees"]
	return data

@frappe.whitelist()
def title6(args):
	data = []
	row = []
	qbp = frappe.get_value("Manpower Plan",{'department':'Quality - WAIP','date':args.date},['business_plan']) or 0
	qacp = frappe.get_value("Manpower Plan",{'department':'Quality - WAIP','date':args.date},['plan']) or 0
	row = [1,'Quality - WAIP','Quality',qbp or 0,qacp or 0]
	data.append(row)
	nbp = frappe.get_value("Manpower Plan",{'department':'NPD - WAIP','date':args.date},['business_plan']) or 0
	nacp = frappe.get_value("Manpower Plan",{'department':'NPD - WAIP','date':args.date},['plan']) or 0
	row = [2,'NPD - WAIP','ME  -  DEVELOPMENT',nbp or 0,nacp or 0]
	data.append(row)
	departments = frappe.get_all('Department', {'parent_department': 'M P L & Purchase - WAIP'}, order_by='name ASC')
	i = 3
	tbp = qbp + nbp
	tacp = qacp + nacp
	for dept in departments:
		row = [i]
		mbp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['business_plan']) or 0
		macp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['plan']) or 0
		row += [dept.name,'M P L & Purchase',mbp or 0,macp or 0]
		tbp += mbp
		tacp += macp
		data.append(row)
		i += 1
	count_mpl = frappe.db.count('Department', {'parent_department': 'M P L & Purchase - WAIP'})
	i = count_mpl + 2 + 1
	departments = frappe.get_all('Department', {'parent_department': 'ME -Regular - WAIP'}, order_by='name ASC')
	for dept in departments:
		row = [i]
		mrbp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['business_plan']) or 0
		mracp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['plan']) or 0
		row += [dept.name,'ME -Regular',mrbp or 0,mracp or 0]
		tbp += mrbp
		tacp += mracp
		data.append(row)
		i += 1
	count_me = frappe.db.count('Department', {'parent_department': 'ME -Regular - WAIP'})
	i = count_mpl + 2 + 1 + count_me
	departments = frappe.get_all('Department', {'parent_department': 'Maintenance - WAIP'}, order_by='name ASC')
	for dept in departments:
		row = [i]
		maibp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['business_plan']) or 0
		maiacp = frappe.get_value("Manpower Plan",{'department':dept.name,'date':args.date},['plan']) or 0
		row += [dept.name,'Maintenance',maibp or 0,maiacp or 0]
		tbp += mrbp
		tacp += mracp
		data.append(row)
		i += 1
	count_main = frappe.db.count('Department', {'parent_department': 'Maintenance - WAIP'})
	i = count_mpl + 2 + 1 + count_me + count_main
	dbp = frappe.get_value("Manpower Plan",{'department':'Delivery - WAIP','date':args.date},['business_plan']) or 0
	dacp = frappe.get_value("Manpower Plan",{'department':'Delivery - WAIP','date':args.date},['plan']) or 0
	row = [i,'Delivery - WAIP','Delivery',dbp or 0,dacp or 0]
	tbp += dbp
	tacp += dacp
	i = count_mpl + 2 + 1 + count_me + count_main + 1
	fbp = frappe.get_value("Manpower Plan",{'department':'Finance - WAIP','date':args.date},['business_plan']) or 0
	facp = frappe.get_value("Manpower Plan",{'department':'Finance - WAIP','date':args.date},['plan']) or 0
	tbp += fbp
	tacp += facp
	row = [i,'Finance - WAIP','Finance',fbp or 0,facp or 0]
	i = count_mpl + 2 + 1 + count_me + count_main + 1 + 1
	hbp = frappe.get_value("Manpower Plan",{'department':'HR - WAIP','date':args.date},['business_plan']) or 0
	hacp = frappe.get_value("Manpower Plan",{'department':'HR - WAIP','date':args.date},['plan']) or 0
	row = [i,'HR - WAIP','HR',hbp or 0,hacp or 0]
	tbp += hbp
	tacp += hacp
	row1 = ["Sub Total"," "," ",tbp,tacp," "," "," "," "," "," "," "," "," "," "," "," "]
	row2 = ["Percentage"," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "]
	totbp = frappe.db.sql("""select sum(business_plan) from `tabManpower Plan` where department = 'Manufacturing - WAIP' and date = '%s' """%(args.date),as_dict = True)[0]
	totacp = frappe.db.sql("""select sum(plan) from `tabManpower Plan` where department = 'Manufacturing - WAIP' and date = '%s' """%(args.date),as_dict = True)[0]
	totbp_value = totbp.get('tbp', 0)
	totacp_value = totacp.get('totbp', 0)

	# Now, you can use these values in your row3 list
	row3 = ["Total", " ", " ", tbp + int(totbp_value),tacp + int(totacp_value), " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " ", " "]
	row4 = ["Percentage"," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "," "]
	data.append(row1)
	data.append(row2)
	data.append(row3)
	data.append(row4)
	return data 