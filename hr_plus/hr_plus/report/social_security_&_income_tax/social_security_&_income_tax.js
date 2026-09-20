frappe.query_reports["Social Security Income Tax"] = {
    "filters": [
        {
            "fieldname": "month",
            "label": __("Month"),
            "fieldtype": "Link",
            "options": "Month",
            "reqd": 0,
            "description": __("Select specific month (optional)")
        },
        {
            "fieldname": "year",
            "label": __("Year"),
            "fieldtype": "Link",
            "options": "Year",
            "reqd": 0,
            "description": __("Select specific year (optional)")
        },
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 0
        },
        {
            "fieldname": "department",
            "label": __("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "reqd": 0,
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                return {
                    filters: { 'company': company }
                }
            }
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "reqd": 0,
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                var department = frappe.query_report.get_filter_value('department');
                var filters = { 'status': 'Active' };
                if (company) filters['company'] = company;
                if (department) filters['department'] = department;
                return { filters: filters }
            }
        },
        {
            "fieldname": "docstatus",
            "label": __("Salary Slip Status"),
            "fieldtype": "Select",
            "options": [
                "All",
                "Draft",
                "Submitted",
                "Cancelled"
            ],
            "default": "Submitted",
            "reqd": 0
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        // Salary Slip Link
        if (column.fieldname == "salary_slip" && data) {
            value = `<a href="/app/salary-slip/${data.salary_slip}" target="_blank">${data.salary_slip}</a>`;
        }
        
        // Status Color
        if (column.fieldname == "status" && data) {
            if (data.status == "Submitted") {
                value = `<span class="label label-success">${value}</span>`;
            } else if (data.status == "Draft") {
                value = `<span class="label label-warning">${value}</span>`;
            } else if (data.status == "Cancelled") {
                value = `<span class="label label-danger">${value}</span>`;
            }
        }
        
        if (value === undefined || value === null || value === "" || value === "NaN" || String(value).includes("NaN")) {
            value = "0.00";
        }
        
        if (column.fieldtype == "Currency") {
            let num = flt(data ? data[column.fieldname] : 0);
            if (isNaN(num)) num = 0;
            value = format_currency(num, frappe.boot.sysdefaults.currency);
        }
        
        // Social Security - Green
        if (column.fieldname == "social_security") {
            let num = data ? flt(data.social_security) : 0;
            if (isNaN(num)) num = 0;
            value = `<span style="color: #2e7d32; font-weight: 500;">${format_currency(num, frappe.boot.sysdefaults.currency)}</span>`;
        }
        
        // Income Tax - Red
        if (column.fieldname == "income_tax") {
            let num = data ? flt(data.income_tax) : 0;
            if (isNaN(num)) num = 0;
            value = `<span style="color: #c62828; font-weight: 500;">${format_currency(num, frappe.boot.sysdefaults.currency)}</span>`;
        }
        
        // ?? Employee Total - Purple
        if (column.fieldname == "employee_total") {
            let num = data ? flt(data.employee_total) : 0;
            if (isNaN(num)) num = 0;
            value = `<b style="color: #6a1b9a; font-size: 12px;">${format_currency(num, frappe.boot.sysdefaults.currency)}</b>`;
        }
        
        // Total Row - Bold
        if (data && data.employee == "TOTAL") {
            if (column.fieldname == "employee") {
                value = `<b>${value}</b>`;
            }
            if (column.fieldtype == "Currency") {
                value = `<b style="font-size: 12px;">${value}</b>`;
            }
        }
        
        return value;
    },

    "get_summary": function(data) {
        if (!data || data.length === 0) {
            return [
                { "label": __("Total Employees"), "value": 0, "indicator": "Blue", "datatype": "Int" },
                { "label": __("Total Salary Slips"), "value": 0, "indicator": "Blue", "datatype": "Int" },
                { "label": __("Total Social Security"), "value": 0, "indicator": "Green", "datatype": "Currency" },
                { "label": __("Total Income Tax"), "value": 0, "indicator": "Red", "datatype": "Currency" },
                { "label": __("Total Deduction"), "value": 0, "indicator": "Purple", "datatype": "Currency" }
            ];
        }
        
        let total_employees = new Set();
        let total_slips = 0;
        let total_ss = 0, total_it = 0;
        
        data.forEach(row => {
            if (row.employee && row.employee != "TOTAL") {
                total_employees.add(row.employee);
                total_slips++;
                total_ss += flt(row.social_security);
                total_it += flt(row.income_tax);
            }
        });
        
        return [
            { "label": __("Total Employees"), "value": total_employees.size, "indicator": "Blue", "datatype": "Int" },
            { "label": __("Total Salary Slips"), "value": total_slips, "indicator": "Blue", "datatype": "Int" },
            { "label": __("Total Social Security"), "value": total_ss, "indicator": "Green", "datatype": "Currency" },
            { "label": __("Total Income Tax"), "value": total_it, "indicator": "Red", "datatype": "Currency" },
            { "label": __("Total Deduction"), "value": total_ss + total_it, "indicator": "Purple", "datatype": "Currency" }
        ];
    },

    "onload": function(report) {
        // Export buttons
        report.page.add_inner_button(__("Export to Excel"), function() {
            frappe.query_report.export_report("Excel");
        });
        
        report.page.add_inner_button(__("Export to CSV"), function() {
            frappe.query_report.export_report("CSV");
        });
        
        // Clear Filters
        report.page.add_inner_button(__("Clear Filters"), function() {
            frappe.query_report.set_filter_value({
                "month": "",
                "year": "",
                "company": "",
                "department": "",
                "employee": "",
                "docstatus": "Submitted"
            });
            frappe.query_report.refresh();
        });
        
        // ?? Tax Summary Button
        report.page.add_inner_button(__("Tax Summary"), function() {
            let total_ss = 0, total_it = 0, total_emp = 0;
            let data = frappe.query_report.data;
            
            data.forEach(row => {
                if (row.employee && row.employee != "TOTAL") {
                    total_emp++;
                    total_ss += flt(row.social_security);
                    total_it += flt(row.income_tax);
                }
            });
            
            frappe.msgprint({
                title: __("Tax Deduction Summary"),
                message: `
                    <div style="padding: 10px;">
                        <h4 style="color: #1a7ea8; margin-bottom: 20px;">SOCIAL SECURITY & INCOME TAX</h4>
                        <table class="table table-bordered">
                            <tr>
                                <th style="width: 60%">Description</th>
                                <th style="width: 40%">Amount</th>
                            </tr>
                            <tr>
                                <td>Total Employees</td>
                                <td><b>${total_emp}</b></td>
                            </tr>
                            <tr>
                                <td>Total Social Security (CNSS) - 6%</td>
                                <td><b style="color: #2e7d32;">${format_currency(total_ss, frappe.boot.sysdefaults.currency)}</b></td>
                            </tr>
                            <tr>
                                <td>Total Income Tax (ITS)</td>
                                <td><b style="color: #c62828;">${format_currency(total_it, frappe.boot.sysdefaults.currency)}</b></td>
                            </tr>
                            <tr style="background-color: #f5f5f5;">
                                <td><b>Total Tax Deduction</b></td>
                                <td><b style="color: #6a1b9a;">${format_currency(total_ss + total_it, frappe.boot.sysdefaults.currency)}</b></td>
                            </tr>
                        </table>
                    </div>
                `
            });
        });
        
        // ?? Department Summary Button
        report.page.add_inner_button(__("Department Summary"), function() {
            let depts = {};
            let data = frappe.query_report.data;
            
            data.forEach(row => {
                if (row.employee && row.employee != "TOTAL") {
                    let dept = row.department || "Other";
                    if (!depts[dept]) {
                        depts[dept] = { ss: 0, it: 0, count: 0 };
                    }
                    depts[dept].ss += flt(row.social_security);
                    depts[dept].it += flt(row.income_tax);
                    depts[dept].count++;
                }
            });
            
            let html = `
                <div style="padding: 10px;">
                    <h4 style="color: #1a7ea8; margin-bottom: 20px;">Department Wise Summary</h4>
                    <table class="table table-bordered">
                        <tr>
                            <th>Department</th>
                            <th>Employees</th>
                            <th>Social Security</th>
                            <th>Income Tax</th>
                            <th>Total</th>
                        </tr>
            `;
            
            Object.keys(depts).sort().forEach(dept => {
                html += `<tr>
                    <td><b>${dept}</b></td>
                    <td>${depts[dept].count}</td>
                    <td style="color: #2e7d32;">${format_currency(depts[dept].ss, frappe.boot.sysdefaults.currency)}</td>
                    <td style="color: #c62828;">${format_currency(depts[dept].it, frappe.boot.sysdefaults.currency)}</td>
                    <td><b>${format_currency(depts[dept].ss + depts[dept].it, frappe.boot.sysdefaults.currency)}</b></td>
                </tr>`;
            });
            
            html += `</table></div>`;
            
            frappe.msgprint({
                title: __("Department Summary"),
                message: html,
                wide: true
            });
        });
    }
};

// Helper functions
function flt(value) {
    if (value === undefined || value === null || value === "") return 0;
    let num = parseFloat(value);
    return isNaN(num) ? 0 : num;
}

function format_currency(value, currency) {
    let num = flt(value);
    return new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency: currency || 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(num);
}