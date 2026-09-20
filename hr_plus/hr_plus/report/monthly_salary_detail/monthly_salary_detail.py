import frappe
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime
from collections import defaultdict
import calendar

def execute(filters=None):
    if not filters:
        filters = frappe._dict()
    
    # Get component filter type
    component_filter = filters.get("component_filter", "All Components")
    
    columns = get_columns(component_filter)
    data = get_data(filters, component_filter)
    
    # Add total row
    if data:
        total_row = get_total_row(data, component_filter)
        data.append(total_row)
    
    summary = get_summary(data, component_filter)
    
    return columns, data, None, None, summary

def get_columns(component_filter):
    columns = []
    
    # Employee Info - Always show these
    columns.append({"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120})
    columns.append({"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180})
    columns.append({"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 180})
    columns.append({"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100})
    columns.append({"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 100})
    columns.append({"label": _("Year"), "fieldname": "year", "fieldtype": "Data", "width": 100})
    columns.append({"label": _("Start Date"), "fieldname": "start_date", "fieldtype": "Date", "width": 100})
    columns.append({"label": _("End Date"), "fieldname": "end_date", "fieldtype": "Date", "width": 100})
    
    # Earning Components
    if component_filter == "Earning Components":
        earnings_fields = [
            "basic", "gratuity", "leave_encashment", "over_time_150", "over_time_125",
            "over_time_175", "over_time_basic", "overtime", "additional_salary",
            "seniority_allowance", "thank_you_allowance", "special_allowance",
            "arrear", "appraisal"
        ]
        
        earnings_labels = [
            "Basic", "Gratuity", "Leave Encashment", "OT 150%", "OT 125%",
            "OT 175%", "OT Basic", "Overtime", "Additional Salary",
            "Seniority", "Thank You", "Special",
            "Arrear", "Appraisal"
        ]
        
        for i, field in enumerate(earnings_fields):
            columns.append({
                "label": _(earnings_labels[i]),
                "fieldname": field,
                "fieldtype": "Currency",
                "width": 110
            })
        
        # Total Earnings only - No header column
        columns.append({"label": _("TOTAL EARNINGS"), "fieldname": "total_earnings", "fieldtype": "Currency", "width": 130})
    
    # Deduction Components
    elif component_filter == "Deduction Components":
        deductions_fields = [
            "employee_advance_deduction", "income_tax", "social_security", "penalty_2",
            "penalty_1", "absent_deduction", "late_entry", "waqf", "loan", "advance"
        ]
        
        deductions_labels = [
            "Emp Advance", "Income Tax", "Social Sec", "Penalty 2",
            "Penalty 1", "Absent", "Late Entry", "Waqf", "Loan", "Advance"
        ]
        
        for i, field in enumerate(deductions_fields):
            columns.append({
                "label": _(deductions_labels[i]),
                "fieldname": field,
                "fieldtype": "Currency",
                "width": 110
            })
        
        # Total Deductions only - No header column
        columns.append({"label": _("TOTAL DEDUCTIONS"), "fieldname": "total_deductions", "fieldtype": "Currency", "width": 130})
    
    # Social Security Only
    elif component_filter == "Social Security":
        columns.append({
            "label": _("Social Security"),
            "fieldname": "social_security",
            "fieldtype": "Currency",
            "width": 150
        })
        # No total column - just the component
    
    # Income Tax Only
    elif component_filter == "Income Tax":
        columns.append({
            "label": _("Income Tax"),
            "fieldname": "income_tax",
            "fieldtype": "Currency",
            "width": 150
        })
        # No total column - just the component
    
    # All Components
    elif component_filter == "All Components":
        # Earnings Header
        columns.append({"label": _(""), "fieldname": "earning_header", "fieldtype": "Data", "width": 30})
        
        earnings_fields = [
            "basic", "gratuity", "leave_encashment", "over_time_150", "over_time_125",
            "over_time_175", "over_time_basic", "overtime", "additional_salary",
            "seniority_allowance", "thank_you_allowance", "special_allowance",
            "arrear", "appraisal"
        ]
        
        earnings_labels = [
            "Basic", "Gratuity", "Leave Encashment", "OT 150%", "OT 125%",
            "OT 175%", "OT Basic", "Overtime", "Additional Salary",
            "Seniority", "Thank You", "Special",
            "Arrear", "Appraisal"
        ]
        
        for i, field in enumerate(earnings_fields):
            columns.append({
                "label": _(earnings_labels[i]),
                "fieldname": field,
                "fieldtype": "Currency",
                "width": 110
            })
        
        columns.append({"label": _("TOTAL EARNINGS"), "fieldname": "total_earnings", "fieldtype": "Currency", "width": 130})
        
        # Deductions Header
        columns.append({"label": _(""), "fieldname": "deduction_header", "fieldtype": "Data", "width": 30})
        
        deductions_fields = [
            "employee_advance_deduction", "income_tax", "social_security", "penalty_2",
            "penalty_1", "absent_deduction", "late_entry", "waqf", "loan", "advance"
        ]
        
        deductions_labels = [
            "Emp Advance", "Income Tax", "Social Sec", "Penalty 2",
            "Penalty 1", "Absent", "Late Entry", "Waqf", "Loan", "Advance"
        ]
        
        for i, field in enumerate(deductions_fields):
            columns.append({
                "label": _(deductions_labels[i]),
                "fieldname": field,
                "fieldtype": "Currency",
                "width": 110
            })
        
        columns.append({"label": _("TOTAL DEDUCTIONS"), "fieldname": "total_deductions", "fieldtype": "Currency", "width": 130})
        
        # Net Pay and Rounded Total - Only for All Components
        columns.append({"label": _("NET PAY"), "fieldname": "net_pay", "fieldtype": "Currency", "width": 130})
        columns.append({"label": _("Rounded Total"), "fieldname": "rounded_total", "fieldtype": "Currency", "width": 130})
    
    return columns

def get_data(filters, component_filter):
    # Month/Year mapping
    month_num = None
    year_num = None
    first_day = None
    last_day = None
    
    month_map = {
        "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
        "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12,
        "01": 1, "02": 2, "03": 3, "04": 4, "05": 5, "06": 6,
        "07": 7, "08": 8, "09": 9, "10": 10, "11": 11, "12": 12,
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
    }
    
    if filters.get("month"):
        month_num = month_map.get(str(filters.month))
    
    if filters.get("year"):
        try:
            year_num = int(str(filters.year))
        except:
            year_num = None
    
    if month_num and year_num:
        first_day = datetime(year_num, month_num, 1).date()
        last_day = datetime(year_num, month_num, calendar.monthrange(year_num, month_num)[1]).date()
    
    # Status filter
    docstatus_condition = ""
    if filters.get("docstatus"):
        if filters.docstatus == "Draft":
            docstatus_condition = "AND ss.docstatus = 0"
        elif filters.docstatus == "Submitted":
            docstatus_condition = "AND ss.docstatus = 1"
        elif filters.docstatus == "Cancelled":
            docstatus_condition = "AND ss.docstatus = 2"
        else:
            docstatus_condition = ""
    else:
        docstatus_condition = "AND ss.docstatus = 1"
    
    conditions = []
    values = []
    
    if filters.get("company"):
        conditions.append("ss.company = %s")
        values.append(filters.company)
    
    if first_day and last_day:
        conditions.append("ss.start_date BETWEEN %s AND %s")
        values.append(first_day)
        values.append(last_day)
    else:
        if year_num:
            conditions.append("YEAR(ss.start_date) = %s")
            values.append(year_num)
        
        if month_num and not year_num:
            conditions.append("MONTH(ss.start_date) = %s")
            values.append(month_num)
    
    if filters.get("employee"):
        conditions.append("ss.employee = %s")
        values.append(filters.employee)
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    query = f"""
        SELECT 
            ss.name as salary_slip,
            ss.employee,
            ss.employee_name,
            ss.start_date,
            ss.end_date,
            ss.status,
            ss.docstatus,
            ss.rounded_total,
            e.date_of_joining,
            MONTH(ss.start_date) as month_number,
            YEAR(ss.start_date) as year_number
        FROM `tabSalary Slip` ss
        LEFT JOIN `tabEmployee` e ON ss.employee = e.name
        {where_clause}
        {docstatus_condition}
        ORDER BY ss.start_date DESC, ss.employee_name
    """
    
    if values:
        salary_slips = frappe.db.sql(query, tuple(values), as_dict=1)
    else:
        salary_slips = frappe.db.sql(query, as_dict=1)
    
    if not salary_slips:
        msg = "No Salary Slips found"
        if month_num and year_num:
            msg += f" for {filters.month} {year_num}"
        elif year_num:
            msg += f" for Year {year_num}"
        elif month_num:
            msg += f" for Month {filters.month}"
        frappe.msgprint(_(msg))
        return []
    
    result = []
    
    for slip in salary_slips:
        row = frappe._dict()
        
        # Basic info
        row.employee = slip.employee or ""
        row.employee_name = slip.employee_name or ""
        row.salary_slip = slip.salary_slip
        row.status = slip.status or get_docstatus_text(slip.docstatus)
        row.start_date = slip.start_date
        row.end_date = slip.end_date
        row.month = slip.month_number
        row.year = slip.year_number
        row.rounded_total = flt(slip.rounded_total)
        
        # Get components
        earnings = get_earnings(slip.salary_slip)
        deductions = get_deductions(slip.salary_slip)
        
        # Earnings components
        row.basic = flt(earnings.get("Basic", 0))
        row.gratuity = flt(earnings.get("Gratuity", 0))
        row.leave_encashment = flt(earnings.get("Leave Encashment", 0))
        row.over_time_150 = flt(earnings.get("Over Time 150%", 0))
        row.over_time_125 = flt(earnings.get("Over Time 125%", 0))
        row.over_time_175 = flt(earnings.get("Over Time 175%", 0))
        row.over_time_basic = flt(earnings.get("Over Time Basic", 0))
        row.overtime = flt(earnings.get("Overtime", 0))
        row.additional_salary = flt(earnings.get("Additional Salary", 0))
        row.seniority_allowance = flt(earnings.get("Seniority Allowance", 0))
        row.thank_you_allowance = flt(earnings.get("Thank You Allowance", 0))
        row.special_allowance = flt(earnings.get("Special Allowance", 0))
        row.arrear = flt(earnings.get("Arrear", 0))
        row.appraisal = flt(earnings.get("Appraisal", 0))
        
        # Total Earnings
        row.total_earnings = (
            row.basic + row.gratuity + row.leave_encashment +
            row.over_time_150 + row.over_time_125 + row.over_time_175 +
            row.over_time_basic + row.overtime + row.additional_salary +
            row.seniority_allowance + row.thank_you_allowance +
            row.special_allowance + row.arrear + row.appraisal
        )
        
        # Deductions components
        row.employee_advance_deduction = flt(deductions.get("Employee advance deduction", 0))
        row.income_tax = flt(deductions.get("Income Tax", 0))
        row.social_security = flt(deductions.get("Social Security", 0))
        row.penalty_2 = flt(deductions.get("Penalty 2", 0))
        row.penalty_1 = flt(deductions.get("Penalty 1", 0))
        row.absent_deduction = flt(deductions.get("Absent Deduction", 0))
        row.late_entry = flt(deductions.get("Late Entry", 0))
        row.waqf = flt(deductions.get("Waqf", 0))
        row.loan = flt(deductions.get("Loan", 0))
        row.advance = flt(deductions.get("Advance", 0))
        
        # Total Deductions
        row.total_deductions = (
            row.employee_advance_deduction + row.income_tax + row.social_security +
            row.penalty_2 + row.penalty_1 + row.absent_deduction +
            row.late_entry + row.waqf + row.loan + row.advance
        )
        
        # Net Pay - Only calculate for All Components
        if component_filter == "All Components":
            row.net_pay = row.total_earnings - row.total_deductions
        
        result.append(row)
    
    return result

def get_total_row(data, component_filter):
    total = frappe._dict()
    
    total.employee = "TOTAL"
    total.employee_name = ""
    total.salary_slip = ""
    total.status = ""
    total.month = ""
    total.year = ""
    total.start_date = ""
    total.end_date = ""
    
    # Earnings Totals
    if component_filter == "Earning Components":
        total.basic = sum([flt(d.basic) for d in data])
        total.gratuity = sum([flt(d.gratuity) for d in data])
        total.leave_encashment = sum([flt(d.leave_encashment) for d in data])
        total.over_time_150 = sum([flt(d.over_time_150) for d in data])
        total.over_time_125 = sum([flt(d.over_time_125) for d in data])
        total.over_time_175 = sum([flt(d.over_time_175) for d in data])
        total.over_time_basic = sum([flt(d.over_time_basic) for d in data])
        total.overtime = sum([flt(d.overtime) for d in data])
        total.additional_salary = sum([flt(d.additional_salary) for d in data])
        total.seniority_allowance = sum([flt(d.seniority_allowance) for d in data])
        total.thank_you_allowance = sum([flt(d.thank_you_allowance) for d in data])
        total.special_allowance = sum([flt(d.special_allowance) for d in data])
        total.arrear = sum([flt(d.arrear) for d in data])
        total.appraisal = sum([flt(d.appraisal) for d in data])
        total.total_earnings = sum([flt(d.total_earnings) for d in data])
    
    # Deductions Totals
    elif component_filter == "Deduction Components":
        total.employee_advance_deduction = sum([flt(d.employee_advance_deduction) for d in data])
        total.income_tax = sum([flt(d.income_tax) for d in data])
        total.social_security = sum([flt(d.social_security) for d in data])
        total.penalty_2 = sum([flt(d.penalty_2) for d in data])
        total.penalty_1 = sum([flt(d.penalty_1) for d in data])
        total.absent_deduction = sum([flt(d.absent_deduction) for d in data])
        total.late_entry = sum([flt(d.late_entry) for d in data])
        total.waqf = sum([flt(d.waqf) for d in data])
        total.loan = sum([flt(d.loan) for d in data])
        total.advance = sum([flt(d.advance) for d in data])
        total.total_deductions = sum([flt(d.total_deductions) for d in data])
    
    # Social Security Total
    elif component_filter == "Social Security":
        total.social_security = sum([flt(d.social_security) for d in data])
    
    # Income Tax Total
    elif component_filter == "Income Tax":
        total.income_tax = sum([flt(d.income_tax) for d in data])
    
    # All Components
    elif component_filter == "All Components":
        # Earnings Totals
        total.basic = sum([flt(d.basic) for d in data])
        total.gratuity = sum([flt(d.gratuity) for d in data])
        total.leave_encashment = sum([flt(d.leave_encashment) for d in data])
        total.over_time_150 = sum([flt(d.over_time_150) for d in data])
        total.over_time_125 = sum([flt(d.over_time_125) for d in data])
        total.over_time_175 = sum([flt(d.over_time_175) for d in data])
        total.over_time_basic = sum([flt(d.over_time_basic) for d in data])
        total.overtime = sum([flt(d.overtime) for d in data])
        total.additional_salary = sum([flt(d.additional_salary) for d in data])
        total.seniority_allowance = sum([flt(d.seniority_allowance) for d in data])
        total.thank_you_allowance = sum([flt(d.thank_you_allowance) for d in data])
        total.special_allowance = sum([flt(d.special_allowance) for d in data])
        total.arrear = sum([flt(d.arrear) for d in data])
        total.appraisal = sum([flt(d.appraisal) for d in data])
        total.total_earnings = sum([flt(d.total_earnings) for d in data])
        
        # Deductions Totals
        total.employee_advance_deduction = sum([flt(d.employee_advance_deduction) for d in data])
        total.income_tax = sum([flt(d.income_tax) for d in data])
        total.social_security = sum([flt(d.social_security) for d in data])
        total.penalty_2 = sum([flt(d.penalty_2) for d in data])
        total.penalty_1 = sum([flt(d.penalty_1) for d in data])
        total.absent_deduction = sum([flt(d.absent_deduction) for d in data])
        total.late_entry = sum([flt(d.late_entry) for d in data])
        total.waqf = sum([flt(d.waqf) for d in data])
        total.loan = sum([flt(d.loan) for d in data])
        total.advance = sum([flt(d.advance) for d in data])
        total.total_deductions = sum([flt(d.total_deductions) for d in data])
        
        # Net Pay and Rounded Total
        total.net_pay = sum([flt(d.net_pay) for d in data])
        total.rounded_total = sum([flt(d.rounded_total) for d in data])
    
    total.earning_header = ""
    total.deduction_header = ""
    
    return total

def get_earnings(salary_slip):
    earnings = defaultdict(float)
    data = frappe.db.sql("""
        SELECT salary_component, amount
        FROM `tabSalary Detail`
        WHERE parent = %s AND parentfield = 'earnings'
    """, salary_slip, as_dict=1)
    
    for d in data:
        earnings[d.salary_component] = flt(d.amount)
    return earnings

def get_deductions(salary_slip):
    deductions = defaultdict(float)
    data = frappe.db.sql("""
        SELECT salary_component, amount
        FROM `tabSalary Detail`
        WHERE parent = %s AND parentfield = 'deductions'
    """, salary_slip, as_dict=1)
    
    for d in data:
        deductions[d.salary_component] = flt(d.amount)
    return deductions

def get_docstatus_text(docstatus):
    if docstatus == 0:
        return "Draft"
    elif docstatus == 1:
        return "Submitted"
    elif docstatus == 2:
        return "Cancelled"
    return ""

def get_summary(data, component_filter):
    if not data:
        summary = [
            {"label": _("Total Salary Slips"), "value": 0, "indicator": "Blue", "datatype": "Int"},
        ]
        
        if component_filter == "Earning Components":
            summary.append({"label": _("Total Earnings"), "value": 0, "indicator": "Green", "datatype": "Currency"})
        elif component_filter == "Deduction Components":
            summary.append({"label": _("Total Deductions"), "value": 0, "indicator": "Red", "datatype": "Currency"})
        elif component_filter == "Social Security":
            summary.append({"label": _("Total Social Security"), "value": 0, "indicator": "Blue", "datatype": "Currency"})
        elif component_filter == "Income Tax":
            summary.append({"label": _("Total Income Tax"), "value": 0, "indicator": "Blue", "datatype": "Currency"})
        elif component_filter == "All Components":
            summary.extend([
                {"label": _("Total Earnings"), "value": 0, "indicator": "Green", "datatype": "Currency"},
                {"label": _("Total Deductions"), "value": 0, "indicator": "Red", "datatype": "Currency"},
                {"label": _("Total Net Pay"), "value": 0, "indicator": "Blue", "datatype": "Currency"},
                {"label": _("Total Rounded"), "value": 0, "indicator": "Purple", "datatype": "Currency"}
            ])
        
        return summary
    
    data_without_total = [d for d in data if d.get("employee") != "TOTAL"]
    employees = set([d.employee for d in data_without_total if d.employee])
    
    summary = [
        {"label": _("Total Employees"), "value": len(employees), "indicator": "Blue", "datatype": "Int"},
        {"label": _("Total Salary Slips"), "value": len(data_without_total), "indicator": "Blue", "datatype": "Int"},
    ]
    
    if component_filter == "Earning Components":
        total_earnings = sum([flt(d.total_earnings) for d in data_without_total])
        summary.append({"label": _("Total Earnings"), "value": total_earnings, "indicator": "Green", "datatype": "Currency"})
    
    elif component_filter == "Deduction Components":
        total_deductions = sum([flt(d.total_deductions) for d in data_without_total])
        summary.append({"label": _("Total Deductions"), "value": total_deductions, "indicator": "Red", "datatype": "Currency"})
    
    elif component_filter == "Social Security":
        total_social_security = sum([flt(d.social_security) for d in data_without_total])
        summary.append({"label": _("Total Social Security"), "value": total_social_security, "indicator": "Blue", "datatype": "Currency"})
    
    elif component_filter == "Income Tax":
        total_income_tax = sum([flt(d.income_tax) for d in data_without_total])
        summary.append({"label": _("Total Income Tax"), "value": total_income_tax, "indicator": "Blue", "datatype": "Currency"})
    
    elif component_filter == "All Components":
        total_earnings = sum([flt(d.total_earnings) for d in data_without_total])
        total_deductions = sum([flt(d.total_deductions) for d in data_without_total])
        total_net = sum([flt(d.net_pay) for d in data_without_total])
        total_rounded = sum([flt(d.rounded_total) for d in data_without_total])
        
        summary.extend([
            {"label": _("Total Earnings"), "value": total_earnings, "indicator": "Green", "datatype": "Currency"},
            {"label": _("Total Deductions"), "value": total_deductions, "indicator": "Red", "datatype": "Currency"},
            {"label": _("Total Net Pay"), "value": total_net, "indicator": "Blue", "datatype": "Currency"},
            {"label": _("Total Rounded"), "value": total_rounded, "indicator": "Purple", "datatype": "Currency"}
        ])
    
    return summary