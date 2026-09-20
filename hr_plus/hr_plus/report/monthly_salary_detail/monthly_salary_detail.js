frappe.query_reports["MONTHLY SALARY DETAIL"] = {
    "filters": [
        {
            "fieldname": "component_filter",
            "label": __("Component Filter"),
            "fieldtype": "Select",
            "options": [
                "All Components",
                "Earning Components",
                "Deduction Components",
                "Social Security",
                "Income Tax"
            ],
            "default": "All Components",
            "reqd": 1,
            "description": __("Select which components to display")
        },
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
            "reqd": 0,
            "description": __("Select company (optional)")
        },
        {
            "fieldname": "employee",
            "label": __("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "reqd": 0,
            "get_query": function() {
                var company = frappe.query_report.get_filter_value('company');
                var filters = { 'status': 'Active' };
                if (company) {
                    filters['company'] = company;
                }
                return { filters: filters }
            },
            "description": __("Select employee (optional)")
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
            "reqd": 0,
            "description": __("Select salary slip status (optional)")
        }
    ],

    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        var component_filter = frappe.query_report.get_filter_value('component_filter') || 'All Components';
        
        // Salary Slip Link
        if (column.fieldname == "salary_slip" && data) {
            value = `<a href="/app/salary-slip/${data.salary_slip}" target="_blank">${data.salary_slip}</a>`;
        }
        
        if (value === undefined || value === null || value === "" || value === "NaN" || String(value).includes("NaN")) {
            value = "0.00";
        }
        
        if (column.fieldtype == "Currency") {
            let num = 0;
            if (data && data[column.fieldname] !== undefined && data[column.fieldname] !== null) {
                num = flt(data[column.fieldname]);
            }
            if (isNaN(num)) num = 0;
            value = format_currency(num, frappe.boot.sysdefaults.currency);
        }
        
        // Section Headers - Only for All Components
        if (component_filter == "All Components") {
            if (column.fieldname == "earning_header") {
                value = `<b style="color: #1a7ea8; font-size: 12px;">?? EARNINGS COMPONENTS</b>`;
            }
            if (column.fieldname == "deduction_header") {
                value = `<b style="color: #1a7ea8; font-size: 12px;">?? DEDUCTION COMPONENTS</b>`;
            }
        }
        
        // Status Color
        if (column.fieldname == "status") {
            if (value == "Submitted") {
                value = `<span class="label label-success">${value}</span>`;
            } else if (value == "Draft") {
                value = `<span class="label label-warning">${value}</span>`;
            } else if (value == "Cancelled") {
                value = `<span class="label label-danger">${value}</span>`;
            }
        }
        
        // Earnings - Green
        if (["basic", "gratuity", "leave_encashment", "over_time_150", "over_time_125", 
             "over_time_175", "over_time_basic", "overtime", "additional_salary", 
             "seniority_allowance", "thank_you_allowance", "special_allowance", 
             "arrear", "appraisal"].includes(column.fieldname)) {
            let num = data ? flt(data[column.fieldname]) : 0;
            if (isNaN(num)) num = 0;
            value = `<span style="color: #2e7d32; font-weight: 500;">${format_currency(num, frappe.boot.sysdefaults.currency)}</span>`;
        }
        
        // Total Earnings - Bold Green
        if (column.fieldname == "total_earnings") {
            let num = data ? flt(data.total_earnings) : 0;
            if (isNaN(num)) num = 0;
            value = `<b style="color: #2e7d32; font-size: 12px;">${format_currency(num, frappe.boot.sysdefaults.currency)}</b>`;
        }
        
        // Deductions - Red
        if (["employee_advance_deduction", "income_tax", "social_security", "penalty_2", 
             "penalty_1", "absent_deduction", "late_entry", "waqf", "loan", 
             "advance"].includes(column.fieldname)) {
            let num = data ? flt(data[column.fieldname]) : 0;
            if (isNaN(num)) num = 0;
            value = `<span style="color: #c62828; font-weight: 500;">${format_currency(num, frappe.boot.sysdefaults.currency)}</span>`;
        }
        
        // Total Deductions - Bold Red
        if (column.fieldname == "total_deductions") {
            let num = data ? flt(data.total_deductions) : 0;
            if (isNaN(num)) num = 0;
            value = `<b style="color: #c62828; font-size: 12px;">${format_currency(num, frappe.boot.sysdefaults.currency)}</b>`;
        }
        
        // Social Security - Bold Blue (only for Social Security filter)
        if (column.fieldname == "social_security" && component_filter == "Social Security") {
            let num = data ? flt(data.social_security) : 0;
            if (isNaN(num)) num = 0;
            value = `<b style="color: #0b5e8a; font-size: 13px;">${format_currency(num, frappe.boot.sysdefaults.currency)}</b>`;
        }
        
        // Income Tax - Bold Blue (only for Income Tax filter)
        if (column.fieldname == "income_tax" && component_filter == "Income Tax") {
            let num = data ? flt(data.income_tax) : 0;
            if (isNaN(num)) num = 0;
            value = `<b style="color: #0b5e8a; font-size: 13px;">${format_currency(num, frappe.boot.sysdefaults.currency)}</b>`;
        }
        
        // Net Pay - Bold Blue (Only for All Components)
        if (column.fieldname == "net_pay" && component_filter == "All Components") {
            let num = data ? flt(data.net_pay) : 0;
            if (isNaN(num)) num = 0;
            value = `<b style="color: #0b5e8a; font-size: 13px;">${format_currency(num, frappe.boot.sysdefaults.currency)}</b>`;
        }
        
        // Rounded Total - Bold Purple (Only for All Components)
        if (column.fieldname == "rounded_total" && component_filter == "All Components") {
            let num = data ? flt(data.rounded_total) : 0;
            if (isNaN(num)) num = 0;
            value = `<b style="color: #6a1b9a; font-size: 13px;">${format_currency(num, frappe.boot.sysdefaults.currency)}</b>`;
        }
        
        return value;
    },

    "get_summary": function(data) {
        if (!data || data.length === 0) {
            return [
                { "label": __("Total Salary Slips"), "value": 0, "indicator": "Blue", "datatype": "Int" }
            ];
        }
        
        var component_filter = frappe.query_report.get_filter_value('component_filter') || 'All Components';
        
        let total_employees = new Set();
        let total_earnings = 0, total_deductions = 0, total_net = 0, total_rounded = 0;
        let total_social_security = 0, total_income_tax = 0;
        
        data.forEach(row => {
            if (row.employee && row.employee != "TOTAL") {
                total_employees.add(row.employee);
                
                if (component_filter == "Earning Components") {
                    total_earnings += flt(row.total_earnings);
                } else if (component_filter == "Deduction Components") {
                    total_deductions += flt(row.total_deductions);
                } else if (component_filter == "Social Security") {
                    total_social_security += flt(row.social_security);
                } else if (component_filter == "Income Tax") {
                    total_income_tax += flt(row.income_tax);
                } else if (component_filter == "All Components") {
                    total_earnings += flt(row.total_earnings);
                    total_deductions += flt(row.total_deductions);
                    total_net += flt(row.net_pay);
                    total_rounded += flt(row.rounded_total);
                }
            }
        });
        
        let summary = [
            { "label": __("Total Employees"), "value": total_employees.size, "indicator": "Blue", "datatype": "Int" },
            { "label": __("Total Salary Slips"), "value": data.length - 1, "indicator": "Blue", "datatype": "Int" }
        ];
        
        if (component_filter == "Earning Components") {
            summary.push({ "label": __("Total Earnings"), "value": total_earnings, "indicator": "Green", "datatype": "Currency" });
        } else if (component_filter == "Deduction Components") {
            summary.push({ "label": __("Total Deductions"), "value": total_deductions, "indicator": "Red", "datatype": "Currency" });
        } else if (component_filter == "Social Security") {
            summary.push({ "label": __("Total Social Security"), "value": total_social_security, "indicator": "Blue", "datatype": "Currency" });
        } else if (component_filter == "Income Tax") {
            summary.push({ "label": __("Total Income Tax"), "value": total_income_tax, "indicator": "Blue", "datatype": "Currency" });
        } else if (component_filter == "All Components") {
            summary.push(
                { "label": __("Total Earnings"), "value": total_earnings, "indicator": "Green", "datatype": "Currency" },
                { "label": __("Total Deductions"), "value": total_deductions, "indicator": "Red", "datatype": "Currency" },
                { "label": __("Total Net Pay"), "value": total_net, "indicator": "Blue", "datatype": "Currency" },
                { "label": __("Total Rounded"), "value": total_rounded, "indicator": "Purple", "datatype": "Currency" }
            );
        }
        
        return summary;
    },

    "onload": function(report) {
        report.page.add_inner_button(__("Export to Excel"), function() {
            frappe.query_report.export_report("Excel");
        });
        
        // Clear filters button
        report.page.add_inner_button(__("Clear Filters"), function() {
            frappe.query_report.set_filter_value({
                "component_filter": "All Components",
                "month": "",
                "year": "",
                "company": "",
                "employee": "",
                "docstatus": "Submitted"
            });
            frappe.query_report.refresh();
        });
    }
};

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