frappe.pages['live-attendance'].on_page_load = function(wrapper) {
	let me = this;
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Attendance',
		single_column: true,
		card_layout : true
	});
	frappe.breadcrumbs.add('HR');

	let emp_details = {};
	frappe.call({
		'method': 'onegene.onegene.custom.get_live_attendance',
		args: {
		},
		callback: function (r) {
			att_details = r.message;
			console.log(r.message)
			page.main.html(frappe.render_template('live_attendance', {data : att_details}));
		}
	});
}
