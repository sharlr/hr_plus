# hooks.py
app_name = "hr_plus"
app_title = "HR Plus"
app_publisher = "Babar Mehmood"
app_description = "HR Plus Customizations"
app_version = "1.0.0"

# ---------------------------
# Fixtures: Custom Fields, Client Scripts, Server Scripts
# ---------------------------
# ---------------------------
# Fixtures: Only for hr_plus module
# ---------------------------
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["module", "=", "HR Plus"]
        ]
    },
    {
        "dt": "Client Script",
        "filters": [
            ["module", "=", "HR Plus"]
        ]
    },
    {
        "dt": "Server Script",
        "filters": [
            ["module", "=", "HR Plus"]
        ]
    }
]
# ---------------------------
# Server-side method expose
# ---------------------------
# Is required only if the Python module is not in a standard path
# Actually frappe.whitelist() already exposes the method
# Example JS call:
# frappe.call({
#     method: "hr_plus.monthly_attendance_utils.fetch_monthly_attendance_summary"
# })
