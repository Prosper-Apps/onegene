// Copyright (c) 2024, TEAMPRO and contributors
// For license information, please see license.txt

frappe.ui.form.on("Reports Dashboard", {
    download:function(frm){
        console.log("HI")
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
        if (frm.doc.report == 'Salary Report for HR Department to  Accounts department') {
            console.log("HI")
            if (frm.doc.from_date && frm.doc.to_date) {
                console.log("HI")
                var path = "onegene.onegene.doctype.reports_dashboard.hr_accounts.download_hr_to_accounts";
                var args = "from_date=" + encodeURIComponent(frm.doc.from_date) +
                           "&to_date=" + encodeURIComponent(frm.doc.to_date) +
                           "&employee_category=" + encodeURIComponent(frm.doc.employee_category) +
                           "&bank=" + encodeURIComponent(frm.doc.bank) +
                           "&branch=" + encodeURIComponent(frm.doc.branch);
                
                if (path) {
                    window.location.href = frappe.request.url +
                        '?cmd=' + encodeURIComponent(path) +
                        '&' + args;
                }
            }
        }
	},
    print:function(frm){
        var f_name = frm.doc.name;
        var print_format = "Live -Attendance";
        window.open(frappe.urllib.get_full_url("/api/method/frappe.utils.print_format.download_pdf?"
            + "doctype=" + encodeURIComponent("Reports Dashboard")
            + "&name=" + encodeURIComponent(f_name)
            + "&trigger_print=1"
            + "&format=" + print_format
            + "&no_letterhead=0"
        ));
    },
    attendance_report: function (frm) {
        var path = "onegene.onegene.doctype.reports_dashboard.live_attendance_report.download";
        var args = 'date=' + frm.doc.date;
        
        if (path) {
            window.location.href = repl(frappe.request.url +
                '?cmd=%(cmd)s&%(args)s', {
                cmd: path,
                args: args
            });
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

