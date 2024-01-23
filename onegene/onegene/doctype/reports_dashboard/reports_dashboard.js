// Copyright (c) 2024, TEAMPRO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Reports Dashboard", {
    // onload(frm){
    //     frm.disable_save()
    // },
    download:function(frm){
        if (frm.doc.report == 'Bulk Salary Slip Report') {
            if(frm.doc.from_date && frm.doc.to_date){
            frappe.call({
                method:"onegene.onegene.doctype.reports_dashboard.bulk_salary.enqueue_download_multi_pdf",
                args:{
                    doctype:"Salary Slip",
                    employee:frm.doc.employee,
                    start_date: frm.doc.from_date,
                    end_date: frm.doc.to_date		
                },
                callback(r){
                    if(r){
                        console.log(r)
                    }
                }
            })
            }
        }
	},
    download_report: function (frm) {
        var path = "onegene.onegene.doctype.reports_dashboard.reports_dashboard.download";
        var args = 'date=' + frm.doc.date;
        
        if (path) {
            window.location.href = repl(frappe.request.url +
                '?cmd=%(cmd)s&%(args)s', {
                cmd: path,
                args: args
            });
        }
    }
});
