// Copyright (c) 2024, TEAMPRO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bulk Compensation Off Option", {
	refresh: function (frm) {
		
		if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.page.clear_primary_action();
			frm.add_custom_button(__("Get Employees"),
				function() {
					frm.events.get_employee_details(frm);
				}
			).toggleClass("btn-primary", !(frm.doc.employees_list || []).length);
			if (frm.doc.compensation_off_date != ''){
				frm.add_custom_button(__("Mark Compensation"),
				function() {
				frm.call('mark_compoff').then((r)=>{
						if(r.message == "OK"){
							frm.set_value('compensation_marked', 1)
							frappe.msgprint("Successfully Marked Compensation")
						}
					})
				})
			}
			}
		},
	get_employee_details: function(frm) {
		if (!frm.doc.department && !frm.doc.designation && !frm.doc.employee_category && !frm.doc.employee && !frm.doc.company ) {
			frappe.msgprint(__("Please choose at least one filter"));
			frappe.validated = false;
		}
		else{
			frm.call('get_employees').then((r)=>{
				frm.clear_table('employees_list')
				var c = 0
				$.each(r.message,function(i,v){
					c = c+1
					frm.add_child('employees_list',{
						'employee':v.employee,
						'attendance':v.attendance
					})
				})
				frm.refresh_field('employees_list')
				frm.set_value('number_of_employees',c)
			})
		}
	},
});
