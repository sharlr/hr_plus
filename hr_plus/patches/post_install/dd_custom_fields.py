import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def after_migrate():
    """
    This function runs after migration to add custom fields to Employee Doctype
    """
    add_employee_custom_fields()
    frappe.db.commit()
    frappe.msgprint("Custom fields added to Employee doctype successfully")

def add_employee_custom_fields():
    """
    Add all required custom fields to Employee doctype
    """
    employee_fields = [
        # ========== PAYROLL FIELDS ==========
        {
            "fieldname": "basic_salary",
            "label": "Basic Salary",
            "fieldtype": "Currency",
            "insert_after": "payroll_cost_center",
            "precision": "2",
            "description": "Employee's basic salary for payroll calculation"
        },
        {
            "fieldname": "additional_salary_amount",
            "label": "Additional Salary",
            "fieldtype": "Currency",
            "insert_after": "basic_salary",
            "precision": "2",
            "description": "Additional salary amount"
        },
        {
            "fieldname": "appraisal_amount",
            "label": "Appraisal Amount",
            "fieldtype": "Currency",
            "insert_after": "additional_salary_amount",
            "precision": "2",
            "description": "Appraisal/increment amount"
        },
        {
            "fieldname": "special_allowance_amount",
            "label": "Special Allowance",
            "fieldtype": "Currency",
            "insert_after": "appraisal_amount",
            "precision": "2",
            "description": "Special allowance amount"
        },
        {
            "fieldname": "thank_you_allowance",
            "label": "Thank You Allowance",
            "fieldtype": "Currency",
            "insert_after": "special_allowance_amount",
            "precision": "2",
            "description": "Thank you allowance amount"
        },
        {
            "fieldname": "penalty1_amount",
            "label": "Penalty 1 Amount",
            "fieldtype": "Currency",
            "insert_after": "thank_you_allowance",
            "precision": "2",
            "description": "Penalty 1 deduction amount"
        },
        {
            "fieldname": "penalty2_amount",
            "label": "Penalty 2 Amount",
            "fieldtype": "Currency",
            "insert_after": "penalty1_amount",
            "precision": "2",
            "description": "Penalty 2 deduction amount"
        },
        {
            "fieldname": "employee_loan_amount",
            "label": "Employee Loan Amount",
            "fieldtype": "Currency",
            "insert_after": "penalty2_amount",
            "precision": "2",
            "description": "Monthly loan installment amount"
        },
        {
            "fieldname": "salary_advance_amount",
            "label": "Salary Advance Amount",
            "fieldtype": "Currency",
            "insert_after": "employee_loan_amount",
            "precision": "2",
            "description": "Salary advance amount to deduct"
        },
        {
            "fieldname": "section_break_payroll",
            "fieldtype": "Section Break",
            "label": "Seniority & Tax",
            "insert_after": "salary_advance_amount"
        },
        {
            "fieldname": "custom_seniority_percentage",
            "label": "Seniority Percentage",
            "fieldtype": "Float",
            "insert_after": "section_break_payroll",
            "precision": "2",
            "default": "2.0",
            "description": "Percentage for seniority allowance calculation (e.g., 2.0 for 2%)"
        },
        {
            "fieldname": "custom_completed_years",
            "label": "Completed Years",
            "fieldtype": "Int",
            "insert_after": "custom_seniority_percentage",
            "description": "Completed years of service for seniority calculation"
        },
        {
            "fieldname": "is_declared",
            "label": "Is Declared for Tax",
            "fieldtype": "Check",
            "insert_after": "custom_completed_years",
            "default": "1",
            "description": "Check if employee is declared for income tax"
        },
        {
            "fieldname": "performance_rating",
            "label": "Performance Rating",
            "fieldtype": "Select",
            "insert_after": "is_declared",
            "options": "Average\nGood\nExcellent",
            "default": "Average",
            "description": "Employee performance rating for thank you allowance"
        },
        {
            "fieldname": "column_break_payroll",
            "fieldtype": "Column Break",
            "insert_after": "performance_rating"
        },
        {
            "fieldname": "cnss_number",
            "label": "CNSS Number",
            "fieldtype": "Data",
            "insert_after": "column_break_payroll",
            "description": "Social Security (CNSS) number"
        },
        {
            "fieldname": "overtime_rate",
            "label": "Overtime Rate (per hour)",
            "fieldtype": "Currency",
            "insert_after": "cnss_number",
            "default": "1000",
            "precision": "2",
            "description": "Overtime rate per hour in cents"
        },
        {
            "fieldname": "pending_vacation_days",
            "label": "Pending Vacation Days",
            "fieldtype": "Float",
            "insert_after": "overtime_rate",
            "precision": "1",
            "description": "Pending vacation days for full & final settlement"
        },
        
        # ========== ATTENDANCE FIELDS ==========
        {
            "fieldname": "section_break_attendance",
            "fieldtype": "Section Break",
            "label": "Attendance Settings",
            "insert_after": "pending_vacation_days"
        },
        {
            "fieldname": "default_shift",
            "label": "Default Shift Type",
            "fieldtype": "Link",
            "options": "Shift Type",
            "insert_after": "section_break_attendance",
            "description": "Default shift type for attendance calculation"
        },
        {
            "fieldname": "attendance_device_id",
            "label": "Attendance Device ID",
            "fieldtype": "Data",
            "insert_after": "default_shift",
            "description": "Biometric device ID for attendance"
        },
        {
            "fieldname": "column_break_attendance",
            "fieldtype": "Column Break",
            "insert_after": "attendance_device_id"
        },
        {
            "fieldname": "custom_absence_days",
            "label": "Absence Days",
            "fieldtype": "Float",
            "insert_after": "column_break_attendance",
            "precision": "1",
            "read_only": 1,
            "description": "Calculated absence days from attendance"
        },
        {
            "fieldname": "custom_late_hours",
            "label": "Late Hours",
            "fieldtype": "Float",
            "insert_after": "custom_absence_days",
            "precision": "2",
            "read_only": 1,
            "description": "Calculated late hours from attendance"
        },
        {
            "fieldname": "custom_overtime_hours",
            "label": "Overtime Hours",
            "fieldtype": "Float",
            "insert_after": "custom_late_hours",
            "precision": "2",
            "read_only": 1,
            "description": "Calculated overtime hours from attendance"
        },
        {
            "fieldname": "custom_attendance_percentage",
            "label": "Attendance Percentage",
            "fieldtype": "Percent",
            "insert_after": "custom_overtime_hours",
            "precision": "2",
            "read_only": 1,
            "description": "Calculated attendance percentage"
        },
        
        # ========== OTHER FIELDS ==========
        {
            "fieldname": "section_break_other",
            "fieldtype": "Section Break",
            "label": "Other Information",
            "insert_after": "custom_attendance_percentage"
        },
        {
            "fieldname": "waqf_amount",
            "label": "Waqf Amount",
            "fieldtype": "Currency",
            "insert_after": "section_break_other",
            "default": "400",
            "precision": "2",
            "description": "Monthly waqf deduction amount (default: 400 cents)"
        },
        {
            "fieldname": "employee_category",
            "label": "Employee Category",
            "fieldtype": "Select",
            "insert_after": "waqf_amount",
            "options": "\nPermanent\nContract\nProbation\nIntern",
            "default": "Permanent"
        },
        {
            "fieldname": "custom_bank_account_number",
            "label": "Bank Account Number",
            "fieldtype": "Data",
            "insert_after": "employee_category",
            "description": "Bank account for salary transfer"
        }
    ]
    
    # Add each field if it doesn't exist
    for field in employee_fields:
        add_custom_field_if_not_exists("Employee", field)
    
    # Also add custom fields to Shift Type if needed
    add_shift_type_custom_fields()

def add_custom_field_if_not_exists(doctype, field):
    """
    Add custom field if it doesn't already exist
    """
    fieldname = field.get("fieldname")
    
    # Check if field already exists
    existing_field = frappe.db.exists("Custom Field", {
        "dt": doctype,
        "fieldname": fieldname
    })
    
    if not existing_field:
        try:
            create_custom_field(doctype, field)
            frappe.log_error(f"Added field {fieldname} to {doctype}")
        except Exception as e:
            frappe.log_error(f"Error adding field {fieldname} to {doctype}: {str(e)}")
    else:
        frappe.log_error(f"Field {fieldname} already exists in {doctype}")

def add_shift_type_custom_fields():
    """
    Add custom fields to Shift Type doctype
    """
    shift_type_fields = [
        {
            "fieldname": "late_deduction_rate",
            "label": "Late Deduction Rate (per hour)",
            "fieldtype": "Currency",
            "insert_after": "enable_auto_attendance",
            "default": "500",
            "precision": "2",
            "description": "Late deduction rate per hour in cents"
        },
        {
            "fieldname": "shift_overtime_rate",
            "label": "Overtime Rate (per hour)",
            "fieldtype": "Currency",
            "insert_after": "late_deduction_rate",
            "default": "1000",
            "precision": "2",
            "description": "Overtime rate per hour in cents"
        },
        {
            "fieldname": "weekly_off_days",
            "label": "Weekly Off Days",
            "fieldtype": "Small Text",
            "insert_after": "shift_overtime_rate",
            "description": "Comma separated weekly off days (e.g., Saturday,Sunday)"
        }
    ]
    
    for field in shift_type_fields:
        add_custom_field_if_not_exists("Shift Type", field)

def add_salary_slip_custom_fields():
    """
    Add custom fields to Salary Slip doctype
    """
    salary_slip_fields = [
        {
            "fieldname": "payroll_type",
            "label": "Payroll Type",
            "fieldtype": "Select",
            "insert_after": "letter_head",
            "options": "Monthly Salary\nFull and Final Settlement",
            "default": "Monthly Salary"
        },
        {
            "fieldname": "custom_absent_days",
            "label": "Absent Days",
            "fieldtype": "Float",
            "insert_after": "payroll_type",
            "precision": "1",
            "read_only": 1
        },
        {
            "fieldname": "custom_late_hours",
            "label": "Late Hours",
            "fieldtype": "Float",
            "insert_after": "custom_absent_days",
            "precision": "2",
            "read_only": 1
        },
        {
            "fieldname": "custom_overtime_hours",
            "label": "Overtime Hours",
            "fieldtype": "Float",
            "insert_after": "custom_late_hours",
            "precision": "2",
            "read_only": 1
        },
        {
            "fieldname": "custom_late_deduction",
            "label": "Late Deduction Amount",
            "fieldtype": "Currency",
            "insert_after": "custom_overtime_hours",
            "precision": "2",
            "read_only": 1
        },
        {
            "fieldname": "custom_overtime_amount",
            "label": "Overtime Amount",
            "fieldtype": "Currency",
            "insert_after": "custom_late_deduction",
            "precision": "2",
            "read_only": 1
        },
        {
            "fieldname": "section_break_vacation",
            "fieldtype": "Section Break",
            "label": "Vacation Details",
            "insert_after": "custom_overtime_amount"
        },
        {
            "fieldname": "pending_last_year",
            "label": "Pending from Last Year",
            "fieldtype": "Float",
            "insert_after": "section_break_vacation",
            "precision": "1",
            "read_only": 1
        },
        {
            "fieldname": "earned_current",
            "label": "Earned Current Year",
            "fieldtype": "Float",
            "insert_after": "pending_last_year",
            "precision": "1",
            "read_only": 1
        },
        {
            "fieldname": "taken_current",
            "label": "Taken Current Year",
            "fieldtype": "Float",
            "insert_after": "earned_current",
            "precision": "1",
            "read_only": 1
        },
        {
            "fieldname": "total_pending",
            "label": "Total Pending",
            "fieldtype": "Float",
            "insert_after": "taken_current",
            "precision": "1",
            "read_only": 1
        }
    ]
    
    for field in salary_slip_fields:
        add_custom_field_if_not_exists("Salary Slip", field)

# ========== COMMAND LINE EXECUTION ==========

def execute_manual_migration():
    """
    Function to run manually from bench console
    Usage: bench execute your_app.patches.post_install.add_custom_fields_to_employee.execute_manual_migration
    """
    print("Starting custom fields migration...")
    
    try:
        add_employee_custom_fields()
        add_salary_slip_custom_fields()
        
        frappe.db.commit()
        print("? Custom fields migration completed successfully!")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"? Migration failed: {str(e)}")
        raise

# ========== PATCH FILE FOR AUTOMATIC MIGRATION ==========

# Create a patch file in your_app/patches/post_install/add_custom_fields.py
# with this content:

"""
from frappe import _
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    \"\"\"
    Add custom fields to Employee, Salary Slip, and Shift Type doctypes
    \"\"\"
    print("Adding custom fields...")
    
    # Add fields to Employee
    employee_fields = [
        # ... (same fields array as above)
    ]
    
    for field in employee_fields:
        if not frappe.db.exists("Custom Field", {"dt": "Employee", "fieldname": field["fieldname"]}):
            create_custom_field("Employee", field)
    
    print("Custom fields added successfully!")
"""