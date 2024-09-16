import frappe
import requests
from datetime import date
import erpnext
import json
from frappe.utils import now
from frappe import throw,_
from frappe.utils import flt
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
from frappe.utils import cstr, cint, getdate, get_last_day, get_first_day, add_days,date_diff
from datetime import date, datetime, timedelta
import datetime as dt
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union


@frappe.whitelist()
def return_total_schedule(doc,method):
    total = frappe.db.sql(""" select `tabSales Order Schedule`.item_code, sum(`tabSales Order Schedule`.schedule_qty) as qty from `tabSales Order`
    left join `tabSales Order Schedule` on `tabSales Order`.name = `tabSales Order Schedule`.parent where `tabSales Order`.name = '%s' group by `tabSales Order Schedule`.item_code"""%(doc.name),as_dict = 1)

    item_total = frappe.db.sql(""" select `tabSales Order Item`.item_code, sum(`tabSales Order Item`.qty) as qty from `tabSales Order`
    left join `tabSales Order Item` on `tabSales Order`.name = `tabSales Order Item`.parent where `tabSales Order`.name = '%s' group by `tabSales Order Item`.item_code"""%(doc.name),as_dict = 1)
    for t in total:
        for i in item_total:
            if i.item_code == t.item_code:
                if t.qty > i.qty:
                    frappe.throw(
                        _(
                            "Schedule Qty {2} is Greater than -  {0} for - {1}."
                        ).format(
                            frappe.bold(i.qty),
                            frappe.bold(i.item_code),
                            frappe.bold(t.qty),
                        )
                    )
                    frappe.validated = False
                if t.qty < i.qty:
                    frappe.throw(
                        _(
                            "Schedule Qty {2} is Less than -  {0} for - {1}."
                        ).format(
                            frappe.bold(i.qty),
                            frappe.bold(i.item_code),
                            frappe.bold(t.qty),
                        )
                    )
                    frappe.validated = False

@frappe.whitelist()
def create_order_schedule_from_so(doc,method):
    if doc.customer_order_type == "Fixed" and not doc.custom_schedule_table:
        frappe.throw("Schedule not Created")
    if doc.customer_order_type == "Fixed" and doc.custom_schedule_table:
        for schedule in doc.custom_schedule_table:
            new_doc = frappe.new_doc('Order Schedule')
            new_doc.customer_code = doc.custom_customer_code
            new_doc.sales_order_number = doc.name
            new_doc.item_code = schedule.item_code
            new_doc.schedule_date = schedule.schedule_date
            new_doc.qty = schedule.schedule_qty
            for item in doc.items:
                if item.item_code == schedule.item_code:
                    new_doc.child_name = schedule.name
                    new_doc.schedule_amount = schedule.schedule_qty * item.rate
                    new_doc.order_rate = item.rate
                    new_doc.pending_qty = schedule.schedule_qty
                    new_doc.pending_amount = schedule.schedule_qty * item.rate
            new_doc.save(ignore_permissions=True)

@frappe.whitelist()
def cancel_order_schedule_on_so_cancel(doc,method):
    if doc.customer_order_type == "Fixed":
        exists = frappe.db.exists("Order Schedule",{"sales_order_number":doc.name})
        if exists:
            os = frappe.db.get_all("Order Schedule",{"sales_order_number":doc.name},'name')
            for o in os:
                print(o.name)
                delete_doc = frappe.get_doc('Order Schedule',o.name)
                delete_doc.delete()

@frappe.whitelist()
def get_so_details(sales):
    dict_list = []
    so = frappe.get_doc("Sales Order",sales)
    for i in so.items:
        dict_list.append(frappe._dict({"name":i.name,"item_code":i.item_code,"pending_qty":i.qty,"bom":i.bom_no,"description": i.description,"warehouse":i.warehouse,"rate":i.rate,"amount":i.amount}))
    return dict_list

@frappe.whitelist()
def sample_check():
    item_code = "333QRJLA-EC03"
    sf = frappe.db.sql("""select `tabMaterial Request Item`.qty as qty from `tabMaterial Request`
        left join `tabMaterial Request Item` on `tabMaterial Request`.name = `tabMaterial Request Item`.parent
        where `tabMaterial Request Item`.item_code = '%s' and `tabMaterial Request`.docstatus != 2 and `tabMaterial Request`.transaction_date = CURDATE() """%(item_code),as_dict = 1)[0].qty or 0
    print(sf)

def get_exploded_items(bom, data, indent=0, qty=1):
    exploded_items = frappe.get_all(
        "BOM Item",
        filters={"parent": bom},
        fields=["qty", "bom_no", "qty", "item_code", "item_name", "description", "uom"],
    )

    for item in exploded_items:
        item["indent"] = indent
        data.append(
            {
                "item_code": item.item_code,
                "item_name": item.item_name,
                "indent": indent,
                "bom_level": indent,
                "bom": item.bom_no,
                "qty": item.qty * qty,
                "uom": item.uom,
                "description": item.description,
            }
        )
        if item.bom_no:
            get_exploded_items(item.bom_no, data, indent=indent + 1, qty=item.qty)

@frappe.whitelist()
def get_open_order(doc,method):
    if doc.customer_order_type == "Open":
        new_doc = frappe.new_doc('Open Order')
        new_doc.sales_order_number = doc.name
        new_doc.set('open_order_table', [])
        for so in doc.items:
            new_doc.append("open_order_table", {
                "item_code": so.item_code,
                "delivery_date": so.delivery_date,
                "item_name": so.item_name,
                "qty": so.qty,
                "rate": so.rate,
                "warehouse": so.warehouse,
                "amount": so.amount,
            })
        new_doc.save(ignore_permissions=True)

@frappe.whitelist()
def create_scheduled_job_type():
    pos = frappe.db.exists('Scheduled Job Type', 'generate_production_plan')
    if not pos:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method" : 'onegene.onegene.custom.generate_production_plan',
            "frequency" : 'Daily'
        })
        sjt.save(ignore_permissions=True)


@frappe.whitelist()
def generate_production_plan():
    from frappe.utils import getdate
    from datetime import datetime
    start_date = datetime.today().replace(day=1).date()
    work_order = frappe.db.sql("""
        SELECT item_code, item_name, item_group, SUM(pending_qty) AS qty
        FROM `tabOrder Schedule`
        WHERE MONTH(schedule_date) = MONTH(CURRENT_DATE())
        GROUP BY item_code, item_name, item_group
    """, as_dict=1)
    for j in work_order:
        rej_allowance = frappe.get_value("Item",j.item_code,['rejection_allowance'])
        pack_size = frappe.get_value("Item",j.item_code,['pack_size'])
        fg_plan = frappe.get_value("Kanban Quantity",{'item_code':j.item_code},['fg_kanban_qty']) or 0
        sfg_days = frappe.get_value("Kanban Quantity",{'item_code':j.item_code},['sfg_days']) or 0
        today_plan = frappe.get_value("Kanban Quantity",{'item_code':j.item_code},['today_production_plan']) or 0
        tent_plan_i= frappe.get_value("Kanban Quantity",{'item_code':j.item_code},['tentative_plan_i']) or 0
        tent_plan_ii = frappe.get_value("Kanban Quantity",{'item_code':j.item_code},['tentative_plan_ii']) or 0
        stock = frappe.db.sql(""" select sum(actual_qty) as actual_qty from `tabBin` where item_code = '%s' """%(j.item_code),as_dict = 1)[0]
        if not stock["actual_qty"]:
            stock["actual_qty"] = 0
        pos = frappe.db.sql("""select `tabDelivery Note Item`.item_code as item_code,`tabDelivery Note Item`.qty as qty from `tabDelivery Note`
        left join `tabDelivery Note Item` on `tabDelivery Note`.name = `tabDelivery Note Item`.parent
        where `tabDelivery Note Item`.item_code = '%s' and `tabDelivery Note`.docstatus = 1 and `tabDelivery Note`.posting_date = CURDATE() """%(j.item_code),as_dict = 1)
        del_qty = 0
        if len(pos)>0:
            for l in pos:
                del_qty = l.qty
        delivery = frappe.db.sql("""select `tabDelivery Note Item`.item_code as item_code,`tabDelivery Note Item`.qty as qty from `tabDelivery Note`
        left join `tabDelivery Note Item` on `tabDelivery Note`.name = `tabDelivery Note Item`.parent
        where `tabDelivery Note Item`.item_code = '%s' and `tabDelivery Note`.docstatus = 1 and `tabDelivery Note`.posting_date between '%s' and '%s' """%(j.item_code,start_date,today()),as_dict = 1)
        del_qty_as_on_date = 0
        if len(delivery)>0:
            for d in delivery:
                del_qty_as_on_date = d.qty
        produced = frappe.db.sql("""select `tabStock Entry Detail`.item_code as item_code,`tabStock Entry Detail`.qty as qty from `tabStock Entry`
        left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
        where `tabStock Entry Detail`.item_code = '%s' and `tabStock Entry`.docstatus = 1 and `tabStock Entry`.posting_date = CURDATE() and `tabStock Entry`.stock_entry_type = "Manufacture"  """%(j.item_code),as_dict = 1)
        prod = 0
        if len(produced)>0:
            for l in produced:
                prod = l.qty
        produced_as_on_date = frappe.db.sql("""select `tabStock Entry Detail`.item_code as item_code,`tabStock Entry Detail`.qty as qty from `tabStock Entry`
        left join `tabStock Entry Detail` on `tabStock Entry`.name = `tabStock Entry Detail`.parent
        where `tabStock Entry Detail`.item_code = '%s' and `tabStock Entry`.docstatus = 1 and `tabStock Entry`.posting_date between '%s' and '%s' and `tabStock Entry`.stock_entry_type = "Manufacture" """%(j.item_code,start_date,today()),as_dict = 1)
        pro_qty_as_on_date = 0
        if len(produced_as_on_date)>0:
            for d in produced_as_on_date:
                pro_qty_as_on_date = d.qty
        work_days = frappe.db.get_single_value("Production Plan Settings", "working_days")
        with_rej = (j.qty * (rej_allowance/100)) + j.qty
        per_day = j.qty / int(work_days)
        if pack_size > 0:
            cal = per_day/ pack_size
        total = ceil(cal) * pack_size
        today_balance = 0
        reqd_plan = 0
        balance = 0
        if with_rej and fg_plan:
            balance = (int(with_rej) + int(fg_plan))
            reqd_plan = (float(total) * float(sfg_days)) + float(fg_plan)
            today_balance = int(today_plan)-int(prod)
        td_balance = 0
        if today_balance > 0:
            td_balance = today_balance
        else:
            td_balance = 0
        exists = frappe.db.exists("Production Plan Report",{"date":today(),'item':j.item_code})
        if exists:
            doc = frappe.get_doc("Production Plan Report",{"date":today(),'item':j.item_code})
        else:
            doc = frappe.new_doc("Production Plan Report")
        doc.item = j.item_code
        doc.item_name = j.item_name
        doc.item_group = j.item_group
        doc.date = today()
        doc.rej_allowance = rej_allowance
        doc.monthly_schedule = with_rej
        doc.bin_qty = pack_size
        doc.per_day_plan = total
        doc.fg_kanban_qty = fg_plan
        doc.sfg_days = sfg_days
        doc.stock_qty = stock["actual_qty"]
        doc.delivered_qty = del_qty
        doc.del_as_on_yes = del_qty_as_on_date
        doc.produced_qty = prod
        doc.pro_as_on_yes = pro_qty_as_on_date
        doc.monthly_balance = balance
        doc.today_prod_plan = today_plan
        doc.today_balance = td_balance
        doc.required_plan = reqd_plan
        doc.tent_prod_plan_1 = tent_plan_i
        doc.tent_prod_plan_2 = tent_plan_ii
        doc.save(ignore_permissions=True)

@frappe.whitelist()
def inactive_employee(doc,method):
    if doc.status=="Active":
        if doc.relieving_date:
            throw(_("Please remove the relieving date for the Active Employee."))

@frappe.whitelist()
def list_all_raw_materials(order_schedule, scheduleqty):
    doc_list = []
    consolidated_items = {}

    self = frappe.get_doc("Order Schedule", order_schedule)
    data = []
    bom_list = []

    bom = frappe.db.get_value("BOM", {'item': self.item_code}, ['name'])
    bom_list.append(frappe._dict({"bom": bom, "qty": scheduleqty}))

    for k in bom_list:
        get_exploded_items(k["bom"], data, k["qty"], bom_list)

    unique_items = {}
    for item in data:
        item_code = item['item_code']
        qty = item['qty']
        if item_code in unique_items:
            unique_items[item_code]['qty'] += qty
        else:
            unique_items[item_code] = item
    combined_items_list = list(unique_items.values())
    doc_list.append(combined_items_list)

    for i in doc_list:
        for h in i:
            item_code = h["item_code"]
            qty = h["qty"]
            if item_code in consolidated_items:
                consolidated_items[item_code] += qty
            else:
                consolidated_items[item_code] = qty
    return consolidated_items

def get_exploded_items(bom, data, qty, skip_list):
    exploded_items = frappe.get_all("BOM Item", filters={"parent": bom},
                                    fields=["qty", "bom_no", "item_code", "item_name", "description", "uom"])
    for item in exploded_items:
        item_code = item['item_code']
        if item_code in skip_list:
            continue
        item_qty = float(item['qty']) * float(qty)
        stock = frappe.db.get_value("Bin", {'item_code': item_code, 'warehouse': "SFS Store - O"},
                                    ['actual_qty']) or 0
        to_order = item_qty - stock if item_qty > stock else 0
        data.append({
            "item_code": item_code,
            "qty": item_qty,
        })
        if item['bom_no']:
            get_exploded_items(item['bom_no'], data, qty=item_qty, skip_list=skip_list)


@frappe.whitelist()
def update_pr():
    pr = frappe.db.sql("""update `tabPurchase Receipt` set docstatus = 2 where name = 'MAT-PRE-2023-00003' """,as_dict = True)
    print(pr)

# The below two methods are called in MRP Test Report, Material Requirement Planning, Internal Material Request Plan
@frappe.whitelist()
def return_print(item_type,based_on):
    from frappe.utils import cstr, add_days, date_diff, getdate,today,gzip_decompress
    pr_name = frappe.db.get_value('Prepared Report', {'report_name': 'Material Requirements Planning','status':'Completed'}, 'name')
    attached_file_name = frappe.db.get_value("File",{"attached_to_doctype": 'Prepared Report',"attached_to_name": pr_name},"name",)
    attached_file = frappe.get_doc("File", attached_file_name)
    compressed_content = attached_file.get_content()
    uncompressed_content = gzip_decompress(compressed_content)
    dos = json.loads(uncompressed_content.decode("utf-8"))
    doc = frappe.new_doc("Material Request")
    doc.material_request_type = "Purchase"
    doc.transaction_date = frappe.utils.today()
    doc.schedule_date = frappe.utils.today()
    doc.set_warehouse = "Stores - O"
    if based_on == "Highlighted Rows":
        for i in dos['result']:
            if float(i['safety_stock']) > float(i['actual_stock_qty']):
                uom = frappe.db.get_value("Item",i['item_code'],'stock_uom')
                pps = frappe.db.sql("""select sum(actual_qty) as qty from `tabBin`
                                        where item_code = %s and warehouse != 'SFS Store - O' """, (i['item_code']), as_dict=1)[0].qty or 0
                sfs = frappe.db.sql("""select sum(actual_qty) as qty from `tabBin`
                                        where item_code = %s and warehouse = 'SFS Store - O' """, (i['item_code']), as_dict=1)[0].qty or 0

                if i['to_order'] > 0:
                    doc.append("items", {
                        'item_code': i['item_code'],
                        'custom_item_type': i['item_type'],
                        'schedule_date': frappe.utils.today(),
                        'qty': i['to_order'],
                        'custom_mr_qty': i['to_order'],
                        'custom_total_req_qty': i['to_order'],
                        'custom_current_req_qty': i['to_order'],
                        'custom_stock_qty_copy': pps,
                        'custom_shop_floor_stock': sfs,
                        'custom_expected_date': i['expected_date'],
                        # 'custom_today_req_qty': today_req,
                        'uom': uom
                    })
        doc.save()
        name = [
            """<a href="/app/Form/Material Request/{0}">{1}</a>""".format(doc.name, doc.name)
        ]
        frappe.msgprint(_("Material Request - {0} created").format(", ".join(name)))
    if based_on == "Item Type":
        for i in dos['result']:
            if i['item_type'] in item_type:
                uom = frappe.db.get_value("Item",i['item_code'],'stock_uom')
                pps = frappe.db.sql("""select sum(actual_qty) as qty from `tabBin`
                                        where item_code = %s and warehouse != 'SFS Store - O' """, (i['item_code']), as_dict=1)[0].qty or 0
                sfs = frappe.db.sql("""select sum(actual_qty) as qty from `tabBin`
                                        where item_code = %s and warehouse = 'SFS Store - O' """, (i['item_code']), as_dict=1)[0].qty or 0

                if i['to_order'] > 0:
                    doc.append("items", {
                        'item_code': i['item_code'],
                        'custom_item_type': i['item_type'],
                        'schedule_date': frappe.utils.today(),
                        'qty': i['to_order'],
                        'custom_mr_qty': i['to_order'],
                        'custom_total_req_qty': i['to_order'],
                        'custom_current_req_qty': i['to_order'],
                        'custom_stock_qty_copy': pps,
                        'custom_shop_floor_stock': sfs,
                        'custom_expected_date': i['expected_date'],
                        # 'custom_today_req_qty': today_req,
                        'uom': uom
                    })
        doc.save()
        name = [
            """<a href="/app/Form/Material Request/{0}">{1}</a>""".format(doc.name, doc.name)
        ]
        frappe.msgprint(_("Material Request - {0} created").format(", ".join(name)))

@frappe.whitelist()
def return_item_type():
    dict = []
    dict_list = []
    from frappe.utils import cstr, add_days, date_diff, getdate,today,gzip_decompress
    pr_name = frappe.db.get_value('Prepared Report', {'report_name': 'Material Requirements Planning','status':'Completed'}, 'name')
    attached_file_name = frappe.db.get_value("File",{"attached_to_doctype": 'Prepared Report',"attached_to_name": pr_name},"name",)
    attached_file = frappe.get_doc("File", attached_file_name)
    compressed_content = attached_file.get_content()
    uncompressed_content = gzip_decompress(compressed_content)
    dos = json.loads(uncompressed_content.decode("utf-8"))
    doc = frappe.new_doc("Material Request")
    doc.material_request_type = "Purchase"
    doc.transaction_date = frappe.utils.today()
    doc.schedule_date = frappe.utils.today()
    doc.set_warehouse = "Stores - O"
    for i in dos['result']:
        if i['item_type'] not in dict:
            dict.append(i['item_type'])
            dict_list.append(frappe._dict({'item_type':i['item_type']}))

    return dict_list

@frappe.whitelist()
def return_mr_details(mr):
    doc = frappe.get_doc("Material Request",mr)
    return doc.items

# The below two methods are called in MRP Test Report, Material Requirement Planning
@frappe.whitelist()
def stock_details_mpd_report(item):
    w_house = frappe.db.get_value("Warehouse",['name'])
    data = ''
    stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin where item_code = '%s' order by warehouse """%(item),as_dict=True)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f" colspan = 10><center>Stock Availability</center></th></tr>'
    data += '''
    <tr><td style="padding:1px;border: 1px solid black" colspan = 4><b>Item Code</b></td>
    <td style="padding:1px;border: 1px solid black" colspan = 6>%s</td></tr>
    <tr><td style="padding:1px;border: 1px solid black" colspan = 4><b>Item Name</b></td>
    <td style="padding:1px;border: 1px solid black" colspan = 6>%s</td></tr>'''%(item,frappe.db.get_value('Item',item,'item_name'))
    data += '''
    <td style="padding:1px;border: 1px solid black;background-color:#f68b1f;color:white"  colspan = 4><b>Warehouse</b></td>
    <td style="padding:1px;border: 1px solid black;background-color:#f68b1f;color:white" colspan = 3><b>Stock Qty</b></td>
    </tr>'''
    i = 0
    for stock in stocks:
        if stock.warehouse != w_house:
            if stock.actual_qty > 0:
                data += '''<tr><td style="padding:1px;border: 1px solid black" colspan = 4 >%s</td><td style="padding:1px;border: 1px solid black" colspan = 3>%s</td></tr>'''%(stock.warehouse,stock.actual_qty)
    i += 1
    stock_qty = 0
    for stock in stocks:
        stock_qty += stock.actual_qty
    data += '''<tr><td style="background-color:#909e8a;padding:1px;border: 1px solid black;color:white;font-weight:bold" colspan = 4 >%s</td><td style="background-color:#909e8a;padding:1px;border: 1px solid black;color:white;font-weight:bold" colspan = 3>%s</td></tr>'''%("Total     ",stock_qty)
    data += '</table>'

    return data



@frappe.whitelist()
def stock_details_mpd(item,quantity):
    w_house = frappe.db.get_value("Warehouse",['name'])
    data = ''
    stocks = frappe.db.sql("""select actual_qty,warehouse,stock_uom,stock_value from tabBin where item_code = '%s' order by warehouse """%(item),as_dict=True)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f" colspan = 10><center>Stock Availability</center></th></tr>'
    data += '''
    <tr><td style="padding:1px;border: 1px solid black" colspan = 4><b>Item Code</b></td>
    <td style="padding:1px;border: 1px solid black" colspan = 6>%s</td></tr>
    <tr><td style="padding:1px;border: 1px solid black" colspan = 4><b>Item Name</b></td>
    <td style="padding:1px;border: 1px solid black" colspan = 6>%s</td></tr>'''%(item,frappe.db.get_value('Item',item,'item_name'))
    data += '''
    <td style="padding:1px;border: 1px solid black;background-color:#f68b1f;color:white"  colspan = 4><b>Warehouse</b></td>
    <td style="padding:1px;border: 1px solid black;background-color:#f68b1f;color:white" colspan = 3><b>Stock Qty</b></td>
    <td style="padding:1px;border: 1px solid black;background-color:#f68b1f;color:white" colspan = 3><b>Required Qty</b></td>

    </tr>'''
    req_qty = 0
    qty = frappe.get_doc("Material Planning Details",quantity)
    for q in qty.material_plan:
        req_qty += q.required_qty
    for stock in stocks:
        if stock.warehouse == w_house:
            if stock.actual_qty > 0:
                comp = frappe.get_value("Warehouse",stock.warehouse,['company'])
                data +=''' <tr><td style="padding:1px;border: 1px solid black;color:black;font-weight:bold" colspan = 4>%s</td><td style="padding:1px;border: 1px solid black;color:black;font-weight:bold" colspan = 3>%s</td><td style="padding:1px;border: 1px solid black;color:black;font-weight:bold" colspan = 3>%s</td></tr>'''%(stock.warehouse,stock.actual_qty,'')
    i = 0
    for stock in stocks:
        if stock.warehouse != w_house:
            if stock.actual_qty > 0:
                data += '''<tr><td style="padding:1px;border: 1px solid black" colspan = 4 >%s</td><td style="padding:1px;border: 1px solid black" colspan = 3>%s</td><td style="padding:1px;border: 1px solid black;color:black;font-weight:bold" colspan = 3>%s</td></tr>'''%(stock.warehouse,stock.actual_qty,"")
    i += 1
    stock_qty = 0
    for stock in stocks:
        stock_qty += stock.actual_qty
    data += '''<tr><td style="background-color:#909e8a;padding:1px;border: 1px solid black;color:white;font-weight:bold" colspan = 4 >%s</td><td style="background-color:#909e8a;padding:1px;border: 1px solid black;color:white;font-weight:bold" colspan = 3>%s</td><td style="background-color:#909e8a;color:white;padding:1px;border: 1px solid black;font-weight:bold" colspan = 3>%s</td></tr>'''%("Total     ",stock_qty,req_qty)
    data += '</table>'

    return data

@frappe.whitelist()
def previous_purchase(item_table):
    item_table = json.loads(item_table)
    data = []
    for item in item_table:
        try:
            item_name = frappe.get_value('Item',{'name':item['item_code']},"item_name")
            pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,sum(`tabPurchase Order Item`.qty) as qty from `tabPurchase Order`
            left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
            where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 """%(item["item_code"]),as_dict=True)
            for po in pos:
                data.append([item['item_code'],item_name,po.qty])
        except:
            pass
    return data


@frappe.whitelist()
def previous_po_html(item_code):
    data = ""
    item_name = frappe.get_value('Item',{'item_code':item_code},"item_name")
    pos = frappe.db.sql("""select `tabPurchase Order Item`.item_code as item_code,`tabPurchase Order Item`.item_name as item_name,`tabPurchase Order`.supplier as supplier,`tabPurchase Order Item`.qty as qty,`tabPurchase Order Item`.rate as rate,`tabPurchase Order Item`.amount as amount,`tabPurchase Order`.transaction_date as date,`tabPurchase Order`.name as po from `tabPurchase Order`
    left join `tabPurchase Order Item` on `tabPurchase Order`.name = `tabPurchase Order Item`.parent
    where `tabPurchase Order Item`.item_code = '%s' and `tabPurchase Order`.docstatus != 2 order by date"""%(item_code),as_dict=True)


    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f" colspan=6><center>Previous Purchase Order</center></th></tr>'
    data += '''
    <tr><td colspan =2 style="padding:1px;border: 1px solid black;width:300px" ><b>Item Code</b></td>
    <td style="padding:1px;border: 1px solid black;width:200px" colspan =4>%s</td></tr>
    <tr><td colspan =2 style="padding:1px;border: 1px solid black" ><b>Item Name</b></td>
    <td style="padding:1px;border: 1px solid black" colspan =4>%s</td></tr>

    <tr><td style="padding:1px;border: 1px solid black" colspan =1><b>Supplier Name</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>Previous Purchase Order</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>PO Date</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>PO Rate</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>PO Quantity</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>PO Amount</b>
    </td></tr>'''%(item_code,item_name)
    for po in pos:
        data += '''<tr>
            <td style="padding:1px;border: 1px solid black" colspan =1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td></tr>'''%(po.supplier,po.po,po.date,po.rate,po.qty,po.amount)

    data += '</table>'
    return data

# The below method is called in MRP Test Report, Material Requirement Planning
@frappe.whitelist()
def mpd_details(name):
    data = ""
    pos = frappe.db.sql("""select `tabMaterial Planning Item`.item_code,`tabMaterial Planning Item`.item_name,`tabMaterial Planning Item`.uom,`tabMaterial Planning Item`.order_schedule_date,sum(`tabMaterial Planning Item`.required_qty) as qty from `tabMaterial Planning Details`
        left join `tabMaterial Planning Item` on `tabMaterial Planning Details`.name = `tabMaterial Planning Item`.parent
        where `tabMaterial Planning Details`.name = '%s' group by `tabMaterial Planning Item`.order_schedule_date """%(name),as_dict = 1)
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f" colspan=6><center>Order Schedule Details</center></th></tr>'
    data += '''
    <tr><td style="padding:1px;border: 1px solid black" colspan =1><b>Item Code</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>Item Name</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>UOM</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>Schedule Date</b></td>
    <td style="padding:1px;border: 1px solid black" colspan=1><b>Quantity</b></td>
    </td></tr>'''
    for po in pos:
        data += '''<tr>
            <td style="padding:1px;border: 1px solid black" colspan =1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td></tr>'''%(po.item_code,po.item_name,po.uom,po.order_schedule_date,po.qty)
    data += '</table>'
    return data


@frappe.whitelist()
def list_raw_mat():
    qty = 120
    skip_list = []
    data = []
    bom = "BOM-742-HWFAB-002"
    exploded_items = frappe.get_all("BOM Item", filters={"parent": bom},fields=["qty", "bom_no as bom", "item_code", "item_name", "description", "uom"])
    for item in exploded_items:
        item_code = item['item_code']
        if item_code in skip_list:
            continue
        item_qty = flt(item['qty']) * qty
        data.append({"item_code": item_code,"item_name": item['item_name'],"bom": item['bom'],"uom": item['uom'],"qty": item_qty,"description": item['description']})
    frappe.errprint(data)


@frappe.whitelist()
def get_bom_details(bo, child):
    dict_list = []
    seen_items = set()

    so = frappe.get_doc("BOM", bo)
    op = frappe.db.get_all("Operation Item List", {"operation_name": child, "document_name": bo}, ["*"])

    if op:
        checked_row = 0
        for j in op:
            checked_row = j.selected_field
            if j.item not in seen_items:
                dict_list.append(frappe._dict({"check_box": 1, "name": checked_row, "item_code": j.item, "req_tot_qty": j.req_tot_qty, "uom": j.uom}))
                seen_items.add(j.item)

    for i in so.items:
        if i.item_code not in seen_items:
            dict_list.append(frappe._dict({"item_code": i.item_code, "req_tot_qty": i.qty, "uom": i.uom}))
            seen_items.add(i.item_code)

    return dict_list

@frappe.whitelist()
def table_multiselect(docs,item,item_code,child,uom,req_tot_qty):
    op = frappe.db.get_value("Operation Item List",{"document_name":docs,"item":item_code,"operation_name":child},["name"])
    if not op:
        bom_child = frappe.new_doc("Operation Item List")
        bom_child.document_name = docs
        bom_child.item = item_code
        bom_child.operation_name = child
        bom_child.selected_field = item
        bom_child.req_tot_qty = req_tot_qty
        bom_child.uom = uom
        bom_child.save()

@frappe.whitelist()
def bday_allocate():
    employee_query = """
    SELECT *
    FROM `tabEmployee`
    WHERE
        status = 'Active'
        AND employee_category IN ('Staff', 'Operator', 'Sub Staff')
        AND MONTH(date_of_birth) = MONTH(CURDATE())
        AND date_of_joining < CURDATE()
    """
    employee = frappe.db.sql(employee_query, as_dict=True)
    pay =  get_first_day(nowdate())
    for emp in employee:
        if frappe.db.exists("Salary Structure Assignment",{'employee':emp.name,'docstatus':1}):
            if not frappe.db.exists('Additional Salary',{'employee':emp.name,'payroll_date':pay,'salary_component':"Birthday Allowance",'docstatus':('!=',2)}):
                bday_amt = frappe.new_doc("Additional Salary")
                bday_amt.employee = emp.name
                bday_amt.payroll_date = pay
                bday_amt.company = emp.company
                bday_amt.salary_component = "Birthday Allowance"
                bday_amt.currency = "INR"
                bday_amt.amount = 1000
                bday_amt.save(ignore_permissions = True)
                bday_amt.submit()

def add_bday_allowance():
    job = frappe.db.exists('Scheduled Job Type', 'bday_allocate')
    if not job:
        sjt = frappe.new_doc("Scheduled Job Type")
    sjt.update({
        "method": 'onegene.onegene.custom.bday_allocate',
        "frequency": 'Cron',
        "cron_format": '00 00 01 * *'
    })
    sjt.save(ignore_permissions=True)


@frappe.whitelist()
def overtime_hours(doc,method):
    ot_hours=frappe.db.sql("""select sum(custom_overtime_hours) from `tabAttendance` where employee = '%s' and attendance_date between '%s' and '%s'"""%(doc.employee,doc.start_date,doc.end_date),as_dict=True)[0]
    doc.custom_overtime_hours = ot_hours['sum(custom_overtime_hours)']

@frappe.whitelist()
def fixed_salary(doc,method):
    earned_basic=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Basic"},["amount"]) or 0
    da=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Dearness Allowance"},["amount"]) or 0
    hra=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"House Rent Allowance"},["amount"]) or 0
    wa=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Washing Allowance"},["amount"]) or 0
    ca=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Conveyance Allowance"},["amount"]) or 0
    ea=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Education Allowance"},["amount"]) or 0
    pa=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Performance Allowance"},["amount"]) or 0
    sa=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Special Allowance"},["amount"]) or 0
    stipend=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Stipend"},["amount"]) or 0
    att_inc=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Attendance Incentive"},["amount"]) or 0
    basic_da=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Basic & DA"},["amount"]) or 0
    lta=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Leave Travel Allowance"},["amount"]) or 0
    mnc=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Medical & Conveyance Allowance"},["amount"]) or 0
    sp=frappe.db.get_value("Salary Detail",{"parent":doc.name,"salary_component":"Special Pay"},["amount"]) or 0
    if doc.payment_days<doc.total_working_days:
        if earned_basic:
            doc.custom_basic = round((earned_basic/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_basic = 0
        if da:
            doc.custom_dearness_allowance = round((da/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_dearness_allowance = 0
        if hra:
            doc.custom_house_rent_allowance = round((hra/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_house_rent_allowance = 0
        if wa:
            doc.custom_washing_allowance = round((wa/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_washing_allowance = 0
        if ca:
            doc.custom_conveyance_allowance = round((ca/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_conveyance_allowance = 0
        if ea:
            doc.custom_education_allowance = round((ea/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_education_allowance = 0
        if pa:
            doc.custom_performance_allowance = round((pa/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_performance_allowance = 0
        if sa:
            doc.custom_special_allowance = round((sa/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_special_allowance = 0
        if stipend:
            doc.custom_stipend = round((stipend/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_stipend = 0
        if att_inc:
            doc.custom_attendance_incentive = round(att_inc)
        else:
            doc.custom_attendance_incentive = 0
        if basic_da:
            doc.custom_basic_da = round((basic_da/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_basic_da = 0
        if lta:
            doc.custom_leave_travel_allowance = round((lta/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_leave_travel_allowance = 0
        if mnc:
            doc.custom_medical_conveyance_allowance = round((mnc/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_medical_conveyance_allowance = 0
        if sp:
            doc.custom_special_pay = round((sp/doc.payment_days)*doc.total_working_days)
        else:
            doc.custom_special_pay = 0
        total = doc.custom_basic+doc.custom_dearness_allowance+doc.custom_house_rent_allowance+doc.custom_washing_allowance+doc.custom_conveyance_allowance+doc.custom_education_allowance+doc.custom_performance_allowance+doc.custom_stipend+doc.custom_basic_da+doc.custom_leave_travel_allowance+doc.custom_medical_conveyance_allowance+doc.custom_special_pay
        doc.custom_total_fixed_amount = round(total)
        doc.save(ignore_permissions = True)
        frappe.db.commit()
    else:
        doc.custom_basic = earned_basic
        doc.custom_dearness_allowance = da
        doc.custom_house_rent_allowance = hra
        doc.custom_washing_allowance = wa
        doc.custom_conveyance_allowance = ca
        doc.custom_education_allowance = ea
        doc.custom_performance_allowance = pa
        doc.custom_special_allowance = sa
        doc.custom_stipend = stipend
        doc.custom_attendance_incentive = att_inc
        doc.custom_basic_da = basic_da
        doc.custom_leave_travel_allowance = lta
        doc.custom_medical_conveyance_allowance = mnc
        doc.custom_special_pay = sp
        doc.custom_total_fixed_amount = earned_basic+da+hra+wa+ca+ea+pa+stipend+basic_da+lta+mnc+sp
        doc.save(ignore_permissions = True)
        frappe.db.commit()

@frappe.whitelist()
def sick_leave_allocation():
    today = date.today()
    year_start_date = datetime(today.year, 1, 1).date()
    year_end_date = datetime(today.year, 12, 31).date()
    employees=frappe.db.get_all("Employee",{"Status":"Active"},['*'])
    for emp in employees:
        frappe.errprint(emp.name)
        la=frappe.db.exists("Leave Allocation",{"employee":emp.name,"leave_type":"Sick Leave","from_date":year_start_date,"to_date":year_end_date})
        if la:
            leave_all=frappe.get_doc("Leave Allocation",la)
            leave_all.new_leaves_allocated +=0.5
            leave_all.total_leaves_allocated +=0.5
            leave_all.save(ignore_permissions=True)
            leave_all.submit()

        else:
            leave_all=frappe.new_doc("Leave Allocation")
            leave_all.employee=emp.name
            leave_all.leave_type="Sick Leave"
            leave_all.from_date=year_start_date
            leave_all.to_date=year_end_date
            leave_all.new_leaves_allocated=0.5
            leave_all.total_leaves_allocated =0.5
            # leave_all.carry_forward=1
            leave_all.save(ignore_permissions=True)
            leave_all.submit()

def update_leave_policy():
    pre_year = date.today().year - 1
    start_of_year = date(pre_year, 1, 1)
    end_of_year = date(pre_year, 12, 31)
    current_year = date.today().year
    start = date(current_year, 1, 1)
    end = date(current_year, 12, 31)
    leave = frappe.get_all("Leave Policy Detail", ["leave_type", "annual_allocation"])
    for i in leave:
        if i.leave_type =="Earned Leave":
            employees = frappe.get_all("Employee",{"status": "Active",'employee_category':('!=','Contractor')},["name","company"])
            for emp in employees:
                present = frappe.db.count("Attendance",{"employee":emp.name,"status":"Present","attendance_date": ["between", [start_of_year, end_of_year]]})
                half_day = frappe.db.count("Attendance",{"employee":emp.name,"status":"Half Day","attendance_date": ["between", [start_of_year, end_of_year]]})
                half = half_day/2
                attendance = present + half
                earned_leave = round(attendance /20)
                if earned_leave:
                    allow = frappe.new_doc("Leave Allocation")
                    allow.employee = emp.name
                    allow.company = emp.company
                    allow.leave_type = "Earned Leave"
                    allow.from_date = start
                    allow.to_date = end
                    allow.new_leaves_allocated = earned_leave
                    allow.total_leaves_allocated = earned_leave
                    allow.save(ignore_permissions=True)
                    allow.submit()
    frappe.db.commit()

@frappe.whitelist()
def create_leave_allocation():
    emc = frappe.new_doc("Scheduled Job Type")
    emc.update({
        "method": 'onegene.onegene.custom.update_leave_policy',
        "frequency": 'Cron',
        "cron_format": '00 01 01 01 *'
    })
    emc.save(ignore_permissions=True)

@frappe.whitelist()
def create_leave_allocation_jan10():
    emc = frappe.new_doc("Scheduled Job Type")
    emc.update({
        "method": 'onegene.onegene.custom.update_leave_policy',
        "frequency": 'Cron',
        "cron_format": '00 01 10 01 *'
    })
    emc.save(ignore_permissions=True)

@frappe.whitelist()
def update_shift(employee,from_date,to_date):
    shift_3 = frappe.db.count("Attendance",{"employee":employee,"attendance_date": ["between", [from_date, to_date]],"status":"Present","shift":"3"})
    shift_3_half = frappe.db.count("Attendance",{"employee":employee,"attendance_date": ["between", [from_date, to_date]],"status":"Half Day","shift":"3"})
    half_3 = shift_3_half/2
    shift3 = shift_3 + half_3
    shift_5 = frappe.db.count("Attendance",{"employee":employee,"attendance_date": ["between", [from_date, to_date]],"status":"Present","shift":"5"})
    shift_5_half = frappe.db.count("Attendance",{"employee":employee,"attendance_date": ["between", [from_date, to_date]],"status":"Half Day","shift":"5"})
    half_5 = shift_5_half/2
    shift5 = shift_5 + half_5
    shift = shift3 + shift5
    return shift


from frappe.utils import cstr, cint, getdate,get_first_day, get_last_day, today, time_diff_in_hours
@frappe.whitelist()
def att_req_hours(f_time,t_time,custom_session,custom_shift):
    if custom_session == "Flexible":
        if f_time and t_time:
            # frappe.errprint("hlo")
            time_diff = time_diff_in_hours(t_time,f_time)
            return time_diff
    elif custom_session == "Full Day":
        return "8"
    else :
        return "4"

@frappe.whitelist()
def od_hours_update(doc, method):
    dates = get_dates(doc.from_date, doc.to_date)
    for date in dates:
        if doc.reason == "On Duty" and doc.custom_session == "Full Day":
            if frappe.db.exists("Attendance", {'employee': doc.employee, 'attendance_date': date, 'docstatus': ('!=', 2)}):
                att = frappe.get_doc("Attendance", {'employee': doc.employee, 'attendance_date': date, 'docstatus': ('!=', 2)})
            else:
                att = frappe.new_doc("Attendance")
                att.employee = doc.employee
            att.company = doc.company
            att.status = "Present"
            att.working_hours = 8
            att.attendance_request = doc.name
            att.save(ignore_permissions=True)
            att.submit()
            frappe.db.commit()
        if doc.reason == "On Duty" and doc.custom_session in ["First Half", "Second Half"]:
            if frappe.db.exists("Attendance", {'employee': doc.employee, 'attendance_date': date, 'docstatus': ('!=', 2)}):
                att = frappe.get_doc("Attendance", {'employee': doc.employee, 'attendance_date': date, 'docstatus': ('!=', 2)})
                if att.working_hours >= 4:
                    att.working_hours += 4
                    att.status = "Present"
                else:
                    att.working_hours += 4
                    att.status = "Half Day"
                att.company = doc.company
            else:
                att = frappe.new_doc("Attendance")
                att.employee = doc.employee
                att.working_hours = 4
                att.company = doc.company
                att.status = "Half Day"
            att.attendance_request = doc.name
            att.save(ignore_permissions=True)
            att.submit()
            frappe.db.commit()
        if doc.reason == "On Duty" and doc.custom_session == "Flexible":
            if frappe.db.exists("Attendance", {'employee': doc.employee, 'attendance_date': date, 'docstatus': ('!=', 2)}):
                att = frappe.get_doc("Attendance", {'employee': doc.employee, 'attendance_date': date, 'docstatus': ('!=', 2)})
                if att.in_time and att.out_time:
                    st = datetime.strptime(str(doc.custom_from_time), '%H:%M:%S').time()
                    start_time = dt.datetime.combine(att.attendance_date,st)
                    if att.in_time > start_time :
                        att.in_time = start_time
                    et = datetime.strptime(str(doc.custom_to_time), '%H:%M:%S').time()
                    end_time = dt.datetime.combine(att.attendance_date,et)
                    if att.out_time < end_time :
                        att.out_time = end_time
                    att.save(ignore_permissions=True)
                    frappe.db.commit()
                    
                    

def get_dates(from_date,to_date):
    no_of_days = date_diff(add_days(to_date, 1), from_date)
    dates = [add_days(from_date, i) for i in range(0, no_of_days)]
    return dates

@frappe.whitelist()
def update_birthday_alowance(doc,method):
    if doc.status == "Left":
        if doc.date_of_birth > doc.relieving_date:
            if doc.date_of_birth.month == doc.relieving_date.month:
                first_day = get_first_day(doc.relieving_date)
                if frappe.db.exists("Additional Salary", {'employee': doc.name, 'salary_component': "Birthday Allowance", 'payroll_date': first_day, 'docstatus': 1}):
                    ad = frappe.get_doc("Additional Salary", {'employee': doc.name, 'salary_component': "Birthday Allowance", 'payroll_date': first_day, 'docstatus': 1})
                    ad.update({
                        'docstatus': 2
                    })
                    ad.save()


@frappe.whitelist()
def create_lwf():
    def is_december_1(date_to_check):
        return date_to_check.month == 12 and date_to_check.day == 1
    employee_query = """
    SELECT *
    FROM `tabEmployee`
    WHERE
        status = 'Active'  """
    employee = frappe.db.sql(employee_query, as_dict=True)
    date_to_check = date.today()
    if is_december_1(date_to_check):
        print("The date is December 1st.")
        for emp in employee:
            if frappe.db.exists("Salary Structure Assignment", {'employee': emp.name, 'docstatus': 1}):
                if not frappe.db.exists('Additional Salary', {'employee': emp.name, 'payroll_date': date_to_check, 'salary_component': "Labour Welfare Fund", 'docstatus': ('!=', 2)}):
                    lwf = frappe.new_doc("Additional Salary")
                    lwf.employee = emp.name
                    lwf.payroll_date = date_to_check
                    lwf.company = emp.company
                    lwf.salary_component = "Labour Welfare Fund"
                    lwf.currency = "INR"
                    lwf.amount = 20
                    lwf.save(ignore_permissions=True)
                    lwf.submit()
    else:
        print("The date is not December 1st.")

@frappe.whitelist()
def renamed_doc(doc,method):
    name = doc.name
    employee_number = doc.employee_number
    emp = frappe.get_doc("Employee",name)
    emps=frappe.get_all("Employee",{"status":"Active"},['*'])
    for i in emps:
        if emp.employee_number == employee_number:
            pass
        elif i.employee_number == employee_number:
            frappe.throw(f"Employee Number already exists for {i.name}")
        else:
            frappe.db.set_value("Employee",name,"employee_number",employee_number)
            frappe.rename_doc("Employee", name, employee_number, force=1)


@frappe.whitelist(allow_guest=True)
def get_live_attendance():
    nowtime = datetime.now()
    att_details = {}
    att_details['nowtime'] = datetime.strftime(nowtime, '%d-%m-%Y %H:%M:%S')
    max_out = datetime.strptime('06:30', '%H:%M').time()

    if nowtime.time() > max_out:
        date1 = nowtime.date()
    else:
        date1 = (nowtime - timedelta(days=1)).date()

    staff_count = frappe.db.sql("""
        SELECT COUNT(*) AS count
        FROM `tabAttendance`
        WHERE attendance_date = %s
        AND custom_employee_category IN ("Staff", "Sub Staff", "Director")
        AND in_time IS NOT NULL
        AND out_time IS NULL
    """, (date1,), as_dict=True)

    att_details['staff_count'] = staff_count[0].count if staff_count else 0
    ops_count = frappe.db.sql("""
        SELECT COUNT(*) AS count
        FROM `tabAttendance`
        WHERE attendance_date = %s
        AND custom_employee_category IN ("Operator")
        AND in_time IS NOT NULL
        AND out_time IS NULL
    """, (date1,), as_dict=True)

    att_details['ops_count'] = ops_count[0].count if ops_count else 0
    aps_count = frappe.db.sql("""
        SELECT COUNT(*) AS count
        FROM `tabAttendance`
        WHERE attendance_date = %s
        AND custom_employee_category IN ("Apprentice")
        AND in_time IS NOT NULL
        AND out_time IS NULL
    """, (date1,), as_dict=True)

    att_details['aps_count'] = aps_count[0].count if aps_count else 0
    cl_count = frappe.db.sql("""
        SELECT COUNT(*) AS count
        FROM `tabAttendance`
        WHERE attendance_date = %s
        AND custom_employee_category IN ("Contractor")
        AND in_time IS NOT NULL
        AND out_time IS NULL
    """, (date1,), as_dict=True)

    att_details['cl_count'] = cl_count[0].count if cl_count else 0
    tot_count = frappe.db.sql("""
        SELECT COUNT(*) AS count
        FROM `tabAttendance`
        WHERE attendance_date = %s
        AND in_time IS NOT NULL
        AND out_time IS NULL
    """, (date1,), as_dict=True)

    att_details['tot_count'] = tot_count[0].count if tot_count else 0
    return att_details

@frappe.whitelist()
def update_leave_ledger():
    leave_updates = [
    """update `tabAttendance` set 
        late_entry = 0,
        early_exit = 0,
        custom_late_entry_time = NULL,
        custom_early_out_time = NULL 
    where status = "Half Day" and attendance_date between "2024-03-01" and "2024-05-31"
    """
]

    for query in leave_updates:
        leave = frappe.db.sql(query, as_dict=True)

@frappe.whitelist()
def check_pf_type(name):
    if frappe.db.exists("Salary Detail",{"parent":name,"salary_component":"Provident Fund"}):
        return "With PF"
    else:
        return "Without PF"


@frappe.whitelist()
def mark_disable(doc,method):
    if doc.status=='Left':
        frappe.db.set_value("User",doc.user_id,"enabled",0)  


@frappe.whitelist()
def update_role(id):
    usr=frappe.get_doc("User",id)
    usr.append("roles",{
        "role":"Staff/Sub Staff"
    })
    usr.save(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist()
def remove_system_manager_role(doc,method):
    usr=frappe.get_doc("User",doc.name)
    usr.remove_roles("System Manager")
    usr.save(ignore_permissions=True)
    frappe.db.commit()

@frappe.whitelist()
def create_user_id(doc,method):
    user_id=doc.name.lower()+'@onegeneindia.in'
    if frappe.db.exists("User",{"email":user_id}):
        frappe.throw("User ID already exists")
    else:
        user=frappe.new_doc("User")
        user.first_name=doc.first_name
        user.middle_name=doc.middle_name
        user.last_name=doc.last_name
        user.username=doc.employee
        user.full_name=doc.employee_name
        user.email=user_id
        user.save(ignore_permissions=True)
        frappe.db.commit()
        frappe.db.set_value("Employee",doc.name,'user_id',user_id)


@frappe.whitelist()
def get_deleted_automatically():
    yesterday = add_days(today(), -1)
    planning = frappe.db.exists("Night Shift Auditors Planning List", {'attendance_date': yesterday})
    if planning:
        attendance_exists = frappe.db.exists("Attendance", {'employee': planning.emp, 'attendance_date': yesterday, 'docstatus': ('!=', 2)})
        if attendance_exists:
            attendance = frappe.get_doc("Attendance", {'employee': planning.emp, 'attendance_date': yesterday, 'docstatus': ('!=', 2)})
            date1 = dt.datetime.strptime(yesterday, "%Y-%m-%d").date()
            shift_end_time = datetime.strptime("05:00:00", '%H:%M:%S').time()
            start_time = dt.datetime.combine(add_days(date1,1), shift_end_time)
            if attendance.out_time :
                if attendance.out_time > start_time:
                    status = "Eligible"
                else:
                    status = "Not-Eligible"
            else:
                status = "Not-Eligible"
            if status == "Not-Eligible":
                frappe.delete_doc("Night Shift Auditors Planning List", planning.name, ignore_permissions=True)

@frappe.whitelist()
def create_scheduled_for_night_shift_planning_auto_delete():
    ns = frappe.db.exists('Scheduled Job Type', 'get_deleted_automatically')
    if not ns:
        sjt = frappe.new_doc("Scheduled Job Type")
        sjt.update({
            "method" : 'onegene.onegene.custom.get_deleted_automatically',
            "frequency": 'Cron',
            "cron_format": '0 10 * * *'

        })
        sjt.save(ignore_permissions=True)

@frappe.whitelist()
def get_data_system(date):
    data =""
    shift=frappe.get_all("Shift Type",['*'],order_by='name ASC')
    shift2=4
    for i in shift:
        shift2+=1
    ec1=0
    ec_count=frappe.get_all("Employee Category",{'name':('not in',['Sub Staff','Director'])},['*'])
    for i in ec_count:
        ec1 +=1 
    data = "<table class='table table-bordered=1'>"
    data += "<tr><td colspan ={}  style='border: 1px solid black;background-color:#f6d992;text-align:center'><b>Live Attendance</b></td><td colspan ={} style='border: 1px solid black;background-color:#f6d992;text-align:center'><b>Date {}  </b></td><tr>" .format(shift2,ec1,date)
    shift1=1
    for i in shift:
        shift1+=1
    data += "<tr><td rowspan=2 style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center;'>Parent Department</td><td rowspan=2 style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center;'>Department</td><td colspan={} style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center'>Shift</td><td colspan={} style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center'>Category</td><td rowspan=2 style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center'>CheckOut</td></tr>".format(shift1,ec1)        
    data += "<tr>"
    for i in shift:
        data += "<td style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center'>{}</td>".format(i.name)
    data += "<td style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center'>Total Present</td>"        
    
    ec=frappe.get_all("Employee Category",{'name':('not in',['Sub Staff','Director'])},['*'])
    for i in ec:
        data += "<td style='border: 1px solid black;background-color:#FFA500;font-weight:bold;text-align:center'>{}</td>".format(i.name)
    data +="</tr>"

    total = 0
    department = frappe.get_all("Department", {'disabled': ('!=', 1),"parent_department":"All Departments"}, ['name'])        
    for d in department:
        length=2
        department1 = frappe.get_all("Department", {'disabled': ('!=', 1),"parent_department":d.name}, ['name'])
        for dep in department1:
            length+=1
        frappe.errprint(length)
        parent_dep=d.name
        total_pre=0
        total_cl=0
        total_trainee=0
        total_ops=0
        total_staff=0
        totl_ch_out=0
        data += "<tr><td rowspan={} style='border: 1px solid black;text-align:left'>{}</td><td style='border: 1px solid black;text-align:center'></td>".format(length,d.name)
        for i in shift:
            shift_attendance_count = frappe.db.sql("""
                SELECT COUNT(*) AS count
                FROM `tabAttendance`
                WHERE attendance_date = %s
                AND shift = %s
                AND department = %s
                AND in_time IS NOT NULL

            """, (date, i.name, d.name), as_dict=True)
            shift_attendance = shift_attendance_count[0].count if shift_attendance_count else 0
            data += "<td style='border: 1px solid black;text-align:center'>{}</td>".format(shift_attendance)
        staff_count = frappe.db.sql("""
            SELECT COUNT(*) AS count
            FROM `tabAttendance`
            WHERE attendance_date = %s
            AND custom_employee_category IN ("Staff", "Sub Staff", "Director")
            AND department = %s
            AND in_time IS NOT NULL
        """, (date,d.name), as_dict=True)
        staff = staff_count[0].count if staff_count else 0
        ops_count = frappe.db.sql("""
            SELECT COUNT(*) AS count
            FROM `tabAttendance`
            WHERE attendance_date = %s
            AND custom_employee_category IN ("Operator")
            AND department = %s
            AND in_time IS NOT NULL
        """, (date,d.name), as_dict=True)
        ops = ops_count[0].count if ops_count else 0
        aps_count = frappe.db.sql("""
            SELECT COUNT(*) AS count
            FROM `tabAttendance`
            WHERE attendance_date = %s
            AND custom_employee_category IN ("Apprentice")
            AND department = %s
            AND in_time IS NOT NULL
        """, (date,d.name), as_dict=True)
        trainee = aps_count[0].count if aps_count else 0
        cl_count = frappe.db.sql("""
            SELECT COUNT(*) AS count
            FROM `tabAttendance`
            WHERE attendance_date = %s
            AND custom_employee_category IN ("Contractor")
            AND department = %s
            AND in_time IS NOT NULL
        """, (date,d.name), as_dict=True)
        cl = cl_count[0].count if cl_count else 0
        
        checkout_count = frappe.db.sql("""
            SELECT COUNT(*) AS count
            FROM `tabAttendance`
            WHERE attendance_date = %s
            AND department = %s
            AND in_time IS NOT NULL
            AND out_time IS NOT NULL
        """, (date,d.name), as_dict=True)
        ch_out = checkout_count[0].count if checkout_count else 0
        total += (staff+ops+trainee+cl)
        total_pre+=(staff+ops+trainee+cl)
        total_cl+=cl
        total_trainee+=trainee
        total_ops+=ops
        total_staff+=staff
        totl_ch_out+=ch_out
        data += "<td style='border: 1px solid black;text-align:center;background-color:#ADD8E6'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center;background-color:#BACC81'>%s</td>" % ((staff+ops+trainee+cl),cl,trainee,ops,staff,ch_out)
        data += '</tr>'
        department = frappe.get_all("Department", {'disabled': ('!=', 1),"parent_department":d.name}, ['name'])
        for d in department:
            data += "<tr><td style='border: 1px solid black;text-align:center'>%s</td>"%(d.name)
            for i in shift:
                shift_attendance_count = frappe.db.sql("""
                    SELECT COUNT(*) AS count
                    FROM `tabAttendance`
                    WHERE attendance_date = %s
                    AND shift = %s
                    AND department = %s
                    AND in_time IS NOT NULL
                """, (date, i.name, d.name), as_dict=True)
                shift_attendance = shift_attendance_count[0].count if shift_attendance_count else 0
                data += "<td style='border: 1px solid black;text-align:center'>{}</td>".format(shift_attendance)
            staff_count = frappe.db.sql("""
                SELECT COUNT(*) AS count
                FROM `tabAttendance`
                WHERE attendance_date = %s
                AND custom_employee_category IN ("Staff", "Sub Staff", "Director")
                AND department = %s
                AND in_time IS NOT NULL
            """, (date,d.name), as_dict=True)
            staff = staff_count[0].count if staff_count else 0
            ops_count = frappe.db.sql("""
                SELECT COUNT(*) AS count
                FROM `tabAttendance`
                WHERE attendance_date = %s
                AND custom_employee_category IN ("Operator")
                AND department = %s
                AND in_time IS NOT NULL
            """, (date,d.name), as_dict=True)
            ops = ops_count[0].count if ops_count else 0
            aps_count = frappe.db.sql("""
                SELECT COUNT(*) AS count
                FROM `tabAttendance`
                WHERE attendance_date = %s
                AND custom_employee_category IN ("Apprentice")
                AND department = %s
                AND in_time IS NOT NULL
            """, (date,d.name), as_dict=True)
            trainee = aps_count[0].count if aps_count else 0
            cl_count = frappe.db.sql("""
                SELECT COUNT(*) AS count
                FROM `tabAttendance`
                WHERE attendance_date = %s
                AND custom_employee_category IN ("Contractor")
                AND department = %s
                AND in_time IS NOT NULL
            """, (date,d.name), as_dict=True)
            cl = cl_count[0].count if cl_count else 0
            checkout_count = frappe.db.sql("""
                SELECT COUNT(*) AS count
                FROM `tabAttendance`
                WHERE attendance_date = %s
                AND department = %s
                AND in_time IS NOT NULL
                AND out_time IS NOT NULL
            """, (date,d.name), as_dict=True)
            ch_out = checkout_count[0].count if checkout_count else 0
            total += (staff+ops+trainee+cl)
            total_pre+=(staff+ops+trainee+cl)
            total_cl+=cl
            total_trainee+=trainee
            total_ops+=ops
            total_staff+=staff
            totl_ch_out+=ch_out
            data += "<td style='border: 1px solid black;text-align:center;background-color:#ADD8E6'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center;background-color:#BACC81'>%s</td></tr>" % ((staff+ops+trainee+cl),cl,trainee,ops,staff,ch_out)
        data += "<tr style='border: 1px solid black;text-align:center;background-color:#C0C0C0'><td style='border: 1px solid black;text-align:center'>Total</td>"
        for i in shift:
            shift_count=0
            shift_attendance_count = frappe.db.sql("""
                SELECT COUNT(*) AS count
                FROM `tabAttendance`
                WHERE attendance_date = %s
                AND shift = %s
                AND department = %s
                AND in_time IS NOT NULL

            """, (date, i.name, parent_dep), as_dict=True)
            shift_attendance = shift_attendance_count[0].count if shift_attendance_count else 0
            shift_count+=shift_attendance
            department = frappe.get_all("Department", {'disabled': ('!=', 1),"parent_department":parent_dep}, ['name'])
            for d in department:
                shift_attendance_count = frappe.db.sql("""
                    SELECT COUNT(*) AS count
                    FROM `tabAttendance`
                    WHERE attendance_date = %s
                    AND shift = %s
                    AND department = %s
                    AND in_time IS NOT NULL

                """, (date, i.name, d.name), as_dict=True)
                shift_attendance = shift_attendance_count[0].count if shift_attendance_count else 0
                shift_count+=shift_attendance
            data += "<td style='border: 1px solid black;text-align:center'>{}</td>".format(shift_count)
        data+="<td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td><td style='border: 1px solid black;text-align:center'>%s</td></tr>" % (total_pre,total_cl,total_trainee,total_ops,total_staff,totl_ch_out)
    colspan=(shift2)-2
    data += "<tr><td colspan = {} style='border: 1px solid black;text-align:left'>Total Present</td><td colspan=6 style='border: 1px solid black;text-align:left'>{}</td></tr>" .format(colspan,total)
    data += "</table>"
    return data

import frappe

@frappe.whitelist()
def restrict_for_zero_balance(doc, method):
    if doc.is_new() and doc.leave_type!='Leave Without Pay': 
        total_leave_days_present=0
        total_lbalance=doc.leave_balance
        draft_leave_applications = frappe.get_all("Leave Application", {"employee": doc.employee,"workflow_state": ('in',["Draft",'Pending For HOD']),"leave_type": doc.leave_type},["*"])
        for i in draft_leave_applications:
            frappe.errprint(i.name)
            total_leave_days_present+=i.total_leave_days
        total_leave_days_present += doc.total_leave_days
        available=total_lbalance-total_leave_days_present
        frappe.errprint(total_lbalance)
        frappe.errprint(total_leave_days_present)
        frappe.errprint(available)
        if available < 0 :
            frappe.throw("Insufficient leave balance for this leave type")

@frappe.whitelist()
def att_request_cancel(doc, method):
    att=frappe.db.get_value("Attendance",{'attendance_request':doc.name},['name'])
    if att:
        attendance = frappe.db.get_value('Attendance', {
            'employee': doc.employee,
            'attendance_date': doc.from_date,
            'docstatus': ("!=", 2)
        }, ['name'])
        frappe.db.set_value('Attendance',att,'attendance_request','')

@frappe.whitelist()
def condition_for_la(doc,method):
    diff = date_diff(today(), doc.from_date)
    role = frappe.db.get_value("Has Role",{"parent":frappe.session.user,"role":["in",["HR User","HR Manager","HOD"]]})
    if not role:
        if diff > 3:
            frappe.throw("The Leave Application must be apply within 3 days from the leave date")

@frappe.whitelist()
def condition_for_ar(doc,method):
    diff = date_diff(today(), doc.from_date)
    role = frappe.db.get_value("Has Role",{"parent":frappe.session.user,"role":["in",["HR User","HR Manager","HOD"]]})
    if not role:
        if diff > 3:
            frappe.throw("The Attendance Request must be apply within 3 days")

@frappe.whitelist()
def condition_for_compoff_lr(doc,method):
    diff = date_diff(today(), doc.work_from_date)
    role = frappe.db.get_value("Has Role",{"parent":frappe.session.user,"role":["in",["HR User","HR Manager","HOD"]]})
    if not role:
        if diff > 3:
            frappe.throw("The Compensatory Leave Request must be apply within 3 days")

@frappe.whitelist()
def condition_for_ap(doc,method):
    diff = date_diff(today(), doc.permission_date)
    role = frappe.db.get_value("Has Role",{"parent":frappe.session.user,"role":["in",["HR User","HR Manager","HOD"]]})
    if not role:
        if diff > 3:
            frappe.throw("The Attendance Permission must be apply within 3 days")

@frappe.whitelist()
def condition_for_nsaps(doc,method):
    diff = date_diff(today(), doc.requesting_date)
    role = frappe.db.get_value("Has Role",{"parent":frappe.session.user,"role":["in",["HR User","HR Manager","HOD"]]})
    if not role:
        if diff > 3:
            frappe.throw("The Night Shift Auditors Plan Swapping must be apply within 3 days")

@frappe.whitelist()
def get_ot_balance(custom_employee,custom_from_date,custom_to_date):
    data = ''
    OTBalance = frappe.qb.DocType("OT Balance")
    ot_balance = (
        frappe.qb.from_(OTBalance)
        .select(OTBalance.employee, OTBalance.total_ot_hours, OTBalance.comp_off_pending_for_approval,OTBalance.comp_off_used,OTBalance.ot_balance)
        .where(
            (OTBalance.employee == custom_employee)
            & ((custom_from_date >= OTBalance.from_date) & (custom_to_date <= OTBalance.to_date))
        )
    ).run(as_dict=True)
    if ot_balance and ot_balance[0]:
        data += '<br><br>'
        data += '<table border=1 width=100%>'
        data += '<tr style="text-align:center;background-color:#ff9248;color:#FFFFFF"><td>Total OT Hours</td><td>C-OFF (Pending for Approval) in Day(s)</td><td>C-OFF Used in Day(s)</td><td>OT Balance Hours</td></tr>'
        data += '<tr style="text-align:center;"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(ot_balance[0].total_ot_hours,ot_balance[0].comp_off_pending_for_approval,ot_balance[0].comp_off_used,ot_balance[0].ot_balance)
        data += '</table><br><br>'
    else:
        data += '<p style="text-align:center;"><b>OT balance is not available</b></p>'
    return data

@frappe.whitelist()
def validate_ot(employee,total_leave_days,from_date,to_date,employee_category):
    result=2
    OTBalance = frappe.qb.DocType("OT Balance")
    ot_balance = (
        frappe.qb.from_(OTBalance)
        .select(OTBalance.ot_balance)
        .where(
            (OTBalance.employee == employee)
            & ((from_date >= OTBalance.from_date) & (to_date <= OTBalance.to_date))
        )
    ).run(as_dict=True)
    if ot_balance and ot_balance[0]:
        if float(total_leave_days)*float(8) > float(ot_balance[0].ot_balance):
            frappe.errprint(float(total_leave_days)*float(8))
            frappe.errprint("The Problem")
            result=frappe.throw("Insufficient OT Balance to apply for C-OFF")
            return result
        else:
            if employee_category not in["Staff","Sub Staff"]:
                frappe.errprint(float(total_leave_days)*float(8))
                frappe.errprint("Hiii")
                if frappe.db.exists("Leave Allocation",{'employee':employee,'leave_type':"Compensatory Off",'from_date':['<=', from_date],'docstatus':("!=",2)}):
                    frappe.errprint("H")
                    lal=frappe.get_doc("Leave Allocation",{'employee':employee,'leave_type':"Compensatory Off",'from_date':['<=', from_date],'docstatus':("!=",2)})
                    frappe.errprint(lal)
                    frappe.errprint(total_leave_days)
                    lal.new_leaves_allocated = lal.new_leaves_allocated + float(total_leave_days)
                    lal.save(ignore_permissions=True)
                    lal.submit()
                else:
                    frappe.errprint("HHH")
                    lal=frappe.new_doc("Leave Allocation")
                    lal.employee=employee
                    lal.leave_type='Compensatory Off'
                    lal.from_date=from_date
                    lal.to_date="2024-12-31"
                    lal.new_leaves_allocated=total_leave_days
                    lal.save(ignore_permissions=True)
                    lal.submit()

@frappe.whitelist()
def get_number_of_leave_days(
    custom_employee: str,
    custom_from_date: datetime.date,
    custom_to_date: datetime.date,
    custom_half_day: Union[int, str, None] = None,
    custom_half_day_date: Union[datetime.date, str, None] = None,
    holiday_list: Optional[str] = None,
) -> float:
    """Returns number of leave days between 2 dates after considering half day and holidays
    (Based on the include_holiday setting in Leave Type)"""
    number_of_days = 0
    if cint(custom_half_day) == 1:
        if getdate(custom_from_date) == getdate(custom_to_date):
            number_of_days = 0.5
        elif custom_half_day_date and getdate(custom_from_date) <= getdate(custom_half_day_date) <= getdate(custom_to_date):
            number_of_days = date_diff(custom_to_date, custom_from_date) + 0.5
        else:
            number_of_days = date_diff(custom_to_date, custom_from_date) + 1
    else:
        number_of_days = date_diff(custom_to_date, custom_from_date) + 1

    return number_of_days

@frappe.whitelist()
def return_select_options(employee_category,employee):
    select_option = []
    frappe.errprint("Select")
    current_year = datetime.now().year
    leave = frappe.db.sql("""
        SELECT leave_type, SUM(leaves) AS total_leaves
        FROM `tabLeave Ledger Entry`
        WHERE docstatus != '2'
        AND employee = %s
        AND YEAR(from_date) = %s
        AND YEAR(to_date) = %s
        GROUP BY leave_type
        HAVING total_leaves > 0
        ORDER BY leave_type
    """, (employee, current_year, current_year), as_dict=1)

    if employee_category not in ["Staff","Sub Staff"]:
        frappe.errprint("Select Leave Type")
        select_option = ["Comp-off from OT","Leave Without Pay"]
        if leave:
            for l in leave:
                select_option.append(l['leave_type'])
    else:
        frappe.errprint("Hiii")
        select_option = ["Leave Without Pay"]
        if leave:
            for l in leave:
                select_option.append(l['leave_type'])
    return select_option

@frappe.whitelist()
def otbalance(doc, method):
    month_start = get_first_day(doc.from_date)
    month_end = get_last_day(doc.from_date)
    draft_leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            'employee': doc.employee,
            'from_date': ('between', [month_start, month_end]),
            'to_date': ('between', [month_start, month_end]),
            'workflow_state': 'Draft',
            'custom_select_leave_type':'Comp-off from OT'
        },
        fields=["total_leave_days"]
    )
    approved_leave_applications = frappe.get_all(
        "Leave Application",
        filters={
            'employee': doc.employee,
            'from_date': ('between', [month_start, month_end]),
            'to_date': ('between', [month_start, month_end]),
            'workflow_state': 'Approved',
            'custom_select_leave_type':'Comp-off from OT'
        },
        fields=["total_leave_days"]
    )
    total_draft_leave_days = sum([i['total_leave_days'] for i in draft_leave_applications])
    total_approved_leave_days = sum([i['total_leave_days'] for i in approved_leave_applications])
    frappe.errprint("The Problem")
    if frappe.db.exists("OT Balance", {'employee': doc.employee, 'from_date': month_start, 'to_date': month_end}):
        otb = frappe.get_doc("OT Balance", {'employee': doc.employee, 'from_date': month_start, 'to_date': month_end})
        otb.comp_off_pending_for_approval = float(total_draft_leave_days)
        otb.comp_off_used = float(total_approved_leave_days)
        otb.ot_balance =float(otb.total_ot_hours)-((float(total_draft_leave_days)*float(8)) + (float(total_approved_leave_days)*float(8)))
        otb.save(ignore_permissions=True)

@frappe.whitelist()
def cancel_leave_application(doc, method):
    leave_allocation = frappe.get_doc("Leave Allocation", {
        'employee': doc.custom_employee2,
        'leave_type': "Compensatory Off",
        'from_date': ['<=', doc.from_date],
        'docstatus': ("!=", 2)
    })
    
    if leave_allocation:
        leave_allocation.new_leaves_allocated -= float(doc.custom_total_leave_days)
        leave_allocation.save(ignore_permissions=True)
        frappe.db.commit()

    OTBalance = frappe.get_doc("OT Balance", {
        'employee': doc.employee,
        'from_date': ['<=', doc.from_date],
        'to_date': ['>=', doc.to_date]
    })

    if OTBalance:
        OTBalance.ot_balance += float(doc.custom_total_leave_days) * 8
        OTBalance.comp_off_used-=doc.custom_total_leave_days
        OTBalance.save(ignore_permissions=True)
        frappe.db.commit()

@frappe.whitelist()
def mail_alert_for_safety_stock():
    item = frappe.get_all("Item",{"disabled":0,"safety_stock":("!=",0)},["name","safety_stock"])
    data = ""
    data += '<table class="table table-bordered"><tr><th style="padding:1px;border: 1px solid black;color:white;background-color:#f68b1f" colspan=3><center>Stock Details</center></th></tr>'
    data += '<tr><td style="padding:1px;border: 1px solid black" colspan =1><b>Item Code</b></td><td style="padding:1px;border: 1px solid black" colspan=1><b>Safety Stock</b></td><td style="padding:1px;border: 1px solid black" colspan=1><b>Available Qty</b></td></tr>'
    for i in item:
        stockqty = frappe.db.sql(""" select item_code,sum(actual_qty) as qty from `tabBin` where item_code = '%s' """%(i.name),as_dict = 1)[0]
        if stockqty['qty']:
            stockqty['qty'] = stockqty['qty']
        else:
            stockqty['qty'] =0
        if i.safety_stock >= stockqty['qty']:
            data += '''  
            <tr><td style="padding:1px;border: 1px solid black" colspan =1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td>
            <td style="padding:1px;border: 1px solid black" colspan=1>%s</td></tr>'''%(i.name,i.safety_stock,stockqty['qty'] or 0)
    data += '</table>'
    frappe.sendmail(
        recipients=["jenisha.p@groupteampro.com","gifty@groupteampro.com","sarath.v@groupteampro.com","sivarenisha.m@groupteampro.com"],
        subject='Stock Details',
        message="""Dear Sir/Mam,<br><br>
            Kindly Check below Item list qty<br>{0}
            """.format(data)
    )
    # user = frappe.db.sql("""
    #     SELECT `tabUser`.name as name
    #     FROM `tabUser`
    #     LEFT JOIN `tabHas Role` ON `tabHas Role`.parent = `tabUser`.name 
    #     WHERE `tabHas Role`.Role = "Stock Manager" AND `tabUser`.enabled = 1
    # """, as_dict=True)
    # if data:
    #     for i in user:
    #         frappe.sendmail(
    #             recipients=["jenisha.p@groupteampro.com"],
    #             subject='Stock Details',
    #             message="""Dear Sir/Mam,<br><br>
    #                 Kindly Check below Item list qty<br>{0}
    #                 """.format(data)
    #         )

@frappe.whitelist()
def cron_job_safety_stock():
    job = frappe.db.exists('Scheduled Job Type', 'mail_alert_for_safety_stock')
    if not job:
        att = frappe.new_doc("Scheduled Job Type")
        att.update({
            "method": 'onegene.onegene.custom.mail_alert_for_safety_stock',
            "frequency": 'Cron',
            "cron_format": '0 0 * * *'
        })
        att.save(ignore_permissions=True)

