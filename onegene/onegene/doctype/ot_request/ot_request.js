// Copyright (c) 2024, TEAMPRO and contributors
// For license information, please see license.txt

frappe.ui.form.on("OT Request", {
    onload(frm){
        frm.fields_dict.employee_details.grid.get_field('employee_code').get_query =function() {
            return {
            filters: {
                "employee_category": frm.doc.employee_category,
                "department": frm.doc.department
            }
            }
        }
        
    },
	refresh(frm){
        frm.set_query("employee_category", function (){
            return {
                filters: {
                    "name": ["not in", ["Staff","Sub Staff"]]
                }
            }
        }) 
        
        
        
        frappe.db.get_value("Company",{},'name')
        .then(r => {
            console.log(r.message.name)
            frm.set_value('company',r.message.name)
        })
    },
    validate(frm) {
        current_date=frappe.datetime.nowdate()
        if(frm.doc.ot_requested_date<current_date){
            frappe.throw("Not allowed to apply OT Request for the Past Date")
        }
	},
    employee_category(frm){
        frm.clear_table("employee_details");
        frm.trigger("department")
    },
    department(frm){
        if(frm.doc.department){
            frm.clear_table("employee_details");
            frappe.call({
                method: "onegene.onegene.doctype.ot_request.ot_request.get_employees",
                args: {
                    dept : frm.doc.department,
                    category:frm.doc.employee_category
                },
                callback: function(r) {
                    if(r.message){
                        $.each(r.message, function(i, d) {
                            var emp = frm.add_child("employee_details");
                            emp.employee_code=d
                            frappe.call({
                                method: 'frappe.client.get',
                                args: {
                                    doctype: 'Employee',
                                    name: d
                                },
                                callback: function (e) {
                                    emp.employee_name = e.message.employee_name;
                                    emp.designation = e.message.designation;
                                    frm.refresh_field('employee_details')
                                }

                            });
                        })
                    }
                    else{
                        frm.clear_table("employee_details");
                    }

                    
                }
            })
        }
    },
    ot_requested_date(frm){
        current_date=frappe.datetime.nowdate()
        if(frm.doc.ot_requested_date<current_date){
            frappe.throw("Not allowed to apply OT Request for the Past Date")
        }
    },
});
