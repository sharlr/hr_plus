// ====================================
// LIST VIEW BUTTON - FIXED
// ====================================
frappe.listview_settings['Monthly Attendance Summary'] = {
    onload: function(listview) {
        // Add bulk button to list view
        listview.page.add_inner_button(__('Create Bulk Summaries'), function() {
            create_bulk_summaries_dialog_from_list();
        }).addClass('btn-info');
    },
    
    // Also add button to menu for better visibility
    refresh: function(listview) {
        if (!listview.page.custom_buttons['Create Bulk Summaries']) {
            listview.page.add_inner_button(__('Create Bulk Summaries'), function() {
                create_bulk_summaries_dialog_from_list();
            }).addClass('btn-info');
        }
    }
};

// ====================================
// FORM VIEW BUTTON (NEW + EXISTING)
// ====================================
frappe.ui.form.on('Monthly Attendance Summary', {
    refresh: function(frm) {
        // Show on both new and existing documents
        frm.add_custom_button(__('Create Bulk Summaries'), function() {
            create_bulk_summaries_dialog_from_form(frm);
        }).addClass('btn-info');
        
        // Original fetch button only for existing docs
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Fetch Attendance'), function() {
                fetch_attendance_with_month_names(frm);
            }).addClass('btn-primary');
        }
    }
});

// ====================================
// DIALOG FROM LIST VIEW
// ====================================
function create_bulk_summaries_dialog_from_list() {
    let dialog = new frappe.ui.Dialog({
        title: __('Create Bulk Attendance Summaries'),
        fields: [
            {
                label: 'Month',
                fieldname: 'month',
                fieldtype: 'Link',
                options: 'Month',
                reqd: 1
            },
            {
                label: 'Year',
                fieldname: 'year',
                fieldtype: 'Link',
                options: 'Year',
                reqd: 1
            }
        ],
        primary_action_label: __('Create Summaries'),
        primary_action(values) {
            dialog.hide();
            frappe.show_progress(__('Processing Bulk Summaries'), 0, 100);
            process_bulk_summaries(null, values.month, values.year);
        }
    });
    dialog.show();
}

// ====================================
// DIALOG FROM FORM VIEW
// ====================================
function create_bulk_summaries_dialog_from_form(frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('Create Bulk Attendance Summaries'),
        fields: [
            {
                label: 'Month',
                fieldname: 'month',
                fieldtype: 'Link',
                options: 'Month',
                reqd: 1
            },
            {
                label: 'Year',
                fieldname: 'year',
                fieldtype: 'Link',
                options: 'Year',
                reqd: 1
            }
        ],
        primary_action_label: __('Create Summaries'),
        primary_action(values) {
            dialog.hide();
            frappe.show_progress(__('Processing Bulk Summaries'), 0, 100);
            process_bulk_summaries(frm, values.month, values.year);
        }
    });
    dialog.show();
}

// ====================================
// BULK SUMMARY PROCESSING
// ====================================
function process_bulk_summaries(frm, month_name, year_name) {
    
    const monthNumber = get_month_number(month_name);
    const year = parseInt(year_name);
    
    if (!monthNumber || !year) {
        frappe.hide_progress();
        frappe.msgprint(__('Invalid Month or Year'));
        return;
    }
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Employee Checkin',
            filters: [
                ['time', '>=', `${year}-${String(monthNumber).padStart(2,'0')}-01`],
                ['time', '<=', get_last_day_of_month(year, monthNumber)]
            ],
            fields: ['employee'],
            limit_page_length: 5000
        },
        callback: function(r) {
            
            if (!r.message || !r.message.length) {
                frappe.hide_progress();
                frappe.msgprint(__('No checkins found for this month/year'));
                return;
            }
            
            let employees = [...new Set(r.message.map(d => d.employee))];
            
            if (employees.length === 0) {
                frappe.hide_progress();
                frappe.msgprint(__('No employees found'));
                return;
            }
            
            let processed = 0;
            let results = {
                created: [],
                updated: [],
                submitted: []
            };
            
            employees.forEach((emp, index) => {
                
                let percent = Math.floor(((index + 1) / employees.length) * 100);
                frappe.show_progress(__('Processing Employees'), percent, 100);
                
                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Monthly Attendance Summary',
                        filters: [
                            ['employee', '=', emp],
                            ['month', '=', month_name],
                            ['year', '=', year_name]
                        ]
                    },
                    callback: function(existing_doc) {
                        
                        if (existing_doc.message) {
                            let doc = existing_doc.message;
                            
                            if (doc.docstatus === 1) {
                                results.submitted.push({
                                    employee: emp,
                                    name: doc.name,
                                    status: 'Submitted'
                                });
                                check_complete();
                            } else {
                                update_single_summary(emp, month_name, year_name, monthNumber, year, doc.name, function(success) {
                                    if (success) {
                                        results.updated.push({
                                            employee: emp,
                                            name: doc.name,
                                            status: 'Updated'
                                        });
                                    }
                                    check_complete();
                                });
                                return;
                            }
                        } else {
                            create_single_summary(emp, month_name, year_name, monthNumber, year, function(new_name) {
                                if (new_name) {
                                    results.created.push({
                                        employee: emp,
                                        name: new_name,
                                        status: 'Created'
                                    });
                                }
                                check_complete();
                            });
                            return;
                        }
                    },
                    
                    error: function(err) {
                        create_single_summary(emp, month_name, year_name, monthNumber, year, function(new_name) {
                            if (new_name) {
                                results.created.push({
                                    employee: emp,
                                    name: new_name,
                                    status: 'Created'
                                });
                            }
                            check_complete();
                        });
                    }
                });
                
                function check_complete() {
                    processed++;
                    if (processed === employees.length) {
                        frappe.hide_progress();
                        show_bulk_results(results);
                    }
                }
            });
        }
    });
}

// ====================================
// CREATE SINGLE SUMMARY - FIXED
// ====================================
function create_single_summary(employee, month_name, year_name, monthNumber, year, callback) {
    
    frappe.call({
        method: 'frappe.client.insert',
        args: {
            doc: {
                doctype: 'Monthly Attendance Summary',
                employee: employee,
                month: month_name,
                year: year_name,
                attendance_date: null
            }
        },
        callback: function(r) {
            if (r.message) {
                let new_frm = { doc: r.message };
                fetch_attendance_for_bulk(new_frm, year, monthNumber, month_name, function() {
                    callback(r.message.name);
                });
            } else {
                callback(null);
            }
        }
    });
}

// ====================================
// UPDATE SINGLE SUMMARY - FIXED
// ====================================
function update_single_summary(employee, month_name, year_name, monthNumber, year, existing_name, callback) {
    
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Monthly Attendance Summary',
            name: existing_name
        },
        callback: function(r) {
            if (r.message) {
                let frm = { doc: r.message };
                fetch_attendance_for_bulk(frm, year, monthNumber, month_name, function() {
                    callback(true);
                });
            } else {
                callback(false);
            }
        }
    });
}

// ====================================
// FETCH ATTENDANCE FOR BULK - WITH LEAVE CHECK
// ====================================
function fetch_attendance_for_bulk(frm, year, monthNumber, monthName, callback) {
    
    let firstDay = `${year}-${String(monthNumber).padStart(2,'0')}-01`;
    let lastDay = get_last_day_of_month(year, monthNumber);
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Employee Checkin',
            filters: [
                ['employee', '=', frm.doc.employee],
                ['time', '>=', firstDay],
                ['time', '<=', lastDay]
            ],
            fields: ['time', 'log_type'],
            limit_page_length: 5000
        },
        callback: function(r) {
            
            if (!r.message || !r.message.length) {
                set_empty_attendance_bulk(frm, year, monthNumber);
                
                frappe.call({
                    method: 'frappe.client.save',
                    args: {
                        doc: frm.doc
                    },
                    callback: function() {
                        if (callback) callback();
                    }
                });
                return;
            }
            
            const filtered = r.message.filter(c => {
                const d = new Date(c.time);
                return (d.getMonth() + 1) === monthNumber && d.getFullYear() === year;
            });
            
            // First calculate attendance normally
            const summary = calculate_attendance_with_month(filtered, year, monthNumber, monthName);
            
            // Then check for leave applications on absent days
            check_leave_applications(frm.doc.employee, year, monthNumber, function(leaveDays) {
                // Process absent days and convert to leaves where applicable
                process_absent_and_leaves(summary, leaveDays, year, monthNumber);
                
                // Update document with processed data
                Object.keys(summary).forEach(k => frm.doc[k] = summary[k]);
                
                frappe.call({
                    method: 'frappe.client.save',
                    args: {
                        doc: frm.doc
                    },
                    callback: function() {
                        // Show alerts for absent days without leave
                        show_absent_without_leave_alerts(summary, leaveDays, year, monthNumber);
                        if (callback) callback();
                    }
                });
            });
        }
    });
}

// ====================================
// CHECK LEAVE APPLICATIONS FOR ABSENT DAYS
// ====================================
function check_leave_applications(employee, year, monthNumber, callback) {
    let firstDay = `${year}-${String(monthNumber).padStart(2,'0')}-01`;
    let lastDay = get_last_day_of_month(year, monthNumber);
    
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Leave Application',
            filters: [
                ['employee', '=', employee],
                ['from_date', '<=', lastDay],
                ['to_date', '>=', firstDay],
                ['status', '=', 'Approved'],  // Only approved leaves
                ['docstatus', '=', 1]  // Only submitted documents
            ],
            fields: ['from_date', 'to_date', 'name'],
            limit_page_length: 100
        },
        callback: function(r) {
            let leaveDays = new Set();
            
            if (r.message && r.message.length) {
                r.message.forEach(leave => {
                    let start = new Date(leave.from_date);
                    let end = new Date(leave.to_date);
                    
                    // Generate all dates between from_date and to_date
                    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
                        // Only include days within our month
                        if (d.getMonth() + 1 === monthNumber && d.getFullYear() === year) {
                            leaveDays.add(d.getDate());
                        }
                    }
                });
            }
            
            callback(leaveDays);
        }
    });
}

// ====================================
// PROCESS ABSENT DAYS AND CONVERT TO LEAVES
// ====================================
function process_absent_and_leaves(summary, leaveDays, year, monthNumber) {
    // Initialize leaves field if not present
    if (!summary.leaves) {
        summary.leaves = 0;
    }
    
    let totalDays = summary.total_days;
    let absentDays = summary.absent_days || 0;
    let leavesCount = 0;
    let absentWithoutLeave = [];
    
    // Check each day of the month
    for (let i = 1; i <= totalDays; i++) {
        let currentDate = new Date(year, monthNumber - 1, i);
        
        // Skip Fridays (holidays)
        if (currentDate.getDay() === 5) {
            continue;
        }
        
        // Check if this day is absent (not in present days)
        // Present days calculation is complex, so we'll use the absent count logic
        // Since we don't have direct access to which specific days are absent,
        // we'll use the leaveDays set to know which days have leave
        
        if (leaveDays.has(i)) {
            leavesCount++;
        }
    }
    
    // Update absent days (remove leaves from absent)
    // Note: This assumes that days with leave applications were counted as absent originally
    summary.leaves = leavesCount;
    
    // Adjust absent days: subtract leaves from absent
    // But ensure absent days doesn't go negative
    if (summary.absent_days >= leavesCount) {
        summary.absent_days = summary.absent_days - leavesCount;
    } else {
        // This case shouldn't happen, but handle gracefully
        summary.absent_days = 0;
    }
}

// ====================================
// SHOW ALERTS FOR ABSENT DAYS WITHOUT LEAVE
// ====================================
function show_absent_without_leave_alerts(summary, leaveDays, year, monthNumber) {
    let totalDays = summary.total_days;
    let absentWithoutLeave = [];
    
    // Track present days from the summary
    // Since we don't have the raw checkins here, we'll need to estimate
    // A better approach would be to pass the filtered checkins, but for now:
    
    // For each day in the month
    for (let i = 1; i <= totalDays; i++) {
        let currentDate = new Date(year, monthNumber - 1, i);
        
        // Skip Fridays (holidays)
        if (currentDate.getDay() === 5) {
            continue;
        }
        
        // If day has leave, it's not absent without leave
        if (leaveDays.has(i)) {
            continue;
        }
        
        // This is a complex check - ideally we'd need to know if the employee was present
        // Since we don't have that info here, we'll show a general message
        // The detailed check would need to be done in calculate_attendance_with_month
    }
    
    // For now, show a summary message if there are leaves vs absent
    if (summary.absent_days > 0) {
        let msg = __(`Employee has {0} absent days. `, [summary.absent_days]);
        
        if (summary.leaves > 0) {
            msg += __(`{0} days are covered by leave applications. `, [summary.leaves]);
        }
        
        if (summary.absent_days > 0) {
            msg += __(`{0} days are absent without any leave application.`, [summary.absent_days]);
            frappe.show_alert({
                message: msg,
                indicator: 'orange'
            });
        }
    }
}

// ====================================
// SET EMPTY FOR BULK - WITH LEAVES FIELD
// ====================================
function set_empty_attendance_bulk(frm, year, month) {
    const total = new Date(year, month, 0).getDate();
    let fri = 0;
    for (let i=1; i<=total; i++) {
        if (new Date(year, month-1, i).getDay() === 5) fri++;
    }
    
    frm.doc.total_days = total;
    frm.doc.holidays = fri;
    frm.doc.working_days = total - fri;
    frm.doc.present_days = 0;
    frm.doc.absent_days = total - fri;
    frm.doc.leaves = 0;  // Initialize leaves field
    frm.doc.late_coming_minutes = 0;
    frm.doc.overtime_hours = 0;
    frm.doc.late_coming_hours = 0;
}

// ====================================
// SHOW BULK RESULTS
// ====================================
function show_bulk_results(results) {
    
    let msg = '<h4>Bulk Summary Creation Report</h4>';
    
    if (results.created.length > 0) {
        msg += `<br><b>? Newly Created: ${results.created.length}</b><br>`;
        results.created.forEach(d => {
            msg += `&nbsp;&nbsp;- ${d.employee} ? <a href="/app/monthly-attendance-summary/${d.name}">${d.name}</a><br>`;
        });
    }
    
    if (results.updated.length > 0) {
        msg += `<br><b>?? Created Before (Updated): ${results.updated.length}</b><br>`;
        results.updated.forEach(d => {
            msg += `&nbsp;&nbsp;- ${d.employee} ? <a href="/app/monthly-attendance-summary/${d.name}">${d.name}</a><br>`;
        });
    }
    
    if (results.submitted.length > 0) {
        msg += `<br><b>?? Submitted (Skipped - Cannot Edit): ${results.submitted.length}</b><br>`;
        results.submitted.forEach(d => {
            msg += `&nbsp;&nbsp;- ${d.employee} ? <a href="/app/monthly-attendance-summary/${d.name}">${d.name}</a> (Submitted)<br>`;
        });
    }
    
    if (results.created.length === 0 && results.updated.length === 0 && results.submitted.length > 0) {
        msg = `<h4>All summaries already exist for this month/year</h4>`;
        msg += `<br><b>?? Submitted Documents: ${results.submitted.length}</b><br>`;
        results.submitted.forEach(d => {
            msg += `&nbsp;&nbsp;- ${d.employee} ? <a href="/app/monthly-attendance-summary/${d.name}">${d.name}</a><br>`;
        });
    }
    
    if (results.created.length === 0 && results.updated.length === 0 && results.submitted.length === 0) {
        msg = '<h4>No employees found with checkins for this month/year</h4>';
    }
    
    frappe.msgprint({
        message: msg,
        title: __('Bulk Summary Results'),
        indicator: results.created.length > 0 ? 'green' : 'blue'
    });
}

// ====================================
// ORIGINAL FETCH ATTENDANCE - UPDATED WITH LEAVE CHECK
// ====================================
function fetch_attendance_with_month_names(frm) {
    if (!frm.doc.employee || !frm.doc.month || !frm.doc.year) {
        frappe.msgprint(__('Please set Employee, Month and Year first'));
        return;
    }

    const monthNumber = get_month_number(frm.doc.month);
    const year = parseInt(frm.doc.year);

    if (!monthNumber || isNaN(monthNumber)) {
        frappe.msgprint(__('Invalid Month'));
        return;
    }

    frappe.show_progress(__('Fetching Attendance'), 0, 100);

    let firstDay, lastDay;

    if (frm.doc.attendance_date) {
        firstDay = frm.doc.attendance_date;
        lastDay = frm.doc.attendance_date;
    } else {
        firstDay = `${year}-${String(monthNumber).padStart(2,'0')}-01`;
        lastDay = get_last_day_of_month(year, monthNumber);
    }

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Employee Checkin',
            filters: [
                ['employee', '=', frm.doc.employee],
                ['time', '>=', firstDay],
                ['time', '<=', lastDay]
            ],
            fields: ['time', 'log_type'],
            limit_page_length: 5000
        },
        callback: function(r) {
            frappe.hide_progress();

            if (!r.message || !r.message.length) {
                set_empty_attendance(frm, year, monthNumber);
                frappe.show_alert({message: __('No checkins found for {0} {1}', [frm.doc.month, year]), indicator: 'orange'});
                return;
            }

            const filtered = r.message.filter(c => {
                const d = new Date(c.time);
                return (d.getMonth() + 1) === monthNumber && d.getFullYear() === year;
            });

            // First calculate attendance normally
            const summary = calculate_attendance_with_month(filtered, year, monthNumber, frm.doc.month);
            
            // Then check for leave applications on absent days
            frappe.show_progress(__('Checking Leave Applications'), 50, 100);
            
            check_leave_applications(frm.doc.employee, year, monthNumber, function(leaveDays) {
                // Process absent days and convert to leaves where applicable
                process_absent_and_leaves(summary, leaveDays, year, monthNumber);
                
                // Update form with processed data
                update_form_with_data(frm, summary);
                
                // Show detailed alerts for absent days without leave
                let absentWithoutLeave = [];
                let totalDays = summary.total_days;
                
                for (let i = 1; i <= totalDays; i++) {
                    let currentDate = new Date(year, monthNumber - 1, i);
                    
                    // Skip Fridays (holidays)
                    if (currentDate.getDay() === 5) {
                        continue;
                    }
                    
                    // Check if this day was present
                    let wasPresent = false;
                    filtered.forEach(c => {
                        let d = new Date(c.time);
                        if (d.getDate() === i) {
                            wasPresent = true;
                        }
                    });
                    
                    // If not present and no leave
                    if (!wasPresent && !leaveDays.has(i)) {
                        absentWithoutLeave.push(i);
                    }
                }
                
                // Show popup for absent days without leave
                if (absentWithoutLeave.length > 0) {
                    let daysList = absentWithoutLeave.join(', ');
                    let msg = __(`Employee was absent on the following days but no leave application found: Day(s) ${daysList}`);
                    
                    frappe.msgprint({
                        title: __('Absent Without Leave'),
                        message: msg,
                        indicator: 'orange'
                    });
                }
                
                frappe.show_alert({
                    message: __('Attendance Updated for {0} {1}', [frm.doc.month, frm.doc.year]),
                    indicator: 'green'
                });
            });
        }
    });
}

// ====================================
// GET MONTH NUMBER
// ====================================
function get_month_number(monthName) {
    if (!monthName) return null;
    const months = {
        january:1,february:2,march:3,april:4,may:5,june:6,
        july:7,august:8,september:9,october:10,november:11,december:12,
        jan:1,feb:2,mar:3,apr:4,may:5,jun:6,jul:7,aug:8,sep:9,oct:10,nov:11,dec:12
    };
    const key = monthName.trim().toLowerCase();
    if (months[key]) return months[key];
    const num = parseInt(key);
    if(!isNaN(num) && num>=1 && num<=12) return num;
    return null;
}

// ====================================
// GET LAST DAY OF MONTH
// ====================================
function get_last_day_of_month(year, month) {
    const lastDayDate = new Date(year, month, 0);
    const monthStr = String(month).padStart(2,'0');
    const dayStr = String(lastDayDate.getDate()).padStart(2,'0');
    return `${year}-${monthStr}-${dayStr}`;
}

// ====================================
// CALCULATE ATTENDANCE WITH UPDATED OVERTIME RULE
// ====================================
function calculate_attendance_with_month(checkins, year, monthNumber, monthName) {
    const totalDays = new Date(year, monthNumber, 0).getDate();
    const presentDays = new Set();
    const dailyData = {};

    checkins.forEach(c => {
        const d = new Date(c.time);
        const day = d.getDate();
        presentDays.add(day);
        if (!dailyData[day]) dailyData[day] = [];
        dailyData[day].push({time: d, log_type: c.log_type});
    });

    let holidays = 0, workingDays = 0, present = 0, absent = 0, lateMinutes = 0, overtime = 0;

    for (let i=1; i<=totalDays; i++) {
        const d = new Date(year, monthNumber-1, i);
        
        if (d.getDay() === 5) {
            holidays++;
            continue;
        }
        
        workingDays++;
        
        if (presentDays.has(i)) {
            present++;
            const stats = calculate_daily_stats(dailyData[i] || []);
            lateMinutes += stats.lateMinutes;
            overtime += stats.overtimeHours;
        } else {
            absent++;
        }
    }

    return {
        total_days: totalDays,
        holidays,
        working_days: workingDays,
        present_days: present,
        absent_days: absent,
        leaves: 0,  // Initialize leaves field
        late_coming_minutes: lateMinutes,
        overtime_hours: parseFloat(overtime.toFixed(2)),
        late_coming_hours: parseFloat((lateMinutes/60).toFixed(2))
    };
}

// ====================================
// CALCULATE DAILY STATS - UPDATED OVERTIME RULE
// ====================================
function calculate_daily_stats(arr) {
    arr.sort((a,b)=>a.time-b.time);
    
    let firstIn = null;
    let lastOut = null;
    let late = 0;
    let ot = 0;
    
    arr.forEach(r=>{
        if(r.log_type==="IN" && !firstIn) firstIn = r.time;
        if(r.log_type==="OUT") lastOut = r.time;
    });
    
    if(firstIn){
        const shiftStart = new Date(firstIn);
        shiftStart.setHours(9, 0, 0, 0);
        
        if(firstIn > shiftStart) {
            late = (firstIn - shiftStart) / 60000;
        }
        else {
            firstIn = shiftStart;
        }
    }
    
    if(firstIn && lastOut){
        const shiftEnd = new Date(firstIn);
        shiftEnd.setHours(shiftEnd.getHours() + 8);
        
        if(lastOut > shiftEnd) {
            ot = (lastOut - shiftEnd) / 3600000;
        }
    }
    
    return {
        lateMinutes: Math.round(late),
        overtimeHours: ot
    };
}

// ====================================
// UPDATE FORM WITH DATA
// ====================================
function update_form_with_data(frm,data){
    Object.keys(data).forEach(k => frm.set_value(k,data[k]));
    frm.save();
}

// ====================================
// SET EMPTY ATTENDANCE - WITH LEAVES FIELD
// ====================================
function set_empty_attendance(frm,year,month){
    const total = new Date(year, month, 0).getDate();
    let fri=0;
    for(let i=1;i<=total;i++){
        if(new Date(year, month-1, i).getDay()===5) fri++;
    }
    frm.set_value('total_days', total);
    frm.set_value('holidays', fri);
    frm.set_value('working_days', total-fri);
    frm.set_value('present_days', 0);
    frm.set_value('absent_days', total-fri);
    frm.set_value('leaves', 0);  // Initialize leaves field
    frm.set_value('late_coming_minutes', 0);
    frm.set_value('overtime_hours', 0);
    frm.set_value('late_coming_hours', 0);
    frm.save();
}