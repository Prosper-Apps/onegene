// Copyright (c) 2024, TEAMPRO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Attendance - Live", {
	refresh: function(frm) {
		frm.disable_save()
        frm.trigger('get_data_system')
	},
	onload: function(frm) {
        frm.disable_save()
	},
    departmentwise(frm){
        frm.trigger('get_data_system')
    },
    designationwise(frm){
        frm.trigger('get_data_system')
    },
    get_data_system(frm){
        frm.disable_save()
		frappe.call({
            method: "onegene.onegene.doctype.attendance___live.attendance___live.get_data_system",
            args: {
                dept : frm.doc.departmentwise,
                desn : frm.doc.designationwise,
            },
            callback: function(r) {
                frm.fields_dict.attendance.$wrapper.empty().append(r.message);
            }
        });
    }
});
