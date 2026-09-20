import frappe
from frappe import _
from frappe.utils import flt
from datetime import datetime
from collections import defaultdict
import calendar

def execute(filters=None):
    if not filters:
        filters = frappe._dict()
    
    columns = get_columns()
    data = get_data(filters)
    
    # TOTAL ROW
    if data:
        total_row = get_total_row(data)
        data.append(total_row)
    
    # Dashboard Summary
    summary = get_summary(data)
    
    # Chart
    chart = get_chart(data)
    
    return columns, data, None, chart, summary

def get_columns():
    columns = []
    
    # Employee Details
    columns.append({"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120})
    columns.append({"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 180})
    columns.append({"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 150})
    columns.append({"label": _("Salary Slip"), "fieldname": "salary_slip", "fieldtype": "Link", "options": "Salary Slip", "width": 180})
    columns.append({"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100})
    columns.append({"label": _("Month"), "fieldname": "month", "fieldtype": "Data", "width": 80})
    columns.append({"label": _("Year"), "fieldname": "year", "fieldtype": "Data", "width": 80})
    
    # Deduction Columns
    columns.append({"label": _("Social Security (CNSS)"), "fieldname": "social_security", "fieldtype": "Currency", "width": 150})
    columns.append({"label": _("Income Tax (ITS)"), "fieldname": "income_tax", "fieldtype": "Currency", "width": 150})
    
    # ?? EMPLOYEE TOTAL - ?? ??????? ?? ????? ????? ?? ??????
    columns.append({"label": _("Employee Total"), "fieldname": "employee_total", "fieldtype": "Currency", "width": 150})
    
    return columns

def get_data(filters):
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
    
    # Dynamic WHERE clause
    conditions = []
    values = []
    
    if filters.get("company"):
        conditions.append("ss.company = %s")
        values.append(filters.company)
    
    if filters.get("department"):
        conditions.append("ss.department = %s")
        values.append(filters.department)
    
    if filters.get("employee"):
        conditions.append("ss.employee = %s")
        values.append(filters.employee)
    
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
    
    # Status filter
    if filters.get("docstatus"):
        if filters.docstatus == "Draft":
            conditions.append("ss.docstatus = 0")
        elif filters.docstatus == "Submitted":
            conditions.append("ss.docstatus = 1")
        elif filters.docstatus == "Cancelled":
            conditions.append("ss.docstatus = 2")
        # All - no condition
    else:
        conditions.append("ss.docstatus = 1")  # Default to Submitted
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    query = f"""
        SELECT 
            ss.name as salary_slip,
            ss.employee,
            ss.employee_name,
            ss.department,
            ss.designation,
            ss.start_date,
            ss.end_date,
            ss.status,
            ss.docstatus,
            MONTH(ss.start_date) as month_number,
            YEAR(ss.start_date) as year_number
        FROM `tabSalary Slip` ss
        {where_clause}
        ORDER BY ss.start_date DESC, ss.department, ss.employee_name
    """
    
    if values:
        salary_slips = frappe.db.sql(query, tuple(values), as_dict=1)
    else:
        salary_slips = frappe.db.sql(query, as_dict=1)
    
    if not salary_slips:
        frappe.msgprint(_("No Salary Slips found"))
        return []
    
    result = []
    
    for slip in salary_slips:
        row = frappe._dict()
        
        # Basic Info
        row.employee = slip.employee or ""
        row.employee_name = slip.employee_name or ""
        row.department = slip.department or ""
        row.salary_slip = slip.salary_slip
        row.status = slip.status or get_docstatus_text(slip.docstatus)
        row.month = slip.month_number
        row.year = slip.year_number
        
        # Get deductions
        deductions = get_deductions(slip.salary_slip)
        
        # Social Security and Income Tax
        row.social_security = flt(deductions.get("Social Security", 0))
        row.income_tax = flt(deductions.get("Income Tax", 0))
        
        # ?? EMPLOYEE TOTAL - ????? ?? ??????
        row.employee_total = row.social_security + row.income_tax
        
        # ??? ??? ???? ????? ?? ??? ???? ????? ??
        if row.social_security > 0 or row.income_tax > 0:
            result.append(row)
    
    return result

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

def get_total_row(data):
    """TOTAL ROW - ?? ?? ??????"""
    
    total = frappe._dict()
    
    total.employee = "TOTAL"
    total.employee_name = ""
    total.department = ""
    total.salary_slip = ""
    total.status = ""
    total.month = ""
    total.year = ""
    
    # Deductions Total
    total.social_security = sum([flt(d.social_security) for d in data])
    total.income_tax = sum([flt(d.income_tax) for d in data])
    
    # ?? GRAND TOTAL - ?? ???????? ?? ?????? ?? ??????
    total.employee_total = total.social_security + total.income_tax
    
    return total

def get_summary(data):
    """Dashboard Summary Cards"""
    if not data:
        return [
            {"label": _("Total Employees"), "value": 0, "indicator": "Blue", "datatype": "Int"},
            {"label": _("Total Salary Slips"), "value": 0, "indicator": "Blue", "datatype": "Int"},
            {"label": _("Total Social Security"), "value": 0, "indicator": "Green", "datatype": "Currency"},
            {"label": _("Total Income Tax"), "value": 0, "indicator": "Red", "datatype": "Currency"},
            {"label": _("Total Deduction"), "value": 0, "indicator": "Purple", "datatype": "Currency"}
        ]
    
    data_without_total = [d for d in data if d.get("employee") != "TOTAL"]
    
    employees = set([d.employee for d in data_without_total if d.employee])
    
    total_ss = sum([flt(d.social_security) for d in data_without_total])
    total_it = sum([flt(d.income_tax) for d in data_without_total])
    total_deduction = total_ss + total_it
    
    return [
        {"label": _("Total Employees"), "value": len(employees), "indicator": "Blue", "datatype": "Int"},
        {"label": _("Total Salary Slips"), "value": len(data_without_total), "indicator": "Blue", "datatype": "Int"},
        {"label": _("Total Social Security"), "value": total_ss, "indicator": "Green", "datatype": "Currency"},
        {"label": _("Total Income Tax"), "value": total_it, "indicator": "Red", "datatype": "Currency"},
        {"label": _("Total Deduction"), "value": total_deduction, "indicator": "Purple", "datatype": "Currency"}
    ]

def get_chart(data):
    """Chart for Dashboard"""
    if not data:
        return None
    
    data_without_total = [d for d in data if d.get("employee") != "TOTAL"]
    
    # Group by Department
    departments = {}
    for d in data_without_total:
        dept = d.department or "Other"
        if dept not in departments:
            departments[dept] = {"ss": 0, "it": 0}
        departments[dept]["ss"] += flt(d.social_security)
        departments[dept]["it"] += flt(d.income_tax)
    
    # Top 5 Departments
    sorted_depts = sorted(departments.items(), key=lambda x: x[1]["ss"] + x[1]["it"], reverse=True)[:5]
    
    return {
        "data": {
            "labels": [d[0] for d in sorted_depts],
            "datasets": [
                {"name": _("Social Security"), "values": [d[1]["ss"] for d in sorted_depts], "chartType": "bar"},
                {"name": _("Income Tax"), "values": [d[1]["it"] for d in sorted_depts], "chartType": "bar"}
            ]
        },
        "type": "bar",
        "colors": ["#4CAF50", "#F44336"],
        "height": 300,
        "axisOptions": {"xAxisMode": "tick", "yAxisMode": "span"}
    }